#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VRN-2 SystemManager v0276 — 薄尾:extract 檔名的「下載副本時間戳」不當報告日期;平行子行程走本版。

容器實測(2026-11-16,24 份真 PDF)查到報告日期判錯 2 份:
  · 瑞基(4171,NR_未評等)-CTBC251208(20261006-122004).pdf → 判成 2026-10-06(同一份不帶時間戳的判 2025-12-08)
  · 華南投顧-3017-奇鋐-1141202(20261006-122001).pdf      → 判成 2026-10-06(民國 114-12-02 = 2025-12-02)
根因:檔名律先找 8 位數日期;檔名尾巴的「(YYYYMMDD-HHMMSS)」是下載 / 複製時加的時間戳,8 位數那一段搶在
6 位數(CTBC251208)與民國 7 位數(1141202)之前被當成報告日期。前面本來就有 8 位數日期的檔(CLST-6669 20251001(…))不受影響。
本版(前版 v0275 一字不動;只在 extract 期間換鏈上兩個名字,跑完還原):
  ① 檔名律先剝掉「(YYYYMMDD-HHMMSS)」再交給前版判;剝掉後沒有別的日期就照實留空,不拿時間戳充數。
     剝掉的時間戳另記在 filename.copy_stamp,不丟。
  ② v0271 的平行子行程是用 v0271 自己的檔起跑的,v0272 之後各版掛上的東西進不了子行程。
     本版在 extract 期間把子行程改成用本檔起跑(同一個動詞、同一份工作單),① 在平行與序跑都生效。
其餘(平行 extract · 引擎矩陣 · 作業系統檔案鎖 · HTML 顯示名)照前版。零網路 · 不碰 TA-Lib · 不讀寫同意閘。
號:前版 v0275(main);本版 v0276(動工前比過 本機 ∪ origin/main,v0276 是空號)。
用法同前版:python VRN_SystemManager_v0276.py extract --dir <夾> [--workers N] · 自測 python VRN_SystemManager_v0276.py --selftest
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
import contextlib
import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "v0276"
DISPLAY_NAME = "VRN-2 SystemManager"
FAMILY = "VRN_SystemManager"


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, "vrn_manager_prior_for_" + TAG)


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(PRIOR, name)


def _owner(name: str):
    m, seen = PRIOR, []
    while m is not None and m not in seen:
        if name in vars(m):
            return m
        seen.append(m)
        m = vars(m).get("PRIOR")
    return None


PAR = _owner("make_parallel")                      # 平行 extract 那一版(v0271):它用自己的檔起子行程
WORKER_VERB = getattr(PAR, "WORKER_VERB", "_extract_worker")


# ────────────────── ① 檔名:下載副本時間戳 ──────────────────
# 只認「(YYYYMMDD-HHMMSS)」這個形狀(括號 · 8 位日期 · 連字號 · 6 位時間);全形括號也算。別的括號內容不動。
_COPY_STAMP = re.compile(r"\s*[((](20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])-([01]\d|2[0-3])([0-5]\d)([0-5]\d)[))]")


def strip_copy_stamp(stem: str) -> tuple:
    """→ (剝掉時間戳的檔名, 時間戳或 None)。"""
    m = _COPY_STAMP.search(stem or "")
    if not m:
        return stem, None
    return _COPY_STAMP.sub("", stem).strip(), "%s-%s-%s %s:%s:%s" % m.groups()


def _wrap_parse(orig):
    def parse_filename(stem: str) -> dict:
        core, stamp = strip_copy_stamp(stem)
        out = orig(core)
        if stamp and isinstance(out, dict):
            out["copy_stamp"] = stamp
        return out
    parse_filename._vrn_v0276 = True
    return parse_filename


