#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_SystemManager v0104 — VDF 子系統管理對接口(側線 2026-09-21;與 VRN_SystemManager 同一份契約)
v0103→v0104(側線 2026-09-23;主線批號由併線的手指定 L25;操作員「更新 VDF」+ 工作站 09-21 實錄):launch 多量四件、全是量不是釘——
  ① **閘二三把尺**:VDF 尾版裡寫死 `VIA_SCRAPE_CONSENT == "YES"` 的引擎逐支量出來(ENG054/056/064…),再從短令冊尾版量出「直呼哪幾個短令會撞到它們」;
     十道(CGC_MDL134)與開機鏈對子行程**自帶** YES 也量出來——所以工作站 NET=YES SCRAPE=OFF 時 via-vdffetch 全綠、via-price/via-chip 卻 FAIL-CLOSED。
     統包 gate_state() 的閘二是「非空即算」(OFF 也算,另報),VRN 爬蟲包要期望 token——三個消費者三把尺,本口只量不裁(掉球)。
  ② **視窗限量**:本視窗帶著 VIA_HIST_LIMIT → 下一次 via-vdffetch 沒打 --limit 也只抓那幾檔(v0104 的啟動器把 --limit 留在視窗;跑完還原的 v0105 是提案、候 L70 許可與 L102 模板章,未出貨——尾版是哪一支、會不會還原都現量)。
  ③ **增量計畫的目錄新鮮度**:委派 VDF_ENG089 v0101 catalog_freshness()(唯一出處 LL316;本口不另算);目錄比庫舊 → 下一步卡先 via-datahome catalog。
  ④ **其他擷取件**:主線批716–724 的 VDF_MDL004 / VDF_ENG092 與本線 v0100 的 MDL002/003/006 在不在、有沒有治理入口 main_governed。
  另:下一步卡把 launch.ps1 寫成 `.\launch.ps1`(PowerShell 不從目前位置載命令,工作站實錄)、抓完先 via-datahome catalog、十道不建調整層/因子庫時講明。
  read_launch(environ=) 可注入環境 → 自測用合成環境,不讀寫任何真同意閘。自測 29 → 31(㉚ 閘二三把尺 + 視窗限量正負控 · ㉛ 目錄新鮮度委派)。其餘一字不動。
v0102→v0103(側線 2026-09-21 d;操作員令「GO 我需要擷取 VDF 的資料,幫我完善到可啟動她」):+ `launch` 啟動就緒(只量不動手)。
  先量(L61):工作站的「啟動 VDF 擷取」正主是 Invoke-VIA-VdfFetch-v*.ps1(批383:自找根 → 倉庫自癒 → 點源短令冊 → 同意閘不覆蓋 →
  家族境 python → 年份旗標 → 20 加速器 + Hydra 哨兵 → CGC_MDL134 十一步十道並行 → 存證),短令 via-vdffetch [年];每日鏈是 via_boot_update.sh(正主)
  與 via_boot_update.ps1(工作站 VIA.ps1 全自動 / launch.ps1 / Deck「boot」)。量到的缺口:.ps1 比 .sh 少 13 步且用裸 python(Z94 只照出兩步);
  容器沒有家族境(duckdb/pandas/pyarrow 不在)= ABSENT;同意閘未開 = GATED。這些都不是本口能代做的:**啟動要的是操作員的手**(閘 L07/L08 · 建境不裝套件),
  本口能做的是把「差什麼」一次量給你看、把下一步的那一行印出來。所以 launch = 八項現量 + 一張下一步卡:
    ① 家族境 python + 必要庫(尺=CGC_MDL137 python_for → CGC_MDL136 resolve_env_python;FAMILY_LIBS[vdf].required;probe_libs 現探,--no-probe 讀上次能跑閘快照)
    ② 同意閘現態(只讀;永不代設)③ 網路工具掛載 ④ 啟動器/短令/鏈在位(Invoke-VIA-VdfFetch · via-vdffetch.cmd · Register 尾版 16 短令 · MDL134 · MDL170 · MDL136)
    ⑤ 開機鏈雙載體同鏈(.sh 正主 vs .ps1;同一把尺抓引擎家族;.ps1 少一步=RED 點名;.ps1 裸 python=STALE)⑥ 上次實跑存證(boot marker/log · 能跑閘 · 獨立鏈 · 十道)⑦ 落點
  燈與 rc:RED 1(啟動器/鏈缺 · 雙載體不同鏈)> ABSENT 3(必要庫不在家族境)> GATED 4(閘未開)> GREEN 0(可啟動);從沒跑過只是紀錄,不擋啟動。
  status/page 也帶一段「啟動就緒」(--no-probe 版,零子行程);連結表 +4 條(兩份開機鏈 · 啟動器 · 十道引擎)讓 sync 看得見鏈被改。
  自測 +㉘(雙載體同鏈:合成負控少一步 → RED 點名;真鏈現量 GREEN)+㉙(啟動就緒只量不動手:燈 ∈ 冊 · rc 表 · 尺 · 閘前後同 · 下一步卡)。其餘一字不動。
v0101→v0102(側線 2026-09-21 c;CGC_MDL164 ⑰ 自我指涉閘照出本口是基線外的 NO_EXCLUDE):橋域的版史掃描(全 VDF .py)把本口自己也算進分母。
  LL133:判定器一律排掉自己的家族——`_SELF_FAMILY` 不進版史分母(尾版列仍由 VCGC 的尺量,本口自己那一列照量、自測 ② 照驗);其餘一字不動。
v0100→v0101(側線 2026-09-21 b;操作員「依你建議執行」→ Register v0242 +via-vdfsys):⑱ 原本寫「Register 短令未登(L70)必須 False」——
  把**當下的暫態**釘成不變量,短令一登冊自測就紅(LL89 的反面:會紅的檢也可以是假的)。改成**量** Register 尾版:七處的 register 旗標必須等於
  冊上有沒有 `function global:via-vdfsys`,登了為 True、沒登為 False,兩種都是誠實。其餘一字不動(v0100 留作版史,尾版律 L04)。

操作員令:「將 session_01RLMQGZLcigd5Bt5aN6J4Ck 關於 VDF 全數接過來 · 建立 VDF_SystemManager 與 VIA 對接 ·
VDF 所有引擎找出來 · 讀取 VIA 政策所有 PY 檔案一定要接加速器 · 所有 VDF 都要加裝網路工具
(VeritasCeleritas.py / VeritasAegisNexus.py)」。

【先量,再造(L61 / LL331)】
  · 那個 session 的 VDF 工作已在主線(批663–679d 的 15 份 B 文 · VDF 獨立鏈 CGC_MDL170 · 六域現況 · 全景批次計畫 ·
    打包就緒閘 · 兩條車道);本口不複製它們,**只指**(L05):records 域由 git 尾註量血脈、docs 量 VDF 文、references/intake 量收容包。
  · 「一定要接加速器」「都要加裝網路工具」——量出來的現況:VDF 195 支 .py 加速器橋 195/195;尾版 86 支網路橋 86/86。
    律已經滿了;本口要做的是**每一跑都量給你看並守住**(bridge 域:尾版少一支就是 RED),不是再裝一次。
  · 本口自己也是 VDF 件:兩座橋(加速器 + 網路)都掛在檔頭;標記的尺用橋掃器的表頭常數 ACCEL_START/NET_START(docstring 提到不算)。
  · 卡書 vs 樹:engine/ 量到 8 支**沒有版號**的 .py(ENG046/047/049/050/051 · MDL002/003/007;L04 尾版律外,VCGC 的尺看不見)——
    其中 5 支只有無版號檔而卡書指著它們(ENG046/049 · MDL002/003/007),本口分開報「無版號」不混進「樹無」(L16);
    另 3 支(ENG047/050/051)旁邊另有尾版檔=疑似舊複本(L05 兩顆頭候裁)。版號要立、複本要清是操作員/主線的事,本口只報。
  · VRN 那扇門(批681/682 VRN_SystemManager v0101)已經立了契約;VDF 這扇門**同形**:一樣的動詞、一樣的六態、
    一樣的 rc 語意、一樣的快照/差異/自審,VCGC 往下讀 VDF 也只走這一扇門。

位置:VIA ─(L20 唯一對接口 VCGC CGC_MDL149)─► **本口** ─► VDF 四庫 + 引擎面 + 橋/工具面 + 交接
  上行(向 VIA 報):九域燈 · 連結表 · 七處自審 · 快照 VIA_Reports/vdf_system/VDF_SYSTEM_latest.json
                  (VCGC v0120 起 vdf_system() 經本口 collect();對接口缺席=ABSENT 誠實,不退回舊路)
  下行(管 VDF):政策 policy (律/lessons 的 VDF 子集 + 釘住的六條:L07/L08 同意閘 · L09 網路只認 Nexus · L35 · L90 · L99)
               邏輯 logic  (VIA_VDFArchitecture 冊 · VDF 卡書 45 張 vs 樹上尾版(冊樹不同步就是 STALE)· 鏈跑器 CGC_MDL170 尾版)
               因子 factor (VDF_Unified_Params · VDF_Param_Registry(678 參數)· VDF_Param_Engine_Map;寫者 ENG053,本口只讀)
               參數 param  (via_params_central.BOOKS 的 VDF 子集 + 規格冊自報:defaults.start / 逐項起始 / 整類起始)
               引擎 engine (VDF 獨立鏈最新一跑(讀 MDL170 快照,不重跑)· 尾版家族(同 VCGC._tail_files 一把尺)·
                            規格/格子/短令/Deck/元件冊 五面 · 卡書覆蓋 · 自測門覆蓋 · 庫表冊 VDF 表)
               橋   bridge (每一支尾版:加速器橋 [VIA:ACCEL-BRIDGE] · 網路橋 [VIA:NET-BRIDGE];排除清單委派 CGC_MDL124._excluded,
                            「真向外擷取」判定委派 CGC_MDL124._is_net_caller(批402)——尾版缺橋=RED,版史(舊版)只報不判)
               工具 tool   (VeritasCeleritas.py / VeritasAegisNexus.py 正典位在不在 · 各副本 md5 同不同一份 ·
                            SUP_MDL740_NetUnified 與 SUP_MDL737_SuperAccel 尾版 · 加速器控制面最新存證 · 同意閘現態(只讀,永不代設))
               交接 handover(VDF 文 · 一頁交接批號 vs 律冊批號 · 掉球清單)
               紀錄 records(血脈由 git 尾註量出 · VDF 文 · 收容包 · 活線;指標不複本)

自適應連結:每一條連結都在**呼叫當下**現解尾版(L04)、現算 sha、現量年齡;`sync` 對上一次快照逐條判 NEW / CHANGED / GONE / SAME;
  快照只落 VIA_Reports(不入 git),`--apply` 才寫。
Zero-Hydra(L05):本口不複製任何規則——尾版家族用 VCGC 的尺、排除清單與真擷取判定用橋掃器的函式、參數清單用 via_params_central.BOOKS、
  五面用 VCGC 的讀器、鏈的燈照抄鏈跑器再拆開講(缺件/缺料/其餘)。同一判準只寫一處(抄到函式才算出處 LL316)。
誠實四態(L16)+ 兩態:GREEN / NODATA(缺料)/ GATED(閘)/ ABSENT(缺件)/ STALE(過期)/ RED(壞)。
  本口 rc 只看四庫+橋+工具+交接;引擎面的燈是鏈跑器的判準,照抄不折進 rc。
零網路 · 零寫庫 · 零 CDN · 預設只讀;自測零污染(L17):VIA_SELFTEST=1 期間快照夾由 VIA_VDFSYS_REPORTS 指向暫存。
同意閘 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 只讀現態,**永不代設**(L07/L08);不裝任何套件。

用法:python3 VDF_SystemManager_v0100.py [status|catalog|links|records|engines|bridges|tools|read <域> [key] [--full]|sync [--apply]|page|launch [--no-probe]] [--json] [--standalone] | --selftest
  rc:0 GREEN · 1 RED(冊缺 / 尾版缺橋 / 工具正典缺 / 讀器炸)· 2 STALE 或 NODATA(過期或缺料——不是壞)
  launch 的 rc 用 L16 五態碼:0 可啟動 · 1 RED(啟動器/鏈缺 · 雙載體不同鏈)· 2 NODATA · 3 ABSENT(家族境缺必要庫)· 4 GATED(同意閘未開=你的手);read launch [probe] 同讀
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
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

import contextlib
import hashlib
import html as _html
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ===== [VIA:JSONIO-BRIDGE:v0100] JSON 讀寫正典橋(批592;正典 SUP_MDL752_VIAJsonIO)=====
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
if _JS_MOD is None:      # 大聲壞掉:讀錯編碼是無聲的錯
    raise RuntimeError("[FAIL] JSON 讀寫正典缺席:supportive modules/SUP_MDL752_VIAJsonIO_v*.py")
_json = _JS_MOD.bind_read()
# ===== [VIA:JSONIO-BRIDGE:END] =====

HERE = Path(__file__).resolve().parent            # functional modules/VDF
VIA = HERE.parent.parent
ROOT = VIA.parent
REG = VIA / "supportive modules" / "registry"
ENG = HERE / "engine"
SUPP = VIA / "supportive modules"
NET_DIR = SUPP / "network"
ACC_DIR = SUPP / "accelerator"
ME = Path(__file__).stem                          # VDF_SystemManager_v0100
FAMILY = ME.rsplit("_v", 1)[0]                    # VDF_SystemManager
_SELF_FAMILY = FAMILY                            # LL133:判定器排掉自己的家族(版史分母不算自己)
VERSION = ME.rsplit("_v", 1)[-1]                  # 由檔名讀出(尾版律;寫死會爛)
VIA_TAG = f"{FAMILY} v{VERSION}"
BORN = "側線 2026-09-21"
DOMAINS = ("policy", "logic", "factor", "param", "engine", "bridge", "tool", "handover", "records")
DOMAIN_ZH = {"policy": "政策", "logic": "邏輯", "factor": "因子", "param": "參數", "engine": "引擎",
             "bridge": "橋", "tool": "工具", "handover": "交接", "records": "紀錄"}
_FORCE_STANDALONE = {"on": False}
RC_SCOPE = ("policy", "logic", "factor", "param", "bridge", "tool", "handover")   # 引擎面的燈是鏈跑器的判準,不折進本口 rc
LAMPS = {"GREEN": "綠", "NODATA": "缺料", "GATED": "閘", "ABSENT": "缺件", "STALE": "過期", "RED": "壞"}
VDF_DIRS = ("functional modules/VDF",)
SEVEN = ("spec", "grid", "register", "deck", "manager", "inventory", "handover")
ACCEL_MARK, NET_MARK = "# ===== [VIA:ACCEL-BRIDGE:v", "# ===== [VIA:NET-BRIDGE:v"   # 橋塊**表頭**才算(docstring 提到不算);橋掃器在位時改用它的 ACCEL_START/NET_START
PINNED_LAWS = ("L07", "L08", "L09", "L35", "L90", "L99")   # 同意閘 · 網路只認 Nexus · 主動 ETF · 正典 DuckDB · 目標價 ADJ
#: 兩支工具的正典位(MDL156 的 CELERITAS / AEGIS 就是這兩個路徑;本口不另立第二個正典)
TOOLS = {"VeritasCeleritas.py": ("supportive modules/accelerator/VeritasCeleritas.py", "加速器本體(CGC_MDL156 CELERITAS 正典位;橋經 VIA_SuperAccel_Module 取用)"),
         "VeritasAegisNexus.py": ("supportive modules/network/VeritasAegisNexus.py", "網路工具本體(L09 唯一網路出口;橋經 SUP_MDL740_NetUnified 委派)")}
TOOL_COPY_DIRS = ("supportive modules", "supportive modules/network", "supportive modules/accelerator", "supportive modules/50_Protection_Acceleration")
FACTOR_BOOKS = (("VDF_UNIFIED", "functional modules/VDF/VDF_Unified_Params_v0100.json", "統一輸入參數(fetch/markets/output)"),
                ("VDF_PARAM_REG", "functional modules/VDF/VDF_Param_Registry_v0100.json", "參數登記冊(params)"),
                ("VDF_PARAM_ENGINE_MAP", "functional modules/VDF/VDF_Param_Engine_Map_v0100.json", "參數×引擎對映(by_engine / by_param / gaps;寫者 ENG053)"))
BOOT_SH, BOOT_PS1 = REG / "via_boot_update.sh", REG / "via_boot_update.ps1"          # 開機日更鏈雙載體(.sh 正主 · .ps1 跟隨其節序)
LAUNCH_CMDS = ("via-vdffetch", "via-vdfchain", "via-vdfinc", "via-vdfcov", "via-vdfdb", "via-align", "via-price", "via-chip",
               "via-etfuniv", "via-etfhist", "via-fred", "via-daytrade", "via-rungate", "via-gates", "via-envpy", "via-vdfsys")   # 啟動 VDF 擷取要用到的短令(只量登沒登)
LAUNCH_RC = {"GREEN": 0, "RED": 1, "NODATA": 2, "ABSENT": 3, "GATED": 4}                  # L16 五態碼(與 CGC_MDL170 同一張表)
_SCRAPE_YES_RX = re.compile(r"VIA_SCRAPE_CONSENT['\"][^\n]{0,40}?[!=]=\s*['\"]YES['\"]")   # v0104:寫死閘二要字面 YES 的比較式
_REG_FAM_RX = re.compile(r"(VDF_(?:ENG|MDL)\d{3}_[A-Za-z0-9]+)_v\*")
_STEP_RX = re.compile(r"\b([A-Z]{3}_(?:ENG|MDL)\d{3}_[A-Za-z0-9_]+?)(?:_v\*)?\.py\b")      # 開機鏈腳本裡的引擎家族(尾版 glob 與無版號檔同一把尺)


def REPORTS() -> Path:
    """快照夾。自測期間由 VIA_VDFSYS_REPORTS 指向暫存(L17 零污染)。"""
    o = os.environ.get("VIA_VDFSYS_REPORTS")
    return Path(o) if o else (VIA / "VIA_Reports" / "vdf_system")


