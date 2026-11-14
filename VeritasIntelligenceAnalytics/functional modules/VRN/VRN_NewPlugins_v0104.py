#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_NewPlugins v0103 — 薄尾:補 L103 PY 加速器橋(v0102 已隨 PR #448 發布、不就地改;其餘一字照 v0102)。

操作員令(2026-10-04,VCGC-REQ155):「所有 PS PY 依規定安裝加速器及模組」。
  掃橋器 CGC_MDL124 全樹只剩 v0102 這一支缺 SuperAccel 橋;VCGC 子系統邊界不准就地改 VRN 正本 → 出本薄尾。
  宿主用法照 v0102(`import VRN_NewPlugins_v0103 as additions` · get_plugins() · ast_catalog());
  沒在本檔定義的名稱一律轉接 v0102(__getattr__),插件字典與統一契約不變。
  python VRN_NewPlugins_v0103.py            照 v0102:印 AST 索引(不擷取、不安裝)
  python VRN_NewPlugins_v0103.py --selftest 自測
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====
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

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / "VRN_NewPlugins_v0102.py"
_spec = importlib.util.spec_from_file_location("VRN_NewPlugins_v0102_for_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


TAG = f"VRN_NewPlugins v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
PLUGINS = PRIOR.PLUGINS


def get_plugins():
    """回傳可自行新增/移除的描述字典(照 v0102:新字典、僅匯入不執行)。"""
    return PRIOR.get_plugins()


def ast_catalog():
    """AST 索引(照 v0102:讀 v0102 本體,不執行第三方套件)。"""
    return PRIOR.ast_catalog()


def selftest() -> int:
    res = []

    def chk(name, cond, note=""):
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""))

    p1, p2 = get_plugins(), PRIOR.get_plugins()
    chk("① 插件字典照 v0102(同鍵 · 同 call)", sorted(p1) == sorted(p2) and len(p1) >= 9
        and all(p1[k]["call"] is p2[k]["call"] for k in p1), sorted(p1))
    p1.pop(next(iter(p1)))
    chk("② 回傳新字典:本地拔除不影響模組內 PLUGINS", len(get_plugins()) == len(PLUGINS) == len(p2))
    cat = ast_catalog()
    chk("③ AST 索引照 v0102(函式數 · 插件 id 對得上)", len(cat) == len(PRIOR.ast_catalog()) > 0
        and {r["plugin_id"] for r in cat if r["plugin_id"]} == {v.get("plugin_id") for v in PLUGINS.values()})
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ L103 PY 加速器橋在(__future__ 之後 · graceful)",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and src.index("from __future__") < src.index("[VIA:ACCEL-BRIDGE:v0100]"))
    chk("⑤ 轉接:本檔沒定義的名稱照 v0102", __getattr__("def_result") is PRIOR.def_result)
    ok = sum(res)
    print(f"[計] {TAG} 本版 {ok}/{len(res)} · 合計 {'PASS' if ok == len(res) else 'FAIL'}")
    return 0 if ok == len(res) else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    # 預設照 v0102:僅列出 AST 索引;不擷取任何檔案、不安裝任何依賴。
    print(json.dumps(ast_catalog(), ensure_ascii=False, indent=2))
