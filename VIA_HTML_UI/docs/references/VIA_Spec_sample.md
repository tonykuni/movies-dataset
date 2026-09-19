# VIA E1 sample — 規格書（VSX v0100）

- contract: `VIA_SPEC_IR/1.0` · 產生 2026-09-06 10:36:19 · 規格項 802 · 缺口 117 · registry 新增 104 / 累計 20112
- 證據等級：**V** 結構明確（標籤/AST/schema）· **M** 模式命中（規則句/正則）· **P** 推論（型別/單位/名稱）

## 來源

| 檔案 | 類型 | bytes | blake2s | 編碼 |
|---|---|---:|---|---|
| Veritas_VOFIE_Reconstructed.docx | docx | 40596 | `33c3808b6be552c1` | utf-8 |
| nlp_default.json | json | 3671 | `99fbdaf933949f51` | utf-8-sig |
| nlp_readme.md | markdown | 24429 | `b91fb303c010d066` | utf-8-sig |
| ves.html | html | 1563729 | `cdcd3936168c8b3b` | utf-8-sig |
| vofie_readme.md | markdown | 9717 | `74618b287f265ad9` | utf-8-sig |
| vshp_ui.html | html | 48889 | `cbf37c3147d78796` | utf-8-sig |

## 1. UI 規格

### 1.1 元件（40）

| ID | 元件 | 選擇器 | role | data-* | 事件 | 子元件 | 文字 | 等級 |
|---|---|---|---|---|---|---:|---|---|
| SPEC-UI-COMPCLS-345CD18A2597 | <header> header | `html > body > header` |  |  |  | 2 | VIA Engine Standardizer v0600 AST 盤點 → 功 | V |
| SPEC-UI-COMPCLS-DD8FD80FD0E7 | <div> kpi ×2 | `html > body > div.kpis` |  |  |  | 10 | 515 .py 檔案 12327 函式/方法 50 邏輯完全相同群 0 功能同· | V |
| SPEC-UI-COMPCLS-49A0518DA2FB | <div> kpi ×16 | `html > body > div.kpis > div.kpi` |  |  |  | 2 | 515 .py 檔案 | V |
| SPEC-UI-COMPCLS-4ED504176400 | <div> tab | `html > body > div.tabs` |  |  |  | 12 | 總覽矩陣 ★ 功能同·工具異 邏輯完全相同 近似重複 風險稽核 檔案 全部函式  | V |
| SPEC-UI-COMPCLS-BABD2E9151A6 | <div> tab | `html > body > div.tabs > div.tab.on` |  | data-p |  | 0 | 總覽矩陣 | V |
| SPEC-UI-COMPCLS-3E8E5266DB03 | <div> tab ×11 | `html > body > div.tabs > div.tab` |  | data-p |  | 0 | ★ 功能同·工具異 | V |
| SPEC-UI-COMPONEN-C6EA2DD4B166 | <div> p0 | `div#p0` |  |  |  | 17 | 能力軸 × 工具家族 熱度矩陣 同一列裡出現 ≥2 個工具欄位 = 「功能相同、 | V |
| SPEC-UI-COMPCLS-D21BFAE094CF | <span> pill ×1143 | `div#p0 > span.pill.pt` |  |  |  | 0 | urllib ×1110 | V |
| SPEC-UI-COMPONEN-ED41FB9F8119 | <div> p1 | `div#p1` |  |  |  | 2 | 功能相同 · 工具相異（標準化整併主目標） FID 函式 檔案:行 參數 工具  | V |
| SPEC-UI-COMPCLS-F681219D90CF | <table> table ×12 | `div#p1 > table` |  |  |  | 1850 | FID 函式 檔案:行 參數 工具 風險 （無） | V |
| SPEC-UI-COMPONEN-A1A31FB6ED81 | <div> p2 | `div#p2` |  |  |  | 2 | 正規化 AST 結構完全相同（變數名/docstring/行號已抹除） FID  | V |
| SPEC-UI-COMPCLS-9BD54A8C82DA | <span> pill ×6179 | `div#p2 > table > tr.c0 > td:nth-of-type(6) > span.pill.pr` |  |  |  | 0 | R03 | V |
| SPEC-UI-COMPONEN-16CBC2A5FB87 | <div> p3 | `div#p3` |  |  |  | 2 | 近似重複（同工具、名稱/參數高度相似） FID 函式 檔案:行 參數 工具 風險 | V |
| SPEC-UI-COMPCLS-9316C317EB7F | <span> pill ×5323 | `div#p3 > table > tr.c0 > td > span.pill.pb` |  |  |  | 0 | TRANSFORM | V |
| SPEC-UI-COMPONEN-7515E36C858C | <div> p4 | `div#p4` |  |  |  | 3 | 25 項風險稽核 · 命中統計 代碼 風險 命中 解決方案 R03_MISSIN | V |
| SPEC-UI-COMPONEN-CADD14C10732 | <div> p5 | `div#p5` |  |  |  | 1 | 檔案 行數 函式 工具 狀態 _pydecimal.py 6426 237 re | V |
| SPEC-UI-COMPCLS-1AA6EFB3FE63 | <span> pill ×528 | `div#p5 > table > tr:nth-of-type(2) > td:nth-of-type(5) > span.pill.pd` |  |  |  | 0 | OK | V |
| SPEC-UI-COMPONEN-EF35EEDBF6F9 | <div> p9 | `div#p9` |  |  |  | 5 | DORMANT 候選（公開函式、fan_in=0、非入口/非裝飾器路由） v06 | V |
| SPEC-UI-COMPONEN-3FE37704A7EC | <div> p10 | `div#p10` |  |  |  | 6 | CPU 跑得動的 ML / DL 工具（自動偵測 + 微基準） Python 3 | V |
| SPEC-UI-COMPCLS-849E9D4B2B89 | <span> pill ×13 | `div#p10 > table:nth-of-type(1) > tr:nth-of-type(9) > td:nth-of-type(3) > span.pill.pg` |  |  |  | 0 | MISSING | V |
| SPEC-UI-COMPONEN-0053B34FE62A | <div> p11 | `div#p11` |  |  |  | 9 | 專案自有儲存（ves_store · Parquet 分區 · append-o | V |
| SPEC-UI-COMPONEN-4FA9C3208DA8 | <div> p6 | `div#p6` |  |  |  | 3 | 函式共 12327 筆，表格只嵌前 5000 筆；完整清單在 ves_inven | V |
| SPEC-UI-COMPONEN-4843DC0881B3 | <input> q | `input#q` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-2E758B1B77CA | <table> fnt | `table#fnt` |  |  |  | 5001 | FID 函式 檔案:行 能力 工具 結構雜湊 風險 FN-00001 _Feat | V |
| SPEC-UI-COMPONEN-7DC139BEF0FD | <div> p8 | `div#p8` |  |  |  | 6 | 分類法（外掛 ves_taxonomy.json · 只增不減） 歸為 OTHE | V |
| SPEC-UI-COMPONEN-007E0799061D | <div> p7 | `div#p7` |  |  |  | 5 | 已生成（全新目錄，原檔未動；重跑時既有 adapter 保留、新版本寫 _vN， | V |
| SPEC-UI-COMPCLS-B37DEAC2FAEF | <header> header | `html > body > div.wrap > header.top` |  |  |  | 2 | 析 VIA SuperHtml Parser · 解讀台 把 HTML 檔（連同 | V |
| SPEC-UI-COMPONEN-578579AD9D00 | <section> inputs | `section#inputs` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-25B65DBEBE40 | <button> go | `button#go` |  |  |  | 0 | 開始解讀 | V |
| SPEC-UI-COMPCLS-1C88E68DFB9F | <label> label ×3 | `html > body > div.wrap > div.cmd > div.opts > label:nth-of-type(1)` |  |  |  | 1 | 內容轉 Markdown | V |
| SPEC-UI-COMPONEN-39AEA2067291 | <input> optContent | `input#optContent` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-597DC1C2096C | <input> optCss | `input#optCss` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-64018695A676 | <input> optJs | `input#optJs` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-5EC2BE6931CD | <i> bar | `i#bar` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-7FE60006C6C0 | <div> status | `div#status` |  |  |  | 0 | 五個位置皆空 — 拖入或點擊選檔 | V |
| SPEC-UI-COMPONEN-F570914D8B5F | <section> results | `section#results` |  |  |  | 2 |  | V |
| SPEC-UI-COMPONEN-738EA0F7936C | <div> tabs | `div#tabs` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-E16A8A298851 | <div> panels | `div#panels` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-D7E620037F26 | <input> picker | `input#picker` |  |  |  | 0 |  | V |
| SPEC-UI-COMPONEN-52BB27F80880 | <input> pickerDir | `input#pickerDir` |  |  |  | 0 |  | V |

### 1.2 表單欄位（6）

| ID | 欄位 | 型別 | 必填 | 驗證 | 選項 | label | 表單 |
|---|---|---|---|---|---|---|---|
| SPEC-UI-FORM_FIE-BB7570EA8890 | q | text |  |  |  | 篩選 函式 / 檔案 / 工具 / 能力… |  |
| SPEC-UI-FORM_FIE-F927BFD83650 | optContent | checkbox |  |  |  |  |  |
| SPEC-UI-FORM_FIE-D17CB5300E0F | optCss | checkbox |  |  |  |  |  |
| SPEC-UI-FORM_FIE-4FFC85265DF7 | optJs | checkbox |  |  |  |  |  |
| SPEC-UI-FORM_FIE-8D3418851300 | picker | file |  | accept=.html,.htm,.js,.mjs,.css,.txt |  |  |  |
| SPEC-UI-FORM_FIE-7CFA63DBC843 | pickerDir | file |  |  |  |  |  |

### 1.x 版面（grid/flex）（18）

- `.kpis` .kpis: flex {"props": {"gap": "10px"}}
- `.tabs` .tabs: flex {"props": {"gap": "4px"}}
- `.mx` .mx: grid {"props": {"gap": "2px"}}
- `header.top` header.top: flex {"props": {"align-items": "flex-end", "justify-content": "space-between", "gap": "24px"}}
- `.brand` .brand: flex {"props": {"gap": "16px", "align-items": "center"}}
- `.seal` .seal: grid {"props": {}}
- `/* five input positions */ .inputs` /* five input positions */ .inputs: grid {"props": {"grid-template-columns": "repeat(5,1fr)", "gap": "14px"}}
- `.slot` .slot: flex {"props": {"flex-direction": "column"}}
- `.slot .head` .slot .head: flex {"props": {"align-items": "baseline", "gap": "8px"}}
- `.drop` .drop: flex {"props": {"flex-direction": "column", "align-items": "center", "justify-content": "center", "gap": "6px"}}
- `.files li` .files li: flex {"props": {"gap": "8px", "align-items": "center"}}
- `.slot .foot` .slot .foot: flex {"props": {"gap": "6px"}}
- `/* command bar */ .cmd` /* command bar */ .cmd: flex {"props": {"align-items": "center", "gap": "14px"}}
- `.opts` .opts: flex {"props": {"gap": "16px"}}
- `.opts label` .opts label: flex {"props": {"gap": "6px", "align-items": "center"}}
- `.filebar` .filebar: flex {"props": {"gap": "6px"}}
- `.sub` .sub: flex {"props": {"gap": "2px"}}
- `.kpis` .kpis: grid {"props": {"grid-template-columns": "repeat(auto-fit,minmax(120px,1fr))", "gap": "10px"}}

