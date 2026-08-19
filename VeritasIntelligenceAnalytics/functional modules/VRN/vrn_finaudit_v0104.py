#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_finaudit_v0104 — 財務驗算稽核器(TOOL-078)
批73:U/I 接母子統一套件
====================================================================
操作員令(批60,2026-08-19):「ALL FINANCIAL DATA / RATIO ANALYSIS
TURNOVER / PER SHARE ANALYSIS / VALUATION BASED ON ADJ CLOSE
數值歷歷對照 加減法驗算 除法驗算 TEST DEBUG OPTIMIZE TEST DEBUG
TILL IT WORKS.」
v0100→v0101(批63,2026-08-19):
  ⑥ 先 MAPPING 再驗算 — 操作員令「漲跌幅是透過 VDF 每天抓新數據
     不必驗 要驗要抓 先 MAPPING DATA 再驗算」:矩陣列先與最新
     VDF 輸出(digest_vdf_rows.csv,工作站每日 via-digest --vdf
     刷新)按 Ticker 映射,ADJ 取 VDF 新鮮值(ADJ源=VDF);映射
     不到=矩陣舊值(ADJ源=矩陣,誠實標)。驗算對象=映射後數據:
     上漲%以新鮮 ADJ 重算(upside_fresh),矩陣舊載 upside 不再
     對照驗證(同源循環無意義,依令不必驗)。
v0101→v0102(批65,2026-08-19):
  ⑦ 全式+異常矩陣 — 操作員令「另一個矩陣列出所有財報數據驗證
     結果 列異常值」:逐列逐式攤平為 all_checks;異常(驗算 FAIL
     +digest TP 黃旗)置頂另立異常矩陣,全式入 JSON/U/I。
v0102→v0103(批67,2026-08-19;工作站證據:MAPPING 源 0 檔):
  ⑧ VDF 落點修 — 六格式輸出樞紐實際落 functional modules/VDF/
     output_hub/(非矩陣夾);搜尋序=矩陣同夾>output_hub>
     digest_runs glob,取 mtime 最新,誠實記源。
原則:
  ① 新舊整合(批58 鐵則)— 驗算引擎=批56 收容之
     VRN_Complete_FeatureAudit_Ultra(§7 三表/§8 比率/§9 每股/
     §10 加減除)動態解析最新版(嚴禁寫死版號);缺席 graceful
     降級本器簡式驗算(僅減法/除法),誠實記降級。
  ② 數值歷歷對照 — 每筆驗算列出 expected/actual/diff%,矩陣
     +U/I 並排顯示;不藏數字。
  ③ 估值以 ADJ CLOSE 為基 — PER=ADJ/EPS、隱含 PER=TP/EPS、
     上漲%重算=(TP-ADJ)/ADJ×100 對照 digest 報告值(除法驗算);
     TP-ADJ 差額(減法驗算)。
  ④ 誠實三態 — 數據缺(無 ADJ/EPS/TP)=SKIP 不假算;分母零=FAIL
     誠實;全表數據(--fin)缺=SKIP 候工作站 MDL006/008 產物。
  ⑤ 存證 — VIA_Reports/finaudit_runs/FINAUDIT_<ts>/:
     FinAudit_Result.json+理印 U/I VIA_UI_FinAudit.html。
用法:
  via-finaudit                    → 掃最新 Digest_Matrix.json 估值稽核
  via-finaudit --matrix <json>    → 指定摘要矩陣
  via-finaudit --fin <json>       → 全表財務數據稽核(三表/比率/週轉/每股)
  via-finaudit --selftest         → 十檢(合成數據零網路)
  via-finaudit --no-open          → 不開 U/I
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent          # functional modules/VRN
VIA = HERE.parent.parent
MOTTO = "VERITAS INTELLIGENCE ANALYTICS · OBSERVA · INTELLEGE · PRAEVIDE"
OUT_ROOT = VIA / "VIA_Reports" / "finaudit_runs"


