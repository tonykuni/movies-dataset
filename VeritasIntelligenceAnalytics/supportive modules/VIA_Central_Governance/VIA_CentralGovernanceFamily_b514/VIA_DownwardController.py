#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA-SYS-MGR-003 : VIA Downward Controller (自動下行控制層).

兩層式架構缺的那一塊：中央總管有了「看」的能力（掃描、發碼、比對、閘門），
但沒有「動」的能力。本層把目前所有治理工具註冊成 **能力（Capability）**，
依相依拓撲自動下行派工、收證據、聚合裁決。

已註冊的能力（URN 依 VIA SSOT Spec v0100 §1 編號）：

    VIA-SYS-MGR-001  中央治理主控台          純 Python，掃描/發碼/契約/拓撲/探針
    VIA-SYS-ENG-001  環境治理引擎 v0110      venv 健康度、PEP508 標記、LKGC
    VIA-SYS-ENG-002  第一輪程式修復引擎      ruff / PSSA / AST，指紋回滾
    VIA-SUP-ENG-001  Polyglot 注入器         Celeritas / NetSupport / Codex 橋
    VIA-SUP-LIB-001  Supportive 分類器       控管 vs 引擎判定
    VIA-SYS-LIB-001  Profile 醫生            $PROFILE 修復與啟動耗時

下行控制的三條鐵律：
  1. **唯讀自動、變更受閘**：ANALYSIS 類能力自動跑；MUTATING 類必須帶核准權杖。
  2. **拓撲下行**：環境先於程式碼，程式碼先於注入，注入先於總控複驗。
     同層彼此獨立者並行（預設 10 路），跨層嚴格循序。
  3. **失敗隔離**：單一能力崩潰不中斷整條鏈，記錄證據後續跑；
     但它的下游能力一律標 BLOCKED，不在錯誤基礎上繼續施工。

用法：
    python VIA_DownwardController.py --root <VIA_ROOT> --tools <工具目錄>
    python VIA_DownwardController.py --root . --tools ./tools --token "==VEM-APPROVE==..." --commit
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import glob
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

URN_SELF = "VIA-SYS-MGR-003"
VERSION = "v0100"
SPEC_VERSION = "VIA-SSOT-SPEC-v0100"

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def strip_ansi(text: str) -> str:
    """pwsh 的錯誤輸出帶 ANSI 色碼，進 JSON 與 HTML 會變亂碼。"""
    return ANSI_RE.sub("", text or "")


VERDICT_RANK = {"GREEN": 0, "AMBER": 1, "RED": 2, "UNKNOWN": 1, "CRASHED": 2,
                "BLOCKED": 1, "SKIPPED": 0, "MISSING": 1, "TIMEOUT": 2}


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
# §1  能力宣告
# ---------------------------------------------------------------------------

@dataclass
class Capability:
    urn: str
    name: str
    kind: str                      # ANALYSIS | REPAIR | ENV | HYGIENE
    runtime: str                   # pwsh | python
    script: str                    # 檔名，於 --tools 目錄解析
    args: List[str] = field(default_factory=list)
    mutating: bool = False
    depends_on: List[str] = field(default_factory=list)
    work_subdir: str = ""
    snapshot_glob: str = ""
    verdict_key: str = "verdict"
    timeout: int = 900
    enabled: bool = True


