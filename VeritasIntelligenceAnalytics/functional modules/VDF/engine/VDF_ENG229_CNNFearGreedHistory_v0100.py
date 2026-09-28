#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG229_CNNFearGreedHistory v0100 — CNN 恐懼與貪婪指數「全歷史」回補(只增不覆寫)

操作員 2026-09-28:「GENERATE A PY CODE TO FETCH ALL HISTORICAL cnn fear and greed」。
既有 VDF_ENG055 lane_sentiment 呼叫 graphdata 不帶起始日 → 只拿到約一年(sentiment_daily 起點 2025-08-25)。
本支只做回補,和 ENG055 寫同一張表、同一組鍵(date+index),兩支並存不打架:

  ① 來源:CNN 官方 dataviz API  production.dataviz.cnn.io/index/fearandgreed/graphdata/{起始日}
     起始日由舊到新試(2011→2016→2018→2020-07-14→不帶),取第一個回得來的 —— CNN 太早的起點會回錯,不硬猜;
     實際最早日期照資料記,不宣稱比資料更早。
  ② 2020 年以前 CNN API 通常不給:可用 --csv 匯入操作員手上的歷史檔(欄 Date + Fear Greed/score),來源欄照實標檔名;
     不從網上抓第三方封存檔(來源不明不入正庫)。
  ③ 外呼一律走統包網路工具 SUP_MDL740 尾版的 curl_bytes(雙閘 VIA_NET_CONSENT + VIA_SCRAPE_CONSENT 在工具裡;
     閘沒開 = DENY、零外呼、零寫入;AI 永不代設同意閘 L07/L08)。原始 JSON 逐位元先存(操作員令)。
  ④ 入庫走正典 VIA_LibCanon.UTILS.upsert_rows(去重唯一實作;鍵已在 = 不動),表 vdf_global_market.duckdb · sentiment_daily。

用法(經 VCGC;VIA_FROM_VCGC=YES):
  python VDF_ENG229_CNNFearGreedHistory_v0100.py status                 # 唯讀:庫裡 CNN 列數 · 最早 · 最新
  python VDF_ENG229_CNNFearGreedHistory_v0100.py run [--start YYYY-MM-DD] [--csv 檔] [--dry]
  python VDF_ENG229_CNNFearGreedHistory_v0100.py --selftest             # 沙盒:假網路工具 + 暫存庫,零外呼
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
# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
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
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
OUT = VDF / "output_hub" / "mega"
DB_GL = OUT / "vdf_global_market.duckdb"
TABLE = "sentiment_daily"
KEYS = ["date", "index"]
INDEX = "CNN_FEAR_GREED"
URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
STARTS = ("2011-01-03", "2016-01-04", "2018-01-02", "2020-07-14", "")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
           "Referer": "https://edition.cnn.com/markets/fear-and-greed", "Accept": "application/json"}   # 沒 Referer CNN 回 418(ENG055 批141 實證)
ENGINE_TAG = "VDF_ENG229_CNNFearGreedHistory_v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def net_tool():
    """統包網路工具尾版(SUP_MDL740_NetUnified_v*.py;curl_bytes 車道 v0114+,雙閘在工具裡)。缺 = None。"""
    hits = sorted((VIA / "supportive modules" / "network").glob("SUP_MDL740_NetUnified_v*.py"))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("via_net_for_eng229", hits[-1])
    mod = importlib.util.module_from_spec(spec)
    sys.modules["via_net_for_eng229"] = mod
    spec.loader.exec_module(mod)
    return mod


