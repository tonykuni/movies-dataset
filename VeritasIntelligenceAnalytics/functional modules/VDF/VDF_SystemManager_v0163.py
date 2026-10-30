#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_SystemManager v0163 — 薄尾:前版鏈自測在 Windows 一般帳號跑得完(v0151 布置「舊接點」改走目錄接點 mklink /J,同正式 db move)

工作站實錄(2026-10-21,vdf-main 工作樹,收據 docs/handoff/evidence/vdf_ws_manager_design.txt):
  `via-vcgc handoff test vdf_ws_manager_design` → 管理員全鏈自測一路到 v0151.selftest 第 458 行
  `os.symlink(home, point, target_is_directory=True)` 就崩:OSError [WinError 1314] 用戶端沒有這項特殊權限。
  Windows 建符號連結要「建立符號連結」特權(系統管理員或開發人員模式);操作員的一般帳號沒有 → 整條鏈之後的自測全沒跑,
  凡是指令 `VDF_SystemManager --selftest` 的交接案(16 案)在工作站一律紅。CI 的 Windows runner 是管理員,所以 CI 綠、工作站紅。
  正式功能沒這個問題:v0151 的 db move 切接點在 Windows 本來就走 `cmd /c mklink /J`(目錄接點,一般帳號就能建),只有自測布置那一步直呼 os.symlink。
本版(其餘全照 v0162;版面 · 功能 · 燈 · 動詞一行不動):
  ① 自測跑前版鏈那一段,把 v0151 模組看到的 `os` 換成代理:目錄連結 → link_dir()(Windows = mklink /J,同 db move;其他 = 符號連結),
     其餘屬性(path · name · environ · rmdir …)全部原樣轉給真的 os;跑完(含例外)還原。v0151 的檔一個字不改。
  ② Windows 上一律走目錄接點(不先試符號連結):CI 的管理員帳號與工作站的一般帳號驗的是同一條路。
入口 · 同意閘 · 零網路 · 不碰 TA-Lib · 不載入他系統程式:照 v0162。本檔唯一的子行程是 Windows 上的 mklink /J(只在自測布置接點時)。
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


import contextlib
import importlib.util
import os
import re
import subprocess
import sys
import types
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
TAG = "v0163"
SELF_ID = "VDF"
LINK_OWNER_TAG_V0163 = "v0151"                  # 自測布置舊接點直呼 os.symlink 的那一版


def _vnum_v0163(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0163(path: Path, name: str):
    """同 v0162 的載入器:載入那一刻擋掉前版的編譯警告(SyntaxWarning / DeprecationWarning);前版的字一個不改。"""
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            warnings.simplefilter("ignore", DeprecationWarning)
            spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0163(p) < _vnum_v0163(__file__)), key=_vnum_v0163)
