#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_selftest_grid_v0129 — 全面自測矩陣(+合約同步/族群量價站)
====================================================================
v0100→v0101:新增第 18 站 SuperDocExtractor selftest(導入自會話
016d7f;15 檢全綠基準)。
v0101→v0102:新增第 19 站 vrn_table_omni 車道矩陣(TOOL-029;唯讀
可用性探測 rc0,不擷取)。
v0102→v0103:新增第 20 站 via_env_plan --offline(TOOL-030;快照+
計畫零網路 rc0)。
v0103→v0104:新增第 21 站 via_dep_super --selftest(TOOL-031;
PEP440 判定器+圖譜衝突掃描 15 檢,零網路零環境依賴 rc0)。
v0104→v0105:雙會話合流——撞版勘誤(本會話曾誤覆寫 v0104,已回復
他方正本):+第 22 站表格統包 --selftest(TOOL-029 四檢)+第 23 站
收編管線 dry(TOOL-036;掃描根缺=env SKIP 誠實)。
v0105→v0106:+第 24 站契約介面引擎 32 測(TOOL-037;pytest/pydantic
缺=env SKIP)+第 25 站留痕包裝器(TOOL-038 --list rc0)。
v0106→v0107:撞版合流(9hh5to 會話亦造 v0106)——併入其重建計畫
自測+教訓帳本 10 檢兩站(27 站)。
v0107→v0108(操作員令 2026-08-18:strengthen optimize automate all
engine · VIA VDF VAP VRN FLOW):五系統全覆蓋——+第 28 站 FlowSystem
14 檢(flow_selftest 合成流零網路)+第 29 站文章攝入五檢(TOOL-045)
+第 30 站介面合約 dry(TOOL-041 零寫入)+第 31 站 office 併表橋 dry
(TOOL-044;空收件夾=rc0 誠實 SKIP 訊息)+第 32 站 ChipWar 引擎編譯
檢(TOOL-043;py_compile 零執行,_sha 鏡像/檢疫夾除外)+第 33/34 站
命名冊六檢+dry(TOOL-047 自動編號註冊命名)——34 站。
v0108→v0109:+第 35 站產品門面九檢(TOOL-048;六頁產出+視覺鎖定
+零 CDN+誠實界線標註)——35 站。
v0109→v0110:+第 36 站缺口總攻四檢(TOOL-049 多方案指揮)——36 站。
v0110→v0111:+第 37/38 站文字統包六檢+矩陣(TOOL-050;十車道+三閘)——38 站。
v0111→v0112:+第 39 站 SuperAccel 六檢(斷點補齊;同意閘/平行/快取)——39 站。
v0112→v0113:+第 40 站引擎總目錄四檢(TOOL-054 全 ENG 覆蓋+實值說明比)——40 站。
v0113→v0114:+41 三因子吸引力四檢+42 lead-lag 邊四檢(TOOL-055)
+43 VME 核心八檢(TOOL-056 方法論導入)——43 站。
v0114→v0115:+第 44 站 VDF 輸出樞紐七檢(TOOL-058 統一參數 SSOT+
六格式輸出 parquet/csv/duckdb/sqlite/sql/gsheet相容+讀回驗證)——44 站。
v0115→v0116:+第 45 站字庫知識樹八檢(TOOL-059 中英文字庫+樹枝
編號 K1-K8+讀報自動建構+JSON 模板回填+審核閉環)——45 站。
v0116→v0117:+46 台灣主動式ETF六檢+47 全球ETF流觀察六檢+48 族群
三分類/族群指數六檢(TOOL-060/061/062)——48 站。
v0117→v0118:+第 49 站中央治理台八檢(TOOL-063 三輪全景/SSOT+
Regex 治理中心/四分區 Matrix/Zero-Hydra)——49 站。
v0118→v0119:+第 50 站語法救援七檢(TOOL-064 三輪沙盒救援/原件
零觸碰/提案並排候裁)——50 站。
v0119→v0120:+第 51 站更名引擎七檢(TOOL-065 SAFE/RISKY/HOLD 分級
/test檔名契約保護/編號永不變鍵遷移/undo 可逆)——51 站。
v0120→v0121:+第 52 站樹圖譜八檢(TOOL-066 向右樹五層/ENV 矩陣
find_spec 安全探測/搜尋濾枝/鍵遷移相容)——52 站。
v0121→v0122:+第 53 站 Matrix 主控台八檢(TOOL-067 VRN 驗證矩陣
/VDF 運作摘要/族群量價指標三 tab;數據驅動誠實候態)——53 站。
v0122→v0123:+第 54 站收尾系統七檢(TOOL-068 舊根導入確認 hash 對
正典/并行電池/缺件誠實 SKIP)——54 站。
v0123→v0124(批41 參數中央化+個股報告摘要):+第 55 站中央參數
樞紐七檢(TOOL-069 十六冊指標索引/跨冊衝突燈/LOCKED 對齊/central_get)
+第 56 站報告摘要批跑七檢(TOOL-070 Summarizer 統包一標題五點/
填充語〔自動生成〕標註/docx 零外依道/ticker 年區疊閘)——56 站。
v0124→v0125(批43 方法統一令):+第 57 站 VRN 方法核十二檢
(TOOL-071 def01-20 方法冊/raw 永不覆寫/混合容忍三態/成長六態/
單季換算閘/三表勾稽/缺值語意/仲裁表)——57 站。
v0125→v0126(批44 三字庫令):+第 58 站財務三字庫八檢(TOOL-072
broker dict 29 家/財務數據中英同義四源合流/報表同義科目歸屬/CJK
分類器/沙盒落冊)——58 站。
v0126→v0127(批45 五件擴源):字庫站自動接 v0101 十二檢(八源合流
+評等冊+ticker/date regex 冊+AST 零執行收割);params 站自動接
v0103(22 冊+對齊檢鍵尾段全等精修)。站數不變 58。
v0127→v0128(批51):+第 59 站註冊台維運八檢(TOOL-075 個股清單/
ETF 持股攝入/AUM 流覆蓋稽核/同意閘誠實)+第 60 站指揮中心十檢
(TOOL-074 多矩陣一頁/數據驅動候態/操作面複製鈕)——60 站。
v0128→v0129(批52-54):+第 61 站合約同步引擎 self-test(收容件
VIA_Central_SSOT_Contract_Sync_Engine:期間解析/評等目標價別名/
fail-closed 閘)+第 62 站族群量價引擎 self-test(收容件 GroupIndex
量價波動;合成走查)——62 站。
執行器新增 pycode 站型(標準庫內聯檢,零外部檔)。
v0137→v0138(批83):+第 75 站介面自湊引擎十四檢(TOOL-089 模組對
模組 mapping/connecting/syncing/activate;O_EXCL 跨平台鎖/原子寫入/
WAL 版本閘防迴圈/輪詢監聽防自觸發)——75 站。
v0138→v0139(批87):+第 76 站 py 加速啟動器四檢(TOOL-091 Celeritas
常駐 runpy;spec_from_file_location 直載=繞開 accelerator/subprocess.py
遮蔽地雷 QA-20260820C)——76 站。
v0139→v0140(批88):+第 77 站 VDF 整合輸入介面矩陣十三檢(TOOL-093
五分區活冊:INTL 增減項目/個股+TW 財報單季累計年度+VRN 路徑三重點
+堆圖新增;軟移除零刪除+restore)——77 站。
v0140→v0141(批95):+第 78 站母系統向下接手十二檢(TOOL-097 六路:
PS 治理考古/雙世代引擎舉證核准閘/SSOT 矛盾+regex 提醒/加速器稽核/
支援模組 SUP 自動註冊/外呼網路稽核)——78 站。
v0141→v0142(批97 焦點四柱):+第 85 站三子系統管理十檢(TOOL-099
憲章對讀/四類盤點/AST 健康 RYG/VSM 遞迴迷你報/缺根缺憲章誠實)
——85 站。
v0156→v0157(批133):+第 94 站治理議題分圈器六檢(CGC_MDL084
GovTriage:七圈先到先判 QUARANTINE/SCOPE_BACKUP/RUNS_EVIDENCE/
EXEMPT_INTAKE/LEGACY_NET/DICT_ARCHIVE/ACTIVE;65,342 議題分圈+
沙盒修補對勘 no promotion)——94 站。
v0157→v0158(批133):+第 95 站議題仲裁器八檢(CGC_MDL085
IssueArbiter:活動圈 CRITICAL 逐類仲裁——影子/鏡像/版史/真雙
四鏡頭+SYNTAX 覆核三態+密鑰偽陽實勘;唯讀建議制零改動)——95 站。
v0158→v0159(批133 收官):+第 96 站正典裁定器六檢(CGC_MDL086
CanonArbiter:R1 位置正典[退役最低/functional 優先]+R2 ID 正當
持有人;正典冊 append-only;零刪除零搬移)——96 站。
v0159→v0160(批134):+第 97 站 VDF 參數映射器十檢(VDF_ENG053
ParamEngineMap:四冊聯動+AST 常數/argparse CLI 雙面收割+車道/
分區源碼實證映射+治理五態;唯讀收割)——97 站。
v0160→v0161(批136 白名單生效波):+第 98 站台股回補工人六檢
(VDF_ENG054:雙所清單落庫+全市場日線 chart 直連回補+檢查點
續跑+upsert 冪等;同意閘 fail-closed)——98 站。
v0161→v0162(批137 大擷取令):+第 99 站總擷取執行器八檢
(VDF_ENG055 OmniFetch:單 004 八車道——清單附產業/成交值/
PE·PB/ETF 冊+主動旗標/AUM 流量/全球擴編/估值代理/FRED 候鑰;
checkpoint+批次落盤斷點零浪費)——99 站。
v0162→v0163(批140):+第 100 站籌碼回補引擎六檢(VDF_ENG056
ChipBackfill:雙所三大法人+融資融券逐日;交易日曆=已庫價格日期;
傳輸敗不記 done 保重試權;按欄名插入防錯位)——100 站。
v0163→v0164(批141):+第 101 站知識堆疊轉接八檢(VRN_ENG064:
送達三件 byte-exact 收容+npl_preprocessor 記憶體級補殼+demo 三元組
真值三檢+mail tracker v2 收編測 pytest 2 綠+P2382 API 真值)——101 站。
v0164→v0165(批142):+第 102 站測試金字塔六檢(CGC_MDL087:
T1 單元 grid/T2 整合六道跨件互接/T3 系統 autorun;主控台 U/I
淺色 auto-fit+Playwright 三視窗橫向實測)——102 站。
v0165→v0166(批143):+第 103 站郵件情報管線八檢(VRN_ENG065
MailIntel:tracker×NLP 合流+彙總矩陣+高優先+TF-IDF 榜+MD/JSON
報告)——103 站。
v0166→v0167(批145):+第 104 站寬表刷新器六檢(VAP_ENG007:
實抓雙庫→MacroRawWide 合併延伸;既有值零觸碰+備份側件)——104 站。
v0167→v0168(批149):+第 105 站主動 ETF 持股引擎 self-test
(ENG051 批131 收容件;25/30 檔實抓已證)——105 站。
v0193 追記(批208):+第 135 站執行橋八檢(CGC_MDL095:127.0.0.1
白名單任務橋=按下直跑+RYG 狀態矩陣+解方冊;任意指令拒絕)——135 站。
v0194 追記(批218):+第 136 站全景同步狀態台八檢(CGC_MDL096:GitHub↔
雲端↔本機六矩陣一頁堆疊;selftest 零觸網 no-fetch)+第 137 站資料庫合併匯入八檢(VDF_ENG065:
批216 三包遞送道;anti-join 只增不減)——137 站。
v0195 追記(批222):+第 138 站使用者介面總入口八檢(CGC_MDL097:
Portal 單頁=核心 4+分析 5+全冊尾版動態;橋偵測誠實三態)——138 站。
v0196 追記(批226):+第 139 站全球宇宙擷取八檢(VDF_ENG066:宇宙冊
11 類 SSOT;候源誠實)+第 140 站資料庫目錄台八檢(CGC_MDL098:完整
header 細則+勾選日期控制)——140 站。
v0197 追記(批227):+第 141 站全球市場觀測八檢(CGC_MDL099:11 類
實值矩陣+SVG 走勢;紅漲綠跌;候源誠實)——141 站。
v0198 追記(批235):+第 142 站首頁文字擷取八檢(VRN_ENG072:fitz
版面序/pypdf 後備/NEEDS_OCR 誠實;抽取物不入 git)——142 站。
v0199 追記(批237):+第 143 站報告結構化入庫十檢(VRN_ENG073:
官方名冊正主/交互驗證/雙 SSOT/anti-join)——143 站。
v0200 追記(批241):+第 144 站券商報告卡八檢(CGC_MDL100)+第 145
站財報頁擷取十檢(VRN_ENG074:SynonymEngine 對齊)——145 站。
v0201 追記(批243):+第 146 站共識增益橋十檢(VDF_ENG067:收容
Adapter graceful 掛+fixture 端到端+來源分欄紅線)——146 站。
v0202 追記(批244):+第 147 站 PS AST 修正引擎十檢(CGC_MDL101:
全景掃描+雙軌診斷+Zero-Hydra 讓位修+RYG 四專區矩陣)——147 站。
v0203 追記(批247):+第 148 站圖庫 SSOT 橋十檢(VAP_ENG010:收容
圖庫/工作流 spec 尾版解析+ssot_rules 驗證+runtime 合流快照)——148 站。
v0204 追記(批249):+第 149 站文件→MD 引擎十檢(VRN_ENG075:
markitdown 正主+NLP ingest HTML reader+雙法對照)+第 150 站指令
整合冊六檢(CGC_MDL102:正道/引擎 CLI/舊代三分區動態盤點)——150 站。
v0205 追記(批250):+第 151 站 TPN 模板冊十二檢(VAP_ENG011:七函式
登記+連接點矩陣+雙軸唯一號+複合引用制同步)——151 站。
v0206 追記(批251):+第 152 站抽取鏈迴歸閘八檢(VRN_ENG076:64 件
真基準對照;TP 100%)+第 153 站治理存圖八檢(VAP_ENG012:批250
唯一斷點補齊)——153 站。
v0207 追記(批255):+第 154 站加速器覆蓋十檢(CGC_MDL103:全樹
scan/inject 安全注入+compile 守衛+整併稽核)——154 站。
v0208 追記(批256):+第 155 站 VOFIE 全格式橋八檢(VRN_ENG077:收容
引擎駕馭+五檔輸出契約+同功能族分工)——155 站。
v0209 追記(批257):+第 156 站測試結果總表六檢(CGC_MDL104:五源
存證導入零重測+一頁 RYG)——156 站。
v0210 追記(批258):+第 157 站治理主控台六檢(CGC_MDL105:操作員
設計稿保真+七閘真燈+現役頁接線)——157 站。
v0211 追記(批259 兄弟流合流):+四站——市場分析引擎(VAP_ENG013
K線/量值/法人/資金流)+Gov 主控台(MDL106)+UI 元件轉碼管理
(MDL107)+對話轉文(MDL108)——161 站。
v0212 追記(批264):+二站——主動 ETF×共識分析(VDF_ENG068 加權
upside 可複算)+月營收×共識分析(VDF_ENG069 四象限守恆)——163 站。
v0213 追記(批265):+一站——Prompt 儲存管理(CGC_MDL109 append-only
+hash 定生死+版本回溯;主控台 v0101 左欄二功能同批)——164 站。
v0214 追記(批267):+一站——三軌測試矩陣(CGC_MDL110 系統/使用者
/驗證三軌;MDL104 資料層複用零重測)——165 站。
v0215 追記(批278):+一站——統一 U/I 元件盤點(CGC_MDL111 頁域
×MDL107 六類×共用判定)——166 站。
v0216 追記(批279):+一站——標準儀表板模板(VAP_ENG014 三層階層
×多頁 Plotly×參數重繪)——167 站(v0215 讓位單一終判)。
v0217 追記(批280/281):+二站——系統現況總圖(MDL112 六區全譜)
+總系統管理器(VIA_SYSTEM_MANAGER 四職)——169 站。
v0218 追記(批283):+一站——NLP OneEngine 收容橋(VRN_ENG078
語意尾版×八類歸類×離線正道)——170 站。
v0219 追記(批287):+一站——統一編號註冊器(CGC_MDL113 編號永久
律×用態真掃×SSOT 目錄)——171 站。
v0220 追記(批288):+一站——AIO 指揮中心收容橋(CGC_MDL114
14 閘×契約抽取×2,593 件健康圖)——172 站。
v0221 追記(批296):+一站——中央 SSOT Regex 治理中心(CGC_MDL115
809 樣式×330 共用×四分區)——173 站。
v0222 追記(批297 八單元稽核實錘):+二站(VAP_ENG003 自測/VDF_
ENG046 八檢=網格層首覆蓋)+站名漂移修二(月營收八檢→九檢/
SuperAccel 六檢→六檢)——175 站。
v0193 追記(批204):+第 134 站指揮台九檢(CGC_MDL094:一鍵卡×
組合器×拖曳收件零打字;VIA-Start.bat 雙擊入口)——134 站。
v0192→v0193(批203):+第 133 站歷史回補八檢(VDF_ENG064:2020~
回補;三鐵則=由新到舊年段倒序/增量維護 checkpoint/中斷安全每批
落盤 anti-join 正本零觸碰)——133 站。
v0191→v0192(批201 Mega-Prompt):+第 132 站治理台 UI Matrix 八檢
(CGC_MDL093:四分區×七矩陣×RYG+小字體/自適應/wrap 排版規範+
存證聚合零重測;launch.ps1 非阻塞啟動器同批)——132 站。
v0190→v0191(批199):+第 131 站鉅亨 FactSet 共識融合九檢
(VRN_ENG071:操作員上傳 4,791 行單體收容+統包道輕鑄不卡斷;
marketinfo 三端點實測通;consensus_daily 第三源 CNYES_FACTSET)
——131 站。
v0188→v0189(批194):+第 128 站月營收分析八檢(VDF_ENG063:鉅亨
統包道候選冊誠實探測+分析視圖數學實證+fixture 零殘留;端點候源
P16)+第 129 站 Yahoo 共識八檢(VRN_ENG070:quoteSummary raw 統包道
+consensus_daily 多源共存+同鍵冪等)——129 站。
v0187→v0188(批193):+第 127 站族群聚合因子層八檢(VDF_ENG062:
features_daily×輪動快照成員冊→group_features_daily 37 群;聚合
數學逐檔對合+守恆不變量;boot ⑧b 接線)——127 站。
v0186→v0187(批188):+第 126 站因子庫九檢(VDF_ENG061:Roadmap
Phase 2——prices_canonical 唯一輸入×11 因子目錄冊 SSOT;視窗不足
NULL 誠實;數學實證手算對合;boot ②c 接線)——126 站。
v0185→v0186(批185):+第 125 站 WorkPulse 整合門面九檢(VIA_ENG170:
操作員令「veritaspulse WorkOps 整合為一」——RC/VTR/PULSE 三子域單一
WorkOps 域;VeritasPulse git mv 移域+名冊 23 鍵遷移;hash 定生死去重
5 件讓位 wave4;引用面零破壞檢)——125 站。
v0184→v0185(批181):+第 124 站工具升階梯九檢(SUP_MDL742:
九工序輕→重階梯冊 resolve/ladder/escalate;輕型優先鐵則+升階必附
輕階實敗證據留痕;NETWORK 凍結永回統包正主;probe 誠實缺件不假在;
同批加速橋 100% 全覆蓋 1226/1226 首達)——124 站。
v0183→v0184(批179):+第 123 站引擎簡化稽核八檢(CGC_MDL092:
未使用引擎盤點 297 件功能分群候裁+Phase1 落地[Schema Registry 雙庫
快照+Engine Contract 四介面/Pydantic 封包];AUDIT-ONLY 零改動;
網路工具凍結名單)——123 站。
v0182→v0183(批178):+第 122 站調整後價格層八檢(VDF_ENG060:
factor=adj_close/close 全 OHLC 同乘;正本零觸碰;prices_canonical
正典視圖=下游一切輸入;保序不變量實證;儀表板/共識層 version-forward
切源)——122 站。
v0181→v0182(批176):+第 121 站驗證共識庫八檢(VRN_ENG069:
consensus_daily 雙源[EXTERNAL_ANALYST 195 檔+BROKER_REPORT 件到即入]
+upside 公式冊載+冪等 upsert+consensus_latest 取數視圖;操作員定位令
=庫優先>模板,platform_doctrine 入憲章)——121 站。
v0180→v0181(批175):+第 120 站系統憲章對照八檢(CGC_MDL091:
操作員四系統定義正典冊[原文照錄]×15 能力對照現樹三態=齊 14/部分 1
[talib 誠實]/缺 0;憲章頁 HTML)——120 站。
v0179→v0180(批174):+第 119 站每日觀察摘要八檢(VRN_ENG068:
四系統節[VIA 治理/VDF 鮮度/VAP 三層/VRN 資產]存證庫冊唯讀 join+
ENG066 verify_summary 誠實閘實錄[發明數字必攔]+boot ⑨日更)——119 站。
v0178→v0179(批168):+第 118 站系統同步樞紐八檢(CGC_MDL090:四面
連動[測試/資料/治理/資產]存證唯讀 join+問題台帳六態+開機⑨步同步;
本批並修 S1 常駐 RED:四語法敗現役件照修+CentralGov v0105 收容原件
區判準=VSM 六燈全綠首達)——118 站。
v0177→v0178(批167):+第 117 站儀表板原始版八檢(VAP_ENG009:
操作員 Layout element 定案收容——版面值單源 token 冊 dashboard 節+
Gate Panel/Auto-Fixer 五修留痕/Auto-Optimizer/duckdb 實料嵌入/零 CDN
SVG 車道)——117 站。
v0176→v0177(批165):+第 116 站原始 UI 模板八檢(CGC_MDL089:
token 冊 SSOT[色/字/距/斷點/槽位單源]→CSS 純冊生成→六槽同一模板
[燈/環境/KPI/逐站表/清單/頁尾]→行動優先卡片化;MDL088 橋唯讀重用
=引擎不重造;實測存證 join 零重測)——116 站。
v0175→v0176(批163):+第 115 站五系統測試分頁八檢(CGC_MDL088:
battery×GRID 存證 name join→五系統+OTHER 自動歸屬→同一模板分頁
[環境列/紅黃綠 KPI/逐站多指標/引擎清單];存證連動零重測)——115 站。
v0174→v0175(批162):+第 114 站 VAP 主控台七檢(VAP_ENG008:
VAP 電池[四 selftest+三編譯檢誠實 COMPILE_ONLY]+繪圖規格收割
[模板冊/圖規 40/chartlib AST/TA roster 正主冊]+小字級響應式 UI)——114 站。
v0173→v0174(批158):+第 113 站三語 SSOT×Mind map 九檢(VRN_ENG067:
繁/簡/英讀入[OpenCC 收斂+雙語冊]→關鍵字 SSOT append-only→庫內冊
命中分類[個股/產業/族群/評等/指標/機構]→K 枝掛載→放射樹 mind map
漸進重生;QA 實錘:OpenCC 台→臺正字漂移之冊名雙鍵收斂+EN 小寫頭
吞大寫詞修)——113 站。
v0172→v0173(批157):+第 112 站 NLP 支援樞紐九檢(VRN_ENG066:
全 NLP 工具統一門面支援 Summarizer——ENG064 正主堆疊+finlex 字庫+
ENG062 摘要核心唯讀掛接;enrich 前處理包/verify 摘要誠實閘[發明
數字必攔]/support 端到端;引擎不重造正本零觸碰)——112 站。
v0171→v0172(批156):+第 111 站網路韌性診斷層七檢(SUP_MDL741:
失敗分類器十例真值[限流/WAF/指紋/瞬斷/Referer/付費牆/404]+自適應
節流倍增封頂+主機政策冊+無爬蟲解誠實 NO_WORKAROUND 不假綠)——111 站。
同批:SUP_MDL740 v0108(curl_json bytes 整體 decode 修 UnicodeDecodeError)
+ENG057 探測退避重試由 newest() 自動吃版。
v0170→v0171(批155):+第 109 站產業混合分類冊六檢(VDF_ENG058:
雙所同碼合併+單所限定誠實+VIA-IND 編號+電子/金融/傳產 rollup)
+第 110 站估值 band 引擎七檢(VDF_ENG059:Yahoo 分析師預估解析+
採用 EPS 規則+PE/PB 分位帶+CNYES_FACTSET_PENDING 誠實階梯)——110 站。
同批:SUP_MDL740 v0107(+quoteSummary raw/cnyes 車道)、MethodLab
v0101(+S7 外資×匯率×美元/S8 資金流四線;十檢)由 newest() 自動吃版。
v0169→v0170(批154):+第 107 站成交值回補六檢(VDF_ENG057:
逐股成交金額雙所日別回補;表頭動態對位/先落盤後記帳/TPEX 變體探測
誠實 PENDING)+第 108 站輪動方法論實測室八檢(GRP_ENG041 MethodLab:
六節方法論冊實測;合成真群偵測+滾動分位紀律+誠實資料階梯)——108 站。
v0168→v0169(批152):+第 106 站族群輪動實庫轉接六檢(GRP_ENG040:
v0202 收容包 glob 尾版+238 檔名冊+實庫覆蓋+parquet 欄約+核心
demo 端到端+誠實欄紀律;核心包內 pytest 20 綠另證)——106 站。
同批:VRN_ENG064 v0101(npl_preprocessor 正主件優先載入,九檢)
由 newest() 自動吃版,站名不動。
v0189→v0190(9hh5to 會話):+OCR 超引擎站(TOOL-035 via-ocrsuper
12 檢:車道階梯/四態探測/Regex 認知/計畫建構,零網路 rc0)。
操作員令(2026-08-12):全面測試修正 till all work perfectly。
原則:
  ① 全站安全模式 — 只跑唯讀/dry-run/selftest/文件模式;零 --commit 零網路
  ② 誠實三態 — OK(如預期)/FAIL(異常)/SKIP(環境缺件,誠實註明)
  ③ 期望制 — 每站宣告期望 rc(rc0=須 0;doc=無參印說明 rc∈{0,2};
     env=環境依賴,缺件 rc≠0 記 SKIP 不記 FAIL)
  ④ 存證 — VIA_Reports/selftest_runs/GRID_<ts>.json
