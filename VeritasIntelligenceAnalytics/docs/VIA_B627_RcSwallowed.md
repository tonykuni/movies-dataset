# 批627 · `rc=2` 被一句寫死的話吞掉

工作站實錄,逐字:

```
VRN_ENG073_ReportStructuredDB_v0129.py rc=2 · [入庫] C:\測試樣本報告 無分區 sidecar(先跑 ENG072 v0101)
兩支都 rc=0,但庫沒有出現在 …\functional modules\VRN\output\vrn_reports.duckdb。
```

上一行才剛印 `rc=2`,下一行說「兩支都 rc=0」。

---

## 一 · 先講你那台的狀況

你那棵樹還停在 **批625**:

```
矩陣引擎 : VRN_ENG083_VerifiedMatrix_v0102.py      ← 批625 的
指令冊   : Register-VIA-Commands-v0226.ps1         ← 批625 的
```

啟動器是 `Get-Newest 'VRN_ENG083_VerifiedMatrix_v*.py'` 取尾版,所以它挑到 v0102
就代表 **v0103 不在你機器上**。而 `無分區 sidecar` 正是 **批626 修掉的那一個**:

> 批624 我看到 ENG073 收不到夾,就補了 `--dir <報告夾>`——而我從來沒讀過 `--dir` 是什麼。
> 讀了才知道 `--dir` 指的是**分區 sidecar 夾**(ENG073 的 `ZONES_DIR` 預設,
> 正好就是 ENG072 寫出去的那一夾),不是 PDF 原始夾。
> 我把一個本來會動的預設,改成一個保證不會動的明傳。

所以你那三輪換庫,是在找一個**根本沒被寫出來**的檔。

## 二 · 但那句「兩支都 rc=0」是另一個病,批626 沒修到

```python
bad = [s for s in steps if s["rc"] not in (0, 2)]     # rc=2 算「不壞」——這是對的
if not bad and not dbp.exists():
    out["why"] = f"兩支都 rc=0,但庫沒有出現在 {dbp}。…"   # ← 這裡把 rc=2 一起吞了
```

自相矛盾只是表面。**真正的傷是它把答案蓋掉了**:ENG073 說的是「我沒有料」,
而這句話把人送去找「庫被寫到哪」。你就照著找了三輪、換了兩個庫,每一輪同一個 NODATA。

**v0105 三態分流**,NODATA 排在找庫前面,句子裡的 rc 由 `steps` 現場組:

```
VRN_ENG072_FirstPageText rc=0 · VRN_ENG073_ReportStructuredDB rc=2。
鏈上有站誠實回報 NODATA(=沒有料),**所以庫不會出現,換一個庫去讀也不會變出資料**。
它說的是:VRN_ENG073_…_v0129.py:[入庫] C:\測試樣本報告 無分區 sidecar(先跑 ENG072 v0101)
```

## 三 · 實跑之後又抓到兩個(都是我這一批自己造的)

| 病 | 症狀 |
|---|---|
| 尾訊按字元切 | 失敗步驟的 `tail` 是**整份輸出**(L62 不切),我用 `[-200:]` 去切,切到橫幅裡的半句話:「…v0136.py:50);③ 只在 ② **跑了但零字**時才升階」。改成**取最後 n 行非空**——引擎的結論印在最後。 |
| 下游猜哪一行是理由 | 啟動器用 `-match 'rc=\d'` 撈最後三行,撈到的也是橫幅。ENG083 v0105 起把理由印成單行 **`[鏈因] …`**,下游 grep 標記(跟「有 rc 就別比字串」同一條)。 |

## 四 · 啟動器 v0103:鏈說沒料就當場停

鏈沒有料,庫就不會被寫出來。**換一個庫不是一個真差異**(批625 輪迴律)。

```
半 A(空樣本夾)  NODATA · 輪次 1 步 · 不換庫       ← v0101 是 4 步 / 3 輪 / 換 2 個庫
半 B(合成 8 件) GREEN  · 輪次 2 步 · exit 0 · matrix OK 81 份 × 7 欄
```

次步也換成對的一組(L92:給一個保證走不通的下一步,等於讓人繞圈繞得更久):

```
1) 料在不在:<樣本夾> 裡有幾份 .pdf/.docx?
2) 分區 sidecar 在不在:VIA_Reports\first_page_text\*.json
   (ENG072 寫這裡、ENG073 預設讀這裡;說「無分區 sidecar」就是這一夾空)
3) 逐步原文在 <存證夾>
```

## 五 · 你現在該打的

```
cd C:\Users\tonyk\OneDrive\Documents\movies-dataset
via-regen --apply
git pull origin claude/via-envmanager-governance-7cls8h
via-reload
via-vrnaudit -In "C:\測試樣本報告"
```

`via-regen --apply` 先把引擎自己長出來的再生物放回去(批613;不先做會被它擋住 pull,
批605/606/612 卡死三次都是這個)。拉完之後尾版律會自己挑到
`VRN_ENG083_VerifiedMatrix_v0105.py` 與 `Invoke-VIA-VRNAudit-v0103.ps1`。
