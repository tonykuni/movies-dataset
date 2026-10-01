#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL230_ToolCoverageProbe v0104 — 薄尾:matrix 不跑 server、直接跳出頁(file://)

v0103 → v0104(操作員 R38 2026-10-01:「不跑SERVER直接跳出」):
  matrix 預設就開頁(不必再帶 --open):頁是單檔 HTML,以 file:// 交給系統預設瀏覽器,零 server、零外部資源。
  不開的情況照實印「略過」:帶 --no-open · CI(環境變數 CI / GITHUB_ACTIONS)· VIA_NO_OPEN=1 · 無桌面(容器)。
其餘照 v0103(六面矩陣 · AST 目錄 · 只增帳本 · 淺色緊湊頁)。

用法:
  python CGC_MDL230_ToolCoverageProbe_v0104.py matrix [--no-open] [--ledger] [--json] [--baseline <json>] [--no-pwsh]
  python CGC_MDL230_ToolCoverageProbe_v0104.py --selftest
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

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL230_ToolCoverageProbe"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _prior() -> Path:
    mine = _vnum(Path(__file__))
    older = [p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < mine]
    if not older:
        raise ImportError(f"{STEM}: no version below v{mine:04d}")
    return max(older, key=_vnum)


PRIOR = _prior()
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_v{_vnum(Path(__file__)):04d}", PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)

for _name, _value in vars(_PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value

ENGINE_TAG = f"{STEM} v{_vnum(Path(__file__)):04d}"


def __getattr__(name: str):
    """Every public name of the prior version stays reachable here."""
    return getattr(_PRIOR, name)


_OPEN_PAGE = _PRIOR.open_page            # 先存前版本體,再換掉前版全域(否則自己呼叫自己)


def open_page(path: str) -> str:
    """No server: hand the single-file page to the default browser as file://; say honestly when it is skipped."""
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        return "略過(CI)"
    return _OPEN_PAGE(path)


_PRIOR.open_page = open_page


def wants_open(argv: list) -> bool:
    return "--no-open" not in argv


def selftest() -> int:
    rc = _PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    chk("㊲ 預設開頁;--no-open 才不開", wants_open(["matrix"]) and not wants_open(["matrix", "--no-open"]))
    old = {k: os.environ.get(k) for k in ("CI", "GITHUB_ACTIONS", "VIA_NO_OPEN")}
    try:
        os.environ["CI"] = "true"
        chk("㊳ CI 不開頁(照實印略過,不報錯)", open_page("/nonexistent.html") == "略過(CI)")
        os.environ.pop("CI", None)
        os.environ.pop("GITHUB_ACTIONS", None)
        os.environ["VIA_NO_OPEN"] = "1"
        chk("㊴ VIA_NO_OPEN=1 不開頁", open_page("/nonexistent.html").startswith("略過"))
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    page = (_PRIOR.OUT / "COVERAGE_MATRIX_latest.html")
    if page.is_file():
        t = page.read_text(encoding="utf-8")
        chk("㊵ 頁是單檔:file:// 直開不需 server(零 http(s) 資源 · 零 <script>:沒有腳本就沒有任何連線)",
            "http://" not in t and "https://" not in t and "<script" not in t)
    ok = rc == 0 and all(results)
    print(f"  [{ENGINE_TAG} 不跑 server 直接跳出] 自測 {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if a and a[0] == "matrix" and wants_open(a) and "--open" not in a:
        a.append("--open")
    return _PRIOR.main(a)


if __name__ == "__main__":
    sys.exit(main())
