# -*- coding: utf-8 -*-
"""
VRN_AutoTestLoop v0104 — 自動測試、自動修正、直到成功（或說清楚卡在哪一段）

v0103→v0104(母倉 批731;操作員 2026-09-24「PS PY檔案都要依規定裝加速器  剛剛跑好慢」「自測報告要自動跳出來」):
  工作站實錄:106 份實檔 G06 入庫 20 分、G07 6.6 分,G08 冪等把 106 份**整批再入庫一次**,第六步撞 1800 秒天花板被停。
  ① G08 改抽樣:平均抽 12 檔(--g08-sample N;首尾兩檔必在,檔名以報告日開頭,尾檔 = 最新一份)再入庫一次,
     列數仍必須不變——冪等是 upsert(ReportID)的性質,
     不必把 106 份重新擷取一遍才驗得出;要全批:--g08-full。明細寫明「抽 12/106 檔」。G11 / G12 讀的是 G06 寫的 JSON,
     G08 不重寫它,抽樣不影響它們看到的列。
  ② 起跑先 VIA_ACCEL.activate()(批323 啟動律:載 Celeritas、套執行緒預算),印一行 [加速器] 在位 / 缺席與原因——
     橋一直在,但從來沒有啟動過。
  ③ 進度協定:一輪的總數改成 G06 n + G07 n + G08 抽樣數,百分比一路往上,不會在 G08 開頭倒退。
  證據核心同批:每一頁、每一份附錄小字對同一個檔只解析一次(首頁、附錄、欄表、G07、G08 原本各自重讀)。
  ④ --selftest 的單元測試改成一檔一個子行程並排跑(行程數同整批平行池:VRN_BATCH_WORKERS > 加速器執行緒預算 >
     CPU−1;大檔先跑):六層鏈 V2 敲這扇門時節點天花板 180 秒(格子 60 秒),序跑 104 支會撞天花板 → 那一格
     「沒跑完=沒有結論」,V2 整層陪它等。子行程在父行程被天花板砍掉時自己收(stdin 關了就走),不留著佔住庫。

v0102→v0103(母倉 批729;操作員 2026-09-24「報告後小字體不相關附錄可抓到局部識別券商」「報告後方小字級附錄可抓到所有評等法可增加到同義字」):
  G07 把檔案路徑交給首頁引擎(PDF 才讀附錄);每檔記下附錄小字的券商、層級、是否用上、與檔名是否衝突與評等定義。
  報告多 appendix 摘要與 appendix_new_rating_words;RATING_SCALE_CANDIDATES.json 落在本輪工作夾——候選而已,
  同義字只增不減要經樞紐,迴圈不寫任何冊。主控台多印一行 [附錄]。
  操作員同日「所有目標價及各前一日的價格都要換成ADJ CLOSE 上漲空間都要用最新的ADJ CLOSE」:首頁引擎 v0104 的上漲空間
  改走 ENG073 adj_quote(最新 ADJ CLOSE);每檔記下 ADJ 狀態,報告多 adj 摘要(算出幾檔、其餘各卡在哪一種),
  主控台多印一行 [ADJ]。這一行是量測,不是關卡:缺價(例如上市所價還沒進庫)照實報名字,不判 FAIL。
  批730:[ADJ] 那一行多印「因子分母」分佈(RAW_EXCHANGE 交易所 · PAGE_PRICE 報告頁面價 · YAHOO_CLOSE 未核)——
  Yahoo 的 close 會事後按配股回調,分母用它的那幾份就是還沒被獨立價核過的。
v0101→v0102(母倉 批728 收回:姊妹倉 festive-ptolemy 41ce6d4/34d91ac 的成果搬回母倉正位):
    +--selftest 自測門(VRN/tests 全部單元測試 + 合成語料 8 檔一輪):六層鏈與全格子都敲這一扇;
    G10 母倉模式(工具讀正本、三支自測、拒絕清單/負控/同義字對帳照跑);名冊讀收容副本;每檔印 [進度] k/K。
    G03 FILENAME 的期望值會認母倉 批679/批702 拒絕清單——稽核包 oracle 寫著 broker=GF 的檔,
    在母倉被 CGC_MDL177 從每一張別名表清掉,檔名層**不得**解出它;期望改成空字串,並在明細具名
    「清除 N 件」。解出被拒券商仍是 FAIL(不是放寬,是把尺對到母倉的法)。

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
    G10 VCGC         母倉 VCGC 鏡像（scripts/VIA_VCGC_Sync.py --check）逐位元相符、CGC_MDL181/182 自測、
                     批679 拒絕清單不外洩（陸券別名不得解出券商）且負控（中信 / 國泰 / 里昂）照常解出
    G11 TRUTH        `--truth`（人工真值，只放在操作員手上、不入庫）：兩支引擎逐欄對真值；
                     類型／代號／券商／日期／評等／目標價／現價 錯一格 = FAIL，公司名／分析師 < 90% = WARN
    G12 FIELDSPEC    母倉 15 欄規格（VIA_VRN_FieldSpec_SSOT）六態，用 CGC_MDL181 的 _state 判；
                     GATED（要觸網）/ NOT_WIRED 照實列，不是壞掉

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
import io
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

LOOP_VERSION = "v0104"
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
    "evidence_core": HERE / "VRN_Evidence_Core.py",
}
VCGC_SYNC = REPO_ROOT / "scripts" / "VIA_VCGC_Sync.py"
LAST_FIRST_PAGE: Dict[str, Dict[str, Any]] = {}      # per-file first-page answers of the current round (G11)
LAST_APPENDIX: Dict[str, Dict[str, Any]] = {}        # v0103 (批729): per-file appendix small print (broker + rating scale)
LAST_ADJ: Dict[str, Dict[str, Any]] = {}             # v0103 (批729): per-file ADJ CLOSE upside (state, value, reason)
LAST_SAMPLES: Dict[str, Path] = {}                    # file name -> sample path of the current round
TRUTH_CRITICAL = ("type", "ticker", "broker", "page_date", "rating", "target_price", "current_price")
AUDIT_DIR = VRN_ROOT / "references" / "intake" / "VIA_SSOT_Additive_Audit_v0100"
# v0102(母倉 批728):母倉沒有 src/lib/via/,讀收容夾裡位元相同的名冊(唯讀,L03);兩處都沒有才回空。
ROSTER_CANDIDATES = (
    REPO_ROOT / "src" / "lib" / "via" / "incoming-roster.ts",
    REPO_ROOT / "supportive modules" / "references" / "intake" / "VIA_GrokConsole_AuroraAcorn_b383" / "src" / "lib" / "via" / "incoming-roster.ts",
)
ROSTER_TS = next((c for c in ROSTER_CANDIDATES if c.is_file()), ROSTER_CANDIDATES[0])
SYNTH_RATINGS = ["BUY", "HOLD", "SELL"]
RATING_WORDS = {"BUY": "買進", "HOLD": "中立", "SELL": "賣出", "NOT_RATED": "未評等", "ADD": "逢低買進"}
DEP_INSTALL_HINT = "pip install pandas pyarrow pdfplumber pymupdf python-docx"
STATUS_ORDER = {"FAIL": 0, "WARN": 1, "SKIP": 2, "PASS": 3}
PROGRESS: Dict[str, Any] = {"quiet": False, "stream": None}   # set in def_main (console captured before any redirect)
PROGRESS_LINE = re.compile(r"^\[(\d+)/(\d+)\] VRN processing: (.+)$")


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


def def_say(text: str) -> None:
    """One progress line on the console (the run takes minutes; silence looks like a hang)."""
    if not PROGRESS["quiet"]:
        stream = PROGRESS.get("stream") or sys.__stdout__ or sys.stdout
        stream.write(time.strftime("%H:%M:%S ") + text + "\n")
        stream.flush()


PASS_INDEX = {"G06": 0, "G07": 1, "G08": 2}    # 三批逐檔:入庫 · 首頁 · 冪等第二批
G08_SAMPLE = 12                                 # v0104:冪等抽樣檔數(--g08-sample;--g08-full 全批)


def def_g08_pick(names: Sequence[str], sample: int, full: bool) -> List[str]:
    """v0104: the idempotency pass re-ingests an evenly spread, fixed sample of the batch (sorted names).  The first
    and the last file are always in it -- names start with the report date, so the last one is the newest report."""
    names = sorted(names)
    if full or sample <= 0 or len(names) <= sample:
        return list(names)
    if sample == 1:
        return [names[-1]]
    last = len(names) - 1
    return [names[round(i * last / (sample - 1))] for i in range(sample)]


def def_tick(prefix: str, i: int, n: int, name: str) -> None:
    """Per-file progress: the human line '[G06 12/106] name' plus the VIA protocol line '[進度] k/K …'
    (母倉 批694 協定:誰有可數的迴圈誰就印 [進度] n/N;Invoke-VIAPython 照它畫真百分比).
    K = 3 passes × n, so one round runs 0→100% instead of restarting three times.  No timestamp on the
    protocol line: the launcher's parser anchors at the line start."""
    def_say(f"   [{prefix} {i}/{n}] {name}")
    if PROGRESS["quiet"] or n <= 0:
        return
    total, offsets = PROGRESS.get("round_total"), PROGRESS.get("round_offsets") or {}
    if total and prefix in offsets:              # v0104: the round declared its real total (G08 is a sample)
        k, kk = min(offsets[prefix] + i, total), total
    else:
        k, kk = PASS_INDEX.get(prefix, 0) * n + i, 3 * n
    stream = PROGRESS.get("stream") or sys.__stdout__ or sys.stdout
    stream.write(f"[進度] {k}/{kk} {prefix} {name}\n")
    stream.flush()


