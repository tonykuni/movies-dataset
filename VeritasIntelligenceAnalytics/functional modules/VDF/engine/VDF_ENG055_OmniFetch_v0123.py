"""VDF_ENG055_OmniFetch tail v0123 — L11 sentiment 同批重鍵先去重(掉球 Z297;操作員 2026-10-14「繼續修 Z297」)。

實錄:vdf_global_market.duckdb · sentiment_daily 256 列、相異 252 列 —— 2026-09-23 / 09-24 各 3 筆一模一樣(CNN_FEAR_GREED)。
根因:L11 把 CNN graphdata 的歷史序列(最近幾天同一個 UTC 日有好幾個時間點)和「今值」(fear_and_greed.timestamp 的日)
接成一批送進正典 upsert_rows(鍵 date+index);正典的 anti-join 只擋「庫裡已在的鍵」,同一批裡重複的鍵照插(v0110 起
dedup_source=False,原文如此;其他寫入者靠呼叫端先去重)。ENG229 的 rows_from_graphdata 本來就「同日留最後一筆」,L11 沒有。

本支只做一件事:L11 送庫前依 (date, index) 留最後一筆(今值排在最後 = 當日最新值;與 ENG229 同一判準),
LANES 的 L11 換成本支的 lane_sentiment;其餘全照前版(前版 = 同族版號小於自己的最新一支,照尾版律取,不釘版號)。
庫裡已經重複的列由 VDF_ENG229 v0101 `dedupe` 清(本支不碰既有資料)。selftest 不抓網路(假工具 + 暫存夾)。
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
    VIA_ACCEL = None
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
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG055_OmniFetch"
SENT_TABLE = "sentiment_daily"
SENT_KEYS = ["date", "index"]


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _prior_path() -> Path:
    """同族版號小於自己的最新一支(尾版律;不釘版號)。"""
    me = _vnum(__file__)
    olds = sorted((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < me), key=_vnum)
    if not olds:
        raise FileNotFoundError(f"{_STEM}:版號小於 v{me:04d} 的前版不在")
    return olds[-1]


def _load(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR = _load(_prior_path(), "_vdf_eng055_prior_for_" + Path(__file__).stem)
_PRIOR_LANE_SENTIMENT = PRIOR.lane_sentiment


def __getattr__(name):
    """前版公開面照轉(TAILAPI:尾版不少名字)。"""
    return getattr(PRIOR, name)


def dedupe_last(rows: list, keys: list) -> tuple:
    """同鍵留最後一筆,位置照該鍵第一次出現的次序。回 (去重後列, 丟掉幾筆)。"""
    keep = {}
    for r in rows:
        keep[tuple(r.get(k) for k in keys)] = r
    return list(keep.values()), len(rows) - len(keep)


def lane_sentiment(net) -> dict:
    """L11(v0123):同前版 CNN Fear&Greed 官方 dataviz API(curl_bytes 車道 · 原始 JSON 先存),
    差別只在送庫前依 (date, index) 留最後一筆 —— 歷史序列同日多點 + 今值不再插成多列(Z297)。"""
    if not hasattr(net, "curl_bytes"):
        return {"state": "FAIL", "note": "網路工具缺 curl_bytes 車道(要 SUP_MDL740 v0114+;不自己打 curl)"}
    rb = net.curl_bytes(PRIOR.CNN_FG, timeout=25, follow=False, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://edition.cnn.com/markets/fear-and-greed",
        "Accept": "application/json"})
    body = (rb.get("data") or b"").decode("utf-8", "replace") if rb.get("state") == "OK" else ""
    if rb.get("state") != "OK" or not body.strip().startswith("{"):
        return {"state": "DENY" if rb.get("state") == "DENY" else "FAIL",
                "note": f"CNN F&G 不可達:{(str(rb.get('note', '')) or body)[:60]}"}
    d = json.loads(body)
    out = Path(PRIOR.OUT)
    out.mkdir(parents=True, exist_ok=True)
    raw = out / f"cnn_fear_greed_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    raw.write_text(body, encoding="utf-8")   # 先保留原始(操作員令)
    rows = []
    hist = (d.get("fear_and_greed_historical") or {}).get("data") or []
    for x in hist:
        ts = x.get("x")
        if ts is None:
            continue
        rows.append({"date": datetime.fromtimestamp(ts / 1000, timezone.utc).strftime("%Y-%m-%d"),
                     "index": "CNN_FEAR_GREED", "score": x.get("y"),
                     "rating": x.get("rating")})
    now = d.get("fear_and_greed") or {}
    if now.get("score") is not None:
        rows.append({"date": str(now.get("timestamp", ""))[:10],
                     "index": "CNN_FEAR_GREED", "score": now["score"],
                     "rating": now.get("rating")})
    if not rows:
        return {"state": "EMPTY", "note": "零列"}
    rows, dropped = dedupe_last(rows, SENT_KEYS)
    PRIOR.write_parquet(rows, SENT_TABLE)
    n = PRIOR.upsert(PRIOR.DB_GL, SENT_TABLE, rows, SENT_KEYS)
    return {"state": "OK", "rows": len(rows), "db": n, "dup_dropped": dropped,
            "note": f"CNN F&G 今值 {round(float(now.get('score', 0)), 1)}"
                    f"({now.get('rating')});同日重點去 {dropped} 筆;AAII 訂閱牆候源"}


PRIOR.lane_sentiment = lane_sentiment
PRIOR.LANES["L11"] = ("sentiment", lane_sentiment)


def main() -> int:
    return PRIOR.main()


# ---------------------------------------------------------------- 自測(假網路工具 + 暫存夾;零外呼)
class _FakeNet:
    """CNN graphdata 形狀:09-22 一點 · 09-23 兩點(同 UTC 日)· 09-24 一點 + 今值 09-24。"""
    def __init__(self):
        day = 86_400_000
        t22 = 1_790_035_200_000   # 2026-09-22T00:00:00Z
        d = {"fear_and_greed": {"score": 36.11, "rating": "fear", "timestamp": "2026-09-24T21:00:00+00:00"},
             "fear_and_greed_historical": {"data": [
                 {"x": t22, "y": 40.0, "rating": "fear"},
                 {"x": t22 + day, "y": 35.5, "rating": "fear"},
                 {"x": t22 + day + 3_600_000 * 20, "y": 35.9, "rating": "fear"},
                 {"x": t22 + 2 * day, "y": 36.0, "rating": "fear"}]}}
        self.body = json.dumps(d).encode("utf-8")

    def curl_bytes(self, url, headers=None, timeout=30, follow=True):
        return {"state": "OK", "data": self.body}


def _dups(db: Path) -> tuple:
    import duckdb
    con = duckdb.connect(str(db), read_only=True)
    try:
        n, k = con.execute(f'SELECT COUNT(*), COUNT(DISTINCT (date, "index")) FROM "{SENT_TABLE}"').fetchone()
        last = con.execute(f'SELECT score FROM "{SENT_TABLE}" WHERE date = ?', ["2026-09-23"]).fetchall()
        return int(n), int(k), [r[0] for r in last]
    finally:
        con.close()


def selftest() -> int:
    import tempfile
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" — {note}" if note else ""))

    text = Path(__file__).read_text(encoding="utf-8")
    chk("① 加速橋 + 網路橋在尾版上", "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text)
    chk("② LANES L11 = 本支 lane_sentiment · 前版公開面照轉",
        PRIOR.LANES["L11"][1] is lane_sentiment and callable(globals()["__getattr__"]("run")), f"前版 {_prior_path().name}")
    rows, dropped = dedupe_last([{"date": "a", "index": "X", "v": 1}, {"date": "b", "index": "X", "v": 2},
                                 {"date": "a", "index": "X", "v": 3}], SENT_KEYS)
    chk("③ dedupe_last 同鍵留最後一筆、次序照首見", [r["v"] for r in rows] == [3, 2] and dropped == 1)
    saved = (PRIOR.OUT, PRIOR.DB_GL)
    with tempfile.TemporaryDirectory() as td:
        try:
            PRIOR.OUT = Path(td) / "fixed"
            PRIOR.DB_GL = PRIOR.OUT / "gl.duckdb"
            r1 = lane_sentiment(_FakeNet())
            r2 = lane_sentiment(_FakeNet())
            n, k, last = _dups(PRIOR.DB_GL)
            chk("④ 本支:同批 5 點 → 3 天 3 列,重跑冪等", r1["state"] == "OK" and r1["dup_dropped"] == 2 and n == k == 3 and r2["db"] == 3,
                f"列 {n} · 相異鍵 {k} · 去 {r1['dup_dropped']}")
            chk("⑤ 同日留最後一筆(09-23 = 當日最後一點 35.9)", last == [35.9], str(last))
            PRIOR.OUT = Path(td) / "prior"
            PRIOR.DB_GL = PRIOR.OUT / "gl.duckdb"
            _PRIOR_LANE_SENTIMENT(_FakeNet())
            pn, pk, _ = _dups(PRIOR.DB_GL)
            chk("⑥ 對照:前版同一份輸入照插重鍵(本測抓得到 Z297)", pn > pk, f"前版 列 {pn} · 相異鍵 {pk}")
        finally:
            PRIOR.OUT, PRIOR.DB_GL = saved
    ok = all(results)
    print(f"  {'PASS' if ok else 'FAIL'} {sum(results)}/{len(results)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
