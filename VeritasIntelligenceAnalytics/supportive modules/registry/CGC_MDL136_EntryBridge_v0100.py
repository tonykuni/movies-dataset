#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL136_EntryBridge v0100 — 單一入口橋(批383)
====================================================================
操作員令(批383):「https://github.com/tonykuni/river-beam-aurora-acorn 將裡面的檔案接回做為
整合為一入口」+「單一入口與這個(SYSTEM MANAGER MATRIX v0700)整合;vap 補充;vdf/vrn 要弄到
實際能跑;vdf 要將資料庫存入;之前有的資料庫能把它整理好,抓過的資料不必再抓」。
職權(Zero-Hydra=全複用正主,零重造):
  ①roster  短指令冊=母倉 Register-VIA-Commands 尾版(function global: 實掃)∪ Grok 主控台
           收容包 scripts/VIA-CmdMatrix.ps1(function global: 實掃)→ 撞名守衛:母倉先發先得,
           Grok 同名令改 -grok 尾綴(Register v0150 載入時同律;本檔=規則正本+驗證)
  ②status  單一入口燈板(GitHub/Mother/Data/Env/PATH/EnvGov/RunGate(批384)/VDF-DB/VAP/Matrix/Console/Grok;
           零網路;RYG 誠實三態;落 VIA_Reports/entry/ENTRY_latest.json + .html 零 CDN)
  ③plan    一貼即用次序(via-entry → via-envgov → REPAIR_BASE → via-vdfdb → ckpt → via-vapone
           → via-open 矩陣 → via-webconsole);每步依現況標 READY/PENDING/SKIP
  ④envpy   家族境 python 解析(vdf/vrn/vap/core/ocr/table/html/nlp/ml/tools):
           VIA_PY_<FAMILY> 覆寫 > 境根(VIA_ENV_ROOT/VIA_ENV_ROOTS/~/envs/conda envs/…)×
           Baseline 冊別名(via_vdf_312/via_vrn_312/via_vap_312/via_paddle_311/via_camelot_311…)
           > base 退路(誠實 BASE_FALLBACK;VDF/VRN 引擎要能跑=功能件住 via_ 境,啟動器須指對 python)
  ⑤cmdmatrix-clean  印去尾段自動執行(via-enter/via-matrix WPF)+撞名改名後的 CmdMatrix 文本
律:只增不減;原件零觸碰(收容包/Grok 腳本/EnvManager 正本皆不改);誠實三態;零 CDN;
    零網路(status 只探本機 127.0.0.1:8080 是否在聽=Grok 網頁主控台 LIVE/OFF);
    尾版律(所有引擎 glob 尾版,嚴禁寫死版號)。
用法:python3 CGC_MDL136_EntryBridge_v0100.py [status|roster|plan|envpy <family>|cmdmatrix-clean] [--json] [--quiet]
      | --selftest
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

import datetime as _dt
import html
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPO = VIA.parent
INTAKE = VIA / "supportive modules" / "references" / "intake"
GROK = INTAKE / "VIA_GrokConsole_AuroraAcorn_b383"
CMDMATRIX = GROK / "scripts" / "VIA-CmdMatrix.ps1"
UI = VIA / "supportive modules" / "ui_support"
OUT = VIA / "VIA_Reports" / "entry"
ENVGOV_RUN = VIA / "VIA_Reports" / "env_governance" / "RUN_latest.json"
VDFDB_RUN = VIA / "VIA_Reports" / "vdf" / "local_db" / "RUN_latest.json"
RUNGATE_RUN = VIA / "VIA_Reports" / "rungate" / "RUNGATE_latest.json"   # 批384 能跑閘(MDL137)
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
DBS = [MEGA / "vdf_tw_market.duckdb", MEGA / "vdf_global_market.duckdb"]
CONSOLE_PORT = 8080

# 母倉正本短令(批383 Register v0150 後定義=先發先得);Grok 同名令一律 -grok 尾綴
MOTHER_FIRST = ("via-entry", "via-env")
# CmdMatrix 尾段自動執行行(載入即進母根+開 WPF 板=違批378 零跳出律)→ 去除
# (欄 0 錨定=只去頂層尾段;函式體內縮排的 via-enter | Out-Null 保留)
# 批387 實錄:Windows autocrlf 工作副本為 CRLF,$ 只認 \n 前 → \r 殘留使 via-enter 行未去除而於載入時執行(cwd 跳到主 clone)→ 容 \r
TAIL_STRIP = (re.compile(r"(?m)^via-enter \| Out-Null[ \t\r]*$"),
              re.compile(r"(?m)^try \{ via-matrix \}.*$"),
              re.compile(r"(?m)^Lamp 'GREEN' 'LOAD'.*$"))
