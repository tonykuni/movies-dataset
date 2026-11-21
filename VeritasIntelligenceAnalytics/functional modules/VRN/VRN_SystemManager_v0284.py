#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0284 — 薄尾(v0283 以前一字不動):修 PR 715 Codex 兩項 P2

  P2-1 Graphify 格:v0283 只要收據裡出現 "VRN 字樣就亮綠 → Graphify 跑 VRN 失敗 / 跳過(lamp RED / YELLOW / GRAY)也會被當成「有圖」綠 7 天。
       本版讀收據的 systems 清單,只看 VRN 的兩張圖(VRN = functional modules\\VRN2 · VRN_Shared = functional modules\\VRN)各自的燈:
       有綠且沒有紅才綠;有紅 = 紅;都沒出圖 = 黃;收據裡沒有 VRN = 黃;收據讀 UTF-8 帶 BOM 也行(PowerShell 寫的)。
  P2-2 備份:v0283 sha256 對不上時照樣寫 MANIFEST、照樣修剪舊輪 → 壞的那輪變成「最新備份」、還可能把 3 輪好的擠掉。
       本版先複製到 <時戳>.partial 暫存夾,逐檔 sha256 全對上才寫 MANIFEST、改名發布,之後才修剪舊輪;任一檔對不上 → 刪掉暫存夾、
       舊備份一個都不動、回紅。latest_backup 只看已發布(有 MANIFEST、不是 .partial)的輪;--verify 時逐檔重算 sha256(預設只比大小)。
其餘(launch --run 的 TEMP 鉤 · 探針 · 清溢寫夾 · resources 其他六格)全照 v0283。用法同 v0283。
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

