#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""CGC_MDL280_VCGCAgentOSHub v0100 — VCGC 的 Agent OS + Graphify 整合樞紐(一個系統裡的一扇門)。

操作員 2026-11-12:「把 Agent OS 的全部功能併進 VCGC 成為一個系統;登錄它的助手 · SSOT · regex · 同義字 · 其他 27 個工具;
Graphify 也併進 VCGC;全部啟用跑起來。四系統(VRN-1 · VRN-2 · VDF · VCGC)獨立、互不干涉、功能互相支援」。
VCGC 的角色(L123 · 本令):幫別人裝環境 / 套件、偵測 SSOT 邏輯 / 格式衝突與環境 / 套件衝突、AI 處理後發新 SSOT 號讓各系統自己更新。
本支只做 VCGC 自己的事(Agent OS 在 supportive modules/agent_os,是 VCGC 的支援模組;Graphify 是 VCGC 的程式碼圖工具):
  inventory           靜態盤點(不執行):Agent OS 尾版的 8 個 Skill · 9 個 MCP 工具 · SuperPrompt v2.0 的 10 個 slash 技能
                      (= 27 個工具;AI 解讀「其他 27 個工具」= 8 + 9 + 10,倉內沒有另一份 27 項清單)· 14 個 CLI 動詞 · 4 個內建模組 ·
                      5 條遮罩正則 · MCP 工具 ↔ CLI 動詞同義對照 · Graphify 狀態。
  register [--apply]  寫 VCGC 整合冊 VIA_VCGC_AgentOS_Integration_SSOT_v####(每項穩定 ID:AOS-SKL / AOS-MCP / AOS-SLS / AOS-VRB / AOS-MOD / AOS-RGX / AOS-SYN);
                      中央正則 · 同義字冊 VIA_Central_Synonym_Regex 出下一版(只增:原有條目一字不動,補 AOS_* 正則與同義字)。不帶 --apply = 只列計畫。
  activate [--out D]  逐項真跑:Agent OS selftest · 14 動詞(會寫檔的 dashboard 只由 selftest 驗)· 8 Skill 逐一 skills run ·
                      MCP stdio 真握手(server/discover → tools/list → 9 個工具逐一 tools/call)· 10 個 slash 技能 chain 計畫 ·
                      中央冊正則全數可編譯 + AOS 條目在 · Graphify 偵測 / 小樣跑圖 → 矩陣 JSON / CSV / HTML(VIA_Reports/vcgc/agentos)。
  graphify status|run [--system S|--path P] [--out D]
                      Graphify 在隔離環境跑(找 VIA_GRAPHIFY_PY → ~/envs/via_graphify → PATH 的 graphify);code-only · GRAPHIFY_BACKEND=none ·
                      一個系統一張圖(VRN / VRN_Shared / VDF / VCGC / VQG / AOS)。沒裝 → ABSENT + 安裝路徑(InstallGate 不裝它:相依約 30 個
                      tree-sitter 會撞引擎環境;第一次下載要操作員開 VIA_NET_CONSENT,本支不代設)。
邊界:不改 Agent OS / Graphify / 他系統檔;只寫自己的冊(--apply)與 VIA_Reports/vcgc/agentos;零網路([VIA:NET-BRIDGE] 留名:本支不出網);
不用 TA-Lib;不讀寫同意閘;Agent OS 一律子行程跑(不 import 進 VCGC 行程)。
rc:0 綠 · 1 紅 · 2 黃 / 沒量 · 3 缺件。用法:python CGC_MDL280_VCGCAgentOSHub_v0100.py <verb> … · --selftest
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

import ast
import copy
import csv
import hashlib
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
TAG = "CGC_MDL280_VCGCAgentOSHub " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
AOS_DIR = VIA / "supportive modules" / "agent_os"
SKX_DIR = VIA / "docs" / "handoff" / "ai"
REG_STEM = "VIA_VCGC_AgentOS_Integration_SSOT"
CENTRAL_STEM = "VIA_Central_Synonym_Regex"
OUT_DEFAULT = VIA / "VIA_Reports" / "vcgc" / "agentos"
RC = {"GREEN": 0, "RED": 1, "YELLOW": 2, "NODATA": 2, "ABSENT": 3}
MCP_TO_VERB = {"via.integration.status": "status", "via.skills.list": "skills list", "via.skill.run": "skills run",
               "via.token.prepare": "context", "via.policy.authorize": "policy", "via.sdd.validate": "sdd validate",
               "via.vcgc.status": "vcgc-status", "via.repo.sync": "repo-check"}
GRAPHIFY_SYSTEMS = {"VRN": "functional modules/VRN2", "VRN_Shared": "functional modules/VRN", "VDF": "functional modules/VDF",
                    "VCGC": "supportive modules/registry", "VQG": "functional modules/VQG", "AOS": "supportive modules/agent_os"}
