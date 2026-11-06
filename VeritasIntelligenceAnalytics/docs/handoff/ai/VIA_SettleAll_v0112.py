#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_SettleAll v0112 — 一支 Python 收尾五系統 + 兩個工具:全景檢視 → 同步 → VDF ui → VRN 狀態 → VCGC 驗 → Graphify → VQG → Agent OS → 報告 + 貼回包。

v0112(桌機 2026-11-06 22:19 v0111 貼回 · v0111 一字不動):③ 還原了 26 支刪掉的舊版 + 2 本壞 JSON,但還剩 2 個 other =
  VRN_SystemManager_v0152 / v0153 被**改了內容**(+220 / −61 · +939 / −73 行;尾版是 v0254 / v0261)→ ③ 又不合併 → ④⑥⑬ 還在舊樹。
  已發布的非尾版是凍結的(只增規則 · 薄尾鏈引用它們 · bytes 以 git 為正本)→ 本版新類 **frozen:改了的非尾版 `_vNNNN.py / .ps1`**
  先把桌機版備份到 VIA_Reports/settle/frozen_version_backup/<檔>.<時間>.desktop 再 `git checkout HEAD -- 檔`(可回滾 = 把備份放回)。
  尾版被改仍算 other(那可能是真的在做事 · 不動)。另:③ 把未追蹤檔(桌機 404 個)依夾計數 + 程式類檔名列進報告(只讀),
  下一輪就看得到桌機 / Manus 新增了什麼。

v0111(容器實跑 v0110 ⑭:144 列「未登號」· v0110 一字不動):那 143 支(VDF 78 · VRN-2 65 · VeritasCeleritas)其實都登在 VCGC 的 **ENG 冊**
  (VIA_NumberBook_ENG_v0100.jsonl · 例 VDF_ENG049_FiveDayFetch_v0100 = VIA-VDF-ENG015 · 2026-09-28),v0110 只查 MDL 冊 → 本版 MDL + ENG 兩本冊一起讀(各一次 · 快取)。
  不是 VCGC 沒編號,是本檔查漏;VCGC 編號冊零寫入。

v0110(操作員 2026-11-06「SYSTEM / FUNCTION / DESCRIPTION / MDL/ENG NAME / CLS / FNC / LIBS / ERROR & AST / STATUS · 逐步將多矩陣管理報告完善 ·
  先整理各系統矩陣第一欄三個燈號」· v0109 一字不動):
  ⑭ 模組矩陣:VRN-2 · VDF(根 + engine)· VCGC(CGC_ 家族)· VCGC·支援(via_ / VIA_ / SUP_)· VCGC·Agent OS · VQG · VAP 每個家族的尾版一列(只 ast.parse · 不執行):
     第一欄 = 該系統這輪的燈(⑤ ④ ⑥ ⑨ ⑧ 同 ⑫ 系統矩陣)· FUNCTION = 家族名 · DESCRIPTION = 模組 docstring / 首個註解行 · MDL/ENG NAME = 尾版檔名 + VCGC 編號(MDL 冊)·
     CLS / FNC = 類與函式(含方法)個數 · LIBS = 第三方套件(標準庫不算 · VIA 內部模組另計個數)· ERROR & AST = 語法 / 編譯錯 · 重複定義 · 無加速器橋 · 網路 import 沒網路橋 ·
     STATUS = 只從本輪證據取:VDF 用 ⑬ 自測結果(rc 0 🟢 · rc 2 🟡 · 其他 🔴 · 預算外 ⚪)· VCGC 用 VCGC 自己的功能帳 VIA_VCGC_FunctionLedger(家族最後一筆 lamp · 版本 · UTC 時間;
     帳上版 ≠ 尾版 → 🟡)· 系統入口家族用該步的燈 · 其餘 ⚪ 未實測(不冒充綠)· 語法錯一律 🔴。
     → VIA_Reports/settle/VIA_ModuleMatrix_latest.json / .md / .html(HTML 可按文字篩)· 綠的列追加只增帳 VIA_ModuleMatrix_Ledger.jsonl(時間 · 檔 · 版本 · VCGC 編號)·
     矩陣帶「上次綠」欄;⑫ 系統矩陣多一列「模組矩陣 ⑭」(各系統 🟢🟡🔴⚪ 個數)· 報告有各系統小計表。MDL 冊改成讀一次快取(500 列不再逐列掃冊)。

v0109(桌機 2026-11-06 21:04 v0108 貼回 · v0108 一字不動):兩個阻塞的真相終於印出來了:
  ③ 28 支 other 的 git 狀態碼 = `D `:桌機把 VRN 舊版(ENG062 v0101–0112 · ENG397 v0113–0128 · SystemManager v0152–0153)整支刪掉並已 git rm(+0 / −1116 行)。
     刪已發布的版本違反只增規則、薄尾還可能引用它們 → 本版新類別 **deleted:從 HEAD 還原**(檔都在 git 裡 · 零資料損失 · 可回滾 = 再刪一次),還原清單進報告。
  ⑥ 壞 JSON = VIA_VCGC_SubsystemSeat_v0100.json 第 8 行(state 冊)→ 本版 stash 前先把 receipt / state 類裡 json.loads 不過的冊**備份到
     VIA_Reports/settle/broken_json_backup/ 再還原 HEAD 版**(可回滾)。這兩件修完 ③ 就能合併,④ ⑥ MCP 全部有燈。
  ⑫ 矩陣多「VCGC 編號 · 編號時間」欄(從 VIA_NumberBooks/VIA_NumberBook_MDL_v0100.jsonl 查該系統尾版的 VIA-…-MDL 號與 numbered_at)—— 成功部分用 VCGC 的名字與版號記。
  ⑬ VDF 全引擎自測掃描(操作員「實測 VDF 所有引擎都可跑」):functional modules/VDF 與 VDF/engine 每個家族尾版跑 `--selftest`(2 線 · 每支 120 秒 · 總預算 20 分)
     → VIA_Reports/settle/VDF_Engines_Matrix_latest.json / .md(綠 rc 0 · 黃 rc 2 · 紅其他 · 附最後一行)+ 系統矩陣 VDF 子列;舊樹不跑(同 ④)。

v0108(操作員 2026-11-06「INTEGRATE ALL INTO ONE CODE · 守住所有已完成功能 · 矩陣式呈現 · 三種燈號 · 成功就記時間 / 版本 / 狀態 · Agent OS 屬於 VCGC」· v0107 一字不動):
  ⑫ 系統矩陣:每輪把 VRN-2 · VDF · VCGC(子列 Agent OS · Graphify · MCP · 政策全景)· VQG · VAP 的燈(🟢 🟡 🔴 · ⚪ = 這輪沒測)· 版本尾 · 狀態 · 本輪秒數
     寫成 VIA_Reports/settle/VIA_SystemMatrix_latest.json / .md / .html;**綠的那列追加到只增帳 VIA_SystemMatrix_Ledger.jsonl(時間 · 版本 · 狀態)**,
     矩陣永遠帶「上次綠:時間 · 版本」欄 → 這輪黃了也看得到已完成功能守在哪一版(守住已完成功能)。VCGC 子列 MCP = 跑 CGC_MDL279 自測(在樹上才跑)。
     Windows 跑完自動開矩陣 HTML(VIA_NO_OPEN=1 不開)。

v0107(桌機 2026-11-06 19:33 / 19:41 v0106 貼回 · v0106 一字不動):整輪 5 分 → 2.5 分(圖沿用 · 快取命中 5,087)。但 ③ 28 個 other 的差異抓不到(+?/−?):
  桌機那些檔已 git add 進索引,`git diff` 只比工作樹對索引 → 空。本版改比 **HEAD**(`git diff HEAD`),並把每檔的 git 狀態碼(XY)寫進報告;
  ⑥ 被略過(舊樹)時壞 JSON 掃描也沒跑 → 本版 ⑥ 不論跑不跑都先掃小 JSON(只讀 · 幾秒)。

v0106(操作員 2026-11-06「PS 指令貼上去跑後速度很慢」· v0105 一字不動):桌機 v0104 實錄 Graphify 四張 1,881 秒(1 worker 下 VRN_Shared 1,114 秒 ·
  VCGC 188 秒後被殺)· VCGC 串測 ~180 秒 · ⓫ 掃 7,000 檔 · ③ 沒同步時 ④ ⑥ 還在舊樹上白跑 → 四處省時:
  ⑦ Graphify 預設 --graphify changed:該系統夾最新 .py 的 mtime 沒晚於上一張 graph.json → 沿用(GREEN · 0 秒);可用記憶體 < 估計 → 直接跳過不耗 15 分
     (--graphify all 照舊全跑 · skip 全不跑)。
  ⓫ 政策全景 mtime 快取(VIA_Reports/settle/policy_cache.json · 檔沒變不重讀)。
  ③ 沒合併(有 other 改動)→ ④ VDF ui 與 ⑥ VCGC 不在舊樹上跑(YELLOW 寫明原因 · --force-old-tree 可逼跑)。
  每段記秒數進報告(stage_secs)。

v0105(桌機 2026-11-05 01:32 v0104 貼回 · v0104 一字不動):
  ③ 同步:38 個改動分出 receipt 5 · state 5 · other 28(VRN 舊版 ENG062 / ENG397 / SystemManager)—— other 不是只差橋塊,但報告裡看不到差在哪
     → 本版對 other 逐檔記 `git diff --numstat`(+ / −)與前幾行差異(head 版 vs 工作樹)進報告,下一輪就知道是誰改的、改了什麼。
  ⑥ VCGC:事件冊抓到 `JSONDecodeError … line 8 column 1 (char 215)` 但沒說哪個檔 → 本版在 VCGC 讀的小 JSON(registry 冊 · VIA_Reports/vcgc · .via)
     逐檔 json.loads,把壞掉的檔名 + 行列印出來(只讀 · 不改);桌機那 5 本 state 冊(SubsystemSeat 13 行 · 416 B)最可疑。
  ⓫ 政策全景:桌機 VIA 樹裡有 venv/Lib(1,977 支 site-packages 被算進去)→ venv / .venv / site-packages / Lib / envs / node_modules 不算。

v0104(桌機 2026-11-05 00:08 v0103 貼回 · v0103 一字不動;操作員:自動完成全部 · PS / PY 都要加速器 · 擷取引擎都走最新網路工具 · 五系統同步進行 · 不傷健康不生九頭龍):
  ③ 同步:桌機 38 個改動 → 收據 1 · 其他 37(VRN 舊版 ENG062 / ENG397 / SystemManager 30 支 · VCGC 狀態冊 4 本 · VDF 的 WHERE_IS_OUTPUT_HUB · U/I html · paste.md)→ v0103 照規矩停。
     本版把每個改動用 `git show HEAD:檔` 對工作樹**算出類別**:receipt(收據)· state(VCGC / VDF 自己寫的狀態冊)· bridge(只差加速器 / 網路橋塊 ·
     = 桌機 via-bridge-sweep / via_net_injector 注入的)· eol(只差換行)· other(真的改了程式或冊)。只有 other 才停;其他四類 stash → 合併 → 放回,
     衝突時 receipt 取桌機版、state / bridge / eol 取分支版(分支是正本 · 桌機的橋由 sweep 再補 → 不會長出第二個頭)。類別逐檔寫進報告。
  ⑥ VCGC:桌機兩個指令只印到 token 卡就 rc 1、沒有任何 [RED] 行 → 本版把 VCGC 自己的事件冊(VIA_Reports/vcgc/events/EVENTS_<日>.jsonl)
     最後幾筆 outcome / error 讀進報告(VCGC 不印的錯它自己有記)。
  ⑦ Graphify:VCGC 那張 extract 階段吃 4.8–5.2 GB(2 個 worker)被殺兩次 → 可用記憶體 < 估計 + 2 GB 時改 `--max-workers 1`(慢一點 · 峰值約減半)。
  ④⑤⑧⑨ 同步進行:VDF ui · VRN 狀態 · VQG · Agent OS 四段彼此不碰同一個檔(各寫各的收據夾)→ 併行跑(--serial 可關);⑥ VCGC(寫紀錄冊)與
     ⑦ Graphify(吃記憶體)仍一個一個來 —— 健康優先。
  ⓫ 政策全景(L103 · 只讀不改):VIA 樹 .py 沒有加速器橋 / 有網路 import 卻沒有網路橋 / .ps1 沒有 Celeritas 的,算個數列檔名;補缺是 VCGC 的
     via-bridge-sweep 的事(本檔不改他系統的檔)。

v0103(桌機 2026-11-04 20:34 v0102 貼回 · v0102 一字不動):
  ③ 同步:桌機在 main · 落後分支 213 提交 · 38 個已追蹤檔有改動 → v0102 一律不合併 → ④ VDF ui 跑到舊版 v0162(AttributeError DB_MOD:
     DB_MOD 在分支的 v0155+ 才有)· ⑥ VCGC 也在舊樹上紅。本版把改動分兩類:**收據類**(VIA_Reports/** · docs/handoff/evidence/** · HANDOFF_latest ·
     Lessons / FunctionLedger 兩本只增冊 · .via/)= 各系統自己跑出來的,自動 `git stash push -- <那些檔>` → 合併 → `stash pop`(衝突取桌機版 · 不丟);
     **其他**(程式 / 冊)才停下來,並把檔名列進報告與畫面(v0102 只印個數)。
  ② AST 全景:多比對分支 origin/<BRANCH> 上每個家族的尾版 → 「工作樹落後分支」逐家族寫出(例 VDF_SystemManager v0162 ← v0168),
     ④ / ⑥ 紅的時候直接指回 ③。
  ⑥ VCGC:把 handoff check / test --quick 的輸出尾段與第一行 [RED] 寫進報告(v0102 只有 rc · 看不出為什麼紅)。
  ⑦ Graphify:看門狗殺掉時記「階段(extract / cluster)」與「吃掉(估)= 起始可用 − 最低可用」(桌機 VCGC 實測 ≥ 3.2 GB 才被殺 ·
     graphify.exe 是殼 · 它自己的 RSS 量不到 worker,v0102 的峰值 RSS 0.01 GB 不算數)· 下一步寫明要多少可用記憶體。

操作員 2026-11-04 桌機貼回四條一行的結果 → 「integrate into one code to handle above」。要處理的(v0101 一字不動 · 本版新檔):
  ⑦ Graphify v0101 一行:VCGC 那張圖用固定表「需要約 6 GB」在 4.6 GB 可用時直接跳過 → 本版改成**真跑 + 記憶體看門狗**:
     每秒量可用記憶體與子行程 RSS,可用 < 下限(預設 0.75 GB · --graphify-floor-gb)就殺整棵子行程(桌機不當掉)· 峰值 RSS 與最低可用記進收據,
     下次就有實測數字,不再靠猜。VRN · VRN_Shared · VDF 三張已綠的照 graphify 自己的增量快取,只重抽改過的檔。
  ⑧ VQG 一行:紅 NO_DAILY_PRICES。根因 = 桌機工作樹的 VDF 冊只有 v0100(家 = via_01_vdf · 2026-10-22 實測底下 .duckdb 0 個),
     分支上的 v0101 才把真正的家 via_database\\vdf_database 排第一;一行只取 VQG 兩個檔、沒更新工作樹 → VQG 照舊冊找錯家。
     本版:③ 同步先把分支併進來(乾淨才併)→ ⑧ VDF 家候選 = $env:VQG_VDF_ROOT → 工作樹 + 分支尾版兩邊所有 VDF_DataHome_SSOT_v*.json
     的 homes(新版冊優先 · 冊內照順序)→ 倉內 VDF\\output_hub 接點;每個在這台機器存在的家都跑 VQG 自己的 doctor,
     取第一個有日線 parquet 的家再 closeout(收據照 VQG 自己寫)。一個都沒有 → RED 列出每個家的 doctor 判決,並指明是 VDF 線要跑日線回填。
  ⑨ Agent OS 一行:selftest rc 2、其餘三項 rc 0。根因 = 引擎自測 test_scan_project_enforces_total_source_bytes_and_nofollow 用
     symlink_to 建捷徑,Windows 沒開「開發人員模式」或不是系統管理員會 OSError WinError 1314(容器 48 / 48 綠)。
     本版:讀自測 JSON 的 details 逐項分類 —— 只有「Windows 建 symlink 權限」這類環境項 → YELLOW(引擎本體照設計拒 symlink · 功能不受影響),
     其他失敗 → RED;不是 RED 才產生儀表板(一行原本 RED 就停)。引擎一字不改(SHA-256 釘住)。
  ⑤ VRN:--confirm H-fd2ea35f 已記、收尾頁 DATA_GAP(資料源缺口 · VRN-2 側結案)→ 本版 --vrn 預設 status:只讀 VRN-2 自己的收尾收據判燈,
     不重跑 40 分鐘那輪(要重跑仍可 --vrn repair / check)。
  取檔:VQG v0104 / v0105 與 Agent OS v0102 先看工作樹(SHA-256 對才用),不對或不在 → 從分支 origin/<BRANCH> git show 取到 Downloads\\VIA_Settle_v0102\\
     再核 SHA-256;不對就不跑。VQG 的 Python 照一行的順序找有 duckdb + polars 的(VQG 不 pip)。
五系統對等(VRN-1 · VRN-2 · VDF · VCGC · VQG)+ Agent OS / Graphify 工具:本檔只經各系統自己的入口跑,不改他系統的檔;
只寫 VIA_Reports/settle · VIA_Reports/agent_os · VIA_Reports/graphify 與 Downloads(VQG / VRN / VDF 的收據由它們自己寫)。
用法:python VIA_SettleAll_v0102.py [--root <倉根>] [--only scan,sync,vdf,vrn,vcgc,graphify,vqg,agentos,report] [--no-sync]
      [--vrn status|repair|check|skip] [--graphify-floor-gb 0.75] [--selftest]
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔零網路。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====


import argparse
import ast
import collections
import contextlib
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path

NAME = "VIA_SettleAll"
VERSION = "v0112"
BRANCH = "claude/optimistic-goodall-yhalc5"
STAGES = ("scan", "sync", "vdf", "vrn", "vcgc", "graphify", "vqg", "agentos", "policy", "vdfeng", "modmatrix", "matrix", "report")
PARALLEL = ("vdf", "vrn", "vqg", "agentos")   # 彼此不碰同一個檔 → 併行;vcgc / graphify 一個一個來
FAMILIES = {   # 家族 → (夾, 前綴);只讀,不改他系統的檔
    "VRN_SystemManager": ("functional modules/VRN", "VRN_SystemManager_v"),
    "VDF_SystemManager": ("functional modules/VDF", "VDF_SystemManager_v"),
    "VDF_ENG236_FetchMatrixUI": ("functional modules/VDF/engine", "VDF_ENG236_FetchMatrixUI_v"),
    "CGC_MDL149_Console": ("supportive modules/registry", "CGC_MDL149_VeritasCentralGovernanceConsole_v"),
    "CGC_MDL261_UIEngine": ("supportive modules/registry", "CGC_MDL261_UIEngine_v"),
    "CGC_MDL274_HealthMatrix": ("supportive modules/registry", "CGC_MDL274_HealthMatrix_v"),
    "CGC_MDL224_TestAuto": ("supportive modules/registry", "CGC_MDL224_TestAuto_v"),
    "VRN2_RoundAll": ("docs/handoff/ai", "VRN2_RoundAll_v"),
    "VQG_AllInOne": ("functional modules/VQG", "VQG_AllInOne_v"),
    "VIA_AgentOS": ("supportive modules/agent_os", "VIA_AgentOS_v"),
    "VAP": ("functional modules/VAP", "VAP_"),
    "CGC_MDL279_MCPServer": ("supportive modules/registry", "CGC_MDL279_MCPServer_v"),
}
PINNED = {   # 從工作樹 / 分支取檔時核 SHA-256(CRLF 先正規化成 LF · 與各一行的算法相同);不對就不跑
    "functional modules/VQG/VQG_AllInOne_v0104.py": "d2a5ca07fa4d29435584c111095a31951075ab585b51cc74b14b22ef48ca1d02",
    "functional modules/VQG/VQG_AllInOne_v0105.py": "cc050f0fe42786f7113dbf0dd920d954feaf0b020e216456f336ce0d30801619",
    "supportive modules/agent_os/VIA_AgentOS_v0102.py": "3d23c7adefce5e688277676fadc0a4a70311da3d41fd6b6ef6de1c1bcd9077fb",
}
VQG_FILES = ("functional modules/VQG/VQG_AllInOne_v0104.py", "functional modules/VQG/VQG_AllInOne_v0105.py")
AGENTOS_FILE = "supportive modules/agent_os/VIA_AgentOS_v0102.py"
GRAPHIFY_SYSTEMS = (("VRN", "functional modules/VRN2", 3), ("VRN_Shared", "functional modules/VRN", 4),
                    ("VDF", "functional modules/VDF", 4), ("VCGC", "supportive modules/registry", 6))   # gb = v0101 一行的估計(只記 · 不再拿來跳過)
RECEIPT_PREFIXES = (   # 各系統自己跑出來的收據 / 只增冊(倉內有追蹤)→ 同步時 stash → 合併 → 放回;其他改動要操作員決定
    "VeritasIntelligenceAnalytics/VIA_Reports/", "VeritasIntelligenceAnalytics/docs/handoff/evidence/", "VeritasIntelligenceAnalytics/docs/handoff/HANDOFF_latest.json",
    "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_Lessons_Ledger_", "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_VCGC_FunctionLedger_",
    "VeritasIntelligenceAnalytics/.via/", ".via/", "VeritasIntelligenceAnalytics/functional modules/VDF/WHERE_IS_OUTPUT_HUB.md",
    "VeritasIntelligenceAnalytics/supportive modules/ui_support/", "VeritasIntelligenceAnalytics/paste.md")
STATE_PREFIXES = (   # VCGC / VDF 自己寫的狀態冊(倉內有追蹤)→ stash → 合併 → 放回;衝突取分支版
    "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_RestorePoint_Ledger_", "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_ParallelLanes_",
    "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_ProjectCompletion_", "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_VCGC_SubsystemSeat_",
    "VeritasIntelligenceAnalytics/supportive modules/VIA_FlowSystem/FlowSystem_v2/config/TW_Active_ETF_Registry_")
BRIDGE_RX = re.compile(r"^[ \t]*# ===== \[VIA:(ACCEL|NET)-BRIDGE:v\d+\][^\n]*\n.*?^[ \t]*# ===== \[VIA:\1-BRIDGE:END\] =====[^\n]*\n?", re.S | re.M)
MARKER_RX = re.compile(r"^[ \t]*# \[VIA:ACCEL-BRIDGE:v\d+\][^\n]*\n?", re.M)
NET_IMPORT_RX = re.compile(r"^\s*(?:import|from)\s+(?:requests|urllib|urllib3|httpx|aiohttp|socket|yfinance|websocket|websockets|http\.client)\b", re.M)
POLICY_SKIP = ("/references/", "/intake/", "quarantine", "VIA_RetiredEngines", "/backup", "/archive", "/.git/", "/__pycache__/", "/VIA_Reports/",
               "/vcg/", "_self_test", "/tests/", "supportive modules/ssot/",                      # = VCGC 全景工具 SKIP_MARK(批535)
               "/_inbox_to_classify/", "/_superseded", "/new modules engines/", "/supportive modules/network/",   # 待分類 / 被取代 / 新模組收容 / 網路工具本體
               "/VIA_HTML_UI/ci/", "/VIA_HTML_UI/e2e/", "/VIA_HTML_UI/qa/", "/VIA_HTML_UI/skills/",
               "/venv/", "/.venv/", "/site-packages/", "/Lib/", "/envs/", "/node_modules/", "/dist-packages/", "/Scripts/")   # 樹裡的虛擬環境不算   # HTML U/I 的 CI / e2e / qa 腳本(不是引擎)
TOOL_SELF_RX = re.compile(r"(VeritasCeleritas|VeritasAegisNexus|SUP_MDL737_SuperAccelModule|SUP_MDL740_NetUnified|via_net_unified|VIA_SuperAccel_Module|via_net_injector|CGC_MDL124_BridgeSweeper)", re.I)   # 加速器 / 網路工具本體不用自己橋自己
CONFLICT_KEEP = {"receipt": "theirs", "state": "ours", "bridge": "ours", "eol": "ours", "deleted": "ours", "frozen": "ours"}   # stash pop 衝突:theirs = stash = 桌機 · ours = 合併後的分支版
_SAY_LOCK = threading.Lock()
GLYPHS = "⓪①②③④⑤⑥⑦⑧⑨⓫⑬⑭⑫⑩"   # ⑩ 報告永遠最後
LAMP_ICON = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴", "GRAY": "⚪"}
MODULE_SCOPES = (   # ⑭ 模組矩陣:(系統, 夾, 檔名正則);夾內不遞迴(隔離 / 凍結 / 輸出子夾不在範圍)· 只讀 AST · 不執行
    ("VRN-2", "functional modules/VRN", r"."), ("VRN-2", "functional modules/VRN/engine", r"."),
    ("VDF", "functional modules/VDF", r"."), ("VDF", "functional modules/VDF/engine", r"."),
    ("VCGC", "supportive modules/registry", r"^CGC_"), ("VCGC·支援", "supportive modules/registry", r"^(?!CGC_)"), ("VCGC·支援", "supportive modules", r"."),
    ("VCGC·Agent OS", "supportive modules/agent_os", r"."), ("VQG", "functional modules/VQG", r"."), ("VAP", "functional modules/VAP", r"."))
SYSTEM_GLYPH = {"VRN-2": "⑤", "VDF": "④", "VCGC": "⑥", "VCGC·支援": "⑥", "VCGC·Agent OS": "⑨", "VQG": "⑧"}   # 第一欄系統燈 = 該步的燈(同 ⑫)
SYSTEM_ENTRY = {"VRN-2": ("VRN_SystemManager",), "VCGC·Agent OS": ("VIA_AgentOS",), "VQG": ("VQG_AllInOne",)}   # 系統入口家族 → STATUS 用該步的燈
INTERNAL_RX = re.compile(r"^(?:VIA|via|SUP_|CGC_|VRN|VDF|VQG|VAP|Veritas|Invoke)")   # VIA 內部模組(不算第三方套件)
GRAPHIFY_EXCLUDES = ("references/", "intake/", "_quarantine*/", "*quarantine*/", "VIA_RetiredEngines/", "backup*/", "archive*/")
WIN_SYMLINK_PRIVILEGE = ("winerror 1314", "privilege is not held")   # Windows 沒有建 symlink 權限(開發人員模式 / 系統管理員)
FRAME_RX = re.compile(r'File "(?P<file>[^"]+)", line (?P<line>\d+)(?:, in (?P<func>\S+))?')
EXC_RX = re.compile(r"^(?P<type>[A-Za-z_][\w.]*(?:Error|Exception|Warning|Exit|Interrupt))(?::\s*(?P<msg>.*))?$")
ATTR_RX = re.compile(r"(?:module|object) '(?P<mod>[^']+)' has no attribute '(?P<attr>[^']+)'")
LOG = []
RANK = {"GREEN": 0, "GRAY": 0, "YELLOW": 1, "RED": 2}


def worst(*lamps) -> str:
    """燈取最差:RED > YELLOW > GREEN(GRAY 當 GREEN);認不得的當 YELLOW(不冒充綠)。"""
    out = "GREEN"
    for x in lamps:
        x = x if x in RANK else "YELLOW"
        if RANK[x] > RANK[out]:
            out = x
    return out


def vdf_lamp(rc: int, lamps: list) -> str:
    """④ rc 不是 0 → RED;rc 0 → 頁上各段燈取最差(YELLOW 不升 GREEN)。"""
    return "RED" if rc != 0 else worst(*lamps)


def vrn_lamp(rc: int, state: dict | None, fresh: bool) -> str:
    """⑤ 本次 rc 不是 0 / 2 → RED(舊收據不救);收據不是本次寫的 → 最多 YELLOW;本次寫的 PASS → GREEN;VRN-2 側有待修 → RED。"""
    if rc not in (0, 2):
        return "RED"
    if not state or not fresh:
        return "YELLOW"
    if (state.get("per_owner") or {}).get("VRN-2"):
        return "RED"
    return "GREEN" if state.get("state") == "PASS" else "YELLOW"


def vrn_status_lamp(state: dict | None) -> str:
    """⑤ status 模式(只讀收據 · 不跑):沒收據 → YELLOW;VRN-2 側有待修 → RED;PASS → GREEN;其他(REVIEW / DATA_GAP …)→ YELLOW。"""
    if not state:
        return "YELLOW"
    if (state.get("per_owner") or {}).get("VRN-2"):
        return "RED"
    return "GREEN" if state.get("state") == "PASS" else "YELLOW"


def vcgc_lamp(test_lamp: str | None, test_rc: int, handoff_rc: int, handoff_red: dict) -> str:
    """⑥ test --quick 總燈與 handoff check 取最差:沒讀到總行 → RED;test rc 不是 0 / 2 → RED;交接閘有紅或 rc 不是 0 → RED。"""
    t = test_lamp if test_lamp in RANK else "RED"
    if test_rc not in (0, 2):
        t = "RED"
    h = "RED" if (handoff_rc != 0 or handoff_red) else "GREEN"
    return worst(t, h)


def agentos_classify(report: dict | None, windows: bool) -> dict:
    """⑨ 自測 JSON → 燈:ok → GREEN;失敗全是「Windows 沒有建 symlink 權限(WinError 1314)」→ YELLOW(環境 · 引擎照設計拒 symlink);
    其他(或不是 Windows 卻這樣)→ RED;讀不到 JSON → RED。"""
    if not isinstance(report, dict) or "ok" not in report:
        return {"lamp": "RED", "known_env": [], "unknown": [{"test": "?", "kind": "NO_JSON"}], "tests_run": 0, "failures": 0, "errors": 0}
    known, unknown = [], []
    for d in report.get("details") or []:
        text = str(d.get("detail") or "").lower()
        row = {"test": str(d.get("test") or "")[:120], "kind": d.get("kind")}
        if windows and any(k in text for k in WIN_SYMLINK_PRIVILEGE):
            known.append(dict(row, why="Windows 建 symlink 要開發人員模式或系統管理員(WinError 1314)· 引擎本體照設計拒 symlink · 功能不受影響"))
        else:
            unknown.append(dict(row, tail=str(d.get("detail") or "")[-300:]))
    lamp = "GREEN" if report.get("ok") else ("YELLOW" if (known and not unknown) else "RED")
    return {"lamp": lamp, "known_env": known, "unknown": unknown, "tests_run": int(report.get("tests_run") or 0),
            "failures": int(report.get("failures") or 0), "errors": int(report.get("errors") or 0)}


def graphify_lamp(results: list) -> str:
    """⑦ 有紅 → RED;沒有一張綠或有黃 → YELLOW;全綠(灰不算)→ GREEN。"""
    lamps = [r.get("lamp") for r in results]
    if "RED" in lamps:
        return "RED"
    if "YELLOW" in lamps or "GREEN" not in lamps:
        return "YELLOW"
    return "GREEN"


_T0 = {}


def tick(step: str) -> None:
    _T0[step[0]] = time.time()


def say(lamp: str, step: str, text: str, nxt: str = "") -> None:
    secs = int(time.time() - _T0[step[0]]) if step and step[0] in _T0 else None
    line = "[%s] %s · %s%s" % (lamp, step, text, (" · %d 秒" % secs) if secs is not None else "")
    with _SAY_LOCK:
        LOG.append({"lamp": lamp, "step": step, "text": text, "next": nxt, "secs": secs})
        print(line + (("\n       → " + nxt) if nxt else ""), flush=True)


def step_order(entry: dict) -> int:
    """報告排序:照步驟圈號(併行段印出的先後不定)。"""
    g = (entry.get("step") or " ")[0]
    return GLYPHS.index(g) if g in GLYPHS else 99


def vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def family_files(via: Path, folder: str, prefix: str) -> list:
    base = via / folder
    if not base.is_dir():
        return []
    pat = ("**/" if folder == "docs/handoff/ai" else "") + prefix + "*.py"
    return sorted((p for p in base.glob(pat) if vnum(p) >= 0), key=vnum)


def _env(env=None) -> dict:
    e = dict(os.environ)
    e.update({"PYTHONUTF8": "1", "VIA_FROM_VCGC": "YES", "VIA_NO_OPEN": "1"})
    e.update(env or {})
    return e


def run(cmd, cwd=None, timeout=1800, env=None) -> tuple:
    """→ (rc, 輸出全文 stdout+stderr);逾時回 rc 124。只跑各系統自己的入口。"""
    rc, out, err = run2(cmd, cwd=cwd, timeout=timeout, env=env)
    return rc, out + err


def run2(cmd, cwd=None, timeout=1800, env=None) -> tuple:
    """→ (rc, stdout, stderr) 分開拿(VQG doctor 的 JSON 在 stdout · 說明在 stderr);逾時 rc 124 · 找不到程式 rc 127。"""
    try:
        p = subprocess.run([str(c) for c in cmd], cwd=str(cwd) if cwd else None, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=_env(env))
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        return 124, (out.decode("utf-8", "replace") if isinstance(out, bytes) else out), "\n[逾時 %d 秒]" % timeout
    except OSError as exc:
        return 127, "", "%s: %s" % (type(exc).__name__, exc)


def run_raw(cmd, cwd=None, timeout=300) -> tuple:
    """→ (rc, stdout bytes);git show 取檔用(不經文字解碼)。"""
    try:
        p = subprocess.run([str(c) for c in cmd], cwd=str(cwd) if cwd else None, capture_output=True, timeout=timeout, env=_env())
        return p.returncode, p.stdout or b""
    except (subprocess.TimeoutExpired, OSError):
        return 127, b""


# ---------------------------------------------------------------- 記憶體看門狗(⑦ Graphify)
def parse_meminfo_gb(text: str) -> float:
    m = re.search(r"^MemAvailable:\s*(\d+)\s*kB", text or "", re.M)
    return round(int(m.group(1)) / 2 ** 20, 2) if m else -1.0


def free_gb() -> float:
    """可用實體記憶體(GB);量不到回 -1(不猜)。"""
    try:
        if os.name == "nt":
            import ctypes

            class _MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = _MS()
            m.dwLength = ctypes.sizeof(_MS)
            return round(m.ullAvailPhys / 2 ** 30, 2) if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)) else -1.0
        return parse_meminfo_gb(Path("/proc/meminfo").read_text(encoding="utf-8"))
    except Exception:                                      # noqa: BLE001 — 量不到就 -1
        return -1.0


