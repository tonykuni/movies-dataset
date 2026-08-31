#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_env_plan_v0103 — 環境暨安裝計畫引擎(TOOL-030;操作員令 2026-08-12)
==========================================================================
令:先寫計畫、先測可行、直到沒有風險才動手安裝。
方法(零風險三段):
  ① 快照 — 環境全景唯讀盤點(層/衝突/cv2 家族/關鍵庫/外部工具/模型快取/磁碟)
  ② 計畫 — 分段安裝計畫(每段:目標/理由/風險預判/候裁點)
  ③ 實測 — pip install --dry-run 只解析不落地,逐段實測可行性:
       · 會裝什麼、動到什麼版本,全數列示
       · 核心庫變版=HIGH 風險;cv2 家族再進入=RED(互撞回歸)
       · 已滿足=NOOP GREEN;解析失敗=誠實 FAIL
  裁決 GREEN 段才給執行令(via-install);YELLOW/RED 段列候裁,不代決
紅線:全程零安裝零落地;dry-run 需連 PyPI 解析=網路行為,過同意閘
     (VIA_NET_CONSENT;未同意=實測 NOT_RUN 誠實,快照+計畫照出)
v0100→v0101:cv2 統包版改錨 opencv-contrib-python(full;順 paddlex/
     img2table 相依鏈)——headless 進場改判 RED 回歸。
v0101→v0102:Top-10 工具強化令(2026-08-17)——+段 5~8 四批次
(靜態治理/契約測試/真實資料/Runtime 監控);快照關鍵庫擴列十件。
v0102→v0103:四層測試工具鏈令(2026-08-18)——+段 9 測試第一批必裝
+段 10 第二批整合(Pester 屬 PS 模組非 pip,候裁另軌誠實排除)。
用法:via-plan               → 快照+計畫+全段實測+裁決
     via-plan --offline     → 只快照+計畫(零網路)
     via-plan --stage 1     → 只實測第 N 段
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

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "envplan_runs"


def _via_load(name: str):
    try:
        sys.path.insert(0, str(VIA / "supportive modules"))
        from VRN_SupportBridge import require  # type: ignore
        return require(name)
    except Exception:
        try:
            import importlib
            sys.path.insert(0, str(VIA / "supportive modules"))
            return importlib.import_module(name)
        except Exception:
            return None


_NET = _via_load("VIA_NetSupport")
_ENVMGR = _via_load("VIA_EnvManager")  # 政策母版(graceful;儲存規定家族)


def _consent() -> bool:
    try:
        return bool(_NET and _NET.net_consent())
    except Exception:
        return False


# ── 風險規則 ─────────────────────────────────────────────────────
CORE_LIBS = {"numpy", "pandas", "duckdb", "paddlepaddle", "torch", "torchvision",
             "pyarrow", "pymupdf", "pypdfium2", "pillow"}
CV2_FAMILY = {"opencv-python", "opencv-python-headless",
              "opencv-contrib-python", "opencv-contrib-python-headless"}
KEEP_CV2 = "opencv-contrib-python"  # 統包版(順 paddlex/img2table 相依鏈錨定)