import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VRN_SystemManager"
TAG = "VRN_SystemManager v0284"
GRAPH_SYSTEMS = ("VRN", "VRN_Shared")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0284", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_BACKUP_V0283, _LATEST_V0283, _RESOURCES_V0283 = PRIOR.backup_db, PRIOR.latest_backup, PRIOR.resources


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- P2-2 備份:驗過才發布、才修剪
def backup_db(out, dest_base: Path, now=None, keep: int = PRIOR.KEEP_BACKUPS) -> dict:
    if out is None or not Path(out).is_dir():
        return {"lamp": "GRAY", "why": "沒有輸出夾(VRN2_Output_Config.json / VRN2_OUTPUT_DIR 都沒設)· 沒有庫可備"}
    out = Path(out)
    skip = PRIOR._SKIP
    dbs = sorted(p for p in out.rglob("*") if p.is_file() and (p.suffix == ".duckdb" or p.name.endswith(".duckdb.wal"))
                 and not any(s in str(p.relative_to(out)).lower() for s in skip))
    pq = sorted(p for p in out.rglob("*.parquet") if not any(s in str(p.relative_to(out)).lower() for s in skip))
    size = sum(p.stat().st_size for p in dbs) // 2 ** 20
    if not dbs:
        return {"lamp": "GRAY", "why": f"輸出夾沒有 .duckdb(parquet {len(pq)} 支是只增分割檔,不需整檔備份)", "parquet": len(pq)}
    fr = PRIOR.free_mb(dest_base)
    if fr is not None and fr < 2 * size + 64:
        return {"lamp": "YELLOW", "why": f"備份夾空間不夠:要 {size} MB × 2 · 剩 {fr} MB → 這輪不備份", "size_mb": size}
    name = (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    dest = Path(dest_base) / name
    stage = Path(dest_base) / (name + ".partial")
    shutil.rmtree(stage, ignore_errors=True)
    rows, bad = [], []
    try:
        for p in dbs:
            rel = p.relative_to(out)
            t = stage / rel
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, t)
            a, b = PRIOR._sha(p), PRIOR._sha(t)
            rows.append({"path": str(rel), "bytes": p.stat().st_size, "sha256": a})
            if a != b:
                bad.append(str(rel))
    except OSError as exc:
        shutil.rmtree(stage, ignore_errors=True)
        return {"lamp": "RED", "why": f"複製失敗:{type(exc).__name__}: {str(exc)[:120]} · 暫存已刪 · 舊備份不動"}
    if bad:
        shutil.rmtree(stage, ignore_errors=True)
        return {"lamp": "RED", "why": "複本 sha256 對不上:" + " · ".join(bad[:3]) + " · 這輪不發布 · 舊備份不動"}
    man = {"tool": TAG, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "source": str(out), "files": rows,
           "parquet": [{"path": str(p.relative_to(out)), "bytes": p.stat().st_size} for p in pq[:5000]], "parquet_n": len(pq)}
    (stage / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    os.replace(stage, dest)                                   # 驗過才發布
    pub = sorted((d for d in Path(dest_base).iterdir() if d.is_dir() and not d.name.endswith(".partial") and (d / "MANIFEST.json").is_file()),
                 key=lambda d: d.name)
    for d in pub[:-keep]:                                     # 發布之後才修剪;只剪已發布的
        shutil.rmtree(d, ignore_errors=True)
    for d in Path(dest_base).glob("*.partial"):              # 前幾輪當掉留下的暫存
        shutil.rmtree(d, ignore_errors=True)
    return {"lamp": "GREEN", "dest": str(dest), "files": len(rows), "size_mb": size, "parquet_n": len(pq), "kept": min(len(pub), keep)}


def latest_backup(dest_base: Path, verify: bool = False) -> dict:
    base = Path(dest_base)
    ds = sorted((d for d in base.glob("*") if d.is_dir() and not d.name.endswith(".partial") and (d / "MANIFEST.json").is_file()),
                key=lambda d: d.name) if base.is_dir() else []
    if not ds:
        return {"lamp": "GRAY", "line": f"還沒有備份({dest_base})· launch --run 起跑前自動備"}
    d = ds[-1]
    try:
        man = json.loads((d / "MANIFEST.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"lamp": "RED", "line": f"{d.name} MANIFEST 讀不懂"}
    files = man.get("files", [])
    bad = []
    for f in files:
        p = d / f["path"]
        if not p.is_file() or p.stat().st_size != f.get("bytes") or (verify and PRIOR._sha(p) != f.get("sha256")):
            bad.append(f["path"])
    age = (time.time() - (d / "MANIFEST.json").stat().st_mtime) / 3600
    lamp = "RED" if bad else ("YELLOW" if age > PRIOR.STALE_H else "GREEN")
    how = "sha256 逐檔重算" if verify else "大小"
    return {"lamp": lamp, "line": f"{d.name} · 庫檔 {len(files)} · {how}對得上 {len(files) - len(bad)} · {age:.0f}h 前 · 留 {len(ds)} 輪"
            + (f" · 不符 {bad[:2]}" if bad else "") + (" · 過期" if age > PRIOR.STALE_H else "")}


# ---------------------------------------------------------------- P2-1 Graphify 格:看 VRN 那兩張圖自己的燈
def graphify_cell(receipt: Path, now: float | None = None) -> dict:
    p = Path(receipt)
    if not p.is_file():
        return {"lamp": "GRAY", "line": "沒有 Graphify 收據(桌機跑 VIA_Graphify v0101;只解析程式碼 · 不出網 · 一系統一張圖;記憶體不夠它自己跳過)"}
    try:
        g = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {"lamp": "RED", "line": f"{p.name} 讀不懂"}
    sy = g.get("systems") if isinstance(g, dict) else None
    sy = [sy] if isinstance(sy, dict) else (sy if isinstance(sy, list) else [])
    mine = [s for s in sy if isinstance(s, dict) and s.get("system") in GRAPH_SYSTEMS]
    age = ((now or time.time()) - p.stat().st_mtime) / 3600
    if not mine:
        return {"lamp": "YELLOW", "line": f"收據 {age:.0f}h 前 · 裡面沒有 VRN 的圖(Graphify 這輪沒跑 VRN)"}
    lamps = [str(s.get("lamp") or "GRAY").upper() for s in mine]
    parts = []
    for s, l in zip(mine, lamps):
        parts.append(f"{s.get('system')} {l}" + (f" 節點 {s.get('nodes')}" if l == "GREEN" else
                                                  f"({s.get('why') or ('rc ' + str(s.get('rc'))) if s.get('rc') is not None else s.get('why') or ''})"))
    if "RED" in lamps:
        lamp = "RED"
    elif "GREEN" in lamps:
        lamp = "GREEN" if age <= 7 * 24 else "YELLOW"
    else:
        lamp = "YELLOW"                                       # 都跳過 / 都不在 = 沒出圖
    return {"lamp": lamp, "line": f"收據 {age:.0f}h 前 · " + " · ".join(parts) + (" · 過期(> 7 天)" if lamp == "YELLOW" and "GREEN" in lamps else "")
            + " · 圖只做導航,證據仍用骨架卡"}


def resources(root: Path | None = None, verify: bool = False) -> dict:
    root = root or PRIOR.via_root()
    r = _RESOURCES_V0283(root)                                # 其餘六格照 v0283(它叫的 latest_backup 已換成本版)
    r["rows"]["GRAPHIFY"] = graphify_cell(root / "VIA_Reports" / "graphify" / "VIA_Graphify_latest.json")
    if verify:
        r["rows"]["BACKUP"] = latest_backup(PRIOR.backup_base(), verify=True)
    rows = r["rows"]
    lamps = [x["lamp"] for x in rows.values()]
    unproven = [k for k, x in rows.items() if x["lamp"] == "GRAY" and k != "AGENT_MEMORY"]
    r.update(lamp="RED" if "RED" in lamps else "YELLOW" if "YELLOW" in lamps or unproven else "GREEN", unproven=unproven,
             counts={k: lamps.count(k) for k in ("GREEN", "YELLOW", "RED", "GRAY")})
    return r


PRIOR.backup_db = backup_db                                   # v0283 launch_run 叫模組全域 backup_db → 換上本版
PRIOR.latest_backup = latest_backup
PRIOR.resources = resources                                   # v0283 main 的 resources 動詞叫模組全域 → 換上本版


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    PRIOR.TAG = TAG
    if a[:1] == ["resources"] and "--verify" in a:
        r = resources(verify=True)
        if "--json" in a:
            print(json.dumps(r, ensure_ascii=False, indent=1))
        else:
            c = r["counts"]
            print(f"[{TAG}] resources {r['lamp']} · 綠 {c['GREEN']} 黃 {c['YELLOW']} 紅 {c['RED']} 灰 {c['GRAY']}"
                  + (f" · 還沒證據:{' · '.join(r['unproven'])}" if r["unproven"] else ""))
            for k, v in r["rows"].items():
                print(f"  [{v['lamp']:<6}] {k:<12} {v['line']}")
        return {"GREEN": 0, "YELLOW": 2, "GRAY": 2}.get(r["lamp"], 1)
    return PRIOR.main(a)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    keep = (PRIOR.backup_db, PRIOR.latest_backup, PRIOR.resources)
    PRIOR.backup_db, PRIOR.latest_backup, PRIOR.resources = _BACKUP_V0283, _LATEST_V0283, _RESOURCES_V0283
    try:
        rc0 = PRIOR.selftest()
    finally:
        PRIOR.backup_db, PRIOR.latest_backup, PRIOR.resources = keep
    print(f"=== {TAG} · 薄尾自測(Graphify 看 VRN 自己的燈 · 備份驗過才發布;暫存夾 · 零網路)===")
    chk("⓪ 直接前版 %s 自測過" % PRIOR_PATH.name, rc0 == 0, f"rc {rc0}")
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        gp = t / "VIA_Graphify_latest.json"
        gp.write_text(json.dumps({"systems": [{"system": "VRN", "lamp": "RED", "rc": 1}]}), encoding="utf-8")
        chk("① Codex 重現:新鮮收據 VRN lamp RED → 紅(不再當成有圖)", graphify_cell(gp)["lamp"] == "RED", graphify_cell(gp))
        gp.write_text(json.dumps({"systems": [{"system": "VRN", "lamp": "YELLOW", "why": "free RAM 2 GB < 4 GB"},
                                              {"system": "VRN_Shared", "lamp": "GRAY", "why": "folder missing"}]}), encoding="utf-8")
        chk("② VRN 兩張圖都跳過(黃 / 灰)→ 黃(沒出圖)", graphify_cell(gp)["lamp"] == "YELLOW", graphify_cell(gp))
        gp.write_text("﻿" + json.dumps({"systems": {"system": "VRN_Shared", "lamp": "GREEN", "nodes": 31579}}), encoding="utf-8")
        chk("③ 有綠沒紅 → 綠 · 收據帶 BOM、systems 只有一筆(物件)也讀得懂", graphify_cell(gp)["lamp"] == "GREEN", graphify_cell(gp))
        old = time.time() - 9 * 24 * 3600
        os.utime(gp, (old, old))
        chk("④ 綠但收據超過 7 天 → 黃", graphify_cell(gp)["lamp"] == "YELLOW")
        gp.write_text(json.dumps({"systems": [{"system": "VDF", "lamp": "GREEN"}]}), encoding="utf-8")
        chk("⑤ 收據裡只有別的系統 → 黃(VRN 沒圖)", graphify_cell(gp)["lamp"] == "YELLOW")
        chk("⑥ 沒收據 → 灰", graphify_cell(t / "none.json")["lamp"] == "GRAY")
        out = t / "db"
        out.mkdir()
        (out / "vrn.duckdb").write_bytes(b"D" * 4000)
        bb = t / "bk"
        for i in range(1, 4):
            backup_db(out, bb, now=datetime(2026, 11, 22, i, 0, 0))
        good = sorted(d.name for d in bb.iterdir())
        real = PRIOR._sha
        calls = {"n": 0}

        def flaky(p):
            calls["n"] += 1
            return "x" * 64 if calls["n"] % 2 == 0 else real(p)   # 第二次(複本那次)算錯 = sha 對不上
        PRIOR._sha = flaky
        try:
            r = backup_db(out, bb, now=datetime(2026, 11, 22, 9, 0, 0))
        finally:
            PRIOR._sha = real
        chk("⑦ Codex 重現:sha256 對不上 → 紅 · 這輪不發布(沒有 MANIFEST、沒有暫存夾)· 3 輪好的一個都沒被擠掉",
            r["lamp"] == "RED" and sorted(d.name for d in bb.iterdir()) == good and not (bb / "20261122_090000").exists(), (r, sorted(d.name for d in bb.iterdir())))
        chk("⑧ 最新備份仍是上一輪好的 · 綠", latest_backup(bb)["lamp"] == "GREEN" and "20261122_030000" in latest_backup(bb)["line"], latest_backup(bb))
        (bb / "20261122_030000" / "vrn.duckdb").write_bytes(b"X" * 4000)          # 同大小、內容壞了
        chk("⑨ 同大小但內容壞了:預設只比大小 = 綠;--verify 逐檔重算 sha256 = 紅", latest_backup(bb)["lamp"] == "GREEN"
            and latest_backup(bb, verify=True)["lamp"] == "RED", latest_backup(bb, verify=True))
        (bb / "20261122_100000.partial").mkdir()
        (bb / "20261122_100000.partial" / "MANIFEST.json").write_text("{}", encoding="utf-8")
        chk("⑩ 當掉留下的 .partial 不算備份", "100000" not in latest_backup(bb)["line"])
        r2 = backup_db(out, bb, now=datetime(2026, 11, 22, 11, 0, 0))
        names = sorted(d.name for d in bb.iterdir())
        chk("⑪ 下一輪好的發布後才修剪:留 3 輪 · 舊暫存清掉", r2["lamp"] == "GREEN" and len(names) == 3 and names[-1] == "20261122_110000"
            and not any(n.endswith(".partial") for n in names), names)
        root = t / "via"
        (root / "VIA_Reports" / "graphify").mkdir(parents=True)
        (root / "VIA_Reports" / "graphify" / "VIA_Graphify_latest.json").write_text(json.dumps({"systems": [{"system": "VRN", "lamp": "RED", "rc": 1}]}), encoding="utf-8")
        rr = resources(root)
        chk("⑫ resources 的 Graphify 格用本版判法(紅)· 總燈跟著紅", rr["rows"]["GRAPHIFY"]["lamp"] == "RED" and rr["lamp"] == "RED", rr["rows"]["GRAPHIFY"])
    chk("⑬ 換裝:v0283 的 launch_run / resources 動詞叫到的是本版", PRIOR.backup_db is backup_db and PRIOR.resources is resources
        and PRIOR.latest_backup is latest_backup)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    peer = [k for k in ("VIA_FROM_VCGC", "VIA_FROM_VDFSM") if re.search(r"environ(?:\[[\"']%s[\"']\]\s*=|\.setdefault\([\"']%s)" % (k, k), body)]
    chk("⑭ 系統獨立:不設他系統的入口旗標(本檔是 VRN 自己的入口;VCGC 只支援不干涉)", not peer, peer)
    chk("⑮ 加速器橋在;不出網 · 不碰 TA-Lib · 不寫契約檔 / 資產冊", "[VIA:ACCEL-BRIDGE:v0100]" in src and "_via_net()." not in body
        and "talib" not in body.lower() and "VRN_NUMBER_REQUEST" not in body and "Asset_Register" not in body)
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑯ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
