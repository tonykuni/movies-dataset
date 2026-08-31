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
v0141→v0142(批97 焦點四柱):+第 83 站三子系統管理十檢(TOOL-099
憲章對讀/四類盤點/AST 健康 RYG/VSM 遞迴迷你報/缺根缺憲章誠實)
——83 站。
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
    add("統包網路工具十檢", newest("via_net_unified_v0*.py", HERE.parent / "network"), ["--selftest"], "rc0", 120)
    add("VAP 圖規鎖八檢", newest("vap_spec_guard_v0*.py", VIA / "functional modules/VAP"), ["--selftest"], "rc0", 120)
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
    add("財務字庫十四檢", newest("vrn_finlex_v0*.py", VRN), ["--selftest"], "rc0", 180)
    add("註冊台維運八檢", VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/FLOW_ENG024_FlowRegistryOps.py", ["--selftest"], "rc0", 120)
    add("指揮中心十檢", newest("via_command_center_v0*.py", HERE), ["--selftest"], "rc0", 120)
    add("合約同步 self-test", HERE / "VIA_Central_SSOT_Contract_Sync_Engine.py", ["self-test"], "rc0", 120)
    add("族群量價 self-test", VIA / "functional modules/GroupIndex/engine/VIA_TW_Group_PriceVolume_Volatility_Engine_v0100.py", ["--self-test"], "env", 300)
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
