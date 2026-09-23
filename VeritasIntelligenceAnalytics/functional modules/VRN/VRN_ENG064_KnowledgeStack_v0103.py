#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v0102→v0103(批689B 缺件不是壞掉 L16):⑦ jieba 不在=NODATA(不代裝)· ⑧ pytest 不在=NODATA(不代裝);裝了才真驗。

VRN_ENG064_KnowledgeStack — 本地知識抽取堆疊轉接 v0101(批152;via-know)
====================================================================
批141 收容三引擎(local_knowledge_cli/engine+knowledge_extraction_engine
=CPU 本地中文金融三元組抽取;十庫選配全後備)於
new modules engines/VIA_KnowledgeStack_Batch141/。
批152 升級:npl_preprocessor **正主件**隨 local_nlp_stack_upgrade 送達
(byte-exact 收容 new modules engines/VIA_NLPStackUpgrade_Batch152/),
本版載入序改為:①正主件優先(檔案級動態載入,原件零觸碰)
②正主缺席才退 v0100 記憶體級補殼(誠實後備,行為不變):
  LanguageNormalizer=NFKC 全形轉半形+OpenCC 簡繁(缺=誠實直通旗標)
  NLPPreprocessor=分句+規則實體(INDICATOR/ORG/PERCENT/DATE/CONCEPT;
  spaCy 缺=正主自身規則後備/補殼規則道,裝中文模型即自動升級)
環境:jieba+opencc(純 Python 版)已裝;rapidfuzz/sklearn 原生;
pkuseg/dateparser/quantulum3/networkx 缺=送達件自身後備覆蓋。
用法:via-know [--text T|--demo] [--json] | --selftest
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
import subprocess
import sys
import types
import unicodedata
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
INTAKE = VIA / "new modules engines" / "VIA_KnowledgeStack_Batch141"
INTAKE152 = (VIA / "new modules engines" / "VIA_NLPStackUpgrade_Batch152"
             / "local_nlp_stack_upgrade")

_ORG_SUFFIX = ("會", "局", "署", "部", "銀行", "公司", "集團", "央行", "基金會")
_ORG_KNOWN = ("金管會", "央行", "主計總處", "Fed", "ECB", "日銀", "人行")
_INDICATOR_WORDS = ("NPL Ratio", "不良貸款率", "備抵呆帳覆蓋率", "備抵呆賬覆蓋率",
                    "覆蓋率", "資本適足率", "殖利率", "本益比", "毛利率", "營益率",
                    "EPS", "ROE", "ROA", "負債比")
_PCT_RX = re.compile(r"[+-]?\d[\d,]*(?:\.\d+)?\s*[%％]")
_DATE_RX = re.compile(r"(?:19|20)\d{2}\s*年(?:\s*Q[1-4]|\s*[01]?\d\s*月)?|Q[1-4]")
_CONCEPT_RX = re.compile(r"[一-鿿]{2,6}(?:市場波動|危機|風險|衝擊|疑慮|循環)")
# ═══ 批611:零依賴簡→繁後備(工作站實錄修)═══════════════════════════════
# 病根實錄:工作站沒裝 opencc → 收容正主 LanguageNormalizer 煙測 raise →
# `except Exception: return None` → 退回補殼 → 補殼 `self._cc = None` **直通不轉** →
# 简体原樣輸出。一支補殼扛三站(ENG064 ② · ENG066 ② · ENG067 ③)全紅。
# 容器裝了 opencc,所以**只走過裝了的那一半路**,三站一直是假綠(L83 第二次現身)。
#
# 補法不是叫操作員裝套件(那是他的手),是給補殼一條零依賴的路:
#   opencc 在 → 照用 opencc(行為零變更)
#   opencc 缺 → 用凍結對照表(逐字元實跑 opencc s2twp 量出來的 2,784 筆,零發明)
# **字元層**補得起來;**片語層**台灣用詞(軟件→軟體 這一類)補不起來,
# 所以 zh_which() 要說得出走的是哪條路,缺片語層要誠實講,不得假裝轉完了。
_ZH_MAP_NAME = "VIA_ZhConvert_S2TWP_CharMap_v0100.json"
_ZH_MAP: dict | None = None
_ZH_MAP_WHY = ""


