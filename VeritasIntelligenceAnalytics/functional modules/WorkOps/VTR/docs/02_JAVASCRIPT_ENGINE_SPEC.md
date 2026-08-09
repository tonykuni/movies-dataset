# VTR · JavaScript 版修復引擎規格書

**套件名稱**：`@dg-in/vtr-js`　**版本**：1.0.0　**角色**：即時預覽／編輯器層／人工裁決介面
**資料契約**：`contracts/vtr-document.schema.json`（與 Python 版共用）

---

## 1. 定位：這一版**不是** Python 版的翻譯

兩版引擎的職責分工在架構文件 §7 已定。這裡把界線講死：

| | Python 版 | JavaScript 版 |
|---|---|---|
| 權威性 | **權威實作**，canonical 修復只能由它產生 | 預覽／輔助，產物永不直接進 canonical |
| 延遲 | 秒～分鐘（批次） | **< 50 ms**（逐鍵盤事件） |
| 執行位置 | 伺服器 / operator workstation | 瀏覽器 / Electron 編輯器 / Node CLI |
| 模型 | Transformer（CSC / GEC / NER） | **無神經模型**（見 §3.2） |
| 對做不到的事 | 降級並標記 `degraded` | 標記 `pending_server`，**不猜** |

> **最重要的一條**：JS 版遇到它無法可靠處理的步驟（中文錯字、英文文法、中文 NER），**必須留白並標記，不得用弱工具硬做**。在會議紀錄上，弱工具的錯誤修復比不修復傷害大得多。這是本規格書刻意的取捨，不是能力不足的藉口。

---

## 2. 專案結構

```
packages/vtr-js/
├── src/
│   ├── document.ts          # 型別 + zod schema（由 vtr-document.schema.json 生成）
│   ├── pipeline.ts          # 與 Python 版相同的 Stage 協定
│   ├── gate.ts              # 信心度閘門（門檻與 Python 版共用設定檔）
│   ├── protect.ts           # P0 遮罩／還原 + sentinel 檢查
│   ├── stages/
│   │   ├── s1-lang-detect.ts
│   │   ├── s2-normalize.ts
│   │   ├── s3-punctuate.ts      # 規則式子集
│   │   ├── s4-segment.ts
│   │   ├── s5-spell.ts          # en 可做；zh → pending_server
│   │   ├── s6-grammar.ts        # en 輕量；zh → pending_server
│   │   ├── s7-lexicon.ts        # 精確 + 拼音模糊（純 JS 可做）
│   │   └── s8-structure.ts      # 僅樣板抽取；分類 → pending_server
│   ├── lexicon/
│   │   ├── store.ts             # 載入 SSOT Lexicon（同一批 JSON 檔）
│   │   ├── trie.ts              # Aho-Corasick 多模式匹配（精確命中）
│   │   └── pinyin.ts            # 拼音模糊比對
│   ├── rules/registry.ts        # rule_id 註冊表（與 Python 版逐項對應）
│   ├── client/transport.ts      # 送 Document 到 Python 服務、接回 patch log
│   └── ui/                      # 選用：Patch 高亮 / Review Queue 元件
├── test/
└── package.json
```

---

## 3. 工具組落點（Top 15 → 八步）

### 3.1 主管線（採用）

| 工具 | 落點 | 用途 |
|---|---|---|
| **unified** | 全管線 | 文字 AST 骨架；Stage 之間傳遞的統一表示 |
| **retext** | 3 / 6 | 英文文字處理插件宿主 |
| **retext-spell** | 5 SPELL（en） | 英文拼寫（含自訂詞典掛載 Lexicon） |
| **sentence-splitter** | 4 SEGMENT | 依標點切句（中英皆可用，含縮寫例外處理） |
| **compromise** | 7 / 8 | 輕量英文 NLP：詞性、人名／組織粗抽、句型樣板 |
| **winkNLP** | 7 / 8 | 高速英文 tokenize + NER（瀏覽器內效能最佳） |
| **segmentit** | 4 SEGMENT（zh） | 純 JS 中文斷詞，**支援自訂詞典** |
| **OpenCC-JS** | 2 NORMALIZE | 簡繁轉換（與 Python 版同一組轉換表） |
| **typo.js** | 5 SPELL（en 備援） | Hunspell 字典；retext-spell 不可用時降級 |
| **RxJS** | pipeline | 逐鍵盤事件的 debounce / 取消 / 背壓控制 |
| **pinyin-pro** | 7 LEXICON | 中文拼音（對應 Python 版 pypinyin） |
| **fastest-levenshtein** | 7 LEXICON | 編輯距離 |

> `pinyin-pro` 與 `fastest-levenshtein` 不在原本 15 個裡，理由同 Python 版：**沒有拼音比對，第 7 步做不了**。這是 JS 版唯一能與 Python 版對等的高價值步驟，必須做好。

### 3.2 不採用（附理由）

