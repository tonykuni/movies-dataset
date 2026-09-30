#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""panorama-matrix 技能入口 — 轉交釘版引擎 VIA_Panorama_v0101.py(薄尾;本體 v0100;同一支程式,不另抄一份)。

為什麼是轉交而不是單檔全文:引擎本體 1600 行;技能夾再放一份 = 兩份會漂(VIA 整合去重律)。
本檔只做三件事:①找引擎(釘版,不自己取尾版)②`--profile <名>` 先對到本技能的 profiles/<名>.json ③原樣轉交參數與結束碼。
找引擎的順序:環境變數 VIA_PANORAMA_ENGINE → 從本檔與目前目錄往上找
  VeritasIntelligenceAnalytics/supportive modules/registry/VIA_Panorama_v0101.py。找不到 = ABSENT,結束碼 3(不猜、不下載)。
換引擎版號:改下面 ENGINE_NAME 一行(並跑 evals/run_evals.py)。
用法同引擎:panorama_matrix.py <目標> [--profile 名|檔] [--scope …] [--static] [--out 夾] [--top N] [--width N] [--json-only] [--no-git] …
          panorama_matrix.py show <A–H|history> · panorama_matrix.py --selftest
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ENGINE_NAME = "VIA_Panorama_v0101.py"  # 薄尾:本體 v0100 原樣載入 + dashboard / watch
ENGINE_REL = Path("VeritasIntelligenceAnalytics") / "supportive modules" / "registry" / ENGINE_NAME
SKILL = Path(__file__).resolve().parents[1]


def find_engine() -> Path | None:
    env = os.environ.get("VIA_PANORAMA_ENGINE")
    if env and Path(env).is_file():
        return Path(env)
    for start in (Path(__file__).resolve(), Path.cwd().resolve()):
        for d in (start, *start.parents):
            if (d / ENGINE_REL).is_file():
                return d / ENGINE_REL
    return None


def map_profile(argv: list) -> list:
    out = list(argv)
    if "--profile" in out:
        i = out.index("--profile")
        if i + 1 < len(out):
            p = SKILL / "profiles" / f"{out[i + 1]}.json"
            if p.is_file():
                out[i + 1] = str(p)
    return out


def main() -> int:
    eng = find_engine()
    if eng is None:
        print(f"[panorama-matrix] 引擎 ABSENT:找不到 {ENGINE_REL}(設 VIA_PANORAMA_ENGINE=<路徑>)")
        return 3
    return subprocess.run([sys.executable, str(eng), *map_profile(sys.argv[1:])]).returncode


if __name__ == "__main__":
    raise SystemExit(main())
