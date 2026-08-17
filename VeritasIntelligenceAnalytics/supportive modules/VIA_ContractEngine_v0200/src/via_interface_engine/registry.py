"""SSOT-backed command registry, DAG resolution, and lifecycle control."""

from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import dataclass
from pathlib import Path
from types import UnionType
from typing import Annotated, Any, Callable, Iterable, Union, get_args, get_origin, get_type_hints

from pydantic import BaseModel, ValidationError

from .contracts import (
    CommandSchemaRecord,
    ModuleContext,
    ModuleManifest,
    ModuleState,
    VIAInputModel,
    VIAModuleABC,
    VIAOutputModel,
)
from .exceptions import (
    ContractInspectionError,
    DependencyResolutionError,
    DuplicateModuleError,
    LifecycleError,
    ManifestValidationError,
)
from .providers import ProviderRegistry
from .ssot import VIASSOTRegistry


@dataclass(frozen=True, slots=True)
class ParameterDescriptor:
    name: str
    annotation: Any
    has_default: bool


@dataclass(slots=True)
class CommandDescriptor:
    resource_urn: str
    manifest: ModuleManifest
    module: VIAModuleABC
    input_parameter: ParameterDescriptor
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    injected_parameters: tuple[ParameterDescriptor, ...]
    is_async: bool

    def to_schema_record(self, providers: ProviderRegistry) -> CommandSchemaRecord:
        return CommandSchemaRecord(
            module_name=self.manifest.name,
            resource_urn=self.resource_urn,
            manifest=self.manifest.model_dump(mode="json"),
            input_parameter=self.input_parameter.name,
            input_schema=self.input_model.model_json_schema(),
            output_schema=self.output_model.model_json_schema(),
            injected_dependencies=[
                providers.describe(item.annotation, item.name)
                for item in self.injected_parameters
            ],
        )


