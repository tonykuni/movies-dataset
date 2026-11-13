#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_UploadsWorkbench v0102 — v0101 薄尾(v0100 · v0101 一字不改):加速器橋 + 動態進度(@@PROGRESS)。

操作員 2026-11-10:「PS/PY 都要導入加速器 · 現在的 PS/PY 檔也是一樣 · 不卡段 · 動態進度條 · 不動就是指令壞了」。
  ① [VIA:ACCEL-BRIDGE] SuperAccel 加速器橋(與全樹同一塊;缺席零影響)。
  ② 每個階段吐一行 `@@PROGRESS|<pct>|<msg>`(stdout,立即 flush):清點 → 審查包 → xlsx 逐表 → 各系統頁 → 總覽 → 收據。
     PowerShell 端(Invoke-VIA-WorkbenchLocal v0101 · AllInOne 同協定)解析成進度條;導向成逐字稿時也看得到。
  其餘判定 / 輸出 / 邊界全部沿用 v0101(→ v0100)。不連網 · 不執行上傳的程式 · 不寫任何系統的冊 / 號。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import importlib.util
import sys
from pathlib import Path

VERSION = "v0102"
HERE = Path(__file__).resolve().parent
PRIOR_FILE = HERE / "VIA_UploadsWorkbench_v0101.py"

_spec = importlib.util.spec_from_file_location("via_uploads_workbench_v0101", PRIOR_FILE)
P1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P1)  # type: ignore[union-attr]
P0 = P1.prior                                  # v0100 本體(build 在這裡,呼叫的都是它的模組全域)
P0.VERSION = VERSION
P0.ENGINE = f"VIA_UploadsWorkbench_{VERSION}"

_STATE = {"pct": 0.0}


def progress(pct: float, msg: str) -> None:
    _STATE["pct"] = max(_STATE["pct"], min(100.0, float(pct)))
    print(f"@@PROGRESS|{_STATE['pct']:.1f}|{msg}", flush=True)


def _wrap(name: str, before, after=None):
    orig = getattr(P0, name)

    def inner(*a, **kw):
        before(*a, **kw)
        out = orig(*a, **kw)
        if after:
            after(out, *a, **kw)
        return out
    setattr(P0, name, inner)


_N_SHEETS = {"n": 0}
_N_PAGES = {"n": 0}
_wrap("inventory", lambda *a, **k: progress(2, "清點上傳夾 · 逐份 SHA-256"), lambda out, *a, **k: progress(12, f"清點完成 · 正本 {sum(1 for i in out['items'] if i['copies'])}/{len(out['items'])}"))
_wrap("kit_checks", lambda *a, **k: progress(14, "審查包:外部 SHA · 包內 SHA256SUMS(只在記憶體讀)"), lambda out, *a, **k: progress(25, f"審查包 {out.get('sums_ok', '-')}/{out.get('sums', '-')} 相符" if out.get("present") else "審查包沒上傳(略過)"))
_wrap("matrix_from_xlsx", lambda *a, **k: progress(26, "矩陣 xlsx:串流解析 UI_* 九張表"), lambda out, *a, **k: progress(70, f"xlsx 完成 · {sum(len(v) for v in out['rows'].values())} 列"))


def _sheet_before(ref, *a, **k):
    _N_SHEETS["n"] += 1
    progress(26 + min(42, _N_SHEETS["n"] * 3.5), f"xlsx 第 {_N_SHEETS['n']} 張表({ref[1].rsplit('/', 1)[-1]})")


_wrap("sheet_rows", _sheet_before)


def _page_before(lock, site, system, *a, **k):
    _N_PAGES["n"] += 1
    progress(70 + min(22, _N_PAGES["n"] * 4.4), f"出頁 · {system}(鎖定 U/I v0106.4)")


_wrap("render_system", _page_before)
_wrap("render_hub", lambda *a, **k: progress(94, "總覽 index.html(無腳本)"), lambda out, *a, **k: progress(97, "收據 uploads_receipt.json"))


def __getattr__(name: str):
    return getattr(P1, name)


def selftest() -> int:
    rc = P1.selftest()
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _STATE["pct"] = 0.0
        progress(10, "a")
        progress(5, "倒退不准")
        progress(150, "封頂")
    lines = buf.getvalue().splitlines()
    ok_proto = lines == ["@@PROGRESS|10.0|a", "@@PROGRESS|10.0|倒退不准", "@@PROGRESS|100.0|封頂"]
    text = Path(__file__).read_text(encoding="utf-8")
    ok = rc == 0 and ok_proto and "[VIA:ACCEL-BRIDGE" in text and P0.ENGINE.endswith(VERSION)
    print({"engine": P0.ENGINE, "selftest_v0102": "PASS" if ok else "FAIL", "progress_protocol": ok_proto, "prior_rc": rc})
    return 0 if ok else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    progress(1, "啟動 · 加速器橋 " + ("已接" if VIA_ACCEL is not None else "缺席(零影響)"))
    rc = P1.main(argv)
    progress(100, f"完成 rc {rc}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
