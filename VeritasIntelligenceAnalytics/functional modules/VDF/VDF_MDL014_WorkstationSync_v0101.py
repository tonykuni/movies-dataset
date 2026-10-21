#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL014_WorkstationSync v0101 — 薄尾:從 VDF 自己的 MAIN 工作樹裡也能一鍵同步(認得原 checkout)· VDF 資料接過去

操作員令(2026-10-20):「用 MDL014 把工作站同步到 main」。v0100 的兩個缺口(工作站實況):
  ① 工作站的 checkout 是分岔(沒合 main),v0100 這支檔只在 main 上 → 只能從「VDF 工作樹(固定在 origin/main)」裡跑;
     但 v0100 把「本檔所在的倉」當原 checkout:在工作樹裡跑 → 量不到原 checkout 的分岔、不備份,還會再建一個 <工作樹>-vdf-main。
  ② VDF 的資料不在 git(output_hub 的 DuckDB · VIA_Reports/vdf_fetch 擷取家都被 .gitignore 擋)→ 工作樹裡的 VDF 是空的。
本版(其餘全照 v0100:預演 / --apply · 備份分岔到新分支 · 交接真的重跑 · 只交 VDF 收據 · 從不 force · 從不推 main):
  ① 原 checkout = `git worktree list` 的第一個(主工作樹);本檔若就在 VDF 工作樹裡 → 就用這個工作樹,不另建。--repo 可明指。
  ② --apply 時把 VDF 的兩個資料夾從工作樹接到原 checkout 的實體夾(Windows 目錄接點 junction,免系統管理員;他處用符號連結):
     工作樹裡已有實體夾 → 不動、照報;原 checkout 沒有 → 不接、照報;已接到同一處 → 照舊。--no-link-data 可關。
     兩邊共用同一份資料:同一時間只從一邊跑 VDF。
用法(工作站 PowerShell;第一次先建工作樹,之後只要更新它):
  cd <倉根>; git fetch origin
  $wt = "$env:LOCALAPPDATA\\VIA\\<倉名>-vdf-main"
  if (Test-Path $wt) { git -C $wt checkout --detach origin/main } else { git worktree add --detach $wt origin/main }
  python "$wt\\VeritasIntelligenceAnalytics\\functional modules\\VDF\\VDF_MDL014_WorkstationSync_v0101.py" --case <案> …          預演
  python "$wt\\VeritasIntelligenceAnalytics\\functional modules\\VDF\\VDF_MDL014_WorkstationSync_v0101.py" --case <案> … --apply  執行
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境變數;git 走本機憑證。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
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

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====



import argparse
import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent                     # …/functional modules/VDF
_STEM = "VDF_MDL014_WorkstationSync"
TAG = "VDF_MDL014_WorkstationSync v0101"
DATA_LINKS_V0101 = ("functional modules/VDF/output_hub", "VIA_Reports/vdf_fetch")   # VDF 不在 git 的資料(兩處都被 .gitignore 擋)


def _vnum_v0101(p) -> int:
    import re
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0101(p) < _vnum_v0101(__file__)), key=_vnum_v0101)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
git = PRIOR.git


def __getattr__(name):
    return getattr(PRIOR, name)


def main_checkout(start: Path) -> Path:
    """原 checkout = 主工作樹(`git worktree list --porcelain` 的第一個 worktree)。從連結的工作樹裡問也一樣。"""
    for ln in git(["worktree", "list", "--porcelain"], start).splitlines():
        if ln.startswith("worktree "):
            return Path(ln[len("worktree "):].strip())
    return Path(git(["rev-parse", "--show-toplevel"], start))


