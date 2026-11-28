#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_PanoramaFusion_SuperEngine v0302 — 薄尾(v0300 / v0301 一字不動):治理四修(PR #782 Codex 3×P1 + 1×P2)

① (P1)不寫別的系統:fusion / batch_prepare 的寫入範圍只留 VCGC 自己的檔。
     `functional modules/` 底下(VDF · VRN · VQG · VAP …)、檔名以 VDF_ / VRN_ / VQG_ / VAP_ 開頭、manifest items 的 system 不是 VCGC → 一律唯讀。
     判不出擁有者 = 唯讀(fail-closed)。唯讀的照常盤點(panorama 不變),修補交該系統自己的 SystemManager。本工具家族自己的檔也不當修補對象。
② (P1)環境不自己重建:repair_environment 一律 BLOCKED;audit_envs 只稽核,不修;有缺就附「via-envgov plan → 操作員 via-envgov apply --approve」。
     boot / all 的第 1 道因此只稽核。
③ (P1)不覆寫原檔:fusion 的 --apply 不再寫回原檔名(前版一字不動 · 已鎖成功不改)。
     只出候選夾與收據,收據寫明 apply_refused;要上線的改動照 VCGC 流程出新版號檔、註冊。
④ (P2)產生的執行期橋找設定的退路改成 engine_config_v0300.json(= config() 預設建的檔名),不再找不存在的 engine_config.json。
另:v0300 開子行程(三道 _lane · _contracts · _bridgeprobe)用它自己的 __file__;本版把它指到本檔,子行程才吃得到上面四修。
其餘照 v0301 → v0300。自測零網路 · 暫存夾 · 不碰 TA-Lib · 不設同意閘。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath

VERSION = "v0302"
STEM = "VIA_PanoramaFusion_SuperEngine"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0301
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V300 = PRIOR.PRIOR                                             # v0300 本體(函式都在它的模組全域)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


FOREIGN_PREFIXES = ("VDF_", "VRN_", "VRN2_", "VQG_", "VAP_")
OWN_FAMILY = re.compile(r"^(VIA_PanoramaFusion_.*|test_panorama_fusion_v\d{4}|test_v\d{4}_workflow)\.py$")
ENV_HANDOFF = "via-envgov plan → 操作員 via-envgov apply --approve"
APPLY_REFUSED = ("IN_PLACE_OVERWRITE_DISABLED:v0302 只出候選夾與收據,不寫回原檔名;"
                 "要上線的改動照 VCGC 流程出新版號檔、註冊")
_ORIG = {k: getattr(V300, k) for k in ("selected_paths", "repair_environment", "audit_envs", "fusion", "RUNTIME_BRIDGE", "__file__")}


def owner_of(name: str, items: dict) -> str:
    """寫入擁有者:manifest items 有 system 就用它;否則看路徑。判不出 = UNKNOWN(唯讀)。"""
    if name in items:
        return str(items[name] or "UNKNOWN").upper()
    p = PurePosixPath(name.replace("\\", "/"))
    if "functional modules" in p.parts or p.name.upper().startswith(FOREIGN_PREFIXES):
        return "FOREIGN"
    return "VCGC" if "supportive modules" in p.parts or p.name.startswith(("VCGC_", "CGC_")) else "UNKNOWN"


LAST_READ_ONLY: list = []


def selected_paths(cfg: dict, fusion: bool = False):
    names, skip, authority = _ORIG["selected_paths"](cfg, fusion)
    if not fusion:
        return names, skip, authority                          # 盤點照舊(唯讀)
    root = V300.absolute(cfg["root"])
    mf = root / cfg.get("registered_manifest", "panorama.manifest.json")
    book = V300.load(mf) if mf.is_file() else {}
    items = {x["path"]: x.get("system", "VCGC") for x in book.get("items") or [] if isinstance(x, dict) and "path" in x}
    keep, ro = [], []
    for n in names:
        o = owner_of(n, items)
        if OWN_FAMILY.match(PurePosixPath(n).name):
            ro.append({"path": n, "owner": "VCGC_TOOL_SELF", "reason": "TOOL_FAMILY_NOT_A_TARGET"})
        elif o == "VCGC":
            keep.append(n)
        else:
            ro.append({"path": n, "owner": o, "reason": "FOREIGN_SYSTEM_READ_ONLY(交該系統 SystemManager)"})
    LAST_READ_ONLY[:] = ro
    return keep, skip, authority


def repair_environment(cfg: dict, spec: dict) -> dict:
    return {"status": "BLOCKED", "reason": "OPERATOR_APPROVAL_REQUIRED", "handoff": ENV_HANDOFF,
            "audit": {"path": str(spec.get("path", "")), "status": "BLOCKED"}}


def audit_envs(cfg: dict, repair: bool = False) -> dict:
    result = _ORIG["audit_envs"](cfg, repair=False)            # 一律只稽核
    if repair and result.get("status") != "PASS":
        result["repair_plan"] = {"status": "HANDOFF", "how": ENV_HANDOFF, "auto_repair": False}
    return result


