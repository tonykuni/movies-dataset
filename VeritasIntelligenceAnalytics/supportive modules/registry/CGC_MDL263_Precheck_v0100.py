#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL263_Precheck v0100 — via_precheck:一行動用 VCGC 全部檢查,每個黃 / 紅都定位到檔與行、編號、分類、說明、歸屬、下一步

操作員令(2026-10-05):「設一個短令 via_precheck 動用 VCGC 所有功能 · 每個編號分類說明 · 所有 py ps 都要加入加速模板且覆蓋率 100% ·
  網路工具等 ps code 也一樣 · 有編號就有註冊 · 利用全景式分析等工具檢查所有引擎都正常可運作綠燈 · 黃紅燈要先定位定點修理好」。
站(全部經 VCGC 唯一入口;只讀,不寫冊、不觸網):
  ① token   省 Token 工具卡                       ⑧ sdd       SDD 驗證(X-COL / X-NUM / X-REG …)
  ② bridge  PY 加速器 · VDF 網路工具覆蓋率(掃橋器) ⑨ handoff   交接閘(收據 · 相依 · 未登)
  ③ celer   PS 兩章 · PY 橋總閘(CGC_MDL183)        ⑩ test      VCGC 全功能串測(盤點冊每站)
  ④ ast     全景 AST 稽核(CGC_MDL158 scan:治理七類) ⑪ rungate   三家族境 RunGate(vdf · vrn · vap)
  ⑤ sync    元件 AST 編號同步乾跑(有編號就有註冊)  ⑫ matrix    引擎四態全景矩陣
  ⑥ number  編號只增稽核(遺失 · 改身分 · 重號)      ⑬ temp      DuckDB TEMP 鉤境覆蓋
  ⑦ ssot    SSOT 全景(VCGC → VDF → VRN → SUP)
每個發現:編號 PC-### · 類 · 說明 · 位置(檔:行)· 歸屬(L111:VDF / VRN 由子系統修;L70:舊 .ps1 出新版;凍結收容件不改)· 下一步。
判讀:PINVER 若是薄尾釘自己家族的前版(<族>_vN-1)= 薄尾設計,記 INFO 不算黃;跨族釘版才算風險。
用法:via-vcgc run CGC_MDL263_Precheck [--only 站,站] [--skip 站,站] [--json] · --selftest
報告:VIA_Reports/precheck/PRECHECK_latest.json(+ 時戳檔;不進 git)。rc:0 全綠 · 2 有黃 · 1 有紅。
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

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ENGINE = Path(__file__).stem
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
TIMEOUT = int(os.environ.get("VIA_PRECHECK_TIMEOUT") or 1800)

CLASS_ZH = {
    "ACCEL": "PY 缺 SuperAccel 加速器橋(L103 ①)",
    "NET": "VDF 缺統包網路工具橋(L103 ②)",
    "PSTPL": "PS 缺兩章(CELERITAS-TEMPLATE-JOIN + PS-ACCEL;L106)",
    "PINVER": "字串釘死版號當路徑(跨族 = 升版就斷)",
    "PINVER_TAIL": "薄尾釘自己家族前版(設計如此,記錄不算黃)",
    "HARDIMP": "模組頂層硬 import 選用庫(不在 try / 探針內;缺庫就整支掛)",
    "SYSEXE": "以 sys.executable 派別支引擎(應走家族境 python)",
    "VERB": "動詞 / 入口違規",
    "TALIB": "碰到 TA-Lib(L50 禁用)",
    "EVIDENCE": "交接收據失效(rc / 標記 / 相依雜湊)",
    "UNTESTED": "改過的程式沒有交接案(CHANGED_CODE_WITHOUT_TEST)",
    "UNREG": "模組未登元件冊(有編號就要有註冊)",
    "NUMBER": "編號稽核(遺失 · 改身分 · 重號 · 冊內不一致)",
    "SSOT": "SSOT 全景黃 / 紅",
    "SDD": "SDD 驗證黃 / 紅",
    "STATION": "VCGC 串測站黃 / 紅",
    "ENV": "家族境 RunGate 不綠",
    "COVER": "覆蓋率未達 100%",
    "SYNC": "元件註冊冊待同步(有新 / 變更未登)",
    "OTHER": "其他黃 / 紅",
}


def console() -> Path:
    return sorted(HERE.glob("CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"))[-1]


