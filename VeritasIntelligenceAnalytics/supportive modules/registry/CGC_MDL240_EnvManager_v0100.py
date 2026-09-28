#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL240_EnvManager v0100 — ENV MANAGER:上下所有 LIB 與環境布建一次總檢(只查不裝;一個總判)

操作員 2026-09-28:「ENV MANAGER 理應自動檢查上下所有 LIBS 跟環境都有布建完畢 尤其是加速器 網路工具等輔助工具常被忽略」。
量過(R26 盤點):檢查器都在,但散在七支、沒有一個總判;Sweep 與操作台都沒跑它們。本支**不另立尺**(L05),逐支委派正主,
把各自的結果收成同一張表(GREEN / AMBER / RED / NODATA),寫 VIA_Reports/env_manager/ENVMGR_latest.json:

  Ⓐ 輔助工具(最常被忽略,判紅):
     ① 四件工具鎖版號 · sha ........ CGC_MDL233_ToolActivate 尾版 status(accelerator · network · layout · nlp)
     ② 加速器載得起來 .............. SUP_MDL737_SuperAccelModule 尾版自測(載的是鎖冊那一份本體)
     ③ 網路工具載得起來 ............ SUP_MDL740_NetUnified 尾版 --selftest(_aegis() 載鎖定核心)
     ④ LAYOUT / ⑤ NLP 載得起來 ..... 鎖冊指名那一支 --selftest
     ⑥ 加速器 / 網路 註冊 · 覆蓋 .... CGC_MDL230_ToolCoverageProbe 尾版 probe --plain(總判)
  Ⓑ 環境與 LIB:
     ⑦ 家族 python 與必備 LIB ....... CGC_MDL137_RunGate 尾版 probe --json(vdf · vrn · vap 各用自己的境匯入)
     ⑧ 各境工具冊 ................... CGC_MDL135_EnvGovernance 尾版 tools --sheet-only(VIA_ToolRoster_SSOT;缺的寫成一貼即用 .ps1)
     ⑨ 鏈上報過的缺件 ............... VDF / VRN 鏈最近一次 JSON 裡「缺件 <套件>」(常被忽略:工具冊沒列的也抓得到,例 pydantic)
     ⑩ 外部執行檔 ................... git · pwsh 必備;node · npm · uv · tesseract · java · pandoc 選配(PATH 上找得到才算)
  Ⓒ PowerShell 端(操作台 PS 寫進 PS_SIDE_latest.json 才有):PS 版本 ≥ 7 · Celeritas PS7 已套且版號 = 鎖冊 · Invoke-VIAPython 在位

**只查不裝**:本支永不帶 --apply / --approve / --approve-install(自測有一檢量這件事);缺的只給補法(補是操作員的手,L10;
要網路的裝件還要操作員自己開同意閘,L07/L08)。總判:任一 Ⓐ 紅 = RED;其餘有缺 = AMBER;rc 0 = GREEN · 2 = AMBER/NODATA · 1 = RED。
只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。用法:python3 CGC_MDL240_EnvManager_v0100.py [check] [--json] | --selftest
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

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
SUPP = VIA / "supportive modules"
REPORTS = VIA / "VIA_Reports"
OUT = REPORTS / "env_manager"
ENGINE = Path(__file__).stem
LOCK = HERE / "VIA_ToolVersion_Lock_v0100.json"
CHAINS = (("VDF", REPORTS / "vdf_chain" / "VDFCHAIN_latest.json"), ("VRN", REPORTS / "vrn_chain" / "VRNCHAIN_latest.json"))
REQUIRED_EXE = ("git", "pwsh")
OPTIONAL_EXE = ("node", "npm", "uv", "tesseract", "java", "pandoc")
FORBIDDEN_FLAGS = ("--apply", "--approve", "--approve-install", "--execute")
MISSING_RX = re.compile(r"缺件\s*([A-Za-z][A-Za-z0-9_.\-]*)")
ORDER = {"RED": 0, "AMBER": 1, "NODATA": 2, "GREEN": 3}


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


def tail(folder: Path, stem: str) -> Path | None:
    hits = sorted(folder.glob(stem + "_v*.py"), key=_vnum)
    return hits[-1] if hits else None


