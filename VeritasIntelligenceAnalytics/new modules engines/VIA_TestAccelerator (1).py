#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA-TST-MGR-001 : Test Accelerator.

把既有各引擎的「報告」轉成**測試平台的產物**：機器可消費的判定、
回歸比對、閃爍偵測，以及一頁能收人工驗收結論的 UI。

差別在哪：
    治理引擎的產物是 HTML，給人看，看完就結束。
    測試加速器的產物是 **verdict**，給流程用，用來決定要不要放行。

四件事：
    1. NORMALISE  任何帶 gates/verdict 的快照 -> 統一測試案例模型
    2. REGRESS    與上一次成功基線比對 -> NEW_FAILURE / FIXED / STILL_FAILING
    3. FLAKY      跨歷次執行偵測翻來覆去的案例 -> 這種案例的訊號不可信
    4. UAT        產出人工驗收頁；人在頁面上按通過/失敗，貼回權杖即歸檔

最有價值的輸出不是通過率，是**機器與人不同調的那幾筆**：
機器 PASS 但人判 FAIL = 這道檢查根本沒檢查到真正重要的事。
那才是下一版該補的閘門。

只讀不改。輸入的快照永遠不動。

用法：
    python VIA_TestAccelerator.py --scan <快照目錄> --out <輸出目錄>
    python VIA_TestAccelerator.py --scan ... --ingest uat_result.txt
    python VIA_TestAccelerator.py --scan ... --junit   # CI 模式，非零退出碼代表失敗
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
import hashlib
import json
import os
import re
import sys
import webbrowser
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.sax.saxutils import escape as xml_escape

URN_SELF = "VIA-TST-MGR-001"
VERSION = "v0100"
SPEC_VERSION = "VIA-SSOT-SPEC-v0100"

UAT_BEGIN = "==VIA-UAT-BEGIN=="
UAT_END = "==VIA-UAT-END=="

STATUS_TO_RESULT = {"PASS": "PASS", "WARN": "WARN", "FAIL": "FAIL"}


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


# ---------------------------------------------------------------------------
# §1  統一測試案例模型
# ---------------------------------------------------------------------------

@dataclass
class TestCase:
    suite: str                       # 來源引擎
    case_id: str                     # 閘門代碼，例如 G15 / F08 / D02
    name: str
    machine: str = "UNKNOWN"         # PASS | WARN | FAIL
    detail: str = ""
    stamp: str = ""
    source: str = ""
    regression: str = "NEW"          # NEW | FIXED | NEW_FAILURE | STILL_FAILING | STABLE
    flaky: bool = False
    flips: int = 0
    human: str = ""                  # PASS | FAIL | SKIP （人工驗收）
    human_note: str = ""
    divergence: str = ""             # MACHINE_MISSED | MACHINE_OVERSTRICT | AGREED

    @property
    def key(self) -> str:
        return self.suite + "::" + self.case_id


def load_snapshot(path: Path) -> Optional[Dict[str, Any]]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError, OSError):
        return None
    if not isinstance(doc, dict) or "gates" not in doc:
        return None
    return doc


def suite_name(doc: Dict[str, Any], path: Path) -> str:
    for key in ("engine", "controller", "launcher", "schema"):
        value = doc.get(key)
        if isinstance(value, str) and value:
            return value.split(".")[-1]
    return path.stem


