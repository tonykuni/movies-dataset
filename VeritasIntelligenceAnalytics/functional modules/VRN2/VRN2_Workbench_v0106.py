#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN2_Workbench v0105 — 動態前版薄尾(同夾最高前版留著一字不改):操作員 2026-11-02 U/I 需求(渲染後處理 · 不碰前版內部)。

桌機的 v0103 / v0104 是另一條線在桌機上加的尾版(原始碼不在本倉);為了不長九頭龍,本版不指名前版檔名:
啟動時在自己同一夾找版號比自己小的最高 VRN2_Workbench_v0NNN.py 當前版(桌機 = v0104 · 本倉 runtime = v0102),
照前版 render 出頁後只做「後處理」:① 注入一段收尾 CSS(蓋版 · 不改前版字串),② 在 <main> 開頭插一個自包含的 v0105 區塊。
前版頁面其他內容一字不動;前版換版(桌機再加 v010x)本版自動接上,x ≥ 105 時本版讓位(_latest_in 會選更高的)。

操作員需求 → 作法:
  · 面板區 LAYOUT 緊湊 · 必要空行別太大 → .box / .stats / .kv / .sm-* 的 padding / margin 縮小(CSS 蓋版)。
  · 面板字體比 HEADER 略小 → 面板最大字(.stat b 24px)壓到 17px(< 頁首 h1 20px);h2 13px。
  · 有底色的字應白色 → .pill 全系列與 .sm-st 徽章改實底 + 白字。
  · 矩陣格式 / 欄寬自動最佳化 → .matrix table 改 auto 欄寬 · 緊湊 padding · 表頭 sticky。
  · 紅黃綠燈顯示每個資料驗證狀況 → 新「資料驗證狀況」面板:逐收據(原文值核對 · 獨立驗證 · 冪等 · 完成判定 · 市場 ⑥e · 共識 ⑥f ·
    歷史對齊 ⑬b · 增量庫 ⑬ · Combined 共識欄)紅黃綠灰燈 + 一行寫實說明(只讀收據,不重算)。
  · 要有共識資料 → 新「共識資料」面板:引擎 / 網路工具 / 燈 / 抓到幾檔 + 兩家目標價中位數小矩陣;
    ConsensusJoin v0106 快照補位的輪次,ASOF 徽章放最顯眼(紅底白字寫快照日,不冒充本輪)。
動詞同前版:render · logo · --selftest;render(root, out_path, logo, assets_zip) 介面不變。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import csv
import datetime
import html
import importlib.util
import json
import re
import sys
from pathlib import Path

VERSION = "v0105"
DISPLAY_NAME = "VRN2_Workbench"
HERE = Path(__file__).resolve().parent
_MYNUM = 105
_RE_VER = re.compile(r"VRN2_Workbench_v(\d{4})\.py$")


def _prior_path() -> Path:
    cands = []
    for p in HERE.glob("VRN2_Workbench_v[0-9][0-9][0-9][0-9].py"):
        m = _RE_VER.search(p.name)
        if m and int(m.group(1)) < _MYNUM:
            cands.append((int(m.group(1)), p))
    if not cands:
        raise FileNotFoundError("同夾沒有版號 < v%04d 的 VRN2_Workbench 前版(%s)" % (_MYNUM, HERE))
    return sorted(cands)[-1][1]


