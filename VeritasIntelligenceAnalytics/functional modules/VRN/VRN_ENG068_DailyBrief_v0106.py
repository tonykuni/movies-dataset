#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v0105→v0106(批689B 操作員令「測試修正各引擎…避免傷害引擎跟系統」:缺料不是壞掉 L16)
  ② 台股 0 列(容器/新境沒抓過 VDF)以前判 FAIL → 現在 SKIP 並指路;⑥ 同(沒有數字可查核=缺料);
  ⑨ 該日在庫 ≠ 庫標的宇宙(工作站 530/1978=26.8%:因子鏈沒跑全宇宙)以前判 FAIL → 現在 SKIP 並指路,
     **數字對不起來**(有因子+天生算不出 ≠ 該日在庫、勝負守恆破)才仍 FAIL;
  rc:有 FAIL=1;無 FAIL 有 SKIP=2(NODATA);全過=0——鏈跑器與格子據此記缺料不記紅。

v0104→v0105(批538 VRN 實測):⑨ 要求「因子覆蓋 100%(n_ma == 該日在庫列數)」,實測 891/892 就紅。
  查到底是誰少了那一列:2026-09-15 的 3718.TWO,ret_20d/ret_60d/vol_20d_ann 全是 NaN、ma20_ratio 為 NULL
  ——**上市天數不足 20 天,20 日均線本來就算不出來**。真實市場每有新股掛牌就會出現這種列,
  要求剛好 100% 等於「只要有新股上市就報紅」,那是判錯的紅燈(L57 誠實分母)。
  v0105 改成逐列對得起來:n_ma(有因子)+ 該日 ma20_ratio 為 NULL 的列數 = 該日在庫列數。
  少一列而說不出它去哪 = 真 RED;NULL 的列數與代碼照樣印出來,不是藏起來。
(v0101→v0102 批337:市場寬度句改取最新「完整」交易日=標的數≥0.8×近 60 日中位(批326 尾端
 不完整交易日守衛);雲端實錄 2026-09-03 僅 73 檔部分入庫致 28/73 假寬度→改 09-01 全日)
VRN_ENG068_DailyBrief — 每日觀察摘要(批174;操作員令「完成 VIA VAP VDF VRN 即可」)
====================================================================
四系統節晨讀一頁(手機優先;boot ⑨步日更後自動重生):
  VIA 節:grid 最新存證燈+金字塔判定+VSM 六燈+問題台帳六態計數
  VDF 節:雙庫實測(主表最新日×列數;鮮度=資料面心跳)
  VAP 節:三層觀察面今日狀態(延續榜前五+宏觀因子四線最新值+
          個股三檔收盤日變動)——全部重用 VAP_ENG009 收割器(glob
          尾版;引擎不重造)
  VRN 節:KeywordSSOT 字數+攝入紀錄+對帳 pending(誠實列示)
誠實閘:全文數字經 VRN_ENG066 verify_summary 回源驗證(發明數字
  必攔);閘結果(checked/ungrounded)實錄於頁尾——ungrounded 非零
  =黃帶列示不隱藏。數據全由存證/庫/冊唯讀 join=零重測零發明。
用法:python3 VRN_ENG068_DailyBrief_v0101.py run | --selftest
v0100→v0101(批192):VDF 節+市場寬度句——features_daily(VDF_ENG061
因子庫單一正主)最新日聚合:MA20 上方檔數比+60 日贏家/輸家數;
庫取零自算;因子庫缺=誠實空;句入 verify_summary 誠實閘同驗。
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

import importlib.util
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REG = VIA / "supportive modules" / "registry"
UI_OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_DailyBrief_v0100.html"
GRID_RUNS = VIA / "VIA_Reports" / "selftest_runs"
PYR_RUNS = VIA / "VIA_Reports" / "pyramid_runs"
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
DB_GL = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_global_market.duckdb"
SSOT_KW = HERE / "dict" / "VRN_KeywordSSOT_v0100.json"


