#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG058_IndustryUnifiedMap v0103 — 薄尾(v0102 一字不動):自測不改寫已追蹤的冊

桌機 2026-11-26 20:21 實錄(HostBoot lakeall):一開跑就 [停] —— 倉裡已追蹤檔
supportive modules/registry/VIA_IndustryUnifiedMap_v0100.json 被改了。追根:上一輪 vdfcheck 的 VDF test 跑到本引擎,
v0102 自測在「產業庫在位」時呼叫 build(),build() 把整本冊寫回 OUT_JSON(已追蹤的正本)→ 自測留下已追蹤檔改動,
擋住下一個要乾淨工作樹的動作。違反 CLAUDE.md「自測不吃本機狀態 · 一律在暫存夾造資料」。
本版只改自測:--selftest 期間 v0102 模組的 OUT_JSON 暫時指到暫存夾,六檢照跑(庫在 → 真建冊驗數字;庫不在 → 照舊 NODATA rc 2),
跑完指回正本並核對正本位元沒變。正式動詞(build · --status)照 v0102,一字不改(build 照舊寫正本 —— 那是要的)。
零網路(自測);不設同意閘;不用 TA-Lib。用法同前:build | --status | --selftest
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

import hashlib
import importlib.util
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG058_IndustryUnifiedMap"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def build() -> dict:                                 # 必備 API 照前版(寫正本)
    return PRIOR.build()


def status() -> int:
    return PRIOR.status()


def _sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def isolated_prior_selftest() -> tuple:
    """v0102 六檢在 OUT_JSON 指到暫存夾下跑;回 (rc, 正本位元前後是否相同, 暫存檔是否寫到)。"""
    real = PRIOR.OUT_JSON
    before = _sha(real)
    box = Path(tempfile.mkdtemp(prefix="eng058_iso_"))
    PRIOR.OUT_JSON = box / real.name
    try:
        rc = PRIOR.selftest()
        wrote_temp = PRIOR.OUT_JSON.is_file()
    finally:
        PRIOR.OUT_JSON = real
        shutil.rmtree(box, ignore_errors=True)
    return rc, _sha(real) == before, wrote_temp


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 產業混合分類冊(VDF_ENG058 v0103)· 自測(冊寫暫存夾,不改寫正本)===")
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note and not cond else ""), flush=True)

    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 網路工具橋在位(載入不出網)", VIA_NET_TOOL_PATH is not None)
    real = PRIOR.OUT_JSON
    rc, same, wrote_temp = isolated_prior_selftest()
    chk("③ 前版 v0102 六檢在隔離下跑完(0 綠 · 2 缺料 NODATA;1 才是壞)", rc in (0, 2), f"rc={rc}")
    chk("④ 正本冊位元前後相同(自測沒改寫已追蹤檔)· 跑完 OUT_JSON 指回正本", same and PRIOR.OUT_JSON == real)
    if rc == 0:
        chk("⑤ 庫在 → 冊真的建在暫存夾(不是沒跑)", wrote_temp)
    with tempfile.TemporaryDirectory() as td:            # 模擬「build 會寫檔」:換一個假 build,確認寫的是暫存不是正本
        keep_build = PRIOR.build
        keep_missing = PRIOR._missing_tables
        hit = {}

        def fake_build():
            PRIOR.OUT_JSON.write_text('{"x": 1}', encoding="utf-8")
            hit["path"] = PRIOR.OUT_JSON
            return {"totals": {"codes": 40, "twse_only": 6, "tpex_only": 2, "sector3_stock_counts": {"ELEC": 600, "FIN": 30, "TRAD": 500}},
                    "items": [{"via_id": "VIA-IND-%02d" % i} for i in range(40)]}
        try:
            PRIOR.build = fake_build
            PRIOR._missing_tables = lambda db, need: []
            before = _sha(real)
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()):     # 模擬那一輪前版印的燈不是真結果,不印(免得誤讀)
                isolated_prior_selftest()
            after = _sha(real)
        finally:
            PRIOR.build, PRIOR._missing_tables = keep_build, keep_missing
        chk("⑥ 模擬「庫在 → build 寫冊」:寫到暫存夾、正本位元不變", hit.get("path") is not None and hit["path"] != real and before == after,
            str(hit.get("path")))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 檔面:第 3 行加速器標記 · glob 取前版 · 零 TA-Lib · 不設同意閘",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "HERE.glob(_STEM" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    n = sum(ok)
    print(f"  [計] {_STEM} v0103 薄尾 {n}/{len(ok)} · 前版 rc={rc}", flush=True)
    if not all(ok):
        return 1
    return rc                                            # 前版缺料 NODATA(2)照實往上傳


if __name__ == "__main__":
    sys.exit(main())
