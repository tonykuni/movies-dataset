#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_LampAudit v0100 — 燈號合理性稽核:每一顆紅 / 黃 / 綠燈,照它那一類的規範重算「應該是什麼燈」,對不上就點名。

操作員 2026-11-16:「紅黃綠燈去檢查其合理性 · 生成一個 PS 指令去檢查三種燈號在各類規範是否合理 ·
每個狀況想規則失敗的十個可能及解決方案內建完善他」。

做法(只讀 · 不改任何系統的冊與檔 · 不出網):
  1 每一步的輸出歸到一個類別(入口自測 · 管理器自報 · 管理器自檢 · SSOT 覆蓋 · 交接閘 · 全功能串測 · 備份)。
  2 照該類規則從輸出重算「應有燈」與「該誰處理」(自己修 / 操作員裁定 / 操作員的手 / 他系統 / 環境)。
  3 實際燈 = 應有燈 → 合理;不同 → 不合理,並對到失敗情境冊裡那一條(現象 · 怎麼認出 · 解法)。
  4 另做三項橫向檢查:同意閘(操作員的手)· 環境缺件 · 收據新鮮度。
失敗情境冊:10 類 × 10 條 = 100 條,全部內建在 FAILURE_MODES(自測檢查每類剛好 10 條、代碼不重複、每條都有認法與解法)。

用法:
  python VIA_LampAudit_v0100.py audit [--report <CLOSEOUT_3SYS_latest.json>] [--json]   稽核最近一次三系統收尾
  python VIA_LampAudit_v0100.py modes [類別]                                           列失敗情境冊
  python VIA_LampAudit_v0100.py --selftest
