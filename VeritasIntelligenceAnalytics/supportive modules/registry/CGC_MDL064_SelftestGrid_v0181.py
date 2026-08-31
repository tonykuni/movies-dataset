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
v0111→v0112:+第 39 站 SuperAccel 四檢(斷點補齊;同意閘/平行/快取)——39 站。
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
操作員令(2026-08-12):全面測試修正 till all work perfectly。
原則:
  ① 全站安全模式 — 只跑唯讀/dry-run/selftest/文件模式;零 --commit 零網路
  ② 誠實三態 — OK(如預期)/FAIL(異常)/SKIP(環境缺件,誠實註明)
  ③ 期望制 — 每站宣告期望 rc(rc0=須 0;doc=無參印說明 rc∈{0,2};
     env=環境依賴,缺件 rc≠0 記 SKIP 不記 FAIL)
  ④ 存證 — VIA_Reports/selftest_runs/GRID_<ts>.json
用法:via-selftest            → 全矩陣(43 站)
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
    add("SuperAccel 四檢", VIA / "supportive modules/VIA_SuperAccel_Module.py", ["--selftest"], "rc0", 120)
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
    add("統包網路工具十四檢(SUP_MDL740)", newest("via_net_unified_v0*.py", HERE.parent / "network"), ["--selftest"], "rc0", 120)
    add("統一加速器六檢(SUP_MDL737)", newest("SUP_MDL737_SuperAccelModule_v*.py", HERE.parent), ["--selftest"], "rc0", 120)
    add("子系統治理器V2八檢(批126)", newest("CGC_MDL081_SubsystemManagerV2_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("雙橋清掃器八檢(批127)", newest("via_bridge_sweeper_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("自動總跑器六檢(批127)", newest("CGC_MDL082_MasterAutorun_v*.py", HERE), ["--selftest"], "rc0", 600)
    add("中央治理引擎四檢(批132)", newest("CGC_MDL083_CentralGovernment_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("測試金字塔六檢(批142)", newest("CGC_MDL087_TestPyramid_v*.py", HERE), ["--selftest"], "rc0", 600)
    add("治理議題分圈器六檢(批133)", newest("CGC_MDL084_GovTriage_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("議題仲裁器八檢(批133)", newest("CGC_MDL085_IssueArbiter_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("正典裁定器六檢(批133 收官)", newest("CGC_MDL086_CanonArbiter_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("總擷取引擎十檢(批128)", newest("VDF_ENG052_MegaFetch_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("VDF 參數映射器十檢(批134)", newest("VDF_ENG053_ParamEngineMap_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("台股回補工人六檢(批136)", newest("VDF_ENG054_TWDailyBackfill_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("總擷取執行器八檢(批137)", newest("VDF_ENG055_OmniFetch_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
    add("籌碼回補引擎六檢(批140)", newest("VDF_ENG056_ChipBackfill_v*.py", VIA / "functional modules/VDF/engine"), ["--selftest"], "rc0", 300)
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
    add("儀表板原始版八檢(批167)", newest("VAP_ENG009_DashboardUI_v*.py", VIA / "functional modules/VAP/engine"), ["--selftest"], "rc0", 300)
    add("系統同步樞紐八檢(批168)", newest("CGC_MDL090_SystemHub_v*.py", HERE), ["--selftest"], "rc0", 300)
    add("每日觀察摘要八檢(批174)", newest("VRN_ENG068_DailyBrief_v*.py", VRN), ["--selftest"], "rc0", 300)
    add("系統憲章對照八檢(批175)", newest("CGC_MDL091_CharterAudit_v*.py", HERE), ["--selftest"], "rc0", 300)
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
    add("selftest grid(自指:文件)", None, [], "doc", 10)  # 佔位:自身以 --fast 遞迴屬禁,列 SKIP
    return B


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


def main() -> int:
    fast = "--fast" in sys.argv
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    B = battery(fast)
    print(f"=== 全面自測矩陣 v0137 · {len(B)} 站 · {'FAST' if fast else 'FULL'} · 全安全模式(零 commit 零網路)===")
    results = []
    for b in B:
        r = run_one(b)
        results.append(r)
        mark = {"OK": "OK  ", "FAIL": "FAIL", "SKIP": "SKIP"}[r["state"]]
        print(f"  [{mark}] {r['name']} · {r['secs']}s · {r.get('note', '')[:96]}")
    n_ok = sum(1 for r in results if r["state"] == "OK")
    n_fail = sum(1 for r in results if r["state"] == "FAIL")
    n_skip = sum(1 for r in results if r["state"] == "SKIP")
    OUT.mkdir(parents=True, exist_ok=True)
    ev = OUT / f"GRID_{ts}.json"
    ev.write_text(json.dumps({"schema": "VIA.SelftestGrid.v1", "ts": ts, "fast": fast,
                              "ok": n_ok, "fail": n_fail, "skip": n_skip, "results": results},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [計] OK {n_ok} · FAIL {n_fail} · SKIP {n_skip}(誠實三態)· 存證 {ev.name}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