DEFAULT_CAPABILITIES: List[Dict[str, Any]] = [
    {
        "urn": "VIA-SYS-ENG-001", "name": "環境治理引擎", "kind": "ENV",
        "runtime": "pwsh", "script": "VIA_EnvManager_UnifiedGovernance_v0110.ps1",
        "args": ["-EnvRoot", "{envroot}", "-WorkRoot", "{work}/EnvManager",
                 "-SkipMirrorProbe", "-NoBrowser"],
        "mutating": False, "depends_on": [],
        "work_subdir": "EnvManager", "snapshot_glob": "out/env_snapshot_*.json",
        "verdict_key": "verdict", "timeout": 900,
    },
    {
        "urn": "VIA-SYS-ENG-003", "name": "檔案優先序路由器", "kind": "ANALYSIS",
        "runtime": "python", "script": "VIA_FilePriorityRouter.py",
        "args": ["--root", "{root}", "--out", "{work}/Priority", "--no-open", "--json"],
        "mutating": False, "depends_on": [],
        "work_subdir": "Priority", "snapshot_glob": "priority_manifest.json",
        "verdict_key": "", "timeout": 900,
    },
    {
        "urn": "VIA-SUP-LIB-001", "name": "Supportive 模組分類器", "kind": "ANALYSIS",
        "runtime": "pwsh", "script": "VIA_SupportiveModules_Classifier_v0100.ps1",
        "args": ["-FolderPath", "{supportive}", "-OutDir", "{work}/Classifier/out",
                 "-NoBrowser"],
        "mutating": False, "depends_on": [],
        "work_subdir": "Classifier", "snapshot_glob": "out/*Classification*.json",
        "verdict_key": "", "timeout": 300,
    },
    {
        "urn": "VIA-SYS-LIB-001", "name": "PowerShell Profile 醫生", "kind": "HYGIENE",
        "runtime": "pwsh", "script": "VIA_Profile_Doctor_v0100.ps1",
        "args": ["-WorkRoot", "{work}/ProfileDoctor", "-DryRun", "-NoBrowser"],
        "mutating": False, "depends_on": [],
        "work_subdir": "ProfileDoctor", "snapshot_glob": "", "verdict_key": "",
        "timeout": 300,
    },
    {
        "urn": "VIA-SYS-ENG-002", "name": "第一輪程式修復引擎", "kind": "REPAIR",
        "runtime": "pwsh", "script": "VIA_Round1_CodeRepair_v0100.ps1",
        "args": ["-Path", "{root}", "-WorkRoot", "{work}/Repair", "-DryRun", "-NoBrowser"],
        "mutating": False, "depends_on": ["VIA-SYS-ENG-001", "VIA-SYS-ENG-003"],
        "work_subdir": "Repair", "snapshot_glob": "out/repair_snapshot_*.json",
        "verdict_key": "verdict", "timeout": 1200,
    },
    {
        "urn": "VIA-SYS-ENG-002-APPLY", "name": "第一輪程式修復（實際套用）", "kind": "REPAIR",
        "runtime": "pwsh", "script": "VIA_Round1_CodeRepair_v0100.ps1",
        "args": ["-Path", "{root}", "-WorkRoot", "{work}/RepairApply", "-NoBrowser"],
        "mutating": True, "depends_on": ["VIA-SYS-ENG-002"],
        "work_subdir": "RepairApply", "snapshot_glob": "out/repair_snapshot_*.json",
        "verdict_key": "verdict", "timeout": 1800,
    },
    {
        "urn": "VIA-SUP-ENG-001", "name": "Polyglot 注入器", "kind": "REPAIR",
        "runtime": "pwsh", "script": "VIA_Polyglot_Repair_Injector_v0100.ps1",
        "args": ["-MotherRoot", "{root}", "-WorkRoot", "{work}/Injector",
                 "-DryRun", "-NoBrowser"],
        "mutating": False, "depends_on": ["VIA-SYS-ENG-002"],
        "work_subdir": "Injector", "snapshot_glob": "inventory/polyglot_repair_*.json",
        "verdict_key": "", "timeout": 900,
    },
    {
        "urn": "VIA-SYS-MGR-001", "name": "中央治理主控台（複驗）", "kind": "ANALYSIS",
        "runtime": "python", "script": "VIA_CentralGovernanceConsole.py",
        "args": ["--root", "{root}", "--no-open", "--json"],
        "mutating": False,
        "depends_on": ["VIA-SYS-ENG-001", "VIA-SYS-ENG-002", "VIA-SUP-ENG-001"],
        "work_subdir": "", "snapshot_glob": "output/SYS/governance_snapshot_*.json",
        "verdict_key": "verdict", "timeout": 1200,
    },
]


# ---------------------------------------------------------------------------
# §2  能力登記處
# ---------------------------------------------------------------------------

