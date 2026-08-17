"""Typed smart executor with validation, DI, lifecycle, and error isolation."""

from __future__ import annotations

import asyncio
import inspect
import time
from contextlib import AsyncExitStack, ExitStack
from typing import Any, Mapping

from pydantic import BaseModel, ValidationError

from .config import DEFAULT_ASYNC_TIMEOUT_SECONDS
from .contracts import ExecutionEnvelope, ExecutionStatus, ModuleState
from .exceptions import (
    AsyncExecutionRequiredError,
    InputContractError,
    ModuleExecutionError,
    OutputContractError,
    VIAInterfaceError,
)
from .registry import CommandDescriptor, VIACommandRegistry


class VIASmartExecutor:
    """Invoke registered commands without blind dict passing."""

    def __init__(
        self,
        registry: VIACommandRegistry,
        *,
        async_timeout_seconds: float = DEFAULT_ASYNC_TIMEOUT_SECONDS,
    ) -> None:
        self._registry = registry
        self._async_timeout_seconds = async_timeout_seconds

    def execute(
        self,
        module_name: str,
        raw_payload: Mapping[str, Any],
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> BaseModel:
        descriptor = self._registry.get(module_name)
        if descriptor.is_async:
            raise AsyncExecutionRequiredError(
                f"{module_name} 是非同步模組，請使用 execute_async"
            )
        self._ensure_ready(descriptor)
        try:
            payload = self._validate_input(descriptor, raw_payload)
        except InputContractError as exc:
            self._registry.ssot.record_metric(
                descriptor.resource_urn,
                "VALIDATION_REJECTION",
                error=str(exc),
            )
            raise
        kwargs: dict[str, Any] = {descriptor.input_parameter.name: payload}
        started = time.perf_counter()
        self._registry.ssot.set_state(descriptor.resource_urn, ModuleState.EXECUTING)
        try:
            with ExitStack() as stack:
                kwargs.update(self._build_sync_dependencies(descriptor, overrides, stack))
                result = descriptor.module.execute(**kwargs)
                if inspect.isawaitable(result):
                    raise AsyncExecutionRequiredError(
                        f"{module_name}.execute 回傳 awaitable，請使用 execute_async"
                    )
                output = self._validate_output(descriptor, result)
            latency_ms = (time.perf_counter() - started) * 1000
            self._registry.ssot.record_metric(
                descriptor.resource_urn,
                "SUCCESS",
                latency_ms=latency_ms,
            )
            self._registry.ssot.set_state(descriptor.resource_urn, ModuleState.READY)
            return output
        except VIAInterfaceError as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            self._registry.ssot.record_metric(
                descriptor.resource_urn,
                "FAILURE",
                latency_ms=latency_ms,
                error=str(exc),
            )
            self._registry.ssot.set_state(descriptor.resource_urn, ModuleState.ERROR)
            raise
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            self._registry.ssot.record_metric(
                descriptor.resource_urn,
                "FAILURE",
                latency_ms=latency_ms,
                error=str(exc),
            )
            self._registry.ssot.set_state(descriptor.resource_urn, ModuleState.ERROR)
            raise ModuleExecutionError(f"模組執行失敗: {module_name}: {exc}") from exc

    async def execute_async(
        self,
        module_name: str,
        raw_payload: Mapping[str, Any],
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> BaseModel:
        descriptor = self._registry.get(module_name)
        self._ensure_ready(descriptor)
        try:
            payload = self._validate_input(descriptor, raw_payload)
        except InputContractError as exc:
            self._registry.ssot.record_metric(
                descriptor.resource_urn,
                "VALIDATION_REJECTION",
                error=str(exc),
            )
            raise
        kwargs: dict[str, Any] = {descriptor.input_parameter.name: payload}
        started = time.perf_counter()
        self._registry.ssot.set_state(descriptor.resource_urn, ModuleState.EXECUTING)

        async def def_invoke() -> BaseModel:
            async with AsyncExitStack() as stack:
                kwargs.update(
                    await self._build_async_dependencies(descriptor, overrides, stack)
                )
                result = descriptor.module.execute(**kwargs)
                if inspect.isawaitable(result):
                    result = await result
                return self._validate_output(descriptor, result)

        try:
            output = await asyncio.wait_for(
                def_invoke(),
                timeout=self._async_timeout_seconds,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            self._registry.ssot.record_metric(
                descriptor.resource_urn,
                "SUCCESS",
                latency_ms=latency_ms,
            )
            self._registry.ssot.set_state(descriptor.resource_urn, ModuleState.READY)
            return output
        except VIAInterfaceError as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            self._registry.ssot.record_metric(
                descriptor.resource_urn,
                "FAILURE",
                latency_ms=latency_ms,
                error=str(exc),
            )
            self._registry.ssot.set_state(descriptor.resource_urn, ModuleState.ERROR)
            raise
        except TimeoutError as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            self._registry.ssot.record_metric(
                descriptor.resource_urn,
                "TIMEOUT",
                latency_ms=latency_ms,
                error=str(exc),
            )
            self._registry.ssot.set_state(descriptor.resource_urn, ModuleState.ERROR)
            raise ModuleExecutionError(
                f"模組執行逾時: {module_name}: {self._async_timeout_seconds}s"
            ) from exc
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            self._registry.ssot.record_metric(
                descriptor.resource_urn,
                "FAILURE",
                latency_ms=latency_ms,
                error=str(exc),
            )
            self._registry.ssot.set_state(descriptor.resource_urn, ModuleState.ERROR)
            raise ModuleExecutionError(f"模組執行失敗: {module_name}: {exc}") from exc

    def execute_safe(
        self,
        module_name: str,
        raw_payload: Mapping[str, Any],
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> ExecutionEnvelope:
        try:
            output = self.execute(module_name, raw_payload, overrides=overrides)
            return ExecutionEnvelope(
                module_name=module_name,
                resource_urn=self._resource_urn_or_none(module_name),
                status=ExecutionStatus.SUCCESS,
                output=output.model_dump(mode="json"),
            )
        except InputContractError as exc:
            return ExecutionEnvelope(
                module_name=module_name,
                resource_urn=self._resource_urn_or_none(module_name),
                status=ExecutionStatus.REJECTED,
                errors=exc.errors,
                message=str(exc),
            )
        except OutputContractError as exc:
            return ExecutionEnvelope(
                module_name=module_name,
                resource_urn=self._resource_urn_or_none(module_name),
                status=ExecutionStatus.ERROR,
                errors=exc.errors,
                message=str(exc),
            )
        except VIAInterfaceError as exc:
            return ExecutionEnvelope(
                module_name=module_name,
                resource_urn=self._resource_urn_or_none(module_name),
                status=ExecutionStatus.ERROR,
                message=str(exc),
            )

    def _validate_input(
        self,
        descriptor: CommandDescriptor,
        raw_payload: Mapping[str, Any],
    ) -> BaseModel:
        try:
            return descriptor.input_model.model_validate(dict(raw_payload))
        except ValidationError as exc:
            raise InputContractError(
                descriptor.manifest.name,
                exc.errors(include_url=False),
            ) from exc

    def _ensure_ready(self, descriptor: CommandDescriptor) -> None:
        record = self._registry.ssot.resolve(descriptor.resource_urn)
        if record.state is not ModuleState.READY:
            raise ModuleExecutionError(
                f"模組不是 READY，拒絕執行: {descriptor.manifest.name}, "
                f"state={record.state.value}"
            )

    def _resource_urn_or_none(self, reference: str) -> str | None:
        try:
            return self._registry.get(reference).resource_urn
        except VIAInterfaceError:
            return None

    def _validate_output(
        self,
        descriptor: CommandDescriptor,
        raw_output: Any,
    ) -> BaseModel:
        try:
            return descriptor.output_model.model_validate(raw_output)
        except ValidationError as exc:
            raise OutputContractError(
                descriptor.manifest.name,
                exc.errors(include_url=False),
            ) from exc

    def _build_sync_dependencies(
        self,
        descriptor: CommandDescriptor,
        overrides: Mapping[str, Any] | None,
        stack: ExitStack,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        override_values = dict(overrides or {})
        unknown = set(override_values) - {
            item.name for item in descriptor.injected_parameters
        }
        if unknown:
            raise ModuleExecutionError(
                f"未知的依賴覆寫: {', '.join(sorted(unknown))}"
            )
        for item in descriptor.injected_parameters:
            if item.name in override_values:
                result[item.name] = override_values[item.name]
            else:
                result[item.name] = self._registry.providers.resolve_sync(
                    item.annotation,
                    item.name,
                    stack,
                )
        return result

    async def _build_async_dependencies(
        self,
        descriptor: CommandDescriptor,
        overrides: Mapping[str, Any] | None,
        stack: AsyncExitStack,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        override_values = dict(overrides or {})
        unknown = set(override_values) - {
            item.name for item in descriptor.injected_parameters
        }
        if unknown:
            raise ModuleExecutionError(
                f"未知的依賴覆寫: {', '.join(sorted(unknown))}"
            )
        for item in descriptor.injected_parameters:
            if item.name in override_values:
                result[item.name] = override_values[item.name]
            else:
                result[item.name] = await self._registry.providers.resolve_async(
                    item.annotation,
                    item.name,
                    stack,
                )
        return result
