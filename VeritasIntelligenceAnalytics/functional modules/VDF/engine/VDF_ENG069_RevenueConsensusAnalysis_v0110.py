#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_ENG069_RevenueConsensusAnalysis v0110 — 薄尾:主庫解析不因一個壞候選就整個退回舊路徑(VCGC 全景 SWALLOW · 第二輪 2026-10-20)

操作員令(2026-10-20):「繼續第二輪修復 SWALLOW 與 TAILAPI」。
v0109 resolve_db 在資料家(VIA_DATA_HOME)裡 rglob 找 vdf_tw_market.duckdb、取最新的;整段包在 `except Exception: pass`:
只要有一個候選 stat 失敗(斷掉的連結 · 被鎖 · 剛被刪 · 網路磁碟出錯),整段放棄、默默退回舊主路徑 —— 可能讀到另一份舊庫。本版(只改這一支):
  ① 逐個候選 stat;壞的略過並照實記(stderr 一行「[庫解析] 略過 N 個讀不到的候選 …」),其餘照取最新的。
  ② 走資料夾用 os.walk(onerror 記下讀不到的資料夾、照樣往下找;不跟連結,避免繞圈)。
  ③ 優先序不變:VIA_DB_VDF_TW_MARKET > 資料家內最新那份 > 舊主路徑;都沒有才退回舊主路徑(有略過照印)。
換在 v0109 模組全域(run / analyze / probe / _data_ready 都走這支)。其餘全照 v0109。
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境。
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG069_RevenueConsensusAnalysis"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0110(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0110(p) < _vnum_v0110(__file__)), key=_vnum_v0110)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)

import os
_RESOLVE_DB_V0109 = PRIOR.resolve_db
_LAST = {"skipped": []}


def resolve_db() -> Path:
    """同 v0109 優先序;資料家內逐個候選 stat,壞的略過照實記(不再整段退回舊主路徑)。"""
    env_db = os.environ.get("VIA_DB_VDF_TW_MARKET")
    if env_db and Path(env_db).exists():
        return Path(env_db)
    home = os.environ.get("VIA_DATA_HOME")
    skipped = []
    if home and Path(home).exists():
        hp = Path(home)
        if hp.is_file():
            cands = [hp] if hp.name == "vdf_tw_market.duckdb" else []
        else:
            cands = []
            for root, _dirs, files in os.walk(hp, onerror=lambda e: skipped.append("資料夾 %s:%s" % (getattr(e, "filename", "?"), type(e).__name__))):
                if "vdf_tw_market.duckdb" in files:
                    cands.append(Path(root) / "vdf_tw_market.duckdb")
        best = None
        for c in cands:
            try:
                mt = c.stat().st_mtime
            except OSError as exc:
                skipped.append("%s:%s" % (c, type(exc).__name__))
                continue
            if best is None or mt > best[0]:
                best = (mt, c)
        _LAST["skipped"] = skipped
        if skipped:
            print("  [庫解析] 略過 %d 個讀不到的候選(%s)%s" % (len(skipped), skipped[0], "" if best else " → 退回舊主路徑"), file=sys.stderr, flush=True)
        if best:
            return best[1]
    _LAST["skipped"] = skipped
    return PRIOR.DB_TW


PRIOR.resolve_db = resolve_db


def own_checks() -> int:
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))
    import shutil
    import tempfile
    keep = {k: os.environ.get(k) for k in ("VIA_DB_VDF_TW_MARKET", "VIA_DATA_HOME")}
    td = Path(tempfile.mkdtemp(prefix="eng069v0110_"))
    try:
        os.environ.pop("VIA_DB_VDF_TW_MARKET", None)
        good = td / "home" / "mega" / "vdf_tw_market.duckdb"
        good.parent.mkdir(parents=True)
        good.write_bytes(b"x")
        flaky = td / "home" / "flaky"                # 掃這個夾丟 OSError(工作站 OneDrive 夾 I/O 錯 / 掃到一半被移走;不是 PermissionError)
        (flaky / "deep").mkdir(parents=True)
        real_scandir = os.scandir

        def scandir(path="."):
            if Path(path) == flaky:
                raise OSError(5, "Input/output error", str(path))
            return real_scandir(path)
        os.environ["VIA_DATA_HOME"] = str(td / "home")
        os.scandir = scandir
        try:
            try:
                got = resolve_db()
            except Exception as exc:                # noqa: BLE001 — 自測裡崩了也照實算 FAIL
                got = "拋 %s" % type(exc).__name__
            try:
                old = _RESOLVE_DB_V0109()
            except OSError as exc:                  # 版本差:有的 Python 讓它直接往外拋(也是不可用)
                old = "拋 %s" % type(exc).__name__
        finally:
            os.scandir = real_scandir
        chk("① 資料家裡有一個夾掃不了(OSError,非權限錯):本版記下略過、照找到好的那份;v0109 整段放棄退回舊主路徑(或往外拋)",
            got == good and len(_LAST["skipped"]) == 1 and "flaky" in _LAST["skipped"][0] and old != good, (got, old, _LAST))
        bad = td / "home" / "stale" / "vdf_tw_market.duckdb"
        bad.parent.mkdir(parents=True)
        bad.symlink_to(td / "gone.duckdb")         # 斷掉的連結:stat 丟 FileNotFoundError → 本版略過照記
        got2 = resolve_db()
        chk("①b 斷掉的連結候選:略過照記,照取好的那份", got2 == good and any("stale" in x for x in _LAST["skipped"]), (got2, _LAST))
        bad.unlink()
        newer = td / "home" / "newer" / "vdf_tw_market.duckdb"
        newer.parent.mkdir(parents=True)
        newer.write_bytes(b"y")
        os.utime(good, (1_700_000_000, 1_700_000_000))
        chk("② 沒有壞候選:取最新那份(同 v0109)", resolve_db() == newer == _RESOLVE_DB_V0109() and not _LAST["skipped"])
        os.environ["VIA_DB_VDF_TW_MARKET"] = str(good)
        env_ok = resolve_db() == good
        os.environ.pop("VIA_DB_VDF_TW_MARKET")
        os.environ["VIA_DATA_HOME"] = str(td / "nowhere")
        chk("③ 優先序不變:VIA_DB_VDF_TW_MARKET 最先;資料家不在 = 舊主路徑", env_ok and resolve_db() == PRIOR.DB_TW)
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    chk("④ v0109 模組全域換成本版(run / analyze / probe / _data_ready 走這支)", PRIOR.resolve_db is resolve_db)
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("⑤ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VRN2_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    print("  [計] %s 本版 %d/%d · %s" % (TAG, p, p + f, "PASS" if not f else "FAIL"), flush=True)
    return 0 if not f else 1


def selftest() -> int:
    return own_checks() or PRIOR.selftest()


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== %s · 薄尾自測(主庫解析壞候選略過照實記;零網路)===" % TAG, flush=True)
        if own_checks():
            return 1
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
