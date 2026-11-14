#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_DataIntegrate v0101 — v0100 薄尾(v0100 留著一字不改):掃描不再走整棵樹 · 只問像 VRN-2 資料庫的檔。

v0100 的 scan 用 Path.rglob("*") 再過濾深度 → 輸出夾的上一層若是 OneDrive 根目錄,會把整個 OneDrive 走一遍(慢 · 同步軟體可能被喚醒),
而且任何 CSV 都會被當候選(它一定會挑一本「最像」的冊)→ 不相干的 CSV 也來問使用者。v0101:
  ① 有深度上限的 os.scandir 走訪:輸出夾 2 層 · 輸出夾的上一層 1 層 · legacy_in 3 層 · VRN2_INTEGRATE_DIRS / --dirs 2 層;
     不進隱藏夾 / 符號連結 / VRN2 · parquet · vdf · integrated · originals · node_modules · .git;每個夾最多看 20,000 個項目(超過照實記 truncated)。
  ② 像不像 VRN-2 的資料庫:對到的欄 ≥ 3 · 至少有一個身分欄(FILENAME / TICKER)· FinancialData 還要有 ITEM 與 VALUE;不像 → 記在 skipped(not_vrn2_like)不問。
  其餘(讀檔 · 欄位對齊 · apply 不刪原檔 · dismiss 記 sha)全照 v0100。apply 在沒有收據時會呼叫的 scan 也改綁本版。
動詞同 v0100:scan [--v2] [--dirs a;b] · apply [--only 1,3] [--move] · dismiss · --selftest
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0101"
DISPLAY_NAME = "VRN2_DataIntegrate"
TAG = "資料整合 v0101"
PRIOR_NAME = "VRN2_DataIntegrate_v0100.py"
HERE = Path(__file__).resolve().parent
SKIP_DIRS = {"VRN2", "VRN2_Workbench_assets", "vdf", "parquet", "integrated", "originals", "node_modules", ".git", "__pycache__", "$RECYCLE.BIN", "System Volume Information"}
MAX_ENTRIES = 20000
DEPTH = {"output": 2, "output_parent": 1, "legacy_in": 3, "env": 2, "arg": 2}


def _prior():
    for path in (HERE / PRIOR_NAME, HERE.parent / "v146" / "new" / PRIOR_NAME):
        if path.is_file():
            spec = importlib.util.spec_from_file_location("vrn2_dataintegrate_prior_v0100", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))


PRIOR = _prior()
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
PRIOR.TAG = TAG


def scan_dirs(v2: Path, dirs: list | None) -> list:
    """[(夾, 深度, 來源)] · 去重(大小寫不分 · resolve)· 只留存在的夾。"""
    out = []
    cfg = PRIOR.read_config(v2)
    if cfg.get("output_dir"):
        od = Path(cfg["output_dir"])
        out += [(od, DEPTH["output"], "輸出夾"), (od.parent, DEPTH["output_parent"], "輸出夾的上一層")]
    out.append((Path(v2) / "legacy_in", DEPTH["legacy_in"], "legacy_in"))
    for d in (os.environ.get("VRN2_INTEGRATE_DIRS") or "").split(";"):
        if d.strip():
            out.append((Path(d.strip()), DEPTH["env"], "VRN2_INTEGRATE_DIRS"))
    for d in dirs or []:
        out.append((Path(d), DEPTH["arg"], "--dirs"))
    seen, res = set(), []
    for d, depth, src in out:
        try:
            key = str(d.resolve()).lower()
        except OSError:
            key = str(d).lower()
        if key not in seen and d.is_dir():
            seen.add(key)
            res.append((d, depth, src))
    return res


def walk(root: Path, depth: int, limit: int = MAX_ENTRIES) -> tuple:
    """深度有上限的走訪:回 (候選檔清單, 看過的項目數, 是否截斷)。depth 1 = 只看夾裡的檔。"""
    found, seen, truncated = [], 0, False
    stack = [(Path(root), 1)]
    while stack:
        folder, level = stack.pop()
        try:
            with os.scandir(folder) as it:
                entries = sorted(it, key=lambda e: e.name)
        except OSError:
            continue
        for e in entries:
            seen += 1
            if seen > limit:
                return found, seen, True
            name = e.name
            if name.startswith(".") or name.startswith("~$"):
                continue
            try:
                if e.is_symlink():
                    continue
                if e.is_dir(follow_symlinks=False):
                    if level < depth and name not in SKIP_DIRS:
                        stack.append((Path(e.path), level + 1))
                    continue
                if not e.is_file(follow_symlinks=False):
                    continue
            except OSError:
                continue
            p = Path(e.path)
            if p.suffix.lower() in PRIOR.EXTS and not PRIOR._is_ours(p):
                found.append(p)
    return found, seen, truncated


