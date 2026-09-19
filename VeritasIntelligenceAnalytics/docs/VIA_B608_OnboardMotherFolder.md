# 批608 — 上船母資料夾:不是一個動作,是一次分類(LL165)

操作員令「上船母資料夾」。

---

## 一、先量再造:`via-intake` **不是**這件事

倉裡已經有 `CGC_MDL057_Intake`(`via-intake`)。看起來很像,但:

| | `via-intake` | 上船母資料夾 |
|---|---|---|
| 對象 | **外面的檔**(預設掃 `~\Downloads`) | 母資料夾裡**早就在它該在的位置**的檔 |
| 做什麼 | 分類 + 給 URN + **搬檔案** + 註冊 | 只缺一件事:**進 git** |

**名字像不代表是同一件事。** 所以不套用它,也不另造引擎 ——
掛在 `Sync-VIA-Bootstrap-v0100.ps1` 上:git 側的事歸 git 側的工具,固定檔名,
而且**它已經在你磁碟上**(批605 那次快轉帶進去的),不必再經歷一次 L85 的「工具在拿不到的那一側」。

## 二、三類,逐件印出來

母資料夾裡沒進 git 的東西有三種。當成同一種處理,兩邊都會壞:

- **全上船** → 再生物和 `.bak_`、`__pycache__` 一起進倉(倉變髒,下一跑又生一批)
- **全不上船** → 你辛苦寫的引擎新版永遠留在那一台

```
再生物   引擎跑一次就重生:VIA_Reports\ · ui_support 的頁 · 被引擎覆寫的註冊表
暫存     .bak_ · .tmp · __pycache__ · ~ · .orig/.rej · 一次性補丁夾 _patches\
該上船   其餘(引擎新版 · docs · launchers · 手維護的冊)
```

**分類是我做的,裁定是你的** —— 所以每一件都印出來,而且**預設只清點不動**。

## 三、怎麼用

```powershell
# 清點(唯讀,什麼都不動)
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\VeritasIntelligenceAnalytics\launchers\Sync-VIA-Bootstrap-v0100.ps1" -Onboard

# 看過清單、同意了才上船(只收「該上船」那一類)
... -Onboard -Commit

# 連推也一起(否則 commit 完會把 git push 那行印給你自己跑)
... -Onboard -Commit -Push
```

## 四、真跑驗過(scratch 倉造 11 件三類混合)

```
[該上船] 5 件   docs/VIA_B999_Note.md · VDF_ENG099_X_v0100.py · Invoke-VIA-Thing-v0100.ps1
                Sync-VIA-Bootstrap-v0100.ps1 · VIA_Policy_Laws_SSOT_v0100.json(已改)
[再生物] 3 件   VIA_Reports\nlp_unified\latest.json · VIA_Schema_Registry · VIA_UI_Foo
[暫存]   3 件   _patches\_apply_bus_diff.py · __pycache__\x.pyc · *.bak_b600_20260918
```

| 量什麼 | 結果 |
|---|---|
| 分類 11 件 | 全對 |
| `-Commit` 收了幾件 | **只有該上船的 5 件** |
| 沒上船的 6 件 | 工作樹**原封不動**(3 件 ` M` + 3 件 `??` 都還在) |
| 有沒有被推 | **沒有**,`origin` 仍停在基準 —— 推是你的手 |

## 五、順帶:這次不必再貼任何東西

`v0106` 不在你那台是因為批607 還沒 pull。但**解卡件已經在你磁碟上**:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\VeritasIntelligenceAnalytics\launchers\Sync-VIA-Bootstrap-v0100.ps1"
```

跑完它會印出「下一步」那一行,指到**當下的尾版** launcher(批606 改成 glob 取尾版,不寫死版號)。
**L85 就是為了這一刻立的。**