def token_tool() -> Path:
    lock = json.loads((HERE / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))
    p = Path(lock["token"]["path"])
    return p if p.is_absolute() else (VIA.parent / p)


def owner_of(path: str) -> str:
    p = (path or "").replace("\\", "/")
    if "/references/intake/" in p or "/intake/" in p or p.startswith("intake/"):
        return "凍結收容件(不改 · 列豁免名冊)"
    if "functional modules/VRN" in p or "70_VRN_Rules" in p or re.search(r"(^|/)VRN_", p):
        return "VRN_SystemManager(L111)"
    if "functional modules/VDF" in p or re.search(r"(^|/)VDF_", p):
        return "VDF_SystemManager(L111)"
    m = re.search(r"functional modules/([^/]+)", p)
    if m:
        return f"{m.group(1)} 子系統"
    if re.search(r"(^|/)CGC_MDL\d+", p) or "supportive modules/registry" in p:
        return "VCGC"
    if p.endswith(".ps1"):
        return "操作員 / VCGC(L70:舊 .ps1 出新版)"
    if p.startswith("supportive modules"):
        return "SUP(VCGC 代管)"
    return "VCGC"


def is_tail_prior_pin(file: str, detail: str) -> bool:
    """薄尾釘自己家族的前版:VDF_X_v0103.py 裡寫 VDF_X_v0102.py = 設計。"""
    m1 = re.search(r"([A-Za-z0-9_\-.]+?)[_-]v(\d{4})\.py$", Path(file).name)
    m2 = re.search(r"([A-Za-z0-9_\-.]+?)[_-]v(\d{4})\.py", detail or "")
    return bool(m1 and m2 and m1.group(1) == m2.group(1) and int(m2.group(2)) < int(m1.group(2)))


def run_vcgc(args: list, timeout: int = TIMEOUT) -> tuple:
    env = dict(os.environ, VIA_FROM_VCGC="YES", PYTHONUTF8="1")
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, str(console())] + args, cwd=str(VIA), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env)
        return p.returncode, p.stdout + p.stderr, round(time.time() - t0, 1)
    except subprocess.TimeoutExpired as e:
        return 124, (e.stdout or "") if isinstance(e.stdout, str) else "", round(time.time() - t0, 1)


NOISE = re.compile(r"^\s*\[(位階|加速|環境計畫|回覆|衝突|還原|分群|不衝突|靜態|教訓)\]|^\[(政策|監控|第一步|步驟|流程)\]")


def clean(out: str) -> list:
    return [ln for ln in out.splitlines() if ln.strip() and not NOISE.search(ln)]


# ---------- 各站解析:回 (lamp, summary, findings[{cls,file,line,detail}]) ----------
def p_token(rc, out):
    m = re.search(r"已啟用 (\d+)/(\d+)", out)
    ok = rc == 0 and m and m.group(1) == m.group(2)
    return ("GREEN" if ok else "RED"), (m.group(0) if m else f"rc {rc}"), []


def p_bridge(rc, out):
    m = re.search(r"四系總表(.*)", out)
    line = m.group(1) if m else ""
    pairs = re.findall(r"([A-Z]+/[a-z]+) (\d+)/(\d+)", line)
    f = [{"cls": "COVER", "file": "", "line": 0, "detail": f"{k} {a}/{b}"} for k, a, b in pairs if a != b]
    lamp = "GREEN" if pairs and not f and rc == 0 else ("RED" if not pairs else "YELLOW")
    return lamp, " · ".join(f"{k} {a}/{b}" for k, a, b in pairs) or f"rc {rc}", f


def p_celer(rc, out):
    f = []
    for m in re.finditer(r"缺橋 (\S.*\.py)", out):
        f.append({"cls": "ACCEL", "file": m.group(1).strip(), "line": 1, "detail": "CGC_MDL183:PY 缺加速器橋"})
    py = re.search(r"\[PY \][^\n]*", out); ps = re.search(r"\[PS \][^\n]*", out)
    new = re.search(r"基線外新缺 (\d+)", out); debt = re.search(r"既有債 (\d+)", out)
    if debt and int(debt.group(1)):
        f.append({"cls": "PSTPL", "file": "", "line": 0, "detail": f"PS 既有債 {debt.group(1)} 支(L70:舊 .ps1 不改,出新版才補)"})
    lamp = "RED" if (new and int(new.group(1))) else ("YELLOW" if f else "GREEN")
    return lamp, ((py.group(0).strip() if py else "") + " | " + (ps.group(0).strip() if ps else "")), f


