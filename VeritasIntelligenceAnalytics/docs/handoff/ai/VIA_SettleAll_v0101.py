#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_SettleAll v0101 — 一支 Python 收尾三系統:全景檢視 → 識別問題 → AST 定位 → 經各系統自己的入口處理 → 報告 + 貼回包。

v0101(PR #585 Codex 審查三項 · 都是 v0100 會把失敗報成 GREEN):
  · ⑤ VRN:舊的 PASS 收尾收據會蓋過本次失敗 / 逾時(rc 124)→ 本次 rc 不是 0 / 2 一律 RED;收據不是本次寫的(mtime 早於本次開跑 · 或 check 模式不重寫)不拿來判 GREEN。
  · ⑥ VCGC:燈只看 test --quick → handoff check 失敗 / 有紅照樣 GREEN → 兩者取最差(交接閘紅 = RED · CLAUDE.md「BLOCKED / REVIEW / 缺證據絕不能寫成成功」)。
  · ④ VDF:rc 0 但頁上有 YELLOW 被升成 GREEN → 燈取最差(RED > YELLOW > GREEN)。
  三個判燈抽成純函數(vdf_lamp / vrn_lamp / vcgc_lamp)· 自測 +3 項。v0100 一字不動。

操作員 2026-11-02:「在全景式分析檢視 識別問題 AST 定位 GENERATE A CODE TO SETTLE DOWN AND HANDLE ALL ABOVE」。
要處理的(2026-11-02 Release Closure 報告 VIA_ReleaseClosure_20261102.md):
  ① 桌機落後 GitHub 719 提交 + 2 個沒推 → --ff-only 一直不成功 → VDF 還跑 v0162:③ 同步用合併(不 rebase · 不強推 · 不丟桌機提交 ·
     有沒提交的改動就不合併 · 失敗自動 merge --abort)。
  ② VDF ui rc 1 的紅字被截斷:④ 跑 VDF 尾版 ui 拿全文 → traceback 逐框 AST 定位(在哪個 def · 原文那一行)· AttributeError 再掃同家族
     每一版誰定義 / 誰先讀那個屬性(前版鏈 __getattr__ 轉手落空的根因)· 遞迴偵測。
  ③ VRN:⑤ 跑 RoundAll 尾版 repair(= Handle-All 那一輪)→ 讀收尾頁燈與負責方。
  ④ VCGC:⑥ handoff check(交接閘紅按類別計)+ test --quick(串測總行 · 紅站)。
  ⑤ ① 環境(duckdb · pyarrow · pwsh)與 ② AST 全景(8 個家族全部版本 ast.parse + compile · 只在記憶體 · 不執行)。
四系統對等:本檔只經各系統自己的入口跑(VDF_SystemManager · VRN2_RoundAll · VCGC 主控台),不改他系統的檔;只寫 VIA_Reports/settle 與 Downloads 貼回包。
用法:python VIA_SettleAll_v0101.py [--root <倉根>] [--only scan,sync,vdf,vrn,vcgc,report] [--no-sync] [--vrn repair|check|skip] [--selftest]
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔零網路。"""
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


import argparse
import ast
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

NAME = "VIA_SettleAll"
VERSION = "v0101"
BRANCH = "claude/vrn2-closeout-authorization-y4ixl7"
STAGES = ("scan", "sync", "vdf", "vrn", "vcgc", "report")
FAMILIES = {   # 家族 → (夾, 前綴);只讀,不改他系統的檔
    "VRN_SystemManager": ("functional modules/VRN", "VRN_SystemManager_v"),
    "VDF_SystemManager": ("functional modules/VDF", "VDF_SystemManager_v"),
    "VDF_ENG236_FetchMatrixUI": ("functional modules/VDF/engine", "VDF_ENG236_FetchMatrixUI_v"),
    "CGC_MDL149_Console": ("supportive modules/registry", "CGC_MDL149_VeritasCentralGovernanceConsole_v"),
    "CGC_MDL261_UIEngine": ("supportive modules/registry", "CGC_MDL261_UIEngine_v"),
    "CGC_MDL274_HealthMatrix": ("supportive modules/registry", "CGC_MDL274_HealthMatrix_v"),
    "CGC_MDL224_TestAuto": ("supportive modules/registry", "CGC_MDL224_TestAuto_v"),
    "VRN2_RoundAll": ("docs/handoff/ai", "VRN2_RoundAll_v"),
}
FRAME_RX = re.compile(r'File "(?P<file>[^"]+)", line (?P<line>\d+)(?:, in (?P<func>\S+))?')
EXC_RX = re.compile(r"^(?P<type>[A-Za-z_][\w.]*(?:Error|Exception|Warning|Exit|Interrupt))(?::\s*(?P<msg>.*))?$")
ATTR_RX = re.compile(r"(?:module|object) '(?P<mod>[^']+)' has no attribute '(?P<attr>[^']+)'")
LOG = []
RANK = {"GREEN": 0, "GRAY": 0, "YELLOW": 1, "RED": 2}


def worst(*lamps) -> str:
    """燈取最差:RED > YELLOW > GREEN(GRAY 當 GREEN);認不得的當 YELLOW(不冒充綠)。"""
    out = "GREEN"
    for x in lamps:
        x = x if x in RANK else "YELLOW"
        if RANK[x] > RANK[out]:
            out = x
    return out


def vdf_lamp(rc: int, lamps: list) -> str:
    """④ rc 不是 0 → RED;rc 0 → 頁上各段燈取最差(YELLOW 不升 GREEN)。"""
    return "RED" if rc != 0 else worst(*lamps)


def vrn_lamp(rc: int, state: dict | None, fresh: bool) -> str:
    """⑤ 本次 rc 不是 0 / 2 → RED(舊收據不救);收據不是本次寫的 → 最多 YELLOW;本次寫的 PASS → GREEN;VRN-2 側有待修 → RED。"""
    if rc not in (0, 2):
        return "RED"
    if not state or not fresh:
        return "YELLOW"
    if (state.get("per_owner") or {}).get("VRN-2"):
        return "RED"
    return "GREEN" if state.get("state") == "PASS" else "YELLOW"


def vcgc_lamp(test_lamp: str | None, test_rc: int, handoff_rc: int, handoff_red: dict) -> str:
    """⑥ test --quick 總燈與 handoff check 取最差:沒讀到總行 → RED;test rc 不是 0 / 2 → RED;交接閘有紅或 rc 不是 0 → RED。"""
    t = test_lamp if test_lamp in RANK else "RED"
    if test_rc not in (0, 2):
        t = "RED"
    h = "RED" if (handoff_rc != 0 or handoff_red) else "GREEN"
    return worst(t, h)


def say(lamp: str, step: str, text: str, nxt: str = "") -> None:
    line = "[%s] %s · %s" % (lamp, step, text)
    LOG.append({"lamp": lamp, "step": step, "text": text, "next": nxt})
    print(line + (("\n       → " + nxt) if nxt else ""), flush=True)


def vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def family_files(via: Path, folder: str, prefix: str) -> list:
    base = via / folder
    if not base.is_dir():
        return []
    pat = ("**/" if folder == "docs/handoff/ai" else "") + prefix + "*.py"
    return sorted((p for p in base.glob(pat) if vnum(p) >= 0), key=vnum)


def run(cmd, cwd=None, timeout=1800, env=None) -> tuple:
    """→ (rc, 輸出全文);逾時回 rc 124。只跑各系統自己的入口。"""
    e = dict(os.environ)
    e.update({"PYTHONUTF8": "1", "VIA_FROM_VCGC": "YES", "VIA_NO_OPEN": "1"})
    e.update(env or {})
    try:
        p = subprocess.run([str(c) for c in cmd], cwd=str(cwd) if cwd else None, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=e)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        return 124, (out.decode("utf-8", "replace") if isinstance(out, bytes) else out) + "\n[逾時 %d 秒]" % timeout
    except OSError as exc:
        return 127, "%s: %s" % (type(exc).__name__, exc)


# ---------------------------------------------------------------- 找根 · git
def find_root(explicit=None) -> Path | None:
    cands = [explicit, os.environ.get("VIA_ROOT"), os.environ.get("VRN2_ROOT")]
    cands += [str(p) for p in Path(__file__).resolve().parents]
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    cands += [str(home / "OneDrive" / "Documents" / "movies-dataset"), str(home / "Documents" / "movies-dataset")]
    for c in cands:
        if not c:
            continue
        p = Path(c)
        for via in (p, p / "VeritasIntelligenceAnalytics"):
            if (via / "functional modules").is_dir() and (via / "supportive modules").is_dir():
                return via
    return None


def parse_ahead_behind(text: str) -> tuple:
    """`git rev-list --left-right --count A...B` → (只在本機, 只在遠端)。"""
    m = re.match(r"\s*(\d+)\s+(\d+)\s*$", text or "")
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def git_state(repo: Path, fetch: bool = True) -> dict:
    st = {"repo": str(repo), "branch": None, "head": None, "fetched": False}
    if shutil.which("git") is None:
        st["error"] = "沒有 git"
        return st
    st["branch"] = run(["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"])[1].strip()
    st["head"] = run(["git", "-C", repo, "rev-parse", "--short", "HEAD"])[1].strip()
    if fetch:
        for ref in (BRANCH, "main"):
            rc, _ = run(["git", "-C", repo, "fetch", "-q", "origin", ref], timeout=300)
            st["fetched"] = st["fetched"] or rc == 0
    for ref in (BRANCH, "main"):
        rc, out = run(["git", "-C", repo, "rev-list", "--left-right", "--count", "HEAD...origin/" + ref])
        a, b = parse_ahead_behind(out) if rc == 0 else (None, None)
        st[ref] = {"local_only": a, "remote_only": b}
    rc, out = run(["git", "-C", repo, "status", "--porcelain"])
    lines = [x for x in out.splitlines() if x.strip()] if rc == 0 else []
    st["dirty_tracked"] = sum(1 for x in lines if not x.startswith("??"))
    st["untracked"] = sum(1 for x in lines if x.startswith("??"))
    return st


# ---------------------------------------------------------------- AST 全景 · AST 定位
def ast_scan(paths) -> dict:
    """每檔 ast.parse + compile(只在記憶體 · 不執行)→ 錯誤位置;編譯警告(如無效跳脫)記檔:行,不印、不算錯。"""
    import warnings
    bad, warns = [], []
    for p in paths:
        try:
            src = Path(p).read_text(encoding="utf-8-sig")
        except OSError as exc:
            bad.append({"file": str(p), "kind": "READ", "msg": type(exc).__name__})
            continue
        try:
            with warnings.catch_warnings(record=True) as ws:
                warnings.simplefilter("always")
                compile(ast.parse(src, filename=str(p)), str(p), "exec")
            warns += [{"file": Path(p).name, "line": w.lineno, "msg": str(w.message)[:120]} for w in ws]
        except SyntaxError as exc:
            bad.append({"file": str(p), "kind": "SYNTAX", "line": exc.lineno, "msg": exc.msg})
        except (ValueError, TypeError) as exc:
            bad.append({"file": str(p), "kind": "COMPILE", "msg": str(exc)[:160]})
    return {"files": len(paths), "errors": bad, "warnings": warns}


def enclosing_def(path: Path, line: int) -> dict:
    """AST 定位:這一行在哪個 def / class 裡(最內層)+ 原文那一行。"""
    try:
        src = Path(path).read_text(encoding="utf-8-sig")
        tree = ast.parse(src)
    except (OSError, SyntaxError, ValueError):
        return {"def": None, "src": None}
    best = None
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.lineno <= line <= (n.end_lineno or n.lineno):
            if best is None or n.lineno >= best.lineno:
                best = n
    lines = src.splitlines()
    return {"def": ("%s (L%d-%d)" % (best.name, best.lineno, best.end_lineno)) if best else "<module>",
            "src": lines[line - 1].strip()[:200] if 0 < line <= len(lines) else None}


def _defined_names(tree) -> set:
    names = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        for x in ast.walk(n):
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store):
                names.add(x.id)
            elif isinstance(x, ast.alias):
                names.add((x.asname or x.name).split(".")[0])
            elif isinstance(x, ast.Global):
                names.update(x.names)
            elif isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "setattr" and len(x.args) >= 2 \
                    and isinstance(x.args[1], ast.Constant) and isinstance(x.args[1].value, str):
                names.add(x.args[1].value)
    return names


def attr_trace(files, attr: str) -> dict:
    """同家族每一版:誰定義 attr、誰去讀它(X.attr / getattr(X, 'attr'))· 只讀 AST。"""
    defined, used = [], []
    for p in files:
        try:
            tree = ast.parse(Path(p).read_text(encoding="utf-8-sig"))
        except (OSError, SyntaxError, ValueError):
            continue
        if attr in _defined_names(tree):
            defined.append(Path(p).name)
        for n in ast.walk(tree):
            hit = (isinstance(n, ast.Attribute) and n.attr == attr) or (
                isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("getattr", "hasattr")
                and len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) and n.args[1].value == attr)
            if hit:
                used.append("%s:L%d" % (Path(p).name, n.lineno))
    first_def = min((vnum(Path(x)) for x in defined), default=None)
    early = [u for u in used if first_def is None or vnum(Path(u.split(":")[0])) <= first_def]
    return {"attr": attr, "defined_in": defined, "used_at": used[:40], "used_before_defined": early[:20]}


def diagnose(text: str, via: Path | None = None) -> dict:
    """Traceback → 例外 · 每一框(AST 定位)· 前版鏈轉手 · 屬性缺 → 同家族誰定義 / 誰讀。"""
    frames = [m.groupdict() for m in FRAME_RX.finditer(text or "")]
    exc = None
    for ln in reversed((text or "").splitlines()):
        m = EXC_RX.match(ln.strip())
        if m and "Warning" not in m.group("type"):
            exc = {"type": m.group("type"), "msg": (m.group("msg") or "").strip()}
            break
    out = {"exception": exc, "frames": [], "recursion": False, "hint": ""}
    for f in frames[-12:]:
        p = Path(f["file"])
        loc = enclosing_def(p, int(f["line"])) if p.is_file() else {"def": None, "src": None}
        out["frames"].append({"file": p.name, "line": int(f["line"]), "func": f["func"], **loc})
    names = [(f["file"], f["line"]) for f in frames]
    out["recursion"] = len(names) > 40 and len(set(names[-40:])) <= 4 or "RecursionError" in (exc or {}).get("type", "")
    hops = [f for f in out["frames"] if f["func"] == "__getattr__"]
    if exc and exc["type"].endswith("AttributeError"):
        m = ATTR_RX.search(exc["msg"])
        attr = m.group("attr") if m else None
        out["attr"] = attr
        fam_files = []
        if attr and frames:
            stem = re.sub(r"_v\d+$", "", Path(frames[-1]["file"]).stem)
            folder = Path(frames[-1]["file"]).parent
            if folder.is_dir():
                fam_files = sorted((p for p in folder.glob(stem + "_v*.py") if vnum(p) >= 0), key=vnum)
            out["trace"] = attr_trace(fam_files, attr) if fam_files else None
        tr = out.get("trace") or {}
        if attr and tr.get("defined_in") == []:
            out["hint"] = "屬性 %s 整個家族都沒有定義 → 讀它的那一版(%s)要改成先檢查或出新版補定義" % (attr, ", ".join(tr.get("used_at", [])[:3]) or "?")
        elif attr and tr.get("used_before_defined"):
            out["hint"] = "屬性 %s 最早在 %s 定義,但更早的版就在讀(%s)→ 前版鏈轉手 %d 次後落到沒有它的那一版" % (
                attr, tr["defined_in"][0], ", ".join(tr["used_before_defined"][:3]), len(hops))
        elif attr:
            out["hint"] = "屬性 %s 經前版鏈轉手 %d 次後找不到 → 看 frames 第一個非 __getattr__ 的框(呼叫端)" % (attr, len(hops))
    elif out["recursion"]:
        out["hint"] = "遞迴:同幾框反覆出現(前版鏈互指或 __getattr__ 自己找自己)"
    elif exc:
        out["hint"] = "%s:看最後一框 %s" % (exc["type"], (out["frames"][-1]["file"] + ":%d" % out["frames"][-1]["line"]) if out["frames"] else "?")
    return out


# ---------------------------------------------------------------- 各階段
def stage_scan(via: Path, ctx: dict) -> None:
    env = {"python": sys.version.split()[0], "exe": sys.executable, "pwsh": shutil.which("pwsh") or shutil.which("pwsh.exe")}
    for mod in ("duckdb", "pyarrow", "pandas", "fitz", "pypdfium2"):
        try:
            m = __import__(mod)
            env[mod] = getattr(m, "__version__", "ok")
        except Exception:                              # noqa: BLE001 — 只量有沒有
            env[mod] = None
    ctx["env"] = env
    miss = [k for k in ("duckdb", "pyarrow") if not env[k]]
    say("YELLOW" if miss else "GREEN", "① 環境", "Python %s · duckdb %s · pyarrow %s · pwsh %s" % (env["python"], env["duckdb"], env["pyarrow"], "有" if env["pwsh"] else "沒有"),
        ("缺 %s → VDF 表頭 / 增量庫 / Parquet 自測會紅(經 VCGC 環境工具裝)" % " · ".join(miss)) if miss else "")
    fams = {}
    allfiles = []
    for fam, (folder, prefix) in FAMILIES.items():
        fs = family_files(via, folder, prefix)
        allfiles += fs
        fams[fam] = {"tail": fs[-1].name if fs else None, "versions": len(fs)}
    sc = ast_scan(allfiles)
    ctx["families"], ctx["ast"] = fams, sc
    say("RED" if sc["errors"] else "GREEN", "② AST 全景", "家族 %d · 檔 %d · 語法 / 編譯錯 %d · 編譯警告 %d(凍結版不改 · 檔:行在報告)· 尾版 %s" % (
        len(fams), sc["files"], len(sc["errors"]), len(sc["warnings"]), " · ".join("%s=%s" % (k, (v["tail"] or "—").rsplit("_v", 1)[-1].replace(".py", "")) for k, v in fams.items())),
        "錯誤位置在報告 ast.errors(檔:行)" if sc["errors"] else "")


def stage_sync(via: Path, ctx: dict, do_sync: bool) -> None:
    repo = via.parent
    st = git_state(repo)
    ctx["git_before"] = st
    if st.get("error"):
        say("RED", "③ 同步", st["error"])
        return
    br = st.get(BRANCH) or {}
    behind, ahead = br.get("remote_only"), br.get("local_only")
    txt = "分支 %s · HEAD %s · 比 GitHub 少 %s 個提交 · 多 %s 個沒推 · 改動 %d · 未追蹤 %d" % (st["branch"], st["head"], behind, ahead, st["dirty_tracked"], st["untracked"])
    if not do_sync or not behind:
        say("GREEN" if not behind else "YELLOW", "③ 同步", txt + (" · 已一致" if not behind else " · 這次不同步(--no-sync)"))
        return
    if st["dirty_tracked"]:
        say("YELLOW", "③ 同步", txt + " · 有沒提交的改動 → 不合併(不動你的檔)", "先提交或還原那些改動,再跑本檔")
        return
    rc, out = run(["git", "-C", repo, "merge", "--no-edit", "origin/" + BRANCH], timeout=600)
    if rc != 0:
        run(["git", "-C", repo, "merge", "--abort"])
        ctx["sync_error"] = out[-3000:]
        say("RED", "③ 同步", txt + " · 合併沒成功 → 已 merge --abort 還原", "把貼回包上傳給 AI(合併衝突的檔名在 sync_error)")
        return
    st2 = git_state(repo, fetch=False)
    ctx["git_after"] = st2
    say("GREEN", "③ 同步", "合併 origin/%s 成功(不 rebase · 不強推 · 桌機的提交保留)· HEAD %s → %s" % (BRANCH, st["head"], st2["head"]),
        "桌機自己的 %s 個提交還沒推 → 照 ChainShip 上船或 git push(你決定)" % ahead if ahead else "")


def _tail(via: Path, fam: str) -> Path | None:
    folder, prefix = FAMILIES[fam]
    fs = family_files(via, folder, prefix)
    return fs[-1] if fs else None


def stage_vdf(via: Path, ctx: dict) -> None:
    t = _tail(via, "VDF_SystemManager")
    if not t:
        say("RED", "④ VDF ui", "找不到 VDF_SystemManager 尾版")
        return
    rc, out = run([sys.executable, t, "ui"], cwd=t.parent, timeout=1800)
    ctx["vdf"] = {"tail": t.name, "rc": rc, "out_tail": out[-6000:]}
    lamps = re.findall(r"·\s*(GREEN|YELLOW|RED)\s*$", out, re.M)
    if rc == 0:
        lp = vdf_lamp(rc, lamps)
        say(lp, "④ VDF ui", "%s ui · rc 0 · 燈 %s" % (t.name, " ".join(lamps[-6:]) or "—"),
            "頁上有 %s 段 → 看 VDF 頁該段的原因(不是假綠)" % lp if lp != "GREEN" else "")
        return
    d = diagnose(out, via)
    ctx["vdf"]["diagnosis"] = d
    e = d.get("exception") or {}
    say("RED", "④ VDF ui", "%s ui · rc %s · %s: %s" % (t.name, rc, e.get("type", "?"), (e.get("msg") or "")[:160]),
        "AST 定位:" + (d.get("hint") or "見報告 vdf.diagnosis") + " · 把貼回包上傳給 AI")


def stage_vrn(via: Path, ctx: dict, mode: str) -> None:
    if mode == "skip":
        say("GRAY", "⑤ VRN", "這次不跑(--vrn skip)")
        return
    t = _tail(via, "VRN2_RoundAll")
    if not t:
        say("RED", "⑤ VRN", "找不到 VRN2_RoundAll")
        return
    only = "package,fix,report,closeout,pasteback" if mode == "repair" else "package,preflight,selftest"
    t0 = _dt.datetime.now().timestamp()
    rc, out = run([sys.executable, t, "--root", via, "--only", only, "--no-open"], cwd=t.parent, timeout=14400)
    cj = via / "VIA_Reports" / "vrn2" / "VRN2_CloseoutUI_latest.json"
    state = None
    try:
        fresh = cj.stat().st_mtime >= t0 - 1
    except OSError:
        fresh = False
    try:
        c = json.loads(cj.read_text(encoding="utf-8"))
        state = {"state": c.get("state"), "per_owner": {o: sum(1 for i in c.get("items") or [] if i.get("owner") == o) for o in ("VRN-2", "VCGC", "人工", "資料源")}}
    except (OSError, ValueError):
        pass
    nxt = [ln for ln in out.splitlines() if ln.startswith("NEXT:")]
    ctx["vrn"] = {"roundall": t.name, "rc": rc, "closeout": state, "closeout_fresh": fresh, "next": nxt[-1] if nxt else None, "out_tail": out[-4000:]}
    lamp = vrn_lamp(rc, state, fresh)
    say(lamp, "⑤ VRN", "%s %s · rc %s · 收尾 %s %s%s" % (t.name, mode, rc, (state or {}).get("state"), (state or {}).get("per_owner"),
        "" if fresh else " · 收尾收據不是本次寫的(舊的 · 不拿來判綠)"),
        "REVIEW = 看收尾頁人工項原文後 --confirm(只有你打才算)" if state and state["state"] == "REVIEW" else ("把貼回包上傳給 AI" if lamp == "RED" else ""))


def stage_vcgc(via: Path, ctx: dict) -> None:
    t = _tail(via, "CGC_MDL149_Console")
    if not t:
        say("RED", "⑥ VCGC", "找不到 VCGC 主控台")
        return
    rc1, out1 = run([sys.executable, t, "handoff", "check"], cwd=via.parent, timeout=1200)
    kinds = {}
    for k in re.findall(r"^\[RED\] ([A-Z_]+) ", out1, re.M):
        kinds[k] = kinds.get(k, 0) + 1
    rc2, out2 = run([sys.executable, t, "test", "--quick"], cwd=via.parent, timeout=3600)
    m = re.search(r"\[VCGC 全功能串測\] (\w+) · ([^\n]{0,160})", out2)
    reds = re.findall(r"^\s*\[RED\s*\]\s+(\S+)", out2, re.M)
    ctx["vcgc"] = {"handoff_rc": rc1, "handoff_red": kinds, "test_rc": rc2, "test_line": m.group(0) if m else None, "test_red": reds}
    lamp = vcgc_lamp(m.group(1) if m else None, rc2, rc1, kinds)
    say(lamp, "⑥ VCGC", "串測 %s · 紅站 %s · 交接閘 rc %s · 紅 %s" % (
        (m.group(2)[:90] if m else "沒讀到總行"), ", ".join(reds) or "0", rc1, " · ".join("%s %d" % kv for kv in sorted(kinds.items())) or "0"),
        "VCGC 的 closeout_lamp 才是 VCGC 驗收;交接閘紅多為歷史版本沒有測試收據(逐案補或裁定)" if kinds else "")


def stage_report(via: Path, ctx: dict) -> Path:
    out_dir = via / "VIA_Reports" / "settle"
    out_dir.mkdir(parents=True, exist_ok=True)
    ctx["log"] = LOG
    ctx["at"] = _dt.datetime.now().isoformat(timespec="seconds")
    j = out_dir / "SETTLE_latest.json"
    j.write_text(json.dumps(ctx, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    md = ["# %s %s · %s" % (NAME, VERSION, ctx["at"]), "", "| 燈 | 步驟 | 內容 | 下一步 |", "|---|---|---|---|"]
    md += ["| %s | %s | %s | %s |" % (x["lamp"], x["step"], x["text"].replace("|", "/"), x["next"].replace("|", "/")) for x in LOG]
    d = (ctx.get("vdf") or {}).get("diagnosis")
    if d:
        md += ["", "## VDF traceback · AST 定位", "", "例外:`%s`" % d.get("exception"), "", "提示:" + d.get("hint", ""), ""]
        md += ["- `%s:%d` · %s · `%s`" % (f["file"], f["line"], f.get("def"), f.get("src")) for f in d.get("frames", [])]
    (out_dir / "SETTLE_latest.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    dl = home / "Downloads" if (home / "Downloads").is_dir() else Path(tempfile.gettempdir())
    zp = dl / ("VIA_Settle_%s.zip" % _dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(j, "settle/SETTLE_latest.json")
        z.write(out_dir / "SETTLE_latest.md", "settle/SETTLE_latest.md")
        seen = set()
        for rel in ("vrn2/VRN2_CloseoutUI_latest.json", "vrn2/VRN2_RoundAll_latest.json", "vdf/VDF_UI_MANIFEST.json"):
            p = via / "VIA_Reports" / rel
            if p.is_file() and rel not in seen:
                seen.add(rel)
                z.write(p, rel)
    worst = "RED" if any(x["lamp"] == "RED" for x in LOG) else "YELLOW" if any(x["lamp"] == "YELLOW" for x in LOG) else "GREEN"
    say(worst, "⑦ 報告", "%s · %s · 貼回包 %s" % (j, out_dir / "SETTLE_latest.md", zp), "把貼回包上傳給 AI" if worst != "GREEN" else "")
    print("NEXT: [%s] %s · 貼回包 %s" % (worst, NAME, zp), flush=True)
    return zp


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    with tempfile.TemporaryDirectory(prefix="via_settle_") as td:
        d = Path(td)
        (d / "Fam_v0100.py").write_text("def a():\n    return 1\nPRIOR = None\n", encoding="utf-8")
        (d / "Fam_v0101.py").write_text("PRIOR = None\n\ndef go():\n    return PRIOR.b()\n\ndef __getattr__(n):\n    return getattr(PRIOR, n)\n", encoding="utf-8")
        (d / "Fam_v0102.py").write_text("def b():\n    return 2\n", encoding="utf-8")
        (d / "Bad_v0100.py").write_text("def x(:\n", encoding="utf-8")
        tb = ('Traceback (most recent call last):\n  File "%s", line 4, in go\n    return PRIOR.b()\n'
              '  File "%s", line 7, in __getattr__\n    return getattr(PRIOR, n)\n'
              "AttributeError: module 'Fam_prior' has no attribute 'b'\n") % (d / "Fam_v0101.py", d / "Fam_v0101.py")
        g = diagnose(tb)
        chk("① traceback → AttributeError · 屬性 b · 兩框 · AST 定位到 go / __getattr__",
            g["exception"]["type"] == "AttributeError" and g.get("attr") == "b" and [f["def"].split()[0] for f in g["frames"]] == ["go", "__getattr__"])
        chk("② 同家族追屬性:b 只在 v0102 定義 · v0101 L4 先讀(轉手 1 次)→ 提示點名",
            g["trace"]["defined_in"] == ["Fam_v0102.py"] and "Fam_v0101.py:L4" in g["trace"]["used_before_defined"] and "v0102" in g["hint"], g["hint"])
        g2 = diagnose("RecursionError: maximum recursion depth exceeded\n")
        chk("③ RecursionError → 遞迴提示", g2["recursion"] and "遞迴" in g2["hint"])
        (d / "Esc_v0100.py").write_text('"""a \\d b"""\n', encoding="utf-8")
        sc = ast_scan([d / "Fam_v0100.py", d / "Bad_v0100.py", d / "Esc_v0100.py"])
        chk("④ AST 全景:語法錯抓到檔與行(不執行)· 無效跳脫記成警告(檔:行)不算錯", len(sc["errors"]) == 1 and sc["errors"][0]["kind"] == "SYNTAX"
            and sc["errors"][0]["line"] == 1 and len(sc["warnings"]) == 1 and sc["warnings"][0]["file"] == "Esc_v0100.py", sc["warnings"])
        chk("⑤ git 計數解析:'2\\t719' → (2, 719) · 壞輸入 → (None, None)", parse_ahead_behind("2\t719\n") == (2, 719) and parse_ahead_behind("x") == (None, None))
        chk("⑥ 警告不當例外:SyntaxWarning 行被略過", diagnose("<unknown>:3: SyntaxWarning: invalid escape\nValueError: boom\n")["exception"]["type"] == "ValueError")
        via = d / "repo" / "VeritasIntelligenceAnalytics"
        (via / "functional modules").mkdir(parents=True)
        (via / "supportive modules").mkdir(parents=True)
        chk("⑦ 找根:--root 給倉根或 VIA 根都認得", find_root(str(d / "repo")) == via and find_root(str(via)) == via)
        rc, out = run([sys.executable, "-c", "import sys;print('x');sys.exit(3)"])
        chk("⑧ 子行程:rc 與輸出都拿到 · 找不到程式回 127", rc == 3 and "x" in out and run(["__no_such_cmd__"])[0] == 127)
    if shutil.which("git"):
        with tempfile.TemporaryDirectory(prefix="via_settle_git_") as tg:
            g = Path(tg)
            gx = lambda *a, cwd=None: run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=cwd)  # noqa: E731
            gx("init", "-q", "--bare", "-b", BRANCH, str(g / "remote.git"))
            gx("clone", "-q", str(g / "remote.git"), str(g / "up"))
            up = g / "up"
            for sub in ("VeritasIntelligenceAnalytics/functional modules", "VeritasIntelligenceAnalytics/supportive modules"):
                (up / sub).mkdir(parents=True)
                (up / sub / "k.txt").write_bytes(b"1\n")
            gx("checkout", "-q", "-b", BRANCH, cwd=up)
            gx("add", "-A", cwd=up); gx("commit", "-q", "-m", "a", cwd=up); gx("push", "-q", "origin", BRANCH, cwd=up)
            gx("clone", "-q", "-b", BRANCH, str(g / "remote.git"), str(g / "desk"))
            (up / "new.txt").write_bytes(b"n\n"); gx("add", "-A", cwd=up); gx("commit", "-q", "-m", "b", cwd=up); gx("push", "-q", "origin", BRANCH, cwd=up)
            desk_via = g / "desk" / "VeritasIntelligenceAnalytics"
            (g / "desk" / "VeritasIntelligenceAnalytics" / "functional modules" / "k.txt").write_bytes(b"dirty\n")
            c1, n1 = {}, len(LOG)
            stage_sync(desk_via, c1, True)
            refused = LOG[-1]["lamp"] == "YELLOW" and "不合併" in LOG[-1]["text"] and not (g / "desk" / "new.txt").exists()
            run(["git", "-C", g / "desk", "checkout", "--", "."])
            c2 = {}
            stage_sync(desk_via, c2, True)
            merged = LOG[-1]["lamp"] == "GREEN" and (g / "desk" / "new.txt").is_file() and (c2.get("git_after") or {}).get(BRANCH, {}).get("remote_only") == 0
            del LOG[n1:]
        chk("⑩ 同步(假遠端 · 真 git):有沒提交的改動 → 不合併、不動檔;乾淨 → 合併後跟遠端一致(少 0)", refused and merged, (refused, merged))
    chk("⑪ VDF 判燈:rc 0 + 頁上 YELLOW → YELLOW(不升綠)· 有 RED → RED · rc 1 → RED · 全綠 → GREEN",
        vdf_lamp(0, ["GREEN", "YELLOW"]) == "YELLOW" and vdf_lamp(0, ["GREEN", "RED"]) == "RED" and vdf_lamp(1, ["GREEN"]) == "RED" and vdf_lamp(0, ["GREEN"]) == "GREEN")
    st_pass = {"state": "PASS", "per_owner": {"VRN-2": 0}}
    chk("⑫ VRN 判燈:舊 PASS + 本次逾時 rc 124 → RED · 舊 PASS + rc 0(check 模式不重寫)→ YELLOW · 本次 PASS → GREEN · 本次 REVIEW → YELLOW · VRN-2 有待修 → RED",
        vrn_lamp(124, st_pass, False) == "RED" and vrn_lamp(0, st_pass, False) == "YELLOW" and vrn_lamp(0, st_pass, True) == "GREEN"
        and vrn_lamp(2, {"state": "REVIEW", "per_owner": {"VRN-2": 0}}, True) == "YELLOW" and vrn_lamp(2, {"state": "OPEN", "per_owner": {"VRN-2": 1}}, True) == "RED")
    chk("⑬ VCGC 判燈:串測 GREEN + 交接閘紅 → RED · 交接 rc 1 → RED · 沒讀到總行 → RED · 串測 YELLOW + 交接乾淨 → YELLOW · 都綠 → GREEN",
        vcgc_lamp("GREEN", 0, 0, {"EVIDENCE_INVALID": 1}) == "RED" and vcgc_lamp("GREEN", 0, 1, {}) == "RED" and vcgc_lamp(None, 0, 0, {}) == "RED"
        and vcgc_lamp("YELLOW", 2, 0, {}) == "YELLOW" and vcgc_lamp("GREEN", 0, 0, {}) == "GREEN" and vcgc_lamp("GREEN", 1, 0, {}) == "RED")
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑨ 橋在 · 不強推 · 不 rebase · 不寫他系統的檔(只寫 VIA_Reports/settle 與 Downloads 貼回包)",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and "--force" not in body and "rebase\"" not in body and "push\"" not in body
        and body.count(".write_text(") == 2)
    bad = len(ok) - sum(ok)
    print("[%s] %s %s --selftest · %d 項 · 不過 %d" % ("PASS" if not bad else "FAIL", NAME, VERSION, len(ok), bad), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="%s_%s" % (NAME, VERSION), description="全景檢視 → 同步 → VDF ui(AST 定位)→ VRN repair → VCGC 驗 → 報告 · 各系統只經自己的入口")
    ap.add_argument("--root")
    ap.add_argument("--only", default=",".join(STAGES))
    ap.add_argument("--no-sync", action="store_true")
    ap.add_argument("--vrn", choices=("repair", "check", "skip"), default="repair")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    via = find_root(a.root)
    if via is None:
        say("RED", "⓪ VIA 根", "找不到(查過 --root · VIA_ROOT · 本檔所在 · OneDrive\\Documents\\movies-dataset)", "加 --root <倉根>")
        return 1
    say("GREEN", "⓪ VIA 根", str(via))
    only = [s.strip() for s in a.only.split(",") if s.strip()]
    ctx = {"tool": NAME + " " + VERSION, "root": str(via)}
    if "scan" in only:
        stage_scan(via, ctx)
    if "sync" in only:
        stage_sync(via, ctx, not a.no_sync)
    if "vdf" in only:
        stage_vdf(via, ctx)
    if "vrn" in only:
        stage_vrn(via, ctx, a.vrn)
    if "vcgc" in only:
        stage_vcgc(via, ctx)
    if "report" in only:
        stage_report(via, ctx)
    return 1 if any(x["lamp"] == "RED" for x in LOG) else 2 if any(x["lamp"] == "YELLOW" for x in LOG) else 0


if __name__ == "__main__":
    sys.exit(main())