## 2. 設計 Token

- **CSS 變數**（25）：`--b: #4c78a8`, `--t: #439a9a`, `--g: #9c9890`, `--up: #c96b5a`, `--dn: #5a9e6f`, `--paper: #f5f4f0`, `--i0: #1c1b19`, `--i1: #3d3b37`, `--i2: #6b6862`, `--i3: #b8b5ae`, `--i4: #e6e3dc`, `--bg: #f5f4f0`, `--paper: #fff`, `--ink: #1e1d1a`, `--ink-2: #5b5955`, `--ink-3: #8d8a84`, `--line: #dbd9d3`, `--blue: #4c78a8`, `--teal: #439a9a`, `--down: #5a9e6f`, `--amber: #d9a441`, `--r: 2px`, `--display: 'Syne',ui-sans-serif,system-ui,sans-serif`, `--body: 'DM Sans','Noto Sans TC','Microsoft JhengHei',ui-sans-serif,sans-serif`, `--mono: 'DM Mono','Cascadia Mono',Consolas,ui-monospace,monospace`
- **顏色**（44）：`rgba(76,120,168,0.31)`, `#fff`, `rgba(76,120,168,0.22)`, `rgba(76,120,168,0.16)`, `rgba(76,120,168,0.15)`, `rgba(76,120,168,0.19)`, `rgba(76,120,168,0.17)`, `rgba(76,120,168,0.18)`, `rgba(76,120,168,1.00)`, `rgba(76,120,168,0.58)`, `rgba(76,120,168,0.28)`, `rgba(76,120,168,0.23)`, `#4c78a8`, `#439a9a`, `#9c9890`, `#c96b5a`, `#5a9e6f`, `#f5f4f0`, `#1c1b19`, `#3d3b37`, `#6b6862`, `#b8b5ae`, `#e6e3dc`, `#eef3f8`, `#ecf5f5`, `#dfe8f2`, `#dcefee`, `#ecebe7`, `#f6e2dd`, `#e0eee4`, `#1e1d1a`, `#5b5955`, `#8d8a84`, `#dbd9d3`, `#d9a441`, `#e0d36a`, `#8a6cb0`, `#b9b6ae`, `#eef5f5`, `#eeede8`
- **字型**（7）：`"DM Sans",system-ui,sans-serif`, `Syne,"DM Sans",sans-serif`, `"DM Mono",monospace`, `var(--body)`, `'Noto Serif TC','PMingLiU',serif`, `var(--display)`, `var(--mono)`
- **字級**（11）：`14px`, `13px`, `22px`, `12px`, `11px`, `30px`, `24px`, `20px`, `11.5px`, `15px`, `12.5px`
- **間距**（47）：`0`, `22px 28px 10px`, `4px`, `10px`, `14px 28px`, `10px 14px`, `0 28px`, `9px 14px`, `18px 28px`, `6px 8px`, `5px 8px`, `1px 7px`, `1px 2px 1px 0`, `2px`, `6px 0`, `6px 10px`, `0 auto`, `26px 28px 60px`, `24px`, `18px`, `16px`, `2px 0 0`, `14px`, `22px`, `8px`, `10px 12px 8px`, `auto`, `6px`, `12px`, `3px 0`, `0 2px`, `0 10px 10px`, `5px 6px`, `12px 14px`, `10px 22px`, `8px 14px`, `-1px`, `18px 20px 24px`, `4px 10px`, `6px 12px`
- **圓角**（8）：`8px`, `8px 8px 0 0`, `10px`, `4px`, `6px`, `var(--r)`, `3px`, `var(--r) var(--r) 0 0`
- **斷點**（2）：`1100px`, `720px`

## 3. 互動邏輯

### 3.x 事件（6）

- `L2104` onclick — `document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));document.querySelectorAll('.p`
- `L2105` input — `const q=document.getElementById('q');q&&q.addEventListener('input',()=>{const v=q.value.toLowerCase();document.querySelectorAll('#fnt tr').forEach((r,i)=>{if(i=`
- `L176` drop — `drop.addEventListener('drop', e=>handleDrop(sl, e.dataTransfer));`
- `L177` click — `drop.addEventListener('click', e=>{ if(e.target.closest('button[data-rm]')){ sl.files.splice(+e.target.dataset.rm,1); refresh(); return; } if(!sl.files.length) `
- `L178` keydown — `drop.addEventListener('keydown', e=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); pick(sl,false);} });`
- `L193` change — `$('#picker').addEventListener('change', async e=>{ if(pickTarget) await addFiles(pickTarget, Array.from(e.target.files)); e.target.value=''; });`

## 4. API / 函式規格

### 4.x 端點（前端呼叫）（1）

| ID | 規格 | 來源 | 等級 |
|---|---|---|---|
| SPEC-API-CALL-3B18DBC4D362 | `FETCH (dynamic)` | vshp_ui.html:L307 | V |

### 4.x 函式簽章（30）

| ID | 規格 | 來源 | 等級 |
|---|---|---|---|
| SPEC-API-FUNCTION-F44A9C90C416 | `clip(s,n)` | vshp_ui.html:L156 | V |
| SPEC-API-FUNCTION-DFB7C21930CF | `renderSlots()` | vshp_ui.html:L160 | V |
| SPEC-API-FUNCTION-CA85E9469415 | `refresh()` | vshp_ui.html:L191 | V |
| SPEC-API-FUNCTION-B20A49180AAA | `pick(sl, dir)` | vshp_ui.html:L192 | V |
| SPEC-API-FUNCTION-69261E1A7526 | `handleDrop(sl, dt)` | vshp_ui.html:L196 | V |
| SPEC-API-FUNCTION-E16D0EFF8A79 | `walkEntry(entry, prefix)` | vshp_ui.html:L204 | V |
| SPEC-API-FUNCTION-4E0B3D225B57 | `readAll()` | vshp_ui.html:L211 | V |
| SPEC-API-FUNCTION-9173858CB523 | `addFiles(sl, files)` | vshp_ui.html:L216 | V |
| SPEC-API-FUNCTION-9A39CF0338DB | `updateGo()` | vshp_ui.html:L227 | V |
| SPEC-API-FUNCTION-C0E8C3CD7A9B | `setStatus(msg, cls)` | vshp_ui.html:L232 | V |
| SPEC-API-FUNCTION-28B814CFA6E2 | `selectorOf(node)` | vshp_ui.html:L237 | V |
| SPEC-API-FUNCTION-7099F55A8F28 | `depthOf(n)` | vshp_ui.html:L250 | V |
| SPEC-API-FUNCTION-01977C6C0AAC | `parseHtmlSpec(name, html, companions, opts)` | vshp_ui.html:L252 | V |
| SPEC-API-FUNCTION-4E4D29350B20 | `lineAt(src,i)` | vshp_ui.html:L295 | V |
| SPEC-API-FUNCTION-6D49DD11B6BC | `analyzeJs(scripts)` | vshp_ui.html:L296 | V |
| SPEC-API-FUNCTION-7412557F21D2 | `shortTarget(s)` | vshp_ui.html:L319 | V |
| SPEC-API-FUNCTION-38B83143853D | `enclosingFn(functions, file, line)` | vshp_ui.html:L320 | V |
| SPEC-API-FUNCTION-CB04359F18A8 | `buildChains(domEvents, js)` | vshp_ui.html:L321 | V |
| SPEC-API-FUNCTION-18FEDA838E96 | `analyzeCss(sheets)` | vshp_ui.html:L334 | V |
| SPEC-API-FUNCTION-3A21A59A550F | `walk(text,media)` | vshp_ui.html:L337 | V |
| SPEC-API-FUNCTION-5E5D590B0FA0 | `htmlToMarkdown(doc)` | vshp_ui.html:L356 | V |
| SPEC-API-FUNCTION-4F6E09684136 | `block(n,depth)` | vshp_ui.html:L360 | V |
| SPEC-API-FUNCTION-A43271B18D6A | `mdTable(headers, rows)` | vshp_ui.html:L380 | V |
| SPEC-API-FUNCTION-1C85B833197D | `buildMarkdown(s, slotIdx)` | vshp_ui.html:L381 | V |
| SPEC-API-FUNCTION-D0F84406768C | `kv(rows)` | vshp_ui.html:L426 | V |
| SPEC-API-FUNCTION-124DC8A1E6FA | `tbl(headers, rows, monoCols)` | vshp_ui.html:L427 | V |
| SPEC-API-FUNCTION-5870FE13494D | `specHtml(s)` | vshp_ui.html:L428 | V |
| SPEC-API-FUNCTION-1E0CA661D913 | `renderResults(results)` | vshp_ui.html:L449 | V |
| SPEC-API-FUNCTION-17ECDE30EDD8 | `stripForJson(s)` | vshp_ui.html:L480 | V |
| SPEC-API-FUNCTION-7C7CD52234AB | `download(name, text, type)` | vshp_ui.html:L481 | V |

## 5. 資料規格