# Grok 非 global 助手函式(Lamp/Get-VIAZh/Get-VIAShortCommands/New-ViaDir/Find-ViaPython)於 Register 函式域內點源會隨域消失
# → 一律升 global(Grok 全域令執行期才找得到);母倉無同名助手=零撞
HELPER_PROMOTE = re.compile(r"(?m)^function (?!global:)([\w-]+)")

# 家族 → 境名候選(Baseline 冊 env_layout/families 別名;既有境優先;尾碼=Python 版)
FAMILY_ENVS = {
    "vdf": ["via_vdf_312", "via_vdf", "via_vdf_313"],
    "vrn": ["via_vrn_312", "via_vrn", "via_extract_312", "via_vrn4"],
    "vap": ["via_vap_312", "via_vap", "via_vap_313"],
    "core": ["via_core_312", "via_core", "venv_core"],
    "ocr": ["via_paddle_311", "via_paddle_312", "via_ocr", "paddle_312", "paddle_311"],
    "table": ["via_camelot_311", "camelot_311"],
    "html": ["via_html_312", "via_html"],
    "nlp": ["via_nlp", "via_nlp_312"],
    "ml": ["via_ml", "via_iso_ml_cuda_H"],
    "tools": ["via_tools_312", "via_tools"],
}
PY_SUBS = ("Scripts/python.exe", "python.exe", "bin/python3", "bin/python")


def _ts() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def newest(root: Path, pat: str) -> Path | None:
    hits = sorted(root.glob(pat)) if root.exists() else []
    return hits[-1] if hits else None


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def lamp(color: str, layer: str, msg: str, quiet: bool = False) -> None:
    if not quiet:
        try:
            print(f"{color:<7} {layer:<10} {msg}")
        except (BrokenPipeError, UnicodeEncodeError):
            pass


# ---------------------------------------------------------------- ① 短指令冊 / 撞名守衛
def register_newest() -> Path | None:
    return newest(VIA, "Register-VIA-Commands-v*.ps1")


def mother_cmds(text: str | None = None) -> set:
    if text is None:
        r = register_newest()
        text = _read(r) if r else ""
    return set(re.findall(r"function global:(via[\w-]*)", text))


def grok_cmds(text: str) -> list:
    return re.findall(r"function global:(via[\w-]*)", text)


def grok_zh(text: str) -> dict:
    """Grok Get-VIAZh 中文說明表('via-x' = '說明')實掃(零發明)"""
    return {m.group(1): m.group(2) for m in re.finditer(r"'(via[\w-]*|selftest|regen-all)'\s*=\s*'([^']*)'", text)}


def collisions(mother: set, grok: list) -> dict:
    """撞名守衛:母倉先發先得;Grok 同名 → <name>-grok(冊律;Register v0150 載入同律)"""
    out = {}
    for n in grok:
        if n in mother or n in MOTHER_FIRST:
            out[n] = f"{n}-grok"
    return out


def clean_cmdmatrix(text: str, mother: set | None = None) -> tuple[str, dict]:
    """去尾段自動執行 + 撞名改名(Grok 內部呼叫鏈同步改指);原件零觸碰(只回文本)"""
    mother = mother if mother is not None else mother_cmds()
    stripped = 0
    for rx in TAIL_STRIP:
        text, n = rx.subn("", text)
        stripped += n
    ren = collisions(mother, grok_cmds(text))
    for old, new in ren.items():
        text = text.replace(f"function global:{old} {{", f"function global:{new} {{")
        # Grok 內部呼叫鏈(整行僅該令)→ 改指 -grok 版,行為與原件一致
        text = re.sub(rf"(?m)^(\s*){re.escape(old)}\s*$", rf"\1{new}", text)
    text, promoted = HELPER_PROMOTE.subn(r"function global:\1", text)
    return text, {"stripped": stripped, "renamed": ren, "promoted": promoted, "verbs": grok_cmds(text)}


