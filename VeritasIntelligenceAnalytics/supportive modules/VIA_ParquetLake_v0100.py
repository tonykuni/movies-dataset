#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_ParquetLake v0100 — 五系統共用的「一系統一湖」增量 Parquet 套件(本體 Parquet · 管家 DuckDB · 只增不減)。

依 VIA_DataHome_SSOT layout_contract:parquet = 資料本體(zstd · 一表一夾 · 分片增量)· duckdb = 管家(表 = VIEW over read_parquet)。
律:
  · 每個系統只碰自己的湖:<root>/<SYSTEM>/<table>/part-<UTC>-<sha8>.parquet;VCGC 不代寫他系統的湖(本套件是工具,不是入口)。
  · 只增:append 只新增分片 + _manifest.jsonl 追一行;同主鍵再來 = 預設跳過(增量),要覆寫就帶 dedupe=False(VIEW 仍以最新 _ingested_at 勝)。
  · 管家:<SYSTEM>_catalog.duckdb 內每表一個 VIEW v_<table>(主鍵去重 · 最新勝);讀側用 DuckDB 零複製掃 Parquet。
  · 零網路 · 零子行程 · 不寫冊。
用法:python3 VIA_ParquetLake_v0100.py status --root <湖根> --system <SYS> · --selftest
程式內:from VIA_ParquetLake_v0100 import Lake; Lake(root, "VDF").append("prices", rows, keys=["ticker", "date"])
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

import argparse
import hashlib
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
ENGINE = "VIA_ParquetLake " + VERSION
SYSTEMS = ("VCGC", "VDF", "VRN2", "VQG", "VAP")
INGEST_COL = "_ingested_at"
_SAFE = re.compile(r"[^A-Za-z0-9_]")