# ────────────────────────── 小工具(現解 · 現算 · 現量) ──────────────────────────
def newest(folder: Path, pat: str) -> Path | None:
    hits = sorted(folder.glob(pat)) if folder.is_dir() else []
    return hits[-1] if hits else None


def rel(p) -> str:
    try:
        return Path(p).resolve().relative_to(VIA).as_posix()
    except Exception:
        return str(p)


def sha12(p) -> str:
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:12]
    except Exception:
        return ""


def age_h(p) -> float | None:
    try:
        return round((datetime.now().timestamp() - Path(p).stat().st_mtime) / 3600.0, 1)
    except Exception:
        return None


def lamp_of(state) -> str:
    """讀器回傳的 state → 燈號冊裡的一盞;燈數一律 len(LAMPS) 現場數,不寫死。"""
    s = str(state or "ABSENT").split(" ")[0]
    if s == "OK":
        return "GREEN"
    if s.startswith("BROKEN"):
        return "RED"
    return s if s in LAMPS else "RED"


_ABSENT_RX = re.compile(r"ModuleNotFoun|No module named|ImportError|缺件|缺席|不可用|不在位|缺[(=]|套件缺|樹不完整")
_NODATA_RX = re.compile(r"誠實停|沒有自測門|缺料|NODATA|0 件|件 0|0 列|列 0|SKIP")
_GATED_RX = re.compile(r"CONSENT|GATED|閘未開|同意閘")


def classify(rc, text: str = "") -> str:
    """四態表驅動(L16):rc0→GREEN;文字命中缺件→ABSENT;命中閘或 rc4→GATED;命中缺料或 rc2→NODATA;其餘 rc≠0→RED。"""
    t = text or ""
    if rc == 0:
        return "GREEN"
    if _ABSENT_RX.search(t):
        return "ABSENT"
    if _GATED_RX.search(t) or rc == 4:
        return "GATED"
    if _NODATA_RX.search(t) or rc == 2:
        return "NODATA"
    return "RED"


_MODS: dict = {}