### 表格 `L7` （7 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| <w:tcPr><w:tcW w:type="dxa" w:w="2700"/><w:shd w:fill="0F5F73"/><w:tcMar><w:top w:type="dxa" w:w="80"/><w:bottom w:type="dxa" w:w="80"/><w:start w:type="dxa" w:w="120"/><w:end w:type="dxa" w:w="120"/></w:tcMar></w:tcPr><w:p><w:r><w:rPr><w:b/><w:color w:val="FFFFFF"/></w:rPr><w:t>Field / 欄位 | string |  | <w:tcPr><w:tcW w:type="dxa" w:w="2700"/><w:vAlign w:val="center"/><w:shd w:fill="E8EEF5"/><w:tcMar><w:top w:type="dxa" w:w="80"/><w:bottom w:type="dxa" w:w="80"/><w:start w:type="dxa" w:w="120"/><w:end w:type="dxa" w:w="120"/></w:tcMar></w:tcPr><w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Run ID, <w:tcPr><w:tcW w:type="dxa" w:w="2700"/><w:vAlign w:val="center"/><w:shd w:fill="E8EEF5"/><w:tcMar><w:top w:type="dxa" w:w="80"/><w:bottom w:type="dxa" w:w="80"/><w:start w:type="dxa" w:w="120"/><w:end w:type="dxa" w:w="120"/></w:tcMar></w:tcPr><w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Quality gate / 品質, <w:tcPr><w:tcW w:type="dxa" w:w="2700"/><w:vAlign w:val="center"/><w:shd w:fill="E8EEF5"/><w:tcMar><w:top w:type="dxa" w:w="80"/><w:bottom w:type="dxa" w:w="80"/><w:start w:type="dxa" w:w="120"/><w:end w:type="dxa" w:w="120"/></w:tcMar></w:tcPr><w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Sources / 來源 |
| <w:tcPr><w:tcW w:type="dxa" w:w="6660"/><w:shd w:fill="0F5F73"/><w:tcMar><w:top w:type="dxa" w:w="80"/><w:bottom w:type="dxa" w:w="80"/><w:start w:type="dxa" w:w="120"/><w:end w:type="dxa" w:w="120"/></w:tcMar></w:tcPr><w:p><w:r><w:rPr><w:b/><w:color w:val="FFFFFF"/></w:rPr><w:t>Value / 內容 | string |  | <w:tcPr><w:tcW w:type="dxa" w:w="6660"/><w:vAlign w:val="center"/><w:tcMar><w:top w:type="dxa" w:w="80"/><w:bottom w:type="dxa" w:w="80"/><w:start w:type="dxa" w:w="120"/><w:end w:type="dxa" w:w="120"/></w:tcMar></w:tcPr><w:p><w:r><w:t>RUN-B000FD820DE58953, <w:tcPr><w:tcW w:type="dxa" w:w="6660"/><w:vAlign w:val="center"/><w:tcMar><w:top w:type="dxa" w:w="80"/><w:bottom w:type="dxa" w:w="80"/><w:start w:type="dxa" w:w="120"/><w:end w:type="dxa" w:w="120"/></w:tcMar></w:tcPr><w:p><w:r><w:t>PASS, <w:tcPr><w:tcW w:type="dxa" w:w="6660"/><w:vAlign w:val="center"/><w:tcMar><w:top w:type="dxa" w:w="80"/><w:bottom w:type="dxa" w:w="80"/><w:start w:type="dxa" w:w="120"/><w:end w:type="dxa" w:w="120"/></w:tcMar></w:tcPr><w:p><w:r><w:t>1 |

### 表格 `L64` VIA NLP One Engine / 四級路由（4 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| Tier | integer |  | 1, 2, 3 |
| 預設工作 | string |  | 正規化、修復、關鍵字、分類、抽取式摘要, 文章結構化、跳題重建、NER、知識圖譜, Embedding／深度語意關聯／語義檢索／離線翻譯 |
| 主要元件 | string |  | Python 規則、可選 Jieba、Scikit-learn, CPU Sparse Semantics、Regex NER、可選 spaCy, Sentence Transformers、ONNX Runtime、Argos |
| 資源策略 | string |  | 常駐輕量, 有界特徵、延遲載入, 明確啟用、資源准入 |

### 表格 `L55` （1 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| FID | string |  | （無） |
| 函式 | empty |  |  |
| 檔案:行 | empty |  |  |
| 參數 | empty |  |  |
| 工具 | empty |  |  |
| 風險 | empty |  |  |

### 表格 `L56` （168 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| FID | string |  | · 成員 3 · I001, FN-00024, FN-00034 |
| 函式 | string |  | Coroutine.throw, AsyncGenerator.athrow, Generator.throw |
| 檔案:行 | string |  | _collections_abc.py:160, _collections_abc.py:246, _collections_abc.py:366 |
| 參數 | string |  | typ, val, tb, typ, val, tb, typ, val, tb |
| 工具 | enum(os|os print|sqlite|urllib|—) |  | —, —, — |
| 風險 | enum(R02 R03|R03|R03 R17) |  | R03, R03, R03 |

### 表格 `L224` （1849 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| FID | string |  | · 成員 141 · 工具集=0 檔案=71 相似=1.0 N001 TRANSFORM 超大群：連鎖傳遞造成，建議 --threshold 調高至 0.8 提, FN-03988, FN-03981 |
| 函式 | string |  | IncrementalEncoder.encode, Codec.encode, Codec.encode |
| 檔案:行 | string |  | encodings/cp1255.py:18, encodings/cp1254.py:11, encodings/cp775.py:11 |
| 參數 | string |  | input, final, input, errors, input, errors |
| 工具 | string |  | —, —, — |
| 風險 | enum(R02|R02 R03|R03|R03 R07|R03 R18|R03 R28|R07|R18) |  | R03, R03, R03 |

### 表格 `L2073` （12 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| 代碼 | string |  | R03_MISSING_TYPE_HINTS, R07_KWARGS_ABUSE, R16_MODULE_MUTABLE_STATE |
| 風險 | string |  | 缺乏型別提示, **kwargs 濫用, 模組層可變狀態(執行緒安全) |
| 命中 | integer |  | 8022, 321, 269 |
| 解決方案 | string |  | 重構前用 MonkeyType/PyAnnotate 收集執行期型別自動補齊, 防腐層：已知參數→強型別欄位，未知→request.config, Factory 每次回傳新實例；contextvars 隔離 |

### 表格 `L2075` （515 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| 檔案 | string |  | _pydecimal.py, xml/dom/minidom.py, turtle.py |
| 行數 | integer |  | 6426, 2009, 4208 |
| 函式 | integer |  | 237, 215, 214 |
| 工具 | string |  | re, , os re |
| 狀態 | string |  | OK R16, OK R26, OK R01 R16 R19 R26 |

### 表格 `L2077` （800 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| FID | string |  | FN-00002, FN-00003, FN-00014 |
| 函式 | string |  | _Feature.getOptionalRelease, _Feature.getMandatoryRelease, aix_buildtag |
| 檔案:行 | string |  | __future__.py:88, __future__.py:95, _aix_support.py:95 |
| fan_out | integer |  | 0, 0, 2 |
| 等級 | enum(模糊命中 0 STRONG) |  | 模糊命中 0 STRONG, 模糊命中 0 STRONG, 模糊命中 0 STRONG |

### 表格 `L2079` （1 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| 檔案 | string |  | 無 |
| 原因 | empty |  |  |

### 表格 `L2082` （21 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| 工具 | string |  | numpy, scipy, pandas |
| 類別 | enum(accel|core|dl|fin|ml) |  | core, core, core |
| 狀態 | enum(MISSING|OK) |  | OK, OK, OK |
| 版本 | string |  | 2.4.4, 1.17.1, 3.0.2 |
| import ms | number |  | 88.4, 89.6, 426.3 |
| 備註 | string |  | , ,  |

### 表格 `L2083` （5 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| 基準 | string |  | numpy_matmul_1024f32, sklearn_rf50_5k, onnxruntime_providers |
| 狀態 | enum(OK) |  | OK, OK, OK |
| ms | number |  | 122.9, 1368.9, 96.5 |
| 備註 | string |  | 268407200.0, 1.0, ['AzureExecutionProvider', 'CPUExecutionProvider'] |

### 表格 `L2088` （1 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| run_id | string |  | 首輪 |
| functions | empty |  |  |
| risk_M | empty |  |  |
| risk_P | empty |  |  |
| gates | empty |  |  |

### 表格 `L2091` （5000 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| FID | string |  | FN-00001, FN-00002, FN-00003 |
| 函式 | string |  | _Feature.__init__, _Feature.getOptionalRelease, _Feature.getMandatoryRelease |
| 檔案:行 | string |  | __future__.py:83, __future__.py:88, __future__.py:95 |
| 能力 | string |  | OTHER, READ, READ |
| 工具 | string |  | , ,  |
| 結構雜湊 | string |  | 9384363e135d, 21e6de9add23, fde4202c2f5f |
| 風險 | string |  | R03, ,  |

### 表格 `L2095` （80 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| 未知首動詞 | string |  | set, close, getregentry |
| 命中 | integer |  | 205, 134, 120 |
| 建議 | enum(→ pending_verbs (待填能力軸)) |  | → pending_verbs (待填能力軸), → pending_verbs (待填能力軸), → pending_verbs (待填能力軸) |

### 表格 `L2097` （3 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| 檔案 | string |  | modulefinder.py, ctypes/__init__.py, encodings/__init__.py |
| 字串型模組名 | string |  | __main__, comtypes.server.inprocserver, encodings. |

### 表格 `L38` Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / 固定五個主要輸出（5 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| # | integer |  | 1, 2, 3 |
| 檔案 | string |  | `Veritas_VOFIE_Reconstructed.md`, `Veritas_VOFIE.html`, `Veritas_VOFIE_ComponentSpecs.json` |
| 定位 | string |  | 完整人可讀內容、ST、整合索引與來源追溯, CSS／JS／JSON 全內嵌的離線互動頁, UI／程式元件、整合視圖、failure framework 與完整 Universal IR |

### 表格 `L69` Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / 五個整合動作（5 rows）

| 欄位 | 型別(推論) | 單位 | 樣本 |
|---|---|---|---|
| Action | string |  | `text_merge`, `code_merge`, `restructure` |
| 行為 | string |  | 依 taxonomy 建立文字主題整合索引, 依 language／symbol 建立跨語言元件索引, 建立可讀的分類視圖 |
| 不變量 | string |  | 原 Topic 不刪, API 簽章不改, 原順序與行號保留 |

### Schema / 欄位定義

