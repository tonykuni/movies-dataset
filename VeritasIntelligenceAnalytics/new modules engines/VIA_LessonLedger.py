#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA-GOV-ENG-002 : Lesson Ledger（成敗教訓台帳）.

每支引擎都在寫自己的 log，但沒有人把它們變成**教訓**。
結果同一個坑會踩第二次 —— 這一輪就發生過：`$Primary` 與區域變數撞名
在 LL 裡早就有規則，我還是又踩了一次。

本台帳做四件事：

    1. 收成   從各引擎的 log／快照抽出「這次做了什麼、結果如何」
    2. 歸因   失敗的抽根因並正規化成签名，同一個坑不重複開單
    3. 累計   同一教訓再次出現就累加次數，不新增條目
    4. 追蹤   **這條教訓有沒有變成可機器檢查的防線**
              沒有防線的教訓＝還會再踩，這是台帳最重要的一欄

成功也要記。成功的組合就是下一次的基準，跟失敗一樣重要 ——
只記失敗會讓人以為系統一直在壞。

只增不減：教訓永不刪除，解決了就轉 RESOLVED 並保留全部歷史。

用法：
    python VIA_LessonLedger.py --scan <治理根目錄> --out <輸出目錄>
    python VIA_LessonLedger.py --scan ... --seed        # 植入已知的語言陷阱
    python VIA_LessonLedger.py --scan ... --resolve LSN-0007 --guard "G15 契約比對"
    python VIA_LessonLedger.py --scan ... --markdown    # 產出可回饋給模型的教訓文件
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
import collections
import glob
import json
import os
import re
import sqlite3
import sys
import webbrowser
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

URN_SELF = "VIA-GOV-ENG-002"
VERSION = "v0100"
SPEC_VERSION = "VIA-SSOT-SPEC-v0100"

STAMP_RE = re.compile(r"\d{8}_\d{6}")
NUM_RE = re.compile(r"\b\d+\b")
PATH_RE = re.compile(r"[A-Za-z]:\\[^\s\"']+|/(?:tmp|home|mnt|Users)/[^\s\"']+")


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Console:
    def __init__(self) -> None:
        self.lines: List[str] = []

    def say(self, message: str, level: str = "INFO") -> None:
        line = "[%s][%s] %s" % (datetime.now().strftime("%H:%M:%S"), level, message)
        self.lines.append(line)
        print(line, flush=True)


LOG = Console()


def signature(text: str) -> str:
    """把訊息正規化成簽名：拿掉時間戳、路徑、數字，同一個坑才不會開兩張單。"""
    out = PATH_RE.sub("<path>", str(text))
    out = STAMP_RE.sub("<stamp>", out)
    out = NUM_RE.sub("<n>", out)
    out = re.sub(r"\s+", " ", out).strip().lower()
    return out[:200]


# ---------------------------------------------------------------------------
# §1  教訓模型
# ---------------------------------------------------------------------------

@dataclass
class Lesson:
    lsn: str
    kind: str                      # SUCCESS | FAILURE
    domain: str
    title: str
    signature: str
    root_cause: str = ""
    remedy: str = ""
    guard: str = ""                # 已編成哪一道可機器檢查的防線
    status: str = "OPEN"           # OPEN | MITIGATED | RESOLVED
    occurrences: int = 1
    first_seen: str = ""
    last_seen: str = ""
    evidence: List[str] = field(default_factory=list)


