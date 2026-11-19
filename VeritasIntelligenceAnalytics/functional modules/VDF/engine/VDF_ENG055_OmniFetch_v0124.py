"""VDF_ENG055_OmniFetch tail v0124 — 系統獨立:VCGC 的 ScrapeGate 尺檔不在或壞掉時,本引擎照樣載得起來(改用 VDF 自己的同一把尺)。

v0123→v0124(2026-11-18;操作員「系統獨立主要是避免任一系統尤其是 VCGC 升級更動造成全面癱瘓」):
  演練實錄(整棵樹拿掉 CGC_*.py 後啟動 VDF):v0123 一載入就 FileNotFoundError(registry/CGC_MDL224_ScrapeGate_v*.py 不在);
  擷取冊裡 e055tw / e055yf / e055fed / e055oth 四列都是這一支。
  本支只改取尺那一段:尺檔在就用它(同一把尺,行為與 v0123 完全相同);不在或載不起來 → 用 VDF 自己的尺
  (判法逐字相同:VIA_NET_CONSENT=YES 且 VIA_SCRAPE_CONSENT 是 YES 或責任字串才開;其餘一律關)。其餘全照 v0123(下面原文保留)。

VDF_ENG055_OmniFetch tail v0123 — L11 sentiment 同批重鍵先去重(掉球 Z297;操作員 2026-10-14「繼續修 Z297」)。

實錄:vdf_global_market.duckdb · sentiment_daily 256 列、相異 252 列 —— 2026-09-23 / 09-24 各 3 筆一模一樣(CNN_FEAR_GREED)。
根因:L11 把 CNN graphdata 的歷史序列(最近幾天同一個 UTC 日有好幾個時間點)和「今值」(fear_and_greed.timestamp 的日)
接成一批送進正典 upsert_rows(鍵 date+index);正典的 anti-join 只擋「庫裡已在的鍵」,同一批裡重複的鍵照插(v0110 起
dedup_source=False,原文如此;其他寫入者靠呼叫端先去重)。ENG229 的 rows_from_graphdata 本來就「同日留最後一筆」,L11 沒有。

本支只做一件事:L11 送庫前依 (date, index) 留最後一筆(今值排在最後 = 當日最新值;與 ENG229 同一判準),
LANES 的 L11 換成本支的 lane_sentiment;其餘全照 v0122 的尾版律(本體 = 版號小於自己、不 exec 也不點名同族版號的最新一支 =
具體實作,在自己的 namespace 跑本體 —— 模組層覆寫照舊生效,tests/test_via_global_incremental_v0100 依賴這一點)。
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
import importlib.util as _tail_ilu
import sys as _tail_sys
from pathlib import Path as _TailPath

_TAIL_SELF = _TailPath(__file__).resolve()


def _tail_concrete_body():
    """同族版號小於自己的檔,由新往舊找第一支「程式碼裡不點名同族版號檔、也不 exec」的 = 具體實作本體。"""
    import ast as _ast
    import re as _re
    stem = _TAIL_SELF.name.rsplit("_v", 1)[0]
    sib = _re.compile(_re.escape(stem) + r"_v\d{4}\.py")
    unreadable = []
    for p in sorted((q for q in _TAIL_SELF.parent.glob(stem + "_v*.py") if q.name < _TAIL_SELF.name), reverse=True):
        try:
            tree = _ast.parse(p.read_text(encoding="utf-8-sig", errors="replace"))
        except SyntaxError as e:
            unreadable.append(f"{p.name}:{e.lineno}")   # 讀不動的版本記下來,找不到本體時一起報
            continue
        first = tree.body[0] if tree.body else None
        doc = first.value if isinstance(first, _ast.Expr) and isinstance(getattr(first, "value", None), _ast.Constant) else None
        consts = [n.value for n in _ast.walk(tree) if isinstance(n, _ast.Constant) and isinstance(n.value, str) and n is not doc]
        execs = any(isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name) and n.func.id == "exec" for n in _ast.walk(tree))
        if not execs and not any(sib.search(c) for c in consts):
            return p
    raise FileNotFoundError(f"{stem}:版號小於 {_TAIL_SELF.name} 的具體實作本體不在" + (f"(讀不動:{', '.join(unreadable)})" if unreadable else ""))


def _tail_newest(folder, pattern):
    hits = sorted(folder.glob(pattern))
    if not hits:
        raise FileNotFoundError(f"{folder / pattern} 不在")
    return hits[-1]


_TAIL_SCRAPE_TOKEN = "I_ACCEPT_RESPONSIBLE_" + "SCRAPING"


def _tail_vdf_gate_open(env=None) -> bool:
    """VDF 自己的同一把尺(VCGC 的尺檔不在或載不起來時才用):兩道同意都在才開,其餘一律關。判法與 CGC_MDL224 v0100 逐字相同。"""
    env = __import__("os").environ if env is None else env
    return env.get("VIA_NET_" + "CONSENT") == "YES" and (env.get("VIA_SCRAPE_" + "CONSENT") or "") in ("YES", _TAIL_SCRAPE_TOKEN)


def _tail_gate_path(folder, pattern):
    """VCGC 的尺檔尾版;不在回 None(不丟例外:VDF 引擎不因為別的系統少一個檔就載不起來)。"""
    hits = sorted(folder.glob(pattern)) if folder.is_dir() else []
    return hits[-1] if hits else None


def _tail_resolve_gate(path, name):
    """有 VCGC 的尺就用它(同一把尺);不在或載不起來 → 用 VDF 自己的(同判法、同樣沒同意就關)。回 (函式, 來源說明)。"""
    if path is not None:
        try:
            fn = _tail_load(path, name).gate_open
            if callable(fn):
                return fn, "VCGC 尺 " + path.name
        except Exception as exc:  # 尺檔壞了也不讓引擎倒
            return _tail_vdf_gate_open, "VDF 自己的尺(VCGC 尺載不起來:" + type(exc).__name__ + ")"
    return _tail_vdf_gate_open, "VDF 自己的尺(VCGC 尺檔不在)"


_TAIL_BODY = _tail_concrete_body()
_TAIL_GATE = _tail_gate_path(_TAIL_SELF.parents[3] / "supportive modules" / "registry", "CGC_MDL224_ScrapeGate_v*.py")
_TAIL_SURFACE = ('lane_global', 'run', 'lane_sentiment')
_TAIL_NET_PATH = globals().get("VIA_NET_TOOL_PATH")


def _tail_load(path, name):
    spec = _tail_ilu.spec_from_file_location(name, path)
    module = _tail_ilu.module_from_spec(spec)
    _tail_sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_tail_name = __name__
globals()["__name__"] = "vdf_eng055_omnifetch_body_in_tail"   # the body's own main block must not fire
globals()["__file__"] = str(_TAIL_BODY)                 # the body reads paths / its own source from here
try:
    exec(compile(_TAIL_BODY.read_text(encoding="utf-8"), str(_TAIL_BODY), "exec"), globals())
finally:
    globals()["__name__"] = _tail_name
gate_open, _TAIL_GATE_SRC = _tail_resolve_gate(_TAIL_GATE, "scrape_gate_for_vdf_eng055_omnifetch_tail")  # v0124:VCGC 尺不在就用 VDF 自己的
_body_main = main  # noqa: F821
_PRIOR_LANE_SENTIMENT = lane_sentiment  # noqa: F821  本體那一版(自測對照用)
SENT_TABLE = "sentiment_daily"
SENT_KEYS = ["date", "index"]


def dedupe_last(rows: list, keys: list) -> tuple:
    """同鍵留最後一筆,位置照該鍵第一次出現的次序。回 (去重後列, 丟掉幾筆)。"""
    keep = {}
    for r in rows:
        keep[tuple(r.get(k) for k in keys)] = r
    return list(keep.values()), len(rows) - len(keep)


def lane_sentiment(net) -> dict:  # noqa: F811
    """L11(v0123):同本體 CNN Fear&Greed 官方 dataviz API(curl_bytes 車道 · 原始 JSON 先存),
    差別只在送庫前依 (date, index) 留最後一筆 —— 歷史序列同日多點 + 今值不再插成多列(Z297)。"""
    from datetime import timezone as _tz
    if not hasattr(net, "curl_bytes"):
        return {"state": "FAIL", "note": "網路工具缺 curl_bytes 車道(要 SUP_MDL740 v0114+;不自己打 curl)"}
    rb = net.curl_bytes(CNN_FG, timeout=25, follow=False, headers={  # noqa: F821
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://edition.cnn.com/markets/fear-and-greed",
        "Accept": "application/json"})
    body = (rb.get("data") or b"").decode("utf-8", "replace") if rb.get("state") == "OK" else ""
    if rb.get("state") != "OK" or not body.strip().startswith("{"):
        return {"state": "DENY" if rb.get("state") == "DENY" else "FAIL",
                "note": f"CNN F&G 不可達:{(str(rb.get('note', '')) or body)[:60]}"}
    d = json.loads(body)  # noqa: F821
    OUT.mkdir(parents=True, exist_ok=True)  # noqa: F821
    raw = OUT / f"cnn_fear_greed_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"  # noqa: F821
    raw.write_text(body, encoding="utf-8")   # 先保留原始(操作員令)
    rows = []
    hist = (d.get("fear_and_greed_historical") or {}).get("data") or []
    for x in hist:
        ts = x.get("x")
        if ts is None:
            continue
        rows.append({"date": datetime.fromtimestamp(ts / 1000, _tz.utc).strftime("%Y-%m-%d"),  # noqa: F821
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
    write_parquet(rows, SENT_TABLE)  # noqa: F821
    n = upsert(DB_GL, SENT_TABLE, rows, SENT_KEYS)  # noqa: F821
    return {"state": "OK", "rows": len(rows), "db": n, "dup_dropped": dropped,
            "note": f"CNN F&G 今值 {round(float(now.get('score', 0)), 1)}"
                    f"({now.get('rating')});同日重點去 {dropped} 筆;AAII 訂閱牆候源"}


LANES["L11"] = ("sentiment", lane_sentiment)  # noqa: F821


def main() -> int:  # noqa: F811
    return _body_main()


class _FakeSentNet:
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
        self.body = json.dumps(d).encode("utf-8")  # noqa: F821

    def curl_bytes(self, url, headers=None, timeout=30, follow=True):
        return {"state": "OK", "data": self.body}


def _sent_dups(db) -> tuple:
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
    from pathlib import Path as _P
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" — {note}" if note else ""))

    text = _TAIL_SELF.read_text(encoding="utf-8")
    chk("① 加速橋 + 網路橋在尾版上", "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and bool(_TAIL_NET_PATH))
    _NK, _SK = "VIA_NET_" + "CONSENT", "VIA_SCRAPE_" + "CONSENT"
    chk("② gate_open = 同一把尺(沒給同意 = 關);VCGC 尺在這台時用的就是它",
        gate_open({}) is False and (_TAIL_GATE is None or getattr(gate_open, "__module__", "") == "scrape_gate_for_vdf_eng055_omnifetch_tail"), _TAIL_GATE_SRC)
    import tempfile as _tf_gate
    _combos = [{}, {_NK: "YES"}, {_SK: "YES"}, {_NK: "YES", _SK: "OFF"}, {_NK: "YES", _SK: "YES"}, {_NK: "YES", _SK: _TAIL_SCRAPE_TOKEN}, {_NK: "NO", _SK: "YES"}, {_NK: "YES", _SK: "maybe"}]
    _expect = [False, False, False, False, True, True, False, False]          # 尺的規格:兩道同意都在才開
    _vcgc_fn = _tail_resolve_gate(_TAIL_GATE, "scrape_gate_selftest_probe")[0] if _TAIL_GATE is not None else None
    chk("⑦ 系統獨立:VDF 自己的尺八種同意組合都照規格;VCGC 的尺在這台時,兩把逐一相同(不在就只對規格,照實寫)",
        [_tail_vdf_gate_open(c) for c in _combos] == _expect and (_vcgc_fn is None or [_vcgc_fn(c) for c in _combos] == _expect),
        "VCGC 尺 " + (_TAIL_GATE.name + " 也對過" if _TAIL_GATE is not None else "不在這台:只對規格"))
    with _tf_gate.TemporaryDirectory(prefix="vdf_gate_indep_") as _gd:
        _gdp = _TailPath(_gd)
        _fn_missing, _src_missing = _tail_resolve_gate(_tail_gate_path(_gdp / "nope", "CGC_MDL224_ScrapeGate_v*.py"), "scrape_gate_selftest_missing")
        (_gdp / "CGC_MDL224_ScrapeGate_v9999.py").write_text("def broken(:\n", encoding="utf-8")
        _fn_broken, _src_broken = _tail_resolve_gate(_tail_gate_path(_gdp, "CGC_MDL224_ScrapeGate_v*.py"), "scrape_gate_selftest_broken")
    chk("⑧ 系統獨立:VCGC 尺檔不在 / 壞掉 → 引擎照樣載得起來,改用 VDF 自己的尺,而且沒同意照樣關",
        _fn_missing is _tail_vdf_gate_open and _fn_broken is _tail_vdf_gate_open and _fn_missing({}) is False and _fn_broken({_NK: "YES"}) is False
        and _fn_missing({_NK: "YES", _SK: "YES"}) is True and "不在" in _src_missing and "載不起來" in _src_broken, _src_missing + " · " + _src_broken)
    import re as _re
    pinned = _re.search(_re.escape(_TAIL_SELF.name.rsplit("_v", 1)[0]) + r"_v\d{4}\.py\"", text.split("def selftest")[0])
    chk("③ 本體照尾版律取到具體實作 · 不釘同族版號 · LANES L11 = 本支 lane_sentiment",
        _TAIL_BODY.name < _TAIL_SELF.name and not pinned and LANES["L11"][1] is lane_sentiment  # noqa: F821
        and all(callable(globals().get(n)) for n in _TAIL_SURFACE), _TAIL_BODY.name)
    rows, dropped = dedupe_last([{"date": "a", "index": "X", "v": 1}, {"date": "b", "index": "X", "v": 2},
                                 {"date": "a", "index": "X", "v": 3}], SENT_KEYS)
    chk("④ dedupe_last 同鍵留最後一筆、次序照首見", [r["v"] for r in rows] == [3, 2] and dropped == 1)
    saved = (globals()["OUT"], globals()["DB_GL"])
    with tempfile.TemporaryDirectory() as td:
        try:
            globals()["OUT"] = _P(td) / "fixed"
            globals()["DB_GL"] = globals()["OUT"] / "gl.duckdb"
            r1 = lane_sentiment(_FakeSentNet())
            r2 = lane_sentiment(_FakeSentNet())
            n, k, last = _sent_dups(globals()["DB_GL"])
            chk("⑤ 本支:同批 5 點 → 3 天 3 列,重跑冪等 · 同日留最後一筆(09-23 = 35.9)",
                r1["state"] == "OK" and r1["dup_dropped"] == 2 and n == k == 3 and r2["db"] == 3 and last == [35.9],
                f"列 {n} · 相異鍵 {k} · 去 {r1['dup_dropped']} · 09-23 {last}")
            globals()["OUT"] = _P(td) / "prior"
            globals()["DB_GL"] = globals()["OUT"] / "gl.duckdb"
            _PRIOR_LANE_SENTIMENT(_FakeSentNet())
            pn, pk, _ = _sent_dups(globals()["DB_GL"])
            chk("⑥ 對照:本體那一版同一份輸入照插重鍵(本測抓得到 Z297)", pn > pk, f"本體 列 {pn} · 相異鍵 {pk}")
        finally:
            globals()["OUT"], globals()["DB_GL"] = saved
    ok = all(results)
    print(f"  {'PASS' if ok else 'FAIL'} {sum(results)}/{len(results)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in _tail_sys.argv else main())
