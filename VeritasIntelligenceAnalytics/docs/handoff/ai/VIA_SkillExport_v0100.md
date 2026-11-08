# VIA_SkillExport v0100 —— 技能引擎:三層漸進載入 · 10 技能登錄表 · /export-skill

操作員 2026-11-08 的 NEXT 指定了一個具體首測:
`/export-skill /ast-diag` → 看 SKILL.md 與 scripts 是否都過 Celeritas 三檢 →
過了就 10 技能全匯出並登錄 VSKE。本支就是那個 `/export-skill`,以及它要過的那三檢。

## 一、為什麼不是再寫一份文件

v2.0 規格裡的 LAW-7(三層漸進載入)、`/export-skill` 的官方結構、PS/PY 強制檔案規則、
Celeritas 三檢 —— 這些寫成文件都很好看,但**沒有程式擋就會漂**。本支把其中可驗的部分
做成會擋的閘:三層是真的分層(各層字元數量得出來)、三檢是真的 AST 走訪(不是字串比對)、
`check` 會對壞技能夾判 RED。

## 二、三層漸進載入(真的分層)

| 層 | 內容 | 什麼時候載 | 動詞 |
|---|---|---|---|
| Tier1 | slash / name / 分類 / 觸發 / ↔加速器 / 一行描述 | **常駐** | `registry` |
| Tier2 | 該技能四段 SOP(Objective · Pre-flight · SOP · Output&Rollback) | 命中才載 | `sop <slash>` |
| Tier3 | `scripts/` `references/` `assets/` | 產檔 / 處理檔案才掛 | `export` |

分層省多少是**量出來的**,不是宣稱:

```
Tier1 索引     1,194 字元(常駐只付這個)
Tier2 全 SOP   5,099 字元
倍數           4.27×
```

也就是說:常駐索引只付 Tier1;10 個技能的 SOP 全載會多付 4.27 倍,而實際一次任務通常
只命中 1–3 個技能。`registry --depth` 可以逐技能看 Tier2 大小。

## 三、10 技能登錄表(↔ Celeritas 加速器,禁止重做輪子)

| Slash | Skill | 分類 | ↔加速器 | Status |
|---|---|---|---|---|
| /ast-diag | ast-driven-diagnosis | A | 01/03/06/13 | READY |
| /token-state | token-optimized-state | A | 02/12 | READY |
| /self-heal | self-healing-automation | A | 05/16/17/18/20 | READY |
| /local-env | local-first-virtualization | A | 21/22/23/24/25 | READY |
| /doc-extract | hybrid-layout-extraction | B | 19 | READY |
| /data-pipe | high-throughput-data-pipeline | B | 19 | READY |
| /quant-roll | dynamic-rolling-analytics | B | 11 | READY |
| /entity-norm | entity-ticker-normalization | B | 08 | READY |
| /canvas-zen | minimalist-canvas-design | C | 09 | READY |
| /ssot-gov | ssot-filename-governance | C | 08/26–30 | READY |

`registry` 會判 `READY` / `UNMAPPED`:對不上加速器編號的照實印 `UNMAPPED`,**不假裝 READY**。
本輪 10/10 READY。

技能的 SOP 裡寫的是本倉**真的踩過的坑**,不是通用建議。例如:

* `/data-pipe` ④「寫完要把整個合併後的庫對帳回去」—— 因為只送 `added` 會讓 JSON 與 DuckDB 永久分歧,
  這是 WorkflowViz 那輪實際發生的事。
* `/canvas-zen` ④「缺資料畫骨架不畫線,絕不畫假 K 線」—— VisualLock 那輪的規矩。
* `/ssot-gov` ②「新需求必須同時登中央需求冊與相應工作流冊」—— Codex #607 P1 抓到的那條。

## 四、/export-skill 產出的官方結構

```
<skill-name>/
  SKILL.md                     YAML frontmatter(name / description)+ 四段
  scripts/<name>_v0100.py      PY 骨架(參數置頂 · 禁 input() · 有 __main__ · 加速器 graceful)
  references/rules_v0100.md    ↔加速器對應表 + 這個技能不做什麼 + 收尾誠實律
  assets/README.md             沒有資產就寫明為什麼沒有,不塞假檔
```

**不產 .ps1**。CLAUDE.md 禁改 .ps1(L70),鬆散 .ps1 也從不提交。所以:

* `scripts/` 一律 Python。
* PS 的八段式 / 引號 / 借用函式 / 禁用動作規則保留成**唯讀驗證器**:`check --ps <檔>`,
  給操作員 Windows 側自己寫的 PS 用。**本支不代寫、不代改 PS。**

## 五、三檢 + PY 骨架規則(Python 這邊是真的 AST 驗)

| # | 檢 | 怎麼驗 |
|---|---|---|
| ① | 語法剖析 | `ast.parse`,再 `compile`(ast 過但 compile 不過真的會發生,例如橋注在 `from __future__` 之前) |
| ② | 借用函式自帶預設 | 走訪每個 `FunctionDef`,凡原始碼含 `vc.` / `VIA_ACCEL.` / `VeritasCeleritas` 的,其位置參數必須有預設值 —— 加速器缺席時也叫得動 |
| ③ | 路徑全引號 / 不走 shell | 走訪 `Call`,抓 `os.system` 與 `shell=True` |
| ④ | 有 `__main__` | 走訪頂層 `If`,比對 `__name__` |
| ⑤ | 禁 `input()` | 走訪 `Call` 找 `input` |
| ⑥ | main 有護欄裝飾 | `funcs['main'].decorator_list` 非空 |
| ⑦ | `CeleritasKernel.register` | 有核心登錄呼叫 |
| ⑧ | 加速器缺席 graceful | `import VeritasCeleritas` 必須被 `try:` 包住 |

