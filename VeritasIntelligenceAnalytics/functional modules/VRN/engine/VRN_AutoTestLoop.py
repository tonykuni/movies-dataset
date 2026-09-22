# -*- coding: utf-8 -*-
"""
VRN_AutoTestLoop v0100 — 自動測試、自動修正、直到成功（或說清楚卡在哪一段）

對象：
    VIA_VRN_FirstPageEngine.py            首頁抽取與交叉驗證
    VRN_Integrated_ReportDatabase_Engine.py  檔名 + 首頁 + 表格 -> Parquet 報告資料庫
    VIA_TW_Ticker_Master_v0210.py         代碼格式分類（ETF / 個股 / 三平台）
    references/intake/VIA_SSOT_Additive_Audit_v0100/audit_ssot.py  30 項 SSOT 稽核

閘門（每輪全部重跑）：
    G01 COMPILE      四支引擎 + 稽核腳本可編譯
    G02 SELFTEST     資料庫引擎 --self-test、首頁引擎 import、代碼主檔分類
    G03 FILENAME     106 個檔名（稽核包 FILENAME_RESULTS.json）+ 64 個 roster 檔名：兩支引擎的
                     代號／日期／券商都要對上 oracle
    G04 AUDIT        audit_ssot.py 在暫存副本重跑，30/30
    G05 CORPUS       測試檔案：`--samples`（Windows 預設 C:\\測試樣本報告）；沒有實檔就合成
                     PDF／DOCX／TXT／JPG（fitz 內建 CJK 字型，表格畫格線）
    G06 BATCH        資料庫引擎整批跑：每檔 OK、Parquet 定型、代號／日期／券商／評等／目標價／EPS
                     對上 truth（合成語料）或 oracle（實檔只比檔名層）
    G07 FIRSTPAGE    首頁引擎逐檔跑：代號、評等、目標價、券商、三平台 PASS、檔名 vs 首頁 PASS
    G08 IDEMPOTENT   第二輪整批：BasicRows 不變（ReportID upsert），Parquet 可讀
    G09 READONLY     樣本檔案 SHA256 前後不變；引擎不改輸入

自動修正（每輪失敗後套用，可回溯）：
    F1 pdf-engine-order     PDF 文字層抽不到／出錯 -> 交換 PyMuPDF / pdfplumber 順序
    F2 first-page-hook-off  首頁引擎鉤子丟例外 -> 關閉鉤子，資料庫引擎獨立跑
    F3 dependency-note      缺 pandas/pyarrow/pdfplumber/pymupdf/python-docx -> 標 DEPENDENCY_MISSING，
                            印出 pip 指令（安裝是操作員的手，本迴圈不自行安裝）
    F4 corpus-regenerate    合成語料損毀 -> 重新產生

治理：LIVE 關；不連網；不設定任何 consent 環境變數；輸出寫到 --out（預設暫存目錄），不寫回倉庫。

執行：
    python VRN_AutoTestLoop.py                                  # Windows: C:\\測試樣本報告 若存在
    python VRN_AutoTestLoop.py --samples "C:\\測試樣本報告" --out "C:\\VRN_AutoTest"
    python VRN_AutoTestLoop.py --synthetic --rounds 3 --json report.json --html report.html
退出碼：0 全綠（WARN 允許）；1 有 FAIL；2 環境無法建立語料（無 fitz 也無實檔）。
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

import argparse
import hashlib
import html
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

LOOP_VERSION = "v0100"
HERE = Path(__file__).resolve().parent
VRN_ROOT = HERE.parent
REPO_ROOT = VRN_ROOT.parent.parent if (VRN_ROOT.parent.name == "functional modules") else VRN_ROOT
DEFAULT_SAMPLES_WINDOWS = r"C:\測試樣本報告"
DEFAULT_ROUNDS = 3
ENGINE_FILES = {
    "first_page": HERE / "VIA_VRN_FirstPageEngine.py",
    "database": HERE / "VRN_Integrated_ReportDatabase_Engine.py",
    "ticker_master": HERE / "VIA_TW_Ticker_Master_v0210.py",
    "panorama": HERE / "VRN_PanoramaProbe.py",
}
AUDIT_DIR = VRN_ROOT / "references" / "intake" / "VIA_SSOT_Additive_Audit_v0100"
ROSTER_TS = REPO_ROOT / "src" / "lib" / "via" / "incoming-roster.ts"
SYNTH_RATINGS = ["BUY", "HOLD", "SELL"]
RATING_WORDS = {"BUY": "買進", "HOLD": "中立", "SELL": "賣出", "NOT_RATED": "未評等", "ADD": "逢低買進"}
DEP_INSTALL_HINT = "pip install pandas pyarrow pdfplumber pymupdf python-docx"
STATUS_ORDER = {"FAIL": 0, "WARN": 1, "SKIP": 2, "PASS": 3}


# ---------------------------------------------------------------------------
# 00. utilities
# ---------------------------------------------------------------------------
def def_load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def def_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


_IMPORT_CACHE: Dict[str, bool] = {}


def def_has(module_name: str) -> bool:
    """True only when the module really imports (find_spec alone misses broken binary stacks)."""
    if module_name not in _IMPORT_CACHE:
        try:
            importlib.import_module(module_name)
            _IMPORT_CACHE[module_name] = True
        except BaseException:  # noqa: BLE001 - a broken extension can raise almost anything
            _IMPORT_CACHE[module_name] = False
    return _IMPORT_CACHE[module_name]


def def_row(gate: str, name: str, status: str, detail: str = "", **extra: Any) -> Dict[str, Any]:
    row = {"gate": gate, "name": name, "status": status, "detail": detail}
    row.update(extra)
    return row


def def_load_roster(ts_path: Path = ROSTER_TS) -> List[str]:
    """MOTHER_INCOMING names from src/lib/via/incoming-roster.ts (graceful when absent)."""
    if not ts_path.is_file():
        return []
    text = ts_path.read_text(encoding="utf-8", errors="replace")
    start = text.find("MOTHER_INCOMING")
    if start < 0:
        return []
    import re
    block = text[start:]
    end = block.find("];")
    block = block[: end if end > 0 else None]
    names = re.findall(r"""["'`]([^"'`\n]+\.(?:pdf|docx|txt|jpe?g|png))["'`]""", block, flags=re.I)
    return list(dict.fromkeys(names))


def def_load_oracle() -> Dict[str, Dict[str, Any]]:
    path = AUDIT_DIR / "FILENAME_RESULTS.json"
    if not path.is_file():
        return {}
    try:
        rows = json.loads(path.read_text(encoding="utf-8-sig"))
    except ValueError:
        return {}
    return {r["filename"]: r for r in rows if isinstance(r, dict) and r.get("filename")}


# ---------------------------------------------------------------------------
# 01. engines
# ---------------------------------------------------------------------------
class Engines:
    def __init__(self) -> None:
        self.errors: Dict[str, str] = {}
        self.first_page = self._load("first_page")
        self.database = self._load("database")
        self.ticker_master = self._load("ticker_master")
        self.fpe = None
        if self.first_page is not None:
            try:
                self.fpe = self.first_page.FirstPageEngine()
            except Exception as error:  # noqa: BLE001
                self.errors["first_page_engine"] = f"{error.__class__.__name__}: {error}"

    def _load(self, key: str):
        path = ENGINE_FILES[key]
        if not path.is_file():
            self.errors[key] = "missing " + str(path)
            return None
        try:
            return def_load_module("vrn_autotest_" + key, path)
        except Exception as error:  # noqa: BLE001
            self.errors[key] = f"{error.__class__.__name__}: {error}"
            return None


# ---------------------------------------------------------------------------
# 02. gates that need no documents
# ---------------------------------------------------------------------------
def def_gate_compile() -> List[Dict[str, Any]]:
    rows = []
    targets = list(ENGINE_FILES.values()) + [AUDIT_DIR / "audit_ssot.py", AUDIT_DIR / "ticker_regexes.py"]
    for path in targets:
        if not path.is_file():
            rows.append(def_row("G01 COMPILE", path.name, "SKIP", "absent"))
            continue
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")   # no .pyc is written
            rows.append(def_row("G01 COMPILE", path.name, "PASS"))
        except (SyntaxError, ValueError, OSError) as error:
            rows.append(def_row("G01 COMPILE", path.name, "FAIL", f"{error.__class__.__name__}: {error}"[:300]))
    return rows


def def_gate_selftest(engines: Engines) -> List[Dict[str, Any]]:
    rows = []
    for key, message in engines.errors.items():
        rows.append(def_row("G02 SELFTEST", key, "FAIL", message))
    if engines.database is not None:
        try:
            import contextlib, io
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                engines.database.run_self_test()
            rows.append(def_row("G02 SELFTEST", "database --self-test", "PASS", buffer.getvalue().strip().splitlines()[-1][:120]))
        except Exception as error:  # noqa: BLE001
            rows.append(def_row("G02 SELFTEST", "database --self-test", "FAIL", f"{error.__class__.__name__}: {error}"[:300]))
    if engines.fpe is not None:
        try:
            out = engines.fpe.run("凱基_神達3706 TT_初次評等_(20)260131_TargetPrice 168.pdf")
            ok = out["ticker"]["ticker"] == "3706" and out["report_date"] == "2026-01-31" and out["broker"] == "KGI"
            rows.append(def_row("G02 SELFTEST", "first-page filename smoke", "PASS" if ok else "FAIL",
                                f"ticker={out['ticker']['ticker']} date={out['report_date']} broker={out['broker']}"))
        except Exception as error:  # noqa: BLE001
            rows.append(def_row("G02 SELFTEST", "first-page filename smoke", "FAIL", f"{error.__class__.__name__}: {error}"[:300]))
    if engines.ticker_master is not None:
        try:
            stock = engines.ticker_master.classify_ticker("2330")
            etf = engines.ticker_master.classify_ticker("006208")
            bad = engines.ticker_master.classify_ticker("2026年")
            ok = (stock.get("pattern_category") == "STOCK" and "ETF" in str(etf.get("pattern_category", ""))
                  and bad.get("status") in {"INVALID", "REVIEW"})
            rows.append(def_row("G02 SELFTEST", "ticker master classify", "PASS" if ok else "FAIL",
                                f"2330={stock.get('pattern_category')} 006208={etf.get('pattern_category')} 2026年={bad.get('status')}"))
        except Exception as error:  # noqa: BLE001
            rows.append(def_row("G02 SELFTEST", "ticker master classify", "FAIL", f"{error.__class__.__name__}: {error}"[:300]))
    return rows


def def_filename_truth(engines: Engines, name: str) -> Dict[str, Any]:
    """Filename-level expectation: oracle row when the audit package knows the name, else the first-page engine."""
    return engines.fpe._filename_fields(name) if engines.fpe is not None else {}


def def_gate_filename_oracle(engines: Engines) -> List[Dict[str, Any]]:
    rows = []
    oracle = def_load_oracle()
    if not oracle:
        return [def_row("G03 FILENAME", "oracle", "SKIP", "FILENAME_RESULTS.json absent")]
    names = list(oracle)
    roster = [n for n in def_load_roster() if n not in oracle]
    if engines.fpe is not None:
        bad = []
        for name, row in oracle.items():
            got = engines.fpe._filename_fields(name)
            exp = ((row.get("ticker_candidates") or [""])[0], row.get("report_date") or "", (row.get("broker") or {}).get("value") or "")
            have = (got["ticker"] or "", got["date"] or "", got["broker"] or "")
            if have != exp:
                bad.append(f"{name}: got={have} exp={exp}")
        rows.append(def_row("G03 FILENAME", f"first-page engine vs oracle ({len(names)})", "FAIL" if bad else "PASS",
                            "; ".join(bad[:6]), mismatches=bad))
    if engines.database is not None:
        db = engines.database
        try:
            broker_alias = db.load_broker_alias_ssot(None)
            bad = []
            for name, row in oracle.items():
                ti = db.tokenize_filename(name)
                cands = [c["ticker"] for c in db.extract_filename_ticker_candidates(ti, {}) if c["ticker"]]
                dates = db.parse_date_candidates_from_number_tokens(ti["number_tokens"])
                frags = db.company_fragments_after_ticker(ti["tokens"])
                broker, _, _ = db.match_broker_from_tokens_and_text(ti["chinese_tokens"], ti["english_tokens"], "", broker_alias, frags)
                have = ((cands or [""])[0], dates[0]["date"] if dates else "", broker or "")
                exp = ((row.get("ticker_candidates") or [""])[0], row.get("report_date") or "", (row.get("broker") or {}).get("value") or "")
                if have != exp:
                    bad.append(f"{name}: got={have} exp={exp}")
            rows.append(def_row("G03 FILENAME", f"database engine vs oracle ({len(names)})", "FAIL" if bad else "PASS",
                                "; ".join(bad[:6]), mismatches=bad))
        except Exception as error:  # noqa: BLE001
            rows.append(def_row("G03 FILENAME", "database engine vs oracle", "FAIL", f"{error.__class__.__name__}: {error}"[:300]))
    if roster and engines.fpe is not None and engines.database is not None:
        db = engines.database
        broker_alias = db.load_broker_alias_ssot(None)
        disagree = []
        for name in roster:
            f = engines.fpe._filename_fields(name)
            ti = db.tokenize_filename(name)
            cands = [c["ticker"] for c in db.extract_filename_ticker_candidates(ti, {}) if c["ticker"]]
            dates = db.parse_date_candidates_from_number_tokens(ti["number_tokens"])
            frags = db.company_fragments_after_ticker(ti["tokens"])
            broker, _, _ = db.match_broker_from_tokens_and_text(ti["chinese_tokens"], ti["english_tokens"], "", broker_alias, frags)
            a = (f["ticker"] or "", f["date"] or "", f["broker"] or "")
            b = ((cands or [""])[0], dates[0]["date"] if dates else "", broker or "")
            if a != b:
                disagree.append(f"{name}: first-page={a} database={b}")
        rows.append(def_row("G03 FILENAME", f"roster names outside the oracle ({len(roster)}): both engines agree",
                            "FAIL" if disagree else "PASS", "; ".join(disagree[:6]), mismatches=disagree))
    return rows


def def_gate_audit(workdir: Path) -> List[Dict[str, Any]]:
    script = AUDIT_DIR / "audit_ssot.py"
    if not script.is_file():
        return [def_row("G04 AUDIT", "audit_ssot.py", "SKIP", "package absent")]
    target = workdir / "audit_copy"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(AUDIT_DIR, target, ignore=shutil.ignore_patterns("_upload", "__pycache__"))
    try:
        completed = subprocess.run([sys.executable, "-I", "audit_ssot.py"], cwd=str(target), capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", timeout=600)
    except (OSError, subprocess.SubprocessError) as error:
        return [def_row("G04 AUDIT", "audit_ssot.py", "FAIL", f"{error.__class__.__name__}: {error}"[:300])]
    summary_path = target / "AUDIT_SUMMARY.json"
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8-sig"))
        qa = summary.get("qa", {})
        ok = completed.returncode == 0 and bool(qa.get("all_passed"))
        return [def_row("G04 AUDIT", "audit_ssot.py 30 checks", "PASS" if ok else "FAIL",
                        f"exit={completed.returncode} passed={qa.get('passed')}/{qa.get('total')} " + (completed.stderr.strip().splitlines()[-1][:160] if completed.stderr.strip() else ""))]
    except (OSError, ValueError) as error:
        return [def_row("G04 AUDIT", "audit_ssot.py 30 checks", "FAIL", f"exit={completed.returncode} summary unreadable: {error}"[:300])]


# ---------------------------------------------------------------------------
# 03. synthetic corpus (fitz built-in CJK font; tables drawn with grid lines)
# ---------------------------------------------------------------------------
def def_synthetic_truth(engines: Engines, name: str, index: int) -> Dict[str, Any]:
    f = def_filename_truth(engines, name)
    parse = f.get("parse", {})
    ticker = f.get("ticker") or ""
    cjk = [t for t in parse.get("cjk", []) if t not in parse.get("company_fragments", [])] or parse.get("cjk", [])
    company = ""
    for tok in parse.get("company_fragments", []) + cjk:
        if tok and not engines.fpe.brd.broker_matches(tok) and len(tok) >= 2:
            company = tok
            break
    if not company:
        company = "測試公司" if ticker else ""
    broker = f.get("broker") or ""
    display = engines.fpe.brd.display.get(broker) if engines.fpe is not None else ""
    broker_line = ""
    if broker:
        zh = display or {"KGI": "凱基", "MS": "摩根士丹利", "GS": "高盛", "JPM": "摩根大通", "UBS": "瑞銀", "CITI": "花旗",
                         "DAIWA": "大和", "CLSA": "里昂", "MACQUARIE": "麥格理", "HUANAN": "華南永昌", "MEGA": "兆豐",
                         "CTBC": "中國信託", "CATHAY": "國泰", "PRESIDENT": "統一", "TAISHIN": "台新", "CAPITAL": "群益",
                         }.get(broker, broker)
        broker_line = f"{zh}證券投資顧問  {broker} Securities Research"
    stock = bool(ticker)
    rating = (f.get("rating") or SYNTH_RATINGS[index % 3]) if stock else ""
    tp = round(100.0 + index * 7.5, 1) if stock else None
    cp = round(tp / 1.3, 1) if stock else None
    date = f.get("date") or ""
    page_date = date or f"2026-09-{(index % 28) + 1:02d}"
    eps = {2024: round(3.0 + index * 0.11, 2), 2025: round(4.0 + index * 0.13, 2), 2026: round(5.0 + index * 0.17, 2)}
    revenue = {2024: 10_000 + index * 137, 2025: 12_000 + index * 151, 2026: 14_500 + index * 163}
    return {
        "name": name, "ticker": ticker, "company": company, "broker": broker, "broker_line": broker_line,
        "rating": rating, "target_price": tp, "current_price": cp, "date": date, "page_date": page_date,
        "eps": eps, "revenue": revenue, "stock": stock, "suffix": Path(name).suffix.lower(),
    }


def def_page_lines(t: Dict[str, Any]) -> List[Tuple[str, float, bool]]:
    """(text, size, bold) lines for the synthetic first page."""
    y, m, d = t["page_date"].split("-")
    lines: List[Tuple[str, float, bool]] = []
    if t["broker_line"]:
        lines.append((t["broker_line"], 9.5, False))
    if t["stock"]:
        lines.append((f"{t['company']}({t['ticker']} TT)  營運動能延續，評價仍具吸引力", 18.0, True))
        lines.append((f"報告日期：{y}/{m}/{d}    Bloomberg {t['ticker']} TT    Yahoo {t['ticker']}.TW", 9.5, False))
        lines.append((f"投資評等：{RATING_WORDS[t['rating']]}    目標價：NT${t['target_price']:.1f}    收盤價：NT${t['current_price']:.1f}", 11.0, True))
    else:
        import re as _re
        lines.append((_re.sub(r"[\d_\-\s]+$", "", Path(t["name"]).stem[:36]) or "市場觀察", 18.0, True))
        lines.append((f"報告日期：{y}/{m}/{d}", 9.5, False))
    lines.append(("分析師 王小明  analyst@example-research.com  (02)2181-8888", 8.5, False))
    if t["stock"]:
        lines.append((f"我們預估{t['company']} 2025 年稀釋 EPS {t['eps'][2025]:.2f} 元，2026 年 {t['eps'][2026]:.2f} 元。", 10.0, False))
        lines.append(("主要動能來自 AI 伺服器需求、產品組合改善與新產能開出，毛利率可望維持在高檔。", 10.0, False))
        lines.append(("催化因素：新客戶認證通過、下半年旺季；風險：匯率波動與原物料成本上升。", 10.0, False))
    else:
        lines.append(("市場維持震盪整理，資金流向 address 記憶體與散熱族群；本文不含個股評等與目標價。", 10.0, False))
        lines.append(("盤面觀察：外資期貨淨部位小幅減碼，成交量能仍有支撐。", 10.0, False))
    return lines


def def_table_rows(t: Dict[str, Any]) -> List[List[str]]:
    return [
        ["項目 (NT$ 百萬元)", "2024A", "2025E", "2026E"],
        ["營收", f"{t['revenue'][2024]:,}", f"{t['revenue'][2025]:,}", f"{t['revenue'][2026]:,}"],
        ["毛利率(%)", "38.5", "39.2", "40.1"],
        ["稅後淨利", f"{int(t['revenue'][2024]*0.12):,}", f"{int(t['revenue'][2025]*0.125):,}", f"{int(t['revenue'][2026]*0.13):,}"],
        ["每股盈餘(元)", f"{t['eps'][2024]:.2f}", f"{t['eps'][2025]:.2f}", f"{t['eps'][2026]:.2f}"],
    ]


def def_write_pdf(path: Path, t: Dict[str, Any]) -> None:
    import fitz  # type: ignore
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    y = 60.0
    for text, size, bold in def_page_lines(t):
        page.insert_text((50, y), text, fontname="china-t", fontsize=size + (1.5 if bold else 0.0))
        y += size * 1.9
    if t["stock"]:
        rows = def_table_rows(t)
        x0, top, col_w, row_h = 50.0, y + 10.0, [150.0, 100.0, 100.0, 100.0], 20.0
        for r_idx, row in enumerate(rows):
            x = x0
            for c_idx, cell in enumerate(row):
                rect = fitz.Rect(x, top + r_idx * row_h, x + col_w[c_idx], top + (r_idx + 1) * row_h)
                page.draw_rect(rect, color=(0, 0, 0), width=0.7)
                page.insert_text((x + 4, top + r_idx * row_h + 14), cell, fontname="china-t", fontsize=9.5)
                x += col_w[c_idx]
        y = top + len(rows) * row_h + 20
    page.insert_text((50, 800), "本報告僅供參考，不構成投資建議。Disclosure: synthetic sample generated for testing only.", fontname="china-t", fontsize=7.5)
    doc.save(str(path))
    doc.close()


def def_write_docx(path: Path, t: Dict[str, Any]) -> None:
    import docx  # type: ignore
    document = docx.Document()
    for text, size, bold in def_page_lines(t):
        para = document.add_paragraph()
        run = para.add_run(text)
        run.bold = bool(bold)
        try:
            from docx.shared import Pt  # type: ignore
            run.font.size = Pt(size)
        except Exception:  # noqa: BLE001
            pass
    if t["stock"]:
        rows = def_table_rows(t)
        table = document.add_table(rows=len(rows), cols=len(rows[0]))
        table.style = "Table Grid"
        for r_idx, row in enumerate(rows):
            for c_idx, cell in enumerate(row):
                table.cell(r_idx, c_idx).text = cell
    document.save(str(path))


def def_write_txt(path: Path, t: Dict[str, Any]) -> None:
    lines = [text for text, _, _ in def_page_lines(t)]
    if t["stock"]:
        lines += ["\t".join(r) for r in def_table_rows(t)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def def_build_corpus(engines: Engines, names: Sequence[str], out_dir: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    rows: List[Dict[str, Any]] = []
    truth: List[Dict[str, Any]] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    have_fitz, have_docx = def_has("fitz"), def_has("docx")
    for index, name in enumerate(names):
        t = def_synthetic_truth(engines, name, index)
        path = out_dir / name
        try:
            if t["suffix"] == ".pdf":
                if not have_fitz:
                    rows.append(def_row("G05 CORPUS", name, "SKIP", "pymupdf missing: " + DEP_INSTALL_HINT)); continue
                def_write_pdf(path, t)
            elif t["suffix"] == ".docx":
                if not have_docx:
                    rows.append(def_row("G05 CORPUS", name, "SKIP", "python-docx missing: " + DEP_INSTALL_HINT)); continue
                def_write_docx(path, t)
            elif t["suffix"] == ".txt":
                def_write_txt(path, t)
            else:
                path.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 64)   # image placeholder: OCR_REQUIRED path
                t["ocr"] = True
            t["path"] = str(path)
            t["sha256"] = def_sha256(path)
            truth.append(t)
            rows.append(def_row("G05 CORPUS", name, "PASS", f"{path.stat().st_size} bytes"))
        except Exception as error:  # noqa: BLE001
            rows.append(def_row("G05 CORPUS", name, "FAIL", f"{error.__class__.__name__}: {error}"[:200]))
    return rows, truth


# ---------------------------------------------------------------------------
# 04. document gates
# ---------------------------------------------------------------------------
def def_near(a: Any, b: Any, tol: float = 0.011) -> bool:
    try:
        if a in (None, "") or b in (None, ""):
            return (a in (None, "")) and (b in (None, ""))
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False


def def_gate_batch(engines: Engines, samples: Path, out_dir: Path, truth: List[Dict[str, Any]], real_mode: bool,
                   run_id: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    db = engines.database
    rows: List[Dict[str, Any]] = []
    if db is None:
        return [def_row("G06 BATCH", "database engine", "FAIL", "engine not loaded")], {}
    for dep in ("pandas", "pyarrow"):
        if not def_has(dep):
            return [def_row("G06 BATCH", "dependencies", "SKIP", f"{dep} missing (DEPENDENCY_MISSING): " + DEP_INSTALL_HINT)], {}
    args = argparse.Namespace(input=str(samples), output=str(out_dir / "vrn_db"), ticker_ssot="", broker_ssot="", rating_ssot="",
                              online_name_update=False, csv=True, json=True, duckdb=False, google_sheet="", google_credentials="",
                              run_id=run_id, self_test=False)
    import contextlib, io
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            summary = db.process_batch(args)
    except Exception as error:  # noqa: BLE001
        return [def_row("G06 BATCH", "process_batch", "FAIL", f"{error.__class__.__name__}: {error}\n{traceback.format_exc()[-600:]}")], {}
    checkpoint = json.loads((out_dir / "vrn_db" / db.BATCH_CHECKPOINT_JSON_NAME).read_text(encoding="utf-8"))
    basic = json.loads((out_dir / "vrn_db" / db.BASICINFO_JSON_NAME).read_text(encoding="utf-8"))
    financial = json.loads((out_dir / "vrn_db" / db.FINANCIALDATA_JSON_NAME).read_text(encoding="utf-8"))
    by_name = {r.get("SourceFileName"): r for r in basic if r.get("RunID") == run_id}
    fin_by_report: Dict[str, List[Dict[str, Any]]] = {}
    for r in financial:
        fin_by_report.setdefault(r.get("ReportID", ""), []).append(r)
    oracle = def_load_oracle()
    truth_by_name = {t["name"]: t for t in truth}
    for item in checkpoint.get("Files", []):
        name = Path(item["path"]).name
        if item.get("status") == "SKIP_OCR_REQUIRED":
            rows.append(def_row("G06 BATCH", name, "WARN", "OCR_REQUIRED (image input, OCR not wired)", stage="S06 OCR_ROUTE"))
            continue
        if item.get("status") != "OK":
            rows.append(def_row("G06 BATCH", name, "FAIL", str(item.get("error", ""))[:400], stage="S02 EXTRACT"))
            continue
        row = by_name.get(name)
        if row is None:
            rows.append(def_row("G06 BATCH", name, "FAIL", "no BasicInfo row for this run", stage="S09 FINANCIAL_SSOT"))
            continue
        problems: List[str] = []
        warns: List[str] = []
        t = truth_by_name.get(name)
        fins = fin_by_report.get(row.get("ReportID", ""), [])
        if t is not None and not real_mode:
            if (row.get("TW_TICKER") or "") != t["ticker"]:
                problems.append(f"ticker {row.get('TW_TICKER')!r} != {t['ticker']!r}")
            exp_date = t["date"] or t["page_date"]
            if (row.get("ReportDate") or "") != exp_date:
                problems.append(f"date {row.get('ReportDate')!r} != {exp_date!r}")
            if t["broker"] and (row.get("Broker") or "") != t["broker"]:
                problems.append(f"broker {row.get('Broker')!r} != {t['broker']!r}")
            if (row.get("Rating") or "") != t["rating"]:
                problems.append(f"rating {row.get('Rating')!r} != {t['rating']!r}")
            if not def_near(row.get("TargetPrice"), t["target_price"]):
                problems.append(f"target {row.get('TargetPrice')!r} != {t['target_price']!r}")
            if not def_near(row.get("CurrentPrice"), t["current_price"]):
                problems.append(f"current {row.get('CurrentPrice')!r} != {t['current_price']!r}")
            if t["stock"] and t["suffix"] in (".pdf", ".docx"):
                table_stack = (def_has("pdfplumber") or def_has("fitz")) if t["suffix"] == ".pdf" else def_has("docx")
                eps_rows = [r for r in fins if r.get("MetricName") == "EPS" and r.get("FiscalYear") in (2025, 2025.0)]
                if not table_stack:
                    warns.append("table extractor missing (DEPENDENCY_MISSING): " + DEP_INSTALL_HINT)
                elif not eps_rows or not def_near(eps_rows[0].get("Value"), t["eps"][2025]):
                    problems.append(f"EPS 2025 {[r.get('Value') for r in eps_rows]} != {t['eps'][2025]}")
                if row.get("TriCodeVerdict") != "PASS":
                    problems.append(f"tri-code {row.get('TriCodeVerdict')!r} != PASS")
            elif not t["stock"] and row.get("TriCodeVerdict") not in ("N/A", ""):
                problems.append(f"tri-code {row.get('TriCodeVerdict')!r} for a non-stock file")
        else:
            o = oracle.get(name)
            if o is not None:
                exp_t = (o.get("ticker_candidates") or [""])[0]
                if exp_t and (row.get("TW_TICKER") or "") != exp_t:
                    problems.append(f"ticker {row.get('TW_TICKER')!r} != oracle {exp_t!r}")
                if o.get("report_date") and (row.get("ReportDate") or "") != o["report_date"]:
                    problems.append(f"date {row.get('ReportDate')!r} != oracle {o['report_date']!r}")
                exp_b = (o.get("broker") or {}).get("value") or ""
                if exp_b and (row.get("Broker") or "") != exp_b:
                    problems.append(f"broker {row.get('Broker')!r} != oracle {exp_b!r}")
            if row.get("TriCodeVerdict") == "MISMATCH":
                problems.append("tri-code MISMATCH between filename and first page")
            if not (row.get("ReportDate") or ""):
                warns.append("no report date")
            if not (row.get("Broker") or ""):
                warns.append("no broker")
            if row.get("SourceFormat") == "pdf" and not fins:
                warns.append("no financial rows (no ruled table found)")
            issues = str(row.get("ValidationIssues") or "")
            if "failed" in issues.lower() or "No PDF extraction engine" in issues:
                problems.append(issues[:200])
        status = "FAIL" if problems else ("WARN" if warns else "PASS")
        rows.append(def_row("G06 BATCH", name, status, "; ".join(problems + warns),
                            ticker=row.get("TW_TICKER"), date=row.get("ReportDate"), broker=row.get("Broker"),
                            rating=row.get("Rating"), target=row.get("TargetPrice"), fin_rows=len(fins),
                            tri_code=row.get("TriCodeVerdict"), confidence=row.get("ConfidenceScore"),
                            stage="S09 FINANCIAL_SSOT" if problems else "S10 SUMMARIZER"))
    parquet_rows = []
    try:
        import pandas as pd  # type: ignore
        b = pd.read_parquet(out_dir / "vrn_db" / db.BASICINFO_PARQUET_NAME)
        f = pd.read_parquet(out_dir / "vrn_db" / db.FINANCIALDATA_PARQUET_NAME)
        typed = all(str(b[c].dtype).startswith("float") for c in db.BASICINFO_NUMERIC_COLUMNS if c in b.columns)
        parquet_rows.append(def_row("G06 BATCH", "parquet typed and readable", "PASS" if typed else "FAIL",
                                    f"basic={len(b)} financial={len(f)} typed={typed}"))
    except Exception as error:  # noqa: BLE001
        parquet_rows.append(def_row("G06 BATCH", "parquet typed and readable", "FAIL", f"{error.__class__.__name__}: {error}"[:300]))
    return rows + parquet_rows, summary


def def_gate_first_page(engines: Engines, truth: List[Dict[str, Any]], samples: Path, real_mode: bool) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    fpe, module = engines.fpe, engines.first_page
    if fpe is None or module is None:
        return [def_row("G07 FIRSTPAGE", "first-page engine", "FAIL", "engine not loaded")]
    if not (def_has("pdfplumber") or def_has("fitz")):
        return [def_row("G07 FIRSTPAGE", "dependencies", "SKIP", "pdfplumber/pymupdf missing (DEPENDENCY_MISSING): " + DEP_INSTALL_HINT)]
    files = truth if truth else [{"name": p.name, "path": str(p), "suffix": p.suffix.lower()} for p in sorted(samples.rglob("*")) if p.is_file()]
    oracle = def_load_oracle()
    for t in files:
        name, path, suffix = t["name"], Path(t["path"]), t["suffix"]
        if suffix not in (".pdf", ".docx"):
            continue
        try:
            got = module._chars_from_pdf(str(path)) if suffix == ".pdf" else module._chars_from_docx(str(path))
            chars, size = (got if got is not None else (None, (None, None)))
            out = fpe.run(name, chars=chars, page_width=size[0], page_height=size[1])
        except Exception as error:  # noqa: BLE001
            rows.append(def_row("G07 FIRSTPAGE", name, "FAIL", f"{error.__class__.__name__}: {error}"[:300], stage="S05 ACCEL_MOUNT"))
            continue
        problems: List[str] = []
        warns: List[str] = []
        if not real_mode and "ticker" in t:
            if (out["ticker"]["ticker"] or "") != t["ticker"]:
                problems.append(f"ticker {out['ticker']['ticker']!r} != {t['ticker']!r}")
            if (out["rating"]["canonical"] or "") != t["rating"]:
                problems.append(f"rating {out['rating']['canonical']!r} != {t['rating']!r}")
            if not def_near(out["target_prices"]["primary"], t["target_price"]):
                problems.append(f"target {out['target_prices']['primary']!r} != {t['target_price']!r}")
            if not def_near(out["current_price"], t["current_price"]):
                problems.append(f"current {out['current_price']!r} != {t['current_price']!r}")
            if t["broker"] and (out["broker"] or "") != t["broker"]:
                problems.append(f"broker {out['broker']!r} != {t['broker']!r}")
            if t["stock"] and out["tri_code"]["verdict"] != "PASS":
                problems.append(f"tri-code {out['tri_code']['verdict']}")
            if out["xv_filename_vs_page"]["verdict"] != "PASS":
                problems.append("filename vs page " + json.dumps(out["xv_filename_vs_page"]["fields"], ensure_ascii=False)[:160])
            if t["stock"] and not out["layout"]["company_name"]:
                problems.append("company name not found in layout")
            if not out["report_date"]:
                problems.append("no report date")
        else:
            o = oracle.get(name)
            if o is not None:
                exp_t = (o.get("ticker_candidates") or [""])[0]
                if exp_t and (out["ticker"]["ticker"] or "") != exp_t:
                    problems.append(f"ticker {out['ticker']['ticker']!r} != oracle {exp_t!r}")
            if out["tri_code"]["verdict"] == "MISMATCH":
                problems.append("tri-code MISMATCH")
            if out["xv_filename_vs_page"]["verdict"] == "FAIL":
                problems.append("filename vs page FAIL " + json.dumps(out["xv_filename_vs_page"]["fields"], ensure_ascii=False)[:160])
            if not chars:
                warns.append("no text layer (scan? OCR_REQUIRED)")
            if not out["report_date"]:
                warns.append("no report date")
        status = "FAIL" if problems else ("WARN" if warns else "PASS")
        rows.append(def_row("G07 FIRSTPAGE", name, status, "; ".join(problems + warns), ticker=out["ticker"]["ticker"],
                            rating=out["rating"]["canonical"], target=out["target_prices"]["primary"], broker=out["broker"],
                            tri_code=out["tri_code"]["verdict"], company=out["layout"]["company_name"],
                            stage="S07 NLP_ENRICH" if problems else "S10 SUMMARIZER"))
    return rows


def def_gate_idempotent(engines: Engines, samples: Path, out_dir: Path, run_id: str) -> List[Dict[str, Any]]:
    db = engines.database
    if db is None or not (def_has("pandas") and def_has("pyarrow")):
        return [def_row("G08 IDEMPOTENT", "second batch", "SKIP", "DEPENDENCY_MISSING")]
    try:
        import pandas as pd  # type: ignore
        before = len(pd.read_parquet(out_dir / "vrn_db" / db.BASICINFO_PARQUET_NAME))
        args = argparse.Namespace(input=str(samples), output=str(out_dir / "vrn_db"), ticker_ssot="", broker_ssot="", rating_ssot="",
                                  online_name_update=False, csv=False, json=False, duckdb=False, google_sheet="", google_credentials="",
                                  run_id=run_id + "_R2", self_test=False)
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            db.process_batch(args)
        after = len(pd.read_parquet(out_dir / "vrn_db" / db.BASICINFO_PARQUET_NAME))
        ok = before == after
        return [def_row("G08 IDEMPOTENT", "second batch keeps one row per ReportID", "PASS" if ok else "FAIL", f"before={before} after={after}")]
    except Exception as error:  # noqa: BLE001
        return [def_row("G08 IDEMPOTENT", "second batch", "FAIL", f"{error.__class__.__name__}: {error}"[:300])]


def def_gate_read_only(samples: Path, before: Dict[str, str]) -> List[Dict[str, Any]]:
    changed = []
    for path in sorted(samples.rglob("*")):
        if path.is_file():
            digest = def_sha256(path)
            rel = str(path.relative_to(samples))
            if rel in before and before[rel] != digest:
                changed.append(rel)
    missing = [rel for rel in before if not (samples / rel).exists()]
    ok = not changed and not missing
    return [def_row("G09 READONLY", f"{len(before)} sample files unchanged", "PASS" if ok else "FAIL",
                    ("changed: " + ", ".join(changed[:5])) if changed else ("missing: " + ", ".join(missing[:5]) if missing else ""))]


# ---------------------------------------------------------------------------
# 05. auto-fix strategies
# ---------------------------------------------------------------------------
def def_auto_fix(engines: Engines, rows: List[Dict[str, Any]], applied: List[str]) -> List[str]:
    """Pick runtime repairs for the failure classes seen this round. Returns the fixes applied now."""
    fixes: List[str] = []
    db = engines.database
    text = "\n".join(str(r.get("detail", "")) for r in rows if r["status"] == "FAIL")
    if db is not None and ("failed:" in text or "No PDF extraction engine" in text or "no text layer" in text) and "F1 pdf-engine-order" not in applied:
        db.PDF_ENGINE_ORDER.reverse()
        fixes.append("F1 pdf-engine-order -> " + "/".join(db.PDF_ENGINE_ORDER))
    if db is not None and ("first_page_engine" in text or "FirstPageEngine" in text) and "F2 first-page-hook-off" not in applied:
        db.FIRST_PAGE_ENGINE_ENABLED = False
        fixes.append("F2 first-page-hook-off")
    if any("DEPENDENCY_MISSING" in str(r.get("detail", "")) for r in rows) and "F3 dependency-note" not in applied:
        fixes.append("F3 dependency-note: " + DEP_INSTALL_HINT)
    if any(r["gate"] == "G05 CORPUS" and r["status"] == "FAIL" for r in rows) and "F4 corpus-regenerate" not in applied:
        fixes.append("F4 corpus-regenerate")
    return fixes


# ---------------------------------------------------------------------------
# 06. loop + reports
# ---------------------------------------------------------------------------
def def_verdict(rows: List[Dict[str, Any]]) -> str:
    statuses = {r["status"] for r in rows}
    if "FAIL" in statuses:
        return "RED"
    if "WARN" in statuses or "SKIP" in statuses:
        return "AMBER"
    return "GREEN"


def def_run_round(engines: Engines, args: argparse.Namespace, workdir: Path, round_no: int, corpus_names: List[str],
                  state: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    rows += def_gate_compile()
    rows += def_gate_selftest(engines)
    rows += def_gate_filename_oracle(engines)
    if not args.no_audit:
        rows += def_gate_audit(workdir)
    samples = state.get("samples")
    truth: List[Dict[str, Any]] = state.get("truth", [])
    real_mode = bool(state.get("real_mode"))
    if samples is None or state.get("regenerate"):
        if args.samples and Path(args.samples).is_dir() and any(p.is_file() for p in Path(args.samples).rglob("*")) and not args.synthetic:
            samples = Path(args.samples)
            real_mode = True
            truth = []
            rows.append(def_row("G05 CORPUS", str(samples), "PASS", f"real samples: {sum(1 for p in samples.rglob('*') if p.is_file())} files"))
        else:
            if not def_has("fitz"):
                rows.append(def_row("G05 CORPUS", "synthetic corpus", "SKIP", "pymupdf missing, no real samples (DEPENDENCY_MISSING): " + DEP_INSTALL_HINT))
                samples = None
            else:
                samples = workdir / "samples"
                if samples.exists():
                    shutil.rmtree(samples)
                corpus_rows, truth = def_build_corpus(engines, corpus_names, samples)
                rows += corpus_rows
                real_mode = False
        state.update({"samples": samples, "truth": truth, "real_mode": real_mode, "regenerate": False})
    if samples is not None:
        before = {str(p.relative_to(samples)): def_sha256(p) for p in sorted(samples.rglob("*")) if p.is_file()}
        out_dir = workdir / f"round{round_no}"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True)
        run_id = f"VRN_AUTOTEST_R{round_no}"
        batch_rows, summary = def_gate_batch(engines, samples, out_dir, truth, real_mode, run_id)
        rows += batch_rows
        state["last_summary"] = summary
        state["last_out"] = str(out_dir)
        rows += def_gate_first_page(engines, truth, samples, real_mode)
        if summary:
            rows += def_gate_idempotent(engines, samples, out_dir, run_id)
        rows += def_gate_read_only(samples, before)
    return rows


def def_render_html(report: Dict[str, Any]) -> str:
    colour = {"PASS": "#16a34a", "WARN": "#f59e0b", "SKIP": "#6b7280", "FAIL": "#dc2626"}
    parts = ["<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VRN AutoTest</title>",
             "<style>body{font-family:-apple-system,Segoe UI,sans-serif;margin:24px;color:#1f2937;font-size:13px;background:#fbfaf7}",
             "table{border-collapse:collapse;width:100%;background:#fff}th,td{border-bottom:1px solid #e5e7eb;padding:6px 8px;text-align:left;vertical-align:top}",
             "th{background:#f3f4f6;position:sticky;top:0}.pill{display:inline-block;padding:1px 8px;border-radius:999px;color:#fff;font-weight:600}",
             ".cards{display:grid;grid-template-columns:repeat(6,minmax(110px,1fr));gap:10px;margin:14px 0}.card{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:10px}",
             ".card b{display:block;font-size:20px}</style></head><body>",
             f"<h1>VRN 自動測試迴圈 {html.escape(LOOP_VERSION)} · {html.escape(report['verdict'])}</h1>",
             f"<div>樣本：{html.escape(str(report.get('samples')))} · 模式：{'實檔' if report.get('real_mode') else '合成語料'} · 輪數：{report['rounds_run']}/{report['rounds_max']} · {html.escape(report['generated'])}</div>",
             "<div class='cards'>"]
    for key in ("PASS", "WARN", "SKIP", "FAIL"):
        parts.append(f"<div class='card'>{key}<b style='color:{colour[key]}'>{report['counts'].get(key, 0)}</b></div>")
    parts.append(f"<div class='card'>修正<b>{len(report['fixes_applied'])}</b></div><div class='card'>檔案<b>{report.get('file_count', 0)}</b></div></div>")
    if report["fixes_applied"]:
        parts.append("<p>自動修正：" + " · ".join(html.escape(f) for f in report["fixes_applied"]) + "</p>")
    for rnd in report["rounds"]:
        parts.append(f"<h2>第 {rnd['round']} 輪 · {html.escape(rnd['verdict'])}</h2><table><thead><tr><th>閘門</th><th>項目</th><th>狀態</th><th>段</th><th>細節</th></tr></thead><tbody>")
        for r in rnd["rows"]:
            parts.append(f"<tr><td>{html.escape(r['gate'])}</td><td>{html.escape(str(r['name']))}</td>"
                         f"<td><span class='pill' style='background:{colour.get(r['status'], '#6b7280')}'>{r['status']}</span></td>"
                         f"<td>{html.escape(str(r.get('stage', '')))}</td><td>{html.escape(str(r.get('detail', ''))[:400])}</td></tr>")
        parts.append("</tbody></table>")
    parts.append("<p>LIVE 關 · 不連網 · 不設定 consent · 輸出只寫到 --out</p></body></html>")
    return "".join(parts)


def def_main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--samples", default="", help=f"測試檔案資料夾（Windows 預設 {DEFAULT_SAMPLES_WINDOWS} 若存在）")
    parser.add_argument("--out", default="", help="輸出資料夾（預設暫存目錄 VRN_AutoTest_<時間>）")
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS, help="最多幾輪自動修正")
    parser.add_argument("--synthetic", action="store_true", help="忽略實檔，一律用合成語料")
    parser.add_argument("--names", default="", help="合成語料檔名清單（每行一個）；預設 roster + 稽核包 106 名")
    parser.add_argument("--limit", type=int, default=0, help="合成語料最多幾個檔（0 = 全部）")
    parser.add_argument("--no-audit", action="store_true", help="跳過 audit_ssot.py")
    parser.add_argument("--json", default="", help="報告 JSON 路徑")
    parser.add_argument("--html", default="", help="報告 HTML 路徑")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass
    if not args.samples and os.name == "nt" and Path(DEFAULT_SAMPLES_WINDOWS).is_dir():
        args.samples = DEFAULT_SAMPLES_WINDOWS
    workdir = Path(args.out) if args.out else Path(tempfile.gettempdir()) / f"VRN_AutoTest_{time.strftime('%Y%m%dT%H%M%S')}"
    workdir.mkdir(parents=True, exist_ok=True)
    engines = Engines()
    if args.names:
        names = [line.strip() for line in Path(args.names).read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    else:
        names = def_load_roster()
        for extra in def_load_oracle():
            if extra not in names:
                names.append(extra)
    if args.limit:
        names = names[: args.limit]
    state: Dict[str, Any] = {}
    rounds: List[Dict[str, Any]] = []
    fixes_applied: List[str] = []
    final_rows: List[Dict[str, Any]] = []
    for round_no in range(1, max(1, args.rounds) + 1):
        rows = def_run_round(engines, args, workdir, round_no, names, state)
        verdict = def_verdict(rows)
        rounds.append({"round": round_no, "verdict": verdict, "rows": rows,
                       "counts": {k: sum(1 for r in rows if r["status"] == k) for k in ("PASS", "WARN", "SKIP", "FAIL")}})
        final_rows = rows
        if not args.quiet:
            print(f"[ROUND {round_no}] {verdict} " + " ".join(f"{k}={v}" for k, v in rounds[-1]["counts"].items()))
            for r in rows:
                if r["status"] in ("FAIL", "WARN"):
                    print(f"   {r['status']:4} {r['gate']:14} {str(r['name'])[:60]:60} {str(r.get('detail', ''))[:140]}")
        if verdict != "RED":
            break
        fixes = def_auto_fix(engines, rows, fixes_applied)
        if not fixes:
            break
        fixes_applied += fixes
        if any(f.startswith("F4") for f in fixes):
            state["regenerate"] = True
        if not args.quiet:
            print("[FIX] " + " · ".join(fixes))
    counts = {k: sum(1 for r in final_rows if r["status"] == k) for k in ("PASS", "WARN", "SKIP", "FAIL")}
    verdict = def_verdict(final_rows)
    report = {
        "loop": "VRN_AutoTestLoop " + LOOP_VERSION, "generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "verdict": verdict,
        "samples": str(state.get("samples") or ""), "real_mode": bool(state.get("real_mode")), "workdir": str(workdir),
        "rounds_run": len(rounds), "rounds_max": args.rounds, "counts": counts, "fixes_applied": fixes_applied,
        "file_count": len(state.get("truth") or []) or (sum(1 for p in Path(state["samples"]).rglob("*") if p.is_file()) if state.get("samples") else 0),
        "engines": {k: str(v) for k, v in ENGINE_FILES.items()}, "engine_errors": engines.errors,
        "dependencies": {m: def_has(m) for m in ("pandas", "pyarrow", "pdfplumber", "fitz", "docx", "duckdb")},
        "last_summary": state.get("last_summary", {}), "rounds": rounds,
    }
    json_path = Path(args.json) if args.json else workdir / "VRN_AutoTest_Report.json"
    html_path = Path(args.html) if args.html else workdir / "VRN_AutoTest_Report.html"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    html_path.write_text(def_render_html(report), encoding="utf-8")
    if not args.quiet:
        print(f"[DONE] {verdict} · rounds={len(rounds)} · {json_path} · {html_path}")
    if state.get("samples") is None and not engines.errors and counts["FAIL"] == 0:
        return 2 if os.environ.get("VRN_AUTOTEST_REQUIRE_CORPUS") == "1" else 0
    return 0 if counts["FAIL"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(def_main())