class def_ProgressTee(io.TextIOBase):
    """Captures an engine's stdout like before, but echoes its per-file progress lines as '[G06 12/106] name'."""

    def __init__(self, prefix: str) -> None:
        super().__init__()
        self.prefix = prefix
        self.buffer_text = io.StringIO()
        self._pending = ""

    def write(self, text: str) -> int:
        self.buffer_text.write(text)
        self._pending += text
        while "\n" in self._pending:
            line, self._pending = self._pending.split("\n", 1)
            m = PROGRESS_LINE.match(line.strip())
            if m:
                def_tick(self.prefix, int(m.group(1)), int(m.group(2)), m.group(3))
        return len(text)

    def getvalue(self) -> str:
        return self.buffer_text.getvalue()


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
        self.core = self._load("evidence_core") if ENGINE_FILES["evidence_core"].is_file() else None
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


def def_oracle_expect(engines: Engines, row: Dict[str, Any]):
    """Oracle triple (ticker, date, broker) under the mother's law.  批679 (operator: 刪中國券商) and 批702
    purge every deny-listed broker (CGC_MDL177) from every alias table, so the filename layer must NOT
    resolve it: the expectation becomes ''.  Returns (triple, purged?)."""
    broker = (row.get("broker") or {}).get("value") or ""
    purged = False
    purge = engines.core.vcgc("purge") if engines.core is not None else None
    if broker and purge is not None:
        try:
            if purge.is_cn_canon(broker):
                broker, purged = "", True
        except Exception:  # noqa: BLE001
            pass
    return ((row.get("ticker_candidates") or [""])[0], row.get("report_date") or "", broker), purged


def def_gate_filename_oracle(engines: Engines) -> List[Dict[str, Any]]:
    rows = []
    oracle = def_load_oracle()
    if not oracle:
        return [def_row("G03 FILENAME", "oracle", "SKIP", "FILENAME_RESULTS.json absent")]
    names = list(oracle)
    roster = [n for n in def_load_roster() if n not in oracle]
    purged_names = sorted(n for n, r in oracle.items() if def_oracle_expect(engines, r)[1])
    purged_note = (f"批679 拒絕清單清除 {len(purged_names)} 件(期望空):" + ", ".join(purged_names[:4])) if purged_names else ""
    if engines.fpe is not None:
        bad = []
        for name, row in oracle.items():
            got = engines.fpe._filename_fields(name)
            exp, _ = def_oracle_expect(engines, row)
            have = (got["ticker"] or "", got["date"] or "", got["broker"] or "")
            if have != exp:
                bad.append(f"{name}: got={have} exp={exp}")
        rows.append(def_row("G03 FILENAME", f"first-page engine vs oracle ({len(names)})", "FAIL" if bad else "PASS",
                            "; ".join(bad[:6]) or purged_note, mismatches=bad))
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
                exp, _ = def_oracle_expect(engines, row)
                if have != exp:
                    bad.append(f"{name}: got={have} exp={exp}")
            rows.append(def_row("G03 FILENAME", f"database engine vs oracle ({len(names)})", "FAIL" if bad else "PASS",
                                "; ".join(bad[:6]) or purged_note, mismatches=bad))
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
    import contextlib
    buffer = def_ProgressTee("G06")
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
                # the oracle is filename-level: compare the filename date (the page date may differ and leads)
                fn_date = row.get("FilenameDate") or row.get("ReportDate") or ""
                if o.get("report_date") and fn_date != o["report_date"]:
                    problems.append(f"filename date {fn_date!r} != oracle {o['report_date']!r}")
                exp_b = (o.get("broker") or {}).get("value") or ""
                denied = exp_b and exp_b in str(row.get("BrokerDenied") or "").split(" | ")
                if exp_b and (row.get("Broker") or "") != exp_b and not denied:
                    problems.append(f"broker {row.get('Broker')!r} != oracle {exp_b!r}")
            if row.get("TriCodeVerdict") == "MISMATCH":
                problems.append("tri-code MISMATCH between filename and first page")
            stock = (row.get("ReportType") or "STOCK") == "STOCK"
            if not (row.get("ReportDate") or "") and stock:
                warns.append("no report date")
            if not (row.get("Broker") or "") and not (row.get("BrokerDenied") or "") and stock:
                warns.append("no broker")
            if row.get("SourceFormat") == "pdf" and not fins and stock:
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
    readable = [t for t in files if t["suffix"] in (".pdf", ".docx")]
    seen = 0
    for t in files:
        name, path, suffix = t["name"], Path(t["path"]), t["suffix"]
        LAST_SAMPLES[name] = path
        if suffix not in (".pdf", ".docx"):
            continue
        seen += 1
        def_tick("G07", seen, len(readable), name)
        try:
            got = module._chars_from_pdf(str(path)) if suffix == ".pdf" else module._chars_from_docx(str(path))
            chars, size = (got if got is not None else (None, (None, None)))
            out = fpe.run(name, chars=chars, page_width=size[0], page_height=size[1],
                          source_path=str(path) if suffix == ".pdf" else None)
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
            if not out["report_date"] and ((out.get("report_type") or {}).get("type", "STOCK") == "STOCK"):
                warns.append("no report date")
        LAST_FIRST_PAGE[name] = {
            "type": (out.get("report_type") or {}).get("type"), "ticker": (out.get("ticker_page") or {}).get("ticker"),
            "broker": out.get("broker"), "denied": out.get("broker_denied") or {}, "page_date": out.get("page_date"),
            "rating": out["rating"].get("canonical"), "target_price": out["target_prices"].get("primary"),
            "current_price": out.get("current_price"), "company": out.get("company_name_page"),
            "analysts": [a.get("name") for a in out.get("analysts", []) or []] + [a.get("alias") for a in out.get("analysts", []) or [] if a.get("alias")],
            "text_layer": bool(chars)}
        if out.get("appendix") is not None:
            LAST_APPENDIX[name] = {"state": out["appendix"].get("state"), "broker": out["appendix"].get("broker"),
                                   "tier": out["appendix"].get("tier"), "strong": out["appendix"].get("strong"),
                                   "used": str(out.get("broker_tier") or "").startswith("APPENDIX_"),
                                   "conflict": out.get("broker_conflict"), "n_lines": out["appendix"].get("n_lines", 0),
                                   "rating_scale": out["appendix"].get("rating_scale") or []}
        up = out.get("upside") or {}
        if up.get("basis") == "ADJ_LATEST":
            LAST_ADJ[name] = {"state": up.get("state"), "upside_adj": up.get("upside_pct"), "why": up.get("why") or "",
                              "basis": up.get("factor_basis") or "",
                              "has_target": out["target_prices"].get("primary") is not None,
                              "upside_page": (out.get("upside_page") or {}).get("upside_pct")}
        status = "FAIL" if problems else ("WARN" if warns else "PASS")
        rows.append(def_row("G07 FIRSTPAGE", name, status, "; ".join(problems + warns), ticker=out["ticker"]["ticker"],
                            rating=out["rating"]["canonical"], target=out["target_prices"]["primary"], broker=out["broker"],
                            tri_code=out["tri_code"]["verdict"], company=out["layout"]["company_name"],
                            stage="S07 NLP_ENRICH" if problems else "S10 SUMMARIZER"))
    return rows