**裝飾器豁免是窄的**:②「借用函式自帶預設」對裝飾器不適用 —— 被裝飾的函式本來就該是位置參數。
豁免條件是**結構判定**:名字真的出現在某個 `decorator_list` 裡 **且** 恰好一個位置參數、
無 `*args`、無 keyword-only。沒被當裝飾器用的單參數借用函式**照樣 FAIL**(有兩個測守著)。

PS 側(唯讀):

| # | 檢 | 本容器狀態 |
|---|---|---|
| ① | `Parser.ParseFile` | **UNAVAILABLE** —— 容器沒有 pwsh。有 pwsh 時才真剖析 |
| ② | 借用函式自帶預設 | 文字剖析:抓 `[Parameter(Mandatory=$true` |
| ③ | 路徑全引號 | 文字剖析:抓帶磁碟機代號 / `$env:` 的裸路徑 |
| ④ | 禁用動作 | `Invoke-Expression` / `WebClient` / `HKLM:` / `Stop-Process` |

`UNAVAILABLE` **不計入通過數、也不算失敗**;收據會寫明「文字剖析,不是 Parser.ParseFile」。
沒有 .ps1 時 PS 三檢標 `N/A`(無適用出口 → N/A,不是灰)。

## 六、首測與全輪結果(容器實跑)

```
/export-skill /ast-diag   三檢 GREEN · 通過 19/19 · N/A 1 · 灰 0
  SKILL.md sha256 ef857dc99a41c287…    script sha256 f3616cea5c9b063b…
10 技能全匯出             GREEN 10/10(各 19/19)· 每個 4 檔
VSKE 登錄                 VIA_VSKE_SkillRegistry_v0100.json · 10 筆 · 只增不減(已存在拒寫)
省 Token 實測             6 個真檔 759,075 字元 → 骨架卡 46,494 字元 · 省 93.9%(真測,非估)
自測                      56/56 PASS
```

每個匯出的腳本都**真的跑過**:`python3 -I <script> --json` rc 0,收據照實印
`accel_bridge: ABSENT` / `kernel: ABSENT` / `lamp: GRAY` —— 骨架期不報綠。

## 七、開發中被自己的閘抓到的三件事

1. **樣板自己過不了 ②**(`_shield(fn)` 判缺預設)→ 不是樣板錯,是**規則太寬**;改成上面那個
   結構判定的窄豁免,並補「沒被當裝飾器用就不豁免」與「真裝飾器得豁免」兩個測。
2. **`tokens` 路徑雙前綴** —— 鎖冊路徑是相對倉根寫的,我拿 VIA 根去接 → 工具找不到;
   改成倉根 / VIA 根都試。
3. **假綠** —— 三段 GREEN + ④ YELLOW 卻印 `[總燈] GREEN`。這是 Codex 在 #607 抓過的同一類錯
   (DB 失敗不進總燈)。改成 ④ 的燈進總燈 + 迴歸測試(量不到時斷言總燈不是 GREEN 且寫明原因)。

## 八、怎麼跑

```bash
# Tier1 索引(常駐只付這層)
python3 "docs/handoff/ai/VIA_SkillExport_v0100.py" registry
python3 "docs/handoff/ai/VIA_SkillExport_v0100.py" registry --depth     # 逐技能 Tier2 大小

# Tier2:只載入一個技能的 SOP
python3 "docs/handoff/ai/VIA_SkillExport_v0100.py" sop /ast-diag

# Tier3:匯出 + 三檢
python3 "docs/handoff/ai/VIA_SkillExport_v0100.py" export /ast-diag --out VIA_Reports/skills
python3 "docs/handoff/ai/VIA_SkillExport_v0100.py" export-all --out VIA_Reports/skills

# 驗別人寫的技能夾 / 驗一支 PS(唯讀,不代修)
python3 "docs/handoff/ai/VIA_SkillExport_v0100.py" check <技能夾…>
python3 "docs/handoff/ai/VIA_SkillExport_v0100.py" check --ps <某支.ps1>

# 整輪 + 自測
python3 "docs/handoff/ai/VIA_SkillExport_v0100.py" all --out VIA_Reports/skills
python3 "docs/handoff/ai/VIA_SkillExport_v0100.py" --selftest
```

輸出落 `VIA_Reports/skills/`(**不提交**,照本倉慣例)。

## 九、照實 BLOCKED

* **Manus 那一側的首測跑不到** —— 那不是我的執行環境。操作員的 NEXT 要「兩邊比對」,
  本倉只完成這半邊;不冒充雙邊都通過。
* **`.claude/skills/` 落地**:v2.0 說 Cowork/Code 用 `.claude/skills/<name>/SKILL.md`。
  本倉 `.claude/skills/` 存在,但把 10 個技能裝進去會改變這個會話自己的技能集,
  **那是操作員的環境決定,不是我該替他裝的** → 匯出產物留在 `VIA_Reports/skills/`,
  要落地請操作員自行複製(路徑與結構已照官方格式)。
* **`pwsh` 不在容器** → PS `Parser.ParseFile` 這一檢在這裡做不到,一律 UNAVAILABLE。
* **numba 不在容器** → `/data-pipe` 不宣稱 JIT 加速。

五系統對等獨立不變:本支只讀各系統自報值,不改他系統正本 / 冊 / 號 / 檔。
