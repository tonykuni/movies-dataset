"""Optional-dependency registry.

The extractor is fully functional with the Python standard library alone.
Every third-party package is optional and only *upgrades* the experience.
`doctor()` reports what is installed and what each package would add.
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib
from functools import lru_cache

#: name -> (import name, what it adds when present)
OPTIONAL_LIBS = {
    "charset_normalizer": ("charset_normalizer", "high-accuracy encoding detection for CSV/text"),
    "chardet":            ("chardet",            "fallback encoding detection"),
    "ftfy":               ("ftfy",               "industrial-strength mojibake (亂碼) repair"),
    "pandas":             ("pandas",             "DataFrame output, richer table exports"),
    "openpyxl":           ("openpyxl",           "preferred .xlsx engine (styles, cached formula values)"),
    "xlrd":               ("xlrd",               "legacy binary .xls support"),
    "python-docx":        ("docx",               "alternate .docx engine for cross-checking"),
    "docx2python":        ("docx2python",        "alternate .docx engine for cross-checking"),
    "datacompy":          ("datacompy",          "professional table-comparison reports"),
    "msoffcrypto-tool":   ("msoffcrypto",        "open password-protected Office files"),
}


@lru_cache(maxsize=None)
def has(name: str) -> bool:
    """True if the optional library *name* (key of OPTIONAL_LIBS) is importable."""
    import_name = OPTIONAL_LIBS.get(name, (name,))[0]
    try:
        importlib.import_module(import_name)
        return True
    except Exception:
        return False


def load(name: str):
    """Import and return the optional module, or None when unavailable."""
    if not has(name):
        return None
    return importlib.import_module(OPTIONAL_LIBS.get(name, (name,))[0])


def doctor() -> dict:
    """Return {package: {available, adds, version}} for every optional lib."""
    out = {}
    for name, (import_name, adds) in OPTIONAL_LIBS.items():
        info = {"available": has(name), "adds": adds, "version": None}
        if info["available"]:
            mod = importlib.import_module(import_name)
            info["version"] = getattr(mod, "__version__", "?")
        out[name] = info
    return out


def doctor_text() -> str:
    lines = ["Optional libraries (the tool works without all of them):", ""]
    for name, info in doctor().items():
        mark = "[x]" if info["available"] else "[ ]"
        ver = f" ({info['version']})" if info["version"] else ""
        lines.append(f"  {mark} {name:<20}{ver:<12} -> {info['adds']}")
    return "\n".join(lines)