- `$ {engine: object, resources: object, routing: object, cache: object, jobs: object, knowledge: object, ml: object, deep: object, translation: object, security: object}` (V) — nlp_default.json:$
- `$.engine {name: string, profile: string, offline: boolean, language: string, max_text_chars: integer, max_batch_items: integer, max_concurrency: integer, request_timeout_seconds: integer, data_dir: string, lexicon_path: string, governance_path: string}` (V) — nlp_default.json:$.engine
- `$.resources {poll_interval_seconds: number, warning_ram_percent: number, shed_ram_percent: number, critical_ram_percent: number, warning_cpu_percent: number, critical_cpu_percent: number, min_available_ram_mb: integer, model_idle_ttl_seconds: integer, model_pool_max_items: integer, model_pool_max_estimated_mb: integer, adaptive_batch_min: integer, adaptive_batch_max: integer, gc_after_request: boolean}` (V) — nlp_default.json:$.resources
- `$.routing {allow_tiers: array, default_tier: integer, fallback_on_pressure: boolean, allow_deep_models: boolean, allow_llm: boolean, deep_min_available_ram_mb: integer, llm_min_available_ram_mb: integer}` (V) — nlp_default.json:$.routing
- `$.cache {enabled: boolean, max_entries: integer, ttl_seconds: integer, max_value_bytes: integer}` (V) — nlp_default.json:$.cache
- `$.jobs {enabled: boolean, worker_count: integer, poll_seconds: number, stale_seconds: integer, max_retries: integer, max_pending_jobs: integer}` (V) — nlp_default.json:$.jobs
- `$.knowledge {max_segment_chars: integer, topic_threshold: number, topic_merge_threshold: number, max_topics: integer, max_features_per_segment: integer, max_topic_keywords: integer, anchor_boost: number, anchor_conflict_penalty: number, max_ai_graph_edges: integer, deep_similarity_threshold: number, extract_structured_tables: boolean, max_table_columns: integer, max_structured_tables: integer, max_knowledge_units: integer, max_knowledge_conflicts: integer, max_code_families: integer, threshold_calibration: object}` (V) — nlp_default.json:$.knowledge
- `$.knowledge.threshold_calibration {enabled: boolean, topic_threshold_grid: array, topic_merge_threshold_grid: array, auto_apply: boolean}` (V) — nlp_default.json:$.knowledge.threshold_calibration
- `$.ml {enabled: boolean, classes: array, n_features: integer, random_state: integer, candidate_min_samples: integer, validation_fraction: number, min_macro_f1: number, max_regression: number, auto_promote: boolean, auto_evolve_every_feedback: integer, linear_epochs: integer, training_batch_size: integer, neural_challenger_enabled: boolean, neural_min_samples: integer, neural_n_features: integer, neural_hidden_layers: array, neural_max_iter: integer, evolution_estimated_ram_mb: integer, max_duplicate_ratio: number, candidate_retention: integer}` (V) — nlp_default.json:$.ml
- `$.deep {embedding_backend: string, embedding_model: string, embedding_device: string, local_files_only: boolean, ollama_url: string, ollama_model: string, ollama_keep_alive: string, ollama_timeout_seconds: integer}` (V) — nlp_default.json:$.deep
- `$.translation {enabled: boolean, default_backend: string, source_language: string, target_language: string, max_chunk_chars: integer, preserve_code: boolean, google_cloud_location: string, google_cloud_project_env: string}` (V) — nlp_default.json:$.translation
- `$.security {bind_host: string, bind_port: integer, api_key_env: string, require_api_key: boolean, allow_remote_bind: boolean, rate_limit_per_minute: integer, trusted_proxy_headers: boolean, redact_sensitive_logs: boolean, audit_hash_chain: boolean}` (V) — nlp_default.json:$.security
- `entities: 日期` (M) — nlp_readme.md:L176

## 6. 業務規則

### MUST_NOT（18）

- **SPEC-RULE-MUST_NOT-EA5DFAFA4316** AI candidates never auto-apply / 來源唯讀；  ⟨Veritas_VOFIE_Reconstructed.docx:L7⟩
- **SPEC-RULE-MUST_NOT-4EDD2E3A5846** AI 候選不可直接套用  ⟨Veritas_VOFIE_Reconstructed.docx:L7⟩
- **SPEC-RULE-MUST_NOT-CD144B098175** 原檔不可改寫，重複內容只標記，不可刪除。  ⟨Veritas_VOFIE_Reconstructed.docx:L61 · 來源：sample.md / 文字內容 / 文字內容⟩
- **SPEC-RULE-MUST_NOT-B8916BCF52D7** Mind Map 新增 context thread、function、standard template 與 layout type 節點，仍透過 append-only snapshot delta 動態修正，禁止靜默刪除或 canonical mutation。  ⟨nlp_readme.md:L13 · VIA NLP One Engine / v1.5 文字、脈絡、程式與標準模板還原⟩
- **SPEC-RULE-MUST_NOT-2C4342447BFE** `VIA_INSTRUCTION_RECONSTRUCTION/1.0`：把零散的中英文需求、決策、禁止事項、前置條件、行動與驗證步驟重建為有來源順序的程序。  ⟨nlp_readme.md:L18 · VIA NLP One Engine / v1.4 指令還原、雙語知識體與動態 Mind Map⟩
- **SPEC-RULE-MUST_NOT-A08DFE825D51** 禁止靜默刪除或改寫 canonical。  ⟨nlp_readme.md:L23 · VIA NLP One Engine / v1.4 指令還原、雙語知識體與動態 Mind Map⟩
- **SPEC-RULE-MUST_NOT-DDE106F2C57A** 未標語言的 code fence 會附信心分數，低信心不得當成確定語言。  ⟨nlp_readme.md:L32 · VIA NLP One Engine / v1.3 討論知識與程式重建基線⟩
- **SPEC-RULE-MUST_NOT-969F8D6209C5** Zero-Hydra：不可信對話中的程式碼只解析，不執行；  ⟨nlp_readme.md:L270 · VIA NLP One Engine / VIA Central Governance Console 對齊⟩
- **SPEC-RULE-MUST_NOT-E74F532410F5** 神經網路未收斂時只列報告，不可勝出；  ⟨nlp_readme.md:L307 · VIA NLP One Engine / 受治理的持續學習⟩
- **SPEC-RULE-MUST_NOT-77954EE9AE23** 不應把 FP16／FP32 大模型與多個 NLP 模型同時常駐一般電腦。  ⟨nlp_readme.md:L333 · VIA NLP One Engine / 深度模型啟用⟩
- **SPEC-RULE-MUST_NOT-376534C015C4** 這種自動化容易受驗證碼、DOM 改版與使用限制影響，不能作為穩定引擎依賴。  ⟨nlp_readme.md:L376 · VIA NLP One Engine / 中↔英分段翻譯 / Google Cloud Translation⟩
- **SPEC-RULE-MUST_NOT-7252B2B8831C** 引擎只能控制載入與降級，不能保證任何硬體都能跑所有模型。  ⟨nlp_readme.md:L403 · VIA NLP One Engine / 重要限制⟩
- **SPEC-RULE-MUST_NOT-E98EA8F0DE5D** 前後以 `byte_size + BLAKE2s` 驗證，禁止刪除、移動、覆寫 canonical。  ⟨vofie_readme.md:L11 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / 不變承諾⟩
- **SPEC-RULE-MUST_NOT-D90757942851** 沒有等價測試不得直接套用。  ⟨vofie_readme.md:L16 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / 不變承諾⟩
- **SPEC-RULE-MUST_NOT-77654F894D30** 每項都有 cause、detectors、breakers、至少三個 solutions、SOP、never-again control 與 repair lane。  ⟨vofie_readme.md:L90 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / 九頭龍風險避免 Top 20⟩
- **SPEC-RULE-MUST_NOT-422684D1119A** Canonical／SSOT 不可直接寫入。  ⟨vofie_readme.md:L108 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / v1.4 Runtime Copy 與 rollback⟩
- **SPEC-RULE-MUST_NOT-E3E7308363E3** 舊工具只設 `enabled: false`，不可刪除。  ⟨vofie_readme.md:L186 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / 未來新增工具的唯一入口⟩
- **SPEC-RULE-MUST_NOT-AC46B6FB6C69** 不得覆寫 `ST-FROZEN`、Universal IR、source hash gate、五檔契約與來源唯讀政策。  ⟨vofie_readme.md:L189 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / 未來新增工具的唯一入口⟩

### MUST（25）

