#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG056_ChipBackfill v0109 — 薄尾:系統獨立 —— 真正開始抓的那一刻,VCGC 的 ScrapeGate 尺檔不在或壞掉也不倒(改用 VDF 自己的同一把尺) · 收 --start(大類起日)

2026-11-19 VCGC 檢視(操作員令「系統獨立 · 啟動 VDF 更新 2021-01-01 至最新」):本家族底下有一層在 _prior() 裡用寫死的路徑
`supportive modules/registry/CGC_MDL224_ScrapeGate_v0100.py` 載 VCGC 的同意尺(每次開始抓才載)。自測走不到那一步,
所以 11-18 的「拔掉 VCGC 模組」演練沒抓到;VCGC 少這個檔或這個檔壞掉,籌碼回補 一開始抓就丟例外。
本版(前版一字不動;直接執行 = 照前版原樣跑,參數 · 輸出 · 結束碼照舊):
  ① 只在本引擎這一個行程跑的期間,攔下「載 VCGC 尺檔」那一步:檔在而且編譯得過 → 照用 VCGC 的尺(行為與前版完全相同);
     檔不在或編譯不過 → 改給 VDF 自己的同一把尺(VIA_NET_CONSENT=YES 且 VIA_SCRAPE_CONSENT 是 YES 或責任字串才開,其餘一律關)。
     跑完還原,不留任何改動在行程外;不寫檔、不讀寫同意閘。
  ② 收 --start YYYY-MM-DD:交易日曆改成從起日起(前版寫死 2024-01-02);日曆照舊取自日價表的上市交易日。不給 = 照前版。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔自己不連網,連網的是回補本體。"""
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

import importlib.abc
import importlib.machinery
import importlib.util
import os
import re
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG056_ChipBackfill"
VERSION = "v0109"
GATE_PREFIX = "CGC_MDL224_ScrapeGate_v"
_TOKEN = "I_ACCEPT_RESPONSIBLE_" + "SCRAPING"
_NK, _SK = "VIA_NET_" + "CONSENT", "VIA_SCRAPE_" + "CONSENT"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_ORIG_SPEC_FROM_FILE = importlib.util.spec_from_file_location   # 載入當下的原件;自測用來確認離開 with 後還原
PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)


def vdf_gate_open(env=None) -> bool:
    """VDF 自己的同一把尺(與 CGC_MDL224 v0100 判法逐字相同)。"""
    env = os.environ if env is None else env
    return env.get(_NK) == "YES" and (env.get(_SK) or "") in ("YES", _TOKEN)


def gate_usable(path) -> bool:
    p = Path(path)
    if not p.is_file():
        return False
    try:
        compile(p.read_text(encoding="utf-8-sig"), str(p), "exec")
        return True
    except (SyntaxError, ValueError, OSError):
        return False


class _ShimLoader(importlib.abc.Loader if hasattr(importlib, "abc") else object):
    def create_module(self, spec):
        return None

    def exec_module(self, module):
        module.gate_open = vdf_gate_open
        module.TOKEN = _TOKEN
        module.__doc__ = "VDF 自己的同一把尺(VCGC 的 ScrapeGate 不在或壞掉時的退路)"


def chip_days(module, start: str):
    """籌碼的交易日曆:日價表上的上市(.TW)交易日,從起日起(前版寫死 2024-01-02)。"""
    def trading_days():
        con = module._connect(module.DB_TW, read_only=True)
        try:
            return [r[0] for r in con.execute(
                "SELECT DISTINCT date FROM tw_daily_prices WHERE ticker LIKE '%.TW' AND date >= ? ORDER BY date", [start]).fetchall()]
        finally:
            con.close()
    return trading_days


def split_start(a: list) -> tuple:
    a = list(a)
    if "--start" not in a:
        return None, a
    i = a.index("--start")
    if i + 1 >= len(a):
        raise ValueError("--start 後面要接日期 YYYY-MM-DD")
    from datetime import date
    s = date.fromisoformat(a[i + 1]).isoformat()
    del a[i:i + 2]
    return s, a



class _Hook:
    """只在 with 區塊裡攔 importlib.util.spec_from_file_location;離開一定還原。"""

    def __init__(self, start=None):
        self.start, self.used = start, []

    def __enter__(self):
        self.orig = importlib.util.spec_from_file_location
        hook = self

        def spec_from_file_location(name, location=None, *a, **k):
            p = Path(str(location)) if location is not None else None
            if p is not None and p.name.startswith(GATE_PREFIX) and p.suffix == ".py" and not gate_usable(p):
                hook.used.append(("VDF 自己的尺", p.name))
                return importlib.util.spec_from_loader(name, _ShimLoader())
            spec = hook.orig(name, location, *a, **k)
            if p is not None and p.name.startswith(GATE_PREFIX):
                hook.used.append(("VCGC 尺", p.name))
            return _wrap_spec(spec, p, hook) if spec is not None else spec

        importlib.util.spec_from_file_location = spec_from_file_location
        return self

    def __exit__(self, *exc):
        importlib.util.spec_from_file_location = self.orig
        return False


class _AfterExec(importlib.abc.Loader if hasattr(importlib, "abc") else object):
    """包住原 loader:模組跑完後,若它有寫死 2024-01-02 的 trading_days,換成從起日起的那一支。"""

    def __init__(self, inner, start, hook):
        self.inner, self.start, self.hook = inner, start, hook

    def create_module(self, spec):
        return self.inner.create_module(spec)

    def exec_module(self, module):
        self.inner.exec_module(module)
        if callable(getattr(module, "trading_days", None)) and hasattr(module, "_connect") and hasattr(module, "DB_TW"):
            module.trading_days = chip_days(module, self.start)
            self.hook.used.append(("籌碼日曆起日", self.start))


def _wrap_spec(spec, p, hook):
    if hook.start and p is not None and p.name.startswith(_STEM + "_v") and spec.loader is not None:
        spec.loader = _AfterExec(spec.loader, hook.start, hook)
    return spec


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    try:
        start, a = split_start(a)
    except ValueError as exc:
        print("[拒絕] " + str(exc) + "(零外呼 · 零寫入)")
        return 2

    saved = sys.argv
    sys.argv = [str(PRIOR_PATH)] + a
    try:
        with _Hook(start=start):
            runpy.run_path(str(PRIOR_PATH), run_name="__main__")
        return 0
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    finally:
        sys.argv = saved


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    print("=== %s %s 薄尾自測(VCGC 尺不在也不倒;零網路)===" % (_STEM, VERSION))
    combos = [{}, {_NK: "YES"}, {_SK: "YES"}, {_NK: "YES", _SK: "OFF"}, {_NK: "YES", _SK: "YES"}, {_NK: "YES", _SK: _TOKEN}, {_NK: "NO", _SK: "YES"}, {_NK: "YES", _SK: "maybe"}]
    expect = [False, False, False, False, True, True, False, False]
    chk("① VDF 自己的尺八種同意組合照規格", [vdf_gate_open(c) for c in combos] == expect)
    real_gate = HERE.parents[2] / "supportive modules" / "registry" / (GATE_PREFIX + "0100.py")
    with tempfile.TemporaryDirectory(prefix="vdf_gate_tail_") as td:
        t = Path(td)
        missing = t / (GATE_PREFIX + "9999.py")
        broken = t / (GATE_PREFIX + "9998.py")
        broken.write_text("def gate_open(:\n", encoding="utf-8")
        neg = ""
        try:
            sp = importlib.util.spec_from_file_location("neg_missing", missing)
            m = importlib.util.module_from_spec(sp)
            sp.loader.exec_module(m)
        except (FileNotFoundError, OSError) as exc:
            neg = type(exc).__name__
        chk("② 負控:沒有攔的時候,尺檔不在 → 一載就丟例外(就是本版要修的)", bool(neg), neg)
        with _Hook() as h:
            got = []
            for p, nm in ((missing, "t_missing"), (broken, "t_broken")):
                sp = importlib.util.spec_from_file_location(nm, p)
                m = importlib.util.module_from_spec(sp)
                sp.loader.exec_module(m)
                got.append(m.gate_open)
            real = None
            if real_gate.is_file():
                sp = importlib.util.spec_from_file_location("t_real", real_gate)
                m = importlib.util.module_from_spec(sp)
                sp.loader.exec_module(m)
                real = m.gate_open
        chk("③ 攔的時候:尺檔不在 / 壞掉 → 給 VDF 自己的尺;沒同意照樣關、兩道同意才開", all(g is vdf_gate_open for g in got) and got[0]({}) is False and got[1]({_NK: "YES", _SK: "YES"}) is True, h.used)
        chk("④ VCGC 尺檔在而且編得過 → 照用 VCGC 的那一支,且兩把八種組合逐一相同(這台沒有 VCGC 尺 = 只對規格)",
            real is None or (real is not vdf_gate_open and [real(c) for c in combos] == expect), "VCGC 尺 " + ("在" if real is not None else "不在這台"))
    chk("⑤ 離開 with 就還原(行程外不留改動)", importlib.util.spec_from_file_location is _ORIG_SPEC_FROM_FILE)
    try:
        import duckdb
    except ImportError:
        duckdb = None
    if duckdb is None:
        chk("⑥ duckdb 在(不在就量不到籌碼日曆)", False, "缺件:SKIP 不是綠")
    else:
        with tempfile.TemporaryDirectory(prefix="chip_start_") as td:
            db = Path(td) / "tw.duckdb"
            con = duckdb.connect(str(db))
            con.execute("CREATE TABLE tw_daily_prices (date VARCHAR, ticker VARCHAR)")
            con.executemany("INSERT INTO tw_daily_prices VALUES (?, ?)", [("2021-01-04", "2330.TW"), ("2023-06-01", "2330.TW"), ("2024-01-02", "2330.TW"), ("2024-01-03", "6488.TWO")])
            con.close()
            body = None
            for p in sorted(HERE.glob(_STEM + "_v*.py"), key=_vnum, reverse=True):
                txt = p.read_text(encoding="utf-8", errors="ignore")
                if _vnum(p) < _vnum(__file__) and "def trading_days" in txt and "AND date >= '2024-01-02'" in txt:
                    body = p
                    break
            sp = importlib.util.spec_from_file_location("chip_body_neg", body)
            m0 = importlib.util.module_from_spec(sp)
            sp.loader.exec_module(m0)
            m0.DB_TW = db
            neg = m0.trading_days()
            with _Hook(start="2021-01-01") as h:
                sp = importlib.util.spec_from_file_location("chip_body_pos", body)
                m1 = importlib.util.module_from_spec(sp)
                sp.loader.exec_module(m1)
            m1.DB_TW = db
            pos = m1.trading_days()
            chk("⑥ 起日:前版日曆從 2024-01-02 起(負控);本版給 --start 2021-01-01 → 從 2021 起;只算上市 .TW 日", neg == ["2024-01-02"] and pos == ["2021-01-04", "2023-06-01", "2024-01-02"], "前版 %s · 本版 %s" % (neg, pos))
        bad = ""
        try:
            split_start(["--start", "nope"])
        except ValueError as exc:
            bad = str(exc)
        chk("⑥b 起日格式不對 → 拒絕;沒給 = 照前版", bool(bad) and split_start(["--days", "3"]) == (None, ["--days", "3"]))

    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 加速器橋真的匯入 · 網路工具橋在 · 不含本機路徑 · 不寫同意值", "import VIA_SuperAccel_Module as VIA_ACCEL" in src and "via_net_unified_v*.py" in src
        and ("C:" + "\\Users") not in src and ("environ[" + "_NK") not in src)
    env = dict(os.environ, VIA_FROM_VCGC="YES")
    p = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd=str(HERE.parent), timeout=600)
    chk("⑧ 前版(%s)自測照過(另起行程)" % PRIOR_PATH.name, p.returncode == 0, "rc %s" % p.returncode)
    good = all(ok)
    print("[計] %s %s 本版 %d/%d · %s" % (_STEM, VERSION, sum(ok), len(ok), "PASS" if good else "FAIL"))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
