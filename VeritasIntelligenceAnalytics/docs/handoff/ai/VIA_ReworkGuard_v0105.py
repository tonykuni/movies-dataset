#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_ReworkGuard v0105 — 薄尾(v0104 以前一字不動;已鎖成功,修改開新版):R10 跨系統守衛補兩檢 + 本機 pre-commit 鉤

來源:操作員 2026-11-28 附件「VCGC / VDF 收尾」第三章 ①「.githooks/vcgc_precommit_guard.py 跨系統擁有權守衛」。
附件要另做一支守衛;本倉已有重工守門(13 類 · CI 的 rework-guard job 跑 base 上的尾版),照「重複功能先併再簡化」
把附件缺的兩檢掛進本家族新版,不另立第二支守衛:
  XOWN  一批改動同時動到兩個以上系統自己的夾(functional modules/<系統>/ · registry 的系統前綴程式檔)→ 黃,逐系統點名檔數
        (「每個系統只寫自己的冊與夾」;共用冊 · docs · .github · CLAUDE.md 不算任何系統)
  XIMP  新 .py 在語法樹裡 import 另一個系統的模組(VDF_ · VRN_ / VRN2_ · VQG_ · VAP_ · CGC_ / VCGC_),而且不在 try 裡 → 黃
        (補強三「用到別的系統模組的地方一律要有退路」;v0100 的 XSYS 只看 VDF / VRN 讀 CGC_* 字串,本檢補「任兩系統 · import 節點」)
本機鉤:`.githooks/pre-commit`(Python)叫本家族尾版 `check --hook`;只有紅才擋提交(黃照印)。
  鉤模式下 git 自己拿著 .git/index.lock,R3 的 index.lock 紅不算(其他 R3 照報)。
  啟用(操作員一次):python VIA_ReworkGuard_v0105.py hook install   → git config core.hooksPath .githooks
  看狀態:          python VIA_ReworkGuard_v0105.py hook status
其餘全照 v0104(經 v0100 模組全域換上 run_check 包裝)。
用法同 v0100:python VIA_ReworkGuard_v0105.py check [--fetch-prs] [--hook] | report | causes | hook install|status | --selftest
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
import ast
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = "v0105"
HERE = Path(__file__).resolve()
FAMILY = "VIA_ReworkGuard"
TAG = "VIA_ReworkGuard " + VERSION
HOOK_ENV = "VIA_REWORK_HOOK"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0105", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE                                         # v0100:main 叫它模組全域的 run_check
VIA = BASE.VIA
_PRIOR_RUN_CHECK, _PRIOR_TAG = PRIOR.run_check, PRIOR.TAG

SYSTEMS = ("VCGC", "VDF", "VRN", "VQG", "VAP")
_MOD_PREFIX = (("VCGC_", "VCGC"), ("CGC_", "VCGC"), ("VDF_", "VDF"), ("VRN2_", "VRN"), ("VRN_", "VRN"),
               ("VQG_", "VQG"), ("VAP_", "VAP"))


def __getattr__(name):
    return getattr(PRIOR, name)


def owner(p: str):
    """倉根相對路徑 → 擁有它的系統;共用(冊 · docs · .github · 根檔)回 None。"""
    if not p.startswith(VIA):
        return None
    rel = p[len(VIA):]
    m = re.match(r"functional modules/(VDF|VRN2?|VQG|VAP)/", rel)
    if m:
        return "VRN" if m.group(1).startswith("VRN") else m.group(1)
    m = re.match(r"supportive modules/registry/([^/]+\.(py|ps1|psm1))$", rel)
    if m:
        return mod_system(m.group(1))
    return None


def mod_system(name: str):
    base = name.rsplit("/", 1)[-1]
    for pre, sysname in _MOD_PREFIX:
        if base.startswith(pre):
            return sysname
    return None


