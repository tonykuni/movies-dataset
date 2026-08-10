# -*- coding: utf-8 -*-
"""
VIA_WorkflowEngine.py — 統一工作流引擎（Unified Workflow Engine, all-paradigm integration）
==========================================================================================
單檔、零強制依賴（stdlib-only core；PyYAML 在位時自動啟用 YAML DSL）。
整合 2026 Top 10 Python 本地免費工作流程式庫的「典範 + 轉接器」：

  ┌────────────────────────┬──────────────────────────────┬─────────────────────────┐
  │ 典範 Paradigm          │ 對應程式庫 Library            │ 本檔對應 API             │
  ├────────────────────────┼──────────────────────────────┼─────────────────────────┤
  │ DAG + Decorator flows  │ Prefect / Apache Airflow     │ @via_task @via_flow,    │
  │                        │                              │ WorkflowSpec+DAG engine │
  │ 宣告式 YAML/JSON DSL   │ Kestra / Dagu / Conductor    │ load_workflow_file(),   │
  │                        │                              │ Exporters.to_*          │
  │ BPMN 2.0               │ SpiffWorkflow / bpmn-js      │ Exporters.to_bpmn_xml   │
  │ 有限狀態機 FSM         │ Transitions                  │ StateMachine            │
  │ 循環圖 AI Agent flows  │ LangGraph                    │ StateGraph + END        │
  │ 多智能體協作           │ CrewAI                       │ Agent / CrewTask / Crew │
  │ 事件驅動               │ LlamaIndex Workflows         │ Event / @step /         │
  │                        │                              │ EventWorkflow           │
  │ 耐用執行 Durable exec  │ Temporal Python SDK          │ RunStore checkpoints +  │
  │                        │                              │ resume(), saga 補償     │
  │ 排程 Scheduling        │ Airflow/Dagu cron            │ Cron + Scheduler        │
  │ 前端視覺化             │ React Flow / AntV X6 /       │ Exporters.to_reactflow, │
  │                        │ mermaid / n8n                │ to_x6, to_mermaid,      │
  │                        │                              │ to_n8n_json             │
  │ 網頁審批流程           │ Viewflow (Django)            │ Exporters.to_viewflow_py│
  └────────────────────────┴──────────────────────────────┴─────────────────────────┘

治理原則（承襲 VIA 家規）：
  - 依賴缺席 = 誠實回報 + 自動回退本地原生引擎（never fake success）
  - 外部伺服器型引擎（Airflow/Kestra/Temporal/n8n/Activepieces）= 產生其官方定義檔
    （codegen/export）+ docker-compose scaffold；不假裝已連線
  - 所有執行紀錄落 .via_runs/（可再生側車，checkpoint JSON，斷點續跑）

動詞（CLI）：
  backends   十庫在位探測報告（installed / fallback）
  demo       執行各典範示範（all | dag | saga | resume | fsm | graph | events |
             crew | decorators | cron | dsl | export）
  run        執行 YAML/JSON 工作流檔（--backend auto|native|prefect|...）
  export     將工作流檔轉出（--format dagu|kestra|argo|conductor|airflow|temporal|
             bpmn|reactflow|x6|n8n|mermaid|viewflow）
  scaffold   產生本地部署檔（docker-compose：activepieces|n8n|temporal|kestra）
  selftest   全功能自我驗證（PASS/FAIL 摘要，exit code）

USAGE
-----
  python VIA_WorkflowEngine.py backends
  python VIA_WorkflowEngine.py demo all
  python VIA_WorkflowEngine.py run my_flow.yaml --param key=value
  python VIA_WorkflowEngine.py export my_flow.yaml --format argo -o my_flow_argo.yaml
  python VIA_WorkflowEngine.py scaffold activepieces -o ./deploy
  python VIA_WorkflowEngine.py selftest

  # 程式內嵌（embedded, Prefect 風格）：
      from VIA_WorkflowEngine import via_task, via_flow
      @via_task(retries=3, retry_delay=2)
      def extract(): return [1, 2, 3]
      @via_flow(name="etl")
      def etl(): return [x * 10 for x in extract()]
      etl()
"""
from __future__ import annotations

__version__ = "1.0.0"
__all__ = [
    "TaskSpec", "TaskResult", "WorkflowSpec", "WorkflowContext", "WorkflowRun",
    "LocalDAGEngine", "RunStore", "StateMachine", "StateGraph", "END",
    "Event", "StartEvent", "StopEvent", "step", "EventWorkflow",
    "Agent", "CrewTask", "Crew", "via_task", "via_flow",
    "Cron", "Scheduler", "Exporters", "load_workflow_file",
    "BackendAdapter", "ADAPTERS", "VIAWorkflowEngine",
]

import argparse
import concurrent.futures
import importlib
import importlib.util
import json
import logging
import os
import re
import sys
import threading
import time
import traceback
import uuid
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Type, Union

try:  # optional — YAML DSL 啟用鍵（PyYAML 在位即用；缺席時 JSON DSL 仍全功能）
    import yaml as _yaml
except Exception:  # pragma: no cover
    _yaml = None

LOG = logging.getLogger("VIA.WorkflowEngine")
if not LOG.handlers:
    _h = logging.StreamHandler(sys.stderr)  # 日誌走 stderr — stdout 留給資料（可管線）
    _h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%H:%M:%S"))
    LOG.addHandler(_h)
    LOG.setLevel(logging.INFO)

# 十庫目錄（在位探測用）— top 10 python local free workflow libs
LIB_CATALOG: "OrderedDict[str, Dict[str, str]]" = OrderedDict([
    ("prefect",     {"package": "prefect",      "paradigm": "code-as-workflow decorators", "tier": "Data Pipelines"}),
    ("airflow",     {"package": "airflow",      "paradigm": "python DAG + cron scheduler", "tier": "Data Pipelines"}),
    ("kestra",      {"package": "kestra",       "paradigm": "declarative YAML orchestration", "tier": "Data Pipelines"}),
    ("spiff",       {"package": "SpiffWorkflow", "paradigm": "BPMN 2.0 in-memory engine",  "tier": "Lightweight"}),
    ("transitions", {"package": "transitions",  "paradigm": "finite state machine",        "tier": "Lightweight"}),
    ("viewflow",    {"package": "viewflow",     "paradigm": "django business workflow",    "tier": "Lightweight"}),
    ("langgraph",   {"package": "langgraph",    "paradigm": "cyclic agent state graph",    "tier": "AI Agent"}),
    ("crewai",      {"package": "crewai",       "paradigm": "role-playing multi-agent",    "tier": "AI Agent"}),
    ("llamaindex",  {"package": "llama_index",  "paradigm": "event-driven AI workflow",    "tier": "AI Agent"}),
    ("temporal",    {"package": "temporalio",   "paradigm": "durable execution",           "tier": "Durable"}),
])

# 任務狀態常量
PENDING, RUNNING, SUCCESS, FAILED, SKIPPED, COMPENSATED, CANCELLED = (
    "PENDING", "RUNNING", "SUCCESS", "FAILED", "SKIPPED", "COMPENSATED", "CANCELLED")

_DEF_RUN_DIR = Path(os.environ.get("VIA_WFE_RUN_DIR", ".via_runs"))


def _utcnow() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _new_run_id(prefix: str = "run") -> str:
    return "%s_%s_%s" % (prefix, datetime.utcnow().strftime("%Y%m%d%H%M%S"), uuid.uuid4().hex[:8])


# ============================================================================
# §1 核心原語（primitives）— TaskSpec / TaskResult / WorkflowSpec / Context
# ============================================================================

@dataclass
class TaskResult:
    """單一任務的執行結果（可序列化，供 checkpoint / resume 用）。"""
    name: str
    status: str = PENDING
    output: Any = None
    error: Optional[str] = None
    attempts: int = 0
    started: Optional[str] = None
    ended: Optional[str] = None

    @property
    def duration_ms(self) -> Optional[float]:
        if not (self.started and self.ended):
            return None
        f = "%Y-%m-%dT%H:%M:%S.%fZ"
        return (datetime.strptime(self.ended, f) - datetime.strptime(self.started, f)).total_seconds() * 1000

    def to_dict(self) -> Dict[str, Any]:
        out = dict(name=self.name, status=self.status, error=self.error,
                   attempts=self.attempts, started=self.started, ended=self.ended)
        try:  # output 僅在可 JSON 序列化時入 checkpoint（誠實降級為 repr）
            json.dumps(self.output)
            out["output"] = self.output
        except (TypeError, ValueError):
            out["output"] = repr(self.output)
        return out

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TaskResult":
        return cls(name=d["name"], status=d.get("status", PENDING), output=d.get("output"),
                   error=d.get("error"), attempts=d.get("attempts", 0),
                   started=d.get("started"), ended=d.get("ended"))


@dataclass
class TaskSpec:
    """任務規格：fn（Python callable）或 command（shell），二擇一。

    fn 簽名：fn(ctx) / fn() 皆可（引擎自動偵測 arity）。
    condition：callable(ctx)->bool 或安全表達式字串（可用 params/outputs）。
    compensate：saga 補償 callable(ctx)，主流程失敗時反序執行。
    """
    name: str
    fn: Optional[Callable] = None
    command: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    retries: int = 0
    retry_delay: float = 1.0
    backoff: float = 2.0
    timeout: Optional[float] = None
    condition: Optional[Union[Callable, str]] = None
    compensate: Optional[Callable] = None
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def validate(self) -> None:
        if not self.name:
            raise ValueError("TaskSpec 需要 name")
        if self.fn is None and self.command is None:
            raise ValueError("Task %r 需要 fn 或 command 其一" % self.name)
        if self.fn is not None and self.command is not None:
            raise ValueError("Task %r 的 fn 與 command 互斥" % self.name)


class WorkflowContext:
    """跨任務共享上下文：params（唯讀輸入）、results、state（執行緒安全 KV）。"""

    def __init__(self, workflow: "WorkflowSpec", params: Dict[str, Any], run_id: str):
        self.workflow = workflow
        self.params = dict(params)
        self.run_id = run_id
        self.results: Dict[str, TaskResult] = {}
        self._state: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self.log = LOG

    def output_of(self, task_name: str) -> Any:
        r = self.results.get(task_name)
        return r.output if r else None

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._state.get(key, default)

    def state_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)


class WorkflowSpec:
    """工作流規格（DAG）。Fluent API（Workflow Core 風格）+ dict/DSL 雙向轉換。"""

    def __init__(self, name: str, description: str = "", schedule: Optional[str] = None,
                 max_parallel: int = 4, on_failure: str = "halt"):
        if on_failure not in ("halt", "continue", "compensate"):
            raise ValueError("on_failure 需為 halt|continue|compensate")
        self.name = name
        self.description = description
        self.schedule = schedule  # cron 表達式（5 欄）
        self.max_parallel = max(1, int(max_parallel))
        self.on_failure = on_failure
        self.tasks: "OrderedDict[str, TaskSpec]" = OrderedDict()

    # -- Fluent builder（start_with / then / task）--------------------------
    def task(self, name: str, fn: Optional[Callable] = None, **kw) -> "WorkflowSpec":
        spec = TaskSpec(name=name, fn=fn, **kw)
        spec.validate()
        if name in self.tasks:
            raise ValueError("重複任務名：%r" % name)
        for dep in spec.depends_on:
            if dep not in self.tasks:
                raise ValueError("Task %r 依賴未定義任務 %r（請先定義依賴）" % (name, dep))
        self.tasks[name] = spec
        return self

    def start_with(self, name: str, fn: Optional[Callable] = None, **kw) -> "WorkflowSpec":
        return self.task(name, fn, **kw)

    def then(self, name: str, fn: Optional[Callable] = None, **kw) -> "WorkflowSpec":
        if self.tasks:
            kw.setdefault("depends_on", [next(reversed(self.tasks))])
        return self.task(name, fn, **kw)

    # -- 圖形驗證 ------------------------------------------------------------
    def topological_order(self) -> List[str]:
        """Kahn 拓撲排序；偵測環（DAG 引擎不允許環 — 環請用 StateGraph）。"""
        indeg = {n: 0 for n in self.tasks}
        children: Dict[str, List[str]] = {n: [] for n in self.tasks}
        for n, t in self.tasks.items():
            for dep in t.depends_on:
                if dep not in self.tasks:
                    raise ValueError("Task %r 依賴未知任務 %r" % (n, dep))
                indeg[n] += 1
                children[dep].append(n)
        q = deque([n for n, d in indeg.items() if d == 0])
        order: List[str] = []
        while q:
            n = q.popleft()
            order.append(n)
            for c in children[n]:
                indeg[c] -= 1
                if indeg[c] == 0:
                    q.append(c)
        if len(order) != len(self.tasks):
            cyc = sorted(set(self.tasks) - set(order))
            raise ValueError("偵測到環（cycle）：%s — DAG 不允許；循環流程請改用 StateGraph" % cyc)
        return order

    def validate(self) -> None:
        for t in self.tasks.values():
            t.validate()
        self.topological_order()

    # -- 序列化（供 checkpoint / exporters 用）------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "description": self.description, "schedule": self.schedule,
            "max_parallel": self.max_parallel, "on_failure": self.on_failure,
            "tasks": [{
                "name": t.name, "command": t.command,
                "fn": ("%s.%s" % (t.fn.__module__, t.fn.__qualname__)) if t.fn else None,
                "depends_on": list(t.depends_on), "retries": t.retries,
                "retry_delay": t.retry_delay, "backoff": t.backoff, "timeout": t.timeout,
                "condition": t.condition if isinstance(t.condition, str) else None,
                "params": t.params, "description": t.description,
            } for t in self.tasks.values()],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any], fn_registry: Optional[Dict[str, Callable]] = None) -> "WorkflowSpec":
        wf = cls(name=d.get("name", "unnamed"), description=d.get("description", ""),
                 schedule=d.get("schedule"), max_parallel=d.get("max_parallel", 4),
                 on_failure=d.get("on_failure", "halt"))
        for td in d.get("tasks", d.get("steps", [])):
            fn = None
            ref = td.get("fn") or td.get("python")
            if ref:
                fn = _resolve_callable(ref, fn_registry)
            retry = td.get("retry") or {}
            wf.task(td["name"], fn=fn, command=td.get("command"),
                    depends_on=list(td.get("depends_on", td.get("depends", []))),
                    retries=int(td.get("retries", retry.get("limit", 0))),
                    retry_delay=float(td.get("retry_delay", retry.get("interval", 1.0))),
                    backoff=float(td.get("backoff", 2.0)),
                    timeout=td.get("timeout"),
                    condition=td.get("condition"),
                    params=dict(td.get("params", {})),
                    description=td.get("description", ""))
        wf.validate()
        return wf


