#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_VCGC_ApplyRun v0101 — 薄尾:R 道(全景三回修正)多一步「SafeRepair 唯讀全景」

操作員 2026-11-20 16:26:「上傳為 VCGC 節省 TOKEN 工具全景修復流」(附 VCGC_SafeRepair_v0100.zip)。
包原樣存在倉根 claude-deliveries/VCGC_SafeRepair_v0100.zip(位元組不改;本檔釘它的 SHA-256)。本版只做三件事:
  ① 核對包的 SHA-256 → 解到倉外(Windows %LOCALAPPDATA%\\VIA\\SafeRepair\\v0100;其他 ~/.via_saferepair/v0100)。
     解包前檢查每個路徑(不准絕對路徑、不准 ..);已解過且標記檔的雜湊相同就不重解。
  ② R 道第一回的 SDD 之後加一步:SafeRepair scan(整個 VIA 夾 · 輸出在倉外 · 候選最多 10 個 · 只產候選與 diff,不改倉內任何檔)。
     它結束碼 2 = REVIEW(有待查項)→ 照前版規則算黃。
  ③ 包不在、雜湊不對、解包被拒 → 那一步照實紅並寫原因,不跑。
其餘(S / C / E / G 道、判燈、道數、越界還原、輸出)全部照 v0100。SafeRepair 的工具本身(VCGC_SafeRepair.py 與它的 runtime)不改。

用法同 v0100:run [--only S,C,E,G,R] [--lanes N] [--no-open] · plan · --selftest
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
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_VCGC_ApplyRun"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path() -> Path:
    me = _vnum(__file__)
    return max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < me), key=_vnum)


PRIOR_PATH = _prior_path()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

VERSION = "v0101"
TAG = "VIA_VCGC_ApplyRun " + VERSION
SR_ZIP = "claude-deliveries/VCGC_SafeRepair_v0100.zip"
SR_SHA = "08b27ffe61b4d199e5df8b729af21686d0570ffd69e54cfd880ff74289a31a60"
SR_DIR = "v0100"


def __getattr__(name):
    return getattr(PRIOR, name)


def sr_home() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    return (Path(base) / "VIA" / "SafeRepair") if base else (Path.home() / ".via_saferepair")