| 工具 | 處置 | 理由 |
|---|---|---|
| **natural** | 不採用 | 與 compromise / winkNLP 功能重疊；bundle 體積大 |
| **nlp.js** | 不採用 | 定位是對話意圖辨識，非文本修復 |
| **node-jieba** | 不採用 | 原生相依，無法在瀏覽器執行；由 segmentit 取代 |
| **node-spellchecker** | 不採用 | 原生相依，同上 |
| **LanguageTool JS** | 僅作為**遠端 client** | 純 JS 版本能力遠低於 Java 本體；本引擎呼叫伺服器端 LanguageTool，或直接留給 Python 版 |

### 3.3 明確留白（`pending_server`）

| 步驟 | 語言 | JS 版行為 |
|---|---|---|
| 5 SPELL | **zh** | 標記 `pending_server`。純 JS 無可用的中文 CSC 模型；用編輯距離猜同音字會大量誤改。 |
| 6 GRAMMAR | **zh** | 標記 `pending_server`。中文語序修復需依存句法模型。 |
| 7 LEXICON | zh NER | 只做**詞庫比對**（有明確候選）；**不做**開放式 NER。 |
| 8 STRUCTURE | 雙語 | 只做句型樣板抽取；`decision`/`action` 分類 → `pending_server`。 |

UI 對 `pending_server` 的呈現：該段落顯示灰色底線 + 「待伺服器完整修復」提示，**不顯示任何猜測結果**。

---

## 4. Stage 協定（與 Python 版同構）

```ts
// pipeline.ts
export interface StageResult {
  doc: Document;
  patches: Patch[];
  metrics: Record<string, number>;
}

export interface Stage {
  readonly name: StageName;
  readonly capability: "full" | "partial" | "server_only";
  apply(doc: Document, ctx: Context): StageResult;
}
```

`capability` 是 JS 版獨有欄位，驅動 `pending_server` 標記：

```ts
export function runPipeline(doc: Document, ctx: Context): Document {
  let cur = doc;
  for (const stage of ctx.stages) {
    if (stage.capability === "server_only") {
      cur = markPendingServer(cur, stage.name);
      continue;
    }
    const r = stage.apply(cur, ctx);
    assertInvariants(cur, r, stage);           // 同 Python 版四條不變式
    cur = commit(cur, r, ctx);                 // 套用 auto、review 進佇列
    if (stage.capability === "partial") {
      cur = markPendingServer(cur, stage.name, r.metrics.uncoveredSegmentIds);
    }
  }
  return cur;
}
```

### 4.1 不變式（與 Python 版逐條相同）

1. 只有 `SEGMENT` 可改變 `segments` 數量。
2. `PROTECT` 與 `UNPROTECT` 之間，所有 sentinel 原封不動。
3. `Patch.span` 必須落在當下 `segment.text` 合法範圍。
4. `rule_id` 必須存在於 `rules/registry.ts`，且該 registry 由 CI 與 Python 版 `RULE_REGISTRY` 比對，**不允許單方新增**。

---

## 5. 即時管線（RxJS）

編輯器場景的核心約束：使用者每一次輸入都可能觸發修復，但**不能卡住輸入**。

```ts
import { Subject, asyncScheduler } from "rxjs";
import { debounceTime, switchMap, observeOn, share } from "rxjs/operators";

const edits$ = new Subject<Document>();

export const localPatches$ = edits$.pipe(
  debounceTime(120),                       // 停止輸入 120ms 後才跑
  observeOn(asyncScheduler),
  switchMap(doc => runLocalPipeline$(doc)),// 新輸入自動取消前一次（switchMap）
  share(),
);

// 伺服器完整修復：更長的 debounce，且不阻擋本地結果
export const serverPatches$ = edits$.pipe(
  debounceTime(2500),
  switchMap(doc => fromFetch(postToVtrPy(doc))),
  share(),
);
```

**效能預算**（3,000 字文件，中階筆電）：

| 階段 | 預算 |
|---|---|
| LANG_DETECT + NORMALIZE + PROTECT | < 15 ms |
| SEGMENT（segmentit） | < 20 ms |
| LEXICON 精確命中（Aho-Corasick） | < 5 ms |
| LEXICON 拼音模糊 | < 10 ms |
| **合計本地管線** | **< 50 ms** |

超過預算時降級順序：關閉拼音模糊 → 關閉 segmentit 改用純標點切句 → 只跑 NORMALIZE + PROTECT。降級狀態必須在 UI 顯示。

### 5.1 Web Worker

本地管線一律跑在 Web Worker，主執行緒只收 patch。詞庫索引（Aho-Corasick trie + 拼音表）在 Worker 啟動時建置一次，之後常駐。

---

## 6. Lexicon 比對（純 JS）

### 6.1 精確命中 —— Aho-Corasick

一次掃描同時匹配全部 alias，複雜度 O(n + m)。詞庫更新時重建 trie（背景 Worker，約 20 ms / 5,000 詞條）。

```ts
// lexicon/trie.ts
export class AliasTrie {
  build(entries: LexiconEntry[]): void;
  /** 回傳所有命中，含重疊；由呼叫端以最長匹配優先解衝突 */
  matchAll(text: string): Array<{ start: number; end: number; entryId: string }>;
}
```