PRIOR = _load_v0163(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain_v0163() -> list:
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = getattr(m, "PRIOR", None)
    return out


def link_owners_v0163() -> list:
    """鏈上 TAG v0151、自己有 db_move · _is_link · selftest 的那一版(依 PRIOR 一路找;同一份檔另被載過的也一併換)。"""
    out = [m for m in _chain_v0163() if getattr(m, "TAG", None) == LINK_OWNER_TAG_V0163
           and all(k in vars(m) for k in ("db_move", "_is_link", "selftest"))]
    if out:
        f0 = Path(out[0].__file__).resolve()
        for m in list(sys.modules.values()):
            f = getattr(m, "__file__", None)
            if isinstance(m, types.ModuleType) and m not in out and f and Path(f).resolve() == f0:
                out.append(m)
    return out


def link_dir(src, dst, nt=None, run=None, symlink=None) -> str:
    """目錄連結 dst → src。Windows:目錄接點 `cmd /c mklink /J <dst> <src>`(同 v0151 db move 切接點那條,一般帳號免特權);
    其他:符號連結。mklink 失敗照拋 OSError(不吞;讓自測照實紅)。回 "junction" / "symlink"。"""
    nt = (os.name == "nt") if nt is None else nt
    if nt:
        r = (run or subprocess.run)(["cmd", "/c", "mklink", "/J", str(dst), str(src)], capture_output=True, text=True)
        if r.returncode != 0:
            raise OSError("mklink /J 失敗(rc %s):%s" % (r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()[:200]))
        return "junction"
    (symlink or os.symlink)(src, dst, target_is_directory=True)
    return "symlink"


def os_proxy_v0163(nt=None, run=None) -> types.ModuleType:
    """給 v0151 模組看的 os:symlink(目錄)→ link_dir;其餘屬性一律轉給真的 os(同一個物件,環境變數改動照樣共用)。"""
    proxy = types.ModuleType("os_proxy_v0163")

    def _fwd(name):
        return getattr(os, name)

    def symlink(src, dst, target_is_directory=False, **kw):
        if target_is_directory and not kw:
            link_dir(src, dst, nt=nt, run=run)
            return None
        return os.symlink(src, dst, target_is_directory, **kw)

    proxy.__getattr__ = _fwd                    # PEP 562:模組層 __getattr__
    proxy.symlink = symlink
    return proxy


@contextlib.contextmanager
def junction_window(owners=None, nt=None, run=None):
    """這段期間 v0151 模組的 os 換成代理;結束(含例外)換回原來那個 os。"""
    owners = link_owners_v0163() if owners is None else owners
    keep = [(m, vars(m).get("os")) for m in owners]
    proxy = os_proxy_v0163(nt, run)
    for m, _ in keep:
        m.os = proxy
    try:
        yield proxy
    finally:
        for m, k in keep:
            m.os = k


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
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

    print("=== %s %s · 薄尾自測(前版鏈的接點布置在 Windows 一般帳號也跑得完)===" % (_STEM, TAG))
    owners = link_owners_v0163()
    o151 = owners[0] if owners else None
    src151 = Path(o151.__file__).read_text(encoding="utf-8") if o151 else ""
    chk("① 主人找得到:鏈上 TAG v0151 · 有 db_move / _is_link / selftest · 它的自測正是直呼 os.symlink 布置舊接點(要修的那一步)· 正式 db move 在 Windows 已走 mklink /J",
        o151 is not None and o151.TAG == "v0151" and "os.symlink(home, point, target_is_directory=True)" in src151
        and '"mklink", "/J"' in src151 and vars(o151).get("os") is os, (len(owners), getattr(o151, "TAG", None)))
    calls, links = [], []

    class _R:
        def __init__(self, rc, out=""):
            self.returncode, self.stdout, self.stderr = rc, out, ""

    def fake_run(args, **kw):
        calls.append(list(args))
        return _R(0)

    def fake_symlink(s, d, target_is_directory=False):
        links.append((str(s), str(d), target_is_directory))
    k1 = link_dir("C:\\home\\output_hub", "C:\\repo\\output_hub", nt=True, run=fake_run, symlink=fake_symlink)
    nt_ok = k1 == "junction" and calls == [["cmd", "/c", "mklink", "/J", "C:\\repo\\output_hub", "C:\\home\\output_hub"]] and not links
    k2 = link_dir("/h/out", "/r/out", nt=False, run=fake_run, symlink=fake_symlink)
    px_ok = k2 == "symlink" and links == [("/h/out", "/r/out", True)] and len(calls) == 1
    try:
        link_dir("a", "b", nt=True, run=lambda a, **kw: _R(1, "拒絕存取"), symlink=fake_symlink)
        bad_ok = False
    except OSError as exc:
        bad_ok = "mklink /J" in str(exc) and "拒絕存取" in str(exc)
    chk("② link_dir:Windows → cmd /c mklink /J <連結> <目標>(不試符號連結)· 其他 → 符號連結(目錄)· mklink 失敗照拋 OSError(不吞)",
        nt_ok and px_ok and bad_ok, (calls, links, bad_ok))
    probe = types.ModuleType("vdf_sm163_probe")
    probe.os = os
    real_symlink, seen = os.symlink, []
    os.symlink = lambda s, d, t=False, **kw: seen.append((s, d, t))
    try:
        with junction_window([probe], nt=True, run=fake_run) as px:
            inside = (probe.os is px and px.path is os.path and px.environ is os.environ and px.name == os.name
                      and px.rmdir is os.rmdir and px.sep == os.sep)
            px.symlink("t", "l")                                   # 非目錄 → 原樣交給真的 os.symlink
            px.symlink("D:\\t", "D:\\l", target_is_directory=True)  # 目錄 → 接點
        try:
            with junction_window([probe], nt=True, run=fake_run):
                raise RuntimeError("x")
        except RuntimeError:
            pass
    finally:
        os.symlink = real_symlink
    chk("③ 代理:窗內 v0151 看到的 os 是代理(path · environ · name · rmdir · sep 都是真 os 的同一物件)· 非目錄連結原樣交給 os.symlink ·"
        " 目錄連結走 mklink /J · 窗外(含例外)換回真的 os",
        inside and seen == [("t", "l", False)] and calls[-1] == ["cmd", "/c", "mklink", "/J", "D:\\l", "D:\\t"] and probe.os is os,
        (inside, seen, calls[-1:]))
    td = Path(tempfile.mkdtemp(prefix="vdfsm163-"))
    try:
        tgt, lnk = td / "home" / "output_hub", td / "repo" / "output_hub"
        tgt.mkdir(parents=True)
        lnk.parent.mkdir()
        (tgt / "a.txt").write_text("x", encoding="utf-8")
        kind = link_dir(tgt, lnk)
        seen_ok = (o151 is not None and o151._is_link(lnk) and Path(os.path.realpath(lnk)).resolve() == tgt.resolve()
                   and (lnk / "a.txt").read_text(encoding="utf-8") == "x")
        if os.name == "nt":
            os.rmdir(lnk)                                         # 只拆接點本身(同 v0151 db move)
        else:
            lnk.unlink()
        gone_ok = not os.path.lexists(lnk) and (tgt / "a.txt").is_file()
        chk("④ 本機真跑一遍(%s):link_dir 建的連結 v0151 的 _is_link 認得 · 解到真址 · 讀得到檔 · 拆連結不動目標資料" % kind,
            kind == ("junction" if os.name == "nt" else "symlink") and seen_ok and gone_ok, (kind, seen_ok, gone_ok))
    finally:
        shutil.rmtree(td, ignore_errors=True)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 橋在(__future__ 之後)· 不碰 TA-Lib · 不代設同意閘 · 不載入 VCGC 程式 · 零網路 · 子行程只有 mklink /J 一處 · 不寫冊 · v0151 正本不改(只在自測窗內換它看到的 os)",
        all(x in body for x in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]")) and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:v0100]")
        and "import " + "talib" not in body and 'environ["VIA_NET_' + 'CONSENT"] = "' not in body and "CGC_MDL" + "1" not in body
        and "url" + "lib" not in body and "req" + "uests" not in body and body.count("subprocess." + "run") == 1
        and not re.search(r"^def (typekit_|design_|ui_|db_|engine_)", body, re.M))
    print("  ── 前版鏈自測(v0151 看到的 os 換成代理;原樣印出;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    skipped, saw = os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1", []
    if skipped:
        prc = 0
    else:
        keep_st = o151.selftest if o151 is not None else None

        def spy():
            saw.append(isinstance(vars(o151).get("os"), types.ModuleType) and vars(o151)["os"] is not os
                       and getattr(vars(o151)["os"], "symlink", None) is not os.symlink)
            return keep_st()
        if o151 is not None:
            o151.selftest = spy
        try:
            with junction_window(owners):
                prc = PRIOR.selftest()
        finally:
            if o151 is not None:
                o151.selftest = keep_st
    chk("⑥ 前版鏈 %s 自測 rc 0 · v0151 自測開跑那一刻看到的 os 是代理(布置舊接點走 link_dir)· 跑完換回真的 os" % PRIOR_PATH.stem,
        prc == 0 and (skipped or saw == [True]) and (o151 is None or vars(o151).get("os") is os), (prc, saw))
    print("[計] %s_%s 自測 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
