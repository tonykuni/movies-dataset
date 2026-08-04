# VTR · Python 版修復引擎規格書

**套件名稱**：`vtr_py`　**版本**：1.0.0　**角色**：權威實作（批次／模型層／LLM 仲裁）
**資料契約**：`contracts/vtr-document.schema.json`（與 JS 版共用）

---

## 1. 專案結構

```
vtr_py/
├── __init__.py
├── document.py            # Document / Segment / Patch / Revision 資料類別（pydantic）
├── context.py             # Context：設定、詞庫快照、模型 handle、量測收集器
├── pipeline.py            # Pipeline 執行器（純函式串接 + patch 收集 + hash 計算）
├── gate.py                # 信心度閘門
├── protect.py             # P0 遮罩／還原 + sentinel 完整性檢查
├── stages/
│   ├── s1_lang_detect.py
│   ├── s2_normalize.py
│   ├── s3_punctuate.py
│   ├── s4_segment.py
│   ├── s5_spell.py
│   ├── s6_grammar.py
│   ├── s7_lexicon.py
│   └── s8_structure.py
├── lang/
│   ├── zh/                # 中文子管線實作
│   └── en/                # 英文子管線實作
├── lexicon/
│   ├── store.py           # SSOT Lexicon 載入、scope 解析、索引建置
│   └── matcher.py         # 精確 / 模糊 / 拼音 / 音素比對
├── arbiter/
│   └── claude.py          # LLM 仲裁層（Anthropic SDK）
├── versioning/
│   ├── patchlog.py        # JSONL append-only
│   └── replay.py          # 重播 / 回滾
├── eval/
│   ├── metrics.py
│   └── goldset.py
└── cli.py                 # vtr restore / replay / lexicon / eval
```

---

## 2. 核心型別

```python
# document.py
from pydantic import BaseModel, Field
from typing import Literal, Optional

Lang     = Literal["zh", "en", "mixed"]
Decision = Literal["auto", "review", "reject"]
Source   = Literal["deterministic", "model", "lexicon", "llm_arbiter", "human"]

class Protection(BaseModel):
    sentinel: str            # ⟦P0001⟧
    surface: str
    kind: Literal["lexicon", "part_number", "url", "email",
                  "code_ident", "number_unit", "timestamp", "id_code"]
    lexicon_id: Optional[str] = None

class Segment(BaseModel):
    id: str
    lang: Lang
    text: str
    speaker: Optional[str] = None
    t_start: Optional[float] = None
    t_end: Optional[float] = None
    runs: list["Run"] = Field(default_factory=list)
    protections: list[Protection] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)

class Patch(BaseModel):
    patch_id: str
    stage: str
    segment_id: str
    span: tuple[int, int]
    before: str
    after: str
    rule_id: str             # VTR.<STAGE>.<rule>
    source: Source
    confidence: float
    decision: Decision
    evidence: Optional[str] = None

class StageResult(BaseModel):
    doc: "Document"
    patches: list[Patch]
    metrics: dict = Field(default_factory=dict)
```

### 2.1 Stage 協定

```python
# pipeline.py
from typing import Protocol

class Stage(Protocol):
    name: str                      # "PUNCTUATE"
    def apply(self, doc: Document, ctx: Context) -> StageResult: ...
```

**強制不變式**（由 `pipeline.py` 在每個 Stage 後檢查，違反即回退該 Stage）：

1. `len(doc.segments)` 只有 `SEGMENT` 步驟可以改變。
2. `PROTECT` 之後、`UNPROTECT` 之前，所有 sentinel 必須原封不動存在。
3. 每個 `Patch.span` 必須落在套用當下 `segment.text` 的合法範圍內。
4. 每個 Patch 的 `rule_id` 必須已註冊於 `RULE_REGISTRY`（防止規則命名漂移，維持與 JS 版的對應）。

---

## 3. 工具組落點（Top 15 → 八步）

Portfolio 列的 15 個工具，**不是每個都該放進主管線**。以下是實際落點與取捨理由。

### 3.1 主管線（必要）

