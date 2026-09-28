#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL242_PathVerify v0100 — 單一路徑驗證:VCGC → VDF → VRN 實跑結果 × 執行版本 × 編號冊 × 註冊冊 × 鎖冊 交叉比對 → 簡單版 HTML

操作員 2026-09-28 R27:「單一路徑實測 VCGC VDF VRN 邊實測邊修邊註冊 邊所指令版本執行後 並驗證結果交互比對 跳出簡單版 HTML 介面 整個收尾」。
本支不重跑任何引擎(一把尺:結果都讀正主剛寫的存證),只做比對:
  ① 路徑步驟(依序):VCGC 流程閘 · ENV MANAGER · 註冊同步 · VDF 建庫計畫 · VDF 鏈 · VRN 鏈 · 橋 / 全景 / DB 面板 / 工具(全景實測)· 版面鎖
  ② 版本交叉:這條路徑實際跑到的每一支(入口引擎 + VRN 鏈上每一站 + 四件工具)取**尾版** →
       編號冊有沒有它的號(VIA_NumberBooks · MDL / ENG)· 註冊冊有沒有 ACTIVE 記錄(VIA_Component_Inventory)· 鎖冊版號 / sha(工具)
  ③ 結果交叉:VDF / VRN 鏈計數 × 燈鎖回歸 × 上一輪(path_verify/HISTORY.jsonl)增減
  ④ 簡單版頁:CGC_MDL241 呈現套件(最簡淺色小規格;自動登記進 SYNCHRONIZER)→ VIA_Reports/path_verify/PATH_VERIFY_latest.html
  ⑤ 布建完成紀錄(操作員:「環境工具布建完成紀錄上傳 收尾儲存備份」):每跑一次在 registry/VIA_EnvProvision_Ledger_v0100.jsonl
     追加一行(只增不減;進版控):總判 · ENV MANAGER 總判與計數 · 四件工具版本 + sha 對不對 · 兩鏈計數 · 燈鎖回歸 · 版本不齊支數 · HEAD。
     上傳(git commit + push 只含這一本)由操作員的 PowerShell 做(Invoke-VIA-OperatorConsole v0103 ⑦),本支不碰 git。
只收 VCGC 呼叫。零網路。用法:python3 CGC_MDL242_PathVerify_v0100.py [run] [--json] [--no-record] | --selftest
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import html as _html
import importlib.util
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REP = VIA / "VIA_Reports"
OUT = REP / "path_verify"
ENGINE = Path(__file__).stem
ENTRY_STEMS = ("CGC_MDL149_VeritasCentralGovernanceConsole", "CGC_MDL223_FlowConsistency", "CGC_MDL240_EnvManager", "CGC_MDL238_OperatorConsole",
               "CGC_MDL239_DataBroker", "CGC_MDL241_TemplateAdapter", "CGC_MDL170_VDFChainRunner", "CGC_MDL172_VRNChainRunner",
               "CGC_MDL124_BridgeSweeper", "CGC_MDL158_VIAPanoramaAuditRepair", "CGC_MDL228_VIADBManager", "CGC_MDL229_SweepReport",
               "CGC_MDL230_ToolCoverageProbe", "CGC_MDL233_ToolActivate", "CGC_MDL137_RunGate", "CGC_MDL135_EnvGovernance",
               "CGC_MDL237_NumberingSystem", "CGC_MDL242_PathVerify")
LAMP = {"GREEN": "GREEN", "OK": "GREEN", "AMBER": "AMBER", "SKIP": "AMBER", "YELLOW": "AMBER", "NODATA": "AMBER", "GATED": "AMBER",
        "ABSENT": "AMBER", "RED": "RED", "FAIL": "RED", "UNTESTED": "NODATA", "": "NODATA", None: "NODATA"}
ORDER = {"RED": 0, "AMBER": 1, "NODATA": 2, "GREEN": 3}
LEDGER = HERE / "VIA_EnvProvision_Ledger_v0100.jsonl"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


def _json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


_TAILS: dict = {}


