# VIA 交接 · 2026-11-26(容器;未在主機實跑的都標明)

依 CLAUDE.md 第六章四組稽核寫,每項都附 PR / 提交 / 回傳碼。沒有證據的寫 UNVERIFIED。
下一個 AI 接手的順序:
1. 先讀本檔與 `docs/handoff/daily/VIA_DailyChecklist_latest.md`。今天的新教訓是 LL-20261126-01~09。
2. 跑 token 卡 → `handoff check`。
3. 看 #758 有沒有合併。
4. 等操作員貼回桌機 `vdfcheck` 的輸出。

## 第一組 · 實質成果與對齊

| PR | 內容 | 證據 |
| --- | --- | --- |
| #751 已合併(main b28136a) | VCGC 系統庫 syscat(DuckDB)+ VTK 副本。`CGC_MDL228_VIADBManager` 走到 v0107:<br>· 號照「檔自己那一列」對,ENV / 政策列不搶檔號<br>· UI token 讀 registry 正本 | Codex 四輪,最後一輪無發現;CI 全綠;自測 8/8 ×3 |
| #756 已合併(main 55700a6) | VCGC 收尾(容器):<br>· `SUP_MDL866` v0111(檔面寫 VERBS,主控台省 Token 門轉綠)<br>· registry-sync<br>· 中央發號 +125<br>· 44 個舊紅交接案重跑:6 綠、38 紅 | 編號稽核 遺失 0 · 改身分 0 · 重號 0 · XCODE 0 · DUPREG 0 · IMMUT 0;`test --quick` 18 站(綠 16 · 黃 1 · 紅 1);總覽頁 Playwright 0 錯 |
| #757 已合併(main cfdd284) | `pr_guard.py` ①:退役夾「原樣搬回」(同 PR 刪退役副本、位元相同)降成黃;內容改過、或退役夾沒有的舊號照舊紅 | 自測 11/11 ×3;ReworkGuard v0104 自測照過 |
| **#758 開著**(分支 `claude/eloquent-rubin-q01657`) | VDF 輸出驗證的容器部分,見下方清單 | 見下方「證據」 |

#758 的內容:
- 搬回 9 支被誤退役的前版:ENG059 v0101–v0103、ENG075 v0100 / v0103–v0105、ENG100 v0100–v0101。
- ENG066 v0105:只修自測量法。
- 中央發號 +523。
- 總控頁重產。
- HostBoot v0104 新動詞 `vdfcheck`。

#758 的證據:
- VDF `test`:紅(失敗 2)→ 黃(失敗 0 · NODATA 4,容器沒有庫)。
- 各自測連過三次。
- `vdfcheck` 桌機模擬跑通,59 秒。
- 合約測試 20/20。

三本尾版冊與衍生產物:
- 今天沒有改 `LogicArchitecture` / `Policy_Laws` / `ToolRoster` 三本冊。對齊狀態沿用 11-25 的稽核:OUT_OF_SYNC,這次沒有重驗,所以是 UNVERIFIED。
- `graphify-out/graph.json`、`graphify-out/wiki/index.md`、`VIA_Database_Topology_Index.md`:容器沒有 graphify,倉裡也沒有這些檔 → **UNVERIFIED**。要等桌機備份的 G1 閘產出。

省 Token:
- 全程用 token 卡、`read`、`slice`、`chain`。
- 批次測試走 `CGC_MDL134_ParallelLanes`。
- 沒有碰 `via_database`。
- 寫入交接的收據只有結構和計數;`DB_STATUS_MATRIX` 含實際資料列,不收。

## 第二組 · 今天的錯誤與修補

完整的 9 條在教訓帳 LL-20261126-01~09。重點如下:

