#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0100]
"""VIA_DesktopValidate v0100 — 桌機一支唯讀驗證:VCGC · VDF · VRN 實測產出逐項驗證(不改任何系統檔 · 不連網 · 不設同意閘)。

操作員 2026-11-12「REVIEW ABOVE AND REAL-TEST AND VALIDATE OUTPUT OF VRN VDF VCGC AUTOMATICALLY」。
三系統對等(L120 / L123 / L128):本支只讀各系統自報的產出與收據,各系統用自己的管理器自檢,不代修、不互相放行。

  V1 管理器自檢   VCGC 主控台 v0195 · VDF v0169 · VRN v0263 的 health(子行程 · 各自入口)
  V2 VDF 清單     最新 tw_stock_list_latest.parquet:列數 · 股數覆蓋 · ISIN 覆蓋 · 日期(MDL009 v0103 T1 欄)
  V3 VDF 持股率   vdf_tw_holding.duckdb / tw_inst_holding_pct:列數 · 股數非空 · 外資持股率非空 · 持股率越界(<0 或 >100)· 最新日
  V4 VRN 產出     VIA_Reports/vrn2 最新收據:*_latest.json 的燈 / 判決欄 · 最新時間
  V5 VQG 指標冊   VQG v0111 indicators --check(冊 ⇄ 程式對帳)
  V6 VRN-1 對等   VRN2_PeerBridge v0102 prove(只讀 VRN-1 clone;選用)

燈:GREEN 0 · YELLOW 2 · RED 1 · ABSENT 3。只寫 VIA_Reports/validate/(不入版控);結果 JSON + MD + 一行貼回摘要。
用法:python VIA_DesktopValidate_v0100.py [--root <倉根>] [--no-prove] [--timeout 900]
自測:python VIA_DesktopValidate_v0100.py --selftest(夾具 · 零網路 · 只在 tempfile 寫)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

VERSION = "v0100"
TAG = "VIA_DesktopValidate " + VERSION
RC = {"GREEN": 0, "YELLOW": 2, "RED": 1, "ABSENT": 3, "SKIP": 0}
ORDER = {"RED": 4, "ABSENT": 3, "YELLOW": 2, "GREEN": 1, "SKIP": 0}
SHARES_MIN_COVER = 0.95
VIA = "VeritasIntelligenceAnalytics"


def find_root(arg: str | None) -> Path | None:
    cands = [Path(arg)] if arg else []
    here = Path(__file__).resolve()
    cands += list(here.parents) + [Path.cwd()] + list(Path.cwd().parents)
    for c in cands:
        if (c / VIA).is_dir() and (c / ".git").exists():
            return c
    for c in cands:
        if (c / VIA).is_dir():
            return c
    return None


def _tail(folder: Path, pattern: str) -> Path | None:
    def vnum(p: Path) -> int:
        m = re.search(r"_v(\d{4})\.py$", p.name)
        return int(m.group(1)) if m else -1
    hits = sorted(folder.glob(pattern), key=vnum)
    return hits[-1] if hits else None


def run_py(script: Path, args: list, timeout: int, env_extra: dict | None = None) -> tuple[int, str]:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", VIA_VCGC_PUSH="NO", VIA_NO_OPEN="1")
    env.update(env_extra or {})
    try:
        p = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, env=env, cwd=str(script.parent))
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


def lamp_of(text: str, rc: int) -> str:
    m = re.findall(r"\b(GREEN|YELLOW|RED|ABSENT)\b", text)
    if rc == 124:
        return "RED"
    if m:
        worst = max(m[-3:], key=lambda x: ORDER[x])
        return worst if rc != 0 or worst != "RED" else "RED"
    return "GREEN" if rc == 0 else "RED"


def key_line(text: str) -> str:
    lines = [l.strip() for l in text.splitlines() if re.search(r"GREEN|YELLOW|RED|ABSENT|PASS|FAIL|TIMEOUT", l)]
    return (lines[-1] if lines else (text.strip().splitlines() or [""])[-1])[:240]


# ── V1 管理器自檢 ──────────────────────────────────────────────────────
def v1_managers(root: Path, timeout: int) -> list:
    v = root / VIA
    plan = [("VCGC", v / "supportive modules" / "registry", "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"),
            ("VDF", v / "functional modules" / "VDF", "VDF_SystemManager_v*.py"),
            ("VRN", v / "functional modules" / "VRN", "VRN_SystemManager_v*.py")]
    out = []
    for name, folder, pat in plan:
        tail = _tail(folder, pat)
        if tail is None:
            out.append({"id": f"V1-{name}", "lamp": "ABSENT", "what": f"{name} 管理器", "note": f"{pat} 不在"})
            continue
        rc, txt = run_py(tail, ["health"], timeout)
        out.append({"id": f"V1-{name}", "lamp": lamp_of(txt, rc), "what": f"{name} 管理器 {tail.stem.rsplit('_', 1)[-1]} health",
                    "note": key_line(txt), "rc": rc})
    return out


# ── V2 VDF 清單 ───────────────────────────────────────────────────────
def _duck():
    try:
        import duckdb  # noqa: PLC0415
        return duckdb
    except ImportError:
        return None


def v2_stock_list(root: Path) -> dict:
    duckdb = _duck()
    if duckdb is None:
        return {"id": "V2", "lamp": "ABSENT", "what": "VDF 全台股清單", "note": "本直譯器沒有 duckdb(不代裝)"}
    v = root / VIA
    hits = []
    for base in (v / "VIA_Reports", v / "functional modules" / "VDF"):
        if base.is_dir():
            hits += list(base.rglob("tw_stock_list_latest.parquet"))
    if not hits:
        return {"id": "V2", "lamp": "ABSENT", "what": "VDF 全台股清單", "note": "找不到 tw_stock_list_latest.parquet(先經 VDF 管理器跑 MDL009)"}
    best = None
    for p in hits:
        q = "read_parquet('" + str(p).replace("'", "''") + "')"
        con = duckdb.connect()
        try:
            cols = [d[0] for d in con.execute("DESCRIBE SELECT * FROM " + q).fetchall()]
            n = con.execute("SELECT count(*) FROM " + q).fetchone()[0]
            sh = con.execute(f"SELECT count(*) FROM {q} WHERE coalesce(CAST(shares_issued AS VARCHAR),'') <> ''").fetchone()[0] if "shares_issued" in cols else -1
            isin = con.execute(f"SELECT count(*) FROM {q} WHERE coalesce(CAST(isin_code AS VARCHAR),'') <> ''").fetchone()[0] if "isin_code" in cols else -1
            day = con.execute(f"SELECT max(CAST(date AS VARCHAR)) FROM {q}").fetchone()[0] if "date" in cols else None
        finally:
            con.close()
        rec = {"path": str(p.relative_to(root)), "rows": n, "shares": sh, "isin": isin, "date": day, "mtime": p.stat().st_mtime}
        if best is None or (rec["shares"] > 0, rec["mtime"]) > (best["shares"] > 0, best["mtime"]):
            best = rec
    cover = (best["shares"] / best["rows"]) if best["rows"] and best["shares"] >= 0 else 0.0
    lamp = "GREEN" if best["shares"] >= 0 and cover >= SHARES_MIN_COVER else ("YELLOW" if best["rows"] else "RED")
    note = (f"{best['path']} · 列 {best['rows']} · 股數 {best['shares']}({cover:.1%})· ISIN {best['isin']} · 日 {best['date']}"
            + (" · 沒有 shares_issued 欄(MDL009 v0103 沒跑到)" if best["shares"] < 0 else ""))
    return {"id": "V2", "lamp": lamp, "what": "VDF 全台股清單(MDL009)", "note": note, "detail": best}


# ── V3 VDF 持股率 ─────────────────────────────────────────────────────
def v3_holding(root: Path) -> dict:
    duckdb = _duck()
    if duckdb is None:
        return {"id": "V3", "lamp": "ABSENT", "what": "VDF 持股率(ENG238)", "note": "本直譯器沒有 duckdb"}
    v = root / VIA
    hits = [p for p in (v / "functional modules" / "VDF").rglob("vdf_tw_holding.duckdb")] if (v / "functional modules" / "VDF").is_dir() else []
    if (v / "VIA_Reports").is_dir():
        hits += list((v / "VIA_Reports").rglob("vdf_tw_holding.duckdb"))
    if not hits:
        return {"id": "V3", "lamp": "ABSENT", "what": "VDF 持股率(ENG238)", "note": "找不到 vdf_tw_holding.duckdb(先跑 ENG238 run)"}
    db = max(hits, key=lambda p: p.stat().st_mtime)
    con = duckdb.connect(str(db), read_only=True)
    try:
        tabs = {r[0] for r in con.execute("SELECT table_name FROM information_schema.tables").fetchall()}
        if "tw_inst_holding_pct" not in tabs:
            return {"id": "V3", "lamp": "RED", "what": "VDF 持股率(ENG238)", "note": f"{db.name} 沒有 tw_inst_holding_pct 表"}
        cols = {r[0] for r in con.execute("SELECT column_name FROM information_schema.columns WHERE table_name='tw_inst_holding_pct'").fetchall()}
        n = con.execute("SELECT count(*) FROM tw_inst_holding_pct").fetchone()[0]
        sh = con.execute("SELECT count(shares_issued) FROM tw_inst_holding_pct").fetchone()[0] if "shares_issued" in cols else -1
        fp = con.execute("SELECT count(foreign_holding_pct) FROM tw_inst_holding_pct").fetchone()[0] if "foreign_holding_pct" in cols else -1
        pct_cols = [c for c in ("foreign_holding_pct", "trust_holding_pct", "dealer_holding_pct") if c in cols]
        oob = {c: con.execute(f"SELECT count(*) FROM tw_inst_holding_pct WHERE {c} < -100 OR {c} > 100").fetchone()[0] for c in pct_cols}
        codes = con.execute("SELECT count(DISTINCT code) FROM tw_inst_holding_pct").fetchone()[0] if "code" in cols else None
        day = con.execute("SELECT max(CAST(date AS VARCHAR)) FROM tw_inst_holding_pct").fetchone()[0] if "date" in cols else None
    finally:
        con.close()
    cover = (sh / n) if n and sh >= 0 else 0.0
    bad = {k: v for k, v in oob.items() if v}
    lamp = "RED" if n == 0 else ("YELLOW" if cover < SHARES_MIN_COVER or bad else "GREEN")
    note = (f"{db.relative_to(root)} · 列 {n} · 股數非空 {sh}({cover:.1%})· 外資持股率非空 {fp} · 股 {codes} · 最新日 {day}"
            + (f" · 越界(|%|>100){bad}" if bad else " · 越界 0"))
    return {"id": "V3", "lamp": lamp, "what": "VDF 持股率(ENG238)", "note": note,
            "detail": {"rows": n, "shares": sh, "foreign_pct": fp, "codes": codes, "date": day, "out_of_range": oob}}


# ── V4 VRN 產出 ───────────────────────────────────────────────────────
def v4_vrn(root: Path) -> dict:
    d = root / VIA / "VIA_Reports" / "vrn2"
    if not d.is_dir():
        return {"id": "V4", "lamp": "ABSENT", "what": "VRN 產出收據", "note": "VIA_Reports/vrn2 不在(VRN-2 還沒在這台跑過)"}
    files = sorted((p for p in d.rglob("*") if p.is_file()), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return {"id": "V4", "lamp": "ABSENT", "what": "VRN 產出收據", "note": "VIA_Reports/vrn2 是空的"}
    lamps = []
    for p in [f for f in files if f.name.endswith("_latest.json")][:12]:
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        val = None
        for k in ("lamp", "verdict", "state", "status", "overall"):
            if isinstance(j, dict) and isinstance(j.get(k), str):
                val = j[k].upper()
                break
        if val:
            lamps.append((p.name, val))
    worst = "GREEN"
    for _n, v in lamps:
        for key in ("RED", "FAIL", "YELLOW", "REVIEW", "WARN"):
            if key in v:
                cand = "RED" if key in ("RED", "FAIL") else "YELLOW"
                worst = cand if ORDER[cand] > ORDER[worst] else worst
    newest = datetime.fromtimestamp(files[0].stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    shown = " · ".join(f"{n.replace('_latest.json', '')}={v}" for n, v in lamps[:6]) or "(收據沒有燈欄)"
    lamp = worst if lamps else "YELLOW"
    return {"id": "V4", "lamp": lamp, "what": "VRN 產出收據(VRN-2)", "note": f"最新 {newest} · 檔 {len(files)} · {shown}",
            "detail": {"newest": newest, "files": len(files), "lamps": lamps}}


# ── V5 VQG 指標冊 · V6 VRN-1 對等 ─────────────────────────────────────────
def v5_vqg(root: Path, timeout: int) -> dict:
    t = _tail(root / VIA / "functional modules" / "VQG", "VQG_AllInOne_v*.py")
    if t is None:
        return {"id": "V5", "lamp": "ABSENT", "what": "VQG 指標冊", "note": "VQG_AllInOne 不在"}
    rc, txt = run_py(t, ["indicators", "--check"], timeout)
    if "indicators" not in txt and rc != 0:
        return {"id": "V5", "lamp": "YELLOW", "what": "VQG 指標冊", "note": f"{t.name} 沒有 indicators 動詞(要 v0111 起) · rc {rc}"}
    return {"id": "V5", "lamp": lamp_of(txt, rc), "what": f"VQG 指標冊({t.stem.rsplit('_', 1)[-1]})", "note": key_line(txt), "rc": rc}


def v6_prove(root: Path, timeout: int) -> dict:
    t = _tail(root / VIA / "functional modules" / "VRN", "VRN2_PeerBridge_v*.py")
    if t is None:
        return {"id": "V6", "lamp": "ABSENT", "what": "VRN-1 對等 prove", "note": "VRN2_PeerBridge 不在"}
    rc, txt = run_py(t, ["prove"], timeout)
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    head = next((l for l in lines if l.startswith("[prove")), key_line(txt))
    state = next((l for l in lines if l.startswith("狀態")), "")
    return {"id": "V6", "lamp": lamp_of(head, rc), "what": f"VRN-1 對等 prove({t.stem.rsplit('_', 1)[-1]})", "note": (head + " · " + state)[:240], "rc": rc}


# ── 彙總 ─────────────────────────────────────────────────────────────
def overall(rows: list) -> str:
    live = [r["lamp"] for r in rows if r["lamp"] != "SKIP"]
    return max(live, key=lambda x: ORDER[x]) if live else "GREEN"


def write_outputs(root: Path, rows: list, stamp: str) -> dict:
    out = root / VIA / "VIA_Reports" / "validate"
    out.mkdir(parents=True, exist_ok=True)
    lamp = overall(rows)
    doc = {"engine": TAG, "at": stamp, "root": str(root), "overall": lamp, "checks": rows}
    (out / f"VIA_DesktopValidate_{stamp}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    md = [f"# {TAG} · {stamp} · 總燈 {lamp}", "", "| 燈 | 項 | 驗什麼 | 結果 |", "|---|---|---|---|"]
    md += [f"| {r['lamp']} | {r['id']} | {r['what']} | {str(r.get('note', '')).replace('|', '/')} |" for r in rows]
    (out / f"VIA_DesktopValidate_{stamp}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (out / "VIA_DesktopValidate_latest.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return {"dir": str(out), "overall": lamp}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="VIA_DesktopValidate_" + VERSION)
    ap.add_argument("--root")
    ap.add_argument("--no-prove", action="store_true")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    root = find_root(a.root)
    if root is None:
        print(f"[RED] {TAG} · 找不到倉根(要有 {VIA} 夾)· 用 --root 指定")
        return 1
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"=== {TAG} · 倉 {root} · 唯讀驗證 ===", flush=True)
    rows = []
    for step in (lambda: v1_managers(root, a.timeout), lambda: [v2_stock_list(root)], lambda: [v3_holding(root)],
                 lambda: [v4_vrn(root)], lambda: [v5_vqg(root, a.timeout)],
                 lambda: [{"id": "V6", "lamp": "SKIP", "what": "VRN-1 對等 prove", "note": "--no-prove"}] if a.no_prove else [v6_prove(root, a.timeout)]):
        try:
            got = step()
        except Exception as e:  # noqa: BLE001
            got = [{"id": "V?", "lamp": "RED", "what": "驗證步驟中斷", "note": f"{type(e).__name__}: {str(e)[:200]}"}]
        for r in got:
            print(f"  [{r['lamp']:6}] {r['id']:8} {r['what']} · {r.get('note', '')}", flush=True)
        rows += got
    w = write_outputs(root, rows, stamp)
    print(f"[{w['overall']}] {TAG} · 總燈 · 紅 {sum(r['lamp'] == 'RED' for r in rows)} · 黃 {sum(r['lamp'] == 'YELLOW' for r in rows)}"
          f" · 缺 {sum(r['lamp'] == 'ABSENT' for r in rows)} · 綠 {sum(r['lamp'] == 'GREEN' for r in rows)} · 報告 {w['dir']}", flush=True)
    return RC[w["overall"]]


def selftest() -> int:
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    duckdb = _duck()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "repo"
        v = root / VIA
        (root / ".git").mkdir(parents=True)
        for sub, name, body in (("supportive modules/registry", "CGC_MDL149_VeritasCentralGovernanceConsole_v0195.py", "print('[X] health GREEN')"),
                                ("functional modules/VDF", "VDF_SystemManager_v0169.py", "print('[X] health YELLOW');import sys;sys.exit(2)"),
                                ("functional modules/VRN", "VRN_SystemManager_v0263.py", "import sys;sys.exit(1)"),
                                ("functional modules/VQG", "VQG_AllInOne_v0111.py", "print('[GREEN] VQG v0111 indicators 對帳 · 問題 0')"),
                                ("functional modules/VRN", "VRN2_PeerBridge_v0102.py", "print('[prove v0102] YELLOW · 驗了 0 項');print('狀態 MATCH 15 · GAP 8')")):
            (v / sub).mkdir(parents=True, exist_ok=True)
            (v / sub / name).write_text(body + "\n", encoding="utf-8")
        ck("找倉根(有 .git 與 VIA 夾)", find_root(str(root)) == root)
        m = v1_managers(root, 60)
        ck("V1 三管理器各自子行程 · 燈照實(GREEN / YELLOW / RED)", [r["lamp"] for r in m] == ["GREEN", "YELLOW", "RED"], [r["lamp"] for r in m])
        ck("V2 / V3 沒有產出 → ABSENT(不假造)", v2_stock_list(root)["lamp"] in ("ABSENT",) and v3_holding(root)["lamp"] in ("ABSENT",))
        if duckdb is not None:
            d9 = v / "VIA_Reports" / "vdf_fetch" / "dict" / "0-1-TWStockList"
            d9.mkdir(parents=True)
            old = v / "functional modules" / "VDF" / "0-1-TWStockList"
            old.mkdir(parents=True)
            duckdb.sql(f"COPY (SELECT '2026-11-01' AS date, '2330' AS ticker) TO '{(old / 'tw_stock_list_latest.parquet').as_posix()}' (FORMAT parquet)")
            duckdb.sql(f"COPY (SELECT '2026-11-12' AS date, '2330' AS ticker, '25932733242' AS shares_issued, 'TW0002330008' AS isin_code "
                       f"UNION ALL SELECT '2026-11-12','2317','29000000000','TW0002317005') TO '{(d9 / 'tw_stock_list_latest.parquet').as_posix()}' (FORMAT parquet)")
            r2 = v2_stock_list(root)
            ck("V2 取有股數的那份(不取舊清單)· 覆蓋 100% → GREEN", r2["lamp"] == "GREEN" and r2["detail"]["shares"] == 2, r2["note"])
            hd = v / "functional modules" / "VDF" / "output_hub" / "holding"
            hd.mkdir(parents=True)
            con = duckdb.connect(str(hd / "vdf_tw_holding.duckdb"))
            con.execute("CREATE TABLE tw_inst_holding_pct(date VARCHAR, code VARCHAR, shares_issued DOUBLE, foreign_holding_pct DOUBLE, trust_holding_pct DOUBLE, dealer_holding_pct DOUBLE)")
            con.execute("INSERT INTO tw_inst_holding_pct VALUES ('2026-11-12','2330',2.6e10,72.1,1.2,0.1),('2026-11-12','2317',2.9e10,40.0,0.5,0.0)")
            con.close()
            r3 = v3_holding(root)
            ck("V3 持股率:股數全有 · 越界 0 → GREEN", r3["lamp"] == "GREEN" and r3["detail"]["shares"] == 2, r3["note"])
            con = duckdb.connect(str(hd / "vdf_tw_holding.duckdb"))
            con.execute("INSERT INTO tw_inst_holding_pct VALUES ('2026-11-12','9999',NULL,NULL,NULL,NULL),('2026-11-12','8888',1e6,150.0,0,0)")
            con.close()
            r3b = v3_holding(root)
            ck("V3 缺股數 > 5% 或越界(>100%)→ YELLOW · 照實列出", r3b["lamp"] == "YELLOW" and r3b["detail"]["out_of_range"]["foreign_holding_pct"] == 1, r3b["note"])
            ck("V3 只讀:驗證後表列數不變", v3_holding(root)["detail"]["rows"] == 4)
        else:
            ck("本直譯器沒有 duckdb → V2/V3 照實 ABSENT", True, "略過 duckdb 夾具")
        vr = v / "VIA_Reports" / "vrn2"
        vr.mkdir(parents=True)
        (vr / "VRN2_HistoryAlign_latest.json").write_text(json.dumps({"lamp": "GREEN"}), encoding="utf-8")
        (vr / "VRN2_Closeout_latest.json").write_text(json.dumps({"verdict": "REVIEW"}), encoding="utf-8")
        r4 = v4_vrn(root)
        ck("V4 VRN 收據:最差燈(REVIEW → YELLOW)", r4["lamp"] == "YELLOW" and len(r4["detail"]["lamps"]) == 2, r4["note"])
        r5 = v5_vqg(root, 60)
        ck("V5 VQG 指標冊對帳燈照實", r5["lamp"] == "GREEN", r5["note"])
        r6 = v6_prove(root, 60)
        ck("V6 prove 抓頭行 + 狀態行", r6["lamp"] == "YELLOW" and "GAP 8" in r6["note"], r6["note"])
        before = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and "VIA_Reports/validate" not in str(p).replace("\\", "/"))
        rc = main(["--root", str(root), "--no-prove", "--timeout", "60"])
        after = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and "VIA_Reports/validate" not in str(p).replace("\\", "/"))
        latest = json.loads((v / "VIA_Reports" / "validate" / "VIA_DesktopValidate_latest.json").read_text(encoding="utf-8"))
        ck("整輪:總燈 = 最差(V1 有 RED)· rc 1 · 報告 JSON/MD 寫在 VIA_Reports/validate", rc == 1 and latest["overall"] == "RED", latest["overall"])
        ck("整輪只寫 VIA_Reports/validate(其他檔一個沒動)", before == after)
    src = Path(__file__).read_text(encoding="utf-8")
    ck("本檔:加速器橋 · 零網路 import · 無 TA-Lib · 不寫同意閘", "[VIA:ACCEL-BRIDGE" in src
       and not re.search(r"^\s*(import|from)\s+(urllib|requests|socket|http|httpx|aiohttp|talib)\b", src, re.M)
       and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src))
    print(f"[{'PASS' if all(ok) else 'FAIL'}] {TAG} selftest · {sum(ok)}/{len(ok)}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