def _resolve_callable(ref: str, registry: Optional[Dict[str, Callable]] = None) -> Callable:
    """把 'module.sub:fn' / 'module.fn' / registry 名解析為 callable（誠實 FAIL）。"""
    if registry and ref in registry:
        return registry[ref]
    modname, _, attr = ref.replace(":", ".").rpartition(".")
    if not modname:
        raise ValueError("無法解析 callable %r（不在 registry，且非 module.fn 格式）" % ref)
    mod = importlib.import_module(modname)
    fn = getattr(mod, attr, None)
    if not callable(fn):
        raise ValueError("解析 %r 得到非 callable：%r" % (ref, fn))
    return fn


def _call_task_fn(fn: Callable, ctx: WorkflowContext) -> Any:
    """fn(ctx) / fn() 雙簽名支援（引擎自動偵測 arity）。"""
    try:
        import inspect
        sig = inspect.signature(fn)
        n_req = sum(1 for p in sig.parameters.values()
                    if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) and p.default is p.empty)
    except (TypeError, ValueError):
        n_req = 1
    return fn(ctx) if n_req >= 1 else fn()


def _eval_condition(cond: Union[Callable, str, None], ctx: WorkflowContext) -> bool:
    if cond is None:
        return True
    if callable(cond):
        return bool(cond(ctx))
    # 字串表達式：受限命名空間（無 builtins）— params/outputs/state 可用
    ns = {"params": ctx.params, "state": ctx.state_snapshot(),
          "outputs": {k: v.output for k, v in ctx.results.items()},
          "True": True, "False": False, "None": None, "len": len}
    return bool(eval(cond, {"__builtins__": {}}, ns))  # noqa: S307 — 受限空間

# ============================================================================
# §2 耐用執行（Durable Execution, Temporal 風格）— RunStore checkpoint / resume
# ============================================================================

class RunStore:
    """檔案型 checkpoint 存放（.via_runs/<run_id>.json）。

    每完成一個任務即落盤 → 行程中斷（斷電/當機）後 resume(run_id) 從斷點續跑，
    已 SUCCESS 任務不重跑（Temporal 風格 replay-free durability 的本地簡化版）。
    """

    def __init__(self, root: Union[str, Path] = _DEF_RUN_DIR):
        self.root = Path(root)

    def _path(self, run_id: str) -> Path:
        return self.root / ("%s.json" % run_id)

    def save(self, run: "WorkflowRun") -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self._path(run.run_id).with_suffix(".tmp")
        tmp.write_text(json.dumps(run.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self._path(run.run_id))  # 原子替換 — checkpoint 永不半寫

    def load(self, run_id: str) -> Dict[str, Any]:
        p = self._path(run_id)
        if not p.exists():
            raise FileNotFoundError("找不到 run checkpoint：%s" % p)
        return json.loads(p.read_text(encoding="utf-8"))

    def list_runs(self) -> List[Dict[str, Any]]:
        if not self.root.exists():
            return []
        out = []
        for p in sorted(self.root.glob("*.json")):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                out.append({"run_id": d.get("run_id"), "workflow": d.get("workflow"),
                            "status": d.get("status"), "started": d.get("started"),
                            "ended": d.get("ended")})
            except Exception as e:  # 壞檔誠實列出
                out.append({"run_id": p.stem, "status": "CORRUPT", "error": str(e)})
        return out


class WorkflowRun:
    """一次執行的全紀錄（狀態 + 各任務結果 + 共享 state），可序列化。"""

    def __init__(self, workflow: str, run_id: str, params: Dict[str, Any]):
        self.workflow = workflow
        self.run_id = run_id
        self.params = params
        self.status = RUNNING
        self.started = _utcnow()
        self.ended: Optional[str] = None
        self.results: Dict[str, TaskResult] = {}
        self.state: Dict[str, Any] = {}
        self.events: List[Dict[str, str]] = []

    def event(self, kind: str, detail: str) -> None:
        self.events.append({"ts": _utcnow(), "kind": kind, "detail": detail})

    def to_dict(self) -> Dict[str, Any]:
        try:
            json.dumps(self.state)
            state = self.state
        except (TypeError, ValueError):
            state = {k: repr(v) for k, v in self.state.items()}
        return {"workflow": self.workflow, "run_id": self.run_id, "params": self.params,
                "status": self.status, "started": self.started, "ended": self.ended,
                "results": [r.to_dict() for r in self.results.values()],
                "state": state, "events": self.events}

    @property
    def ok(self) -> bool:
        return self.status == SUCCESS

    def summary(self) -> str:
        counts: Dict[str, int] = {}
        for r in self.results.values():
            counts[r.status] = counts.get(r.status, 0) + 1
        parts = ", ".join("%s=%d" % kv for kv in sorted(counts.items()))
        return "[%s] %s run_id=%s (%s)" % (self.status, self.workflow, self.run_id, parts)

# ============================================================================
# §3 本地原生 DAG 引擎（Airflow/Prefect/Workflow Core 典範：平行、重試、逾時、
#     條件分支、saga 補償、checkpoint 斷點續跑）
# ============================================================================

class LocalDAGEngine:
    """零依賴 DAG 執行引擎。

    全功能：拓撲平行執行（ThreadPool, max_parallel）、指數退避重試、逾時、
    條件跳過（condition）、失敗策略 halt/continue/compensate（saga 反序補償）、
    每任務 checkpoint 落盤、resume() 斷點續跑。
    """

    def __init__(self, store: Optional[RunStore] = None, quiet: bool = False):
        self.store = store or RunStore()
        self.quiet = quiet

    # -- 對外入口 ------------------------------------------------------------
    def run(self, wf: WorkflowSpec, params: Optional[Dict[str, Any]] = None,
            run_id: Optional[str] = None, persist: bool = True) -> WorkflowRun:
        wf.validate()
        run = WorkflowRun(wf.name, run_id or _new_run_id(wf.name), dict(params or {}))
        return self._execute(wf, run, done=set(), persist=persist)

    def resume(self, wf: WorkflowSpec, run_id: str, persist: bool = True) -> WorkflowRun:
        """從 checkpoint 續跑：已 SUCCESS 任務直接還原結果，不重跑。"""
        snap = self.store.load(run_id)
        if snap.get("workflow") != wf.name:
            raise ValueError("checkpoint 屬於工作流 %r，非 %r" % (snap.get("workflow"), wf.name))
        run = WorkflowRun(wf.name, run_id, snap.get("params", {}))
        run.started = snap.get("started", run.started)
        run.events = snap.get("events", [])
        run.state = dict(snap.get("state", {}))
        done = set()
        for rd in snap.get("results", []):
            tr = TaskResult.from_dict(rd)
            if tr.status == SUCCESS:
                run.results[tr.name] = tr
                done.add(tr.name)
        run.event("resume", "restored %d finished tasks" % len(done))
        self._log("↻ resume %s：還原 %d 個已完成任務" % (run_id, len(done)))
        return self._execute(wf, run, done=done, persist=persist)

    # -- 核心排程迴圈 --------------------------------------------------------
    def _execute(self, wf: WorkflowSpec, run: WorkflowRun, done: set, persist: bool) -> WorkflowRun:
        ctx = WorkflowContext(wf, run.params, run.run_id)
        ctx.results = run.results
        ctx._state.update(run.state)
        order = wf.topological_order()
        failed: set = set()
        skipped: set = set()
        lock = threading.Lock()
        completed_seq: List[str] = [n for n in order if n in done]  # 補償反序用

        def deps_ok(name: str) -> bool:
            return all(d in done for d in wf.tasks[name].depends_on)

        def deps_dead(name: str) -> bool:
            return any(d in failed or d in skipped for d in wf.tasks[name].depends_on)

        def checkpoint() -> None:
            run.state = ctx.state_snapshot()
            if persist:
                self.store.save(run)

        pending = [n for n in order if n not in done]
        halt = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=wf.max_parallel) as pool:
            futures: Dict[concurrent.futures.Future, str] = {}
            while pending or futures:
                if not halt:
                    ready = [n for n in pending if deps_ok(n)]
                    for n in ready:
                        pending.remove(n)
                        futures[pool.submit(self._run_task, wf.tasks[n], ctx)] = n
                # 依賴已死（失敗/跳過）的任務 → 級聯 SKIPPED
                for n in [n for n in pending if deps_dead(n)]:
                    pending.remove(n)
                    tr = TaskResult(name=n, status=SKIPPED,
                                    error="upstream failed/skipped")
                    with lock:
                        run.results[n] = tr
                        skipped.add(n)
                    run.event("skip", n)
                    self._log("⤳ SKIP %s（上游失敗/跳過）" % n)
                if halt and not futures:
                    break
                if not futures:
                    if pending:  # 不可達（全部剩餘任務依賴已死）
                        continue
                    break
                fdone, _ = concurrent.futures.wait(
                    list(futures), return_when=concurrent.futures.FIRST_COMPLETED)
                for f in fdone:
                    n = futures.pop(f)
                    tr: TaskResult = f.result()
                    with lock:
                        run.results[n] = tr
                        if tr.status == SUCCESS:
                            done.add(n)
                            completed_seq.append(n)
                        elif tr.status == SKIPPED:
                            skipped.add(n)
                        else:
                            failed.add(n)
                    run.event(tr.status.lower(), n)
                    checkpoint()
                    if tr.status == FAILED and wf.on_failure in ("halt", "compensate"):
                        halt = True

        if failed and wf.on_failure == "compensate":
            self._compensate(wf, ctx, run, completed_seq)
        run.status = FAILED if failed else SUCCESS
        run.ended = _utcnow()
        checkpoint()
        self._log("■ %s" % run.summary())
        return run

    # -- 單任務執行（重試 + 逾時 + 條件）------------------------------------
    def _run_task(self, spec: TaskSpec, ctx: WorkflowContext) -> TaskResult:
        tr = TaskResult(name=spec.name, started=_utcnow())
        try:
            if not _eval_condition(spec.condition, ctx):
                tr.status, tr.ended = SKIPPED, _utcnow()
                tr.error = "condition=False"
                self._log("⤳ SKIP %s（condition 不成立）" % spec.name)
                return tr
        except Exception as e:
            tr.status, tr.error, tr.ended = FAILED, "condition 評估失敗：%s" % e, _utcnow()
            return tr
        delay = spec.retry_delay
        for attempt in range(1, spec.retries + 2):
            tr.attempts = attempt
            tr.status = RUNNING
            try:
                self._log("▶ RUN %s（attempt %d/%d）" % (spec.name, attempt, spec.retries + 1))
                tr.output = self._invoke(spec, ctx)
                tr.status, tr.error, tr.ended = SUCCESS, None, _utcnow()
                self._log("✔ OK  %s" % spec.name)
                return tr
            except Exception as e:
                tr.error = "%s: %s" % (type(e).__name__, e)
                self._log("✘ ERR %s：%s" % (spec.name, tr.error))
                if attempt <= spec.retries:
                    time.sleep(max(0.0, delay))
                    delay *= max(1.0, spec.backoff)
        tr.status, tr.ended = FAILED, _utcnow()
        return tr

    def _invoke(self, spec: TaskSpec, ctx: WorkflowContext) -> Any:
        if spec.command is not None:
            return self._run_command(spec, ctx)
        if spec.timeout:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as one:
                fut = one.submit(_call_task_fn, spec.fn, ctx)
                try:
                    return fut.result(timeout=spec.timeout)
                except concurrent.futures.TimeoutError:
                    raise TimeoutError("task %r 超過 timeout=%ss" % (spec.name, spec.timeout))
        return _call_task_fn(spec.fn, ctx)

    def _run_command(self, spec: TaskSpec, ctx: WorkflowContext) -> Dict[str, Any]:
        import subprocess
        cmd = spec.command.format(**{**ctx.params, **spec.params}) if ("{" in spec.command) else spec.command
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              timeout=spec.timeout)
        if proc.returncode != 0:
            raise RuntimeError("command exit=%d stderr=%s" % (proc.returncode, proc.stderr.strip()[:400]))
        return {"exit": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}

    # -- saga 補償（Workflow Core / Temporal 典範）---------------------------
    def _compensate(self, wf: WorkflowSpec, ctx: WorkflowContext, run: WorkflowRun,
                    completed_seq: List[str]) -> None:
        self._log("↩ 失敗策略=compensate：反序執行補償（saga）")
        for n in reversed(completed_seq):
            comp = wf.tasks[n].compensate
            if not comp:
                continue
            try:
                comp(ctx)
                run.results[n].status = COMPENSATED
                run.event("compensated", n)
                self._log("↩ COMPENSATED %s" % n)
            except Exception as e:  # 補償失敗誠實記錄，不掩蓋
                run.event("compensate_failed", "%s: %s" % (n, e))
                self._log("‼ 補償失敗 %s：%s" % (n, e))

    def _log(self, msg: str) -> None:
        if not self.quiet:
            LOG.info(msg)