v0222→v0223(批347 工作站實錄「FULL 175 站 OK 149 FAIL 24」;操作員令 TEST DEBUG TILL ALL WORKS PERFECT):
  +--refail [GRID_*.json 路徑|省略=最新存證]:只重跑上次 FAIL 站,逐站印全 [FAIL] 行/Traceback/例外末行
   (根因可讀;不再只給尾 2 行)→REFAIL_<stamp>.json(不入 GRID 序列,零重測污染)
  +--only a,b:站名子字串篩選(逐站除錯);--lines N 每站印行數上限(預設 40)
v0223→v0224(批353 操作員問「有導入加速器嗎 為何速度極慢 交疊使用應該很快」):矩陣改平行=真用加速器
  SUP_MDL737.accel_map(執行緒池;例外隔離)跑站(每站本就獨立子進程;工人數 env VIA_GRID_WORKERS,預設
  min(8, CPU);--serial 退原序);完成即印(含序號),結果按站序存證;同型 tally 律不變。
  雲端實測:169 站串行 516s→平行 8 工 277s;平行鎖撞 7 站(duckdb 單寫者)→第二段序跑複判=終態不假紅;瓶頸真相=站內重型 import(torch/cupy/paddle/jieba)與網路等待,
  加速器橋掛在 2263 檔但真呼叫僅 15 檔=「掛橋≠加速」,本版為矩陣首個真用例。