def _zh_map() -> dict:
    """凍結對照表(懶載;缺冊=空表+留因由,不拋例外)"""
    global _ZH_MAP, _ZH_MAP_WHY
    if _ZH_MAP is not None:
        return _ZH_MAP
    via = Path(__file__).resolve()
    while via.parent != via and not (via / "supportive modules").is_dir():
        via = via.parent
    cand = [via / "supportive modules" / "registry" / _ZH_MAP_NAME,
            Path(__file__).resolve().parent / _ZH_MAP_NAME]
    for c in cand:
        try:
            if c.is_file():
                _ZH_MAP = json.loads(c.read_text(encoding="utf-8")).get("map", {})
                _ZH_MAP_WHY = f"凍結對照表 {c.name}({len(_ZH_MAP)} 筆)"
                return _ZH_MAP
        except Exception as e:
            _ZH_MAP_WHY = f"對照表讀不動:{type(e).__name__}: {e}"
    _ZH_MAP = {}
    _ZH_MAP_WHY = _ZH_MAP_WHY or f"對照表不在(找過 {len(cand)} 處)"
    return _ZH_MAP


def zh_convert(text: str) -> str:
    """簡→繁(字元層);沒有對照表時原樣回,不假裝轉過"""
    m = _zh_map()
    return "".join(m.get(c, c) for c in text) if m else text


def zh_which() -> str:
    """走的是哪條路:opencc(含片語層)/ builtin_char(只有字元層)/ passthrough(都沒有)"""
    try:
        import opencc  # noqa: F401
        return "opencc"
    except Exception:
        return "builtin_char" if _zh_map() else "passthrough"


_SENT_RX = re.compile(r"(?<=[。!?!?])\s*")


def _build_shim() -> types.ModuleType:
    """npl_preprocessor 記憶體級補殼(缺依賴件;收容夾零污染)"""
    mod = types.ModuleType("npl_preprocessor")

    @dataclass(frozen=True)
    class NormalizationConfig:
        opencc_config: str = "s2twp"
        punctuation_style: str = "preserve"
        preserve_newlines: bool = False

    @dataclass(frozen=True)
    class NLPConfig:
        model_name: str = "zh_core_web_sm"
        batch_size: int = 32
        n_process: int = 1
        disable_components: tuple = ("transformer",)

    class LanguageNormalizer:
        def __init__(self, config: NormalizationConfig | None = None):
            self.config = config or NormalizationConfig()
            try:
                import opencc
                self._cc = opencc.OpenCC(self.config.opencc_config.replace(".json", ""))
                self.zh_lane = "opencc"
            except Exception:
                # 批611:OpenCC 缺不再直通不轉——退凍結對照表(字元層)。
                # 直通等於把簡體原樣交給下游,下游冊按繁體正字比對,於是全部落空。
                self._cc = None
                self.zh_lane = zh_which()

        def normalize(self, text):
            if text is None:
                return ""
            out = unicodedata.normalize("NFKC", str(text))
            if self._cc is not None:
                out = self._cc.convert(out)
            else:
                out = zh_convert(out)          # 批611:零依賴字元層後備
            if not self.config.preserve_newlines:
                out = re.sub(r"\s*\n\s*", "", out)
            if self.config.punctuation_style == "ascii":
                out = out.translate(str.maketrans(",。:;?!“”‘’()", ',.:;?!""\'\'()'))
            return out.strip()

    class NLPPreprocessor:
        def __init__(self, config: NLPConfig | None = None, domain_patterns=None):
            self.config = config or NLPConfig()
            self.domain_patterns = list(domain_patterns or [])
            self.backend = "rule"  # spaCy 缺=規則道誠實後備
            if importlib.util.find_spec("spacy"):
                try:
                    import spacy
                    self._nlp = spacy.load(self.config.model_name)
                    self.backend = "spacy"
                except Exception:
                    self._nlp = None
            else:
                self._nlp = None

        def _rule_entities(self, text: str):
            ents = []

            def add(t, label, start):
                ents.append({"text": t, "label": label,
                             "start_char": start, "end_char": start + len(t)})
            for w in _INDICATOR_WORDS:
                for m in re.finditer(re.escape(w), text):
                    add(w, "INDICATOR", m.start())
            for org in _ORG_KNOWN:
                for m in re.finditer(re.escape(org), text):
                    add(org, "POLICY_ORG", m.start())
            for m in _PCT_RX.finditer(text):
                add(m.group(0), "PERCENT", m.start())
            for m in _DATE_RX.finditer(text):
                add(m.group(0), "DATE", m.start())
            for m in _CONCEPT_RX.finditer(text):
                add(m.group(0), "CONCEPT", m.start())
            return ents

        def process(self, text: str) -> dict:
            if self._nlp is not None:
                doc = self._nlp(text)
                return {"text": text,
                        "sentences": [s.text for s in doc.sents],
                        "entities": [{"text": e.text, "label": e.label_,
                                      "start_char": e.start_char,
                                      "end_char": e.end_char} for e in doc.ents],
                        "backend": "spacy"}
            sentences = [s for s in _SENT_RX.split(text) if s.strip()]
            return {"text": text, "sentences": sentences,
                    "entities": self._rule_entities(text), "backend": "rule"}

        def process_many(self, texts, batch_size=32, n_process=1):
            return [self.process(t or "") for t in texts]

    mod.NormalizationConfig = NormalizationConfig
    mod.NLPConfig = NLPConfig
    mod.LanguageNormalizer = LanguageNormalizer
    mod.NLPPreprocessor = NLPPreprocessor
    return mod