def _load_prior():
    path = _prior_path()
    spec = importlib.util.spec_from_file_location("vrn2_workbench_prior_dyn", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path.name


PRIOR, PRIOR_NAME = _load_prior()

_CSS = """
<style id="wb105-css">/* VRN2_Workbench v0105:緊湊 · 白字 · 欄寬自動(蓋版 · 前版規則不改) */
main{padding:10px 14px}
.box{padding:10px 12px;margin-bottom:8px}
.stats{gap:8px;margin-bottom:8px}
.stat{padding:8px 10px}
.stat b{font-size:clamp(12px,1vw + 7px,17px)}
h2{font-size:13px;margin:0 0 6px}
h3{margin:6px 0 4px}
.kv{gap:6px}.kv .cell{padding:6px 8px}
.cards{gap:8px}.split{gap:8px}
.sm-hdr{padding-bottom:8px;margin-bottom:8px;gap:12px}
.sm-state{padding:6px 10px;margin-bottom:8px}
.sm-card{padding:10px 12px}
.sm-row>.sm-c{padding:4px 10px}
.sm-row>.sm-c:first-child{padding-top:8px}
.sm-row>.sm-c:last-child{padding-bottom:8px}
.toolbar{padding:5px 0}
.pill{color:#fff;background:var(--am)}
.pill.good{color:#fff}.pill.bad{color:#fff}.pill.gray{color:#fff;background:var(--mut2)}
.sm-st{color:#fff;background:var(--c,var(--mut2));border-color:var(--c,var(--mut2))}
.sm-st .sm-dot{background:#fff}
.matrix table{table-layout:auto;width:auto;min-width:100%;border-collapse:collapse}
.matrix th,.matrix td{padding:3px 8px;white-space:nowrap}
.matrix th{position:sticky;top:0;background:var(--paper2);z-index:2}
td.lampcell{white-space:normal;min-width:120px;max-width:360px}
#wb105 .g{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:4px 14px;font-size:11.5px;line-height:1.45}
#wb105 .g>div{display:flex;gap:7px;align-items:baseline;min-width:0}
#wb105 .g b{flex:none;font-weight:700}
#wb105 .g .d{color:var(--ink2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#wb105 .g>div:hover .d{white-space:normal;overflow-wrap:anywhere}
#wb105 .asof{display:inline-block;font:700 10px "DM Mono",monospace;letter-spacing:.5px;padding:2px 8px;border-radius:3px;background:var(--up);color:#fff;margin-left:8px}
#wb105 table{border-collapse:collapse;font-size:11px;margin-top:4px}
#wb105 table th{background:var(--blue);color:#fff;padding:3px 8px;text-align:left;white-space:nowrap}
#wb105 table td{padding:3px 8px;border-bottom:1px solid var(--soft);white-space:nowrap}
</style>"""


def jread105(p: Path, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


_LAMP_OF = {"完成": "GREEN", "PASS": "GREEN", "OK": "GREEN", "GREEN": "GREEN", "YELLOW": "YELLOW", "RED": "RED", "GRAY": "GRAY",
            "REVIEW": "YELLOW", "REVIEW_OCR": "YELLOW", "FAIL": "RED", "BLOCKED": "RED", "DATA_GAP": "YELLOW"}


def _lamp(d: dict) -> str:
    if not isinstance(d, dict) or not d:
        return "GRAY"
    for k in ("lamp", "verdict", "state", "status"):
        v = str(d.get(k) or "").strip()
        if v:
            return _LAMP_OF.get(v, _LAMP_OF.get(v.split()[0], "YELLOW"))
    return "GRAY"


def _detail(d: dict, *keys) -> str:
    if not isinstance(d, dict):
        return "收據不在"
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v
        if isinstance(v, dict) and v:
            return " · ".join("%s %s" % (a, b) for a, b in list(v.items())[:6])
    return str(d.get("verdict") or d.get("state") or "")


def _combined_consensus(v2: Path) -> tuple:
    """output/VRN2_Combined_latest.csv:(總列數, FACTSET 中位數欄有值列數, YFINANCE 中位數欄有值列數)。讀不了 → (None, 0, 0)。"""
    p = v2 / "output" / "VRN2_Combined_latest.csv"
    if not p.is_file():
        return None, 0, 0
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
    except (OSError, csv.Error, UnicodeError):
        return None, 0, 0
    fs = sum(1 for r in rows if str(r.get("FACTSET_TARGET_PRICE_MEDIAN") or "").strip())
    yf = sum(1 for r in rows if str(r.get("YFINANCE_TARGET_PRICE_MEDIAN") or "").strip())
    return len(rows), fs, yf


def _fmt2(v):
    try:
        return "%.2f" % float(v)
    except (TypeError, ValueError):
        return "—"


def _closeout_steps(v2: Path) -> dict:
    """最新收尾收據的步驟燈 {步驟字首: (燈, 說明)}(⑥e 等市場收據自己沒帶燈時的寫實來源)。"""
    books = sorted(p for p in Path(v2).glob("VRN2_Closeout_v[0-9][0-9][0-9][0-9].json") if ".before_roundall" not in p.name)
    steps = (jread105(books[-1], {}) or {}).get("steps") if books else None
    out = {}
    for s in steps or []:
        key = str(s.get("step", "")).split(" ")[0]
        if key:
            out.setdefault(key, (str(s.get("lamp") or "GRAY"), str(s.get("detail") or "")))
    return out


def verification_rows(v2: Path) -> list:
    """逐收據的 (名稱, 燈, 一行說明) · 只讀,不重算。"""
    cons = jread105(v2 / "consensus" / "VRN2_Consensus_latest.json", {})
    steps = _closeout_steps(v2)
    vv = jread105(v2 / "VRN2_VerbatimVerify_latest.json", {})
    vv_counts = vv.get("counts") or {}
    total, fs_n, yf_n = _combined_consensus(v2)
    snap = cons.get("snapshot_reused") if isinstance(cons.get("snapshot_reused"), dict) else None
    cons_lamp = _lamp(cons)
    cons_note = ("快照補位 ASOF %s · %d 檔(閘未開 · 非本輪抓)" % (snap["asof"], snap.get("codes", 0))) if snap else \
        ("抓到 %d / 缺 %d" % (len(cons.get("codes_got") or []), len(cons.get("codes_missing") or [])) if cons.get("per_code") else str(cons.get("why") or "")[:160])
    comb_lamp = "GRAY" if total is None else ("GREEN" if total and fs_n == total and yf_n == total else ("YELLOW" if (fs_n or yf_n) else "RED"))
    rows = [
        ("原文值核對(VerbatimVerify)", _lamp(vv), " · ".join("%s %s" % (k, v) for k, v in list(vv_counts.items())[:5]) or _detail(vv, "why")),
        ("獨立驗證(IndependentVerifier)", _lamp(jread105(v2 / "VRN2_FailEvidence_latest.json", {})) if (v2 / "VRN2_FailEvidence_latest.json").is_file() else "GRAY",
         _detail(jread105(v2 / "VRN2_FailEvidence_latest.json", {}), "why", "counts")),
        ("冪等(同輸入同輸出)", _lamp(jread105(v2 / "IDEMPOTENCE_latest.json", {})), _detail(jread105(v2 / "IDEMPOTENCE_latest.json", {}), "why") or "見 IDEMPOTENCE_latest.json"),
        ("完成判定", _lamp(jread105(v2 / "VRN2_Completion_latest.json", {})), _detail(jread105(v2 / "VRN2_Completion_latest.json", {}), "why", "verdict")),
        ("市場資料 ⑥e(TWSE / TPEX / Yahoo)",
         (_lamp(jread105(v2 / "market" / "VRN2_Market_latest.json", {})) if "lamp" in jread105(v2 / "market" / "VRN2_Market_latest.json", {}) else (steps.get("⑥e", ("GRAY", ""))[0])),
         _detail(jread105(v2 / "market" / "VRN2_Market_latest.json", {}), "why", "detail") or steps.get("⑥e", ("", "market/VRN2_Market_latest.json"))[1][:200]),
        ("共識 ⑥f(FactSet × Yahoo)", cons_lamp, cons_note),
        ("歷史對齊 ⑬b", _lamp(jread105(v2 / "VRN2_HistoryAlign_latest.json", {})), _detail(jread105(v2 / "VRN2_HistoryAlign_latest.json", {}), "why")),
        ("增量庫 ⑬(DuckDB / Parquet)", _lamp(jread105(v2 / "VRN2_OutputStore_latest.json", {})), _detail(jread105(v2 / "VRN2_OutputStore_latest.json", {}), "why", "totals")),
        ("Combined 共識欄", comb_lamp, ("%s 列 · FactSet 中位數 %s · Yahoo 中位數 %s%s" % (total, fs_n, yf_n, (" · 快照 ASOF " + snap["asof"]) if snap and fs_n else "")) if total is not None else "Combined 冊不在"),
    ]
    return rows


def consensus_block(v2: Path) -> str:
    cons = jread105(v2 / "consensus" / "VRN2_Consensus_latest.json", {})
    per = cons.get("per_code") if isinstance(cons.get("per_code"), dict) else {}
    snap = cons.get("snapshot_reused") if isinstance(cons.get("snapshot_reused"), dict) else None
    e = html.escape
    head = "<h3>共識資料(FactSet × Yahoo 目標價中位數)%s</h3>" % (('<span class="asof">快照 ASOF %s</span>' % e(str(snap["asof"]))) if snap else "")
    meta = '<div class="d" style="font-size:11px;color:var(--mut)">%s</div>' % e(("引擎 %s · 網路工具 %s · " % (Path(str(cons.get("engine") or "—")).name, cons.get("net_tool") or "—")) +
                                                                                 (snap["why"] if snap else str(cons.get("why") or "這輪沒有共識收據")[:220]))
    if not per:
        return head + meta
    rows = []
    for code, c in sorted(per.items())[:40]:
        if not isinstance(c, dict):
            continue
        rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            e(str(code)), e(str(c.get("company_name") or "")[:16]), _fmt2(c.get("factset_target_median")), _fmt2(c.get("yf_target_median")),
            e(str(c.get("factset_analyst_count") or "—")), e(str(c.get("yf_analyst_count") or "—")), e(str(c.get("source_agreement_gate") or ""))))
    table = ('<div class="matrix" style="max-height:34vh;overflow:auto"><table><thead><tr><th>代號</th><th>名稱</th><th>FactSet 中位數</th><th>Yahoo 中位數</th>'
             "<th>FactSet 人數</th><th>Yahoo 人數</th><th>兩源閘</th></tr></thead><tbody>%s</tbody></table></div>" % "".join(rows))
    return head + meta + table