def p_ast(rc, out):
    s = out[out.find("{"):] if "{" in out else ""
    try:
        d = json.loads(s)
    except Exception:
        return "RED", f"scan 讀不到 JSON(rc {rc})", []
    f, info = [], 0
    for r in d.get("rows", []):
        if r.get("exempt"):
            continue
        cls = r.get("cls", "OTHER")
        if cls == "PINVER" and is_tail_prior_pin(r.get("file", ""), r.get("detail", "")):
            info += 1
            continue
        f.append({"cls": cls, "file": r.get("file", ""), "line": r.get("line", 0), "detail": r.get("detail", "")[:160]})
    lamp = "GREEN" if not f else ("RED" if any(x["cls"] in ("TALIB", "ACCEL", "NET") for x in f) else "YELLOW")
    return lamp, f"活檔 {d.get('files_scanned')} · 問題 {d.get('issues')} · 豁免 {sum((d.get('by_class_exempt') or {}).values())} · 薄尾前版釘 {info}(設計) · 待修 {len(f)}", f


def p_sync(rc, out):
    m = re.search(r"\{'new': (\d+), 'changed': (\d+), 'stale': (\d+)", out)
    if m and (int(m.group(1)) or int(m.group(2)) or int(m.group(3))):
        return "YELLOW", f"待同步 new {m.group(1)} · changed {m.group(2)} · stale {m.group(3)}", [{"cls": "SYNC", "file": "", "line": 0, "detail": m.group(0)}]
    return ("GREEN" if rc == 0 else "YELLOW"), (m.group(0) if m else f"rc {rc} · 註冊冊與樹對齊"), []


def p_number(rc, out):
    m = re.search(r"遺失 (\d+) · 改身分 (\d+) · 重號 (\d+)(?: · 冊內不一致 (\d+))?", out)
    if not m:
        return "RED", f"讀不到稽核行(rc {rc})", []
    lost, recode, dup, inc = (int(x or 0) for x in m.groups())
    f = []
    if inc:
        f.append({"cls": "NUMBER", "file": "supportive modules/registry/VIA_NumberBooks", "line": 0, "detail": f"冊內不一致 {inc}(冊上宣告碼 ≠ 發出號;多為待裁定)"})
    lamp = "RED" if (lost or recode or dup) else ("YELLOW" if inc else "GREEN")
    return lamp, m.group(0), f


def p_lines(cls):
    def parse(rc, out):
        f = []
        for ln in clean(out):
            m = re.search(r"\[(RED|YELLOW)\s*\]\s*(.*)", ln) or re.search(r"^\s+(RED|YELLOW)\s+(.*)", ln)
            if m:
                txt = m.group(2).strip()
                pm = re.search(r"((?:functional|supportive) modules/[^\s'\"]+\.(?:py|ps1|json))", txt)
                f.append({"cls": cls, "file": pm.group(1) if pm else "", "line": 0, "detail": txt[:200], "lamp": m.group(1)})
        lamp = "RED" if any(x.get("lamp") == "RED" for x in f) else ("YELLOW" if f or rc not in (0,) else "GREEN")
        summ = next((ln.strip() for ln in reversed(clean(out)) if re.search(r"(GREEN|YELLOW|RED)", ln)), f"rc {rc}")
        return lamp, summ[:200], f
    return parse


def p_handoff(rc, out):
    f = []
    for ln in out.splitlines():
        m = re.match(r"\[(RED|YELLOW)\] (\w+) (.*)", ln.strip())
        if not m:
            continue
        kind, rest = m.group(2), m.group(3)
        cls = {"EVIDENCE_INVALID": "EVIDENCE", "CHANGED_CODE_WITHOUT_TEST": "UNTESTED", "MODULE_UNREGISTERED": "UNREG",
               "ACCEL_BRIDGE_MISSING": "ACCEL"}.get(kind, "OTHER")
        if kind == "REQ_CHANGED":
            continue                                   # 需求有變 = 待 checkpoint 的提示,不是缺陷
        pm = re.search(r"((?:functional|supportive) modules/[^'\"]+?\.(?:py|ps1))", rest)
        idm = re.search(r"'id': '([^']+)'", rest)
        f.append({"cls": cls, "file": pm.group(1) if pm else (idm.group(1) if idm else ""), "line": 0, "detail": f"{kind} {rest[:160]}", "lamp": m.group(1)})
    lamp = "RED" if any(x["lamp"] == "RED" for x in f) else ("YELLOW" if f else ("GREEN" if rc == 0 else "YELLOW"))
    return lamp, f"紅 {sum(1 for x in f if x['lamp'] == 'RED')} · 黃 {sum(1 for x in f if x['lamp'] == 'YELLOW')}(REQ_CHANGED 不計)", f


