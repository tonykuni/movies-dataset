#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0199 — 薄尾(v0198 以前一字不動):主機 2026-11-28 第二輪實跑抓到的三件事

一、v0192 自測「run:工作立刻跑一次 · 帶 VDF 入口標記」只在主機 NG:
    run_job 的入口標記取「環境裡已有的值優先」;操作員的 PS 工作階段由 Register-VIA-Commands 設了
    VIA_CENTRAL_ENTRY / VIA_ENTRY_CONTROL(= VCGC 唯一入口控制),自測讀到的是那個值,不是 VDF 自己的 → NG。
    容器把兩個變數設成主機的值,同一行 NG 重現(其餘 5 支設了照樣綠 → 它們另有原因)。行為沒錯,是自測吃了本機環境。
    → 本版:跑前版鏈自測的期間,暫時拿掉這兩個入口標記,跑完原樣放回(只在自測期間;動詞照舊)。
二、tidy 的 temp 證明範圍太窄:只拿 functional modules/VDF 的檔名比,副本裡還有 supportive modules / tools / tests,
    主機 5 份全判「證明不過(57%)」→ 照規矩一份沒搬。
    → 本版改成更嚴、範圍對的證明:副本每個 .py 的內容(原樣或 CRLF→LF 後)在倉的 git 物件庫裡找得到(= 隨時可從 git 取回),
      而且現役程式(tidy 所在的管理器家族本身除外)沒提到這條路徑,才搬進隔離區;非 .py 檔照搬(移動不是刪除),
      不在 git 的檔數照實記在計畫裡。刪除仍要另外問、全部檔案都在 git 才行(本版不做刪除)。
三、主機的紅藏在「前版鏈子行程」裡,vv 只看得到包裝行。
    → 本版新增 diag --only 家族,家族:每個家族的每一版都單獨跑一次自測(3 道並行 · 每版上限 600 秒),
      列每版 rc 與最像根因的行,點名「最先紅的版」(= 根因所在);收據 VIA_Reports/vdf/manager/DIAG_latest.json。
零網路 · 不碰 TA-Lib · 不設同意閘 · 不 import VCGC。
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

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

VERSION = "v0199"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent
ENTRY_MARKERS = ("VIA_CENTRAL_ENTRY", "VIA_ENTRY_CONTROL")
DIAG_TIMEOUT = 600


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0198(tidy · vv 原因行)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


V198 = PRIOR
V197, V194 = V198.V197, V198.V194

# ---------- 二、temp 證明:內容在 git 物件庫裡 ----------


def git_root(start: Path) -> Path | None:
    try:
        r = subprocess.run(["git", "-C", str(start), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=30)
        return Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def blob_ids(data: bytes) -> set:
    out = set()
    for b in {data, data.replace(b"\r\n", b"\n")}:
        out.add(hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest())
    return out


def git_has(repo: Path, ids: list) -> set:
    """git cat-file --batch-check:回在物件庫裡的那些 id(只讀)。"""
    if not ids:
        return set()
    r = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch-check"], input="\n".join(ids) + "\n",
                       capture_output=True, text=True, timeout=600)
    return {ln.split()[0] for ln in r.stdout.splitlines() if ln.strip() and not ln.strip().endswith("missing")}


def temp_proof(copy: Path, code_dir: Path, tails_text: str, repo: Path | None = None) -> dict:
    mention = ("temp/VDF_Manager" in tails_text) or ("temp\\\\VDF_Manager" in tails_text) or ("temp\\VDF_Manager" in tails_text)
    repo = repo or git_root(code_dir)
    files = [f for f in copy.rglob("*") if f.is_file()]
    if repo is None:
        return {"ok": False, "mention": mention, "why": "找不到 git 倉(沒有 git 就不能證明)", "files": len(files)}
    ids = {}
    for f in files:
        try:
            ids[f] = blob_ids(f.read_bytes())
        except OSError:
            ids[f] = set()
    have = git_has(repo, sorted({i for s in ids.values() for i in s}))
    py = [f for f in files if f.suffix == ".py"]
    py_in = [f for f in py if ids[f] & have]
    all_in = [f for f in files if ids[f] & have]
    miss_py = [str(f.relative_to(copy)) for f in py if not (ids[f] & have)]
    ok = (not mention) and bool(py) and len(py_in) == len(py)
    return {"ok": ok, "mention": mention, "py": len(py), "py_in_git": len(py_in), "files": len(files), "files_in_git": len(all_in),
            "missing_py": miss_py[:10]}


