#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_RoundAll v0111 — 一支 Python 跑完 VRN-2 一輪:取套件 → 環境診斷 → 全部自測 → 跑啟動器 → 自動修 → 除錯報告 → 收尾頁(HTML U/I)→ 貼回包。

v0111(桌機 2026-10-31 02:06 · Handle-All v0102 repair · 608 秒:⑥f 用 ConsensusJoin v0103 重跑 → 搬 38 / 43 份 · 8358 / 2891 抓到 · 4171 / 6933 / 7728 重試仍 404 →
  不納入閘 → GREEN;收尾卻 OPEN「VRN-2 1」= ⑥ Combined 冊):GFHK Apple(TICKER AAPL,不是台股 4 碼)那一列共識欄空。v0109 以前碰巧被整批摘要裡的
  「鉅亨沒有 FactSet 頁」字樣算成資料源;v0110 拿掉整批摘要的代號清單後掉進「共識缺 → VRN-2」。v0111:共識欄空、代號不是台股 4 碼 →
  「代號不是台股 4 碼 · 共識只查台股」(TICKER 有值 = 資料源 · 空白 = 人工 · 同調整後目標價的規則)。套件仍是 v0154。

v0110(桌機 2026-10-30 20:09 · Handle-All v0101 整輪 2225 秒:DUPKEY 0 · 管理器 v0257 改名 37 · 剔除 8 · 收尾 OPEN「VRN-2 2 項」= ⑥f 共識):
  · 套件 v0154(啟動器 v0154 · runtime v0154 = v0153 的 189 個成員不動 + ConsensusJoin v0103)。⑥f 第一次 43 檔 · 6933 / 7728 / 4171 回 404 →
    v0102 拿掉這三檔再跑 → 引擎 checkpoint 雜湊含代號清單 → 對不上 → 40 檔全部重抓 → 8358 / 2891 這次拿到沒有 __NEXT_DATA__ 的頁 → gate FAIL_CLOSED。
    v0103:跑引擎前把今天抓到的 payload 搬進這次清單的 checkpoint(引擎自己的函式 · 續跑不上網)· 404 / 一時抓不到先等一下重試(只重抓沒抓到的)·
    重試後仍沒有 → 404 進 no_coverage · 一時抓不到進 source_gap(黃 · 資料源)→ 拿掉再跑;Combined 那幾列寫它自己的原因。
  · 收尾頁:共識閘不過列分 404 / 一時抓不到 / 其他(同 v0103)· 一時抓不到 + 收據是 v0103 以前做的 → VRN-2(說明根因 · ⑤ 會用 v0103 重跑)·
    v0103 做的 source_gap → 資料源(鉅亨這次沒給)· 其他 → VRN-2。⑥f 的步驟列 / 共識閘 FAIL 列 / 鉅亨這次沒給 / ⑤ 修 ⑥f = 同一件事只列一次。
  · Combined 空格原因:每列看它自己(代號在 no_coverage / source_gap)· 整批摘要裡「鉅亨沒有 FactSet 頁(404)不納入閘:…」那串代號不再讓別檔也算成 404
    (桌機 6 列算成 404,其實 8358 / 2891 不是)。
  · ⑤ 自動修(新):共識閘 FAIL_CLOSED 只因 404 / 一時抓不到、而且是 ConsensusJoin v0103 以前做的 → 先把套件 runtime 的 ConsensusJoin 鏈與共識引擎
    只增不覆寫地放進 functional modules\\VRN2(核對清單雜湊 · 同名不同內容不覆寫)→ 用 v0103 重跑 ⑥f(沿用今天抓到的)→ 重組 Combined → 增量庫 / Workbench。
    v0103 也不再把上次的矩陣當這次的(引擎整批沒抓到 · 沒有 Gate 行)→ 收尾頁算資料源(網路被擋 → VCGC)。
    給 Handle-All v0102 的「repair」模式用(上一輪輸出冊是啟動器 v0153 做的 → 不整輪 · 只修 ⑥f · 幾分鐘)。

v0109(桌機 2026-10-30 18:34 · Handle-All v0100 → v0108 只重跑 ⑪b:收尾 BLOCKED · VRN-2 0 · VCGC 3 · 人工 5 · 資料源 2 · Daiwa aspeed PBR 26E → NILVAL):
  · 套件 v0153(啟動器 v0153 · runtime v0153 = v0152 的 188 個成員不動 + 管理器 VRN_SystemManager_v0257「一列一科目」):驗證器還數到 DUPKEY 45 ——
    6933 AMAX 第 8 頁兩張表並排(資產負債表 ∥ 損益表),右表的值被掛在左表科目下(流動資產 2020 = 1,331,956 又 = 3,411,492)· 凱基 2891 第 5 頁 8 筆沒有列號。
    v0257:同檔 · 頁 · 表 · 列號 · 科目 · 期間卻有不同值 → 最左邊那格留給本列科目;右邊的值取同一列自己的科目名(改名 · 註明)或移剔除冊;
    沒有列號的 → 都移剔除冊。同一個科目字在不同列(Percent of Revenues · Other adjustments)不動。這要整輪重跑(輸出冊由管理器重做)。
  · 收尾頁負責方:⑪ 獨立驗證的 DUPKEY > 0 → VRN-2(以前算人工:驗證器自己寫「錯值」);年度 FAIL 證據照舊。
  · 收尾頁同一件事只列一次(數負責方也只算一件):⑪b 與收據的 ⑪ 是同一份驗證結果 · 「四點原文核對」與「輸出缺項 · 四點原文核對」是同一批 OCR 摘錄 ·
    ⑥e 的步驟列 / last_error / MOPS 說明是同一個 MOPS DENY → 合成一列(負責方取最重的 · 燈取最差的 · 另見哪幾列寫在「為什麼」)。
  · 自測改跑管理器 v0257(它也重跑 v0255 的冪等閘測試 · 計數檔每份一個:v0255 的假引擎 3 路共用一個計數檔會互蓋 · 偶發紅)。給 Handle-All v0101 用(auto:上一輪輸出冊不是啟動器 v0153 做的 → 整輪)。

v0108(桌機 2026-10-30 17:06 · v0107 只重做報告:收尾 OPEN「VRN-2 1 項」= ⑪ 年度數據 FAIL 證據(驗證器讀法 · 原文相符)· 操作員「GENERATE A PS CODE TO HANDLE ALL」):
  · 套件 v0152(啟動器 v0152 · runtime v0152 = v0151 的 187 個成員不動 + IndependentVerifier v0114:年度 FAIL 用第二種讀法依欄位對齊 ——
    Daiwa aspeed PBR 26E 原文「Year to 31 Dec 26E 27E 28E」/「PBR (x) n.a. 29.2 16.8」→ 26E 是 n.a. = 冊值 → NILVAL;值不同 / 對不齊照樣 FAIL)。
  · ⑪b 只重跑獨立驗證(新步驟 verify · 只在 --verify 或 --only 有 verify 時跑):從套件的 runtime zip 取最新的 IndependentVerifier(核對清單雜湊)
    → 只增不覆寫地放進 functional modules\\VRN2(同名不同內容 → 紅、不覆寫;它 load 的檔缺了也一起補)→ 照啟動器 ⑪ 的方式跑(輸出冊 · scope_in · 寫回 U/I)
    → 收據的 ⑪ 換成這次的結果(先備份)。整輪 66 分鐘 → 只驗約 11 分鐘。
  · ⑥ ⑪ 驗證器版本:v0114 以前 → 黃。
  · 給 PowerShell 7 的「Handle-All」一段碼用(VRN2_HandleAll_v0100.md):full / verify / report 三種模式。

v0107(同日 · 給桌機 v0106 之前先補的兩個洞):
  · 略過取套件(--only report,closeout / --skip-package)時:v0106 只看 Downloads\\VRN2_Closeout_v0151 —— 桌機那個夾讀不到 → ① 黃 → 收尾頁又算「VRN-2 要修」。
    v0107 依序找 --package / VRN2_PACKAGE / Downloads\\<套件> / Downloads\\<套件>_<時間>(新的先)裡第一個讀得到啟動器的;這輪不跑啟動器也不自測 → 不需要套件(灰)。
  · 原套件夾讀不到時:v0106 每輪都再建一個 <套件>_<時間>(每個約 8 MB);v0107 先沿用既有的新夾(逐檔相符就直接用),都不行才建新的。

v0106(桌機 2026-10-30 14:41 跑 v0105:紅 0 · 黃 16 · 3977 秒 · ⑪ 基本資料 FAIL 0 · 年度 BADITEM 0 · 收尾 OPEN「VRN-2 2 項」):
  · 收尾頁的「VRN-2 2 項」都不是 VRN-2 的錯,是分類規則不夠細:「② CPU 忙碌 93%」= 別的程式佔 CPU(啟動器自動降路數 · 只會慢)→ 提醒;
    「⑥ Combined 冊」只因 1 格「基本資料冊代號不是 4 碼」規則認不出來 → 冊裡 TICKER 空白 = 人工核對(原文有沒有印代號)· 有值但不是台股 4 碼 = 資料源。
    Combined 每種空格原因列出是哪幾份檔(_files)。
  · ⑪ 年度數據 FAIL 證據(新):對每筆 FAIL 讀原 PDF 那一頁(PDFium + pdfplumber)找表頭(含該期間)與科目列,依欄位順序對齊 →
    原文該期間的值 = 冊值 → 驗證器讀法問題;≠ 冊值 → 擷取對錯欄(兩種都是 VRN-2 要修);對不齊 → 人工核對 → VRN2_FinFailEvidence_latest.json(進貼回包)。
  · ① 套件安裝不再把 Python 暫存夾整個搬進 Downloads:Python 3.13 在 Windows 建的暫存夾只給擁有者權限,搬過去權限會跟著走 —— 某次用系統管理員
    身分跑過,擁有者就變 Administrators,平常身分讀不到(桌機 icacls 對舊 zip:Access is denied)。改成在目的地正常建資料夾(繼承上一層權限)、逐檔複製。
    證據多一句:icacls 讀不到權限 → 權限不給目前使用者 · 怎麼清(以系統管理員身分 icacls /reset)。

v0105(桌機 2026-10-30 13:15 · PowerShell 7.6.9 原生一行 · RoundAll v0104 在 ① 就 Traceback 當掉):
  · ① 讀本機套件 zip(Downloads\\VRN2_Closeout_v0151\\VRN2_Closeout_v0151.zip)PermissionError [Errno 13] → v0104 整支當掉,收尾頁 / 貼回包都沒有。
    v0105:讀不到先重試(0.5 / 1 / 2 / 4 秒 —— 防毒掃描這類短暫鎖)· 還是讀不到 → 印證據(啟動器鎖 PID 還在不在 · icacls 權限 · attrib)
    → 改從 GitHub 取套件 · 原套件夾換不了(檔被鎖 / 權限)→ 裝到新夾 VRN2_Closeout_v0151_<時間>(原夾不動)· zip 副本寫不進去不算失敗。
  · 每一步都包起來:任何一步出例外 → 那一步記紅(例外類別 + 訊息 + 最後幾行)· 其他步驟照跑 · 收尾頁 / 貼回包照產生(貼回包讀不到的檔略過並記下)。
  · 收尾頁:⑥f 收據裡啟動器當時的「Combined YELLOW」在 ⑤ 重組後已過時 → 算「提醒」不算「資料源」(v0104 已知小瑕疵)· ① 讀不到 zip 的證據列進「這輪的數據」。

v0104(操作員 2026-10-29「解決剩餘系統問題 HTML U/I CLOSE OUT」· 桌機 RoundAll v0102 貼回 紅 0 黃 20):
  · 套件 v0151(啟動器 v0151 · runtime v0151 = v0150 的 186 個成員不動 + IndependentVerifier v0113)。
  · 驗證器 v0113(⑪):年度數據 BADITEM 19(MS-3665 / MS-8358 / MS-8210 / Daiwa aspeed ·「ModelWare net inc (NT $ mn)」「Prior EPS (NT$)**」「DPS」,
    值都在該頁)只有字元框讀法說「科目本頁原文沒有」—— 跟 v0112 修的側欄同一個讀法;現在先用第二種讀法(PDFium 整頁文字 + pdfplumber 文字行)找科目
    (整個科目 · 折行 · 兩個字以上的科目字依序在三列內)才判 BADITEM;造假 / 改名的科目兩種讀法都找不到 → 照樣 BADITEM,註記帶原文最像的那一列。
  · ⑧ 收尾頁(新):VIA_Reports\\vrn2\\VRN2_CloseoutUI_latest.html(+ .json)—— 每一列非綠結果判負責方:VRN-2 要修 / 交 VCGC / 人工核對 /
    資料源沒有 / 提醒(不擋)/ 彙總;結案狀態 OPEN(VRN-2 還有要修)> BLOCKED(等 VCGC)> REVIEW(等人工)> DATA_GAP(外部來源沒有 · 已附證據)> PASS。
    BLOCKED / REVIEW / DATA_GAP 都不是成功;認不出來的一律算 VRN-2(寧可未結案)。頁面:燈號數 · 結案判定 · 待辦表(依負責方篩 · 搜尋)· 這輪數據 ·
    檔案連結(Workbench / U/I / 貼回包 / 收據 / 驗證摘要 / 證據 / 品質矩陣)· 下次指令(一鍵複製)· 不連外 · 淺 / 深色。跑完在 Windows 自動開(--no-open / VRN2_NO_UI=1 不開)。
  · ⑥ Combined 冊空格照原因分:原文沒有目標價(不是缺)· 沒有市場資料 · 報告日前沒有日資料 · 鉅亨沒有這檔 FactSet 頁(404)· 共識有這檔但來源沒有這欄;
    只剩「原文沒有目標價」= 綠(v0103 把報告本來就沒有目標價的 15 列也算成缺)。
  · ⑥ ⑪ 驗證器版本:v0113 以前 → 黃(BADITEM 只用字元框讀法)。

v0103(桌機 2026-10-29 19:00 跑 v0102 的貼回 · 紅 0 黃 20 · 5957 秒 · rc 2):3014TT 第 3 點 / SyntaxWarning / ⑥e 選錯 Python 都好了;這輪修:
  · 套件 v0150(啟動器 v0150 · runtime v0150 = v0149 的 184 個成員不動 + IndependentVerifier v0112 · ConsensusJoin v0102)。
  · ⑤ 不再重抓 ⑥e:啟動器 v0149 已經用合 VDF 界線的 Python(MarketFetchRun)抓過,但它的明細寫「Python 本行程」,v0102 誤判成「用錯 Python」
    又整輪重抓一次(約 35 分鐘、結果一樣)。收據 ⑥e 有 runner(經 MarketFetchRun 跑)就不重抓。
  · ⑥ ⑪ 基本資料 FAIL 證據改成逐值:每個冊值(現價 / 目標價 / 上漲空間)各列原 PDF 前 4 頁「數字相等」的行(不是字串包含 —— v0102 把 38 對到 4388、
    730 對到電話 2730-2869),跳過 Email / 電話行;沒有就寫「前 4 頁沒有這個數」。
  · ⑥ ⑥e 財報被拒的說明:last_error 有「Existing VIA network bridge denied this request」= VDF 引擎打 MOPS 財報時,VIA 鎖版網路工具的合規層回 DENY;
    VDF / VRN-2 照規則不繞 → 沒有歷史財報 → ⑬b「無歷史」。要不要放行是 VCGC(網路工具)的決定。
  · ③ 自測:ConsensusJoin v0101 → v0102(鉅亨沒有 FactSet 頁的 404 代號不納入閘)。
  · 驗證器 v0112(⑪ · 在 VIA 樹裡跑):MS-6669 3510 / MS-3661 3190 的現價 FAIL 是字元框讀法漏讀 / 配錯側欄 —— 冊值就等於原文
    「Shr price, close (…) NT$3,510.00」;字元框說不對時,換第二種讀法只看同一列的標籤(對調照樣 FAIL)。

v0102(桌機 2026-10-29 17:01 跑 v0101 的貼回 · 紅 4 黃 11 ·「我的 PS 是 7.6.9 請用一個指令完成剩餘工作完成系統」):
  · 套件 v0149(啟動器 v0149 · runtime v0149 = v0148 的 181 個成員不動 + VerbatimVerifier v0105 · IndependentVerifier v0111 · MarketFetchRun v0100)。
  · 收尾 rc 1 的唯一原因 = 四點原文核對 3014TT-20231005.pdf 第 3 點 FAIL:摘錄(pdfplumber)「…聯陽Type-」換行「C PD 至少」,PDFium 把行尾連字號寫成
    U+FFFE 並吃掉換行 →「Type\\ufffeC」;v0104 只在下一字小寫時接合、也不認 U+FFFE。VerbatimVerifier v0105 / IndependentVerifier v0111 把兩種寫法當同一段字
    (只改比對形式,冊裡的摘錄不動)· 容器用產生的 PDF 重現:v0104 FAIL · v0105 PASS。
  · ⑥e 擷取黃的根因:啟動器給 MarketFetch 的是 envs\\via_core_312(套件都在),但 MarketFetch 自己的 fetch_python() 只要 envs\\via_tw_fetch 夾在就用它 ——
    那個環境什麼都沒裝(VDF 引擎上一輪在那裡 pip 失敗)。runtime 的 VRN2_MarketFetchRun_v0100 載入共用 MarketFetch(不改不抄)、只換掉它的
    fetch_python(),換成第一個通過 VDF 引擎自己檢查的 Python(同模組 · 同 >= / < 界線,從引擎檔讀 · Python 3.11+)。都不合 → 不啟動引擎(它會自己 pip)·
    印每個候選缺什麼 + 交 VCGC 的指令(帶版本界線 · 加引號,cmd 的 < 不會被當成導向)。② 也用同一支工具診斷。
  · ⑥ 除錯多印:⑪ 基本資料 FAIL 的冊值 + 原 PDF 前 4 頁對到的行(→ VRN2_FailEvidence_latest.json · 進貼回包)· ⑪ 用的驗證器版本 ·
    ⑥f 共識閘 FAIL_CLOSED 的不過檢查列(quality_matrix.csv)· ⑥e 擷取 Python 每個候選缺什麼。
  · ③ 自測多跑 VerbatimVerifier v0105 · MarketFetchRun v0100(IndependentVerifier v0111 要 VIA 樹 → 在 ⑪ 真跑時用,⑥ 印它的版本)。
  · 本檔 docstring 的 Windows 路徑反斜線全部成對(v0101 在桌機印 SyntaxWarning: invalid escape sequence '\\l')。
  · 一行指令兩種:pwsh(PowerShell 7.x · 例 7.6.9)與 Windows PowerShell 5.1,內容相同(見 VRN2_RoundAll_v0102.md)。

v0101(桌機 2026-10-29 14:40 第一次跑 v0100 的貼回 · 紅 4 黃 10):
  · 套件 v0148(啟動器 v0148 · runtime v0148 = v0147 的 178 個成員不動 + UIAction v0110 · ConsensusJoin v0101 · HistoryAlign v0102)。
  · ② 擷取 Python 不再選退役 / 備份的環境:桌機 envs\\via_core.retired-20260914_111946 被當成 ⑥e / ⑥f 的 Python(名字有 retired / backup / bak / old /
    deprecated / archive 的夾一律略過,略過的照列)。
  · ③ 自測清單:UIAction v0109 → v0110(v0109 的自測在殼有 VIA_ROOT 時會失敗 —— 桌機就是)· ConsensusJoin v0101 · HistoryAlign v0102。
  · ⑥ 除錯報告多帶證據,貼主控台文字也看得到:四點原文核對 FAIL 的那一點的摘錄原文(摘要冊)· ⑥e 不綠時 market\\vdf\\last_error.txt 最後幾行 ·
    ⑥f Yahoo 404 的代號與上櫃 .TWO 對應數。
  · 最後印「下次怎麼跑」:用本檔的完整路徑(cmd / PowerShell 都能貼;%USERPROFILE% 只在 cmd 有效,PowerShell 要 $env:USERPROFILE)。

操作員令(2026-10-29):「generate a py code to handle all above and fix all test all debug all」。
「above」= 本輪所有需求:Workbench(雙語表頭 · 靠上 · 百萬台幣千分位 · 自動縮放 · 左欄輸出夾 · 右欄去重矩陣 + 引擎狀態 · logo)·
⑥e TWSE / TPEX / Yahoo 市場擷取 · ⑥f FactSet / YFinance 共識 → Combined 冊 · ⑬b 歷史對齊(至少一期對上才覆蓋 · 刪除區)·
⑬c 舊資料庫整合(問使用者 · 原檔不刪)· ⑬ 長線 Parquet 增量庫 · SSOT 提案。這些都在 VRN-2 套件 v0152 裡;本檔負責把它們跑起來、測過、修能修的、說清楚修不了的。

  ① 套件  :本機 Downloads\\VRN2_Closeout_v0152 的 zip 雜湊對 + 逐檔對 → 直接用;否則從 GitHub 分支(讀不到 → main)git archive 取發行夾 → 核對 SHA-256 → 解壓;
            本機套件夾有檔不對 → 整夾改名備份(不刪)再解壓。--offline 只用本機。
  ② 診斷  :VRN-2 Python(--python / VRN2_PY / 處理器設定檔記的 / 本行程)的必裝套件 · 擷取 Python(VIA_FETCH_PY / %USERPROFILE%\\envs\\via_tw_fetch)的 yfinance 等 ·
            共用夾 MarketFetch / VDF 引擎 · 啟動器鎖 · 磁碟 · 來源夾 · 輸出夾 · git。缺的只列、照印指令(VRN-2 只檢查 · 安裝交 VCGC)。
  ③ 自測  :把套件裡的 runtime zip 解到 TEMP(逐檔核對清單)· 十二支 --selftest + 啟動器 --selftest,各自限時,結果逐支列。
  ④ 跑    :ActivateVRN-2_v0152(預設不上船 VIA_VRN2_NO_PUSH=1 · --ship 才推)· 輸出逐行即時印 · 60 秒沒輸出印心跳。
  ⑤ 自動修:只做安全、可重跑、不刪資料的:擷取 Python 有套件但 ⑥e 用錯 Python → 重抓;找到有 yfinance 的 Python → 重跑 ⑥f;
            市場資料比歷史對齊新 → 重跑 ⑬b;Combined 比市場 / 共識舊 → 重組;有修 → ⑬ 增量庫補寫(v0101 補缺)→ Workbench 重渲染;
            舊資料庫待決定 → 問你(--integrate yes / no / ask / skip);過期鎖(PID 已不在)→ 清掉。收尾收據先備份成 .before_roundall.json 再標註修正。
  ⑥ 除錯  :逐步燈號 + 原因 + 下一步;四點原文核對不過的檔 / 點;輸出缺項;完成判定;冪等閘;階段耗時前三;Combined 欄序與空格數;
            Workbench 標記;市場 / 歷史對齊 / 增量庫 / 整合 / SSOT 狀態 → VIA_Reports\\vrn2\\VRN2_RoundAll_latest.json。
  ⑦ 貼回包:Downloads\\VRN2_PasteBack_<時間>.zip(整段逐字稿 · 最後 300 行 · 各收據 · Combined / 四本冊 csv · Workbench · 獨立驗證摘要)。
  ⑧ 收尾頁:VIA_Reports\\vrn2\\VRN2_CloseoutUI_latest.html(待辦依負責方 · 結案狀態 · 檔案連結 · 下次指令)· 貼回包也帶它(v0104)。
用法:python VRN2_RoundAll_v0111.py [--root <VIA 根>] [--source <報告夾>] [--integrate ask|yes|no|skip] [--no-open] [--ship]
      [--only package,preflight,selftest,run,fix,verify,report,closeout,pasteback] [--verify] [--skip-run] [--skip-selftest] [--offline] [--python <VRN-2 的 python>] · --selftest
結束碼:0 綠 · 2 黃 · 1 紅(最後一行 NEXT: [燈] …)。
[VIA:AST-CLASS] 類別 = 操作員一支入口(VRN-2 · 只用標準庫)· 入口 = 本檔 CLI
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path

# ===== 1. 參數 =====
VERSION = "v0111"
NAME = "VRN2_RoundAll"
PACKAGE = "VRN2_Closeout_v0154"
PACKAGE_SHA256 = "a74f476610b9282ec5a85c869cea914fd6933ea677bb570a4716258f0478baf7"                                   # 建置時填入 VRN2_Closeout_v0154.zip 的 SHA-256
RELEASE_REL = "VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0154"
RELEASE_JSON = "VRN2_Release_v0154.json"
BRANCH = "claude/optimistic-goodall-yhalc5"
LAUNCHER = "ActivateVRN-2_v0154.py"
RUNTIME_ZIP = "VRN2_Runtime_v0154.zip"
RUNTIME_MANIFEST = "VRN2_Runtime_v0154.json"
RECEIPT = "VRN2_Closeout_v0154.json"
SELFTESTS = (("VRN2_Workbench_v0102.py", 600), ("VRN2_HistoryAlign_v0100.py", 300), ("VRN2_HistoryAlign_v0102.py", 300), ("VRN2_DataIntegrate_v0100.py", 300), ("VRN2_DataIntegrate_v0101.py", 300),
             ("VRN2_UIAction_v0110.py", 300), ("VRN2_SSOTSync_v0101.py", 300), ("VRN2_OutputStore_v0101.py", 300), ("VRN2_ConsensusJoin_v0103.py", 900), ("VRN_SystemManager_v0257.py", 1800),
             ("VRN2_VerbatimVerifier_v0105.py", 300), ("VRN2_MarketFetchRun_v0100.py", 600))
MARKET_RUNNER = "VRN2_MarketFetchRun_v0100.py"                       # v0102:⑥e 擷取 Python 照 VDF 引擎自己的版本界線挑(runtime 裡 · 只用標準庫)
VDF_BOUNDS = ("pandas>=2.2,<3", "pyarrow>=17,<27", "duckdb>=1.1,<3", "yfinance>=0.2.54,<2", "lxml>=5,<7", "tzdata>=2024.1")   # VDF_TW_AllInOne_v039 · 實際以引擎檔為準
RETIRED_ENV = re.compile(r"retired|backup|\.bak|_bak|\bbak\b|\.old|_old|-old|deprecated|archive", re.I)   # 退役 / 備份的環境夾不當擷取 Python
SKIPPED_ENVS = []
VRN2_REQUIRED = ("pdfplumber", "pypdfium2", "PIL", "pyarrow", "pandas")
VRN2_OPTIONAL = ("duckdb", "fitz", "rapidocr_onnxruntime")
FETCH_REQUIRED = ("yfinance", "lxml", "pandas", "pyarrow", "duckdb")
COMBINED_HEAD = ["REPORT_DATE", "FILENAME", "TICKER", "YFINANCE_TICKER", "BLOOMBERG_TICKER", "NAME", "BROKER", "ANALYST", "RATING", "TARGET_PRICE", "TARGET_PRICE(ADJ)", "FACTSET_TARGET_PRICE_MEDIAN", "YFINANCE_TARGET_PRICE_MEDIAN"]
COMBINED_TAIL = ["CURRENT_PRICE_REPORT", "UPSIDE_PCT(ADJ)", "ADJ_CLOSE", "ADJ_CLOSE_BEFORE_REPORT", "TOPIC & SUMMARY", "STATUS"]
WORKBENCH_MARKS = (('id="first"', "右欄第一區(去重矩陣 + 引擎狀態)"), ('id="outfolder"', "左欄輸出檔案夾"), ("Report Date / 報告日期", "雙語表頭"), ("function fitStats", "自動縮放"), ("function unitOf", "百萬台幣換算"))
PASTE_FILES = ("VRN2_Closeout_v0154.json", "VRN2_Closeout_v0154.before_roundall.json", "VRN2_RoundAll_latest.json", "VRN2_Phase_Timing_latest.json", "VRN2_OutputStore_latest.json", "VRN2_Output_Config.json",
               "IDEMPOTENCE_latest.json", "VRN2_VerbatimVerify_latest.json", "VRN2_Completion_latest.json", "VRN2_Activate_latest.json", "VRN2_Input_latest.json", "VRN2_HistoryAlign_latest.json",
               "VRN2_Integrate_latest.json", "VRN2_Acceptance_latest.json", "market/VRN2_Market_latest.json", "consensus/VRN2_Consensus_latest.json", "VRN2_Workbench_latest.html",
               "output/VRN2_Combined_latest.csv", "output/VRN2_BasicInfo_latest.csv", "output/VRN2_Summary_latest.csv", "output/VRN2_FinancialData_latest.csv", "output/VRN2_Rejected_latest.csv",
               "output/VRN2_FinancialAligned_latest.csv", "output/VRN2_Deleted_latest.csv", "market/vdf/last_error.txt", "consensus/VRN2_YFTickerMap_latest.json",
               "VRN2_FailEvidence_latest.json", "consensus/factset_yfinance_consensus_quality_matrix.csv", "VRN2_CloseoutUI_latest.html", "VRN2_CloseoutUI_latest.json",
               "VRN2_FinFailEvidence_latest.json")
LAMP_RANK = {"GREEN": 0, "GRAY": 0, "YELLOW": 1, "RED": 2}
VCGC_FETCH_ENV = ('python -m venv "%USERPROFILE%\\envs\\via_tw_fetch"', '"%USERPROFILE%\\envs\\via_tw_fetch\\Scripts\\python.exe" -m pip install ' + " ".join('"%s"' % b for b in VDF_BOUNDS))   # v0102:帶 VDF 界線 · 加引號

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass


# ===== 2. 小工具 =====
class Tee:
    """畫面 + 逐字稿同時寫(貼回包用)。"""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.fh = self.path.open("a", encoding="utf-8")
        self.out = sys.stdout

    def write(self, text):
        try:
            self.out.write(text)
        except UnicodeEncodeError:
            self.out.write(text.encode("utf-8", "replace").decode("ascii", "replace"))
        self.fh.write(text)
        return len(text)

    def flush(self):
        self.out.flush()
        self.fh.flush()


RESULTS = []


def say(lamp: str, step: str, detail: str = "", hint: str = "") -> dict:
    """一列結果:印出 + 收進總表。"""
    row = {"lamp": lamp, "step": step, "detail": str(detail), "hint": str(hint)}
    RESULTS.append(row)
    print("[%s] %s%s%s" % (lamp, step, (" · " + str(detail)) if detail else "", ("\n       → " + str(hint)) if hint else ""), flush=True)
    return row


def info(text: str) -> None:
    print("[計] " + text, flush=True)