def tail_of(stem: str) -> Path | None:
    """Newest version file of a stem anywhere under the live tree (references / reports excluded)."""
    if not _TAILS:
        for root in (VIA / "supportive modules", VIA / "functional modules"):
            for p in root.rglob("*_v*.py"):
                sp = str(p)
                if "/references/" in sp or "SCOPE_COPY" in sp:
                    continue
                s = re.sub(r"_v\d+$", "", p.stem)
                if s not in _TAILS or _vnum(p) > _vnum(_TAILS[s]):
                    _TAILS[s] = p
    return _TAILS.get(stem)


def _mod(stem: str):
    p = tail_of(stem)
    if p is None:
        return None
    spec = importlib.util.spec_from_file_location(stem + "_for_" + ENGINE, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- books

def number_index() -> dict:
    """file stem (with version) → code, from the MDL / ENG number books."""
    out = {}
    for b in sorted((HERE / "VIA_NumberBooks").glob("VIA_NumberBook_*_v*.jsonl")):
        if not re.search(r"_(MDL|ENG)_v\d+\.jsonl$", b.name):
            continue
        with b.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get("gone_since"):
                    continue
                out.setdefault(str(r.get("name")), r.get("code"))
    return out


def register_index() -> dict:
    """relative source path → state, from the VCGC component register (module / engine rows)."""
    reg = _json(HERE / "VIA_Component_Inventory_SSOT_v0100.json") or {}
    out = {}
    for r in reg.get("records") or []:
        src = str(r.get("source") or "")
        if src.endswith(".py") and r.get("category") in ("module", "engine", "tool", "system"):
            if out.get(src) != "ACTIVE":
                out[src] = r.get("state")
    return out


def lock_index() -> dict:
    lock = _json(HERE / "VIA_ToolVersion_Lock_v0100.json") or {}
    return {Path(str(v.get("path"))).name: (fam, v.get("version")) for fam, v in lock.items() if isinstance(v, dict) and v.get("path")}


# ---------------------------------------------------------------- ① path steps · ② versions · ③ results

def path_steps() -> list:
    rows = []
    side = _json(REP / "sweep" / "SWEEP_SIDE_latest.json") or {}
    flow = str(side.get("flow") or "")
    gate = next((s for s in side.get("steps") or [] if s.get("id") == "vcgc"), {})
    rows.append({"step": "⓪ VCGC 流程閘", "state": "GREEN" if gate.get("rc") == 0 else ("NODATA" if not gate else "RED"),
                 "note": (flow[:80] or "流程閘由全景實測第一步跑") + f" · {side.get('ts', '')}"})
    ev = _json(REP / "env_manager" / "ENVMGR_latest.json") or {}
    rows.append({"step": "① ENV MANAGER(輔助工具 · 環境 · LIB)", "state": LAMP.get(ev.get("verdict"), "NODATA"),
                 "note": " · ".join(f"{k} {v}" for k, v in sorted((ev.get("tally") or {}).items())) + f" · {ev.get('ts', '—')}"})
    sy = _json(REP / "operator_console" / "SYNC_latest.json") or {}
    rs = next((r for r in sy.get("rows") or [] if str(r.get("item", "")).startswith("VCGC 元件註冊冊")), {})
    rows.append({"step": "② 註冊同步(registry-sync)", "state": LAMP.get(sy.get("lamp"), "NODATA"), "note": str(rs.get("note") or "—")[:140]})
    b = _mod("CGC_MDL239_DataBroker")
    if b is not None:
        bd = b.build()
        rows.append({"step": "③ VDF 建庫計畫(VCGC→VDF,乾跑)", "state": "GREEN" if set(bd["tally"]) <= {"GREEN"} else "AMBER",
                     "note": " · ".join(f"{k} {v}" for k, v in sorted(bd["tally"].items())) + " · 需網路的項同意閘由操作員開"})
    for fam, p in (("④ VDF 鏈", REP / "vdf_chain" / "VDFCHAIN_latest.json"), ("⑤ VRN 鏈", REP / "vrn_chain" / "VRNCHAIN_latest.json")):
        d = _json(p) or {}
        t = d.get("tally") or {}
        st = "NODATA" if not t else ("RED" if t.get("RED") else ("GREEN" if set(k for k, v in t.items() if v) <= {"GREEN"} else "AMBER"))
        rows.append({"step": fam, "state": st, "note": " · ".join(f"{k} {v}" for k, v in t.items() if v) + f" · {d.get('generated', '—')}"})
    for s in side.get("steps") or []:
        if s.get("id") in ("vcgc", "vdf", "vrn"):
            continue
        rows.append({"step": "⑥ " + str(s.get("title")), "state": "GREEN" if s.get("rc") == 0 else ("AMBER" if s.get("rc") == 2 else "RED"),
                     "note": f"rc {s.get('rc')} · {s.get('sec')}s"})
    oc = _mod("CGC_MDL238_OperatorConsole")
    if oc is not None:
        fl = oc.format_lock()
        rows.append({"step": "⑦ 版面鎖(HTML U/I 格式)", "state": "GREEN" if fl["state"] == "GREEN" else "RED", "note": f"{fl['state']} · {fl['sha']}"})
    return rows


def executed_files() -> list:
    """Every file this path runs: entry engines · VRN chain stations · the four locked tools (loader + body)."""
    seen, out = set(), []

    def add(where, p):
        if p is not None and p.exists() and p not in seen:
            seen.add(p)
            out.append((where, p))

    for s in ENTRY_STEMS:
        add("入口 / VCGC", tail_of(s))
    vrn = _json(REP / "vrn_chain" / "VRNCHAIN_latest.json") or {}
    for st in vrn.get("stages") or []:
        if re.match(r"^(VRN_ENG|SUP_MDL|VIS_VRN|VIA_VRN)\w*$", str(st.get("name"))):
            add("VRN 鏈站", tail_of(str(st["name"])))
    lock = _json(HERE / "VIA_ToolVersion_Lock_v0100.json") or {}
    for fam, v in lock.items():
        if isinstance(v, dict) and v.get("path"):
            add("工具鎖 · " + fam, VIA.parent / v["path"])
    add("工具載入器 · accelerator", tail_of("SUP_MDL737_SuperAccelModule"))
    add("工具載入器 · network", tail_of("SUP_MDL740_NetUnified"))
    return out


def version_rows(files=None, nums=None, reg=None, locks=None) -> list:
    files = files if files is not None else executed_files()
    nums = nums if nums is not None else number_index()
    reg = reg if reg is not None else register_index()
    locks = locks if locks is not None else lock_index()
    rows = []
    for where, p in files:
        rel = str(p.relative_to(VIA)) if str(p).startswith(str(VIA)) else str(p)
        code = nums.get(p.stem)
        state = reg.get(rel)
        lk = locks.get(p.name)
        miss = []
        if not code:
            miss.append("編號冊沒號")
        if state != "ACTIVE":
            miss.append("註冊冊 " + (state or "沒記錄"))
        verdict = "GREEN" if not miss else ("AMBER" if code or state else "RED")
        rows.append({"where": where, "file": p.name, "version": f"v{_vnum(p):04d}" if _vnum(p) >= 0 else "—", "code": code or "—",
                     "register": state or "—", "lock": f"{lk[0]} {lk[1]}" if lk else "—", "state": verdict, "why": " · ".join(miss)})
    return rows


def result_rows(history_path: Path | None = None) -> dict:
    vdf = (_json(REP / "vdf_chain" / "VDFCHAIN_latest.json") or {}).get("tally") or {}
    vrn = (_json(REP / "vrn_chain" / "VRNCHAIN_latest.json") or {}).get("tally") or {}
    oc = _mod("CGC_MDL238_OperatorConsole")
    lk = oc.lock_regressions() if oc is not None else {"regress": [], "held": 0}
    hp = history_path or (OUT / "HISTORY.jsonl")
    prev = None
    if hp.exists():
        lines = [x for x in hp.read_text(encoding="utf-8").splitlines() if x.strip()]
        prev = json.loads(lines[-1]) if lines else None
    now = {"vdf": vdf, "vrn": vrn, "regress": len(lk.get("regress") or []), "held": lk.get("held", 0)}
    delta = []
    if prev:
        for fam in ("vdf", "vrn"):
            for k in set(now[fam]) | set(prev.get(fam) or {}):
                d = int(now[fam].get(k, 0)) - int((prev.get(fam) or {}).get(k, 0))
                if d:
                    delta.append(f"{fam.upper()} {k} {'+' if d > 0 else ''}{d}")
        if now["regress"] != prev.get("regress"):
            delta.append(f"燈鎖回歸 {prev.get('regress')} → {now['regress']}")
    return {"now": now, "prev_ts": (prev or {}).get("ts"), "delta": delta, "regress_list": lk.get("regress") or []}


def verdict(steps: list, vers: list, res: dict) -> str:
    worst = min([ORDER[s["state"]] for s in steps] + [ORDER[v["state"]] for v in vers] or [3])
    if res["now"]["vdf"].get("RED") or res["now"]["vrn"].get("RED"):
        worst = 0
    return {0: "RED", 1: "AMBER", 2: "AMBER", 3: "GREEN"}[worst]


# ---------------------------------------------------------------- ④ simple page

def page(steps, vers, res, v, kit) -> str:
    e = _html.escape
    lamp = kit.lamp
    st = "".join(f"<tr><td>{lamp(s['state'], s['state'])}</td><td>{e(s['step'])}</td><td>{e(s['note'])}</td></tr>" for s in steps)
    bad = [x for x in vers if x["state"] != "GREEN"]
    vr = "".join(f"<tr><td>{lamp(x['state'], x['state'])}</td><td>{e(x['where'])}</td><td>{e(x['file'])}</td><td>{e(x['code'])}</td>"
                 f"<td>{e(x['register'])}</td><td>{e(x['lock'])}</td><td>{e(x['why'])}</td></tr>" for x in sorted(vers, key=lambda r: ORDER[r["state"]]))
    now = res["now"]
    rr = (f"<tr><td>VDF 鏈</td><td>{e(' · '.join(f'{k} {c}' for k, c in now['vdf'].items() if c))}</td></tr>"
          f"<tr><td>VRN 鏈</td><td>{e(' · '.join(f'{k} {c}' for k, c in now['vrn'].items() if c))}</td></tr>"
          f"<tr><td>燈鎖</td><td>守住 {now['held']} · 回歸 {now['regress']}:{e('、'.join(res['regress_list'][:6]))}</td></tr>"
          f"<tr><td>和上一輪比({e(res['prev_ts'] or '第一輪')})</td><td>{e(' · '.join(res['delta']) or '沒有變化')}</td></tr>")
    links = [("操作台", "../operator_console/VIA_OperatorConsole_latest.html"), ("SYNCHRONIZER", "../operator_console/ui/VIA-SYNCHRONIZER-Standalone.html"),
             ("全景實測報告", "../sweep/SWEEP_REPORT_latest.html"), ("ENV MANAGER JSON", "../env_manager/ENVMGR_latest.json")]
    side = ("<div class='via-card'>" + lamp(v, "總判 " + v) + "</div>"
            f"<div class='via-note'>{e(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</div>"
            f"<div class='via-note'>路徑 {len(steps)} 步 · 版本 {len(vers)} 支(不齊 {len(bad)})</div>"
            + "".join(f"<div><a href='{e(h)}' target='_blank'>{e(t)}</a></div>" for t, h in links))
    body = (f"<h3>① 單一路徑(VCGC → VDF → VRN)依序結果</h3><table class='via'><tr><th>燈</th><th>步</th><th>重點</th></tr>{st}</table>"
            f"<h3>② 執行版本 × 編號冊 × 註冊冊 × 鎖冊(不齊的排前面)</h3><table class='via'><tr><th>燈</th><th>在哪</th><th>執行的檔(尾版)</th>"
            f"<th>編號</th><th>註冊冊</th><th>鎖冊</th><th>不齊</th></tr>{vr}</table>"
            f"<h3>③ 結果交叉比對</h3><table class='via'><tr><th>項</th><th>值</th></tr>{rr}</table>"
            "<div class='via-note'>本頁只讀各正主剛寫的存證,不重跑、不改數;黃 = 缺料 / 閘未開 / 待批准,紅 = 壞掉或版本對不上。</div>")
    return kit.page("單一路徑實測 · 交叉驗證", body, side, module={"id": "vcgc-path-verify", "name": "單一路徑驗證"})


def _head() -> str:
    try:
        import subprocess
        p = subprocess.run(["git", "-C", str(VIA), "rev-parse", "--short=8", "HEAD"], capture_output=True, text=True, timeout=10)
        return p.stdout.strip() or "—"
    except Exception:
        return "—"


def record(rep: dict, ledger: Path = LEDGER) -> dict:
    """One append-only line: what was provisioned and verified on this run (the record the operator uploads)."""
    ev = _json(REP / "env_manager" / "ENVMGR_latest.json") or {}
    tools = [{"family": r["item"].split("·")[-1].strip(), "state": r["state"], "note": r["note"]}
             for r in ev.get("rows") or [] if r.get("id") == "A1"]
    loads = {r["item"]: r["state"] for r in ev.get("rows") or [] if r.get("id") == "A2"}
    ps = _json(REP / "env_manager" / "PS_SIDE_latest.json") or {}
    row = {"ts": rep["ts"], "engine": ENGINE, "head": _head(), "verdict": rep["verdict"],
           "env": {"verdict": ev.get("verdict"), "tally": ev.get("tally"), "ts": ev.get("ts")},
           "tools_lock": tools, "tools_load": loads,
           "ps": {k: ps.get(k) for k in ("ps_version", "celeritas_version", "celeritas_applied", "invoke_viapython")} if ps else None,
           "chains": {"vdf": rep["results"]["now"]["vdf"], "vrn": rep["results"]["now"]["vrn"]},
           "lamp_lock": {"held": rep["results"]["now"]["held"], "regress": rep["results"]["now"]["regress"]},
           "versions": {"checked": len(rep["versions"]), "not_aligned": sum(1 for v in rep["versions"] if v["state"] != "GREEN")},
           "steps": {s["step"]: s["state"] for s in rep["steps"]}}
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return row


def run(write: bool = True, rec: bool = True) -> dict:
    kit = _mod("CGC_MDL241_TemplateAdapter")
    steps, vers = path_steps(), version_rows()
    res = result_rows()
    v = verdict(steps, vers, res)
    rep = {"engine": ENGINE, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "verdict": v, "steps": steps, "versions": vers, "results": res}
    if write:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "PATH_VERIFY_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        if kit is not None:
            (OUT / "PATH_VERIFY_latest.html").write_text(page(steps, vers, res, v, kit), encoding="utf-8")
        with (OUT / "HISTORY.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": rep["ts"], "verdict": v, **res["now"]}, ensure_ascii=False) + "\n")
        if rec:
            rep["record"] = str(LEDGER)
            record(rep)
    return rep


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    rep = run(rec="--no-record" not in args)
    if "--json" in args:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    for s in rep["steps"]:
        print(f"  {s['state']:<6} {s['step']:<34} {s['note'][:90]}")
    bad = [x for x in rep["versions"] if x["state"] != "GREEN"]
    print(f"  版本交叉 {len(rep['versions'])} 支 · 不齊 {len(bad)}" + ("".join(f"\n    {x['state']:<6} {x['file']} · {x['why']}" for x in bad[:12])))
    print(f"  和上一輪比:{' · '.join(rep['results']['delta']) or '沒有變化'}")
    print(f"[單一路徑驗證] 總判 {rep['verdict']} · 頁 {OUT / 'PATH_VERIFY_latest.html'}" + (f" · 布建紀錄 +1 行 {LEDGER.name}" if rep.get("record") else ""))
    return {"GREEN": 0, "RED": 1}.get(rep["verdict"], 2)