def block_html(v2: Path) -> str:
    e = html.escape
    lamps = "".join('<div><span class="lamp %s"></span><b>%s</b><span class="d" title="%s">%s</span></div>'
                    % (lp, e(nm), e(str(dt)[:400]), e(str(dt)[:200])) for nm, lp, dt in verification_rows(v2))
    return ('\n<section class="box" id="wb105"><h2>資料驗證狀況(紅黃綠燈 · 逐收據)<span class="pill good">Workbench v0105</span></h2>'
            '<div class="g">%s</div>%s</section>\n' % (lamps, consensus_block(v2)))


def augment(page: str, v2: Path) -> str:
    """渲染後處理(純函式 · 可測):CSS 蓋版 + v0105 區塊 + 版本註記。前版頁面其他內容一字不動。"""
    if page.count("</head>") == 1:
        page = page.replace("</head>", _CSS + "\n</head>", 1)
    if page.count("</title>") >= 1:
        page = page.replace("</title>", "</title><!-- VRN2_Workbench %s over %s -->" % (VERSION, PRIOR_NAME.rsplit("_", 1)[-1][:-3]), 1)
    block = block_html(v2)
    if page.count("<main>") == 1:
        page = page.replace("<main>", "<main>" + block, 1)
    elif page.count("</body>") == 1:                                            # 前版版型變了也不失敗:退而求其次放頁尾
        page = page.replace("</body>", block + "</body>", 1)
    return page