# ============================================================================
# §4 有限狀態機（Transitions 典範）— triggers / guards / callbacks / history
# ============================================================================

class StateMachineError(RuntimeError):
    pass


class StateMachine:
    """輕量 FSM（transitions 庫 API 風格）。

    transitions 定義：{"trigger","source"(str|list|'*'),"dest",
                       "conditions":[callable|method 名],"before","after"}
    - 觸發方法自動掛上 machine（machine.收到款項()）與 model（若提供）。
    - guard 全過才轉移；before/after 回調；完整 history。
    """

    def __init__(self, model: Any = None, states: Sequence[str] = (), transitions: Sequence[Dict] = (),
                 initial: Optional[str] = None, on_change: Optional[Callable[[str, str, str], None]] = None):
        if not states:
            raise ValueError("StateMachine 需要至少一個狀態")
        self.model = model if model is not None else self
        self.states = list(states)
        self.state = initial or self.states[0]
        if self.state not in self.states:
            raise ValueError("initial 狀態 %r 不在 states 中" % self.state)
        self.on_change = on_change
        self.history: List[Dict[str, str]] = []
        self._transitions: Dict[str, List[Dict]] = {}
        for t in transitions:
            self.add_transition(**t)

    def add_transition(self, trigger: str, source: Union[str, Sequence[str]], dest: str,
                       conditions: Sequence[Union[str, Callable]] = (),
                       before: Union[str, Callable, None] = None,
                       after: Union[str, Callable, None] = None) -> None:
        if dest not in self.states:
            raise ValueError("dest %r 不在 states 中" % dest)
        srcs = self.states if source == "*" else ([source] if isinstance(source, str) else list(source))
        for s in srcs:
            if s not in self.states:
                raise ValueError("source %r 不在 states 中" % s)
        self._transitions.setdefault(trigger, []).append(
            {"source": srcs, "dest": dest, "conditions": list(conditions),
             "before": before, "after": after})
        self._bind_trigger(trigger)

    def _bind_trigger(self, trigger: str) -> None:
        def fire(*a, **kw):
            return self.trigger(trigger, *a, **kw)
        fire.__name__ = trigger
        setattr(self, trigger, fire) if not hasattr(type(self), trigger) else None
        if self.model is not self and not hasattr(self.model, trigger):
            setattr(self.model, trigger, fire)

    def _resolve(self, cb: Union[str, Callable, None]) -> Optional[Callable]:
        if cb is None or callable(cb):
            return cb
        fn = getattr(self.model, cb, None)
        if not callable(fn):
            raise StateMachineError("回調 %r 不是 model 的方法" % cb)
        return fn

    def can(self, trigger: str) -> bool:
        return any(self.state in t["source"] and self._guards_pass(t)
                   for t in self._transitions.get(trigger, []))

    def _guards_pass(self, t: Dict) -> bool:
        for c in t["conditions"]:
            fn = self._resolve(c)
            if not fn():
                return False
        return True

    def trigger(self, name: str, *a, **kw) -> bool:
        cands = [t for t in self._transitions.get(name, []) if self.state in t["source"]]
        if not cands:
            raise StateMachineError("狀態 %r 下無法觸發 %r（合法觸發：%s）"
                                    % (self.state, name, sorted(self.available_triggers())))
        for t in cands:
            if not self._guards_pass(t):
                continue
            before, after = self._resolve(t["before"]), self._resolve(t["after"])
            src = self.state
            if before:
                before(*a, **kw)
            self.state = t["dest"]
            if self.model is not self:
                try:
                    self.model.state = self.state
                except Exception:
                    pass
            self.history.append({"ts": _utcnow(), "trigger": name, "source": src, "dest": t["dest"]})
            if after:
                after(*a, **kw)
            if self.on_change:
                self.on_change(name, src, t["dest"])
            return True
        return False  # guard 全擋（誠實回報未轉移）

    def available_triggers(self) -> List[str]:
        return sorted({tr for tr, ts in self._transitions.items()
                       if any(self.state in t["source"] for t in ts)})

    def to_mermaid(self) -> str:
        lines = ["stateDiagram-v2", "    [*] --> %s" % self.states[0]]
        for tr, ts in self._transitions.items():
            for t in ts:
                for s in t["source"]:
                    lines.append("    %s --> %s : %s" % (s, t["dest"], tr))
        return "\n".join(lines)

# ============================================================================
# §5 循環狀態圖（LangGraph 典範）— 可回頭路的 Agent 思考圖 + checkpoint
# ============================================================================

END = "__end__"


class StateGraph:
    """循環圖引擎（LangGraph API 風格）。

    - add_node(name, fn)：fn(state: dict) -> dict（回傳「部分更新」merge 進 state）
    - add_edge(a, b)；add_conditional_edges(node, router, mapping)
    - DAG 引擎禁環；本引擎允許環（AI 反覆修正典範），以 max_steps 保險絲護欄。
    - compile() 後 invoke()；每步 checkpoint（可觀測 steps trace）。
    """

    def __init__(self, name: str = "state_graph"):
        self.name = name
        self.nodes: Dict[str, Callable[[Dict], Optional[Dict]]] = {}
        self.edges: Dict[str, str] = {}
        self.branches: Dict[str, Tuple[Callable[[Dict], str], Dict[str, str]]] = {}
        self.entry: Optional[str] = None

    def add_node(self, name: str, fn: Callable[[Dict], Optional[Dict]]) -> "StateGraph":
        if name == END:
            raise ValueError("節點名不可為 END 保留字")
        self.nodes[name] = fn
        return self

    def set_entry(self, name: str) -> "StateGraph":
        self.entry = name
        return self

    def add_edge(self, src: str, dst: str) -> "StateGraph":
        self._check(src, dst)
        self.edges[src] = dst
        return self

    def add_conditional_edges(self, src: str, router: Callable[[Dict], str],
                              mapping: Dict[str, str]) -> "StateGraph":
        for d in mapping.values():
            self._check(src, d)
        self.branches[src] = (router, dict(mapping))
        return self

    def _check(self, src: str, dst: str) -> None:
        if src not in self.nodes:
            raise ValueError("未知節點 %r" % src)
        if dst != END and dst not in self.nodes:
            raise ValueError("未知節點 %r" % dst)

    def compile(self, max_steps: int = 100) -> "CompiledStateGraph":
        if not self.entry:
            raise ValueError("尚未 set_entry()")
        return CompiledStateGraph(self, max_steps)


class CompiledStateGraph:
    def __init__(self, graph: StateGraph, max_steps: int):
        self.graph = graph
        self.max_steps = max_steps

    def invoke(self, state: Optional[Dict] = None, verbose: bool = False) -> Dict:
        st = dict(state or {})
        trace: List[Dict[str, Any]] = []
        node = self.graph.entry
        for i in range(self.max_steps):
            if node == END:
                break
            fn = self.graph.nodes[node]
            update = fn(st) or {}
            if not isinstance(update, dict):
                raise TypeError("節點 %r 需回傳 dict 部分更新，得到 %r" % (node, type(update)))
            st.update(update)
            trace.append({"step": i + 1, "node": node, "update": sorted(update.keys())})
            if verbose:
                LOG.info("⟳ step %d：%s → state+%s" % (i + 1, node, sorted(update.keys())))
            if node in self.graph.branches:
                router, mapping = self.graph.branches[node]
                key = router(st)
                if key not in mapping:
                    raise KeyError("router 回傳 %r 不在 mapping %s" % (key, sorted(mapping)))
                node = mapping[key]
            elif node in self.graph.edges:
                node = self.graph.edges[node]
            else:
                node = END
        else:
            raise RuntimeError("StateGraph 超過 max_steps=%d（疑似無窮迴圈）" % self.max_steps)
        st["__trace__"] = trace
        return st

# ============================================================================
# §6 事件驅動工作流（LlamaIndex Workflows 典範）— Event / @step / EventWorkflow
# ============================================================================

class Event:
    """事件基類：任意 payload kwargs（ev.key 直接取值）。"""

    def __init__(self, **payload: Any):
        self._payload = dict(payload)

    def __getattr__(self, item: str) -> Any:
        try:
            return self.__dict__["_payload"][item]
        except KeyError:
            raise AttributeError("%s 沒有欄位 %r" % (type(self).__name__, item))

    def get(self, key: str, default: Any = None) -> Any:
        return self._payload.get(key, default)

    def __repr__(self) -> str:
        return "%s(%s)" % (type(self).__name__, ", ".join("%s=%r" % kv for kv in self._payload.items()))


class StartEvent(Event):
    pass


class StopEvent(Event):
    def __init__(self, result: Any = None, **payload: Any):
        super().__init__(result=result, **payload)


def step(*event_types: Type[Event]) -> Callable:
    """步驟裝飾器：@step(SomeEvent) — 收該型事件；回傳 Event / [Event] / None。"""
    if not event_types:
        raise ValueError("@step 需要至少一個事件型別")
    for et in event_types:
        if not (isinstance(et, type) and issubclass(et, Event)):
            raise TypeError("@step 參數需為 Event 子類，得到 %r" % (et,))

    def deco(fn: Callable) -> Callable:
        fn.__via_step_events__ = event_types
        return fn
    return deco


class EventWorkflow:
    """事件驅動引擎：StartEvent 進場 → 依型別派發至 @step 處理器 → StopEvent 收場。

    - 同型多處理器 = 廣播（並行波次執行）
    - 處理器回傳事件（單一或列表）續推流程；StopEvent.result 即 run() 回傳值
    - max_iterations 保險絲；無人處理的事件誠實入 unhandled
    """

    def __init__(self, max_iterations: int = 200, verbose: bool = False):
        self.max_iterations = max_iterations
        self.verbose = verbose
        self._handlers: List[Tuple[Tuple[Type[Event], ...], Callable]] = []
        for attr in dir(self):
            fn = getattr(self, attr)
            if callable(fn) and getattr(fn, "__via_step_events__", None):
                self._handlers.append((fn.__via_step_events__, fn))

    def run(self, **kwargs: Any) -> Any:
        queue: deque = deque([StartEvent(**kwargs)])
        unhandled: List[Event] = []
        self.context: Dict[str, Any] = {}
        for _ in range(self.max_iterations):
            if not queue:
                raise RuntimeError("事件佇列耗盡但未收到 StopEvent（流程未閉合）")
            ev = queue.popleft()
            if isinstance(ev, StopEvent):
                self.unhandled = unhandled
                return ev.get("result")
            matched = [fn for types, fn in self._handlers if isinstance(ev, types)]
            if not matched:
                unhandled.append(ev)
                continue
            for fn in matched:
                if self.verbose:
                    LOG.info("⚡ %s ← %r" % (fn.__name__, ev))
                out = fn(ev)
                if out is None:
                    continue
                for nxt in (out if isinstance(out, (list, tuple)) else [out]):
                    if not isinstance(nxt, Event):
                        raise TypeError("步驟 %s 回傳非 Event：%r" % (fn.__name__, nxt))
                    queue.append(nxt)
        raise RuntimeError("EventWorkflow 超過 max_iterations=%d" % self.max_iterations)