def normalise(paths: List[Path]) -> Tuple[List[TestCase], List[Dict[str, Any]]]:
    cases: List[TestCase] = []
    runs: List[Dict[str, Any]] = []
    for path in sorted(paths, key=lambda p: p.stat().st_mtime):
        doc = load_snapshot(path)
        if doc is None:
            continue
        suite = suite_name(doc, path)
        stamp = str(doc.get("stamp") or datetime.fromtimestamp(
            path.stat().st_mtime).strftime("%Y%m%d_%H%M%S"))
        gate_rows = doc.get("gates") or []
        parsed = 0
        for gate in gate_rows:
            if not isinstance(gate, dict):
                continue
            code = str(gate.get("code") or gate.get("Code") or "")
            title = str(gate.get("title") or gate.get("Title") or "")
            status = str(gate.get("status") or gate.get("Status") or "").upper()
            if not code or status not in STATUS_TO_RESULT:
                continue
            cases.append(TestCase(
                suite=suite, case_id=code, name=title,
                machine=STATUS_TO_RESULT[status],
                detail=str(gate.get("detail") or gate.get("Detail") or ""),
                stamp=stamp, source=str(path)))
            parsed += 1
        runs.append({"suite": suite, "stamp": stamp, "path": str(path),
                     "verdict": str(doc.get("verdict", "")), "cases": parsed})
    return cases, runs


# ---------------------------------------------------------------------------
# §2  回歸與閃爍
# ---------------------------------------------------------------------------

def latest_per_case(cases: List[TestCase]) -> Dict[str, TestCase]:
    newest: Dict[str, TestCase] = {}
    for case in sorted(cases, key=lambda c: c.stamp):
        newest[case.key] = case
    return newest


def analyse_history(cases: List[TestCase]) -> Tuple[Dict[str, TestCase], Dict[str, List[str]]]:
    """回傳（每個案例的最新一次, 每個案例的歷史狀態序列）。"""
    history: Dict[str, List[Tuple[str, str]]] = collections.defaultdict(list)
    for case in cases:
        history[case.key].append((case.stamp, case.machine))
    for key in history:
        history[key].sort()

    current = latest_per_case(cases)
    sequences: Dict[str, List[str]] = {}
    for key, entries in history.items():
        states = [state for _, state in entries]
        sequences[key] = states
        case = current[key]
        if len(states) == 1:
            case.regression = "NEW"
        else:
            previous = states[-2]
            now = states[-1]
            if previous == now:
                case.regression = "STILL_FAILING" if now == "FAIL" else "STABLE"
            elif now == "FAIL":
                case.regression = "NEW_FAILURE"
            elif previous == "FAIL":
                case.regression = "FIXED"
            else:
                case.regression = "STABLE"
        # 閃爍：狀態變化次數 >= 2，代表這道檢查自己不穩定
        flips = sum(1 for i in range(1, len(states)) if states[i] != states[i - 1])
        case.flips = flips
        case.flaky = flips >= 2
    return current, sequences


# ---------------------------------------------------------------------------
# §3  人工驗收（UAT）
# ---------------------------------------------------------------------------

def uat_token(cases: List[TestCase], stamp: str) -> str:
    payload = "|".join(sorted(c.key + ":" + c.machine for c in cases))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return "==VIA-UAT==%s-%s" % (stamp, digest)


def parse_uat(text: str) -> Dict[str, Dict[str, str]]:
    """解析人工驗收回傳區塊。格式：suite::case | PASS/FAIL/SKIP | 備註"""
    out: Dict[str, Dict[str, str]] = {}
    inside = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(UAT_BEGIN):
            inside = True
            continue
        if stripped.startswith(UAT_END):
            inside = False
            continue
        if not inside or not stripped or stripped.startswith("#"):
            continue
        parts = [p.strip() for p in stripped.split("|")]
        if len(parts) < 2:
            continue
        verdict = parts[1].upper()
        if verdict not in ("PASS", "FAIL", "SKIP"):
            continue
        out[parts[0]] = {"human": verdict,
                         "note": parts[2] if len(parts) > 2 else ""}
    return out


