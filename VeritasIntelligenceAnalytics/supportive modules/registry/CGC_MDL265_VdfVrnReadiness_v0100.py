#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL265_VdfVrnReadiness v0100 — VCGC 母系統監控:VRN / VDF 工具與環境檢查(可修)· PY / PS 加速器 · VDF 網路工具覆蓋 · 衝突提醒

操作員令(2026-10-05):「via_activate_vdf ……原始指令用 py 寫並加入加速器;啟動 vcgc 對 vrn vdf 所有工具及環境檢查及修復 ·
  確認所有 py ps 指令都加速器 · vdf 都有加網路工具」;同日裁定「vcgc vdf vrn 為獨立系統 · vdf 啟動指令由 vdf manager 控管」
  「權力下放子系統 · 母系統監控及衝突提醒全力 · 更改由我跟你定案」(VCGC-REQ170)。
所以本支只做母系統那一段(VDF 讀庫 / 啟動前改 / U/I 歸 VDF_SystemManager activate,本支不碰):
  ① vcgc      省 Token 工具卡(工具經鎖冊啟用 · 實測過;紅 = VCGC 本身停)
  ② env       RunGate probe --family vdf / vrn(家族境真跑)· EnvGovernance lkgc status(你測過全綠時存的版本鎖)
  ③ repair    不綠才修,而且要 --repair:LKGC 可用 → rollback(照鎖重建 via_* 隔離境,不刪 base);
              不可用 → RunGate run --approve-install(只補缺件)。安裝要連網 = 雙閘(操作員的手,本支只讀永不代設);沒開 = GATED 照實說
  ④ coverage  CGC_MDL263 precheck 的 bridge · celer · accel 三站:PY 加速器 · VDF 網路工具 · PS 模板章 · 25 加速器控制面
              (子系統檔的紅依 L111 記歸屬 = 黃 + 衝突提醒,由子系統修;VCGC / VDF 範圍的紅才算紅)
用法:via-vcgc run CGC_MDL265_VdfVrnReadiness [--repair] [--only 步,步] [--json] · --selftest
報告:VIA_Reports/activate_vdf/READINESS_latest.json。rc:0 全綠 · 2 有黃 · 1 有紅。不碰 TA-Lib;不改 VDF / VRN 正本(L111)。
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
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ENGINE = Path(__file__).stem
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT_DIR = VIA / "VIA_Reports" / "activate_vdf"
TIMEOUT = int(os.environ.get("VIA_ACTIVATE_TIMEOUT") or 1800)
FAMILIES = ("vdf", "vrn")                       # RunGate --family 只收 vdf|vrn|vap;本令管 VDF + VRN
STEPS = ("vcgc", "env", "repair", "coverage")
NOISE = re.compile(r"^\s*\[(位階|加速|環境計畫|回覆|衝突|還原|分群|不衝突|靜態|教訓|沿用)\]|^\[(政策|監控|第一步|步驟|流程)\]|via-vcgc run\] \[流程\]")
L111_OWNER = (("functional modules/VRN/", "VRN"), ("supportive modules/70_VRN_Rules/", "VRN"),
              ("functional modules/VDF/", "VDF"), ("functional modules/VAP/", "VAP"))


def console() -> Path:
    return sorted(HERE.glob("CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"))[-1]


def run_vcgc(args: list, timeout: int = TIMEOUT) -> tuple:
    """經 VCGC 唯一入口跑一個動作;回 (rc, 輸出, 秒)。逾時 = rc 124(不中斷整輪)。"""
    env = dict(os.environ, VIA_FROM_VCGC="YES", PYTHONUTF8="1")
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, str(console())] + [str(a) for a in args], cwd=str(VIA), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env)
        return p.returncode, p.stdout + p.stderr, round(time.time() - t0, 1)
    except subprocess.TimeoutExpired as e:
        return 124, (e.stdout or "") if isinstance(e.stdout, str) else "", round(time.time() - t0, 1)


def clean(out: str) -> list:
    return [ln for ln in out.splitlines() if ln.strip() and not NOISE.search(ln)]