def p_test(rc, out):
    f = []
    for ln in out.splitlines():
        m = re.search(r"\[(RED|YELLOW)\s*\]\s+(\S+)\s+rc (\d+)\s+[\d.]+s · (.*)", ln)
        if m:
            f.append({"cls": "STATION", "file": m.group(2), "line": 0, "detail": m.group(4)[:180], "lamp": m.group(1)})
    s = re.search(r"\[VCGC 全功能串測\] (\w+) · ([^·]+·[^·]+)", out)
    lamp = s.group(1) if s else ("GREEN" if rc == 0 else "RED")
    return lamp, (s.group(0)[:160] if s else f"rc {rc}"), f


def p_rc(cls, ok_word=None):
    def parse(rc, out):
        tail = clean(out)[-1:] or [""]
        lamp = "GREEN" if rc == 0 and (ok_word is None or re.search(ok_word, out)) else ("YELLOW" if rc == 2 else "RED")
        f = [] if lamp == "GREEN" else [{"cls": cls, "file": "", "line": 0, "detail": tail[0][:200]}]
        return lamp, f"rc {rc} · {tail[0][:140]}", f
    return parse


def p_temp(rc, out):
    m = re.search(r"境覆蓋 (\d+)/(\d+) · (\w+)", out)
    if not m:
        return "RED", f"rc {rc}", []
    ok = m.group(1) == m.group(2) and int(m.group(2)) > 0
    return ("GREEN" if ok else "YELLOW"), m.group(0), ([] if ok else [{"cls": "ENV", "file": "", "line": 0, "detail": f"DuckDB TEMP 鉤 {m.group(0)}(工作站跑 install --apply)"}])


STATIONS = [
    ("token", "① 省 Token 工具卡", ["token"], p_token),
    ("bridge", "② PY 加速器 · VDF 網路工具覆蓋率", ["run", "CGC_MDL124_BridgeSweeper", "--subsystems"], p_bridge),
    ("celer", "③ PS 兩章 · PY 橋總閘", ["run", "CGC_MDL183_CeleritasPolicyGate"], p_celer),
    ("ast", "④ 全景 AST 稽核(治理七類)", None, p_ast),
    ("sync", "⑤ 元件 AST 編號同步(有編號就有註冊)", ["sync-check"], p_sync),
    ("number", "⑥ 編號只增稽核", ["run", "CGC_MDL237_NumberingSystem", "audit"], p_number),
    ("ssot", "⑦ SSOT 全景", ["ssot", "panorama", "--no-write"], p_lines("SSOT")),
    ("sdd", "⑧ SDD 驗證", ["sdd", "check"], p_lines("SDD")),
    ("handoff", "⑨ 交接閘", ["handoff", "check"], p_handoff),
    ("test", "⑩ VCGC 全功能串測", ["test", "--quick"], p_test),
    ("rungate_vdf", "⑪ RunGate vdf", ["run", "CGC_MDL137_RunGate", "probe", "--family", "vdf"], p_rc("ENV")),
    ("rungate_vrn", "⑪ RunGate vrn", ["run", "CGC_MDL137_RunGate", "probe", "--family", "vrn"], p_rc("ENV")),
    ("rungate_vap", "⑪ RunGate vap", ["run", "CGC_MDL137_RunGate", "probe", "--family", "vap"], p_rc("ENV")),
    ("matrix", "⑫ 引擎四態全景矩陣", ["matrix"], p_rc("OTHER")),
    ("temp", "⑬ DuckDB TEMP 鉤", ["run", "CGC_MDL262_DuckTempHook", "status"], p_temp),
]


def run_station(key, args, parser):
    if key == "ast":
        t0 = time.time()
        p = subprocess.run([sys.executable, str(token_tool()), "scan", "--json", "--fast"], cwd=str(VIA.parent),
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT)
        out = "\n".join(ln for ln in p.stdout.splitlines() if not ln.startswith("@@PROGRESS"))
        rc, secs = p.returncode, round(time.time() - t0, 1)
    else:
        rc, out, secs = run_vcgc(args)
    lamp, summ, f = parser(rc, out)
    return {"rc": rc, "secs": secs, "lamp": lamp, "summary": summ, "findings": f}