_ORIG_PROOF = V198.temp_proof
V198.temp_proof = temp_proof                                   # build_plan 讀模組層 temp_proof

# ---------- 一、自測期間拿掉入口標記 ----------


class no_entry_markers:
    def __enter__(self):
        self.keep = {k: os.environ.pop(k) for k in ENTRY_MARKERS if k in os.environ}
        return self

    def __exit__(self, *exc):
        os.environ.update(self.keep)


# ---------- 三、diag ----------


def family_versions(root: Path, fam: str) -> list:
    rx = V194._p("SM_VER_RX")
    out = []
    for p in V194._p("sm_own_files")(root):
        m = rx.match(p.name)
        if m and m.group("fam") == fam:
            out.append(p)
    return sorted(out, key=_vnum)


def run_version(p: Path, env: dict, timeout: int = DIAG_TIMEOUT) -> dict:
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, str(p), "--selftest"], cwd=tempfile.gettempdir(), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=env, stdin=subprocess.DEVNULL)
        rc, text = r.returncode, (r.stdout or "") + "\n" + (r.stderr or "")
    except subprocess.TimeoutExpired as exc:
        rc, text = 124, V197._txt(exc.stdout) + "\n" + V197._txt(exc.stderr)
    lines = [ln for ln in V198.why_lines(text, 20) if not V197.WRAP_RX.search(ln)][:3] if rc else []
    return {"file": p.name, "version": "v%04d" % _vnum(p), "rc": rc, "secs": round(time.time() - t0, 1), "why": lines}


def diag(root: Path, fams: list, lanes: int = 3, env: dict | None = None) -> dict:
    env = env or V194._p("sm_child_env")()
    jobs = [(fam, p) for fam in fams for p in family_versions(root, fam)]
    with ThreadPoolExecutor(max_workers=max(1, lanes)) as ex:
        rows = list(ex.map(lambda j: {"family": j[0], **run_version(j[1], env)}, jobs))
    out = {}
    for fam in fams:
        rs = [r for r in rows if r["family"] == fam]
        red = [r for r in rs if r["rc"] not in (0, 2, 3, 4)]
        out[fam] = {"versions": rs, "first_red": red[0]["version"] if red else None,
                    "lamp": "RED" if red else ("YELLOW" if any(r["rc"] for r in rs) else ("GREEN" if rs else "GRAY"))}
    return out


