#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0209 — 薄尾(v0208 以前一字不動):hostrun 的「更新倉 · 換新版重跑 · 摘要進剪貼簿」搬進 Python(PR #777 Codex P1)

Invoke-VDF-HostRun-v0100 / v0101.ps1 把更新倉的判斷(fetch 失敗怎麼辦 · 有沒有未提交改動 · 切哪條分支)、挑管理器、
  處理摘要檔都寫在 PowerShell —— 違反 AGENTS.md / CLAUDE.md L117「PS 只進環境、叫一個 python 動詞;判斷與流程寫在 Python」。
本版 hostrun 自己做完整條:
  hostrun [--branch 分支] [--no-update] [--no-clip] [--full] [--only …]
    ① 更新倉:fetch origin/<分支>;本機有未提交的改動(可能是另一個工作階段在用)→ 不切,照現在的版本跑並照實記;
       乾淨 → switch -C via-hostrun origin/<分支>
    ② 更新後家族尾版若比本檔新 → 用新尾版重跑 hostrun --no-update(新程式才生效);否則本檔直接跑 v0208 的 hostrun
    ③ 摘要(這一輪寫的 HOSTRUN_latest.txt)前面補上「更新」那幾行,複製到剪貼簿(Windows 用 clip.exe · UTF-16LE BOM;
       其他系統照實說沒複製)
  PS(Invoke-VDF-HostRun-v0102.ps1)只剩:找管理器尾版、把參數原樣交給 hostrun。
其餘照 v0208。零網路(git fetch 除外,走 git 自己的設定)· 不碰 TA-Lib · 不設同意閘 · 不 import VCGC。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

VERSION = "v0209"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent
DEFAULT_BRANCH = "claude/sweet-hamilton-gei01h"
LOCAL_BRANCH = "via-hostrun"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0208
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


V208 = PRIOR
V194 = V208.V194


def _git(repo: Path, *args, timeout: int = 300):
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(args, 1, "", f"{type(exc).__name__}: {exc}")


def repo_root(start: Path) -> Path | None:
    r = _git(start, "rev-parse", "--show-toplevel", timeout=30)
    return Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None


def update(repo: Path, branch: str) -> list:
    """fetch → 有未提交改動就不切 → 乾淨就切到 origin/<branch>。回要記進摘要的幾行(照實)。"""
    notes = []
    f = _git(repo, "fetch", "-q", "origin", branch)
    if f.returncode != 0:
        return [f"[hostrun] 更新:抓不到 origin/{branch}(rc {f.returncode})→ 照現在的版本跑 · {(f.stderr or '').strip()[:160]}"]
    d = _git(repo, "-c", "core.quotepath=off", "status", "--porcelain", "--untracked-files=no")
    dirty = [ln for ln in (d.stdout or "").splitlines() if ln.strip()]
    if dirty:
        notes.append(f"[hostrun] 更新:本機有 {len(dirty)} 個未提交的改動(可能是另一個工作階段在用)→ 不切分支、照現在的版本跑")
        notes += [f"[hostrun]   {ln}" for ln in dirty[:10]]
        return notes
    s = _git(repo, "switch", "-q", "-C", LOCAL_BRANCH, f"origin/{branch}")
    if s.returncode != 0:
        return [f"[hostrun] 更新:切不到 origin/{branch}(rc {s.returncode})→ 照現在的版本跑 · {(s.stderr or '').strip()[:160]}"]
    head = _git(repo, "rev-parse", "--short", "HEAD").stdout.strip()
    return [f"[hostrun] 更新:已切到 origin/{branch} @ {head}(本機分支 {LOCAL_BRANCH})"]


def newest_tail(folder: Path = HERE) -> Path:
    return max(folder.glob(STEM + "_v*.py"), key=_vnum)


def copy_to_clipboard(text: str, runner=None) -> str:
    """Windows:clip.exe 吃 UTF-16LE(開頭 BOM)→ 中文不亂碼。其他系統照實回沒複製。"""
    if runner is None:
        if os.name != "nt" or not shutil.which("clip"):
            return "沒複製(這台不是 Windows 或沒有 clip.exe);摘要在檔案裡"
        runner = lambda data: subprocess.run(["clip"], input=data, timeout=30).returncode  # noqa: E731
    rc = runner(b"\xff\xfe" + text.encode("utf-16-le"))
    return "已複製到剪貼簿" if rc == 0 else f"複製失敗(rc {rc});摘要在檔案裡"


def _pop_opt(a: list, key: str, default=None):
    if key in a:
        i = a.index(key)
        v = a[i + 1] if i + 1 < len(a) else default
        del a[i:i + 2]
        return v
    return default


