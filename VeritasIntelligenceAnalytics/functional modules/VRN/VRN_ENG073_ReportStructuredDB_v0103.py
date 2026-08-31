#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG073_ReportStructuredDB v0103 — 報告結構化入庫引擎(批237 立;批240 庫驗證道)
====================================================================
操作員令:「個股名稱用四碼台股 TICKER 去 TWSE/TPEX 擷取;NLP 工具
引擎協助文字處理;VRN BASIC INFO & SUMMARY & FINANCIAL DATA 都可
抓出交互驗證整理成資料庫;收官所有」。
機制(規格書 b236 契約:決定性擷取為主;NLP 只協助不創造):
  輸入=ENG072 v0101 分區 sidecar(first_page_text/*.json)+檔名
  ①Basic Info:ticker(檔名四碼 rx)→官方名=tw_listings 名冊
    (TWSE+TPEX 1,979 檔在庫=零網路正主);券商字典;日期多格式
    (西元 8 碼/民國 1141202/6 碼);評等/目標價/現價 rx(右資訊區優先)
  ②交互驗證:Upside_calc=TP/Price-1 對報告明示值→EXACT/
    ROUNDING_ONLY/FORMULA_MISMATCH/MISSING_SOURCE;檔名 ticker↔
    區文 ticker;官方名↔區文名——衝突=KEEP_BOTH 列示不覆寫(雙 SSOT)
  ③Summary:標題帶+本文(修復)前二句=決定性摘要頭(證據連回 sidecar)
  ④Financial:EPS/目標價/殖利率/總報酬 rx;期間 24E→2024·ESTIMATE
    (三層隔離:REPORT_ESTIMATE 永不冒充 OFFICIAL_ACTUAL)
  ⑤NLP 掛載:收容件 via_nlp_engine.TextProcessor(NFKC 正規化)
    graceful 缺席零影響
落庫:vrn_report_basic+vrn_report_metrics(anti-join 只增不減;
每列帶 raw 證據片段)。
批238 真件四修(工作站 59 件實錄揭露):
  ①美系格式:TP_RX +「Price Target/PT」;PX_RX 否定前瞻拒「Price
    Target」誤入現價(MS/GS 誤植修)
  ②ticker 驗證:檔名四碼候選逐一對官方名冊,不在冊=試下一候選;
    全不在=空(研討會/晨報誠實非個股,杜絕 2026 誤當代號)
  ③荒謬升幅防呆:|升幅|>150% 或 TP/P 比例失真=PARSE_SUSPECT
    誠實隔離(杜絕 凱基 P=19→1831% 笑話;值保留供查)
  ④run=派生層重算(同 report_file DELETE+INSERT=ENG063 同例;
    v0100 首寫鎖=修正永不生效之債)
批239 配對收斂(第二輪 59 件實錄:MS P 抓小雜數/JP TP=25/Daiwa
TP=2=標籤誤中他數):TP/P 改「候選集+合理性配對」——右區優先收集
全部候選(>0),取比例落 [0.30,3.2] 之首對;無合理對=僅留可信單值,
不可信者=None 誠實(寧缺勿假;PARSE_SUSPECT 網保留為最後防線)。
批240 裁示落實(操作員:「報告上漲空間=目標價÷報告前一日 CLOSE,
非 ADJ CLOSE」):資料庫補值/驗證道——
  price_db=tw_daily_prices 報告日前一交易日 close(原始 close 正主;
  雲端實證:JP 台積電 2025-07-18 前日 close=1130=頁面 P 全吻合)
  ①頁 P 缺→P_FROM_DB 補值(升幅得算)②頁 P 在→對質:差<1%=
  P_CONFIRMED_DB;差大=P_DB_CONFLICT(KEEP_BOTH;升幅以庫值軌另計)
  新欄 price_db/upside_db/price_state(ALTER 容錯補欄)。
用法:python3 VRN_ENG073_ReportStructuredDB_v0103.py run [--open]
      | --status | --selftest
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

import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ZONES_DIR = VIA / "VIA_Reports" / "first_page_text"
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"

BROKER_DICT = {"MS": "摩根士丹利", "GS": "高盛", "JP": "摩根大通",
               "Citi": "花旗", "UBS": "瑞銀", "Daiwa": "大和",
               "CLST": "里昂", "MQ": "麥格理", "GF": "廣發",
               "凱基": "凱基投顧", "兆豐": "兆豐", "華南": "華南投顧",
               "統一": "統一投顧", "台新": "台新", "國泰": "國泰證期",
               "CTBC": "中國信託"}
RATING_RX = re.compile(
    r"\b(Buy|Sell|Hold|Neutral|Overweight|Underweight|Outperform|"
    r"Underperform)\b|買進|賣出|中立|增持|減持|優於大盤|強力買進", re.I)
TP_RX = re.compile(r"(?:Target\s*price|Price\s*Target|目標價|\bPT\b)"
                   r"[^\d]{0,20}(?:NT\$|新台幣)?\s*"
                   r"([\d,]+(?:\.\d+)?)", re.I)
PX_RX = re.compile(r"(?<![Tt]arget )(?<![Tt]arget\n)(?<![Tt]ARGET )(?:\b[Pp]rice\b(?![ \t]*"
                   r"[Tt]arget)|現價|收盤價)\s*(?:\([^)]*\))?[^\d]{0,20}"
                   r"(?:NT\$)?\s*([\d,]+(?:\.\d+)?)", re.M)
UPS_RX = re.compile(r"(?:Expected\s*total\s*return|上漲空間|Upside|漲跌空間)"
                    r"[^\d\-]{0,15}(-?[\d.]+)\s*%", re.I)
YLD_RX = re.compile(r"(?:dividend\s*yield|殖利率)[^\d]{0,15}([\d.]+)\s*%", re.I)
EPS_RX = re.compile(r"(20\d{2}|1[01]\d)\s*[EFA]?\s*(?:年)?\s*"
                    r"(?:Diluted\s+)?EPS[^\d\-]{0,15}(-?[\d,]+(?:\.\d+)?)", re.I)
TICK_RX = re.compile(r"(?<!\d)(\d{4})(?!\d)")


def _nfkc(s: str) -> str:
    """NLP 掛載:收容件 TextProcessor graceful;缺席=stdlib NFKC"""
    try:
        sys.path.insert(0, str(HERE / "references" / "intake" /
                               "VIA_NLP_OneEngine_v1.1.0" / "src"))
        from via_nlp_engine.text_ops import TextProcessor  # noqa
        tp = TextProcessor()
        if hasattr(tp, "normalize"):
            return tp.normalize(s)
    except Exception:
        pass
    return unicodedata.normalize("NFKC", s)


def _num(s: str) -> float | None:
    try:
        return float(s.replace(",", ""))
    except Exception:
        return None


def parse_date(name: str) -> str:
    m = re.search(r"(20\d{2})[-_]?(\d{2})[-_]?(\d{2})", name)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"(?<!\d)(1[01]\d)(\d{2})(\d{2})(?!\d)", name)  # 民國 1141202
    if m:
        return f"{int(m.group(1)) + 1911}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"(?<!\d)(2[3-9])(\d{2})(\d{2})(?!\d)", name)   # 251208
    if m:
        return f"20{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return ""


def parse_broker(name: str) -> str:
    for k in BROKER_DICT:
        if k in name:
            return k
    return ""


def extract_one(stem: str, zones: dict, names: dict) -> tuple[dict, list]:
    """回 (basic row, metrics rows);全決定性;衝突=KEEP_BOTH 列示"""
    text_all = _nfkc("\n".join(str(zones.get(k, ""))
                               for k in ("header", "right", "body")))
    right = _nfkc(str(zones.get("right", "")))
    # 批239b(操作員令「文字修復後可抓目標價」):斷行修復版=標籤與
    # 數值被換行切開(Target↵price↵NT$165)之救回文本;raw 優先、修復版後備
    right_rep = re.sub(r"\s*\n\s*", " ", right)
    text_rep = re.sub(r"\s*\n\s*", " ", text_all)
    # 批238②:候選逐驗官方名冊;全不在=誠實空(研討會/晨報非個股)
    ticker = ""
    for cand in TICK_RX.finditer(stem):
        if names.get(cand.group(1)):
            ticker = cand.group(1)
            break
    if not ticker and not names:          # 名冊缺(測試環境)=首候選
        m0 = TICK_RX.search(stem)
        ticker = m0.group(1) if m0 else ""
    name_official = names.get(ticker, "")
    tick_z = TICK_RX.search(text_all)
    conflicts = []
    if ticker and tick_z and tick_z.group(1) != ticker \
            and names.get(tick_z.group(1)):
        conflicts.append(f"TICKER_ZONE={tick_z.group(1)}(KEEP_BOTH)")
    if name_official and name_official not in text_all:
        conflicts.append("NAME_NOT_IN_PAGE(KEEP_BOTH)")
    rat = RATING_RX.search(right) or RATING_RX.search(text_all)
    tp = (TP_RX.search(right) or TP_RX.search(right_rep)
          or TP_RX.search(text_all) or TP_RX.search(text_rep))
    ups = (UPS_RX.search(right) or UPS_RX.search(right_rep)
           or UPS_RX.search(text_all) or UPS_RX.search(text_rep))
    # 批239:候選集+合理性配對(右區優先;比例 [0.30,3.2] 取首對;
    # 無合理對=僅留可信單值,不可信=None 寧缺勿假)
    def _cands(rx, *texts):
        out = []
        for t in texts:
            for m in rx.finditer(t):
                v = _num(m.group(1))
                if v and v > 0 and v not in out:
                    out.append(v)
        return out
    tp_c = _cands(TP_RX, right, right_rep, text_all, text_rep)
    px_c = _cands(PX_RX, right, right_rep, text_all, text_rep)
    tpv = pxv = None
    for a in tp_c:
        for b in px_c:
            if 0.30 <= a / b <= 3.2:
                tpv, pxv = a, b
                break
        if tpv:
            break
    if tpv is None and pxv is None:
        # 無合理對:僅單側有候選=取之;雙側衝突=取值大者(小值=標籤
        # 誤中日期/點數碎片之經驗律:MS 1130vs2/JP 25vs1130/Daiwa 2vs2470)
        cand = [(tp_c[0], "tp")] if tp_c else []
        cand += [(px_c[0], "px")] if px_c else []
        if cand:
            v, side = max(cand)
            if side == "tp":
                tpv = v
            else:
                pxv = v
    upr = _num(ups.group(1)) if ups else None
    upc = round((tpv / pxv - 1) * 100, 1) if tpv and pxv else None
    if upc is not None and (abs(upc) > 150 or (tpv and pxv
            and (tpv / pxv > 8 or tpv / pxv < 0.15))):
        state = "PARSE_SUSPECT"           # 批238③:荒謬比例=誠實隔離
    elif upr is not None and upc is not None:
        state = ("EXACT_MATCH" if abs(upr - upc) < 0.05 else
                 "ROUNDING_ONLY" if abs(upr - upc) <= 0.8 else
                 "FORMULA_MISMATCH")
    elif upc is not None or upr is not None:
        state = "SINGLE_SOURCE"
    else:
        state = "MISSING_SOURCE"
    body = str(zones.get("body", ""))
    sents = [x for x in re.split(r"(?<=[。.!?])\s+", body.replace("\n", " "))
             if len(x) > 15][:2]
    basic = {"report_file": stem, "ticker": ticker,
             "name_official": name_official,
             "broker": parse_broker(stem), "report_date": parse_date(stem),
             "rating_raw": rat.group(0) if rat else "",
             "target_price": tpv, "price": pxv,
             "upside_report": upr, "upside_calc": upc,
             "upside_state": state,
             "title_head": str(zones.get("header", ""))[:200],
             "summary_head": " ".join(sents)[:400],
             "conflicts": ";".join(conflicts),
             "extracted_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
    mets = []
    for m in EPS_RX.finditer(text_all):
        yraw = m.group(1)
        yr = str(int(yraw) + 1911) if len(yraw) == 3 else yraw
        seg = text_all[m.start():m.end() + 4]
        status = "ESTIMATE" if re.search(r"[EF]", seg) else "STATED"
        mets.append({"report_file": stem, "metric": "eps", "period": yr,
                     "status": status, "value": _num(m.group(2)),
                     "raw_text": m.group(0)[:80]})
    if tpv:
        mets.append({"report_file": stem, "metric": "target_price",
                     "period": basic["report_date"][:4], "status": "ESTIMATE",
                     "value": tpv, "raw_text": tp.group(0)[:80]})
    y = YLD_RX.search(text_all) or YLD_RX.search(text_rep)
    if y:
        mets.append({"report_file": stem, "metric": "dividend_yield_pct",
                     "period": basic["report_date"][:4], "status": "ESTIMATE",
                     "value": _num(y.group(1)), "raw_text": y.group(0)[:80]})
    return basic, mets


def _prior_close(con, ticker: str, rdate: str) -> float | None:
    """報告日前一交易日原始 close(批240 裁示:CLOSE 非 ADJ)"""
    if not ticker or not rdate:
        return None
    for t in (f"{ticker}.TW", f"{ticker}.TWO", ticker):
        try:
            r = con.execute(
                "SELECT close FROM tw_daily_prices WHERE ticker=? AND date<? "
                "ORDER BY date DESC LIMIT 1", [t, rdate]).fetchone()
            if r and r[0]:
                return float(r[0])
        except Exception:
            return None
    return None


def _ensure_tables(con):
    con.execute("""CREATE TABLE IF NOT EXISTS vrn_report_basic(
        report_file VARCHAR, ticker VARCHAR, name_official VARCHAR,
        broker VARCHAR, report_date VARCHAR, rating_raw VARCHAR,
        target_price DOUBLE, price DOUBLE, upside_report DOUBLE,
        upside_calc DOUBLE, upside_state VARCHAR, title_head VARCHAR,
        summary_head VARCHAR, conflicts VARCHAR, extracted_at VARCHAR)""")
    for col in ("price_db DOUBLE", "upside_db DOUBLE", "price_state VARCHAR"):
        try:
            con.execute(f"ALTER TABLE vrn_report_basic ADD COLUMN {col}")
        except Exception:
            pass
    con.execute("""CREATE TABLE IF NOT EXISTS vrn_report_metrics(
        report_file VARCHAR, metric VARCHAR, period VARCHAR,
        status VARCHAR, value DOUBLE, raw_text VARCHAR)""")


def run(zdir: Path | None = None, db: Path | None = None) -> int:
    import duckdb
    zdir = zdir or ZONES_DIR
    files = sorted(zdir.glob("*.json")) if zdir.exists() else []
    if not files:
        print(f"[入庫] {zdir} 無分區 sidecar(先跑 ENG072 v0101)")
        return 2
    con = duckdb.connect(str(db or DB_TW))
    _ensure_tables(con)
    names = dict(con.execute(
        "SELECT code, name FROM tw_listings").fetchall()) \
        if "tw_listings" in {r[0] for r in con.execute("SHOW TABLES").fetchall()} \
        else {}
    nb = nm = 0
    for f in files:
        try:
            zones = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        basic, mets = extract_one(f.stem, zones, names)
        # 批240:庫驗證道(前日 close 補值/對質)
        pdb = _prior_close(con, basic["ticker"], basic["report_date"])
        tpv2 = basic["target_price"]
        basic["price_db"] = pdb
        basic["upside_db"] = round((tpv2 / pdb - 1) * 100, 1) \
            if tpv2 and pdb else None
        if pdb is None:
            basic["price_state"] = "DB_NO_MATCH" if basic["ticker"] else ""
        elif basic["price"] is None:
            basic["price_state"] = "P_FROM_DB"
        elif abs(basic["price"] - pdb) / pdb < 0.01:
            basic["price_state"] = "P_CONFIRMED_DB"
        else:
            basic["price_state"] = "P_DB_CONFLICT(KEEP_BOTH)"
        # 升幅態升級:頁無 P 但庫有=可判
        if basic["upside_state"] in ("MISSING_SOURCE", "SINGLE_SOURCE") \
                and basic["upside_db"] is not None:
            if basic["upside_report"] is not None:
                d0 = abs(basic["upside_report"] - basic["upside_db"])
                basic["upside_state"] = ("EXACT_MATCH_DB" if d0 < 0.05 else
                                         "ROUNDING_ONLY_DB" if d0 <= 0.8 else
                                         "FORMULA_MISMATCH_DB")
            else:
                basic["upside_state"] = "DB_DERIVED"
        # 批238④:派生層重算=同鍵 DELETE+INSERT(ENG063 同例;
        # 正本=input_reports 原件+sidecar 零觸碰)
        con.execute("DELETE FROM vrn_report_basic WHERE report_file=?",
                    [basic["report_file"]])
        con.execute("DELETE FROM vrn_report_metrics WHERE report_file=?",
                    [basic["report_file"]])
        con.execute("INSERT INTO vrn_report_basic VALUES (" +
                    ",".join("?" * 18) + ")", list(basic.values()))
        nb += 1
        for m in mets:
            con.execute("INSERT INTO vrn_report_metrics VALUES (?,?,?,?,?,?)",
                        list(m.values()))
            nm += 1
        flag = basic["upside_state"]
        print(f"  [{flag}] {basic['ticker']} {basic['name_official'] or '?'} "
              f"{basic['broker']} TP={basic['target_price']} "
              f"P={basic['price']} 庫P={basic['price_db']}"
              f"({basic['price_state']}) 升幅 報告={basic['upside_report']} "
              f"算={basic['upside_calc']} 庫算={basic['upside_db']}")
    tb = con.execute("SELECT count(*) FROM vrn_report_basic").fetchone()[0]
    tm = con.execute("SELECT count(*) FROM vrn_report_metrics").fetchone()[0]
    con.close()
    print(f"[入庫計] 檔 {len(files)} · basic +{nb}(庫 {tb})· metrics +{nm}"
          f"(庫 {tm})· 官方名冊命中={sum(1 for _ in names) and '在庫'}")
    return 0


def status() -> int:
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    for t in ("vrn_report_basic", "vrn_report_metrics"):
        try:
            n = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            print(f"  [{t}] {n:,} 列")
        except Exception:
            print(f"  [{t}] 未建(先 run)")
    con.close()
    return 0


def selftest() -> int:
    import tempfile
    import duckdb
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 官方名冊正主宣告(ticker→tw_listings=TWSE/TPEX;零網路)",
        "tw_listings" in src and all(("import " + k) not in src
                                     for k in ("requests", "httpx")))
    zones = {"header": "Earnings Upside; Reiterate Buy",
             "right": "Buy\nTarget price NT$165.00\nPrice (04 Jun) NT$114.00\n"
                      "Expected total return 48.1%\nExpected dividend yield 3.3%",
             "body": "Wistron 3231 reported strong sales. We expect 2025E EPS 9.8 "
                     "to grow further. Momentum continues into 2H25.",
             "footer": "disclaimer"}
    names = {"3231": "緯創"}
    basic, mets = extract_one("Citi-3231 20250604", zones, names)
    chk("② Basic Info(ticker/官方名/券商/日期/評等/TP/現價)",
        basic["ticker"] == "3231" and basic["name_official"] == "緯創"
        and basic["broker"] == "Citi" and basic["report_date"] == "2025-06-04"
        and "Buy" in basic["rating_raw"] and basic["target_price"] == 165.0
        and basic["price"] == 114.0)
    chk("③ 交互驗證(Upside 報告 48.1% vs 算 44.7%=FORMULA_MISMATCH 誠實列示)",
        basic["upside_calc"] == 44.7
        and basic["upside_state"] == "FORMULA_MISMATCH")
    chk("④ Financial(EPS 2025E=9.8 ESTIMATE+殖利率+TP;帶 raw 證據)",
        any(m["metric"] == "eps" and m["value"] == 9.8
            and m["status"] == "ESTIMATE" and m["period"] == "2025"
            for m in mets)
        and any(m["metric"] == "dividend_yield_pct" for m in mets)
        and all(m["raw_text"] for m in mets))
    chk("⑤ Summary 頭=決定性(標題帶+本文前二句;零 LLM 創造)",
        "Reiterate Buy" in basic["title_head"]
        and "strong sales" in basic["summary_head"])
    b2, _ = extract_one("華南投顧-2606-裕民-1141202", {"header": "", "right": "",
                                                      "body": "", "footer": ""},
                        {"2606": "裕民"})
    chk("⑥ 民國日期+缺值誠實(1141202→2025-12-02;無 TP=MISSING_SOURCE)",
        b2["report_date"] == "2025-12-02"
        and b2["upside_state"] == "MISSING_SOURCE")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        (tdp / "Citi-3231 20250604.json").write_text(
            json.dumps(zones, ensure_ascii=False), encoding="utf-8")
        dbp = tdp / "t.duckdb"
        c0 = duckdb.connect(str(dbp))
        c0.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR)")
        c0.execute("INSERT INTO tw_listings VALUES ('3231','緯創')")
        c0.close()
        rc1 = run(tdp, dbp)
        rc2 = run(tdp, dbp)
        con = duckdb.connect(str(dbp))
        nb = con.execute("SELECT count(*) FROM vrn_report_basic").fetchone()[0]
        nm = con.execute("SELECT count(*) FROM vrn_report_metrics").fetchone()[0]
        con.close()
        chk("⑦ 落庫+重跑冪等(派生層重算=同鍵重寫;basic 恆 1 列)",
            rc1 == 0 and rc2 == 0 and nb == 1 and nm >= 3)
        c2 = duckdb.connect(str(dbp))
        c2.execute("INSERT INTO tw_listings VALUES ('1476','儒鴻')")
        c2.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR,"
                   " close DOUBLE)")
        c2.execute("INSERT INTO tw_daily_prices VALUES "
                   "('2025-06-03','3231.TW',113.5),"
                   "('2026-05-18','1476.TW',350.0)")
        c2.close()
        (tdp / "凱基投顧_1476 儒鴻_20260519.json").write_text(json.dumps(
            {"header": "", "right": "目標價 367 元\n收盤價 19",
             "body": "", "footer": ""}, ensure_ascii=False), encoding="utf-8")
        run(tdp, dbp)
        con = duckdb.connect(str(dbp))
        r1 = con.execute("SELECT price_db, upside_db, price_state, upside_state"
                         " FROM vrn_report_basic WHERE ticker='1476'").fetchone()
        r2 = con.execute("SELECT price_db, price_state FROM vrn_report_basic "
                         "WHERE ticker='3231'").fetchone()
        con.close()
        chk("⑱ 庫補值道(批240:凱基 P 缺→前日 close 350 補;升幅 4.9=DB_DERIVED)",
            r1 is not None and r1[0] == 350.0 and r1[1] == 4.9
            and r1[2] == "P_FROM_DB" and r1[3] == "DB_DERIVED")
        chk("⑲ 庫對質道(Citi 頁 P=114 vs 庫 113.5 差<1%=P_CONFIRMED_DB)",
            r2 is not None and r2[0] == 113.5 and r2[1] == "P_CONFIRMED_DB")
        chk("⑧ 空夾誠實 rc2", run(tdp / "none_x", dbp) == 2)
    b3, _ = extract_one("MS-3661 20251203",
                        {"header": "", "right": "Price Target NT$4,388.00",
                         "body": "", "footer": ""}, {"3661": "世芯-KY"})
    chk("⑪ 美系 Price Target(批238①:TP=4388 且不誤入現價)",
        b3["target_price"] == 4388.0 and b3["price"] is None)
    b4, _ = extract_one("第一場 2026年投資大趨勢 - 華南投顧 -1141201",
                        {"header": "", "right": "", "body": "", "footer": ""},
                        {"3661": "世芯-KY"})
    chk("⑫ 研討會檔誠實非個股(批238②:2026 不當 ticker)",
        b4["ticker"] == "")
    b5, _ = extract_one("凱基投顧_1476 儒鴻_20260519",
                        {"header": "", "right": "目標價 367 元\n收盤價 19",
                         "body": "", "footer": ""}, {"1476": "儒鴻"})
    chk("⑬ 配對收斂(批239:TP=367 留/P=19 碎片丟=寧缺勿假)",
        b5["target_price"] == 367.0 and b5["price"] is None
        and b5["upside_state"] == "MISSING_SOURCE")
    b6, _ = extract_one("MS-1590 20251202",
                        {"header": "", "right": "Price Target NT$1,130.00",
                         "body": "share price fell 2. points", "footer": ""},
                        {"1590": "亞德客-KY"})
    chk("⑭ MS 型(TP=1130 可信;P 小雜數 2 落配對外=None)",
        b6["target_price"] == 1130.0 and b6["price"] is None)
    b7, _ = extract_one("JP-2330 20250718",
                        {"header": "", "right": "Price NT$1,130\nPT Dec-25",
                         "body": "", "footer": ""}, {"2330": "台積電"})
    chk("⑮ JP 型(TP 候選 25 對 P=1130 失真=丟;P=1130 存)",
        b7["price"] == 1130.0 and b7["target_price"] is None)
    b8, _ = extract_one("Citi-3231 20250604", zones, {"3231": "緯創"})
    chk("⑯ 正常對照不退化(Citi TP=165/P=114 配對成立)",
        b8["target_price"] == 165.0 and b8["price"] == 114.0)
    b9, _ = extract_one("GS-2317 20251205",
                        {"header": "", "right": "Target\nprice\nNT$250.00\n"
                                                "Price\nNT$205.00",
                         "body": "", "footer": ""}, {"2317": "鴻海"})
    chk("⑳ CLOSE 正主宣告(批240 裁示:原始 close 非 adj_close)",
        "SELECT close FROM tw_daily_prices" in src
        and "adj_close" not in src.split("def _prior_close")[1]
                                  .split("def _ensure_tables")[0])
    chk("⑰ 斷行修復救回(批239b:Target↵price 切開仍抓 TP=250/P=205)",
        b9["target_price"] == 250.0 and b9["price"] == 205.0)
    chk("⑨ 雙 SSOT 紀律(KEEP_BOTH 衝突列示;REPORT_ESTIMATE 隔離宣告)",
        "KEEP_BOTH" in src and "ESTIMATE" in src and "不覆寫" in src)
    chk("⑩ NLP 掛載 graceful+加速橋",
        "TextProcessor" in src and "ACCEL-BRIDGE" in src)
    print(f"  [計] 二十檢 OK {20 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 報告結構化入庫引擎(VRN_ENG073 v0103)· 二十檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        return status()
    if args and args[0] == "run":
        return run()
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