def d_xown(ch) -> list:
    by = {}
    for k in ("A", "M", "D", "U"):
        for p in ch.get(k, ()):
            s = owner(p)
            if s:
                by.setdefault(s, []).append(p)
    if len(by) < 2:
        return []
    parts = " · ".join(f"{s} {len(by[s])} 檔(例 `{by[s][0]}`)" for s in SYSTEMS if s in by)
    return [("YELLOW", "R10", f"XOWN 一批改動跨 {len(by)} 個系統自己的夾:{parts} → 每個系統只寫自己的夾;不是本批範圍就拆開或還原")]


def d_ximp(repo, files) -> list:
    out = []
    for p in files:
        me = owner(p)
        if not p.endswith(".py") or me is None or "/intake/" in p:
            continue
        tree = BASE._parse(BASE.read(repo, p))
        if tree is None:
            continue
        guarded = set()
        for t in (n for n in ast.walk(tree) if isinstance(n, ast.Try)):
            for blk in (t.body,):
                for st in blk:
                    for n in ast.walk(st):
                        guarded.add(id(n))
        hits = []
        for n in ast.walk(tree):
            if id(n) in guarded:
                continue
            names = [a.name for a in n.names] if isinstance(n, ast.Import) else (
                [n.module] if isinstance(n, ast.ImportFrom) and n.module and not n.level else [])
            for nm in names:
                other = mod_system(nm.split(".")[0])
                if other and other != me:
                    hits.append(f"{nm}(L{n.lineno} · {other})")
        if hits:
            out.append(("YELLOW", "R10", f"XIMP `{p}`({me})import 別的系統模組不在 try 裡:{', '.join(hits[:3])} → 包 try 給退路(拿掉那個系統也要載得起來)"))
    return out


def run_check(repo, base="origin/main", head="HEAD", fetch=False, open_prs=None) -> dict:
    r = _PRIOR_RUN_CHECK(repo, base, head, fetch, open_prs)
    ch = BASE.changed(Path(repo), base, head)
    new = sorted(set(ch["A"]) | set(ch["U"]))
    extra = d_xown(ch) + d_ximp(Path(repo), new)
    r["findings"] += [{"lamp": a, "cause": b, "what": c} for a, b, c in extra]
    if os.environ.get(HOOK_ENV) == "1":                   # 鉤模式:index.lock 是 git commit 自己拿的
        r["findings"] = [f for f in r["findings"] if not (f["cause"] == "R3" and "index.lock" in f["what"])]
    r["lamp"] = max((f["lamp"] for f in r["findings"] if f["lamp"] != "GRAY"), key=lambda x: BASE.ORDER[x], default="GREEN")
    r["tool"] = TAG
    return r


def _install():
    PRIOR._install()                                      # v0104 的 d_openpr 換上(冪等)
    BASE.run_check = run_check
    BASE.TAG = TAG
    for c in BASE.CAUSES:
        c["cmd"] = c["cmd"].replace(PRIOR_PATH.name, HERE.name)
        if c.get("code") == "R10" and "XOWN" not in c.get("detector", ""):
            c["detector"] = c["detector"] + " · XOWN(一批跨兩系統的夾)· XIMP(import 別系統模組沒 try)"


def _uninstall():
    BASE.run_check = _PRIOR_RUN_CHECK
    BASE.TAG = _PRIOR_TAG
    for c in BASE.CAUSES:
        c["cmd"] = c["cmd"].replace(HERE.name, PRIOR_PATH.name)
        if c.get("code") == "R10":
            c["detector"] = c["detector"].split(" · XOWN")[0]


_install()


def _git(repo, *a) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True)


