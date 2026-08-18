#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_report_digest_v0100 — 個股報告摘要批跑器(TOOL-070)
====================================================================
操作員令(批41,2026-08-18):「現在又修復文字功能及摘要功能
請寫每個個股報告摘葉(=摘要)」。
原則:
  ① 引擎不重造 — 摘要核心=VRN_ENG062 Summarizer(一標題五點+
     ADJ CLOSE 指標);本批跑器動態解析最新版匯入,零改寫正本。
  ② 黃旗補治 — Summarizer 五點缺句時落預設填充語;本器逐點比對
     填充語清單,命中即加「〔自動生成〕」標註(台帳黃旗結案,
     正本零觸碰=version-forward 外包裝)。
  ③ 參數中央化 — 全參數讀 knowledge/VRN_Digest_Params_v0100.json
     (該冊已入 TOOL-069 中央參數樞紐衝突圈);引擎零寫死。
  ④ 誠實三態 — 逐報告 OK/FAIL/SKIP;pdf 無抽取器=SKIP 誠實;
     ticker 年區 2021-2030 依 LOCKED regex 排除。
  ⑤ 存證 — VIA_Reports/digest_runs/DIGEST_<ts>/:逐報告 .md+
     Digest_Matrix.json;理印 U/I VIA_UI_ReportDigest.html。
用法:
  via-digest --dir <報告夾>       → 批跑(txt/md/docx;pdf 視環境)
  via-digest                      → 掃預設候選夾(冊列)
  via-digest --limit N            → 只跑前 N 件
  via-digest --selftest           → 七檢(合成 fixture 零網路)
  via-digest --no-open            → 不開 U/I
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent          # functional modules/VRN
VIA = HERE.parent.parent
PARAMS_PATH = HERE / "knowledge" / "VRN_Digest_Params_v0100.json"
MOTTO = "VERITAS INTELLIGENCE ANALYTICS · OBSERVA · INTELLEGE · PRAEVIDE"


def load_params() -> dict:
    return json.loads(PARAMS_PATH.read_text(encoding="utf-8-sig"))


def load_summarizer():
    """動態解析最新 Summarizer(鐵律:嚴禁寫死版號)"""
    hits = sorted(HERE.glob("VRN_ENG062_Summarizer*.py")) or sorted(HERE.glob("VRN_Summarizer_v*.py"))
    if not hits:
        return None, "Summarizer 引擎缺(誠實)"
    eng = hits[-1]
    spec = importlib.util.spec_from_file_location("vrn_summarizer_dyn", eng)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:
        return None, f"Summarizer 匯入敗:{str(exc)[:80]}"
    return mod, eng.name


def _sweep(msg: str, i: int, n: int) -> None:
    """常備令Ⅱ:動態進度條(單行覆寫,不卡斷)"""
    w = 24
    k = int(w * i / max(n, 1))
    sys.stdout.write(f"\r  [{'█' * k}{'░' * (w - k)}] {i}/{n} {msg[:44]:<44}")
    sys.stdout.flush()
    if i >= n:
        sys.stdout.write("\n")


# ── 文字抽取(修復後文字功能之最小自足道;docx 零外依)──────
def extract_text(p: Path) -> tuple[str, str]:
    """回 (text, state);state ∈ OK / SKIP:<因>"""
    ext = p.suffix.lower()
    if ext in (".txt", ".md"):
        for enc in ("utf-8-sig", "cp950", "big5", "latin-1"):
            try:
                return p.read_text(encoding=enc), "OK"
            except (UnicodeDecodeError, LookupError):
                continue
        return "", "SKIP:編碼不明"
    if ext == ".docx":
        try:
            with zipfile.ZipFile(p) as z:
                xml = z.read("word/document.xml").decode("utf-8", "ignore")
            xml = re.sub(r"</w:p>", "\n", xml)
            text = re.sub(r"<[^>]+>", "", xml)
            return re.sub(r"\n{3,}", "\n\n", text).strip(), "OK"
        except Exception as exc:
            return "", f"SKIP:docx 讀取敗 {str(exc)[:40]}"
    if ext == ".pdf":
        try:
            import pypdf  # 環境有則用;無=誠實 SKIP
            reader = pypdf.PdfReader(str(p))
            return "\n".join((pg.extract_text() or "") for pg in reader.pages), "OK"
        except ImportError:
            return "", "SKIP:pdf 抽取器缺(pypdf)"
        except Exception as exc:
            return "", f"SKIP:pdf 讀取敗 {str(exc)[:40]}"
    return "", f"SKIP:副檔名不支援 {ext}"