def where_of(f: dict) -> str:
    """precheck 發現的位置欄是 where(檔:行);舊格式 file 也認。"""
    return str(f.get("where") or f.get("file") or "").rsplit(":", 1)[0] if re.search(r":\d+$", str(f.get("where") or f.get("file") or "")) else str(f.get("where") or f.get("file") or "")


def finding_owner(f: dict) -> str:
    """歸屬:precheck 已判的 owner(含 L111 標記)優先;沒有才看路徑。"""
    o = str(f.get("owner") or "")
    for who in ("VRN", "VDF", "VAP"):
        if o.startswith(who):
            return who
    return owner_of(where_of(f)) if not o else ("VCGC" if o.startswith("VCGC") else owner_of(where_of(f)))


def owner_of(rel: str) -> str:
    rel = str(rel).replace("\\", "/")
    for pre, who in L111_OWNER:
        if rel.startswith(pre):
            return who
    return "VCGC"


def consent_open() -> bool:
    """雙閘只讀不寫(AI 永不代設):VIA_NET_CONSENT=YES 且 VIA_SCRAPE_CONSENT 有開。"""
    return os.environ.get("VIA_NET_CONSENT") == "YES" and os.environ.get("VIA_SCRAPE_CONSENT", "OFF") not in ("", "OFF")




# ---------- 解析(純函式,自測可餵假輸出) ----------
def p_token(rc: int, out: str) -> tuple:
    m = re.search(r"已啟用 (\d+)/(\d+)", out)
    ok = rc == 0 and m and m.group(1) == m.group(2)
    return ("GREEN" if ok else "RED"), (m.group(0) if m else f"rc {rc}")


def p_rungate(rc: int, out: str) -> tuple:
    m = re.search(r"\[via-rungate\] 判定 (GREEN|YELLOW|RED)", out)
    lamp = m.group(1) if m else ("RED" if rc not in (0, 2) else "YELLOW")
    if rc not in (0,) and lamp == "GREEN":
        lamp = "YELLOW"
    return lamp, (f"RunGate {lamp}" + ("" if m else f" · rc {rc}"))


def p_lkgc(rc: int, out: str) -> dict:
    m = re.search(r"\[LKGC\] latest (\S+) · verdict (\w+)", out)
    return {"latest": m.group(1) if m else None, "verdict": m.group(2) if m else None, "eligible": bool(m and m.group(2) == "GREEN"), "rc": rc}


def p_coverage(report: dict) -> tuple:
    """precheck 報告(bridge · celer · accel)→ (lamp, 摘要, 紅黃發現依歸屬)。VCGC / VDF 範圍內有紅才 RED;子系統的紅 = YELLOW 附歸屬(L111)。"""
    st = report.get("stations") or {}
    fnd = [f for f in report.get("findings") or [] if f.get("lamp") in ("RED", "YELLOW")]
    own_red = [f for f in fnd if f.get("lamp") == "RED" and finding_owner(f) in ("VCGC", "VDF")]
    other = [f for f in fnd if f not in own_red]
    lamps = [v.get("lamp") for v in st.values()]
    if not st:
        return "RED", "precheck 報告沒有站(沒跑成)", fnd
    lamp = "RED" if own_red or "RED" in lamps and not fnd else ("YELLOW" if other or "YELLOW" in lamps or "RED" in lamps else "GREEN")
    summ = " · ".join(f"{k} {v.get('lamp')}" for k, v in st.items())
    m = re.search(r"ALL/accel (\d+)/(\d+)", (st.get("bridge") or {}).get("summary", ""))
    n = re.search(r"VDF/net (\d+)/(\d+)", (st.get("bridge") or {}).get("summary", ""))
    if m:
        summ += f" · PY 加速 {m.group(1)}/{m.group(2)}"
    if n:
        summ += f" · VDF 網路 {n.group(1)}/{n.group(2)}"
    return lamp, summ, fnd