v0224→v0225(批376 操作員令「Final test and user test debug till them work perfectly to insure, they are qualified to become a product」):
  +9 站(批360–375 新引擎/模組入矩陣;產品資格閘 MDL133 以本矩陣 GRID 存證為分母):
  VDF 資料架構九檢(ENG073)/FRED 巨觀 SSOT 十七檢(ENG074)/月營收史深回補九檢(ENG075)/
  主動 ETF×月營收動能八檢(ENG076)/主動 ETF 宇宙八檢(ENG077)/主動 ETF 持股史深八檢(ENG078)/
  四專案完工矩陣七檢(MDL131)/VES 橋六檢(MDL132)/產品資格閘九檢(MDL133)——184 站。
  站名皆帶(批376)可 --only 批376 單跑九站;引擎路徑 newest() 尾版律動態解析,永不寫死版號。
v0225→v0226(批377 操作員令「safely proceed with the 10 parallel procedures … Prevent hydra issues」):+第 185 站十道並行編排九檢(MDL134;
  FixAll 步冊→資源鏈 DAG 單寫者律;Hydra 哨兵 H1–H5)+第 186 站資料本機家九檢(MDL123 v0101 可用律;此前從未入站)——186 站。
v0226→v0227(批381 操作員令「依照已成功地建構布局向上新增;最壞還原成原本規劃;base 只放該有的工具;其他放在 via_core 及 via_ 開頭的環境」):
  +第 187 站環境治理統一引擎 29 檢(CGC_MDL135;批382 +非可選閉包/單寫者律/專屬境覆寫/命名律 rename;全景式分析/uv 快篩行解析/base 該有冊閉包/OCR 家族整包 albucore 案/白名單優先路由/
  Zero-Hydra 分流拓撲/三輪段冊/模擬判讀/未授權零動作/LKGC 晉升律/rollback 原本規劃/四分區矩陣/log JSONL;零網路零環境依賴)——187 站。
v0227→v0228(批383 操作員令「將 river-beam-aurora-acorn 接回整合為一入口;單一入口與總控矩陣 v0700 整合;vap 補充;vdf/vrn 要能跑;vdf 資料庫存入;抓過的不必再抓」):
  +第 188 站單一入口橋八檢(CGC_MDL136 EntryBridge:CmdMatrix 去尾段自動執行/撞名守衛母倉先發先得/家族境 python 解析/燈板/短令冊/一貼即用次序;零網路)
  +第 189 站本機三庫整併十一檢(VDF_ENG079 LocalDbConsolidate:日期正規化/scan 唯讀/dry-run 零寫入/anti-join 只補缺鍵/冪等/coverage/need 缺口/ckpt 交棒/缺 src 誠實 RED;臨時庫)
  +第 190 站 VAP ONE 單檔整合引擎 72 檢(VAP_ENG016 AutoplotOne --selftest;缺車道誠實 SKIP);MDL135 站升 30 檢(+--only-kind 段類過濾)——190 站。
v0228→v0229(批384 操作員令「以此為中央控管將 session_01R2d69oa1AGvnPVwjSUdSv5 整合完畢;vdf vrn 能跑」):
  +第 191 站 VDF/VRN/VAP 能跑閘八檢(CGC_MDL137 RunGate:家族判定/家族境 python 解析/庫探針/家族站篩選/站執行三態/判定律/整合跑報告/紀律;零網路)——191 站。
v0229→v0230(批386 Grok 主控台 VRN 契約接回:「潛在上漲空間(最新 adj close)/目標價/評價方式/基於;n～n+3 稀釋 EPS YoY 主要原因;首頁其餘兩點;報告在除權息前=目標價須除權息調整」):
  +第 192 站研報一題四點文摘十五檢(VRN_ENG080 FourPointDigest:文本規則/YoY 律/除權息因子鏈/K1–K5 契約/quote-or-abstain/novel numbers/落庫冪等/報告日缺/多值不平均;臨時庫)——192 站。