# ── 元資料收割(檔名+內文;LOCKED regex 年區排除)────────────
def harvest_meta(p: Path, text: str, prm: dict, broker_dict: dict) -> dict:
    pats = prm["meta_patterns"]
    locked = re.compile(prm["tw_ticker_locked"])
    year = re.compile(prm["year_suspect"])  # LOCKED 第一支放行四碼,年區須疊拒絕閘(字庫 v0101 同法)
    hay = p.stem + "\n" + text[:3000]
    meta = {}
    for cand in re.findall(pats["ticker_candidate"], hay):
        if locked.match(cand) and not year.match(cand):
            meta["ticker"] = cand
            break
    m = re.search(pats["target_price"], text)
    if m:
        meta["target_price"] = float(m.group(1).replace(",", ""))
    m = re.search(pats["rating"], text)
    if m:
        meta["rating"] = m.group(1)
    m = re.search(pats["eps_current"], text)
    if m:
        meta["eps_current"] = float(m.group(1))
    m = re.search(pats["report_date"], hay)
    if m:
        d = re.sub(r"[-/\.]", "", m.group(1))
        meta["report_date"] = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    for broker in broker_dict:
        if broker and broker in hay:
            meta["broker"] = broker
            break
    return meta


def tag_fillers(summary, prm: dict) -> tuple[int, dict]:
    """五點逐比填充語;命中加〔自動生成〕標註(正本 dataclass 就地
    改欄位值=本器輸出物,Summarizer 引擎零觸碰)"""
    tag = prm["filler_tag"]
    fillers = set(prm["filler_phrases"])
    p1_rx = re.compile(prm["point1_fallback_regex"])
    fields = ["point_1_conclusion", "point_2_growth", "point_3_valuation",
              "point_4_peers", "point_5_risk"]
    n = 0
    flags = {}
    for f in fields:
        v = getattr(summary, f, "") or ""
        auto = v in fillers or (f == "point_1_conclusion" and bool(p1_rx.match(v)))
        flags[f] = "AUTO" if auto else "TEXT"
        if auto and tag not in v:
            setattr(summary, f, f"{v}{tag}")
            n += 1
    return n, flags