- **SPEC-RULE-MUST-A349BC43DA05** document_output（1）— VOFIE 範例需求  ⟨Veritas_VOFIE_Reconstructed.docx:L37 · 合併／重組／去重／優化視圖⟩
- **SPEC-RULE-MUST-435F8A719B0E** 本文應依主題重構，轉為 Markdown、Word、PowerPoint、Excel、CSV，以及 HTML／CSS／JavaScript 模板。  ⟨Veritas_VOFIE_Reconstructed.docx:L53 · 來源：sample.md / VOFIE 範例需求 / VOFIE 範例需求⟩
- **SPEC-RULE-MUST-B0F0C28135D5** 需要一個搜尋欄位、分類下拉選單、結果表格與匯出 CSV 按鈕。  ⟨Veritas_VOFIE_Reconstructed.docx:L105 · 來源：sample.md / HTML 規格 / HTML 規格⟩
- **SPEC-RULE-MUST-4185FBF011E7** 所有互動應支援鍵盤與可見焦點。  ⟨Veritas_VOFIE_Reconstructed.docx:L105 · 來源：sample.md / HTML 規格 / HTML 規格⟩
- **SPEC-RULE-MUST-83BCF80B7B15** 預設只啟動低資源規則與機器學習元件，較重的 spaCy、Embedding 與 Ollama 只在路由需要、設定允許且資源閘門通過時載入。  ⟨nlp_readme.md:L3 · VIA NLP One Engine⟩
- **SPEC-RULE-MUST-EBECF9B338A1** `VIA_KNOWLEDGE_OBJECT_REGISTRY/1.0`：大量討論中的決策、需求、問題、風險、行動與參數具有穩定 Knowledge ID、全部來源 occurrence 與 Topic 關聯。  ⟨nlp_readme.md:L28 · VIA NLP One Engine / v1.3 討論知識與程式重建基線⟩
- **SPEC-RULE-MUST-73CD099769A8** 加速：HashingVectorizer、增量 `partial_fit`、SQLite WAL 快取、自適應批次、斷點續跑。  ⟨nlp_readme.md:L56 · VIA NLP One Engine / 已完成能力⟩
- **SPEC-RULE-MUST-8DF4618F93D5** PDF 需安裝 `documents` extra。  ⟨nlp_readme.md:L100 · VIA NLP One Engine / 最快開始⟩
- **SPEC-RULE-MUST-762BD71C7B9B** 使用 Microsoft MarkItDown 本機轉換（需要先安裝 `.[markitdown]`）：  ⟨nlp_readme.md:L102 · VIA NLP One Engine / 最快開始⟩
- **SPEC-RULE-MUST-E657D4A03F11** 對掃描圖片的 OCR 品質仍需人工抽查。  ⟨nlp_readme.md:L111 · VIA NLP One Engine / 最快開始⟩
- **SPEC-RULE-MUST-45A348BD9A4C** 高風險變更必須人工授權。  ⟨nlp_readme.md:L270 · VIA NLP One Engine / VIA Central Governance Console 對齊⟩
- **SPEC-RULE-MUST-EA6499E3A084** 若要網路存取，必須明確開啟 `security.allow_remote_bind`、啟用 API key，並在反向代理層加 TLS、來源限制與請求大小限制。  ⟨nlp_readme.md:L299 · VIA NLP One Engine / FastAPI⟩
- **SPEC-RULE-MUST-62E4FDA10655** 候選還必須通過 Macro-F1、balanced accuracy、相對退化與檔案雜湊。  ⟨nlp_readme.md:L307 · VIA NLP One Engine / 受治理的持續學習⟩
- **SPEC-RULE-MUST-885370DBAC59** 先安裝 `translate` extra，並由使用者明確安裝所需的 `.argosmodel` 語言包；  ⟨nlp_readme.md:L339 · VIA NLP One Engine / 中↔英分段翻譯 / 建議 1：Argos Translate 離線⟩
- **SPEC-RULE-MUST-2A228A8ADD14** 需同時啟用 `routing.allow_deep_models=true` 與 `routing.allow_llm=true`，並安裝可處理繁體中文的本地模型。  ⟨nlp_readme.md:L363 · VIA NLP One Engine / 中↔英分段翻譯 / 建議 2：本機 Ollama⟩
- **SPEC-RULE-MUST-90ED1BF0B62C** Cloud Translation 是正式可程式化的 Google 翻譯路徑，需要啟用 billing、API 與 authentication。  ⟨nlp_readme.md:L367 · VIA NLP One Engine / 中↔英分段翻譯 / Google Cloud Translation⟩
- **SPEC-RULE-MUST-7159EB72E024** 引擎預設離線，因此每次使用還必須明確傳入 `--allow-network`。  ⟨nlp_readme.md:L367 · VIA NLP One Engine / 中↔英分段翻譯 / Google Cloud Translation⟩
- **SPEC-RULE-MUST-0502E05ADE35** PDF 若沒有文字層需先經 OCR；  ⟨nlp_readme.md:L404 · VIA NLP One Engine / 重要限制⟩
- **SPEC-RULE-MUST-595617569857** FN-10185 Required typing.py:3017 parameters R02 R03  ⟨ves.html:L56⟩
- **SPEC-RULE-MUST-A0784AE59105** R02_DECORATOR_HIDES_SIGNATURE 裝飾器隱藏真實簽名 擷取 decorator_list 建對應表；  ⟨ves.html:L2073⟩
- **SPEC-RULE-MUST-749249F3809A** 把它搬進 的對應能力軸，下次執行即生效，OTHER 會自動縮小。  ⟨ves.html:L2093⟩
- **SPEC-RULE-MUST-FCD54A98AE28** 下一步：① adapters 已自動生成 Payload 型別模型＋群內參數同義映射(PARAM_ALIAS)，只剩「未註記型別 = Any」需要補 ② tests 填代表性 payload → ③ 用 影子跑一週再切換。  ⟨ves.html:L2101⟩
- **SPEC-RULE-MUST-A27C978C412A** Activation 必須同時通過 Hydra、self-test、user-test、recovery 與 rollback-ready 契約。  ⟨vofie_readme.md:L96 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / 九頭龍風險避免 Top 20⟩
- **SPEC-RULE-MUST-9814E94BEDA5** `rollback-check` 只驗證復原所需 hash 與 manifest，不執行真實 rollback，也不提升 Runtime Copy 為 canonical。  ⟨vofie_readme.md:L123 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / v1.4 Runtime Copy 與 rollback⟩
- **SPEC-RULE-MUST-440693E8EBC9** 需求式調用：  ⟨vofie_readme.md:L140 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / JavaScript／PowerShell Top 20 CPU 工具⟩

### SHOULD（8）

- **SPEC-RULE-SHOULD-B3B343E6FD7A** CPU 主機建議先使用較小的 Embedding 模型；  ⟨nlp_readme.md:L332 · VIA NLP One Engine / 深度模型啟用⟩
- **SPEC-RULE-SHOULD-EB98FF5A73DF** 官方建議單次約 5,000 code points；  ⟨nlp_readme.md:L367 · VIA NLP One Engine / 中↔英分段翻譯 / Google Cloud Translation⟩
- **SPEC-RULE-SHOULD-D1852DF2631C** · 成員 141 · 工具集=0 檔案=71 相似=1.0 N001 TRANSFORM 超大群：連鎖傳遞造成，建議 --threshold 調高至 0.8 提  ⟨ves.html:L224⟩
- **SPEC-RULE-SHOULD-7F71586DAEEC** · 成員 141 · 工具集=0 檔案=71 相似=1.0 N002 PARSE 超大群：連鎖傳遞造成，建議 --threshold 調高至 0.8 提案介面  ⟨ves.html:L224⟩
- **SPEC-RULE-SHOULD-0881CE8D4E63** FN-11088 register webbrowser.py:23 name, klass, instance, preferred  ⟨ves.html:L224⟩
- **SPEC-RULE-SHOULD-92249F33CD70** · ML 首選 scikit-learn · DL 首選 onnxruntime · 本機 LLM 建議 qwen2.5:1.5b 等級：T4 僅輕量 sklearn  ⟨ves.html:L2081⟩
- **SPEC-RULE-SHOULD-E6205B0F7E11** qwen2.5:3b 建議）；  ⟨ves.html:L2094⟩
- **SPEC-RULE-SHOULD-0660FBD6835C** LLM 建議標 M 級，人工搬進 verbs 才升 V。  ⟨ves.html:L2094⟩

### CONDITION（2）

- **SPEC-RULE-CONDITIO-D0DD492A66F8** 任意內容只有詞庫或來源明示配對時才自動投影，否則保留來源並標記待翻譯。  ⟨nlp_readme.md:L223 · VIA NLP One Engine / 跳題對話 → Body of Knowledge / 指令與動態修正的安全邊界⟩
- **SPEC-RULE-CONDITIO-B9264C7921EA** 只有明確允許且全部品質閘門通過時才替換 active model。  ⟨nlp_readme.md:L308 · VIA NLP One Engine / 受治理的持續學習⟩

### THRESHOLD（9）

- **SPEC-RULE-THRESHOL-9275B246CC90** 每 50 筆回饋可自動觸發 candidate evaluation；  ⟨nlp_readme.md:L304 · VIA NLP One Engine / 受治理的持續學習⟩
- **SPEC-RULE-THRESHOL-DBA6970F4523** 同一列裡出現 ≥2 個工具欄位 = 「功能相同、工具相異」的整併候選帶。  ⟨ves.html:L53⟩
- **SPEC-RULE-THRESHOL-AEBFE8D3B33F** Python 3.12.3 · x86_64 · 1 核 · RAM 3.9 GB · avx,avx2,avx512f,fma,sse4_2  ⟨ves.html:L2081⟩
- **SPEC-RULE-THRESHOL-AE7D2AC64BC7** 3,391,554 245 100.0%  ⟨ves.html:L2089⟩
- **SPEC-RULE-THRESHOL-375A10BBAE60** 函式共 12327 筆，表格只嵌前 5000 筆；  ⟨ves.html:L2091⟩
- **SPEC-RULE-THRESHOL-9F1A4479322F** 命中 ≥3 已自動寫入 (P 級)。  ⟨ves.html:L2093⟩
- **SPEC-RULE-THRESHOL-B0C7A0A1B55E** 視窗可用「選取檔案」或拖放輸入，最多 5 檔。  ⟨vofie_readme.md:L32 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / 最簡單的使用方式⟩
- **SPEC-RULE-THRESHOL-C91A4332FD31** 每項繼承該環節至少 5 個已實作 recovery handlers；  ⟨vofie_readme.md:L79 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / Top 20 Failures × 8 環節⟩
- **SPEC-RULE-THRESHOL-9A8488A34BB0** parallel fixer 最多 2、global concurrency cap 4。  ⟨vofie_readme.md:L93 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / 九頭龍風險避免 Top 20⟩

### FORMULA（1）

- **SPEC-RULE-FORMULA-DEEEF44CE1DE** 本輪寫入：runs → /tmp/vs6/ves_store/runs/date=20260906/run_1.parquet functions → /tmp/vs6/ves_store/functions/date=20260906/run_1.parquet risks → /tmp/vs6/ves_store/risks/date=20260906/run_1.parquet gates → /tmp/vs6/ves_store/gates/date=20260906/run_1.parquet bench → /tmp/vs6/ves_store/bench/date=20260906/run_1.parquet pyarrow  ⟨ves.html:L2085⟩

### TRANSITION（44）

- **SPEC-RULE-TRANSITI-CB73D492C3FA** Microsoft MarkItDown 是可選本機入口：可將官方支援的 Office、PDF、HTML、CSV／JSON／XML、EPUB、圖片與音訊轉為 Markdown 分析投影。  ⟨nlp_readme.md:L8 · VIA NLP One Engine / v1.5 文字、脈絡、程式與標準模板還原⟩
- **SPEC-RULE-TRANSITI-D5269208BF60** `VIA_CONTEXT_RECONSTRUCTION/1.0`：區分 article／dialogue／mixed／code-heavy，為每段加上中英文功能標籤，保留 chronology，重建 topic threads、跳題復返與待審查 question→answer links；  ⟨nlp_readme.md:L9 · VIA NLP One Engine / v1.5 文字、脈絡、程式與標準模板還原⟩
- **SPEC-RULE-TRANSITI-849E8318DD2E** `VIA_ENGINE_BLUEPRINT/3.0`：只有每個 family 的候選版進入建構拓撲；  ⟨nlp_readme.md:L33 · VIA NLP One Engine / v1.3 討論知識與程式重建基線⟩
- **SPEC-RULE-TRANSITI-48D8143E64FE** 不完整命令降低信心並進入 review queue。  ⟨nlp_readme.md:L220 · VIA NLP One Engine / 跳題對話 → Body of Knowledge / 指令與動態修正的安全邊界⟩
- **SPEC-RULE-TRANSITI-996DCAECA027** `config/governance.json` 已將 Mega-Prompt 轉為機器可讀治理契約：  ⟨nlp_readme.md:L264 · VIA NLP One Engine / VIA Central Governance Console 對齊⟩
- **SPEC-RULE-TRANSITI-9D5E616491F6** R01_DYNAMIC_IMPORT 動態載入遺漏 AST 看不到 importlib/eval 匯入 → 改 sys.settrace 執行期追蹤或 regex 補掃  ⟨ves.html:L2073⟩
- **SPEC-RULE-TRANSITI-5CEDD91C46DC** 歷史輪數 0 · STABLE_P（≥3 輪只出現 :P 從未 :M → 疑似誤報降權）0 項 · 本輪降權 0  ⟨ves.html:L2087⟩
- **SPEC-RULE-TRANSITI-61946B146924** 整棵原始碼 ≈ tokens → 交接檔 ≈ tokens，省 。  ⟨ves.html:L2089⟩
- **SPEC-RULE-TRANSITI-8CA3EF45E7E8** getregentry → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-61C342982F11** create → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-F37BA981EC1D** remove → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-213FF79AD549** handle → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-FB286CFD28A1** readline → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-79A729A62BC4** replace → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-6C1E9772F0CE** writable → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-A40121A488DE** fileno → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-0076B828EB35** shutdown → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-81FBCCDA029F** readable → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-6DED13A7B1F1** seekable → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-02779AF22870** append → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-11DB46E5330D** readinto → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-2C5FF39D9C3B** update → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-CC9EAB9F25B8** prepare → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-3085F10298F3** closed → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-36D16AE572F7** writelines → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-B1D22FF795AA** connect → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-26821224B462** accept → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-7C8E372B5609** getstate → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-41F819DBE8EE** setstate → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-308476425CA7** connection → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-B6CB7DFB8D02** cancel → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-56081C994574** version → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-75F0B0213BD6** resolve → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-B53C1EACA85A** compare → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-E8C77897EF47** truncate → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-8793CD4914A9** release → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-8E2CDB8D3D8B** domain → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-56CD10F83C69** server → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-AFC27C897E83** readlines → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-6CDB73CA0589** detach → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-BFF83DF7C34F** resume → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-94E389F530D9** joinpath → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-5D28EA2B02CA** values → pending_verbs (待填能力軸)  ⟨ves.html:L2095⟩
- **SPEC-RULE-TRANSITI-EB3CFC3A28AE** payload → ③  ⟨ves.html:L2101⟩

