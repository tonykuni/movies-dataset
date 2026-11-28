#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL020_DataPlane v0102 — 薄尾:群組起始日 · 每檔版本號 + 註冊時間 · 輸入輸出分類矩陣(parquet io)

操作員 2026-11-15:「檔案名稱上註冊時就應該有版本號 註冊時間 輸入輸出參數分類矩陣表也是 VDF 起始時間依照群體集體設定
輸入輸出清單較多來源也多可能要整理仔細」;「系統全部獨立 獨立修正 … 各有各的 MAIN SYSTEM MANAGER」。v0101 / v0100 一字不動。
本版多的(其餘照 v0101;__getattr__ 轉接):
  ① 冊 VDF_DataPlane_SSOT_v0102:每個輸入 / 輸出帶 version + registered_at + group;5 個群組各自的起始日。
  ② parquet sync / backfill 沒給 --start 時照群組起始日分批(快照群整份);給了 --start 照 v0101 蓋過全部群。
  ③ 資料家清單 VDF_PARQUET_MANIFEST.json 每檔多 version(內容 sha256 變一次 +1:v0001 起)· registered_at(首次)· updated_at(內容最後變的時間)。
     檔名不改(ENG065 協定;下游 ENG065 / ENG079 / VRN2_VDFBridge / VAP 照讀)。
  ④ parquet io:輸入輸出分類矩陣 —— 輸入 7 + 輸出 21:編號 · 類別 · 群組 · 名稱 / 檔 · 庫 / 來源 · 鍵 · 寫入引擎 · 起始 · 冊上版本 · 註冊時間 ·
     資料家現況(內容版本 · 列 · 最新日)→ VIA_Reports/vdf/VDF_IO_MATRIX_latest.html / .json / .csv(卡片 = 每群大概 · 矩陣 = 明細)。
零網路(擷取由 ENG064)· 不碰 TA-Lib · 不讀寫同意閘 · 不刪使用者的檔。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
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
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本支零外呼。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import csv
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "VDF_MDL020_DataPlane v" + Path(__file__).stem.rsplit("_v", 1)[-1]
PRIOR_NAME = "VDF_MDL020_DataPlane_v0101.py"
IO_NAME = "VDF_IO_MATRIX_latest"


def _load_prior():
    spec = importlib.util.spec_from_file_location("vdf_mdl020_v0101_for_v0102", HERE / PRIOR_NAME)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V1 = _load_prior()                     # v0101(它的 P = v0100)
