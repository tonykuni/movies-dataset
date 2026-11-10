#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_LakeMatrix v0100 — 五系統資料湖矩陣 + 工具活動報告矩陣(VCGC 自己的湖寫入 · 他系統只讀盤點 · DuckDB 管家 · HTML U/I)。

操作員 2026-11-10:「五個獨立系統即一個資料庫以 parquet 為格式增量維護 · 以 duckdb 為工具來管理 · 工具活動報告矩陣 · 啟動測試及使用者測試修正直到完善 · 跳出 HTML U/I」。
做法(L123 五系統對等 · 互不干涉):
  ① VCGC 自己的湖:把 VCGC 落檔的帳本(FunctionLedger · toolboard · mutual · closeout · gate · TEST_STATE · 備份 MANIFEST)經 VIA_ParquetLake 增量入 Parquet
     <root>/VCGC/<table>/part-*.parquet,管家 VCGC_catalog.duckdb 一表一 VIEW;同主鍵不重入。
  ② 他系統(VDF · VRN-2 · VQG · VAP):只讀盤點——有自己的湖(<root>/<SYS>)就讀湖;沒有就列倉內既有 .duckdb / .parquet 資產(照實標「尚未入湖」);VCGC 不代建、不代寫。
  ③ 工具活動報告矩陣:DuckDB 查 VCGC 湖 → 事件 × 日 · 類 · 站;五系統 × 日 活動(湖 / 資產檔案更新日 · 代理指標照實標)。
  ④ 輸出 VIA_Reports/lake/LAKE_MATRIX_latest.{json,md,html} + lake_matrix_ledger.jsonl(只增);HTML 燈號放最前、可篩選(系統鈕 · 搜尋 · 只看有資料)。
湖根:--root > env VIA_DATA_HOME > VIA_DataHome_SSOT home_posix > 倉內 VIA_Reports/lake(容器預設 · 照實標來源)。
用法:run [--root] [--no-write] [--open] · --selftest
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
import glob
import html
import importlib.util
import json
import os
import re
import sys
import tempfile
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

VERSION = "v0100"
ENGINE = "VIA_LakeMatrix " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[2] if HERE.name == "ai" else HERE
SYSTEMS = ["VCGC", "VDF", "VRN2", "VQG", "VAP"]
LABEL = {"VCGC": "VCGC", "VDF": "VDF", "VRN2": "VRN-2", "VQG": "VQG", "VAP": "VAP"}
ORDER = {"GREEN": 0, "YELLOW": 1, "GRAY": 2, "RED": 3}
STALE_HOURS = 48.0
OUT_DIR = "VIA_Reports/lake"
MAX_FILES = 80
LEGACY = {  # 倉內既有資產(只讀盤點;來源照實);湖在 <root>/<SYS>
    "VCGC": [("parquet", "VIA_Reports/workflow_viz/*.parquet")],
    "VDF": [("duckdb", "functional modules/VDF/output_hub/**/*.duckdb"), ("duckdb", "functional modules/VDF/db/**/*.duckdb"), ("duckdb", "VIA_Reports/vdf_fetch/dict/*.duckdb"),
            ("parquet", "VIA_Reports/vdf_fetch/dict/**/*.parquet"), ("parquet", "functional modules/VDF/output_hub/**/*.parquet")],
    "VRN2": [("duckdb", "functional modules/VRN/db/*.duckdb"), ("parquet", "VIA_Reports/vrn2/output/*.parquet"), ("parquet", "VIA_Reports/data_broker/out/**/*.parquet")],
    "VQG": [("parquet", "VIA_Reports/vqg/vap_export/*/**/*.parquet")],
    "VAP": [("parquet", "functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_warehouse/parquet/*.parquet")],
}
LEDGERS = {  # VCGC 自己的帳本 → 湖表(主鍵)
    "function_ledger": ("supportive modules/registry/VIA_VCGC_FunctionLedger_v0100.jsonl", ["ts", "id", "event"]),
    "toolboard_ledger": ("VIA_Reports/vcgc/toolboard_ledger.jsonl", ["at"]),
    "mutual_ledger": ("VIA_Reports/mutual/mutual_ledger.jsonl", ["at"]),
    "closeout_ledger": ("VIA_Reports/closeout/closeout_ledger.jsonl", ["run"]),
    "gate_ledger": ("VIA_Reports/gate/gate_ledger.jsonl", ["run"]),
}