v0230→v0231(批388 操作員令「若能跑 vdf vrn 的 u/i」):
  +第 193 站家族 U/I 再生閘八檢(CGC_MDL138 FamilyUI:動詞白名單/CDN 偵測/頁新鮮判準/資料閘/產生器缺/靜態缺/FAIL=RED/索引頁 file:// 零 CDN/base 先跑退家族境/--no-build;假產生器臨時樹)——193 站。
v0231→v0232(批389 工作站實錄:part3_rest 的 ENG065 協定檔 tw__/gl__ 曾落 local_rest__<stem>;資料家接點 UNLINKED;VRN 控制塔 plotly 未安裝誠實降級):
  第 189 站本機三庫整併十一檢→十三檢(VDF_ENG079:+⑫ ENG065 協定回歸正典表(tw__X→X/gl__X→全球庫 X;零改名;date+ticker 鍵 anti-join 否則 EXCEPT;臨時 parquet 跨庫;台帳鍵含目標表)+⑬ 資料家接點燈)——193 站不變。
v0232→v0233(批390 操作員令「左面板輸入/右面板矩陣;VDF 查詢標的分類細項;起始日個別可改;財報期別年起迄;庫狀況;日交易×籌碼對齊更新清單;VRN 資料夾拖曳/啟動/整體跑況;VAP 簡輸入」):
  +第 194 站輸入主控台八檢(CGC_MDL139 InputConsole:冊載入/參數→argv 白名單/宏觀類別展開/set 個別改動鏡寫/VRN 跑況判準/status 結構/頁面零 CDN/紀律;臨時冊)
  +第 195 站台股日交易×籌碼對齊八檢(VDF_ENG081 UniverseAlign:逐日核對/清單更新 parquet 增量/冪等/status/籌碼落後誠實/庫缺 RED/無冊推定/紀律;臨時庫)——195 站。
v0233→v0234(批391 工作站實錄:via-align update --apply 撞日更鏈單寫者鎖 IOException traceback):
  第 195 站八檢→九檢(VDF_ENG081 +⑨ 讓庫律:鎖短等重試/永鎖誠實 RuntimeError rc3/非鎖 IOException 原樣拋)——195 站不變。
v0234→v0235(批392 操作員令「參數最小化;台股除財報外抓全部;國際資訊右面板勾選;啟動跑一切;VRN TAB2/3/4;起始統一 2023-01-01 整類可改;VAP 規格與圖;VIA Central Console=超詳細系統狀態接棒」):
v0235→v0236(批393 工作站實錄修:ENG081 基準日律(最新價日殘缺=不作清單基準;--asof/--allow-latest)+持鎖者解析(PID→引擎名)+via-bg 指路=十一檢;第 195 站名更新;196 站不變)。
v0236→v0237(批395 操作員令「剛才有卡斷 修正;20 個 PS 加速器;動態進度條及數字」:ENG056 v0102 checkpoint 自庫重建+accel_map 平行工+動態進度條+Ctrl+C 安全=九檢;第 100 站名更新;196 站不變)。
v0237→v0238(批398 操作員令「將 VRN VAL 收個尾吧」):+第 197 站收尾閘八檢(CGC_MDL141_ClosingGate --selftest)——197 站。
v0238→v0239(批400 八流程並進):站名更新——對齊十二檢(ENG081 SQL 側計數)、單一入口九檢(deadends 死路掃描)、儀表板缺料前檢(ENG009 v0107);Deck v0134/Manager v0121 由尾版 glob 自動接;197 站不變。
v0239→v0240(批402 加速/網路雙正典令):站名「統包網路工具十四檢」→「二十檢」(SUP_MDL740 v0112:_aegis 正典優先 VeritasAegisNexus.py、env VIA_AEGIS_PATH、後備 netcore);+「橋塊掃描注入器九檢」站(CGC_MDL124 v0103 --net-callers:只掛真向外擷取檔、vendored/工具本體排除);其餘站零改。
v0240→v0241(批403 六流程並進):站名——財報頁擷取十檢→十五檢(VRN_ENG074 v0102 三方對照:檔名×首頁×財報頁表格,vrn_report_crosscheck 七態)、收尾閘八檢→九檢(CGC_MDL141 v0101 認得對照態,DIVERGE=資訊級不降 verdict);PS 修復總入口 v0101(參數綁定修+看門狗不卡斷)為 ps1,沙盒/CI 無 pwsh 不設站,工作站以 via-psrepair -Selftest 八檢驗。
v0241→v0242(批406 主動 ETF 持股回補通路):站名「主動ETF持股史深八檢」→「十三檢」(ENG078 v0101:discover 自 TWSE OpenAPI 規格真列舉、probe 驗過才升 VERIFIED、parse_holdings JSON/HTML 雙道、DATED 車道真取真解析真落 ENG051 正本表)。
v0242→v0243(批406b 工作站首跑修):站名十三檢→十四檢(ENG078 spec_base 推導;規格 paths 相對 base,漏 /v1 致 candidate 全 404)。
v0243→v0244(批406c 假陽性修):站名十四檢→十八檢(ENG078 判準收緊:反指標否決董監事/外資持股表、列數上限 600、給代號須相關;+撤銷道 曾誤升者重驗不過降回 CANDIDATE)。
v0244→v0245(批407 掛網路工具及爬蟲):站名十八檢→二十二檢(ENG078 v0102 三道升級:http→headers(curl_json/http_bytes+瀏覽器標頭)→scrape(收容雙引擎 PlaywrightBackend,XHR JSON 優先);法遵 DENY 不啟動爬蟲;勝出道寫回車道冊)。
v0245→v0246(批408 爬蟲道可達性修):站名二十二檢→二十三檢(ENG078 v0103 加 gate2_diagnosis()——短令自 批374/375 起把閘二預設成 "YES",而包內法遵只認 I_ACCEPT_RESPONSIBLE_SCRAPING,gate_state() 顯示 open=True 但 verdict 只說「法遵 finding 阻擋」,操作員無從得知差在哪;DENY 訊息改為講白差別且不印原值)。
v0246→v0247(批409 主動 ETF 持股真通路):站名二十三檢→二十六檢(ENG078 v0104 POST 單檔點名車道:代號→投信基金編號→body 渲染→pick 路徑→解析→日期硬閘;群益 PCF 端點實測驗真;車道併入只增不減且冪等);統包網路工具站二十檢→二十一檢(SUP_MDL740 v0113 +post_json)。
v0247→v0248(批410 VRN 自測污染修):站名「首頁文字擷取八檢」→「十五檢(批410 自測零污染)」(ENG072 v0106 自測把 OUTDIR 一併重導進暫存夾;v0105 以前每跑一次自測就在正式產出夾留 fx_report/fx_scan/fx_twocol 六個 fixture,ENG073 隨後當真報告收進正本庫,收尾閘因此把「尚無報告」變成假的「報告 3 · FAIL 2」);收尾閘九檢→十檢(MDL141 v0102 認出 fixture 外流件、不進判定、單列說明並指路清理)。
v0248→v0249(批411 回補重試律 + 批412 金融機構 SSOT 接線):站名「主動ETF持股史深二十六檢」→「二十七檢」(ENG078 v0105:NO_SOURCE 不是終局——發行商已有 VERIFIED DATED 車道時該日格復活重試;過期 PENDING_TODAY 同理;工作站 backfill 回 tried 0 之真因);站名「報告結構化入庫十檢」→「二十三檢」(ENG073 v0106 綁正典金融機構 SSOT:券商/評等正典化 + 分析師姓名擷取)。
v0249→v0250(批413 操作員裁決疊加層):+一站「金融機構疊加層九檢」(VIA_FinancialInstitution_Overlay:拒絕清單先於正典、檔名鍵命名空間、Grok 冊 59 條評等別名接上正典鍵;正典唯讀零觸碰);ENG073 站改指 v0107(綁疊加層)。
v0250→v0251(批415 發行商上市日車道):站名二十七檢→二十八檢(ENG078 v0106:回補深度的真限制不在 --max-days,在上市日解析——主動 ETF 多為新掛牌,yfinance 常查無而全部退到「首快照=下界」,覆蓋窗只剩兩天;改自發行商自家 detail 端點取真上市日,排在 yfinance 之前)。
v0251→v0252(批416 sync 補鍵須及於 VERIFIED 車道):站名二十八檢→二十九檢(ENG078 v0107:批415 幫車道種子加了 listing_api,但 sync 的**硬寫鍵白名單**沒跟著改,工作站 `sync --apply` 於是靜默回「新增 0 · 補鍵 0」,L1b 上市日車道等於沒上線——日格仍 46、listing 仍 LOWER_BOUND、backfill 仍 tried 1。改為自種子逐鍵推導,只排除執行期欄 id/state/note/url/id_map,以後加欄零維護;零動作訊息也改成逐鍵比對後才敢說「種子鍵全在」)。
v0252→v0253(批418 真報告 INPUT FOR TEST):站名「報告結構化入庫二十三檢」→「二十六檢」(ENG073 v0108:年份守衛——「展望2026半導體產業趨勢」的 2026 是年份不是代號,而 2026 恰好也是真實上市代號 聚亨,連逐驗名冊都擋不住;+報告型別分類 個股/產業/大盤晨報/海外/研討會/其他);站名「收尾閘十檢」→「十一檢」(MDL141 v0103:非個股報告不得被判成假紅——MDL139 classify_report 在零 metrics 且零 financial 時判 FAIL,操作員 63 份真報告裡 19 份是產業/晨報/研討會,會整面假紅;有型別欄才改判 DONE_NS,真核對不符照舊 FAIL)。
v0253→v0254(批419 K1 兩道閘):站名「一題四點文摘十二檢」→「十四檢」(ENG080 v0101:目標價合理帶 0.2–5.0——工作站 37 份真文摘中三份的 TP/價比是 0.020/0.019/0.005,那是抽錯的數不是預測;價格基準日律——37 份全部拿 2026-09-07 的價比,但 18 份報告逾 180 天,最舊 1062 天,拿三年後的價算三年前報告的上漲空間是事後看圖。兩道閘都只 flag 不丟棄;順帶把位置式 INSERT 改具名(加欄與位置式天生互斥,批412 同坑))。
v0254→v0255(批419b/c 工作站實錄修):站名「一題四點文摘十四檢」→「十五檢」(ENG080 v0102:批419 的閘會在 K1 印出閘門自己的診斷值——比值 0.020、合理帶界 0.2/5.0——而 novel numbers 把它們當成「報告裡沒有的發明數字」,工作站三份因此 QC 紅、vrn_fourpoint rc=1,整段鏈被自己的診斷訊息判死;診斷值列入 derived 即解);站名「報告結構化入庫二十六檢」→「二十七檢」(ENG073 v0109:`NULL <> ''` 在 SQL 回 NULL 不是 TRUE,加欄前的舊列一律不被計入,印「0/59」時分不出是認不出還是沒欄;改 COALESCE 並分開報 NULL 列數。另加報告型別直方圖與 SSOT 零命中逐項取樣診斷,把靜默的 0 變成有因由的 0)。
v0255→v0256(批419d 工作站實錄修 ×2):站名「報告結構化入庫二十七檢」→「二十八檢」(ENG073 v0110:批419c 我加的零命中診斷在關庫後另開唯讀連線、且傳函式參數 db(預設 None)而非解析後的 dbp,組出「…(反斜線)None」直接 IOException,整個 vrn_structdb rc=1——診斷程式碼把主流程弄掛比沒有診斷更糟;改成關庫前先取樣、不再開第二條連線,新檢 ㉘ 以 stub SSOT 逼出零命中分支真的走一遍)。收尾閘 MDL141 v0104:批418 的守衛太寬,MDL139 的 FAIL_STATES 含 MISSING_SOURCE,而「沒目標價沒價」正是產業/晨報/研討會的**正常態**,於是 22 份非個股全被擋回 FAIL=又走回假紅;真該留 FAIL 的只有 FORMULA_MISMATCH/PARSE_SUSPECT(數字抽出來了而且對不起來)。檢 ⑪ 的 fixture 同時改帶真實狀態——v0103 用空字串,所以檢過了而真跑沒過。
v0256→v0257(批419e 捕捉到卻不顯示等於沒捕捉):站名「報告結構化入庫二十八檢」→「二十九檢」(ENG073 v0111:工作站回「券商正典鍵 0/59 · 金融機構 SSOT 在位」,真實故障是模組載得起來但每次查詢都拋例外——ssot_broker 的 except 把因由存進 _FIN['why'] 之後就沒人看它,因為那個變數只在模組 None 時才印。改成因由一律印,並在零命中診斷加印疊加層 stats() 與資料檔存在與否;新檢 ㉙ 以「模組在位但每次查詢都炸」的 stub 重現工作站的故障形狀)。
v0257→v0258(批419f 正典缺席時疊加層自有的鍵不得一起陪葬):站名「金融機構疊加層九檢」→「十檢」(Overlay v0101:工作站診斷指出 vrn 境無 pydantic → 正典載入失敗 → resolve_broker_filename 把 兆豐→MEGA 查出來後,拿 MEGA 去問正典要中英名,正典缺席就把整個結果丟掉,回「券商正典鍵 0/59」;而 stats() 明明是 filename_keys 16。中英名確實只有正典有,但**鍵**是操作員裁決寫在疊加層 JSON 裡的資料,正典缺席不影響它成立——鍵照回、中英名誠實留空、src 明標「正典缺席;僅鍵無中英名」不冒充 CANON;查無仍是查無、拒絕仍是拒絕。端到端實證:正典缺席下 9 個真檔名命中 8(GF 正確 DENY))。
v0258→v0259(批419g 抽取器詞表比正規化器窄):站名「報告結構化入庫二十九檢」→「三十檢」(ENG073 v0112:工作站券商鍵 0/59→54/59 之後,評等仍 0/59。批413 把 59 條別名加進疊加層,但 RATING_RX 只認 8 個英文字加 7 個中文詞——加碼/續抱/低配/未評等一個都掃不到,字典加了等於白加。第三道改用**疊加層自己的別名**當掃描詞表(Zero-Hydra,不寫第二份),且只掃標題帶/右區與檔名(掃全文會把內文敘述裡的『中立』當評等);計數加「原始評等字串 N 筆」,分得出是抽取階段沒有還是正規化查不到。另補疊加層資料:操作員裁決「增持=加碼」但疊加層只帶「增持」,「加碼」原本靠正典——正典缺席時裁決掉一半,已補進疊加層自帶;「未評等/NR」出自操作員真檔名 瑞基(4171,NR_未評等),疊加層原本只有「未評級」)。
v0259→v0260(批420 操作員規格:檔名拆解律 + 評等全名冊):站名「報告結構化入庫三十檢」→「三十二檢」(ENG073 v0113:新增 tokenize_filename()——中英文標點與**字集轉換處**切開、TRIM 後成為獨立連續的英/中/數單位,四碼數字=台股 TICKER、較長的數字=日期、TT/TW/TWO=市場後綴、名字-KY 也是公司名稱;關鍵在 3014TT 這種沒有標點只有字集轉換的寫法,舊的三支 regex 各管一段誰也切不開。新增 RATING_LIST 評等全名冊(中英文)併入掃描詞表,第一頁符合即可。parse_date/ticker/名冊反查全部改吃拆解器結果)。
v0260→v0261(批421 操作員令「REGISTER AND IMPLEMENT THESE TWO SYSTEMS AS SUPPORTIVE MODULES TO SUPPORT VRN」):+「GLE 全後端統轄橋九檢」(SUP_MDL743:GenericLayoutEngine v2.1.0 四正主掛載、19 後端矩陣誠實、32 支 adapter 優先序、四具名路由+auto/all 落空分支如實、尾版律語意版號對照組、收容缺席=ABSENT)、+「NLP 應用系統統轄橋十一檢」(SUP_MDL744:VIA_NLP_Application_System v1.8.0 收容 68 檔/41 模組、跨兩家族尾版律、__main__ 排除、表格與版面服務實跑、逐格照抄不補值、缺席退空不編表);站名「首頁三法整合擷取十五檢」→「十六檢」(ENG072 v0107 兩收容件改由支援模組統轄)、「報告結構化入庫三十二檢」→「三十三檢」(ENG073 v0114 NLP 掛載由寫死 v1.1.0 改走尾版橋)。
v0261→v0262(批423 操作員令「卡斷 加入20個加速器 不卡斷 動態進度條」):工作站實錄 via-go 停在「① TEST(自測矩陣)」不動。查下來格子這端沒問題(逐站都有 flush),吞掉輸出的是 AllGreen v0100 的 `| Out-String`;但格子這端仍欠三件,補齊:①動態進度條(TTY 走 \r 就地重畫,非 TTY 每 10 站一行,不洗掉站名)②SELFTEST_PROGRESS.json 心跳每站落檔(外部可證明行程還活著;**刻意不叫 GRID_***——既有消費者 VRN_ENG068 三版/CGC_MDL131(按 mtime)/CGC_MDL095/Invoke-VIA-FinishLine 都用 GRID_*.json 取最新證據,叫那個名會被誤讀成證據檔)③Ctrl+C 安全落檔:中斷不是崩潰,已跑完的站寫出來,未跑到的標 NOT_RUN 不冒充 SKIP,rc=130 不冒充成功也不冒充失敗。另開跑先點 20 加速器名(SUP_MDL737→Celeritas;缺席誠實說缺不點假燈)。存證新增 interrupted/done/total/not_run/elapsed_s 五鍵。
v0262→v0263(批424 操作員令「TEST DEBUG OPTIMIZE TEST DEBUG CONSOLIDATE TEST DEBUG TILL THEY WORKS」;沙盒實跑五輪):站名「工具升階梯九檢」→「十檢」(SUP_MDL742 v0101 修自測污染正本)。
v0263→v0264(批425 操作員令「test debug optimize test debug till VRN works, then verify VDF」;沙盒造真 PDF+真價表,實跑五段鏈到 GREEN):站名「報告結構化入庫三十三檢」→「三十四檢」、「財報頁表格十五檢」→「十六檢」、「收尾閘十一檢」→「十二檢」。三支都是同一個病:**參數在、線沒接**——ENG073 main() 是光禿禿的 run()、ENG074 run 分支寫死 run(d, None, ...)、MDL141 main() 不解析 --db。連批423 的 $StageTimeoutSec 一起算,四天內同一模式第四次。
v0269→v0270(批430 工作站 v0106 實跑:志強-KY TP=23.0 其實是「潛在上漲空間 23%」;另操作員說報告沒有自動跳出):站名→「首頁全能引擎二十二檢(批430)」。引擎 v0107:Y1 百分比/倍數/幅度三道剔除(泓德能源 208·神達 128·志強-KY 145 全部回正)、Y2 --open 旗標(零彈窗律:操作員明打才開,VIA_NO_OPEN=1 照樣不開但講清楚為何)、Y3 勘查 tonykuni/VIA-VDF-VRN(test:vrn 36/36 綠,但 nlp-extract.ts 把「目標價」與「潛在上漲」當同一欄且要求緊接冒號→無可複製,本引擎抽取層較前面)。
v0268→v0269(批429 操作員拿 64 份**真 PDF** 跑 v0105 貼回全表,錯得有系統):站名「首頁全能引擎十九檢(批428)」→「首頁全能引擎二十一檢(批429)」,逾時 240→300 秒。引擎 v0106:W1 TP 候選評分(代號回音/量級後綴/前次目標價 五道剔除)、W2 不需現價的台股幣別合理帶、W3 非個股不從內文取代號、W4 離線代號冊(庫不在時的後備,1978 檔快照)、X 六分頁+字級再收一級+欄寬自動。
v0267→v0268(批428 操作員把 64 份真報告放進正典收件夾並貼出檔名,令「先拿裡面的報告實測,跳出四頁式,字小一點比較專業,矩陣報告:1. detailed summary matrix and error matrix 2. basic info 3. financial data」):站名「首頁全能引擎十六檢(批427b)」→「首頁全能引擎十九檢(批428)」,逾時 180→240 秒(檢⑰⑱⑲ 要掛庫取代號冊)。引擎 v0105 加 R 純文字車道、S 四分頁矩陣、T 檔名層六修(64 份真檔名 54 對 10 錯→ 64 對)、U 非個股假綠、V 頁面券商嚴格模式與 TP 缺席二分。
v0266→v0267(批427b 工作站實錄:操作員照我給的路徑打 --dir VIA_Reports\incoming,得到一句沒有資訊量的「[絕] 無可處理檔」):站名「首頁全能引擎十四檢(批427)」→「首頁全能引擎十六檢(批427b)」。引擎 v0104 補 P(路徑是我憑印象給錯的+三種收件失敗壓成同一句+副檔名只認小寫 .pdf)與 Q(無文字層被判假紅)。
v0265→v0266(批427 操作員令「AI-PCB AI-CCL 解決後將引擎一個 PY 檔提供給我」,續令「台新 BROKER 2317 TICKER 鴻海 股票名稱 可透過 TICKER 去 TWSE TPEX 去找證券名稱抓回來對照 也可以 VDF 系統建立的股票清單每日更新去對帳」):站名「首頁全能引擎十二檢(批426)」→「首頁全能引擎十四檢(批427)」。引擎本體走尾版 glob,v0103 落庫即自動接上,不必改路徑;要改的只有檢數。本次照 批425 的教訓先 grep 真字串再改,沒有再憑印象猜站名。
v0264→v0265(批426 操作員上傳 VIA_VRN_FirstPageEngine v0101 + 四支同族件,令「根據上面資訊更新」「整合如果關聯 驗證法」+ 規格三條「百萬兩位小數 / 補不足能力 / 帶前綴的數字·英文數字·民國」):+「首頁全能引擎十二檢」站(v0102)。**同時補正 批425 漏改的一個站名**——當時我把 ENG074 的站名猜成「財報頁表格十五檢」,實際冊上是「財報頁擷取十五檢」,字串不符所以 replace 靜默沒生效,檢數已加到十六卻還印十五。教訓:改站名要先 grep 真字串,不要憑印象寫。
**本輪查出的結構性事實,記在這裡免得下次又被誤判成回歸**:格子裡有四個『自指站』會讀格子自己的存證——五系統測試分頁(MDL088)、測試結果總表(MDL104)、三軌測試矩陣(MDL110)、治理台 UI Matrix(MDL093)。它們在格子**內**跑時,本輪存證還沒落檔,讀到的是**上一輪**的 GRID_*.json,所以永遠慢一拍:修好之後的第一輪它們仍紅,第二輪才轉綠。實測 R4 三站紅、單跑卻綠;R5 三站全綠。MDL093 例外——它斷言綠燈率≥95%,那是後果不是原因,別家紅它就跟著紅。
  第 194 站輸入主控台八檢→十檢(CGC_MDL139 +⑨ 統一起始/整類起始/國際資訊冊增減 +⑩ VRN 三 TAB 判準 VDF 為主/VAP 規格冊);
  +第 196 站接棒狀態台八檢(CGC_MDL140 HandoverConsole:來源冊掃描/分類堆疊/Markdown 匯出/頁零 CDN/缺件誠實/紀律)——196 站。
用法:via-selftest            → 全矩陣(43 站)
      via-selftest --refail  → 只重跑上次紅站+全原因;via-selftest --only 共識,調整後
     via-selftest --fast     → 略過重站(sysman/pipe)
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

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VRN = VIA / "functional modules/VRN"
OUT = VIA / "VIA_Reports" / "selftest_runs"


def newest(pattern: str, root: Path) -> Path | None:
    hits = sorted(root.glob(pattern))
    return hits[-1] if hits else None


def battery(fast: bool):
    py = sys.executable
    B = []

    def add(name, path, args, expect, timeout=180, heavy=False):
        if fast and heavy:
            return
        B.append({"name": name, "path": path, "args": args, "expect": expect, "timeout": timeout})

    add("sysman 三輪協議", newest("CGC_MDL069_SystemManager_v0*.py", HERE), ["--no-open"], "rc0", 900, heavy=True)
    add("衝突哨兵十檢", newest("via_conflict_guard_v0*.py", HERE), ["--selftest"], "rc0", 300)
    add("美國細目擷取八檢", newest("VDF_ENG047_USMacroDetailFetcher*.py", VIA / "functional modules" / "VDF" / "engine"), ["--selftest"], "rc0", 300)
    add("TA 工廠十檢", newest("VDF_ENG048_TAFactory*.py", VIA / "functional modules" / "VDF" / "engine"), ["--selftest"], "rc0", 300)
    add("五日擷取八檢", newest("VDF_ENG049_FiveDayFetch*.py", VIA / "functional modules" / "VDF" / "engine"), ["--selftest"], "rc0", 300)
    add("擷取單引擎八檢", newest("VDF_ENG050_OrderFetch*.py", VIA / "functional modules" / "VDF" / "engine"), ["--selftest"], "rc0", 300)
    add("ETF 持股引擎自測", newest("VDF_ENG051_ActiveTWETF_Holdings*.py", VIA / "functional modules" / "VDF" / "engine"), ["--self-test"], "rc0", 300)
    add("panorama six 六車道", newest("CGC_MDL061_PanoramaSix_v0*.py", HERE), ["--no-open"], "rc0", 300)
    add("xcheck SSOT 對齊", newest("panorama_xcheck_v*.py", VRN), ["--no-pause"], "rc0", 180)
    add("supaudit 導入稽核", newest("CGC_MDL068_SupportImportAudit_v0*.py", HERE), [], "env", 300)
    add("provision 體檢", newest("CGC_MDL062_Provision_v0*.py", HERE), ["--check"], "rc0", 300)
    add("master Console", newest("CGC_MDL059_MasterHub_v0*.py", HERE), ["--no-open"], "rc0", 120)
    add("install 閘 check-only", newest("CGC_MDL056_InstallGate_v0*.py", HERE), ["--check-only"], "rc0", 300)
    add("tidy 整理(dry)", newest("CGC_MDL047_DownloadsOrganizer_v0*.py", HERE), [], "env", 600)
    add("store 落庫(dry)", newest("VRN_ENG050_ContentStore_v0*.py", VRN), [], "env", 120)
    add("reconcile 對帳", newest("VRN_ENG049_ContentReconcile_v0*.py", VRN), [], "env", 120)
    add("pdfcheck 法醫(doc)", newest("VRN_ENG056_PdfForensics_v0*.py", VRN), [], "doc", 60)
    add("docx 引擎(doc)", newest("VRN_ENG052_DocxEngine_v0*.py", VRN), [], "doc", 60)
    add("rescue 救援(doc)", newest("VRN_ENG057_ScanOcrRescue_v0*.py", VRN), [], "doc", 60)
    add("pipeline 輪動證偽", VIA / "supportive modules/VIA_Pipeline/SUP_MDL152_Pipeline.py", ["--demo"], "rc0", 600, heavy=True)
    add("via_io 編碼自檢", VIA / "supportive modules/VIA_Pipeline/via_io.py", ["--selftest"], "rc0", 120)
    add("NetSupport 同意閘", VIA / "supportive modules/VIA_NetSupport.py", [], "rc0", 60)
    sdx = VIA / "functional modules/SuperDocExtractor/PLG_ENG001_SuperExtract.py"
    add("SuperDocExtractor 15檢", sdx, ["selftest"], "rc0", 300)
    add("表格統包車道矩陣", newest("VRN_ENG058_TableOmni_v0*.py", VRN), [], "rc0", 120)
    add("環境計畫快照(offline)", newest("CGC_MDL049_EnvPlan_v0*.py", HERE), ["--offline"], "rc0", 300)
    add("依賴統包 15 檢", newest("CGC_MDL046_DepSuper_v0*.py", HERE), ["--selftest"], "rc0", 300)
    add("表格統包四檢自測", newest("VRN_ENG058_TableOmni_v0*.py", VRN), ["--selftest"], "rc0", 180)
    add("收編管線(dry)", newest("CGC_MDL057_Intake_v0*.py", HERE), [], "env", 300)
    add("契約介面引擎 32 測", VIA / "supportive modules/VIA_ContractEngine_v0200/CGC_MDL002_SelftestEntry.py", [], "env", 300)
    add("留痕包裝器(list)", newest("CGC_MDL044_Cmdlog_v0*.py", HERE), ["--list"], "rc0", 60)
    add("重建計畫自測", newest("CGC_MDL050_EnvRebuild_v0*.py", HERE), ["--selftest"], "rc0", 300)
    add("教訓帳本 10 檢", newest("CGC_MDL058_Lessons_v0*.py", HERE), ["--selftest"], "rc0", 300)
    add("FlowSystem 14 檢", VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_selftest.py", [], "rc0", 300)
    add("文章攝入五檢", newest("CGC_MDL041_ArticleIntake_v0*.py", HERE), ["--selftest"], "rc0", 120)
    add("介面合約(dry)", newest("CGC_MDL054_IfaceContract_v0*.py", HERE), ["--dry"], "rc0", 600)
    add("office 併表橋(dry)", newest("VRN_ENG055_OfficeMerge_v0*.py", VRN), [], "env", 180)
    add("命名冊六檢", newest("CGC_MDL071_Namereg_v0*.py", HERE), ["--selftest"], "rc0", 120)
    add("命名冊(dry)", newest("CGC_MDL071_Namereg_v0*.py", HERE), ["--dry"], "rc0", 300)
    add("產品門面九檢", newest("CGC_MDL072_ProductUi_v0*.py", HERE), ["--selftest"], "rc0", 180)
    add("缺口總攻四檢", newest("VRN_ENG059_GapMultirescue_v0*.py", VRN), ["--selftest"], "rc0", 120)
    add("文字統包六檢", newest("VRN_ENG060_TextOmni_v0*.py", VRN), ["--selftest"], "rc0", 180)
    add("文字統包矩陣", newest("VRN_ENG060_TextOmni_v0*.py", VRN), [], "rc0", 120)
    add("SuperAccel 六檢", VIA / "supportive modules/VIA_SuperAccel_Module.py", ["--selftest"], "rc0", 120)
    add("引擎總目錄四檢", newest("CGC_MDL073_EngineCatalog_v0*.py", HERE), ["--selftest"], "rc0", 180)
    add("三因子吸引力四檢", VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/FLOW_ENG019_FlowAttractiveness.py", ["--selftest"], "rc0", 120)
    add("leadlag 邊四檢", VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/FLOW_ENG020_FlowLeadlag.py", ["--selftest"], "rc0", 120)
    add("VME 核心八檢", VIA / "functional modules/VME/engines/vme_main.py", ["--selftest"], "rc0", 180)
    add("VDF 輸出樞紐七檢", newest("VDF_ENG045_OutputHub_v0*.py", VIA / "functional modules/VDF"), ["--selftest"], "rc0", 300)
    add("字庫知識樹八檢", newest("VRN_ENG063_Lexicon_v0*.py", VRN), ["--selftest"], "rc0", 300)
    FLOWENG = VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/engines"
    add("台灣主動式ETF六檢", FLOWENG / "FLOW_ENG023_FlowTwActiveEtf.py", ["--selftest"], "rc0", 120)
    add("全球ETF流觀察六檢", FLOWENG / "FLOW_ENG021_FlowGlobalEtfFlowscope.py", ["--selftest"], "rc0", 120)
    add("族群三分類指數六檢", FLOWENG / "FLOW_ENG022_FlowGroupTaxonomy.py", ["--selftest"], "rc0", 120)
    add("中央治理台八檢", newest("CGC_MDL075_CentralGov_v0*.py", HERE), ["--selftest"], "rc0", 600)
    add("語法救援七檢", newest("CGC_MDL076_SyntaxRescue_v0*.py", HERE), ["--selftest"], "rc0", 120)
    add("更名引擎七檢", newest("CGC_MDL077_RenameEngine_v0*.py", HERE), ["--selftest"], "rc0", 180)
    add("樹圖譜八檢", newest("CGC_MDL078_TreeAtlas_v0*.py", HERE), ["--selftest"], "rc0", 300)
    add("Matrix 主控台八檢", newest("CGC_MDL079_MatrixConsole_v0*.py", HERE), ["--selftest"], "rc0", 120)
    add("收尾系統七檢", newest("CGC_MDL080_Wrapup_v0*.py", HERE), ["--selftest"], "rc0", 600)
    add("中央參數樞紐七檢", newest("via_params_central_v0*.py", HERE), ["--selftest"], "rc0", 180)
    add("報告摘要批跑七檢", newest("vrn_report_digest_v0*.py", VRN), ["--selftest"], "rc0", 300)
    add("TW01 代碼橋自測", newest("VRN_TW01_TickerBridge_v0*.py", VRN), [], "rc0", 120)
    add("TW02 報告解析自測", newest("VRN_TW02_ReportParser_v0*.py", VRN), [], "rc0", 120)
    add("財務驗算稽核十檢", newest("vrn_finaudit_v0*.py", VRN), ["--selftest"], "rc0", 180)
    add("年度擷取器十檢", newest("vrn_fin_extract_v0*.py", VRN), ["--selftest"], "rc0", 180)
    add("統包網路工具二十一檢(SUP_MDL740;批402 AegisNexus 正典優先)", newest("via_net_unified_v0*.py", HERE.parent / "network"), ["--selftest"], "rc0", 120)
    add("統一加速器六檢(SUP_MDL737)", newest("SUP_MDL737_SuperAccelModule_v*.py", HERE.parent), ["--selftest"], "rc0", 120)
    add("子系統治理器V2八檢(批126)", newest("CGC_MDL081_SubsystemManagerV2_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("雙橋清掃器八檢(批127)", newest("via_bridge_sweeper_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("橋塊掃描注入器九檢(批345/402 --net-callers)", newest("CGC_MDL124_BridgeSweeper_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("自動總跑器六檢(批127)", newest("CGC_MDL082_MasterAutorun_v*.py", HERE), ["--selftest"], "rc0", 600)
    add("中央治理引擎四檢(批132)", newest("CGC_MDL083_CentralGovernment_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("測試金字塔六檢(批142)", newest("CGC_MDL087_TestPyramid_v*.py", HERE), ["--selftest"], "rc0", 600)
    add("治理議題分圈器六檢(批133)", newest("CGC_MDL084_GovTriage_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("議題仲裁器八檢(批133)", newest("CGC_MDL085_IssueArbiter_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("正典裁定器六檢(批133 收官)", newest("CGC_MDL086_CanonArbiter_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("總擷取引擎十檢(批128)", newest("VDF_ENG052_MegaFetch_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("VDF 參數映射器十檢(批134)", newest("VDF_ENG053_ParamEngineMap_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("台股回補工人九檢(批136/401)", newest("VDF_ENG054_TWDailyBackfill_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("總擷取執行器八檢(批137)", newest("VDF_ENG055_OmniFetch_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("籌碼回補引擎九檢(批140/395)", newest("VDF_ENG056_ChipBackfill_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("主動 ETF 持股引擎 self-test(批131)", VIA / "functional modules/VDF/engine/VDF_ENG051_ActiveTWETF_Holdings.py", ["--self-test"], "rc0", 600)
    add("VAP 圖規鎖八檢", newest("vap_spec_guard_v0*.py", VIA / "functional modules/VAP"), ["--selftest"], "rc0", 120)
    add("VAP TA工廠十二檢(批123)", newest("VAP_ENG004_TAFactory_v*.py", VIA / "functional modules/VAP/engine"), ["--selftest"], "rc0", 300)
    add("VAP 模板跑器十檢(批123)", newest("VAP_ENG005_TemplateRunner_v*.py", VIA / "functional modules/VAP/engine"), ["--selftest"], "rc0", 600)
    add("VAP 驗收稽核八檢(批124)", newest("VAP_ENG006_AcceptanceAudit_v*.py", VIA / "functional modules/VAP/engine"), ["--selftest"], "rc0", 600)
    add("寬表刷新器六檢(批145)", newest("VAP_ENG007_RawWideRefresh_v*.py", VIA / "functional modules/VAP/engine"), ["--selftest"], "rc0", 300)
    add("統一U/I套件六檢", newest("via_ui_kit_v0*.py", HERE), ["--selftest"], "rc0", 120)
    add("舊根對帳八檢", newest("via_oldroot_scan_v0*.py", HERE), ["--selftest"], "rc0", 120)
    add("介面自湊十四檢", newest("via_iface_autosync_v0*.py", HERE), ["--selftest"], "rc0", 120)
    add("py 加速啟動器四檢", newest("via_py_celeritas_launcher_v0*.py", HERE), ["--selftest"], "rc0", 120)
    add("VDF 輸入矩陣十三檢", newest("vdf_input_matrix_v0*.py", VIA / "functional modules/VDF"), ["--selftest"], "rc0", 120)
    add("母系統接手十二檢", newest("via_mother_takeover_v0*.py", HERE), ["--selftest"], "rc0", 300)
    add("子系統管理十檢", newest("via_subsys_manager_v0*.py", HERE), ["--selftest"], "rc0", 180)
    add("四點文件摘要引擎自測", VRN / "VIA_Financial_Document_Summarizer_Engine_1.py", ["--self-test"], "rc0", 180)
    add("治理型摘要引擎自測", VRN / "VIA_SummarizerEngine_2.py", ["self-test"], "rc0", 300, heavy=True)
    add("族群流模擬30測試", VIA / "functional modules/GroupIndex/flow_simulation_v0400/run_tests.py", [], "rc0", 300, heavy=True)
    add("VRN 方法核十二檢", newest("vrn_method_kernel_v0*.py", VRN), ["--selftest"], "rc0", 120)
    add("知識堆疊轉接八檢(批141)", newest("VRN_ENG064_KnowledgeStack_v*.py", VRN), ["--selftest"], "rc0", 300)
    add("郵件情報管線八檢(批143)", newest("VRN_ENG065_MailIntel_v*.py", VRN), ["--selftest"], "rc0", 300)
    add("財務字庫十四檢", newest("vrn_finlex_v0*.py", VRN), ["--selftest"], "rc0", 180)
    add("註冊台維運八檢", VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/FLOW_ENG024_FlowRegistryOps.py", ["--selftest"], "rc0", 120)
    add("指揮中心十檢", newest("via_command_center_v0*.py", HERE), ["--selftest"], "rc0", 120)
    add("合約同步 self-test", HERE / "VIA_Central_SSOT_Contract_Sync_Engine.py", ["self-test"], "rc0", 120)
    add("族群量價 self-test", VIA / "functional modules/GroupIndex/engine/VIA_TW_Group_PriceVolume_Volatility_Engine_v0100.py", ["--self-test"], "env", 300)
    add("族群輪動實庫轉接六檢(批152)", newest("GRP_ENG040_GroupingRotationRunner_v*.py", VIA / "functional modules/GroupIndex/engine"), ["--selftest"], "rc0", 600, heavy=True)
    add("成交值回補六檢(批154)", newest("VDF_ENG057_TradingValueBackfill_v*.py", VIA / "functional modules" / "VDF" / "engine"), ["--selftest"], "rc0", 300)
    add("輪動方法論實測室八檢(批154)", newest("GRP_ENG041_RotationMethodLab_v*.py", VIA / "functional modules/GroupIndex/engine"), ["--selftest"], "rc0", 600, heavy=True)
    add("產業混合分類冊六檢(批155)", newest("VDF_ENG058_IndustryUnifiedMap_v*.py", VIA / "functional modules" / "VDF" / "engine"), ["--selftest"], "rc0", 180)
    add("估值 band 引擎七檢(批155)", newest("VDF_ENG059_EstimateBands_v*.py", VIA / "functional modules" / "VDF" / "engine"), ["--selftest"], "rc0", 180)
    add("網路韌性診斷層七檢(批156)", newest("SUP_MDL741_NetResilience_v*.py", VIA / "supportive modules" / "network"), ["--selftest"], "rc0", 120)
    add("NLP 支援樞紐九檢(批157)", newest("VRN_ENG066_NLPSupportHub_v*.py", VRN), ["--selftest"], "rc0", 300)
    add("三語 SSOT×MindMap 九檢(批158)", newest("VRN_ENG067_MindMapSSOT_v*.py", VRN), ["--selftest"], "rc0", 300)
    add("VAP 主控台七檢(批162)", newest("VAP_ENG008_TestConsole_v*.py", VIA / "functional modules/VAP/engine"), ["--selftest"], "rc0", 300)
    add("五系統測試分頁八檢(批163)", newest("CGC_MDL088_SystemTestPages_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("原始 UI 模板八檢(批165)", newest("CGC_MDL089_UIBaseTemplate_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("儀表板原始版八檢(批167)+缺料前檢(批400 v0107)", newest("VAP_ENG009_DashboardUI_v*.py", VIA / "functional modules/VAP/engine"), ["--selftest"], "rc0", 300)
    add("系統同步樞紐八檢(批168)", newest("CGC_MDL090_SystemHub_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("每日觀察摘要八檢(批174)", newest("VRN_ENG068_DailyBrief_v*.py", VRN), ["--selftest"], "rc0", 300)
    add("系統憲章對照八檢(批175)", newest("CGC_MDL091_CharterAudit_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("驗證共識庫八檢(批176)", newest("VRN_ENG069_ConsensusDB_v*.py", VRN), ["--selftest"], "rc0", 300)
    add("調整後價格層八檢(批178)", newest("VDF_ENG060_AdjPriceLayer_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 600)
    add("引擎簡化稽核八檢(批179)", newest("CGC_MDL092_ConsolidationAudit_v*.py", HERE), ["--selftest"], "rc0", 600)
    add("工具升階梯十檢(批181/424)", newest("SUP_MDL742_ToolLadder_v*.py", VIA / "supportive modules" / "network"), ["--selftest"], "rc0", 300)
    add("GLE 全後端統轄橋九檢(批421)", newest("SUP_MDL743_GenericLayoutHub_v*.py", VIA / "supportive modules" / "70_VRN_Rules"), ["--selftest"], "rc0", 300)
    add("NLP 應用系統統轄橋十一檢(批421)", newest("SUP_MDL744_NLPApplicationHub_v*.py", VIA / "supportive modules" / "70_VRN_Rules"), ["--selftest"], "rc0", 300)
    add("WorkPulse 整合門面九檢(批185)", newest("VIA_ENG170_WorkPulseUnified_v*.py", VIA / "functional modules/WorkOps"), ["--selftest"], "rc0", 300)
    add("因子庫九檢(批188)", newest("VDF_ENG061_FeatureStore_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 600)
    add("族群聚合因子層八檢(批193)", newest("VDF_ENG062_GroupFeatureLayer_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 600)
    add("月營收分析九檢(批194)", newest("VDF_ENG063_MonthlyRevenue_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("Yahoo 共識八檢(批194)", newest("VRN_ENG070_YahooConsensus_v*.py", VRN), ["--selftest"], "rc0", 300)
    add("鉅亨 FactSet 共識九檢(批199)", newest("VRN_ENG071_CnyesFusion_v*.py", VRN), ["--selftest"], "rc0", 300)
    add("治理台 UI Matrix 八檢(批201)", newest("CGC_MDL093_GovernanceMatrix_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("歷史回補八檢(批203)", newest("VDF_ENG064_HistoryBackfill_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("全景同步狀態台八檢(批218)", newest("CGC_MDL096_SyncStatus_v*.py", VIA / "supportive modules/registry"), ["--selftest"], "rc0", 120)
    add("資料庫合併匯入八檢(批216)", newest("VDF_ENG065_DbImport_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 120)
    add("使用者介面總入口八檢(批222)", newest("CGC_MDL097_PortalUI_v*.py", VIA / "supportive modules/registry"), ["--selftest"], "rc0", 120)
    add("全球宇宙擷取八檢(批226)", newest("VDF_ENG066_GlobalUniverse_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 120)
    add("資料庫目錄台八檢(批226)", newest("CGC_MDL098_DataCatalog_v*.py", VIA / "supportive modules/registry"), ["--selftest"], "rc0", 180)
    add("全球市場觀測八檢(批227)", newest("CGC_MDL099_GlobalMarkets_v*.py", VIA / "supportive modules/registry"), ["--selftest"], "rc0", 120)
    add("首頁文字擷取十五檢(批235;批410 自測零污染)", newest("VRN_ENG072_FirstPageText_v*.py", VIA / "functional modules/VRN"), ["--selftest"], "rc0", 120)
    add("首頁全能引擎二十二檢(批430)", newest("VIA_VRN_FirstPageEngine_v*.py", VIA / "functional modules/VRN"), ["--selftest"], "rc0", 300)
    add("報告結構化入庫三十四檢(批237;批412 SSOT;批418 年份守衛+報告型別)", newest("VRN_ENG073_ReportStructuredDB_v*.py", VIA / "functional modules/VRN"), ["--selftest"], "rc0", 120)
    add("金融機構疊加層十檢(批413 操作員裁決;批419f 正典缺席鍵不陪葬)", newest("VIA_FinancialInstitution_Overlay_v*.py", VIA / "supportive modules/ssot"), ["--selftest"], "rc0", 120)
    add("券商報告卡八檢(批241)", newest("CGC_MDL100_ReportCards_v*.py", VIA / "supportive modules/registry"), ["--selftest"], "rc0", 120)
    add("財報頁擷取十六檢(批241/403 三方對照;批425 --db 接線)", newest("VRN_ENG074_FinancialPages_v*.py", VIA / "functional modules/VRN"), ["--selftest"], "rc0", 120)
    add("共識增益橋十檢(批243)", newest("VDF_ENG067_ConsensusEnrichment_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 180)
    add("PS AST 修正引擎十檢(批244)", newest("CGC_MDL101_PSAstRepair_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("圖庫 SSOT 橋十檢(批247)", newest("VAP_ENG010_ChartLibrarySSOT_v*.py", VIA / "functional modules/VAP/engine"), ["--selftest"], "rc0", 120)
    add("文件轉MD引擎十檢(批249)", newest("VRN_ENG075_DocToMarkdown_v*.py", VIA / "functional modules/VRN"), ["--selftest"], "rc0", 240)
    add("指令整合冊六檢(批249)", newest("CGC_MDL102_CommandRoster_v*.py", HERE), ["--selftest"], "rc0", 120)
    add("TPN 模板冊十二檢(批250)", newest("VAP_ENG011_TemplateRegistry_v*.py", VIA / "functional modules/VAP/engine"), ["--selftest"], "rc0", 120)
    add("抽取鏈迴歸閘八檢(批251)", newest("VRN_ENG076_RegressionGate_v*.py", VIA / "functional modules/VRN"), ["--selftest"], "rc0", 180)
    add("治理存圖八檢(批251)", newest("VAP_ENG012_GovernedImageStore_v*.py", VIA / "functional modules/VAP/engine"), ["--selftest"], "rc0", 120)
    add("加速器覆蓋十檢(批255)", newest("CGC_MDL103_AccelCoverage_v*.py", HERE), ["--selftest"], "rc0", 240)
    add("VOFIE 全格式橋八檢(批256)", newest("VRN_ENG077_OmniFormatBridge_v*.py", VIA / "functional modules/VRN"), ["--selftest"], "rc0", 300)
    add("測試結果總表六檢(批257)", newest("CGC_MDL104_TestResultsHub_v*.py", HERE), ["--selftest"], "rc0", 180)
    add("治理主控台六檢(批258)", newest("CGC_MDL105_GovernanceConsole_v*.py", HERE), ["--selftest"], "rc0", 120)
    add("市場分析引擎自測(批259 合流)", newest("VAP_ENG013_MarketAnalytics_v*.py", VIA / "functional modules/VAP/engine"), ["--selftest"], "rc0", 300)
    add("主動ETF×共識分析自測(批264)", newest("VDF_ENG068_ETFConsensusAnalysis_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("月營收×共識分析自測(批264)", newest("VDF_ENG069_RevenueConsensusAnalysis_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("Prompt 儲存管理自測(批265)", newest("CGC_MDL109_PromptManager_v*.py", HERE), ["--selftest"], "rc0", 180)
    add("三軌測試矩陣自測(批267)", newest("CGC_MDL110_TriTestMatrix_v*.py", HERE), ["--selftest"], "rc0", 180)
    add("統一UI元件盤點自測(批278)", newest("CGC_MDL111_UIComponentRoster_v*.py", HERE), ["--selftest"], "rc0", 180)
    add("標準儀表板模板自測(批279)", newest("VAP_ENG014_StdDashboardTemplate_v*.py", VIA / "functional modules/VAP/engine"), ["--selftest"], "rc0", 300)
    add("系統現況總圖自測(批280)", newest("CGC_MDL112_SystemAtlas_v*.py", HERE), ["--selftest"], "rc0", 180)
    add("總系統管理器自測(批281)", newest("VIA_SYSTEM_MANAGER_v*.py", VIA), ["--selftest"], "rc0", 180)
    add("NLP OneEngine 橋自測(批283)", newest("VRN_ENG078_NLPOneBridge_v*.py", VIA / "functional modules/VRN"), ["--selftest"], "rc0", 240)
    add("統一編號註冊器自測(批287)", newest("CGC_MDL113_UnifiedRegistry_v*.py", HERE), ["--selftest"], "rc0", 180)
    add("AIO 指揮中心橋自測(批288)", newest("CGC_MDL114_CommandCenterBridge_v*.py", HERE), ["--selftest"], "rc0", 570)
    add("中央SSOT Regex治理自測(批296)", newest("CGC_MDL115_SSOTRegexDict_v*.py", HERE), ["--selftest"], "rc0", 180)
    add("Seaborn/Plotly 雙後端自測(批297 補站)", newest("VAP_ENG003_AutoplotSeabornPlotly_v*.py", VIA / "functional modules/VAP/engine"), ["selftest"], "rc0", 300)
    add("擷取矩陣冊八檢(批297 補站)", VIA / "functional modules/VDF/engine/VDF_ENG046_FetchMatrixRegistry.py", ["--selftest"], "rc0", 180)
    add("Gov 主控台自測(批259 合流)", newest("CGC_MDL106_GovConsole_v*.py", HERE), ["--selftest"], "rc0", 180)
    add("UI 元件轉碼管理自測(批259 合流)", newest("CGC_MDL107_UISpecManager_v*.py", HERE), ["--selftest"], "rc0", 180)
    add("對話轉文自測(批259 合流)", newest("CGC_MDL108_ChatToDoc_v*.py", HERE), ["--selftest"], "rc0", 180)
    add("指揮台九檢(批204)", newest("CGC_MDL094_CommandDeck_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("執行橋八檢(批208)", newest("CGC_MDL095_DeckServer_v*.py", HERE), ["--selftest"], "rc0", 300)
    B.append({"name": "ChipWar 引擎編譯檢(零執行)", "path": "PYCODE", "args": [], "expect": "rc0",
              "timeout": 180, "pycode": (
                  "import py_compile,sys\n"
                  "from pathlib import Path\n"
                  "root=Path(r'" + str(VIA / "functional modules/ChipWar/engines") + "')\n"
                  "bad=n=0\n"
                  "for p in sorted(root.glob('*.py')):\n"
                  "    if '_sha' in p.stem: continue\n"
                  "    n+=1\n"
                  "    try: py_compile.compile(str(p),doraise=True)\n"
                  "    except Exception as e: bad+=1; print(f'[FAIL] {p.name}: {str(e)[:80]}')\n"
                  "print(f'[計] ChipWar 編譯 {n} 件 · 壞 {bad}(_sha 鏡像/檢疫夾除外)')\n"
                  "sys.exit(1 if bad else 0)\n")})
    add("OCR 超引擎 12 檢(9hh5to)", newest("via_ocr_super_v0*.py", HERE), ["--selftest"], "rc0", 300)
    # 批376:產品化最終測——批360–375 新引擎/模組入矩陣(尾版律 newest;皆 --selftest rc0)
    add("VDF 資料架構九檢(批376)", newest("VDF_ENG073_DataArchitecture_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("FRED 巨觀 SSOT 十七檢(批376)", newest("VDF_ENG074_FredMacroSSOT_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("月營收史深回補九檢(批376)", newest("VDF_ENG075_MonthlyRevenueBackfill_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("主動ETF×月營收動能八檢(批376)", newest("VDF_ENG076_ETFRevenueMomentum_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("主動ETF宇宙八檢(批376)", newest("VDF_ENG077_ActiveETFUniverse_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("主動ETF持股史深二十九檢(批376/406×4/407-409/411 重試律/415 上市日車道/416 sync 補鍵)", newest("VDF_ENG078_ActiveETFHoldingsHistory_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("四專案完工矩陣七檢(批376)", newest("CGC_MDL131_ProjectCompletion_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("VES 橋六檢(批376)", newest("CGC_MDL132_VesBridge_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("產品資格閘九檢(批376)", newest("CGC_MDL133_ProductGate_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("十道並行編排九檢(批377)", newest("CGC_MDL134_ParallelLanes_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("資料本機家九檢(批377)", newest("CGC_MDL123_DataHome_v0*.py", HERE), ["--selftest"], "rc0", 300)
    add("環境治理統一引擎 31 檢(批381–385)", newest("CGC_MDL135_EnvGovernance_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("單一入口橋九檢(批383)(批400 deadends)", newest("CGC_MDL136_EntryBridge_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("本機三庫整併十三檢(批383/389)", newest("VDF_ENG079_LocalDbConsolidate_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("VAP ONE 單檔整合引擎 72 檢(批383)", newest("VAP_ENG016_AutoplotOne_v*.py", VIA / "functional modules/VAP/engine"), ["--selftest"], "rc0", 300)
    add("VDF/VRN/VAP 能跑閘十檢(批384/387)", newest("CGC_MDL137_RunGate_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("研報一題四點文摘十五檢(批386;批419 TP 合理帶+基準日律)", newest("VRN_ENG080_FourPointDigest_v*.py", VRN), ["--selftest"], "rc0", 300)
    add("家族 U/I 再生閘八檢(批388)", newest("CGC_MDL138_FamilyUI_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("輸入主控台十檢(批390/392)", newest("CGC_MDL139_InputConsole_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("台股日交易×籌碼對齊十二檢(批390/391/393/400)", newest("VDF_ENG081_UniverseAlign_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("接棒狀態台八檢(批392)", newest("CGC_MDL140_HandoverConsole_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("收尾閘十二檢(批398/403 三方對照;批410 fixture;批418 非個股不假紅)", newest("CGC_MDL141_ClosingGate_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("selftest grid(自指:文件)", None, [], "doc", 10)  # 佔位:自身以 --fast 遞迴屬禁,列 SKIP
    return B


# ===== 批423:不卡斷三件套(操作員令「卡斷 加入20個加速器 不卡斷 動態進度條」)=====
# 根因(工作站實錄):via-go 卡在「── ① TEST(自測矩陣)──」不動。
# 格子這一端其實一直在印(逐站 flush),真正吞掉輸出的是 AllGreen v0100 的
#   $out = & $PY @Argv 2>&1 | Out-String       ← 緩衝到子行程結束才吐
# 200 站序列等於整段畫面空白 = 看起來就是死機。批419e 同一個病的 PowerShell 版:
# **捕捉到卻不顯示,等於沒捕捉。**
# 這一批在格子側補三件,讓「還活著」這件事在任何管道都看得見:
#   ①動態進度條(TTY 走 \r 就地重畫;非 TTY 走節流換行,不洗版)
#   ②PROGRESS.json 心跳(每站落檔=外部 via-bg / AllGreen 可證明它在動)
#   ③Ctrl+C 安全落檔(中斷不是崩潰:寫出已完成的部分證據,誠實回 rc=130)
_TTY = bool(getattr(sys.stdout, "isatty", lambda: False)())
# 心跳檔名**刻意不叫 GRID_***:既有消費者都用 sorted(OUT.glob("GRID_*.json"))[-1]
# 或按 mtime 取「最新證據」——VRN_ENG068_DailyBrief(三版)、CGC_MDL131_ProjectCompletion
# (按 mtime,而心跳永遠最後寫=必中)、CGC_MDL095_DeckServer、Invoke-VIA-FinishLine。
# 叫 GRID_PROGRESS.json 會讓它們把心跳當成證據檔讀(字母序 GRID_P > GRID_2)。
# 教訓:新增產出檔之前先查誰在 glob 同一個樣式。
PROG_P = OUT / "SELFTEST_PROGRESS.json"


def accel_lamp() -> str:
    """20 加速器真點名(SUP_MDL737 → Celeritas)。缺席=誠實說缺,不點假燈。"""
    try:
        sys.path.insert(0, str(VIA / "supportive modules"))
        import importlib
        _m = importlib.import_module("SUP_MDL737_SuperAccelModule_v0104")
    except Exception:
        try:
            hits = sorted((VIA / "supportive modules").glob("SUP_MDL737_SuperAccelModule_v*.py"))
            if not hits:
                return "加速器:SUP_MDL737 缺檔(誠實;不影響跑,只是沒加速)"
            import importlib.util
            spec = importlib.util.spec_from_file_location("via_accel_dyn", hits[-1])
            _m = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = _m
            spec.loader.exec_module(_m)
        except Exception as exc:
            return f"加速器:載入失敗 {type(exc).__name__}(誠實;不影響跑)"
    try:
        a = _m.activate(apply_limits=True)
    except Exception as exc:
        return f"加速器:activate 例外 {type(exc).__name__}(誠實)"
    if not a.get("celeritas"):
        return f"加速器:Celeritas 未載入 — {a.get('err') or '無因由'}(誠實;退無加速)"
    return (f"加速器:Celeritas OK · lib {a['libs_available']}/{a['libs_total']}"
            f" · 能力 {a['capability_real']}/{a['capability_total']}"
            f" · 執行緒預算 {a.get('thread_budget')} · 模式 {a.get('mode')}"
            + (f" · 缺 {len(a['missing'])} 支(列名不假在)" if a.get("missing") else ""))


def _bar(done, total, t0, ok, fail, skip, cur="", width=26) -> None:
    """動態進度條。TTY 就地重畫;非 TTY(被 AllGreen 導向檔案)節流換行印,
    否則 200 行進度條會把真正的站名洗掉。"""
    frac = done / max(1, total)
    el = time.time() - t0
    eta = int(el / done * (total - done)) if done else 0
    s = (f"  [{'█' * int(width * frac)}{'░' * (width - int(width * frac))}]"
         f" {done}/{total} {frac * 100:4.1f}% · 經過 {int(el)}s · 剩約 {eta}s"
         f" · OK {ok} FAIL {fail} SKIP {skip}")
    if _TTY:
        print("\r" + s + " " * 8, end="", flush=True)
    elif done == total or done % 10 == 0:      # 非 TTY:每 10 站一行=看得到在動又不洗版
        print(s + (f" · 正在 {cur[:40]}" if cur else ""), flush=True)


def _progress_write(done, total, t0, ok, fail, skip, cur="", state="RUNNING") -> None:
    """心跳落檔。外部(via-bg / AllGreen 輪詢)靠它證明行程還活著,
    不必去猜『沒輸出』是卡死還是在跑。"""
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        PROG_P.write_text(json.dumps({
            "schema": "VIA.SelftestGrid.progress.v1", "state": state,
            "done": done, "total": total, "ok": ok, "fail": fail, "skip": skip,
            "elapsed_s": round(time.time() - t0, 1),
            "eta_s": int((time.time() - t0) / done * (total - done)) if done else None,
            "current": cur, "pid": os.getpid(),
            "heartbeat": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass                                    # 心跳失敗不得拖垮主流程(批419d 教訓)


def _tally(results):
    return (sum(1 for r in results if r and r["state"] == "OK"),
            sum(1 for r in results if r and r["state"] == "FAIL"),
            sum(1 for r in results if r and r["state"] == "SKIP"))


def run_one(b):
    if b["path"] is None or (b["path"] != "PYCODE" and not Path(b["path"]).exists()):
        return {"name": b["name"], "state": "SKIP", "note": "引擎缺/自指佔位(誠實)", "secs": 0}
    t0 = time.time()
    try:
        if b["path"] == "PYCODE":  # pycode 站型:標準庫內聯檢(零外部檔)
            argv = [sys.executable, "-c", b["pycode"]]
            cwd = str(VIA)
        else:
            argv = [sys.executable, str(b["path"]), *b["args"]]
            cwd = str(Path(b["path"]).parent)
        r = subprocess.run(argv, capture_output=True,
                           text=True, timeout=b["timeout"], stdin=subprocess.DEVNULL,
                           cwd=cwd)
        secs = round(time.time() - t0, 1)
        tail = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()][-2:]
        if b["expect"] == "rc0":
            state = "OK" if r.returncode == 0 else "FAIL"
        elif b["expect"] == "doc":
            state = "OK" if r.returncode in (0, 2) else "FAIL"
        else:  # env
            state = "OK" if r.returncode == 0 else "SKIP"
        note = " / ".join(t[:80] for t in tail)
        if state == "SKIP":
            note = "環境缺件(誠實):" + note
        return {"name": b["name"], "state": state, "rc": r.returncode, "secs": secs, "note": note}
    except subprocess.TimeoutExpired:
        return {"name": b["name"], "state": "FAIL", "rc": "TIMEOUT", "secs": b["timeout"], "note": "逾時"}
    except Exception as exc:
        return {"name": b["name"], "state": "FAIL", "rc": type(exc).__name__, "secs": 0, "note": str(exc)[:80]}


def _detail(b, max_lines: int = 40) -> str:
    """批347:單站全原因(重跑一次;印 [FAIL]/Traceback/Error/例外 行+末 6 行;上限 max_lines)"""
    if b["path"] is None or (b["path"] != "PYCODE" and not Path(b["path"]).exists()):
        return "(引擎缺/佔位)"
    argv = [sys.executable, "-c", b["pycode"]] if b["path"] == "PYCODE" else [sys.executable, str(b["path"]), *b["args"]]
    cwd = str(VIA) if b["path"] == "PYCODE" else str(Path(b["path"]).parent)
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=b["timeout"], stdin=subprocess.DEVNULL, cwd=cwd,
                           env={**os.environ, "PYTHONUTF8": "1", "PYTHONWARNINGS": "ignore"})
        lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    except subprocess.TimeoutExpired:
        return f"逾時 {b['timeout']}s"
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    key = [l for l in lines if ("[FAIL" in l or "Traceback" in l or "Error" in l or "錯誤" in l or "計]" in l)]
    tail = lines[-6:]
    seen, out = set(), []
    for l in key + tail:
        if l not in seen:
            seen.add(l)
            out.append(l[:220])
    return "\n".join(out[:max_lines]) + (f"\n… 共 {len(lines)} 行" if len(lines) > max_lines else "")


def _refail_targets(a: list) -> tuple:
    """--refail [json]:讀 GRID 存證取 FAIL 站名;--only a,b:子字串"""
    names = set()
    if "--refail" in a:
        i = a.index("--refail")
        p = Path(a[i + 1]) if i + 1 < len(a) and not a[i + 1].startswith("--") else None
        if p is None:
            hits = sorted(OUT.glob("GRID_*.json"))
            p = hits[-1] if hits else None
        if p and p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            names |= {r["name"] for r in d.get("results", []) if r.get("state") == "FAIL"}
            print(f"  [refail] 來源 {p.name} · 紅站 {len(names)}")
        else:
            print("  [refail] 無 GRID 存證(先跑 via-selftest)")
    subs = []
    if "--only" in a:
        subs = [x for x in a[a.index("--only") + 1].split(",") if x]
    return names, subs


def main() -> int:
    a = sys.argv[1:]
    fast = "--fast" in a
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    B = battery(fast)
    if "--refail" in a or "--only" in a:  # 批347:逐站除錯模式
        names, subs = _refail_targets(a)
        max_lines = int(a[a.index("--lines") + 1]) if "--lines" in a and a.index("--lines") + 1 < len(a) else 40
        sel = [b for b in B if b["name"] in names or any(sb in b["name"] for sb in subs)]
        print(f"=== 逐站除錯(v0265)· {len(sel)} 站 · 全原因 ===")
        results = []
        for b in sel:
            r = run_one(b)
            r["detail"] = _detail(b, max_lines) if r["state"] == "FAIL" else ""
            results.append(r)
            mark = {"OK": "OK  ", "FAIL": "FAIL", "SKIP": "SKIP"}[r["state"]]
            print(f"  [{mark}] {r['name']} · {r['secs']}s")
            if r["detail"]:
                for l in r["detail"].splitlines():
                    print("      | " + l)
        n_ok = sum(1 for r in results if r["state"] == "OK")
        n_fail = sum(1 for r in results if r["state"] == "FAIL")
        OUT.mkdir(parents=True, exist_ok=True)
        ev = OUT / f"REFAIL_{ts}.json"
        ev.write_text(json.dumps({"schema": "VIA.SelftestGrid.refail.v1", "ts": ts, "n": len(sel), "ok": n_ok, "fail": n_fail,
                                  "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  [計] 重跑 {len(sel)} 站 · OK {n_ok} · FAIL {n_fail}(轉綠 {n_ok})· 存證 {ev.name}")
        return 0 if n_fail == 0 else 1
    print(f"=== 全面自測矩陣 v0265 · {len(B)} 站 · {'FAST' if fast else 'FULL'} · 全安全模式(零 commit 零網路)===")
    print(f"  [{accel_lamp()}]", flush=True)          # 批423:20 加速器真點名(缺席誠實說缺)
    results = [None] * len(B)
    workers = 1 if "--serial" in a else max(1, int(os.environ.get("VIA_GRID_WORKERS") or min(8, os.cpu_count() or 4)))
    t_grid = time.time()
    done_n = [0]
    print(f"  [進度] 動態進度條{'(TTY 就地重畫)' if _TTY else '(非 TTY:每 10 站一行)'}"
          f" · 心跳 {PROG_P.name}(每站落檔;外部可證明還活著)· Ctrl+C 安全落檔", flush=True)
    _progress_write(0, len(B), t_grid, 0, 0, 0, "啟動", "RUNNING")

    def _job(ib):
        i, b = ib
        r = run_one(b)
        results[i] = r
        done_n[0] += 1
        mark = {"OK": "OK  ", "FAIL": "FAIL", "SKIP": "SKIP"}[r["state"]]
        if _TTY:
            print("\r" + " " * 78 + "\r", end="")     # 清掉進度條那一行再印站名
        print(f"  [{mark}] {r['name']} · {r['secs']}s · {r.get('note', '')[:96]}"
              + (f"  ({done_n[0]}/{len(B)} · {int(time.time() - t_grid)}s)" if workers > 1 else ""), flush=True)
        _ok, _fa, _sk = _tally(results)
        _bar(done_n[0], len(B), t_grid, _ok, _fa, _sk, b["name"])
        _progress_write(done_n[0], len(B), t_grid, _ok, _fa, _sk, b["name"], "RUNNING")
        return True

    interrupted = False
    try:
      if workers > 1:
        print(f"  [平行] 工人 {workers}(SUP_MDL737 accel_map;--serial 退原序)", flush=True)
        try:
            import VIA_SuperAccel_Module as _A
            _A.accel_map(_job, list(enumerate(B)), workers=workers)
        except KeyboardInterrupt:
            raise
        except Exception:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=workers) as ex:
                list(ex.map(_job, list(enumerate(B))))
        results = [r if r else {"name": b["name"], "state": "FAIL", "rc": "NORESULT", "secs": 0, "note": "平行工人無回(誠實)"} for r, b in zip(results, B)]
        # 第二段(讓庫律):平行敗站序跑一次=排除 duckdb 單寫者鎖/產物半寫之假紅;終態取序跑;note 留「平行敗→序跑」
        redo = [i for i, r in enumerate(results) if r["state"] == "FAIL"]
        if redo:
            print(f"  [第二段] 平行敗 {len(redo)} 站→序跑複判(讓庫律;鎖撞=假紅)", flush=True)
            for i in redo:
                r2 = run_one(B[i])
                r2["note"] = ("平行敗→序跑 " + ("轉綠" if r2["state"] == "OK" else "仍紅") + ":") + r2.get("note", "")
                results[i] = r2
                mark = {"OK": "OK  ", "FAIL": "FAIL", "SKIP": "SKIP"}[r2["state"]]
                print(f"  [{mark}] {r2['name']} · {r2['secs']}s · {r2['note'][:96]}", flush=True)
      else:
        for i, b in enumerate(B):
            _job((i, b))
    except KeyboardInterrupt:
        # 批423:中斷不是崩潰。已跑完的站是真證據,寫出來再走;
        # 沒跑到的誠實標 NOT_RUN,不拿空白冒充 SKIP。
        interrupted = True
        if _TTY:
            print()
        print(f"\n  [中斷] Ctrl+C —— 已完成 {done_n[0]}/{len(B)} 站,"
              f"落檔已完成部分(未跑到的標 NOT_RUN,不冒充 SKIP)", flush=True)
    results = [r if r else {"name": b["name"], "state": "NOT_RUN", "rc": "INTERRUPTED" if interrupted else "NORESULT",
                            "secs": 0, "note": "中斷時尚未跑到(誠實)" if interrupted else "無回(誠實)"}
               for r, b in zip(results, B)]
    n_ok, n_fail, n_skip = _tally(results)
    n_nr = sum(1 for r in results if r["state"] == "NOT_RUN")
    if _TTY:
        _bar(done_n[0], len(B), t_grid, n_ok, n_fail, n_skip)
        print()
    OUT.mkdir(parents=True, exist_ok=True)
    ev = OUT / f"GRID_{ts}.json"
    ev.write_text(json.dumps({"schema": "VIA.SelftestGrid.v1", "ts": ts, "fast": fast,
                              "interrupted": interrupted, "done": done_n[0], "total": len(B),
                              "ok": n_ok, "fail": n_fail, "skip": n_skip, "not_run": n_nr,
                              "elapsed_s": round(time.time() - t_grid, 1), "results": results},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    _progress_write(done_n[0], len(B), t_grid, n_ok, n_fail, n_skip,
                    "", "INTERRUPTED" if interrupted else "DONE")
    print(f"  [計] OK {n_ok} · FAIL {n_fail} · SKIP {n_skip}"
          + (f" · NOT_RUN {n_nr}(中斷)" if n_nr else "")
          + f"(誠實三態)· {int(time.time() - t_grid)}s · 存證 {ev.name}")
    if interrupted:
        return 130                              # 128+SIGINT:中斷不冒充成功也不冒充失敗
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
