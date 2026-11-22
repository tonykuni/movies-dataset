from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "app" / "VIA_NLP_Control_Center_v8.html"


def main() -> None:
    text = UI.read_text(encoding="utf-8")
    required = {
        "brand_zh": "VIA 天青智流",
        "brand_en": "AzureFlow",
        "light_theme": "--sky-0",
        "drag_input": "拖曳到這裡",
        "mouse_engine_picker": "enginePickerPanel",
        "mouse_output_picker": "outputPickerPanel",
        "checkbox_options": "picker-option",
        "select_all": "data-select-all",
        "clear_all": "data-clear-all",
        "windows_io": "Windows I/O",
        "read_only": "唯讀",
    }
    missing = [name for name, marker in required.items() if marker not in text]
    if missing:
        raise AssertionError(f"missing UI markers: {missing}")
    if '<select id="engineIds"' in text or '<select id="outputFormats"' in text:
        raise AssertionError("legacy native multi-select remains in AzureFlow UI")
    if "input[type=checkbox]" not in text or "checkbox" not in text:
        raise AssertionError("checkbox picker contract is incomplete")
    print({"status": "PASS", "ui": str(UI), "bytes": UI.stat().st_size, "markers": len(required)})


if __name__ == "__main__":
    main()