def selftest() -> int:
    import tempfile
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE} · 自測 ===")
    fake = [("入口", VIA / "a" / "X_v0101.py"), ("入口", VIA / "a" / "Y_v0100.py"), ("入口", VIA / "a" / "Z_v0100.py")]
    rows = version_rows(fake, {"X_v0101": "VIA-VCGC-MDL0001", "Y_v0100": "VIA-VCGC-MDL0002"},
                        {"a/X_v0101.py": "ACTIVE", "a/Y_v0100.py": "RETIRED"}, {})
    st = {r["file"]: r["state"] for r in rows}
    chk("② 版本交叉:號 + 註冊 ACTIVE = 綠;有號但註冊 RETIRED = 黃;兩邊都沒有 = 紅", st == {"X_v0101.py": "GREEN", "Y_v0100.py": "AMBER",
                                                                            "Z_v0100.py": "RED"}, st)
    files = executed_files()
    names = {p.name for _, p in files}
    chk("② 路徑跑到的檔:入口引擎 + VRN 鏈站 + 四件工具都在", any(n.startswith("CGC_MDL240_EnvManager") for n in names)
        and any(n.startswith("VRN_ENG") for n in names) and any(n.startswith("VeritasCeleritas_v") for n in names), f"{len(files)} 支")
    nums, reg = number_index(), register_index()
    chk("② 編號冊 / 註冊冊讀得到", len(nums) > 1000 and len(reg) > 100, f"號 {len(nums)} · 註冊 {len(reg)}")
    with tempfile.TemporaryDirectory() as td:
        hp = Path(td) / "h.jsonl"
        hp.write_text(json.dumps({"ts": "t0", "vdf": {"GREEN": 6}, "vrn": {"GREEN": 42}, "regress": 5}) + "\n", encoding="utf-8")
        res = result_rows(hp)
    chk("③ 和上一輪比:計數增減逐項列出", res["prev_ts"] == "t0" and any(x.startswith("VDF GREEN") for x in res["delta"]) or not res["now"]["vdf"],
        " · ".join(res["delta"][:4]))
    v = verdict([{"state": "GREEN"}], [{"state": "GREEN"}], {"now": {"vdf": {"RED": 1}, "vrn": {}}})
    chk("總判:鏈上有紅 = 紅(不被綠蓋掉)", v == "RED")
    kit = _mod("CGC_MDL241_TemplateAdapter")
    html = page([{"step": "⓪", "state": "GREEN", "note": "<x>"}], rows, {"now": {"vdf": {}, "vrn": {}, "held": 0, "regress": 0}, "regress_list": [],
                                                                        "prev_ts": None, "delta": []}, "AMBER", kit) if kit else ""
    chk("④ 簡單版頁:呈現套件樣式 + 登記進 SYNCHRONIZER;字照樣跳脫", "via-wrap" in html and "vcgc-path-verify" in html and "<x>" not in html)
    with tempfile.TemporaryDirectory() as td:
        lg = Path(td) / "ledger.jsonl"
        fake_rep = {"ts": "t", "verdict": "AMBER", "versions": rows, "steps": [{"step": "⓪", "state": "GREEN"}],
                    "results": {"now": {"vdf": {"GREEN": 7}, "vrn": {"GREEN": 42}, "held": 30, "regress": 5}}}
        r1 = record(fake_rep, lg)
        record(fake_rep, lg)
        lines = lg.read_text(encoding="utf-8").splitlines()
    chk("⑤ 布建紀錄:每跑一次追加一行(只增);帶工具版本 · 兩鏈 · 版本不齊數 · HEAD", len(lines) == 2 and r1["versions"]["not_aligned"] == 2
        and r1["chains"]["vrn"] == {"GREEN": 42} and "head" in r1 and "tools_lock" in r1)
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    try:
        chk("不經 VCGC 就拒跑", main(["run"]) == 2)
    finally:
        if keep is not None:
            os.environ["VIA_FROM_VCGC"] = keep
    ok = all(results)
    print(f"  [計] {len(results)} 檢 OK {sum(results)} · FAIL {len(results) - sum(results)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