| 工具 | 落點 | 用途 | 備註 |
|---|---|---|---|
| **OpenCC** | 2 NORMALIZE | 簡繁轉換 `s2twp`（含台灣用語轉換） | DG-IN 產出一律台灣正體 |
| **jieba** | 4 SEGMENT / 7 LEXICON | 中文斷詞、**自訂詞典載入 SSOT Lexicon** | `jieba.load_userdict()` 是專名保護的第一道防線 |
| **pkuseg** | 4 SEGMENT（交叉驗證） | 領域自適應斷詞 | 與 jieba 不一致的邊界 → 標記待仲裁 |
| **Transformers** | 3 PUNCTUATE / 5 SPELL / 6 GRAMMAR | 承載標點恢復、中文 CSC、英文 GEC 模型 | 模型 ID 見 §4 |
| **SymSpell** | 5 SPELL（en） | O(1) 編輯距離拼寫修正 | 比 pyspellchecker 快兩個數量級，主力 |
| **LanguageTool** | 6 GRAMMAR（en） | 規則式文法／標點檢查 | 提供 `rule_id`，可解釋性最好 |
| **spaCy** | 7 LEXICON / 8 STRUCTURE | 英文 NER、依存句法、`EntityRuler` 掛載詞庫 | `en_core_web_trf` |
| **Stanza** | 7 LEXICON（zh） | 中文 NER 與依存句法 | 中文 NER 主力 |
| **HanLP** | 7 LEXICON（zh 交叉驗證） | 中文全家桶 | 與 Stanza 不一致 → 進仲裁 |
| **pypinyin** | 7 LEXICON | 專名拼音模糊比對 | **中文 ASR 錯字的頭號解法**（同音字） |
| **jellyfish** | 7 LEXICON | Double Metaphone 音素比對（en） | 英文專名的對應解法 |

> `pypinyin` 與 `jellyfish` 不在 Portfolio 原本的 15 個裡，但**沒有它們，第 7 步等於做不了**：中文 ASR 的主要錯誤型態是同音字（「威瑞塔斯」→「維瑞他斯」），字面編輯距離抓不到，拼音距離一抓就中。

### 3.2 降級為輔助或替換（附理由）

| 工具 | 處置 | 理由 |
|---|---|---|
| **NLTK** | 僅用於 eval（BLEU/GLEU 計分） | 主管線功能已被 spaCy 覆蓋且更快 |
| **Flair** | 不入主管線，列為 NER 備援 | 與 spaCy/Stanza 功能重疊，增加一份模型權重與相依 |
| **SnowNLP** | 不採用 | 基於簡體語料、久未維護；繁中會議語料表現不穩 |
| **pyspellchecker** | 不採用（由 SymSpell 取代） | 純 Python 迴圈，長逐字稿吞吐不足 |
| **DeepSegment** | 由 `PUNCTUATE + 規則切句` 取代 | 專案已停止維護；本架構斷句依賴標點訊號，不需獨立模型 |
| **Punctuator** | 由 Transformers 標點模型取代 | Punctuator2 為 Theano 時代產物，中文支援差 |

**取捨原則**：同一職責只留一個主力 + 最多一個交叉驗證者。交叉驗證者的價值不是「更準」，而是**不一致時能觸發仲裁**。

---

## 4. 模型清單

> **必須在 build 時 pin 住並驗證可用性。** 以下為候選，非保證；`vtr models verify` 會在 CI 檢查每個 ID 可下載且輸出格式符合預期。無法取得時，該 Stage 降級為規則式並在 `metrics` 標記 `degraded=true`（**絕不靜默跳過**）。

| 步驟 | 語言 | 候選模型 | 任務型別 |
|---|---|---|---|
| 3 PUNCTUATE | zh | `p208p2002/zh-punctuation-restore`（候選） | token classification |
| 3 PUNCTUATE | en | `oliverguhr/fullstop-punctuation-multilang-large`（候選） | token classification |
| 5 SPELL | zh | `shibing624/macbert4csc-base-chinese`（候選） | 中文拼寫糾錯 CSC |
| 5 SPELL | en | SymSpell + 自建頻率詞典（非神經） | 確定性 |
| 6 GRAMMAR | en | `grammarly/coedit-large`（候選） | seq2seq GEC |
| 7 NER | zh | `ckiplab/bert-base-chinese-ner`（候選）／ Stanza `zh-hant` | NER |
| 7 NER | en | spaCy `en_core_web_trf` | NER |
| 仲裁／結構化 | 雙語 | **`claude-opus-5`** | 見 §6 |

### 4.1 模型輸出 → Patch 的轉換

模型不直接改文字。轉換規則：

