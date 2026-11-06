# VIA_SettleAll v0113(操作員 2026-11-06「自動導入完成 VCGC 收尾 · 啟動所有節省 TOKEN 工具 · 矩陣式顯示測試所有 VCGC 內容工具架構不要遺漏 · 功能 / 狀況 / 測試類型分類 · 版本 / 耗時 / 燈號 / 編號 / 名稱 / 說明 HEADERS」· v0112 一字不動)

## 新增

| 段 | 內容 |
|---|---|
| **⑮ VAP** | 入倉夾 `functional modules/VAP/intake/allinone_v0300/` 的 `VAP_AllInOne_v*.py` 尾版跑 `--run-self-test`(python -I · 它自己的夾 · 不開瀏覽器 · loopback · 不連網)→ JSON status PASS 且 rc 0 🟢 · rc 2 🟡 · 其他 🔴 · 沒檔 ⚪。⑫ VAP 列從此有真燈 · 版本 · VCGC 編號;⑭ 也掃這個夾;④⑤⑧⑨⑮ 併行。 |
| **⑫ VCGC 站表矩陣** | 只讀 VCGC 自己的冊與收據:盤點冊 `VIA_VCGC_FunctionInventory_SSOT` **每一站**(319)× 測試狀態冊 `VIA_Reports/vcgc/TEST_STATE_v0101.json`(最後一次燈 · rc · 秒 · 時間 · 最後一行;TEST_latest 更新的蓋過去)× 相依模組尾版(版本 · VCGC 編號(MDL / ENG 冊)· 功能帳最後一筆)。HEADERS:燈 · 站號 · **類型**(主控台動詞 / 交接案 / 引擎自測 / PowerShell 入口 / 項鏈派送 / 舊套 / 品質閘候選 / 席位自測 / SSOT 中央資產 / 本地工具契約)· 名稱 · 說明 / 指令 · **測試型**(quick / full · ps · 黃 rc)· 逾時 · 模組尾版 · 版本 · VCGC 編號 · 功能帳 · rc · 耗時秒 · 測試時間 · 最後一行 → `VIA_Reports/settle/VCGC_StationMatrix_latest.json / .md / .html`(可篩);⑫ 多子列「VCGC 站表」;報告有依類型小計;貼回包含三檔。 |

自測 43 / 43(新 ㉙ ⑮ 三色 · ㉚ 站表:新狀態蓋舊 · 類型 / 測試型 · 相依尾版 + 功能帳 + 編號 · 沒測 ⚪ · 小計 · ⑫ 子列)。

## 容器實跑(2026-11-06 14:51 · `--only scan,vcgc,vap,modmatrix,matrix,report`)

- ⑮ VAP **🟢** AllInOne v0300 自測 PASS · 16 項 · 缺選用套件 duckdb / talib(容器)。
- ⑫ VCGC 站表 **319 站 · 🟢 248 🟡 15 🔴 51 ⚪ 5**(狀態到 14:51;紅 = 08:46 那輪 full 的環境紅:NODATA / fastparquet / 無 pwsh / 落後 main 的舊判)。依類:主控台動詞 45(🟢27 🟡12 🔴4 ⚪2)· 交接案 230(🟢184 🔴45 ⚪1)· 引擎自測 8 · PowerShell 7 · 項鏈 10 · 舊套 7 · 品質閘 5 · 席位 3 · SSOT 2 · 本地工具 2。
- ⑥ VCGC **🔴**:串測 11 站綠 9 黃 2,但**交接閘 rc 1**:EVIDENCE_INVALID 259(幾乎全是「相依集多了主控台 v0192」= 併 main 後所有依賴主控台的交接案要重跑 `handoff test <case>`)· CHANGED_CODE_WITHOUT_TEST 427 · ACCEL_BRIDGE_MISSING 4(VRN2_UIAction_v0100 · _vdf_fetch/VDF_TW_AllInOne_v039 · nonstock 引擎原件 · …)· MODULE_UNREGISTERED 4(nonstock reuse 3 + VDF_TW_AllInOne_v039)。
- ⑭ 509 模組尾版(多 VAP_AllInOne)· 🟢 280 🔴 4 ⚪ 225。

## 桌機一行(PowerShell 7 · 從檔案複製 · 取代 v0112 那行)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0113";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0113.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0113.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'B5B75B7B9DBFDE3A10CB4A70B193B337CD9C08174FE0A460C88A335A0F9852B0'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```