def hook(verb: str, repo=None) -> int:
    repo = Path(repo) if repo else BASE.repo_root()
    f = repo / ".githooks" / "pre-commit"
    cur = _git(repo, "config", "--get", "core.hooksPath").stdout.strip()
    if verb == "install":
        if not f.is_file():
            print(f"[{TAG}] hook RED · 找不到 {f.relative_to(repo)}(先同步到有它的分支)")
            return 1
        if cur and cur != ".githooks":
            print(f"[{TAG}] hook RED · core.hooksPath 已設成 {cur!r}(別人的設定不蓋;要換請自己 git config core.hooksPath .githooks)")
            return 1
        _git(repo, "config", "core.hooksPath", ".githooks")
        cur = _git(repo, "config", "--get", "core.hooksPath").stdout.strip()
    ok = cur == ".githooks" and f.is_file()
    print(f"[{TAG}] hook {'GREEN' if ok else 'YELLOW'} · core.hooksPath={cur or '(未設)'} · .githooks/pre-commit {'在' if f.is_file() else '不在'}"
          + ("" if ok else " → python " + HERE.name + " hook install"))
    return 0 if ok else 2


def selftest() -> int:
    import contextlib
    import io
    import shutil
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    buf = io.StringIO()
    _uninstall()
    try:
        with contextlib.redirect_stdout(buf):
            rc0 = PRIOR.selftest()                        # v0104 自測照 v0104 的判法跑(它再照前版鏈跑)
    finally:
        _install()
    print(f"=== {TAG} · 薄尾自測(XOWN · XIMP · 鉤模式;暫存倉 · 零網路)===", flush=True)
    chk("⓪ 前版 %s 自測照過(含整條前版鏈)" % PRIOR_PATH.name, rc0 == 0, buf.getvalue()[-300:])
    acc_file = next((q / "supportive modules" / "VIA_SuperAccel_Module.py" for q in HERE.parents
                     if (q / "supportive modules" / "VIA_SuperAccel_Module.py").exists()), None)
    if acc_file is None:                                  # CI 把本家族抄到暫存夾跑:樹上沒有加速器 = 灰(照實印,不算綠也不算假加速)
        print("  [GRAY] ① 加速器橋:這棵樹上沒有 VIA_SuperAccel_Module.py(CI 暫存夾)→ 載入檢查未跑", flush=True)
    else:
        chk("① 加速器橋執行時載到(VIA_ACCEL is not None)", VIA_ACCEL is not None, str(acc_file))
    td = Path(tempfile.mkdtemp(prefix="via_rework105_"))
    env = dict(os.environ, GIT_AUTHOR_NAME="fx", GIT_AUTHOR_EMAIL="fx@fx", GIT_COMMITTER_NAME="fx", GIT_COMMITTER_EMAIL="fx@fx")
    env.pop(HOOK_ENV, None)

    def g(*a):
        return subprocess.run(["git", "-C", str(td), *a], capture_output=True, text=True, env=env, check=True).stdout.strip()
    try:
        g("init", "-q", "-b", "main")
        (td / "a.txt").write_text("a\n", encoding="utf-8")
        g("add", "-A")
        g("commit", "-q", "-m", "base")
        g("update-ref", "refs/remotes/origin/main", "HEAD")
        vdf = td / VIA / "functional modules" / "VDF"
        vrn = td / VIA / "functional modules" / "VRN"
        vdf.mkdir(parents=True)
        vrn.mkdir(parents=True)
        (vdf / "VDF_X_v0100.py").write_text("import VRN_SystemManager_v0100\ntry:\n    import CGC_MDL149_A\nexcept Exception:\n    pass\nimport json\n", encoding="utf-8")
        (vrn / "VRN_Y_v0100.py").write_text("try:\n    import VDF_SystemManager_v0200 as V\nexcept ImportError:\n    V = None\n", encoding="utf-8")
        ch = BASE.changed(td, "origin/main", "HEAD")
        xo = d_xown(ch)
        chk("② XOWN:一批動到 VDF + VRN 兩個系統的夾 → 黃,兩系統都點名", len(xo) == 1 and xo[0][0] == "YELLOW" and "VDF 1" in xo[0][2] and "VRN 1" in xo[0][2], xo)
        chk("③ XOWN:只動一個系統 + 共用冊 / docs → 不報",
            d_xown({"A": [VIA + "functional modules/VDF/a.py", VIA + "supportive modules/registry/VIA_X_v0100.json", "CLAUDE.md"], "M": [], "D": [], "U": []}) == [])
        new = sorted(set(ch["A"]) | set(ch["U"]))
        xi = d_ximp(td, new)
        chk("④ XIMP:VDF 檔頂層 import VRN 模組 → 黃;try 裡的 CGC / VDF 匯入與標準庫不報",
            len(xi) == 1 and "VRN_SystemManager_v0100" in xi[0][2] and "VDF_X_v0100.py" in xi[0][2] and "CGC_MDL149_A" not in xi[0][2], xi)
        chk("⑤ owner():registry 程式檔依前綴歸系統;共用冊與 VIA_ 檔不歸任何系統",
            owner(VIA + "supportive modules/registry/CGC_MDL1_v0100.py") == "VCGC" and owner(VIA + "supportive modules/registry/VDF_Z_v0100.py") == "VDF"
            and owner(VIA + "supportive modules/registry/VIA_Component_Inventory_SSOT_v0100.json") is None and owner(VIA + "functional modules/VRN2/x.py") == "VRN")
        g("add", "-A")
        g("commit", "-q", "-m", "mine")
        (td / ".git" / "index.lock").write_text("", encoding="utf-8")
        try:
            r_plain = run_check(td, "origin/main", "HEAD", False, set())
            os.environ[HOOK_ENV] = "1"
            try:
                r_hook = run_check(td, "origin/main", "HEAD", False, set())
            finally:
                os.environ.pop(HOOK_ENV, None)
        finally:
            (td / ".git" / "index.lock").unlink()
        lock_plain = any(f["cause"] == "R3" and "index.lock" in f["what"] for f in r_plain["findings"])
        lock_hook = any(f["cause"] == "R3" and "index.lock" in f["what"] for f in r_hook["findings"])
        chk("⑥ 鉤模式:git 自己的 index.lock 不算紅;一般模式照報紅", lock_plain and r_plain["lamp"] == "RED" and not lock_hook, (r_plain["lamp"], r_hook["lamp"]))
        chk("⑦ run_check 帶上 XOWN / XIMP,tool = 本版", any("XOWN" in f["what"] for f in r_hook["findings"]) and any("XIMP" in f["what"] for f in r_hook["findings"]) and r_hook["tool"] == TAG)
        hk = td / ".githooks"
        hk.mkdir()
        (hk / "pre-commit").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            rc_i = hook("install", td)
            rc_s = hook("status", td)
        chk("⑧ hook install 設 core.hooksPath=.githooks(暫存倉);status 綠", rc_i == 0 and rc_s == 0 and g("config", "--get", "core.hooksPath") == ".githooks")
        g("config", "core.hooksPath", "elsewhere")
        with contextlib.redirect_stdout(io.StringIO()):
            rc_o = hook("install", td)
        chk("⑨ 別人已設的 core.hooksPath 不蓋(紅、不改)", rc_o == 1 and g("config", "--get", "core.hooksPath") == "elsewhere")
    finally:
        shutil.rmtree(td, ignore_errors=True)
    chk("⑩ main 走本版 run_check(v0100 模組全域已換上)", BASE.run_check is run_check and BASE.TAG == TAG)
    pub = [n for n in vars(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n)) and getattr(getattr(PRIOR, n), "__module__", "") == PRIOR.__name__]
    chk("⑪ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    src = HERE.read_text(encoding="utf-8")
    tree = ast.parse(src)
    bad = [n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("eval", "exec")]
    chk("⑫ 本版沒有 eval / exec;第 3 行是加速器橋標記", not bad and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]", bad)
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["hook"]:
        return hook(a[1] if len(a) > 1 else "status", a[a.index("--repo") + 1] if "--repo" in a else None)
    if "--hook" in a:
        a.remove("--hook")
        os.environ[HOOK_ENV] = "1"
    _install()
    return BASE.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
