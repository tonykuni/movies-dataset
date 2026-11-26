#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL022_SafeParallelLaunch v0112 — 薄尾(v0100–v0111 一字不動):每輪接上「同一輪共用回應快取」

操作員 2026-11-26「YES FOR ALL」核准第 1 項:同一個 API 不重複擷取。
本版只在 run / launch(不是 --check)外面包一層:
  ① 開跑前用 VDF_MDL024_RunFetchCache 尾版在本機 TEMP 建本輪快取夾與掛鉤夾,設 env VIA_VDF_RUN_CACHE 並把掛鉤夾排到
     PYTHONPATH 最前面 → 這一輪所有 python 子行程(擷取引擎與它們的子行程)同一個 GET 只真的送一次。
  ② 跑完(含失敗 / 中斷)一定收尾:讀計數 → 寫 VIA_Reports\vdf\launch\RUN_CACHE_latest.json(只計數與主機名,不含網址與內容)
     → 印一行「共用快取 命中 X / 請求 Y」→ 刪掉本輪快取夾。summary 動詞也印這一行。
  ③ --no-shared-cache:這一輪不接快取(照 v0111)。找不到 MDL024 → 照 v0111 跑並印黃字,不擋。
  ④ 子行程預設 PYTHONWARNINGS=ignore::SyntaxWarning(只藏舊檔字串跳脫的語法警告,不改任何行為;已設就不動)。