def apply_uat(cases: Dict[str, TestCase], uat: Dict[str, Dict[str, str]]) -> None:
    for key, case in cases.items():
        record = uat.get(key)
        if not record:
            continue
        case.human = record["human"]
        case.human_note = record["note"]
        if case.human == "SKIP":
            case.divergence = ""
            continue
        # 判準是「會不會擋下發布」，不是字面相等。
        # WARN 不擋，所以 機器WARN + 人FAIL 仍然是機器漏掉了，不是同調。
        machine_blocks = case.machine == "FAIL"
        human_blocks = case.human == "FAIL"
        if machine_blocks == human_blocks:
            case.divergence = "AGREED"
        elif human_blocks:
            # 機器放行、人擋下 —— 這道檢查沒檢查到真正重要的事
            case.divergence = "MACHINE_MISSED"
        else:
            # 機器擋下、人放行 —— 判準太嚴或已過時
            case.divergence = "MACHINE_OVERSTRICT"


# ---------------------------------------------------------------------------
# §4  輸出：JUnit / HTML / JSON
# ---------------------------------------------------------------------------

def to_junit(cases: List[TestCase]) -> str:
    by_suite: Dict[str, List[TestCase]] = collections.defaultdict(list)
    for case in cases:
        by_suite[case.suite].append(case)
    parts = ['<?xml version="1.0" encoding="UTF-8"?>', "<testsuites>"]
    for suite, items in sorted(by_suite.items()):
        failures = len([c for c in items if c.machine == "FAIL" or c.human == "FAIL"])
        skipped = len([c for c in items if c.human == "SKIP"])
        parts.append('  <testsuite name="%s" tests="%d" failures="%d" skipped="%d">'
                     % (xml_escape(suite), len(items), failures, skipped))
        for case in items:
            name = "%s %s" % (case.case_id, case.name)
            parts.append('    <testcase classname="%s" name="%s">'
                         % (xml_escape(suite), xml_escape(name)))
            if case.human == "SKIP":
                parts.append('      <skipped/>')
            elif case.machine == "FAIL" or case.human == "FAIL":
                who = "machine" if case.machine == "FAIL" else "human"
                message = "%s: %s" % (who, case.detail or case.human_note)
                parts.append('      <failure message="%s">%s</failure>'
                             % (xml_escape(message[:200]),
                                xml_escape((case.detail + " " + case.human_note).strip())))
            elif case.machine == "WARN":
                parts.append('      <system-out>WARN: %s</system-out>'
                             % xml_escape(case.detail[:300]))
            if case.flaky:
                parts.append('      <system-err>FLAKY: %d 次狀態翻轉，訊號不可信</system-err>'
                             % case.flips)
            parts.append("    </testcase>")
        parts.append("  </testsuite>")
    parts.append("</testsuites>")
    return "\n".join(parts)


def esc(value: Any) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def klass(value: str) -> str:
    upper = str(value).upper()
    if upper in ("PASS", "GREEN", "FIXED", "STABLE", "AGREED"):
        return "ok"
    if upper in ("FAIL", "RED", "NEW_FAILURE", "MACHINE_MISSED", "STILL_FAILING"):
        return "fail"
    if upper in ("WARN", "AMBER", "SKIP", "NEW", "MACHINE_OVERSTRICT"):
        return "warn"
    return ""


