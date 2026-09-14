#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL149_VeritasCentralGovernanceConsole v0101 — Veritas Central Governance Console(VCGC;批506;v0101 批507)
v0100→v0101(批507 操作員問「多 AI 寫作要怎麼接手不掉球、格式如何、長久使用」):一頁交接 +〇 接手提示詞(docs/VIA_AI_Handover_Prompt_v*.md 尾版全文嵌入)
  +九 掉球清單(docs/VIA_DroppedBalls_*.md 尾版);格子 PYCODE/自指站標「特殊」不當缺;十二檢。
====================================================================
操作員令:「相關中央控管為 Veritas Central Governance Console,為此系統連接各模組引擎的唯一對接口,
控管 政策庫 · 邏輯庫 · 因子庫 · 資料庫 · VIA 引擎調度 · 多矩陣實測結果;不要丟失參數及指令;
所有引擎/模組/功能/工具/環境都要註冊;lesson-learned;環境統一測式無誤後才可核可安裝;
詳細 handover report 整合成同一頁 + 環境工具管理 + 自動編號註冊表。」(律 L20)
Zero-Hydra:本台**只讀不造**——各庫各冊各引擎的正主不變,這裡是唯一對接口(讀它們的冊/台帳/報告、印一頁、稽核註冊)。
  政策庫  VIA_Policy_Laws_SSOT_v*.json(律+lessons)+ ENG082 policy_factors()(攤平入 via_policy_factors)
  邏輯庫  ENG082 LOGIC_latest.json(件/法/後端健康)+ sync_state(全庫同步對帳)
  因子庫  SUP_MDL748 policy_rows()(AllInOne + FDS 兩本冊)
  資料庫  VIA_DB_Table_SSOT(冊)+ DATAHOME_CATALOG_latest.json(家內庫/湖)
  引擎調度 CGC_MDL095 Deck 任務冊 + VIA_InputConsole_Spec 項 + CGC_MDL064 格子站 + Register-VIA-Commands 指令(含用法/參數)
  多矩陣  ENGINE_BUS_latest.json(五矩陣)+ RUNGATE_latest.json(環境統一測式)
  環境工具 TOOLS_PLAN_latest.json(MDL135 tools)
  註冊表  VIA_AutoCode_Registry(自動編號類別 current + 台帳尾)
  註冊稽核 硬碟上的引擎家族(尾版)× 七處登冊(規格/Deck/格子/Register/Manager)→ 未登冊清單(誠實)
  安裝核可 L19:RunGate 判定 GREEN 且 24h 內 → INSTALL_OK;否則 BLOCKED_UNITEST
用法:python3 CGC_MDL149_VeritasCentralGovernanceConsole_v0101.py [status|page|onepage|audit|register-plan|check] [--publish] | --selftest
  page/onepage 預設落 VIA_Reports/vcgc/(不入 git、不弄髒工作樹);--publish 才複製到 ui_support 頁與 docs/VIA_Handover_ONEPAGE.md + 倉根 VIA_HANDOVER_LATEST.md(我 commit 時的手)
