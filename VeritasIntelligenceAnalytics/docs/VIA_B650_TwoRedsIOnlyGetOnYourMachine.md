# 批650 · 兩盞只在你機器上會亮的紅燈

你跑 `via-run25`,拿回來的是:

```
[計] GREEN 4 · RED 2 · NODATA 1 · ABSENT 0 · GATED 0 · SKIP 1 · 162s
```

容器裡同一支令是 **GREEN 6 · RED 0**。差別不是運氣,是**容器的料走不到那兩條路**。

---

## 紅① ENG085 `NameError: name 'ok' is not defined`

```
File "...VRN_ENG085_MarkdownRestore_v0103.py", line 1040, in main
    _pp = disagree_pairs(ok)
NameError: name 'ok' is not defined
```

還原本身是**成功**的:105 份 OK 105 · 保全 100% · 二尺一致 1093/1123 = 97.3%。
**炸的是印報告那一段。**

`ok` 是 `run()` 的區域變數,`main()` 裡根本沒有這個名字。
而這一行只有在**二尺對不上**的時候才會執行:

| | 二尺一致 | 這一行 |
|---|---|---|
| 容器 | 380/380 = **100%** | 從寫下來那天起**沒執行過一次** |
| 你的機器 | 1093/1123 = 97.3% | 第一次走進去,當場炸 |

### 最難看的一層

批640 我**已經**把 `disagree_pairs` 抽成函式,還寫了檢 ㉛ 拿假資料測它。
那個檢的說明我自己是這樣寫的:

> (容器零分歧,所以這一段在容器裡走不到,**抽成函式才驗得了 L83**)

**我測了那支函式,沒測呼叫它的那一行。**
抽成函式讓那支函式可測,不等於那個呼叫點被測過。→ **LL286**

### 修法

整段畫面抽成純函式 `render_run(res)`,自測餵一個「有分歧」的 `res` 走完全程,
外加負控(零分歧時不得印成對統計)。

然後**把 v0103 的錯誤重新注回去**,確認檢會 FAIL:

```
[FAIL] ㉜ **有分歧時的那一段畫面要真的被跑過**…
[計] 32 檢 OK 31 · FAIL 1
```

尺要證明咬得住,不能只證明自己會過。ENG085 v0104:**32 檢 OK 32**。

---

## 紅② MDL160「漂移 173」—— 那不是漂移

```
[完整性] 冊上 223 件 · sha 對得上 50 · **漂移 173** · **缺件 0**
  [不一致] CHANGELOG.md / README.md / STANDARD.md / ci/deploy_via_remote.sh …
```

先不猜,先數。容器裡量同一包 223 件:

| | 件 |
|---|--:|
| 二進位(png/woff/…) | 42 |
| 本來就是 CRLF 的文字件 | 8 |
| **小計** | **50** ← 正好是你對得上的 50 |
| **純 LF 文字件** | **173** ← 正好是你的「漂移 173」 |

**一個不多一個不少。**
那不是正本被改過,是 Windows 的 `core.autocrlf` 在 checkout 時把 LF 換成 CRLF,
每一行多一個位元組。`manifest.json` 的 sha256 算的是**原始位元**,當然對不上。

### 更該講的是:倉庫裡早就有這把鎖

`.gitattributes` 裡本來就有:

```
VeritasIntelligenceAnalytics/functional*modules/VTR/** -text
VeritasIntelligenceAnalytics/supportive*modules/VIA_Governance_Runtime/v0160A/** -text
# 批546 收容件位元鎖(md5 冊比對的是**原始位元**…那是判錯的紅燈)
VeritasIntelligenceAnalytics/**/references/intake/** -text
```

VTR、v0160A、收容件 —— 三種東西都因為**同一個理由**鎖過位元。
批647 我帶進第四種同類的東西(223 筆 sha256 的正典包),**沒去看那把鎖**。→ **LL287**

### 修法(兩件缺一不可)

```
# ① 倉庫端:位元鎖(本批已加)
VeritasIntelligenceAnalytics/VIA_HTML_UI/** -text
```

② **光 pull 不會把已經在磁碟上的檔換回來**——這句我在沙盒裡實測過,不是推論:

```
加 .gitattributes 後 pull → od -c a.md → line1 \r \n   (還是 CRLF)
git status                → " M a.md"                  (git 認為它被改過了)
git checkout HEAD -- a.md → od -c a.md → line1 \n      (換回原始位元)
git status                → (空)                        (乾淨)
```

### 閘也改了

換行被改寫 **仍然判紅** —— 冊的承諾就是逐位元相同,放行等於假綠。
但它要跟「內容被人改過」分開報,而且當場講得出治法:

```
[完整性] 冊上 223 件 · sha 對得上 223 · **內容漂移 0** · **換行被改寫 0** · **缺件 0**
```

檢 ㉗ 雙向負控:CRLF 化的 → `eol_converted`;真的動到內容的 → `sha_drift`。
兩種都紅,但**紅的理由不能混為一談**。

---

## 順便更正我自己講過的一句話

批644 我說「**TWSE 整所缺席 1,088 檔**」。那是**容器空庫的樣子**,不是你的庫的樣子。
你的機器量出來是:

```
[TPEX] 冊 892 · 有料 892(100.0%) · 缺 0
[TWSE] 冊 1103 · 有料 1097( 99.5%) · 缺 6
[缺價] 0054 元大台商50 / 0058 富邦發達 / 0059 富邦金融 / 0060 新台灣 / 0080 恒中國 / 0081 恒香港
```

**缺的是 6 檔老 ETF,不是一整個交易所。** VRN 研報的 47 檔票號,正典冊認得 47、價表有料 47。
`UNIVERSE_RECONCILIATION` 也已經在位(那是 LL274 欠的)。

---

## 你這邊要下的三道

```powershell
cd C:\Users\tonyk\OneDrive\Documents\movies-dataset
git pull origin claude/via-envmanager-governance-7cls8h
git checkout HEAD -- "VeritasIntelligenceAnalytics/VIA_HTML_UI"
via-run25
```

第三道之後那兩盞紅應該都會轉綠。`roster` 那盞仍然是 **NODATA(缺 6 檔 ETF 的價)**——
補價要觸網,`VIA_NET_CONSENT` 一樣是你的手,我不代設。
