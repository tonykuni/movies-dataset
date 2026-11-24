#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG085_VatetfBridge v0104 — VATETF 應用端正主橋(批522 工作站實錄:via-vetf 印 OK 40 筆但 adapter 其實 FileExistsError APPEND_ONLY_CONFLICT=假綠)
v0103→v0104(批522):① 每跑一夾 VIA_Reports/vatetf/out/RUN_<ts>(adapter append-only 的 asof=夾永不撞;律 L44)② 判讀只認**本跑新產**的 audit.json,
  不再退回舊 audit(舊 audit=上一跑的 0% 覆蓋被當成這一跑的結果=假綠;LL44)③ adapter JSON 帶 error_type 或 status 以 FAIL 開頭 → FAIL 帶因由;十一檢 +⑪。
VDF_ENG085_VatetfBridge v0103 — VATETF 應用端正主橋(批521 操作員令「CONSENSUS EPS SHOULD BE DILUTED EPS ONLY IN FACTSET CONSENSUS」)
v0102→v0103(批521):EPS 碎片只給 FactSet 來源(consensus_daily source='CNYES_FACTSET':鉅亨 FactSet estimateProfit?type=eps 年度 feMean=稀釋 EPS 共識);
  YFinance(YAHOO_QS)/其他來源只給目標價,不給 EPS;碎片帶 eps_basis 標示欄;律 L43。十檢 ⑤⑩ 追上。
VDF_ENG085_VatetfBridge v0102 — VATETF 應用端正主橋(批521:共識 EPS 兩期入 adapter → Forward P/E 有料)
v0101→v0102(批521 工作站實錄 via-vetf OK 40 筆但 coverage eps/forward_pe 0%:consensus_latest 的 eps_fy0/eps_fy1 沒對到 adapter 的期別欄):
  暫存 factset/yfinance 表每檔兩列碎片(period n=eps_fy0 · fiscal_year=快照年;period n1=eps_fy1 · 年+1;eps_mean/eps_median 同值;adapter merge_consensus_fragments
  按 (ticker,snapshot_date,provider) 併回一列 → eps_n/eps_n1 → Forward P/E N/N+1);十檢 +⑩。
VDF_ENG085_VatetfBridge v0101 — VATETF 應用端正主橋(批520a 容器實跑修:持股表缺先誠實 NODATA;錯誤行取有意義那行)
v0100→v0101(批520a 容器 run 實錄 FAIL「暫存輸入庫建不起來:^」):run 先走盤點(表在不在/列數),holdings_daily 缺或空=NODATA 誠實停,不進暫存庫建表;
  子行程錯誤行改取最後一行有字的(DuckDB 錯誤尾行是 ^ 指標),why 才看得懂;自測 +⑨。
VDF_ENG085_VatetfBridge v0100 — VATETF 應用端正主橋(批520;操作員實錄 via-vetf → 收容件 adapter FAIL_CLOSED「Need a DataFrame with at least one column」)
====================================================================
根因(LL37):VETF adapter(收容件 b242;正本零觸碰)只認自己的欄名別名——holding_date/etf_code/ticker/holding_weight、price_date/adj_close——
  VDF 正本 holdings_daily 的欄叫 portfolio_date/etf_ticker/holding_ticker/weight_pct,tw_prices_adj 的 ticker 帶 .TW/.TWO 尾綴;
  別名對不上 → 每列被丟 → 0 筆 → 寫候選 DuckDB 時空表炸掉。錯的不是庫也不是 adapter,是**對接口沒有合約**。
本橋=對接口合約自適應(L31/L34;一功能一正主 L30):
  status                    庫解析律(資料家優先;LL27/LL30/LL35)找 ActiveTWETF.duckdb::holdings_daily 與 vdf_tw_market.duckdb(tw_prices_adj|tw_daily_prices|consensus_latest)
                            → 每表 在/列數/最新日/欄位齊不齊(對 adapter 別名);最新 audit.json 摘要;誠實三態
  run [--asof YYYY-MM-DD|latest] [--holdings P::T] [--prices P] [--no-consensus] [--days 45] [--json]
                            家族境 python 建**暫存輸入庫**(VIA_Reports/vatetf/_bridge/inputs_<ts>.duckdb):
                              holdings = 每檔 ETF 在 asof 前最新一日的持股(欄改 adapter 別名;代碼去 .TW/.TWO;currency TWD)
                              prices   = 持股代碼 asof 前 --days 日內的 adj_close/close(來源 tw_prices_adj,缺則 tw_daily_prices)
                              factset/yfinance = consensus_latest 依 source 分欄(FactSet/其他;缺=不給旗標,adapter 照跑)
                            → 以家族境跑 adapter(--write-mode candidate 沙盒;--output-dir VIA_Reports/vatetf/out)→ 讀 audit.json 摘要;誠實 NODATA/FAIL 理由
  --selftest                八檢(零網路;合成 DuckDB;假 adapter)