```python
# stages/s5_spell.py（節錄）
def _to_patches(seg, orig, corrected, probs, rule_id, ctx) -> list[Patch]:
    patches = []
    for start, end, before, after, p in align_diff(orig, corrected, probs):
        if _touches_sentinel(seg, start, end):
            ctx.metrics.bump("sentinel_guard_blocked")
            continue                                    # 遮罩區永不修改
        conf = ctx.calibrator.calibrate(rule_id, p)     # temperature scaling
        patches.append(Patch(
            patch_id=new_id(), stage="SPELL", segment_id=seg.id,
            span=(start, end), before=before, after=after,
            rule_id=rule_id, source="model", confidence=conf,
            decision=ctx.gate.decide(conf),
            evidence=f"model p={p:.3f} calibrated={conf:.3f}",
        ))
    return patches
```

**校準（calibration）是必要步驟**：未校準的模型機率會系統性高估，直接拿來當信心度會讓 `auto` 頻帶塞滿本該人工複核的改動。校準參數由黃金測試集擬合，存於 `config/calibration.json`。

---

## 5. 各步驟實作要點

### 5.1 `LANG_DETECT` —— Script Run 演算法

不使用 langdetect 之類的**整句**語言偵測（對中英混雜句無效）。改用 code-point 分類 + run 合併：

```python
CJK_RANGES = [(0x4E00,0x9FFF), (0x3400,0x4DBF), (0xF900,0xFAFF),
              (0x3000,0x303F), (0xFF00,0xFFEF)]

def classify(ch: str) -> str:
    cp = ord(ch)
    if any(lo <= cp <= hi for lo, hi in CJK_RANGES): return "cjk"
    if ch.isascii() and ch.isalpha():                return "latin"
    if ch.isdigit():                                  return "digit"
    if not ch.isalnum() and not ch.isspace():        return "punct"
    return "other"
```

合併規則：

1. 連續同類 code point 合成一個 run。
2. run 長度 < `min_run`（zh 預設 2 字、en 預設 3 字母）併入前一個 run。
3. **CJK 主體句中的 latin run → `role="embedded"`**，不送進英文子管線做獨立句法修復（否則 `dashboard` 會被要求加冠詞）。
4. 句子 `lang`：cjk 佔比 > 0.7 → `zh`；latin > 0.7 → `en`；否則 `mixed`。

### 5.2 `NORMALIZE`

順序固定（每一項都產生一筆 `deterministic` patch，confidence = 1.0）：

1. Unicode NFKC
2. 全形英數 → 半形（`VTR.NORMALIZE.fullwidth_ascii`）
3. 半形中文標點 → 全形（`VTR.NORMALIZE.cjk_punct`）
4. OpenCC `s2twp`（`VTR.NORMALIZE.opencc_s2twp`）
5. 空白正規化：CJK 之間移除空白；CJK–Latin 邊界插入單一空白（DG-IN 排版慣例）
6. ASR 語助詞：**標記而非刪除**（`VTR.NORMALIZE.filler_mark`，decision 一律 `review`）

> 第 6 點刻意不自動刪除：「那個…」有時是語助詞，有時是指示代詞（「那個料號」）。誤刪會改變語意。

### 5.3 `SPELL`（zh）與 `LEXICON` 的分工

| 情境 | 由誰處理 |
|---|---|
| 一般詞同音／形近錯字（「因該」→「應該」） | 5 SPELL（CSC 模型） |
| 專名被打壞（「威瑞塔斯」→「維瑞他斯」） | 7 LEXICON（拼音模糊比對） |
| 專名完全正確 | P0 已遮罩，兩者都碰不到 |

CSC 模型會嘗試把不在其詞彙表裡的專名「修正」成常見詞 —— P0 遮罩正是為了擋掉這件事。

### 5.4 `LEXICON` —— 比對演算法

詳見 `03_SSOT_LEXICON_SPEC.md` §5。摘要：

```
score = 0.5 · literal_sim + 0.3 · phonetic_sim + 0.2 · context_boost

literal_sim   : 正規化 Levenshtein
phonetic_sim  : zh → pypinyin（去聲調）編輯距離；en → Double Metaphone
context_boost : 同 scope 詞條 +0.15；meta.participants 命中人名 +0.25；
                同段落已出現同專案詞 +0.10（上限 1.0）
```

**護欄**：候選詞若同時是常用詞（在通用詞頻表前 5000 名內），門檻由 0.75 提高到 0.92。避免把「大衛」改成專案代號「David-Ops」。