GRAPHIFY_EXCLUDES = ["references/", "intake/", "_quarantine*/", "*quarantine*/", "VIA_RetiredEngines/", "backup*/", "archive*/"]
GRAPHIFY_VERSION = "0.9.100"


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _tail(d: Path, stem: str, ext: str = ".py"):
    hits = [p for p in d.glob(stem + "_v*" + ext) if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p and p.is_file() else ""


def _rel(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(VIA))
    except ValueError:
        return str(p)


# ── ① 靜態盤點(只讀 · 不執行 Agent OS)──────────────────────────────────────
def _slash_index() -> dict:
    """SuperPrompt v2.0 的 slash 技能:載 SkillExport 尾版(倉內資料模組,不出網不寫檔)取 SLASH_INDEX。"""
    p = _tail(SKX_DIR, "VIA_SkillExport")
    if p is None:
        return {}
    spec = importlib.util.spec_from_file_location("vcgc_aos_skx_" + p.stem, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    try:
        spec.loader.exec_module(mod)
        return {k: {"name": (v or {}).get("name", k), "file": _rel(p)} for k, v in dict(mod.SLASH_INDEX).items()}
    except Exception:  # noqa: BLE001 — 載不到照實回空(盤點列 ABSENT)
        return {}


def inventory() -> dict:
    aos = _tail(AOS_DIR, "VIA_AgentOS")
    if aos is None:
        return {"lamp": "ABSENT", "why": "supportive modules/agent_os/VIA_AgentOS_v*.py 不在"}
    src = aos.read_text(encoding="utf-8")
    tree = ast.parse(src)
    skills = re.findall(r'SkillSpec\(\s*"([^"]+)",\s*"([^"]+)"', src)
    req = re.findall(r'SkillSpec\(\s*"([^"]+)",[\s\S]*?\),\s*(\("[a-z_]+"(?:,\s*"[a-z_]+")*,?\))', src)
    req_map = {k: re.findall(r'"([a-z_]+)"', v) for k, v in req}
    mcp = re.findall(r'_tool_schema\("([^"]+)",\s*"([^"]+)"', src)
    i = src.rfind('add_subparsers(dest="command"')
    verbs = list(dict.fromkeys(re.findall(r'(?<![\w])sub\.add_parser\("([^"]+)"', src[i:]))) if i >= 0 else []
    mods = re.findall(r'\{"id": "(VIA-MOD-[^"]+)", "name": "([^"]+)"[^}]*?"status": "([^"]+)"', src)
    regex = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, (ast.Tuple, ast.List)):
            pats = [a.args[0].value for a in node.value.elts if isinstance(a, ast.Call) and getattr(a.func, "attr", "") == "compile"
                    and a.args and isinstance(a.args[0], ast.Constant)]
            if len(pats) >= 3 and node.targets and isinstance(node.targets[0], ast.Name):
                regex += [(node.targets[0].id, p) for p in pats]
    slash = _slash_index()
    tools = ([{"id": "AOS-SKL-%03d" % n, "kind": "skill", "name": k, "title": t, "entry": "skills run " + k, "inputs": req_map.get(k, [])}
              for n, (k, t) in enumerate(skills, 1)]
             + [{"id": "AOS-MCP-%03d" % n, "kind": "mcp_tool", "name": k, "title": t, "entry": "mcp serve → tools/call " + k,
                 "cli_equivalent": MCP_TO_VERB.get(k, "")} for n, (k, t) in enumerate(mcp, 1)]
             + [{"id": "AOS-SLS-%03d" % n, "kind": "slash_skill", "name": k, "title": v["name"], "entry": "VIA_SkillExport chain " + k}
                for n, (k, v) in enumerate(sorted(slash.items()), 1)])
    syn = [{"id": "AOS-SYN-%03d" % n, "key": "AOS_TOOL_" + re.sub(r"\W", "_", k.split(".", 1)[1]).upper(), "aliases": [k, v, "agentos " + v]}
           for n, (k, v) in enumerate(sorted(MCP_TO_VERB.items()), 1)]
    return {"lamp": "GREEN", "agent_os": {"file": _rel(aos), "sha256": _sha(aos), "lines": src.count("\n") + 1},
            "skill_export": _rel(_tail(SKX_DIR, "VIA_SkillExport")) if _tail(SKX_DIR, "VIA_SkillExport") else "",
            "counts": {"skills": len(skills), "mcp_tools": len(mcp), "slash_skills": len(slash), "tools_total": len(tools),
                       "verbs": len(verbs), "modules": len(mods), "regex": len(regex), "synonyms": len(syn)},
            "tools": tools,
            "verbs": [{"id": "AOS-VRB-%03d" % n, "verb": v, "console": "via-vcgc agentos " + v} for n, v in enumerate(verbs, 1)],
            "modules": [{"id": "AOS-MOD-%03d" % n, "module_id": m, "name": nm, "status": st} for n, (m, nm, st) in enumerate(mods, 1)],
            "regex": [{"id": "AOS-RGX-%03d" % n, "key": "AOS_SECRET_MASK_%02d" % n, "var": var, "pattern": p} for n, (var, p) in enumerate(regex, 1)],
            "synonyms": syn, "graphify": graphify_status()}


# ── ② 登錄(VCGC 整合冊 + 中央正則 / 同義字冊下一版;只增)────────────────────────────
def _strip_volatile(d: dict) -> dict:
    x = copy.deepcopy(d)
    for k in ("version", "prior", "ts", "graphify"):
        x.pop(k, None)
    return x


def build_register(inv: dict) -> dict:
    return {"schema": "VIA.VCGC.AgentOSIntegration.v1", "version": "v0100", "prior": None, "ts": _utc(),
            "source": "操作員 2026-11-12:Agent OS 全功能併入 VCGC · 登錄助手 / SSOT / regex / 同義字 / 27 工具 · Graphify 併入 · 全啟用",
            "independence": "四系統(VRN-1 · VRN-2 · VDF · VCGC)對等獨立(L123);本冊是 VCGC 自己的冊,不改他系統;Agent OS / Graphify 是 VCGC 的支援工具",
            "interpretation_27": "27 = 8 Skill + 9 MCP 工具 + 10 slash 技能(AI 解讀;倉內沒有另一份 27 項清單,操作員可更正)",
            "agent_os": inv["agent_os"], "skill_export": inv["skill_export"], "counts": inv["counts"], "tools": inv["tools"],
            "verbs": inv["verbs"], "modules": inv["modules"], "regex": inv["regex"], "synonyms": inv["synonyms"],
            "console": {"entry": "via-vcgc agentos <verb> · via-vcgc graphify status|run", "hub": _rel(Path(__file__))},
            "graphify": {"systems": GRAPHIFY_SYSTEMS, "version": GRAPHIFY_VERSION, "mode": "code-only · GRAPHIFY_BACKEND=none · offline · isolated venv"}}


def central_next(inv: dict) -> tuple:
    """中央冊尾版 → (新冊 dict 或 None(已含全部 AOS 條目), 尾版路徑, 新增鍵)。原有條目一字不動。"""
    tail = _tail(HERE, CENTRAL_STEM, ".json")
    if tail is None:
        return None, None, []
    d = json.loads(tail.read_text(encoding="utf-8"))
    new = copy.deepcopy(d)
    added = []
    for r in inv["regex"]:
        if r["key"] not in new["regex"]:
            new["regex"][r["key"]] = {"pattern": r["pattern"], "owner": inv["agent_os"]["file"].rsplit("/", 1)[-1][:-3], "locked": False,
                                      "note": "Agent OS 憑證遮罩(%s;只遮罩不外送);VCGC 整合冊 %s 登錄" % (r["var"], r["id"])}
            added.append(r["key"])
    for s in inv["synonyms"]:
        if s["key"] not in new["synonyms"]:
            new["synonyms"][s["key"]] = s["aliases"]
            new.setdefault("synonyms_meta", {})[s["key"]] = {"namespace": "agentos_tool", "canonical": s["aliases"][0],
                                                            "source": "VIA_AgentOS MCP 工具 ↔ CLI 動詞(%s)" % s["id"], "grade": "M",
                                                            "batch": "操作員 2026-11-12 Agent OS 併入 VCGC"}
            added.append(s["key"])
    if not added:
        return None, tail, []
    nv = _vnum(tail) + 1
    new.update(version="v%04d" % nv, prior=tail.name, ts=_utc(), batch="Agent OS 併入 VCGC(操作員 2026-11-12):+%d AOS 條目(只增)" % len(added))
    return new, tail, added


def register(apply: bool) -> dict:
    inv = inventory()
    if inv["lamp"] != "GREEN":
        return inv
    reg = build_register(inv)
    tail = _tail(HERE, REG_STEM, ".json")
    reg_target = None
    if tail is None:
        reg_target = HERE / (REG_STEM + "_v0100.json")
    elif _strip_volatile(json.loads(tail.read_text(encoding="utf-8"))) != _strip_volatile(reg):
        reg.update(version="v%04d" % (_vnum(tail) + 1), prior=tail.name)
        reg_target = HERE / ("%s_v%04d.json" % (REG_STEM, _vnum(tail) + 1))
    cen, cen_tail, added = central_next(inv)
    cen_target = HERE / ("%s_%s.json" % (CENTRAL_STEM, cen["version"])) if cen else None
    if apply:
        if reg_target:
            reg_target.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        if cen_target:
            cen_target.write_text(json.dumps(cen, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"lamp": "GREEN", "apply": apply, "register": _rel(reg_target) if reg_target else "(整合冊尾版已是最新 · 不出新版)",
            "central": _rel(cen_target) if cen_target else "(中央冊已含全部 AOS 條目 · 不出新版)", "central_prior": cen_tail.name if cen_tail else "",
            "central_added": added, "counts": inv["counts"]}


# ── ③ 啟用(逐項真跑)──────────────────────────────────────────────────────
def _run(argv: list, stdin: str = "", timeout: int = 300, env=None) -> tuple:
    try:
        cp = subprocess.run(argv, input=stdin, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                            env={**os.environ, "PYTHONIOENCODING": "utf-8", **(env or {})}, cwd=str(VIA))
        last = [x for x in (cp.stdout or "").strip().splitlines() + (cp.stderr or "").strip().splitlines() if x.strip()]
        return cp.returncode, (cp.stdout or ""), _brief(cp.stdout or "") or (last[-1][:200] if last else "")
    except subprocess.TimeoutExpired:
        return 124, "", "逾時 %ss" % timeout


def _brief(out: str) -> str:
    """JSON 輸出 → 一行重點(status / passed / total / allowed / 數量);不是 JSON 回空。"""
    try:
        j = json.loads(out)
    except ValueError:
        return ""
    if not isinstance(j, dict):
        return "JSON 陣列 %d 筆" % len(j) if isinstance(j, list) else ""
    keys = ("status", "lamp", "result", "passed", "total", "failed", "allowed", "ok", "valid", "count", "reason", "error")
    parts = ["%s=%s" % (k, j[k]) for k in keys if k in j and not isinstance(j[k], (dict, list))]
    parts += ["%s %d 筆" % (k, len(v)) for k, v in j.items() if isinstance(v, list)][:3]
    return (" · ".join(parts) or "JSON %d 鍵" % len(j))[:200]


def _lamp_rc(rc: int) -> str:
    return "GREEN" if rc == 0 else ("YELLOW" if rc in (2, 3, 4) else "RED")


def _sdd_template(aos: Path) -> dict:
    """Agent OS 自己的 SDD 範本(sdd template)當 via.sdd.validate 的探針合約;拿不到回空物件(照實 isError)。"""
    rc, out, _l = _run([sys.executable, str(aos), "sdd", "template"], "", 120)
    try:
        tpl = json.loads(out) if rc == 0 else {}
    except ValueError:
        return {}
    if isinstance(tpl.get("scope"), list) and tpl["scope"]:
        tpl["scope"][0] = "CLAUDE.md"          # Agent OS 允許清單(READ_ONLY_REPO_PATHS)裡的固定路徑;範本的佔位路徑本來就會被擋
    return tpl


def _mcp_session(aos: Path, tool_rows: list) -> list:
    meta = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {},
            "io.modelcontextprotocol/clientInfo": {"name": "vcgc-agentos-hub", "version": VERSION}}
    reqs = [{"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {"_meta": meta}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {"_meta": meta}}]
    args = {"via.skill.run": {"skill_id": "via-planner", "payload": {"objective": "VCGC activation probe"}},
            "via.token.prepare": {"text": "VCGC activation probe · token prepare"},
            "via.policy.authorize": {"request": {"tool": "github", "action": "read", "repository": "tonykuni/movies-dataset"}},
            "via.sdd.validate": {"contract": _sdd_template(aos)}}
    for n, t in enumerate(tool_rows, 3):
        reqs.append({"jsonrpc": "2.0", "id": n, "method": "tools/call", "params": {"name": t["name"], "arguments": args.get(t["name"], {}), "_meta": meta}})
    rc, out, last = _run([sys.executable, str(aos), "mcp", "serve", "--max-tool-calls", "30", "--max-runtime-seconds", "120"],  # Agent OS 上限 1..30
                         "\n".join(json.dumps(r, ensure_ascii=False) for r in reqs) + "\n", 180)
    replies = {}
    for line in out.splitlines():
        try:
            j = json.loads(line)
            replies[j.get("id")] = j
        except ValueError:
            continue
    rows = []
    listed = {x.get("name") for x in ((replies.get(2) or {}).get("result") or {}).get("tools", [])}
    rows.append({"id": "AOS-MCP-HS", "kind": "mcp_handshake", "name": "server/discover + tools/list", "how": "mcp serve(stdio 換行框)",
                 "rc": rc, "lamp": "GREEN" if replies.get(1) and listed else "RED", "note": "列出 %d 工具 · %s" % (len(listed), last[:80])})
    for n, t in enumerate(tool_rows, 3):
        r = replies.get(n) or {}
        res = r.get("result") or {}
        err = r.get("error")
        is_err = bool(res.get("isError")) or bool(err)
        sc = res.get("structuredContent") or {}
        note = (err or {}).get("message") if err else (sc.get("reason") or sc.get("status") or ("回覆 %d 鍵" % len(sc)))
        lamp = "GREEN" if r and not is_err and t["name"] in listed else ("YELLOW" if r and t["name"] in listed else "RED")
        rows.append({"id": t["id"], "kind": "mcp_tool", "name": t["name"], "how": "tools/call", "rc": 0 if r else 1, "lamp": lamp,
                     "note": "%s%s" % ("isError · " if is_err else "", str(note)[:120])})
    return rows


def activate(out: Path) -> dict:
    inv = inventory()
    if inv["lamp"] != "GREEN":
        return inv
    aos = VIA / inv["agent_os"]["file"]
    py = sys.executable
    rows = []

    def add(id_, kind, name, how, rc, note, lamp=None):
        rows.append({"id": id_, "kind": kind, "name": name, "how": how, "rc": rc, "lamp": lamp or _lamp_rc(rc), "note": note})

    rc, _o, last = _run([py, str(aos), "selftest"], timeout=1500)
    add("AOS-SELFTEST", "selftest", "Agent OS selftest(含 27 個 Skill 驗收例)", "selftest", rc, last)
    probe = json.dumps({"tool": "github", "action": "read", "repository": "tonykuni/movies-dataset"})
    verb_plan = {"selftest": None, "status": (["status", "--repo-root", str(VIA.parent)], ""),
                 "repo-check": (["repo-check", "--repo-root", str(VIA.parent)], ""),
                 "deploy-preflight": (["deploy-preflight", "--repo-root", str(VIA.parent)], ""),
                 "sdd": (["sdd", "template"], ""), "skills": (["skills", "test"], ""),
                 "context": (["context", "--query", "VCGC"], "VCGC 啟用探針:token 準備 · api_key=XXXXXXXXXXXXXXXXXXXX"),
                 "policy": (["policy"], probe), "vcgc-status": (["vcgc-status", "--repo-root", str(VIA.parent)], ""),
                 "mcp": (["mcp", "config-example"], ""), "scan": (["scan", "--root", str(AOS_DIR)], ""),
                 "mounts": (["mounts", "--root", str(AOS_DIR)], ""), "route": (["route", str(aos)], ""), "dashboard": None}
    for v in inv["verbs"]:
        plan = verb_plan.get(v["verb"], ())
        if plan is None:
            add(v["id"], "verb", v["verb"], "由 selftest 驗(%s)" % ("本身" if v["verb"] == "selftest" else "會在倉外寫檔 · 站只准唯讀"),
                rc, "見 AOS-SELFTEST", rows[0]["lamp"])
            continue
        if plan == ():
            add(v["id"], "verb", v["verb"], "—", 3, "沒有啟用計畫(新動詞?)→ 補 verb_plan", "YELLOW")
            continue
        r, _o, last = _run([py, str(aos), *plan[0]], plan[1], 300)
        add(v["id"], "verb", v["verb"], " ".join(plan[0][:2]), r, last)
    factor = {"name": "momentum_20d", "category": "momentum", "dataset": "VDF 台股日線", "market": "TW", "signal": "20 日報酬",
              "formula": "close / close.shift(20) - 1", "regime": "trend", "failure_case": "盤整反轉"}
    probe_inputs = {"factor": factor, "factor_list": [factor], "evidence": {"ic_mean": 0.03, "t_stat": 2.1, "sample_years": 8},
                    "source_code": "def add_one(x: int) -> int:\n    return x + 1\n",
                    "memory_candidate": {"content": "VCGC 啟用探針:Agent OS 併入 VCGC", "kind": "decision", "source": "VCGC"}}
    for t in [x for x in inv["tools"] if x["kind"] == "skill"]:
        payload = json.dumps({k: probe_inputs.get(k, "VCGC 啟用探針:%s" % k) for k in t["inputs"]}, ensure_ascii=False)
        r, o, last = _run([py, str(aos), "skills", "run", t["name"]], payload, 300)
        bad = re.search(r"status=(INVALID_INPUT|ERROR|BLOCKED|FAIL\w*|SYNTAX_FAIL)", last)
        add(t["id"], "skill", t["name"], "skills run(stdin JSON)", r, last, "YELLOW" if (r == 0 and bad) else None)
    rows += _mcp_session(aos, [x for x in inv["tools"] if x["kind"] == "mcp_tool"])
    skx = VIA / inv["skill_export"] if inv["skill_export"] else None
    for t in [x for x in inv["tools"] if x["kind"] == "slash_skill"]:
        if skx is None:
            add(t["id"], "slash_skill", t["name"], "—", 3, "VIA_SkillExport 不在", "ABSENT")
            continue
        r, _o, last = _run([py, str(skx), "chain", t["name"]], "", 120)
        add(t["id"], "slash_skill", t["name"], "SkillExport chain", r, last)
    cen = _tail(HERE, CENTRAL_STEM, ".json")
    bad, have = [], set()
    if cen:
        d = json.loads(cen.read_text(encoding="utf-8"))
        have = set(d.get("regex", {})) | set(d.get("synonyms", {}))
        for k, v in d.get("regex", {}).items():
            try:
                re.compile(v["pattern"] if isinstance(v, dict) else v)
            except (re.error, TypeError, KeyError):
                bad.append(k)
    for r_ in inv["regex"] + inv["synonyms"]:
        ok = r_["key"] in have
        add(r_["id"], "ssot_regex" if r_["id"].startswith("AOS-RGX") else "ssot_synonym", r_["key"], "中央冊 %s" % (cen.name if cen else "—"),
            0 if ok else 2, "已登錄" if ok else "未登錄 → register --apply", "GREEN" if ok else "YELLOW")
    add("SSOT-CENTRAL-COMPILE", "ssot_regex", "中央冊全部正則可編譯", cen.name if cen else "—", 0 if cen and not bad else 1,
        "壞 %d:%s" % (len(bad), ",".join(bad[:5])) if bad else "全部可編譯")
    g = graphify_status()
    if g["state"] == "READY":
        gr = graphify_run("AOS", None, out / "graphify")
        add("GRAPHIFY-AOS", "graphify", "Graphify 小樣跑圖(Agent OS 夾)", "extract --code-only + cluster-only", 0 if gr["lamp"] == "GREEN" else 1,
            "節點 %s · 連線 %s · %s" % (gr.get("nodes"), gr.get("edges"), gr.get("why", "")), gr["lamp"])
    else:
        add("GRAPHIFY", "graphify", "Graphify(隔離環境)", "偵測", 3, g["why"], "ABSENT")
    lamps = [r["lamp"] for r in rows]
    lamp = "RED" if "RED" in lamps else ("YELLOW" if ("YELLOW" in lamps or "ABSENT" in lamps) else "GREEN")
    res = {"engine": TAG, "at": _utc(), "lamp": lamp, "counts": inv["counts"], "tally": {k: lamps.count(k) for k in ("GREEN", "YELLOW", "RED", "ABSENT")},
           "rows": rows, "agent_os": inv["agent_os"]}
    write_matrix(res, out)
    return res


def write_matrix(res: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "AOS_ACTIVATION_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    cols = ["id", "kind", "name", "how", "rc", "lamp", "note"]
    with (out / "AOS_ACTIVATION_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["編號", "類別", "名稱", "怎麼跑", "rc", "燈", "說明"])
        for r in res["rows"]:
            w.writerow([r.get(c, "") for c in cols])
    e = lambda s: html.escape(str(s))  # noqa: E731
    color = {"GREEN": "ok", "YELLOW": "warn", "RED": "bad", "ABSENT": "warn"}
    body = "".join("<tr>%s</tr>" % "".join(('<td><span class="pill %s">%s</span></td>' % (color.get(r["lamp"], ""), e(r["lamp"]))) if c == "lamp"
                                           else "<td>%s</td>" % e(r.get(c, "")) for c in cols) for r in res["rows"])
    (out / "AOS_ACTIVATION_latest.html").write_text("""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VCGC Agent OS 啟用矩陣</title><style>:root{--bg:#f6f5f2;--card:#fff;--fg:#26282b;--mute:#6b6f76;--line:#e3e1dc;--ok:#2f7d4f;--warn:#a86b12;--bad:#b3362c}
@media (prefers-color-scheme:dark){:root{--bg:#17181a;--card:#1f2124;--fg:#e8e6e1;--mute:#9a9ea5;--line:#33363a;--ok:#6cc08b;--warn:#e0a84a;--bad:#ec7a6f}}
body{margin:0;background:var(--bg);color:var(--fg);font:13px/1.5 "Noto Sans TC","Segoe UI",system-ui,sans-serif}main{padding:16px;max-width:1600px;margin:auto}
.wrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:8px}table{border-collapse:collapse;width:100%%}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}th{color:var(--mute)}.pill{padding:1px 8px;border:1px solid currentColor;border-radius:10px}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}</style></head><body><main><h1>VCGC · Agent OS + Graphify 啟用矩陣</h1>
<p>%s · 燈 %s · 綠 %d · 黃 %d · 紅 %d · 缺件 %d · 工具 %d(Skill %d + MCP %d + slash %d)</p>
<div class="wrap"><table><thead><tr><th>編號</th><th>類別</th><th>名稱</th><th>怎麼跑</th><th>rc</th><th>燈</th><th>說明</th></tr></thead><tbody>%s</tbody></table></div></main></body></html>""" % (
        e(res["at"]), e(res["lamp"]), res["tally"]["GREEN"], res["tally"]["YELLOW"], res["tally"]["RED"], res["tally"]["ABSENT"],
        res["counts"]["tools_total"], res["counts"]["skills"], res["counts"]["mcp_tools"], res["counts"]["slash_skills"], body), encoding="utf-8")


# ── ④ Graphify(隔離環境)──────────────────────────────────────────────────
def graphify_exe():
    cands = []
    if os.environ.get("VIA_GRAPHIFY_PY"):
        p = Path(os.environ["VIA_GRAPHIFY_PY"])
        cands.append(p.parent / ("graphify.exe" if os.name == "nt" else "graphify"))
    venv = Path(os.environ.get("VIA_GRAPHIFY_VENV") or (Path(os.environ.get("USERPROFILE") or Path.home()) / "envs" / "via_graphify"))
    cands.append(venv / ("Scripts/graphify.exe" if os.name == "nt" else "bin/graphify"))
    w = shutil.which("graphify")
    if w:
        cands.append(Path(w))
    return next((c for c in cands if c.is_file()), None)


def graphify_status() -> dict:
    exe = graphify_exe()
    if exe is None:
        return {"state": "ABSENT", "why": "沒有隔離環境的 graphify(VIA_GRAPHIFY_PY / ~/envs/via_graphify / PATH)→ 桌機貼 via_graphify_v0101 那一行建隔離 venv"
                "(第一次下載 graphifyy %s 要操作員開 VIA_NET_CONSENT · 本支不代設)" % GRAPHIFY_VERSION}
    rc, out, last = _run([str(exe), "--version"], timeout=60)
    ver = (out.strip().splitlines() or [last])[0]
    return {"state": "READY" if rc == 0 else "BROKEN", "exe": str(exe), "version": ver, "why": "" if rc == 0 else last,
            "pinned": GRAPHIFY_VERSION in ver}


def graphify_run(system, path, out: Path) -> dict:
    st = graphify_status()
    if st["state"] != "READY":
        return {"lamp": "ABSENT", "why": st["why"]}
    src = Path(path) if path else VIA / GRAPHIFY_SYSTEMS.get(system or "", "")
    if not src.is_dir():
        return {"lamp": "RED", "why": "來源夾不在 %s" % src}
    o = out / (system or src.name)
    o.mkdir(parents=True, exist_ok=True)
    ex = [a for g in GRAPHIFY_EXCLUDES for a in ("--exclude", g)]
    env = {"GRAPHIFY_BACKEND": "none", "GRAPHIFY_QUERY_LOG_DISABLE": "1"}
    rc, _o, last = _run([st["exe"], "extract", str(src), "--code-only", "--max-workers", "2", "--out", str(o), *ex], timeout=3600, env=env)
    if rc == 0:
        rc, _o, last = _run([st["exe"], "cluster-only", str(o), "--no-label"], timeout=1800, env=env)
    gj = o / "graphify-out" / "graph.json"
    if rc or not gj.is_file():
        return {"lamp": "RED", "rc": rc, "why": last}
    g = json.loads(gj.read_text(encoding="utf-8"))
    nn, ne = len(g.get("nodes") or []), len(g.get("links") or g.get("edges") or [])
    rec = {"lamp": "GREEN" if nn > 0 else "RED", "system": system or src.name, "src": _rel(src), "nodes": nn, "edges": ne,
           "graph": str(gj), "html": str(o / "graphify-out" / "graph.html"), "version": st["version"], "at": _utc(),
           "mode": "code-only · GRAPHIFY_BACKEND=none · offline"}
    (out / ("VIA_Graphify_%s_latest.json" % rec["system"])).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


# ── ⑤ 自測 / CLI ──────────────────────────────────────────────────────────
def selftest() -> int:
    global HERE  # noqa: PLW0603 — ⑥–⑨ 暫指暫存夾,結束還原
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s 自測 ===" % TAG, flush=True)
    inv = inventory()
    c = inv.get("counts", {})
    chk("① 靜態盤點 Agent OS 尾版(不執行)", inv["lamp"] == "GREEN", inv.get("agent_os", {}).get("file"))
    chk("② 8 Skill · 9 MCP 工具 · 10 slash 技能 = 27 工具", (c.get("skills"), c.get("mcp_tools"), c.get("slash_skills"), c.get("tools_total")) == (8, 9, 10, 27), c)
    chk("③ 14 個 CLI 動詞 · 4 個內建模組 · ≥ 3 條遮罩正則", c.get("verbs") == 14 and c.get("modules") == 4 and c.get("regex", 0) >= 3, c)
    ids = [t["id"] for t in inv["tools"]] + [x["id"] for x in inv["verbs"] + inv["modules"] + inv["regex"] + inv["synonyms"]]
    chk("④ 穩定 ID 不重號", len(ids) == len(set(ids)), len(ids))
    chk("⑤ MCP 工具 ↔ CLI 動詞同義對照都指得到真的動詞", all(s["aliases"][1].split()[0] in {v["verb"] for v in inv["verbs"]} for s in inv["synonyms"]))
    with tempfile.TemporaryDirectory() as td:
        fake = Path(td)
        tail = _tail(HERE, CENTRAL_STEM, ".json")
        shutil.copy(tail, fake / tail.name)
        keep = HERE
        HERE = fake
        try:
            r1 = register(apply=True)
            r2 = register(apply=True)
        finally:
            HERE = keep
        newc = sorted(fake.glob(CENTRAL_STEM + "_v*.json"))
        old = json.loads((fake / tail.name).read_text(encoding="utf-8"))
        nxt = json.loads(newc[-1].read_text(encoding="utf-8")) if len(newc) > 1 else {}
        chk("⑥ register --apply:整合冊 v0100 + 中央冊下一版", (fake / (REG_STEM + "_v0100.json")).is_file() and len(newc) == 2, r1.get("central"))
        chk("⑦ 中央冊只增:原有正則 / 同義字一字不動 · AOS 條目補上", nxt and all(nxt["regex"].get(k) == v for k, v in old["regex"].items())
            and all(nxt["synonyms"].get(k) == v for k, v in old["synonyms"].items()) and all(k in nxt["regex"] or k in nxt["synonyms"] for k in r1["central_added"]),
            "+%d" % len(r1["central_added"]))
        chk("⑧ 再跑一次不重出版(冪等)", "不出新版" in r2["register"] and "不出新版" in r2["central"], (r2["register"], r2["central"]))
        chk("⑨ 新正則都可編譯", all(re.compile(nxt["regex"][k]["pattern"]) for k in r1["central_added"] if k in nxt.get("regex", {})))
        res = {"at": _utc(), "lamp": "YELLOW", "counts": c, "tally": {"GREEN": 1, "YELLOW": 0, "RED": 0, "ABSENT": 1},
               "rows": [{"id": "X", "kind": "k", "name": "<b>", "how": "h", "rc": 0, "lamp": "GREEN", "note": "n"}]}
        write_matrix(res, fake / "m")
        chk("⑩ 矩陣 JSON / CSV / HTML 寫出 · HTML 跳脫", all((fake / "m" / f).is_file() for f in ("AOS_ACTIVATION_latest.json", "AOS_ACTIVATION_latest.csv", "AOS_ACTIVATION_latest.html"))
            and "&lt;b&gt;" in (fake / "m" / "AOS_ACTIVATION_latest.html").read_text(encoding="utf-8"))
    g = graphify_status()
    chk("⑪ Graphify 偵測照實(READY / ABSENT 附建法)", g["state"] in ("READY", "ABSENT", "BROKEN") and (g["state"] != "ABSENT" or "VIA_NET_CONSENT" in g["why"]), g["state"])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 不 import Agent OS(子行程跑)· 零網路 · 不用 TA-Lib · 不寫同意閘",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|VIA_AgentOS)", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", TAG, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("--selftest", "selftest"):
        return selftest()
    verb, rest = args[0], args[1:]
    out = Path(rest[rest.index("--out") + 1]) if "--out" in rest else OUT_DEFAULT
    as_json = "--json" in rest
    if verb == "inventory":
        inv = inventory()
        if as_json:
            print(json.dumps(inv, ensure_ascii=False, indent=1))
        else:
            c = inv.get("counts", {})
            for t in inv.get("tools", []):
                print("  %-12s %-12s %-26s %s" % (t["id"], t["kind"], t["name"], t["title"]))
            print("[%s] %s · Agent OS %s · 工具 %s(Skill %s + MCP %s + slash %s)· 動詞 %s · 模組 %s · 正則 %s · 同義 %s · Graphify %s" % (
                inv["lamp"], TAG, inv.get("agent_os", {}).get("file"), c.get("tools_total"), c.get("skills"), c.get("mcp_tools"), c.get("slash_skills"),
                c.get("verbs"), c.get("modules"), c.get("regex"), c.get("synonyms"), inv.get("graphify", {}).get("state")))
        return RC.get(inv["lamp"], 1)
    if verb == "register":
        r = register("--apply" in rest)
        print(json.dumps(r, ensure_ascii=False, indent=1) if as_json else
              "[%s] %s register %s · 整合冊 %s · 中央冊 %s(+%d:%s)" % (r["lamp"], TAG, "APPLY" if r.get("apply") else "PLAN(加 --apply 才寫)",
                                                                   r.get("register"), r.get("central"), len(r.get("central_added", [])), ",".join(r.get("central_added", [])[:6])))
        return RC.get(r["lamp"], 1)
    if verb == "activate":
        r = activate(out)
        for x in r.get("rows", []):
            print("  %-7s %-22s %-14s %-24s %s" % (x["lamp"], x["id"], x["kind"], x["name"][:24], x["note"][:90]))
        print("[%s] %s activate · 綠 %d · 黃 %d · 紅 %d · 缺件 %d → %s" % (r["lamp"], TAG, r["tally"]["GREEN"], r["tally"]["YELLOW"], r["tally"]["RED"],
                                                                    r["tally"]["ABSENT"], out / "AOS_ACTIVATION_latest.html"))
        return RC.get(r["lamp"], 1)
    if verb == "graphify":
        sub = rest[0] if rest and not rest[0].startswith("--") else "status"
        if sub == "status":
            g = graphify_status()
            print("[%s] %s graphify · %s" % (g["state"], TAG, g.get("exe") or g["why"]))
            return {"READY": 0, "ABSENT": 3}.get(g["state"], 1)
        system = rest[rest.index("--system") + 1] if "--system" in rest else None
        path = rest[rest.index("--path") + 1] if "--path" in rest else None
        systems = [system] if (system or path) else list(GRAPHIFY_SYSTEMS)
        worst = 0
        for s in systems:
            r = graphify_run(s, path, out / "graphify")
            print("[%s] graphify %s · %s" % (r["lamp"], s or path, ("節點 %s · 連線 %s · %s" % (r["nodes"], r["edges"], r["html"])) if r["lamp"] == "GREEN" else r.get("why")))
            worst = max(worst, RC.get(r["lamp"], 1) if r["lamp"] != "RED" else 9)
        return 1 if worst == 9 else worst
    print("用法:%s inventory|register [--apply]|activate [--out D]|graphify status|run [--system S|--path P] · --selftest" % TAG)
    return 2


if __name__ == "__main__":
    sys.exit(main())
