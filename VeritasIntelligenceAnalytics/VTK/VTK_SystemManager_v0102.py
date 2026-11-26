#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VTK_SystemManager v0102 — 薄尾(v0101 · v0100 一字不動):drill 在 Windows 一般帳號也跑得起來。

主機實錄 2026-11-26 23:23:drill 與自測停在 os.symlink → WinError 1314(一般帳號沒有建符號連結的權限)。
本版:暫存樹的連結改成「能用哪種用哪種」,不需要系統管理員權限:
  夾 :符號連結 → junction(目錄連接點,Windows 免權限)→ 整夾複製
  檔 :符號連結 → 硬連結(同一顆磁碟)→ 複製
  清除時先逐一拆掉自己建的連結(只拆連結本身,不進去),再刪其餘,刪除永遠不會順著連結碰到真倉。
drill 摘要多印一行「連結法」各用了幾個。前版的 drill 在本版行程裡一律換成本版(前版自測也走得過)。
動詞同前版;drill 換成本版,其餘轉給 v0101。
"""
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
import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ENGINE = "VTK_SystemManager_v0102"
PRIOR_NAME = "VTK_SystemManager_v0101.py"
HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("VTK_SystemManager_v0101", HERE / PRIOR_NAME)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["VTK_SystemManager_v0101"] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE
VERBS = dict(PRIOR.VERBS, drill="系統獨立演練(拿掉 VCGC 的 CGC_*.py 後逐家載入;Windows 一般帳號用 junction / 硬連結)")


def _try_symlink(src: Path, dst: Path) -> None:
    os.symlink(str(src), str(dst), target_is_directory=src.is_dir())


def _try_junction(src: Path, dst: Path) -> None:
    import _winapi  # 只有 Windows 有;別的平台丟 ImportError → 走下一招
    _winapi.CreateJunction(str(src), str(dst))


class Linker:
    """把真倉的一項代入暫存樹。記下每個連結,清除時先拆連結。"""

    def __init__(self, symlink=_try_symlink, junction=_try_junction):
        self.symlink, self.junction = symlink, junction
        self.links, self.count = [], {"符號": 0, "junction": 0, "硬連結": 0, "複製": 0}

    def put(self, src: Path, dst: Path) -> None:
        try:
            self.symlink(src, dst)
            self.links.append(dst)
            self.count["符號"] += 1
            return
        except (OSError, NotImplementedError):
            pass
        if src.is_dir():
            try:
                self.junction(src, dst)
                self.links.append(dst)
                self.count["junction"] += 1
                return
            except (OSError, ImportError, AttributeError):
                pass
            shutil.copytree(str(src), str(dst), ignore=shutil.ignore_patterns("__pycache__"))
            self.count["複製"] += 1
            return
        try:
            os.link(str(src), str(dst))  # 硬連結:拆掉只少一個名字,真檔不動
            self.count["硬連結"] += 1
        except OSError:
            shutil.copy2(str(src), str(dst))
            self.count["複製"] += 1

    def unlink_all(self) -> int:
        bad = 0
        for p in reversed(self.links):
            try:
                if os.path.isdir(p) and not os.path.islink(p):
                    os.rmdir(p)  # junction:rmdir 只拆連接點本身
                else:
                    os.unlink(p)
            except OSError:
                bad += 1
        self.links = []
        return bad

    def note(self) -> str:
        return " · ".join("%s %d" % kv for kv in self.count.items())


def drill(c, linker: Linker = None) -> int:
    """暫存樹:VTK 整份複製(在哪都一樣),registry 拿掉 CGC_*.py,其餘一律代入(符號 → junction / 硬連結 → 複製)。"""
    lk = linker or Linker()
    last, tmp = c.latest(c.register()), Path(tempfile.mkdtemp(prefix="vtk_drill_"))
    home, regdir = c.home.resolve(), (c.via / "supportive modules" / "registry").resolve()

    def place(src: Path, dst: Path, top: bool = False):
        rs = src.resolve()
        if rs == home:
            shutil.copytree(str(src), str(dst), ignore=shutil.ignore_patterns("__pycache__", ".*"))
        elif src.is_dir() and (home.is_relative_to(rs) or regdir.is_relative_to(rs)):
            dst.mkdir(parents=True, exist_ok=True)
            for e in src.iterdir():
                if (top and e.name in (".git", "VIA_Reports")) or (rs == regdir and e.name.startswith("CGC_") and e.suffix == ".py"):
                    continue
                place(e, dst / e.name)
        else:
            lk.put(src, dst)

    res, cgc_left, left = [], [], 0
    try:
        root = tmp / c.via.name
        place(c.via, root, True)
        home2 = root / c.home.relative_to(c.via)
        cgc_left = [p.name for p in (root / "supportive modules" / "registry").glob("CGC_*.py")]
        for fam, r in sorted(last.items()):
            f = home2 / c.prm["tools_dir"] / fam / r["tail"]
            try:
                cp = subprocess.run([sys.executable, "-c", BASE.PROBE, str(f)], cwd=str(tmp), capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=c.prm["drill_timeout_s"],
                                    env=dict(os.environ, VIA_FROM_VTK="YES", PYTHONIOENCODING="utf-8"))
                ok = cp.returncode == 0
                acc = ok and json.loads(cp.stdout.strip().splitlines()[-1]).get("accel")
                why = "" if ok else (cp.stderr.strip().splitlines() or ["?"])[-1][:140]
            except subprocess.TimeoutExpired:
                ok, acc, why = False, False, "逾時 %ss" % c.prm["drill_timeout_s"]
            res.append(("GREEN" if ok and acc else "YELLOW" if ok else "RED", fam, r["code"],
                        "載入過 · 加速器在" if ok and acc else ("載入過但加速器載不到" if ok else why)))
    finally:
        left = lk.unlink_all()
        if left == 0:
            shutil.rmtree(str(tmp), ignore_errors=True)
    lamp = "RED" if any(x[0] == "RED" for x in res) or cgc_left else ("YELLOW" if any(x[0] != "GREEN" for x in res) else "GREEN")
    print("[VTK drill] %s · 應演練 %d · 已演練 %d · 略過 0 · 暫存樹裡 VCGC CGC_*.py = %d" % (lamp, len(last), len(res), len(cgc_left)))
    print("  連結法:%s%s" % (lk.note(), "" if not left else " · [黃] %d 個連結拆不掉,暫存夾留著不刪:%s" % (left, tmp)))
    for x in res:
        print("  %-6s %-11s %-14s %s" % x)
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[lamp]


# 前版的 drill 在本版行程裡一律換成本版(前版自測呼叫的是各自模組裡的 drill 名字)
PRIOR.drill = drill
BASE.drill = drill


def __getattr__(name):
    return getattr(PRIOR, name)


def selftest() -> int:
    res = []

    def chk(name, ok, extra=""):
        res.append(bool(ok))
        print("  [%s] %s%s" % ("過" if ok else "敗", name, "" if ok else " · " + str(extra)[:240]))

    with contextlib.redirect_stdout(io.StringIO()):
        rp = PRIOR.selftest()
    chk("① 直接前版 v0101 自測過(它的前版 v0100 也照跑;drill 走本版)", rp == 0)

    def no_symlink(src, dst):
        raise OSError(1314, "用戶端沒有這項特殊權限")

    tmp = Path(tempfile.mkdtemp(prefix="vtk_link_"))
    try:
        real = tmp / "real"
        (real / "d" / "inner").mkdir(parents=True)
        (real / "d" / "inner" / "keep.txt").write_text("keep", encoding="utf-8")
        (real / "f.txt").write_text("file", encoding="utf-8")
        out = tmp / "out"
        out.mkdir()
        lk = Linker(symlink=no_symlink, junction=lambda s, d: os.symlink(str(s), str(d), target_is_directory=True))
        lk.put(real / "d", out / "d")
        lk.put(real / "f.txt", out / "f.txt")
        chk("② 沒有符號連結權限(WinError 1314):夾改用 junction、檔改用硬連結", lk.count["junction"] == 1 and lk.count["硬連結"] == 1
            and (out / "d" / "inner" / "keep.txt").read_text(encoding="utf-8") == "keep" and (out / "f.txt").read_text(encoding="utf-8") == "file", lk.note())
        bad = lk.unlink_all()
        shutil.rmtree(str(out))
        chk("③ 清除先拆連結:真倉的夾與檔一個都沒少", bad == 0 and (real / "d" / "inner" / "keep.txt").is_file() and (real / "f.txt").is_file())

        def no_link(*a, **k):
            raise OSError(17, "跨磁碟")

        out.mkdir()
        lk2 = Linker(symlink=no_symlink, junction=no_symlink)
        keep_link, os.link = os.link, no_link
        try:
            lk2.put(real / "d", out / "d")
            lk2.put(real / "f.txt", out / "f.txt")
        finally:
            os.link = keep_link
        (out / "f.txt").write_text("changed", encoding="utf-8")
        chk("④ junction 與硬連結也不行:退到複製,改暫存樹不影響真倉", lk2.count["複製"] == 2 and (real / "f.txt").read_text(encoding="utf-8") == "file", lk2.note())
        lk2.unlink_all()
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)

    via = BASE.via_root()
    t2 = Path(tempfile.mkdtemp(prefix="vtk_selftest_"))
    try:
        src = Path(tempfile.mkdtemp(prefix="vtk_src_"))
        # 用前版自測的同一套假樹:兩家工具,一家不靠 VCGC、一家靠 CGC_*.py
        v = src / "VeritasIntelligenceAnalytics"
        reg = v / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        for f in [via / "supportive modules" / "VIA_SuperAccel_Module.py"] + sorted((via / "supportive modules").glob("SUP_MDL737_SuperAccelModule_v*.py")):
            shutil.copy2(str(f), str(v / "supportive modules"))
        bridge = Path(__file__).read_text(encoding="utf-8").split("# ===== [VIA:ACCEL-BRIDGE:v0100]", 1)[1].split("# ===== [VIA:ACCEL-BRIDGE:END] =====")[0]
        hdr = "# [VIA:ACCEL-BRIDGE:v0111]\n# ===== [VIA:ACCEL-BRIDGE:v0100]" + bridge + "# ===== [VIA:ACCEL-BRIDGE:END] =====\n"
        (reg / "AAA_Tool_v0100.py").write_text(hdr + "X = 1\n", encoding="utf-8")
        (reg / "CGC_MDL999_Dep_v0100.py").write_text("X = 1\n", encoding="utf-8")
        (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps(
            {"alpha": {"path": "VeritasIntelligenceAnalytics/supportive modules/registry/AAA_Tool_v0100.py"}}), encoding="utf-8")
        (v / "other").mkdir()
        (v / "other" / "x.txt").write_text("x", encoding="utf-8")
        home = v / "VTK"
        home.mkdir()
        pb = json.loads(BASE.tail(HERE, "VTK_Params").read_text(encoding="utf-8"))
        pb["params"].update({"extra_sources": {}, "extra_files": {}, "adapt": {}})
        BASE.write_json(home / "VTK_Params_v0101.json", pb)
        c = BASE.Ctx(home, v)
        with contextlib.redirect_stdout(io.StringIO()):
            PRIOR.sync(c, True)
        lk = Linker(symlink=no_symlink, junction=lambda s, d: os.symlink(str(s), str(d), target_is_directory=True))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r = drill(c, lk)
        o = buf.getvalue()
        chk("⑤ drill 在「沒有符號連結權限」下照跑:綠、CGC_*.py = 0、連結法列出 junction / 硬連結", r == 0 and "CGC_*.py = 0" in o
            and "junction" in o and lk.count["符號"] == 0 and lk.count["junction"] + lk.count["硬連結"] > 0, o)
        chk("⑥ 演練完真樹一個檔都沒少", (v / "other" / "x.txt").is_file() and (reg / "CGC_MDL999_Dep_v0100.py").is_file() and (reg / "AAA_Tool_v0100.py").is_file())
        shutil.rmtree(str(src), ignore_errors=True)
    finally:
        shutil.rmtree(str(t2), ignore_errors=True)
    chk("⑦ 加速器執行時真的載到", VIA_ACCEL is not None)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        main(["verbs", "--json"])
    chk("⑧ verbs --json 自報", set(json.loads(buf.getvalue())["verbs"]) == set(VERBS))
    ok = all(res)
    print("[selftest] %s · %d 敗 · %s" % ("GREEN" if ok else "RED", res.count(False), ENGINE))
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a and a[0] in ("--selftest", "selftest"):
        return selftest()
    if a and a[0] == "verbs":
        if "--json" in a[1:]:
            print(json.dumps({"system": "VTK", "entry": ENGINE, "verbs": VERBS}, ensure_ascii=False))
        else:
            for k, d in VERBS.items():
                print("  %-9s %s" % (k, d))
        return 0
    if a and a[0] == "drill":
        return drill(BASE.Ctx(HERE))
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