P = V1.P
V1.TAG = P.TAG = TAG
V1.BOOK_NAME = "VDF_DataPlane_SSOT_v0102.json"


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接(先 v0101,再 v0100)。"""
    return getattr(V1, name)


# ---------------------------------------------------------------- ③ 清單:每檔內容版本 + 註冊時間
_UPDATE_MANIFEST_V0100 = P.update_manifest


def update_manifest(pq_dir, files, results=None):
    p = Path(pq_dir) / P.MANIFEST
    try:
        old = (json.loads(p.read_text(encoding="utf-8")).get("files") or {}) if p.is_file() else {}
    except (OSError, ValueError):
        old = {}
    out = _UPDATE_MANIFEST_V0100(pq_dir, files, results)
    man = json.loads(p.read_text(encoding="utf-8"))
    now = P.utc_now()
    for f, rec in (man.get("files") or {}).items():
        o = old.get(f) or {}
        if not o:
            rec.update(version="v0001", registered_at=now, updated_at=now)
        elif o.get("sha256") != rec.get("sha256"):
            vn = int(str(o.get("version") or "v0000")[1:] or 0) + 1
            rec.update(version="v%04d" % vn, registered_at=o.get("registered_at") or now, updated_at=now)
        else:
            rec.update(version=o.get("version") or "v0001", registered_at=o.get("registered_at") or now, updated_at=o.get("updated_at") or now)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, p)
    return out


P.update_manifest = update_manifest


# ---------------------------------------------------------------- ② 群組起始日
def groups() -> dict:
    return V1.book().get("groups") or {}


def table_start(table: str, gs: dict | None = None):
    gs = groups() if gs is None else gs
    for g, v in gs.items():
        if table in (v.get("tables") or []):
            return g, v.get("start")
    return None, ((V1.book().get("params") or {}).get("fetch") or {}).get("start")


def min_start() -> str:
    starts = [v.get("start") for v in groups().values() if v.get("start")]
    return min(starts) if starts else "2022-01-01"


_SYNC_V0101 = V1.sync


def sync(home, pq_dir=None, only=None, dedup=False, start=None, stop_after=None) -> dict:
    """沒給 start:照群組起始日分批同步(同一個起始日的表一起跑);給了 start 照 v0101。"""
    if start or dedup:
        return _SYNC_V0101(home, pq_dir, only, dedup, start, stop_after)
    duckdb = P._duck()
    dbs = P.find_dbs(Path(home))
    con = duckdb.connect()
    att = P._attach(con, dbs)
    tables = sorted({t for a in att.values() if not a.startswith("ERR") for t in P._src_tables(con, a)})
    con.close()
    gs = groups()
    by_start = {}
    for t in tables:
        if only and t not in only:
            continue
        _g, s = table_start(t, gs)
        by_start.setdefault(s, []).append(t)
    merged = None
    for s, ts in sorted(by_start.items(), key=lambda kv: str(kv[0])):
        r = _SYNC_V0101(home, pq_dir, ts, False, s, stop_after)
        for x in r["results"]:
            x["start"] = s
        if merged is None:
            merged = r
        else:
            merged["results"] += r["results"]
            for k in ("written", "unchanged", "added_rows", "resumed", "batches", "errors"):
                merged[k] += r[k]
            merged["lamp"] = P.worst([merged["lamp"], r["lamp"]])
            merged["manifest"], merged["catalog"] = r["manifest"], r["catalog"]
    if merged is None:
        return _SYNC_V0101(home, pq_dir, ["__none__"], False, min_start(), stop_after)
    merged["start"] = "照群組:" + " · ".join("%s=%s" % (g, v.get("start") or "整份") for g, v in gs.items())
    return merged


V1.sync = sync                          # v0101 的 backfill 走這一支


# ---------------------------------------------------------------- ④ 輸入輸出分類矩陣
def io_matrix(home=None) -> dict:
    bk = V1.book()
    gs = bk.get("groups") or {}
    man = {}
    if home:
        mp = Path(home) / P.MANIFEST
        try:
            man = (json.loads(mp.read_text(encoding="utf-8")).get("files") or {}) if mp.is_file() else {}
        except (OSError, ValueError):
            man = {}
    rows = []
    for x in bk.get("inputs") or []:
        rows.append({"id": x["id"], "io": "輸入", "class": x.get("io_class") or "—", "group": "—", "name": x["name"], "where": x.get("source"), "key": "—",
                     "writers": "—", "start": "—", "version": x.get("version"), "registered_at": x.get("registered_at"), "now": x.get("gate")})
    for o in bk.get("outputs") or []:
        g = gs.get(o.get("group")) or {}
        m = man.get(o["file"]) or {}
        now = ("內容 %s · %s 列 · 最新 %s · 註冊 %s" % (m.get("version", "—"), format(m["rows"], ",") if m.get("rows") is not None else "—",
                                                   m.get("date_max") or "—", (m.get("registered_at") or "—")[:16])) if m else "資料家還沒有這個檔"
        rows.append({"id": o["id"], "io": "輸出", "class": "DataFrame · parquet", "group": "%s %s" % (o.get("group"), g.get("name", "")), "name": o["file"],
                     "where": "%s · %s" % (o["db"], o["table"]), "key": "+".join(o["key"]) if o.get("key") else "鍵律推", "writers": " ".join(o.get("writers") or []) or "冊上沒登",
                     "start": g.get("start") or "整份", "version": o.get("version"), "registered_at": o.get("registered_at"), "now": now, "_have": bool(m)})
    return {"tag": TAG, "ts": P.utc_now(), "book": bk.get("version"), "home": str(home) if home else None, "groups": gs, "rows": rows}


def io_page(mx: dict) -> str:
    css, note = P._spec_css()
    cols = [("id", "編號"), ("io", "輸入 / 輸出"), ("class", "類別"), ("group", "群組"), ("name", "名稱 / 檔"), ("where", "庫 · 表 / 來源"), ("key", "鍵"),
            ("writers", "寫入引擎"), ("start", "起始"), ("version", "冊上版本"), ("registered_at", "註冊時間"), ("now", "現況")]
    p = ['<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="via-page" content="VDF_IO_MATRIX">'
         '<meta name="viewport" content="width=device-width,initial-scale=1"><title>VDF 輸入輸出矩陣</title><style>%s</style><style>%s</style></head><body>' % (css, P.EXTRA_CSS),
         '<header class="dp-head"><div class="dp-r1">VERITAS INTELLIGENCE ANALYTICS</div><div class="dp-r2">VeritasDataForge</div>'
         '<div class="dp-r3">輸入輸出分類矩陣 · 冊 %s · 卡片看每群大概 · 矩陣看每一項的來源 · 鍵 · 起始 · 版本 · 註冊時間</div></header>' % P._e(mx["book"])]
    cards = []
    for g, v in mx["groups"].items():
        outs = [r for r in mx["rows"] if r["io"] == "輸出" and r["group"].startswith(g + " ")]
        cards.append('<div class="dp-kpi"><div class="k">%s %s</div><div class="v" style="font-size:15px">起始 %s · %d 個輸出 · 已有 %d</div>'
                     '<div class="dp-small">版本 %s · 註冊 %s</div></div>' % (P._e(g), P._e(v.get("name")), P._e(v.get("start") or "整份"), len(outs),
                                                                       sum(1 for r in outs if r.get("_have")), P._e(v.get("version")), P._e((v.get("registered_at") or "")[:16])))
    ins = [r for r in mx["rows"] if r["io"] == "輸入"]
    cards.append('<div class="dp-kpi"><div class="k">輸入</div><div class="v" style="font-size:15px">%d 項</div><div class="dp-small">%s</div></div>' % (
        len(ins), P._e(" · ".join(sorted({r["class"] for r in ins})))))
    p.append('<div class="dp-kpis">%s</div>' % "".join(cards))
    body = ["<tr>%s</tr>" % "".join("<td%s>%s</td>" % (' class="dp-small"' if k in ("where", "now", "registered_at") else "", P._e(r.get(k))) for k, _h in cols) for r in mx["rows"]]
    p.append('<section class="dp-sec"><h2>矩陣(輸入 %d · 輸出 %d)</h2><div class="dp-scroll"><table class="dp"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div></section>' % (
        len(ins), len(mx["rows"]) - len(ins), "".join("<th>%s</th>" % P._e(h) for _k, h in cols), "".join(body)))
    p.append('<p class="dp-small">%s · 資料家 %s · 樣式 %s</p></body></html>' % (P._e(TAG), P._e(mx["home"] or "沒給(只看冊)"), P._e(note)))
    return "".join(p)


def io(home=None, root=None) -> dict:
    mx = io_matrix(home)
    out = Path(root or P.VIA) / P.OUT_REL
    out.mkdir(parents=True, exist_ok=True)
    clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in mx["rows"]]
    (out / (IO_NAME + ".json")).write_text(json.dumps(dict(mx, rows=clean), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with open(out / (IO_NAME + ".csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(clean[0].keys()) if clean else ["id"])
        w.writeheader()
        w.writerows(clean)
    (out / (IO_NAME + ".html")).write_text(io_page(mx), encoding="utf-8")
    return {"html": str(out / (IO_NAME + ".html")), "rows": len(clean), "inputs": sum(1 for r in clean if r["io"] == "輸入"), "outputs": sum(1 for r in clean if r["io"] == "輸出")}


# ---------------------------------------------------------------- CLI
def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    sub = args[1] if args[:1] == ["parquet"] and len(args) > 1 else None
    if sub == "io":
        home, _w = P.resolve_home(P._opt(args, "--home"))
        r = io(home)
        print("[%s] 輸入輸出分類矩陣 · 輸入 %d · 輸出 %d · 冊 %s · %s" % (TAG, r["inputs"], r["outputs"], V1.book().get("version"), r["html"]))
        return 0
    if sub == "backfill" and not P._opt(args, "--start"):
        args = args + ["--start", min_start()]                  # 擷取從最早的群組起始日抓;sync 照各群自己的起始日
        os.environ["VDF_DP_GROUP_SYNC"] = "1"
    if sub == "sync" and not P._opt(args, "--start") and "--dedup" not in args:
        if not P.entry_ok():
            print("[%s] 拒絕寫入:由 VDF System Manager 總控(VIA_FROM_VDFSM=YES)或 VCGC" % TAG)
            return 2
        home, hwhy = P.resolve_home(P._opt(args, "--home"))
        if home is None:
            print("[%s] GRAY · %s" % (TAG, hwhy))
            return 2
        only = [x for x in (P._opt(args, "--only") or "").split(",") if x] or None
        t0 = time.time()
        r = sync(home, Path(P._opt(args, "--pq-dir")) if P._opt(args, "--pq-dir") else None, only)
        print("[%s] parquet sync(%s)%s · %.1fs · 寫 %d 檔 · 沒新鍵不動 %d 檔 · 補 %d 列 · 錯 %d" % (TAG, r.get("start"), r["lamp"], time.time() - t0, r["written"], r["unchanged"], r["added_rows"], r["errors"]))
        for x in r["results"]:
            if x.get("action") != "沒新鍵 · 不動檔":
                print("  %-18s %-34s 起 %-10s +%-8s %s" % (x.get("action"), x.get("file"), x.get("start") or "整份", x.get("added", 0), x.get("error") or ""))
        return {"GREEN": 0, "GRAY": 2}.get(r["lamp"], 1)
    return V1.main(args)


_BACKFILL_V0101 = V1.backfill


def backfill(home, start, end, skip_fetch=False, lists_arg=None, limit=None):
    """擷取照 start(最早群組起始日);sync 照各群自己的起始日(VDF_DP_GROUP_SYNC)。"""
    if os.environ.pop("VDF_DP_GROUP_SYNC", None):
        gate = P.inputs(home, lists_arg)
        if gate["lamp"] == "RED":
            return {"lamp": "RED", "why": "清單輸入閘紅 → 不擷取(先 VDF_SystemManager inputs 看哪一項)", "inputs": gate}
        f = {"state": "SKIPPED", "note": "--skip-fetch"} if skip_fetch else V1.fetch(start, end, limit)
        s = sync(home)
        v = V1.view(home, start=start)
        lamp = P.worst([gate["lamp"], s["lamp"], "YELLOW" if f["state"] in ("GATED", "FAIL", "ABSENT", "INTERRUPTED") else None])
        return {"lamp": lamp, "inputs": gate["lamp"], "fetch": f, "sync": s, "view": v}
    return _BACKFILL_V0101(home, start, end, skip_fetch, lists_arg, limit)


V1.backfill = backfill


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:280]) if note and not cond else ""), flush=True)

    bk = V1.book()
    tabs = {o["table"] for o in bk.get("outputs") or []}
    gt = [t for v in (bk.get("groups") or {}).values() for t in v["tables"]]
    chk("① 冊 v0102:5 群 · 21 個輸出每個都在剛好一群 · 每個輸入 / 輸出都有 version + registered_at · 財報期別參數在 · v0101 冊不動",
        bk.get("version") == "v0102" and len(bk.get("groups") or {}) == 5 and sorted(gt) == sorted(tabs) and len(gt) == len(set(gt)) == 21
        and all(x.get("version") and x.get("registered_at") for x in (bk.get("outputs") or []) + (bk.get("inputs") or []))
        and (bk.get("params") or {}).get("fin_period") and (HERE / "VDF_DataPlane_SSOT_v0101.json").is_file())
    duckdb = P._duck()
    with tempfile.TemporaryDirectory() as td:
        h = Path(td) / "vdf_database"
        (h / "output_hub" / "mega").mkdir(parents=True)
        c = duckdb.connect(str(h / "output_hub" / "mega" / "vdf_tw_market.duckdb"))
        c.execute("CREATE TABLE tw_daily_prices AS SELECT strftime(DATE '2021-10-01' + INTERVAL (i * 10) DAY, '%Y-%m-%d') AS date, '2330' AS ticker, 1.0 * i AS close FROM range(30) t(i)")
        c.execute("CREATE TABLE tw_listings AS SELECT '2330' AS code, '台積電' AS name")
        c.execute("CREATE TABLE tw_monthly_revenue AS SELECT strftime(DATE '2021-07-01' + INTERVAL (i) MONTH, '%Y%m') AS ym, '2330' AS code, 10 + i AS revenue FROM range(12) t(i)")
        c.close()
        r = sync(h)
        res = {x["table"]: x for x in r["results"]}
        con = duckdb.connect()
        n_px = con.execute("SELECT COUNT(*) FROM read_parquet('%s')" % (h / "tw__tw_daily_prices.parquet")).fetchone()[0]
        old_px = con.execute("SELECT COUNT(*) FROM read_parquet('%s') WHERE date < '2022-01-01'" % (h / "tw__tw_daily_prices.parquet")).fetchone()[0]
        chk("② 照群組起始日:價量群 2022-01-01 起(2021 的列不輸出)· 清單群整份 · 基本面群 2022-01 起 · 每列記用了哪個起始日",
            old_px == 0 and n_px > 0 and res["tw_daily_prices"]["start"] == "2022-01-01" and res["tw_listings"]["start"] is None
            and con.execute("SELECT COUNT(*) FROM read_parquet('%s')" % (h / "tw__tw_monthly_revenue.parquet")).fetchone()[0] == 6, res)
        m1 = json.loads((h / P.MANIFEST).read_text(encoding="utf-8"))["files"]
        sync(h)
        m2 = json.loads((h / P.MANIFEST).read_text(encoding="utf-8"))["files"]
        c = duckdb.connect(str(h / "output_hub" / "mega" / "vdf_tw_market.duckdb"))
        c.execute("INSERT INTO tw_daily_prices VALUES ('2026-11-13', '2330', 99.0)")
        c.close()
        time.sleep(1.1)
        sync(h)
        m3 = json.loads((h / P.MANIFEST).read_text(encoding="utf-8"))["files"]
        f = "tw__tw_daily_prices.parquet"
        chk("③ 清單每檔:首次 v0001 + 註冊時間 · 內容沒變再跑版本與時間不動 · 內容變了 → v0002、註冊時間留首次、updated_at 換新 · 檔名不帶版號(協定不變)",
            m1[f]["version"] == "v0001" and m1[f]["registered_at"] and all(m2[f][k] == m1[f][k] for k in ("version", "registered_at", "updated_at", "sha256"))
            and m3[f]["version"] == "v0002"
            and m3[f]["registered_at"] == m1[f]["registered_at"] and m3[f]["updated_at"] != m1[f]["updated_at"] and (h / f).is_file(),
            [{k: m.get(f, {}).get(k) for k in ("version", "registered_at", "updated_at")} for m in (m1, m2, m3)])
        r = io(h, root=Path(td) / "via")
        mx = json.loads((Path(td) / "via" / P.OUT_REL / (IO_NAME + ".json")).read_text(encoding="utf-8"))
        pg = Path(r["html"]).read_text(encoding="utf-8")
        row = next(x for x in mx["rows"] if x["name"] == f)
        chk("④ 輸入輸出分類矩陣:輸入 7 + 輸出 21 · 每列有 類別 · 群組 · 起始 · 冊上版本 · 註冊時間 · 現況(內容版本 v0002)· JSON / CSV / HTML 都寫 · VeritasDataForge",
            r["inputs"] == 7 and r["outputs"] == 21 and row["version"] and row["registered_at"] and "v0002" in row["now"] and row["start"] == "2022-01-01"
            and (Path(td) / "via" / P.OUT_REL / (IO_NAME + ".csv")).is_file() and "VeritasDataForge" in pg and "<script" not in pg.lower(), row)
        con.close()
    cp = subprocess.run([sys.executable, str(HERE / PRIOR_NAME), "--selftest"], env=dict(os.environ, VIA_FROM_VDFSM="YES"),
                        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    last = [x for x in (cp.stdout or "").splitlines() if x.startswith("[計]")]
    chk("⑤ 前版 v0101 自測照過(%s)" % (last[-1][4:] if last else "沒有計數行"), cp.returncode == 0 and last and "PASS" in last[-1], (cp.stdout or cp.stderr)[-300:])
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 薄尾:v0101 / v0100 不改檔 · 前版公開名稱經 __getattr__ 轉接 · 不碰 TA-Lib / 同意閘 · 兩座橋在",
        (HERE / PRIOR_NAME).is_file() and callable(__getattr__("status")) and "[VIA:ACCEL-BRIDGE:v0100]" in text and "[VIA:NET-BRIDGE:v0100]" in text
        and not re.search(r"^\s*(import|from)\s+(talib|CGC_|VRN_|VQG_|VAP_)", text, re.M) and ("environ[" + '"VIA_NET_' + 'CONSENT"]') not in text)
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