def sr_stage(via: Path, zpath: Path | None = None, expect: str = SR_SHA, home: Path | None = None) -> tuple[Path | None, str]:
    """核對包 → 解到倉外。回 (VCGC_SafeRepair.py 路徑 或 None, 說明)。"""
    zpath = zpath or (via.parent / SR_ZIP)
    home = home or sr_home()
    if not zpath.is_file():
        return None, "包不在:%s(PR 合併後才有)" % zpath
    raw = zpath.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != expect:
        return None, "包的 SHA-256 不對(%s…,本檔釘 %s…),不解不跑" % (got[:12], expect[:12])
    dest = home / SR_DIR
    mark = dest / ".via_stage_sha256"
    tool = dest / "VCGC_SafeRepair.py"
    if mark.is_file() and mark.read_text(encoding="utf-8").strip() == got and tool.is_file():
        return tool, "已解在 %s(雜湊相同,沿用)" % dest
    try:
        with zipfile.ZipFile(zpath) as z:
            names = z.namelist()
            bad = [n for n in names if n.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", n) or ".." in re.split(r"[\\/]", n)]
            if bad:
                return None, "包裡有不安全的路徑 %d 個(例 %s),不解" % (len(bad), bad[0])
            dest.mkdir(parents=True, exist_ok=True)
            z.extractall(dest)
    except (OSError, zipfile.BadZipFile) as e:
        return None, "解包失敗:%s" % type(e).__name__
    if not tool.is_file():
        return None, "包裡沒有 VCGC_SafeRepair.py"
    mark.write_text(got + "\n", encoding="utf-8")
    return tool, "已解到 %s" % dest


def plan(via: Path, only: list[str]):
    g, notes = _PRIOR_PLAN(via, only)
    if "R" in g:
        tool, why = sr_stage(via)
        out = sr_home()
        step = PRIOR.Step("R", "R1-saferepair", tool, ["scan", "--repo", str(via.parent), "--scope", "VeritasIntelligenceAnalytics", "--out", str(out), "--candidates", "10"], 1800)
        if tool is None:
            notes.append("[R] SafeRepair 沒跑:" + why)
        else:
            notes.append("[R] SafeRepair " + why + " · 輸出在倉外 " + str(out) + "(summary.json · findings.json · candidates/ · diffs/;不改倉內檔)")
        names = [s.name for s in g["R"]]
        at = names.index("R1-sdd") + 1 if "R1-sdd" in names else len(names)
        g["R"].insert(at, step)
    return g, notes


_PRIOR_PLAN = PRIOR.plan
PRIOR.plan = plan   # run() 走前版,但計畫用本版(前版原本那支留在 _PRIOR_PLAN)
PRIOR.VERSION, PRIOR.TAG = VERSION, TAG


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    print("=== %s 薄尾自測(暫存夾;前版鏈另跑)===" % TAG)
    with tempfile.TemporaryDirectory(prefix="via_applyrun101_") as td:
        t = Path(td)
        good = t / "pkg.zip"
        with zipfile.ZipFile(good, "w") as z:
            z.writestr("VCGC_SafeRepair.py", "print('fake')\n")
            z.writestr("runtime/x.txt", "x")
        sha = hashlib.sha256(good.read_bytes()).hexdigest()
        tool, why = sr_stage(t, good, sha, t / "home")
        chk("① 包雜湊對 → 解到指定的倉外夾 · 寫標記", tool is not None and tool.read_text() == "print('fake')\n" and (t / "home" / SR_DIR / ".via_stage_sha256").is_file(), why)
        tool2, why2 = sr_stage(t, good, sha, t / "home")
        chk("② 已解過、雜湊相同 → 沿用不重解", tool2 == tool and "沿用" in why2, why2)
        n, w = sr_stage(t, good, "0" * 64, t / "home2")
        chk("③ 雜湊不對 → 不解不跑 · 說明原因", n is None and "SHA-256 不對" in w and not (t / "home2").exists(), w)
        evil = t / "evil.zip"
        with zipfile.ZipFile(evil, "w") as z:
            z.writestr("../escape.py", "x")
        n, w = sr_stage(t, evil, hashlib.sha256(evil.read_bytes()).hexdigest(), t / "home3")
        chk("④ 包裡有 .. 路徑 → 拒絕、零寫入", n is None and "不安全" in w and not (t / "escape.py").exists() and not (t / "home3").exists(), w)
        n, w = sr_stage(t, t / "none.zip", sha, t / "home4")
        chk("⑤ 包不在 → 照實說", n is None and "包不在" in w, w)
    via = PRIOR.find_via(HERE)
    if via is not None:
        me = sys.modules[__name__]
        keep = me.sr_stage
        me.sr_stage = lambda *a, **k: (Path("VCGC_SafeRepair.py"), "自測替身(不解包)")   # 自測不在倉外寫檔
        try:
            g, notes = plan(via, ["R"])
        finally:
            me.sr_stage = keep
        names = [s.name for s in g["R"]]
        chk("⑥ 真樹計畫:R 道有 R1-saferepair,排在 SDD 之後 · 輸出在倉外 · 說明寫進 notes",
            "R1-saferepair" in names and names.index("R1-saferepair") == names.index("R1-sdd") + 1
            and not str(sr_home()).startswith(str(via.parent)) and any("SafeRepair" in x for x in notes), names[:12])
    else:
        chk("⑥ 找不到 VIA 夾(這台不是倉):跳過 = 黃", False)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 加速器橋在 · 不碰 TA-Lib · 沒有色碼 · 前版的公開名稱都拿得到", "[VIA:ACCEL-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"#[0-9a-fA-F]{6}\b", src) and all(hasattr(sys.modules[__name__], n) for n in ("run", "sync", "Step", "omniroute", "find_via")))
    rc_prior = PRIOR.selftest()
    chk("⑧ 前版 %s 自測照過" % PRIOR_PATH.stem, rc_prior == 0, rc_prior)
    good_all = all(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if good_all else "FAIL", TAG, sum(ok), len(ok)))
    return 0 if good_all else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a == ["--selftest"]:
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