def _now() -> str:
    """微秒級 UTC 戳:同一秒內兩個分片也分得出先後(秒級曾讓「最新勝」平手 · 主控台實跑抓到)。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _q(s: str) -> str:
    return str(s).replace("'", "''")


def safe_name(name: str) -> str:
    n = _SAFE.sub("_", str(name)).strip("_")
    if not n or n[0].isdigit():
        n = "t_" + n
    return n[:80]


def _libs():
    import duckdb  # noqa: WPS433 — 延遲匯入:缺套件時 status 照實說,不在 import 時炸
    import pyarrow as pa
    import pyarrow.parquet as pq
    return duckdb, pa, pq


def _flatten(row: dict) -> dict:
    """巢狀 dict / list 轉 JSON 字串,Parquet 欄位保持平面;None 保留。"""
    out = {}
    for k, v in row.items():
        kk = safe_name(k)
        if isinstance(v, (dict, list, tuple)):
            out[kk] = json.dumps(v, ensure_ascii=False, sort_keys=True)
        elif isinstance(v, bool) or v is None or isinstance(v, (int, float, str)):
            out[kk] = v
        else:
            out[kk] = str(v)
    return out



def _arrow_from_rows(pa, rows: list[dict], cols: list[str]):
    """逐欄推型:全是 bool → bool;全是 int → int64;int/float 混 → float64;其餘(含 str 混數字)→ 全轉字串。
    來源不同(jsonl 的 3 vs csv 的 "3")也能入同一表;跨分片型別不同時 DuckDB union_by_name 會升成 VARCHAR(實測)。"""
    data = {}
    for c in cols:
        vals = [r.get(c) for r in rows]
        nn = [v for v in vals if v is not None]
        if nn and all(isinstance(v, bool) for v in nn):
            data[c] = pa.array(vals, type=pa.bool_())
        elif nn and all(isinstance(v, int) and not isinstance(v, bool) for v in nn):
            data[c] = pa.array(vals, type=pa.int64())
        elif nn and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in nn):
            data[c] = pa.array([None if v is None else float(v) for v in vals], type=pa.float64())
        else:
            data[c] = pa.array([None if v is None else (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)) for v in vals], type=pa.string())
    return pa.table(data)


class Lake:
    def __init__(self, root: Path | str, system: str):
        system = str(system).upper().replace("-", "")
        if system not in SYSTEMS:
            raise ValueError("system must be one of %s" % (SYSTEMS,))
        self.system = system
        self.root = Path(root).resolve()
        self.home = self.root / system
        self.manifest = self.home / "_manifest.jsonl"
        self.catalog = self.home / ("%s_catalog.duckdb" % system)

    # ── 寫側(只增) ──
    def append(self, table: str, rows: list[dict], keys: list[str], dedupe: bool = True) -> dict:
        duckdb, pa, pq = _libs()
        table = safe_name(table)
        keys = [safe_name(k) for k in keys]
        stamp = _now()
        flat = [_flatten(r) for r in rows if isinstance(r, dict)]
        for r in flat:
            r[INGEST_COL] = stamp
            for k in keys:
                r.setdefault(k, None)
        skipped = 0
        tdir = self.home / table
        if dedupe and flat and tdir.exists() and any(tdir.glob("part-*.parquet")):
            con = duckdb.connect()
            try:
                sel = ", ".join('"%s"' % k for k in keys)
                existing = {tuple(x) for x in con.execute("select distinct %s from read_parquet('%s', union_by_name=true)" % (sel, _q(str(tdir / "part-*.parquet")))).fetchall()}
            finally:
                con.close()
            keep = []
            for r in flat:
                tup = tuple(r.get(k) for k in keys)
                if tup in existing:
                    skipped += 1
                else:
                    keep.append(r)
            flat = keep
        if not flat:
            return {"table": table, "added": 0, "skipped": skipped, "file": None, "at": stamp}
        tdir.mkdir(parents=True, exist_ok=True)
        cols = []
        for r in flat:
            for k in r:
                if k not in cols:
                    cols.append(k)
        arrow = _arrow_from_rows(pa, flat, cols)
        payload = json.dumps([[r.get(c) for c in cols] for r in flat], ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
        sha8 = hashlib.sha256(payload).hexdigest()[:8]
        fname = "part-%s-%s.parquet" % (stamp.replace(":", "").replace("-", "").replace(".", ""), sha8)
        dest = tdir / fname
        tmp = tdir / (fname + ".tmp")
        pq.write_table(arrow, tmp, compression="zstd")
        tmp.replace(dest)  # 原子換名:不留半個 Parquet
        rec = {"at": stamp, "system": self.system, "table": table, "file": "%s/%s" % (table, fname), "rows": len(flat), "skipped": skipped,
               "keys": keys, "cols": len(cols), "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(), "bytes": dest.stat().st_size}
        self.home.mkdir(parents=True, exist_ok=True)
        with self.manifest.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.refresh_views()
        return {"table": table, "added": len(flat), "skipped": skipped, "file": rec["file"], "at": stamp}

    # ── 管家 ──
    def tables(self) -> list[str]:
        if not self.home.exists():
            return []
        return sorted(p.name for p in self.home.iterdir() if p.is_dir() and any(p.glob("part-*.parquet")))

    def _keys_for(self, table: str) -> list[str]:
        keys = []
        if self.manifest.exists():
            for line in self.manifest.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("table") == table and r.get("keys"):
                    keys = r["keys"]
        return keys

    def view_sql(self, table: str) -> str:
        table = safe_name(table)
        glob_ = _q(str(self.home / table / "part-*.parquet"))
        keys = self._keys_for(table)
        if keys:
            part = ", ".join('"%s"' % k for k in keys)
            return ("create or replace view v_%s as select * exclude(_rn, filename) from (select *, row_number() over (partition by %s order by %s desc, filename desc) as _rn "
                    "from read_parquet('%s', union_by_name=true, filename=true)) where _rn = 1" % (table, part, INGEST_COL, glob_))
        return "create or replace view v_%s as select * from read_parquet('%s', union_by_name=true)" % (table, glob_)

    def refresh_views(self) -> list[str]:
        duckdb, _, _ = _libs()
        self.home.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(self.catalog))
        try:
            made = []
            for t in self.tables():
                con.execute(self.view_sql(t))
                made.append("v_" + t)
            return made
        finally:
            con.close()

    def status(self) -> dict:
        out = {"engine": ENGINE, "system": self.system, "home": str(self.home), "exists": self.home.exists(), "catalog": str(self.catalog) if self.catalog.exists() else None,
               "manifest_lines": 0, "tables": [], "at": _now()}
        if not self.home.exists():
            return out
        if self.manifest.exists():
            out["manifest_lines"] = sum(1 for l in self.manifest.read_text(encoding="utf-8").splitlines() if l.strip())
        try:
            duckdb, _, _ = _libs()
        except Exception as e:  # noqa: BLE001
            out["error"] = "libs: %s" % str(e)[:120]
            return out
        con = duckdb.connect()
        try:
            for t in self.tables():
                parts = sorted((self.home / t).glob("part-*.parquet"))
                g = _q(str(self.home / t / "part-*.parquet"))
                try:
                    n_raw, lo, hi = con.execute("select count(*), min(%s), max(%s) from read_parquet('%s', union_by_name=true)" % (INGEST_COL, INGEST_COL, g)).fetchone()
                    cols = [c[0] for c in con.execute("describe select * from read_parquet('%s', union_by_name=true)" % g).fetchall()]
                    keys = self._keys_for(t)
                    if keys:
                        n_view = con.execute("select count(*) from (select distinct %s from read_parquet('%s', union_by_name=true))" % (", ".join('"%s"' % k for k in keys), g)).fetchone()[0]
                    else:
                        n_view = n_raw
                    out["tables"].append({"table": t, "parts": len(parts), "rows_raw": n_raw, "rows_view": n_view, "cols": len(cols), "keys": keys,
                                          "first_ingest": lo, "last_ingest": hi, "bytes": sum(p.stat().st_size for p in parts), "view": "v_" + t})
                except Exception as e:  # noqa: BLE001 — 單表壞了照實列,不炸整湖
                    out["tables"].append({"table": t, "parts": len(parts), "error": str(e)[:160]})
        finally:
            con.close()
        return out


# ───────────────────────── 自測 ─────────────────────────
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))
    try:
        duckdb, _, _ = _libs()
    except Exception as e:  # noqa: BLE001
        print("  [SKIP] 缺 duckdb / pyarrow:%s" % e)
        print("[FAIL] %s selftest · 0/0 · 環境缺套件(不假綠)" % ENGINE)
        return 1
    with tempfile.TemporaryDirectory(prefix="via_lake_") as td:
        lk = Lake(td, "VDF")
        r1 = lk.append("prices", [{"ticker": "2330", "date": "2026-11-07", "close": 1000.0, "meta": {"src": "a"}},
                                  {"ticker": "2330", "date": "2026-11-08", "close": 1010.0},
                                  {"ticker": "2317", "date": "2026-11-08", "close": 200.5}], keys=["ticker", "date"])
        chk("ⓐ 首次 append 3 列 · 巢狀欄轉 JSON 字串 · 分片 + manifest + 管家 duckdb 都在",
            r1["added"] == 3 and (lk.home / "prices" / r1["file"].split("/")[1]).exists() and lk.manifest.exists() and lk.catalog.exists(), r1)
        r2 = lk.append("prices", [{"ticker": "2330", "date": "2026-11-08", "close": 1011.0}, {"ticker": "2330", "date": "2026-11-09", "close": 1020.0}], keys=["ticker", "date"])
        chk("ⓑ 增量:同主鍵 1 列跳過 · 新 1 列入 · manifest 2 行", r2["added"] == 1 and r2["skipped"] == 1 and sum(1 for l in lk.manifest.read_text(encoding="utf-8").splitlines() if l.strip()) == 2, r2)
        r3 = lk.append("prices", [{"ticker": "2330", "date": "2026-11-08", "close": 1012.0}], keys=["ticker", "date"], dedupe=False)
        con = duckdb.connect(str(lk.catalog), read_only=True)
        try:
            rows = con.execute("select ticker, date, close from v_prices order by ticker, date").fetchall()
            raw = con.execute("select count(*) from read_parquet('%s', union_by_name=true)" % _q(str(lk.home / "prices" / "part-*.parquet"))).fetchone()[0]
        finally:
            con.close()
        chk("ⓒ dedupe=False 允許覆寫分片 · VIEW 主鍵去重最新勝(2330/11-08 = 1012;微秒戳 + 檔名次序 · 同一秒也分先後)· 原始列 5 · 視圖列 4",
            r3["added"] == 1 and raw == 5 and len(rows) == 4 and [r for r in rows if r[0] == "2330" and r[1] == "2026-11-08"][0][2] == 1012.0, rows)
        st = lk.status()
        t = st["tables"][0]
        chk("ⓓ status:表 prices · parts 3 · rows_raw 5 · rows_view 4 · keys · first/last ingest · bytes > 0 · view 名",
            st["exists"] and st["manifest_lines"] == 3 and t["table"] == "prices" and t["parts"] == 3 and t["rows_raw"] == 5 and t["rows_view"] == 4 and t["keys"] == ["ticker", "date"]
            and t["first_ingest"] <= t["last_ingest"] and t["bytes"] > 0 and t["view"] == "v_prices", {k: v for k, v in t.items() if k != "keys"})
        r4 = lk.append("empty", [], keys=["k"])
        chk("ⓔ 空批不落檔 · 回 added 0", r4["added"] == 0 and r4["file"] is None and "empty" not in lk.tables())
        chk("ⓕ 表名 / 欄名消毒(a b-c → a_b_c · 數字開頭加 t_)", safe_name("a b-c") == "a_b_c" and safe_name("1x") == "t_1x")
        other = Lake(td, "VQG")
        chk("ⓖ 另一系統另一夾 · 互不可見(VQG 0 表 · VDF 1 表)", other.tables() == [] and lk.tables() == ["prices"] and other.home != lk.home)
        try:
            Lake(td, "XYZ")
            bad = False
        except ValueError:
            bad = True
        chk("ⓗ 非五系統名拒絕 · 連字號正規化 VRN-2 → VRN2", bad and Lake(td, "VRN-2").system == "VRN2")
        gone = Lake(td, "VAP").status()
        chk("ⓘ 沒有湖:status exists False · 0 表 · 不炸", not gone["exists"] and gone["tables"] == [])
    with tempfile.TemporaryDirectory(prefix="via_lake_") as td:
        lk = Lake(td, "VCGC")
        r1 = lk.append("mixed", [{"id": "a", "n": 1, "f": 1.5, "b": True}], keys=["id"])
        r2 = lk.append("mixed", [{"id": "b", "n": "3", "f": 2, "b": "yes", "extra": {"k": 1}}], keys=["id"])
        con = duckdb.connect(str(lk.catalog), read_only=True)
        try:
            rows = con.execute("select id, n, f, b, extra from v_mixed order by id").fetchall()
            types = [t[1] for t in con.execute("describe v_mixed").fetchall()]
        finally:
            con.close()
        chk("ⓚ 來源混型(jsonl 的 3 vs csv 的 '3' · 巢狀欄)仍入同一表 · 跨分片升 VARCHAR · 視圖可讀 2 列",
            r1["added"] == 1 and r2["added"] == 1 and len(rows) == 2 and rows[1][1] == "3" and rows[1][4] == '{"k": 1}' and "VARCHAR" in types, (rows, types))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("ⓙ 邊界:不開網路 / 不開子行程 / 不寫冊", not re.search(r"^\s*(import|from)\s+(urllib|socket|requests|http\b|subprocess)", src, re.M) and "registry" not in src.split("class Lake")[1].split("def selftest")[0])
    bad = len(ok) - sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if not bad else "FAIL", ENGINE, sum(ok), len(ok)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="VIA_ParquetLake", description=__doc__.splitlines()[0])
    ap.add_argument("verb", nargs="?", default="status", choices=["status", "selftest"])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--root", default=None)
    ap.add_argument("--system", default="VCGC")
    a = ap.parse_args(argv)
    if a.selftest or a.verb == "selftest":
        return selftest()
    if not a.root:
        print("[GRAY] 要 --root <湖根>(各系統自己的家;VCGC 預設 VIA_Reports/lake)")
        return 1
    st = Lake(a.root, a.system).status()
    print(json.dumps(st, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
