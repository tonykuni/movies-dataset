from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import asyncio
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import Field

from via_interface_engine import (
    ExecutionStatus,
    ModuleContext,
    ProviderRegistry,
    VIACommandRegistry,
    VIAInputModel,
    VIAModuleABC,
    VIAOutputModel,
    VIASmartExecutor,
    VIASSOTRegistry,
)
from via_interface_engine.exceptions import (
    AsyncExecutionRequiredError,
    ContractInspectionError,
    OutputContractError,
)


# def TEST PARAMETERS
TEST_CONTEXT = ModuleContext(run_id="RUN_EXECUTOR", subsystem="TEST")


class NumberInput(VIAInputModel):
    amount: float = Field(gt=0)


class NumberOutput(VIAOutputModel):
    result: float


class Resource:
    opened = 0
    closed = 0

    def __enter__(self) -> "Resource":
        type(self).opened += 1
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:  # type: ignore[no-untyped-def]
        type(self).closed += 1


class TypedModule(VIAModuleABC):
    __manifest__ = {"name": "TypedModule", "version": "1.0.0", "author": "VIA"}

    def setup(self, context: ModuleContext) -> None:
        self.context = context

    def health_check(self) -> bool:
        return self.context is not None

    def execute(self, input_data: NumberInput, resource: Resource) -> NumberOutput:
        return NumberOutput(result=input_data.amount * 2)

    def teardown(self) -> None:
        self.context = None


class BadOutputModule(TypedModule):
    __manifest__ = {"name": "BadOutputModule", "version": "1.0.0", "author": "VIA"}

    def execute(self, input_data: NumberInput, resource: Resource) -> NumberOutput:
        return {"wrong": 1}  # type: ignore[return-value]


class MissingProviderModule(VIAModuleABC):
    __manifest__ = {"name": "MissingProvider", "version": "1.0.0", "author": "VIA"}

    def setup(self, context: ModuleContext) -> None:
        pass

    def health_check(self) -> bool:
        return True

    def execute(self, input_data: NumberInput, missing: str) -> NumberOutput:
        return NumberOutput(result=input_data.amount)

    def teardown(self) -> None:
        pass


class AsyncModule(TypedModule):
    __manifest__ = {"name": "AsyncModule", "version": "1.0.0", "author": "VIA"}

    async def execute(self, input_data: NumberInput, resource: Resource) -> NumberOutput:
        await asyncio.sleep(0)
        return NumberOutput(result=input_data.amount + 1)


class ExecutorDITests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        VIASSOTRegistry.reset_for_testing()
        Resource.opened = 0
        Resource.closed = 0
        providers = ProviderRegistry()
        providers.register(Resource, Resource, name="resource")
        self.registry = VIACommandRegistry(
            providers,
            VIASSOTRegistry(Path(self.temporary_directory.name) / "registry.sqlite3"),
        )
        self.executor = VIASmartExecutor(self.registry)

    def tearDown(self) -> None:
        self.registry.shutdown()
        VIASSOTRegistry.reset_for_testing()
        self.temporary_directory.cleanup()

    def test_html_numeric_string_is_converted_before_execute(self) -> None:
        self.registry.register(TypedModule(), TEST_CONTEXT)
        output = self.executor.execute("TypedModule", {"amount": "500"})
        self.assertEqual(output.result, 1000.0)
        metrics = self.registry.ssot.resolve("TypedModule").metrics
        self.assertEqual(metrics.success_count, 1)

    def test_non_numeric_text_is_rejected_without_opening_resource(self) -> None:
        self.registry.register(TypedModule(), TEST_CONTEXT)
        envelope = self.executor.execute_safe("TypedModule", {"amount": "五百"})
        self.assertEqual(envelope.status, ExecutionStatus.REJECTED)
        self.assertEqual(Resource.opened, 0)
        self.assertEqual(Resource.closed, 0)
        metrics = self.registry.ssot.resolve("TypedModule").metrics
        self.assertEqual(metrics.validation_rejection_count, 1)

    def test_request_resource_is_closed_after_success(self) -> None:
        self.registry.register(TypedModule(), TEST_CONTEXT)
        self.executor.execute("TypedModule", {"amount": 3})
        self.assertEqual(Resource.opened, 1)
        self.assertEqual(Resource.closed, 1)

    def test_output_is_validated(self) -> None:
        self.registry.register(BadOutputModule(), TEST_CONTEXT)
        with self.assertRaises(OutputContractError):
            self.executor.execute("BadOutputModule", {"amount": 3})
        self.assertEqual(Resource.closed, 1)

    def test_output_contract_failure_is_system_error_not_input_rejection(self) -> None:
        self.registry.register(BadOutputModule(), TEST_CONTEXT)
        envelope = self.executor.execute_safe("BadOutputModule", {"amount": 3})
        self.assertEqual(envelope.status, ExecutionStatus.ERROR)
        self.assertTrue(envelope.errors)

    def test_missing_provider_is_rejected_at_registration(self) -> None:
        with self.assertRaises(ContractInspectionError):
            self.registry.register(MissingProviderModule(), TEST_CONTEXT)

    def test_sync_path_rejects_async_command(self) -> None:
        self.registry.register(AsyncModule(), TEST_CONTEXT)
        with self.assertRaises(AsyncExecutionRequiredError):
            self.executor.execute("AsyncModule", {"amount": 1})


class AsyncExecutorTests(unittest.IsolatedAsyncioTestCase):
    async def test_async_command_and_sync_context_resource(self) -> None:
        temporary_directory = TemporaryDirectory()
        VIASSOTRegistry.reset_for_testing()
        Resource.opened = 0
        Resource.closed = 0
        providers = ProviderRegistry()
        providers.register(Resource, Resource)
        registry = VIACommandRegistry(
            providers,
            VIASSOTRegistry(Path(temporary_directory.name) / "registry.sqlite3"),
        )
        try:
            registry.register(AsyncModule(), TEST_CONTEXT)
            executor = VIASmartExecutor(registry)
            output = await executor.execute_async("AsyncModule", {"amount": 4})
            self.assertEqual(output.result, 5.0)
            self.assertEqual(Resource.opened, 1)
            self.assertEqual(Resource.closed, 1)
        finally:
            registry.shutdown()
            VIASSOTRegistry.reset_for_testing()
            temporary_directory.cleanup()


if __name__ == "__main__":
    unittest.main()