### ACCEPTANCE（7）

- **SPEC-RULE-ACCEPTAN-AA496BE0605A** FN-09771 setraw tty.py:59 fd, when  ⟨ves.html:L56⟩
- **SPEC-RULE-ACCEPTAN-F35425307FE1** FN-09772 setcbreak tty.py:67 fd, when  ⟨ves.html:L56⟩
- **SPEC-RULE-ACCEPTAN-89F282BEBED4** FN-01386 TimerHandle.when asyncio/events.py:160 模糊命中 0 STRONG  ⟨ves.html:L2077⟩
- **SPEC-RULE-ACCEPTAN-537CFB63683D** FN-01938 Timeout.when asyncio/timeouts.py:46 模糊命中 0 STRONG  ⟨ves.html:L2077⟩
- **SPEC-RULE-ACCEPTAN-A4A552EA0A67** FN-01386 TimerHandle.when asyncio/events.py:160 eb562e998389  ⟨ves.html:L2091⟩
- **SPEC-RULE-ACCEPTAN-8BA285DE55F0** FN-01938 Timeout.when asyncio/timeouts.py:46 eb562e998389  ⟨ves.html:L2091⟩
- **SPEC-RULE-ACCEPTAN-8902172ACD20** FN-04486 _not_given.__repr__ enum.py:170 b58987bea98d  ⟨ves.html:L2091⟩

### PERMISSION（9）

- **SPEC-RULE-PERMISSI-DFE43770AC21** 完善稿包含高信心修復、角色、語意單元、改動與雜湊，不覆蓋原文。  ⟨nlp_readme.md:L50 · VIA NLP One Engine / 已完成能力⟩
- **SPEC-RULE-PERMISSI-15E9B1D5016D** Playwright／Puppeteer 只定位為已授權的測試與動態頁面渲染工具，不提供 CAPTCHA、登入、驗證或網站限制繞過。  ⟨nlp_readme.md:L138 · VIA NLP One Engine / 最快開始⟩
- **SPEC-RULE-PERMISSI-A4AFF4588BEF** `refinement_ledger`：每段完善稿、角色、語意單元、修改紀錄、來源及衍生雜湊。  ⟨nlp_readme.md:L194 · VIA NLP One Engine / 跳題對話 → Body of Knowledge⟩
- **SPEC-RULE-PERMISSI-6580BEDB8418** `knowledge_object_registry`：穩定知識 ID、角色 registers、重複 occurrence、參數衝突、取代審查與 Evidence Matrix。  ⟨nlp_readme.md:L204 · VIA NLP One Engine / 跳題對話 → Body of Knowledge⟩
- **SPEC-RULE-PERMISSI-F59A9068F00F** ENGINE 角色只產生上述 5 檔；  ⟨vofie_readme.md:L46 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / 固定五個主要輸出⟩
- **SPEC-RULE-PERMISSI-FFE72974584F** SYSTEM 角色仍只顯示這 5 個主要檔，但另在 `_system/` 保存 10 個治理 sidecars，包含 NoHydra audit／HTML matrix、Runtime Copy safety、工具與測試證據。  ⟨vofie_readme.md:L46 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / 固定五個主要輸出⟩
- **SPEC-RULE-PERMISSI-ADA2381C316D** SYSTEM 角色：  ⟨vofie_readme.md:L56 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / 固定五個主要輸出⟩
- **SPEC-RULE-PERMISSI-2F75FC869ED7** 真實寫入只允許在新建的版本化 run-local Runtime Copy，並要求精確核准 token；  ⟨vofie_readme.md:L108 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / v1.4 Runtime Copy 與 rollback⟩
- **SPEC-RULE-PERMISSI-BD69AB780385** `--execute-safe` 只允許唯讀 syntax quick check；  ⟨vofie_readme.md:L156 · Veritas OmniFormat Intelligence Engine（VOFIE）v1.4 / JavaScript／PowerShell Top 20 CPU 工具⟩

## 7. 內容模型

- 標題 68 · 段落 93 · 清單/任務/步驟 152 · 程式碼區塊 31 · 連結 0 · 圖片 0

- 來源登記  ⟨Veritas_VOFIE_Reconstructed.docx:L17⟩
- 合併／重組／去重／優化視圖  ⟨Veritas_VOFIE_Reconstructed.docx:L21⟩
- 主題重構內容  ⟨Veritas_VOFIE_Reconstructed.docx:L43⟩
- 來源：sample.md  ⟨Veritas_VOFIE_Reconstructed.docx:L45⟩
  - VOFIE 範例需求  ⟨Veritas_VOFIE_Reconstructed.docx:L47⟩
  - 文字內容  ⟨Veritas_VOFIE_Reconstructed.docx:L55⟩
  - Python 元件  ⟨Veritas_VOFIE_Reconstructed.docx:L63⟩
    - 程式元件  ⟨Veritas_VOFIE_Reconstructed.docx:L67⟩
  - JavaScript 元件  ⟨Veritas_VOFIE_Reconstructed.docx:L81⟩
  - HTML 規格  ⟨Veritas_VOFIE_Reconstructed.docx:L99⟩
- 品質 Gate  ⟨Veritas_VOFIE_Reconstructed.docx:L107⟩
- VIA NLP One Engine  ⟨nlp_readme.md:L1⟩
  - v1.5 文字、脈絡、程式與標準模板還原  ⟨nlp_readme.md:L5⟩
  - v1.4 指令還原、雙語知識體與動態 Mind Map  ⟨nlp_readme.md:L16⟩
  - v1.3 討論知識與程式重建基線  ⟨nlp_readme.md:L26⟩
  - v1.2 NLP-only 強化  ⟨nlp_readme.md:L36⟩
  - 已完成能力  ⟨nlp_readme.md:L44⟩
  - 四級路由  ⟨nlp_readme.md:L62⟩
  - 最快開始  ⟨nlp_readme.md:L73⟩
  - Windows 一鍵安裝  ⟨nlp_readme.md:L140⟩
  - Python API  ⟨nlp_readme.md:L149⟩
    - 主要任務  ⟨nlp_readme.md:L165⟩
  - 跳題對話 → Body of Knowledge  ⟨nlp_readme.md:L183⟩
    - 指令與動態修正的安全邊界  ⟨nlp_readme.md:L217⟩
    - CPU 知識重組參數  ⟨nlp_readme.md:L225⟩
  - VIA Central Governance Console 對齊  ⟨nlp_readme.md:L262⟩
  - FastAPI  ⟨nlp_readme.md:L281⟩
  - 受治理的持續學習  ⟨nlp_readme.md:L301⟩
  - 深度模型啟用  ⟨nlp_readme.md:L312⟩
  - 中↔英分段翻譯  ⟨nlp_readme.md:L335⟩
    - 建議 1：Argos Translate 離線  ⟨nlp_readme.md:L337⟩
    - 建議 2：本機 Ollama  ⟨nlp_readme.md:L361⟩
    - Google Cloud Translation  ⟨nlp_readme.md:L365⟩
  - 設定覆寫  ⟨nlp_readme.md:L378⟩
  - 測試  ⟨nlp_readme.md:L391⟩
  - 重要限制  ⟨nlp_readme.md:L399⟩
  - 參考設計依據  ⟨nlp_readme.md:L406⟩
- VIA Engine Standardizer v0600  ⟨ves.html:L33⟩
  - 能力軸 × 工具家族 熱度矩陣  ⟨ves.html:L53⟩
  - 工具家族註冊  ⟨ves.html:L54⟩
  - 功能相同 · 工具相異（標準化整併主目標）  ⟨ves.html:L55⟩
  - 正規化 AST 結構完全相同（變數名/docstring/行號已抹除）  ⟨ves.html:L56⟩
  - 近似重複（同工具、名稱/參數高度相似）  ⟨ves.html:L224⟩
  - 25 項風險稽核 · 命中統計  ⟨ves.html:L2073⟩
  - DORMANT 候選（公開函式、fan_in=0、非入口/非裝飾器路由）  ⟨ves.html:L2076⟩
  - 跳過的檔案  ⟨ves.html:L2079⟩
  - CPU 跑得動的 ML / DL 工具（自動偵測 + 微基準）  ⟨ves.html:L2080⟩
  - 微基準  ⟨ves.html:L2083⟩
  - 專案自有儲存（ves_store · Parquet 分區 · append-only）  ⟨ves.html:L2084⟩
  - 持續強化（自學，純統計可審計）  ⟨ves.html:L2087⟩
  - 先機器修復 → 再交 AI（AI_HANDOFF.md）  ⟨ves.html:L2089⟩
  - 分類法（外掛 ves_taxonomy.json · 只增不減）  ⟨ves.html:L2092⟩
  - 動態匯入目標（R01 regex 補掃，AST 看不到的）  ⟨ves.html:L2096⟩
  - 已生成（全新目錄，原檔未動；重跑時既有 adapter 保留、新版本寫 _vN，scaffold_ledger.jsonl 追加）  ⟨ves.html:L2098⟩