# ── 安裝計畫(現階段開口)────────────────────────────────────────
STAGES = [
    {"n": 1, "goal": "ppstructure 表格鏈附加依賴(PP-StructureV3 pipeline 缺件)",
     "pkgs": ["paddleocr[doc-parser]"],
     "why": "MQ-1560 掃描件表格中文視覺解析主力車道;pipeline creation 依賴錯誤之修",
     "watch": "恐拖入 opencv 家族/paddlex 大件——dry-run 先驗"},
    {"n": 2, "goal": "unstructured OCR 代理(OCRAgent 缺件)",
     "pkgs": ["unstructured.pytesseract"],
     "why": "unstructured 車道掃描件 OCR;另需 Tesseract 本體(外部安裝器,候裁)",
     "watch": "Tesseract 本體不在 pip 內——裝完仍需本體才會轉綠(誠實)"},
    {"n": 3, "goal": "docling 重量視覺車道(擇需)",
     "pkgs": ["docling"],
     "why": "IBM TableFormer 表格結構,第三條視覺車道交叉共識用",
     "watch": "重件(torch 家族已在應共用);首跑另下模型(同意閘)"},
    {"n": 4, "goal": "pypdf 版本選邊(候裁,預設不動)",
     "pkgs": ["pypdf<6"],
     "why": "camelot 要 <6、unstructured-client 要 >=6.2——同環境不可兼得;此段僅實測降級影響",
     "watch": "選 camelot=降級(unstructured-client 出衝突);選 unstructured=維持現狀——操作員裁"},
    {"n": 5, "goal": "Top-10 批次一:靜態治理",
     "pkgs": ["libcst", "networkx", "ruff", "bandit"],
     "why": "保格式重構/依賴 DAG/高速 lint/安全 AST——P1/P3/A01/A03/A04(SPEC-015)",
     "watch": "純 Python 輕件;libcst 有原生輪,dry-run 驗版本相容"},
    {"n": 6, "goal": "Top-10 批次二:契約與測試",
     "pkgs": ["pydantic", "pytest", "hypothesis"],
     "why": "契約驗證/測試基座/邊界案例生成——P2/P5/T2/T4/T5;契約引擎 v0200 依賴",
     "watch": "pydantic 恐已在(v2);hypothesis 輕件"},
    {"n": 7, "goal": "Top-10 批次三:真實資料",
     "pkgs": ["duckdb", "polars"],
     "why": "資料品質查核/高速增量管線——T3/T4/R06/VDF",
     "watch": "duckdb 已在(勿變版!核心庫變版=YELLOW 候裁);polars 原生輪較大"},
    {"n": 8, "goal": "Top-10 批次四:Runtime 監控",
     "pkgs": ["psutil"],
     "why": "Worker CPU/Memory/Heartbeat/資源洩漏——P4/A11/A18",
     "watch": "原生輪;輕件"},
    {"n": 9, "goal": "測試四層·第一批必裝",
     "pkgs": ["pytest-cov", "pytest-mock", "pytest-timeout", "freezegun", "pyfakefs",
              "jsonschema", "ruamel.yaml", "deepdiff", "filelock"],
     "why": "覆蓋率/Mock/卡死攔截/凍時/假檔系+SSOT Schema/YAML round-trip/漂移比對/單一寫者鎖",
     "watch": "全輕件;Pester=PowerShell 模組(Install-Module)非 pip——候裁另軌"},
    {"n": 10, "goal": "測試四層·第二批整合(擇需)",
     "pkgs": ["pytest-asyncio", "tox", "pytest-httpserver", "robotframework",
              "playwright", "watchdog", "rapidfuzz", "regex"],
     "why": "非同步/環境矩陣/本機 HTTP/端到端編排/UI 回歸/檔案監測/同義字比對",
     "watch": "playwright 瀏覽器另需 install(下載屬網路;同意閘);tox 建環境較重"},
]


def get_dists() -> dict[str, str]:
    from importlib.metadata import distributions
    out = {}
    for d in distributions():
        try:
            n = (d.metadata["Name"] or "").strip().lower()
            if n and n not in out:
                out[n] = d.version
        except Exception:
            continue
    return out


def snapshot() -> dict:
    import platform
    dists = get_dists()
    cv = {n: v for n, v in dists.items() if n in CV2_FAMILY}
    keys = ("paddleocr", "paddlex", "paddlepaddle", "torch", "torchvision", "easyocr",
            "unstructured", "unstructured-inference", "camelot-py", "pypdf", "img2table",
            "numpy", "pandas", "duckdb", "docling", "pi-heif",
            "libcst", "networkx", "ruff", "bandit", "pydantic", "pytest", "hypothesis",
            "polars", "psutil")
    key_vers = {k: dists.get(k, "—") for k in keys}
    tools = {t: bool(shutil.which(t)) for t in ("java", "tesseract")}
    caches = {c: (Path.home() / c).is_dir() and any((Path.home() / c).iterdir())
              for c in (".paddlex/official_models", ".EasyOCR", ".cache/docling")}
    try:
        free_gb = round(shutil.disk_usage(Path.home()).free / 1e9, 1)
    except Exception:
        free_gb = None
    try:
        r = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True, timeout=180)
        n_conf = 0 if r.returncode == 0 else len([l for l in r.stdout.splitlines() if l.strip()])
    except Exception:
        n_conf = None
    snap = {"python": platform.python_version(), "dists_total": len(dists), "pip_conflicts": n_conf,
            "cv2_family": cv, "key_libs": key_vers, "ext_tools": tools, "model_caches": caches,
            "disk_free_gb": free_gb, "envmgr_loaded": bool(_ENVMGR)}
    print(f"  [快照] Python {snap['python']} · 發行版 {len(dists)} · pip 衝突 {n_conf} 條 · 磁碟餘 {free_gb} GB")
    print(f"  [快照] cv2 家族:{', '.join(f'{k} {v}' for k, v in cv.items()) or '無'}")
    print("  [快照] 關鍵庫:" + " · ".join(f"{k} {v}" for k, v in key_vers.items() if v != "—"))
    print(f"  [快照] 外部工具:java={'在' if tools['java'] else '缺'} · tesseract={'在' if tools['tesseract'] else '缺'}"
          f" · 模型快取:paddle={'在' if caches['.paddlex/official_models'] else '缺'}"
          f" easyocr={'在' if caches['.EasyOCR'] else '缺'} docling={'在' if caches['.cache/docling'] else '缺'}")
    print(f"  [快照] EnvManager 母版:{'導入 OK' if _ENVMGR else '缺(graceful)'}")
    return snap


