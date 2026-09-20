# 批647 · 做好的東西站在系統外面,跟沒做一樣

## 你的裁定
> VIA_HTML_UI 進 VIA,為可調整統一銜接系統的 TEMPLATE

## 我先量它到底是什麼

那 226 件是**一整包做完、驗過、寫好標準**的離線 U/I:

| 量到的 | |
|---|---|
| 三支入口頁 | **零 `fetch(`、零 XHR、零外部 src** · 狀態走 `localStorage` |
| `manifest.json` | 223 筆逐檔 **sha256** · 4 產業 profile × 5 模組 |
| 品質基線 | e2e **54/54** · 跨頁同步 **11/11** · 三視埠 |
| `STANDARD.md` | 「The package must remain usable from `file://` without network access」 |

**而它只在 `main`。**

- 我的工作分支:**0 件**
- Register 冊上:**零引用**
- 短令:無 · 梭:無 · 格子站:無

> **系統裡沒有任何一條路走得到它。**

而在同一段時間,我正在量「樹內 `ui_support/VIA_UI_*.html` 68 份裡有 **30 份要靠 hub**」。

兩件事其實是同一件:
**能離線開的那一套沒被接上,被接上的那一套不能離線開。** → **LL279**

## 搬進來:兩條歷史沒有共同祖先

```
git merge origin/main → fatal: refusing to merge unrelated histories
```

所以不能合併歷史,改成**把目錄整包搬入** `VeritasIntelligenceAnalytics/VIA_HTML_UI/`
—— 內部相對路徑原封不動,再**逐檔對 main 驗 sha256**:

> **226 件,不一致 0。** 正本零觸碰要拿得出證據,不是宣稱。

## `CGC_MDL160` v0105 +`template` 車道

Zero-Hydra:**不新開引擎**。U/I 統一的正主本來就是畫面統一閘,TEMPLATE 契約掛它。

```
via-ui --check
```

```
[CGC_MDL160 v0105] 正典 TEMPLATE · GREEN · 完整性與離線契約皆過
  [完整性] 冊上 223 件 · sha 對得上 223 · 漂移 0 · 缺件 0
  [離線契約] 「file:// 直開、零 server」——本閘逐頁量,不看它自己怎麼宣稱:
    [GREEN ] launcher     ui/VIA-Complete-System.html            6,233 字
    [GREEN ] centralUI    ui/VIA-UI-Standalone-NoServer.html   183,947 字
    [GREEN ] synchronizer ui/VIA-SYNCHRONIZER-Standalone.html   97,800 字
  [銜接面] 產業 profile 4 個 · 模組 5/5/5/5
  [品質基線(冊上)] e2e 54/54 · 跨頁同步 11/11 · 三視埠
```

**那份 STANDARD 的 Offline contract,從散文變成機器每次重驗的一道檢。** → **L100**

四檢咬得住(不是空檢):
- 改**一個位元組** → 當場指名漂移
- 夾不在 → **ABSENT,不是 GREEN**(缺件是缺件,不是零違規)
- 入口頁塞一個 `fetch(` → **RED**
- `--open` 走 SUP_MDL737 的 `VIA_NO_OPEN` 閘,**不自己繞過**

`root` 可注入,自測不摸全域正式產物(LL263 那次撞名的教訓)。

## 自動跳出:一個字

```
via-ui            ← 直接開啟動器(file://,零 server)
via-ui --check    ← 只驗不開
```

**`via-ui.cmd` 這支梭刻意不設 `VIA_NO_OPEN`** ——
其餘 86 支梭都 `set "VIA_NO_OPEN=1"`(批366 零跳出閘,免得全格子開幾百個分頁),
**而這一支的工作就是跳出來**。不想跳就 `--check`,或自己在殼裡設 `VIA_NO_OPEN=1`。

登錄四處(LL199):加速器橋(MDL160 既有)· **梭**(MDL157 26/26)· Register **v0228** · 格子站改名。

## 帳

| 件 | 動作 |
|---|---|
| `VIA_HTML_UI/` 226 件 | 整包進 VIA 樹 · **對 main byte-exact** |
| `CGC_MDL160_UIUnifyGate_v0105.py` | +`template` 車道 · **26 檢** |
| `Register-VIA-Commands-v0228.ps1` | +`via-ui`(v0227 零觸碰,L70) |
| `via-ui.cmd` | 新梭 · **刻意不設 VIA_NO_OPEN** |
| `CGC_MDL064_SelftestGrid_v0403.py` | 站名 二十二檢 → 二十六檢 |
| 律 | **L100** 正典 U/I 是 file:// 零 server 的 TEMPLATE |
| 訓 | **LL279** 只驗內容不驗入口,會得到一個完美而沒有人到得了的東西 |
| 台帳 | 1264 |

## 還沒做的(下一批)

`ui_support/VIA_UI_*.html` 那 30 份要靠 hub 的頁 —— 它們是**產物面**,不是入口面。
要不要把它們也收成「資料內嵌、file:// 直開」,是下一批的題目。