# 本輪對話實際踩到的語言陷阱。這些目前只存在於對話裡，
# 不寫進台帳就會再踩第三次。
SEED_LESSONS: List[Dict[str, str]] = [
    {"domain": "PowerShell", "title": "New-Object 建立的泛型 List 無法用 @() 展開",
     "root_cause": "New-Object System.Collections.Generic.List[object] 回傳被 PSObject 包住的實例，"
                   "@($list) 轉換時丟 Argument types do not match",
     "remedy": "改用 [System.Collections.Generic.List[object]]::new()",
     "guard": "EngineHardening 可加規則掃 New-Object .*List\\[", "status": "MITIGATED"},
    {"domain": "PowerShell", "title": "$str.Split('\\','/') 綁到 Split(char,int)",
     "root_cause": "兩個字元參數被解讀成 (separator, count)，第二個引數轉 Int32 失敗",
     "remedy": "寫成 $str.Split([char[]]@('\\','/'))",
     "guard": "", "status": "OPEN"},
    {"domain": "PowerShell", "title": "$home 是唯讀自動變數",
     "root_cause": "賦值給 $home 直接 WriteError；$env 亦會擋掉 $env:VAR 語法",
     "remedy": "改用 $riskHome / $venv 等具名變數",
     "guard": "", "status": "OPEN"},
    {"domain": "PowerShell", "title": "函式 return 單元素陣列會被展開成純量",
     "root_cause": "return @($one) 退化成 String，StrictMode 下取 .Count 立即中斷",
     "remedy": "用逗號運算子 return , @(...)",
     "guard": "", "status": "OPEN"},
    {"domain": "PowerShell", "title": "參數與區域變數大小寫不敏感撞名",
     "root_cause": "$Primary 帶 ValidateSet，區域 $primary 賦值時觸發驗證而中斷",
     "remedy": "區域變數改名（$primaryFile）",
     "guard": "", "status": "OPEN"},
    {"domain": "PowerShell", "title": "pwsh -File 不會把逗號拆成陣列",
     "root_cause": "-Extension '.ps1,.py' 整串成為單一元素，比對不到任何副檔名，"
                   "而且不報錯，只回報掃描 0 個檔案",
     "remedy": "腳本內自行以 [,;] 拆解列表參數",
     "guard": "", "status": "MITIGATED"},
    {"domain": "PowerShell", "title": "Format-Table -AutoSize 在非互動環境輸出空白",
     "root_cause": "沒有主控台寬度時格式化器產不出內容，重導向與 CI 下報表全空",
     "remedy": "自行以 -f 排版，不依賴主機格式化器",
     "guard": "", "status": "MITIGATED"},
    {"domain": "PowerShell", "title": "巢狀 Where-Object 內的 $_ 覆蓋外層",
     "root_cause": "內層管線改寫 $_，外層屬性存取變成找不到屬性",
     "remedy": "外層值先存進具名變數再用",
     "guard": "", "status": "MITIGATED"},
    {"domain": "PowerShell", "title": "長腳本貼進互動主控台會靜默失效",
     "root_cause": "param() 不綁定，路徑變數為 null，$PSCommandPath 為 null，"
                   "而且多半不會報錯，只是什麼都沒做",
     "remedy": "一律以 -File 執行；必要時整段包 &{ }",
     "guard": "", "status": "MITIGATED"},
    {"domain": "Python", "title": "\\b 在 CJK 情境失效",
     "root_cause": "Python 把 CJK 視為 word 字元，2330.TW今日 無法命中",
     "remedy": "改用 (?![A-Za-z0-9]) 前後瞻",
     "guard": "CentralGovernanceEngine 代號鎖向量測試", "status": "RESOLVED"},
    {"domain": "Python", "title": "交替式兩端非字元時不能加 \\b",
     "root_cause": "^GSPC / .TW 這類樣式加了 \\b 永遠不命中",
     "remedy": "依內容決定邊界策略",
     "guard": "CentralGovernanceEngine build_pattern + selftest", "status": "RESOLVED"},
    {"domain": "Python", "title": "同名模組被載入兩次導致類別身分不同",
     "root_cause": "子系統自行 import 共用基底時取得另一個類別物件，issubclass 回 False",
     "remedy": "以 MRO 名稱 + 介面完整性雙軌認定",
     "guard": "CentralGovernanceConsole ProbeHarness.is_manager", "status": "RESOLVED"},
    {"domain": "治理", "title": "治理引擎掃到自己的輸出造成回饋迴路",
     "root_cause": "掃描範圍含 configs/logs/out，每跑一次就對自己的產物再發一批編號",
     "remedy": "掃描時明確排除自身工作目錄，並以產出檔名樣式二次過濾",
     "guard": "FilePriorityRouter DERIVED 類別 + Console exclude_dirs", "status": "RESOLVED"},
    {"domain": "治理", "title": "契約宣告與原始碼不符可存活整個版本世代",
     "root_cause": "介面契約只寫在文件裡，沒有任何閘門把它跟 param() 對照",
     "remedy": "以 AST 萃取真實簽章並比對，不符即 FAIL",
     "guard": "G15 CONTRACT_MATCHES_SOURCE", "status": "RESOLVED"},
    {"domain": "治理", "title": "日期被當成版本號導致快照資料夾被誤收",
     "root_cause": "家族鍵剝掉 8 位數字，且不含所在資料夾，"
                   "VRN\\20260804\\ 與別的日期夾同名檔被判為同一族",
     "remedy": "家族鍵綁資料夾；不剝日期；整族無版本記號一律不動",
     "guard": "VersionGuard v0110 三條規則", "status": "RESOLVED"},
    {"domain": "治理", "title": "還原時只取檔名會把巢狀結構壓平",
     "root_cause": "列檔用 -Recurse 但還原目標用 Join-Path origin name",
     "remedy": "保留隔離區內相對路徑並自動建目錄",
     "guard": "Recover v0110", "status": "RESOLVED"},
    {"domain": "資料", "title": "抽取層對無證據的列標 GREEN",
     "root_cause": "PeriodNormalized 為空、ValueRaw 是整列數字串，仍標 VALID/GREEN/可晉升",
     "remedy": "原子性判準：單期間單數值才可為 V，否則 P 且禁止晉升",
     "guard": "VRN_FinancialRowAuditor F01/F05/F08", "status": "MITIGATED"},
    {"domain": "環境", "title": "忽略 PEP 508 標記造成大量假衝突",
     "root_cause": "marker 未求值，python_version<3.11 / sys_platform==darwin 的相依被無條件套用",
     "remedy": "實作標記求值器；無法解析的標記一律略過而非誤報",
     "guard": "EnvManager v0110 Test-Marker", "status": "RESOLVED"},
    {"domain": "環境", "title": "偵測失敗被當成衝突",
     "root_cause": "uv 回非零且輸出 Failed to inspect 時被標成 CONFLICT",
     "remedy": "區分 UNAVAILABLE 與 CONFLICT，兩者證據等級不同",
     "guard": "EnvManager v0110 uv 仲裁", "status": "RESOLVED"},
    {"domain": "編排", "title": "以裁決而非硬故障阻斷下游",
     "root_cause": "上游回報 RED（它盡職找到問題）就讓整條鏈停擺",
     "remedy": "只有硬故障阻斷；軟裁決只影響聚合結果",
     "guard": "DownwardController hard_fail 判定", "status": "RESOLVED"},
]


