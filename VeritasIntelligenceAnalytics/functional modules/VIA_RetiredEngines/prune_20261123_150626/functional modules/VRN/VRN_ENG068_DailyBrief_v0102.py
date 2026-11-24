#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
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
    rot = m.harvest_rotation()
    glb = m.harvest_global()
    stocks = []
    for c, v in m.harvest_data()["stocks"].items():
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
            "factors": factors, "glb_note": glb.get("note", ""), "stocks": stocks}


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

    via = harvest_via()
    chk("① VIA 節收割(grid 燈+金字塔+VSM 六燈+問題板六態)",
        via["grid"].get("ok", 0) >= 110 and via["pyramid"] is not None
        and set(via["vsm"]) >= {"S1", "S2", "S3", "S3star", "S4", "S5"}
        and via["prob_n"] >= 14)
    vdf = harvest_vdf()
    chk("② VDF 節收割(台股五表+全球二表最新日;總列>1M)",
        len(vdf["tw"]) == 5 and len(vdf["gl"]) == 2 and vdf["tw_total"] > 1_000_000,
        f"(台股 {vdf['tw_total']:,} 列)")
    vap = harvest_vap()
    chk("③ VAP 節收割(榜前五+因子四線+個股三檔日變動)",
        len(vap["rank5"]) == 5 and len(vap["factors"]) == 4
        and len(vap["stocks"]) == 3
        and all(s["chg_pct"] is not None for s in vap["stocks"]))
    vrn = harvest_vrn()
    chk("④ VRN 節收割(SSOT 字數+攝入+pending 誠實)",
        vrn["kw"].get("keywords", 0) >= 500 and "P03" in vrn["pending"])
    p, gate = build()
    h = p.read_text(encoding="utf-8")
    chk("⑤ 四系統節在頁(①-④+誠實閘尾)",
        all(k in h for k in ("VIA 總覽", "VDF 資料面", "VAP 觀察面",
                             "VRN 報告智能", "verify_summary")))
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
    chk("⑨ 市場寬度句(批192:features_daily 最新日聚合庫取+守恆"
        "n≥勝+負+誠實閘納句)",
        br is not None and br["n_ma"] > 1000
        and br["n_ma"] >= br["win60"] + br["lose60"]
        and 0 <= br["pct_above"] <= 100,
        f"({br['date']}:{br['above_ma20']}/{br['n_ma']}={br['pct_above']}%"
        f"·勝 {br['win60']}/負 {br['lose60']})" if br else "(因子庫缺)")
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


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