def def_gate_idempotent(engines: Engines, samples: Path, out_dir: Path, run_id: str,
                        sample: int = G08_SAMPLE, full: bool = False) -> List[Dict[str, Any]]:
    db = engines.database
    if db is None or not (def_has("pandas") and def_has("pyarrow")):
        return [def_row("G08 IDEMPOTENT", "second batch", "SKIP", "DEPENDENCY_MISSING")]
    try:
        import pandas as pd  # type: ignore
        before = len(pd.read_parquet(out_dir / "vrn_db" / db.BASICINFO_PARQUET_NAME))
        names = [f.name for f in db.scan_input_files(Path(samples)) if f.suffix.lower() not in db.OCR_SUFFIXES]
        pick = def_g08_pick(names, sample, full)
        args = argparse.Namespace(input=str(samples), output=str(out_dir / "vrn_db"), ticker_ssot="", broker_ssot="", rating_ssot="",
                                  online_name_update=False, csv=False, json=False, duckdb=False, google_sheet="", google_credentials="",
                                  run_id=run_id + "_R2", self_test=False, only_files=pick)
        import contextlib
        with contextlib.redirect_stdout(def_ProgressTee("G08")):
            db.process_batch(args)
        after = len(pd.read_parquet(out_dir / "vrn_db" / db.BASICINFO_PARQUET_NAME))
        ok = before == after
        how = "" if len(pick) == len(names) else f" · 抽 {len(pick)}/{len(names)} 檔再入庫(要全批:--g08-full)"
        return [def_row("G08 IDEMPOTENT", "second batch keeps one row per ReportID", "PASS" if ok else "FAIL",
                        f"before={before} after={after}{how}")]
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
# ---------------------------------------------------------------------------
# 04. VCGC / truth / 15-column gates (v0101)
# ---------------------------------------------------------------------------
def def_gate_vcgc(engines: Engines) -> List[Dict[str, Any]]:
    """Mother VCGC mirror == manifest, the mirrored CGC selftests pass, the 批679 deny list holds."""
    rows: List[Dict[str, Any]] = []
    if not VCGC_SYNC.is_file():
        # v0102 母倉模式:這棵樹就是母倉——沒有鏡像可比,工具直接讀正本;自測照跑;
        # 拒絕清單 / 負控 / 同義字對帳**一律照跑**(v0101 在這裡整段 return,母倉的 G10 等於沒驗)。
        rows += def_gate_vcgc_mother(engines)
    else:
        try:
            sync = def_load_module("vrn_autotest_vcgc_sync", VCGC_SYNC)
            chk = sync.check()
            drift = [r for r in chk.get("rows", []) if r.get("state") != "SAME"]
            rows.append(def_row("G10 VCGC", f"mirror == manifest ({len(chk.get('rows', []))} files)",
                                "PASS" if chk.get("verdict") == "PASS" else ("WARN" if chk.get("verdict") == "ABSENT" else "FAIL"),
                                json.dumps({"source": chk.get("source"), "drift": drift[:5]}, ensure_ascii=False)[:300]))
            tools = sync.selftest_tools()
            for r in tools.get("rows", []):
                rows.append(def_row("G10 VCGC", f"{r.get('tool')} --selftest", r.get("state", "FAIL"),
                                    f"{r.get('ok')}/{r.get('checks')} " + " | ".join(r.get("fail_lines", [])[:2])))
        except Exception as error:  # noqa: BLE001
            rows.append(def_row("G10 VCGC", "VIA_VCGC_Sync", "FAIL", f"{error.__class__.__name__}: {error}"[:300]))
    core = engines.core
    if core is None or engines.fpe is None:
        rows.append(def_row("G10 VCGC", "deny list", "SKIP", "evidence core or first-page engine absent"))
        return rows
    purge = core.vcgc("purge")
    if purge is None:
        rows.append(def_row("G10 VCGC", "deny list", "WARN", "CGC_MDL177 not mirrored: 批679 deny list not enforced"))
        return rows
    leaks = []
    # v0102 母倉:整本拒絕清單(疊加層 deny_keys + CGC_MDL177),頁面層與檔名層兩道都驗(批413「去摩通」也在裡面)
    phrases = list(getattr(core, "deny_phrases", lambda: ())()) or sorted(getattr(purge, "CN_ALIAS", ()))
    for alias in phrases:
        ev = core.broker_evidence([f"{alias} 研究部", f"本報告由 {alias} 證券發布"], engines.fpe.brd.b)
        if ev.get("broker"):
            leaks.append(f"頁:{alias}->{ev['broker']}")
        got = engines.fpe.brd.broker_normalize(alias)
        if got:
            leaks.append(f"名:{alias}->{got}")
    rows.append(def_row("G10 VCGC", f"deny list holds ({len(phrases)} names never resolve · page + filename layers)",
                        "FAIL" if leaks else "PASS", ", ".join(leaks)[:300]))
    controls = {"中國信託證券投顧": "CTBC", "國泰證期研究部": "CATHAY", "CLSA Limited": "CLSA", "凱基證券投資顧問": "KGI",
                "摩根士丹利證券研究部": "MS", "本報告由摩根大通發布": "JPM", "中信投顧研究部": "CTBC"}
    wrong = []
    for text, expect in controls.items():
        got = core.broker_evidence([text], engines.fpe.brd.b).get("broker")
        if got != expect:
            wrong.append(f"{text}->{got} (want {expect})")
    rows.append(def_row("G10 VCGC", "negative controls (CTBC / CATHAY / CLSA / KGI / MS / JPM keep resolving; longest wins)",
                        "FAIL" if wrong else "PASS", ", ".join(wrong)[:300]))
    rows += def_synonym_reconcile(engines, purge)
    return rows


MOTHER_SELFTEST_TOOLS = ("gate", "rulers", "purge")     # CGC_MDL181 / CGC_MDL182 / CGC_MDL177(姊妹倉鏡像跑前兩支;母倉三支都在)


def def_run_tool_selftest(path: Path, timeout: int = 420) -> Dict[str, Any]:
    """One mother tool's own --selftest (UTF-8 stdout; consent variables removed).  Honest states:
    rc 0 and no [FAIL] = PASS · rc 2 NODATA / rc 3 ABSENT = WARN (缺料/缺件不是壞掉) · else FAIL."""
    env = dict(os.environ)
    env.pop("VIA_NET_CONSENT", None)
    env.pop("VIA_SCRAPE_CONSENT", None)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["VIA_NO_OPEN"] = "1"
    try:
        proc = subprocess.run([sys.executable, str(path), "--selftest"], capture_output=True, timeout=timeout,
                              cwd=str(path.parent), env=env, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"state": "WARN", "detail": f"timeout {timeout}s (沒跑完=沒有結論,不記紅)"}
    text = proc.stdout.decode("utf-8", "replace") + proc.stderr.decode("utf-8", "replace")
    fails = [l.strip()[:160] for l in text.splitlines() if l.strip().startswith("[FAIL]")]
    tally = [l.strip()[:120] for l in text.splitlines() if "[計]" in l][-1:]
    if proc.returncode == 0 and not fails:
        state = "PASS"
    elif proc.returncode in (2, 3):
        state = "WARN"
    else:
        state = "FAIL"
    return {"state": state, "detail": f"rc={proc.returncode} " + " | ".join(fails[:2] + tally)}