_SHIM_WHY = ""            # 批611:退回補殼的因由(空=沒退過)


def _load_real_preprocessor():
    """批152 正主件優先載入(檔案級;原件零觸碰);敗=None 退補殼
    正主 NLPPreprocessor 於 spaCy 缺席時設計為 raise(誠實紅線),
    本環境 spaCy 未裝→混血:正主 LanguageNormalizer(全保真正規化)
    +補殼規則 NLPPreprocessor(記憶體級);spaCy 裝上即自動全正主。"""
    p = INTAKE152 / "npl_preprocessor.py"
    if not p.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location("npl_preprocessor", p)
        m = importlib.util.module_from_spec(spec)
        # dataclass 解析需模組先掛 sys.modules(敗則 finally 前回滾)
        sys.modules["npl_preprocessor"] = m
        spec.loader.exec_module(m)
        # 可用性煙測:正規化必須實跑(OpenCC 缺時正主自身誠實訊息)
        m.LanguageNormalizer().normalize("測試")
        if getattr(m, "spacy", None) is None:
            m.NLPPreprocessor = _build_shim().NLPPreprocessor
            m._via_source = "hybrid_batch152(正主 Normalizer+規則 NLP)"
        else:
            m._via_source = "real_batch152"
        return m
    except Exception as e:
        # 批611(LL168 同一課):`except: return None` 吞掉的不只是例外,
        # 是下一個人找到這個 bug 的機會。原因留下來,畫面才說得出為什麼退回補殼。
        global _SHIM_WHY
        _SHIM_WHY = f"{type(e).__name__}: {e}"
        sys.modules.pop("npl_preprocessor", None)  # 回滾失敗殘掛
        return None


def load_stack():
    """動態載入收容原件(byte-exact 零觸碰;正主優先→shim 後備預掛)"""
    if "npl_preprocessor" not in sys.modules:
        real = _load_real_preprocessor()
        sys.modules["npl_preprocessor"] = real if real is not None else _build_shim()
    loaded = {}
    for name in ("knowledge_extraction_engine", "local_knowledge_engine"):
        p = INTAKE / f"{name}.py"
        if not p.exists():
            return None
        spec = importlib.util.spec_from_file_location(name, p)
        m = importlib.util.module_from_spec(spec)
        sys.modules[name] = m
        spec.loader.exec_module(m)
        loaded[name] = m
    return loaded


DEMO = ("2026年Q1,受房地產市場波動影響,其 NPL Ratio 攀升至 1.85%。"
        "為防範風險,金管會要求將備抵呆帳覆蓋率提升至150%。")


def analyze(text: str) -> dict:
    stack = load_stack()
    if stack is None:
        raise RuntimeError("收容原件缺(INTAKE)")
    pipe = stack["local_knowledge_engine"].LocalKnowledgePipeline()
    return pipe.analyze(text)


