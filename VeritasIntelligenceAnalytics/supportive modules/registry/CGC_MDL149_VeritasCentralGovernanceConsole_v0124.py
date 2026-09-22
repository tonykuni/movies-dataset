#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL149_VeritasCentralGovernanceConsole v0123 — VCGC(批691B:那扇門再往下一層——工具與支援性模組盤點)
v0122→v0123(操作員令「這裡負責環境工具及 VCGC 對接子系統,並盤點支援性及所有工具模組」;
  **從主線 v0122 長**,不是從我自己的那一份 —— 主線 v0122 修了我 v0121 收尺時漏掉的 bridge 段,
  從我那一份長會把他們的修整個弄丟(LL334/LL343)):
  新增 `inventory` 動詞 —— **委派給 `CGC_MDL178`,不在這裡再寫一把尺**(LL341)。
  +㉙ 一檢:AST 釘住這件事 —— 本檔裡只准有委派,一旦有人把盤點/棘輪/撞號的實作抄進來就當場紅。
v0123→v0124(批698 開第三扇門):+SYNC-PORT 資料樞紐對接口(正主 CGC_MDL179_VcgcSyncHub)。
  批697 把樞紐做出來、collect() 也自測過,但沒掛上來——**一支沒掛在門上的引擎,
  對操作員而言等於不存在**(批647 的 VIA_HTML_UI 就是這樣)。這裡只開埠不搬實作:
  形狀逐字照 _invport()/tool_inventory(),+sync 動詞,+㉚ 一檢(釘法照 ㉙)。
  ㉚ 另外釘一件 ㉙ 沒釘的:**誠實態原封轉呈** —— 樞紐回 GATED/FIRST_RUN,
  本台就報 GATED/FIRST_RUN;壓成 GREEN 或 RED 就是在門上偷偷立第二把尺。廿九檢→三十檢。
  順手更正抬頭口誤:`--selftest` 抬頭印「二十六檢」而 [計] 印「二十八檢」,抬頭是舊的。
  `status` 刻意不動 —— 撞號那把尺要掃 30+ 條 refs,掛進 status 會讓每次看狀態都變慢。