律:零 CDN;零彈窗;零網路;只讀;誠實 ABSENT(報告不在=講不在,不編)。
"""
from __future__ import annotations

import html
import importlib.util
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ROOT = VIA.parent
REPORTS = VIA / "VIA_Reports"
OUTDIR = REPORTS / "vcgc"
VERSION = "0101"
BATCH = 507
UNITEST_MAX_AGE_H = 24.0


def _newest(root: Path, pat: str) -> Path | None:
    c = sorted(root.glob(pat))
    return c[-1] if c else None


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _json(p: Path | None) -> dict | None:
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig")) if p and Path(p).is_file() else None
    except Exception:
        return None


def _age_h(ts: str) -> float | None:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return (datetime.now() - datetime.strptime(str(ts)[:19], fmt)).total_seconds() / 3600.0
        except Exception:
            pass
    return None


# ────────────────────────── 讀各庫各冊(只讀) ──────────────────────────
def laws() -> dict:
    j = _json(_newest(HERE, "VIA_Policy_Laws_SSOT_v*.json"))
    return {"state": "OK" if j else "ABSENT", "laws": (j or {}).get("laws", []), "lessons": (j or {}).get("lessons", []), "src": (j or {}).get("batch", "")}


def ledger() -> dict:
    j = _json(HERE / "VIA_AutoCode_Registry_v0100.json")
    if not j:
        return {"state": "ABSENT"}
    L = j.get("ledger", [])
    return {"state": "OK", "n": len(L), "tail": L[-8:], "categories": {k: v.get("current") for k, v in (j.get("categories") or {}).items()},
            "components": len(j.get("components") or {}), "updated_at": j.get("updated_at")}


def deck_tasks() -> dict:
    p = _newest(HERE, "CGC_MDL095_DeckServer_v*.py")
    if not p:
        return {"state": "ABSENT", "tasks": {}}
    try:
        m = _load("vcgc_deck", p)
        t = m.task_registry()
        return {"state": "OK", "src": p.name, "tasks": {k: {"zh": v.get("zh", ""), "argv": [str(x) for x in v.get("argv", [])], "net": bool(v.get("net"))} for k, v in t.items()}}
    except Exception as exc:
        return {"state": f"BROKEN {type(exc).__name__}", "tasks": {}}


def spec_items() -> dict:
    j = _json(HERE / "VIA_InputConsole_Spec_v0100.json")
    if not j:
        return {"state": "ABSENT", "items": []}
    items = []

    def walk(o, fam):
        if isinstance(o, dict):
            if "id" in o and ("engine" in o or "state" in o):
                e = o.get("engine") or {}
                items.append({"family": fam, "id": o["id"], "zh": o.get("zh", ""), "glob": e.get("glob", ""), "dir": e.get("dir", ""), "verb": e.get("verb", []),
                              "params": o.get("params", []), "net": bool(o.get("net")), "state": o.get("state", "")})
            for k, v in o.items():
                walk(v, k if k in ("vdf", "vrn", "vap") else fam)
        elif isinstance(o, list):
            for x in o:
                walk(x, fam)
    walk(j.get("families", {}), "")
    return {"state": "OK", "items": items, "param_kinds": list((j.get("param_kinds") or {}).keys())}


def grid_stations() -> dict:
    p = _newest(HERE, "CGC_MDL064_SelftestGrid_v*.py")
    if not p:
        return {"state": "ABSENT", "stations": []}
    try:
        m = _load("vcgc_grid", p)
        B = m.battery(False)
        st = []
        for b in B:
            pth = str(b["path"]) if b.get("path") else ""
            special = (pth in ("", "PYCODE")) or ("自指" in b["name"])
            st.append({"name": b["name"], "path": pth, "present": ("特殊" if special else (Path(pth).is_file())), "args": b.get("args", [])})
        return {"state": "OK", "src": p.name, "stations": st}
    except Exception as exc:
        return {"state": f"BROKEN {type(exc).__name__}", "stations": []}


def register_cmds() -> dict:
    p = _newest(VIA, "Register-VIA-Commands-v*.ps1")
    if not p:
        return {"state": "ABSENT", "cmds": []}
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    cmds, aliases = [], {}
    for i, ln in enumerate(lines):
        m = re.match(r"^function global:(via-[A-Za-z0-9\-]+)", ln)
        if m:
            name = m.group(1)
            usage = ""
            for j in range(i - 1, max(-1, i - 8), -1):
                if lines[j].startswith("#") and name in lines[j]:
                    usage = lines[j].lstrip("# ").strip()
                    break
            cmds.append({"cmd": name, "usage": usage[:220], "line": i + 1})
        m2 = re.match(r"^Set-Alias -Name (\S+) -Value (via-[A-Za-z0-9\-]+)", ln)
        if m2:
            aliases.setdefault(m2.group(2), []).append(m2.group(1))
    for c in cmds:
        c["aliases"] = aliases.get(c["cmd"], [])
    return {"state": "OK", "src": p.name, "cmds": cmds}


def manager_names() -> dict:
    p = _newest(VIA, "VIA_SYSTEM_MANAGER_v*.py")
    if not p:
        return {"state": "ABSENT", "tasks": {}, "engines": {}}
    s = p.read_text(encoding="utf-8", errors="replace")

    def block(key):
        m = re.search(key + r"\s*=\s*\{(.*?)\n\}", s, flags=re.S)
        return dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', m.group(1))) if m else {}
    return {"state": "OK", "src": p.name, "tasks": block("TASK_FORMAL_NAMES"), "engines": block("ENGINE_FORMAL_NAMES")}


def db_sheet() -> dict:
    j = _json(HERE / "VIA_DB_Table_SSOT_v0100.json")
    if not j:
        return {"state": "ABSENT"}
    t = j.get("tables", [])
    return {"state": "OK", "n": len(t), "all_home": sum(1 for x in t if x.get("db_scope") == "all_home"), "batch": j.get("batch", ""), "dbs": sorted({x.get("db", "") for x in t})}


def datahome() -> dict:
    j = _json(REPORTS / "datahome" / "DATAHOME_CATALOG_latest.json")
    if not j:
        return {"state": "ABSENT", "why": "VIA_Reports/datahome/DATAHOME_CATALOG_latest.json 不在(via-datahome catalog)"}
    return {"state": "OK", "home": j.get("home", ""), "dbs": len(j.get("by_name") or {}), "tables": len(j.get("by_table") or {}), "lakes": len(j.get("lake") or []), "ts": j.get("ts", "")}


def logic() -> dict:
    p = _newest(VIA / "functional modules" / "VRN", "VRN_ENG082_ExtractionLogic_v*.py")
    if not p:
        return {"state": "ABSENT"}
    try:
        m = _load("vcgc_eng082", p)
        d = m.load_latest()
        files = d.get("files") or {}
        by: dict = {}
        for r in files.values():
            by[r.get("verdict")] = by.get(r.get("verdict"), 0) + 1
        out = {"state": "OK", "src": p.name, "files": len(files), "verdicts": by, "backends": {k: v.get("state") for k, v in (d.get("backends") or {}).items()},
               "broken": list(m.broken_backends()), "policy_rows": len(m.policy_factors())}
        try:
            ss = m.sync_state(quiet=True)
            out["sync"] = {"hash": ss.get("hash"), "counts": dict(ss.get("counts") or {}), "dbs": len(ss.get("dbs") or [])}
        except Exception as exc:
            out["sync"] = {"state": f"BROKEN {type(exc).__name__}"}
        try:
            out["handover"] = m.handover_copies(quiet=True)
        except Exception:
            pass
        return out
    except Exception as exc:
        return {"state": f"BROKEN {type(exc).__name__}:{str(exc)[:60]}"}


def factors() -> dict:
    p = _newest(VIA / "supportive modules" / "70_VRN_Rules", "SUP_MDL748_FinancialLogicHub_v*.py")
    if not p:
        return {"state": "ABSENT"}
    try:
        m = _load("vcgc_748", p)
        rows = m.policy_rows()
        by: dict = {}
        for r in rows:
            by[r["source"]] = by.get(r["source"], 0) + 1
        m.allinone(); m.fds()
        return {"state": "OK", "src": p.name, "rows": len(rows), "by_source": by, "mounts": dict(m._M.get("why") or {})}
    except Exception as exc:
        return {"state": f"BROKEN {type(exc).__name__}"}


def tools_plan() -> dict:
    j = _json(REPORTS / "env_governance" / "TOOLS_PLAN_latest.json")
    if not j:
        return {"state": "ABSENT", "why": "TOOLS_PLAN_latest.json 不在(via-envtools)"}
    return {"state": j.get("state", "?"), "ts": j.get("ts"), "counts": j.get("counts", {}), "risk": j.get("risk_counts", {}), "stages": len(j.get("stages", [])),
            "unrouted": len(j.get("unrouted", [])), "hold": len(j.get("whitelist_hold", [])), "envs": [(e.get("name"), e.get("state")) for e in j.get("envs", [])][:24]}


def rungate() -> dict:
    p = Path(os.environ.get("VIA_RUNGATE_LATEST") or (REPORTS / "rungate" / "RUNGATE_latest.json"))
    j = _json(p)
    if not j:
        return {"state": "ABSENT", "why": f"{p.name} 不在(via-rungate 先跑)", "install": "BLOCKED_UNITEST"}
    age = _age_h(j.get("ts", ""))
    ok = j.get("verdict") == "GREEN" and age is not None and age <= UNITEST_MAX_AGE_H
    return {"state": j.get("verdict", "?"), "ts": j.get("ts"), "age_h": (round(age, 1) if age is not None else None), "families": list((j.get("families") or {}).keys()),
            "install": "INSTALL_OK" if ok else "BLOCKED_UNITEST"}


def bus() -> dict:
    j = _json(REPORTS / "engine_bus" / "ENGINE_BUS_latest.json")
    if not j:
        return {"state": "ABSENT", "why": "ENGINE_BUS_latest.json 不在(via-ryg)"}
    res = j.get("results") or []
    by: dict = {}
    for r in res:
        by[r.get("state", "?")] = by.get(r.get("state", "?"), 0) + 1
    reds = [(r.get("id") or r.get("item"), (r.get("why") or "")[:90]) for r in res if r.get("state") in ("RED", "TIMEOUT")]
    return {"state": "OK", "ts": j.get("ts"), "apply_families": j.get("apply_families"), "n": len(res), "counts": by or j.get("counts", {}), "reds": reds[:12],
            "html": str(REPORTS / "engine_bus" / "ENGINE_BUS_MATRIX.html")}


def handover_src() -> dict:
    hits = []
    for q in (VIA / "docs").glob("VIA_Handover_*_B*.md"):
        m = re.match(r"VIA_Handover_(\d{8})_B(\d+)\.md$", q.name)
        if m:
            hits.append(((m.group(1), int(m.group(2))), q))
    if not hits:
        return {"state": "ABSENT", "sections": {}}
    p = sorted(hits)[-1][1]
    t = p.read_text(encoding="utf-8", errors="replace")
    secs, cur, buf = {}, None, []
    for ln in t.splitlines():
        if ln.startswith("## "):
            if cur:
                secs[cur] = "\n".join(buf).strip()
            cur, buf = ln[3:].strip(), []
        else:
            buf.append(ln)
    if cur:
        secs[cur] = "\n".join(buf).strip()
    return {"state": "OK", "src": p.name, "sections": secs, "text": t}


def prompt_doc() -> dict:
    p = _newest(VIA / "docs", "VIA_AI_Handover_Prompt_v*.md")
    return {"state": "OK" if p else "ABSENT", "src": (p.name if p else ""), "text": (p.read_text(encoding="utf-8", errors="replace") if p else "")}


def dropped_balls() -> dict:
    hits = sorted((VIA / "docs").glob("VIA_DroppedBalls_B*.md"), key=lambda q: int(re.search(r"_B(\d+)", q.name).group(1)))
    p = hits[-1] if hits else None
    t = p.read_text(encoding="utf-8", errors="replace") if p else ""
    rows = [ln for ln in t.splitlines() if ln.startswith("| ") and not ln.startswith("| 代號") and not ln.startswith("|---")]
    return {"state": "OK" if p else "ABSENT", "src": (p.name if p else ""), "text": t, "n": len(rows), "open": sum(1 for r in rows if "~~" not in r)}


# ────────────────────────── 註冊稽核 ──────────────────────────
ENGINE_GLOBS = [("functional modules/VDF/engine", "*_v????.py"), ("functional modules/VRN", "*_v????.py"), ("functional modules/VAP/engine", "*_v????.py"),
                ("supportive modules/registry", "CGC_*_v????.py"), ("supportive modules/70_VRN_Rules", "SUP_*_v????.py"), ("supportive modules/network", "SUP_*_v????.py"),
                ("supportive modules/VIA_Central_Governance", "CGC_*_v????.py"), (".", "VIA_SYSTEM_MANAGER_v????.py")]


def audit(deck=None, spec=None, grid=None, reg=None, man=None) -> dict:
    deck = deck if deck is not None else deck_tasks()
    spec = spec if spec is not None else spec_items()
    grid = grid if grid is not None else grid_stations()
    reg = reg if reg is not None else register_cmds()
    man = man if man is not None else manager_names()
    reg_text = ""
    p = _newest(VIA, "Register-VIA-Commands-v*.ps1")
    if p:
        reg_text = p.read_text(encoding="utf-8", errors="replace")
    hay = "\n".join([json.dumps(deck.get("tasks"), ensure_ascii=False), json.dumps(spec.get("items"), ensure_ascii=False),
                     "\n".join(s["path"] + " " + s["name"] for s in grid.get("stations", [])), reg_text, json.dumps(man, ensure_ascii=False)])
    fams: dict = {}
    for d, g in ENGINE_GLOBS:
        for q in (VIA / d).glob(g):
            if "references" in q.parts or "_superseded" in str(q):
                continue
            stem = re.sub(r"_v\d{4}\.py$", "", q.name)
            if stem not in fams or q.name > fams[stem]["newest"]:
                fams[stem] = {"newest": q.name, "dir": d}
    rows = []
    for stem, v in sorted(fams.items()):
        key = stem.split("_")[0] + "_" + stem.split("_")[1] if stem.count("_") >= 1 else stem      # 例 VRN_ENG082 / CGC_MDL149
        registered = (stem in hay) or (key in hay and key.count("_") == 1 and len(key) > 6)
        rows.append({"family": stem, "newest": v["newest"], "dir": v["dir"], "registered": bool(registered)})
    unreg = [r for r in rows if not r["registered"]]
    return {"families": len(rows), "registered": len(rows) - len(unreg), "unregistered": unreg, "rows": rows}


def check() -> dict:
    """L19 安裝核可:RunGate GREEN 且 24h 內。"""
    r = rungate()
    return {"install": r.get("install"), "rungate": r.get("state"), "age_h": r.get("age_h"), "law": "L19 環境統一測式無誤後才可核可安裝"}


# ────────────────────────── 一頁交接 + 頁 ──────────────────────────
def snapshot() -> dict:
    deck, spec, grid, reg, man = deck_tasks(), spec_items(), grid_stations(), register_cmds(), manager_names()
    return {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "version": VERSION, "batch": BATCH, "laws": laws(), "ledger": ledger(), "deck": deck, "spec": spec,
            "grid": grid, "register": reg, "manager": man, "db_sheet": db_sheet(), "datahome": datahome(), "logic": logic(), "factors": factors(),
            "tools": tools_plan(), "rungate": rungate(), "bus": bus(), "handover": handover_src(), "audit": audit(deck, spec, grid, reg, man),
            "prompt": prompt_doc(), "balls": dropped_balls()}


def onepage_md(s: dict) -> str:
    L, lg, dk, sp, gr, rg, mn, db, dh, lo, fa, tp, ru, bu, ho, au = (s[k] for k in ("laws", "ledger", "deck", "spec", "grid", "register", "manager", "db_sheet", "datahome", "logic", "factors", "tools", "rungate", "bus", "handover", "audit"))
    o = [f"# VIA 一頁交接 · Veritas Central Governance Console(VCGC v{VERSION} · 批{BATCH})", "",
         f"> 產生 {s['ts']} · 唯一對接口(律 L20):政策庫 · 邏輯庫 · 因子庫 · 資料庫 · 引擎調度 · 多矩陣 · 環境工具 · 註冊表 · 交接。動態段(矩陣/RunGate/工具計畫/資料家)以**你機器上最新一次 `via-vcgc onepage`** 為準;倉內這份是 commit 時的快照。", ""]
    pr, bl = s.get("prompt", {}), s.get("balls", {})
    o += ["## 〇 · 接手提示詞(給下一個 AI;來源 " + str(pr.get("src") or "ABSENT") + ")", "", (pr.get("text") or "(docs/VIA_AI_Handover_Prompt_v*.md 缺)").strip(), ""]
    o += ["## 一 · 政策庫(律 + lessons-learned)", ""]
    for x in L["laws"]:
        o.append(f"- **{x['id']}**({x['batch']};{x['cat']}){x['zh']}")
    o += ["", "**Lessons-learned**", ""] + [f"- {x['id']}({x['batch']}){x['zh']}" for x in L["lessons"]]
    o += ["", "## 二 · 安裝核可(L19)與環境工具", "",
          f"- RunGate:{ru.get('state')} · {ru.get('ts') or '-'} · 齡 {ru.get('age_h')} h → **{ru.get('install')}**" + (f"({ru.get('why')})" if ru.get("why") else ""),
          f"- 工具冊導入計畫:{tp.get('state')} · {tp.get('ts') or '-'} · 件態 {tp.get('counts')} · 風險 {tp.get('risk')} · 段 {tp.get('stages')} · 未路由 {tp.get('unrouted')} · 白名單留置 {tp.get('hold')}" + (f"({tp.get('why')})" if tp.get("why") else ""),
          "- 裝件=操作員的手:`$env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve`(閘不代設;L19 未綠=BLOCKED_UNITEST)", ""]
    o += ["## 三 · 邏輯庫 · 因子庫 · 資料庫", "",
          f"- 邏輯庫 {lo.get('state')}:件 {lo.get('files')} · 判準 {lo.get('verdicts')} · 壞後端 {lo.get('broken')} · 政策因子 {lo.get('policy_rows')} 列 · 全庫同步 {lo.get('sync')} · 交接三處 {lo.get('handover')}",
          f"- 因子庫 {fa.get('state')}:{fa.get('rows')} 列 · {fa.get('by_source')} · 掛載 {fa.get('mounts')}",
          f"- 庫表冊 {db.get('state')}:{db.get('n')} 表({db.get('batch')})· 全庫表 {db.get('all_home')} · 庫 {db.get('dbs')}",
          f"- 資料家 {dh.get('state')}:{dh.get('home') or dh.get('why')} · 庫 {dh.get('dbs')} · 表 {dh.get('tables')} · 湖 {dh.get('lakes')}", ""]
    o += ["## 四 · 引擎調度 · 多矩陣實測", "",
          f"- 五矩陣 {bu.get('state')}:{bu.get('ts') or bu.get('why')} · 真跑 {bu.get('apply_families')} · 項 {bu.get('n')} · 態 {bu.get('counts')}"]
    for rid, why in (bu.get("reds") or []):
        o.append(f"  - RED {rid}:{why}")
    o += [f"- Deck 任務 {len(dk.get('tasks', {}))} · 規格項 {len(sp.get('items', []))} · 格子站 {len(gr.get('stations', []))}(在位 {sum(1 for x in gr.get('stations', []) if x['present'])})· Register 指令 {len(rg.get('cmds', []))} · Manager 正式名稱 任務 {len(mn.get('tasks', {}))} / 引擎 {len(mn.get('engines', {}))}", ""]
    o += ["## 五 · 指令與參數(不丟失;來源 " + str(rg.get("src")) + ")", ""] + [f"- `{c['cmd']}`" + (f"(別名 {'/'.join(c['aliases'])})" if c["aliases"] else "") + (f":{c['usage']}" if c["usage"] else "") for c in rg.get("cmds", [])]
    o += ["", "## 六 · 註冊稽核(所有引擎/模組/工具都要註冊)", "",
          f"- 引擎家族(尾版){au['families']} · 已登冊 {au['registered']} · **未登冊 {len(au['unregistered'])}**"] + [f"  - {r['newest']}({r['dir']})" for r in au["unregistered"][:60]]
    o += ["", "## 七 · 自動編號註冊表(台帳)", "", f"- 台帳 {lg.get('n')} 筆 · 元件 {lg.get('components')} · 更新 {lg.get('updated_at')}",
          "- 類別 current:" + " · ".join(f"{k} {v}" for k, v in (lg.get("categories") or {}).items() if v), ""]
    for e in (lg.get("tail") or [])[-6:]:
        o.append(f"- {e.get('ts')} {str(e.get('kind'))[:90]}")
    secs = ho.get("sections") or {}
    o += ["", f"## 八 · 交接本文(來源 {ho.get('src')};逐批紀錄見該檔)", ""]
    o_tail = ["", f"## 九 · 掉球清單(來源 {bl.get('src') or 'ABSENT'};列 {bl.get('n')} · 未結 {bl.get('open')};只增不減,結案劃線)", "", (bl.get("text") or "(缺)").strip(), ""]
    for key in ("三 · 還掛著的事", "四 · 紀律(每條都付過代價)", "五 · 一貼即用(操作員工作站)"):
        for k, v in secs.items():
            if k.startswith(key.split("(")[0]):
                o += [f"### {k}", "", v, ""]
    o += o_tail
    return "\n".join(o) + "\n"


def page_html(s: dict) -> str:
    def esc(x):
        return html.escape(str(x))

    def table(rows, cols):
        h = "<table><tr>" + "".join(f"<th>{esc(c)}</th>" for c in cols) + "</tr>"
        for r in rows:
            h += "<tr>" + "".join(f"<td>{esc(r.get(c, ''))}</td>" for c in cols) + "</tr>"
        return h + "</table>"
    lamp = {"OK": "#16a34a", "GREEN": "#16a34a", "INSTALL_OK": "#16a34a", "ABSENT": "#6b7280", "BLOCKED_UNITEST": "#f59e0b", "RED": "#dc2626", "PLAN": "#2563eb"}
    ru, bu, tp, lo, fa, db, dh, au, rg, lg, L = (s[k] for k in ("rungate", "bus", "tools", "logic", "factors", "db_sheet", "datahome", "audit", "register", "ledger", "laws"))

    def chip(t):
        return f'<span class="chip" style="background:{lamp.get(str(t).split(" ")[0], "#6b7280")}">{esc(t)}</span>'
    parts = [f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>Veritas Central Governance Console v{VERSION}</title>",
             "<style>body{font-family:'Segoe UI',system-ui,sans-serif;margin:0;background:#0f172a;color:#e5e7eb}header{padding:18px 28px;background:#111827;border-bottom:1px solid #334155}h1{margin:0;font-size:20px}h2{font-size:15px;margin:22px 0 8px;color:#93c5fd}section{padding:6px 28px}table{border-collapse:collapse;font-size:12px;width:100%}th,td{border:1px solid #334155;padding:4px 6px;text-align:left;vertical-align:top}th{background:#1f2937}.chip{display:inline-block;padding:2px 8px;border-radius:10px;color:#fff;font-size:12px;margin-right:6px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}.card{background:#111827;border:1px solid #334155;border-radius:8px;padding:10px 12px;font-size:13px}code{background:#1f2937;padding:1px 4px;border-radius:4px}small{color:#9ca3af}</style></head><body>",
             f"<header><h1>Veritas Central Governance Console <small>v{VERSION} · 批{BATCH} · {esc(s['ts'])} · 唯一對接口(L20)· 零 CDN · 只讀</small></h1></header>",
             "<section><div class='grid'>",
             f"<div class='card'><b>安裝核可 L19</b><br>{chip(ru.get('install'))} RunGate {chip(ru.get('state'))} {esc(ru.get('ts') or ru.get('why') or '')} 齡 {esc(ru.get('age_h'))} h</div>",
             f"<div class='card'><b>五矩陣</b><br>{chip(bu.get('state'))} {esc(bu.get('ts') or bu.get('why') or '')}<br>{esc(bu.get('counts'))}</div>",
             f"<div class='card'><b>環境工具計畫</b><br>{chip(tp.get('state'))} {esc(tp.get('ts') or tp.get('why') or '')}<br>{esc(tp.get('counts'))} · 風險 {esc(tp.get('risk'))}</div>",
             f"<div class='card'><b>邏輯庫</b><br>{chip(lo.get('state'))} 件 {esc(lo.get('files'))} · {esc(lo.get('verdicts'))}<br>壞後端 {esc(lo.get('broken'))}<br>同步 {esc(lo.get('sync'))}</div>",
             f"<div class='card'><b>因子庫</b><br>{chip(fa.get('state'))} {esc(fa.get('rows'))} 列 · {esc(fa.get('by_source'))}</div>",
             f"<div class='card'><b>資料庫</b><br>庫表冊 {esc(db.get('n'))} 表({esc(db.get('batch'))})· 資料家 {chip(dh.get('state'))} {esc(dh.get('home') or dh.get('why'))} · 庫 {esc(dh.get('dbs'))} 湖 {esc(dh.get('lakes'))}</div>",
             f"<div class='card'><b>註冊稽核</b><br>家族 {au['families']} · 已登 {au['registered']} · 未登 {len(au['unregistered'])}</div>",
             f"<div class='card'><b>掉球清單</b><br>{esc(s.get('balls', {}).get('src') or 'ABSENT')} · 列 {esc(s.get('balls', {}).get('n'))} · 未結 {esc(s.get('balls', {}).get('open'))}<br><small>接手提示詞:{esc(s.get('prompt', {}).get('src') or 'ABSENT')}</small></div>",
             f"<div class='card'><b>自動編號註冊表</b><br>台帳 {esc(lg.get('n'))} 筆 · 元件 {esc(lg.get('components'))}<br>{esc({k: v for k, v in (lg.get('categories') or {}).items() if v})}</div>",
             "</div></section>",
             "<section><h2>政策庫 · 律</h2>" + table(L["laws"], ["id", "batch", "cat", "zh"]) + "<h2>Lessons-learned</h2>" + table(L["lessons"], ["id", "batch", "zh"]) + "</section>",
             "<section><h2>指令與參數(不丟失)</h2>" + table([{"cmd": c["cmd"], "aliases": "/".join(c["aliases"]), "usage": c["usage"]} for c in rg.get("cmds", [])], ["cmd", "aliases", "usage"]) + "</section>",
             "<section><h2>Deck 任務冊</h2>" + table([{"task": k, "zh": v["zh"], "net": v["net"], "argv": " ".join(Path(a).name if "/" in a or "\\" in a else a for a in v["argv"])} for k, v in s["deck"].get("tasks", {}).items()], ["task", "zh", "net", "argv"]) + "</section>",
             "<section><h2>主控台規格項</h2>" + table(s["spec"].get("items", []), ["family", "id", "zh", "glob", "verb", "params", "net", "state"]) + "</section>",
             "<section><h2>格子站</h2>" + table(s["grid"].get("stations", []), ["name", "present", "path"]) + "</section>",
             "<section><h2>未登冊引擎家族(誠實)</h2>" + table(au["unregistered"], ["family", "newest", "dir"]) + "</section>",
             "<section><h2>紅項(五矩陣)</h2>" + table([{"id": i, "why": w} for i, w in (bu.get("reds") or [])], ["id", "why"]) + "</section>",
             "<section><h2>台帳尾</h2>" + table(lg.get("tail") or [], ["ts", "kind"]) + "</section>",
             "</body></html>"]
    return "".join(parts)


def write_outputs(s: dict, out_dir: Path, publish: bool) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    md, pg = onepage_md(s), page_html(s)
    (out_dir / "VIA_Handover_ONEPAGE.md").write_text(md, encoding="utf-8")
    (out_dir / "VIA_UI_CentralGovernanceConsole_v0100.html").write_text(pg, encoding="utf-8")
    (out_dir / "VCGC_latest.json").write_text(json.dumps({k: v for k, v in s.items() if k != "handover"}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    res = {"out": str(out_dir), "published": []}
    if publish:
        for dst in ((VIA / "docs" / "VIA_Handover_ONEPAGE.md"), (ROOT / "VIA_HANDOVER_LATEST.md")):
            dst.write_text(md, encoding="utf-8"); res["published"].append(str(dst))
        d2 = VIA / "supportive modules" / "ui_support" / "VIA_UI_CentralGovernanceConsole_v0100.html"
        d2.write_text(pg, encoding="utf-8"); res["published"].append(str(d2))
    return res


def status() -> int:
    s = snapshot()
    print(f"[VCGC] v{VERSION} 批{BATCH} · 唯一對接口(L20)· {s['ts']}")
    print(f"  政策庫 {s['laws']['state']}:律 {len(s['laws']['laws'])} · lessons {len(s['laws']['lessons'])} · 政策因子 {s['logic'].get('policy_rows')} 列")
    print(f"  邏輯庫 {s['logic'].get('state')}:件 {s['logic'].get('files')} · {s['logic'].get('verdicts')} · 壞後端 {s['logic'].get('broken')} · 同步 {s['logic'].get('sync')}")
    print(f"  因子庫 {s['factors'].get('state')}:{s['factors'].get('rows')} 列 {s['factors'].get('by_source')}")
    print(f"  資料庫:庫表冊 {s['db_sheet'].get('n')} 表 · 資料家 {s['datahome'].get('state')} {s['datahome'].get('home') or s['datahome'].get('why')}")
    print(f"  引擎調度:Deck {len(s['deck'].get('tasks', {}))} 任務 · 規格 {len(s['spec'].get('items', []))} 項 · 格子 {len(s['grid'].get('stations', []))} 站 · Register {len(s['register'].get('cmds', []))} 指令")
    print(f"  多矩陣 {s['bus'].get('state')}:{s['bus'].get('counts') or s['bus'].get('why')} · RunGate {s['rungate'].get('state')} → {s['rungate'].get('install')}")
    print(f"  環境工具 {s['tools'].get('state')}:{s['tools'].get('counts') or s['tools'].get('why')}")
    print(f"  註冊稽核:家族 {s['audit']['families']} · 已登 {s['audit']['registered']} · 未登 {len(s['audit']['unregistered'])}" + (":" + ", ".join(r['newest'] for r in s['audit']['unregistered'][:8]) if s['audit']['unregistered'] else ""))
    print(f"  台帳 {s['ledger'].get('n')} 筆 · 交接源 {s['handover'].get('src')} · 頁/一頁:via-vcgc page|onepage(落 VIA_Reports/vcgc;--publish 才入倉)")
    return 0


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    L = laws()
    chk("① 政策庫冊掛載(≥20 律、≥8 lessons;含 L19 安裝核可 / L20 唯一對接口)", L["state"] == "OK" and len(L["laws"]) >= 20 and len(L["lessons"]) >= 8 and {x["id"] for x in L["laws"]} >= {"L19", "L20"}, f"({len(L['laws'])} 律 · {len(L['lessons'])} lessons)")
    lg = ledger()
    chk("② 自動編號註冊表(台帳 ≥1000 筆 · 類別 current · 元件)", lg["state"] == "OK" and lg["n"] >= 1000 and "引擎" in lg["categories"] and lg["components"] > 0, f"({lg.get('n')} 筆)")
    dk = deck_tasks()
    chk("③ Deck 任務冊只讀取得(≥60 任務;含 vrn_logic/fin_logic/fin_statements)", dk["state"] == "OK" and len(dk["tasks"]) >= 60 and {"vrn_logic", "fin_logic", "fin_statements"} <= set(dk["tasks"]), f"({dk['state']} · {len(dk['tasks'])})")
    sp = spec_items()
    chk("④ 主控台規格項(≥40 項;fin_statements 接引擎)", sp["state"] == "OK" and len(sp["items"]) >= 40 and any(i["id"] == "fin_statements" and i["glob"] for i in sp["items"]), f"({len(sp['items'])})")
    gr = grid_stations()
    chk("⑤ 格子站只讀取得(≥100 站;在位計數誠實)", gr["state"] == "OK" and len(gr["stations"]) >= 100, f"({gr['state']} · {len(gr['stations'])} 站 · 在位 {sum(1 for x in gr['stations'] if x['present'])})")
    rg = register_cmds()
    chk("⑥ Register 指令與用法解析(≥60 指令;via-vrnlogic/via-finstat 帶用法行;別名 邏輯庫)", rg["state"] == "OK" and len(rg["cmds"]) >= 60
        and any(c["cmd"] == "via-vrnlogic" and c["usage"] and "邏輯庫" in c["aliases"] for c in rg["cmds"]) and any(c["cmd"] == "via-finstat" and c["usage"] for c in rg["cmds"]), f"({len(rg['cmds'])})")
    mn = manager_names()
    chk("⑦ Manager 正式名稱只讀(任務 ≥50 · 引擎 ≥30)", mn["state"] == "OK" and len(mn["tasks"]) >= 50 and len(mn["engines"]) >= 30, f"({len(mn['tasks'])}/{len(mn['engines'])})")
    au = audit(dk, sp, gr, rg, mn)
    chk("⑧ 註冊稽核:家族 ≥80;本批引擎(CGC_MDL149/VDF_ENG082/SUP_MDL748/VRN_ENG082)皆已登冊;未登冊清單誠實列出",
        au["families"] >= 80 and all(any(r["family"].startswith(k) and r["registered"] for r in au["rows"]) for k in ("VDF_ENG082_FinStatements", "SUP_MDL748_FinancialLogicHub", "VRN_ENG082_ExtractionLogic")),
        f"(家族 {au['families']} · 已登 {au['registered']} · 未登 {len(au['unregistered'])})")
    sv = os.environ.get("VIA_RUNGATE_LATEST")
    with tempfile.TemporaryDirectory() as td:
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "none.json")
        c0 = check()
        Path(td, "g.json").write_text(json.dumps({"verdict": "GREEN", "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "families": {"vrn": {}}}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "g.json")
        c1 = check()
        Path(td, "old.json").write_text(json.dumps({"verdict": "GREEN", "ts": "2020-01-01T00:00:00"}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "old.json")
        c2 = check()
        if sv is None:
            os.environ.pop("VIA_RUNGATE_LATEST", None)
        else:
            os.environ["VIA_RUNGATE_LATEST"] = sv
        chk("⑨ 安裝核可 L19:RunGate 缺=BLOCKED_UNITEST;GREEN 且 24h 內=INSTALL_OK;GREEN 但過期=BLOCKED_UNITEST", c0["install"] == "BLOCKED_UNITEST" and c1["install"] == "INSTALL_OK" and c2["install"] == "BLOCKED_UNITEST", f"({c0['install']}/{c1['install']}/{c2['install']})")
        s = snapshot()
        res = write_outputs(s, Path(td) / "out", publish=False)
        md = (Path(td) / "out" / "VIA_Handover_ONEPAGE.md").read_text(encoding="utf-8")
        pg = (Path(td) / "out" / "VIA_UI_CentralGovernanceConsole_v0100.html").read_text(encoding="utf-8")
        chk("⑩ 一頁交接 + 頁(零 CDN;八段齊;預設落暫存夾不入倉;--publish 才入倉)", not res["published"] and all(k in md for k in ("## 一 · 政策庫", "## 二 · 安裝核可", "## 五 · 指令與參數", "## 六 · 註冊稽核", "## 七 · 自動編號註冊表", "## 八 · 交接本文"))
            and "<script src" not in pg and "<link rel" not in pg and "Veritas Central Governance Console" in pg, f"({len(md)} 字 · 頁 {len(pg)//1024} KB)")
    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]     # 不讀自測本身的字串(LL 自我引用)
    chk("⑪ 零網路 · 只讀(無 import requests/httpx/duckdb;不寫任何冊/庫;只寫 VIA_Reports/vcgc 或 --publish 三處)", all(("import " + k) not in code for k in ("requests", "httpx", "duckdb")) and "CREATE " not in code)
    pr, bl = prompt_doc(), dropped_balls()
    gs = grid_stations()
    chk("⑫ 批507:接手提示詞(docs 尾版;含 A 開場/B 收尾/C 格式)與掉球清單(≥12 列)嵌入一頁交接 〇/九 段;格子 PYCODE/自指站標「特殊」不當缺",
        pr["state"] == "OK" and all(k in pr["text"] for k in ("## A", "## B", "## C")) and bl["state"] == "OK" and bl["n"] >= 12
        and "## 〇 · 接手提示詞" in md and "## 九 · 掉球清單" in md and not any(x["present"] is False for x in gs["stations"] if x["path"] in ("", "PYCODE")),
        f"({pr.get('src')} · {bl.get('src')} 列 {bl.get('n')} 未結 {bl.get('open')} · 格子在位 {sum(1 for x in gs['stations'] if x['present'] is True)} 特殊 {sum(1 for x in gs['stations'] if x['present'] == '特殊')})")
    print(f"  [計] 十二檢 OK {12 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print(f"=== Veritas Central Governance Console(CGC_MDL149 v{VERSION})· 十二檢自測(零網路;只讀)===")
        return selftest()
    verb = a[0] if a else "status"
    if verb == "status":
        return status()
    if verb in ("page", "onepage"):
        s = snapshot()
        res = write_outputs(s, OUTDIR, publish="--publish" in a)
        print(f"[VCGC] 一頁交接 + 頁 → {res['out']}" + (f" · 已發佈 {res['published']}" if res["published"] else " (未入倉;--publish 才入倉)"))
        return 0
    if verb == "audit":
        au = audit()
        print(f"[VCGC 註冊稽核] 家族 {au['families']} · 已登冊 {au['registered']} · 未登冊 {len(au['unregistered'])}")
        for r in au["unregistered"]:
            print(f"  未登 {r['newest']}({r['dir']})")
        return 0
    if verb == "register-plan":
        # 律 L18/L02:未登冊家族 → 列出建議登冊(格子站行 + Deck 任務樁),只列不寫;操作員核准後另批登冊
        au = audit()
        OUTDIR.mkdir(parents=True, exist_ok=True)
        lines = [f"# VCGC 登冊建議 {datetime.now():%Y-%m-%d %H:%M} · 未登冊家族 {len(au['unregistered'])}(只列不寫;核准後另批登冊)", ""]
        for r in au["unregistered"]:
            q = VIA / r["dir"] / r["newest"]
            has_st = False
            try:
                has_st = "--selftest" in q.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
            lines.append(f"- {r['newest']}({r['dir']})· 自測旗 {'有' if has_st else '無'} → " + (f"格子站:add(\"{r['family']} 自測\", newest(\"{r['family']}_v*.py\", VIA / \"{r['dir']}\"), [\"--selftest\"], \"rc0\", 300)" if has_st else "先補 --selftest 再登站;Deck/Register 依其動詞另議"))
        (OUTDIR / "REGISTER_PLAN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines[:30]) + (f"\n… 共 {len(lines) - 2} 條 → {OUTDIR / 'REGISTER_PLAN.md'}" if len(lines) > 30 else ""))
        return 0
    if verb == "check":
        c = check()
        print(f"[VCGC 安裝核可] {c['install']} · RunGate {c['rungate']} · 齡 {c['age_h']} h · {c['law']}")
        return 0 if c["install"] == "INSTALL_OK" else 2
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
