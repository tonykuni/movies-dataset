#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VCGC_CommandHub_v0121.py — 薄尾(v0100–v0120 一字不動):退役閘先讀「搬回清單」,清單上的檔一律不退。

操作員 2026-11-26 23:33:「優化功能更新上傳 GITHUB」;承 2026-11-25 VDF 整合時找到的缺口(VDF-REQ054 · VCGC-REQ268):
  退役閘 via-prune 把 19 支舊版判成 CODE_DEAD(只被死碼點名)而列為可退,但這 19 支全部在 11-24 的搬回清單
  `functional modules/VIA_RetiredEngines/RESTORED_20261124.json` 上(現役程式寫死完整檔名);11-26 又搬回 9 支
  (`RESTORED_20261126_vdf.json`,前版用 CHAIN_VERSIONS 拼檔名載入)。照退役閘做會重演同一次重工。

本版只加一道門,判法不改:
  ① 掃描(prune_scan)之後:路徑或檔名出現在任何 `RESTORED_*.json` 的 files[].file 上 → 類別改成 RESTORED
     (不在任何可退類別裡,所以 --prove / --apply 都不會碰),每列帶 restored_by(哪一本清單)。
  ② 搬移(prune_apply)之前:再擋一次(給直接呼叫 prune_apply 的工具用),清單上的檔剔除並回報 skipped_restored。
  清單讀不到或格式不對 → 照舊放行並在報告寫 restored_lists_error(不冒充綠、不中斷)。
用法同 v0120 | --selftest
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

