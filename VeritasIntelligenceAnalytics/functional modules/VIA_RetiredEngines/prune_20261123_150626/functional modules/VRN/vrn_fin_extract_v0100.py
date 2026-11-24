#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_fin_extract_v0100 — 財報頁年度分析擷取器(TOOL-082)
====================================================================
操作員令(批69,2026-08-19):「擷取財報頁有三大報表 比率分析
每股分析 評價分析 年度分析擷取表格」+整份跨平台同義字/年度
REGEX/公式核定貼文(轉錄於 knowledge/VRN_AnnualExtract_SSOT_v0100
.json,79 科目六板塊)。
原則:
  ① 冊為 SSOT — 科目同義字(MOPS/YFinance/10-K)、年度 REGEX
     (西元/民國/FY/'縮寫/季度)、公式悉出自操作員核定冊;引擎
     零寫死零發明。
  ② 擷取法 — 逐行掃描:年欄=同行 ≥2 個年度 token;科目行=同義
     字最長優先命中(MOPS「合計」優先於明細,冊內序即優先序);
     數字=千分位+括號負數;行內數字依序對齊年欄。
  ③ 閉環 — --fin-out 將擷取值映射 finaudit 全表稽核鍵(assets/
     liabilities/equity/revenue/…),via-finaudit --fin 接手三表
     勾稽+比率+每股加減除驗算(批60 鏈完成:擷取→映射→驗算)。
  ④ 誠實三態 — 科目未中=留空不猜;年欄缺=以出現序 Y1/Y2 標註;
     民國年自動 +1911 換算西元並記 src。
用法:
  via-finx --file <財報頁txt> [--fin-out <fin.json>] [--year <西元年>]
  via-finx --selftest          → 十檢(合成 fixture 零網路)
  via-finx --no-open           → 不開 U/I
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent          # functional modules/VRN
VIA = HERE.parent.parent
SSOT_PATH = HERE / "knowledge" / "VRN_AnnualExtract_SSOT_v0100.json"
MOTTO = "VERITAS INTELLIGENCE ANALYTICS · OBSERVA · INTELLEGE · PRAEVIDE"
OUT_ROOT = VIA / "VIA_Reports" / "finx_runs"

NUM_RX = re.compile(r"\(?-?[\d,]+(?:\.\d+)?\)?%?")


def load_ssot() -> dict:
    return json.loads(SSOT_PATH.read_text(encoding="utf-8-sig"))


def parse_number(tok: str):
    """千分位+括號負數+尾百分號;非數=None"""
    t = tok.strip().rstrip("%")
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace(",", "")
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", t):
        return None
    v = float(t)
    return -v if neg else v


def find_years(line: str, ssot: dict) -> list[tuple[str, str]]:
    """行內年度 token → [(西元年, src)];民國 +1911;FY 正規化"""
    out = []
    # 西元:lookaround 版(冊式 \b 在「2024年」因 年=\w 無邊界,引擎側等價強化)
    for m in re.finditer(r"(?<!\d)(?:19|20)\d{2}(?!\d)", line):
        out.append((m.group(0), "西元"))
    for m in re.finditer(r"\b(1[0-3]\d)(?=年度?|年)", line):  # 民國 100-139(冊:3 位數民國年)
        out.append((str(int(m.group(1)) + 1911), "民國+1911"))
    for m in re.finditer(r"(?i)FY\s?(\d{2,4})", line):
        y = m.group(1)
        y = ("20" + y) if len(y) == 2 else y
        if not any(o[0] == y for o in out):
            out.append((y, "FY"))
    seen = set()
    dedup = []
    for y, s in out:
        if y not in seen:
            seen.add(y)
            dedup.append((y, s))
    return dedup


def extract_annual(text: str, ssot: dict) -> dict:
    """財報頁文字 → {years, rows:{key:{block,label,values:{year:v},hit}}, misses}"""
    # 全形括號/冒號正規化(MOPS（損失）→(損失);冊內半形為準)
    text = text.replace("（", "(").replace("）", ")")
    lines = text.splitlines()
    years: list[str] = []
    year_src = ""
    for ln in lines[:80]:  # 年欄列通常在前段
        ys = find_years(ln, ssot)
        if len(ys) >= 2:
            years = [y for y, _ in ys]
            year_src = "、".join(sorted({s for _, s in ys}))
            break
    rows = {}
    for item in ssot["items"]:
        pats = sorted(item.get("zh", []) + item.get("en", []), key=len, reverse=True)
        for ln in lines:
            hit = next((p for p in pats
                        if (p in ln) or (re.match(r"^[A-Za-z]", p)
                                         and re.search(re.escape(p).replace(r"\ ", r"\s*"), ln, re.I))), None)
            if hit is None:
                continue
            nums = [parse_number(t) for t in NUM_RX.findall(ln.split(hit)[-1])]
            nums = [n for n in nums if n is not None]
            if not nums:
                continue
            vals = {}
            for i, v in enumerate(nums[:max(len(years), 1) if years else len(nums)]):
                col = years[i] if i < len(years) else f"Y{i + 1}"
                vals[col] = v
            rows[item["key"]] = {"block": item["block"], "label": hit, "values": vals,
                                 "fin": item.get("fin")}
            break
    misses = [i["key"] for i in ssot["items"] if i["key"] not in rows]
    return {"years": years or ["Y1"], "year_src": year_src or "出現序",
            "rows": rows, "misses": misses}


def to_fin_dict(result: dict, year: str | None = None) -> dict:
    """擷取結果 → finaudit --fin 全表稽核鍵(取指定年或首年欄)"""
    col = year or (result["years"][0] if result["years"] else "Y1")
    fin = {}
    for key, r in result["rows"].items():
        fk = r.get("fin")
        if fk and col in r["values"]:
            fin[fk] = r["values"][col]
    if "cfo" in fin and "cfi" in fin and "cff" in fin:
        fin.setdefault("net_change", round(fin["cfo"] + fin["cfi"] + fin["cff"], 4))
    return fin


def rich_matrix(title, columns, rows, state_col=None) -> bool:
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
                color = ("green" if s.startswith(("OK", "命中")) else
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


CSS = """
body{background:#f2f1ec;color:#1b1a17;font-family:'Cormorant Garamond','Noto Serif CJK TC','Microsoft JhengHei',serif;margin:0;padding:24px}
.card{background:#fbfaf7;border:1px solid #dbd9d3;border-radius:6px;padding:18px 22px;margin:14px auto;max-width:1180px}
h1{font-size:20px;margin:0 0 2px}h2{font-size:15px;color:#3c6660;margin:16px 0 6px}
.motto{color:#9e2b25;letter-spacing:.14em;font-size:11px;margin-bottom:14px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th{color:#3c6660;text-align:left;border-bottom:1.5px solid #3c6660;padding:4px 8px}
td{border-bottom:1px solid #dbd9d3;padding:4px 8px;vertical-align:top}
.ok{color:#3d7a52;font-weight:bold}.warn{color:#8a6420;font-weight:bold}
.mono{font-family:Consolas,monospace;font-size:11.5px}.dim{color:#6b6a64}
"""


def render_ui(result: dict, src_name: str, run_dir: Path, ssot: dict) -> Path:
    blocks = ssot["blocks"]
    years = result["years"]
    secs = []
    for bk, bname in blocks.items():
        rws = [(k, r) for k, r in result["rows"].items() if r["block"] == bk]
        if not rws:
            continue
        trs = "".join(
            f"<tr><td>{r['label']}</td>"
            + "".join(f"<td class='mono'>{r['values'].get(y, '—')}</td>" for y in years)
            + "</tr>" for _k, r in rws)
        secs.append(f"<h2>{bname}({bk})</h2><table><tr><th>科目</th>"
                    + "".join(f"<th>{y}</th>" for y in years) + f"</tr>{trs}</table>")
    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VRN 年度分析擷取表格</title><style>{CSS}</style></head><body>
<div class="card"><h1>年度分析擷取表格 · Annual Extraction</h1>
<div class="motto">{MOTTO}</div>
<div class="dim">源 {src_name} · 年欄 {'/'.join(years)}({result['year_src']})
 · 命中 {len(result['rows'])} / 未中 {len(result['misses'])}(誠實留空不猜)</div>
{''.join(secs)}
<h2 class="warn">未命中科目(誠實)</h2><div class="dim mono">{', '.join(result['misses']) or '—'}</div>
</div></body></html>"""
    out = run_dir / "VIA_UI_AnnualExtract.html"
    out.write_text(html, encoding="utf-8")
    return out


def run_file(path: Path, fin_out: Path | None, year: str | None, no_open: bool,
             out_root: Path | None = None) -> int:
    ssot = load_ssot()
    text = path.read_text(encoding="utf-8", errors="replace")
    result = extract_annual(text, ssot)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = (out_root or OUT_ROOT) / f"FINX_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "AnnualExtract_Result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    years = result["years"]
    rich_matrix(f"年度分析擷取表格 · {path.name}(四板塊;冊 SSOT {len(ssot['items'])} 科目)",
                ["板塊", "科目", *years],
                [[r["block"], r["label"], *[r["values"].get(y) for y in years]]
                 for r in result["rows"].values()])
    print(f"  [計] 命中 {len(result['rows'])} · 未中 {len(result['misses'])}(誠實留空)"
          f" · 年欄 {'/'.join(years)}({result['year_src']})")
    if fin_out:
        fin = to_fin_dict(result, year)
        fin_out.write_text(json.dumps(fin, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  [出] finaudit 全表稽核鍵 {len(fin)} → {fin_out}(via-finaudit --fin 接手)")
    ui = render_ui(result, path.name, run_dir, ssot)
    print(f"  [存] {run_dir.relative_to(VIA) if run_dir.is_relative_to(VIA) else run_dir}"
          f" · U/I {ui.name}")
    if not no_open:
        try:
            import webbrowser
            webbrowser.open(ui.as_uri())
        except Exception:
            pass
    return 0


# ── 十檢自測(合成 fixture 零網路)────────────────────────────
FIXTURE_MOPS = """數位測試工業 年度財務報告
                          2023年     2024年     2025年
營業收入合計             800,000    900,000    1,000,000
營業成本合計             480,000    530,000    580,000
營業毛利                 320,000    370,000    420,000
營業費用合計             120,000    130,000    140,000
營業利益                 200,000    240,000    280,000
本期淨利（損失）         160,000    190,000    (5,000)
流動資產合計             500,000    550,000    600,000
資產總額               1,000,000  1,100,000  1,200,000
流動負債合計             250,000    260,000    270,000
負債總額                 400,000    430,000    460,000
歸屬於母公司業主之權益總計 600,000   670,000    740,000
營業活動之淨現金流入（流出） 150,000  170,000    180,000
投資活動之淨現金流入（流出） (90,000) (95,000)  (100,000)
籌資活動之淨現金流入（流出） (20,000) (25,000)   (30,000)
基本每股盈餘             12.00      14.20      15.10
每股淨值                 60.00      64.00      68.00
"""

FIXTURE_YF = """FY2023 FY2024 Annual Report (US style)
Total Revenue    500,000  620,000
Cost of Revenue  300,000  360,000
Gross Profit     200,000  260,000
Operating Income 120,000  160,000
Net Income        90,000  120,000
Total Assets     800,000  900,000
Inventory         40,000   45,000
"""


def selftest() -> int:
    import tempfile
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        state = "OK" if cond else "FAIL"
        if not cond:
            fails.append(name)
        print(f"  [{state}] {name} {note}")

    ssot = load_ssot()
    # ① 冊在位:六板塊+科目數+年度式+公式
    chk("SSOT 冊在位", len(ssot["items"]) >= 70 and len(ssot["blocks"]) == 6
        and len(ssot["year_regex"]) >= 7 and "ccc" in ssot["formulas"],
        f"({len(ssot['items'])} 科目)")
    # ② 年度式:西元/民國+1911/FY 正規化
    y2 = find_years("2024年     113年度   FY23", ssot)
    chk("年度式(西元/民國/FY)", ("2024", "西元") in y2 and ("2024", "民國+1911") not in y2
        and any(y == "2023" and s == "FY" for y, s in y2)
        and any(y == "2024" and s == "民國+1911" for y, s in find_years("113年度 114年", ssot)))
    # ③ 數字解析:千分位/括號負數/百分比尾
    chk("數字解析", parse_number("1,234.5") == 1234.5 and parse_number("(5,000)") == -5000.0
        and parse_number("42.21%") == 42.21 and parse_number("N/A") is None)
    # ④ MOPS fixture:合計優先+年欄對齊
    r = extract_annual(FIXTURE_MOPS, ssot)
    chk("MOPS 擷取(合計優先+三年欄)",
        r["years"] == ["2023", "2024", "2025"]
        and r["rows"]["revenue"]["label"] == "營業收入合計"
        and r["rows"]["revenue"]["values"]["2025"] == 1000000.0
        and r["rows"]["net_income"]["values"]["2025"] == -5000.0)
    # ⑤ 四板塊在列:IS/BS/CF/PERSHARE 全命中
    blocks_hit = {v["block"] for v in r["rows"].values()}
    chk("四板塊命中", {"IS", "BS", "CF", "PERSHARE"} <= blocks_hit)
    # ⑥ YF 英文 fixture(FY 年欄+大小寫)
    r2 = extract_annual(FIXTURE_YF, ssot)
    chk("YFinance 擷取(FY 年欄)",
        r2["years"] == ["2023", "2024"]
        and r2["rows"]["revenue"]["values"]["2024"] == 620000.0
        and r2["rows"]["inventory"]["values"]["2023"] == 40000.0)
    # ⑦ 未中誠實留空
    chk("未中誠實", "ev_ebitda" in r["misses"] and "goodwill" in r["misses"])
    # ⑧ fin 映射+net_change 推導
    fin = to_fin_dict(r, "2025")
    chk("finaudit 鍵映射+net_change",
        fin["revenue"] == 1000000.0 and fin["equity"] == 740000.0
        and fin["net_change"] == 50000.0 and fin["eps"] == 15.10)
    # ⑨ finaudit 閉環:映射值餵 audit_financials(動態最新 finaudit)
    ok9 = False
    hits = sorted(HERE.glob("vrn_finaudit_v0*.py"))
    if hits:
        import importlib.util
        import warnings
        spec = importlib.util.spec_from_file_location("finx_fa_dyn", hits[-1])
        fam = importlib.util.module_from_spec(spec)
        sys.modules["finx_fa_dyn"] = fam
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            spec.loader.exec_module(fam)
        fa, _ = fam.load_feature_audit()
        fin23 = to_fin_dict(r, "2023")
        checks = fam.audit_financials(fin23, fa)
        ok9 = (len(checks) >= 2
               and any("恆等式" in c["rule"] and c["passed"] for c in checks))
    chk("finaudit 閉環(擷取→映射→三表勾稽)", ok9)
    # ⑩ 批跑產物:JSON+U/I 銘言+fin-out
    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        src = sand / "fin_page.txt"
        src.write_text(FIXTURE_MOPS, encoding="utf-8")
        fo = sand / "fin.json"
        rc = run_file(src, fo, "2024", no_open=True, out_root=sand / "out")
        runs = sorted((sand / "out").glob("FINX_*"))
        ok10 = (rc == 0 and runs and fo.exists()
                and (runs[-1] / "VIA_UI_AnnualExtract.html").exists()
                and MOTTO in (runs[-1] / "VIA_UI_AnnualExtract.html").read_text(encoding="utf-8")
                and json.loads(fo.read_text(encoding="utf-8"))["revenue"] == 900000.0)
        chk("批跑產物(JSON+U/I+fin-out)", bool(ok10))
    n = 10 - len(fails)
    print(f"  [計] 十檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 財報頁年度分析擷取器 v0100 · 十檢自測(合成 fixture 零網路)===")
        return selftest()
    if "--file" in args:
        i = args.index("--file")
        p = Path(args[i + 1]) if i + 1 < len(args) else None
        if not p or not p.exists():
            print(f"  [FAIL] 檔不存在:{p}")
            return 1
        fin_out = None
        if "--fin-out" in args:
            j = args.index("--fin-out")
            fin_out = Path(args[j + 1]) if j + 1 < len(args) else None
        year = None
        if "--year" in args:
            k = args.index("--year")
            year = args[k + 1] if k + 1 < len(args) else None
        print("=== 財報頁年度分析擷取器 v0100 · 四板塊年度表格(TOOL-082)===")
        return run_file(p, fin_out, year, "--no-open" in args)
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