def def_gate_vcgc_mother(engines: Engines) -> List[Dict[str, Any]]:
    """Mother mode of G10: the VCGC tools are read from source (newest version, L54) and their selftests run."""
    rows: List[Dict[str, Any]] = []
    core = engines.core
    if core is None:
        return [def_row("G10 VCGC", "mother tools", "SKIP", "evidence core absent")]
    paths = {}
    for name in ("hub", "rulers", "gate", "purge"):
        mod = core.vcgc(name)
        paths[name] = Path(getattr(mod, "__vcgc_path__", "")) if mod is not None else None
    missing = [n for n, pth in paths.items() if pth is None]
    rows.append(def_row("G10 VCGC", "mother source (no mirror: this tree is the mother)",
                        "FAIL" if missing else "PASS",
                        ("missing " + ", ".join(missing) + " · ") * bool(missing)
                        + " · ".join(pth.name for pth in paths.values() if pth is not None)))
    for name in MOTHER_SELFTEST_TOOLS:
        pth = paths.get(name)
        if pth is None:
            continue
        res = def_run_tool_selftest(pth)
        rows.append(def_row("G10 VCGC", f"{pth.name} --selftest", res["state"], res["detail"][:300]))
    return rows


def def_synonym_reconcile(engines: Engines, purge: Any) -> List[Dict[str, Any]]:
    """SSOT synonyms vs the mother canonical (institution SSOT; mother order: deny list -> canonical ->
    overlay -> union).  Every broker alias and rating word this repo resolves is SAME / SISTER_ONLY
    (allowed: only-add) / DENIED; a CONFLICT (the mother names another key for the same word) is a FAIL."""
    core = engines.core
    inst = core.institution_ssot() or {}
    regs = inst.get("registries") or {}
    if not regs:
        return [def_row("G10 VCGC", "synonym reconcile", "WARN", "institution SSOT not found: canonical keys unknown")]
    mother_b: Dict[str, str] = {}
    for grp in ("domestic_brokers", "foreign_brokers"):
        for key, spec in (regs.get(grp) or {}).items():
            for alias in [spec.get("ssot_key", ""), spec.get("chinese_name", ""), spec.get("english_name", "")] + list(spec.get("aliases") or []):
                if alias:
                    mother_b.setdefault(str(alias).lower(), key)
    tally: Dict[str, int] = {}
    conflicts: List[str] = []
    for canon, aliases in engines.fpe.brd.b.items():
        for alias in aliases:
            try:
                denied = bool(purge and (purge.is_cn_alias(alias) or purge.is_cn_canon(canon)))
            except Exception:  # noqa: BLE001
                denied = False
            state = "DENIED" if denied else ("SISTER_ONLY" if alias.lower() not in mother_b else
                                             ("SAME" if mother_b[alias.lower()] == canon else "CONFLICT"))
            tally[state] = tally.get(state, 0) + 1
            if state == "CONFLICT":
                conflicts.append(f"{alias}: here {canon}, mother {mother_b[alias.lower()]}")
    rows = [def_row("G10 VCGC", "broker synonyms vs mother canonical " + " · ".join(f"{k} {v}" for k, v in sorted(tally.items())),
                    "FAIL" if conflicts else "PASS", " | ".join(conflicts)[:300])]
    mother_r: Dict[str, str] = {}
    for key, spec in (regs.get("broker_ratings") or {}).items():
        for alias in [spec.get("chinese_name", ""), spec.get("english_name", "")] + list(spec.get("aliases") or []):
            if alias:
                mother_r.setdefault(str(alias).lower(), key)
    coarse = {"STRONG_BUY": "BUY", "STRONG_SELL": "SELL"}
    r_tally: Dict[str, int] = {}
    r_conflicts: List[str] = []
    for word, level in core.merged_rating_words(core.load_rules()).items():
        m = mother_r.get(word.lower())
        mine = {"ADD": "BUY"}.get(level, level)
        state = "SISTER_ONLY" if m is None else ("SAME" if coarse.get(m, m) == mine else "CONFLICT")
        r_tally[state] = r_tally.get(state, 0) + 1
        if state == "CONFLICT":
            r_conflicts.append(f"{word}: here {level}, mother {m}")
    rows.append(def_row("G10 VCGC", "rating words vs mother canonical keys " + " · ".join(f"{k} {v}" for k, v in sorted(r_tally.items())),
                        "FAIL" if r_conflicts else "PASS", " | ".join(r_conflicts)[:300]))
    return rows