def _same(a: Path, b: Path) -> bool:
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def resolve_roots(here: Path, repo: str | None = None, worktree: str | None = None) -> tuple:
    """→ (原 checkout, VDF 工作樹, 怎麼定的)。本檔在別的工作樹裡跑:只有那正是 VDF 的預設位置(%LOCALAPPDATA%\\VIA\\<倉名>-vdf-main)
    才沿用;其他工作樹(他系統的功能分支等)一律不接手 —— 要用就 --worktree 明指(Codex #549 P1;四系統對等獨立 L123)。"""
    top = Path(git(["rev-parse", "--show-toplevel"], here)).resolve()
    root = Path(repo).resolve() if repo else main_checkout(top).resolve()
    if worktree:
        return root, Path(worktree).resolve(), "--worktree 指定"
    default = PRIOR.default_worktree(root)
    if not _same(top, root) and not _same(top, default):
        raise RuntimeError("本檔所在的工作樹 %s 不是 VDF 的工作樹(預設 %s)—— 不接手別人的工作樹;"
                           "要用它就加 --worktree \"%s\"" % (top, default, top))
    return root, default, ("本檔就在 VDF 工作樹裡" if _same(top, default) else "預設位置")


def _next_cmd(a) -> str:
    """預演印的 NEXT:照這次給的全部參數重組(--case · --repo · --worktree · --remote · --no-link-data),只多一個 --apply(Codex #549 P2)。"""
    q = lambda x: '"%s"' % x if (" " in str(x) or not str(x)) else str(x)
    parts = ["python", q(Path(__file__).name)]
    for c in a.case or []:
        parts += ["--case", q(c)]
    for flag, val in (("--repo", a.repo), ("--worktree", a.worktree)):
        if val:
            parts += [flag, q(val)]
    if a.remote != "origin":
        parts += ["--remote", q(a.remote)]
    if a.no_link_data:
        parts.append("--no-link-data")
    return " ".join(parts + ["--apply"])


def make_link(dst: Path, src: Path, apply: bool, nt: bool | None = None) -> str:
    """dst(工作樹裡)接到 src(原 checkout 的實體夾)。只在 dst 不存在時動手;回一句照實的狀態。"""
    nt = (os.name == "nt") if nt is None else nt
    if os.path.lexists(dst):
        same = src.exists() and os.path.realpath(dst) == os.path.realpath(src)
        return "已接(照舊)" if same else "工作樹裡已有自己的資料夾,不動(要共用請先移走它)"
    if not src.exists():
        return "原 checkout 沒有這個夾,不接"
    if not apply:
        return "會接上 → %s" % src
    dst.parent.mkdir(parents=True, exist_ok=True)
    target = os.path.realpath(src)
    if nt:
        try:
            import _winapi
            _winapi.CreateJunction(target, str(dst))
        except (ImportError, OSError) as exc:
            p = subprocess.run(["cmd", "/c", "mklink", "/J", str(dst), target], capture_output=True, text=True)
            if p.returncode != 0:
                return "接不上(%s;%s)→ 手動:mklink /J \"%s\" \"%s\"" % (type(exc).__name__, (p.stdout + p.stderr).strip()[:120], dst, target)
        return "已接上(目錄接點)→ %s" % target
    os.symlink(target, dst, target_is_directory=True)
    return "已接上(符號連結)→ %s" % target


def _not_link_lines(lines: list) -> list:
    """git status 的行去掉本版接的資料夾:.gitignore 的 output_hub/ 帶斜線只擋實體夾,接點 / 連結會被當成未追蹤 → 不算工作樹髒。"""
    mine = {(PRIOR.VIA_DIR + "/" + rel).rstrip("/") for rel in DATA_LINKS_V0101}
    return [ln for ln in lines if ln[3:].strip().strip('"').rstrip("/") not in mine]


def survey(root: Path, remote: str, wt: Path, fetch: bool = True) -> dict:
    s = PRIOR.survey(root, remote, wt, fetch)
    s["wt_dirty"] = _not_link_lines(s["wt_dirty"])
    return s


def link_data(root: Path, wt: Path, apply: bool, nt: bool | None = None) -> list:
    via_r, via_w = root / PRIOR.VIA_DIR, wt / PRIOR.VIA_DIR
    return [(rel, make_link(via_w / rel, via_r / rel, apply, nt)) for rel in DATA_LINKS_V0101]