其他一律照 v0111(降壓一次後 3 道同步跑、不中途減道;Rich 詳細摘要矩陣;進度檔)。不代設同意閘;不碰 TA-Lib。
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
STEM = "VDF_MDL022_SafeParallelLaunch"
VERSION = "v0112"
TAG = f"{STEM} {VERSION}"
CACHE_STEM = "VDF_MDL024_RunFetchCache"
CACHE_RECEIPT = VIA / "VIA_Reports" / "vdf" / "launch" / "RUN_CACHE_latest.json"
NO_CACHE = "--no-shared-cache"
RUNNER = None                                           # 自測換掉主流程用(本檔自己的鉤子,不改前版模組)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def cache_module(folder: Path = HERE):
    hits = sorted(folder.glob(CACHE_STEM + "_v[0-9][0-9][0-9][0-9].py"), key=_vnum)
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location(f"{CACHE_STEM}_for_{VERSION}", hits[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def wants_cache(args: list) -> bool:
    return args[:1] in (["run"], ["launch"]) and "--check" not in args and NO_CACHE not in args


def cache_line(st: dict) -> str:
    if not st:
        return "共用快取 · 本輪沒接(--no-shared-cache 或找不到 MDL024)"
    mb = st.get("bytes_saved", 0) / 1048576
    return (f"共用快取 · 命中 {st.get('hit', 0)} / 請求 {st.get('requests', 0)}({st.get('hit_pct', 0.0)}%)"
            f" · 省下 {mb:.1f} MB · 真送 {st.get('miss_stored', 0) + st.get('miss_big', 0)}")


def _save_receipt(st: dict, path: Path = CACHE_RECEIPT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rec = {"tag": TAG, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), **st}
    tmp = path.with_name(path.name + f".{os.getpid()}.sdd_tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def run_with_cache(args: list, runner, env=None, receipt: Path = CACHE_RECEIPT, base=None) -> int:
    """在 env(預設 os.environ)設好本輪快取再跑 runner(args);跑完一定收尾。"""
    env = os.environ if env is None else env
    mod = cache_module()
    if mod is None:
        print(f"[{TAG}] 黃 · 找不到 {CACHE_STEM} 尾版:本輪不接共用快取,照 v0111 跑", flush=True)
        return runner(args)
    root, hook = mod.prepare(base)
    keep = {k: env.get(k) for k in (mod.ENV_DIR, "PYTHONPATH")}
    env.update({k: v for k, v in mod.child_env(root, hook, env).items() if k in keep})
    print(f"[{TAG}] 共用快取接上 · 本輪夾在本機 TEMP · 同一個 GET 只真的送一次(--no-shared-cache 可關)", flush=True)
    try:
        return runner(args)
    finally:
        for k, v in keep.items():
            if v is None:
                env.pop(k, None)
            else:
                env[k] = v
        st = mod.stats(root)
        try:
            _save_receipt(st, receipt)
        except OSError as exc:
            print(f"[{TAG}] 共用快取收據寫不進:{exc}", flush=True)
        mod.cleanup(root)
        print(f"[{TAG}] {cache_line(st)}", flush=True)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    os.environ.setdefault("PYTHONWARNINGS", "ignore::SyntaxWarning")
    runner = RUNNER or PRIOR.main
    if args[:1] == ["summary"]:
        rc = runner(args)
        try:
            st = json.loads(CACHE_RECEIPT.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            st = {}
        print(f"[{TAG}] {cache_line(st)}", flush=True)
        return rc
    if wants_cache(args):
        return run_with_cache(args, runner)
    return runner([a for a in args if a != NO_CACHE])


def selftest() -> int:
    import subprocess
    import tempfile
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, VIA_NET_TOOL_PATH)
    chk("① 只在 run / launch 接快取;--check · --no-shared-cache · 其他動詞不接",
        wants_cache(["run"]) and wants_cache(["launch", "--skip-preflight"]) and not wants_cache(["launch", "--check"])
        and not wants_cache(["run", NO_CACHE]) and not wants_cache(["summary"]) and not wants_cache(["status"]))
    chk("② 找得到 MDL024 尾版", cache_module() is not None)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        env = {"PYTHONPATH": "orig"}
        seen = {}

        def fake(a):
            seen["env"] = dict(env)
            seen["args"] = list(a)
            mod = cache_module()
            root = Path(env[mod.ENV_DIR])
            mod._stat(root, "miss_stored", "http://example.invalid/x", 10)
            mod._stat(root, "hit", "http://example.invalid/x", 10)
            return 0

        rc = run_with_cache(["run", "--dry"], fake, env=env, receipt=td / "rc.json", base=td)
        mod = cache_module()
        root = Path(seen["env"].get(mod.ENV_DIR, ""))
        chk("③ 跑的時候 env 有快取夾 · 掛鉤夾在 PYTHONPATH 最前面 · 原 PYTHONPATH 還在",
            rc == 0 and seen["env"]["PYTHONPATH"].endswith(os.pathsep + "orig")
            and seen["env"]["PYTHONPATH"].split(os.pathsep)[0].endswith("_hook"), seen.get("env"))
        rec = json.loads((td / "rc.json").read_text(encoding="utf-8"))
        chk("④ 收尾:env 還原 · 本輪夾已刪 · 收據只有計數(命中 1 / 請求 2)不含網址",
            env == {"PYTHONPATH": "orig"} and not root.exists() and rec.get("hit") == 1 and rec.get("requests") == 2
            and "example.invalid/x" not in json.dumps(rec), (env, rec))

        def boom(a):
            raise RuntimeError("x")

        try:
            run_with_cache(["run"], boom, env=env, receipt=td / "rc2.json", base=td)
            raised = False
        except RuntimeError:
            raised = True
        left = [p for p in (td / "via_vdf_run_cache").iterdir()] if (td / "via_vdf_run_cache").exists() else []
        chk("⑤ 主流程丟例外也收尾(env 還原 · 夾刪掉 · 收據照寫)· 例外照樣往上丟",
            raised and env == {"PYTHONPATH": "orig"} and not left and (td / "rc2.json").exists(), left)
    calls = []
    globals()["RUNNER"] = lambda a: calls.append(list(a)) or 0
    try:
        keep = os.environ.get("VIA_VDF_RUN_CACHE")
        main(["status", NO_CACHE])
        main(["launch", "--check"])
        unchanged = os.environ.get("VIA_VDF_RUN_CACHE") == keep
    finally:
        globals()["RUNNER"] = None
    chk("⑥ 其他動詞照轉 v0111(拿掉 --no-shared-cache)· --check 不建快取",
        calls == [["status"], ["launch", "--check"]] and unchanged, calls)
    alone = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, timeout=1800)
    tail = (alone.stdout.strip().splitlines() or [""])[-1]
    chk("⑦ 前版 v0111 自測單獨跑:綠,或它自己照實回黃(rc 2,例:容器缺 rich)· 本版不換裝前版任何名稱",
        alone.returncode in (0, 2), (alone.returncode, tail))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("檔面:第 3 行加速器標記 · 雙橋在 · 不設同意閘 · 不含本機路徑",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M)
        and "C:\\Users\\" + "tonyk" not in src)
    yellow = alone.returncode == 2
    print(f"[selftest] {TAG} {len(ok)}/{len(ok) + len(bad)} " + ("PASS" if not bad else "FAIL · " + " · ".join(bad))
          + (" · 前版自測本來就黃(照實回 rc 2)" if yellow and not bad else ""), flush=True)
    return 1 if bad else (2 if yellow else 0)


if __name__ == "__main__":
    sys.exit(main())