| 錯誤 | 根因 | 修補 · 以後怎麼擋 |
| --- | --- | --- |
| VDF test 紅:ENG059 FileNotFoundError | 11-23 prune 把用 `CHAIN_VERSIONS` + `'%s_v%s'` 拼檔名載入的前版搬走;11-24 還原只掃字面檔名 | 原樣搬回 + `RESTORED_20261126_vdf.json`;守門 #757。prune 前後每個家族尾版都要實際 import 加 `--selftest` |
| 主控台所有動詞 rc 2「缺 brief」 | 省 Token 門靠字串比對;#747 帶進的 `SUP_MDL866` v0110 薄尾沒寫 `--brief` | v0111 檔面寫 VERBS;受閘工具出薄尾必寫動詞表 |
| 44 案重跑太慢 | 單道序列 | 改走 MDL134 Supervisor 3 道;超過 5 案一律並行 |
| `test --quick` 逾時留下孤兒子行程、自測改寫已追蹤報告 | 逾時沒有收整棵行程樹 | 手動清理加 `git checkout`;**OPEN**,待 VCGC 出新版 |
| #758 Windows UAT 紅 | 搬回改了總控頁的計數 | 用管理器尾版重產;搬移退役檔後跑總控頁合約測試 |
| 差點 `git push -f` | 誤以為要強推 | 一律快轉推送,先用 `merge-base --is-ancestor` 確認 |

## 第三組 · 蟲攻擊 / 九頭龍

- **公開介面**:
  - 今天的新尾版都帶 `__getattr__` 轉接,並明寫必備 API。
  - 搬回的檔位元原樣。
  - `read` 卡 TAILAPI 0 · COMPILE 0。
- **雙橋**:
  - 新檔第 3 行都有加速器標記,執行時 `VIA_ACCEL is not None` 自測都過。
  - ENG066 v0105 另帶網路橋。
  - VDF 加速器 117/117、網路 9/9、缺橋 0。
- **繞道直連 `via_database`**:新程式沒有。`vdfcheck` 只叫 VDF 管理器自己的動詞。
- **靜默失敗**:
  - `vdfcheck` 收據缺件 → rc ≥ 2,不冒充綠。
  - `test --quick` 的 MDL230 逾時照實記紅。
  - SDD 自測被 1500 秒截斷,照實記「未出總結」。
- **還沒有權限修的**:VDF `db verify` 只收 VCGC 的入口標記(LL-20261126-09)。

## 第四組 · 未解決與交接

**P0 阻斷**
- 交接閘紅:38 個舊交接案仍紅,名單在 #756 PR 描述。
- `handoff daily` rc 1。
- `sdd lock` 因此拒寫 VCGC-WKF007 / 009 / 010 等 5 個工作流的重驗鎖。

**P1 高風險**
- VDF 真正的輸出驗證還沒在主機跑。等操作員貼回 `vdfcheck` 輸出,收據在 `intake/fastrun-…`。
- ENG242 v0106 的湖重跑也還沒在主機跑。指令照 11-26 的 lake 一行。
- 待操作員裁定:
  - US_MACRO 來源重複列。
  - 測試庫和 `_repo_` 副本被收進湖。
  - TWIndex 日資料只到 2019-06-28。

**P2 優化**
- `test --quick` 逾時收整棵樹、MDL230 自測 690 秒,都待 VCGC 出新版。
- VDF 自己的工作流冊漂移,要 `sync --apply`,需操作員批准。
- 舊遠端分支 83 條要操作員在網頁上刪,代理不讓 AI 刪。

**桌機一行指令**(都先在倉根貼;取 HostBoot 的方式同 11-26 的 lake / vdfcheck,`$B='claude/eloquent-rubin-q01657'`)
- VDF 輸出驗證:最後一段是 `… --repo $R vdfcheck --branch $B --push`
- 備份 + Graphify:最後一段是 `… --repo $R bak --push`
  - 會跑 VIA_DailyBackup 尾版 `full`:三閘並行 G1 Graphify + 三冊 · G2 環境 · G3 工具來源 → Fail-Closed → 備份。
  - 照第五章已定案:Q1 A · Q2 Mode C · Q3 本機隔離區 · Q4 5 份輪替 · Q5 Fail-Closed · Q6 純本地。

### 標準跨 AI 交接狀態卡

- `[整體健康度]` **RED**:交接閘 38 案紅;主機未實跑 VDF 輸出驗證與備份。
- `[最新基準點]` main @ cfdd284(#757);工作分支 `claude/eloquent-rubin-q01657` @ #758 頭。
- `[今日已閉環]`
  1. #751 syscat v0107(Codex 四輪 0 發現)
  2. #756 主控台省 Token 門修復 + 發號稽核六項 0
  3. #757 守門原樣搬回例外
- `[明日第一動]` 看 #758 是否已合併;接著判讀操作員貼回的 `vdfcheck` 收據。收據在 `intake/fastrun-*` 的 `vdfcheck_DB_CHECK_latest.json`。