class VIACommandRegistry:
    """The only supported gateway to runtime module instances."""

    def __init__(
        self,
        providers: ProviderRegistry,
        ssot_registry: VIASSOTRegistry,
    ) -> None:
        self._providers = providers
        self._ssot = ssot_registry

    @property
    def providers(self) -> ProviderRegistry:
        return self._providers

    @property
    def ssot(self) -> VIASSOTRegistry:
        return self._ssot

    def register(
        self,
        module: VIAModuleABC,
        context: ModuleContext,
        *,
        source_ref: str | None = None,
        source_sha256: str | None = None,
    ) -> CommandDescriptor:
        if not isinstance(module, VIAModuleABC):
            raise ContractInspectionError("模組必須繼承 VIAModuleABC")

        manifest = self.validate_manifest(module)
        resolved_source_ref, resolved_source_sha256 = self._resolve_source_identity(
            module,
            manifest,
            source_ref,
            source_sha256,
        )
        try:
            existing = self._ssot.resolve(manifest.name)
        except DependencyResolutionError:
            existing = None
        else:
            may_promote_staged = (
                existing.instance is None
                and existing.source_sha256 == resolved_source_sha256
            )
            if not may_promote_staged:
                raise DuplicateModuleError(f"模組名稱已註冊: {manifest.name}")

        if manifest.name in manifest.dependencies:
            raise DependencyResolutionError("模組不得依賴自己")

        dependency_urns = tuple(
            self._require_ready_dependency(reference).resource_urn
            for reference in manifest.dependencies
        )
        descriptor = self._inspect_module(module, manifest)
        resource_urn, registered_at = self._ssot.allocate_identity(
            manifest,
            resolved_source_ref,
            resolved_source_sha256,
        )
        descriptor.resource_urn = resource_urn
        self._ssot.attach_runtime(
            resource_urn=resource_urn,
            registered_at=registered_at,
            manifest=manifest,
            instance=module,
            state=ModuleState.SETTING_UP,
            dependencies=dependency_urns,
            source_ref=resolved_source_ref,
            source_sha256=resolved_source_sha256,
            descriptor=descriptor,
        )

        try:
            module.on_load(context)
            healthy = bool(module.health_check())
            if not healthy:
                raise LifecycleError(f"模組首次 health_check 未通過: {manifest.name}")
        except Exception as exc:
            self._ssot.set_state(
                resource_urn,
                ModuleState.ERROR,
                detail={"setup_error": str(exc)},
            )
            if isinstance(exc, LifecycleError):
                raise
            raise LifecycleError(f"模組 on_load 失敗: {manifest.name}: {exc}") from exc

        self._ssot.set_state(resource_urn, ModuleState.READY)
        self._ssot.record_metric(resource_urn, "HEALTH_SUCCESS")
        return descriptor

    def register_many(
        self,
        modules: Iterable[VIAModuleABC],
        context_factory: Callable[[ModuleManifest], ModuleContext],
    ) -> tuple[CommandDescriptor, ...]:
        module_list = list(modules)
        manifests = [self.validate_manifest(module) for module in module_list]
        module_by_name = dict(zip((item.name for item in manifests), module_list, strict=True))
        manifest_by_name = {item.name: item for item in manifests}
        if len(module_by_name) != len(module_list):
            raise DuplicateModuleError("批次模組包含重複 Manifest name")

        ordered_names = self._batch_topological_order(manifest_by_name)
        registered: list[CommandDescriptor] = []
        try:
            for name in ordered_names:
                manifest = manifest_by_name[name]
                descriptor = self.register(
                    module_by_name[name],
                    context_factory(manifest),
                )
                registered.append(descriptor)
        except Exception:
            for descriptor in reversed(registered):
                try:
                    self.unregister(descriptor.resource_urn)
                except Exception:
                    self._ssot.set_state(
                        descriptor.resource_urn,
                        ModuleState.ERROR,
                        detail={"rollback": "teardown_failed"},
                    )
            raise
        return tuple(registered)

    def unregister(self, reference: str) -> None:
        record = self._ssot.resolve(reference)
        descriptor = record.descriptor
        if descriptor is None or record.instance is None:
            raise LifecycleError(f"資源不是已掛載的可執行模組: {reference}")
        dependents = self._ssot.find_dependents(record.resource_urn)
        if dependents:
            dependent_names = ", ".join(item.manifest.name for item in dependents)
            raise DependencyResolutionError(
                f"不可卸載 {record.manifest.name}；仍被依賴: {dependent_names}"
            )

        self._ssot.set_state(record.resource_urn, ModuleState.TEARING_DOWN)
        try:
            record.instance.teardown()
        except Exception as exc:
            self._ssot.set_state(
                record.resource_urn,
                ModuleState.ERROR,
                detail={"teardown_error": str(exc)},
            )
            raise LifecycleError(
                f"模組 teardown 失敗: {record.manifest.name}: {exc}"
            ) from exc
        self._ssot.detach_runtime(record.resource_urn)

    def shutdown(self) -> None:
        errors: list[str] = []
        for resource_urn in reversed(self.topological_order()):
            try:
                self.unregister(resource_urn)
            except LifecycleError as exc:
                errors.append(str(exc))
        if errors:
            raise LifecycleError("; ".join(errors))

    def get(self, reference: str) -> CommandDescriptor:
        record = self._ssot.resolve(reference)
        if record.descriptor is None:
            raise DependencyResolutionError(f"資源尚未掛載 Command Descriptor: {reference}")
        return record.descriptor

    def get_instance(self, reference: str) -> VIAModuleABC:
        record = self._ssot.resolve(reference)
        if record.instance is None:
            raise DependencyResolutionError(f"資源尚未掛載實例: {reference}")
        return record.instance

    def list_descriptors(self) -> tuple[CommandDescriptor, ...]:
        descriptors = [
            item.descriptor
            for item in self._ssot.list_records(include_staged=False)
            if item.descriptor is not None
        ]
        return tuple(sorted(descriptors, key=lambda item: item.resource_urn))

    def schema_catalog(self) -> dict[str, Any]:
        return {
            "catalog_version": "2.0",
            "commands": [
                item.to_schema_record(self._providers).model_dump(mode="json")
                for item in self.list_descriptors()
            ],
        }

    def tool_catalog(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        for descriptor in self.list_descriptors():
            schema = descriptor.input_model.model_json_schema()
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": descriptor.manifest.name,
                        "description": descriptor.manifest.description,
                        "parameters": schema,
                        "x-via-resource-urn": descriptor.resource_urn,
                    },
                }
            )
        return tools

    def topological_order(self) -> tuple[str, ...]:
        records = {
            item.resource_urn: item
            for item in self._ssot.list_records(include_staged=False)
            if item.descriptor is not None
        }
        indegree = {resource_urn: 0 for resource_urn in records}
        children: dict[str, list[str]] = {resource_urn: [] for resource_urn in records}
        for resource_urn, record in records.items():
            for dependency in record.dependencies:
                if dependency not in records:
                    raise DependencyResolutionError(
                        f"模組 {record.manifest.name} 的 Runtime 依賴不存在: {dependency}"
                    )
                indegree[resource_urn] += 1
                children[dependency].append(resource_urn)
        return self._topological_sort(indegree, children)

    def health_check_all(self) -> dict[str, bool]:
        return self._ssot.health_check_all()

    @staticmethod
    def validate_manifest(module: VIAModuleABC) -> ModuleManifest:
        raw_manifest = getattr(module, "__manifest__", None)
        if raw_manifest is None:
            raise ManifestValidationError("模組缺少 __manifest__")
        try:
            return ModuleManifest.model_validate(raw_manifest)
        except ValidationError as exc:
            raise ManifestValidationError(str(exc)) from exc

    def _batch_topological_order(
        self,
        manifest_by_name: dict[str, ModuleManifest],
    ) -> tuple[str, ...]:
        indegree = {name: 0 for name in manifest_by_name}
        children: dict[str, list[str]] = {name: [] for name in manifest_by_name}
        for name, manifest in manifest_by_name.items():
            for dependency in manifest.dependencies:
                if dependency in manifest_by_name:
                    indegree[name] += 1
                    children[dependency].append(name)
                    continue
                try:
                    record = self._ssot.resolve_dependency(dependency)
                except DependencyResolutionError as exc:
                    raise DependencyResolutionError(
                        f"批次模組 {name} 缺少依賴: {dependency}"
                    ) from exc
                if record.state is not ModuleState.READY:
                    raise DependencyResolutionError(
                        f"批次模組 {name} 的外部依賴不是 READY: {dependency}"
                    )
        return self._topological_sort(indegree, children)

    @staticmethod
    def _topological_sort(
        indegree: dict[str, int],
        children: dict[str, list[str]],
    ) -> tuple[str, ...]:
        ready = sorted(name for name, degree in indegree.items() if degree == 0)
        ordered: list[str] = []
        while ready:
            current = ready.pop(0)
            ordered.append(current)
            for child in sorted(children[current]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
                    ready.sort()
        if len(ordered) != len(indegree):
            raise DependencyResolutionError("模組依賴圖存在循環")
        return tuple(ordered)

    def _require_ready_dependency(self, reference: str):
        record = self._ssot.resolve_dependency(reference)
        if record.state is not ModuleState.READY:
            raise DependencyResolutionError(
                f"依賴尚未 READY: {reference}, state={record.state.value}"
            )
        return record

    def _inspect_module(
        self,
        module: VIAModuleABC,
        manifest: ModuleManifest,
    ) -> CommandDescriptor:
        method = module.execute
        signature = inspect.signature(method)
        try:
            type_hints = get_type_hints(method, include_extras=True)
        except Exception as exc:
            raise ContractInspectionError(
                f"無法解析 execute 型別註記: {manifest.name}: {exc}"
            ) from exc

        payload_candidates: list[ParameterDescriptor] = []
        dependencies: list[ParameterDescriptor] = []
        for parameter in signature.parameters.values():
            if parameter.kind in {
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
                inspect.Parameter.POSITIONAL_ONLY,
            }:
                raise ContractInspectionError(
                    f"{manifest.name}.execute 不得使用 *args、**kwargs 或 positional-only"
                )
            annotation = self._unwrap_annotation(
                type_hints.get(parameter.name, parameter.annotation)
            )
            if annotation is inspect.Signature.empty:
                raise ContractInspectionError(
                    f"參數缺少型別註記: {manifest.name}.{parameter.name}"
                )
            item = ParameterDescriptor(
                name=parameter.name,
                annotation=annotation,
                has_default=parameter.default is not inspect.Signature.empty,
            )
            if self._is_input_model_type(annotation):
                payload_candidates.append(item)
            elif self._is_model_type(annotation):
                raise ContractInspectionError(
                    f"Input Contract 必須繼承 VIAInputModel: "
                    f"{manifest.name}.{parameter.name}"
                )
            else:
                if not self._providers.contains(annotation, parameter.name):
                    raise ContractInspectionError(
                        f"參數沒有白名單 Provider: {manifest.name}.{parameter.name}"
                    )
                dependencies.append(item)

        if len(payload_candidates) != 1:
            raise ContractInspectionError(
                f"{manifest.name}.execute 必須且只能有一個 Pydantic Input；"
                f"目前為 {len(payload_candidates)} 個"
            )
        return_annotation = self._unwrap_annotation(
            type_hints.get("return", signature.return_annotation)
        )
        if not self._is_output_model_type(return_annotation):
            raise ContractInspectionError(
                f"{manifest.name}.execute 回傳型別必須繼承 VIAOutputModel"
            )
        input_parameter = payload_candidates[0]
        return CommandDescriptor(
            resource_urn="",
            manifest=manifest,
            module=module,
            input_parameter=input_parameter,
            input_model=input_parameter.annotation,
            output_model=return_annotation,
            injected_parameters=tuple(dependencies),
            is_async=inspect.iscoroutinefunction(method),
        )

    @staticmethod
    def _resolve_source_identity(
        module: VIAModuleABC,
        manifest: ModuleManifest,
        source_ref: str | None,
        source_sha256: str | None,
    ) -> tuple[str, str]:
        resolved_ref = source_ref
        resolved_hash = source_sha256
        if resolved_ref is None:
            source_file = inspect.getsourcefile(module.__class__)
            resolved_ref = str(Path(source_file).resolve()) if source_file else "memory://dynamic"
        if resolved_hash is None:
            path = Path(resolved_ref)
            if path.is_file():
                resolved_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            else:
                canonical = json.dumps(
                    manifest.model_dump(mode="json"),
                    ensure_ascii=False,
                    sort_keys=True,
                )
                resolved_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if not re_full_sha256(resolved_hash):
            raise ManifestValidationError("source_sha256 必須是 64 位十六進位")
        return resolved_ref, resolved_hash.lower()

    @staticmethod
    def _is_model_type(annotation: Any) -> bool:
        return inspect.isclass(annotation) and issubclass(annotation, BaseModel)

    @staticmethod
    def _is_input_model_type(annotation: Any) -> bool:
        return inspect.isclass(annotation) and issubclass(annotation, VIAInputModel)

    @staticmethod
    def _is_output_model_type(annotation: Any) -> bool:
        return inspect.isclass(annotation) and issubclass(annotation, VIAOutputModel)

    @staticmethod
    def _unwrap_annotation(annotation: Any) -> Any:
        origin = get_origin(annotation)
        if origin is Annotated:
            return VIACommandRegistry._unwrap_annotation(get_args(annotation)[0])
        if origin in {Union, UnionType}:
            args = tuple(arg for arg in get_args(annotation) if arg is not type(None))
            if len(args) == 1:
                return VIACommandRegistry._unwrap_annotation(args[0])
        return annotation


def re_full_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdefABCDEF" for character in value)