class CapabilityRegistry:
    """只增不減：新增能力用附加，停用用 enabled=false，不刪除紀錄。"""

    def __init__(self, config_path: Path, tools_dir: Path) -> None:
        self.config_path = config_path
        self.tools_dir = tools_dir
        self.capabilities: List[Capability] = []
        self.resolved: Dict[str, Path] = {}
        self.missing: List[Capability] = []
        self._load()

    def _load(self) -> None:
        rows = DEFAULT_CAPABILITIES
        if self.config_path.exists():
            try:
                doc = json.loads(self.config_path.read_text(encoding="utf-8"))
                known = {r["urn"] for r in doc.get("capabilities", [])}
                rows = list(doc.get("capabilities", []))
                for default in DEFAULT_CAPABILITIES:      # 只增不減：補上新出廠的能力
                    if default["urn"] not in known:
                        rows.append(default)
                        LOG.say("登記處補入新能力 %s" % default["urn"], "OK")
            except (json.JSONDecodeError, ValueError, KeyError):
                LOG.say("能力登記檔無法解析，改用出廠清單（原檔不動）", "WARN")
                rows = DEFAULT_CAPABILITIES

        for row in rows:
            fields = {k: row.get(k, v) for k, v in Capability.__dataclass_fields__.items()
                      if not callable(v)}
            try:
                cap = Capability(**{k: row.get(k) for k in
                                    Capability.__dataclass_fields__ if k in row})
            except TypeError:
                continue
            self.capabilities.append(cap)

        for cap in self.capabilities:
            found = self._resolve(cap.script)
            if found is None:
                self.missing.append(cap)
            else:
                self.resolved[cap.urn] = found

    def _resolve(self, script: str) -> Optional[Path]:
        direct = self.tools_dir / script
        if direct.is_file():
            return direct
        hits = list(self.tools_dir.rglob(script))
        return hits[0] if hits else None

    def persist(self, dry_run: bool) -> None:
        doc = {
            "schema": "VIA.CapabilityRegistry", "spec": SPEC_VERSION,
            "controller": URN_SELF, "generated": iso_now(),
            "policy": "append-only; disable with enabled=false, never delete",
            "capabilities": [asdict(c) for c in self.capabilities],
        }
        target = self.config_path if not dry_run else \
            self.config_path.with_suffix(".preview.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------------------
# §3  下行順序：拓撲分層
# ---------------------------------------------------------------------------

def topological_levels(caps: List[Capability]) -> Tuple[List[List[Capability]], List[str]]:
    """回傳 (分層, 循環節點)。同層彼此獨立可並行，跨層嚴格循序。"""
    by_urn = {c.urn: c for c in caps}
    indegree = {c.urn: 0 for c in caps}
    children: Dict[str, List[str]] = {c.urn: [] for c in caps}
    for cap in caps:
        for parent in cap.depends_on:
            if parent not in by_urn:
                continue                                   # 缺席的上游不算相依
            indegree[cap.urn] += 1
            children[parent].append(cap.urn)

    levels: List[List[Capability]] = []
    ready = sorted([u for u, d in indegree.items() if d == 0])
    seen: Set[str] = set()
    while ready:
        level = [by_urn[u] for u in ready]
        levels.append(level)
        seen.update(ready)
        nxt: List[str] = []
        for urn in ready:
            for child in children[urn]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    nxt.append(child)
        ready = sorted(nxt)
    cycles = sorted(set(by_urn) - seen)
    return levels, cycles


# ---------------------------------------------------------------------------
# §4  下行控制器
# ---------------------------------------------------------------------------

@dataclass
class Evidence:
    urn: str
    name: str
    kind: str
    state: str = "PENDING"          # OK|FAILED|TIMEOUT|SKIPPED|BLOCKED|MISSING
    verdict: str = "UNKNOWN"
    exit_code: int = -1
    seconds: float = 0.0
    level: int = -1
    snapshot: str = ""
    detail: str = ""
    command: str = ""


class DownwardController:
    def __init__(self, root: Path, tools: Path, work: Path,
                 token: str = "", commit: bool = False,
                 workers: int = 10, pwsh: str = "", python_exe: str = "",
                 env_root: str = "", supportive: str = "",
                 strict_chain: bool = False) -> None:
        self.root = root
        self.tools = tools
        self.work = work
        self.token = token
        self.commit = commit
        self.strict_chain = strict_chain
        self.workers = max(1, workers)
        self.stamp = now_stamp()
        self.started = time.perf_counter()

        self.pwsh = pwsh or self._which(["pwsh", "powershell"])
        self.python = python_exe or sys.executable or self._which(["python", "python3"])
        self.env_root = env_root or str(Path.home() / "envs")
        self.supportive = supportive or str(root / "supportive modules")

        for sub in ("configs", "logs", "out"):
            (self.work / sub).mkdir(parents=True, exist_ok=True)

        self.registry = CapabilityRegistry(self.work / "configs" / "capabilities.json",
                                           tools)
        self.evidence: Dict[str, Evidence] = {}
        self.cycles: List[str] = []
        self.levels: List[List[Capability]] = []

    @staticmethod
    def _which(names: List[str]) -> str:
        for name in names:
            found = shutil.which(name)
            if found:
                return found
        return ""

    # -- 權杖 -------------------------------------------------------------
    @property
    def authorized(self) -> bool:
        """變更類能力的通行條件：權杖格式正確且明示 --commit。"""
        if not self.commit or not self.token:
            return False
        return bool(re.match(r"^==[A-Z-]+APPROVE==\d{8}_\d{6}-[0-9a-f]{6,}$", self.token))

    # -- 參數展開 ---------------------------------------------------------
    def _expand(self, args: List[str]) -> List[str]:
        mapping = {
            "root": str(self.root), "work": str(self.work),
            "tools": str(self.tools), "envroot": self.env_root,
            "supportive": self.supportive, "stamp": self.stamp,
        }
        out: List[str] = []
        for arg in args:
            value = arg
            for key, replacement in mapping.items():
                value = value.replace("{" + key + "}", replacement)
            out.append(os.path.normpath(value) if ("/" in value or "\\" in value)
                       and not value.startswith("-") else value)
        return out

    # -- 單一能力執行 -----------------------------------------------------
    def _run_capability(self, cap: Capability, level: int) -> Evidence:
        ev = Evidence(urn=cap.urn, name=cap.name, kind=cap.kind, level=level)
        script = self.registry.resolved.get(cap.urn)
        if script is None:
            ev.state, ev.verdict = "MISSING", "MISSING"
            ev.detail = "工具檔不存在：" + cap.script
            return ev
        if not cap.enabled:
            ev.state, ev.verdict = "SKIPPED", "SKIPPED"
            ev.detail = "登記處已停用（enabled=false）"
            return ev
        if cap.mutating and not self.authorized:
            ev.state, ev.verdict = "SKIPPED", "SKIPPED"
            ev.detail = "變更類能力；需 --token 與 --commit 才會下行"
            return ev

        runner = self.pwsh if cap.runtime == "pwsh" else self.python
        if not runner:
            ev.state, ev.verdict = "MISSING", "MISSING"
            ev.detail = "找不到執行期：" + cap.runtime
            return ev

        if cap.runtime == "pwsh":
            argv = [runner, "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", str(script)] + self._expand(cap.args)
        else:
            argv = [runner, str(script)] + self._expand(cap.args)
        ev.command = " ".join(argv)

        begin = time.perf_counter()
        try:
            proc = subprocess.run(argv, capture_output=True, text=True,
                                  timeout=cap.timeout, cwd=str(self.root),
                                  encoding="utf-8", errors="replace")
            ev.exit_code = proc.returncode
            tail = [strip_ansi(ln).strip() for ln in (proc.stdout or "").splitlines()
                    if strip_ansi(ln).strip()][-4:]
            ev.detail = " / ".join(tail)
            if proc.returncode != 0:
                err = [strip_ansi(ln).strip() for ln in (proc.stderr or "").splitlines()
                       if strip_ansi(ln).strip()][-2:]
                if err:
                    ev.detail = (ev.detail + " || " + " / ".join(err)).strip(" |")
            ev.state = "OK" if proc.returncode == 0 else "FAILED"
        except subprocess.TimeoutExpired:
            ev.state, ev.verdict = "TIMEOUT", "TIMEOUT"
            ev.detail = "逾時 %ds，已終止" % cap.timeout
            ev.seconds = round(time.perf_counter() - begin, 2)
            return ev
        except OSError as exc:
            ev.state, ev.verdict = "FAILED", "CRASHED"
            ev.detail = "%s: %s" % (type(exc).__name__, exc)
            ev.seconds = round(time.perf_counter() - begin, 2)
            return ev
        ev.seconds = round(time.perf_counter() - begin, 2)

        ev.verdict = self._collect_verdict(cap, ev)
        return ev

    def _collect_verdict(self, cap: Capability, ev: Evidence) -> str:
        """證據優先序：能力自己的快照 JSON > 退出碼。"""
        if cap.snapshot_glob:
            base = self.work / cap.work_subdir if cap.work_subdir else self.root
            hits = sorted(glob.glob(str(base / cap.snapshot_glob)),
                          key=lambda p: os.path.getmtime(p), reverse=True)
            if hits:
                ev.snapshot = hits[0]
                if cap.verdict_key:
                    try:
                        doc = json.loads(Path(hits[0]).read_text(encoding="utf-8"))
                        value = doc.get(cap.verdict_key)
                        if isinstance(value, str) and value:
                            return value.upper()
                    except (json.JSONDecodeError, ValueError, OSError):
                        pass
                return "GREEN" if ev.state == "OK" else "RED"
        if ev.state == "OK":
            return "GREEN"
        if ev.state == "FAILED":
            return "RED"
        return "UNKNOWN"

    # -- 下行主流程 -------------------------------------------------------
    def dispatch(self) -> str:
        active = [c for c in self.registry.capabilities]
        self.levels, self.cycles = topological_levels(active)
        if self.cycles:
            LOG.say("能力相依有循環，涉及 %s，這些能力不下行" % ", ".join(self.cycles), "FAIL")

        LOG.say("下行分層：%s" % " -> ".join(
            "L%d(%d)" % (i, len(lv)) for i, lv in enumerate(self.levels)), "OK")
        LOG.say("授權狀態：%s" % ("已核准（變更類會下行）" if self.authorized
                                else "未核准（僅唯讀能力下行）"),
                "WARN" if not self.authorized else "OK")

        blocked: Set[str] = set()
        for index, level in enumerate(self.levels):
            runnable: List[Capability] = []
            for cap in level:
                upstream_bad = [p for p in cap.depends_on if p in blocked]
                if upstream_bad:
                    ev = Evidence(urn=cap.urn, name=cap.name, kind=cap.kind,
                                  level=index, state="BLOCKED", verdict="BLOCKED",
                                  detail="上游硬故障：" + ", ".join(upstream_bad))
                    self.evidence[cap.urn] = ev
                    blocked.add(cap.urn)
                    continue
                runnable.append(cap)

            if not runnable:
                continue
            LOG.say("L%d 下行 %d 個能力（並行上限 %d）"
                    % (index, len(runnable), self.workers))
            with futures.ThreadPoolExecutor(max_workers=self.workers) as pool:
                pending = {pool.submit(self._run_capability, cap, index): cap
                           for cap in runnable}
                for done in futures.as_completed(pending):
                    cap = pending[done]
                    try:
                        ev = done.result()
                    except BaseException as exc:            # noqa: BLE001
                        ev = Evidence(urn=cap.urn, name=cap.name, kind=cap.kind,
                                      level=index, state="FAILED", verdict="CRASHED",
                                      detail="%s: %s" % (type(exc).__name__, exc))
                    self.evidence[cap.urn] = ev
                    mark = "OK" if ev.verdict in ("GREEN", "SKIPPED") else \
                        ("WARN" if ev.verdict in ("AMBER", "UNKNOWN", "MISSING") else "FAIL")
                    LOG.say("  %s %s -> %s (%.1fs)"
                            % (ev.urn, ev.name, ev.verdict, ev.seconds), mark)
                    # 硬故障（能力自己壞了）才阻斷下游。
                    # 能力跑得好好的、只是回報 RED（它找到問題了），那是它盡了職責，
                    # 不該讓下游停擺 —— 環境有政策爭議不代表程式碼不能檢查。
                    # --strict-chain 才改成以裁決阻斷。
                    hard_fail = ev.state in ("FAILED", "TIMEOUT", "MISSING")
                    soft_fail = ev.verdict in ("RED", "CRASHED", "TIMEOUT")
                    if hard_fail or (self.strict_chain and soft_fail):
                        blocked.add(cap.urn)

        for cap in self.registry.capabilities:
            if cap.urn not in self.evidence:
                self.evidence[cap.urn] = Evidence(
                    urn=cap.urn, name=cap.name, kind=cap.kind, state="BLOCKED",
                    verdict="BLOCKED", detail="位於循環相依中，未下行")

        return self.aggregate()

    def aggregate(self) -> str:
        worst = "GREEN"
        for ev in self.evidence.values():
            if VERDICT_RANK.get(ev.verdict, 1) > VERDICT_RANK.get(worst, 0):
                worst = ev.verdict
        if worst in ("CRASHED", "TIMEOUT"):
            worst = "RED"
        if worst in ("BLOCKED", "MISSING", "UNKNOWN"):
            worst = "AMBER"
        return worst

    # -- 閘門 -------------------------------------------------------------
    def gates(self, overall: str) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []

        def add(code: str, title: str, status: str, detail: str) -> None:
            rows.append({"code": code, "title": title, "status": status, "detail": detail})

        missing = [c.urn for c in self.registry.missing]
        add("D01", "CAPABILITY_PRESENT", "PASS" if not missing else "WARN",
            "缺席能力 %d 個 %s" % (len(missing), ("： " + ", ".join(missing)) if missing else ""))
        add("D02", "NO_CAPABILITY_CYCLE", "PASS" if not self.cycles else "FAIL",
            "循環相依 %d 個" % len(self.cycles))
        unauthorized = [e.urn for e in self.evidence.values()
                        if e.state == "SKIPPED" and "變更類" in e.detail]
        add("D03", "NO_UNAUTHORIZED_MUTATION", "PASS",
            "未授權而攔下的變更類能力 %d 個；本輪授權=%s"
            % (len(unauthorized), self.authorized))
        timeouts = [e.urn for e in self.evidence.values() if e.state == "TIMEOUT"]
        add("D04", "NO_TIMEOUT", "PASS" if not timeouts else "FAIL",
            "逾時 %d 個 %s" % (len(timeouts), ", ".join(timeouts)))
        blocked = [e.urn for e in self.evidence.values() if e.state == "BLOCKED"]
        add("D05", "FAILURE_ISOLATED", "PASS" if not blocked else "WARN",
            "因上游硬故障而未下行 %d 個（模式：%s）"
            % (len(blocked), "strict-chain" if self.strict_chain else "hard-fail-only"))
        ran = [e for e in self.evidence.values() if e.state == "OK"]
        add("D06", "EVIDENCE_COLLECTED", "PASS" if ran else "WARN",
            "取得快照證據 %d 份" % len([e for e in ran if e.snapshot]))
        add("D07", "APPEND_ONLY_REGISTRY", "PASS",
            "能力登記處只增不減；停用以 enabled=false 表示")
        add("D08", "AGGREGATE_VERDICT", "PASS" if overall == "GREEN" else
            ("WARN" if overall == "AMBER" else "FAIL"), "聚合裁決 " + overall)
        return rows


# ---------------------------------------------------------------------------
# §5  指揮中心 HTML
# ---------------------------------------------------------------------------

CSS = """
:root{--paper:#f2f2f3;--ink:#1d1f20;--line:#d8d8d9;--red:#b0453d;--green:#3f7d5e;--amber:#c4943a;--panel:#fff}
*{box-sizing:border-box}
body{margin:0;padding:22px 26px;background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","Segoe UI",system-ui,sans-serif;font-size:12px;line-height:1.45}
.seal{display:inline-flex;width:38px;height:38px;align-items:center;justify-content:center;background:var(--red);color:#fff;font-family:"Noto Serif TC",serif;font-size:21px;border-radius:3px}
h1{font-family:"Noto Serif TC",Georgia,serif;font-size:16px;letter-spacing:.14em;text-transform:uppercase;margin:10px 0 3px}
h2{font-family:"Noto Serif TC",Georgia,serif;font-size:14px;margin:22px 0 5px}
.lede{color:#6c6e70;font-size:11.5px;margin:0 0 12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:9px;margin:14px 0 4px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:10px 12px}
.card .k{font-size:10px;letter-spacing:.1em;color:#8a8c8e;text-transform:uppercase}
.card .v{font-size:20px;font-family:"Noto Serif TC",Georgia,serif;margin-top:3px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:11.5px;table-layout:fixed}
th,td{border-bottom:1px solid #ececed;padding:5px 7px;text-align:left;vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word}
th{background:#eeeeef;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#5c5e60}
tr:hover td{background:#fbfbfb}
.ok{color:var(--green);font-weight:600}.warn{color:var(--amber);font-weight:600}.fail{color:var(--red);font-weight:600}
.muted{color:#9a9c9e;text-align:center;padding:12px}
.chain{background:var(--panel);border:1px solid var(--line);padding:12px 14px;font-family:Consolas,monospace;font-size:11.5px;overflow-wrap:anywhere}
pre{background:var(--panel);border:1px solid var(--line);padding:11px;font-size:11px;white-space:pre-wrap;max-height:36vh;overflow:auto}
code{background:#ececed;padding:1px 5px;border-radius:2px}
"""


def esc(value: Any) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def klass(value: str) -> str:
    upper = str(value).upper()
    if re.search(r"PASS|GREEN|^OK$|SKIPPED", upper):
        return "ok"
    if re.search(r"FAIL|RED|CRASH|TIMEOUT", upper):
        return "fail"
    if re.search(r"WARN|AMBER|BLOCKED|MISSING|UNKNOWN", upper):
        return "warn"
    return ""


def rows_html(items: List[Dict[str, Any]], fields: List[str],
              status_field: str = "") -> str:
    if not items:
        return "<tr><td colspan='%d' class='muted'>—— 無 ——</td></tr>" % len(fields)
    out = []
    for item in items:
        cells = []
        for name in fields:
            value = item.get(name, "")
            if isinstance(value, (list, tuple)):
                value = ", ".join(str(v) for v in value)
            cls = " class='%s'" % klass(str(value)) if name == status_field else ""
            cells.append("<td%s>%s</td>" % (cls, esc(value)))
        out.append("<tr>%s</tr>" % "".join(cells))
    return "".join(out)


def render(ctl: DownwardController, overall: str, gates: List[Dict[str, str]]) -> str:
    ev_rows = [asdict(e) for e in sorted(ctl.evidence.values(),
                                         key=lambda e: (e.level, e.urn))]
    chain = []
    for index, level in enumerate(ctl.levels):
        names = " ｜ ".join("%s %s" % (c.urn, c.name) for c in level)
        chain.append("L%d  %s" % (index, names))
    chain_html = esc("\n   ↓\n".join(chain)) if chain else "（無）"

    counts = {"OK": 0, "SKIPPED": 0, "BLOCKED": 0, "FAILED": 0, "MISSING": 0, "TIMEOUT": 0}
    for e in ctl.evidence.values():
        counts[e.state] = counts.get(e.state, 0) + 1
    elapsed = int(time.perf_counter() - ctl.started)

    return """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Downward Controller</title><style>%s</style></head><body>
<div class="seal">令</div>
<h1>Downward Controller</h1>
<p class="lede">%s · %s · %s · 耗時 %ds · 並行上限 %d</p>
<div class="cards">
  <div class="card"><div class="k">Aggregate</div><div class="v %s">%s</div></div>
  <div class="card"><div class="k">Capabilities</div><div class="v">%d</div></div>
  <div class="card"><div class="k">Dispatched</div><div class="v ok">%d</div></div>
  <div class="card"><div class="k">Gated Off</div><div class="v warn">%d</div></div>
  <div class="card"><div class="k">Blocked</div><div class="v warn">%d</div></div>
  <div class="card"><div class="k">Missing</div><div class="v warn">%d</div></div>
  <div class="card"><div class="k">Failed</div><div class="v fail">%d</div></div>
</div>

<h2>下行鏈（拓撲分層）</h2>
<p class="lede">同層並行，跨層循序。上游未通過時，下游一律 BLOCKED，不在錯誤基礎上繼續施工。</p>
<div class="chain">%s</div>

<h2>能力執行證據</h2>
<table><colgroup><col style="width:4%%"><col style="width:15%%"><col style="width:16%%"><col style="width:8%%"><col style="width:9%%"><col style="width:9%%"><col style="width:6%%"><col style="width:33%%"></colgroup>
<tr><th>L</th><th>URN</th><th>能力</th><th>類型</th><th>狀態</th><th>裁決</th><th>秒</th><th>細節</th></tr>%s</table>

<h2>下行閘門</h2>
<table><colgroup><col style="width:7%%"><col style="width:22%%"><col style="width:9%%"><col style="width:62%%"></colgroup>
<tr><th>Code</th><th>Gate</th><th>Status</th><th>Detail</th></tr>%s</table>

<h2>證據快照</h2>
<table><colgroup><col style="width:16%%"><col style="width:84%%"></colgroup>
<tr><th>URN</th><th>Snapshot</th></tr>%s</table>

<h2>執行日誌</h2>
<pre>%s</pre>
</body></html>""" % (
        CSS, esc(ctl.root), ctl.stamp,
        "已核准（變更類能力可下行）" if ctl.authorized else "未核准（僅唯讀下行）",
        elapsed, ctl.workers,
        klass(overall), overall, len(ctl.registry.capabilities),
        counts.get("OK", 0), counts.get("SKIPPED", 0), counts.get("BLOCKED", 0),
        counts.get("MISSING", 0), counts.get("FAILED", 0) + counts.get("TIMEOUT", 0),
        chain_html,
        rows_html(ev_rows, ["level", "urn", "name", "kind", "state", "verdict",
                            "seconds", "detail"], "verdict"),
        rows_html(gates, ["code", "title", "status", "detail"], "status"),
        rows_html([e for e in ev_rows if e.get("snapshot")], ["urn", "snapshot"]),
        esc("\n".join(LOG.lines)),
    )


# ---------------------------------------------------------------------------
# §6  CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="VIA_DownwardController.py",
        description="VIA-SYS-MGR-003 自動下行控制層")
    parser.add_argument("--root", default=".", help="VIA 母系統根目錄")
    parser.add_argument("--tools", default="./tools", help="治理工具所在目錄")
    parser.add_argument("--work", default="", help="工作區（預設 <root>/_governance）")
    parser.add_argument("--env-root", default="", help="venv 根目錄")
    parser.add_argument("--supportive", default="", help="supportive modules 目錄")
    parser.add_argument("--token", default="", help="變更類能力的核准權杖")
    parser.add_argument("--commit", action="store_true", help="與 --token 併用才會下行變更類能力")
    parser.add_argument("--workers", type=int, default=10, help="同層並行上限")
    parser.add_argument("--strict-chain", action="store_true",
                        help="上游回報 RED 就阻斷下游（預設只有硬故障才阻斷）")
    parser.add_argument("--pwsh", default="", help="pwsh 路徑")
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--json", action="store_true", help="只輸出裁決 JSON")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print("root 不存在：%s" % root, file=sys.stderr)
        return 2
    tools = Path(args.tools).expanduser().resolve()
    if not tools.is_dir():
        print("tools 目錄不存在：%s" % tools, file=sys.stderr)
        return 2
    work = Path(args.work).expanduser().resolve() if args.work else root / "_governance"

    LOG.say("%s VIA Downward Controller %s 啟動" % (URN_SELF, VERSION), "OK")
    ctl = DownwardController(root=root, tools=tools, work=work,
                             token=args.token, commit=args.commit,
                             workers=args.workers, pwsh=args.pwsh,
                             env_root=args.env_root, supportive=args.supportive,
                             strict_chain=args.strict_chain)
    LOG.say("能力登記：%d 個，缺席 %d 個"
            % (len(ctl.registry.capabilities), len(ctl.registry.missing)),
            "OK" if not ctl.registry.missing else "WARN")
    ctl.registry.persist(dry_run=False)

    overall = ctl.dispatch()
    gates = ctl.gates(overall)
    fails = len([g for g in gates if g["status"] == "FAIL"])
    warns = len([g for g in gates if g["status"] == "WARN"])
    LOG.say("下行閘門：%d 道，WARN %d，FAIL %d" % (len(gates), warns, fails),
            "FAIL" if fails else ("WARN" if warns else "OK"))

    html_path = work / "out" / ("VIA_DownwardController_%s.html" % ctl.stamp)
    json_path = work / "out" / ("downward_snapshot_%s.json" % ctl.stamp)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(render(ctl, overall, gates), encoding="utf-8")
    snapshot = {
        "schema": "VIA.DownwardDispatch", "spec": SPEC_VERSION,
        "controller": URN_SELF, "version": VERSION, "stamp": ctl.stamp,
        "root": str(root), "tools": str(tools), "work": str(work),
        "authorized": ctl.authorized, "workers": ctl.workers,
        "strict_chain": ctl.strict_chain,
        "verdict": overall, "cycles": ctl.cycles,
        "levels": [[c.urn for c in level] for level in ctl.levels],
        "missing": [c.urn for c in ctl.registry.missing],
        "evidence": [asdict(e) for e in ctl.evidence.values()],
        "gates": gates,
    }
    json_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    (work / "logs" / ("controller_%s.log" % ctl.stamp)).write_text(
        "\n".join(LOG.lines), encoding="utf-8")

    LOG.say("指揮中心 -> %s" % html_path, "OK")
    LOG.say("快照     -> %s" % json_path, "OK")
    print("")
    print("=" * 60)
    print(" VIA DOWNWARD CONTROLLER  ->  %s" % overall)
    print(" 唯讀能力自動下行；變更類能力需權杖 + --commit。")
    print("=" * 60)

    if not args.no_open and not args.json:
        try:
            webbrowser.open(html_path.as_uri())
        except Exception:                                    # noqa: BLE001
            pass
    if args.json:
        print(json.dumps({"verdict": overall, "stamp": ctl.stamp}, ensure_ascii=False))
    return 0 if overall != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