# ---------------------------------------------------------------------------
# §2  收成
# ---------------------------------------------------------------------------

class Harvester:
    """從各引擎既有的 log 與快照抽出成敗事件。"""

    def __init__(self, roots: List[Path]) -> None:
        self.roots = roots
        self.events: List[Dict[str, Any]] = []
        self.sources: List[str] = []

    def run(self) -> None:
        for root in self.roots:
            if not root.is_dir():
                continue
            for path in glob.glob(str(root / "**" / "*.json"), recursive=True):
                self._json_snapshot(Path(path))
            for path in glob.glob(str(root / "**" / "*.jsonl"), recursive=True):
                self._jsonl(Path(path))
            for path in glob.glob(str(root / "**" / "*.log"), recursive=True):
                self._jsonl(Path(path))
            for path in glob.glob(str(root / "**" / "*.sqlite"), recursive=True):
                self._sqlite(Path(path))
        LOG.say("收成：%d 個來源，%d 筆事件" % (len(self.sources), len(self.events)), "OK")

    def _record(self, source: Path) -> None:
        rel = str(source)
        if rel not in self.sources:
            self.sources.append(rel)

    def _json_snapshot(self, path: Path) -> None:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError, OSError):
            return
        if not isinstance(doc, dict):
            return
        engine = str(doc.get("engine") or doc.get("controller") or doc.get("tool")
                     or doc.get("launcher") or doc.get("schema") or path.stem)
        stamp = str(doc.get("stamp") or doc.get("generated") or "")
        gates = doc.get("gates")
        if isinstance(gates, list):
            self._record(path)
            for gate in gates:
                if not isinstance(gate, dict):
                    continue
                status = str(gate.get("status", "")).upper()
                if status not in ("FAIL", "WARN", "PASS"):
                    continue
                # 閘門會觸發，代表**防線已經存在且有效**——它抓到了。
                # 所以閘門本身就是 guard，不該被算成「尚無防線的教訓」。
                self.events.append({
                    "kind": "FAILURE" if status == "FAIL" else
                            ("SUCCESS" if status == "PASS" else "WARNING"),
                    "domain": engine.split(".")[-1],
                    "title": "%s %s" % (gate.get("code", ""), gate.get("title", "")),
                    "detail": str(gate.get("detail", "")),
                    "guard": "%s@%s" % (gate.get("code", ""), engine.split(".")[-1]),
                    "stamp": stamp, "source": str(path),
                })
        verdict = str(doc.get("verdict", "")).upper()
        if verdict == "GREEN":
            # 只有全綠才記成「成功組合」。AMBER/RED 的細節已由各閘門逐條記錄，
            # 再開一張「整體裁決 RED」的單只會製造雜訊。
            self._record(path)
            self.events.append({
                "kind": "SUCCESS", "domain": engine.split(".")[-1],
                "title": "全綠通過：%s" % engine.split(".")[-1],
                "detail": "來源 %s" % path.name,
                "guard": "該引擎自身閘門",
                "stamp": stamp, "source": str(path),
            })

    def _jsonl(self, path: Path) -> None:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return
        taken = 0
        for line in lines[-500:]:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                row = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            taken += 1
            engine = str(row.get("engine") or row.get("tool") or path.stem)
            outcome = str(row.get("outcome") or row.get("verdict") or "").upper()
            failures = row.get("failures") or []
            if isinstance(failures, list) and failures:
                for item in failures[:10]:
                    # 執行步驟失敗沒有對應的偵測器 —— 這才是真正尚無防線的教訓
                    self.events.append({
                        "kind": "FAILURE", "domain": engine,
                        "title": "執行步驟失敗", "detail": str(item),
                        "stamp": str(row.get("stamp", "")), "source": str(path)})
            elif outcome == "GREEN":
                self.events.append({
                    "kind": "SUCCESS",
                    "domain": engine, "title": "執行結果 %s" % outcome,
                    "guard": "該引擎自身閘門",
                    "detail": json.dumps({k: v for k, v in row.items()
                                          if k in ("envs", "fail", "warn", "executed",
                                                   "issued", "canonicals")},
                                         ensure_ascii=False),
                    "stamp": str(row.get("stamp", "")), "source": str(path)})
        if taken:
            self._record(path)

    def _sqlite(self, path: Path) -> None:
        try:
            conn = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
        except sqlite3.Error:
            return
        try:
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")]
            if "probe_run" not in tables:
                return
            self._record(path)
            for row in conn.execute(
                    "SELECT stamp, env, code, severity, detail FROM probe_run "
                    "WHERE severity = 'FAIL' LIMIT 400"):
                # 同上：偵測器代碼本身就是防線
                self.events.append({
                    "kind": "FAILURE", "domain": "EnvDeepProbe",
                    "title": "%s %s" % (row[2], row[1]), "detail": str(row[4]),
                    "guard": "%s@EnvDeepProbe" % row[2],
                    "stamp": str(row[0]), "source": str(path)})
        except sqlite3.Error:
            return
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# §3  台帳
# ---------------------------------------------------------------------------

