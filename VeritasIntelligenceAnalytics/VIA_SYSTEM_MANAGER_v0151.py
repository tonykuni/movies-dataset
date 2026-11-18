#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v0150→v0151: a candidate name that still carries a program identifier is not shown.

Seen on PR 629 (2026-11-18, Windows check "bundled Chromium UAT", contract
test_05_primary_names_hide_program_identifiers): two thin tails wrote another
program's number into the first line of their docstring, and the manager used
that line as the display name:
  VDF_ENG238_InstHoldingPct v0102   "... MDL009 ..."   (engine table, E054)
  CGC_MDL149_Integrate              "... ENG085 ..."   (module table, M127)
The body's cleaner (_docstring_formal_name) removes a leading file name but
not a number inside the sentence. This file adds one rule after that cleaner:
if the cleaned name still matches the contract's identifier pattern, there is
no candidate name, and the row shows the existing placeholder
("正式名稱待治理") with the same candidate number. No name is invented here.
Same shape as v0150: the v0148 body runs in this namespace, then the v0149
unplug is applied. v0148, v0149 and v0150 stay on disk (L04). No talib
import, nothing installed, no network.
"""
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
import re as _v151_re
import sys as _v151_sys
from pathlib import Path as _V151Path

_V151_SELF = _V151Path(__file__).resolve()
_V151_BODY = _V151_SELF.parent / "VIA_SYSTEM_MANAGER_v0148.py"
_V151_RETIRED = "VIA_ENG003_TALibEngine"
_V151_REPLACEMENT = "VDF_ENG086_QuantGuardOneBridge"
# the same pattern the MasterControl contract test applies to every primary name
_V151_IDENT = _v151_re.compile(r"(?:ENG|MDL)\d+|[A-Za-z]{2,}_[A-Za-z0-9_]+")

_v151_name = __name__
globals()["__name__"] = "via_system_manager_v0148_body_in_v0151"  # the body's own main block must not fire
globals()["__file__"] = str(_V151_BODY)                             # the body's selftest reads its own source
try:
    exec(compile(_V151_BODY.read_text(encoding="utf-8"), str(_V151_BODY), "exec"), globals())
finally:
    globals()["__name__"] = _v151_name
ENGINE_CANDIDATE_NAMES.pop(_V151_RETIRED, None)  # noqa: F821  (defined by the v0148 body)
_v148_selftest = selftest  # noqa: F821
_v148_docstring_formal_name = _docstring_formal_name  # noqa: F821


def _docstring_formal_name(path, item_type):  # noqa: F811
    """v0148 cleaner, then: a name that still shows a program identifier is no name (None → placeholder row)."""
    name = _v148_docstring_formal_name(path, item_type)
    if name and _V151_IDENT.search(name):
        return None
    return name


def _v151_leaks() -> list:
    """Every engine and module row of the live inventory whose primary name shows a program identifier."""
    atlas = do_list(do_print=False)  # noqa: F821
    rows = _engine_rows(atlas) + _module_rows(atlas)  # noqa: F821
    return [(row["identifier"], row["name"]) for row in rows if _V151_IDENT.search(row["name"])]


def selftest() -> int:  # noqa: F811
    import tempfile
    gone = _V151_RETIRED not in ENGINE_CANDIDATE_NAMES  # noqa: F821
    pointed = _V151_REPLACEMENT in ENGINE_FORMAL_NAMES  # noqa: F821
    surface = all(callable(globals().get(n)) for n in ("do_list", "_build_page", "do_template", "do_ui"))
    with tempfile.TemporaryDirectory() as folder:
        leaky = _V151Path(folder) / "X_ENG900_Sample_v0101.py"
        leaky.write_text('"""X_ENG900_Sample v0101 — 薄尾:股數也讀 MDL009 同輪檔"""\n', encoding="utf-8")
        clean = _V151Path(folder) / "X_ENG901_Sample_v0100.py"
        clean.write_text('"""X_ENG901_Sample v0100 — 三大法人持股率"""\n', encoding="utf-8")
        was = _v148_docstring_formal_name(leaky, "engine")
        dropped = bool(was) and bool(_V151_IDENT.search(was)) and _docstring_formal_name(leaky, "engine") is None
        kept = _docstring_formal_name(clean, "engine") == _v148_docstring_formal_name(clean, "engine") is not None
    leaks = _v151_leaks()
    print(f"  [{'OK' if gone else 'FAIL'}] candidate command {_V151_RETIRED} unplugged (v0149)")
    print(f"  [{'OK' if pointed else 'FAIL'}] pointer is {_V151_REPLACEMENT}")
    print(f"  [{'OK' if surface else 'FAIL'}] do_list / _build_page / do_template / do_ui on the newest manager")
    print(f"  [{'OK' if dropped else 'FAIL'}] a docstring name with a program identifier gives no candidate name (v0148 kept it)")
    print(f"  [{'OK' if kept else 'FAIL'}] a clean docstring name is unchanged")
    print(f"  [{'OK' if not leaks else 'FAIL'}] live inventory: no engine or module primary name shows a program identifier{'' if not leaks else ' · ' + str(leaks[:3])}")
    if not (gone and pointed and surface and dropped and kept and not leaks):
        return 1
    print("=== v0148 body selftest ===")
    return _v148_selftest()


if __name__ == "__main__":
    if "--selftest" in _v151_sys.argv:
        raise SystemExit(selftest())
    raise SystemExit(main())  # noqa: F821
