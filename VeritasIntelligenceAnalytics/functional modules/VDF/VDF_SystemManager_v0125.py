#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0125 — 薄尾:單引擎啟動前備料(動詞 params / prep;輸入參數 · SSOT · regex · 同義字)

操作員(2026-10-03):「準備單引擎啟動 vdf 及相關輸入參數 ssot regex 同義字於 … system manager」→ VDF 與 VRN 兩個管理員都做(VCGC-REQ133)。
  params <引擎> [--json]   一支引擎的啟動前備料卡(= engine params):① 輸入參數(argparse 旗標 · 預設 · 選項 · 必填 · 說明 + 子令 / 字面旗標)
                           ② 環境變數(同意閘另標,AI 永不代設)③ SSOT 冊 → 樹上尾版 ④ regex(本地條數 · 中央屬本支 · 與中央同式)
                           ⑤ 同義字(委樞印記 · 本地表 · 中央來源)⑥ 工作流步 + VDF 輸入範圍冊(E-xx 站 · 被哪些 IN-xx 用到) ⑦ 啟動短令範本 + 先自測那一句;
                           薄尾鏈沿全景 _link 走到本體,參數 / 冊 / regex / 同義字從整條鏈收
  prep [--json]            整個 VDF 每支引擎一列,寫 VIA_Reports/tooling/ENGINE_PARAMS_VDF_latest.json / .html(= engine prep)
本體在 VCGC 的 CGC_MDL253_ToolingInventory v0101(兩個管理員共用一份,VDF 不另抄);只讀(ast.parse,不執行被讀的檔),
本地同義字表 / 與中央同式的 regex 只列不改。其餘動詞(engine list / check / card · universe · validate …)全照前版。
只收 VCGC 呼叫(VIA_FROM_VCGC=YES);不碰 TA-Lib;不代設同意閘。
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REG = HERE.parents[1] / "supportive modules" / "registry"
_STEM = "VDF_SystemManager"
SUB = "VDF"
SAMPLE_v0125 = "VDF_ENG055_OmniFetch"                   # 自測用的真引擎(薄尾鏈 + 讀冊都有)
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
_inv_v0125 = None


def _vnum_v0125(path) -> int:            # 版本專屬名:元件冊以函式登記,共用名會把前版的紀錄搶走
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0125(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0125(p) < _vnum_v0125(__file__)), key=_vnum_v0125)
PRIOR = _load_v0125(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _inventory_v0125():
    """VCGC 檢視本體 CGC_MDL253 尾版(兩個管理員共用一份;v0101 起有 params / prep)。"""
    global _inv_v0125
    if _inv_v0125 is None:
        hits = [p for p in REG.glob("CGC_MDL253_ToolingInventory_v*.py") if _vnum_v0125(p) >= 0]
        if not hits:
            raise RuntimeError("CGC_MDL253_ToolingInventory 不在(先 git pull)")
        _inv_v0125 = _load_v0125(max(hits, key=_vnum_v0125), "_vdf_mgr_v0125_inventory")
    return _inv_v0125


def prep(args: list) -> int:
    """params <引擎> / prep:單引擎啟動前備料(輸入參數 · 環境變數 · SSOT 冊 · regex · 同義字 · 工作流步 · 短令)。"""
    try:
        inv = _inventory_v0125()
    except RuntimeError as e:
        print(f"[{TAG}] 備料 ABSENT:{e}")
        return 3
    if not hasattr(inv, "params_card_v0101"):
        print(f"[{TAG}] CGC_MDL253 尾版還沒有 params / prep(要 v0101 起;先 git pull)")
        return 3
    return inv.engine_main(SUB, list(args), TAG)


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("params", "prep"):
        return prep(args)
    if args[:2] in (["engine", "params"], ["engine", "prep"]):
        return prep(args[1:])
    return PRIOR.main()


def selftest() -> int:
    prior_rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(單引擎備料:params / prep)===")
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    chk("① 未經 VCGC 拒絕(params 也一樣)", main(["params", SAMPLE_v0125]) == 2)
    os.environ["VIA_FROM_VCGC"] = "YES"
    try:
        inv = _inventory_v0125()
        chk("② 檢視本體 = VCGC 的 CGC_MDL253 尾版且有 params / prep(兩個管理員同一份)",
            hasattr(inv, "params_card_v0101") and hasattr(inv, "prep_v0101"), Path(inv.__file__).name)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["params", SAMPLE_v0125, "--json"])
        line = next((x for x in reversed(buf.getvalue().splitlines()) if x.startswith('{"engine_params"')), "{}")
        card = json.loads(line).get("engine_params") or {}
        chk("③ params <引擎>:備料卡七段都在(參數 · 環境變數 · SSOT · regex · 同義字 · 工作流步 · 短令)· rc 照燈",
            rc in (0, 2) and all(k in card for k in ("params", "ssot", "regex", "synonyms", "workflow", "launch", "chain"))
            and card["launch"]["template"].startswith("via-vdfeng "), (rc, card.get("lamp"), card.get("chain"), card.get("launch", {}).get("template")))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc2 = main(["engine", "params", SAMPLE_v0125, "--json"])
        chk("④ engine params 與 params 同一條路(rc 相同)", rc2 == rc, (rc, rc2))
        with tempfile.TemporaryDirectory() as tmp:
            doc = inv.prep_v0101(SUB, write=True, out_dir=Path(tmp))
            wrote = all((Path(tmp) / f"ENGINE_PARAMS_{SUB}_latest.{x}").is_file() for x in ("json", "html"))
        s = doc["summary"]
        chk("⑤ prep:VDF 每支引擎一列 · json + html 落地 · 沒有被擋的紅燈", wrote and s["engines"] > 10 and not s["lamps"]["RED"],
            {k: s[k] for k in ("engines", "lamps", "with_cli", "with_books", "local_synonym_tables")})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            miss = main(["params", "NO_SUCH_ENGINE_ZZZ"])
        chk("⑥ 找不到的引擎回 3(不猜)", miss == 3)
    finally:
        if keep is None:
            os.environ.pop("VIA_FROM_VCGC", None)
        else:
            os.environ["VIA_FROM_VCGC"] = keep
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 加速器橋 · 網路工具橋 · 正典橋在;不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and "[VIA:LIB-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) and prior_rc == 0 else 'FAIL'}")
    return 0 if all(ok) and prior_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