# ── 批跑 ─────────────────────────────────────────────────────
def run_batch(report_dir: Path, limit: int | None, no_open: bool,
              out_root: Path | None = None) -> int:
    prm = load_params()
    mod, eng_name = load_summarizer()
    if mod is None:
        print(f"  [FAIL] {eng_name}")
        return 1
    print(f"  [引擎] {eng_name} · 參數冊 {PARAMS_PATH.name}(中央化)")
    exts = set(prm["extensions"])
    files = sorted(p for p in report_dir.rglob("*")
                   if p.is_file() and p.suffix.lower() in exts and "_sha" not in p.stem)
    if limit:
        files = files[:limit]
    if not files:
        print(f"  [SKIP] {report_dir} 內零報告件(誠實;支援 {'/'.join(sorted(exts))})")
        return 0
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = (out_root or (VIA / prm["output_root"])) / f"DIGEST_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    broker_dict = getattr(mod, "BROKER_ABBR_DICT", {})
    rows = []
    n_ok = n_fail = n_skip = 0
    for i, p in enumerate(files, 1):
        _sweep(p.name, i, len(files))
        text, state = extract_text(p)
        if state != "OK" or not text.strip():
            n_skip += 1
            rows.append({"file": p.name, "state": state if state != "OK" else "SKIP:空文",
                         "ticker": "", "headline": ""})
            continue
        try:
            meta = harvest_meta(p, text, prm, broker_dict)
            fp = text[:prm["first_page_chars"]]
            rest = text[prm["first_page_chars"]:]
            summary = mod.summarize_report(
                ticker=meta.get("ticker", ""), first_page_text=fp, remaining_text=rest,
                broker=meta.get("broker", ""), report_date=meta.get("report_date", ""),
                filename=p.name, target_price=meta.get("target_price"),
                rating=meta.get("rating", ""), eps_current=meta.get("eps_current"))
            n_auto, flags = tag_fillers(summary, prm)
            stem = (summary.report_code or p.stem).replace("/", "_")
            md_path = run_dir / f"{stem}_digest.md"
            md_path.write_text(summary.to_markdown() + "\n", encoding="utf-8")
            n_ok += 1
            rows.append({"file": p.name, "state": "OK", "ticker": summary.ticker,
                         "name": summary.name, "broker": summary.broker,
                         "rating": summary.rating, "target_price": summary.target_price,
                         "adj_close": summary.adj_close, "upside_pct": summary.upside_pct,
                         "report_code": summary.report_code, "headline": summary.headline,
                         "auto_filled": n_auto, "point_flags": flags,
                         "md": md_path.name})
        except Exception as exc:
            n_fail += 1
            rows.append({"file": p.name, "state": f"FAIL:{str(exc)[:60]}",
                         "ticker": "", "headline": ""})
    matrix = {"schema": "VIA.ReportDigest.v1", "ts": ts, "dir": str(report_dir),
              "engine": eng_name, "total": len(files),
              "ok": n_ok, "fail": n_fail, "skip": n_skip, "rows": rows}
    (run_dir / "Digest_Matrix.json").write_text(
        json.dumps(matrix, ensure_ascii=False, indent=1), encoding="utf-8")
    ui = render_ui(matrix, run_dir, prm)
    print(f"  [計] 報告 {len(files)} · OK {n_ok} · FAIL {n_fail} · SKIP {n_skip}(誠實三態)")
    print(f"  [存] {run_dir.relative_to(VIA) if run_dir.is_relative_to(VIA) else run_dir}"
          f" · U/I {ui.name}")
    if not no_open:
        try:
            import webbrowser
            webbrowser.open(ui.as_uri())
        except Exception:
            pass
    return 1 if n_fail else 0


# ── 理印紙墨 U/I ──────────────────────────────────────────────
CSS = """
body{background:#f2f1ec;color:#1b1a17;font-family:'Cormorant Garamond','Noto Serif CJK TC','Microsoft JhengHei',serif;margin:0;padding:24px}
.card{background:#fbfaf7;border:1px solid #dbd9d3;border-radius:6px;padding:18px 22px;margin:14px auto;max-width:1280px}
h1{font-size:20px;margin:0 0 2px}
.motto{color:#9e2b25;letter-spacing:.14em;font-size:11px;margin-bottom:14px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th{color:#3c6660;text-align:left;border-bottom:1.5px solid #3c6660;padding:4px 8px}
td{border-bottom:1px solid #dbd9d3;padding:4px 8px;vertical-align:top}
.ok{color:#3d7a52;font-weight:bold}.warn{color:#8a6420;font-weight:bold}.bad{color:#9e2b25;font-weight:bold}
.mono{font-family:Consolas,monospace;font-size:11.5px}.dim{color:#6b6a64}
"""


