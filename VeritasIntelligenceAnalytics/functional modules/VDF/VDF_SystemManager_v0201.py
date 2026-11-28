#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0201 — 薄尾(v0200 以前一字不動):PR #777 Codex P1「tidy 把在用的價格倉當成匯出成品搬走」

v0198 tidy 的 runs 類把整個 output_hub/export 搬到 VIA_Reports/vdf/export/legacy_output_hub;但那個夾不只是匯出成品:
  · quote(v0147 _db_lookup)只在 <資料家>/output_hub/export 找 *daily_prices*.csv / *prices_adj*.csv 做離線報價
  · extend(v0148 _store_path / _load_store)在同一夾讀寫累積的 vdf_store_daily_prices.csv
  · ENG118 ExportDesk · ENG055 OmniFetch 也寫這個夾
  搬走後 → 離線報價找不到 · 下一次 extend 從空倉重來(歷史列不見)。我當初只搜了 "export" + output_hub 的寫法,漏了 / 串接的路徑。
本版:
  ① output_hub/export 改列「不搬」(理由寫明在用的讀寫者);計畫裡不再有這一項。
  ② tidy undo <run> --match <字串>:只把來源路徑(正斜線比對)含這個字串的那幾項搬回原位,其餘照留
     (主機 2026-11-28 那一輪已經搬了:tidy undo 20261128T074610Z --match output_hub/export)。
其餘照 v0200。零網路 · 不碰 TA-Lib · 不設同意閘 · 不 import VCGC。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

VERSION = "v0201"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent
KEEP_IN_PLACE = {"output_hub/export": "在用的價格倉與匯出夾(quote 讀 · extend 讀寫 vdf_store_daily_prices.csv · ENG118 / ENG055 寫)"}


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0200
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


V198 = PRIOR.V198
V194 = V198.V194


def _rel(p: str, home: str) -> str:
    a, b = str(p).replace("\\", "/"), str(home).replace("\\", "/").rstrip("/")
    return a[len(b) + 1:] if a.startswith(b + "/") else a


_ORIG_BUILD = V198.build_plan


def build_plan(home: Path, via: Path, code_dir: Path, tails_text: str, stamp: str) -> dict:
    plan = _ORIG_BUILD(home, via, code_dir, tails_text, stamp)
    keep = []
    for it in plan["items"]:
        rel = _rel(it["src"], str(home))
        why = KEEP_IN_PLACE.get(rel)
        if why:
            plan["excluded"].append({"path": rel, "why": why})
        else:
            keep.append(it)
    plan["items"] = keep
    return plan


V198.build_plan = build_plan


def undo_match(run: str, ledger: Path, match: str) -> dict:
    """只把來源含 match(正斜線比對)的那幾項搬回;其餘照留。每搬回一項記一列 undo。"""
    back, skipped = [], []
    rows = [json.loads(x) for x in ledger.read_text(encoding="utf-8").splitlines() if x.strip()] if ledger.is_file() else []
    done = {(r["src"], r["dst"]) for r in rows if r.get("run") == run and r.get("undo")}
    m = match.replace("\\", "/")
    for r in reversed([r for r in rows if r.get("run") == run and not r.get("undo")]):
        if m not in r["src"].replace("\\", "/") or (r["src"], r["dst"]) in done:
            continue
        src, dst = Path(r["src"]), Path(r["dst"])
        if src.exists() or not dst.exists():
            skipped.append({**r, "skip": "原位已有東西" if src.exists() else "目的地不在"})
            continue
        src.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dst), str(src))
        rec = {**r, "undo": True, "match": match, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        with open(ledger, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        back.append(rec)
    return {"back": back, "skipped": skipped}


def cmd_undo_match(args: list) -> int:
    run = args[1] if len(args) > 1 else ""
    match = args[args.index("--match") + 1] if "--match" in args else ""
    via = V194._p("sm_via_root")()
    ledger = V194._p("v73_out")(via) / "TIDY_ledger.jsonl"
    r = undo_match(run, ledger, match)
    print(f"[{TAG}] tidy undo {run} --match {match} · 搬回 {len(r['back'])} · 略過 {len(r['skipped'])}")
    for b in r["back"]:
        print(f"  [搬回] {b['dst']} → {b['src']} · {b['files']} 檔")
    for s in r["skipped"]:
        print(f"  [略過] {s['src']} · {s['skip']}")
    return 0 if r["back"] and not r["skipped"] else 2


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 3 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存夾 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    with tempfile.TemporaryDirectory(prefix="vdf_sm201_") as td:
        d = Path(td)
        home, via = d / "home", d / "via"
        code = via / "functional modules" / "VDF"
        code.mkdir(parents=True)
        oh = home / "output_hub"
        (oh / "export").mkdir(parents=True)
        (oh / "export" / "vdf_store_daily_prices.csv").write_text("ticker,date,close\n2330,2026-11-27,1\n", encoding="utf-8")
        (oh / "ta_factory").mkdir()
        (oh / "ta_factory" / "TA_RUN_1.json").write_text("{}", encoding="utf-8")
        plan = V198.build_plan(home, via, code, "", "T201")
        srcs = [_rel(i["src"], str(home)) for i in plan["items"]]
        chk("T2 (Codex P1)計畫不再搬 output_hub/export · 列在「不搬」並寫明讀寫者 · 其他執行紀錄照搬",
            "output_hub/export" not in srcs and "output_hub/ta_factory" in srcs
            and any(e["path"] == "output_hub/export" and "extend" in e["why"] for e in plan["excluded"]), (srcs, plan["excluded"]))
        ledger = d / "L.jsonl"
        dst_e, dst_t = d / "R" / "export" / "legacy_output_hub", d / "R" / "runs" / "ta_factory"
        for s_, t_ in ((oh / "export", dst_e), (oh / "ta_factory", dst_t)):     # 模擬 v0198 那一輪已經搬走兩項
            t_.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(s_), str(t_))
            with open(ledger, "a", encoding="utf-8") as f:
                f.write(json.dumps({"run": "R1", "cat": "runs", "src": str(s_).replace("/", "\\"), "dst": str(t_), "files": 1, "bytes": 1}) + "\n")
        keep_rows = ledger.read_text(encoding="utf-8")
        rows = [json.loads(x) for x in keep_rows.splitlines()]                # 帳上一列用反斜線、一列用正斜線:比對一律照正斜線
        ledger.write_text("".join(json.dumps({**r, "src": r["src"].replace("\\", "/")}) + "\n" for r in rows), encoding="utf-8")
        r = undo_match("R1", ledger, "output_hub\\export")
        r2 = undo_match("R1", ledger, "output_hub/export")
        chk("T3 undo --match:只搬回 export(價格倉回原位)· ta_factory 照留 · 再跑一次不重複",
            len(r["back"]) == 1 and (oh / "export" / "vdf_store_daily_prices.csv").is_file() and not (oh / "ta_factory").exists()
            and dst_t.is_dir() and not r2["back"] and not r2["skipped"], (r, r2))
    rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    V198.build_plan = build_plan                               # 前版自測後重新裝上本版
    chk("T4 前版 v0200 自測照過(含整條前版鏈)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:2] == ["tidy", "undo"] and "--match" in a:
        return cmd_undo_match(a[1:])
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
