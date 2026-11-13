#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem_v0122 — 薄尾(v0100 … 前版 一字不動):自測在「缺 DuckDB」的環境照實標黃(SKIP_ENV),不再誤報紅。

操作員 2026-11-13:「修 CGC_MDL237 和 CGC_MDL278 紅燈」。
根因:Regex 候選的證明引擎是 DuckDB(CGC_MDL237 v0116 regex_check:duckdb 不在 → 'REGEX_PROOF_ENGINE_ABSENT',候選留 REVIEW、不發號、
不拿 re 冒充證明 —— 這個設計是對的)。但前版自測把「Regex 候選 READY」寫成必過條件,於是在沒裝 DuckDB 的環境(v0119 自測 ④ · ⑥c)必紅;
裝了 DuckDB 的機器(操作員桌機 duckdb 1.5.2)不受影響。
本版:`--selftest` 以子行程照跑前版全套自測(輸出原樣轉印),再判:
  · 前版 rc 0 → rc 0(綠)。
  · DuckDB 不在,而且失敗的只有已知依賴 DuckDB 的那幾項(v0119 自測 ④ · ⑥c),且失敗行都帶 REGEX_PROOF_ENGINE_ABSENT → 印 [SKIP_ENV],rc 2(黃 ≠ 綠;不代裝套件)。
  · 其他任何失敗 → rc 1(紅,照實)。
其餘動詞一律交前版(本行程載入;參數 / rc 不變)。零網路;不碰 TA-Lib;不寫任何冊。
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
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL237_NumberingSystem"
ENGINE = Path(__file__).stem
DUCKDB_DEPENDENT = {'④', '⑥c'}          # 前版自測裡依賴 DuckDB 正則證明的檢查編號


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def duckdb_present() -> bool:
    return importlib.util.find_spec("duckdb") is not None


def classify(rc: int, out: str, has_duckdb: bool) -> tuple:
    """(本版 rc, 說明)。純函式,自測直接測它。"""
    if rc == 0:
        return 0, "前版全綠"
    fails = [ln for ln in out.splitlines() if "[FAIL]" in ln]
    ids = {(ln.split("[FAIL]", 1)[1].strip().split() or ["?"])[0] for ln in fails}
    if fails and not has_duckdb and ids <= DUCKDB_DEPENDENT and all('REGEX_PROOF_ENGINE_ABSENT' in ln for ln in fails):
        return 2, "SKIP_ENV:DuckDB 不在 → %d 項正則證明檢查({})在本境無法執行;不冒充綠、不代裝".replace("{}", "·".join(sorted(ids))) % len(fails)
    return 1, "前版自測失敗:" + "、".join(sorted(ids)) if ids else "前版自測失敗(rc %d)" % rc


def selftest() -> int:
    cp = subprocess.run([sys.executable, str(PRIOR), "--selftest"], capture_output=True, text=True,
                        encoding="utf-8", errors="replace", env=os.environ.copy())
    sys.stdout.write(cp.stdout)
    sys.stderr.write(cp.stderr)
    rc, why = classify(cp.returncode, cp.stdout, duckdb_present())
    ok = []
    ok.append(classify(0, "", False)[0] == 0)
    ok.append(classify(1, "  [FAIL] ④ x · REGEX_PROOF_ENGINE_ABSENT", False)[0] == 2)
    ok.append(classify(1, "  [FAIL] ④ x · REGEX_PROOF_ENGINE_ABSENT", True)[0] == 1)
    ok.append(classify(1, "  [FAIL] ① 別的檢查", False)[0] == 1)
    ok.append(classify(1, "  [FAIL] ④ x\n  [FAIL] ① 別的", False)[0] == 1)
    tag = {0: "PASS", 2: "SKIP_ENV", 1: "FAIL"}[rc]
    if rc == 2:
        print("  [SKIP_ENV] " + why)
    mine = "本版判定 %d/5" % sum(ok)
    print("[計] %s · %s · 前版 rc %d · %s · %s" % (ENGINE, mine, cp.returncode, why, tag), flush=True)
    return rc if all(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args or args[:1] in (["selftest"], ["test"]):
        return selftest()
    return _PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())
