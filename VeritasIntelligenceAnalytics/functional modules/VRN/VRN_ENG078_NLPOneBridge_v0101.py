#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG078_NLPOneBridge — NLP OneEngine 收容橋(批283;操作員令)
====================================================================
操作員令:「將所有類似的引擎分類整合簡化 功能更多」+ NLP OneEngine
v1.5.0 收容包。收容律=原件不動,本橋駕馭:
  ①尾版掛載:intake 夾內 VIA_NLP_OneEngine_v* 語意版號排序取尾
    (GLE 字母序陷阱教訓=_ver 語意比較)→ src 入 sys.path
  ②probe:35 模組冊(v1.5.0 排除 __init__ 實數)+選配依賴誠實矩陣(fastapi/torch 等缺=降級
    lane 如實標,不假綠)
  ③分類整合:模組→八功能類歸類冊;與既有 NLP 家族(ENG073
    TextProcessor 等)登整併冊 CANDIDATE_MERGE(不失功能重新註冊
    =候操作員裁示,零破壞)
  ④run 輕測:離線正道真跑(config 自解 lexicon→TextProcessor
    normalize+chunk;零 LLM 零網路)
紅線:零網路(LLM/model_pool lane 不啟動);原件唯讀。
用法:python3 VRN_ENG078_NLPOneBridge_v0101.py probe|run|--selftest
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
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
INTAKE = HERE / "references" / "intake" / "VIA_NLP_OneEngine_b283"
CONS = (VIA / "supportive modules" / "registry"
        / "VIA_Engine_Consolidation_Register_v0100.json")

# 八功能類歸類冊(分類整合=模組→類;零發明,依模組名職責)
CLASSES = {
    "text": ["text_ops", "discourse", "context_reconstruction"],
    "layout": ["layout_analysis", "template_reconstruction"],
    "translate": ["translation"],
    "knowledge": ["knowledge", "knowledge_body_ops", "mindmap_evolution"],
    "code": ["code_restoration", "code_reconstruction"],
    "learn": ["learning", "function_classifier", "evaluation"],
    "orchestrate": ["engine", "routing", "jobs", "cli", "api",
                    "instruction_ops", "discussion_ops"],
    "infra": ["config", "cache", "audit", "resources", "schemas",
              "adapters", "model_pool", "ingest"],
}
OPTIONAL_DEPS = ("fastapi", "torch", "transformers", "onnxruntime")


def _ver(p: Path) -> tuple:
    m = re.search(r"v(\d+)\.(\d+)\.(\d+)", p.name)
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


def _tail() -> Path | None:
    hits = sorted((d for d in INTAKE.glob("VIA_NLP_OneEngine_v*")
                   if d.is_dir()), key=_ver)
    return hits[-1] if hits else None


def _mount():
    t = _tail()
    if not t:
        return None
    src = str(t / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    return t


def probe() -> dict:
    t = _mount()
    if not t:
        return {"ok": False, "err": "intake 缺=誠實停"}
    mods = sorted(p.stem for p in (t / "src" / "via_nlp_engine")
                  .glob("*.py") if p.stem != "__init__")
    classified = {k: [m for m in v if m in mods]
                  for k, v in CLASSES.items()}
    un = [m for m in mods
          if not any(m in v for v in CLASSES.values())]
    deps = {d: importlib.util.find_spec(d) is not None
            for d in OPTIONAL_DEPS}
    return {"ok": True, "tail": t.name, "n_mods": len(mods),
            "classes": classified, "unclassified": un,
            "optional_deps": deps,
            "degraded": [d for d, ok in deps.items() if not ok]}


def register_merge() -> str:
    """整併冊登記:NLP 家族 CANDIDATE_MERGE(append-only;冪等)"""
    if not CONS.exists():
        return "冊缺=誠實略"
    d = json.loads(CONS.read_text(encoding="utf-8"))
    key = "nlp_one_vs_eng073_family_b283"
    lst = d.setdefault("candidate_merges_b256", []) \
        if isinstance(d.get("candidate_merges_b256"), list) else \
        d.setdefault("candidates", [])
    if any(isinstance(e, dict) and e.get("key") == key for e in lst):
        return "SKIP_IDENTICAL"
    lst.append({"key": key, "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "family": "NLP 文字處理",
                "members": ["VIA_NLP_OneEngine v1.5.0(收容;36 模組)",
                            "VRN_ENG073 TextProcessor+ssot_lexicon(現役)",
                            "NLP 正主(批152)"],
                "rule": "不失功能重新註冊;候操作員裁示,零破壞"})
    CONS.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    return "REGISTERED"


def run() -> int:
    p = probe()
    if not p["ok"]:
        print(f"[NLP橋] {p['err']}")
        return 2
    from via_nlp_engine.config import load_config
    from via_nlp_engine.text_ops import TextProcessor, chunk_text
    cfg = load_config(None)
    tp = TextProcessor(cfg["engine"]["lexicon_path"])
    sample = "　ＶＩＡ全形　文字  多空白　測試"
    norm = tp.normalize(sample)
    chunks = list(chunk_text("字" * 500, 120, overlap=20))  # 產生器實體化;overlap<max_chars 守衛
    reg = register_merge()
    print(f"[NLP橋] {p['tail']} · 模組 {p['n_mods']}(八類歸畢,"
          f"未類 {len(p['unclassified'])})· 降級 lane:"
          f"{','.join(p['degraded']) or '無'} · normalize "
          f"'{sample[:6]}…'→'{norm[:10]}…' · chunk {len(chunks)} 段 · "
          f"整併冊 {reg}")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    p = probe()
    chk("① 收容在位+語意尾版(v1.5.0>v1.1.0;manifest 存證)",
        p.get("tail") == "VIA_NLP_OneEngine_v1.5.0"
        and (INTAKE / "_INTAKE_MANIFEST.json").exists())
    chk("② 35 模組全歸類精確釘數(v1.5.0 排 __init__;八類+未類守恆)",
        p.get("n_mods", 0) == 35
        and sum(len(v) for v in p["classes"].values())
        + len(p["unclassified"]) == p["n_mods"])
    chk("③ 選配依賴誠實矩陣(缺=降級 lane 如實標)",
        set(p["optional_deps"]) == set(OPTIONAL_DEPS))
    rc = run()
    chk("④ 離線正道真跑(config 自解 lexicon+normalize+chunk)",
        rc == 0)
    d = json.loads(CONS.read_text(encoding="utf-8")) if CONS.exists() else {}
    flat = json.dumps(d, ensure_ascii=False)
    chk("⑤ 整併冊登記(NLP 家族 CANDIDATE_MERGE 冪等)",
        "nlp_one_vs_eng073_family_b283" in flat
        and run() == 0)                        # 再跑=SKIP 冪等仍 rc0
    chk("⑥ 紅線(零網路 lane+原件唯讀宣告)+加速橋",
        "零網路" in src and "原件" in src and "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== NLP OneEngine 收容橋(VRN_ENG078)· 六檢自測(零網路)===")
        return selftest()
    if "probe" in a:
        print(json.dumps(probe(), ensure_ascii=False, indent=1)[:1500])
        return 0
    return run()


if __name__ == "__main__":
    sys.exit(main())