### 5.5 `STRUCTURE`

兩階段：

1. **確定性抽取**：句型模板（「我們決定…」「@某人 負責…」「下週前完成」）+ spaCy/Stanza 依存句法，抽出候選。
2. **LLM 分類**：候選送 Claude 判定 `decision` / `action` / `issue` / `risk` / `info`，並抽 owner 與 due。

第 8 步是唯一**預設就走 LLM** 的步驟 —— 因為「這句是決議還是討論」沒有確定性 ground truth。

---

## 6. LLM 仲裁層

### 6.1 呼叫時機

```python
def needs_arbitration(seg, patches, ctx) -> bool:
    return (
        _has_conflicting_patches(patches)                       # 同 span 多來源衝突
        or any(p.decision == "review" for p in patches)
          and "unresolved_entity" in seg.flags
        or ctx.stage == "STRUCTURE"
    )
```

### 6.2 實作

```python
# arbiter/claude.py
import anthropic

MODEL = "claude-opus-5"

ARBITER_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["accept", "reject", "alternative"]},
        "chosen_patch_id": {"type": ["string", "null"]},
        "alternative_text": {"type": ["string", "null"]},
        "confidence": {"type": "number"},
        "evidence": {"type": "string"},
    },
    "required": ["verdict", "chosen_patch_id", "alternative_text",
                 "confidence", "evidence"],
    "additionalProperties": False,
}

SYSTEM = """你是 DG-IN 會議紀錄修復引擎的仲裁層。
你的職責是在確定性修復層產生衝突時裁決，不是重寫會議紀錄。

規則：
1. ⟦Pnnnn⟧ 形式的遮罩符是受保護內容。原樣保留，絕不改動、拆解或翻譯。
2. 只裁決被提出的候選；不要提出新的修改範圍。
3. 語意不明時選擇最小改動（`reject` 優於猜測）。
4. evidence 用一句話說明依據，供人工複核閱讀。
5. 中文輸出使用台灣正體。"""

class ClaudeArbiter:
    def __init__(self, client: anthropic.Anthropic, effort: str = "medium"):
        self.client, self.effort = client, effort

    def _system_blocks(self, lexicon_slice: str):
        # 穩定內容在前並掛快取斷點；波動內容（本次待裁決 segment）放在 messages。
        # Opus 5 最小可快取前綴為 512 tokens，詞庫切片幾乎必然可快取。
        return [
            {"type": "text", "text": SYSTEM},
            {"type": "text", "text": lexicon_slice,
             "cache_control": {"type": "ephemeral"}},
        ]

    def arbitrate(self, seg, candidates, lexicon_slice: str) -> dict:
        resp = self.client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=self._system_blocks(lexicon_slice),
            output_config={
                "effort": self.effort,
                "format": {"type": "json_schema", "schema": ARBITER_SCHEMA},
            },
            messages=[{"role": "user", "content": _render_case(seg, candidates)}],
        )
        if resp.stop_reason == "refusal":          # Opus 5 安全分類器可能拒絕
            return {"verdict": "reject", "chosen_patch_id": None,
                    "alternative_text": None, "confidence": 0.0,
                    "evidence": "arbiter refusal; escalated to human review"}
        text = next(b.text for b in resp.content if b.type == "text")
        return json.loads(text)
```

**API 注意事項（Opus 5）**：

- **不要**送 `temperature` / `top_p` / `top_k` / `budget_tokens` —— 一律 400。
- thinking 預設即開啟（省略 `thinking` 欄位等同 adaptive）。因此 `max_tokens` 是 thinking + 回應的**共同上限**，不可壓太低。
- `thinking: {"type": "disabled"}` 僅在 effort ≤ `high` 時可用；與 `xhigh`/`max` 併用回 400。本引擎不關閉 thinking。
- 讀 `resp.content` **之前**先檢查 `stop_reason == "refusal"`。
- 結構化輸出用 `output_config.format`（`output_format` 已棄用）。

### 6.3 批次模式

離線批次（夜間跑整週會議）用 Batch API，全額 50% 折扣：

```python
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

batch = client.messages.batches.create(requests=[
    Request(custom_id=f"arb-{case.id}",
            params=MessageCreateParamsNonStreaming(
                model=MODEL, max_tokens=4096,
                system=system_blocks,
                output_config={"effort": "medium",
                               "format": {"type": "json_schema", "schema": ARBITER_SCHEMA}},
                messages=[{"role": "user", "content": _render_case(*case.args)}]))
    for case in cases
])
# 結果順序不保證 —— 一律以 custom_id 對應，不可用位置索引。
```