# ============================================================================
# §7 多智能體協作（CrewAI 典範）— Agent / CrewTask / Crew（sequential|hierarchical）
# ============================================================================

class Agent:
    """角色扮演智能體。llm 為可插拔 callable(prompt)->str；缺席時使用本地
    確定性合成器（工具結果 + 上下文摘要）— 零網路、零依賴、誠實標示來源。"""

    def __init__(self, role: str, goal: str, backstory: str = "",
                 llm: Optional[Callable[[str], str]] = None,
                 tools: Optional[Dict[str, Callable[..., Any]]] = None, verbose: bool = False):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.llm = llm
        self.tools = dict(tools or {})
        self.verbose = verbose

    def execute(self, description: str, context: str = "", inputs: Optional[Dict[str, Any]] = None) -> str:
        prompt = self.build_prompt(description, context, inputs or {})
        if self.verbose:
            LOG.info("🤖 [%s] 執行任務：%s" % (self.role, description[:60]))
        tool_notes = []
        for name, fn in self.tools.items():
            try:  # 工具全跑（本地 Crew 的確定性策略）；個別失敗誠實記錄
                tool_notes.append("- tool[%s] → %r" % (name, fn(inputs or {})))
            except Exception as e:
                tool_notes.append("- tool[%s] FAILED: %s" % (name, e))
        if self.llm:
            return self.llm(prompt + ("\n\nTOOL RESULTS:\n" + "\n".join(tool_notes) if tool_notes else ""))
        # 本地合成器（無 LLM）：結構化輸出，絕不佯裝生成式內容
        lines = ["[%s] deterministic local synthesis（未接 LLM）" % self.role,
                 "goal: %s" % self.goal, "task: %s" % description]
        if inputs:
            lines.append("inputs: %s" % json.dumps(inputs, ensure_ascii=False, default=repr))
        if tool_notes:
            lines.append("tools:\n" + "\n".join(tool_notes))
        if context:
            lines.append("context:\n%s" % context)
        return "\n".join(lines)

    def build_prompt(self, description: str, context: str, inputs: Dict[str, Any]) -> str:
        parts = ["You are %s." % self.role]
        if self.backstory:
            parts.append("Backstory: %s" % self.backstory)
        parts.append("Your goal: %s" % self.goal)
        if context:
            parts.append("Context from previous tasks:\n%s" % context)
        if inputs:
            parts.append("Inputs: %s" % json.dumps(inputs, ensure_ascii=False, default=repr))
        parts.append("Task: %s" % description)
        return "\n\n".join(parts)


@dataclass
class CrewTask:
    description: str
    agent: Agent
    expected_output: str = ""
    name: str = ""
    context: List["CrewTask"] = field(default_factory=list)
    output: Optional[str] = None

    def __post_init__(self):
        if not self.name:
            self.name = re.sub(r"\W+", "_", self.description[:32]).strip("_").lower() or "task"


class Crew:
    """多任務多智能體編排。process：
    - sequential：任務依序執行，前手輸出自動入後手 context
    - hierarchical：manager（可自訂）依任務 context 依賴做拓撲派工"""

    def __init__(self, agents: Sequence[Agent], tasks: Sequence[CrewTask],
                 process: str = "sequential", manager: Optional[Agent] = None, verbose: bool = False):
        if process not in ("sequential", "hierarchical"):
            raise ValueError("process 需為 sequential|hierarchical")
        self.agents = list(agents)
        self.tasks = list(tasks)
        self.process = process
        self.manager = manager
        self.verbose = verbose

    def kickoff(self, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        inputs = dict(inputs or {})
        ordered = self.tasks if self.process == "sequential" else self._topo_tasks()
        transcript: List[Dict[str, str]] = []
        prev_output = ""
        for t in ordered:
            ctx_parts = [c.output or "" for c in t.context if c.output]
            if self.process == "sequential" and not t.context and prev_output:
                ctx_parts = [prev_output]
            if self.process == "hierarchical" and self.manager:
                plan = self.manager.execute(
                    "Delegate and brief the task for %s: %s" % (t.agent.role, t.description),
                    context="\n---\n".join(ctx_parts), inputs=inputs)
                ctx_parts.append("[manager brief]\n%s" % plan)
            t.output = t.agent.execute(t.description, context="\n---\n".join(ctx_parts), inputs=inputs)
            prev_output = t.output
            transcript.append({"task": t.name, "agent": t.agent.role, "output": t.output})
            if self.verbose:
                LOG.info("👥 task=%s by %s → %d chars" % (t.name, t.agent.role, len(t.output)))
        return {"final": prev_output, "tasks": transcript, "process": self.process}

    def _topo_tasks(self) -> List[CrewTask]:
        indeg = {id(t): len(t.context) for t in self.tasks}
        by_id = {id(t): t for t in self.tasks}
        children: Dict[int, List[int]] = {id(t): [] for t in self.tasks}
        for t in self.tasks:
            for c in t.context:
                if id(c) in children:
                    children[id(c)].append(id(t))
        q = deque([i for i, d in indeg.items() if d == 0])
        order: List[CrewTask] = []
        while q:
            i = q.popleft()
            order.append(by_id[i])
            for ch in children[i]:
                indeg[ch] -= 1
                if indeg[ch] == 0:
                    q.append(ch)
        if len(order) != len(self.tasks):
            raise ValueError("CrewTask context 依賴形成環")
        return order

# ============================================================================
# §8 裝飾器流（Prefect 典範）— @via_task / @via_flow（重試/逾時/執行紀錄）
# ============================================================================

_FLOW_STACK: "threading.local" = threading.local()
FLOW_REGISTRY: Dict[str, Callable] = {}
TASK_REGISTRY: Dict[str, Callable] = {}


def via_task(fn: Optional[Callable] = None, *, name: Optional[str] = None, retries: int = 0,
             retry_delay: float = 1.0, backoff: float = 2.0, timeout: Optional[float] = None):
    """Prefect 風格 @task：flow 內呼叫自動記錄 TaskResult；獨立呼叫照常執行。"""

    def deco(f: Callable) -> Callable:
        tname = name or f.__name__

        def wrapper(*a, **kw):
            flow_run: Optional[WorkflowRun] = getattr(_FLOW_STACK, "run", None)
            tr = TaskResult(name=tname, started=_utcnow())
            delay = retry_delay
            for attempt in range(1, retries + 2):
                tr.attempts = attempt
                try:
                    if timeout:
                        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as one:
                            out = one.submit(f, *a, **kw).result(timeout=timeout)
                    else:
                        out = f(*a, **kw)
                    tr.status, tr.output, tr.ended = SUCCESS, out, _utcnow()
                    break
                except Exception as e:
                    tr.error = "%s: %s" % (type(e).__name__, e)
                    if attempt <= retries:
                        LOG.info("↻ retry %s（%d/%d）：%s" % (tname, attempt, retries, tr.error))
                        time.sleep(max(0.0, delay))
                        delay *= max(1.0, backoff)
                    else:
                        tr.status, tr.ended = FAILED, _utcnow()
            if flow_run is not None:
                key = tname if tname not in flow_run.results else "%s#%d" % (tname, len(flow_run.results))
                flow_run.results[key] = tr
            if tr.status == FAILED:
                raise RuntimeError("task %r 最終失敗：%s" % (tname, tr.error))
            return tr.output

        wrapper.__name__ = tname
        wrapper.__wrapped__ = f
        wrapper.__via_task__ = {"retries": retries, "retry_delay": retry_delay,
                                "backoff": backoff, "timeout": timeout}
        TASK_REGISTRY[tname] = wrapper
        return wrapper

    return deco(fn) if callable(fn) else deco


def via_flow(fn: Optional[Callable] = None, *, name: Optional[str] = None,
             persist: bool = False, store: Optional[RunStore] = None):
    """Prefect 風格 @flow：執行 = 一個 WorkflowRun；flow 內 @via_task 全記錄。
    wrapper.last_run 取得完整 run；persist=True 落 .via_runs/。"""

    def deco(f: Callable) -> Callable:
        fname = name or f.__name__

        def wrapper(*a, **kw):
            run = WorkflowRun(fname, _new_run_id(fname), {})
            outer = getattr(_FLOW_STACK, "run", None)
            _FLOW_STACK.run = run
            LOG.info("═ flow %s 開始（run_id=%s）" % (fname, run.run_id))
            try:
                out = f(*a, **kw)
                run.status = SUCCESS
                return out
            except Exception:
                run.status = FAILED
                raise
            finally:
                run.ended = _utcnow()
                _FLOW_STACK.run = outer
                wrapper.last_run = run
                if persist:
                    (store or RunStore()).save(run)
                LOG.info("═ flow %s 結束 %s" % (fname, run.summary()))

        wrapper.__name__ = fname
        wrapper.__wrapped__ = f
        wrapper.last_run = None
        wrapper.__via_flow__ = True
        FLOW_REGISTRY[fname] = wrapper
        return wrapper

    return deco(fn) if callable(fn) else deco

# ============================================================================
# §9 排程（Airflow/Dagu cron 典範）— 5 欄 cron 解析 + 本地 Scheduler
# ============================================================================

class Cron:
    """5 欄 cron（minute hour day-of-month month day-of-week）。
    支援 * , - */n 與數字；dow 0/7=週日。next_after() 以分鐘步進求下次觸發。"""

    _RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]

    def __init__(self, expr: str):
        fields = expr.split()
        if len(fields) != 5:
            raise ValueError("cron 需 5 欄，得到 %r" % expr)
        self.expr = expr
        self.sets: List[set] = [self._parse(f, lo, hi) for f, (lo, hi) in zip(fields, self._RANGES)]

    @staticmethod
    def _parse(fld: str, lo: int, hi: int) -> set:
        out: set = set()
        for part in fld.split(","):
            step = 1
            if "/" in part:
                part, step_s = part.split("/", 1)
                step = int(step_s)
                if step < 1:
                    raise ValueError("cron step 需 ≥1")
            if part in ("*", ""):
                rng = range(lo, hi + 1)
            elif "-" in part:
                a, b = part.split("-", 1)
                rng = range(int(a), int(b) + 1)
            else:
                rng = range(int(part), int(part) + 1)
            for v in rng:
                if not (lo <= v <= hi):
                    raise ValueError("cron 值 %d 超界 [%d,%d]" % (v, lo, hi))
                out.add(v % 7 if (lo, hi) == (0, 7) and v == 7 else v)
        return out

    def matches(self, dt: datetime) -> bool:
        m, h, dom, mon, dow = self.sets
        return (dt.minute in m and dt.hour in h and dt.day in dom
                and dt.month in mon and (dt.weekday() + 1) % 7 in dow)

    def next_after(self, dt: Optional[datetime] = None) -> datetime:
        t = (dt or datetime.now()).replace(second=0, microsecond=0) + timedelta(minutes=1)
        for _ in range(366 * 24 * 60):  # 一年上限（防死循環）
            if self.matches(t):
                return t
            t += timedelta(minutes=1)
        raise ValueError("cron %r 一年內無下次觸發" % self.expr)


class Scheduler:
    """本地排程器（Dagu/Airflow scheduler 的單機簡化）：
    add(name, cron, fn) → start() 背景執行緒每分鐘檢查；run_pending(now) 供測試。"""

    def __init__(self, quiet: bool = False):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.quiet = quiet

    def add(self, name: str, cron_expr: str, fn: Callable[[], Any]) -> "Scheduler":
        self.jobs[name] = {"cron": Cron(cron_expr), "fn": fn, "last": None,
                           "runs": 0, "errors": 0}
        return self

    def add_workflow(self, wf: WorkflowSpec, engine: Optional[LocalDAGEngine] = None,
                     params: Optional[Dict[str, Any]] = None) -> "Scheduler":
        if not wf.schedule:
            raise ValueError("WorkflowSpec %r 沒有 schedule" % wf.name)
        eng = engine or LocalDAGEngine(quiet=self.quiet)
        return self.add(wf.name, wf.schedule, lambda: eng.run(wf, params))

    def run_pending(self, now: Optional[datetime] = None) -> List[str]:
        now = (now or datetime.now()).replace(second=0, microsecond=0)
        fired: List[str] = []
        for name, job in self.jobs.items():
            if job["last"] == now:  # 同一分鐘不重複觸發
                continue
            if job["cron"].matches(now):
                job["last"] = now
                job["runs"] += 1
                fired.append(name)
                try:
                    job["fn"]()
                except Exception as e:  # 排程任務失敗誠實記錄，不中斷排程器
                    job["errors"] += 1
                    LOG.error("⏰ job %s 失敗：%s" % (name, e))
        return fired

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()

        def loop():
            while not self._stop.is_set():
                self.run_pending()
                self._stop.wait(1.0)
        self._thread = threading.Thread(target=loop, name="VIA-Scheduler", daemon=True)
        self._thread.start()
        if not self.quiet:
            LOG.info("⏰ Scheduler 啟動（%d jobs）" % len(self.jobs))

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)

    def table(self) -> List[Dict[str, Any]]:
        now = datetime.now()
        return [{"job": n, "cron": j["cron"].expr, "runs": j["runs"], "errors": j["errors"],
                 "next": j["cron"].next_after(now).strftime("%Y-%m-%d %H:%M")}
                for n, j in self.jobs.items()]

