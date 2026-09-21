# 批686 · 一扇門、三條腿 —— 「東西太多」的解法不是再開一個檔

操作員令:「VIA 東西太多,用一個 `VIA_CentralGovernanceConsole.py` 整合一切;
**如果現在已經有這個角色就合併**;對接下方。」

那句「已經有就合併」是這一批的關鍵 —— 因為量下去,**它已經有了,而且那個檔名也已經被佔走了**。

## 一 · 先量:這個角色在樹上是什麼狀態

| 在哪 | 是什麼 | 狀態 |
|---|---|---|
| `supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0119.py` | **VCGC · 活的正主**(`status`/`check`/`audit`/`matrix`/`panorama`/`registry-sync`/`register-plan`) | 活 |
| `supportive modules/registry/CGC_MDL150_CentralGovernanceFamily_v0103.py` | 中央治理**家族擁有者** | 活 |
| `supportive modules/VIA_Central_Governance/VIA_CentralGovernanceFamily_b514/VIA_CentralGovernanceConsole.py` | b514 家族件 · **原名零觸碰** · `MANIFEST_b514.json` md5 冊 · 擁有者 CGC_MDL150 | 保存件 |
| `references/intake/VIA_GrokConsole_AuroraAcorn_b383/attachments/VIA_CentralGovernanceConsole.py` | 收容件 | 正本零觸碰 |

**所以在根目錄再開一支 `VIA_CentralGovernanceConsole.py` 是錯的**:
同一個名字會變成兩扇門(L101),而且踩到 CGC_MDL150 的所有權(L30)。
操作員那句「已經有就合併」正好把這條路擋住了。

## 二 · 真正缺的不是角色,是「對接下方」那一句

```
VCGC 裡 VRN_SystemManager  提到 15 次,而且是**真的下行呼叫**
        logic()/factors() → VRN_SystemManager.read('logic'|'factor'),缺席=ABSENT 誠實
VCGC 裡 VDF_SystemManager  0 次   ← 本線;側線 busy-bell 的 v0120 已經接上了
VCGC 裡 VAP_SystemManager  0 次   ← 樹上根本沒有這支
bin/ 148 支梭裡沒有 via-vcgc(短令在 Register 裡有,但梭這一面缺)
```

## 三 · 而兩條腿的寫法,本身就是「東西太多」的長法

把批681 的 VRN 段與側線的 VDF 段擺在一起看:

```python
def _vrnsys():                                   def _vdfsys():
    if _VRNSYS["mod"] ... return _VRNSYS["mod"]      if _VDFSYS["mod"] ... return _VDFSYS["mod"]
    p = _newest(VIA/"functional modules"/"VRN",      p = _newest(VIA/"functional modules"/"VDF",
                "VRN_SystemManager_v*.py")                       "VDF_SystemManager_v*.py")
    ...                                              ...
```

**逐字複製貼上,只換家族名。** 再照抄一份給 VAP,就是第三顆頭。
「VIA 東西太多」不是檔案數的問題,是**同一個判準被抄了很多份**的問題。

## 四 · 收成一把尺

新增 `[VIA:SUBSYS-PORT:v0100]` 區塊:

```python
SUBSYS_PORT = {
    "VRN": {"dir": ("functional modules", "VRN"), "glob": "VRN_SystemManager_v*.py"},
    "VDF": {"dir": ("functional modules", "VDF"), "glob": "VDF_SystemManager_v*.py"},
    "VAP": {"dir": ("functional modules", "VAP"), "glob": "VAP_SystemManager_v*.py"},
}
def _subsys(fam)           # 一家的對接口尾版;缺席=None + 因由
def _subsys_section(fam)   # 一家的段(collect();不寫檔)
def subsystems()           # VIA 往下的那一扇門:三家一次報
```

`_vrnsys()` / `_vdfsys()` 退成薄殼(`return _subsys("VRN"|"VDF")`),
而 **`_VRNSYS` / `_VDFSYS` 仍是同一個 dict 物件** —— 所以 `_via_vrnsys()`、
批681 的 ㉔、側線的 ㉖ **一個字都不用改**。收尺不是改行為。

**第四家的成本:表上加一列。** 不是再抄二十行。

跑出來的樣子:

```
三家對接口 1/3 在位
  VRN  STALE/NODATA  VRN_SystemManager_v0101.py
  VDF  ABSENT        functional modules/VDF/VDF_SystemManager_v*.py 缺
  VAP  ABSENT        functional modules/VAP/VAP_SystemManager_v*.py 缺
```

**三欄各說各的,不混成一個數字**(LL327)。`1/3` 這個分數是真的 ——
VDF 那支只在側線分支、VAP 那支根本還沒有,而**缺件不是壞掉**。

## 五 · 順手照出兩條「永遠紅」的檢

改完之後跑自測,㉖ 是紅的。看它的敘述:

> ㉖ …在位時 vdf_system 段九盞燈…;**缺席時 ABSENT 而不是炸**

可是斷言寫的是:

```python
chk("㉖ …", ok_present and vd_abs.get("state") == "ABSENT", …)
#            ↑ 裡面含 `m26 is not None` 與 `"VDF_SystemManager" in _tail_files()`
```