def roster(do_print: bool = True, quiet: bool = False) -> list:
    reg = register_newest()
    mtext = _read(reg) if reg else ""
    mset = mother_cmds(mtext)
    gtext = _read(CMDMATRIX) if CMDMATRIX.exists() else ""
    glist = grok_cmds(gtext)
    gzh = grok_zh(gtext)
    ren = collisions(mset, glist)
    ssot = {}
    sp = newest(HERE, "VIA_MasterGovernance_SSOT_v*.json")
    if sp:
        try:
            ssot = json.loads(_read(sp)).get("verbs", {}) or {}
        except Exception:
            ssot = {}
    rows = []
    for n in sorted(mset):
        rows.append({"name": n, "owner": "MOTHER", "state": "母倉正本" + ("(撞名:母倉勝)" if n in ren else ""),
                     "zh": (ssot.get(n) or gzh.get(n) or "")[:120]})
    for n in glist:
        nm = ren.get(n, n)
        rows.append({"name": nm, "owner": "GROK", "state": ("撞名改名 ← " + n) if n in ren else "Grok 主控台短令",
                     "zh": (gzh.get(n) or "")[:120]})
    if do_print and not quiet:
        print(f"--- 短指令冊(母倉 {len(mset)} · Grok {len(glist)} · 撞名 {len(ren)}:母倉先發先得,Grok 改 -grok)---")
        for r in rows:
            if r["owner"] == "GROK" or r["name"] in ren:
                print(f"  [{r['owner']:<6}] {r['name']:<22} {r['state']:<24} {r['zh']}")
        print("  (母倉全冊:via-help;Grok 冊來源=收容包 b383 scripts/VIA-CmdMatrix.ps1;原件零觸碰)")
    return rows


# ---------------------------------------------------------------- ④ 家族境 python 解析
def env_roots(extra: list | None = None, environ: dict | None = None) -> list:
    e = environ if environ is not None else os.environ
    roots: list[Path] = []
    for raw in [e.get("VIA_ENV_ROOT", "")] + e.get("VIA_ENV_ROOTS", "").split(os.pathsep):
        if raw and raw.strip():
            roots.append(Path(raw.strip()))
    roots += [Path(x) for x in (extra or []) if x]
    home = Path(e.get("USERPROFILE") or e.get("HOME") or Path.home())
    roots += [home / "envs", Path(r"C:\Users\tonyk\envs"), home / "miniconda3" / "envs", home / "Miniconda3" / "envs",
              home / "anaconda3" / "envs", home / "Anaconda3" / "envs", home / ".virtualenvs", VIA / "Environments", VIA, REPO]
    seen, out = set(), []
    for r in roots:
        k = str(r).lower()
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def _env_python(env_dir: Path) -> Path | None:
    for sub in PY_SUBS:
        p = env_dir / sub
        if p.exists():
            return p
    return None


def resolve_env_python(family: str, roots: list | None = None, environ: dict | None = None) -> dict:
    """家族境 python:VIA_PY_<FAMILY> 覆寫 > 境根×候選名 > base 退路(誠實 BASE_FALLBACK)"""
    e = environ if environ is not None else os.environ
    fam = family.strip().lower()
    ov = (e.get(f"VIA_PY_{fam.upper()}") or "").strip()
    if ov and Path(ov).exists():
        return {"family": fam, "env": Path(ov).parent.parent.name, "python": ov, "source": f"env VIA_PY_{fam.upper()}", "state": "OK"}
    names = list(FAMILY_ENVS.get(fam, [])) + [f"via_{fam}_312", f"via_{fam}", f"via_{fam}_313", f"via_{fam}_311", f".venv-via_{fam}"]
    seen = set()
    for root in (roots if roots is not None else env_roots(environ=e)):
        for n in names:
            if n in seen and root != roots:
                pass
            d = root / n
            if d.is_dir():
                py = _env_python(d)
                if py:
                    return {"family": fam, "env": n, "python": str(py), "source": str(root), "state": "OK"}
    return {"family": fam, "env": "", "python": sys.executable, "source": "base 退路(境未見)", "state": "BASE_FALLBACK",
            "hint": f"建境:via-envgov apply --approve(ENSURE_ENV via_{fam}_312)或 uv venv <境根>\\via_{fam}_312 --python 3.12;或設 VIA_PY_{fam.upper()}"}


# ---------------------------------------------------------------- ② 單一入口燈板
def _git(args: list) -> str:
    try:
        r = subprocess.run(["git", "-C", str(REPO)] + args, capture_output=True, text=True, timeout=8)
        return (r.stdout or "").strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def _port_open(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.3):
            return True
    except Exception:
        return False