def _prior_render(root, out_path, logo, assets_zip):
    """前版 render 依它自己的簽章呼叫(桌機的 v0104 是另一條線寫的 · 不假設跟 v0102 一樣)。"""
    import inspect
    try:
        params = set(inspect.signature(PRIOR.render).parameters)
    except (TypeError, ValueError):
        params = {"root"}
    kwargs = {k: v for k, v in (("out_path", out_path), ("logo", logo), ("assets_zip", assets_zip)) if v is not None and k in params}
    return PRIOR.render(root, **kwargs)


def render(root: Path, out_path: Path | None = None, logo: str | None = None, assets_zip: Path | None = None) -> Path:
    root = Path(root).resolve()
    out = _prior_render(root, out_path, logo, assets_zip)
    v2 = root / "VIA_Reports" / "vrn2"
    page = Path(out).read_text(encoding="utf-8")
    try:
        page = augment(page, v2)
    except Exception as error:  # noqa: BLE001  後處理失敗不毀前版頁(頁照出 · 印原因)
        print("    [U/I] [YELLOW] Workbench v0105 後處理沒做成(前版頁照出):%s: %s" % (type(error).__name__, str(error)[:160]), flush=True)
        return Path(out)
    tmp = Path(out).with_suffix(".v0105.tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(Path(out))
    return Path(out)


# ── 自測(不跑前版 render:前版在桌機是 v0104(原始碼另一條線),只測本版的後處理與鏈)──────────────────────
def _fixture_v2(v2: Path) -> None:
    (v2 / "market").mkdir(parents=True, exist_ok=True)
    (v2 / "consensus").mkdir(parents=True, exist_ok=True)
    (v2 / "output").mkdir(parents=True, exist_ok=True)
    jw = lambda p, d: (v2 / p).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")  # noqa: E731
    jw("VRN2_VerbatimVerify_latest.json", {"verdict": "REVIEW_OCR", "counts": {"PASS": 50, "REVIEW_OCR": 2}})
    jw("IDEMPOTENCE_latest.json", {"lamp": "GREEN", "why": "兩次雜湊一致"})
    jw("VRN2_Completion_latest.json", {"verdict": "完成"})
    jw("market/VRN2_Market_latest.json", {"lamp": "YELLOW", "why": "擷取 YELLOW · 失敗 0(VDF rc 2 PARTIAL)"})
    jw("VRN2_HistoryAlign_latest.json", {"lamp": "GRAY", "why": "無歷史 47"})
    jw("VRN2_OutputStore_latest.json", {"lamp": "GREEN", "totals": {"Combined": 52}})
    jw("consensus/VRN2_Consensus_latest.json", {"lamp": "YELLOW", "why": "快照補位:…", "engine": "ENG_x.py", "net_tool": "SUP_MDL740 · 閘 關",
                                                "snapshot_reused": {"asof": "2026-11-01", "codes": 2, "why": "同意閘未開 · 先用碟上 ASOF 2026-11-01 快照補位(2 檔)"},
                                                "per_code": {"1101": {"company_name": "合成公司0", "factset_target_median": 120.0, "yf_target_median": 110.0, "factset_analyst_count": 5, "yf_analyst_count": 7, "source_agreement_gate": "PASS"},
                                                             "2330": {"company_name": "合成公司1", "factset_target_median": 132.0, "yf_target_median": 123.2, "factset_analyst_count": 6, "yf_analyst_count": 8, "source_agreement_gate": "PASS"}}})
    with (v2 / "output" / "VRN2_Combined_latest.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["TICKER", "FACTSET_TARGET_PRICE_MEDIAN", "YFINANCE_TARGET_PRICE_MEDIAN"])
        w.writerow(["1101", "120.00", "110.00"])
        w.writerow(["2330", "132.00", "123.20"])
        w.writerow(["9999", "", ""])


def selftest() -> int:
    import tempfile
    fails = []

    def chk(label, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", label))
        if not cond:
            fails.append(label)

    pn = int(_RE_VER.search(PRIOR_NAME).group(1))
    chk("① 動態前版:同夾最高前版 %s(版號 < 105)· render / main 都在" % PRIOR_NAME, pn < _MYNUM and callable(getattr(PRIOR, "render", None)) and callable(getattr(PRIOR, "main", None)))
    with tempfile.TemporaryDirectory() as td:
        v2 = Path(td) / "VIA_Reports" / "vrn2"
        _fixture_v2(v2)
        rows = verification_rows(v2)
        by = {n: (lp, dt) for n, lp, dt in rows}
        chk("② 資料驗證燈 9 列 · 冪等綠 · 市場黃 · 歷史灰", len(rows) == 9 and by["冪等(同輸入同輸出)"][0] == "GREEN"
            and by["市場資料 ⑥e(TWSE / TPEX / Yahoo)"][0] == "YELLOW" and by["歷史對齊 ⑬b"][0] == "GRAY")
        chk("③ 共識列:快照補位 ASOF 2026-11-01 寫在燈的說明裡", "ASOF 2026-11-01" in by["共識 ⑥f(FactSet × Yahoo)"][1])
        chk("④ Combined 共識欄列:3 列 · 兩家各 2 有值 → 黃", by["Combined 共識欄"][0] == "YELLOW" and "FactSet 中位數 2" in by["Combined 共識欄"][1])
        page = ('<!DOCTYPE html>\n<html><head><title>VeritasReportNova · VRN Workbench</title>'
                "<style>:root{}</style></head><body><header class=\"vh\"></header><main><section class=\"box\"><h2>報告輸入</h2></section></main></body></html>")
        got = augment(page, v2)
        chk("⑤ CSS 蓋版注入一次(wb105-css)· 白字 / 欄寬自動 / 緊湊規則在", got.count('id="wb105-css"') == 1 and ".pill{color:#fff" in got and "table-layout:auto" in got and ".box{padding:10px 12px;margin-bottom:8px}" in got)
        chk("⑥ v0105 區塊插在 <main> 開頭 · 版本註記接在 </title> 後", got.count('id="wb105"') == 1 and got.index('id="wb105"') < got.index("報告輸入")
            and "<!-- VRN2_Workbench v0105 over v%04d -->" % pn in got)
        chk("⑦ 共識面板:ASOF 徽章 + 兩檔兩家中位數", 'class="asof">快照 ASOF 2026-11-01' in got and "120.00" in got and "123.20" in got and "合成公司1" in got)
        chk("⑧ 燈的符號齊:GREEN / YELLOW / GRAY 圓點都有", 'class="lamp GREEN"' in got and 'class="lamp YELLOW"' in got and 'class="lamp GRAY"' in got)
        nomain = augment("<html><head><title>x</title></head><body><div>y</div></body></html>", v2)
        chk("⑨ 前版版型沒有 <main> 也不失敗(區塊退到頁尾)", nomain.count('id="wb105"') == 1)
        (v2 / "consensus" / "VRN2_Consensus_latest.json").write_text(json.dumps({"lamp": "YELLOW", "why": "VIA 網路工具 DENY(同意閘未開)", "per_code": {}}, ensure_ascii=False), encoding="utf-8")
        got2 = augment(page, v2)
        chk("⑩ 沒共識資料的輪次:面板寫實(DENY 原因)· 不出空矩陣", "DENY" in got2 and got2.count("<tbody>") == 0)
    print("[%s] %s %s 自測 %s(%d 項)" % ("GREEN" if not fails else "RED", DISPLAY_NAME, VERSION, "全過" if not fails else "不過:%s" % "; ".join(fails), 10))
    return 0 if not fails else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    if argv and argv[0] == "logo":
        return PRIOR.main(argv)
    import argparse
    import os
    ap = argparse.ArgumentParser(prog="VRN2_Workbench_v0105")
    ap.add_argument("verb", nargs="?", default="render")
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--logo", default=None)
    a = ap.parse_args(argv)
    if a.verb != "render":
        return PRIOR.main(argv)
    root = Path(a.root) if a.root else (os.environ.get("VIA_ROOT") and Path(os.environ["VIA_ROOT"])) or HERE.parent.parent
    path = render(root, a.out, a.logo)
    print("[GREEN] %s %s(前版 %s)· %s" % (DISPLAY_NAME, VERSION, PRIOR_NAME.rsplit("_", 1)[-1][:-3], path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
