#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL158_VIAPanoramaAuditRepair v0107 — PowerShell 代讀誤報修正(批734;原在 PR #104 的 v0105 上,main 已升 v0106,改號重套)

v0106→v0107:全樹首跑 14 件 PSDUPFN **全是誤報**——here-string(@' … '@)裡內嵌的 JavaScript(fmt/render/done…)、
  產生另一支腳本的模板(EnsureDir/def_Main)、以及不同父函式裡的同名區域函式(Test-Prot)。
  ① 讀 .ps1 前先遮掉 here-string 內容(行數不變);② 同名只在**同一個父作用域**內才算重複;
  ③ 自測 +㉛ 反例(三型都不得報;同父內真重複照報)。其餘判準、scan 帳一字不動。

CGC_MDL158_VIAPanoramaAuditRepair v0106 — 全景稽核修復正主 + AI 代讀(批707:read / slice;批708:digest,省 token 的唯一標準入口)

v0105→v0106(批708 操作員令「善用它來替你執行自測攻並優化他作為節省 TOKEN 的工具 實測自測優化」):
  兩件都是**對 v0105 做對抗式自審**量出來的,不是加功能加爽的。

  ① **那把 token 尺自己就是錯的。** v0105 一律 `字元數 // 4`。ASCII 大致對,
     CJK 在主流 BPE 上約 1 字元 1 token —— 實測 CGC_MDL147_v0103:舊尺 8908,
     CJK 感知尺 13375,**少報 33%**。為什麼一直沒被抓到:`read` 印的是**省下的百分比**,
     而原檔與骨架卡的 CJK 佔比相近,分子分母一起偏低,**比值幾乎不動**(95.0% vs 94.9%)。
     **只檢比值的檢永遠照不出這個缺陷。** 檢 ㉛ 因此釘**絕對值**,並拿舊尺當負控。
     (同一族:批707 LL390「尺自己要先量得準,才有資格去判別人」。)

  ② **read/slice 省的是讀原始碼;我這條迴圈真正的大宗是讀跑測日誌。**
     全格子一跑 108 KB ≈ 三萬 token。而且土法 `grep` **會把人帶錯** ——
     批707 實錄:我 grep 到 1 行 FAIL,總表卻寫 FAIL 0,多花兩次工具呼叫
     才查出那一站是**平行敗→序跑轉綠**。新動詞 `digest`:
       · 只認**行首第一個**中括號(站自己的輸出裡也有同樣標記,那不是站的判決)
       · 同一站以**最後一列**為準;轉綠的**自成一態並照列**(不列=洗紅;列成 FAIL=假紅)
       · 沒有 `[計]` 總表行 = 截斷或還在跑 → **NODATA 不編**
     實測真日誌:30634 token → 371 token,**省 98.8%**,而且把批707 誤導我的那一站直接點名。

  自審留痕:`render_digest` 我第一版寫成 `_tok(0, "x" * chars)` ——
  用一串 ASCII 的 x 去代表一份中文滿天飛的日誌,**等於把剛修好的錯尺再犯一次**;
  已改成帶日誌自己的 CJK 佔比算。三檢各帶負控,36 檢 OK 36。

v0104→v0105(批707 操作員令「全景式讀取…代為讀取節省 AI 讀取的 TOKEN…自動讀取識別錯誤 AST…避免傷害…串成唯一的標準功能」):
  先量(L116):scan 是全樹治理稽核、PEIS(CGC_MDL161)是跨家族能力卡——兩者都不回答「這支檔裡有什麼、錯在哪一行」。
  缺的是 L65「AI 讀卡,不讀原始碼」的**單檔那一層**,所以補在全景正主上,不另立引擎(零九頭龍):
  ① `read <檔或夾…>`:骨架卡——匯入 · 定義樹(行號範圍/簽章/首行說明)· 問題(治理七類僅 VIA 樹內 + 通用 AST 五類
     DUPDEF/UNREACH/BAREEXC/SWALLOW/MUTDEF + PowerShell 兩類 PSDUPFN/PSDOCSTR)· token 帳。給夾=一檔一行全景,真 bug 類排前。
  ② `slice <檔> <名|Class.method>`:只回那一個定義的原始碼(帶行號,裝飾器一起帶)。
  ③ **唯讀**:零寫檔、不執行被讀的檔(只 ast.parse / 文字剖析),自測 ㉗ 用「頂層會寫旗標檔」的樣品釘死。
  ④ 通用五類只報位置、**不進 scan 的帳**(㉚)——scan 數字與歷批已修冊零變動。
  實測(本境):registry 夾 191 檔 ≈130 萬 token → 全景卡 ≈4.5 千(省 99.7%);單檔 1,797 行 → 骨架卡省 95%。

CGC_MDL158_VIAPanoramaAuditRepair v0103 — 全景稽核修復正主(批538:md5 冊管的夾一律零觸碰)

v0102→v0103(批538 VIA 實測打出來的真紅燈):
  批535 的加速器橋全樹掃補,把 `[VIA:ACCEL-BRIDGE]` 插進了 `supportive modules/VIA_Central_Governance/VIA_CentralGovernanceFamily_b514/`
  的四個檔——那是**操作員上傳、MANIFEST_b514.json md5 冊管著的正本**(原名零觸碰律)。md5 一變,CGC_MDL150 ①「五成員 md5 對冊」
  自批535 起就一直紅,而我先前把它歸成「本境空庫」——**那是把自己造的紅燈說成環境問題,和假綠一樣傷**。
  這一版把規則一般化,不再靠人工列夾名:**夾內有帶 md5 的 *MANIFEST*.json = 該夾受 md5 冊管,零觸碰**(連加速器橋都不插),
  而且這類檔連覆蓋率分母都不進——不然 100% 會永遠掉到 99.7%,又生一盞判錯的紅燈(L57 誠實分母)。
  同族的 `supportive modules/ssot/`(批535 已補)、`references/intake/`(本來就在)留著,雙保險。

CGC_MDL158_VIAPanoramaAuditRepair v0102 — 全景稽核修復正主(批537:已修冊複驗 + 摘要講得清楚)

v0101→v0102(操作員令「FIXED CONTENT IN THE AST PAGE AND SUMMARY」):
  ① **已修冊複驗**(新 SSOT `VIA_PanoramaFixed_SSOT_v0100.json`;擁有者本器)。舊頁的 TAB③「已修」在乾跑時是一句
     「本次未套用」——等於這張 AST 頁只講還沒修的、不講修過的。現在 TAB③ 分兩張表:**本次**(套用或乾跑計畫)與
     **歷批已修冊**,而冊上每一筆都拿活樹重量一次:冊說修好、現在也還是修好=GREEN;冊說修好、現在又量到=**RED(回歸)**
     ——尾版律下這最容易發生:有人切了新版卻沒把修帶過去。量不了=ABSENT,誠實講量不了,不當綠。
  ② **摘要講得清楚**。舊摘要只有「問題 129 · 自動修 0」,看不出 129 是什麼、也看不出修過什麼。
     現在主控台一行、頁首、TAB①、Markdown 四處同一句:問題按 L56 三態拆(可同時修/順序修/只報位置待令)、
     已修冊複驗(綠/紅/待驗)、實測綠燈數、真 RED 數,四個數字各有出處。
  ③ 乾跑也要有內容:TAB③「本次」在乾跑時列**修復計畫**(哪一檔、平行還順序、會動哪幾類),不再是一句空話。

CGC_MDL158_VIAPanoramaAuditRepair v0104 — 全景稽核修復正主(批658 正典 TEMPLATE 豁免)

v0103→v0104(批658 · 第四把掃描器補上批647 豁免):
  操作員令「全景式分析 AST,識別錯誤後分前後可修正,可修正者在**不傷害系統、不產生九頭龍風險**前提下修」。
  照令先量:`scan` → 1504 檔 · 135 問題,其中標為「可修」的 `ACCEL 22`。
  **但那 22 件全部在 `VIA_HTML_UI/` 裡面。** 那是批647 收進來的正典 U/I TEMPLATE——byte-exact 正本,
  完整性由它自己的 `manifest.json`(223 筆 sha256)守。往裡面注入 22 個加速器橋,`via-ui --check`
  當場從 223/223 掉成 `內容漂移 22`;而那盞燈是批650 才剛轉綠的。**「照令修完」會直接打掉一盞真綠燈。**
  根因不是這 22 件,是**尺**:批647 的豁免寫進了 CGC_MDL156(_ACCEL_EXEMPT/_TREE_EXEMPT)與
  via_bridge_sweeper(EXEMPT_TEMPLATE),**唯獨這第四把掃描器沒有**。三把有、一把沒有=同一棵樹兩種答案(L30)。
  本版補上,且照 L57/L87 的作法:
  ① `_EXEMPT_TEMPLATE` 具名+**逐條附理由**(不是把尺放寬,是把豁免寫成可讀、可質疑、可改的名冊);
  ② 豁免**不從分母消失**——`scan` 照樣量到、照樣列位置,只是蓋上豁免章(`exempt` 欄),
     `by_class` 仍是誠實總數,另出 `by_class_exempt`;誠實的講法是「量到 22,其中 22 依批647 不得改」,
     不是把它掃進地毯下變成 0;
  ③ 閘擺在**唯一的寫檔出口** `fix_one()`(LL289:閘擺在唯一出口,不是每個呼叫點),`fix()` 的計畫也先濾掉;
  ④ 自測加**反向對照**:把豁免名冊清空,同一份夾具必須改判為「會動到」——證明這道閘真的會咬。
  順手更正:`VERSION` 從 v0101 起就沒跟著檔名走(v0102/v0103 都還寫 v0101),自測計數寫死 20 而實有 21 檢。

CGC_MDL158_VIAPanoramaAuditRepair v0101 — 全景稽核修復正主(批536 判準精準化)