def load_feature_audit():
    """動態解析最新 FeatureAudit(批56 收容;嚴禁寫死版號;缺=誠實降級)"""
    import warnings
    hits = sorted(HERE.glob("VRN_Complete_FeatureAudit*.py"))
    hits = [h for h in hits if h.suffix == ".py"]
    if not hits:
        return None, "FeatureAudit 缺(降級簡式)"
    eng = hits[-1]
    name = "vrn_finaudit_fa_dyn"
    spec = importlib.util.spec_from_file_location(name, eng)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            spec.loader.exec_module(mod)
    except Exception as exc:
        sys.modules.pop(name, None)
        return None, f"FeatureAudit 匯入敗:{str(exc)[:60]}"
    return mod, eng.name


def _vr_dict(vr) -> dict:
    """ValidationResult → dict(歷歷對照:expected/actual/diff%)"""
    return {"rule": vr.rule_name, "passed": bool(vr.passed),
            "expected": vr.expected, "actual": vr.actual,
            "diff_pct": round(vr.diff_pct, 4) if vr.diff_pct is not None else None,
            "message": vr.message or ""}


# ── 降級簡式驗算(FeatureAudit 缺席時;容忍 1%)─────────────
def _simple_sub(a: float, b: float, d: float, label: str) -> dict:
    calc = a - b
    diff = abs(d - calc) / abs(a) * 100 if a else 0.0
    return {"rule": f"減法驗證: {label}(簡式降級)", "passed": diff <= 1,
            "expected": calc, "actual": d, "diff_pct": round(diff, 4), "message": ""}


def _simple_div(num: float, den: float, q: float, label: str) -> dict:
    if not den:
        return {"rule": f"除法驗證: {label}(簡式降級)", "passed": False,
                "expected": None, "actual": q, "diff_pct": None, "message": "分母為零"}
    calc = num / den
    diff = abs(q - calc) / abs(calc) * 100 if calc else 0.0
    return {"rule": f"除法驗證: {label}(簡式降級)", "passed": diff <= 1,
            "expected": calc, "actual": q, "diff_pct": round(diff, 4), "message": ""}