# ────────────────── ② 平行子行程走本版 ──────────────────
class _SubprocessVia:
    """只改一件事:v0271 起「擷取子行程」時,把它自己的檔換成本檔;其他呼叫原樣交給 subprocess。"""

    def __init__(self, real, old: Path, new: Path):
        self._real, self._old, self._new = real, Path(old).resolve(), Path(new).resolve()

    def __getattr__(self, name):
        return getattr(self._real, name)

    def rewrite(self, cmd):
        if isinstance(cmd, (list, tuple)) and len(cmd) >= 3 and cmd[2] == WORKER_VERB:
            try:
                same = Path(str(cmd[1])).resolve() == self._old
            except OSError:
                same = False
            if same:
                return [cmd[0], str(self._new)] + list(cmd[2:])
        return cmd

    def Popen(self, cmd, *a, **k):  # noqa: N802
        return self._real.Popen(self.rewrite(cmd), *a, **k)


@contextlib.contextmanager
def patched():
    """extract 期間換上 ① ②,跑完還原(前版鏈上的檔一個字都不改)。"""
    PRIOR.p27()                                                      # 讓擷取本體那條鏈先載好
    swapped = []
    for m in list(sys.modules.values()):
        f = Path(getattr(m, "__file__", "") or "").name
        fn = vars(m).get("parse_filename") if f.startswith(FAMILY + "_v") else None
        if callable(fn) and not getattr(fn, "_vrn_v0276", False):
            swapped.append((m, fn))
            m.parse_filename = _wrap_parse(fn)
    real_sp = vars(PAR).get("subprocess") if PAR is not None else None
    if real_sp is not None and not isinstance(real_sp, _SubprocessVia):
        PAR.subprocess = _SubprocessVia(real_sp, PAR.__file__, __file__)
    else:
        real_sp = None
    try:
        yield {"parse_owners": [Path(m.__file__).name for m, _ in swapped], "workers_via": Path(__file__).name if real_sp is not None else None}
    finally:
        for m, fn in swapped:
            m.parse_filename = fn
        if real_sp is not None:
            PAR.subprocess = real_sp


# ────────────────── 動詞 ──────────────────
def collect() -> dict:
    """VCGC 子系統對接口(照前版 · 只讀)· served_by 記本版。"""
    out = PRIOR.collect()
    if isinstance(out, dict):
        out = dict(out)
        sb = dict(out.get("served_by") or {})
        sb["tail"] = FAMILY + "_" + TAG
        out["served_by"] = sb
    return out


def provenance(args: list) -> int:
    """同前版:直送 ENG114 尾版;`--selftest` 之後再跑本版自測,回傳碼取大。"""
    h = PRIOR.host()
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    rc = int(h._load_engine(h.provenance_engine_path()).main(list(args)) or 0)
    if "--selftest" in args:
        print("  ── 來源回歸之後:本版管理器自測 ──", flush=True)
        rc = max(rc, int(selftest() or 0))
    return rc


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["provenance"]:
        return provenance(args[1:])
    if args == ["--selftest"] or "--selftest" in args[:1]:
        return selftest()
    if args[:1] in (["extract"], [WORKER_VERB]):
        with patched():
            return PRIOR.main(args)
    return PRIOR.main(args)


