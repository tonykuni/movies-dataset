# 批620:環境完不了工,不是因為缺件

操作員令:**「先把環境完工」**。

量完之後的結論是:**那三個家族境不能靠裝件完工**。理由在下面,證據都在他自己的逐字稿裡。

---

## 一 · 三條線索,同一個根

| # | 線索 | 出處 |
|---|---|---|
| 1 | 彈窗「程式碼執行無法繼續,因為找不到 **python312.dll**」 | 他的截圖 |
| 2 | `vdf/vrn/vap 解譯器 OK **3.13.7** · re=`C:\Python313\Lib\re\__init__.py` | `04_EnvRunGate` |
| 3 | `AttributeError: module 'pyarrow' has no attribute '__version__'` | `VAP_ENG015` ENV_BROKEN |

三個境叫 `via_vdf_312` / `via_vrn_312` / `via_vap_312`，**名字寫 312，跑的是 313**。

`pyarrow` 那一句不是缺件，是**原生模組半載**的長相：site-packages 裡若還躺著
`cp312` 的輪子，載進 3.13 就是這樣。而 RunGate 給的下一步是
`--approve-install pandas` ——**往一個 ABI 已經錯位的境裡再裝一個輪子**。

## 二 · 還有一件更難發現的：BASE 換了一支直譯器

同一台機器，相隔 70 分鐘：

```
plan  --offline   BASE py3.12.12 · 件 242 · 衝突   0 · 封鎖家族件 29 · manifest 缺 10
apply --online    BASE py3.13.7  · 件 692 · 衝突 136 · 封鎖家族件 70 · manifest 缺  0
```

看起來像環境在這 70 分鐘裡爆炸。其實是 `discover_envs()` 的第一行：

```python
bp = base_python or sys.executable
```

**BASE 的定義是「誰在跑我」。**3.12 那支壞了（線索 1），啟動器退到 3.13，BASE 就換了人。
而 digest 從頭到尾只印 `BASE py3.13.7` ——**沒有印它是哪一支檔案**，所以也看不出來換了。

引擎其實察覺了一半：`in_venv` 時會印 `[警] 本解譯器為 venv 非 base`。
但那是一行警告，不擋任何事，而且只管 venv、不管換版。

**救了這一跑的是 L19**：`執行:跑 0 · BLOCKED 136` ——RunGate 判 YELLOW，整批擋下，一件都沒裝。
閘做對了事；看得見的那一層沒有。

---

## 三 · v0112 補了什麼

### 境身分四來源對照

每一境比對四個來源：**名字 / `pyvenv.cfg` / 活直譯器 / 原生輪子標籤**。

| 態 | 意思 |
|---|---|
| `OK` | 四者一致 |
| `NAME_LIES` | 名字宣告 3.12，活直譯器 3.13 —— 冊上照名字分類就會全錯 |
| `HOME_DRIFT` | `pyvenv.cfg` 記的 base 已經不是現在回答的那一支 |
| `ABI_MISMATCH` | 輪子 `cp312` 配直譯器 3.13 —— **不是缺件，裝更多件只會更糟** |
| `NODATA` | 探針沒跑起來 —— 不猜，也**不判紅** |

修法句直接寫在紅燈底下：
**名實不符的境不能靠裝件補，要 `via-rebuild --env <名>` 在同一支直譯器上重建。**

### BASE 換人閘（L94）

* digest 第一行現在印 **BASE 是哪一支檔案**：
  `BASE 身分:3.11.15 @ /usr/local/bin/python3 · 件 98 · base`
* 每一跑把身分寫進存證，下一跑自動對照：`SAME` / `CHANGED` / `NODATA`
* `CHANGED` 時 **apply 一律擋下**，並講出新舊兩支；要照跑得自己打
  `--base-changed-ok` ——**不代設**

自測 46 → **49 檢**，五條身分路與三態換人閘各走一次（L83：半條路不算跑過）。

---

## 四 · 完工要怎麼走（你的手）

引擎不代裝、不代刪、不代重建。順序是固定的：

```powershell
# ① 先看 BASE 到底是誰，以及 3.12 還在不在
where.exe python ; py -0p
Get-Command python | Select-Object -Expand Source

# ② 三個家族境的身分(v0112 會自己印;這是給你眼睛看的版本)
foreach ($e in 'via_vdf_312','via_vrn_312','via_vap_312') {
  $p = "C:\Users\tonyk\envs\$e"
  "$e : " + (& "$p\Scripts\python.exe" -c "import sys;print(sys.version.split()[0])" 2>&1)
  Get-Content "$p\pyvenv.cfg" | Select-String 'home|version'
  (Get-ChildItem "$p\Lib\site-packages" -Recurse -Filter *.pyd -EA 0 |
     ForEach-Object { if ($_.Name -match 'cp(3\d\d)') { $Matches[1] } } |
     Group-Object | Sort-Object Count -Desc | Select-Object -First 3 Name,Count)
}
```

② 若印出 `cp312` 的輪子而直譯器是 3.13 —— 那就是 ABI 錯位，**重建，不要補裝**：

```powershell
via-envgov plan --offline          # 先在現在這支 BASE 上重新量一次
via-rebuild --env via_vap_312
via-rebuild --env via_vrn_312
via-rebuild --env via_paddle_311
via-envgov apply --approve         # BASE 沒換人才會放行
```

**先決定 BASE 要是哪一支**（把 3.12 修回來，或全樹改站在 3.13），再重建。
決定之前重建只是換個時間再壞一次。

---

## 登錄

* 法 92（**+L94 計畫與執行同體律**）· 課 193（+LL192/LL193）· 台帳 1218
* 新件：`CGC_MDL135_EnvGovernance_v0112.py` · `CGC_MDL064_SelftestGrid_v0374.py`（站名 31→49 檢）