def _mod(key: str, path):
    """惰性載入正主(尾版現解);載入期間的印字吞掉,不污染本口的輸出。"""
    if not path or not Path(path).is_file():
        return None
    k = f"{key}:{path}"
    if k in _MODS:
        return _MODS[k]
    spec = importlib.util.spec_from_file_location(f"vdfsys_{key}", path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[f"vdfsys_{key}"] = m
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(m)
    _MODS[k] = m
    return m


def _vcgc():
    if _FORCE_STANDALONE["on"]:
        return None
    return _mod("vcgc", newest(REG, "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"))


def mode() -> str:
    """獨立系統 / 子系統:VCGC 在位且載得起=subsystem;不在或 --standalone=standalone。現量,不是設定。"""
    if _FORCE_STANDALONE["on"]:
        return "standalone"
    try:
        return "subsystem" if _vcgc() is not None else "standalone"
    except Exception:
        return "standalone"


def _sweeper():
    """橋掃器 CGC_MDL124(排除清單 `_excluded` · 真擷取判定 `_is_net_caller`);缺=None 並在讀器裡講明。"""
    return _mod("sweeper", newest(REG, "CGC_MDL124_BridgeSweeper_v*.py"))


def _marks() -> tuple[str, str, str]:
    """橋標記的尺:橋掃器在位就用它的 ACCEL_START/NET_START(抄到函式才算出處 LL316);缺席才退本口表頭常數並講明。"""
    sw = _sweeper()
    a, n = getattr(sw, "ACCEL_START", None), getattr(sw, "NET_START", None)
    if isinstance(a, str) and isinstance(n, str) and a and n:
        return a, n, "CGC_MDL124.ACCEL_START/NET_START"
    return ACCEL_MARK, NET_MARK, "本口表頭常數(橋掃器缺,講明)"


def _has_bridge(src: str, kind: str, marks=None) -> bool:
    """與 CGC_MDL124.scan 同一判準:表頭在=有;自掛(VIA_SuperAccel_Module / via_net_unified_v)=有。"""
    a, n, _ = marks or _marks()
    return ((a in src) or ("VIA_SuperAccel_Module" in src)) if kind == "accel" else ((n in src) or ("via_net_unified_v" in src))


def _params_central():
    return _mod("vpc", newest(REG, "via_params_central_v*.py"))


def _is_vdf_path(s) -> bool:
    s = str(s).replace("\\", "/")
    return any(d in s for d in VDF_DIRS)


def _tails() -> tuple[dict, str]:
    """VDF 尾版家族 {family: 相對路徑}。尺=VCGC._tail_files(VIA 不在才退自家 glob 並講明)。"""
    fams: dict = {}
    try:
        v = _vcgc()
        if v is not None:
            for stem, q in v._tail_files().items():
                if _is_vdf_path(q):
                    fams[stem] = rel(q)
            if fams:
                return fams, "VCGC._tail_files"
    except Exception:
        pass
    for q in sorted(ENG.glob("*_v????.py")) + sorted(HERE.glob("*_v????.py")):
        fams[re.sub(r"_v\d{4}$", "", q.stem)] = rel(q)      # sorted → 後者覆蓋前者 = 尾版
    return fams, "own glob(standalone:VIA 不在,講明)"


def _src(p) -> str:
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


# ────────────────────────── 下行九域(只讀) ──────────────────────────
def read_policy(key: str | None = None) -> dict:
    p = newest(REG, "VIA_Policy_Laws_SSOT_v*.json")
    j = _json(p) if p else None
    if not j:
        return {"state": "ABSENT", "why": "supportive modules/registry/VIA_Policy_Laws_SSOT_v*.json 缺", "via": VIA_TAG}
    laws, lessons = list(j.get("laws") or []), list(j.get("lessons") or [])

    def _vdf(x):
        return "VDF" in (str(x.get("cat") or "") + str(x.get("zh") or ""))
    ids = {str(x.get("id")) for x in laws}
    out = {"state": "GREEN", "src": p.name, "path": rel(p), "sha12": sha12(p), "age_h": age_h(p),
           "batch": j.get("batch"), "ts": j.get("ts"), "laws": len(laws), "lessons": len(lessons),
           "vdf_laws": [x.get("id") for x in laws if _vdf(x)], "vdf_lessons": [x.get("id") for x in lessons if _vdf(x)],
           "pinned": {k: (k in ids) for k in PINNED_LAWS},
           "last_law": (laws[-1].get("id") if laws else None), "last_lesson": (lessons[-1].get("id") if lessons else None), "via": VIA_TAG}
    if not all(out["pinned"].values()):
        out["state"], out["why"] = "STALE", f"釘住的律缺 {[k for k, v in out['pinned'].items() if not v]}(律冊比本口舊或律被改號)"
    if key:
        hit = next((x for x in laws + lessons if str(x.get("id", "")).upper() == key.upper()), None)
        out["key"], out["hit"] = key, hit
        if not hit:
            out["state"], out["why"] = "NODATA", f"{key} 不在律冊(律 {len(laws)} · lessons {len(lessons)})"
    return out


def read_logic(key: str | None = None) -> dict:
    out = {"state": "GREEN", "via": VIA_TAG}
    ap = REG / "VIA_VDFArchitecture_v0100.json"
    arch = _json(ap)
    out["arch"] = ({"state": "GREEN", "path": rel(ap), "sha12": sha12(ap), "age_h": age_h(ap), "rules": len(arch.get("rules") or []),
                    "lanes_available": arch.get("lanes_available"), "stamp": arch.get("stamp"), "engine": arch.get("engine")}
                   if arch else {"state": "ABSENT", "path": rel(ap), "why": "VIA_VDFArchitecture_v0100.json 缺"})
    cp = REG / "VIA_Essentia_CardBook_VDF_v0100.json"
    cb = _json(cp)
    fams, ruler = _tails()
    if cb:
        cards = [c for c in (cb.get("cards") or []) if isinstance(c, dict)]
        card_fams = {re.sub(r"_v\d{4}$", "", str(c.get("engine"))) for c in cards}
        unv = {q.stem for q in list(ENG.glob("*.py")) + list(HERE.glob("*.py")) if not re.search(r"_v\d{4}$", q.stem)}
        gone = sorted(f for f in card_fams if f not in fams)
        unversioned = [f for f in gone if f in unv]          # 樹上有檔但沒版號:VCGC 的尺(L04 尾版律)看不見它——分開報,不混進「樹無」(L16)
        book_only = [f for f in gone if f not in unv]
        tree_only = sorted(f for f in fams if f not in card_fams and f != FAMILY)
        path_gone = sorted(str(c.get("engine")) for c in cards if c.get("path") and not (VIA / str(c.get("path"))).is_file())
        stale = bool(book_only or unversioned or tree_only or path_gone)
        out["cards"] = {"state": ("STALE" if stale else "GREEN"), "path": rel(cp), "sha12": sha12(cp), "age_h": age_h(cp),
                        "n": len(cards), "has_selftest": sum(1 for c in cards if c.get("has_selftest")), "batch": cb.get("batch"),
                        "book_only": book_only, "unversioned": unversioned, "tree_only": tree_only, "path_gone": path_gone, "ruler": ruler,
                        "why": ("冊樹不同步:冊有樹無 %d · 樹上有檔但無版號 %d(L04 尾版律外,VCGC 的尺看不見)· 樹有冊無 %d · 冊上路徑不在 %d(卡書要重建,不手改;版號要立,本口只報)"
                                % (len(book_only), len(unversioned), len(tree_only), len(path_gone)) if stale else "冊樹同步")}
    else:
        out["cards"] = {"state": "ABSENT", "path": rel(cp), "why": "VIA_Essentia_CardBook_VDF_v0100.json 缺"}
    rp = newest(REG, "CGC_MDL170_VDFChainRunner_v*.py")
    out["chain_runner"] = ({"state": "GREEN", "tail": rel(rp), "sha12": sha12(rp)} if rp else {"state": "ABSENT", "why": "CGC_MDL170_VDFChainRunner_v*.py 缺"})
    lamps = [lamp_of(out["arch"]["state"]), lamp_of(out["cards"]["state"]), lamp_of(out["chain_runner"]["state"])]
    out["state"] = "ABSENT" if "ABSENT" in lamps else ("STALE" if "STALE" in lamps else "GREEN")
    if out["state"] != "GREEN":
        out["why"] = out["cards"].get("why") or out["arch"].get("why") or out["chain_runner"].get("why")
    if key:
        table = {"arch": out["arch"], "cards": out["cards"], "chain_runner": out["chain_runner"]}
        out["key"], out["hit"] = key, table.get(key)
        if out["hit"] is None:
            out["why"] = f"{key} 不是 logic 的鍵(arch|cards|chain_runner)"
    return out


def read_factor(key: str | None = None) -> dict:
    out = {"state": "GREEN", "via": VIA_TAG, "books": [], "writer": "VDF_ENG053_ParamEngineMap(build_map;本口只讀)"}
    for bid, relp, note in FACTOR_BOOKS:
        p = VIA / relp
        j = _json(p)
        row = {"id": bid, "path": relp, "note": note, "exists": p.is_file(), "sha12": sha12(p) if p.is_file() else "", "age_h": age_h(p) if p.is_file() else None}
        if j:
            row["state"] = "GREEN"
            if bid == "VDF_PARAM_REG":
                row["params"] = len(j.get("params") or [])
                row["canonical"] = len(j.get("canonical") or [])
            elif bid == "VDF_PARAM_ENGINE_MAP":
                row["by_engine"] = len(j.get("by_engine") or {})
                row["by_param"] = len(j.get("by_param") or {})
                row["gaps"] = len(j.get("gaps") or [])
            else:
                row["sections"] = [k for k in j.keys() if k not in ("schema", "note")]
        else:
            row["state"] = "ABSENT" if not p.is_file() else "RED"
            row["why"] = "冊缺" if not p.is_file() else "冊讀不動"
        out["books"].append(row)
    if any(b["state"] != "GREEN" for b in out["books"]):
        out["state"] = "ABSENT" if any(b["state"] == "ABSENT" for b in out["books"]) else "RED"
        out["why"] = "; ".join(f"{b['id']} {b.get('why')}" for b in out["books"] if b["state"] != "GREEN")
    out["n"] = len(out["books"])
    if key:
        hit = next((b for b in out["books"] if b["id"].upper() == key.upper()), None)
        out["key"], out["hit"] = key, hit
        if not hit:
            out["why"] = f"{key} 不是因子冊(" + "|".join(b[0] for b in FACTOR_BOOKS) + ")"
    return out


def param_books() -> list:
    """via_params_central.BOOKS 的 VDF 子集(抄到函式才算出處)+ 規格冊自報。"""
    rows = []
    vpc = _params_central()
    for b in (getattr(vpc, "BOOKS", []) if vpc else []):
        pth = str(b.get("path", ""))
        if "VDF" in pth.upper() or str(b.get("id", "")).upper().startswith("VDF"):
            p = VIA / pth
            rows.append({"id": b.get("id"), "path": pth, "domain": b.get("domain"), "note": b.get("note", ""), "src": "via_params_central.BOOKS",
                         "exists": p.is_file(), "state": "GREEN" if p.is_file() else "ABSENT", "sha12": sha12(p) if p.is_file() else "", "age_h": age_h(p) if p.is_file() else None})
    sp = REG / "VIA_InputConsole_Spec_v0100.json"
    j = _json(sp) or {}
    vdf = (j.get("families") or {}).get("vdf") or {}
    n_items = sum(len(g.get("items", [])) for g in vdf.get("groups", []))
    user = j.get("user") or {}
    rows.append({"id": "SPEC:vdf", "path": rel(sp), "domain": "SPEC", "src": "VIA_InputConsole_Spec(規格冊自報)", "exists": sp.is_file(),
                 "state": "GREEN" if vdf else "ABSENT", "sha12": sha12(sp) if sp.is_file() else "", "age_h": age_h(sp) if sp.is_file() else None,
                 "summary": {"items": n_items, "groups": [g.get("id") for g in vdf.get("groups", [])], "defaults.start": (j.get("defaults") or {}).get("start"),
                             "user.starts": len(user.get("starts") or {}), "user.group_starts": len(user.get("group_starts") or {}), "python": vdf.get("python")}})
    return rows


def _book_summary(j) -> str:
    if isinstance(j, dict):
        return f"dict {len(j)} 鍵:{', '.join(list(j.keys())[:8])}"
    if isinstance(j, list):
        return f"list {len(j)} 筆"
    return type(j).__name__


def read_param(key: str | None = None, full: bool = False) -> dict:
    rows = param_books()
    absent = [r["id"] for r in rows if r["state"] != "GREEN"]
    out = {"state": "ABSENT" if absent else "GREEN", "n": len(rows), "absent": absent, "books": rows, "via": VIA_TAG,
           "src": "via_params_central.BOOKS VDF 子集 + 規格冊自報"}
    if absent:
        out["why"] = f"冊缺 {absent}"
    if key:
        hit = next((r for r in rows if str(r["id"]).upper() == key.upper()), None)
        if hit:
            h = dict(hit)
            j = _json(VIA / h["path"]) if h.get("exists") else None
            if "summary" not in h:
                h["summary"] = _book_summary(j)
            if full:
                h["content"] = j
            out["key"], out["hit"] = key, h
        else:
            out["key"], out["hit"], out["state"], out["why"] = key, None, "NODATA", f"{key} 不是 VDF 參數冊({len(rows)} 本)"
    return out


def _head1(p: Path) -> str:
    try:
        for ln in _src(p).splitlines()[:40]:
            s = ln.strip()
            if s and not s.startswith(("#", "r\"\"\"", "\"\"\"", "from __future__")):
                return s[:120]
    except Exception:
        pass
    return "(讀不到抬頭;誠實)"


def read_engine(key: str | None = None) -> dict:
    out = {"state": "NODATA", "via": VIA_TAG}
    cp = VIA / "VIA_Reports" / "vdf_chain" / "VDFCHAIN_latest.json"
    cj = _json(cp)
    if not cj:
        out["chain"] = {"state": "NODATA", "why": "VIA_Reports/vdf_chain/VDFCHAIN_latest.json 不在(via-vdfchain run)", "src": rel(cp)}
    else:
        stages = [s for s in (cj.get("stages") or []) if isinstance(s, dict)]
        split = {"ABSENT": 0, "NODATA": 0, "RED": 0, "GATED": 0}
        for st in stages:
            if str(st.get("state")) == "RED":
                c = classify(1, str(st.get("detail", "")) + " " + str(st.get("fix", "")))
                split[c] = split.get(c, 0) + 1
        out["chain"] = {"state": str(cj.get("rc_name") or "?"), "generated": cj.get("generated"), "age_h": age_h(cp), "tally": cj.get("tally") or {},
                        "stages": len(stages), "red_split": split, "mode": cj.get("mode"), "since": cj.get("since"), "src": rel(cp),
                        "consent_set": {k: (str(v) == "YES") for k, v in (cj.get("consent") or {}).items()}}
        out["state"] = lamp_of(out["chain"]["state"])
    fams, ruler = _tails()
    out["families"], out["families_detail"], out["families_ruler"] = len(fams), fams, ruler
    door = sum(1 for f, relp in fams.items() if "--selftest" in _src(VIA / relp))
    out["selftest_door"] = {"with": door, "families": len(fams)}
    cb = _json(REG / "VIA_Essentia_CardBook_VDF_v0100.json") or {}
    cards = [c for c in (cb.get("cards") or []) if isinstance(c, dict)]
    out["cards"] = {"n": len(cards), "covered": sum(1 for c in cards if str(c.get("engine")) in fams)}
    faces: dict = {}
    try:
        v = _vcgc()
        if v is None:
            raise LookupError("STANDALONE")
        sp = v.spec_items()
        faces["spec"] = [i["id"] for i in sp.get("items", []) if i.get("family") == "vdf"]
        gr = v.grid_stations()
        faces["grid"] = [s["name"][:48] for s in gr.get("stations", []) if _is_vdf_path(s.get("path", "")) or "VDF" in s.get("name", "")]
        rg = v.register_cmds()
        faces["register"] = [c["cmd"] for c in rg.get("cmds", []) if "vdf" in c["cmd"].lower() or "VDF" in str(c.get("usage") or "")]
        dk = v.deck_tasks()
        faces["deck"] = [k for k, t in dk.get("tasks", {}).items() if "vdf" in k.lower() or "VDF" in str(t.get("zh", "")) or any("VDF" in a for a in t.get("argv", []))]
        inv = v.component_registry()
        faces["inventory_active"] = sum(1 for r in inv.get("records", []) if r.get("state", "ACTIVE") == "ACTIVE" and _is_vdf_path(r.get("source", "")))
        db = v.db_sheet()
        faces["db_tables_all"] = db.get("n")
    except LookupError:
        faces["state"] = "STANDALONE:VIA 不在,五面(規格/格子/短令/Deck/元件冊)是 VIA 的面,不代讀不猜"
    except Exception as exc:
        faces["state"] = f"ABSENT VCGC {type(exc).__name__}"
    dbj = _json(REG / "VIA_DB_Table_SSOT_v0100.json") or {}
    vt = [t for t in (dbj.get("tables") or []) if str(t.get("db", "")).lower().startswith("vdf") or any(str(w).startswith("VDF_") for w in (t.get("writers") or []))]
    out["db"] = {"tables": len(vt), "rows_seen": sum(int(t.get("rows_seen") or 0) for t in vt), "batch": dbj.get("batch"), "src": "VIA_DB_Table_SSOT_v0100.json(冊上數字;真表要在資料家量)"}
    out["mode"] = mode()
    out["faces"] = {k: (len(v) if isinstance(v, list) else v) for k, v in faces.items()}
    out["faces_detail"] = {k: v for k, v in faces.items() if isinstance(v, list)}
    if key:
        fam = next((f for f in fams if f.upper() == key.upper() or f.upper().startswith(key.upper())), None)
        if fam:
            q = VIA / fams[fam]
            s = _src(q)
            out["key"], out["hit"] = key, {"family": fam, "tail": fams[fam], "sha12": sha12(q), "age_h": age_h(q), "head": _head1(q),
                                          "accel": _has_bridge(s, "accel"), "net": _has_bridge(s, "net"),
                                          "selftest_door": ("--selftest" in s),
                                          "in_spec": any(fam.lower()[:14] in str(i).lower() for i in faces.get("spec", [])),
                                          "in_grid": any(fam in n for n in faces.get("grid", [])), "in_cards": fam in {str(c.get("engine")) for c in cards}}
        else:
            out["key"], out["hit"], out["why"] = key, None, f"{key} 不是 VDF 尾版家族({len(fams)} 族)"
    return out


def read_bridge(key: str | None = None) -> dict:
    """律:所有 .py 一定要接加速器(批102 全樹導入令);所有向外擷取的 VDF 都要走網路工具(L09)。尾版逐支量;版史只報不判。"""
    sw = _sweeper()
    mk = _marks()
    fams, ruler = _tails()
    rows = []
    for fam, relp in sorted(fams.items()):
        p = VIA / relp
        s = _src(p)
        ex = ""
        caller = None
        if sw is not None:
            try:
                ex = sw._excluded(p) or ""
            except Exception:
                ex = ""
            try:
                caller = bool(sw._is_net_caller(s))
            except Exception:
                caller = None
        rows.append({"family": fam, "tail": relp, "accel": _has_bridge(s, "accel", mk), "net": _has_bridge(s, "net", mk), "net_caller": caller, "excluded": ex})
    accel_missing = [r["family"] for r in rows if not r["excluded"] and not r["accel"]]
    net_callers = [r["family"] for r in rows if r["net_caller"]]
    net_callers_missing = [r["family"] for r in rows if r["net_caller"] and not r["net"] and not r["excluded"]]
    net_missing_any = [r["family"] for r in rows if not r["net"] and not r["excluded"]]
    all_py = [q for q in HERE.rglob("*.py") if "references" not in q.parts and "__pycache__" not in q.parts
              and q.stem.rsplit("_v", 1)[0] != _SELF_FAMILY]      # LL133:自家族不進版史分母(尾版列另由 VCGC 的尺量)
    hist = {"py": len(all_py), "accel": sum(1 for q in all_py if _has_bridge(_src(q), "accel", mk)),
            "net": sum(1 for q in all_py if _has_bridge(_src(q), "net", mk))}
    out = {"state": ("RED" if (accel_missing or net_callers_missing) else "GREEN"), "via": VIA_TAG,
           "ruler": {"tails": ruler, "exclusions": ("CGC_MDL124._excluded" if sw else "橋掃器缺:未套排除清單(講明)"),
                     "net_caller": ("CGC_MDL124._is_net_caller(批402)" if sw else "橋掃器缺:未判真擷取(講明)"), "marks": mk[2]},
           "tails": len(rows), "excluded": sum(1 for r in rows if r["excluded"]),
           "accel": {"has": sum(1 for r in rows if r["accel"]), "missing": accel_missing},
           "net": {"has": sum(1 for r in rows if r["net"]), "callers": len(net_callers), "callers_missing": net_callers_missing, "missing_any": net_missing_any},
           "history": hist, "rows": rows,
           "law": "加速器橋:每一支尾版都要有(批102);網路橋:真向外擷取的每一支都要有(L09);缺一支=RED(律不是建議)"}
    if out["state"] == "RED":
        out["why"] = f"尾版缺加速器橋 {accel_missing} · 真擷取缺網路橋 {net_callers_missing}"
    if key:
        hit = next((r for r in rows if r["family"].upper() == key.upper() or r["family"].upper().startswith(key.upper())), None)
        out["key"], out["hit"] = key, hit
        if not hit:
            out["why"] = f"{key} 不是 VDF 尾版家族"
    return out


def read_tool(key: str | None = None) -> dict:
    """兩支工具:正典位在不在 · 各副本 md5 同不同一份 · 橋的尾版 · 加速器控制面存證 · 同意閘現態(只讀,永不代設)。"""
    out = {"state": "GREEN", "via": VIA_TAG, "tools": {}}
    stale = []
    for name, (canon_rel, role) in TOOLS.items():
        canon = VIA / canon_rel
        copies = []
        for d in TOOL_COPY_DIRS:
            p = VIA / d / name
            if p.is_file():
                copies.append({"path": rel(p), "sha12": sha12(p), "bytes": p.stat().st_size, "canon": (p.resolve() == canon.resolve())})
        variants = sorted({c["sha12"] for c in copies})
        row = {"role": role, "canon": canon_rel, "exists": canon.is_file(), "sha12": sha12(canon) if canon.is_file() else "", "bytes": (canon.stat().st_size if canon.is_file() else None),
               "copies": copies, "variants": len(variants), "state": ("ABSENT" if not canon.is_file() else ("STALE" if len(variants) > 1 else "GREEN"))}
        if row["state"] == "STALE":
            row["why"] = f"樹上有 {len(variants)} 種不同一份的副本(正典位 {canon_rel};其餘副本不是同一份=有人過期);裁定哪一份是正典是操作員的手,本口只照出來"
            stale.append(name)
        out["tools"][name] = row
    nu = newest(NET_DIR, "SUP_MDL740_NetUnified_v*.py")
    sa = newest(SUPP, "SUP_MDL737_SuperAccelModule_v*.py")
    out["bridges"] = {"net_unified": (rel(nu) if nu else None), "super_accel": (rel(sa) if sa else None),
                      "super_accel_module": (SUPP / "VIA_SuperAccel_Module.py").is_file()}
    ap = VIA / "VIA_Reports" / "accelerator" / "VIA_ACCELERATOR_CONTROL_latest.json"
    aj = _json(ap)
    out["accel_control"] = ({"state": "GREEN", "age_h": age_h(ap), "src": rel(ap), "summary": {k: aj.get(k) for k in ("generated", "verdict", "state", "coverage") if k in aj}}
                            if aj else {"state": "NODATA", "why": "VIA_Reports/accelerator/VIA_ACCELERATOR_CONTROL_latest.json 不在(via-accel-check)"})
    out["gate"] = {"VIA_NET_CONSENT": os.environ.get("VIA_NET_CONSENT", "") == "YES", "VIA_SCRAPE_CONSENT": os.environ.get("VIA_SCRAPE_CONSENT", "") == "YES",
                   "rule": "只讀現態;AI 永不代設(L07/L08);閘沒開 = GATED 不是壞"}
    if not all(t["exists"] for t in out["tools"].values()) or not nu or not sa or not out["bridges"]["super_accel_module"]:
        out["state"], out["why"] = "ABSENT", "工具正典位或橋尾版缺:" + ", ".join(
            [n for n, t in out["tools"].items() if not t["exists"]] + ([] if nu else ["SUP_MDL740_NetUnified"]) + ([] if sa else ["SUP_MDL737_SuperAccelModule"]) + ([] if out["bridges"]["super_accel_module"] else ["VIA_SuperAccel_Module.py"]))
    elif stale:
        out["state"], out["why"] = "STALE", f"副本不同一份:{stale}(見 tools.*.why)"
    if key:
        out["key"], out["hit"] = key, out["tools"].get(key) or out["tools"].get(key + ".py")
        if out["hit"] is None:
            out["why"] = f"{key} 不是本口管的工具({'|'.join(TOOLS)})"
    return out


def read_handover() -> dict:
    out = {"state": "GREEN", "via": VIA_TAG}
    v = None
    try:
        v = _vcgc()
    except Exception:
        v = None
    if v is None:
        hits = sorted(VIA.glob("docs/VIA_Handover_*_B*.md"))
        out["latest_batch_doc"] = hits[-1].name if hits else None
        db = sorted(VIA.glob("docs/VIA_DroppedBalls_B*.md"))
        out["dropped_balls"] = {"src": (db[-1].name if db else None), "state": "STANDALONE(未解析;VIA 在位時由 VCGC 讀 n/open)"}
    else:
        try:
            out["latest_batch_doc"] = v.handover_src().get("src")
            bl = v.dropped_balls()
            out["dropped_balls"] = {"src": bl.get("src"), "n": bl.get("n"), "open": bl.get("open")}
        except Exception as exc:
            out["latest_batch_doc"] = f"ABSENT {type(exc).__name__}"
    onepage, root_copy = VIA / "docs" / "VIA_Handover_ONEPAGE.md", ROOT / "VIA_HANDOVER_LATEST.md"

    def _batch_of(p: Path):
        try:
            m = re.search(r"批(\d+)", _src(p)[:400])
            return int(m.group(1)) if m else None
        except Exception:
            return None
    ob, rb = _batch_of(onepage), _batch_of(root_copy)
    lawb = None
    try:
        lawb = int(re.search(r"(\d+)", str(read_policy().get("batch") or "")).group(1))
    except Exception:
        pass
    out["onepage"] = {"docs_batch": ob, "root_batch": rb, "laws_batch": lawb, "age_h": age_h(onepage),
                      "same": (sha12(onepage) == sha12(root_copy)) if onepage.is_file() and root_copy.is_file() else None}
    vdocs = docs_index()
    out["vdf_docs"] = len(vdocs)
    nums = [int(m.group(1)) for q in VIA.glob("docs/VIA_B*_*.md") for m in [re.match(r"VIA_B(\d+)", q.name)] if m]
    out["latest_b_doc"] = max(nums) if nums else None
    if ob is None:
        out["state"], out["why"] = "ABSENT", "docs/VIA_Handover_ONEPAGE.md 缺或無批號"
    elif lawb and ob < lawb:
        out["state"], out["why"] = "STALE", f"一頁交接 批{ob} < 律冊 批{lawb}(L15 三處同一份但都舊;via-vcgc page --publish 未跑)"
    elif out["onepage"]["same"] is False:
        out["state"], out["why"] = "STALE", "docs ONEPAGE 與倉根 VIA_HANDOVER_LATEST.md 不同一份(L15)"
    return out


# ────────────────────────── 啟動就緒(launch;只量不動手——閘與境是操作員的手) ──────────────────────────
def chain_steps(text: str) -> list:
    """開機鏈腳本呼叫到的引擎家族(順序保留 · 去重;整行註解不算步)。
    .sh 的 newest 'X_v*.py' / ls "$DIR"/X_v*.py / "$ENG/X.py" 與 .ps1 的 Newest $DIR "X_v*.py" / Join-Path $ENG "X.py" 用同一把尺 _STEP_RX。"""
    out: list = []
    for ln in (text or "").splitlines():
        if ln.strip().startswith("#"):
            continue
        for m in _STEP_RX.finditer(ln):
            if m.group(1) not in out:
                out.append(m.group(1))
    return out


def chain_parity(sh: Path | None = None, ps: Path | None = None) -> dict:
    """開機鏈雙載體同鏈(Z94 那一課:.ps1 少了兩步,走 VIA.ps1 的工作站主動 ETF 就永遠不會自動更新——量出來其實少 13 步)。
    .sh 是正主:.ps1 少一步 = RED 並點名;.sh 少一步(.ps1 多出來)= STALE;.ps1 用裸 python 起引擎(批384 律)= STALE。"""
    sh, ps = (sh or BOOT_SH), (ps or BOOT_PS1)
    out: dict = {"sh": rel(sh), "ps1": rel(ps), "sh_exists": sh.is_file(), "ps1_exists": ps.is_file(), "only_sh": [], "only_ps1": [], "steps_sh": 0, "steps_ps1": 0, "ps1_family_python": False}
    if not (sh.is_file() and ps.is_file()):
        out["state"] = "ABSENT"
        out["why"] = "開機鏈腳本缺:" + " · ".join(n for n, p in (("via_boot_update.sh", sh), ("via_boot_update.ps1", ps)) if not p.is_file())
        return out
    a, b = chain_steps(_src(sh)), chain_steps(_src(ps))
    out["steps_sh"], out["steps_ps1"] = len(a), len(b)
    out["only_sh"], out["only_ps1"] = [x for x in a if x not in b], [x for x in b if x not in a]
    out["ps1_family_python"] = re.search(r"envpy|Get-VIAEnvPython|VIA_PY_VDF", _src(ps)) is not None
    if out["only_sh"]:
        out["state"], out["why"] = "RED", f".ps1 少 {len(out['only_sh'])} 步(.sh 正主有):{' · '.join(out['only_sh'])}"
    elif out["only_ps1"]:
        out["state"], out["why"] = "STALE", f".sh 正主少 {len(out['only_ps1'])} 步(.ps1 有):{' · '.join(out['only_ps1'])}"
    elif not out["ps1_family_python"]:
        out["state"], out["why"] = "STALE", ".ps1 用裸 python 起引擎(批384 律:VDF 引擎以家族境 python 啟動)"
    else:
        out["state"], out["why"] = "GREEN", f"同鏈 {len(a)} 步"
    return out


def _rungate():
    """能跑閘 CGC_MDL137(家族境 python 解析 python_for → MDL136;必要庫表 FAMILY_LIBS;探針 probe_libs);缺=None 並講明。"""
    return _mod("rungate", newest(REG, "CGC_MDL137_RunGate_v*.py"))


def _chain_last() -> dict:
    cp = VIA / "VIA_Reports" / "vdf_chain" / "VDFCHAIN_latest.json"
    cj = _json(cp)
    if not cj:
        return {"state": "NODATA", "why": "VDFCHAIN_latest.json 不在(via-vdfchain run)"}
    return {"state": str(cj.get("rc_name") or "?"), "generated": cj.get("generated"), "tally": cj.get("tally") or {}, "mode": cj.get("mode"), "age_h": age_h(cp), "src": rel(cp)}


def _lanes_last() -> dict:
    d = VIA / "VIA_Reports" / "lanes"
    hits = sorted(d.glob("LANES_*.json"), key=lambda p: p.stat().st_mtime) if d.is_dir() else []
    if not hits:
        return {"state": "NODATA", "why": "VIA_Reports/lanes 無存證(via-vdffetch 還沒跑過)"}
    j = _json(hits[-1]) or {}
    return {"state": str(j.get("state") or "?"), "stamp": j.get("stamp"), "n_ok": j.get("n_ok"), "n_fail": j.get("n_fail"), "n_skip": j.get("n_skip"), "age_h": age_h(hits[-1]), "src": rel(hits[-1])}



def scrape_gate_split(environ=None) -> dict:
    """閘二的三個消費者(只量不裁):寫死字面 YES 的尾版引擎 · 直呼會撞到它們的短令 · 十道/開機鏈對子行程自帶 YES · 統包 gate_state()。"""
    env = os.environ if environ is None else environ
    raw = str(env.get("VIA_SCRAPE_CONSENT") or "")
    value = "YES" if raw == "YES" else ("OFF" if raw == "OFF" else ("UNSET" if not raw else "OTHER"))   # 不印原值(via-gates 同律)
    fams, _ = _tails()
    legacy = sorted(f for f, p in fams.items() if f != _SELF_FAMILY and _SCRAPE_YES_RX.search(_src(VIA / p)))
    reg_p = newest(VIA, "Register-VIA-Commands-v*.ps1")
    blocked = []
    for chunk in re.split(r"(?m)^function global:", _src(reg_p) if reg_p else "")[1:]:
        name = re.match(r"([\w-]+)", chunk)
        if name and any(f in legacy for f in _REG_FAM_RX.findall(chunk[:2000])):
            blocked.append(name.group(1))
    lanes = newest(REG, "CGC_MDL134_ParallelLanes_v*.py")
    lanes_force = bool(lanes) and re.search(r'env\["VIA_SCRAPE_CONSENT"\]\s*=\s*"YES"', _src(lanes)) is not None
    boot_force = ('$env:VIA_SCRAPE_CONSENT = "YES"' in _src(BOOT_PS1)) and ("VIA_SCRAPE_CONSENT=YES" in _src(BOOT_SH))
    tool = None
    if environ is None:
        try:
            nt = _via_net()
            g = nt.gate_state() if (nt is not None and hasattr(nt, "gate_state")) else None
            if isinstance(g, dict):
                tool = {"open": bool(g.get("open")), "gate2_set": bool(g.get("gate2_scrape_token_set")),
                        "off_counts_as_set": (value == "OFF" and bool(g.get("gate2_scrape_token_set")))}
        except Exception as exc:
            tool = {"error": type(exc).__name__}
    return {"value": value, "legacy_yes": legacy, "blocked_direct": (blocked if value != "YES" else []), "cmds_on_legacy": blocked,
            "lanes_force_yes": lanes_force, "boot_force_yes": boot_force, "tool_gate": tool,
            "ruler": "尾版源碼比較式(字面 YES)× 短令冊尾版函式體 × CGC_MDL134 子行程環境 × SUP_MDL740.gate_state()"}


def hist_limit_state(environ=None) -> dict:
    env = os.environ if environ is None else environ
    raw = str(env.get("VIA_HIST_LIMIT") or "").strip()
    fetch = newest(VIA, "Invoke-VIA-VdfFetch-v*.ps1")
    return {"set": raw.isdigit(), "n": (int(raw) if raw.isdigit() else None),
            "launcher": fetch.name if fetch else None, "launcher_restores": bool(fetch) and ("Restore-VIAFetchEnv" in _src(fetch))}


def plan_catalog() -> dict:
    """增量計畫目錄新鮮度:委派 VDF_ENG089 尾版的 catalog_freshness()(唯一出處;本口不另算)。"""
    p = newest(ENG, "VDF_ENG089_IncrementalFetchGate_v*.py")
    try:
        m = _mod("eng089", p)
    except Exception as exc:
        return {"state": "UNKNOWN", "why": f"VDF_ENG089 載入炸:{type(exc).__name__}"}
    if m is None or not hasattr(m, "catalog_freshness"):
        return {"state": "UNKNOWN", "why": f"{p.name if p else 'VDF_ENG089'} 沒有 catalog_freshness(v0101 起才有)"}
    try:
        r = m.catalog_freshness()
    except Exception as exc:
        return {"state": "UNKNOWN", "why": f"catalog_freshness 炸:{type(exc).__name__}"}
    r["ruler"] = f"{p.name}.catalog_freshness"
    return r


def other_fetchers() -> list:
    """VDF 其他擷取件(量在不在與有沒有治理入口):主線批716–724 的 MDL004/ENG092 · 本線 v0100 的 MDL002/003/006。"""
    out = []
    for fam in ("VDF_MDL004_TWFullMarketEngine", "VDF_ENG092_TWFlowsAdjConsensus", "VDF_MDL002_YFinanceFetchingEngine",
                "VDF_MDL003_SentimentMacroEngine", "VDF_MDL006_FinancialModel"):
        p = newest(HERE, fam + "_v*.py") or newest(ENG, fam + "_v*.py")
        src = _src(p) if p else ""
        out.append({"family": fam, "tail": rel(p) if p else None, "governed": ("def main_governed" in src) or ("rc4 GATED" in src and "def main" in src)})
    return out


def read_launch(probe: bool = True, environ=None) -> dict:
    """啟動就緒(只量不動手)。probe=True 用家族境 python 現探必要庫(一個子行程);False 讀上次能跑閘快照(零子行程;status/page 用這個)。
    燈:RED(啟動器/鏈缺 · 雙載體不同鏈)> ABSENT(必要庫不在家族境)> GATED(同意閘未開=你的手)> GREEN(可啟動);從沒跑過只是紀錄。"""
    env = os.environ if environ is None else environ     # v0104:可注入(自測用合成環境,不讀寫真同意閘)
    out: dict = {"via": VIA_TAG, "probe": probe, "notes": [], "environ": ("process" if environ is None else "injected")}
    # ① 家族境 python + 必要庫(尺=CGC_MDL137;本口不抄別名表、不抄必要庫表)
    rg = None
    try:
        rg = _rungate()
    except Exception as exc:
        out["notes"].append(f"CGC_MDL137 載入炸:{type(exc).__name__}")
    req: list = []
    missing: list = []
    libs_known = False
    if rg is None:
        out["python"] = {"state": "ABSENT", "why": "CGC_MDL137_RunGate_v*.py 缺或載不起(尺不在,不猜)", "ruler": "CGC_MDL137.python_for → CGC_MDL136.resolve_env_python"}
        out["libs"] = {"required": [], "have": {}, "missing": [], "src": "尺缺", "known": False}
    else:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                py = rg.python_for("vdf")
        except Exception as exc:
            py = {"state": "ABSENT", "python": sys.executable, "why": f"python_for 炸:{type(exc).__name__}"}
        req = list(((getattr(rg, "FAMILY_LIBS", {}) or {}).get("vdf") or {}).get("required") or [])
        libs: dict = {}
        if probe and req:
            try:
                libs = rg.probe_libs(py.get("python") or sys.executable, req)
            except Exception as exc:
                libs = {"__probe_error__": f"{type(exc).__name__}"}
            libs_src = "現探(CGC_MDL137.probe_libs;家族境 python 子行程)"
        else:
            snap = _json(VIA / "VIA_Reports" / "rungate" / "RUNGATE_latest.json") or {}
            fam = (snap.get("families") or {}).get("vdf") or {}
            libs = {k: v for k, v in (fam.get("libs") or {}).items() if k in req}
            libs_src = f"上次能跑閘快照 {snap.get('ts')}(via-rungate)" if fam else "無快照(via-rungate 沒跑過;--no-probe 不現探)"
        libs_known = any(k in libs for k in req)
        missing = [k for k in req if not libs.get(k)] if libs_known else []
        out["python"] = {"state": py.get("state"), "python": py.get("python"), "env": py.get("env"), "source": py.get("source"), "hint": py.get("hint"),
                         "ruler": "CGC_MDL137.python_for → CGC_MDL136.resolve_env_python"}
        out["libs"] = {"required": req, "have": {k: libs.get(k) for k in req}, "missing": missing, "src": libs_src, "known": libs_known, "probe_error": libs.get("__probe_error__")}
    # ② 同意閘現態(只讀;永不代設 L07/L08)+ FRED 鑰只判在不在
    net, scr = env.get("VIA_NET_CONSENT", ""), env.get("VIA_SCRAPE_CONSENT", "")
    out["consent"] = {"VIA_NET_CONSENT": ("OPEN" if net.upper() == "YES" else ("SET" if net else "UNSET")), "VIA_SCRAPE_CONSENT": ("SET" if scr else "UNSET"),
                      "fred_key": bool(env.get("FRED_API_KEY")), "hand": "操作員($env:VIA_NET_CONSENT='YES';本口永不代設)"}
    out["consent"]["scrape_split"] = scrape_gate_split(environ)      # v0104 ①
    out["hist_limit"] = hist_limit_state(environ)                     # v0104 ②
    # ③ 網路工具掛載(統包唯一網路工具;後端 AegisNexus 正典)
    nm = _via_net()
    net_ok = None
    if nm is not None and hasattr(nm, "net_ok"):
        try:
            net_ok = bool(nm.net_ok())
        except Exception:
            net_ok = None
    out["net_tool"] = {"path": rel(VIA_NET_TOOL_PATH) if VIA_NET_TOOL_PATH else None, "loads": nm is not None, "net_ok": net_ok,
                       "aegis": (VIA / TOOLS["VeritasAegisNexus.py"][0]).is_file()}
    # ④ 啟動器 · 短令 · 鏈(尾版現解)
    fetch, reg_p = newest(VIA, "Invoke-VIA-VdfFetch-v*.ps1"), newest(VIA, "Register-VIA-Commands-v*.ps1")
    reg_src = _src(reg_p) if reg_p else ""
    cmds = {c: (re.search(r"function global:" + re.escape(c) + r"\s*\{", reg_src) is not None) for c in LAUNCH_CMDS}
    lanes, chain, envpy = newest(REG, "CGC_MDL134_ParallelLanes_v*.py"), newest(REG, "CGC_MDL170_VDFChainRunner_v*.py"), newest(REG, "CGC_MDL136_EntryBridge_v*.py")
    out["launchers"] = {"fetch_ps1": rel(fetch) if fetch else None, "fetch_cmd": (VIA / "via-vdffetch.cmd").is_file(), "register": reg_p.name if reg_p else None,
                        "cmds": cmds, "cmds_missing": [c for c, ok in cmds.items() if not ok], "lanes": rel(lanes) if lanes else None,
                        "chain_runner": rel(chain) if chain else None, "envpy": rel(envpy) if envpy else None, "boot_sh": BOOT_SH.is_file(), "boot_ps1": BOOT_PS1.is_file(),
                        "other_fetchers": other_fetchers(),                                                   # v0104 ④
                        "lanes_build_derived": bool(re.search(r"ENG060_AdjPriceLayer|ENG061_FeatureStore", _src(newest(REG, "CGC_MDL125_FixAll_v*.py")) if newest(REG, "CGC_MDL125_FixAll_v*.py") else ""))}
    # ⑤ 開機鏈雙載體同鏈
    out["parity"] = chain_parity()
    # ⑥ 上次實跑存證(只讀;沒有=沒跑過,不是紅)
    mark = HERE / "output_hub" / "mega" / ".last_boot_update"
    logd = VIA / "VIA_Reports" / "boot_update_logs"
    logs = sorted(logd.glob("BOOT_*.log")) if logd.is_dir() else []
    rgs = _json(VIA / "VIA_Reports" / "rungate" / "RUNGATE_latest.json") or {}
    out["evidence"] = {"boot_marker": (_src(mark).strip() or None) if mark.is_file() else None, "boot_log": (logs[-1].name if logs else None),
                       "boot_log_age_h": (age_h(logs[-1]) if logs else None),
                       "rungate": ({"verdict": rgs.get("verdict"), "ts": rgs.get("ts"), "vdf": ((rgs.get("families") or {}).get("vdf") or {}).get("verdict")} if rgs else {"state": "NODATA", "why": "via-rungate 沒跑過"}),
                       "chain": _chain_last(), "lanes": _lanes_last(), "plan_catalog": plan_catalog()}          # v0104 ③
    # ⑦ 落點(.gitignore 批128:mega 產物不入版控;0 件=沒抓過,不是壞)
    hub = HERE / "output_hub"
    n_db = sum(1 for q in hub.rglob("*") if q.suffix in (".duckdb", ".parquet")) if hub.is_dir() else 0
    out["data"] = {"output_hub": hub.is_dir(), "mega": (hub / "mega").is_dir(), "db_files": n_db}
    # 判(RED > ABSENT > GATED > GREEN)+ 下一步卡(每一行都是可貼的;閘與境那兩行是你的手)
    card: list = []
    if not fetch or not lanes or not chain or not cmds.get("via-vdffetch"):
        gone = [n for n, ok in (("Invoke-VIA-VdfFetch-v*.ps1", fetch), ("CGC_MDL134_ParallelLanes_v*.py", lanes), ("CGC_MDL170_VDFChainRunner_v*.py", chain), ("Register via-vdffetch", cmds.get("via-vdffetch"))) if not ok]
        out["state"], out["why"] = "RED", "啟動器/鏈缺:" + " · ".join(gone)
        card += ["[修] 這些是樹上的檔,不是設定:git pull(或把側線併進來)後再 via-vdfsys launch"]
    elif out["parity"]["state"] == "RED":
        out["state"], out["why"] = "RED", "開機鏈雙載體不同鏈:" + out["parity"]["why"]
        card += ["[修] via_boot_update.ps1 補上 .sh 正主的那幾步(L70:.ps1 改動要你點頭)後再 via-vdfsys launch"]
    elif out["python"].get("state") == "ABSENT" or (libs_known and missing):
        out["state"], out["why"] = "ABSENT", ("必要庫不在家族境:" + ", ".join(missing)) if missing else str(out["python"].get("why"))
        card += ["[你的手] " + (out["python"].get("hint") or "建 vdf 境:via-envgov apply --approve(ENSURE_ENV via_vdf_312);本口不裝套件"),
                 "via-rungate(境好了複測;GREEN 24h 內才過 L19)→ via-vdfsys launch"]
    elif out["consent"]["VIA_NET_CONSENT"] != "OPEN":
        out["state"], out["why"] = "GATED", "同意閘未開(VIA_NET_CONSENT ≠ YES):料齊、等你的手;零網路的站照跑"
        card += ["[你的手] $env:VIA_NET_CONSENT='YES'(本視窗;直呼 via-price / via-chip 那一類另需閘二,見下一行)",
                 "via-vdffetch 2023 --dry(只印十一步計畫不抓)→ via-vdffetch 2023(十一步十道並行;史深 2023-01-01 起)"]
    else:
        out["state"], out["why"] = "GREEN", "可啟動:家族境 + 必要庫 + 閘開 + 啟動器/鏈在位 + 雙載體同鏈"
        card += ["via-vdffetch 2023 --dry(只印十一步計畫不抓)→ via-vdffetch 2023(十一步十道並行;史深 2023-01-01 起)"]
    if not libs_known and out["state"] not in ("RED", "ABSENT"):
        out["notes"].append("必要庫沒量到(--no-probe 且無能跑閘快照):via-rungate 或 via-vdfsys launch(現探)")
    if out["parity"]["state"] == "STALE":
        out["notes"].append("雙載體 " + out["parity"]["why"])
    if out["launchers"]["cmds_missing"]:
        out["notes"].append("短令冊少:" + " · ".join(out["launchers"]["cmds_missing"]) + "(via-reload 拉尾版冊)")
    if not out["consent"]["fred_key"]:
        out["notes"].append("FRED_API_KEY 不在(via-fred 那一步會 SKIP 印指令;鑰是你的手)")
    hl, sp, pc = out["hist_limit"], out["consent"]["scrape_split"], out["evidence"]["plan_catalog"]
    if hl["set"]:
        card.append(f"[你的手] $env:VIA_HIST_LIMIT=''(本視窗帶著 VIA_HIST_LIMIT={hl['n']}:via-vdffetch 沒打 --limit 也只抓 {hl['n']} 檔"
                    + ("" if hl["launcher_restores"] else ";這一版啟動器會把 --limit 留在視窗") + ")")
        out["notes"].append(f"視窗限量 VIA_HIST_LIMIT={hl['n']}(啟動器 {hl['launcher']} 跑完{'會' if hl['launcher_restores'] else '不會'}還原)")
    if sp["blocked_direct"]:
        card.append("[你的手] 直呼 " + " / ".join(sp["blocked_direct"][:6]) + (" …" if len(sp["blocked_direct"]) > 6 else "")
                    + f" 前:$env:VIA_SCRAPE_CONSENT='YES'(量到 {len(sp['legacy_yes'])} 支尾版引擎只認字面 YES;閘二現在是 {sp['value']};"
                    + ("via-vdffetch 十道與開機鏈對子行程自帶 YES,不受影響" if sp["lanes_force_yes"] else "十道沒有自帶 YES") + ")")
    if (sp.get("tool_gate") or {}).get("off_counts_as_set"):
        out["notes"].append("統包 gate_state() 把閘二 OFF 也算「已設」(非空即算);實際 http 道仍由包內法遵擋——判讀以引擎自己的閘為準")
    if pc.get("state") == "STALE":
        card.append("抓完先 via-datahome catalog(" + str(pc.get("why"))[:90] + ")→ 再 via-vdfinc plan")
    today = datetime.now().strftime("%Y-%m-%d")
    card += ["每日:VIA.ps1 全自動 / .\\launch.ps1 / Deck「boot」→ via_boot_update.ps1(與 .sh 同鏈 ⓪–⑳;marker 每日首跑一次"
             + (f";今天 marker 已是 {today},再跑會 SKIP" if out["evidence"].get("boot_marker") == today else "") + ")",
             "抓完:via-datahome catalog → via-vdfinc plan · "
             + ("" if out["launchers"]["lanes_build_derived"] else "調整層/因子庫(prices_canonical · features_daily)十道不建,要開機鏈 ②b ②c · ")
             + "via-vdfchain run · via-vdfcov roster · via-align check · via-vdfsys"]
    out["next"] = card
    out["rc"] = LAUNCH_RC.get(out["state"], 1)
    return out


def _print_launch(r: dict) -> None:
    py, lb, co, nt, la, pa, ev, da = (r.get(k) or {} for k in ("python", "libs", "consent", "net_tool", "launchers", "parity", "evidence", "data"))
    print(f"[VDF_SystemManager] launch · {VIA_TAG} · 啟動就緒 {r['state']}(rc {r['rc']})· {r.get('why')}")
    print(f"  ① python   {str(py.get('state')):13s} {py.get('python')}({py.get('env') or 'base'};{py.get('source') or py.get('why')})")
    have = sum(1 for k in lb.get("required", []) if (lb.get("have") or {}).get(k))
    print(f"  ② 必要庫   {have}/{len(lb.get('required', []))} 缺 {', '.join(lb.get('missing') or []) or '-'}({lb.get('src')})" + (f" · 探針炸 {lb.get('probe_error')}" if lb.get("probe_error") else ""))
    print(f"  ③ 同意閘   NET {co.get('VIA_NET_CONSENT')} · SCRAPE {co.get('VIA_SCRAPE_CONSENT')} · FRED_API_KEY {'在' if co.get('fred_key') else '不在'}(只讀;永不代設)")
    sp = co.get("scrape_split") or {}
    print(f"  ③b 閘二    值 {sp.get('value')} · 寫死字面 YES 的尾版 {len(sp.get('legacy_yes') or [])} 支 · 直呼會撞到的短令 {', '.join(sp.get('cmds_on_legacy') or []) or '-'} · 十道自帶 YES {sp.get('lanes_force_yes')} · 開機鏈自帶 YES {sp.get('boot_force_yes')} · 統包 gate_state {sp.get('tool_gate')}")
    hl = r.get("hist_limit") or {}
    print(f"  ③c 視窗限量 VIA_HIST_LIMIT {hl.get('n') if hl.get('set') else '未設'} · 啟動器 {hl.get('launcher')} 跑完還原 {hl.get('launcher_restores')}")
    print(f"  ④ 網路工具 {Path(nt.get('path') or '缺').name} 載入 {nt.get('loads')} net_ok {nt.get('net_ok')} · AegisNexus 正典 {'在' if nt.get('aegis') else '缺'}")
    cm = la.get("cmds") or {}
    print(f"  ⑤ 啟動器   {Path(la.get('fetch_ps1') or '缺').name} · via-vdffetch.cmd {'在' if la.get('fetch_cmd') else '缺'} · {la.get('register')} 短令 {sum(1 for v in cm.values() if v)}/{len(cm)}(缺 {', '.join(la.get('cmds_missing') or []) or '-'})· 十道 {Path(la.get('lanes') or '缺').name} · 鏈跑器 {Path(la.get('chain_runner') or '缺').name} · envpy {Path(la.get('envpy') or '缺').name}")
    print(f"  ⑥ 雙載體   {pa.get('state')} .sh {pa.get('steps_sh')} 步 · .ps1 {pa.get('steps_ps1')} 步 · 只在 .sh {pa.get('only_sh') or '-'} · 只在 .ps1 {pa.get('only_ps1') or '-'} · .ps1 家族境 python {pa.get('ps1_family_python')}")
    rgv, chv, lnv = ev.get("rungate") or {}, ev.get("chain") or {}, ev.get("lanes") or {}
    print(f"  ⑦ 上次實跑 boot marker {ev.get('boot_marker')} · log {ev.get('boot_log')}({ev.get('boot_log_age_h')} h)· 能跑閘 {rgv.get('verdict') or rgv.get('state')}({rgv.get('ts') or ''};vdf {rgv.get('vdf')})· 獨立鏈 {chv.get('state')} {chv.get('tally') or ''} · 十道 {lnv.get('state')} {lnv.get('stamp') or ''}")
    print(f"  ⑧ 落點     output_hub {'在' if da.get('output_hub') else '缺'} · mega {'在' if da.get('mega') else '缺'} · 庫/parquet {da.get('db_files')} 件(0 件=沒抓過,不是壞)")
    pc = ev.get("plan_catalog") or {}
    print(f"  ⑦b 增量目錄 {pc.get('state')} · {pc.get('why', '')}")
    print("  ⑨ 其他擷取件 " + " · ".join(f"{Path(str(x['tail'])).name if x['tail'] else x['family'] + ' 缺'}{'(治理入口)' if x['governed'] else ''}" for x in (la.get("other_fetchers") or [])))
    for n in r.get("notes") or []:
        print(f"  [註] {n}")
    print("  [下一步]")
    for i, line in enumerate(r.get("next") or [], 1):
        print(f"    {i}. {line}")


# ────────────────────────── 上行(七處自審;不假綠) ──────────────────────────
def upstream() -> dict:
    out: dict = {"via": VIA_TAG, "mode": mode()}
    v = None
    try:
        v = _vcgc()
    except Exception as exc:
        out["vcgc"] = f"ABSENT {type(exc).__name__}"
    if v is None and out["mode"] == "standalone":
        out["vcgc"] = "STANDALONE"
    if v is not None:
        out["vcgc"] = {"src": Path(v.__file__).name, "version": getattr(v, "VERSION", "?"), "delegates": callable(getattr(v, "_vdfsys", None))}
        try:
            out["spec"] = any(i.get("id") == "vdf_system" for i in v.spec_items().get("items", []))
            out["grid"] = any(FAMILY in str(s.get("path", "")) for s in v.grid_stations().get("stations", []))
            out["register"] = any(c.get("cmd") == "via-vdfsys" for c in v.register_cmds().get("cmds", []))
            out["deck"] = "vdf_system" in v.deck_tasks().get("tasks", {})
            out["manager"] = FAMILY in (v.manager_names().get("engines") or {})
            rec = next((r for r in v.component_registry().get("records", []) if r.get("identity") == FAMILY and r.get("state", "ACTIVE") == "ACTIVE"), None)
            out["inventory"] = (rec or {}).get("code") or False
        except Exception as exc:
            out["faces_error"] = type(exc).__name__
    else:
        out.setdefault("vcgc", "ABSENT")
    mp = newest(VIA, "VIA_SYSTEM_MANAGER_v*.py")
    out["via_manager"] = mp.name if mp else "ABSENT"
    docs = sorted(VIA.glob("docs/*.md"))[-40:]
    out["handover"] = any(FAMILY in _src(q) for q in docs)
    out["seven"] = {k: out.get(k, False) for k in SEVEN}
    out["done"] = sum(1 for k in SEVEN if out.get(k))
    return out


# ────────────────────────── 紀錄索引(指標不複本) ──────────────────────
def _git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return ""


def lineage(limit: int = 800) -> dict:
    """血脈由 git 尾註量出來:每個 Claude-Session 幾筆 commit、幾筆提到 VDF、批號範圍、最新/最早主題。"""
    raw = _git("log", "--all", f"-n{limit}", "--format=%H%x1f%s%x1f%b%x1e")
    sessions: dict = {}
    for rec in raw.split("\x1e"):
        parts = rec.strip("\n").split("\x1f")
        if len(parts) < 3:
            continue
        sha, subj, body = parts[0].strip(), parts[1].strip(), parts[2]
        m = re.search(r"Claude-Session:\s*https?://\S+/(session_[A-Za-z0-9]+)", body)
        sid = m.group(1) if m else "(無 Claude-Session 尾註)"
        s = sessions.setdefault(sid, {"commits": 0, "vdf_commits": 0, "batch_hits": [], "latest": subj[:72], "earliest": subj[:72], "shas": []})
        s["commits"] += 1
        s["earliest"] = subj[:72]
        if "VDF" in subj.upper():
            s["vdf_commits"] += 1
        b = re.search(r"批(\d+)", subj)
        if b:
            s["batch_hits"].append(int(b.group(1)))
        if len(s["shas"]) < 3:
            s["shas"].append(sha[:8])
    for s in sessions.values():
        h = s.pop("batch_hits")
        s["batch_min"], s["batch_max"], s["batched_commits"] = (min(h) if h else None), (max(h) if h else None), len(h)
    return sessions


def docs_index() -> list:
    rows = []
    for q in sorted(VIA.glob("docs/*.md")) + sorted(ROOT.glob("docs/*.md")):
        t = _src(q)
        if not t:
            continue
        n = t.count("VDF")
        if "VDF" in q.name or n >= 8:
            rows.append({"doc": (rel(q) if str(q).startswith(str(VIA)) else "../docs/" + q.name), "vdf_mentions": n, "sha12": sha12(q), "age_h": age_h(q), "bytes": q.stat().st_size})
    return rows


def intake_index() -> list:
    d = HERE / "references" / "intake"
    rows = []
    if d.is_dir():
        for q in sorted(d.iterdir()):
            files = sum(1 for _ in q.rglob("*") if _.is_file()) if q.is_dir() else 1
            m = re.search(r"_b(\d{3,8})", q.name)
            rows.append({"intake": q.name, "files": files, "batch_tag": (m.group(1) if m else None)})
    return rows


def read_records(key: str | None = None) -> dict:
    out = {"state": "GREEN", "mode": mode(), "via": VIA_TAG}
    out["lineage"] = lineage()
    out["docs"] = docs_index()
    out["intake"] = intake_index()
    heads = [ln.strip() for ln in _git("for-each-ref", "--format=%(refname:short)", "refs/remotes/origin").splitlines() if ln.strip()]
    out["lines"] = {"current": _git("rev-parse", "--abbrev-ref", "HEAD").strip(), "remote_heads": len(heads), "vdf_named": [h for h in heads if "vdf" in h.lower()]}
    if not out["lineage"]:
        out["state"], out["why"] = "NODATA", "git log 讀不到(不是倉或歷史為空)"
    if key:
        table = {"lineage": out["lineage"], "docs": out["docs"], "intake": out["intake"], "lines": out["lines"]}
        out["key"], out["hit"] = key, table.get(key)
        if out["hit"] is None:
            out["why"] = f"{key} 不是 records 的鍵(lineage|docs|intake|lines)"
    return out


# ────────────────────────── 連結 · 快照 · 差異 ──────────────────────────
def links(s: dict) -> list:
    L: list = []

    def add(kind, id_, path, state, **kw):
        p = None
        if path:
            sp = str(path)
            p = Path(sp) if (sp.startswith("/") or (len(sp) > 1 and sp[1] == ":")) else (VIA / sp)
        L.append({"kind": kind, "id": id_, "path": (rel(p) if p else ""), "state": lamp_of(state),
                  "sha12": (sha12(p) if p and p.is_file() else ""), "age_h": (age_h(p) if p and p.is_file() else None), **kw})
    po = s["policy"]
    add("book", "policy:laws", po.get("path"), po.get("state"), domain="policy", batch=po.get("batch"))
    lo = s["logic"]
    add("book", "logic:arch", lo["arch"].get("path"), lo["arch"].get("state"), domain="logic", rules=lo["arch"].get("rules"))
    add("book", "logic:cards", lo["cards"].get("path"), lo["cards"].get("state"), domain="logic", n=lo["cards"].get("n"))
    add("engine", "logic:chain_runner", lo["chain_runner"].get("tail"), lo["chain_runner"].get("state"), domain="logic")
    for b in s["factor"]["books"]:
        add("book", "factor:" + b["id"], b["path"], b["state"], domain="factor")
    for b in s["param"]["books"]:
        add("book", "param:" + str(b["id"]), b["path"], b["state"], domain="param", src=b["src"])
    en = s["engine"]
    add("report", "engine:chain", en["chain"].get("src"), en["chain"].get("state"), domain="engine", tally=en["chain"].get("tally"), red_split=en["chain"].get("red_split"))
    for fam, path in sorted((en.get("families_detail") or {}).items()):
        add("engine", "engine:" + fam, path, "GREEN", domain="engine")
    br = s["bridge"]
    add("law", "bridge:accel", "", "RED" if br["accel"]["missing"] else "GREEN", domain="bridge", has=br["accel"]["has"], tails=br["tails"], missing=br["accel"]["missing"][:20])
    add("law", "bridge:net", "", "RED" if br["net"]["callers_missing"] else "GREEN", domain="bridge", has=br["net"]["has"], callers=br["net"]["callers"], callers_missing=br["net"]["callers_missing"][:20])
    to = s["tool"]
    for name, t in (to.get("tools") or {}).items():
        add("tool", "tool:" + name, t.get("canon"), t.get("state"), domain="tool", variants=t.get("variants"), copies=len(t.get("copies") or []))
    for k in ("net_unified", "super_accel"):
        add("engine", "tool:" + k, (to.get("bridges") or {}).get(k), "GREEN" if (to.get("bridges") or {}).get(k) else "ABSENT", domain="tool")
    ho = s["handover"]
    add("doc", "handover:onepage", "docs/VIA_Handover_ONEPAGE.md", ho.get("state"), domain="handover", batch=(ho.get("onepage") or {}).get("docs_batch"))
    add("doc", "handover:root", str(ROOT / "VIA_HANDOVER_LATEST.md"), ho.get("state"), domain="handover", batch=(ho.get("onepage") or {}).get("root_batch"))
    for r in (s.get("records") or {}).get("docs") or []:
        add("doc", "records:" + Path(r["doc"]).name, r["doc"] if not r["doc"].startswith("../") else str(ROOT / r["doc"][3:]), "GREEN", domain="records", vdf_mentions=r["vdf_mentions"])
    for r in (s.get("records") or {}).get("intake") or []:
        add("intake", "records:intake:" + r["intake"], "functional modules/VDF/references/intake/" + r["intake"], "GREEN", domain="records", files=r["files"])
    la = s.get("launch") or {}
    pa, lc = (la.get("parity") or {}), (la.get("launchers") or {})
    add("script", "launch:boot_sh", "supportive modules/registry/via_boot_update.sh", "GREEN" if BOOT_SH.is_file() else "ABSENT", domain="launch", steps=pa.get("steps_sh"))
    add("script", "launch:boot_ps1", "supportive modules/registry/via_boot_update.ps1", pa.get("state") or "ABSENT", domain="launch", steps=pa.get("steps_ps1"), only_sh=(pa.get("only_sh") or [])[:20])
    add("script", "launch:fetch", lc.get("fetch_ps1"), "GREEN" if lc.get("fetch_ps1") else "ABSENT", domain="launch", cmd="via-vdffetch [年]")
    add("engine", "launch:lanes", lc.get("lanes"), "GREEN" if lc.get("lanes") else "ABSENT", domain="launch")
    up = s["upstream"]
    vc = up.get("vcgc")
    add("upstream", "vcgc", ("supportive modules/registry/" + vc["src"]) if isinstance(vc, dict) else "", "GREEN" if isinstance(vc, dict) else "ABSENT", domain="upstream",
        delegates=(vc or {}).get("delegates") if isinstance(vc, dict) else None)
    return L


def rc_of(s: dict) -> int:
    lamps = [s["lamps"][d] for d in RC_SCOPE]
    if any(x in ("RED", "ABSENT") for x in lamps):
        return 1
    if any(x in ("STALE", "NODATA", "GATED") for x in lamps):
        return 2
    return 0


def collect() -> dict:
    s: dict = {"schema": "VIA.VDF.SystemManager.v1", "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "me": ME, "version": VERSION, "born": BORN}
    s["policy"], s["logic"], s["factor"], s["param"] = read_policy(), read_logic(), read_factor(), read_param()
    s["engine"], s["bridge"], s["tool"], s["handover"] = read_engine(), read_bridge(), read_tool(), read_handover()
    s["records"] = read_records()
    s["launch"] = read_launch(probe=False)        # 啟動就緒(零子行程版;launch 動詞才現探)
    s["upstream"] = upstream()
    s["mode"] = mode()
    s["lamps"] = {d: lamp_of(s[d].get("state")) for d in DOMAINS}
    s["links"] = links(s)
    cnt: dict = {}
    for l in s["links"]:
        cnt[l["state"]] = cnt.get(l["state"], 0) + 1
    s["link_counts"] = cnt
    s["rc"] = rc_of(s)
    s["rc_name"] = {0: "GREEN", 1: "RED", 2: "STALE/NODATA"}[s["rc"]]
    return s


def sync(apply: bool = False) -> dict:
    s = collect()
    prev = _json(REPORTS() / "VDF_SYSTEM_latest.json") or {}
    pl = {l["id"]: l for l in prev.get("links", [])}
    cur = {l["id"]: l for l in s["links"]}
    diff: dict = {"NEW": [], "GONE": [], "CHANGED": [], "SAME": []}
    for k, l in cur.items():
        if k not in pl:
            diff["NEW"].append(k)
        elif (l.get("sha12"), l.get("state"), l.get("path")) != (pl[k].get("sha12"), pl[k].get("state"), pl[k].get("path")):
            diff["CHANGED"].append(k)
        else:
            diff["SAME"].append(k)
    diff["GONE"] = [k for k in pl if k not in cur]
    s["diff"] = {k: len(v) for k, v in diff.items()}
    s["diff_ids"] = {k: v[:60] for k, v in diff.items() if k != "SAME"}
    s["prev_ts"] = prev.get("ts")
    s["written"] = False
    if apply:
        s["written"] = True
        s["outputs"] = write_outputs(s)
    return s


# ────────────────────────── 產出(MD / HTML / JSON;零 CDN) ──────────────────────────
def _launch_rows(la: dict) -> list:
    """啟動就緒八項 → (項, 燈, 現況) 列;MD 與 HTML 同一份。"""
    py, lb, co, nt, lc, pa, ev, da = (la.get(k) or {} for k in ("python", "libs", "consent", "net_tool", "launchers", "parity", "evidence", "data"))
    have = sum(1 for k in lb.get("required", []) if (lb.get("have") or {}).get(k))
    cm = lc.get("cmds") or {}
    rgv, chv, lnv = ev.get("rungate") or {}, ev.get("chain") or {}, ev.get("lanes") or {}
    return [("家族境 python", "GREEN" if py.get("state") == "OK" else ("ABSENT" if py.get("state") == "ABSENT" else "STALE"), f"{py.get('python')}({py.get('env') or 'base'};{py.get('source') or py.get('why')})"),
            ("必要庫", ("GREEN" if lb.get("known") and not lb.get("missing") else ("ABSENT" if lb.get("missing") else "NODATA")), f"{have}/{len(lb.get('required', []))} 缺 {', '.join(lb.get('missing') or []) or '-'}({lb.get('src')})"),
            ("閘二三把尺", "GREEN" if not (co.get("scrape_split") or {}).get("blocked_direct") else "GATED",
             f"值 {(co.get('scrape_split') or {}).get('value')} · 字面 YES 尾版 {len((co.get('scrape_split') or {}).get('legacy_yes') or [])} 支 · 直呼受阻 {', '.join((co.get('scrape_split') or {}).get('blocked_direct') or []) or '-'} · 十道自帶 YES {(co.get('scrape_split') or {}).get('lanes_force_yes')}"),
            ("視窗限量", "STALE" if (la.get("hist_limit") or {}).get("set") else "GREEN", f"VIA_HIST_LIMIT {(la.get('hist_limit') or {}).get('n') if (la.get('hist_limit') or {}).get('set') else '未設'} · 啟動器跑完還原 {(la.get('hist_limit') or {}).get('launcher_restores')}"),
            ("增量目錄", {"FRESH": "GREEN", "STALE": "STALE"}.get(str((ev.get("plan_catalog") or {}).get("state")), "NODATA"), str((ev.get("plan_catalog") or {}).get("why") or "")[:140]),
            ("同意閘", "GREEN" if co.get("VIA_NET_CONSENT") == "OPEN" else "GATED", f"NET {co.get('VIA_NET_CONSENT')} · SCRAPE {co.get('VIA_SCRAPE_CONSENT')} · FRED_API_KEY {'在' if co.get('fred_key') else '不在'}(只讀;永不代設)"),
            ("網路工具", "GREEN" if nt.get("loads") and nt.get("aegis") else "ABSENT", f"{Path(nt.get('path') or '缺').name} 載入 {nt.get('loads')} net_ok {nt.get('net_ok')} · AegisNexus {'在' if nt.get('aegis') else '缺'}"),
            ("啟動器/短令/鏈", "GREEN" if lc.get("fetch_ps1") and lc.get("lanes") and lc.get("chain_runner") and not lc.get("cmds_missing") else ("RED" if not (lc.get("fetch_ps1") and lc.get("lanes") and lc.get("chain_runner")) else "STALE"),
             f"{Path(lc.get('fetch_ps1') or '缺').name} · cmd {'在' if lc.get('fetch_cmd') else '缺'} · {lc.get('register')} 短令 {sum(1 for v in cm.values() if v)}/{len(cm)} · 十道 {Path(lc.get('lanes') or '缺').name} · 鏈跑器 {Path(lc.get('chain_runner') or '缺').name}"),
            ("開機鏈雙載體", pa.get("state") or "ABSENT", f".sh {pa.get('steps_sh')} 步 · .ps1 {pa.get('steps_ps1')} 步 · 只在 .sh {pa.get('only_sh') or '-'} · 只在 .ps1 {pa.get('only_ps1') or '-'} · .ps1 家族境 python {pa.get('ps1_family_python')}"),
            ("上次實跑", "GREEN" if ev.get("boot_marker") or rgv.get("verdict") or chv.get("generated") else "NODATA", f"boot {ev.get('boot_marker')} {ev.get('boot_log')} · 能跑閘 {rgv.get('verdict') or rgv.get('state')}(vdf {rgv.get('vdf')})· 獨立鏈 {chv.get('state')} {chv.get('tally') or ''} · 十道 {lnv.get('state')}"),
            ("落點", "GREEN" if da.get("db_files") else "NODATA", f"output_hub {'在' if da.get('output_hub') else '缺'} · mega {'在' if da.get('mega') else '缺'} · 庫/parquet {da.get('db_files')} 件(0=沒抓過)")]


def to_markdown(s: dict) -> str:
    vc = s["upstream"].get("vcgc")
    o = [f"# VDF 子系統管理對接口 · {VIA_TAG}({BORN})· {s['ts']}", "",
         f"> 上接 VIA(VCGC {(vc or {}).get('src', 'ABSENT') if isinstance(vc, dict) else vc})· 下管 VDF 四庫 + 引擎面 + 橋/工具面 + 交接 · 模式 {s.get('mode')} · rc {s['rc']} {s['rc_name']}", "",
         "## 一 · 九域現況", "", "| 域 | 燈 | 正本 / 讀法 | 現況 |", "|---|---|---|---|"]
    po, lo, fa, pa, en, br, to, ho, rc_ = (s[d] for d in DOMAINS)
    o.append(f"| 政策 | {s['lamps']['policy']} | {po.get('path', '')} · read policy [id] | 律 {po.get('laws')} · lessons {po.get('lessons')} · VDF 律 {len(po.get('vdf_laws') or [])} / lessons {len(po.get('vdf_lessons') or [])} · 釘住 {sum(1 for v in (po.get('pinned') or {}).values() if v)}/{len(PINNED_LAWS)} · 批 {po.get('batch')} |")
    o.append(f"| 邏輯 | {s['lamps']['logic']} | 架構冊 + 卡書 + 鏈跑器 · read logic [arch\\|cards\\|chain_runner] | 架構規則 {lo['arch'].get('rules')} · 卡 {lo['cards'].get('n')}(冊有樹無 {len(lo['cards'].get('book_only') or [])} · 無版號 {len(lo['cards'].get('unversioned') or [])} · 樹有冊無 {len(lo['cards'].get('tree_only') or [])})· 鏈跑器 {Path(lo['chain_runner'].get('tail') or '缺').name} |")
    o.append(f"| 因子 | {s['lamps']['factor']} | 三本因子冊(寫者 ENG053)· read factor [id] | " + " · ".join(f"{b['id']} {b.get('params') or b.get('by_engine') or b.get('sections') or b['state']}" for b in fa['books']) + " |")
    o.append(f"| 參數 | {s['lamps']['param']} | via_params_central.BOOKS VDF 子集 + 規格冊自報 · read param [id] [--full] | 冊 {pa.get('n')} · 缺 {pa.get('absent')} |")
    ch = en.get("chain") or {}
    o.append(f"| 引擎 | {s['lamps']['engine']}(鏈跑器判準) | VIA_Reports/vdf_chain/VDFCHAIN_latest.json · read engine [family] | 鏈 {ch.get('state')} {ch.get('tally')} · RED 拆 {ch.get('red_split')} · 尾版家族 {en.get('families')}({en.get('families_ruler')})· 自測門 {en['selftest_door']['with']}/{en['selftest_door']['families']} · 卡書覆蓋 {en['cards']['covered']}/{en['cards']['n']} · 庫表 {en['db']['tables']} · 五面 {en.get('faces')} |")
    o.append(f"| 橋 | {s['lamps']['bridge']} | 尾版逐支;排除 {br['ruler']['exclusions']} · read bridge [family] | 加速器 {br['accel']['has']}/{br['tails']}(缺 {len(br['accel']['missing'])})· 網路 {br['net']['has']}/{br['tails']}(真擷取 {br['net']['callers']} · 缺 {len(br['net']['callers_missing'])})· 版史 {br['history']} |")
    o.append(f"| 工具 | {s['lamps']['tool']} | 正典位 + 副本 md5 + 橋尾版 · read tool [name] | " + " · ".join(f"{n} {t['state']}(副本 {len(t['copies'])} · 版本 {t['variants']})" for n, t in to['tools'].items()) + f" · 閘 {to['gate']['VIA_NET_CONSENT']}/{to['gate']['VIA_SCRAPE_CONSENT']} |")
    op = ho.get("onepage") or {}
    o.append(f"| 交接 | {s['lamps']['handover']} | docs + 掉球 · read handover | 一頁 批{op.get('docs_batch')} vs 律冊 批{op.get('laws_batch')} 同 {op.get('same')} · 逐批 {ho.get('latest_batch_doc')} · VDF 文 {ho.get('vdf_docs')} · 掉球 {(ho.get('dropped_balls') or {}).get('open')}/{(ho.get('dropped_balls') or {}).get('n')} |")
    ln = rc_.get("lineage") or {}
    o.append(f"| 紀錄 | {s['lamps']['records']} | git 尾註 + docs + references/intake · read records [lineage\\|docs\\|intake\\|lines] | session {len(ln)}(commit {sum(v.get('commits', 0) for v in ln.values())} · VDF {sum(v.get('vdf_commits', 0) for v in ln.values())})· VDF 文 {len(rc_.get('docs') or [])} · 收容包 {len(rc_.get('intake') or [])} · 活線 {rc_.get('lines', {}).get('remote_heads')} |")
    o += ["", "## 一之二 · 血脈(git 尾註量出來的)", "", "| session | commit | 提到 VDF | 批號範圍 | 最新主題 |", "|---|---|---|---|---|"]
    for sid, v in sorted(ln.items(), key=lambda kv: -kv[1].get("commits", 0)):
        o.append(f"| {sid} | {v.get('commits')} | {v.get('vdf_commits')} | {v.get('batch_min')}–{v.get('batch_max')}({v.get('batched_commits')}) | {v.get('latest')} |")
    la = s.get("launch") or {}
    o += ["", f"## 一之三 · 啟動就緒(launch;只量不動手)· {la.get('state')} rc {la.get('rc')} · {la.get('why')}", "", "| 項 | 燈 | 現況 |", "|---|---|---|"]
    for zh, lamp, txt in _launch_rows(la):
        o.append(f"| {zh} | {lamp} | {txt} |")
    o += [""] + [f"- 下一步 {i}. {ln}" for i, ln in enumerate(la.get("next") or [], 1)]
    up = s["upstream"]
    o += ["", "## 二 · 上行七處自審(不假綠)", "", "| 處 | 在 | 說明 |", "|---|---|---|"]
    zh = {"spec": "規格項 vdf_system", "grid": "格子站(newest VDF_SystemManager_v*)", "register": "短令 via-vdfsys(L70 未許可前=否)", "deck": "Deck 任務 vdf_system",
          "manager": "Manager 正式名稱", "inventory": "中央元件冊", "handover": "交接文提及"}
    for k in SEVEN:
        o.append(f"| {zh[k]} | {'✅' if up['seven'].get(k) else '❌'} | {up.get(k) if not isinstance(up.get(k), bool) else ''} |")
    o.append(f"| VCGC | {'✅' if isinstance(up.get('vcgc'), dict) else '❌'} | {up.get('vcgc')} · 總管理器 {up.get('via_manager')} |")
    o += ["", f"## 三 · 連結表({len(s['links'])} 條;現解尾版 · 現算 sha · 現量年齡)", "", "| 域 | 種 | id | 燈 | 路徑 | sha12 | 齡 h |", "|---|---|---|---|---|---|---|"]
    for l in s["links"]:
        o.append(f"| {l.get('domain')} | {l['kind']} | {l['id']} | {l['state']} | {l['path']} | {l['sha12']} | {l['age_h'] if l['age_h'] is not None else '-'} |")
    if s.get("diff"):
        o += ["", f"## 四 · 與上次快照({s.get('prev_ts') or '無'})的差異:{s['diff']}", ""]
        for k, v in (s.get("diff_ids") or {}).items():
            if v:
                o.append(f"- {k}:{', '.join(v[:30])}" + (" …" if len(v) > 30 else ""))
    o += ["", "## 律", "", "- L20 唯一對接口:VIA 往下讀 VDF 一律經本口;本口不複製任何規則(L05)。",
          "- 批102 全樹加速器橋 · L09 網路只認 Nexus:橋域每一跑逐支量,尾版缺一支=RED;版史只報不判。",
          "- L07/L08 同意閘只讀現態,永不代設;L16 缺件≠缺料≠過期≠壞掉;L04 尾版律;L17 自測零污染;零網路 · 零寫庫 · 零 CDN。"]
    return "\n".join(o) + "\n"


def to_html(s: dict, md: str, out: Path) -> Path:
    rows9 = []
    for d in DOMAINS:
        x = s[d]
        rows9.append([DOMAIN_ZH[d], {"t": s["lamps"][d], "s": s["lamps"][d]}, str(x.get("why") or x.get("path") or x.get("src") or "")[:120]])
    rows7 = [[k, "✅" if s["upstream"]["seven"].get(k) else "❌", str(s["upstream"].get(k))[:60]] for k in SEVEN]
    la = s.get("launch") or {}
    rowsA = [[zh, {"t": lamp, "s": lamp}, txt[:160]] for zh, lamp, txt in _launch_rows(la)] + [["下一步", {"t": la.get("state") or "?", "s": la.get("state") or "NA"}, " ｜ ".join(la.get("next") or [])[:400]]]
    rowsL = [[l.get("domain"), l["kind"], l["id"], {"t": l["state"], "s": l["state"]}, l["path"], l["sha12"], str(l["age_h"] if l["age_h"] is not None else "-")] for l in s["links"]]
    kpis = [f"rc {s['rc']} {s['rc_name']}", f"連結 {len(s['links'])}", " · ".join(f"{k} {v}" for k, v in s["link_counts"].items())]
    try:
        m = _mod("m173", newest(REG, "CGC_MDL173_MatrixReportSpec_v*.py"))
        if m is None:
            raise RuntimeError("MDL173 缺")
        body = (m.html_table(["域", "燈", "正本 / 現況"], rows9, caption="一 · 九域現況", center_cols={1})
                + m.html_table(["項", "燈", "現況"], rowsA, caption=f"一之三 · 啟動就緒(launch;只量不動手)· {la.get('state')} rc {la.get('rc')}", center_cols={1})
                + m.html_table(["處", "在", "說明"], rows7, caption="二 · 上行七處自審(不假綠)", center_cols={1})
                + m.html_table(["域", "種", "id", "燈", "路徑", "sha12", "齡 h"], rowsL, caption=f"三 · 連結表({len(rowsL)})", center_cols={3}, num_cols={6}))
        return m.page_html(body, title=f"VDF 子系統管理對接口 · {VIA_TAG}", subtitle=f"{s['ts']} · {BORN} · 上接 VCGC · 下管四庫+橋/工具 · 零 CDN", md=md,
                           payload={k: v for k, v in s.items() if k != "links"}, kpis=kpis, law="L20 唯一對接口 · L05 零 Hydra · 批102/L09 橋律 · L16 誠實四態 · L04 尾版律", out=out)
    except Exception:
        def tbl(h, rows):
            def cell(c):
                return _html.escape(str(c.get("t") if isinstance(c, dict) else c))
            return ("<table><tr>" + "".join(f"<th>{_html.escape(x)}</th>" for x in h) + "</tr>"
                    + "".join("<tr>" + "".join(f"<td>{cell(c)}</td>" for c in r) + "</tr>" for r in rows) + "</table>")
        page = ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
                f"<title>VDF 子系統管理對接口 {VIA_TAG}</title><style>body{{font-family:system-ui,sans-serif;font-size:10.5px;margin:12px;background:#0f172a;color:#e5e7eb}}"
                "table{border-collapse:collapse;margin:8px 0}td,th{border:1px solid #334155;padding:2px 6px;text-align:left}h1{font-size:15px}h2{font-size:12px}</style></head><body>"
                f"<h1>VDF 子系統管理對接口 · {VIA_TAG} · {s['ts']} · {' · '.join(kpis)}</h1>"
                "<h2>一 · 九域現況</h2>" + tbl(["域", "燈", "正本 / 現況"], rows9) + "<h2>一之三 · 啟動就緒</h2>" + tbl(["項", "燈", "現況"], rowsA) + "<h2>二 · 上行七處自審</h2>" + tbl(["處", "在", "說明"], rows7)
                + f"<h2>三 · 連結表({len(rowsL)})</h2>" + tbl(["域", "種", "id", "燈", "路徑", "sha12", "齡 h"], rowsL)
                + "<p>MDL173 殼缺席 → 最小殼(講明);零 CDN 零外連。</p></body></html>")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")
        return out


def write_outputs(s: dict) -> dict:
    d = REPORTS()
    d.mkdir(parents=True, exist_ok=True)
    md = to_markdown(s)
    (d / "VDF_SYSTEM_latest.json").write_text(json.dumps(s, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    (d / "VDF_SYSTEM_latest.md").write_text(md, encoding="utf-8")
    page = to_html(s, md, d / f"VIA_VDF_SystemManager_v{VERSION}.html")
    with (d / "LEDGER.tsv").open("a", encoding="utf-8") as f:
        f.write("\t".join([s["ts"], VIA_TAG, s["rc_name"], str(len(s["links"])), json.dumps(s.get("diff") or {}, ensure_ascii=False), json.dumps(s["lamps"], ensure_ascii=False)]) + "\n")
    return {"json": rel(d / "VDF_SYSTEM_latest.json"), "md": rel(d / "VDF_SYSTEM_latest.md"), "html": rel(page), "ledger": rel(d / "LEDGER.tsv")}


# ────────────────────────── 統一讀口(VIA 往下讀 VDF 一律經此) ──────────────────────────
READERS = {"policy": read_policy, "logic": read_logic, "factor": read_factor, "param": read_param, "engine": read_engine,
           "bridge": read_bridge, "tool": read_tool, "handover": read_handover, "records": read_records, "upstream": upstream,
           "launch": lambda key=None: read_launch(probe=(str(key or "").lower() == "probe"))}   # read launch [probe]:probe 才起子行程現探


def read(domain: str, key: str | None = None, full: bool = False) -> dict:
    f = READERS.get(str(domain).lower())
    if f is None:
        return {"state": "NODATA", "why": f"{domain} 不是本口的域({'|'.join(READERS)})", "via": VIA_TAG}
    if domain == "param":
        r = f(key, full)
    elif domain in ("handover", "upstream"):
        r = f()
    else:
        r = f(key)
    r.setdefault("via", VIA_TAG)
    return r


def catalog() -> list:
    s = collect()
    up = "VCGC status/onepage/page(v0119 起經本口)"
    return [
        {"domain": "policy", "zh": "政策", "canon": s["policy"].get("path"), "verb": "read policy [id]", "consumer": up, "lamp": s["lamps"]["policy"]},
        {"domain": "logic", "zh": "邏輯", "canon": f"{s['logic']['arch'].get('path')} + {s['logic']['cards'].get('path')} + {s['logic']['chain_runner'].get('tail')}", "verb": "read logic [arch|cards|chain_runner]", "consumer": up, "lamp": s["lamps"]["logic"]},
        {"domain": "factor", "zh": "因子", "canon": " + ".join(b["path"] for b in s["factor"]["books"]), "verb": "read factor [id]", "consumer": "ENG053(寫者)· " + up, "lamp": s["lamps"]["factor"]},
        {"domain": "param", "zh": "參數", "canon": f"{s['param'].get('n')} 本(via_params_central.BOOKS VDF 子集 + 規格冊自報)", "verb": "read param [id] [--full]", "consumer": "via-params / InputConsole", "lamp": s["lamps"]["param"]},
        {"domain": "engine", "zh": "引擎", "canon": s["engine"]["chain"].get("src"), "verb": "read engine [family]", "consumer": "格子 / 匯流排 / via-vdfchain(本口只讀快照)", "lamp": s["lamps"]["engine"]},
        {"domain": "bridge", "zh": "橋", "canon": "尾版逐支(排除清單與真擷取判定委派 CGC_MDL124)", "verb": "read bridge [family]", "consumer": "MDL156 加速器控制面 / MDL124 橋掃器 / 打包就緒閘 MDL174 ④", "lamp": s["lamps"]["bridge"]},
        {"domain": "tool", "zh": "工具", "canon": " + ".join(t["canon"] for t in s["tool"]["tools"].values()), "verb": "read tool [name]", "consumer": "SUP_MDL740 / SUP_MDL737 / VIA_SuperAccel_Module", "lamp": s["lamps"]["tool"]},
        {"domain": "handover", "zh": "交接", "canon": "docs/VIA_Handover_ONEPAGE.md + docs/VIA_DroppedBalls_B*.md + VDF 文", "verb": "read handover", "consumer": "VCGC 交接段", "lamp": s["lamps"]["handover"]},
        {"domain": "records", "zh": "紀錄", "canon": "git 尾註 + docs + functional modules/VDF/references/intake", "verb": "read records [lineage|docs|intake|lines]", "consumer": "接手者", "lamp": s["lamps"]["records"]},
        {"domain": "launch", "zh": "啟動", "canon": "Invoke-VIA-VdfFetch-v*.ps1(via-vdffetch)+ via_boot_update.sh/.ps1 + CGC_MDL134/170/136/137", "verb": "launch [--no-probe] · read launch [probe]", "consumer": "操作員(via-vdfsys launch)· 格子站「VDF 啟動就緒」", "lamp": s["launch"]["state"]},
        {"domain": "upstream", "zh": "上行", "canon": str(s["upstream"].get("vcgc")), "verb": "read upstream", "consumer": "七處自審:" + json.dumps(s["upstream"]["seven"], ensure_ascii=False), "lamp": "-"},
    ]


# ────────────────────────── 畫面 ──────────────────────────
def _print_status(s: dict) -> None:
    vc = s["upstream"].get("vcgc")
    print(f"[VDF_SystemManager] {VIA_TAG} · {BORN} · 模式 {s.get('mode')} · {s['ts']} · 上接 VCGC {(vc or {}).get('src', 'ABSENT') if isinstance(vc, dict) else vc}")
    po, lo, fa, pa, en, br, to, ho, rc_ = (s[d] for d in DOMAINS)
    print(f"  政策 {s['lamps']['policy']:6s} 律 {po.get('laws')} · lessons {po.get('lessons')} · VDF 律 {len(po.get('vdf_laws') or [])} / lessons {len(po.get('vdf_lessons') or [])} · 釘住 {sum(1 for v in (po.get('pinned') or {}).values() if v)}/{len(PINNED_LAWS)} · 批 {po.get('batch')} · 尾 {po.get('last_law')}/{po.get('last_lesson')}")
    print(f"  邏輯 {s['lamps']['logic']:6s} 架構冊規則 {lo['arch'].get('rules')} · 卡書 {lo['cards'].get('n')} 張(冊有樹無 {len(lo['cards'].get('book_only') or [])} · 無版號 {len(lo['cards'].get('unversioned') or [])} · 樹有冊無 {len(lo['cards'].get('tree_only') or [])} · 路徑不在 {len(lo['cards'].get('path_gone') or [])})· 鏈跑器 {Path(lo['chain_runner'].get('tail') or '缺').name}" + (f" · {lo.get('why')}" if lo.get('why') else ""))
    print(f"  因子 {s['lamps']['factor']:6s} " + " · ".join(f"{b['id']} " + (f"參數 {b['params']}" if 'params' in b else f"對映 引擎 {b['by_engine']} 參數 {b['by_param']} 缺口 {b['gaps']}" if 'by_engine' in b else f"段 {b.get('sections')}" if 'sections' in b else b['state']) for b in fa['books']))
    print(f"  參數 {s['lamps']['param']:6s} 冊 {pa.get('n')} · 缺 {pa.get('absent')} · 出處 {pa.get('src')}")
    ch = en.get("chain") or {}
    print(f"  引擎 {s['lamps']['engine']:6s} 鏈 {ch.get('state')} {ch.get('tally') or ch.get('why')} · RED 拆 {ch.get('red_split')}(燈照抄鏈跑器)· 尾版家族 {en.get('families')}({en.get('families_ruler')})· 自測門 {en['selftest_door']['with']}/{en['selftest_door']['families']} · 卡書覆蓋 {en['cards']['covered']}/{en['cards']['n']} · 庫表 {en['db']['tables']}(列 {en['db']['rows_seen']})· 五面 {en.get('faces')}")
    print(f"  橋   {s['lamps']['bridge']:6s} 加速器 {br['accel']['has']}/{br['tails']}(缺 {br['accel']['missing'] or 0})· 網路 {br['net']['has']}/{br['tails']}(真擷取 {br['net']['callers']} · 真擷取缺橋 {br['net']['callers_missing'] or 0})· 排除 {br['excluded']}({br['ruler']['exclusions']})· 版史 {br['history']}")
    print(f"  工具 {s['lamps']['tool']:6s} " + " · ".join(f"{n} {t['state']}(正典 {t['canon'].split('/')[-2]}/ · 副本 {len(t['copies'])} · 版本 {t['variants']})" for n, t in to['tools'].items()) + f" · 橋 {Path(to['bridges'].get('net_unified') or '缺').name}/{Path(to['bridges'].get('super_accel') or '缺').name} · 控制面 {to['accel_control'].get('state')} · 閘 NET {to['gate']['VIA_NET_CONSENT']} SCRAPE {to['gate']['VIA_SCRAPE_CONSENT']}(只讀,永不代設)")
    op = ho.get("onepage") or {}
    print(f"  交接 {s['lamps']['handover']:6s} 一頁 批{op.get('docs_batch')} vs 律冊 批{op.get('laws_batch')} 同 {op.get('same')} · 逐批 {ho.get('latest_batch_doc')} · B 文 {ho.get('latest_b_doc')} · VDF 文 {ho.get('vdf_docs')} · 掉球 {(ho.get('dropped_balls') or {}).get('open')}/{(ho.get('dropped_balls') or {}).get('n')}" + (f" · {ho.get('why')}" if ho.get("why") else ""))
    ln = rc_.get("lineage") or {}
    print(f"  紀錄 {s['lamps']['records']:6s} session {len(ln)}(commit {sum(v.get('commits', 0) for v in ln.values())} · 提到 VDF {sum(v.get('vdf_commits', 0) for v in ln.values())})· VDF 文 {len(rc_.get('docs') or [])} · 收容包 {len(rc_.get('intake') or [])} · 活線 {rc_.get('lines', {}).get('remote_heads')}(本線 {rc_.get('lines', {}).get('current')})")
    la = s.get("launch") or {}
    lpa, llb, lco = la.get("parity") or {}, la.get("libs") or {}, la.get("consent") or {}
    print(f"  啟動 {str(la.get('state')):6s} rc {la.get('rc')} · {la.get('why')} · python {(la.get('python') or {}).get('state')} · 必要庫缺 {', '.join(llb.get('missing') or []) or '-'}({'量到' if llb.get('known') else '未量'})· 閘 NET {lco.get('VIA_NET_CONSENT')} · 雙載體 {lpa.get('state')}(.sh {lpa.get('steps_sh')} · .ps1 {lpa.get('steps_ps1')})· 下一步 {(la.get('next') or ['-'])[0][:60]}")
    up = s["upstream"]
    print(f"  上行 七處 {up.get('done')}/{len(SEVEN)} {json.dumps(up.get('seven'), ensure_ascii=False)} · VCGC 委派 {(up.get('vcgc') or {}).get('delegates') if isinstance(up.get('vcgc'), dict) else up.get('vcgc')}")
    print(f"  [計] 連結 {len(s['links'])} · {s['link_counts']} · 本口 rc {s['rc']} {s['rc_name']}(看四庫+橋+工具+交接;引擎面不折進 rc)" + (f" · 差異 {s['diff']}" if s.get("diff") else ""))


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    as_json = "--json" in a
    full = "--full" in a
    if "--standalone" in a:
        _FORCE_STANDALONE["on"] = True
    a = [x for x in a if x not in ("--json", "--full", "--standalone")]
    verb = a[0] if a else "status"
    if verb == "status":
        s = collect()
        _print_status(s)
        if as_json:
            print(json.dumps({k: v for k, v in s.items() if k != "links"}, ensure_ascii=False, indent=1, default=str))
        return s["rc"]
    if verb in ("engines", "bridges", "tools"):
        dom = {"engines": "engine", "bridges": "bridge", "tools": "tool"}[verb]
        r = read(dom, a[1] if len(a) > 1 else None)
        if verb == "engines":
            for fam, p in sorted((r.get("families_detail") or {}).items()):
                print(f"  {fam:44s} {p}")
            print(f"  [計] 尾版家族 {r.get('families')}({r.get('families_ruler')})· 自測門 {r['selftest_door']['with']}/{r['selftest_door']['families']} · 卡書 {r['cards']['covered']}/{r['cards']['n']} · 五面 {r.get('faces')}")
        elif verb == "bridges":
            for x in r.get("rows", []):
                print(f"  {'A' if x['accel'] else '-'}{'N' if x['net'] else '-'}{'c' if x['net_caller'] else '.'} {x['family']:44s} {x['tail']}" + (f"  [排除:{x['excluded']}]" if x["excluded"] else ""))
            print(f"  [計] {r['state']} · 加速器 {r['accel']['has']}/{r['tails']} 缺 {r['accel']['missing']} · 網路 {r['net']['has']}/{r['tails']} 真擷取 {r['net']['callers']} 缺 {r['net']['callers_missing']} · 排除 {r['excluded']} · 版史 {r['history']} · 尺 {r['ruler']}")
        else:
            for n, t in r.get("tools", {}).items():
                print(f"  {n:24s} {t['state']:6s} 正典 {t['canon']} sha {t['sha12']} · 副本 {len(t['copies'])} · 版本 {t['variants']}")
                for c in t["copies"]:
                    print(f"      {'★' if c['canon'] else ' '} {c['sha12']} {c['bytes']:>8} {c['path']}")
            print(f"  [計] {r['state']} · 橋 {r['bridges']} · 控制面 {r['accel_control'].get('state')} · 閘 {r['gate']}" + (f" · {r.get('why')}" if r.get("why") else ""))
        if as_json:
            print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
        return 0 if lamp_of(r.get("state")) == "GREEN" else (2 if lamp_of(r.get("state")) in ("NODATA", "STALE", "GATED") else 1)
    if verb == "launch":
        r = read_launch(probe=("--no-probe" not in a))
        _print_launch(r)
        if as_json:
            print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
        return r["rc"]
    if verb == "records":
        r = read_records()
        print(f"  模式 {r['mode']} · session {len(r['lineage'])} · VDF 文 {len(r['docs'])} · 收容包 {len(r['intake'])} · 活線 {r['lines'].get('remote_heads')}(本線 {r['lines'].get('current')})")
        for sid, v in sorted(r["lineage"].items(), key=lambda kv: -kv[1]["commits"]):
            print(f"    {sid:34s} commit {v['commits']:4d} · 提到 VDF {v['vdf_commits']:3d} · 批 {v['batch_min']}–{v['batch_max']}({v['batched_commits']})· 最新:{v['latest']}")
        for d in r["docs"]:
            print(f"    文 {d['doc']}(VDF×{d['vdf_mentions']} · {d['bytes']} B)")
        for i in r["intake"]:
            print(f"    收容 {i['intake']}(檔 {i['files']} · b{i['batch_tag']})")
        if as_json:
            print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
        return 0 if r["state"] == "GREEN" else 2
    if verb == "catalog":
        rows = catalog()
        for r in rows:
            print(f"  {r['zh']} {r['lamp']:6s} 正本 {r['canon']} · 讀法 {r['verb']} · 上游 {r['consumer']}")
        if as_json:
            print(json.dumps(rows, ensure_ascii=False, indent=1, default=str))
        return 0
    if verb == "links":
        s = collect()
        for l in s["links"]:
            print(f"  {str(l.get('domain')):9s} {l['kind']:8s} {l['state']:6s} {l['id']:44s} {l['path']} {l['sha12']} {l['age_h'] if l['age_h'] is not None else '-'}")
        print(f"  [計] {len(s['links'])} 條 · {s['link_counts']}")
        if as_json:
            print(json.dumps(s["links"], ensure_ascii=False, indent=1, default=str))
        return s["rc"]
    if verb == "read":
        if len(a) < 2:
            print("  用法:read <policy|logic|factor|param|engine|bridge|tool|handover|records|upstream|launch> [key] [--full]")
            return 2
        r = read(a[1], a[2] if len(a) > 2 else None, full)
        print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
        return 0 if lamp_of(r.get("state")) == "GREEN" else (2 if lamp_of(r.get("state")) in ("NODATA", "STALE", "GATED") else 1)
    if verb in ("sync", "page"):
        apply = ("--apply" in a) or verb == "page"
        s = sync(apply=apply)
        _print_status(s)
        for k, v in (s.get("diff_ids") or {}).items():
            if v:
                print(f"  {k}:{', '.join(v[:12])}" + (" …" if len(v) > 12 else ""))
        if s["written"]:
            print(f"  [落] {s['outputs']}(只落 VIA_Reports;不入 git)")
        else:
            print("  [乾跑] 一個位元都沒寫;--apply 才落快照(json/md/html + LEDGER.tsv)")
        return s["rc"]
    print(__doc__.split("用法:", 1)[-1])
    return 2


# ────────────────────────── 自測(卅一檢;零網路;只寫暫存) ──────────────────────────
def selftest() -> int:
    import tempfile
    fails: list = []
    src = Path(__file__).read_text(encoding="utf-8", errors="replace")
    body = src.split("def selftest(")[0]        # 自測不讀自測本身的字串(LL:批504/506)
    n = [0]

    def chk(name, cond, note=""):
        n[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    print(f"=== VDF 子系統管理對接口({VIA_TAG})· 自測(零網路;只寫暫存;檢數現場計)===")
    os.environ["VIA_SELFTEST"] = "1"
    real_dir = VIA / "VIA_Reports" / "vdf_system"
    marker_before = sorted(p.name for p in real_dir.glob("*")) if real_dir.is_dir() else []
    gate_before = (os.environ.get("VIA_NET_CONSENT"), os.environ.get("VIA_SCRAPE_CONSENT"))
    with tempfile.TemporaryDirectory() as td:
        os.environ["VIA_VDFSYS_REPORTS"] = td
        try:
            chk("① 尾版律:版號由檔名讀出,不寫死(VERSION 四碼 · FAMILY 無版號)", re.fullmatch(r"\d{4}", VERSION) is not None and FAMILY == "VDF_SystemManager" and ("VERSION = ME.rsplit" in body))
            chk("② 三座正典橋在位:加速器橋 + 網路橋(所有 VDF 都要加裝網路工具——本口自己也是 VDF 件;表頭才算)+ JSON 讀寫正典橋(bind_read 綁定不是 def)", "# ===== [VIA:ACCEL-BRIDGE:v0100]" in body and "# ===== [VIA:NET-BRIDGE:v0100]" in body and "def _via_net" in body and "[VIA:JSONIO-BRIDGE:v0100]" in body and "bind_read()" in body)
            s = collect()
            chk("③ 九域齊 + 每域一盞燈且燈名出自燈號冊(len(LAMPS) 現場數)", set(s["lamps"]) == set(DOMAINS) and all(v in LAMPS for v in s["lamps"].values()) and len(LAMPS) == 6, f"{s['lamps']}")
            po = s["policy"]
            chk("④ 政策:律冊在位 · 律/lessons >0 · VDF 子集 >0 · 釘住的六條(L07/L08/L09/L35/L90/L99)都在 · sha12 十二碼",
                po["state"] == "GREEN" and po["laws"] > 0 and po["lessons"] > 0 and len(po["vdf_laws"]) > 0 and all(po["pinned"].values()) and len(po["sha12"]) == 12,
                f"(律 {po['laws']} · VDF 律 {len(po['vdf_laws'])} · 釘住 {po['pinned']})")
            lo = s["logic"]
            chk("⑤ 邏輯:架構冊在位(規則 >0)· 卡書在位(卡 ≥40)· 冊樹同不同步**量出來講**(STALE 不是 RED)· 鏈跑器 CGC_MDL170 尾版在位",
                lo["arch"]["state"] == "GREEN" and (lo["arch"].get("rules") or 0) > 0 and lo["cards"].get("n", 0) >= 40 and lo["cards"]["state"] in ("GREEN", "STALE")
                and lo["chain_runner"]["state"] == "GREEN" and lo["state"] in ("GREEN", "STALE"),
                f"(規則 {lo['arch'].get('rules')} · 卡 {lo['cards'].get('n')} · 冊有樹無 {lo['cards'].get('book_only')} · 無版號 {lo['cards'].get('unversioned')} · 樹有冊無 {lo['cards'].get('tree_only')} · 尺 {lo['cards'].get('ruler')})")
            fa = s["factor"]
            chk("⑥ 因子:三本冊都在(統一參數 · 參數登記冊 params>500 · 參數×引擎對映 by_engine>10)· 寫者 ENG053 本口只讀(源碼無 build_map 呼叫)",
                fa["state"] == "GREEN" and next(b for b in fa["books"] if b["id"] == "VDF_PARAM_REG").get("params", 0) > 500
                and next(b for b in fa["books"] if b["id"] == "VDF_PARAM_ENGINE_MAP").get("by_engine", 0) > 10 and "build_map(" not in body,
                f"({[ (b['id'], b.get('params') or b.get('by_engine') or b.get('sections')) for b in fa['books'] ]})")
            pa = s["param"]
            vpc = _params_central()
            ids_central = {b["id"] for b in getattr(vpc, "BOOKS", [])} if vpc else set()
            sub = [b for b in pa["books"] if b["src"] == "via_params_central.BOOKS"]
            chk("⑦ 參數:VDF 子集 ⊆ via_params_central.BOOKS(抄到函式才算出處 LL316)· 子集 ≥10 本 · 規格冊自報(defaults.start / 逐項 / 整類)在列 · 缺 0",
                len(sub) >= 10 and all(b["id"] in ids_central for b in sub) and any(b["id"] == "SPEC:vdf" and b.get("summary", {}).get("defaults.start") for b in pa["books"]) and pa["state"] == "GREEN",
                f"(子集 {len(sub)} · 冊 {pa['n']} · 缺 {pa['absent']} · defaults.start {next((b['summary']['defaults.start'] for b in pa['books'] if b['id'] == 'SPEC:vdf'), None)})")
            en = s["engine"]
            chk("⑧ 引擎:尾版家族用 VCGC._tail_files 同一把尺(VCGC 缺席才退自家 glob 並講明)· VDF 家族 ≥40 · 五面計數齊 · 卡書覆蓋數 ≤ 卡數 · 庫表冊 VDF 表 >0",
                (en["families_ruler"] == "VCGC._tail_files" or _vcgc() is None) and en["families"] >= 40 and all(k in en["faces"] for k in ("spec", "grid", "register", "deck", "inventory_active"))
                and en["cards"]["covered"] <= en["cards"]["n"] and en["db"]["tables"] > 0,
                f"(家族 {en['families']} · 尺 {en['families_ruler']} · 五面 {en['faces']} · 卡書 {en['cards']} · 庫表 {en['db']['tables']})")
            table = [(0, "", "GREEN"), (1, "ModuleNotFoundError: No module named 'duckdb'", "ABSENT"), (1, "VIA_NET_CONSENT 未設 GATED", "GATED"), (2, "SKIP 只攤開", "NODATA"), (4, "", "GATED"), (1, "AssertionError 壞了", "RED")]
            chk("⑨ 四態表驅動:rc0→GREEN · import 缺件→ABSENT · 閘/rc4→GATED · 缺料/rc2→NODATA · 其餘→RED(負控:壞就是壞)", all(classify(rc, t) == exp for rc, t, exp in table))
            ch = en.get("chain") or {}
            chk("⑩ 引擎面照抄鏈跑器的燈、只拆不改:快照在則 red_split 各鍵 ∈ 燈號冊且總和 == tally.RED;不在則 NODATA 誠實(容器沒跑過鏈就是沒跑過)",
                (ch.get("state") == "NODATA") or (all(k in LAMPS for k in ch.get("red_split", {})) and sum(ch.get("red_split", {}).values()) == (ch.get("tally") or {}).get("RED", 0)),
                f"(鏈 {ch.get('state')} · {ch.get('tally') or ch.get('why')})")
            chk("⑪ 本口 rc 只看四庫+橋+工具+交接(RC_SCOPE 不含 engine / records):引擎面 RED 不折進 rc", "engine" not in RC_SCOPE and "records" not in RC_SCOPE and rc_of(s) == s["rc"], f"(rc {s['rc']} {s['rc_name']} · 引擎燈 {s['lamps']['engine']})")
            n0 = len(list(Path(td).glob("*")))
            s1 = sync(apply=False)
            chk("⑫ sync 乾跑一個位元都不寫(暫存夾前後檔數相同)且 diff 全 NEW(無上次快照)", len(list(Path(td).glob("*"))) == n0 and s1["diff"]["NEW"] == len(s1["links"]) and s1["written"] is False)
            s2 = sync(apply=True)
            files = sorted(p.name for p in Path(td).glob("*"))
            page = (Path(td) / f"VIA_VDF_SystemManager_v{VERSION}.html").read_text(encoding="utf-8", errors="replace")
            chk("⑬ sync --apply 落三件 + 台帳(json/md/html/LEDGER.tsv)且頁零 CDN 零外連",
                {"VDF_SYSTEM_latest.json", "VDF_SYSTEM_latest.md", f"VIA_VDF_SystemManager_v{VERSION}.html", "LEDGER.tsv"} <= set(files) and "http://" not in page and "https://" not in page.replace("https://json-schema", "") and "<script src" not in page, f"{files}")
            s3 = sync(apply=False)
            chk("⑭ 第二次 sync 對上一次快照全 SAME(NEW 0 · GONE 0 · CHANGED 0)", s3["diff"]["SAME"] == len(s3["links"]) and s3["diff"]["NEW"] == 0 and s3["diff"]["GONE"] == 0 and s3["diff"]["CHANGED"] == 0, f"{s3['diff']}")
            lp = Path(td) / "VDF_SYSTEM_latest.json"
            j = json.loads(lp.read_text(encoding="utf-8"))
            j["links"][0]["sha12"] = "deadbeef0000"
            j["links"].append({"id": "ghost:link", "kind": "book", "path": "x", "state": "GREEN", "sha12": "", "age_h": None})
            lp.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
            s4 = sync(apply=False)
            chk("⑮ 差異負控:改一條 sha → CHANGED 1;快照多一條鬼連結 → GONE 1(會過的檢等於沒有檢 LL89)", s4["diff"]["CHANGED"] == 1 and s4["diff"]["GONE"] == 1 and "ghost:link" in s4["diff_ids"]["GONE"], f"{s4['diff']}")
            r1, r2 = read("policy", "L09"), read("policy", "L99999")
            chk("⑯ 統一讀口 read('policy','L09') 命中且回 id;讀不存在的 id → NODATA 不炸;每個回傳都署名 via", (r1.get("hit") or {}).get("id") == "L09" and r2["state"] == "NODATA" and r1.get("via") == VIA_TAG and r2.get("via") == VIA_TAG)
            pid = next((b["id"] for b in pa["books"] if b["exists"] and b["src"] == "via_params_central.BOOKS"), None)
            r3, r4 = read("param", pid), read("param", pid, full=True)
            chk("⑰ read param <id> 回摘要不回內容,--full 才回內容;讀不存在的域 → NODATA", pid is not None and "content" not in (r3.get("hit") or {}) and "summary" in (r3.get("hit") or {}) and "content" in (r4.get("hit") or {}) and read("nope")["state"] == "NODATA")
            up = s["upstream"]
            reg_p = newest(VIA, "Register-VIA-Commands-v*.ps1")
            reg_has = bool(reg_p) and ("function global:via-vdfsys" in _src(reg_p))
            chk("⑱ 上行七處自審回七鍵且不假綠:Register 旗標必須**等於**冊上有沒有 via-vdfsys(登了 True、沒登 False,量的不是釘的);VCGC 在位時 delegates 為 bool", set(up["seven"]) == set(SEVEN) and up["seven"]["register"] is reg_has and (not isinstance(up.get("vcgc"), dict) or isinstance(up["vcgc"].get("delegates"), bool)), f"(Register {reg_p.name if reg_p else '缺'} 有 via-vdfsys={reg_has}){up['seven']}")
            code = re.sub(r"#.*", "", body)
            chk("⑲ 零網路(原始碼無 requests/urllib.request/http.client/socket 呼叫;排除註解與自測段)", not re.search(r"\b(requests\.|urllib\.request|http\.client|socket\.)", code))
            chk("⑳ 零寫庫(原始碼無 duckdb.connect / CREATE TABLE / INSERT INTO;只讀冊與快照)", not re.search(r"duckdb\.connect|CREATE TABLE|INSERT INTO", code))
            md = (Path(td) / "VDF_SYSTEM_latest.md").read_text(encoding="utf-8")
            chk("㉑ 一頁 MD 九域每域一行(表列)+ 七處表 + 連結表;燈名全出自燈號冊", all(f"| {DOMAIN_ZH[d]} |" in md for d in DOMAINS) and "七處自審" in md and f"連結表({len(s['links'])}" in md)
            ho = s["handover"]
            chk("㉒ 交接:一頁批號 < 律冊批號 → STALE 而不是 RED(過期≠壞);VDF 文 >0;掉球經 VCGC 讀 n/open(在位時)", ho["state"] in ("GREEN", "STALE") and ho.get("vdf_docs", 0) > 0 and (mode() != "subsystem" or "n" in (ho.get("dropped_balls") or {})), f"({ho['state']} · {ho.get('why', '')[:50]} · VDF 文 {ho.get('vdf_docs')})")
            _FORCE_STANDALONE["on"] = True
            try:
                sa = collect()
            finally:
                _FORCE_STANDALONE["on"] = False
            chk("㉓ 雙模式:--standalone 下九域照讀、mode=standalone、五面標 STANDALONE 不代讀、尾版家族改自家 glob 並講明、上行 vcgc=STANDALONE;關掉後回 subsystem",
                sa["mode"] == "standalone" and set(sa["lamps"]) == set(DOMAINS) and str(sa["engine"]["faces"].get("state", "")).startswith("STANDALONE") and "standalone" in sa["engine"].get("families_ruler", "")
                and sa["upstream"].get("vcgc") == "STANDALONE" and sa["engine"]["families"] >= 40 and (mode() == "subsystem" or _vcgc() is None),
                f"(standalone 家族 {sa['engine']['families']} · 現在 {mode()})")
            rcd = s["records"]
            chk("㉔ 紀錄索引:血脈由 git 尾註量出(≥2 session 且提到 VDF 的 commit >0)· VDF 文含側線的 VDF 審視文 · 收容包 >0 · 指標不複本",
                rcd["state"] == "GREEN" and len(rcd["lineage"]) >= 2 and sum(v.get("vdf_commits", 0) for v in rcd["lineage"].values()) > 0
                and any("VIA_VDF_StatusReview" in d["doc"] for d in rcd["docs"]) and len(rcd["intake"]) > 0 and all("content" not in d for d in rcd["docs"]),
                f"(session {len(rcd['lineage'])} · 文 {len(rcd['docs'])} · 收容包 {len(rcd['intake'])})")
            br = s["bridge"]
            chk("㉕ 橋律逐支量:排除清單與真擷取判定**委派**橋掃器(源碼 `_excluded(` / `_is_net_caller(` 都在)· 尾版加速器橋缺 0 · 真擷取尾版網路橋缺 0 · 版史另報不判",
                "_excluded(" in body and "_is_net_caller(" in body and br["state"] == "GREEN" and not br["accel"]["missing"] and not br["net"]["callers_missing"] and br["tails"] >= 40 and "py" in br["history"],
                f"(加速器 {br['accel']['has']}/{br['tails']} · 網路 {br['net']['has']}/{br['tails']} 真擷取 {br['net']['callers']} · 排除 {br['excluded']} · 版史 {br['history']})")
            to = s["tool"]
            chk("㉖ 工具:兩支正典位在 · SUP_MDL740 / SUP_MDL737 / VIA_SuperAccel_Module 尾版在 · 副本不同一份只判 STALE 不判 RED · 同意閘只讀(源碼無 environ[...]= 賦值)",
                all(t["exists"] for t in to["tools"].values()) and to["bridges"]["net_unified"] and to["bridges"]["super_accel"] and to["bridges"]["super_accel_module"]
                and to["state"] in ("GREEN", "STALE") and not re.search(r"environ\[\s*[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\s*\]\s*=", body) and "putenv" not in body,
                f"({ {n: (t['state'], t['variants']) for n, t in to['tools'].items()} } · 橋 {to['bridges']})")
            chk("㉗ 自測不動同意閘(前後環境同)且 read('bridge','VDF_ENG054') 回單支橋況(accel/net/net_caller 三鍵)",
                (os.environ.get("VIA_NET_CONSENT"), os.environ.get("VIA_SCRAPE_CONSENT")) == gate_before and all(k in (read("bridge", "VDF_ENG054").get("hit") or {}) for k in ("accel", "net", "net_caller")))
            with tempfile.TemporaryDirectory() as td2:
                shp, psp = Path(td2) / "a.sh", Path(td2) / "a.ps1"
                shp.write_text("echo x; python3 \"$(newest 'VDF_ENG055_OmniFetch_v*.py')\" run\n# newest 'VDF_ENG999_Ghost_v*.py'\npython3 \"$ENG/VDF_ENG051_ActiveTWETF_Holdings.py\"\npython3 \"$(ls \"$REG\"/CGC_MDL088_SystemTestPages_v*.py | sort | tail -1)\" run\n", encoding="utf-8")
                psp.write_text("Step \"x\" (Newest $ENG \"VDF_ENG055_OmniFetch_v*.py\") @(\"run\")\nStep \"y\" (Join-Path $ENG \"VDF_ENG051_ActiveTWETF_Holdings.py\") @()\n$PY = & python $envpy envpy vdf\n", encoding="utf-8")
                neg = chain_parity(shp, psp)
                psp.write_text(psp.read_text(encoding="utf-8") + "Step \"z\" (Newest $REG \"CGC_MDL088_SystemTestPages_v*.py\") @(\"run\")\n", encoding="utf-8")
                pos = chain_parity(shp, psp)
                psp.write_text(psp.read_text(encoding="utf-8").replace("$PY = & python $envpy envpy vdf\n", ""), encoding="utf-8")
                bare = chain_parity(shp, psp)
            real = chain_parity()
            chk("㉘ 開機鏈雙載體同鏈(Z94 那一課):合成負控 .ps1 少一步 → RED 且點名(整行註解不算步)· 補上 → GREEN · 裸 python → STALE;真 .sh/.ps1 現量 GREEN(同一把尺 _STEP_RX)",
                neg["state"] == "RED" and neg["only_sh"] == ["CGC_MDL088_SystemTestPages"] and neg["steps_sh"] == 3 and pos["state"] == "GREEN" and bare["state"] == "STALE" and real["state"] == "GREEN",
                f"(真:.sh {real.get('steps_sh')} 步 · .ps1 {real.get('steps_ps1')} 步 · {real.get('why', '')})")
            la = read_launch(probe=False)
            first = (la.get("next") or [""])[0]
            hand_ok = {"GATED": first.startswith("[你的手] $env:VIA_NET_CONSENT"), "ABSENT": first.startswith("[你的手] "), "RED": first.startswith("[修] "), "GREEN": first.startswith("via-vdffetch")}.get(la["state"], la["state"] == "NODATA")
            chk("㉙ 啟動就緒只量不動手:燈 ∈ 燈號冊 · rc 表 {GREEN 0 · RED 1 · NODATA 2 · ABSENT 3 · GATED 4} · python 的尺是 CGC_MDL137→MDL136 · 同意閘前後同(永不代設)· 下一步卡第一行對得上燈(GATED/ABSENT=你的手 · RED=修 · GREEN=via-vdffetch)· status 也帶同一段(links +4)",
                la["state"] in LAMPS and la["rc"] == LAUNCH_RC[la["state"]] and LAUNCH_RC == {"GREEN": 0, "RED": 1, "NODATA": 2, "ABSENT": 3, "GATED": 4} and "CGC_MDL137" in str((la.get("python") or {}).get("ruler"))
                and (os.environ.get("VIA_NET_CONSENT"), os.environ.get("VIA_SCRAPE_CONSENT")) == gate_before and hand_ok and s["launch"]["state"] == la["state"] and sum(1 for l in s["links"] if l.get("domain") == "launch") == 4,
                f"({la['state']} rc {la['rc']} · {str(la.get('why'))[:60]})")
            envA = {"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "OFF", "VIA_HIST_LIMIT": "100"}
            envB = {"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"}
            lA, lB = read_launch(probe=False, environ=envA), read_launch(probe=False, environ=envB)
            spA, spB = lA["consent"]["scrape_split"], lB["consent"]["scrape_split"]
            rx_ok = bool(_SCRAPE_YES_RX.search('x = os.environ.get("VIA_SCRAPE_CONSENT") != "YES"')) and not _SCRAPE_YES_RX.search('g2 = bool(os.environ.get("VIA_SCRAPE_CONSENT"))')
            chk("㉚ 閘二三把尺 + 視窗限量(合成環境,不讀寫真同意閘):SCRAPE=OFF → 量得出寫死字面 YES 的尾版與直呼會撞到的短令(含 via-price · via-chip)、十道自帶 YES、下一步卡有 $env:VIA_SCRAPE_CONSENT='YES' 一行;"
                "VIA_HIST_LIMIT=100 → 卡上有清掉它那一行;SCRAPE=YES 且未限量 → 兩行都不出;比較式尺正負控",
                rx_ok and spA["value"] == "OFF" and len(spA["legacy_yes"]) >= 3 and {"via-price", "via-chip"} <= set(spA["blocked_direct"]) and spA["lanes_force_yes"]
                and any("$env:VIA_SCRAPE_CONSENT='YES'" in ln for ln in lA["next"]) and any("$env:VIA_HIST_LIMIT=''" in ln for ln in lA["next"])
                and lA["environ"] == "injected" and spB["value"] == "YES" and spB["blocked_direct"] == []
                and not any("VIA_SCRAPE_CONSENT='YES'" in ln or "VIA_HIST_LIMIT=''" in ln for ln in lB["next"]) and spA["tool_gate"] is None,
                f"(字面 YES {len(spA['legacy_yes'])} 支 · 直呼受阻 {spA['blocked_direct'][:6]} · 十道自帶 {spA['lanes_force_yes']} · 開機鏈自帶 {spA['boot_force_yes']})")
            pcx = plan_catalog()
            body_no_st = body.split("def plan_catalog(")[1].split("def other_fetchers(")[0]
            chk("㉛ 增量目錄新鮮度委派 VDF_ENG089 catalog_freshness()(本口不另算:源碼無 mtime 比較、無容忍秒數);回態 ∈ {FRESH, STALE, UNKNOWN, ABSENT} 且署名尺",
                "catalog_freshness()" in body_no_st and "st_mtime" not in body_no_st and "TOLERANCE" not in body and pcx.get("state") in ("FRESH", "STALE", "UNKNOWN", "ABSENT")
                and (pcx.get("state") in ("UNKNOWN",) or "catalog_freshness" in str(pcx.get("ruler", ""))),
                f"({pcx.get('state')} · {str(pcx.get('why', ''))[:60]})")
        finally:
            os.environ.pop("VIA_VDFSYS_REPORTS", None)
            os.environ.pop("VIA_SELFTEST", None)
    marker_after = sorted(p.name for p in real_dir.glob("*")) if real_dir.is_dir() else []
    if marker_before != marker_after:
        fails.append("零污染")
        print(f"  [FAIL] 自測零污染:真 VIA_Reports/vdf_system 被自測動過 {marker_before} → {marker_after}")
    print(f"  [計] {n[0]} 檢 OK {n[0] - len([f for f in fails if f != '零污染'])} · FAIL {len(fails)}(檢數現場計,不寫死)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