v0121→v0122(側線 2026-09-21 e 併 main 批686b(PR #59);主線批號由併線的手指定 L25):主線把三家的段收成一把尺 `_subsys_section()`,
  但收尺時漏了側線 v0120 `vdf_system()` 回的 **bridge 段**(tails/accel/net/net_callers/…)與 mode、why 鏈;主線 ㉖ 自己就要 `bridge.tails` 是 int——
  在沒有 VDF 對接口的樹上走「缺席=ABSENT」那條路所以綠,對接口一在位就紅(本線併後實錄:二十八檢 OK 27 · FAIL 1;單元測試 T03 同紅)。
  修在同一把尺上:`_subsys_section()` 對**任何**家族只要 collect() 有 bridge 就回同形的 bridge 摘要(沒有的家族回 None),mode/why 鏈照舊補回;
  不另開第二個載入器、不改 ㉔㉖㉗㉘ 一個字;檢數不變(二十八檢)。其餘一字不動(v0121 留作版史,尾版律 L04)。
v0120→v0121(操作員令「VIA 東西太多,用一個中央治理台整合一切;已經有這個角色就合併;對接下方」):
  先量再寫——這個角色**已經存在**(本支就是),而 `VIA_CentralGovernanceConsole.py` 這個檔名
  已被 b514 家族件佔用(原名零觸碰,MANIFEST_b514.json md5 冊,擁有者 CGC_MDL150)。
  所以**不開新檔**(同名兩扇門=L101),而是把這一支補成真正的那一扇門。
  ① 收尺:批681 接 VRN、側線接 VDF,兩段是**逐字複製貼上、只換家族名**;再抄一份給 VAP 就是第三顆頭。
     新增 `[VIA:SUBSYS-PORT]` 區塊——`SUBSYS_PORT` 一家一列,`_subsys()` / `_subsys_section()` 一把尺。
     `_VRNSYS`/`_VDFSYS` 仍是**同一個 dict 物件**,`_via_vrnsys()`、批681 的 ㉔、側線的 ㉖ 一個字都不用改。
  ② 補位:VAP 那條腿接上(樹上尚無 VAP_SystemManager → **ABSENT 誠實**,不假裝有);
     新增 `subsystems()` 一次報三家,`audit` 收錄 vap_system 與 subsystems。
  ③ +㉗㉘ 兩檢:AST 釘住「三家一律委派同一把尺」(有人再抄一份載入器就當場紅)· 誠實四態正負控。
     二十六 → 二十八檢。
  沒做的(L87):沒有建立 VAP_SystemManager(那是一支新引擎,另一批);沒有動任何 .ps1(L70)。

CGC_MDL149_VeritasCentralGovernanceConsole v0120 — VCGC(側線 2026-09-21:VDF 子系統管理對接口上線;VIA 往下讀 VDF 也只走一扇門)
v0119→v0120(操作員令「將 session_01RLMQ… 關於 VDF 全數接過來 · 建立 VDF_SystemManager 與 VIA 對接 · VDF 所有引擎找出來 · 讀取 VIA 政策所有 PY 檔案一定要接加速器 ·
  所有 VDF 都要加裝網路工具」;側線 claude/busy-bell-97sa4f,主線批號由併線的手指定 L25):
  ① +_vdfsys()/vdf_system() 段:讀 functional modules/VDF/VDF_SystemManager 尾版的 collect()(九域燈:政策/邏輯/因子/參數/引擎/橋/工具/交接/紀錄 · 連結表 · 七處自審 · 橋律逐支量);
     status 多一行、一頁多一段(十四)、頁多一卡。對接口缺席 = ABSENT 誠實(缺件≠壞掉),**不退回舊路**(L05)。與 VRN 那扇門(批681)同一份契約。
     本台不另判 VDF 的燈:「所有 PY 接加速器 / 所有 VDF 加裝網路工具」由對接口 bridge 域按 CGC_MDL124 的尺逐支量,尾版少一支就是它的 RED;本台照抄。
  ② ENGINE_GLOBS +("functional modules/VDF", "*_v????.py"):VDF **根目錄**的尾版件(VDF_SystemManager · VDF_ENG045_OutputHub · vdf_input_matrix)以前不在受治理範圍——
     「VDF 所有引擎找出來」量出來就是這三支漏網(engine/ 另有 8 支無版號 .py,L04 尾版律外,尺照舊看不見,對接口 logic 域分開報)。入尺後 registry-sync --apply 才補號(唯一寫入口不變)。
  ③ +㉖ 檢:對接口在位時 vdf_system 段九盞燈、有連結、七處為七鍵、橋律量得出尾版數,且 VDF_SystemManager 是受治理家族;缺席時 ABSENT 而不是炸。二十五檢 → 二十六檢。主線批682B 同時取了 v0119(執行期境不進等式 ㉕),L25 改號:本線 v0120 疊在它上面,它的 ㉕ 原樣保留。

CGC_MDL149_VeritasCentralGovernanceConsole v0119 — VCGC(批682B:執行期境不進元件等式——⑬ 兩台機器互翻的根治;Z79 / PR #58 Codex P1)
v0118→v0119(批682B):live_components() 把 TOOLS_PLAN_latest.json(執行期產物,不入 git)列出的境標 runtime,
  不進 rows(⑬ 等式、audit 缺件表、registry-sync 新增/退役都看不到它),另列 runtime_rows 供查;
  覆寫鍵 VIA_TOOLS_PLAN_LATEST(同 ⑳ 來源閘的規矩:每個真機器來源都配覆寫鍵);+㉕ 合成檢(有沒有那份檔,活元件數一樣)。
  之前:工作站有 TOOLS_PLAN=虛境 (未路由:加速器通用件) 算活元件;容器沒有=退役;兩邊各 --apply 一次就互翻(批681/682/682B 三次)。
  已退役的 VIA-ENV-0001 留著不動:執行期境本來就不是樹上的元件。

CGC_MDL149_VeritasCentralGovernanceConsole v0118 — VCGC(批681:VRN 四庫讀取改經 VRN_SystemManager 下行對接口)
v0117→v0118(批681 操作員令「設立 VRN_SystemManager.py 上下銜接 VIA,管理子系統的政策/邏輯/因子/參數;以後讀取就從 VIA 往下透過 VRN_System 作為管理對接口;自適應、智慧化、上下資訊自動更新的連結」):
  ① logic()/factors() 不再各自 import ENG082 / SUP_MDL748——一律呼叫 VRN_SystemManager.read('logic'|'factor');回傳形狀不變(status/onepage/page 零改動),
     多一個 via 欄署名證明是經對接口讀的。對接口缺席 = ABSENT 誠實(缺件≠壞掉),**不退回舊路**(退回舊路=同一判準寫兩處=第二顆頭,L05)。
  ② +vrn_system() 段:讀對接口 collect()(六域燈 · 連結表 · 七處自審);status 多一行、一頁多一段(十三)、頁多一卡。
  ③ +㉔ 檢:對接口在位時 logic()/factors() 必須署名 VRN_SystemManager;對接口缺席時 logic()/factors()/vrn_system() 三者都 ABSENT 而不是炸。
  引擎面(六層鏈)的燈由對接口照抄鏈跑器再拆開講(缺件/缺料/其餘),本台不另判。

CGC_MDL149_VeritasCentralGovernanceConsole v0113 — VCGC(批568:⑨ 的第二個洩漏口,以及一道「以後不准再有第三個」的閘)
v0112→v0113(批568 操作員工作站實錄:⑨ 印的是 **BLOCKED_PANORAMA**,不是我本境修的 BLOCKED_UNITEST):
  我在批567 寫下 LL114「引擎有幾個資料來源,自測就要把**每一個**都關進沙盒」,然後**自己只關了一個**。
  `check()` 讀兩個真機器來源:① `rungate()`(批567 已關:VIA_RUNGATE_LATEST + VIA_RUNGATE_DIR)
  ② `REPORTS/panorama/PANORAMA_latest.json`——**寫死路徑、沒有覆寫鍵**,而且它會把 install 直接覆蓋成
  BLOCKED_PANORAMA。本境沒有 panorama 夾,那道閘是啞的,所以我看到的是 UNITEST;操作員機器上有一份
  未完成的全景報告,八個合成案例**全部**被覆蓋成 BLOCKED_PANORAMA。同一個檢、兩台機器、兩種紅法,
  而核可邏輯一行都沒錯。(我連自己查證時都再犯一次:`grep | head -5` 把 v0111/v0112 切掉,
  讓我一度以為新版沒有這道閘——批567 剛立的 L62 打自己的臉。)
  本版兩件:
  ① `PANORAMA_LATEST` 比照 RunGate 慣例加 `VIA_PANORAMA_LATEST` 覆寫鍵(生產預設路徑不變),⑨ 一併關進沙盒。
  ② 新增 ⑳ **來源閘**:用 AST 掃 `check()/rungate()/_rungate_merged()`,列出這條路真正讀的每一個
     `REPORTS / …` 磁碟來源,要求**每一個都配一個 VIA_* 覆寫鍵**,而且自測 ⑨ 區塊**每一個鍵都要指進暫存夾**。
     少一個就報紅並指名是哪一個——「底下還有一層」這件事,從此由機器講,不靠我記得。
  十九檢 → 二十檢。
CGC_MDL149_VeritasCentralGovernanceConsole v0112 — Veritas Central Governance Console(VCGC;批567 ⑨ 不再被機器狀態判成紅燈)
v0111→v0112(批567「自測時測字完成」同族:一個**看機器臉色**的檢,和一個被切掉的訊息一樣不誠實):
  ⑨ 安裝核可是**合成檢**——自測自己在暫存夾寫八份 RunGate 報告,用 VIA_RUNGATE_LATEST 指過去,
  驗「缺/單族/零站/零庫/壞值/未來/過期都 BLOCKED,雙族完整 GREEN 才 INSTALL_OK」。
  但 `_rungate_merged()`(批517 起)會另外掃**真機器**的 `VIA_Reports/rungate/RUNGATE_2*.json` 史,
  而且史**優先於**傳進來的那一份。於是只要機器上有一份 24h 內的真報告,合成的那八份就被蓋掉,
  ⑨ 當場紅。本境量到的正是這個:批566 跑 OneShot 留下 2.2 小時前一份 verdict=YELLOW 的真報告,
  ⑨ 印出「雙族=BLOCKED_UNITEST」——**核可邏輯一行沒變,紅燈是機器狀態換來的**(LL103 同族的判錯紅燈)。
  修法只動自測、**零生產邏輯變更**:⑨ 連 `VIA_RUNGATE_DIR` 一起指向暫存夾(引擎本來就吃這個覆寫鍵),
  讓史掃描也關進沙盒;跑完照原樣還原兩個鍵。合成檢就該只驗自己合成的東西。
CGC_MDL149_VeritasCentralGovernanceConsole v0111 — Veritas Central Governance Console(VCGC;批520 批號改讀政策庫,不再每批改常數)
v0110→v0111(批520):BATCH 不再寫死——讀 VIA_Policy_Laws_SSOT_v0100.json 的 batch(政策庫是批號正本;LL 每批為改一個常數就出新版=假版本);讀不到退 519。
CGC_MDL149_VeritasCentralGovernanceConsole v0110 — Veritas Central Governance Console(VCGC;批519 十二段 U/I 對接與工作流:中央自適應連結)
v0109→v0110(批519 操作員令「中央可以自適應式連結對接 U/I · WORKFLOW 圖可重整不同引擎 · 自動跳出實測真實結果 · VDF 資料庫分類歸納摘要」):
  讀 CGC_MDL153 WorkflowComposer 落的 UI_CONTRACT_latest.json(頁/擁有者/在不在/新鮮/再生令)+ WORKFLOW_latest.json(最新一跑)+ DB_SUMMARY_latest.json(庫分類燈)
  → 十二段 + 頁卡/頁段:頁在=連結(file://)、不在=ABSENT 誠實;工作流最新真跑逐節點;庫分類每類一燈;十九檢 +⑲。
CGC_MDL149_VeritasCentralGovernanceConsole v0109 — Veritas Central Governance Console(VCGC;批518 中央治理主控台 G17 循環判讀入十一段)
v0108→v0109(批518 操作員貼回 via-cgfamily:console RED=G17 3 個循環依賴 + 五 WARN):FAMILY_latest.json 的 console.cycles_reading(CGC_MDL150 v0103 cycles 動詞:
  URN→檔名→區)入十一段一行 + 頁段一行:活樹圈數才是債,退役/收容/存檔內互呼不算(L38);缺=ABSENT 誠實;十八檢 +⑱。
CGC_MDL149_VeritasCentralGovernanceConsole v0108 — Veritas Central Governance Console(VCGC;批517 安裝核可看兩族各自最新一跑)
v0107→v0108(批517 操作員實錄:via-rungate vdf GREEN(早上)+ via-rungate vrn GREEN(晚上),via-vcgc 仍 BLOCKED_UNITEST——
  rungate() 只讀 RUNGATE_latest.json(最後一跑只有 vrn)= 判錯的紅燈):改讀 RUNGATE_*.json 史,每個必驗族取 24h 內最新一筆(VIA_RUNGATE_DIR 可覆寫史夾);
  總燈=各族取用那筆的最壞;十七檢 +⑰。
v0106→v0107(批516 操作員令「除錯成功後才 VTMRA · TA-LIB 確認測試無誤」):+vtmra()(CGC_MDL152 VTMRA_latest.json:七成員態 + 判定;TA-Lib 態在內)
  於四段/頁卡/status;批 516;十六檢 +⑯。
v0105→v0106(批515 操作員令「VETF 改名為 VATETF;直接抓 VDF 擷取的資料庫來用,他是應用端;以 VIA 為中央管理全部 SSOT 化 唯一接觸口」):
  十段/頁標題 VRN / VDF / VATETF(舊名 VETF;契約 names 鍵);批 515;十五檢不變(結構判準)。
v0104→v0105(批514 操作員令「將中央管理系統不足的部分補上」):+十一段 中央治理家族(CGC_MDL150 FAMILY_latest.json:VIA-SYS-MGR-001 主控台 ·
  VIA-GOV-ENG-001 詞彙引擎 · VIA-SYS-MGR-003 下行控制 · VIA-SYS-ENG-003 檔案優先序 · 同名整併;五成員 md5 對冊 + 各自最新快照;誠實 ABSENT)於一頁/頁卡/status;
  RunGate 段帶 host.pythonhome_scrubbed(L32 母殼 PYTHONHOME 撤除存證);十五檢 +⑮。
v0103→v0104(批511 併線):並行線 v0102/v0103(INSTALL_OK 兩族同時在位、registry-sync 元件編號冊唯一寫入口、panorama 契約)+ 本線 批508 環境復原段
  (RECOVER_latest.json;MDL135 recover;律 L24)於二段/頁卡/status;政策庫冊聯集(L26–L29、LL15–LL18 來自並行線 panorama-v0103,orig_id 保留)。
v0101→v0102(批508 結案):① INSTALL_OK 強制 VDF+VRN 兩族同時在位、家族境/必要庫/自測站全綠且 24h 內；
  零站、SKIP、只跑一族都 BLOCKED_UNITEST。② VCGC 成為元件自動編號冊唯一寫入口：registry-sync 預設只列，
  --apply 才把尾版引擎/模組/類別/函數/功能/短令/工具套件/環境以穩定編號寫入 append-only SSOT。
  ③ 註冊稽核分開呈現「中央編號冊覆蓋」與「操作介面掛載」，不再用 ENG/MDL 編號片段模糊命中假裝已登。
v0100→v0101(批507 操作員問「多 AI 寫作要怎麼接手不掉球、格式如何、長久使用」):一頁交接 +〇 接手提示詞(docs/VIA_AI_Handover_Prompt_v*.md 尾版全文嵌入)
  +九 掉球清單(docs/VIA_DroppedBalls_*.md 尾版);格子 PYCODE/自指站標「特殊」不當缺;十二檢。
====================================================================
操作員令:「相關中央控管為 Veritas Central Governance Console,為此系統連接各模組引擎的唯一對接口,
控管 政策庫 · 邏輯庫 · 因子庫 · 資料庫 · VIA 引擎調度 · 多矩陣實測結果;不要丟失參數及指令;
所有引擎/模組/功能/工具/環境都要註冊;lesson-learned;環境統一測式無誤後才可核可安裝;
詳細 handover report 整合成同一頁 + 環境工具管理 + 自動編號註冊表。」(律 L20)
Zero-Hydra:本台**預設只讀**——各庫各冊各引擎的正主不變；唯一例外是明示
`registry-sync --apply` 原子寫中央元件編號冊，與 `page --publish` 發布同頁交接。
  政策庫  VIA_Policy_Laws_SSOT_v*.json(律+lessons)+ ENG082 policy_factors()(攤平入 via_policy_factors)
  邏輯庫  ENG082 LOGIC_latest.json(件/法/後端健康)+ sync_state(全庫同步對帳)
  因子庫  SUP_MDL748 policy_rows()(AllInOne + FDS 兩本冊)
  資料庫  VIA_DB_Table_SSOT(冊)+ DATAHOME_CATALOG_latest.json(家內庫/湖)
  引擎調度 CGC_MDL095 Deck 任務冊 + VIA_InputConsole_Spec 項 + CGC_MDL064 格子站 + Register-VIA-Commands 指令(含用法/參數)
  多矩陣  ENGINE_BUS_latest.json(五矩陣)+ RUNGATE_latest.json(環境統一測式)
  環境工具 TOOLS_PLAN_latest.json(MDL135 tools)
  環境復原 RECOVER_latest.json(MDL135 recover;律 L24 還原前次→順序裝→_M/_H 單獨隔離)
  註冊表  VIA_AutoCode_Registry(自動編號類別 current + 台帳尾)
  註冊稽核 尾版家族×中央元件編號冊；顯式操作介面(規格/Deck/格子/Register/Manager)另列缺口，不模糊命中
  安裝核可 L19:RunGate 24h 內 VDF+VRN 兩族完整 GREEN → INSTALL_OK;否則 BLOCKED_UNITEST
用法:python3 CGC_MDL149_VeritasCentralGovernanceConsole_v0102.py [status|page|onepage|audit|register-plan|registry-sync|check|matrix|inventory|sync] [--publish|--apply] | --selftest

  matrix(批598 操作員令「中央管理系統設一個管理啟動各子系統及引擎及設定參數的指令」):
    via-vcgc matrix                       全景:冊 × 啟動矩陣 × 引擎四態 × 修復候選 → 一頁 HTML
    via-vcgc matrix --family vdf          只看一個子系統
    via-vcgc matrix --ids tw_align,tw_need  **單獨啟動**點名的項(寫庫動詞只認這條路)
    via-vcgc matrix --engine CGC_MDL156   **單獨測**一支引擎的檢查邏輯
    via-vcgc matrix --apply               真跑(預設 PLAN:一個開關發動幾十支回補是地雷)
    via-vcgc matrix --no-tests            不測引擎(那一格會標成「沒量」,不冒充綠)
    via-vcgc matrix --full                引擎測試不用 fast(逾時放寬)
    via-vcgc matrix --json                另印 JSON
  rc:0 綠 · 1 紅 · 2 黃(有修復候選/缺件/沒量——**黃不是綠**)
  page/onepage 預設落 VIA_Reports/vcgc/(不入 git、不弄髒工作樹);--publish 才複製到 ui_support 頁與 docs/VIA_Handover_ONEPAGE.md + 倉根 VIA_HANDOVER_LATEST.md(我 commit 時的手)
律:零 CDN;零彈窗;零網路;預設只讀；只有 page --publish 與 registry-sync --apply 明示寫入；誠實 ABSENT(報告不在=講不在,不編)。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====


import ast
import html
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ROOT = VIA.parent
REPORTS = VIA / "VIA_Reports"
OUTDIR = REPORTS / "vcgc"
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]   # 批586:寫死會爛——v0114 上印著 v0113,一路印進每一份報告
def _batch_from_laws() -> int:
    """批520:批號正本=政策庫 batch(「批520」→ 520);讀不到退 519。"""
    try:
        _b = json.loads((HERE / "VIA_Policy_Laws_SSOT_v0100.json").read_text(encoding="utf-8")).get("batch") or ""
        return int(re.sub(r"\D", "", str(_b)) or 519)
    except Exception:
        return 519


BATCH = _batch_from_laws()
UNITEST_MAX_AGE_H = 24.0
INSTALL_REQUIRED_FAMILIES = ("vdf", "vrn")
COMPONENT_REGISTRY = HERE / "VIA_Component_Inventory_SSOT_v0100.json"


# ===== [VIA:TAILPICK-BRIDGE:v0100] 尾版取用正典橋(批590/591;正典 SUP_MDL751_VIATailPick)=====
# 本群原本的行為:_newest(dirp, pat)
# 批590 量過:CGC 族 32 份 `newest` 是 **13 個行為群**,不是同一件事(最大兩群參數順序相反、
# 兩支走 rglob、一支缺件回 pattern、一支按 mtime 排序)。所以正典把差異變成**明示選項**,
# 並逐群重放證零損失(15 種具名變體 × 6 組語料,90 組全同)。
# 這裡是**綁定**不是再定義一支 def:寫 def 的話能力庫裡這一家族還在,家族數不會掉(LL143)。
import importlib.util as _tp_ilu
from pathlib import Path as _tp_Path
_TP_MOD = None
_tp_p = _tp_Path(__file__).resolve()
while _tp_p.parent != _tp_p:
    _tp_hits = sorted((_tp_p / "supportive modules").glob("SUP_MDL751_VIATailPick_v*.py"))
    if _tp_hits:
        _tp_spec = _tp_ilu.spec_from_file_location("VIA_TAILPICK", _tp_hits[-1])
        _TP_MOD = _tp_ilu.module_from_spec(_tp_spec)
        _tp_spec.loader.exec_module(_TP_MOD)
        break
    _tp_p = _tp_p.parent
if _TP_MOD is None:      # 大聲壞掉:尾版取錯是無聲的錯(整條鏈指到舊引擎,沒人會發現)
    raise RuntimeError("[FAIL] 尾版取用正典缺席:supportive modules/SUP_MDL751_VIATailPick_v*.py")
_newest = _TP_MOD.bind(order="rp")
# ===== [VIA:TAILPICK-BRIDGE:END] =====


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# ===== [VIA:JSONIO-BRIDGE:v0100] JSON 讀寫正典橋(批592;正典 SUP_MDL752_VIAJsonIO)=====
# 本處原本的行為:utf-8-sig + is_file 守衛 · try/except→None
# 批592 量過:活樹尾版 168 支只有 **20 處**定義 / **17 個行為群**(debt 報的 83/35 檔含版本史,LL142)。
# 差異軸:讀=編碼 utf-8-sig vs utf-8(**活的不一致**:帶 BOM 的檔有些引擎讀得到有些讀不到)、
# 缺檔與壞檔**是兩個旋鈕**(合成一個 default 會把壞檔說成不存在=假的零,LL138);
# 寫=原子寫 / indent / 尾換行 / default=str ——**indent 與尾換行是產出契約,不得統一**。
# 所以正典把差異變成明示選項,並逐群重放證零損失(讀 9 種 × 4 語料全同;寫 4 種**逐位元組相同**)。
# 這裡是**綁定**不是再定義一支 def(寫 def 家族數不會掉=等於沒併,LL143)。
import importlib.util as _js_ilu
from pathlib import Path as _js_Path
_JS_MOD = None
_js_p = _js_Path(__file__).resolve()
while _js_p.parent != _js_p:
    _js_hits = sorted((_js_p / "supportive modules").glob("SUP_MDL752_VIAJsonIO_v*.py"))
    if _js_hits:
        _js_spec = _js_ilu.spec_from_file_location("VIA_JSONIO", _js_hits[-1])
        _JS_MOD = _js_ilu.module_from_spec(_js_spec)
        _js_spec.loader.exec_module(_JS_MOD)
        break
    _js_p = _js_p.parent
if _JS_MOD is None:      # 大聲壞掉:讀錯編碼/寫錯 indent 都是無聲的錯
    raise RuntimeError("[FAIL] JSON 讀寫正典缺席:supportive modules/SUP_MDL752_VIAJsonIO_v*.py")
_json = _JS_MOD.bind_read()
# ===== [VIA:JSONIO-BRIDGE:END] =====


def _age_h(ts: str) -> float | None:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return (datetime.now() - datetime.strptime(str(ts)[:19], fmt)).total_seconds() / 3600.0
        except Exception:
            pass
    return None


def _nat(value) -> int:
    """報告計數的 fail-closed 轉換；壞值/負值不得因相等而假綠。"""
    try:
        value = int(value)
        return value if value >= 0 else -1
    except (TypeError, ValueError):
        return -1


# ────────────────────────── 讀各庫各冊(只讀) ──────────────────────────
def laws() -> dict:
    j = _json(_newest(HERE, "VIA_Policy_Laws_SSOT_v*.json"))
    return {"state": "OK" if j else "ABSENT", "laws": (j or {}).get("laws", []), "lessons": (j or {}).get("lessons", []), "src": (j or {}).get("batch", "")}


def ledger() -> dict:
    j = _json(HERE / "VIA_AutoCode_Registry_v0100.json")
    if not j:
        return {"state": "ABSENT"}
    L = j.get("ledger", [])
    return {"state": "OK", "n": len(L), "tail": L[-8:], "categories": {k: v.get("current") for k, v in (j.get("categories") or {}).items()},
            "components": len(j.get("components") or {}), "updated_at": j.get("updated_at")}


def deck_tasks() -> dict:
    p = _newest(HERE, "CGC_MDL095_DeckServer_v*.py")
    if not p:
        return {"state": "ABSENT", "tasks": {}}
    try:
        m = _load("vcgc_deck", p)
        t = m.task_registry()
        return {"state": "OK", "src": p.name, "tasks": {k: {"zh": v.get("zh", ""), "argv": [str(x) for x in v.get("argv", [])], "net": bool(v.get("net"))} for k, v in t.items()}}
    except Exception as exc:
        return {"state": f"BROKEN {type(exc).__name__}", "tasks": {}}


def spec_items() -> dict:
    j = _json(HERE / "VIA_InputConsole_Spec_v0100.json")
    if not j:
        return {"state": "ABSENT", "items": []}
    items = []

    def walk(o, fam):
        if isinstance(o, dict):
            if "id" in o and ("engine" in o or "state" in o):
                e = o.get("engine") or {}
                items.append({"family": fam, "id": o["id"], "zh": o.get("zh", ""), "glob": e.get("glob", ""), "dir": e.get("dir", ""), "verb": e.get("verb", []),
                              "params": o.get("params", []), "net": bool(o.get("net")), "state": o.get("state", "")})
            for k, v in o.items():
                walk(v, k if k in ("vdf", "vrn", "vap") else fam)
        elif isinstance(o, list):
            for x in o:
                walk(x, fam)
    walk(j.get("families", {}), "")
    return {"state": "OK", "items": items, "param_kinds": list((j.get("param_kinds") or {}).keys())}


def grid_stations() -> dict:
    p = _newest(HERE, "CGC_MDL064_SelftestGrid_v*.py")
    if not p:
        return {"state": "ABSENT", "stations": []}
    try:
        m = _load("vcgc_grid", p)
        B = m.battery(False)
        st = []
        for b in B:
            pth = str(b["path"]) if b.get("path") else ""
            special = (pth in ("", "PYCODE")) or ("自指" in b["name"])
            st.append({"name": b["name"], "path": pth, "present": ("特殊" if special else (Path(pth).is_file())), "args": b.get("args", [])})
        return {"state": "OK", "src": p.name, "stations": st}
    except Exception as exc:
        return {"state": f"BROKEN {type(exc).__name__}", "stations": []}


def register_cmds() -> dict:
    p = _newest(VIA, "Register-VIA-Commands-v*.ps1")
    if not p:
        return {"state": "ABSENT", "cmds": []}
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    cmds, aliases = [], {}
    for i, ln in enumerate(lines):
        m = re.match(r"^function global:(via-[A-Za-z0-9\-]+)", ln)
        if m:
            name = m.group(1)
            usage = ""
            for j in range(i - 1, max(-1, i - 8), -1):
                if lines[j].startswith("#") and name in lines[j]:
                    usage = lines[j].lstrip("# ").strip()
                    break
            cmds.append({"cmd": name, "usage": usage[:220], "line": i + 1})
        m2 = re.match(r"^Set-Alias -Name (\S+) -Value (via-[A-Za-z0-9\-]+)", ln)
        if m2:
            aliases.setdefault(m2.group(2), []).append(m2.group(1))
    for c in cmds:
        c["aliases"] = aliases.get(c["cmd"], [])
    return {"state": "OK", "src": p.name, "cmds": cmds}


def manager_names() -> dict:
    p = _newest(VIA, "VIA_SYSTEM_MANAGER_v*.py")
    if not p:
        return {"state": "ABSENT", "tasks": {}, "engines": {}}
    s = p.read_text(encoding="utf-8", errors="replace")

    def block(key):
        m = re.search(key + r"\s*=\s*\{(.*?)\n\}", s, flags=re.S)
        return dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', m.group(1))) if m else {}
    return {"state": "OK", "src": p.name, "tasks": block("TASK_FORMAL_NAMES"), "engines": block("ENGINE_FORMAL_NAMES")}


def db_sheet() -> dict:
    j = _json(HERE / "VIA_DB_Table_SSOT_v0100.json")
    if not j:
        return {"state": "ABSENT"}
    t = j.get("tables", [])
    return {"state": "OK", "n": len(t), "all_home": sum(1 for x in t if x.get("db_scope") == "all_home"), "batch": j.get("batch", ""), "dbs": sorted({x.get("db", "") for x in t})}


def datahome() -> dict:
    j = _json(REPORTS / "datahome" / "DATAHOME_CATALOG_latest.json")
    if not j:
        return {"state": "ABSENT", "why": "VIA_Reports/datahome/DATAHOME_CATALOG_latest.json 不在(via-datahome catalog)"}
    return {"state": "OK", "home": j.get("home", ""), "dbs": len(j.get("by_name") or {}), "tables": len(j.get("by_table") or {}), "lakes": len(j.get("lake") or []), "ts": j.get("ts", "")}


# ===== [VIA:TOOL-INVENTORY-PORT:v0100] 工具與支援性模組盤點口(批691B)=====
#
# 這裡**只有一扇門,沒有第二把尺**。盤點/棘輪/撞號的實作全在 `CGC_MDL178`;
# 中央治理台做的事情只有兩件:解析它的尾版、把它的話原樣端上來。
# 批686 剛立過這條律(LL341:「東西太多」是同一個判準被抄了太多份),
# 而 LL339 說自己剛立的律最先違反的人通常是自己 —— 所以 ㉙ 用 AST 釘住它。

_INVPORT = {"mod": None, "why": ""}
_INVPORT_GLOB = "CGC_MDL178_ToolInventoryRatchet_v*.py"


def _invport():
    """工具盤點引擎尾版;缺席=None + 因由(缺件≠壞掉,也不准在這裡退回舊路自己算)。"""
    if _INVPORT["mod"] is not None or _INVPORT["why"]:
        return _INVPORT["mod"]
    p = _newest(HERE, _INVPORT_GLOB)
    if not p:
        _INVPORT["why"] = f"supportive modules/registry/{_INVPORT_GLOB} 缺"
        return None
    try:
        _INVPORT["mod"] = _load("vcgc_toolinv", p)
    except Exception as exc:
        _INVPORT["why"] = f"BROKEN {type(exc).__name__}:{str(exc)[:60]}"
    return _INVPORT["mod"]


def tool_inventory() -> dict:
    """VIA 往下的第二扇門:工具與支援性模組的三把尺,一次報。**三欄各自報,永不相加**(LL327)。"""
    m = _invport()
    if m is None:
        return {"state": "ABSENT", "why": _INVPORT["why"] or "CGC_MDL178 缺",
                "src": "", "盤點": {}, "棘輪": {}, "撞號": {}}
    try:
        inv, rat, race, sh = m.inventory(), m.ratchet(), m.version_race(), m.shuttles()
    except Exception as exc:
        return {"state": "BROKEN", "why": f"{type(exc).__name__}:{str(exc)[:80]}",
                "src": getattr(m, "__file__", ""), "盤點": {}, "棘輪": {}, "撞號": {}}
    return {
        "state": "RED" if rat.get("regress") else ("NODATA" if rat.get("state") == "NODATA" else "GREEN"),
        "why": "", "src": Path(getattr(m, "__file__", "")).name,
        "盤點": {"模組": inv["modules"]["n"], "短令": inv["tools"]["n"],
                 "缺": {k: len(v) for k, v in inv["modules"]["missing"].items()},
                 # 「無同名 .cmd」(寬)與「缺真梭」(嚴)是兩個問題,**分兩欄**:
                 # 共用一個「缺梭」就會讓 141 和 154 同時出現在同一頁上(MDL178 ⑮ 釘死恆等式)
                 "無同名cmd": len(inv["tools"]["missing"]["梭"]),
                 "缺真梭": (None if sh.get("state") == "NODATA" else sh["tally"]["缺真梭"]),
                 "真梭": sh.get("n_shuttle"), "撞名": len(sh.get("撞名") or []),
                 "非短令另欄": inv["other_kinds"]["n"]},
        "棘輪": {"態": rat.get("state"), "存證": rat.get("runs"), "最新": rat.get("latest"),
                 "計": rat.get("tally"), "退步": [r["station"][:44] for r in rat.get("regress", [])]},
        "撞號": {"態": race.get("state"), "活線": race.get("n_refs"), "計": race.get("tally"),
                 "本線涉入": [r["版號"] for r in race.get("mine", [])]},
    }


# ===== [VIA:SYNC-PORT:v0100] 資料樞紐對接口(批698;正主 CGC_MDL179_VcgcSyncHub)=====
#   批697 把樞紐做出來了,collect() 契約也自測過,但當時沒掛上來——一支沒掛在門上的引擎,
#   對操作員而言等於不存在(批647 的 VIA_HTML_UI 就是這樣:在樹上、冊上沒有、沒有梭)。
#   這裡**只開埠、不搬實作**:形狀逐字照 _invport()/tool_inventory(),
#   所以 ㉚ 那條 AST 釘子跟 ㉙ 是同一種釘法(LL341;LL339 說自己剛立的律最先違反的人通常是自己)。
_SYNCPORT = {"mod": None, "why": ""}
_SYNCPORT_GLOB = "CGC_MDL179_VcgcSyncHub_v*.py"


def _syncport():
    """資料樞紐引擎尾版;缺席=None + 因由(缺件≠壞掉,也不准在這裡自己算一份對帳)。"""
    if _SYNCPORT["mod"] is not None or _SYNCPORT["why"]:
        return _SYNCPORT["mod"]
    p = _newest(HERE, _SYNCPORT_GLOB)
    if not p:
        _SYNCPORT["why"] = f"supportive modules/registry/{_SYNCPORT_GLOB} 缺"
        return None
    try:
        _SYNCPORT["mod"] = _load("vcgc_synchub", p)
    except Exception as exc:
        _SYNCPORT["why"] = f"BROKEN {type(exc).__name__}:{str(exc)[:60]}"
    return _SYNCPORT["mod"]


def sync_hub() -> dict:
    """VIA 往下的第三扇門:端點 × 面的對帳態,一次報。

    **原樣端上來,不重算**:樞紐是唯讀對帳層(零搬移、零寫入對端),
    它的誠實態(GREEN/RED/NODATA/ABSENT/GATED/SKIP/FIRST_RUN)直接轉呈,
    本台不把任何一態改寫成別的(改寫就是第二把尺)。
    """
    m = _syncport()
    if m is None:
        return {"state": "ABSENT", "why": _SYNCPORT["why"] or "CGC_MDL179 缺",
                "src": "", "端點": {}, "燈": {}}
    try:
        c = m.collect()
    except Exception as exc:                      # collect() 契約說永不拋;真拋了也不准炸這台
        return {"state": "BROKEN", "why": f"{type(exc).__name__}:{str(exc)[:80]}",
                "src": getattr(m, "__file__", ""), "端點": {}, "燈": {}}
    return {"state": c.get("state", "NODATA"), "why": "", "rc": c.get("rc"),
            "src": Path(getattr(m, "__file__", "")).name,
            "模式": c.get("mode", ""), "端點": c.get("link_counts", {}),
            "燈": c.get("lamps", {}), "橋": c.get("bridge", {}),
            "委派因由": c.get("why", {})}


# ===== [VIA:SUBSYS-PORT:v0100] 子系統管理對接口(批686:三家一把尺)=====
#   批681 接 VRN、側線接 VDF——兩段是**逐字複製貼上、只換家族名**。
#   每多一家就多抄一份二十行,而那正是「VIA 東西太多」的樣態(L30 一個出處 / Zero-Hydra)。
#   這裡把它收成一把尺:家族只是 SUBSYS_PORT 上的一列,第四家不必再抄一次。
#   `_VRNSYS` / `_VDFSYS` 仍是**同一個 dict 物件**,所以 `_via_vrnsys()`、
#   批681 的 ㉔ 與側線的 ㉖ 一個字都不用改 —— 收尺不是改行為。
SUBSYS_PORT = {
    "VRN": {"dir": ("functional modules", "VRN"), "glob": "VRN_SystemManager_v*.py"},
    "VDF": {"dir": ("functional modules", "VDF"), "glob": "VDF_SystemManager_v*.py"},
    "VAP": {"dir": ("functional modules", "VAP"), "glob": "VAP_SystemManager_v*.py"},
}
_VRNSYS = {"mod": None, "why": ""}
_VDFSYS = {"mod": None, "why": ""}
_VAPSYS = {"mod": None, "why": ""}
_SUBSYS_STATE = {"VRN": _VRNSYS, "VDF": _VDFSYS, "VAP": _VAPSYS}


def _subsys(fam: str):
    """家族的子系統管理對接口尾版;缺席=None 而且把因由留在該家族的狀態格
    (缺件≠壞掉;**不退回舊路**——退回舊路=同一判準寫兩處=第二顆頭)。"""
    st = _SUBSYS_STATE.get(fam)
    if st is None:
        return None
    if st["mod"] is not None or st["why"]:
        return st["mod"]
    spec = SUBSYS_PORT[fam]
    p = _newest(VIA.joinpath(*spec["dir"]), spec["glob"])
    if not p:
        st["why"] = "%s/%s 缺" % ("/".join(spec["dir"]), spec["glob"])
        return None
    try:
        st["mod"] = _load("vcgc_%ssys" % fam.lower(), p)
    except Exception as exc:
        st["why"] = f"BROKEN {type(exc).__name__}:{str(exc)[:60]}"
    return st["mod"]


def _subsys_section(fam: str) -> dict:
    """一家的子系統管理段——對接口 collect();不寫任何檔。三家共用這一段。"""
    m = _subsys(fam)
    if m is None:
        return {"state": "ABSENT", "why": _SUBSYS_STATE[fam]["why"] or f"{fam}_SystemManager 缺"}
    try:
        s = m.collect()
        br = s.get("bridge") if isinstance(s.get("bridge"), dict) else None      # v0122:有橋律的家族(VDF)回同形摘要;沒有的回 None
        bridge = None if br is None else {"tails": br.get("tails"), "accel": (br.get("accel") or {}).get("has"), "net": (br.get("net") or {}).get("has"),
                                          "net_callers": (br.get("net") or {}).get("callers"), "accel_missing": (br.get("accel") or {}).get("missing"),
                                          "net_callers_missing": (br.get("net") or {}).get("callers_missing"), "ruler": br.get("ruler")}
        return {"state": s.get("rc_name"), "rc": s.get("rc"), "src": s.get("me"), "ts": s.get("ts"), "mode": s.get("mode"),
                "lamps": s.get("lamps"), "links": len(s.get("links") or []),
                "link_counts": s.get("link_counts"), "seven": (s.get("upstream") or {}).get("seven"),
                "seven_done": (s.get("upstream") or {}).get("done"), "bridge": bridge,
                "why": (s.get("logic") or {}).get("why") or (s.get("tool") or {}).get("why") or (s.get("handover") or {}).get("why", "")}
    except Exception as exc:
        return {"state": f"BROKEN {type(exc).__name__}:{str(exc)[:60]}"}


def subsystems() -> dict:
    """VIA 往下的**那一扇門**:三家對接口一次報,誠實四態各自說,不混成一個數字(LL327)。
    想加第四家,加 SUBSYS_PORT 一列即可——不必再抄一份載入器。"""
    out = {}
    for fam in SUBSYS_PORT:
        sec = _subsys_section(fam)
        mod = _subsys(fam)
        out[fam] = {"state": sec.get("state") or "ABSENT", "why": sec.get("why", ""),
                    "engine": (getattr(mod, "__file__", "") or "").replace("\\", "/").split("/")[-1],
                    "lamps": sec.get("lamps"), "links": sec.get("links")}
    live = [f for f, v in out.items() if v["engine"]]
    return {"families": out, "n": len(out), "live": len(live), "live_names": live}


def _vrnsys():
    """批681 的門;批686 起實作收在 _subsys('VRN')——同一把尺,形狀與行為不變。"""
    return _subsys("VRN")


def _via_vrnsys(domain: str) -> dict:
    m = _vrnsys()
    if m is None:
        return {"state": "ABSENT", "why": _VRNSYS["why"] or "VRN_SystemManager 缺", "via": None}
    try:
        return m.read(domain)
    except Exception as exc:
        return {"state": f"BROKEN {type(exc).__name__}:{str(exc)[:60]}", "via": getattr(m, "VIA_TAG", "?")}


def logic() -> dict:
    """批681 起:經 VRN_SystemManager.read('logic') 讀(回傳形狀不變;多一個 via 欄署名)。"""
    return _via_vrnsys("logic")


def factors() -> dict:
    """批681 起:經 VRN_SystemManager.read('factor') 讀。"""
    return _via_vrnsys("factor")


def vrn_system() -> dict:
    """批681:VRN 子系統管理段——六域燈 · 連結 · 七處自審(對接口 collect();不寫任何檔)。(批686 起與其餘家族共用 _subsys_section)"""
    return _subsys_section("VRN")



def _vdfsys():
    """側線的門;批686 起實作收在 _subsys('VDF')——同一把尺,形狀與行為不變。"""
    return _subsys("VDF")


def vdf_system() -> dict:
    """VDF 子系統管理段——九域燈 · 連結 · 七處自審 · 橋律逐支量(對接口 collect();不寫任何檔)。(批686 起與其餘家族共用 _subsys_section)"""
    return _subsys_section("VDF")


def _vapsys():
    """批686:VAP 子系統管理對接口(與 VRN/VDF 同一份契約)。樹上尚無 VAP_SystemManager → ABSENT 誠實。"""
    return _subsys("VAP")


def vap_system() -> dict:
    """批686:VAP 子系統管理段——與 VRN/VDF 共用 _subsys_section;對接口缺席=ABSENT,不假裝有。"""
    return _subsys_section("VAP")


def tools_plan() -> dict:
    j = _json(REPORTS / "env_governance" / "TOOLS_PLAN_latest.json")
    if not j:
        return {"state": "ABSENT", "why": "TOOLS_PLAN_latest.json 不在(via-envtools)"}
    return {"state": j.get("state", "?"), "ts": j.get("ts"), "counts": j.get("counts", {}), "risk": j.get("risk_counts", {}), "stages": len(j.get("stages", [])),
            "unrouted": len(j.get("unrouted", [])), "hold": len(j.get("whitelist_hold", [])), "envs": [(e.get("name"), e.get("state")) for e in j.get("envs", [])][:24]}


def recover_plan() -> dict:
    """批508 律 L24:環境復原計畫(MDL135 recover;plan 唯讀;--execute --approve 才跑)。"""
    j = _json(REPORTS / "env_governance" / "RECOVER_latest.json")
    if not j:
        return {"state": "ABSENT", "why": "RECOVER_latest.json 不在(via-envrecover;L24 安裝出問題先還原前次再順序裝)"}
    return {"state": j.get("state", "?"), "ts": j.get("ts"), "restore": (j.get("restore") or {}).get("mode"), "stages": len((j.get("install") or {}).get("stages") or []),
            "exclusive": (j.get("isolation") or {}).get("exclusive", []), "borrow_blocked": j.get("borrow_blocked", []),
            "order": [x.split("(")[0] for x in (j.get("order") or [])]}


def cg_family() -> dict:
    """批514:中央治理家族快照(CGC_MDL150 status 落 VIA_Reports/central_governance/FAMILY_latest.json;VIA_CGFAMILY_LATEST 可覆寫路徑)。"""
    p = Path(os.environ.get("VIA_CGFAMILY_LATEST") or (REPORTS / "central_governance" / "FAMILY_latest.json"))
    j = _json(p)
    if not j:
        return {"state": "ABSENT", "why": "FAMILY_latest.json 不在(via-cgfamily 跑一次即有;五成員經 CGC_MDL150 擁有者起跑,預設 dry-run)"}
    ff = j.get("files") or {}
    mem = j.get("members") or {}
    return {"state": j.get("state", "?"), "ts": j.get("ts"), "home": Path(str(j.get("home") or "")).name or "-",
            "files": {k: v.get("state") for k, v in (ff.get("members") or {}).items()},
            "members": {k: {"state": v.get("state"), "snapshot": v.get("snapshot") or v.get("stamp") or v.get("ts") or "", "why": v.get("why") or ""} for k, v in mem.items()},
            "cycles": ((mem.get("console") or {}).get("cycles_reading") or None),      # 批518:G17 循環判讀(CGC_MDL150 v0103 cycles)
            "age_h": _age_h(str(j.get("ts") or ""))}


def cg_cycles_line(cg: dict) -> str:
    """批518:十一段/頁段共用一行——活樹圈才是債;缺=ABSENT 誠實。"""
    cr = (cg or {}).get("cycles")
    if not cr:
        return "主控台 G17 循環判讀:ABSENT(via-cgfamily cycles 跑一次即有;工具 RED 先分活樹/存檔再判)"
    return (f"主控台 G17 循環判讀(批518;L38):{cr.get('n')} 圈 · 活樹 {cr.get('live')} · " + " · ".join(f"{k} {v}" for k, v in (cr.get("by_zone") or {}).items())
            + f" → 活樹 {cr.get('verdict')}(退役/收容/存檔內互呼不是活樹的債;via-cgfamily cycles @ {cr.get('ts') or '-'})")


def ui_workflow() -> dict:
    """批519:U/I 對接契約 + 工作流最新一跑 + 庫分類歸納(CGC_MDL153 落 VIA_Reports/ui|workflow;缺=ABSENT 誠實;VIA_UI_CONTRACT_LATEST/VIA_WORKFLOW_LATEST/VIA_DB_SUMMARY_LATEST 可覆寫)。"""
    _e = os.environ.get("VIA_UI_CONTRACT_LATEST")
    uc = _json(Path(_e)) if _e else (_json(REPORTS / "ui" / "UI_CONTRACT_latest.json") or _json(HERE / "VIA_UI_Contract_v0100.json"))   # 明給路徑不退冊(自測 ABSENT 要真 ABSENT)
    wf = _json(Path(os.environ.get("VIA_WORKFLOW_LATEST") or (REPORTS / "workflow" / "WORKFLOW_latest.json")))
    db = _json(Path(os.environ.get("VIA_DB_SUMMARY_LATEST") or (REPORTS / "workflow" / "DB_SUMMARY_latest.json")))
    pages = (uc or {}).get("pages") or []
    out = {"state": "ABSENT" if not uc else "OK", "ts": (uc or {}).get("ts"), "n": len(pages), "by_family": (uc or {}).get("by_family") or {},
           "absent": [p.get("page") for p in pages if not p.get("exists")], "fresh": sum(1 for p in pages if p.get("fresh")),
           "pages": [{"page": p.get("page"), "family": p.get("family"), "lamp": p.get("lamp"), "owner": p.get("owner") or "", "refresh": p.get("refresh") or "", "path": p.get("path") or "", "exists": bool(p.get("exists"))} for p in pages],
           "workflow": ({"state": "ABSENT", "why": "尚未 via-workflow run"} if not wf else {"state": wf.get("verdict"), "id": wf.get("id"), "ts": wf.get("ts"), "profile": wf.get("profile"), "counts": wf.get("counts"),
                                                                                   "results": [{"id": r.get("id"), "state": r.get("state"), "why": str(r.get("why") or "")[:100]} for r in wf.get("results") or []]}),
           "db": ({"state": "ABSENT", "why": "尚未 via-workflow db-summary"} if not db else {"state": db.get("verdict"), "ts": db.get("ts"), "n_tables": db.get("n_tables"),
                                                                                         "categories": [{"cat": c.get("cat"), "lamp": c.get("lamp"), "n": c.get("n"), "newest": c.get("newest"), "worst_lag": c.get("worst_lag")} for c in db.get("categories") or []]}),
           "composer": "via-workflow page(WORKFLOW_COMPOSER.html;--publish 入倉 ui_support/VIA_UI_WorkflowComposer_v0100.html)"}
    if not uc:
        out["why"] = "UI_CONTRACT_latest.json 不在(via-workflow ui-contract --apply 跑一次即有)"
    return out


def vtmra() -> dict:
    """批516:VTMRA 家族測試閘快照(CGC_MDL152 test 落 VIA_Reports/vtmra/VTMRA_latest.json;VIA_VTMRA_LATEST 可覆寫)。"""
    p = Path(os.environ.get("VIA_VTMRA_LATEST") or (REPORTS / "vtmra" / "VTMRA_latest.json"))
    j = _json(p)
    if not j:
        return {"state": "ABSENT", "why": "VTMRA_latest.json 不在(via-vtmra 跑一次即有;七成員家族境真跑自測)"}
    return {"state": j.get("verdict", "?"), "ts": j.get("ts"), "members": {r.get("id"): r.get("state") for r in (j.get("results") or [])},
            "reasons": j.get("reasons") or [], "age_h": _age_h(str(j.get("ts") or ""))}


def _rungate_merged(latest: dict) -> tuple[dict, dict, list]:
    """批517:每個必驗族取 24h 內最新一跑(RUNGATE_*.json 史;VIA_RUNGATE_DIR 覆寫);回 (families, per-family ts, 取用檔名)。"""
    d = Path(os.environ.get("VIA_RUNGATE_DIR") or (REPORTS / "rungate"))
    fams, ts_of, used = {}, {}, []
    hist = sorted((p for p in d.glob("RUNGATE_2*.json")), key=lambda p: p.name, reverse=True) if d.is_dir() else []
    for fam in INSTALL_REQUIRED_FAMILIES:
        for p in hist:
            j = _json(p) or {}
            f = (j.get("families") or {}).get(fam)
            a = _age_h(j.get("ts", ""))
            if isinstance(f, dict) and a is not None and 0 <= a <= UNITEST_MAX_AGE_H:
                fams[fam], ts_of[fam] = f, j.get("ts", "")
                used.append(f"{fam}:{p.name}")
                break
        if fam not in fams and isinstance((latest.get("families") or {}).get(fam), dict):
            fams[fam], ts_of[fam] = latest["families"][fam], latest.get("ts", "")
            used.append(f"{fam}:latest")
    for fam, f in (latest.get("families") or {}).items():
        fams.setdefault(fam, f); ts_of.setdefault(fam, latest.get("ts", ""))
    return fams, ts_of, used


def rungate() -> dict:
    p = Path(os.environ.get("VIA_RUNGATE_LATEST") or (REPORTS / "rungate" / "RUNGATE_latest.json"))
    j = _json(p)
    if not j:
        return {"state": "ABSENT", "why": f"{p.name} 不在(via-rungate 先跑)", "install": "BLOCKED_UNITEST"}
    families, ts_of, used = _rungate_merged(j)
    _ages = [_age_h(ts_of.get(f, "")) for f in INSTALL_REQUIRED_FAMILIES if f in families]
    age = (max(a for a in _ages if a is not None) if any(a is not None for a in _ages) else _age_h(j.get("ts", "")))
    _order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
    _verdicts = [str((families.get(f) or {}).get("verdict", "?")) for f in INSTALL_REQUIRED_FAMILIES if f in families]
    merged_verdict = (max(_verdicts, key=lambda v: _order.get(v, 3)) if _verdicts else j.get("verdict", "?"))
    j = {**j, "verdict": merged_verdict, "_used": used}
    # L19 必驗族是政策常數，不允許以環境變數縮成單族繞門。
    required = list(INSTALL_REQUIRED_FAMILIES)
    reasons = []
    if j.get("verdict") != "GREEN":
        reasons.append(f"總燈={j.get('verdict', '?')}≠GREEN")
    if age is None or not 0 <= age <= UNITEST_MAX_AGE_H:
        reasons.append("RunGate 時間缺/來自未來/逾 24h")
    coverage = {}
    for fam in required:
        f = families.get(fam)
        if not isinstance(f, dict):
            coverage[fam] = {"ok": False, "why": "家族未測"}
            reasons.append(f"{fam} 家族未測")
            continue
        sm = f.get("summary") or {}
        py_ok = (f.get("python") or {}).get("state") == "OK"
        required_ok = _nat(sm.get("required_ok"))
        required_n = _nat(sm.get("required_n"))
        libs_ok = required_n > 0 and required_ok == required_n
        engines_n = _nat(sm.get("engines_n"))
        engines_ok = _nat(sm.get("engines_ok"))
        tests_ok = engines_n > 0 and engines_ok == engines_n
        fam_ok = f.get("verdict") == "GREEN" and py_ok and libs_ok and tests_ok
        why = []
        if f.get("verdict") != "GREEN": why.append(f"燈={f.get('verdict', '?')}")
        if not py_ok: why.append("家族境非 OK")
        if not libs_ok: why.append(f"必要庫 {sm.get('required_ok', 0)}/{sm.get('required_n', 0)}")
        if not tests_ok: why.append(f"自測站 {engines_ok}/{engines_n}")
        coverage[fam] = {"ok": fam_ok, "why": "、".join(why) or "完整 GREEN",
                         "required_ok": required_ok, "required_n": required_n,
                         "engines_ok": engines_ok, "engines_n": engines_n}
        if not fam_ok:
            reasons.append(f"{fam}:" + coverage[fam]["why"])
    ok = not reasons
    return {"state": j.get("verdict", "?"), "ts": j.get("ts"),
            "age_h": (round(age, 1) if age is not None else None),
            "families": list(families), "required_families": required, "used": j.get("_used", []),
            "coverage": coverage, "reasons": reasons,
            "install": "INSTALL_OK" if ok else "BLOCKED_UNITEST"}


def bus() -> dict:
    j = _json(REPORTS / "engine_bus" / "ENGINE_BUS_latest.json")
    if not j:
        return {"state": "ABSENT", "why": "ENGINE_BUS_latest.json 不在(via-ryg)"}
    res = j.get("results") or []
    by: dict = {}
    for r in res:
        by[r.get("state", "?")] = by.get(r.get("state", "?"), 0) + 1
    reds = [(r.get("id") or r.get("item"), (r.get("why") or "")[:90]) for r in res if r.get("state") in ("RED", "TIMEOUT")]
    return {"state": "OK", "ts": j.get("ts"), "profile": j.get("profile", "run"),
            "apply_families": j.get("apply_families"), "n": len(res), "counts": by or j.get("counts", {}), "reds": reds[:12],
            "html": str(REPORTS / "engine_bus" / "ENGINE_BUS_MATRIX.html")}


def handover_src() -> dict:
    hits = []
    for q in (VIA / "docs").glob("VIA_Handover_*_B*.md"):
        m = re.match(r"VIA_Handover_(\d{8})_B(\d+)\.md$", q.name)
        if m:
            hits.append(((m.group(1), int(m.group(2))), q))
    if not hits:
        return {"state": "ABSENT", "sections": {}}
    p = sorted(hits)[-1][1]
    t = p.read_text(encoding="utf-8", errors="replace")
    secs, cur, buf = {}, None, []
    for ln in t.splitlines():
        if ln.startswith("## "):
            if cur:
                secs[cur] = "\n".join(buf).strip()
            cur, buf = ln[3:].strip(), []
        else:
            buf.append(ln)
    if cur:
        secs[cur] = "\n".join(buf).strip()
    return {"state": "OK", "src": p.name, "sections": secs, "text": t}


def prompt_doc() -> dict:
    p = _newest(VIA / "docs", "VIA_AI_Handover_Prompt_v*.md")
    return {"state": "OK" if p else "ABSENT", "src": (p.name if p else ""), "text": (p.read_text(encoding="utf-8", errors="replace") if p else "")}


def dropped_balls() -> dict:
    hits = sorted((VIA / "docs").glob("VIA_DroppedBalls_B*.md"), key=lambda q: int(re.search(r"_B(\d+)", q.name).group(1)))
    p = hits[-1] if hits else None
    t = p.read_text(encoding="utf-8", errors="replace") if p else ""
    rows = [ln for ln in t.splitlines() if ln.startswith("| ") and not ln.startswith("| 代號") and not ln.startswith("|---")]
    return {"state": "OK" if p else "ABSENT", "src": (p.name if p else ""), "text": t, "n": len(rows), "open": sum(1 for r in rows if "~~" not in r)}


# ────────────────────────── 註冊稽核 ──────────────────────────
ENGINE_GLOBS = [("functional modules/VDF/engine", "*_v????.py"), ("functional modules/VDF", "*_v????.py"), ("functional modules/VRN", "*_v????.py"), ("functional modules/VAP/engine", "*_v????.py"),
                ("supportive modules/registry", "CGC_*_v????.py"), ("supportive modules/70_VRN_Rules", "SUP_*_v????.py"), ("supportive modules/network", "SUP_*_v????.py"),
                ("supportive modules/VIA_Central_Governance", "CGC_*_v????.py"), (".", "VIA_SYSTEM_MANAGER_v????.py")]

COMPONENT_PREFIX = {"system": "SYS", "engine": "ENG", "module": "MDL", "class": "CLS",
                    "function": "FNC", "feature": "FNT", "tool": "TOOL",
                    "package": "PKG", "environment": "ENV"}


def _tail_files() -> dict[str, Path]:
    """受治理範圍的尾版家族。版本變動不重發元件號。"""
    fams: dict[str, Path] = {}
    for d, g in ENGINE_GLOBS:
        for q in (VIA / d).glob(g):
            if "references" in q.parts or "_superseded" in str(q):
                continue
            stem = re.sub(r"_v\d{4}\.py$", "", q.name)
            if stem not in fams or q.name > fams[stem].name:
                fams[stem] = q
    return fams


def live_components() -> dict:
    """建立可重現的活元件清單；不寫檔。

    掃描界線刻意固定：受治理尾版 PY、其 AST 類別/函數、InputConsole 功能項、
    Register 短令、ToolRoster/Baseline 工具套件與環境。references 收容件除非已被
    規格冊掛成正式功能，否則不把整個封存倉當現役元件。
    """
    rows: dict[str, dict] = {}
    parse_errors = []

    def add(category: str, identity: str, source: str, line: int | None = None):
        identity = str(identity).strip()
        if not identity:
            return
        key = f"{category}|{identity}"
        row = {"key": key, "category": category, "identity": identity, "source": source}
        if line:
            row["line"] = int(line)
        rows.setdefault(key, row)

    tails = _tail_files()
    for stem, q in sorted(tails.items()):
        rel = q.relative_to(VIA).as_posix()
        cat = "engine" if re.search(r"_ENG\d+", stem) else ("module" if re.search(r"_MDL\d+", stem) else "system")
        add(cat, stem, rel)
        try:
            tree = ast.parse(q.read_text(encoding="utf-8", errors="replace"), filename=str(q))
        except Exception as exc:
            parse_errors.append({"file": rel, "why": f"{type(exc).__name__}:{str(exc)[:100]}"})
            continue

        class Visitor(ast.NodeVisitor):
            def __init__(self):
                self.stack: list[str] = []

            def visit_ClassDef(self, node):
                qual = ".".join(self.stack + [node.name])
                add("class", f"{stem}:{qual}", rel, node.lineno)
                self.stack.append(node.name); self.generic_visit(node); self.stack.pop()

            def _function(self, node):
                qual = ".".join(self.stack + [node.name])
                add("function", f"{stem}:{qual}", rel, node.lineno)
                self.stack.append(node.name); self.generic_visit(node); self.stack.pop()

            visit_FunctionDef = _function
            visit_AsyncFunctionDef = _function

        Visitor().visit(tree)

    # PowerShell launchers and their declared functions share the same central codes.
    ps_tails = {}
    for q in sorted((VIA / 'launchers').glob('*.ps1')):
        stem = re.sub(r'-v\d+$', '', q.stem)
        ps_tails[stem] = q
    for stem, q in ps_tails.items():
        rel = q.relative_to(VIA).as_posix()
        add('tool', 'launcher:' + stem, rel)
        for no, line in enumerate(q.read_text(encoding='utf-8-sig').splitlines(), 1):
            m = re.match(r'^function\s+(def_[A-Za-z0-9_]+)', line)
            if m:
                add('function', stem + ':' + m.group(1), rel, no)
    pc = _json(HERE / 'VIA_Panorama_Contract_v0100.json') or {}
    if pc:
        add('module', 'VIA_Panorama_Contract', 'supportive modules/registry/VIA_Panorama_Contract_v0100.json')
    for issue in pc.get('problem_types', []):
        add('feature', 'panorama/problem:' + issue['code'], 'VIA_Panorama_Contract')
    for item, params in pc.get('engine_params', {}).items():
        for name in params:
            add('feature', 'panorama/parameter:' + item + ':' + name, 'VIA_Panorama_Contract')
    for it in spec_items().get("items", []):
        add("feature", f"{it.get('family')}/{it.get('id')}", "VIA_InputConsole_Spec")
    for c in register_cmds().get("cmds", []):
        add("tool", c.get("cmd"), "Register-VIA-Commands")

    baseline = _json(HERE / "VIA_EnvGovernance_Baseline_v0100.json") or {}
    envs = {"base"}
    for name, cfg in (baseline.get("env_layout") or {}).items():
        if isinstance(cfg, dict):
            envs.add(str(name)); envs.update(str(x) for x in cfg.get("aliases", []) if x)
    for fam, cfg in (baseline.get("families") or {}).items():
        if not isinstance(cfg, dict):
            continue
        envs.add(str(cfg.get("target_env") or "")); envs.update(str(x) for x in cfg.get("alt_envs", []) if x)
        for pkg in cfg.get("members", []):
            add("package", str(pkg).lower(), f"EnvBaseline:{fam}")
    roster = _json(HERE / "VIA_ToolRoster_SSOT_v0100.json") or {}
    for env, cfg in (roster.get("envs") or {}).items():
        envs.add(str(env)); envs.update(str(x) for x in cfg.get("aliases", []) if x)
        for tool in cfg.get("tools", []):
            if isinstance(tool, dict):
                add("package", str(tool.get("pip") or tool.get("imp") or "").lower(), f"ToolRoster:{env}")
    for env in sorted(x for x in envs if x):
        add("environment", env, "EnvGovernance")
    # 批682B(Z79;PR #58 Codex P1):TOOLS_PLAN_latest.json 是執行期產物(不入 git),
    # 它列的境只在跑過 via-envtools 的機器上存在。算進活元件=冊會隨機器翻轉:
    # 工作站 --apply 復活、容器 --apply 退役、再回工作站又「缺 1」。
    # 所以它們標 runtime、另列;⑬ 等式 / audit 缺件表 / registry-sync 都只看 rows。
    tp_path = Path(os.environ.get("VIA_TOOLS_PLAN_LATEST") or (REPORTS / "env_governance" / "TOOLS_PLAN_latest.json"))
    runtime = _json(tp_path) or {}
    runtime_rows = []
    for e in runtime.get("envs", []):
        name = str(e.get("name") or "").strip() if isinstance(e, dict) else ""
        if name and f"environment|{name}" not in rows:
            runtime_rows.append({"key": f"environment|{name}", "category": "environment",
                                 "identity": name, "source": "EnvGovernance:runtime", "runtime": True})
    counts: dict[str, int] = {}
    for r in rows.values():
        counts[r["category"]] = counts.get(r["category"], 0) + 1
    return {"rows": [rows[k] for k in sorted(rows)], "counts": counts,
            "parse_errors": parse_errors, "tails": len(tails),
            "runtime_rows": runtime_rows, "runtime": len(runtime_rows)}


def component_registry() -> dict:
    j = _json(COMPONENT_REGISTRY)
    if not j:
        return {"state": "ABSENT", "path": str(COMPONENT_REGISTRY), "n": 0,
                "active": 0, "retired": 0, "counts": {}, "records": []}
    rec = j.get("records") or []
    active = [r for r in rec if r.get("state", "ACTIVE") == "ACTIVE"]
    counts: dict[str, int] = {}
    for r in active:
        counts[r.get("category", "?")] = counts.get(r.get("category", "?"), 0) + 1
    return {"state": "OK", "path": str(COMPONENT_REGISTRY), "n": len(rec),
            "active": len(active), "retired": len(rec) - len(active), "counts": counts,
            "updated_at": j.get("updated_at"), "records": rec, "counters": j.get("counters", {})}


def registry_sync(apply: bool = False, path: Path = COMPONENT_REGISTRY) -> dict:
    """VCGC 唯一寫入口；穩定號只增不減，消失件標 RETIRED、不刪號。"""
    live = live_components()
    old = _json(path) or {"schema": "VIA.ComponentInventory.v1", "append_only": True,
                          "writer": "VCGC registry-sync --apply", "counters": {}, "records": []}
    counters = {k: int(v) for k, v in (old.get("counters") or {}).items()}
    records = [dict(r) for r in (old.get("records") or [])]
    by_key = {r.get("key"): r for r in records if r.get("key")}
    live_by = {r["key"]: r for r in live["rows"]}
    new_keys = sorted(set(live_by) - set(by_key))
    stale_keys = sorted(k for k, r in by_key.items() if r.get("state", "ACTIVE") == "ACTIVE" and k not in live_by)
    tracked_fields = ("category", "identity", "source", "line")
    changed_keys = sorted(
        key for key in set(live_by) & set(by_key)
        if by_key[key].get("state") != "ACTIVE"
        or any(by_key[key].get(k) != live_by[key].get(k) for k in tracked_fields)
    )
    now = datetime.now().isoformat(timespec="seconds")
    if apply:
        for key in new_keys:
            r = live_by[key]
            prefix = COMPONENT_PREFIX[r["category"]]
            counters[prefix] = counters.get(prefix, 0) + 1
            records.append({**r, "code": f"VIA-{prefix}-{counters[prefix]:04d}",
                            "state": "ACTIVE", "first_seen": now})
        for key in changed_keys:
            cur, src = by_key[key], live_by[key]
            cur.update(src); cur["state"] = "ACTIVE"; cur.pop("retired_at", None)
            cur["changed_at"] = now
        for key in stale_keys:
            by_key[key]["state"] = "RETIRED"; by_key[key]["retired_at"] = now
        dirty = bool(new_keys or stale_keys or changed_keys or not path.exists())
        if dirty:
            out = {**old, "schema": "VIA.ComponentInventory.v1", "append_only": True,
                   "writer": "VCGC registry-sync --apply", "batch": BATCH,
                   "updated_at": now, "counters": counters,
                   "records": sorted(records, key=lambda r: r.get("code", ""))}
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            os.replace(tmp, path)
    return {"state": "APPLIED" if apply else "PLAN", "path": str(path),
            "expected": len(live_by), "counts": live["counts"], "parse_errors": live["parse_errors"],
            "new": len(new_keys), "new_keys": new_keys, "stale": len(stale_keys),
            "stale_keys": stale_keys, "changed": len(changed_keys)}


def audit(deck=None, spec=None, grid=None, reg=None, man=None) -> dict:
    deck = deck if deck is not None else deck_tasks()
    spec = spec if spec is not None else spec_items()
    grid = grid if grid is not None else grid_stations()
    reg = reg if reg is not None else register_cmds()
    man = man if man is not None else manager_names()
    reg_text = ""
    p = _newest(VIA, "Register-VIA-Commands-v*.ps1")
    if p:
        reg_text = p.read_text(encoding="utf-8", errors="replace")
    surface_text = {
        "Deck": json.dumps(deck.get("tasks"), ensure_ascii=False),
        "Spec": json.dumps(spec.get("items"), ensure_ascii=False),
        "Grid": "\n".join(s["path"] + " " + s["name"] for s in grid.get("stations", [])),
        "Register": reg_text,
        "Manager": json.dumps(man, ensure_ascii=False),
    }
    fams = {stem: {"newest": q.name, "dir": q.parent.relative_to(VIA).as_posix()}
            for stem, q in _tail_files().items()}
    inv = component_registry()
    inv_active = {r.get("key") for r in inv.get("records", []) if r.get("state", "ACTIVE") == "ACTIVE"}
    rows = []
    for stem, v in sorted(fams.items()):
        cat = "engine" if re.search(r"_ENG\d+", stem) else ("module" if re.search(r"_MDL\d+", stem) else "system")
        registered = f"{cat}|{stem}" in inv_active
        surfaces = [name for name, text in surface_text.items() if stem in text]
        rows.append({"family": stem, "newest": v["newest"], "dir": v["dir"],
                     "registered": registered, "surfaces": surfaces,
                     "interface_registered": bool(surfaces)})
    unreg = [r for r in rows if not r["registered"]]
    interface_gaps = [r for r in rows if not r["interface_registered"]]
    live = live_components()
    live_keys = {r["key"] for r in live["rows"]}
    missing_all = sorted(live_keys - inv_active)
    return {"families": len(rows), "registered": len(rows) - len(unreg),
            "unregistered": unreg, "rows": rows, "interface_registered": len(rows) - len(interface_gaps),
            "interface_gaps": interface_gaps, "inventory_state": inv.get("state"),
            "inventory_active": inv.get("active", 0), "inventory_expected": len(live_keys),
            "inventory_missing": missing_all, "inventory_counts": inv.get("counts", {}),
            "parse_errors": live.get("parse_errors", [])}


def check() -> dict:
    """L19 安裝核可:VDF+VRN 完整 RunGate GREEN 且 24h 內。"""
    r = rungate()
    result = {"install": r.get("install"), "rungate": r.get("state"), "age_h": r.get("age_h"),
            "required_families": r.get("required_families"), "coverage": r.get("coverage"),
            "reasons": r.get("reasons"), "law": "L19 環境統一測式(VDF+VRN 完整覆蓋)無誤後才可核可安裝"}
    # 批568:比照 RunGate 慣例給覆寫鍵,生產預設路徑不變;合成檢才關得進沙盒(LL114)
    latest_path = Path(os.environ.get("VIA_PANORAMA_LATEST") or (REPORTS / 'panorama' / 'PANORAMA_latest.json'))
    latest = _json(latest_path)
    age = _age_h((latest or {}).get('updated_at', ''))
    if latest_path.exists() and (not latest or latest.get('status') != 'FINISHED' or latest.get('blockers', 1)
                                 or not latest.get('results') or age is None or age < 0 or age > UNITEST_MAX_AGE_H):
        result['install'] = 'BLOCKED_PANORAMA'
        result['reasons'] = list(result.get('reasons') or []) + ['全景實測尚未完成或仍有待修項目']
    return result


# ── 批568 來源閘:⑨ 這條路真正讀的每一個真機器來源,都要配覆寫鍵、都要被自測關進沙盒 ──
SOURCE_GUARD_FUNCS = ("check", "rungate", "_rungate_merged")


def _reports_reads(node) -> list:
    """回傳函式體內所有 `REPORTS / …` 磁碟來源運算式(只留最外層,不留中間節點)。"""
    seen = set()
    for n in ast.walk(node):
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
            s = ast.unparse(n)
            if s.startswith("REPORTS"):
                seen.add(s)
    return sorted(s for s in seen if not any(o != s and o.startswith(s + " /") for o in seen))


def source_guard() -> dict:
    """⑳ 批568:列 ⑨ 這條路的來源清單,並驗①每個磁碟來源都有 VIA_* 覆寫鍵 ②自測 ⑨ 區塊每個鍵都設過。

    立這道閘的原因寫在檔頭:批567 我只關了 RunGate 一個口,panorama 那口漏著,
    同一個檢在兩台機器上紅成兩種樣子。以後「底下還有一層」由機器講,不靠我記得。
    """
    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    guarded, keys, disk = {}, [], []
    for fn in SOURCE_GUARD_FUNCS:
        node = funcs.get(fn)
        if node is None:
            continue
        for n in ast.walk(node):                      # 覆寫慣用式:os.environ.get("VIA_X") or (REPORTS / …)
            if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or) and len(n.values) == 2:
                lhs, rhs = n.values
                if (isinstance(lhs, ast.Call) and isinstance(lhs.func, ast.Attribute) and lhs.func.attr == "get"
                        and isinstance(lhs.func.value, ast.Attribute) and lhs.func.value.attr == "environ"
                        and lhs.args and isinstance(lhs.args[0], ast.Constant)):
                    k = str(lhs.args[0].value)
                    keys.append(k)
                    guarded[ast.unparse(rhs).strip("()")] = k
        for s in _reports_reads(node):
            disk.append((fn, s))
    unguarded = sorted({s for _, s in disk if s not in guarded})
    blk = src.split('sv = os.environ.get("VIA_RUNGATE_LATEST")', 1)[-1].split('chk("\u2468', 1)[0]
    unsandboxed = sorted(k for k in set(keys) if f'os.environ["{k}"]' not in blk)
    return {"state": "OK" if not unguarded and not unsandboxed else "FAIL",
            "funcs": list(SOURCE_GUARD_FUNCS), "keys": sorted(set(keys)),
            "disk": sorted({s for _, s in disk}), "guarded": guarded,
            "unguarded": unguarded, "unsandboxed": unsandboxed}


# ────────────────────────── 一頁交接 + 頁 ──────────────────────────
def snapshot() -> dict:
    deck, spec, grid, reg, man = deck_tasks(), spec_items(), grid_stations(), register_cmds(), manager_names()
    return {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "version": VERSION, "batch": BATCH, "laws": laws(), "ledger": ledger(), "deck": deck, "spec": spec,
            "grid": grid, "register": reg, "manager": man, "db_sheet": db_sheet(), "datahome": datahome(), "logic": logic(), "factors": factors(), "vrn_system": vrn_system(), "vdf_system": vdf_system(), "vap_system": vap_system(), "subsystems": subsystems(),
            "tools": tools_plan(), "recover": recover_plan(), "cg_family": cg_family(), "vtmra": vtmra(), "ui_workflow": ui_workflow(), "rungate": rungate(), "bus": bus(), "handover": handover_src(), "audit": audit(deck, spec, grid, reg, man),
            "inventory": component_registry(), "prompt": prompt_doc(), "balls": dropped_balls(),
            "panorama": _json(REPORTS / "panorama" / "PANORAMA_latest.json") or {}}


def onepage_md(s: dict) -> str:
    L, lg, dk, sp, gr, rg, mn, db, dh, lo, fa, tp, ru, bu, ho, au, inv = (s[k] for k in ("laws", "ledger", "deck", "spec", "grid", "register", "manager", "db_sheet", "datahome", "logic", "factors", "tools", "rungate", "bus", "handover", "audit", "inventory"))
    o = [f"# VIA 一頁交接 · Veritas Central Governance Console(VCGC v{VERSION} · 批{BATCH})", "",
         f"> 產生 {s['ts']} · 唯一對接口(律 L20):政策庫 · 邏輯庫 · 因子庫 · 資料庫 · 引擎調度 · 多矩陣 · 環境工具 · 註冊表 · 交接。動態段(矩陣/RunGate/工具計畫/資料家)以**你機器上最新一次 `via-vcgc onepage`** 為準;倉內這份是 commit 時的快照。", ""]
    pr, bl = s.get("prompt", {}), s.get("balls", {})
    o += ["## 〇 · 接手提示詞(給下一個 AI;來源 " + str(pr.get("src") or "ABSENT") + ")", "", (pr.get("text") or "(docs/VIA_AI_Handover_Prompt_v*.md 缺)").strip(), ""]
    o += ["## 一 · 政策庫(律 + lessons-learned)", ""]
    # 批602:政策庫是**手維護的冊**,選填欄少一個是遲早的事——但 `x['cat']` 這種寫法會讓
    #   「冊上少一個選填欄」升級成「整台中央控管台 KeyError 垮掉、全格報紅」。
    #   實錄:批602 新增 L81/L82 時沒帶 `cat`(既有兩條律的 cat 本來就是 null),
    #   結果不是「那一格印不出來」,是 onepage/page 兩條路一起炸。讀冊一律 .get,缺就誠實留白。
    for x in L["laws"]:
        cat = x.get("cat")
        o.append(f"- **{x.get('id', '?')}**({x.get('batch', '?')}" + (f";{cat}" if cat else "") + f"){x.get('zh', '')}")
    o += ["", "**Lessons-learned**", ""] + [f"- {x.get('id', '?')}({x.get('batch', '?')}){x.get('zh', '')}" for x in L["lessons"]]
    rv = s.get("recover") or {}
    o += ["", "## 二 · 安裝核可(L19)與環境工具", "",
          f"- RunGate:{ru.get('state')} · {ru.get('ts') or '-'} · 齡 {ru.get('age_h')} h · 必驗 {ru.get('required_families')} · 覆蓋 {ru.get('coverage')} → **{ru.get('install')}**" + (f" · 原因 {ru.get('reasons')}" if ru.get("reasons") else ""),
          f"- 工具冊導入計畫:{tp.get('state')} · {tp.get('ts') or '-'} · 件態 {tp.get('counts') if tp.get('counts') is not None else '-'} · 風險 {tp.get('risk') if tp.get('risk') is not None else '-'} · 段 {tp.get('stages') if tp.get('stages') is not None else '-'} · 未路由 {tp.get('unrouted') if tp.get('unrouted') is not None else '-'} · 白名單留置 {tp.get('hold') if tp.get('hold') is not None else '-'}" + (f"({tp.get('why')})" if tp.get("why") else ""),
          f"- 環境復原(L24):{rv.get('state')} · {rv.get('ts') or '-'} · 還原 {rv.get('restore') or '-'} · 段 {rv.get('stages')} · 單獨隔離境 {rv.get('exclusive')} · 借境封鎖 {rv.get('borrow_blocked')} · 次序 {' → '.join(rv.get('order') or []) or '-'}" + (f"({rv.get('why')})" if rv.get("why") else "") + ";安裝出問題=`via-envrecover`(①還原前次 ②順序裝 ③_M/_H 單獨隔離;-Execute -Approve 才跑,① 不受 L19,② 過 L19)",
          "- 裝件=操作員的手:`$env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve`(閘不代設;L19 未綠=BLOCKED_UNITEST)", ""]
    o += ["## 三 · 邏輯庫 · 因子庫 · 資料庫", "",
          f"- 邏輯庫 {lo.get('state')}:件 {lo.get('files')} · 判準 {lo.get('verdicts')} · 壞後端 {lo.get('broken')} · 政策因子 {lo.get('policy_rows')} 列 · 全庫同步 {lo.get('sync')} · 交接三處 {lo.get('handover')}",
          f"- 因子庫 {fa.get('state')}:{fa.get('rows')} 列 · {fa.get('by_source')} · 掛載 {fa.get('mounts')}",
          f"- 庫表冊 {db.get('state')}:{db.get('n')} 表({db.get('batch')})· 全庫表 {db.get('all_home')} · 庫 {db.get('dbs')}",
          f"- 資料家 {dh.get('state')}:{dh.get('home') or dh.get('why')} · 庫 {dh.get('dbs') if dh.get('dbs') is not None else '-'} · 表 {dh.get('tables') if dh.get('tables') is not None else '-'} · 湖 {dh.get('lakes') if dh.get('lakes') is not None else '-'}", ""]
    o += ["## 四 · 引擎調度 · 多矩陣實測", "",
          f"- 五矩陣 {bu.get('state')}:{bu.get('ts') or bu.get('why')} · profile {bu.get('profile')} · 真跑 {bu.get('apply_families')} · 項 {bu.get('n')} · 態 {bu.get('counts')}"]
    for rid, why in (bu.get("reds") or []):
        o.append(f"  - RED {rid}:{why}")
    vt = s.get("vtmra") or {}
    o.append(f"- VTMRA 家族測試閘(批516;台股月營收分析七成員):{vt.get('state')} · {vt.get('ts') or vt.get('why') or '-'} · 成員 {vt.get('members') or '-'}" + (f" · {'; '.join(vt.get('reasons') or [])}" if vt.get("reasons") else ""))
    o += [f"- Deck 任務 {len(dk.get('tasks', {}))} · 規格項 {len(sp.get('items', []))} · 格子站 {len(gr.get('stations', []))}(在位 {sum(1 for x in gr.get('stations', []) if x['present'])})· Register 指令 {len(rg.get('cmds', []))} · Manager 正式名稱 任務 {len(mn.get('tasks', {}))} / 引擎 {len(mn.get('engines', {}))}", ""]
    o += ["## 五 · 指令與參數(不丟失;來源 " + str(rg.get("src")) + ")", ""] + [f"- `{c['cmd']}`" + (f"(別名 {'/'.join(c['aliases'])})" if c["aliases"] else "") + (f":{c['usage']}" if c["usage"] else "") for c in rg.get("cmds", [])]
    o += ["", "## 六 · 註冊稽核(所有引擎/模組/功能/工具/環境)", "",
          f"- 中央自動編號冊 {au.get('inventory_state')} · ACTIVE {au.get('inventory_active')}/{au.get('inventory_expected')} · **缺 {len(au.get('inventory_missing', []))}** · 類別 {au.get('inventory_counts')}",
          f"- 尾版引擎/模組家族 {au['families']} · 中央冊已登 {au['registered']} · **未登 {len(au['unregistered'])}** · 操作介面有掛載 {au.get('interface_registered')} · 內部件無操作介面 {len(au.get('interface_gaps', []))}(誠實分列，不拿編號片段假命中)"] + [f"  - 未登 {r['newest']}({r['dir']})" for r in au["unregistered"][:60]]
    o += ["", "## 七 · 自動編號註冊表(台帳)", "", f"- 全域台帳 {lg.get('n')} 筆 · 元件 {lg.get('components')} · 更新 {lg.get('updated_at')}",
          f"- 元件冊 {inv.get('state')} · ACTIVE {inv.get('active')} · RETIRED {inv.get('retired')} · 更新 {inv.get('updated_at')} · {inv.get('counts')}",
          "- 類別 current:" + " · ".join(f"{k} {v}" for k, v in (lg.get("categories") or {}).items() if v), ""]
    for e in (lg.get("tail") or [])[-6:]:
        detail = e.get("kind") or " ".join(
            str(x) for x in (e.get("op"), e.get("category"), e.get("component"), e.get("code")) if x
        )
        o.append(f"- {e.get('ts')} {detail[:90]}")
    o += ["", f"## 八 · 交接本文(來源 {ho.get('src')};逐批紀錄見該檔)", ""]
    # 批508：舊版只挑名稱寫死的「三 還掛／四 紀律／五 一貼」三節；
    # 新固定格式 〇–八 因此整段空白。交接不能靠標題碰巧同名，尾版全文才是
    # 唯一記憶。嵌入時只把標題降一級，維持 ONEPAGE 九個主段不被打散。
    handover_lines = []
    for i, line in enumerate((ho.get("text") or "").splitlines()):
        if i == 0 and line.startswith("# "):
            continue
        if line.startswith("### "):
            line = "#### " + line[4:]
        elif line.startswith("## "):
            line = "### " + line[3:]
        handover_lines.append(line)
    o += handover_lines or ["(逐批交接本文缺)"]
    o_tail = ["", f"## 九 · 掉球清單(來源 {bl.get('src') or 'ABSENT'};列 {bl.get('n')} · 未結 {bl.get('open')};只增不減,結案劃線)", "", (bl.get("text") or "(缺)").strip(), ""]
    o += o_tail
    pa = s.get("panorama") or {}
    if pa:
        o += ["", "## 十 · VRN / VDF / VATETF(舊名 VETF)最新全景實測", "",
              f"{pa.get('start')} → {pa.get('end')} · {pa.get('status')} · 核可 {pa.get('approval')} · 待修 {pa.get('blockers')}", "",
              "| 項目 | 階段 | 狀態 | 問題與處置 |", "|---|---|---|---|"]
        for row in pa.get('results', []):
            vals = [str(row.get(k, '')).replace('|','\\|').replace('\n','<br>') for k in ('id','phase','state','why')]
            o.append('| ' + ' | '.join(vals) + ' |')
    cg = s.get("cg_family") or {}
    o += ["", "## 十一 · 中央治理家族(批514;VIA-SYS-MGR-001 主控台 · VIA-GOV-ENG-001 詞彙引擎 · VIA-SYS-MGR-003 下行控制 · VIA-SYS-ENG-003 檔案優先序 · 同名整併;擁有者 CGC_MDL150;預設 dry-run)", "",
          f"- 家族 {cg.get('state')} · {cg.get('ts') or cg.get('why') or '-'} · 正位 {cg.get('home') or '-'} · 成員件 {cg.get('files') or '-'}"]
    for k, m in (cg.get("members") or {}).items():
        o.append(f"  - {k}:{m.get('state')}" + (f" · {m.get('snapshot')}" if m.get("snapshot") else "") + (f" · {m.get('why')}" if m.get("why") else ""))
    o += ["- " + cg_cycles_line(cg)]
    o += ["- 一貼即用:`via-cgfamily plan`(router → engine --selftest → console → downward → samename;--commit/--probe/--token=你的手)"]
    uw = s.get("ui_workflow") or {}
    o += ["", "## 十二 · U/I 對接與工作流(批519;擁有者 CGC_MDL153 WorkflowComposer;中央只連結不重造;頁在=連、不在=ABSENT)", "",
          f"- U/I 契約 {uw.get('state')} · {uw.get('ts') or uw.get('why') or '-'} · 頁 {uw.get('n')} · 家族 {uw.get('by_family') or '-'} · 新鮮 {uw.get('fresh')} · 不在 {len(uw.get('absent') or [])}"]
    for p in (uw.get("pages") or [])[:60]:
        o.append(f"  - [{p.get('lamp')}] {p.get('family')} · {p.get('page')} · 擁有者 {p.get('owner') or '-'} · 再生 {p.get('refresh') or '-'}")
    w = uw.get("workflow") or {}
    o.append(f"- 工作流最新一跑 {w.get('state')} · {w.get('id') or ''} · {w.get('ts') or w.get('why') or '-'} · {w.get('counts') or ''}")
    for r in w.get("results") or []:
        o.append(f"  - [{r.get('state')}] {r.get('id')} {r.get('why') or ''}")
    d = uw.get("db") or {}
    o.append(f"- VDF 庫分類歸納 {d.get('state')} · {d.get('ts') or d.get('why') or '-'} · 表 {d.get('n_tables') if d.get('n_tables') is not None else '-'} · " + " · ".join(f"{c.get('cat')} {c.get('lamp')}(表 {c.get('n')} 最新 {c.get('newest') or '-'} 滯後 {c.get('worst_lag') if c.get('worst_lag') is not None else '?'})" for c in d.get("categories") or []))
    o.append(f"- 一貼即用:`via-workflow ui-contract --apply` → `via-workflow db-summary` → `via-workflow run <id> --profile test` → `via-workflow page --publish` → `via-open`(零彈窗:頁不自開)")
    vs = s.get("vrn_system") or {}
    o += ["", "## 十三 · VRN 子系統管理對接口(批681;VRN_SystemManager;VIA 往下讀 VRN 四庫一律經此;上接 VCGC · 下管 政策/邏輯/因子/參數 + 引擎面 + 交接;自適應連結現解尾版;預設只讀)", "",
          f"- {vs.get('state')} · {vs.get('src') or vs.get('why') or '-'} · {vs.get('ts') or '-'} · 燈 {vs.get('lamps') or '-'} · 連結 {vs.get('links')} {vs.get('link_counts') or ''} · 七處自審 {vs.get('seven_done')}/7 {vs.get('seven') or ''}" + (f" · {vs.get('why')}" if vs.get('why') else ""),
          "- 直呼引擎(尾版 glob,短令候 L70 許可):functional modules/VRN/VRN_SystemManager_v*.py status | catalog | links | read <policy|logic|factor|param|engine|handover|upstream> [key] | sync --apply(只落 VIA_Reports/vrn_system)"]
    vd = s.get("vdf_system") or {}
    vb = vd.get("bridge") or {}
    o += ["", "## 十四 · VDF 子系統管理對接口(側線 2026-09-21;VDF_SystemManager;VIA 往下讀 VDF 一律經此;上接 VCGC · 下管 政策/邏輯/因子/參數 + 引擎面 + 橋/工具面 + 交接/紀錄;橋律逐支量;自適應連結現解尾版;預設只讀)", "",
          f"- {vd.get('state')} · {vd.get('src') or vd.get('why') or '-'} · {vd.get('ts') or '-'} · 模式 {vd.get('mode') or '-'} · 燈 {vd.get('lamps') or '-'} · 連結 {vd.get('links')} {vd.get('link_counts') or ''} · 七處自審 {vd.get('seven_done')}/7 {vd.get('seven') or ''}" + (f" · {vd.get('why')}" if vd.get('why') else ""),
          f"- 橋律(所有 PY 接加速器 · 真向外擷取走網路工具;尺=CGC_MDL124):尾版 {vb.get('tails')} · 加速器橋 {vb.get('accel')} · 網路橋 {vb.get('net')} · 真擷取 {vb.get('net_callers')} · 缺加速器 {vb.get('accel_missing')} · 真擷取缺網路橋 {vb.get('net_callers_missing')}",
          "- 直呼引擎(尾版 glob,短令候 L70 許可):functional modules/VDF/VDF_SystemManager_v*.py status | engines | bridges | tools | catalog | links | records | read <policy|logic|factor|param|engine|bridge|tool|handover|records|upstream> [key] [--full] | sync --apply(只落 VIA_Reports/vdf_system)"]
    return "\n".join(o) + "\n"


def page_html(s: dict) -> str:
    def esc(x):
        return html.escape(str(x))

    def table(rows, cols):
        h = "<table><tr>" + "".join(f"<th>{esc(c)}</th>" for c in cols) + "</tr>"
        for r in rows:
            h += "<tr>" + "".join(f"<td>{esc(r.get(c, ''))}</td>" for c in cols) + "</tr>"
        return h + "</table>"
    lamp = {"OK": "#16a34a", "GREEN": "#16a34a", "INSTALL_OK": "#16a34a", "ABSENT": "#6b7280", "BLOCKED_UNITEST": "#f59e0b", "RED": "#dc2626", "PLAN": "#2563eb"}
    ru, bu, tp, lo, fa, db, dh, au, rg, lg, L, inv = (s[k] for k in ("rungate", "bus", "tools", "logic", "factors", "db_sheet", "datahome", "audit", "register", "ledger", "laws", "inventory"))

    def chip(t):
        return f'<span class="chip" style="background:{lamp.get(str(t).split(" ")[0], "#6b7280")}">{esc(t)}</span>'
    # 批577 畫面統一閘 LAW:補 viewport(手機開這張頁不再被迫橫向捲)
    parts = [f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'>"
             f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
             f"<title>Veritas Central Governance Console v{VERSION}</title>",
             "<style>body{font-family:'Segoe UI',system-ui,sans-serif;margin:0;background:#0f172a;color:#e5e7eb}header{padding:18px 28px;background:#111827;border-bottom:1px solid #334155}h1{margin:0;font-size:20px}h2{font-size:15px;margin:22px 0 8px;color:#93c5fd}section{padding:6px 28px}table{border-collapse:collapse;font-size:12px;width:100%}th,td{border:1px solid #334155;padding:4px 6px;text-align:left;vertical-align:top}th{background:#1f2937}.chip{display:inline-block;padding:2px 8px;border-radius:10px;color:#fff;font-size:12px;margin-right:6px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}.card{background:#111827;border:1px solid #334155;border-radius:8px;padding:10px 12px;font-size:13px}code{background:#1f2937;padding:1px 4px;border-radius:4px}small{color:#9ca3af}</style></head><body>",
             f"<header><h1>Veritas Central Governance Console <small>v{VERSION} · 批{BATCH} · {esc(s['ts'])} · 唯一對接口(L20)· 零 CDN · 預設只讀</small></h1></header>",
             "<section><div class='grid'>",
             f"<div class='card'><b>安裝核可 L19</b><br>{chip(ru.get('install'))} RunGate {chip(ru.get('state'))} {esc(ru.get('ts') or ru.get('why') or '')} 齡 {esc(ru.get('age_h'))} h<br>必驗 {esc(ru.get('required_families'))} · {esc(ru.get('coverage'))}<br>{esc(ru.get('reasons'))}</div>",
             f"<div class='card'><b>五矩陣</b><br>{chip(bu.get('state'))} {esc(bu.get('ts') or bu.get('why') or '')} · profile {esc(bu.get('profile'))}<br>{esc(bu.get('counts'))}</div>",
             f"<div class='card'><b>環境工具計畫</b><br>{chip(tp.get('state'))} {esc(tp.get('ts') or tp.get('why') or '')}<br>{esc(tp.get('counts') if tp.get('counts') is not None else '-')} · 風險 {esc(tp.get('risk') if tp.get('risk') is not None else '-')}</div>",
             f"<div class='card'><b>環境復原(L24)</b><br>{chip((s.get('recover') or {}).get('state'))} {esc((s.get('recover') or {}).get('ts') or (s.get('recover') or {}).get('why') or '')}<br>還原 {esc((s.get('recover') or {}).get('restore') or '-')} · 段 {esc((s.get('recover') or {}).get('stages'))} · 隔離境 {esc(len((s.get('recover') or {}).get('exclusive') or []))}</div>",
             f"<div class='card'><b>中央治理家族(批514)</b><br>{chip((s.get('cg_family') or {}).get('state'))} {esc((s.get('cg_family') or {}).get('ts') or (s.get('cg_family') or {}).get('why') or '')}<br>正位 {esc((s.get('cg_family') or {}).get('home') or '-')} · 成員 {esc({k: v.get('state') for k, v in ((s.get('cg_family') or {}).get('members') or {}).items()})}</div>",
             f"<div class='card'><b>U/I 對接與工作流(批519)</b><br>{chip((s.get('ui_workflow') or {}).get('state'))} 頁 {esc((s.get('ui_workflow') or {}).get('n'))} · 新鮮 {esc((s.get('ui_workflow') or {}).get('fresh'))} · 不在 {esc(len((s.get('ui_workflow') or {}).get('absent') or []))}<br>工作流 {chip(((s.get('ui_workflow') or {}).get('workflow') or {}).get('state'))} {esc(((s.get('ui_workflow') or {}).get('workflow') or {}).get('id') or '')} · 庫分類 {chip(((s.get('ui_workflow') or {}).get('db') or {}).get('state'))}</div>",
             f"<div class='card'><b>VTMRA 家族測試閘(批516)</b><br>{chip((s.get('vtmra') or {}).get('state'))} {esc((s.get('vtmra') or {}).get('ts') or (s.get('vtmra') or {}).get('why') or '')}<br>成員 {esc((s.get('vtmra') or {}).get('members') or '-')}</div>",
             f"<div class='card'><b>邏輯庫</b><br>{chip(lo.get('state'))} 件 {esc(lo.get('files'))} · {esc(lo.get('verdicts'))}<br>壞後端 {esc(lo.get('broken'))}<br>同步 {esc(lo.get('sync'))}</div>",
             f"<div class='card'><b>因子庫</b><br>{chip(fa.get('state'))} {esc(fa.get('rows'))} 列 · {esc(fa.get('by_source'))}</div>",
             f"<div class='card'><b>VRN 子系統管理(批681)</b><br>{chip((s.get('vrn_system') or {}).get('state'))} {esc((s.get('vrn_system') or {}).get('src') or (s.get('vrn_system') or {}).get('why') or '')}<br>燈 {esc((s.get('vrn_system') or {}).get('lamps'))}<br>連結 {esc((s.get('vrn_system') or {}).get('links'))} {esc((s.get('vrn_system') or {}).get('link_counts'))} · 七處 {esc((s.get('vrn_system') or {}).get('seven_done'))}/7</div>",
             f"<div class='card'><b>VDF 子系統管理(側線 2026-09-21)</b><br>{chip((s.get('vdf_system') or {}).get('state'))} {esc((s.get('vdf_system') or {}).get('src') or (s.get('vdf_system') or {}).get('why') or '')}<br>燈 {esc((s.get('vdf_system') or {}).get('lamps'))}<br>連結 {esc((s.get('vdf_system') or {}).get('links'))} {esc((s.get('vdf_system') or {}).get('link_counts'))} · 七處 {esc((s.get('vdf_system') or {}).get('seven_done'))}/7<br>橋 加速器 {esc(((s.get('vdf_system') or {}).get('bridge') or {}).get('accel'))}/{esc(((s.get('vdf_system') or {}).get('bridge') or {}).get('tails'))} · 網路 {esc(((s.get('vdf_system') or {}).get('bridge') or {}).get('net'))}/{esc(((s.get('vdf_system') or {}).get('bridge') or {}).get('tails'))} · 真擷取 {esc(((s.get('vdf_system') or {}).get('bridge') or {}).get('net_callers'))}</div>",
             f"<div class='card'><b>資料庫</b><br>庫表冊 {esc(db.get('n'))} 表({esc(db.get('batch'))})· 資料家 {chip(dh.get('state'))} {esc(dh.get('home') or dh.get('why'))} · 庫 {esc(dh.get('dbs') if dh.get('dbs') is not None else '-')} 湖 {esc(dh.get('lakes') if dh.get('lakes') is not None else '-')}</div>",
             f"<div class='card'><b>註冊稽核</b><br>中央冊 {esc(au.get('inventory_active'))}/{esc(au.get('inventory_expected'))} · 缺 {len(au.get('inventory_missing', []))}<br>尾版家族 {au['families']} · 已登 {au['registered']} · 未登 {len(au['unregistered'])} · 介面掛載 {esc(au.get('interface_registered'))}</div>",
             f"<div class='card'><b>掉球清單</b><br>{esc(s.get('balls', {}).get('src') or 'ABSENT')} · 列 {esc(s.get('balls', {}).get('n'))} · 未結 {esc(s.get('balls', {}).get('open'))}<br><small>接手提示詞:{esc(s.get('prompt', {}).get('src') or 'ABSENT')}</small></div>",
             f"<div class='card'><b>自動編號註冊表</b><br>全域台帳 {esc(lg.get('n'))} 筆 · 舊元件 {esc(lg.get('components'))}<br>元件冊 ACTIVE {esc(inv.get('active'))} · RETIRED {esc(inv.get('retired'))}<br>{esc(inv.get('counts'))}</div>",
             "</div></section>",
             "<section><h2>政策庫 · 律</h2>" + table(L["laws"], ["id", "batch", "cat", "zh"]) + "<h2>Lessons-learned</h2>" + table(L["lessons"], ["id", "batch", "zh"]) + "</section>",
             "<section><h2>指令與參數(不丟失)</h2>" + table([{"cmd": c["cmd"], "aliases": "/".join(c["aliases"]), "usage": c["usage"]} for c in rg.get("cmds", [])], ["cmd", "aliases", "usage"]) + "</section>",
             "<section><h2>Deck 任務冊</h2>" + table([{"task": k, "zh": v["zh"], "net": v["net"], "argv": " ".join(Path(a).name if "/" in a or "\\" in a else a for a in v["argv"])} for k, v in s["deck"].get("tasks", {}).items()], ["task", "zh", "net", "argv"]) + "</section>",
             "<section><h2>主控台規格項</h2>" + table(s["spec"].get("items", []), ["family", "id", "zh", "glob", "verb", "params", "net", "state"]) + "</section>",
             "<section><h2>格子站</h2>" + table(s["grid"].get("stations", []), ["name", "present", "path"]) + "</section>",
             "<section><h2>未登中央編號冊的引擎家族(誠實)</h2>" + table(au["unregistered"], ["family", "newest", "dir", "surfaces"]) + "</section>",
             "<section><h2>中央冊完整但未設操作介面的內部家族(不是未註冊)</h2>" + table(au.get("interface_gaps", []), ["family", "newest", "dir"]) + "</section>",
             "<section><h2>紅項(五矩陣)</h2>" + table([{"id": i, "why": w} for i, w in (bu.get("reds") or [])], ["id", "why"]) + "</section>",
             "<section><h2>台帳尾</h2>" + table(lg.get("tail") or [], ["ts", "kind"]) + "</section>",
             "<section><h2>U/I 對接與工作流(批519;擁有者 CGC_MDL153;頁在=連、不在=ABSENT)</h2><table><tr><th>page</th><th>family</th><th>lamp</th><th>owner</th><th>refresh</th></tr>" + "".join(("<tr><td>" + (f"<a href='file:///{esc(str(p.get('path')).replace(chr(92), '/'))}'>{esc(p.get('page'))}</a>" if p.get("exists") else esc(p.get("page"))) + f"</td><td>{esc(p.get('family'))}</td><td>{esc(p.get('lamp'))}</td><td>{esc(p.get('owner'))}</td><td>{esc(p.get('refresh'))}</td></tr>") for p in ((s.get("ui_workflow") or {}).get("pages") or [])) + "</table><p>工作流最新一跑:" + esc(json.dumps(((s.get("ui_workflow") or {}).get("workflow") or {}).get("counts") or ((s.get("ui_workflow") or {}).get("workflow") or {}).get("why") or "ABSENT", ensure_ascii=False)) + " · 庫分類:" + esc(" · ".join(f"{c.get('cat')} {c.get('lamp')}" for c in ((s.get("ui_workflow") or {}).get("db") or {}).get("categories") or []) or "ABSENT") + "</p></section>",
             "<section><h2>中央治理家族(批514;擁有者 CGC_MDL150;預設 dry-run)</h2>" + "<p>" + esc(cg_cycles_line(s.get("cg_family") or {})) + "</p>" + table([{"member": k, "state": v.get("state"), "snapshot": v.get("snapshot"), "why": v.get("why")} for k, v in ((s.get("cg_family") or {}).get("members") or {}).items()], ["member", "state", "snapshot", "why"]) + "</section>",
             "</body></html>"]
    pa = s.get('panorama') or {}
    if pa:
        parts.insert(-1, "<section><h2>VRN / VDF / VATETF(舊名 VETF)最新全景實測</h2><p>" + esc(pa.get('start')) + " → " + esc(pa.get('end')) + " · " + esc(pa.get('status')) + " · 核可 " + esc(pa.get('approval')) + "</p>" + table(pa.get('results', []), ['id','family','phase','state','why']) + "</section>")
    return "".join(parts)


def write_outputs(s: dict, out_dir: Path, publish: bool) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    md, pg = onepage_md(s), page_html(s)
    (out_dir / "VIA_Handover_ONEPAGE.md").write_text(md, encoding="utf-8")
    (out_dir / "VIA_UI_CentralGovernanceConsole_v0100.html").write_text(pg, encoding="utf-8")
    (out_dir / "VCGC_latest.json").write_text(json.dumps({k: v for k, v in s.items() if k != "handover"}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    res = {"out": str(out_dir), "published": []}
    if publish:
        for dst in ((VIA / "docs" / "VIA_Handover_ONEPAGE.md"), (ROOT / "VIA_HANDOVER_LATEST.md")):
            dst.write_text(md, encoding="utf-8"); res["published"].append(str(dst))
        d2 = VIA / "supportive modules" / "ui_support" / "VIA_UI_CentralGovernanceConsole_v0100.html"
        d2.write_text(pg, encoding="utf-8"); res["published"].append(str(d2))
    return res


def status() -> int:
    s = snapshot()
    print(f"[VCGC] v{VERSION} 批{BATCH} · 唯一對接口(L20)· {s['ts']}")
    print(f"  政策庫 {s['laws']['state']}:律 {len(s['laws']['laws'])} · lessons {len(s['laws']['lessons'])} · 政策因子 {s['logic'].get('policy_rows')} 列")
    print(f"  邏輯庫 {s['logic'].get('state')}:件 {s['logic'].get('files')} · {s['logic'].get('verdicts')} · 壞後端 {s['logic'].get('broken')} · 同步 {s['logic'].get('sync')}")
    print(f"  因子庫 {s['factors'].get('state')}:{s['factors'].get('rows')} 列 {s['factors'].get('by_source')}")
    vs = s.get("vrn_system") or {}
    print(f"  VRN 系統管理 {vs.get('state')}:燈 {vs.get('lamps')} · 連結 {vs.get('links')} {vs.get('link_counts')} · 七處 {vs.get('seven_done')}/7 · {vs.get('src') or vs.get('why')}(批681;VIA 往下讀 VRN 經此口;via {s['logic'].get('via')})")
    vd = s.get("vdf_system") or {}
    vb = vd.get("bridge") or {}
    print(f"  VDF 系統管理 {vd.get('state')}:燈 {vd.get('lamps')} · 連結 {vd.get('links')} {vd.get('link_counts')} · 七處 {vd.get('seven_done')}/7 · 橋 加速器 {vb.get('accel')}/{vb.get('tails')} 網路 {vb.get('net')}/{vb.get('tails')} 真擷取 {vb.get('net_callers')} · {vd.get('src') or vd.get('why')}(側線 2026-09-21;VIA 往下讀 VDF 經此口)")
    print(f"  資料庫:庫表冊 {s['db_sheet'].get('n')} 表 · 資料家 {s['datahome'].get('state')} {s['datahome'].get('home') or s['datahome'].get('why')}")
    print(f"  引擎調度:Deck {len(s['deck'].get('tasks', {}))} 任務 · 規格 {len(s['spec'].get('items', []))} 項 · 格子 {len(s['grid'].get('stations', []))} 站 · Register {len(s['register'].get('cmds', []))} 指令")
    print(f"  多矩陣 {s['bus'].get('state')}:{s['bus'].get('counts') or s['bus'].get('why')} · profile {s['bus'].get('profile')} · RunGate {s['rungate'].get('state')} → {s['rungate'].get('install')}")
    print(f"  環境工具 {s['tools'].get('state')}:{s['tools'].get('counts') or s['tools'].get('why')}")
    print(f"  環境復原 {s['recover'].get('state')}:{s['recover'].get('restore') or s['recover'].get('why')} · 隔離境 {len(s['recover'].get('exclusive') or [])}(L24)")
    print(f"  VTMRA 家族測試閘 {s['vtmra'].get('state')}:{s['vtmra'].get('members') or s['vtmra'].get('why')}(批516;via-vtmra)")
    print(f"  中央治理家族 {s['cg_family'].get('state')}:{s['cg_family'].get('files') or s['cg_family'].get('why')} · 成員 {({k: v.get('state') for k, v in (s['cg_family'].get('members') or {}).items()}) or '-'}(批514;via-cgfamily)")
    print(f"  註冊稽核:中央冊 {s['audit'].get('inventory_active')}/{s['audit'].get('inventory_expected')} 缺 {len(s['audit'].get('inventory_missing', []))} · 家族 {s['audit']['families']} 已登 {s['audit']['registered']} 未登 {len(s['audit']['unregistered'])} · 操作介面 {s['audit'].get('interface_registered')}" + (":" + ", ".join(r['newest'] for r in s['audit']['unregistered'][:8]) if s['audit']['unregistered'] else ""))
    print(f"  台帳 {s['ledger'].get('n')} 筆 · 交接源 {s['handover'].get('src')} · 頁/一頁:via-vcgc page|onepage(落 VIA_Reports/vcgc;--publish 才入倉)")
    return 0


def _last_h2_demoted(text: str) -> str:
    """交接本文最後一個 ## 標題,依八段嵌入規則降一級(### );沒有標題=空字串(在任何頁裡都真,誠實退化)。"""
    hs = [ln for ln in text.splitlines() if ln.startswith("## ")]
    return ("### " + hs[-1][3:]) if hs else ""


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    L = laws()
    chk("① 政策庫冊掛載(≥20 律、≥8 lessons;含 L19 安裝核可 / L20 唯一對接口)", L["state"] == "OK" and len(L["laws"]) >= 20 and len(L["lessons"]) >= 8 and {x["id"] for x in L["laws"]} >= {"L19", "L20"}, f"({len(L['laws'])} 律 · {len(L['lessons'])} lessons)")
    lg = ledger()
    chk("② 自動編號註冊表(台帳 ≥1000 筆 · 類別 current · 元件)", lg["state"] == "OK" and lg["n"] >= 1000 and "引擎" in lg["categories"] and lg["components"] > 0, f"({lg.get('n')} 筆)")
    dk = deck_tasks()
    chk("③ Deck 任務冊只讀取得(≥60 任務;含 vrn_logic/fin_logic/fin_statements)", dk["state"] == "OK" and len(dk["tasks"]) >= 60 and {"vrn_logic", "fin_logic", "fin_statements"} <= set(dk["tasks"]), f"({dk['state']} · {len(dk['tasks'])})")
    sp = spec_items()
    chk("④ 主控台規格項(≥40 項;fin_statements 接引擎)", sp["state"] == "OK" and len(sp["items"]) >= 40 and any(i["id"] == "fin_statements" and i["glob"] for i in sp["items"]), f"({len(sp['items'])})")
    gr = grid_stations()
    chk("⑤ 格子站只讀取得(≥100 站;在位計數誠實)", gr["state"] == "OK" and len(gr["stations"]) >= 100, f"({gr['state']} · {len(gr['stations'])} 站 · 在位 {sum(1 for x in gr['stations'] if x['present'])})")
    rg = register_cmds()
    chk("⑥ Register 指令與用法解析(≥60 指令;via-vrnlogic/via-finstat 帶用法行;別名 邏輯庫)", rg["state"] == "OK" and len(rg["cmds"]) >= 60
        and any(c["cmd"] == "via-vrnlogic" and c["usage"] and "邏輯庫" in c["aliases"] for c in rg["cmds"]) and any(c["cmd"] == "via-finstat" and c["usage"] for c in rg["cmds"]), f"({len(rg['cmds'])})")
    mn = manager_names()
    chk("⑦ Manager 正式名稱只讀(任務 ≥50 · 引擎 ≥30)", mn["state"] == "OK" and len(mn["tasks"]) >= 50 and len(mn["engines"]) >= 30, f"({len(mn['tasks'])}/{len(mn['engines'])})")
    au = audit(dk, sp, gr, rg, mn)
    chk("⑧ 註冊稽核:家族 ≥80;本批引擎(CGC_MDL149/VDF_ENG082/SUP_MDL748/VRN_ENG082)皆在中央自動編號冊;操作介面覆蓋另列不模糊命中",
        au["families"] >= 80 and all(any(r["family"].startswith(k) and r["registered"] for r in au["rows"]) for k in ("VDF_ENG082_FinStatements", "SUP_MDL748_FinancialLogicHub", "VRN_ENG082_ExtractionLogic")),
        f"(家族 {au['families']} · 中央冊 {au['registered']} · 未登 {len(au['unregistered'])} · 介面 {au.get('interface_registered')})")
    sv = os.environ.get("VIA_RUNGATE_LATEST")
    sr = os.environ.get("VIA_INSTALL_REQUIRED_FAMILIES")
    sd = os.environ.get("VIA_RUNGATE_DIR")
    sp_pan = os.environ.get("VIA_PANORAMA_LATEST")
    with tempfile.TemporaryDirectory() as td:
        # 批567:_rungate_merged() 會掃真機器的 RUNGATE_2*.json 史,而且史優先於傳進來那份。
        # 合成檢只准驗自己合成的東西——史掃描也指進暫存夾,否則機器上有一份 24h 內的真報告就把 ⑨ 判成紅燈。
        os.environ["VIA_RUNGATE_DIR"] = td
        # 批568:panorama 是 check() 的第二個真機器來源,會把 install 直接覆蓋成 BLOCKED_PANORAMA。
        # 指到暫存夾一個不存在的檔=那道閘在合成檢裡是啞的(生產行為零變更)。
        os.environ["VIA_PANORAMA_LATEST"] = str(Path(td) / "no_panorama.json")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "none.json")
        c0 = check()
        good_family = {"verdict": "GREEN", "python": {"state": "OK"},
                       "summary": {"required_ok": 3, "required_n": 3, "engines_ok": 3, "engines_n": 3}}
        Path(td, "one.json").write_text(json.dumps({"verdict": "GREEN", "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "families": {"vrn": good_family}}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "one.json")
        os.environ["VIA_INSTALL_REQUIRED_FAMILIES"] = "vrn"  # 舊繞門形：不得縮減 L19 必驗族
        c1 = check()
        incomplete = {**good_family, "summary": {**good_family["summary"], "engines_ok": 0, "engines_n": 0}}
        Path(td, "zero.json").write_text(json.dumps({"verdict": "GREEN", "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "families": {"vdf": incomplete, "vrn": good_family}}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "zero.json")
        c2 = check()
        Path(td, "both.json").write_text(json.dumps({"verdict": "GREEN", "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "families": {"vdf": good_family, "vrn": good_family}}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "both.json")
        c3 = check()
        no_libs = {**good_family, "summary": {**good_family["summary"], "required_ok": 0, "required_n": 0}}
        Path(td, "nolibs.json").write_text(json.dumps({"verdict": "GREEN", "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "families": {"vdf": no_libs, "vrn": good_family}}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "nolibs.json")
        c_libs = check()
        malformed = {**good_family, "summary": {**good_family["summary"], "required_ok": "broken"}}
        Path(td, "malformed.json").write_text(json.dumps({"verdict": "GREEN", "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "families": {"vdf": malformed, "vrn": good_family}}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "malformed.json")
        c_bad = check()
        Path(td, "future.json").write_text(json.dumps({"verdict": "GREEN", "ts": "2099-01-01T00:00:00", "families": {"vdf": good_family, "vrn": good_family}}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "future.json")
        c_future = check()
        Path(td, "old.json").write_text(json.dumps({"verdict": "GREEN", "ts": "2020-01-01T00:00:00"}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "old.json")
        c4 = check()
        if sv is None:
            os.environ.pop("VIA_RUNGATE_LATEST", None)
        else:
            os.environ["VIA_RUNGATE_LATEST"] = sv
        if sr is None:
            os.environ.pop("VIA_INSTALL_REQUIRED_FAMILIES", None)
        else:
            os.environ["VIA_INSTALL_REQUIRED_FAMILIES"] = sr
        if sd is None:
            os.environ.pop("VIA_RUNGATE_DIR", None)
        else:
            os.environ["VIA_RUNGATE_DIR"] = sd
        if sp_pan is None:
            os.environ.pop("VIA_PANORAMA_LATEST", None)
        else:
            os.environ["VIA_PANORAMA_LATEST"] = sp_pan
        chk("⑨ 安裝核可 L19:缺報告/單族繞閘/零測站/零必要庫/壞計數/未來或過期皆 BLOCKED；VDF+VRN 完整 GREEN 且 24h 內才 INSTALL_OK",
            all(c["install"] == "BLOCKED_UNITEST" for c in (c0, c1, c2, c_libs, c_bad, c_future, c4))
            and set(c1["coverage"]) == {"vdf", "vrn"}
            and c3["install"] == "INSTALL_OK" and set(c3["coverage"]) == {"vdf", "vrn"},
            f"(缺={c0['install']} / 單族={c1['install']} / 零站={c2['install']} / 零庫={c_libs['install']} / 壞值={c_bad['install']} / 未來={c_future['install']} / 雙族={c3['install']} / 舊={c4['install']})")
        s = snapshot()
        res = write_outputs(s, Path(td) / "out", publish=False)
        md = (Path(td) / "out" / "VIA_Handover_ONEPAGE.md").read_text(encoding="utf-8")
        pg = (Path(td) / "out" / "VIA_UI_CentralGovernanceConsole_v0100.html").read_text(encoding="utf-8")
        chk("⑩ 一頁交接 + 頁(零 CDN;九主段齊;尾版詳細 handover 全文在八段;預設落暫存夾不入倉;--publish 才入倉)", not res["published"] and all(k in md for k in ("## 一 · 政策庫", "## 二 · 安裝核可", "## 五 · 指令與參數", "## 六 · 註冊稽核", "## 七 · 自動編號註冊表", "## 八 · 交接本文", "## 九 · 掉球清單"))
            and f"來源 {s['handover'].get('src')}" in md and _last_h2_demoted(s["handover"].get("text") or "") in md   # 批511:不釘固定字串,驗「尾版全文真的在八段」(最後一個 ## 標題降級後在頁裡)
            and "<script src" not in pg and "<link rel" not in pg and "Veritas Central Governance Console" in pg, f"({len(md)} 字 · 頁 {len(pg)//1024} KB)")
    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]     # 不讀自測本身的字串(LL 自我引用)
    chk("⑪ 零網路 · 預設只讀(無 requests/httpx/duckdb/SQL；元件冊只在 registry-sync --apply 明示後原子寫)",
        all(("import " + k) not in code for k in ("requests", "httpx", "duckdb")) and "CREATE " not in code
        and "registry-sync" in code and "if apply:" in code and "os.replace" in code)
    pr, bl = prompt_doc(), dropped_balls()
    gs = grid_stations()
    chk("⑫ 批508:接手提示詞(docs 尾版;含 A 開場/B 收尾/C 格式)與掉球清單(≥12 列)嵌入一頁交接 〇/九 段;格子 PYCODE/自指站標「特殊」不當缺",
        pr["state"] == "OK" and all(k in pr["text"] for k in ("## A", "## B", "## C")) and bl["state"] == "OK" and bl["n"] >= 12
        and "## 〇 · 接手提示詞" in md and "## 九 · 掉球清單" in md and not any(x["present"] is False for x in gs["stations"] if x["path"] in ("", "PYCODE")),
        f"({pr.get('src')} · {bl.get('src')} 列 {bl.get('n')} 未結 {bl.get('open')} · 格子在位 {sum(1 for x in gs['stations'] if x['present'] is True)} 特殊 {sum(1 for x in gs['stations'] if x['present'] == '特殊')})")
    inv = component_registry()
    live = live_components()
    chk("⑬ 元件自動編號冊完整覆蓋尾版引擎/模組/類別/函數/功能/短令/套件/環境；AST 零解析錯；代號穩定且只增不減",
        inv["state"] == "OK" and inv["active"] == len(live["rows"]) and not live["parse_errors"]
        and not au.get("inventory_missing") and {"engine", "module", "function", "feature", "tool", "package", "environment"} <= set(inv["counts"]),
        f"(ACTIVE {inv.get('active')}/{len(live['rows'])} · {inv.get('counts')} · parse_error {len(live['parse_errors'])} · runtime 另列 {live.get('runtime', 0)})")
    with tempfile.TemporaryDirectory() as td:
        rp = Path(td) / "inventory.json"
        p0 = registry_sync(False, rp)
        plan_wrote = rp.exists()
        p1 = registry_sync(True, rp)
        codes1 = {r["key"]: r["code"] for r in (_json(rp) or {}).get("records", [])}
        p2 = registry_sync(True, rp)
        codes2 = {r["key"]: r["code"] for r in (_json(rp) or {}).get("records", [])}
        tampered = _json(rp)
        tampered["records"][0]["source"] = "selftest/tampered"
        rp.write_text(json.dumps(tampered, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        before = rp.read_bytes()
        p3 = registry_sync(False, rp)
        chk("⑭ registry-sync 預設 PLAN 零寫且如實列變更；--apply 才建冊；第二次同步 new=0 且既有代號完全不變",
            p0["state"] == "PLAN" and not plan_wrote and p1["new"] == p1["expected"]
            and p2["new"] == 0 and codes1 == codes2 and len(codes1) == p1["expected"]
            and p3["changed"] == 1 and rp.read_bytes() == before)
    with tempfile.TemporaryDirectory() as td15:
        fp = Path(td15) / "FAMILY_latest.json"
        fp.write_text(json.dumps({"state": "PARTIAL", "ts": "2026-09-15T08:00:00", "home": "/x/VIA_CentralGovernanceFamily_b514",
                                  "files": {"members": {"console": {"state": "OK"}, "engine": {"state": "OK"}}},
                                  "members": {"console": {"state": "AMBER", "stamp": "20260915_080000"}, "router": {"state": "ABSENT", "why": "尚未跑"}}}, ensure_ascii=False), encoding="utf-8")
        _sv = os.environ.get("VIA_CGFAMILY_LATEST")
        os.environ["VIA_CGFAMILY_LATEST"] = str(fp)
        try:
            cg_ok = cg_family()
            os.environ["VIA_CGFAMILY_LATEST"] = str(Path(td15) / "none.json")
            cg_absent = cg_family()
        finally:
            if _sv is None:
                os.environ.pop("VIA_CGFAMILY_LATEST", None)
            else:
                os.environ["VIA_CGFAMILY_LATEST"] = _sv
        md15 = onepage_md({**s, "cg_family": cg_ok})
        pg15 = page_html({**s, "cg_family": cg_ok})
    chk("⑮ 批514 中央治理家族段:FAMILY_latest.json 讀成員態/成員件 md5 態;缺=ABSENT 誠實;一頁 十一段 + 頁卡/表列成員",
        cg_ok["state"] == "PARTIAL" and cg_ok["members"]["console"]["state"] == "AMBER" and cg_ok["members"]["console"]["snapshot"] == "20260915_080000"
        and cg_ok["files"] == {"console": "OK", "engine": "OK"} and cg_ok["home"] == "VIA_CentralGovernanceFamily_b514" and cg_absent["state"] == "ABSENT"
        and "## 十一 · 中央治理家族" in md15 and "console:AMBER · 20260915_080000" in md15 and "router:ABSENT" in md15 and "中央治理家族(批514" in pg15 and "20260915_080000" in pg15)
    with tempfile.TemporaryDirectory() as td16:
        fp16 = Path(td16) / "VTMRA_latest.json"
        fp16.write_text(json.dumps({"verdict": "YELLOW", "ts": "2026-09-15T18:00:00", "results": [{"id": "eng063", "state": "OK"}, {"id": "talib", "state": "ABSENT"}], "reasons": ["TA-Lib 未裝"]}, ensure_ascii=False), encoding="utf-8")
        _sv16 = os.environ.get("VIA_VTMRA_LATEST")
        os.environ["VIA_VTMRA_LATEST"] = str(fp16)
        try:
            vt_ok = vtmra()
            os.environ["VIA_VTMRA_LATEST"] = str(Path(td16) / "none.json")
            vt_absent = vtmra()
        finally:
            if _sv16 is None:
                os.environ.pop("VIA_VTMRA_LATEST", None)
            else:
                os.environ["VIA_VTMRA_LATEST"] = _sv16
        md16 = onepage_md({**s, "vtmra": vt_ok})
        pg16 = page_html({**s, "vtmra": vt_ok})
    chk("⑯ 批516 VTMRA 家族測試閘段:VTMRA_latest.json 讀判定/成員態/理由;缺=ABSENT 誠實;四段一行 + 頁卡",
        vt_ok["state"] == "YELLOW" and vt_ok["members"] == {"eng063": "OK", "talib": "ABSENT"} and vt_absent["state"] == "ABSENT"
        and "VTMRA 家族測試閘(批516" in md16 and "'talib': 'ABSENT'" in md16 and "VTMRA 家族測試閘(批516)" in pg16)
    with tempfile.TemporaryDirectory() as td17:
        D17 = Path(td17)
        now17 = datetime.now()
        fam_ok = lambda: {"verdict": "GREEN", "python": {"state": "OK"}, "summary": {"required_ok": 3, "required_n": 3, "engines_ok": 5, "engines_n": 5}}
        (D17 / "RUNGATE_20260915_080000.json").write_text(json.dumps({"ts": (now17 - timedelta(hours=6)).isoformat(timespec="seconds"), "verdict": "GREEN", "families": {"vdf": fam_ok()}}), encoding="utf-8")
        (D17 / "RUNGATE_20260915_180000.json").write_text(json.dumps({"ts": (now17 - timedelta(hours=1)).isoformat(timespec="seconds"), "verdict": "GREEN", "families": {"vrn": fam_ok()}}), encoding="utf-8")
        (D17 / "RUNGATE_latest.json").write_text((D17 / "RUNGATE_20260915_180000.json").read_text(encoding="utf-8"), encoding="utf-8")
        _sv = {k: os.environ.get(k) for k in ("VIA_RUNGATE_LATEST", "VIA_RUNGATE_DIR")}
        os.environ["VIA_RUNGATE_LATEST"] = str(D17 / "RUNGATE_latest.json"); os.environ["VIA_RUNGATE_DIR"] = str(D17)
        try:
            r17 = rungate()
            (D17 / "RUNGATE_20260915_080000.json").write_text(json.dumps({"ts": (now17 - timedelta(hours=30)).isoformat(timespec="seconds"), "verdict": "GREEN", "families": {"vdf": fam_ok()}}), encoding="utf-8")
            r17b = rungate()
        finally:
            for k, v in _sv.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    chk("⑰ 批517 安裝核可看兩族各自最新一跑(vdf 早跑+vrn 晚跑各自 GREEN=INSTALL_OK;vdf 那跑逾 24h 則 vdf 家族未測=BLOCKED)",
        r17["install"] == "INSTALL_OK" and set(r17["coverage"]) == {"vdf", "vrn"} and any(x.startswith("vdf:RUNGATE_20260915_080000") for x in r17.get("used", []))
        and r17b["install"] == "BLOCKED_UNITEST" and any("vdf" in x for x in r17b["reasons"]), f"({r17.get('used')} / {r17b.get('reasons')})")
    with tempfile.TemporaryDirectory() as td18:
        fp18 = Path(td18) / "FAMILY_latest.json"
        fp18.write_text(json.dumps({"state": "PARTIAL", "ts": "2026-09-15T12:00:00", "home": "/x/VIA_CentralGovernanceFamily_b514", "files": {"members": {}},
                                    "members": {"console": {"state": "RED", "stamp": "20260915_113543", "cycles_reading": {"ts": "2026-09-15T12:00:00", "n": 4, "live": 0, "by_zone": {"退役": 3, "收容": 1}, "verdict": "GREEN"}}}}, ensure_ascii=False), encoding="utf-8")
        _sv18 = os.environ.get("VIA_CGFAMILY_LATEST")
        os.environ["VIA_CGFAMILY_LATEST"] = str(fp18)
        try:
            cg18 = cg_family()
        finally:
            if _sv18 is None:
                os.environ.pop("VIA_CGFAMILY_LATEST", None)
            else:
                os.environ["VIA_CGFAMILY_LATEST"] = _sv18
        md18 = onepage_md({**s, "cg_family": cg18})
        pg18 = page_html({**s, "cg_family": cg18})
        md18b = onepage_md({**s, "cg_family": {**cg18, "cycles": None}})
    chk("⑱ 批518 十一段 G17 循環判讀(L38):FAMILY_latest console.cycles_reading → 圈數/活樹/分區/活樹判定一行入一頁與頁;缺=ABSENT 誠實",
        (cg18.get("cycles") or {}).get("live") == 0 and "4 圈 · 活樹 0 · 退役 3 · 收容 1 → 活樹 GREEN" in md18 and "G17 循環判讀(批518" in pg18 and "循環判讀:ABSENT" in md18b)
    with tempfile.TemporaryDirectory() as td19:
        T19 = Path(td19)
        (T19 / "uc.json").write_text(json.dumps({"ts": "2026-09-15T13:00:00", "n": 2, "by_family": {"vrn": 1, "central": 1}, "pages": [{"page": "VIA_UI_VRNControlTower_v0100.html", "family": "vrn", "lamp": "GREEN", "owner": "VRN_ENG079_ControlTower_v0100.py", "refresh": "via-vrnui", "path": str(T19 / "uc.json"), "exists": True, "fresh": True}, {"page": "GHOST.html", "family": "central", "lamp": "ABSENT", "owner": "", "refresh": "", "path": "/nope", "exists": False, "fresh": False}]}, ensure_ascii=False), encoding="utf-8")
        (T19 / "wf.json").write_text(json.dumps({"id": "vrn_logic_nlp", "verdict": "GREEN", "ts": "2026-09-15T13:01:00", "profile": "test", "counts": {"GREEN": 3}, "results": [{"id": "vrn_logic", "state": "GREEN", "why": ""}]}, ensure_ascii=False), encoding="utf-8")
        (T19 / "db.json").write_text(json.dumps({"verdict": "YELLOW", "ts": "2026-09-15T13:02:00", "n_tables": 51, "categories": [{"cat": "價量", "lamp": "GREEN", "n": 5, "newest": "2026-09-12", "worst_lag": 3}, {"cat": "籌碼", "lamp": "YELLOW", "n": 3, "newest": "2026-09-01", "worst_lag": 14}]}, ensure_ascii=False), encoding="utf-8")
        _sv19 = {k: os.environ.get(k) for k in ("VIA_UI_CONTRACT_LATEST", "VIA_WORKFLOW_LATEST", "VIA_DB_SUMMARY_LATEST")}
        try:
            os.environ["VIA_UI_CONTRACT_LATEST"] = str(T19 / "uc.json"); os.environ["VIA_WORKFLOW_LATEST"] = str(T19 / "wf.json"); os.environ["VIA_DB_SUMMARY_LATEST"] = str(T19 / "db.json")
            uw = ui_workflow()
            os.environ["VIA_UI_CONTRACT_LATEST"] = str(T19 / "none.json"); os.environ["VIA_WORKFLOW_LATEST"] = str(T19 / "none.json"); os.environ["VIA_DB_SUMMARY_LATEST"] = str(T19 / "none.json")
            uw_absent = ui_workflow()
        finally:
            for k, v in _sv19.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        md19 = onepage_md({**s, "ui_workflow": uw})
        pg19 = page_html({**s, "ui_workflow": uw})
        md19b = onepage_md({**s, "ui_workflow": uw_absent})
    chk("⑲ 批519 十二段 U/I 對接與工作流:契約頁(在=連結/不在=ABSENT)· 工作流最新一跑逐節點 · 庫分類每類一燈入一頁與頁;三件缺=ABSENT 誠實",
        uw["state"] == "OK" and uw["n"] == 2 and uw["absent"] == ["GHOST.html"] and uw["workflow"]["state"] == "GREEN" and uw["db"]["state"] == "YELLOW"
        and "## 十二 · U/I 對接與工作流" in md19 and "[GREEN] vrn · VIA_UI_VRNControlTower_v0100.html · 擁有者 VRN_ENG079_ControlTower_v0100.py · 再生 via-vrnui" in md19 and "[ABSENT] central · GHOST.html" in md19
        and "工作流最新一跑 GREEN · vrn_logic_nlp" in md19 and "價量 GREEN(表 5 最新 2026-09-12 滯後 3)" in md19 and "U/I 對接與工作流(批519" in pg19 and "<a href='file:///" in pg19 and "GHOST.html" in pg19
        and uw_absent["state"] == "ABSENT" and uw_absent["workflow"]["state"] == "ABSENT" and uw_absent["db"]["state"] == "ABSENT" and "U/I 契約 ABSENT" in md19b)
    sg = source_guard()
    chk("⑳ 批568 來源閘:⑨ 這條路(check/rungate/_rungate_merged)讀的每個真機器來源都配覆寫鍵,且自測 ⑨ 區塊每個鍵都關進沙盒",
        sg["state"] == "OK" and len(sg["keys"]) >= 3 and "VIA_PANORAMA_LATEST" in sg["keys"],
        f"(來源 {len(sg['disk'])} · 覆寫鍵 {sg['keys']} · 沒配鍵 {sg['unguarded'] or '無'} · 沒關沙盒 {sg['unsandboxed'] or '無'})")
    # ㉑ 批598:matrix 不准自己寫跑法。操作員令是「引擎請用他節省 TOKEN」——
    #    如果本段自己 subprocess 去跑 63 項,那就是又造一支匯流排。
    #    量法:matrix_run 的原始碼裡**不得出現**自己的調度迴圈,必須看得到
    #    bus.catalog / bus.matrix / rep.run_tests / rep.scan 這四個正典呼叫。
    _mx_src = ""
    try:
        import inspect as _insp
        _mx_src = _insp.getsource(matrix_run)
    except Exception:
        pass
    _need = ("bus.catalog(", "bus.matrix(", "rep.run_tests(", "rep.scan(")
    _miss = [x for x in _need if x not in _mx_src]
    chk("㉑ 批598 matrix **一行跑法都不自己寫**:四個正典呼叫齊"
        "(CGC_MDL148 catalog/matrix · CGC_MDL158 run_tests/scan),缺一個就是又造一支匯流排",
        not _miss and bool(_mx_src), f"缺 {_miss}" if _miss else "四個都在")

    # ㉒ 批598:一頁 HTML 的三個硬條件——零 CDN(第三方)· 零彈窗(腳本脈絡)·
    #    欄寬是**量出來的**不是寫死的。第三條用合成語料真跑 _mx_cols,
    #    證明「內容變寬,欄就變寬」,而且夾得住上限(一欄獨大會把整頁擠爛)。
    _w_narrow = _mx_cols([{"a": "x"}], ["a"])[0]
    _w_wide = _mx_cols([{"a": "中文字很長很長很長很長很長很長"}], ["a"])[0]
    _w_huge = _mx_cols([{"a": "x" * 500}], ["a"])[0]
    _src149 = Path(__file__).read_text(encoding="utf-8")
    _cdn = bool(re.search(r'(?:src|href)="https?://(?!127\.0\.0\.1|localhost|\[?::1)', MATRIX_CSS))
    chk("㉒ 批598 一頁契約:零 CDN · 零彈窗 · **欄寬量得出來**"
        "(窄內容窄欄、寬內容寬欄、超長夾在上限——最佳化不是讓某一欄贏,是讓整頁讀得動)",
        (not _cdn) and all(w not in MATRIX_CSS for w in ("confirm(", "alert(", "prompt("))
        and _w_narrow < _w_wide < 46 and _w_huge == 44,
        f"窄 {_w_narrow} < 寬 {_w_wide} < 上限;超長夾成 {_w_huge}")

    # ㉓ 批602:政策庫是**手維護的冊**,選填欄遲早會少一個。本批新增 L81/L82 時漏了 `cat`
    #   (既有兩條律的 cat 本來就是 null,所以「有這個欄」從來不是全體事實),
    #   結果不是那一格印不出來——是 `x['cat']` 直接 KeyError,**整台中央控管台垮、全格報紅**。
    #   釘法:把冊換成「少欄/空 cat/全欄」三種律各一條,一頁與頁都要生得出來,而且三條都不准被吞掉。
    try:
        _real_laws = laws
        def _fake_laws():
            return {"state": "OK", "src": "selftest",
                    "laws": [{"id": "LX1", "batch": "批X"},
                             {"id": "LX2", "batch": "批X", "cat": None, "zh": "空 cat"},
                             {"id": "LX3", "batch": "批X", "cat": "紀律", "zh": "全欄"}],
                    "lessons": [{"id": "LLX", "batch": "批X"}]}
        globals()["laws"] = _fake_laws
        try:
            s23 = snapshot()
            md23, pg23 = onepage_md(s23), page_html(s23)
        finally:
            globals()["laws"] = _real_laws
        chk("㉓ 政策庫選填欄缺失不得炸台(批602 實錄:新增 L81/L82 漏 `cat` → onepage/page 兩條路一起 KeyError):"
            "少欄 / 空 cat / 全欄 三種律都要生得出來,且三條都在",
            all(k in md23 for k in ("LX1", "LX2", "LX3", "LLX")) and "紀律" in md23 and len(pg23) > 1000,
            f"(md {len(md23)} 字 · 頁 {len(pg23) // 1024} KB)")
    except Exception as exc:
        fails.append("㉓"); print("  [FAIL] ㉓ 例外:", type(exc).__name__, exc)

    try:
        lo24, fa24, vs24 = logic(), factors(), vrn_system()
        m24 = _vrnsys()
        # 批686:改成**不變量**。原本 `ok_present` 裡寫著 `m24 is not None`,
        #   等於斷言「VRN 這條腿一定要在」——在沒有 VRN_SystemManager 的樹上它**永遠紅**,
        #   而那是狀態不是規格(LL332)。兩態各驗各的:在位驗署名與燈,缺席驗誠實 ABSENT。
        present24 = m24 is not None
        ok_present = (not present24) or (
            str(lo24.get("via", "")).startswith("VRN_SystemManager")
            and str(fa24.get("via", "")).startswith("VRN_SystemManager")
            and isinstance(vs24.get("lamps"), dict) and (vs24.get("links") or 0) > 0)
        ok_honest24 = present24 or all(
            x.get("state") == "ABSENT" and bool(x.get("why")) for x in (lo24, fa24, vs24))
        _saved = dict(_VRNSYS)
        _VRNSYS["mod"], _VRNSYS["why"] = None, "selftest:模擬缺席"
        try:
            lo_abs, fa_abs, vs_abs = logic(), factors(), vrn_system()
        finally:
            _VRNSYS.clear()
            _VRNSYS.update(_saved)
        ok_absent = all(x.get("state") == "ABSENT" for x in (lo_abs, fa_abs, vs_abs))
        chk("㉔ 批681 VRN 對接口:在位時 logic()/factors() 必須署名 VRN_SystemManager(VIA 往下讀 VRN 經此口)且 vrn_system 段有燈有連結;缺席時三者都 ABSENT 而不是炸、也不退回舊路",
            ok_present and ok_absent and ok_honest24,
            f"(模式 {'在位' if present24 else '缺席(誠實 ABSENT,不是紅燈)'} · via {lo24.get('via')} · 連結 {vs24.get('links')} · 缺席控 {lo_abs.get('state')}/{fa_abs.get('state')}/{vs_abs.get('state')})")
    except Exception as exc:
        fails.append("㉔"); print("  [FAIL] ㉔ 例外:", type(exc).__name__, exc)

    # ── 批682B ㉕:執行期境不進元件等式(Z79;PR #58 Codex P1)──
    _tp_saved = os.environ.get("VIA_TOOLS_PLAN_LATEST")
    try:
        with tempfile.TemporaryDirectory() as td25:
            tp25 = Path(td25) / "TOOLS_PLAN_latest.json"
            ghost = "(selftest:runtime-only-env)"
            tp25.write_text(json.dumps({"envs": [{"name": ghost}, {"name": "base"}]}, ensure_ascii=False), encoding="utf-8")
            os.environ["VIA_TOOLS_PLAN_LATEST"] = str(tp25)
            live_with = live_components()
            plan25 = registry_sync(False, Path(td25) / "inv.json")
            os.environ["VIA_TOOLS_PLAN_LATEST"] = str(Path(td25) / "no_tools_plan.json")
            live_without = live_components()
        ghost_key = f"environment|{ghost}"
        chk("㉕ 批682B 執行期境不進元件等式:TOOLS_PLAN 來的境標 runtime 另列,不進 rows、不進 registry-sync 新增;有沒有那份檔活元件數一樣(兩台機器不再互翻);冊上已有的境(base)不重列",
            ghost_key not in {r["key"] for r in live_with["rows"]}
            and any(r["key"] == ghost_key and r.get("runtime") for r in live_with["runtime_rows"])
            and live_with["runtime"] == 1
            and ghost_key not in plan25["new_keys"]
            and len(live_with["rows"]) == len(live_without["rows"]) and live_without["runtime"] == 0,
            f"(runtime 另列 {live_with['runtime']} · rows 有檔 {len(live_with['rows'])} / 無檔 {len(live_without['rows'])} · plan 新 {plan25['new']})")
    except Exception as exc:
        fails.append("㉕"); print("  [FAIL] ㉕ 例外:", type(exc).__name__, exc)
    finally:
        if _tp_saved is None:
            os.environ.pop("VIA_TOOLS_PLAN_LATEST", None)
        else:
            os.environ["VIA_TOOLS_PLAN_LATEST"] = _tp_saved

    try:
        vd26 = vdf_system()
        m26 = _vdfsys()
        # 批686:同 ㉔,改成**不變量**。原式要求 `m26 is not None` + `VDF_SystemManager in _tail_files()`,
        #   於是在本線(VDF_SystemManager 只在側線分支)它**永遠紅**——那是狀態不是規格(LL332)。
        #   「尺有沒有含 VDF 根目錄」與對接口在不在無關,所以它維持無條件斷言。
        present26 = m26 is not None
        ok_glob26 = any(d == "functional modules/VDF" for d, _ in ENGINE_GLOBS)
        ok_present = (not present26) or (
            isinstance(vd26.get("lamps"), dict) and len(vd26["lamps"]) == 9 and (vd26.get("links") or 0) > 0
            and isinstance(vd26.get("seven"), dict) and len(vd26["seven"]) == 7
            and isinstance((vd26.get("bridge") or {}).get("tails"), int)
            and "VDF_SystemManager" in _tail_files())
        ok_honest26 = present26 or (vd26.get("state") == "ABSENT" and bool(vd26.get("why")))
        _saved = dict(_VDFSYS)
        _VDFSYS["mod"], _VDFSYS["why"] = None, "selftest:模擬缺席"
        try:
            vd_abs = vdf_system()
        finally:
            _VDFSYS.clear()
            _VDFSYS.update(_saved)
        chk("㉖ 側線 2026-09-21 VDF 對接口:在位時 vdf_system 段九盞燈、有連結、七處為七鍵、橋律量得出尾版數,且 VDF 根目錄尾版件入尺(VDF_SystemManager 是受治理家族);缺席時 ABSENT 而不是炸、也不退回舊路",
            ok_glob26 and ok_present and ok_honest26 and vd_abs.get("state") == "ABSENT",
            f"(模式 {'在位' if present26 else '缺席(誠實 ABSENT,不是紅燈)'} · 尺含 VDF 根 {ok_glob26} · 燈 {list((vd26.get('lamps') or {}).keys())} · 連結 {vd26.get('links')} · 橋 {(vd26.get('bridge') or {}).get('accel')}/{(vd26.get('bridge') or {}).get('net')}/{(vd26.get('bridge') or {}).get('tails')} · 缺席態 {vd_abs.get('state')})")
    except Exception as exc:
        fails.append("㉖"); print("  [FAIL] ㉖ 例外:", type(exc).__name__, exc)

    # ── 批686:VIA 往下只准有**一扇門**。批681 接 VRN、側線接 VDF,兩段是逐字複製貼上;
    #   再照抄一份給 VAP 就是第三顆頭。㉗ 用 AST 釘住「三家走的是同一把尺」——
    #   哪天有人手癢再抄一份載入器,這一檢當場紅。
    import ast as _a
    _selfsrc = open(__file__, encoding="utf-8").read()
    _tree = _a.parse(_selfsrc)
    def _calls_of(_fn):
        return {c.func.id for c in _a.walk(_fn) if isinstance(c, _a.Call) and isinstance(c.func, _a.Name)}
    _shell, _secs = {}, {}
    for _n in _tree.body:
        if isinstance(_n, _a.FunctionDef) and _n.name in ("_vrnsys", "_vdfsys", "_vapsys"):
            _shell[_n.name] = "_subsys" in _calls_of(_n)
        if isinstance(_n, _a.FunctionDef) and _n.name in ("vrn_system", "vdf_system", "vap_system"):
            _secs[_n.name] = "_subsys_section" in _calls_of(_n)
    chk("㉗ 批686 三家一把尺:VRN/VDF/VAP 的門一律委派 `_subsys()`、段一律委派 `_subsys_section()`,"
        "**不准有第二份載入器**(每多一家抄一份二十行,正是「VIA 東西太多」的長法;L30 / Zero-Hydra)",
        len(_shell) == 3 and all(_shell.values()) and len(_secs) == 3 and all(_secs.values()),
        f"(門 {sum(_shell.values())}/3 委派 · 段 {sum(_secs.values())}/3 委派 · 家族表 {len(SUBSYS_PORT)} 列)")
    _ss = subsystems()
    _fams = set(_ss["families"])
    _absent_ok = all(v["state"] == "ABSENT" and v["why"]
                     for v in _ss["families"].values() if not v["engine"])
    _live_ok = all(v["engine"] for v in _ss["families"].values() if v["state"] != "ABSENT")
    chk("㉘ 誠實四態:對接口缺席的家族要回 **ABSENT + 講得出因由**(缺件≠壞掉,也不准假綠);"
        "在位的家族一定要署名是哪一支引擎讀來的。三家分三欄各自報,不混成一個數字(LL327)",
        _fams == set(SUBSYS_PORT) and _absent_ok and _live_ok,
        "(" + " · ".join(f"{f}={v['state']}" + (f"/{v['engine']}" if v["engine"] else "") 
                          for f, v in _ss["families"].items()) + ")")
    # ㉙ 一扇門不准長成第二把尺(LL341/LL339)——**用 AST 釘死**:
    #    本檔頂層只准有委派用的 `tool_inventory`,不准出現 MDL178 那三把尺的實作。
    _me_src = Path(__file__).read_text(encoding="utf-8", errors="replace")
    _tops = {n.name for n in ast.parse(_me_src).body if isinstance(n, ast.FunctionDef)}
    _copied = _tops & {"inventory", "ratchet", "version_race", "shuttles",
                       "tail_modules", "_ver_blobs", "_grid_runs"}
    _ti = tool_inventory()
    _port_ok = (_ti["state"] == "ABSENT" and _ti["why"]) or (
        _ti["state"] in ("GREEN", "RED", "NODATA", "BROKEN") and _ti["src"].startswith("CGC_MDL178")
        and set(_ti["棘輪"]) >= {"態", "計"} and set(_ti["撞號"]) >= {"態", "計"})
    chk("㉙ 盤點口是**委派不是複製**:實作留在 CGC_MDL178,本檔只解析尾版 + 原樣端上來;"
        "一旦有人把 inventory/ratchet/version_race 抄進這裡就當場紅(LL341;"
        "缺席時回 ABSENT + 因由,不准自己退回舊路算一份)",
        not _copied and _port_ok,
        f"(態 {_ti['state']} · 來源 {_ti['src'] or _ti['why']} · 抄進來的實作 {sorted(_copied) or '無'})")

    # ㉚ 第三扇門同樣不准長成第二把尺(批698;釘法逐字照 ㉙)——
    #    樞紐的實作留在 CGC_MDL179,本檔只解析尾版 + 原樣端上來。
    #    而且**誠實態不准改寫**:樞紐回 GATED/FIRST_RUN/ABSENT,本台就報 GATED/FIRST_RUN/ABSENT,
    #    把它們壓成 GREEN 或 RED 都是在這裡偷偷立第二把尺。
    _h30 = sync_hub()
    _copied30 = _tops & {"reconcile", "scan_cloud_health", "conflict_copies", "cloud_only",
                         "data_plane", "function_plane", "watch_list"}
    # 括號寫清楚:`A and B or C` 的優先序很容易讓一條檢**看起來嚴、實際上寬**。
    _HONEST30 = ("GREEN", "RED", "NODATA", "ABSENT", "GATED", "SKIP", "FIRST_RUN")
    _hub_ok = (
        (_h30["state"] == "ABSENT" and bool(_h30["why"]))            # 引擎缺席:要講得出因由
        or (_h30["state"] == "BROKEN" and bool(_h30["why"]))         # 引擎壞掉:同樣要有因由
        or (_h30["src"].startswith("CGC_MDL179") and _h30["state"] in _HONEST30)
    )
    chk("㉚ 樞紐口是**委派不是複製**(批698):實作留在 CGC_MDL179,本檔只解析尾版 + 原樣端上來;"
        "誠實態原封轉呈(GATED/FIRST_RUN/ABSENT 不准被壓成 GREEN 或 RED);"
        "一旦有人把對帳/雲端掃描抄進這裡就當場紅(LL341)",
        not _copied30 and _hub_ok,
        f"(態 {_h30['state']} · 來源 {_h30['src'] or _h30['why']} · 端點 {_h30.get('端點')}"
        f" · 抄進來的實作 {sorted(_copied30) or '無'})")

    print(f"  [計] 三十檢 OK {30 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


# ===== VCGC panorama: central orchestration, no second fetch/router implementation =====
PANORAMA_MONTHS = 2
PANORAMA_BATCH_SIZE = 20
PANORAMA_STATION_TIMEOUT = 600
PANORAMA_FETCH_TIMEOUT = 7200
PANORAMA_CONTRACT = HERE / 'VIA_Panorama_Contract_v0100.json'
PANORAMA_OK = {'GREEN', 'COMPLETE', 'APPLIED', 'NOT_NEEDED'}


def def_panorama_atomic(path: Path, data: dict, indent: int = 2) -> None:
    import uuid
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=indent, default=str), encoding='utf-8')
    os.replace(tmp, path)


def def_panorama_dates(months: int = PANORAMA_MONTHS, end: str = '') -> tuple[str, str]:
    import calendar
    from datetime import date, timedelta, timezone
    if not 1 <= months <= 24:
        raise ValueError('months must be 1..24')
    # Default excludes the still-changing current Taiwan calendar day.
    hi = date.fromisoformat(end) if end else datetime.now(timezone(timedelta(hours=8))).date() - timedelta(days=1)
    n = hi.year * 12 + hi.month - 1 - months
    year, month0 = divmod(n, 12)
    lo = date(year, month0 + 1, min(hi.day, calendar.monthrange(year, month0 + 1)[1]))
    return lo.isoformat(), hi.isoformat()


def def_panorama_collect(run_dir: Path) -> list:
    """Collect existing evidence before tests overwrite latest; never re-run merely to read logs."""
    import shutil
    evidence_dir = run_dir / 'previous_evidence'
    evidence_dir.mkdir(parents=True, exist_ok=True)
    found = []
    for filename in ('ENGINE_BUS_latest.json', 'ENGINE_BUS_progress.json'):
        source = REPORTS / 'engine_bus' / filename
        data = _json(source)
        if not data:
            continue
        shutil.copy2(source, evidence_dir / filename)
        for row in data.get('results', []):
            if row.get('family') not in ('vdf', 'vrn'):
                continue
            copy = dict(row)
            log = Path(str(row.get('stdout_log') or ''))
            if row.get('stdout_log') and log.is_file() and log.resolve().is_relative_to((REPORTS / 'engine_bus').resolve()):
                shutil.copy2(log, evidence_dir / log.name)
                copy['evidence_log'] = str((evidence_dir / log.name).resolve())
                text = log.read_text(encoding='utf-8-sig', errors='replace')
                copy['failed_assertions'] = [x for x in text.splitlines() if re.match(r'^\s*\[FAIL\]', x)]
            copy['evidence_source'] = filename
            found.append(copy)
    return found


def def_panorama_resolve_dbs() -> dict:
    """Use declared central data home; ambiguous copies block writes instead of choosing newest."""
    wanted = {'prices': ('VIA_DB_VDF_TW_MARKET', 'vdf_tw_market.duckdb'),
              'etf': ('VIA_DB_ACTIVETWETF', 'ActiveTWETF.duckdb')}
    home_mod = _load('panorama_datahome', _newest(HERE, 'CGC_MDL123_DataHome_v*.py'))
    h, origin = home_mod.resolve_home(VIA)
    hd, hf = home_mod.home_dir(h)
    out = {}
    for key, (env_name, name) in wanted.items():
        explicit = os.environ.get(env_name)
        if explicit:
            candidates = [Path(explicit)]
            source = env_name
        else:
            candidates = ([hf] if hf and hf.name.lower() == name.lower() else
                          [p for p in hd.rglob('*.duckdb') if p.name.lower() == name.lower() and not home_mod._is_sandbox(str(p))] if hd.is_dir() else [])
            source = str(origin)
        candidates = list({p.resolve(): p for p in candidates if p and p.is_file()}.values())
        if len(candidates) == 1:
            out[key] = {'state': 'GREEN', 'path': str(candidates[0].resolve()), 'source': source, 'env': env_name}
        else:
            out[key] = {'state': 'BLOCKED_DB' if not candidates else 'AMBIGUOUS_DB',
                        'path': '', 'source': source, 'candidates': [str(p) for p in candidates],
                        'why': '正庫缺席或多份，須以中央資料家/明示路徑對齊；不建空白替代庫'}
    return out


def def_panorama_sync_laws(run_dir: Path, contract: dict) -> dict:
    import shutil
    path = _newest(HERE, 'VIA_Policy_Laws_SSOT_v*.json')
    data = _json(path)
    if not data:
        return {'state': 'BLOCKED', 'why': '中央政策庫缺/壞；不建立第二份政策正本'}
    changed = 0
    for field, prefix in (('laws', 'L'), ('lessons', 'LL')):
        rows = data.setdefault(field, [])
        existing_keys = {r.get('key') for r in rows}
        nums = [int(m.group(1)) for r in rows if (m := re.fullmatch(prefix + r'(\d+)', str(r.get('id', ''))))]
        counter = max(nums, default=0)
        for item in contract.get(field, []):
            if item['key'] in existing_keys:
                continue
            counter += 1
            rows.append({**item, 'id': f'{prefix}{counter:02}', 'batch': 'panorama-v0103'})
            changed += 1
    if changed:
        shutil.copy2(path, run_dir / 'policy_before.json')
        def_panorama_atomic(path, data, indent=1)
    return {'state': 'APPLIED', 'new': changed, 'path': str(path)}


def def_panorama_sync_params(run_dir: Path, contract: dict) -> dict:
    import shutil
    path = _newest(HERE, 'VIA_InputConsole_Spec_v*.json')
    data = _json(path)
    if not data:
        return {'state': 'BLOCKED', 'why': 'InputConsole 正典缺席或損壞'}
    added = 0
    found = set()
    for family in data.get('families', {}).values():
        for group in family.get('groups', []):
            for item in group.get('items', []):
                if item['id'] not in contract.get('engine_params', {}):
                    continue
                found.add(item['id'])
                params = item.setdefault('params', [])
                for name in contract['engine_params'][item['id']]:
                    if name not in params:
                        params.append(name); added += 1
    missing = set(contract.get('engine_params', {})) - found
    if missing:
        return {'state': 'BLOCKED', 'why': '冊缺item: ' + ','.join(sorted(missing))}
    if added:
        shutil.copy2(path, run_dir / 'input_spec_before.json')
        def_panorama_atomic(path, data, indent=1)
    return {'state': 'APPLIED', 'new_params': added, 'path': str(path)}


def def_panorama_problem(row: dict, contract: dict) -> list:
    text = '\n'.join([str(row.get('why', '')), str(row.get('stdout_tail', '')),
                       *[str(x) for x in row.get('failed_assertions', [])]])
    matches = []
    for issue in contract.get('problem_types', []):
        if issue.get('pattern') and re.search(issue['pattern'], text, re.I):
            matches.append(issue['code'])
    return matches or (['TEST_ASSERTION'] if row.get('state') not in PANORAMA_OK else [])


def def_panorama_render(data: dict) -> str:
    def esc(v):
        return html.escape(str(v))
    def table(rows, cols):
        cells = ['<div class="scroll"><table><thead><tr>' + ''.join('<th>'+esc(label)+'</th>' for key,label in cols) + '</tr></thead><tbody>']
        for r in rows:
            color = 'good' if r.get('state') in PANORAMA_OK else 'bad' if r.get('state') in ('RED','ERROR') else 'pending'
            cells.append('<tr class="'+color+'">'+''.join('<td>'+esc(r.get(key,''))+'</td>' for key,label in cols)+'</tr>')
        return ''.join(cells)+'</tbody></table></div>'
    rows = data.get('results', [])
    tests = [r for r in rows if r.get('phase') == 'test']
    jobs = [r for r in rows if r.get('phase') != 'test']
    rules = data.get('contract', {}).get('problem_types', [])
    known = data.get('contract', {}).get('known_findings', [])
    prior = [{'id': r.get('id'), 'state':r.get('state'), 'why':'\n'.join(r.get('failed_assertions') or [r.get('why','')]),
              'stdout_log':r.get('evidence_log',r.get('stdout_log',''))} for r in data.get('previous_evidence',[]) if r.get('state') not in PANORAMA_OK and r.get('state') != 'PLAN']
    cols = [('id','項目'),('family','家族'),('phase','階段'),('state','狀態'),('seconds','秒'),('why','問題／處置'),('stdout_log','完整紀錄')]
    refresh = '<meta http-equiv="refresh" content="8">' if data.get('status') == 'RUNNING' else ''
    return '''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'''+refresh+'''<title>VIA 全景實測矩陣</title><style>
body{font:13px/1.6 "Segoe UI","Microsoft JhengHei",sans-serif;background:#f4f6f8;color:#172b3a;margin:0}header,main{max-width:1560px;margin:auto;padding:20px}header{border-bottom:3px solid #217b88}h1{font-size:23px;margin:0}h2{font-size:16px;margin-top:26px}p{margin:6px 0}.cards{display:flex;gap:10px;flex-wrap:wrap}.card{background:white;border:1px solid #dae3e9;padding:12px 18px;border-radius:7px}.card b{display:block;font-size:19px}.scroll{overflow:auto;background:white;border:1px solid #dce3e8;border-radius:6px}table{width:100%;border-collapse:collapse}th{background:#e9eff4;text-align:left;position:sticky;top:0}td,th{padding:8px 10px;border-bottom:1px solid #e3e9ed;vertical-align:top}td{white-space:pre-wrap;overflow-wrap:anywhere;max-width:650px}.bad td:first-child{border-left:4px solid #c35159}.pending td:first-child{border-left:4px solid #c69b35}.good td:first-child{border-left:4px solid #238771}input{padding:9px;border:1px solid #abbecb;border-radius:5px;width:300px;max-width:90%}summary{cursor:pointer;font-weight:600;padding:10px;background:#edf2f5}.muted{color:#5f7380}code{white-space:pre-wrap}</style>
<header><h1>VIA · VRN / VDF / VATETF(舊名 VETF)全景實測</h1><p>唯一治理入口：Veritas Central Governance Console</p><p>'''+esc(data.get('start',''))+' → '+esc(data.get('end',''))+' · 最近 '+esc(data.get('months',''))+' 個曆月 · '+esc(data.get('status',''))+'''</p><div class="cards"><div class="card">安裝核可<b>'''+esc(data.get('approval','BLOCKED'))+'''</b></div><div class="card">本輪已記錄<b>'''+str(len(rows))+'''</b></div><div class="card">待處理項目<b>'''+str(data.get('blockers',0))+'''</b></div></div></header><main>
<p class="muted">測試通過、擷取成功與資料完整分開判定。平日候選不是官方交易日曆；ETF 有快照日不代表每筆持股已完整驗證。既有欄位缺值、未扣當沖輸入、未驗證來源均保留待修。</p><input id="q" placeholder="搜尋站名、狀態、問題或解法" oninput="document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(this.value.toLowerCase()))">
<h2>本輪引擎測試</h2>'''+table(tests,cols)+'''<h2>查庫、缺口補抓、報告與環境驗收</h2>'''+table(jobs,cols)+'''<h2>已識別問題與本輪處置</h2>'''+table(known,[('code','代碼'),('state','狀態'),('finding','證據／影響'),('solution','本輪解法／下一輪')])+'''<details><summary>前次完整失敗證據</summary>'''+table(prior,[('id','站'),('state','狀態'),('why','失敗斷言'),('stdout_log','已保存紀錄')])+'''</details><details><summary>問題類型與解法手冊（類型不代表本機全部發生）</summary>'''+table(rules,[('code','類型'),('name','問題'),('solution','解法'),('auto','自動處理範圍')])+'''</details><details><summary>日期、環境與執行參數</summary><pre>'''+esc(json.dumps({k:data.get(k) for k in ('start','end','months','dbs','environments','parameters')},ensure_ascii=False,indent=2))+'''</pre></details></main></html>'''


def def_panorama_save(run_dir: Path, data: dict) -> None:
    import csv
    import uuid
    data['blockers'] = sum(r.get('state') not in PANORAMA_OK for r in data.get('results', []))
    data['updated_at'] = datetime.now().isoformat(timespec='seconds')
    def_panorama_atomic(run_dir / 'PANORAMA.json', data)
    if data.get('owns_lock'):
        def_panorama_atomic(REPORTS / 'panorama' / 'PANORAMA_latest.json', data)
    path = run_dir / 'PANORAMA.html'
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(def_panorama_render(data), encoding='utf-8')
    os.replace(tmp,path)
    cols = ['id','family','phase','state','seconds','why','stdout_log']
    with (run_dir / 'summary_matrix.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=cols,extrasaction='ignore')
        writer.writeheader(); writer.writerows(data.get('results',[]))


def def_panorama_main(args: list) -> int:
    import contextlib
    import io
    def arg(flag, default=''):
        return args[args.index(flag)+1] if flag in args else default
    months = int(arg('--months', str(PANORAMA_MONTHS)))
    start, end = def_panorama_dates(months, arg('--end'))
    station_timeout = int(arg('--timeout', str(PANORAMA_STATION_TIMEOUT)))
    fetch_timeout = int(arg('--fetch-timeout', str(PANORAMA_FETCH_TIMEOUT)))
    batch_size = int(arg('--batch-size', str(PANORAMA_BATCH_SIZE)))
    if min(station_timeout,fetch_timeout,batch_size) < 1:
        raise ValueError('timeout and batch-size must be positive')
    apply = '--apply' in args
    fetch = '--fetch' in args
    run_dir = Path(arg('--out', str(REPORTS/'panorama'/datetime.now().strftime('%Y%m%d_%H%M%S'))))
    run_dir.mkdir(parents=True,exist_ok=True)
    contract = _json(PANORAMA_CONTRACT)
    if not contract:
        raise RuntimeError('中央 panorama 契約缺席；停止，不猜動詞')
    data = {'schema':'VIA.Panorama.v1', 'status':'RUNNING','approval':'BLOCKED', 'start':start,'end':end,
            'months':months,'contract':contract,'results':[], 'owns_lock':False, 'run_dir':str(run_dir.resolve()),
            'parameters':{'apply':apply,'fetch':fetch,'batch_size':batch_size,'timeout':station_timeout,'fetch_timeout':fetch_timeout}}
    data['previous_evidence'] = def_panorama_collect(run_dir)
    bus = _load('panorama_bus', _newest(HERE,'CGC_MDL148_EngineBus_v*.py'))
    catalog_rows = [r for r in bus.catalog() if r['family'] in ('vdf','vrn')]
    data['environments'] = {f:bus.python_for(f) for f in ('vdf','vrn')}
    def record(row, phase):
        row = {**row, 'phase':phase}
        row['problem_types'] = def_panorama_problem(row,contract)
        data['results'].append(row)
        def_panorama_save(run_dir,data)
        print(f"[PANORAMA] {row.get('id')} · {row.get('state')} · {row.get('why','')}",flush=True)
        return row
    def call(item, params=None, phase='test', timeout=station_timeout):
        try:
            r = bus.call(item,params=params,timeout=timeout,apply=apply,catalog_rows=catalog_rows,
                         profile='test' if phase=='test' else 'run')
        except Exception as exc:
            r = {'id':item,'state':'ERROR','why':f'{type(exc).__name__}: {exc}'}
        if params and params.get('report'):
            detail = _json(Path(params['report']))
            if detail:
                if 'missing_keys' in detail:
                    summary = f"候選缺鍵 {detail['missing_keys']} · 品質缺列 {len(detail.get('quality_gaps', []))} · 抓回 {detail.get('fetched',0)} · 新插 {detail.get('inserted',0)} · {detail.get('state')}"
                else:
                    coverage = detail.get('coverage', detail)
                    summary = f"ETF {len(coverage.get('etfs', []))} 檔 · 缺快照 {sum(x.get('missing_days',0) for x in coverage.get('etfs', []))} 日格 · 快照日期覆蓋尚非成分完整性驗證"
                r['why'] = summary + ' · ' + str(r.get('why',''))
                r['detail_report'] = params['report']
        return record(r,phase)
    def delegated(name, function, phase):
        log=run_dir/(name+'.log')
        try:
            # Console progress remains visible; detailed module reports keep their own evidence.
            result=function()
            if not isinstance(result,dict):
                result={'result':result}
            log.write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
            state=result.get('verdict',result.get('state','UNKNOWN'))
            return record({'id':name,'state':state,'why':str(result.get('why','')),'stdout_log':str(log)},phase)
        except Exception as exc:
            import traceback
            log.write_text(traceback.format_exc(),encoding='utf-8')
            return record({'id':name,'state':'ERROR','why':str(exc),'stdout_log':str(log)},phase)
    lock=None
    try:
        if apply:
            lock_path=REPORTS/'panorama'/'panorama_runner.lock'
            lock_path.parent.mkdir(parents=True,exist_ok=True)
            lock=lock_path.open('a+b')
            lock.seek(0)
            if os.name=='nt':
                import msvcrt
                if not lock.read(1):
                    lock.write(b'0');lock.flush()
                lock.seek(0)
                msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            data['owns_lock']=True
        data['dbs']=def_panorama_resolve_dbs()
        for key,row in data['dbs'].items():
            record({'id':'db_'+key,**row},'database')
            if row['state']=='GREEN':
                os.environ[row['env']]=row['path']
        if apply:
            for fam,env in data['environments'].items():
                parents=Path(env['python']).parents
                formal=any(p.name.lower().startswith('via_') for p in list(parents)[:3])
                if not formal or not Path(env['python']).is_file():
                    record({'id':'env_'+fam,'state':'BLOCKED_ENV','why':'非正式 via_ 家族境：'+str(env)},'environment')
            if any(r['state']=='BLOCKED_ENV' for r in data['results']):
                return 2
            delegated('policy_append',lambda:def_panorama_sync_laws(run_dir,contract),'governance')
            delegated('input_params',lambda:def_panorama_sync_params(run_dir,contract),'governance')
            delegated('registry_sync',lambda:registry_sync(apply=True),'governance')
            catalog_rows = [r for r in bus.catalog() if r['family'] in ('vdf','vrn')]
        # Run all independent test stations; a failed VRN station never hides VDF/VETF results.
        tested={}
        for row in catalog_rows:
            tested[row['id']]=call(row['id'])
        if apply:
            tests=list(tested.values())
            counts={st:sum(r.get('state')==st for r in tests) for st in {r.get('state') for r in tests}}
            def_panorama_atomic(REPORTS/'engine_bus'/'ENGINE_BUS_latest.json',{'schema':'VIA.EngineBus.v2','profile':'test','ts':datetime.now().isoformat(timespec='seconds'),'results':tests,'catalog':catalog_rows,'counts':counts,'family':'vdf,vrn','apply':True,'apply_families':['vdf','vrn'],'ids':[],'live_n':len(tests),'census':bus._census_block()})
        if not apply:
            record({'id':'workstation_execution','state':'NOT_EXECUTED','why':'唯讀預覽；未啟動家族引擎或網路'},'execution')
            return 2
        # Always inspect the DB before deciding whether to fetch, even on later rounds.
        for item,key in (('tw_history','prices'),('etf_holdings_daily','etf')):
            if data['dbs'][key]['state']!='GREEN':
                record({'id':item+'_gap','state':'BLOCKED_DEPENDENCY','why':'正庫尚未唯一定位'},'gap')
                continue
            params={'gap-mode':'plan','start':start,'end':end,'report':str(run_dir/(item+'_gap_before.json'))}
            if key=='prices':
                params['db']=data['dbs'][key]['path']
            plan=call(item,params,'gap')
            if fetch and tested.get(item,{}).get('state')=='GREEN' and plan.get('state')=='GREEN':
                params.update({'gap-mode':'fetch','report':str(run_dir/(item+'_gap_after.json'))})
                if key=='prices':
                    params['batch-size']=str(batch_size)
                else:
                    params['max-days']='0'
                call(item,params,'fetch',fetch_timeout)
            elif fetch:
                record({'id':item+'_fetch','state':'BLOCKED_DEPENDENCY','why':'對應自測或查庫未通過，保留待下一輪'},'fetch')
        # No speculative fetch of unbounded lanes: declare uncovered scope explicitly.
        for item in contract.get('deferred_fetch',[]):
            record({'id':item['id'],'family':'vdf','state':'DEFERRED','why':item['why']},'next_round')
        vrn=[r for key,r in tested.items() if r.get('family')=='vrn']
        if vrn and all(r.get('state')=='GREEN' for r in vrn) and data['dbs']['prices']['state']=='GREEN':
            closing=_load('panorama_closeout',_newest(HERE,'CGC_MDL141_ClosingGate_v*.py'))
            delegated('vrn_real_reports',lambda:closing.closeout('vrn',run=True,
                      report_dir=arg('--input-dir',str(VIA/'functional modules/VRN/input/incoming')),
                      db=Path(data['dbs']['prices']['path'])),'real_reports')
        else:
            record({'id':'vrn_real_reports','family':'vrn','state':'BLOCKED_DEPENDENCY',
                    'why':'VRN 自測或正庫未通過；完整失敗斷言已保存，未假報原始報告通過'},'real_reports')
        gate=_load('panorama_rungate',_newest(HERE,'CGC_MDL137_RunGate_v*.py'))
        delegated('environment_gate',lambda:gate.run(['vdf','vrn'],mode='fast'),'environment')
        try:
            def_panorama_save(run_dir,data)
            write_outputs(snapshot(),OUTDIR,publish=True)
        except Exception as exc:
            record({'id':'handover','state':'ERROR','why':str(exc)},'governance')
    except Exception as exc:
        import traceback
        (run_dir/'fatal.log').write_text(traceback.format_exc(),encoding='utf-8')
        record({'id':'panorama','state':'ERROR','why':str(exc),'stdout_log':str(run_dir/'fatal.log')},'execution')
    finally:
        data['status']='FINISHED'
        data['approval']='BLOCKED'
        def_panorama_save(run_dir,data)
        # Existing L19 check remains authoritative and is never overwritten to green.
        data['gate']=check()
        if not data['blockers'] and data['gate'].get('install')=='INSTALL_OK':
            data['approval']='INSTALL_OK'
        def_panorama_save(run_dir,data)
        if apply and data.get('owns_lock'):
            try:
                write_outputs(snapshot(),OUTDIR,publish=True)
            except Exception as exc:
                (run_dir/'handover_error.txt').write_text(str(exc),encoding='utf-8')
        if lock is not None:
            lock.close()
        print('[PANORAMA_REPORT] '+str((run_dir/'PANORAMA.html').resolve()),flush=True)
    return 0 if data['approval']=='INSTALL_OK' else 2


# ================================================================== 批598:矩陣控制台(matrix)
#
# 操作員令:「在中央管理系統設一個管理啟動各子系統及引擎及設定參數的指令,透過他們啟動
#            或單獨啟動,測試矩陣化管理;AI 啟動他們看結果,錯誤顯示於一頁 HTML;
#            已經內建指令全景式修復工具,引擎請用他節省 TOKEN」。
#
# 所以本段**一行跑法都不自己寫**,只做一件事:**把既有正典串起來,合成一頁**。
#   子系統/引擎/參數冊 · 啟動 · 單獨啟動 → CGC_MDL148 EngineBus(catalog / matrix)
#   引擎檢查邏輯的誠實四態             → CGC_MDL158 全景稽核修復(run_tests / judge)
#   全景式修復候選                     → CGC_MDL158 scan(**只列不修**;修要另外明點)
#   頁頭/主題令牌/頁腳                 → SUP_MDL750 Veritas 正典頁頭件(U/I 統一閘的正本)
# 全部**尾版律 import**,不寫死版號(L79);缺席**大聲拋**不 graceful(LL151)。
#
MATRIX_PAGE = OUTDIR / "VIA_UI_MatrixControl_v0100.html"
_MX_CANON = {
    "bus": ("supportive modules/registry", "CGC_MDL148_EngineBus_v*.py"),
    "repair": ("supportive modules/registry", "CGC_MDL158_VIAPanoramaAuditRepair_v*.py"),
    "uihead": ("supportive modules/ui_support", "SUP_MDL750_VeritasUIHead_v*.py"),
}


def _mx_load(key: str):
    """尾版律載入正典;缺席大聲拋(L79 律②:正典不在就別假裝有)。"""
    d, g = _MX_CANON[key]
    hits = sorted((VIA / d).glob(g))
    if not hits:
        raise RuntimeError(f"[FAIL] 正典缺席:{d}/{g}(批598 不提供 graceful 退路)")
    spec = importlib.util.spec_from_file_location(hits[-1].stem, hits[-1])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[hits[-1].stem] = mod
    spec.loader.exec_module(mod)
    return mod, hits[-1].name


def _mx_w(s) -> int:
    """顯示寬度(CJK 算 2 格)——欄寬要照**看得到的寬度**算,不是照字元數。"""
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in str(s))


def _mx_cols(rows: list, keys: list, lo: int = 6, hi: int = 44) -> list:
    """逐欄量**實際內容**的最大顯示寬度,夾在 [lo, hi] → 這就是「自動調節欄寬」。

    不是猜的:標題與每一格都量過取最大。夾上限是因為一格塞 200 字的欄會把其他欄
    擠成一條線——**最佳化不是讓某一欄贏,是讓整頁讀得動**。
    """
    out = []
    for k in keys:
        w = _mx_w(k)
        for r in rows:
            w = max(w, _mx_w(r.get(k, "")))
        out.append(max(lo, min(hi, w + 2)))
    return out


_MX_LAMP = {"GREEN": "g", "OK": "g", "在位": "g", "RED": "r", "FAIL": "r", "TIMEOUT": "r",
            "NODATA": "y", "YELLOW": "y", "PARTIAL": "y", "ABSENT": "a", "缺": "a",
            "GATED": "a", "SKIP": "a", "PLAN": "p"}
_MX_BAD = {"RED", "FAIL", "TIMEOUT"}
_MX_MID = {"NODATA", "YELLOW", "PARTIAL"}


def _mx_table(title: str, rows: list, keys: list, heads: list, note: str = "") -> str:
    """一張矩陣。**壞的排前面**——錯誤要看得到,不是埋在第 80 列。"""
    rows = sorted(rows, key=lambda r: (0 if str(r.get("state", "")) in _MX_BAD
                                       else 1 if str(r.get("state", "")) in _MX_MID else 2,
                                       str(r.get(keys[0], ""))))
    n_bad = sum(1 for r in rows if str(r.get("state", "")) in _MX_BAD)
    cols = "".join(f'<col style="width:{w}ch">' for w in _mx_cols(rows, keys))
    th = "".join(f"<th>{html.escape(h)}</th>" for h in heads)
    tr = []
    for r in rows:
        st = str(r.get("state", ""))
        tds = []
        for k in keys:
            v = html.escape(str(r.get(k, "")))
            tds.append(f'<td class="lamp {_MX_LAMP.get(st, "")}">{v}</td>' if k == "state"
                       else f"<td>{v}</td>")
        tr.append(f'<tr class="{"bad" if st in _MX_BAD else ""}">' + "".join(tds) + "</tr>")
    head = (f"<h2>{html.escape(title)} <span class=\"chip{' bad' if n_bad else ''}\">"
            f"{n_bad} 紅 / {len(rows)} 列</span></h2>")
    hint = f'<p class="note">{html.escape(note)}</p>' if note else ""
    return (f'<section class="card">{head}{hint}<div class="scroll"><table>'
            f"<colgroup>{cols}</colgroup><thead><tr>{th}</tr></thead>"
            f'<tbody>{"".join(tr) or "<tr><td>(空)</td></tr>"}</tbody></table></div></section>')


MATRIX_CSS = """
:root{--mx-row:1.55;--mx-gap:.9rem}
.mxwrap{display:grid;gap:var(--mx-gap);grid-template-columns:repeat(auto-fit,minmax(min(100%,30rem),1fr));align-items:start}
.mxwrap .card{border:1px solid var(--line,#d7dbe0);border-radius:10px;padding:.7rem .8rem;min-width:0}
.mxwrap h2{font-size:1rem;margin:.1rem 0 .45rem}
.mxwrap .chip{font-size:.72rem;font-weight:600;padding:.08rem .45rem;border-radius:999px;border:1px solid var(--line,#d7dbe0);margin-left:.4rem}
.mxwrap .chip.bad{background:#fdecec;border-color:#e6a5a5;color:#c0392b}
.mxwrap .note{font-size:.74rem;opacity:.72;margin:.1rem 0 .45rem}
.mxwrap .scroll{overflow-x:auto}
.mxwrap table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:.78rem}
.mxwrap th,.mxwrap td{border-bottom:1px solid var(--line,#e6e9ec);padding:.16rem .4rem;text-align:left;
 line-height:var(--mx-row);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mxwrap tr.bad td{background:#fff6f6}
.mxwrap tr:hover td{white-space:normal;word-break:break-word}
.mxwrap td.lamp{font-weight:700;text-align:center}
.mxwrap td.lamp.g{color:#1a7f37}.mxwrap td.lamp.r{color:#c0392b}
.mxwrap td.lamp.y{color:#b7791f}.mxwrap td.lamp.a{color:#6b7280}.mxwrap td.lamp.p{color:#2563eb}
@media (max-width:640px){.mxwrap table{font-size:.72rem}.mxwrap th,.mxwrap td{padding:.12rem .25rem}}
"""


def _mx_param_note() -> str:
    """把**參數冊現值**帶進範圍說明(批599)。

    起始日不是矩陣的旗標,它在參數庫裡(`user.group_starts`,`via-console set` 設的)。
    頁上一定要看得到現值,否則「跑了 2023-07-01 起」這句話**沒有出處**。
    """
    try:
        hits = sorted(x for x in VIA.rglob("VIA_InputConsole_Spec_v*.json")
                      if "_superseded" not in str(x) and "intake" not in str(x))
        if not hits:
            return "參數冊缺"
        d = json.loads(hits[-1].read_text(encoding="utf-8"))
        gs = (d.get("user") or {}).get("group_starts") or {}
        dflt = ((d.get("defaults") or {}).get("start")) or "?"
        return ("起始:" + (" · ".join(f"{k}={v}" for k, v in sorted(gs.items())) or "(未設群組)")
                + f" · 預設 {dflt} · 冊 {hits[-1].name}")
    except Exception as exc:
        return f"參數冊讀不開:{type(exc).__name__}"


def matrix_run(family: str = "", ids: list | None = None, engine: str = "",
               apply: bool = False, tests: bool = True, fast: bool = True,
               scan_limit: int = 0, do_print: bool = True) -> dict:
    """串既有正典,不自己重寫跑法(操作員令:引擎請用他節省 TOKEN)。"""
    import time as _t
    bus, bus_f = _mx_load("bus")
    rep, rep_f = _mx_load("repair")
    out = {"schema": "VIA.VCGC.matrix.v1", "ts": datetime.now().isoformat(timespec="seconds"),
           "canon": {"bus": bus_f, "repair": rep_f}, "apply": bool(apply),
           "scope": {"family": family or "all", "ids": ids or [], "engine": engine or "",
                     "params": _mx_param_note()}}
    # ① 子系統 × 引擎 × 參數冊(在位 ≠ 跑得動;冊自己講的)
    #   批599:`--family vdf,vrn` 一次兩家。bus.catalog() 只吃單一家族,
    #   所以這裡逐家取再串起來——**串的是正典的輸出,不是自己重查一遍冊**。
    fams = [x.strip() for x in str(family).split(",") if x.strip()]
    cat = []
    for _f in (fams or [None]):
        cat.extend(bus.catalog(_f))
    out["catalog"] = [{"id": r.get("id", ""), "family": r.get("family", ""),
                       "engine": r.get("engine") or "(缺)",
                       "verb": ",".join(r.get("verb") or []) or "-",
                       "params": ",".join(str(x) for x in (r.get("params") or [])) or "-",
                       "state": "GREEN" if r.get("engine") else "ABSENT"} for r in cat]
    # ② 啟動 / 單獨啟動(預設 PLAN:一個開關發動幾十支回補不叫方便,叫地雷)
    _res, _cnt = [], {}
    for _f in (fams or [None]):
        _sub = [r for r in cat if (not _f) or r.get("family") == _f]
        if not _sub:
            continue
        _m = bus.matrix(_f, ids=ids or None, apply=apply, do_print=False, catalog_rows=_sub)
        _res.extend(_m.get("results") or [])
        for k, v in (_m.get("counts") or {}).items():
            _cnt[k] = _cnt.get(k, 0) + v
    out["bus"] = {"counts": _cnt,
                  "rows": [{"id": r.get("id", ""), "family": r.get("family", ""),
                            "state": r.get("state", ""), "secs": r.get("seconds", ""),
                            "why": str(r.get("why") or r.get("zh") or "")[:160]}
                           for r in _res]}
    # ③ 引擎檢查邏輯:單獨測 or 全測(四態由 MDL158 的 judge 判,不自己重寫)
    if engine:
        hits = (sorted((VIA / "supportive modules" / "registry").rglob(f"*{engine}*_v*.py"))
                or sorted((VIA / "functional modules").rglob(f"*{engine}*_v*.py")))
        if not hits:
            out["tests"] = {"rows": [{"system": "-", "name": engine, "state": "ABSENT",
                                      "why": "找不到這支引擎(尾版律 glob)", "secs": 0}],
                            "tally": {"ABSENT": 1}, "verdict": "YELLOW"}
        else:
            import subprocess as _sp
            eng, t0 = hits[-1], _t.time()
            try:
                r = _sp.run([sys.executable, str(eng), "--selftest"], capture_output=True,
                            text=True, timeout=900, cwd=str(VIA), errors="replace")
                rc, so = r.returncode, (r.stdout or "") + "\n" + (r.stderr or "")
            except Exception as exc:
                rc, so = 1, f"{type(exc).__name__}: {exc}"
            st, why = rep.judge(rc, so)
            out["tests"] = {"rows": [{"system": "單測", "name": eng.name, "state": st,
                                      "why": str(why)[:160], "secs": round(_t.time() - t0, 1)}],
                            "tally": {st: 1}, "verdict": st}
    elif tests:
        t = rep.run_tests(fast=fast)
        out["tests"] = {"rows": [{"system": r["system"], "name": r["name"], "state": r["state"],
                                  "why": str(r.get("why") or "")[:160], "secs": r.get("secs", 0)}
                                 for r in t["rows"]],
                        "tally": t["tally"], "verdict": t["verdict"]}
    else:
        out["tests"] = {"rows": [], "tally": {}, "verdict": "SKIP",
                        "why": "--no-tests:本次沒測,所以這一格**不是綠的,是沒量**"}
    # ④ 全景修復候選(只列不修;要修走 via-panorama fix --apply,那是另一個明點)
    s = rep.scan(limit=scan_limit, progress=False)
    out["repair"] = {"issues": s["issues"], "files": s["files_scanned"],
                     "by_class": s.get("by_class") or {},
                     "rows": [{"file": r.get("file", ""), "cls": r.get("cls", ""),
                               "state": "RED",
                               "why": str(r.get("detail") or r.get("how") or "")[:160]}
                              for r in (s.get("rows") or [])[:60]]}
    tal = out["tests"]["tally"] or {}
    bad = (tal.get("RED", 0) + tal.get("TIMEOUT", 0)
           + sum(1 for r in out["bus"]["rows"] if r["state"] in _MX_BAD))
    out["n_bad"] = bad
    out["verdict"] = ("RED" if bad else
                      "YELLOW" if (tal.get("NODATA") or tal.get("ABSENT") or s["issues"])
                      else "GREEN")
    if do_print:
        print(f"[VCGC 矩陣] {out['verdict']} · 冊 {len(out['catalog'])} 項 · "
              f"調度 {out['bus']['counts']} · 測 {tal or '(沒測)'} · 修復候選 {s['issues']} 處 · "
              + ("真跑" if apply else "PLAN(要真跑加 --apply)"))
        print(f"  正典:{bus_f} · {rep_f}(本段一行跑法都沒自己寫)")
    return out


def matrix_page(d: dict, out: Path | None = None) -> Path:
    """一頁 HTML:多矩陣、自動欄寬、壞的排前面。頁頭走 SUP_MDL750 正本(U/I 統一閘的契約)。"""
    uih, uih_f = _mx_load("uihead")
    sc = d["scope"]
    scope_txt = (f"家族={sc['family']} · {sc.get('params', '')}\n"
                 + (f" · 點名={','.join(sc['ids'])}" if sc["ids"] else "")
                 + (f" · 單測引擎={sc['engine']}" if sc["engine"] else "")
                 + (" · 真跑" if d["apply"] else " · PLAN(預設不動手)"))
    cards = [
        _mx_table("① 子系統 × 引擎 × 參數冊", d["catalog"],
                  ["family", "id", "engine", "verb", "params", "state"],
                  ["子系統", "項", "引擎(尾版)", "動詞", "參數", "在位"],
                  "冊 = CGC_MDL148 catalog。**在位 ≠ 跑得動**,這張只說在不在。"),
        _mx_table("② 啟動矩陣(單獨啟動走 --ids)", d["bus"]["rows"],
                  ["family", "id", "state", "secs", "why"],
                  ["子系統", "項", "狀態", "秒", "因由"],
                  "調度 = CGC_MDL148 matrix。預設 PLAN;`--apply` 才真跑,"
                  "`--ids a,b` 只跑點名的(寫庫動詞只認這條路)。"),
        _mx_table("③ 引擎檢查邏輯(誠實四態)", d["tests"]["rows"],
                  ["system", "name", "state", "secs", "why"],
                  ["子系統", "引擎", "狀態", "秒", "因由"],
                  str(d["tests"].get("why") or
                      "判定 = CGC_MDL158 judge:rc 不是穩定慣例,看的是引擎自己印出來的那句話。"
                      "`--engine <名>` 可只測一支。")),
        _mx_table("④ 全景修復候選(只列不修)", d["repair"]["rows"],
                  ["file", "cls", "state", "why"], ["檔", "類", "狀態", "因由"],
                  f"掃 = CGC_MDL158 scan:{d['repair']['files']} 支活樹尾版 · "
                  f"{d['repair']['issues']} 處候選(本表只列前 60)。"
                  "要修走 `via-panorama fix --apply`——**修是另一個明點,不在這一頁按**。"),
    ]
    body = (f'<p class="note">範圍:{html.escape(scope_txt)} · 產生 {html.escape(d["ts"])}<br>'
            f"資料源(全部尾版律 import,零二次加工):"
            f'{html.escape(d["canon"]["bus"])} · {html.escape(d["canon"]["repair"])} · '
            f"{html.escape(uih_f)}</p>"
            f'<div class="mxwrap">{"".join(cards)}</div>')
    page = uih.page("VIA 矩陣控制台", body, subsystem="CGC", lamp=d["verdict"],
                    extra_css=MATRIX_CSS,
                    foot_note="本頁由 via-vcgc matrix 產;矩陣資料源=CGC_MDL148 + CGC_MDL158,"
                              "本頁不自己跑引擎、也不代修。")
    p = out or MATRIX_PAGE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(page, encoding="utf-8")
    return p


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print(f"=== Veritas Central Governance Console(CGC_MDL149 v{VERSION})· 廿九檢自測(零網路;預設只讀)===")
        return selftest()
    verb = a[0] if a else "status"
    if verb == "status":
        return status()
    if verb in ("page", "onepage"):
        s = snapshot()
        res = write_outputs(s, OUTDIR, publish="--publish" in a)
        print(f"[VCGC] 一頁交接 + 頁 → {res['out']}" + (f" · 已發佈 {res['published']}" if res["published"] else " (未入倉;--publish 才入倉)"))
        return 0
    if verb == "panorama":
        return def_panorama_main(a[1:])
    if verb == "audit":
        au = audit()
        print(f"[VCGC 註冊稽核] 中央冊 ACTIVE {au['inventory_active']}/{au['inventory_expected']} · 全類缺 {len(au['inventory_missing'])} · 家族 {au['families']} 已登 {au['registered']} 未登 {len(au['unregistered'])} · 操作介面掛載 {au['interface_registered']}")
        for r in au["unregistered"]:
            print(f"  未登 {r['newest']}({r['dir']})")
        if au["interface_gaps"]:
            print(f"  [介面分列] {len(au['interface_gaps'])} 個內部家族已在中央冊、未設操作介面(非未註冊；via-vcgc register-plan 看清單)")
        return 0
    if verb == "register-plan":
        # 中央編號冊由 registry-sync 管；此處只列尚無操作介面的內部家族，不混為「未註冊」。
        au = audit()
        OUTDIR.mkdir(parents=True, exist_ok=True)
        lines = [f"# VCGC 操作介面掛載建議 {datetime.now():%Y-%m-%d %H:%M} · 中央冊已覆蓋；無操作介面家族 {len(au['interface_gaps'])}(只列不寫)", ""]
        for r in au["interface_gaps"]:
            q = VIA / r["dir"] / r["newest"]
            has_st = False
            try:
                has_st = "--selftest" in q.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
            lines.append(f"- {r['newest']}({r['dir']})· 自測旗 {'有' if has_st else '無'} → " + (f"格子站:add(\"{r['family']} 自測\", newest(\"{r['family']}_v*.py\", VIA / \"{r['dir']}\"), [\"--selftest\"], \"rc0\", 300)" if has_st else "先補 --selftest 再登站;Deck/Register 依其動詞另議"))
        (OUTDIR / "REGISTER_PLAN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines[:30]) + (f"\n… 共 {len(lines) - 2} 條 → {OUTDIR / 'REGISTER_PLAN.md'}" if len(lines) > 30 else ""))
        return 0
    if verb == "registry-sync":
        r = registry_sync(apply="--apply" in a)
        print(f"[VCGC 元件自動編號冊] {r['state']} · 活元件 {r['expected']} · 新 {r['new']} · 變更 {r['changed']} · 退役 {r['stale']} · AST錯 {len(r['parse_errors'])} · {r['counts']}")
        if r["state"] == "PLAN":
            print("  預設零寫；確認後才用 via-vcgc registry-sync --apply")
        if r["parse_errors"]:
            for e in r["parse_errors"][:10]: print(f"  [AST錯] {e['file']}:{e['why']}")
        return 0 if not r["parse_errors"] else 2
    if verb == "matrix":
        def _v(flag: str, dflt: str = "") -> str:
            i = a.index(flag) + 1 if flag in a else -1
            return a[i] if 0 < i < len(a) and not a[i].startswith("--") else dflt
        d = matrix_run(family=_v("--family"),
                       ids=[x.strip() for x in _v("--ids").split(",") if x.strip()] or None,
                       engine=_v("--engine"),
                       apply="--apply" in a,
                       tests="--no-tests" not in a,
                       fast="--full" not in a)
        p = matrix_page(d)
        if "--json" in a:
            print(json.dumps(d, ensure_ascii=False, indent=1, default=str))
        print(f"  一頁 → {p}")
        # 誠實三態:0 綠 · 1 紅 · 2 黃(有修復候選/缺件/沒量,**不是綠的**)
        return {"GREEN": 0, "RED": 1}.get(d["verdict"], 2)
    if verb == "sync":
        h = sync_hub()
        if h["state"] in ("ABSENT", "BROKEN"):
            print(f"[VCGC 資料樞紐] {h['state']} · {h['why']}")
            return 3 if h["state"] == "ABSENT" else 1
        print(f"[VCGC 資料樞紐] {h['state']} · 來源 {h['src']}(**委派,本台不另立一把尺**)")
        print(f"  模式 {h['模式']} · 端點 {h['端點']}")
        for ep, lamps in (h["燈"] or {}).items():
            print(f"  {ep:<26} " + " · ".join(f"{k} {v}" for k, v in lamps.items()))
        for k, v in (h["委派因由"] or {}).items():
            print(f"  [委派] {k}:{v}")
        print("  界線:樞紐全唯讀——零搬移、零寫入對端、零網路。"
              "分岔只報不裁(LL90);要動手是操作員的手。")
        return {"GREEN": 0, "FIRST_RUN": 0, "RED": 1}.get(h["state"], 2)
    if verb == "inventory":
        t = tool_inventory()
        if t["state"] in ("ABSENT", "BROKEN"):
            print(f"[VCGC 工具盤點] {t['state']} · {t['why']}")
            return 3 if t["state"] == "ABSENT" else 1
        p, r, z = t["盤點"], t["棘輪"], t["撞號"]
        print(f"[VCGC 工具盤點] 來源 {t['src']}(**委派,本台不另立一把尺**)")
        print(f"  [盤點] 支援性模組 {p['模組']} · 工具短令 {p['短令']} · 缺 {p['缺']}"
              f" · 非短令另欄 {p['非短令另欄']}")
        print(f"  [梭]   無同名 .cmd {p['無同名cmd']}(寬)· **缺真梭 {p['缺真梭']}**(嚴)"
              f" · 真梭 {p['真梭']} · 撞名的獨立實作 {p['撞名']}"
              "   ← 兩個問題分兩欄,不共用一個詞(LL341)")
        print(f"  [棘輪] {r['態']} · 存證 {r['存證']} 份 · 最新 {r['最新']} · {r['計']}")
        for x in r["退步"]:
            print(f"     **退步** {x}")
        print(f"  [撞號] {z['態']} · 活線 {z['活線']} 條 · {z['計']}")
        for x in z["本線涉入"]:
            print(f"     **本線涉入** {x}(LL334:版號還給先併的那一份,裁定權在操作員)")
        print("  [律] 三欄各自報,永不相加(LL327)。")
        print(f"  [逐支名單] py \"supportive modules/registry/{t['src']}\" report"
              "   (短令 via-tools 樹上**還沒有**——加短令要改 Register 的 .ps1,"
              "那是操作員逐次許可的事(L70);指路不指到死路)")
        return 1 if t["state"] == "RED" else (2 if t["state"] == "NODATA" else 0)
    if verb == "check":
        c = check()
        print(f"[VCGC 安裝核可] {c['install']} · RunGate {c['rungate']} · 齡 {c['age_h']} h · 必驗 {c['required_families']} · {c['law']}")
        for fam, v in (c.get("coverage") or {}).items(): print(f"  [{fam}] {'GREEN' if v.get('ok') else 'BLOCK'} · {v.get('why')}")
        for why in c.get("reasons") or []: print(f"  [阻擋] {why}")
        return 0 if c["install"] == "INSTALL_OK" else 2
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
