# VIA 全庫整合稽核（2026-09-24）

唯讀稽核，**不刪檔、不改寫來源、不執行被讀的檔**——依 `CLAUDE.md` 的讀檔規則辦理。
本文只出結論與定位，動手與否由人決定。

分支：`claude/consolidation-audit-001` · Base：`18c7494`

---

## 一、規模

| 指標 | 數值 |
|---|---:|
| Python 檔 | 3,993 |
| 總量 | 182.3 MB |
| 唯一內容（依 SHA-256） | 3,588 |
| 逐位元重複群組 | 253 |
| 多餘副本 | 405 檔 · 12.3 MB（6.8%） |

「逐位元重複」指 SHA-256 完全相同，不是「看起來像」。這類重複不需要行為等價證明——
同樣的位元組必然同樣的行為。

## 二、405 個多餘副本裡，只有 84 個能碰

這是本次稽核最重要的一條。直接拿 405 這個數字去砍會砍壞系統。

| 分類 | 群組 | 說明 |
|---|---:|---|
| **live-only** | 58 | 兩份都在活路徑 → **真正的整合目標**，84 個多餘副本、1.03 MB |
| archival-only | 75 | 兩份都在收容／退役區 → 刻意保留的快照，**不得動** |
| live + archival 混合 | 120 | 活的那份是本體，另一份是快照 → **不得動** |

判為 archival 的路徑標記：`references/intake`、`attachments/`、`SCOPE_COPY`、`sandbox/`、
`RetiredEngines`、`_superseded`、`_from_vap_iso_cleanup`、`_supportive_bundle`、
`Standalone_Package`、`legacy`、`backup`、`archive`、`site-packages`。

這些目錄在 VIA 治理裡是 `REFERENCE_DONT_COPY` / `register-read-only` 的登錄快照，
存在的目的就是保留當時的樣子。把它們「去重」等於銷毀證據。

> 第一次分類時我漏掉了 `RetiredEngines`、`_superseded`、`_supportive_bundle` 這幾個標記，
> 得到的 live 群組是 72 組。補上之後是 58 組。這裡記錄下來，因為分類標記的完整度
> 直接決定這份稽核可不可信。

## 三、最大的一筆：整棵 `VIA_HTML_UI` 樹重複

```
VIA_HTML_UI/                              226 檔 · 28 MB
VeritasIntelligenceAnalytics/VIA_HTML_UI/ 226 檔 · 28 MB
diff -rq → 0 處差異
```

**整棵樹逐位元相同**，不是個別檔案巧合重複。這是結構問題不是清理問題：
同一個 UI 引擎樹同時掛在倉庫頂層與 `VeritasIntelligenceAnalytics/` 底下，
兩邊都是活路徑，改其中一邊另一邊不會跟著動。

先決問題是**哪一邊是正典**，這要由 SSOT 決定，不是由稽核決定。

## 四、live-only 群組中值得優先處理的

| 份數 | 大小 | 檔名 | 位置 |
|---:|---:|---|---|
| 2 | 84 KB | `via_spec_extractor.py` | `VIA_HTML_UI/engines/` ↔ 巢狀同名樹 |
| 3 | 68 KB | `VIA_EnvManager.py` | `supportive modules/` ↔ `environment/` ↔ `40_Environment_Health/` |
| 2 | 43 KB | `via_triengine_hub.py` | `VIA_HTML_UI/engines/` ↔ 巢狀同名樹 |
| 2 | 29 KB | `VIA_GovernanceUIContractSeal_v0115F8.py` | — |
| 3 | 4 KB | `validate_standardized_zip.py` | — |
| 4 | 8 KB | `generate_module_validation.py` | — |
| 7 | 1 KB | `SUP_MDL550_PyAudit….py` | — |

`VIA_EnvManager.py` 的三份分散在三個功能分組目錄（`environment/`、`40_Environment_Health/`
與根層），屬於同一個活元件被放在三處，是最典型的整合目標。

## 五、不算整合目標的東西

以下在統計裡出現，但**不應該被消除**：

- **`__init__.py`**（7 份、6 份、3 份三組）——同內容的空 `__init__.py` 是 Python
  套件的正常結構，不是重複。
- **`check_libs.py`**（1 KB 級，多組）——若各 bundle 需要自帶一份以獨立執行，
  重複是刻意的。要先確認它是不是「每包自帶」的設計。

任何自動化去重如果沒有排除這兩類，產生的數字都會灌水。

## 六、倉庫自帶的全景稽核工具（另一條線）

`CGC_MDL158_VIAPanoramaAuditRepair_v0106.py` 不帶子命令執行會跑「稽核＋修復」，
本次結果：

```
RED · 問題 136(可同時修 1 · 順序修 0 · 只報位置待令 109 · 正典不得改 26 · 真 RED 0)
已修冊 11 筆複驗 GREEN 10 / 回歸 1
回歸：F535-ACCEL(冊說修好,現在又量到=真紅燈)
```

兩點必須記下來：

1. **`CLAUDE.md` 只保證 `read` / `slice` 子命令唯讀**；不帶子命令跑會進入修復模式。
   本次它自動修了 1 處，並改寫了三個 `VIA_Reports/` 產出檔——其中
   `VIA_UNIFIED_NLP_latest.json` 的 `roster` / `control` 被覆寫成 `UNSET`
   （因為本沙箱解析不到那些元件）。**已全部還原**，本分支不含這些變更。
   在不完整的環境跑修復模式會讓已登錄的報告資料退化。

2. **`F535-ACCEL` 是回歸**：修復冊記為已修，實測又紅。這不是本次稽核造成的，
   但它是目前唯一一筆「冊與實測不一致」，值得優先查。

## 七、沒有做的事

- 沒有刪除任何檔案
- 沒有改寫任何來源
- 沒有執行被稽核的檔（只做內容雜湊與路徑分類）
- 沒有判定 `VIA_HTML_UI` 哪一邊是正典——那要 SSOT 決定

## 八、建議順序

1. **先定 `VIA_HTML_UI` 的正典位置**（28 MB、226 檔，影響面最大，且是結構問題）
2. 合併 `VIA_EnvManager.py` 的三份到單一位置，其餘兩處改為引用
3. 其餘 live-only 群組逐案處理，每案先確認呼叫點（AST 定位）再動
4. archival 與混合群組**維持原狀**

逐位元相同的檔案不需要行為等價證明；但**移除副本仍會動到呼叫點**，
每一筆都要先查誰在 import 它。這份稽核沒有做呼叫點分析。