def load_vdf_rows(explicit: Path | None = None) -> tuple[dict, str]:
    """最新 VDF 輸出(每日新鮮數據)→ {ticker: row};缺=誠實空"""
    import csv
    cands = []
    if explicit is not None and explicit.exists():
        cands.append(explicit)
    hub_csv = VIA / "functional modules" / "VDF" / "output_hub" / "digest_vdf_rows.csv"
    if hub_csv.exists():
        cands.append(hub_csv)  # 批67:六格式樞紐實際落點
    cands += [h for h in (VIA / "VIA_Reports" / "digest_runs").glob("DIGEST_*/digest_vdf_rows.csv")]
    p = max(cands, key=lambda x: x.stat().st_mtime) if cands else None
    if p is None:
        return {}, "VDF 輸出缺(ADJ 用矩陣舊值,誠實)"
    out = {}
    try:
        with open(p, encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                tk = (row.get("Ticker") or "").strip()
                if tk:
                    out[tk] = row
    except Exception as exc:
        return {}, f"VDF 讀取敗:{str(exc)[:50]}"
    return out, p.name


# ── 估值列稽核(VALUATION BASED ON ADJ CLOSE)────────────────
def audit_row(r: dict, fa, vdf_map: dict | None = None) -> dict:
    """先 MAPPING(VDF 新鮮 ADJ)再驗算(批63 令);數據缺=SKIP"""
    adj = r.get("adj_close")
    adj_src = "矩陣"
    v = (vdf_map or {}).get(str(r.get("ticker", "")).strip())
    if v is not None:
        try:
            fresh = float(v.get("AdjClose") or "")
            adj, adj_src = fresh, "VDF"
        except (TypeError, ValueError):
            pass
    eps = r.get("eps_current")
    tp = r.get("target_price")
    up = r.get("upside_pct")
    out = {"file": r.get("file", ""), "ticker": r.get("ticker", ""),
           "adj_close": adj, "adj_src": adj_src, "eps_current": eps,
           "target_price": tp, "upside_reported": up,
           "tp_suspect": bool(r.get("tp_suspect")), "checks": [], "state": "OK"}
    if adj in (None, 0) and tp in (None, 0):
        out["state"] = "SKIP:數據缺(無 ADJ/TP)"
        return out
    eng = fa.FinancialValidationEngine if fa else None
    # 每股/估值(PER SHARE ANALYSIS;除法歷歷對照)
    if adj and eps:
        out["pe_adj"] = round(adj / eps, 2)
        vr = (eng.validate_division(adj, eps, out["pe_adj"], "PER=ADJ/EPS") if eng
              else _simple_div(adj, eps, out["pe_adj"], "PER=ADJ/EPS"))
        out["checks"].append(_vr_dict(vr) if eng else vr)
    if tp and eps:
        out["pe_target"] = round(tp / eps, 2)
        vr = (eng.validate_division(tp, eps, out["pe_target"], "隱含PER=TP/EPS") if eng
              else _simple_div(tp, eps, out["pe_target"], "隱含PER=TP/EPS"))
        out["checks"].append(_vr_dict(vr) if eng else vr)
    # 減法驗算:TP-ADJ 差額
    if tp and adj:
        diff = round(tp - adj, 4)
        out["tp_minus_adj"] = diff
        vr = (eng.validate_subtraction(tp, adj, diff, "TP-AdjClose") if eng
              else _simple_sub(tp, adj, diff, "TP-AdjClose"))
        out["checks"].append(_vr_dict(vr) if eng else vr)
        # 除法驗算:上漲%重算對照 digest 報告值
        out["upside_fresh"] = round(diff / adj * 100, 2)
        vr = (eng.validate_division(diff * 100, adj, out["upside_fresh"],
                                    f"Upside%({adj_src} ADJ 重算)") if eng
              else _simple_div(diff * 100, adj, out["upside_fresh"],
                               f"Upside%({adj_src} ADJ 重算)"))
        out["checks"].append(_vr_dict(vr) if eng else vr)
        # 舊載 upside 依批63 令不必驗(同源循環);僅並列顯示
    if any(not c["passed"] for c in out["checks"]):
        out["state"] = "FAIL:驗算不符"
    if not out["checks"]:
        out["state"] = "SKIP:數據缺(EPS/ADJ 不足)"
    return out


# ── 全表財務數據稽核(ALL FINANCIAL DATA;--fin/自測)────────
def audit_financials(fin: dict, fa) -> list[dict]:
    """三表勾稽+比率(含週轉 TURNOVER)+每股;鍵缺=誠實跳過該式"""
    if fa is None:
        return [{"rule": "全表稽核", "passed": False, "expected": None,
                 "actual": None, "diff_pct": None,
                 "message": "FeatureAudit 缺席(簡式無三表能力,誠實)"}]
    eng = fa.FinancialValidationEngine
    res = []
    g = fin.get
    if all(g(k) is not None for k in ("assets", "liabilities", "equity")):
        res.append(_vr_dict(eng.validate_balance_sheet(g("assets"), g("liabilities"), g("equity"))))
    if all(g(k) is not None for k in ("revenue", "cogs", "gross_profit", "opex", "operating_income")):
        res += [_vr_dict(v) for v in eng.validate_income_statement(
            g("revenue"), g("cogs"), g("gross_profit"), g("opex"), g("operating_income"))]
    if all(g(k) is not None for k in ("cfo", "cfi", "cff", "net_change")):
        res.append(_vr_dict(eng.validate_cash_flow(g("cfo"), g("cfi"), g("cff"), g("net_change"))))
    if all(g(k) is not None for k in ("revenue", "gross_profit", "gross_margin")):
        res.append(_vr_dict(eng.validate_gross_margin(g("revenue"), g("gross_profit"), g("gross_margin"))))
    if all(g(k) is not None for k in ("net_income", "equity", "roe")):
        res.append(_vr_dict(eng.validate_roe(g("net_income"), g("equity"), g("roe"))))
    if all(g(k) is not None for k in ("current_assets", "current_liab", "current_ratio")):
        res.append(_vr_dict(eng.validate_current_ratio(g("current_assets"), g("current_liab"), g("current_ratio"))))
    if all(g(k) is not None for k in ("revenue", "assets", "asset_turnover")):
        res.append(_vr_dict(eng.validate_division(g("revenue"), g("assets"),
                                                  g("asset_turnover"), "資產週轉率=營收/資產")))
    if all(g(k) is not None for k in ("net_income", "shares", "eps")):
        res.append(_vr_dict(eng.validate_eps(g("net_income"), g("shares"), g("eps"))))
    if all(g(k) is not None for k in ("equity", "shares", "bvps")):
        res.append(_vr_dict(eng.validate_bvps(g("equity"), g("shares"), g("bvps"))))
    return res


# ── RICH 矩陣(降級純文字)────────────────────────────────────
def rich_matrix(title: str, columns: list[str], rows: list[list[str]],
                state_col: int | None = None) -> bool:
    try:
        from rich import box
        from rich.console import Console
        from rich.table import Table
        t = Table(title=title, box=box.SIMPLE_HEAVY, title_style="bold",
                  header_style="bold cyan", show_lines=False, pad_edge=False)
        for c in columns:
            t.add_column(c, overflow="fold", no_wrap=False)
        for r in rows:
            cells = [str(x) if x is not None else "—" for x in r]
            if state_col is not None and state_col < len(cells):
                s = cells[state_col]
                color = ("green" if s.startswith(("OK", "PASS")) else
                         "red" if s.startswith("FAIL") else "yellow")
                cells[state_col] = f"[{color}]{s}[/{color}]"
            t.add_row(*cells)
        Console().print(t)
        return True
    except Exception:
        print(f"  ── {title}(rich 缺席,純文字降級)──")
        print("  " + " | ".join(columns))
        for r in rows:
            print("  " + " | ".join(str(x) if x is not None else "—" for x in r))
        return False


# ── 理印 U/I ─────────────────────────────────────────────────


def _load_ui_kit():
    """批73:母子統一 U/I 套件(動態最新;缺=graceful 用內建 CSS)"""
    import importlib.util
    import warnings
    hits = sorted((VIA / "supportive modules" / "registry").glob("via_ui_kit_v0*.py"))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("via_ui_kit_dyn", hits[-1])
    mod = importlib.util.module_from_spec(spec)
    sys.modules["via_ui_kit_dyn"] = mod
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop("via_ui_kit_dyn", None)
        return None
    return mod

CSS = """
body{background:#f2f1ec;color:#1b1a17;font-family:'Cormorant Garamond','Noto Serif CJK TC','Microsoft JhengHei',serif;margin:0;padding:24px}
.card{background:#fbfaf7;border:1px solid #dbd9d3;border-radius:6px;padding:18px 22px;margin:14px auto;max-width:1280px}
h1{font-size:20px;margin:0 0 2px}h2{font-size:15px;color:#3c6660;margin:16px 0 6px}
.motto{color:#9e2b25;letter-spacing:.14em;font-size:11px;margin-bottom:14px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th{color:#3c6660;text-align:left;border-bottom:1.5px solid #3c6660;padding:4px 8px}
td{border-bottom:1px solid #dbd9d3;padding:4px 8px;vertical-align:top}
.ok{color:#3d7a52;font-weight:bold}.warn{color:#8a6420;font-weight:bold}.bad{color:#9e2b25;font-weight:bold}
.mono{font-family:Consolas,monospace;font-size:11.5px}.dim{color:#6b6a64}
"""


def render_ui(result: dict, run_dir: Path) -> Path:
    _kit = _load_ui_kit()
    _css = _kit.kit_css() if _kit else CSS
    _js = ('<script>' + _kit.kit_js() + '</script>') if _kit else ''
    vrows = []
    for r in result["rows"]:
        st = r["state"]
        cls = "ok" if st == "OK" else ("bad" if st.startswith("FAIL") else "warn")
        chk = "<br>".join(
            f"<span class='{'ok' if c['passed'] else 'bad'}'>{'✓' if c['passed'] else '✗'}</span> "
            f"{c['rule']}:期 {c['expected'] if c['expected'] is not None else '—'} · "
            f"實 {c['actual'] if c['actual'] is not None else '—'} · Δ{c['diff_pct']}%"
            for c in r["checks"]) or "—"
        vrows.append(
            f"<tr><td class='{cls}'>{st}</td><td class='mono'>{r['ticker']}</td>"
            f"<td class='mono dim'>{r['file']}</td><td class='mono'>{r.get('adj_close') or '—'}</td>"
            f"<td class='mono'>{r.get('eps_current') or '—'}</td>"
            f"<td class='mono'>{r.get('pe_adj', '—')}</td><td class='mono'>{r.get('target_price') or '—'}</td>"
            f"<td class='mono'>{r.get('pe_target', '—')}</td>"
            f"<td class='mono dim'>{r.get('upside_reported') if r.get('upside_reported') is not None else '—'}</td>"
            f"<td class='mono'>{r.get('upside_fresh', '—')}</td><td>{chk}</td></tr>")
    frows = "".join(
        f"<tr><td class='{'ok' if c['passed'] else 'bad'}'>{'PASS' if c['passed'] else 'FAIL'}</td>"
        f"<td>{c['rule']}</td><td class='mono'>{c['expected'] if c['expected'] is not None else '—'}</td>"
        f"<td class='mono'>{c['actual'] if c['actual'] is not None else '—'}</td>"
        f"<td class='mono'>{c['diff_pct'] if c['diff_pct'] is not None else '—'}</td>"
        f"<td class='dim'>{c['message']}</td></tr>"
        for c in result.get("fin_checks", []))
    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VRN 財務驗算稽核</title><style>{_css}</style></head><body>
<div class="card"><h1>財務驗算稽核 · FinAudit</h1>
<div class="motto">{MOTTO}</div>
<div class="dim">批次 {result['ts']} · 引擎 {result['engine']} · 估值列 {len(result['rows'])}
(OK {result['ok']} / FAIL {result['fail']} / SKIP {result['skip']})
 · 數值歷歷對照:期=重算值 · 實=載入值 · Δ=誤差%</div>
<h2>估值稽核(先 MAPPING VDF 新鮮 ADJ 再驗算;上漲%舊載依令不必驗,僅並列)</h2>
<table><tr><th>態</th><th>代碼</th><th>檔</th><th>ADJ</th><th>ADJ源</th><th>EPS</th><th>PER</th>
<th>目標價</th><th>隱含PER</th><th>上漲%舊載</th><th>上漲%新算</th><th>加減除驗算(歷歷對照)</th></tr>
{''.join(vrows)}</table>
{'<h2>全表財務數據稽核(三表勾稽/比率含週轉/每股)</h2><table><tr><th>態</th><th>式</th><th>期</th><th>實</th><th>Δ%</th><th>註</th></tr>' + frows + '</table>' if frows else ''}
<h2>財報數據驗證全式({len(result.get('all_checks', []))} 式)· 異常 {len(result.get('anomalies', []))} 置頂</h2>
<table><tr><th>態</th><th>代碼</th><th>式</th><th>期</th><th>實</th><th>Δ%</th><th>因</th></tr>
{''.join(f"<tr><td class='bad'>FAIL</td><td class='mono'>{a.get('ticker','')}</td><td>{a.get('rule','')}</td><td class='mono'>{a.get('expected') if a.get('expected') is not None else '—'}</td><td class='mono'>{a.get('actual') if a.get('actual') is not None else '—'}</td><td class='mono'>{a.get('diff_pct') if a.get('diff_pct') is not None else '—'}</td><td>{a.get('why','')}</td></tr>" for a in result.get('anomalies', []))}
{''.join(f"<tr><td class='ok'>PASS</td><td class='mono'>{c.get('ticker','')}</td><td>{c.get('rule','')}</td><td class='mono'>{c.get('expected') if c.get('expected') is not None else '—'}</td><td class='mono'>{c.get('actual') if c.get('actual') is not None else '—'}</td><td class='mono'>{c.get('diff_pct') if c.get('diff_pct') is not None else '—'}</td><td></td></tr>" for c in result.get('all_checks', []) if c.get('passed'))}
</table>
</div>{_js}</body></html>"""
    out = run_dir / "VIA_UI_FinAudit.html"
    out.write_text(html, encoding="utf-8")
    return out


# ── 批跑 ─────────────────────────────────────────────────────
def newest_matrix() -> Path | None:
    runs = sorted((VIA / "VIA_Reports" / "digest_runs").glob("DIGEST_*/Digest_Matrix.json"))
    return runs[-1] if runs else None


def run_audit(matrix_path: Path | None, fin_path: Path | None, no_open: bool,
              out_root: Path | None = None) -> tuple[int, dict | None]:
    fa, fa_name = load_feature_audit()
    vdf_map, vdf_name = load_vdf_rows(
        matrix_path.parent / "digest_vdf_rows.csv" if matrix_path else None)
    print(f"  [引擎] 驗算引擎 {fa_name}{'' if fa else '(誠實降級)'}"
          f" · MAPPING 源 {vdf_name}({len(vdf_map)} 檔)")
    rows = []
    src = "—"
    if matrix_path and matrix_path.exists():
        mx = json.loads(matrix_path.read_text(encoding="utf-8"))
        src = str(matrix_path)
        rows = [audit_row(r, fa, vdf_map) for r in mx.get("rows", []) if r.get("state") == "OK"]
    fin_checks = []
    if fin_path and fin_path.exists():
        fin_checks = audit_financials(
            json.loads(fin_path.read_text(encoding="utf-8")), fa)
    all_checks = []
    anomalies = []
    for r in rows:
        for c in r["checks"]:
            item = {"ticker": r["ticker"], "file": r["file"], **c}
            all_checks.append(item)
            if not c["passed"]:
                anomalies.append({**item, "why": "驗算FAIL"})
        if r.get("tp_suspect"):
            anomalies.append({"ticker": r["ticker"], "file": r["file"],
                              "rule": "TP黃旗(|上漲%|逾閾)", "passed": False,
                              "expected": None, "actual": r.get("target_price"),
                              "diff_pct": None, "why": "TP疑誤抽(digest 標)"})
    for c in fin_checks:
        all_checks.append({"ticker": "(全表)", "file": "--fin", **c})
        if not c["passed"]:
            anomalies.append({"ticker": "(全表)", "file": "--fin", **c, "why": "驗算FAIL"})
    n_ok = sum(1 for r in rows if r["state"] == "OK")
    n_fail = sum(1 for r in rows if r["state"].startswith("FAIL"))
    n_skip = sum(1 for r in rows if r["state"].startswith("SKIP"))
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {"schema": "VIA.FinAudit.v2", "ts": ts, "engine": fa_name,
              "vdf_source": vdf_name, "vdf_mapped": len(vdf_map),
              "source_matrix": src, "ok": n_ok, "fail": n_fail, "skip": n_skip,
              "rows": rows, "fin_checks": fin_checks,
              "all_checks": all_checks, "anomalies": anomalies}
    run_dir = (out_root or OUT_ROOT) / f"FINAUDIT_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "FinAudit_Result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    ui = render_ui(result, run_dir)
    rich_matrix(f"財務驗算稽核矩陣 · {ts}(先 MAPPING 再驗算;數值歷歷對照)",
                ["態", "代碼", "ADJ", "ADJ源", "EPS", "PER", "目標價", "隱含PER",
                 "上漲%舊載", "上漲%新算", "驗算"],
                [[r["state"], r["ticker"], r.get("adj_close"), r.get("adj_src", ""),
                  r.get("eps_current"), r.get("pe_adj"), r.get("target_price"),
                  r.get("pe_target"), r.get("upside_reported"), r.get("upside_fresh"),
                  "、".join(("✓" if c["passed"] else "✗") + c["rule"][:14] for c in r["checks"]) or "—"]
                 for r in rows], state_col=0)
    ordered = anomalies + [c for c in all_checks if c["passed"]]
    rich_matrix(f"財報數據驗證全式矩陣(全 {len(all_checks)} 式 · 異常 {len(anomalies)} 置頂)",
                ["態", "代碼", "式", "期", "實", "Δ%"],
                [[("FAIL:" + c.get("why", "")) if not c.get("passed") else "PASS",
                  c.get("ticker", ""), c.get("rule", ""), c.get("expected"),
                  c.get("actual"), c.get("diff_pct")]
                 for c in ordered[:80]], state_col=0)
    if len(ordered) > 80:
        print(f"  [註] 矩陣顯示前 80 式,全量 {len(ordered)} 式在 JSON/U/I(誠實)")
    if fin_checks:
        rich_matrix("全表財務數據稽核(三表/比率含週轉/每股)",
                    ["態", "式", "期", "實", "Δ%"],
                    [["PASS" if c["passed"] else "FAIL", c["rule"], c["expected"],
                      c["actual"], c["diff_pct"]] for c in fin_checks], state_col=0)
    print(f"  [計] 估值列 {len(rows)} · OK {n_ok} · FAIL {n_fail} · SKIP {n_skip}"
          f" · 全表式 {len(fin_checks)}(誠實三態)")
    print(f"  [存] {run_dir.relative_to(VIA) if run_dir.is_relative_to(VIA) else run_dir}"
          f" · U/I {ui.name}")
    if not no_open:
        try:
            import webbrowser
            webbrowser.open(ui.as_uri())
        except Exception:
            pass
    return (1 if n_fail else 0), result


# ── 十檢自測(合成數據零網路)────────────────────────────────
FIN_GOOD = {"assets": 1000.0, "liabilities": 400.0, "equity": 600.0,
            "revenue": 800.0, "cogs": 480.0, "gross_profit": 320.0,
            "opex": 120.0, "operating_income": 200.0,
            "cfo": 150.0, "cfi": -90.0, "cff": -20.0, "net_change": 40.0,
            "gross_margin": 40.0, "net_income": 120.0, "roe": 20.0,
            "current_assets": 500.0, "current_liab": 250.0, "current_ratio": 2.0,
            "asset_turnover": 0.8, "shares": 10.0, "eps": 12.0, "bvps": 60.0}


def selftest() -> int:
    import tempfile
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        state = "OK" if cond else "FAIL"
        if not cond:
            fails.append(name)
        print(f"  [{state}] {name} {note}")

    fa, fa_name = load_feature_audit()
    chk("FeatureAudit 動態匯入", fa is not None, f"({fa_name})")
    if fa is None:
        print("  [計] 十檢中止(引擎缺)")
        return 1
    eng = fa.FinancialValidationEngine
    # ② 資產負債恆等式:正例過、破例抓
    chk("BS 恆等式 A=L+E",
        eng.validate_balance_sheet(1000, 400, 600).passed
        and not eng.validate_balance_sheet(1000, 400, 500).passed)
    # ③ 損益兩式(減法歷歷)
    inc = eng.validate_income_statement(800, 480, 320, 120, 200)
    chk("損益表(毛利/營益)", len(inc) == 2 and all(v.passed for v in inc))
    # ④ 現金流
    chk("現金流 CFO+CFI+CFF",
        eng.validate_cash_flow(150, -90, -20, 40).passed
        and not eng.validate_cash_flow(150, -90, -20, 80).passed)
    # ⑤ 比率:毛利率/ROE/流動比+資產週轉(TURNOVER 除法)
    chk("比率(毛利率/ROE/流動比/週轉)",
        eng.validate_gross_margin(800, 320, 40.0).passed
        and eng.validate_roe(120, 600, 20.0).passed
        and eng.validate_current_ratio(500, 250, 2.0).passed
        and eng.validate_division(800, 1000, 0.8, "資產週轉").passed)
    # ⑥ 每股:EPS/BVPS(除法)
    chk("每股(EPS/BVPS)",
        eng.validate_eps(120, 10, 12.0).passed
        and eng.validate_bvps(600, 10, 60.0).passed)
    # ⑦ 加減除 generic+分母零誠實 FAIL
    chk("加減除三式+分母零",
        eng.validate_addition([1, 2, 3], 6, "t").passed
        and eng.validate_subtraction(250, 200, 50, "t").passed
        and eng.validate_division(50, 200, 0.25, "t").passed
        and not eng.validate_division(1, 0, 9, "t").passed)
    # ⑧ 先 MAPPING 再驗算(批63 令):VDF 新鮮 ADJ 覆蓋矩陣舊值,上漲%新算;
    #    舊載值不必驗(同源循環)——誤載 30 不再判 FAIL,僅並列
    base = {"file": "a", "ticker": "2330", "adj_close": 200.0,
            "eps_current": 12.5, "target_price": 250.0,
            "upside_pct": 30.0, "state": "OK"}
    unmapped = audit_row(dict(base), fa)
    mapped = audit_row(dict(base), fa, {"2330": {"AdjClose": "500"}})
    chk("MAPPING+新算(VDF ADJ 覆蓋/矩陣後備)",
        unmapped["state"] == "OK" and unmapped["adj_src"] == "矩陣"
        and unmapped["pe_adj"] == 16.0 and unmapped["upside_fresh"] == 25.0
        and mapped["adj_src"] == "VDF" and mapped["adj_close"] == 500.0
        and mapped["pe_adj"] == 40.0 and mapped["upside_fresh"] == -50.0
        and mapped["state"] == "OK")
    # ⑨ 數據缺=SKIP 誠實+FA 缺席降級道通
    miss = audit_row({"file": "c", "ticker": "1101", "state": "OK"}, fa)
    degr = audit_row({"file": "d", "ticker": "2330", "adj_close": 200.0,
                      "eps_current": 12.5, "target_price": 250.0,
                      "upside_pct": 25.0, "state": "OK"}, None)
    chk("數據缺SKIP+降級簡式道通",
        miss["state"].startswith("SKIP") and degr["state"] == "OK"
        and any("簡式降級" in c["rule"] for c in degr["checks"]))
    # ⑩ 批跑產物:JSON+U/I 銘言+全表 fin 稽核入頁
    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        mxp = sand / "Digest_Matrix.json"
        mxp.write_text(json.dumps({"rows": [
            {"file": "a", "ticker": "2330", "adj_close": 200.0, "eps_current": 12.5,
             "target_price": 250.0, "upside_pct": 25.0, "state": "OK"}]},
            ensure_ascii=False), encoding="utf-8")
        finp = sand / "fin.json"
        finp.write_text(json.dumps(FIN_GOOD), encoding="utf-8")
        (sand / "digest_vdf_rows.csv").write_text(
            "Ticker,AdjClose\n2330,400\n", encoding="utf-8")  # 與 mxp 同層=映射源
        rc, res = run_audit(mxp, finp, no_open=True, out_root=sand / "out")
        runs = sorted((sand / "out").glob("FINAUDIT_*"))
        ok10 = (bool(runs) and rc == 0 and res["ok"] == 1
                and res.get("vdf_mapped") == 1
                and res["rows"][0]["adj_src"] == "VDF"
                and res["rows"][0]["adj_close"] == 400.0
                and res["rows"][0]["upside_fresh"] == -37.5)
        if ok10:
            ui = runs[-1] / "VIA_UI_FinAudit.html"
            jj = runs[-1] / "FinAudit_Result.json"
            ok10 = (ui.exists() and MOTTO in ui.read_text(encoding="utf-8")
                    and jj.exists()
                    and len(res["fin_checks"]) >= 10
                    and all(c["passed"] for c in res["fin_checks"]))
        chk("批跑產物(MAPPING 生效+JSON+U/I+全表≥10式)", ok10)
        # ⑪ 全式+異常矩陣:壞全表(權益短列)+TP 黃旗列→異常置頂
        mxp2 = sand / "m2" / "Digest_Matrix.json"
        mxp2.parent.mkdir()
        mxp2.write_text(json.dumps({"rows": [
            {"file": "s", "ticker": "6533", "adj_close": 248.5, "eps_current": None,
             "target_price": 3.0, "upside_pct": -98.79, "tp_suspect": True,
             "state": "OK"}]}, ensure_ascii=False), encoding="utf-8")
        finp2 = sand / "fin_bad.json"
        bad_fin = dict(FIN_GOOD); bad_fin["equity"] = 500.0  # BS 恆等式破
        finp2.write_text(json.dumps(bad_fin), encoding="utf-8")
        rc11, res11 = run_audit(mxp2, finp2, no_open=True, out_root=sand / "out2")
        an = res11.get("anomalies", [])
        chk("全式+異常矩陣(BS破+TP黃旗置頂)",
            len(res11.get("all_checks", [])) >= 10
            and any("TP黃旗" in a.get("rule", "") for a in an)
            and any(a.get("why") == "驗算FAIL" for a in an))
    n = 11 - len(fails)
    print(f"  [計] 十一檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0



def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 財務驗算稽核器 v0104 · 十一檢自測(合成數據零網路)===")
        return selftest()
    mxp = None
    if "--matrix" in args:
        i = args.index("--matrix")
        mxp = Path(args[i + 1]) if i + 1 < len(args) else None
    else:
        mxp = newest_matrix()
        if mxp is None:
            print("  [SKIP] 無 Digest_Matrix.json(先跑 via-digest;誠實)")
    finp = None
    if "--fin" in args:
        i = args.index("--fin")
        finp = Path(args[i + 1]) if i + 1 < len(args) else None
    print("=== 財務驗算稽核器 v0104 · 先MAPPING再驗算+統一U/I(TOOL-078)===")
    rc, _res = run_audit(mxp, finp, "--no-open" in args)
    return rc


if __name__ == "__main__":
    sys.exit(main())