v0100→v0101:① SYSEXE 排除「自己跑自己」(`subprocess.run([sys.executable, Path(__file__)…])`,引擎自測常態)——
  批535 報的 2 件全是這種誤報,真數為 0 ② PINVER 排除自測/夾具區(`def selftest` 之後、chk(/assert 行、X_ENG/Y_ENG 假名、
  /tmp 假路徑)——那些字串不是真的釘死路由 ③ 非活樹再加 `candidates/`、`bundle/`、`launchers/panorama_tests/`
  (候選夾與打包副本不是活樹)④ 判準改動一律附反例自測(⑮)。原 v0100 的修復器與報告不變。

CGC_MDL158_VIAPanoramaAuditRepair v0100 — 全景稽核修復正主(批535 操作員令:
「一個 PowerShell 指令全包:進環境→全景式分析→AST 精準/彈性定位→列出所有問題類型與位置→
  不傷系統、不生九頭龍的前提下,能同時修的同時修、不能同時修的順序修→25 加速器→動態進度條→
  自動跳出多 TAB 矩陣報告(TAB1 給 AI 與我、內附 JSON/MD;TAB2 起逐項測試結果)→紅黃綠燈、分系統分範疇」)

一功能一主(L30):本器是**唯一**的全景稽核+修復入口;它不重寫別人的判斷,只呼叫既有正主:
  · 家族境 python / 子行程環境 = 匯流排 CGC_MDL148(python_for/child_env)
  · 25 加速器名冊 = CGC_MDL156(roster;本器只讀,不自行定義)
  · 中央派送 = CGC_MDL157(dispatch;誠實四態)
  · 自測站清單 = CGC_MDL064 SelftestGrid(尾版;本器只挑站跑,不另立名冊)

九頭龍防線(Zero-Hydra):
  ① 收容件/退役夾/__pycache__/VIA_Reports/vcg/.git 一律不碰(正本零觸碰)
  ② 每次修改前後都 ast.parse,失敗即整檔回滾(原字節留在記憶體)
  ③ 只做「純增量、零行為變更」的自動修(加速器橋、網路工具橋、自測動詞等價轉換)
  ④ 會改行為的(硬相依搬家、釘死版號、裸 sys.executable 派送)只**報位置**,附建議修法,等操作員令
  ⑤ 同檔同時只有一個工人(平行以「檔」為單位切分,互不交疊)

用法:
  python3 CGC_MDL158_VIAPanoramaAuditRepair_v0100.py scan [--json] [--limit N]
  python3 ... fix [--apply] [--classes ACCEL,NET,VERB] [--workers N] [--limit N]
  python3 ... tests [--fast]            # 逐引擎自測 + 中央派送(誠實四態)
  python3 ... report [--open]           # 多 TAB 報告(HTML/JSON/MD)
  python3 ... all [--apply] [--open]    # 掃描→修→測→報(PowerShell 一貼式走這條)
  python3 ... read <檔或夾…> [--json] [--full] [--max-defs N]   # 批707:AI 代讀骨架卡(唯讀)
  python3 ... slice <檔> <定義名|Class.method>                     # 批707:只回一個定義的原始碼
  python3 ... --selftest                # 十二檢(零網路;合成夾具;不碰真樹)
"""
from __future__ import annotations

import argparse
import ast
import concurrent.futures as _cf
import datetime as _dt
import hashlib
import html as _html
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

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

ENGINE_ID = "CGC_MDL158_VIAPanoramaAuditRepair"
VERSION = "v0107"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "panorama_audit"      # 批535:自己的命名空間。`VIA_Reports/panorama` 是 CGC_MDL135/CGC_MDL149
                                                  # L19 安裝核可閘的地盤(schema 不同,我寫進去會讓那道閘整排 BLOCKED=假紅;一名一主 L30)
SKIP_PARTS = ("__pycache__", ".git", "VIA_Reports", "node_modules", ".venv", "site-packages")
SKIP_MARK = ("references/intake/", "references\\intake\\", "VIA_RetiredEngines", "/vcg/", "\\vcg\\", "_self_test", "/tests/", "\\tests\\",
             "supportive modules/ssot/", "supportive modules\\ssot\\")     # 批535:金融機構正典 SSOT 與其 overlay=READ_ONLY 正本,零觸碰(連加速器橋都不插)

#: 批658 正典 TEMPLATE 免修名冊——**每一條都附「為什麼不得改」**,不是「懶得處理」。
#: 與 CGC_MDL156 `_ACCEL_EXEMPT` / `via_bridge_sweeper` `EXEMPT_TEMPLATE` 同一份理由(L30 一個出處)。
#: 名冊只免「修」,不免「量」:掃描照樣報位置,只是蓋豁免章——L57 誠實分母。
_EXEMPT_TEMPLATE = (
    ("VIA_HTML_UI", "批647 正典 U/I TEMPLATE:byte-exact 正本,完整性由它自己的 manifest.json(223 筆 sha256)守;注入任何橋都會打破那份完整性,故正本零觸碰優先於全樹導入令。它的驗收走 `via-ui --check`(CGC_MDL160 template 車道),不走全樹雙橋"),
)


def _load_exempt_roster() -> tuple:
    """批658 L30 一個出處:免修名冊的**正主是 CGC_MDL156**(`_ACCEL_EXEMPT` + `_TREE_EXEMPT`,34 條起跳)。
    本器**讀它的碼、不執行它**(`ast.literal_eval`,零副作用、零 import 連鎖);讀不到就退回內建底線,
    並把「用了哪一把尺」寫進報告(讀不到卻裝作讀到=假綠)。

    為什麼不把 34 條抄過來:抄過來就是第二份,下次只改一邊就又變成「同一棵樹兩種答案」——
    這一批的根因正是那個(三把掃描器有批647 豁免、第四把沒有)。"""
    base = list(_EXEMPT_TEMPLATE)
    seen = {k for k, _ in base}
    cand = sorted(HERE.glob("CGC_MDL156_VIAAcceleratorControl_v*.py"))
    if not cand:
        return tuple(base), "內建底線(CGC_MDL156 不在樹上=ABSENT,不編)"
    try:
        tree = ast.parse(cand[-1].read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        return tuple(base), f"內建底線(讀 {cand[-1].name} 失敗:{type(exc).__name__})"
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id in ("_ACCEL_EXEMPT", "_TREE_EXEMPT") for t in node.targets):
            continue
        try:
            for item in ast.literal_eval(node.value):
                k, w = str(item[0]), str(item[1])
                if k not in seen:
                    seen.add(k)
                    base.append((k, w))
        except Exception:
            continue
    return tuple(base), cand[-1].name


def template_exempt(rel: str) -> str:
    """批658:這條相對路徑在免修名冊上嗎?是→回「為什麼不得改」;否→回空字串。
    **比對法刻意與 CGC_MDL156 第 308/367/410 行逐字同形**(`"/" + rel` 的子字串),
    兩把尺同形才不會出現「這邊免、那邊不免」——那正是這一批要修掉的病(L30)。
    名冊只擋「修」不擋「掃」:掃描照樣報位置(L57 誠實分母)。"""
    r = "/" + str(rel).replace("\\", "/").lstrip("/")
    for name, why in _EXEMPT_ROSTER:
        if name in r:
            return why
    return ""

ACCEL_BLOCK = '''# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
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
'''

NET_BLOCK = '''# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
'''

VERB_BLOCK = '''

# ===== [VIA:VERB-ALIAS:v0100] 批535:全樹以 `--selftest` 呼叫自測(格子站/匯流排/Deck/總控頁契約;律 L53)=====
# 本引擎原只認位置動詞;等價轉換,只增不減,既有呼叫方零影響。
_FLAG_VERBS_B535 = {"--selftest": "selftest", "--status": "status", "--manifest": "manifest", "--routes": "routes"}


def _normalise_argv_b535(argv):
    out, verb = [], None
    for a in argv:
        if a in _FLAG_VERBS_B535 and verb is None:
            verb = _FLAG_VERBS_B535[a]
        else:
            out.append(a)
    return ([verb] + out) if verb else out

'''

# 重相依:module 頂層硬 import 這些 = 本境沒裝就 Traceback(LL51 假紅)
HEAVY_LIBS = {"polars", "talib", "plotly", "yfinance", "akshare", "torch", "paddle", "paddleocr", "easyocr",
              "cv2", "sklearn", "matplotlib", "seaborn", "fitz", "pdfplumber", "docx", "pytesseract",
              "duckdb", "pandas", "numpy", "requests", "httpx", "bs4", "lxml", "openpyxl", "PIL", "psycopg"}
# 這幾支是 VIA 家族境的基底(境內必裝),硬 import 不算問題
BASE_OK = {"pandas", "numpy"}

CATEGORIES = {
    "ACCEL": ("加速器橋缺席", "GREEN_FIX", "純增量;import 時零行為變更"),
    "NET": ("VDF 網路工具橋缺席", "GREEN_FIX", "惰性載入;import 時零網路"),
    "VERB": ("自測動詞契約不齊(只認位置動詞)", "GREEN_FIX", "旗標=位置動詞等價轉換"),
    "HARDIMP": ("模組頂硬相依重庫(缺件會 Traceback=假紅)", "REPORT", "搬進探針式載入 → 缺=ABSENT"),
    "PINVER": ("釘死版號(違尾版律 L54)", "REPORT", "改 newest-glob"),
    "SYSEXE": ("裸 sys.executable 派子行程(違家族境律 L51)", "REPORT", "改匯流排 python_for(family)"),
    "TALIB": ("TA-Lib 活動接線(違 L50)", "REPORT", "QuantGuard 為唯一活動路徑"),
    "SYNTAX": ("語法錯(compile 失敗)", "REPORT", "必修;本器不猜改"),
}
SYSTEMS = (("VDF", "functional modules/VDF"), ("VRN", "functional modules/VRN"), ("VAP", "functional modules/VAP"),
           ("TALib", "functional modules/TALib"), ("治理 CGC", "supportive modules/registry"),
           ("支援 SUP", "supportive modules"), ("其他", ""))


def _p(pct: float, msg: str) -> None:
    """動態進度條協定:PowerShell 端解析 @@PROGRESS|<pct>|<msg> → Write-Progress。"""
    print(f"@@PROGRESS|{max(0.0, min(100.0, pct)):.1f}|{msg}", flush=True)


_MD5_CANON: set | None = None


def md5_canon_dirs(root: Path | None = None) -> set:
    """批538:夾內有帶 md5 的 *MANIFEST*.json → 該夾(含子夾)受 md5 冊管,零觸碰。
    這是**規則**,不是夾名清單:以後操作員再上傳一套帶 md5 冊的正本,不必改這支就自動受保護。"""
    global _MD5_CANON
    if _MD5_CANON is not None:
        return _MD5_CANON
    out = set()
    for mf in (root or VIA).rglob("*MANIFEST*.json"):
        if ".git" in mf.parts:
            continue
        try:
            if "md5" in mf.read_text(encoding="utf-8", errors="replace").lower():
                out.add(str(mf.parent))
        except Exception:
            continue
    _MD5_CANON = out
    return out


def _skip(p: Path) -> bool:
    s = str(p)
    if any(x in p.parts for x in SKIP_PARTS):
        return True
    if any(m in s for m in SKIP_MARK):
        return True
    return any(s.startswith(d + os.sep) or s == d for d in md5_canon_dirs())   # 批538:md5 冊管的夾零觸碰


def system_of(rel: str) -> str:
    for name, pref in SYSTEMS:
        if pref and rel.replace("\\", "/").startswith(pref):
            return name
    return "其他"


_VER_RX = re.compile(r"^(?P<stem>.+?)_v(?P<ver>\d{3,4})$")
_FROZEN_RX = re.compile(r"(_sha[0-9a-f]{6,}|\(\d+\)|[ _-]copy|備份|backup)", re.I)
_NONLIVE_DIR = ("/candidates/", "\\candidates\\", "/bundle/", "\\bundle\\", "launchers/panorama_tests", "launchers\\panorama_tests")
_NONLIVE_PART = ("_output", "_superseded")            # 批538:建置產出夾 / 讓位夾不是活樹
_NONLIVE_DATED = re.compile(r"^\d{8}$")                 # 批538:日期傾印夾 functional modules/VRN/20260804/
_NONLIVE_STAMP = re.compile(r"_\d{8}_\d{6}$")           # 批538:時戳產出夾 VAP_WAREHOUSE_V6_ALL_20260507_100922/


def _nonlive_part(p: Path) -> bool:
    """批538(與清掃器 v0101 共用同一判準;L30 一功能一主):
    _output/ 建置產出、_superseded/ 讓位件、日期夾 20260804/、時戳夾 *_20260507_100922/ 都不是活樹。
    這 56 件正是兩個中央稽核器對不上的來源——CGC_MDL158 說 100%、清掃器說還差 6 件網路橋。"""
    return any(x in _NONLIVE_PART or _NONLIVE_DATED.match(x) or _NONLIVE_STAMP.search(x) for x in p.parts)


def py_files(root: Path | None = None, live_only: bool = True) -> list[Path]:
    """全樹 .py(排除收容件/退役夾/pycache)。live_only=True 再過**活樹**:
    ① 同 stem 多版只留尾版(尾版律:舊版不是活樹,對它報紅=假紅)
    ② 凍結副本(_sha…、(1)、copy、備份)不算活樹。"""
    root = root or VIA
    files = sorted(p for p in root.rglob("*.py") if not _skip(p))
    if not live_only:
        return files
    newest: dict[tuple[str, str], tuple[int, Path]] = {}
    plain: list[Path] = []
    for f in files:
        if _FROZEN_RX.search(f.name) or any(k in str(f) for k in _NONLIVE_DIR) or _nonlive_part(f):   # 批536/538:候選夾·打包副本·夾具測試·建置產出·讓位夾·日期/時戳傾印夾 都不是活樹
            continue
        m = _VER_RX.match(f.stem)
        if m:
            key = (str(f.parent), m.group("stem"))
            v = int(m.group("ver"))
            if key not in newest or v > newest[key][0]:
                newest[key] = (v, f)
        else:
            plain.append(f)
    return sorted(plain + [v[1] for v in newest.values()])


_EXEMPT_ROSTER, _EXEMPT_SRC = _load_exempt_roster()


# ---------------------------------------------------------------- AST 稽核
def audit_source(path: Path, src: str, rel: str) -> list[dict]:
    """批658:稽核的**唯一出口**——在這裡蓋豁免章,免得每個呼叫點各蓋各的(LL289)。
    豁免件照樣回問題(位置要看得見),只是每筆多一個 `exempt` 欄寫明不得改的理由。"""
    issues = _audit_source_raw(path, src, rel)
    why = template_exempt(rel)
    if why:
        for it in issues:
            it["exempt"] = why
    return issues


def _audit_source_raw(path: Path, src: str, rel: str) -> list[dict]:
    """單檔稽核:AST 精準定位(行號);AST 壞則退回彈性(正則)定位,兩者都記法。"""
    issues: list[dict] = []
    is_vdf_engine = rel.replace("\\", "/").startswith("functional modules/VDF/engine") and path.name.endswith(".py")

    if "[VIA:ACCEL-BRIDGE" not in src:
        issues.append({"cls": "ACCEL", "line": 1, "how": "marker", "detail": "無 [VIA:ACCEL-BRIDGE] 區塊"})
    if is_vdf_engine and "[VIA:NET-BRIDGE" not in src:
        issues.append({"cls": "NET", "line": 1, "how": "marker", "detail": "VDF 引擎無 [VIA:NET-BRIDGE] 區塊"})

    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as exc:
        issues.append({"cls": "SYNTAX", "line": int(exc.lineno or 1), "how": "compile",
                       "detail": f"{type(exc).__name__}: {str(exc)[:120]}"})
        return issues

    # 模組頂層(不在 try 內)硬 import 重庫
    for node in tree.body:
        names = []
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split(".")[0]]
        for n in names:
            if n in HEAVY_LIBS and n not in BASE_OK:
                issues.append({"cls": "HARDIMP", "line": node.lineno, "how": "ast",
                               "detail": f"模組頂層 import {n}(不在 try/探針內)"})

    src_lines = src.splitlines()
    doc_lines = set()
    for nd in ast.walk(tree):
        if isinstance(nd, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(nd, "body", None)
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) and isinstance(b[0].value.value, str):
                doc_lines.update(range(b[0].lineno, (b[0].end_lineno or b[0].lineno) + 1))
    selftest_line = next((nd.lineno for nd in tree.body if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef))
                          and nd.name in ("selftest", "self_test", "_selftest")), 10 ** 9)
    fixture_span = set()                       # 批536:自測/探針函式整段都是夾具(在暫存夾寫假冊、假引擎名)
    for nd in ast.walk(tree):
        if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                nd.name.startswith(("selftest", "self_test", "_selftest", "_probe", "probe_", "test_", "_test"))
                or "selftest" in nd.name or nd.name.endswith("_fixture")):
            fixture_span.update(range(nd.lineno, (nd.end_lineno or nd.lineno) + 1))
    # 批658(L93 先疑尺不疑樹):尾版 glob **常常寫成跨行**——
    #     `cand = sorted((D).glob("X_v*.py")) or [D / "X_v0100.py"]`
    #   那個 `_v0100` 是 glob 落空時的**後備預設**,不是釘死版號;舊尺只看「同一行有沒有 glob」,
    #   跨行就看不到,於是報一盞判錯的紅燈(量到的 24 件裡有 4 件是這種)。
    #   改看**同一個簡單陳述式**(Assign/Expr/Return…)裡有沒有 glob/newest;
    #   刻意不含 def/if/for 這種複合陳述式——否則一個函式裡任何一處 glob 會讓整支函式免驗(尺放太寬)。
    #   算它要 ast.dump 每個簡單陳述式,全樹 1504 檔會多花 ~7s;所以**只在真有候選時才算一次**
    #   (絕大多數檔根本沒有 `_vNNNN` 字串,不該替它們付這個錢)。
    _glob_cache: list = []

    def glob_stmt_lines() -> set:
        if not _glob_cache:
            got: set = set()
            for nd in ast.walk(tree):
                if isinstance(nd, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr, ast.Return)):
                    seg = ast.dump(nd)
                    if ("attr='glob'" in seg or "attr='rglob'" in seg
                            or "id='newest'" in seg or "attr='newest'" in seg or "id='iglob'" in seg):
                        got.update(range(nd.lineno, (nd.end_lineno or nd.lineno) + 1))
            _glob_cache.append(got)
        return _glob_cache[0]
    has_selftest_choice = False
    for node in ast.walk(tree):
        # 釘死版號字串
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            if (re.search(r"_v\d{4}\.(py|ps1)$", v) or re.search(r"-v\d{4}\.ps1$", v)) and node.lineno not in doc_lines:
                ln = src_lines[node.lineno - 1] if node.lineno <= len(src_lines) else ""
                # 只有「真的拿去開檔/執行/組路徑」才算違尾版律;報告文字、註解、說明字串不算(避免假紅)
                path_use = any(k in ln for k in ("Path(", "open(", "os.path.join", "joinpath", "/ \"", "subprocess", "run(", "_eng(", "newest(", "import_module"))
                var_use = bool(re.match(r"\s*[A-Z_]*(PATH|FILE|BOOK|SCRIPT|ENGINE|TARGET|ENTRY)[A-Z_]*\s*=", ln))
                fixture = (node.lineno >= selftest_line or node.lineno in fixture_span                               # 批536:自測段之後=夾具,不是正式路由
                           or any(k in ln for k in ("chk(", "assert ", "_td", "tmp", "TemporaryDirectory"))
                           or re.search(r"\b[XYZ]_(ENG|MDL)\d+", v) is not None)
                if (path_use or var_use) and "glob" not in ln and not fixture and node.lineno not in glob_stmt_lines():
                    issues.append({"cls": "PINVER", "line": node.lineno, "how": "ast",
                                   "detail": f"字串釘死版號當路徑用:{v[:64]}"})
            if v == "selftest":
                has_selftest_choice = True
        # 裸 sys.executable 派子行程
        if isinstance(node, ast.Call):
            fn = node.func
            is_sub = (isinstance(fn, ast.Attribute) and fn.attr in ("run", "Popen", "check_output")
                      and isinstance(fn.value, ast.Name) and fn.value.id == "subprocess")
            if is_sub and node.args:
                seg = ast.dump(node.args[0])
                if "attr='executable'" in seg and "id='sys'" in seg:
                    # 只有「派到別支引擎/別家族」才違家族境律;自跑自己(同境)不算
                    self_run = "id='__file__'" in seg or "'__file__'" in seg          # 批536:自己跑自己(自測常態)不是跨家族派送
                    cross = (not self_run) and any(k in seg for k in ("functional modules", "_eng", "newest", "ENGINE", "engine"))
                    if cross:
                        issues.append({"cls": "SYSEXE", "line": node.lineno, "how": "ast",
                                       "detail": "subprocess 以 sys.executable 派**別支引擎**(應走匯流排家族境 python)"})
        # TA-Lib 活動接線
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            nm = ""
            if isinstance(node, ast.Import):
                nm = ",".join(a.name for a in node.names)
            elif node.module:
                nm = node.module
            if re.search(r"\btalib\b", nm):
                issues.append({"cls": "TALIB", "line": node.lineno, "how": "ast",
                               "detail": f"import {nm}(L50 禁用;QuantGuard 為唯一活動路徑)"})

    # 動詞契約:有 selftest 位置動詞但無旗標等價
    if has_selftest_choice and "argparse" in src and "--selftest" not in src:
        ln = next((i + 1 for i, l in enumerate(src_lines) if "selftest" in l), 1)
        issues.append({"cls": "VERB", "line": ln, "how": "ast+flex",
                       "detail": "argparse 有 selftest 位置動詞,但不吃 --selftest(全樹契約 L53)"})
    return issues


def scan(limit: int = 0, progress: bool = True) -> dict:
    files = py_files()
    if limit:
        files = files[:limit]
    rows: list[dict] = []
    t0 = time.time()
    n = len(files)
    for i, f in enumerate(files):
        if progress and (i % 60 == 0 or i == n - 1):
            _p(5 + 25.0 * i / max(1, n), f"AST 全景掃描 {i+1}/{n} · {f.name[:38]}")
        try:
            src = f.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            rows.append({"file": str(f.relative_to(VIA)), "cls": "SYNTAX", "line": 1, "how": "io",
                         "detail": f"讀不了 {type(exc).__name__}", "system": system_of(str(f.relative_to(VIA)))})
            continue
        rel = str(f.relative_to(VIA))
        for it in audit_source(f, src, rel):
            it.update({"file": rel, "system": system_of(rel)})
            rows.append(it)
    by_cls: dict[str, int] = {}
    by_ex: dict[str, int] = {}                       # 批658:其中依名冊不得改的(不從分母扣,只另計)
    by_sys: dict[str, dict[str, int]] = {}
    for r in rows:
        by_cls[r["cls"]] = by_cls.get(r["cls"], 0) + 1
        if r.get("exempt"):
            by_ex[r["cls"]] = by_ex.get(r["cls"], 0) + 1
        by_sys.setdefault(r["system"], {})
        by_sys[r["system"]][r["cls"]] = by_sys[r["system"]].get(r["cls"], 0) + 1
    allf = py_files(live_only=False)
    return {"schema": "VIA.CGC158.scan.v1", "ts": _dt.datetime.now().isoformat(timespec="seconds"),
            "files_scanned": len(files), "files_all": len(allf), "files_nonlive": len(allf) - len(files),
            "scope": "活樹(尾版律:同 stem 只算尾版;凍結副本 _sha/(1)/copy 不算)",
            "issues": len(rows), "by_class": by_cls, "by_class_exempt": by_ex,
            "exempt_names": [x[0] for x in _EXEMPT_TEMPLATE],
            "exempt_roster": len(_EXEMPT_ROSTER), "exempt_source": _EXEMPT_SRC, "by_system": by_sys,
            "rows": rows, "secs": round(time.time() - t0, 1)}


# ---------------------------------------------------------------- 修復
def _insert_after_header(src: str, block: str) -> str:
    """插在 docstring / __future__ / shebang 之後、其餘 import 之前(AST 求位)。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return ""
    line = 0
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            line = max(line, node.end_lineno or 0)
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            line = max(line, node.end_lineno or 0)
            continue
        break
    lines = src.splitlines(keepends=True)
    if line == 0:
        i = 0
        while i < len(lines) and (lines[i].startswith("#!") or lines[i].startswith("# -*-") or lines[i].startswith("# coding")):
            i += 1
        line = i
    return "".join(lines[:line]) + "\n" + block + "\n" + "".join(lines[line:])


def fix_one(rel: str, classes: set[str], apply: bool) -> dict:
    """單檔修復(平行工人;一檔一工人,互不交疊)。回 {file, applied[], skipped[], ok, why}"""
    path = VIA / rel
    res = {"file": rel, "applied": [], "skipped": [], "ok": True, "why": ""}
    why_ex = template_exempt(rel)          # 批658:唯一寫檔出口的硬閘——名冊上的正本,連讀都不必讀
    if why_ex:
        res.update(skipped=sorted(classes), why=f"豁免不修:{why_ex}", exempt=why_ex)
        return res
    try:
        original = path.read_text(encoding="utf-8")
    except Exception as exc:
        res.update(ok=False, why=f"讀不了 {type(exc).__name__}")
        return res
    src = original
    try:
        ast.parse(src)
    except SyntaxError as exc:
        res.update(ok=False, why=f"原檔語法錯,不動(行 {exc.lineno})")
        return res

    if "ACCEL" in classes and "[VIA:ACCEL-BRIDGE" not in src:
        cand = _insert_after_header(src, ACCEL_BLOCK)
        if cand:
            src = cand
            res["applied"].append("ACCEL")
        else:
            res["skipped"].append("ACCEL:求位失敗")
    if "NET" in classes and "[VIA:NET-BRIDGE" not in src and rel.replace("\\", "/").startswith("functional modules/VDF/engine"):
        cand = _insert_after_header(src, NET_BLOCK)
        if cand:
            src = cand
            res["applied"].append("NET")
        else:
            res["skipped"].append("NET:求位失敗")
    if "VERB" in classes:
        # 批658:L92「哨兵抓到就要給得出下一步」——舊版只認一種 parse_args 形狀,對不上就**無聲不修**
        #   (v0103 乾跑 applied_by_class 只有 ACCEL,VERB 8 件掃得到卻一件也沒進計畫,連理由都沒有)。
        #   本版:① 加第二種形狀 `X.parse_args(argv)`(main(argv=None) 的寫法,全樹最常見)
        #        ② 每一條不修的路徑都留下**講得出來的**理由,不再靜悄悄。
        if "--selftest" in src:
            res["skipped"].append("VERB:檔內已出現 --selftest(可能已修或另有旗標;不重複插塊)")
        elif "argparse" not in src or '"selftest"' not in src:
            res["skipped"].append("VERB:非 argparse 或無 selftest 動詞(不猜改)")
        else:
            m = re.search(r"\ndef main\(.*?\)\s*(->\s*[\w\[\], |]+)?:", src)
            pa = [x for x in ("    args = parser.parse_args()", "    return parser.parse_args()") if src.count(x) == 1]
            # 形狀 B:`main(argv=None)` + 一次 `….parse_args(argv)`(VIA_WorkflowEngine / twrevenue / superextract 都是這型)
            mb = re.search(r"\n(?P<line>    (?:\w+\s*=\s*|return )?[A-Za-z_][\w.]*(?:\(\))?\.parse_args\(argv\))\n", src)
            has_argv_main = bool(re.search(r"\ndef main\(\s*argv", src))
            if m and pa:
                src = src[:m.start()] + VERB_BLOCK + src[m.start():]
                src = src.replace(pa[0], pa[0].replace("parse_args()", "parse_args(_normalise_argv_b535(sys.argv[1:]))"), 1)
                if "\nimport sys" not in src:
                    src = src.replace("\nimport argparse", "\nimport argparse\nimport sys", 1)
                res["applied"].append("VERB")
            elif m and mb and has_argv_main and src.count(".parse_args(argv)") == 1:
                line = mb.group("line")
                src = src[:m.start()] + VERB_BLOCK + src[m.start():]
                src = src.replace(line, line.replace(
                    ".parse_args(argv)",
                    ".parse_args(_normalise_argv_b535(argv if argv is not None else sys.argv[1:]))"), 1)
                if "\nimport sys" not in src:
                    src = src.replace("\nimport argparse", "\nimport argparse\nimport sys", 1)
                res["applied"].append("VERB")
            elif not m:
                res["skipped"].append("VERB:找不到模組層 def main(…)(不猜改)")
            elif src.count(".parse_args(argv)") > 1:
                res["skipped"].append(f"VERB:parse_args(argv) 出現 {src.count('.parse_args(argv)')} 次,改哪一處要操作員裁定(不猜改)")
            else:
                res["skipped"].append("VERB:parse_args 形狀不在已知兩型(`parser.parse_args()` / `X.parse_args(argv)`)——"
                                      "請把這一型帶回 CGC_MDL158 加形狀,不在這裡猜改")

    if not res["applied"]:
        return res
    try:
        ast.parse(src)
    except SyntaxError as exc:
        res.update(ok=False, why=f"改後語法錯 → 回滾(行 {exc.lineno})", applied=[])
        return res
    if apply:
        path.write_text(src, encoding="utf-8")
    res["bytes_delta"] = len(src) - len(original)
    return res


def accel_workers(default: int = 8) -> tuple[int, str]:
    """並行度取自 CGC156 的 25 項加速器名冊(只讀,不自行定義;缺席=預設)。"""
    try:
        j = OUT.parent / "accelerator" / "VIA_ACCELERATOR_CONTROL_latest.json"
        if j.is_file():
            d = json.loads(j.read_text(encoding="utf-8"))
            n = int(d.get("roster_count") or d.get("accelerators") or 0)
            if n > 0:
                return max(4, min(n, 25)), f"CGC156 名冊 {n} 項"
    except Exception:
        pass
    return default, "預設(CGC156 報告未見)"


def fix(classes: set[str], apply: bool, workers: int = 0, limit: int = 0, scan_rows: list | None = None) -> dict:
    rows = scan_rows if scan_rows is not None else scan(progress=False)["rows"]
    targets: dict[str, set[str]] = {}
    exempt: dict[str, str] = {}                      # 批658:名冊件連計畫都不進,免得「乾跑說要修 22 件」誤導
    for r in rows:
        if r["cls"] in classes:
            why_ex = r.get("exempt") or template_exempt(r["file"])
            if why_ex:
                exempt[r["file"]] = why_ex
                continue
            targets.setdefault(r["file"], set()).add(r["cls"])
    files = sorted(targets)
    if limit:
        files = files[:limit]
    w, wsrc = accel_workers()
    if workers:
        w = workers
    par_files = [f for f in files if targets[f] <= {"ACCEL", "NET"}]          # 純增量=可同時修
    seq_files = [f for f in files if f not in set(par_files)]                  # 碰 main/parse_args=順序修
    out: list[dict] = []
    t0 = time.time()
    n = max(1, len(files))
    done = 0
    if par_files:
        with _cf.ThreadPoolExecutor(max_workers=w) as ex:
            futs = {ex.submit(fix_one, f, targets[f], apply): f for f in par_files}
            for fu in _cf.as_completed(futs):
                out.append(fu.result())
                done += 1
                if done % 15 == 0 or done == len(par_files):
                    _p(32 + 28.0 * done / n, f"平行修復 {done}/{len(par_files)}(工人 {w};{wsrc})")
    for f in seq_files:
        out.append(fix_one(f, targets[f], apply))
        done += 1
        _p(32 + 28.0 * done / n, f"順序修復 {done - len(par_files)}/{len(seq_files)} · {Path(f).name[:34]}")
    applied = {}
    for r in out:
        for c in r["applied"]:
            applied[c] = applied.get(c, 0) + 1
    return {"schema": "VIA.CGC158.fix.v1", "apply": apply, "workers": w, "worker_source": wsrc,
            "parallel_files": len(par_files), "sequential_files": len(seq_files),
            "exempt_files": len(exempt), "exempt_rows": sorted(exempt.items()),
            "applied_by_class": applied, "failed": [r for r in out if not r["ok"]],
            "rows": out, "secs": round(time.time() - t0, 1)}


# ---------------------------------------------------------------- 測試
def _bus_python(family: str) -> str:
    try:
        import importlib.util
        c = sorted(HERE.glob("CGC_MDL148_EngineBus_v*.py"))
        if c:
            spec = importlib.util.spec_from_file_location("bus_for_158", c[-1])
            m = importlib.util.module_from_spec(spec)
            sys.modules["bus_for_158"] = m
            spec.loader.exec_module(m)
            got = m.python_for(family) or {}
            if got.get("python") and Path(got["python"]).exists():
                return got["python"]
    except Exception:
        pass
    return sys.executable


TEST_TARGETS = [
    ("治理", "CGC_MDL157 唯一接觸口", "supportive modules/registry", "CGC_MDL157_VIAUniqueEntryControl_v*.py", "core"),
    ("治理", "CGC_MDL156 加速器控制面", "supportive modules/registry", "CGC_MDL156_VIAAcceleratorControl_v*.py", "core"),
    ("治理", "CGC_MDL155 統一 SSOT", "supportive modules/registry", "CGC_MDL155_VIAUnifiedSSOTAutoCode_v*.py", "core"),
    ("治理", "CGC_MDL148 引擎匯流排", "supportive modules/registry", "CGC_MDL148_EngineBus_v*.py", "core"),
    ("治理", "CGC_MDL153 工作流重組台", "supportive modules/registry", "CGC_MDL153_WorkflowComposer_v*.py", "core"),
    ("治理", "CGC_MDL149 中央控管台", "supportive modules/registry", "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py", "vrn"),
    ("治理", "CGC_MDL095 指揮台橋", "supportive modules/registry", "CGC_MDL095_DeckServer_v*.py", "core"),
    ("VDF", "VDF_ENG073 資料架構", "functional modules/VDF/engine", "VDF_ENG073_DataArchitecture_v*.py", "vdf"),
    ("VDF", "VDF_ENG087 市場清單治理", "functional modules/VDF/engine", "VDF_ENG087_MarketListGovernance_v*.py", "vdf"),
    ("VDF", "VDF_ENG086 QuantGuard 正主橋", "functional modules/VDF/engine", "VDF_ENG086_QuantGuardOneBridge_v*.py", "vdf"),
    ("VDF", "VDF_ENG085 VATETF 正主橋", "functional modules/VDF/engine", "VDF_ENG085_VatetfBridge_v*.py", "vdf"),
    ("VDF", "VDF_ENG055 總擷取執行器", "functional modules/VDF/engine", "VDF_ENG055_OmniFetch_v*.py", "vdf"),
    ("VRN", "VRN_ENG087 NLP 文字摘要橋", "functional modules/VRN", "VRN_ENG087_NLPTextSummaryBridge_v*.py", "vrn"),
    ("VRN", "VRN_ENG086 第一頁邏輯補缺", "functional modules/VRN", "VRN_ENG086_FirstPageLogicBridge_v*.py", "vrn"),
    ("VRN", "VRN_ENG073 報告結構庫", "functional modules/VRN", "VRN_ENG073_ReportStructuredDB_v*.py", "vrn"),
    ("VRN", "VRN_ENG074 財報頁擷取", "functional modules/VRN", "VRN_ENG074_FinancialPages_v*.py", "vrn"),
    ("支援", "SUP_MDL866 統一 NLP 編排", "supportive modules/70_VRN_Rules", "SUP_MDL866_VIAUnifiedNLPOrchestrator_v*.py", "vrn"),
]
_ABSENT_MARK = ("ModuleNotFoundError", "[ABSENT]", "· ABSENT ·", "No module named")
_NODATA_MARK = ("[NODATA]", "[NEED_INPUT]", "NODATA")


def judge(rc: int | None, out: str) -> tuple[str, str]:
    """誠實四態(與 CGC157 同律 L52):缺件 ABSENT · 缺料 NODATA · 逾時 TIMEOUT · 真壞才 RED。"""
    if rc is None:
        return "TIMEOUT", "逾時"
    if rc == 0:
        return "GREEN", (next((l for l in reversed(out.splitlines()) if "計]" in l or "OK" in l), "rc0")[:110])
    tail = out[-2500:]
    if rc == 3 or any(k in tail for k in _ABSENT_MARK):
        return "ABSENT", next((l.strip() for l in reversed(tail.splitlines()) if any(k in l for k in _ABSENT_MARK)), "本境缺件")[:130]
    if rc == 2 or any(k in tail for k in _NODATA_MARK):
        return "NODATA", next((l.strip() for l in reversed(tail.splitlines()) if any(k in l for k in _NODATA_MARK)), "資料側")[:130]
    return "RED", (tail.splitlines()[-1].strip()[:130] if tail.strip() else f"rc={rc}")


def run_tests(fast: bool = False, timeout: int = 900) -> dict:
    rows = []
    n = len(TEST_TARGETS)
    for i, (sysname, label, folder, glob, fam) in enumerate(TEST_TARGETS):
        _p(62 + 26.0 * i / n, f"實測 {i+1}/{n} · {label}")
        hits = sorted((VIA / folder).glob(glob))
        if not hits:
            rows.append({"system": sysname, "name": label, "state": "ABSENT", "why": f"檔缺 {glob}", "rc": None, "secs": 0, "engine": ""})
            continue
        eng = hits[-1]
        py = _bus_python(fam)
        t0 = time.time()
        try:
            r = subprocess.run([py, str(eng), "--selftest"], capture_output=True, text=True,
                               timeout=(300 if fast else timeout), cwd=str(VIA), errors="replace")
            rc, out = r.returncode, (r.stdout or "") + "\n" + (r.stderr or "")
        except subprocess.TimeoutExpired:
            rc, out = None, "TIMEOUT"
        except Exception as exc:
            rc, out = 1, f"{type(exc).__name__}: {exc}"
        st, why = judge(rc, out)
        rows.append({"system": sysname, "name": label, "engine": eng.name, "state": st, "why": why,
                     "rc": rc, "secs": round(time.time() - t0, 1)})
    # 中央派送(CGC157)
    disp = {"state": "ABSENT", "why": "CGC157 缺"}
    c = sorted(HERE.glob("CGC_MDL157_VIAUniqueEntryControl_v*.py"))
    if c:
        _p(89, "中央派送 dispatch --family all")
        try:
            r = subprocess.run([sys.executable, str(c[-1]), "dispatch", "--family", "all"],
                               capture_output=True, text=True, timeout=timeout, cwd=str(VIA), errors="replace")
            j = None
            s = r.stdout or ""
            if "{" in s:
                try:
                    j = json.loads(s[s.index("{"):s.rindex("}") + 1])
                except Exception:
                    j = None
            disp = {"state": (j or {}).get("verdict") or judge(r.returncode, s)[0],
                    "counts": (j or {}).get("counts"), "routes": [
                        {"family": x.get("family"), "engine": x.get("engine"), "state": x.get("state"),
                         "rc": x.get("returncode"), "python_source": x.get("python_source")} for x in (j or {}).get("routes", [])],
                    "why": "" if j else (s[-160:] if s else "無 JSON")}
        except Exception as exc:
            disp = {"state": "RED", "why": f"{type(exc).__name__}: {exc}"}
    tally = {}
    for r in rows:
        tally[r["state"]] = tally.get(r["state"], 0) + 1
    return {"schema": "VIA.CGC158.tests.v1", "rows": rows, "tally": tally, "dispatch": disp,
            "verdict": "RED" if (tally.get("RED") or tally.get("TIMEOUT")) else ("YELLOW" if (tally.get("ABSENT") or tally.get("NODATA")) else "GREEN")}


# ---------------------------------------------------------------- 報告(多 TAB · 零 CDN)
def coverage() -> dict:
    """批658:**免修名冊上的檔不進覆蓋率分母**——與 CGC_MDL156 第 367 行同一判準(L30)。
    不扣的話,批647 那 22 件依律不得插橋的正典件會把 accel_pct 永遠壓在 98.5%,
    於是冊上 `accel_pct ≥ 100%` 那條變成一盞**怎麼修都修不掉的紅燈**(判錯的紅燈和假綠一樣傷)。
    扣了多少一樣要講出來:`accel_exempt` 與未扣的 `accel_pct_raw` 都留在報告裡(L57 誠實分母)。"""
    allf = py_files()
    files = [f for f in allf if not template_exempt(str(f.relative_to(VIA)))]
    n_ex = len(allf) - len(files)
    acc = sum(1 for f in files if "[VIA:ACCEL-BRIDGE" in f.read_text(encoding="utf-8", errors="replace"))
    acc_all = sum(1 for f in allf if "[VIA:ACCEL-BRIDGE" in f.read_text(encoding="utf-8", errors="replace"))
    vdfe = [f for f in files if str(f.relative_to(VIA)).replace("\\", "/").startswith("functional modules/VDF/engine")]
    net = sum(1 for f in vdfe if "[VIA:NET-BRIDGE" in f.read_text(encoding="utf-8", errors="replace"))
    return {"py_total": len(files), "py_all": len(allf), "accel_exempt": n_ex,
            "accel": acc, "accel_pct": round(100.0 * acc / max(1, len(files)), 1),
            "accel_pct_raw": round(100.0 * acc_all / max(1, len(allf)), 1),
            "exempt_source": _EXEMPT_SRC,
            "vdf_engines": len(vdfe), "net": net, "net_pct": round(100.0 * net / max(1, len(vdfe)), 1)}


FIXED_SSOT = VIA / "supportive modules" / "registry" / "VIA_PanoramaFixed_SSOT_v0100.json"
PAR_CLS = {"ACCEL", "NET"}                 # L56 ①:純增量、零行為變更、可冪等 → 以檔為單位平行修


def _tail_file(rel_dir: str, glob: str):
    base = VIA if rel_dir in (".", "") else VIA / rel_dir
    hits = sorted(p for p in base.glob(glob) if p.is_file())
    return hits[-1] if hits else None


def _verify_one(v: dict, scan_d: dict, cov: dict) -> tuple:
    """一條憑據 → (燈, 說明)。量不出來就說量不出來(ABSENT),不當綠。"""
    k = v.get("kind")
    if k == "class_zero":
        # 批658:冊上這條的意思是「**沒有還該修而沒修的**」,不是「掃描總數是 0」。
        #   批647 之後樹上多了 22 件正典 TEMPLATE 的 ACCEL——它們依名冊不得改,
        #   拿總數去判就讓 F535-ACCEL 從那天起一直亮著一盞**永遠修不掉的紅燈**(判錯的紅燈和假綠一樣傷)。
        #   所以扣掉名冊件;而且扣了多少要當場講出來,不是默默扣掉(L57)。
        cls = v.get("cls")
        n = int((scan_d.get("by_class") or {}).get(cls, 0))
        ex = min(int((scan_d.get("by_class_exempt") or {}).get(cls, 0)), n)
        left = n - ex
        tail = f"(冊要求 0;另有 {ex} 件依免修名冊不得改,不計入)" if ex else "(冊要求 0)"
        return ("GREEN" if left == 0 else "RED"), f"活樹 {cls} 可修 {left}{tail}"
    if k == "coverage_pct":
        fld = v.get("field")
        if fld not in cov:
            return "ABSENT", f"覆蓋率無 {fld} 欄,量不了"
        got, exp = float(cov[fld]), float(v.get("expect", 100.0))
        return ("GREEN" if got >= exp else "RED"), f"{fld} {got}%(冊要求 ≥{exp}%)"
    if k == "tail_contains":
        p = _tail_file(v.get("dir", "."), v.get("glob", ""))
        if p is None:
            return "ABSENT", f"尾版不在:{v.get('dir')}/{v.get('glob')}"
        txt = p.read_text(encoding="utf-8", errors="replace")
        miss = [m for m in (v.get("markers") or []) if m not in txt]
        back = [m for m in (v.get("markers_absent") or []) if m in txt]
        if miss:
            return "RED", f"{p.name} 少了 {miss}(修沒帶進尾版=回歸)"
        if back:
            return "RED", f"{p.name} 又出現 {back}(退役件復活=回歸)"
        return "GREEN", f"{p.name} 憑據齊"
    return "ABSENT", f"不認得的憑據類 {k}"


def fixed_ledger(scan_d: dict, cov: dict) -> dict:
    """已修冊複驗。冊不在=誠實 ABSENT,不編。"""
    rep = {"schema": "VIA.CGC158.fixed.v1", "src": str(FIXED_SSOT), "state": "ABSENT",
           "rows": [], "tally": {}, "regressions": []}
    if not FIXED_SSOT.is_file():
        rep["why"] = f"已修冊不在:{FIXED_SSOT.name}"
        return rep
    try:
        d = json.loads(FIXED_SSOT.read_text(encoding="utf-8"))
    except Exception as exc:
        rep.update(state="RED", why=f"已修冊讀不動:{type(exc).__name__}")
        return rep
    for e in d.get("entries") or []:
        checks = [dict(zip(("lamp", "why"), _verify_one(v, scan_d, cov))) for v in (e.get("verify") or [])]
        lamps = [c["lamp"] for c in checks]
        lamp = "RED" if "RED" in lamps else ("ABSENT" if (not lamps or "ABSENT" in lamps) else "GREEN")
        row = {"id": e.get("id"), "batch": e.get("batch"), "cls": e.get("cls"), "n": e.get("n"),
               "what": e.get("what"), "lamp": lamp, "checks": checks}
        rep["rows"].append(row)
        rep["tally"][lamp] = rep["tally"].get(lamp, 0) + 1
        if lamp == "RED":
            rep["regressions"].append(row["id"])
    rep["state"] = "RED" if rep["regressions"] else ("ABSENT" if not rep["rows"] else "GREEN")
    rep["why"] = (f"冊 {len(rep['rows'])} 筆複驗 · " + " · ".join(f"{k} {v}" for k, v in sorted(rep["tally"].items()))
                  + (f" · 回歸 {rep['regressions']}" if rep["regressions"] else " · 回歸 0"))
    return rep


def issue_triage(scan_d: dict) -> dict:
    """把問題數按 L56 三態拆開——同時修 / 順序修 / 只報位置待令,再單列真 RED。"""
    par = seq = rep_only = red = ex = 0
    ex_by = (scan_d.get("by_class_exempt") or {})
    for cls, n in (scan_d.get("by_class") or {}).items():
        act = CATEGORIES.get(cls, (cls, "REPORT", ""))[1]
        e = min(int(ex_by.get(cls, 0)), n)           # 批658:同類裡屬正典 TEMPLATE 的份額
        if cls in ("SYNTAX", "TALIB"):
            red += n
            continue
        if act == "GREEN_FIX":
            ex += e                                   # 名冊件:看得見、算得出,但**不可修**
            if cls in PAR_CLS:                        # ACCEL/NET 純增量=可同檔平行;VERB 動入口=順序
                par += n - e
            else:
                seq += n - e
        else:
            rep_only += n
    return {"parallel": par, "sequential": seq, "report_only": rep_only, "red": red,
            "exempt": ex, "total": int(scan_d.get("issues", 0))}


def summary_line(pay: dict) -> str:
    """一句話講清楚:四個數字各有出處(主控台、頁首、TAB①、Markdown 同一句)。"""
    tri = pay.get("triage") or {}
    fl = pay.get("fixed") or {}
    t = pay.get("tests") or {}
    tally = t.get("tally") or {}
    n_test = len(t.get("rows") or [])
    ft = fl.get("tally") or {}
    return (f"問題 {tri.get('total', 0)}(可同時修 {tri.get('parallel', 0)} · 順序修 {tri.get('sequential', 0)}"
            f" · 只報位置待令 {tri.get('report_only', 0)} · 正典不得改 {tri.get('exempt', 0)} · 真 RED {tri.get('red', 0)})"
            f" · 已修冊 {len(fl.get('rows') or [])} 筆複驗 GREEN {ft.get('GREEN', 0)} / 回歸 {len(fl.get('regressions') or [])}"
            f" / 待驗 {ft.get('ABSENT', 0)}"
            f" · 本次自動修 {sum((pay.get('fix') or {}).get('applied_by_class', {}).values())} 處"
            f" · 實測 {tally.get('GREEN', 0)}/{n_test} 綠")


def _lamp(state: str) -> str:
    return {"GREEN": "g", "YELLOW": "y", "ABSENT": "a", "NODATA": "a", "TIMEOUT": "r", "RED": "r"}.get(state, "a")


def render_md(pay: dict) -> str:
    s = pay["scan"]; f = pay.get("fix") or {}; t = pay.get("tests") or {}; c = pay["coverage"]
    L = [f"# VIA 全景稽核修復報告 · {pay['batch']} · {pay['ts']}", "",
         f"**總裁決:{pay['verdict']}** · 掃 {s['files_scanned']} 檔", "",
         f"**{pay.get('summary') or summary_line(pay)}**", "",
         "## 一 · 問題分類(紅黃綠)", "", "| 類 | 說明 | 處置 | 件數 |", "|---|---|---|---:|"]
    for cls, n in sorted(s["by_class"].items(), key=lambda x: -x[1]):
        zh, act, fixhow = CATEGORIES.get(cls, (cls, "REPORT", ""))
        L.append(f"| {cls} | {zh} | {'自動修' if act == 'GREEN_FIX' else '報位置待令'} | {n} |")
    L += ["", "## 二 · 分系統矩陣", "", "| 系統 | " + " | ".join(CATEGORIES) + " |", "|---" * (len(CATEGORIES) + 1) + "|"]
    for sysname, d in sorted(s["by_system"].items()):
        L.append(f"| {sysname} | " + " | ".join(str(d.get(k, 0)) for k in CATEGORIES) + " |")
    L += ["", "## 三 · 覆蓋率", "",
          f"- 加速器橋:{c['accel']}/{c['py_total']}({c['accel_pct']}%)",
          f"- VDF 網路工具橋:{c['net']}/{c['vdf_engines']}({c['net_pct']}%)", "",
          "## 四 · 實測結果(誠實四態)", "", "| 系統 | 引擎 | 燈 | rc | 秒 | 說明 |", "|---|---|---|---:|---:|---|"]
    for r in t.get("rows", []):
        L.append(f"| {r['system']} | {r['name']} | {r['state']} | {r['rc']} | {r['secs']} | {str(r['why'])[:90]} |")
    d = t.get("dispatch") or {}
    L += ["", f"**中央派送**:{d.get('state')} · {d.get('counts')}", ""]
    if f.get("rows"):
        L += ["## 五 · 本次修復(平行/順序)", "",
              f"{'已套用' if f.get('apply') else '乾跑計畫(加 --apply 才寫檔)'} · 平行 {f['parallel_files']} 檔 · 順序 {f['sequential_files']} 檔 · 工人 {f['workers']}({f['worker_source']})", ""]
    fl = pay.get("fixed") or {}
    L += ["## 六 · 歷批已修冊複驗(冊說修好,現在還是不是?)", "",
          f"冊:`{fl.get('src','-')}` · {fl.get('why','-')}", "",
          "| 批 | 類 | 已修 | 燈 | 內容 | 複驗憑據 |", "|---|---|---:|---|---|---|"]
    for r in fl.get("rows", []):
        ev = " ／ ".join(f"{c['lamp']}:{c['why']}" for c in r.get("checks", []))
        L.append(f"| {r['batch']} | {r['cls']} | {r['n']} | {r['lamp']} | {str(r['what'])[:70]} | {ev[:150]} |")
    if not fl.get("rows"):
        L.append(f"| — | — | — | ABSENT | {fl.get('why','冊不在')} | — |")
    return "\n".join(L)


def render_html(pay: dict) -> str:
    s = pay["scan"]; f = pay.get("fix") or {}; t = pay.get("tests") or {}; c = pay["coverage"]
    j = _html.escape(json.dumps(pay, ensure_ascii=False, indent=1))
    md = _html.escape(render_md(pay))
    def rows_issue():
        out = []
        for r in s["rows"][:4000]:
            zh, act, fixhow = CATEGORIES.get(r["cls"], (r["cls"], "REPORT", ""))
            lamp = "g" if act == "GREEN_FIX" else ("r" if r["cls"] in ("SYNTAX", "TALIB") else "y")
            out.append(f"<tr data-sys='{_html.escape(r['system'])}' data-cls='{r['cls']}'><td><span class=d-{lamp}></span>{r['cls']}</td>"
                       f"<td>{_html.escape(r['system'])}</td><td class=mono>{_html.escape(r['file'])}</td><td class=num>{r['line']}</td>"
                       f"<td>{_html.escape(r['how'])}</td><td>{_html.escape(str(r['detail'])[:150])}</td><td>{_html.escape(fixhow)}</td></tr>")
        return "".join(out)
    def rows_test():
        out = []
        for r in t.get("rows", []):
            out.append(f"<tr><td>{_html.escape(r['system'])}</td><td>{_html.escape(r['name'])}</td>"
                       f"<td class=mono>{_html.escape(r.get('engine') or '')}</td>"
                       f"<td><span class=d-{_lamp(r['state'])}></span>{r['state']}</td><td class=num>{r['rc']}</td>"
                       f"<td class=num>{r['secs']}</td><td>{_html.escape(str(r['why'])[:160])}</td></tr>")
        return "".join(out)
    def rows_fix():
        out = []
        for r in (f.get("rows") or []):
            if not r.get("applied") and not r.get("skipped"):
                continue
            out.append(f"<tr><td class=mono>{_html.escape(r['file'])}</td><td>{'平行' if set(r.get('applied') or []) <= {'ACCEL','NET'} else '順序'}</td>"
                       f"<td>{_html.escape(','.join(r.get('applied') or []) or '-')}</td>"
                       f"<td>{_html.escape(','.join(r.get('skipped') or []) or '-')}</td>"
                       f"<td><span class=d-{('g' if r['ok'] else 'r') if f.get('apply') else 'a'}></span>"
                       f"{('OK' if r['ok'] else 'FAIL') if f.get('apply') else '乾跑(未寫檔)'}</td>"
                       f"<td>{_html.escape(str(r.get('why') or ''))[:110]}</td></tr>")
        return "".join(out) or "<tr><td colspan=6>本次無可自動修的項(ACCEL/NET/VERB 三類皆為 0)</td></tr>"

    def rows_fixed():
        out = []
        for r in ((pay.get("fixed") or {}).get("rows") or []):
            ev = "<br>".join(f"<span class=d-{_lamp(c['lamp'])}></span>{_html.escape(c['why'])}" for c in r.get("checks", []))
            out.append(f"<tr><td>{_html.escape(str(r['batch']))}</td><td>{_html.escape(str(r['cls']))}</td>"
                       f"<td class=num>{r['n']}</td><td><span class=d-{_lamp(r['lamp'])}></span>{r['lamp']}</td>"
                       f"<td>{_html.escape(str(r['what']))}</td><td>{ev}</td></tr>")
        return "".join(out) or f"<tr><td colspan=6>{_html.escape(str((pay.get('fixed') or {}).get('why') or '已修冊不在'))}</td></tr>"
    n_fix = sum((f.get("applied_by_class") or {}).values())
    tri = pay.get("triage") or issue_triage(s)
    _fl = pay.get("fixed") or {}
    n_fixed = len(_fl.get("rows") or [])
    n_fixed_green = (_fl.get("tally") or {}).get("GREEN", 0)
    n_regress = len(_fl.get("regressions") or [])
    tally = t.get("tally") or {}
    n_green = tally.get("GREEN", 0)
    n_test = len(t.get("rows") or [])
    matrix_head = "".join(f"<th>{k}</th>" for k in CATEGORIES)
    matrix_rows = "".join(
        "<tr><td>" + _html.escape(sysname) + "</td>" + "".join(
            f"<td class=num><span class=d-{'g' if d.get(k,0)==0 else ('y' if CATEGORIES[k][1]=='GREEN_FIX' else 'r')}></span>{d.get(k,0)}</td>"
            for k in CATEGORIES) + "</tr>"
        for sysname, d in sorted(s["by_system"].items()))
    d = t.get("dispatch") or {}
    disp_rows = "".join(f"<tr><td>{_html.escape(str(x.get('family')))}</td><td class=mono>{_html.escape(str(x.get('engine')))}</td>"
                        f"<td><span class=d-{_lamp(str(x.get('state')))}></span>{x.get('state')}</td><td class=num>{x.get('rc')}</td>"
                        f"<td>{_html.escape(str(x.get('python_source')))}</td></tr>" for x in (d.get("routes") or []))
    return f"""<!doctype html><html lang=zh-Hant><head><meta charset=utf-8>
<title>VIA 全景稽核修復矩陣 · {pay['batch']}</title><style>
:root{{--g:#16a34a;--y:#d97706;--r:#dc2626;--a:#64748b;--bg:#fbfcfd;--bd:#e2e8f0;--tx:#0f172a}}
*{{box-sizing:border-box}}body{{margin:0;font:11.5px/1.5 -apple-system,"Segoe UI","Noto Sans TC",sans-serif;background:var(--bg);color:var(--tx)}}
header{{padding:10px 14px;border-bottom:1px solid var(--bd);background:#fff;position:sticky;top:0;z-index:5}}
h1{{font-size:14px;margin:0 0 4px}}.sub{{color:#64748b;font-size:11px}}
.tabs{{display:flex;gap:2px;flex-wrap:wrap;margin-top:8px}}
.tab{{padding:4px 10px;border:1px solid var(--bd);border-bottom:none;background:#f1f5f9;cursor:pointer;font-size:11px;border-radius:4px 4px 0 0}}
.tab.on{{background:#fff;font-weight:600;color:#0369a1}}
.panel{{display:none;padding:12px 14px}}.panel.on{{display:block}}
table{{border-collapse:collapse;width:100%;background:#fff;font-size:11px}}
th,td{{border:1px solid var(--bd);padding:3px 6px;text-align:left;vertical-align:top}}
th{{background:#f8fafc;position:sticky;top:0;font-weight:600}}
td.num{{text-align:right;font-variant-numeric:tabular-nums}}.mono{{font-family:ui-monospace,Consolas,monospace;font-size:10.5px}}
span[class^=d-]{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}}
.d-g{{background:var(--g)}}.d-y{{background:var(--y)}}.d-r{{background:var(--r)}}.d-a{{background:var(--a)}}
.kpi{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}}
.card{{border:1px solid var(--bd);background:#fff;border-radius:6px;padding:8px 12px;min-width:120px}}
.card b{{display:block;font-size:18px;line-height:1.1}}.card span{{color:#64748b;font-size:10.5px}}
pre{{background:#0f172a;color:#e2e8f0;padding:10px;border-radius:6px;overflow:auto;max-height:440px;font-size:10.5px}}
.bar{{height:6px;background:#e2e8f0;border-radius:3px;overflow:hidden;margin-top:4px}}.bar i{{display:block;height:100%;background:var(--g)}}
input,select{{font:11px inherit;padding:2px 6px;border:1px solid var(--bd);border-radius:4px}}
.wrap{{max-height:70vh;overflow:auto;border:1px solid var(--bd);border-radius:6px}}
</style></head><body>
<header><h1>VIA 全景稽核修復矩陣 · {pay['batch']} · 總裁決 <span class=d-{_lamp(pay['verdict'])}></span>{pay['verdict']}</h1>
<div class=sub>{pay['ts']} · 掃 {s['files_scanned']} 檔 · 工人 {f.get('workers','-')}({_html.escape(str(f.get('worker_source','-')))})</div>
<div class=sub style="color:#0f172a;font-weight:600">{_html.escape(pay.get('summary') or '')}</div>
<div class=tabs>
<div class="tab on" data-t=0>① 總覽(AI/操作員)</div><div class=tab data-t=1>② 問題明細</div><div class=tab data-t=2>③ 本次修復</div>
<div class=tab data-t=3>④ 已修冊複驗</div><div class=tab data-t=4>⑤ 實測結果</div><div class=tab data-t=5>⑥ 中央派送</div>
<div class=tab data-t=6>⑦ 覆蓋率</div><div class=tab data-t=7>⑧ JSON</div><div class=tab data-t=8>⑨ Markdown</div></div></header>

<div class="panel on" id=p0>
<div class=kpi>
<div class=card><b>{tri.get('total',0)}</b><span>問題總數(可同時修 {tri.get('parallel',0)} · 順序 {tri.get('sequential',0)} · 待令 {tri.get('report_only',0)})</span></div>
<div class=card><b>{tri.get('red',0)}</b><span>真 RED(語法錯／TA-Lib 接線)</span></div>
<div class=card><b>{n_fixed_green}/{n_fixed}</b><span>已修冊複驗綠 · 回歸 {n_regress}</span></div>
<div class=card><b>{n_fix}</b><span>本次自動修</span></div>
<div class=card><b>{c['accel_pct']}%</b><span>加速器橋覆蓋<div class=bar><i style="width:{c['accel_pct']}%"></i></div></span></div>
<div class=card><b>{c['net_pct']}%</b><span>VDF 網路工具覆蓋<div class=bar><i style="width:{c['net_pct']}%"></i></div></span></div>
<div class=card><b>{n_green}/{n_test}</b><span>實測綠燈</span></div>
</div>
<h3 style="font-size:12px">分系統 × 分範疇矩陣(綠=零問題;黃=可自動修;紅=需人工判)</h3>
<table><thead><tr><th>系統</th>{matrix_head}</tr></thead><tbody>{matrix_rows}</tbody></table>
<h3 style="font-size:12px;margin-top:12px">範疇說明與處置</h3>
<table><thead><tr><th>類</th><th>說明</th><th>處置</th><th>修法</th><th>件數</th></tr></thead><tbody>
{"".join(f"<tr><td><span class=d-{'g' if v[1]=='GREEN_FIX' else 'y'}></span>{k}</td><td>{v[0]}</td><td>{'自動修(本器)' if v[1]=='GREEN_FIX' else '報位置待令'}</td><td>{v[2]}</td><td class=num>{s['by_class'].get(k,0)}</td></tr>" for k, v in CATEGORIES.items())}
</tbody></table></div>

<div class=panel id=p1><div style="margin-bottom:6px">篩選 <input id=q placeholder="檔名/類/系統…" oninput="flt()"> </div>
<div class=wrap><table id=tIssue><thead><tr><th>類</th><th>系統</th><th>檔案</th><th>行</th><th>定位</th><th>說明</th><th>建議修法</th></tr></thead><tbody>{rows_issue()}</tbody></table></div></div>

<div class=panel id=p2><div class=wrap><table><thead><tr><th>檔案</th><th>模式</th><th>已套用</th><th>略過</th><th>結果</th><th>說明</th></tr></thead><tbody>{rows_fix()}</tbody></table></div></div>

<div class=panel id=p3><p>冊:<span class=mono>{_html.escape(str((pay.get('fixed') or {}).get('src','-')))}</span> · {_html.escape(str((pay.get('fixed') or {}).get('why','-')))}</p>
<p class=sub>這張表不是功勞簿:每一筆都拿活樹重量一次。綠=冊說修好、現在也還是修好;紅=<b>回歸</b>(尾版律下最容易發生——切了新版沒把修帶過去);灰=量不了,誠實講量不了。</p>
<div class=wrap><table><thead><tr><th>批</th><th>類</th><th>已修</th><th>燈</th><th>內容</th><th>複驗憑據(活樹重量)</th></tr></thead><tbody>{rows_fixed()}</tbody></table></div></div>

<div class=panel id=p4><div class=wrap><table><thead><tr><th>系統</th><th>引擎</th><th>檔</th><th>燈</th><th>rc</th><th>秒</th><th>說明</th></tr></thead><tbody>{rows_test()}</tbody></table></div></div>

<div class=panel id=p5><p>中央派送裁決:<span class=d-{_lamp(str(d.get('state')))}></span><b>{d.get('state')}</b> · {_html.escape(str(d.get('counts')))}</p>
<table><thead><tr><th>家族</th><th>引擎</th><th>燈</th><th>rc</th><th>python 來源</th></tr></thead><tbody>{disp_rows or '<tr><td colspan=5>無路由</td></tr>'}</tbody></table></div>

<div class=panel id=p6><table><thead><tr><th>項</th><th>已有</th><th>總數</th><th>覆蓋率</th></tr></thead><tbody>
<tr><td>指令加速器橋(全樹 .py)</td><td class=num>{c['accel']}</td><td class=num>{c['py_total']}</td><td class=num>{c['accel_pct']}%</td></tr>
<tr><td>網路工具橋(VDF 引擎)</td><td class=num>{c['net']}</td><td class=num>{c['vdf_engines']}</td><td class=num>{c['net_pct']}%</td></tr>
</tbody></table></div>

<div class=panel id=p7><pre id=js>{j}</pre></div>
<div class=panel id=p8><pre id=mdp>{md}</pre></div>

<script>
document.querySelectorAll('.tab').forEach(function(x){{x.onclick=function(){{
 document.querySelectorAll('.tab').forEach(function(y){{y.classList.remove('on')}});
 document.querySelectorAll('.panel').forEach(function(y){{y.classList.remove('on')}});
 x.classList.add('on'); document.getElementById('p'+x.dataset.t).classList.add('on');}}}});
function flt(){{var v=document.getElementById('q').value.toLowerCase();
 document.querySelectorAll('#tIssue tbody tr').forEach(function(r){{r.style.display=r.innerText.toLowerCase().indexOf(v)>=0?'':'none'}});}}
</script></body></html>"""


def write_report(pay: dict, do_open: bool = False) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    hp, jp, mp = OUT / "PANORAMA_AUDIT_latest.html", OUT / "PANORAMA_AUDIT_latest.json", OUT / "PANORAMA_AUDIT_latest.md"
    hp.write_text(render_html(pay), encoding="utf-8")
    jp.write_text(json.dumps(pay, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    mp.write_text(render_md(pay), encoding="utf-8")
    (OUT / f"PANORAMA_AUDIT_{stamp}.json").write_text(json.dumps(pay, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if do_open and not os.environ.get("VIA_NO_OPEN"):
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(hp))  # noqa: S606
        except Exception:
            pass
    return {"html": str(hp), "json": str(jp), "md": str(mp)}


def run_all(apply: bool, do_open: bool, fast: bool = False, limit: int = 0) -> dict:
    _p(1, "全景稽核啟動(AST 精準定位;收容件/退役夾零觸碰)")
    s = scan(limit=limit)
    _p(31, f"掃描完成:{s['files_scanned']} 檔 · {s['issues']} 問題")
    f = fix({"ACCEL", "NET", "VERB"}, apply=apply, scan_rows=s["rows"])
    _p(61, f"修復{'(已套用)' if apply else '(乾跑)'}:{sum(f['applied_by_class'].values())} 處")
    t = run_tests(fast=fast)
    _p(90, f"實測完成:{t['verdict']}")
    s2 = scan(progress=False) if apply else s
    cov = coverage()
    verdict = "RED" if (t["verdict"] == "RED" or s2["by_class"].get("SYNTAX")) else (
        "YELLOW" if (t["verdict"] == "YELLOW" or s2["issues"]) else "GREEN")
    fl = fixed_ledger(s2, cov)                       # 批537:已修冊拿活樹重量一次(回歸=RED)
    if fl.get("regressions") and verdict != "RED":
        verdict = "RED"                              # 冊說修好卻又量到=回歸,這是真紅燈,不能被 YELLOW 蓋過去
    pay = {"schema": "VIA.CGC158.panorama.v1", "batch": "批537", "engine": f"{ENGINE_ID} {VERSION}",
           "ts": _dt.datetime.now().isoformat(timespec="seconds"), "verdict": verdict,
           "scan": s2, "scan_before": {"issues": s["issues"], "by_class": s["by_class"]}, "fix": f,
           "tests": t, "coverage": cov, "triage": issue_triage(s2), "fixed": fl,
           "laws": ["L30 一功能一主", "L50 QuantGuard-only", "L51 中央派送家族境", "L52 誠實四態", "L53 動詞契約",
                    "L54 尾版律", "L56 自動修三態", "L57 誠實分母", "L58 證據分級"]}
    pay["summary"] = summary_line(pay)
    _p(95, f"已修冊複驗:{fl.get('why', '')[:70]}")
    paths = write_report(pay, do_open)
    pay["paths"] = paths
    _p(100, f"報告完成 → {paths['html']}")
    return pay


# ---------------------------------------------------------------- 自測
# ---------------------------------------------------------------- 批707:AI 代讀(read / slice)
# 操作員令(批707):「全景式讀取指令的功能整合起來…代為讀取節省 AI 讀取的 TOKEN…自動讀取識別錯誤 AST…
#   避免傷害…串起來成唯一的標準功能」。先量(L116「整合進來最好的做法常常是不要重寫」):
#   · 本器 scan = 全樹**稽核**(治理七類),不回答「這支檔裡有什麼」;
#   · CGC_MDL161 PEIS = 跨家族**能力卡**(要先 scan 建庫),也不回答「這支檔第 N 行那個函式長什麼樣」。
#   缺的正是 L65「AI 讀卡,不讀原始碼」的**單檔那一層**。所以不另立引擎(零九頭龍),補在全景正主上:
#   · `read <路徑…>`  → 骨架卡(匯入 · 定義樹含行號/簽章/首行說明 · AST 錯誤),不回原始碼;
#   · `slice <路徑> <名>` → 只回那一個定義的原始碼(帶行號)——L65「只載入受影響的最小片段」。
#   **唯讀**:兩個動詞零寫檔、零執行被讀的檔(只 ast.parse;PowerShell 只做文字剖析),所以不可能傷系統。
#   錯誤判準分兩層,不混帳:治理七類照舊由 audit_source 出(只在 VIA 樹內才算,樹外的檔不背 VIA 的律);
#   通用程式錯誤是本批新增的「只報位置」五類(READ_CHECKS),**不進 scan 的帳**——scan 的數字與歷批已修冊零變動。
READ_CHECKS = {
    "DUPDEF": "同一層同名定義兩次(後者默默蓋掉前者;LL283 via-ui 被自己抹掉就是這一型)",
    "SWALLOW": "except 本體只有 pass/continue/...(例外被吞、沒有任何看得見的改變;LL151)",
    "BAREEXC": "裸 except:(連 KeyboardInterrupt / SystemExit 都吞)",
    "MUTDEF": "可變預設引數([] / {} / set() / dict() / list())——跨呼叫共用同一個物件",
    "UNREACH": "return/raise/break/continue 之後同一區塊還有陳述式(永遠跑不到)",
    "PSDUPFN": "PowerShell 同名 function 定義兩次(後者蓋掉前者;LL283)",
    "PSDOCSTR": "PowerShell 函式本體開頭是三引號字串(不是註解,是回傳值;LL182)",
}
#: 全景排序先看「真會出錯」的類(語法/同名蓋掉/跑不到/裸 except/PS 回傳值污染),再看總數——
#: SWALLOW 在 graceful 設計裡常是刻意的,數量又大,拿總數排會把真 bug 淹在後面。
_READ_SEVERE = frozenset(("SYNTAX", "DUPDEF", "PSDUPFN", "UNREACH", "BAREEXC", "PSDOCSTR"))
_READ_TEXT_EXT = (".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".cmd", ".bat", ".html", ".css", ".js", ".ts", ".sh")


def _CJK(ch: str) -> bool:
    """這個字元算不算 CJK(含全形標點)。單一出處,兩處尺共用(L30)。"""
    return "\u3000" <= ch <= "\u9fff" or "\uff00" <= ch <= "\uffef"


def _tok(n_chars: int, text: str = "") -> int:
    """粗估 token。

    批708(操作員令「優化他作為節省 TOKEN 的工具」)**這把尺原本是錯的**:
      v0105 一律 `n_chars // 4`。ASCII 大致對,**CJK 差很多** —— 中日韓字元在
      主流 BPE 分詞器上約 1 字元 1 token,用 4 字元/token 去估會把帳報成**約一半**。
      實測 `CGC_MDL147_v0103`:舊尺 8908,CJK 感知尺 13375 —— **少報 33%**。

    為什麼原本沒被抓到:`read` 印的是**省下的百分比**,而原檔與骨架卡的 CJK 佔比相近,
      分子分母一起偏低,**比值幾乎不動**(95.0% vs 94.9%)。
      **只檢比值的檢,永遠照不出這個缺陷**——所以檢 ㉛ 釘的是**絕對值**。

    `text` 給了就照它的 CJK 佔比算;沒給就退回舊的純字元估(呼叫端沒改到的地方誠實降級,不假裝)。
    """
    if not text:
        return max(1, n_chars // 4)
    cjk = sum(1 for c in text if _CJK(c))
    return max(1, (len(text) - cjk) // 4 + cjk)


def _sig(fn) -> str:
    """定義簽章(含型別註記與回傳);ast.unparse 讀不出來就退回參數名,不猜。"""
    try:
        s = ast.unparse(fn.args)
    except Exception:
        s = ", ".join(a.arg for a in fn.args.args)
    ret = ""
    if getattr(fn, "returns", None) is not None:
        try:
            ret = " -> " + ast.unparse(fn.returns)
        except Exception:
            ret = ""
    return f"({s}){ret}"


def _doc1(node) -> str:
    d = ast.get_docstring(node, clean=True) if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) else None
    return (d or "").strip().splitlines()[0][:100] if d else ""


def _read_checks_py(tree) -> list[dict]:
    """通用程式錯誤五類——只報位置,不改(L56 ③)。"""
    out: list[dict] = []
    for nd in ast.walk(tree):
        body_lists = [getattr(nd, f, None) for f in ("body", "orelse", "finalbody")]
        if isinstance(nd, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            seen: dict[str, int] = {}
            for st in nd.body:
                if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    deco = {ast.unparse(d) for d in st.decorator_list} if st.decorator_list else set()
                    if any(x.endswith((".setter", ".deleter", ".register")) or x in ("overload", "typing.overload") for x in deco):
                        continue                            # property setter / singledispatch / overload 是刻意同名
                    if st.name in seen:
                        out.append({"cls": "DUPDEF", "line": st.lineno, "how": "ast",
                                    "detail": f"{st.name} 在第 {seen[st.name]} 行已定義,這裡蓋掉它"})
                    seen[st.name] = st.lineno
        for bl in body_lists:
            if not isinstance(bl, list):
                continue
            for i, st in enumerate(bl[:-1]):
                if isinstance(st, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                    out.append({"cls": "UNREACH", "line": bl[i + 1].lineno, "how": "ast",
                                "detail": f"第 {st.lineno} 行 {type(st).__name__.lower()} 之後的陳述式跑不到"})
                    break
        if isinstance(nd, ast.ExceptHandler):
            if nd.type is None:
                out.append({"cls": "BAREEXC", "line": nd.lineno, "how": "ast", "detail": "except: 未指名例外型別"})
            if all(isinstance(s, (ast.Pass, ast.Continue)) or (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
                   for s in nd.body):
                what = ast.unparse(nd.type) if nd.type is not None else "(全部)"
                out.append({"cls": "SWALLOW", "line": nd.lineno, "how": "ast", "detail": f"except {what} 被吞:本體只有 pass/continue"})
        if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dv in list(nd.args.defaults) + [d for d in nd.args.kw_defaults if d is not None]:
                mut = isinstance(dv, (ast.List, ast.Dict, ast.Set)) or (
                    isinstance(dv, ast.Call) and isinstance(dv.func, ast.Name) and dv.func.id in ("list", "dict", "set") and not dv.args)
                if mut:
                    out.append({"cls": "MUTDEF", "line": dv.lineno, "how": "ast",
                                "detail": f"{nd.name}() 預設引數 {ast.unparse(dv)[:24]} 可變"})
    return out


def _outline_py(tree) -> list[dict]:
    """定義樹:類別與函式(含巢狀方法),每筆 行號範圍/簽章/首行說明;不含函式內部的區域定義細節以外的原始碼。"""
    rows: list[dict] = []

    def walk(body, prefix: str, depth: int):
        for st in body:
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
                rows.append({"kind": "async def" if isinstance(st, ast.AsyncFunctionDef) else "def",
                             "name": prefix + st.name, "line": st.lineno, "end": st.end_lineno or st.lineno,
                             "sig": _sig(st), "doc": _doc1(st), "depth": depth})
                if depth < 1:
                    walk(st.body, prefix + st.name + ".", depth + 1)
            elif isinstance(st, ast.ClassDef):
                bases = ", ".join(ast.unparse(b) for b in st.bases)
                rows.append({"kind": "class", "name": prefix + st.name, "line": st.lineno, "end": st.end_lineno or st.lineno,
                             "sig": f"({bases})" if bases else "", "doc": _doc1(st), "depth": depth})
                walk(st.body, prefix + st.name + ".", depth + 1)
    walk(tree.body, "", 0)
    return rows


def _imports_py(tree) -> list[str]:
    got: list[str] = []
    for st in tree.body:
        if isinstance(st, ast.Import):
            got += [a.name for a in st.names]
        elif isinstance(st, ast.ImportFrom):
            got.append(("." * st.level) + (st.module or ""))
    return sorted(set(got))


_PS_FN = re.compile(r"^\s*function\s+(?:global:|script:)?([\w\-\.]+)", re.I | re.M)


def _ps_block_end(lines: list[str], start: int) -> int:
    """從第 start 行(0 起)找函式的收尾大括號;字串/註解內的括號不精算——只給位置,不拿去改檔。"""
    depth, opened = 0, False
    for i in range(start, len(lines)):
        ln = re.sub(r"#.*$", "", lines[i])
        ln = re.sub(r"'[^']*'|\"[^\"]*\"", "", ln)
        depth += ln.count("{") - ln.count("}")
        opened = opened or "{" in ln
        if opened and depth <= 0:
            return i
    return len(lines) - 1


def _mask_herestrings(src: str) -> str:
    """把 here-string(@' … '@ / @" … "@)的內容行換成空行(行數不變)。
    批707 首跑實錄:14 件 PSDUPFN 全是誤報——內嵌在 here-string 裡的 JavaScript(fmt/render/done…)
    與「產生另一支腳本」的模板(EnsureDir/def_Main)被當成 PowerShell 函式。"""
    out, inside = [], None
    for ln in src.split("\n"):
        if inside is None:
            out.append(ln)
            t = ln.rstrip()
            if t.endswith("@'") or t.endswith('@"'):
                inside = t[-1]
        else:
            if ln.startswith(inside + "@"):
                out.append(ln)
                inside = None
            else:
                out.append("")
    return "\n".join(out)


def _read_ps1(src: str) -> tuple[list[dict], list[dict]]:
    masked = _mask_herestrings(src)
    lines = masked.splitlines()
    rows, issues, seen = [], [], {}
    for m in _PS_FN.finditer(masked):
        ln0 = masked.count("\n", 0, m.start())
        end = _ps_block_end(lines, ln0)
        name = m.group(1)
        # 父作用域=包住它的最內層函式;巢狀在不同父函式裡的同名函式各是區域函式,互不覆蓋(批707 實錄 Test-Prot)
        parent = next((r["name"] for r in reversed(rows) if r["line"] <= ln0 + 1 <= r["end"]), "")
        rows.append({"kind": "function", "name": name, "line": ln0 + 1, "end": end + 1, "sig": "", "doc": "",
                     "depth": 1 if parent else 0})
        key = (parent.lower(), name.lower())
        if key in seen:
            issues.append({"cls": "PSDUPFN", "line": ln0 + 1, "how": "text",
                           "detail": f"{name} 在第 {seen[key]} 行已定義,這裡蓋掉它" + (f"(同在 {parent} 內)" if parent else "")})
        seen[key] = ln0 + 1
        body = "\n".join(lines[ln0:end + 1])
        inner = body.split("{", 1)[1].lstrip() if "{" in body else ""
        inner = re.sub(r"^\s*(param\s*\([^)]*\)|\[CmdletBinding\([^)]*\)\])\s*", "", inner, flags=re.I)
        if inner.startswith(('"""', "'''")):
            issues.append({"cls": "PSDOCSTR", "line": ln0 + 1, "how": "text", "detail": f"{name} 開頭三引號字串會變成回傳值"})
    return rows, issues


def _read_text(src: str, ext: str) -> list[dict]:
    rows = []
    if ext == ".md":
        for i, ln in enumerate(src.splitlines(), 1):
            m = re.match(r"^(#{1,4})\s+(.*)", ln)
            if m:
                rows.append({"kind": "h" + str(len(m.group(1))), "name": m.group(2)[:90], "line": i, "end": i,
                             "sig": "", "doc": "", "depth": len(m.group(1)) - 1})
    elif ext == ".json":
        try:
            obj = json.loads(src)
            if isinstance(obj, dict):
                for k, v in list(obj.items())[:80]:
                    size = len(v) if isinstance(v, (list, dict, str)) else ""
                    rows.append({"kind": type(v).__name__, "name": str(k)[:90], "line": 0, "end": 0,
                                 "sig": f"[{size}]" if size != "" else "", "doc": "", "depth": 0})
            elif isinstance(obj, list):
                rows.append({"kind": "list", "name": f"頂層陣列 {len(obj)} 筆", "line": 1, "end": 1, "sig": "", "doc": "", "depth": 0})
        except Exception as exc:
            rows.append({"kind": "ERROR", "name": f"JSON 解析失敗:{type(exc).__name__}: {str(exc)[:80]}", "line": 0, "end": 0,
                         "sig": "", "doc": "", "depth": 0})
    return rows


def read_file(path: Path) -> dict:
    """單檔骨架卡(唯讀)。回:行數 · 匯入 · 定義樹 · 問題(治理七類僅 VIA 樹內 + 通用五類)· token 帳。"""
    path = Path(path).resolve()
    src = path.read_text(encoding="utf-8-sig", errors="replace")
    ext = path.suffix.lower()
    card: dict = {"path": str(path), "lines": src.count("\n") + (0 if src.endswith("\n") or not src else 1),
                  "bytes": len(src.encode("utf-8")), "chars": len(src),
                  "cjk": sum(1 for _c in src if _CJK(_c)),   # 批708:token 尺要分 ASCII/CJK
                  "lang": ext.lstrip(".") or "text",
                  "imports": [], "defs": [], "issues": [], "in_via": False}
    try:
        rel = str(path.relative_to(VIA))
        card["in_via"] = True
    except ValueError:
        rel = path.name
    if ext == ".py":
        try:
            tree = ast.parse(src, filename=str(path))
        except SyntaxError as exc:
            card["issues"].append({"cls": "SYNTAX", "line": int(exc.lineno or 1), "how": "compile",
                                   "detail": f"{type(exc).__name__}: {str(exc)[:120]}"})
            tree = None
        if tree is not None:
            card["module_doc"] = _doc1(tree)
            card["imports"] = _imports_py(tree)
            card["defs"] = _outline_py(tree)
            card["issues"] += _read_checks_py(tree)
            if card["in_via"]:
                card["issues"] += [i for i in audit_source(path, src, rel) if i["cls"] != "SYNTAX"]
    elif ext == ".ps1" or ext == ".psm1":
        card["defs"], card["issues"] = _read_ps1(src)
    elif ext in _READ_TEXT_EXT:
        card["defs"] = _read_text(src, ext)
    card["issues"].sort(key=lambda r: (r["line"], r["cls"]))
    return card


def render_card(card: dict, max_defs: int = 400) -> str:
    """骨架卡文字版——給 AI 讀的就是這一份,原始碼一行都不帶。"""
    out = [f"## {card['path']}  [{card['lang']} · {card['lines']} 行 · {card['bytes']} B]"]
    if card.get("module_doc"):
        out.append(f"  說明: {card['module_doc']}")
    if card["imports"]:
        out.append("  匯入: " + ", ".join(card["imports"])[:600])
    for d in card["defs"][:max_defs]:
        rng = f"L{d['line']}-{d['end']}" if d["line"] else ""
        doc = f"  # {d['doc']}" if d["doc"] else ""
        out.append(f"  {'  ' * d['depth']}{rng:<12} {d['kind']} {d['name']}{d['sig']}{doc}")
    if len(card["defs"]) > max_defs:
        out.append(f"  …(另 {len(card['defs']) - max_defs} 個定義未列;加 --max-defs 放寬)")
    if card["issues"]:
        out.append(f"  問題 {len(card['issues'])}:")
        for it in card["issues"]:
            tag = "免" if it.get("exempt") else ("報" if it["cls"] in READ_CHECKS or CATEGORIES.get(it["cls"], ("", "REPORT"))[1] == "REPORT" else "修")
            out.append(f"    [{tag}] L{it['line']:<5} {it['cls']:<8} {it['detail']}")
    else:
        out.append("  問題 0")
    return "\n".join(out)


def _expand_read_targets(paths: list[str]) -> list[Path]:
    """資料夾=只收活樹 .py/.ps1(沿用 _skip 與尾版律;收容件/退役夾不讀);檔案=照收。"""
    got: list[Path] = []
    for p in paths:
        q = Path(p)
        if not q.is_absolute() and not q.exists() and (VIA / p).exists():
            q = VIA / p
        if q.is_dir():
            py = py_files(q, live_only=True)
            ps = sorted(x for x in q.rglob("*.ps1") if not _skip(x))
            newest: dict[tuple[str, str], tuple[int, Path]] = {}
            plain = []
            for f in ps:
                m = re.match(r"^(?P<stem>.+?)[-_]v(?P<ver>\d{3,4})$", f.stem)
                if m:
                    k = (str(f.parent), m.group("stem"))
                    if k not in newest or int(m.group("ver")) > newest[k][0]:
                        newest[k] = (int(m.group("ver")), f)
                else:
                    plain.append(f)
            got += py + sorted(plain + [v[1] for v in newest.values()])
        elif q.is_file():
            got.append(q)
        else:
            raise FileNotFoundError(f"找不到:{p}(相對路徑先找目前目錄,再找 VIA 根 {VIA})")
    return got


def read_many(paths: list[str]) -> dict:
    """read 動詞本體:一檔=完整骨架卡;一夾=全景一檔一行 + 有問題的檔再展開問題。回 token 帳(誠實:小檔可能是負的)。"""
    files = _expand_read_targets(paths)
    cards = [read_file(f) for f in files]
    src_chars = sum(c["chars"] for c in cards)
    src_cjk = sum(int(c.get("cjk", 0)) for c in cards)          # 批708:CJK 分開算,不然帳少報約三成
    return {"engine": ENGINE_ID, "version": VERSION, "files": len(cards), "cards": cards,
            "issues": sum(len(c["issues"]) for c in cards),
            "src_tokens": max(1, (src_chars - src_cjk) // 4 + src_cjk)}


def render_many(pay: dict, max_defs: int = 400, panorama: bool = False) -> str:
    cards = pay["cards"]
    if not panorama:
        body = "\n\n".join(render_card(c, max_defs) for c in cards)
    else:
        rows = [f"## 全景代讀 · {len(cards)} 檔 · {pay['issues']} 問題(一檔一行;要看某檔再 read 那一檔)"]
        for c in sorted(cards, key=lambda c: (-sum(i["cls"] in _READ_SEVERE for i in c["issues"]), -len(c["issues"]), c["path"])):
            try:
                shown = str(Path(c["path"]).relative_to(VIA))
            except ValueError:
                shown = c["path"]
            cls: dict[str, int] = {}
            for it in c["issues"]:
                cls[it["cls"]] = cls.get(it["cls"], 0) + 1
            tag = " ".join(f"{k}{v}" for k, v in sorted(cls.items())) or "-"
            rows.append(f"  {c['lines']:>6} 行 {len(c['defs']):>4} 定義  問題[{tag}]  {shown}")
        body = "\n".join(rows)
    card_tok = _tok(len(body), body)
    saved = 100.0 * (1 - card_tok / pay["src_tokens"]) if pay["src_tokens"] else 0.0
    return body + f"\n[token 帳] 原檔≈{pay['src_tokens']} · 骨架卡≈{card_tok} · 省 {saved:.1f}%(ASCII≈4 字元/token · CJK≈1 字元/token;負數照報不修飾)"


def slice_def(path: str, name: str) -> dict:
    """只回一個定義的原始碼(帶行號)。名字可寫 `Class.method`;同名多個全列(DUPDEF 時兩個都看得到)。"""
    files = _expand_read_targets([path])
    if len(files) != 1:
        raise ValueError("slice 只吃單一檔案")
    f = files[0]
    src = f.read_text(encoding="utf-8-sig", errors="replace")
    lines = src.splitlines()
    hits: list[tuple[int, int]] = []
    if f.suffix.lower() == ".py":
        tree = ast.parse(src, filename=str(f))
        for d in _outline_py(tree):
            if d["name"] == name or ("." not in name and d["name"].split(".")[-1] == name):
                hits.append((d["line"], d["end"]))
    elif f.suffix.lower() in (".ps1", ".psm1"):
        rows, _ = _read_ps1(src)
        hits = [(d["line"], d["end"]) for d in rows if d["name"].lower() == name.lower()]
    else:
        raise ValueError(f"slice 只支援 .py / .ps1(收到 {f.suffix})")
    # 裝飾器一起帶(它是定義的一部分)
    segs = []
    for a, b in hits:
        while a > 1 and lines[a - 2].lstrip().startswith("@"):
            a -= 1
        segs.append({"line": a, "end": b, "text": "\n".join(f"{i:>6}\t{lines[i - 1]}" for i in range(a, b + 1))})
    return {"path": str(f), "name": name, "hits": segs, "src_tokens": _tok(len(src), src),
            "slice_tokens": _tok(0, "".join(s["text"] for s in segs))}


def selftest() -> int:
    fails = []
    total = [0]

    def chk(name, cond, note=""):
        total[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        T = Path(td)
        (T / "functional modules" / "VDF" / "engine").mkdir(parents=True)
        (T / "references" / "intake").mkdir(parents=True)
        good = T / "functional modules" / "VDF" / "engine" / "VDF_ENG999_Good_v0100.py"
        good.write_text('"""doc."""\nfrom __future__ import annotations\nimport json\n\n\ndef main():\n    return 0\n', encoding="utf-8")
        bad = T / "functional modules" / "VDF" / "engine" / "VDF_ENG998_Hard_v0100.py"
        bad.write_text('"""doc."""\nimport polars as pl\nimport subprocess, sys, argparse\nfrom pathlib import Path\n\n\ndef go():\n    subprocess.run([sys.executable, str(Path("functional modules/VRN/x.py"))])\n\n\ndef main() -> int:\n    p = argparse.ArgumentParser()\n    p.add_argument("verb", choices=("selftest", "status"))\n    args = parser.parse_args()\n    return 0\n', encoding="utf-8")
        pin = T / "functional modules" / "VDF" / "engine" / "VDF_ENG997_Pin_v0100.py"
        pin.write_text('"""說明文字提到 CGC_MDL149_X_v0100.py 不算違律。"""\nENGINE_PATH = "CGC_MDL157_VIAUniqueEntryControl_v0100.py"\nNOTE = "報告裡寫 VDF_ENG086_QuantGuardOneBridge_v0100.py 只是說明"\nimport talib\n', encoding="utf-8")
        intake = T / "references" / "intake" / "收容件_v0100.py"
        intake.write_text("import polars\n", encoding="utf-8")
        syn = T / "functional modules" / "VDF" / "engine" / "VDF_ENG996_Syn_v0100.py"
        syn.write_text("def broken(:\n    pass\n", encoding="utf-8")

        i_good = audit_source(good, good.read_text(encoding="utf-8"), "functional modules/VDF/engine/VDF_ENG999_Good_v0100.py")
        i_bad = audit_source(bad, bad.read_text(encoding="utf-8"), "functional modules/VDF/engine/VDF_ENG998_Hard_v0100.py")
        i_pin = audit_source(pin, pin.read_text(encoding="utf-8"), "functional modules/VDF/engine/VDF_ENG997_Pin_v0100.py")
        i_syn = audit_source(syn, syn.read_text(encoding="utf-8"), "functional modules/VDF/engine/VDF_ENG996_Syn_v0100.py")
        cls = lambda L: {x["cls"] for x in L}

        chk("① 缺加速器橋/網路工具橋(VDF 引擎)逐檔定位", cls(i_good) == {"ACCEL", "NET"}, str(sorted(cls(i_good))))
        chk("② AST 精準:模組頂硬相依重庫(polars)帶行號", any(x["cls"] == "HARDIMP" and x["line"] == 2 and x["how"] == "ast" for x in i_bad),
            str([(x['cls'], x['line']) for x in i_bad]))
        chk("③ AST 精準:sys.executable 派**別支引擎**才報(家族境律 L51);自跑自己不報",
            any(x["cls"] == "SYSEXE" and x["how"] == "ast" for x in i_bad)
            and not any(x["cls"] == "SYSEXE" for x in audit_source(good, '"""d."""\nimport subprocess, sys\nsubprocess.run([sys.executable, "-c", "print(1)"])\n', "functional modules/VDF/engine/z_v0100.py")))
        chk("④ 彈性定位:argparse 有 selftest 位置動詞但不吃 --selftest(L53)", any(x["cls"] == "VERB" for x in i_bad))
        chk("⑤ AST:釘死版號**當路徑用**才報(L54)· 說明字串/docstring 不報(避免假紅)· TA-Lib 活動接線(L50)",
            cls(i_pin) >= {"PINVER", "TALIB"} and len([x for x in i_pin if x["cls"] == "PINVER"]) == 1,
            str(sorted(cls(i_pin))) + f" · PINVER {len([x for x in i_pin if x['cls'] == 'PINVER'])} 件(只有 ENGINE_PATH 那行)")
        chk("⑥ 語法錯誠實報 SYNTAX 不猜改", cls(i_syn) == {"ACCEL", "NET", "SYNTAX"} or "SYNTAX" in cls(i_syn), str(sorted(cls(i_syn))))
        chk("⑦ 收容件/退役夾/正典 SSOT 零觸碰(SKIP 名單;READ_ONLY 正本連加速器橋都不插)",
            _skip(intake) and _skip(T / "__pycache__" / "x.py") and not _skip(good)
            and _skip(Path("/x/supportive modules/ssot/VIA_Financial_Institution_SSOT_v0100.py"))
            and _skip(Path("/x/VIA_RetiredEngines/y.py")))

        g0 = good.read_text(encoding="utf-8")
        sv = globals()["VIA"]
        globals()["VIA"] = T
        try:
            r1 = fix_one("functional modules/VDF/engine/VDF_ENG999_Good_v0100.py", {"ACCEL", "NET"}, apply=True)
            after = good.read_text(encoding="utf-8")
            r2 = fix_one("functional modules/VDF/engine/VDF_ENG999_Good_v0100.py", {"ACCEL", "NET"}, apply=True)
            r3 = fix_one("functional modules/VDF/engine/VDF_ENG996_Syn_v0100.py", {"ACCEL"}, apply=True)
            rv = fix_one("functional modules/VDF/engine/VDF_ENG998_Hard_v0100.py", {"VERB"}, apply=False)
        finally:
            globals()["VIA"] = sv
        chk("⑧ 修復=純增量:區塊插在 docstring/__future__ 之後,AST 仍可解析,原邏輯字面不動",
            set(r1["applied"]) == {"ACCEL", "NET"} and "[VIA:ACCEL-BRIDGE" in after and "[VIA:NET-BRIDGE" in after
            and "def main():" in after and ast.parse(after) is not None and len(after) > len(g0))
        chk("⑨ 冪等:同檔再修一次=零套用(不重複插塊)", r2["applied"] == [] and good.read_text(encoding="utf-8") == after)
        chk("⑩ 語法壞檔不動(原檔語法錯=拒修,誠實回因由)", r3["ok"] is False and "語法錯" in r3["why"] and syn.read_text(encoding="utf-8") == "def broken(:\n    pass\n")
        chk("⑪ 動詞等價轉換只在 main/parse_args 形狀吻合時做(不猜改)", "VERB" in rv["applied"] or any("VERB" in x for x in rv["skipped"]), str(rv))

    with tempfile.TemporaryDirectory() as td2:
        T2 = Path(td2)
        (T2 / "functional modules" / "VDF" / "engine").mkdir(parents=True)
        selfrun = T2 / "functional modules" / "VDF" / "engine" / "VDF_ENG995_Self_v0100.py"
        selfrun.write_text('"""d."""\nimport subprocess, sys\nfrom pathlib import Path\n\n\ndef go():\n    subprocess.run([sys.executable, str(Path(__file__).resolve()), "--probe-one"])\n', encoding="utf-8")
        fixt = T2 / "functional modules" / "VDF" / "engine" / "VDF_ENG994_Fix_v0100.py"
        fixt.write_text('"""d."""\nfrom pathlib import Path\nREAL_PATH = Path("VDF_ENG001_Real_v0100.py")\n\n\ndef _probe_env(tmp):\n    d = tmp / "V"\n    (d / "Register-VIA-Commands-v0174.ps1").write_text("x")\n    return d\n\n\ndef selftest():\n    P = Path("X_ENG001_A_v0100.py")\n    chk("x", P.exists())\n    return 0\n', encoding="utf-8")
        i_self = audit_source(selfrun, selfrun.read_text(encoding="utf-8"), "functional modules/VDF/engine/VDF_ENG995_Self_v0100.py")
        i_fix = audit_source(fixt, fixt.read_text(encoding="utf-8"), "functional modules/VDF/engine/VDF_ENG994_Fix_v0100.py")
    chk("⑮ 批536 判準精準化反例:自己跑自己≠跨家族派送(SYSEXE 0)· 自測段/探針函式/夾具字串≠釘死版號(只留正式那一個)· 候選夾/打包副本不是活樹",
        not any(x["cls"] == "SYSEXE" for x in i_self)
        and len([x for x in i_fix if x["cls"] == "PINVER"]) == 1
        and _skip(Path("/x/functional modules/VDF/engine/candidates/z.py")) is False
        and all(k in Path(__file__).read_text(encoding="utf-8") for k in ("_NONLIVE_DIR", "self_run")),
        f"(自跑 SYSEXE {len([x for x in i_self if x['cls'] == 'SYSEXE'])} · 夾具檔 PINVER {len([x for x in i_fix if x['cls'] == 'PINVER'])})")
    a, b, cc, dd = judge(0, "[計] OK 9"), judge(3, "=== ABSENT 本境無 polars ==="), judge(1, "Traceback\nModuleNotFoundError: No module named 'x'"), judge(1, "AssertionError")
    chk("⑫ 誠實四態(與 CGC157 同律 L52):GREEN/ABSENT/ABSENT(訊息)/RED",
        a[0] == "GREEN" and b[0] == "ABSENT" and cc[0] == "ABSENT" and dd[0] == "RED")
    canon = md5_canon_dirs()
    fam = VIA / "supportive modules" / "VIA_Central_Governance" / "VIA_CentralGovernanceFamily_b514"
    chk("⑯ 批538 md5 冊管的夾零觸碰(規則不是夾名清單:夾內有帶 md5 的 *MANIFEST*.json 就受保護)· 中央治理家族 b514 在保護名內 · 受保護的檔不進覆蓋率分母(免生判錯的紅燈 L57)",
        len(canon) >= 5 and str(fam) in canon and _skip(fam / "VIA_CentralGovernanceConsole.py")
        and all(not _skip(f) for f in [VIA / "supportive modules" / "registry" / Path(__file__).name]),
        f"(md5 冊管夾 {len(canon)} 個)")
    chk("⑰ 批538 活樹判準與清掃器同一把尺(L30/L55):_output 建置產出 · _superseded 讓位 · 20260804 日期夾 · *_20260507_100922 時戳夾 都不算活樹;兩個中央稽核器不再對同一棵樹講不同的話",
        _nonlive_part(Path("functional modules/VAP/x/_output/VAP_V8_MASTER_20260507_233550/a.py"))
        and _nonlive_part(Path("functional modules/VRN/20260804/VRN_MDL001_Converter.py"))
        and _nonlive_part(Path("functional modules/VRN/_superseded/20260804/x.py"))
        and not _nonlive_part(Path("functional modules/VRN/VRN_ENG086_FirstPageLogicBridge_v0102.py")))
    _scan_ok = {"issues": 0, "by_class": {}}
    _scan_bad = {"issues": 3, "by_class": {"ACCEL": 3}}
    _cov_ok, _cov_bad = {"accel_pct": 100.0, "net_pct": 100.0}, {"accel_pct": 97.2, "net_pct": 100.0}
    v_ok = _verify_one({"kind": "class_zero", "cls": "ACCEL"}, _scan_ok, _cov_ok)
    v_re = _verify_one({"kind": "class_zero", "cls": "ACCEL"}, _scan_bad, _cov_ok)
    v_cv = _verify_one({"kind": "coverage_pct", "field": "accel_pct", "expect": 100.0}, _scan_ok, _cov_bad)
    v_ab = _verify_one({"kind": "coverage_pct", "field": "nope_pct", "expect": 100.0}, _scan_ok, _cov_ok)
    v_no = _verify_one({"kind": "tail_contains", "dir": "supportive modules/registry", "glob": "ZZZ_NOPE_v*.py", "markers": ["x"]}, _scan_ok, _cov_ok)
    v_tc = _verify_one({"kind": "tail_contains", "dir": "supportive modules/registry",
                        "glob": "CGC_MDL158_VIAPanoramaAuditRepair_v*.py", "markers": ["fixed_ledger"]}, _scan_ok, _cov_ok)
    v_ab2 = _verify_one({"kind": "tail_contains", "dir": ".", "glob": "VIA_SYSTEM_MANAGER_v*.py",
                         "markers": ["TASK_FORMAL_NAMES"], "markers_absent": ['"talib_probe":']}, _scan_ok, _cov_ok)
    chk("⑭ 批537 已修冊複驗三態:冊說修好且活樹仍為 0=GREEN · 活樹又量到=RED(回歸)· 覆蓋率退步=RED · 量不了(欄不在/尾版不在)=ABSENT 不當綠 · 尾版憑據齊=GREEN · 退役件在尾版復活=RED",
        v_ok[0] == "GREEN" and v_re[0] == "RED" and v_cv[0] == "RED" and v_ab[0] == "ABSENT" and v_no[0] == "ABSENT"
        and v_tc[0] == "GREEN" and v_ab2[0] == "GREEN",
        f"({v_ok[0]} {v_re[0]} {v_cv[0]} {v_ab[0]} {v_no[0]} {v_tc[0]} 退役件未復活={v_ab2[0]})")
    fl_live = fixed_ledger(_scan_ok, _cov_ok)
    tri = issue_triage({"issues": 129, "by_class": {"VERB": 6, "HARDIMP": 100, "PINVER": 23}})
    _dummy = {"triage": tri, "fixed": fl_live, "tests": {"tally": {"GREEN": 17}, "rows": [0] * 17}, "fix": {"applied_by_class": {}}}
    line = summary_line(_dummy)
    chk("⑮a 批537 摘要講得清楚:問題按 L56 三態拆(ACCEL/NET 可同時 · VERB 順序 · HARDIMP/PINVER 待令)· 真 RED 單列 · 已修冊與實測同句;四處(主控台/頁首/TAB①/MD)同一句",
        tri["parallel"] == 0 and tri["sequential"] == 6 and tri["report_only"] == 123 and tri["red"] == 0 and tri["total"] == 129
        and "可同時修 0" in line and "順序修 6" in line and "只報位置待令 123" in line and "真 RED 0" in line
        and "已修冊" in line and "實測 17/17 綠" in line, f"({line[:96]})")
    chk("⑮b 批537 已修冊在位且本器是它的擁有者(冊不在=ABSENT 誠實,不編)",
        FIXED_SSOT.is_file() and fl_live["state"] in ("GREEN", "RED") and len(fl_live["rows"]) >= 5,
        f"({FIXED_SSOT.name} · {fl_live.get('why','')[:70]})")
    src = Path(__file__).read_text(encoding="utf-8").split("\ndef selftest() -> int:")[0]   # 批536:唯一切點(文件字串裡也寫得到 def selftest)
    chk("⑬a 一名一主(L30):本器只寫 VIA_Reports/panorama_audit;不碰 CGC_MDL135/CGC_MDL149 L19 閘的 VIA_Reports/panorama",
        '"panorama_audit"' in src and '"VIA_Reports" / "panorama"\n' not in src and "PANORAMA_AUDIT_latest" in src)
    chk("⑬ 律:零網路 · 不代裝 · 家族境走匯流排 · 25 加速器名冊只讀 CGC156",
        all(("import " + k) not in src for k in ("requests", "httpx", "urllib")) and "pip install" not in src
        and "_bus_python" in src and "VIA_ACCELERATOR_CONTROL_latest.json" in src)
    # ── 批658 ⑱:正典 U/I TEMPLATE 免修名冊(批647 裁定)——量得到、修不到
    _rel_ui = "VIA_HTML_UI/engines/via_ui_engine.py"
    _rel_ok = "functional modules/VRN/VRN_ENG085_MarkdownRestore_v0106.py"
    with tempfile.TemporaryDirectory() as td2:
        T2 = Path(td2)
        _f = T2 / "x.py"
        _f.write_text('"""doc."""\nimport json\n', encoding="utf-8")
        _i_ui = audit_source(_f, _f.read_text(encoding="utf-8"), _rel_ui)
        _i_ok = audit_source(_f, _f.read_text(encoding="utf-8"), _rel_ok)
    chk("⑱ 批658 正典 TEMPLATE 免修名冊:VIA_HTML_UI 的缺橋**照樣量到**(位置看得見)但每筆蓋豁免章;"
        "非名冊件不蓋;名冊逐條附「為什麼不得改」(L87 豁免必附理由)",
        len(_i_ui) >= 1 and all(x.get("exempt") for x in _i_ui)
        and len(_i_ok) >= 1 and not any(x.get("exempt") for x in _i_ok)
        and template_exempt("VIA_HTML_UI/x.py") and template_exempt("supportive modules/VIA_Central_Governance/a.py")
        and template_exempt("new modules engines/x/a.py") and not template_exempt("functional modules/VRN/VRN_ENG085_x_v0100.py")
        and all(str(w).strip() for _, w in _EXEMPT_ROSTER) and len(_EXEMPT_ROSTER) >= 20,
        f"(名冊 {len(_EXEMPT_ROSTER)} 條 · 出處 {_EXEMPT_SRC} · 蓋章 {sum(1 for x in _i_ui if x.get('exempt'))}/{len(_i_ui)})")
    _fx_ui = fix_one(_rel_ui, {"ACCEL"}, apply=True)          # 帶 --apply 也不准寫(唯一出口硬閘)
    _plan = fix({"ACCEL"}, apply=False, scan_rows=[
        {"file": _rel_ui, "cls": "ACCEL", "exempt": _EXEMPT_TEMPLATE[0][1]},
        {"file": _rel_ui, "cls": "VERB"},
    ])
    chk("⑲ 批658 閘擺在**唯一寫檔出口** fix_one(LL289):名冊件即使帶 --apply 也 applied 0 且講得出理由;"
        "fix() 的計畫也先濾掉(乾跑不會說「要修 22 件」);計畫另記 exempt_files",
        _fx_ui["applied"] == [] and _fx_ui["ok"] and "豁免不修" in _fx_ui["why"]
        and _plan["parallel_files"] == 0 and _plan["sequential_files"] == 0 and _plan["exempt_files"] == 1,
        f"(applied {_fx_ui['applied']} · 計畫 平行{_plan['parallel_files']}/順序{_plan['sequential_files']}/豁免{_plan['exempt_files']})")
    _saved = globals()["_EXEMPT_ROSTER"]              # ⑳ 反向對照:名冊清空,同一份夾具必須改判為「會動到」
    try:
        globals()["_EXEMPT_ROSTER"] = ()
        _neg_tag = audit_source(Path(__file__), '"""d."""\nimport json\n', _rel_ui)
        _neg_plan = fix({"ACCEL"}, apply=False, scan_rows=[{"file": _rel_ui, "cls": "ACCEL"}])
    finally:
        globals()["_EXEMPT_ROSTER"] = _saved
    chk("⑳ 批658 反向對照(判準改動一律附反例):把免修名冊清空後,同一份夾具**必須**改判成會蓋不到章、"
        "且進得了修復計畫——證明這道閘是真的在咬,不是擺著好看",
        not any(x.get("exempt") for x in _neg_tag) and _neg_plan["parallel_files"] == 1
        and _neg_plan["exempt_files"] == 0 and template_exempt(_rel_ui),
        f"(清空後 平行{_neg_plan['parallel_files']} · 蓋章 {sum(1 for x in _neg_tag if x.get('exempt'))};還原後名冊 {len(_EXEMPT_ROSTER)} 條)")
    _tri_ex = issue_triage({"issues": 135, "by_class": {"ACCEL": 22, "VERB": 8, "HARDIMP": 80, "PINVER": 24, "SYSEXE": 1},
                            "by_class_exempt": {"ACCEL": 22, "VERB": 3}})
    chk("㉑ 批658 誠實分母(L57):豁免件**不從總數消失**——135 還是 135,只是「可同時修」從 22 降到 0、"
        "「順序修」扣掉名冊內的 3,另立「正典不得改 25」一欄;掃進地毯下變 0 才是假綠",
        _tri_ex["total"] == 135 and _tri_ex["parallel"] == 0 and _tri_ex["sequential"] == 5
        and _tri_ex["exempt"] == 25 and "正典不得改 25" in summary_line({"triage": _tri_ex}),
        f"(可同時修 {_tri_ex['parallel']} · 順序修 {_tri_ex['sequential']} · 不得改 {_tri_ex['exempt']} / 總 {_tri_ex['total']})")
    chk("㉒ 批658 四把掃描器同一把尺(L30):免修名冊**不抄第二份**,直接讀 CGC_MDL156 尾版的 "
        "`_ACCEL_EXEMPT`+`_TREE_EXEMPT`(ast.literal_eval,不執行它);MDL156 收容件家族/未納管暫存區"
        "/批647 TEMPLATE 三條都吃得到;出處寫進報告,讀不到就誠實退回內建底線",
        _exempt_same_as_mdl156() and "CGC_MDL156" in _EXEMPT_SRC and len(_EXEMPT_ROSTER) > len(_EXEMPT_TEMPLATE)
        and all(template_exempt(x) for x in ("VIA_Central_Governance/a.py", "new modules engines/a.py",
                                             "x/_patches/a.py", "VIA_HTML_UI/a.py"))
        and _load_exempt_roster.__doc__ and "一個出處" in _load_exempt_roster.__doc__,
        f"(名冊 {len(_EXEMPT_ROSTER)} 條 · 內建底線 {len(_EXEMPT_TEMPLATE)} 條 · 出處 {_EXEMPT_SRC})")
    # ── 批658 ㉓:跨行的 glob 後備不是釘死版號(L93 先疑尺不疑樹 · 判準改動一律附反例)
    _pin_src = ("\"\"\"d.\"\"\"\n"
                "from pathlib import Path\n"
                "D = Path('.')\n"
                "CAND = (sorted(D.glob('CGC_MDL148_EngineBus_v*.py'))\n"
                "        or [D / 'CGC_MDL148_EngineBus_v0100.py'])[-1]\n"
                "HARD = Path('supportive modules') / 'CGC_MDL999_Hard_v0100.py'\n")
    _i_pin2 = audit_source(Path(__file__), _pin_src, "functional modules/VDF/engine/VDF_ENG995_Pin_v0100.py")
    _pv = [x for x in _i_pin2 if x["cls"] == "PINVER"]
    chk("㉓ 批658 跨行的尾版後備不報紅(L93):`sorted(D.glob('X_v*.py')) or [D/'X_v0100.py']` 換行寫時,"
        "那個 _v0100 是 glob 落空的後備、不是釘死版號(舊尺只看同一行有沒有 glob,跨行就報假紅);"
        "**同一份夾具裡真的釘死那一行仍要照報**——不然就是把尺放寬,不是把尺修對",
        len(_pv) == 1 and "CGC_MDL999_Hard_v0100.py" in _pv[0]["detail"],
        f"(PINVER {len(_pv)} 件 · {(_pv[0]['detail'][:52] if _pv else '無')})")
    # ── 批658 ㉔:已修冊那條「該修的都修完了」不能拿掃描總數去判
    _sc = {"issues": 22, "by_class": {"ACCEL": 22}, "by_class_exempt": {"ACCEL": 22}}
    _sc_half = {"issues": 22, "by_class": {"ACCEL": 22}, "by_class_exempt": {"ACCEL": 20}}
    _v_ex = _verify_one({"kind": "class_zero", "cls": "ACCEL"}, _sc, {})
    _v_half = _verify_one({"kind": "class_zero", "cls": "ACCEL"}, _sc_half, {})
    _v_none = _verify_one({"kind": "class_zero", "cls": "ACCEL"}, {"issues": 22, "by_class": {"ACCEL": 22}}, {})
    chk("㉔ 批658 已修冊 class_zero 改判「還該修而沒修的 = 0」,不是「掃描總數 = 0」:22 件全在免修名冊=GREEN "
        "且說明講出扣了幾件;只免 20 件、還剩 2 件沒修=**照樣 RED**;名冊沒收錄=RED。"
        "批647 之後 F535-ACCEL 就一直亮著一盞永遠修不掉的紅燈,沒人讀它",
        _v_ex[0] == "GREEN" and "不得改,不計入" in _v_ex[1] and _v_half[0] == "RED" and _v_none[0] == "RED",
        f"(全免 {_v_ex[0]} · 剩 2 件 {_v_half[0]} · 沒名冊 {_v_none[0]})")
    _cov = coverage()
    chk("㉕ 批658 覆蓋率分母同扣名冊件(與 CGC_MDL156 第 367 行同判準 L30):扣後 accel_pct 與未扣的 "
        "accel_pct_raw **兩個數字都留在報告裡**,扣了幾件也寫明——只留一個扣過的數字,那是把分母做漂亮",
        _cov["accel_pct"] >= _cov["accel_pct_raw"] and _cov["py_all"] > _cov["py_total"]
        and _cov["accel_exempt"] == _cov["py_all"] - _cov["py_total"] and "exempt_source" in _cov,
        f"(扣後 {_cov['accel_pct']}% / {_cov['py_total']} 件 · 未扣 {_cov['accel_pct_raw']}% / {_cov['py_all']} 件 · 扣 {_cov['accel_exempt']} 件)")
    # ── 批707 ㉖–㉚:AI 代讀(read / slice)——唯讀、不執行、只回骨架/最小片段
    with tempfile.TemporaryDirectory() as td2:
        T2 = Path(td2)
        mark = T2 / "EXECUTED.flag"
        pyf = T2 / "sample_mod.py"
        pyf.write_text(
            '"""樣品模組。"""\nimport json\nfrom pathlib import Path\n'
            f'Path({str(mark)!r}).write_text("x")\n'
            'class Box:\n    """盒子。"""\n    @property\n    def v(self):\n        return 1\n'
            '    @v.setter\n    def v(self, x):\n        pass\n'
            '    def put(self, item, bag=[]):\n        bag.append(item)\n        return bag\n\n'
            'def load(p: str) -> dict:\n    """讀檔。"""\n    try:\n        return json.loads(Path(p).read_text())\n'
            '    except:\n        pass\n    return {}\n    print("never")\n\n'
            'def load(p):\n    try:\n        return 1\n    except ValueError:\n        pass\n',
            encoding="utf-8")
        before = (pyf.read_bytes(), pyf.stat().st_mtime_ns)
        card = read_file(pyf)
        cls = sorted({i["cls"] for i in card["issues"]})
        names = [d["name"] for d in card["defs"]]
        chk("㉖ 批707 read 骨架卡:定義樹含 class/方法/行號/簽章/首行說明;通用五類 DUPDEF/UNREACH/BAREEXC/SWALLOW/MUTDEF 全抓到,"
            "property setter 刻意同名**不**算 DUPDEF(反例)",
            {"Box", "Box.v", "Box.put", "load"} <= set(names)
            and cls == ["BAREEXC", "DUPDEF", "MUTDEF", "SWALLOW", "UNREACH"]
            and sum(i["cls"] == "DUPDEF" for i in card["issues"]) == 1
            and any(d["name"] == "load" and "-> dict" in d["sig"] and d["doc"] == "讀檔。" for d in card["defs"]),
            f"(類 {cls} · 定義 {len(names)})")
        chk("㉗ 批707 read 唯讀且**不執行**被讀的檔:樣品頂層會寫旗標檔,讀完旗標不得出現;位元組與 mtime 不變",
            not mark.exists() and (pyf.read_bytes(), pyf.stat().st_mtime_ns) == before,
            f"(旗標 {'出現' if mark.exists() else '無'})")
        sl = slice_def(str(pyf), "Box.put")
        sl2 = slice_def(str(pyf), "load")
        sl3 = slice_def(str(pyf), "nope")
        sl4 = slice_def(str(pyf), "v")
        chk("㉘ 批707 slice 只回那一個定義(帶行號);Class.method 可指;同名兩個都列(DUPDEF 時兩個都看得到);"
            "裝飾器一起帶;查無=空,不猜",
            len(sl["hits"]) == 1 and "def put" in sl["hits"][0]["text"] and "class Box" not in sl["hits"][0]["text"]
            and len(sl2["hits"]) == 2 and not sl3["hits"] and len(sl4["hits"]) == 2 and "@property" in sl4["hits"][0]["text"],
            f"(put {len(sl['hits'])} · load {len(sl2['hits'])} · nope {len(sl3['hits'])} · v {len(sl4['hits'])})")
        psf = T2 / "Reg-v0100.ps1"
        psf.write_text('function global:via-a {\n    """說明"""\n    Write-Host "{"\n}\nfunction via-b { 1 }\n'
                       'function global:VIA-A {\n    param($x)\n    2\n}\n', encoding="utf-8")
        pc = read_file(psf)
        pcls = sorted(i["cls"] for i in pc["issues"])
        ps_sl = slice_def(str(psf), "via-b")
        psf2 = T2 / "Gen-v0100.ps1"
        psf2.write_text("function Outer-A {\n    function Test-Prot { 1 }\n    Test-Prot\n}\nfunction Outer-B {\n    function Test-Prot { 2 }\n}\n"
                        "$tpl = @'\n<script>\nfunction render(){ return 1 }\nfunction render(){ return 2 }\n</script>\n'@\n"
                        "$gen = @\"\nfunction EnsureDir { 1 }\n\"@\nfunction EnsureDir { 2 }\n", encoding="utf-8")
        pc2 = read_file(psf2)
        chk("㉝ 批734 PowerShell 誤報反例:here-string 裡的 JS/模板函式不算、不同父函式裡的同名區域函式不算"
            "(首跑 14 件 PSDUPFN 全是這兩型);同一父函式內真重複照報",
            not pc2["issues"] and {d["name"] for d in pc2["defs"]} == {"Outer-A", "Outer-B", "Test-Prot", "EnsureDir"},
            f"(問題 {[i['detail'] for i in pc2['issues']]})")
        chk("㉙ 批707 PowerShell:同名 function(不分大小寫)=PSDUPFN;函式開頭三引號字串=PSDOCSTR(LL182);"
            "字串裡的大括號不打亂收尾;slice 取得到",
            pcls == ["PSDOCSTR", "PSDUPFN"] and [d["end"] for d in pc["defs"]] == [4, 5, 9]
            and len(ps_sl["hits"]) == 1 and "via-b" in ps_sl["hits"][0]["text"],
            f"(類 {pcls} · 收尾 {[d['end'] for d in pc['defs']]})")
        gov = audit_source(pyf, pyf.read_text(encoding="utf-8"), "functional modules/VDF/engine/X.py")
        chk("㉚ 批707 通用五類**不進 scan 的帳**(audit_source 不回 READ_CHECKS 類=scan 數字與歷批已修冊零變動);"
            "VIA 樹外的檔不背 VIA 治理七類(read 樹外檔不出 ACCEL/NET)",
            not any(i["cls"] in READ_CHECKS for i in gov) and card["in_via"] is False
            and not any(i["cls"] in CATEGORIES for i in card["issues"]),
            f"(scan 類 {sorted({i['cls'] for i in gov})})")
    # ── 批708 ㉛ token 尺:釘**絕對值**,不是比值 ───────────────────
    _zh, _en = "中" * 100, "a" * 100
    _t_zh, _t_en = _tok(0, _zh), _tok(0, _en)
    _old_zh = max(1, len(_zh) // 4)          # v0105 的舊尺:一律 4 字元/token
    chk("㉛ 批708 **token 尺分 ASCII/CJK**:100 個中文字 ≉ 100 個英文字元。v0105 一律 4 字元/token,"
        "把中文的帳報成約四分之一;實測 CGC_MDL147 舊尺 8908 → 新尺 13375(**少報 33%**)。"
        "**為什麼以前沒被抓到**:read 印的是**省下的百分比**,原檔與骨架卡的 CJK 佔比相近,"
        "分子分母一起偏低,比值幾乎不動(95.0% vs 94.9%)——**只檢比值的檢永遠照不出這個缺陷**,"
        "所以本檢釘絕對值。**負控**:舊尺拿來跑同一條斷言必須當場破",
        _t_zh == 100 and _t_en == 25 and _old_zh == 25 and _t_zh != _old_zh,
        f"(中文 100 字→{_t_zh} token · 英文 100 字元→{_t_en} · 舊尺中文→{_old_zh}(必須 ≠ {_t_zh}))")

    # ── 批708 ㉜㉝ digest:跑測日誌摘要 ────────────────────────────
    _LOG = ("  [OK  ] 甲站 · 1.0s · 好了  (1/4 · 1s)\n"
            "  [FAIL] 乙站 · 0.5s ·   [FAIL] ③ 站自己的輸出  (2/4 · 2s)\n"
            "  [FAIL] 丙站 · 0.4s · 平行時炸了  (3/4 · 3s)\n"
            "  [SKIP] 丁站 · 0.1s · 環境缺件(誠實): 沒裝\n"
            "  [OK  ] 丙站 · 0.4s · 平行敗→序跑 轉綠\n"
            "  [計] OK 2 · FAIL 1 · SKIP 1 · TIMEOUT 0(誠實多態)· 5s\n")
    _d = digest_log(_LOG)
    _neg = digest_log(_LOG.replace("  [OK  ] 丙站 · 0.4s · 平行敗→序跑 轉綠\n", ""))
    _nodata = digest_log("  [OK  ] 甲站 · 1.0s · 好了\n")
    chk("㉜ 批708 digest **同一站以最後一列為準**:平行敗→序跑轉綠的不算紅,**但一定要列出來**"
        "(不列=把紅洗掉;列成 FAIL=假紅,兩個都不行,所以它自成一態)。"
        "**負控**:把那一列轉綠的拿掉,真 FAIL 必須當場從 1 變 2",
        [n for n, _ in _d["fails"]] == ["乙站"] and [n for n, _ in _d["flipped"]] == ["丙站"]
        and len(_d["skips"]) == 1 and _d["state"] == "RED"
        and sorted(n for n, _ in _neg["fails"]) == ["丙站", "乙站"] and not _neg["flipped"],
        f"(真 FAIL {[n for n, _ in _d['fails']]} · 轉綠 {[n for n, _ in _d['flipped']]}"
        f" · 負控真 FAIL {sorted(n for n, _ in _neg['fails'])})")
    chk("㉝ 批708 digest **只認行首第一個中括號**:站列印的是「站名 · 秒 · 站自己的輸出」,"
        "而站自己的輸出裡常常也有同樣的方括號標記 —— 批707 實錄:我 grep 到 1 行,總表卻寫 0,"
        "多花兩次工具呼叫才查出那是轉綠。**嵌在後面的不是站的判決。**"
        "另:沒有總表行 = 日誌被截斷或還在跑 → **NODATA 不編**",
        _d["rows"] == 4 and _nodata["state"] == "NODATA" and bool(_nodata["why"]),
        f"(站列 {_d['rows']}(必須 4,不是 5)· 無總表→{_nodata['state']})")

    _lock = ("  [LOCKED] 戊站 · 0.2s · DuckDB 鎖撞\n  [SKIP] 己站 · 0.1s · 環境缺件(誠實): x\n"
             "  [計] OK 0 · FAIL 0 · SKIP 1 · 1s\n")
    _clean = "  [OK  ] 甲站 · 1.0s · 好\n  [SKIP] 己站 · 0.1s · 環境缺件(誠實): x\n  [計] OK 1 · FAIL 0 · SKIP 1 · 1s\n"
    _dl, _dc = digest_log(_lock), digest_log(_clean)
    chk("㉞ 批708 **LOCKED/TIMEOUT 既不綠也不紅,摘要就不准下綠紅判**(MIXED,rc5)。"
        "v0106 第一版寫 `RED if fails else GREEN`,一份末列 LOCKED 的日誌當場被判 GREEN ——"
        "那是假綠。**負控**:全是 OK/誠實 SKIP 的那一份必須仍然是 GREEN"
        "(否則就是把閘調成「永遠不綠」,那跟永遠綠一樣沒有判斷力)",
        _dl["state"] == "MIXED" and [n for n, _ in _dl["others"]] == ["戊站"]
        and _dc["state"] == "GREEN" and not _dc["others"],
        f"(鎖撞那份→{_dl['state']} · 乾淨那份→{_dc['state']})")

    print(f"  [計] {total[0]} 檢 OK {total[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def _exempt_same_as_mdl156() -> bool:
    """對照 CGC_MDL156 尾版的 _ACCEL_EXEMPT 理由字串;對照件不在=ABSENT 不當綠(回 False 不編)。"""
    cand = sorted((VIA / "supportive modules" / "registry").glob("CGC_MDL156_VIAAcceleratorControl_v*.py"))
    if not cand:
        return False
    txt = cand[-1].read_text(encoding="utf-8", errors="replace")
    return all(why in txt for _, why in _EXEMPT_TEMPLATE)


# ── 批708 digest:把一份跑測日誌壓成一頁 ──────────────────────────────
#: 操作員令「優化他作為節省 TOKEN 的工具」。read/slice 省的是**讀原始碼**;
#: 我這條迴圈真正的大宗是**讀跑測日誌** —— 全格子一跑 108 KB ≈ 兩萬多 token。
#: 而且土法 `grep '\[FAIL\]'` **會把我帶錯**:批707 實錄——我 grep 到 1 行 FAIL,
#: 總表卻寫 FAIL 0,多花兩次工具呼叫才查出那一站是**平行敗→序跑轉綠**。
#: 省 token 是其次,**不被自己的 grep 誤導**才是主因(判錯的紅燈和假綠一樣傷)。
_ROW = re.compile(r"^\s*\[([^\]]{1,10}?)\s*\]\s*(.+)$")
_TALLY = re.compile(r"OK\s+\d+\s*·\s*FAIL\s+\d+")


def digest_log(text: str) -> dict:
    """跑測日誌 → 一頁摘要(誠實多態;不洗紅、不吞掉轉綠、沒有總表就回 NODATA)。

    判準逐條寫死在這裡,因為**這把尺判錯的代價是我去修一支沒壞的引擎**:
      · 只認**行首第一個**中括號 —— 站列印的是 `[OK  ] 站名 · 1.2s · <站自己的輸出>`,
        而站自己的輸出裡常常也有 `[FAIL] ③ …`。**嵌在後面的不是站的判決。**
      · 同一站出現多列時,**以最後一列為準**(格子的既有機制:平行敗→序跑重跑)。
      · 但轉綠的**一定要列出來**:不列=把紅洗掉;列成 FAIL=假紅。所以它自成一態。
      · 沒有 `[計] … OK n · FAIL n …` 那一行 = 日誌被截斷或還在跑 → **NODATA,不編**。
    """
    rows, order = {}, []
    tally = ""
    for ln in text.replace("\r", "\n").split("\n"):
        m = _ROW.match(ln)
        if not m:
            continue
        st, rest = m.group(1).strip(), m.group(2)
        if st == "計":
            if _TALLY.search(rest):
                tally = rest.strip()
            continue
        if st not in ("OK", "FAIL", "SKIP", "LOCKED", "TIMEOUT", "NODATA", "ABSENT", "GATED"):
            continue
        name = rest.split(" · ")[0].strip()
        why = " · ".join(rest.split(" · ")[2:]).strip() if rest.count(" · ") >= 2 else ""
        if name not in rows:
            rows[name] = []
            order.append(name)
        rows[name].append((st, why))
    fails, flipped, skips, others = [], [], [], []
    for name in order:
        seq = rows[name]
        last, why = seq[-1]
        had_fail = any(s == "FAIL" for s, _ in seq[:-1])
        if last == "FAIL":
            fails.append((name, why))
        elif had_fail:
            flipped.append((name, f"{len(seq)} 次;末列 {last}"))
        elif last == "SKIP":
            skips.append((name, why))
        elif last != "OK":
            others.append((name, last))
    # 批708 自審②:v0106 第一版寫 `"RED" if fails else "GREEN"` —— 於是一份
    #   末列是 LOCKED(鎖撞)的日誌被判 GREEN。**LOCKED/TIMEOUT 是「既不綠也不紅」**,
    #   判它綠就是假綠,判它紅就是假紅;本摘的誠實作法是**不下綠紅判**(rc5 SKIP),
    #   並把那幾站逐站點名要人去看。
    if not tally:
        state = "NODATA"
    elif fails:
        state = "RED"
    elif others:
        state = "MIXED"
    else:
        state = "GREEN"
    return {"state": state, "tally": tally, "rows": len(order),
            "fails": fails, "flipped": flipped, "skips": skips, "others": others,
            "chars": len(text), "cjk": sum(1 for _c in text if _CJK(_c)),
            "why": "" if tally else "日誌裡沒有 [計] 總表行:被截斷或還在跑 —— 不編一個總表出來"}


def render_digest(d: dict) -> str:
    _note = {"MIXED": "(有既不綠也不紅的態 → 本摘不下綠紅判,逐站看)", "NODATA": "", "RED": "", "GREEN": ""}
    out = [f"[摘] {d['state']}{_note.get(d['state'], '')} · 站列 {d['rows']} · 真 FAIL {len(d['fails'])}"
           f" · 平行敗→序跑轉綠 {len(d['flipped'])} · SKIP {len(d['skips'])} · 其他態 {len(d['others'])}"]
    if d["tally"]:
        out.append(f"  總表:{d['tally']}")
    else:
        out.append(f"  NODATA:{d['why']}")
    for tag, items in (("真 FAIL", d["fails"]), ("轉綠(不算紅,但照列)", d["flipped"]),
                       ("SKIP", d["skips"]), ("其他態", d["others"])):
        for n, w in items[:20]:
            out.append(f"  [{tag}] {n}" + (f" · {w[:90]}" if w else ""))
        if len(items) > 20:
            out.append(f"  [{tag}] …另 {len(items) - 20} 筆")
    # 自審(批708):這一行我第一版寫成 `_tok(0, "x" * d["chars"])` ——
    #   用一串 ASCII 的 x 去代表一份**中文滿天飛**的日誌,等於把剛修好的錯尺再犯一次。
    #   已改成帶著日誌自己的 CJK 佔比算。
    src = max(1, (d["chars"] - d["cjk"]) // 4 + d["cjk"]) if d["chars"] else 1
    dig = _tok(0, "\n".join(out))
    out.append(f"[token 帳] 日誌≈{src} · 摘要≈{dig} · 省 {100 * (1 - dig / max(src, 1)):.1f}%")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="VIA 全景稽核修復正主")
    ap.add_argument("verb", nargs="?", choices=("scan", "fix", "tests", "report", "all", "selftest", "read", "slice", "digest"), default="all")
    ap.add_argument("targets", nargs="*", help="read:檔或夾(可多個);slice:檔 名稱;digest:跑測日誌(不給=讀 stdin)")
    ap.add_argument("--max-defs", type=int, default=400)
    ap.add_argument("--full", action="store_true", help="read 夾時也逐檔印完整骨架卡(預設一檔一行)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--open", dest="do_open", action="store_true")
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--json", dest="as_json", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--classes", default="ACCEL,NET,VERB")
    argv = [("selftest" if a == "--selftest" else a) for a in sys.argv[1:]]
    args = ap.parse_args(argv)
    if args.verb == "selftest":
        print(f"=== 全景稽核修復正主({ENGINE_ID} {VERSION})· 自測(零網路;合成夾具;真樹零觸碰)===")
        return selftest()
    if args.verb == "read":                    # 批707:AI 代讀——唯讀,零寫檔,不執行被讀的檔
        if not args.targets:
            print("  [read] 用法:read <檔或夾…> [--json] [--full] [--max-defs N]")
            return 2
        try:
            pay = read_many(args.targets)
        except (FileNotFoundError, OSError) as exc:
            print(f"  [read] ABSENT:{exc}")
            return 3
        if args.as_json:
            print(json.dumps(pay, ensure_ascii=False, indent=1))
        else:
            dirs = any((Path(t).is_dir() or (VIA / t).is_dir()) for t in args.targets)
            print(render_many(pay, args.max_defs, panorama=dirs and not args.full))
        return 0
    if args.verb == "slice":
        if len(args.targets) != 2:
            print("  [slice] 用法:slice <檔> <定義名|Class.method>")
            return 2
        try:
            r = slice_def(args.targets[0], args.targets[1])
        except (FileNotFoundError, OSError, ValueError, SyntaxError) as exc:
            print(f"  [slice] ABSENT:{type(exc).__name__}: {exc}")
            return 3
        if args.as_json:
            print(json.dumps(r, ensure_ascii=False, indent=1))
        elif not r["hits"]:
            print(f"  [slice] NODATA:{r['path']} 裡沒有定義 {r['name']}(先 read 看定義樹)")
            return 3
        else:
            for h in r["hits"]:
                print(f"## {r['path']} · {r['name']} · L{h['line']}-{h['end']}\n{h['text']}")
            print(f"[token 帳] 整檔≈{r['src_tokens']} · 片段≈{r['slice_tokens']}")
        return 0
    if args.verb == "digest":
        if args.targets:
            q = Path(args.targets[0])
            if not q.exists():
                print(f"  [digest] ABSENT:找不到:{q}")
                return 3
            txt = q.read_text(encoding="utf-8", errors="replace")
        else:
            txt = sys.stdin.read()
        d = digest_log(txt)
        print(json.dumps(d, ensure_ascii=False, indent=1) if args.as_json else render_digest(d))
        return {"GREEN": 0, "RED": 1, "NODATA": 2, "MIXED": 5}[d["state"]]
    if args.verb == "scan":
        s = scan(limit=args.limit)
        if args.as_json:
            print(json.dumps(s, ensure_ascii=False, indent=1))
        else:
            print(f"=== 全景掃描 · {s['files_scanned']} 檔 · {s['issues']} 問題 · {s['secs']}s ===")
            _ex = s.get("by_class_exempt") or {}
            for k, v in sorted(s["by_class"].items(), key=lambda x: -x[1]):
                zh, act, fixhow = CATEGORIES.get(k, (k, "", ""))
                e = int(_ex.get(k, 0))               # 批658:標「修」就要真的修得動——名冊內的不得改,
                if act != "GREEN_FIX":               #   那一份要寫在同一行,不能讓人看著「[修] 22」以為跑 fix 就會少 22
                    tag, tail = "報", ""
                elif e >= v:
                    tag, tail = "免", f"(全數依批647 正典 TEMPLATE 不得改:{'/'.join(s.get('exempt_names') or [])})"
                elif e:
                    tag, tail = "修", f"(其中 {e} 件依批647 正典 TEMPLATE 不得改 → 實可修 {v - e})"
                else:
                    tag, tail = "修", ""
                print(f"  [{tag}] {k:<8} {v:>5} · {zh}{tail}")
        return 0
    if args.verb == "fix":
        f = fix(set(args.classes.split(",")), apply=args.apply, workers=args.workers, limit=args.limit)
        print(json.dumps({k: v for k, v in f.items() if k != "rows"}, ensure_ascii=False, indent=1))
        return 0
    if args.verb == "tests":
        t = run_tests(fast=args.fast)
        for r in t["rows"]:
            print(f"  [{r['state']:<7}] {r['system']:<5} {r['name']:<28} rc={r['rc']} · {str(r['why'])[:70]}")
        print(f"  [計] {t['tally']} · 裁決 {t['verdict']} · 中央派送 {t['dispatch'].get('state')}")
        return 0 if t["verdict"] != "RED" else 2
    if args.verb == "report":
        pay = json.loads((OUT / "PANORAMA_AUDIT_latest.json").read_text(encoding="utf-8")) if (OUT / "PANORAMA_AUDIT_latest.json").is_file() else run_all(False, False)
        print(write_report(pay, args.do_open))
        return 0
    pay = run_all(args.apply, args.do_open, args.fast, args.limit)
    print(f"=== 全景稽核修復 · {pay['verdict']} · {pay.get('summary') or summary_line(pay)} ===")
    fl = pay.get("fixed") or {}
    for r in fl.get("rows", []):
        print(f"  [{r['lamp']:<6}] 已修冊 {r['batch']} {str(r['cls']):<16} {str(r['what'])[:52]}")
    if fl.get("regressions"):
        print(f"  [回歸] {fl['regressions']}(冊說修好,現在又量到=真紅燈)")
    print(f"  [頁] {pay['paths']['html']}")
    return 0 if pay["verdict"] != "RED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