def selftest() -> int:
    fails = []
    nodata = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    def nod(name, note=""):
        """缺套件不是壞掉:誠實 NODATA,不混進 FAIL(判錯的紅燈和假綠一樣傷)"""
        print(f"  [NODATA] {name} {note}")
        nodata.append(name)

    files = ["local_knowledge_cli.py", "local_knowledge_engine.py",
             "knowledge_extraction_engine.py", "mail_tracker_v2_packaged.zip",
             "mail_tracker_v2_packaged_guide.pdf"]
    chk("① 批141 五件收容在位", all((INTAKE / f).exists() for f in files))

    shim = _build_shim()
    norm = shim.LanguageNormalizer(shim.NormalizationConfig()).normalize(
        "２０２６年Ｑ１,备抵呆账覆盖率")
    chk("② 補殼正規化(全形→半形+簡→繁;賬/帳=OpenCC 正字下游 alias 收斂)",
        "2026年Q1" in norm and ("備抵呆帳覆蓋率" in norm or "備抵呆賬覆蓋率" in norm),
        f"({norm[:24]})")

    stack = load_stack()
    chk("③ 原件動態載入(正主優先→shim 後備;零觸碰)", stack is not None)
    if stack is None:
        return 1

    src = getattr(sys.modules.get("npl_preprocessor"), "_via_source", "shim")
    have_real = (INTAKE152 / "npl_preprocessor.py").exists()
    if have_real and "batch152" in src:
        chk("③b 批152 正主件生效(npl_preprocessor 檔案級載入)", True, f"(source={src})")
    elif have_real:
        # 批611 工作站實錄:正主件**在**,是它的相依(OpenCC)缺,所以煙測 raise。
        # 缺套件 ≠ 缺件 ≠ 壞掉——判紅會把真正的紅淹掉(L57);而且**不代裝**。
        nod("③b 批152 正主件生效(npl_preprocessor 檔案級載入)",
            f"(正主件在,但它的相依缺 → 退補殼;因由={_SHIM_WHY or 'n/a'};"
            f"字元層已由 {zh_which()} 補上,片語層台灣用詞(軟件→軟體 這一類)要裝 opencc 才有)")
    else:
        chk("③b 批152 正主件生效(npl_preprocessor 檔案級載入)", False,
            f"(正主件不在 {INTAKE152.name}/)")

    r = analyze(DEMO)
    kinds = {t["attributes"].get("type") for t in r["triples"]}
    chk("④ demo 三型齊(metric/causation/policy)",
        {"metric_change", "causation", "policy_action"} <= kinds,
        f"(型={sorted(kinds)})")
    has_npl = any(t["subject"] == "NPL Ratio" and "1.85" in t["object"]
                  for t in r["triples"])
    has_cause = any("房地產市場波動" in t["subject"] for t in r["triples"])
    has_policy = any(t["subject"] == "金管會" for t in r["triples"])
    chk("⑤ 真值三檢(NPL 1.85%/房市波動因果/金管會政策)",
        has_npl and has_cause and has_policy)
    g = r["graph"]
    chk("⑥ 圖載荷(nodes/edges JSON-safe)",
        isinstance(g.get("nodes"), list) and len(g["nodes"]) >= 4)

    import importlib.util as _ilu64
    if _ilu64.find_spec("jieba") is None:
        nod("⑦ 分詞(jieba 道)", "(缺件 jieba;不代裝——via-rungate --family vrn --approve-install)")
    else:
        _probe = "台積電第三季毛利率創高"
        seg = stack["local_knowledge_engine"].LocalKnowledgePipeline.segment(
            _probe, backend="auto")
        # 批725:這一檢紅的時候要**自己講原因**。工作站實錄切出 ['台積電第三季毛利率創高']
        # —— 整串沒切,那不是「分詞判斷錯」,是**字典根本沒載進來**(jieba 退化成原樣回傳)。
        # 兩種紅長得一樣、修法完全不同,所以把它們分開講。
        _whole = (len(seg) == 1 and str(seg[0]).replace(" ", "") == _probe)
        if _whole:
            try:
                import jieba as _jb
                _cache = getattr(_jb.dt, "cache_file", "(問不到)")
            except Exception:
                _cache = "(問不到)"
            _why = (f"**整串沒切** → jieba 字典沒載進來(退化成原樣回傳),"
                    f"**不是分詞判斷錯**。快取 {_cache} —— 刪掉它讓 jieba 重建;"
                    f"刪不掉就是權限。切出來的:{seg[:2]}")
        else:
            _why = f"({seg[:5]})"
        chk("⑦ 分詞(jieba 道):切得開才算過。**整串原樣回傳=字典沒載**,"
            "與『切錯詞』是兩種紅、兩種修法,要分開講",
            ("毛利率" in seg or len(seg) >= 4) and not _whole, _why)

    tree = INTAKE / "mail_tracker_v2_packaged"
    if _ilu64.find_spec("pytest") is None:
        nod("⑧ mail tracker 收編測(pytest 2 綠+P2382 API 真值)", "(缺件 pytest;不代裝)")
        rt = None
    else:
        rt = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"],
                            cwd=tree, capture_output=True, text=True)
    api_ok = False
    if rt is not None and rt.returncode == 0:
        rr = subprocess.run([sys.executable, "-c", (
            "import sys; sys.path.insert(0,'.');"
            "from mail_tracker_v2 import mail_tracker_v2;"
            "r=mail_tracker_v2({'sender':'rd_lead@example.com','receiver':'pm@example.com',"
            "'subject':'P2382 risk on validation schedule',"
            "'body':'We see potential risk and delay on validation phase.',"
            "'timestamp':'2026-08-25 16:50'});"
            "import json; print(json.dumps(r, default=str)[:400])")],
            cwd=tree, capture_output=True, text=True)
        out = rr.stdout
        api_ok = rr.returncode == 0 and "P2382" in out and ("Risk" in out or "risk" in out)
    if rt is not None:
        chk("⑧ mail tracker 收編測(pytest 2 綠+P2382 API 真值)",
            rt.returncode == 0 and api_ok,
            f"(pytest rc{rt.returncode})")
    # ⑩ 批611(L83):**兩條路都要走過**。容器裝了 opencc 所以一直只走裝了那一半,
    #    工作站沒裝的那一半從來沒被驗過——三站就是這樣一起假綠的。
    #    這裡把 opencc 擋掉,逼補殼走零依賴後備,當場再驗一次。
    class _BlockOpenCC:
        def find_module(self, name, path=None):
            return self if name == "opencc" else None

        def find_spec(self, name, path=None, target=None):
            if name == "opencc":
                raise ImportError("VIA selftest:本檢刻意擋掉 opencc,驗零依賴後備")
            return None

    _saved = sys.modules.pop("opencc", None)
    sys.meta_path.insert(0, _BlockOpenCC())
    try:
        sh2 = _build_shim()
        n2 = sh2.LanguageNormalizer(sh2.NormalizationConfig()).normalize(
            "２０２６年Ｑ１,备抵呆账覆盖率")
        lane = zh_which()
    finally:
        sys.meta_path.pop(0)
        if _saved is not None:
            sys.modules["opencc"] = _saved
    chk("⑩ 沒有 OpenCC 的那條路也轉得動(零依賴字元層後備;L83 兩條路都走)",
        "2026年Q1" in n2 and ("備抵呆賬覆蓋率" in n2 or "備抵呆帳覆蓋率" in n2),
        f"(lane={lane} · {n2[:26]})")

    chk("⑪ 對照表有出處,不是我憑記憶造字(零發明)",
        len(_zh_map()) >= 2000 and zh_convert("联发科") == "聯發科",
        f"({_ZH_MAP_WHY})")

    n_tot = 11
    rc = 1 if fails else (2 if nodata else 0)
    state = {0: "GREEN", 1: "RED", 2: "NODATA"}[rc]
    print(f"  [計] 十一檢 OK {n_tot - len(fails) - len(nodata)} · FAIL {len(fails)}"
          f" · NODATA {len(nodata)} → rc={rc} ({state})")
    return rc


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 知識堆疊轉接(VRN_ENG064 v0102)· 十一檢自測(零網路)===")
        return selftest()
    text = DEMO if "--demo" in args else None
    if "--text" in args:
        text = args[args.index("--text") + 1]
    if text is None:
        print(__doc__.split("用法:")[1])
        return 0
    r = analyze(text)
    if "--json" in args:
        print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
    else:
        print(r["normalized_text"])
        for t in r["triples"]:
            print(f"- {t['subject']} --{t['predicate']}--> {t['object']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
