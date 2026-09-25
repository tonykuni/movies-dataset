# 批651 · VRN 最成功的那一次,不在你每天跑的那條鏈上

## 你的令

> 只要先完成 VIA VRN VDF,其他先暫緩。VRN 之前有非常成功的實測成功紀錄,
> 母系統及 GITHUB LOGS 及上面的對話紀錄,**從最成功的狀態去修改優化直到成功**。

## 考古:最成功的那一次是哪一次

翻 commit log + docs,找到的是 **批630B**:

```
[判對率] 100.0% = PASS ÷(PASS+FAIL) = 302/302 · 另有 4 格驗不了
判對率 100%,FAIL 0 格。
```

那是 `VRN_ENG083 驗真矩陣`。容器今天原地重跑:

```
[自證] 一致 · 格子 567/567 · 5 態重數符合
       裁決 {'NOT_APPLICABLE': 34, 'NO_VALUE': 197, 'PASS': 302, 'UNVERIFIABLE': 34}
[判對率] 100.0% = 302/302 · 另有 34 格驗不了
rc=0
```

**沒有退步。東西還在。**

## 但它不在鏈上

`via-run25` 的八站裡**沒有矩陣**。
你每天跑的那條鏈,量不到 VRN 的頭號成功指標 —— 它只會出現在你特地去敲 `via-vrnmatrix` 的時候。

> **LL279:做好的東西站在系統外面,跟沒做一樣。** 這次輪到 VRN 最好的那個數字。

開第九站:

```
    matrix    驗真矩陣·判對率(ENG083)   批630B 最成功紀錄 302/302 ← 需 structdb
```

容器九站實跑:

```
  [GREEN ] 驗真矩陣·判對率(ENG083)   0.3s
  [判對率] 100.0% = PASS ÷(PASS+FAIL) = 302/302
  [計] GREEN 7 · RED 0 · NODATA 1 · ABSENT 0 · GATED 0 · SKIP 1 · 28s
```

零彈窗:ENG083 認 `VIA_NO_OPEN`,不會在你的機器上跳出瀏覽器。

---

## 往上修①:那 16 次「一個字母是大標題」

批650 那盞紅轉綠之後,成對統計第一次吐出來:

```
 14 次 · ENG085=標題/H1     vs 分析器=paragraph/段落  例:'M'
 10 次 · ENG085=表/表格殘片  vs 分析器=unordered_list  例:'- - - - - - iPhone 12 Pr'
  2 次 · ENG085=表/表格殘片  vs 分析器=ordered_list
  2 次 · ENG085=標題/H1     vs 分析器=blockquote/引用  例:'M'
  2 次 · ENG085=本文/句      vs 分析器=table/表格      例:'00J g |!'
```

**30 塊裡有 16 塊,是同一個字母 `'M'` 被判成大標題。**

去讀碼,根因一眼:

```python
def level_of(el, body_font):
    r = (el.get("size") or 0) / body_font
    for L in LEVELS:
        if r >= L["min_ratio"] and (el.get("bold") if L["need_bold"] else True):
            return L["id"]
```

**只看字級 × 粗體,完全不看內容。** 研報封面那個又大又粗的券商 logo 單字(M)當然中。
而這條規則自己的說明寫的是:

> 「**大標題是帶著股票名稱與代碼的那一句**」

一個孤零零的 `'M'` 不是那一句。

### 但我不能在這裡驗證它

容器 81 份還原 `.md`,我 grep 單字元標題:**0 個**。
那 16 塊在你多出來的 24 份研報裡,**我看不到**。

所以這條改動我寫成一個講得出理由的假設,並且**證明它在容器零回歸**:

```
v0104 → 81 份 OK 81 · 保全 100.00% · 二尺量到 73 份 · 表格 8 列
v0105 → 81 份 OK 81 · 保全 100.00% · 二尺量到 73 份 · 表格 8 列
（逐行相同）
```

內容閘:標題至少要 **2 個有效字元**(CJK 或英數)。`結論`、`2330` 留得住,`M`、`※` 擋掉。
兩個出標題的口(LAYOUT 標的、字級推算)**都要過**。

### 而且下一次跑會自己回答

分歧統計補上**檔名**:

```
   14 次 · ENG085=標題/H1 vs 分析器=paragraph/段落 例:'M'
          出處:XXX.json / YYY.json / ZZZ.json
```

我在這裡重現不了,那就讓你的機器說。

---

## 往上修②:我不該猜第二次

批650 我量出「漂移 173 = git 改寫換行」—— 那一步是對的。
開的藥方 `git checkout HEAD -- <路徑>` 在我的沙盒**兩種情境都成功**換回 LF。

**你的機器上一件都沒換回來。**

可能的原因至少三個,而且我一個都驗證不了:

| 可能 | 我為什麼看不到 |
|---|---|
| 位元鎖沒生效 | 要在你的機器跑 `git check-attr` |
| `$GIT_DIR/info/attributes` 有本機規則 | **那個檔不進倉庫,我永遠看不到** |
| git 的 stat 快取認為乾淨 → checkout 不重寫 | 只在舊 checkout 上發生,沙盒太新 |

**隔著網路猜第二次,就是亂槍打鳥。** → **LL288**

所以把三個只讀的問題搬進閘裡,一次問完:

```
[問 git] 工作副本 C:\... · core.autocrlf=true
         check-attr → VIA_HTML_UI/CHANGELOG.md: text: unset · git 看得見被改過的 173 件
[YELLOW] 位元鎖生效,而且 git 看得見這些檔被改過(173 件)。下一道:
    git checkout HEAD -- "VeritasIntelligenceAnalytics/VIA_HTML_UI"
```

三種局面各給**不同**的下一道。最要緊的是第三種:

```
[RED] 位元鎖生效,但 git 認為工作副本是乾淨的 —— 它的 stat 快取還停在舊屬性下的判斷,
      所以 checkout 不會重寫任何檔案(這正是批650 那一道沒生效的樣子)。
      把索引條目拿掉再長回來,強制重寫:
    git rm --cached -r -q -- "VeritasIntelligenceAnalytics/VIA_HTML_UI"
    git checkout HEAD -- "VeritasIntelligenceAnalytics/VIA_HTML_UI"
```

只讀、不寫、不觸網。閘自測三種局面都各自造了一個真的 git repo 驗過。

---

## 你這邊

```powershell
git pull origin claude/via-envmanager-governance-7cls8h
via-run25 --only template
```

那一站會**自己告訴你**下一道該打什麼 —— 不用再等我猜。
然後:

```powershell
via-run25
```

九站,判對率會直接印在鏈上。`roster` 那盞仍是 NODATA(缺 6 檔老 ETF 的價),補價要 `VIA_NET_CONSENT`,那是你的手。