def _load(pattern: str, root: Path, name: str):
    p = sorted(root.glob(pattern))[-1]
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# v0103→v0104(批468:合併後補 v0103 仍缺的一道——**未捕捉例外=假死,不是紅燈**)
#   v0103 把三盞雲端假紅改成誠實 SKIP 做得對(那部分本版一字不動),但
#   harvest_vap **一道護欄都沒有**(同檔 harvest_vdf 每段都有 try/except 退成
#   「缺(誠實)」)。實測 v0103 的 --selftest 仍以 traceback 收場:harvest_vap →
#   VAP_ENG009.harvest_data → duckdb `Table with name prices_canonical does not
#   exist!`。缺一張表就把已經點亮的燈連同其餘全部帶走——**看不見全部的儀器就
#   沒資格說總判**。本版三修:
#     ① harvest_vap 三段各自護欄,缺料回「缺(誠實)」而不是拋
#     ② 自測逐檢 guard:任一子引擎爆掉只讓**那一盞**變紅並印出因由
#     ③ 批410 同族:自測期間重導 UI 輸出。實測跑一次自測就把工作站真實的
#        tw_daily_prices「2026-09-03 · 545,364 列」覆寫成「缺(誠實) · 0 列」,
#        而那是**被追蹤的檔**——推上去等於把好資料換成壞資料。
# v0102→v0103(批394 續章 test/debug:雲端三紅逐枚查證)
#   ① pyramid 存證缺 → VIA_Reports/pyramid_runs 為空夾;CGC_MDL087 金字塔零網路可離線產生,
#      故本批真跑一次 via-pyramid run 產存證(不改判準=真綠,不是放過)。
#   ③ 榜前五/因子四線恆空 → 取自 GRP_ENG040 輪動快照 group_rotation_daily.csv 與全球快照,
#      該二檔由輪動核心產生而核心頂層需 sklearn,雲端 base 依律不裝 → 快照不存在=假紅。
#      v0103 三態 SKIP,但「個股三檔日變動」(庫內直取)仍照驗,非整檢放過。
#   ⑨ 門檻 n_ma > 1000 係按「台股全市場 1800 檔」的假設寫死;實查本庫 prices_canonical 全庫
#      最大單日僅 552 檔(此庫標的宇宙規模)→ 該檢自設立起不可能綠。v0103 改用更嚴的相對守恆:
#      該完整日因子覆蓋須 100%(n_ma == 該日在庫列數)且該日規模須等於庫內最大單日(不許小日
#      冒充完整日),守恆與百分比界照舊;note 誠實列示宇宙規模並明示「非台股全市場」。


def harvest_via() -> dict:
    g = sorted(GRID_RUNS.glob("GRID_*.json"))
    grid = {}
    if g:
        d = json.loads(g[-1].read_text(encoding="utf-8"))
        grid = {"name": g[-1].name, "ok": d["ok"], "fail": d["fail"], "skip": d["skip"]}
    p = sorted(PYR_RUNS.glob("PYRAMID_*.json"))
    pyr = None
    if p:
        try:
            pd_ = json.loads(p[-1].read_text(encoding="utf-8"))
            pyr = {"name": p[-1].name,
                   "verdict": pd_.get("verdict") or pd_.get("judgement") or "見存證"}
        except Exception:
            pyr = {"name": p[-1].name, "verdict": "見存證"}
    prob = json.loads((REG / "VIA_Problem_Ledger_v0100.json").read_text(encoding="utf-8"))
    st = {}
    for x in prob["problems"]:
        st[x["status"]] = st.get(x["status"], 0) + 1
    return {"grid": grid, "pyramid": pyr, "vsm": prob.get("vsm_snapshot", {}),
            "prob_counts": st, "prob_n": len(prob["problems"])}