def rss_gb(pid: int) -> tuple:
    """子行程 (目前 RSS, 峰值 RSS) GB;量不到回 (0, 0)。"""
    try:
        if os.name == "nt":
            import ctypes

            class _PMC(ctypes.Structure):
                _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong), ("PeakWorkingSetSize", ctypes.c_size_t),
                            ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
            k32, psapi = ctypes.windll.kernel32, ctypes.windll.psapi
            h = k32.OpenProcess(0x1000, False, int(pid))          # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return 0.0, 0.0
            pmc = _PMC()
            pmc.cb = ctypes.sizeof(_PMC)
            ok = psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb)
            k32.CloseHandle(h)
            return (round(pmc.WorkingSetSize / 2 ** 30, 3), round(pmc.PeakWorkingSetSize / 2 ** 30, 3)) if ok else (0.0, 0.0)
        txt = Path("/proc/%d/status" % pid).read_text(encoding="utf-8")
        cur = re.search(r"^VmRSS:\s*(\d+)\s*kB", txt, re.M)
        pk = re.search(r"^VmHWM:\s*(\d+)\s*kB", txt, re.M)
        return (round(int(cur.group(1)) / 2 ** 20, 3) if cur else 0.0), (round(int(pk.group(1)) / 2 ** 20, 3) if pk else 0.0)
    except Exception:                                      # noqa: BLE001 — 子行程已結束或量不到
        return 0.0, 0.0


def kill_tree(pid: int) -> None:
    """殺子行程整棵(graphify 有 worker):Windows taskkill /T;POSIX 殺整個 session。"""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True, timeout=60)
        else:
            import signal
            os.killpg(os.getpgid(pid), signal.SIGKILL)
    except Exception:                                      # noqa: BLE001 — 已經死了就算了
        return


def run_watched(cmd, cwd=None, env=None, floor_gb: float = 0.75, timeout: int = 5400, poll: float = 1.0) -> dict:
    """跑子行程並看記憶體:每 poll 秒量可用記憶體與子行程 RSS;可用 < floor_gb → 殺整棵(rc 137)· 逾時 → 殺(rc 124)。
    → {rc, out, peak_rss_gb, min_free_gb, free_start_gb, killed, seconds}"""
    kw = {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)} if os.name == "nt" else {"start_new_session": True}
    t0 = time.time()
    f0 = free_gb()
    try:
        p = subprocess.Popen([str(c) for c in cmd], cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace", env=_env(env), **kw)
    except OSError as exc:
        return {"rc": 127, "out": "%s: %s" % (type(exc).__name__, exc), "peak_rss_gb": 0.0, "min_free_gb": f0, "free_start_gb": f0, "killed": None, "seconds": 0}
    chunks = []

    def _drain():
        for line in p.stdout:
            chunks.append(line)
    th = threading.Thread(target=_drain, daemon=True)
    th.start()
    peak, min_free, killed = 0.0, f0, None
    while p.poll() is None:
        time.sleep(poll)
        f = free_gb()
        if f >= 0:
            min_free = f if min_free < 0 else min(min_free, f)
        cur, pk = rss_gb(p.pid)
        peak = max(peak, cur, pk)
        if 0 <= f < floor_gb:
            killed = "可用記憶體 %.2f GB < 下限 %.2f GB → 殺子行程(桌機不當掉)" % (f, floor_gb)
            kill_tree(p.pid)
            break
        if time.time() - t0 > timeout:
            killed = "逾時 %d 秒 → 殺子行程" % timeout
            kill_tree(p.pid)
            break
    try:
        p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        killed = (killed or "") + " · 殺不掉(還在跑)"
    th.join(timeout=10)
    rc = p.returncode if killed is None else (124 if "逾時" in killed else 137)
    return {"rc": rc, "out": "".join(chunks), "peak_rss_gb": round(peak, 3), "min_free_gb": min_free, "free_start_gb": f0,
            "killed": killed, "seconds": int(time.time() - t0)}


# ---------------------------------------------------------------- 取檔(SHA-256 釘住)· Python 探找 · VDF 家候選
def sha_lf(data: bytes) -> str:
    """CRLF 正規化成 LF 再算 SHA-256(與 VQG / Agent OS 一行的算法相同)。"""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def git_show_bytes(repo: Path, ref: str, rel_repo: str) -> bytes | None:
    rc, data = run_raw(["git", "-C", repo, "show", "%s:%s" % (ref, rel_repo)], timeout=300)
    return data if rc == 0 and data else None


def fetch_set(via: Path, rels, dst_dir: Path, pinned: dict | None = None) -> tuple:
    """同一組檔(VQG 兩個 · Agent OS 一個)一起取:工作樹每個 SHA 都對 → 就地用;否則全組從分支 origin/<BRANCH> 取到 dst_dir(逐檔核 SHA)。
    → (路徑清單 | None, 說明)"""
    pinned = pinned or PINNED
    ok_tree, paths = True, []
    for rel in rels:
        p = via / rel
        try:
            good = p.is_file() and sha_lf(p.read_bytes()) == pinned[rel]
        except OSError:
            good = False
        ok_tree = ok_tree and good
        paths.append(p)
    if ok_tree:
        return paths, "工作樹(SHA-256 全對)"
    out, why = [], []
    for rel in rels:
        data = git_show_bytes(via.parent, "origin/" + BRANCH, "VeritasIntelligenceAnalytics/" + rel)
        if data is None:
            why.append("%s:分支取不到" % Path(rel).name)
            continue
        if sha_lf(data) != pinned[rel]:
            why.append("%s:分支上 SHA-256 %s 不是釘住的 %s" % (Path(rel).name, sha_lf(data)[:12], pinned[rel][:12]))
            continue
        dst_dir.mkdir(parents=True, exist_ok=True)
        q = dst_dir / Path(rel).name
        q.write_bytes(data.replace(b"\r\n", b"\n"))
        out.append(q)
    if why:
        return None, "工作樹的檔不在或 SHA 不符 · " + " · ".join(why)
    return out, "分支 origin/%s(SHA-256 全對)→ %s" % (BRANCH, dst_dir)


def find_python_with(mods, extra=()) -> Path | None:
    """照 VQG 一行的順序找有指定套件的 Python(不 pip):VQG_PY → envs\\via_core → via_core_312 → via_vdf_312 → C:\\Python313 → 本檔的 → PATH 上的。"""
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    sub = "Scripts/python.exe" if os.name == "nt" else "bin/python"
    cands = [os.environ.get("VQG_PY"), *extra]
    cands += [home / "envs" / n / sub for n in ("via_core", "via_core_312", "via_vdf_312")]
    cands += ["C:/Python313/python.exe" if os.name == "nt" else None, sys.executable, shutil.which("python"), shutil.which("python3")]
    seen = set()
    for c in cands:
        if not c or "WindowsApps" in str(c) or str(c) in seen:
            continue
        seen.add(str(c))
        p = Path(c)
        if p.is_file() and run2([p, "-c", "import " + ", ".join(mods)], timeout=120)[0] == 0:
            return p
    return None


def vdf_homes(text: str) -> list:
    """VDF_DataHome_SSOT 冊 → [(id, db_home)] 照冊上順序(讀不懂回空)。"""
    try:
        d = json.loads(text)
    except ValueError:
        return []
    return [(str(h.get("id") or "?"), str(h.get("db_home") or "")) for h in (d.get("homes") or []) if isinstance(h, dict) and h.get("db_home")]


def vdf_root_candidates(via: Path, branch_book: tuple | None = None) -> list:
    """VDF 家候選(順序 = 試的順序):$env:VQG_VDF_ROOT → 工作樹 + 分支尾版的 VDF_DataHome_SSOT_v*.json(新版冊優先 · 冊內照順序)→ 倉內 VDF\\output_hub 接點。
    branch_book = (檔名, 冊內容文字) · 由呼叫端從 origin/<BRANCH> 取(本函數不碰 git)。"""
    out, seen = [], set()

    def add(path, how):
        key = str(path).rstrip("\\/").lower()
        if key and key not in seen:
            seen.add(key)
            out.append({"path": str(path), "how": how})
    env = os.environ.get("VQG_VDF_ROOT")
    if env:
        add(env, "環境變數 VQG_VDF_ROOT")
    books = {}
    for p in (via / "functional modules" / "VDF").glob("VDF_DataHome_SSOT_v[0-9][0-9][0-9][0-9].json"):
        try:
            books[vnum(p)] = (p.name, vdf_homes(p.read_text(encoding="utf-8")), "工作樹")
        except OSError:
            books[vnum(p)] = (p.name, [], "工作樹(讀不到)")
    if branch_book:
        v = vnum(Path(branch_book[0]))
        if v not in books:
            books[v] = (branch_book[0], vdf_homes(branch_book[1]), "分支 origin/" + BRANCH)
    for v in sorted(books, reverse=True):
        name, homes, where = books[v]
        for hid, home in homes:
            add(home, "VDF 的冊 %s · %s(%s)" % (name, hid, where))
    add(via / "functional modules" / "VDF" / "output_hub", "倉內 VDF\\output_hub 接點(桌機是指到資料家的 junction)")
    return out


def pick_vdf_root(cands: list, doctor_fn) -> tuple:
    """每個在這台機器存在的家跑 doctor_fn(path) → dict;取第一個 daily_price_files > 0 的家。→ (選到的列 | None, 全表)"""
    chosen, table = None, []
    for c in cands:
        p = Path(c["path"])
        if not p.is_dir():
            table.append(dict(c, exists=False))
            continue
        if chosen is not None:
            table.append(dict(c, exists=True, verdict="(已選到前面的家 · 未探)"))
            continue
        d = doctor_fn(p) or {}
        row = dict(c, exists=True, verdict=d.get("verdict"), daily_price_files=int(d.get("daily_price_files") or 0),
                   files=d.get("files"), missing_for_strict=d.get("missing_for_strict"))
        table.append(row)
        if row["daily_price_files"] > 0:
            chosen = row
    return chosen, table


# ---------------------------------------------------------------- 找根 · git
def find_root(explicit=None) -> Path | None:
    cands = [explicit, os.environ.get("VIA_ROOT"), os.environ.get("VRN2_ROOT")]
    cands += [str(p) for p in Path(__file__).resolve().parents]
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    cands += [str(home / "OneDrive" / "Documents" / "movies-dataset"), str(home / "Documents" / "movies-dataset")]
    for c in cands:
        if not c:
            continue
        p = Path(c)
        for via in (p, p / "VeritasIntelligenceAnalytics"):
            if (via / "functional modules").is_dir() and (via / "supportive modules").is_dir():
                return via
    return None


def parse_ahead_behind(text: str) -> tuple:
    """`git rev-list --left-right --count A...B` → (只在本機, 只在遠端)。"""
    m = re.match(r"\s*(\d+)\s+(\d+)\s*$", text or "")
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def git_state(repo: Path, fetch: bool = True) -> dict:
    st = {"repo": str(repo), "branch": None, "head": None, "fetched": False}
    if shutil.which("git") is None:
        st["error"] = "沒有 git"
        return st
    st["branch"] = run(["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"])[1].strip()
    st["head"] = run(["git", "-C", repo, "rev-parse", "--short", "HEAD"])[1].strip()
    if fetch:
        for ref in (BRANCH, "main"):
            rc, _ = run(["git", "-C", repo, "fetch", "-q", "origin", ref], timeout=300)
            st["fetched"] = st["fetched"] or rc == 0
    for ref in (BRANCH, "main"):
        rc, out = run(["git", "-C", repo, "rev-list", "--left-right", "--count", "HEAD...origin/" + ref])
        a, b = parse_ahead_behind(out) if rc == 0 else (None, None)
        st[ref] = {"local_only": a, "remote_only": b}
    rc, out = run(["git", "-C", repo, "status", "--porcelain"])
    lines = [x for x in out.splitlines() if x.strip()] if rc == 0 else []
    st["dirty_tracked"] = sum(1 for x in lines if not x.startswith("??"))
    st["untracked"] = sum(1 for x in lines if x.startswith("??"))
    st["dirty_files"] = [x[3:].split(" -> ")[-1].strip().strip('"') for x in lines if not x.startswith("??")]
    st["dirty_xy"] = {x[3:].split(" -> ")[-1].strip().strip('"'): x[:2] for x in lines if not x.startswith("??")}
    st["untracked_files"] = [x[3:].strip().strip('"') for x in lines if x.startswith("??")][:800]
    return st


def untracked_summary(names: list) -> dict:
    """未追蹤檔(只讀 · 不加不刪):依前兩層夾計數 + 程式 / 冊類檔名(前 40)→ 下一輪看得到桌機新增了什麼。"""
    by = collections.Counter("/".join(Path(n).parts[:3]) for n in names)
    code = [n for n in names if Path(n).suffix.lower() in (".py", ".ps1", ".json", ".jsonl", ".md")]
    return {"total": len(names), "by_folder": by.most_common(12), "code_files": code[:40], "code_total": len(code)}



def _norm_rel(rel: str) -> str:
    r = str(rel).replace("\\", "/")
    return r[2:] if r.startswith("./") else r


def is_receipt(rel: str) -> bool:
    """倉內相對路徑是不是收據類(各系統自己寫的 · 可 stash 再放回)。"""
    return _norm_rel(rel).startswith(RECEIPT_PREFIXES)


def strip_bridges(text: str) -> str:
    """去掉加速器橋 / 網路橋塊與第 3 行標記 · CRLF → LF(比「程式本體」有沒有變)。"""
    s = text.replace("\r\n", "\n")
    s = BRIDGE_RX.sub("", s)
    return MARKER_RX.sub("", s)


def classify_dirty(repo: Path, rel: str, head_text=None, work_text=None, xy: str | None = None) -> str:
    """一個已追蹤改動的類別:deleted(整支刪了 · 從 HEAD 還原)· receipt · state · bridge(只差橋塊)· eol(只差換行)· other(真的改了)。"""
    r = _norm_rel(rel)
    if xy and "D" in xy[:2]:
        return "deleted"
    if work_text is None and not (repo / r).exists():
        return "deleted"
    if r.startswith(RECEIPT_PREFIXES):
        return "receipt"
    if r.startswith(STATE_PREFIXES):
        return "state"
    if head_text is None:
        rc, data = run_raw(["git", "-C", repo, "show", "HEAD:" + r], timeout=120)
        if rc != 0:
            return "other"
        head_text = data.decode("utf-8", "replace")
    if work_text is None:
        try:
            work_text = (repo / r).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return "other"
    if head_text.replace("\r\n", "\n") == work_text.replace("\r\n", "\n"):
        return "eol"
    if strip_bridges(head_text) == strip_bridges(work_text):
        return "bridge"
    if is_frozen_version(repo, r):
        return "frozen"
    return "other"


def is_frozen_version(repo: Path, rel: str) -> bool:
    """已發布的非尾版(同夾有更高版號的 _vNNNN 同家族檔)→ 凍結:桌機改了它 = 偏離正本,備份後還原 HEAD。尾版不算。"""
    p = repo / rel
    m = re.match(r"^(.*)_v(\d{4})$", p.stem)
    if not m or p.suffix.lower() not in (".py", ".ps1"):
        return False
    fam, v = m.group(1), int(m.group(2))
    try:
        return any(vnum(q) > v for q in p.parent.glob(fam + "_v[0-9][0-9][0-9][0-9]" + p.suffix))
    except OSError:
        return False


def other_diff(repo: Path, rel: str) -> dict:
    """一個 other 類改動差在哪(只讀):numstat(+ / −)與前幾行差異(head 版 vs 工作樹 · 各 160 字)。"""
    r = _norm_rel(rel)
    rc, so, _ = run2(["git", "-C", repo, "diff", "HEAD", "--numstat", "--", r], timeout=120)
    m = re.match(r"\s*(\S+)\s+(\S+)", so or "")
    out = {"file": r, "added": m.group(1) if m else "?", "deleted": m.group(2) if m else "?", "samples": []}
    rc2, so2, _ = run2(["git", "-C", repo, "diff", "HEAD", "-U0", "--", r], timeout=120)
    for ln in (so2 or "").splitlines():
        if (ln.startswith("+") or ln.startswith("-")) and not ln.startswith(("+++", "---")):
            out["samples"].append(ln[:160])
            if len(out["samples"]) >= 6:
                break
    return out


def bad_json_scan(via: Path, max_bytes: int = 400000) -> list:
    """VCGC 會讀的小 JSON 逐檔 json.loads(只讀):registry 冊 · VIA_Reports/vcgc · .via → 壞的回 [{file, line, col, char, msg}]。"""
    bad = []
    roots = [via / "supportive modules" / "registry", via / "VIA_Reports" / "vcgc", via / ".via", via.parent / ".via"]
    for root in roots:
        if not root.is_dir():
            continue
        for p in root.rglob("*.json"):
            try:
                if p.stat().st_size > max_bytes:
                    continue
                json.loads(p.read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError as exc:
                bad.append({"file": str(p.relative_to(via.parent)), "line": exc.lineno, "col": exc.colno, "char": exc.pos, "msg": exc.msg[:80]})
            except OSError:
                bad.append({"file": str(p), "msg": "讀不到"})
    return bad


def branch_tails(via: Path) -> dict:
    """分支 origin/<BRANCH> 上每個家族的尾版號(git ls-tree · 只讀);取不到回 {}。"""
    rc, so, _ = run2(["git", "-C", via.parent, "ls-tree", "-r", "--name-only", "origin/" + BRANCH, "--", "VeritasIntelligenceAnalytics/"], timeout=300)
    if rc != 0:
        return {}
    names = so.splitlines()
    out = {}
    for fam, (folder, prefix) in FAMILIES.items():
        pre = "VeritasIntelligenceAnalytics/" + folder + "/"
        vs = [vnum(n) for n in names if n.startswith(pre) and n.endswith(".py") and Path(n).name.startswith(prefix)]
        vs = [v for v in vs if v >= 0]
        out[fam] = max(vs) if vs else None
    return out


# ---------------------------------------------------------------- AST 全景 · AST 定位
def ast_scan(paths) -> dict:
    """每檔 ast.parse + compile(只在記憶體 · 不執行)→ 錯誤位置;編譯警告(如無效跳脫)記檔:行,不印、不算錯。"""
    import warnings
    bad, warns = [], []
    for p in paths:
        try:
            src = Path(p).read_text(encoding="utf-8-sig")
        except OSError as exc:
            bad.append({"file": str(p), "kind": "READ", "msg": type(exc).__name__})
            continue
        try:
            with warnings.catch_warnings(record=True) as ws:
                warnings.simplefilter("always")
                compile(ast.parse(src, filename=str(p)), str(p), "exec")
            warns += [{"file": Path(p).name, "line": w.lineno, "msg": str(w.message)[:120]} for w in ws]
        except SyntaxError as exc:
            bad.append({"file": str(p), "kind": "SYNTAX", "line": exc.lineno, "msg": exc.msg})
        except (ValueError, TypeError) as exc:
            bad.append({"file": str(p), "kind": "COMPILE", "msg": str(exc)[:160]})
    return {"files": len(paths), "errors": bad, "warnings": warns}


def enclosing_def(path: Path, line: int) -> dict:
    """AST 定位:這一行在哪個 def / class 裡(最內層)+ 原文那一行。"""
    try:
        src = Path(path).read_text(encoding="utf-8-sig")
        tree = ast.parse(src)
    except (OSError, SyntaxError, ValueError):
        return {"def": None, "src": None}
    best = None
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.lineno <= line <= (n.end_lineno or n.lineno):
            if best is None or n.lineno >= best.lineno:
                best = n
    lines = src.splitlines()
    return {"def": ("%s (L%d-%d)" % (best.name, best.lineno, best.end_lineno)) if best else "<module>",
            "src": lines[line - 1].strip()[:200] if 0 < line <= len(lines) else None}


def _defined_names(tree) -> set:
    names = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        for x in ast.walk(n):
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store):
                names.add(x.id)
            elif isinstance(x, ast.alias):
                names.add((x.asname or x.name).split(".")[0])
            elif isinstance(x, ast.Global):
                names.update(x.names)
            elif isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "setattr" and len(x.args) >= 2 \
                    and isinstance(x.args[1], ast.Constant) and isinstance(x.args[1].value, str):
                names.add(x.args[1].value)
    return names


def attr_trace(files, attr: str) -> dict:
    """同家族每一版:誰定義 attr、誰去讀它(X.attr / getattr(X, 'attr'))· 只讀 AST。"""
    defined, used = [], []
    for p in files:
        try:
            tree = ast.parse(Path(p).read_text(encoding="utf-8-sig"))
        except (OSError, SyntaxError, ValueError):
            continue
        if attr in _defined_names(tree):
            defined.append(Path(p).name)
        for n in ast.walk(tree):
            hit = (isinstance(n, ast.Attribute) and n.attr == attr) or (
                isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("getattr", "hasattr")
                and len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) and n.args[1].value == attr)
            if hit:
                used.append("%s:L%d" % (Path(p).name, n.lineno))
    first_def = min((vnum(Path(x)) for x in defined), default=None)
    early = [u for u in used if first_def is None or vnum(Path(u.split(":")[0])) <= first_def]
    return {"attr": attr, "defined_in": defined, "used_at": used[:40], "used_before_defined": early[:20]}


