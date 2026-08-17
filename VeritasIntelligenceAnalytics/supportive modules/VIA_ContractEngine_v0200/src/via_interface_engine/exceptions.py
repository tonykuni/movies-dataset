"""Typed fail-closed exceptions for the VIA interface engine."""

from __future__ import annotations

from typing import Any


class VIAInterfaceError(Exception):
    """Base exception for all governed interface failures."""


class ManifestValidationError(VIAInterfaceError):
    """Raised when module metadata is invalid."""


class ContractInspectionError(VIAInterfaceError):
    """Raised when an execute signature cannot be governed safely."""


class DuplicateModuleError(VIAInterfaceError):
    """Raised when a manifest name is already registered."""


class DependencyResolutionError(VIAInterfaceError):
    """Raised when module dependencies are missing or form a cycle."""


class LifecycleError(VIAInterfaceError):
    """Raised when setup or teardown violates the lifecycle contract."""


class ProviderRegistrationError(VIAInterfaceError):
    """Raised when a dependency provider is unsafe or duplicated."""


class ProviderResolutionError(VIAInterfaceError):
    """Raised when an execute dependency cannot be injected."""


class InputContractError(VIAInterfaceError):
    """Raised before module execution when input validation fails."""

    def __init__(self, module_name: str, errors: list[dict[str, Any]]) -> None:
        self.module_name = module_name
        self.errors = errors
        super().__init__(f"Input contract rejected payload for {module_name}")


class OutputContractError(VIAInterfaceError):
    """Raised after module execution when its result breaks the contract."""

    def __init__(self, module_name: str, errors: list[dict[str, Any]]) -> None:
        self.module_name = module_name
        self.errors = errors
        super().__init__(f"Output contract rejected result from {module_name}")


class ModuleExecutionError(VIAInterfaceError):
    """Raised when governed business logic fails."""


class AsyncExecutionRequiredError(VIAInterfaceError):
    """Raised when a coroutine is passed through the synchronous executor."""