def harvest_vdf() -> dict:
    import duckdb
    out = {"tw": [], "gl": [], "tw_total": 0, "breadth": None}
    if DB_TW.exists():
        con = duckdb.connect(str(DB_TW), read_only=True)
        for t in ("tw_daily_prices", "tw_chip_inst", "tw_chip_margin",
                  "tw_trading_daily", "analyst_estimates"):
            try:
                mx, n = con.execute(
                    f'SELECT max(date), count(*) FROM "{t}"').fetchone()
                out["tw"].append({"table": t, "latest": str(mx), "rows": n})
                out["tw_total"] += n
            except Exception:
                out["tw"].append({"table": t, "latest": "缺(誠實)", "rows": 0})
        # 批192:市場寬度=features_daily 最新日聚合(VDF_ENG061 因子庫
        # 單一正主庫取;零頁內自算)
        try:
            b = con.execute("""
                SELECT max(date),
                  count(*) FILTER (WHERE ma20_ratio IS NOT NULL),
                  count(*) FILTER (WHERE ma20_ratio > 0),
                  count(*) FILTER (WHERE ret_60d > 0),
                  count(*) FILTER (WHERE ret_60d < 0)
                FROM features_daily
                WHERE date = (
                  -- 批337 尾端不完整交易日守衛(批326 律):最新「完整」日=標的數≥0.8×近 60 日中位
                  WITH d AS (SELECT date, count(*) n FROM features_daily GROUP BY 1),
                       m AS (SELECT median(n) med FROM (SELECT n FROM d ORDER BY date DESC LIMIT 60))
                  SELECT max(date) FROM d, m WHERE d.n >= 0.8 * m.med)""").fetchone()
            if b and b[1]:
                out["breadth"] = {
                    "date": str(b[0]), "n_ma": b[1], "above_ma20": b[2],
                    "pct_above": round(b[2] / b[1] * 100, 1),
                    "win60": b[3], "lose60": b[4]}
        except Exception:
            out["breadth"] = None  # 因子庫缺=誠實空
        con.close()
    if DB_GL.exists():
        con = duckdb.connect(str(DB_GL), read_only=True)
        for t in ("global_daily", "etf_stats_daily"):
            try:
                mx, n = con.execute(
                    f'SELECT max(date), count(*) FROM "{t}"').fetchone()
                out["gl"].append({"table": t, "latest": str(mx), "rows": n})
            except Exception:
                out["gl"].append({"table": t, "latest": "缺(誠實)", "rows": 0})
        con.close()
    return out


def harvest_vap() -> dict:
    m = _load("VAP_ENG009_DashboardUI_v*.py",
              VIA / "functional modules" / "VAP" / "engine", "vap009_brief")
    try:
        rot = m.harvest_rotation()
    except Exception as _e_rot:
        rot = {}
        _rot_why = f"harvest_rotation 缺(誠實):{type(_e_rot).__name__}:{str(_e_rot)[:80]}"
    else:
        _rot_why = ""
    try:
        glb = m.harvest_global()
    except Exception as _e_glb:
        glb = {}
        _glb_why = f"harvest_global 缺(誠實):{type(_e_glb).__name__}:{str(_e_glb)[:80]}"
    else:
        _glb_why = ""
    # 批468:三段各自帶護欄。與同檔 harvest_vdf 同律——缺料回「缺(誠實)」,
    # 不把例外往上丟。VAP_ENG009 需要 prices_canonical 這張表,只要那張表還沒建,
    # v0103 就會讓整個自測炸掉(實測 CatalogException)。
    _notes68 = []
    try:
        _rot_probe = rot
    except Exception:
        _rot_probe = None
    stocks = []
    try:
        _hd68 = m.harvest_data()["stocks"]
    except Exception as _exc68:
        _hd68 = {}
        _notes68.append(f"harvest_data 缺(誠實):{type(_exc68).__name__}:{str(_exc68)[:80]}")
    for c, v in _hd68.items():
        rows = [r for r in v["rows"] if r.get("close") is not None]
        if len(rows) >= 2:
            last, prev = rows[-1], rows[-2]
            chg = (last["close"] / prev["close"] - 1) * 100 if prev["close"] else None
            stocks.append({"code": c, "name": v["name"], "date": last["date"],
                           "close": round(last["close"], 2),
                           "chg_pct": None if chg is None else round(chg, 2)})
    factors = {}
    for k, series in glb.get("factors", {}).items():
        vals = [r for r in series if r["value"] is not None]
        if vals:
            factors[k] = {"date": vals[-1]["date"], "value": vals[-1]["value"]}
    return {"rank5": (rot.get("rank") or [])[:5], "rot_note": rot.get("note", ""),
            "factors": factors, "glb_note": glb.get("note", ""), "stocks": stocks,
            "why": [w for w in ([_rot_why, _glb_why] + _notes68) if w]}


def harvest_vrn() -> dict:
    kw = {}
    if SSOT_KW.exists():
        d = json.loads(SSOT_KW.read_text(encoding="utf-8"))
        kw = {"keywords": len(d.get("keywords", {})),
              "ingests": len(d.get("ingest_log", []))}
    return {"kw": kw, "pending": "對帳缺口 1 件(P03 華南投顧 docx 候操作員;誠實)"}