def number_findings(stations: dict) -> list:
    out, n = [], 0
    for key, st in stations.items():
        for x in st["findings"]:
            n += 1
            cls = x.get("cls", "OTHER")
            out.append({"id": f"PC-{n:03d}", "station": key, "class": cls, "class_zh": CLASS_ZH.get(cls, CLASS_ZH["OTHER"]),
                        "lamp": x.get("lamp") or st["lamp"], "where": (x.get("file") or "") + (f":{x['line']}" if x.get("line") else ""),
                        "owner": owner_of(x.get("file") or ""), "detail": x.get("detail", "")})
    return out


def aggregate(stations: dict) -> str:
    lamps = [s["lamp"] for s in stations.values()]
    return "RED" if "RED" in lamps else ("YELLOW" if "YELLOW" in lamps else "GREEN")


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a == ["--selftest"]:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[DENY] 只收 VCGC 呼叫(via-vcgc run CGC_MDL263_Precheck)")
        return 2
    only = next((a[i + 1].split(",") for i, x in enumerate(a) if x == "--only" and i + 1 < len(a)), None)
    skip = next((a[i + 1].split(",") for i, x in enumerate(a) if x == "--skip" and i + 1 < len(a)), [])
    stations = {}
    for key, name, args, parser in STATIONS:
        if (only and key not in only) or key in skip:
            continue
        print(f"  … {name}", flush=True)
        st = run_station(key, args, parser)
        st["name"] = name
        stations[key] = st
        print(f"    [{st['lamp']:<6}] rc {st['rc']:<3} {st['secs']:>6}s · {st['summary']}", flush=True)
    findings = number_findings(stations)
    overall = aggregate(stations)
    rep = {"engine": ENGINE, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "overall": overall,
           "stations": {k: {kk: v for kk, v in s.items() if kk != "findings"} | {"n_findings": len(s["findings"])} for k, s in stations.items()},
           "findings": findings,
           "by_owner": {o: sum(1 for f in findings if f["owner"] == o) for o in sorted({f["owner"] for f in findings})},
           "by_class": {c: sum(1 for f in findings if f["class"] == c) for c in sorted({f["class"] for f in findings})}}
    d = VIA / "VIA_Reports" / "precheck"
    d.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for name in (f"PRECHECK_{stamp}.json", "PRECHECK_latest.json"):
        (d / name).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n  ===== [via_precheck] 發現(依歸屬)=====")
    for o, n in sorted(rep["by_owner"].items(), key=lambda kv: -kv[1]):
        print(f"  {o:<34} {n:>4} 條")
        for f in [x for x in findings if x["owner"] == o][:6]:
            print(f"     {f['id']} [{f['lamp']:<6}] {f['class']:<8} {f['where'][:70]:<70} {f['detail'][:70]}")
    if "--json" in a:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    print(f"\n[via_precheck] {overall} · 站 {len(stations)} · 發現 {len(findings)} · 類 {rep['by_class']} · 報告 VIA_Reports/precheck/PRECHECK_latest.json")
    return {"GREEN": 0, "YELLOW": 2}.get(overall, 1)