def fusion(cfg: dict, apply: bool = False, retire: bool = False, offline: bool = False, prepared=None, prepared_hashes=None) -> dict:
    result = _ORIG["fusion"](cfg, False, retire, offline, prepared=prepared, prepared_hashes=prepared_hashes)
    result["read_only_foreign"] = list(LAST_READ_ONLY)
    if apply:
        result["apply_refused"] = APPLY_REFUSED
    if result.get("receipt"):
        V300.save(Path(result["receipt"]), result)
    return result


BRIDGE_OLD = '"VIA/PanoramaFusion/engine_config.json"'
BRIDGE_NEW = '"VIA/PanoramaFusion/engine_config_v0300.json"'


def install() -> None:
    V300.selected_paths = selected_paths
    V300.repair_environment = repair_environment
    V300.audit_envs = audit_envs
    V300.fusion = fusion
    V300.RUNTIME_BRIDGE = _ORIG["RUNTIME_BRIDGE"].replace(BRIDGE_OLD, BRIDGE_NEW)
    V300.__file__ = str(Path(__file__).resolve())              # 子行程(_lane · _contracts · _bridgeprobe)跑本檔


def uninstall() -> None:
    for k, v in _ORIG.items():
        setattr(V300, k, v)


install()


def selftest() -> int:
    ok = []

    def chk(label, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + label + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 6 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存夾 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路工具橋", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    with tempfile.TemporaryDirectory(prefix="pf302_") as td:
        root = Path(td)
        files = {"supportive modules/registry/CGC_X_v0100.py": "VCGC", "functional modules/VDF/VDF_Y_v0100.py": "VDF",
                 "supportive modules/z/VDF_Z_v0100.py": None, "supportive modules/VCGC_TokenSavingToolkit/v0300/VIA_PanoramaFusion_SuperEngine_v0399.py": None,
                 "other/unknown_v0100.py": None}
        for n in files:
            (root / n).parent.mkdir(parents=True, exist_ok=True)
            (root / n).write_text("x = 1\n", encoding="utf-8")
        items = [{"path": n, "system": s} for n, s in files.items() if s]
        V300.save(root / "panorama.manifest.json", {"include_files": list(files)})
        cfg = {"root": str(root), "fusion": {"include": ["*.py", "**/*.py"], "exclude": []}}
        w, _, _ = selected_paths(cfg, True)
        r, _, _ = selected_paths(cfg, False)
        V300.save(root / "panorama.manifest.json", {"items": items + [{"path": "other/unknown_v0100.py", "system": "VCGC"}]})
        w2, _, _ = selected_paths(cfg, True)
    chk("T2 (P1)寫入範圍只留 VCGC:functional modules/ · VDF_ 開頭 · 判不出擁有者 · 工具自己 → 唯讀;盤點照舊全看",
        w == ["supportive modules/registry/CGC_X_v0100.py"] and len(r) == 5
        and sorted(w2) == ["other/unknown_v0100.py", "supportive modules/registry/CGC_X_v0100.py"], (w, r, w2))
    seen = []
    _ORIG["audit_envs"], keep = (lambda cfg, repair=False: (seen.append(repair), {"status": "BLOCKED", "environments": []})[1]), _ORIG["audit_envs"]
    try:
        res = audit_envs({}, repair=True)
    finally:
        _ORIG["audit_envs"] = keep
    rep = repair_environment({}, {"path": "/x/env"})
    chk("T3 (P1)環境只稽核:audit_envs(repair=True) 實際以 repair=False 跑、附交接;repair_environment 一律 BLOCKED",
        seen == [False] and res.get("repair_plan", {}).get("auto_repair") is False and rep["status"] == "BLOCKED"
        and V300.audit_envs is audit_envs and V300.repair_environment is repair_environment, (seen, res, rep))
    calls = []
    _ORIG["fusion"], keepf = (lambda cfg, apply, retire, offline, prepared=None, prepared_hashes=None: (calls.append((apply, retire)), {"status": "READY", "applied": False})[1]), _ORIG["fusion"]
    try:
        fr = fusion({}, apply=True, retire=True)
    finally:
        _ORIG["fusion"] = keepf
    chk("T4 (P1)不覆寫原檔:fusion(apply=True) 實際以 apply=False 跑 · 收據寫 apply_refused · applied False",
        calls == [(False, True)] and fr.get("apply_refused") == APPLY_REFUSED and fr["applied"] is False and V300.fusion is fusion, (calls, fr))
    chk("T5 (P2)產生的橋退路 = engine_config_v0300.json(config() 預設建的那一個)",
        BRIDGE_NEW in V300.RUNTIME_BRIDGE and BRIDGE_OLD not in V300.RUNTIME_BRIDGE and BRIDGE_OLD in _ORIG["RUNTIME_BRIDGE"])
    chk("T6 子行程(三道 · _contracts · _bridgeprobe)跑本檔:v0300 的 __file__ 指到 v0302",
        Path(V300.__file__).resolve() == Path(__file__).resolve() and Path(_ORIG["__file__"]).name.endswith("_v0300.py"))
    uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        install()
    chk("T7 前版 v0301 自測照過(含 v0300 原有 107 項)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
