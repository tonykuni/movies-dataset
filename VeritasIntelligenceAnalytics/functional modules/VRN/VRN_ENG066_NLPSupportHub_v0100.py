#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG066_NLPSupportHub — NLP 工具統一整合×Summarizer 支援樞紐(批157;via-nlphub)
====================================================================
操作員令:將所有 NLP 工具整合在一起支援 VRN Summarizer。
去重紅線:引擎不重造、正本零觸碰——本器=統一門面,底層全複用:
  正規化/實體/三元組 = VRN_ENG064 KnowledgeStack(glob 尾版;
    批152 正主 npl_preprocessor 優先+批141 知識堆疊三引擎)
  分詞 = LocalKnowledgePipeline.segment(jieba 道)
  財務詞彙 = vrn_finlex(glob 尾版;八源字庫)
  摘要核心 = VRN_ENG062 SummarizerV1(唯讀消費,ExtractiveSummarizer)
支援面(Summarizer 消費之三 API):
  enrich_for_summary(text)  前處理包:正規化文+實體+三元組+關鍵詞
    +錨定選句(實體×三元組密度)+數字清單 → 摘要引擎的錨
  verify_summary(summary, source)  摘要誠實閘:摘要中數字/百分比/
    實體逐一回源驗證 → ungrounded 清單(「AI 只整理不發明」的 NLP 化)
  support_summarizer(text)  端到端:enrich→ENG062 五點摘要→verify
    →增強摘要包(bullets+實體錨+三元組要點+誠實驗證)
用法:via-nlphub [--text T|--demo] [--json] | --selftest
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
from pathlib import Path

HERE = Path(__file__).resolve().parent

_NUM_RX = re.compile(r"[+-]?\d[\d,]*(?:\.\d+)?\s*[%％]?")
_SENT_RX = re.compile(r"(?<=[。!?!?])\s*")