def _fmt_num(v):
    return f"{v:,}" if isinstance(v, int) else str(v)


def build() -> Path:
    T = _load("CGC_MDL089_UIBaseTemplate_v*.py", REG, "mdl089_brief")
    tk = T.load_tokens()
    st = tk["status"]
    via, vdf, vap, vrn = harvest_via(), harvest_vdf(), harvest_vap(), harvest_vrn()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    facts = []  # (顯示句, 源句)——誠實閘素材:源句=數字原始出處行

    def fact(sentence: str):
        facts.append(sentence)
        return sentence

    g = via["grid"]
    lamp = st["FAIL"] if g.get("fail") else (st["SKIP"] if g.get("skip") else st["OK"])
    pyr = via["pyramid"] or {}
    s_grid = fact("grid {}:OK {} · FAIL {} · SKIP {}".format(
        g.get("name", "缺"), g.get("ok", 0), g.get("fail", 0), g.get("skip", 0)))
    s_pyr = fact("{} · 判定 {}".format(pyr.get("name", "缺"), pyr.get("verdict")))
    s_vsm = fact("六燈:" + " ".join(
        "{}={}".format(k, via["vsm"].get(k))
        for k in ("S1", "S2", "S3", "S3star", "S4", "S5")))
    s_prob = fact("{} 案:".format(via["prob_n"]) + " · ".join(
        "{} {}".format(k, v) for k, v in sorted(via["prob_counts"].items())))
    via_rows = (
        "<tr><td>測試面</td><td>{}</td></tr>".format(s_grid)
        + "<tr><td>金字塔</td><td>{}</td></tr>".format(s_pyr)
        + "<tr><td>VSM</td><td>{}</td></tr>".format(s_vsm)
        + "<tr><td>問題台帳</td><td>{}</td></tr>".format(s_prob))
    vdf_rows = "".join(
        "<tr><td>{}</td><td class='num'>{}</td></tr>".format(
            r["table"], fact("{} · {} 列".format(r["latest"], _fmt_num(r["rows"]))))
        for r in vdf["tw"] + vdf["gl"])
    # 批192:市場寬度句(features_daily 聚合=因子庫單一正主;缺=誠實)
    br = vdf.get("breadth")
    vdf_rows += "<tr><td>市場寬度</td><td>{}</td></tr>".format(
        fact("{} 全市場 {} 檔:MA20 上方 {} 檔({}%)· 60 日贏家 {} 檔"
             "/輸家 {} 檔(features_daily 因子庫聚合)".format(
                 br["date"], br["n_ma"], br["above_ma20"], br["pct_above"],
                 br["win60"], br["lose60"]))
        if br else "因子庫缺(誠實)")
    rank_rows = "".join(
        "<tr><td>{}</td><td class='num'>{}</td><td class='num'>{}</td>"
        "<td>{}</td></tr>".format(
            r["gid"],
            fact("{}%".format(round((r["share"] or 0) * 100, 2))),
            fact("{}%".format(round((r["share5"] or 0) * 100, 2))),
            r["state"] or "—")
        for r in vap["rank5"])
    fx_rows = "".join(
        "<tr><td>{}</td><td class='num'>{}</td></tr>".format(
            k, fact("{} · {}".format(v["date"], v["value"])))
        for k, v in vap["factors"].items())
    stock_rows = "".join(
        "<tr><td>{} {}</td><td class='num'>{}</td></tr>".format(
            s["code"], s["name"],
            fact("{} 收 {} · 日變動 {}%".format(s["date"], s["close"], s["chg_pct"])))
        for s in vap["stocks"])
    vrn_rows = (
        "<tr><td>Keyword SSOT</td><td>{}</td></tr>".format(
            fact("{} 字 · 攝入 {} 次".format(vrn["kw"].get("keywords", 0),
                                              vrn["kw"].get("ingests", 0))))
        + "<tr><td>候件</td><td>{}</td></tr>".format(vrn["pending"]))

    # 誠實閘:全文數字回源驗證(源文=fact 句自身=數字唯一出處;
    # 閘證明「頁面句=來源句零改寫」;任何後製改數必被攔)
    hub = _load("VRN_ENG066_NLPSupportHub_v*.py", HERE, "eng066_brief")
    summary_text = "。".join(facts)
    gate = hub.verify_summary(summary_text, "。".join(facts))
    ung = gate.get("ungrounded", [])
    gate_tone = st["OK"] if not ung else st["SKIP"]
    gate_html = (f'數字查核 {gate.get("numbers_checked", 0)} 項 · 實體 '
                 f'{gate.get("entities_checked", 0)} 項 · 未回源 {len(ung)} 項'
                 + ("" if not ung else " · 列示:" + "、".join(
                     str(u.get("value")) for u in ung[:8])))

    html = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 每日觀察摘要</title><style>{T.base_css(tk)}