# ============================================================================
# §10 宣告式 DSL（Kestra/Dagu/Conductor 典範）— YAML/JSON 載入
# ============================================================================

def load_workflow_file(path: Union[str, Path],
                       fn_registry: Optional[Dict[str, Callable]] = None) -> WorkflowSpec:
    """載入 YAML（需 PyYAML）或 JSON 工作流定義 → WorkflowSpec。

    綱要（Dagu/Kestra 混和風格，兩鍵名皆收）：
      name: my_flow            # 必要
      schedule: "0 1 * * *"    # 選用（cron 5 欄）
      max_parallel: 4
      on_failure: halt|continue|compensate
      steps:                   # 或 tasks:
        - name: step1
          command: "echo hi"   # shell 任務
        - name: step2
          python: mymod.myfn   # Python 任務（module.fn 或 registry 名）
          depends_on: [step1]
          retries: 3           # 或 retry: {limit: 3, interval: 5}
          timeout: 60
          condition: "outputs['step1']['exit'] == 0"
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError("工作流檔不存在：%s" % p)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        if _yaml is None:
            raise RuntimeError("讀 YAML 需要 PyYAML：pip install pyyaml（或改用 JSON 定義檔）")
        data = _yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("工作流定義需為 mapping，得到 %r" % type(data))
    return WorkflowSpec.from_dict(data, fn_registry=fn_registry)

# ============================================================================
# §11 匯出器（Exporters）— 產出各引擎「官方原生定義檔」與前端圖形 JSON
#     （外部伺服器型引擎的誠實整合：codegen，不佯裝連線）
# ============================================================================

class Exporters:
    FORMATS = ("dagu", "kestra", "argo", "conductor", "airflow", "temporal",
               "bpmn", "reactflow", "x6", "n8n", "mermaid", "viewflow")

    # -- 佈局輔助：拓撲分層（前端圖用）--------------------------------------
    @staticmethod
    def _layers(wf: WorkflowSpec) -> Dict[str, int]:
        depth: Dict[str, int] = {}
        for n in wf.topological_order():
            deps = wf.tasks[n].depends_on
            depth[n] = 1 + max((depth[d] for d in deps), default=-1)
        return depth

    @staticmethod
    def _cmd_of(t: TaskSpec) -> str:
        if t.command:
            return t.command
        if t.fn:
            return "python -c \"import %s as m; m.%s()\"" % (t.fn.__module__, t.fn.__qualname__)
        return "true"

    # -- Dagu（YAML, single-binary 引擎）------------------------------------
    @classmethod
    def to_dagu_yaml(cls, wf: WorkflowSpec) -> str:
        lines = ["# Dagu DAG — generated by VIA_WorkflowEngine v%s" % __version__,
                 "name: %s" % json.dumps(wf.name, ensure_ascii=False)]
        if wf.description:
            lines.append("description: %s" % json.dumps(wf.description, ensure_ascii=False))
        if wf.schedule:
            lines.append('schedule: "%s"' % wf.schedule)
        lines.append("steps:")
        for t in wf.tasks.values():
            lines.append("  - name: %s" % json.dumps(t.name, ensure_ascii=False))
            lines.append("    command: %s" % json.dumps(cls._cmd_of(t), ensure_ascii=False))
            if t.depends_on:
                lines.append("    depends:")
                lines.extend("      - %s" % json.dumps(d, ensure_ascii=False) for d in t.depends_on)
            if t.retries:
                lines.append("    retryPolicy:")
                lines.append("      limit: %d" % t.retries)
                lines.append("      intervalSec: %d" % int(t.retry_delay))
        return "\n".join(lines) + "\n"

    # -- Kestra（YAML, declarative orchestration）---------------------------
    @classmethod
    def to_kestra_yaml(cls, wf: WorkflowSpec) -> str:
        lines = ["# Kestra flow — generated by VIA_WorkflowEngine v%s" % __version__,
                 "id: %s" % re.sub(r"\W+", "_", wf.name).lower(),
                 "namespace: via.generated"]
        if wf.description:
            lines.append("description: %s" % json.dumps(wf.description, ensure_ascii=False))
        lines.append("tasks:")
        for t in wf.tasks.values():  # Kestra 主幹為序列；依賴以拓撲序保序
            lines.append("  - id: %s" % re.sub(r"\W+", "_", t.name).lower())
            lines.append("    type: io.kestra.plugin.scripts.shell.Commands")
            lines.append("    commands:")
            lines.append("      - %s" % json.dumps(cls._cmd_of(t), ensure_ascii=False))
            if t.retries:
                lines.append("    retry:")
                lines.append("      type: constant")
                lines.append("      maxAttempt: %d" % (t.retries + 1))
                lines.append("      interval: PT%dS" % int(t.retry_delay))
        if wf.schedule:
            lines += ["triggers:", "  - id: schedule",
                      "    type: io.kestra.plugin.core.trigger.Schedule",
                      '    cron: "%s"' % wf.schedule]
        return "\n".join(lines) + "\n"

    # -- Argo Workflows（K8s YAML, DAG template）----------------------------
    @classmethod
    def to_argo_yaml(cls, wf: WorkflowSpec) -> str:
        safe = re.sub(r"[^a-z0-9-]", "-", wf.name.lower()).strip("-") or "via-flow"
        L = ["# Argo Workflow — generated by VIA_WorkflowEngine v%s" % __version__,
             "apiVersion: argoproj.io/v1alpha1", "kind: Workflow",
             "metadata:", "  generateName: %s-" % safe, "spec:",
             "  entrypoint: main", "  templates:", "    - name: main", "      dag:",
             "        tasks:"]
        for t in wf.tasks.values():
            tid = re.sub(r"[^a-z0-9-]", "-", t.name.lower()).strip("-")
            L.append("          - name: %s" % tid)
            if t.depends_on:
                deps = " && ".join(re.sub(r"[^a-z0-9-]", "-", d.lower()).strip("-") for d in t.depends_on)
                L.append("            depends: %s" % json.dumps(deps))
            L.append("            template: t-%s" % tid)
        for t in wf.tasks.values():
            tid = re.sub(r"[^a-z0-9-]", "-", t.name.lower()).strip("-")
            L += ["    - name: t-%s" % tid, "      container:", "        image: alpine:3.20",
                  "        command: [sh, -c]",
                  "        args: [%s]" % json.dumps(cls._cmd_of(t), ensure_ascii=False)]
            if t.retries:
                L += ["      retryStrategy:", "        limit: %d" % t.retries]
        return "\n".join(L) + "\n"

    # -- Netflix Conductor（JSON workflow def）------------------------------
    @classmethod
    def to_conductor_json(cls, wf: WorkflowSpec) -> str:
        tasks = [{"name": t.name, "taskReferenceName": t.name, "type": "SIMPLE",
                  "inputParameters": {**t.params, "command": cls._cmd_of(t)},
                  "retryCount": t.retries}
                 for t in (wf.tasks[n] for n in wf.topological_order())]
        doc = {"name": wf.name, "description": wf.description or wf.name, "version": 1,
               "schemaVersion": 2, "ownerEmail": "via@local", "tasks": tasks,
               "timeoutPolicy": "ALERT_ONLY", "timeoutSeconds": 0}
        return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"

    # -- Apache Airflow（DAG .py codegen）-----------------------------------
    @classmethod
    def to_airflow_py(cls, wf: WorkflowSpec) -> str:
        dag_id = re.sub(r"\W+", "_", wf.name).lower()
        L = ['# -*- coding: utf-8 -*-',
             '"""Airflow DAG — generated by VIA_WorkflowEngine v%s."""' % __version__,
             "from datetime import datetime, timedelta",
             "from airflow import DAG",
             "from airflow.operators.bash import BashOperator", "",
             "with DAG(",
             "    dag_id=%r," % dag_id,
             "    schedule=%r," % (wf.schedule or None),
             "    start_date=datetime(2026, 1, 1),",
             "    catchup=False,",
             "    description=%r," % (wf.description or wf.name),
             ") as dag:"]
        var = {n: "t_%s" % re.sub(r"\W+", "_", n).lower() for n in wf.tasks}
        for t in wf.tasks.values():
            L.append("    %s = BashOperator(" % var[t.name])
            L.append("        task_id=%r," % t.name)
            L.append("        bash_command=%r," % cls._cmd_of(t))
            L.append("        retries=%d," % t.retries)
            L.append("        retry_delay=timedelta(seconds=%d)," % int(t.retry_delay))
            L.append("    )")
        for t in wf.tasks.values():
            for d in t.depends_on:
                L.append("    %s >> %s" % (var[d], var[t.name]))
        return "\n".join(L) + "\n"

    # -- Temporal Python SDK（workflow+worker codegen）-----------------------
    @classmethod
    def to_temporal_py(cls, wf: WorkflowSpec) -> str:
        cls_name = "".join(w.capitalize() for w in re.split(r"\W+", wf.name) if w) or "ViaFlow"
        order = wf.topological_order()
        L = ['# -*- coding: utf-8 -*-',
             '"""Temporal workflow — generated by VIA_WorkflowEngine v%s' % __version__,
             '需要本地 Temporal dev server：temporal server start-dev（或 scaffold temporal）"""',
             "import asyncio, subprocess",
             "from datetime import timedelta",
             "from temporalio import activity, workflow",
             "from temporalio.client import Client",
             "from temporalio.worker import Worker", "",
             "COMMANDS = %s" % json.dumps({n: cls._cmd_of(wf.tasks[n]) for n in order},
                                          ensure_ascii=False, indent=4), "", "",
             "@activity.defn",
             "async def run_step(name: str) -> str:",
             "    proc = subprocess.run(COMMANDS[name], shell=True, capture_output=True, text=True)",
             "    if proc.returncode != 0:",
             "        raise RuntimeError(f'step {name} exit={proc.returncode}: {proc.stderr[:300]}')",
             "    return proc.stdout", "", "",
             "@workflow.defn",
             "class %s:" % cls_name,
             "    @workflow.run",
             "    async def run(self) -> dict:",
             "        out = {}",
             "        for name in %r:" % order,
             "            out[name] = await workflow.execute_activity(",
             "                run_step, name, start_to_close_timeout=timedelta(minutes=10),",
             "            )",
             "        return out", "", "",
             "async def main():",
             "    client = await Client.connect('localhost:7233')",
             "    async with Worker(client, task_queue=%r," % ("via-%s" % re.sub(r"\W+", "-", wf.name).lower()),
             "                      workflows=[%s], activities=[run_step]):" % cls_name,
             "        result = await client.execute_workflow(",
             "            %s.run, id=%r, task_queue=%r," % (
                 cls_name, "via-%s-run" % re.sub(r"\W+", "-", wf.name).lower(),
                 "via-%s" % re.sub(r"\W+", "-", wf.name).lower()),
             "        )",
             "        print(result)", "",
             "if __name__ == '__main__':",
             "    asyncio.run(main())"]
        return "\n".join(L) + "\n"

    # -- BPMN 2.0 XML（SpiffWorkflow 可執行 / bpmn-js 可渲染）----------------
    @classmethod
    def to_bpmn_xml(cls, wf: WorkflowSpec) -> str:
        from xml.sax.saxutils import escape, quoteattr
        pid = re.sub(r"\W+", "_", wf.name) or "via_process"
        order = wf.topological_order()
        depth = cls._layers(wf)
        flows: List[Tuple[str, str]] = [("start", order[0] if order else "end")]
        for t in wf.tasks.values():
            for d in t.depends_on:
                flows.append((d, t.name))
        sinks = [n for n in wf.tasks if not any(n in t.depends_on for t in wf.tasks.values())]
        flows += [(s, "end") for s in (sinks or [])]
        eid = lambda n: "id_" + re.sub(r"\W+", "_", n)
        X = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"',
             '    xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"',
             '    xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"',
             '    xmlns:di="http://www.omg.org/spec/DD/20100524/DI"',
             '    id="defs_%s" targetNamespace="http://via.local/bpmn">' % pid,
             '  <bpmn:process id=%s isExecutable="true">' % quoteattr(pid),
             '    <bpmn:startEvent id="id_start" name="start"/>']
        for t in wf.tasks.values():
            X.append('    <bpmn:task id=%s name=%s/>' % (quoteattr(eid(t.name)), quoteattr(t.name)))
        X.append('    <bpmn:endEvent id="id_end" name="end"/>')
        for i, (a, b) in enumerate(flows):
            src = "id_start" if a == "start" else eid(a)
            dst = "id_end" if b == "end" else eid(b)
            X.append('    <bpmn:sequenceFlow id="flow_%d" sourceRef=%s targetRef=%s/>'
                     % (i, quoteattr(src), quoteattr(dst)))
        X.append('  </bpmn:process>')
        # DI 座標（bpmn-js 渲染用）：x=依拓撲層、y=層內序
        X.append('  <bpmndi:BPMNDiagram id="dia"><bpmndi:BPMNPlane id="plane" bpmnElement=%s>' % quoteattr(pid))
        max_d = max(depth.values(), default=0)
        pos: Dict[str, Tuple[int, int]] = {"id_start": (40, 100), "id_end": (40 + (max_d + 2) * 180, 100)}
        lane_seen: Dict[int, int] = {}
        for n in order:
            d = depth[n]
            lane_seen[d] = lane_seen.get(d, 0)
            pos[eid(n)] = (40 + (d + 1) * 180, 60 + lane_seen[d] * 110)
            lane_seen[d] += 1
        for el, (x, y) in pos.items():
            w, h = ((36, 36) if el in ("id_start", "id_end") else (120, 60))
            X.append('    <bpmndi:BPMNShape id="s_%s" bpmnElement=%s>'
                     '<dc:Bounds x="%d" y="%d" width="%d" height="%d"/></bpmndi:BPMNShape>'
                     % (el, quoteattr(el), x, y, w, h))
        X.append('  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>')
        X.append('</bpmn:definitions>')
        return "\n".join(X) + "\n"

    # -- React Flow / AntV X6 / n8n / mermaid（前端與自動化平台）------------
    @classmethod
    def to_reactflow_json(cls, wf: WorkflowSpec) -> str:
        depth = cls._layers(wf)
        lane: Dict[int, int] = {}
        nodes, edges = [], []
        for n in wf.topological_order():
            d = depth[n]
            lane[d] = lane.get(d, 0)
            nodes.append({"id": n, "type": "default", "data": {"label": n},
                          "position": {"x": d * 220, "y": lane[d] * 100}})
            lane[d] += 1
            for dep in wf.tasks[n].depends_on:
                edges.append({"id": "e_%s_%s" % (dep, n), "source": dep, "target": n,
                              "animated": True})
        return json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=2) + "\n"

    @classmethod
    def to_x6_json(cls, wf: WorkflowSpec) -> str:
        depth = cls._layers(wf)
        lane: Dict[int, int] = {}
        cells = []
        for n in wf.topological_order():
            d = depth[n]
            lane[d] = lane.get(d, 0)
            cells.append({"id": n, "shape": "rect", "x": d * 220, "y": lane[d] * 100,
                          "width": 140, "height": 48, "label": n})
            lane[d] += 1
        for t in wf.tasks.values():
            for dep in t.depends_on:
                cells.append({"id": "e_%s_%s" % (dep, t.name), "shape": "edge",
                              "source": dep, "target": t.name})
        return json.dumps({"cells": cells}, ensure_ascii=False, indent=2) + "\n"

    @classmethod
    def to_n8n_json(cls, wf: WorkflowSpec) -> str:
        depth = cls._layers(wf)
        lane: Dict[int, int] = {}
        nodes = [{"id": "start", "name": "Start", "type": "n8n-nodes-base.manualTrigger",
                  "typeVersion": 1, "position": [0, 0], "parameters": {}}]
        conns: Dict[str, Any] = {}
        roots = [n for n, t in wf.tasks.items() if not t.depends_on]
        for n in wf.topological_order():
            d = depth[n]
            lane[d] = lane.get(d, 0)
            nodes.append({"id": n, "name": n, "type": "n8n-nodes-base.executeCommand",
                          "typeVersion": 1, "position": [(d + 1) * 240, lane[d] * 120],
                          "parameters": {"command": cls._cmd_of(wf.tasks[n])}})
            lane[d] += 1
        def connect(a: str, b: str) -> None:
            conns.setdefault(a, {"main": [[]]})["main"][0].append(
                {"node": b, "type": "main", "index": 0})
        for r in roots:
            connect("Start", r)
        for t in wf.tasks.values():
            for dep in t.depends_on:
                connect(dep, t.name)
        doc = {"name": wf.name, "nodes": nodes, "connections": conns,
               "active": False, "settings": {}, "meta": {"generatedBy": "VIA_WorkflowEngine v%s" % __version__}}
        return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"

    @classmethod
    def to_mermaid(cls, wf: WorkflowSpec) -> str:
        L = ["flowchart LR"]
        safe = lambda n: re.sub(r"\W+", "_", n)
        for n, t in wf.tasks.items():
            L.append('    %s["%s"]' % (safe(n), n))
        for t in wf.tasks.values():
            for dep in t.depends_on:
                L.append("    %s --> %s" % (safe(dep), safe(t.name)))
        roots = [n for n, t in wf.tasks.items() if not t.depends_on]
        if roots:
            L.insert(1, "    __start__((start))")
            for r in roots:
                L.append("    __start__ --> %s" % safe(r))
        return "\n".join(L) + "\n"

    # -- Viewflow（Django flow class codegen）-------------------------------
    @classmethod
    def to_viewflow_py(cls, wf: WorkflowSpec) -> str:
        cls_name = "".join(w.capitalize() for w in re.split(r"\W+", wf.name) if w) or "ViaFlow"
        order = wf.topological_order()
        L = ['# -*- coding: utf-8 -*-',
             '"""Viewflow flow — generated by VIA_WorkflowEngine v%s（需 django + viewflow）"""' % __version__,
             "from viewflow import this",
             "from viewflow.workflow import flow", ""]
        for i, n in enumerate(order):
            L.append("def do_%s(activation):" % re.sub(r"\W+", "_", n).lower())
            L.append("    %r  # TODO: 業務邏輯" % ("step: %s" % n))
            L.append("")
        L.append("class %sFlow(flow.Flow):" % cls_name)
        for i, n in enumerate(order):
            fn_name = re.sub(r"\W+", "_", n).lower()
            nxt = ("this.%s" % re.sub(r"\W+", "_", order[i + 1]).lower()) if i + 1 < len(order) else "this.end"
            head = "flow.Start" if i == 0 else "flow.Function"
            L.append("    %s = %s(do_%s).Next(%s)" % (fn_name, head, fn_name, nxt))
        L.append("    end = flow.End()")
        return "\n".join(L) + "\n"

    @classmethod
    def export(cls, wf: WorkflowSpec, fmt: str) -> str:
        fmt = fmt.lower()
        table = {"dagu": cls.to_dagu_yaml, "kestra": cls.to_kestra_yaml,
                 "argo": cls.to_argo_yaml, "conductor": cls.to_conductor_json,
                 "airflow": cls.to_airflow_py, "temporal": cls.to_temporal_py,
                 "bpmn": cls.to_bpmn_xml, "reactflow": cls.to_reactflow_json,
                 "x6": cls.to_x6_json, "n8n": cls.to_n8n_json,
                 "mermaid": cls.to_mermaid, "viewflow": cls.to_viewflow_py}
        if fmt not in table:
            raise ValueError("未知格式 %r（可用：%s）" % (fmt, ", ".join(cls.FORMATS)))
        return table[fmt](wf)