def _load_latest(pattern: str, name: str):
    """glob 尾版動態載入(嚴禁寫死版號;缺席=None 誠實)"""
    hits = sorted(HERE.glob(pattern))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location(name, hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


_STACK = None   # ENG064 模組(內含 load_stack→npl_preprocessor 正主+堆疊)
_PIPE = None    # LocalKnowledgePipeline 實例


def _knowledge():
    """NLP 底盤:ENG064 尾版→堆疊管線(正主優先;一次載入全域複用)"""
    global _STACK, _PIPE
    if _PIPE is not None:
        return _PIPE
    _STACK = _load_latest("VRN_ENG064_KnowledgeStack_v*.py", "via_eng064_dyn")
    if _STACK is None:
        raise RuntimeError("ENG064 缺席(NLP 底盤)")
    stack = _STACK.load_stack()
    if stack is None:
        raise RuntimeError("知識堆疊收容原件缺")
    _PIPE = stack["local_knowledge_engine"].LocalKnowledgePipeline()
    return _PIPE


def _finlex_terms() -> set:
    """財務字庫詞面(finlex 尾版;缺席=空集誠實)"""
    fl = _load_latest("vrn_finlex_v*.py", "via_finlex_dyn")
    if fl is None:
        return set()
    for attr in ("load_lexicon", "lexicon", "build_lexicon"):
        try:
            obj = getattr(fl, attr, None)
            data = obj() if callable(obj) else obj
            if isinstance(data, dict):
                out = set()
                for v in data.values():
                    if isinstance(v, (list, set, tuple)):
                        out |= {str(x) for x in v if isinstance(x, str)}
                    elif isinstance(v, dict):
                        out |= {str(k) for k in v}
                if out:
                    return out
        except Exception:
            continue
    return set()


# ---------------------------------------------------------------- 門面 API
def normalize(text: str) -> str:
    return _knowledge().normalizer.normalize(text)


def analyze(text: str) -> dict:
    """正規化+實體+三元組+圖(ENG064 analyze 同構,經統一管線)"""
    return _knowledge().analyze(text)


def segment(text: str) -> list:
    return _knowledge().segment(text, backend="auto")


def enrich_for_summary(text: str, top_sentences: int = 5) -> dict:
    """Summarizer 前處理包:錨定選句=實體+三元組命中密度(零固定門檻,
    取密度排序前 N);數字清單=誠實閘之比對基底"""
    r = analyze(text)
    norm = r["normalized_text"]
    ents = r["parsed"].get("entities", [])
    triples = r["triples"]
    sentences = [s for s in _SENT_RX.split(norm) if s.strip()]
    ent_texts = [e["text"] for e in ents]
    trip_texts = {t["subject"] for t in triples} | {t["object"] for t in triples}
    scored = []
    for s in sentences:
        density = sum(1 for e in ent_texts if e in s) + \
            sum(1 for t in trip_texts if t and t in s)
        scored.append((density, s))
    key_sents = [s for d, s in sorted(scored, key=lambda x: -x[0])[:top_sentences] if d > 0]
    lex = _finlex_terms()
    seg = segment(norm)
    keywords = sorted({w for w in seg if w in lex} | {e["text"] for e in ents
                                                     if e.get("label") == "INDICATOR"})
    return {"normalized_text": norm, "entities": ents, "triples": triples,
            "key_sentences": key_sents, "keywords": keywords,
            "numbers": _NUM_RX.findall(norm),
            "graph": r.get("graph"), "backend": r["parsed"].get("backend")}


def verify_summary(summary_text: str, source_text: str) -> dict:
    """摘要誠實閘:摘要中每一數字/百分比與 INDICATOR/ORG 實體須回源可證;
    ungrounded 非空=摘要含源文沒有的數字/實體(「只整理不發明」NLP 化)"""
    norm_sum = normalize(summary_text)
    norm_src = normalize(source_text)
    src_nums = {n.replace(",", "").replace(" ", "").replace("％", "%")
                for n in _NUM_RX.findall(norm_src)}
    checked, ungrounded = [], []
    for n in _NUM_RX.findall(norm_sum):
        key = n.replace(",", "").replace(" ", "").replace("％", "%")
        checked.append(n)
        if key not in src_nums:
            ungrounded.append({"kind": "number", "value": n})
    ents_sum = _knowledge().preprocessor.process(norm_sum).get("entities", [])
    for e in ents_sum:
        if e.get("label") in ("INDICATOR", "POLICY_ORG") and e["text"] not in norm_src:
            ungrounded.append({"kind": e["label"], "value": e["text"]})
    return {"numbers_checked": len(checked),
            "entities_checked": len(ents_sum),
            "ungrounded": ungrounded,
            "grounded_ok": not ungrounded}


def _summarizer():
    """ENG062 摘要核心(唯讀消費;正本零觸碰)"""
    m = _load_latest("VRN_ENG062_SummarizerV1.py", "via_eng062_dyn")
    if m is None or not hasattr(m, "ExtractiveSummarizer"):
        return None
    return m.ExtractiveSummarizer()


def support_summarizer(text: str, bullets: int = 5) -> dict:
    """端到端:NLP 前處理→ENG062 五點摘要→誠實閘→增強摘要包"""
    enr = enrich_for_summary(text)
    eng = _summarizer()
    if eng is not None:
        summary = eng.summarize(enr["normalized_text"], num_sentences=bullets)
        engine = "VRN_ENG062.ExtractiveSummarizer"
    else:
        summary = enr["key_sentences"][:bullets]  # 誠實後備=錨定選句
        engine = "FALLBACK_key_sentences(ENG062 缺席)"
    ver = verify_summary("。".join(summary), text)
    triple_points = [f"{t['subject']}→{t['predicate']}→{t['object']}"
                     for t in enr["triples"][:5]]
    return {"engine": engine, "summary_bullets": summary,
            "entity_anchors": [e["text"] for e in enr["entities"]][:12],
            "triple_points": triple_points, "keywords": enr["keywords"][:12],
            "verification": ver, "backend": enr["backend"]}


DEMO = ("2026年Q1,受房地產市場波動影響,其 NPL Ratio 攀升至 1.85%。"
        "為防範風險,金管會要求將備抵呆帳覆蓋率提升至150%。"
        "台積電第三季毛利率創高,分析師目標價中位數上修。")


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① NLP 工具鏈在位(ENG064/062/finlex glob 尾版)",
        bool(sorted(HERE.glob("VRN_ENG064_KnowledgeStack_v*.py"))
             and sorted(HERE.glob("VRN_ENG062_SummarizerV1.py"))
             and sorted(HERE.glob("vrn_finlex_v*.py"))))

    n = normalize("２０２６年Ｑ１ 备抵呆账覆盖率")
    chk("② 正規化統一道(全形→半形+簡→繁)",
        "2026年Q1" in n and ("備抵呆帳" in n or "備抵呆賬" in n), f"({n[:20]})")

    enr = enrich_for_summary(DEMO)
    kinds = {t["attributes"].get("type") for t in enr["triples"]}
    chk("③ 前處理包三元組三型齊",
        {"metric_change", "causation", "policy_action"} <= kinds)
    chk("④ 錨定選句(實體×三元組密度)+數字清單",
        len(enr["key_sentences"]) >= 2 and "1.85%" in "".join(enr["numbers"])
        and any("NPL" in s for s in enr["key_sentences"]))
    chk("⑤ 關鍵詞(實體 INDICATOR∪字庫命中)",
        any("NPL" in k or "毛利率" in k or "覆蓋率" in k for k in enr["keywords"]),
        f"({enr['keywords'][:4]})")

    good = verify_summary("NPL Ratio 攀升至 1.85%,金管會要求覆蓋率 150%。", DEMO)
    bad = verify_summary("NPL Ratio 攀升至 9.99%,聯準會出手。", DEMO)
    chk("⑥ 摘要誠實閘(真摘要過)", good["grounded_ok"])
    chk("⑦ 摘要誠實閘(發明數字 9.99% 必攔)",
        not bad["grounded_ok"]
        and any(u["value"].startswith("9.99") for u in bad["ungrounded"]
                if u["kind"] == "number"))

    r = support_summarizer(DEMO, bullets=3)
    chk("⑧ 端到端(ENG062 掛接+增強包+驗證)",
        len(r["summary_bullets"]) >= 1 and r["triple_points"]
        and "verification" in r and "ENG062" in r["engine"],
        f"(engine={r['engine'][:32]})")

    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 去重紀律宣告(引擎不重造/正本零觸碰/glob 尾版)",
        all(k in src for k in ("引擎不重造", "正本零觸碰", "glob 尾版")))
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== NLP 支援樞紐(VRN_ENG066)· 九檢自測(零網路)===")
        return selftest()
    text = DEMO if "--demo" in args else None
    if "--text" in args:
        text = args[args.index("--text") + 1]
    if text is None:
        print(__doc__.split("用法:")[1])
        return 0
    r = support_summarizer(text)
    if "--json" in args:
        print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
    else:
        print(f"[引擎] {r['engine']} · backend={r['backend']}")
        for b in r["summary_bullets"]:
            print(f"  • {b}")
        print(f"[實體錨] {'、'.join(r['entity_anchors'][:8])}")
        for t in r["triple_points"]:
            print(f"[三元組] {t}")
        v = r["verification"]
        print(f"[誠實閘] 數字 {v['numbers_checked']} 查核 · "
              f"{'全回源可證' if v['grounded_ok'] else '未證:' + str(v['ungrounded'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