def worst(lamps) -> str:
    lamps = [l for l in lamps if l]
    if not lamps:
        return "GRAY"
    return max(lamps, key=lambda l: (LAMP_RANK.get(l, 1), l == "YELLOW"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


SHA_TRIES, SHA_WAIT = 5, 0.5                                          # v0105 讀不到(被鎖)重試:0.5 / 1 / 2 / 4 秒


def read_sha(path: Path) -> tuple:
    """v0105:(SHA-256, "") · 讀不到(PermissionError 等)重試 SHA_TRIES 次 → (None, 錯誤)。"""
    err = ""
    for i in range(SHA_TRIES):
        try:
            return sha256_file(path), ""
        except OSError as error:
            err = "%s: %s" % (type(error).__name__, error)
            if i < SHA_TRIES - 1:
                time.sleep(min(SHA_WAIT * 2 ** i, 4))
    return None, err


def lock_evidence(path: Path, root=None) -> str:
    """v0105 讀不到檔時的證據(只讀):啟動器鎖 PID 還在不在 · Windows 上 icacls / attrib 的輸出。"""
    bits = []
    lock = Path(root) / "VIA_Reports" / "vrn2" / "VRN2_Launcher.lock" if root else None
    if lock and lock.is_file():
        pid = (jread(lock, {}) or {}).get("pid")
        try:
            alive = pid_alive(int(pid or 0))
        except (TypeError, ValueError):
            alive = False
        bits.append("啟動器鎖 PID %s %s" % (pid, "還在跑(另一個 VRN-2 視窗沒關?)" if alive else "已不在"))
    if os.name == "nt":
        for cmd in (["icacls", str(path)], ["attrib", str(path)]):
            try:
                out = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=15).stdout
                bits.append("%s:%s%s" % (cmd[0], " ".join(l.strip() for l in out.splitlines() if l.strip())[:300], acl_hint(out, path) if cmd[0] == "icacls" else ""))
            except (OSError, subprocess.SubprocessError) as error:
                bits.append("%s 失敗 %s" % (cmd[0], type(error).__name__))
    return " · ".join(bits) or "沒有其他線索"


def acl_hint(text: str, path) -> str:
    """v0106:icacls 連權限都讀不到 → 權限不給目前的使用者(多半某次用系統管理員身分跑過 + 暫存夾權限被搬進來)· 怎麼清。"""
    if re.search(r"Access is denied|存取被拒|拒絕存取", str(text or "")):
        return (" →(權限不給目前的使用者:多半某次用系統管理員身分跑過,檔的擁有者變 Administrators。要清:以系統管理員身分開 PowerShell 跑 "
                "icacls \"%s\" /reset /T /C;不清也沒關係,本輪改從 GitHub 取)" % Path(path).parent)
    return ""


def guarded(label: str, fn, *a, default=None, **kw):
    """v0105:一步出例外 → 記紅(類別 + 訊息 + 最後幾行)· 回 default · 後面的步驟(收尾頁 / 貼回包)照跑。"""
    try:
        return fn(*a, **kw)
    except Exception as error:  # noqa: BLE001
        import traceback
        tail = [l.strip() for l in traceback.format_exc().strip().splitlines()][-4:]
        say("RED", label, "例外 %s: %s · %s" % (type(error).__name__, str(error)[:240], " | ".join(tail)[:400]),
            "RoundAll 這一步當掉了 · 其他步驟照跑 · 收尾頁 / 貼回包照產生 → 把貼回包給 AI" + ("(檔案被鎖 / 權限:先關掉佔用它的程式或等防毒掃完再跑)" if isinstance(error, PermissionError) else ""))
        return default


def jread(path: Path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return default


def stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def home() -> Path:
    return Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or str(Path.home()))


def downloads() -> Path:
    return Path(os.environ.get("VRN2_DOWNLOADS") or (home() / "Downloads"))


def is_via_root(p: Path) -> bool:
    return (Path(p) / "functional modules").is_dir() and (Path(p) / "supportive modules").is_dir()


def pid_alive(pid: int) -> bool:
    if not pid or pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes  # noqa: WPS433
            handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))
            if not handle:
                return False
            code = ctypes.c_ulong()
            ok = ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
            ctypes.windll.kernel32.CloseHandle(handle)
            return bool(ok) and code.value == 259
        except Exception:  # noqa: BLE001
            return True
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def run_stream(cmd: list, cwd=None, env=None, timeout: int = 3600, prefix: str = "    ", quiet: bool = False, heartbeat: int = 60) -> tuple:
    """子行程:逐行即時印(有前綴)· 沒輸出超過 heartbeat 秒印心跳 · 總時間超過 timeout 就停。回 (rc, 全部行)。"""
    env2 = dict(os.environ if env is None else env)
    env2.setdefault("PYTHONUTF8", "1")
    env2.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        proc = subprocess.Popen([str(c) for c in cmd], cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                text=True, encoding="utf-8", errors="replace", env=env2)
    except OSError as error:
        return 127, ["[RED] 起不來:%s: %s" % (type(error).__name__, error)]
    bucket: queue.Queue = queue.Queue()

    def pump():
        for line in proc.stdout:
            bucket.put(line)
        bucket.put(None)
    threading.Thread(target=pump, daemon=True).start()
    lines, started, last = [], time.time(), time.time()
    while True:
        try:
            line = bucket.get(timeout=5)
        except queue.Empty:
            now = time.time()
            if now - started > timeout:
                proc.kill()
                lines.append("[RED] 逾時 %d 秒 · 已停止" % timeout)
                print(prefix + lines[-1], flush=True)
                break
            if now - last > heartbeat:
                print("%s[心跳] 還在跑 · 已 %d 秒 · 最後一行:%s" % (prefix, now - started, (lines[-1] if lines else "(還沒有輸出)")[:120]), flush=True)
                last = now
            continue
        if line is None:
            break
        last = time.time()
        text = line.rstrip("\n")
        lines.append(text)
        if not quiet:
            print(prefix + text[:400], flush=True)
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
    return (proc.returncode if proc.returncode is not None else -9), lines


