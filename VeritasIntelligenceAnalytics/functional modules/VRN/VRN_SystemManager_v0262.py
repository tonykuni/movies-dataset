#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VRN-2 SystemManager v0262 — 薄尾(前版 = v0261 · 一字不改)。provenance 動詞放回自測攔截之前(2026-11-06 · Codex PR #602 P2)。

為什麼要這一版:交接案 provenance(`VRN_SystemManager provenance --selftest` · 標記「[來源回歸] fail=0」)的來源回歸
(tests/test_SourceProvenance_v0100.py · 經 VRN_ENG114_SourceProvenance 尾版)自 v0239 起從沒跑到:v0239 / v0242 / v0244 … 各版
main 開頭以 `"--selftest" in args[:2]` 攔自測,v0249 / v0254 / v0256 / v0261 再在 `__main__` 以 `"--selftest" in sys.argv` 攔一次,
`provenance --selftest` 被吃成管理器自測鏈(v0152 曾修過一次,之後的版又蓋回去)。2026-11-06 交接冊一度把該案標記改認管理器自測
判決行 —— 那是拿不相干的 PASS 當來源回歸證據(Codex P2 抓到)。本版把它修回去:

  · args[0] == "provenance" → 先直送 VRN_ENG114_SourceProvenance 尾版(引數照傳;`--selftest` = 跑 tests/test_SourceProvenance_v0100,
    印「[來源回歸] fail=N; tests=M」);管理器自己的攔截放在它後面。`provenance --selftest` 在來源回歸之後**再**跑本版管理器自測
    (CI「VRN-2 manager contracts through its own MAIN」沿用同一行指令 → 兩段判決行都印;回傳碼 = 兩段取大)。
  · 其餘動詞(logic / completion / collect / read / --selftest …)一字不改照 v0261。
  · 直送引擎時 VIA_FROM_VCGC 沒設就 setdefault("YES")(同 v0152;ENG114 的 [DENY] 守門是對外來呼叫,管理器是 VRN-2 自己的入口)。
  · 號:v0262 由本夾用掉;VRN-2 私有 runtime 線(ActivateVRN-2 · 桌機 functional modules\VRN2)下一個管理器號從 v0263 起。
自測:python VRN_SystemManager_v0262.py --selftest(= v0261 自測 + 本版 5 項 · 零網路 · 不寫檔)。
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

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "v0262"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0261.py"
ENGINE_STEM = "VRN_ENG114_SourceProvenance"
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.exists():
    raise FileNotFoundError("前版 %s 不在 · v0262 不接" % PRIOR_NAME)
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0262", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in vars(PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name):
    return getattr(PRIOR, name)


def collect() -> dict:
    """VCGC 子系統對接口(照 v0261 · 只讀)· served_by 記本版。"""
    out = PRIOR.collect()
    if isinstance(out, dict):
        out = dict(out)
        sb = dict(out.get("served_by") or {})
        sb["tail"] = "VRN_SystemManager_" + TAG
        out["served_by"] = sb
    return out


def read(domain: str, key: str | None = None, full: bool = False) -> dict:
    """VCGC 子系統對接口 read(照 v0261 · 只讀)。"""
    return PRIOR.read(domain, key, full)


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def provenance_engine_path() -> Path:
    """VRN_ENG114 來源證據引擎尾版(版號最大)。"""
    return max(HERE.glob(ENGINE_STEM + "_v*.py"), key=_vnum)


def _load_engine(path: Path):
    name = "_vrn_provenance_engine_for_" + TAG
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


def provenance(args: list) -> int:
    """provenance 動詞:直送 ENG114 尾版(來源回歸 / 來源驗證);`--selftest` 之後再跑本版管理器自測,回傳碼取大。"""
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    engine = _load_engine(provenance_engine_path())
    rc = int(engine.main(list(args)) or 0)
    if "--selftest" in args:
        print("  ── 來源回歸之後:本版管理器自測(CI「VRN-2 manager contracts through its own MAIN」同一行)──", flush=True)
        rc = max(rc, int(selftest() or 0))
    return rc


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["provenance"]:            # v0262:放在任何 --selftest 攔截之前
        return provenance(args[1:])
    if args == ["--selftest"] or "--selftest" in args[:1]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    from unittest.mock import Mock, patch
    print("[計] %s %s 自測開始(前版鏈先跑 · 再本版 5 項)" % (DISPLAY_NAME, TAG), flush=True)
    prior_rc = PRIOR.selftest()
    me = sys.modules[__name__]
    fake = Mock()
    fake.main.return_value = 23
    with patch.object(me, "_load_engine", Mock(return_value=fake)), patch.object(me, "selftest", Mock(return_value=0)) as st:
        rc1 = main(["provenance", "--selftest"])
    with patch.object(me, "_load_engine", Mock(return_value=fake)), patch.object(me, "selftest", Mock(return_value=0)) as st2:
        rc2 = main(["provenance", "--report", "r", "--source", "s", "--out", "o"])
    with patch.object(PRIOR, "main", Mock(return_value=7)) as pm:
        rc3 = main(["status"])
    text = Path(__file__).read_text(encoding="utf-8")
    checks = [("① provenance --selftest 先直送來源引擎(引數 ['--selftest'] · 引擎回傳碼 23 照帶)· 之後才跑管理器自測(叫到 1 次)",
               rc1 == 23 and fake.main.call_args_list[0].args[0] == ["--selftest"] and st.call_count == 1),
              ("② provenance 其他引數直送引擎(--report/--source/--out)· 不跑管理器自測",
               rc2 == 23 and fake.main.call_args_list[1].args[0] == ["--report", "r", "--source", "s", "--out", "o"] and st2.call_count == 0),
              ("③ 其他動詞照前版鏈(status → v0261 main)", rc3 == 7 and pm.call_args.args[0] == ["status"]),
              ("④ 來源引擎尾版找得到 · 其 selftest 載的是 tests/test_SourceProvenance_v0100.py",
               provenance_engine_path().is_file() and "test_SourceProvenance_v0100.py" in provenance_engine_path().read_text(encoding="utf-8")),
              ("⑤ 檔面 def main / def selftest / def collect · 第 3 行加速器標記 · __main__ 的 provenance 守門在 --selftest 攔截之前",
               "\ndef main(" in text and "\ndef selftest(" in text and "\ndef collect(" in text and text.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]"
               and text.index('sys.argv[1:2] == ["provenance"]') < text.index('"--selftest" in sys.argv:'))]
    bad = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(("  [OK] " if ok else "  [FAIL] ") + name, flush=True)
    chain = [TAG] + list(PRIOR._chain())
    print("[計] VRN-2 SystemManager v0262(VRN_SystemManager_v0262.py)自測 %d/%d · %s · 前版鏈 rc %d · 鏈 %s" % (
        len(checks) - len(bad), len(checks), "PASS" if not bad and prior_rc == 0 else "FAIL", prior_rc, "→".join(chain[:10])), flush=True)
    return 0 if not bad and prior_rc == 0 else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["provenance"]:     # v0262:provenance 先於任何 --selftest 攔截
        sys.exit(provenance(sys.argv[2:]))
    if "--selftest" in sys.argv:           # 同 v0261:純 --selftest 進本版自測
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))