def _data_home() -> tuple[str, str]:
    try:
        import importlib.util
        p = newest(HERE, "CGC_MDL123_DataHome_v0*.py")
        if not p:
            return "", "MDL123 缺"
        spec = importlib.util.spec_from_file_location("datahome_e136", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules["datahome_e136"] = m
        spec.loader.exec_module(m)
        home, src = m.resolve_home(VIA)
        return str(home), src
    except Exception as exc:
        return "", f"解析失敗 {str(exc)[:60]}"


def status(do_print: bool = True, quiet: bool = False, environ: dict | None = None) -> dict:
    q = quiet or not do_print
    lamps = []

    def add(color, layer, msg, **kw):
        lamps.append({"lamp": color, "layer": layer, "msg": msg, **kw})
        lamp(color, layer, msg, q)

    # GitHub
    br, rem = _git(["rev-parse", "--abbrev-ref", "HEAD"]), _git(["remote", "get-url", "origin"])
    if br:
        add("GREEN", "GitHub", f"{br}  {rem}  root={REPO}")
    else:
        add("YELLOW", "GitHub", f"非 git 倉或 git 缺(母倉 .git 在上層 {REPO});對帳走 via-reload / sync")
    # Mother
    reg = register_newest()
    keys = ["functional modules/VDF/engine", "functional modules/VRN", "functional modules/VAP/engine", "supportive modules/registry", "supportive modules/ui_support"]
    miss = [k for k in keys if not (VIA / k).exists()]
    add("GREEN" if not miss and reg else "RED", "Mother", f"{VIA}  Register={reg.name if reg else '缺'}" + (f"  缺 {miss}" if miss else ""))
    # Data
    home, src = _data_home()
    dbs = [(p.name, p.exists(), (p.stat().st_size // 1_048_576) if p.exists() else 0) for p in DBS]
    have = [f"{n} {mb}MB" for n, ok, mb in dbs if ok]
    add("GREEN" if have else "YELLOW", "Data", f"資料家={home or '未解析'}({src}) · mega 庫 {'、'.join(have) if have else '缺(via-vdfdb run --apply 建;ENG065 三包匯入)'}",
        home=home, dbs=dbs)
    # Env(家族境 python)
    fams = ["vdf", "vrn", "vap", "core", "ocr", "table"]
    res = {f: resolve_env_python(f, environ=environ) for f in fams}
    ok = [f for f in fams if res[f]["state"] == "OK"]
    fb = [f for f in fams if res[f]["state"] != "OK"]
    add("GREEN" if "vdf" in ok and "vrn" in ok and "vap" in ok else ("YELLOW" if ok else "RED"), "Env",
        "境 python:" + " ".join(f"{f}={res[f]['env']}" for f in ok) + (f"  base 退路:{','.join(fb)}" if fb else ""), envs=res)
    add("GREEN", "PATH", "via_iso_* 不進 PATH(ISO99);啟動器以 Get-VIAEnvPython <family> 指對境 python;base 只放共用工具")
    # EnvGov
    if ENVGOV_RUN.exists():
        try:
            r = json.loads(_read(ENVGOV_RUN))
            base = next((s for s in r.get("panorama", []) if s.get("env", {}).get("name") == "BASE"), {})
            ba = r.get("base_analysis") or {}
            mm = ba.get("manifest_missing") or []
            v = r.get("verdict", "?")
            add({"GREEN": "GREEN", "YELLOW": "YELLOW"}.get(v, "RED"), "EnvGov",
                f"{v} · {r.get('ts', '')[:16]} · 境 {len(r.get('panorama', []))} · BASE 衝突 {len(base.get('conflicts') or [])} · manifest 缺 {len(mm)}"
                + (f"({','.join(mm[:6])}{'…' if len(mm) > 6 else ''})→ via-envgov apply --approve --only-kind REPAIR_BASE" if mm else ""),
                verdict=v, manifest_missing=mm)
        except Exception as exc:
            add("YELLOW", "EnvGov", f"RUN_latest 讀取失敗 {str(exc)[:60]}")
    else:
        add("GREY", "EnvGov", "未跑;via-envgov(唯讀 run --offline)")
    # VDF-DB(ENG079)
    if VDFDB_RUN.exists():
        try:
            r = json.loads(_read(VDFDB_RUN))
            s = r.get("summary") or {}
            add("GREEN" if r.get("verdict") == "GREEN" else ("YELLOW" if r.get("verdict") == "YELLOW" else "RED"), "VDF-DB",
                f"{r.get('verdict', '?')} · {r.get('mode', '')} · 檔 {s.get('files', 0)} · 新增列 {s.get('rows_new', 0):,} · 已入冊跳過 {s.get('skipped_ledger', 0)} · {r.get('ts', '')[:16]}")
        except Exception as exc:
            add("YELLOW", "VDF-DB", f"RUN_latest 讀取失敗 {str(exc)[:60]}")
    else:
        add("GREY", "VDF-DB", "未跑;via-vdfdb scan(本機三庫盤點;唯讀)→ via-vdfdb run --apply → via-vdfdb ckpt")
    # RunGate(批384 能跑閘:家族境 python 真跑引擎自測)
    if RUNGATE_RUN.exists():
        try:
            r = json.loads(_read(RUNGATE_RUN))
            fams = " ".join(f"{k}={v['verdict']}({v['summary']['engines_ok']}/{v['summary']['engines_n']};{v['python']['state']})" for k, v in (r.get("families") or {}).items())
            add({"GREEN": "GREEN", "YELLOW": "YELLOW"}.get(r.get("verdict"), "RED"), "RunGate", f"{r.get('verdict', '?')} · {r.get('ts', '')[:16]} · {fams} · via-rungate status")
        except Exception as exc:
            add("YELLOW", "RunGate", f"RUNGATE_latest 讀取失敗 {str(exc)[:60]}")
    else:
        add("GREY", "RunGate", "未跑;via-rungate(家族境 python 真跑 VDF/VRN/VAP 引擎自測;--fast 每族 3 站)")
    # VAP ONE
    vap = newest(VIA / "functional modules" / "VAP" / "engine", "VAP_ENG016_AutoplotOne_v*.py")
    sj = INTAKE / "VIA_VapOne_b383" / "VAP_ONE_selftest.json"
    note = ""
    if sj.exists():
        try:
            j = json.loads(_read(sj))
            lanes = [k for k, v in (j.get("lanes") or {}).items() if not v.get("available")]
            note = f" · 工作站實錄 {j.get('verdict')} {j.get('passed')}/{j.get('total')}" + (f"(base 缺車道 {','.join(lanes)})" if lanes else "")
        except Exception:
            pass
    add("GREEN" if vap else "RED", "VAP", (f"{vap.name} 在位;via-vapone(--selftest;via_vap_312 python 優先)" if vap else "VAP_ENG016 缺") + note)
    # Matrix(靜態總控矩陣頁 v0700)
    mx = newest(UI, "VIA_MasterControl_Matrix_*.html")
    if mx:
        t = _read(mx)
        add("GREEN", "Matrix", f"{mx.name} {mx.stat().st_size // 1024}KB · 表 {t.count('<table')} · via-open 矩陣(瀏覽器道零跳出)")
    else:
        add("YELLOW", "Matrix", "ui_support 無 VIA_MasterControl_Matrix_*.html(收容包 b383 複本缺)")
    # Console(Grok 網頁主控台)
    if (GROK / "package.json").exists():
        node, npm = shutil.which("node"), shutil.which("npm")
        nm = (GROK / "node_modules").exists()
        live = _port_open(CONSOLE_PORT)
        c = "GREEN" if live else ("YELLOW" if (node and npm) else "GREY")
        add(c, "Console", f"Grok 主控台 {'LIVE http://localhost:%d' % CONSOLE_PORT if live else 'OFF'} · node={'有' if node else '缺'} npm={'有' if npm else '缺'} · node_modules={'在' if nm else '缺(via-webconsole --install 觸網同意閘)'} · via-webconsole [--background]",
            live=live, node=bool(node), node_modules=nm)
    else:
        add("RED", "Console", f"收容包缺 {GROK}")
    # Grok 短令
    if CMDMATRIX.exists():
        gtext = _read(CMDMATRIX)
        gl = grok_cmds(gtext)
        ren = collisions(mother_cmds(), gl)
        add("GREEN", "Grok", f"CmdMatrix {len(gl)} 令(去尾段自動 via-enter/via-matrix;撞名 {len(ren)}:{','.join(f'{k}→{v}' for k, v in ren.items())})")
    else:
        add("YELLOW", "Grok", "scripts/VIA-CmdMatrix.ps1 缺")
    colors = [x["lamp"] for x in lamps]
    verdict = "RED" if "RED" in colors else ("YELLOW" if "YELLOW" in colors else "GREEN")
    rep = {"schema": "VIA.EntryBridge.v1", "ts": _dt.datetime.now().isoformat(timespec="seconds"), "via": str(VIA), "verdict": verdict, "lamps": lamps,
           "next": ["via-entry(本燈板)", "via-envgov(全景;唯讀)", "via-envgov apply --approve --only-kind REPAIR_BASE(base 補 manifest 缺件;非破壞)",
                    "via-rungate(能跑閘:家族境 python 真跑 VDF/VRN/VAP 引擎自測)",
                    "via-vdfdb scan → via-vdfdb run --apply → via-vdfdb ckpt(抓過不再抓)", "via-vapone(VAP ONE 72 檢)", "via-open 矩陣", "via-webconsole --background(選配;Node 22)"]}
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        _write_json(OUT / f"ENTRY_{_ts()}.json", rep)
        _write_json(OUT / "ENTRY_latest.json", rep)
        (OUT / "ENTRY_latest.html").write_text(render_html(rep), encoding="utf-8")
    except Exception as exc:
        lamp("YELLOW", "Report", f"落檔失敗 {str(exc)[:60]}", q)
    if not q:
        print(f"[via-entry] 判定 {verdict} · 存證 {OUT / 'ENTRY_latest.json'} · 次步:{' → '.join(rep['next'][1:5])}")
    return rep


def render_html(rep: dict) -> str:
    col = {"GREEN": "#34d399", "YELLOW": "#fde047", "RED": "#fca5a5", "GREY": "#94a3b8"}
    rows = "".join(f"<tr><td style='color:{col.get(x['lamp'], '#ddd')}'>{x['lamp']}</td><td>{html.escape(x['layer'])}</td><td>{html.escape(x['msg'])}</td></tr>" for x in rep["lamps"])
    nxt = "".join(f"<li><code>{html.escape(n)}</code></li>" for n in rep["next"])
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>VIA 單一入口燈板 · EntryBridge</title><style>body{background:#0f172a;color:#f8fafc;font:11px/1.35 -apple-system,'Segoe UI',Roboto,Arial,sans-serif;padding:12px}"
            "table{border-collapse:collapse;width:100%}td,th{border:1px solid #334155;padding:3px 6px;text-align:left;vertical-align:top}th{background:#1e293b}code{color:#38bdf8}</style></head><body>"
            f"<h1 style='font-size:14px;margin:0 0 6px'>VIA 單一入口燈板 · {html.escape(rep['verdict'])} · {html.escape(rep['ts'])}</h1>"
            f"<div style='color:#94a3b8;margin-bottom:8px'>{html.escape(rep['via'])} · 零 CDN · 零網路 · 母倉 Register 點源=唯一入口;Grok 主控台=via-webconsole 子入口</div>"
            f"<table><tr><th>燈</th><th>層</th><th>狀態</th></tr>{rows}</table><h2 style='font-size:12px'>次步</h2><ol>{nxt}</ol></body></html>")


# ---------------------------------------------------------------- ③ 一貼即用次序
def plan(do_print: bool = True, quiet: bool = False) -> list:
    st = None
    try:
        st = json.loads(_read(OUT / "ENTRY_latest.json")) if (OUT / "ENTRY_latest.json").exists() else None
    except Exception:
        st = None
    L = {x["layer"]: x for x in (st or {}).get("lamps", [])}
    mm = (L.get("EnvGov") or {}).get("manifest_missing") or []
    steps = [
        ("via-reload", "拉齊母倉並重載短令冊(Register 尾版;Grok 矩陣同載)", "READY"),
        ("via-entry", "單一入口燈板(GitHub/Mother/Data/Env/EnvGov/VDF-DB/VAP/Matrix/Console/Grok)", "READY"),
        ("via-envgov", "環境治理全景(唯讀 run --offline;digest 25 行)", "READY" if "EnvGov" not in L or L["EnvGov"]["lamp"] == "GREY" else "DONE"),
        ("via-envgov apply --approve --only-kind REPAIR_BASE", "base 補 manifest 缺件(duckdb/pyarrow/plotly…;非破壞;鏡像鏈 Tsinghua→Aliyun→PyPI)", "READY" if mm else "SKIP(manifest 齊)"),
        ("via-rungate", "能跑閘(批384):家族境 python(via_vdf_312/via_vrn_312/via_vap_312)逐庫 import + 真跑引擎自測;RED=有引擎跑不起來;YELLOW=base 退路", "READY" if "RunGate" not in L or L["RunGate"]["lamp"] == "GREY" else "DONE"),
        ("via-famui vdf,vrn --open", "家族 U/I 再生閘(批388):家族境 python 真跑 VDF/VRN 頁面產生器→頁新鮮/零 CDN→索引一鍵開(via-open VDF/VRN/四點/家族)", "READY"),
        ("via-vdfdb scan", "本機三庫(prices/chips/rest)盤點+路由計畫(唯讀;檔冊 sha 已入冊=跳過)", "READY"),
        ("via-vdfdb run --apply", "COPY_ONLY anti-join 入正典 DuckDB(只補缺鍵;原件不刪不搬)", "PENDING(先 scan)"),
        ("via-vdfdb ckpt", "ENG064 checkpoint 自庫重建=已有年段/檔永不重抓", "PENDING(先 run --apply)"),
        ("via-vdfdb need --start 2023-01-01", "覆蓋缺口清單(只列缺的;抓取引擎只抓缺口)", "PENDING"),
        ("via-vapone", "VAP ONE 72 檢(via_vap_312 python 優先;缺車道誠實 SKIP)", "READY"),
        ("via-open 矩陣", "SYSTEM MANAGER MATRIX v0700 靜態頁(瀏覽器道;零跳出)", "READY"),
        ("via-webconsole --background", "Grok 網頁主控台 8080(選配;Node 22;首次 --install 觸網同意閘)", "READY" if (L.get("Console") or {}).get("node") else "SKIP(Node 缺)"),
    ]
    rows = [{"n": i + 1, "cmd": c, "zh": z, "state": s} for i, (c, z, s) in enumerate(steps)]
    if do_print and not quiet:
        print("--- 一貼即用次序(母倉 pwsh;每步可單跑;破壞段一律另加 --approve-remove 且本冊無)---")
        for r in rows:
            print(f"  {r['n']:>2}. {r['cmd']:<52} {r['state']:<18} {r['zh']}")
    return rows


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    sample = ("function Lamp([string]$c) { }\nfunction global:via-enter {\n    return $true\n}\nfunction global:via-env {\n    via-path\n}\n"
              "function global:via-entry {\n    via-env\n    Lamp 'GREEN' 'ENTRY' 'x'\n}\nfunction global:via-ingest {\n    via-enter | Out-Null\n}\n"
              "Lamp 'GREEN' 'LOAD' 'x'\nvia-enter | Out-Null\ntry { via-matrix } catch { }\n")
    t, rep = clean_cmdmatrix(sample, {"via-entry", "via-env", "via-status"})
    t_crlf, rep_crlf = clean_cmdmatrix(sample.replace("\n", "\r\n"), {"via-entry", "via-env", "via-status"})
    chk("① 去尾段自動執行(欄 0 三行:via-enter/via-matrix/LOAD;LF 與 CRLF 皆去=批387 Windows 實錄)且函式體內 via-enter | Out-Null 保留;助手函式升 global",
        rep["stripped"] == 3 and "try { via-matrix }" not in t and t.count("via-enter | Out-Null") == 1
        and rep["promoted"] == 1 and "function global:Lamp(" in t
        and rep_crlf["stripped"] == 3 and t_crlf.count("via-enter | Out-Null") == 1)
    chk("② 撞名守衛(母倉先發先得;Grok via-entry/via-env → -grok;內部呼叫鏈同步改指)",
        rep["renamed"] == {"via-env": "via-env-grok", "via-entry": "via-entry-grok"} and "function global:via-entry-grok {" in t
        and "\n    via-env-grok\n" in t and "via-path" in t and set(rep["verbs"]) == {"via-enter", "via-env-grok", "via-entry-grok", "via-ingest"})
    if CMDMATRIX.exists():
        t2, rep2 = clean_cmdmatrix(_read(CMDMATRIX))
        chk("③ 真件 CmdMatrix(收容包 b383)去尾 3 行+撞名≥2+函式 ≥ 12", rep2["stripped"] == 3 and len(rep2["renamed"]) >= 2 and len(rep2["verbs"]) >= 12,
            f"(令 {len(rep2['verbs'])};改名 {rep2['renamed']})")
    else:
        chk("③ 真件 CmdMatrix(收容包 b383)", False, "缺")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "via_vdf_312" / "Scripts").mkdir(parents=True)
        (root / "via_vdf_312" / "Scripts" / "python.exe").write_text("", encoding="utf-8")
        (root / "via_vrn" / "bin").mkdir(parents=True)
        (root / "via_vrn" / "bin" / "python").write_text("", encoding="utf-8")
        r1 = resolve_env_python("vdf", roots=[root], environ={})
        r2 = resolve_env_python("vrn", roots=[root], environ={})
        r3 = resolve_env_python("zzz", roots=[root], environ={})
        r4 = resolve_env_python("vdf", roots=[root], environ={"VIA_PY_VDF": str(root / "via_vrn" / "bin" / "python")})
        chk("④ 家族境 python 解析(候選名序/Scripts 與 bin 兩制/base 退路誠實/VIA_PY_<FAMILY> 覆寫勝)",
            r1["env"] == "via_vdf_312" and r1["state"] == "OK" and r2["env"] == "via_vrn" and r3["state"] == "BASE_FALLBACK"
            and r3["python"] == sys.executable and r4["source"] == "env VIA_PY_VDF")
    rep = status(do_print=False, quiet=True, environ={})
    layers = [x["layer"] for x in rep["lamps"]]
    chk("⑤ 燈板(零網路;≥12 層含 RunGate;三態+GREY;落 ENTRY_latest.json/.html 零 CDN)",
        len(layers) >= 12 and all(x["lamp"] in ("GREEN", "YELLOW", "RED", "GREY") for x in rep["lamps"])
        and (OUT / "ENTRY_latest.json").exists() and 'src="http' not in _read(OUT / "ENTRY_latest.html")
        and all(k in layers for k in ("GitHub", "Mother", "Data", "Env", "EnvGov", "RunGate", "VDF-DB", "VAP", "Matrix", "Console", "Grok")),
        f"({rep['verdict']};{len(layers)} 層)")
    rows = roster(do_print=False)
    names = [r["name"] for r in rows]
    chk("⑥ 短指令冊(母倉∪Grok;名稱唯一;撞名列 -grok)", len(rows) >= 60 and len(names) == len(set(names))
        and any(r["state"].startswith("撞名改名") for r in rows if r["owner"] == "GROK"), f"({len(rows)} 令)")
    pl = plan(do_print=False)
    chk("⑦ 一貼即用次序(≥13 步;含 envgov/REPAIR_BASE/rungate/famui/vdfdb/ckpt/vapone/矩陣/webconsole)",
        len(pl) >= 13 and all(any(k in r["cmd"] for r in pl) for k in ("via-envgov", "REPAIR_BASE", "via-rungate", "via-famui", "via-vdfdb", "ckpt", "via-vapone", "矩陣", "via-webconsole")))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(只增不減/原件零觸碰/誠實三態/零 CDN/尾版律/ACCEL-BRIDGE)",
        all(k in src for k in ("只增不減", "原件零觸碰", "誠實三態", "零 CDN", "尾版律", "ACCEL-BRIDGE")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 單一入口橋(CGC_MDL136_EntryBridge)· 八檢自測(零網路)===")
        return selftest()
    quiet = "--quiet" in a
    as_json = "--json" in a
    verb = next((x for x in a if x in ("status", "roster", "plan", "envpy", "cmdmatrix-clean")), "status")   # 批387:動詞白名單
    try:
        if verb == "status":
            rep = status(do_print=not as_json, quiet=quiet)
            if as_json:
                print(json.dumps(rep, ensure_ascii=False, indent=1))
            return 0
        if verb == "roster":
            rows = roster(do_print=not as_json, quiet=quiet)
            if as_json:
                print(json.dumps(rows, ensure_ascii=False, indent=1))
            return 0
        if verb == "plan":
            rows = plan(do_print=not as_json, quiet=quiet)
            if as_json:
                print(json.dumps(rows, ensure_ascii=False, indent=1))
            return 0
        if verb == "envpy":
            fam = next((x for x in a[a.index("envpy") + 1:] if not x.startswith("--")), "vdf")
            r = resolve_env_python(fam)
            print(json.dumps(r, ensure_ascii=False) if as_json else r["python"])
            if not as_json and r["state"] != "OK":
                print(f"  [envpy] {fam} 境未見 → base 退路;{r.get('hint', '')}", file=sys.stderr)
            return 0
        if verb == "cmdmatrix-clean":
            if not CMDMATRIX.exists():
                print(f"[cmdmatrix-clean] 缺 {CMDMATRIX}")
                return 2
            t, rep = clean_cmdmatrix(_read(CMDMATRIX))
            sys.stdout.write(t)
            return 0
        print(__doc__)
        return 2
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