class LessonLedger:
    def __init__(self, out_dir: Path) -> None:
        self.out_dir = out_dir
        self.path = out_dir / "lesson_ledger.json"
        self.stream = out_dir / "lesson_stream.jsonl"
        self.lessons: Dict[str, Lesson] = {}
        self.serial = 0
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            doc = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError, OSError):
            LOG.say("教訓台帳無法解析，以空白視圖執行（原檔不動）", "WARN")
            return
        for row in doc.get("lessons", []):
            lesson = Lesson(**{k: row.get(k, v) for k, v in
                               Lesson.__dataclass_fields__.items()
                               if k in row or True})
            self.lessons[lesson.signature] = lesson
            try:
                self.serial = max(self.serial, int(lesson.lsn.rsplit("-", 1)[1]))
            except (ValueError, IndexError):
                pass
        LOG.say("台帳載入：%d 條教訓" % len(self.lessons), "OK")

    def upsert(self, kind: str, domain: str, title: str, detail: str,
               root_cause: str = "", remedy: str = "", guard: str = "",
               status: str = "OPEN", evidence: str = "") -> Lesson:
        sig = signature(title + " | " + detail)
        stamp = now_stamp()
        existing = self.lessons.get(sig)
        if existing is not None:
            existing.occurrences += 1
            existing.last_seen = stamp
            if evidence and evidence not in existing.evidence:
                existing.evidence = (existing.evidence + [evidence])[-8:]
            if root_cause and not existing.root_cause:
                existing.root_cause = root_cause
            if guard and not existing.guard:
                existing.guard = guard
            return existing
        self.serial += 1
        lesson = Lesson(
            lsn="LSN-%04d" % self.serial, kind=kind, domain=domain,
            title=title[:120], signature=sig, root_cause=root_cause,
            remedy=remedy, guard=guard, status=status,
            first_seen=stamp, last_seen=stamp,
            evidence=[evidence] if evidence else [])
        self.lessons[sig] = lesson
        return lesson

    def resolve(self, lsn: str, guard: str, status: str = "RESOLVED") -> bool:
        for lesson in self.lessons.values():
            if lesson.lsn == lsn:
                lesson.guard = guard or lesson.guard
                lesson.status = status
                lesson.last_seen = now_stamp()
                return True
        return False

    def commit(self, dry_run: bool) -> Path:
        ordered = sorted(self.lessons.values(), key=lambda l: l.lsn)
        doc = {"schema": "VIA.LessonLedger", "spec": SPEC_VERSION, "engine": URN_SELF,
               "generated": iso_now(),
               "policy": "只增不減：教訓永不刪除，解決了轉 RESOLVED 並保留歷史",
               "total": len(ordered),
               "lessons": [asdict(l) for l in ordered]}
        target = self.path if not dry_run else self.path.with_suffix(".preview.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        if not dry_run:
            with self.stream.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps({
                    "ts": iso_now(), "total": len(ordered),
                    "open": len([l for l in ordered if l.status == "OPEN"]),
                    "unguarded": len([l for l in ordered if not l.guard]),
                }, ensure_ascii=False) + "\n")
        return target

    def markdown(self) -> str:
        ordered = sorted(self.lessons.values(),
                         key=lambda l: (l.status != "OPEN", -l.occurrences, l.lsn))
        out = ["# VIA 教訓台帳 — %s" % now_stamp(), "",
               "只增不減。已解決的保留，因為它解釋了現在的防線為什麼存在。", ""]
        unguarded = [l for l in ordered if not l.guard and l.kind == "FAILURE"]
        if unguarded:
            out += ["## 尚未編成防線（會再踩）", "",
                    "| LSN | 域 | 教訓 | 次數 | 修法 |", "|---|---|---|---|---|"]
            for l in unguarded:
                out.append("| %s | %s | %s | %d | %s |"
                           % (l.lsn, l.domain, l.title.replace("|", "\\|"),
                              l.occurrences, l.remedy.replace("|", "\\|")))
            out.append("")
        out += ["## 全部教訓", "", "| LSN | 類型 | 域 | 教訓 | 根因 | 防線 | 狀態 | 次數 |",
                "|---|---|---|---|---|---|---|---|"]
        for l in ordered:
            out.append("| %s | %s | %s | %s | %s | %s | %s | %d |"
                       % (l.lsn, l.kind, l.domain, l.title.replace("|", "\\|"),
                          (l.root_cause or "—").replace("|", "\\|")[:110],
                          (l.guard or "**無**").replace("|", "\\|"),
                          l.status, l.occurrences))
        return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# §4  輸出
