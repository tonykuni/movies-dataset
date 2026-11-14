#!/usr/bin/env python3
r"""VDF_ENG236_FetchMatrixUI v0102 — 薄尾:自測不再被「本機資料家讀得到」左右(頁面 / 建頁行為一字不動)

工作站實跑(2026-11-15 ActivateVDF engine_launch):本支 RED —— v0101 自測 11/12:④b「讀庫失敗 → 沿用快取」。
v0101 的 table_columns 經 ENG237 resolve_home 找資料家(--home > VIA_VDF_DB_HOME > 冊 > 倉內 output_hub);
工作站一輪裡 VIA_VDF_DB_HOME 指向真的資料家、讀得到表 → 不會走快取 → ④b 判 FAIL(引擎沒錯,測資跟著環境走)。
容器重現:VIA_VDF_DB_HOME 指向一份有表的庫 → v0101 自測同樣 11/12 · ④b FAIL。
本版(v0100 … v0101 一字不動;只換自測期間的環境,跑完還原):
  ① 測具檢:自測期間 VIA_VDF_DB_HOME 指向空的暫存夾(= 讀不到庫)→ 跑 v0101 自測(含 v0100)→ 前版鏈 rc 0。
  ② 本境真實檢:用本機真的資料家跑一次 table_columns(只讀;快取寫進暫存夾)→ 讀到表 = 欄名;讀不到 = 原因(不當掉、不假綠)。
零網路 · 不寫模板冊 · 不碰 TA-Lib · 同意閘不讀不寫。
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

_STEM = "VDF_ENG236_FetchMatrixUI"
import contextlib
import importlib.util
import os
import pathlib
import re
import sys
import tempfile
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_tail(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_tail(p) < _vnum_tail(__file__)), key=_vnum_tail)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _own_src_ok() -> bool:
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    return ("[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and "_CONSENT" not in body
            and not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC|ta" + r"lib\b)", src, re.M))


class _Checks:
    def __init__(self):
        self.ok = []

    def __call__(self, name, cond, note=""):
        self.ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if (note and not cond) else ""), flush=True)

    def done(self) -> int:
        good = all(self.ok)
        print("[計] %s 薄尾 %d/%d · %s" % (TAG, sum(self.ok), len(self.ok), "PASS" if good else "FAIL"), flush=True)
        return 0 if good else 1


@contextlib.contextmanager
def env_as(**kv):
    keep = {k: os.environ.get(k) for k in kv}
    os.environ.update({k: str(v) for k, v in kv.items()})
    try:
        yield
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def selftest() -> int:
    chk = _Checks()
    print("=== %s · 薄尾自測(資料家測具;零網路)===" % TAG, flush=True)
    before = os.environ.get("VIA_VDF_DB_HOME")
    with tempfile.TemporaryDirectory(prefix="vdf_eng236_v0102_") as td:
        with env_as(VIA_VDF_DB_HOME=Path(td) / "empty_home"):
            (Path(td) / "empty_home").mkdir()
            rc = PRIOR.selftest()
        chk("① 測具下(資料家 = 空暫存夾,讀不到庫)前版鏈自測 rc 0(④ 讀不到 → 寫原因 · 有快取 → 沿用快取)", rc == 0, rc)
        r = PRIOR.table_columns(Path(td) / "real_probe")
    real = ("讀到 %d 表" % len(r["cols"])) if r["cols"] else ("讀不到:%s" % (r.get("why") or r.get("source")))
    chk("② 本境真實資料家照實(%s):讀到 → 欄名;讀不到 → 原因(不當掉)" % real, isinstance(r.get("cols"), dict) and bool(r["cols"] or r.get("why") or r.get("source")), r)
    chk("③ VIA_VDF_DB_HOME 還原成自測前的值", os.environ.get("VIA_VDF_DB_HOME") == before)
    chk("④ 兩座橋在 · 不匯入他系統程式 · 不碰 TA-Lib · 同意閘不讀不寫", _own_src_ok())
    return chk.done()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
