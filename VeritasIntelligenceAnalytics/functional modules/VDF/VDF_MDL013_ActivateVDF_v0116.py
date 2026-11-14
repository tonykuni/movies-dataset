#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0116 — 薄尾:總覽頁操作入口多「擷取矩陣」· 總覽頁也套 VRN-2 視覺規格(鎖)

操作員令(2026-11-01):「參考這種方式有架構地呈現擷取項目於 HTML U/I」「U/I 同 VRN-2 HTML U/I 相同視覺規格鎖死」。
疊在 v0115 之上;v0100 … v0115 一字不動。本版:
  ① 操作入口(總覽頁 · 終端 [操作入口] 行)多一條「擷取矩陣」→ VIA_Reports/vdf/FETCH_MATRIX_latest.html(VDF_SystemManager v0165 的 ui 步產;
     一輪裡 ui 在 db check 之後,所以矩陣的庫況是這一輪的)。檔在才出連結(同 v0114 規則)。
  ② 總覽頁寫完,經 VDF_ENG236_FetchMatrixUI.apply_spec 套 VDF_UI_VisualSpec_SSOT(= VRN-2 vrn2-professional-v0242 鎖定原文)+ 色票對照;
     鎖對不上就不套(照實黃)。終端印一行矩陣總結。
  ③ 收尾跑 VDF_SSOTSync 尾版 sync(VDF 自己的 SSOT / 正則 / 同義字 / 參數 / 政策帳本):登記 → 讀 VCGC 核發冊補 ssot_id → 未核號的寫請求;
     印「[VDF 編號同步] …」一行。同步出錯只記一行紅,不擋啟動(編號是 VCGC 的事,VDF 只提請求 · 只讀核發冊)。
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件。
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
LINK_V0116 = ("擷取矩陣", "FETCH_MATRIX_latest.html")
FM_GLOB_V0116 = "VDF_ENG236_FetchMatrixUI_v*.py"
SYNC_GLOB_V0116 = "VDF_SSOTSync_v*.py"


def _vnum_v0116(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0116(p) < _vnum_v0116(__file__)), key=_vnum_v0116)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100 = PRIOR.V0100


def __getattr__(name):
    return getattr(PRIOR, name)


_V0114_G = PRIOR.operate_links.__globals__          # v0114 本體全域(操作入口清單 · main 叫的 activate)
_LINKS_ORIG = tuple(_V0114_G["OPERATE_LINKS_V0114"])
_ACTIVATE_V0115 = PRIOR.activate


def _tail_module(folder: Path, glob: str, prefix: str):
    hits = [p for p in folder.glob(glob) if _vnum_v0116(p) >= 0]
    if not hits:
        return None
    p = max(hits, key=_vnum_v0116)
    name = prefix + p.stem
    if name not in sys.modules:
        sp = importlib.util.spec_from_file_location(name, p)
        mod = importlib.util.module_from_spec(sp)
        sys.modules[name] = mod
        sp.loader.exec_module(mod)
    return sys.modules[name]


def fm_module():
    return _tail_module(HERE / "engine", FM_GLOB_V0116, "_vdf_act_fm_")


def ssot_sync(vdf: Path = HERE) -> dict:
    """VDF 編號同步(VDF_SSOTSync 尾版 sync);出錯回紅一行,不擋啟動。"""
    try:
        mod = _tail_module(HERE, SYNC_GLOB_V0116, "_vdf_act_sync_")
        if mod is None:
            return {"lamp": "GRAY", "line": "[VDF 編號同步] GRAY · 沒有 VDF_SSOTSync 尾版"}
        return mod.sync(Path(vdf))
    except Exception as exc:  # noqa: BLE001 — 同步是收尾步,錯誤照實報、不擋啟動
        return {"lamp": "RED", "line": "[VDF 編號同步] RED · %s: %s" % (type(exc).__name__, str(exc)[:200])}