def run(argv=None, here: Path = HERE) -> int:
    ap = argparse.ArgumentParser(prog=Path(__file__).name, description=TAG)
    ap.add_argument("--apply", action="store_true", help="真的執行(預設只預演)")
    ap.add_argument("--case", action="append", help="要重跑的交接案(可多次;預設 qg_onebridge)")
    ap.add_argument("--repo", help="原 checkout(預設:git worktree list 的主工作樹)")
    ap.add_argument("--worktree", help="VDF 工作樹位置(預設:本檔所在的工作樹;本檔在原 checkout 時用 %%LOCALAPPDATA%%\\VIA\\<倉名>-vdf-main)")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--no-link-data", action="store_true", help="不把 VDF 資料夾接到原 checkout")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    try:
        root, wt, how = resolve_roots(here, a.repo, a.worktree)
    except RuntimeError as exc:
        print("=== %s · 停 ===\n  [VDF MAIN] %s" % (TAG, exc))
        return 2
    cases = a.case or list(PRIOR.DEFAULT_CASES)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    print("=== %s · %s ===" % (TAG, "執行" if a.apply else "預演(加 --apply 才動手)"))
    s = survey(root, a.remote, wt)
    print("  [倉] 原 checkout %s · HEAD %s · 落後 %s %d 提交 · 本機獨有 %d 提交" % (root, s["head"][:9], s["up"], s["behind"], s["ahead"]))
    if s["main_dirty"]:
        print("  [倉] 原 checkout 有 %d 個未提交改動 —— 本工具不碰它們(他系統的工作照留)" % len(s["main_dirty"]))
    print("  [備份] %s" % ("需要:推到新分支 %s%s(不動 main、不 force)" % (PRIOR.BACKUP_PREFIX, stamp) if s["backup_needed"]
                          else ("不需要:已在 %s" % ", ".join(s["holders"][:3]) if s["ahead"] else "不需要:沒有本機獨有提交")))
    print("  [VDF MAIN] %s(%s)· %s" % (wt, how, ("已在" + (" · 有未提交改動 %d" % len(s["wt_dirty"]) if s["wt_dirty"] else " · 乾淨"))
                                     if s["wt_exists"] else "還沒建"))
    if not a.no_link_data:
        for rel, st in link_data(root, wt, False):
            print("  [資料] %s:%s" % (rel, st))
    print("  [交接案] %s(先移開舊收據 → 真的重跑;只收 VDF 的收據)" % ", ".join(cases))
    if not a.apply:
        print("NEXT: " + _next_cmd(a))
        return 0
    held = PRIOR.backup(root, a.remote, s, stamp)
    if held:
        print("  [備份] 本機獨有提交在 %s" % held)
    print("  [VDF MAIN] %s → %s" % (PRIOR.ensure_worktree(root, s), git(["rev-parse", "--short", "HEAD"], wt)))
    links = [] if a.no_link_data else link_data(root, wt, True)
    for rel, st in links:
        print("  [資料] %s:%s" % (rel, st))
    ran = PRIOR.run_cases(wt, cases)
    for r in ran:
        print("  [交接] %s rc %s · 標記 %s%s" % (r["case"], r["rc"], r["marker"], " · 沿用(不該發生)" if r["reused"] else ""))
    picked = PRIOR.stage_vdf_receipts(wt, ran)
    br = PRIOR.publish(wt, a.remote, picked, ran, stamp)
    ok = all(r["rc"] == 0 and r["marker"] and not r["reused"] for r in ran)
    web = PRIOR.remote_web(root, a.remote)
    if br:
        print("  [收據] %d 檔 → 分支 %s" % (len(picked), br))
        print("NEXT: 開 PR %s/pull/new/%s(或把這行貼給 AI)" % (web, br))
    else:
        print("  [收據] 沒有新的 VDF 收據要交")
    bad_links = [rel for rel, st in links if st.startswith("接不上")]
    print("[計] %s · 交接 %s · 資料 %s · %s" % (TAG, "全綠" if ok else "有紅", "接不上 %s" % bad_links if bad_links else "OK",
                                          "PASS" if ok and not bad_links else "FAIL"))
    return 0 if ok and not bad_links else 1


def main(argv=None) -> int:
    return run(argv)