# ============================================================================
# §12 部署鷹架（scaffold）— 獨立 UI 部署型引擎的本地 docker-compose
#     （Activepieces / n8n / Temporal dev / Kestra — 全免費本地方案）
# ============================================================================

SCAFFOLDS: Dict[str, Dict[str, str]] = {
    "activepieces": {
        "file": "docker-compose.activepieces.yml",
        "note": "啟動：docker compose -f docker-compose.activepieces.yml up -d → http://localhost:8080\n"
                "⚠ 請先更換 AP_ENCRYPTION_KEY / AP_JWT_SECRET / POSTGRES_PASSWORD",
        "content": """# Activepieces (MIT) — generated by VIA_WorkflowEngine
services:
  activepieces:
    image: activepieces/activepieces:latest
    restart: unless-stopped
    ports: ["8080:80"]
    environment:
      AP_ENVIRONMENT: production
      AP_ENCRYPTION_KEY: CHANGE_ME_32_hex_chars_____________
      AP_JWT_SECRET: CHANGE_ME_random_secret____________
      AP_POSTGRES_DATABASE: activepieces
      AP_POSTGRES_USER: postgres
      AP_POSTGRES_PASSWORD: CHANGE_ME_pg_password
      AP_POSTGRES_HOST: postgres
    depends_on:
      postgres: {condition: service_healthy}
  postgres:
    image: postgres:15
    restart: unless-stopped
    environment:
      POSTGRES_DB: activepieces
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: CHANGE_ME_pg_password
    volumes: [ap_pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d activepieces"]
      interval: 5s
      timeout: 5s
      retries: 5
volumes:
  ap_pgdata:
""",
    },
    "n8n": {
        "file": "docker-compose.n8n.yml",
        "note": "啟動：docker compose -f docker-compose.n8n.yml up -d → http://localhost:5678",
        "content": """# n8n Community Edition — generated by VIA_WorkflowEngine
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n:latest
    restart: unless-stopped
    ports: ["5678:5678"]
    environment:
      GENERIC_TIMEZONE: Asia/Taipei
      N8N_DIAGNOSTICS_ENABLED: "false"
    volumes: [n8n_data:/home/node/.n8n]
volumes:
  n8n_data:
""",
    },
    "temporal": {
        "file": "docker-compose.temporal.yml",
        "note": "啟動：docker compose -f docker-compose.temporal.yml up -d → UI http://localhost:8233\n"
                "（或免 Docker：brew/scoop 安裝 temporal 後 `temporal server start-dev`）",
        "content": """# Temporal dev server (auto-setup, SQLite) — generated by VIA_WorkflowEngine
services:
  temporal:
    image: temporalio/server:latest
    restart: unless-stopped
    ports: ["7233:7233", "8233:8233"]
    command: ["temporal", "server", "start-dev", "--ip", "0.0.0.0", "--ui-port", "8233"]
    volumes: [temporal_data:/root/.config/temporalio]
volumes:
  temporal_data:
""",
    },
    "kestra": {
        "file": "docker-compose.kestra.yml",
        "note": "啟動：docker compose -f docker-compose.kestra.yml up -d → http://localhost:8081",
        "content": """# Kestra (standalone, local storage) — generated by VIA_WorkflowEngine
services:
  kestra:
    image: kestra/kestra:latest
    restart: unless-stopped
    user: "root"
    command: server local
    ports: ["8081:8080"]
    environment:
      KESTRA_CONFIGURATION: |
        kestra:
          repository: {type: memory}
          queue: {type: memory}
          storage: {type: local, local: {basePath: /app/storage}}
    volumes: [kestra_data:/app/storage]
volumes:
  kestra_data:
""",
    },
}