# ---------------------------------------------------------------------------

def esc(value: Any) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def klass(value: str) -> str:
    upper = str(value).upper()
    if upper in ("SUCCESS", "RESOLVED", "GREEN"):
        return "ok"
    if upper in ("FAILURE", "OPEN", "RED"):
        return "fail"
    if upper in ("WARNING", "MITIGATED", "AMBER"):
        return "warn"
    return ""


def table(items: List[Dict[str, Any]], fields: List[str], status: str = "",
          limit: int = 400) -> str:
    if not items:
        return "<tr><td colspan='%d' class='muted'>—— 無 ——</td></tr>" % len(fields)
    out = []
    for item in items[:limit]:
        cells = []
        for name in fields:
            value = item.get(name, "")
            if isinstance(value, (list, tuple)):
                value = " ／ ".join(str(v) for v in value)
            if name == "guard" and not value:
                cells.append("<td class='fail'>無防線</td>")
                continue
            cls = " class='%s'" % klass(str(value)) if name == status else ""
            cells.append("<td%s>%s</td>" % (cls, esc(value)))
        out.append("<tr>%s</tr>" % "".join(cells))
    return "".join(out)


CSS = """
:root{--paper:#f2f2f3;--ink:#1d1f20;--line:#d8d8d9;--red:#b0453d;--green:#3f7d5e;--amber:#c4943a;--panel:#fff}
*{box-sizing:border-box}
body{margin:0;padding:22px 26px;background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","Segoe UI",system-ui,sans-serif;font-size:12px;line-height:1.45}
.seal{display:inline-flex;width:38px;height:38px;align-items:center;justify-content:center;background:var(--red);color:#fff;font-family:"Noto Serif TC",serif;font-size:21px;border-radius:3px}
h1{font-family:"Noto Serif TC",Georgia,serif;font-size:16px;letter-spacing:.14em;text-transform:uppercase;margin:10px 0 3px}
h2{font-family:"Noto Serif TC",Georgia,serif;font-size:14px;margin:22px 0 5px}
.lede{color:#6c6e70;font-size:11.5px;margin:0 0 12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(112px,1fr));gap:9px;margin:14px 0 4px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:10px 12px}
.card .k{font-size:10px;letter-spacing:.1em;color:#8a8c8e;text-transform:uppercase}
.card .v{font-size:20px;font-family:"Noto Serif TC",Georgia,serif;margin-top:3px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:11.5px;table-layout:fixed}
th,td{border-bottom:1px solid #ececed;padding:5px 7px;text-align:left;vertical-align:top;overflow-wrap:anywhere}
th{background:#eeeeef;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#5c5e60}
.ok{color:var(--green);font-weight:600}.warn{color:var(--amber);font-weight:600}.fail{color:var(--red);font-weight:600}
.muted{color:#9a9c9e;text-align:center;padding:12px}
pre{background:var(--panel);border:1px solid var(--line);padding:11px;font-size:11px;white-space:pre-wrap;max-height:26vh;overflow:auto}
"""


