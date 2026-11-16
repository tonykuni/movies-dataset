#!/usr/bin/env python3
r"""VDF_MDL013_ActivateVDF v0118 — 薄尾:記憶體准入閘認人改看原始命令列(sys.orig_argv)· 收據標對哪一支 · 指揮行程確實不等

工作站實跑(2026-11-15 09:55,ActivateVDF v0117 · 管理員 v0181):記憶體閘最低可用 69 → 481 MB · engine_launch 1,610 → 1,269 秒 ·
自測 RED 10 → 6;可是收尾「[記憶體] 子行程 261(引擎工作 261)· 准入等過 40 支(最長 45.4 秒)· 峰值最大 3245 MB(sitecustomize.py --selftest)」——
指揮行程算成 0 支、峰值最大那支認不出是誰。
根因(容器重現):工作站的中央啟動鉤(supportive modules/bootstrap/sitecustomize.py)用 runpy.run_path 接力跑本輪鉤;
runpy 跑的期間把 sys.argv[0] 換成「正在跑的那個檔」→ 本輪鉤看到的 argv[0] 一律是 sitecustomize.py:
  · 收據的 argv 全成「sitecustomize.py …」(哪支引擎吃了 3.2 GB 看不出來)
  · 指揮行程(VDF_SystemManager_* / ActivateVDF)認不出 → 也在准入閘排隊(本來一律不等)
本版只改一件事:認人改看 sys.orig_argv(直譯器收到的原始命令列,runpy 改不到;3.10 起有;沒有才退回 sys.argv):
  · 跳過直譯器選項(-X / -W 帶值、其他 -x 單旗標);-c → 記「-c <其後參數的檔名>」(引擎載入探針會帶引擎路徑)· -m → 記模組名;
  · 收據 argv 記腳本檔名 + 參數(路徑一律只留檔名)· 指揮行程照 v0117 的名單判(不等)。
另一件(操作員 2026-11-15 令「將此模組移除:… VDF_ENG070_GroupClassificationIndex · 逾時」):
  · engine_list 步多讀「啟動退役冊」VDF_LaunchRetire_SSOT_v*.json 尾版:冊上的家族不啟動、不計分母,總覽列在「已被取代 / 退役」並寫原因。
    引擎檔不刪不搬(ENG071 GroupBacktest 以尾版 glob 直接 import ENG070;VAP_ENG015 讀它的產出)。冊不在 / 讀不了 → 照前版(全啟動)。
其餘(保底 · 等待上限 · 工作數 · 峰值收據 · 總覽一段)全照 v0117。VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib。
用法同前(ActivateVDF.py run …;本檔是尾版就用本版)· 自測 --selftest(本版 + 前版鏈)。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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
import importlib.util
import json
import os
import re
import sys
import types
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL013_ActivateVDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0118(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0118(p) < _vnum_v0118(__file__)), key=_vnum_v0118)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100, V0115 = PRIOR.V0100, PRIOR.V0115


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


CMD_FN_V0118 = r'''

def _vdf_cmd():
    # v0118:原始命令列(sys.orig_argv;runpy.run_path 改不到)→ [腳本或 -c / -m 標記, 參數…];沒有才退回 sys.argv。
    oa = [str(a) for a in (getattr(sys, "orig_argv", None) or [])]
    i = 1
    while i < len(oa):
        a = oa[i]
        if a == "-c":
            return ["-c"] + oa[i + 2:]
        if a == "-m":
            return ["-m"] + oa[i + 1:]
        if a in ("-X", "-W", "-Q"):
            i += 2
            continue
        if a.startswith("-") and len(a) > 1:
            i += 1
            continue
        return oa[i:]
    return [str(a) for a in (getattr(sys, "argv", None) or [""])]
'''
OLD_ID = '''    argv = [str(a) for a in (getattr(sys, "argv", None) or [""])]
    head = os.path.basename(argv[0]) if argv else ""
    boss = head.startswith(("VDF_SystemManager", "VDF_MDL013_ActivateVDF", "ActivateVDF"))
    rec = {"pid": os.getpid(), "argv": (" ".join(os.path.basename(a) if i == 0 else a for i, a in enumerate(argv[:3])))[-160:],'''
NEW_ID = '''    argv = _vdf_cmd()
    head = os.path.basename(argv[0]) if argv else ""
    boss = head.startswith(("VDF_SystemManager", "VDF_MDL013_ActivateVDF", "ActivateVDF"))
    rec = {"pid": os.getpid(), "argv": (" ".join(os.path.basename(a) if (i == 0 or "/" in a or "\\\\" in a) else a
                                                 for i, a in enumerate(argv[:3])))[-160:],'''


def mem_snippet_v0118() -> str:
    s = PRIOR.MEM_SNIPPET_V0117
    if OLD_ID not in s:
        raise RuntimeError("v0117 准入閘原文對不上(認人那幾行)")
    s = s.replace(OLD_ID, NEW_ID, 1)
    anchor = "\n\ndef _vdf_mem_admit():"
    return s.replace(anchor, CMD_FN_V0118.rstrip("\n") + anchor, 1)


MEM_SNIPPET_V0118 = mem_snippet_v0118()
HOOK_SRC_V0118 = PRIOR.hook_src_v0117(PRIOR._ORIG["HOOK_SRC_V0115"]).replace(PRIOR.MEM_SNIPPET_V0117.rstrip("\n"), MEM_SNIPPET_V0118.rstrip("\n"), 1)
_V0114_G = PRIOR._V0114_G
_ACTIVATE_V0117 = PRIOR.activate
_TAG_V0117 = PRIOR.TAG
RETIRE_GLOB_V0118 = "VDF_LaunchRetire_SSOT_v*.json"


def _chain_v0118() -> list:
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = vars(m).get("PRIOR")
    return out


_IDS_OWNER = next(m for m in _chain_v0118() if "_ENGINE_LIST_CARD" in vars(m))     # v0102:engine_ids 本體 + 名單卡
_ENGINE_IDS_PRIOR = _IDS_OWNER.engine_ids
_IDS_HOLDERS = [m for m in _chain_v0118() + [V0100] if vars(m).get("engine_ids") is _ENGINE_IDS_PRIOR]


def launch_retire_book(folder: Path = HERE) -> dict:
    """啟動退役冊尾版 → {file, families{家族: 列}, error}。冊不在 = 空(照前版全啟動)。"""
    hits = [p for p in Path(folder).glob(RETIRE_GLOB_V0118) if _vnum_v0118(p) >= 0]
    if not hits:
        return {"file": None, "families": {}, "error": None}
    p = max(hits, key=_vnum_v0118)
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        fams = {r["family"]: r for r in d.get("families") or [] if isinstance(r, dict) and r.get("family")}
        return {"file": p.name, "families": fams, "error": None}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"file": p.name, "families": {}, "error": "%s: %s" % (type(exc).__name__, str(exc)[:120])}


def apply_retire(keep: list, skip: list, book: dict) -> tuple:
    out, gone = [], []
    for fam in keep:
        r = book["families"].get(fam)
        if r:
            gone.append(fam)
            skip.append({"eid": fam.split("_")[1] if fam.count("_") >= 2 else fam, "family": fam,
                         "path": "退役(%s · %s · %s):%s" % (r.get("since") or "—", r.get("by") or "—", book["file"], r.get("why") or "")})
        else:
            out.append(fam)
    return out, skip, gone


def engine_ids(env: dict, log_dir: Path, manager: Path | None = None, py: str | None = None) -> tuple:
    """同 v0102 engine_ids;再照啟動退役冊把冊上的家族移到「已被取代 / 退役」(不啟動 · 不計分母)。"""
    keep, skip = _ENGINE_IDS_PRIOR(env, log_dir, manager, py)
    book = launch_retire_book()
    keep, skip, gone = apply_retire(list(keep), list(skip), book)
    card = _IDS_OWNER._ENGINE_LIST_CARD
    if card:
        card.update(n=len(keep), skipped=len(skip), retired=gone, retire_book=book["file"], retire_error=book["error"])
    if gone or book["error"]:
        PRIOR._say("  [退役] 照 %s 不啟動 %d 支:%s%s" % (book["file"], len(gone), " · ".join(gone) or "—",
                                                     (" · 冊讀不了:" + book["error"]) if book["error"] else ""))
    return keep, skip


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0117 activate;本輪鉤用 v0118 准入閘(認人看原始命令列);總覽標本版。"""
    keep = (V0115.HOOK_SRC_V0115, PRIOR.TAG)
    V0115.HOOK_SRC_V0115, PRIOR.TAG = HOOK_SRC_V0118, TAG
    for m in _IDS_HOLDERS:
        m.engine_ids = engine_ids
    try:
        return _ACTIVATE_V0117(opt, manager, py, temp)
    finally:
        V0115.HOOK_SRC_V0115, PRIOR.TAG = keep
        for m in _IDS_HOLDERS:
            m.engine_ids = _ENGINE_IDS_PRIOR