- Veritas OmniFormat Intelligence Engine（VOFIE）v1.4  ⟨vofie_readme.md:L1⟩
  - 不變承諾  ⟨vofie_readme.md:L9⟩
  - 最簡單的使用方式  ⟨vofie_readme.md:L18⟩
  - 固定五個主要輸出  ⟨vofie_readme.md:L34⟩
  - 五個整合動作  ⟨vofie_readme.md:L65⟩
  - Top 20 Failures × 8 環節  ⟨vofie_readme.md:L77⟩
  - 九頭龍風險避免 Top 20  ⟨vofie_readme.md:L88⟩
  - v1.4 Runtime Copy 與 rollback  ⟨vofie_readme.md:L106⟩
  - JavaScript／PowerShell Top 20 CPU 工具  ⟨vofie_readme.md:L125⟩
  - 測試、除錯與啟用  ⟨vofie_readme.md:L158⟩
  - 完整模式仍保留  ⟨vofie_readme.md:L170⟩
  - 未來新增工具的唯一入口  ⟨vofie_readme.md:L181⟩
  - 專案結構  ⟨vofie_readme.md:L191⟩
- VIA SuperHtml Parser · 解讀台  ⟨vshp_ui.html:L119⟩

## 8. 缺口（Gap）

| ID | 類型 | 說明 | 等級 | 來源 |
|---|---|---|---|---|
| SPEC-GAP-RULE_NO_-B8B0ADA80FA8 | rule_no_condition | 規則缺觸發條件/門檻: AI candidates never auto-apply / 來源唯讀； | M | Veritas_VOFIE_Reconstructed.docx:L7 |
| SPEC-GAP-RULE_NO_-1D98C3549C34 | rule_no_condition | 規則缺觸發條件/門檻: AI 候選不可直接套用 | M | Veritas_VOFIE_Reconstructed.docx:L7 |
| SPEC-GAP-RULE_NO_-63B7FB1C7770 | rule_no_condition | 規則缺觸發條件/門檻: document_output（1）— VOFIE 範例需求 | M | Veritas_VOFIE_Reconstructed.docx:L37 |
| SPEC-GAP-RULE_NO_-8EE172FDFB5E | rule_no_condition | 規則缺觸發條件/門檻: 本文應依主題重構，轉為 Markdown、Word、PowerPoint、Excel、CSV，以及 HTML／CSS／JavaScript 模板。 | M | Veritas_VOFIE_Reconstructed.docx:L53 |
| SPEC-GAP-RULE_NO_-74CC00081D33 | rule_no_condition | 規則缺觸發條件/門檻: 原檔不可改寫，重複內容只標記，不可刪除。 | M | Veritas_VOFIE_Reconstructed.docx:L61 |
| SPEC-GAP-RULE_NO_-33486F499A19 | rule_no_condition | 規則缺觸發條件/門檻: 需要一個搜尋欄位、分類下拉選單、結果表格與匯出 CSV 按鈕。 | M | Veritas_VOFIE_Reconstructed.docx:L105 |
| SPEC-GAP-RULE_NO_-F8FB6B489C97 | rule_no_condition | 規則缺觸發條件/門檻: 所有互動應支援鍵盤與可見焦點。 | M | Veritas_VOFIE_Reconstructed.docx:L105 |
| SPEC-GAP-RULE_NO_-BF4C6A00A306 | rule_no_condition | 規則缺觸發條件/門檻: 預設只啟動低資源規則與機器學習元件，較重的 spaCy、Embedding 與 Ollama 只在路由需要、設定允許且資源閘門通過時載入。 | M | nlp_readme.md:L3 |
| SPEC-GAP-RULE_NO_-958DDDE4762D | rule_no_condition | 規則缺觸發條件/門檻: Mind Map 新增 context thread、function、standard template 與 layout type 節點，仍透過 appen | M | nlp_readme.md:L13 |
| SPEC-GAP-RULE_NO_-1198A2EFD0DD | rule_no_condition | 規則缺觸發條件/門檻: `VIA_INSTRUCTION_RECONSTRUCTION/1.0`：把零散的中英文需求、決策、禁止事項、前置條件、行動與驗證步驟重建為有來源順序的程序。 | M | nlp_readme.md:L18 |
| SPEC-GAP-RULE_NO_-868E3154D78A | rule_no_condition | 規則缺觸發條件/門檻: 禁止靜默刪除或改寫 canonical。 | M | nlp_readme.md:L23 |
| SPEC-GAP-RULE_NO_-A5B30A80AC40 | rule_no_condition | 規則缺觸發條件/門檻: `VIA_KNOWLEDGE_OBJECT_REGISTRY/1.0`：大量討論中的決策、需求、問題、風險、行動與參數具有穩定 Knowledge ID、全部來 | M | nlp_readme.md:L28 |
| SPEC-GAP-RULE_NO_-C9AB7416FC52 | rule_no_condition | 規則缺觸發條件/門檻: 未標語言的 code fence 會附信心分數，低信心不得當成確定語言。 | M | nlp_readme.md:L32 |
| SPEC-GAP-RULE_NO_-3FA2C3E5AE0D | rule_no_condition | 規則缺觸發條件/門檻: 加速：HashingVectorizer、增量 `partial_fit`、SQLite WAL 快取、自適應批次、斷點續跑。 | M | nlp_readme.md:L56 |
| SPEC-GAP-RULE_NO_-9202D1ED4561 | rule_no_condition | 規則缺觸發條件/門檻: PDF 需安裝 `documents` extra。 | M | nlp_readme.md:L100 |
| SPEC-GAP-RULE_NO_-1B4AA685306E | rule_no_condition | 規則缺觸發條件/門檻: 使用 Microsoft MarkItDown 本機轉換（需要先安裝 `.[markitdown]`）： | M | nlp_readme.md:L102 |
| SPEC-GAP-RULE_NO_-CE968804BDC0 | rule_no_condition | 規則缺觸發條件/門檻: 對掃描圖片的 OCR 品質仍需人工抽查。 | M | nlp_readme.md:L111 |
| SPEC-GAP-RULE_NO_-48F6C70262BD | rule_no_condition | 規則缺觸發條件/門檻: Zero-Hydra：不可信對話中的程式碼只解析，不執行； | M | nlp_readme.md:L270 |
| SPEC-GAP-RULE_NO_-383543D04474 | rule_no_condition | 規則缺觸發條件/門檻: 高風險變更必須人工授權。 | M | nlp_readme.md:L270 |
| SPEC-GAP-RULE_NO_-E2EB1A144FCC | rule_no_condition | 規則缺觸發條件/門檻: 若要網路存取，必須明確開啟 `security.allow_remote_bind`、啟用 API key，並在反向代理層加 TLS、來源限制與請求大小限制。 | M | nlp_readme.md:L299 |
| SPEC-GAP-RULE_NO_-2FE18DAFD437 | rule_no_condition | 規則缺觸發條件/門檻: 神經網路未收斂時只列報告，不可勝出； | M | nlp_readme.md:L307 |
| SPEC-GAP-RULE_NO_-093688811F15 | rule_no_condition | 規則缺觸發條件/門檻: 候選還必須通過 Macro-F1、balanced accuracy、相對退化與檔案雜湊。 | M | nlp_readme.md:L307 |
| SPEC-GAP-RULE_NO_-E21E40460D02 | rule_no_condition | 規則缺觸發條件/門檻: CPU 主機建議先使用較小的 Embedding 模型； | M | nlp_readme.md:L332 |
| SPEC-GAP-RULE_NO_-6D6FC739DF40 | rule_no_condition | 規則缺觸發條件/門檻: 不應把 FP16／FP32 大模型與多個 NLP 模型同時常駐一般電腦。 | M | nlp_readme.md:L333 |
| SPEC-GAP-RULE_NO_-24883FA2B87A | rule_no_condition | 規則缺觸發條件/門檻: 先安裝 `translate` extra，並由使用者明確安裝所需的 `.argosmodel` 語言包； | M | nlp_readme.md:L339 |
| SPEC-GAP-RULE_NO_-316538D31E56 | rule_no_condition | 規則缺觸發條件/門檻: 需同時啟用 `routing.allow_deep_models=true` 與 `routing.allow_llm=true`，並安裝可處理繁體中文的本地模 | M | nlp_readme.md:L363 |
| SPEC-GAP-RULE_NO_-EFDBE11406FE | rule_no_condition | 規則缺觸發條件/門檻: Cloud Translation 是正式可程式化的 Google 翻譯路徑，需要啟用 billing、API 與 authentication。 | M | nlp_readme.md:L367 |
| SPEC-GAP-RULE_NO_-1C4277482D0F | rule_no_condition | 規則缺觸發條件/門檻: 引擎預設離線，因此每次使用還必須明確傳入 `--allow-network`。 | M | nlp_readme.md:L367 |
| SPEC-GAP-RULE_NO_-1215376B57BE | rule_no_condition | 規則缺觸發條件/門檻: 官方建議單次約 5,000 code points； | M | nlp_readme.md:L367 |
| SPEC-GAP-RULE_NO_-FCC6C466B008 | rule_no_condition | 規則缺觸發條件/門檻: 這種自動化容易受驗證碼、DOM 改版與使用限制影響，不能作為穩定引擎依賴。 | M | nlp_readme.md:L376 |
| SPEC-GAP-RULE_NO_-E2E80F975EC6 | rule_no_condition | 規則缺觸發條件/門檻: 引擎只能控制載入與降級，不能保證任何硬體都能跑所有模型。 | M | nlp_readme.md:L403 |
| SPEC-GAP-RULE_NO_-70186668F5B3 | rule_no_condition | 規則缺觸發條件/門檻: PDF 若沒有文字層需先經 OCR； | M | nlp_readme.md:L404 |
| SPEC-GAP-COLUMN_N-AEE30E171145 | column_no_values | 欄位「函式」無值可推型別 | V | ves.html:L55 |
| SPEC-GAP-COLUMN_N-6B35EC53D678 | column_no_values | 欄位「檔案:行」無值可推型別 | V | ves.html:L55 |
| SPEC-GAP-COLUMN_N-3A33525F7477 | column_no_values | 欄位「參數」無值可推型別 | V | ves.html:L55 |
| SPEC-GAP-COLUMN_N-4CBE441848F2 | column_no_values | 欄位「工具」無值可推型別 | V | ves.html:L55 |
| SPEC-GAP-COLUMN_N-3667A47C420A | column_no_values | 欄位「風險」無值可推型別 | V | ves.html:L55 |
| SPEC-GAP-RULE_NO_-DB5525B6F90F | rule_no_condition | 規則缺觸發條件/門檻: FN-10185 Required typing.py:3017 parameters R02 R03 | M | ves.html:L56 |
| SPEC-GAP-RULE_NO_-3CD35BC70412 | rule_no_condition | 規則缺觸發條件/門檻: · 成員 141 · 工具集=0 檔案=71 相似=1.0 N001 TRANSFORM 超大群：連鎖傳遞造成，建議 --threshold 調高至 0.8 提 | M | ves.html:L224 |
| SPEC-GAP-RULE_NO_-3437B046AFCC | rule_no_condition | 規則缺觸發條件/門檻: · 成員 141 · 工具集=0 檔案=71 相似=1.0 N002 PARSE 超大群：連鎖傳遞造成，建議 --threshold 調高至 0.8 提案介面 | M | ves.html:L224 |
| SPEC-GAP-RULE_NO_-7891B6C1C1F6 | rule_no_condition | 規則缺觸發條件/門檻: FN-11088 register webbrowser.py:23 name, klass, instance, preferred | M | ves.html:L224 |
| SPEC-GAP-RULE_NO_-835B18FD229C | rule_no_condition | 規則缺觸發條件/門檻: R02_DECORATOR_HIDES_SIGNATURE 裝飾器隱藏真實簽名 擷取 decorator_list 建對應表； | M | ves.html:L2073 |
| SPEC-GAP-COLUMN_N-D27D0AB41CF0 | column_no_values | 欄位「原因」無值可推型別 | V | ves.html:L2079 |
| SPEC-GAP-RULE_NO_-2B2C4D9BEE89 | rule_no_condition | 規則缺觸發條件/門檻: · ML 首選 scikit-learn · DL 首選 onnxruntime · 本機 LLM 建議 qwen2.5:1.5b 等級：T4 僅輕量 skle | M | ves.html:L2081 |
| SPEC-GAP-COLUMN_N-AD1C5B20A803 | column_no_values | 欄位「functions」無值可推型別 | V | ves.html:L2088 |
| SPEC-GAP-COLUMN_N-36EBD970AE9F | column_no_values | 欄位「risk_M」無值可推型別 | V | ves.html:L2088 |
| SPEC-GAP-COLUMN_N-E0BD7C6342C6 | column_no_values | 欄位「risk_P」無值可推型別 | V | ves.html:L2088 |
| SPEC-GAP-COLUMN_N-E3E5BA0F98DA | column_no_values | 欄位「gates」無值可推型別 | V | ves.html:L2088 |
| SPEC-GAP-FIELD_NO-B8F22BF29DFA | field_no_validation | 欄位 q 無任何驗證(required/pattern/min/max) | V | ves.html:input#q |
| SPEC-GAP-RULE_NO_-F1C9F4D00916 | rule_no_condition | 規則缺觸發條件/門檻: 把它搬進 的對應能力軸，下次執行即生效，OTHER 會自動縮小。 | M | ves.html:L2093 |
| SPEC-GAP-RULE_NO_-7C8FC334EE52 | rule_no_condition | 規則缺觸發條件/門檻: qwen2.5:3b 建議）； | M | ves.html:L2094 |
| SPEC-GAP-RULE_NO_-DEC1D653471D | rule_no_condition | 規則缺觸發條件/門檻: LLM 建議標 M 級，人工搬進 verbs 才升 V。 | M | ves.html:L2094 |
| SPEC-GAP-RULE_NO_-63440749112E | rule_no_condition | 規則缺觸發條件/門檻: 下一步：① adapters 已自動生成 Payload 型別模型＋群內參數同義映射(PARAM_ALIAS)，只剩「未註記型別 = Any」需要補 ② tes | M | ves.html:L2101 |
| SPEC-GAP-NO_VIEWP-5E1BC4B65E0E | no_viewport | 缺 viewport meta（響應式） | V | ves.html:head |
| SPEC-GAP-RULE_NO_-B4C313A08B8F | rule_no_condition | 規則缺觸發條件/門檻: 前後以 `byte_size + BLAKE2s` 驗證，禁止刪除、移動、覆寫 canonical。 | M | vofie_readme.md:L11 |
| SPEC-GAP-RULE_NO_-518B5119A172 | rule_no_condition | 規則缺觸發條件/門檻: 沒有等價測試不得直接套用。 | M | vofie_readme.md:L16 |
| SPEC-GAP-RULE_NO_-F2D0669464C2 | rule_no_condition | 規則缺觸發條件/門檻: 每項都有 cause、detectors、breakers、至少三個 solutions、SOP、never-again control 與 repair la | M | vofie_readme.md:L90 |
| SPEC-GAP-RULE_NO_-FB5CE32E09C8 | rule_no_condition | 規則缺觸發條件/門檻: Activation 必須同時通過 Hydra、self-test、user-test、recovery 與 rollback-ready 契約。 | M | vofie_readme.md:L96 |
| SPEC-GAP-RULE_NO_-ED5E5708D39C | rule_no_condition | 規則缺觸發條件/門檻: Canonical／SSOT 不可直接寫入。 | M | vofie_readme.md:L108 |
| SPEC-GAP-RULE_NO_-F78F121CB40B | rule_no_condition | 規則缺觸發條件/門檻: `rollback-check` 只驗證復原所需 hash 與 manifest，不執行真實 rollback，也不提升 Runtime Copy 為 cano | M | vofie_readme.md:L123 |
| SPEC-GAP-RULE_NO_-417A69358360 | rule_no_condition | 規則缺觸發條件/門檻: 需求式調用： | M | vofie_readme.md:L140 |
| SPEC-GAP-RULE_NO_-6BD4D249CC03 | rule_no_condition | 規則缺觸發條件/門檻: 舊工具只設 `enabled: false`，不可刪除。 | M | vofie_readme.md:L186 |
| SPEC-GAP-RULE_NO_-EBAD9A4CF6A6 | rule_no_condition | 規則缺觸發條件/門檻: 不得覆寫 `ST-FROZEN`、Universal IR、source hash gate、五檔契約與來源唯讀政策。 | M | vofie_readme.md:L189 |
| SPEC-GAP-COMPONEN-74161AF5E7BA | component_no_behavior | button#go <button> 無事件/資料綁定(可能由外部 JS 綁定) | P | vshp_ui.html:button#go |
| SPEC-GAP-FIELD_NO-76444AE724EA | field_no_label | 欄位 optContent 無 label/placeholder/aria-label | V | vshp_ui.html:input#optContent |
| SPEC-GAP-FIELD_NO-5586FB3D8EA0 | field_no_label | 欄位 optCss 無 label/placeholder/aria-label | V | vshp_ui.html:input#optCss |
| SPEC-GAP-FIELD_NO-771716C27AE3 | field_no_label | 欄位 optJs 無 label/placeholder/aria-label | V | vshp_ui.html:input#optJs |
| SPEC-GAP-FIELD_NO-7882558C84ED | field_no_label | 欄位 picker 無 label/placeholder/aria-label | V | vshp_ui.html:input#picker |
| SPEC-GAP-FIELD_NO-4B3F9250C64B | field_no_label | 欄位 pickerDir 無 label/placeholder/aria-label | V | vshp_ui.html:input#pickerDir |
| SPEC-GAP-API_DYNA-E179993CB323 | api_dynamic_url | API 呼叫 URL 為動態組字串，無法靜態確認 | M | vshp_ui.html:L307 |
| SPEC-GAP-STATE-ED7CDF5B99BE | state_no_rule | 狀態「Prompt」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-7F69DFE67498 | state_no_rule | 狀態「accept」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-B3DA7F581A6A | state_no_rule | 狀態「answer」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-AE826B5665B7 | state_no_rule | 狀態「cancel」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-76C023E8E215 | state_no_rule | 狀態「closed」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-C4E8E3ED78E6 | state_no_rule | 狀態「compare」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-6D9AFBBAE267 | state_no_rule | 狀態「connect」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-20F564B5B2BF | state_no_rule | 狀態「connection」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-BDF84CE0ECEE | state_no_rule | 狀態「create」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-747B18987E17 | state_no_rule | 狀態「detach」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-F780381A1174 | state_no_rule | 狀態「domain」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-DF222CC326D6 | state_no_rule | 狀態「fileno」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-204EED4AA5A1 | state_no_rule | 狀態「getregentry」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-427107C87148 | state_no_rule | 狀態「getstate」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-0F8E3123CF1E | state_no_rule | 狀態「joinpath」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-983195FFCF99 | state_no_rule | 狀態「pending_verbs」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-E2047B69DE85 | state_no_rule | 狀態「prepare」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-A663EBB09D86 | state_no_rule | 狀態「question」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-C41634CD839A | state_no_rule | 狀態「readable」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-A9C5BCA25CD4 | state_no_rule | 狀態「readinto」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-7A4728579DB0 | state_no_rule | 狀態「readline」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-C0160D3C75F6 | state_no_rule | 狀態「readlines」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-BE4BDA4544F9 | state_no_rule | 狀態「release」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-804C655E5A38 | state_no_rule | 狀態「remove」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-73BD2852B235 | state_no_rule | 狀態「replace」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-4C3E02160157 | state_no_rule | 狀態「resolve」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-C9ACC2C679F6 | state_no_rule | 狀態「resume」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-8139C875CBF2 | state_no_rule | 狀態「review」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-4620E387A941 | state_no_rule | 狀態「seekable」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-7CAA78306C5B | state_no_rule | 狀態「server」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-1B43BA60CE1D | state_no_rule | 狀態「setstate」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-A6BA89DAD41B | state_no_rule | 狀態「shutdown」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-F891198F92E2 | state_no_rule | 狀態「tokens」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-4AD01C04195A | state_no_rule | 狀態「truncate」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-187AB0BFE7F4 | state_no_rule | 狀態「update」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-6B3F6CA7A82F | state_no_rule | 狀態「values」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-38363F110224 | state_no_rule | 狀態「version」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-5D1996CF3FF9 | state_no_rule | 狀態「writable」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-9855FA04DFEE | state_no_rule | 狀態「writelines」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-E415F9779DE8 | state_no_rule | 狀態「不完整命令降低信心並」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-1876D0616F31 | state_no_rule | 狀態「交接檔」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-C003D02792B9 | state_no_rule | 狀態「匯入」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-62C63CBF3AFA | state_no_rule | 狀態「圖片與音訊」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-016416D56049 | state_no_rule | 狀態「建構拓撲」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-CD0E378950A5 | state_no_rule | 狀態「機器可讀治理契約」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-F820C4092B81 | state_no_rule | 狀態「疑似誤報降權」出現在轉移但無任何規則描述其條件/行為 | P | cross |
| SPEC-GAP-STATE-11ABB7195F33 | state_no_rule | 狀態「的候選版」出現在轉移但無任何規則描述其條件/行為 | P | cross |