def selftest() -> int:
    res = []

    def chk(name, cond, note=""):
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:200]}" if note and not cond else ""))

    chk("① 歸屬:VRN / VDF / 收容件 / VCGC / 其他子系統 / 舊 PS",
        owner_of("functional modules/VRN/VRN_ENG112_x_v0100.py").startswith("VRN")
        and owner_of("functional modules/VDF/engine/VDF_ENG1_v0100.py").startswith("VDF")
        and owner_of("supportive modules/intake/X/a.py").startswith("凍結")
        and owner_of("supportive modules/registry/CGC_MDL244_A_v0100.py") == "VCGC"
        and owner_of("functional modules/ChipWar/engines/x.py") == "ChipWar 子系統"
        and owner_of("Invoke-VIA-X.ps1").startswith("操作員"))
    chk("② 薄尾前版釘 = 設計;跨族釘 = 風險",
        is_tail_prior_pin("functional modules/VDF/VDF_MDL012_FetchGroups_v0103.py", "字串釘死版號當路徑用:VDF_MDL012_FetchGroups_v0102.py")
        and not is_tail_prior_pin("functional modules/VDF/VDF_SystemManager_v0128.py", "字串釘死版號當路徑用:VDF_MDL008_FetchSystem_v0100.py"))
    lamp, summ, f = p_bridge(0, "[橋掃] 四系總表 VDF/accel 138/138 (100.0%) · VDF/net 137/138 (99%) · ALL/accel 1796/1796")
    chk("③ 覆蓋率:任一 < 100% = 黃並列出", lamp == "YELLOW" and len(f) == 1 and "137/138" in f[0]["detail"], (lamp, f))
    lamp, summ, f = p_celer(1, "  [PY ] 掃描面 3390 · 帶橋 3366 · 缺 1\n   · 缺橋 functional modules/VRN/VRN_NewPlugins_v0102.py\n  [PS ] 掃描面 1045 · 既有債 50(L70) · **基線外新缺 0**")
    chk("④ 政策閘:缺橋定位到檔 · 既有債黃 · 新缺 0 不紅", lamp == "YELLOW" and f[0]["file"].endswith("VRN_NewPlugins_v0102.py") and len(f) == 2, (lamp, f))
    lamp, summ, f = p_number(0, "[編號只增稽核] YELLOW · 列 1 → 2 · 遺失 0 · 改身分 0 · 重號 0 · 冊內不一致 1")
    chk("⑤ 編號稽核:遺失 / 改身分 / 重號 = 紅;冊內不一致 = 黃", lamp == "YELLOW" and len(f) == 1, (lamp, f))
    lamp, summ, f = p_number(0, "遺失 0 · 改身分 2 · 重號 0")
    chk("⑥ 改身分 > 0 = 紅", lamp == "RED")
    lamp, summ, f = p_handoff(1, "[RED] EVIDENCE_INVALID {'id': 'VRN-REQ008:x', 'why': ['t']}\n[RED] MODULE_UNREGISTERED functional modules/VDF/engine/VDF_ENG234_UiLauncher_v0100.py\n[YELLOW] REQ_CHANGED VCGC-REQ1")
    chk("⑦ 交接閘:收據 / 未登分類,REQ_CHANGED 不計", lamp == "RED" and [x["cls"] for x in f] == ["EVIDENCE", "UNREG"] and f[1]["file"].endswith("v0100.py"), f)
    lamp, summ, f = p_test(0, "  [YELLOW] V-handoff-check                    rc 1      7.2s · 教訓\n[VCGC 全功能串測] YELLOW · 站 9(綠 8 · 黃 1 · 紅 0)· x")
    chk("⑧ 串測:黃站定位", lamp == "YELLOW" and f and f[0]["file"] == "V-handoff-check", (lamp, f))
    st = {"a": {"lamp": "GREEN", "findings": []}, "b": {"lamp": "YELLOW", "findings": [{"cls": "SYSEXE", "file": "supportive modules/registry/CGC_MDL244_A_v0100.py", "line": 74, "detail": "x"}]}}
    nf = number_findings(st)
    chk("⑨ 編號 PC-### · 類說明 · 位置檔:行 · 歸屬", nf[0]["id"] == "PC-001" and nf[0]["where"].endswith(":74") and nf[0]["owner"] == "VCGC" and "sys.executable" in nf[0]["class_zh"], nf)
    chk("⑩ 彙總:有紅 = RED · 有黃 = YELLOW · 全綠 = GREEN", aggregate(st) == "YELLOW" and aggregate({"x": {"lamp": "RED"}, "y": {"lamp": "GREEN"}}) == "RED")
    chk("⑪ 站表 13 類全在(token · bridge · celer · ast · sync · number · ssot · sdd · handoff · test · rungate · matrix · temp)",
        {k.split("_")[0] for k, *_ in STATIONS} == {"token", "bridge", "celer", "ast", "sync", "number", "ssot", "sdd", "handoff", "test", "rungate", "matrix", "temp"})
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 加速器橋 · 網路工具橋在(__future__ 之後)· 不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src and src.index("from __future__") < src.index("[VIA:ACCEL-BRIDGE:v0100]")
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    ok = sum(res)
    print(f"[計] {ENGINE} 自測 {ok}/{len(res)} · {'PASS' if ok == len(res) else 'FAIL'}")
    return 0 if ok == len(res) else 1


if __name__ == "__main__":
    raise SystemExit(main())