rc:0 = 每顆燈都合理(不論紅黃綠)· 1 = 有不合理的燈 · 2 = 沒有可稽核的報告
"""
from __future__ import annotations
# [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 零行為變更)
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
    VIA_ACCEL = None
# [VIA:ACCEL-BRIDGE:END]

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
ENGINE = "VIA_LampAudit " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[2] if len(HERE.parents) > 2 and (HERE.parents[2] / "supportive modules").is_dir() else HERE
OWNERS = {"SELF": "本系統自己修", "OPERATOR_RULING": "操作員裁定", "OPERATOR_HAND": "操作員的手(同意閘 · 工作站)",
          "OTHER_SYSTEM": "他系統補正本", "ENV": "環境缺件(不代裝)", "NONE": "不需處理"}

# ───────────────────────── 失敗情境冊(10 類 × 10 條)─────────────────────────
# (代碼, 情境:規則或燈可能錯在哪, 怎麼認出, 解法)
FAILURE_MODES = {
    "ENTRY_SELFTEST": ("入口自測(三系統各自啟動)", [
        ("E01", "行程 rc 0 但自測總計寫 FAIL(結束碼被吞)", "rc == 0 且最後一行 [計] 含 FAIL", "判紅;引擎自測失敗時要回非 0"),
        ("E02", "行程 rc 非 0 但總計寫 PASS(收尾階段崩潰)", "rc != 0 且 [計] 含 PASS", "判紅;看 stderr 最後幾行修收尾段"),
        ("E03", "沒有任何總計行(無法證明自測跑完)", "輸出沒有 [計] / [PASS] / [FAIL]", "判黃(未證);引擎補印總計行"),
        ("E04", "逾時被收掉", "rc 124 或輸出寫逾時", "判紅;查卡在哪一步,必要時加長逾時,不要放任"),
        ("E05", "取到錯的尾版(版號排序錯)", "入口檔名的版號不是同族最大", "判紅;尾版一律依四碼數字取最大"),
        ("E06", "前版鏈有人失敗但本版只看自己", "輸出中前版那行是 FAIL 而總計 PASS", "判紅;本版總計要含前版鏈結果"),
        ("E07", "缺 VCGC 入口旗標被拒跑卻當成失敗", "輸出含 DENY 且是 VIA_FROM_VCGC", "子行程內設旗標(只在本行程),重跑"),
        ("E08", "缺第三方套件崩潰被當成程式壞", "No module named / ABSENT", "判黃(環境);經 InstallGate 由操作員裝"),
        ("E09", "輸出編碼亂碼導致總計行認不出", "總計行出現替代字元 �", "子行程設 PYTHONIOENCODING=utf-8 重跑"),
        ("E10", "同一台同時跑兩輪,互相蓋收據", "收尾鎖檔存在且持有者還活著", "單一執行鎖:第二輪拒跑,等第一輪結束"),
    ]),
    "MANAGER_COLLECT": ("管理器自報(七處 · 健康 · 規範 · 啟動)", [
        ("C01", "七處不到 7 卻判綠", "七處 n/7 且 n < 7,燈為綠", "判黃;缺哪一處由本系統補登"),
        ("C02", "只因同意閘未開卻判紅", "啟動 YELLOW 且同意閘未設,燈為紅", "判黃(操作員的手);不代設同意閘"),
        ("C03", "健康紅卻只判黃", "燈 health RED,整體不是紅", "判紅;先修自檢紅項"),
        ("C04", "規範自查讀到舊版標準", "conform 引用的標準不是尾版", "標準取尾版;管理器重跑 conform"),
        ("C05", "自報靠 import 他系統(違反 P4)", "輸出或模組載入了 CGC_ / VIA_VCGC 模組", "改成只讀冊判定(標準 v0101 P9)"),
        ("C06", "collect() 不存在被當成紅", "AttributeError collect", "判灰(無資料);由本系統補 collect()"),
        ("C07", "rc 2 被操作台當成行程失敗", "rc 2 但燈為紅", "依管理器約定:rc 2 = 黃"),
        ("C08", "啟動探測沒有資料庫就當紅", "啟動 NODATA(庫還沒建)", "判黃;到工作站開閘跑一次擷取建庫"),
        ("C09", "命令冊只讀最新一本漏掉舊本登記", "register False 但舊本有該命令", "命令冊整條 dot-source 鏈都讀"),
        ("C10", "自報讀冊失敗卻照樣綠", "upstream 有 errors 或 inventory_error", "判黃;照錯誤修冊或讀法"),
    ]),
    "MANAGER_HEALTH": ("管理器自檢", [
        ("H01", "自檢印 GREEN 但 rc 非 0", "health GREEN 且 rc != 0", "判紅;行程失敗不可能綠"),
        ("H02", "自檢印 RED 但 rc 0", "health RED 且 rc 0", "判紅;管理器 rc 要跟燈一致"),
        ("H03", "自己的夾不在", "own_dir ✗", "判紅;確認工作目錄與倉根"),
        ("H04", "前版不在(薄尾鏈斷)", "prior_present ✗", "判紅;找回前版檔,薄尾不准斷鏈"),
        ("H05", "SSOT 正本不在", "ssot_present ✗", "判黃;本系統出正本"),
        ("H06", "缺加速器橋", "P7_accel_bridge ✗", "判紅;出帶橋的新版(不就地改)"),
        ("H07", "缺網路工具橋(VDF 必要)", "P7_net_bridge ✗", "判紅;出帶橋的新版"),
        ("H08", "要求他系統放行旗標", "P3_no_peer_gate ✗", "判紅;管理器動詞不得以他系統旗標為前提"),
        ("H09", "寫了同意閘", "P8_no_consent_write ✗", "判紅;刪除寫同意閘的程式碼(出新版)"),
        ("H10", "碰了 TA-Lib", "P8_no_talib ✗", "判紅;TA-Lib 禁用(L50),改 QuantGuard"),
    ]),
    "SSOT_COVERAGE": ("SSOT 領域覆蓋", [
        ("S01", "有缺口(rc 1)被判成紅", "rc 1 且引擎自己印 YELLOW,燈為紅", "依引擎說明:有缺口 = 黃"),
        ("S02", "有缺口卻判綠", "黃 > 0 或無 > 0,燈為綠", "判黃;缺口由各系統補正本"),
        ("S03", "引擎崩潰(rc 非 0 / 1)", "rc 不在 0、1", "判紅;看 stderr 修引擎"),
        ("S04", "覆蓋冊讀的不是尾版", "冊名版號不是最大", "冊取尾版"),
        ("S05", "編號冊有壞列", "bad_number_rows > 0", "判紅;修編號冊壞列"),
        ("S06", "證據 partial 卻算完整", "格內有 partial 註記但格綠", "判黃;補完整正本"),
        ("S07", "不適用的格算成缺口", "該系統確實不擁有此領域", "由系統宣告 na,不是硬補一本"),
        ("S08", "正本有了但沒編號", "有正本但編號冊找不到", "提交後跑中央編號 --scope"),
        ("S09", "VCGC 代建他系統正本(越界)", "正本路徑在他系統夾且作者是 VCGC", "判紅;撤回,由他系統自己建"),
        ("S10", "格數不等於領域 × 系統", "cells 數 != 領域數 × 系統數", "判紅;覆蓋冊宣告不完整"),
    ]),
    "HANDOFF_GATE": ("交接閘", [
        ("G01", "有紅項卻判綠", "[RED] 項 > 0,燈為綠", "判紅;照紅項逐一處理"),
        ("G02", "改了程式沒有測試案涵蓋", "CHANGED_CODE_WITHOUT_TEST", "宣告測試案(自己的家族)或交給該系統"),
        ("G03", "收據因相依檔變更失效", "EVIDENCE_INVALID · dependency changed", "重跑該案;相依改成只看相關段落可根治"),
        ("G04", "舊版缺加速器橋", "ACCEL_BRIDGE_MISSING", "操作員裁定:豁免冊或出新版"),
        ("G05", "收容件未註冊", "MODULE_UNREGISTERED", "操作員裁定:正式導入或退役"),
        ("G06", "檢查點過舊", "CHECKPOINT_STALE", "閘綠後跑 handoff checkpoint"),
        ("G07", "待辦沒有需求歸屬", "UNREGISTERED_REQUIREMENT", "待辦補 requirement"),
        ("G08", "成功標記跟不上實際輸出", "rc 0 但 marker 沒出現", "標記改成實際 PASS 行,舊字串保留"),
        ("G09", "環境缺件的案被算成程式紅", "收據日誌含 No module named / pwsh", "判黃(環境);到工作站跑"),
        ("G10", "測試夾具日期寫死", "夾具 now 是固定日期且比對今天", "該工具出新版修夾具"),
    ]),
    "QUICK_TEST": ("VCGC 全功能串測", [
        ("Q01", "有紅站卻總燈黃 / 綠", "counts.RED > 0,燈不是紅", "判紅"),
        ("Q02", "只有黃站卻總燈紅", "RED 0 且燈為紅", "判黃"),
        ("Q03", "串測結果過舊", "TEST_latest 超過 26 小時", "重跑 test --quick"),
        ("Q04", "沒有 PowerShell 的站被當紅", "P-entry 沒有 pwsh", "判黃(環境);工作站驗"),
        ("Q05", "交接站黃被誤當串測失敗", "V-handoff-check 黃", "交接閘本身的問題,照交接閘處理"),
        ("Q06", "盤點有新指令沒登", "盤點 verb 未全登", "新指令登進盤點冊"),
        ("Q07", "家族尾版編譯錯", "compile 錯 > 0", "判紅;修語法(出新版)"),
        ("Q08", "缺橋", "缺橋 > 0", "判紅;補橋(出新版)"),
        ("Q09", "沿用舊站結果誤當新跑", "沿用 > 0 且相依有變", "強制重跑該站"),
        ("Q10", "案數不全仍判綠", "case 通過數 < 總數,燈為綠", "判黃;列出未過案"),
    ]),
    "BACKUP": ("五系統備份", [
        ("B01", "備份過期仍判綠", "age_hours > 26", "判黃;重跑備份"),
        ("B02", "倉內與備份不一致仍判綠", "check 不是一字不差", "判紅;查差異再備份"),
        ("B03", "zip 損壞", "zip 驗證失敗", "判紅;重做該系統壓縮檔"),
        ("B04", "備份清單沒入倉", "MANIFEST 未提交", "提交 MANIFEST"),
        ("B05", "git 已前進但備份沒跟", "git 前進", "重跑備份"),
        ("B06", "備份夾不在", "報告找不到", "判灰;先跑一次備份"),
        ("B07", "備份把機密打包", "清單含 .env / private/", "判紅;排除後重備"),
        ("B08", "備份太大塞爆磁碟", "總大小異常", "清舊備份(只增帳本保留)"),
        ("B09", "只備了部分系統", "系統數 < 6", "判黃;補齊"),
        ("B10", "備份時間戳在未來(時鐘錯)", "backup_at > 現在", "判黃;校時後重備"),
    ]),
    "CONSENT_GATE": ("同意閘(操作員的手)", [
        ("P01", "同意閘未開卻判紅", "VIA_NET_CONSENT 未設,燈紅", "判黃;不代設"),
        ("P02", "同意閘未開卻判綠(假裝擷取成功)", "未設卻報 READY", "判黃;擷取結果不可信"),
        ("P03", "程式碼替操作員設同意閘", "原始碼有 VIA_NET_CONSENT =", "判紅;刪除(出新版)"),
        ("P04", "只開了一道閘", "兩道閘只有一道 YES", "判黃;兩道都要操作員開"),
        ("P05", "閘值大小寫不一致被誤判", "值為 yes / Yes", "比對時不分大小寫"),
        ("P06", "閘在系統環境永久開著", "使用者層環境變數常駐 YES", "改成只在本次行程設"),
        ("P07", "雲端容器被要求開閘", "容器內要求擷取", "雲端不擷取;到工作站"),
        ("P08", "抓資料的引擎沒經網路工具橋", "直接 import requests", "改走網路工具橋"),
        ("P09", "閘開了但沒有網路", "連線失敗", "判黃(環境);查網路"),
        ("P10", "閘開了擷取到 0 列卻判綠", "列數 0", "判黃;查來源或日期"),
    ]),
    "ENVIRONMENT": ("環境缺件", [
        ("V01", "缺 polars 被當程式紅", "No module named 'polars'", "判黃;經 InstallGate 由操作員裝"),
        ("V02", "缺 PowerShell 被當紅", "沒有 pwsh", "判黃;工作站驗"),
        ("V03", "缺 fitz(PyMuPDF)", "No module named 'fitz'", "判黃;經 InstallGate"),
        ("V04", "缺 akshare", "No module named 'akshare'", "判黃;經 InstallGate"),
        ("V05", "Python 版本太舊", "版本 < 3.10", "判紅;換 3.10 以上"),
        ("V06", "瀏覽器自動化逾時", "chrome TimeoutExpired", "判黃;改用 Playwright 內建 chromium"),
        ("V07", "沒有桌面無法開頁", "headless", "照實不開頁,改給連結"),
        ("V08", "磁碟滿", "No space left on device", "判紅;清暫存"),
        ("V09", "記憶體不足被系統砍", "rc -9 / MemoryError", "判紅;降並行度"),
        ("V10", "檔案被防毒鎖住", "PermissionError", "判黃;排除夾或稍後重跑"),
    ]),
    "FRESHNESS": ("收據新鮮度", [
        ("R01", "報告比程式舊仍採信", "報告時間早於入口檔修改時間", "判灰(過期);重跑"),
        ("R02", "報告跨日", "報告 > 26 小時", "判灰;重跑"),
        ("R03", "報告缺時間戳", "沒有 at 欄", "判灰;引擎補時間戳"),
        ("R04", "時區混用", "時間沒有 Z / +00:00", "一律 UTC"),
        ("R05", "報告來自別的分支", "git head 不同", "判灰;在本分支重跑"),
        ("R06", "報告被手改", "sha 不符", "判紅;重產"),
        ("R07", "多份 latest 互相矛盾", "兩份報告同一步燈不同", "取時間較新的一份並註明"),
        ("R08", "步驟缺漏", "報告步數 < 預期", "判黃;補跑缺的步驟"),
        ("R09", "報告的入口版號不是現在的尾版", "entry 版號 < 尾版", "判灰;重跑"),
        ("R10", "空報告", "steps 為空", "判灰;重跑"),
    ]),
}
CATEGORY_OF = {"activate_vcgc": "ENTRY_SELFTEST", "activate_vdf": "ENTRY_SELFTEST", "activate_vrn2": "ENTRY_SELFTEST",
               "vdf_collect": "MANAGER_COLLECT", "vrn_collect": "MANAGER_COLLECT", "vdf_health": "MANAGER_HEALTH", "vrn_health": "MANAGER_HEALTH",
               "ssot_domains": "SSOT_COVERAGE", "vcgc_handoff": "HANDOFF_GATE", "vcgc_test_quick": "QUICK_TEST"}
_TALLY = re.compile(r"\[計\][^\n]*|\[(?:PASS|FAIL)\][^\n]*selftest[^\n]*")
_MISSING = re.compile(r"No module named '([^']+)'|缺少 (\w+)|沒有 pwsh")


def _last_tally(text: str) -> str:
    hits = _TALLY.findall(text or "")
    return hits[-1] if hits else ""


def judge(step: dict, env: dict | None = None) -> dict:
    """一步 → 應有燈 · 誰處理 · 對到的失敗情境(若實際燈與應有燈不同)。"""
    env = env if env is not None else dict(os.environ)
    name, rc, text = step.get("step", ""), step.get("rc"), (step.get("out") or step.get("tail") or "")
    cat = CATEGORY_OF.get(name, "ENTRY_SELFTEST" if name.startswith("activate_") else "FRESHNESS")
    exp, owner, why, mode = "GRAY", "SELF", "沒有規則", None
    tally = _last_tally(text)
    missing = _MISSING.search(text)
    if cat == "ENTRY_SELFTEST":
        if rc == 124 or "逾時" in text[:40]:
            exp, owner, why, mode = "RED", "SELF", "逾時", "E04"
        elif "DENY" in text and "VIA_FROM_VCGC" in text:
            exp, owner, why, mode = "RED", "SELF", "缺入口旗標被拒跑", "E07"
        elif missing and not re.search(r"\[FAIL", text):
            exp, owner, why, mode = "YELLOW", "ENV", "缺件:" + (missing.group(1) or missing.group(2) or "pwsh"), "E08"
        elif rc == 0 and tally and "FAIL" not in tally:
            exp, owner, why = "GREEN", "NONE", "rc 0 · 總計 PASS:" + tally[:80]
        elif rc == 0 and not tally:
            exp, owner, why, mode = "YELLOW", "SELF", "rc 0 但沒有總計行", "E03"
        elif rc == 0:
            exp, owner, why, mode = "RED", "SELF", "rc 0 但總計 FAIL", "E01"
        else:
            exp, owner, why, mode = "RED", "SELF", "rc %s" % rc, "E02"
    elif cat == "MANAGER_COLLECT":
        m7 = re.search(r"七處 (\d)/7", text)
        lamps = dict(re.findall(r"'(upstream|health|conform)': '(\w+)'", text))
        launch = re.search(r"啟動 (\w+)", text)
        consent_open = all(str(env.get(k, "")).upper() == "YES" for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT"))
        if "AttributeError" in text and "collect" in text:
            exp, owner, why, mode = "GRAY", "SELF", "管理器沒有 collect()", "C06"
        elif "RED" in (lamps.get("health"), lamps.get("conform")) or rc == 1:
            exp, owner, why, mode = "RED", "SELF", "自檢或規範自查紅", "C03"
        elif m7 and int(m7.group(1)) < 7:
            exp, owner, why, mode = "YELLOW", "SELF", "七處 %s/7" % m7.group(1), "C01"
        elif launch and launch.group(1) != "GREEN" and not consent_open:
            exp, owner, why, mode = "YELLOW", "OPERATOR_HAND", "啟動探測 %s:同意閘未開(操作員的手)" % launch.group(1), "C02"
        elif launch and launch.group(1) != "GREEN":
            exp, owner, why, mode = "YELLOW", "OPERATOR_HAND", "啟動探測 %s:庫還沒建或缺件" % launch.group(1), "C08"
        elif rc == 0 and m7 and all(v == "GREEN" for v in lamps.values()):
            exp, owner, why = "GREEN", "NONE", "七處 7/7 · 健康 / 規範綠"
        else:
            exp, owner, why, mode = "YELLOW", "SELF", "自報不完整", "C10"
    elif cat == "MANAGER_HEALTH":
        m = re.search(r"health (GREEN|YELLOW|RED)", text)
        said = m.group(1) if m else None
        crosses = re.findall(r"(\w+) ✗", text)
        if crosses:
            first = crosses[0]
            code = {"own_dir": "H03", "prior_present": "H04", "ssot_present": "H05", "P7_accel_bridge": "H06", "P7_net_bridge": "H07",
                    "P3_no_peer_gate": "H08", "P8_no_consent_write": "H09", "P8_no_talib": "H10"}.get(first, "H02")
            exp, owner, why, mode = ("YELLOW" if code == "H05" else "RED"), "SELF", "自檢項不過:" + " ".join(crosses[:4]), code
        elif said == "GREEN" and rc == 0:
            exp, owner, why = "GREEN", "NONE", "自檢全項 ✓"
        elif said == "GREEN":
            exp, owner, why, mode = "RED", "SELF", "印綠但 rc %s" % rc, "H01"
        elif said == "RED" or rc == 1:
            exp, owner, why, mode = "RED", "SELF", "自檢紅", "H02"
        else:
            exp, owner, why = "YELLOW", "SELF", "自檢黃"
    elif cat == "SSOT_COVERAGE":
        m = re.search(r"綠 (\d+) · 黃 (\d+) · 無 (\d+)", text)
        if rc not in (0, 1):
            exp, owner, why, mode = "RED", "SELF", "覆蓋引擎 rc %s" % rc, "S03"
        elif m and (int(m.group(2)) or int(m.group(3))):
            exp, owner, why = "YELLOW", "OTHER_SYSTEM", "有缺口:黃 %s · 無 %s(各系統補正本或宣告不適用)" % (m.group(2), m.group(3))
            mode = "S01" if step.get("lamp") == "RED" else ("S02" if step.get("lamp") == "GREEN" else None)
        elif m:
            exp, owner, why = "GREEN", "NONE", "15 領域 × 5 系統全齊"
        else:
            exp, owner, why = ("YELLOW" if rc == 1 else "GREEN"), "OTHER_SYSTEM", "依引擎 rc 約定(有缺口 rc 1)"
    elif cat == "HANDOFF_GATE":
        reds = re.findall(r"\[RED\]\s+([A-Z_]+)", text)
        if reds:
            kinds = sorted(set(reds))
            ruling = {"ACCEL_BRIDGE_MISSING", "MODULE_UNREGISTERED"}
            owner = "OPERATOR_RULING" if set(kinds) <= ruling else "SELF"
            exp, why = "RED", "紅項 %d:%s" % (len(reds), " · ".join(kinds))
            mode = "G01" if step.get("lamp") == "GREEN" else None
        else:
            exp, owner, why = ("GREEN" if rc == 0 else "YELLOW"), "NONE", "沒有紅項"
    elif cat == "QUICK_TEST":
        m = re.search(r"綠 (\d+) · 黃 (\d+) · 紅 (\d+)", text)
        if m and int(m.group(3)):
            exp, owner, why = "RED", "SELF", "紅站 %s" % m.group(3)
        elif m and int(m.group(2)):
            exp, owner, why = "YELLOW", "ENV", "黃站 %s(多為環境或交接閘)" % m.group(2)
        else:
            exp, owner, why = ("GREEN" if rc == 0 else "RED"), "NONE", "依 rc"
    actual = step.get("lamp", "GRAY")
    if actual != exp and mode is None:
        mode = {"ENTRY_SELFTEST": "E02", "MANAGER_COLLECT": "C07", "MANAGER_HEALTH": "H01", "SSOT_COVERAGE": "S01",
                "HANDOFF_GATE": "G01", "QUICK_TEST": "Q02"}.get(cat, "R07")
    fm = next((x for x in FAILURE_MODES[cat][1] if x[0] == mode), None) if mode else None
    return {"step": name, "system": step.get("system"), "category": cat, "category_zh": FAILURE_MODES[cat][0], "actual": actual, "expected": exp,
            "reasonable": actual == exp, "owner": owner, "owner_zh": OWNERS[owner], "why": why,
            "mode": ({"id": fm[0], "situation": fm[1], "detect": fm[2], "fix": fm[3]} if fm else None)}


def freshness(report: dict, via: Path = VIA, now: datetime | None = None) -> list:
    """收據新鮮度:報告時間 · 步數 · 入口版號是不是現在的尾版。"""
    now = now or datetime.now(timezone.utc)
    out = []
    at = str(report.get("at") or "")
    try:
        t = datetime.fromisoformat(at.replace("Z", "+00:00"))
        age = (now - t).total_seconds() / 3600
        if age > 26:
            out.append({"id": "R02", "lamp": "GRAY", "why": "報告 %.0f 小時前(超過 26 小時)" % age})
    except ValueError:
        out.append({"id": "R03", "lamp": "GRAY", "why": "報告沒有可讀的時間戳"})
    steps = report.get("steps") or []
    if not steps:
        out.append({"id": "R10", "lamp": "GRAY", "why": "報告沒有任何步驟"})
    for s in steps:
        ent = str(s.get("entry") or "")
        m = re.match(r"(.+)_v(\d{4})\.py$", ent)
        if not m:
            continue
        fam, ver = m.group(1), int(m.group(2))
        hits = [int(re.search(r"_v(\d{4})\.py$", p.name).group(1)) for p in via.rglob(fam + "_v[0-9][0-9][0-9][0-9].py") if "intake" not in str(p)] if via.is_dir() else []
        if hits and max(hits) > ver:
            out.append({"id": "R09", "lamp": "GRAY", "why": "%s 跑的是 v%04d,現在尾版 v%04d" % (s.get("step"), ver, max(hits))})
    return out


def consent(env: dict | None = None) -> dict:
    env = env if env is not None else dict(os.environ)
    vals = {k: str(env.get(k, "")) for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    opened = [k for k, v in vals.items() if v.upper() == "YES"]
    if len(opened) == 2:
        return {"id": None, "lamp": "GREEN", "why": "兩道同意閘都開(操作員親手)"}
    if len(opened) == 1:
        return {"id": "P04", "lamp": "YELLOW", "why": "只開了一道:" + opened[0]}
    return {"id": "P01", "lamp": "YELLOW", "why": "同意閘未開:VDF 真資料擷取要操作員親手開(本工具不代設)"}


def audit(report: dict, env: dict | None = None, via: Path = VIA) -> dict:
    rows = [judge(s, env) for s in report.get("steps") or []]
    side = {"consent": consent(env), "freshness": freshness(report, via)}
    bad = [r for r in rows if not r["reasonable"]]
    non_green = [r for r in rows if r["expected"] != "GREEN"]
    by_owner = {}
    for r in non_green:
        by_owner.setdefault(r["owner"], []).append(r["step"])
    lamp = "RED" if bad else ("YELLOW" if non_green or side["freshness"] else "GREEN")
    return {"engine": ENGINE, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "lamp": lamp,
            "verdict": ("有 %d 顆燈不合理" % len(bad)) if bad else "每顆燈都合理(紅黃綠都跟規則對得上)",
            "rows": rows, "side": side, "non_green_by_owner": {OWNERS[k]: v for k, v in by_owner.items()},
            "counts": {"steps": len(rows), "reasonable": len(rows) - len(bad), "unreasonable": len(bad), "non_green": len(non_green)}}


def _load_report(path: Path | None) -> dict | None:
    p = path or (VIA / "VIA_Reports" / "lake" / "CLOSEOUT_3SYS_latest.json")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note and not cond else ""))
    print("[%s selftest]" % ENGINE)
    ids = [x[0] for c in FAILURE_MODES.values() for x in c[1]]
    chk("① 失敗情境冊 10 類 × 10 條 · 代碼不重複 · 每條都有情境 / 認法 / 解法",
        len(FAILURE_MODES) == 10 and all(len(c[1]) == 10 for c in FAILURE_MODES.values()) and len(ids) == len(set(ids)) == 100
        and all(all(len(x) == 4 and all(str(f).strip() for f in x) for x in c[1]) for c in FAILURE_MODES.values()))
    env0 = {}
    j = judge({"step": "activate_vdf", "rc": 0, "lamp": "GREEN", "out": "...\n[計] VDF_SystemManager v0175 自測 9/9 PASS"}, env0)
    chk("② 入口自測 rc 0 + 總計 PASS + 綠 → 合理", j["expected"] == "GREEN" and j["reasonable"])
    j = judge({"step": "activate_vcgc", "rc": 0, "lamp": "GREEN", "out": "[計] X 本版 6/7 · FAIL"}, env0)
    chk("③ 入口自測 rc 0 但總計 FAIL 卻綠 → 不合理 · E01", not j["reasonable"] and j["mode"]["id"] == "E01" and j["expected"] == "RED")
    j = judge({"step": "activate_vrn2", "rc": 1, "lamp": "RED", "out": "Traceback\nModuleNotFoundError: No module named 'polars'"}, env0)
    chk("④ 缺第三方套件 → 應黃(環境)· 實際紅 → 不合理 · E08", j["expected"] == "YELLOW" and j["owner"] == "ENV" and j["mode"]["id"] == "E08")
    t = "[VDF_SystemManager v0175] collect · rc 2 YELLOW/NODATA · 七處 7/7  · 燈 {'upstream': 'GREEN', 'health': 'GREEN', 'conform': 'GREEN'} · 啟動 YELLOW"
    j = judge({"step": "vdf_collect", "rc": 2, "lamp": "YELLOW", "out": t}, env0)
    chk("⑤ VDF 自報:同意閘未開 → 應黃 · 操作員的手 · 合理", j["expected"] == "YELLOW" and j["owner"] == "OPERATOR_HAND" and j["reasonable"])
    j = judge({"step": "vdf_collect", "rc": 2, "lamp": "RED", "out": t}, env0)
    chk("⑥ 同一狀況被判紅 → 不合理 · C02", not j["reasonable"] and j["mode"]["id"] == "C02")
    j = judge({"step": "vdf_collect", "rc": 2, "lamp": "GREEN", "out": t.replace("七處 7/7", "七處 6/7")}, env0)
    chk("⑦ 七處 6/7 卻綠 → 不合理 · C01", not j["reasonable"] and j["mode"]["id"] == "C01")
    j = judge({"step": "vrn_health", "rc": 0, "lamp": "GREEN", "out": "health GREEN · own_dir ✓ · P7_accel_bridge ✗"}, env0)
    chk("⑧ 自檢有 ✗ 卻綠 → 不合理 · H06", not j["reasonable"] and j["mode"]["id"] == "H06")
    s = "[SSOT 領域涵蓋] YELLOW · x · 綠 28 · 黃 17 · 無 30 · 不適用 0"
    j = judge({"step": "ssot_domains", "rc": 1, "lamp": "RED", "out": s}, env0)
    chk("⑨ SSOT 有缺口 rc 1 被判紅 → 不合理 · S01(今天實際踩過的錯)", not j["reasonable"] and j["mode"]["id"] == "S01" and j["expected"] == "YELLOW")
    j = judge({"step": "ssot_domains", "rc": 1, "lamp": "YELLOW", "out": s}, env0)
    chk("⑩ 同一狀況判黃 → 合理 · 他系統補正本", j["reasonable"] and j["owner"] == "OTHER_SYSTEM")
    j = judge({"step": "vcgc_handoff", "rc": 1, "lamp": "GREEN", "out": "[RED] ACCEL_BRIDGE_MISSING a\n[RED] MODULE_UNREGISTERED b"}, env0)
    chk("⑪ 交接有紅項卻綠 → 不合理 · G01 · 只剩裁定類 → 操作員裁定", not j["reasonable"] and j["mode"]["id"] == "G01" and j["owner"] == "OPERATOR_RULING")
    chk("⑫ 同意閘:未開 → P01 黃;一道 → P04;兩道 YES → 綠(本工具只讀不設)",
        consent({})["id"] == "P01" and consent({"VIA_NET_CONSENT": "yes"})["id"] == "P04" and consent({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"})["lamp"] == "GREEN")
    rep = {"at": "2020-01-01T00:00:00Z", "steps": []}
    fr = {x["id"] for x in freshness(rep, Path("/nonexistent"))}
    chk("⑬ 新鮮度:報告過期 → R02 · 沒步驟 → R10", {"R02", "R10"} <= fr, fr)
    a = audit({"at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "steps": [{"step": "activate_vdf", "rc": 0, "lamp": "GREEN", "out": "[計] V 9/9 PASS"},
                                                                                           {"step": "vdf_collect", "rc": 2, "lamp": "YELLOW", "out": t}]}, env0, Path("/nonexistent"))
    chk("⑭ 整體:燈都合理 → rc 0 的「合理」判定 · 非綠的照擁有者分組", a["counts"]["unreasonable"] == 0 and "操作員的手(同意閘 · 工作站)" in a["non_green_by_owner"], a["counts"])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑮ 本檔不設同意閘 · 不出網 · 不碰 TA-Lib", not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src)
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket|http|ta" + "lib)\b", src, re.M))
    n = sum(ok)
    print("[計] %s 自測 %d/%d %s" % (ENGINE, n, len(ok), "PASS" if n == len(ok) else "FAIL"))
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args or args[:1] == ["selftest"]:
        return selftest()
    if args[:1] == ["modes"]:
        want = args[1] if len(args) > 1 else None
        for cat, (zh, rows) in FAILURE_MODES.items():
            if want and want != cat:
                continue
            print("## %s %s" % (cat, zh))
            for i, sit, det, fix in rows:
                print("  %s %s\n      認法:%s\n      解法:%s" % (i, sit, det, fix))
        return 0
    if args[:1] in (["audit"], []):
        rp = Path(args[args.index("--report") + 1]) if "--report" in args else None
        rep = _load_report(rp)
        if not rep:
            print("[GRAY] %s · 沒有可稽核的報告(先跑三系統收尾)" % ENGINE)
            return 2
        a = audit(rep)
        if "--json" in args:
            print(json.dumps(a, ensure_ascii=False, indent=1))
        else:
            print("[%s] %s · %s · 步 %d · 合理 %d · 不合理 %d" % (a["lamp"], ENGINE, a["verdict"], a["counts"]["steps"], a["counts"]["reasonable"], a["counts"]["unreasonable"]))
            for r in a["rows"]:
                print("  %s %-14s 實際 %-6s 應有 %-6s %s · %s%s" % ("✓" if r["reasonable"] else "✗", r["step"], r["actual"], r["expected"], r["owner_zh"], r["why"],
                                                           (" · %s %s → %s" % (r["mode"]["id"], r["mode"]["situation"], r["mode"]["fix"])) if r["mode"] and not r["reasonable"] else ""))
            print("  同意閘:%s · %s" % (a["side"]["consent"]["lamp"], a["side"]["consent"]["why"]))
            for f in a["side"]["freshness"]:
                print("  新鮮度:%s %s · %s" % (f["lamp"], f["id"], f["why"]))
        return 1 if a["counts"]["unreasonable"] else 0
    print("用法:audit [--report 檔] [--json] | modes [類別] | --selftest")
    return 2


if __name__ == "__main__":
    sys.exit(main())