def vrn2_like(al: dict) -> tuple:
    """對齊結果像不像 VRN-2 的冊:(是否, 理由)。"""
    used = {t for t in (al.get("mapping") or {}).values() if t}
    book = al.get("target_book")
    if len(used) < 3:
        return False, "只對到 %d 欄(要 ≥ 3)" % len(used)
    if not ({"FILENAME", "TICKER"} & used):
        return False, "沒有身分欄(FILENAME / TICKER)"
    if book == "FinancialData" and not {"ITEM", "VALUE"} <= used:
        return False, "年度數據缺 ITEM 或 VALUE"
    return True, "對到 %d 欄 · %s" % (len(used), book)


def scan(v2: Path, dirs: list | None = None, depth: int = 2) -> dict:
    v2 = Path(v2)
    prior = PRIOR.read_receipt(v2)
    done = {a.get("original_sha256") for a in (prior.get("applied") or []) if a.get("original_sha256")} | set(prior.get("done_sha256") or [])
    dismissed = set() if os.environ.get("VRN2_INTEGRATE_RESCAN") == "1" else ({c.get("sha256") for c in (prior.get("candidates") or []) if prior.get("state") == "DISMISSED" and c.get("sha256")} | set(prior.get("dismissed_sha256") or []))
    rec = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "scan", "at": PRIOR.now(), "state": "NONE", "scanned_dirs": [], "candidates": [], "skipped": [], "temp_dir": str(PRIOR.temp_root() / "VRN2_Integrate_<時間>"),
           "done_sha256": sorted(done), "dismissed_sha256": sorted(dismissed), "applied": prior.get("applied") or [], "integrated_dir": prior.get("integrated_dir"),
           "last_apply_at": prior.get("at") if prior.get("state") == "APPLIED" else prior.get("last_apply_at")}
    seen_paths = set()
    for d, dmax, src in scan_dirs(v2, dirs):
        found, n_seen, truncated = walk(d, dmax)
        rec["scanned_dirs"].append({"dir": str(d), "depth": dmax, "from": src, "entries": n_seen, "truncated": truncated})
        for p in found:
            try:
                key = str(p.resolve()).lower()
            except OSError:
                key = str(p).lower()
            if key in seen_paths:
                continue
            seen_paths.add(key)
            if len(rec["candidates"]) >= PRIOR.MAX_CANDIDATES:
                break
            kind = PRIOR.EXTS[p.suffix.lower()]
            if p.suffix.lower() == ".csv" and re.search(r"\s-\s(sheet|工作表)\s*\d*\.csv$", p.name, re.I):
                kind = "Google Sheet 匯出 CSV"
            if p.suffix.lower() == ".gsheet":
                rec["candidates"].append({"path": str(p), "kind": kind, "rows": None, "readable": False, "note": "Google Sheet 捷徑:請在 Google Sheets 用「檔案 › 下載 › CSV」匯出後放同一夾再掃描", "bytes": p.stat().st_size})
                continue
            try:
                if p.stat().st_size > PRIOR.MAX_BYTES:
                    rec["skipped"].append({"path": str(p), "why": "> 200 MB"})
                    continue
                header, rows, note = PRIOR.read_any(p)
            except Exception as error:  # noqa: BLE001
                rec["skipped"].append({"path": str(p), "why": "%s: %s" % (type(error).__name__, str(error)[:120])})
                continue
            if not header or len(rows) < 1:
                rec["skipped"].append({"path": str(p), "why": note or "沒有資料列"})
                continue
            al = PRIOR.align_columns(header, rows)
            like, why_like = vrn2_like(al)
            if not like:
                rec["skipped"].append({"path": str(p), "why": "not_vrn2_like · " + why_like})
                continue
            sha = PRIOR.sha256_file(p)
            if sha in done:
                rec["skipped"].append({"path": str(p), "why": "已整合過(同內容)· 不再問"})
                continue
            if sha in dismissed:
                rec["skipped"].append({"path": str(p), "why": "使用者上次選「不要」(同內容)· 不再問;VRN2_INTEGRATE_RESCAN=1 或 Workbench 重新掃描才再問"})
                continue
            st = p.stat()
            rec["candidates"].append({"path": str(p), "kind": kind, "bytes": st.st_size, "mtime": PRIOR._dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"), "sha256": sha,
                                      "rows_sampled": len(rows), "columns": header, "read_note": note, "readable": True, "why_like": why_like, **al})
    n = len([c for c in rec["candidates"] if c.get("readable")])
    n_unlike = sum(1 for x in rec["skipped"] if str(x.get("why", "")).startswith("not_vrn2_like"))
    if n:
        rec["state"] = "PENDING_USER"
        rec["prompt"] = "偵測到 %d 份舊資料庫(%s)。要不要進行資料整合?整合會依對齊表建立新的整合檔(Parquet / JSON / CSV),原有資料在整合成功前絕不刪除;成功後原檔複製到 TEMP 由你自行處理。" % (n, " · ".join(sorted({c["kind"] for c in rec["candidates"] if c.get("readable")})))
        rec["lamp"] = "YELLOW"
        rec["why"] = "候選 %d 份 · 等使用者決定(Workbench:整合 / 不要)" % n + (" · 不像 VRN-2 資料庫略過 %d 份" % n_unlike if n_unlike else "")
    else:
        rec["state"] = "APPLIED" if (rec["applied"] and not rec["candidates"]) else "NONE"
        rec["lamp"] = "GREEN" if rec["state"] == "APPLIED" else "GRAY"
        n_skip = sum(1 for x in rec["skipped"] if "不再問" in str(x.get("why", "")))
        rec["why"] = ("已整合 %d 份(同內容不再問)· 沒有新的舊資料庫" % len(rec["applied"])) if rec["state"] == "APPLIED" else (
            "掃了 %d 個夾沒有新的舊資料庫(csv / xlsx / parquet / json)" % len(rec["scanned_dirs"]) + (" · 略過 %d 份(已整合 / 上次不要)" % n_skip if n_skip else "")
            + (" · 不像 VRN-2 資料庫 %d 份" % n_unlike if n_unlike else "") + ("" if not rec["candidates"] else " · %d 份 Google Sheet 捷徑要先匯出 CSV" % len(rec["candidates"])))
    if any(d.get("truncated") for d in rec["scanned_dirs"]):
        rec["why"] += " · 有夾項目超過 %d 個只看前段(truncated)" % MAX_ENTRIES
    return PRIOR._write(v2, rec)


