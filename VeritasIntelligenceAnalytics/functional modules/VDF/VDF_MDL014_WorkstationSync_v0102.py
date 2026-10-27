#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL014_WorkstationSync v0102 — 薄尾:自己上次沒交完的收據不再擋住同步 · 交完收據回到 main · 停得乾淨(不噴 traceback)

工作站實錄(操作員 2026-10-21 16:03,cmd):`--apply` 在 ensure_worktree 停住 ——
  RuntimeError: VDF 工作樹有未提交的改動,先處理再跑(不覆蓋):['M  …/docs/handoff/evidence/qg_onebridge.json', ' M …/qg_onebridge.txt']
那兩個檔是本工具自己上一次 --apply 跑交接案後寫的收據(stage 了、沒交完),v0100 的 ensure_worktree 把它們當成「別人的改動」拒絕,
而且 v0100 publish 交完收據後留在收據分支上、沒回到 main。本版(其餘全照 v0101 / v0100):
  ① ensure_worktree 前先看工作樹的髒檔:全部都在 docs/handoff/evidence/(本工具自己的收據,重跑會重產)→ 還原 + 清掉未追蹤,
     印「清掉上次沒交完的收據 N 檔」再照常移到最新 main;只要有一個不是收據的檔 → 一個都不動、照舊拒絕(訊息多給 `git status` 指引)。
  ② publish 推完收據分支後 `git checkout --detach origin/main`:工作樹回到 main、乾淨;收據留在分支上(NEXT 照印開 PR)。
  ③ run 裡的 RuntimeError(git 失敗 · 拒絕同步)→ 印一行 `[VDF MAIN] 停:…` 回 rc 2,不噴 traceback。
