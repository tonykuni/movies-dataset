#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_SystemManager v0162 — 薄尾:fetch 動詞不補套(資料動詞不產頁;36 支逐支啟動不再每支多跑一遍字級套件)· 載前版鏈壓掉前版的編譯警告

工作站實錄(操作員 2026-10-27,PowerShell,逐支 `python $M fetch run <代號> --apply --mode live --home …`):
  ① 每個 fetch 動詞(run / verify / status / list)跑完,v0153 的 main 都再對 VIA_Reports/vdf 直下的 *_latest.html 補一遍字級套件
     (fetch 不產頁,純白工;36 支 = 36 遍;操作員在 fetch status 收尾那段按了 Ctrl+C,traceback 停在 typekit_block)。
  ② 每次都印 VDF_SystemManager_v0155.py:6: SyntaxWarning: invalid escape sequence '\o'(v0155 說明字串裡的 VDF\output_hub;正本不改)。
本版(其餘全照 v0161;不動版面 · 功能 · 燈):
  ① main:args[0] == "fetch" → 這一輪把 v0153 的 typekit_dir 換成零動作替身(changed 0 · 說明「fetch 不產頁」),跑完(含例外)還原;
     其他動詞照舊補套(ui · db · engine … 會產頁)。
  ② 載前版鏈那一刻 warnings.catch_warnings 只擋 SyntaxWarning / DeprecationWarning(同 ActivateVDF v0102 的做法);本檔自己的原始碼
     沒有無效跳脫(自測驗);前版的字沒改。
入口 · 子行程 · 同意閘 · 零網路 · 不碰 TA-Lib · 不載入他系統程式:照 v0161。
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


import importlib.util
import os
import re
import sys
import types
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
TAG = "v0162"
SELF_ID = "VDF"
SKIP_TYPEKIT_VERBS_V0162 = ("fetch",)           # 資料動詞:不產頁 → 動詞後不補套


def _vnum_v0162(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0162(path: Path, name: str):
    """同 v0157 的載入器,只多一層:載入那一刻擋掉前版的編譯警告(SyntaxWarning / DeprecationWarning);前版的字一個不改。"""
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            warnings.simplefilter("ignore", DeprecationWarning)
            spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0162(p) < _vnum_v0162(__file__)), key=_vnum_v0162)