def selftest() -> int:
    print("[計] %s %s 自測開始(本版 6 項 · 再前版 %s)" % (DISPLAY_NAME, TAG, PRIOR_PATH.name), flush=True)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)
    s = strip_copy_stamp
    chk("F1 時間戳形狀:半形 / 全形括號都剝 · 時間戳另記 · 沒有的原樣",
        s("瑞基(4171,NR_未評等)-CTBC251208(20261006-122004)") == ("瑞基(4171,NR_未評等)-CTBC251208", "2026-10-06 12:20:04")
        and s("A-1101 20251001(20261006-052156)")[0] == "A-1101 20251001" and s("甲(20261006-052156)乙")[0] == "甲乙"
        and s("MS-2308 20251128") == ("MS-2308 20251128", None))
    chk("F2 不誤剝:公司(代號)· (二) · 月份 13 · 時 25 · 少一位 都不動",
        all(s(x) == (x, None) for x in ("神達(3706 TT)", "晨會報告(二)", "X(20261306-122004)", "X(20261006-252004)", "X(2026100-122004)")))
    with patched() as info:
        owners = [m for m in sys.modules.values() if getattr(vars(m).get("parse_filename"), "_vrn_v0276", False)]
        pf = owners[0].parse_filename if owners else None
        a = pf("瑞基(4171,NR_未評等)-CTBC251208(20261006-122004)") if pf else {}
        b = pf("華南投顧-3017-奇鋐-1141202(20261006-122001)") if pf else {}
        c = pf("CLST-6669 20251001(20261006-052156)") if pf else {}
        d = pf("瑞基(4171,NR_未評等)-CTBC251208") if pf else {}
        e = pf("某報告(20261006-122001)") if pf else {}
        chk("F3 實跑檔名律(鏈上 %s):6 位數 / 民國 7 位數日期不再被時間戳搶走 · 代號 · 券商照舊" % (info["parse_owners"][:1] or ["?"])[0],
            a.get("report_date") == "2025-12-08" and a.get("codes") == ["4171"] and a.get("copy_stamp") == "2026-10-06 12:20:04"
            and b.get("report_date") == "2025-12-02" and b.get("codes") == ["3017"] and c.get("report_date") == "2025-10-01"
            and d.get("report_date") == "2025-12-08" and "copy_stamp" not in d and {k: v for k, v in a.items() if k != "copy_stamp"} == d,
            (a.get("report_date"), b.get("report_date"), c.get("report_date"), d.get("report_date")))
        chk("F4 只有時間戳、沒有別的日期 → 報告日期照實留空(不拿下載時間充數)", bool(pf) and e.get("report_date") is None and e.get("copy_stamp"), e)
        sp = vars(PAR).get("subprocess") if PAR is not None else None
        me, old = str(Path(__file__).resolve()), str(Path(PAR.__file__).resolve()) if PAR is not None else ""
        chk("F5 平行子行程改用本檔起跑:擷取子行程的指令換檔 · 其他指令 · 別的檔原樣",
            isinstance(sp, _SubprocessVia) and sp.rewrite(["py", old, WORKER_VERB, "job.json"]) == ["py", me, WORKER_VERB, "job.json"]
            and sp.rewrite(["py", old, "extract"]) == ["py", old, "extract"] and sp.rewrite(["py", "x.py", WORKER_VERB, "j"]) == ["py", "x.py", WORKER_VERB, "j"]
            and sp.PIPE is sp._real.PIPE)
    restored = (not any(getattr(vars(m).get("parse_filename"), "_vrn_v0276", False) for m in sys.modules.values())
                and not isinstance(vars(PAR).get("subprocess"), _SubprocessVia))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("F6 跑完還原(鏈上檔名律與 subprocess 都是原件)· 檔面:第 3 行加速器標記 · provenance 守門在 --selftest 之前 · 零 TA-Lib · 不寫同意閘",
        restored and "\ndef main(" in text and "\ndef selftest(" in text and "\ndef collect(" in text
        and text.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and text.index('sys.argv[1:2] == ["provenance"]') < text.index('"--selftest" in sys.argv:')
        and "import " + "talib" not in text and "environ[\"VIA_NET" + "_CONSENT\"] =" not in text)
    print("  ── 前版 %s 自測(本版沒有常駐換裝,照前版原行為)──" % PRIOR_PATH.name, flush=True)
    prior_rc = int(PRIOR.selftest() or 0)
    chk("F7 前版 %s 自測照過" % PRIOR_PATH.name, prior_rc == 0, prior_rc)
    n = sum(ok)
    print("[計] %s %s(%s_%s.py)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, FAMILY, TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["provenance"]:     # 同前版:provenance 先於任何 --selftest 攔截
        sys.exit(provenance(sys.argv[2:]))
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))