用法同 v0101(工作站 PowerShell 或 cmd,站在 VDF 工作樹裡):
  python "VeritasIntelligenceAnalytics\\functional modules\\VDF\\VDF_MDL014_WorkstationSync_v0102.py" --apply
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境變數;git 走本機憑證;從不 force、從不推 main。
"""
from __future__ import annotations

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
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent                     # …/functional modules/VDF
_STEM = "VDF_MDL014_WorkstationSync"
TAG = "VDF_MDL014_WorkstationSync v0102"


def _vnum_v0102(p) -> int:
    import re
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0102(p) < _vnum_v0102(__file__)), key=_vnum_v0102)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0100 = PRIOR.PRIOR                                        # 本體(ensure_worktree · publish 都在它身上;v0101 的 run 經 PRIOR.* 呼叫)
git = V0100.git
EVID_REL = V0100.VIA_DIR + "/" + V0100.EVID               # 工作樹裡收據夾的相對路徑(git status 印的樣子)
_LAST = {"up": None}
_ENSURE_V0100, _PUBLISH_V0100, _NEXT_CMD_V0101 = V0100.ensure_worktree, V0100.publish, PRIOR._next_cmd


def __getattr__(name):
    return getattr(PRIOR, name)


def _dirty_now(wt: Path) -> list:
    """同 v0101 的量法(VCGC 兩本冊 · VDF 資料接點不算髒)。"""
    lines = [ln for ln in git(["status", "--porcelain"], wt).splitlines()
             if ln.strip() and not any(ln[3:].strip().strip('"').endswith(b) for b in V0100.VCGC_BOOKS)]
    return PRIOR._not_link_lines(lines)


def split_receipts(dirty: list) -> tuple:
    """髒檔分兩堆:(本工具自己的收據 docs/handoff/evidence/…, 其他)。"""
    mine, others = [], []
    for ln in dirty:
        rel = ln[3:].strip().strip('"')
        (mine if rel.startswith(EVID_REL + "/") else others).append(ln)
    return mine, others


def tidy_receipts(wt: Path, s: dict) -> list:
    """髒檔全是自己的收據 → 還原(已 stage 的退回 · 改動還原 · 未追蹤的清掉)並重量 s['wt_dirty'];有別的檔 → 一個都不動。→ 清掉的行"""
    mine, others = split_receipts(s.get("wt_dirty") or [])
    if not mine or others:
        return []
    git(["reset", "-q", "--", EVID_REL], wt, check=False)
    git(["checkout", "--", EVID_REL], wt, check=False)
    git(["clean", "-fdq", "--", EVID_REL], wt, check=False)
    s["wt_dirty"] = _dirty_now(wt)
    return mine


def ensure_worktree(root: Path, s: dict) -> str:
    """同 v0100,但先清自己的收據殘留;還是髒 → 拒絕(訊息帶指引)。"""
    _LAST["up"] = s.get("up")
    if s.get("wt_exists"):
        cleaned = tidy_receipts(Path(s["wt"]), s)
        if cleaned:
            print("  [VDF MAIN] 清掉上次沒交完的收據 %d 檔(只限 %s;重跑會重產)" % (len(cleaned), EVID_REL))
        if s["wt_dirty"]:
            raise RuntimeError("VDF 工作樹有未提交的改動(不是本工具的收據),先處理再跑(不覆蓋):%s · 看:git -C \"%s\" status"
                               % (s["wt_dirty"][:5], s["wt"]))
    return _ENSURE_V0100(root, s)


def publish(wt: Path, remote: str, picked: list, ran: list, stamp: str) -> str:
    """同 v0100(新分支 · 不 force · 不推 main);推完回到 origin/main(detached),工作樹乾淨、收據留在分支。"""
    name = _PUBLISH_V0100(wt, remote, picked, ran, stamp)
    if name and _LAST["up"]:
        git(["checkout", "--detach", _LAST["up"]], wt, check=False)
        print("  [VDF MAIN] 收據在分支 %s · 工作樹回到 %s" % (name, _LAST["up"]))
    return name


def _next_cmd(a) -> str:
    return _NEXT_CMD_V0101(a).replace(PRIOR_PATH.name, Path(__file__).name, 1)


V0100.ensure_worktree, V0100.publish, PRIOR._next_cmd = ensure_worktree, publish, _next_cmd


def run(argv=None, here: Path = HERE) -> int:
    """v0101 的流程(標籤換本版);RuntimeError(git 失敗 · 拒絕同步)→ 一行 [VDF MAIN] 停 · rc 2。"""
    keep = PRIOR.TAG
    PRIOR.TAG = TAG
    try:
        return PRIOR.run(argv, here)
    except RuntimeError as exc:
        print("  [VDF MAIN] 停:%s" % exc)
        print("[計] %s · 停在動手之前或中途 · FAIL" % TAG)
        return 2
    finally:
        PRIOR.TAG = keep


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    return run(argv)


def selftest() -> int:
    """離線假倉:工作樹留著上次沒交完的收據 → 本版清掉並照常同步、交完回到 main;別的髒檔照舊拒絕(rc 2 一行);前版鏈自測照跑。"""
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
    td = Path(tempfile.mkdtemp(prefix="vdf_mdl014c_"))
    keep = {k: os.environ.get(k) for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "LOCALAPPDATA")}
    os.environ.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x")
    VIA, EV = V0100.VIA_DIR, V0100.EVID
    try:
        remote = td / "remote.git"
        git(["init", "--bare", "-b", "main", str(remote)], td)
        seed = td / "seed"
        git(["clone", str(remote), str(seed)], td)
        via = seed / VIA
        (via / EV).mkdir(parents=True)
        (via / EV / "qg_onebridge.json").write_text("{\"old\": 1}\n", encoding="utf-8")
        (via / EV / "qg_onebridge.txt").write_text("old\n", encoding="utf-8")
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (reg / "VIA_VCGC_SubsystemSeat_v0100.json").write_text("{}\n", encoding="utf-8")
        (via / V0100.SSOT).write_text(json.dumps({"test_cases": {
            "vdf_case": {"argv": ["VDF_X", "--selftest"], "dependencies": ["functional modules/VDF/VDF_X_v*.py"]}}}), encoding="utf-8")
        (reg / "CGC_MDL149_VeritasCentralGovernanceConsole_v0001.py").write_text(
            "import json, sys, pathlib\ncase = sys.argv[3]\nev = pathlib.Path('docs/handoff/evidence')\n"
            "(ev / (case + '.json')).write_text(json.dumps({'case': case, 'rc': 0}))\n"
            "print(json.dumps({'case': case, 'rc': 0, 'marker': True, 'reused': False}))\n", encoding="utf-8")
        (via / "functional modules" / "VDF").mkdir(parents=True)
        (via / "functional modules" / "VDF" / "VDF_X_v0001.py").write_text("# VDF\n", encoding="utf-8")
        (seed / ".gitignore").write_text(VIA + "/functional modules/VDF/output_hub/\n" + VIA + "/VIA_Reports/*\n", encoding="utf-8")
        git(["add", "-A"], seed)
        git(["commit", "-m", "seed"], seed)
        git(["push", "origin", "main"], seed)
        work = td / "movies-dataset"
        git(["clone", str(remote), str(work)], td)
        (seed / "upstream.txt").write_text("main 前進\n", encoding="utf-8")
        git(["add", "-A"], seed)
        git(["commit", "-m", "upstream"], seed)
        git(["push", "origin", "main"], seed)
        git(["fetch", "origin"], work)
        os.environ["LOCALAPPDATA"] = str(td / "LocalAppData")
        wt = td / "LocalAppData" / "VIA" / "movies-dataset-vdf-main"
        git(["worktree", "add", "--detach", str(wt), "origin/main~1"], work)
        here_wt = wt / VIA / "functional modules" / "VDF"
        wev = wt / VIA / EV
        # 工作站實況:上次 --apply 的收據 stage 了一個、改了一個、還多一個未追蹤的
        (wev / "qg_onebridge.json").write_text("{\"new\": 1}\n", encoding="utf-8")
        git(["add", "--", EV + "/qg_onebridge.json"], wt / VIA)
        (wev / "qg_onebridge.txt").write_text("new\n", encoding="utf-8")
        (wev / "history").mkdir()
        (wev / "history" / "qg_onebridge-deadbeefdeadbeef.json").write_text("{}", encoding="utf-8")
        s0 = PRIOR.survey(work, "origin", wt)
        mine0, others0 = split_receipts(s0["wt_dirty"])
        chk("v0102-① 分堆:三個髒檔(stage 的 · 改的 · 未追蹤的)都認成本工具的收據、沒有別的",
            len(mine0) == 3 and not others0 and s0["wt_dirty"], s0["wt_dirty"])

        # ②+③ 整條流程:清掉殘留 → 移到最新 main → 交接 → 收據分支 → 回到 main
        V0100.GIT_LOG.clear()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc_ap = run(["--case", "vdf_case", "--apply", "--no-link-data"], here=here_wt)
        txt = out.getvalue()
        br = [b for b in git(["for-each-ref", "--format=%(refname:short)", "refs/heads"], remote).splitlines() if b.startswith(V0100.RECEIPT_PREFIX)]
        head_wt = git(["rev-parse", "HEAD"], wt)
        chk("v0102-② 殘留的收據自動清掉(印一行)· 工作樹移到最新 main · 交接重跑 · 收據分支推上去 · [計] PASS",
            rc_ap == 0 and "清掉上次沒交完的收據 3 檔" in txt and "=== %s · 執行 ===" % TAG in txt and (wt / "upstream.txt").exists()
            and br and "[收據] " in txt and "PASS" in txt.splitlines()[-1], (rc_ap, br, txt[-500:]))
        chk("v0102-③ 推完收據後工作樹回到 origin/main(detached · 乾淨);收據留在分支上(分支的 HEAD 比工作樹多一個提交);從不 force · 從不推 main",
            git(["rev-parse", "--abbrev-ref", "HEAD"], wt) == "HEAD" and head_wt == git(["rev-parse", "refs/heads/main"], remote)
            and git(["rev-parse", "refs/heads/" + br[0] + "~1"], remote) == head_wt and not _dirty_now(wt) and "工作樹回到 origin/main" in txt
            and not any(("--force" in c or "-f" in c or any(str(x).endswith(":refs/heads/main") or x == "main" for x in c[1:]))
                        for c in V0100.GIT_LOG if c and c[0] == "push"), (git(["status", "--porcelain"], wt), txt[-300:]))

        # ④ 收據殘留 + 別的髒檔 → 一個都不動、拒絕、rc 2 一行(不噴 traceback)
        (wev / "qg_onebridge.txt").write_text("again\n", encoding="utf-8")
        (wt / "someone_else.txt").write_text("他系統\n", encoding="utf-8")
        git(["add", "--", "someone_else.txt"], wt)
        V0100.GIT_LOG.clear()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc_bad = run(["--case", "vdf_case", "--apply", "--no-link-data"], here=here_wt)
        txt_bad = out.getvalue()
        chk("v0102-④ 有別的髒檔 → 收據也不動 · 拒絕 · [VDF MAIN] 停 一行 + rc 2(沒 traceback)· 訊息帶 git status 指引 · 沒跑交接 · 沒推",
            rc_bad == 2 and "[VDF MAIN] 停:" in txt_bad and "git -C" in txt_bad and "someone_else.txt" in txt_bad
            and (wev / "qg_onebridge.txt").read_text(encoding="utf-8") == "again\n" and "清掉" not in txt_bad
            and not [c for c in V0100.GIT_LOG if c and c[0] in ("push", "commit", "switch")], (rc_bad, txt_bad[-300:]))
        git(["reset", "-q", "--", "someone_else.txt"], wt)
        (wt / "someone_else.txt").unlink()

        # ⑤ 預演的 NEXT 印本版檔名;--selftest 由 main 攔下(不落到前版)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc_pre = run(["--case", "vdf_case", "--no-link-data"], here=here_wt)
        nxt = [ln for ln in out.getvalue().splitlines() if ln.startswith("NEXT: ")]
        chk("v0102-⑤ 預演:NEXT 印本版檔名(不是前版)· 還原殘留只在 --apply 才做(預演只報髒)· 標籤是本版",
            rc_pre == 0 and len(nxt) == 1 and Path(__file__).name in nxt[0] and PRIOR_PATH.name not in nxt[0]
            and "有未提交改動 1" in out.getvalue() and "=== %s · 預演" % TAG in out.getvalue(), (nxt, out.getvalue()[-300:]))
        src = Path(__file__).read_text(encoding="utf-8")
        imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
        chk("v0102-⑥ 三橋在 · 不匯入他系統程式 · 不碰 TA-Lib · 同意閘不寫 · 不寫環境變數(自測外)· 本體的 ensure_worktree / publish 已換上本版",
            all(t in src for t in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]", "[VIA:LIB-BRIDGE:v0100]"))
            and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VRN2_", "VCGC"))]
            and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
            and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src)
            and not re.search(r"\b" + "setx" + r"\b|os\.environ\[[^\]]+\]\s*=(?!=)|os\.environ\.update\(|" + "putenv", src.split("def " + "selftest")[0])
            and V0100.ensure_worktree is ensure_worktree and V0100.publish is publish)
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    print("  ── 前版鏈自測(VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        prc = 0
    else:
        V0100.ensure_worktree, V0100.publish, PRIOR._next_cmd = _ENSURE_V0100, _PUBLISH_V0100, _NEXT_CMD_V0101   # 前版自測看它自己的
        try:
            prc = PRIOR.selftest()
        finally:
            V0100.ensure_worktree, V0100.publish, PRIOR._next_cmd = ensure_worktree, publish, _next_cmd
    chk("v0102-⑦ 前版 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("  [計] %s 薄尾 %d/%d · %s" % (TAG, p, p + f, "PASS" if not f else "FAIL"))
    return 0 if not f else 1


if __name__ == "__main__":
    raise SystemExit(main())
