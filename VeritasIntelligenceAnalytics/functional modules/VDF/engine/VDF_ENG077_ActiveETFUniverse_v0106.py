"""VDF_ENG077_ActiveETFUniverse tail v0106. 退役冊:操作員裁定退役的 A 碼不再算「官方冊消失」。

v0105→v0106(2026-10-13;操作員裁定「00998A 標退役」;VDF-REQ021):
  工作站 2026-10-13 一鍵實錄:TWSE 冊 A 碼 31 · 既有快照 32 → 00998A 官方冊消失 → MISSING_FROM_SOURCE(候查)→ rc 2
  → 並行道 etf 鏈 FAIL,後三步(etf_fetch · etf_history · etf_revenue)沒起。候查律本身沒錯(不刪、誠實回 2),
  但裁定退役之後要有地方登記,不然每天都紅。
  本支:讀 VDF 自己的退役冊 functional modules/VDF/VDF_ActiveETF_Retired_SSOT_v*.json(尾版;只增不減,撤銷填 revoked_at):
    ① unify 之後濾掉退役碼(不入當日宇宙列 · 不入 SSOT csv · ENG051 不再抓它的持股)—— 三支換裝函式 _unify_v0106 / _persist_v0106 / _run_v0106 經 globals 掛回本體的名字
    ② persist 之後把退役碼在註冊表標 status=RETIRED · daily_required=FALSE(本體先標 MISSING_FROM_SOURCE,本支再改;不刪列,版史留)
    ③ 退役碼不計入「官方冊消失」→ 不因它回 rc 2;run 收尾印一行 [退役]
  本體 / ScrapeGate / 橋全照 v0105(尾版律取本體 = 最後一版具體實作;今天是 v0101)。舊版全留作版史(L04)。selftest 不抓網路。
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


_TAIL_BODY = _tail_concrete_body()
_TAIL_GATE = _tail_newest(_TAIL_SELF.parents[3] / "supportive modules" / "registry", "CGC_MDL224_ScrapeGate_v*.py")
_TAIL_SURFACE = ('unify', 'run', 'persist', 'retired_tickers')
_TAIL_NET_PATH = globals().get("VIA_NET_TOOL_PATH")
_RETIRED_GLOB = "VDF_ActiveETF_Retired_SSOT_v*.json"


def _tail_load(path, name):
    spec = _tail_ilu.spec_from_file_location(name, path)
    module = _tail_ilu.module_from_spec(spec)
    _tail_sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_tail_name = __name__
globals()["__name__"] = "vdf_eng077_activeetfuniverse_body_in_tail"   # the body's own main block must not fire
globals()["__file__"] = str(_TAIL_BODY)                 # the body reads paths / its own source from here
try:
    exec(compile(_TAIL_BODY.read_text(encoding="utf-8"), str(_TAIL_BODY), "exec"), globals())
finally:
    globals()["__name__"] = _tail_name
gate_open = _tail_load(_TAIL_GATE, "scrape_gate_for_vdf_eng077_activeetfuniverse_tail").gate_open  # same swap v0102 made
_body_main = main  # noqa: F821
_body_unify = unify  # noqa: F821
_body_persist = persist  # noqa: F821
_body_run = run  # noqa: F821
_RETIRED_BOOK = None            # None = functional modules/VDF 夾裡退役冊尾版;selftest 指到 fixture
_LAST = {"retired": [], "book": ""}


def _retired_book():
    if _RETIRED_BOOK is not None:
        return _TailPath(_RETIRED_BOOK)
    hits = sorted(_TAIL_SELF.parents[1].glob(_RETIRED_GLOB))
    return hits[-1] if hits else None


def retired_tickers() -> dict:
    """退役碼 → 裁定列。沒冊 = 空(誠實,不是錯);revoked_at 有值 = 撤銷,不算退役。"""
    book = _retired_book()
    if book is None or not book.exists():
        return {}
    import json as _json
    try:
        d = _json.loads(book.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for r in d.get("retired", []) if isinstance(d, dict) else []:
        t = str(r.get("ticker", "")).strip()
        if t and not r.get("revoked_at"):
            out[t] = r
    return out


def _unify_v0106(primary, fallback, existing):
    """本體聯集之後濾掉退役碼:不入當日宇宙列、不入 SSOT csv。"""
    rows = _body_unify(primary, fallback, existing)
    ret = retired_tickers()
    return [r for r in rows if r["ticker"] not in ret]


def _persist_v0106(rows, ts, observed_tickers=None):
    """本體落地之後:註冊表裡的退役碼改標 RETIRED · daily_required=FALSE(不刪列),並從「官方冊消失」名單拿掉。"""
    p = _body_persist(rows, ts, observed_tickers)
    ret = retired_tickers()
    done = []
    if ret:
        import duckdb
        con = duckdb.connect(str(DB_ETF))  # noqa: F821
        try:
            have = {t for (t,) in con.execute(f"SELECT ticker FROM {REG_TABLE}").fetchall()}  # noqa: F821
            for t in sorted(ret):
                if t in have:
                    con.execute(f"UPDATE {REG_TABLE} SET status='RETIRED', daily_required=FALSE WHERE ticker=?", [t])  # noqa: F821
                    done.append(t)
        finally:
            con.close()
    p["missing"] = [t for t in p.get("missing", []) if t not in ret]
    p["retired"] = done
    book = _retired_book()
    _LAST.update(retired=done, book=book.name if book else "")
    return p


def _run_v0106(args):
    _LAST.update(retired=[], book="")
    rc = _body_run(args)
    ret = retired_tickers()
    if ret:
        book = _retired_book()
        print(f"  [退役] 冊 {book.name if book else '—'} · {len(ret)} 檔 {sorted(ret)} · 註冊表改標 RETIRED {len(_LAST['retired'])} 檔 · 不入宇宙列 · 不計官方冊消失(操作員裁定)", flush=True)
    return rc


# 本體的名字用 globals 換裝(不在本支靜態重定義 unify / persist / run):註冊冊掃描照舊把本體函式記在 v0101,本支只多三支 _v0106
globals()["unify"], globals()["persist"], globals()["run"] = _unify_v0106, _persist_v0106, _run_v0106


def main() -> int:  # noqa: F811
    return _body_main()


def selftest() -> int:
    import contextlib
    import io
    import json as _json
    import re as _re
    import tempfile
    global DB_ETF, DB_TW, SSOT_CSV, REP, _RETIRED_BOOK  # noqa: F824
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    text = _TAIL_SELF.read_text(encoding="utf-8")
    chk("① 加速橋 + 網路橋在尾版上", "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and bool(_TAIL_NET_PATH))
    chk("② 尾版帶著具體實作的面:" + ", ".join(_TAIL_SURFACE), all(callable(globals().get(n)) for n in _TAIL_SURFACE))
    g = gate_open
    chk("③ gate_open = CGC_MDL224 ScrapeGate(同意閘沒開就關)",
        g({}) is False and g({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "OFF"}) is False and g({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"}) is True)
    chk("④ 本體照尾版律取到具體實作", _TAIL_BODY.name < _TAIL_SELF.name and "exec(" not in _TAIL_BODY.read_text(encoding="utf-8", errors="ignore"),
        f"{_TAIL_BODY.name} · ScrapeGate {_TAIL_GATE.name}")
    pinned = _re.search(_re.escape(_TAIL_SELF.name.rsplit("_v", 1)[0]) + r"_v\d{4}\.py\"", text.split("def selftest")[0])
    chk("⑤ 本支沒有字串釘死同族版號(PINVER 0)", not pinned)
    real = _retired_book()
    real_ret = retired_tickers()
    chk("⑥ 退役冊尾版在、00998A 在冊、帶裁定與日期",
        real is not None and "00998A" in real_ret and bool(real_ret["00998A"].get("ruling")) and bool(real_ret["00998A"].get("retired_at")),
        (real.name if real else "冊不在") + f" · 退役 {sorted(real_ret)}")
    saved = (DB_ETF, DB_TW, SSOT_CSV, REP, _RETIRED_BOOK)  # noqa: F821
    with tempfile.TemporaryDirectory() as td:
        import duckdb
        DB_ETF, DB_TW = _TailPath(td) / "etf.duckdb", _TailPath(td) / "tw.duckdb"
        SSOT_CSV, REP = _TailPath(td) / "ssot" / "ActiveTWETF_Latest.csv", _TailPath(td) / "rep"
        fx = _TailPath(td) / "VDF_ActiveETF_Retired_SSOT_v9999.json"
        fx.write_text(_json.dumps({"retired": [
            {"ticker": "00777A", "name": "已下市主動", "ruling": "fixture", "retired_at": "2026-10-13", "revoked_at": None},
            {"ticker": "00555A", "name": "撤銷退役", "ruling": "fixture", "retired_at": "2026-01-01", "revoked_at": "2026-02-01"}]}, ensure_ascii=False), encoding="utf-8")
        _RETIRED_BOOK = str(fx)
        c = duckdb.connect(str(DB_TW))
        c.execute("CREATE TABLE etf_book(fund_code VARCHAR, fund_name VARCHAR, fund_type VARCHAR, is_active BOOLEAN, tracking_index VARCHAR, as_of VARCHAR)")
        c.executemany("INSERT INTO etf_book VALUES (?,?,?,?,?,?)", [
            ("00981A", "主動群益台灣強棒", "國內成分證券主動式交易所交易基金(股票)", True, "不適用", "1150905"),
            ("00777A", "已下市主動", "國內成分證券主動式交易所交易基金(股票)", True, "不適用", "1150905"),
            ("00555A", "撤銷退役", "國內成分證券主動式交易所交易基金(股票)", True, "不適用", "1150905")])
        c.close()
        c = duckdb.connect(str(DB_ETF))
        c.execute(f"""CREATE TABLE {REG_TABLE}(ticker VARCHAR PRIMARY KEY, name VARCHAR, fund_type VARCHAR, domestic BOOLEAN,
            daily_required BOOLEAN, status VARCHAR, source VARCHAR, issuer VARCHAR, first_seen VARCHAR, last_seen VARCHAR)""")  # noqa: F821
        c.executemany(f"INSERT INTO {REG_TABLE} VALUES (?,?,?,?,?,?,?,?,?,?)", [  # noqa: F821
            ("00981A", "主動群益台灣強棒", "國內成分證券主動式交易所交易基金(股票)", True, True, "ACTIVE_DOMESTIC", "twse", "群益投信", "t0", "t0"),
            ("00777A", "已下市主動", "國內成分證券主動式交易所交易基金(股票)", True, True, "ACTIVE_DOMESTIC", "twse", "某投信", "t0", "t0")])
        c.close()
        fb, _n2 = from_etf_book()  # noqa: F821
        ex = from_existing()  # noqa: F821
        rows = unify([], fb, ex)
        by = {r["ticker"]: r for r in rows}
        chk("⑦ unify 濾掉退役碼(00777A 不入);撤銷退役的 00555A 照入;其餘不動", set(by) == {"00981A", "00555A"} and by["00981A"]["status"] == "ACTIVE_DOMESTIC", str(sorted(by)))
        p = persist(rows, "t1", {"00981A", "00555A"})
        c = duckdb.connect(str(DB_ETF), read_only=True)
        st = {t: (s, d) for t, s, d in c.execute(f"SELECT ticker, status, daily_required FROM {REG_TABLE}").fetchall()}  # noqa: F821
        c.close()
        chk("⑧ persist:退役碼註冊表標 RETIRED · daily_required=FALSE · 列不刪 · 不計官方冊消失;其餘照本體(新 00555A · 00981A 仍 ACTIVE)",
            p["missing"] == [] and p["retired"] == ["00777A"] and st["00777A"] == ("RETIRED", False) and st["00981A"][0] == "ACTIVE_DOMESTIC" and st["00981A"][1] is True and p["new"] == ["00555A"],
            f"missing={p['missing']} retired={p['retired']} 00777A={st['00777A']}")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = run(["--offline"])
        out = buf.getvalue()
        csv_txt = SSOT_CSV.read_text(encoding="utf-8") if SSOT_CSV.exists() else ""
        chk("⑨ run --offline:誠實 rc 2(離線後備)· SSOT csv 沒有退役碼 · 印 [退役] 一行",
            rc == 2 and "00777A" not in csv_txt and "00981A" in csv_txt and "[退役]" in out and "00777A" in out, f"rc={rc}")
    DB_ETF, DB_TW, SSOT_CSV, REP, _RETIRED_BOOK = saved
    n = 9
    print(f"  [計] VDF_ENG077_ActiveETFUniverse v0106 薄尾 {n - len(fails)}/{n} · {'PASS' if not fails else 'FAIL ' + ', '.join(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in _tail_sys.argv else main())