def diagnose(text: str, via: Path | None = None) -> dict:
    """Traceback → 例外 · 每一框(AST 定位)· 前版鏈轉手 · 屬性缺 → 同家族誰定義 / 誰讀。"""
    frames = [m.groupdict() for m in FRAME_RX.finditer(text or "")]
    exc = None
    for ln in reversed((text or "").splitlines()):
        m = EXC_RX.match(ln.strip())
        if m and "Warning" not in m.group("type"):
            exc = {"type": m.group("type"), "msg": (m.group("msg") or "").strip()}
            break
    out = {"exception": exc, "frames": [], "recursion": False, "hint": ""}
    for f in frames[-12:]:
        p = Path(f["file"])
        loc = enclosing_def(p, int(f["line"])) if p.is_file() else {"def": None, "src": None}
        out["frames"].append({"file": p.name, "line": int(f["line"]), "func": f["func"], **loc})
    names = [(f["file"], f["line"]) for f in frames]
    out["recursion"] = len(names) > 40 and len(set(names[-40:])) <= 4 or "RecursionError" in (exc or {}).get("type", "")
    hops = [f for f in out["frames"] if f["func"] == "__getattr__"]
    if exc and exc["type"].endswith("AttributeError"):
        m = ATTR_RX.search(exc["msg"])
        attr = m.group("attr") if m else None
        out["attr"] = attr
        fam_files = []
        if attr and frames:
            stem = re.sub(r"_v\d+$", "", Path(frames[-1]["file"]).stem)
            folder = Path(frames[-1]["file"]).parent
            if folder.is_dir():
                fam_files = sorted((p for p in folder.glob(stem + "_v*.py") if vnum(p) >= 0), key=vnum)
            out["trace"] = attr_trace(fam_files, attr) if fam_files else None
        tr = out.get("trace") or {}
        if attr and tr.get("defined_in") == []:
            out["hint"] = "屬性 %s 整個家族都沒有定義 → 讀它的那一版(%s)要改成先檢查或出新版補定義" % (attr, ", ".join(tr.get("used_at", [])[:3]) or "?")
        elif attr and tr.get("used_before_defined"):
            out["hint"] = "屬性 %s 最早在 %s 定義,但更早的版就在讀(%s)→ 前版鏈轉手 %d 次後落到沒有它的那一版" % (
                attr, tr["defined_in"][0], ", ".join(tr["used_before_defined"][:3]), len(hops))
        elif attr:
            out["hint"] = "屬性 %s 經前版鏈轉手 %d 次後找不到 → 看 frames 第一個非 __getattr__ 的框(呼叫端)" % (attr, len(hops))
    elif out["recursion"]:
        out["hint"] = "遞迴:同幾框反覆出現(前版鏈互指或 __getattr__ 自己找自己)"
    elif exc:
        out["hint"] = "%s:看最後一框 %s" % (exc["type"], (out["frames"][-1]["file"] + ":%d" % out["frames"][-1]["line"]) if out["frames"] else "?")
    return out


# ---------------------------------------------------------------- 各階段
def stage_scan(via: Path, ctx: dict) -> None:
    tick("①")
    env = {"python": sys.version.split()[0], "exe": sys.executable, "pwsh": shutil.which("pwsh") or shutil.which("pwsh.exe"), "free_gb": free_gb()}
    for mod in ("duckdb", "pyarrow", "polars", "pandas", "fitz", "pypdfium2"):
        try:
            m = __import__(mod)
            env[mod] = getattr(m, "__version__", "ok")
        except Exception:                              # noqa: BLE001 — 只量有沒有
            env[mod] = None
    ctx["env"] = env
    miss = [k for k in ("duckdb", "pyarrow") if not env[k]]
    say("YELLOW" if miss else "GREEN", "① 環境", "Python %s · duckdb %s · pyarrow %s · polars %s · pwsh %s · 可用記憶體 %s GB" % (
        env["python"], env["duckdb"], env["pyarrow"], env["polars"], "有" if env["pwsh"] else "沒有", env["free_gb"]),
        ("缺 %s → VDF 表頭 / 增量庫 / Parquet 自測會紅(經 VCGC 環境工具裝);VQG 另找有 duckdb + polars 的 Python" % " · ".join(miss)) if miss else "")
    fams = {}
    allfiles = []
    for fam, (folder, prefix) in FAMILIES.items():
        fs = family_files(via, folder, prefix)
        allfiles += fs
        fams[fam] = {"tail": fs[-1].name if fs else None, "versions": len(fs)}
    sc = ast_scan(allfiles)
    bt = branch_tails(via)
    behind = []
    for fam, v in fams.items():
        v["branch_tail"] = bt.get(fam)
        tv = vnum(v["tail"]) if v["tail"] else -1
        if bt.get(fam) and tv < bt[fam]:
            behind.append("%s v%04d←v%04d" % (fam, max(tv, 0), bt[fam]))
    ctx["families"], ctx["ast"], ctx["behind_branch"] = fams, sc, behind
    say("RED" if sc["errors"] else ("YELLOW" if behind else "GREEN"), "② AST 全景", "家族 %d · 檔 %d · 語法 / 編譯錯 %d · 編譯警告 %d(凍結版不改 · 檔:行在報告)· 尾版 %s%s" % (
        len(fams), sc["files"], len(sc["errors"]), len(sc["warnings"]), " · ".join("%s=%s" % (k, (v["tail"] or "—").rsplit("_v", 1)[-1].replace(".py", "")) for k, v in fams.items()),
        (" · 工作樹落後分支 %d 家族:%s" % (len(behind), " · ".join(behind))) if behind else (" · 與分支尾版一致" if bt else "")),
        "錯誤位置在報告 ast.errors(檔:行)" if sc["errors"] else ("落後的家族要 ③ 同步成功才會更新(④ / ⑥ 在舊版上紅不算數)" if behind else ""))


def stage_sync(via: Path, ctx: dict, do_sync: bool) -> None:
    tick("③")
    repo = via.parent
    st = git_state(repo)
    ctx["git_before"] = st
    if st.get("error"):
        say("RED", "③ 同步", st["error"])
        return
    br = st.get(BRANCH) or {}
    behind, ahead = br.get("remote_only"), br.get("local_only")
    txt = "分支 %s · HEAD %s · 比 GitHub 少 %s 個提交 · 多 %s 個沒推 · 改動 %d · 未追蹤 %d" % (st["branch"], st["head"], behind, ahead, st["dirty_tracked"], st["untracked"])
    if not do_sync or not behind:
        say("GREEN" if not behind else "YELLOW", "③ 同步", txt + (" · 已一致" if not behind else " · 這次不同步(--no-sync)"))
        return
    dirty = st.get("dirty_files") or []
    xy = st.get("dirty_xy") or {}
    classes = {}
    for x in dirty:
        classes.setdefault(classify_dirty(repo, x, xy=xy.get(x)), []).append(x)
    others = classes.get("other") or []
    restored, fixed_json, frozen_fixed = [], [], []
    for x in list(classes.get("frozen") or []):                           # 改了的非尾版(凍結):備份桌機版 → 還原 HEAD(可回滾)
        fp = repo / _norm_rel(x)
        bk = via / "VIA_Reports" / "settle" / "frozen_version_backup"
        try:
            bk.mkdir(parents=True, exist_ok=True)
            if fp.is_file():
                shutil.copy2(fp, bk / (fp.name + "." + _dt.datetime.now().strftime("%Y%m%d_%H%M%S") + ".desktop"))
        except OSError:
            continue
        if run(["git", "-C", repo, "checkout", "HEAD", "--", x])[0] == 0:
            frozen_fixed.append(x)
            classes["frozen"].remove(x)
    for x in classes.get("deleted") or []:                               # 刪掉的已發布版本:從 HEAD 還原(檔在 git 裡 · 零損失)
        if run(["git", "-C", repo, "checkout", "HEAD", "--", x])[0] == 0:
            restored.append(x)
    for k in ("state", "receipt"):
        for x in list(classes.get(k) or []):
            fp = repo / _norm_rel(x)
            if fp.suffix.lower() != ".json" or not fp.is_file():
                continue
            try:
                json.loads(fp.read_text(encoding="utf-8-sig"))
            except (ValueError, OSError):
                bk = via / "VIA_Reports" / "settle" / "broken_json_backup"
                bk.mkdir(parents=True, exist_ok=True)
                shutil.copy2(fp, bk / (fp.name + "." + _dt.datetime.now().strftime("%Y%m%d_%H%M%S") + ".broken"))
                if run(["git", "-C", repo, "checkout", "HEAD", "--", x])[0] == 0:
                    fixed_json.append(x)
                    classes[k].remove(x)
    if restored:
        classes["deleted"] = []
    ctx["sync_dirty"] = {"classes": {k: v[:80] for k, v in classes.items()}, "counts": {k: len(v) for k, v in classes.items()}, "others": others[:80],
                         "restored_deleted": restored[:80], "fixed_broken_json": fixed_json, "restored_frozen": frozen_fixed[:80], "untracked": untracked_summary(st.get("untracked_files") or [])}
    if restored or fixed_json or frozen_fixed:
        print("[計] ③ 從 HEAD 還原:刪掉的已發布版本 %d 支 · 壞 JSON 冊 %d 本 · 改了的凍結版 %d 支(原件備份在 VIA_Reports/settle/broken_json_backup · frozen_version_backup)" % (len(restored), len(fixed_json), len(frozen_fixed)), flush=True)
    cnt = " · ".join("%s %d" % kv for kv in sorted(ctx["sync_dirty"]["counts"].items()))
    if others:
        ctx["sync_dirty"]["other_diff"] = [dict(other_diff(repo, x), xy=(st.get("dirty_xy") or {}).get(x)) for x in others[:12]]
        say("YELLOW", "③ 同步", txt + " · 改動分類 %s · 真的改了程式 / 冊的 %d 個(%s)→ 不合併(不動你的檔)" % (
            cnt, len(others), " · ".join(Path(x).name for x in others[:5]) + (" …" if len(others) > 5 else "")),
            "這些檔要你決定:提交(git add / commit)或還原(git checkout -- <檔>)後再跑本檔;全清單在報告 sync_dirty.others · 其他類別本檔會自己 stash 放回")
        return
    stash_paths = [x for k, v in classes.items() if k not in ("other", "deleted", "frozen") for x in v]
    stashed = False
    if stash_paths:
        rc, out = run(["git", "-C", repo, "stash", "push", "-q", "-m", "VIA_SettleAll receipts", "--", *stash_paths], timeout=300)
        if rc != 0:
            ctx["sync_error"] = out[-2000:]
            say("RED", "③ 同步", txt + " · 改動 %d 個 stash 不成功 → 不合併" % len(stash_paths), "把貼回包上傳給 AI(sync_error)")
            return
        stashed = True
    rc, out = run(["git", "-C", repo, "merge", "--no-edit", "origin/" + BRANCH], timeout=600)
    if rc != 0:
        run(["git", "-C", repo, "merge", "--abort"])
        if stashed:
            run(["git", "-C", repo, "stash", "pop", "-q"], timeout=300)
        ctx["sync_error"] = out[-3000:]
        say("RED", "③ 同步", txt + " · 合併沒成功 → 已 merge --abort 還原(改動已放回)", "把貼回包上傳給 AI(合併衝突的檔名在 sync_error)")
        return
    pop_note = ""
    if stashed:
        rc2, out2 = run(["git", "-C", repo, "stash", "pop", "-q"], timeout=300)
        if rc2 != 0:
            rc3, out3 = run(["git", "-C", repo, "diff", "--name-only", "--diff-filter=U"])
            conflicted = [x for x in out3.splitlines() if x.strip()] if rc3 == 0 else []
            kept = {}
            cls_of = {x: k for k, v in classes.items() for x in v}
            for x in conflicted:
                side = CONFLICT_KEEP.get(cls_of.get(_norm_rel(x), "receipt"), "ours")
                run(["git", "-C", repo, "checkout", "--" + side, "--", x])       # theirs = stash = 桌機 · ours = 合併後的分支版
                kept[x] = "桌機版" if side == "theirs" else "分支版"
            run(["git", "-C", repo, "reset", "-q"])
            run(["git", "-C", repo, "stash", "drop", "-q"])
            ctx["sync_dirty"]["conflicted"] = kept
            pop_note = " · 改動 %d 個放回(%d 個與分支衝突:%s)" % (len(stash_paths), len(conflicted), " · ".join("%s→%s" % (Path(k).name, v) for k, v in list(kept.items())[:4]))
        else:
            pop_note = " · 改動 %d 個放回(%s)" % (len(stash_paths), cnt)
    if restored or fixed_json or frozen_fixed:
        pop_note += " · 從 HEAD 還原:刪掉的舊版 %d · 壞 JSON %d · 改了的凍結版 %d" % (len(restored), len(fixed_json), len(frozen_fixed))
    st2 = git_state(repo, fetch=False)
    ctx["git_after"] = st2
    say("GREEN", "③ 同步", "合併 origin/%s 成功(不 rebase · 不強推 · 桌機的提交保留)· HEAD %s → %s%s" % (BRANCH, st["head"], st2["head"], pop_note),
        "桌機自己的 %s 個提交還沒推 → 照 ChainShip 上船或 git push(你決定)" % ahead if ahead else "")


def _tail(via: Path, fam: str) -> Path | None:
    folder, prefix = FAMILIES[fam]
    fs = family_files(via, folder, prefix)
    return fs[-1] if fs else None


def stale_tree(ctx: dict) -> str:
    """③ 沒合併成功且工作樹落後分支 → 回原因字串(④ ⑥ 不在舊版上跑);否則空。"""
    gb = (ctx.get("git_before") or {}).get(BRANCH) or {}
    merged = bool(ctx.get("git_after"))
    if not merged and (gb.get("remote_only") or 0) > 0 and ctx.get("behind_branch"):
        return "工作樹落後分支 %s 提交且 ③ 沒合併(%s)" % (gb.get("remote_only"), " · ".join(ctx["behind_branch"][:3]))
    return ""


def stage_vdf(via: Path, ctx: dict, force_old: bool = False) -> None:
    tick("④")
    why = stale_tree(ctx)
    if why and not force_old:
        ctx["vdf"] = {"skipped": why}
        say("YELLOW", "④ VDF ui", "不在舊版上跑:%s" % why, "先讓 ③ 同步成功(或 --force-old-tree 逼跑)")
        return
    t = _tail(via, "VDF_SystemManager")
    if not t:
        say("RED", "④ VDF ui", "找不到 VDF_SystemManager 尾版")
        return
    rc, out = run([sys.executable, t, "ui"], cwd=t.parent, timeout=1800)
    ctx["vdf"] = {"tail": t.name, "rc": rc, "out_tail": out[-6000:]}
    lamps = re.findall(r"·\s*(GREEN|YELLOW|RED)\s*$", out, re.M)
    if rc == 0:
        lp = vdf_lamp(rc, lamps)
        say(lp, "④ VDF ui", "%s ui · rc 0 · 燈 %s" % (t.name, " ".join(lamps[-6:]) or "—"),
            "頁上有 %s 段 → 看 VDF 頁該段的原因(不是假綠)" % lp if lp != "GREEN" else "")
        return
    d = diagnose(out, via)
    ctx["vdf"]["diagnosis"] = d
    e = d.get("exception") or {}
    lag = [b for b in (ctx.get("behind_branch") or []) if b.startswith("VDF_SystemManager ")]
    say("RED", "④ VDF ui", "%s ui · rc %s · %s: %s" % (t.name, rc, e.get("type", "?"), (e.get("msg") or "")[:160]),
        (("工作樹 %s 落後分支(分支尾版容器 ui 綠)→ 先讓 ③ 同步成功再跑 · " % lag[0]) if lag else "") + "AST 定位:" + (d.get("hint") or "見報告 vdf.diagnosis") + " · 把貼回包上傳給 AI")