def render_ui(matrix: dict, run_dir: Path, prm: dict) -> Path:
    rows = []
    for r in matrix["rows"]:
        st = r["state"]
        cls = "ok" if st == "OK" else ("bad" if st.startswith("FAIL") else "warn")
        flags = r.get("point_flags", {})
        dots = "".join(
            f"<span class='{'warn' if flags.get(f) == 'AUTO' else 'ok'}'>●</span>"
            for f in ["point_1_conclusion", "point_2_growth", "point_3_valuation",
                      "point_4_peers", "point_5_risk"]) if flags else "—"
        rows.append(
            f"<tr><td class='mono dim'>{r['file']}</td><td class='{cls}'>{st}</td>"
            f"<td class='mono'>{r.get('ticker', '')}</td><td>{r.get('name', '') or ''}</td>"
            f"<td>{r.get('broker', '') or ''}</td><td>{r.get('rating', '') or ''}</td>"
            f"<td>{r.get('target_price', '') or ''}</td><td>{r.get('upside_pct', '') or ''}</td>"
            f"<td>{dots}</td><td class='dim'>{(r.get('headline', '') or '')[:60]}</td></tr>")
    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VRN 個股報告摘要矩陣</title><style>{CSS}</style></head><body>
<div class="card"><h1>個股報告摘要矩陣 · Report Digest</h1>
<div class="motto">{MOTTO}</div>
<div class="dim">批次 {matrix['ts']} · 來源 {matrix['dir']} · 引擎 {matrix['engine']}
 · 報告 {matrix['total']}(OK {matrix['ok']} / FAIL {matrix['fail']} / SKIP {matrix['skip']})
 · 五點燈:綠=原文抽句 / 黃=填充語{prm['filler_tag']}標註</div>
