# 批577 · U/I 紅燈 18 → 6,而且剩下的 6 張全是「頁比引擎舊」

## 一、先逐張看紅在哪一個字 —— 18 盞裡有 9 盞是假的

批576 收完分母剩 18 紅。我原本要直接去修 18 支引擎;**先把違規字串印出來**:

| 假紅 | 幾張 | 紅在哪一個字 | 為什麼是假的 |
|---|---|---|---|
| `zero_cdn` | **8** | `href="http://127.0.0.1:8765/master"` | 那是**本機指揮台橋**(DeckServer),不是 CDN。零 CDN 管的是外連第三方;把回送位址算進去,等於要求頁不准連自己的橋 |
| `zero_popup` | **1** | `<code>FNC009</code> confirm()` | `VIA_UI_TreeAtlas` 列的是**函數名冊的說明文字**。彈窗是行為,行為只可能發生在腳本裡 |

尺收窄(並用合成頁**雙向**釘住:真的 `fonts.googleapis` / 真的 `alert(` 仍然判紅):

- `zero_cdn` → 只看**第三方**外連;回送位址(`127.0.0.1` / `localhost` / `::1`)具名豁免,
  但**另計** `local_bridge_pages`,不讓豁免變成消失(L68)
- `zero_popup` → 只看**腳本脈絡**:`<script>` 內文 + `on*` 行內處理器

```
RED 18  →  9（九張全是真的）
```

## 二、九張真紅逐支修完

| 頁 | 違規 | 修法 |
|---|---|---|
| DataCatalog · SyncStatus | `alert("無橋…")` | `CGC_MDL098 v0101` / `CGC_MDL096 v0110`:改**行內提示條**(JS 自建元素,不動 HTML 模板,保留原訊息字串) |
| WorkflowComposer | `prompt('工作流 id…')` | `CGC_MDL153 v0101`:改行內 `<input>`(自動插在按鈕旁),命名能力沒有損失 |
| Hub_v0108 | Google Fonts 外連 | `SUP_MDL141 v0109`:拿掉 `<link>`,襯線/CJK 走系統字體堆疊(離線可用) |
| CentralGovernanceConsole | 缺 viewport | `CGC_MDL149 v0114` |
| ReportDigest | 缺 viewport | `vrn_report_digest v0116` |
| VAP / VDF / VRN_Standalone | 缺 viewport·lang·字體外連 | 改**靜態正本**:`functional modules/VDF/VIA_VDF_Fetch_ONE__Standalone.html`、`functional modules/VAP/VIA_VAP_ONE__Standalone.html`、`supportive modules/VIA_VisualLock/VIA_VRN_VisualLock_Sidebar_v0159.html`(`VIA_Reports/` 下那三張是 MDL138 複製過去的**產物**,而且被 .gitignore,改它沒有用) |

## 三、剩下 6 張:不是「引擎沒修」,是「頁比引擎舊」

```
RED 6 · 全部 fix_ready=True
  VIA_UI_CentralGovernanceConsole_v0100.html   ← CGC_MDL149 尾版已乾淨
  VIA_UI_DataCatalog_v0100.html                ← CGC_MDL098 尾版已乾淨
  VIA_UI_Hub_v0108.html                        ← SUP_MDL141 尾版已乾淨
  VIA_UI_SyncStatus_v0100.html                 ← CGC_MDL096 / MDL122 尾版已乾淨
  VIA_UI_WorkflowComposer_v0100.html           ← CGC_MDL153 尾版已乾淨
  VIA_UI_ReportDigest.html                     ← vrn_report_digest 尾版已乾淨
```

這六張是**批577 之前產出的舊產物**。閘現在分得出兩件事:

- **引擎還沒修** → 去改引擎
- **頁比引擎舊** → `★ owner 尾版已修好(批577):跑一次再生這張就會綠`

> 混在同一個 RED 裡就等於沒講 —— 兩者的下一步完全不同。

**容器不代再生**(LL49:沙盒庫是空的,再生會拿 ABSENT 蓋掉工作站的真快照)。
你那邊跑一次總控頁/現況台再生,這六張就會轉綠。

## 四、我自己踩到的兩個坑

**① 改錯了地方。** 我先去改 `VIA_Reports/VIA_UI_VAP_Standalone.html` —— 跑完全格子之後改動不見了。
原因有兩層:那三張是 MDL138 從**靜態正本**複製過去的產物,而且 `VIA_Reports/*` 在 `.gitignore` 裡,
**根本推不上去**。真正要改的是 `functional modules/` 與 `VIA_VisualLock/` 下的三張靜態正本。
**產物長得跟正本一樣,但改產物等於沒改。**

**②** 我在閘的說明文字裡拿 `VIA_UI_Hub_v0108.html` 當例子,結果 owner 判定把**閘自己**
認成那張頁的 owner —— 自我指涉要排除。另外 `OWNER_SCAN` 漏了
`supportive modules/VIA_Governance_Runtime`(Hub 系列的 owner 住那裡)與 `ui_support`,
補上之後 Hub 才找得到真正的再生者。

## 五、回歸

```
全格子 241 站 · OK 239 · FAIL 0 · SKIP 2
CGC_MDL160 v0103 22/22 · MDL096 v0110 10/10 · MDL098 v0101 8/8 · MDL153 v0101 12/12
VCGC v0114 20/20 · 元件冊 5340
```

**本批零 PowerShell 改動 · 零套件安裝**(L70)。
所有短令都用 `Get-VIANewest` 自動接到新版:`via-uiunify` / `via-sync` / `via-catalog` / `via-workflow` / `via-vcgc`。

教訓 `LL132`。