def render(ledger: LessonLedger, harvester: Harvester, stamp: str) -> str:
    rows = [asdict(l) for l in sorted(ledger.lessons.values(), key=lambda l: l.lsn)]
    failures = [r for r in rows if r["kind"] == "FAILURE"]
    successes = [r for r in rows if r["kind"] == "SUCCESS"]
    unguarded = [r for r in failures if not r["guard"]]
    repeat = [r for r in rows if r["occurrences"] > 1]
    by_domain = collections.Counter(r["domain"] for r in rows)

    return """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Lesson Ledger</title><style>%s</style></head><body>
<div class="seal">鑑</div>
<h1>Lesson Ledger</h1>
<p class="lede">%s · 收成 %d 個來源 / %d 筆事件 · 只增不減</p>
<div class="cards">
  <div class="card"><div class="k">教訓總數</div><div class="v">%d</div></div>
  <div class="card"><div class="k">失敗類</div><div class="v fail">%d</div></div>
  <div class="card"><div class="k">成功類</div><div class="v ok">%d</div></div>
  <div class="card"><div class="k">尚無防線</div><div class="v fail">%d</div></div>
  <div class="card"><div class="k">重複發生</div><div class="v warn">%d</div></div>
</div>

<h2>尚未編成防線的教訓</h2>
<p class="lede"><strong>這張表才是重點。</strong>教訓沒有變成可機器檢查的防線，就只是紀錄，
下次還是會踩。次數大於 1 的代表已經踩過不只一次。</p>
<table><colgroup><col style="width:8%%"><col style="width:9%%"><col style="width:24%%"><col style="width:6%%"><col style="width:27%%"><col style="width:26%%"></colgroup>
<tr><th>LSN</th><th>域</th><th>教訓</th><th>次數</th><th>根因</th><th>修法</th></tr>%s</table>

<h2>已編成防線</h2>
<table><colgroup><col style="width:8%%"><col style="width:9%%"><col style="width:26%%"><col style="width:24%%"><col style="width:10%%"><col style="width:23%%"></colgroup>
<tr><th>LSN</th><th>域</th><th>教訓</th><th>防線</th><th>狀態</th><th>根因</th></tr>%s</table>

<h2>成功紀錄</h2>
<p class="lede">成功也要記。成功的組合就是下一次的基準，只記失敗會讓人以為系統一直在壞。</p>
<table><colgroup><col style="width:8%%"><col style="width:12%%"><col style="width:44%%"><col style="width:8%%"><col style="width:28%%"></colgroup>
<tr><th>LSN</th><th>域</th><th>內容</th><th>次數</th><th>最後出現</th></tr>%s</table>

<h2>域分佈</h2>
<table><colgroup><col style="width:60%%"><col style="width:40%%"></colgroup>
<tr><th>域</th><th>教訓數</th></tr>%s</table>

<h2>收成來源</h2>
<pre>%s</pre>

<h2>執行日誌</h2>
<pre>%s</pre>
</body></html>""" % (
        CSS, stamp, len(harvester.sources), len(harvester.events),
        len(rows), len(failures), len(successes), len(unguarded), len(repeat),
        table(unguarded, ["lsn", "domain", "title", "occurrences", "root_cause", "remedy"]),
        table([r for r in failures if r["guard"]],
              ["lsn", "domain", "title", "guard", "status", "root_cause"], "status"),
        table(successes, ["lsn", "domain", "title", "occurrences", "last_seen"]),
        table([{"domain": k, "count": v} for k, v in by_domain.most_common()],
              ["domain", "count"]),
        esc("\n".join(harvester.sources[:40])),
        esc("\n".join(LOG.lines)),
    )


# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="VIA_LessonLedger.py",
        description="VIA-GOV-ENG-002 成敗教訓台帳")
    parser.add_argument("--scan", action="append", default=[], help="要收成的根目錄（可重複）")
    parser.add_argument("--out", default="", help="輸出目錄（預設 <scan[0]>/_lessons）")
    parser.add_argument("--seed", action="store_true", help="植入已知的語言與治理陷阱")
    parser.add_argument("--resolve", default="", help="把某條教訓標為已解決，例如 LSN-0007")
    parser.add_argument("--guard", default="", help="與 --resolve 併用，記錄防線名稱")
    parser.add_argument("--markdown", action="store_true", help="另外產出教訓 markdown")
    parser.add_argument("--commit", action="store_true", help="寫入台帳（預設 dry-run）")
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    raw = args.scan or ["."]
    roots: List[Path] = []
    for item in raw:
        for piece in str(item).split(","):
            piece = piece.strip().strip("'\"")
            if not piece:
                continue
            path = Path(piece).expanduser().resolve()
            if path.is_dir():
                roots.append(path)
            else:
                LOG.say("略過不存在的路徑：%s" % path, "WARN")
    if not roots:
        print("沒有有效的 --scan", file=sys.stderr)
        return 2

    stamp = now_stamp()
    out_dir = Path(args.out).expanduser().resolve() if args.out else roots[0] / "_lessons"
    out_dir.mkdir(parents=True, exist_ok=True)
    dry_run = not args.commit

    LOG.say("%s Lesson Ledger %s 啟動（%s）"
            % (URN_SELF, VERSION, "DRY-RUN" if dry_run else "COMMIT"), "OK")

    ledger = LessonLedger(out_dir)

    if args.seed:
        added = 0
        for row in SEED_LESSONS:
            before = len(ledger.lessons)
            ledger.upsert(kind="FAILURE", domain=row["domain"], title=row["title"],
                          detail=row["root_cause"], root_cause=row["root_cause"],
                          remedy=row["remedy"], guard=row.get("guard", ""),
                          status=row.get("status", "OPEN"), evidence="seed")
            if len(ledger.lessons) > before:
                added += 1
        LOG.say("植入已知陷阱：新增 %d 條（既有的只累加次數）" % added, "OK")

    harvester = Harvester(roots)
    harvester.run()

    new_count = 0
    for event in harvester.events:
        before = len(ledger.lessons)
        ledger.upsert(kind=event["kind"] if event["kind"] != "WARNING" else "FAILURE",
                      domain=event["domain"], title=event["title"],
                      detail=event["detail"], guard=event.get("guard", ""),
                      evidence=event["source"])
        if len(ledger.lessons) > before:
            new_count += 1
    LOG.say("收成歸檔：新增 %d 條，其餘累加既有教訓" % new_count, "OK")

    if args.resolve:
        if ledger.resolve(args.resolve, args.guard):
            LOG.say("%s 已標為 RESOLVED（防線：%s）" % (args.resolve, args.guard or "未填"), "OK")
        else:
            LOG.say("找不到 %s" % args.resolve, "WARN")

    unguarded = [l for l in ledger.lessons.values() if l.kind == "FAILURE" and not l.guard]
    repeat = [l for l in ledger.lessons.values() if l.occurrences > 1]
    LOG.say("教訓 %d 條：尚無防線 %d、重複發生 %d"
            % (len(ledger.lessons), len(unguarded), len(repeat)),
            "FAIL" if unguarded else "OK")
    for lesson in sorted(unguarded, key=lambda l: -l.occurrences)[:8]:
        LOG.say("  無防線 %s [%s] %s（%d 次）"
                % (lesson.lsn, lesson.domain, lesson.title, lesson.occurrences), "WARN")

    target = ledger.commit(dry_run)
    html_path = out_dir / ("VIA_LessonLedger_%s.html" % stamp)
    html_path.write_text(render(ledger, harvester, stamp), encoding="utf-8")
    md_path = out_dir / "VIA_Lessons.md"
    if args.markdown:
        md_path.write_text(ledger.markdown(), encoding="utf-8")
        LOG.say("教訓文件 -> %s" % md_path.name, "OK")

    verdict = "GREEN"
    if repeat:
        verdict = "AMBER"
    if unguarded:
        verdict = "RED"

    LOG.say("台帳 -> %s" % target.name, "OK")
    LOG.say("報告 -> %s" % html_path, "OK")
    print("")
    print("=" * 60)
    print(" VIA LESSON LEDGER  ->  %s" % verdict)
    print(" 教訓 %d ｜ 失敗類 %d ｜ 成功類 %d ｜ 尚無防線 %d ｜ 重複 %d"
          % (len(ledger.lessons),
             len([l for l in ledger.lessons.values() if l.kind == "FAILURE"]),
             len([l for l in ledger.lessons.values() if l.kind == "SUCCESS"]),
             len(unguarded), len(repeat)))
    if dry_run:
        print(" DRY-RUN：只寫 .preview.json，--commit 才動正式台帳")
    print("=" * 60)
    if not args.no_open and not args.json:
        try:
            webbrowser.open(html_path.as_uri())
        except Exception:                                # noqa: BLE001
            pass
    if args.json:
        print(json.dumps({"verdict": verdict, "lessons": len(ledger.lessons),
                          "unguarded": len(unguarded)}, ensure_ascii=False))
    return 0 if verdict != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