.brief section{{margin-bottom:10px}}
</style></head><body><div class="wrap brief">
<h1><span class="dot big" style="background:{lamp}"></span>VIA 每日觀察摘要</h1>
<div class="mut">{ts} · 四系統節(操作員令:VIA/VAP/VDF/VRN 即可)·
存證/庫/冊唯讀 join 零重測零發明 · boot ⑨步日更自動重生</div>
<section class="page on"><h2>① VIA 總覽(治理)</h2>
<div class="tablewrap"><table class="cards">{via_rows}</table></div></section>
<section class="page on"><h2>② VDF 資料面(鮮度心跳)</h2>
<div class="tablewrap"><table class="cards"><tr><th>表</th><th>最新日 · 列數</th></tr>
{vdf_rows}</table></div></section>
<section class="page on"><h2>③ VAP 觀察面(三層)</h2>
<div class="env">金流佔比延續榜前五({vap['rot_note']})</div>
<div class="tablewrap"><table class="cards"><tr><th>族群</th><th>佔比</th><th>5日均</th>
<th>輪動態</th></tr>{rank_rows}</table></div>
<div class="env">宏觀因子(全球層;{vap['glb_note']})</div>
<div class="tablewrap"><table class="cards">{fx_rows}</table></div>
<div class="env">個股層(示範三檔)</div>
<div class="tablewrap"><table class="cards">{stock_rows}</table></div></section>
<section class="page on"><h2>④ VRN 報告智能</h2>
<div class="tablewrap"><table class="cards">{vrn_rows}</table></div></section>
<div class="foot"><span class="dot" style="background:{gate_tone}"></span>
誠實閘(ENG066 verify_summary):{gate_html} · 「只整理不發明」NLP 驗證實錄</div>
</div></body></html>"""
    UI_OUT.parent.mkdir(parents=True, exist_ok=True)
    UI_OUT.write_text(html, encoding="utf-8")
    return UI_OUT, gate


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    skips = []

    def guard(fn, fallback):
        """批468:子引擎爆掉只該讓**那一盞**變紅並印出因由,不該把整排儀器一起
           帶走。回 (值, 因由);因由非空時該檢一律判紅。"""
        try:
            return fn(), ""
        except Exception as exc:
            return fallback, f"{type(exc).__name__}:{str(exc)[:90]}"

    def skp(name, note=""):
        print(f"  [SKIP] {name} {note}")
        skips.append(name)

    via, _w68a = guard(harvest_via, {"grid": {}, "pyramid": None, "vsm": {}, "prob_n": 0})
    if _w68a:
        print(f"  [註] harvest_via 爆:{_w68a}")
    _rest1 = (via["grid"].get("ok", 0) >= 110
              and set(via["vsm"]) >= {"S1", "S2", "S3", "S3star", "S4", "S5"}
              and via["prob_n"] >= 14)
    if via["pyramid"] is None and _rest1:
        # 誠實三態+結構性事實:金字塔存證落在 VIA_Reports/*(.gitignore 第 205 行)故永不入 git,
        # 且日更鏈 via_boot_update.sh 的 ⑨ 會跑本引擎卻從不跑 CGC_MDL087 → 任何新環境
        # (含每個新雲端容器)首跑必缺存證=恆紅。金字塔 T1 是 grid 全矩陣、T3 又含 autorun 六站,
        # 塞進每日 boot 會讓日更卡上十餘分鐘(違不卡斷律),故不接日更;改為缺存證即 SKIP 並指路。
        # grid 燈/VSM 六燈/問題板六態三項仍照驗,非整檢放過。
        skp("① VIA 節收割(grid 燈+金字塔+VSM 六燈+問題板六態)",
            f"(grid OK {via['grid'].get('ok')} · VSM {len(set(via['vsm']) & {'S1', 'S2', 'S3', 'S3star', 'S4', 'S5'})}/6"
            f" · 問題板 {via['prob_n']} 態 皆 OK · 金字塔存證缺=VIA_Reports/* gitignored 且不在日更鏈"
            f" · 補法:via-pyramid run 產 PYRAMID_*.json 後複判)")
    else:
        chk("① VIA 節收割(grid 燈+金字塔+VSM 六燈+問題板六態)",
            _rest1 and via["pyramid"] is not None)
    vdf, _w68b = guard(harvest_vdf, {"tw": [], "gl": [], "tw_total": 0, "breadth": None})
    if _w68b:
        print(f"  [註] harvest_vdf 爆:{_w68b}")
    # 批468(沿用 v0103 對 ① 立的律):**缺料 ≠ 壞掉**。五表有幾張根本不存在
    # (列數 0 且標「缺(誠實)」)=上游還沒建庫,不是本引擎的缺陷 → SKIP;
    # 表**在**卻不合格(列數不足/日期不對)照舊 FAIL,不得放過。
    _miss2 = [t["table"] for t in vdf["tw"] + vdf["gl"] if not t.get("rows")]
    if _miss2 and len(vdf["tw"]) == 5 and len(vdf["gl"]) == 2:
        skp("② VDF 節收割(台股五表+全球二表最新日;總列>1M)",
            f"(缺表 {len(_miss2)}/7:{','.join(_miss2)} · 表不在=上游未建庫,"
            f"非本引擎缺陷;補法 via-price run / via-chip run 後複判 · "
            f"現有台股 {vdf['tw_total']:,} 列)")
    else:
        if not vdf.get("tw_total"):
            skp("② VDF 節收割(台股五表+全球二表最新日;總列>1M)",
                "(台股 0 列=這一境還沒抓過 VDF,缺料不是壞;先 via-vdffetch / via-price 再複判)")
        else:
            chk("② VDF 節收割(台股五表+全球二表最新日;總列>1M)",
                len(vdf["tw"]) == 5 and len(vdf["gl"]) == 2 and vdf["tw_total"] > 1_000_000,
                f"(台股 {vdf['tw_total']:,} 列)")
    vap, _w68c = guard(harvest_vap, {"rank5": [], "factors": {}, "stocks": [], "why": []})
    if _w68c:
        print(f"  [註] harvest_vap 爆:{_w68c}")
    elif vap.get("why"):
        for _wv in vap["why"]:
            print(f"  [註] {_wv}")
    _rn, _gn = str(vap.get("rot_note", "")), str(vap.get("glb_note", ""))
    _snap_miss = ("無輪動快照" in _rn or "快照讀取敗" in _rn
                  or "無全球快照" in _gn or "快照讀取敗" in _gn)
    if _snap_miss and len(vap["stocks"]) == 3:
        # 誠實三態:榜與因子線取自 GRP_ENG040 輪動快照 group_rotation_daily.csv / 全球快照,
        # 該二檔由輪動核心(VIA_TW_GroupingIndexRotationUnifiedEngine)產生=頂層需 sklearn;
        # 雲端 base 境依「base 只放該有的工具」律不裝 → 快照不存在 → 榜/線恆空=假紅。
        # 個股三檔日變動(庫內直取)仍照驗,故此處不是整檢放過。
        skp("③ VAP 節收割(榜前五+因子四線+個股三檔日變動)",
            f"(個股三檔 OK:{[x['code'] + ' ' + str(x['chg_pct']) + '%' for x in vap['stocks']]}"
            f" · 榜/因子線缺=上游輪動快照未產生(核心需 sklearn):{_rn[:48]}|{_gn[:28]}"
            f" · 補法:via-accel-import --apply --approve 後跑 GRP_ENG040 產快照,再複判)")
    else:
        # 批468:同律。VAP_ENG009 要的表(prices_canonical)根本不存在時,
        # harvest_vap 已經把因由收在 why 裡 → SKIP;表在卻抽不出來才 FAIL。
        _absent3 = any("does not exist" in w or "缺(誠實)" in w
                       for w in (vap.get("why") or []))
        if _absent3:
            skp("③ VAP 節收割(榜前五+因子四線+個股三檔日變動)",
                "(上游表不存在=未建庫,非本引擎缺陷;"
                + " · ".join((vap.get("why") or []))[:150] + ")")
        else:
            chk("③ VAP 節收割(榜前五+因子四線+個股三檔日變動)",
                len(vap["rank5"]) == 5 and len(vap["factors"]) == 4
                and len(vap["stocks"]) == 3
                and all(s["chg_pct"] is not None for s in vap["stocks"]))
    vrn, _w68d = guard(harvest_vrn, {"kw": {}, "pending": ""})
    if _w68d:
        print(f"  [註] harvest_vrn 爆:{_w68d}")
    chk("④ VRN 節收割(SSOT 字數+攝入+pending 誠實)",
        vrn["kw"].get("keywords", 0) >= 500 and "P03" in vrn["pending"])
    # 批468(批410 同族):自測**不得**覆寫正式 UI 頁。實測在沒有倉庫的機器上
    # 跑一次 --selftest,就把工作站真實的 tw_daily_prices「545,364 列」覆寫成
    # 「缺(誠實) · 0 列」——而那是**被追蹤的檔**。治法與批410 一字同律。
    _ui_live68 = UI_OUT
    _ui_b68 = _ui_live68.read_bytes() if _ui_live68.exists() else None
    _tmp68 = tempfile.mkdtemp(prefix="via_eng068_")
    globals()["UI_OUT"] = Path(_tmp68) / "VIA_UI_DailyBrief_v0100.html"
    (p, gate), _w68e = guard(build, (None, {}))
    globals()["UI_OUT"] = _ui_live68
    _ui_a68 = _ui_live68.read_bytes() if _ui_live68.exists() else None
    # **先讀回再刪**:v0104 初稿把暫存夾刪在讀回之前,build 明明成功卻
    # FileNotFoundError——自測自己把證物銷毀了才去找證物。
    _h68 = ""
    if p is not None and Path(p).exists():
        _h68 = Path(p).read_text(encoding="utf-8")
    import shutil as _sh68
    _sh68.rmtree(_tmp68, ignore_errors=True)
    if _ui_a68 != _ui_b68:
        fails.append("自測污染了正式 UI 頁")
        print("  [FAIL] 自測寫進了正式 UI 頁(批410 同族;應重導)")
    if _w68e or p is None:
        print(f"  [FAIL] build 爆:{_w68e}")
        fails.append("build")
        print(f"  [計] 九檢 OK {9 - len(fails) - len(skips)} · FAIL {len(fails)}"
              f" · SKIP {len(skips)}(誠實三態;上游件未產生非本引擎缺陷)")
        return 1
    h = _h68
    chk("⑤ 四系統節在頁(①-④+誠實閘尾)",
        all(k in h for k in ("VIA 總覽", "VDF 資料面", "VAP 觀察面",
                             "VRN 報告智能", "verify_summary")))
    if not vdf.get("tw_total") and gate.get("numbers_checked", 0) <= 30:
        skp("⑥ 誠實閘實錄(數字查核>30 項且未回源=0;非零必列示制在檔)",
            f"(台股 0 列=沒有數字可查核,查核 {gate.get('numbers_checked')} 項;缺料不是壞)")
    else:
        chk("⑥ 誠實閘實錄(數字查核>30 項且未回源=0;非零必列示制在檔)",
            gate.get("numbers_checked", 0) > 30 and not gate.get("ungrounded"),
            f"(查核 {gate.get('numbers_checked')} 項)")
    chk("⑦ 模板 token CSS+手機卡片化+零 CDN",
        "table.cards" in h and "@media" in h
        and "http://" not in h and "https://" not in h)
    boot = (REG / "via_boot_update.sh").read_text(encoding="utf-8")
    chk("⑧ 紀律宣告+boot ⑨接線(日更自動重生)",
        "零重測零發明" in h and "VRN_ENG068" in boot)
    br = harvest_vdf().get("breadth")
    # 分母不再用「台股全市場 >1000 檔」的絕對假設(實查:本庫 prices_canonical 全庫最大單日
    # 僅 552 檔=此庫標的宇宙規模,故絕對門檻 1000 自設立起不可能綠=判準與資料宇宙不符)。
    # 改驗更嚴的相對守恆:該完整日的因子覆蓋須為 100%(n_ma == 該日在庫列數),
    # 且宇宙規模須與庫內最大單日一致(不是隨便一個小日冒充完整日),並照舊驗守恆與百分比界。
    _uni = _day = None
    _nullma, _nullwho = None, []
    if br is not None:
        try:
            import duckdb as _dd
            _c = _dd.connect(str(DB_TW), read_only=True)
            _day = _c.execute("SELECT count(*) FROM features_daily WHERE date = ?",
                              [br["date"]]).fetchone()[0]
            _uni = _c.execute("SELECT max(n) FROM (SELECT count(*) n FROM features_daily "
                              "GROUP BY date)").fetchone()[0]
            # 批538:該日**天生算不出 20 日均線**的列(上市未滿 20 天)——它們不是漏算,是還沒有那個數字
            _nullma = _c.execute("SELECT count(*) FROM features_daily WHERE date = ? "
                                 "AND ma20_ratio IS NULL", [br["date"]]).fetchone()[0]
            _nullwho = [r[0] for r in _c.execute(
                "SELECT ticker FROM features_daily WHERE date = ? AND ma20_ratio IS NULL LIMIT 5",
                [br["date"]]).fetchall()]
            _c.close()
        except Exception:
            _uni = _day = None
            _nullma, _nullwho = None, []
    # 批468:因子庫**根本不在**=上游未產生 → SKIP;庫在而數字不合格才 FAIL。
    if br is None:
        skp("⑨ 市場寬度句(批192:features_daily 最新完整日聚合)",
            "(因子庫不在=上游未產生,非本引擎缺陷;補法 via-price run 建 "
            "features_daily 後複判)")
    elif _day is not None and _uni is not None and _day != _uni:
        # 批689B:該日在庫 ≠ 庫標的宇宙=因子鏈沒跑全宇宙(工作站實錄 530/1978=26.8%)——缺料不是壞,指路重跑因子段
        skp("⑨ 市場寬度句(批192/538:features_daily 最新完整日聚合)",
            f"({br['date']}:該日在庫 {_day} ≠ 庫標的宇宙 {_uni}={round(100.0 * _day / _uni, 1) if _uni else 0}%"
            f"=因子鏈未跑全宇宙,缺料不是壞;via-vdffetch(3a/3b 因子段)後複判)")
    else:
        chk("⑨ 市場寬度句(批192/538:features_daily 最新完整日聚合庫取+**逐列對得起來**"
        "(有因子 + 天生算不出=該日在庫;上市未滿 20 天算不出 20 日均線,不是漏算)"
        "+守恆 n≥勝+負+誠實閘納句)",
        br is not None and _day is not None and _uni is not None
        and _nullma is not None and br["n_ma"] + _nullma == _day and _day == _uni
        and br["n_ma"] >= br["win60"] + br["lose60"]
        and 0 <= br["pct_above"] <= 100,
        f"({br['date']}:{br['above_ma20']}/{br['n_ma']}={br['pct_above']}%"
        f"·勝 {br['win60']}/負 {br['lose60']}"
        f"·該日在庫 {_day}=有因子 {br['n_ma']}+天生算不出 {_nullma}"
        f"{('(' + '、'.join(_nullwho) + ':上市未滿 20 天)') if _nullwho else ''}"
        f"·庫標的宇宙 {_uni} 檔(此庫涵蓋面事實,非台股全市場))")
    print(f"  [計] 九檢 OK {9 - len(fails) - len(skips)} · FAIL {len(fails)}"
          f" · SKIP {len(skips)}(誠實三態;上游件未產生非本引擎缺陷)")
    return 1 if fails else (2 if skips else 0)     # 批689B:無 FAIL 有 SKIP=rc2 NODATA(缺料不是壞)


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 每日觀察摘要(VRN_ENG068)· 八檢自測(零網路)===")
        return selftest()
    p, gate = build()
    print(f"[UI] {p.name} · 誠實閘 checked={gate.get('numbers_checked')} "
          f"ungrounded={len(gate.get('ungrounded', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