def _read_vrn_closeout(via: Path) -> tuple:
    cj = via / "VIA_Reports" / "vrn2" / "VRN2_CloseoutUI_latest.json"
    try:
        c = json.loads(cj.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, cj
    state = {"state": c.get("state"), "at": c.get("at") or c.get("ts") or c.get("generated_at"),
             "per_owner": {o: sum(1 for i in c.get("items") or [] if i.get("owner") == o) for o in ("VRN-2", "VCGC", "人工", "資料源")}}
    return state, cj


def stage_vrn(via: Path, ctx: dict, mode: str) -> None:
    tick("⑤")
    if mode == "skip":
        say("GRAY", "⑤ VRN", "這次不跑(--vrn skip)")
        return
    if mode == "status":
        state, cj = _read_vrn_closeout(via)
        ctx["vrn"] = {"mode": "status", "closeout": state, "closeout_file": str(cj)}
        lamp = vrn_status_lamp(state)
        say(lamp, "⑤ VRN", "只讀 VRN-2 自己的收尾收據 · 狀態 %s · 負責方 %s · 時間 %s(不重跑那輪;要重跑 --vrn repair)" % (
            (state or {}).get("state", "沒收據"), (state or {}).get("per_owner"), (state or {}).get("at")),
            "" if lamp == "GREEN" else ("VRN-2 側有待修 → 跑 --vrn repair" if lamp == "RED" else "REVIEW = 看收尾頁人工項原文後 --confirm · DATA_GAP = 外部資料源沒有(已附證據 · VRN-2 側結案)"))
        return
    t = _tail(via, "VRN2_RoundAll")
    if not t:
        say("RED", "⑤ VRN", "找不到 VRN2_RoundAll")
        return
    only = "package,fix,report,closeout,pasteback" if mode == "repair" else "package,preflight,selftest"
    t0 = _dt.datetime.now().timestamp()
    rc, out = run([sys.executable, t, "--root", via, "--only", only, "--no-open"], cwd=t.parent, timeout=14400)
    state, cj = _read_vrn_closeout(via)
    try:
        fresh = cj.stat().st_mtime >= t0 - 1
    except OSError:
        fresh = False
    nxt = [ln for ln in out.splitlines() if ln.startswith("NEXT:")]
    ctx["vrn"] = {"mode": mode, "roundall": t.name, "rc": rc, "closeout": state, "closeout_fresh": fresh, "next": nxt[-1] if nxt else None, "out_tail": out[-4000:]}
    lamp = vrn_lamp(rc, state, fresh)
    say(lamp, "⑤ VRN", "%s %s · rc %s · 收尾 %s %s%s" % (t.name, mode, rc, (state or {}).get("state"), (state or {}).get("per_owner"),
        "" if fresh else " · 收尾收據不是本次寫的(舊的 · 不拿來判綠)"),
        "REVIEW = 看收尾頁人工項原文後 --confirm(只有你打才算)" if state and state["state"] == "REVIEW" else ("把貼回包上傳給 AI" if lamp == "RED" else ""))


def stage_vcgc(via: Path, ctx: dict, force_old: bool = False) -> None:
    tick("⑥")
    why = stale_tree(ctx)
    if why and not force_old:
        bj = bad_json_scan(via)
        ctx["vcgc"] = {"skipped": why, "bad_json": bj}
        say("YELLOW" if not bj else "RED", "⑥ VCGC", "不在舊版上跑:%s%s" % (why, (" · 壞 JSON %d:%s" % (len(bj), " · ".join("%s(行 %s 列 %s)" % (Path(b["file"]).name, b.get("line"), b.get("col")) for b in bj[:4]))) if bj else " · 小 JSON 全部讀得過"),
            ("壞 JSON 是桌機主控台 rc 1 的原因 → 還原或修那本冊 · " if bj else "") + "先讓 ③ 同步成功(或 --force-old-tree 逼跑)")
        return
    t = _tail(via, "CGC_MDL149_Console")
    if not t:
        say("RED", "⑥ VCGC", "找不到 VCGC 主控台")
        return
    rc1, out1 = run([sys.executable, t, "handoff", "check"], cwd=via.parent, timeout=1200)
    kinds = {}
    for k in re.findall(r"^\[RED\] ([A-Z_]+) ", out1, re.M):
        kinds[k] = kinds.get(k, 0) + 1
    rc2, out2 = run([sys.executable, t, "test", "--quick"], cwd=via.parent, timeout=3600)
    m = re.search(r"\[VCGC 全功能串測\] (\w+) · ([^\n]{0,160})", out2)
    reds = re.findall(r"^\s*\[RED\s*\]\s+(\S+)", out2, re.M)
    first_red = lambda s: next((ln.strip()[:200] for ln in s.splitlines() if ln.strip().startswith("[RED")), None)  # noqa: E731
    ctx["vcgc"] = {"handoff_rc": rc1, "handoff_red": kinds, "test_rc": rc2, "test_line": m.group(0) if m else None, "test_red": reds,
                   "handoff_first_red": first_red(out1), "test_first_red": first_red(out2), "handoff_out_tail": out1[-2500:], "test_out_tail": out2[-2500:]}
    ctx["vcgc"]["events"] = vcgc_events(via)
    if any("JSONDecodeError" in (e.get("error") or "") for e in ctx["vcgc"]["events"]) or "JSONDecodeError" in (out1 + out2):
        ctx["vcgc"]["bad_json"] = bad_json_scan(via)
    ev_err = next((e for e in reversed(ctx["vcgc"]["events"]) if e.get("error") or e.get("outcome") == "FAIL"), None)
    lamp = vcgc_lamp(m.group(1) if m else None, rc2, rc1, kinds)
    lag = [b for b in (ctx.get("behind_branch") or []) if b.startswith("CGC_")]
    bj = ctx["vcgc"].get("bad_json") or []
    bj_txt = (" · 壞 JSON:%s" % " · ".join("%s(行 %s 列 %s)" % (Path(b["file"]).name, b.get("line"), b.get("col")) for b in bj[:4])) if bj else ""
    why = "" if m else (" · 第一行紅:%s" % (ctx["vcgc"]["test_first_red"] or ctx["vcgc"]["handoff_first_red"] or (
        ("事件冊 %s %s rc %s:%s" % (ev_err.get("target"), ev_err.get("outcome"), ev_err.get("rc"), (ev_err.get("error") or (ev_err.get("lesson") or {}).get("sig") or "")[:160])) if ev_err else "(輸出裡沒有 [RED] 行 · 事件冊也沒有錯 · 看報告 vcgc.test_out_tail)")))
    say(lamp, "⑥ VCGC", "串測 %s · 紅站 %s · 交接閘 rc %s · 紅 %s%s" % (
        (m.group(2)[:90] if m else "沒讀到總行"), ", ".join(reds) or "0", rc1, " · ".join("%s %d" % kv for kv in sorted(kinds.items())) or "0", why + bj_txt),
        (("工作樹 VCGC 家族落後分支(%s)→ 先讓 ③ 同步成功再看 · " % " · ".join(lag)) if lag else "") + ("VCGC 的 closeout_lamp 才是 VCGC 驗收;交接閘紅多為歷史版本沒有測試收據(逐案補或裁定)" if kinds else ""))


def vcgc_events(via: Path, n: int = 6) -> list:
    """VCGC 自己的事件冊(VIA_Reports/vcgc/events/EVENTS_<日>.jsonl)最後 n 筆的 verb / target / rc / outcome / error(只讀)。"""
    d = via / "VIA_Reports" / "vcgc" / "events"
    files = sorted(d.glob("EVENTS_*.jsonl")) if d.is_dir() else []
    if not files:
        return []
    out = []
    try:
        lines = files[-1].read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    for ln in lines[-n:]:
        try:
            e = json.loads(ln)
        except ValueError:
            continue
        out.append({k: e.get(k) for k in ("ts", "verb", "act", "target", "rc", "outcome", "secs")} | {"error": str(e.get("error") or "")[:300], "lesson": e.get("lesson")})
    return out


def graphify_workers(free_start_gb: float, estimate_gb: int) -> int:
    """可用記憶體 < 估計 + 2 GB → 1 個 worker(峰值約減半 · 慢一點);否則 2(v0101 一行的值)。量不到 → 2。"""
    return 1 if (free_start_gb >= 0 and free_start_gb < estimate_gb + 2) else 2


def graphify_exe() -> tuple:
    """(隔離環境, graphify 可執行檔):VIA_GRAPHIFY_VENV 或 ~/envs/via_graphify(Graphify v0101 一行建的)。"""
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    venv = Path(os.environ.get("VIA_GRAPHIFY_VENV") or (home / "envs" / "via_graphify"))
    return venv, venv / ("Scripts/graphify.exe" if os.name == "nt" else "bin/graphify")


def graph_is_fresh(src: Path, gj: Path) -> bool:
    """上一張 graph.json 比該系統夾裡最新的 .py / .ps1 還新 → 沒變 · 沿用。"""
    if not gj.is_file():
        return False
    try:
        g = gj.stat().st_mtime
        newest = max((p.stat().st_mtime for p in src.rglob("*") if p.suffix.lower() in (".py", ".ps1") and p.is_file()), default=0.0)
    except OSError:
        return False
    return newest <= g


def stage_graphify(via: Path, ctx: dict, floor_gb: float = 0.75, gx_cmd: list | None = None, out_root: Path | None = None, mode: str = "changed") -> None:
    tick("⑦")
    venv, gx = graphify_exe()
    if mode == "skip":
        ctx["graphify"] = {"lamp": "GRAY", "why": "--graphify skip"}
        say("GRAY", "⑦ Graphify", "這次不跑(--graphify skip)")
        return
    cmd0 = list(gx_cmd) if gx_cmd else [gx]
    out_root = out_root or Path(os.environ.get("VIA_GRAPHIFY_OUT") or (via / "VIA_Reports" / "graphify"))
    if not gx_cmd and not gx.is_file():
        ctx["graphify"] = {"lamp": "GRAY", "venv": str(venv), "why": "no graphify"}
        say("GRAY", "⑦ Graphify", "隔離環境 %s 沒有 graphify → 跳過(不裝 · 不連網)" % venv, "先貼 Graphify v0101 一行(docs/handoff/ai/via_graphify_v0101)建隔離環境,再跑本檔")
        return
    only = [s for s in re.split(r"[,; ]+", os.environ.get("VIA_GRAPHIFY_ONLY", "")) if s]
    env = {"GRAPHIFY_BACKEND": "none", "GRAPHIFY_QUERY_LOG_DISABLE": "1"}
    exa = [x for ex in GRAPHIFY_EXCLUDES for x in ("--exclude", ex)]
    res, t_all = [], time.time()
    for name, rel, gb in GRAPHIFY_SYSTEMS:
        if only and name not in only:
            continue
        src = via / rel
        if not src.is_dir():
            res.append({"system": name, "lamp": "GRAY", "why": "folder missing"})
            continue
        f0 = free_gb()
        gj0 = out_root / name / "graphify-out" / "graph.json"
        if mode == "changed" and graph_is_fresh(src, gj0):
            try:
                g = json.loads(gj0.read_text(encoding="utf-8")); nn, ne = len(g.get("nodes") or []), len(g.get("links") or g.get("edges") or [])
            except (OSError, ValueError):
                nn, ne = 0, 0
            res.append({"system": name, "lamp": "GREEN", "reused": True, "nodes": nn, "edges": ne, "seconds": 0, "graph": str(gj0), "html": str(gj0.with_name("graph.html")), "why": "程式沒變 · 沿用上一張"})
            print("[GREEN] ⑦ %s · 沿用上一張(程式沒變)· 節點 %d · 連線 %d · 0 秒" % (name, nn, ne), flush=True)
            continue
        if 0 <= f0 < gb and mode != "all":
            res.append({"system": name, "lamp": "YELLOW", "why": "free RAM %.2f GB < v0101 估 %d GB → 這次不跑(實測會被殺 · 省 15 分)" % (f0, gb), "free_start_gb": f0})
            print("[YELLOW] ⑦ %s · 可用 %.2f GB < 估 %d GB → 不跑(--graphify all 才硬跑)" % (name, f0, gb), flush=True)
            continue
        if 0 <= f0 < max(floor_gb, 1.0):
            res.append({"system": name, "lamp": "YELLOW", "why": "free RAM %.2f GB < %.2f GB(連啟動都不夠)" % (f0, max(floor_gb, 1.0))})
            print("[YELLOW] ⑦ %s · 可用記憶體 %.2f GB 連啟動都不夠 · 跳過" % (name, f0), flush=True)
            continue
        o = out_root / name
        o.mkdir(parents=True, exist_ok=True)
        workers = graphify_workers(f0, gb)
        print("[計] ⑦ %s · %s · 可用記憶體 %s GB(v0101 估 %d GB · worker %d · 看門狗下限 %.2f GB)· 抽取中" % (name, src, f0, gb, workers, floor_gb), flush=True)
        r = run_watched(cmd0 + ["extract", src, "--code-only", "--max-workers", str(workers), "--out", o] + exa, env=env, floor_gb=floor_gb, timeout=7200)
        rc, peak, mfree, killed, secs = r["rc"], r["peak_rss_gb"], r["min_free_gb"], r["killed"], r["seconds"]
        phase = "extract"
        tail = r["out"][-1500:]
        if rc == 0:
            phase = "cluster"
            r2 = run_watched(cmd0 + ["cluster-only", o, "--no-label"], env=env, floor_gb=floor_gb, timeout=3600)
            rc, killed, secs = r2["rc"], r2["killed"], secs + r2["seconds"]
            peak, mfree = max(peak, r2["peak_rss_gb"]), min(mfree, r2["min_free_gb"]) if mfree >= 0 else r2["min_free_gb"]
            tail += r2["out"][-1500:]
        gj = o / "graphify-out" / "graph.json"
        used = round(max(0.0, f0 - mfree), 2) if (f0 >= 0 and mfree >= 0) else None
        row = {"system": name, "seconds": secs, "phase": phase, "workers": workers, "used_est_gb": used, "launcher_rss_gb": peak, "min_free_gb": mfree, "free_start_gb": f0, "estimate_gb_v0101": gb}
        if killed:
            row.update(lamp="YELLOW", why="%s 階段 · %s" % (phase, killed), rc=rc)
            print("[YELLOW] ⑦ %s · %s 階段 · %s · 吃掉(估)%s GB(起始可用 %.2f → 最低 %.2f)" % (name, phase, killed, used, f0, mfree), flush=True)
        elif rc != 0 or not gj.is_file():
            row.update(lamp="RED", rc=rc, out_tail=tail)
            print("[RED] ⑦ %s · rc %s · 沒有圖(graphify 的訊息在報告)" % (name, rc), flush=True)
        else:
            try:
                g = json.loads(gj.read_text(encoding="utf-8"))
                nn, ne = len(g.get("nodes") or []), len(g.get("links") or g.get("edges") or [])
            except (OSError, ValueError):
                nn, ne = 0, 0
            if nn <= 0:
                row.update(lamp="RED", why="graph.json has 0 nodes")
                print("[RED] ⑦ %s · graph.json 讀不出節點" % name, flush=True)
            else:
                row.update(lamp="GREEN", nodes=nn, edges=ne, html=str(o / "graphify-out" / "graph.html"), report=str(o / "graphify-out" / "GRAPH_REPORT.md"), graph=str(gj))
                print("[GREEN] ⑦ %s · 節點 %d · 連線 %d · %d 秒 · 吃掉(估)%s GB · 最低可用 %.2f GB" % (name, nn, ne, secs, used, mfree), flush=True)
        res.append(row)
    out_root.mkdir(parents=True, exist_ok=True)
    rec = {"tool": "graphifyy", "engine": "%s %s (graphify stage · v0101 line commands + memory watchdog)" % (NAME, VERSION), "root": str(via),
           "mode": "code-only · GRAPHIFY_BACKEND=none · offline · one graph per system", "excludes": list(GRAPHIFY_EXCLUDES),
           "watchdog": {"floor_gb": floor_gb, "rule": "每秒量可用記憶體 · 可用 < 下限就殺整棵 · 吃掉(估)= 起始可用 − 最低可用(graphify 殼的 RSS 量不到 worker · 只當參考)"},
           "systems": res, "seconds": int(time.time() - t_all), "at": _dt.datetime.now().isoformat(timespec="seconds")}
    (out_root / "VIA_Graphify_latest.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    ctx["graphify"] = rec
    lamp = graphify_lamp(res)
    g_ok = [r for r in res if r.get("lamp") == "GREEN"]
    ylw = [r for r in res if r.get("lamp") == "YELLOW"]
    say(lamp, "⑦ Graphify", "綠 %d · 黃 %d · 紅 %d · 灰 %d · %d 秒 · 收據 %s" % (
        len(g_ok), len(ylw), sum(1 for r in res if r.get("lamp") == "RED"), sum(1 for r in res if r.get("lamp") == "GRAY"), rec["seconds"], out_root / "VIA_Graphify_latest.json"),
        ("看門狗中止的:%s → 這台機器可用記憶體不夠這張圖(實測吃到被殺 · v0101 估的 6 GB 看來是對的):關掉瀏覽器 / Office / OneDrive 同步,可用 ≥ 6 GB 再跑 `$env:VIA_GRAPHIFY_ONLY='%s'`(本版可用 < 估計 + 2 GB 已自動改 1 個 worker)" % (
            " · ".join("%s(%s · 吃掉(估)%s GB)" % (r["system"], r.get("why"), r.get("used_est_gb")) for r in ylw), ",".join(r["system"] for r in ylw))) if ylw else "")


def stage_vqg(via: Path, ctx: dict) -> None:
    tick("⑧")
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    dl = home / "Downloads" if (home / "Downloads").is_dir() else Path(tempfile.gettempdir())
    files, how = fetch_set(via, VQG_FILES, dl / ("VIA_Settle_" + VERSION) / "VQG")
    info = {"files_from": how}
    ctx["vqg"] = info
    if not files:
        say("RED", "⑧ VQG", "取不到 VQG v0104 / v0105 · %s" % how, "git -C <倉> fetch origin %s 後再跑;SHA 不符 = 檔被改過,不跑" % BRANCH)
        return
    v0105 = [p for p in files if p.name.endswith("_v0105.py")][0]
    py = find_python_with(("duckdb", "polars"))
    info["python"] = str(py) if py else None
    if not py:
        say("RED", "⑧ VQG", "找不到有 duckdb + polars 的 Python(VQG 不 pip)", "VCGC:via-install duckdb polars(或 $env:VQG_PY 指定)")
        return
    rc0, so0, _ = run2(["git", "-C", via.parent, "ls-tree", "--name-only", "origin/" + BRANCH, "VeritasIntelligenceAnalytics/functional modules/VDF/"], timeout=120)
    branch_book = None
    if rc0 == 0:
        names = sorted((n for n in so0.splitlines() if re.search(r"VDF_DataHome_SSOT_v\d{4}\.json$", n)), key=vnum)
        if names:
            data = git_show_bytes(via.parent, "origin/" + BRANCH, names[-1])
            if data:
                branch_book = (Path(names[-1]).name, data.decode("utf-8", "replace"))
    cands = vdf_root_candidates(via, branch_book)

    def doctor_fn(p):
        rc, so, se = run2([py, v0105, "doctor", "--root", p, "--via-root", via], cwd=v0105.parent, timeout=900)
        try:
            return json.loads(so[so.index("{"):]) if "{" in so else {"verdict": "DOCTOR_RC_%s" % rc, "error": (se or so)[-300:]}
        except ValueError:
            return {"verdict": "DOCTOR_UNREADABLE", "error": (se or so)[-300:]}
    chosen, table = pick_vdf_root(cands, doctor_fn)
    info.update(candidates=table, chosen=chosen, branch_book=branch_book[0] if branch_book else None)
    root = Path(chosen["path"]) if chosen else next((Path(c["path"]) for c in table if c.get("exists")), None)
    rec_path = via / "VIA_Reports" / "vqg" / "VQG_Closeout_latest.json"
    rc, so, se = run2([py, v0105, "closeout", "--via-root", via] + (["--root", root] if root else []), cwd=v0105.parent, timeout=1800)
    info.update(closeout_rc=rc, closeout_out=(so + se)[-3000:])
    try:
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        fresh = rec_path.stat().st_mtime >= time.time() - 3600
    except (OSError, ValueError):
        rec, fresh = None, False
    info["receipt"] = {"lamp": (rec or {}).get("lamp"), "vdf_root": (rec or {}).get("vdf_root"), "steps": [(s.get("step"), s.get("lamp")) for s in (rec or {}).get("steps") or []], "fresh": fresh}
    lamp = (rec or {}).get("lamp") if (rec and fresh) else "RED"
    lamp = lamp if lamp in RANK else "RED"
    probed = ["%s → %s(%s 日線 %s)" % (Path(c["path"]).name or c["path"], c.get("verdict") or ("不在" if not c.get("exists") else "?"), c["how"].split("(")[0][:28], c.get("daily_price_files", "-")) for c in table]
    if chosen:
        say(lamp, "⑧ VQG", "VDF 家 %s(%s)· closeout rc %s · 收據 %s · 步 %s" % (
            chosen["path"], chosen["how"], rc, (rec or {}).get("lamp"), " ".join("%s=%s" % (str(s)[:6], l) for s, l in info["receipt"]["steps"])),
            "YELLOW = 曆是 VQG 從 VDF 日線推的 · 要 GREEN 是 VDF 線出 market / session_index / available_on" if lamp == "YELLOW" else ("看收據 steps" if lamp == "RED" else ""))
    elif not any(c.get("exists") for c in table) and (rec or {}).get("lamp") == "GRAY":
        say("GRAY", "⑧ VQG", "這台機器沒有任何 VDF 家(容器 / CI)· 只驗了自測 · 收據 GRAY · 候選:%s" % " / ".join(probed),
            "桌機才有 VDF 庫;家不在清單 → $env:VQG_VDF_ROOT 指定")
    else:
        say("RED", "⑧ VQG", "每個 VDF 家都沒有日線 parquet(ticker + date + adj_close):%s · closeout rc %s" % (" / ".join(probed), rc),
            "VDF 線:跑 VDF 日線回填(ENG054 · 寫到 <db_home>\\output_hub\\mega\\tw_daily_prices_<時間>.parquet)後再跑本檔;家不在清單 → $env:VQG_VDF_ROOT 指定")


def stage_agentos(via: Path, ctx: dict) -> None:
    tick("⑨")
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    dl = home / "Downloads" if (home / "Downloads").is_dir() else Path(tempfile.gettempdir())
    files, how = fetch_set(via, (AGENTOS_FILE,), dl / ("VIA_Settle_" + VERSION))
    info = {"file_from": how}
    ctx["agentos"] = info
    if not files:
        say("RED", "⑨ Agent OS", "取不到 VIA_AgentOS_v0102 · %s" % how, "git -C <倉> fetch origin %s 後再跑;SHA 不符 = 檔被改過,不跑" % BRANCH)
        return
    f = files[0]
    py = Path(os.environ.get("VIA_AGENTOS_PY") or sys.executable)
    out = via / "VIA_Reports" / "agent_os"
    out.mkdir(parents=True, exist_ok=True)
    repo = via.parent
    runs = {}
    for key, args in (("selftest", ["selftest"]), ("skills", ["skills", "test"]), ("status", ["status", "--repo-root", repo]), ("vcgc_status", ["vcgc-status", "--repo-root", repo])):
        rc, so, se = run2([py, f, *args], cwd=f.parent, timeout=900)
        (out / ("VIA_AgentOS_v0102_%s.json" % key)).write_text(so, encoding="utf-8")
        runs[key] = {"rc": rc, "stderr_tail": se[-600:]}
        if key == "selftest":
            try:
                report = json.loads(so[so.index("{"):]) if "{" in so else None
            except ValueError:
                report = None
    cls = agentos_classify(report, os.name == "nt")
    info.update(python=str(py), runs=runs, selftest=cls, out_dir=str(out))
    others_red = any(runs[k]["rc"] != 0 for k in ("skills", "status", "vcgc_status"))
    lamp = worst(cls["lamp"], "RED" if others_red else "GREEN")
    html = None
    if lamp != "RED":
        html = dl / ("VIA_AgentOS_Dashboard_v0102_%s.html" % _dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
        rcd, _, sed = run2([py, f, "dashboard", "--root", via, "--out", html, "--label", "VIA desktop"], cwd=f.parent, timeout=900)
        if rcd != 0 or not html.is_file():
            info["dashboard_error"] = sed[-600:]
            html = None
            lamp = worst(lamp, "YELLOW")
        info["dashboard"] = str(html) if html else None
    say(lamp, "⑨ Agent OS", "selftest %d 項 · 失敗 %d 錯誤 %d(環境 N/A %d · 真的 %d)· skills rc %s · status rc %s · vcgc-status rc %s · 儀表板 %s" % (
        cls["tests_run"], cls["failures"], cls["errors"], len(cls["known_env"]), len(cls["unknown"]), runs["skills"]["rc"], runs["status"]["rc"], runs["vcgc_status"]["rc"], html or "沒產生"),
        ("環境 N/A = %s" % cls["known_env"][0]["why"]) if cls["known_env"] and not cls["unknown"] else ("真的失敗在 VIA_Reports/agent_os/VIA_AgentOS_v0102_selftest.json 的 details → 貼回包上傳給 AI" if cls["unknown"] else ""))
    if html and os.name == "nt" and os.environ.get("VIA_NO_OPEN") != "1":
        try:
            os.startfile(str(html))                          # noqa: S606 — 只開本機剛寫的 HTML
        except OSError:
            info["dashboard_open"] = "沒開成 · 自己開"


def policy_scan(via: Path, cache_path: Path | None = None) -> dict:
    """L103 三條只讀盤點:.py 沒有加速器橋 · 有網路 import 卻沒有網路橋 · .ps1 沒有 Celeritas;凍結 / 隔離 / 報告夾不算。"""
    no_accel, no_net, ps_no, n_py, n_ps = [], [], [], 0, 0
    cache = {}
    if cache_path and cache_path.is_file():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cache = {}
    new_cache, hits = {}, 0
    for p in via.rglob("*"):
        if p.suffix.lower() not in (".py", ".ps1") or not p.is_file():
            continue
        rel = p.relative_to(via).as_posix()
        if any(s in "/" + rel for s in POLICY_SKIP) or TOOL_SELF_RX.search(p.name):
            continue
        try:
            st = p.stat()
            key = "%d:%d" % (int(st.st_mtime), st.st_size)
            c = cache.get(rel)
            if c and c.get("k") == key:
                flags, hits = c["f"], hits + 1
            else:
                text = p.read_text(encoding="utf-8", errors="replace")
                flags = {"accel": "VIA:ACCEL-BRIDGE" in text, "net_import": bool(NET_IMPORT_RX.search(text)), "net": "VIA:NET-BRIDGE" in text, "cel": "Celeritas" in text}
        except OSError:
            continue
        new_cache[rel] = {"k": key, "f": flags}
        if p.suffix.lower() == ".py":
            n_py += 1
            if not flags["accel"]:
                no_accel.append(rel)
            if flags["net_import"] and not flags["net"]:
                no_net.append(rel)
        else:
            n_ps += 1
            if not flags["cel"]:
                ps_no.append(rel)
    if cache_path:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(new_cache), encoding="utf-8")
        except OSError:
            hits = hits
    return {"py": n_py, "ps1": n_ps, "py_no_accel": no_accel, "py_net_no_bridge": no_net, "ps1_no_celeritas": ps_no, "cache_hits": hits}


def stage_policy(via: Path, ctx: dict) -> None:
    tick("⓫")
    r = policy_scan(via, via / "VIA_Reports" / "settle" / "policy_cache.json")
    ctx["policy"] = {k: (v[:200] if isinstance(v, list) else v) for k, v in r.items()}
    miss = len(r["py_no_accel"]) + len(r["py_net_no_bridge"]) + len(r["ps1_no_celeritas"])
    say("YELLOW" if miss else "GREEN", "⓫ 政策全景", "L103 · .py %d(沒加速器橋 %d · 網路 import 沒網路橋 %d)· .ps1 %d(沒 Celeritas %d)· 快取命中 %d · 例 %s" % (
        r["py"], len(r["py_no_accel"]), len(r["py_net_no_bridge"]), r["ps1"], len(r["ps1_no_celeritas"]), r.get("cache_hits", 0),
        " · ".join(Path(x).name for x in (r["py_no_accel"] + r["py_net_no_bridge"] + r["ps1_no_celeritas"])[:6]) or "—"),
        "補缺是 VCGC 自己的事:via-bridge-sweep --subsystems --apply(加速器)· via_net_injector(網路橋)· PS 用 Invoke-VIACeleritasScoped;本檔只讀不改他系統的檔 · 全清單在報告 policy" if miss else "")


def run_parallel(jobs: list) -> None:
    """併行跑幾段(各寫各的收據夾 · 不碰同一個檔);任一段炸了記成該段 RED,不拖垮別段。"""
    def wrap(name, fn):
        try:
            fn()
        except Exception as exc:                        # noqa: BLE001 — 併行段的例外照實記成紅
            say("RED", name, "%s: %s" % (type(exc).__name__, str(exc)[:200]), "把貼回包上傳給 AI")
    ths = [threading.Thread(target=wrap, args=(name, fn), daemon=True) for name, fn in jobs]
    for th in ths:
        th.start()
    for th in ths:
        th.join()


def _tail_v(ctx: dict, fam: str) -> str:
    v = ((ctx.get("families") or {}).get(fam) or {}).get("tail")
    return ("v" + v.rsplit("_v", 1)[-1].replace(".py", "")) if v else "—"


_MDL_BOOK = {}


def mdl_book(via: Path) -> dict:
    """VCGC 編號冊 MDL + ENG 兩本讀一次(冊沒變不重讀):{name / declared: {code, numbered_at, lamp}};沒冊回 {}。"""
    books = [via / "supportive modules" / "registry" / "VIA_NumberBooks" / ("VIA_NumberBook_%s_v0100.jsonl" % k) for k in ("MDL", "ENG")]
    key = []
    for p in books:
        try:
            st = p.stat()
            key.append((str(p), int(st.st_mtime), st.st_size))
        except OSError:
            key.append((str(p), 0, 0))
    key = tuple(key)
    if key in _MDL_BOOK:
        return _MDL_BOOK[key]
    book = {}
    for p in books:
        if not p.is_file():
            continue
        try:
            for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    e = json.loads(ln)
                except ValueError:
                    continue
                for k in (e.get("name"), e.get("declared")):
                    if k and k not in book:
                        book[k] = {"code": e.get("code"), "numbered_at": e.get("numbered_at"), "lamp": e.get("lamp")}
        except OSError:
            continue
    _MDL_BOOK.clear()
    _MDL_BOOK[key] = book
    return book


def vcgc_number(via: Path, filename: str) -> dict:
    """從 VCGC 編號冊(MDL 冊)查一支檔的 VIA 號與編號時間;沒登回 {}。"""
    if not filename:
        return {}
    stem = filename[:-3] if filename.endswith(".py") else filename
    return dict(mdl_book(via).get(stem) or {})


def _lamp_of(step_glyph: str) -> tuple:
    for x in LOG:
        if (x.get("step") or "").startswith(step_glyph):
            return x["lamp"], x["text"][:140], x.get("secs")
    return "GRAY", "這輪沒測", None


def matrix_rows(via: Path, ctx: dict) -> list:
    """五系統 + VCGC 子列:燈 · 版本尾 · 狀態 · 秒數(只從本輪 LOG 與各系統自報收據取 · 不猜)。"""
    rows = []
    fam = ctx.get("families") or {}

    def num(f):
        n = vcgc_number(via, (fam.get(f) or {}).get("tail") or "")
        return ("%s · %s" % (n.get("code"), (n.get("numbered_at") or "")[:10])) if n else "未登號"
    l, s, sec = _lamp_of("⑤")
    vr = (ctx.get("vrn") or {}).get("closeout") or {}
    rows.append({"system": "VRN-2", "parent": None, "lamp": l, "version": "RoundAll %s · SM %s" % (_tail_v(ctx, "VRN2_RoundAll"), _tail_v(ctx, "VRN_SystemManager")), "status": "收尾 %s · VRN-2 待修 %s · 資料源 %s" % (vr.get("state", "—"), (vr.get("per_owner") or {}).get("VRN-2", "—"), (vr.get("per_owner") or {}).get("資料源", "—")), "secs": sec, "vcgc_no": num("VRN_SystemManager")})
    l, s, sec = _lamp_of("④")
    rows.append({"system": "VDF", "parent": None, "lamp": l, "version": "SM %s" % _tail_v(ctx, "VDF_SystemManager"), "status": s, "secs": sec, "vcgc_no": num("VDF_SystemManager")})
    ve = ctx.get("vdfeng") or {}
    if ve:
        rows.append({"system": "VDF 引擎自測", "parent": "VDF", "lamp": ve.get("lamp", "GRAY"), "version": "%d 家族" % ve.get("total", 0), "status": ve.get("text", ""), "secs": ve.get("secs"), "vcgc_no": "—"})
    l, s, sec = _lamp_of("⑥")
    vc = ctx.get("vcgc") or {}
    inv = sorted((via / "supportive modules" / "registry").glob("VIA_VCGC_FunctionInventory_SSOT_v[0-9][0-9][0-9][0-9].json"), key=vnum)
    rows.append({"system": "VCGC", "parent": None, "lamp": l, "version": "主控台 %s · 盤點冊 %s" % (_tail_v(ctx, "CGC_MDL149_Console"), ("v" + inv[-1].stem.rsplit("_v", 1)[-1]) if inv else "—"), "status": (vc.get("test_line") or s)[:140], "secs": sec, "vcgc_no": num("CGC_MDL149_Console")})
    l, s, sec = _lamp_of("⑨")
    ao = ctx.get("agentos") or {}
    rows.append({"system": "Agent OS", "parent": "VCGC", "lamp": l, "version": _tail_v(ctx, "VIA_AgentOS"), "status": s, "secs": sec, "vcgc_no": num("VIA_AgentOS")})
    l, s, sec = _lamp_of("⑦")
    gr = ctx.get("graphify") or {}
    rows.append({"system": "Graphify", "parent": "VCGC", "lamp": l, "version": "v0101 一行 · graphifyy", "status": " · ".join("%s %s" % (r.get("system"), LAMP_ICON.get(r.get("lamp"), "")) for r in gr.get("systems") or []) or s, "secs": sec})
    mcp = ctx.get("mcp") or {}
    rows.append({"system": "MCP 伺服器", "parent": "VCGC", "lamp": mcp.get("lamp", "GRAY"), "version": _tail_v(ctx, "CGC_MDL279_MCPServer"), "status": mcp.get("text", "工作樹沒這支(同步後才有)"), "secs": mcp.get("secs"), "vcgc_no": num("CGC_MDL279_MCPServer")})
    l, s, sec = _lamp_of("⓫")
    rows.append({"system": "政策全景 L103", "parent": "VCGC", "lamp": l, "version": "SettleAll " + VERSION, "status": s, "secs": sec})
    l, s, sec = _lamp_of("⑧")
    vq = ((ctx.get("vqg") or {}).get("receipt") or {})
    rows.append({"system": "VQG", "parent": None, "lamp": l, "version": "AllInOne " + _tail_v(ctx, "VQG_AllInOne"), "status": "closeout %s · %s" % (vq.get("lamp", "—"), " ".join("%s=%s" % (str(a)[:4], b) for a, b in vq.get("steps") or [])) if vq else s, "secs": sec, "vcgc_no": num("VQG_AllInOne")})
    vap_tail = _tail_v(ctx, "VAP")
    rows.append({"system": "VAP(支援模組)", "parent": None, "lamp": "GRAY", "version": vap_tail, "status": "未納入自動測試(供 VRN-2 繪圖 · 桌機 VAP_AllInOne 未上傳)", "secs": None})
    mm = ctx.get("modmatrix") or {}
    if mm.get("rows") is not None:
        rows.append({"system": "模組矩陣 ⑭", "parent": None, "lamp": mm.get("lamp", "GRAY"), "version": "%d 模組尾版" % mm.get("rows", 0), "status": mm.get("text", ""), "secs": mm.get("secs"), "vcgc_no": "—"})
    return rows


def ledger_path(via: Path) -> Path:
    return via / "VIA_Reports" / "settle" / "VIA_SystemMatrix_Ledger.jsonl"


def last_green(via: Path) -> dict:
    """只增帳裡每個系統最後一次綠:{system: {ts, version, status}}。"""
    out = {}
    p = ledger_path(via)
    if not p.is_file():
        return out
    for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(ln)
        except ValueError:
            continue
        if e.get("lamp") == "GREEN":
            out[e.get("system")] = {"ts": e.get("ts"), "version": e.get("version"), "status": e.get("status")}
    return out


def ledger_append(via: Path, rows: list, run_id: str) -> int:
    """綠的那列追加(時間 · 版本 · 狀態);只增 · 不改舊行。→ 追加筆數。"""
    p = ledger_path(via)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with p.open("a", encoding="utf-8") as f:
        for r in rows:
            if r["lamp"] == "GREEN":
                f.write(json.dumps({"ts": _dt.datetime.now().isoformat(timespec="seconds"), "run": run_id, "system": r["system"], "parent": r["parent"], "lamp": "GREEN", "version": r["version"], "vcgc_no": r.get("vcgc_no"), "status": r["status"], "tool": NAME + " " + VERSION}, ensure_ascii=False) + "\n")
                n += 1
    return n


def render_matrix(rows: list, lg: dict, at: str, root: str) -> tuple:
    """→ (md, html)。"""
    hdr = ["| 系統 | 燈 | 版本 | VCGC 編號 · 編號時間 | 狀態(本輪)| 秒 | 上次綠(時間 · 版本)|", "|---|---|---|---|---|---|---|"]
    md = ["# VIA 系統矩陣 · %s · %s" % (at, root), "", "🟢 綠 = 本輪實測過 · 🟡 黃 = 能動但有條件 · 🔴 紅 = 沒過 · ⚪ = 這輪沒測;「上次綠」來自只增帳 VIA_SystemMatrix_Ledger.jsonl(已完成功能守在那一版)。", ""] + hdr
    for r in rows:
        g = lg.get(r["system"]) or {}
        name = ("　└ " if r["parent"] else "**") + r["system"] + ("" if r["parent"] else "**")
        md.append("| %s | %s %s | %s | %s | %s | %s | %s |" % (name, LAMP_ICON.get(r["lamp"], "⚪"), r["lamp"], r["version"], r.get("vcgc_no", "—"), str(r["status"]).replace("|", "/")[:120], r.get("secs") if r.get("secs") is not None else "", ("%s · %s" % (g.get("ts", "")[:16], g.get("version", ""))) if g else "—"))
    color = {"GREEN": "#1b9e4b", "YELLOW": "#d8a000", "RED": "#c0392b", "GRAY": "#999"}
    trs = "".join("<tr%s><td>%s%s</td><td style='color:%s;font-weight:700'>%s %s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (" class='sub'" if r["parent"] else "", "└ " if r["parent"] else "", r["system"], color.get(r["lamp"], "#999"), LAMP_ICON.get(r["lamp"], "⚪"), r["lamp"], r["version"], r.get("vcgc_no", "—"), str(r["status"])[:160].replace("<", "&lt;"), r.get("secs") if r.get("secs") is not None else "", (("%s · %s" % ((lg.get(r["system"]) or {}).get("ts", "")[:16], (lg.get(r["system"]) or {}).get("version", ""))) if lg.get(r["system"]) else "—")) for r in rows)
    html = ("<!doctype html><html lang='zh-Hant'><meta charset='utf-8'><title>VIA 系統矩陣</title><style>body{font:14px/1.5 Segoe UI,Noto Sans TC,sans-serif;margin:18px;background:#f6f7f9;color:#222}h1{font-size:20px}table{border-collapse:collapse;background:#fff;width:100%%}th,td{border-bottom:1px solid #ddd;padding:6px 8px;text-align:left;vertical-align:top}th{background:#eee}tr.sub td:first-child{padding-left:28px;color:#555}.note{color:#555;font-size:12px}</style>"
            "<h1>VIA 系統矩陣 · %s</h1><div class='note'>%s · 🟢 本輪實測過 · 🟡 能動但有條件 · 🔴 沒過 · ⚪ 這輪沒測 · 「上次綠」= 只增帳</div><table><thead><tr><th>系統</th><th>燈</th><th>版本</th><th>VCGC 編號 · 時間</th><th>狀態(本輪)</th><th>秒</th><th>上次綠</th></tr></thead><tbody>%s</tbody></table></html>" % (at, root, trs))
    return "\n".join(md) + "\n", html


def vdf_engine_tails(via: Path) -> list:
    """VDF 根與 VDF/engine 每個家族的尾版(_vNNNN.py)。"""
    fams = {}
    for folder in (via / "functional modules" / "VDF", via / "functional modules" / "VDF" / "engine"):
        if not folder.is_dir():
            continue
        for p in folder.glob("*_v[0-9][0-9][0-9][0-9].py"):
            key = re.sub(r"_v\d{4}\.py$", "", p.name)
            if key not in fams or vnum(p) > vnum(fams[key]):
                fams[key] = p
    return [fams[k] for k in sorted(fams)]


def stage_vdfeng(via: Path, ctx: dict, budget_s: int = 1200, each_s: int = 120, workers: int = 2, force_old: bool = False, tails: list | None = None) -> None:
    """⑬ VDF 全引擎自測掃描:每個家族尾版 `--selftest`(本直譯器 · 2 線 · 每支 each_s 秒 · 總預算 budget_s)→ 綠 rc 0 · 黃 rc 2 · 紅其他。"""
    tick("⑬")
    why = stale_tree(ctx)
    if why and not force_old:
        ctx["vdfeng"] = {"skipped": why}
        say("YELLOW", "⑬ VDF 引擎", "不在舊版上掃:%s" % why, "先讓 ③ 同步成功")
        return
    tails = tails if tails is not None else vdf_engine_tails(via)
    t0 = time.time()
    results, lock = [], threading.Lock()
    queue = list(tails)

    def worker():
        while True:
            with lock:
                if not queue or time.time() - t0 > budget_s:
                    return
                p = queue.pop(0)
            t1 = time.time()
            rc, out = run([sys.executable, p, "--selftest"], cwd=p.parent, timeout=each_s)
            last = next((ln.strip() for ln in reversed(out.splitlines()) if ln.strip() and "SyntaxWarning" not in ln), "")
            with lock:
                results.append({"engine": p.name, "rc": rc, "lamp": "GREEN" if rc == 0 else ("YELLOW" if rc == 2 else "RED"), "secs": int(time.time() - t1), "last": last[:160]})
    ths = [threading.Thread(target=worker, daemon=True) for _ in range(max(1, workers))]
    for th in ths:
        th.start()
    for th in ths:
        th.join()
    results.sort(key=lambda r: r["engine"])
    cnt = collections.Counter(r["lamp"] for r in results)
    skipped = len(tails) - len(results)
    out_dir = via / "VIA_Reports" / "settle"
    out_dir.mkdir(parents=True, exist_ok=True)
    at = _dt.datetime.now().isoformat(timespec="seconds")
    (out_dir / "VDF_Engines_Matrix_latest.json").write_text(json.dumps({"at": at, "tool": NAME + " " + VERSION, "python": sys.executable, "total": len(tails), "ran": len(results), "skipped_budget": skipped, "counts": dict(cnt), "engines": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# VDF 引擎自測矩陣 · %s" % at, "", "%d 家族 · 跑 %d · 預算外 %d · 🟢 %d 🟡 %d 🔴 %d" % (len(tails), len(results), skipped, cnt.get("GREEN", 0), cnt.get("YELLOW", 0), cnt.get("RED", 0)), "", "| 引擎尾版 | 燈 | rc | 秒 | 最後一行 |", "|---|---|---|---|---|"] + ["| %s | %s %s | %s | %s | %s |" % (r["engine"], LAMP_ICON[r["lamp"]], r["lamp"], r["rc"], r["secs"], r["last"].replace("|", "/")) for r in results]
    (out_dir / "VDF_Engines_Matrix_latest.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    lamp = "RED" if cnt.get("RED") else ("YELLOW" if (cnt.get("YELLOW") or skipped) else ("GREEN" if results else "GRAY"))
    text = "%d 家族 · 🟢 %d 🟡 %d 🔴 %d%s" % (len(tails), cnt.get("GREEN", 0), cnt.get("YELLOW", 0), cnt.get("RED", 0), (" · 預算外 %d" % skipped) if skipped else "")
    ctx["vdfeng"] = {"lamp": lamp, "text": text, "total": len(tails), "counts": dict(cnt), "skipped": skipped, "secs": int(time.time() - t0), "reds": [r["engine"] for r in results if r["lamp"] == "RED"][:30]}
    say(lamp, "⑬ VDF 引擎", text + " · %s" % (out_dir / "VDF_Engines_Matrix_latest.md"), ("紅的:%s → 看矩陣最後一行(容器缺套件 / 無網是環境 · 不是程式)" % " · ".join(ctx["vdfeng"]["reds"][:6])) if cnt.get("RED") else "")


def module_card(path: Path) -> dict:
    """⑭ 一支檔的 AST 卡(只 ast.parse + compile · 不執行):說明首行 · 類數 · 函式數(含方法)· 第三方套件 · 內部模組數 · 重複頂層定義 · 語法 / 編譯錯 · 橋旗標。"""
    out = {"file": path.name, "lines": 0, "desc": "", "cls": 0, "fnc": 0, "libs": [], "internal": 0, "dupdef": [], "error": "", "accel": False, "net_import": False, "net": False}
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as exc:
        out["error"] = "READ " + type(exc).__name__
        return out
    out["lines"] = text.count("\n") + 1
    out["accel"], out["net"], out["net_import"] = "VIA:ACCEL-BRIDGE" in text, "VIA:NET-BRIDGE" in text, bool(NET_IMPORT_RX.search(text))
    import warnings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(text, filename=str(path))
            compile(tree, str(path), "exec")
    except SyntaxError as exc:
        out["error"] = "SYNTAX L%s %s" % (exc.lineno, exc.msg)
        return out
    except (ValueError, TypeError, RecursionError) as exc:
        out["error"] = "COMPILE " + str(exc)[:100]
        return out
    doc = ast.get_docstring(tree, clean=True) or ""
    desc = next((ln.strip() for ln in doc.splitlines() if ln.strip()), "")
    if not desc:
        for ln in text.splitlines()[:20]:
            s = ln.strip()
            if s.startswith("#") and not s.startswith(("#!", "# -*-", "# [VIA:", "# =====")) and len(s) > 3:
                desc = s.lstrip("# ").strip()
                break
    out["desc"] = desc[:100]
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            out["cls"] += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out["fnc"] += 1
        elif isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            mods.add(node.module.split(".")[0])
    names = collections.Counter(n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
    out["dupdef"] = sorted(n for n, c in names.items() if c > 1)
    std = getattr(sys, "stdlib_module_names", frozenset())
    third, internal = [], 0
    for m in sorted(mods):
        if m in std or m == "__future__" or m.startswith("_"):
            continue
        if INTERNAL_RX.match(m):
            internal += 1
        else:
            third.append(m)
    out["libs"], out["internal"] = third[:14], internal
    return out


def module_tails(via: Path) -> list:
    """⑭ 每個系統夾裡每個家族的尾版(_vNNNN.py · 夾內不遞迴)→ [(系統, 家族, 檔)];系統順序照 MODULE_SCOPES。"""
    order = {s: i for i, (s, _, _) in enumerate(MODULE_SCOPES)}
    fams = {}
    for system, folder, rx in MODULE_SCOPES:
        base = via / folder
        if not base.is_dir():
            continue
        for p in base.glob("*_v[0-9][0-9][0-9][0-9].py"):
            if not re.match(rx, p.name):
                continue
            key = (system, re.sub(r"_v\d{4}\.py$", "", p.name))
            if key not in fams or vnum(p) > vnum(fams[key]):
                fams[key] = p
    return [(s, f, fams[(s, f)]) for s, f in sorted(fams, key=lambda k: (order[k[0]], k[1].lower()))]


def vcgc_ledger_last(via: Path) -> dict:
    """VCGC 自己的功能帳(VIA_VCGC_FunctionLedger_v*.jsonl · 只增 · 只讀)每個家族最後一筆:{家族: {ts, version, lamp, event}}。"""
    out = {}
    for p in sorted((via / "supportive modules" / "registry").glob("VIA_VCGC_FunctionLedger_v[0-9][0-9][0-9][0-9].jsonl"), key=vnum):
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for ln in lines:
            try:
                e = json.loads(ln)
            except ValueError:
                continue
            if e.get("kind") == "family" and str(e.get("id", "")).startswith("family:"):
                out[e["id"][7:]] = {"ts": e.get("ts"), "version": e.get("version"), "lamp": e.get("lamp"), "event": e.get("event")}
    return out


def module_status(system: str, fam: str, card: dict, ctx: dict, vdfeng: dict, ledger: dict) -> tuple:
    """⑭ 一列的 STATUS(燈, 文字):只從本輪證據(⑬ 引擎自測 · 系統入口那步的燈 · MCP 自測)與 VCGC 功能帳取;沒證據 → ⚪ 未實測(不冒充綠);語法錯 → 🔴。"""
    if card.get("error"):
        return "RED", "AST " + card["error"][:70]
    if system == "VDF":
        r = vdfeng.get(card["file"])
        return (r["lamp"], "⑬ 自測 rc %s · %s 秒" % (r.get("rc"), r.get("secs"))) if r else ("GRAY", "⑬ 沒跑到(預算外 / 這輪沒掃)")
    if system in ("VCGC", "VCGC·支援"):
        if fam == "CGC_MDL279_MCPServer" and (ctx.get("mcp") or {}).get("lamp"):
            return ctx["mcp"]["lamp"], "MCP " + str(ctx["mcp"].get("text", ""))[:70]
        e = ledger.get(fam)
        if e:
            same = e.get("version") == "v" + card["file"].rsplit("_v", 1)[-1][:-3]
            lamp = e.get("lamp") if e.get("lamp") in LAMP_ICON else "GRAY"
            if lamp == "GREEN" and not same:
                lamp = "YELLOW"
            return lamp, "VCGC 功能帳 %s %s · %s%s" % (e.get("event"), e.get("version"), (e.get("ts") or "")[:16], "" if same else " · 帳上版 ≠ 尾版")
        return "GRAY", "未實測(VCGC 功能帳沒這家族)"
    g = SYSTEM_GLYPH.get(system)
    if g and fam in SYSTEM_ENTRY.get(system, ()):
        l, s, _ = _lamp_of(g)
        return l, "%s %s" % (g, s[:70])
    return "GRAY", "未實測(不是這輪的入口 · 看系統第一欄)"


def modmatrix_render(rows: list, summary: dict, lg: dict, at: str, root: str) -> tuple:
    """⑭ → (md, html);md 一系統一表 · html 一表可按文字篩。"""
    md = ["# VIA 模組矩陣 ⑭ · %s · %s" % (at, root), "", "第一欄 = 系統這輪的燈(同 ⑫)· STATUS = 本輪證據(⑬ 自測 / VCGC 功能帳 / 入口步燈)· ⚪ = 沒證據不冒充 · 「上次綠」= 只增帳 VIA_ModuleMatrix_Ledger.jsonl", "",
          "| 系統 | 燈 | 模組 | 🟢 | 🟡 | 🔴 | ⚪ | AST 錯 | 無加速器橋 | 網路 import 沒橋 |", "|---|---|---|---|---|---|---|---|---|---|"]
    md += ["| %s | %s | %d | %d | %d | %d | %d | %d | %d | %d |" % (s, LAMP_ICON.get(v["sys_lamp"], "⚪"), v["n"], v["GREEN"], v["YELLOW"], v["RED"], v["GRAY"], v["ast"], v["no_accel"], v["no_net"]) for s, v in summary.items()]
    hdr = ["| SYSTEM | FUNCTION | DESCRIPTION | MDL / ENG NAME · VCGC 編號 | CLS | FNC | LIBS | ERROR & AST | STATUS | 上次綠 |", "|---|---|---|---|---|---|---|---|---|---|"]
    cur = None
    for r in rows:
        if r["system"] != cur:
            cur = r["system"]
            md += ["", "## %s %s" % (LAMP_ICON.get(r["sys_lamp"], "⚪"), cur), ""] + hdr
        g = lg.get(r["name"]) or {}
        md.append("| %s %s | %s | %s | %s · %s | %d | %d | %s | %s | %s %s | %s |" % (
            LAMP_ICON.get(r["sys_lamp"], "⚪"), r["system"], r["function"], r["desc"].replace("|", "/"), r["name"], r["vcgc_no"], r["cls"], r["fnc"],
            (" ".join(r["libs"]) + (" +%d 內部" % r["internal"] if r["internal"] else "")) or "—", " · ".join(r["issues"]).replace("|", "/") or "—",
            LAMP_ICON.get(r["lamp"], "⚪"), r["status"].replace("|", "/"), ("%s · %s" % (g.get("ts", "")[:16], g.get("version", ""))) if g else "—"))
    color = {"GREEN": "#1b9e4b", "YELLOW": "#d8a000", "RED": "#c0392b", "GRAY": "#999"}
    esc = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;")   # noqa: E731
    trs = "".join("<tr><td style='color:%s;font-weight:700;white-space:nowrap'>%s %s</td><td>%s</td><td class='d'>%s</td><td>%s<br><small>%s</small></td><td>%d</td><td>%d</td><td class='d'>%s</td><td class='d'>%s</td><td style='color:%s'>%s %s</td><td><small>%s</small></td></tr>" % (
        color.get(r["sys_lamp"], "#999"), LAMP_ICON.get(r["sys_lamp"], "⚪"), esc(r["system"]), esc(r["function"]), esc(r["desc"]), esc(r["name"]), esc(r["vcgc_no"]), r["cls"], r["fnc"],
        esc(" ".join(r["libs"]) + (" +%d 內部" % r["internal"] if r["internal"] else "")) or "—", esc(" · ".join(r["issues"])) or "—", color.get(r["lamp"], "#999"), LAMP_ICON.get(r["lamp"], "⚪"), esc(r["status"]),
        esc("%s · %s" % ((lg.get(r["name"]) or {}).get("ts", "")[:16], (lg.get(r["name"]) or {}).get("version", ""))) if lg.get(r["name"]) else "—") for r in rows)
    sm = "".join("<tr><td style='color:%s;font-weight:700'>%s %s</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td></tr>" % (
        color.get(v["sys_lamp"], "#999"), LAMP_ICON.get(v["sys_lamp"], "⚪"), esc(s), v["n"], v["GREEN"], v["YELLOW"], v["RED"], v["GRAY"], v["ast"], v["no_accel"], v["no_net"]) for s, v in summary.items())
    html = ("<!doctype html><html lang='zh-Hant'><meta charset='utf-8'><title>VIA 模組矩陣</title><style>body{font:13px/1.45 Segoe UI,Noto Sans TC,sans-serif;margin:18px;background:#f6f7f9;color:#222}h1{font-size:20px}table{border-collapse:collapse;background:#fff;width:100%%}th,td{border-bottom:1px solid #ddd;padding:4px 7px;text-align:left;vertical-align:top}th{background:#eee;position:sticky;top:0}td.d{max-width:260px;color:#444}.note{color:#555;font-size:12px}input{font:14px Segoe UI,sans-serif;padding:4px 8px;width:360px;margin:8px 0}</style>"
            "<h1>VIA 模組矩陣 ⑭ · %s</h1><div class='note'>%s · 第一欄 = 系統這輪的燈(同 ⑫)· STATUS = 本輪證據(⑬ 自測 / VCGC 功能帳 / 入口步燈)· ⚪ 沒證據不冒充 · 上次綠 = 只增帳</div>"
            "<table><thead><tr><th>系統</th><th>模組</th><th>🟢</th><th>🟡</th><th>🔴</th><th>⚪</th><th>AST 錯</th><th>無加速器橋</th><th>網路 import 沒橋</th></tr></thead><tbody>%s</tbody></table>"
            "<input id='q' placeholder='篩:系統 / 家族 / 套件 / 錯誤字樣' oninput=\"for(const t of document.querySelectorAll('#m tbody tr'))t.style.display=t.textContent.toLowerCase().includes(this.value.toLowerCase())?'':'none'\">"
            "<table id='m'><thead><tr><th>SYSTEM</th><th>FUNCTION</th><th>DESCRIPTION</th><th>MDL / ENG NAME · VCGC 編號</th><th>CLS</th><th>FNC</th><th>LIBS</th><th>ERROR &amp; AST</th><th>STATUS</th><th>上次綠</th></tr></thead><tbody>%s</tbody></table></html>" % (at, esc(root), sm, trs))
    return "\n".join(md) + "\n", html


def stage_modmatrix(via: Path, ctx: dict) -> None:
    """⑭ 模組矩陣:各系統每個家族尾版一列(只讀 AST · 不執行)· 第一欄系統燈 · FUNCTION · DESCRIPTION · MDL/ENG NAME(+ VCGC 編號)· CLS · FNC · LIBS · ERROR & AST · STATUS(本輪證據)。"""
    tick("⑭")
    t0 = time.time()
    tails = module_tails(via)
    ve = {}
    vp = via / "VIA_Reports" / "settle" / "VDF_Engines_Matrix_latest.json"
    if (ctx.get("vdfeng") or {}).get("lamp") and vp.is_file():          # 只用本輪 ⑬ 剛寫的結果
        try:
            ve = {r["engine"]: r for r in json.loads(vp.read_text(encoding="utf-8")).get("engines") or []}
        except (OSError, ValueError, KeyError, TypeError):
            ve = {}
    ledger = vcgc_ledger_last(via)
    sys_lamp = {s: _lamp_of(g)[0] for s, g in SYSTEM_GLYPH.items()}
    rows, summary = [], {}
    for system, fam, path in tails:
        c = module_card(path)
        lamp, status = module_status(system, fam, c, ctx, ve, ledger)
        n = vcgc_number(via, path.name)
        issues = ([c["error"][:70]] if c["error"] else []) + (["重複定義 " + " ".join(c["dupdef"][:3])] if c["dupdef"] else []) \
            + (["無加速器橋"] if not c["accel"] and not TOOL_SELF_RX.search(path.name) else []) + (["網路 import 沒網路橋"] if c["net_import"] and not c["net"] else [])
        rows.append({"system": system, "sys_lamp": sys_lamp.get(system, "GRAY"), "function": fam, "desc": c["desc"] or "—", "name": path.name, "vcgc_no": n.get("code") or "未登號",
                     "numbered_at": (n.get("numbered_at") or "")[:10], "cls": c["cls"], "fnc": c["fnc"], "lines": c["lines"], "libs": c["libs"], "internal": c["internal"], "issues": issues, "lamp": lamp, "status": status})
        s = summary.setdefault(system, {"sys_lamp": sys_lamp.get(system, "GRAY"), "n": 0, "GREEN": 0, "YELLOW": 0, "RED": 0, "GRAY": 0, "ast": 0, "no_accel": 0, "no_net": 0})
        s["n"] += 1
        s[lamp] += 1
        s["ast"] += 1 if c["error"] else 0
        s["no_accel"] += 1 if "無加速器橋" in issues else 0
        s["no_net"] += 1 if "網路 import 沒網路橋" in issues else 0
    out_dir = via / "VIA_Reports" / "settle"
    out_dir.mkdir(parents=True, exist_ok=True)
    at = _dt.datetime.now().isoformat(timespec="seconds")
    run_id = ctx.get("run_id") or _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    lp = out_dir / "VIA_ModuleMatrix_Ledger.jsonl"
    n_green = 0
    with lp.open("a", encoding="utf-8") as f:                                # 只增:綠的列(時間 · 檔 · 版本 · VCGC 編號 · 狀態)
        for r in rows:
            if r["lamp"] == "GREEN":
                f.write(json.dumps({"ts": at, "run": run_id, "system": r["system"], "name": r["name"], "version": "v" + r["name"].rsplit("_v", 1)[-1][:-3], "vcgc_no": r["vcgc_no"], "status": r["status"], "tool": NAME + " " + VERSION}, ensure_ascii=False) + "\n")
                n_green += 1
    lg = {}
    for ln in lp.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(ln)
            lg[e.get("name")] = {"ts": e.get("ts"), "version": e.get("version")}
        except ValueError:
            continue
    md, html = modmatrix_render(rows, summary, lg, at, str(via))
    (out_dir / "VIA_ModuleMatrix_latest.json").write_text(json.dumps({"at": at, "run": run_id, "tool": NAME + " " + VERSION, "columns": ["SYSTEM", "FUNCTION", "DESCRIPTION", "MDL/ENG NAME", "VCGC_NO", "CLS", "FNC", "LIBS", "ERROR & AST", "STATUS"], "summary": summary, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "VIA_ModuleMatrix_latest.md").write_text(md, encoding="utf-8")
    (out_dir / "VIA_ModuleMatrix_latest.html").write_text(html, encoding="utf-8")
    cnt = collections.Counter(r["lamp"] for r in rows)
    n_ast = sum(v["ast"] for v in summary.values())
    text = "%d 模組尾版 · 🟢 %d 🟡 %d 🔴 %d ⚪ %d · AST 錯 %d · 無加速器橋 %d · %s" % (len(rows), cnt.get("GREEN", 0), cnt.get("YELLOW", 0), cnt.get("RED", 0), cnt.get("GRAY", 0), n_ast, sum(v["no_accel"] for v in summary.values()),
                                                                           " · ".join("%s %s%d" % (s, LAMP_ICON.get(v["sys_lamp"], "⚪"), v["n"]) for s, v in summary.items()))
    lamp = "RED" if n_ast else "GREEN"
    ctx["modmatrix"] = {"lamp": lamp, "rows": len(rows), "counts": dict(cnt), "summary": summary, "ast_errors": [r["name"] + " " + r["issues"][0] for r in rows if r["issues"] and r["issues"][0].startswith(("SYNTAX", "COMPILE", "READ"))][:20], "ledger_appended": n_green, "secs": int(time.time() - t0), "text": text, "html": str(out_dir / "VIA_ModuleMatrix_latest.html")}
    say(lamp, "⑭ 模組矩陣", text + " · 綠的進只增帳 %d 筆 · %s" % (n_green, out_dir / "VIA_ModuleMatrix_latest.html"), ("語法 / 編譯錯的尾版:%s(該系統自己修 · 本檔只讀)" % " · ".join(ctx["modmatrix"]["ast_errors"][:4])) if n_ast else "")


def stage_matrix(via: Path, ctx: dict) -> None:
    tick("⑫")
    mcp = sorted((via / "supportive modules" / "registry").glob("CGC_MDL279_MCPServer_v*.py"), key=vnum)
    if mcp:
        t0 = time.time()
        rc, out = run([sys.executable, mcp[-1], "--selftest"], cwd=mcp[-1].parent, timeout=300)
        m = re.search(r"\[(PASS|FAIL)\] CGC_MDL279_MCPServer \S+ --selftest · (\d+) 項 · 不過 (\d+)", out)
        ctx["mcp"] = {"lamp": "GREEN" if rc == 0 and m and m.group(1) == "PASS" else "RED", "text": ("自測 %s 項 · 不過 %s" % (m.group(2), m.group(3))) if m else out[-160:], "secs": int(time.time() - t0), "file": mcp[-1].name}
    rows = matrix_rows(via, ctx)
    out_dir = via / "VIA_Reports" / "settle"
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = ctx.get("run_id") or _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    n = ledger_append(via, rows, run_id)
    lg = last_green(via)
    at = _dt.datetime.now().isoformat(timespec="seconds")
    md, html = render_matrix(rows, lg, at, str(via))
    (out_dir / "VIA_SystemMatrix_latest.json").write_text(json.dumps({"at": at, "run": run_id, "tool": NAME + " " + VERSION, "rows": rows, "last_green": lg}, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "VIA_SystemMatrix_latest.md").write_text(md, encoding="utf-8")
    (out_dir / "VIA_SystemMatrix_latest.html").write_text(html, encoding="utf-8")
    ctx["matrix"] = {"rows": rows, "ledger_appended": n, "html": str(out_dir / "VIA_SystemMatrix_latest.html")}
    cnt = collections.Counter(r["lamp"] for r in rows)
    say("GREEN", "⑫ 系統矩陣", "%d 列 · 🟢 %d 🟡 %d 🔴 %d ⚪ %d · 綠的記進只增帳 %d 筆 · %s" % (len(rows), cnt.get("GREEN", 0), cnt.get("YELLOW", 0), cnt.get("RED", 0), cnt.get("GRAY", 0), n, out_dir / "VIA_SystemMatrix_latest.html"))
    if os.name == "nt" and os.environ.get("VIA_NO_OPEN") != "1":
        try:
            os.startfile(str(out_dir / "VIA_SystemMatrix_latest.html"))         # noqa: S606 — 只開本機剛寫的頁
        except OSError:
            ctx["matrix"]["open"] = "沒開成 · 自己開"


def stage_report(via: Path, ctx: dict) -> Path:
    out_dir = via / "VIA_Reports" / "settle"
    out_dir.mkdir(parents=True, exist_ok=True)
    LOG.sort(key=step_order)
    ctx["log"] = LOG
    ctx["at"] = _dt.datetime.now().isoformat(timespec="seconds")
    j = out_dir / "SETTLE_latest.json"
    j.write_text(json.dumps(ctx, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    md = ["# %s %s · %s" % (NAME, VERSION, ctx["at"]), "", "| 燈 | 步驟 | 內容 | 下一步 |", "|---|---|---|---|"]
    md += ["| %s | %s | %s | %s |" % (x["lamp"], x["step"], x["text"].replace("|", "/"), x["next"].replace("|", "/")) for x in LOG]
    d = (ctx.get("vdf") or {}).get("diagnosis")
    if d:
        md += ["", "## VDF traceback · AST 定位", "", "例外:`%s`" % d.get("exception"), "", "提示:" + d.get("hint", ""), ""]
        md += ["- `%s:%d` · %s · `%s`" % (f["file"], f["line"], f.get("def"), f.get("src")) for f in d.get("frames", [])]
    cands = (ctx.get("vqg") or {}).get("candidates")
    if cands:
        md += ["", "## VQG · VDF 家候選(試的順序)", "", "| 家 | 來源 | 在 | doctor | 日線檔 |", "|---|---|---|---|---|"]
        md += ["| %s | %s | %s | %s | %s |" % (c["path"], c["how"], "是" if c.get("exists") else "否", c.get("verdict") or "—", c.get("daily_price_files", "—")) for c in cands]
    cl = (ctx.get("sync_dirty") or {}).get("classes")
    if cl:
        md += ["", "## 同步 · 已追蹤改動分類", ""] + ["- **%s** %d:%s" % (k, len(v), " · ".join(Path(x).name for x in v[:12]) + (" …" if len(v) > 12 else "")) for k, v in cl.items()]
    od = (ctx.get("sync_dirty") or {}).get("other_diff")
    if od:
        md += ["", "## 同步 · other 類改動差在哪(對 HEAD · 前 12 檔 · 每檔前 6 行 · XY = git 狀態碼)", ""] + ["- `%s` [%s] +%s/−%s:%s" % (Path(x["file"]).name, x.get("xy"), x["added"], x["deleted"], " ⏎ ".join(s.replace("|", "/") for s in x["samples"])[:600]) for x in od]
    ut = (ctx.get("sync_dirty") or {}).get("untracked")
    if ut and ut.get("total"):
        md += ["", "## 同步 · 未追蹤檔(只讀 · %d 個 · 程式 / 冊類 %d)" % (ut["total"], ut["code_total"]), ""] + ["- `%s` %d" % (k, n) for k, n in ut["by_folder"]] + ["", "程式 / 冊類(前 40):" + " · ".join(Path(x).name for x in ut["code_files"])]
    bj = (ctx.get("vcgc") or {}).get("bad_json")
    if bj:
        md += ["", "## VCGC · 壞 JSON(json.loads 不過)", ""] + ["- `%s` 行 %s 列 %s(char %s)· %s" % (b["file"], b.get("line"), b.get("col"), b.get("char"), b.get("msg")) for b in bj]
    mx = (ctx.get("matrix") or {}).get("rows")
    if mx:
        md += ["", "## 系統矩陣(⑫ · 詳見 VIA_SystemMatrix_latest.md / .html)", "", "| 系統 | 燈 | 版本 | 狀態 |", "|---|---|---|---|"] + ["| %s%s | %s %s | %s | %s |" % ("└ " if r["parent"] else "", r["system"], LAMP_ICON.get(r["lamp"], "⚪"), r["lamp"], r["version"], str(r["status"]).replace("|", "/")[:100]) for r in mx]
    ms = (ctx.get("modmatrix") or {}).get("summary")
    if ms:
        md += ["", "## 模組矩陣(⑭ · 每家族尾版一列 · 詳見 VIA_ModuleMatrix_latest.md / .html)", "", "| 系統 | 燈 | 模組 | 🟢 | 🟡 | 🔴 | ⚪ | AST 錯 | 無加速器橋 | 網路 import 沒橋 |", "|---|---|---|---|---|---|---|---|---|---|"]
        md += ["| %s | %s | %d | %d | %d | %d | %d | %d | %d | %d |" % (s, LAMP_ICON.get(v["sys_lamp"], "⚪"), v["n"], v["GREEN"], v["YELLOW"], v["RED"], v["GRAY"], v["ast"], v["no_accel"], v["no_net"]) for s, v in ms.items()]
        ae = (ctx.get("modmatrix") or {}).get("ast_errors")
        if ae:
            md += ["", "語法 / 編譯錯的尾版(該系統自己修):"] + ["- `%s`" % x for x in ae]
    pol = ctx.get("policy")
    if pol:
        md += ["", "## 政策全景(L103 · 只讀)", ""] + ["- **%s** %d:%s" % (k, len(pol.get(k) or []), " · ".join(pol.get(k) or [][:1])[:600]) for k in ("py_no_accel", "py_net_no_bridge", "ps1_no_celeritas")]
    (out_dir / "SETTLE_latest.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    dl = home / "Downloads" if (home / "Downloads").is_dir() else Path(tempfile.gettempdir())
    zp = dl / ("VIA_Settle_%s.zip" % _dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(j, "settle/SETTLE_latest.json")
        z.write(out_dir / "SETTLE_latest.md", "settle/SETTLE_latest.md")
        for rel in ("vrn2/VRN2_CloseoutUI_latest.json", "vrn2/VRN2_RoundAll_latest.json", "vdf/VDF_UI_MANIFEST.json", "graphify/VIA_Graphify_latest.json",
                    "settle/VIA_SystemMatrix_latest.json", "settle/VIA_SystemMatrix_latest.md", "settle/VIA_SystemMatrix_latest.html", "settle/VIA_SystemMatrix_Ledger.jsonl", "settle/VDF_Engines_Matrix_latest.json", "settle/VDF_Engines_Matrix_latest.md",
                    "settle/VIA_ModuleMatrix_latest.json", "settle/VIA_ModuleMatrix_latest.md", "settle/VIA_ModuleMatrix_latest.html", "settle/VIA_ModuleMatrix_Ledger.jsonl",
                    "vqg/VQG_Closeout_latest.json", "agent_os/VIA_AgentOS_v0102_selftest.json", "agent_os/VIA_AgentOS_v0102_skills.json",
                    "agent_os/VIA_AgentOS_v0102_status.json", "agent_os/VIA_AgentOS_v0102_vcgc_status.json"):
            p = via / "VIA_Reports" / rel
            if p.is_file():
                z.write(p, rel)
    worst_lamp = "RED" if any(x["lamp"] == "RED" for x in LOG) else "YELLOW" if any(x["lamp"] == "YELLOW" for x in LOG) else "GREEN"
    say(worst_lamp, "⑩ 報告", "%s · %s · 貼回包 %s" % (j, out_dir / "SETTLE_latest.md", zp), "把貼回包上傳給 AI" if worst_lamp != "GREEN" else "")
    print("NEXT: [%s] %s · 貼回包 %s" % (worst_lamp, NAME, zp), flush=True)
    return zp


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    with tempfile.TemporaryDirectory(prefix="via_settle_") as td:
        d = Path(td)
        (d / "Fam_v0100.py").write_text("def a():\n    return 1\nPRIOR = None\n", encoding="utf-8")
        (d / "Fam_v0101.py").write_text("PRIOR = None\n\ndef go():\n    return PRIOR.b()\n\ndef __getattr__(n):\n    return getattr(PRIOR, n)\n", encoding="utf-8")
        (d / "Fam_v0102.py").write_text("def b():\n    return 2\n", encoding="utf-8")
        (d / "Bad_v0100.py").write_text("def x(:\n", encoding="utf-8")
        tb = ('Traceback (most recent call last):\n  File "%s", line 4, in go\n    return PRIOR.b()\n'
              '  File "%s", line 7, in __getattr__\n    return getattr(PRIOR, n)\n'
              "AttributeError: module 'Fam_prior' has no attribute 'b'\n") % (d / "Fam_v0101.py", d / "Fam_v0101.py")
        g = diagnose(tb)
        chk("① traceback → AttributeError · 屬性 b · 兩框 · AST 定位到 go / __getattr__",
            g["exception"]["type"] == "AttributeError" and g.get("attr") == "b" and [f["def"].split()[0] for f in g["frames"]] == ["go", "__getattr__"])
        chk("② 同家族追屬性:b 只在 v0102 定義 · v0101 L4 先讀(轉手 1 次)→ 提示點名",
            g["trace"]["defined_in"] == ["Fam_v0102.py"] and "Fam_v0101.py:L4" in g["trace"]["used_before_defined"] and "v0102" in g["hint"], g["hint"])
        g2 = diagnose("RecursionError: maximum recursion depth exceeded\n")
        chk("③ RecursionError → 遞迴提示", g2["recursion"] and "遞迴" in g2["hint"])
        (d / "Esc_v0100.py").write_text('"""a \\d b"""\n', encoding="utf-8")
        sc = ast_scan([d / "Fam_v0100.py", d / "Bad_v0100.py", d / "Esc_v0100.py"])
        chk("④ AST 全景:語法錯抓到檔與行(不執行)· 無效跳脫記成警告(檔:行)不算錯", len(sc["errors"]) == 1 and sc["errors"][0]["kind"] == "SYNTAX"
            and sc["errors"][0]["line"] == 1 and len(sc["warnings"]) == 1 and sc["warnings"][0]["file"] == "Esc_v0100.py", sc["warnings"])
        chk("⑤ git 計數解析:'2\\t719' → (2, 719) · 壞輸入 → (None, None)", parse_ahead_behind("2\t719\n") == (2, 719) and parse_ahead_behind("x") == (None, None))
        chk("⑥ 警告不當例外:SyntaxWarning 行被略過", diagnose("<unknown>:3: SyntaxWarning: invalid escape\nValueError: boom\n")["exception"]["type"] == "ValueError")
        via = d / "repo" / "VeritasIntelligenceAnalytics"
        (via / "functional modules").mkdir(parents=True)
        (via / "supportive modules").mkdir(parents=True)
        chk("⑦ 找根:--root 給倉根或 VIA 根都認得", find_root(str(d / "repo")) == via and find_root(str(via)) == via)
        rc, out = run([sys.executable, "-c", "import sys;print('x');sys.exit(3)"])
        chk("⑧ 子行程:rc 與輸出都拿到 · 找不到程式回 127", rc == 3 and "x" in out and run(["__no_such_cmd__"])[0] == 127)
        # ---- v0102 新增
        chk("⑭ 記憶體:meminfo 解析 8 GB · 量不到回 -1 · free_gb() 是數字", parse_meminfo_gb("MemTotal: 16 kB\nMemAvailable: 8388608 kB\n") == 8.0
            and parse_meminfo_gb("") == -1.0 and isinstance(free_gb(), float))
        win_err = {"ok": False, "tests_run": 48, "failures": 0, "errors": 1, "details": [{"test": "t_nofollow", "kind": "ERROR", "detail": "OSError: [WinError 1314] A required privilege is not held by the client"}]}
        other = {"ok": False, "tests_run": 48, "failures": 1, "errors": 0, "details": [{"test": "t_x", "kind": "FAIL", "detail": "AssertionError: 1 != 2"}]}
        mixed = dict(win_err, details=win_err["details"] + other["details"])
        chk("⑮ Agent OS 分類:ok → GREEN · Windows 只有 symlink 權限項 → YELLOW · 同樣訊息在非 Windows → RED · 混有真失敗 → RED · 沒 JSON → RED",
            agentos_classify({"ok": True, "tests_run": 48, "details": []}, True)["lamp"] == "GREEN" and agentos_classify(win_err, True)["lamp"] == "YELLOW"
            and agentos_classify(win_err, False)["lamp"] == "RED" and agentos_classify(mixed, True)["lamp"] == "RED" and agentos_classify(None, True)["lamp"] == "RED"
            and len(agentos_classify(mixed, True)["known_env"]) == 1 and len(agentos_classify(mixed, True)["unknown"]) == 1)
        vdf = via / "functional modules" / "VDF"
        vdf.mkdir()
        home_a, home_b = d / "home_a", d / "home_b"
        home_a.mkdir()
        home_b.mkdir()
        (vdf / "VDF_DataHome_SSOT_v0100.json").write_text(json.dumps({"homes": [{"id": "ws", "db_home": str(home_a)}]}), encoding="utf-8")
        branch = ("VDF_DataHome_SSOT_v0101.json", json.dumps({"homes": [{"id": "ws", "db_home": str(home_b)}, {"id": "ws2", "db_home": str(home_a)}]}))
        old_env = os.environ.pop("VQG_VDF_ROOT", None)
        cands = vdf_root_candidates(via, branch)
        os.environ["VQG_VDF_ROOT"] = str(d / "env_home")
        cands_env = vdf_root_candidates(via, branch)
        if old_env is None:
            os.environ.pop("VQG_VDF_ROOT", None)
        else:
            os.environ["VQG_VDF_ROOT"] = old_env
        chk("⑯ VDF 家候選:分支 v0101 的家排前(B · A)· 工作樹 v0100 的 A 不重複 · 最後是倉內 output_hub 接點 · 環境變數最優先",
            [Path(c["path"]) for c in cands] == [home_b, home_a, vdf / "output_hub"] and "分支" in cands[0]["how"] and Path(cands_env[0]["path"]) == d / "env_home", [c["how"][:20] for c in cands])
        calls = []

        def fake_doctor(p):
            calls.append(Path(p).name)
            return {"verdict": "NO_DAILY_PRICES", "daily_price_files": 0} if Path(p) == home_a else {"verdict": "DERIVE_READY", "daily_price_files": 2}
        chosen, table = pick_vdf_root(cands_env, fake_doctor)
        first_calls = list(calls)
        chosen2, _ = pick_vdf_root([{"path": str(home_a), "how": "x"}], fake_doctor)
        chk("⑰ 選家:不在的家不探(env_home)· 第一個有日線的家被選(B · 2 檔)· 後面的家標「未探」· 全沒有 → None",
            chosen is not None and Path(chosen["path"]) == home_b and first_calls == ["home_b"] and table[0]["exists"] is False
            and any("未探" in str(r.get("verdict")) for r in table) and chosen2 is None, (first_calls, chosen2))
        chk("⑱ SHA-256 CRLF 正規化:CRLF 與 LF 同一個雜湊 · 與釘住格式(64 hex)相同",
            sha_lf(b"a\r\nb\r\n") == sha_lf(b"a\nb\n") and len(sha_lf(b"x")) == 64 and sha_lf(b"a\r\nb") != sha_lf(b"a\nb\n"))
        slow = d / "slow.py"
        slow.write_text("import time,sys\nprint('go',flush=True)\ntime.sleep(30)\n", encoding="utf-8")
        quick = d / "quick.py"
        quick.write_text("print('hi')\n", encoding="utf-8")
        r_ok = run_watched([sys.executable, quick], floor_gb=0.0, timeout=60, poll=0.2)
        r_to = run_watched([sys.executable, slow], floor_gb=0.0, timeout=1, poll=0.2)
        r_mem = run_watched([sys.executable, slow], floor_gb=10 ** 6, timeout=60, poll=0.2)
        chk("⑲ 看門狗:正常 rc 0 + 輸出 · 逾時 1 秒殺掉 rc 124 · 可用記憶體 < 下限(設成 100 萬 GB)立刻殺 rc 137 · 都在 10 秒內",
            r_ok["rc"] == 0 and "hi" in r_ok["out"] and r_to["rc"] == 124 and "逾時" in (r_to["killed"] or "") and r_mem["rc"] == 137 and "記憶體" in (r_mem["killed"] or "")
            and r_to["seconds"] <= 10 and r_mem["seconds"] <= 10, (r_ok["rc"], r_to["rc"], r_mem["rc"], r_to["seconds"], r_mem["seconds"]))
        fake_gx = d / "fake_graphify.py"
        fake_gx.write_text("import sys,json,pathlib\nargs=sys.argv[1:]\nif args[0]=='extract':\n    o=pathlib.Path(args[args.index('--out')+1])/'graphify-out'\n    o.mkdir(parents=True,exist_ok=True)\n"
                           "    (o/'graph.json').write_text(json.dumps({'nodes':[1,2,3],'links':[[1,2]]}))\nelif args[0]=='cluster-only':\n    pass\nelse:\n    sys.exit(9)\nprint('fake graphify',args[0])\n", encoding="utf-8")
        (via / "functional modules" / "VRN2").mkdir()
        (via / "supportive modules" / "registry").mkdir()
        gout = d / "gout"
        old_only = os.environ.get("VIA_GRAPHIFY_ONLY")
        os.environ["VIA_GRAPHIFY_ONLY"] = "VRN,VCGC,VRN_Shared"
        n0 = len(LOG)
        c_g = {}
        stage_graphify(via, c_g, floor_gb=0.0, gx_cmd=[sys.executable, fake_gx], out_root=gout, mode="all")
        if old_only is None:
            os.environ.pop("VIA_GRAPHIFY_ONLY", None)
        else:
            os.environ["VIA_GRAPHIFY_ONLY"] = old_only
        g_lamp, g_sys = LOG[-1]["lamp"], {r["system"]: r["lamp"] for r in c_g["graphify"]["systems"]}
        del LOG[n0:]
        chk("⑳ Graphify 段(假 graphify):VRN · VCGC 綠(graph.json 3 節點)· VRN_Shared 夾不在 → 灰 · VDF 沒點名不跑 · 收據寫在 out · 總燈 GREEN",
            g_lamp == "GREEN" and g_sys == {"VRN": "GREEN", "VCGC": "GREEN", "VRN_Shared": "GRAY"} and (gout / "VIA_Graphify_latest.json").is_file()
            and c_g["graphify"]["systems"][0].get("nodes") == 3 and c_g["graphify"]["systems"][0].get("phase") == "cluster" and "used_est_gb" in c_g["graphify"]["systems"][0], (g_lamp, g_sys))
        c_g2 = {}
        n3 = len(LOG)
        os.environ["VIA_GRAPHIFY_ONLY"] = "VRN"
        stage_graphify(via, c_g2, floor_gb=0.0, gx_cmd=[sys.executable, fake_gx], out_root=gout, mode="changed")
        reused = c_g2["graphify"]["systems"][0]
        (via / "functional modules" / "VRN2" / "new_v0100.py").write_text("x=1\n", encoding="utf-8")
        import time as _t
        _t.sleep(1.1)
        c_g3 = {}
        stage_graphify(via, c_g3, floor_gb=0.0, gx_cmd=[sys.executable, fake_gx], out_root=gout, mode="changed")
        rerun = c_g3["graphify"]["systems"][0]
        if old_only is None:
            os.environ.pop("VIA_GRAPHIFY_ONLY", None)
        else:
            os.environ["VIA_GRAPHIFY_ONLY"] = old_only
        del LOG[n3:]
        chk("㉝ Graphify changed 模式:程式沒變 → 沿用上一張(0 秒 · reused)· 夾裡多一支新 .py → 重抽", reused.get("reused") is True and reused["seconds"] == 0 and not rerun.get("reused") and rerun.get("lamp") == "GREEN", (reused.get("reused"), rerun.get("reused")))
        pc = d / "pol_cache.json"
        pq = d / "polq" / "VeritasIntelligenceAnalytics" / "functional modules" / "Q"
        pq.mkdir(parents=True)
        (pq / "a_v0100.py").write_text("import os\n", encoding="utf-8"); (pq / "b.ps1").write_text("x\n", encoding="utf-8")
        r1 = policy_scan(d / "polq" / "VeritasIntelligenceAnalytics", pc); r2 = policy_scan(d / "polq" / "VeritasIntelligenceAnalytics", pc)
        chk("㉟b 政策全景 mtime 快取:第一次命中 0 · 第二次全命中 · 結果相同", r1["cache_hits"] == 0 and r2["cache_hits"] == r2["py"] + r2["ps1"] and r1["py_no_accel"] == r2["py_no_accel"], (r1["cache_hits"], r2["cache_hits"]))
        chk("㊱ 舊樹判定:③ 沒合併 + 落後 + 家族落後 → ④ ⑥ 不跑;合併了 → 跑", stale_tree({"git_before": {BRANCH: {"remote_only": 5}}, "behind_branch": ["VDF_SystemManager v0162←v0168"]}) != "" and stale_tree({"git_before": {BRANCH: {"remote_only": 5}}, "behind_branch": ["x"], "git_after": {"head": "a"}}) == "" and stale_tree({"git_before": {BRANCH: {"remote_only": 0}}, "behind_branch": []}) == "")
        mv = d / "mx" / "VeritasIntelligenceAnalytics"
        (mv / "VIA_Reports").mkdir(parents=True)
        n4 = len(LOG)
        say("GREEN", "⑤ VRN", "x"); say("YELLOW", "④ VDF ui", "y"); say("GREEN", "⑧ VQG", "z")
        fctx = {"families": {"VRN2_RoundAll": {"tail": "VRN2_RoundAll_v0135.py"}, "VQG_AllInOne": {"tail": "VQG_AllInOne_v0105.py"}}, "vrn": {"closeout": {"state": "DATA_GAP", "per_owner": {"VRN-2": 0, "資料源": 3}}}}
        rows = matrix_rows(mv, fctx)
        n_app = ledger_append(mv, rows, "t1")
        lg = last_green(mv)
        md_m, html_m = render_matrix(rows, lg, "2026-11-06T00:00:00", "x")
        del LOG[n4:]
        by = {r["system"]: r for r in rows}
        chk("㉝ 系統矩陣:VRN-2 綠(RoundAll v0135 · DATA_GAP · 待修 0)· VDF 黃 · VQG 綠 · VCGC / Agent OS ⚪ 這輪沒測 · 子列掛在 VCGC · 綠的記進只增帳 2 筆 · 上次綠讀得回 · md / html 有三色燈",
            by["VRN-2"]["lamp"] == "GREEN" and "v0135" in by["VRN-2"]["version"] and "DATA_GAP" in by["VRN-2"]["status"] and by["VDF"]["lamp"] == "YELLOW" and by["VQG"]["lamp"] == "GREEN"
            and by["VCGC"]["lamp"] == "GRAY" and by["Agent OS"]["parent"] == "VCGC" and n_app == 2 and set(lg) == {"VRN-2", "VQG"} and "🟢" in md_m and "🟡" in md_m and "⚪" in md_m and "<table" in html_m, (n_app, sorted(lg)))
        ledger_append(mv, [{"system": "VDF", "parent": None, "lamp": "GREEN", "version": "SM v0168", "status": "ok", "secs": 1}], "t2")
        nb = mv / "supportive modules" / "registry" / "VIA_NumberBooks"
        nb.mkdir(parents=True)
        (nb / "VIA_NumberBook_MDL_v0100.jsonl").write_text(json.dumps({"code": "VIA-VRN-MDL330", "name": "VRN_SystemManager_v0261", "declared": "VRN_SystemManager_v0261", "numbered_at": "2026-11-04 09:00:00 +0000"}) + "\n", encoding="utf-8")
        fctx2 = dict(fctx, families=dict(fctx["families"], VRN_SystemManager={"tail": "VRN_SystemManager_v0261.py"}))
        n5 = len(LOG); say("GREEN", "⑤ VRN", "x"); rows2 = matrix_rows(mv, fctx2); del LOG[n5:]
        chk("㊲ 矩陣 VCGC 編號欄:VRN-2 尾版查到 VIA-VRN-MDL330 · 2026-11-04;沒登的寫「未登號」", rows2[0]["vcgc_no"].startswith("VIA-VRN-MDL330 · 2026-11-04") and rows2[1]["vcgc_no"] == "未登號", rows2[0]["vcgc_no"])
        ve = d / "ve" / "VeritasIntelligenceAnalytics"
        (ve / "functional modules" / "VDF" / "engine").mkdir(parents=True)
        (ve / "functional modules" / "VDF" / "VDF_A_v0100.py").write_text("import sys\nprint('A ok')\nsys.exit(0)\n", encoding="utf-8")
        (ve / "functional modules" / "VDF" / "VDF_A_v0101.py").write_text("import sys\nprint('A v0101 ok')\nsys.exit(0)\n", encoding="utf-8")
        (ve / "functional modules" / "VDF" / "engine" / "VDF_ENG001_B_v0100.py").write_text("import sys\nprint('B 無資料')\nsys.exit(2)\n", encoding="utf-8")
        (ve / "functional modules" / "VDF" / "engine" / "VDF_ENG002_C_v0100.py").write_text("raise RuntimeError('boom')\n", encoding="utf-8")
        (ve / "VIA_Reports").mkdir()
        n6 = len(LOG); c_ve = {}
        stage_vdfeng(ve, c_ve, budget_s=60, each_s=30, workers=2)
        del LOG[n6:]
        tails_ve = [p.name for p in vdf_engine_tails(ve)]
        chk("㊳ VDF 全引擎掃描:只取每家族尾版(A 取 v0101)· 3 支 → 🟢 1 🟡 1 🔴 1 · 矩陣 json / md 寫出 · 總燈 RED · 紅的點名", tails_ve == ["VDF_A_v0101.py", "VDF_ENG001_B_v0100.py", "VDF_ENG002_C_v0100.py"] and c_ve["vdfeng"]["counts"] == {"GREEN": 1, "YELLOW": 1, "RED": 1}
            and c_ve["vdfeng"]["lamp"] == "RED" and c_ve["vdfeng"]["reds"] == ["VDF_ENG002_C_v0100.py"] and (ve / "VIA_Reports" / "settle" / "VDF_Engines_Matrix_latest.md").is_file(), (tails_ve, c_ve.get("vdfeng", {}).get("counts")))
        chk("㉞ 只增帳守住已完成:第二輪 VDF 綠 → 上次綠多 VDF · 舊行不動(3 行)", set(last_green(mv)) == {"VRN-2", "VQG", "VDF"} and len(ledger_path(mv).read_text(encoding="utf-8").splitlines()) == 3)
        chk("㉑ Graphify 判燈:有紅 → RED · 全黃 → YELLOW · 綠 + 黃 → YELLOW · 綠 + 灰 → GREEN · 空 → YELLOW",
            graphify_lamp([{"lamp": "GREEN"}, {"lamp": "RED"}]) == "RED" and graphify_lamp([{"lamp": "YELLOW"}]) == "YELLOW"
            and graphify_lamp([{"lamp": "GREEN"}, {"lamp": "YELLOW"}]) == "YELLOW" and graphify_lamp([{"lamp": "GREEN"}, {"lamp": "GRAY"}]) == "GREEN" and graphify_lamp([]) == "YELLOW")
        chk("㉕ 收據分類:VIA_Reports / evidence / HANDOFF_latest / 兩本只增冊 / .via 是收據 · 程式與其他冊不是",
            all(is_receipt(x) for x in ("VeritasIntelligenceAnalytics/VIA_Reports/vcgc/events/E.jsonl", "VeritasIntelligenceAnalytics\\docs\\handoff\\evidence\\x.json",
                                        "VeritasIntelligenceAnalytics/docs/handoff/HANDOFF_latest.json", "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_Lessons_Ledger_v0100.json",
                                        "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_VCGC_FunctionLedger_v0100.jsonl", ".via/ssot.json"))
            and not any(is_receipt(x) for x in ("VeritasIntelligenceAnalytics/functional modules/VDF/VDF_SystemManager_v0162.py", "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_Requirements_SSOT_v0209.json", "CLAUDE.md")))
        pd = d / "pol" / "VeritasIntelligenceAnalytics"
        (pd / "functional modules" / "X").mkdir(parents=True)
        (pd / "functional modules" / "X" / "references").mkdir()
        (pd / "functional modules" / "X" / "a_v0100.py").write_text("# [VIA:ACCEL-BRIDGE:v0111]\nimport requests\n# VIA:NET-BRIDGE ok\n", encoding="utf-8")
        (pd / "functional modules" / "X" / "b_v0100.py").write_text("import urllib.request\n", encoding="utf-8")
        (pd / "functional modules" / "X" / "references" / "c.py").write_text("x=1\n", encoding="utf-8")
        (pd / "functional modules" / "X" / "d.ps1").write_text("Write-Host hi\n", encoding="utf-8")
        (pd / "functional modules" / "X" / "e.ps1").write_text("Invoke-VIACeleritasScoped { }\n", encoding="utf-8")
        ps = policy_scan(pd)
        chk("㉗ 政策全景(L103 只讀):b 沒加速器橋且網路 import 沒網路橋 · a 都有 · references 不算 · d.ps1 沒 Celeritas · e 有",
            ps["py"] == 2 and ps["py_no_accel"] == ["functional modules/X/b_v0100.py"] and ps["py_net_no_bridge"] == ["functional modules/X/b_v0100.py"] and ps["ps1_no_celeritas"] == ["functional modules/X/d.ps1"], ps)
        bjd = d / "bj" / "VeritasIntelligenceAnalytics" / "supportive modules" / "registry"
        bjd.mkdir(parents=True)
        (bjd / "ok.json").write_text("{\"a\": 1}\n", encoding="utf-8"); (bjd / "bad.json").write_text("{\n \"a\": 1,\n}\n", encoding="utf-8")
        bjr = bad_json_scan(d / "bj" / "VeritasIntelligenceAnalytics")
        chk("㉛ 壞 JSON 定位:尾逗號那本抓到(檔 · 行 · 列)· 好的不報", len(bjr) == 1 and bjr[0]["file"].endswith("bad.json") and bjr[0]["line"] in (2, 3) and bjr[0]["col"] >= 1, bjr)
        (pd / "functional modules" / "X" / "venv" / "Lib").mkdir(parents=True)
        (pd / "functional modules" / "X" / "venv" / "Lib" / "site.py").write_text("import urllib.request\n", encoding="utf-8")
        chk("㉜ 政策全景不算樹裡的 venv / Lib", policy_scan(pd)["py"] == 2)
        chk("㉘ Graphify worker:可用 5.5 GB · 估 6 → 1;可用 9 → 2;量不到(-1)→ 2", graphify_workers(5.5, 6) == 1 and graphify_workers(9.0, 6) == 2 and graphify_workers(-1.0, 6) == 2)
        n2 = len(LOG)
        run_parallel([("⑨ t", lambda: say("GREEN", "⑨ t", "b")), ("④ t", lambda: say("GREEN", "④ t", "a")), ("⑧ t", lambda: (_ for _ in ()).throw(ValueError("boom")))])
        par = sorted(LOG[n2:], key=step_order)
        par_ok = [x["step"][0] for x in par] == ["④", "⑧", "⑨"] and par[1]["lamp"] == "RED" and "boom" in par[1]["text"]
        del LOG[n2:]
        chk("㉙ 併行段:三段都跑完 · 炸掉的那段記 RED 不拖垮別段 · 報告照圈號排", par_ok)
        chk("㉚ 去橋比對:同一支程式加了 ACCEL / NET 橋塊與第 3 行標記 → 本體相同;改了一行 → 不同",
            strip_bridges("# [VIA:ACCEL-BRIDGE:v0111]\n# ===== [VIA:NET-BRIDGE:v0100] x =====\nVIA_NET_TOOL_PATH = None\n# ===== [VIA:NET-BRIDGE:END] =====\nimport os\r\n") == "import os\n"
            and strip_bridges("import os\nx = 2\n") != strip_bridges("import os\nx = 1\n"))
        chk("㉒ VRN status 判燈:沒收據 → YELLOW · VRN-2 有待修 → RED · PASS → GREEN · DATA_GAP / REVIEW → YELLOW",
            vrn_status_lamp(None) == "YELLOW" and vrn_status_lamp({"state": "OPEN", "per_owner": {"VRN-2": 2}}) == "RED"
            and vrn_status_lamp({"state": "PASS", "per_owner": {"VRN-2": 0}}) == "GREEN" and vrn_status_lamp({"state": "DATA_GAP", "per_owner": {"VRN-2": 0}}) == "YELLOW")
    if shutil.which("git"):
        with tempfile.TemporaryDirectory(prefix="via_settle_git_") as tg:
            g = Path(tg)
            gx = lambda *a, cwd=None: run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=cwd)  # noqa: E731
            gx("init", "-q", "--bare", "-b", BRANCH, str(g / "remote.git"))
            gx("clone", "-q", str(g / "remote.git"), str(g / "up"))
            up = g / "up"
            for sub in ("VeritasIntelligenceAnalytics/functional modules", "VeritasIntelligenceAnalytics/supportive modules"):
                (up / sub).mkdir(parents=True)
                (up / sub / "k.txt").write_bytes(b"1\n")
            pin_rel = "functional modules/pinned_v0100.py"
            (up / "VeritasIntelligenceAnalytics" / pin_rel).write_bytes(b"print(1)\r\n")
            gx("checkout", "-q", "-b", BRANCH, cwd=up)
            gx("add", "-A", cwd=up); gx("commit", "-q", "-m", "a", cwd=up); gx("push", "-q", "origin", BRANCH, cwd=up)
            gx("clone", "-q", "-b", BRANCH, str(g / "remote.git"), str(g / "desk"))
            (up / "new.txt").write_bytes(b"n\n"); gx("add", "-A", cwd=up); gx("commit", "-q", "-m", "b", cwd=up); gx("push", "-q", "origin", BRANCH, cwd=up)
            desk_via = g / "desk" / "VeritasIntelligenceAnalytics"
            (g / "desk" / "VeritasIntelligenceAnalytics" / "functional modules" / "k.txt").write_bytes(b"dirty\n")
            run(["git", "-C", g / "desk", "add", "VeritasIntelligenceAnalytics/functional modules/k.txt"])      # 桌機情境:改動已進索引
            c1, n1 = {}, len(LOG)
            stage_sync(desk_via, c1, True)
            refused = LOG[-1]["lamp"] == "YELLOW" and "不合併" in LOG[-1]["text"] and "k.txt" in LOG[-1]["text"] and not (g / "desk" / "new.txt").exists() \
                and (c1.get("sync_dirty") or {}).get("others") == ["VeritasIntelligenceAnalytics/functional modules/k.txt"] and (c1["sync_dirty"]["counts"] == {"other": 1}) \
                and c1["sync_dirty"]["other_diff"][0]["added"] == "1" and c1["sync_dirty"]["other_diff"][0]["samples"] == ["-1", "+dirty"] and c1["sync_dirty"]["other_diff"][0]["xy"] == "M "
            run(["git", "-C", g / "desk", "reset", "-q"]); run(["git", "-C", g / "desk", "checkout", "--", "."])
            c2 = {}
            stage_sync(desk_via, c2, True)
            merged = LOG[-1]["lamp"] == "GREEN" and (g / "desk" / "new.txt").is_file() and (c2.get("git_after") or {}).get(BRANCH, {}).get("remote_only") == 0
            # 收據類改動:遠端與桌機都改了同一個 VIA_Reports 檔 + 桌機另改一個只增冊 → stash → 合併 → 放回(衝突取桌機版)
            rcp = "VeritasIntelligenceAnalytics/VIA_Reports/handover/r.json"
            led = "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_VCGC_FunctionLedger_v0100.jsonl"
            for base in (up, g / "desk"):
                (base / rcp).parent.mkdir(parents=True, exist_ok=True)
                (base / led).parent.mkdir(parents=True, exist_ok=True)
            (up / rcp).write_bytes(b"{\"v\": 0}\n"); (up / led).write_bytes(b"a\n"); gx("add", "-A", cwd=up); gx("commit", "-q", "-m", "c", cwd=up); gx("push", "-q", "origin", BRANCH, cwd=up)
            run(["git", "-C", g / "desk", "pull", "-q", "origin", BRANCH])
            (up / rcp).write_bytes(b"{\"v\": 1}\n"); (up / "new2.txt").write_bytes(b"n\n"); gx("add", "-A", cwd=up); gx("commit", "-q", "-m", "d", cwd=up); gx("push", "-q", "origin", BRANCH, cwd=up)
            (g / "desk" / rcp).write_bytes(b"{\"v\": \"desk\"}\n"); (g / "desk" / led).write_bytes(b"a\nb\n")
            c3 = {}
            stage_sync(desk_via, c3, True)
            rc_s, out_s = run(["git", "-C", g / "desk", "stash", "list"])
            receipts_ok = LOG[-1]["lamp"] == "GREEN" and "放回" in LOG[-1]["text"] and (g / "desk" / "new2.txt").is_file() \
                and (g / "desk" / rcp).read_bytes() == b"{\"v\": \"desk\"}\n" and (g / "desk" / led).read_bytes() == b"a\nb\n" \
                and b"<<<<" not in (g / "desk" / rcp).read_bytes() and not out_s.strip() and (c3.get("sync_dirty") or {}).get("conflicted") == {rcp: "桌機版"} \
                and run(["git", "-C", g / "desk", "show", "HEAD:" + rcp])[1].strip() == "{\"v\": 1}"
            # 橋塊 / 換行 / 狀態冊三類:遠端加了新版 · 桌機只在舊檔注入橋塊 + 狀態冊兩邊都改 → 自動 stash → 合併 → 放回;衝突 state 取分支版
            code_rel = "VeritasIntelligenceAnalytics/functional modules/VRN/E_v0100.py"
            state_rel = "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_VCGC_SubsystemSeat_v0100.json"
            for base in (up, g / "desk"):
                (base / code_rel).parent.mkdir(parents=True, exist_ok=True)
                (base / state_rel).parent.mkdir(parents=True, exist_ok=True)
            (up / code_rel).write_bytes(b"import os\n\ndef f():\n    return 1\n"); (up / state_rel).write_bytes(b"{\"seat\": 1}\n")
            gx("add", "-A", cwd=up); gx("commit", "-q", "-m", "e", cwd=up); gx("push", "-q", "origin", BRANCH, cwd=up)
            run(["git", "-C", g / "desk", "pull", "-q", "origin", BRANCH])
            del_rel = "VeritasIntelligenceAnalytics/functional modules/VRN/Old_v0100.py"
            fz0, fz1 = "VeritasIntelligenceAnalytics/functional modules/VRN/Fz_v0100.py", "VeritasIntelligenceAnalytics/functional modules/VRN/Fz_v0101.py"
            (up / fz0).write_bytes(b"x=1\n"); (up / fz1).write_bytes(b"x=2\n")
            (up / del_rel).write_bytes(b"x=1\n"); gx("add", "-A", cwd=up); gx("commit", "-q", "-m", "g", cwd=up); gx("push", "-q", "origin", BRANCH, cwd=up)
            run(["git", "-C", g / "desk", "pull", "-q", "origin", BRANCH])
            run(["git", "-C", g / "desk", "rm", "-q", del_rel])
            (g / "desk" / fz0).write_bytes(b"x=1\n# desk edit\n")                                                   # 桌機情境:非尾版(凍結)被改了內容                                                        # 桌機情境:舊版被 git rm(在弄髒其他檔之前 · pull 才進得來)
            (up / state_rel).write_bytes(b"{\"seat\": 2}\n"); (up / "new3.txt").write_bytes(b"n\n"); gx("add", "-A", cwd=up); gx("commit", "-q", "-m", "f", cwd=up); gx("push", "-q", "origin", BRANCH, cwd=up)
            bridge = "# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel =====\ntry:\n    import x\nexcept Exception:\n    x = None\n# ===== [VIA:ACCEL-BRIDGE:END] =====\n"
            (g / "desk" / code_rel).write_bytes(("# [VIA:ACCEL-BRIDGE:v0111]\n" + bridge + "import os\n\ndef f():\n    return 1\n").encode())
            (g / "desk" / state_rel).write_bytes(b"{\n \"seat\": \"desk\",\n}\n")                                   # 桌機情境:state 冊被改壞(尾逗號)
            (g / "desk" / "VeritasIntelligenceAnalytics" / "functional modules" / "k.txt").write_bytes(b"1\r\n")
            cls_b = classify_dirty(g / "desk", code_rel); cls_s = classify_dirty(g / "desk", state_rel); cls_e = classify_dirty(g / "desk", "VeritasIntelligenceAnalytics/functional modules/k.txt")
            cls_d = classify_dirty(g / "desk", del_rel, xy="D ")
            cls_f = classify_dirty(g / "desk", fz0)
            cls_t = classify_dirty(g / "desk", fz1, head_text="x=2\n", work_text="x=3\n")
            cls_o = classify_dirty(g / "desk", code_rel, head_text="import os\n", work_text="import sys\n")
            c4 = {}
            stage_sync(desk_via, c4, True)
            sd4 = c4.get("sync_dirty") or {}
            bridge_ok = (cls_b, cls_s, cls_e, cls_o, cls_d, cls_f, cls_t) == ("bridge", "state", "eol", "other", "deleted", "frozen", "other") and LOG[-1]["lamp"] == "GREEN"\
                and sd4.get("restored_frozen") == [fz0] and (g / "desk" / fz0).read_bytes() == b"x=1\n" and any((desk_via / "VIA_Reports" / "settle" / "frozen_version_backup").glob("Fz_v0100.py.*.desktop")) and isinstance((sd4.get("untracked") or {}).get("total"), int) and (g / "desk" / "new3.txt").is_file() \
                and (g / "desk" / state_rel).read_bytes() == b"{\"seat\": 2}\n" and "VIA:ACCEL-BRIDGE" in (g / "desk" / code_rel).read_text() \
                and sd4.get("fixed_broken_json") == [state_rel] and sd4.get("restored_deleted") == [del_rel] and (g / "desk" / del_rel).is_file() \
                and any((desk_via / "VIA_Reports" / "settle" / "broken_json_backup").glob("*.broken")) and not run(["git", "-C", g / "desk", "stash", "list"])[1].strip()
            del LOG[n1:]
            pinned = {pin_rel: sha_lf(b"print(1)\n")}
            f_tree, how_tree = fetch_set(desk_via, (pin_rel,), g / "dl", pinned)
            (desk_via / pin_rel).write_bytes(b"print(2)\n")
            f_br, how_br = fetch_set(desk_via, (pin_rel,), g / "dl", pinned)
            f_bad, how_bad = fetch_set(desk_via, (pin_rel,), g / "dl", {pin_rel: "0" * 64})
        chk("⑩ 同步(假遠端 · 真 git):已 git add 的非收據改動 → 不合併、不動檔、列檔名、差異對 HEAD 抓得到(+1 · XY=M );乾淨 → 合併後跟遠端一致(少 0)", refused and merged, (refused, merged))
        chk("㉖ 同步分類:bridge · state · eol · other · deleted · frozen(改了的非尾版 → 備份 → 還原 HEAD;尾版改了仍是 other)判對 · 未追蹤摘要在;git rm 的舊版從 HEAD 還原 · 壞 JSON state 冊備份後還原 HEAD 版 · bridge 自動 stash 合併放回 · 橋塊留在桌機檔 · stash 清空",
            bridge_ok, (cls_b, cls_s, cls_e, cls_o, cls_d, cls_f, cls_t, sd4.get("fixed_broken_json"), sd4.get("restored_deleted"), sd4.get("restored_frozen"), LOG[-1:] if not bridge_ok else ""))
        chk("㉔ 同步收據類:桌機改了 VIA_Reports 檔(遠端也改)+ 只增冊 → stash → 合併 → 放回:合併提交帶遠端版 · 工作樹留桌機版 · 無衝突記號 · stash 清空",
            receipts_ok, (LOG[-1:], (c3.get("sync_dirty") or {}).get("conflicted")) if not receipts_ok else "")
        chk("㉓ 取檔(釘 SHA):工作樹 SHA 對 → 就地用;工作樹被改 → 從分支 origin 取到 dl 並 LF 化;分支 SHA 也不對 → None 不跑",
            f_tree and f_tree[0] == desk_via / pin_rel and "工作樹" in how_tree and f_br and f_br[0] == g / "dl" / "pinned_v0100.py" and "分支" in how_br
            and f_bad is None and "不是釘住的" in how_bad, (how_tree[:12], how_br[:12], how_bad[:40]))
    chk("⑪ VDF 判燈:rc 0 + 頁上 YELLOW → YELLOW(不升綠)· 有 RED → RED · rc 1 → RED · 全綠 → GREEN",
        vdf_lamp(0, ["GREEN", "YELLOW"]) == "YELLOW" and vdf_lamp(0, ["GREEN", "RED"]) == "RED" and vdf_lamp(1, ["GREEN"]) == "RED" and vdf_lamp(0, ["GREEN"]) == "GREEN")
    st_pass = {"state": "PASS", "per_owner": {"VRN-2": 0}}
    chk("⑫ VRN 判燈:舊 PASS + 本次逾時 rc 124 → RED · 舊 PASS + rc 0(check 模式不重寫)→ YELLOW · 本次 PASS → GREEN · 本次 REVIEW → YELLOW · VRN-2 有待修 → RED",
        vrn_lamp(124, st_pass, False) == "RED" and vrn_lamp(0, st_pass, False) == "YELLOW" and vrn_lamp(0, st_pass, True) == "GREEN"
        and vrn_lamp(2, {"state": "REVIEW", "per_owner": {"VRN-2": 0}}, True) == "YELLOW" and vrn_lamp(2, {"state": "OPEN", "per_owner": {"VRN-2": 1}}, True) == "RED")
    chk("⑬ VCGC 判燈:串測 GREEN + 交接閘紅 → RED · 交接 rc 1 → RED · 沒讀到總行 → RED · 串測 YELLOW + 交接乾淨 → YELLOW · 都綠 → GREEN",
        vcgc_lamp("GREEN", 0, 0, {"EVIDENCE_INVALID": 1}) == "RED" and vcgc_lamp("GREEN", 0, 1, {}) == "RED" and vcgc_lamp(None, 0, 0, {}) == "RED"
        and vcgc_lamp("YELLOW", 2, 0, {}) == "YELLOW" and vcgc_lamp("GREEN", 0, 0, {}) == "GREEN" and vcgc_lamp("GREEN", 1, 0, {}) == "RED")
    with tempfile.TemporaryDirectory(prefix="via_mm_") as td2:
        mm = Path(td2) / "VeritasIntelligenceAnalytics"
        for rel, body in (("functional modules/VDF/engine/VDF_ENG001_A_v0100.py", "x = 1\n"),
                          ("functional modules/VDF/engine/VDF_ENG001_A_v0101.py", '"""引擎 A · 說明首行\n\n多行。"""\n# [VIA:ACCEL-BRIDGE:v0111]\nimport os\nimport pandas\nfrom VIA_Lib import q\n\n\nclass K:\n    def m(self):\n        return q\n\n\ndef f():\n    return os\n\n\ndef f():\n    return pandas\n'),
                          ("supportive modules/registry/CGC_MDL001_B_v0100.py", "# 冊 B\nimport requests\n\n\ndef g():\n    return requests\n"),
                          ("functional modules/VRN/VRN_SystemManager_v0100.py", "def h(:\n"),
                          ("functional modules/VRN/_quarantine/VRN_X_v0100.py", "x = 1\n"), ("functional modules/VRN/notes.py", "x = 1\n")):
            (mm / rel).parent.mkdir(parents=True, exist_ok=True)
            (mm / rel).write_text(body, encoding="utf-8")
        (mm / "supportive modules" / "registry" / "VIA_VCGC_FunctionLedger_v0100.jsonl").write_text(json.dumps({"ts": "2026-11-06T00:00:00+00:00", "event": "changed", "id": "family:CGC_MDL001_B", "kind": "family", "file": "CGC_MDL001_B_v0100.py", "version": "v0100", "lamp": "GREEN"}) + "\n", encoding="utf-8")
        (mm / "supportive modules" / "registry" / "VIA_NumberBooks").mkdir(parents=True)
        (mm / "supportive modules" / "registry" / "VIA_NumberBooks" / "VIA_NumberBook_ENG_v0100.jsonl").write_text(json.dumps({"code": "VIA-VDF-ENG001", "name": "VDF_ENG001_A_v0101", "numbered_at": "2026-09-28 15:31:52 +0000", "kind": "ENG"}) + "\n", encoding="utf-8")
        (mm / "VIA_Reports" / "settle").mkdir(parents=True)
        (mm / "VIA_Reports" / "settle" / "VDF_Engines_Matrix_latest.json").write_text(json.dumps({"engines": [{"engine": "VDF_ENG001_A_v0101.py", "rc": 0, "lamp": "GREEN", "secs": 3}]}), encoding="utf-8")
        card = module_card(mm / "functional modules" / "VDF" / "engine" / "VDF_ENG001_A_v0101.py")
        chk("㉗ 模組卡(只 AST 不執行):說明首行 · 類 1 · 函式 3(含方法)· 第三方只有 pandas(os 標準庫不算 · VIA_Lib 算內部 1)· 重複頂層定義 f · 加速器橋旗標 · 沒錯",
            card["desc"] == "引擎 A · 說明首行" and card["cls"] == 1 and card["fnc"] == 3 and card["libs"] == ["pandas"] and card["internal"] == 1 and card["dupdef"] == ["f"] and card["accel"] and not card["error"], card)
        n0 = len(LOG)
        LOG.append({"lamp": "YELLOW", "step": "④ VDF ui", "text": "假", "next": "", "secs": 1})
        exp4 = _lamp_of("④")[0]
        cm = {"vdfeng": {"lamp": "GREEN"}, "run_id": "t"}
        stage_modmatrix(mm, cm)
        mrows = {r["name"]: r for r in json.loads((mm / "VIA_Reports" / "settle" / "VIA_ModuleMatrix_latest.json").read_text(encoding="utf-8"))["rows"]}
        mm_md = (mm / "VIA_Reports" / "settle" / "VIA_ModuleMatrix_latest.md").read_text(encoding="utf-8")
        led = (mm / "VIA_Reports" / "settle" / "VIA_ModuleMatrix_Ledger.jsonl").read_text(encoding="utf-8").splitlines()
        rows_sys = matrix_rows(mm, dict(cm, families={}))
        del LOG[n0:]
        chk("㉘ 模組矩陣:只看尾版 v0101 · 隔離夾 / 沒版號的檔不算 · VDF 第一欄 = ④ 的燈 · VCGC 編號從 ENG 冊查到(MDL 冊沒有的不冒充) · STATUS:VDF 取 ⑬ 自測綠 · CGC 取 VCGC 功能帳綠(同版)· VRN 語法錯 🔴(段燈 RED)· "
            "網路 import 沒橋記在 ERROR & AST · 綠的 2 列進只增帳 · md 有 SYSTEM / FUNCTION … STATUS 欄 · html 在 · ⑫ 多一列模組矩陣",
            set(mrows) == {"VDF_ENG001_A_v0101.py", "CGC_MDL001_B_v0100.py", "VRN_SystemManager_v0100.py"} and mrows["VDF_ENG001_A_v0101.py"]["sys_lamp"] == exp4 and mrows["VDF_ENG001_A_v0101.py"]["lamp"] == "GREEN"
            and mrows["VDF_ENG001_A_v0101.py"]["cls"] == 1 and mrows["VDF_ENG001_A_v0101.py"]["vcgc_no"] == "VIA-VDF-ENG001" and mrows["CGC_MDL001_B_v0100.py"]["vcgc_no"] == "未登號" and mrows["CGC_MDL001_B_v0100.py"]["lamp"] == "GREEN" and "功能帳" in mrows["CGC_MDL001_B_v0100.py"]["status"] and "網路 import 沒網路橋" in mrows["CGC_MDL001_B_v0100.py"]["issues"]
            and mrows["VRN_SystemManager_v0100.py"]["lamp"] == "RED" and cm["modmatrix"]["lamp"] == "RED" and len(led) == 2 and "| SYSTEM | FUNCTION | DESCRIPTION | MDL / ENG NAME · VCGC 編號 | CLS | FNC | LIBS | ERROR & AST | STATUS |" in mm_md
            and (mm / "VIA_Reports" / "settle" / "VIA_ModuleMatrix_latest.html").is_file() and cm["modmatrix"]["rows"] == 3 and any(r["system"] == "模組矩陣 ⑭" and r["lamp"] == "RED" for r in rows_sys),
            (sorted(mrows), {k: (v["sys_lamp"], v["lamp"], v["issues"]) for k, v in mrows.items()}, len(led), cm.get("modmatrix", {}).get("lamp")))
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    dirs = set(re.findall(r'"VIA_Reports"\s*/\s*"(\w+)"', body))
    chk("⑨ 橋在 · 不強推 · 不 rebase · 不 push · 不 pip · 不寫他系統的檔(VIA_Reports 只碰 settle / agent_os / graphify;vrn2 / vdf / vqg 只讀)",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and "\"--force\"" not in body and "force-with-lease" not in body and "\"rebase\"" not in body and "\"push\", \"origin\"" not in body
        and "\"push\", \"-u\"" not in body and "\"pip\"" not in body and dirs <= {"settle", "agent_os", "graphify", "vrn2", "vdf", "vqg", "vcgc"}, sorted(dirs))
    bad = len(ok) - sum(ok)
    print("[%s] %s %s --selftest · %d 項 · 不過 %d" % ("PASS" if not bad else "FAIL", NAME, VERSION, len(ok), bad), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):       # Windows 主控台不是 UTF-8 時也能印中文(印不出就照原樣)
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="%s_%s" % (NAME, VERSION), description="全景檢視 → 同步 → VDF ui(AST 定位)→ VRN 狀態 → VCGC 驗 → Graphify(看門狗)→ VQG(VDF 多家探根)→ Agent OS → 報告 · 各系統只經自己的入口")
    ap.add_argument("--root")
    ap.add_argument("--only", default=",".join(STAGES))
    ap.add_argument("--no-sync", action="store_true")
    ap.add_argument("--vrn", choices=("status", "repair", "check", "skip"), default="status")
    ap.add_argument("--graphify-floor-gb", type=float, default=0.75)
    ap.add_argument("--serial", action="store_true", help="④⑤⑧⑨ 一個一個跑(預設併行)")
    ap.add_argument("--graphify", choices=("changed", "all", "skip"), default="changed", help="changed = 程式沒變沿用上一張 · 記憶體不夠不跑(預設)")
    ap.add_argument("--force-old-tree", action="store_true", help="③ 沒同步也在舊版上跑 ④ ⑥ ⑬")
    ap.add_argument("--vdf-budget", type=int, default=1200, help="⑬ VDF 全引擎自測總預算秒(預設 1200)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    via = find_root(a.root)
    if via is None:
        say("RED", "⓪ VIA 根", "找不到(查過 --root · VIA_ROOT · 本檔所在 · OneDrive\\Documents\\movies-dataset)", "加 --root <倉根>")
        return 1
    tick("⓪")
    say("GREEN", "⓪ VIA 根", str(via))
    only = [s.strip() for s in a.only.split(",") if s.strip()]
    ctx = {"tool": NAME + " " + VERSION, "root": str(via), "branch": BRANCH, "run_id": _dt.datetime.now().strftime("%Y%m%d_%H%M%S")}
    if "scan" in only:
        stage_scan(via, ctx)
    if "sync" in only:
        stage_sync(via, ctx, not a.no_sync)
    light = [("④ VDF ui", lambda: stage_vdf(via, ctx, a.force_old_tree)), ("⑤ VRN", lambda: stage_vrn(via, ctx, a.vrn)), ("⑧ VQG", lambda: stage_vqg(via, ctx)), ("⑨ Agent OS", lambda: stage_agentos(via, ctx))]
    light = [(n, f) for (n, f), key in zip(light, PARALLEL) if key in only]
    if light and not a.serial:
        print("[計] ④⑤⑧⑨ 併行(%s)· 各寫各的收據夾 · 輸出行會交錯 · 報告照步驟排" % " · ".join(n for n, _ in light), flush=True)
        run_parallel(light)
    else:
        for _, f in light:
            f()
    if "vcgc" in only:
        stage_vcgc(via, ctx, a.force_old_tree)
    if "graphify" in only:
        stage_graphify(via, ctx, a.graphify_floor_gb, mode=a.graphify)
    if "policy" in only:
        stage_policy(via, ctx)
    if "vdfeng" in only:
        stage_vdfeng(via, ctx, budget_s=a.vdf_budget, force_old=a.force_old_tree)
    if "modmatrix" in only:
        stage_modmatrix(via, ctx)
    if "matrix" in only:
        stage_matrix(via, ctx)
    if "report" in only:
        stage_report(via, ctx)
    return 1 if any(x["lamp"] == "RED" for x in LOG) else 2 if any(x["lamp"] == "YELLOW" for x in LOG) else 0


if __name__ == "__main__":
    sys.exit(main())