def _patch_v0118() -> None:
    _V0114_G["activate"] = activate


def _unpatch_v0118() -> None:
    _V0114_G["activate"] = _ACTIVATE_V0117


_patch_v0118()


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    PRIOR.PRIOR._patch_v0116()
    PRIOR._patch_v0117()
    _patch_v0118()
    return V0115.main(argv)


def selftest() -> int:
    import shutil
    import subprocess
    import tempfile
    import time
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s · 薄尾自測(准入閘認人看原始命令列;沙盒 · 零網路)===" % TAG)
    try:
        compile(HOOK_SRC_V0118, "sitecustomize.py", "exec")
        ok_c = True
    except SyntaxError as exc:
        ok_c = exc
    chk("① 本輪鉤可編譯 · 只換了認人那幾行 + 多一個 _vdf_cmd · 其餘與 v0117 一字不差",
        ok_c is True and "_vdf_cmd()" in HOOK_SRC_V0118 and HOOK_SRC_V0118.replace(MEM_SNIPPET_V0118.rstrip("\n"), "")
        == PRIOR.HOOK_SRC_V0117.replace(PRIOR.MEM_SNIPPET_V0117.rstrip("\n"), ""), ok_c)
    tmp = Path(tempfile.mkdtemp(prefix="vdf_act0118_"))
    try:
        rows = {}
        for ver, src in (("v0117", PRIOR.HOOK_SRC_V0117), ("v0118", HOOK_SRC_V0118)):
            hook = tmp / ver / "pyhook"
            hook.mkdir(parents=True)
            (hook / "sitecustomize.py").write_text(src, encoding="utf-8")
            central = tmp / ver / "central"                                  # 模擬工作站中央啟動鉤:runpy.run_path 接力跑本輪鉤
            central.mkdir()
            (central / "sitecustomize.py").write_text(
                "import runpy\nrunpy.run_path(%r, run_name='sitecustomize_after_vdf')\n" % str(hook / "sitecustomize.py"), encoding="utf-8")
            log = tmp / ver / "mem.jsonl"
            base = {k: v for k, v in os.environ.items() if not k.startswith(("VIA_VDF_", "VIA_DUCK"))}
            base.update(PYTHONPATH=str(central), VIA_VDF_MEM_LOG=str(log), VIA_VDF_TOOLS="0", VIA_DUCK_TEMP="0", PYTHONIOENCODING="utf-8",
                        VIA_VDF_MEM_FLOOR_MB=str(10 ** 9), VIA_VDF_MEM_ADMIT_MAX_S="1.2")
            boss = tmp / ver / "VDF_SystemManager_v9999.py"
            boss.write_text("print('boss')\n", encoding="utf-8")
            eng = tmp / ver / "VDF_ENG998_Big_v0100.py"
            eng.write_text("print('eng')\n", encoding="utf-8")
            t = {}
            for name, cmd in (("boss", [sys.executable, str(boss), "engine", "list"]),
                              ("eng", [sys.executable, "-X", "utf8", str(eng), "--selftest"]),
                              ("probe", [sys.executable, "-c", "import sys;print('probe')", str(eng)])):
                t0 = time.time()
                subprocess.run(cmd, env=base, capture_output=True, text=True, timeout=60)
                t[name] = round(time.time() - t0, 2)
            got = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()] if log.is_file() else []
            rows[ver] = (t, got)
        t7, r7 = rows["v0117"]
        t8, r8 = rows["v0118"]
        chk("② 重現工作站:中央鉤 runpy 接力時 v0117 收據一律記成 sitecustomize.py · 指揮行程也去排隊(%.1f 秒)" % t7["boss"],
            len(r7) == 3 and all(x["argv"].startswith("sitecustomize.py") for x in r7) and not r7[0]["boss"] and t7["boss"] >= 1.0,
            [x["argv"] for x in r7])
        chk("③ 本版:指揮行程認得出 → 不等(%.2f 秒)· 收據記 VDF_SystemManager_v9999.py engine list" % t8["boss"],
            len(r8) == 3 and r8[0]["boss"] and r8[0]["argv"] == "VDF_SystemManager_v9999.py engine list" and t8["boss"] < 1.0, r8[:1])
        chk("④ 本版:引擎自測(帶 -X utf8 直譯器選項)收據記 VDF_ENG998_Big_v0100.py --selftest · 照樣排隊(%.1f 秒)" % t8["eng"],
            r8[1]["argv"] == "VDF_ENG998_Big_v0100.py --selftest" and not r8[1]["boss"] and r8[1]["wait_s"] >= 1.0, r8[1:2])
        chk("⑤ 本版:載入探針 python -c 記成「-c VDF_ENG998_Big_v0100.py」(看得出是哪支引擎)",
            r8[2]["argv"] == "-c VDF_ENG998_Big_v0100.py" and not r8[2]["boss"], r8[2:3])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    real = launch_retire_book()
    r70 = real["families"].get("VDF_ENG070_GroupClassificationIndex") or {}
    chk("⑧ 啟動退役冊在倉:%s · ENG070 在冊(since %s · by %s)· 寫明原因與「檔不刪不搬」的理由" % (real["file"], r70.get("since"), r70.get("by")),
        real["file"] == "VDF_LaunchRetire_SSOT_v0100.json" and r70.get("by") == "operator" and "逾時" in (r70.get("why") or "")
        and r70.get("files_kept_because"), real)
    keep, skip, gone = apply_retire(["VDF_ENG069_A", "VDF_ENG070_GroupClassificationIndex", "VDF_ENG071_GroupBacktest"],
                                    [{"eid": "MDL001", "family": "VDF_MDL001_X_v0100R", "path": "_rebuilds_superseded/x.py"}], real)
    chk("⑨ 照冊退役:ENG070 移到「已被取代 / 退役」(原因寫在 path 欄)· ENG071 照常啟動 · 原有的已取代照留",
        keep == ["VDF_ENG069_A", "VDF_ENG071_GroupBacktest"] and gone == ["VDF_ENG070_GroupClassificationIndex"] and len(skip) == 2
        and skip[-1]["family"] == "VDF_ENG070_GroupClassificationIndex" and "退役" in skip[-1]["path"] and "逾時" in skip[-1]["path"], skip)
    tmpd = Path(tempfile.mkdtemp(prefix="vdf_retire_"))
    try:
        none = launch_retire_book(tmpd)
        (tmpd / "VDF_LaunchRetire_SSOT_v0100.json").write_text("{壞", encoding="utf-8")
        bad = launch_retire_book(tmpd)
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
    k2, _s2, g2 = apply_retire(["VDF_ENG070_GroupClassificationIndex"], [], none)
    chk("⑩ 冊不在 → 照前版全啟動 · 冊壞 → 不退役任何一支並記錯(不擋啟動)", k2 == ["VDF_ENG070_GroupClassificationIndex"] and not g2
        and not bad["families"] and bad["error"], (none, bad))
    chk("⑪ engine_ids 換裝只在一輪裡:平時 v0100 / v0102 的 engine_ids 仍是前版(前版自測照舊)",
        all(vars(m).get("engine_ids") is _ENGINE_IDS_PRIOR for m in _IDS_HOLDERS) and len(_IDS_HOLDERS) >= 2, [m.__name__ for m in _IDS_HOLDERS])
    chk("⑥ 換裝在位:main 叫的 activate = 本版", _V0114_G["activate"] is activate)
    me = Path(__file__).read_text(encoding="utf-8")
    body = me.split("def selftest", 1)[0]
    chk("⑦ VDF 獨立:不匯入他系統程式 · 兩座橋在 · 同意閘不讀不寫 · 不碰 TA-Lib",
        not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC|talib)", me, re.M) and "VIA:ACCEL-BRIDGE" in me and "VIA:NET-BRIDGE" in me
        and "_CONSENT" not in body)
    if f:
        print("[計] %s 自測 %d/%d · FAIL" % (TAG, p, p + f))
        return 1
    print("[計] %s 本版 %d/%d · PASS" % (TAG, p, p + f))
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        return 0
    _unpatch_v0118()
    try:
        rc1 = PRIOR.selftest()
    finally:
        _patch_v0118()
    print("[計] %s 前版鏈 rc %s · %s" % (TAG, rc1, "PASS" if rc1 == 0 else "FAIL"))
    return rc1 if rc1 in (0, 1, 2, 3) else 1


if __name__ == "__main__":
    raise SystemExit(main())