def table(items: List[Dict[str, Any]], fields: List[str], status: str = "") -> str:
    if not items:
        return "<tr><td colspan='%d' class='muted'>—— 無 ——</td></tr>" % len(fields)
    out = []
    for item in items:
        cells = []
        for name in fields:
            value = item.get(name, "")
            if isinstance(value, bool):
                value = "YES" if value else ""
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
th,td{border-bottom:1px solid #ececed;padding:5px 7px;text-align:left;vertical-align:top;white-space:normal;overflow-wrap:anywhere}
th{background:#eeeeef;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#5c5e60}
.ok{color:var(--green);font-weight:600}.warn{color:var(--amber);font-weight:600}.fail{color:var(--red);font-weight:600}
.muted{color:#9a9c9e;text-align:center;padding:12px}
button{font:inherit;padding:2px 9px;margin-right:3px;border:1px solid var(--line);background:#fff;cursor:pointer;border-radius:2px}
button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
input.note{width:100%;font:inherit;padding:2px 5px;border:1px solid var(--line);border-radius:2px}
textarea{width:100%;height:190px;font-family:Consolas,monospace;font-size:11.5px;padding:9px;border:1px solid var(--line);border-radius:3px}
pre{background:var(--panel);border:1px solid var(--line);padding:11px;font-size:11px;white-space:pre-wrap;max-height:28vh;overflow:auto}
"""


def render(cases: List[TestCase], runs: List[Dict[str, Any]], token: str,
           stamp: str, verdict: str, has_uat: bool) -> str:
    rows = [asdict(c) | {"key": c.key} for c in cases]
    machine = collections.Counter(c.machine for c in cases)
    regress = collections.Counter(c.regression for c in cases)
    flaky = [r for r in rows if r["flaky"]]
    diverge = [r for r in rows if r["divergence"] in ("MACHINE_MISSED", "MACHINE_OVERSTRICT")]
    new_fail = [r for r in rows if r["regression"] == "NEW_FAILURE"]

    uat_rows = ""
    for case in cases:
        uat_rows += (
            "<tr data-key='%s'><td>%s</td><td>%s</td><td class='%s'>%s</td>"
            "<td><button data-v='PASS'>通過</button><button data-v='FAIL'>失敗</button>"
            "<button data-v='SKIP'>略過</button></td>"
            "<td><input class='note' placeholder='備註（選填）'></td></tr>"
            % (esc(case.key), esc(case.suite), esc(case.case_id + " " + case.name),
               klass(case.machine), esc(case.machine)))

    divergence_note = ("""<h2>機器與人不同調</h2>
<p class="lede"><strong>MACHINE_MISSED</strong>＝機器說過、人說不過：這道檢查沒檢查到真正重要的事，
下一版必須補閘門。<strong>MACHINE_OVERSTRICT</strong>＝機器說不過、人說可以：判準過時，該裁決規則本身。
這張表比通過率有價值得多。</p>
<table><colgroup><col style="width:22%%"><col style="width:22%%"><col style="width:12%%"><col style="width:12%%"><col style="width:32%%"></colgroup>
<tr><th>Case</th><th>Name</th><th>機器</th><th>人工</th><th>不同調類型</th></tr>%s</table>"""
                       % table(diverge, ["key", "name", "machine", "human", "divergence"],
                               "divergence")) if has_uat else ""

    return """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Test Accelerator</title><style>%s</style></head><body>
<div class="seal">驗</div>
<h1>Test Accelerator</h1>
<p class="lede">%s · 判定 <span class="%s">%s</span> · %d 個案例 / %d 次執行 · 只讀不改</p>
<div class="cards">
  <div class="card"><div class="k">Pass</div><div class="v ok">%d</div></div>
  <div class="card"><div class="k">Warn</div><div class="v warn">%d</div></div>
  <div class="card"><div class="k">Fail</div><div class="v fail">%d</div></div>
  <div class="card"><div class="k">新增失敗</div><div class="v fail">%d</div></div>
  <div class="card"><div class="k">已修復</div><div class="v ok">%d</div></div>
  <div class="card"><div class="k">閃爍</div><div class="v warn">%d</div></div>
  <div class="card"><div class="k">不同調</div><div class="v fail">%d</div></div>
</div>

<h2>回歸比對</h2>
<p class="lede">NEW_FAILURE 是唯一該擋下發布的訊號；STILL_FAILING 是已知債務；FLAKY 的案例訊號不可信，先修檢查本身。</p>
<table><colgroup><col style="width:16%%"><col style="width:8%%"><col style="width:20%%"><col style="width:10%%"><col style="width:14%%"><col style="width:6%%"><col style="width:26%%"></colgroup>
<tr><th>Suite</th><th>Case</th><th>Name</th><th>機器</th><th>回歸</th><th>翻轉</th><th>Detail</th></tr>%s</table>

<h2>人工驗收</h2>
<p class="lede">在下表按鈕做判定，按「產生回傳區塊」把結果貼回，用
<code>--ingest</code> 歸檔。不需要伺服器，純靜態頁。</p>
<table><colgroup><col style="width:16%%"><col style="width:34%%"><col style="width:10%%"><col style="width:18%%"><col style="width:22%%"></colgroup>
<tr><th>Suite</th><th>Case</th><th>機器判定</th><th>人工判定</th><th>備註</th></tr>%s</table>
<p><button id="gen">產生回傳區塊</button> <button id="all">全部標通過</button></p>
<textarea id="out" readonly></textarea>

%s

<h2>執行歷史</h2>
<table><colgroup><col style="width:22%%"><col style="width:16%%"><col style="width:12%%"><col style="width:10%%"><col style="width:40%%"></colgroup>
<tr><th>Suite</th><th>Stamp</th><th>Verdict</th><th>Cases</th><th>Source</th></tr>%s</table>

<h2>執行日誌</h2>
<pre>%s</pre>

<script>
var picks = {};
document.querySelectorAll('tr[data-key] button[data-v]').forEach(function(b){
  b.addEventListener('click', function(){
    var tr = b.closest('tr'), key = tr.getAttribute('data-key');
    tr.querySelectorAll('button[data-v]').forEach(function(x){ x.classList.remove('on'); });
    b.classList.add('on');
    picks[key] = b.getAttribute('data-v');
  });
});
document.getElementById('all').addEventListener('click', function(){
  document.querySelectorAll("tr[data-key] button[data-v='PASS']").forEach(function(b){ b.click(); });
});
document.getElementById('gen').addEventListener('click', function(){
  var lines = ['%s', '# token: %s'];
  document.querySelectorAll('tr[data-key]').forEach(function(tr){
    var key = tr.getAttribute('data-key');
    var v = picks[key];
    if (!v) { return; }
    var note = tr.querySelector('input.note').value.replace(/\\|/g, '/');
    lines.push(key + ' | ' + v + ' | ' + note);
  });
  lines.push('%s');
  document.getElementById('out').value = lines.join('\\n');
  document.getElementById('out').select();
});
</script>
</body></html>""" % (
        CSS, stamp, klass(verdict), verdict, len(cases), len(runs),
        machine.get("PASS", 0), machine.get("WARN", 0), machine.get("FAIL", 0),
        len(new_fail), regress.get("FIXED", 0), len(flaky), len(diverge),
        table(rows, ["suite", "case_id", "name", "machine", "regression",
                     "flips", "detail"], "regression"),
        uat_rows, divergence_note,
        table(runs, ["suite", "stamp", "verdict", "cases", "path"], "verdict"),
        esc("\n".join(LOG.lines)),
        UAT_BEGIN, token, UAT_END,
    )


# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="VIA_TestAccelerator.py",
        description="VIA-TST-MGR-001 測試加速器：判定、回歸、閃爍、人工驗收")
    parser.add_argument("--scan", action="append", default=[],
                        help="要掃描快照的目錄（可重複）")
    parser.add_argument("--out", default="./_testaccel", help="輸出目錄")
    parser.add_argument("--ingest", default="", help="人工驗收回傳檔")
    parser.add_argument("--junit", action="store_true", help="CI 模式：有 FAIL 就非零退出")
    parser.add_argument("--no-open", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    scans = args.scan or ["."]
    stamp = now_stamp()
    LOG.say("%s Test Accelerator %s 啟動" % (URN_SELF, VERSION), "OK")

    paths: List[Path] = []
    for root in scans:
        base = Path(root).expanduser().resolve()
        if base.is_file():
            paths.append(base)
            continue
        if not base.is_dir():
            LOG.say("略過不存在的路徑：%s" % base, "WARN")
            continue
        for hit in glob.glob(str(base / "**" / "*.json"), recursive=True):
            paths.append(Path(hit))
    LOG.say("掃到 %d 個 JSON" % len(paths))

    cases, runs = normalise(paths)
    if not cases:
        LOG.say("沒有任何帶 gates 的快照，無法組成測試案例", "FAIL")
        return 1
    LOG.say("正規化：%d 個案例，%d 次執行，%d 個 suite"
            % (len(cases), len(runs), len({c.suite for c in cases})), "OK")

    current, sequences = analyse_history(cases)
    latest = sorted(current.values(), key=lambda c: (c.suite, c.case_id))

    has_uat = False
    if args.ingest:
        ingest_path = Path(args.ingest).expanduser().resolve()
        if ingest_path.is_file():
            uat = parse_uat(ingest_path.read_text(encoding="utf-8"))
            apply_uat(current, uat)
            has_uat = bool(uat)
            LOG.say("人工驗收：收到 %d 筆判定" % len(uat), "OK" if uat else "WARN")
        else:
            LOG.say("找不到驗收檔：%s" % ingest_path, "WARN")

    fails = len([c for c in latest if c.machine == "FAIL" or c.human == "FAIL"])
    warns = len([c for c in latest if c.machine == "WARN"])
    new_failures = [c for c in latest if c.regression == "NEW_FAILURE"]
    flaky = [c for c in latest if c.flaky]
    diverge = [c for c in latest
               if c.divergence in ("MACHINE_MISSED", "MACHINE_OVERSTRICT")]

    verdict = "GREEN"
    if warns or flaky:
        verdict = "AMBER"
    if fails or new_failures:
        verdict = "RED"

    LOG.say("回歸：新增失敗 %d，已修復 %d，仍失敗 %d"
            % (len(new_failures),
               len([c for c in latest if c.regression == "FIXED"]),
               len([c for c in latest if c.regression == "STILL_FAILING"])),
            "FAIL" if new_failures else "OK")
    if flaky:
        LOG.say("閃爍案例 %d 個 —— 這些檢查自己不穩定，訊號不可信" % len(flaky), "WARN")
    if diverge:
        LOG.say("機器與人不同調 %d 筆" % len(diverge), "FAIL")

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    token = uat_token(latest, stamp)

    html_path = out_dir / ("VIA_TestAccelerator_%s.html" % stamp)
    junit_path = out_dir / ("junit_%s.xml" % stamp)
    json_path = out_dir / ("testaccel_%s.json" % stamp)
    html_path.write_text(render(latest, runs, token, stamp, verdict, has_uat),
                         encoding="utf-8")
    junit_path.write_text(to_junit(latest), encoding="utf-8")
    json_path.write_text(json.dumps({
        "schema": "VIA.TestAcceleration", "spec": SPEC_VERSION, "engine": URN_SELF,
        "version": VERSION, "generated": iso_now(), "stamp": stamp,
        "verdict": verdict, "token": token,
        "counts": {"cases": len(latest), "runs": len(runs), "fail": fails,
                   "warn": warns, "new_failure": len(new_failures),
                   "flaky": len(flaky), "divergence": len(diverge)},
        "cases": [asdict(c) for c in latest],
        "history": sequences, "runs": runs,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    LOG.say("報告 -> %s" % html_path, "OK")
    LOG.say("JUnit -> %s" % junit_path, "OK")
    print("")
    print("=" * 60)
    print(" VIA TEST ACCELERATOR  ->  %s" % verdict)
    print(" 案例 %d ｜ FAIL %d ｜ 新增失敗 %d ｜ 閃爍 %d ｜ 不同調 %d"
          % (len(latest), fails, len(new_failures), len(flaky), len(diverge)))
    print(" 驗收權杖：%s" % token)
    print("=" * 60)

    if not args.no_open:
        try:
            webbrowser.open(html_path.as_uri())
        except Exception:                                    # noqa: BLE001
            pass
    if args.junit:
        return 1 if (fails or new_failures) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