**它要求那支引擎一定要在。** 在沒有 VDF_SystemManager 的樹上(本線、以及側線併入前的 main)
它**永遠是紅的** —— 敘述說它容忍缺席,斷言說不容忍。

㉔(VRN 那條)是同一個病,只是本線碰巧有 VRN_SystemManager 所以是綠的
—— **一盞剛好綠著的燈,和一盞對的燈,看起來一模一樣。**

兩條一起改成**不變量**:

| 態 | 驗什麼 |
|---|---|
| 在位 | 九盞燈 · 有連結 · 七處為七鍵 · 橋律量得出尾版數 · 署名對 |
| 缺席 | 回 ABSENT **而且講得出因由**,不是炸、也不退回舊路 |
| 與對接口無關的 | 「尺有沒有含 VDF 根目錄」維持**無條件**斷言 |

而且把「現在是哪一態」印進細節裡 —— **綠燈不准藏住「這條腿根本不在」。**

## 六 · 那扇門

`bin/via-vcgc.cmd`(LL199 四個註冊面裡缺的那一個;短令在 Register 裡早就有)。
照樹上既有的梭慣例寫:**動態解析尾版,嚴禁寫死版號**。
`.cmd` 不是 `.ps1`,所以這一批**沒有碰任何 PowerShell**(L70)。

### 六之二 · 而我第一版的梭,自己就是第二扇門

第一版 `via-vcgc.cmd` 寫成直接跑引擎:

```cmd
py "%~dp0..\supportive modules\registry\%V_ENG%" %*
```

全格子當場照紅 —— `CGC_MDL165` 的撞名棘輪:

```
⑮ 棘輪:撞名基線外 0    名 307 · 撞名 19 · 基線外 1
```

那個閘分得很清楚(批340 律):

| 類型 | 判定 |
|---|---|
| **梭**(點源 Register 尾版 → 叫 `%~n0` 同名函式) | 契約,**不算撞名** |
| **獨立實作**(自己去跑引擎) | **同一個名字指到不同的東西** → 撞名 |

而 `via-vcgc` 在 Register 裡**早就是同名函式**。所以我那一版不是「補一扇門」,
是**再實作了一次** —— 在這一批的主題正好是「不准有第二扇門」的時候。

> **「補一扇門」跟「補一個入口」不是同一件事。**
> 入口已經有了,我該補的只是讓 cmd 殼也走得到它,不是再走一次相同的路。
> 這跟本批主體修的病一模一樣,只是這次犯的人是我。

改成真正的梭之後:`CGC_MDL165` 15/15 · 撞名 18(回到基線)· 基線外 0;
`CGC_MDL157` GREEN 29/29(梭沒有釘死版號)。

## 七 · 又一次 LL334,而且這次救回了真東西

取版號前掃過所有活分支:**`CGC_MDL149_v0120` 已被 `claude/busy-bell-97sa4f` 佔走**,
而且他們的 v0120 **已經把 VDF 那條腿接上了**。

所以 v0121 **從他們的 v0120 長**,不是從我的 v0119 長。
先量過才敢這樣做:AST 比對頂層函式,v0120 是 v0119 的**嚴格超集**
(只多 `_vdfsys` / `vdf_system`),從他們那裡長不會丟我的東西;
反過來從 v0119 長,他們那條 VDF 腿會在尾版律下整個消失。

**這是 LL334 第三次兌現,而且是第一次「從對方的基底長」救回別人的工。**

## 八 · 沒做的,以及為什麼(L87)

* **沒有建立 `VAP_SystemManager`** —— 那是一支新引擎(要四庫、九域燈、七處自審、自測門),
  是另一批的事。這一批把**位子**留好、把**缺席**誠實報出來,不假裝有。
* **沒有在根目錄開 `VIA_CentralGovernanceConsole.py`** —— 那個名字歸 b514 家族(見第一節)。
  要把活的正主改叫那個名字,是**改名+改擁有者**,得操作員一句話。
* **沒有碰任何 `.ps1`**(L70)。短令 `via-vcgc` 在 Register 裡本來就有,這一批只補梭。

## 九 · 收

| 檔 | 是什麼 |
|---|---|
| `supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0121.py` | 三家一把尺 + VAP 補位 + ㉔㉖ 改不變量 · **二十八檢** |
| `bin/via-vcgc.cmd` | 那扇門(LL199 缺的第四面) |
| `supportive modules/registry/CGC_MDL064_SelftestGrid_v0436.py` | 站敘述跟上二十八檢 |

> **LL341:「東西太多」通常不是檔案太多,是同一個判準被抄了太多份。**
> 解法不是再開一個總表去管它們,是把那幾份抄本收回同一把尺 ——
> 再開一個總表,就是第 N+1 份抄本。

> **LL342:一盞剛好綠著的燈,和一盞對的燈,看起來一模一樣。**
> 斷言裡寫「這個東西一定要在」的檢,在它不在的樹上永遠紅、在它在的樹上永遠綠
> —— 兩邊都沒有量到規格。要分兩態各驗各的,而且把**現在是哪一態**印出來。
