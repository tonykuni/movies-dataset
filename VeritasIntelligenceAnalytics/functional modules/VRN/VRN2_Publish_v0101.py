#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_Publish v0101 — 發布引擎薄尾(前版 v0100 原樣載入 · 只增不減)。資料庫夾(parquet 為準)。

v0101 新增:
  ① 累計冊加 Combined(鍵 TICKER)· Quarterly(鍵 FILENAME / ITEM / PERIOD / PAGE / VALUE(TABLE 是 duckdb 保留字))· Restored(鍵 FILENAME / ITEM / PERIOD / VALUE)
  ② --inventory:掃資料庫夾(output · publish/cumulative · 雲端同步夾 · cloud.extra_folders · 使用者加的 db_folders)所有 csv / json / parquet / xlsx → 列數 / 欄數 / 大小 / 是否 parquet
     → publish/VRN2_DB_Inventory_latest.json + .md(U/I 面板顯示)
  ③ --to-parquet:資料庫夾裡非 parquet(csv / json / xlsx)→ 旁邊出同名 .parquet(原檔不動 · 已有且較新則跳過)· 一致性以 parquet 為準
  ④ --export <csv|json|xlsx> [--book 名]:從累計 parquet 匯出到 publish/export/(全部冊或指定冊)· Google Sheet 仍走 --publish(啟用時)
  ⑤ --db-folder <路徑>:把一個資料庫夾加入清單(cfg.db_folders · 不重複)
