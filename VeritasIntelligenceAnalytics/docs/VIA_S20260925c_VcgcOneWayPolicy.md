# 2026-09-25c · 唯一入口與單向

操作員令：VCGC 為唯一入口。引擎、工具、子系統政策與 GitHub 的自動註冊、自動編碼都在 VCGC。所有 AI 禁止擅自讀取任何指令或引擎，除非經過 VCGC。VCGC 保留 GitHub 上傳的 PR 與子系統。子系統要有 System Manager 才得單向進入下方。REGEX SSOT 與同義字設雙向交互驗證。VRN / VDF 是 VCGC 下一層。VDF 資訊可供給 VRN。VDF 往下先開 QUANTGUARD 與 VATETF：產出單向向下，規範檢查雙向。

這一頁只把令寫進冊。沒改 `CGC_MDL149`。編號仍只能走它的 `registry-sync`：預設只列，`--apply` 才寫。這一頁不是第二扇門（L101）。

## 已在冊上，不另造

| 冊 | 怎麼用 |
| --- | --- |
| L20 | VCGC 是唯一對接口。正主尾版 `CGC_MDL149_VeritasCentralGovernanceConsole_v0130.py` |
| L101 · 批686 | 一個名字一扇門。往下只走 `SUBSYS_PORT`：VRN、VDF、VAP 各報各的。沒有 System Manager = ABSENT，不是壞掉，也不補一顆 |
| 批515 | VATETF 是應用端，只讀 VDF 擷取庫，不是入口 |
| 批728 | 正則與同義字的雙向檢查已經是 VCGC 的 `ssot` 門：委派正主，本台不重寫一條正則 |
| registry-sync | 引擎、工具、子系統的自動註冊與自動編碼的唯一寫入口 |

## 本令的走向

入口只有下行。沒有對接口，下方不開。

```
VCGC
  ↓ 要有 System Manager
  VRN ← VDF 可以把擷取結果供過來（資料，不是第二入口）
  VDF
    ↓ 產出單向
    QUANTGUARD   VDF_ENG086_QuantGuardOneBridge_v0101.py
    VATETF       應用端，只讀 VDF
```

雙向只用在檢查，不用在進入：

- REGEX SSOT、同義字：冊與產物互相對。對不上就停，不另寫一條。
- QUANTGUARD、VATETF 的規範檢查也是雙向：產出向下，核對回上。缺的日、缺的持股不記成 0。

GitHub 的 PR 留在 GitHub。VCGC 保留它們，不把某一個 PR 收成另一個入口。

## AI

要讀指令或引擎，先經過 VCGC。不經對接口就打開子系統下方，視同沒走這扇門。

## 還沒做的

- 沒把這一頁寫進政策庫。要上冊，走 `via-vcgc registry-sync` 列出來，再由操作員 `--apply`。
- 這台預覽沒載 VRN / VDF 對接口，所以那兩家是 ABSENT，下方不開。
- VATETF 引擎 `VIA_ActiveTWETF_AllInOne_v0410.py --mode run --live-issuer` 停在缺 pytz，庫沒寫成，每日台股持股不算齊。