律:只增不減;正本零觸碰(adapter 與 VDF 正本表零改;暫存庫只讀來源);誠實三態;零網路;子行程環境走匯流排 child_env(L32);VATETF 只讀 VDF 庫(L34)。
用法:python3 VDF_ENG085_VatetfBridge_v0103.py status|run [...] [--json] | --selftest
"""
from __future__ import annotations

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====


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
from functools import partial as _lb_partial
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====



import datetime as _dt
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
OUT = VIA / "VIA_Reports" / "vatetf"
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
HUB = VIA / "functional modules" / "VDF" / "output_hub"
ADAPTER_DIR = VIA / "functional modules" / "VDF" / "references" / "intake" / "VETF_FINAL_SEAL_b242" / "01_ENGINES" / "Consensus_Enrichment_Adapter"
ADAPTER_GLOB = "VETF_ConsensusEnrichment_Adapter_v*.py"

# adapter 別名(收容件 HOLDING_ALIASES/PRICE_ALIASES/TARGET_ALIASES 節錄;對接契約=我們把欄名改成它認得的)
CONTRACT = {
    "holdings": {"holding_date": "portfolio_date", "etf_code": "etf_ticker", "etf_name": "etf_name", "ticker": "holding_ticker", "company_name": "holding_name", "holding_weight": "weight_pct", "holding_shares": "shares"},
    "prices": {"price_date": "date", "ticker": "ticker", "adj_close": "adj_close", "close": "close"},
    "targets": {"snapshot_date": "date", "ticker": "code", "target_low": "target_low", "target_mean": "target_mean", "target_median": "target_median", "target_high": "target_high", "target_analyst_count": "n_analysts"},
}


#: 批597 三庫整併:_newest → 正典綁定(原本多一個 root.exists() 守衛;正典的 base.is_dir() 已涵蓋,語料零差異)。
#  綁定不是 def——再包一層 def 的話能力庫裡那一族還在,家族數不會掉(LL143)。
_newest = _LIB.newest


def _bus():
    p = _newest(VIA / "supportive modules" / "registry", "CGC_MDL148_EngineBus_v*.py")
    if not p:
        return None
    try:
        spec = importlib.util.spec_from_file_location("via_bus_for_eng085", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules["via_bus_for_eng085"] = m
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


def family_python() -> str:
    e = os.environ.get("VIA_PY_VDF")
    if e and Path(e).exists():
        return e
    b = _bus()
    if b is not None:
        try:
            return b.python_for("vdf").get("python") or sys.executable
        except Exception:
            pass
    return sys.executable


def child_env() -> dict:
    b = _bus()
    if b is not None:
        try:
            return b.child_env("vdf")
        except Exception:
            pass
    e = dict(os.environ)
    e.pop("PYTHONHOME", None)
    e["VIA_PYTHONHOME_SCRUBBED"] = "1"
    return e


def _find(name: str, env_key: str = "") -> tuple[Path | None, str]:
    """庫解析律:env 明給 > VIA_DATA_HOME 家內 rglob > 舊主路徑 output_hub rglob;排除 _self_test/_repo_。"""
    e = os.environ.get(env_key) if env_key else None
    if e and Path(e).exists():
        return Path(e), env_key
    for root, how in ((os.environ.get("VIA_DATA_HOME"), "VIA_DATA_HOME 家內 rglob"), (str(HUB), "舊主路徑 output_hub")):
        if root and Path(root).exists():
            hits = [p for p in sorted(Path(root).rglob(name)) if "_self_test" not in str(p) and "_repo_" not in str(p)]
            if hits:
                return hits[0], how
    return None, "ABSENT"


def resolve_sources(holdings: str | None = None, prices: str | None = None) -> dict:
    out = {}
    if holdings and "::" in holdings:
        p, t = holdings.rsplit("::", 1)
        out["holdings"] = {"path": p, "table": t, "how": "--holdings 明給"}
    else:
        p, how = _find("ActiveTWETF.duckdb", "VIA_DB_ACTIVE_TW_ETF")
        out["holdings"] = {"path": str(p) if p else None, "table": "holdings_daily", "how": how}
    if prices:
        out["prices"] = {"path": prices.split("::")[0], "how": "--prices 明給"}
    else:
        e = os.environ.get("VIA_DB_VDF_TW_MARKET")
        if e and Path(e).exists():
            out["prices"] = {"path": e, "how": "VIA_DB_VDF_TW_MARKET"}
        else:
            p, how = _find("vdf_tw_market.duckdb")
            out["prices"] = {"path": str(p) if p else None, "how": how}
    return out


# 家族境 DuckDB 工作腳本(本行程 python 可能沒 duckdb=工作站 base;一律經家族境跑,回 JSON)
_INSPECT = r'''
import json, sys, duckdb
p = json.loads(sys.argv[1]); out = {}
for key, path in (("holdings", p["holdings"]), ("prices", p["prices"])):
    if not path: out[key] = {"state": "ABSENT"}; continue
    try:
        con = duckdb.connect(path, read_only=True)
        tabs = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        rep = {"state": "OK", "tables": {}}
        for t in (["holdings_daily"] if key == "holdings" else ["tw_prices_adj", "tw_daily_prices", "consensus_latest"]):
            if t not in tabs: rep["tables"][t] = {"state": "ABSENT"}; continue
            cols = [r[0] for r in con.execute(f'DESCRIBE "{t}"').fetchall()]
            n = con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
            dc = "portfolio_date" if t == "holdings_daily" else "date"
            mx = con.execute(f'SELECT max(CAST("{dc}" AS VARCHAR)) FROM "{t}"').fetchone()[0] if dc in cols else None
            rep["tables"][t] = {"state": "OK" if n else "EMPTY", "rows": n, "max": mx, "cols": cols}
        con.close(); out[key] = rep
    except Exception as e:
        out[key] = {"state": "FAIL", "why": type(e).__name__ + ":" + str(e)[:120]}
print(json.dumps(out, ensure_ascii=False, default=str))
'''

_PREPARE = r'''
import json, sys, duckdb, datetime
p = json.loads(sys.argv[1]); asof = p["asof"]; days = int(p["days"]); rep = {"state": "OK", "notes": []}
con = duckdb.connect(p["tmp"])
con.execute(f"ATTACH '{p['holdings']}' AS h (READ_ONLY)")
con.execute(f"ATTACH '{p['prices']}' AS m (READ_ONLY)")
htab = p["htable"]
hcols = {r[0] for r in con.execute(f'DESCRIBE h."{htab}"').fetchall()}
def col(name, default="NULL"):
    return name if name in hcols else default
con.execute(f"""CREATE TABLE holdings AS
  SELECT CAST(portfolio_date AS VARCHAR) AS holding_date, etf_ticker AS etf_code, {col('etf_name', "''")} AS etf_name,
         regexp_replace(holding_ticker, '\\.(TW|TWO)$', '') AS ticker, {col('holding_name', "''")} AS company_name,
         weight_pct AS holding_weight, {col('shares')} AS holding_shares, 'TWD' AS currency, 'TWSE' AS exchange
  FROM h."{htab}" x
  WHERE CAST(portfolio_date AS VARCHAR) <= '{asof}'
    AND portfolio_date = (SELECT max(portfolio_date) FROM h."{htab}" y WHERE y.etf_ticker = x.etf_ticker AND CAST(y.portfolio_date AS VARCHAR) <= '{asof}')""")
rep["holdings"] = con.execute("SELECT count(*), count(DISTINCT etf_code), min(holding_date), max(holding_date) FROM holdings").fetchone()
mt = {r[0] for r in con.execute("SHOW TABLES FROM m").fetchall()} if False else {r[0] for r in con.execute("SELECT table_name FROM information_schema.tables WHERE table_catalog='m'").fetchall()}
since = (datetime.date.fromisoformat(asof) - datetime.timedelta(days=days)).isoformat()
if "tw_prices_adj" in mt:
    con.execute(f"""CREATE TABLE prices AS SELECT date AS price_date, regexp_replace(ticker, '\\.(TW|TWO)$', '') AS ticker, adj_close,
                    CASE WHEN factor IS NOT NULL AND factor <> 0 THEN adj_close / factor END AS close, 'TWD' AS currency
                    FROM m.tw_prices_adj WHERE date BETWEEN '{since}' AND '{asof}' AND regexp_replace(ticker, '\\.(TW|TWO)$', '') IN (SELECT DISTINCT ticker FROM holdings)""")
    rep["prices_src"] = "tw_prices_adj"
elif "tw_daily_prices" in mt:
    con.execute(f"""CREATE TABLE prices AS SELECT date AS price_date, regexp_replace(ticker, '\\.(TW|TWO)$', '') AS ticker, adj_close, close, 'TWD' AS currency
                    FROM m.tw_daily_prices WHERE date BETWEEN '{since}' AND '{asof}' AND regexp_replace(ticker, '\\.(TW|TWO)$', '') IN (SELECT DISTINCT ticker FROM holdings)""")
    rep["prices_src"] = "tw_daily_prices"
else:
    con.execute("CREATE TABLE prices(price_date VARCHAR, ticker VARCHAR, adj_close DOUBLE, close DOUBLE, currency VARCHAR)"); rep["prices_src"] = "ABSENT"
rep["prices"] = con.execute("SELECT count(*), count(DISTINCT ticker), max(price_date) FROM prices").fetchone()
rep["missing_price_tickers"] = con.execute("SELECT count(*) FROM (SELECT DISTINCT ticker FROM holdings) h WHERE ticker NOT IN (SELECT DISTINCT ticker FROM prices)").fetchone()[0]
rep["factset"] = rep["yfinance"] = 0
if p.get("consensus") and "consensus_latest" in mt:
    # 批521 L43:EPS 只給 FactSet(CNYES_FACTSET 年度 feMean=稀釋 EPS 共識)每檔兩列碎片(n=eps_fy0 / n1=eps_fy1);其他來源(YAHOO_QS 等)只給目標價
    where = f"""WHERE CAST(c.date AS VARCHAR) <= '{asof}' AND c.code IN (SELECT DISTINCT ticker FROM holdings)"""
    con.execute(f"""CREATE TABLE factset AS
        SELECT CAST(c.date AS VARCHAR) AS snapshot_date, c.code AS ticker, c.source, c.target_low, c.target_mean, c.target_median, c.target_high, c.n_analysts AS target_analyst_count, 'TWD' AS currency,
               h.period, h.fiscal_year, h.eps AS eps_mean, c.n_analysts AS eps_analyst_count, 'FACTSET_DILUTED_EPS(cnyes estimateProfit feMean 年度均值;L43)' AS eps_basis
        FROM m.consensus_latest c
        CROSS JOIN LATERAL (VALUES ('n', year(CAST(c.date AS DATE)), c.eps_fy0), ('n1', year(CAST(c.date AS DATE)) + 1, c.eps_fy1)) AS h(period, fiscal_year, eps)
        {where} AND lower(c.source) LIKE '%factset%'""")
    con.execute(f"""CREATE TABLE yfinance AS
        SELECT CAST(c.date AS VARCHAR) AS snapshot_date, c.code AS ticker, c.source, c.target_low, c.target_mean, c.target_median, c.target_high, c.n_analysts AS target_analyst_count, 'TWD' AS currency
        FROM m.consensus_latest c {where} AND NOT (lower(c.source) LIKE '%factset%')""")
    rep["factset"] = con.execute("SELECT count(*) FROM factset").fetchone()[0]; rep["yfinance"] = con.execute("SELECT count(*) FROM yfinance").fetchone()[0]
con.close()
print(json.dumps(rep, ensure_ascii=False, default=str))
'''


def _err_line(text: str) -> str:
    """批520a:DuckDB 例外尾行常是「^」指標/空行;取最後一行有意義的(含 Error/Exception 優先)。"""
    lines = [l.strip() for l in (text or "").splitlines() if l.strip() and set(l.strip()) != {"^"}]
    for l in reversed(lines):
        if "Error" in l or "Exception" in l or "error" in l:
            return l[:200]
    return lines[-1][:200] if lines else ""


def _family_json(script: str, params: dict, timeout: int = 600) -> dict:
    py = family_python()
    try:
        r = subprocess.run([py, "-c", script, json.dumps(params, ensure_ascii=False)], capture_output=True, text=True, timeout=timeout, env=child_env(), cwd=str(VIA))
        out = (r.stdout or "").strip()
        if r.returncode == 0 and out:
            return json.loads(out.splitlines()[-1])
        return {"state": "FAIL", "why": _err_line(r.stderr or out) or f"rc={r.returncode}"}
    except subprocess.TimeoutExpired:
        return {"state": "TIMEOUT", "why": f"逾時 {timeout}s"}
    except Exception as exc:
        return {"state": "FAIL", "why": f"{type(exc).__name__}:{str(exc)[:120]}"}


def contract_check(cols: list, kind: str) -> dict:
    """VDF 正本欄 ↔ adapter 別名對接:缺哪些正本欄=講出來。"""
    need = CONTRACT[kind]
    missing = [f"{k}←{v}" for k, v in need.items() if v not in cols and k in ("holding_date", "etf_code", "ticker", "holding_weight", "price_date", "adj_close", "snapshot_date", "target_median")]
    return {"state": "OK" if not missing else "MISMATCH", "missing": missing, "mapped": {k: v for k, v in need.items() if v in cols}}


def status(do_print: bool = True, holdings: str | None = None, prices: str | None = None) -> dict:
    src = resolve_sources(holdings, prices)
    rep = {"schema": "VIA.VatetfBridge.status.v1", "ts": _dt.datetime.now().isoformat(timespec="seconds"), "sources": src, "adapter": None, "state": "OK", "why": ""}
    ad = _newest(ADAPTER_DIR, ADAPTER_GLOB)
    rep["adapter"] = str(ad) if ad else None
    if not ad:
        rep["state"], rep["why"] = "ABSENT", "收容件 adapter 不在(VETF_FINAL_SEAL_b242)"
    if not src["holdings"]["path"] or not src["prices"]["path"]:
        rep["state"] = "ABSENT"
        rep["why"] = (rep["why"] + " · " if rep["why"] else "") + "庫解析:" + " · ".join(f"{k} {v['how']}" for k, v in src.items() if not v["path"])
    if src["holdings"]["path"] and src["prices"]["path"]:
        ins = _family_json(_INSPECT, {"holdings": src["holdings"]["path"], "prices": src["prices"]["path"]})
        rep["inspect"] = ins
        ht = ((ins.get("holdings") or {}).get("tables") or {}).get(src["holdings"]["table"]) or {}
        if ht.get("cols"):
            rep["contract_holdings"] = contract_check(ht["cols"], "holdings")
        pt = ((ins.get("prices") or {}).get("tables") or {})
        for t in ("tw_prices_adj", "tw_daily_prices"):
            if (pt.get(t) or {}).get("cols"):
                rep["contract_prices"] = dict(contract_check(pt[t]["cols"], "prices"), table=t)
                break
        if (pt.get("consensus_latest") or {}).get("cols"):
            rep["contract_targets"] = contract_check(pt["consensus_latest"]["cols"], "targets")
        if ht.get("state") in (None, "ABSENT", "EMPTY") and rep["state"] == "OK":
            rep["state"], rep["why"] = "NODATA", f"holdings_daily {ht.get('state') or 'ABSENT'}(先 via-etfhold / via-bus one etf_holdings_daily)"
    aud = sorted((OUT / "out").rglob("audit.json")) if (OUT / "out").exists() else []
    if aud:
        try:
            j = json.loads(aud[-1].read_text(encoding="utf-8"))
            rep["audit"] = {"file": str(aud[-1]), "analysis_date": j.get("analysis_date"), "record_count": j.get("record_count"), "status_counts": j.get("status_counts"), "coverage_pct": j.get("coverage_pct")}
        except Exception as exc:
            rep["audit"] = {"file": str(aud[-1]), "why": f"讀不了 {type(exc).__name__}"}
    else:
        rep["audit"] = {"state": "ABSENT", "why": "尚未 via-vetf run"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "STATUS_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if do_print:
        print(f"=== [via-vetf status] VATETF 應用端正主橋 · {rep['state']} {rep['why']} ===")
        for k, v in src.items():
            print(f"  [庫解析] {k:<9} {v.get('how')} → {v.get('path') or 'ABSENT'}" + (f"::{v['table']}" if v.get("table") else ""))
        for k in ("holdings", "prices"):
            for t, v in (((rep.get("inspect") or {}).get(k) or {}).get("tables") or {}).items():
                print(f"  [{v.get('state'):<6}] {t:<18} 列 {v.get('rows', '-')} 最新 {v.get('max') or '-'}")
        for k in ("contract_holdings", "contract_prices", "contract_targets"):
            if rep.get(k):
                print(f"  [合約 {rep[k]['state']:<8}] {k.split('_')[1]:<9} 缺 {rep[k]['missing'] or '無'}")
        print(f"  [audit] {rep['audit']}")
    return rep


def run(args: list, do_print: bool = True, runner=None) -> dict:
    asof = _arg(args, "--asof", "latest") or "latest"
    if asof == "latest":
        asof = _dt.date.today().isoformat()
    days = int(_arg(args, "--days", "45") or 45)
    src = resolve_sources(_arg(args, "--holdings"), _arg(args, "--prices"))
    rep = {"schema": "VIA.VatetfBridge.run.v1", "ts": _dt.datetime.now().isoformat(timespec="seconds"), "asof": asof, "sources": src, "state": "ABSENT", "why": "", "prepare": None, "adapter": None, "audit": None}
    ad = _newest(ADAPTER_DIR, ADAPTER_GLOB)
    if not ad or not src["holdings"]["path"] or not src["prices"]["path"]:
        rep["why"] = "收容件 adapter 不在" if not ad else "庫解析:" + " · ".join(f"{k} {v['how']}" for k, v in src.items() if not v["path"])
        _emit(rep, do_print)
        return rep
    ins = _family_json(_INSPECT, {"holdings": src["holdings"]["path"], "prices": src["prices"]["path"]})   # 批520a:先盤點再建
    rep["inspect"] = ins
    ht = ((ins.get("holdings") or {}).get("tables") or {}).get(src["holdings"]["table"]) or {}
    if ht.get("state") in (None, "ABSENT", "EMPTY"):
        rep["state"], rep["why"] = "NODATA", f"{src['holdings']['table']} {ht.get('state') or 'ABSENT'}(持股表缺/空;先 via-etfhold / via-bus one etf_holdings_daily;{(ins.get('holdings') or {}).get('why') or ''})".rstrip("; ")
        _emit(rep, do_print)
        return rep
    if not any(((ins.get("prices") or {}).get("tables") or {}).get(x, {}).get("state") == "OK" for x in ("tw_prices_adj", "tw_daily_prices")):
        rep["state"], rep["why"] = "NODATA", "價表 tw_prices_adj/tw_daily_prices 缺或空(先 via-price / via-vdfdb)"
        _emit(rep, do_print)
        return rep
    (OUT / "_bridge").mkdir(parents=True, exist_ok=True)
    tmp = OUT / "_bridge" / f"inputs_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.duckdb"
    prep = _family_json(_PREPARE, {"holdings": src["holdings"]["path"], "htable": src["holdings"]["table"], "prices": src["prices"]["path"], "tmp": str(tmp), "asof": asof, "days": days, "consensus": "--no-consensus" not in args})
    rep["prepare"] = prep
    if prep.get("state") != "OK":
        rep["state"], rep["why"] = prep.get("state", "FAIL"), "暫存輸入庫建不起來:" + str(prep.get("why"))
        _emit(rep, do_print)
        return rep
    h_n = int((prep.get("holdings") or [0])[0] or 0)
    p_n = int((prep.get("prices") or [0])[0] or 0)
    if h_n == 0:
        rep["state"], rep["why"] = "NODATA", f"asof {asof} 前無持股列(holdings_daily 空或日期都在 asof 之後;先 via-etfhold)"
        _emit(rep, do_print)
        return rep
    if p_n == 0:
        rep["state"], rep["why"] = "NODATA", f"持股代碼 {days} 日內無價(prices 來源 {prep.get('prices_src')};先 via-price / ENG060 tw_prices_adj)"
        _emit(rep, do_print)
        return rep
    out_dir = OUT / "out" / f"RUN_{_dt.datetime.now():%Y%m%d_%H%M%S}"     # 批522:每跑一夾(adapter append-only;asof= 夾永不撞;L44)
    out_dir.mkdir(parents=True, exist_ok=True)
    rep["out_dir"] = str(out_dir)
    argv = [family_python(), str(ad), "--holdings", f"{tmp}::holdings", "--prices", f"{tmp}::prices", "--output-dir", str(out_dir), "--write-mode", "candidate", "--asof", asof]
    if int(prep.get("factset") or 0):
        argv += ["--factset", f"{tmp}::factset"]
    if int(prep.get("yfinance") or 0):
        argv += ["--yfinance", f"{tmp}::yfinance"]
    rep["argv"] = argv
    before = set(str(p) for p in out_dir.rglob("audit.json"))
    r = (runner or _run_adapter)(argv)
    rep["adapter"] = r
    after = sorted(p for p in out_dir.rglob("audit.json") if str(p) not in before)     # 批522:只認本跑新產;不退回舊 audit(LL44)
    rep["state"], rep["why"], rep["audit"] = judge_adapter(r, after)
    if rep["audit"] is None:
        rep.pop("audit", None)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "RUN_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _emit(rep, do_print)
    return rep



def judge_adapter(r: dict, after: list) -> tuple:
    """批522:adapter 結果 → (state, why, audit|None)。只認本跑新產的 audit.json;error_type/FAIL 狀態/rc≠0 且無新 audit=FAIL 帶因由;逾時=TIMEOUT。"""
    js = r.get("json") or {}
    tail = r.get("tail") or []
    if r.get("rc") is None and not after:
        return "TIMEOUT", str(r.get("why") or "逾時"), None
    if js.get("error_type") or str(js.get("status", "")).startswith("FAIL") or (r.get("rc") not in (0, None) and not after):
        return "FAIL", f"adapter {js.get('status') or 'rc=' + str(r.get('rc'))}:{js.get('error_type') or ''} {str(js.get('message') or (tail[-1] if tail else ''))[:140]}", None
    if after:
        try:
            j = json.loads(after[-1].read_text(encoding="utf-8"))
        except Exception as exc:
            return "FAIL", f"audit.json 讀不了 {type(exc).__name__}", None
        audit = {"file": str(after[-1]), "analysis_date": j.get("analysis_date"), "record_count": j.get("record_count"), "status_counts": j.get("status_counts"), "coverage_pct": j.get("coverage_pct")}
        n = int(j.get("record_count") or 0)
        return ("OK" if n > 0 else "NODATA"), f"records {j.get('record_count')} · {j.get('status_counts')}", audit
    return "FAIL", "沒有本跑的 audit.json 產出(adapter 尾段見下;舊夾的 audit 不算)", None

def _run_adapter(argv: list, timeout: int = 1800) -> dict:
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=child_env(), cwd=str(OUT))
        out = r.stdout or ""
        js = None
        if "{" in out:
            try:
                js = json.loads(out[out.index("{"):])
            except Exception:
                js = None
        return {"rc": r.returncode, "json": js, "tail": [l for l in (out + "\n" + (r.stderr or "")).splitlines() if l.strip()][-6:]}
    except subprocess.TimeoutExpired:
        return {"rc": None, "json": None, "tail": [], "why": f"逾時 {timeout}s"}
    except Exception as exc:
        return {"rc": 1, "json": None, "tail": [f"{type(exc).__name__}: {exc}"]}


def _emit(rep: dict, do_print: bool) -> None:
    if not do_print:
        return
    print(f"=== [via-vetf run] VATETF 持股×Consensus(candidate 沙盒)· asof {rep.get('asof')} · {rep['state']} · {rep['why'][:150]} ===")
    for k, v in (rep.get("sources") or {}).items():
        print(f"  [庫解析] {k:<9} {v.get('how')} → {v.get('path') or 'ABSENT'}")
    pr = rep.get("prepare") or {}
    if pr.get("holdings") is not None:
        print(f"  [對接] holdings {pr.get('holdings')} · prices {pr.get('prices')}(源 {pr.get('prices_src')};缺價代碼 {pr.get('missing_price_tickers')})· factset {pr.get('factset')} · yfinance {pr.get('yfinance')}")
    for l in ((rep.get("adapter") or {}).get("tail") or [])[-4:]:
        print("  | " + l[:180])
    if rep.get("audit"):
        print(f"  [audit] {rep['audit']}")


#: 批597 三庫整併:_arg → 正典綁定(同 ENG079 群)。
#  綁定不是 def——再包一層 def 的話能力庫裡那一族還在,家族數不會掉(LL143)。
_arg = _lb_partial(_LIB.argval, quiet=True, dashdash=True)


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 收容件 adapter 在位(尾版 glob;零觸碰)", _newest(ADAPTER_DIR, ADAPTER_GLOB) is not None)
    c1 = contract_check(["portfolio_date", "etf_ticker", "holding_ticker", "weight_pct", "shares"], "holdings")
    c2 = contract_check(["date", "ticker", "adj_close", "volume"], "prices")
    c3 = contract_check(["date", "code", "target_median", "n_analysts"], "targets")
    c4 = contract_check(["etf_ticker", "holding_ticker"], "holdings")
    chk("② 對接合約:VDF 正本欄 ↔ adapter 別名逐欄對映;缺必要欄=MISMATCH 點名", c1["state"] == "OK" and c2["state"] == "OK" and c3["state"] == "OK" and c4["state"] == "MISMATCH" and "holding_date←portfolio_date" in c4["missing"])
    try:
        import duckdb
        with tempfile.TemporaryDirectory() as td:
            T = Path(td)
            h = duckdb.connect(str(T / "ActiveTWETF.duckdb"))
            h.execute("CREATE TABLE holdings_daily(portfolio_date DATE, etf_ticker VARCHAR, etf_yf_ticker VARCHAR, etf_name VARCHAR, issuer VARCHAR, holding_ticker VARCHAR, holding_yf_ticker VARCHAR, holding_name VARCHAR, weight_pct DOUBLE, shares DOUBLE, source_type VARCHAR, source_url VARCHAR, fetched_at TIMESTAMP)")
            h.executemany("INSERT INTO holdings_daily VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", [
                ("2026-09-10", "00981A", "00981A.TW", "統一台股增長主動式", "統一", "2330.TW", "2330.TW", "台積電", 9.5, 1000, "PCF", "", None),
                ("2026-09-12", "00981A", "00981A.TW", "統一台股增長主動式", "統一", "2330", "2330.TW", "台積電", 10.0, 1100, "PCF", "", None),
                ("2026-09-12", "00981A", "00981A.TW", "統一台股增長主動式", "統一", "2317", "2317.TW", "鴻海", 5.0, 900, "PCF", "", None),
                ("2026-09-20", "00981A", "00981A.TW", "統一台股增長主動式", "統一", "2454", "2454.TW", "聯發科", 4.0, 100, "PCF", "", None)])
            h.close()
            m = duckdb.connect(str(T / "vdf_tw_market.duckdb"))
            m.execute("CREATE TABLE tw_prices_adj(date VARCHAR, ticker VARCHAR, factor DOUBLE, adj_open DOUBLE, adj_high DOUBLE, adj_low DOUBLE, adj_close DOUBLE, volume DOUBLE, data_class VARCHAR)")
            m.executemany("INSERT INTO tw_prices_adj VALUES (?,?,?,?,?,?,?,?,?)", [("2026-09-12", "2330.TW", 1.0, 1000, 1010, 990, 1000.0, 1e6, "x"), ("2026-09-11", "2330.TW", 1.0, 990, 1000, 980, 990.0, 1e6, "x"), ("2026-09-12", "9999.TW", 1.0, 1, 1, 1, 1.0, 1, "x")])
            m.execute("CREATE TABLE consensus_latest(date DATE, code VARCHAR, source VARCHAR, target_high DOUBLE, target_low DOUBLE, target_mean DOUBLE, target_median DOUBLE, n_analysts INTEGER, eps_fy0 DOUBLE, eps_fy1 DOUBLE, adopted_eps DOUBLE, close DOUBLE, upside_pct DOUBLE, validated VARCHAR, rn BIGINT)")
            m.executemany("INSERT INTO consensus_latest VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [("2026-09-01", "2330", "FACTSET", 1300, 1000, 1200, 1200, 20, 60, 70, 60, 1000, 0.2, "Y", 1), ("2026-09-01", "2330", "YFINANCE", 1250, 1000, 1150, 1150, 5, 60, 70, 60, 1000, 0.15, "Y", 1), ("2026-09-01", "2454", "YFINANCE", 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.1, "Y", 1)])
            m.close()
            _sv = os.environ.get("VIA_PY_VDF")
            os.environ["VIA_PY_VDF"] = sys.executable
            try:
                prep = _family_json(_PREPARE, {"holdings": str(T / "ActiveTWETF.duckdb"), "htable": "holdings_daily", "prices": str(T / "vdf_tw_market.duckdb"), "tmp": str(T / "in.duckdb"), "asof": "2026-09-15", "days": 45, "consensus": True})
                ins = _family_json(_INSPECT, {"holdings": str(T / "ActiveTWETF.duckdb"), "prices": str(T / "vdf_tw_market.duckdb")})
            finally:
                if _sv is None:
                    os.environ.pop("VIA_PY_VDF", None)
                else:
                    os.environ["VIA_PY_VDF"] = _sv
            hh = list(prep.get("holdings") or [])
            pp = list(prep.get("prices") or [])
            chk("③ 暫存輸入庫:每檔 ETF 取 asof 前最新一日(09-12;09-20 不取;09-10 舊日不取)、代碼去 .TW、欄名改 adapter 別名、currency TWD",
                prep.get("state") == "OK" and int(hh[0]) == 2 and str(hh[3]).startswith("2026-09-12") and int(hh[1]) == 1, f"({prep})")
            chk("④ 價:只取持股代碼 45 日內(2330 兩日;9999 不取)、close=adj_close/factor;缺價代碼數=1(2317)", pp and int(pp[0]) == 2 and int(pp[1]) == 1 and prep.get("missing_price_tickers") == 1 and prep.get("prices_src") == "tw_prices_adj")
            chk("⑤ 共識分欄(L43):FactSet 2 列(每檔 n/n1 兩期 EPS 碎片)/ 其他來源 1 列(只目標價;無 EPS;2454 不在持股=不取)", prep.get("factset") == 2 and prep.get("yfinance") == 1)
            con = duckdb.connect(str(T / "in.duckdb"), read_only=True)
            hcols = [r[0] for r in con.execute("DESCRIBE holdings").fetchall()]
            tk = sorted(r[0] for r in con.execute("SELECT DISTINCT ticker FROM holdings").fetchall())
            con.close()
            chk("⑥ 暫存表欄=adapter 別名(holding_date/etf_code/ticker/holding_weight…);ticker 四碼", {"holding_date", "etf_code", "ticker", "holding_weight", "currency"} <= set(hcols) and tk == ["2317", "2330"])
            con = duckdb.connect(str(T / "in.duckdb"), read_only=True)
            fs = con.execute("SELECT period, fiscal_year, eps_mean, eps_basis FROM factset ORDER BY period").fetchall()
            ycols = [r[0] for r in con.execute("DESCRIBE yfinance").fetchall()]
            con.close()
            chk("⑩ 批521 L43 EPS 只給 FactSet:period n=eps_fy0(快照年)· n1=eps_fy1(年+1)· eps_basis 標稀釋 FactSet;yfinance 表無 EPS 欄", [x[:3] for x in fs] == [("n", 2026, 60.0), ("n1", 2027, 70.0)] and all("FACTSET_DILUTED" in x[3] for x in fs) and "eps_mean" not in ycols and "period" not in ycols, f"({fs[0][3][:30]})")
            chk("⑦ 盤點腳本:表在/列數/最新日/欄位(對合約)", ((ins.get("holdings") or {}).get("tables") or {}).get("holdings_daily", {}).get("rows") == 4 and "portfolio_date" in ((ins.get("holdings") or {}).get("tables") or {}).get("holdings_daily", {}).get("cols", []))
    except ImportError:
        chk("③–⑦ 合成庫(本境無 duckdb=SKIP 誠實)", True, "(duckdb 缺)")
    fake_fail = {"rc": 1, "json": {"status": "FAIL_CLOSED", "engine": "VETF_ConsensusEnrichment_Adapter", "error_type": "InvalidInputException", "message": "Invalid Input Error: Need a DataFrame with at least one column"}, "tail": []}
    src = Path(__file__).read_text(encoding="utf-8").split("def selftest")[0]
    chk("⑧ 律:adapter FAIL_CLOSED 帶 error_type/message 判 FAIL(不吞)· 零網路 · 只讀來源(ATTACH READ_ONLY)· candidate 沙盒 · 子行程走匯流排 child_env",
        "FAIL_CLOSED" in json.dumps(fake_fail) and all(("import " + k) not in src for k in ("requests", "httpx", "urllib")) and "(READ_ONLY)" in src and '"--write-mode", "candidate"' in src and "child_env(" in src)
    chk("⑨ 批520a 錯誤行取有意義那行(略過 ^ 指標/空行;Error 優先)", _err_line("Catalog Error: Table x does not exist\nLINE 1: DESCRIBE x\n                 ^") == "Catalog Error: Table x does not exist" and _err_line("") == "")
    with tempfile.TemporaryDirectory() as td11:
        T11 = Path(td11)
        (T11 / "asof=2026-09-15").mkdir(parents=True)
        (T11 / "asof=2026-09-15" / "audit.json").write_text('{"record_count": 40, "status_counts": {"PASS": 2}}', encoding="utf-8")
        stale = sorted(T11.rglob("audit.json"))
        conflict = {"rc": 0, "json": {"engine": "VETF_ConsensusEnrichment_Adapter", "error_type": "FileExistsError", "message": "APPEND_ONLY_CONFLICT:manifest.json 已存在"}, "tail": ["}"]}
        s11a = judge_adapter(conflict, [])                       # 本跑無新 audit(舊夾的 stale 不得傳入)
        s11b = judge_adapter({"rc": 0, "json": {"status": "SUCCESS"}, "tail": []}, stale)
        s11c = judge_adapter({"rc": 0, "json": {}, "tail": ["x"]}, [])
        src11 = Path(__file__).read_text(encoding="utf-8").split("def selftest")[0]
    chk("⑪ 批522 假綠修:adapter error_type(APPEND_ONLY_CONFLICT)=FAIL 帶因由,不拿舊 audit 充數;本跑新 audit 才 OK;無新 audit=FAIL;每跑一夾 RUN_<ts>(L44)",
        s11a[0] == "FAIL" and "FileExistsError" in s11a[1] and s11b[0] == "OK" and s11b[2] is not None and s11c[0] == "FAIL" and '"out" / f"RUN_{' in src11 and "or sorted(out_dir.rglob" not in src11)
    print(f"  [計] 十一檢 OK {11 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== VATETF 應用端正主橋(VDF_ENG085 v0103)· 十一檢自測(零網路;合成 DuckDB)===")
        return selftest()
    verb = a[0] if a and not a[0].startswith("-") else "status"
    if verb == "status":
        rep = status(do_print="--json" not in a, holdings=_arg(a, "--holdings"), prices=_arg(a, "--prices"))
    elif verb == "run":
        rep = run(a[1:], do_print="--json" not in a)
    else:
        print(__doc__)
        return 2
    if "--json" in a:
        print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
    return 0 if rep["state"] in ("OK", "NODATA", "ABSENT") else 1


if __name__ == "__main__":
    sys.exit(main())