def repair_plan(env_lamps: dict, lkgc: dict, gate: bool) -> list:
    """不綠的家族境 → 修法(只進 via_* 隔離境;不刪 base)。雙閘沒開 = GATED,只印命令。"""
    bad = [f for f, lamp in env_lamps.items() if lamp != "GREEN"]
    if not bad:
        return []
    if lkgc.get("eligible"):
        acts = [{"why": "LKGC 全綠存檔可用 → 照你測過的版本鎖重建隔離境", "argv": ["run", "CGC_MDL135_EnvGovernance", "rollback", "--to", "LKGC_latest.json", "--execute", "--approve"]}]
    else:
        acts = [{"why": f"LKGC 不可用(verdict {lkgc.get('verdict')})→ RunGate 只把缺件裝進 {f} 家族境", "argv": ["run", "CGC_MDL137_RunGate", "run", "--family", f, "--approve-install"]} for f in bad]
    for a in acts:
        a["state"] = "READY" if gate else "GATED"
    return acts


# ---------- 主流程 ----------
def stamp(rows: list, key: str, lamp: str, summary: str, sec: float = 0.0, **extra) -> dict:
    r = {"step": key, "lamp": lamp, "summary": summary, "sec": sec, **extra}
    rows.append(r)
    tag = f"[{lamp:<6}]"
    if sys.stdout.isatty():
        tag = "\033[" + {"GREEN": "32", "YELLOW": "33", "RED": "31"}.get(lamp, "36") + "m" + tag + "\033[0m"
    print(f"  {tag} {key:<9} {summary}" + (f" · {sec}s" if sec else ""), flush=True)
    return r