def dryrun_stage(stage: dict, dists: dict) -> dict:
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, "-m", "pip", "install", "--dry-run", "--user", *stage["pkgs"]],
                           capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"stage": stage["n"], "state": "NOT_RUN", "risk": "?", "note": "dry-run 逾時 600s(誠實)"}
    secs = round(time.time() - t0, 1)
    out = r.stdout + r.stderr
    if r.returncode != 0:
        tail = [l for l in out.strip().splitlines() if l.strip()][-2:]
        return {"stage": stage["n"], "state": "FAIL", "risk": "RED", "secs": secs,
                "note": "解析失敗:" + " / ".join(t[:90] for t in tail)}
    would = []
    for line in out.splitlines():
        if line.strip().startswith("Would install"):
            would = line.strip()[len("Would install"):].split()
    if not would:
        return {"stage": stage["n"], "state": "NOOP", "risk": "GREEN", "secs": secs,
                "note": "已全滿足——零變動(可能上輪已裝妥)"}
    risks = []
    for tok in would:
        name = tok.rsplit("-", 1)[0].lower()
        ver = tok.rsplit("-", 1)[-1]
        if name in CV2_FAMILY and name != KEEP_CV2:
            risks.append(f"RED:cv2 互撞回歸({tok})")
        elif name in CORE_LIBS and name in dists and dists[name] != ver:
            risks.append(f"HIGH:核心變版 {name} {dists[name]}→{ver}")
    risk = "GREEN"
    if any(x.startswith("RED") for x in risks):
        risk = "RED"
    elif risks:
        risk = "YELLOW"
    return {"stage": stage["n"], "state": "OK", "risk": risk, "secs": secs,
            "would_install": would, "risks": risks,
            "note": f"會裝 {len(would)} 件" + ("——" + ";".join(risks) if risks else "(無核心變版/無 cv2 回歸)")}


def main() -> int:
    args = sys.argv[1:]
    offline = "--offline" in args
    only = int(args[args.index("--stage") + 1]) if "--stage" in args else None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"=== 環境暨安裝計畫引擎 v0103 · {ts} · 零安裝零落地(先計畫先實測)===")
    print("── ① 環境快照(唯讀)──")
    snap = snapshot()
    dists = get_dists()
    print("── ② 安裝計畫(分段+風險預判)──")
    for st in STAGES:
        if only and st["n"] != only:
            continue
        print(f"  [段{st['n']}] {st['goal']}")
        print(f"     裝:{' '.join(st['pkgs'])} · 由:{st['why'][:60]}")
        print(f"     防:{st['watch'][:80]}")
    results = []
    if offline:
        print("── ③ 可行性實測:SKIP(--offline,零網路)──")
    elif not _consent():
        print("── ③ 可行性實測:NOT_RUN(dry-run 需連 PyPI 解析=網路行為,同意閘關)──")
        print("     同意後本視窗即時生效:$env:VIA_NET_CONSENT=\"YES\"")
    else:
        print("── ③ 可行性實測(pip --dry-run 只解析不落地)──")
        for st in STAGES:
            if only and st["n"] != only:
                continue
            r = dryrun_stage(st, dists)
            results.append(r)
            mark = {"OK": r["risk"], "NOOP": "GREEN", "FAIL": "RED", "NOT_RUN": "候"}[r["state"]]
            print(f"  [{mark:6s}] 段{r['stage']} · {r['note'][:110]} · {r.get('secs', '—')}s")
            for tok in r.get("would_install", [])[:12]:
                print(f"      + {tok}")
            if len(r.get("would_install", [])) > 12:
                print(f"      …共 {len(r['would_install'])} 件(全清單見存證)")
    print("── ④ 裁決──")
    greens = [r["stage"] for r in results if r.get("risk") == "GREEN"]
    yellows = [r["stage"] for r in results if r.get("risk") == "YELLOW"]
    reds = [r["stage"] for r in results if r.get("risk") == "RED" or r["state"] == "FAIL"]
    if results:
        print(f"  GREEN 段 {greens or '無'} · YELLOW 候裁 {yellows or '無'} · RED 禁行 {reds or '無'}")
        for n in greens:
            st = next(s for s in STAGES if s["n"] == n)
            print(f"  [執行令] via-install {' '.join(chr(34) + p + chr(34) if '[' in p or '<' in p else p for p in st['pkgs'])}")
        if yellows or reds:
            print("  [候裁] YELLOW/RED 段不代決——貼回實測結果由操作員裁")
    else:
        print("  實測未跑(offline/同意閘)——計畫已列,可行性待測")
    OUT.mkdir(parents=True, exist_ok=True)
    ev = OUT / f"PLAN_{ts}.json"
    ev.write_text(json.dumps({"schema": "VIA.EnvPlan.v1", "ts": ts, "snapshot": snap,
                              "stages": STAGES, "dryrun": results,
                              "policy": "zero_install·dryrun_only·consent_gated·green_only_commands"},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存證] {ev.relative_to(VIA)}")
    return 0 if not reds else 1


if __name__ == "__main__":
    sys.exit(main())