def def_truth_values(kind: str, src: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise one engine's answer for a file into the truth vocabulary."""
    if kind == "database":
        def num(v):
            try:
                return float(v) if v not in ("", None) else None
            except (TypeError, ValueError):
                return None
        return {"type": src.get("ReportType") or None, "ticker": src.get("TW_TICKER") or None,
                "broker": src.get("Broker") or None, "denied": bool(src.get("BrokerDenied")),
                "page_date": src.get("PageDate") or None, "rating": src.get("Rating") or None,
                "target_price": num(src.get("TargetPrice")), "current_price": num(src.get("CurrentPrice")),
                "company": src.get("CompanyNamePage") or None,
                "analysts": [a for a in str(src.get("Analyst") or "").split(" | ") if a]}
    return {"type": src.get("type"), "ticker": src.get("ticker"), "broker": src.get("broker"),
            "denied": bool(src.get("denied")), "page_date": src.get("page_date"), "rating": src.get("rating"),
            "target_price": src.get("target_price"), "current_price": src.get("current_price"),
            "company": src.get("company"), "analysts": [a for a in src.get("analysts", []) if a]}


def def_same_name(a: str, b: str) -> bool:
    ka = re.sub(r"[^a-z一-鿿]", "", (a or "").lower())
    kb = re.sub(r"[^a-z一-鿿]", "", (b or "").lower())
    if not ka or not kb:
        return False
    if ka == kb or ka in kb or kb in ka:
        return True
    ta, tb = (a or "").lower().replace(".", " ").split(), (b or "").lower().replace(".", " ").split()
    return len(ta) >= 2 and len(tb) >= 2 and ta[0] == tb[0] and ta[-1] == tb[-1]


def def_truth_compare(t: Dict[str, Any], got: Dict[str, Any]) -> Tuple[List[str], List[str], Dict[str, str]]:
    """(critical mismatches, soft mismatches, per-field state) for one file."""
    hard, soft, state = [], [], {}
    op = t.get("on_page1") or {}
    stock = t.get("report_type") == "STOCK"
    acc = t.get("accept") or {}
    ok_type = (got["type"] == "STOCK") == stock
    state["type"] = "OK" if ok_type else "BAD"
    if not ok_type:
        hard.append(f"type {got['type']} vs {t.get('report_type')}")
    state["ticker"] = "OK" if got["ticker"] == t.get("ticker") else "BAD"
    if state["ticker"] == "BAD":
        hard.append(f"ticker {got['ticker']} vs {t.get('ticker')}")
    b_ok = got["broker"] == t.get("broker") or (acc.get("broker") is not None and
                                                 (got["broker"] in acc["broker"] or (got["denied"] and "DENIED" in acc["broker"])))
    state["broker"] = "OK" if b_ok else "BAD"
    if not b_ok:
        hard.append(f"broker {got['broker']} vs {t.get('broker')}")
    if t.get("page_date") and op.get("page_date"):
        state["page_date"] = "OK" if got["page_date"] == t["page_date"] else "BAD"
        if state["page_date"] == "BAD":
            hard.append(f"page date {got['page_date']} vs {t['page_date']}")
    elif got["page_date"] and not t.get("page_date"):
        state["page_date"] = "FALSE_POSITIVE"
        hard.append(f"page date {got['page_date']} where none is printed")
    for fld in ("rating", "target_price", "current_price"):
        want, have = t.get(fld), got[fld]
        same = (have == want) if fld == "rating" else def_near(have, want)
        if not stock:
            if have not in (None, ""):
                state[fld] = "FALSE_POSITIVE"
                hard.append(f"{fld} {have} on a {t.get('report_type')} report")
            continue
        if want is not None and op.get(fld):
            state[fld] = "OK" if same else "BAD"
            if not same:
                hard.append(f"{fld} {have} vs {want}")
        elif want is None and have not in (None, ""):
            state[fld] = "FALSE_POSITIVE"
            hard.append(f"{fld} {have} where none is printed")
        else:
            state[fld] = "NOT_ON_PAGE1"
    if stock and t.get("company_name") and t.get("text_layer"):
        ok = bool(got["company"]) and def_same_name(got["company"], t["company_name"])
        state["company"] = "OK" if ok else "BAD"
        if not ok:
            soft.append(f"company {got['company']} vs {t['company_name']}")
    if t.get("analysts") and t.get("text_layer"):
        ok = any(def_same_name(a, t["analysts"][0]) for a in got["analysts"])
        state["analyst"] = "OK" if ok else "BAD"
        if not ok:
            soft.append(f"analyst {got['analysts'][:2]} vs {t['analysts'][:1]}")
    return hard, soft, state


def def_gate_truth(engines: Engines, truth_path: str, out_dir: Optional[Path], run_id: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not truth_path:
        return [], {}
    try:
        truth = json.loads(Path(truth_path).read_text(encoding="utf-8"))
    except Exception as error:  # noqa: BLE001
        return [def_row("G11 TRUTH", truth_path, "FAIL", f"truth unreadable: {error}")], {}
    by_db: Dict[str, Dict[str, Any]] = {}
    if out_dir is not None and engines.database is not None:
        try:
            basic = json.loads((out_dir / "vrn_db" / engines.database.BASICINFO_JSON_NAME).read_text(encoding="utf-8"))
            by_db = {r.get("SourceFileName"): r for r in basic if r.get("RunID") == run_id}
        except Exception:  # noqa: BLE001
            by_db = {}
    rows: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {"files": len(truth), "engines": {}}
    for kind, source in (("database", by_db), ("first_page", LAST_FIRST_PAGE)):
        tally: Dict[str, Dict[str, int]] = {}
        hard_all, soft_all = [], []
        judged = 0
        for t in truth:
            src = source.get(t.get("file"))
            if src is None:
                continue
            if kind == "first_page" and not src.get("text_layer"):
                continue
            judged += 1
            hard, soft, state = def_truth_compare(t, def_truth_values(kind, src))
            for fld, st in state.items():
                tally.setdefault(fld, {}).setdefault(st, 0)
                tally[fld][st] += 1
            hard_all += [f"{t['file']}: {h}" for h in hard]
            soft_all += [f"{t['file']}: {x}" for x in soft]
        summary["engines"][kind] = {"judged": judged, "fields": tally}
        for fld in TRUTH_CRITICAL:
            st = tally.get(fld, {})
            bad = [h for h in hard_all if (" " + fld.replace("_", " ")) in (" " + h.split(": ", 1)[1]) or h.split(": ", 1)[1].startswith(fld.replace("_", " "))]
            status = "FAIL" if (st.get("BAD", 0) or st.get("FALSE_POSITIVE", 0)) else ("PASS" if st else "SKIP")
            rows.append(def_row("G11 TRUTH", f"{kind}: {fld} {st.get('OK', 0)} ok / {st.get('BAD', 0)} wrong / "
                                f"{st.get('FALSE_POSITIVE', 0)} false+ / {st.get('NOT_ON_PAGE1', 0)} not on p1",
                                status, " | ".join(bad)[:400], stage="S07 NLP_ENRICH" if status == "FAIL" else "S10 SUMMARIZER"))
        for fld in ("company", "analyst"):
            st = tally.get(fld, {})
            total = st.get("OK", 0) + st.get("BAD", 0)
            rate = (st.get("OK", 0) / total) if total else 1.0
            misses = [x for x in soft_all if x.split(": ", 1)[1].startswith(fld)]
            rows.append(def_row("G11 TRUTH", f"{kind}: {fld} {st.get('OK', 0)}/{total} ({rate:.0%})",
                                "PASS" if rate >= 0.9 else "WARN", " | ".join(misses)[:400]))
    if getattr(engines, "canonical_crosscheck", False) and engines.core is not None:
        rows += def_canonical_reference(engines, truth, summary)
    return rows, summary


def def_canonical_reference(engines: Engines, truth: List[Dict[str, Any]], summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Reference only: the mother's canonical extractor (SUP_MDL749 hub -> ENG086) on the same truth.
    Rows are PASS/SKIP (never FAIL): the numbers are feedback for the mother, not a verdict on this repo."""
    core = engines.core
    if core.vcgc("hub") is None:
        return [def_row("G11 TRUTH", "canonical ENG086 reference", "SKIP", "hub not mirrored")]
    if not list((REPO_ROOT / "functional modules" / "VRN").glob("VRN_ENG086_FirstPageLogicBridge_v*.py")):
        return [def_row("G11 TRUTH", "canonical ENG086 reference", "SKIP",
                        "ENG086 is not in the tree: python scripts/VIA_VCGC_Sync.py --apply --with-reference --mother <clone>")]
    tally = {"rating": [0, 0], "target_price": [0, 0], "broker": [0, 0]}
    for t in truth:
        if t.get("report_type") != "STOCK" or not t.get("text_layer"):
            continue
        path = LAST_SAMPLES.get(t.get("file"))
        if not path:
            continue
        lines = core.document_first_page_lines(str(path))["lines"]
        ref = core.canonical_cross_check(lines, t["file"], t.get("ticker"))
        op = t.get("on_page1") or {}
        if t.get("rating") and op.get("rating"):
            got = str(ref.get("rating") or "").upper().replace("STRONG_", "")
            tally["rating"][0 if (got == t["rating"] or (t["rating"] == "ADD" and got == "BUY")) else 1] += 1
        if t.get("target_price") is not None and op.get("target_price"):
            tally["target_price"][0 if def_near(ref.get("target_price"), t["target_price"]) else 1] += 1
        got_b = str(ref.get("broker") or "").upper()
        want_b = str(t.get("broker") or "").upper()
        aliases = {"GOLDMANSACHS": "GS", "MORGANSTANLEY": "MS", "CITIGROUP": "CITI", "JPMORGAN": "JPM", "J.P. MORGAN": "JPM"}
        tally["broker"][0 if aliases.get(got_b, got_b) == want_b else 1] += 1
    summary["canonical_reference"] = {k: {"ok": v[0], "wrong": v[1]} for k, v in tally.items()}
    return [def_row("G11 TRUTH", f"canonical ENG086 reference: {k} {v[0]}/{v[0] + v[1]}", "PASS",
                    "reference only (mother canonical extractor on the same truth; feedback, not a verdict)")
            for k, v in tally.items()]


FIELD_GATED = {"yf_ticker", "bloomberg_ticker", "name", "target_price_adj", "adj_close", "yf_consensus_median", "forward_per_n_n2"}
FIELD_NOT_WIRED = {"factset_consensus_median"}


def def_gate_fieldspec(engines: Engines, out_dir: Optional[Path], run_id: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """15 columns x six states through the mother's CGC_MDL181 (spec and _state read from the VCGC mirror)."""
    core = engines.core
    gate = core.vcgc("gate") if core is not None else None
    if gate is None or out_dir is None or engines.database is None:
        return [def_row("G12 FIELDSPEC", "CGC_MDL181", "SKIP", "gate tool, evidence core or batch output absent")], []
    spec = gate.load_spec()
    try:
        basic = [r for r in json.loads((out_dir / "vrn_db" / engines.database.BASICINFO_JSON_NAME).read_text(encoding="utf-8"))
                 if r.get("RunID") == run_id]
        fin = json.loads((out_dir / "vrn_db" / engines.database.FINANCIALDATA_JSON_NAME).read_text(encoding="utf-8"))
    except Exception as error:  # noqa: BLE001
        return [def_row("G12 FIELDSPEC", "batch output", "FAIL", f"{error.__class__.__name__}: {error}")], []
    inst = core.institution_ssot() or {}
    regs = inst.get("registries") or {}
    broker_keys = set(regs.get("domestic_brokers") or {}) | set(regs.get("foreign_brokers") or {})
    hub = core.vcgc("hub")
    try:
        rating_keys = set(hub.rating_keys()) if hub else set()
    except Exception:  # noqa: BLE001
        rating_keys = set()
    # the hub reads the institution book at the mother's path; here the book lives once, in the sealed
    # audit package, so the same six keys come from there when the hub finds none
    rating_keys = rating_keys or set((regs.get("broker_ratings") or {}).keys())
    rows_t = [r for r in basic if r.get("TW_TICKER")]
    total = len(rows_t)
    today = time.strftime("%Y-%m-%d")
    fin_by: Dict[str, Dict[str, set]] = {}
    for r in fin:
        if r.get("MetricName") in ("EPS", "PER") and r.get("FiscalYear") not in (None, "") and r.get("Value") not in (None, ""):
            try:
                fin_by.setdefault(r.get("ReportID", ""), {}).setdefault(r["MetricName"], set()).add(int(float(r["FiscalYear"])))
            except (TypeError, ValueError):
                continue

    def three_years(row: Dict[str, Any], metric: str) -> bool:
        years = (fin_by.get(row.get("ReportID", "")) or {}).get(metric, set())
        try:
            n = int(str(row.get("ReportDate") or "")[:4])
        except ValueError:
            return False
        return {n, n + 1, n + 2} <= years

    have = {
        "report_date": sum(1 for r in rows_t if r.get("ReportDate") and str(r["ReportDate"]) <= today),
        "filename": sum(1 for r in rows_t if r.get("SourceFileName")),
        "broker": sum(1 for r in rows_t if (r.get("Broker") or "") in broker_keys),
        "analyst": sum(1 for r in rows_t if r.get("Analyst")),
        "ticker": sum(1 for r in rows_t if r.get("TriCodeVerdict") != "MISMATCH"),
        "yf_ticker": sum(1 for r in rows_t if r.get("YF_TICKER")),
        "bloomberg_ticker": sum(1 for r in rows_t if r.get("YF_TICKER")),
        "name": sum(1 for r in rows_t if r.get("Name")),
        "rating": sum(1 for r in rows_t if (r.get("RatingKey") or "") in rating_keys and r.get("RatingKey")),
        "target_price_adj": 0, "adj_close": 0, "factset_consensus_median": 0, "yf_consensus_median": 0,
        "diluted_eps_n_n2": sum(1 for r in rows_t if three_years(r, "EPS")),
        "forward_per_n_n2": sum(1 for r in rows_t if three_years(r, "PER")),
    }
    table: List[Dict[str, Any]] = []
    rows: List[Dict[str, Any]] = []
    for f in spec.get("fields", []):
        key = f.get("key")
        h = have.get(key, 0)
        state = gate._state(h, total, wired=key not in FIELD_NOT_WIRED, gated=key in FIELD_GATED)
        table.append({"key": key, "zh": f.get("zh"), "state": state, "have": h, "total": total})
        broken = state == "NODATA" and key in ("report_date", "filename", "ticker", "broker")
        rows.append(def_row("G12 FIELDSPEC", f"{key} {f.get('zh', '')}: {state} {h}/{total}",
                            "FAIL" if broken else "PASS",
                            {"GATED": "needs network (consent gate off; never set by AI)",
                             "NOT_WIRED": "no writer in this tree", "PARTIAL": "honest coverage below 95%"}.get(state, "")))
    return rows, table


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
    LAST_FIRST_PAGE.clear()
    LAST_APPENDIX.clear()
    LAST_ADJ.clear()
    LAST_SAMPLES.clear()
    def_say(f"[ROUND {round_no}] G01 編譯 · G02 自測 · G03 檔名 oracle" + ("" if args.no_audit else " · G04 稽核"))
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
        g08_full, g08_n = bool(getattr(args, "g08_full", False)), int(getattr(args, "g08_sample", G08_SAMPLE))
        db_eng = engines.database
        files_in = db_eng.scan_input_files(Path(samples)) if db_eng is not None else []
        n_in = len(files_in) if db_eng is not None else len(before)
        n_g08 = len(def_g08_pick([f.name for f in files_in if f.suffix.lower() not in db_eng.OCR_SUFFIXES]
                                 if db_eng is not None else [], g08_n, g08_full))
        PROGRESS["round_total"] = 2 * n_in + n_g08            # v0104:G06 n + G07 n + G08 抽樣,百分比一路往上
        PROGRESS["round_offsets"] = {"G06": 0, "G07": n_in, "G08": 2 * n_in}
        def_say(f"[ROUND {round_no}] G06 資料庫引擎整批入庫（{len(before)} 檔；每檔一行進度）")
        batch_rows, summary = def_gate_batch(engines, samples, out_dir, truth, real_mode, run_id)
        rows += batch_rows
        state["last_summary"] = summary
        state["last_out"] = str(out_dir)
        def_say(f"[ROUND {round_no}] G07 首頁引擎逐檔")
        rows += def_gate_first_page(engines, truth, samples, real_mode)
        if summary:
            def_say(f"[ROUND {round_no}] G08 冪等：抽 {n_g08} 檔再入庫一次（--g08-full 全批），列數必須不變")
            rows += def_gate_idempotent(engines, samples, out_dir, run_id, g08_n, g08_full)
        rows += def_gate_read_only(samples, before)
        def_say(f"[ROUND {round_no}] G09 唯讀 · G11 真值" + ("" if getattr(args, "truth", "") else "（未給 --truth，略過）") + " · G12 15 欄六態")
        truth_rows, truth_summary = def_gate_truth(engines, getattr(args, "truth", ""), out_dir if summary else None, run_id)
        rows += truth_rows
        state["truth_summary"] = truth_summary
        spec_rows, spec_table = def_gate_fieldspec(engines, out_dir if summary else None, run_id)
        rows += spec_rows
        state["fieldspec"] = spec_table
    def_say(f"[ROUND {round_no}] G10 母倉 VCGC 鏡像、自測、拒絕清單、同義字對帳")
    rows += def_gate_vcgc(engines)
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
    if report.get("fieldspec"):
        state_colour = {"GREEN": "#16a34a", "PARTIAL": "#f59e0b", "GATED": "#6366f1", "NOT_WIRED": "#6b7280",
                        "SOURCE_PENDING": "#0ea5e9", "NODATA": "#dc2626"}
        parts.append("<h2>15 欄規格 · 六態（母倉 CGC_MDL181）</h2><table><thead><tr><th>欄</th><th>中文</th><th>態</th><th>有值 / 分母</th></tr></thead><tbody>")
        for f in report["fieldspec"]:
            parts.append(f"<tr><td>{html.escape(str(f['key']))}</td><td>{html.escape(str(f.get('zh') or ''))}</td>"
                         f"<td><span class='pill' style='background:{state_colour.get(f['state'], '#6b7280')}'>{html.escape(f['state'])}</span></td>"
                         f"<td>{f['have']} / {f['total']}</td></tr>")
        parts.append("</tbody></table>")
    ts = report.get("truth_summary") or {}
    if ts.get("engines"):
        parts.append(f"<h2>真值比對（{ts.get('files')} 份）</h2><table><thead><tr><th>引擎</th><th>欄</th><th>對</th><th>錯</th><th>誤報</th><th>首頁未印</th></tr></thead><tbody>")
        for kind, e in ts["engines"].items():
            for fld, st in e.get("fields", {}).items():
                parts.append(f"<tr><td>{html.escape(kind)}</td><td>{html.escape(fld)}</td><td>{st.get('OK', 0)}</td><td>{st.get('BAD', 0)}</td>"
                             f"<td>{st.get('FALSE_POSITIVE', 0)}</td><td>{st.get('NOT_ON_PAGE1', 0)}</td></tr>")
        parts.append("</tbody></table>")
    for rnd in report["rounds"]:
        parts.append(f"<h2>第 {rnd['round']} 輪 · {html.escape(rnd['verdict'])}</h2><table><thead><tr><th>閘門</th><th>項目</th><th>狀態</th><th>段</th><th>細節</th></tr></thead><tbody>")
        for r in rnd["rows"]:
            parts.append(f"<tr><td>{html.escape(r['gate'])}</td><td>{html.escape(str(r['name']))}</td>"
                         f"<td><span class='pill' style='background:{colour.get(r['status'], '#6b7280')}'>{r['status']}</span></td>"
                         f"<td>{html.escape(str(r.get('stage', '')))}</td><td>{html.escape(str(r.get('detail', ''))[:400])}</td></tr>")
        parts.append("</tbody></table>")
    parts.append("<p>LIVE 關 · 不連網 · 不設定 consent · 輸出只寫到 --out</p></body></html>")
    return "".join(parts)


UNIT_MARK = "[UNIT-JSON] "
UNIT_FILE_TIMEOUT = 900        # v0104:單一測試檔的天花板(秒);逾時 = 那一檔 FAIL,不拖住整扇門


def def_flatten(suite: Any) -> List[Any]:
    import unittest
    out: List[Any] = []
    for item in suite:
        out += def_flatten(item) if isinstance(item, unittest.TestSuite) else [item]
    return out


def def_unit_file(spec: str) -> int:
    """v0104 (--unit-file FILE[::k/n]): one VRN/tests file in this process -- or part k of n of it: the file is
    discovered whole and its test classes are dealt out in name order, so every test runs in exactly one part (inherited
    tests too) and a class's shared set-up runs once per part.  One ASCII JSON line on stdout.  Started by the
    self-test with VRN_UNIT_WATCH_STDIN=1: when that parent is gone (killed by an outer ceiling) its end of our stdin
    closes and this process exits too -- an orphaned test must not keep the market database open for the next station."""
    import threading
    import unittest
    path, _, part = spec.partition("::")
    if os.environ.get("VRN_UNIT_WATCH_STDIN") == "1" and sys.stdin is not None:
        def watch_parent() -> None:
            try:
                sys.stdin.buffer.read()
            except (OSError, ValueError):
                return
            os._exit(3)
        threading.Thread(target=watch_parent, daemon=True).start()
    target = Path(path).resolve()
    suite = unittest.TestLoader().discover(str(target.parent), pattern=target.name, top_level_dir=str(target.parent))
    if part:
        k, n = (int(x) for x in part.split("/"))
        cases = def_flatten(suite)
        names = sorted({f"{type(c).__module__}.{type(c).__qualname__}" for c in cases})
        mine = set(names[k::n])
        suite = unittest.TestSuite([c for c in cases if f"{type(c).__module__}.{type(c).__qualname__}" in mine])
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    print(UNIT_MARK + json.dumps({"file": target.name + (f"[{part}]" if part else ""), "run": res.testsRun,
                                  "skipped": len(res.skipped), "bad": [str(t[0]) for t in res.failures + res.errors]}),
          flush=True)
    return 0


def def_unit_specs(tests_dir: Path, workers: int) -> List[str]:
    """v0104: the self-test's work units, costliest first -- a file, or FILE::k/n parts when it holds several classes
    (the ADJ oracle's three classes then run side by side instead of one after another).  Cost = the file's own
    `SELFTEST_SECONDS = N` (read from its source, not run) shared by its parts; otherwise its size (~1 s per 4 KB).
    Nothing is timed and written back: a self-test writes only to its scratch folder."""
    import ast
    weighted: List[Tuple[float, str, str]] = []
    for f in sorted(tests_dir.glob("test_*.py")):
        try:
            body = ast.parse(f.read_text(encoding="utf-8", errors="replace")).body
        except SyntaxError:
            body = []                               # its own run reports the error
        n_cls = sum(isinstance(n, ast.ClassDef) for n in body) or 1
        hint = next((float(n.value.value) for n in body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "SELFTEST_SECONDS" for t in n.targets)
                     and isinstance(n.value, ast.Constant) and isinstance(n.value.value, (int, float))), None)
        parts = min(n_cls, workers)
        cost = (hint if hint is not None else f.stat().st_size / 4000) / max(parts, 1)
        units = [f"{f}::{k}/{parts}" for k in range(parts)] if parts > 1 else [str(f)]
        weighted += [(cost, f.name, u) for u in units]
    return [u for _, _, u in sorted(weighted, key=lambda w: (-w[0], w[1], w[2]))]


def def_unit_child(spec: str, timeout: int = UNIT_FILE_TIMEOUT) -> Dict[str, Any]:
    """v0104: one work unit (a test file or FILE::k/n) in a child process of this script -> {file, run, skipped, bad,
    secs}.  No answer line (crash, timeout) = that unit is a failure, with the last lines of its output."""
    import threading
    t0 = time.time()
    env = dict(os.environ, PYTHONIOENCODING="utf-8", VRN_UNIT_WATCH_STDIN="1")
    proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--unit-file", spec],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    timer = threading.Timer(timeout, proc.kill)
    timer.start()
    try:
        raw = proc.stdout.read() if proc.stdout else b""
        rc = proc.wait()
    finally:
        timer.cancel()
        if proc.stdin:
            proc.stdin.close()
    text = raw.decode("utf-8", errors="replace")
    secs = round(time.time() - t0, 1)
    for line in reversed(text.splitlines()):
        if line.startswith(UNIT_MARK):
            out = json.loads(line[len(UNIT_MARK):])
            out["secs"] = secs
            return out
    why = f"逾時 {timeout}s" if secs >= timeout else f"rc={rc}"
    tail = " / ".join(text.strip().splitlines()[-2:])[:200]
    name = Path(spec.partition("::")[0]).name + (f"[{spec.partition('::')[2]}]" if "::" in spec else "")
    return {"file": name, "run": 0, "skipped": 0, "bad": [f"{name} 沒有回報({why}){tail}"], "secs": secs}


def def_unit_all(tests_dir: Path) -> Tuple[int, int, List[str], str]:
    """v0104: all VRN/tests files -> (run, skipped, bad, how).  Work units (def_unit_specs) run side by side, one
    process each (the batch pool's worker count: VRN_BATCH_WORKERS > the accelerator's thread budget > CPUs - 1); one
    worker = the whole suite in this process, as before.  Each unit keeps its own main process, so the tests that
    start the batch pool still start it."""
    import unittest
    files = sorted(tests_dir.glob("test_*.py"), key=lambda f: (-f.stat().st_size, f.name))
    workers, why = 1, ""
    try:
        if str(HERE) not in sys.path:
            sys.path.insert(0, str(HERE))
        import VRN_BatchPool as pool  # type: ignore
        workers = pool.workers_for(len(files))
    except ImportError as exc:
        why = f"(平行池載不到:{exc.name or exc})"
    if workers <= 1:
        suite = unittest.TestLoader().discover(str(tests_dir), pattern="test_*.py", top_level_dir=str(tests_dir))
        res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
        return res.testsRun, len(res.skipped), [str(t[0]) for t in res.failures + res.errors], "本行程序跑" + why
    from concurrent.futures import ThreadPoolExecutor
    specs = def_unit_specs(tests_dir, workers)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        got = list(ex.map(def_unit_child, specs))
    slow = max(got, key=lambda g: g["secs"])
    return (sum(g["run"] for g in got), sum(g["skipped"] for g in got), [b for g in got for b in g["bad"]],
            f"{len(files)} 檔 {len(specs)} 份 · 平行 {workers} 行程 · 最慢 {slow['file']} {slow['secs']}s")


def def_selftest() -> int:
    """母倉 批728 自測門(六層鏈 CGC_MDL172 與全格子都敲這扇門):
    ① VRN/tests 全部單元測試(unittest,不需 pytest);② 合成語料小批(--limit 8,一輪)跑到底,不得有 FAIL。
    輸出寫暫存夾、跑完刪掉;不連網、不設同意閘、不動樣本。rc 0 = 兩段都沒有 FAIL。"""
    import unittest
    t0 = time.time()
    ran, fails = [], []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        ran.append(name)
        if not ok:
            fails.append(name)
            print(f"  [FAIL] {name} {detail}".rstrip())
        else:
            print(f"  [OK] {name} {detail}".rstrip())

    tests_dir = VRN_ROOT / "tests"
    if tests_dir.is_dir():
        n_run, n_skip, bad, how = def_unit_all(tests_dir)
        chk(f"① VRN/tests 單元測試 {n_run} 支(跳過 {n_skip};{how})", not bad and n_run > 0,
            ("壞:" + " | ".join(bad[:3])) if bad else "")
    else:
        chk("① VRN/tests 單元測試", False, "tests 夾不在")
    tmp = Path(tempfile.mkdtemp(prefix="vrn_autotest_selftest_"))
    try:
        import contextlib
        # v0104: the pool's one-line notes go to stderr; the six-layer chain reads stdout then stderr and shows the
        # last two lines, so keep them in stdout here -- the [計] summary stays the last line it shows
        with contextlib.redirect_stderr(sys.stdout):
            rc = def_main(["--synthetic", "--limit", "8", "--rounds", "1", "--quiet", "--out", str(tmp)])
        rep = tmp / "VRN_AutoTest_Report.json"
        verdict, n_fail = "?", -1
        if rep.is_file():
            data = json.loads(rep.read_text(encoding="utf-8"))
            verdict = data.get("verdict", "?")
            last = (data.get("rounds") or [{}])[-1]
            n_fail = sum(1 for r in (last.get("rows") or data.get("rows") or []) if r.get("status") == "FAIL")
        chk(f"② 合成語料小批(8 檔 · 1 輪)跑到底無 FAIL", rc == 0 and n_fail == 0, f"(rc={rc} · {verdict} · FAIL {n_fail})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"  [計] 自測 {len(ran)} 檢 OK {len(ran) - len(fails)} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def def_appendix_summary(per_file: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """v0103 (批729): the appendix small print of the round, summed.  New rating words are CANDIDATES only --
    synonyms are only-add and go through the hub; this loop never writes a book."""
    new: Dict[str, Dict[str, Any]] = {}
    for name, a in per_file.items():
        for r in a.get("rating_scale") or []:
            for word, known, other in ((r.get("word"), r.get("word_known"), r.get("alt")),
                                       (r.get("alt"), r.get("alt_known"), r.get("word"))):
                if not word or known:
                    continue
                w = new.setdefault(word, {"word": word, "count": 0, "alts": [], "suggested": [], "examples": [], "files": []})
                w["count"] += 1
                if other and other not in w["alts"]:
                    w["alts"].append(other)
                if r.get("suggested") and r["suggested"] not in w["suggested"]:
                    w["suggested"].append(r["suggested"])
                if len(w["examples"]) < 2:
                    w["examples"].append(r.get("definition"))
                if name not in w["files"] and len(w["files"]) < 5:
                    w["files"].append(name)
    vals = list(per_file.values())
    return {"n_files": len(vals), "n_with_small_print": sum(1 for a in vals if a.get("n_lines")),
            "n_used": sum(1 for a in vals if a.get("used")), "n_conflict": sum(1 for a in vals if a.get("conflict")),
            "n_scale_lines": sum(len(a.get("rating_scale") or []) for a in vals),
            "new_words": sorted(new.values(), key=lambda x: (-x["count"], x["word"]))}


def def_adj_summary(per_file: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """v0103 (批729): the ADJ CLOSE upside of the round, counted by state (ADJ_OK(因子1…) counts as ADJ_OK,
    ADJ_ABSURD(…) as ADJ_ABSURD).  A measurement, not a gate: a missing price row is named, never a FAIL."""
    states: Dict[str, int] = {}
    why: Dict[str, int] = {}
    for a in per_file.values():
        key = str(a.get("state") or "NONE").split("(")[0]
        states[key] = states.get(key, 0) + 1
        if a.get("why") and a.get("upside_adj") is None and a.get("has_target"):
            reason = str(a["why"])[:80]
            why[reason] = why.get(reason, 0) + 1
    vals = list(per_file.values())
    bases: Dict[str, int] = {}
    for a in vals:
        if a.get("upside_adj") is not None:
            key = str(a.get("basis") or "?").split("(")[0]
            bases[key] = bases.get(key, 0) + 1
    return {"n_files": len(vals), "n_with_target": sum(1 for a in vals if a.get("has_target")),
            "bases": dict(sorted(bases.items(), key=lambda kv: (-kv[1], kv[0]))),
            "n_adj": sum(1 for a in vals if a.get("upside_adj") is not None),
            "states": dict(sorted(states.items(), key=lambda kv: (-kv[1], kv[0]))),
            "why": [{"reason": r, "count": n} for r, n in sorted(why.items(), key=lambda kv: (-kv[1], kv[0]))[:6]],
            "files": {name: a for name, a in sorted(per_file.items())}}


def def_main(argv: Optional[Sequence[str]] = None) -> int:
    if argv is None and "--unit-file" in sys.argv[1:]:
        at = sys.argv.index("--unit-file")
        return def_unit_file(sys.argv[at + 1]) if at + 1 < len(sys.argv) else 2
    if argv is None and "--selftest" in sys.argv[1:]:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            pass
        print(f"=== VRN_AutoTestLoop {LOOP_VERSION} · 自測門(單元測試 + 合成小批;沙盒零網路)===")
        return def_selftest()
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
    parser.add_argument("--truth", default="", help="人工真值 JSON（schema 見 docs/VIA_VRN_AUTOTEST.md；只放操作員手上，不入庫）")
    parser.add_argument("--g08-sample", type=int, default=G08_SAMPLE, help="G08 冪等抽幾檔再入庫(預設 12;0=全批)")
    parser.add_argument("--g08-full", action="store_true", help="G08 冪等把整批再入庫一次(舊行為;慢)")
    parser.add_argument("--canonical-crosscheck", action="store_true",
                        help="G11 另量母倉正本 ENG086（經 SUP_MDL749）在同一份真值上的表現（僅供參考，不影響判定）")
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass
    PROGRESS["quiet"] = bool(args.quiet)
    PROGRESS["stream"] = sys.stdout
    # pdfminer logs 'Could not get FontBBox from font descriptor …' for fonts without a bounding box; the text
    # is still extracted.  The warning floods the console on real reports, so only its errors are shown.
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    # v0104 批323 啟動律:橋一直在,但從來沒有啟動過——載 Celeritas、套執行緒預算,在位 / 缺席照實印一行
    if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "activate"):
        try:
            act = VIA_ACCEL.activate()
            def_say(f"[加速器] Celeritas {'在位' if act.get('celeritas') else '缺席'} · lib {act.get('libs_available')}/"
                    f"{act.get('libs_total')} · 執行緒預算 {act.get('thread_budget')}" + (f" · {act['err']}" if act.get("err") else ""))
        except Exception as error:  # noqa: BLE001
            def_say(f"[加速器] 啟動失敗(不擋跑):{error.__class__.__name__}: {str(error)[:80]}")
    else:
        def_say("[加速器] 橋缺席(不擋跑;supportive modules/VIA_SuperAccel_Module.py 找不到)")
    if not args.samples and os.name == "nt" and Path(DEFAULT_SAMPLES_WINDOWS).is_dir():
        args.samples = DEFAULT_SAMPLES_WINDOWS
    workdir = Path(args.out) if args.out else Path(tempfile.gettempdir()) / f"VRN_AutoTest_{time.strftime('%Y%m%dT%H%M%S')}"
    workdir.mkdir(parents=True, exist_ok=True)
    engines = Engines()
    engines.canonical_crosscheck = bool(args.canonical_crosscheck)
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
        "truth_summary": state.get("truth_summary", {}), "fieldspec": state.get("fieldspec", []),
        "vcgc": (engines.core.vcgc_status() if engines.core is not None else {}),
    }
    appendix = def_appendix_summary(LAST_APPENDIX)
    report["appendix"] = {k: v for k, v in appendix.items() if k != "new_words"}
    report["appendix_new_rating_words"] = appendix["new_words"]
    if appendix["n_files"]:
        (workdir / "RATING_SCALE_CANDIDATES.json").write_text(
            json.dumps(appendix["new_words"], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        if not args.quiet:
            print(f"[附錄] 讀到附錄小字 {appendix['n_with_small_print']}/{appendix['n_files']} 檔 · "
                  f"附錄定出券商 {appendix['n_used']} 檔 · 與檔名不一致待看 {appendix['n_conflict']} 檔 · "
                  f"評等定義 {appendix['n_scale_lines']} 行 · 新詞 {len(appendix['new_words'])} 個(候選,不寫冊)")
    adj = def_adj_summary(LAST_ADJ)
    report["adj"] = adj
    if adj["n_files"] and not args.quiet:
        top = " · ".join(f"{k} {v}" for k, v in adj["states"].items() if k != "ADJ_OK")
        print(f"[ADJ] 上漲空間用最新 ADJ CLOSE:算出 {adj['n_adj']}/{adj['n_with_target']} 檔(有目標價者)"
              + (f" · 因子分母 {' · '.join(f'{k} {v}' for k, v in adj['bases'].items())}" if adj["bases"] else "")
              + (f" · 其餘 {top}" if top else "") + (f" · 最多的因由:{adj['why'][0]['reason']}" if adj["why"] else ""))
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