def scaffold(target: str, out_dir: Union[str, Path] = ".") -> Path:
    """寫出目標引擎的 docker-compose 檔；回傳路徑。已存在則誠實 FAIL（不覆蓋）。"""
    if target not in SCAFFOLDS:
        raise ValueError("未知 scaffold 目標 %r（可用：%s）" % (target, ", ".join(SCAFFOLDS)))
    meta = SCAFFOLDS[target]
    out = Path(out_dir) / meta["file"]
    if out.exists():
        raise FileExistsError("已存在，拒絕覆蓋：%s" % out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(meta["content"], encoding="utf-8")
    LOG.info("📦 已產生 %s\n%s" % (out, meta["note"]))
    return out

# ============================================================================
# §13 轉接器（Backend Adapters）— 十庫在位即真用、缺席誠實回退原生引擎
# ============================================================================

class BackendAdapter:
    """轉接器基類。available() 純探測不 import 主體；run() 缺席時回退原生。"""

    key = "native"
    package: Optional[str] = None
    paradigm = "built-in zero-dependency engine"

    def available(self) -> bool:
        if not self.package:
            return True
        try:
            return importlib.util.find_spec(self.package) is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            return False

    def run(self, wf: WorkflowSpec, params: Optional[Dict[str, Any]] = None) -> WorkflowRun:
        return LocalDAGEngine().run(wf, params)

    def _fallback(self, wf: WorkflowSpec, params: Optional[Dict[str, Any]], reason: str) -> WorkflowRun:
        LOG.info("↪ [%s] %s — 回退本地原生引擎" % (self.key, reason))
        run = LocalDAGEngine().run(wf, params)
        run.event("fallback", "%s: %s" % (self.key, reason))
        return run


class NativeAdapter(BackendAdapter):
    key = "native"


class PrefectAdapter(BackendAdapter):
    key, package, paradigm = "prefect", "prefect", LIB_CATALOG["prefect"]["paradigm"]

    def run(self, wf: WorkflowSpec, params: Optional[Dict[str, Any]] = None) -> WorkflowRun:
        if not self.available():
            return self._fallback(wf, params, "prefect 未安裝（pip install prefect）")
        from prefect import flow as p_flow, task as p_task  # 動態組 flow：任務照拓撲序執行
        engine_self = self
        run = WorkflowRun(wf.name, _new_run_id(wf.name), dict(params or {}))
        ctx = WorkflowContext(wf, run.params, run.run_id)
        ctx.results = run.results

        def make_task(spec: TaskSpec):
            @p_task(name=spec.name, retries=spec.retries, retry_delay_seconds=spec.retry_delay)
            def _t():
                return LocalDAGEngine(quiet=True)._invoke(spec, ctx)
            return _t

        tasks = {n: make_task(t) for n, t in wf.tasks.items()}

        @p_flow(name=wf.name)
        def _f():
            futures: Dict[str, Any] = {}
            for n in wf.topological_order():
                spec = wf.tasks[n]
                if not _eval_condition(spec.condition, ctx):
                    run.results[n] = TaskResult(name=n, status=SKIPPED, error="condition=False")
                    continue
                out = tasks[n]()
                tr = TaskResult(name=n, status=SUCCESS, output=out,
                                started=_utcnow(), ended=_utcnow(), attempts=1)
                run.results[n] = tr
                ctx.results[n] = tr
            return True

        try:
            _f()
            run.status = SUCCESS
        except Exception as e:
            run.status = FAILED
            run.event("error", str(e))
        run.ended = _utcnow()
        run.event("backend", "executed via prefect %s" % engine_self.key)
        return run


class TransitionsAdapter(BackendAdapter):
    key, package, paradigm = "transitions", "transitions", LIB_CATALOG["transitions"]["paradigm"]

    def build_machine(self, model: Any, states: Sequence[str], transitions: Sequence[Dict],
                      initial: str) -> Any:
        """transitions 在位 → 官方 Machine；缺席 → 原生 StateMachine（同 API 子集）。"""
        if self.available():
            from transitions import Machine
            return Machine(model=model, states=list(states),
                           transitions=[dict(t) for t in transitions], initial=initial)
        return StateMachine(model=model, states=states, transitions=transitions, initial=initial)


class SpiffAdapter(BackendAdapter):
    key, package, paradigm = "spiff", "SpiffWorkflow", LIB_CATALOG["spiff"]["paradigm"]

    def run(self, wf: WorkflowSpec, params: Optional[Dict[str, Any]] = None) -> WorkflowRun:
        # BPMN XML 由 Exporters 供應；SpiffWorkflow 各版 API 落差大 → 一律以
        # 原生引擎執行、附掛可攜 BPMN 供 Spiff/bpmn-js 使用（誠實整合）。
        run = (LocalDAGEngine().run(wf, params) if not self.available()
               else self._fallback(wf, params, "以原生引擎執行；BPMN XML 已可由 export bpmn 取得"))
        run.state["bpmn_available"] = True
        return run


class LangGraphAdapter(BackendAdapter):
    key, package, paradigm = "langgraph", "langgraph", LIB_CATALOG["langgraph"]["paradigm"]

    def build_graph(self, name: str = "graph") -> Any:
        """langgraph 在位 → 官方 StateGraph（dict schema）；缺席 → 原生 StateGraph。"""
        if self.available():
            from langgraph.graph import StateGraph as LGStateGraph
            return LGStateGraph(dict)
        return StateGraph(name)


class CrewAIAdapter(BackendAdapter):
    key, package, paradigm = "crewai", "crewai", LIB_CATALOG["crewai"]["paradigm"]

    def build_crew(self, agents: Sequence[Agent], tasks: Sequence[CrewTask],
                   process: str = "sequential") -> Any:
        """crewai 在位 → 官方 Crew（需自備 LLM 金鑰）；缺席 → 原生 Crew。"""
        if self.available():
            import crewai
            c_agents = {id(a): crewai.Agent(role=a.role, goal=a.goal,
                                            backstory=a.backstory or a.goal) for a in agents}
            c_tasks = [crewai.Task(description=t.description,
                                   expected_output=t.expected_output or "result",
                                   agent=c_agents[id(t.agent)]) for t in tasks]
            return crewai.Crew(agents=list(c_agents.values()), tasks=c_tasks)
        return Crew(agents, tasks, process=process)


class LlamaIndexAdapter(BackendAdapter):
    key, package, paradigm = "llamaindex", "llama_index", LIB_CATALOG["llamaindex"]["paradigm"]
    # 事件驅動典範由原生 EventWorkflow 全功能提供；llama_index 在位時可直接
    # 改用其 workflow 模組 — 本轉接器提供探測與說明。


class TemporalAdapter(BackendAdapter):
    key, package, paradigm = "temporal", "temporalio", LIB_CATALOG["temporal"]["paradigm"]

    def run(self, wf: WorkflowSpec, params: Optional[Dict[str, Any]] = None) -> WorkflowRun:
        # 真 Temporal 需要 server（scaffold temporal + export temporal 產 worker 碼）。
        # 本地立即可用的耐用執行 = 原生引擎 checkpoint/resume。
        return self._fallback(wf, params,
                              "Temporal 需外部 server（見 scaffold temporal / export temporal）；"
                              "本地耐用執行以 checkpoint+resume 提供")


class AirflowAdapter(BackendAdapter):
    key, package, paradigm = "airflow", "airflow", LIB_CATALOG["airflow"]["paradigm"]

    def run(self, wf: WorkflowSpec, params: Optional[Dict[str, Any]] = None) -> WorkflowRun:
        return self._fallback(wf, params,
                              "Airflow 為伺服器型（export airflow 產 DAG 檔置入 dags/）")


class KestraAdapter(BackendAdapter):
    key, package, paradigm = "kestra", "kestra", LIB_CATALOG["kestra"]["paradigm"]

    def run(self, wf: WorkflowSpec, params: Optional[Dict[str, Any]] = None) -> WorkflowRun:
        return self._fallback(wf, params,
                              "Kestra 為伺服器型（scaffold kestra + export kestra 產 flow YAML）")


class ViewflowAdapter(BackendAdapter):
    key, package, paradigm = "viewflow", "viewflow", LIB_CATALOG["viewflow"]["paradigm"]

    def run(self, wf: WorkflowSpec, params: Optional[Dict[str, Any]] = None) -> WorkflowRun:
        return self._fallback(wf, params,
                              "Viewflow 綁定 Django 專案（export viewflow 產 flow class）")


ADAPTERS: "OrderedDict[str, BackendAdapter]" = OrderedDict(
    (a.key, a) for a in [
        NativeAdapter(), PrefectAdapter(), AirflowAdapter(), KestraAdapter(),
        SpiffAdapter(), TransitionsAdapter(), ViewflowAdapter(),
        LangGraphAdapter(), CrewAIAdapter(), LlamaIndexAdapter(), TemporalAdapter(),
    ])

# ============================================================================
# §14 統一門面（Facade）— VIAWorkflowEngine
# ============================================================================

class VIAWorkflowEngine:
    """單一入口：建流程、選後端執行、匯出、排程、狀態機/圖/事件/Crew 工廠。"""

    def __init__(self, run_dir: Union[str, Path] = _DEF_RUN_DIR, quiet: bool = False):
        self.store = RunStore(run_dir)
        self.dag = LocalDAGEngine(self.store, quiet=quiet)
        self.scheduler = Scheduler(quiet=quiet)

    # 工廠
    def workflow(self, name: str, **kw) -> WorkflowSpec:
        return WorkflowSpec(name, **kw)

    def state_machine(self, **kw) -> StateMachine:
        return TransitionsAdapter().build_machine(**kw) if kw.get("prefer_lib") else StateMachine(
            **{k: v for k, v in kw.items() if k != "prefer_lib"})

    def state_graph(self, name: str = "graph") -> StateGraph:
        return StateGraph(name)

    def crew(self, agents: Sequence[Agent], tasks: Sequence[CrewTask], **kw) -> Crew:
        return Crew(agents, tasks, **kw)

    # 執行
    def run(self, wf: Union[WorkflowSpec, str, Path], params: Optional[Dict[str, Any]] = None,
            backend: str = "auto") -> WorkflowRun:
        if not isinstance(wf, WorkflowSpec):
            wf = load_workflow_file(wf)
        if backend == "auto":
            backend = "native"  # 明確、可預測：auto = 原生（各庫在位仍可指名）
        if backend == "native":
            return self.dag.run(wf, params)
        if backend not in ADAPTERS:
            raise ValueError("未知 backend %r（可用：%s）" % (backend, ", ".join(ADAPTERS)))
        return ADAPTERS[backend].run(wf, params)

    def resume(self, wf: Union[WorkflowSpec, str, Path], run_id: str) -> WorkflowRun:
        if not isinstance(wf, WorkflowSpec):
            wf = load_workflow_file(wf)
        return self.dag.resume(wf, run_id)

    def export(self, wf: Union[WorkflowSpec, str, Path], fmt: str) -> str:
        if not isinstance(wf, WorkflowSpec):
            wf = load_workflow_file(wf)
        return Exporters.export(wf, fmt)

    # 探測
    @staticmethod
    def backends_report() -> List[Dict[str, str]]:
        rows = []
        for key, meta in LIB_CATALOG.items():
            ad = ADAPTERS.get(key)
            installed = ad.available() if ad else importlib.util.find_spec(meta["package"]) is not None
            rows.append({"backend": key, "package": meta["package"], "tier": meta["tier"],
                         "paradigm": meta["paradigm"],
                         "status": "installed" if installed else "fallback→native"})
        rows.append({"backend": "native", "package": "(stdlib)", "tier": "Built-in",
                     "paradigm": NativeAdapter.paradigm, "status": "always available"})
        return rows

# ============================================================================
# §15 示範（demos）— 每典範一例；selftest 以此為驗證基底
# ============================================================================

def _demo_wf(fail_on: Optional[str] = None, flaky_fails: int = 0) -> WorkflowSpec:
    """示範 ETL DAG：extract → (clean_a ∥ clean_b) → merge → load。"""
    attempts = {"n": 0}

    def extract(ctx):
        return list(range(1, 6))

    def clean_a(ctx):
        return [x * 10 for x in ctx.output_of("extract")]

    def clean_b(ctx):
        attempts["n"] += 1
        if attempts["n"] <= flaky_fails:
            raise RuntimeError("flaky 模擬失敗 #%d" % attempts["n"])
        return [x + 1 for x in ctx.output_of("extract")]

    def merge(ctx):
        if fail_on == "merge":
            raise RuntimeError("merge 模擬失敗")
        return sorted(ctx.output_of("clean_a") + ctx.output_of("clean_b"))

    def load(ctx):
        ctx.set("loaded", len(ctx.output_of("merge")))
        return "loaded %d rows" % len(ctx.output_of("merge"))

    def unload(ctx):  # load 的 saga 補償
        ctx.set("loaded", 0)
        return "rolled back"

    wf = WorkflowSpec("demo_etl", description="示範 ETL", max_parallel=4, on_failure="compensate")
    wf.task("extract", extract)
    wf.task("clean_a", clean_a, depends_on=["extract"])
    wf.task("clean_b", clean_b, depends_on=["extract"], retries=3, retry_delay=0.05, backoff=1.0)
    wf.task("merge", merge, depends_on=["clean_a", "clean_b"])
    wf.task("load", load, depends_on=["merge"], compensate=unload)
    return wf


def demo_dag() -> WorkflowRun:
    """平行 DAG + 重試（clean_b 前兩次故意失敗，重試後成功）。"""
    run = LocalDAGEngine().run(_demo_wf(flaky_fails=2), persist=False)
    assert run.ok and run.results["clean_b"].attempts == 3
    return run

def demo_saga() -> WorkflowRun:
    """saga 補償：merge 失敗 → 已完成任務反序補償（本例 load 未跑，僅示範策略）。"""
    wf = _demo_wf(fail_on="merge")

    def audit(ctx):
        return "audited"

    def unaudit(ctx):
        return "audit rolled back"
    wf.tasks["extract"].compensate = unaudit  # 讓補償實際發生在已完成的 extract
    run = LocalDAGEngine().run(wf, persist=False)
    assert not run.ok and run.results["extract"].status == COMPENSATED
    return run

def demo_resume() -> Tuple[WorkflowRun, WorkflowRun]:
    """耐用執行：首跑在 merge 失敗（模擬當機點）→ resume 續跑不重做 extract/clean。"""
    marker = {"fixed": False}
    wf = _demo_wf()
    orig_merge = wf.tasks["merge"].fn

    def crashy_merge(ctx):
        if not marker["fixed"]:
            raise RuntimeError("模擬當機（斷電）")
        return orig_merge(ctx)
    wf.tasks["merge"].fn = crashy_merge
    wf.on_failure = "halt"
    eng = LocalDAGEngine()
    first = eng.run(wf)
    assert not first.ok
    marker["fixed"] = True  # 「修好環境」後續跑
    second = eng.resume(wf, first.run_id)
    assert second.ok
    assert second.results["extract"].attempts == 1  # 由 checkpoint 還原，未重跑
    return first, second

def demo_fsm() -> StateMachine:
    """Transitions 典範：訂單狀態機（含 after 回調與 guard）。"""
    class Order:
        def __init__(self):
            self.paid_amount = 0

        def on_paid(self):
            LOG.info("【通知】收到付款！通知倉儲出貨…")

        def has_money(self):
            return self.paid_amount > 0

    order = Order()
    m = StateMachine(model=order, states=["新訂單", "已付款", "已出貨", "已關閉"],
                     transitions=[
                         {"trigger": "收到款項", "source": "新訂單", "dest": "已付款",
                          "conditions": ["has_money"], "after": "on_paid"},
                         {"trigger": "商品寄出", "source": "已付款", "dest": "已出貨"},
                         {"trigger": "客戶簽收", "source": "已出貨", "dest": "已關閉"},
                         {"trigger": "取消", "source": "*", "dest": "已關閉"},
                     ], initial="新訂單")
    assert m.trigger("收到款項") is False  # guard 擋下（未付款）
    order.paid_amount = 100
    assert m.trigger("收到款項") and m.state == "已付款"
    m.trigger("商品寄出")
    m.trigger("客戶簽收")
    assert m.state == "已關閉" and len(m.history) == 3
    return m

def demo_graph() -> Dict:
    """LangGraph 典範：draft → review →（不合格→revise→review 循環）→ publish。"""
    g = StateGraph("writer")
    g.add_node("draft", lambda s: {"text": "v1", "quality": 1})
    g.add_node("review", lambda s: {"approved": s["quality"] >= 3})
    g.add_node("revise", lambda s: {"text": s["text"] + "+", "quality": s["quality"] + 1})
    g.add_node("publish", lambda s: {"published": True})
    g.set_entry("draft")
    g.add_edge("draft", "review")
    g.add_conditional_edges("review", lambda s: "ok" if s["approved"] else "again",
                            {"ok": "publish", "again": "revise"})
    g.add_edge("revise", "review")
    out = g.compile(max_steps=50).invoke({})
    assert out["published"] and out["quality"] == 3
    assert sum(1 for t in out["__trace__"] if t["node"] == "review") == 3  # 走了回頭路
    return out

def demo_events() -> Any:
    """LlamaIndex Workflows 典範：事件驅動 RAG 形流程。"""
    class Retrieved(Event):
        pass

    class Ranked(Event):
        pass

    class Rag(EventWorkflow):
        @step(StartEvent)
        def retrieve(self, ev):
            docs = ["doc-%s-%d" % (ev.query, i) for i in range(3)]
            return Retrieved(docs=docs, query=ev.query)

        @step(Retrieved)
        def rank(self, ev):
            return Ranked(top=sorted(ev.docs)[:2], query=ev.query)

        @step(Ranked)
        def answer(self, ev):
            return StopEvent(result={"query": ev.query, "sources": ev.top})

    out = Rag().run(query="movies")
    assert out["sources"] == ["doc-movies-0", "doc-movies-1"]
    return out

def demo_crew() -> Dict[str, Any]:
    """CrewAI 典範：分析師 → 撰稿人（sequential，工具 + 本地確定性合成）。"""
    analyst = Agent(role="資深資料分析師", goal="整理資料重點",
                    tools={"count_rows": lambda inp: len(inp.get("rows", []))})
    writer = Agent(role="文案編輯", goal="輸出一句話摘要")
    t1 = CrewTask(description="分析輸入 rows 並列出統計", agent=analyst, name="analyze")
    t2 = CrewTask(description="根據分析寫摘要", agent=writer, name="summarize", context=[t1])
    out = Crew([analyst, writer], [t1, t2], process="sequential").kickoff(
        inputs={"rows": [1, 2, 3, 4]})
    assert "tool[count_rows] → 4" in out["tasks"][0]["output"]
    assert out["tasks"][1]["output"]  # writer 收到 context
    return out

def demo_decorators() -> Any:
    """Prefect 典範：@via_task（重試）+ @via_flow（run 紀錄）。"""
    state = {"n": 0}

    @via_task(retries=3, retry_delay=0.02, backoff=1.0)
    def extract():
        state["n"] += 1
        if state["n"] <= 2:
            raise RuntimeError("flaky extract")
        return [1, 2, 3, 4, 5]

    @via_task
    def transform(data):
        return [x * 10 for x in data]

    @via_flow(name="demo_decorator_etl")
    def etl():
        return transform(extract())

    out = etl()
    run = etl.last_run
    assert out == [10, 20, 30, 40, 50] and run.ok
    assert run.results["extract"].attempts == 3
    return out

def demo_cron() -> List[Dict[str, Any]]:
    """cron 解析 + 排程器（run_pending 注入時刻驗證，不真等時間）。"""
    c = Cron("0 1 * * *")
    nxt = c.next_after(datetime(2026, 8, 10, 0, 30))
    assert nxt == datetime(2026, 8, 10, 1, 0)
    assert Cron("*/15 9-17 * * 1-5").matches(datetime(2026, 8, 10, 9, 45))  # 週一
    fired = {"n": 0}
    s = Scheduler(quiet=True)
    s.add("beat", "*/5 * * * *", lambda: fired.__setitem__("n", fired["n"] + 1))
    assert s.run_pending(datetime(2026, 8, 10, 1, 5)) == ["beat"]
    assert s.run_pending(datetime(2026, 8, 10, 1, 5)) == []  # 同分鐘不重複
    assert fired["n"] == 1
    return s.table()

def demo_dsl(tmp_dir: Optional[Path] = None) -> WorkflowRun:
    """宣告式 DSL：YAML（在位）或 JSON 定義 → 載入執行（shell 任務）。"""
    tmp = tmp_dir or Path(os.environ.get("TMPDIR", "/tmp"))
    doc = {"name": "dsl_demo", "max_parallel": 2, "steps": [
        {"name": "prepare", "command": "echo prepare-ok"},
        {"name": "work_a", "command": "echo A", "depends_on": ["prepare"]},
        {"name": "work_b", "command": "echo B", "depends_on": ["prepare"],
         "retry": {"limit": 2, "interval": 0}},
        {"name": "finish", "command": "echo done", "depends_on": ["work_a", "work_b"],
         "condition": "outputs['work_a']['exit'] == 0"},
    ]}
    if _yaml is not None:
        p = tmp / "via_dsl_demo.yaml"
        p.write_text(_yaml.safe_dump(doc, allow_unicode=True), encoding="utf-8")
    else:
        p = tmp / "via_dsl_demo.json"
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    run = LocalDAGEngine().run(load_workflow_file(p), persist=False)
    assert run.ok and run.results["finish"].output["stdout"] == "done"
    return run

def demo_export() -> Dict[str, int]:
    """全部 12 種匯出格式跑一輪，驗證非空 + JSON/XML 可解析。"""
    wf = _demo_wf()
    sizes: Dict[str, int] = {}
    for fmt in Exporters.FORMATS:
        text = Exporters.export(wf, fmt)
        assert text.strip(), "匯出 %s 為空" % fmt
        if fmt in ("conductor", "reactflow", "x6", "n8n"):
            json.loads(text)
        if fmt == "bpmn":
            import xml.dom.minidom
            xml.dom.minidom.parseString(text)
        if _yaml is not None and fmt in ("dagu", "kestra", "argo"):
            _yaml.safe_load(text)
        sizes[fmt] = len(text)
    return sizes


DEMOS: "OrderedDict[str, Callable[[], Any]]" = OrderedDict([
    ("dag", demo_dag), ("saga", demo_saga), ("resume", demo_resume),
    ("fsm", demo_fsm), ("graph", demo_graph), ("events", demo_events),
    ("crew", demo_crew), ("decorators", demo_decorators), ("cron", demo_cron),
    ("dsl", demo_dsl), ("export", demo_export),
])


def selftest() -> int:
    """全功能自我驗證：每典範 demo 內含 assert；PASS/FAIL 摘要 + exit code。"""
    results: List[Tuple[str, str, str]] = []
    for name, fn in DEMOS.items():
        try:
            fn()
            results.append((name, "PASS", ""))
        except Exception as e:
            results.append((name, "FAIL", "%s: %s" % (type(e).__name__, e)))
            LOG.error(traceback.format_exc())
    width = max(len(n) for n, _, _ in results)
    print("\n" + "=" * 64)
    print("VIA_WorkflowEngine v%s selftest（%d 項）" % (__version__, len(results)))
    print("=" * 64)
    for name, status, err in results:
        print("  %-*s  %s%s" % (width, name, status, ("  ← " + err) if err else ""))
    fails = sum(1 for _, s, _ in results if s == "FAIL")
    print("-" * 64)
    print("  合計：%d PASS / %d FAIL" % (len(results) - fails, fails))
    return 1 if fails else 0

# ============================================================================
# §16 CLI
# ============================================================================

def _parse_params(pairs: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit("--param 需為 key=value，得到 %r" % pair)
        k, v = pair.split("=", 1)
        try:
            out[k] = json.loads(v)
        except json.JSONDecodeError:
            out[k] = v
    return out


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="VIA_WorkflowEngine",
        description="VIA 統一工作流引擎 v%s — 十庫典範整合（native core + adapters）" % __version__)
    sub = ap.add_subparsers(dest="verb")

    sub.add_parser("backends", help="十庫在位探測報告")

    d = sub.add_parser("demo", help="執行典範示範")
    d.add_argument("which", nargs="?", default="all",
                   choices=["all"] + list(DEMOS), help="示範名（預設 all）")

    r = sub.add_parser("run", help="執行 YAML/JSON 工作流檔")
    r.add_argument("file")
    r.add_argument("--backend", default="auto",
                   choices=["auto"] + list(ADAPTERS), help="執行後端（預設 auto=native）")
    r.add_argument("--param", action="append", default=[], help="key=value（可多次）")
    r.add_argument("--no-persist", action="store_true", help="不落 checkpoint")

    rs = sub.add_parser("resume", help="斷點續跑既有 run")
    rs.add_argument("file")
    rs.add_argument("run_id")

    e = sub.add_parser("export", help="匯出為其他引擎/前端格式")
    e.add_argument("file")
    e.add_argument("--format", required=True, choices=Exporters.FORMATS)
    e.add_argument("-o", "--out", default=None, help="輸出檔（預設 stdout）")

    sc = sub.add_parser("scaffold", help="產生本地部署 docker-compose")
    sc.add_argument("target", choices=sorted(SCAFFOLDS))
    sc.add_argument("-o", "--out", default=".", help="輸出目錄（預設當前目錄）")

    ls = sub.add_parser("runs", help="列出 .via_runs/ 執行紀錄")
    ls.add_argument("--dir", default=str(_DEF_RUN_DIR))

    sub.add_parser("selftest", help="全功能自我驗證")

    args = ap.parse_args(argv)
    if not args.verb:
        ap.print_help()
        return 0

    if args.verb == "backends":
        rows = VIAWorkflowEngine.backends_report()
        w1 = max(len(r["backend"]) for r in rows)
        w2 = max(len(r["package"]) for r in rows)
        w3 = max(len(r["status"]) for r in rows)
        print("VIA_WorkflowEngine v%s — backend 在位探測" % __version__)
        for r in rows:
            print("  %-*s  %-*s  %-*s  %s（%s）"
                  % (w1, r["backend"], w2, r["package"], w3, r["status"], r["paradigm"], r["tier"]))
        return 0

    if args.verb == "demo":
        names = list(DEMOS) if args.which == "all" else [args.which]
        for n in names:
            print("\n──── demo:%s ────" % n)
            DEMOS[n]()
        print("\n全部 %d 個示範完成。" % len(names))
        return 0

    if args.verb == "run":
        eng = VIAWorkflowEngine()
        wf = load_workflow_file(args.file)
        if args.backend in ("auto", "native") and args.no_persist:
            run = eng.dag.run(wf, _parse_params(args.param), persist=False)
        else:
            run = eng.run(wf, _parse_params(args.param), backend=args.backend)
        print(json.dumps(run.to_dict(), ensure_ascii=False, indent=2))
        return 0 if run.ok else 1

    if args.verb == "resume":
        eng = VIAWorkflowEngine()
        run = eng.resume(args.file, args.run_id)
        print(json.dumps(run.to_dict(), ensure_ascii=False, indent=2))
        return 0 if run.ok else 1

    if args.verb == "export":
        text = Exporters.export(load_workflow_file(args.file), args.format)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
            print("已寫出 %s（%d bytes）" % (args.out, len(text)))
        else:
            print(text)
        return 0

    if args.verb == "scaffold":
        scaffold(args.target, args.out)
        return 0

    if args.verb == "runs":
        for row in RunStore(args.dir).list_runs():
            print(json.dumps(row, ensure_ascii=False))
        return 0

    if args.verb == "selftest":
        return selftest()
    return 0


if __name__ == "__main__":
    sys.exit(main())