def probe_modules(py: str, modules) -> dict:
    """在指定 Python 裡看套件在不在(版本或 None)。"""
    code = ("import importlib.util,json,sys\nout={}\nfor m in sys.argv[1:]:\n    v=None\n    try:\n        if importlib.util.find_spec(m):\n            mod=__import__(m); v=str(getattr(mod,'__version__','ok'))\n"
            "    except Exception as e:\n        v=None\n    out[m]=v\nprint(json.dumps(out))")
    try:
        r = subprocess.run([py, "-c", code] + list(modules), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
        return json.loads((r.stdout.strip().splitlines() or ["{}"])[-1])
    except Exception:  # noqa: BLE001
        return {m: None for m in modules}


def python_version(py: str) -> str:
    try:
        r = subprocess.run([py, "-c", "import sys;print(sys.version.split()[0])"], capture_output=True, text=True, timeout=60)
        return r.stdout.strip() or "?"
    except Exception:  # noqa: BLE001
        return "起不來"


# ===== 3. 位置 =====
def registry_root():
    """vrn2:// 註冊的處理器路徑(Windows HKCU)→ VIA 根。"""
    if os.name != "nt":
        return None
    try:
        import winreg  # noqa: WPS433
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\vrn2\shell\open\command") as key:
            value = winreg.QueryValue(key, "")
        paths = re.findall(r'"([^"]+\.py)"', value)
        for p in paths:
            for parent in Path(p).parents:
                if is_via_root(parent):
                    return parent
    except OSError:
        return None
    return None


def find_root(explicit=None) -> tuple:
    tried = []

    def ok(p, how):
        if not p:
            return None
        p = Path(p)
        tried.append("%s · %s · %s" % (how, p, "是 VIA 根" if is_via_root(p) else "不是"))
        return p if is_via_root(p) else None
    for p, how in ((explicit, "--root"), (os.environ.get("VRN2_ROOT"), "VRN2_ROOT"), (os.environ.get("VIA_ROOT"), "VIA_ROOT")):
        got = ok(p, how)
        if got:
            return got, tried
    for parent in Path(__file__).resolve().parents:
        if is_via_root(parent):
            tried.append("本檔所在的倉 · %s" % parent)
            return parent, tried
    dl = downloads()
    if dl.is_dir():
        for ctx in sorted(dl.glob("VRN2_Closeout_v0*/VRN2_Runtime_Context.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            got = ok((jread(ctx, {}) or {}).get("root"), "啟動器記的 " + ctx.parent.name)
            if got:
                return got, tried
    got = ok(registry_root(), "vrn2:// 註冊")
    if got:
        return got, tried
    for base in (home() / "OneDrive" / "Documents", home() / "Documents", home(), home() / "OneDrive"):
        got = ok(base / "movies-dataset" / "VeritasIntelligenceAnalytics", "預設位置")
        if got:
            return got, tried
    return None, tried


def vrn2_python(root: Path, explicit=None) -> tuple:
    if explicit:
        return explicit, "--python"
    if os.environ.get("VRN2_PY"):
        return os.environ["VRN2_PY"], "VRN2_PY"
    cfg = jread(Path(root) / "functional modules" / "VRN2" / "VRN2_UIAction_Config.json", {}) if root else {}
    if cfg and cfg.get("python") and Path(cfg["python"]).is_file():
        return cfg["python"], "處理器設定檔(上一輪啟動器用的)"
    return sys.executable, "本行程"


def fetch_python_candidates() -> list:
    out = []
    if os.environ.get("VIA_FETCH_PY"):
        out.append(os.environ["VIA_FETCH_PY"])
    envs = home() / "envs"
    SKIPPED_ENVS.clear()
    for name in ["via_tw_fetch"] + (sorted(p.name for p in envs.iterdir() if p.is_dir() and p.name != "via_tw_fetch") if envs.is_dir() else []):
        if RETIRED_ENV.search(name):
            SKIPPED_ENVS.append(name)
            continue
        for rel in ("Scripts/python.exe", "bin/python"):
            cand = envs / name / rel
            if cand.is_file():
                out.append(str(cand))
    out.append(sys.executable)
    seen, res = set(), []
    for c in out:
        if c and c not in seen and Path(c).is_file():
            seen.add(c)
            res.append(c)
    return res


def find_fetch_python(need=FETCH_REQUIRED) -> tuple:
    """第一個裝齊 need 的 Python;都沒有 → (None, 各候選缺什麼)。"""
    report = []
    for py in fetch_python_candidates():
        got = probe_modules(py, need)
        missing = [m for m in need if not got.get(m)]
        report.append((py, missing))
        if not missing:
            return py, report
    return None, report


def runner_from_package(pkg):
    """v0102:⑥e 挑 Python 的工具(VRN2_MarketFetchRun)從套件的 runtime zip 取出 → TEMP(對清單雜湊 · 不對不用)。"""
    manifest = jread(Path(pkg) / RUNTIME_MANIFEST, {}) or {}
    want = {e.get("path"): e.get("sha256") for e in manifest.get("files") or []}.get(MARKET_RUNNER)
    try:
        with zipfile.ZipFile(Path(pkg) / RUNTIME_ZIP) as z:
            data = z.read(MARKET_RUNNER)
    except (OSError, KeyError, zipfile.BadZipFile):
        return None
    if not want or hashlib.sha256(data).hexdigest() != want:
        return None
    folder = Path(tempfile.mkdtemp(prefix="vrn2_roundall_mr_"))
    (folder / MARKET_RUNNER).write_bytes(data)
    return folder / MARKET_RUNNER


def pick_fetch_python(pkg, vpy: str, tool, preferred=None) -> dict:
    """v0102:哪個 Python 通過 VDF 引擎自己的套件檢查(同模組 · 同界線 · 3.11+)→ {python, fill_python, requirements, candidates, why}。不裝任何東西。"""
    runner = runner_from_package(pkg) if pkg else None
    if not runner:
        return {"python": None, "why": "套件 runtime 裡沒有 %s(或雜湊不對)" % MARKET_RUNNER, "candidates": [], "requirements": []}
    cmd = [vpy, "-X", "utf8", str(runner), "--tool", str(tool)] + (["--python", str(preferred)] if preferred else []) + ["--pick-python"]
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
        return json.loads((done.stdout.strip().splitlines() or ["{}"])[-1])
    except Exception as error:  # noqa: BLE001
        return {"python": None, "why": "%s: %s" % (type(error).__name__, str(error)[:160]), "candidates": [], "requirements": []}
    finally:
        shutil.rmtree(str(runner.parent), ignore_errors=True)


def vcgc_fetch_commands(bounds=None) -> list:
    """交 VCGC 建 via_tw_fetch 的指令(cmd 與 PowerShell 各一組 · 界線加引號)。"""
    pins = " ".join('"%s"' % b for b in (bounds or VDF_BOUNDS))
    return ['cmd        : python -m venv "%USERPROFILE%\\envs\\via_tw_fetch"',
            'cmd        : "%USERPROFILE%\\envs\\via_tw_fetch\\Scripts\\python.exe" -m pip install ' + pins,
            'PowerShell : python -m venv "$env:USERPROFILE\\envs\\via_tw_fetch"',
            'PowerShell : & "$env:USERPROFILE\\envs\\via_tw_fetch\\Scripts\\python.exe" -m pip install ' + pins]


# ===== 4. ① 套件 =====
def _manifest_check(folder: Path, manifest: dict) -> list:
    bad = []
    for e in manifest.get("files") or []:
        p = Path(folder) / e["path"]
        if not p.is_file() or sha256_file(p) != e["sha256"]:
            bad.append(e["path"])
    return bad


def install_package(zip_path: Path, want: str, pkg: Path, release_json=None) -> dict:
    """核對 zip 雜湊 → 解到暫存 → 逐檔核對 PACKAGE_SHA256.json → 本機套件夾不同就改名備份 → 換上。回 {lamp, detail, pkg}。"""
    got, err = read_sha(zip_path)
    if got is None:
        raise PermissionError("讀不到 %s(%s)" % (zip_path, err))
    if want and got != want:
        return {"lamp": "RED", "detail": "套件 zip SHA-256 %s ≠ 應為 %s · 不使用" % (got[:12], want[:12])}
    stage = Path(tempfile.mkdtemp(prefix="vrn2_roundall_pkg_"))
    with zipfile.ZipFile(zip_path) as z:
        for member in z.namelist():
            if member.endswith("/") or ".." in Path(member).parts or Path(member).is_absolute():
                continue
            rel = Path(*Path(member).parts[1:]) if len(Path(member).parts) > 1 else Path(member)
            target = stage / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(member))
    manifest = jread(stage / "PACKAGE_SHA256.json", {}) or {}
    bad = _manifest_check(stage, manifest)
    if bad or not manifest:
        return {"lamp": "RED", "detail": "套件解壓後逐檔核對不符:%s" % (", ".join(bad[:5]) or "沒有 PACKAGE_SHA256.json")}
    pkg = Path(pkg)
    backup = ""
    if pkg.is_dir():
        same = not _manifest_check(pkg, manifest)
        if same:
            shutil.rmtree(stage, ignore_errors=True)
            note = _copy_extras(pkg, zip_path, release_json)
            return {"lamp": "GREEN", "detail": "本機已是 %s(%d 檔逐檔相符)· %s%s" % (PACKAGE, len(manifest["files"]), pkg, note), "pkg": str(pkg)}
        backup = str(pkg) + ".bak_" + stamp()
        pkg.rename(backup)
    pkg.parent.mkdir(parents=True, exist_ok=True)
    _place(stage, pkg)
    note = _copy_extras(pkg, zip_path, release_json)
    return {"lamp": "GREEN", "detail": "套件就位 %s(SHA-256 %s · %d 檔逐檔相符)%s%s" % (pkg, got[:12], len(manifest["files"]), (" · 舊套件夾改名備份 → " + backup) if backup else "", note), "pkg": str(pkg)}


def _place(stage: Path, pkg: Path) -> None:
    """v0106:不把暫存夾整個搬過去 —— Python 3.13 在 Windows 建的暫存夾(tempfile.mkdtemp)只給擁有者權限,搬過去權限跟著走;某次用系統管理員
    身分跑過,擁有者就是 Administrators,平常身分讀不到(桌機 icacls:Access is denied)。在目的地正常建資料夾(繼承上一層權限)· 逐檔複製內容 · 刪暫存。"""
    Path(pkg).mkdir(parents=True, exist_ok=False)
    for src in sorted(Path(stage).rglob("*")):
        dst = Path(pkg) / src.relative_to(stage)
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(str(src), str(dst))                            # 只複製內容(權限照目的地繼承)
    shutil.rmtree(str(stage), ignore_errors=True)


def _copy_extras(pkg: Path, zip_path, release_json) -> str:
    """v0105:zip / 發行清單副本放進套件夾(方便下次本機核對)· 寫不進去(被鎖)只記一句,不算失敗。"""
    skipped = []
    for extra in (zip_path, release_json):
        if extra and Path(extra).is_file() and Path(extra).resolve() != (Path(pkg) / Path(extra).name).resolve():
            try:
                shutil.copyfile(str(extra), str(Path(pkg) / Path(extra).name))      # v0106 只複製內容(權限照套件夾繼承)
            except OSError as error:
                skipped.append("%s(%s)" % (Path(extra).name, type(error).__name__))
    return (" · 副本沒放進套件夾:" + "、".join(skipped)) if skipped else ""


def git_fetch_release(root: Path, branch: str, work: Path) -> tuple:
    """git archive 發行夾的 zip + 發行清單(分支 → main)。回 (zip, json, 來源說明) 或 (None, None, 原因)。"""
    try:
        top = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=60).stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as error:
        return None, None, "找不到 git(%s)" % type(error).__name__
    if not top:
        return None, None, "%s 不是 git 倉" % root
    for b in (branch, "main"):
        for wait in (0, 2, 4, 8, 16):
            if wait:
                time.sleep(wait)
            r = subprocess.run(["git", "-C", top, "fetch", "-q", "origin", b], capture_output=True, text=True, timeout=600)
            if r.returncode == 0:
                break
        out = work / ("release_%s.zip" % re.sub(r"\W", "_", b))
        r = subprocess.run(["git", "-C", top, "archive", "--format=zip", "-o", str(out), "origin/%s:%s" % (b, RELEASE_REL), PACKAGE + ".zip", RELEASE_JSON], capture_output=True, text=True, timeout=600)
        if r.returncode == 0 and out.is_file():
            folder = work / ("release_" + re.sub(r"\W", "_", b))
            with zipfile.ZipFile(out) as z:
                z.extractall(folder)
            return folder / (PACKAGE + ".zip"), folder / RELEASE_JSON, "GitHub %s" % b
    return None, None, "讀不到 GitHub 分支 %s 或 main 的 %s(網路 / git)" % (branch, RELEASE_REL)


def step_package(root: Path, args) -> Path | None:
    pkg = Path(args.package or os.environ.get("VRN2_PACKAGE") or (downloads() / PACKAGE))
    local_zip = pkg / (PACKAGE + ".zip")
    got, err = read_sha(local_zip) if local_zip.is_file() else (None, "")
    if err:                                                                # v0105:讀不到(被鎖 / 權限)→ 證據 → 改從 GitHub 取
        ev = lock_evidence(local_zip, root)
        say("GRAY", "① 套件 zip 讀不到(改從 GitHub 取)", "%s · %s · 證據:%s" % (local_zip, err, ev),
            "有別的程式佔著這個檔(防毒掃描 / 另一個 VRN-2 視窗 / 檔案總管預覽)或權限不對;不影響這輪(改從 GitHub 取)")
    manifest, bad = {}, ["(沒讀)"]
    if got == PACKAGE_SHA256:
        try:
            with zipfile.ZipFile(local_zip) as z:
                name = next((n for n in z.namelist() if n.endswith("PACKAGE_SHA256.json")), None)
                if name:
                    manifest = json.loads(z.read(name).decode("utf-8"))
            bad = _manifest_check(pkg, manifest) if manifest else ["PACKAGE_SHA256.json"]
        except OSError as error:
            got, bad = None, ["%s: %s" % (type(error).__name__, error)]
            say("GRAY", "① 套件 zip 讀不到(改從 GitHub 取)", "%s · %s · 證據:%s" % (local_zip, bad[0], lock_evidence(local_zip, root)))
    if got == PACKAGE_SHA256:
        if not bad:
            say("GREEN", "① 套件", "本機已是 %s(SHA-256 %s · %d 檔逐檔相符)· %s" % (PACKAGE, PACKAGE_SHA256[:12], len(manifest.get("files") or []), pkg))
            return pkg
        info("本機套件夾有 %d 個檔與已驗證的 zip 不同或不在(%s)→ 從這份 zip 重新解壓" % (len(bad), ", ".join(bad[:3])))
        copy = Path(tempfile.mkdtemp(prefix="vrn2_roundall_zip_")) / local_zip.name
        shutil.copy2(str(local_zip), str(copy))
        return _install_with_fallback(copy, pkg / RELEASE_JSON if (pkg / RELEASE_JSON).is_file() else None, pkg, "")
    if args.offline:
        say("RED", "① 套件", "--offline 但本機沒有雜湊相符的 %s.zip(%s)" % (PACKAGE, local_zip), "拿掉 --offline 讓它從 GitHub 取,或把發行夾的 zip 放到 %s" % pkg)
        return None
    if not root:
        say("RED", "① 套件", "沒有 VIA 根 · 無法用 git 取套件", "加 --root <…\\movies-dataset\\VeritasIntelligenceAnalytics>")
        return None
    work = Path(tempfile.mkdtemp(prefix="vrn2_roundall_rel_"))
    z, rj, how = git_fetch_release(root, args.branch, work)
    if not z:
        say("RED", "① 套件", how, "確認網路 / git;或手動下載 %s/%s.zip 解壓到 %s" % (RELEASE_REL, PACKAGE, pkg))
        return None
    return _install_with_fallback(z, rj, pkg, how)


def _alt_folders(pkg: Path) -> list:
    """v0107:<套件>_<時間> 新夾(新的先 · 不含 .bak_ 備份)。"""
    try:
        return sorted((p for p in Path(pkg).parent.glob(Path(pkg).name + "_*") if p.is_dir() and re.fullmatch(r"\d{8}_\d{6}", p.name[len(Path(pkg).name) + 1:])), key=_mtime, reverse=True)
    except OSError:
        return []


def find_package(args) -> Path | None:
    """v0107 略過取套件時用哪個套件夾:--package / VRN2_PACKAGE / Downloads\\<套件> / Downloads\\<套件>_<時間>(新的先)裡第一個讀得到啟動器的。"""
    first = [Path(x) for x in (args.package, os.environ.get("VRN2_PACKAGE")) if x]
    base = downloads() / PACKAGE
    for cand in first + [base] + _alt_folders(base):
        try:
            with (cand / LAUNCHER).open("rb") as fh:
                fh.read(1)
            return cand
        except OSError:
            continue
    return None


def _install_with_fallback(z: Path, rj, pkg: Path, how: str):
    """v0105:裝進原套件夾;原夾用不了(檔被鎖 / 權限 · 改名失敗)→ 裝到新夾 <套件>_<時間>(原夾不動)。"""
    try:
        r = install_package(z, PACKAGE_SHA256, pkg, rj)
    except OSError as error:
        for old in _alt_folders(pkg):                                         # v0107 先沿用既有的 <套件>_<時間>(逐檔相符就直接用)
            try:
                r = install_package(z, PACKAGE_SHA256, old, rj)
            except OSError:
                continue
            if r["lamp"] == "GREEN":
                r["detail"] += " · 原套件夾 %s 用不了(%s)→ 沿用 %s" % (pkg, type(error).__name__, old.name)
                say(r["lamp"], "① 套件", r["detail"] + ((" · 來源 " + how) if how else ""))
                return Path(r["pkg"])
        alt = Path(pkg).with_name(Path(pkg).name + "_" + stamp())
        info("① 套件夾 %s 用不了(%s: %s)→ 改裝到新夾 %s(原夾不動)" % (pkg, type(error).__name__, str(error)[:160], alt))
        r = install_package(z, PACKAGE_SHA256, alt, rj)
        r["detail"] += " · 原套件夾 %s 用不了(%s)→ 用新夾" % (pkg, type(error).__name__)
    say(r["lamp"], "① 套件", r["detail"] + ((" · 來源 " + how) if how else ""))
    return Path(r["pkg"]) if r["lamp"] == "GREEN" and r.get("pkg") else None


# ===== 5. ② 診斷 =====
def step_preflight(root: Path, pkg, vpy: str, vpy_how: str, args) -> dict:
    state = {}
    v2 = Path(root) / "VIA_Reports" / "vrn2" if root else None
    say("GREEN", "② VRN-2 Python", "%s(%s · %s)" % (vpy, vpy_how, python_version(vpy)))
    got = probe_modules(vpy, VRN2_REQUIRED + VRN2_OPTIONAL)
    miss = [m for m in VRN2_REQUIRED if not got.get(m)]
    opt = [m for m in VRN2_OPTIONAL if not got.get(m)]
    say("YELLOW" if miss else "GREEN", "② VRN-2 套件", "必裝 %s%s · 選裝缺 %s" % ("全在" if not miss else "缺 " + ", ".join(miss), "" if miss else "", ", ".join(opt) or "無"),
        "啟動器 ③ 會檢查 / 補裝;仍缺 → 交 VCGC 安裝:%s -m pip install %s" % (vpy, " ".join(miss)) if miss else "")
    fpy, report = find_fetch_python()
    state["fetch_python"] = fpy
    if SKIPPED_ENVS:
        info("擷取 Python 不用退役 / 備份的環境:%s" % "、".join(SKIPPED_ENVS))
    if fpy:
        say("GREEN", "② 擷取 Python(⑥e / ⑥f)", "%s · %s 全在" % (fpy, " / ".join(FETCH_REQUIRED)))
    else:
        say("YELLOW", "② 擷取 Python(⑥e / ⑥f)", "沒有裝齊 %s 的 Python(看過 %s)" % (" / ".join(FETCH_REQUIRED), " ; ".join("%s 缺 %s" % (Path(p).parent.parent.name or p, ",".join(m)) for p, m in report)[:300]),
            "TWSE / TPEX / Yahoo 與 FactSet 共識會黃。交 VCGC 建環境:\n         " + "\n         ".join(VCGC_FETCH_ENV))
    if root:
        shared = Path(root) / "functional modules" / "VRN"
        tools = sorted(shared.glob("VRN2_MarketFetch_v[0-9][0-9][0-9][0-9].py"), key=lambda p: int(re.search(r"_v(\d{4})", p.name).group(1))) if shared.is_dir() else []
        eng = sorted((shared / "_vdf_fetch").glob("VDF_TW_*.py"), key=lambda p: int((re.search(r"_v(\d+)", p.name) or re.search(r"(\d+)", "0")).group(1))) if (shared / "_vdf_fetch").is_dir() else []
        state["market_tool"] = str(tools[-1]) if tools else ""
        if tools and pkg:
            picked = pick_fetch_python(pkg, vpy, tools[-1], fpy)
            state["bounds_python"] = picked.get("python")
            bounds = [r[1] for r in picked.get("requirements") or []] or list(VDF_BOUNDS)
            if picked.get("python"):
                say("GREEN", "② 擷取 Python · VDF 版本界線(⑥e)", "%s · 合 %s(%s)" % (picked["python"], " ".join(bounds), picked.get("requirements_from", "")))
            else:
                say("YELLOW", "② 擷取 Python · VDF 版本界線(⑥e)", "沒有合 %s 的 Python:%s" % (" ".join(bounds), str(picked.get("why", ""))[:500]),
                    "⑥e 會黃(不啟動 VDF 引擎 · 免得它自己 pip);填值照用現有 Parquet。交 VCGC 建 via_tw_fetch(VRN-2 不裝):\n         " + "\n         ".join(vcgc_fetch_commands(bounds)))
        say("GREEN" if tools and eng else "YELLOW", "② 共用市場擷取工具", ("%s · VDF 引擎 %s" % (tools[-1].name, " / ".join(p.name for p in eng))) if tools and eng else "共用夾 %s 沒有 %s" % (shared, "VRN2_MarketFetch_v*.py" if not tools else "_vdf_fetch\\VDF_TW_*.py"),
            "" if tools and eng else "⑥e 會灰 → 先在倉裡 git pull(共用夾的桌機線工具),或用桌機線自己的啟動器抓市場資料")
        lock = v2 / "VRN2_Launcher.lock"
        if lock.is_file():
            pid = int((jread(lock, {}) or {}).get("pid") or 0)
            alive = pid_alive(pid)
            state["lock_alive"] = alive
            say("RED" if alive else "YELLOW", "② 啟動器鎖", "%s · PID %s %s" % (lock, pid, "還在跑" if alive else "已不在(過期鎖)"),
                "另一個 VRN-2 啟動器正在跑:等它結束再跑本檔(不要硬跑)" if alive else "⑤ 自動修會清掉(啟動器自己也會)")
        else:
            say("GREEN", "② 啟動器鎖", "沒有其他啟動器在跑")
        cfg = jread(v2 / "VRN2_Output_Config.json", {}) or {}
        out_dir = cfg.get("output_dir") or os.environ.get("VRN2_OUTPUT_DIR") or ""
        if out_dir:
            try:
                Path(out_dir).mkdir(parents=True, exist_ok=True)
                probe = Path(out_dir) / (".vrn2_write_test_%d" % os.getpid())
                probe.write_text("x", encoding="utf-8")
                probe.unlink()
                say("GREEN", "② 輸出檔案夾(長線 Parquet 庫)", "%s · 可寫" % out_dir)
            except OSError as error:
                say("RED", "② 輸出檔案夾(長線 Parquet 庫)", "%s 寫不進去(%s)" % (out_dir, type(error).__name__), "Workbench 左欄「換輸出夾…」選一個可寫的夾")
        else:
            say("GRAY", "② 輸出檔案夾(長線 Parquet 庫)", "還沒選 · 輸出留在 VIA_Reports\\vrn2\\output", "Workbench 左欄「選擇輸出夾…」或 $env:VRN2_OUTPUT_DIR")
        src = args.source or os.environ.get("VRN2_SOURCE") or (jread(v2 / "VRN2_Input_latest.json", {}) or {}).get("source_dir") or ""
        if src and Path(src).is_dir():
            n_pdf = sum(1 for _ in Path(src).rglob("*.pdf"))
            say("GREEN" if n_pdf else "YELLOW", "② 來源夾", "%s · PDF %d 份" % (src, n_pdf))
        elif src:
            say("RED", "② 來源夾", "%s 不存在" % src, "--source <報告夾> 或 Workbench「選擇檔案夾…」")
        else:
            say("GRAY", "② 來源夾", "沒指定 · 啟動器用上一輪 / VRN2_SSOT 的來源夾")
        for label, folder in (("VIA 根", Path(root)), ("TEMP", Path(tempfile.gettempdir()))):
            try:
                free = shutil.disk_usage(str(folder)).free / 1e9
                say("GREEN" if free >= 2 else "YELLOW", "② 磁碟 · " + label, "可用 %.1f GB" % free, "" if free >= 2 else "清出 ≥ 2 GB(OCR / 快取 / 增量庫要空間)")
            except OSError:
                pass
        if "onedrive" in str(root).lower():
            info("VIA 根在 OneDrive 同步夾:檔案 I/O 慢(v0145 輸出冊 969 秒有一部分是它)· 跑的時候可暫停 OneDrive 同步")
    try:
        import psutil  # noqa: WPS433
        busy = psutil.cpu_percent(interval=1.0)
        say("YELLOW" if busy > 60 else "GREEN", "② CPU", "忙碌 %.0f%%" % busy, "別的程式佔 CPU → 啟動器只能降路數(v0145 就是 87.5%% → 1 路)· 先關掉再跑" if busy > 60 else "")
    except Exception:  # noqa: BLE001
        pass
    git = shutil.which("git")
    say("GREEN" if git else "YELLOW", "② git", git or "找不到 git", "" if git else "取套件 / 上船要 git")
    return state


# ===== 6. ③ 自測 =====
def step_selftest(pkg: Path, vpy: str, timeout_scale: float = 1.0) -> list:
    out = []
    manifest = jread(Path(pkg) / RUNTIME_MANIFEST, {}) or {}
    rt = Path(tempfile.mkdtemp(prefix="vrn2_roundall_rt_"))
    try:
        with zipfile.ZipFile(Path(pkg) / RUNTIME_ZIP) as z:
            z.extractall(rt)
    except (OSError, zipfile.BadZipFile) as error:
        say("RED", "③ 自測 · runtime zip", "解不開 %s(%s)" % (RUNTIME_ZIP, type(error).__name__))
        return out
    bad = _manifest_check(rt, manifest)
    say("RED" if bad else "GREEN", "③ 自測 · runtime 解壓", "%d 檔%s" % (len(manifest.get("files") or []), (" · 不符 " + ", ".join(bad[:5])) if bad else " 逐檔相符"))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", VRN2_UIACTION_DRY="1")
    for name, limit in SELFTESTS:
        path = rt / name
        if not path.is_file():
            say("RED", "③ 自測 · " + name, "runtime 裡沒有")
            continue
        t0 = time.time()
        rc, lines = run_stream([vpy, "-X", "utf8", str(path), "--selftest"], cwd=rt, env=env, timeout=int(limit * timeout_scale), quiet=True)
        fails = [l for l in lines if l.lstrip().startswith(("[FAIL]", "  [FAIL]")) or "Traceback" in l]
        tail = next((l for l in reversed(lines) if "--selftest" in l or l.startswith("[PASS]") or l.startswith("[FAIL]")), lines[-1] if lines else "")
        lamp = "GREEN" if rc == 0 and not fails else "RED"
        row = say(lamp, "③ 自測 · " + name, "%s · %.0f 秒%s" % (tail.strip()[:160], time.time() - t0, (" · " + " | ".join(f.strip()[:120] for f in fails[:3])) if fails else ""))
        if lamp == "RED":
            for l in lines[-15:]:
                print("       " + l[:300])
        out.append(row)
    t0 = time.time()
    rc, lines = run_stream([vpy, "-X", "utf8", str(Path(pkg) / LAUNCHER), "--selftest"], cwd=pkg, env=env, timeout=int(900 * timeout_scale), quiet=True)
    passes = [l for l in lines if l.startswith("[PASS] v01")]
    row = say("GREEN" if rc == 0 and len(passes) >= 5 else "RED", "③ 自測 · " + LAUNCHER, "PASS %d 段 · %.0f 秒%s" % (len(passes), time.time() - t0, "" if rc == 0 else " · " + (lines[-1] if lines else "")[:200]))
    if row["lamp"] == "RED":
        for l in lines[-15:]:
            print("       " + l[:300])
    out.append(row)
    shutil.rmtree(rt, ignore_errors=True)
    return out


# ===== 7. ④ 跑 =====
def step_run(pkg: Path, root: Path, vpy: str, state: dict, args) -> int:
    if state.get("lock_alive"):
        say("RED", "④ 跑啟動器", "另一個 VRN-2 啟動器還在跑 · 本輪不跑", "等它結束(或關掉那個視窗)再執行本檔")
        return 1
    cmd = [vpy, "-X", "utf8", str(Path(pkg) / LAUNCHER)]
    src = args.source or os.environ.get("VRN2_SOURCE") or ""
    if src:
        cmd += ["--source", src]
    if args.no_open:
        cmd += ["--no-open"]
    cmd += [a for a in (args.launcher_args or "").split() if a]
    env = dict(os.environ)
    if not args.ship:
        env["VIA_VRN2_NO_PUSH"] = "1"
    if state.get("fetch_python") and not env.get("VIA_FETCH_PY"):
        env["VIA_FETCH_PY"] = state["fetch_python"]
    if root:
        env.setdefault("VRN2_ROOT", str(root))
    info("④ " + " ".join('"%s"' % c if " " in str(c) else str(c) for c in cmd) + ("(不上船)" if not args.ship else "(會上船)"))
    t0 = time.time()
    rc, lines = run_stream(cmd, cwd=pkg, env=env, timeout=int(args.run_timeout), prefix="  ")
    nxt = next((l for l in reversed(lines) if l.startswith("NEXT:")), "")
    say({0: "GREEN", 2: "YELLOW"}.get(rc, "RED"), "④ 跑啟動器 " + LAUNCHER, "rc %s · %.0f 秒 · %s" % (rc, time.time() - t0, nxt[:200] or "(沒有 NEXT 行)"))
    return rc


# ===== 8. ⑤ 自動修 =====
def _mtime(p: Path) -> float:
    try:
        return Path(p).stat().st_mtime
    except OSError:
        return 0.0


def _latest_in(folder: Path, pattern: str):
    hits = sorted(Path(folder).glob(pattern), key=lambda p: int(re.search(r"_v(\d{4})", p.name).group(1))) if Path(folder).is_dir() else []
    return hits[-1] if hits else None


def plan_fixes(root: Path, receipt: dict, fetch_py, args, market_tool: str = "") -> list:
    """純判斷(可測):回要做的修正清單 [(代號, 說明)]。"""
    v2 = Path(root) / "VIA_Reports" / "vrn2"
    plan = []
    market = receipt.get("market") or {}
    consensus = receipt.get("consensus") or {}
    run = consensus.get("run") or {}
    mjson, hrec = v2 / "market" / "VRN2_Market_latest.json", v2 / "VRN2_HistoryAlign_latest.json"
    cjson, comb = v2 / "consensus" / "VRN2_Consensus_latest.json", v2 / "output" / "VRN2_Combined_latest.json"
    if market_tool and fetch_py and market.get("lamp") in ("YELLOW", "RED") and "Python 本行程" in str(market.get("detail", "")) and not market.get("runner") and os.environ.get("VIA_VRN2_NO_MARKET") != "1":   # v0103:經 MarketFetchRun 跑過的不重抓
        plan.append(("market", "⑥e 用了 VRN-2 的 Python · 擷取 Python %s 套件齊 → 重抓" % fetch_py))
    if fetch_py and run.get("lamp") == "YELLOW" and "yfinance" in str(run.get("why", "")) and os.environ.get("VIA_VRN2_NO_CONSENSUS") != "1":
        plan.append(("consensus", "⑥f 缺 yfinance · 找到 %s → 重跑共識" % fetch_py))
    cons_now = jread(cjson, {}) or {}
    q404, qtr, qother = gate_rows(v2)
    if (fetch_py and not any(k == "consensus" for k, _ in plan) and str(cons_now.get("gate") or run.get("gate") or "").upper() == "FAIL_CLOSED" and (q404 or qtr) and not qother
            and "retries" not in cons_now and os.environ.get("VIA_VRN2_NO_CONSENSUS") != "1"):          # v0110 ConsensusJoin v0103 以前做的
        plan.append(("consensus", "⑥f 共識閘只因 404 / 一時抓不到(%s) → 用 ConsensusJoin v0103 重跑(沿用今天抓到的 · 重試 · 暫缺不納入閘)" % ",".join(sorted(q404 | qtr))[:40]))
    planned = {p[0] for p in plan}
    if mjson.is_file() and ("market" in planned or not hrec.is_file() or _mtime(mjson) > _mtime(hrec) or (receipt.get("history_align") or {}).get("lamp") == "GRAY"):
        plan.append(("history", "市場資料比歷史對齊新 / 歷史對齊沒跑 → 重跑 ⑬b"))
    if (v2 / "output" / "VRN2_BasicInfo_latest.json").is_file() and (planned & {"market", "consensus"} or not comb.is_file() or max(_mtime(mjson), _mtime(cjson)) > _mtime(comb)):
        plan.append(("combined", "Combined 比市場 / 共識舊(或不在)→ 重組"))
    planned = {p[0] for p in plan}
    store = jread(v2 / "VRN2_OutputStore_latest.json", {}) or {}
    cfg = jread(v2 / "VRN2_Output_Config.json", {}) or {}
    totals = store.get("totals") or {}
    missing_books = [b for b in ("Combined", "FinancialAligned", "Deleted") if (v2 / "output" / ("VRN2_%s_latest.json" % b)).is_file() and b not in totals]
    if cfg.get("output_dir") and (planned or missing_books):
        plan.append(("store", "⑬ 增量庫補寫(%s)" % ("本輪有修正" if planned else "庫裡還沒有 " + "、".join(missing_books))))
    integ = jread(v2 / "VRN2_Integrate_latest.json", {}) or {}
    if integ.get("state") == "PENDING_USER" and args.integrate in ("yes", "no", "ask"):
        plan.append(("integrate", "舊資料庫 %d 份待決定 · 模式 %s" % (len([c for c in integ.get("candidates") or [] if c.get("readable")]), args.integrate)))
    lock = v2 / "VRN2_Launcher.lock"
    if lock.is_file() and not pid_alive(int((jread(lock, {}) or {}).get("pid") or 0)):
        plan.append(("lock", "過期鎖(PID 已不在)→ 清掉"))
    wb = v2 / "VRN2_Workbench_latest.html"
    if plan or not wb.is_file():
        plan.append(("workbench", "Workbench 重渲染(最新收據)"))
    return plan


def _cli_lamp(lines: list) -> tuple:
    for l in reversed(lines):
        m = re.search(r"\[(GREEN|YELLOW|RED|GRAY)\]\s*(.*)", l)
        if m:
            return m.group(1), m.group(2)[:240]
        m = re.search(r"\[計\] (?:市場擷取|市場填值|[^·]+) · (GREEN|YELLOW|RED|GRAY) · (.*)", l)
        if m:
            return m.group(1), m.group(2)[:240]
    return "YELLOW", (lines[-1] if lines else "沒有輸出")[:240]


def step_fix(root: Path, vpy: str, state: dict, args) -> list:
    v2 = Path(root) / "VIA_Reports" / "vrn2"
    rt = Path(root) / "functional modules" / "VRN2"
    rpath = receipt_path(v2)
    receipt = jread(rpath, {}) or {}
    if not receipt:
        say("GRAY", "⑤ 自動修", "沒有收尾收據 %s(啟動器沒跑完)· 不修" % RECEIPT)
        return []
    fetch_py = state.get("fetch_python")
    if fetch_py is None and "fetch_python" not in state:
        fetch_py, _ = find_fetch_python()
    plan = plan_fixes(root, receipt, fetch_py, args, state.get("market_tool") or "")
    if not plan:
        say("GREEN", "⑤ 自動修", "沒有要修的(能自動修的都已綠 / 灰)")
        return []
    info("⑤ 自動修計畫:" + " · ".join(d for _, d in plan))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    if fetch_py:
        env["VIA_FETCH_PY"] = fetch_py
    done, step_updates = [], {}
    for key, desc in plan:
        lamp, detail = "GRAY", ""
        if key == "market":
            tool, basic = Path(state["market_tool"]), v2 / "output" / "VRN2_BasicInfo_latest.json"
            lamps = []
            runner = rt / MARKET_RUNNER                                  # v0102:runtime 有 MarketFetchRun → 經它跑(fetch_python 換成合 VDF 界線的)
            py = state.get("bounds_python") or fetch_py
            for verb in ("--fetch", "--fill"):
                head = [py, "-X", "utf8", str(runner), "--tool", str(tool), "--python", py] if runner.is_file() else [py, "-X", "utf8", str(tool)]
                rc, lines = run_stream(head + [verb, "--basic", str(basic), "--out", str(v2 / "market")], cwd=tool.parent, env=env, timeout=2400, prefix="    [⑥e] ")
                lamps.append(_cli_lamp(lines))
            lamp = worst([l for l, _ in lamps])
            lamp = "YELLOW" if lamp == "RED" else lamp
            detail = "擷取 %s:%s · 填值 %s:%s" % (lamps[0][0], lamps[0][1], lamps[-1][0], lamps[-1][1])
            step_updates["⑥e"] = (lamp, detail)
        elif key == "consensus":
            put, refused = place_consensus(state.get("pkg"), root)               # v0110 套件 runtime 的 ConsensusJoin 鏈 / 共識引擎只增不覆寫地補放
            cj = _latest_in(rt, "VRN2_ConsensusJoin_v[0-9][0-9][0-9][0-9].py")
            rc, lines = run_stream([vpy, "-X", "utf8", str(cj), "run", "--v2", str(v2), "--root", str(root)], cwd=rt, env=env, timeout=1200, prefix="    [⑥f] ")
            lamp, detail = _cli_lamp(lines)
            if put or refused:
                detail = ("%s%s · %s" % (("補放 " + "、".join(put)) if put else "", (" · 不覆寫 " + "、".join(refused)) if refused else "", detail)).strip(" ·")
            step_updates["⑥f"] = (lamp if lamp != "RED" else "YELLOW", detail)
        elif key == "history":
            ha = _latest_in(rt, "VRN2_HistoryAlign_v[0-9][0-9][0-9][0-9].py")
            rc, lines = run_stream([vpy, "-X", "utf8", str(ha), "align", "--root", str(root)], cwd=rt, env=env, timeout=900, prefix="    [⑬b] ")
            lamp, detail = _cli_lamp(lines)
            step_updates["⑬b"] = (lamp if lamp != "RED" else "YELLOW", detail)
        elif key == "combined":
            cj = _latest_in(rt, "VRN2_ConsensusJoin_v[0-9][0-9][0-9][0-9].py")
            rc, lines = run_stream([vpy, "-X", "utf8", str(cj), "join", "--v2", str(v2)], cwd=rt, env=env, timeout=600, prefix="    [Combined] ")
            lamp, detail = _cli_lamp(lines)
            if "⑥f" in step_updates:
                step_updates["⑥f"] = (worst([step_updates["⑥f"][0], lamp]), step_updates["⑥f"][1] + " · " + detail)
        elif key == "store":
            st = _latest_in(rt, "VRN2_OutputStore_v[0-9][0-9][0-9][0-9].py")
            rc, lines = run_stream([vpy, "-X", "utf8", str(st), "sync", "--v2", str(v2), "--run-id", stamp() + "_roundall"], cwd=rt, env=env, timeout=1800, prefix="    [⑬] ")
            lamp, detail = _cli_lamp(lines)
            rec = jread(v2 / "VRN2_OutputStore_latest.json", {}) or {}
            if rec:
                lamp = rec.get("lamp", lamp)
                detail = "%s · 追加 %s · 補缺 %s · 累計 %s" % (rec.get("store_engine", ""), json.dumps(rec.get("appended") or {}, ensure_ascii=False), json.dumps(rec.get("backfilled") or {}, ensure_ascii=False), json.dumps(rec.get("totals") or {}, ensure_ascii=False))
            step_updates["⑬ "] = (lamp, detail)
        elif key == "integrate":
            integ = jread(v2 / "VRN2_Integrate_latest.json", {}) or {}
            mode = args.integrate
            if mode == "ask":
                cands = [c for c in integ.get("candidates") or [] if c.get("readable")]
                print("\n" + (integ.get("prompt") or "偵測到舊資料庫,要不要整合?"))
                for i, c in enumerate(cands, 1):
                    print("   %d. %s(%s → %s · 對到 %s 欄)" % (i, c.get("path"), c.get("kind"), c.get("target_book"), c.get("mapped")))
                if sys.stdin is not None and sys.stdin.isatty():
                    try:
                        answer = input("要整合嗎?[y = 整合 / n = 不要 / 其他 = 先不決定]:").strip().lower()
                    except EOFError:
                        answer = ""
                    mode = "yes" if answer in ("y", "yes", "是", "要") else ("no" if answer in ("n", "no", "否", "不要") else "skip")
                else:
                    mode = "skip"
            if mode in ("yes", "no"):
                di = _latest_in(rt, "VRN2_DataIntegrate_v[0-9][0-9][0-9][0-9].py")
                rc, lines = run_stream([vpy, "-X", "utf8", str(di), "apply" if mode == "yes" else "dismiss", "--v2", str(v2)], cwd=rt, env=env, timeout=1800, prefix="    [⑬c] ")
                lamp, detail = _cli_lamp(lines)
                reminder = next((l for l in lines if "原檔已複製到" in l), "")
                if reminder:
                    detail += " · " + reminder.replace("[計] ", "")[:200]
                step_updates["⑬c"] = (lamp if lamp != "RED" else "YELLOW", detail)
            else:
                lamp, detail = "YELLOW", "先不決定 · 舊資料庫仍待決定(Workbench 按「整合 / 不要」或本檔 --integrate yes|no)"
        elif key == "lock":
            try:
                (v2 / "VRN2_Launcher.lock").unlink()
                lamp, detail = "GREEN", "過期鎖已清"
            except OSError as error:
                lamp, detail = "YELLOW", "清不掉(%s)" % type(error).__name__
        elif key == "workbench":
            wb = _latest_in(rt, "VRN2_Workbench_v[0-9][0-9][0-9][0-9].py")
            if step_updates:
                _patch_receipt(rpath, receipt, step_updates)
            if wb:
                rc, lines = run_stream([vpy, "-X", "utf8", str(wb), "render", "--root", str(root)], cwd=rt, env=env, timeout=600, prefix="    [U/I] ")
                lamp, detail = _cli_lamp(lines)
            else:
                lamp, detail = "YELLOW", "私有 runtime 沒有 VRN2_Workbench_v*.py"
        done.append(say(lamp, "⑤ 修 · " + desc.split(" → ")[0][:60], detail))
    if step_updates and not any(k == "workbench" for k, _ in plan):
        _patch_receipt(rpath, receipt, step_updates)
    return done


def receipt_path(v2) -> Path:
    """v0108:這版啟動器的收據;還沒有(這輪只重跑 ⑪b / 只重做報告,啟動器 v0154 還沒跑過)→ 最新的前版收據 VRN2_Closeout_v0NNN.json(不含 .before_roundall)。"""
    p = Path(v2) / RECEIPT
    if p.is_file() or not Path(v2).is_dir():
        return p
    olds = sorted(q for q in Path(v2).glob("VRN2_Closeout_v0[0-9][0-9][0-9].json") if q.name < RECEIPT)
    return olds[-1] if olds else p


def _patch_receipt(rpath: Path, receipt: dict, updates: dict) -> None:
    """收尾收據先備份(只備份一次)→ 被修的步驟換燈 + 註明「RoundAll 修正後」。"""
    backup = rpath.with_name(rpath.stem + ".before_roundall.json")
    if not backup.is_file():
        shutil.copy2(str(rpath), str(backup))
    for s in receipt.get("steps") or []:
        for prefix, (lamp, detail) in updates.items():
            if str(s.get("step", "")).startswith(prefix):
                s["lamp"] = lamp
                s["detail"] = ("RoundAll 修正後 · " + detail)[:300]
    fixed = dict((receipt.get("roundall") or {}).get("fixed") or {})       # v0108 合併:⑪b 不蓋掉之前 ⑤ 自動修的紀錄
    fixed.update({k: {"lamp": v[0], "detail": v[1]} for k, v in updates.items()})
    receipt["roundall"] = {"version": "%s %s" % (NAME, VERSION), "at": _dt.datetime.now().isoformat(timespec="seconds"), "fixed": fixed}
    rpath.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")


def place_consensus(pkg, root) -> tuple:
    """v0110 ⑤ 重跑 ⑥f 前:套件 runtime 的 ConsensusJoin 鏈與共識引擎(核對清單雜湊)只增不覆寫地放進 functional modules\\VRN2
    (修 / 只重做報告的輪次啟動器沒跑 → runtime 沒還原)。回 (補放了哪些, 同名不同內容沒覆寫的)。"""
    if not pkg or not (Path(pkg) / RUNTIME_ZIP).is_file():
        return [], []
    with zipfile.ZipFile(Path(pkg) / RUNTIME_ZIP) as z:
        names = sorted(n for n in z.namelist() if re.fullmatch(r"(VRN2_ConsensusJoin|VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine)_v\d{4}\.py", n))
    put, refused = [], []
    for name in names:
        got, why = install_runtime_member(pkg, root, name)
        if got is None:
            refused.append(name)
        elif why == "補放":
            put.append(name)
    return put, refused


# ===== 8b. ⑪b 只重跑獨立驗證(v0108)=====
def install_runtime_member(pkg, root, name: str) -> tuple:
    """套件 runtime zip 的一個成員(核對清單雜湊)→ 只增不覆寫地放進 functional modules\\VRN2。回 (路徑 | None, 說明)。"""
    rz, rm = Path(pkg) / RUNTIME_ZIP, Path(pkg) / RUNTIME_MANIFEST
    want_sha = {e["path"]: e["sha256"] for e in (jread(rm, {}) or {}).get("files") or []}
    with zipfile.ZipFile(rz) as z:
        data = z.read(name)
    got = hashlib.sha256(data).hexdigest()
    if want_sha.get(name) != got:
        return None, "%s 與 runtime 清單雜湊不符 · 不用" % name
    dest = Path(root) / "functional modules" / "VRN2" / name
    if dest.is_file():
        return (dest, "已在") if sha256_file(dest) == got else (None, "%s 已在但內容不同(同名不同內容 · 不覆寫)" % name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest, "補放"


def step_verify(root, pkg, vpy) -> dict:
    """v0108 ⑪b:只重跑獨立驗證 —— 套件 runtime 最新的 IndependentVerifier(與它 load 的檔)只增不覆寫地放進 functional modules\\VRN2 →
    照啟動器 ⑪ 的方式跑(輸出冊 · scope_in · 寫回 U/I · 新報告)→ 收據 ⑪ 換成這次結果(先備份)。"""
    v2 = Path(root) / "VIA_Reports" / "vrn2"
    if not pkg or not (Path(pkg) / RUNTIME_ZIP).is_file():
        say("YELLOW", "⑪b 重跑獨立驗證", "沒有套件 runtime(%s)· 不驗" % (Path(pkg or ".") / RUNTIME_ZIP), "用 --only package,verify,report,closeout,pasteback(先取套件)")
        return {}
    with zipfile.ZipFile(Path(pkg) / RUNTIME_ZIP) as z:
        ivs = sorted(n for n in z.namelist() if re.fullmatch(r"VRN2_IndependentVerifier_v\d{4}\.py", n))
        newest = ivs[-1] if ivs else ""
        code = z.read(newest).decode("utf-8") if newest else ""
    if not newest:
        say("RED", "⑪b 重跑獨立驗證", "套件 runtime 裡沒有 IndependentVerifier")
        return {}
    notes = []
    for name in [newest] + re.findall(r'load\("[^"]+",\s*"([^"]+\.py)"\)', code):
        got, why = install_runtime_member(pkg, root, name)
        if got is None:
            say("RED", "⑪b 重跑獨立驗證", why, "同名不同內容的檔不覆寫(只增)→ 貼回包給 AI")
            return {}
        if why == "補放":
            notes.append(name)
    od, scope = v2 / "output", v2 / "scope_in"
    if not (od / "VRN2_FinancialData_latest.json").is_file() or not scope.is_dir():
        say("YELLOW", "⑪b 重跑獨立驗證", "沒有上一輪的輸出冊或 scope_in(%s)· 不驗" % od, "先跑一次整輪")
        return {}
    vd = v2 / "verify_independent"
    vd.mkdir(parents=True, exist_ok=True)
    rep_path = vd / ("VRN2_IndependentVerify_%s.json" % stamp())
    fm = Path(root) / "functional modules" / "VRN2"
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    info("⑪b %s 重跑(%s)· 輸出冊 %s · 原檔 %s%s" % (newest, vpy, od, scope, (" · 補放 " + "、".join(notes)) if notes else ""))
    t0 = time.time()
    rc, lines = run_stream([vpy, "-W", "ignore", str(fm / newest), str(od), str(scope), str(rep_path), "--ui", str(v2 / "VRN2_UI_latest.html")], cwd=fm, env=env,
                           timeout=int(os.environ.get("VIA_VRN2_VERIFY_WAIT") or 3600), prefix="    ")
    got = jread(rep_path, {}) or {}
    vl = [l.strip() for l in lines if l.startswith("[驗證]")]
    cnt = " · ".join(l.split("]", 1)[1].strip() for l in vl if any(k in l for k in ("基本資料", "一標題四重點", "年度數據")))[:400]
    if rc not in (0, 1) or not got:
        say("RED", "⑪b 重跑獨立驗證", "%s 沒跑完 rc %s · %s" % (newest, rc, " | ".join(lines[-3:])[:300]), "看上面幾行;貼回包給 AI")
        return {}
    lamp = "GREEN" if rc == 0 else "YELLOW"
    detail = "%s · %s · %s · 報告 %s · %.0f 秒" % (newest.replace(".py", ""), "錯值 0" if rc == 0 else "有待核對(先看原文再判 · 驗證器也要被驗)", cnt, rep_path.name, time.time() - t0)
    say(lamp, "⑪b 重跑獨立驗證", detail)
    rpath = receipt_path(v2)
    receipt = jread(rpath, {}) or {}
    if receipt.get("steps"):
        _patch_receipt(rpath, receipt, {"⑪": (lamp, detail)})
    return {"rc": rc, "report": str(rep_path), "version": got.get("version")}


# ===== 9. ⑥ 除錯報告 =====
ADVICE = (("③", "缺必裝套件 / 加速器:看 ③ 那行列的缺項;啟動器會試著補裝,仍缺 → 交 VCGC 安裝(VRN-2 只檢查)"),
          ("⑥c", "vrn2:// 協定沒註冊:非 Windows 或權限 → 桌機重跑一次;仍灰看 ⑤b 那行"),
          ("⑥e", "市場擷取:共用夾沒有 MarketFetch → git pull;缺套件 → 建 via_tw_fetch 環境(VCGC);網路 → 看 VIA_Reports\\vrn2\\market\\vdf\\last_error.txt"),
          ("⑥f", "共識:缺 yfinance → via_tw_fetch 環境;gate FAIL_CLOSED → 看 VIA_Reports\\vrn2\\consensus 的 quality_matrix.csv"),
          ("⑬b", "歷史對齊:灰 = 沒有市場資料(先讓 ⑥e 綠);黃 = 有報告一期都沒對上(看 VRN2_HistoryAlign_latest.json 的 files)"),
          ("⑬c", "舊資料庫待決定:Workbench 按「整合 / 不要」或本檔 --skip-run --integrate yes|no"),
          ("⑬ ", "輸出夾未選 → Workbench 左欄「選擇輸出夾…」;pyarrow 備援(黃)→ 裝 duckdb 走正式路徑"),
          ("⑨", "上船 GitHub 預設關(只測不推)· 要推加 --ship"), ("⑩", "整併封存 · 灰 = 本輪不需要"), ("⑫a", "VRN-1 倉同步 · 灰 = 關掉 / 沒設 VIA_VRN1_ROOT"),
          ("⑫", "PIVOT 借用 VRN-1 · 灰 = 關掉 / 沒有 VRN-1 倉"), ("⑤b", "SSOT-ID:黃 = VRN-2 內部自撞(看請求冊 self_conflicts)"),
          ("⑧", "完成判定 / 四點原文核對 / 缺項:看下面的清單;FAIL 要原 PDF 與貼回包"), ("⑪", "獨立驗證:看 verify_independent 的 .digest.txt"),
          ("⑦", "VRN-2 主跑:看 ⑦ 那段的 [計] 行(冪等閘 · 階段耗時)"))


def advice_for(step: str) -> str:
    for prefix, text in ADVICE:
        if str(step).startswith(prefix):
            return text
    return "看主控台該步那一行"


EVIDENCE_PY = r"""
import json, re, sys
pdf, values = sys.argv[1], json.loads(sys.argv[2])
labels = re.compile(r"price|target|close|upside|股價|目標|收盤|現價|潛在|漲幅|上漲", re.I)
contact = re.compile(r"@|\+\d{1,3}[\s-]*\d|\b\d{3,4}-\d{4}\b|tel\b|fax\b|電話|傳真", re.I)
def num(t):
    try:
        return float(str(t).replace(",", "").replace(" ", ""))
    except ValueError:
        return None
want = [(f, num(re.sub(r"[^\d.,-]", "", str(v)))) for f, v in values]
out = []
try:
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(pdf)
    for i in range(min(4, len(doc))):
        for line in doc[i].get_textpage().get_text_range().replace("\r", "\n").split("\n"):
            if not line.strip() or contact.search(line):
                continue
            ns = [num(m.group()) for m in re.finditer(r"-?\d[\d,]*(?:\.\d+)?", line)]
            hit = [f for f, w in want if w is not None and any(n is not None and abs(n - w) < 1e-6 for n in ns)]
            if hit or (labels.search(line) and re.search(r"\d", line)):
                out.append({"page": i + 1, "line": line.strip()[:200], "values": hit})
except Exception as error:
    out.append({"error": "%s: %s" % (type(error).__name__, str(error)[:160])})
out.sort(key=lambda r: (not r.get("values"), r.get("page", 0)))
print(json.dumps(out[:60], ensure_ascii=False))
"""
FIN_EVIDENCE_PY = r"""
import json, re, sys
pdf, page, item, period, value = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
words = [w for w in re.findall(r"[a-z]+|\d+|[\u3400-\u9fff]+", item.lower()) if len(w) >= 2][:3]
PER = re.compile(r"^(?:fy)?(?:(?:19|20)\d{2}[aefp]?|\d{2}[aefp])$", re.I)
VAL = re.compile(r"^(?:\(?-?[\d,]*\.?\d+\)?%?|n\.?a\.?|n/a|nm|n\.m\.|-+|–|—)$", re.I)
def key(t):
    d = re.sub(r"\D", "", t); l = re.sub(r"[^aefp]", "", t.lower())
    return (d[-2:], l)
want = key(period)
def norm(v):
    return re.sub(r"[\s,]", "", v.lower()).rstrip(".")
out = []
def scan(lines, how):
    heads, items = [], []
    for line in lines:
        toks = line.split()
        pers = [t for t in toks if PER.match(t)]
        if len(pers) >= 2 and any(key(t) == want or (key(t)[0] == want[0] and not want[1]) for t in pers):
            heads.append((line, pers))
        low = line.lower()
        if words and all(w in low for w in words):
            items.append((line, toks))
    for line, pers in heads[-2:]:
        out.append({"how": how, "kind": "header", "line": line.strip()[:220]})
    for line, toks in items[:3]:
        out.append({"how": how, "kind": "item", "line": line.strip()[:220]})
    if heads and items:
        line, pers = heads[-1]
        idx = next((i for i, t in enumerate(pers) if key(t) == want), None)
        if idx is None:
            idx = next((i for i, t in enumerate(pers) if key(t)[0] == want[0]), None)
        for iline, toks in items[:1]:
            vals = [t for t in toks if VAL.match(t)]
            if idx is not None and len(vals) == len(pers):
                at = vals[idx]
                out.append({"how": how, "kind": "aligned", "periods": pers, "values": vals, "at": at, "match": norm(at) == norm(value)})
            else:
                out.append({"how": how, "kind": "unaligned", "periods": pers, "values": vals})
for how, get in (("pdfium", "pdfium"), ("pdfplumber", "pdfplumber")):
    try:
        if get == "pdfium":
            import pypdfium2 as pdfium
            doc = pdfium.PdfDocument(pdf)
            lines = doc[page - 1].get_textpage().get_text_range().replace("\r", "\n").split("\n") if 1 <= page <= len(doc) else []
        else:
            import pdfplumber
            with pdfplumber.open(pdf) as d:
                lines = (d.pages[page - 1].extract_text() or "").split("\n") if 1 <= page <= len(d.pages) else []
        scan(lines, how)
    except Exception as error:
        out.append({"how": how, "error": "%s: %s" % (type(error).__name__, str(error)[:120])})
print(json.dumps(out[:24], ensure_ascii=False))
"""


def fin_fail_evidence(root: Path, vpy=None) -> list:
    """v0106:⑪ 年度數據 FAIL(值不在該頁)的證據 —— 讀原 PDF 那一頁找表頭(含該期間)與科目列,依欄位順序對齊 → 原文該期間的值 vs 冊值 →
    VRN2_FinFailEvidence_latest.json(進貼回包)。只讀。"""
    v2 = Path(root) / "VIA_Reports" / "vrn2"
    reps = sorted((v2 / "verify_independent").glob("VRN2_IndependentVerify_*.json"), key=_mtime) if (v2 / "verify_independent").is_dir() else []
    report = jread(reps[-1], {}) if reps else {}
    src_dir = (jread(v2 / "VRN2_Input_latest.json", {}) or {}).get("source_dir") or ""
    out = []
    for r in [x for x in (report or {}).get("fin_bad") or [] if x.get("_V") == "FAIL"][:8]:
        name = str(r.get("FILENAME"))
        pdf = next((p for p in (v2 / "scope_in" / name, Path(src_dir) / name if src_dir else None) if p and p.is_file()), None)
        lines = []
        if pdf and vpy:
            try:
                done = subprocess.run([vpy, "-X", "utf8", "-c", FIN_EVIDENCE_PY, str(pdf), str(r.get("PAGE") or 1), str(r.get("ITEM") or ""), str(r.get("PERIOD") or ""), str(r.get("VALUE") or "")],
                                      capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
                lines = json.loads((done.stdout.strip().splitlines() or ["[]"])[-1])
            except Exception as error:  # noqa: BLE001
                lines = [{"error": "%s: %s" % (type(error).__name__, str(error)[:160])}]
        out.append({"file": name, "page": r.get("PAGE"), "item": r.get("ITEM"), "period": r.get("PERIOD"), "value": r.get("VALUE"), "note": r.get("_N"), "pdf": str(pdf or ""),
                    "lines": lines if pdf else [{"error": "找不到原檔(scope_in / 來源夾)"}]})
    if out:
        try:
            (v2 / "VRN2_FinFailEvidence_latest.json").write_text(json.dumps({"at": _dt.datetime.now().isoformat(timespec="seconds"), "verifier": (report or {}).get("version"), "rows": out}, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass
    return out


EVIDENCE_FIELDS = ("CURRENT_PRICE_REPORT", "TARGET_PRICE", "UPSIDE_PCT", "RATING", "REPORT_DATE", "CURRENCY")


def fail_evidence(root: Path, vpy=None) -> list:
    """v0102:⑪ 基本資料 FAIL 的證據 = 冊值 + 原 PDF 前 4 頁含這些數或價格標籤的行(VRN-2 的 Python 用 pypdfium2 讀 · 只讀)→ VRN2_FailEvidence_latest.json。"""
    v2 = Path(root) / "VIA_Reports" / "vrn2"
    reps = sorted((v2 / "verify_independent").glob("VRN2_IndependentVerify_*.json"), key=_mtime) if (v2 / "verify_independent").is_dir() else []
    report = jread(reps[-1], {}) if reps else {}
    basic = {str(r.get("FILENAME")): r for r in (jread(v2 / "output" / "VRN2_BasicInfo_latest.json", []) or []) if isinstance(r, dict)}
    src_dir = (jread(v2 / "VRN2_Input_latest.json", {}) or {}).get("source_dir") or ""
    out = []
    for row in (report or {}).get("basic") or []:
        fails = {k: v for k, v in (row.get("checks") or {}).items() if str(v).startswith("FAIL")}
        if not fails:
            continue
        name = str(row.get("FILENAME"))
        rec = basic.get(name, {})
        values = {k: rec.get(k) for k in EVIDENCE_FIELDS if rec.get(k) not in (None, "")}
        pdf = next((p for p in (v2 / "scope_in" / name, Path(src_dir) / name if src_dir else None) if p and p.is_file()), None)
        lines = []
        if pdf and vpy:
            try:
                done = subprocess.run([vpy, "-X", "utf8", "-c", EVIDENCE_PY, str(pdf), json.dumps([[k, values.get(k)] for k in ("CURRENT_PRICE_REPORT", "TARGET_PRICE", "UPSIDE_PCT") if values.get(k)])],
                                      capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
                lines = json.loads((done.stdout.strip().splitlines() or ["[]"])[-1])
            except Exception as error:  # noqa: BLE001
                lines = [{"error": "%s: %s" % (type(error).__name__, str(error)[:160])}]
        out.append({"file": name, "fails": fails, "values": values, "pdf": str(pdf or ""), "lines": lines if pdf else [{"error": "找不到原檔(scope_in / 來源夾)"}]})
    if out:
        try:
            (v2 / "VRN2_FailEvidence_latest.json").write_text(json.dumps({"at": _dt.datetime.now().isoformat(timespec="seconds"), "verifier": (report or {}).get("version"), "files": out}, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass
    return out


def quality_fails(v2: Path) -> list:
    """v0102:⑥f 共識引擎品質矩陣裡 status = FAIL 的列(gate FAIL_CLOSED 的原因)。"""
    import csv
    path = Path(v2) / "consensus" / "factset_yfinance_consensus_quality_matrix.csv"
    if not path.is_file():
        return []
    try:
        with path.open(encoding="utf-8-sig", newline="") as fh:
            return [r for r in csv.DictReader(fh) if str(r.get("status", "")).upper() == "FAIL"]
    except (OSError, csv.Error):
        return []


def diagnose(root: Path, vpy=None) -> dict:
    v2 = Path(root) / "VIA_Reports" / "vrn2"
    rep = {"at": _dt.datetime.now().isoformat(timespec="seconds"), "findings": []}

    def f(lamp, area, text, nxt=""):
        rep["findings"].append({"lamp": lamp, "area": area, "finding": text, "next": nxt})
        say(lamp, "⑥ " + area, text, nxt)
    rp = receipt_path(v2)
    receipt = jread(rp, {}) or {}
    if not receipt:
        f("RED", "收尾收據", "沒有 %s" % (v2 / RECEIPT), "啟動器沒跑完:看 ④ 的最後幾行")
        return rep
    rep["rc"] = receipt.get("rc")
    f({0: "GREEN", 2: "YELLOW"}.get(receipt.get("rc"), "RED"), "收尾收據", "%s · rc %s · %s 秒 · %d 輪%s" % (receipt.get("version"), receipt.get("rc"), receipt.get("elapsed_s"), len(receipt.get("passes") or []), (" · RoundAll 補修 %d 步(rc 不改 · 原收據 %s.before_roundall.json)" % (len((receipt.get("roundall") or {}).get("fixed") or {}), rp.stem)) if receipt.get("roundall") else "")
      + ("" if rp.name == RECEIPT else " · 沿用前版收據 %s(這輪沒跑啟動器 %s)" % (rp.name, Path(RECEIPT).stem.split("_")[-1])))
    for s in receipt.get("steps") or []:
        if s.get("lamp") not in ("GREEN",):
            f(s.get("lamp", "GRAY"), "步驟 " + str(s.get("step", ""))[:40], str(s.get("detail", ""))[:220], advice_for(s.get("step", "")))
    vv = jread(v2 / "VRN2_VerbatimVerify_latest.json", {}) or {}
    bad = [r for r in vv.get("rows") or [] if r.get("state") not in ("PASS",)]
    if bad:
        lamp = "RED" if any(r.get("state") == "FAIL" for r in bad) else "YELLOW"
        f(lamp, "四點原文核對", "%s · %s · 不過 %d 點:%s" % (vv.get("verdict"), json.dumps(vv.get("counts") or {}, ensure_ascii=False), len(bad), " | ".join("%s 第 %s 點 %s(%s)" % (r.get("file"), r.get("point"), r.get("state"), r.get("match") or r.get("reason") or "") for r in bad[:8])[:600]),
          "FAIL = 第二讀取器在原文找不到完整摘錄 → 貼回包(含原 PDF 檔名)給 AI;OCR_PENDING = 影像頁等 OCR")
        summ = {str(r.get("FILENAME")): r for r in (jread(v2 / "output" / "VRN2_Summary_latest.json", []) or []) if isinstance(r, dict)}
        for r in [x for x in bad if x.get("state") == "FAIL"][:6]:
            text = str((summ.get(str(r.get("file"))) or {}).get("POINT_%s" % r.get("point")) or "")
            if text:
                f("RED", "四點 FAIL 摘錄", "%s 第 %s 點(第 %s 頁 · %s):%s" % (r.get("file"), r.get("point"), r.get("page") or "?", r.get("reason") or r.get("match") or "", text[:240]),
                  "這段字要在原 PDF 找得到一字不差;找不到的那幾個字就是摘要器拼錯 / 斷行合錯的地方")
    for g in receipt.get("output_gaps") or []:
        f("YELLOW", "輸出缺項", json.dumps(g, ensure_ascii=False)[:240], "缺年度數據 / 欄位 → 貼回包;原文沒有就是真的沒有")
    comp = jread(v2 / "VRN2_Completion_latest.json", {}) or {}
    for i in comp.get("items") or []:
        if i.get("lamp") in ("RED", "YELLOW"):
            f(i.get("lamp"), "完成判定 · " + str(i.get("name"))[:30], str(i.get("detail", ""))[:220])
    idem = jread(v2 / "IDEMPOTENCE_latest.json", {}) or {}
    if idem and idem.get("classification") != "GREEN":
        f("RED" if idem.get("classification") == "NONDETERMINISTIC" else "YELLOW", "冪等閘", "%s · %s" % (idem.get("classification"), json.dumps((idem.get("files") or [])[:2], ensure_ascii=False)[:240]), "看 evidence_directory 第一個差異路徑")
    pt = jread(v2 / "VRN2_Phase_Timing_latest.json", {}) or {}
    if pt.get("phases"):
        top = sorted(pt["phases"], key=lambda p: -float(p.get("seconds") or 0))[:3]
        f("GRAY", "階段耗時", "總 %s 秒 · 最慢 %s" % (pt.get("total_s"), " · ".join("%s %.0f" % (p.get("phase"), float(p.get("seconds") or 0)) for p in top)))
    comb = jread(v2 / "output" / "VRN2_Combined_latest.json", None)
    cons = jread(v2 / "consensus" / "VRN2_Consensus_latest.json", {}) or {}
    if isinstance(comb, list) and comb:
        n = int(cons.get("year_n") or _dt.date.today().year)
        want = COMBINED_HEAD + ["%d_DILUTED_EPS_FACTSET" % y for y in (n, n + 1, n + 2)] + ["%d_PER_FACTSET" % y for y in (n, n + 1, n + 2)] + COMBINED_TAIL
        cols = list(comb[0].keys())
        empty = {c: sum(1 for r in comb if not str(r.get(c) or "").strip()) for c in ("TARGET_PRICE(ADJ)", "FACTSET_TARGET_PRICE_MEDIAN", "YFINANCE_TARGET_PRICE_MEDIAN", "%d_DILUTED_EPS_FACTSET" % n)}
        cctx = closeout_context(root)                                     # v0104 空格照原因分(原文沒有目標價不是缺)
        gaps, gap_owner = cctx["combined_gaps"], cctx["combined_owner"]
        f("GREEN" if cols == want and gap_owner is None else "YELLOW", "Combined 冊", "%d 列 · 欄序%s · 空格 %s%s" % (len(comb), "正確" if cols == want else "不同(%s)" % [c for c in want if c not in cols][:4], json.dumps(empty, ensure_ascii=False),
          (" · 原因 " + json.dumps(gaps, ensure_ascii=False)) if gaps else ""),
          "" if gap_owner is None else "原文沒有目標價 = 不是缺;沒有市場資料 = ⑥e;鉅亨 404 / 來源沒有這欄 = 資料源本來沒有;其他看 STATUS 欄")
    else:
        f("YELLOW", "Combined 冊", "沒有 output\\VRN2_Combined_latest.json", "⑥f 沒跑:看 ⑥f 那行")
    wb = v2 / "VRN2_Workbench_latest.html"
    if wb.is_file():
        page = wb.read_text(encoding="utf-8", errors="replace")
        miss = [label for mark, label in WORKBENCH_MARKS if mark not in page]
        f("GREEN" if not miss else "YELLOW", "Workbench U/I", "%s · %s" % (wb, "雙語表頭 / 靠上 / 千分位 / 自動縮放 / 輸出夾格 / 第一區 都在" if not miss else "缺 " + "、".join(miss)))
    else:
        f("YELLOW", "Workbench U/I", "沒有 %s" % wb, "⑤ 自動修會重渲染")
    step_e = next((s for s in receipt.get("steps") or [] if str(s.get("step", "")).startswith("⑥e")), {})
    err = v2 / "market" / "vdf" / "last_error.txt"
    if step_e.get("lamp") not in (None, "GREEN") and err.is_file():
        tail = [l.strip() for l in err.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()][-6:]
        f("YELLOW", "⑥e 擷取錯誤(last_error.txt)", " | ".join(tail)[:600], "VDF 引擎自己的錯誤(VRN-2 只讀不改)· 網路 / 憑證 / 套件 → 照錯誤處理;整段在貼回包 vrn2/market/vdf/last_error.txt")
        whole = err.read_text(encoding="utf-8", errors="replace")
        if "Existing VIA network bridge denied" in whole:                   # v0103
            f("YELLOW", "⑥e MOPS 財報被拒(VIA 網路工具 DENY)", "VDF 引擎打 MOPS(公開資訊觀測站)財報時,VIA 鎖版網路工具的合規層回 DENY → PermissionError;VDF / VRN-2 照規則不繞道 → 沒有歷史財報 → ⑬b 無歷史",
              "要不要放行 mops.twse.com.tw 是 VCGC(鎖版網路工具)的決定;價格 / 還原價(TWSE / TPEX / Yahoo)不受影響")
    run_c = (receipt.get("consensus") or {}).get("run") or {}
    cons_rec = jread(v2 / "consensus" / "VRN2_Consensus_latest.json", {}) or {}
    if cons_rec.get("yf_404") or cons_rec.get("yf_ticker_map"):
        ym = cons_rec.get("yf_ticker_map") or {}
        f("YELLOW" if cons_rec.get("yf_404") else "GREEN", "⑥f Yahoo 代號", "對應表 %s 筆 · 上櫃 .TWO %d(%s)· Yahoo 404:%s" % (ym.get("codes", 0), len(ym.get("tpex") or []), ",".join((ym.get("tpex") or [])[:12]), ",".join(cons_rec.get("yf_404") or []) or "無"),
          "" if not cons_rec.get("yf_404") else "404 的代號 Yahoo 沒有 → 共識只有 FactSet;若是上櫃卻還是 .TW → 市場冊沒有它的 yfinance_ticker(先讓 ⑥e 綠)")
    elif run_c.get("why"):
        rep.setdefault("consensus_why", run_c.get("why"))
    market = jread(v2 / "market" / "VRN2_Market_latest.json", {}) or {}
    if market.get("per_file"):
        st = {}
        for r in market["per_file"].values():
            st[r.get("status", "?")] = st.get(r.get("status", "?"), 0) + 1
        f("GREEN" if set(st) <= {"OK"} else "YELLOW", "市場資料", "%s · %s" % (str(market.get("ts", ""))[:19], json.dumps(st, ensure_ascii=False)))
    hist = jread(v2 / "VRN2_HistoryAlign_latest.json", {}) or {}
    if hist:
        f(hist.get("lamp", "GRAY"), "歷史對齊", str(hist.get("why", ""))[:240])
    store = jread(v2 / "VRN2_OutputStore_latest.json", {}) or {}
    if store:
        f(store.get("lamp", "GRAY"), "長線 Parquet 庫", "%s · %s · 累計 %s" % (store.get("output_dir", "未設定"), store.get("store_engine", ""), json.dumps(store.get("totals") or {}, ensure_ascii=False)))
    integ = jread(v2 / "VRN2_Integrate_latest.json", {}) or {}
    if integ:
        f(integ.get("lamp", "GRAY"), "舊資料庫整合", "%s · %s" % (integ.get("state"), str(integ.get("why", ""))[:200]))
    req = jread(Path(root) / "functional modules" / "VRN2" / "contract" / "VRN2_NUMBER_REQUEST_latest.json", {}) or {}
    if req:
        f("GRAY", "SSOT-ID 請求", "待核號 %d · 提案 %s · 自撞 %d(等 VCGC 核發)" % (len(req.get("pending") or []), (req.get("counts") or {}).get("proposals", 0), len(req.get("self_conflicts") or [])))
    fpick = (receipt.get("market") or {}).get("fetch_python") or {}
    if fpick and not fpick.get("python"):
        rows = fpick.get("candidates") or []
        f("YELLOW", "⑥e 擷取 Python(VDF 版本界線)", "沒有合界線的 · " + " | ".join("%s(%s):%s" % (r.get("how"), r.get("py_version"), " ".join((r.get("missing") or []) + ["匯入失敗 " + x for x in r.get("import_failed") or []]) or "?") for r in rows)[:600],
          "交 VCGC 建 via_tw_fetch(帶界線):" + " ; ".join(vcgc_fetch_commands()[2:]))
    elif fpick.get("python"):
        f("GREEN", "⑥e 擷取 Python(VDF 版本界線)", "%s · %s" % (fpick.get("python"), fpick.get("requirements_from", "")))
    qf = quality_fails(v2)
    if qf:
        codes = sorted({str(r.get("code")) for r in qf})
        f("YELLOW", "⑥f 共識閘 FAIL 列", "%d 列 · 代號 %s · %s" % (len(qf), ",".join(codes[:12]), " | ".join("%s %s 實際 %s 應為 %s(%s)" % (r.get("code"), r.get("check_id"), r.get("actual"), r.get("expected"), str(r.get("note", ""))[:60]) for r in qf[:6]))[:700],
          "共識引擎(原樣內附)品質閘不過就 FAIL_CLOSED;FactSet 沒有覆蓋的代號(未評等 / 新上市)= 真的沒有,其餘看 quality_matrix.csv")
    gap = cons_rec.get("source_gap") or {}
    if gap:                                                                   # v0110 ConsensusJoin v0103 重試後仍抓不到
        tries = cons_rec.get("retries") or []
        f("YELLOW", "⑥f 鉅亨這次沒給資料", "%d 檔 · %s · 重試 %d 次(等 %s 秒)· 這幾檔不納入閘、其他代號照評 · Combined 那幾列寫「鉅亨這次沒給資料」" % (
            len(gap), " | ".join("%s 抓了 %s 次:%s" % (c, (v or {}).get("tries"), str((v or {}).get("why") or "")[:80]) for c, v in sorted(gap.items())[:6]),
            len(tries), " / ".join(str(t.get("wait_s")) for t in tries) or "—"),
          "鉅亨對這幾檔回的頁沒有資料(例:ASSIGNED_JSON_NOT_FOUND = 頁面沒有 __NEXT_DATA__)· 不是 VRN-2 的程式 · 下輪再抓")
    reps = sorted((v2 / "verify_independent").glob("VRN2_IndependentVerify_*.json"), key=_mtime) if (v2 / "verify_independent").is_dir() else []
    if reps:
        ver = str((jread(reps[-1], {}) or {}).get("version") or "?")
        num = re.search(r"_v(\d{4})$", ver)
        new_enough = bool(num) and int(num.group(1)) >= 114                # v0108:v0114 起年度 FAIL 依欄位對齊(v0113 起 BADITEM 先用第二種讀法)
        f("GREEN" if new_enough else "YELLOW", "⑪ 驗證器版本", "%s · %s" % (ver, reps[-1].name),
          "" if new_enough else "還是舊驗證器(v0114 以前:年度 FAIL / BADITEM 只用字元框讀法)→ 套件 v0154 的 runtime 沒還原進 functional modules\\VRN2?看 ④ 的 runtime 那行")
    for ev in fail_evidence(root, vpy):
        err = next((r["error"] for r in ev["lines"] if r.get("error")), "")
        per = []                                                          # v0103 逐值:每個冊值各列數字相等的行(跳過 Email / 電話)
        for k in ("CURRENT_PRICE_REPORT", "TARGET_PRICE", "UPSIDE_PCT"):
            if ev["values"].get(k):
                rows = [r for r in ev["lines"] if k in (r.get("values") or [])][:2]
                per.append("%s %s → %s" % (k, ev["values"][k], " / ".join("第 %s 頁「%s」" % (r.get("page"), r.get("line")) for r in rows) if rows else "前 4 頁沒有這個數"))
        f("YELLOW", "⑪ 基本資料 FAIL 證據", "%s · %s · %s" % (ev["file"], " / ".join("%s %s" % (k, str(v)[:70]) for k, v in ev["fails"].items()), " | ".join(per)[:700] or err or "前 4 頁沒有對到的行"),
          "冊值與原文那行對不上 = 擷取取錯數;原文那行就是對的值 = 驗證器誤判。整份在 VRN2_FailEvidence_latest.json(貼回包裡)")
    for ev in fin_fail_evidence(root, vpy):                               # v0106 ⑪ 年度數據 FAIL:原文表頭 + 科目列對齊
        al = next((x for x in ev["lines"] if x.get("kind") == "aligned"), None)
        heads = [x["line"] for x in ev["lines"] if x.get("kind") == "header"][:1]
        items = [x["line"] for x in ev["lines"] if x.get("kind") == "item"][:1]
        err = next((x["error"] for x in ev["lines"] if x.get("error")), "")
        tag = "" if not al else ("(驗證器讀法 · 原文相符)" if al["match"] else "(擷取對錯欄)")
        verdict = ("原文 %s 這一欄是 %r(冊值 %r)→ %s" % (ev["period"], al["at"], ev["value"], "冊值 = 原文,是驗證器讀法沒找到" if al["match"] else "冊值 ≠ 原文,擷取對錯欄")) if al else "原文表頭與科目列對不齊(欄數不同或找不到)· 要人看"
        f("YELLOW", "⑪ 年度數據 FAIL 證據" + tag, "%s 第 %s 頁 · %s %s = %r · %s · 表頭「%s」· 科目列「%s」%s" % (ev["file"], ev["page"], ev["item"], ev["period"], ev["value"], verdict,
          heads[0] if heads else "沒找到", items[0] if items else "沒找到", (" · " + err) if err and not al else ""),
          "整份在 VRN2_FinFailEvidence_latest.json(貼回包裡)· 擷取對錯欄 → 改擷取;冊值 = 原文 → 改驗證器;對不齊 → 看原 PDF 那一頁")
    digests = sorted((v2 / "verify_independent").glob("*.digest.txt"), key=_mtime) if (v2 / "verify_independent").is_dir() else []
    if digests:
        head = digests[-1].read_text(encoding="utf-8", errors="replace").splitlines()[:3]
        f("GRAY", "獨立驗證摘要", "%s · %s" % (digests[-1].name, " / ".join(h.strip() for h in head)[:240]))
    return rep


# ===== 9b. ⑧ 收尾頁(v0104 · HTML U/I · CLOSE OUT)=====
CLOSEOUT_HTML = "VRN2_CloseoutUI_latest.html"
CLOSEOUT_JSON = "VRN2_CloseoutUI_latest.json"
OWNERS = (("VRN-2", "VRN-2 要修", "VRN-2 自己的程式 / 輸出還有問題 → 貼回包給 AI 修(出新版號 · 舊版不動)"),
          ("VCGC", "交 VCGC", "環境安裝 / 鎖版網路工具放行 / 核號是 VCGC 的決定 · VRN-2 只檢查、照規則不繞道"),
          ("人工", "人工核對", "影像頁 OCR 摘錄 · 驗證器標的待核對值 · 缺年度數據 → 先看原 PDF 再判(擷取錯 / 驗證器誤判 / 原文真的沒有)"),
          ("資料源", "資料源沒有", "外部來源本來就沒有(鉅亨沒有這檔的 FactSet 頁 404 · Yahoo / TWSE 沒有這天)· 已附證據 · 不是 VRN-2 的錯"),
          ("提醒", "提醒(不擋)", "管理器自己標「提醒 · 不擋完成」/ 剔除列帶理由在 Rejected 冊"),
          ("彙總", "彙總", "啟動器的 rc 由各步驟燈號而來 → 看分項"))
OWNER_RANK = {"VRN-2": 3, "VCGC": 2, "人工": 1.5, "資料源": 1}
STATES = {"OPEN": ("未結案", "VRN-2 還有 %d 項要修"), "BLOCKED": ("等 VCGC", "VRN-2 側沒有待修 · %d 項等 VCGC 決定 / 安裝"),
          "REVIEW": ("等人工核對", "VRN-2 側沒有待修 · %d 項要人看原文"), "DATA_GAP": ("資料源缺口", "VRN-2 側結案 · %d 項是外部來源沒有(已附證據)"),
          "PASS": ("結案", "全綠(或只剩提醒)")}
_NO_PAGE = re.compile(r"statusCode=404|頁面或商品不存在|鉅亨沒有 FactSet 頁")
_TRANSIENT = re.compile(r"ASSIGNED_JSON_NOT_FOUND|NEXT_DATA_NOT_OBJECT|PAGE_PROPS_NOT_OBJECT|JSON_DECODE_FAILED|HTTP_GET_FAILED|HTTP_STATUS_(?:408|425|429|5\d\d)"
                        r"|HTTP Error (?:408|425|429|5\d\d)|timed out|[Tt]imeout|Connection ?(?:[Rr]eset|aborted|refused)|RemoteDisconnected|IncompleteRead|Temporary failure")   # v0110 同 ConsensusJoin v0103
_PERMANENT = re.compile(r"HTTP Error (?:400|401|403|404|410)\b")
_LISTS = re.compile(r"(?:鉅亨沒有 FactSet 頁\(404\)|鉅亨這次沒給資料\(抓了 \d+ 次\)暫)不納入閘:[\d,]+")   # v0110 整批摘要裡的代號清單(不是這一列自己的原因)


def gate_rows(v2) -> tuple:
    """v0110 共識品質閘不過的列 → (404 代號, 一時抓不到的代號, 其他代號)· 分法同 ConsensusJoin v0103。"""
    nopage, transient, other = set(), set(), set()
    for r in quality_fails(v2) if Path(v2).is_dir() else []:
        code, text = str(r.get("code") or "").strip(), "%s %s" % (r.get("actual") or "", r.get("note") or "")
        if _NO_PAGE.search(text):
            nopage.add(code)
        elif str(r.get("check_id") or "") == "FETCH_PIPELINE" and _TRANSIENT.search(text) and not _PERMANENT.search(text):
            transient.add(code)
        else:
            other.add(code)
    return nopage, transient, other


def combined_consensus_only(gaps: dict) -> bool:
    """v0110 Combined 算到 VRN-2 的空格全是「共識缺」(⑥f 沒抓到的後果)→ 收尾頁跟 ⑥f 算同一件事。"""
    adj = [w for w in (gaps.get("TARGET_PRICE(ADJ)") or {}) if not re.search(r"原文沒有目標價|沒有市場資料|代號不是台股 4 碼|報告日前沒有日資料|MISSING|沒有目標價或還原因子", w)]
    cons = [w for col, d in gaps.items() if col not in ("TARGET_PRICE(ADJ)", "_files") and isinstance(d, dict) for w in d if w.startswith("共識缺:") and not re.search(r"yfinance|via_tw_fetch|擷取環境", w)]
    return not adj and bool(cons)


def combined_gaps(comb, no_cov=(), fetch_env_ok=None, gap=()) -> tuple:
    """v0104 Combined 空格照原因分 → ({欄: {原因: 筆數}}, 負責方 | None):原文沒有目標價 = 不是缺(None)· 沒有市場資料 → 擷取環境不合就 VCGC、否則資料源 ·
    報告日前沒有日資料 / 沒有還原因子 → 資料源 · 共識沒有這檔(鉅亨 404)→ 資料源 · 共識缺 yfinance / via_tw_fetch → VCGC · 共識有這檔但來源沒有這欄 → 資料源 · 其他 → VRN-2。"""
    gaps, owner, files = {}, None, {}
    eps = sorted(c for c in ((comb or [{}])[0] or {}) if re.fullmatch(r"\d{4}_DILUTED_EPS_FACTSET", str(c)))[:1]

    def add(col, why, who, fname=""):
        nonlocal owner
        gaps.setdefault(col, {})
        gaps[col][why] = gaps[col].get(why, 0) + 1
        if who and fname and len(files.setdefault(why, [])) < 6 and fname not in files[why]:   # v0106 哪幾份檔(原文沒有目標價不列)
            files[why].append(fname)
        if who and (owner is None or OWNER_RANK[who] > OWNER_RANK[owner]):
            owner = who
    for r in comb or []:
        if not isinstance(r, dict):
            continue
        st = str(r.get("STATUS") or "")
        m0 = re.match(r"\s*(\d{4,6})", str(r.get("TICKER") or ""))
        code = m0.group(1) if m0 else ""
        if not str(r.get("TARGET_PRICE(ADJ)") or "").strip():
            if not str(r.get("TARGET_PRICE") or "").strip():
                add("TARGET_PRICE(ADJ)", "原文沒有目標價", None)
            else:
                m = re.search(r"TARGET_PRICE\(ADJ\): 缺:([^|]*)", st)
                why = m.group(1).strip() if m else "沒有說明"
                fname = str(r.get("FILENAME") or "")
                if "沒有市場資料" in why:
                    add("TARGET_PRICE(ADJ)", "沒有市場資料(⑥e)", "VCGC" if fetch_env_ok is False else "資料源", fname)
                elif "代號不是 4 碼" in why:                                  # v0106:冊裡 TICKER 空白 → 人工(原文有沒有印代號)· 有值但不是台股 4 碼 → 資料源
                    tk = str(r.get("TICKER") or "").strip()
                    add("TARGET_PRICE(ADJ)", "基本資料冊代號不是台股 4 碼(TICKER %s)" % (repr(tk) if tk else "空白"), "資料源" if tk else "人工", fname)
                elif re.search(r"報告日前沒有日資料|MISSING|沒有目標價或還原因子", why):
                    add("TARGET_PRICE(ADJ)", why[:40], "資料源", fname)
                else:
                    add("TARGET_PRICE(ADJ)", why[:40], "VRN-2", fname)
        for col in ["FACTSET_TARGET_PRICE_MEDIAN", "YFINANCE_TARGET_PRICE_MEDIAN"] + eps:
            if col in r and not str(r.get(col) or "").strip():
                st_row = _LISTS.sub("", st)                                    # v0110 整批摘要的代號清單不算這一列的原因
                m = re.search(r"CONSENSUS: 缺:([^|]*)", st_row)
                fname = str(r.get("FILENAME") or "")
                if (code and code in no_cov) or _NO_PAGE.search(st_row):
                    add(col, "鉅亨沒有這檔的 FactSet 頁(404)", "資料源", fname)
                elif (code and code in gap) or "鉅亨這次沒給資料" in st_row:
                    add(col, "鉅亨這次沒給資料(暫缺 · 下輪再抓)", "資料源", fname)
                elif "共識引擎這次沒有產出" in st_row:
                    add(col, "共識引擎這次沒有產出(整批沒抓到)", "資料源", fname)
                elif not code:                                                 # v0111 代號不是台股 4 碼 → 共識不查(同調整後目標價的規則)
                    tk = str(r.get("TICKER") or "").strip()
                    add(col, "代號不是台股 4 碼(TICKER %s)· 共識只查台股" % (repr(tk) if tk else "空白"), "資料源" if tk else "人工", fname)
                elif m:
                    why = m.group(1).strip()
                    add(col, "共識缺:" + why[:40], "VCGC" if re.search(r"yfinance|via_tw_fetch|擷取環境", why) else "VRN-2", fname)
                else:
                    add(col, "共識有這檔 · 來源沒有這欄", "資料源", fname)
    if files:
        gaps["_files"] = files
    return gaps, owner


def closeout_context(root) -> dict:
    """收尾頁判負責方要的事實(只讀):MOPS 被 VIA 網路工具 DENY · 擷取環境合不合 VDF 界線 · 鉅亨沒有 FactSet 頁的代號 · 共識閘別的不過 · Combined 空格原因。"""
    v2 = Path(root) / "VIA_Reports" / "vrn2" if root else Path(".")
    err = v2 / "market" / "vdf" / "last_error.txt"
    text = err.read_text(encoding="utf-8", errors="replace") if err.is_file() else ""
    receipt = jread(receipt_path(v2), {}) or {}
    fpick = (receipt.get("market") or {}).get("fetch_python")
    cons = jread(v2 / "consensus" / "VRN2_Consensus_latest.json", {}) or {}
    no_cov = {str(c) for c in (cons.get("no_coverage") or {})}
    q404, qtr, other = gate_rows(v2)                                          # v0110 一時抓不到另算(不再當成「別的不過」)
    no_cov |= q404
    ctx = {"receipt": bool(receipt), "mops_deny": "Existing VIA network bridge denied" in text, "fetch_env_ok": (bool(fpick.get("python")) if isinstance(fpick, dict) else None),
           "no_cov": no_cov - other - qtr, "gate_other": other, "gate_transient": qtr, "source_gap": {str(c): v for c, v in (cons.get("source_gap") or {}).items()},
           "cj_v0103": "retries" in cons, "engine_no_output": cons.get("engine_no_output")}
    comb = jread(v2 / "output" / "VRN2_Combined_latest.json", None)
    ctx["combined_gaps"], ctx["combined_owner"] = combined_gaps(comb if isinstance(comb, list) else [], ctx["no_cov"], ctx["fetch_env_ok"], set(ctx["source_gap"]))
    ctx["combined_now"] = isinstance(comb, list) and bool(comb)
    return ctx


def owner_of(row: dict, ctx: dict):
    """一列結果的負責方(綠 / 灰 → None)· 認不出來的一律 VRN-2(寧可把 VRN-2 留在未結案,也不把別人的事說成結案)。回 (負責方, 理由)。"""
    lamp, step, detail = row.get("lamp"), str(row.get("step", "")), str(row.get("detail", ""))
    if lamp in ("GREEN", "GRAY", None):
        return None
    text = step + " " + detail
    if step.startswith("② CPU"):                                             # v0106
        return "提醒", "CPU 被別的程式佔用 · 啟動器自動降平行路數(只會慢 · 不影響結果)"
    if ctx.get("receipt") and (step == "⑥ 收尾收據" and " rc " in detail or step.startswith("④ 跑啟動器") and re.search(r"rc [12] ", detail)):
        return "彙總", "啟動器 rc 由各步驟燈號合成 · 分項在下面各列"
    if "不擋完成" in detail or step.startswith("⑥ 完成判定 · 輸出值驗證"):
        return "提醒", "管理器標「提醒 · 不擋完成」/ 剔除列帶理由(output\\VRN2_Rejected_latest)"
    if re.search(r"③ 環境檢查|② VRN-2 套件|② 擷取 Python|⑥e 擷取 Python", step):
        return "VCGC", "缺套件 / 擷取環境不合 VDF 界線 → VCGC 安裝(VRN-2 只檢查 · 不 pip)"
    if re.search(r"輸出", step) and re.search(r"未選|未設定|沒有選", detail):
        return "人工", "在 Workbench 左欄「選擇輸出夾…」選一個(操作員決定)"
    if re.search(r"增量庫|Parquet 庫", step) and "pyarrow" in detail:
        return "VCGC", "沒有 duckdb → pyarrow 備援(資料照寫)· 裝 duckdb 交 VCGC"
    if re.search(r"MOPS|network bridge denied|網路工具 DENY", text):
        return "VCGC", "VIA 鎖版網路工具 DENY MOPS(公開資訊觀測站)→ 放不放行是 VCGC 的決定 · VDF / VRN-2 不繞道"
    if "⑥e" in step or step.startswith("⑥ 市場資料"):
        if ctx.get("fetch_env_ok") is False or re.search(r"沒有合 VDF|匯入失敗|缺 yfinance", detail):
            return "VCGC", "擷取環境不合 VDF 界線 → VCGC 建 via_tw_fetch(帶界線)"
        if step.startswith("⑥ 市場資料"):                          # 價格 / 還原價不經 MOPS:缺的檔是來源沒有
            return "資料源", "TWSE / TPEX / Yahoo 沒有這檔 / 這天的價格(MISSING 的檔看 market\\VRN2_Market_latest.json)"
        if ctx.get("mops_deny"):
            return "VCGC", "VDF 引擎打 MOPS 財報被 VIA 網路工具 DENY(價格照抓)→ VCGC 決定"
        return "VRN-2", ""
    if ("⑬b" in step or step.startswith("⑥ 歷史對齊")) and ctx.get("mops_deny"):
        return "VCGC", "沒有歷史財報 = MOPS 被 DENY 的結果"
    if step.startswith("⑥ Combined 冊"):
        if re.search(r"欄序不同|沒有 output", detail):
            return "VRN-2", "Combined 冊欄序不對 / 沒組出來"
        own = ctx.get("combined_owner")
        return (own or "資料源"), "空格原因:%s" % json.dumps(ctx.get("combined_gaps") or {}, ensure_ascii=False)[:200]
    if "⑥f" in step:
        if "Yahoo 代號" in step:
            return "資料源", "Yahoo 沒有這些代號"
        if "共識閘 FAIL 列" in step or "鉅亨這次沒給" in step or re.search(r"共識 (YELLOW|RED)|共識合併 v\d{4} · run", detail):
            if re.search(r"缺 yfinance|擷取環境缺", detail) or ctx.get("fetch_env_ok") is False and "共識 GREEN" not in detail:
                return "VCGC", "共識要 yfinance(擷取環境)→ VCGC 建 via_tw_fetch"
            if ctx.get("engine_no_output"):                                   # v0110 引擎這次沒有產出(品質矩陣 / 矩陣都是上次的 · 不看)
                return "資料源", ("共識引擎這次整批沒抓到(%s)· 上次的矩陣不沿用 · 網路被擋(VIA 網路工具 / 代理)→ 交 VCGC · 鉅亨沒回 → 下輪再抓"
                                  % str((ctx["engine_no_output"] or {}).get("last") or "")[:80])
            if ctx.get("gate_other"):                                         # v0110 404 / 一時抓不到以外的不過
                return "VRN-2", "共識閘有 404 / 一時抓不到以外的不過(%s)→ 看 consensus\\factset_yfinance_consensus_quality_matrix.csv" % ",".join(sorted(ctx["gate_other"]))
            if ctx.get("gate_transient") and not ctx.get("cj_v0103"):
                return "VRN-2", ("%s 一時抓不到(第一次有):ConsensusJoin v0103 以前拿掉 404 代號再跑時代號清單變了 → 引擎 checkpoint 對不上 → 整批重抓"
                                 " → v0103 起沿用今天抓到的 · ⑤ 自動修用 v0103 重跑 ⑥f" % ",".join(sorted(ctx["gate_transient"])))
            if ctx.get("gate_transient"):
                return "資料源", "鉅亨整批沒給資料(%s · ConsensusJoin v0103 重試後仍抓不到)· 下輪再抓" % ",".join(sorted(ctx["gate_transient"]))
            if ctx.get("source_gap"):
                tries = max(int((v or {}).get("tries") or 1) for v in ctx["source_gap"].values())
                return "資料源", "鉅亨這次沒給 %s 的資料(抓了 %d 次仍沒有 · 下輪再抓)%s · 其他代號閘照評" % (
                    ",".join(sorted(ctx["source_gap"])), tries, (" · 沒有 FactSet 頁(404):%s" % ",".join(sorted(ctx["no_cov"]))) if ctx.get("no_cov") else "")
            if ctx.get("no_cov"):
                return "資料源", "鉅亨沒有 %s 的 FactSet 頁(404)· 其他代號閘照評" % ",".join(sorted(ctx["no_cov"]))
            return "VRN-2", ""
        if re.search(r"Combined (YELLOW|RED)", detail):
            if ctx.get("combined_owner") is None and ctx.get("combined_now"):     # v0105:啟動器當時的 Combined 黃 · ⑤ 重組後只剩原文沒有目標價
                return "提醒", "⑥f 那時的 Combined 黃已被 ⑤ 重組蓋過 · 現在的 Combined 只剩原文沒有目標價的空格(不是缺)"
            return (ctx.get("combined_owner") or "資料源"), "Combined 空格原因:%s" % json.dumps(ctx.get("combined_gaps") or {}, ensure_ascii=False)[:200]
        return "VRN-2", ""
    if "四點" in step:
        if lamp == "RED" or "FAIL 摘錄" in step:
            return "VRN-2", "摘要器的摘錄跟原文不一樣(一字不差才算)"
        return "人工", "影像頁(OCR)摘錄要對原圖"
    if step.startswith("⑥ 輸出缺項") or step.startswith("⑥ 完成判定 · 輸出冊"):
        return "人工", "先看原 PDF:原文真的沒有年度數據 / 欄位就是沒有;有 → 貼回包給 AI"
    if "⑪" in step:
        dk = re.search(r"'DUPKEY': (\d+)", detail)
        if dk and int(dk.group(1)) > 0 and "FAIL 證據" not in step:                # v0109:驗證器自己寫「錯值 / 分不出」→ 輸出冊的事
            return "VRN-2", ("年度數據同鍵兩值 DUPKEY %s(同一列同科目同期間兩個不同的值 · 並排的另一張表 / 沒有列號)→ 管理器 v0257 起處理(改名 / 剔除)"
                             "· 舊輸出冊要整輪重跑" % dk.group(1))
        if "年度數據 FAIL 證據" in step and re.search(r"擷取對錯欄|驗證器讀法", step):   # v0106:原文對齊得出結論 → VRN-2 要修(擷取或驗證器)
            return "VRN-2", "原文表頭 + 科目列依欄位對齊得出結論(見內容)· 擷取對錯欄 → 改擷取;冊值 = 原文 → 改驗證器"
        if lamp == "RED" or re.search(r"逾時|Traceback", detail):
            return "VRN-2", "驗證器沒跑完(逾時 / 例外)"
        if "驗證器版本" in step:
            return "VRN-2", "還在用舊驗證器 → runtime 沒還原"
        return "人工", "驗證器標的待核對值:冊值 vs 原文那行(貼回包 VRN2_FailEvidence_latest.json · 獨立驗證摘要)"
    if "SSOT-ID" in step:
        return "VCGC", "等 VCGC 核號"
    return "VRN-2", ""


def closeout_root(item: dict, ctx: dict) -> str:
    """v0109 同一件事的幾列 → 同一個根(收尾頁只列一次 · 數負責方算一件):⑪b 與收據的 ⑪ = 同一份驗證結果 · 四點原文核對與「輸出缺項 · 四點原文核對」=
    同一批 OCR 摘錄 · ⑥e 步驟列 / last_error / MOPS 說明 = 同一個 MOPS DENY。認不出來的不合併(空字串)。"""
    step, detail, owner = str(item.get("step", "")), str(item.get("detail", "")), item.get("owner")
    if re.match(r"(⑪b 重跑獨立驗證|⑥ 步驟 ⑪ 獨立驗證)", step):
        return "⑪ 獨立驗證"
    if owner == "人工" and ("四點原文核對" in step or (step.startswith("⑥ 輸出缺項") and "四點原文核對" in detail)):
        return "人工|四點原文 OCR"
    if owner == "VCGC" and ctx.get("mops_deny") and re.match(r"⑥ (步驟 ⑥e 市場擷取|⑥e 擷取錯誤|⑥e MOPS)", step):
        return "VCGC|⑥e MOPS DENY"
    if "⑥f" in step and "Yahoo 代號" not in step:                          # v0110 ⑥f 步驟列 · 共識閘 FAIL 列 · 鉅亨這次沒給 · ⑤ 修 ⑥f = 同一次共識
        return "⑥f 共識"
    if step.startswith("⑥ Combined 冊") and owner == "VRN-2" and combined_consensus_only(ctx.get("combined_gaps") or {}):   # v0110 VRN-2 的空格全是 ⑥f 的後果
        return "⑥f 共識"
    return ""


def merge_same(items: list, ctx: dict) -> list:
    """v0109 同一個根的列合成一列:負責方取最重的(VRN-2 > VCGC > 人工 > 資料源)· 燈取最差的 · 內容取負責方最重那列 · 另見哪幾列寫進「為什麼」。順序照第一次出現。"""
    groups, order = {}, []
    for it in items:
        k = closeout_root(it, ctx)
        key = k or ("#%d" % len(order))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(it)
    out = []
    for key in order:
        members = groups[key]
        if len(members) == 1:
            out.append(members[0])
            continue
        lead = max(members, key=lambda m: (OWNER_RANK.get(m.get("owner"), 0), -members.index(m)))
        worst = min((m.get("lamp") for m in members), key=lambda l: {"RED": 0, "YELLOW": 1}.get(l, 2))
        also = [m["step"] for m in members if m is not lead]
        out.append(dict(lead, lamp=worst, also=also, why=(str(lead.get("why") or "") + " · 同一件事另見:" + "、".join(also))[:500]))
    return out


def closeout_state(items: list) -> tuple:
    """v0104 結案狀態:VRN-2 有項目 → OPEN · 否則有 VCGC → BLOCKED · 有人工 → REVIEW · 有資料源 → DATA_GAP · 都沒有 → PASS(提醒 / 彙總不算)。
    BLOCKED / REVIEW / DATA_GAP 都不是成功;VRN-2 側結案 = 不是 OPEN。"""
    n = {}
    for it in items:
        n[it["owner"]] = n.get(it["owner"], 0) + 1
    for state, owner in (("OPEN", "VRN-2"), ("BLOCKED", "VCGC"), ("REVIEW", "人工"), ("DATA_GAP", "資料源")):
        if n.get(owner):
            return state, STATES[state][1] % n[owner], n
    return "PASS", STATES["PASS"][1], n


def _h(t) -> str:
    import html as _html
    return _html.escape(str(t if t is not None else ""), quote=True)


def _uri(p) -> str:
    try:
        return Path(p).resolve().as_uri()
    except (ValueError, OSError):
        return ""


CLOSEOUT_CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#1b2430;--mute:#5d6b7c;--line:#dfe4ea;--accent:#2457c5;--green:#1f8a4c;--yellow:#a76a00;--red:#c0362c;--gray:#7b8794;
--chip-vrn2:#c0362c;--chip-vcgc:#6b4fbb;--chip-human:#a76a00;--chip-src:#2b7a9b;--chip-note:#7b8794;--chip-sum:#7b8794;--code:#eef1f5}
@media (prefers-color-scheme:dark){:root{--bg:#11161d;--card:#18202a;--ink:#e6ebf1;--mute:#9aa7b6;--line:#2a3542;--accent:#7aa2ff;--green:#4cc27f;--yellow:#e0a93a;--red:#ff7a6e;--gray:#8a96a3;
--chip-vrn2:#ff7a6e;--chip-vcgc:#a98bff;--chip-human:#e0a93a;--chip-src:#5fb8d9;--chip-note:#8a96a3;--chip-sum:#8a96a3;--code:#0f141a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 "Segoe UI","Microsoft JhengHei","PingFang TC","Noto Sans TC",system-ui,sans-serif}
header{display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:space-between;padding:18px 24px;background:var(--card);border-bottom:1px solid var(--line)}
h1{font-size:20px;margin:0}h2{font-size:16px;margin:0 0 10px}.sub{color:var(--mute);font-size:12px}
.brand{display:flex;gap:12px;align-items:center}.logo{white-space:nowrap;font-weight:700;letter-spacing:.5px;color:#fff;background:var(--accent);border-radius:8px;padding:6px 10px}
.state{border-radius:12px;padding:10px 16px;min-width:260px;border:2px solid currentColor}.state b{font-size:18px;display:block}.state span{font-size:12px}
.s-OPEN{color:var(--red)}.s-BLOCKED{color:var(--chip-vcgc)}.s-REVIEW{color:var(--yellow)}.s-DATA_GAP{color:var(--chip-src)}.s-PASS{color:var(--green)}
main{max-width:1280px;margin:0 auto;padding:18px 16px 40px;display:grid;grid-template-columns:minmax(0,1fr);gap:16px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;min-width:0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px}.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.kpi .k{color:var(--mute);font-size:12px}.kpi .v{font-size:24px;font-weight:700;font-variant-numeric:tabular-nums}
.v.green{color:var(--green)}.v.yellow{color:var(--yellow)}.v.red{color:var(--red)}.v.gray{color:var(--gray)}
.owners{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin-top:10px}
.owner{border:1px solid var(--line);border-left:4px solid var(--c);border-radius:10px;padding:10px 12px}.owner b{font-size:15px}.owner .n{float:right;font-weight:700;font-size:18px;color:var(--c)}
.owner p{margin:6px 0 0;color:var(--mute);font-size:12px}
.chip{display:inline-block;border-radius:999px;padding:1px 9px;font-size:12px;font-weight:600;color:#fff;background:var(--c);white-space:nowrap}
.c-VRN-2{--c:var(--chip-vrn2)}.c-VCGC{--c:var(--chip-vcgc)}.c-人工{--c:var(--chip-human)}.c-資料源{--c:var(--chip-src)}.c-提醒{--c:var(--chip-note)}.c-彙總{--c:var(--chip-sum)}
.lamp{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:middle}.l-GREEN{background:var(--green)}.l-YELLOW{background:var(--yellow)}.l-RED{background:var(--red)}.l-GRAY{background:var(--gray)}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px}.filters button{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:4px 12px;cursor:pointer;font:inherit}
.filters button.on{border-color:var(--accent);color:var(--accent);font-weight:600}.filters input{flex:1;min-width:180px;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:5px 10px;font:inherit}
.tablewrap{overflow-x:auto}table{border-collapse:collapse;width:100%}th,td{text-align:left;vertical-align:top;padding:7px 8px;border-bottom:1px solid var(--line)}th{font-size:12px;color:var(--mute);font-weight:600;white-space:nowrap}
td.lampcell{white-space:nowrap}td.detail{max-width:560px;word-break:break-word}td.next{max-width:360px;color:var(--mute);word-break:break-word}
dl.facts{display:grid;grid-template-columns:minmax(140px,220px) 1fr;gap:6px 14px;margin:0}dl.facts dt{color:var(--mute)}dl.facts dd{margin:0;word-break:break-word}
.links{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:8px}.links a,.links span{display:block;border:1px solid var(--line);border-radius:8px;padding:8px 10px;text-decoration:none;color:var(--ink)}
.links a:hover{border-color:var(--accent)}.links .miss{color:var(--mute);border-style:dashed}.links small{display:block;color:var(--mute);font-size:11px;word-break:break-all}
.cmd{display:flex;gap:8px;align-items:flex-start;margin:6px 0}.cmd code{flex:1;background:var(--code);border:1px solid var(--line);border-radius:8px;padding:8px 10px;font:12px/1.5 Consolas,"Cascadia Mono",monospace;word-break:break-all}
.cmd button{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:6px 10px;cursor:pointer;font:inherit}
.note{color:var(--mute);font-size:12px;margin:10px 0 0}.big{font-size:15px;margin:0}.primary{display:inline-block;margin-top:10px;background:var(--accent);color:#fff;border-radius:8px;padding:6px 14px;text-decoration:none}
details summary{cursor:pointer;font-weight:600}footer{color:var(--mute);font-size:12px;text-align:center;padding:0 16px 24px}
@media (max-width:640px){header{padding:14px 16px}.state{min-width:0;width:100%}dl.facts{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(3,minmax(0,1fr))}.kpi .v{font-size:20px}#items thead{display:none}#items,#items tbody,#items tr,#items td{display:block;width:100%}#items tr{border:1px solid var(--line);border-radius:10px;padding:8px 10px;margin-bottom:8px}#items td{border:none;padding:2px 0;max-width:none}#items td.lampcell{display:inline-block;width:auto;margin-left:8px}#items td:first-child{display:inline-block;width:auto}}
"""
CLOSEOUT_JS = """
(function(){var own='全部',q='';function apply(){document.querySelectorAll('#items tbody tr').forEach(function(tr){var ok=(own==='全部'||tr.dataset.owner===own)&&(!q||tr.textContent.toLowerCase().indexOf(q)>=0);tr.style.display=ok?'':'none';});}
document.querySelectorAll('.filters button').forEach(function(b){b.addEventListener('click',function(){own=b.dataset.owner;document.querySelectorAll('.filters button').forEach(function(x){x.classList.toggle('on',x===b);});apply();});});
var s=document.getElementById('q');if(s){s.addEventListener('input',function(){q=s.value.toLowerCase();apply();});}
document.querySelectorAll('.cmd button').forEach(function(b){b.addEventListener('click',function(){var t=b.parentNode.querySelector('code').textContent;function done(){b.textContent='已複製';setTimeout(function(){b.textContent='複製';},1500);}
if(navigator.clipboard){navigator.clipboard.writeText(t).then(done,function(){});}else{var a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();try{document.execCommand('copy');done();}catch(e){}document.body.removeChild(a);}});});})();
"""


def build_closeout(root, results: list, summary: dict, zpath=None, script=None) -> dict:
    """v0104 收尾頁:RESULTS 每一列(非綠灰)判負責方 → 結案狀態 → VIA_Reports\\vrn2\\VRN2_CloseoutUI_latest.html + .json(只讀別系統的檔 · 只寫這兩個)。"""
    v2 = Path(root) / "VIA_Reports" / "vrn2"
    ctx = closeout_context(root)
    items = []
    for r in results:
        got = owner_of(r, ctx)
        if got:
            items.append(dict(r, owner=got[0], why=got[1]))
    items = merge_same(items, ctx)                                            # v0109 同一件事只列一次
    real = [i for i in items if i["owner"] not in ("提醒", "彙總")]
    state, state_text, per_owner = closeout_state(real)
    counts = {k: sum(1 for r in results if r.get("lamp") == k) for k in ("GREEN", "YELLOW", "RED", "GRAY")}
    reps = sorted((v2 / "verify_independent").glob("VRN2_IndependentVerify_*.json"), key=_mtime) if (v2 / "verify_independent").is_dir() else []
    digests = sorted((v2 / "verify_independent").glob("*.digest.txt"), key=_mtime) if (v2 / "verify_independent").is_dir() else []
    links = [("Workbench(四本冊 · 去重矩陣 · 引擎狀態)", v2 / "VRN2_Workbench_latest.html"), ("VRN-2 U/I", v2 / "VRN2_UI_latest.html"),
             ("貼回包(上傳給 AI)", zpath), ("RoundAll 結果 json", v2 / "VRN2_RoundAll_latest.json"), ("啟動器收尾收據", receipt_path(v2)),
             ("獨立驗證摘要", digests[-1] if digests else None), ("獨立驗證報告", reps[-1] if reps else None), ("⑪ FAIL 證據", v2 / "VRN2_FailEvidence_latest.json"),
             ("Combined 冊 csv", v2 / "output" / "VRN2_Combined_latest.csv"), ("剔除冊(帶理由)", v2 / "output" / "VRN2_Rejected_latest.csv"),
             ("共識品質矩陣", v2 / "consensus" / "factset_yfinance_consensus_quality_matrix.csv"), ("⑥e 擷取錯誤", v2 / "market" / "vdf" / "last_error.txt"),
             ("本輪逐字稿", summary.get("transcript"))]
    link_rows = [{"label": label, "path": str(p or ""), "exists": bool(p) and (Path(str(p)).is_file() or (zpath is not None and p is zpath))} for label, p in links]   # 貼回包在收尾頁之後才打包(路徑先定好)
    fact_steps = ("① 套件", "⑥ 完成判定 · 輸出冊", "⑥ ⑪ 驗證器版本", "⑥ 步驟 ⑪", "⑥ 四點原文核對", "⑥ 市場資料", "⑥ 步驟 ⑥f", "⑥ Combined 冊", "⑥ 歷史對齊", "⑥ 長線 Parquet 庫", "⑥ 階段耗時", "④ 跑啟動器")
    facts = [(r["step"], r["detail"]) for r in results if any(str(r.get("step", "")).startswith(s) for s in fact_steps)][:14]
    if ctx.get("combined_gaps"):
        facts.append(("Combined 空格原因", json.dumps(ctx["combined_gaps"], ensure_ascii=False)))
    cmds = rerun_hint(Path(script or __file__).resolve())[1:]
    doc = {"tool": "%s %s" % (NAME, VERSION), "at": summary.get("at") or _dt.datetime.now().isoformat(timespec="seconds"), "state": state, "state_label": STATES[state][0], "state_text": state_text,
           "vrn2_closed": state != "OPEN", "per_owner": per_owner, "counts": counts, "elapsed_s": summary.get("elapsed_s"), "package": summary.get("package"), "launcher": LAUNCHER,
           "items": [{k: i.get(k) for k in ("owner", "lamp", "step", "detail", "hint", "why", "also")} for i in items], "links": link_rows, "facts": facts, "next": cmds, "context": {k: (sorted(v) if isinstance(v, set) else v) for k, v in ctx.items()},
           "rule": "BLOCKED / REVIEW / DATA_GAP 都不是成功;VRN-2 側結案 = 不是 OPEN。VCGC 的 closeout_lamp 才是 VCGC 驗收(四系統對等 · 只讀互看)。"}
    out_json, out_html = v2 / CLOSEOUT_JSON, v2 / CLOSEOUT_HTML
    v2.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    out_html.write_text(render_closeout(doc), encoding="utf-8")
    doc["html"], doc["json"] = str(out_html), str(out_json)
    return doc


def render_closeout(doc: dict) -> str:
    """收尾頁 HTML(單檔 · 不連外 · 淺 / 深色 · 手機寬度可讀)。"""
    c = doc["counts"]
    order = [o for o, _, _ in OWNERS]
    items = sorted(doc["items"], key=lambda i: (order.index(i["owner"]) if i["owner"] in order else 9, {"RED": 0, "YELLOW": 1}.get(i["lamp"], 2)))
    open_n = sum(1 for i in items if i["owner"] not in ("提醒", "彙總"))
    kpi = "".join('<div class="kpi"><div class="k">%s</div><div class="v %s">%s</div></div>' % (_h(k), cls, _h(v)) for k, v, cls in (
        ("綠", c.get("GREEN", 0), "green"), ("黃", c.get("YELLOW", 0), "yellow"), ("紅", c.get("RED", 0), "red"), ("灰", c.get("GRAY", 0), "gray"),
        ("待辦(不含提醒)", open_n, "red" if doc["state"] == "OPEN" else ("yellow" if open_n else "green")), ("耗時(秒)", "%.0f" % float(doc.get("elapsed_s") or 0), "")))
    owner_cards = "".join('<div class="owner c-%s"><span class="n">%d</span><b>%s</b><p>%s</p></div>' % (_h(o), doc["per_owner"].get(o, 0) if o not in ("提醒", "彙總") else sum(1 for i in items if i["owner"] == o), _h(label), _h(what))
                          for o, label, what in OWNERS if o != "彙總")
    buttons = '<button class="on" data-owner="全部">全部 %d</button>' % len(items) + "".join('<button data-owner="%s">%s %d</button>' % (_h(o), _h(label), sum(1 for i in items if i["owner"] == o)) for o, label, _ in OWNERS if any(i["owner"] == o for i in items))
    label_of = {o: label for o, label, _ in OWNERS}
    lamp_zh = {"RED": "紅", "YELLOW": "黃", "GREEN": "綠", "GRAY": "灰"}
    rows = "".join('<tr data-owner="%s"><td><span class="chip c-%s">%s</span></td><td class="lampcell"><span class="lamp l-%s"></span>%s</td><td>%s</td><td class="detail">%s</td><td class="next">%s</td></tr>' % (
        _h(i["owner"]), _h(i["owner"]), _h(label_of.get(i["owner"], i["owner"])), _h(i["lamp"]), _h(lamp_zh.get(i["lamp"], i["lamp"])), _h(i["step"]), _h(i["detail"][:700]), _h(" · ".join(x for x in (i.get("why"), i.get("hint")) if x)[:500]))
        for i in items) or '<tr><td colspan="5">沒有待辦</td></tr>'
    facts = "".join("<dt>%s</dt><dd>%s</dd>" % (_h(k), _h(str(v)[:600])) for k, v in doc["facts"])
    links = "".join(('<a href="%s"><b>%s</b><small>%s</small></a>' % (_h(_uri(l["path"])), _h(l["label"]), _h(l["path"]))) if l["exists"] else
                    '<span class="miss"><b>%s</b><small>%s</small></span>' % (_h(l["label"]), _h(l["path"] or "(這輪沒有)")) for l in doc["links"])
    wb = next((l for l in doc["links"] if l["label"].startswith("Workbench") and l["exists"]), None)
    cmds = "".join('<div class="cmd"><code>%s</code><button type="button">複製</button></div>' % _h(x) for x in doc["next"])
    return ("<!doctype html><html lang=\"zh-Hant\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<title>VRN-2 收尾</title><style>%s</style></head><body>" % CLOSEOUT_CSS
            + '<header><div class="brand"><span class="logo">VRN-2</span><div><h1>收尾 · Close-out</h1><div class="sub">%s · %s · 套件 %s · 啟動器 %s</div></div></div>' % (_h(doc["at"]), _h(doc["tool"]), _h(Path(str(doc.get("package") or "")).name or "—"), _h(doc["launcher"]))
            + '<div class="state s-%s"><b>%s · %s</b><span>%s</span></div></header><main>' % (_h(doc["state"]), _h(doc["state"]), _h(doc["state_label"]), _h(doc["state_text"]))
            + '<section class="kpis">%s</section>' % kpi
            + '<section class="panel"><h2>結案判定</h2><p class="big">%s</p><div class="owners">%s</div><p class="note">%s</p>%s</section>' % (
                _h(("VRN-2 側可結案(不是 OPEN)· " if doc["vrn2_closed"] else "VRN-2 側未結案 · ") + doc["state_text"]), owner_cards, _h(doc["rule"]),
                ('<a class="primary" href="%s">開 Workbench</a>' % _h(_uri(wb["path"]))) if wb else "")
            + '<section class="panel"><h2>待辦(依負責方)</h2><div class="filters">%s<input id="q" type="search" placeholder="搜尋步驟 / 檔名 / 代號"></div>' % buttons
            + '<div class="tablewrap"><table id="items"><thead><tr><th>負責</th><th>燈</th><th>步驟</th><th>內容</th><th>為什麼是它 · 下一步</th></tr></thead><tbody>%s</tbody></table></div></section>' % rows
            + '<section class="panel"><h2>這輪的數據</h2><dl class="facts">%s</dl></section>' % (facts or "<dt>—</dt><dd>沒有(只跑了部分步驟)</dd>")
            + '<section class="panel"><h2>檔案</h2><div class="links">%s</div></section>' % links
            + '<section class="panel"><h2>下次怎麼跑</h2>%s<p class="note">第 1 行整輪 · 第 2 行不重跑只修 + 除錯 + 打包 · 第 3 行只診斷 + 自測 · 跑完把貼回包 zip 上傳給 AI</p></section>' % cmds
            + "</main><footer>VRN-2 自己的收尾頁 · 只讀其他系統的檔 · %s</footer><script>%s</script></body></html>" % (_h(doc["tool"]), CLOSEOUT_JS))


def step_closeout(root, summary: dict, zpath=None, script=None):
    try:
        doc = build_closeout(root, list(RESULTS), summary, zpath, script)
    except Exception as error:  # noqa: BLE001
        say("YELLOW", "⑧ 收尾頁", "沒寫成(%s: %s)" % (type(error).__name__, str(error)[:200]), "其他結果不受影響 · 看 VRN2_RoundAll_latest.json")
        return None
    po = doc["per_owner"]
    say("GREEN" if doc["state"] in ("PASS", "DATA_GAP") else ("RED" if doc["state"] == "OPEN" and any(i["lamp"] == "RED" and i["owner"] == "VRN-2" for i in doc["items"]) else "YELLOW"),
        "⑧ 收尾頁(HTML U/I)", "%s · %s · %s · VRN-2 %d · VCGC %d · 人工 %d · 資料源 %d → %s" % (doc["state"], doc["state_label"], doc["state_text"], po.get("VRN-2", 0), po.get("VCGC", 0), po.get("人工", 0), po.get("資料源", 0), doc["html"]),
        "BLOCKED / REVIEW / DATA_GAP 都不是成功 · 待辦依負責方分好 · VCGC 的 closeout_lamp 才是 VCGC 驗收")
    return doc


# ===== 10. ⑦ 貼回包 =====
def pasteback_path() -> Path:
    """v0104 貼回包路徑先定好(收尾頁要連到它):Downloads 建不了 → TEMP。"""
    dest = downloads()
    try:
        dest.mkdir(parents=True, exist_ok=True)
    except OSError:
        dest = Path(tempfile.gettempdir())
    return dest / ("VRN2_PasteBack_%s.zip" % stamp())


def step_pasteback(root, transcript: Path, zpath=None) -> Path | None:
    zpath = Path(zpath) if zpath else pasteback_path()
    lines = transcript.read_text(encoding="utf-8", errors="replace").splitlines() if transcript.is_file() else []
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("transcript.txt", "\n".join(lines) + "\n")
        z.writestr("digest_last300.txt", "\n".join(lines[-300:]) + "\n")
        if root:
            v2 = Path(root) / "VIA_Reports" / "vrn2"
            skipped = []
            rp = receipt_path(v2)
            extra = () if rp.name == RECEIPT else (rp.name, rp.stem + ".before_roundall.json")   # v0108 沿用的前版收據也包
            for rel in PASTE_FILES + extra:
                p = v2 / rel
                if p.is_file() and p.stat().st_size <= 20 * 1024 * 1024:
                    try:
                        z.write(str(p), "vrn2/" + rel)
                    except OSError as error:                               # v0105 被鎖的檔略過(其他照包)
                        skipped.append("%s(%s)" % (rel, type(error).__name__))
            if skipped:
                z.writestr("skipped_files.txt", "\n".join(skipped) + "\n")
            dig = sorted((v2 / "verify_independent").glob("*.digest.txt"), key=_mtime) if (v2 / "verify_independent").is_dir() else []
            if dig:
                z.write(str(dig[-1]), "vrn2/verify_independent/" + dig[-1].name)
            req = Path(root) / "functional modules" / "VRN2" / "contract" / "VRN2_NUMBER_REQUEST_latest.json"
            if req.is_file():
                z.write(str(req), "vrn2/contract/" + req.name)
    say("GREEN", "⑦ 貼回包", "%s(%.1f MB)" % (zpath, zpath.stat().st_size / 1e6), "把這個 zip 上傳給 AI(比貼主控台文字完整)")
    return zpath


# ===== 11. 主流程 =====
STEPS = ("package", "preflight", "selftest", "run", "fix", "verify", "report", "closeout", "pasteback")


def parse_args(argv):
    import argparse
    ap = argparse.ArgumentParser(prog=NAME + "_" + VERSION, description="VRN-2 一支 Python 跑完一輪(取套件 → 診斷 → 自測 → 跑 → 自動修 → 除錯 → 貼回包)")
    ap.add_argument("--root", default=None, help="VIA 根(…\\movies-dataset\\VeritasIntelligenceAnalytics)")
    ap.add_argument("--source", default=None, help="報告來源夾(不給 = 上一輪 / U/I 選的)")
    ap.add_argument("--package", default=None, help="套件夾(預設 Downloads\\%s)" % PACKAGE)
    ap.add_argument("--python", default=None, help="跑 VRN-2 的 python(預設 VRN2_PY / 上一輪記的 / 本行程)")
    ap.add_argument("--branch", default=BRANCH)
    ap.add_argument("--offline", action="store_true", help="不連 GitHub,只用本機套件")
    ap.add_argument("--ship", action="store_true", help="允許 ⑨ 上船 GitHub(預設只測不推)")
    ap.add_argument("--integrate", choices=("ask", "yes", "no", "skip"), default="ask", help="舊資料庫待決定時:問 / 整合 / 不要 / 先不決定")
    ap.add_argument("--no-open", action="store_true", help="不開瀏覽器")
    ap.add_argument("--verify", action="store_true", help="v0108 也跑 ⑪b 只重跑獨立驗證(預設不跑:整輪時啟動器 ⑪ 已經驗過)")
    ap.add_argument("--launcher-args", default="", help="多帶給啟動器的參數(空白分隔)")
    ap.add_argument("--run-timeout", type=int, default=4 * 3600)
    ap.add_argument("--only", default="", help="只跑這些步驟(逗號分隔:%s)" % ",".join(STEPS))
    for s in ("package", "preflight", "selftest", "run", "fix", "closeout", "pasteback"):
        ap.add_argument("--skip-" + s, action="store_true")
    ap.add_argument("--selftest", action="store_true", help="本檔自測(不碰真環境)")
    fixed, i = [], 0
    while i < len(argv):                                                 # --launcher-args "--no-install":值以 - 開頭時 argparse 會當成選項 → 併成 --launcher-args=…
        if argv[i] == "--launcher-args" and i + 1 < len(argv):
            fixed.append("--launcher-args=" + argv[i + 1])
            i += 2
            continue
        fixed.append(argv[i])
        i += 1
    return ap.parse_args(fixed)


def main(argv=None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.selftest:
        return selftest()
    only = {s.strip() for s in args.only.split(",") if s.strip()}
    want = {s: ((not only or s in only) and not getattr(args, "skip_" + s, False)) for s in STEPS}
    want["verify"] = ("verify" in only) or bool(args.verify)                 # v0108 ⑪b 只在要求時跑
    transcript = Path(tempfile.gettempdir()) / ("VRN2_RoundAll_%s.log" % stamp())
    sys.stdout = Tee(transcript)
    t0 = time.time()
    print("══════ %s %s · %s · Python %s · %s ══════" % (NAME, VERSION, _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sys.version.split()[0], " → ".join(s for s in STEPS if want[s])), flush=True)
    root, tried = find_root(args.root)
    if root:
        say("GREEN", "⓪ VIA 根", str(root))
    else:
        say("RED", "⓪ VIA 根", "找不到(查過:%s)" % " | ".join(tried)[:600], "加 --root <…\\movies-dataset\\VeritasIntelligenceAnalytics>")
    pkg = None
    if want["package"]:
        pkg = guarded("① 套件", step_package, root, args)
    else:
        pkg = find_package(args)                                                # v0107 找讀得到的套件夾 · 不跑啟動器 / 自測就不需要
        if pkg:
            say("GRAY", "① 套件", "略過取套件 · 用 %s" % pkg)
        elif want["run"] or want["selftest"]:
            say("YELLOW", "① 套件", "略過取套件 · 找不到讀得到啟動器的套件夾(--package / VRN2_PACKAGE / Downloads\\%s / %s_<時間>)" % (PACKAGE, PACKAGE), "拿掉 --skip-package / --only 讓它取套件")
        else:
            say("GRAY", "① 套件", "略過取套件 · 這輪不跑啟動器也不自測(只做 %s)· 不需要套件" % ",".join(s_ for s_ in STEPS if want[s_]))
    vpy, vpy_how = guarded("② VRN-2 Python", vrn2_python, root, args.python, default=(sys.executable, "本行程(找 Python 時出例外)"))
    state = {}
    if want["preflight"]:
        state = guarded("② 診斷", step_preflight, root, pkg, vpy, vpy_how, args, default={}) or {}
    if want["selftest"] and pkg:
        guarded("③ 自測", step_selftest, pkg, vpy)
    if want["run"] and pkg and root:
        guarded("④ 跑啟動器", step_run, pkg, root, vpy, state, args)
    elif want["run"]:
        say("RED", "④ 跑啟動器", "沒有套件或 VIA 根 · 不跑", "看 ① 套件那一行(讀不到 / 雜湊不對 / GitHub 取不到)")
    if want["fix"] and root:
        guarded("⑤ 自動修", step_fix, root, vpy, dict(state, pkg=pkg), args)      # v0110 ⑥f 重跑要套件 runtime
    if want["verify"] and root:
        guarded("⑪b 重跑獨立驗證", step_verify, root, pkg, vpy)
    report = {}
    if want["report"] and root:
        report = guarded("⑥ 除錯報告", diagnose, root, vpy, default={}) or {}
    overall = worst([r["lamp"] for r in RESULTS])
    summary = {"tool": "%s %s" % (NAME, VERSION), "at": _dt.datetime.now().isoformat(timespec="seconds"), "elapsed_s": round(time.time() - t0, 1), "root": str(root or ""), "package": str(pkg or ""),
               "python": vpy, "overall": overall, "results": RESULTS, "report": report, "transcript": str(transcript)}
    if root:
        try:
            out = Path(root) / "VIA_Reports" / "vrn2" / "VRN2_RoundAll_latest.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass
    zplan = pasteback_path() if want["pasteback"] else None
    page = step_closeout(root, summary, zplan) if (want["closeout"] and root) else None     # v0104 ⑧ 收尾頁(貼回包也帶它)
    zpath = guarded("⑦ 貼回包", step_pasteback, root, transcript, zplan) if want["pasteback"] else None
    counts = {k: sum(1 for r in RESULTS if r["lamp"] == k) for k in ("GREEN", "YELLOW", "RED", "GRAY")}
    reds = [r for r in RESULTS if r["lamp"] == "RED"]
    print("─" * 88)
    print("總表 · 綠 %(GREEN)d · 黃 %(YELLOW)d · 紅 %(RED)d · 灰 %(GRAY)d" % counts + " · %.0f 秒" % (time.time() - t0))
    for r in reds[:12]:
        print("  [RED] %s · %s" % (r["step"], r["detail"][:180]))
    if page:
        print("收尾頁 · %s · %s · %s → %s" % (page["state"], page["state_label"], page["state_text"], page["html"]))
    if root and not args.no_open and os.environ.get("VRN2_NO_UI") != "1" and os.name == "nt":    # v0104 開收尾頁(它連 Workbench);沒有收尾頁 → 照 v0103 開 Workbench
        target = Path(page["html"]) if page else Path(root) / "VIA_Reports" / "vrn2" / "VRN2_Workbench_latest.html"
        if target.is_file() and (page or (want["fix"] and any(r["step"].startswith("⑤ 修") for r in RESULTS))):
            try:
                os.startfile(str(target))  # type: ignore[attr-defined]
            except OSError:
                pass
    for line in rerun_hint(Path(__file__).resolve()):
        print(line)
    print("NEXT: [%s] %s · 紅 %d · 黃 %d · %s%s" % (overall, NAME, counts["RED"], counts["YELLOW"], ("貼回包 " + str(zpath)) if zpath else "(沒打包)", (" · 收尾 %s" % page["state"]) if page else ""), flush=True)
    return {"GREEN": 0, "GRAY": 0, "YELLOW": 2}.get(overall, 1)


def rerun_hint(script: Path) -> list:
    """下次怎麼跑:完整路徑加引號(cmd 與 PowerShell 都能直接貼;%USERPROFILE% 只有 cmd 認得)。"""
    exe = "python"
    return ["下次(cmd / PowerShell 都能貼 · 一行一個指令 · 整行複製;第 1 行整輪 · 第 2 行不重跑只修 + 除錯 + 打包 · 第 3 行只診斷 + 自測):",
            '%s "%s"' % (exe, script),
            '%s "%s" --skip-run --integrate yes' % (exe, script),
            '%s "%s" --only preflight,selftest' % (exe, script)]


# ===== 12. 自測 =====
def selftest() -> int:
    bad = []

    ran = []

    def chk(label, cond):
        ran.append(label)
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)

    class A:
        integrate = "no"
    saved_env = {k: os.environ.get(k) for k in ("USERPROFILE", "HOME", "VRN2_DOWNLOADS", "VRN2_ROOT", "VIA_ROOT", "VIA_FETCH_PY", "VRN2_PACKAGE")}
    with tempfile.TemporaryDirectory(prefix="vrn2-roundall-") as td:
        td = Path(td)
        for k in ("VRN2_ROOT", "VIA_ROOT", "VIA_FETCH_PY", "VRN2_PACKAGE"):
            os.environ.pop(k, None)
        os.environ["USERPROFILE"] = os.environ["HOME"] = str(td / "home")
        os.environ["VRN2_DOWNLOADS"] = str(td / "home" / "Downloads")
        root = td / "home" / "OneDrive" / "Documents" / "movies-dataset" / "VeritasIntelligenceAnalytics"
        (root / "functional modules" / "VRN2").mkdir(parents=True)
        (root / "supportive modules").mkdir(parents=True)
        got, tried = find_root(None)
        chk("① 找 VIA 根:沒有參數 / 環境變數 → 預設位置 OneDrive\\Documents\\movies-dataset 找到 · 查過的地方都記", got == root and any("預設位置" in t for t in tried))
        other = td / "elsewhere" / "VIA"
        (other / "functional modules").mkdir(parents=True)
        (other / "supportive modules").mkdir(parents=True)
        ctx = Path(os.environ["VRN2_DOWNLOADS"]) / "VRN2_Closeout_v0146"
        ctx.mkdir(parents=True)
        (ctx / "VRN2_Runtime_Context.json").write_text(json.dumps({"root": str(other)}), encoding="utf-8")
        chk("② 找 VIA 根:啟動器記的 Runtime_Context 優先於預設位置 · --root 最優先", find_root(None)[0] == other and find_root(str(root))[0] == root)
        # ③ 套件安裝 / 竄改 / 錯雜湊
        src = td / "build" / PACKAGE
        src.mkdir(parents=True)
        files = {LAUNCHER: b"print('launcher')\n", RUNTIME_ZIP: b"zipbytes", "README.txt": b"readme"}
        for n, b in files.items():
            (src / n).write_bytes(b)
        man = {"files": [{"path": n, "sha256": hashlib.sha256(b).hexdigest()} for n, b in files.items()]}
        (src / "PACKAGE_SHA256.json").write_text(json.dumps(man), encoding="utf-8")
        zp = td / "build" / (PACKAGE + ".zip")
        with zipfile.ZipFile(zp, "w") as z:
            for p in sorted(src.iterdir()):
                z.write(str(p), PACKAGE + "/" + p.name)
        want = sha256_file(zp)
        pkg = Path(os.environ["VRN2_DOWNLOADS"]) / PACKAGE
        r1 = install_package(zp, want, pkg)
        r2 = install_package(zp, want, pkg)
        (pkg / LAUNCHER).write_bytes(b"tampered")
        r3 = install_package(zp, want, pkg)
        backups = list(pkg.parent.glob(PACKAGE + ".bak_*"))
        r4 = install_package(zp, "0" * 64, pkg)
        chk("③ 套件:裝好(逐檔相符 · zip 也放進套件夾)→ 再裝 = 本機已是 → 竄改 → 整夾改名備份再裝(不刪)→ 雜湊不對拒用",
            r1["lamp"] == "GREEN" and (pkg / (PACKAGE + ".zip")).is_file() and "本機已是" in r2["detail"] and r3["lamp"] == "GREEN" and (pkg / LAUNCHER).read_bytes() == files[LAUNCHER] and len(backups) == 1 and (backups[0] / LAUNCHER).read_bytes() == b"tampered" and r4["lamp"] == "RED")
        # ④ git 取發行夾
        if shutil.which("git"):
            remote, work = td / "remote.git", td / "clone"
            subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
            rel = td / "relsrc"
            (rel / RELEASE_REL).mkdir(parents=True)
            shutil.copy2(str(zp), str(rel / RELEASE_REL / zp.name))
            (rel / RELEASE_REL / RELEASE_JSON).write_text("{}", encoding="utf-8")
            g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
            subprocess.run(["git", "-C", str(rel), "init", "-q", "-b", "x"], check=True)
            subprocess.run(["git", "-C", str(rel), "add", "-A"], check=True)
            subprocess.run(g + ["-C", str(rel), "commit", "-qm", "rel"], check=True)
            subprocess.run(["git", "-C", str(rel), "push", "-q", str(remote), "x:refs/heads/" + BRANCH], check=True, capture_output=True)
            subprocess.run(["git", "clone", "-q", str(remote), str(work)], check=True, capture_output=True)
            z2, j2, how = git_fetch_release(work, BRANCH, td)
            chk("④ git:從分支 archive 發行夾 → zip 雜湊與建置的一樣 · 來源記分支", z2 is not None and sha256_file(z2) == want and how == "GitHub " + BRANCH and j2.is_file())
        else:
            print("[SKIP] ④ 沒有 git")
        # ⑤ 修正計畫(純判斷)
        v2 = root / "VIA_Reports" / "vrn2"
        (v2 / "output").mkdir(parents=True)
        (v2 / "market").mkdir()
        (v2 / "output" / "VRN2_BasicInfo_latest.json").write_text("[]", encoding="utf-8")
        (v2 / "VRN2_HistoryAlign_latest.json").write_text("{}", encoding="utf-8")
        time.sleep(0.05)
        (v2 / "market" / "VRN2_Market_latest.json").write_text('{"per_file": {}}', encoding="utf-8")
        (v2 / "VRN2_Output_Config.json").write_text(json.dumps({"output_dir": str(td / "out")}), encoding="utf-8")
        (v2 / "VRN2_Integrate_latest.json").write_text(json.dumps({"state": "PENDING_USER", "candidates": [{"readable": True}]}), encoding="utf-8")
        (v2 / "VRN2_Launcher.lock").write_text(json.dumps({"pid": 2 ** 22 + 12345}), encoding="utf-8")
        receipt = {"market": {"lamp": "YELLOW", "detail": "VRN2_MarketFetch_v0112.py · Python 本行程 · 擷取 YELLOW:缺套件"}, "consensus": {"run": {"lamp": "YELLOW", "why": "擷取環境缺 yfinance(x)"}}, "history_align": {"lamp": "GRAY"}}
        plan = [k for k, _ in plan_fixes(root, receipt, "/x/py", A(), "/x/MarketFetch.py")]
        chk("⑤ 修正計畫:⑥e 用錯 Python → market · 缺 yfinance → consensus · 市場比歷史新 → history · Combined 不在 → combined · 有修 → store · 待決定 → integrate · 過期鎖 → lock · 最後 workbench",
            plan == ["market", "consensus", "history", "combined", "store", "integrate", "lock", "workbench"])
        plan2 = [k for k, _ in plan_fixes(root, {"market": {"lamp": "GREEN"}, "consensus": {"run": {"lamp": "GREEN"}}, "history_align": {"lamp": "GREEN"}}, None, type("B", (), {"integrate": "skip"})(), "")]
        chk("⑤b 修正計畫:沒有擷取 Python · 整合模式 skip → 只剩 history / combined / store / lock / workbench(不亂修)", plan2 == ["history", "combined", "store", "lock", "workbench"])
        # ⑥ 除錯報告
        RESULTS.clear()
        sys_stdout = sys.stdout
        (v2 / RECEIPT).write_text(json.dumps({"version": "ActivateVRN-2 v0147", "rc": 1, "elapsed_s": 10, "passes": [{}], "steps": [{"step": "③ 環境檢查與補裝", "lamp": "RED", "detail": "缺 7"}, {"step": "⑥e 市場擷取", "lamp": "GRAY", "detail": "沒有 MarketFetch"}, {"step": "⑦ 啟動", "lamp": "GREEN"}],
                                              "output_gaps": [{"book": "FinancialData", "file": "a.pdf"}]}, ensure_ascii=False), encoding="utf-8")
        (v2 / "VRN2_VerbatimVerify_latest.json").write_text(json.dumps({"verdict": "FAIL", "counts": {"PASS": 3, "FAIL": 1}, "rows": [{"file": "3014TT.pdf", "point": 3, "state": "FAIL", "match": "not found"}, {"file": "b.pdf", "point": 1, "state": "PASS"}]}), encoding="utf-8")
        comb = [{c: "x" for c in COMBINED_HEAD + ["%d_DILUTED_EPS_FACTSET" % y for y in (2026, 2027, 2028)] + ["%d_PER_FACTSET" % y for y in (2026, 2027, 2028)] + COMBINED_TAIL}]
        comb[0]["TARGET_PRICE(ADJ)"] = ""
        (v2 / "output" / "VRN2_Combined_latest.json").write_text(json.dumps(comb), encoding="utf-8")
        (v2 / "consensus").mkdir()
        (v2 / "consensus" / "VRN2_Consensus_latest.json").write_text(json.dumps({"year_n": 2026}), encoding="utf-8")
        (v2 / "VRN2_Workbench_latest.html").write_text('<div id="first"></div><div id="outfolder"></div>Report Date / 報告日期 function fitStats', encoding="utf-8")
        import io
        sys.stdout = io.StringIO()
        try:
            rep = diagnose(root)
        finally:
            sys.stdout = sys_stdout
        areas = {x["area"]: x for x in rep["findings"]}
        chk("⑥ 除錯:收尾 rc 1 紅 · 非綠步驟帶下一步(③ / ⑥e)· 四點核對列出 3014TT 第 3 點 · 缺項 · Combined 欄序正確但調整後目標價空 1 · Workbench 缺「百萬台幣換算」標記",
            areas["收尾收據"]["lamp"] == "RED" and "VCGC" in areas["步驟 ③ 環境檢查與補裝"]["next"] and "MarketFetch" in areas["步驟 ⑥e 市場擷取"]["next"] and "3014TT.pdf 第 3 點 FAIL" in areas["四點原文核對"]["finding"]
            and areas["輸出缺項"]["lamp"] == "YELLOW" and "欄序正確" in areas["Combined 冊"]["finding"] and '"TARGET_PRICE(ADJ)": 1' in areas["Combined 冊"]["finding"] and "百萬台幣換算" in areas["Workbench U/I"]["finding"])
        # ⑦ 修正後的收據備份 + 標註
        rpath = v2 / RECEIPT
        rec = jread(rpath, {})
        _patch_receipt(rpath, rec, {"⑥e": ("YELLOW", "擷取 YELLOW")})
        _patch_receipt(rpath, jread(rpath, {}), {"⑥e": ("GREEN", "擷取 GREEN")})
        backup = jread(rpath.with_name(rpath.stem + ".before_roundall.json"), {})
        now = jread(rpath, {})
        chk("⑦ 收據:先備份一次(原燈 GRAY 留在備份)· 被修的步驟換燈 + 註明 RoundAll 修正後 · roundall 欄", backup["steps"][1]["lamp"] == "GRAY" and now["steps"][1]["lamp"] == "GREEN" and now["steps"][1]["detail"].startswith("RoundAll 修正後") and now["roundall"]["fixed"]["⑥e"]["lamp"] == "GREEN")
        # ⑧ 貼回包
        tr = td / "t.log"
        tr.write_text("\n".join("line %d" % i for i in range(400)), encoding="utf-8")
        sys.stdout = io.StringIO()
        try:
            zpath = step_pasteback(root, tr)
        finally:
            sys.stdout = sys_stdout
        with zipfile.ZipFile(zpath) as z:
            names = set(z.namelist())
            last = z.read("digest_last300.txt").decode("utf-8").splitlines()
        chk("⑧ 貼回包:Downloads 下 · 逐字稿 + 最後 300 行 + 收尾收據 + 備份 + Combined / Workbench", zpath.parent == Path(os.environ["VRN2_DOWNLOADS"]) and "transcript.txt" in names and len(last) == 300 and last[0] == "line 100"
            and "vrn2/" + RECEIPT in names and "vrn2/VRN2_Closeout_v0154.before_roundall.json" in names and "vrn2/VRN2_Workbench_latest.html" in names)
        # ⑨ 子行程串流 + 逾時 + 心跳
        rc, lines = run_stream([sys.executable, "-c", "import time;print('a');print('b')"], quiet=True)
        rc2, lines2 = run_stream([sys.executable, "-c", "import time;time.sleep(30)"], timeout=6, quiet=True, heartbeat=1)
        chk("⑨ 子行程:逐行收 · 逾時會停並記紅", rc == 0 and lines == ["a", "b"] and rc2 != 0 and "逾時" in lines2[-1])
        chk("⑩ 燈號合併 / PID / 結束碼:紅 > 黃 > 綠灰 · 不存在的 PID 不算活", worst(["GREEN", "GRAY"]) in ("GREEN", "GRAY") and worst(["GREEN", "YELLOW"]) == "YELLOW" and worst(["YELLOW", "RED"]) == "RED" and pid_alive(os.getpid()) and not pid_alive(2 ** 22 + 12345))
        chk("⑪ 參數:--only / --skip / --integrate 解析 · --launcher-args 的值以 - 開頭也收得到", parse_args(["--only", "fix,report", "--integrate", "yes", "--skip-selftest"]).integrate == "yes" and parse_args(["--skip-run"]).skip_run
            and parse_args(["--launcher-args", "--no-install --x", "--no-open"]).launcher_args == "--no-install --x" and parse_args(["--launcher-args", "--no-install"]).no_open is False)
        # ⑫ 擷取 Python 不用退役 / 備份環境
        envs = Path(os.environ["USERPROFILE"]) / "envs"
        for name in ("via_core.retired-20260914_111946", "via_tw_fetch.bak_1", "old_backup", "work"):
            exe = envs / name / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            exe.parent.mkdir(parents=True, exist_ok=True)
            exe.write_text("", encoding="utf-8")
        cands = fetch_python_candidates()
        chk("⑫ 擷取 Python 候選:via_core.retired-… / via_tw_fetch.bak_1 / old_backup 略過並記下 · work 照收 · 本行程最後",
            any("work" in c for c in cands) and not any(("retired" in c or ".bak_" in c or "old_backup" in c) for c in cands) and set(SKIPPED_ENVS) == {"via_core.retired-20260914_111946", "via_tw_fetch.bak_1", "old_backup"} and cands[-1] == sys.executable)
        # ⑬ ⑭ 除錯報告的證據
        (v2 / "output" / "VRN2_Summary_latest.json").write_text(json.dumps([{"FILENAME": "3014TT.pdf", "POINT_3": "營收年增 25% 優於預期"}], ensure_ascii=False), encoding="utf-8")
        (v2 / "market" / "vdf").mkdir(parents=True, exist_ok=True)
        (v2 / "market" / "vdf" / "last_error.txt").write_text("Traceback\nConnectionError: www.twse.com.tw timed out\n", encoding="utf-8")
        (v2 / "consensus" / "VRN2_Consensus_latest.json").write_text(json.dumps({"year_n": 2026, "yf_404": ["6933.TW"], "yf_ticker_map": {"codes": 3, "tpex": ["5274"]}}), encoding="utf-8")
        rr = jread(v2 / RECEIPT, {})
        for st in rr.get("steps") or []:
            if str(st.get("step", "")).startswith("⑥e"):
                st["lamp"] = "YELLOW"                                    # ⑦ 把它標成綠了;⑭ 要「⑥e 不綠」
        (v2 / RECEIPT).write_text(json.dumps(rr, ensure_ascii=False), encoding="utf-8")
        sys.stdout = io.StringIO()
        try:
            rep2 = diagnose(root)
        finally:
            sys.stdout = sys_stdout
        a2 = {x["area"]: x for x in rep2["findings"]}
        chk("⑬ 除錯:四點 FAIL 帶摘錄原文(3014TT 第 3 點「營收年增 25% 優於預期」)", "營收年增 25% 優於預期" in a2.get("四點 FAIL 摘錄", {}).get("finding", ""))
        chk("⑭ 除錯:⑥e 不綠 → last_error.txt 最後幾行(timed out)· ⑥f Yahoo 404 代號與上櫃 .TWO 數", "timed out" in a2.get("⑥e 擷取錯誤(last_error.txt)", {}).get("finding", "") and "6933.TW" in a2.get("⑥f Yahoo 代號", {}).get("finding", "") and "上櫃 .TWO 1" in a2.get("⑥f Yahoo 代號", {}).get("finding", ""))
        hint = rerun_hint(Path("C:/Users/x/Downloads/VRN2_RoundAll_v0111.py"))
        chk("⑮ 下次怎麼跑:完整路徑加引號(兩種殼都能貼 · 不用 %USERPROFILE% · 指令行沒有 :: / # 註解尾巴 · 行首就是 python)· 整輪 / --skip-run / --only preflight,selftest",
            len(hint) == 4 and all(h.startswith('python "') for h in hint[1:]) and not any("%USERPROFILE%" in h or "::" in h or "#" in h for h in hint[1:]) and hint[2].endswith("--skip-run --integrate yes") and hint[1].endswith('.py"'))
        # ⑯ ~ ⑲ v0102
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            try:
                compile(Path(__file__).read_text(encoding="utf-8"), str(Path(__file__)), "exec")
                clean = True
            except SyntaxError:
                clean = False
        chk("⑯ 本檔編譯不出 SyntaxWarning(docstring 的 Windows 路徑反斜線成對 · v0101 在桌機印 invalid escape sequence)", clean)
        (v2 / "consensus" / "factset_yfinance_consensus_quality_matrix.csv").write_text("\ufeffcode,check_id,actual,expected,status,severity,note\n6933,FACTSET_TARGET,0,>0,FAIL,FAIL,no coverage\n2330,HTTP_PAGE_200,200,200,PASS,FAIL,ok\n", encoding="utf-8")
        vi = v2 / "verify_independent"
        vi.mkdir(exist_ok=True)
        (vi / "VRN2_IndependentVerify_20261029_000000.json").write_text(json.dumps({"version": "VRN2_IndependentVerifier_v0114", "basic": [{"FILENAME": "MS-3661 20251203.pdf", "checks": {"CURRENT_PRICE_REPORT": "FAIL · 前 4 頁沒有這個數", "TARGET_PRICE": "PASS · 第 1 頁"}}]}), encoding="utf-8")
        (v2 / "output" / "VRN2_BasicInfo_latest.json").write_text(json.dumps([{"FILENAME": "MS-3661 20251203.pdf", "CURRENT_PRICE_REPORT": "3190.00", "TARGET_PRICE": "4388.00", "UPSIDE_PCT": "38"}]), encoding="utf-8")
        pdf_ok = False
        try:
            try:
                import pymupdf as fitz  # noqa: WPS433
            except ImportError:
                import fitz  # noqa: WPS433
            (v2 / "scope_in").mkdir(exist_ok=True)
            doc = fitz.open()
            page = doc.new_page()
            for i, line in enumerate(("Morgan Stanley Taiwan", "Price target NT$4,388.00", "Shr price, close (Dec 3, 2025) NT$3,190.00", "Up/downside to price target (%) 38")):
                page.insert_text((72, 72 + 16 * i), line, fontsize=11)
            doc.save(str(v2 / "scope_in" / "MS-3661 20251203.pdf"))
            import pypdfium2  # noqa: F401,WPS433
            pdf_ok = True
        except Exception:  # noqa: BLE001
            pass
        sys.stdout = io.StringIO()
        try:
            rep3 = diagnose(root, sys.executable)
        finally:
            sys.stdout = sys_stdout
        a3 = {x["area"]: x for x in rep3["findings"]}
        chk("⑰ 除錯:⑥f 共識閘 FAIL 列(只列 status FAIL:6933 FACTSET_TARGET)· ⑪ 驗證器版本 v0114 = 綠(v0108 起 v0114 以前算舊)", "6933 FACTSET_TARGET" in a3.get("⑥f 共識閘 FAIL 列", {}).get("finding", "") and "2330" not in a3.get("⑥f 共識閘 FAIL 列", {}).get("finding", "")
            and a3.get("⑪ 驗證器版本", {}).get("lamp") == "GREEN")
        ev = a3.get("⑪ 基本資料 FAIL 證據", {}).get("finding", "")
        if pdf_ok:
            chk("⑱ 除錯:⑪ 基本資料 FAIL 證據 = 冊值 + 原 PDF 那一行(「Shr price, close (Dec 3, 2025) NT$3,190.00」)· 寫 VRN2_FailEvidence_latest.json", "MS-3661" in ev and "3,190.00" in ev and (v2 / "VRN2_FailEvidence_latest.json").is_file())
        else:
            chk("⑱ 除錯:⑪ 基本資料 FAIL 證據(本 Python 沒有 PyMuPDF / pypdfium2 → 只驗冊值與「找不到 / 讀不到」說明)", "MS-3661" in ev and "3190.00" in ev)
        cmds = vcgc_fetch_commands()
        chk("⑲ 交 VCGC 的擷取環境指令:cmd / PowerShell 各一組 · 帶 VDF 界線且加引號(cmd 的 < 不會變導向)", len(cmds) == 4 and '"pandas>=2.2,<3"' in cmds[1] and "$env:USERPROFILE" in cmds[3] and '"pandas>=2.2,<3"' in VCGC_FETCH_ENV[1])
        # ⑳ ~ ㉒ v0103
        rr = {"market": {"lamp": "YELLOW", "detail": "VRN2_MarketFetch_v0112.py · Python 本行程 · 擷取 RED:…", "runner": "VRN2_MarketFetchRun_v0100.py", "fetch_python": {"python": "/x/py"}}, "consensus": {"run": {"lamp": "GREEN"}}, "history_align": {"lamp": "GRAY"}}
        chk("⑳ 修正計畫:⑥e 已經經 MarketFetchRun(合 VDF 界線)跑過 → 不重抓(v0102 因為「Python 本行程」又抓了一輪)", "market" not in [k for k, _ in plan_fixes(root, rr, "/x/py", A(), "/x/MarketFetch.py")])
        ev_ok = False
        try:
            try:
                import pymupdf as fitz  # noqa: WPS433
            except ImportError:
                import fitz  # noqa: WPS433
            import pypdfium2  # noqa: F401,WPS433
            doc = fitz.open()
            page = doc.new_page()
            for i, line in enumerate(("Morgan Stanley Taiwan", "We reiterate our OW rating with a NT$730 price target.", "Irene.Yen@morganstanley.com +886 2 2730-2869",
                                      "Shr price, close (Sep 15, 2026) NT$510.00", "Price target NT$4,388.00 · upside 38%")):
                page.insert_text((72, 72 + 16 * i), line, fontsize=10)
            pdf = Path(td) / "ev.pdf"
            doc.save(str(pdf))
            done = subprocess.run([sys.executable, "-X", "utf8", "-c", EVIDENCE_PY, str(pdf), json.dumps([["CURRENT_PRICE_REPORT", "510.00"], ["TARGET_PRICE", "730.00"], ["UPSIDE_PCT", "38"]])], capture_output=True, text=True, encoding="utf-8", timeout=120)
            got = json.loads(done.stdout.strip().splitlines()[-1])
            lines_of = {k: [r["line"] for r in got if k in r.get("values", [])] for k in ("CURRENT_PRICE_REPORT", "TARGET_PRICE", "UPSIDE_PCT")}
            ev_ok = (lines_of["CURRENT_PRICE_REPORT"] == ["Shr price, close (Sep 15, 2026) NT$510.00"] and lines_of["TARGET_PRICE"] == ["We reiterate our OW rating with a NT$730 price target."]
                     and lines_of["UPSIDE_PCT"] == ["Price target NT$4,388.00 · upside 38%"] and not any("@" in r.get("line", "") for r in got))
            chk("㉑ 證據逐值:數字相等才算(38 不對到 4388 · 730 不對到電話 2730-2869)· Email / 電話行跳過", ev_ok)
        except Exception as error:  # noqa: BLE001
            print("[SKIP] ㉑ 沒有 PyMuPDF / pypdfium2(%s)· 不產生 PDF" % type(error).__name__)
        (v2 / "market" / "vdf" / "last_error.txt").write_text("CMD: python VDF_TW_AllInOne_v039.py --datasets financial\n[FIN] 1303 1/43\n[ERROR] PermissionError: Existing VIA network bridge denied this request\n", encoding="utf-8")
        sys.stdout = io.StringIO()
        try:
            rep4 = diagnose(root, None)
        finally:
            sys.stdout = sys_stdout
        a4 = {x["area"]: x for x in rep4["findings"]}
        chk("㉒ 除錯:⑥e last_error 是 VIA 網路工具 DENY(MOPS)→ 說明「不繞道 · 交 VCGC 決定」· ⑬b 無歷史的原因", "VCGC" in a4.get("⑥e MOPS 財報被拒(VIA 網路工具 DENY)", {}).get("next", "") and "MOPS" in a4.get("⑥e MOPS 財報被拒(VIA 網路工具 DENY)", {}).get("finding", ""))
        # ㉓ ~ ㉗ v0104 收尾頁
        ctx0 = {"receipt": True, "mops_deny": True, "fetch_env_ok": True, "no_cov": {"6933", "4171"}, "gate_other": set(), "combined_gaps": {"TARGET_PRICE(ADJ)": {"原文沒有目標價": 15}}, "combined_owner": None}
        rows = [("YELLOW", "⑥ 收尾收據", "ActivateVRN-2 v0154 · rc 2 · 3654 秒", "彙總"), ("YELLOW", "⑥ ⑥e MOPS 財報被拒(VIA 網路工具 DENY)", "VDF 引擎打 MOPS", "VCGC"),
                ("YELLOW", "⑥ 步驟 ⑥e 市場擷取(TWSE / TPEX / Yahoo · 借共用 Market", "擷取 RED:失敗 4 · rc2", "VCGC"), ("YELLOW", "⑥ 四點原文核對", "REVIEW_OCR · {\"PASS\": 204, \"OCR_PENDING\": 4}", "人工"),
                ("RED", "⑥ 四點原文核對", "FAIL · 3014TT 第 3 點", "VRN-2"), ("YELLOW", "⑥ ⑥f 共識閘 FAIL 列", "2 列 · 代號 4171,6933 · 404", "資料源"), ("YELLOW", "⑥ 完成判定 · ① 結果計算驗證", "黃 1(提醒 · 不擋完成)", "提醒"),
                ("YELLOW", "⑥ ⑪ 基本資料 FAIL 證據", "MS-8358 20260916.pdf · CURRENT_PRICE_REPORT FAIL", "人工"), ("RED", "⑥ 步驟 ⑪ 獨立驗證(背景 · 只讀)", "逾時 3600 秒", "VRN-2"),
                ("YELLOW", "⑥ Combined 冊", "52 列 · 欄序正確", "資料源"), ("RED", "③ 自測 · VRN2_Workbench_v0102.py", "rc 1", "VRN-2"), ("YELLOW", "⑥ 冪等閘", "NONDETERMINISTIC", "VRN-2"),
                ("YELLOW", "② 擷取 Python · VDF 版本界線(⑥e)", "沒有合 pandas>=2.2 的 Python", "VCGC"), ("GREEN", "⑥ Workbench U/I", "都在", None)]
        got = [(owner_of({"lamp": l, "step": st, "detail": d}, ctx0) or (None,))[0] for l, st, d, _ in rows]
        chk("㉓ 收尾頁負責方:收據 rc = 彙總 · MOPS DENY / 擷取環境 = VCGC · OCR / ⑪ 證據 = 人工 · 四點 FAIL / 驗證器逾時 / 自測紅 / 冪等 = VRN-2 · 404 = 資料源 · 不擋 = 提醒 · 綠 = 不列",
            got == [o for *_, o in rows])
        chk("㉓b 認不出來的一律 VRN-2(不把別人的事說成結案)· 沒有收據時「收尾收據」不算彙總", owner_of({"lamp": "YELLOW", "step": "⑥ 新的檢查", "detail": "?"}, ctx0)[0] == "VRN-2"
            and owner_of({"lamp": "RED", "step": "⑥ 收尾收據", "detail": "沒有 x"}, dict(ctx0, receipt=False))[0] == "VRN-2")
        st = [closeout_state([{"owner": o} for o in owners])[0] for owners in (["VRN-2", "VCGC"], ["VCGC", "人工", "資料源"], ["人工", "資料源"], ["資料源"], [])]
        chk("㉔ 結案狀態:VRN-2 有 → OPEN > VCGC → BLOCKED > 人工 → REVIEW > 資料源 → DATA_GAP > PASS(BLOCKED / REVIEW / DATA_GAP 不是成功)", st == ["OPEN", "BLOCKED", "REVIEW", "DATA_GAP", "PASS"])
        gaps, gown = combined_gaps([{"TICKER": "2330", "TARGET_PRICE": "", "TARGET_PRICE(ADJ)": "", "FACTSET_TARGET_PRICE_MEDIAN": "1450", "YFINANCE_TARGET_PRICE_MEDIAN": "1500", "2026_DILUTED_EPS_FACTSET": "60", "STATUS": ""},
                                    {"TICKER": "6933", "TARGET_PRICE": "100", "TARGET_PRICE(ADJ)": "", "FACTSET_TARGET_PRICE_MEDIAN": "", "YFINANCE_TARGET_PRICE_MEDIAN": "90", "2026_DILUTED_EPS_FACTSET": "",
                                     "STATUS": "TARGET_PRICE(ADJ): 缺:MISSING(報告日前沒有日資料) | CONSENSUS: 缺:沒有共識資料(⑥f) · 鉅亨沒有 FactSet 頁(404)"}], {"6933"}, True)
        only_src, own_src = combined_gaps([{"TICKER": "2330", "TARGET_PRICE": "", "TARGET_PRICE(ADJ)": "", "STATUS": ""}], set(), True)
        odd, own_odd = combined_gaps([{"TICKER": "2330", "TARGET_PRICE": "100", "TARGET_PRICE(ADJ)": "", "STATUS": "TARGET_PRICE(ADJ): 缺:除以零"}], set(), True)
        chk("㉕ Combined 空格照原因分:原文沒有目標價不是缺(只剩它 → 綠)· 報告日前沒有日資料 / 鉅亨 404 = 資料源 · 說不出原因 = VRN-2",
            gaps["TARGET_PRICE(ADJ)"] == {"原文沒有目標價": 1, "MISSING(報告日前沒有日資料)": 1} and gaps["FACTSET_TARGET_PRICE_MEDIAN"] == {"鉅亨沒有這檔的 FactSet 頁(404)": 1} and gown == "資料源"
            and own_src is None and only_src == {"TARGET_PRICE(ADJ)": {"原文沒有目標價": 1}} and own_odd == "VRN-2")
        RESULTS.clear()
        for l, st_, d, _ in rows:
            RESULTS.append({"lamp": l, "step": st_, "detail": d, "hint": ""})
        RESULTS.append({"lamp": "YELLOW", "step": "⑥ 輸出缺項", "detail": "<script>alert(1)</script> & \"q\"", "hint": ""})
        (v2 / "market" / "vdf").mkdir(parents=True, exist_ok=True)
        sys.stdout = io.StringIO()
        try:
            page = step_closeout(root, {"at": "2026-10-29T21:00:00", "elapsed_s": 12.5, "package": str(td / "pkg"), "transcript": str(td / "t.log")}, td / "home" / "Downloads" / "VRN2_PasteBack_x.zip", "C:/Users/x/Downloads/VRN2_RoundAll_v0111.py")
        finally:
            sys.stdout = sys_stdout
        html_ = (v2 / CLOSEOUT_HTML).read_text(encoding="utf-8")
        cj = jread(v2 / CLOSEOUT_JSON, {})
        chk("㉖ 收尾頁寫出 html + json:狀態 OPEN(有 VRN-2 項)· 負責方各類都在 · 待辦表 / 檔案 / 下次指令 / 複製鈕 · 不連外(沒有 http)· 內容跳脫(<script> 不會原樣出現)· 貼回包連結用先定好的路徑(之後才打包)",
            page is not None and page["state"] == "OPEN" and cj.get("state") == "OPEN" and not cj.get("vrn2_closed") and 'class="state s-OPEN"' in html_ and "VRN-2 要修" in html_ and "交 VCGC" in html_ and "人工核對" in html_
            and "資料源沒有" in html_ and 'id="items"' in html_ and "下次怎麼跑" in html_ and "VRN2_RoundAll_v0111.py" in html_ and "複製" in html_ and "http://" not in html_ and "https://" not in html_
            and "<script>alert(1)" not in html_ and "&lt;script&gt;alert(1)&lt;/script&gt;" in html_ and html_.count("<script>") == 1 and RESULTS[-1]["step"] == "⑧ 收尾頁(HTML U/I)" and RESULTS[-1]["lamp"] == "RED"
            and next(l for l in cj["links"] if l["label"].startswith("貼回包"))["exists"] and 'class="miss"><b>貼回包' not in html_)
        RESULTS.clear()
        RESULTS.append({"lamp": "YELLOW", "step": "⑥ ⑥e MOPS 財報被拒(VIA 網路工具 DENY)", "detail": "VDF 引擎打 MOPS", "hint": ""})
        RESULTS.append({"lamp": "YELLOW", "step": "⑥ 四點原文核對", "detail": "REVIEW_OCR", "hint": ""})
        sys.stdout = io.StringIO()
        try:
            page2 = step_closeout(root, {"at": "x"}, None)
            zp2 = step_pasteback(root, tr, td / "home" / "Downloads" / "VRN2_PasteBack_plan.zip")
        finally:
            sys.stdout = sys_stdout
        with zipfile.ZipFile(zp2) as z:
            names2 = set(z.namelist())
        chk("㉗ 只剩 VCGC + 人工 → BLOCKED(VRN-2 側可結案 · 不是成功)· 貼回包用先定好的路徑 · 帶收尾頁 html / json · --only 認 closeout",
            page2["state"] == "BLOCKED" and page2["vrn2_closed"] and zp2.name == "VRN2_PasteBack_plan.zip" and "vrn2/" + CLOSEOUT_HTML in names2 and "vrn2/" + CLOSEOUT_JSON in names2
            and "closeout" in STEPS and parse_args(["--only", "report,closeout"]).only == "report,closeout" and parse_args(["--skip-closeout"]).skip_closeout)
        # ㉘ ~ ㉜ v0105:檔被鎖 / 例外不當掉
        g = globals()
        real_sha, real_install, real_fetch, real_pkgsha, real_tries = g["sha256_file"], g["install_package"], g["git_fetch_release"], g["PACKAGE_SHA256"], (g["SHA_TRIES"], g["SHA_WAIT"])
        lockpkg = td / "lockdl" / PACKAGE
        lockpkg.mkdir(parents=True)
        (lockpkg / (PACKAGE + ".zip")).write_bytes(zp.read_bytes())
        calls = {"n": 0}

        def flaky(path):
            if Path(path).name == PACKAGE + ".zip" and Path(path).parent == lockpkg:
                calls["n"] += 1
                if calls["n"] <= 2:
                    raise PermissionError(13, "Permission denied", str(path))
            return real_sha(path)
        sys.stdout = io.StringIO()
        try:
            g["sha256_file"], g["SHA_TRIES"], g["SHA_WAIT"] = flaky, 5, 0.01
            got_r = read_sha(lockpkg / (PACKAGE + ".zip"))
            calls["n"] = -100
            got_x = read_sha(lockpkg / (PACKAGE + ".zip"))
        finally:
            sys.stdout = sys_stdout
            g["sha256_file"], (g["SHA_TRIES"], g["SHA_WAIT"]) = real_sha, real_tries
        chk("㉘ 讀雜湊:被鎖兩次(PermissionError)→ 重試後讀到 · 一直被鎖 → (None, PermissionError …) 不丟例外", got_r[0] == want and got_x[0] is None and "PermissionError" in got_x[1])

        def locked(path):
            if Path(path).parent == lockpkg:
                raise PermissionError(13, "Permission denied", str(path))
            return real_sha(path)

        def install_locked(z_, want_, pkg_, rj_=None):
            if Path(pkg_) == lockpkg:
                raise PermissionError(13, "Permission denied", str(pkg_))
            return real_install(z_, want_, pkg_, rj_)
        RESULTS.clear()
        sys.stdout = io.StringIO()
        try:
            g["sha256_file"], g["SHA_TRIES"], g["SHA_WAIT"], g["PACKAGE_SHA256"] = locked, 2, 0.01, want
            g["install_package"], g["git_fetch_release"] = install_locked, (lambda root_, branch_, work_: (zp, None, "GitHub " + BRANCH))
            got_pkg = step_package(root, type("P", (), {"package": str(lockpkg), "offline": False, "branch": BRANCH})())
        finally:
            sys.stdout = sys_stdout
            g["sha256_file"], (g["SHA_TRIES"], g["SHA_WAIT"]), g["PACKAGE_SHA256"] = real_sha, real_tries, real_pkgsha
            g["install_package"], g["git_fetch_release"] = real_install, real_fetch
        rows = {r["step"]: r for r in RESULTS}
        chk("㉙ ① 本機 zip 被鎖:記證據(GRAY · 不擋)→ 改從 GitHub 取 → 原套件夾用不了 → 裝到新夾 <套件>_<時間>(原夾不動 · 逐檔相符)",
            got_pkg is not None and got_pkg != lockpkg and got_pkg.name.startswith(PACKAGE + "_") and (got_pkg / LAUNCHER).read_bytes() == files[LAUNCHER]
            and rows.get("① 套件 zip 讀不到(改從 GitHub 取)", {}).get("lamp") == "GRAY" and "PermissionError" in rows["① 套件 zip 讀不到(改從 GitHub 取)"]["detail"]
            and rows.get("① 套件", {}).get("lamp") == "GREEN" and "用新夾" in rows["① 套件"]["detail"] and (lockpkg / (PACKAGE + ".zip")).is_file())
        RESULTS.clear()
        sys.stdout = io.StringIO()
        try:
            out_g = guarded("⑥ 除錯報告", lambda: (_ for _ in ()).throw(PermissionError(13, "Permission denied", "x.zip")), default={"d": 1})
        finally:
            sys.stdout = sys_stdout
        src = Path(__file__).read_text(encoding="utf-8")
        chk("㉚ 一步出例外 → 那一步記紅(例外類別 + 訊息)· 回預設值 · main 每一步都包起來(① ② ③ ④ ⑤ ⑥ ⑦)",
            out_g == {"d": 1} and RESULTS[-1]["lamp"] == "RED" and "例外 PermissionError" in RESULTS[-1]["detail"] and "防毒" in RESULTS[-1]["hint"]
            and all(('guarded("%s"' % k) in src for k in ("① 套件", "② VRN-2 Python", "② 診斷", "③ 自測", "④ 跑啟動器", "⑤ 自動修", "⑥ 除錯報告", "⑦ 貼回包")))
        ctx1 = dict(ctx0, combined_owner=None, combined_now=True)
        stale = owner_of({"lamp": "YELLOW", "step": "⑥ 步驟 ⑥f 共識合併(FactSet / YFinance → Combined 冊)", "detail": "共識 GREEN:… · Combined YELLOW:Combined 14 列 · 調整後目標價 0"}, ctx1)
        real_gap = owner_of({"lamp": "YELLOW", "step": "⑥ 步驟 ⑥f 共識合併(FactSet / YFinance → Combined 冊)", "detail": "共識 GREEN:… · Combined YELLOW:…"}, dict(ctx0, combined_owner="資料源", combined_now=True))
        chk("㉛ 收尾頁:⑥f 當時的 Combined 黃在 ⑤ 重組後過時 → 提醒(不再算資料源)· 現在還有缺 → 照缺的負責方", stale[0] == "提醒" and real_gap[0] == "資料源")
        real_write = zipfile.ZipFile.write

        def write_locked(self, filename, arcname=None, *a, **k):
            if str(arcname or "").endswith("VRN2_Workbench_latest.html"):
                raise PermissionError(13, "Permission denied", str(filename))
            return real_write(self, filename, arcname, *a, **k)
        sys.stdout = io.StringIO()
        try:
            zipfile.ZipFile.write = write_locked
            zp3 = step_pasteback(root, tr, td / "home" / "Downloads" / "VRN2_PasteBack_locked.zip")
        finally:
            zipfile.ZipFile.write = real_write
            sys.stdout = sys_stdout
        with zipfile.ZipFile(zp3) as z:
            names3 = set(z.namelist())
            skipped3 = z.read("skipped_files.txt").decode("utf-8") if "skipped_files.txt" in names3 else ""
        chk("㉜ 貼回包:被鎖的檔略過並記在 skipped_files.txt · 其他照包", "vrn2/" + RECEIPT in names3 and "vrn2/VRN2_Workbench_latest.html" not in names3 and "VRN2_Workbench_latest.html(PermissionError)" in skipped3)
        # ㉝ ~ ㊲ v0106
        stage = Path(tempfile.mkdtemp(prefix="vrn2_place_check_"))
        (stage / "sub").mkdir()
        (stage / "a.txt").write_text("a", encoding="utf-8")
        (stage / "sub" / "b.txt").write_text("b", encoding="utf-8")
        dest = td / "placed" / PACKAGE
        dest.parent.mkdir()
        _place(stage, dest)
        src_code = Path(__file__).read_text(encoding="utf-8")
        mode_ok = os.name == "nt" or (dest.stat().st_mode & 0o777) != 0o700
        chk("㉝ 套件安裝不搬暫存夾(Python 3.13 暫存夾只給擁有者權限):目的地正常建夾 · 逐檔複製 · 暫存刪掉 · 權限不是 0o700",
            (dest / "a.txt").read_text(encoding="utf-8") == "a" and (dest / "sub" / "b.txt").read_text(encoding="utf-8") == "b" and not stage.exists() and mode_ok
            and ("shutil.move(str(" + "stage), str(pkg))") not in src_code and ("_place(" + "stage, pkg)") in src_code)
        cpu = owner_of({"lamp": "YELLOW", "step": "② CPU", "detail": "忙碌 93%"}, ctx0)
        chk("㉞ 收尾頁:② CPU 忙碌 → 提醒(不是 VRN-2 要修)", cpu[0] == "提醒")
        g1, o1 = combined_gaps([{"FILENAME": "x.pdf", "TICKER": "", "TARGET_PRICE": "100", "TARGET_PRICE(ADJ)": "", "STATUS": "TARGET_PRICE(ADJ): 缺:基本資料冊代號不是 4 碼"}], set(), True)
        g2, o2 = combined_gaps([{"FILENAME": "y.pdf", "TICKER": "AAPL US", "TARGET_PRICE": "300", "TARGET_PRICE(ADJ)": "", "STATUS": "TARGET_PRICE(ADJ): 缺:基本資料冊代號不是 4 碼"},
                                {"FILENAME": "z.pdf", "TICKER": "2330", "TARGET_PRICE": "1500", "TARGET_PRICE(ADJ)": "", "STATUS": "TARGET_PRICE(ADJ): 缺:MISSING(報告日前沒有日資料 · 需 --start 回補)"}], set(), True)
        chk("㉟ Combined「代號不是 4 碼」:冊裡 TICKER 空白 → 人工(原文有沒有印代號)· 有值但不是台股 4 碼 → 資料源 · 每種原因列檔名(_files)",
            o1 == "人工" and "x.pdf" in g1["_files"]["基本資料冊代號不是台股 4 碼(TICKER 空白)"] and o2 == "資料源" and g2["_files"]["MISSING(報告日前沒有日資料 · 需 --start 回補)"] == ["z.pdf"])
        al_ok = False
        try:
            try:
                import pymupdf as fitz  # noqa: WPS433
            except ImportError:
                import fitz  # noqa: WPS433
            import pypdfium2  # noqa: F401,WPS433
            doc = fitz.open()
            page = doc.new_page()
            for i, line in enumerate(("Daiwa Capital Markets", "Year to 31 Dec 2024A 2025E 2026E 2027E", "EPS (TWD) 85.1 102.3 120.4 141.0", "PBR (x) n.a. 29.2 25.1 20.3", "Tel +886 2 2345 6789")):
                page.insert_text((60, 80 + 18 * i), line, fontsize=10)
            pdf = td / "fin_ev.pdf"
            doc.save(str(pdf))
            res = {}
            for per, val in (("26E", "n.a."), ("24A", "n.a."), ("25E", "29.2")):
                done = subprocess.run([sys.executable, "-X", "utf8", "-c", FIN_EVIDENCE_PY, str(pdf), "1", "PBR (x)", per, val], capture_output=True, text=True, encoding="utf-8", timeout=120)
                got = json.loads(done.stdout.strip().splitlines()[-1])
                res[per] = next((x for x in got if x.get("kind") == "aligned"), {})
            al_ok = (res["26E"].get("at") == "25.1" and res["26E"].get("match") is False and res["24A"].get("at") == "n.a." and res["24A"].get("match") is True
                     and res["25E"].get("match") is True and res["26E"].get("periods") == ["2024A", "2025E", "2026E", "2027E"])
            chk("㊱ ⑪ 年度數據 FAIL 證據:原文表頭(2024A 2025E 2026E 2027E)+ 科目列(PBR (x) n.a. 29.2 25.1 20.3)依欄位對齊 → 26E 是 25.1 ≠ 冊值 n.a.(擷取對錯欄)· 24A 是 n.a. = 冊值(驗證器讀法)", al_ok)
        except Exception as error:  # noqa: BLE001
            print("[SKIP] ㊱ 沒有 PyMuPDF / pypdfium2(%s)· 不產生 PDF" % type(error).__name__)
        hint = acl_hint("C:\\Users\\x\\Downloads\\VRN2_Closeout_v0154\\VRN2_Closeout_v0154.zip: Access is denied.", Path("C:/Users/x/Downloads/VRN2_Closeout_v0154/VRN2_Closeout_v0154.zip"))
        chk("㊲ 證據:icacls「Access is denied」→ 說明權限不給目前使用者 + 以系統管理員身分 icacls /reset 的指令 · 讀得到權限時不多話", "系統管理員" in hint and "/reset /T /C" in hint and acl_hint("ok (F)", Path("x")) == "")
        # ㊳ ㊴ v0107
        dl = Path(os.environ["VRN2_DOWNLOADS"])
        base = dl / PACKAGE
        base.mkdir(parents=True, exist_ok=True)
        (base / LAUNCHER).unlink(missing_ok=True)                            # 原夾讀不到啟動器(桌機:權限)
        older, newer = dl / (PACKAGE + "_20261030_100000"), dl / (PACKAGE + "_20261030_120000")
        for d_, ts_ in ((older, 1000), (newer, 2000)):
            d_.mkdir(exist_ok=True)
            (d_ / LAUNCHER).write_text("x", encoding="utf-8")
            os.utime(d_, (ts_, ts_))
        (dl / (PACKAGE + ".bak_20261030_130000")).mkdir(exist_ok=True)
        os.environ.pop("VRN2_PACKAGE", None)
        fp = find_package(type("Q", (), {"package": None})())
        alts = _alt_folders(base)
        chk("㊳ 略過取套件:原夾讀不到 → 用最新的 <套件>_<時間>(不碰 .bak_ 備份)· --package 優先", fp == newer and alts == [newer, older] and find_package(type("Q", (), {"package": str(older)})()) == older)
        shutil.rmtree(str(older)); shutil.rmtree(str(newer))
        real_install = g["install_package"]
        good = dl / (PACKAGE + "_20261030_140000")

        def install_alt(z_, want_, pkg_, rj_=None):
            if Path(pkg_) == base:
                raise PermissionError(13, "Permission denied", str(pkg_))
            return {"lamp": "GREEN", "detail": "本機已是 %s" % PACKAGE, "pkg": str(pkg_)}
        good.mkdir(exist_ok=True)
        before = sorted(p.name for p in dl.iterdir())
        RESULTS.clear()
        sys.stdout = io.StringIO()
        try:
            g["install_package"] = install_alt
            got_alt = _install_with_fallback(zp, None, base, "GitHub x")
        finally:
            g["install_package"] = real_install
            sys.stdout = sys_stdout
        chk("㊴ 原套件夾用不了 → 先沿用既有的 <套件>_<時間>(不再每輪多建一個 8 MB 的新夾)", got_alt == good and sorted(p.name for p in dl.iterdir()) == before and "沿用" in RESULTS[-1]["detail"])
        # ㊵ ㊶ v0108 ⑪b
        vroot = td / "vroot"
        (vroot / "functional modules" / "VRN2").mkdir(parents=True)
        (vroot / "supportive modules").mkdir(parents=True)
        vv2 = vroot / "VIA_Reports" / "vrn2"
        (vv2 / "output").mkdir(parents=True)
        (vv2 / "scope_in").mkdir(parents=True)
        (vv2 / "output" / "VRN2_FinancialData_latest.json").write_text("[]", encoding="utf-8")
        (vv2 / RECEIPT).write_text(json.dumps({"version": "x", "rc": 2, "steps": [{"step": "⑪ 獨立驗证", "lamp": "YELLOW", "detail": "有待核對 · FAIL 1"}, {"step": "⑪ 獨立驗證(背景 · 只讀)", "lamp": "YELLOW", "detail": "有待核對 · FAIL 1"}]}, ensure_ascii=False), encoding="utf-8")
        fake = ('import json, sys\nfrom pathlib import Path\nB = load("x", "VRN2_Dep_v0100.py") if False else None\n'
                'od, sc, rp = sys.argv[1:4]\nprint("[驗證] 基本資料 1 份 · 欄位檢查 {\'PASS\': 3}")\nprint("[驗證] 年度數據 2 筆 · {\'ALIGNED\': 1, \'NILVAL\': 1}")\n'
                'Path(rp).write_text(json.dumps({"version": "VRN2_IndependentVerifier_v0999", "fin_counts": {"ALIGNED": 1, "NILVAL": 1}}), encoding="utf-8")\nsys.exit(0)\n')
        fake = fake.replace('load("x", "VRN2_Dep_v0100.py") if False else None', 'None  # load("x", "VRN2_Dep_v0100.py")')
        members = {"VRN2_IndependentVerifier_v0998.py": "print('old')\n", "VRN2_IndependentVerifier_v0999.py": fake, "VRN2_Dep_v0100.py": "X = 1\n"}
        vpkg = td / "vpkg"
        vpkg.mkdir()
        with zipfile.ZipFile(vpkg / RUNTIME_ZIP, "w") as z:
            for n_, t_ in members.items():
                z.writestr(n_, t_)
        (vpkg / RUNTIME_MANIFEST).write_text(json.dumps({"files": [{"path": n_, "sha256": hashlib.sha256(t_.encode("utf-8")).hexdigest()} for n_, t_ in members.items()]}), encoding="utf-8")
        RESULTS.clear()
        sys.stdout = io.StringIO()
        try:
            out_v = step_verify(vroot, vpkg, sys.executable)
        finally:
            sys.stdout = sys_stdout
        rec_v = jread(vv2 / RECEIPT, {})
        fmv = vroot / "functional modules" / "VRN2"
        chk("㊵ ⑪b 只重跑獨立驗證:套件 runtime 最新的驗證器(v0999)+ 它 load 的檔補放進 functional modules\\VRN2(核對清單雜湊)→ 照 ⑪ 的方式跑 → 綠 · 收據 ⑪ 換成這次結果(先備份)",
            out_v.get("rc") == 0 and (fmv / "VRN2_IndependentVerifier_v0999.py").is_file() and (fmv / "VRN2_Dep_v0100.py").is_file() and not (fmv / "VRN2_IndependentVerifier_v0998.py").exists()
            and RESULTS[-1]["lamp"] == "GREEN" and "NILVAL" in RESULTS[-1]["detail"] and rec_v["steps"][1]["detail"].startswith("RoundAll 修正後") and (vv2 / (Path(RECEIPT).stem + ".before_roundall.json")).is_file())
        (fmv / "VRN2_IndependentVerifier_v0999.py").write_text("tampered\n", encoding="utf-8")
        RESULTS.clear()
        sys.stdout = io.StringIO()
        try:
            out_x = step_verify(vroot, vpkg, sys.executable)
        finally:
            sys.stdout = sys_stdout
        a1 = parse_args(["--only", "package,verify,report"])
        chk("㊶ ⑪b:同名不同內容不覆寫(紅 · 原檔留著)· --only 有 verify / --verify 才跑(整輪預設不跑,啟動器 ⑪ 已經驗過)",
            out_x == {} and RESULTS[-1]["lamp"] == "RED" and "不覆寫" in RESULTS[-1]["detail"] and (fmv / "VRN2_IndependentVerifier_v0999.py").read_text(encoding="utf-8") == "tampered\n"
            and "verify" in STEPS and a1.only == "package,verify,report" and parse_args(["--verify"]).verify and not parse_args([]).verify)
        # ㊷ v0108 沿用前版收據
        wroot = td / "wroot"
        (wroot / "functional modules" / "VRN2").mkdir(parents=True)
        wv2 = wroot / "VIA_Reports" / "vrn2"
        (wv2 / "output").mkdir(parents=True)
        (wv2 / "scope_in").mkdir(parents=True)
        (wv2 / "output" / "VRN2_FinancialData_latest.json").write_text("[]", encoding="utf-8")
        old_name = "VRN2_Closeout_v01" + "51.json"
        (wv2 / "VRN2_Closeout_v0150.json").write_text(json.dumps({"version": "ActivateVRN-2 v0150", "rc": 2, "steps": []}), encoding="utf-8")
        (wv2 / old_name).write_text(json.dumps({"version": "ActivateVRN-2 v01" + "51", "rc": 2, "elapsed_s": 3900, "passes": [{}], "steps": [{"step": "⑪ 獨立驗證", "lamp": "YELLOW", "detail": "有待核對 · FAIL 1"}],
                                                "roundall": {"version": "VRN2_RoundAll v0107", "fixed": {"⑬": {"lamp": "YELLOW", "detail": "pyarrow"}}}}, ensure_ascii=False), encoding="utf-8")
        (wv2 / (Path(old_name).stem + ".before_roundall.json")).write_text("{}", encoding="utf-8")
        pick1 = receipt_path(wv2)
        RESULTS.clear()
        sys.stdout = io.StringIO()
        try:
            out_w = step_verify(wroot, vpkg, sys.executable)
            diagnose(wroot, sys.executable)
        finally:
            sys.stdout = sys_stdout
        rec_w = jread(wv2 / old_name, {})
        rline = [r for r in RESULTS if r["step"] == "⑥ 收尾收據"]
        zw = td / "w_paste.zip"
        sys.stdout = io.StringIO()
        try:
            step_pasteback(wroot, td / "no_transcript.txt", zw)
        finally:
            sys.stdout = sys_stdout
        names_w = zipfile.ZipFile(zw).namelist() if zw.is_file() else []
        (wv2 / RECEIPT).write_text(json.dumps({"version": "now", "rc": 0, "steps": []}), encoding="utf-8")
        chk("㊷ 這版收據還沒有(桌機只跑過啟動器 v0151)→ 沿用最新的前版收據(不挑 .before_roundall · 不挑更舊的)· ⑪b 改它的 ⑪(之前 ⑤ 修過的紀錄留著)· 除錯報告「收尾收據」不算紅 · 貼回包有它;有這版收據就用這版",
            pick1.name == old_name and out_w.get("rc") == 0 and rec_w["steps"][0]["detail"].startswith("RoundAll 修正後") and sorted(rec_w["roundall"]["fixed"]) == ["⑪", "⑬"]
            and (not rline or (rline[-1]["lamp"] != "RED" and "沿用前版收據 " + old_name in rline[-1]["detail"]))
            and "vrn2/" + old_name in names_w and "vrn2/" + Path(old_name).stem + ".before_roundall.json" in names_w and receipt_path(wv2).name == RECEIPT and bool(rline))
        # ㊸ ㊹ v0109 收尾頁
        cx9 = {"receipt": True, "mops_deny": True, "fetch_env_ok": True, "no_cov": {"6933", "4171"}, "gate_other": set(), "combined_gaps": {"TARGET_PRICE(ADJ)": {"原文沒有目標價": 9}}, "combined_owner": "資料源", "combined_now": True}
        dk_on = {"lamp": "YELLOW", "step": "⑪b 重跑獨立驗證", "detail": "VRN2_IndependentVerifier_v0114 · 有待核對 · 年度數據 11513 筆 · {'ALIGNED': 10424, 'DUPKEY': 45, 'NILVAL': 1}"}
        dk_off = dict(dk_on, detail=dk_on["detail"].replace("'DUPKEY': 45, ", ""))
        dk_fin = {"lamp": "YELLOW", "step": "⑥ ⑪ 年度數據 FAIL 證據(對不齊)", "detail": "{'DUPKEY': 3} · 對不齊"}
        chk("㊸ 收尾頁:⑪ 驗證器數到 DUPKEY > 0(同一列同科目同期間兩個值 · 驗證器寫「錯值 / 分不出」)→ VRN-2 · 沒有 DUPKEY → 人工 · 年度 FAIL 證據照舊規則",
            owner_of(dk_on, cx9)[0] == "VRN-2" and "v0257" in owner_of(dk_on, cx9)[1] and owner_of(dk_off, cx9)[0] == "人工" and owner_of(dk_fin, cx9)[0] == "人工")
        d1834 = [("YELLOW", "⑪b 重跑獨立驗證", dk_off["detail"]), ("YELLOW", "⑥ 步驟 ⑪ 獨立驗證(背景 · 只讀)", "RoundAll 修正後 · VRN2_IndependentVerifier_v0114 · 有待核對"),
                 ("YELLOW", "⑥ 步驟 ⑥e 市場擷取(TWSE / TPEX / Yahoo · 借共用 Market", "擷取 RED:失敗 4"), ("YELLOW", "⑥ 四點原文核對", "REVIEW_OCR · {\"PASS\": 204, \"OCR_PENDING\": 4}"),
                 ("YELLOW", "⑥ 輸出缺項", "{\"book\": \"四點原文核對\", \"reason\": \"REVIEW_OCR\"}"), ("YELLOW", "⑥ 完成判定 · 輸出冊(基本資料 / 年度數據 / 一標題四重點)", "個股 52 份 · 缺項 3 份"),
                 ("YELLOW", "⑥ Combined 冊", "52 列 · 欄序正確 · 空格"), ("YELLOW", "⑥ ⑥e 擷取錯誤(last_error.txt)", "[ERROR] PermissionError: Existing VIA network bridge denied this request"),
                 ("YELLOW", "⑥ ⑥e MOPS 財報被拒(VIA 網路工具 DENY)", "VDF 引擎打 MOPS"), ("YELLOW", "⑥ 市場資料", "{\"OK\": 51, \"MISSING\": 1}"),
                 ("YELLOW", "② 擷取 Python · VDF 版本界線(⑥e)", "沒有合 pandas>=2.2 的 Python"), ("YELLOW", "⑥ 收尾收據", "ActivateVRN-2 v0151 · rc 2 · 3367 秒")]
        its = [dict({"lamp": l, "step": st, "detail": d}, owner=owner_of({"lamp": l, "step": st, "detail": d}, cx9)[0], why=owner_of({"lamp": l, "step": st, "detail": d}, cx9)[1]) for l, st, d in d1834]
        merged = merge_same(its, cx9)
        real9 = [i for i in merged if i["owner"] not in ("提醒", "彙總")]
        st9, _t9, po9 = closeout_state(real9)
        its2 = [dict(i) for i in its]
        its2[0] = dict(its2[0], detail=dk_on["detail"], owner="VRN-2", why=owner_of(dk_on, cx9)[1])
        m2 = merge_same(its2, cx9)
        st2, _t2, po2 = closeout_state([i for i in m2 if i["owner"] not in ("提醒", "彙總")])
        lead = next(i for i in m2 if i.get("also") and "⑪" in i["step"])
        chk("㊹ 收尾頁同一件事只列一次:桌機 18:34 那 12 列 → ⑪b + 收據 ⑪ 合一 · 四點 + 輸出缺項(四點)合一 · ⑥e 步驟 / last_error / MOPS 合一 · 擷取 Python 環境不併 → %s %s · 有 DUPKEY → %s %s(負責方取最重 · 另見寫在為什麼)"
            % (st9, po9, st2, po2),
            st9 == "BLOCKED" and po9 == {"人工": 3, "VCGC": 2, "資料源": 2} and len(merged) == len(its) - 4 and st2 == "OPEN" and po2.get("VRN-2") == 1 and po2.get("人工") == 2
            and lead["owner"] == "VRN-2" and "同一件事另見" in lead["why"] and lead["also"] == ["⑥ 步驟 ⑪ 獨立驗證(背景 · 只讀)"])
        # ㊺ ~ ㊾ v0110 ⑥f 共識(桌機 20:09)
        r10 = td / "r110" / "VIA"
        v10 = r10 / "VIA_Reports" / "vrn2"
        (v10 / "consensus").mkdir(parents=True)
        (v10 / "output").mkdir(parents=True)
        (v10 / "output" / "VRN2_BasicInfo_latest.json").write_text("[]", encoding="utf-8")
        qm = v10 / "consensus" / "factset_yfinance_consensus_quality_matrix.csv"
        qm.write_text("\ufeffcode,check_id,actual,expected,status,severity,note\n8358,FETCH_PIPELINE,ASSIGNED_JSON_NOT_FOUND: __NEXT_DATA__,successful fetch,FAIL,FAIL,Ticker fetch failed.\n"
                      "2891,FETCH_PIPELINE,ASSIGNED_JSON_NOT_FOUND: __NEXT_DATA__,successful fetch,FAIL,FAIL,Ticker fetch failed.\n2330,HTTP_PAGE_200,200,200,PASS,FAIL,ok\n", encoding="utf-8")
        why102 = "共識 38 / 40 代號(缺 8358,2891)· gate FAIL_CLOSED · rc 1 · 鉅亨沒有 FactSet 頁(404)不納入閘:4171,6933,7728"
        (v10 / "consensus" / "VRN2_Consensus_latest.json").write_text(json.dumps({"gate": "FAIL_CLOSED", "why": why102, "no_coverage": {"4171": "404", "6933": "404", "7728": "404"}}, ensure_ascii=False), encoding="utf-8")
        comb10 = [{"TICKER": "8358", "FILENAME": "a.pdf", "TARGET_PRICE": "", "FACTSET_TARGET_PRICE_MEDIAN": "", "STATUS": "CONSENSUS: 缺:" + why102 + " | BASIC: B"},
                  {"TICKER": "6933", "FILENAME": "b.pdf", "TARGET_PRICE": "", "FACTSET_TARGET_PRICE_MEDIAN": "", "STATUS": "CONSENSUS: 缺:" + why102 + " | BASIC: B"}]
        g1, o1 = combined_gaps(comb10, {"6933", "4171", "7728"}, True)
        g2, o2 = combined_gaps(comb10, {"6933"}, True, {"8358"})
        chk("㊺ Combined 空格每列看它自己:整批摘要裡「鉅亨沒有 FactSet 頁(404)不納入閘:4171,6933,7728」不再讓 8358 也算 404(桌機 6 列裡 2 列算錯)· 8358 在 source_gap → 鉅亨這次沒給(資料源)",
            g1["FACTSET_TARGET_PRICE_MEDIAN"].get("鉅亨沒有這檔的 FactSet 頁(404)") == 1 and o1 == "VRN-2" and g2["FACTSET_TARGET_PRICE_MEDIAN"] == {"鉅亨沒有這檔的 FactSet 頁(404)": 1, "鉅亨這次沒給資料(暫缺 · 下輪再抓)": 1} and o2 == "資料源")
        q404, qtr, qot = gate_rows(v10)
        cx10 = closeout_context(r10)
        row10 = {"lamp": "YELLOW", "step": "⑥ 步驟 ⑥f 共識合併(FactSet / YFinance → Combined 冊)", "detail": "共識 YELLOW:" + why102 + " · Combined GREEN:Combined 52 列"}
        own102 = owner_of(row10, cx10)
        cx10b = dict(cx10, gate_transient=set(), cj_v0103=True, source_gap={"2891": {"why": "ASSIGNED_JSON_NOT_FOUND: __NEXT_DATA__", "tries": 3}})
        own103 = owner_of(dict(row10, detail="共識 YELLOW:共識 39 / 39 代號 · gate PASS · 鉅亨這次沒給資料(抓了 3 次)暫不納入閘:2891"), cx10b)
        own_other = owner_of(row10, dict(cx10, gate_other={"2330"}))
        chk("㊻ 收尾頁 ⑥f:8358 / 2891 沒有 __NEXT_DATA__ = 一時抓不到(不是「別的不過」)· v0103 以前做的 → VRN-2(說明整批重抓的根因)· v0103 的 source_gap → 資料源 · 別的不過 → VRN-2",
            q404 == set() and qtr == {"8358", "2891"} and qot == set() and cx10["gate_transient"] == {"8358", "2891"} and not cx10["cj_v0103"]
            and own102[0] == "VRN-2" and "checkpoint" in own102[1] and own103[0] == "資料源" and "2891" in own103[1] and "抓了 3 次" in own103[1] and own_other[0] == "VRN-2" and "2330" in own_other[1])
        rcp10 = {"consensus": {"run": {"lamp": "YELLOW", "gate": "FAIL_CLOSED", "why": why102}}}
        p10 = [k for k, _ in plan_fixes(r10, rcp10, "/x/py", A(), "")]
        cj10 = json.loads((v10 / "consensus" / "VRN2_Consensus_latest.json").read_text(encoding="utf-8"))
        (v10 / "consensus" / "VRN2_Consensus_latest.json").write_text(json.dumps(dict(cj10, retries=[]), ensure_ascii=False), encoding="utf-8")
        p10b = [k for k, _ in plan_fixes(r10, rcp10, "/x/py", A(), "")]
        (v10 / "consensus" / "VRN2_Consensus_latest.json").write_text(json.dumps(cj10, ensure_ascii=False), encoding="utf-8")
        qm.write_text(qm.read_text(encoding="utf-8") + "1234,FETCH_PIPELINE,HTTP_GET_FAILED: HTTP Error 404: Not Found,successful fetch,FAIL,FAIL,x\n", encoding="utf-8")
        p10c = [k for k, _ in plan_fixes(r10, rcp10, "/x/py", A(), "")]
        p10d = [k for k, _ in plan_fixes(r10, rcp10, None, A(), "")]
        chk("㊼ ⑤ 自動修:共識閘只因 404 / 一時抓不到、是 v0103 以前做的 → 用 v0103 重跑 ⑥f + 重組 Combined · 已是 v0103(收據有 retries)→ 不重跑 · 有別的不過 / 沒有擷取 Python → 不重跑",
            p10[:2] == ["consensus", "combined"] and "consensus" not in p10b and "consensus" not in p10c and "consensus" not in p10d)
        rows10 = [("YELLOW", "⑥ 步驟 ⑥f 共識合併(FactSet / YFinance → Combined 冊)", row10["detail"]), ("YELLOW", "⑥ ⑥f 共識閘 FAIL 列", "2 列 · 代號 2891,8358 · 8358 FETCH_PIPELINE 實際 ASSIGNED_JSON_NOT_FOUND"),
                  ("GREEN", "⑥ ⑥f Yahoo 代號", "對應表 40 筆"), ("YELLOW", "⑥ ⑥f Yahoo 代號", "Yahoo 404:6933.TW"), ("YELLOW", "⑥ Combined 冊", "52 列 · 欄序正確 · 空格")]
        cx10m = dict(cx10, combined_gaps=g1, combined_owner=o1)
        its10 = [dict({"lamp": l, "step": st_, "detail": d}, owner=(owner_of({"lamp": l, "step": st_, "detail": d}, cx10m) or (None, ""))[0], why=(owner_of({"lamp": l, "step": st_, "detail": d}, cx10m) or (None, ""))[1]) for l, st_, d in rows10]
        its10 = [i for i in its10 if i["owner"]]
        m10 = merge_same(its10, cx10m)
        st10, _t10, po10 = closeout_state([i for i in m10 if i["owner"] not in ("提醒", "彙總")])
        m10b = merge_same(its10, dict(cx10m, combined_gaps={"TARGET_PRICE(ADJ)": {"別的原因": 1}, "FACTSET_TARGET_PRICE_MEDIAN": g1["FACTSET_TARGET_PRICE_MEDIAN"]}))
        chk("㊽ 收尾頁同一件事只列一次:⑥f 步驟列 + 共識閘 FAIL 列 + Combined 冊(VRN-2 的空格全是「共識缺」)= 同一次共識 → 1 項(桌機算成 VRN-2 2 項)· Yahoo 代號另列 · Combined 還有別的 VRN-2 空格 → 不併 → %s %s" % (st10, po10),
            po10 == {"VRN-2": 1, "資料源": 1} and len(m10) == 2 and any(i.get("also") == ["⑥ ⑥f 共識閘 FAIL 列", "⑥ Combined 冊"] for i in m10) and len(m10b) == 3
            and combined_consensus_only(g1) and not combined_consensus_only(g2))
        pk10 = td / "pk110"
        pk10.mkdir()
        body10 = b"VERSION = 'v0103'\n"
        with zipfile.ZipFile(pk10 / RUNTIME_ZIP, "w") as z:
            z.writestr("VRN2_ConsensusJoin_v0103.py", body10)
            z.writestr("VRN2_ConsensusJoin_v0102.py", b"old\n")
            z.writestr("VRN2_Workbench_v0102.py", b"wb\n")
        (pk10 / RUNTIME_MANIFEST).write_text(json.dumps({"files": [{"path": "VRN2_ConsensusJoin_v0103.py", "sha256": hashlib.sha256(body10).hexdigest()},
                                                                   {"path": "VRN2_ConsensusJoin_v0102.py", "sha256": hashlib.sha256(b"old\n").hexdigest()}]}), encoding="utf-8")
        fm10 = r10 / "functional modules" / "VRN2"
        fm10.mkdir(parents=True)
        (fm10 / "VRN2_ConsensusJoin_v0102.py").write_bytes(b"different\n")
        put10, ref10 = place_consensus(pk10, r10)
        put10b, ref10b = place_consensus(pk10, r10)
        chk("㊾ ⑤ 重跑 ⑥f 前補放套件 runtime 的 ConsensusJoin:v0103 補放(雜湊對清單)· 已在的同名不同內容 v0102 不覆寫 · 別的模組不動 · 再跑一次 = 已在(不重放)",
            put10 == ["VRN2_ConsensusJoin_v0103.py"] and ref10 == ["VRN2_ConsensusJoin_v0102.py"] and (fm10 / "VRN2_ConsensusJoin_v0103.py").read_bytes() == body10
            and (fm10 / "VRN2_ConsensusJoin_v0102.py").read_bytes() == b"different\n" and not (fm10 / "VRN2_Workbench_v0102.py").exists() and put10b == [] and ref10b == ["VRN2_ConsensusJoin_v0102.py"])
        cx_no = dict(cx10, engine_no_output={"rc": 1, "last": "RuntimeError: NO_PAYLOAD_FETCHED: [...]"}, gate_other={"2330"})
        own_no = owner_of({"lamp": "YELLOW", "step": "⑥ 步驟 ⑥f 共識合併(FactSet / YFinance → Combined 冊)", "detail": "共識 YELLOW:共識引擎這次沒有產出(rc 1 · NO_PAYLOAD_FETCHED)· 上次的矩陣不算這次的"}, cx_no)
        g_no, o_no = combined_gaps([{"TICKER": "2330", "TARGET_PRICE": "", "FACTSET_TARGET_PRICE_MEDIAN": "", "STATUS": "CONSENSUS: 缺:共識引擎這次沒有產出(rc 1 · NO_PAYLOAD_FETCHED)"}], set(), True)
        chk("㊿ ⑥f 共識引擎這次沒有產出(ConsensusJoin v0103 不沿用上次的矩陣)→ 資料源(網路被擋則交 VCGC)· 上次的品質矩陣不看 · Combined 那幾格同樣算資料源",
            own_no[0] == "資料源" and "NO_PAYLOAD_FETCHED" in own_no[1] and o_no == "資料源" and g_no["FACTSET_TARGET_PRICE_MEDIAN"] == {"共識引擎這次沒有產出(整批沒抓到)": 1})
        # 51 v0111 桌機 02:06:Combined 的 AAPL 列
        why40 = "共識 40 / 40 代號 · FactSet 中位數 40 · YFinance 中位數 39 · 上櫃 .TWO 7 · gate PASS_WITH_WARNINGS · rc 0 · 鉅亨沒有 FactSet 頁(404)不納入閘:4171,6933,7728"
        rows51 = [{"TICKER": "AAPL", "FILENAME": "GFHK - Apple update 20260915.pdf", "TARGET_PRICE": "", "FACTSET_TARGET_PRICE_MEDIAN": "", "YFINANCE_TARGET_PRICE_MEDIAN": "", "2026_DILUTED_EPS_FACTSET": "",
                   "STATUS": "CONSENSUS: 缺:" + why40 + " | BASIC: B"},
                  {"TICKER": "6933", "FILENAME": "6933_AMAX-KY_個股介紹報告.pdf", "TARGET_PRICE": "", "FACTSET_TARGET_PRICE_MEDIAN": "", "STATUS": "CONSENSUS: 缺:鉅亨沒有 FactSet 頁(404) | BASIC: B"},
                  {"TICKER": "2330", "FILENAME": "a.pdf", "TARGET_PRICE": "", "FACTSET_TARGET_PRICE_MEDIAN": "1450.00", "STATUS": "CONSENSUS: FactSet(鉅亨)20 位"}]
        g51, o51 = combined_gaps(rows51, {"4171", "6933", "7728"}, True)
        g51b, o51b = combined_gaps([dict(rows51[0], TICKER="")], set(), True)
        g51c, o51c = combined_gaps([dict(rows51[0], TICKER="1590")], set(), True)
        chk("51 Combined:代號不是台股 4 碼(GFHK Apple · AAPL)那列共識欄空 → 資料源(桌機 02:06 被 v0110 算成 VRN-2)· TICKER 空白 → 人工 · 台股代號的「共識缺」照舊 VRN-2",
            o51 == "資料源" and g51["FACTSET_TARGET_PRICE_MEDIAN"] == {"代號不是台股 4 碼(TICKER 'AAPL')· 共識只查台股": 1, "鉅亨沒有這檔的 FactSet 頁(404)": 1}
            and o51b == "人工" and o51c == "VRN-2" and not combined_consensus_only(g51))
    for k, v in saved_env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    RESULTS.clear()
    print("[%s] %s %s --selftest · %d 項 · 不過 %d" % ("PASS" if not bad else "FAIL", NAME, VERSION, len(ran), len(bad)), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