def cmd_hostrun(args: list) -> int:
    a = list(args)
    branch = _pop_opt(a, "--branch", DEFAULT_BRANCH)
    no_update = "--no-update" in a
    no_clip = "--no-clip" in a
    a = [x for x in a if x not in ("--no-update", "--no-clip")]
    via = V194._p("sm_via_root")()
    out = V194._p("v73_out")(via)
    f = out / "HOSTRUN_latest.txt"
    try:
        f.unlink()
    except OSError:
        pass
    notes = []
    if not no_update:
        repo = repo_root(via)
        notes = update(repo, branch) if repo else ["[hostrun] 更新:這裡不是 git 倉 → 照現在的版本跑"]
        for n in notes:
            print(n, flush=True)
    tail = newest_tail()
    if _vnum(tail) > _vnum(Path(__file__)):
        print(f"[hostrun] 更新後尾版是 {tail.name}(比 {Path(__file__).name} 新)→ 用新尾版重跑", flush=True)
        rc = subprocess.run([sys.executable, str(tail), "hostrun", "--no-update", "--no-clip", *a], stdin=subprocess.DEVNULL).returncode
    else:
        rc = V208.cmd_hostrun(a)
    body = f.read_text(encoding="utf-8") if f.is_file() else ""
    if not body:
        print(f"[hostrun] 這一輪沒有寫出摘要(rc {rc});把上面畫面最後幾行貼給我", flush=True)
        return rc if rc else 1
    text = "\n".join(notes) + ("\n" if notes else "") + body
    f.write_text(text, encoding="utf-8")
    msg = "沒複製(--no-clip)" if no_clip else copy_to_clipboard(text)
    print(f"[hostrun] 摘要{msg}(rc {rc}){',直接貼給我' if msg.startswith('已複製') else ''}", flush=True)
    return rc


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存 git 倉 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    with tempfile.TemporaryDirectory(prefix="vdf_sm209_") as td:
        d = Path(td)
        g = ["-c", "user.name=fx", "-c", "user.email=fx@example.invalid"]
        subprocess.run(["git", "init", "-q", "--bare", str(d / "origin.git")], capture_output=True)
        subprocess.run(["git", "clone", "-q", str(d / "origin.git"), str(d / "repo")], capture_output=True)
        r = d / "repo"
        (r / "a.txt").write_text("1\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(r), *g, "checkout", "-q", "-b", "feat"], capture_output=True)
        subprocess.run(["git", "-C", str(r), "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", str(r), *g, "commit", "-qm", "1"], capture_output=True)
        subprocess.run(["git", "-C", str(r), "push", "-q", "origin", "feat"], capture_output=True)
        (r / "a.txt").write_text("dirty\n", encoding="utf-8")
        n_dirty = update(r, "feat")
        br_dirty = _git(r, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        subprocess.run(["git", "-C", str(r), "checkout", "-q", "--", "a.txt"], capture_output=True)
        n_clean = update(r, "feat")
        br_clean = _git(r, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        n_bad = update(r, "no-such-branch")
    chk("T2 更新倉:有未提交改動 → 不切並列出;乾淨 → 切到 origin/<分支>(本機 via-hostrun);抓不到分支 → 照實說、照現在的跑",
        "不切分支" in n_dirty[0] and br_dirty == "feat" and br_clean == LOCAL_BRANCH and "已切到 origin/feat" in n_clean[0]
        and "抓不到 origin/no-such-branch" in n_bad[0], (n_dirty, n_clean, n_bad))
    got = []
    msg = copy_to_clipboard("摘要 OK", lambda data: (got.append(data), 0)[1])
    chk("T3 剪貼簿:送 UTF-16LE(開頭 BOM)給 clip,中文原樣;非 Windows 照實說沒複製",
        msg == "已複製到剪貼簿" and got and got[0][:2] == b"\xff\xfe" and got[0][2:].decode("utf-16-le") == "摘要 OK"
        and (os.name == "nt" or copy_to_clipboard("x").startswith("沒複製")), (msg, got))
    a = ["--branch", "main", "--full", "--no-update"]
    chk("T4 參數:--branch 取值後拿掉 · 其餘照轉;更新後尾版比本檔新才用新尾版重跑",
        _pop_opt(a, "--branch") == "main" and a == ["--full", "--no-update"] and _vnum(newest_tail()) >= _vnum(Path(__file__)), a)
    rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    chk("T5 前版 v0208 自測照過(含整條前版鏈)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["hostrun"]:
        return cmd_hostrun(a[1:])
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
