#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL149_VeritasCentralGovernanceConsole v0173 — 薄尾:`via-vcgc enter` 一句進環境(位置 · 更新 · 閘 · 加速器 · 工具版本 · 啟動全部)

操作員 2026-09-29:「應該要有進入環境指令 由vcgc進入跑他的流程如規定 加入加速器並告知目前加速器 網路工具 layout工具版本
  ssot一切整合最佳化測試除錯更新啟動全部」。實錄:PowerShell 停在 C:\Users\tonyk,`git push` → not a git repository。
本尾版多收一個動詞(其餘原樣轉前一版):
  via-vcgc enter [--card] [--no-pull] [go 的參數 …]
  0 第一步 省 Token:紅就停(同 v0170 的規矩)。
  1 位置與更新:目前資料夾在不在倉內(不在 → 印那一行 Set-Location;本動詞的 git 一律 -C 倉根)· 分支 · HEAD · 上游 · 本機改動;
    git fetch 上游 → **只快轉**(merge --ff-only)。分岔不合併;本機改動會被蓋時 git 自己拒絕 —— 都照實印,不 stash、不 rebase、不 force。
    放在閘前:閘要判的是等一下真的會跑的碼;閘後座位冊若有變,既有流程推 GitHub 時也不會因為落後被拒而分岔。
    HEAD 有變 → 交給更新後的 VCGC 尾版(子行程 enter --no-pull),閘與後面各步都跑在新碼上。
  2 閘:照工作流 SSOT VCGC-WKF001-STP002 跑 status(政策整冊 · 子系統座位 · 加速器 / 網路已接);rc 不是 0 → 一步都不跑。
  3 加速器:VIA_SuperAccel_Module → SUP_MDL737 尾版 → 鎖冊那一本 Celeritas,activate():執行緒預算寫進本行程環境,
    後面 go 起的每一支子行程都帶著(L103 ①)。載不起來 / 載到的不是鎖冊那一本 / 執行緒預算沒套上 → 停。
  4 工具版本:鎖冊(CGC_MDL233 尾版 status)六件 —— 加速器 · 網路工具 · layout · nlp · token · frame —— 版號 · sha · 待啟用;
    網路載入器(SUP_MDL740 尾版)解析到哪一支、核心載不載得起來(不連網;同意閘只報開 / 閉)· layout 動詞走哪一支 · PS 模板章在不在。
    sha 對不上 / 缺件 / 網路核心載不起來 / layout 動詞走的不是鎖冊那一支 → 停(換版只經 via-vcgc tools activate … --apply)。
  5 啟動全部:交給 go(v0166;操作台 PowerShell 尾版跑整輪:閘 → ENV MANAGER → 註冊同步 → VDF → 全景實測 → … → 單一路徑驗證 → 紀錄上傳)。
    --card 只出卡不啟動。結尾一行總結 + 一筆中樞事件(verb enter;VIA_HUB_RUN 沒設就給本輪一個 enter- 輪號,結束還原)。
  Python 改不了 PowerShell 的目前資料夾:「先進倉再跑」要一句完成,得在短令冊加一行(L70:本批不動 .ps1,一次貼見批文件)。
只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。不設同意閘、不裝件;推送仍只走既有流程(本動詞自己不 push)。不用 TA-Lib。
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