def rows_from_graphdata(d: dict) -> list:
    """graphdata JSON → [{date, index, score, rating, source}];毫秒時間戳轉 UTC 日;同日留最後一筆。"""
    out = {}
    for x in (d.get("fear_and_greed_historical") or {}).get("data") or []:
        ts, y = x.get("x"), x.get("y")
        if ts is None or y is None:
            continue
        day = datetime.fromtimestamp(float(ts) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        out[day] = {"date": day, "index": INDEX, "score": round(float(y), 4), "rating": x.get("rating"),
                    "source": "CNN_DATAVIZ_API"}
    now = d.get("fear_and_greed") or {}
    if now.get("score") is not None and str(now.get("timestamp", ""))[:10]:
        day = str(now["timestamp"])[:10]
        out[day] = {"date": day, "index": INDEX, "score": round(float(now["score"]), 4), "rating": now.get("rating"),
                    "source": "CNN_DATAVIZ_API"}
    return [out[k] for k in sorted(out)]


def rows_from_csv(path: Path) -> tuple:
    """操作員手上的歷史檔:要有日期欄(Date/date)與分數欄(Fear Greed / score / value / fear_greed)。來源照實標檔名。
    回 (列, 丟掉的列數);丟掉的照實報,不默默吞。"""
    out, bad = {}, 0
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        cols = {c.lower().strip(): c for c in (rd.fieldnames or [])}
        dc = next((cols[k] for k in ("date", "日期") if k in cols), None)
        sc = next((cols[k] for k in ("fear greed", "fear_greed", "score", "value", "fear & greed") if k in cols), None)
        if not dc or not sc:
            raise ValueError(f"CSV 欄位認不得(要日期欄 + 分數欄):{rd.fieldnames}")
        for r in rd:
            raw_d, raw_s = str(r.get(dc) or "").strip(), str(r.get(sc) or "").strip()
            if not raw_d or not raw_s:
                bad += 1
                continue
            try:
                day = datetime.fromisoformat(raw_d[:10]).strftime("%Y-%m-%d")
                val = float(raw_s)
            except ValueError:
                bad += 1                          # 日期或分數讀不動:丟掉並計數
                continue
            if 0 <= val <= 100:
                out[day] = {"date": day, "index": INDEX, "score": round(val, 4), "rating": None, "source": "CSV:" + path.name}
            else:
                bad += 1
    return [out[k] for k in sorted(out)], bad


def fetch_history(net, starts=STARTS, out_dir: Path = OUT) -> dict:
    """由舊到新試起始日;第一個回 JSON 且有歷史的就用。原始位元組先存。回 {state, start, rows, raw, tried}。"""
    if net is None or not hasattr(net, "curl_bytes"):
        return {"state": "FAIL", "note": "網路工具缺(要 SUP_MDL740 v0114+ 的 curl_bytes;不自己打網路)", "rows": [], "tried": []}
    tried = []
    for s in starts:
        url = URL + (f"/{s}" if s else "")
        rb = net.curl_bytes(url, timeout=30, follow=False, headers=HEADERS)
        state = rb.get("state")
        if state == "DENY":
            return {"state": "DENY", "note": "同意閘沒開(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 是你的手)", "rows": [], "tried": tried + [(s or "-", "DENY")]}
        body = (rb.get("data") or b"") if state == "OK" else b""
        txt = body.decode("utf-8", "replace").strip()
        if state != "OK" or not txt.startswith("{"):
            tried.append((s or "-", (state or "FAIL") if state != "OK" else "NOTJSON"))   # 回得來但不是 JSON(錯誤頁 / 擋頁)
            continue
        try:
            d = json.loads(txt)
        except ValueError:
            tried.append((s or "-", "BADJSON"))
            continue
        rows = rows_from_graphdata(d)
        if not rows:
            tried.append((s or "-", "EMPTY"))
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        raw = out_dir / f"cnn_fear_greed_hist_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{s or 'default'}.json"
        raw.write_bytes(body)                    # 原始逐位元先存(操作員令)
        tried.append((s or "-", "OK"))
        return {"state": "OK", "start": s or "(不帶)", "rows": rows, "raw": str(raw), "tried": tried}
    return {"state": "FAIL", "note": "每個起始日都拿不到歷史", "rows": [], "tried": tried}


def store(rows: list, db: Path = DB_GL) -> tuple:
    """正典 upsert(鍵 date+index;已在 = 不動,只補空欄)。回 (新增, 表內 CNN 列數)。"""
    if not rows:
        return 0, count(db)[0]
    db.parent.mkdir(parents=True, exist_ok=True)
    new, _total = _LIB.UTILS.upsert_rows(db, TABLE, rows, KEYS, counts=True)
    return int(new), count(db)[0]


def count(db: Path = DB_GL) -> tuple:
    """唯讀:(CNN 列數, 最早, 最新)。庫或表不在 = (0, None, None)。"""
    if not Path(db).is_file():
        return 0, None, None
    import duckdb
    con = duckdb.connect(str(db), read_only=True)
    try:
        if TABLE not in {r[0] for r in con.execute("SHOW TABLES").fetchall()}:
            return 0, None, None
        n, lo, hi = con.execute(f'SELECT COUNT(*), MIN(CAST(date AS VARCHAR)), MAX(CAST(date AS VARCHAR)) FROM "{TABLE}" WHERE "index" = ?', [INDEX]).fetchone()
        return int(n or 0), lo, hi
    finally:
        con.close()


def export_csv(db: Path = DB_GL, path: Path | None = None) -> Path | None:
    """全歷史匯出一份 CSV(Date, Fear_Greed_Score, rating, source)給人看 / 給其他工具吃。"""
    if not Path(db).is_file():
        return None
    import duckdb
    path = path or (OUT / "cnn_fear_greed_history.csv")
    con = duckdb.connect(str(db), read_only=True)
    try:
        rows = con.execute(f'SELECT CAST(date AS VARCHAR), score, rating, source FROM "{TABLE}" WHERE "index" = ? ORDER BY date', [INDEX]).fetchall()
    except Exception:
        rows = con.execute(f'SELECT CAST(date AS VARCHAR), score, rating, NULL FROM "{TABLE}" WHERE "index" = ? ORDER BY date', [INDEX]).fetchall()
    finally:
        con.close()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Date", "Fear_Greed_Score", "rating", "source"])
        w.writerows(rows)
    return path


def run(args: list, net=None, db: Path = DB_GL, out_dir: Path = OUT) -> dict:
    starts = STARTS
    if "--start" in args and args.index("--start") + 1 < len(args):
        starts = (args[args.index("--start") + 1],)
    dry = "--dry" in args
    rows, notes = [], []
    if "--csv" in args and args.index("--csv") + 1 < len(args):
        p = Path(args[args.index("--csv") + 1])
        c, bad = rows_from_csv(p)
        rows += c
        notes.append(f"CSV {p.name} {len(c)} 列 · 丟掉 {bad} 列(日期/分數讀不動或超出 0–100)")
    f = fetch_history(net if net is not None else net_tool(), starts, out_dir)
    notes.append(f"CNN {f['state']} 起始 {f.get('start', '-')} · 試 {f['tried']}")
    rows += f["rows"]
    # 同一天 CSV 與 API 都有 → API 優先(官方)
    merged = {}
    for r in rows:
        if r["date"] not in merged or r["source"] == "CNN_DATAVIZ_API":
            merged[r["date"]] = r
    rows = [merged[k] for k in sorted(merged)]
    added, total = (0, count(db)[0]) if dry else store(rows, db)
    state = f["state"] if f["state"] in ("DENY", "FAIL") and not rows else ("OK" if rows else f["state"])
    n, lo, hi = count(db)
    return {"engine": ENGINE_TAG, "state": state, "fetched": len(f["rows"]), "rows_in": len(rows), "added": added,
            "table_rows": n, "earliest": lo, "latest": hi, "dry": dry, "raw": f.get("raw"), "notes": notes,
            "fetch_state": f["state"]}


def _allowed() -> bool:
    return os.environ.get("VIA_FROM_VCGC") == "YES"


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if not _allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "只經 VCGC(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = next((x for x in a if not x.startswith("-")), "status")
    if verb == "status":
        n, lo, hi = count()
        print(f"  [CNN F&G] {DB_GL.name} · {TABLE} · {INDEX} {n} 列 · {lo or '—'} → {hi or '—'}")
        return 0 if n else 2
    if verb == "run":
        r = run(a)
        p = export_csv() if r["table_rows"] else None
        print(json.dumps(r, ensure_ascii=False, indent=1))
        print(f"  [CNN F&G] {r['state']} · 抓到 {r['fetched']} · 新增 {r['added']} · 表內 {r['table_rows']} 列 · {r['earliest']} → {r['latest']}"
              + (f" · CSV {p}" if p else ""))
        return {"OK": 0, "DENY": 4, "FAIL": 1}.get(r["state"], 2)
    print(__doc__)
    return 2


# ---------------------------------------------------------------- 自測(沙盒:假網路工具 + 暫存庫;零外呼)
class _FakeNet:
    def __init__(self, table: dict, deny: bool = False):
        self.table, self.deny, self.calls = table, deny, []

    def curl_bytes(self, url, headers=None, timeout=30, follow=True):
        self.calls.append(url)
        if self.deny:
            return {"state": "DENY", "note": "gate"}
        for k, v in self.table.items():
            if url.endswith(k):
                return v
        return {"state": "FAIL", "note": "no fixture"}


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    ms = lambda d: int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp() * 1000)
    js = {"fear_and_greed": {"score": 61.2, "rating": "greed", "timestamp": "2026-09-28T12:00:00+00:00"},
          "fear_and_greed_historical": {"data": [{"x": ms("2020-07-14"), "y": 50.0, "rating": "neutral"},
                                                 {"x": ms("2020-07-15"), "y": 52.5, "rating": "neutral"},
                                                 {"x": ms("2020-07-15") + 3600_000, "y": 53.0, "rating": "neutral"},
                                                 {"x": ms("2026-09-25"), "y": 60.0, "rating": "greed"}]}}
    ok_body = {"state": "OK", "data": json.dumps(js).encode()}
    fake = _FakeNet({"/2011-01-03": {"state": "FAIL", "note": "500"}, "/2016-01-04": {"state": "OK", "data": b"<html>err</html>"},
                     "/2018-01-02": {"state": "OK", "data": b'{"fear_and_greed_historical":{"data":[]}}'}, "/2020-07-14": ok_body})
    r = rows_from_graphdata(js)
    chk("① 毫秒時間戳 → UTC 日期;同日多筆留最後一筆;今值併入", [x["date"] for x in r] == ["2020-07-14", "2020-07-15", "2026-09-25", "2026-09-28"]
        and r[1]["score"] == 53.0, str([(x["date"], x["score"]) for x in r]))
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        f = fetch_history(fake, STARTS, td)
        chk("② 起始日由舊到新試:2011 回錯 · 2016 回 HTML · 2018 空 → 用 2020-07-14,不硬猜", f["state"] == "OK" and f["start"] == "2020-07-14"
            and [t[1] for t in f["tried"]] == ["FAIL", "NOTJSON", "EMPTY", "OK"], str(f["tried"]))
        chk("③ 原始 JSON 逐位元先存", f.get("raw") and Path(f["raw"]).read_bytes() == ok_body["data"])
        db = td / "gl.duckdb"
        a1 = run([], net=fake, db=db, out_dir=td)
        a2 = run([], net=fake, db=db, out_dir=td)
        chk("④ 正典 upsert 冪等:跑兩次表內列數不變、第二次新增 0", a1["table_rows"] == 4 and a2["table_rows"] == 4 and a2["added"] == 0,
            f"{a1['added']}/{a1['table_rows']} → {a2['added']}/{a2['table_rows']}")
        chk("⑤ 最早 / 最新照資料記", a1["earliest"] == "2020-07-14" and a1["latest"] == "2026-09-28", f"{a1['earliest']} → {a1['latest']}")
        deny = _FakeNet({}, deny=True)
        db2 = td / "deny.duckdb"
        d = run([], net=deny, db=db2, out_dir=td)
        chk("⑥ 同意閘沒開 = DENY:第一趟就停、零寫入、庫沒建", d["state"] == "DENY" and len(deny.calls) == 1 and not db2.exists(), str(d["notes"]))
        cp = td / "old.csv"
        cp.write_text("Date,Fear Greed\n2011-01-03,68\n2011-01-04,70\n2020-07-14,49\nbad,xx\n2011-01-05,150\n", encoding="utf-8")
        c = run(["--csv", str(cp)], net=fake, db=db, out_dir=td)
        n, lo, hi = count(db)
        chk("⑦ --csv 補 2020 前:新增 2 列、最早變 2011-01-03;同日 API 優先;壞列 / 超界丟掉且照實計數", c["added"] == 2 and lo == "2011-01-03" and n == 6
            and any("丟掉 2 列" in x for x in c["notes"]), f"{c['added']} · {lo} · {n} · {c['notes'][0]}")
        e = export_csv(db, td / "out.csv")
        lines = e.read_text(encoding="utf-8").splitlines()
        chk("⑧ 匯出全歷史 CSV(表頭 + 6 列、依日期排序)", lines[0].startswith("Date,Fear_Greed_Score") and len(lines) == 7 and lines[1].startswith("2011-01-03"), lines[1])
        dry = run(["--dry"], net=fake, db=td / "dry.duckdb", out_dir=td)
        chk("⑨ --dry 只抓不寫", dry["dry"] and not (td / "dry.duckdb").exists())
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    denied = main(["status"]) == 2
    if keep is not None:
        os.environ["VIA_FROM_VCGC"] = keep
    chk("⑩ 不經 VCGC 就拒跑", denied)
    ok = all(results)
    print(f"  [計] {ENGINE_TAG} 自測 {sum(results)}/{len(results)} · {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
