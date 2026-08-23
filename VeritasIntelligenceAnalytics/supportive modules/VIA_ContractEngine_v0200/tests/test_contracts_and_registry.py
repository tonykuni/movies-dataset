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

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import Field

from via_interface_engine import (
    ModuleContext,
    ModuleManifest,
    ProviderRegistry,
    VIACommandRegistry,
    VIAInputModel,
    VIAModuleABC,
    VIAOutputModel,
    VIASSOTRegistry,
)
from via_interface_engine.exceptions import (
    ContractInspectionError,
    DependencyResolutionError,
    DuplicateModuleError,
    LifecycleError,
    ManifestValidationError,
)


# def TEST PARAMETERS
TEST_CONTEXT = ModuleContext(run_id="RUN_TEST", subsystem="TEST", config={"safe": True})


class SimpleInput(VIAInputModel):
    value: int = Field(ge=1, le=10)


class SimpleOutput(VIAOutputModel):
    doubled: int


class SimpleModule(VIAModuleABC):
    __manifest__ = {
        "name": "SimpleModule",
        "version": "1.0.0",
        "author": "VIA",
        "dependencies": [],
    }

    def __init__(self) -> None:
        self.setup_called = False
        self.teardown_called = False

    def setup(self, context: ModuleContext) -> None:
        self.setup_called = True

    def health_check(self) -> bool:
        return self.setup_called and not self.teardown_called

    def execute(self, input_data: SimpleInput) -> SimpleOutput:
        return SimpleOutput(doubled=input_data.value * 2)

    def teardown(self) -> None:
        self.teardown_called = True


class ChildModule(SimpleModule):
    __manifest__ = ModuleManifest(
        name="ChildModule",
        version="1.0.0",
        author="VIA",
        dependencies=("SimpleModule",),
    )


class BadManifestModule(SimpleModule):
    __manifest__ = {"name": "bad name", "version": "not-version", "author": ""}


class UntypedModule(SimpleModule):
    __manifest__ = {"name": "UntypedModule", "version": "1.0.0", "author": "VIA"}

    def execute(self, input_data) -> SimpleOutput:  # type: ignore[no-untyped-def]
        return SimpleOutput(doubled=1)


class CycleModuleA(SimpleModule):
    __manifest__ = ModuleManifest(
        name="CycleModuleA",
        version="1.0.0",
        dependencies=("CycleModuleB",),
    )


class CycleModuleB(SimpleModule):
    __manifest__ = ModuleManifest(
        name="CycleModuleB",
        version="1.0.0",
        dependencies=("CycleModuleA",),
    )


class UnhealthyModule(SimpleModule):
    __manifest__ = ModuleManifest(name="UnhealthyModule", version="1.0.0")

    def health_check(self) -> bool:
        return False


class RegistryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        VIASSOTRegistry.reset_for_testing()
        self.providers = ProviderRegistry()
        self.ssot = VIASSOTRegistry(
            Path(self.temporary_directory.name) / "registry.sqlite3"
        )
        self.registry = VIACommandRegistry(self.providers, self.ssot)

    def tearDown(self) -> None:
        self.registry.shutdown()
        VIASSOTRegistry.reset_for_testing()
        self.temporary_directory.cleanup()

    def test_register_calls_setup_and_schema_is_self_describing(self) -> None:
        module = SimpleModule()
        descriptor = self.registry.register(module, TEST_CONTEXT)
        self.assertTrue(module.setup_called)
        self.assertEqual(descriptor.input_model, SimpleInput)
        catalog = self.registry.schema_catalog()
        self.assertEqual(catalog["commands"][0]["module_name"], "SimpleModule")
        self.assertIn("properties", catalog["commands"][0]["input_schema"])
        self.assertRegex(
            descriptor.resource_urn,
            r"^VIA-MOD-PY-SIMPLEMODULE-\d{8}-\d{4,}$",
        )
        self.assertEqual(self.registry.get(descriptor.resource_urn), descriptor)

    def test_duplicate_manifest_name_is_rejected(self) -> None:
        self.registry.register(SimpleModule(), TEST_CONTEXT)
        with self.assertRaises(DuplicateModuleError):
            self.registry.register(SimpleModule(), TEST_CONTEXT)

    def test_invalid_manifest_is_rejected_before_setup(self) -> None:
        module = BadManifestModule()
        with self.assertRaises(ManifestValidationError):
            self.registry.register(module, TEST_CONTEXT)
        self.assertFalse(module.setup_called)

    def test_untyped_execute_parameter_is_rejected(self) -> None:
        with self.assertRaises(ContractInspectionError):
            self.registry.register(UntypedModule(), TEST_CONTEXT)

    def test_dependency_must_be_registered_first(self) -> None:
        with self.assertRaises(DependencyResolutionError):
            self.registry.register(ChildModule(), TEST_CONTEXT)

    def test_dependent_blocks_parent_unload(self) -> None:
        parent = SimpleModule()
        child = ChildModule()
        self.registry.register(parent, TEST_CONTEXT)
        self.registry.register(child, TEST_CONTEXT)
        with self.assertRaises(DependencyResolutionError):
            self.registry.unregister("SimpleModule")
        self.registry.unregister("ChildModule")
        self.registry.unregister("SimpleModule")
        self.assertTrue(parent.teardown_called)
        self.assertTrue(child.teardown_called)

    def test_tool_catalog_uses_same_input_schema(self) -> None:
        self.registry.register(SimpleModule(), TEST_CONTEXT)
        tool = self.registry.tool_catalog()[0]
        self.assertEqual(tool["function"]["name"], "SimpleModule")
        self.assertIn("value", tool["function"]["parameters"]["properties"])
        self.assertTrue(tool["function"]["x-via-resource-urn"].startswith("VIA-MOD-PY-"))

    def test_batch_registration_uses_dependency_topology(self) -> None:
        descriptors = self.registry.register_many(
            [ChildModule(), SimpleModule()],
            lambda manifest: ModuleContext(
                run_id=f"RUN_{manifest.name}",
                subsystem="TEST",
            ),
        )
        self.assertEqual(
            [item.manifest.name for item in descriptors],
            ["SimpleModule", "ChildModule"],
        )
        ordered_names = [
            self.ssot.resolve(resource_urn).manifest.name
            for resource_urn in self.registry.topological_order()
        ]
        self.assertEqual(ordered_names, ["SimpleModule", "ChildModule"])

    def test_same_source_identity_reuses_immutable_urn(self) -> None:
        first = self.registry.register(SimpleModule(), TEST_CONTEXT)
        self.registry.unregister(first.resource_urn)
        second = self.registry.register(SimpleModule(), TEST_CONTEXT)
        self.assertEqual(first.resource_urn, second.resource_urn)

    def test_batch_cycle_is_rejected_before_setup(self) -> None:
        first = CycleModuleA()
        second = CycleModuleB()
        with self.assertRaises(DependencyResolutionError):
            self.registry.register_many(
                [first, second],
                lambda manifest: TEST_CONTEXT,
            )
        self.assertFalse(first.setup_called)
        self.assertFalse(second.setup_called)

    def test_initial_health_failure_never_reaches_ready(self) -> None:
        with self.assertRaises(LifecycleError):
            self.registry.register(UnhealthyModule(), TEST_CONTEXT)
        record = self.ssot.resolve("UnhealthyModule")
        self.assertNotEqual(record.state.value, "READY")


if __name__ == "__main__":
    unittest.main()