"""
from __future__ import annotations

import datetime as _dt
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERSION = "v0101"
PRIOR_PATH = HERE / "VRN2_Publish_v0100.py"
if not PRIOR_PATH.exists():
    raise FileNotFoundError("前版 VRN2_Publish_v0100.py 不在 · v0101 不接")
_spec = importlib.util.spec_from_file_location("vrn2_publish_prior_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec); sys.modules[_spec.name] = PRIOR; _spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v
PRIOR.BOOKS.update({"Combined": ["TICKER"], "Quarterly": ["FILENAME", "ITEM", "PERIOD", "PAGE", "VALUE"], "Restored": ["FILENAME", "ITEM", "PERIOD", "VALUE"]})
BOOKS = PRIOR.BOOKS
_EXT = {".parquet", ".csv", ".json", ".xlsx"}


def db_folders(v2: Path, cfg: dict) -> list:
    out = [v2 / "output", v2 / "publish" / "cumulative"]
    try:
        out += [Path(f["path"]) for f in PRIOR.detect_sync_folders((cfg.get("cloud") or {}).get("extra_folders") or []) if f.get("path")]
    except Exception:  # noqa: BLE001
        pass
    out += [Path(p) for p in (cfg.get("db_folders") or [])]
    seen, res = set(), []
    for p in out:
        k = str(p).lower()
        if k not in seen and p.exists():
            seen.add(k); res.append(p)
    return res


def _rows_cols(p: Path) -> tuple:
    try:
        import pandas as pd
        if p.suffix == ".parquet":
            import pyarrow.parquet as pq
            f = pq.ParquetFile(str(p)); return f.metadata.num_rows, len(f.schema_arrow.names)
        if p.suffix == ".csv":
            n = sum(1 for _ in p.open("r", encoding="utf-8-sig", errors="replace")) - 1; cols = len(p.open("r", encoding="utf-8-sig", errors="replace").readline().split(","))
            return max(n, 0), cols
        if p.suffix == ".json":
            d = json.loads(p.read_text(encoding="utf-8"))
            return (len(d), len(d[0]) if d and isinstance(d[0], dict) else 0) if isinstance(d, list) else (1, len(d) if isinstance(d, dict) else 0)
        if p.suffix == ".xlsx":
            df = pd.read_excel(p); return len(df), len(df.columns)
    except Exception:  # noqa: BLE001
        pass
    return None, None


def inventory(v2: Path) -> dict:
    cfg = PRIOR.load_cfg()
    files = []
    for d in db_folders(v2, cfg):
        for p in sorted(d.glob("*")):
            if p.suffix.lower() in _EXT and p.is_file() and not p.name.startswith("~"):
                r, c = _rows_cols(p)
                files.append({"folder": str(d), "path": str(p), "book": p.stem.replace("VRN2_", "").replace("_latest", ""), "format": p.suffix.lstrip(".").lower(), "rows": r, "cols": c,
                              "bytes": p.stat().st_size, "parquet": p.suffix.lower() == ".parquet", "has_parquet_twin": p.with_suffix(".parquet").exists() or p.suffix.lower() == ".parquet",
                              "mtime": _dt.datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds")})
    rep = {"version": VERSION, "ts": _dt.datetime.now().isoformat(timespec="seconds"), "folders": [str(d) for d in db_folders(v2, cfg)], "files": files,
           "non_parquet_without_twin": [f["path"] for f in files if not f["has_parquet_twin"]]}
    (v2 / "publish").mkdir(parents=True, exist_ok=True)
    (v2 / "publish" / "VRN2_DB_Inventory_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# VRN-2 資料庫夾 · %s · 檔 %d · 夾 %d" % (rep["ts"], len(files), len(rep["folders"])), "", "| 冊 | 格式 | 列 | 欄 | parquet | 路徑 |", "|---|---|---|---|---|---|"]
    md += ["| %s | %s | %s | %s | %s | %s |" % (f["book"], f["format"], f["rows"], f["cols"], "✓" if f["has_parquet_twin"] else "✗", f["path"]) for f in files]
    (v2 / "publish" / "VRN2_DB_Inventory_latest.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return rep


def to_parquet(v2: Path) -> dict:
    import pandas as pd
    rep = inventory(v2); done, skip, bad = [], [], []
    for f in rep["files"]:
        p = Path(f["path"])
        if f["parquet"]:
            continue
        q = p.with_suffix(".parquet")
        if q.exists() and q.stat().st_mtime >= p.stat().st_mtime:
            skip.append(p.name); continue
        try:
            if p.suffix == ".csv":
                df = pd.read_csv(p, encoding="utf-8-sig", dtype=str, low_memory=False)
            elif p.suffix == ".json":
                d = json.loads(p.read_text(encoding="utf-8"))
                if not isinstance(d, list):
                    skip.append(p.name + "(非表格 JSON)"); continue
                df = pd.DataFrame([{k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in r.items()} for r in d])
            else:
                df = pd.read_excel(p, dtype=str)
            df = df.astype({c: "string" for c in df.columns if df[c].dtype == object})
            df.to_parquet(q, index=False); done.append(q.name)
        except Exception as exc:  # noqa: BLE001
            bad.append("%s %s" % (p.name, type(exc).__name__))
    inventory(v2)
    return {"converted": done, "skipped": skip, "failed": bad}


def export(v2: Path, fmt: str, book: str = "") -> dict:
    import pandas as pd
    cd = v2 / "publish" / "cumulative"; ed = v2 / "publish" / "export"; ed.mkdir(parents=True, exist_ok=True)
    out = []
    for p in sorted(cd.glob("*.parquet")):
        if book and p.stem.lower() != book.lower():
            continue
        df = pd.read_parquet(p)
        if fmt == "csv":
            q = ed / (p.stem + ".csv"); df.to_csv(q, index=False, encoding="utf-8-sig")
        elif fmt == "json":
            q = ed / (p.stem + ".json"); q.write_text(df.to_json(orient="records", force_ascii=False, indent=1), encoding="utf-8")
        elif fmt == "xlsx":
            q = ed / (p.stem + ".xlsx"); df.head(PRIOR.LIMITS["excel_rows"] - 1).to_excel(q, index=False)
        else:
            continue
        out.append({"book": p.stem, "rows": len(df), "path": str(q)})
    return {"format": fmt, "files": out}


def main(argv: list) -> int:
    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    v2 = Path(opt("--v2", str(HERE.parent.parent / "VIA_Reports" / "vrn2")))
    if "--selftest" in argv:
        return selftest()
    if "--inventory" in argv:
        r = inventory(v2)
        print("[計] 資料庫夾 · 夾 %d · 檔 %d(parquet %d · 缺 parquet 對照 %d)→ publish/VRN2_DB_Inventory_latest.md" % (len(r["folders"]), len(r["files"]), sum(1 for f in r["files"] if f["parquet"]), len(r["non_parquet_without_twin"]))); return 0
    if "--to-parquet" in argv:
        r = to_parquet(v2)
        print("[計] 轉 parquet · 轉 %d · 跳過 %d · 失敗 %d %s" % (len(r["converted"]), len(r["skipped"]), len(r["failed"]), r["failed"][:3])); return 0
    if "--export" in argv:
        r = export(v2, (opt("--export") or "csv").lower(), opt("--book", "") or "")
        print("[計] 匯出 %s · %s → publish/export" % (r["format"], " · ".join("%s %s 列" % (f["book"], f["rows"]) for f in r["files"]) or "無累計冊(先發布一次)")); return 0
    if "--db-folder" in argv:
        c = PRIOR.load_cfg(); lst = c.setdefault("db_folders", [])
        p = opt("--db-folder")
        if p and p not in lst:
            lst.append(p)
        PRIOR.save_cfg(c); print("[計] 資料庫夾已加入 %s · 共 %d" % (p, len(lst))); return 0
    return PRIOR.main(argv)


def selftest() -> int:
    import tempfile
    import pandas as pd
    ok = [0, 0]
    def chk(name, cond):
        ok[0 if cond else 1] += 1; print("  [%s] %s" % ("OK" if cond else "FAIL", name))
    v2 = Path(tempfile.mkdtemp()); od = v2 / "output"; od.mkdir(parents=True)
    PRIOR.cfg_path = lambda: v2 / "cfg.json"                                   # 自測不碰真設定冊
    pd.DataFrame([{"TICKER": "2330", "REPORTS": 2, "STATUS": "x", "SOURCE": "彙整"}]).to_parquet(od / "VRN2_Combined_latest.parquet", index=False)
    (od / "VRN2_Quarterly_latest.json").write_text(json.dumps([{"FILENAME": "a.pdf", "ITEM": "Revenue", "PERIOD": "1Q23", "PAGE": 2, "TABLE": "t", "VALUE": "1"}]), encoding="utf-8")
    pd.DataFrame([{"FILENAME": "a.pdf", "X": 1}]).to_csv(od / "VRN2_BasicInfo_latest.csv", index=False, encoding="utf-8-sig")
    r = inventory(v2)
    chk("② 資料庫夾盤點 %d 檔 · 缺 parquet 對照 %d" % (len(r["files"]), len(r["non_parquet_without_twin"])), len(r["files"]) == 3 and len(r["non_parquet_without_twin"]) == 2 and (v2 / "publish" / "VRN2_DB_Inventory_latest.md").exists())
    t = to_parquet(v2)
    chk("③ 轉 parquet %s · 再跑跳過 %s" % (t["converted"], to_parquet(v2)["skipped"]), sorted(t["converted"]) == ["VRN2_BasicInfo_latest.parquet", "VRN2_Quarterly_latest.parquet"] and len(to_parquet(v2)["skipped"]) == 2)
    cfg = PRIOR.load_cfg(); cfg.setdefault("formats", {})["google_sheet"] = False; PRIOR.save_cfg(cfg)
    pub = PRIOR.publish(v2)
    e = export(v2, "json")
    chk("① ④ 累計含 Combined / Quarterly %s · 匯出 json %s" % ({k: v.get("total") for k, v in pub["cumulative"]["books"].items() if k in ("Combined", "Quarterly")}, [f["book"] for f in e["files"]]),
        pub["cumulative"]["books"]["Combined"]["total"] == 1 and pub["cumulative"]["books"]["Quarterly"]["total"] == 1 and "Combined" in [f["book"] for f in e["files"]])
    c = PRIOR.load_cfg(); c.setdefault("db_folders", []).append(str(v2 / "output")); PRIOR.save_cfg(c)
    chk("⑤ db_folders 去重 %d" % len(db_folders(v2, PRIOR.load_cfg())), len(db_folders(v2, PRIOR.load_cfg())) == 2)
    p, f = ok
    print("[計] VRN2_Publish v0101 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
