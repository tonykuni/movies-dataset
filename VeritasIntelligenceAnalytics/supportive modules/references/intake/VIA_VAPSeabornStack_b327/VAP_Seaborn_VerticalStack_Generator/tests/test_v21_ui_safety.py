from __future__ import annotations

import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import vap_seaborn_stack_ui as ui


class MainThreadOnlyVariable:
    def __init__(self, value: str) -> None:
        self.value = value
        self.main_thread = threading.get_ident()
        self.read_count = 0

    def get(self) -> str:
        if threading.get_ident() != self.main_thread:
            raise AssertionError("Tk-style variable was read outside the UI thread")
        self.read_count += 1
        return self.value


class VAPV21UISafetyTests(unittest.TestCase):
    def test_render_worker_receives_resolved_config_path(self) -> None:
        config_variable = MainThreadOnlyVariable("examples/demo_stack.json")
        state = {"variables": {"config": config_variable}}
        captured: dict[str, object] = {}

        def capture_task(_state, _name, _status, function) -> None:
            captured["function"] = function

        with patch.object(ui, "start_async_task", side_effect=capture_task), patch.object(
            ui,
            "render_stack",
            side_effect=lambda path: path,
        ):
            ui.start_render_stack(state)
            result: list[Path] = []
            worker = threading.Thread(target=lambda: result.append(captured["function"]()))
            worker.start()
            worker.join(timeout=5)

        self.assertFalse(worker.is_alive())
        self.assertEqual(config_variable.read_count, 1)
        self.assertEqual(result, [Path("examples/demo_stack.json").resolve()])


if __name__ == "__main__":
    unittest.main()