<table><tr><th>檔</th><th>態</th><th>代碼</th><th>名</th><th>券商</th><th>評等</th>
<th>目標價</th><th>上漲%</th><th>五點</th><th>標題</th></tr>{''.join(rows)}</table></div>
</body></html>"""
    out = run_dir / prm["ui_name"]
    out.write_text(html, encoding="utf-8")
    return out


# ── 七檢自測(合成 fixture 零網路)───────────────────────────
FIXTURE_FULL = """數位測試工業 投資報告
評等:買進 (維持)
目標價:250 元
2026-01-15
AI 應用需求強勁,先進封裝訂單能見度達兩季。
預估 EPS 12.5 元,年增 18%。
成長動能:高速運算產品線放量,市佔持續提升。
財務預估:毛利率站穩 42%,ROE 20% 以上。
同業比較:相較同業 A 公司與 B 公司,產品組合較優。
風險因子:留意庫存去化不如預期與匯率波動。
"""

FIXTURE_SPARSE = """測試精機
簡評:產業復甦初期。
"""


def selftest() -> int:
    import shutil
    import tempfile
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        state = "OK" if cond else "FAIL"
        if not cond:
            fails.append(name)
        print(f"  [{state}] {name} {note}")

    prm = load_params()
    # ① 參數冊中央化在位:必備鍵齊
    need = {"first_page_chars", "filler_phrases", "filler_tag", "meta_patterns",
            "tw_ticker_locked", "output_root"}
    chk("參數冊必備鍵", need <= set(prm.keys()), f"({PARAMS_PATH.name})")

    # ② Summarizer 動態解析可匯入
    mod, eng_name = load_summarizer()
    chk("Summarizer 動態匯入", mod is not None, f"({eng_name})")
    if mod is None:
        print("  [計] 七檢中止(引擎缺)")
        return 1

    # ③ ticker 年區閘=LOCKED 收+YEAR_SUSPECT 拒疊閘:2330 收、2025 拒
    locked = re.compile(prm["tw_ticker_locked"])
    year = re.compile(prm["year_suspect"])
    gate = lambda s: bool(locked.match(s)) and not year.match(s)
    chk("ticker 年區閘", gate("2330") and not gate("2025"))

    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        rpt = sand / "reports"
        rpt.mkdir()
        (rpt / "2330_數位測試工業_20260115.txt").write_text(FIXTURE_FULL, encoding="utf-8")
        (rpt / "1560_測試精機.txt").write_text(FIXTURE_SPARSE, encoding="utf-8")
        # 合成 docx(zip+document.xml;零外依)
        dx = rpt / "3661_合成docx報告.docx"
        with zipfile.ZipFile(dx, "w") as z:
            z.writestr("word/document.xml",
                       "<w:document><w:p><w:t>合成docx 目標價:300 元 評等:持有</w:t></w:p>"
                       "<w:p><w:t>風險因子:留意需求波動。</w:t></w:p></w:document>")
        (rpt / "空文報告.txt").write_text("", encoding="utf-8")  # SKIP 態觸發件(空文;兩端環境穩定)

        # ④ docx 抽取道通
        text, state = extract_text(dx)
        chk("docx 抽取(零外依)", state == "OK" and "目標價" in text)

        # ⑤ 元資料收割:ticker/目標價/評等/日期
        meta = harvest_meta(rpt / "2330_數位測試工業_20260115.txt", FIXTURE_FULL, prm,
                            getattr(mod, "BROKER_ABBR_DICT", {}))
        chk("元資料收割", meta.get("ticker") == "2330" and meta.get("target_price") == 250.0
            and meta.get("rating") == "買進" and meta.get("report_date") == "2026-01-15")

        # ⑥ 批跑三態+黃旗標註:sparse 件五點必有 AUTO 標
        rc = run_batch(rpt, limit=None, no_open=True, out_root=sand / "out")
        runs = sorted((sand / "out").glob("DIGEST_*"))
        ok6 = bool(runs) and rc == 0
        if ok6:
            mx = json.loads((runs[-1] / "Digest_Matrix.json").read_text(encoding="utf-8"))
            sparse = next((r for r in mx["rows"] if r["file"].startswith("1560")), {})
            ok6 = (mx["ok"] >= 3 and mx["fail"] == 0 and mx["skip"] == 1
                   and sparse.get("auto_filled", 0) >= 3)
        chk("批跑三態+填充語標註", ok6)

        # ⑦ 產物齊:逐報告 md 含標註、U/I 含銘言
        ok7 = False
        if runs:
            mds = list(runs[-1].glob("*_digest.md"))
            ui = runs[-1] / prm["ui_name"]
            ok7 = (len(mds) >= 3 and ui.exists()
                   and MOTTO in ui.read_text(encoding="utf-8")
                   and any(prm["filler_tag"] in m.read_text(encoding="utf-8") for m in mds))
        chk("md+U/I 產物齊", ok7)
    n = 7 - len(fails)
    print(f"  [計] 七檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 個股報告摘要批跑器 v0100 · 七檢自測(合成 fixture 零網路)===")
        return selftest()
    limit = None
    if "--limit" in args:
        i = args.index("--limit")
        limit = int(args[i + 1]) if i + 1 < len(args) else None
    no_open = "--no-open" in args
    prm = load_params()
    if "--dir" in args:
        i = args.index("--dir")
        report_dir = Path(args[i + 1]) if i + 1 < len(args) else None
        if not report_dir or not report_dir.exists():
            print(f"  [FAIL] 報告夾不存在:{report_dir}")
            return 1
    else:
        report_dir = next((VIA / d for d in prm["default_scan_dirs"]
                           if (VIA / d).exists()), None)
        if report_dir is None:
            print("  [SKIP] 未指定 --dir 且預設候選夾皆缺(誠實):")
            for d in prm["default_scan_dirs"]:
                print(f"         · {d}")
            return 0
        print(f"  [夾] 未指定 --dir,用預設候選:{report_dir.relative_to(VIA)}")
    print(f"=== 個股報告摘要批跑器 v0100 · 一標題五點(TOOL-070)===")
    return run_batch(report_dir, limit, no_open)


if __name__ == "__main__":
    sys.exit(main())
