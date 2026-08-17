"""Whitelisted dependency providers with deterministic resource cleanup."""

from __future__ import annotations

import inspect
from contextlib import AsyncExitStack, ExitStack
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Callable

from .config import ALLOW_PROVIDER_NAME_FALLBACK
from .exceptions import ProviderRegistrationError, ProviderResolutionError


class ProviderLifetime(StrEnum):
    REQUEST = "REQUEST"
    SINGLETON = "SINGLETON"


@dataclass(frozen=True, slots=True)
class ProviderDefinition:
    annotation: Any
    factory: Callable[[], Any]
    name: str | None
    lifetime: ProviderLifetime


class ProviderRegistry:
    """Central allowlist for injectable resources."""

    def __init__(self, *, allow_name_fallback: bool = ALLOW_PROVIDER_NAME_FALLBACK) -> None:
        self._allow_name_fallback = allow_name_fallback
        self._by_type: dict[Any, ProviderDefinition] = {}
        self._by_name: dict[str, ProviderDefinition] = {}
        self._singletons: dict[ProviderDefinition, Any] = {}

    def register(
        self,
        annotation: Any,
        factory: Callable[[], Any],
        *,
        name: str | None = None,
        lifetime: ProviderLifetime = ProviderLifetime.REQUEST,
        replace: bool = False,
    ) -> None:
        if annotation is inspect.Signature.empty:
            raise ProviderRegistrationError("Provider 必須指定型別")
        if not callable(factory):
            raise ProviderRegistrationError("Provider factory 必須可呼叫")
        if not replace and annotation in self._by_type:
            raise ProviderRegistrationError(f"Provider 型別已註冊: {annotation!r}")
        if name and not replace and name in self._by_name:
            raise ProviderRegistrationError(f"Provider 名稱已註冊: {name}")

        definition = ProviderDefinition(annotation, factory, name, lifetime)
        self._by_type[annotation] = definition
        if name:
            self._by_name[name] = definition

    def register_instance(
        self,
        annotation: Any,
        instance: Any,
        *,
        name: str | None = None,
        replace: bool = False,
    ) -> None:
        self.register(
            annotation,
            lambda: instance,
            name=name,
            lifetime=ProviderLifetime.SINGLETON,
            replace=replace,
        )

    def contains(self, annotation: Any, parameter_name: str | None = None) -> bool:
        return self._find_definition(annotation, parameter_name, required=False) is not None

    def describe(self, annotation: Any, parameter_name: str) -> dict[str, str]:
        definition = self._find_definition(annotation, parameter_name, required=True)
        return {
            "parameter": parameter_name,
            "annotation": getattr(annotation, "__name__", repr(annotation)),
            "provider": definition.name or getattr(annotation, "__name__", repr(annotation)),
            "lifetime": definition.lifetime.value,
        }

    def resolve_sync(
        self,
        annotation: Any,
        parameter_name: str,
        stack: ExitStack,
    ) -> Any:
        definition = self._find_definition(annotation, parameter_name, required=True)
        value = self._get_or_create(definition)
        if inspect.isawaitable(value) or hasattr(value, "__aenter__"):
            raise ProviderResolutionError(
                f"Provider {parameter_name} 是非同步資源，必須使用 execute_async"
            )
        if definition.lifetime is ProviderLifetime.REQUEST and hasattr(value, "__enter__"):
            value = stack.enter_context(value)
        return value

    async def resolve_async(
        self,
        annotation: Any,
        parameter_name: str,
        stack: AsyncExitStack,
    ) -> Any:
        definition = self._find_definition(annotation, parameter_name, required=True)
        value = self._get_or_create(definition)
        if inspect.isawaitable(value):
            value = await value
        if definition.lifetime is ProviderLifetime.REQUEST:
            if hasattr(value, "__aenter__"):
                value = await stack.enter_async_context(value)
            elif hasattr(value, "__enter__"):
                value = stack.enter_context(value)
        return value

    def _get_or_create(self, definition: ProviderDefinition) -> Any:
        if definition.lifetime is ProviderLifetime.SINGLETON:
            if definition not in self._singletons:
                value = definition.factory()
                if inspect.isawaitable(value) or hasattr(value, "__enter__") or hasattr(value, "__aenter__"):
                    raise ProviderResolutionError(
                        "Singleton Provider 不得是 awaitable 或 context manager；"
                        "請使用 register_instance 或 REQUEST lifetime"
                    )
                self._singletons[definition] = value
            return self._singletons[definition]
        return definition.factory()

    def _find_definition(
        self,
        annotation: Any,
        parameter_name: str | None,
        *,
        required: bool,
    ) -> ProviderDefinition | None:
        definition = self._by_type.get(annotation)
        if definition is None and self._allow_name_fallback and parameter_name:
            definition = self._by_name.get(parameter_name)
        if definition is None and required:
            raise ProviderResolutionError(
                f"沒有白名單 Provider: parameter={parameter_name}, annotation={annotation!r}"
            )
        return definition

