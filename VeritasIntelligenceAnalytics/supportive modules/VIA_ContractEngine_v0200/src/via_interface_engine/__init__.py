"""VIA Contract Interface Engine public API."""

from .config import ENGINE_NAME, ENGINE_VERSION
from .contracts import (
    ExecutionEnvelope,
    ExecutionStatus,
    ModuleContext,
    ModuleManifest,
    ModuleState,
    VIAInputModel,
    VIAModuleABC,
    VIAOutputModel,
)
from .executor import VIASmartExecutor
from .discovery import (
    CandidateFinding,
    SSOTAutoRegistrar,
    StaticCandidate,
    StaticManifestScanner,
    VIAFileWatchdog,
    VIAMemoryWatchdog,
)
from .providers import ProviderLifetime, ProviderRegistry
from .registry import CommandDescriptor, VIACommandRegistry
from .ssot import ReadWriteLock, VIASSOTRegistry
from .twin import TwinCheck, TwinReport, VIADigitalTwinTester
from .ui import SchemaToHTMLRenderer

__all__ = [
    "CommandDescriptor",
    "CandidateFinding",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ExecutionEnvelope",
    "ExecutionStatus",
    "ModuleContext",
    "ModuleManifest",
    "ModuleState",
    "ProviderLifetime",
    "ProviderRegistry",
    "SchemaToHTMLRenderer",
    "SSOTAutoRegistrar",
    "StaticCandidate",
    "StaticManifestScanner",
    "TwinCheck",
    "TwinReport",
    "VIACommandRegistry",
    "VIADigitalTwinTester",
    "VIAInputModel",
    "VIAModuleABC",
    "VIAOutputModel",
    "VIASmartExecutor",
    "VIAFileWatchdog",
    "VIAMemoryWatchdog",
    "VIASSOTRegistry",
    "ReadWriteLock",
]