def run(argv: list, timeout: int = 300) -> dict:
    """One delegated check: the owner's own CLI, read-only flags only; rc + text + seconds."""
    bad = [a for a in argv if str(a) in FORBIDDEN_FLAGS]
    if bad:
        return {"rc": None, "out": f"拒跑:帶了寫入 / 安裝旗標 {bad}(本支只查不裝)", "secs": 0.0}
    env = dict(os.environ, VIA_FROM_VCGC="YES", VIA_VCGC_PUSH="NO", VIA_NO_OPEN="1", PYTHONIOENCODING="utf-8")
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable] + [str(a) for a in argv], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, env=env, cwd=str(VIA))
        return {"rc": p.returncode, "out": (p.stdout or "") + (p.stderr or ""), "secs": round(time.time() - t0, 1)}
    except subprocess.TimeoutExpired:
        return {"rc": None, "out": f"逾 {timeout}s", "secs": round(time.time() - t0, 1)}
    except OSError as exc:
        return {"rc": None, "out": f"起不來 {type(exc).__name__}", "secs": 0.0}


def _row(group, item, state, note, fix="", secs=0.0, cid=""):
    return {"id": cid, "group": group, "item": item, "state": state, "note": note, "fix": fix, "secs": secs}


def _lock() -> dict:
    try:
        return json.loads(LOCK.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


# ---------------------------------------------------------------- parsers (pure; selftest feeds them samples)

def parse_tools_lock(rc, out: str) -> list:
    m = re.search(r"\{.*\}", out, re.S)
    try:
        data = json.loads(m.group(0)) if m else {}
    except ValueError:
        data = {}
    rows = []
    for t in data.get("tools") or []:
        ok = bool(t.get("sha_ok"))
        wait = t.get("waiting") or []
        rows.append(_row("Ⓐ 輔助工具", f"① 鎖版號 · {t.get('family')}", "GREEN" if ok else "RED",
                         f"{t.get('pinned') or t.get('version')} · sha {'對' if ok else '不對'}" + (f" · 新版待啟用 {len(wait)}" if wait else ""),
                         "" if ok else "via-vcgc tools 看差在哪;換版走 CGC_MDL233 activate(操作員 --apply)", cid="A1"))
    if not rows:
        rows.append(_row("Ⓐ 輔助工具", "① 鎖版號(四件工具)", "RED", f"讀不到 CGC_MDL233 status 的結果(rc {rc})", "via-vcgc tools", cid="A1"))
    return rows


def parse_selftest(rc, out: str) -> tuple:
    """(state, note) of a selftest: rc 0 and no [FAIL] line = GREEN; missing-package words = NODATA; otherwise RED."""
    fails = [x.strip() for x in out.splitlines() if re.match(r"\s*\[FAIL\]", x)]
    tally = ([x.strip() for x in out.splitlines() if re.search(r"\[計\]", x)] or [""])[-1]
    if rc == 0 and not fails:
        return "GREEN", tally[:120] or "自測過"
    if MISSING_RX.search(out) or "ModuleNotFoundError" in out:
        return "NODATA", "缺件:" + ", ".join(sorted(set(MISSING_RX.findall(out))))[:120]
    return "RED", (fails[0] if fails else f"rc {rc} · " + out.strip()[-120:])[:160]


def parse_coverage(rc, out: str) -> tuple:
    m = re.search(r"總判\s+([A-Z]+)", out)
    v = m.group(1) if m else ("RED" if rc else "NODATA")
    return {"GREEN": "GREEN", "AMBER": "AMBER", "YELLOW": "AMBER", "RED": "RED"}.get(v, "NODATA"), (m.group(0) if m else f"rc {rc}")


def parse_rungate(rc, out: str) -> list:
    m = re.search(r"\{.*\}", out, re.S)
    try:
        data = json.loads(m.group(0)) if m else {}
    except ValueError:
        data = {}
    rows = []
    for fam, f in (data.get("families") or {}).items():
        py = f.get("python") or {}
        v = str(f.get("verdict") or "")
        state = {"GREEN": "GREEN", "YELLOW": "AMBER", "RED": "RED"}.get(v, "NODATA")
        miss = [k for k, x in (f.get("libs") or {}).items() if isinstance(x, dict) and not x.get("ok", True)]
        note = f"{py.get('state', '?')} · {py.get('python', '?')}" + (f" · 缺 {', '.join(miss[:6])}" if miss else "")
        rows.append(_row("Ⓑ 環境與 LIB", f"⑦ 家族境 · {fam}", state, note, "" if state == "GREEN" else str(py.get("hint") or "via-rungate probe")[:160],
                         cid="B7"))
    if not rows:
        rows.append(_row("Ⓑ 環境與 LIB", "⑦ 家族境", "NODATA", f"RunGate 沒給結果(rc {rc})", "via-rungate probe", cid="B7"))
    return rows


def parse_roster(rc, out: str) -> tuple:
    m = re.search(r"\[工具冊\]\s*(\{[^}]*\})", out)
    counts = m.group(1) if m else ""
    plan = "VIA_Reports/env_governance/TOOLS_PLAN_latest.ps1"
    if rc == 0:
        return "GREEN", f"各境工具齊 {counts}", ""
    if "ENV_ABSENT" in counts and not re.search(r"BROKEN|CONFLICT", counts):
        return "AMBER", f"境還沒建 {counts}", f"補法寫在 {plan}(一貼即用;裝件是操作員的手)"
    if counts:
        return "RED" if re.search(r"BROKEN|CONFLICT", counts) else "AMBER", counts, f"看 {plan}"
    return "NODATA", f"rc {rc} · 讀不到工具冊結果", "via-envgov tools"


def chain_missing(paths=CHAINS) -> dict:
    """Packages the latest chain runs reported as missing (缺件 <pkg>), with the stage that needed them."""
    found = {}
    for fam, p in paths:
        try:
            d = json.loads(Path(p).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for st in d.get("stages") or []:
            for pkg in MISSING_RX.findall(str(st.get("detail") or "")):
                found.setdefault(pkg, []).append(f"{fam} {st.get('name')}")
    return found


def exe_rows(which=shutil.which, ps_side: dict | None = None) -> list:
    rows = []
    ps7 = bool(ps_side) and str(ps_side.get("ps_version", "0")).split(".")[0].isdigit() and int(str(ps_side.get("ps_version")).split(".")[0]) >= 7
    for exe in REQUIRED_EXE + OPTIONAL_EXE:
        hit = which(exe) or (f"PS 端正在用 PowerShell {ps_side.get('ps_version')} 跑" if exe == "pwsh" and ps7 else None)
        req = exe in REQUIRED_EXE
        rows.append(_row("Ⓑ 環境與 LIB", f"⑩ 執行檔 · {exe}" + ("(必備)" if req else ""),
                         "GREEN" if hit else ("RED" if req else "AMBER"), hit or "PATH 上找不到",
                         "" if hit else ("必備:裝好並放進 PATH" if req else "選配:用到的功能才需要"), cid="B10"))
    return rows


def ps_rows(ps_side: dict | None, lock: dict) -> list:
    if not ps_side:
        return [_row("Ⓒ PowerShell 端", "PS 端檢查", "NODATA", "沒有 PS_SIDE_latest.json(從操作台 PowerShell 跑才有)",
                     ".\\VIA-OperatorConsole.ps1", cid="C")]
    rows = []
    maj = int(str(ps_side.get("ps_version", "0")).split(".")[0] or 0)
    rows.append(_row("Ⓒ PowerShell 端", "PowerShell ≥ 7", "GREEN" if maj >= 7 else "RED", str(ps_side.get("ps_version")),
                     "" if maj >= 7 else "裝 PowerShell 7 並用 pwsh 跑", cid="C1"))
    want = str((lock.get("accelerator") or {}).get("version") or "")
    got = str(ps_side.get("celeritas_version") or "")
    applied = bool(ps_side.get("celeritas_applied"))
    ok = applied and (not want or want.lstrip("v") == got.lstrip("v"))
    rows.append(_row("Ⓒ PowerShell 端", "加速器 Celeritas PS7 已套 · 版號 = 鎖冊", "GREEN" if ok else "RED",
                     f"PS7 {got or '未載'} · 鎖冊 {want or '?'} · Applied {applied}",
                     "" if ok else "supportive modules\\ps7\\VeritasCeleritas.PS7.ps1 要在;版號要跟鎖冊一致", cid="C2"))
    for key, zh, need in (("invoke_viapython", "Invoke-VIAPython 在位(中央呼叫口)", True),
                          ("celeritas_scoped", "Invoke-VIACeleritasScoped 在位(每步包加速器)", False)):
        have = bool(ps_side.get(key))
        rows.append(_row("Ⓒ PowerShell 端", zh, "GREEN" if have else ("RED" if need else "AMBER"), "在" if have else "不在",
                         "" if have else "載 Register-VIA-Commands 尾版 / VIA_PS_PyProgress_Module.ps1", cid="C3"))
    return rows


# ---------------------------------------------------------------- the check

def check(runner=run, which=shutil.which, ps_side: dict | None = None, chains=CHAINS) -> dict:
    rows = []
    lock = _lock()
    t233 = tail(HERE, "CGC_MDL233_ToolActivate")
    r = runner([t233, "status"], 60) if t233 else {"rc": None, "out": "", "secs": 0}
    rows += [dict(x, secs=r["secs"]) for x in parse_tools_lock(r["rc"], r["out"])]
    loaders = [("② 加速器載入(SUP_MDL737 尾版)", tail(SUPP, "SUP_MDL737_SuperAccelModule"), []),
               ("③ 網路工具載入(SUP_MDL740 尾版)", tail(SUPP / "network", "SUP_MDL740_NetUnified"), ["--selftest"])]
    for fam, zh in (("layout", "④ LAYOUT 載入"), ("nlp", "⑤ NLP 載入")):
        p = (lock.get(fam) or {}).get("path")
        loaders.append((f"{zh}({Path(p).name if p else '鎖冊沒這家'})", (VIA.parent / p) if p else None, ["--selftest"]))  # lock paths are repo-root relative
    for zh, path, args in loaders:
        if path is None or not Path(path).exists():
            rows.append(_row("Ⓐ 輔助工具", zh, "RED", "檔不在", "git pull;鎖冊指名的檔要在", cid="A2"))
            continue
        r = runner([path] + args, 180)
        st, note = parse_selftest(r["rc"], r["out"])
        rows.append(_row("Ⓐ 輔助工具", zh, "RED" if st == "NODATA" else st, note, "" if st == "GREEN" else f"python \"{path.name}\" {' '.join(args)}",
                         r["secs"], cid="A2"))
    t230 = tail(HERE, "CGC_MDL230_ToolCoverageProbe")
    if t230:
        r = runner([t230, "probe", "--plain"], 300)
        st, note = parse_coverage(r["rc"], r["out"])
        rows.append(_row("Ⓐ 輔助工具", "⑥ 加速器 / 網路 註冊 · 覆蓋(CGC_MDL230)", st, note,
                         "" if st == "GREEN" else "看 VIA_Reports/toolprobe/TOOLPROBE_latest.json 的待辦", r["secs"], cid="A6"))
    t137 = tail(HERE, "CGC_MDL137_RunGate")
    if t137:
        r = runner([t137, "probe", "--json", "--quiet"], 300)
        rows += [dict(x, secs=r["secs"]) for x in parse_rungate(r["rc"], r["out"])]
    t135 = tail(HERE, "CGC_MDL135_EnvGovernance")
    if t135:
        r = runner([t135, "tools", "--sheet-only"], 300)
        st, note, fix = parse_roster(r["rc"], r["out"])
        rows.append(_row("Ⓑ 環境與 LIB", "⑧ 各境工具冊(VIA_ToolRoster_SSOT)", st, note, fix, r["secs"], cid="B8"))
    miss = chain_missing(chains)
    if miss:
        for pkg, where in sorted(miss.items()):
            rows.append(_row("Ⓑ 環境與 LIB", f"⑨ 鏈上缺件 · {pkg}", "AMBER", "要它的站:" + "、".join(where[:4]),
                             f"裝進該家族境(你的手):via-rungate --family vrn --approve-install 或 pip install {pkg}", cid="B9"))
    else:
        rows.append(_row("Ⓑ 環境與 LIB", "⑨ 鏈上缺件", "GREEN" if any(Path(p).exists() for _, p in chains) else "NODATA",
                         "最近一次鏈跑沒有缺件" if any(Path(p).exists() for _, p in chains) else "還沒跑過鏈", cid="B9"))
    rows += exe_rows(which, ps_side)
    rows += ps_rows(ps_side, lock)
    worst_a = min((ORDER[r["state"]] for r in rows if r["group"].startswith("Ⓐ")), default=3)
    worst = min((ORDER[r["state"]] for r in rows), default=3)
    verdict = "RED" if worst_a == 0 or worst == 0 else ("AMBER" if worst <= 2 else "GREEN")
    tally = {}
    for x in rows:
        tally[x["state"]] = tally.get(x["state"], 0) + 1
    return {"engine": ENGINE, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "verdict": verdict, "tally": tally, "rows": rows,
            "rule": "只查不裝:補法是操作員的手(L10);要網路的裝件先由操作員開同意閘(L07/L08)"}


def write(rep: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "ENVMGR_latest.json"
    p.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def _ps_side() -> dict | None:
    p = OUT / "PS_SIDE_latest.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return d if time.time() - p.stat().st_mtime < 3600 else None      # stale PS facts are not facts


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    rep = check(ps_side=_ps_side())
    p = write(rep)
    if "--json" in args:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        for r in rep["rows"]:
            print(f"  {r['state']:<6} │ {r['group']:<10} │ {r['item'][:44]:<44} │ {r['note'][:70]}")
            if r["fix"] and r["state"] != "GREEN":
                print(f"         └ 補法:{r['fix'][:140]}")
    print(f"[ENV MANAGER] 總判 {rep['verdict']} · " + " · ".join(f"{k} {v}" for k, v in sorted(rep["tally"].items())) + f" · JSON {p}")
    return {"GREEN": 0, "RED": 1}.get(rep["verdict"], 2)


def selftest() -> int:
    import tempfile
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE} · 自測(假委派,零子行程;另一檢真跑)===")
    out233 = '{"tools":[{"family":"accelerator","pinned":"v1141","sha_ok":true,"waiting":[]},' \
             '{"family":"network","pinned":"v1652","sha_ok":false,"waiting":["x"]}],"next":"none"}'
    r = parse_tools_lock(2, out233)
    chk("① 四件工具鎖:sha 對 = 綠、不對 = 紅(一家一列)", [x["state"] for x in r] == ["GREEN", "RED"])
    chk("②③④⑤ 自測判讀:rc 0 無 [FAIL] = 綠;有 [FAIL] = 紅;缺件 = NODATA(工具類再升紅)",
        parse_selftest(0, "  [OK] a\n  [計] 9/9")[0] == "GREEN" and parse_selftest(1, "  [FAIL] x\n")[0] == "RED"
        and parse_selftest(1, "缺件 paddleocr(ModuleNotFoundError)")[0] == "NODATA")
    chk("⑥ 覆蓋總判照正主(AMBER = 黃)", parse_coverage(0, "[ToolProbe] plain · 總判 AMBER · 待辦 2")[0] == "AMBER")
    rg = parse_rungate(0, json.dumps({"families": {"vrn": {"verdict": "YELLOW", "python": {"state": "BASE_FALLBACK", "python": "/x", "hint": "建境"}}}}))
    chk("⑦ RunGate YELLOW = 黃並帶補法", rg[0]["state"] == "AMBER" and rg[0]["fix"] == "建境")
    chk("⑧ 工具冊:只是境還沒建 = 黃(補法指向一貼即用 .ps1);BROKEN = 紅",
        parse_roster(2, "[工具冊] {'ENV_ABSENT': 32} · 段 8")[0] == "AMBER" and parse_roster(2, "[工具冊] {'BROKEN': 1}")[0] == "RED")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "c.json"
        p.write_text(json.dumps({"stages": [{"name": "VRN_ENG073", "detail": "缺件 pydantic(ModuleNotFoundError)"},
                                            {"name": "VRN_ENG057", "detail": "缺件 paddleocr(x)"}]}), encoding="utf-8")
        cm = chain_missing((("VRN", p),))
    chk("⑨ 鏈上缺件收得到(工具冊沒列的 pydantic 也抓到)", set(cm) == {"pydantic", "paddleocr"}, ", ".join(sorted(cm)))
    ex = {x["item"]: x["state"] for x in exe_rows(lambda e: "/bin/" + e if e in ("git", "node") else None)}
    ex2 = {x["item"]: x["state"] for x in exe_rows(lambda e: None, {"ps_version": "7.4.6"})}
    chk("⑩ 執行檔:必備缺 = 紅、選配缺 = 黃;PS 端回報 PS7 在跑 = pwsh 算在", ex["⑩ 執行檔 · pwsh(必備)"] == "RED"
        and ex["⑩ 執行檔 · uv"] == "AMBER" and ex["⑩ 執行檔 · git(必備)"] == "GREEN" and ex2["⑩ 執行檔 · pwsh(必備)"] == "GREEN")
    lock = {"accelerator": {"version": "v1141"}}
    good = {r["item"]: r["state"] for r in ps_rows({"ps_version": "7.4.6", "celeritas_version": "v1141", "celeritas_applied": True,
                                                    "invoke_viapython": True, "celeritas_scoped": False}, lock)}
    bad = {r["item"]: r["state"] for r in ps_rows({"ps_version": "5.1", "celeritas_version": "v1140", "celeritas_applied": True,
                                                   "invoke_viapython": True}, lock)}
    chk("Ⓒ PS 端:PS7 · 加速器版號 = 鎖冊才綠;PS5 或版號不一 = 紅", good["加速器 Celeritas PS7 已套 · 版號 = 鎖冊"] == "GREEN"
        and bad["PowerShell ≥ 7"] == "RED" and bad["加速器 Celeritas PS7 已套 · 版號 = 鎖冊"] == "RED")
    calls = []

    def fake(argv, timeout=0):
        calls.append([str(a) for a in argv])
        name = Path(str(argv[0])).name
        if name.startswith("CGC_MDL233"):
            return {"rc": 0, "out": out233.replace("false", "true"), "secs": 0.1}
        if name.startswith("CGC_MDL137"):
            return {"rc": 0, "out": json.dumps({"families": {"vdf": {"verdict": "GREEN", "python": {"state": "OK"}}}}), "secs": 0.1}
        if name.startswith("CGC_MDL135"):
            return {"rc": 0, "out": "[工具冊] {'OK': 8}", "secs": 0.1}
        if name.startswith("CGC_MDL230"):
            return {"rc": 0, "out": "總判 GREEN", "secs": 0.1}
        return {"rc": 0, "out": "  [OK] x\n  [計] 3/3", "secs": 0.1}

    with tempfile.TemporaryDirectory() as td:
        clean = Path(td) / "chain.json"
        clean.write_text(json.dumps({"stages": [{"name": "x", "detail": "[計] 3/3"}]}), encoding="utf-8")
        rep = check(runner=fake, which=lambda e: "/bin/" + e, ps_side={"ps_version": "7.4", "celeritas_version": "v1141",
                    "celeritas_applied": True, "invoke_viapython": True, "celeritas_scoped": True}, chains=(("VRN", clean),))
    chk("總判:全綠 = GREEN(八支正主都有委派:233 · 737 · 740 · 743 · 866 · 230 · 137 · 135)", rep["verdict"] == "GREEN" and len(calls) == 8,
        f"{rep['verdict']} · 委派 {len(calls)}")
    chk("只查不裝:委派的每一句都不帶 --apply / --approve / --approve-install / --execute",
        not any(a in FORBIDDEN_FLAGS for c in calls for a in c) and run(["x.py", "--apply"])["rc"] is None)

    def fake_red(argv, timeout=0):
        if Path(str(argv[0])).name.startswith("SUP_MDL740"):
            return {"rc": 1, "out": "  [FAIL] _aegis() loads the pinned core", "secs": 0.1}
        return fake(argv, timeout)

    rep2 = check(runner=fake_red, which=lambda e: "/bin/" + e, ps_side=None, chains=())
    chk("網路工具載不起來 = 總判 RED(輔助工具不准被黃蓋掉)", rep2["verdict"] == "RED")
    real = run([tail(HERE, "CGC_MDL233_ToolActivate"), "status"], 60)
    chk("真跑一支正主(CGC_MDL233 status)讀得懂", any(x["state"] in ("GREEN", "RED") for x in parse_tools_lock(real["rc"], real["out"]))
        and len(parse_tools_lock(real["rc"], real["out"])) >= 4, f"rc {real['rc']}")
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    try:
        chk("不經 VCGC 就拒跑", main(["check"]) == 2)
    finally:
        if keep is not None:
            os.environ["VIA_FROM_VCGC"] = keep
    ok = all(results)
    print(f"  [計] {len(results)} 檢 OK {sum(results)} · FAIL {len(results) - sum(results)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