def readiness(repair: bool = False, only: set | None = None) -> dict:
    t0 = time.time()
    want = (lambda k: (not only) or k in only)
    rows: list = []
    print(f"=== VCGC 母系統監控 · {ENGINE} · VRN / VDF 工具 · 環境 · 加速器 / 網路工具覆蓋 ===", flush=True)

    if want("vcgc"):
        print("  [1/4] VCGC 啟動(省 Token 工具卡:工具經鎖冊啟用 · 實測過)", flush=True)
        rc, out, sec = run_vcgc(["token"], 600)
        lamp, summ = p_token(rc, out)
        stamp(rows, "vcgc", lamp, f"token {summ}", sec)

    env_lamps, lkgc = {}, {}
    if want("env") or want("repair"):
        print("  [2/4] 環境檢查(VDF · VRN 家族境 RunGate probe · LKGC 版本鎖)", flush=True)
        for fam in FAMILIES:
            rc, out, sec = run_vcgc(["run", "CGC_MDL137_RunGate", "probe", "--family", fam], 900)
            lamp, summ = p_rungate(rc, out)
            env_lamps[fam] = lamp
            stamp(rows, "env", lamp, f"{fam} {summ}", sec, family=fam)
        rc, out, sec = run_vcgc(["run", "CGC_MDL135_EnvGovernance", "lkgc", "status"], 600)
        lkgc = p_lkgc(rc, out)
        stamp(rows, "env", "GREEN" if lkgc.get("eligible") else "YELLOW",
              f"LKGC {lkgc.get('latest')} · verdict {lkgc.get('verdict')}(你測過全綠時存的版本鎖;非 GREEN = 修理改走 RunGate 補缺件)", sec, family="lkgc")

    if want("repair"):
        gate = consent_open()
        plan = repair_plan(env_lamps, lkgc, gate)
        if not plan:
            stamp(rows, "repair", "GREEN", "家族境都綠 → 不用修")
        elif not repair:
            stamp(rows, "repair", "YELLOW", f"有 {len(plan)} 項待修;加 --repair 才動手(只裝進 via_* 隔離境,不刪 base)", plan=plan)
        elif not gate:
            stamp(rows, "repair", "YELLOW", "GATED:安裝要連網,本視窗先開雙閘(操作員的手,本令永不代設):"
                  "$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES' → 再跑 via_activate_vdf --repair", plan=plan)
        else:
            done = []
            for act in plan:
                rc, out, sec = run_vcgc(act["argv"], TIMEOUT)
                act.update({"state": "DONE" if rc == 0 else "FAIL", "rc": rc, "sec": sec, "tail": clean(out)[-3:]})
                done.append(act)
            for fam in list(env_lamps):
                rc, out, sec = run_vcgc(["run", "CGC_MDL137_RunGate", "probe", "--family", fam, "--fresh"], 900)
                env_lamps[fam] = p_rungate(rc, out)[0]
            ok = all(a["state"] == "DONE" for a in done) and all(v == "GREEN" for v in env_lamps.values())
            stamp(rows, "repair", "GREEN" if ok else "RED", f"修理 {len(done)} 項 · 修後 RunGate {env_lamps}", plan=done)

    if want("coverage"):
        print("  [3/4] 覆蓋率(PY 加速器 · VDF 網路工具 · PS 模板 · 25 加速器控制面)", flush=True)
        rc, out, sec = run_vcgc(["run", "CGC_MDL263_Precheck", "--only", "bridge,celer,accel"], TIMEOUT)
        try:
            rep = json.loads((VIA / "VIA_Reports" / "precheck" / "PRECHECK_latest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            rep = {}
        lamp, summ, fnd = p_coverage(rep)
        by = {}
        for f in fnd:
            by.setdefault(finding_owner(f), []).append(f"{f.get('id')} {f.get('lamp')} {f.get('class') or f.get('cls')} {where_of(f) or f.get('detail', '')}")
        note = " · ".join(f"{k} {len(v)}" for k, v in by.items())
        stamp(rows, "coverage", lamp, summ + (f" · 黃紅歸屬 {note}(L111:子系統的由子系統修,VCGC 出資訊卡)" if note else ""), sec, findings=by)

    lamps = [r["lamp"] for r in rows]
    overall = "RED" if "RED" in lamps else ("YELLOW" if "YELLOW" in lamps else "GREEN")
    rep = {"engine": ENGINE, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "overall": overall,
           "repair": repair, "consent_open": consent_open(),
           "steps": rows, "sec": round(time.time() - t0, 1)}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "READINESS_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"  [4/4] [VCGC 監控] {overall} · 站 {len(rows)}(綠 {lamps.count('GREEN')} · 黃 {lamps.count('YELLOW')} · 紅 {lamps.count('RED')})"
          f" · {rep['sec']}s · 報告 {(OUT_DIR / 'READINESS_latest.json').relative_to(VIA)}", flush=True)
    return rep


def ps_register() -> Path | None:
    """定義 via-activate-vdf 的最新 Register 檔(尾版律)。"""
    hits = [p for p in VIA.glob("Register-VIA-Commands-v*.ps1") if "function global:via-activate-vdf" in p.read_text(encoding="utf-8", errors="ignore")]
    return sorted(hits)[-1] if hits else None


PS_MOCK = r"""
$e = $null; $tk = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile('__REG__', [ref]$tk, [ref]$e)
"PARSE=" + $e.Count
foreach ($n in 'ConvertTo-VIAVdfEdit', 'via-activate-vdf') {
    $fn = $ast.Find({ param($x) $x -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $x.Name -eq "global:$n" }, $true)
    . ([scriptblock]::Create($fn.Extent.Text))
}
$global:VIAMockScoped = 0
function global:via-vcgc { "CALL=" + ($args -join '|') }
function global:Add-VIAUiHome([object[]]$Rest) { $x = @($Rest); if ($x -notcontains '--home') { $x += @('--home', '/db/x') }; return ,$x }
function global:Invoke-VIACeleritasScoped([scriptblock]$B) { $global:VIAMockScoped++; & $B }
"--- A"
via-activate-vdf --start TW_MARKET=2022-01-01 --apply -NoOpen -Repair 6>$null
"--- B"
via-activate-vdf -SkipCheck -NoPrompt --add TW_FIN=2330,3324 6>$null
"--- C"
"EDIT=" + ((ConvertTo-VIAVdfEdit 'TW_MARKET=2022-01-01') -join '|') + ';' + ((ConvertTo-VIAVdfEdit '+TW_FIN=2330') -join '|') + ';' + ((ConvertTo-VIAVdfEdit '-TW_FIN=2330') -join '|') + ';' + [string]($null -eq (ConvertTo-VIAVdfEdit 'junk'))
"SCOPED=" + $global:VIAMockScoped
"""


def ps_mock(reg: Path) -> tuple:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "mock.ps1"
        f.write_text(PS_MOCK.replace("__REG__", str(reg).replace("'", "''")), encoding="utf-8-sig")
        try:
            p = subprocess.run(["pwsh", "-NoProfile", "-NonInteractive", "-File", str(f)], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=120)
            return p.returncode, p.stdout + p.stderr
        except subprocess.TimeoutExpired:
            return 124, "timeout"


# ---------- 自測(零網路 · 不起 VCGC 子行程 · 不開瀏覽器;有 pwsh 才驗 PS 短令接線) ----------
def selftest() -> int:
    res = []

    def chk(name, ok, note=""):
        res.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' (' + str(note) + ')') if note else ''}")

    print(f"=== {ENGINE} · VCGC 母系統監控自測(零網路 · 不起 VCGC 子行程)===")
    chk("① token 卡 6/6 = GREEN;5/6 或 rc≠0 = RED", p_token(0, "已啟用 6/6")[0] == "GREEN" and p_token(0, "已啟用 5/6")[0] == "RED" and p_token(1, "已啟用 6/6")[0] == "RED")
    chk("② RunGate 判定行照讀;沒有判定行 + rc 1 = RED(不假綠)",
        p_rungate(0, "[via-rungate] 判定 GREEN · 存證")[0] == "GREEN" and p_rungate(1, "boom")[0] == "RED" and p_rungate(2, "[via-rungate] 判定 GREEN")[0] == "YELLOW")
    lk = p_lkgc(0, "[LKGC] latest 20261001_1 · verdict RED · 境 4")
    chk("③ LKGC verdict RED = 不可用(修理改走 RunGate 補缺件)", lk["verdict"] == "RED" and not lk["eligible"])
    plan_gated = repair_plan({"vdf": "RED", "vrn": "GREEN"}, lk, gate=False)
    plan_lkgc = repair_plan({"vdf": "RED"}, {"eligible": True}, gate=True)
    chk("④ 修理計畫:只修不綠的家族 · 雙閘沒開 = GATED · LKGC 可用走 rollback(不給 --approve-remove = 不刪 base)",
        len(plan_gated) == 1 and plan_gated[0]["argv"][-3:] == ["--family", "vdf", "--approve-install"] and plan_gated[0]["state"] == "GATED"
        and plan_lkgc[0]["argv"][2] == "rollback" and "--approve-remove" not in plan_lkgc[0]["argv"] and repair_plan({"vdf": "GREEN"}, lk, True) == [])
    rep = {"stations": {"bridge": {"lamp": "GREEN", "summary": "VDF/net 138/138 · ALL/accel 1796/1796"}, "celer": {"lamp": "RED", "summary": "x"}},
           "findings": [{"id": "PC-001", "lamp": "RED", "class": "ACCEL", "where": "functional modules/VRN/VRN_NewPlugins_v0102.py:1", "owner": "VRN_SystemManager(L111)"},
                        {"id": "PC-009", "lamp": "YELLOW", "class": "PSTPL", "where": "", "owner": "VCGC"}]}
    lamp, summ, _ = p_coverage(rep)
    rep2 = dict(rep, findings=[{"id": "PC-002", "lamp": "RED", "class": "ACCEL", "where": "functional modules/VDF/engine/X_v0101.py:3", "owner": "VDF_SystemManager(L111)"},
                               {"id": "PC-003", "lamp": "RED", "class": "SYSEXE", "where": "supportive modules/registry/Y_v0100.py:9", "owner": "VCGC"}])
    chk("⑤ 覆蓋率:子系統 VRN 的紅 = YELLOW 附歸屬(L111);VDF / VCGC 的紅 = RED;讀出 PY 加速 · VDF 網路比數",
        lamp == "YELLOW" and p_coverage(rep2)[0] == "RED" and "PY 加速 1796/1796" in summ and "VDF 網路 138/138" in summ and p_coverage({})[0] == "RED", f"{lamp} · {summ}")
    keep = {k: os.environ.get(k) for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    try:
        for k in keep:
            os.environ.pop(k, None)
        closed = consent_open()
        os.environ["VIA_NET_CONSENT"], os.environ["VIA_SCRAPE_CONSENT"] = "YES", "YES"
        opened = consent_open()
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    import ast
    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    sets_consent = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Store)
                    and isinstance(n.slice, ast.Constant) and str(n.slice.value).endswith("_CONSENT") and n.lineno < tree.body[-1].lineno
                    and not any(isinstance(f, ast.FunctionDef) and f.name == "selftest" and f.lineno <= n.lineno <= f.end_lineno for f in tree.body)]
    chk("⑨ 雙閘只讀:沒開 = 關、兩個都開才算開;selftest 以外沒有任何一行寫 *_CONSENT(AI 永不代設)", not closed and opened and not sets_consent, f"寫入行 {sets_consent}")
    talib = [n.lineno for n in ast.walk(tree) if (isinstance(n, ast.Import) and any(a.name.split(".")[0] == "talib" for a in n.names))
             or (isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "talib")]
    chk("⑩ 帶加速器橋 + VDF 網路工具橋;不碰 TA-Lib(AST 查 import,不比對字串)", "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src and not talib, f"talib import 行 {talib}")
    chk("⑫ 歸屬:precheck owner 欄優先(VRN_SystemManager(L111) → VRN);沒有才看路徑;where 去掉 :行",
        owner_of("functional modules/VRN/a.py") == "VRN" and owner_of("supportive modules/70_VRN_Rules/b.py") == "VRN"
        and owner_of("functional modules/VDF/engine/c.py") == "VDF" and owner_of("supportive modules/registry/d.py") == "VCGC"
        and finding_owner(rep["findings"][0]) == "VRN" and finding_owner({"where": "functional modules/VDF/x.py:2"}) == "VDF"
        and where_of({"where": "a/b.py:12"}) == "a/b.py")
    reg = ps_register()
    rtxt = reg.read_text(encoding="utf-8", errors="ignore") if reg else ""
    chk("⑭ PS 短令在尾版 Register:via-activate-vdf · via_activate_vdf · 啟動VDF;兩章在;① VCGC 監控 CGC_MDL265 ② 交 VDF_SystemManager activate",
        reg is not None and "CELERITAS-TEMPLATE-JOIN" in rtxt and "[VIA:PS-ACCEL:v0101]" in rtxt and "CGC_MDL265_VdfVrnReadiness" in rtxt
        and "'VDF_SystemManager', 'activate'" in rtxt and "-Name via_activate_vdf -Value via-activate-vdf" in rtxt and "-Name 啟動VDF -Value via-activate-vdf" in rtxt,
        reg.name if reg else "找不到")
    if reg is not None and shutil.which("pwsh"):
        rc, out = ps_mock(reg)
        a_part = out.split("--- A")[-1].split("--- B")[0]
        b_part = out.split("--- B")[-1].split("--- C")[0]
        chk("⑮ pwsh:Parser 0 錯 · 兩段各歸各的系統:① CGC_MDL265 --repair ② VDF_SystemManager activate(改動旗標 · --no-open · 操作台 --home)· 都包加速器 scope",
            rc == 0 and "PARSE=0" in out and "CALL=run|CGC_MDL265_VdfVrnReadiness|--repair" in a_part
            and "CALL=run|--family|vdf|VDF_SystemManager|activate|--start|TW_MARKET=2022-01-01|--apply|--no-open|--home|/db/x" in a_part, a_part.strip()[-300:])
        chk("⑯ -SkipCheck 只跑 VDF 段 · 陣列參數攤平(TW_FIN=2330,3324)· 互動行解析:大類=日期 → --start · +族群=值 → --add · -族群=值 → --remove · 看不懂 = 拒",
            "CGC_MDL265" not in b_part and "CALL=run|--family|vdf|VDF_SystemManager|activate|--add|TW_FIN=2330,3324|--home|/db/x" in b_part
            and "EDIT=--start|TW_MARKET=2022-01-01;--add|TW_FIN=2330;--remove|TW_FIN=2330;True" in out and "SCOPED=3" in out, out.strip()[-260:])
    ok = all(res)
    print(f"  [計] {ENGINE} 自測 {sum(res)}/{len(res)} · {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] in (["-h"], ["--help"]):
        print(__doc__)
        return 0
    only = set(a[a.index("--only") + 1].split(",")) if "--only" in a and a.index("--only") + 1 < len(a) else None
    if only and not only <= set(STEPS):
        print(f"  [VCGC 監控] --only 只收 {','.join(STEPS)};收到 {sorted(only - set(STEPS))}")
        return 2
    rep = readiness(repair="--repair" in a, only=only)
    if "--json" in a:
        print(json.dumps(rep, ensure_ascii=False, default=str))
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[rep["overall"]]


if __name__ == "__main__":
    raise SystemExit(main())