def matrix_line(ui_dir: Path) -> str:
    f = Path(ui_dir) / "FETCH_MATRIX_latest.json"
    try:
        c = json.loads(f.read_text(encoding="utf-8"))["counts"]
    except (OSError, ValueError, KeyError):
        return "[擷取矩陣] 這一輪沒產(ui 步沒跑到 VDF_SystemManager v0165 以上?)"
    return "[擷取矩陣] 表 %d · 到齊 %d · 待補 %d · 缺 %d · 未量 %d · 端點實測 %d/%d · 頁 %s" % (
        c["tables"], c["GREEN"], c["YELLOW"], c["RED"], c["NONE"], c["endpoints_verified"], c["endpoints"], f.with_suffix(".html"))


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0115 activate;收尾:總覽頁套 VRN-2 視覺規格 · 印擷取矩陣一行 · VDF 編號同步一行。"""
    card = _ACTIVATE_V0115(opt, manager, py, temp)
    ui_dir = V0100.VIA / "VIA_Reports" / "vdf"
    fm = fm_module()
    html_path = (card.get("report") or {}).get("html")
    how = fm.apply_spec(Path(html_path)) if (fm and html_path) else "ENG236 不在 / 沒有總覽頁"
    print("  " + matrix_line(ui_dir), flush=True)
    print("  [視覺規格] 總覽頁套 VRN-2 vrn2-professional-v0242:%s" % how, flush=True)
    card["visual_spec"] = how
    sy = ssot_sync()
    print("  " + sy["line"], flush=True)
    card["ssot_sync"] = {"lamp": sy.get("lamp"), "line": sy.get("line")}
    return card


def _patch_v0116() -> None:
    if LINK_V0116 not in _V0114_G["OPERATE_LINKS_V0114"]:
        _V0114_G["OPERATE_LINKS_V0114"] = tuple(_V0114_G["OPERATE_LINKS_V0114"]) + (LINK_V0116,)
    _V0114_G["activate"] = activate


def _unpatch_v0116() -> None:
    _V0114_G["OPERATE_LINKS_V0114"] = _LINKS_ORIG
    _V0114_G["activate"] = _ACTIVATE_V0115


_patch_v0116()


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    _patch_v0116()
    return PRIOR.main(argv)


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

    print("=== %s · 薄尾自測(操作入口多擷取矩陣 · 總覽頁套 VRN-2 視覺規格)===" % TAG)
    tmp = Path(tempfile.mkdtemp(prefix="vdf_act0116_"))
    try:
        (tmp / "FETCH_MATRIX_latest.html").write_text("<html></html>", encoding="utf-8")
        links = dict(PRIOR.operate_links(tmp))
        chk("① 操作入口有「擷取矩陣」且檔在才給連結(其他入口照舊)", links.get("擷取矩陣") and "VDF 操作頁(U/I)" in links
            and dict(PRIOR.operate_links(tmp / "none")).get("擷取矩陣") is None, links)
        ov = tmp / "ACTIVATE_VDF_latest.html"
        ov.write_text("<html><head><style>body{}</style></head><body>x</body></html>", encoding="utf-8")
        fm = fm_module()
        how = fm.apply_spec(ov) if fm else None
        chk("② 總覽頁套 VRN-2 視覺規格(%s)· ENG236 尾版 %s" % (how, getattr(fm, "TAG", None)), how == "inserted" and 'id="vrn2-professional-v0242"' in ov.read_text(encoding="utf-8"))
        (tmp / "FETCH_MATRIX_latest.json").write_text(json.dumps({"counts": {"tables": 58, "GREEN": 26, "YELLOW": 25, "RED": 0, "NONE": 7, "endpoints_verified": 7,
                                                                             "endpoints": 32}}), encoding="utf-8")
        chk("③ 收尾印矩陣一行", matrix_line(tmp).startswith("[擷取矩陣] 表 58 · 到齊 26"), matrix_line(tmp))
        vdf = tmp / "via" / "functional modules" / "VDF"
        vdf.mkdir(parents=True)
        (vdf / "VDF_Demo_SSOT_v0100.json").write_text(json.dumps({"code_regex": r"^\d{4}$"}), encoding="utf-8")
        sy = ssot_sync(vdf)
        chk("③b 收尾 VDF 編號同步一行(VDF_SSOTSync 尾版 sync;只寫 VDF 自己的 registry / contract)· %s" % sy.get("line"),
            str(sy.get("line", "")).startswith("[VDF 編號同步] ") and sy.get("lamp") in ("GREEN", "YELLOW")
            and any((vdf / "registry").glob("VDF_SSOT_Register_v*.json")) and (vdf / "contract" / "VDF_NUMBER_REQUEST_latest.json").is_file())
        bad = ssot_sync(ov / "VDF")                       # 父層是檔案 → 寫冊必失敗
        chk("③c 同步出錯 → 紅燈一行照實報(不丟例外、不擋啟動)· %s" % bad.get("line"),
            bad.get("lamp") == "RED" and str(bad.get("line", "")).startswith("[VDF 編號同步] RED · "), bad)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    chk("④ 換裝在位:v0114 全域 OPERATE_LINKS 多一條 · main 叫的 activate = 本版", LINK_V0116 in _V0114_G["OPERATE_LINKS_V0114"] and _V0114_G["activate"] is activate)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑤ VDF 獨立:不匯入他系統程式 · 兩座橋在 · 同意閘不寫", not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC)", src, re.M)
        and "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and "_CONSENT\"] =" not in body)
    if f:
        print("[計] %s 自測 %d/%d · FAIL" % (TAG, p, p + f))
        return 1
    print("[計] %s 本版 %d/%d · PASS" % (TAG, p, p + f))
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        return 0
    _unpatch_v0116()
    try:
        rc1 = PRIOR.selftest()
    finally:
        _patch_v0116()
    print("[計] %s 前版鏈 rc %s · %s" % (TAG, rc1, "PASS" if rc1 == 0 else "FAIL"))
    return rc1 if rc1 in (0, 1, 2, 3) else 1


if __name__ == "__main__":
    raise SystemExit(main())