def cmd_diag(args: list) -> int:
    only = args[args.index("--only") + 1] if "--only" in args else ""
    fams = [x.strip() for x in only.split(",") if x.strip()]
    if not fams:
        print(f"[{TAG}] diag 要點名家族:diag --only VDF_ENG232_TWIndexOfficial,VDF_MDL008_FetchSystem")
        return 2
    root = V194._p("sm_via_root")()
    known = {f for f in V194._p("sm_engines")(root)}
    full = []
    for f in fams:
        hit = [k for k in known if k == f] or sorted(k for k in known if f in k)
        full += hit[:1] if hit else [f]
    t0 = time.time()
    print(f"[{TAG}] diag · {len(full)} 個家族的每一版各跑一次自測(3 道 · 每版上限 {DIAG_TIMEOUT}s)· 加速器 {'載到' if V198.VIA_ACCEL is not None else '沒載到'}",
          flush=True)
    with V194.Beat(f"{TAG} diag") as _beat:
        res = diag(root, full)
    out = V194._p("v73_out")(root)
    (out / "DIAG_latest.json").write_text(json.dumps({"by": TAG, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                                     "families": res, "secs": round(time.time() - t0, 1)}, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    worst = "GREEN"
    for fam, r in res.items():
        worst = V194.worst([worst, r["lamp"]])
        print(f"  {r['lamp']:6} {fam} · 最先紅的版 {r['first_red'] or '—'}")
        for v in r["versions"]:
            mark = "OK" if v["rc"] == 0 else ("黃" if v["rc"] in (2, 3, 4) else "紅")
            print(f"     {mark} {v['version']} rc {v['rc']} · {v['secs']}s" + "".join(f"\n         {ln}" for ln in v["why"]))
    print(f"[收據] VIA_Reports/vdf/manager/DIAG_latest.json · {round(time.time() - t0, 1)}s")
    return {"GREEN": 0, "YELLOW": 2}.get(worst, 1)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 5 項 + 前版 {PRIOR_PATH.name} 自測(拿掉入口標記)· 暫存夾 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", V198.VIA_ACCEL is not None and VIA_ACCEL is not None
        and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_NET_TOOL_PATH is not None)
    os.environ["VIA_ENTRY_CONTROL"] = "FX_ENTRY"
    with no_entry_markers():
        inside = os.environ.get("VIA_ENTRY_CONTROL")
    after = os.environ.pop("VIA_ENTRY_CONTROL", None)
    chk("T2 自測期間入口標記拿掉 · 結束原樣放回", inside is None and after == "FX_ENTRY", (inside, after))
    with tempfile.TemporaryDirectory(prefix="vdf_sm199_") as td:
        d = Path(td)
        repo = d / "repo"
        (repo / "a").mkdir(parents=True)
        (repo / "a" / "x.py").write_bytes(b"x = 1\n")
        gitok = subprocess.run(["git", "init", "-q", str(repo)], capture_output=True).returncode == 0
        if gitok:
            subprocess.run(["git", "-C", str(repo), "add", "-A"], capture_output=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=fx", "-c", "user.email=fx@example.invalid", "commit", "-qm", "fx"],
                           capture_output=True)
        cp = d / "copy"
        (cp / "deep" / "tools").mkdir(parents=True)
        (cp / "deep" / "tools" / "x.py").write_bytes(b"x = 1\r\n")                # CRLF 取出的同一份
        (cp / "evidence.json").write_text("{}", encoding="utf-8")                 # 非 .py、不在 git:照搬、照實記
        p1 = temp_proof(cp, repo, "", repo)
        (cp / "only_here.py").write_text("y = 2\n", encoding="utf-8")
        p2 = temp_proof(cp, repo, "", repo)
        p3 = temp_proof(cp, repo, "temp/VDF_Manager_v0104", repo)
        chk("T3 temp 證明:.py 內容(含 CRLF 版)在 git → 過 · 有一支 .py 只在副本 → 不過 · 現役程式提到路徑 → 不過",
            gitok and p1["ok"] and p1["files_in_git"] == 1 and p1["files"] == 2 and not p2["ok"] and p2["missing_py"] == ["only_here.py"]
            and not p3["ok"], (p1, p2))
        vd = d / "via" / "functional modules" / "VDF"
        vd.mkdir(parents=True)
        for v, code in (("0100", "import sys;print('  [OK] a');sys.exit(0)"), ("0101", "import sys;print('  [FAIL] 真的壞了');sys.exit(1)"),
                        ("0102", "import sys;print('  [FAIL] ⓪ 前版 v0101 自測照過 · rc 1');sys.exit(1)")):
            (vd / f"VDF_ENG990_Fx_v{v}.py").write_text(code + "\n# --selftest\n", encoding="utf-8")
        keep = V194._p("sm_own_files")
        rows = sorted(vd.glob("VDF_ENG990_Fx_v*.py"))
        V194.PRIOR.sm_own_files = lambda r: rows
        try:
            res = diag(d / "via", ["VDF_ENG990_Fx"], 3, dict(os.environ))["VDF_ENG990_Fx"]
        finally:
            V194.PRIOR.sm_own_files = keep
        chk("T4 diag:每一版各跑 · 點名最先紅的版(v0101)· 包裝行不當原因",
            [v["rc"] for v in res["versions"]] == [0, 1, 1] and res["first_red"] == "v0101" and res["versions"][1]["why"] == ["[FAIL] 真的壞了"]
            and res["versions"][2]["why"] == [], res)
    os.environ["VIA_ENTRY_CONTROL"] = "CGC_MDL157_VIAUniqueEntryControl_v0109"
    os.environ["VIA_CENTRAL_ENTRY"] = "1"
    try:
        V198.temp_proof = _ORIG_PROOF                         # 前版自測看它自己的判法(夾具不在 git)
        with no_entry_markers():
            rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    finally:
        V198.temp_proof = temp_proof
        os.environ.pop("VIA_ENTRY_CONTROL", None)
        os.environ.pop("VIA_CENTRAL_ENTRY", None)
    chk("T5 前版 v0198 自測照過(含整條前版鏈;環境帶著主機那兩個入口標記也照過)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["diag"]:
        return cmd_diag(a[1:])
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