命中即產生 `PROTECT` patch（`confidence = 1.0`，`source = "lexicon"`）。

### 6.2 拼音模糊比對

```ts
// lexicon/pinyin.ts
import { pinyin } from "pinyin-pro";
import { distance } from "fastest-levenshtein";

const toKey = (s: string) =>
  pinyin(s, { toneType: "none", type: "array" }).join("");

export function phoneticScore(candidate: string, canonical: string): number {
  const a = toKey(candidate), b = toKey(canonical);
  if (!a || !b) return 0;
  return 1 - distance(a, b) / Math.max(a.length, b.length);
}
```

總分與 Python 版**使用同一組權重與門檻**（讀同一份 `config/vtr.yaml`）：

```
score = 0.5·literal + 0.3·phonetic + 0.2·context
門檻 0.75；候選為通用高頻詞時提高到 0.92
```

**跨引擎一致性測試**：同一組 (candidate, canonical) 輸入，Python 版與 JS 版的 `score` 差異必須 < 0.01，否則 CI 失敗。這是兩版引擎唯一必須數值對齊的地方。

---

## 7. 人工裁決 UI（Review Queue）

JS 版的獨有價值不在修復能力，而在**讓人能高效裁決**。

| 元件 | 行為 |
|---|---|
| Patch 高亮 | 依 `decision` 上色：`auto` 綠底、`review` 黃底、`reject` 不顯示（可切換） |
| 懸停卡片 | 顯示 `before → after`、`rule_id`、`confidence`、**`evidence`** |
| 一鍵裁決 | 接受 / 拒絕 / 改寫 → 產生 `source: "human"`、`confidence: 1.0` 的 patch |
| 批次裁決 | 依 `rule_id` 分組：「接受全部 12 筆 `VTR.NORMALIZE.fullwidth_ascii`」 |
| 時間軸回聽 | 有 `t_start` 時提供音檔跳轉，供 `needs_audio_recheck` 段落確認 |
| 版本滑桿 | 拖曳 rev 0…N 即時預覽任一版本（本地重播，不呼叫伺服器） |

**裁決結果一律附加為新 patch，不修改既有 patch。** 這維持 append-only 稽核鏈。

---

## 8. 傳輸協定

```ts
// client/transport.ts
POST /vtr/restore
  body: { document: Document, from_stage?: StageName, scopes: string[] }
  200 : { document: Document, patches: Patch[], revisions: Revision[] }
  409 : { error: "content_hash_mismatch", server_hash, client_hash }
```

**409 處理**：客戶端在等待期間文件已被編輯 → 以伺服器回傳的 patch log 對新文件重播（patch 帶 span，可用標準 OT/rebase 規則調整偏移）；無法乾淨 rebase 的 patch 降級為 `review` 交人工。**絕不靜默覆蓋使用者的編輯。**

---

## 9. 建置與相依

```json
{
  "name": "@dg-in/vtr-js",
  "type": "module",
  "engines": { "node": ">=20" },
  "dependencies": {
    "unified": "^11", "retext": "^9", "retext-spell": "^6",
    "sentence-splitter": "^5", "compromise": "^14", "wink-nlp": "^2",
    "segmentit": "^2", "opencc-js": "^1", "typo-js": "^1",
    "pinyin-pro": "^3", "fastest-levenshtein": "^1",
    "rxjs": "^7", "zod": "^3"
  }
}
```

- **Bundle 預算**：核心（不含詞庫）gzip 後 **< 300 KB**。超標則將 winkNLP 模型與 typo.js 字典改為動態 import。
- **無原生相依**：全部套件必須可在瀏覽器執行（這是排除 node-jieba / node-spellchecker 的硬性理由）。
- 型別由 `vtr-document.schema.json` 以 `json-schema-to-zod` 生成，CI 檢查生成結果與 committed 檔案一致 —— **契約漂移即建置失敗**。

---

## 10. 測試策略

| 層級 | 內容 |
|---|---|
| 單元 | 每個 Stage 固定輸入 → 固定 patch 集 |
| 不變式 | `unprotect(protect(x)) === x`；`replay(patches)` 收斂；本地管線冪等 |
| **跨引擎** | 共用 fixture：同一 Document 分別跑兩版，比對共同 `rule_id` 的 patch（span、before/after 必須相同；confidence 差異 < 0.01） |
| 效能 | 3,000 字文件本地管線 p95 < 50 ms（CI 以固定機型基準） |
| 留白驗證 | 斷言 JS 版**沒有**對 zh SPELL / zh GRAMMAR 產生任何 patch —— 防止有人「順手」加了弱實作 |

最後一項是刻意的回歸防線：本規格的核心取捨（寧可留白，不可亂改）必須由測試保護，不能只靠文件約定。

---

*本文件為 VTR 子系統 canonical 規格的一部分，SHA-256 已登錄於 `VTR_Subsystem_Manifest.json`。*