### 6.4 快取排序（成本關鍵）

渲染順序為 `tools → system → messages`。因此：

- **穩定內容置前**：仲裁 SYSTEM prompt（凍結）、Lexicon scope 切片（每場會議固定）。
- **波動內容置後**：待裁決 segment、候選 patch，放 `messages`，在最後一個快取斷點之後。
- **禁止**在 system prompt 內插入時間戳、會議 ID、UUID —— 會使整段前綴每次失效，快取讀取率歸零。
- 驗證方式：連續請求檢查 `resp.usage.cache_read_input_tokens`，若持續為 0 即代表有靜默失效源。

---

## 7. CLI

```bash
# 完整修復
vtr restore transcript.txt --doc-id DGIN-MTG-20260804-01 \
    --lexicon-scope global,project:VIA --out ./out/

# 從第 5 步重跑（前 4 步結果由 patch log 重播）
vtr restore --replay ./out/DGIN-MTG-20260804-01 --from-stage SPELL

# 回滾到 rev 3
vtr replay ./out/DGIN-MTG-20260804-01 --to-rev 3 --out ./out/rollback/

# 人工裁決佇列
vtr review ./out/DGIN-MTG-20260804-01           # 互動式；產生 human patch

# 詞庫
vtr lexicon validate
vtr lexicon add --kind product --canonical "VeritasAutoPlot" --alias "VAP"   # → enabled=false 草稿

# 評估
vtr eval --goldset ./eval/goldset/ --report ./out/eval.html
```

**退出碼**：`0` 成功；`2` schema 驗證失敗；`3` sentinel 完整性違反；`4` 改壞率超過門檻（CI 用）。

---

## 8. 設定檔

```yaml
# config/vtr.yaml
engine: vtr-py/1.0.0

gate:
  auto_threshold: 0.85
  review_threshold: 0.60
  llm_only_ceiling: 0.80        # 單獨 LLM 判斷永遠進 review

normalize:
  opencc: s2twp
  filler_policy: mark           # mark | remove | keep（預設 mark）

lang_detect:
  min_run_cjk: 2
  min_run_latin: 3
  mixed_threshold: 0.7

lexicon:
  scopes: [global]
  match_threshold: 0.75
  common_word_threshold: 0.92   # 常用詞護欄
  weights: { literal: 0.5, phonetic: 0.3, context: 0.2 }

arbiter:
  enabled: true
  model: claude-opus-5
  effort: medium                # low | medium | high | xhigh | max
  max_tokens: 4096
  batch: false
  max_cases_per_doc: 200        # 超過即中止並告警（防成本失控）

eval:
  harmful_edit_rate_max: 0.005  # 超過即 CI 失敗
```

---

## 9. 測試策略

| 層級 | 內容 |
|---|---|
| 單元 | 每個 Stage 對固定輸入產生固定 patch 集（含 rule_id、span、confidence） |
| 屬性測試 | **不變式**：`UNPROTECT(PROTECT(x)) == x`；`replay(patches) == final_doc`；任一 Stage 對已修復文本再跑一次為冪等（除 STRUCTURE） |
| 對抗測試 | 專門構造會誘使模型改壞專名的輸入（料號旁邊放常見詞、人名用同音字），斷言 `harmful_edit == 0` |
| 黃金集回歸 | ≥200 段人工標註；任一指標退步即 CI 失敗 |
| 跨引擎 | 同一 Document 分別跑 Python 版與 JS 版，比對共同 rule_id 的 patch；不一致即告警 |

---

## 10. 相依與版本

```
python = ">=3.11"

# 主管線
opencc-python-reimplemented, jieba, pkuseg, transformers, torch,
symspellpy, language-tool-python, spacy, stanza, hanlp,
pypinyin, jellyfish, pydantic>=2, typer, orjson

# LLM
anthropic

# 評估
nltk, scikit-learn
```

模型權重不入 git；由 `vtr models pull` 取得並以 SHA-256 登錄於 `models.lock.json`（與 VIA hash-lock 治理一致）。

---

*本文件為 VTR 子系統 canonical 規格的一部分，SHA-256 已登錄於 `VTR_Subsystem_Manifest.json`。*