import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
SUPP = VIA / "supportive modules"
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
ENTER_VERBS = ("enter",)
OWN_FLAGS = ("--card", "--no-pull")
MUST = ("accelerator", "network", "layout")          # 操作員點名要報的三件;鎖冊上缺任何一件都停
LAYOUT_DIR = SUPP / "70_VRN_Rules"                    # v0146 layout 動詞找 SUP_MDL743 的同一個夾(自測核 = PRIOR.LAYOUT_HUB)
LAYOUT_PATTERN = "SUP_MDL743_GenericLayoutHub_v*.py"  # 同上(自測核 = PRIOR.LAYOUT_PATTERN)
PS_TEMPLATE = SUPP / "ps7" / "VeritasCeleritas.PS7.ps1"
_DEFAULT = object()


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("vcgc_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = [p for p in folder.glob(pattern) if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def git(repo: Path, *args, timeout: int = 180) -> tuple:
    """(rc, stdout, stderr) of one git call on the repo. Never prompts, never opens an editor."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_EDITOR="true", GIT_MERGE_AUTOEDIT="no")
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, env=env, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return 124, "", f"git {args[0]} 逾時 {timeout}s"
    except OSError as exc:
        return 127, "", f"git 起不來:{type(exc).__name__}"
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _last(text: str) -> str:
    lines = [ln.strip() for ln in str(text or "").splitlines() if ln.strip()]
    return lines[-1][:160] if lines else "?"


def inside(child: Path, parent: Path) -> bool:
    c, p = os.path.normcase(str(child.resolve())), os.path.normcase(str(parent.resolve()))
    return c == p or c.startswith(p.rstrip("\\/") + os.sep)


def repo_root(via: Path = VIA, run=git) -> Path:
    rc, out, _err = run(via, "rev-parse", "--show-toplevel")
    return Path(out) if rc == 0 and out else via.parent


def position(repo: Path, cwd: Path | None = None) -> dict:
    """Where the operator's shell stands. Python cannot move it; it can only say the one line that does."""
    try:
        here = Path(cwd) if cwd is not None else Path.cwd()
        ok = inside(here, repo)
    except OSError:
        here, ok = Path("?"), False
    q = str(repo).replace("'", "''")
    line = f"Set-Location -LiteralPath '{q}'" if os.name == "nt" else f"cd '{q}'"
    return {"cwd": str(here), "in_repo": ok, "cd": "" if ok else line}


def update(repo: Path, pull: bool = True, run=git) -> dict:
    """Branch · HEAD · upstream · ahead/behind, then fast-forward only. Never merges, stashes, rebases or forces:
    a diverged branch is left alone, and git itself refuses a fast-forward that would overwrite local changes."""
    out = {"repo": str(repo), "branch": "", "head": "", "head_after": "", "upstream": "", "ahead": None, "behind": None,
           "dirty": None, "fetched": False, "moved": False, "state": "", "why": ""}
    rc, br, _err = run(repo, "rev-parse", "--abbrev-ref", "HEAD")
    if rc != 0:
        out.update(state="ABSENT", why="不是 git 倉(或 git 不在 PATH):" + _last(_err))
        return out
    out["branch"] = br
    out["head"] = out["head_after"] = run(repo, "rev-parse", "--short=12", "HEAD")[1]
    rc, st, _err = run(repo, "status", "--porcelain", "--untracked-files=no")
    out["dirty"] = len([ln for ln in st.splitlines() if ln.strip()]) if rc == 0 else None
    rc, up, _err = run(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if br == "HEAD" or rc != 0 or not up:
        out.update(state="SKIP", why="沒有上游分支(分離 HEAD 或沒設追蹤)· 不更新")
        return out
    out["upstream"] = up
    if pull:
        remote = run(repo, "config", f"branch.{br}.remote")[1] or up.split("/", 1)[0]
        ref = run(repo, "config", f"branch.{br}.merge")[1] or up.split("/", 1)[-1]
        rc, _o, err = run(repo, "fetch", "--quiet", remote, ref)
        out["fetched"] = rc == 0
        if rc != 0:
            out.update(state="YELLOW", why=f"fetch 沒成(rc {rc}):{_last(err)} · 照目前版本跑")
    rc, cnt, _err = run(repo, "rev-list", "--left-right", "--count", "HEAD...@{u}")
    if rc == 0 and len(cnt.split()) == 2:
        out["ahead"], out["behind"] = (int(x) for x in cnt.split())
    if out["state"]:
        return out
    if not pull:
        out.update(state="SKIP", why="--no-pull:不更新")
    elif out["behind"] is None:
        out.update(state="YELLOW", why="算不出和上游差幾個提交 · 照目前版本跑")
    elif out["behind"] == 0:
        push = f" · 本機多 {out['ahead']} 個提交還沒推(git -C \"{repo}\" push)" if out["ahead"] else ""
        out.update(state="OK", why="已是最新" + push)
    elif out["ahead"]:
        out.update(state="YELLOW", why=f"分岔(本機多 {out['ahead']} · 上游多 {out['behind']}):不自動合併"
                                       f" → 操作員決定:git -C \"{repo}\" pull --no-rebase · 照目前版本跑")
    else:
        rc, _o, err = run(repo, "merge", "--ff-only", "--quiet", "@{u}")
        after = run(repo, "rev-parse", "--short=12", "HEAD")[1]
        out["head_after"] = after
        if rc == 0 and after != out["head"]:
            out.update(state="OK", moved=True, why=f"快轉 {out['behind']} 個提交 {out['head']} → {after}")
        else:
            out.update(state="YELLOW", why=f"快轉沒成(git 拒絕,多半是本機改動會被蓋):{_last(err)} · 照目前版本跑")
    return out


def token_step() -> dict:
    card = PRIOR.first_step()
    if card is None:
        return {"lamp": "ABSENT", "missing": ["CGC_MDL226 步驟矩陣"], "line": "", "hint": ""}
    tok = card["token"]
    return {"lamp": "RED" if tok["missing"] else "GREEN", "missing": list(tok["missing"]), "line": card.get("ai_line", ""),
            "hint": tok.get("activate_hint", "")}


def _tool_act():
    tail = _newest(HERE, "CGC_MDL233_ToolActivate_v*.py")
    return _load(tail, "tool_activate_for_" + Path(__file__).stem) if tail else None


def accelerator(mod=_DEFAULT, act=_DEFAULT) -> dict:
    """Load the accelerator the lock book names and apply its thread budget to this process (children inherit it)."""
    mod = VIA_ACCEL if mod is _DEFAULT else mod
    out = {"state": "RED", "body": "", "pinned": "", "loader": "", "threads": None, "mode": None, "libs": "", "real": "",
           "applied": 0, "why": ""}
    if mod is None:
        out["why"] = "VIA_SuperAccel_Module 載不起來(加速器橋回 None)"
        return out
    try:
        act = _tool_act() if act is _DEFAULT else act
        pin = act.pinned("accelerator") if act is not None else None
    except Exception as exc:                       # 鎖冊讀不到:照實記,判定交給工具卡
        pin, out["why"] = None, f"鎖冊讀不到:{type(exc).__name__}"
    out["pinned"] = pin.name if pin else ""
    try:
        a = mod.activate(apply_limits=True)
    except Exception as exc:
        out["why"] = f"activate 例外 {type(exc).__name__}: {str(exc)[:120]}"
        return out
    cel = (getattr(mod, "_CEL", None) or {}).get("mod")
    applied = a.get("applied") or {}
    out.update(body=Path(str(getattr(cel, "__file__", "") or "")).name if a.get("celeritas") else "",
               loader=str(getattr(mod, "CANONICAL", "") or ""), threads=a.get("thread_budget"), mode=a.get("mode"),
               libs=f"{a.get('libs_available', 0)}/{a.get('libs_total', 0)}",
               real=f"{a.get('capability_real', 0)}/{a.get('capability_total', 0)}",
               applied=0 if "err" in applied else len(applied))
    if not a.get("celeritas") or not out["body"]:
        out["why"] = "Celeritas 沒載起來:" + str(a.get("err") or "?")[:160]
    elif out["pinned"] and out["body"] != out["pinned"]:
        out["why"] = f"載到 {out['body']},鎖冊是 {out['pinned']}"
    elif not out["applied"]:                        # Codex #372 P2:沒套上的執行緒預算不能報 GREEN、不能照樣交 go
        out["why"] = "執行緒預算沒套上:" + (str(applied["err"])[:120] if "err" in applied else "activate 沒回任何環境變數")
    else:
        out["state"] = "GREEN"
    return out


def tools_card(act=_DEFAULT, net=_DEFAULT, layout_dir: Path = LAYOUT_DIR, ps_template: Path = PS_TEMPLATE) -> dict:
    """The six locked tools with version and sha, where the network loader resolves and whether its core loads,
    which file the layout verb runs, and whether the PS template is there. Any drift stops the round."""
    act = _tool_act() if act is _DEFAULT else act
    if act is None:
        return {"state": "RED", "lock": "ABSENT", "rows": [], "problems": ["CGC_MDL233 工具啟用閘不在"], "net": {}, "layout": {},
                "ps": {}}
    st = act.status()
    rows = list(st.get("tools") or [])
    by = {r.get("family"): r for r in rows}
    problems = [f"{r.get('family')} {'檔不在' if r.get('pinned') == 'ABSENT' else 'sha 對不上鎖冊'}"
                for r in rows if r.get("sha_ok") is not True]
    problems += [f"{fam} 不在鎖冊" for fam in MUST if fam not in by]
    net_row = {"loader": "", "resolved": "", "core": False, "gate_open": None, "why": ""}
    if net is _DEFAULT:
        tail = _newest(SUPP / "network", "SUP_MDL740_NetUnified_v*.py")
        try:
            net = _load(tail, "net_loader_for_" + Path(__file__).stem) if tail else None
        except Exception as exc:
            net, net_row["why"] = None, f"網路載入器載不起來:{type(exc).__name__}: {str(exc)[:100]}"
    if net is not None:
        net_row["loader"] = Path(str(getattr(net, "__file__", "") or "")).name
        net_row["resolved"] = Path(str(getattr(net, "VIA_AEGIS_PATH", "") or "")).name
        try:
            core = net._PRIOR._aegis() if hasattr(net, "_PRIOR") else net._aegis()
            net_row["core"] = core is not None
            gs = net.gate_state()
            net_row["gate_open"] = bool(gs.get("open"))
        except Exception as exc:
            net_row["why"] = f"網路核心載入例外:{type(exc).__name__}: {str(exc)[:100]}"
    pinned_net = (by.get("network") or {}).get("pinned", "")
    if not net_row["loader"]:
        problems.append("網路載入器不在 · " + (net_row["why"] or "SUP_MDL740 尾版不在"))
    elif net_row["resolved"] != pinned_net:
        problems.append(f"網路載入器解析到 {net_row['resolved'] or '(無)'},鎖冊是 {pinned_net}")
    elif not net_row["core"]:
        problems.append("網路核心載不起來 · " + (net_row["why"] or "_aegis() 回 None"))
    picks = sorted(layout_dir.glob(LAYOUT_PATTERN))  # v0146 def_layout_hub() 的同一條:夾內 sorted()[-1],不看鎖冊
    layout = {"verb_uses": picks[-1].name if picks else "", "pinned": (by.get("layout") or {}).get("pinned", "")}
    if layout["verb_uses"] != layout["pinned"]:       # Codex #372 P2:layout 動詞實際跑的不是鎖冊那一支 = 漂移,和網路載入器同一把尺
        problems.append(f"layout 動詞走 {layout['verb_uses'] or '(夾內沒有)'},鎖冊是 {layout['pinned'] or '(無)'}"
                        " → 新版先經 VCGC 啟用:via-vcgc tools activate layout <檔> --apply")
    ps = {"path": str(ps_template), "present": ps_template.is_file()}
    if not ps["present"]:
        problems.append("PS 模板章不在 · " + ps_template.name)
    return {"state": "RED" if problems else "GREEN", "lock": st.get("lock", ""), "rows": rows, "problems": problems,
            "net": net_row, "layout": layout, "ps": ps}


def _verb(argv: list) -> int:
    """One VCGC verb through the whole chain (token line · v0168 event and sync · v0159 flow gate as usual)."""
    sys.stdout.flush()
    try:
        rc = PRIOR.main(argv)
    except SystemExit as exc:
        rc = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    sys.stdout.flush()
    return int(rc or 0)


def restart(args: list, runner=subprocess.run) -> int:
    """After a fast-forward: the updated newest VCGC tail carries on (enter --no-pull), so the gate reads the new code."""
    tail = _newest(HERE, _STEM + "_v*.py")
    rest = [a for a in args if a != "--no-pull"]
    print(f"[進入 1/5] HEAD 變了 → 交給更新後的 VCGC 尾版 {tail.name} 接著跑(enter --no-pull;閘與後面各步都跑在新碼上)")
    sys.stdout.flush()
    try:
        cwd = os.getcwd()
    except OSError:
        cwd = str(VIA)
    r = runner([sys.executable, str(tail), "enter", "--no-pull", *rest], cwd=cwd, env=dict(os.environ, VIA_FROM_VCGC="YES"))
    return int(getattr(r, "returncode", 1) or 0)


def _print_card(pos: dict, upd: dict) -> None:
    where = "倉內" if pos["in_repo"] else f"不在倉內 → 下 git 指令前先:{pos['cd']}(本動詞的 git 一律 -C 倉根,不受影響)"
    print(f"[進入 1/5 · 位置與更新] 目前夾 {pos['cwd']} · {where}")
    if upd["state"] == "ABSENT":
        print(f"  倉 {upd['repo']} · {upd['why']}")
        return
    dirty = "?" if upd["dirty"] is None else upd["dirty"]
    print(f"  倉 {upd['repo']} · 分支 {upd['branch']}{' → ' + upd['upstream'] if upd['upstream'] else ''} · HEAD {upd['head']}"
          f" · 本機改動 {dirty} 檔")
    print(f"  更新 {upd['state']}:{upd['why']}")


def _print_tools(acc: dict, tools: dict) -> None:
    ok = "全部 sha ✓" if not [r for r in tools["rows"] if r.get("sha_ok") is not True] else "有漂移"
    print(f"[進入 4/5 · 工具版本] 鎖冊 {tools['lock']} · {ok}(換版只經 via-vcgc tools activate <家族> <檔> --apply)")
    names = {"accelerator": "加速器", "network": "網路工具", "layout": "layout", "nlp": "nlp", "token": "token", "frame": "frame"}
    for r in tools["rows"]:
        fam = r.get("family")
        mark = "✓" if r.get("sha_ok") is True else "✗"
        extra = ""
        if fam == "accelerator":
            extra = " · 已載入" if acc.get("state") == "GREEN" and acc.get("body") == r.get("pinned") else " · 沒載入"
        elif fam == "network":
            n = tools["net"]
            same = "解析同一支" if n.get("resolved") == r.get("pinned") else f"解析到 {n.get('resolved') or '(無)'}"
            gate = "未知" if n.get("gate_open") is None else ("開" if n["gate_open"] else "閉(抓料 fail-closed;開閘是操作員的手)")
            extra = (f" · 載入器 {n.get('loader') or '(無)'} {same} · 核心{'已載入' if n.get('core') else '沒載起來'}(不連網)"
                     f" · 同意閘 {gate}")
        elif fam == "layout":
            lay = tools["layout"]
            extra = (" · layout 動詞走同一支" if lay.get("verb_uses") == r.get("pinned")
                     else f" · layout 動詞走 {lay.get('verb_uses') or '(無)'}(鎖冊 {r.get('pinned')})")
        wait = f" · 待啟用 {', '.join(r['waiting'])}" if r.get("waiting") else ""
        print(f"  {names.get(fam, fam):<6} {r.get('pinned')} {r.get('version') or ''} {mark}{extra}{wait}")
    ps = tools["ps"]
    print(f"  PS 模板 {Path(ps['path']).parent.name}/{Path(ps['path']).name} {'✓' if ps.get('present') else '✗ 不在'}")
    for p in tools["problems"]:
        print(f"  ✗ {p}")


def record(rc: int, t0: float, args: list, card: dict, folder: Path | None = None) -> None:
    """The round's summary event. Written last and ordered last: its t0 is the time it is written (the start is kept in
    `started`). v0168 run_events orders a run by t0, and the first event of a round must stay the H1 gate (status);
    with the wrapper's start as t0 the summary would sort before the gate it wraps (workflow RED, measured)."""
    now = time.time()
    ev = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "verb": "enter", "args": [str(a)[:80] for a in args[:6]],
          "rc": rc, "outcome": PRIOR.outcome(rc), "secs": round(now - t0, 1), "head": PRIOR._head()[:12], "error": "",
          "engine": Path(__file__).stem, "run": os.environ.get("VIA_HUB_RUN", ""), "t0": round(now, 3),
          "started": round(t0, 3), "target": _STEM, "act": "enter", "card": card}
    try:
        PRIOR.write_event(ev) if folder is None else PRIOR.write_event(ev, folder)
    except (OSError, TypeError, ValueError) as exc:  # 事件寫不進去不擋動作(v0168 同一個規矩),但照實說
        print(f"  [事件] 沒寫進去:{type(exc).__name__}")


def enter(args: list, **dep) -> int:
    t0 = time.time()
    own_run = not os.environ.get("VIA_HUB_RUN")
    if own_run:
        os.environ["VIA_HUB_RUN"] = f"enter-{datetime.now():%Y%m%d-%H%M%S}-{os.getpid()}"
    card: dict = {}
    rc = 1                                          # 中途例外 = FAIL 事件,例外照樣往上拋
    try:
        rc = _enter(list(args), card, dep)
    finally:
        record(rc, t0, list(args), card, dep.get("events"))
        if own_run:
            os.environ.pop("VIA_HUB_RUN", None)
    return rc


def _enter(args: list, card: dict, dep: dict) -> int:
    card_only = "--card" in args
    pull = "--no-pull" not in args
    go_args = [a for a in args if a not in OWN_FLAGS]
    tok = dep.get("token", token_step)()
    card["token"] = tok["lamp"]
    print(f"[進入 0/5 · 第一步 省 Token] {tok['lamp']}" + (f" · 缺 {tok['missing']} · {tok['hint']}" if tok["missing"] else ""))
    if tok["lamp"] != "GREEN":
        print("[進入] 第一步沒過:不讀政策、不開子系統,先修第一步(via-vcgc token)")
        return 2
    repo = dep.get("repo") or repo_root()
    pos = dep.get("position", position)(repo)
    upd = dep.get("update", update)(repo, pull)
    card.update(position=pos, update={k: upd[k] for k in ("state", "why", "branch", "head", "head_after", "ahead", "behind")})
    _print_card(pos, upd)
    if upd.get("moved"):
        card["restarted"] = True
        return dep.get("restart", restart)(args)
    print("[進入 2/5 · 閘] 照工作流 SSOT VCGC-WKF001-STP002 跑 status(政策整冊 · 子系統座位 · 加速器 / 網路已接)")
    g = dep.get("gate", lambda: _verb(["status"]))()
    card["gate"] = g
    if g != 0:
        print(f"[進入 2/5 · 閘] 沒過(rc {g}):閘沒過一步都不跑")
        return g
    print("[進入 2/5 · 閘] 過(rc 0)")
    acc = dep.get("accel", accelerator)()
    card["accelerator"] = {k: acc.get(k) for k in ("state", "body", "pinned", "loader", "threads", "mode", "why")}
    if acc["state"] == "GREEN":
        print(f"[進入 3/5 · 加速器] 已載入 {acc['body']}(= 鎖冊)· 載入器 {acc['loader']} · 執行緒預算 {acc['threads']}"
              f"({acc['mode']})寫進本行程 {acc['applied']} 個環境變數,後面每支子行程都帶 · lib 可用 {acc['libs']}"
              f" · 真實能力 {acc['real']}" + (f" · 註:{acc['why']}" if acc["why"] else ""))
    else:
        print(f"[進入 3/5 · 加速器] RED:{acc['why']} → 停(L103 ①:PY 要導入加速器,執行緒預算要套上)")
        return 2
    tools = dep.get("tools", tools_card)()
    card["tools"] = {"state": tools["state"], "problems": tools["problems"],
                     "pinned": {r.get("family"): r.get("pinned") for r in tools["rows"]}}
    _print_tools(acc, tools)
    if tools["state"] != "GREEN":
        print("[進入 4/5 · 工具版本] 有漂移或缺件 → 停(鎖冊是尺;不解鎖,先點名)")
        return 2
    pins = card["tools"]["pinned"]
    rc = 0
    if card_only:
        print("[進入 5/5 · 啟動全部] --card:只出卡,不啟動(要跑全部:via-vcgc enter)")
    else:
        print("[進入 5/5 · 啟動全部] via-vcgc go(操作台 PowerShell 尾版跑整輪:閘 → ENV MANAGER → 註冊同步 → VDF → 全景實測"
              " → … → 單一路徑驗證 → 紀錄上傳)")
        rc = dep.get("go", lambda a: _verb(["go", *a]))(go_args)
        card["go"] = rc
    print(f"[進入 · 總結] rc {rc} · {'倉內' if pos['in_repo'] else '倉外(git 先 ' + pos['cd'] + ')'} · 更新 {upd['state']}"
          f" · 閘 過 · 加速器 {acc['body']} 執行緒 {acc['threads']}({acc['mode']})· 網路工具 {pins.get('network')}"
          f" · layout {pins.get('layout')} · 啟動全部 {'略(--card)' if card_only else 'rc ' + str(rc)}")
    return rc


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] and args[0] in ENTER_VERBS:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
            return 2
        return enter(args[1:])
    return PRIOR.main(argv)