import collections
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0121"
FAMILY = "VCGC_CommandHub"
HERE = Path(__file__).resolve().parent
RESTORED_DIR = Path("functional modules") / "VIA_RetiredEngines"
RESTORED_GLOB = "RESTORED_*.json"
KIND = "RESTORED"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(FAMILY + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def _find_p2(m):
    """沿前版鏈找 v0102(prune_scan / prune_apply / cmd_prune 與指令冊 COMMANDS 都在那一層)。"""
    seen = []
    while m is not None and m not in seen:
        seen.append(m)
        if "COMMANDS" in vars(m) and "SYS_ENTRY" in vars(m):
            return m
        nxt = vars(m).get("PRIOR")
        m = nxt if hasattr(nxt, "__dict__") else None
    raise ImportError("前版鏈上找不到指令冊(v0102 的 COMMANDS / SYS_ENTRY)")


P2 = _find_p2(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _norm(rel: str) -> str:
    return str(rel).replace("\\", "/").strip().lstrip("./")


def restored_index(via: Path) -> tuple[dict, list]:
    """讀 VIA_RetiredEngines/RESTORED_*.json → ({正規化路徑: 清單檔名}, 錯誤清單)。檔名另存一份 'name:<檔名>' 鍵。"""
    idx, errs = {}, []
    d = Path(via) / RESTORED_DIR
    for f in sorted(d.glob(RESTORED_GLOB)) if d.is_dir() else []:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            rows = data.get("files") if isinstance(data, dict) else None
            if not isinstance(rows, list):
                raise ValueError("沒有 files 清單")
            for r in rows:
                rel = _norm(r.get("file", "") if isinstance(r, dict) else r)
                if rel:
                    idx.setdefault(rel, f.name)
                    idx.setdefault("name:" + Path(rel).name, f.name)
        except Exception as e:  # noqa: BLE001
            errs.append(f"{f.name}: {e}")
    return idx, errs


def _hit(idx: dict, rel: str) -> str | None:
    rel = _norm(rel)
    return idx.get(rel) or idx.get("name:" + Path(rel).name)


_PRIOR_SCAN = P2.prune_scan
_PRIOR_APPLY = P2.prune_apply


def prune_scan(via: Path, systems: list[str] | None = None) -> dict:
    """前版掃描 + 搬回清單上的列改成 RESTORED(不可退)。"""
    rep = _PRIOR_SCAN(via, systems)
    if not isinstance(rep, dict) or "error" in rep:
        return rep
    idx, errs = restored_index(via)
    if errs:
        rep["restored_lists_error"] = errs
    by = collections.Counter(rep.get("by_kind") or {})
    n = 0
    for x in rep.get("dead", []):
        src = _hit(idx, x.get("path", ""))
        if src and x.get("kind") != KIND:
            by[x.get("kind")] -= 1
            x["kind_before"], x["kind"], x["restored_by"] = x.get("kind"), KIND, src
            by[KIND] += 1
            n += 1
    if n:
        rep["by_kind"] = {k: v for k, v in by.items() if v}
    rep["restored_guard"] = {"version": VERSION, "lists": sorted(set(v for v in idx.values())), "marked": n}
    return rep


def prune_apply(via: Path, proven: list[dict]) -> dict:
    """搬移前再擋一次:搬回清單上的檔剔除,其餘照前版搬。"""
    idx, errs = restored_index(via)
    keep, skipped = [], []
    for x in proven or []:
        src = _hit(idx, x.get("path", ""))
        (skipped if src else keep).append(dict(x, restored_by=src) if src else x)
    if not keep:
        r = {"moved": 0, "note": "全部在搬回清單上,不搬"}
    else:
        r = _PRIOR_APPLY(via, keep)
    if isinstance(r, dict):
        r["skipped_restored"] = [{"path": x["path"], "restored_by": x["restored_by"]} for x in skipped]
        if errs:
            r["restored_lists_error"] = errs
    return r


P2.prune_scan = prune_scan
P2.prune_apply = prune_apply
if "via-prune" in P2.CMD and "搬回清單" not in P2.CMD["via-prune"].get("help", ""):
    P2.CMD["via-prune"]["help"] += " 搬回清單(VIA_RetiredEngines/RESTORED_*.json)上的檔一律標 RESTORED、不退(v0121)。"


def main(argv: list[str] | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    import contextlib
    import io
    ok = bad = 0

    def chk(name, cond, note=""):
        nonlocal ok, bad
        ok += bool(cond)
        bad += not cond
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}", flush=True)

    with tempfile.TemporaryDirectory() as td:
        via = Path(td)
        d = via / RESTORED_DIR
        d.mkdir(parents=True)
        (d / "RESTORED_20990101.json").write_text(json.dumps({"files": [
            {"file": "functional modules/VDF/engine/VDF_ENGX_Demo_v0101.py", "why": "selftest"}]}), encoding="utf-8")
        (d / "RESTORED_20990102_bad.json").write_text("{not json", encoding="utf-8")
        idx, errs = restored_index(via)
        chk("① 讀得到搬回清單(路徑與檔名兩種鍵)", _hit(idx, "functional modules/VDF/engine/VDF_ENGX_Demo_v0101.py") == "RESTORED_20990101.json"
            and _hit(idx, "VDF_ENGX_Demo_v0101.py") == "RESTORED_20990101.json")
        chk("② 壞清單照實回報、不中斷", len(errs) == 1 and "RESTORED_20990102_bad.json" in errs[0])
        chk("②b Windows 斜線也認得", _hit(idx, "functional modules\\VDF\\engine\\VDF_ENGX_Demo_v0101.py") is not None)

        fake = {"dead": [{"path": "functional modules/VDF/engine/VDF_ENGX_Demo_v0101.py", "kind": "CODE_DEAD"},
                         {"path": "functional modules/VDF/engine/VDF_ENGX_Other_v0101.py", "kind": "UNREF"}],
                "by_kind": {"CODE_DEAD": 1, "UNREF": 1}}
        global _PRIOR_SCAN, _PRIOR_APPLY
        saved = (_PRIOR_SCAN, _PRIOR_APPLY)
        calls = []
        try:
            _PRIOR_SCAN = lambda v, s=None: json.loads(json.dumps(fake))  # noqa: E731
            _PRIOR_APPLY = lambda v, c: (calls.append([x["path"] for x in c]) or {"moved": len(c)})  # noqa: E731
            rep = prune_scan(via)
            kinds = {Path(x["path"]).name: x["kind"] for x in rep["dead"]}
            chk("③ 清單上的列改成 RESTORED,其餘不動", kinds == {"VDF_ENGX_Demo_v0101.py": KIND, "VDF_ENGX_Other_v0101.py": "UNREF"})
            chk("④ by_kind 重算", rep["by_kind"] == {KIND: 1, "UNREF": 1}, f"({rep['by_kind']})")
            chk("⑤ RESTORED 不在任何可退類別", KIND not in set(getattr(PRIOR, "DEFAULT_KINDS", ()) or ()) and KIND not in ("UNREF", "DOC_REF", "SNAP_REF", "REG_REF", "CODE_DEAD"))
            r = prune_apply(via, fake["dead"])
            chk("⑥ 搬移前再擋一次:只搬清單外的", calls == [["functional modules/VDF/engine/VDF_ENGX_Other_v0101.py"]]
                and [x["path"] for x in r["skipped_restored"]] == ["functional modules/VDF/engine/VDF_ENGX_Demo_v0101.py"])
            calls.clear()
            r2 = prune_apply(via, fake["dead"][:1])
            chk("⑦ 全在清單上 → 不叫前版搬移", calls == [] and r2["moved"] == 0)
        finally:
            _PRIOR_SCAN, _PRIOR_APPLY = saved

    real_idx, real_errs = restored_index(HERE)
    chk("⑧ 倉內兩本搬回清單讀得到(11-24 54 列 · 11-26 9 列)", not real_errs and len([k for k in real_idx if not k.startswith("name:")]) >= 63,
        f"({len([k for k in real_idx if not k.startswith('name:')])} 列)")
    chk("⑨ 已掛到退役閘(cmd_prune 會用到本版)", P2.prune_scan is prune_scan and P2.prune_apply is prune_apply)
    chk("⑩ 加速器橋執行時生效", VIA_ACCEL is not None)
    with contextlib.redirect_stdout(io.StringIO()) as pb:
        rc = PRIOR.selftest()
    tl = [l for l in pb.getvalue().splitlines() if "[計]" in l]
    chk("⑪ 前版自測", rc == 0, f"({tl[-1].strip() if tl else rc})")
    print(f"  [計] {FAMILY} {VERSION} 自測 OK {ok} · FAIL {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