PRIOR = _load_v0162(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain_v0162() -> list:
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = getattr(m, "PRIOR", None)
    return out


def pass_owner_v0162():
    """動詞後補套那一行(typekit_dir(_out_dir()))住在 v0153 的 main;找鏈上 TAG v0153 且自己有 _out_dir · typekit_dir 的那一版。"""
    for m in _chain_v0162():
        if getattr(m, "TAG", None) == "v0153" and "_out_dir" in vars(m) and "typekit_dir" in vars(m):
            return m
    return None


_PASS_OWNER = pass_owner_v0162()


def skip_typekit(args) -> bool:
    return bool(args) and args[0] in SKIP_TYPEKIT_VERBS_V0162


def _no_pass_v0162(out_dir, tk=None) -> dict:
    return {"book": None, "why": "fetch 動詞不產頁 · 本輪不補套(v0162)", "rows": [], "changed": 0, "n": 0, "skipped": True}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    if skip_typekit(args) and _PASS_OWNER is not None:
        keep = _PASS_OWNER.typekit_dir
        _PASS_OWNER.typekit_dir = _no_pass_v0162
        try:
            return PRIOR.main(args)
        finally:
            _PASS_OWNER.typekit_dir = keep
    return PRIOR.main(args)


def selftest() -> int:
    import contextlib
    import io
    import shutil
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

    print("=== %s %s · 薄尾自測(fetch 不補套 · 前版編譯警告壓掉)===" % (_STEM, TAG))
    owner = _PASS_OWNER
    chk("① 補套那一行的主人找得到:鏈上 TAG v0153 · 有 _out_dir / typekit_dir · 它的 typekit_dir 現在是 v0154 換上的那份(本版不動它,只在 fetch 那一輪借位)",
        owner is not None and owner.TAG == "v0153" and callable(owner.typekit_dir) and getattr(owner.typekit_dir, "__name__", "") == "typekit_dir_v0154",
        getattr(getattr(owner, "typekit_dir", None), "__name__", None))
    calls = []
    keep_td = owner.typekit_dir

    def rec(out_dir, tk=None):
        calls.append(str(out_dir))
        return {"book": None, "why": "", "rows": [], "changed": 0, "n": 0}
    owner.typekit_dir = rec
    try:
        with contextlib.redirect_stdout(io.StringIO()) as o1:
            rc1 = main(["fetch", "list"])
        n_fetch = len(calls)
        with contextlib.redirect_stdout(io.StringIO()):
            rc2 = PRIOR.main(["fetch", "list"])
        n_prior = len(calls) - n_fetch
        with contextlib.redirect_stdout(io.StringIO()):
            rc3 = main(["zz_no_such_verb_v0162"])
        n_other = len(calls) - n_fetch - n_prior
        chk("② fetch 動詞經本版:跑完不補套(替身零動作 · 清單照印 · rc 0);同一個 fetch 直接走前版會補一遍(= 工作站每支多跑的那遍);非 fetch 動詞經本版照舊補套",
            rc1 == 0 and n_fetch == 0 and "總控" in o1.getvalue() and rc2 == 0 and n_prior == 1 and n_other == 1 and rc3 != 0 and owner.typekit_dir is rec,
            (rc1, n_fetch, rc2, n_prior, rc3, n_other))
        keep_main = PRIOR.main

        def boom(args):
            raise RuntimeError("x")
        PRIOR.main = boom
        try:
            try:
                main(["fetch", "run", "009"])
                raised = False
            except RuntimeError:
                raised = True
        finally:
            PRIOR.main = keep_main
        chk("③ fetch 那一輪炸掉也還原:typekit_dir 回到原來那份 · skip_typekit 只認 fetch(db / engine / 空參數不跳)· 替身回 changed 0 · skipped",
            raised and owner.typekit_dir is rec and skip_typekit(["fetch", "verify", "009"]) and not skip_typekit(["db", "check"])
            and not skip_typekit([]) and not skip_typekit(["--selftest"]) and _no_pass_v0162("/x")["changed"] == 0 and _no_pass_v0162("/x")["skipped"])
    finally:
        owner.typekit_dir = keep_td
    td = Path(tempfile.mkdtemp(prefix="vdfsm162_"))
    try:
        bad, bad2 = td / "probe_bad_escape_a.py", td / "probe_bad_escape_b.py"   # 兩個檔:同一檔第二次載會吃 __pycache__ 不再編譯
        for q in (bad, bad2):
            q.write_text('X = "VDF\\output_hub"\n', encoding="utf-8")      # 跟 v0155 一樣的無效跳脫 \o
        v0155 = HERE / "VDF_SystemManager_v0155.py"
        with warnings.catch_warnings(record=True) as w0:
            warnings.simplefilter("always")
            compile(v0155.read_text(encoding="utf-8"), str(v0155), "exec") if v0155.is_file() else None
        with warnings.catch_warnings(record=True) as w1:
            warnings.simplefilter("always")
            PRIOR._load_v0157(bad, "vdf_sm_probe_prior_loader_v0162")
        with warnings.catch_warnings(record=True) as w2:
            warnings.simplefilter("always")
            m2 = _load_v0162(bad2, "vdf_sm_probe_own_loader_v0162")
        with warnings.catch_warnings(record=True) as w3:
            warnings.simplefilter("always")
            compile(Path(__file__).read_text(encoding="utf-8"), str(Path(__file__)), "exec")
        n_syn = lambda ws: sum(1 for x in ws if "invalid escape" in str(x.message))   # noqa: E731 — 3.12+ SyntaxWarning · 3.11 DeprecationWarning,認訊息
        chk("④ 前版 v0155 本身編譯就有 SyntaxWarning(無效跳脫;正本不改)· 前版載入器載同樣的檔會印 · 本版載入器載同樣的檔零警告且模組照載 · 本檔自己零無效跳脫",
            (not v0155.is_file() or n_syn(w0) >= 1) and n_syn(w1) >= 1 and n_syn(w2) == 0 and getattr(m2, "X", None) == "VDF\\output_hub" and n_syn(w3) == 0,
            (n_syn(w0), n_syn(w1), n_syn(w2), n_syn(w3)))
    finally:
        for k in ("vdf_sm_probe_prior_loader_v0162", "vdf_sm_probe_own_loader_v0162"):
            sys.modules.pop(k, None)
        shutil.rmtree(td, ignore_errors=True)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 橋在(__future__ 之後)· 不碰 TA-Lib · 不代設同意閘 · 不載入 VCGC 程式 · 本檔不起子行程 · 零網路 · 不寫冊 · 版面 / 功能 / 燈的程式一行沒動(只有 main 與載入器)",
        all(x in body for x in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]")) and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:v0100]")
        and "import " + "talib" not in body and 'environ["VIA_NET_' + 'CONSENT"] = "' not in body and "CGC_MDL" + "1" not in body
        and "import " + "subprocess" not in body and "url" + "lib" not in body and "req" + "uests" not in body
        and not re.search(r"^def (typekit_|design_|ui_|db_|engine_)", body, re.M))
    print("  ── 前版鏈自測(原樣印出;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑥ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] %s_%s 自測 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