def selftest() -> int:
    import tempfile
    from types import SimpleNamespace
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    keep = os.environ.get("VIA_FROM_VCGC")
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main(["enter", "--card"]) == 2
    if keep is not None:
        os.environ["VIA_FROM_VCGC"] = keep
    chk("① enter 只收 VCGC 呼叫(沒有 VIA_FROM_VCGC = DENY rc 2)", denied)

    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        repo = t / "repo"
        (repo / "sub").mkdir(parents=True)
        (t / "elsewhere").mkdir()
        out, sub = position(repo, t / "elsewhere"), position(repo, repo / "sub")
        chk("② 位置:倉外 → 給一行進倉(指名倉根);倉內子夾 → 不給", not out["in_repo"] and str(repo).replace("'", "''") in out["cd"]
            and sub["in_repo"] and sub["cd"] == "", out["cd"])

        def g(*a, cwd=None):
            r = subprocess.run(["git", "-c", "user.name=VIA selftest", "-c", "user.email=selftest@via.invalid",
                                "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false", *a],
                               cwd=cwd, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f"git {a}: {r.stderr.strip()[:200]}")
            return r.stdout.strip()

        def commit(where: Path, name: str, text: str, push: bool = True):
            (where / name).write_text(text, encoding="utf-8")
            g("add", name, cwd=where)
            g("commit", "-q", "-m", name + " " + text, cwd=where)
            if push:
                g("push", "-q", cwd=where)

        origin, seed, a, b = t / "origin.git", t / "seed", t / "a", t / "b"
        g("init", "-q", "--bare", str(origin))
        g("init", "-q", str(seed))
        commit(seed, "f.txt", "1", push=False)
        g("remote", "add", "origin", str(origin), cwd=seed)
        g("push", "-q", "-u", "origin", "main", cwd=seed)
        g("clone", "-q", str(origin), str(a))
        g("clone", "-q", str(origin), str(b))
        head = lambda p: g("rev-parse", "--short=12", "HEAD", cwd=p)   # noqa: E731
        s1 = update(a)
        commit(b, "f.txt", "2")
        hb = head(b)
        s2 = update(a)
        commit(b, "g.txt", "3")
        h0 = head(a)
        s3 = update(a, pull=False)
        chk("③ 更新:已是最新 = OK 不動;上游多 1 = 只快轉到上游那一個 HEAD;--no-pull 不 fetch 不動",
            s1["state"] == "OK" and not s1["moved"] and s2["state"] == "OK" and s2["moved"] and s2["behind"] == 1
            and s2["head_after"] == hb == h0 and s3["state"] == "SKIP" and head(a) == h0 and not s3["fetched"],
            f"{s1['why']} | {s2['why']} | {s3['why']}")
        commit(b, "f.txt", "4")
        (a / "f.txt").write_text("local edit", encoding="utf-8")
        s4 = update(a)
        kept = (a / "f.txt").read_text(encoding="utf-8") == "local edit"
        g("checkout", "--", "f.txt", cwd=a)
        s4b = update(a)
        chk("④ 本機改動會被蓋 → git 拒絕快轉:YELLOW · HEAD 不動 · 改動留著;清掉後同一句就快轉",
            s4["state"] == "YELLOW" and not s4["moved"] and kept and s4["head_after"] == s4["head"]
            and s4b["state"] == "OK" and s4b["moved"], s4["why"])
        commit(a, "h.txt", "local", push=False)
        commit(b, "i.txt", "5")
        h1 = head(a)
        s5 = update(a)
        merges = g("rev-list", "--merges", "--count", "HEAD", cwd=a)
        g("checkout", "-q", "-b", "loose", cwd=a)
        s6 = update(a)
        s7 = update(t / "elsewhere")
        chk("⑤ 分岔 → 不合併(YELLOW · HEAD 不動 · 沒有合併提交);沒上游 → SKIP;不是倉 → ABSENT",
            s5["state"] == "YELLOW" and "分岔" in s5["why"] and s5["ahead"] == 1 and s5["behind"] == 1 and head(a) == h1
            and merges == "0"
            and s6["state"] == "SKIP" and s7["state"] == "ABSENT", f"{s5['why']} | {s6['why']}")

    acc = accelerator()
    act = _tool_act()
    pin = act.pinned("accelerator") if act else None
    fake_off = SimpleNamespace(activate=lambda apply_limits=True: {"celeritas": False, "err": "boom", "applied": {}})
    fake_other = SimpleNamespace(activate=lambda apply_limits=True: {"celeritas": True, "err": "", "applied": {"X": "1"},
                                                                     "thread_budget": 1, "mode": "safe"},
                                 _CEL={"mod": SimpleNamespace(__file__="/x/VeritasCeleritas_v" + "9999.py")}, CANONICAL="x")
    other = accelerator(mod=fake_other, act=act)

    def fake_applied(applied):                      # 鎖冊那一本載起來了,但執行緒預算沒套上(activate 回 err / 空)
        return SimpleNamespace(activate=lambda apply_limits=True: {"celeritas": True, "err": "", "applied": applied,
                                                                   "thread_budget": 2, "mode": "safe"},
                               _CEL={"mod": SimpleNamespace(__file__="/x/" + (pin.name if pin else "none"))}, CANONICAL="x")
    unapplied = [accelerator(mod=fake_applied(a), act=act) for a in ({"err": "RuntimeError: boom"}, {})]
    chk("⑥ 加速器:載入的就是鎖冊那一本 · 執行緒預算寫進本行程環境;載不起來 / 橋缺席 / 載到別本 / 執行緒預算沒套上 = RED",
        acc["state"] == "GREEN" and pin is not None and acc["body"] == pin.name and isinstance(acc["threads"], int)
        and acc["threads"] > 0 and os.environ.get("VIA_ACCEL_ACTIVE_THREADS") == str(acc["threads"])
        and accelerator(mod=fake_off, act=act)["state"] == "RED" and "沒載起來" in accelerator(mod=fake_off, act=act)["why"]
        and accelerator(mod=None)["state"] == "RED" and other["state"] == "RED" and "鎖冊是" in other["why"]
        and all(u["state"] == "RED" and "執行緒預算沒套上" in u["why"] for u in unapplied),
        f"{acc['body']} · 執行緒 {acc['threads']}({acc['mode']})")

    tools = tools_card(act=act)
    fams = {r.get("family"): r for r in tools["rows"]}
    drift = SimpleNamespace(status=lambda: {"lock": "L", "tools": [dict(r, sha_ok=(False if r.get("family") == "layout"
                                                                                  else r.get("sha_ok")))
                                                                   for r in tools["rows"]]})
    bad = tools_card(act=drift, net=None, ps_template=Path("/nonexistent-via-dir") / PS_TEMPLATE.name)
    elsewhere = SimpleNamespace(__file__="/x/SUP_MDL740_NetUnified_v0999.py", VIA_AEGIS_PATH="/x/VeritasAegisNexus_v" + "0001.py",
                                _aegis=lambda: object(), gate_state=lambda: {"open": False})
    off = tools_card(act=act, net=elsewhere)
    chk("⑦ 工具卡:六件都在鎖冊且 sha ✓ · 網路載入器解析到鎖冊那一支、核心載得起來 · PS 模板在;"
        "layout sha 不對 / 網路載入器缺 / 解析到別支 / PS 模板缺 → RED 並點名",
        tools["state"] == "GREEN" and set(MUST) <= set(fams) and len(fams) >= 6 and tools["net"]["core"]
        and tools["net"]["resolved"] == fams["network"]["pinned"] and tools["ps"]["present"]
        and bad["state"] == "RED" and any(p.startswith("layout") for p in bad["problems"])
        and any("網路載入器不在" in p for p in bad["problems"]) and any("PS 模板" in p for p in bad["problems"])
        and off["state"] == "RED" and any("解析到" in p for p in off["problems"]),
        " · ".join(f"{k} {v.get('version')}" for k, v in fams.items()))
    lay_pin = fams["layout"]["pinned"]
    good_net = SimpleNamespace(__file__="/x/SUP_MDL740_NetUnified_v0999.py", VIA_AEGIS_PATH="/x/" + fams["network"]["pinned"],
                               _aegis=lambda: object(), gate_state=lambda: {"open": False})
    with tempfile.TemporaryDirectory() as ld:          # layout 夾只有鎖冊那一支 = 綠;多一支比鎖冊新(還沒啟用)= 動詞會走新的 → 紅
        (Path(ld) / lay_pin).write_text("", encoding="utf-8")
        same_lay = tools_card(act=act, net=good_net, layout_dir=Path(ld))
        (Path(ld) / f"{lay_pin.rsplit('_v', 1)[0]}_v{_vnum(Path(lay_pin)) + 1:04d}.py").write_text("", encoding="utf-8")
        ahead_lay = tools_card(act=act, net=good_net, layout_dir=Path(ld))
    chk("⑦b layout 動詞走的 = 鎖冊那一支才綠;夾內有比鎖冊新、還沒啟用的一支 → RED 點名(同 v0146 的夾與 glob)",
        same_lay["state"] == "GREEN" and ahead_lay["state"] == "RED"
        and any(p.startswith("layout 動詞走") for p in ahead_lay["problems"])
        and LAYOUT_DIR == PRIOR.LAYOUT_HUB and LAYOUT_PATTERN == PRIOR.LAYOUT_PATTERN, ahead_lay["layout"].get("verb_uses"))

    same = {"state": "OK", "why": "已是最新", "moved": False, "repo": "r", "branch": "main", "upstream": "origin/main",
            "head": "h", "head_after": "h", "ahead": 0, "behind": 0, "dirty": 0}

    def gate_event():                               # 假閘也像真閘一樣留一筆 status 事件(同一輪號)
        PRIOR.write_event({"ts": "t", "verb": "status", "args": [], "rc": 0, "outcome": "OK", "secs": 0.0, "head": "",
                           "error": "", "engine": "selftest", "run": os.environ.get("VIA_HUB_RUN", ""),
                           "t0": round(time.time(), 3), "target": _STEM, "act": "status"}, Path(ev_dir))
        return 0

    def flow(args, **over):
        calls = []
        dep = {"token": lambda: {"lamp": "GREEN", "missing": [], "line": "", "hint": ""},
               "position": lambda r: {"cwd": "/x", "in_repo": True, "cd": ""},
               "update": lambda r, p: dict(same), "gate": gate_event, "accel": lambda: dict(acc), "tools": lambda: tools,
               "go": lambda a: 0, "restart": lambda a: 7}
        dep.update(over)

        def rec(name, fn):                          # 每一步都記下來(被覆寫的也記),次序才量得到
            def w(*a):
                calls.append((name, *[list(x) if isinstance(x, list) else x for x in a]))
                return fn(*a)
            return w
        steps = ("token", "update", "gate", "accel", "tools", "go", "restart")
        dep = {k: rec(k, v) if k in steps else v for k, v in dep.items()}
        rc = enter(args, repo=Path("/nonexistent-repo"), events=Path(ev_dir), **dep)
        return rc, [c for c in calls if c[0] != "token"]

    with tempfile.TemporaryDirectory() as ev_dir:
        keep_run = os.environ.pop("VIA_HUB_RUN", None)
        rc_all, c_all = flow(["-Full", "--no-pull", "-NoOpen"])
        rc_def, c_def = flow([])
        rc_card, c_card = flow(["--card"])
        rc_gate, c_gate = flow([], gate=lambda: 2)
        rc_tok, c_tok = flow([], token=lambda: {"lamp": "RED", "missing": ["read"], "line": "", "hint": "x"})
        rc_tool, c_tool = flow([], tools=lambda: dict(bad))
        moved = dict(same, why="快轉", moved=True, head="a", head_after="b", behind=2)
        rc_mv, c_mv = flow(["-Full"], update=lambda r, p: moved)
        run_after = os.environ.get("VIA_HUB_RUN")
        if keep_run is not None:
            os.environ["VIA_HUB_RUN"] = keep_run
        rows = [json.loads(ln) for f in Path(ev_dir).glob("EVENTS_*.jsonl") for ln in f.read_text(encoding="utf-8").splitlines()]
        evs = [e for e in rows if e["verb"] == "enter"]
        _p, book = PRIOR._flow_book()
        conf = [PRIOR.conformance(book, PRIOR.run_events(e["run"], Path(ev_dir))[1]) for e in evs[:2]]
    with tempfile.TemporaryDirectory() as d2:          # 確定性的排序:閘在 enter 開始 4 秒後才起跑(真實情形),總結照樣排最後
        keep_run = os.environ.get("VIA_HUB_RUN")
        os.environ["VIA_HUB_RUN"] = "enter-selftest-order"
        PRIOR.write_event({"ts": "t", "verb": "status", "args": [], "rc": 0, "outcome": "OK", "secs": 0.0, "head": "", "error": "",
                           "engine": "selftest", "run": "enter-selftest-order", "t0": round(time.time() - 1, 3), "target": _STEM,
                           "act": "status"}, Path(d2))
        record(0, time.time() - 5, [], {}, Path(d2))
        os.environ.pop("VIA_HUB_RUN", None)
        if keep_run is not None:
            os.environ["VIA_HUB_RUN"] = keep_run
        ordered = PRIOR.run_events("enter-selftest-order", Path(d2))[1]
        conf.append(PRIOR.conformance(book, ordered))
    order = [c[0] for c in c_all]
    chk("⑧ 次序:更新 → 閘 → 加速器 → 工具 → go;go 收到的是去掉本動詞旗標的參數;--no-pull 傳到更新",
        rc_all == 0 and order == ["update", "gate", "accel", "tools", "go"] and c_all[-1] == ("go", ["-Full", "-NoOpen"])
        and c_all[0][-1] is False and rc_def == 0 and c_def[0][-1] is True and c_def[-1] == ("go", []), " → ".join(order))
    chk("⑨ --card 不啟動;閘沒過 / 工具漂移 → 後面一步都不跑;第一步紅 → 連更新都不做",
        rc_card == 0 and "go" not in [c[0] for c in c_card] and rc_gate == 2 and [c[0] for c in c_gate] == ["update", "gate"]
        and rc_tool == 2 and "go" not in [c[0] for c in c_tool] and rc_tok == 2 and c_tok == [])
    chk("⑩ HEAD 快轉後交給新碼接手(帶原參數;本行程不再跑閘 / go),回它的 rc",
        rc_mv == 7 and [c[0] for c in c_mv] == ["update", "restart"] and c_mv[-1] == ("restart", ["-Full"]))
    calls = []
    rr = restart(["-Full", "--no-pull"], runner=lambda cmd, cwd=None, env=None: calls.append((cmd, env)) or SimpleNamespace(returncode=3))
    chk("⑪ 接手的子行程:最新 VCGC 尾版 enter --no-pull(旗標不重複)· 帶 VIA_FROM_VCGC=YES",
        rr == 3 and calls and calls[0][0][1] == str(_newest(HERE, _STEM + "_v*.py")) and calls[0][0][2:] == ["enter", "--no-pull", "-Full"]
        and calls[0][1].get("VIA_FROM_VCGC") == "YES")
    chk("⑫ 每次 enter 留一筆中樞事件(verb enter · rc · 卡);本輪輪號自己給、結束還原",
        len(evs) == 7 and all(e["verb"] == "enter" for e in evs) and [e["rc"] for e in evs] == [0, 0, 0, 2, 2, 2, 7]
        and all(e["run"].startswith("enter-") for e in evs) and run_after is None and evs[-1]["card"].get("restarted") is True)
    chk("⑮ 總結事件排在本輪最後:工作流 SSOT 核對本輪第一筆仍是 H1 閘(status)· 開始時間另記 started",
        len(conf) == 3 and all(not any("第一筆" in x for x in c["red"]) and next(iter(c["seen"]), "") == "H1" for c in conf)
        and [e["verb"] for e in ordered] == ["status", "enter"] and all(e["started"] <= e["t0"] for e in evs),
        " | ".join(" → ".join(c["seen"]) for c in conf))
    b = Path(__file__).read_text(encoding="utf-8")
    body = b.split("\ndef selftest", 1)[0]          # 自測自己會對暫存的 bare 倉 push;要查的是動詞本身
    chk("⑬ 抬頭 raw · 帶加速器橋 · 網路橋 · VIA_FROM_VCGC 標記;不寫死任何工具本體檔名(照鎖冊 / 尾版解析)",
        b.split("\n", 3)[2].startswith('r"""') and "[VIA:ACCEL-BRIDGE" in b and "[VIA:NET-BRIDGE" in b and "VIA_FROM_VCGC" in b
        and not re.search(r"(VeritasCeleritas|VeritasAegisNexus|SUP_MDL743_GenericLayoutHub)_v\d{4}\.py", b))
    chk("⑭ 不含 TA-Lib 匯入;動詞本身不 push、不設同意閘",
        not re.search(r"^\s*(?:import|from)\s+" + "ta" + r"lib\b", b, re.M)
        and not re.search(r"""["']push["']""", body) and not re.search(r"environ\[[\"']VIA_(?:NET|SCRAPE)_CONSENT", body))
    if not all(ok):
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    a = sys.argv[1:]
    raise SystemExit(selftest() if a == ["--selftest"] else main())