PRIOR.scan = scan          # v0100 的 apply() 沒有收據時叫的 scan → 本版
apply = PRIOR.apply
dismiss = PRIOR.dismiss
read_receipt = PRIOR.read_receipt


def selftest() -> int:
    bad = []

    def chk(label, cond):
        PRIOR.say(("[PASS] " if cond else "[FAIL] ") + label)
        if not cond:
            bad.append(label)

    with tempfile.TemporaryDirectory(prefix="vrn2-integ101-") as td:
        root = Path(td)
        v2 = root / "VIA_Reports" / "vrn2"
        (v2 / "output").mkdir(parents=True)
        od = root / "OneDrive" / "VRN2_out"
        od.mkdir(parents=True)
        (v2 / "VRN2_Output_Config.json").write_text(json.dumps({"output_dir": str(od)}), encoding="utf-8")
        # 輸出夾:一份像 VRN-2 的基本資料(Google Sheet 匯出)+ 一份不相干的 CSV
        (od / "舊基本資料 - Sheet1.csv").write_text("Ticker,Date,Broker,Target Price,Rating\n2330,2025-10-01,CLSA,1200,BUY\n", encoding="utf-8-sig")
        (od / "家用記帳.csv").write_text("日期,項目,金額\n2025-01-01,午餐,120\n", encoding="utf-8-sig")
        (od / "VRN2").mkdir()
        (od / "VRN2" / "x.csv").write_text("Ticker,Date,Broker\n2330,2025-10-01,A\n", encoding="utf-8")
        # 上一層(OneDrive 根):深度 1 只看這一層的檔;深層的不看
        deep = root / "OneDrive" / "a" / "b"
        deep.mkdir(parents=True)
        (deep / "深層 - Sheet1.csv").write_text("Ticker,Date,Broker,Target Price\n2454,2025-10-02,KGI,1300\n", encoding="utf-8-sig")
        (root / "OneDrive" / "根目錄財報.csv").write_text("代號,年度,項目,金額\n2330,2024A,營收,999\n", encoding="utf-8-sig")
        for i in range(30):
            (root / "OneDrive" / ("雜檔%02d.txt" % i)).write_text("x", encoding="utf-8")
        r = scan(v2)
        names = sorted(Path(c["path"]).name for c in r["candidates"])
        unlike = [s for s in r["skipped"] if str(s.get("why", "")).startswith("not_vrn2_like")]
        chk("① 只問像 VRN-2 的:輸出夾的基本資料 + 上一層的財報 → 2 份;家用記帳(沒身分欄)略過 not_vrn2_like;VRN2 子夾不進;深層(上一層 + 2)不看", names == ["根目錄財報.csv", "舊基本資料 - Sheet1.csv"] and len(unlike) == 1 and "家用記帳" in unlike[0]["path"] and r["state"] == "PENDING_USER")
        dirs = {Path(d["dir"]).name: d for d in r["scanned_dirs"]}
        chk("② 走訪深度:輸出夾 2 · 上一層 1 · legacy_in 不存在不列 · 每夾記看過幾項", dirs["VRN2_out"]["depth"] == 2 and dirs["OneDrive"]["depth"] == 1 and dirs["OneDrive"]["entries"] >= 32 and "legacy_in" not in dirs)
        found, n_seen, trunc = walk(root / "OneDrive", 5, limit=10)
        chk("③ 項目上限:超過 limit 就停並標 truncated", trunc and n_seen == 11)
        chk("④ vrn2_like:對到 2 欄 → 否 · 沒身分欄 → 否 · 年度數據缺 VALUE → 否 · 正常 → 是", not vrn2_like({"mapping": {"a": "ITEM", "b": "VALUE"}, "target_book": "FinancialData"})[0] and not vrn2_like({"mapping": {"a": "ITEM", "b": "VALUE", "c": "PERIOD"}, "target_book": "FinancialData"})[0]
            and not vrn2_like({"mapping": {"a": "TICKER", "b": "ITEM", "c": "PERIOD"}, "target_book": "FinancialData"})[0] and vrn2_like({"mapping": {"a": "TICKER", "b": "ITEM", "c": "VALUE"}, "target_book": "FinancialData"})[0])
        os.environ["VRN2_INTEGRATE_TEMP"] = str(root / "temp")
        before = {p.name: PRIOR.sha256_file(p) for p in od.glob("*.csv")}
        r2 = apply(v2)
        chk("⑤ apply 走 v0100(原檔不刪 · TEMP 副本)· 2 份 APPLIED · 原檔 sha 不變", r2["state"] == "APPLIED" and len(r2["applied"]) == 2 and before == {p.name: PRIOR.sha256_file(p) for p in od.glob("*.csv")} and all(a["original_in_place"] for a in r2["applied"]))
        r3 = scan(v2)
        chk("⑥ 再掃:已整合的不再問 → APPLIED 綠 · 家用記帳仍只是略過", r3["state"] == "APPLIED" and not r3["candidates"] and any(str(s.get("why", "")).startswith("not_vrn2_like") for s in r3["skipped"]))
        os.environ.pop("VRN2_INTEGRATE_TEMP", None)
        (v2 / "VRN2_Integrate_latest.json").unlink()
        (v2 / "VRN2_Output_Config.json").unlink()
        r4 = apply(v2)
        chk("⑦ 沒有收據時 apply 叫的 scan 是本版(收據 engine = v0101)· 沒有輸出夾 → NONE", "v0101" in r4.get("engine", "") and r4["state"] == "NONE")
    PRIOR.say("[%s] %s %s --selftest · 7 項 · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, VERSION, len(bad)))
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())