def selftest() -> int:
    """離線:假遠端 + 分岔的原 checkout + 先手動建好的 VDF 工作樹;從工作樹裡跑整條流程(本版的兩個缺口)。前版鏈自測照跑。"""
    import contextlib
    import io
    import re
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s · 薄尾自測(離線假倉;不連網 · 不碰真倉)===" % TAG)
    td = Path(tempfile.mkdtemp(prefix="vdf_mdl014b_"))
    keep = {k: os.environ.get(k) for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "LOCALAPPDATA")}
    os.environ.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x")
    os.environ.pop("LOCALAPPDATA", None)
    VIA, EV = PRIOR.VIA_DIR, PRIOR.EVID
    try:
        remote = td / "remote.git"
        git(["init", "--bare", "-b", "main", str(remote)], td)
        seed = td / "seed"
        git(["clone", str(remote), str(seed)], td)
        via = seed / VIA
        (via / EV).mkdir(parents=True)
        (via / EV / ".keep").write_text("", encoding="utf-8")       # 空夾 git 不收
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (reg / "VIA_VCGC_SubsystemSeat_v0100.json").write_text("{}\n", encoding="utf-8")
        (via / PRIOR.SSOT).write_text(json.dumps({"test_cases": {
            "vdf_case": {"argv": ["VDF_X", "--selftest"], "dependencies": ["functional modules/VDF/VDF_X_v*.py"]}}}), encoding="utf-8")
        (reg / "CGC_MDL149_VeritasCentralGovernanceConsole_v0001.py").write_text(
            "import json, sys, pathlib\n"
            "case = sys.argv[3]\n"
            "ev = pathlib.Path('docs/handoff/evidence')\n"
            "db = pathlib.Path('functional modules/VDF/output_hub/probe.txt')\n"
            "seen = db.read_text() if db.exists() else 'none'\n"
            "(ev / (case + '.json')).write_text(json.dumps({'case': case, 'rc': 0, 'seen': seen}))\n"
            "print(json.dumps({'case': case, 'rc': 0, 'marker': True, 'reused': False}))\n", encoding="utf-8")
        (via / "functional modules" / "VDF").mkdir(parents=True)
        (via / "functional modules" / "VDF" / "VDF_X_v0001.py").write_text("# VDF 本體(真倉裡這一夾有追蹤的檔)\n", encoding="utf-8")
        (seed / ".gitignore").write_text(VIA + "/functional modules/VDF/output_hub/\n" + VIA + "/VIA_Reports/*\n", encoding="utf-8")
        git(["add", "-A"], seed)
        git(["commit", "-m", "seed"], seed)
        git(["push", "origin", "main"], seed)
        work = td / "movies-dataset"                       # 原 checkout:分岔(本機獨有 1)· 有他系統未提交檔 · 有 VDF 實體資料
        git(["clone", str(remote), str(work)], td)
        (work / "ws_only.txt").write_text("VRN-2 本機獨有\n", encoding="utf-8")
        git(["add", "-A"], work)
        git(["commit", "-m", "ws local"], work)
        (work / "uncommitted.txt").write_text("他系統未提交\n", encoding="utf-8")
        hub = work / VIA / "functional modules" / "VDF" / "output_hub"
        hub.mkdir(parents=True)
        (hub / "probe.txt").write_text("真資料", encoding="utf-8")
        (work / VIA / "VIA_Reports" / "vdf_fetch").mkdir(parents=True)
        (seed / "upstream.txt").write_text("main 前進\n", encoding="utf-8")
        git(["add", "-A"], seed)
        git(["commit", "-m", "upstream"], seed)
        git(["push", "origin", "main"], seed)
        git(["fetch", "origin"], work)
        os.environ["LOCALAPPDATA"] = str(td / "LocalAppData")
        wt = td / "LocalAppData" / "VIA" / "movies-dataset-vdf-main"            # VDF 的預設位置(工作站用法:先手動建在這裡)
        git(["worktree", "add", "--detach", str(wt), "origin/main~1"], work)     # 舊的 main(使用說明:先手動建)
        here_wt = wt / VIA / "functional modules" / "VDF"
        head0 = git(["rev-parse", "HEAD"], work)

        r_wt = resolve_roots(here_wt)
        r_root = resolve_roots(work)
        r_rep = resolve_roots(here_wt, repo=str(work), worktree=str(td / "elsewhere"))
        chk("v0101-① 認原 checkout:在 VDF 工作樹裡跑 → 原 checkout = 主工作樹、工作樹 = 本身(不另建 *-vdf-main-vdf-main);"
            "在原 checkout 跑 → 照 v0100 預設位置;--repo / --worktree 明指照用",
            r_wt[0] == work.resolve() and _same(r_wt[1], wt) and r_root[0] == work.resolve()
            and r_root[1] == PRIOR.default_worktree(work.resolve()) and r_rep[1] == (td / "elsewhere").resolve(), (r_wt, r_root[1]))
        other = td / "vrn-feature"                                         # 他系統的另一個工作樹(乾淨)
        git(["worktree", "add", "-b", "vrn-feature", str(other), "origin/main"], work)
        here_other = other / VIA / "functional modules" / "VDF"
        head_other = git(["rev-parse", "HEAD"], other)
        PRIOR.GIT_LOG.clear()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc_other = run(["--case", "vdf_case", "--apply"], here=here_other)
        r_explicit = resolve_roots(here_other, worktree=str(other))
        chk("v0101-①b 不接手別的工作樹:從他系統的工作樹跑 --apply → rc 2 · 停在動手前(沒 fetch / 沒推 / 沒切 / 沒接資料)· 分支照舊;--worktree 明指才用它",
            rc_other == 2 and "不接手" in out.getvalue()
            and not [c for c in PRIOR.GIT_LOG if c and c[0] in ("fetch", "push", "checkout", "switch", "commit", "add", "worktree") and c[:2] != ["worktree", "list"]] and git(["rev-parse", "HEAD"], other) == head_other
            and git(["rev-parse", "--abbrev-ref", "HEAD"], other) == "vrn-feature" and not os.path.lexists(other / VIA / DATA_LINKS_V0101[0])
            and _same(r_explicit[1], other), (rc_other, out.getvalue()[-200:], PRIOR.GIT_LOG[:3]))
        git(["worktree", "remove", "--force", str(other)], work)

        PRIOR.GIT_LOG.clear()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc_pre = run(["--case", "vdf_case"], here=here_wt)
        pre = out.getvalue()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            run(["--case", "vdf_case", "--case", "x y", "--remote", "origin", "--no-link-data", "--repo", str(work)], here=here_wt)
        nxt = [ln for ln in out.getvalue().splitlines() if ln.startswith("NEXT: ")]
        chk("v0101-②b 預演的 NEXT 照這次全部參數重組(--case 含空白加引號 · --repo · --no-link-data)只多 --apply;--no-link-data 時不報資料夾",
            len(nxt) == 1 and nxt[0].endswith(" --apply") and "--case vdf_case --case \"x y\"" in nxt[0] and "--no-link-data" in nxt[0]
            and ("--repo \"%s\"" % work if " " in str(work) else "--repo %s" % work) in nxt[0] and "[資料]" not in out.getvalue(), nxt)
        chk("v0101-② 預演零動作:量得到原 checkout 分岔(落後 1 · 獨有 1 · 要備份)· 資料夾只報「會接上」· 沒推分支 · 沒接資料",
            rc_pre == 0 and "本機獨有 1 提交" in pre and "需要:推到新分支" in pre and "會接上" in pre
            and not [c for c in PRIOR.GIT_LOG if c and c[0] == "push"] and not os.path.lexists(wt / VIA / DATA_LINKS_V0101[0]), pre[-300:])

        PRIOR.GIT_LOG.clear()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc_ap = run(["--case", "vdf_case", "--apply"], here=here_wt)
        txt = out.getvalue()
        wts = [ln for ln in git(["worktree", "list", "--porcelain"], work).splitlines() if ln.startswith("worktree ")]
        ev = json.loads((wt / VIA / EV / "vdf_case.json").read_text(encoding="utf-8"))
        backups = [b for b in git(["for-each-ref", "--format=%(refname:short)", "refs/heads"], remote).splitlines() if b.startswith(PRIOR.BACKUP_PREFIX)]
        chk("v0101-③ 執行:備份的是原 checkout 的獨有提交 · 工作樹還是同一個(只 2 個 worktree)且移到最新 main",
            rc_ap == 0 and backups and git(["rev-parse", "refs/heads/" + backups[0]], remote) == head0 and len(wts) == 2
            and subprocess.run(["git", "merge-base", "--is-ancestor", git(["rev-parse", "refs/heads/main"], remote), "HEAD"], cwd=str(wt)).returncode == 0
            and (wt / "upstream.txt").exists(), (rc_ap, backups, wts, txt[-400:]))
        chk("v0101-④ VDF 資料接過去:工作樹的 output_hub · VIA_Reports/vdf_fetch 指到原 checkout 的實體夾;交接案在工作樹裡讀得到真資料",
            all(os.path.realpath(wt / VIA / rel) == os.path.realpath(work / VIA / rel) for rel in DATA_LINKS_V0101)
            and ev.get("seen") == "真資料", (ev, [os.path.realpath(wt / VIA / r) for r in DATA_LINKS_V0101]))
        chk("v0101-⑤ 接點不算工作樹髒(git 把 output_hub 接點當未追蹤;本版濾掉、v0100 的量法會算)· 收據分支推上去 · 原 checkout 一點沒動 · 從不 force · 從不推 main",
            not survey(work, "origin", wt)["wt_dirty"] and PRIOR.survey(work, "origin", wt)["wt_dirty"] and "[收據] " in txt and git(["rev-parse", "HEAD"], work) == head0
            and (work / "uncommitted.txt").exists() and (hub / "probe.txt").read_text(encoding="utf-8") == "真資料"
            and not any(("--force" in c or "-f" in c or any(str(x).endswith(":refs/heads/main") or x == "main" for x in c[1:]))
                        for c in PRIOR.GIT_LOG if c and c[0] == "push"), txt[-300:])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc_again = run(["--case", "vdf_case", "--apply"], here=here_wt)
        chk("v0101-⑥ 再跑一次:接點照舊(不重接)· 已有遠端分支收著不重備份 · rc 0", rc_again == 0 and "已接(照舊)" in out.getvalue()
            and "不需要:已在" in out.getvalue(), out.getvalue()[-300:])

        lone = td / "lone"
        (lone / "src").mkdir(parents=True)
        (lone / "dst_real").mkdir()
        st_real = make_link(lone / "dst_real", lone / "src", True)
        st_nosrc = make_link(lone / "dst_x", lone / "nosrc", True)
        calls = []

        class _FakeWinapi:
            @staticmethod
            def CreateJunction(src, dst):
                calls.append((src, dst))
                os.symlink(src, dst, target_is_directory=True)

        sys.modules["_winapi"], keep_w = _FakeWinapi, sys.modules.get("_winapi")
        try:
            st_nt = make_link(lone / "dst_nt", lone / "src", True, nt=True)
        finally:
            if keep_w is None:
                sys.modules.pop("_winapi", None)
            else:
                sys.modules["_winapi"] = keep_w
        chk("v0101-⑦ 接點邊界:工作樹已有實體夾 → 不動 · 原 checkout 沒有 → 不接 · Windows 走 CreateJunction(目錄接點,免管理員)",
            "不動" in st_real and (lone / "dst_real").is_dir() and not os.path.islink(lone / "dst_real")
            and "不接" in st_nosrc and not os.path.lexists(lone / "dst_x")
            and "目錄接點" in st_nt and calls == [(os.path.realpath(lone / "src"), str(lone / "dst_nt"))], (st_real, st_nosrc, st_nt, calls))
        src = Path(__file__).read_text(encoding="utf-8")
        imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
        chk("v0101-⑧ 三橋在 · 不匯入他系統程式 · 不碰 TA-Lib · 同意閘不寫 · 不寫環境變數(只讀 LOCALAPPDATA)",
            all(t in src for t in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]", "[VIA:LIB-BRIDGE:v0100]"))
            and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VRN2_", "VCGC"))]
            and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
            and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src)
            and not re.search(r"\b" + "setx" + r"\b|os\.environ\[[^\]]+\]\s*=(?!=)|os\.environ\.update\(|" + "putenv", src.split("def " + "selftest")[0]))
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    print("  ── 前版鏈自測(VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("v0101-⑨ 前版 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("  [計] %s 薄尾 %d/%d · %s" % (TAG, p, p + f, "PASS" if not f else "FAIL"))
    return 0 if not f else 1


if __name__ == "__main__":
    raise SystemExit(main())