def _lake_module():
    p = VIA / "supportive modules" / "VIA_ParquetLake_v0100.py"
    spec = importlib.util.spec_from_file_location("VIA_ParquetLake_v0100", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _q(s) -> str:
    return str(s).replace("'", "''")


def e(s) -> str:
    return html.escape(str(s if s is not None else ""))


def parse_at(v):
    if not v:
        return None
    try:
        d = datetime.fromisoformat(str(v).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


# ───────────────────────── 湖根 ─────────────────────────
def resolve_root(via: Path, override: str | None = None) -> tuple[Path, str]:
    if override:
        return Path(override).resolve(), "--root"
    env = os.environ.get("VIA_DATA_HOME")
    if env and Path(env).is_dir():
        return Path(env).resolve(), "env VIA_DATA_HOME"
    hits = sorted(glob.glob(str(via / "supportive modules/registry/VIA_DataHome_SSOT_v*.json")))
    if hits:
        try:
            d = json.loads(Path(hits[-1]).read_text(encoding="utf-8"))
            hp = d.get("home_posix")
            if hp and Path(hp).is_dir():
                return Path(hp).resolve(), "VIA_DataHome_SSOT home_posix"
        except ValueError:
            pass
    return (via / OUT_DIR).resolve(), "repo_default(容器 · 冊上 Windows 家在這台機器不在)"


# ───────────────────────── ① VCGC 自己的湖 ─────────────────────────
def _jsonl(p: Path) -> list[dict]:
    rows = []
    if not p.exists():
        return rows
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if isinstance(r, dict):
            rows.append(r)
    return rows


def ingest_vcgc(via: Path, root: Path) -> dict:
    Lake = _lake_module().Lake
    lk = Lake(root, "VCGC")
    out = {"home": str(lk.home), "tables": {}}
    for table, (rel, keys) in LEDGERS.items():
        rows = _jsonl(via / rel)
        if rows:
            r = lk.append(table, rows, keys=keys)
            out["tables"][table] = {"source": rel, "rows_in": len(rows), "added": r["added"], "skipped": r["skipped"]}
        else:
            out["tables"][table] = {"source": rel, "rows_in": 0, "added": 0, "skipped": 0, "note": "來源不在或空"}
    st = sorted(glob.glob(str(via / "VIA_Reports/vcgc/TEST_STATE_v*.json")))
    if st:
        try:
            d = json.loads(Path(st[-1]).read_text(encoding="utf-8"))
            rows = [dict(v, id=k) for k, v in d.items() if isinstance(v, dict)]
            r = lk.append("test_state", rows, keys=["id", "at"])
            out["tables"]["test_state"] = {"source": str(Path(st[-1]).relative_to(via)), "rows_in": len(rows), "added": r["added"], "skipped": r["skipped"]}
        except ValueError:
            out["tables"]["test_state"] = {"source": st[-1], "rows_in": 0, "added": 0, "skipped": 0, "note": "壞 JSON"}
    mans = [p for p in sorted(glob.glob(str(via / "docs/handoff/backup/BACKUP_MANIFEST_*.json"))) if not p.endswith("_latest.json")]
    rows = []
    for p in mans:
        try:
            m = json.loads(Path(p).read_text(encoding="utf-8"))
        except ValueError:
            continue
        for sysname, v in (m.get("systems") or {}).items():
            if isinstance(v, dict):
                rows.append({"stamp": m.get("stamp"), "at": m.get("at"), "system": sysname, "zip": v.get("zip"), "zip_sha256": v.get("zip_sha256"), "zip_bytes": v.get("zip_bytes"),
                             "count": v.get("count"), "git_head": (m.get("git") or {}).get("head") if isinstance(m.get("git"), dict) else None})
    if rows:
        r = lk.append("backup_manifest", rows, keys=["stamp", "system"])
        out["tables"]["backup_manifest"] = {"source": "docs/handoff/backup/BACKUP_MANIFEST_*.json", "rows_in": len(rows), "added": r["added"], "skipped": r["skipped"]}
    lk.refresh_views()  # 套件 VIEW 定義若換版,無新列的一輪也要重建視圖
    out["status"] = lk.status()
    return out


# ───────────────────────── ② 五系統盤點(只讀) ─────────────────────────
def _probe_duckdb(duckdb, p: Path) -> dict:
    rec = {"kind": "duckdb", "name": p.name, "path": str(p), "bytes": p.stat().st_size, "mtime": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "tables": []}
    try:
        con = duckdb.connect(str(p), read_only=True)
        try:
            names = [r[0] for r in con.execute("select table_name from information_schema.tables where table_schema='main' order by 1").fetchall()][:40]
            for t in names:
                try:
                    n = con.execute('select count(*) from "%s"' % t.replace('"', '""')).fetchone()[0]
                except Exception as ex:  # noqa: BLE001
                    n = None
                    rec.setdefault("errors", []).append("%s: %s" % (t, str(ex)[:80]))
                rec["tables"].append({"table": t, "rows": n})
        finally:
            con.close()
    except Exception as ex:  # noqa: BLE001 — 壞庫照實標,不炸整輪
        rec["error"] = str(ex)[:160]
    rec["rows"] = sum((t["rows"] or 0) for t in rec["tables"])
    return rec


def _probe_parquet_set(duckdb, files: list[Path]) -> dict:
    files = sorted(files)[:MAX_FILES]
    d = files[0].parent
    rec = {"kind": "parquet", "name": d.name, "path": str(d), "files": len(files), "bytes": sum(f.stat().st_size for f in files),
           "mtime": max(datetime.fromtimestamp(f.stat().st_mtime, timezone.utc) for f in files).strftime("%Y-%m-%dT%H:%M:%SZ"), "tables": []}
    con = duckdb.connect()
    try:
        total = 0
        bad = 0
        cols = None
        for f in files:
            try:
                n = con.execute("select count(*) from read_parquet('%s')" % _q(f)).fetchone()[0]
                total += n
                if cols is None:
                    cols = [c[0] for c in con.execute("describe select * from read_parquet('%s')" % _q(f)).fetchall()]
            except Exception as ex:  # noqa: BLE001
                bad += 1
                rec.setdefault("errors", []).append("%s: %s" % (f.name, str(ex)[:80]))
        rec["rows"] = total
        rec["cols"] = cols or []
        rec["bad_files"] = bad
        rec["tables"] = [{"table": d.name, "rows": total}]
    finally:
        con.close()
    return rec


def system_cards(via: Path, root: Path, now: datetime) -> list[dict]:
    Lake = _lake_module().Lake
    import duckdb
    cards = []
    for s in SYSTEMS:
        lk = Lake(root, s)
        st = lk.status()
        legacy = []
        for kind, pat in LEGACY.get(s, []):
            hits = [Path(p) for p in glob.glob(str(via / pat), recursive=True)]
            if not hits:
                continue
            if kind == "duckdb":
                for p in sorted(hits)[:12]:
                    legacy.append(_probe_duckdb(duckdb, p))
            else:
                groups = {}
                for p in hits:
                    groups.setdefault(p.parent, []).append(p)
                for _, fs in sorted(groups.items(), key=lambda kv: str(kv[0]))[:12]:
                    legacy.append(_probe_parquet_set(duckdb, fs))
        for a in legacy:
            a["rel"] = str(Path(a["path"]).relative_to(via)) if str(a["path"]).startswith(str(via)) else a["path"]
            a["age_days"] = round((now - parse_at(a["mtime"])).total_seconds() / 86400, 1) if parse_at(a["mtime"]) else None
        lake_tables = [t for t in st.get("tables", []) if "error" not in t]
        lake_err = [t for t in st.get("tables", []) if "error" in t]
        last = max((t.get("last_ingest") or "" for t in lake_tables), default="")
        age_h = round((now - parse_at(last)).total_seconds() / 3600, 2) if parse_at(last) else None
        if lake_err and not lake_tables:
            lamp, why = "RED", "湖內表全壞:%s" % "; ".join(t["error"][:60] for t in lake_err[:2])
        elif lake_tables:
            if age_h is not None and age_h > STALE_HOURS:
                lamp, why = "YELLOW", "湖在 · 最後入湖 %.0f 小時前(> %dh 過期)" % (age_h, int(STALE_HOURS))
            else:
                lamp, why = "GREEN", "湖在 · %d 表 · 最後入湖 %s" % (len(lake_tables), last[:16])
        elif legacy:
            lamp, why = "YELLOW", "尚未入湖 · 倉內既有資產 %d 組(%s)— 接入是 %s 自己的手(用 VIA_ParquetLake)" % (len(legacy), " · ".join(sorted({a["kind"] for a in legacy})), LABEL[s])
        else:
            lamp, why = "GRAY", "這台機器沒有 %s 的湖也沒有既有資產(操作員桌機資料家不在容器)" % LABEL[s]
        cards.append({"system": s, "label": LABEL[s], "lamp": lamp, "why": why, "lake_home": str(lk.home), "lake_exists": st.get("exists", False), "lake_tables": lake_tables, "lake_errors": lake_err,
                      "catalog": st.get("catalog"), "manifest_lines": st.get("manifest_lines", 0), "last_ingest": last or None, "lake_age_hours": age_h,
                      "legacy": legacy, "legacy_rows": sum((a.get("rows") or 0) for a in legacy), "legacy_bytes": sum(a.get("bytes", 0) for a in legacy)})
    return cards


# ───────────────────────── ③ 工具活動報告矩陣 ─────────────────────────
def activity(root: Path, cards: list[dict], now: datetime) -> dict:
    import duckdb
    days = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    out = {"days": days, "events_by_day": {}, "kinds_7d": {}, "top_ids_7d": [], "ledger_latest": {}, "systems_by_day": {}, "proxy_note": "五系統 × 日 = 湖分片 / 既有資產檔案的更新日(代理指標 · 照實);工具事件 = VCGC 湖 function_ledger"}
    cat = root / "VCGC" / "VCGC_catalog.duckdb"
    if cat.exists():
        con = duckdb.connect(str(cat), read_only=True)
        try:
            views = {r[0] for r in con.execute("select table_name from information_schema.tables where table_schema='main'").fetchall()}
            if "v_function_ledger" in views:
                since = days[0]
                for d, ev, n in con.execute("select substr(ts,1,10) d, event, count(*) from v_function_ledger where substr(ts,1,10) >= ? group by 1,2 order by 1,2", [since]).fetchall():
                    out["events_by_day"].setdefault(d, {})[ev] = n
                out["kinds_7d"] = {k: n for k, n in con.execute("select kind, count(*) from v_function_ledger where substr(ts,1,10) >= ? group by 1 order by 2 desc", [since]).fetchall()}
                out["top_ids_7d"] = [{"id": i, "n": n, "last": l} for i, n, l in con.execute("select id, count(*), max(ts) from v_function_ledger where substr(ts,1,10) >= ? group by 1 order by 2 desc, 1 limit 15", [since]).fetchall()]
            for v in sorted(views):
                col = "at" if v in ("v_toolboard_ledger", "v_mutual_ledger", "v_closeout_ledger", "v_gate_ledger", "v_backup_manifest", "v_test_state") else ("ts" if v == "v_function_ledger" else None)
                try:
                    n = con.execute("select count(*) from %s" % v).fetchone()[0]
                    last = con.execute("select max(%s) from %s" % (col, v)).fetchone()[0] if col else None
                    out["ledger_latest"][v] = {"rows": n, "last": last}
                except Exception as ex:  # noqa: BLE001
                    out["ledger_latest"][v] = {"error": str(ex)[:100]}
        finally:
            con.close()
    for c in cards:
        row = {d: 0 for d in days}
        for t in c["lake_tables"]:
            for stamp in (t.get("first_ingest"), t.get("last_ingest")):
                dd = str(stamp or "")[:10]
                if dd in row:
                    row[dd] += 1
        for a in c["legacy"]:
            dd = str(a.get("mtime", ""))[:10]
            if dd in row:
                row[dd] += a.get("files", 1) if a["kind"] == "parquet" else 1
        out["systems_by_day"][c["system"]] = row
    return out


# ───────────────────────── 組裝 · 輸出 ─────────────────────────
def build(via: Path, root: Path | None = None, root_src: str = "", now: datetime | None = None, ingest: bool = True) -> dict:
    now = now or datetime.now(timezone.utc)
    if root is None:
        root, root_src = resolve_root(via)
    ing = ingest_vcgc(via, root) if ingest else {"skipped": True}
    cards = system_cards(via, root, now)
    act = activity(root, cards, now)
    overall = max((c["lamp"] for c in cards), key=lambda l: ORDER[l])
    return {"schema": "VIA-LAKE-MATRIX/1.0", "engine": ENGINE, "at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "via_root": str(via), "lake_root": str(root), "lake_root_source": root_src,
            "overall": {"lamp": overall, "rule": "五系統湖燈取最差;GREEN 湖在且 48h 內入湖 · YELLOW 過期或尚未入湖(只有既有資產)· GRAY 這台機器沒資料 · RED 湖壞;VCGC 只寫自己的湖"},
            "ingest": ing, "systems": cards, "activity": act,
            "law": "L123 五系統對等 · 互不干涉:VCGC 不代建 / 不代寫他系統的湖;本套件(VIA_ParquetLake)供各系統自用;本矩陣對他系統只讀"}


def to_md(b: dict) -> str:
    L = ["# 五系統資料湖矩陣 · %s · **%s**" % (b["at"], b["overall"]["lamp"]), "", "湖根:`%s`(%s)· %s" % (b["lake_root"], b["lake_root_source"], b["overall"]["rule"]), "",
         "## 1. 五系統燈(放最前面)", "", "| 燈 | 系統 | 湖 | 表 | 最後入湖 | 既有資產 | 說明 |", "|---|---|---|---|---|---|---|"]
    for c in b["systems"]:
        L.append("| **%s** | %s | %s | %d | %s | %d 組 · %s 列 | %s |" % (c["lamp"], c["label"], "在" if c["lake_exists"] else "無", len(c["lake_tables"]), str(c["last_ingest"] or "—")[:16], len(c["legacy"]), f"{c['legacy_rows']:,}", c["why"]))
    a = b["activity"]
    L += ["", "## 2. 五系統 × 日 活動矩陣(%s)" % a["proxy_note"], "", "| 系統 | " + " | ".join(d[5:] for d in a["days"]) + " |", "|---|" + "---|" * len(a["days"])]
    for s, row in a["systems_by_day"].items():
        L.append("| %s | " % LABEL[s] + " | ".join(str(row[d]) if row[d] else "·" for d in a["days"]) + " |")
    evs = sorted({ev for d in a["events_by_day"].values() for ev in d})
    L += ["", "## 3. 工具活動報告矩陣(VCGC 湖 function_ledger · 事件 × 日)", ""]
    if evs:
        L += ["| 事件 | " + " | ".join(d[5:] for d in a["days"]) + " |", "|---|" + "---|" * len(a["days"])]
        for ev in evs:
            L.append("| %s | " % ev + " | ".join(str(a["events_by_day"].get(d, {}).get(ev, "·")) for d in a["days"]) + " |")
        L += ["", "七日類別:" + " · ".join("%s %d" % (k, n) for k, n in a["kinds_7d"].items()), "", "| 站 / 冊 / 家族 | 七日次數 | 最後 |", "|---|---|---|"]
        for t in a["top_ids_7d"]:
            L.append("| %s | %d | %s |" % (t["id"], t["n"], str(t["last"])[:16]))
    else:
        L.append("(VCGC 湖沒有 function_ledger 視圖 — 帳本不在或尚未入湖)")
    L += ["", "## 4. 資產明細(湖表 + 既有資產 · 只讀)", "", "| 系統 | 類 | 名 | 表 / 檔 | 列 | 最後更新 | 大小 | 狀態 |", "|---|---|---|---|---|---|---|---|"]
    for c in b["systems"]:
        for t in c["lake_tables"]:
            L.append("| %s | 湖 | %s | %d 分片 · %s | %s | %s | %s | 增量 · 主鍵 %s |" % (c["label"], t["table"], t["parts"], t["view"], f"{t['rows_view']:,}", str(t["last_ingest"])[:16], _hb(t["bytes"]), ",".join(t["keys"]) or "—"))
        for x in c["legacy"]:
            L.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (c["label"], x["kind"], x["name"], ("%d 表" % len(x["tables"])) if x["kind"] == "duckdb" else ("%d 檔" % x["files"]), f"{x.get('rows') or 0:,}", str(x["mtime"])[:16], _hb(x["bytes"]),
                                                              ("錯:" + x["error"][:60]) if x.get("error") else ("尚未入湖" + (" · 壞檔 %d" % x["bad_files"] if x.get("bad_files") else ""))))
    ing = b["ingest"]
    if "tables" in ing:
        L += ["", "## 5. 本輪 VCGC 入湖收據(增量:同主鍵跳過)", "", "| 表 | 來源 | 讀到 | 新入 | 跳過 |", "|---|---|---|---|---|"]
        for t, r in ing["tables"].items():
            L.append("| %s | `%s` | %d | %d | %d |" % (t, r["source"], r["rows_in"], r["added"], r["skipped"]))
    L += ["", b["law"]]
    return "\n".join(L) + "\n"


def _hb(n) -> str:
    n = float(n or 0)
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return "%.0f %s" % (n, u) if u == "B" else "%.1f %s" % (n, u)
        n /= 1024
    return "%.1f TB" % n


CSS = """
:root{--bg:#f6f7f9;--fg:#1d2430;--mute:#5d6676;--line:#d9dee6;--card:#fff;--g:#1f9d55;--y:#d99a00;--r:#c62828;--n:#7a8290;--acc:#2f5fb3;--head:56px}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0f1318;--fg:#e6e9ee;--mute:#9aa3b2;--line:#273040;--card:#161c24;--acc:#7aa2f7;color-scheme:dark}}
:root[data-theme=dark]{--bg:#0f1318;--fg:#e6e9ee;--mute:#9aa3b2;--line:#273040;--card:#161c24;--acc:#7aa2f7;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:clamp(14px,.35vw + 13px,15.5px)/1.5 system-ui,-apple-system,"Segoe UI","Noto Sans TC",sans-serif}
header{position:sticky;top:0;z-index:5;height:var(--head);display:flex;align-items:center;gap:.8rem;padding:0 max(16px,env(safe-area-inset-right,0px)) 0 max(16px,env(safe-area-inset-left,0px));background:var(--card);border-bottom:1px solid var(--line)}
header h1{font-size:1.05rem;margin:0;font-weight:650;white-space:nowrap}header .meta{color:var(--mute);font-size:.82rem;margin-left:auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
main{padding:1rem max(16px,env(safe-area-inset-right,0px)) 2rem max(16px,env(safe-area-inset-left,0px));max-width:1400px;margin:0 auto;overflow-wrap:anywhere;min-width:0}
.lamp{display:inline-block;min-width:4.6em;text-align:center;padding:.1em .55em;border-radius:999px;font-weight:650;font-size:.8rem;color:#fff;background:var(--n)}
.lamp.GREEN{background:var(--g)}.lamp.YELLOW{background:var(--y)}.lamp.RED{background:var(--r)}.lamp.GRAY{background:var(--n)}.lamp.big{font-size:1.1rem;padding:.25em .9em}
.strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:.7rem;margin:.8rem 0 1.2rem}
.tile{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:.7rem .9rem;min-width:0;cursor:pointer}.tile.on{outline:2px solid var(--acc)}
.tile .t{font-weight:650;margin:.2rem 0}.tile .s{color:var(--mute);font-size:.82rem;overflow-wrap:anywhere}
.ctl{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin:.6rem 0 1rem;min-width:0}.ctl label{white-space:nowrap}.ctl button{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:.25em .9em;cursor:pointer;font:inherit}
.ctl button.on{background:var(--acc);color:#fff;border-color:var(--acc)}.ctl input[type=search]{flex:1;min-width:160px;padding:.35em .7em;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);font:inherit}
.ctl label{color:var(--mute);font-size:.88rem;display:flex;gap:.3rem;align-items:center}
h2{font-size:1.1rem;margin:1.4rem 0 .5rem}table{border-collapse:collapse;width:100%;font-size:.86rem}th,td{border-bottom:1px solid var(--line);padding:.3rem .45rem;text-align:left;vertical-align:top}th{color:var(--mute);font-weight:600}
.wrap{overflow-x:auto}code{font-size:.85em;background:rgba(127,127,127,.12);padding:.05em .3em;border-radius:4px}.num{text-align:right;font-variant-numeric:tabular-nums}
.heat td.c{text-align:center;font-variant-numeric:tabular-nums}.heat td.c.h1{background:rgba(47,95,179,.12)}.heat td.c.h2{background:rgba(47,95,179,.28)}.heat td.c.h3{background:rgba(47,95,179,.5);color:#fff}
.empty{color:var(--mute);padding:.6rem 0}#count{color:var(--mute);font-size:.85rem}
@media(max-width:700px){.strip{grid-template-columns:1fr 1fr}:root{--head:48px}}
"""

JS = """
(function(){
  var sys='ALL', q='', only=false;
  var rows=[].slice.call(document.querySelectorAll('#assets tbody tr'));
  var btns=[].slice.call(document.querySelectorAll('.ctl button[data-sys]'));
  var tiles=[].slice.call(document.querySelectorAll('.tile[data-sys]'));
  function apply(){
    var n=0;
    rows.forEach(function(r){
      var ok=(sys==='ALL'||r.dataset.sys===sys) && (!q||r.dataset.name.indexOf(q)>=0) && (!only||Number(r.dataset.rows)>0);
      r.hidden=!ok; if(ok) n++;
    });
    document.getElementById('count').textContent='顯示 '+n+' / '+rows.length+' 列';
    document.getElementById('empty').hidden = n>0;
    btns.forEach(function(b){b.classList.toggle('on',b.dataset.sys===sys);});
    tiles.forEach(function(t){t.classList.toggle('on',t.dataset.sys===sys);});
    [].slice.call(document.querySelectorAll('.heat tbody tr[data-sys]')).forEach(function(r){r.hidden = sys!=='ALL' && r.dataset.sys!==sys;});
  }
  btns.forEach(function(b){b.addEventListener('click',function(){sys=b.dataset.sys;apply();});});
  tiles.forEach(function(t){t.addEventListener('click',function(){sys=(sys===t.dataset.sys)?'ALL':t.dataset.sys;apply();});});
  document.getElementById('q').addEventListener('input',function(ev){q=ev.target.value.trim().toLowerCase();apply();});
  document.getElementById('only-data').addEventListener('change',function(ev){only=ev.target.checked;apply();});
  document.getElementById('reset').addEventListener('click',function(){sys='ALL';q='';only=false;document.getElementById('q').value='';document.getElementById('only-data').checked=false;apply();});
  apply();
})();
"""


def to_html(b: dict) -> str:
    o = b["overall"]
    a = b["activity"]
    H = ['<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
         "<title>五系統資料湖矩陣 · %s</title><style>%s</style></head><body>" % (e(b["at"]), CSS),
         '<header><span class="lamp big %s">%s</span><h1>五系統資料湖矩陣</h1><span class="meta">%s · 湖根 %s(%s)</span></header><main>' % (e(o["lamp"]), e(o["lamp"]), e(b["at"]), e(b["lake_root"]), e(b["lake_root_source"])),
         '<p style="color:var(--mute);margin:.2rem 0 .6rem">%s</p><section id="lamps" class="strip">' % e(o["rule"])]
    for c in b["systems"]:
        H.append('<div class="tile" data-sys="%s" id="tile-%s"><span class="lamp %s">%s</span><div class="t">%s</div><div class="s">%s</div><div class="s">湖 %s · %d 表 · 既有 %d 組 · %s 列</div></div>' % (
            e(c["system"]), e(c["system"]), e(c["lamp"]), e(c["lamp"]), e(c["label"]), e(c["why"]), "在" if c["lake_exists"] else "無", len(c["lake_tables"]), len(c["legacy"]), f"{c['legacy_rows']:,}"))
    H.append('</section><div class="ctl" id="controls"><button data-sys="ALL" id="btn-all">全部</button>' + "".join('<button data-sys="%s" id="btn-%s">%s</button>' % (s, s, LABEL[s]) for s in SYSTEMS)
             + '<input type="search" id="q" placeholder="搜表名 / 檔名 / 路徑" aria-label="搜尋"><label><input type="checkbox" id="only-data"> 只看有資料</label><button id="reset">重設</button><span id="count"></span></div>')
    H.append('<h2 id="activity">五系統 × 日 活動矩陣 <span style="color:var(--mute);font-weight:400;font-size:.82rem">%s</span></h2><div class="wrap"><table class="heat"><thead><tr><th>系統</th>%s</tr></thead><tbody>' % (e(a["proxy_note"]), "".join("<th>%s</th>" % e(d[5:]) for d in a["days"])))
    for s, row in a["systems_by_day"].items():
        H.append('<tr data-sys="%s"><td>%s</td>%s</tr>' % (e(s), e(LABEL[s]), "".join('<td class="c %s">%s</td>' % (_heat(row[d]), row[d] if row[d] else "·") for d in a["days"])))
    H.append("</tbody></table></div>")
    evs = sorted({ev for d in a["events_by_day"].values() for ev in d})
    H.append('<h2 id="tools">工具活動報告矩陣 <span style="color:var(--mute);font-weight:400;font-size:.82rem">VCGC 湖 function_ledger · 事件 × 日 · 七日類別 · 最活躍站 / 冊 / 家族</span></h2>')
    if evs:
        H.append('<div class="wrap"><table class="heat"><thead><tr><th>事件</th>%s</tr></thead><tbody>' % "".join("<th>%s</th>" % e(d[5:]) for d in a["days"]))
        for ev in evs:
            H.append("<tr><td>%s</td>%s</tr>" % (e(ev), "".join('<td class="c %s">%s</td>' % (_heat(a["events_by_day"].get(d, {}).get(ev, 0)), a["events_by_day"].get(d, {}).get(ev, "·")) for d in a["days"])))
        H.append("</tbody></table></div><p>七日類別:%s</p><div class=\"wrap\"><table><thead><tr><th>站 / 冊 / 家族</th><th class=\"num\">七日次數</th><th>最後</th></tr></thead><tbody>" % e(" · ".join("%s %d" % (k, n) for k, n in a["kinds_7d"].items())))
        for t in a["top_ids_7d"]:
            H.append('<tr><td><code>%s</code></td><td class="num">%d</td><td>%s</td></tr>' % (e(t["id"]), t["n"], e(str(t["last"])[:16])))
        H.append("</tbody></table></div>")
    else:
        H.append('<p class="empty">VCGC 湖沒有 function_ledger 視圖(帳本不在或尚未入湖)</p>')
    H.append('<h2 id="assets-h">資產明細 <span style="color:var(--mute);font-weight:400;font-size:.82rem">湖表(增量 · 主鍵去重)+ 倉內既有資產(只讀 · 尚未入湖)</span></h2><div class="wrap"><table id="assets"><thead><tr><th>系統</th><th>類</th><th>名</th><th>表 / 檔</th><th class="num">列</th><th>最後更新</th><th class="num">大小</th><th>狀態</th></tr></thead><tbody>')
    for c in b["systems"]:
        for t in c["lake_tables"]:
            H.append('<tr data-sys="%s" data-name="%s" data-rows="%d"><td>%s</td><td>湖</td><td><code>%s</code></td><td>%d 分片 · %s</td><td class="num">%s</td><td>%s</td><td class="num">%s</td><td>增量 · 主鍵 %s</td></tr>' % (
                e(c["system"]), e((t["table"] + " " + c["lake_home"]).lower()), t["rows_view"], e(c["label"]), e(t["table"]), t["parts"], e(t["view"]), f"{t['rows_view']:,}", e(str(t["last_ingest"])[:16]), e(_hb(t["bytes"])), e(",".join(t["keys"]) or "—")))
        for x in c["legacy"]:
            stt = ("錯:" + x["error"][:60]) if x.get("error") else ("尚未入湖" + (" · 壞檔 %d" % x["bad_files"] if x.get("bad_files") else ""))
            H.append('<tr data-sys="%s" data-name="%s" data-rows="%d"><td>%s</td><td>%s</td><td><code>%s</code></td><td>%s</td><td class="num">%s</td><td>%s</td><td class="num">%s</td><td>%s</td></tr>' % (
                e(c["system"]), e((x["name"] + " " + x["rel"]).lower()), x.get("rows") or 0, e(c["label"]), e(x["kind"]), e(x["rel"]), ("%d 表" % len(x["tables"])) if x["kind"] == "duckdb" else ("%d 檔" % x["files"]),
                f"{x.get('rows') or 0:,}", e(str(x["mtime"])[:16]), e(_hb(x["bytes"])), e(stt)))
    H.append('</tbody></table></div><p class="empty" id="empty" hidden>沒有符合的列</p>')
    ing = b["ingest"]
    if "tables" in ing:
        H.append('<h2 id="ingest">本輪 VCGC 入湖收據 <span style="color:var(--mute);font-weight:400;font-size:.82rem">增量:同主鍵跳過 · 管家 %s</span></h2><div class="wrap"><table><thead><tr><th>表</th><th>來源</th><th class="num">讀到</th><th class="num">新入</th><th class="num">跳過</th></tr></thead><tbody>' % e(ing.get("status", {}).get("catalog") or ""))
        for t, r in ing["tables"].items():
            H.append('<tr><td><code>%s</code></td><td><code>%s</code></td><td class="num">%d</td><td class="num">%d</td><td class="num">%d</td></tr>' % (e(t), e(r["source"]), r["rows_in"], r["added"], r["skipped"]))
        H.append("</tbody></table></div>")
    H.append('<p style="color:var(--mute);font-size:.85rem">%s</p><script>%s</script></main></body></html>' % (e(b["law"]), JS))
    return "\n".join(H)


def _heat(n) -> str:
    n = int(n or 0)
    return "" if n <= 0 else ("h1" if n < 5 else ("h2" if n < 50 else "h3"))


def write_outputs(via: Path, b: dict) -> dict:
    out = via / OUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    (out / "LAKE_MATRIX_latest.json").write_text(json.dumps(b, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (out / "LAKE_MATRIX_latest.md").write_text(to_md(b), encoding="utf-8")
    (out / "LAKE_MATRIX_latest.html").write_text(to_html(b), encoding="utf-8")
    with (out / "lake_matrix_ledger.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": b["at"], "engine": ENGINE, "lamp": b["overall"]["lamp"], "systems": {c["system"]: c["lamp"] for c in b["systems"]}, "lake_root": b["lake_root"],
                            "ingest_added": sum(r.get("added", 0) for r in b["ingest"].get("tables", {}).values())}, ensure_ascii=False) + "\n")
    return {"json": str(out / "LAKE_MATRIX_latest.json"), "md": str(out / "LAKE_MATRIX_latest.md"), "html": str(out / "LAKE_MATRIX_latest.html"), "ledger": str(out / "lake_matrix_ledger.jsonl")}


def run(via: Path, root: str | None = None, no_write: bool = False, open_after: bool = False) -> int:
    r, src = resolve_root(via, root)
    b = build(via, r, src, ingest=not no_write)
    paths = {} if no_write else write_outputs(via, b)
    print("[%s] %s · 湖根 %s(%s)" % (b["overall"]["lamp"], ENGINE, b["lake_root"], b["lake_root_source"]))
    for c in b["systems"]:
        print("  [%s] %s · %s" % (c["lamp"], c["label"], c["why"]))
    if "tables" in b["ingest"]:
        print("  入湖:" + " · ".join("%s +%d(跳 %d)" % (t, r_["added"], r_["skipped"]) for t, r_ in b["ingest"]["tables"].items()))
    a = b["activity"]
    print("  七日工具事件:" + (" · ".join("%s %d" % (k, n) for k, n in a["kinds_7d"].items()) or "無"))
    if paths:
        print("  落檔:" + " · ".join(paths.values()))
        if open_after:
            webbrowser.open(Path(paths["html"]).as_uri())
    return 0 if b["overall"]["lamp"] in ("GREEN", "YELLOW") else 1


# ───────────────────────── 自測 ─────────────────────────
def _fixture(td: Path, now: datetime) -> Path:
    import duckdb
    via = td / "VeritasIntelligenceAnalytics"
    (via / "supportive modules").mkdir(parents=True)
    (via / "supportive modules" / "VIA_ParquetLake_v0100.py").write_text((VIA / "supportive modules" / "VIA_ParquetLake_v0100.py").read_text(encoding="utf-8"), encoding="utf-8")

    def w(rel, text):
        p = via / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    ts = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    y = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    w("supportive modules/registry/VIA_VCGC_FunctionLedger_v0100.jsonl", "\n".join(json.dumps(r) for r in [
        {"ts": ts, "event": "changed", "id": "book:A", "kind": "book", "run": "t1"}, {"ts": ts, "event": "added", "id": "family:B", "kind": "family", "run": "t1"},
        {"ts": y, "event": "changed", "id": "book:A", "kind": "book", "run": "t0"}, {"ts": "2026-01-01T00:00:00+00:00", "event": "baseline", "id": "verb:x", "kind": "verb"}]) + "\n")
    w("VIA_Reports/vcgc/toolboard_ledger.jsonl", json.dumps({"at": ts, "lamp": "YELLOW", "lamps": {"backup": "YELLOW"}}) + "\n")
    w("VIA_Reports/gate/gate_ledger.jsonl", json.dumps({"run": "gate-1", "at": y, "verdict": "GREEN"}) + "\n")
    w("VIA_Reports/vcgc/TEST_STATE_v0101.json", json.dumps({"V-token": {"lamp": "GREEN", "at": ts, "secs": 1.0}, "C-x": {"lamp": "RED", "at": y}}))
    w("docs/handoff/backup/BACKUP_MANIFEST_20261109_155702Z.json", json.dumps({"stamp": "20261109_155702Z", "at": y, "git": {"head": "abc"}, "systems": {"VCGC": {"zip": "VCGC.zip", "zip_sha256": "x", "zip_bytes": 1, "count": 2}, "VDF": {"zip": "VDF.zip", "zip_sha256": "y", "zip_bytes": 1, "count": 3}}}))
    w("docs/handoff/backup/BACKUP_MANIFEST_latest.json", "{}")
    dbp = via / "functional modules/VDF/output_hub/universe/VDF_Universe.duckdb"
    dbp.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(dbp))
    con.execute("create table universe_list(code varchar, name varchar)")
    con.execute("insert into universe_list values ('2330','TSMC'),('2317','HonHai')")
    con.close()
    import pyarrow as pa
    import pyarrow.parquet as pq
    ex = via / "VIA_Reports/vqg/vap_export/vap_export_1/backtest"
    ex.mkdir(parents=True)
    pq.write_table(pa.table({"date": ["2026-11-01", "2026-11-02"], "eq": [1.0, 1.1]}), ex / "2330_TW.parquet")
    (ex / "broken.parquet").write_bytes(b"not parquet")
    return via


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))
    try:
        import duckdb  # noqa: F401
        import pyarrow  # noqa: F401
    except Exception as ex:  # noqa: BLE001
        print("[FAIL] %s selftest · 環境缺 duckdb / pyarrow:%s(不假綠)" % (ENGINE, ex))
        return 1
    now = datetime(2026, 11, 10, 3, 0, tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory(prefix="via_lakematrix_") as td:
        via = _fixture(Path(td), now)
        root, src = resolve_root(via)
        chk("ⓐ 湖根:無 --root / env / 冊 → 倉內 VIA_Reports/lake(來源照實)", root == (via / OUT_DIR).resolve() and src.startswith("repo_default"), src)
        b = build(via, root, src, now)
        S = {c["system"]: c for c in b["systems"]}
        ing = b["ingest"]["tables"]
        chk("ⓑ VCGC 入湖:function_ledger 4 · toolboard 1 · gate 1 · test_state 2 · backup_manifest 2(latest 不重讀)· mutual / closeout 來源不在 0",
            ing["function_ledger"]["added"] == 4 and ing["toolboard_ledger"]["added"] == 1 and ing["gate_ledger"]["added"] == 1 and ing["test_state"]["added"] == 2 and ing["backup_manifest"]["added"] == 2
            and ing["mutual_ledger"]["added"] == 0 and "note" in ing["mutual_ledger"], {k: v["added"] for k, v in ing.items()})
        chk("ⓒ 燈:VCGC GREEN(剛入湖)· VDF YELLOW 尚未入湖(duckdb 1 庫 2 列)· VQG YELLOW(parquet 1 好 1 壞 · 壞檔照實)· VRN-2 / VAP GRAY · 總燈 GRAY(最差)",
            S["VCGC"]["lamp"] == "GREEN" and S["VDF"]["lamp"] == "YELLOW" and S["VDF"]["legacy"][0]["kind"] == "duckdb" and S["VDF"]["legacy_rows"] == 2
            and S["VQG"]["lamp"] == "YELLOW" and S["VQG"]["legacy"][0]["bad_files"] == 1 and S["VQG"]["legacy_rows"] == 2 and S["VRN2"]["lamp"] == "GRAY" and S["VAP"]["lamp"] == "GRAY" and b["overall"]["lamp"] == "GRAY",
            {k: (v["lamp"], v["why"][:40]) for k, v in S.items()})
        a = b["activity"]
        d0, d1 = now.strftime("%Y-%m-%d"), (now - timedelta(days=1)).strftime("%Y-%m-%d")
        chk("ⓓ 工具活動矩陣:今 changed 1 added 1 · 昨 changed 1 · 2026-01 基線不在七日 · 類 book 2 family 1 · 最活躍 book:A 2 · 帳本視圖 5(mutual / closeout 來源不在就沒有視圖)",
            a["events_by_day"].get(d0) == {"added": 1, "changed": 1} and a["events_by_day"].get(d1) == {"changed": 1} and a["kinds_7d"] == {"book": 2, "family": 1}
            and a["top_ids_7d"][0]["id"] == "book:A" and a["top_ids_7d"][0]["n"] == 2 and len(a["ledger_latest"]) == 5, (a["kinds_7d"], a["top_ids_7d"][:1], sorted(a["ledger_latest"])))
        chk("ⓔ 五系統 × 日:VCGC 今天有活動 · 七欄日期連續到今天", a["systems_by_day"]["VCGC"][d0] > 0 and a["days"][-1] == d0 and len(a["days"]) == 7)
        b2 = build(via, root, src, now)
        ing2 = b2["ingest"]["tables"]
        chk("ⓕ 再跑一次 = 增量 0(全跳過)· 湖表列數不變 · 燈不變", all(v["added"] == 0 for v in ing2.values()) and ing2["function_ledger"]["skipped"] == 4
            and {c["system"]: c["lamp"] for c in b2["systems"]} == {c["system"]: c["lamp"] for c in b["systems"]}
            and [t["rows_view"] for t in b2["ingest"]["status"]["tables"]] == [t["rows_view"] for t in b["ingest"]["status"]["tables"]], {k: v["skipped"] for k, v in ing2.items()})
        h = to_html(b2)
        md = to_md(b2)
        chk("ⓖ HTML:燈號條在控制列與矩陣之前 · 五個系統鈕 + 全部 + 搜尋 + 只看有資料 + 重設 · 資產列帶 data-sys/data-name/data-rows · 一支 script",
            h.index('id="lamps"') < h.index('id="controls"') < h.index('id="activity"') < h.index('id="tools"') < h.index('id="assets"')
            and all('id="btn-%s"' % s in h for s in SYSTEMS) and 'id="btn-all"' in h and 'id="q"' in h and 'id="only-data"' in h and 'id="reset"' in h
            and h.count('data-sys="VDF" data-name=') >= 1 and h.count("<script>") == 1 and "lamp big GRAY" in h)
        chk("ⓗ md:第一節是五系統燈 · 五節齊", md.index("## 1. 五系統燈") < md.index("## 2.") < md.index("## 3.") < md.index("## 4.") < md.index("## 5."))
        paths = write_outputs(via, b2)
        n = len((via / OUT_DIR / "lake_matrix_ledger.jsonl").read_text(encoding="utf-8").splitlines())
        chk("ⓘ 落檔三份 + 只增帳 1 行 · 管家 VCGC_catalog.duckdb 在湖內 · 他系統夾未被建立(不代寫)",
            all(Path(p).exists() for p in paths.values()) and n == 1 and (root / "VCGC" / "VCGC_catalog.duckdb").exists() and not (root / "VDF").exists() and not (root / "VQG").exists())
        os.environ["VIA_DATA_HOME"] = str(Path(td) / "home")
        (Path(td) / "home").mkdir()
        r2, s2 = resolve_root(via)
        del os.environ["VIA_DATA_HOME"]
        chk("ⓙ env VIA_DATA_HOME 存在時優先 · --root 再優先", r2 == (Path(td) / "home").resolve() and s2 == "env VIA_DATA_HOME" and resolve_root(via, str(Path(td)))[1] == "--root")
    with tempfile.TemporaryDirectory(prefix="via_lakematrix_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        (via / "supportive modules").mkdir(parents=True)
        (via / "supportive modules" / "VIA_ParquetLake_v0100.py").write_text((VIA / "supportive modules" / "VIA_ParquetLake_v0100.py").read_text(encoding="utf-8"), encoding="utf-8")
        b = build(via, (via / OUT_DIR), "repo_default", now)
        chk("ⓚ 空樹:五系統全 GRAY · 入湖 0 · 工具活動空 · 不炸 · rc 1(不是綠)", all(c["lamp"] == "GRAY" for c in b["systems"]) and all(v["added"] == 0 for v in b["ingest"]["tables"].values())
            and b["activity"]["events_by_day"] == {} and run(via, no_write=True) == 1)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest()")[0]
    chk("ⓛ 邊界:不開網路 / 不開子行程 · 只寫 <root>/VCGC 與 VIA_Reports/lake(他系統只讀)",
        not re.search(r"^\s*(import|from)\s+(urllib|socket|requests|http\b|subprocess)", body, re.M) and 'Lake(root, "VCGC")' in body and "read_only=True" in body)
    bad = len(ok) - sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if not bad else "FAIL", ENGINE, sum(ok), len(ok)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="VIA_LakeMatrix", description=__doc__.splitlines()[0])
    ap.add_argument("verb", nargs="?", default="run", choices=["run", "selftest"])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--root", default=None, help="湖根(各系統子夾 <root>/<SYS>);預設 env VIA_DATA_HOME → 冊 → 倉內 VIA_Reports/lake")
    ap.add_argument("--via", default=None, help="VIA 根(預設由本檔位置推)")
    ap.add_argument("--no-write", action="store_true", help="只看不寫(不入湖 · 不落檔)")
    ap.add_argument("--open", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest or a.verb == "selftest":
        return selftest()
    via = Path(a.via).resolve() if a.via else VIA
    if (via / "VeritasIntelligenceAnalytics").is_dir():
        via = via / "VeritasIntelligenceAnalytics"
    return run(via, root=a.root, no_write=a.no_write, open_after=a.open)


if __name__ == "__main__":
    sys.exit(main())
