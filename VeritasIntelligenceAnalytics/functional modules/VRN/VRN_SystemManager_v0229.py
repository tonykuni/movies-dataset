#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 SystemManager v0229 — 薄尾(第 35 輪全景一輪修正:① 年度數據冊改用表頭判斷(CLST / Citi / 華南 0 筆)· 項目須有文字(圖表座標「100 · 200」「-0.3% 4.3%」不收)② ⑦ Email 跨行接回 · 網域補 Daiwa / CLSA / 中信 ③ 分析師中文名排除「法說 / 封裝 / 研究中心」等非姓名 ④ 資產恆等式合理性(負值 / 權益 <1% 資產不比 · 6933 誤報)⑤ ⑤ 報告沒印目標價 → 目標價那點不適用(四點有證據 3/3)⑥ 完成判定「實測退步」寫出是哪一份)(v0228:調節輪交給 MAIN:① 漏斗 T0 文字層 → T1 換引擎 → T2 OCR 200 DPI → T3 OCR 325 DPI + 前處理 → T4 待人工 · 每份停在哪層的統計 · 門檻 / 階梯 / 上限寫在 VRN2_SSOT(funnel)由 MAIN 帶入引擎 ② 完成判定加「調節輪」③ U/I 頂端操作列(重跑 · 重跑驗收 · 開輸出冊 / 切割檢視 / 範圍夾 · 複製執行指令)+ 漏斗分頁)(v0227:VRN-2 獨立收尾:① vrn2scope 動詞 — VRN-2 獨立設定冊 VRN2_SSOT(來源夾 · 範圍 = 個股報告 · 交付項 · 參數可向其他系統取用不衝突即可)+ 只擷取個股報告(上輪判定非個股 / 檔名明確非個股不跑 · 同步到 vrn2\\scope_in)② 範圍冊 VRN2_Scope_latest.json ③ 三本輸出冊:基本資料 BASIC INFO · 年度財報數據 FINANCIAL DATA · 一標題四重點 SUMMARY(JSON / CSV / Parquet)④ U/I 加三分頁 · 完成判定加「輸出冊完整」)(v0226:向 VRN-1 學(方法 · 不照抄):① ⑦ 基本資料雙讀(讀法 A = 首頁區塊 · 讀法 B = pypdfium2 獨立讀原文 · Email / 電話 / 券商網域逐欄 VERIFIED / CONFLICT / SINGLE / MISSING · 字距拆斷修復「D errick.Yang」· 最多黃)② ① 加資產 = 負債 + 權益恆等式(不平衡判黃:少數股權 / 口徑)③ 冪等閘:每輪挑 3 份重跑擷取 · 輸出須逐字相同 · 列入完成判定)(v0225:全景黃燈:① ② 覆蓋率排除頁尾(頁面最底部 8% · 頁尾依規則不擷取)② ③ / ⑤ OCR 表算術交叉驗證(成長率 = 前後年相除 · 本益比 × EPS 各年一致)通過 → 綠(註明驗證方式)· ⑤ OCR 摘要數字對 OCR 文字(含摘要快取第 2 頁)③ 驗收鎖校正擴大:上輪 ⑤ 綠的重點含免責句(假綠)不算退步 · 貼包列出)(v0224:OCR 檔驗收時限:有 OCR 的檔(影像 PDF)單份逾時放寬到 VIA_VRN2_OCR_ACC_TIMEOUT(預設 900 秒)· 其餘照 300 秒(MQ-1560 3 路並跑搶 CPU 逾時 300 秒實證)· 分路器支援逐份時限)(v0223:③ OCR 表:引擎 rapidocr 的表格數字不對文字層(影像 PDF 沒有)· 改對同頁 OCR 文字逐一回查 · 最多黃並註明「OCR 來源 · 人工抽查」(全景第三輪實證:MQ-1560 重建表 72 個數字被判紅)· 文字層表格照舊)(v0222:驗收鎖校正:上輪 ⑤ 綠的標題若是券商橫幅(「Sachs I Research」等 · 假綠)→ 不算退步 · 以本輪為新基準並在貼包列「驗收鎖校正」(其他項目退步規則不動 · 精準錨點只改 ⑤ 比對)(v0221:OCR 收尾:① 摘要來自 OCR(影像 PDF)→ ⑤ 註明「OCR 來源 · 數字只能對 OCR 文字」最多黃(不宣稱回查原文)② 驗收子行程(acc-shard)也關 pdfminer 字型警告 ③ 首頁 OCR 成功的影像 PDF 不再列已知例外(由 ENG397 v0119 OCR 階梯產生文字區))(v0220:數字斷裂:逗號開頭的格子(GS-2382「,163,923」)不再當數字計算 · 驗收 ① 直接判紅「擷取數字斷裂」並列出格子(不再出現 84,370 ÷ 163,923 這種誤導的重算)· 搭配 ENG397 v0118 接回)(v0219:不卡住:完成驗收逐份抽成 _acc_one(行為不變)· 平行最多 3 路(子行程分路 acc-shard · VIA_VRN2_LANES)· 每份進度行 · 單份逾時(VIA_VRN2_ACC_TIMEOUT · 預設 300 秒)只停那一路並記紅 · 20 秒心跳 · 中間結果寫 TEMP 溢寫夾)(v0218:VRN-2 完成判定:每輪依完成定義逐條判燈(實測退步 0 · 交互驗證一致 · 鎖定 · 驗收 ①②③⑤ 無紅 · ⑥ 新輸入 AUDIT 無紅 · 個股四項無紅(影像 PDF 待 OCR 列已知例外))→ VRN2_Completion_latest.json + 輪次帳本 · U/I 最上方完成判定面板 · 貼包「VRN-2 完成判定」行 · 輸出根可由 VIA_VRN_HEALTH_OUT 指到 VIA_Reports\vrn2(與 VRN-1 區隔 · 不替換函式))(v0217:正式名稱改為 VRN-2 SystemManager:畫面 / 貼包 / 登記冊 / 核號請求 / 自測行全部用新名 · 檔名家族 VRN_SystemManager_v#### 保留(前版鏈與修正閘靠它找尾版 · 改檔名會讓修正閘檢查不到新管理器)· 程式行為與 v0216 相同)(v0216:完成驗收第一次 97 份實證修正:① 利潤 ÷ 營收必須同一張表(MS-2308 百萬 ÷ 十億 = 32434% 誤報)· 比率可跨表 · 表頭同年多欄取最右(凱基季度 + 年度並列 · 慧洋 6.8 是 1Q25)② 摘要 EPS 與任一 EPS 列相符即可(Daiwa EPS / Core EPS 兩列)③ 覆蓋率排除旋轉 / 直排字(JP-3653 橫式圖表頁 0%)④ pdfminer 字型警告不印 ⑤ 毛利率可用「(營收 − 營業成本) ÷ 營收」通過(泓德:毛利淨額為調整後)· 跨表算不平(損益表 vs 比率表 · 數字都在原文)判黃「原文跨表不一致」· 同表算不平才紅 FAIL_CLOSED ⑥ 數字回查用 pdfplumber + pypdfium2 兩個讀取器聯集(pdfplumber 文字層壞掉的頁 · 引擎已改用 pypdfium2 擷取))(v0215:VRN-2 完成驗收 acceptance:① 結果計算驗證(表內毛利率 / 營益率 / 淨利率 = 利潤 ÷ 營收重算 · 上漲空間 = 目標價 ÷ 現價 − 1 重算 · 不符 FAIL_CLOSED)② 本文 / 資訊區 / 財報頁覆蓋率(頁面文字層每個字都在某一區)③ 輸出數字回原文搜尋(表格數字 + 摘要數字逐一在 PDF 文字層找到)⑤ 一標題四重點(ENG062 v0105 · 每點附證據 · 成功紀錄 3 份 oracle 逐項比對)⑥ AUDIT(新輸入檔自動判定)· 驗收退步計入退步 · 不鎖)(v0214:VRN-2 元件登記冊 register 動詞:一本冊管 MGR / ENG / MDL / PS · CLS · FNC · SSOT / REGEX / SYN / DICT / LIST / CFG(檔案冊 + 程式內常數)· IN / OUT · DF 欄位 · ENV 套件(含版本)· PARAM(環境變數)→ 編號 VRN2-<類>-#### 暫編待 VCGC 核號 · 鍵不變號不變 · 內容變記版本史 · 消失只標退役不刪 · 內容有變才出新版冊 · vrn2 與 ActivateVRN-2 每次自動登記 · U/I 加「元件登記」分頁)(前版 v0213:ActivateVRN 後端:accelfix --all 補齊加速器到 100%(py:缺標記 + 舊橋 + 寫死舊版號 → 注入動態最新版號橋 · ps1:CELERITAS-TEMPLATE-JOIN + PS-ACCEL 橋,用 pwsh AST 定位 param 之後 / 第一個敘述之前 · 注入後再剖析 0 錯才寫)· envcheck 動詞:AST 掃加速器 / 網路工具 / VRN 尾版的 import → 缺的 --install 用本環境 pip 補(numpy 釘 <2 · 隔離套件不裝)· VRN-2 U/I 加「啟動檢查」分頁)(前版 v0212:個股四項第 20 輪實證:快訊判定看首頁前 600 字(月營收 · Background · We met · Summit)· Note / NR / 快訊首頁無評等 → 灰 · 快訊評價 EPS + 1 項即綠 · 無 EPS → 灰 · 年度數據只在文字段未切成表 → 黃(引擎待修)· 首頁無文字層 → 紅(OCR)· 交互驗證重算燈納入首頁無文字層)(前版 v0211:個股四項判定修正:年份往下排的表也算年度表 · 欄位整齊(數字列格數 ≈ 年度欄數)視為對齊 · 快訊 / 月營收更新 / 法說摘要 / Note 無年度表 → 灰 · Note / NR / 未評等首頁無評等 → 灰 · 券商與日期從首頁頁首補 · 未綠明細行改 [計] 開頭進貼包)(前版 v0210:VRN-2 個股報告四項驗收:辨識個股報告(代號 + 排除產業 / 晨報 / 盤後 / ETF / 論壇等)→ ①檔名(代號 · 日期 · 券商)②首頁(評等 / 目標價)③年度財報頁(期間欄對齊 · ≥2 個年度欄)④年度重要財報及評價資訊(EPS + ≥2 個評價指標)· 每項三燈 + 灰(快訊無年度財報)· 逐項鎖定只增不減 · 鎖過的項退步亮紅 · 先前成功先鎖 · U/I 個股分頁)(前版 v0209:VRN-2 交互驗證修正:CSV 只寫非空格與有內容的區 → 比對口徑改為「有內容的區 · 非空格 · 文字記錄」三項 · 不一致時列出哪一項 · 引擎欄取 P1Segment / AssetIndex 最新版)(前版 v0208:VRN-2 獨立子系統 vrn2 動詞:p1loop 成功(退步 0)→ 鎖版本 + 時間(registry/VRN2_Lock_*.json · 引擎 sha · 輸入檔 sha)· 備份成功狀態(VIA_Reports/vrn2/backup/<時間>/)· 對 C:\測試樣本報告 結果做一次交互驗證(JSON ↔ CSV ↔ 燈號)· 自動跳出 HTML U/I(VIA_Reports/vrn2/VRN2_UI_latest.html);accelfix 排除 intake/ 交接副本)(前版 v0207:accelfix 修正:同時掃程式碼夾(HERE · 現役尾版)與資料家目錄 · 計畫行帶相對路徑 · 摘要分夾計數 · 程式碼夾優先)(前版 v0206:accelfix:缺加速器標記的現役尾版 → AST 定位(docstring / __future__ 之後)注入加速器橋 · 出 v+1 新版原檔不動 · 先編譯檢查 · 每批 ≤20 · 計畫 / --apply · 帳本)(前版 v0205:reconcile:references / baseline / _sandbox 底下的基準快照不算衝突 · 只調和現役的冊與引擎)(前版 v0204:沙盒閘環境相依過濾修正:測試名稱比對去數字 / # / % / 標點 · 只比骨幹 · 閘印的 P# 對得上原始碼的 P%d)(前版 v0203:linkmap 動詞 → ENG396 v0102 連結圖:管理器 / 引擎 → 冊 · regex · 參數 · JSON 資料流 三燈矩陣 · 可同步 / 順序 分類 · MD + HTML)(前版 v0202:沙盒閘:新尾版多出的失敗若是舊版本就有的環境相依測試(OCR / 網路)→ 歸類環境 · 不算新增失敗 · 其餘仍判紅)(前版 v0201:reconcile 修正:衝突用相對路徑 · 同族以資料夾 + 名稱分 · 版號固定四位 · 去重;前版算出 v0001 與重複列的 bug)(前版 v0200:修正閘快查前核對指紋快照:只差行尾(CRLF/LF)的檔視為未改 · 更新該筆快照 · 內容真不同仍判紅 · 零替換)(前版 v0199:reconcile 整族接續編號:同族多版衝突時 · 本機各版依序存到該族現有最大版號之後(v0102→v0110 …)· 不再 v+1 互相覆蓋 · Result / Registry 不算冊)(前版 v0198:計畫每件一行 [計] 調和(進貼包)· 計畫寫 registry/VRN_Reconcile_Plan_latest.md)(前版 v0197:自查遺漏:易變參數(VIA_SPILL_DIR · rep)只登記名稱來源不登記值 → 登記冊內容沒變不出新版;隔離 / 傾倒 / _sha 字尾的舊腳本不掃 · 另計「待整理」· 不再點名 3624 支沒版號)(前版 v0196:版本號衝突只算有版號的冊 / 引擎(帳本 · 紀錄 · 輸出不算)· reconcile 動詞 = 不要同號出新版號(本機內容 → v+1 · 原號還原 main · 只增不減 · 先列計畫 --apply 才動)· p1loop 把退步區塊細節直接印進貼包)(前版 v0195:該註冊註冊 · 該編號編號 · 版本號寫版本號 · 每版規格存冊 · 自動建立;編號待 VCGC 核號無衝突才確認 · 本機先用 git 比對 main 抓同名不同內容的版本號衝突)(前版 v0194:退步細節追加 MD · 印 MD 路徑 · AI 讀 MD 不用截圖)(前版 v0193:實測實修迴圈 p1loop · 每輪跑 p1view → 綠燈檔案鎖定(只增不減 · 退步亮紅)· 與上一輪比較燈號 / 原因增減 · 輪次 append-only 帳本)(前版 v0192:摘要如實寫 PDF 份數 · 先切割再 pdfplumber 擷取 · 本文 / 資訊區分開 · 不亂碼 · 不能用馬上換)。
  p1view 動詞 → VRN_ENG397_P1Segment(輸入夾 = VRN 設定 input_dir · 預設 C:\\測試樣本報告)· p1view --one <檔名片段> 只看一份
  零替換(不動任何前版函式)。其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import os
import html
from collections import Counter
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0229"
DISPLAY_NAME = "VRN-2 SystemManager"   # v0217 正式名稱(檔名家族仍是 VRN_SystemManager)


def _vnum_v0214(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0214(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0214(p) < _vnum_v0214(__file__)), key=_vnum_v0214)
PRIOR = _load_v0214(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


def _mod_v0214(tag: str):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if vars(mod).get("TAG") == tag:
            return mod
        mod = vars(mod).get("PRIOR")
    return PRIOR


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


_BOOK_RX = re.compile(r"(?i)synonym|regex|pattern|dict|lexicon|rules?|config|masterlist|book|ssot|roster|register(?!_v)|ledger|lock", re.I)


def _spec_of(p: Path) -> str:
    """每個版本的規格 = 檔案第一行說明(py docstring 第一行 / json 的 description · rule · schema)。"""
    try:
        if p.suffix == ".py":
            t = p.read_text(encoding="utf-8", errors="replace")
            m = re.search(r'"""\s*(.+?)\s*(?:\n|""")', t)
            return (m.group(1) if m else "")[:160]
        if p.suffix == ".json":
            d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            if isinstance(d, dict):
                return str(d.get("description") or d.get("rule") or d.get("schema") or d.get("title") or "")[:160]
    except Exception:  # noqa: BLE001
        return ""
    return ""


def _git_conflicts(home: Path) -> list:
    """本機先做一層衝突偵測:GitHub main 上同名的 VRN 檔 · 內容不同 = 版本號衝突(上次 v0151 / v0152 撞名就是這種)。沒有 git → 空清單(灰)。"""
    import subprocess
    try:
        top = subprocess.run(["git", "-C", str(home), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=20).stdout.strip()
        if not top:
            return []
        rel = str(home.resolve().relative_to(Path(top).resolve())).replace("\\", "/")
        out = subprocess.run(["git", "-C", top, "ls-tree", "-r", "origin/main", "--", rel], capture_output=True, text=True, timeout=60).stdout
        bad = []
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) != 2 or not parts[1].endswith((".py", ".json", ".ps1")):
                continue
            nm = Path(parts[1]).name
            if not re.search(r"_v\d{3,4}", nm) or re.search(r"(?i)ledger|manifest|evidence|audit|report|_latest|lock|registr|progress|cache|result", nm):
                continue
            if re.search(r"(?i)[\\/](?:references|baseline|_sandbox|vrn_sandbox|_quarantine|_superseded)[\\/]", parts[1] + "/"):
                continue                                               # v0205:基準快照 / 隔離 / 沙盒副本不是現役的冊                                           # v0196:只算有版號的冊 / 引擎 · 帳本 / 紀錄 / 輸出不算
            sha = parts[0].split()[2]
            lp = Path(top) / parts[1]
            if lp.exists():
                mine = subprocess.run(["git", "-C", top, "hash-object", str(lp)], capture_output=True, text=True, timeout=20).stdout.strip()
                if mine and mine != sha:
                    try:
                        bad.append(str(lp.resolve().relative_to(home.resolve())).replace("\\", "/"))   # v0201:相對路徑(同名不同夾不混)
                    except ValueError:
                        bad.append(nm)
        return sorted(set(bad))
    except Exception:  # noqa: BLE001
        return []


def asset_register(home: Path = None) -> dict:
    """資產登記冊(v0195):引擎(沿用 VRN-E · 暫編待 VCGC 確認)+ 冊 VRN-B + 參數 VRN-P + 每版規格(只增不減)· 核號請求 contract/VRN_NUMBER_REQUEST_latest.json · VCGC 核發 VCGC_NUMBER_GRANT_latest.json 後轉已確認。"""
    import datetime
    import hashlib
    home = Path(home or (_resolve("_home") or (lambda: HERE))())
    rd, cd = home / "registry", home / "contract"
    rd.mkdir(parents=True, exist_ok=True)
    cd.mkdir(parents=True, exist_ok=True)
    vn = lambda p: (lambda m: int(m.group(1)) if m else -1)(re.search(r"_v(\d{4})", Path(p).stem))  # noqa: E731
    hits = sorted(rd.glob("VRN_Asset_Register_v*.json"), key=vn)
    prev = {}
    if hits:
        try:
            prev = json.loads(hits[-1].read_text(encoding="utf-8"))
        except ValueError:
            prev = {}
    grant = {}
    for gp in (cd / "VCGC_NUMBER_GRANT_latest.json", home.parent.parent / "VCGC" / "contract" / "VCGC_NUMBER_GRANT_latest.json"):
        if gp.exists():
            try:
                grant.update(json.loads(gp.read_text(encoding="utf-8")).get("grants") or {})
            except ValueError:
                pass
    eng_hits = sorted(rd.glob("VRN_Engine_Register_v*.json"), key=vn)
    engines = {}
    if eng_hits:
        try:
            engines = json.loads(eng_hits[-1].read_text(encoding="utf-8")).get("engines") or {}
        except ValueError:
            engines = {}
    skip = re.compile(r"[\\/](?:_superseded|__pycache__|\.git|VIA_Reports|restore|restore_learned|_p1view_out|contract)[\\/]|_latest\.|Register_v\d|Ledger")   # 登記冊 / 帳本 / 契約 / latest 不是資產
    tidy_rx = re.compile(r"(?i)[\\/](?:_?quarantine|隔離|_dump|_raw|archive|_old|backup|_backup)[\\/]|_sha[0-9a-f]{6,}\.")   # v0197:隔離 / 傾倒 / _sha 字尾 = 待整理 · 不掃
    allf = [p for p in home.rglob("*") if p.is_file() and p.suffix in (".py", ".json") and not skip.search(str(p))]
    pending_tidy = sum(1 for p in allf if tidy_rx.search(str(p)))
    files = [p for p in allf if not tidy_rx.search(str(p))]
    sha8 = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()[:8]  # noqa: E731
    specs = dict((prev.get("specs") or {}))
    nover = []
    for p in files:
        m = re.search(r"^(.*)_v(\d{3,4})$", p.stem)
        fam = (m.group(1) if m else p.stem) + p.suffix
        ver = ("v" + m.group(2).zfill(4)) if m else "(無版號)"
        if not m and p.suffix == ".py" and not p.name.startswith("_"):
            nover.append(p.name)
        specs.setdefault(fam, {})
        if ver not in specs[fam]:
            specs[fam][ver] = {"spec": _spec_of(p), "sha8": sha8(p), "bytes": p.stat().st_size, "date": datetime.date.fromtimestamp(p.stat().st_mtime).isoformat()}
    books = dict(prev.get("books") or {})
    bused = [int(v["no"][6:10]) for v in books.values() if re.match(r"VRN-B-\d{4}", str(v.get("no", "")))]
    nb = max(bused, default=0) + 1
    for p in sorted(files):
        if p.suffix == ".json" and "registry" in p.parts and "Register" in p.name:
            continue
        if not (_BOOK_RX.search(p.stem) and ("SSOT" in p.parts or "knowledge" in p.parts or "registry" in p.parts or p.suffix == ".json" or _BOOK_RX.search(p.stem))):
            continue
        if "SystemManager" in p.name or "ENG3" in p.name:
            continue
        m = re.search(r"^(.*)_v(\d{3,4})$", p.stem)
        fam = (m.group(1) if m else p.stem) + p.suffix
        old = books.get(fam) or {}
        no = old.get("no")
        if not no:
            no = "VRN-B-%04d" % nb
            nb += 1
        books[fam] = {"no": no, "kind": "冊(SSOT / regex / 同義字 / 字典 / 規則 / 設定)", "tail": p.name, "version": ("v" + m.group(2).zfill(4)) if m else "(無版號)", "domain": str(p.parent.relative_to(home)) if p.parent != home else ".",
                      "sha8": sha8(p), "status": "已確認(VCGC)" if grant.get(fam) == no else "暫編 · 待 VCGC 核號", "first_seen": old.get("first_seen") or datetime.date.today().isoformat()}
    params = dict(prev.get("params") or {})
    pused = [int(v["no"][6:10]) for v in params.values() if re.match(r"VRN-P-\d{4}", str(v.get("no", "")))]
    npn = max(pused, default=0) + 1
    for k, getter in (("input_dir", lambda: str((_resolve("input_dir") or (lambda: ""))())), ("home", lambda: str(home)), ("rep", lambda: str((_resolve("_rep") or (lambda: ""))())),
                      ("VIA_ROOTS_BASE", lambda: os.environ.get("VIA_ROOTS_BASE", "")), ("VIA_DB_ROOT", lambda: os.environ.get("VIA_DB_ROOT", "")), ("VIA_VRN_SSOT_HOME", lambda: os.environ.get("VIA_VRN_SSOT_HOME", "")),
                      ("VIA_SPILL_DIR", lambda: os.environ.get("VIA_SPILL_DIR", ""))):
        try:
            val = getter()
        except Exception:  # noqa: BLE001
            val = ""
        old = params.get(k) or {}
        no = old.get("no") or ("VRN-P-%04d" % npn)
        if not old.get("no"):
            npn += 1
        if k in ("VIA_SPILL_DIR", "rep"):
            val = "(易變 · 每輪不同 · 只登記名稱與來源)"                  # v0197:易變值不登記 → 內容沒變不出新版
        params[k] = {"no": no, "value": val, "source": "環境變數" if k.startswith("VIA_") else "管理器", "status": "已確認(VCGC)" if grant.get(k) == no else "暫編 · 待 VCGC 核號"}
    eng = {k: dict(no=v.get("no"), version=v.get("version"), status="已確認(VCGC)" if grant.get(k) == v.get("no") else "暫編 · 待 VCGC 核號", versions=sorted(specs.get(k, {}).keys()))
           for k, v in engines.items() if isinstance(v, dict)}
    conflicts = _git_conflicts(home)
    pending = {k: v["no"] for sec in (eng, books, params) for k, v in sec.items() if v.get("no") and "暫編" in v.get("status", "")}
    body = {"schema": "VIA.VRN.AssetRegister.v1", "engines": eng, "books": books, "params": params, "specs": specs, "no_version": sorted(nover), "version_conflicts_vs_main": conflicts, "pending_tidy": pending_tidy}
    chg = {k: body[k] for k in body if k != "schema"} != {k: prev.get(k) for k in body if k != "schema"}
    nv = "v%04d" % ((vn(hits[-1]) + 1) if hits else 100)
    if chg:
        body.update(version=nv, prior=hits[-1].name if hits else None, ts=datetime.datetime.now().isoformat(timespec="seconds"),
                    rule="資產登記冊(唯一寫入者 VRN SystemManager):引擎沿用 VRN-E · 冊 VRN-B · 參數 VRN-P · 編號只在冊裡 · 暫編待 VCGC 核號 · 每版規格只增不減 · 內容變才出新版")
        (rd / ("VRN_Asset_Register_%s.json" % nv)).write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    (cd / "VRN_NUMBER_REQUEST_latest.json").write_text(json.dumps({"from": DISPLAY_NAME, "ts": datetime.datetime.now().isoformat(timespec="seconds"), "pending": pending,
                                                                    "rule": "VCGC 偵測三系統無衝突後寫 VCGC_NUMBER_GRANT_latest.json {grants:{key:no}} · VRN 讀到才轉已確認"}, ensure_ascii=False, indent=1), encoding="utf-8")
    cnt = lambda sec: (sum(1 for v in sec.values() if "已確認" in v.get("status", "")), sum(1 for v in sec.values() if "暫編" in v.get("status", "")))  # noqa: E731
    return {"file": ("VRN_Asset_Register_%s.json" % nv) if chg else (hits[-1].name + "(無變更)" if hits else "—"), "changed": chg, "engines": cnt(eng), "books": cnt(books), "params": cnt(params),
            "specs": sum(len(v) for v in specs.values()), "no_version": nover, "conflicts": conflicts, "pending": len(pending), "pending_tidy": pending_tidy}


def asset_lines(o: dict) -> list:
    L = ["[計] 資產登記(%s)· 引擎 已確認 %d / 暫編 %d · 冊 已確認 %d / 暫編 %d · 參數 已確認 %d / 暫編 %d · 版本規格 %d 筆 · 待 VCGC 核號 %d(contract/VRN_NUMBER_REQUEST_latest.json)" % (
        o["file"], *o["engines"], *o["books"], *o["params"], o["specs"], o["pending"])]
    if o["no_version"]:
        L.append("[計] 沒版號的 py %d:%s(該寫版本號)" % (len(o["no_version"]), " · ".join(o["no_version"][:6])))
    if o.get("pending_tidy"):
        L.append("[計] 待整理(隔離 / 傾倒 / _sha 字尾舊腳本 · 未掃 · 未點名)%d 支" % o["pending_tidy"])
    if o["conflicts"]:
        L.append("[RED] 版本號衝突(GitHub main 同名不同內容)%d:%s → 不要同號 · 出新版號" % (len(o["conflicts"]), " · ".join(o["conflicts"][:6])))
    return L


_ENVTEST = re.compile(r"OCR|rapidocr|paddle|tesseract|雙引擎|網路|download|http|yfinance|連線", re.I)


def env_flaky_filter(o: dict, older_has) -> list:
    """v0202:「新尾版多出失敗「X」」若 X 是舊版本就有的環境相依測試(OCR / 網路)→ 從紅字移到環境 · 回傳移走的清單。older_has(label) 查舊版本原始碼。"""
    reds = list(o.get("red") or [])
    moved = []
    for r in reds:
        m = re.search(r"新尾版多出失敗「(.{6,40})", r)
        if m and _ENVTEST.search(m.group(1)) and older_has(m.group(1)):
            o["red"].remove(r)
            o.setdefault("env_flaky", []).append(r)
            moved.append(m.group(1)[:30])
    if moved and not o.get("red") and o.get("verdict") == "RED":
        o["verdict"] = "YELLOW"
    return moved


def _skel(t: str) -> str:
    return re.sub(r"[\s\d#%()（）:：·,，.。\[\]\-_]", "", t)


def _older_has(label: str) -> bool:
    """v0204:只比名稱骨幹(去數字 / # / % / 空白 / 標點)· 閘印出的「P# 圖區」對得上原始碼的「P%d 圖區」。"""
    key = _skel(label)[:10]
    if len(key) < 4:
        return False
    for p in HERE.glob(_STEM + "_v*.py"):
        if _vnum_v0214(p) < _vnum_v0214(__file__):
            try:
                if key in _skel(p.read_text(encoding="utf-8", errors="replace")):
                    return True
            except OSError:
                continue
    return False


def linkmap_verb() -> tuple:
    cands = sorted(HERE.glob("VRN_ENG396_AssetIndex_v*.py"), key=_vnum_v0214)
    m = _load_v0214(cands[-1], "vrn_eng396_" + cands[-1].stem) if cands else None
    if m is None or not hasattr(m, "linkmap"):
        return 1, ["[RED] 連結圖 · ENG396 v0102 以上不在 VRN 樹"]
    try:
        o = m.linkmap(HERE, Path(_resolve("_rep")()))
    except Exception as exc:  # noqa: BLE001
        return 1, ["[RED] 連結圖失敗 · %s: %s" % (type(exc).__name__, str(exc)[:120])]
    return 0, ["[計] 連結圖(ENG396)· 尾版 %d · 燈 %s · 可同步修正 %d · 順序修正(要決定)%d · 同領域多本冊 %s" % (o["nodes"], o["lamps"], o["sync"], o["seq"], o["multi"] or "無"),
               "  [MD] %s" % o["md"], "  [U/I] %s" % o["html"]]


BRIDGE_TXT = '# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====\nimport importlib as _cb_il\nimport re as _cb_re\nimport sys as _cb_sys\nfrom pathlib import Path as _cb_Path\n_ACCEL, _ACCEL_VER = None, ""\n_cb_p = _cb_Path(__file__).resolve()\nwhile _cb_p.parent != _cb_p:\n    if (_cb_p / "supportive modules").is_dir():\n        _cb_sup = _cb_p / "supportive modules"\n        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),\n                       key=lambda x: int(_cb_re.search(r"_v(\\d{4})", x.name).group(1)))\n        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:\n            if _cb_d not in _cb_sys.path:\n                _cb_sys.path.insert(0, _cb_d)\n        if _cb_c:\n            try:\n                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem\n            except Exception:  # noqa: BLE001\n                _ACCEL = None\n        break\n    _cb_p = _cb_p.parent\nif _ACCEL is None:\n    try:\n        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版\n        _ACCEL_VER = "VeritasCeleritas_v1141"\n    except Exception:  # noqa: BLE001\n        _ACCEL = None\n\n\ndef _net():\n    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""\n    try:\n        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433\n        return _NET\n    except Exception:  # noqa: BLE001\n        return None\n# ===== [VIA:ACCEL-BRIDGE:END] =====\n'
_AF_SKIP = re.compile(r"(?i)[\\/](?:_superseded|__pycache__|\.git|\.venv|venv|envs|tests?|_quarantine|quarantine|隔離|_dump|_raw|archive|_old|backup|references|baseline|_sandbox|vrn_sandbox|VIA_Reports|restore|restore_learned|intake|handover)[\\/]|_sha[0-9a-f]{6,}\.")


def accelfix(apply: bool = False, home=None, limit: int = 20, every: bool = False) -> tuple:
    """缺加速器標記的現役尾版(py)→ 在 docstring / from __future__ 之後注入加速器橋 · 出 v+1 · 原檔不動 · 先編譯 · 每批 ≤limit · 計畫 / --apply。"""
    import ast
    import datetime
    dh = Path((_resolve("_home") or (lambda: HERE))())
    roots = [Path(home)] if home else ([HERE] + ([dh] if dh.resolve() != HERE.resolve() else []))   # v0207:程式碼夾優先 · 資料家目錄次之
    home = roots[0]
    fams = {}
    for root in roots:
      for p in root.rglob("*.py"):
        if _AF_SKIP.search(str(p)) or not p.is_file():
            continue
        m = re.search(r"^(.*)_v(\d{3,4})$", p.stem)
        if not m:
            continue
        k = (str(p.parent), m.group(1))
        v = int(m.group(2))
        if k not in fams or v > fams[k][1]:
            fams[k] = (p, v)
    def _rel(p):
        for r in roots:
            try:
                return ("[碼] " if r == roots[0] and len(roots) > 1 else ("[資料] " if len(roots) > 1 else "")) + str(p.parent.resolve().relative_to(r.resolve())).replace("\\", "/")
            except ValueError:
                continue
        return str(p.parent)
    cands = []
    for (sub, fam), (p, v) in sorted(fams.items()):
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if every:                                                    # v0213:--all = 只要不是綠(缺標記 / 舊橋 / 寫死舊版號 / 沒接正本)都補動態最新版號橋
            kind = (_resolve("accel_kind") or (lambda *a: ("", "OP-300")))(src, ".py", _latest_accel_name())
            if kind[1] == "GREEN" or "VIA:ACCEL-BRIDGE:v0111" in src:
                continue
        elif "[VIA:ACCEL-BRIDGE" in src or "VeritasCeleritas" in src:
            continue
        cands.append((p, v, src))
    batch = cands[:limit]
    fold = Counter(_rel(p) for p, _, _ in cands)
    L = ["[計] 加速器注入(accelfix)%s · 缺標記現役尾版 %d · 本批 %d(每批 ≤%d · AST 定位 docstring / __future__ 之後 · 出 v+1 原檔不動 · 先編譯)· 分夾:%s" % (" 執行" if apply else " 計畫(不動檔 · --apply 才寫)", len(cands), len(batch), limit, " · ".join("%s %d" % kv for kv in fold.most_common(6)))]
    done, bad = [], []
    for p, v, src in batch:
        try:
            t = ast.parse(src)
        except SyntaxError as exc:
            bad.append("%s 原檔語法錯 %s" % (p.name, exc.lineno))
            continue
        idx = 0
        body = t.body
        if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
            idx = 1
        while idx < len(body) and isinstance(body[idx], ast.ImportFrom) and body[idx].module == "__future__":
            idx += 1
        line = body[idx - 1].end_lineno if idx > 0 else 0
        lines = src.splitlines(keepends=True)
        new = "".join(lines[:line]) + ("\n" if line and not lines[line - 1].endswith("\n") else "") + BRIDGE_TXT.rstrip("\n") + "\n" + "".join(lines[line:])
        try:
            compile(new, p.name, "exec")
        except SyntaxError as exc:
            bad.append("%s 注入後編譯失敗 %s" % (p.name, exc.lineno))
            continue
        nv = p.with_name(re.sub(r"_v\d{3,4}$", "_v%04d" % (v + 1), p.stem) + ".py")
        L.append("[計] 注入 %s/%s → %s(定位第 %d 行後)%s" % (_rel(p), p.name, nv.name, line, "(新版已存在 · 跳過)" if nv.exists() else ""))
        if apply and not nv.exists():
            nv.write_text(new, encoding="utf-8", newline="")
            done.append({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "src": p.name, "new": nv.name, "line": line})
    for b in bad:
        L.append("[計] 跳過 %s" % b)
    if apply:
        rd = home / "registry"
        rd.mkdir(parents=True, exist_ok=True)
        with (rd / "VRN_AccelFix_Ledger.jsonl").open("a", encoding="utf-8") as fh:
            for d in done:
                fh.write(json.dumps(d, ensure_ascii=False) + "\n")
        L.append("[計] 加速器注入完成 %d 件 · 跳過 %d · 剩餘缺標記 %d · 帳本 registry/VRN_AccelFix_Ledger.jsonl" % (len(done), len(bad), len(cands) - len(done)))
    return 0, L


def _latest_accel_name() -> str:
    try:
        return (_resolve("latest_accel") or (lambda h: ""))(HERE) or ""
    except Exception:  # noqa: BLE001
        return ""


PS_JOIN = "# CELERITAS-TEMPLATE-JOIN v1"
PS_ACCEL = ("# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====\n"
            "try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\\Users\\tonyk\\OneDrive\\Documents\\movies-dataset\\VeritasIntelligenceAnalytics' }\n"
            "  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe \"supportive modules\\VIA_PS_Accel_Module.ps1\"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }\n"
            "# ===== [VIA:PS-ACCEL:END] =====")
_PS_PROBE = r"""param([string]$List)
$out = @{}
foreach ($p in (Get-Content -LiteralPath $List -Encoding utf8)) {
  if (-not $p) { continue }
  $tok = $null; $err = $null
  $a = [System.Management.Automation.Language.Parser]::ParseFile($p, [ref]$tok, [ref]$err)
  $first = @(@($a.BeginBlock, $a.ProcessBlock, $a.EndBlock, $a.DynamicParamBlock) | Where-Object { $_ } | ForEach-Object { $_.Statements } | Where-Object { $_ } | ForEach-Object { $_.Extent.StartOffset } | Sort-Object | Select-Object -First 1)
  $ue = @($a.UsingStatements | ForEach-Object { $_.Extent.EndOffset } | Sort-Object -Descending | Select-Object -First 1)
  $out[$p] = @{ errors = @($err).Count; param_end = $(if ($a.ParamBlock) { $a.ParamBlock.Extent.EndOffset } else { -1 }); using_end = $(if ($ue) { $ue[0] } else { -1 }); first = $(if ($first) { $first[0] } else { -1 }) }
}
$out | ConvertTo-Json -Depth 4 -Compress
"""


def _ps_probe(paths: list) -> dict:
    """pwsh AST 定位(一次批次):每檔 param 結尾 / using 結尾 / 第一個敘述起點 / 剖析錯數;沒有 pwsh → {}。"""
    import shutil
    import subprocess
    import tempfile
    exe = shutil.which("pwsh") or shutil.which("pwsh.exe")
    if not exe or not paths:
        return {}
    td = Path(tempfile.mkdtemp(prefix="psaccel-"))
    (td / "probe.ps1").write_text(_PS_PROBE, encoding="utf-8-sig")
    (td / "list.txt").write_text("\n".join(str(p) for p in paths), encoding="utf-8")
    try:
        r = subprocess.run([exe, "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(td / "probe.ps1"), "-List", str(td / "list.txt")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        txt = (r.stdout or "").strip()
        d = json.loads(txt) if txt.startswith("{") else {}
        return {k: v for k, v in d.items()} if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def ps_accelfix(apply: bool = False, limit: int = 2000) -> tuple:
    """現役尾版 .ps1 缺 PS 加速橋 → 頂端補 CELERITAS-TEMPLATE-JOIN 標記 + PS-ACCEL 橋(param 之後 / using 之後 / 第一個敘述之前)· 出 v+1 · 原檔不動 · 注入後 pwsh 再剖析 0 錯才寫。"""
    import datetime
    import tempfile
    fams = {}
    for p in HERE.rglob("*.ps1"):
        if _AF_SKIP.search(str(p)) or not p.is_file():
            continue
        m = re.search(r"^(.*)_v(\d{3,4})$", p.stem)
        if not m:
            continue
        k = (str(p.parent), m.group(1))
        if k not in fams or int(m.group(2)) > fams[k][1]:
            fams[k] = (p, int(m.group(2)))
    cands = []
    for (sub, fam), (p, v) in sorted(fams.items()):
        raw = p.read_bytes()
        bom = raw.startswith(b"\xef\xbb\xbf")
        src = raw.decode("utf-8-sig", errors="replace")
        if PS_JOIN.split(" v")[0] in src and "[VIA:PS-ACCEL" in src:
            continue
        cands.append((p, v, src, bom))
    batch = cands[:limit]
    L = ["[計] PS 加速橋(accelfix --all · ps1)%s · 缺橋現役尾版 %d · 本批 %d(pwsh AST 定位 · 出 v+1 原檔不動 · 注入後再剖析 0 錯才寫)" % (" 執行" if apply else " 計畫", len(cands), len(batch))]
    if not batch:
        return 0, L
    pr = _ps_probe([p for p, _, _, _ in batch])
    if not pr:
        L.append("[計] PS 加速橋 · 找不到 pwsh 或剖析失敗 → 本批略過(不動任何 ps1)")
        return 0, L
    td = Path(tempfile.mkdtemp(prefix="psaccel-new-"))
    staged, bad = [], []
    for p, v, src, bom in batch:
        info = pr.get(str(p)) or {}
        if info.get("errors", 1):
            bad.append("%s 原檔剖析錯 %s 處" % (p.name, info.get("errors", "?")))
            continue
        nl = "\r\n" if "\r\n" in src else "\n"
        blk = PS_ACCEL.replace("\n", nl)
        at = next((x for x in (info.get("param_end", -1), info.get("using_end", -1)) if x is not None and x >= 0), -1)
        if at >= 0:
            new = src[:at] + nl + blk + nl + src[at:].lstrip("\r\n") if not src[at:].startswith(nl) else src[:at] + nl + blk + src[at:]
            where = "param 之後" if info.get("param_end", -1) >= 0 else "using 之後"
        else:
            f = info.get("first", -1)
            f = f if f is not None and f >= 0 else len(src)
            new, where = src[:f] + blk + nl + src[f:], "第一個敘述之前"
        if PS_JOIN.split(" v")[0] not in new:
            new = PS_JOIN + nl + new
        nv = p.with_name(re.sub(r"_v\d{3,4}$", "_v%04d" % (v + 1), p.stem) + ".ps1")
        tmp = td / nv.name
        tmp.write_bytes((b"\xef\xbb\xbf" if bom else b"") + new.encode("utf-8"))
        staged.append((p, nv, tmp, where))
    chk = _ps_probe([t for _, _, t, _ in staged])
    done = []
    for p, nv, tmp, where in staged:
        e = (chk.get(str(tmp)) or {}).get("errors", 1)
        if e:
            bad.append("%s 注入後剖析錯 %s 處(不寫)" % (p.name, e))
            continue
        L.append("[計] 注入 PS 橋 %s → %s(%s)%s" % (p.name, nv.name, where, "(新版已存在 · 跳過)" if nv.exists() else ""))
        if apply and not nv.exists():
            nv.write_bytes(tmp.read_bytes())
            done.append({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "src": p.name, "new": nv.name, "where": where, "kind": "ps1"})
    for b in bad:
        L.append("[計] 跳過 %s" % b)
    if apply and done:
        rd = HERE / "registry"
        rd.mkdir(parents=True, exist_ok=True)
        with (rd / "VRN_AccelFix_Ledger.jsonl").open("a", encoding="utf-8") as fh:
            for d in done:
                fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    L.append("[計] PS 加速橋完成 %d 件 · 跳過 %d · 剩餘 %d" % (len(done), len(bad), len(cands) - len(done)))
    return 0, L


_PIPNAME = {"fitz": "pymupdf", "yaml": "pyyaml", "bs4": "beautifulsoup4", "docx": "python-docx", "pptx": "python-pptx", "PIL": "pillow", "cv2": "opencv-python-headless",
            "sklearn": "scikit-learn", "dateutil": "python-dateutil", "win32api": "pywin32", "win32con": "pywin32", "win32com": "pywin32", "pythoncom": "pywin32", "pywintypes": "pywin32",
            "Crypto": "pycryptodome", "dotenv": "python-dotenv", "rapidocr_onnxruntime": "rapidocr-onnxruntime", "google": "google-api-python-client", "jwt": "pyjwt", "magic": "python-magic-bin",
            "serial": "pyserial", "attr": "attrs", "OpenSSL": "pyopenssl", "lz4": "lz4", "zstandard": "zstandard", "talib": "TA-Lib", "pdfminer": "pdfminer.six", "Levenshtein": "python-Levenshtein",
            "multipart": "python-multipart", "socks": "pysocks", "markdown": "markdown", "sentence_transformers": "sentence-transformers"}
_ISOLATED = re.compile(r"(?i)^(?:torch|torchvision|torchaudio|surya|ray|tabula|camelot|numba|ortools|paddle\w*|tensorflow|keras|uvloop|pm4py|ocrmypdf|modnet|rembg|onnxruntime_gpu|jax|cupy)$")


def envcheck(install: bool = False) -> tuple:
    """AST 掃 import(加速器 + 網路工具 = 必裝;VRN 尾版:頂層必裝 · try 內選裝)→ 缺的用本環境 pip 補(numpy 釘 >=1.24,<2.0 · 隔離套件不裝只列灰)。"""
    import ast
    import importlib.util
    import subprocess
    import sys
    import tempfile
    sup = next((p / "supportive modules" for p in [HERE] + list(HERE.parents) if (p / "supportive modules").is_dir()), None)
    must_files, opt_files = [], []
    if sup:
        acc = sorted(list(sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")), key=lambda x: int(re.search(r"_v(\d{4})", x.name).group(1)))
        must_files += acc[-1:] + list(sup.glob("VeritasAegisNexus_v1652.py"))[:1] + list(sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]
    fams = {}
    for p in HERE.rglob("*.py"):
        if _AF_SKIP.search(str(p)):
            continue
        m = re.search(r"^(.*)_v(\d{3,4})$", p.stem)
        if m and ((str(p.parent), m.group(1)) not in fams or int(m.group(2)) > fams[(str(p.parent), m.group(1))][1]):
            fams[(str(p.parent), m.group(1))] = (p, int(m.group(2)))
    opt_files = [p for p, _ in fams.values()]
    local = {p.stem for p in HERE.rglob("*.py")} | ({p.stem for p in sup.rglob("*.py")} if sup else set()) | {p.name for p in HERE.iterdir() if p.is_dir()}
    std = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
    need = {}

    def scan(f, must):
        try:
            t = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, OSError, ValueError):
            return
        tries = {id(n) for x in ast.walk(t) if isinstance(x, ast.Try) for b in x.body for n in ast.walk(b)}
        for n in ast.walk(t):
            names = [a.name for a in n.names] if isinstance(n, ast.Import) else ([n.module] if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module else [])
            for nm in names:
                top = nm.split(".")[0]
                if not top or top in std or top in local or top.startswith(("_", "VRN_", "VIA_", "Veritas", "CGC_", "VDF_", "VCGC")):
                    continue
                hard = must or id(n) not in tries
                d = need.setdefault(top, {"must": False, "hard": False, "by": set()})
                d["must"] |= must
                d["hard"] |= hard
                d["by"].add(f.name)
    for f in must_files:
        scan(f, True)
    for f in opt_files:
        scan(f, False)
    rows = []
    for top, d in sorted(need.items()):
        ok = importlib.util.find_spec(top) is not None
        pip = _PIPNAME.get(top, top.replace("_", "-"))
        lamp = "GREEN" if ok else ("GRAY" if _ISOLATED.match(top) else ("RED" if d["must"] or d["hard"] else "YELLOW"))
        rows.append({"module": top, "pip": pip, "lamp": lamp, "must": d["must"], "hard": d["hard"], "by": sorted(d["by"])[:3], "installed": ok, "action": ""})
    todo = [r for r in rows if r["lamp"] in ("RED", "YELLOW")]
    L = ["[計] 環境檢查(envcheck · %s)· 掃 加速器 / 網路工具 %d 檔 + VRN-2 尾版 %d 檔 · 第三方套件 %d · 已裝 %d · 缺(必裝)%d · 缺(選裝)%d · 隔離不裝 %d" % (
        sys.executable, len(must_files), len(opt_files), len(rows), sum(1 for r in rows if r["installed"]), sum(1 for r in rows if r["lamp"] == "RED"),
        sum(1 for r in rows if r["lamp"] == "YELLOW"), sum(1 for r in rows if r["lamp"] == "GRAY"))]
    if install and todo:
        cf = Path(tempfile.mkdtemp(prefix="pipc-")) / "constraints.txt"
        cf.write_text("numpy>=1.24,<2.0\n", encoding="utf-8")
        for r in todo:
            try:
                p = subprocess.run([sys.executable, "-m", "pip", "install", "--no-input", "--disable-pip-version-check", "-c", str(cf), r["pip"]], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
                importlib.invalidate_caches()
                r["installed"] = importlib.util.find_spec(r["module"]) is not None
                r["action"] = "已補裝" if r["installed"] else "補裝失敗 rc %d · %s" % (p.returncode, ((p.stderr or "").strip().splitlines() or [""])[-1][:90])
            except Exception as exc:  # noqa: BLE001
                r["action"] = "補裝失敗 · %s" % type(exc).__name__
            if r["installed"]:
                r["lamp"] = "GREEN"
            L.append("[計] 補裝 %s(%s)· %s" % (r["pip"], "必裝" if r["must"] else ("頂層" if r["hard"] else "選裝"), r["action"]))
    for r in rows:
        if r["lamp"] in ("RED", "YELLOW") and not (install and r["action"]):
            L.append("[計] 缺 %s %s(pip %s · 用於 %s)" % ("必裝" if r["lamp"] == "RED" else "選裝", r["module"], r["pip"], " · ".join(r["by"])))
        elif r["lamp"] == "GRAY":
            L.append("[計] 隔離套件 %s 不裝進本環境(LL#21–24 · 經橋呼叫)" % r["module"])
    try:
        rep = Path(_resolve("_rep")()).parent / "vrn2"
        rep.mkdir(parents=True, exist_ok=True)
        (rep / "VRN2_Env_latest.json").write_text(json.dumps({"python": sys.executable, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    bad = [r for r in rows if r["lamp"] == "RED"]
    return (1 if bad else 0), L


def _activate_html(v2: Path) -> str:
    try:
        a = json.loads((v2 / "VRN2_Activate_latest.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return ""
    lampi = lambda l: "<i style='background:%s'%s></i>" % (_V2C.get(l, "#9ca3af"), " class='bl'" if l == "RED" else "")  # noqa: E731
    rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (lampi(s.get("lamp", "GRAY")), html.escape(s.get("step", "")), html.escape(s.get("detail", ""))) for s in a.get("steps", []))
    return "<h3>%s啟動檢查(ActivateVRN-2 · %s)</h3><table><tr><th>燈</th><th>步驟</th><th>結果</th></tr>%s</table>" % (lampi(a.get("lamp", "GRAY")), html.escape(a.get("ts", "")), rows)


_RG_KINDS = ["MGR", "ENG", "MDL", "PS", "CLS", "FNC", "SSOT", "REGEX", "SYN", "DICT", "LIST", "CFG", "IN", "OUT", "DF", "ENV", "PARAM"]
_RG_LABEL = {"MGR": "管理器", "ENG": "引擎", "MDL": "模組", "PS": "PS 指令", "CLS": "類別", "FNC": "函式庫", "SSOT": "SSOT 冊", "REGEX": "Regex", "SYN": "同義字", "DICT": "字典",
             "LIST": "清單 / 名冊", "CFG": "設定 / 參數冊", "IN": "輸入", "OUT": "輸出", "DF": "DATAFRAME 欄位", "ENV": "環境套件", "PARAM": "參數(環境變數)"}
_RG_FILE = re.compile(r"^[\w\-.()%*\u4e00-\u9fff]+\.(?:json|jsonl|csv|md|html|parquet|png|txt|xlsx|pdf|duckdb|yaml|yml)$", re.I)


def _rg_book_kind(name: str) -> str:
    for k, rx in (("REGEX", r"(?i)regex|pattern|_rx|_re_"), ("SYN", r"(?i)synonym|同義|lexicon|alias"), ("DICT", r"(?i)dict|字典|rating|broker|券商"),
                  ("LIST", r"(?i)list|名冊|roster|ticker"), ("CFG", r"(?i)config|setting|param|policy|設定|參數")):
        if re.search(rx, name):
            return k
    return "SSOT"


def _rg_scan(paths: list) -> list:
    """AST 掃現役尾版 → (類, 鍵, 來源, 版本, 指紋, 備註)。不執行任何程式。"""
    import ast
    import hashlib
    h = lambda t: hashlib.sha256(t.encode("utf-8", "replace")).hexdigest()[:12]  # noqa: E731
    out = []
    for p in paths:
        m = re.search(r"^(.*)_v(\d{3,4})$", p.stem)
        fam, ver = (m.group(1), "v" + m.group(2).zfill(4)) if m else (p.stem, "")
        src = p.read_text(encoding="utf-8", errors="replace")
        if p.suffix.lower() == ".ps1":
            out.append(("PS", fam, p.name, ver, h(src), ""))
            continue
        kind = "MGR" if "SystemManager" in fam else ("ENG" if re.search(r"(?i)_ENG\d", fam) else "MDL")
        out.append((kind, fam, p.name, ver, h(src), ""))
        try:
            t = ast.parse(src)
        except (SyntaxError, ValueError):
            continue
        for n in t.body:
            if isinstance(n, ast.ClassDef):
                out.append(("CLS", "%s.%s" % (fam, n.name), p.name, ver, h(ast.unparse(n)), ""))
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("_"):
                out.append(("FNC", "%s.%s" % (fam, n.name), p.name, ver, h(ast.unparse(n)), ", ".join(a.arg for a in n.args.args)[:80]))
            elif isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                nm, v = n.targets[0].id, n.value
                if isinstance(v, ast.Call) and getattr(v.func, "attr", "") == "compile" and getattr(getattr(v.func, "value", None), "id", "") == "re":
                    out.append(("REGEX", "%s.%s" % (fam, nm), p.name, ver, h(ast.unparse(v)), "程式內常數"))
                elif nm.lstrip("_").isupper() and isinstance(v, (ast.Dict, ast.List, ast.Set, ast.Tuple)) and len(getattr(v, "keys", None) or getattr(v, "elts", [])) >= 5:
                    k = "SYN" if re.search(r"(?i)SYN|ALIAS|同義", nm) else ("DICT" if isinstance(v, ast.Dict) or re.search(r"(?i)BROKER|RATING|MAP|NAME", nm) else "LIST")
                    out.append((k, "%s.%s" % (fam, nm), p.name, ver, h(ast.unparse(v)), "程式內常數 %d 項" % len(getattr(v, "keys", None) or getattr(v, "elts", []))))
        for n in ast.walk(t):
            if isinstance(n, ast.Call):
                fn = getattr(n.func, "attr", "") or getattr(n.func, "id", "")
                io = "OUT" if fn in ("write_text", "write_bytes", "to_csv", "to_parquet", "to_json", "savefig", "save", "DictWriter") else ("IN" if fn in ("read_text", "read_bytes", "read_csv", "read_parquet", "glob", "rglob", "DocumentFile", "PdfDocument") else "")
                if fn == "open" and n.args:
                    mode = n.args[1].value if len(n.args) > 1 and isinstance(n.args[1], ast.Constant) else next((k.value.value for k in n.keywords if k.arg == "mode" and isinstance(k.value, ast.Constant)), "r")
                    io = "OUT" if any(c in str(mode) for c in "wa") else "IN"
                if io:
                    for c in ast.walk(n):
                        if isinstance(c, ast.Constant) and isinstance(c.value, str):
                            nm = re.sub(r"%[sd0-9.]*", "*", c.value.strip().replace("\\", "/").split("/")[-1])
                            if _RG_FILE.match(nm) or (fn in ("glob", "rglob") and re.match(r"^\*?\.?\*?[\w*]*\.\w{2,7}$|^\*\.\w+$", nm)):
                                out.append((io, nm, p.name, ver, "", fam))
                if fn in ("get", "getenv") and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str) and re.match(r"^[A-Z][A-Z0-9_]{3,}$", n.args[0].value):
                    if fn == "getenv" or "environ" in ast.unparse(n.func):
                        out.append(("PARAM", n.args[0].value, p.name, ver, "", fam))
            elif isinstance(n, ast.Subscript) and "environ" in ast.unparse(n.value) and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str):
                out.append(("PARAM", n.slice.value, p.name, ver, "", fam))
            elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.lstrip().startswith('{"schema"'):
                try:
                    c = json.loads(n.value)
                except ValueError:
                    continue
                for f in c.get("fields") or c.get("columns") or []:
                    nm = f.get("name") if isinstance(f, dict) else f
                    if nm:
                        out.append(("DF", "%s.%s" % (c.get("schema", fam), nm), p.name, ver, h(json.dumps(f, ensure_ascii=False)), (f.get("type", "") if isinstance(f, dict) else "")))
    return out


def register(home=None, rd=None, rep=None) -> tuple:
    """VRN-2 元件登記冊(唯一寫入者 = VRN SystemManager):AST 掃現役尾版 + 檔案冊 + 環境套件 → 編號 VRN2-<類>-####(暫編 · 待 VCGC 核號)· 鍵不變號不變 · 內容變記版本史 · 消失標退役不刪 · 內容有變才出新版。"""
    import datetime
    import importlib.metadata as md
    root = Path(home or HERE)
    rd = Path(rd or root / "registry")
    rd.mkdir(parents=True, exist_ok=True)
    fams = {}
    for p in list(root.rglob("*.py")) + list(root.rglob("*.ps1")):
        if _AF_SKIP.search(str(p)) or not p.is_file():
            continue
        m = re.search(r"^(.*)_v(\d{3,4})$", p.stem)
        k = (str(p.parent), m.group(1) if m else p.stem, p.suffix.lower())
        v = int(m.group(2)) if m else -1
        if k not in fams or v > fams[k][1]:
            fams[k] = (p, v)
    items = _rg_scan([p for p, _ in fams.values()])
    for f in sorted(rd.glob("VRN_Asset_Register_v*.json"))[-1:]:
        try:
            ar = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            ar = {}
        for fam, b in (ar.get("books") or {}).items():
            items.append((_rg_book_kind(fam + " " + str(b.get("tail", ""))), fam, str(b.get("tail", "")), str(b.get("version", "")), str(b.get("sha", b.get("hash", "")))[:12], "檔案冊 · 舊號 %s" % b.get("no", "")))
        for nm, pv in (ar.get("params") or {}).items():
            items.append(("PARAM", nm, str(pv.get("src", pv.get("file", ""))), "", "", "舊號 %s" % pv.get("no", "")))
    try:
        env = json.loads((Path(rep or Path(_resolve("_rep")()).parent / "vrn2") / "VRN2_Env_latest.json").read_text(encoding="utf-8"))
        for r in env.get("rows") or []:
            try:
                ver = md.version(r["pip"])
            except Exception:  # noqa: BLE001
                ver = "未安裝"
            items.append(("ENV", r["module"], r["pip"], ver, "", "必裝" if r.get("must") else ("頂層" if r.get("hard") else "選裝")))
    except Exception:  # noqa: BLE001
        pass
    prev_f = sorted(rd.glob("VRN2_Component_Register_v*.json"))
    prev = json.loads(prev_f[-1].read_text(encoding="utf-8")) if prev_f else {"entries": {}}
    E = prev.get("entries", {})
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    used = Counter()
    for e in E.values():
        mm = re.match(r"VRN2-([A-Z]+)-(\d{4})$", e.get("no", ""))
        if mm:
            used[mm.group(1)] = max(used[mm.group(1)], int(mm.group(2)))
    seen, changed, new = set(), 0, 0
    merged = {}
    for kind, key, src, ver, fp, note in items:
        ek = "%s|%s" % (kind, key)
        if ek in merged:
            if kind in ("IN", "OUT", "PARAM") and note and note not in merged[ek]["users"]:
                merged[ek]["users"].append(note)
            continue
        merged[ek] = {"kind": kind, "key": key, "src": src, "version": ver, "fp": fp, "note": note if kind not in ("IN", "OUT", "PARAM") else "", "users": [note] if kind in ("IN", "OUT", "PARAM") and note else []}
    for ek, it in sorted(merged.items()):
        seen.add(ek)
        old = E.get(ek)
        if not old:
            used[it["kind"]] += 1
            E[ek] = {"no": "VRN2-%s-%04d" % (it["kind"], used[it["kind"]]), "kind": it["kind"], "key": it["key"], "status": "暫編 · 待 VCGC 核號", "first": now, "last": now,
                     "src": it["src"], "version": it["version"], "fp": it["fp"], "note": it["note"], "users": it["users"], "history": [{"at": now, "version": it["version"], "fp": it["fp"]}]}
            new += 1
            continue
        if old.get("status", "").startswith("退役"):
            old["status"] = "暫編 · 待 VCGC 核號"
            changed += 1
        if (it["fp"] and it["fp"] != old.get("fp")) or (it["version"] and it["version"] != old.get("version")):
            old["history"].append({"at": now, "version": it["version"], "fp": it["fp"]})
            changed += 1
        old.update(src=it["src"], version=it["version"], fp=it["fp"] or old.get("fp", ""), note=it["note"] or old.get("note", ""), users=sorted(set(old.get("users", [])) | set(it["users"])))
    retired = 0
    for ek, e in E.items():
        if ek not in seen and not e.get("status", "").startswith("退役"):
            e["status"] = "退役(現役尾版已不含 · 保留不刪)"
            e["last"] = now
            retired += 1
    cnt = {k: sum(1 for e in E.values() if e["kind"] == k and not e["status"].startswith("退役")) for k in _RG_KINDS}
    L = ["[計] 元件登記(VRN-2 register)· 現役 %d · 本次新登 %d · 內容變 %d · 退役 %d(保留)· %s" % (sum(cnt.values()), new, changed, retired, " · ".join("%s %d" % (_RG_LABEL[k], v) for k, v in cnt.items() if v))]
    if new or changed or retired or not prev_f:
        nv = (int(re.search(r"_v(\d{4})", prev_f[-1].name).group(1)) + 1) if prev_f else 100
        out = rd / ("VRN2_Component_Register_v%04d.json" % nv)
        out.write_text(json.dumps({"schema": "VIA.VRN2.ComponentRegister.v1", "at": now, "writer": DISPLAY_NAME + " " + TAG, "rule": "編號 VRN2-<類>-#### 暫編待 VCGC 核號 · 鍵不變號不變 · 內容變記版本史 · 消失標退役不刪 · 有變才出新版",
                                   "counts": cnt, "entries": E}, ensure_ascii=False, indent=1), encoding="utf-8")
        cdir = root / "contract"
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / "VRN2_NUMBER_REQUEST_latest.json").write_text(json.dumps({"from": "VRN-2", "register": out.name, "pending": [e["no"] for e in E.values() if e["status"].startswith("暫編")]}, ensure_ascii=False), encoding="utf-8")
        L.append("[計] 元件登記冊 → registry/%s(內容有變才出新版)· 核號請求 contract/VRN2_NUMBER_REQUEST_latest.json" % out.name)
    else:
        L.append("[計] 元件登記冊無變更 · 沿用 %s" % prev_f[-1].name)
    return 0, L, E, cnt


def _register_html(E: dict, cnt: dict) -> str:
    if not E:
        return ""
    lamp = lambda e: "GRAY" if e["status"].startswith("退役") else ("GREEN" if e["status"].startswith("已確認") else "YELLOW")  # noqa: E731
    li = lambda l: "<i style='background:%s'></i>" % _V2C.get(l, "#9ca3af")  # noqa: E731
    parts = ["<h3>%s元件登記冊(VRN-2 · 現役 %d · 黃 = 暫編待 VCGC 核號 · 灰 = 退役保留)</h3><div class='sum'>%s</div>" % (li("YELLOW"), sum(cnt.values()), "".join("<span>%s %d</span>" % (_RG_LABEL[k], v) for k, v in cnt.items() if v))]
    for k in _RG_KINDS:
        es = sorted((e for e in E.values() if e["kind"] == k), key=lambda e: e["no"])
        if not es:
            continue
        rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>" % (li(lamp(e)), e["no"], html.escape(e["key"]), html.escape(e.get("src", "")), html.escape(e.get("version", "")), len(e.get("history", [])), html.escape((e.get("note") or " · ".join(e.get("users", [])))[:80])) for e in es[:150])
        more = "<tr><td colspan='7' style='color:#6b7280'>…另 %d 筆在 registry JSON</td></tr>" % (len(es) - 150) if len(es) > 150 else ""
        parts.append("<details><summary>%s(%d)</summary><table><tr><th>燈</th><th>編號</th><th>鍵</th><th>來源</th><th>版本</th><th>版本史</th><th>備註 / 使用者</th></tr>%s%s</table></details>" % (_RG_LABEL[k], len(es), rows, more))
    return "".join(parts)


_V2C = {"GREEN": "#16a34a", "YELLOW": "#eab308", "RED": "#dc2626", "GRAY": "#9ca3af"}

_SK_EXCL = re.compile(r"(?i)晨會|早報|盤後|盤勢|ETF|籌碼|總經|論壇|第.場|專題|產業|Databook|summit|Insights|hardware|Thermal|Memory|Automation|PCB|ABF|CPO|AI Power|TPU|Components|觀察家|[周週]報|解盤|股市分析|股分析|鋼鐵")
_SK_BROKER = [("兆豐", r"兆豐"), ("國泰", r"國泰|團泰|Cathay"), ("中信", r"中國信託|中國僖託|CTBC"), ("凱基", r"凱基|KGI"), ("華南", r"華南|Hua Nan"), ("凱基", r"凱基|KGI"), ("華南", r"華南"), ("統一", r"統一投顧"), ("國泰", r"國泰"), ("中信", r"CTBC|中信"), ("群益", r"群益"), ("元富", r"元富"), ("台新", r"台新"),
              ("Morgan Stanley", r"(?i)(?:^|[_\- ])ms(?:[_\- ]|$)"), ("Goldman Sachs", r"(?i)^GS[-_ ]"), ("J.P. Morgan", r"(?i)^JP[-_ ]"), ("UBS", r"(?i)ubs"), ("Citi", r"(?i)citi"),
              ("Daiwa", r"(?i)daiwa"), ("CLSA", r"(?i)CLS[AT]"), ("GF", r"(?i)^GF"), ("Macquarie", r"(?i)^MQ[-_ ]")]
_SK_ANNUAL = re.compile(r"^(?:FY)?(?:19|20)\d{2}(?:[AEFP]|\([AEFP]\)|年度?|CT)?$|^\d{2}[AEFP]$|^FY\d{2}[AEFP]?$|^(?:Dec|Mar|Jun|Sep)-\d{2}[AEFP]?$|^1[01]\d年[AEFP]?$|^12/\d{2}[AEFP]?$", re.I)
_SK_EPS = re.compile(r"(?i)EPS|每股盈餘|每股純益|Earnings per share")
_SK_VAL = [("本益比", r"(?i)本益比|P/E|\bPERs?\b"), ("股價淨值比", r"(?i)股價淨值比|本淨比|P/B|\bPBR\b|P/BV"), ("ROE", r"(?i)ROE|股東權益報酬率|ROAE"), ("殖利率", r"(?i)殖利率|Dividend yield|Div yld"),
           ("EV/EBITDA", r"(?i)EV/EBITDA"), ("目標價", r"(?i)目標價|Target price|Price target|\bTP\b"), ("每股淨值", r"(?i)每股淨值|BVPS")]


_SK_NOTE = re.compile(r"(?i)Background:|We met with|update with the management|(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (?:monthly )?(?:sales|revenue)|\bUpdate\b|\bFlash\b|\bNote\b|Takeaway|Summit|速報|摘要|法說|座談|Monthly|monthly (?:sales|revenue)|月營收|Nov Rev|Sep revenue|revenue \+")
_SK_NR = re.compile(r"(?i)\bNote\b|\bNR\b|未評等|Not rated|Takeaway|法說|座談")
_NUMC = re.compile(r"^[\(\-−]?[\d,]+(?:\.\d+)?%?\)?$|^n\.?a\.?$|^-+$|^NM$", re.I)


def _sk_date(nm: str) -> str:
    m = re.search(r"(20\d{2})[-_.]?([01]\d)[-_.]?([0-3]\d)", nm)
    if m:
        return "%s-%s-%s" % m.groups()
    m = re.search(r"(?<!\d)1(1\d)([01]\d)([0-3]\d)(?!\d)", nm)
    if m:
        return "%d-%s-%s" % (1911 + 100 + int(m.group(1)), m.group(2), m.group(3))
    m = re.search(r"(?<!\d)(2\d)([01]\d)([0-3]\d)(?!\d)", nm)
    return "20%s-%s-%s" % m.groups() if m else ""


def _sk_ticker(nm: str, title: str) -> str:
    for t in re.findall(r"(?<!\d)(\d{4})(?!\d|年)", nm):
        if not re.match(r"20[1-3]\d$", t) or re.search(t + r"\s?(?:TT|\)|,)", nm):
            return t
    m = re.search(r"\(?(?<!\d)(\d{4})(?:\s?TT|\.TWO?|\s?TW|\))", title) or re.search(r"\(([A-Z]{1,5})\s?US\)", title)
    return m.group(1) if m else ""


def stock_eval(r: dict, npages: int) -> dict:
    """個股報告四項:檔名 · 首頁 · 年度財報頁 · 年度重要財報及評價資訊 → 每項 GREEN / YELLOW / RED / GRAY + 說明。"""
    f = r.get("file", "")
    pages = r.get("pages") or []
    zs = [(pg.get("pno", 1), z) for pg in pages for z in pg.get("zones") or []]
    ztxt = lambda z: " ".join(x.get("text", "") for x in z.get("records") or []) + " " + " ".join(c for row in (z.get("rows") or []) for c in row if c)  # noqa: E731
    title = " ".join(ztxt(z) for p, z in zs if p == 1 and z.get("major") in ("T", "L", "R"))
    tk, dt = _sk_ticker(f, title), _sk_date(f)
    if not dt:
        m = re.search(r"(20\d{2})[/.\-年]\s?(\d{1,2})[/.\-月]\s?(\d{1,2})", title)
        dt = "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3))) if m else ""
    if not tk or _SK_EXCL.search(f):
        return {"stock": False, "file": f, "why": "產業 / 晨報 / 盤後 / ETF / 論壇等" if tk else "沒有個股代號"}
    br = next((n for n, rx in _SK_BROKER if re.search(rx, f)), "") or next((n for n, rx in _SK_BROKER if re.search(rx, title)), "")
    p1all = " ".join(ztxt(z) for p, z in zs if p == 1)
    nr = bool(_SK_NR.search(f) or _SK_NR.search(title[:400]))
    note = bool(_SK_NOTE.search(f) or _SK_NOTE.search(title[:400]) or _SK_NOTE.search(p1all[:600])) or nr
    notext = "首頁無文字層 → OCR 排隊" in (r.get("reasons") or []) or not any(p == 1 for p, _ in zs)
    p_fn = ("GREEN" if br and dt else "YELLOW", "代號 %s · 日期 %s · 券商 %s" % (tk, dt or "—", br or "—"))
    rt = [ztxt(z)[:40] for p, z in zs if p == 1 and z.get("minor") == "RT"]
    miss = "首頁沒抓到評等 / 目標價" in (r.get("reasons") or []) or any(str(x).startswith("首頁沒抓到評等") for x in (r.get("na") or []))   # v0225 ENG397 v0122 不適用改備註 · 判斷口徑不變
    if notext:
        p_p1 = ("RED", "首頁無文字層(影像 PDF)→ OCR 排隊")
    elif miss and note:
        p_p1 = ("GRAY", "Note / 未評等 / 快訊 · 首頁本來沒有評等")
    else:
        p_p1 = ("YELLOW" if miss else "GREEN", rt[0] if rt else "")
    ann = []
    for p, z in zs:
        if z.get("minor") != "TB":
            continue
        rows = [[c.strip() for c in row if c and c.strip()] for row in (z.get("rows") or [])]
        rows = [r_ for r_ in rows if r_]
        hdr = next((r_ for r_ in rows if sum(1 for c in r_ if _SK_ANNUAL.match(c)) >= 2), None)
        tr = [r_ for r_ in rows if _SK_ANNUAL.match(r_[0]) and sum(1 for c in r_[1:] if _NUMC.match(c)) >= 2]
        if hdr:                                                     # 年度欄在表頭
            na = sum(1 for c in hdr if _SK_ANNUAL.match(c))
            nr = [r_ for r_ in rows if sum(1 for c in r_ if _NUMC.match(c)) >= 2]
            tidy = bool(nr) and sum(1 for r_ in nr if na <= sum(1 for c in r_ if _NUMC.match(c)) <= na + 2 or len(r_) % na <= 2) / len(nr) >= 0.6
            ann.append((p, z.get("id"), "期間欄" in (z.get("engine") or "") or tidy))
        elif len(tr) >= 2:                                          # 年份往下排(第一欄是年度)
            ann.append((p, z.get("id"), True))
    short = not ann and r.get("fin_n", 0) == 0 and (note or 0 < npages <= 4)
    if ann:
        al = [a for a in ann if a[2]]
        p_fin = ("GREEN" if al else "YELLOW", "年度表 %d 張(期間欄對齊 %d)· %s" % (len(ann), len(al), " ".join(str(a[1] or "P%d" % a[0]) for a in ann[:3])))
    elif any(sum(1 for t in x.get("text", "").split() if _SK_ANNUAL.match(t.strip("()"))) >= 3 for _, z in zs for x in (z.get("records") or [])):
        p_fin = ("YELLOW", "年度數據在文字段(未切成表 · 引擎待修)")
    elif short:
        p_fin = ("GRAY", "快訊 / 更新 / 摘要(%s頁)· 未附年度財報" % (npages or "?"))
    else:
        p_fin = ("YELLOW", "沒有年度表(財報頁 %d · 全文 %s 頁)" % (r.get("fin_n", 0), npages or "?"))
    alltxt = " ".join(ztxt(z) for _, z in zs)
    vh = [n for n, rx in _SK_VAL if re.search(rx, alltxt)]
    eps = bool(_SK_EPS.search(alltxt))
    if eps and len(vh) >= (1 if note else 2):
        p_val = ("GREEN", "EPS + " + " · ".join(vh))
    elif note and not (eps and vh):
        p_val = ("GRAY", "快訊 / 摘要 · 未附完整評價" + (("(只有 " + " · ".join(vh) + ")") if vh else ""))
    elif short and not vh:
        p_val = ("GRAY", "快訊 / 摘要 · 未附評價表")
    else:
        p_val = ("YELLOW", ("EPS ✓ · " if eps else "缺 EPS · ") + ("評價 " + " · ".join(vh) if vh else "沒有評價指標"))
    parts = {"檔名": p_fn, "首頁": p_p1, "年度財報": p_fin, "評價資訊": p_val}
    ocr = r.get("lamp") == "RED"
    worst = "RED" if ocr else ("YELLOW" if any(v[0] == "YELLOW" for v in parts.values()) else "GREEN")
    return {"stock": True, "file": f, "ticker": tk, "date": dt, "broker": br, "parts": parts, "ocr": ocr, "lamp": worst}


def _npages(p: Path) -> int:
    try:
        import pypdfium2 as pdfium  # noqa: WPS433
        d = pdfium.PdfDocument(str(p))
        n = len(d)
        d.close()
        return n
    except Exception:  # noqa: BLE001
        try:
            import pdfplumber  # noqa: WPS433
            with pdfplumber.open(str(p)) as d:
                return len(d.pages)
        except Exception:  # noqa: BLE001
            return 0


# ===== v0215 完成驗收(acceptance)=====
_ACC_ORACLE = {  # 成功紀錄(VRN_Summarizer_Optimization_v0104 real_validation · 53 項 PASS · 人工逐項核對)
    "Daiwa-1319": {"target": "100", "current": "78.90", "old_target": "91", "upside": "26.7", "eps": {2023: "5.185", 2024: "5.531", 2025: "6.145"}, "title": "Anticipating another round of upward EPS revisions"},
    "MS-2308": {"target": "1288.00", "current": "932.00", "old_target": None, "upside": "38", "eps": {2024: "13.56", 2025: "23.73", 2026: "35.03", 2027: "42.14"}, "title": "What's Next? Business Extension to Power AI"},
    "GS-6415": {"target": "650.00", "current": "468.00", "old_target": "310", "upside": "38.9", "eps": {2025: "6.40", 2026: "11.48", 2027: "21.66", 2028: "32.44"},
                "title": "Data center and auto segments set to fuel next earnings upcycle; Upgrade to Buy; TP up to NT$650"},
}
_ACC_NUM = re.compile(r"\(?-?\d[\d,]*(?:\.\d+)?%?\)?")
_ACC_BS = {"mi": r"^(?:少數股(?:權|東權益)|非控制權益|Minority interests?|Non-?controlling interests?)", "ta": r"^(?:資產總(?:額|計)|總資產|Total assets)", "tl": r"^(?:負債總(?:額|計)|總負債|Total liabilities(?! (?:and|&)))", "te": r"^(?:(?:股東)?權益總(?:額|計)|總權益|Total (?:shareholders'? |stockholders'? )?equity(?! (?:and|&))|Shareholders'? equity)"}
_ACC_ROWS = {"rev": r"^(?:營業收入(?:淨額)?|營收(?:淨額)?|Revenues?|Revenue, net|Net (?:sales|revenues?)|Sales|Total revenues?)", "gp": r"^(?:營業毛利(?:淨額)?|毛利(?!率)|Gross profit)",
             "gm": r"^(?:營業毛利率|毛利率|Gross margin|GPM)", "op": r"^(?:營業利益(?!率)|Operating (?:income|profit)|EBIT\b(?!DA))", "om": r"^(?:營業利益率|營益率|Operating margin|OPM|EBIT(?: \([^)]*\))? margin)",
             "ni": r"^(?:稅後(?:純益|淨利)|本期淨利|淨利(?!率)|Net (?:income|profit))", "nm": r"^(?:稅後(?:純益|淨利)率|淨利率|Net margin)"}


_ACC_DISCL = r"本刊所刊載|僅做為參考|恕不負擔|並不適合每一個投資人|從事特定交易|資料來源\s*[:：]|Analysts?'? Compensation|research analysts responsible|please contact your sales|[（(]\s*[左右]軸\s*[)）]"   # v0225 上輪重點含免責 / 圖例 = 假綠
_ACC_BANNER = re.compile(r"(?i)^\s*(?:goldman\s+)?sachs\s*[|I｜l]?\s*(?:equity\s+)?research\s*$|^\s*(?:equity|global\s+investment)\s+research\s*$|^\s*research\s*$")


def _acc_dec(t: str):
    from decimal import Decimal, InvalidOperation
    if re.match(r"^\s*[,，]\d", t or ""):
        return None                                                    # v0220 逗號開頭 = 擷取斷裂 · 不當數字
    t = (t or "").strip().replace(",", "").replace("%", "")
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    try:
        d = Decimal(t)
    except (InvalidOperation, ValueError):
        return None
    return -d if neg else d


def _acc_key(d) -> str:
    return "{:f}".format(abs(d).normalize()) if d is not None else ""


def _acc_page_text(pdf: Path, pnos: list, figs: dict = None, foot: dict = None) -> dict:
    """頁面文字層;figs = {頁: [圖區框]} 時排除圖內座標字(圖表內字刻意不進文字區 · 覆蓋率不算)。"""
    out = {}
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf)) as doc:
            for n in pnos:
                if 1 <= n <= len(doc.pages):
                    pg = doc.pages[n - 1]
                    if figs is not None:
                        fb = list(figs.get(n) or []) + [(float(i["x0"]), float(i["top"]), float(i["x1"]), float(i["bottom"])) for i in pg.images]   # 點陣圖上的 OCR 隱形字也算圖內
                        try:
                            _ws = pg.extract_words(extra_attrs=["upright"])
                        except Exception:  # noqa: BLE001
                            _ws = pg.extract_words()
                        ws = [w for w in _ws if w.get("upright", True) and not any(b[0] - 1 <= w["x0"] and w["x1"] <= b[2] + 1 and b[1] - 1 <= w["top"] and w["bottom"] <= b[3] + 1 for b in fb)]
                        if foot is not None:                               # v0225 頁尾(頁面最底部 8%)不算 · 頁尾依規則不擷取
                            ws = [w for w in ws if not w["top"] > 0.92 * float(pg.height)]
                        out[n] = " ".join(w["text"] for w in ws)
                    else:
                        out[n] = pg.extract_text() or ""
    except Exception:  # noqa: BLE001
        pass
    return out


def _acc_pdfium_text(pdf: Path, pnos: list) -> dict:
    """v0216 第二讀取器(pypdfium2):pdfplumber 文字層壞掉的頁(凱基首頁 · MS-2308 P6)回查用。"""
    out = {}
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(pdf))
        for n in pnos:
            if 1 <= n <= len(doc):
                out[n] = doc[n - 1].get_textpage().get_text_range()
    except Exception:  # noqa: BLE001
        pass
    return out


def _acc_numset(text: str) -> set:
    import unicodedata
    t = unicodedata.normalize("NFKC", text or "")
    t2 = re.sub(r"(?<=[\d,.])\s+(?=[\d,.])", "", t)
    out = {_acc_key(_acc_dec(m)) for x in (t, t2) for m in _ACC_NUM.findall(x) if _acc_dec(m) is not None}
    for x in (t, t2):                                                  # 緊鄰兩欄被黏住(88,469101,908)→ 拆開
        for m in re.findall(r"[\d,]{9,}", x):
            out |= {_acc_key(_acc_dec(p)) for p in re.findall(r"\d{1,3}(?:,\d{3})+", m)}
    return out


def _acc_year(p: str):
    p = (p or "").strip()
    m = re.search(r"(?:19|20)(\d{2})", p) if re.search(r"(?:19|20)\d{2}", p) else re.search(r"(?:/|-|FY)(\d{2})", p, re.I)
    return 2000 + int(m.group(1)) if m else None


def _acc_series(zones: list) -> dict:
    """全份報告合併(相容 v0215):{鍵: {年: 原字串}}(取第一張表)。"""
    out = {}
    for t in _acc_tables(zones):
        for k, d in t.items():
            for y, v in d.items():
                out.setdefault(k, {}).setdefault(y, v)
    return out


def _acc_tables(zones: list) -> list:
    """v0216 逐表:[{鍵: {年: 原字串}}];表頭同一年多欄 → 取最右(年度欄在季度欄右邊);成長率章節底下不取。"""
    out = []
    for z in zones:
        rows = z.get("rows") or []
        if z.get("kind") not in ("表", "表文") or len(rows) < 3:
            continue
        hdr = next((i for i, r in enumerate(rows) if sum(1 for c in r if c and _acc_year(c) and re.match(r"^(?:FY)?\d{2,4}|^\d{1,2}/\d{2}|^Dec-\d{2}|^\d{2,3}年", c.strip())) >= 2), None)
        if hdr is None:
            continue
        cols = {}
        for i, c in enumerate(rows[hdr]):
            if i and c and _acc_year(c):
                y = _acc_year(c)
                for j in [j for j, yy in cols.items() if yy == y]:
                    del cols[j]                                        # 同年多欄 → 留最右
                cols[i] = y
        growth = False
        tab = {}
        for r in rows[hdr + 1:]:
            lab = (r[0] if r else "").strip()
            if lab and not any((c or "").strip() for c in r[1:]):
                growth = bool(re.search(r"成長率|增率|growth|yoy", lab, re.I))
                continue
            if growth or re.search(r"成長|growth|yoy|§|consensus|prior|舊", lab, re.I):
                continue
            for k, rx in list(_ACC_ROWS.items()) + [("eps", r"^(?:EPS|每股(?:稅後)?盈餘|每股收益)"), ("cogs", r"^(?:營業成本|銷貨成本|Cost of (?:goods sold|sales|revenues?)|COGS)")] + list(_ACC_BS.items()):
                if re.search(rx, lab, re.I) and not (k in ("op", "gp", "ni", "rev") and re.search(r"率|margin|%", lab, re.I)):
                    for i, y in cols.items():
                        if i < len(r) and (r[i] or "").strip():
                            if k == "eps":
                                tab.setdefault("eps_all", {}).setdefault(y, set()).add(r[i].strip())
                            tab.setdefault(k, {}).setdefault(y, r[i].strip())
                    break
        if tab:
            out.append(tab)
    return out


def _acc_calc(zones: list) -> tuple:
    """① 全份報告跨表重算:利潤率 = 利潤 ÷ 營收(依年度對齊 · 容差依原文小數位 + 0.15pp)。"""
    ok, bad, det = 0, 0, []
    T = _acc_tables(zones)
    pall = {}
    for t in T:
        for k in ("gm", "om", "nm"):
            for y, v in t.get(k, {}).items():
                pall.setdefault(k, {}).setdefault(y, v)
    seen = set()
    for t in T:
      for num, den, pct in (("gp", "rev", "gm"), ("op", "rev", "om"), ("ni", "rev", "nm")):
        same = bool(t.get(pct))
        P = t.get(pct) or pall.get(pct, {})                            # 比率優先同表 · 否則跨表(比率沒有單位)
        for y in sorted(set(t.get(num, {})) & set(t.get(den, {})) & set(P)):
            if (pct, y) in seen:
                continue
            seen.add((pct, y))
            S = {num: t[num], den: t[den], pct: P}
            a, b, p = _acc_dec(S[num][y]), _acc_dec(S[den][y]), _acc_dec(S[pct][y])
            if a is None or b in (None, 0) or p is None:
                continue
            calc = a / b * 100
            if abs(p) <= 1 and abs(calc) > 1.5:
                p = p * 100
            raw = S[pct][y]
            dp = len(raw.split(".")[1].rstrip("%)")) if "." in raw else 0
            tol = 0.5 * (10 ** -dp) + 0.15
            alt = None
            if pct == "gm" and abs(calc - p) > tol and y in t.get("cogs", {}) and _acc_dec(t["cogs"][y]) is not None:
                alt = (b - abs(_acc_dec(t["cogs"][y]))) / b * 100            # 毛利率以「營收 − 營業成本」計(毛利淨額為調整後)
            if abs(calc - p) <= tol or (alt is not None and abs(alt - p) <= tol):
                ok += 1
                if alt is not None and abs(alt - p) <= tol:
                    det.append("〔定義〕gm %d:毛利率 %s = (營收 − 營業成本) ÷ 營收 %.2f%%(表內毛利 %s 為調整後淨額)" % (y, raw, alt, S[num][y]))
            elif same:
                bad += 1
                det.append("%s %d:%s ÷ %s = %.2f%% ≠ 表上 %s" % (pct, y, S[num][y], S[den][y], calc, raw))
            else:
                det.append("〔原文跨表不一致〕%s %d:損益表 %s ÷ %s = %.2f%% · 比率表 %s" % (pct, y, S[num][y], S[den][y], calc, raw))
    from decimal import Decimal as _D
    for t in T:                                                            # v0226 資產 = 負債 + 權益(同表)
        for y in sorted(set(t.get("ta", {})) & set(t.get("tl", {})) & set(t.get("te", {}))):
            a_, l_, q_ = _acc_dec(t["ta"][y]), _acc_dec(t["tl"][y]), _acc_dec(t["te"][y])
            if a_ is None or l_ is None or q_ is None or a_ <= 0 or l_ < 0 or q_ <= 0 or q_ < a_ * _D("0.01") or l_ > a_ * _D("1.5"):
                continue                                                   # v0229 合理性:負值 / 權益 <1% 資產 / 負債 >1.5 倍資產 = 不是資產負債表列(6933 誤報)
            m_ = _acc_dec(t.get("mi", {}).get(y, "")) if t.get("mi", {}).get(y) else None
            if abs(a_ - (l_ + q_)) <= max(1, abs(a_) * _D("0.002")) or (m_ is not None and abs(a_ - (l_ + q_ + m_)) <= max(1, abs(a_) * _D("0.002"))):
                ok += 1                                                    # 含少數股權 / 非控制權益也算平
            else:
                det.append("〔原文恆等式〕%d:資產 %s ≠ 負債 %s + 權益 %s(差 %s · 可能含少數股權或科目口徑不同)" % (y, t["ta"][y], t["tl"][y], t["te"][y], a_ - l_ - q_))
    return ok, bad, det


def _acc_calc_table(zones: list) -> tuple:
    """(v0215 初版:同表內重算 · 保留)"""
    ok, bad, det = 0, 0, []
    for z in zones:
        rows = z.get("rows") or []
        if z.get("kind") != "表" or len(rows) < 3:
            continue
        hdr = next((i for i, r in enumerate(rows) if sum(1 for c in r if c and re.match(r"^(?:FY)?\d{2,4}|^\d{1,2}/\d{2}|^Dec-\d{2}|^\d{2,3}年", c.strip())) >= 2), None)
        if hdr is None:
            continue
        found = {}
        for r in rows[hdr + 1:]:
            lab = (r[0] if r else "").strip()
            for k, rx in _ACC_ROWS.items():
                if k not in found and re.search(rx, lab, re.I):
                    found[k] = r
        for num, den, pct in (("gp", "rev", "gm"), ("op", "rev", "om"), ("ni", "rev", "nm")):
            if not all(k in found for k in (num, den, pct)):
                continue
            for c in range(1, min(len(found[num]), len(found[den]), len(found[pct]))):
                a, b, p = _acc_dec(found[num][c]), _acc_dec(found[den][c]), _acc_dec(found[pct][c])
                if a is None or b in (None, 0) or p is None:
                    continue
                calc = a / b * 100
                if abs(p) <= 1 and abs(calc) > 1.5:
                    p = p * 100
                dp = len(found[pct][c].split(".")[1].rstrip("%)")) if "." in found[pct][c] else 0
                tol = 0.5 * (10 ** -dp) + 0.15
                if abs(calc - p) <= tol:
                    ok += 1
                else:
                    bad += 1
                    det.append("%s %s 欄%d:%s ÷ %s = %.2f%% ≠ 表上 %s" % (z.get("id"), pct, c, found[num][c], found[den][c], calc, found[pct][c]))
    return ok, bad, det


def _acc_cover(page_text: str, zones: list) -> float:
    import unicodedata
    def cnt(t):
        return Counter(c for c in unicodedata.normalize("NFKC", t or "") if not c.isspace())
    cp = cnt(page_text)
    if not cp:
        return -1.0
    zt = []
    for z in zones:
        zt += [x.get("text", "") for x in (z.get("records") or []) if isinstance(x, dict)]
        zt += [c for r in (z.get("rows") or []) for c in r if c]
    cz = cnt(" ".join(zt))
    return sum(min(v, cz.get(k, 0)) for k, v in cp.items()) / sum(cp.values())


def _acc_eng062():
    cands = sorted(HERE.glob("VRN_ENG062_SummarizerV1_v*.py"))
    cands = [p for p in cands if int(re.search(r"_v(\d{4})", p.name).group(1)) >= 105]
    if not cands:
        return None, "ENG062 v0105+ 不在"
    try:
        import importlib.util
        sp = importlib.util.spec_from_file_location("vrn_eng062", str(cands[-1]))
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        return m, cands[-1].name
    except Exception as exc:  # noqa: BLE001
        return None, "ENG062 載入失敗 %s" % type(exc).__name__


def _acc_lanes() -> int:
    v = os.environ.get("VIA_VRN2_LANES")
    if v and v.isdigit():
        return max(1, min(3, int(v)))
    n = os.cpu_count() or 1
    try:
        import psutil  # noqa: WPS433
        ram = psutil.virtual_memory().available / 1e9
    except Exception:  # noqa: BLE001
        ram = 2.0
    return 3 if n >= 4 and ram >= 3 else (2 if n >= 2 and ram >= 1.5 else 1)


def _spill() -> Path:
    import tempfile
    d = Path(os.environ.get("VIA_SPILL_DIR") or tempfile.gettempdir()) / ("vrn2_lanes_%d" % os.getpid())
    d.mkdir(parents=True, exist_ok=True)
    return d


def lanes_run(script: str, verb: list, jobs: list, lanes: int, label: str, timeout_s: int = 300, done_line=None) -> tuple:
    """v0117 通用分路器:jobs = [(n, 名稱, 資料)] 平均分 lanes 路 · 每路一個子行程(python script *verb --shard 檔)·
    子行程每份印 @@START n / @@DONE n 並把結果一行 JSON 寫進溢寫夾 · 單份超過 timeout_s → 只停那一路、該份記逾時、剩下的用新子行程接著跑。
    回 ({n: 結果}, [逾時的 n])。"""
    import subprocess
    import threading
    import queue as _q
    import time
    sp = _spill()
    shards = [jobs[k::lanes] for k in range(lanes)]
    out, timed, q = {}, [], _q.Queue()
    total, done_n, t_beat = len(jobs), 0, time.time()
    names = {j[0]: j[1] for j in jobs}
    def launch(k, todo, gen):
        sf = sp / ("%s_shard%d_%d.json" % (label, k, gen))
        of = sp / ("%s_out%d_%d.jsonl" % (label, k, gen))
        sf.write_text(json.dumps({"jobs": todo, "out": str(of)}, ensure_ascii=False, default=str), encoding="utf-8")
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", VIA_VRN2_LANES="1")
        p = subprocess.Popen([sys.executable, "-W", "ignore", script] + verb + ["--shard", str(sf)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace", bufsize=1, env=env)
        def rd():
            for ln in p.stdout:
                q.put((k, gen, ln.rstrip("\n")))
            q.put((k, gen, None))
        threading.Thread(target=rd, daemon=True).start()
        return {"p": p, "todo": [j[0] for j in todo], "of": of, "cur": None, "t": time.time(), "gen": gen, "alive": True, "jobs": {j[0]: j for j in todo}}
    st = {k: launch(k, shards[k], 0) for k in range(lanes) if shards[k]}
    def harvest(s_):
        try:
            for ln in s_["of"].read_text(encoding="utf-8").splitlines():
                if ln.strip():
                    d = json.loads(ln)
                    out[int(d["n"])] = d["r"]
        except OSError:
            pass
    while any(s_["alive"] for s_ in st.values()):
        try:
            k, gen, ln = q.get(timeout=1.0)
        except _q.Empty:
            k = gen = ln = None
        now = time.time()
        if k is not None and st.get(k) and st[k]["gen"] == gen:
            s_ = st[k]
            if ln is None:
                s_["alive"] = False
                harvest(s_)
            elif ln.startswith("@@START "):
                s_["cur"], s_["t"] = int(ln.split()[1]), now
            elif ln.startswith("@@DONE "):
                n = int(ln.split()[1])
                s_["done"] = s_.get("done", set()) | {n}
                s_["cur"] = None
                done_n += 1
                if done_line:
                    print(done_line(n, done_n, total, k), flush=True)
            elif ln.strip() and not ln.startswith("@@"):
                print(ln, flush=True)
        for kk, s_ in list(st.items()):
            _lim = ((s_["jobs"].get(s_["cur"]) or (0, "", {}))[2] or {}).get("timeout", timeout_s) if s_["cur"] is not None else timeout_s   # v0224 逐份時限
            if s_["alive"] and s_["cur"] is not None and now - s_["t"] > _lim:
                n = s_["cur"]
                try:
                    s_["p"].kill()
                except OSError:
                    pass
                s_["alive"] = False
                harvest(s_)
                timed.append(n)
                done_n += 1
                print("  [RED] 逾時 %d 秒 · 第 %d 份 %s · 只停第 %d 路 · 該份記逾時 · 剩下的接著跑" % (_lim, n, str(names.get(n, ""))[:40], kk + 1), flush=True)
                rest = [s_["jobs"][x] for x in s_["todo"] if x != n and x not in out and x not in s_.get("done", set())]
                if rest:
                    st[kk] = launch(kk, rest, s_["gen"] + 1)
        if now - t_beat >= 20:
            t_beat = now
            run_now = ["%d 路:%s" % (kk + 1, str(names.get(s_["cur"], "—"))[:24]) for kk, s_ in st.items() if s_["alive"]]
            print("  [心跳] %s · 平行 %d 路 · 完成 %d/%d · 進行中 %s" % (label, lanes, done_n, total, " | ".join(run_now) or "收尾"), flush=True)
    return out, timed



def _acc_parallel(res: list, indir, sd, stock_files: set, lock_inputs, lanes: int) -> list:
    """v0219 平行驗收:每份交給 _acc_one(子行程)· 依原順序合併 · 逾時的各項記紅。"""
    to = int(os.environ.get("VIA_VRN2_ACC_TIMEOUT") or 300)
    oto = int(os.environ.get("VIA_VRN2_OCR_ACC_TIMEOUT") or 900)
    jobs = [(n, r.get("file", ""), {"r": r, "indir": str(indir), "sd": str(sd), "stock": r.get("file", "") in stock_files, "timeout": oto if r.get("ocr") else to,
             "lock_has": lock_inputs is not None, "lock_sha": (lock_inputs or {}).get(r.get("file", ""))}) for n, r in enumerate(res, 1)]
    print("  [計] 平行驗收 %d 路 · %d 份 · 每份逾時 %d 秒 · 中間結果寫 TEMP 溢寫夾" % (lanes, len(res), to), flush=True)
    def dl(n, k, total, lane):
        return "  [驗收] %d/%d · %s · 第 %d 路" % (k, total, res[n - 1].get("file", "")[:40], lane + 1)
    got, timed = lanes_run(str(Path(__file__).resolve()), ["acc-shard"], jobs, lanes, "accept", to, dl)
    out = []
    for n, r in enumerate(res, 1):
        e = got.get(n)
        if e is None:
            why = ("逾時 %d 秒 · 未完成驗收" % to) if n in timed else "子行程未回報結果"
            e = {"file": r.get("file", ""), "c1": ("RED", why), "c2": ("RED", why), "c3": ("RED", why), "c5": ("RED", why), "c6": ("GRAY", "既有輸入"), "c7": ("GRAY", why)}
        out.append(e)
    return out


def _acc_shard_main(shard: str) -> int:
    """v0219 子行程:逐份驗收 · 每份 @@START / @@DONE · 結果一行 JSON 寫溢寫夾。"""
    import logging
    logging.getLogger("pdfminer").setLevel(logging.ERROR)                # v0221 子行程也不印字型警告
    d = json.loads(Path(shard).read_text(encoding="utf-8"))
    eng, eng_name = (None, "無個股")
    if any(j[2].get("stock") for j in d["jobs"]):
        eng, eng_name = _acc_eng062()
    with open(d["out"], "a", encoding="utf-8") as fh:
        for n, name, data in d["jobs"]:
            print("@@START %d" % n, flush=True)
            lock = None if not data.get("lock_has") else ({name: data["lock_sha"]} if data.get("lock_sha") else {})
            try:
                e = _acc_one(data["r"], data["indir"], data["sd"], eng, eng_name, {name} if data.get("stock") else set(), lock)
            except Exception as exc:  # noqa: BLE001
                e = {"file": name, "c1": ("RED", "驗收失敗 %s" % type(exc).__name__), "c2": ("GRAY", "—"), "c3": ("GRAY", "—"), "c5": ("GRAY", "—"), "c6": ("GRAY", "—"), "c7": ("GRAY", "—")}
            fh.write(json.dumps({"n": n, "r": e}, ensure_ascii=False, default=str) + "\n")
            fh.flush()
            print("@@DONE %d" % n, flush=True)
    return 0


def _acc_ocr_xcheck(zones: list) -> tuple:
    """v0225 OCR 表算術交叉驗證:成長率列 = 前後年相除(容許 rounding)· 本益比 × EPS 各年一致(±1.5%)。回 (檢查數, 通過數, 說明)。"""
    from decimal import Decimal
    n = ok = 0
    for z in zones:
        if z.get("kind") != "表" or not str(z.get("engine", "")).startswith("rapidocr"):
            continue
        rows = z.get("rows") or []
        if len(rows) < 3:
            continue
        def key(lab):
            return re.sub(r"[^a-z]", "", re.sub(r"[\(\[\{].*?[\)\]\}]", "", (lab or "").lower()))
        def unit(c):
            c = (c or "").strip()
            return Decimal(1).scaleb(-len(c.split(".")[1])) / 2 if "." in c else Decimal("0.5")
        vals = {}
        for r in rows[1:]:
            vals[key(r[0])] = (r[0], [(_acc_dec(c), c) for c in r[1:]])
        for gk, (glab, gv) in vals.items():
            if "growth" not in gk:
                continue
            base = gk.replace("growth", "")
            bk = next((k for k in vals if "growth" not in k and k and (k.startswith(base) or base.startswith(k))), None)
            if not bk:
                continue
            bv = vals[bk][1]
            for t in range(1, min(len(bv), len(gv))):
                a, b, g = bv[t - 1][0], bv[t][0], gv[t][0]
                if a in (None, 0) or b is None or g is None:
                    continue
                calc = (b / a - 1) * 100
                tol = abs(b / a) * (unit(bv[t][1]) / abs(b) + unit(bv[t - 1][1]) / abs(a)) * 100 + unit(gv[t][1]) + Decimal("0.06")
                n += 1
                ok += abs(calc - g) <= tol
        pers = [k for k in vals if k.startswith("per") or k.startswith("pe")]
        epss = [k for k in vals if k.startswith("eps") and "growth" not in k]
        for pk in pers:
            for ek in epss:
                prod = [p_[0] * e_[0] for p_, e_ in zip(vals[pk][1], vals[ek][1]) if p_[0] and e_[0]]
                if len(prod) >= 3:
                    med = sorted(prod)[len(prod) // 2]
                    n += len(prod)
                    ok += sum(abs(x - med) <= med * Decimal("0.015") for x in prod)
                    break
    return n, ok, "OCR 表內計算交叉驗證 %d/%d 通過(成長率 = 前後年相除 · 本益比 × EPS 各年一致)" % (ok, n)


def _acc_ocr_cache_text(pdf: Path) -> str:
    """v0225 OCR 快取文字(擷取 + 摘要共用 · VIA_VRN2_OCR_CACHE)。"""
    import hashlib
    d = os.environ.get("VIA_VRN2_OCR_CACHE")
    if not d or not Path(d).is_dir():
        return ""
    try:
        h = hashlib.sha1(Path(pdf).read_bytes()).hexdigest()[:16]
    except OSError:
        return ""
    out = []
    for f in Path(d).glob(h + "_p*.json"):
        try:
            out += [x.get("text", "") for r in json.loads(f.read_text(encoding="utf-8")).get("results") or [] for x in r.get("lines") or []]
        except Exception:  # noqa: BLE001
            continue
    return "\n".join(out)


_BI_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
_BI_TEL = re.compile(r"\+\s?\d{2,3}[\s\-]?\(?\d{1,2}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}|\(0\d\)\s?\d{3,4}-\d{4}|(?<![\d-])886[\s\-]\(?\d\)?[\s\-]?\d{4}[\s\-]?\d{4}")   # 不含分機 · 凱基「886 2 2181 8710」
_BI_DOMAIN = {"gs.com": "Goldman Sachs", "jpmorgan.com": "J.P. Morgan", "jpmchase.com": "J.P. Morgan", "morganstanley.com": "Morgan Stanley", "ubs.com": "UBS",
              "kgi.com": "凱基", "cathayfut.com.tw": "國泰", "cathaysec.com.tw": "國泰", "macquarie.com": "Macquarie", "citi.com": "Citi", "daiwa.co.jp": "Daiwa",
              "daiwa-cm.com": "Daiwa", "clsa.com": "CLSA", "megasec.com.tw": "兆豐", "emega.com.tw": "兆豐", "ctbcsec.com": "中信", "entrust.com.tw": "華南",
              "gfgroup.com.hk": "GF", "daiwacm-cathay.com.tw": "Daiwa", "cl-sec.com": "CLSA", "ctbcsis.com": "中信", "ctbcsec.com.tw": "中信", "capital.com.tw": "群益", "pscnet.com.tw": "統一", "nomura.com": "Nomura", "hsbc.com": "HSBC", "bofa.com": "BofA"}
_BI_FILE = [(r"^GS-", "Goldman Sachs"), (r"^JP-", "J.P. Morgan"), (r"^MS-", "Morgan Stanley"), (r"^UBS-", "UBS"), (r"^Citi-", "Citi"), (r"^CLST?-", "CLSA"),
            (r"^Daiwa-|_daiwa_", "Daiwa"), (r"^MQ-", "Macquarie"), (r"^GF", "GF"), (r"_ms_", "Morgan Stanley"), (r"_ubs_", "UBS"), (r"凱基", "凱基"), (r"國泰|^3014TT", "國泰"),
            (r"兆豐", "兆豐"), (r"CTBC|中信", "中信"), (r"華南", "華南"), (r"統一", "統一"), (r"群益", "群益")]


def _bi_norm(t: str) -> str:
    """v0226 字距拆斷修復:「D errick.Yang@」「To mmy.Lai@」→ 接回(只接 1~2 個字母的大寫開頭碎片)· 字母間怪字元 % 去掉 · 授權使用者浮水印(For the exclusive use of x@y)不算。"""
    t = re.sub(r"(?<=[A-Za-z])%(?=[a-z])", "", t or "")
    t = re.sub(r"(?<=[\w.@])-\s*\n\s*(?=[\w.])", "-", t)                     # v0229 Email 跨行(daiwacm-⏎cathay)接回
    t = re.sub(r"@\s*\n\s*", "@", t)
    t = re.sub(r"(?<=[\w])\.\s*\n\s*(?=(?:com|tw|hk|co|jp|net)\b)", ".", t)
    t = re.sub(r"(?i)exclusive use of\s+\S+@\S+", " ", t)
    return re.sub(r"\b([A-Z][a-z]?) ([a-z]{2,}[\w.]*@)", r"\1\2", t)


def _bi_read(text: str) -> dict:
    t = _bi_norm(text)
    em = sorted({e.lower().rstrip(".") for e in _BI_EMAIL.findall(t)})
    tel = sorted({re.sub(r"\D", "", x)[-8:] for x in _BI_TEL.findall(t) if len(re.sub(r"\D", "", x)) >= 8})
    return {"email": em, "tel": tel}


def _bi_cmp(a: list, b: list) -> tuple:
    def same(x, y):                                                       # 同網域且帳號一個是另一個的尾段 = 一條讀法被截斷(mmy.lai ⊂ tommy.lai)
        if x == y:
            return True
        if "@" in x and "@" in y and x.split("@")[1] == y.split("@")[1]:
            lx, ly = x.split("@")[0], y.split("@")[0]
            return len(min(lx, ly, key=len)) >= 4 and (lx.endswith(ly) or ly.endswith(lx))
        return False
    if a and b and a != b and len(a) == len(b) and all(any(same(x, y) for y in b) for x in a):
        return "VERIFIED", "%d/%d 一致(一條讀法截斷 · 取完整)" % (len(a), len(a))
    if a and b and set(a) < set(b):                                       # 區塊是原文的子集合(原文多頁尾總機等)
        return "VERIFIED", "%d/%d 一致(原文另有 %d 筆不在資訊區:頁尾總機等)" % (len(a), len(a), len(set(b) - set(a)))
    if a and b:
        return ("VERIFIED", "%d/%d 一致" % (len(a), len(a))) if a == b else ("CONFLICT", "區塊 %s ≠ 原文 %s" % ("、".join(sorted(set(a) - set(b)))[:60] or "—", "、".join(sorted(set(b) - set(a)))[:60] or "—"))
    if a or b:
        return "SINGLE", "只有%s讀到 %d 筆" % ("區塊" if a else "原文", len(a or b))
    return "MISSING", "兩條讀法都沒有"


def _acc_basic(r: dict, pdf) -> tuple:
    """v0226 ⑦ 基本資料雙讀(學 VRN-1 的雙讀法 · VRN-2 自己實作):讀法 A = ENG397 首頁區塊 · 讀法 B = pypdfium2 獨立讀首頁原文 ·
    Email / 電話逐欄 VERIFIED / CONFLICT / SINGLE / MISSING · 券商由 Email 網域反查並與檔名比對 · 最多黃(提醒)。"""
    zs = [z for pg in r.get("pages") or [] if pg.get("pno") == 1 for z in pg.get("zones", [])]
    ta = "\n".join([x.get("text", "") for z in zs for x in (z.get("records") or []) if isinstance(x, dict)] + [" ".join(c for c in row if c) for z in zs for row in (z.get("rows") or [])])
    tb = _acc_pdfium_text(Path(pdf), [1]).get(1, "")
    A, B = _bi_read(ta), _bi_read(tb)
    em = _bi_cmp(A["email"], B["email"])
    tel = _bi_cmp(A["tel"], B["tel"])
    fb = next((b for rx, b in _BI_FILE if re.search(rx, r.get("file", ""), re.I)), None)
    dom = sorted({_BI_DOMAIN.get(e.split("@")[1]) for e in (A["email"] or B["email"]) if _BI_DOMAIN.get(e.split("@")[1])})
    if dom and fb:
        br = ("VERIFIED", "%s(網域 = 檔名)" % dom[0]) if fb in dom else ("CONFLICT", "網域 %s ≠ 檔名 %s" % ("、".join(dom), fb))
    else:
        br = ("SINGLE", "只有%s" % ("網域 " + "、".join(dom) if dom else "檔名 " + (fb or "—")))
    names = [" ".join(w.capitalize() for w in re.split(r"[._]", e.split("@")[0]) if w.isalpha()) for e in (A["email"] or B["email"])][:3]
    st = {"email": em, "tel": tel, "broker": br, "analysts": names, "email_a": A["email"], "email_b": B["email"]}
    if em[0] == "MISSING" and tel[0] == "MISSING":                       # 首頁沒印分析師聯絡資料(兆豐 / MQ)= 不適用(VRN-1 的 NOT_PRINTED)
        return ("GRAY", "首頁未印分析師聯絡資料 · 券商 %s %s" % (br[0], br[1])), dict(email=em, tel=tel, broker=br, analysts=[], email_a=A["email"], email_b=B["email"])
    rank = {"VERIFIED": 0, "MISSING": 0, "SINGLE": 1, "CONFLICT": 2}
    worst = max((em[0], tel[0], br[0] if br[0] != "SINGLE" else "VERIFIED"), key=lambda x: rank[x])
    lamp = "GREEN" if worst == "VERIFIED" or worst == "MISSING" else "YELLOW"
    note = "Email %s %s · 電話 %s %s · 券商 %s %s%s" % (em[0], em[1], tel[0], tel[1], br[0], br[1], (" · 分析師 " + "、".join(names)) if names else "")
    return (lamp, note), st


def _idem_check(res: list, indir: Path, k: int = 3) -> tuple:
    """v0226 冪等閘(學 VRN-1 G08 · VRN-2 自己實作):本輪挑 k 份(有財報頁的綠燈檔 · 依檔名排序)用同一引擎重跑 · 輸出(去掉序號 / 圖檔路徑)須逐字相同。"""
    import contextlib
    import io
    import shutil
    import tempfile
    pick = sorted([r for r in res if r.get("lamp") == "GREEN" and len(r.get("pages") or []) >= 2], key=lambda r: r.get("file", ""))[:k]
    if not pick:
        return "GRAY", "沒有可重跑的檔"
    engs = sorted(HERE.glob("VRN_ENG397_P1Segment_v[0-9][0-9][0-9][0-9].py"), key=lambda p: int(re.search(r"_v(\d{4})", p.name).group(1)))
    if not engs:
        return "GRAY", "找不到 ENG397"
    import importlib.util
    sp = importlib.util.spec_from_file_location("vrn_eng397_idem", str(engs[-1]))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    tmp = Path(tempfile.mkdtemp(prefix="vrn2_idem_"))
    (tmp / "in").mkdir()
    for r in pick:
        shutil.copy2(str(Path(indir) / r["file"]), str(tmp / "in" / r["file"]))
    old = os.environ.get("VIA_VRN2_LANES")
    os.environ["VIA_VRN2_LANES"] = "1"
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            m.run(tmp / "in", tmp / "rep")
        again = {x["file"]: x for x in json.loads((tmp / "rep" / "p1view" / "P1VIEW_latest.json").read_text(encoding="utf-8"))}
    except Exception as exc:  # noqa: BLE001
        return "RED", "重跑失敗 %s" % type(exc).__name__
    finally:
        if old is None:
            os.environ.pop("VIA_VRN2_LANES", None)
        else:
            os.environ["VIA_VRN2_LANES"] = old
        shutil.rmtree(str(tmp), ignore_errors=True)
    def clean(o):
        if isinstance(o, dict):
            return {k_: clean(v) for k_, v in o.items() if k_ not in ("n", "img")}
        if isinstance(o, list):
            return [clean(v) for v in o]
        return o
    diff = [r["file"] for r in pick if json.dumps(clean(r), sort_keys=True, ensure_ascii=False) != json.dumps(clean(again.get(r["file"], {})), sort_keys=True, ensure_ascii=False)]
    return ("GREEN", "重跑 %d 份輸出逐字相同(%s)" % (len(pick), "、".join(r["file"][:18] for r in pick))) if not diff else ("RED", "重跑不一致 %d 份:%s" % (len(diff), "、".join(d[:24] for d in diff)))


def _acc_one(r: dict, indir, sd, eng, eng_name: str, stock_files: set, lock_inputs) -> dict:
    """v0219:一份的完成驗收(原 acceptance 迴圈主體 · 行為不變)· 循序與平行共用。"""
    import datetime
    import hashlib
    indir, sd = Path(indir), Path(sd)
    f = r.get("file", "")
    pdf = Path(indir) / f
    pages = r.get("pages") or []
    e = {"file": f, "c1": ("GRAY", "無可重算項"), "c2": ("GRAY", "—"), "c3": ("GRAY", "—"), "c5": ("GRAY", "非個股報告"), "c6": ("GRAY", "既有輸入"), "c7": ("GRAY", "非個股報告")}
    if not pdf.exists():
        e["c2"] = e["c3"] = ("GRAY", "PDF 不在")
        return e
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()[:12]
    pt = _acc_page_text(pdf, [pg.get("pno", 1) for pg in pages])
    figs = {pg.get("pno"): [z["bbox"] for z in pg.get("zones", []) if z.get("kind") == "圖" and not z.get("records") and not z.get("rows")] for pg in pages}
    foot = {pg.get("pno"): max([z["bbox"][3] for z in pg.get("zones", []) if z.get("bbox") and z.get("major") != "B" and z.get("minor") not in ("FT", "DS", "PG")] or [0]) + 3 for pg in pages}   # 頁尾 / 免責區不撐下界
    ptc = _acc_page_text(pdf, [pg.get("pno", 1) for pg in pages], figs, foot)
    allz = [z for pg in pages for z in pg.get("zones", [])]
    # ② 覆蓋(圖內座標字不算)
    covs = [(pg.get("pno"), _acc_cover(ptc.get(pg.get("pno"), ""), pg.get("zones", []))) for pg in pages]
    covs = [(n, c) for n, c in covs if c >= 0]
    if covs:
        mn = min(c for _, c in covs)
        e["c2"] = ("GREEN" if mn >= 0.97 else "YELLOW" if mn >= 0.90 else "RED", "最低 P%s %.1f%%" % (min(covs, key=lambda x: x[1])[0], mn * 100))
    # ③ 回查(表格數字 ≥3 位有效字)
    tot = hit = 0
    miss = []
    pt2 = _acc_pdfium_text(pdf, [pg.get("pno", 1) for pg in pages])
    otot = ohit = 0
    for pg in pages:
        ns = _acc_numset(pt.get(pg.get("pno"), "")) | _acc_numset(pt2.get(pg.get("pno"), ""))
        ons = _acc_numset("\n".join(x.get("text", "") for z in pg.get("zones", []) if str(z.get("engine", "")).startswith("rapidocr") for x in (z.get("records") or [])))
        for z in pg.get("zones", []):
            ocr_z = str(z.get("engine", "")).startswith("rapidocr")               # v0223 OCR 表 → 對 OCR 文字
            for row in (z.get("rows") or [])[1:]:
                for c in row[1:]:
                    d = _acc_dec(c)
                    if d is None or len(re.sub(r"\D", "", c)) < 3:
                        continue
                    if ocr_z:
                        otot += 1
                        ohit += _acc_key(d) in ons
                        continue
                    tot += 1
                    if _acc_key(d) in ns:
                        hit += 1
                    elif len(miss) < 5:
                        miss.append("%s %s" % (z.get("id"), c))
    if tot:
        rt = hit / tot
        e["c3"] = ("GREEN" if rt >= 0.99 else "YELLOW" if rt >= 0.95 else "RED", "表格數字 %d/%d 在原文%s" % (hit, tot, (" · 找不到 " + "、".join(miss)) if miss else ""))
    xn, xo, xnote = _acc_ocr_xcheck(allz) if otot else (0, 0, "")
    if otot:
        if ohit == otot and xn >= 3 and xo / xn >= 0.9:                 # v0225 算術交叉驗證通過 → 綠
            on, ol = "OCR 表數字 %d/%d 對 OCR 文字 · %s" % (ohit, otot, xnote), "GREEN"
        else:
            on = "OCR 表數字 %d/%d 對 OCR 文字(影像 PDF 無文字層 · 人工抽查)%s" % (ohit, otot, (" · " + xnote) if xn else "")
            ol = "YELLOW" if ohit / otot >= 0.95 else "RED"
        e["c3"] = ((e["c3"][0] if e["c3"][0] in ("RED",) else ol) if tot else ol, ((e["c3"][1] + " · ") if tot else "") + on)
    # ① 計算
    ok, bad, det = _acc_calc(allz)
    frag = ["%s「%s」" % (z.get("id"), c.strip()) for z in allz if z.get("kind") == "表" for row in (z.get("rows") or []) for c in row if re.match(r"^\s*[,，]\d{3}", c or "")]
    calc_note = []
    if ok or bad:
        calc_note.append("表內利潤率重算 %d 過 %d 不符" % (ok, bad))
    # ⑤ 摘要(個股)
    if f in stock_files:
        if eng is None:
            e["c5"] = ("GRAY", eng_name)
        else:
            cf = sd / ("%s_%s.json" % (sha, eng_name.replace(".py", "")))
            try:
                sm = json.loads(cf.read_text(encoding="utf-8")) if cf.exists() else None
                if sm is None:
                    try:
                        sm = eng.summarize_pdf(str(pdf))
                    except ValueError as exc:
                        if "NO_TEXT" not in str(exc):
                            raise
                        sm = {"_no_text": True}
                    cf.write_text(json.dumps(sm, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
                if sm.get("_no_text"):
                    raise ValueError("NO_TEXT")
                pts = sm.get("points") or []
                good = [p for p in pts if p.get("status") in ("EVIDENCE_FOUND", "EXTRACTIVE") and p.get("evidence")]
                title = (sm.get("title_original") or "").strip()
                lamp = "GREEN" if title and len(pts) == 4 and len(good) == 4 else "YELLOW"
                note = "標題%s · 四點有證據 %d/4" % ("✓" if title else "缺", len(good))
                _tp_printed = bool(re.search(r"(?i)(目標價|target price|price target|\bTP\b)[^\n]{0,25}?\d", "\n".join(str(v) for v in pt.values())))
                if len(pts) == 4 and pts[0] not in good and len(good) == 3 and all(p in good for p in pts[1:]) and not ((sm.get("metrics") or {}).get("target") or {}).get("value") and not _tp_printed:
                    lamp = "GREEN" if title else "YELLOW"                      # v0229 報告沒印目標價(Note / 未評等 / 介紹)→ 目標價那點不適用
                    note = "標題%s · 四點有證據 3/3(目標價未印 · 不適用)" % ("✓" if title else "缺")
                up = (sm.get("validation") or {}).get("upside")
                if up == "PASS":
                    ok += 1
                    calc_note.append("上漲空間重算相符")
                elif up == "CALCULATED":
                    calc_note.append("上漲空間由目標價 / 現價算出(原文未列)")
                elif up == "REVIEW":
                    bad += 1
                    det.append("上漲空間:原文 %s ≠ 重算 %s" % ((sm.get("metrics") or {}).get("upside", {}).get("value"), (sm.get("validation") or {}).get("calculated_upside")))
                # ③ 摘要數字回查(重算的上漲空間除外)
                allnum = _acc_numset("\n".join(_acc_page_text(pdf, list(range(1, 25))).values())) | _acc_numset("\n".join(_acc_pdfium_text(pdf, list(range(1, 25))).values()))
                calc_up = _acc_key(_acc_dec(str((sm.get("validation") or {}).get("calculated_upside") or "x")))
                ptxt = [re.sub(r"(?:19|20)\d{2}\s*年|計算 ?YoY ?-?[\d.]+%|計算上漲空間 ?-?[\d.]+%", " ", p.get("text") or "") for p in pts]   # 自算 YoY / 轉寫年份不回查(下面重算)
                sn = [m for t in ptxt for m in _ACC_NUM.findall(t) if _acc_dec(m) is not None and len(re.sub(r"\D", "", m)) >= 2]
                sn = [m for m in sn if not (up == "CALCULATED" and _acc_key(_acc_dec(m)) and calc_up.startswith(_acc_key(_acc_dec(m))[:4]))]
                shit = sum(1 for m in sn if _acc_key(_acc_dec(m)) in allnum)
                note += " · 摘要數字 %d/%d 在原文" % (shit, len(sn))
                if sn and shit < len(sn):
                    lamp = "YELLOW"
                if any(str(w).startswith("OCR_TEXT") for w in (sm.get("reader_warnings") or [])):   # v0221 影像 PDF
                    onum = _acc_numset("\n".join(x.get("text", "") for z in allz if str(z.get("engine", "")).startswith("rapidocr") for x in (z.get("records") or [])) + "\n" + _acc_ocr_cache_text(pdf))
                    ohit5 = sum(1 for m in sn if _acc_key(_acc_dec(m)) in (allnum | onum))
                    note = note.replace(" · 摘要數字 %d/%d 在原文" % (shit, len(sn)), " · 摘要數字 %d/%d 在 OCR 文字" % (ohit5, len(sn)))
                    if (not sn or ohit5 == len(sn)) and xn >= 3 and xo / xn >= 0.9 and lamp != "RED":   # v0225 OCR 算術驗證通過
                        note += " · OCR 來源(%s)" % xnote
                        lamp = "GREEN" if lamp in ("GREEN", "YELLOW") and (not sn or ohit5 == len(sn)) and "四點有證據 4/4" in note else lamp
                    else:
                        note += " · OCR 來源(影像 PDF · 數字只能對 OCR 文字 · 人工抽查)"
                        lamp = "YELLOW" if lamp == "GREEN" else lamp
                # ① 摘要自算 YoY 重算 · EPS 對擷取表格(同年度)
                eps = {int(x["year"]): x["value"] for x in sm.get("annual_eps") or []}
                for yy, pc in re.findall(r"((?:19|20)\d{2}) 年[^；]*?計算 ?YoY ?(-?[\d.]+)%", " ".join(p.get("text") or "" for p in pts)):
                    yy = int(yy)
                    if yy in eps and yy - 1 in eps and _acc_dec(eps[yy - 1]):
                        c = (_acc_dec(eps[yy]) / _acc_dec(eps[yy - 1]) - 1) * 100
                        if abs(c - _acc_dec(pc)) <= 0.06:
                            ok += 1
                        else:
                            bad += 1
                            det.append("摘要 YoY %d:%s ≠ 重算 %.1f%%" % (yy, pc, c))
                te = {}
                for t in _acc_tables(allz):
                    for y, vs in t.get("eps_all", {}).items():
                        te.setdefault(y, set()).update(vs)
                def _eps_ok(v, cands):
                    for c in cands:
                        dc, dv = _acc_dec(c), _acc_dec(v)
                        if dc is not None and dv is not None and abs(dc - dv) <= 0.5 * 10 ** -(len(c.split(".")[1]) if "." in c else 0) + 1e-9:
                            return True
                    return False
                em = [(y, v, "/".join(sorted(te[y]))) for y, v in eps.items() if y in te and _acc_dec(v) is not None and not _eps_ok(v, te[y])]
                eh = sum(1 for y in eps if y in te)
                if eh:
                    note += " · 摘要 EPS 對表 %d/%d" % (eh - len(em), eh)
                if em:
                    lamp = "RED"
                    bad += 1
                    det.append("摘要 EPS ≠ 擷取表格:" + "、".join("%d 摘要 %s / 表 %s" % x for x in em[:3]))
                    calc_note.append("摘要 EPS 對表不符 %d" % len(em))
                elif eh:
                    ok += 1
                    calc_note.append("摘要 EPS 對表 %d 年相符" % eh)
                key = next((k for k in _ACC_ORACLE if f.startswith(k)), None)
                if key:
                    o = _ACC_ORACLE[key]
                    got = {k: (sm.get("metrics") or {}).get(k) for k in ("target", "current", "old_target", "upside")}
                    eps = {int(x["year"]): x["value"] for x in sm.get("annual_eps") or []}
                    chk = [(_acc_dec((got[k] or {}).get("value", "")) if got[k] else None) == (_acc_dec(o[k]) if o[k] else None) for k in ("target", "current", "old_target", "upside")]
                    chk += [set(eps) == set(o["eps"])] + [y in eps and _acc_dec(eps[y]) == _acc_dec(v) for y, v in o["eps"].items()]
                    chk += [" ".join(title.split()) == o["title"]]
                    lamp = "GREEN" if all(chk) and lamp == "GREEN" else "RED"
                    note += " · 成功紀錄比對 %d/%d" % (sum(chk), len(chk))
                e["c5"] = (lamp, note)
                e["metrics"] = {k: ((sm.get("metrics") or {}).get(k) or {}).get("value") for k in ("target", "current", "old_target", "upside")}   # v0227 輸出冊用
                e["summary"] = {"title": title, "points": [{"topic": p.get("topic"), "status": p.get("status"), "text": (p.get("text") or "")[:240]} for p in pts]}
            except ValueError as exc:
                e["c5"] = ("GRAY", "首頁無文字層(影像 PDF)· OCR 後再摘要") if "NO_TEXT" in str(exc) else ("RED", "摘要失敗 ValueError")
            except Exception as exc:  # noqa: BLE001
                e["c5"] = ("RED", "摘要失敗 %s" % type(exc).__name__)
    ddet = [d for d in det if d.startswith("〔定義〕")]
    if ddet:
        calc_note.append("毛利率以營收 − 營業成本計 %d 年(毛利為調整後淨額)" % len(ddet))
    det = [d for d in det if not d.startswith("〔定義〕")]
    xdet = [d for d in det if d.startswith("〔原文")]
    if xdet:
        calc_note.append("原文跨表不一致 %d(擷取正確 · 報告本身兩表不同 · 請人工確認)" % len(xdet))
    if ok or bad or xdet:
        e["c1"] = ("RED" if bad else "YELLOW" if xdet else "GREEN", " · ".join(calc_note) + ((" · FAIL_CLOSED " + " | ".join([d for d in det if d not in xdet][:3])) if bad else "") + ((" · " + " | ".join(xdet[:2])) if xdet else ""))
    elif calc_note:
        e["c1"] = ("GRAY", " · ".join(calc_note))
    if frag:                                                           # v0220 擷取數字斷裂 → 紅(不當數字算)
        e["c1"] = ("RED", (e["c1"][1] + " · " if e["c1"][0] != "GRAY" and e["c1"][1] else "") + "擷取數字斷裂 %d 格(逗號開頭 · 引擎待接回):%s" % (len(frag), "、".join(frag[:4])))
    # ⑥ AUDIT:新輸入
    if lock_inputs is not None and f not in lock_inputs:
        core = [e["c1"][0], e["c2"][0], e["c3"][0], e["c5"][0]]
        e["c6"] = ("RED" if "RED" in core else "YELLOW" if "YELLOW" in core else "GREEN", "新輸入 · AUDIT 實測")
    elif lock_inputs is not None and lock_inputs.get(f) != sha:
        e["c6"] = ("YELLOW", "內容已換 · 重新驗收")
    if f in stock_files and pdf.exists():                                   # v0226 ⑦ 基本資料雙讀
        try:
            e["c7"], e["basic"] = _acc_basic(r, pdf)
        except Exception as exc:  # noqa: BLE001
            e["c7"] = ("YELLOW", "雙讀失敗 %s" % type(exc).__name__)
    return e


def acceptance(res: list, indir: Path, v2: Path, stock: list, lock_inputs: dict = None) -> tuple:
    """完成驗收:每份 ① 計算 ② 覆蓋 ③ 回查 ⑤ 摘要(個股)⑥ AUDIT(新輸入)。回 (清單, 退步, 文字行)。"""
    import logging
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    import datetime
    import hashlib
    L, out = [], []
    sd = v2 / "summary"
    sd.mkdir(parents=True, exist_ok=True)
    stock_files = {e["file"] for e in stock}
    eng, eng_name = _acc_eng062() if stock_files else (None, "無個股")
    prev = {}
    try:
        prev = {x["file"]: x for x in json.loads((v2 / "VRN2_Acceptance_latest.json").read_text(encoding="utf-8")).get("files", [])}
    except Exception:  # noqa: BLE001
        pass
    lanes = _acc_lanes()
    if lanes > 1 and len(res) >= 2 * lanes:
        out = _acc_parallel(res, indir, sd, stock_files, lock_inputs, lanes)
    else:
      for k, r in enumerate(res, 1):
        out.append(_acc_one(r, indir, sd, eng, eng_name, stock_files, lock_inputs))
        print("  [驗收] %d/%d · %s" % (k, len(res), r.get("file", "")[:40]), flush=True)
    rank = {"GREEN": 3, "GRAY": 2, "YELLOW": 1, "RED": 0}
    reg, corr = [], []
    for e in out:
        p = prev.get(e["file"])
        for k in ("c1", "c2", "c3", "c5"):
            if p and p.get(k, ["GRAY"])[0] == "GREEN" and rank[e[k][0]] < 2:
                pt = ((p.get("summary") or {}).get("title") or "")
                ppts = " ".join((x.get("text") or "") for x in ((p.get("summary") or {}).get("points") or []))
                if k == "c5" and re.search(_ACC_DISCL, ppts):
                    pt = "重點含免責句:" + re.search(_ACC_DISCL, ppts).group(0)[:20]
                if k == "c5" and (_ACC_BANNER.match(pt) or pt.startswith("重點含免責句")):                       # v0222 上輪的綠建立在券商橫幅假標題上
                    corr.append((e["file"], pt, e[k][0]))
                    continue
                reg.append((e["file"], k, e[k][0]))
    names = {"c1": "① 計算驗證", "c2": "② 本文/資訊區/財報頁覆蓋", "c3": "③ 數字回原文", "c5": "⑤ 一標題四重點", "c6": "⑥ AUDIT 新輸入", "c7": "⑦ 基本資料雙讀"}
    cnt = {k: Counter(e.get(k, ("GRAY", ""))[0] for e in out) for k in names}
    for f_, pt_, l_ in corr:
        print("  [計] 驗收鎖校正 · %s · ⑤ 上輪綠%s(假綠)· 不算退步 · 以本輪 %s 為新基準" % (f_[:40], ("的" + pt_[:30]) if pt_.startswith("重點含") else ("的標題是券商橫幅「%s」" % pt_[:30]), l_), flush=True)
    (v2 / "VRN2_Acceptance_latest.json").write_text(json.dumps({"at": datetime.datetime.now().isoformat(timespec="seconds"), "manager": TAG, "summarizer": eng_name,
                                                               "counts": {k: dict(v) for k, v in cnt.items()}, "regress": reg, "files": out}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    import csv as _csv
    with (v2 / "VRN2_Acceptance_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = _csv.writer(fh)
        w.writerow(["FILE"] + [names[k] + x for k in names for x in ("_燈", "_說明")])
        for e in out:
            w.writerow([e["file"]] + [v for k in names for v in e[k]])
    L.append("[計] VRN-2 完成驗收 · %d 份 · %s · 摘要器 %s · 驗收退步 %d" % (len(out), " · ".join("%s 綠%d黃%d紅%d灰%d" % (names[k], v.get("GREEN", 0), v.get("YELLOW", 0), v.get("RED", 0), v.get("GRAY", 0)) for k, v in cnt.items()), eng_name, len(reg)))
    for f, k, l in reg[:20]:
        L.append("[RED] 驗收退步 · %s · %s(上輪綠 → %s)" % (f[:40], names[k], l))
    for e in [e for e in out if any(e[k][0] == "RED" for k in names)][:25]:
        L.append("[計] 驗收 RED · %s · %s" % (e["file"][:36], " | ".join("%s %s" % (names[k][:2], e[k][1][:90]) for k in names if e[k][0] == "RED")))
    return out, reg, L, cnt


def _accept_html(out: list, cnt: dict) -> str:
    names = [("c1", "① 計算驗證"), ("c2", "② 覆蓋"), ("c3", "③ 回原文"), ("c5", "⑤ 一標題四重點"), ("c6", "⑥ AUDIT"), ("c7", "⑦ 基本資料雙讀")]
    head = " · ".join("%s 綠%d 黃%d 紅%d 灰%d" % (n, cnt[k].get("GREEN", 0), cnt[k].get("YELLOW", 0), cnt[k].get("RED", 0), cnt[k].get("GRAY", 0)) for k, n in names)
    trs = []
    for e in out:
        tds = "".join("<td%s><i style='background:%s'></i>%s</td>" % (" class='bl'" if e.get(k, ("GRAY", ""))[0] == "RED" else "", _V2C.get(e.get(k, ("GRAY", ""))[0], "#9ca3af"), html.escape(e.get(k, ("GRAY", "—"))[1])) for k, _ in names)
        sm = e.get("summary")
        st = ("<details><summary>%s</summary><ol>%s</ol></details>" % (html.escape(sm["title"] or "(缺標題)"), "".join("<li>[%s · %s] %s</li>" % (html.escape(str(p["topic"])), html.escape(str(p["status"])), html.escape(p["text"])) for p in sm["points"]))) if sm else ""
        trs.append("<tr><td>%s</td>%s<td>%s</td></tr>" % (html.escape(e["file"]), tds, st))
    return ("<h2 style='margin-top:14px'>完成驗收</h2><div style='margin:4px 0'>%s</div><table><tr><th>檔案</th>%s<th>一標題四重點</th></tr>%s</table>"
            % (html.escape(head), "".join("<th>%s</th>" % n for _, n in names), "".join(trs)))


def completion(regress: int, ok: int, n: int, success: bool, acnt: dict, st: list, idem: tuple = None, outbook: tuple = None, funnel: tuple = None, regress_names: str = "") -> dict:
    """v0218 VRN-2 完成判定:依完成定義逐條判燈;紅 = 未完成 · 黃 = 完成但列提醒 · 影像 PDF 待 OCR 列已知例外。"""
    import datetime
    items = []
    def add(name, lamp, detail):
        items.append({"name": name, "lamp": lamp, "detail": detail})
    add("實測退步", "GREEN" if regress == 0 else "RED", "退步 %d%s" % (regress, (" · " + regress_names[:200]) if regress_names else ""))   # v0229 寫出是哪一份
    add("交互驗證(JSON ↔ CSV ↔ 燈號)", "GREEN" if n and ok == n else "RED", "%d/%d 一致" % (ok, n))
    add("鎖定 + 備份", "GREEN" if success else "RED", "成功鎖定" if success else "未鎖定")
    if idem:
        add("冪等(同輸入重跑輸出一致)", idem[0], idem[1])                 # v0226 學 VRN-1 G08
    if outbook:
        add("輸出冊(基本資料 / 年度數據 / 一標題四重點)", outbook[0], outbook[1])   # v0227
    if funnel:
        add("調節輪(漏斗 · 輕的先用)", funnel[0], funnel[1])                 # v0228
    names = {"c1": "① 結果計算驗證", "c2": "② 本文 / 資訊區 / 財報頁覆蓋", "c3": "③ 數字回原文搜尋", "c5": "⑤ 一標題四重點", "c6": "⑥ AUDIT 新輸入", "c7": "⑦ 基本資料雙讀"}
    for k, nm in names.items():
        c = (acnt or {}).get(k, {})
        if not acnt:
            add(nm, "GRAY", "驗收未執行")
        elif c.get("RED"):
            add(nm, "RED", "紅 %d · 黃 %d · 綠 %d" % (c.get("RED", 0), c.get("YELLOW", 0), c.get("GREEN", 0)))
        elif c.get("YELLOW"):
            add(nm, "YELLOW", "黃 %d(提醒 · 不擋完成)· 綠 %d" % (c.get("YELLOW", 0), c.get("GREEN", 0)))
        elif not c.get("GREEN"):
            add(nm, "GRAY", "本輪無適用項目" + ("(沒有新輸入)" if k == "c6" else ""))
        else:
            add(nm, "GREEN", "綠 %d" % c.get("GREEN", 0))
    exc_files, red_files = [], []
    for e in st or []:
        parts = e.get("parts") or {}
        reds = [(k, v) for k, v in parts.items() if v and v[0] == "RED"]
        if not reds:
            continue
        if all("無文字層" in (v[1] or "") for _, v in reds):
            exc_files.append(e.get("file", "")[:40])
        else:
            red_files.append(e.get("file", "")[:40])
    if red_files:
        add("個股四項", "RED", "紅 %d 份:%s" % (len(red_files), "、".join(red_files[:5])))
    elif exc_files:
        add("個股四項", "YELLOW", "已知例外 %d 份(影像 PDF · 待 OCR):%s" % (len(exc_files), "、".join(exc_files)))
    else:
        add("個股四項", "GREEN", "%d 份無紅燈" % len(st or []))
    red = sum(1 for it in items if it["lamp"] == "RED")
    yel = sum(1 for it in items if it["lamp"] == "YELLOW")
    return {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "manager": "VRN-2 SystemManager " + TAG, "verdict": "未完成" if red else "完成",
            "red": red, "yellow": yel, "exceptions": exc_files, "items": items}


def _completion_html(comp: dict) -> str:
    col = {"GREEN": "#16a34a", "YELLOW": "#eab308", "RED": "#dc2626", "GRAY": "#9ca3af"}
    big = "#16a34a" if comp["verdict"] == "完成" else "#dc2626"
    rows = "".join("<tr><td%s><i style='background:%s'></i>%s</td><td>%s</td><td>%s</td></tr>" % (
        " class='bl'" if it["lamp"] == "RED" else "", col.get(it["lamp"], "#9ca3af"), it["lamp"], html.escape(it["name"]), html.escape(it["detail"])) for it in comp["items"])
    return ("<div style='border:2px solid %s;border-radius:6px;padding:6px 10px;margin:0 0 10px'><b style='font-size:15px;color:%s'>VRN-2 完成判定 · %s</b>"
            " <span style='color:#555'>紅 %d · 黃 %d · %s · %s</span><table style='margin-top:4px'><tr><th>燈</th><th>完成條件</th><th>本輪</th></tr>%s</table></div>"
            % (big, big, comp["verdict"], comp["red"], comp["yellow"], html.escape(comp["manager"]), comp["ts"], rows))


def stock_round(res: list, indir: Path, v2: Path, rnd, reg=None) -> tuple:
    """個股四項:評估 → 逐項鎖定(綠才鎖 · 只增不減)→ 鎖過的項不再綠 = 退步(紅)→ 輪次帳本。回傳 (結果清單, 非個股清單, 退步清單, 鎖)。"""
    import datetime
    ev = [stock_eval(r, _npages(indir / r.get("file", "")) if (indir / r.get("file", "")).exists() else 0) for r in res]
    st, ns = [e for e in ev if e["stock"]], [e for e in ev if not e["stock"]]
    lp = Path(reg or HERE / "registry") / "VRN2_Stock_Lock_latest.json"
    lock = json.loads(lp.read_text(encoding="utf-8")) if lp.exists() else {"files": {}}
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    regress, newly = [], 0
    for e in st:
        lf = lock["files"].setdefault(e["file"], {})
        for k, (lamp, _) in e["parts"].items():
            if lamp == "GREEN" and k not in lf:
                lf[k] = {"round": rnd, "at": now}
                newly += 1
            elif k in lf and lamp != "GREEN":
                regress.append((e["file"], k, lamp))
                e["parts"][k] = ("RED", "退步(第 %s 輪已鎖)· " % lf[k]["round"] + e["parts"][k][1])
                e["lamp"] = "RED"
    lock.update(round=rnd, at=now)
    lp.parent.mkdir(parents=True, exist_ok=True)
    lp.write_text(json.dumps(lock, ensure_ascii=False, indent=1), encoding="utf-8")
    pc = {k: Counter(e["parts"][k][0] for e in st) for k in ("檔名", "首頁", "年度財報", "評價資訊")}
    with (v2 / "VRN2_Stock_Rounds.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"round": rnd, "at": now, "stock": len(st), "non_stock": len(ns), "parts": {k: dict(v) for k, v in pc.items()}, "file_green": sum(1 for e in st if e["lamp"] == "GREEN"),
                             "locked_parts": sum(len(v) for v in lock["files"].values()), "newly": newly, "regress": len(regress)}, ensure_ascii=False) + "\n")
    return st, ns, regress, lock, pc, newly


def _stock_html(st, ns, regress, pc, lock) -> str:
    lampi = lambda l: "<i style='background:%s'%s></i>" % (_V2C.get(l, "#9ca3af"), " class='bl'" if l == "RED" else "")  # noqa: E731
    keys = ("檔名", "首頁", "年度財報", "評價資訊")
    rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td>%s</tr>" % (lampi(e["lamp"]), html.escape(e["file"]), html.escape(e["ticker"]),
                   "".join("<td>%s%s</td>" % (lampi(e["parts"][k][0]), html.escape(e["parts"][k][1])) for k in keys)) for e in sorted(st, key=lambda e: {"RED": 0, "YELLOW": 1, "GREEN": 2}[e["lamp"]]))
    summ = " · ".join("%s 綠 %d / 黃 %d / 紅 %d / 灰 %d" % (k, pc[k].get("GREEN", 0), pc[k].get("YELLOW", 0), pc[k].get("RED", 0), pc[k].get("GRAY", 0)) for k in keys)
    return ("<h3>%s個股報告四項驗收 · %d 份(全綠 %d)· 逐項鎖定 %d · 退步 %d</h3><div class='sum'><span>%s</span></div>"
            "<table><tr><th>燈</th><th>檔案</th><th>代號</th><th>①檔名</th><th>②首頁</th><th>③年度財報頁</th><th>④重要財報及評價</th></tr>%s</table>"
            "<p style='color:#6b7280'>非個股(不適用 · 灰)%d 份:%s</p>" % (lampi("RED" if regress else ("GREEN" if all(e["lamp"] == "GREEN" for e in st) else "YELLOW")), len(st), sum(1 for e in st if e["lamp"] == "GREEN"),
                sum(len(v) for v in lock["files"].values()), len(regress), html.escape(summ), rows, len(ns), html.escape(" · ".join(e["file"][:28] for e in ns))))


_OUT_NOTNAME = {"法說", "封裝", "研究中心", "研究部", "伺服器", "半導體", "電子", "金融", "傳產", "航運"}
_OUT_RATING = re.compile(r"(?i)\b(Overweight|Underweight|Equal-?weight|Outperform|Underperform|Market Perform|Neutral|Buy|Sell|Hold|Reduce|Accumulate)\b|(強力買進|逢低買進|增加持股|降低持股|區間操作|逢高賣出|買進|持有|中立|賣出|未評等)")


def _out_p1(r: dict) -> str:
    zs = [z for pg in r.get("pages") or [] if pg.get("pno") == 1 for z in pg.get("zones") or []]
    return "\n".join([x.get("text", "") for z in zs for x in (z.get("records") or []) if isinstance(x, dict)] + [" ".join(c for c in row if c) for z in zs for row in (z.get("rows") or [])])


def _out_rating(r: dict) -> tuple:
    zs = [z for pg in r.get("pages") or [] for z in pg.get("zones") or []]
    for src, txt in (("首頁評等區", " ".join(x.get("text", "") for z in zs if z.get("minor") == "RT" for x in (z.get("records") or []))), ("首頁", _out_p1(r)[:2500]),
                     ("資訊框", " ".join(x.get("text", "") for z in zs if "救回" in (z.get("engine") or "") for x in (z.get("records") or [])))):
        m = _OUT_RATING.search(txt or "")
        if m:
            return (m.group(1) or m.group(2)), src
    return "", ""


def _out_books(res: list, acc: list, st: list, v2: Path) -> tuple:
    """v0227 三本輸出冊(範圍:個股報告):基本資料 BASIC INFO · 年度財報數據 FINANCIAL DATA · 一標題四重點 SUMMARY → JSON + CSV(+ Parquet 若有 pyarrow)。"""
    import csv
    byf = {r.get("file"): r for r in res}
    ac = {e.get("file"): e for e in acc or []}
    basic, fin, summ, gaps = [], [], [], []
    for s_ in st or []:
        f = s_.get("file")
        r, e = byf.get(f) or {}, ac.get(f) or {}
        if not s_.get("stock", True) or not r:
            continue
        tk = s_.get("ticker", "")
        p1 = _out_p1(r)
        yf = re.search(r"\b(%s)\.(TWO|TW)\b" % re.escape(tk), p1) if tk else None
        bb = re.search(r"\b(%s)\s+TT\b" % re.escape(tk), p1) if tk else None
        en = re.search(r"([A-Z][A-Za-z&.,'\- ]{2,48}?)\s*\(\s*%s\.TWO?" % re.escape(tk), p1) if tk else None
        zh = re.search(r"(?<!\d)%s[\s_\-]*([\u4e00-\u9fff][\u4e00-\u9fff]{0,8}(?:-KY)?)" % re.escape(tk), f) if tk else None
        zh = zh or (re.search(r"([\u4e00-\u9fff]{2,8}(?:-KY)?)[\s_\(（]*%s" % re.escape(tk), f) if tk else None)
        rt, rts = _out_rating(r)
        bi = e.get("basic") or {}
        mt = e.get("metrics") or {}
        names_ = []
        for em_ in (bi.get("email_a") or bi.get("email_b") or []):           # 分析師:Email 前面的中文姓名優先(呂旻旂/紡織…)· 找不到才用帳號
            k_ = p1.lower().find(em_.split("@")[0][-6:])
            pre = p1[max(0, k_ - 90):k_] if k_ >= 0 else ""
            cj = re.findall(r"([\u4e00-\u9fff]{2,4})(?=\s*[/／])", pre) or re.findall(r"([\u4e00-\u9fff]{2,4})(?=\s*[,，]\s*(?:CPA|CFA|FRM|PhD|MBA|CMA))", pre) or re.findall(r"([\u4e00-\u9fff]{2,4})(?=\s*分析師|\s*研究員|\s*\+?886|\s*\n)", pre)   # 國泰「呂旻旂/紡織…」斜線前是姓名
            cj = [x for x in cj if x not in _OUT_NOTNAME and not re.search(r"研究|中心|產業|分析|投資|部門|團隊|報告|說明|設計|設備|封裝|法說|服務", x)]   # v0229 非姓名
            names_.append(cj[-1] if cj else " ".join(w.capitalize() for w in re.split(r"[._]", em_.split("@")[0]) if w.isalpha()))
        up_, ups_ = mt.get("upside") or "", "原文"
        try:
            if not up_ and mt.get("target") and mt.get("current"):
                up_ = "%.1f" % ((float(str(mt["target"]).replace(",", "")) / float(str(mt["current"]).replace(",", "")) - 1) * 100)
                ups_ = "計算(目標價 ÷ 現價 − 1)"
        except (ValueError, ZeroDivisionError):
            pass
        row = {"REPORT_DATE": s_.get("date", ""), "FILENAME": f, "TICKER": tk,
               "YFINANCE_TICKER": ("%s.%s" % (yf.group(1), yf.group(2))) if yf else "", "BLOOMBERG_TICKER": ("%s TT" % tk) if tk else "",
               "NAME": zh.group(1) if zh else "", "ENGLISH_NAME": en.group(1).strip(" ,:-") if en else "", "BROKER": s_.get("broker", ""),
               "ANALYST": "、".join(dict.fromkeys(names_)) or "、".join(bi.get("analysts") or []), "EMAIL": "、".join(bi.get("email_a") or bi.get("email_b") or []),
               "TEL": "", "TITLE": (e.get("summary") or {}).get("title") or "", "RATING": rt,
               "TARGET_PRICE": mt.get("target") or "", "CURRENT_PRICE_REPORT": mt.get("current") or "", "UPSIDE_PCT": up_,
               "ADJ_CLOSE": "", "ADJ_CLOSE_BEFORE_REPORT": "",
               "_STATUS": {"BLOOMBERG_TICKER": "VERIFIED" if bb else "推算(代號 + TT)", "YFINANCE_TICKER": "VERIFIED" if yf else "待 VDF 上市櫃清單(.TW / .TWO)",
                           "EMAIL": (bi.get("email") or ["—"])[0], "TEL": (bi.get("tel") or ["—"])[0], "BROKER": (bi.get("broker") or ["—"])[0],
                           "RATING": rts or "首頁未印", "UPSIDE_PCT": ups_ if up_ else "缺目標價或現價", "NAME": "檔名" if zh else "待 VDF 上市櫃清單(不衝突即可取用)",
                           "ADJ_CLOSE": "待 VDF 股價庫(不衝突即可取用)"}}
        tel = bi.get("tel") or ["", ""]
        row["TEL"] = "" if tel[0] in ("MISSING", "—", "") else tel[1]
        basic.append(row)
        nrow = 0
        for pg in r.get("pages") or []:
            for z in pg.get("zones") or []:
                eng = z.get("engine") or ""
                rows = z.get("rows") or []
                if z.get("minor") != "TB" or not rows:
                    continue                                              # v0229 不看引擎標籤 · 改用表頭判斷(與個股四項同口徑)
                hdr = next(((i, rw) for i, rw in enumerate(rows[:4]) if sum(bool(_SK_ANNUAL.match((c or "").strip())) for c in rw[1:]) >= 2), None)
                if not hdr:
                    continue
                hi, hrow = hdr
                for rw in rows[hi + 1:]:
                    item = (rw[0] if rw else "") or ""
                    if not re.search(r"[A-Za-z\u4e00-\u9fff]{2,}", item) or re.fullmatch(r"[\d\s,.%()\-+]+", item.strip()) or re.search(r"\d{4}\.TWO?\(", item):
                        continue                                          # v0229 圖表座標 / 數字當科目 / 股價圖軸不收
                    for j, c in enumerate(rw[1:], 1):
                        per = (hrow[j] if j < len(hrow) else "") or ""
                        if item.strip() and (c or "").strip() and _SK_ANNUAL.match(per.strip()):
                            fin.append({"REPORT_DATE": row["REPORT_DATE"], "FILENAME": f, "TICKER": tk, "BROKER": row["BROKER"], "PAGE": pg.get("pno"), "TABLE": z.get("id"),
                                        "ITEM": item.strip(), "PERIOD": per.strip(), "VALUE": c.strip()})
                            nrow += 1
        sm = e.get("summary") or {}
        pts = sm.get("points") or []
        summ.append({"REPORT_DATE": row["REPORT_DATE"], "FILENAME": f, "TICKER": tk, "BROKER": row["BROKER"], "TITLE": sm.get("title") or "",
                     **{"POINT_%d" % (i + 1): ((pts[i].get("text") or "") if i < len(pts) else "") for i in range(4)},
                     "POINTS_OK": sum(1 for p in pts if p.get("text"))})
        miss = [k for k in ("REPORT_DATE", "TICKER", "BROKER", "TITLE") if not row[k]]
        quick = (s_.get("parts") or {}).get("年度財報", ("", ""))[0] == "GRAY"
        if not nrow and not quick:
            miss.append("年度數據")
        if summ[-1]["POINTS_OK"] < 4:
            miss.append("四重點 %d/4" % summ[-1]["POINTS_OK"])
        if miss:
            gaps.append("%s:%s" % (f[:28], "、".join(miss)))
    od = v2 / "output"
    od.mkdir(parents=True, exist_ok=True)
    made = []
    for name, rows_, cols in (("BasicInfo", basic, None), ("FinancialData", fin, None), ("Summary", summ, None)):
        (od / ("VRN2_%s_latest.json" % name)).write_text(json.dumps(rows_, ensure_ascii=False, indent=1), encoding="utf-8")
        flat = [{k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in x.items()} for x in rows_]
        keys = list(dict.fromkeys(k for x in flat for k in x))
        with (od / ("VRN2_%s_latest.csv" % name)).open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys or ["EMPTY"])
            w.writeheader()
            w.writerows(flat)
        try:
            import pandas as pd  # noqa: WPS433
            pd.DataFrame(flat).to_parquet(od / ("VRN2_%s_latest.parquet" % name), index=False)
            made.append("%s(%d 列 · JSON / CSV / Parquet)" % (name, len(rows_)))
        except Exception:  # noqa: BLE001
            made.append("%s(%d 列 · JSON / CSV)" % (name, len(rows_)))
    return basic, fin, summ, gaps, made


def _out_html(basic: list, fin: list, summ: list) -> str:
    cols = ["REPORT_DATE", "TICKER", "NAME", "ENGLISH_NAME", "BROKER", "ANALYST", "EMAIL", "TEL", "RATING", "TARGET_PRICE", "CURRENT_PRICE_REPORT", "UPSIDE_PCT", "YFINANCE_TICKER", "BLOOMBERG_TICKER", "TITLE"]
    bt = "".join("<tr><td>%s</td>%s</tr>" % (html.escape(b["FILENAME"][:40]), "".join("<td>%s</td>" % html.escape(str(b.get(c, ""))[:80]) for c in cols)) for b in basic)
    from collections import Counter
    nf = Counter(x["FILENAME"] for x in fin)
    ft = "".join("<tr><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>" % (html.escape(b["FILENAME"][:40]), html.escape(b["TICKER"]), nf.get(b["FILENAME"], 0),
                 html.escape(" · ".join(sorted({x["ITEM"][:14] for x in fin if x["FILENAME"] == b["FILENAME"]})[:8]))) for b in basic)
    stb = "".join("<tr><td>%s</td><td><b>%s</b><ol>%s</ol></td></tr>" % (html.escape(s["FILENAME"][:40]), html.escape(s["TITLE"] or "(缺標題)"),
                  "".join("<li>%s</li>" % html.escape(s["POINT_%d" % i][:220] or "—") for i in range(1, 5))) for s in summ)
    return ("<h2 style='margin-top:14px'>基本資料(BASIC INFO · %d 份個股)</h2><div style='overflow-x:auto'><table><tr><th>檔案</th>%s</tr>%s</table></div>"
            "<h2 style='margin-top:14px'>年度財報數據(FINANCIAL DATA · %d 筆)</h2><table><tr><th>檔案</th><th>代號</th><th>數據筆數</th><th>項目</th></tr>%s</table>"
            "<h2 style='margin-top:14px'>一標題四重點(SUMMARY)</h2><table><tr><th>檔案</th><th>標題 / 四重點</th></tr>%s</table>"
            % (len(basic), "".join("<th>%s</th>" % c for c in cols), bt, len(fin), ft, stb))


def vrn2scope(args: list) -> tuple:
    """v0227 VRN-2 獨立設定冊 + 範圍聚焦:VRN2_SSOT(來源夾 · 範圍 = 個股報告 · 交付項)· 來源夾的 PDF 扣掉上輪判定非個股 / 檔名明確非個股 → 同步到 VIA_Reports\\vrn2\\scope_in · 設定冊 input_dir 指向它(只增不減:出新版)。"""
    import shutil
    L = []
    ssd = HERE / "SSOT"
    ssd.mkdir(parents=True, exist_ok=True)
    v2 = Path(_resolve("_rep")()).parent / "vrn2"
    scope_dir = v2 / "scope_in"
    cur_in = Path(_resolve("input_dir")())
    books = sorted(ssd.glob("VRN2_SSOT_v[0-9][0-9][0-9][0-9].json"), key=lambda p: int(re.search(r"_v(\d{4})", p.name).group(1)))
    ss = json.loads(books[-1].read_text(encoding="utf-8")) if books else {}
    src = Path(ss.get("source_dir") or (str(cur_in) if cur_in.resolve() != scope_dir.resolve() else r"C:\測試樣本報告"))
    new = dict(ss, system="VRN-2", owner="VRN-2 SystemManager", independent=True, source_dir=str(src), scope="stock_only", scope_dir=str(scope_dir),
               deliverables=["FILENAME", "首頁(本文 / 資訊區)", "年度財報頁(年度財報及數據分解)", "100% 還原", "一標題四重點", "輸出驗證", "HTML U/I"],
               borrow_rule="參數可向其他系統取用(VDF 上市櫃清單 / 股價庫等)· 不衝突即可 · 不照抄程式",
               funnel=dict(_FUNNEL_DEFAULT, **(ss.get("funnel") or {})))
    if new != ss:
        nv = (int(re.search(r"_v(\d{4})", books[-1].name).group(1)) + 1) if books else 100
        (ssd / ("VRN2_SSOT_v%04d.json" % nv)).write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
        L.append("[計] VRN-2 獨立設定冊 → SSOT/VRN2_SSOT_v%04d.json(來源 %s · 範圍 個股報告)" % (nv, src))
    prev = {}
    try:
        prev = json.loads((v2 / "VRN2_Scope_latest.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    nons = set(prev.get("non_stock") or [])
    if not src.is_dir():
        return 1, L + ["[RED] VRN-2 範圍 · 來源夾不在 %s" % src]
    allf = sorted([p for p in src.rglob("*") if p.is_file()], key=lambda p: p.name)
    pdfs = [p for p in allf if p.suffix.lower() == ".pdf"]
    keep = [p for p in pdfs if p.name not in nons and not _SK_EXCL.search(p.name)]
    scope_dir.mkdir(parents=True, exist_ok=True)
    names = {p.name for p in keep}
    cp = 0
    for p in keep:
        d = scope_dir / p.name
        if not d.exists() or d.stat().st_size != p.stat().st_size or int(d.stat().st_mtime) != int(p.stat().st_mtime):
            shutil.copy2(str(p), str(d))
            cp += 1
    rm = 0
    for d in scope_dir.iterdir():
        if d.is_file() and d.name not in names:
            d.unlink()
            rm += 1
    cfgs = sorted(ssd.glob("VRN_Config_v[0-9][0-9][0-9][0-9].json"), key=lambda p: int(re.search(r"_v(\d{4})", p.name).group(1)))
    cfg = json.loads(cfgs[-1].read_text(encoding="utf-8")) if cfgs else {}
    if Path(cfg.get("input_dir") or "").resolve() != scope_dir.resolve() if cfg.get("input_dir") else True:
        nv = (int(re.search(r"_v(\d{4})", cfgs[-1].name).group(1)) + 1) if cfgs else 1000
        (ssd / ("VRN_Config_v%04d.json" % nv)).write_text(json.dumps(dict(cfg, input_dir=str(scope_dir), vrn2_scope="stock_only", vrn2_source_dir=str(src)), ensure_ascii=False, indent=1), encoding="utf-8")
        L.append("[計] VRN-2 設定冊 → SSOT/VRN_Config_v%04d.json(input_dir = 個股範圍夾)" % nv)
    L.append("[計] VRN-2 範圍(只擷取個股報告)· 來源 %s · 檔 %d(PDF %d · 非 PDF %d 不在範圍)· 個股範圍 %d · 排除非個股 %d(上輪判定 %d · 檔名 %d)· 同步 新增 / 更新 %d · 移除 %d" % (
        src, len(allf), len(pdfs), len(allf) - len(pdfs), len(keep), len(pdfs) - len(keep), len([p for p in pdfs if p.name in nons]),
        len([p for p in pdfs if p.name not in nons and _SK_EXCL.search(p.name)]), cp, rm))
    return 0, L


_FUNNEL = [("T0", "文字層(pdfplumber)"), ("T1", "換引擎(pypdfium2)"), ("T2", "OCR 標準(200 DPI)"), ("T3", "OCR 高畫質(325 DPI + 前處理)"), ("T4", "待人工(OCR 佇列)")]
_FUNNEL_DEFAULT = {"order": [n for _, n in _FUNNEL], "ocr_ladder": "200,325p", "ocr_min_conf": 0.85, "ocr_min_chars": 40, "max_tier": "T3",
                   "rule": "輕的先用 · 不夠才升一層 · 不必全部都用(漏斗)"}


def _funnel_tier(r: dict) -> str:
    """v0228 調節輪:依實際用到的工具判定該份停在漏斗哪一層。"""
    zs = [z for pg in r.get("pages") or [] for z in pg.get("zones") or []]
    engs = " ".join(str(z.get("engine") or "") for z in zs)
    if any(z.get("needs_ocr") for z in zs) or any("首頁無文字層" in x for x in (r.get("reasons") or [])):
        return "T4"
    if "rapidocr" in engs:
        tried = (r.get("ocr") or {}).get("tried") if isinstance(r.get("ocr"), dict) else None
        return "T3" if ("325" in engs or (tried and len(tried) > 1)) else "T2"
    if "pypdfium2" in engs:
        return "T1"
    return "T0"


def _funnel(res: list, ssot: dict) -> tuple:
    from collections import Counter
    tiers = {r.get("file", ""): _funnel_tier(r) for r in res}
    c = Counter(tiers.values())
    fp = dict(_FUNNEL_DEFAULT, **((ssot or {}).get("funnel") or {}))
    line = "[計] 調節輪(漏斗 · 輕的先用 · 不夠才升層)· %s · 門檻 信心 %.2f / %d 字 · 階梯 %s · 上限 %s(VRN2_SSOT)" % (
        " · ".join("%s %s %d" % (k, n.split("(")[0], c.get(k, 0)) for k, n in _FUNNEL), float(fp["ocr_min_conf"]), int(fp["ocr_min_chars"]), fp["ocr_ladder"].replace(",", "→"), fp["max_tier"])
    lamp = ("GREEN" if not c.get("T4") else "YELLOW", "%s%s" % (" · ".join("%s %d" % (k, c.get(k, 0)) for k, _ in _FUNNEL), (" · 待人工:" + "、".join(f[:24] for f, t in tiers.items() if t == "T4")) if c.get("T4") else ""))
    return tiers, c, line, lamp


def _funnel_html(tiers: dict, c, ssot: dict) -> str:
    fp = dict(_FUNNEL_DEFAULT, **((ssot or {}).get("funnel") or {}))
    tot = max(1, sum(c.values()))
    bars = "".join("<tr><td><b>%s</b> %s</td><td style='width:55%%'><div style='background:%s;height:12px;width:%.1f%%;border-radius:3px'></div></td><td>%d 份</td><td>%s</td></tr>" % (
        k, html.escape(n), ("#16a34a", "#22c55e", "#eab308", "#f59e0b", "#dc2626")[i], 100.0 * c.get(k, 0) / tot, c.get(k, 0),
        html.escape("、".join(f[:22] for f, t in tiers.items() if t == k)[:300]) if k != "T0" else "") for i, (k, n) in enumerate(_FUNNEL))
    return ("<h2 style='margin-top:14px'>調節輪(漏斗:輕的先用 · 不夠才升層 · 不必全部都用)</h2><p>門檻:OCR 信心 ≥ %.2f 且 ≥ %d 字才停 · 階梯 %s · 上限 %s · 設定在 VRN2_SSOT(MAIN 帶入引擎)</p>"
            "<table><tr><th>層</th><th>比例</th><th>份數</th><th>停在此層的檔(T0 省略)</th></tr>%s</table>" % (float(fp["ocr_min_conf"]), int(fp["ocr_min_chars"]), html.escape(fp["ocr_ladder"].replace(",", " → ")), fp["max_tier"], bars))


def _opbar_html(v2: Path, root_hint: str = "") -> str:
    """v0228 U/I 頂端操作列(使用者直接在上方操作):via://VRN2/... 動作 + 檔案連結 + 複製執行指令(via:// 未註冊時的後援)。"""
    out = (v2 / "output").as_uri() if (v2 / "output").exists() else ""
    pv = (v2 / "p1view" / "P1VIEW_latest.html").as_uri() if (v2 / "p1view" / "P1VIEW_latest.html").exists() else ""
    sc = (v2 / "scope_in").as_uri() if (v2 / "scope_in").exists() else ""
    cmd = "& { $A = \"$env:USERPROFILE\\Downloads\\ActivateVRN-2.py\"; $py = (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1).Source; & $py $A }"
    btn = "display:inline-block;margin:0 6px 4px 0;padding:4px 10px;border:1px solid #d1d5db;border-radius:6px;background:#fff;color:#111;text-decoration:none;cursor:pointer;font:12px system-ui,'Microsoft JhengHei'"
    items = ["<a style=\"%s;background:#16a34a;color:#fff;border-color:#16a34a\" href='via://VRN2/run' title='重跑 VRN-2(需 via:// 協定;未註冊時請用「複製執行指令」)'>▶ 重跑 VRN-2</a>" % btn,
             "<a style=\"%s\" href='via://VRN2/accept' title='只重跑完成驗收'>↻ 重跑驗收</a>" % btn]
    for lab, u in (("📂 輸出冊", out), ("🔍 切割檢視", pv), ("📁 個股範圍夾", sc)):
        if u:
            items.append("<a style=\"%s\" href='%s' target='_blank'>%s</a>" % (btn, u, lab))
    items.append("<button style=\"%s\" onclick=\"navigator.clipboard.writeText(this.dataset.c).then(()=>{this.textContent='✓ 已複製'})\" data-c=\"%s\">⧉ 複製執行指令</button>" % (btn, html.escape(cmd, quote=True)))
    return "<div style='position:sticky;top:0;z-index:9;background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:6px 4px 2px;margin:-10px -10px 8px'>%s</div>" % "".join(items)


def vrn2(args: list, rep=None, indir=None, open_ui: bool = True, reg=None) -> tuple:
    """VRN-2 獨立子系統(第一頁 + 財報頁 切割 / 擷取 / 修復):--run 先跑 p1loop;成功(退步 0)→ 鎖版本 + 時間 · 備份成功狀態 · 交互驗證(JSON ↔ CSV ↔ 燈號)· HTML U/I 自動跳出。"""
    import csv
    import datetime
    import hashlib
    import shutil
    L = []
    if "--run" in args:
        rc0, l0 = _resolve("p1loop")("")
        L += l0
        if rc0 not in (0, 1):
            return rc0, L
    rep = Path(rep or _resolve("_rep")())
    pv, v2 = rep / "p1view", rep.parent / "vrn2"
    v2.mkdir(parents=True, exist_ok=True)
    try:
        res = json.loads((pv / "P1VIEW_latest.json").read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return 1, L + ["[RED] VRN-2 · 讀不到 P1VIEW_latest.json · %s" % type(exc).__name__]
    rows = [l for l in (pv / "VRN_P1View_Rounds.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()] if (pv / "VRN_P1View_Rounds.jsonl").exists() else []
    entry = json.loads(rows[-1]) if rows else {}
    csvz, csvc, csvt = {}, {}, {}
    cp = pv / "P1VIEW_records_latest.csv"
    if cp.exists():
        with cp.open(encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                csvz.setdefault(r["FILE"], set()).add(r["ZONE"])
                if r.get("REC_KIND") == "格":
                    csvc[r["FILE"]] = csvc.get(r["FILE"], 0) + 1
                else:
                    csvt[r["FILE"]] = csvt.get(r["FILE"], 0) + 1
    indir = Path(indir or (_resolve("input_dir") or (lambda: Path(r"C:\測試樣本報告")))())
    files, ok = [], 0
    for r in res:
        f = r.get("file", "")
        zs = [z for pg in r.get("pages") or [] for z in pg.get("zones") or []]
        nonempty = lambda z: [c for row in (z.get("rows") or []) for c in row if c]  # noqa: E731     與 CSV 同口徑:只算非空格
        zj = sum(1 for z in zs if (nonempty(z) if z.get("rows") else z.get("records")))
        zc = len(csvz.get(f, ()))
        cj, cc = sum(len(nonempty(z)) for z in zs), csvc.get(f, 0)
        tj, tc = sum(len(z.get("records") or []) for z in zs if not z.get("rows")), csvt.get(f, 0)
        lamp_re = "RED" if (any(z.get("needs_ocr") for z in zs) or any("首頁無文字層" in x for x in (r.get("reasons") or []))) else ("YELLOW" if r.get("reasons") else "GREEN")
        p = indir / f
        exists = p.exists()
        bad = [n for n, okk in (("區", zj == zc), ("格", cj == cc), ("文", tj == tc), ("燈", lamp_re == r.get("lamp"))) if not okk]
        x = not bad
        ok += 1 if x else 0
        files.append({"file": f, "lamp": r.get("lamp"), "layout": r.get("layout", ""), "reasons": r.get("reasons") or [], "na": r.get("na") or [], "zones_json": zj, "zones_csv": zc, "cells_json": cj, "cells_csv": cc,
                      "lamp_recomputed": lamp_re, "xcheck": x, "bad": bad, "text_json": tj, "text_csv": tc, "input": "GRAY" if not exists else ("GREEN" if x else "RED"), "sha": hashlib.sha256(p.read_bytes()).hexdigest()[:12] if exists else ""})
    lamps = Counter(r.get("lamp") for r in res)
    regress = int(entry.get("regress", 0) or 0)
    st, ns, sreg, slock, spc, snew = stock_round(res, indir, v2, entry.get("round"), reg)
    L.append("[計] VRN-2 個股四項 · %d 份(全綠 %d)· %s · 本輪新鎖 %d 項 · 累計鎖 %d 項 · 退步 %d" % (len(st), sum(1 for e in st if e["lamp"] == "GREEN"),
             " · ".join("%s 綠%d黃%d紅%d灰%d" % (k, v.get("GREEN", 0), v.get("YELLOW", 0), v.get("RED", 0), v.get("GRAY", 0)) for k, v in spc.items()), snew, sum(len(v) for v in slock["files"].values()), len(sreg)))
    for f, k, l in sreg[:20]:
        L.append("[RED] 個股退步 · %s · %s(已鎖 → %s)" % (f[:40], k, l))
    for e in [e for e in st if e["lamp"] != "GREEN"][:40]:
        L.append("[計] 個股 %s · %s · %s" % (e["lamp"], e["file"][:36], " | ".join("%s %s %s" % (k, v[0][0], v[1][:34]) for k, v in e["parts"].items() if v[0] != "GREEN")))
    regress += len(sreg)
    acc, acnt = [], {}
    try:
        _li = json.loads((Path(reg or HERE / "registry") / "VRN2_Lock_latest.json").read_text(encoding="utf-8")).get("inputs")
    except Exception:  # noqa: BLE001
        _li = None
    try:
        acc, areg, aL, acnt = acceptance(res, indir, v2, st, _li)
        L.extend(aL)
        regress += len(areg)
    except Exception as exc:  # noqa: BLE001
        L.append("[RED] 完成驗收失敗 · %s %s" % (type(exc).__name__, str(exc)[:120]))
    success = bool(res) and regress == 0 and ok == len(files)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    engs = {}
    for pat in ("VRN_ENG397_P1Segment_v*.py", "VRN_ENG396_AssetIndex_v*.py"):
        c = sorted(HERE.glob(pat))
        if c:
            engs[c[-1].name] = hashlib.sha256(c[-1].read_bytes()).hexdigest()[:12]
    lock = {"subsystem": "VRN-2", "ts": ts, "success": success, "round": entry.get("round"), "manager": TAG, "engines": engs, "lamps": dict(lamps), "reasons": entry.get("reasons", {}), "locked": entry.get("locked"),
            "regress": regress, "xcheck_ok": ok, "n": len(files), "input_dir": str(indir), "inputs": {x["file"]: x["sha"] for x in files if x["sha"]}}
    L.append("[計] VRN-2 · 第 %s 輪 · 燈 %s · 退步 %d · 交互驗證(JSON ↔ CSV ↔ 燈號)%d/%d 一致 → %s" % (entry.get("round", "?"), dict(lamps), regress, ok, len(files), "成功 → 鎖定 + 備份" if success else "未達成功 · 不鎖不備份"))
    bk = None
    if success:
        rd = Path(reg or HERE / "registry")
        rd.mkdir(parents=True, exist_ok=True)
        (rd / ("VRN2_Lock_%s.json" % ts)).write_text(json.dumps(lock, ensure_ascii=False, indent=1), encoding="utf-8")
        (rd / "VRN2_Lock_latest.json").write_text(json.dumps(lock, ensure_ascii=False, indent=1), encoding="utf-8")
        bk = v2 / "backup" / ts
        bk.mkdir(parents=True, exist_ok=True)
        n = 0
        for nm in ("P1VIEW_latest.json", "P1VIEW_records_latest.csv", "P1VIEW_latest.md", "P1VIEW_latest.html", "VRN_P1View_Lock_latest.json", "VRN_P1View_Rounds.jsonl"):
            if (pv / nm).exists():
                shutil.copy2(pv / nm, bk / nm)
                n += 1
        (v2 / "VRN2_Success_latest.json").write_text(json.dumps({"ts": ts, "backup": str(bk), "lock": str(rd / ("VRN2_Lock_%s.json" % ts)), "files": n}, ensure_ascii=False, indent=1), encoding="utf-8")
        L.append("[計] VRN-2 鎖定 registry/VRN2_Lock_%s.json(引擎 %s)· 備份 %d 檔 → %s" % (ts, " · ".join("%s %s" % kv for kv in engs.items()), n, bk))
    trs = "".join("<tr><td><i style='background:%s'%s></i></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%d/%d</td><td>%d/%d</td><td>%s</td></tr>" % (
        _V2C.get(x["input"], "#9ca3af"), " class='bl'" if x["input"] == "RED" else "", html.escape(x["file"]), "<i style='background:%s'></i>%s" % (_V2C.get(x["lamp"], "#9ca3af"), x["lamp"]), html.escape(x["layout"]),
        html.escape(" / ".join(x["reasons"])) + (("<br><span style='color:#9ca3af'>" + html.escape(" / ".join(x.get("na") or [])) + "</span>") if x.get("na") else ""), x["zones_json"], x["zones_csv"], x["cells_json"], x["cells_csv"], "✓" if x["xcheck"] else "✗ 不一致:" + "、".join(x["bad"]) + ("(重算燈 %s)" % x["lamp_recomputed"] if "燈" in x["bad"] else "")) for x in files)
    page = ("<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>VRN-2 · 切割 / 擷取 / 修復</title><style>:root{--g:#16a34a;--y:#eab308;--r:#dc2626;--k:#9ca3af}body{font:12px system-ui,'Microsoft JhengHei';margin:10px;color:#111;background:#fff}"
            "h2{margin:0 0 6px}table{border-collapse:collapse;width:100%%;table-layout:auto}td,th{border:1px solid #e5e7eb;padding:2px 5px;vertical-align:top;word-break:break-all;text-align:left}th{background:#f3f4f6}i{display:inline-block;width:10px;height:10px;border-radius:50%%;margin-right:4px;vertical-align:middle}"
            ".bl{animation:b 1.6s infinite}@keyframes b{50%%{opacity:.25}}.sum{display:flex;gap:14px;flex-wrap:wrap;margin:6px 0}.sum span{padding:2px 8px;border:1px solid #e5e7eb;border-radius:6px}</style>"
            "<h2><i style='background:%s'%s></i>VRN-2 · 第一頁 + 財報頁 切割 / 擷取 / 修復 · %s</h2><div class='sum'><span>第 %s 輪</span><span>綠 %d · 黃 %d · 紅 %d</span><span>退步 %d</span><span>交互驗證 %d/%d</span><span>管理器 %s</span><span>引擎 %s</span><span>輸入 %s</span>%s</div>"
            "<table><tr><th>驗證</th><th>檔案</th><th>燈</th><th>版型</th><th>原因</th><th>區 JSON/CSV</th><th>格 JSON/CSV</th><th>交互驗證</th></tr>%s</table>" % (
                _V2C["GREEN" if success else "RED"], "" if success else " class='bl'", "成功 · 已鎖定 " + ts if success else "未達成功(退步 %d · 不一致 %d)" % (regress, len(files) - ok), entry.get("round", "?"), lamps.get("GREEN", 0), lamps.get("YELLOW", 0), lamps.get("RED", 0),
                regress, ok, len(files), TAG, html.escape(" · ".join(engs)), html.escape(str(indir)), ("<span>備份 %s</span>" % html.escape(str(bk))) if bk else "", trs))
    try:
        rgc, rgl, rgE, rgcnt = register(rd=reg)
        L += rgl
    except Exception as exc:  # noqa: BLE001
        rgE, rgcnt = {}, {}
        L.append("[計] 元件登記略過 · %s" % type(exc).__name__)
    page += _stock_html(st, ns, sreg, spc, slock) + (_accept_html(acc, acnt) if acc else "") + _activate_html(v2) + _register_html(rgE, rgcnt)
    try:
        try:
            _nons = sorted(e_["file"] for e_ in (acc or []) if e_.get("c5", ("", ""))[1] == "非個股報告")
            (v2 / "VRN2_Scope_latest.json").write_text(json.dumps({"stock": sorted(e_["file"] for e_ in (acc or []) if e_["file"] not in _nons), "non_stock": _nons}, ensure_ascii=False, indent=1), encoding="utf-8")
            _bk, _fd, _sm, _gaps, _made = _out_books(res, acc, st, v2)                # v0227 三本輸出冊
            L.append("[計] VRN-2 輸出冊 · %s · 目錄 %s" % (" · ".join(_made), v2 / "output"))
            for g_ in _gaps[:8]:
                L.append("[計] 輸出冊缺項 · %s" % g_)
            page = page.replace("</body>", _out_html(_bk, _fd, _sm) + "</body>") if "</body>" in page else page + _out_html(_bk, _fd, _sm)
            outbook = ("GREEN" if not _gaps else "YELLOW", "個股 %d 份 · 基本資料 %d · 年度數據 %d 筆 · 一標題四重點 %d%s" % (len(_bk), len(_bk), len(_fd), len(_sm), (" · 缺項 %d 份" % len(_gaps)) if _gaps else ""))
        except Exception as exc:  # noqa: BLE001
            outbook = ("RED", "輸出冊失敗 %s %s" % (type(exc).__name__, str(exc)[:80]))
        try:
            idem = _idem_check(res, indir)                                    # v0226 冪等閘
        except Exception as exc:  # noqa: BLE001
            idem = ("YELLOW", "冪等閘未完成 %s" % type(exc).__name__)
        L.append("[計] 冪等閘 · %s · %s" % (idem[0], idem[1][:160]))
        try:
            _ssb = sorted((HERE / "SSOT").glob("VRN2_SSOT_v[0-9][0-9][0-9][0-9].json"), key=lambda p: int(re.search(r"_v(\d{4})", p.name).group(1)))
            _ss = json.loads(_ssb[-1].read_text(encoding="utf-8")) if _ssb else {}
            _ft, _fc, _fl, funnel = _funnel(res, _ss)                         # v0228 調節輪
            L.append(_fl)
            page = page.replace("</body>", _funnel_html(_ft, _fc, _ss) + "</body>") if "</body>" in page else page + _funnel_html(_ft, _fc, _ss)
        except Exception as exc:  # noqa: BLE001
            funnel = ("YELLOW", "調節輪統計失敗 %s" % type(exc).__name__)
        page = page.replace("</style>", "</style>" + _opbar_html(v2), 1)       # v0228 頂端操作列
        _rn = next((x.split(":", 1)[-1].strip() for x in L if x.startswith("[RED] 鎖定過的檔案退步")), "")
        comp = completion(regress, ok, len(files), success, acnt, st, idem, outbook, funnel, _rn)
        (v2 / "VRN2_Completion_latest.json").write_text(json.dumps(comp, ensure_ascii=False, indent=1), encoding="utf-8")
        with (v2 / "VRN2_Completion_Rounds.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": comp["ts"], "verdict": comp["verdict"], "red": comp["red"], "yellow": comp["yellow"], "round": entry.get("round")}, ensure_ascii=False) + "\n")
        page = page.replace("</style>", "</style>" + _completion_html(comp), 1)
        L.append("[計] VRN-2 完成判定 · %s · 紅 %d · 黃 %d%s" % (comp["verdict"], comp["red"], comp["yellow"], (" · 已知例外:" + "、".join(comp["exceptions"])) if comp["exceptions"] else ""))
        for it in comp["items"]:
            if it["lamp"] == "RED":
                L.append("[RED] 完成判定未過 · %s · %s" % (it["name"], it["detail"][:160]))
    except Exception as exc:  # noqa: BLE001
        L.append("[RED] 完成判定失敗 · %s %s" % (type(exc).__name__, str(exc)[:120]))
    up = v2 / "VRN2_UI_latest.html"
    up.write_text(page, encoding="utf-8")
    L.append("  [U/I] %s" % up)
    if open_ui and hasattr(os, "startfile") and "--no-open" not in args:
        try:
            os.startfile(str(up))  # noqa: S606
        except OSError:
            pass
    return (0 if success else 1), L


def eol_refresh(home=None, snap=None) -> int:
    """v0200:修正閘指紋快照 · 只差行尾的檔(換行方式換一下就和快照一致)→ 視為未改 · 更新該筆 · 真不同的不動。回傳更新筆數。"""
    import hashlib
    home = Path(home or HERE)
    if snap is None:
        rf = _resolve("_rep_for")
        rep = Path(rf(home)) if rf else Path(_resolve("_rep")())
        snap = rep / "selfgate" / "snapshot_latest.json"
    snap = Path(snap)
    if not snap.exists():
        return 0
    try:
        prev = json.loads(snap.read_text(encoding="utf-8"))
    except ValueError:
        return 0
    fp, n = prev.get("fp") or {}, 0
    h16 = lambda b: hashlib.sha256(b).hexdigest()[:16]  # noqa: E731
    for rel, old in list(fp.items()):
        p = home / rel
        if not p.exists():
            continue
        b = p.read_bytes()
        cur = h16(b)
        if cur == old:
            continue
        lf = b.replace(b"\r\n", b"\n")
        if old in (h16(lf), h16(lf.replace(b"\n", b"\r\n"))):
            fp[rel] = cur
            n += 1
    if n:
        prev["fp"] = fp
        snap.write_text(json.dumps(prev, ensure_ascii=False), encoding="utf-8")
    return n


def reconcile(apply: bool = False, home=None, conf=None) -> tuple:
    """不要同號 · 出新版號(v0196):同版號內容不同 → 本機內容另存 v+1 · 原號還原成 main 的內容 · 兩邊都保留 · 先列計畫 · --apply 才動 · 每步寫帳本。"""
    import datetime
    import subprocess
    home = Path(home or (_resolve("_home") or (lambda: HERE))())
    conf = _git_conflicts(home) if conf is None else list(conf)   # conf 只供自測注入
    if not conf:
        return 0, ["[計] 版本號衝突 0 · 不用調和"]
    try:
        top = subprocess.run(["git", "-C", str(home), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:  # noqa: BLE001
        top = ""
    L, done = ["[計] 版本號衝突調和 %s · %d 件(整族接續編號:本機各版依序存到該族現有最大版號之後 · 原號還原 main · 只增不減)" % ("執行" if apply else "計畫(不動檔 · 加 --apply 才執行)", len(conf))], []
    fams = {}
    for rel in conf:
        rp = Path(rel)
        m = re.search(r"^(.*_v)(\d{3,4})(\..+)$", rp.name)
        if m:
            fams.setdefault((str(rp.parent), m.group(1), m.group(3)), set()).add(int(m.group(2)))
    for (sub, pre, ext), vers in sorted(fams.items()):
        folder = home / sub
        exist = [int(mm.group(1)) for q in folder.glob(pre + "*" + ext) for mm in [re.search(r"_v(\d{3,4})$", q.stem)] if mm]
        nxt = max(exist, default=0) + 1
        for v in sorted(vers):
            old = pre + ("%04d" % v) + ext
            p = folder / old
            if not p.exists():
                p = next((q for q in folder.glob(pre + "%d" % v + ext)), None)
            if not p:
                continue
            nv = pre + ("%04d" % nxt) + ext
            nxt += 1
            np_ = p.with_name(nv)
            L.append("[計] 調和 %s → 本機內容存為 %s · 原號還原 main%s" % ((sub + "/" if sub != "." else "") + old, nv, " · 同族 %d 版衝突 · 接續編號" % len(vers) if len(vers) > 1 else ""))
            if apply and not np_.exists() and top:
                try:
                    np_.write_bytes(p.read_bytes())
                    relp = str(p.resolve().relative_to(Path(top).resolve())).replace("\\", "/")
                    r = subprocess.run(["git", "-C", top, "checkout", "origin/main", "--", relp], capture_output=True, text=True, timeout=60)
                    done.append({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "file": (sub + "/" if sub != "." else "") + old, "new_version": nv, "restored_from": "origin/main", "rc": r.returncode})
                except Exception as exc:  # noqa: BLE001
                    L.append("[RED] 調和失敗 %s · %s" % (old, type(exc).__name__))
    rd = home / "registry"
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "VRN_Reconcile_Plan_latest.md").write_text("# 版本號衝突調和計畫 · %s · %d 件\n" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), len(conf)) + "\n".join("- " + l[4:] for l in L[1:] if l.startswith("[計] 調和")) + "\n", encoding="utf-8")
    L.append("  [MD] %s" % (rd / "VRN_Reconcile_Plan_latest.md"))
    if apply:
        with (rd / "VRN_Reconcile_Ledger.jsonl").open("a", encoding="utf-8") as fh:
            for d in done:
                fh.write(json.dumps(d, ensure_ascii=False) + "\n")
        L.append("[計] 調和完成 %d 件 · 帳本 registry/VRN_Reconcile_Ledger.jsonl" % len(done))
    return 0, L


def p1loop(one: str = "", rep=None, prior=None) -> tuple:
    """v0196:退步區塊細節直接印進貼包(≤12 行)· 不用開 MD。rep / prior 只供自測注入 · 不替換任何函式(零頭)。"""
    rc, lines = (prior or PRIOR.p1loop)(one)
    try:
        pv = (Path(rep) if rep else Path(_resolve("_rep")())) / "p1view"
        reg = [l for l in lines if l.startswith("[RED] 鎖定過的檔案退步")]
        if reg:
            res = {r["file"]: r for r in json.loads((pv / "P1VIEW_latest.json").read_text(encoding="utf-8"))}
            names = re.findall(r"([^|:]+?\.pdf)\(", reg[0])
            n = 0
            for nm in names:
                r = next((v for k, v in res.items() if k.startswith(nm.strip()[:20])), None)
                for pg in (r or {}).get("pages") or []:
                    for z in pg["zones"]:
                        if n < 12 and (z.get("needs_ocr") or (z["minor"] == "TB" and pg["pno"] > 1 and "期間欄" not in (z.get("engine") or ""))):
                            txt = " ".join(x["text"] for x in z.get("records") or []) or " | ".join(" ".join(c for c in row if c) for row in (z.get("rows") or [])[:3])
                            lines.append("[計] 退步細節 %s · %s | %s·%s | %s | %s | 亂碼 %s 常用 %s | %s" % (r["file"][:22], z["id"], z["major"], z["minor_zh"], [int(v) for v in z["bbox"]], z.get("engine", ""), z.get("garbled", 0), z.get("common", ""), txt[:70]))
                            n += 1
    except Exception as exc:  # noqa: BLE001
        lines.append("[計] 退步細節印出失敗 · %s" % type(exc).__name__)
    return rc, lines


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["vrn2scope"]:                                          # v0227 範圍聚焦 + 獨立設定冊
        rc_, ln_ = vrn2scope(args[1:])
        for x in ln_:
            print(x, flush=True)
        return rc_
    if args[:1] == ["acc-shard"] and "--shard" in args:
        return _acc_shard_main(args[args.index("--shard") + 1])
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["selfgate"] and "--sandbox" in args:
        run, pg = _resolve("selfgate_run"), _resolve("_print_gate")
        o = run("sandbox", panorama="--no-panorama" not in args)
        moved = env_flaky_filter(o, _older_has)
        if moved:
            print("[計] 在地測試 · 新尾版多出的失敗 %d 筆是舊版本就有的環境相依測試(OCR / 網路 · 時過時不過)→ 歸類環境 · 不算新增失敗:%s" % (len(moved), " | ".join(moved)))
        return pg(o)
    if args[:1] == ["selfgate"] and "--sandbox" not in args:
        try:
            n = eol_refresh()
            if n:
                print("[計] 修正閘指紋 · 只差行尾(CRLF/LF)%d 檔 → 視為未改(內容相同 · 快照已更新 · 真不同的仍判紅)" % n)
        except Exception as exc:  # noqa: BLE001
            print("[計] 修正閘指紋核對略過 · %s" % type(exc).__name__)
        return _mod_v0214("v0194").main(args)
    if args[:1] == ["vrn2"]:
        rc, lines = vrn2(args[1:])
        for l in lines:
            print(l)
        return rc
    if args[:1] == ["accelfix"]:
        lim = int(args[args.index("--limit") + 1]) if "--limit" in args and args.index("--limit") + 1 < len(args) else 20
        rc, lines = accelfix("--apply" in args, limit=lim, every="--all" in args)
        if "--all" in args:
            rc2, l2 = ps_accelfix("--apply" in args, limit=max(lim, 2000))
            lines += l2
        for l in lines:
            print(l)
        return rc
    if args[:1] == ["register"]:
        rc, lines, _, _ = register()
        for l in lines:
            print(l)
        return rc
    if args[:1] == ["envcheck"]:
        rc, lines = envcheck("--install" in args)
        for l in lines:
            print(l)
        return rc
    if args[:1] == ["linkmap"]:
        rc, lines = linkmap_verb()
        for l in lines:
            print(l)
        return rc
    if args[:1] == ["reconcile"]:
        rc, lines = reconcile("--apply" in args)
        for l in lines:
            print(l)
        return rc
    if args[:1] == ["register2"]:
        for l in asset_lines(asset_register()):
            print(l)
        return 0
    if args[:1] in (["p1view"], ["p1loop"]):
        one = args[args.index("--one") + 1] if "--one" in args and args.index("--one") + 1 < len(args) else ""
        rc, lines = (p1loop if args[0] == "p1loop" else _resolve("p1view"))(one)
        for l in lines:
            print(l)
    else:
        rc = _mod_v0214("v0194").main(args)                    # v0197:其他動詞走 v0194 的 main(避免 v0195 / v0196 的登記鉤子重複登記)
    if args and args[0] not in ("selfgate", "ui", "reconcile", "accelfix", "vrn2", "envcheck", "register") and not args[0].startswith("-"):
        try:
            for l in asset_lines(asset_register()):               # v0195:任何動詞跑完自動登記(內容沒變不出新版)
                print(l)
        except Exception as exc:  # noqa: BLE001
            print("[計] 資產登記失敗 · %s" % type(exc).__name__)
    return rc


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    import json
    import tempfile
    td = Path(tempfile.mkdtemp(prefix="p1loop-"))
    (td / "p1view").mkdir()
    (td / "p1view" / "P1VIEW_latest.json").write_text(json.dumps([{"file": "Citi-5904 20260916.pdf", "lamp": "YELLOW", "reasons": ["財報表沒對到期間欄 1/7"], "pages": [{"pno": 1, "zones": []}, {"pno": 4, "zones": [{"id": "P4·FR·02·TB", "major": "FR", "minor": "TB", "minor_zh": "財報表", "bbox": [300, 100, 560, 400], "engine": "pdfplumber", "garbled": 0, "common": 0.95, "rows": [["Key ratios"], ["ROE (%)", "12.1", "13.4"]]}]}]}]), encoding="utf-8")
    rc1, l1 = p1loop(rep=td, prior=lambda one="": (1, ["[RED] 鎖定過的檔案退步 1:Citi-5904 20260916.pdf(財報表沒對到期間欄 1/7)"]))
    ta = Path(tempfile.mkdtemp(prefix="areg2-"))
    (ta / "registry").mkdir()
    (ta / "VRN_X_v0100.py").write_text('"""x"""\n', encoding="utf-8")
    (ta / "old_tool_sha0123456789ab.py").write_text("y = 1\n", encoding="utf-8")
    os.environ["VIA_SPILL_DIR"] = str(ta / "run1")
    a1 = asset_register(ta)
    os.environ["VIA_SPILL_DIR"] = str(ta / "run2")
    a2 = asset_register(ta)
    chk("⓪ 易變參數(VIA_SPILL_DIR 換值)不出新版(第二次無變更 %s)· _sha 字尾舊腳本不點名(沒版號 %s)· 待整理 %d" % (not a2["changed"], a1["no_version"], a1["pending_tidy"]),
        a1["changed"] and not a2["changed"] and "old_tool_sha0123456789ab.py" not in a1["no_version"] and a1["pending_tidy"] == 1 and _mod_v0214("v0194").TAG == "v0194")
    o_t = {"red": ["新尾版多出失敗「⑥ 第三步 OCR:影像表格(P# 圖區無文字層)→ 自動選 輕型單引擎 rapidocr」", "新尾版多出失敗「③ 斷句銜接」"], "verdict": "RED"}
    mv = env_flaky_filter(o_t, lambda lab: True)
    o_u = {"red": ["新尾版多出失敗「⑥ 第三步 OCR:影像表格」"], "verdict": "RED"}
    mv2 = env_flaky_filter(o_u, lambda lab: True)
    chk("⓪ 沙盒閘環境相依過濾:OCR 測試移到環境(1)· 斷句測試仍紅 · 全是環境時 RED→YELLOW", len(mv) == 1 and o_t["red"] == ["新尾版多出失敗「③ 斷句銜接」"] and o_t["verdict"] == "RED" and len(mv2) == 1 and o_u["verdict"] == "YELLOW" and not o_u["red"])
    te = Path(tempfile.mkdtemp(prefix="eol-"))
    import hashlib as _h
    (te / "a.py").write_bytes(b"x = 1\ny = 2\n")
    (te / "b.py").write_bytes(b"x = 9\n")
    sp = te / "snap.json"
    sp.write_text(json.dumps({"fp": {"a.py": _h.sha256(b"x = 1\r\ny = 2\r\n").hexdigest()[:16], "b.py": _h.sha256(b"x = 1\n").hexdigest()[:16]}, "verdict": "RED"}), encoding="utf-8")
    n_e = eol_refresh(te, sp)
    fp2 = json.loads(sp.read_text(encoding="utf-8"))["fp"]
    chk("⓪ 修正閘指紋核對:a.py 只差行尾 → 快照更新(1 筆)· b.py 內容真不同 → 不動(仍會判紅)", n_e == 1 and fp2["a.py"] == _h.sha256(b"x = 1\ny = 2\n").hexdigest()[:16] and fp2["b.py"] == _h.sha256(b"x = 1\n").hexdigest()[:16])
    tf = Path(tempfile.mkdtemp(prefix="rec-"))
    for v in (102, 103, 104):
        (tf / ("VRN_X_SSOT_v%04d.json" % v)).write_text("{}", encoding="utf-8")
    (tf / "sub").mkdir()
    (tf / "sub" / "VRN_X_SSOT_v0102.json").write_text("{}", encoding="utf-8")
    rc0, pl = reconcile(False, home=tf, conf=["VRN_X_SSOT_v0102.json", "VRN_X_SSOT_v0103.json", "VRN_X_SSOT_v0104.json", "sub/VRN_X_SSOT_v0102.json", "VRN_X_SSOT_v0102.json"])
    got = re.findall(r"調和 (\S+) → 本機內容存為 (\S+)", "\n".join(pl))
    chk("⓪ 整族接續編號:根夾 v0102~v0104 → v0105 / v0106 / v0107(四位 · 去重)· sub 夾同名 v0102 另成一族 → v0103 · 不動檔 → %s" % got,
        got == [("VRN_X_SSOT_v0102.json", "VRN_X_SSOT_v0105.json"), ("VRN_X_SSOT_v0103.json", "VRN_X_SSOT_v0106.json"), ("VRN_X_SSOT_v0104.json", "VRN_X_SSOT_v0107.json"), ("sub/VRN_X_SSOT_v0102.json", "VRN_X_SSOT_v0103.json")]
        and not (tf / "VRN_X_SSOT_v0105.json").exists() and rc0 == 0)
    ta2 = Path(tempfile.mkdtemp(prefix="af-"))
    (ta2 / "VRN_ENG_Q_v0100.py").write_text('"""Q 引擎"""\nfrom __future__ import annotations\nimport json\nX = 1\n', encoding="utf-8")
    (ta2 / "VRN_ENG_R_v0100.py").write_text('"""R 引擎 [VIA:ACCEL-BRIDGE:v0111] 已有"""\nY = 2\n', encoding="utf-8")
    rc_a, la = accelfix(True, home=ta2, limit=20)
    nq = ta2 / "VRN_ENG_Q_v0101.py"
    chk("⓪ accelfix:缺標記的 Q → 出 v0101(docstring + __future__ 之後注入 · 編譯過)· 已有標記的 R 不動 · 原檔不動 → %s" % [l for l in la if "注入 VRN_ENG_Q" in l][:1],
        rc_a == 0 and nq.exists() and "[VIA:ACCEL-BRIDGE" in nq.read_text(encoding="utf-8") and nq.read_text(encoding="utf-8").splitlines()[1].startswith("from __future__") and compile(nq.read_text(encoding="utf-8"), "q", "exec")
        and not (ta2 / "VRN_ENG_R_v0101.py").exists() and (ta2 / "VRN_ENG_Q_v0100.py").read_text(encoding="utf-8").count("ACCEL") == 0 and (ta2 / "registry" / "VRN_AccelFix_Ledger.jsonl").exists())
    _t0 = __import__("time").time()
    tv = Path(tempfile.mkdtemp(prefix="v2-"))
    (tv / "rep" / "p1view").mkdir(parents=True)
    (tv / "in").mkdir()
    (tv / "in" / "a.pdf").write_bytes(b"%PDF-1.4 a")
    resj = [{"file": "a.pdf", "lamp": "GREEN", "layout": "單欄型", "reasons": [], "pages": [{"zones": [{"id": "P1·M·01·TB", "rows": [["x", "1", ""], ["y", "2", ""]], "needs_ocr": False}, {"id": "P1·M·02·TX", "rows": [], "records": [{"kind": "句", "text": "hi"}], "needs_ocr": False}, {"id": "P1·M·03·IMG", "rows": [], "records": [], "needs_ocr": False}]}]},
            {"file": "b.pdf", "lamp": "YELLOW", "layout": "側欄型(右)", "reasons": ["沒找到財報頁"], "pages": [{"zones": [{"id": "P1·M·01·TX", "rows": [], "records": [{"kind": "句", "text": "yo"}], "needs_ocr": False}]}]}]
    (tv / "rep" / "p1view" / "P1VIEW_latest.json").write_text(json.dumps(resj, ensure_ascii=False), encoding="utf-8")
    (tv / "rep" / "p1view" / "P1VIEW_records_latest.csv").write_text("\ufeffFILE,ZONE,REC_KIND,TEXT\na.pdf,P1·M·01·TB,格,x\na.pdf,P1·M·01·TB,格,1\na.pdf,P1·M·01·TB,格,y\na.pdf,P1·M·01·TB,格,2\na.pdf,P1·M·02·TX,句,hi\nb.pdf,P1·M·01·TX,句,yo\n", encoding="utf-8")
    (tv / "rep" / "p1view" / "VRN_P1View_Rounds.jsonl").write_text(json.dumps({"round": 12, "regress": 0, "locked": 14, "reasons": {}}) + "\n", encoding="utf-8")
    rc_v, lv = vrn2(["--no-open"], rep=tv / "rep", indir=tv / "in", open_ui=False, reg=tv / "reg")
    ui = (tv / "vrn2" / "VRN2_UI_latest.html")
    lk = tv / "reg" / "VRN2_Lock_latest.json"
    chk("⓪ VRN-2:退步 0 + 交互驗證 2/2 一致(圖區無內容 · 空格不寫 CSV → 口徑一致不誤判) → 成功 · 鎖定(registry/VRN2_Lock_latest.json)· 備份 3 檔 · U/I 產出(a 綠 · b 的 PDF 不在 → 灰)· rc 0", rc_v == 0 and ui.exists() and lk.exists() and json.loads(lk.read_text(encoding="utf-8"))["xcheck_ok"] == 2 and "VRN2_Success_latest.json" in [p.name for p in (tv / "vrn2").iterdir()] and len(list((tv / "vrn2" / "backup").iterdir())) == 1)
    (tv / "rep" / "p1view" / "VRN_P1View_Rounds.jsonl").write_text(json.dumps({"round": 13, "regress": 1, "locked": 14}) + "\n", encoding="utf-8")
    rc_w, lw = vrn2(["--no-open"], rep=tv / "rep", indir=tv / "in", open_ui=False, reg=tv / "reg")
    chk("⓪ VRN-2:退步 1 → 未達成功 · 不鎖不備份 · U/I 紅燈閃爍 · rc 1", rc_w == 1 and "未達成功" in ui.read_text(encoding="utf-8") and len(list((tv / "vrn2" / "backup").iterdir())) == 1)
    sa = stock_eval({"file": "20250819兆豐個股報告-泓德能源(6873).pdf", "lamp": "GREEN", "reasons": [], "fin_n": 2, "pages": [
        {"pno": 1, "zones": [{"major": "T", "minor": "RT", "records": [{"text": "逢低買進 $208"}], "rows": []}]},
        {"pno": 6, "zones": [{"major": "F", "minor": "TB", "engine": "pdfplumber(期間欄對齊)", "rows": [["", "2023", "2024", "2025(F)"], ["每股盈餘(元)", "8.16", "11.10", "9.76"], ["本益比(X)", "16.0", "20.5", "17.6"], ["股價淨值比(X)", "2.2", "2.6", "1.9"]]}]}]}, 8)
    sb = stock_eval({"file": "20260917兆豐投資早報.pdf", "lamp": "YELLOW", "reasons": ["沒找到財報頁"], "pages": []}, 4)
    sd = stock_eval({"file": "Citi-3231 20250604.pdf", "lamp": "YELLOW", "reasons": ["沒找到財報頁"], "fin_n": 0, "pages": [{"pno": 1, "zones": [
        {"major": "T", "minor": "TX", "records": [{"text": "Flash | Wistron (3231.TW)"}], "rows": []},
        {"major": "M", "minor": "TB", "engine": "pdfplumber", "rows": [["Year to", "Net Profit", "EPS", "P/E", "P/B", "ROE", "Yield"], ["2024A", "17,446", "6.12", "18.6", "2.5", "14.7", "3.3"], ["2025E", "24,878", "8.72", "13.1", "2.0", "16.8", "4.5"]]}]}]}, 13)
    se = stock_eval({"file": "MS-1590 20251202.pdf", "lamp": "YELLOW", "reasons": ["沒找到財報頁"], "fin_n": 0, "pages": [{"pno": 1, "zones": [{"major": "T", "minor": "TX", "records": [{"text": "Update"}], "rows": []}]}]}, 9)
    sf = stock_eval({"file": "3014TT-20231005.pdf", "lamp": "YELLOW", "reasons": [], "fin_n": 1, "pages": [{"pno": 1, "zones": [{"major": "T", "minor": "DT", "records": [{"text": "投資顧問 個股報告 2023/10/05"}], "rows": []}, {"major": "T", "minor": "TT", "records": [{"text": "團泰期賃國泰證券子公司"}], "rows": []}]}]}, 10)
    chk("⓪ 判定修正:Citi 年份往下排的 Earnings Summary 算年度表(綠)· MS 月營收 Update 無年度表 → 灰 · 3014TT 券商從首頁補「國泰」 → %s / %s / %s" % (sd["parts"]["年度財報"][0], se["parts"]["年度財報"][0], sf.get("broker")),
        sd["parts"]["年度財報"][0] == "GREEN" and sd["parts"]["評價資訊"][0] == "GREEN" and se["parts"]["年度財報"][0] == "GRAY" and sf["broker"] == "國泰" and sf["parts"]["檔名"][0] == "GREEN")
    sg = stock_eval({"file": "Daiwa-6278 20260521.pdf", "lamp": "GREEN", "reasons": [], "fin_n": 1, "pages": [{"pno": 1, "zones": [{"major": "M", "minor": "TX", "records": [{"text": "Background: We met with Taiwan Surface Mounting Technology's management on 21 May. Valuation: PERs of 21.4x and 17.4x"}], "rows": []}]},
        {"pno": 2, "zones": [{"major": "F", "minor": "TB", "engine": "pdfplumber(期間欄對齊)", "rows": [["(TWDm)", "2024", "2025"], ["Net sales", "45,288", "49,877"], ["EPS (TWD)", "9.94", "9.39"]]}]}]}, 4)
    sh = stock_eval({"file": "MQ-1560 20260520.pdf", "lamp": "RED", "reasons": ["首頁無文字層 → OCR 排隊", "沒找到財報頁"], "fin_n": 0, "pages": [{"pno": 1, "zones": []}]}, 4)
    si = stock_eval({"file": "UBS-4966 20260914.pdf", "lamp": "YELLOW", "reasons": ["沒找到財報頁"], "fin_n": 0, "pages": [{"pno": 1, "zones": [{"major": "M", "minor": "TX", "records": [{"text": "2026 Taiwan Summit Highlights (NT$m) 12/23 12/24 12/25 12/27E Revenues 13,769 EPS P/E Dividend yield EV/EBITDA price target"}], "rows": []}]}]}, 12)
    chk("⓪ 第 20 輪實證:Daiwa Background 快訊 EPS + 本益比 → 評價綠 · MQ 首頁無文字層 → 首頁紅(OCR)· UBS Summit 年度數據在文字段 → 年度黃(引擎待修)→ %s / %s / %s" % (sg["parts"]["評價資訊"][0], sh["parts"]["首頁"][0], si["parts"]["年度財報"][0]),
        sg["parts"]["評價資訊"][0] == "GREEN" and sh["parts"]["首頁"][0] == "RED" and si["parts"]["年度財報"][0] == "YELLOW")
    sc = stock_eval({"file": "光焱(7728,Note)-CTBC260918.pdf", "lamp": "YELLOW", "reasons": ["沒找到財報頁", "首頁沒抓到評等 / 目標價"], "fin_n": 0, "pages": [{"pno": 1, "zones": [{"major": "M", "minor": "TX", "records": [{"text": "法說 / 座談摘要"}], "rows": []}]}]}, 2)
    chk("⓪ 個股四項:泓德(6873)四項全綠(兆豐 · 2025-08-19 · 年度表期間欄對齊 · EPS + 本益比 + 股價淨值比)· 投資早報 = 非個股 · 光焱 Note 2 頁 = 檔名綠(中信 · 2026-09-18)· 首頁 / 財報 / 評價灰(Note 本來沒有評等) → %s / %s / %s" % (
        sa.get("lamp"), sb.get("stock"), {k: v[0] for k, v in (sc.get("parts") or {}).items()}),
        sa["lamp"] == "GREEN" and sa["date"] == "2025-08-19" and sa["broker"] == "兆豐" and not sb["stock"] and sc["date"] == "2026-09-18" and sc["broker"] == "中信"
        and {k: v[0] for k, v in sc["parts"].items()} == {"檔名": "GREEN", "首頁": "GRAY", "年度財報": "GRAY", "評價資訊": "GRAY"} and _sk_date("華南投顧-2606-裕民-1141202.pdf") == "2025-12-02" and _sk_ticker("華南投顧-2606-裕民-1141202.pdf", "") == "2606")
    chk("⓪ VRN-2 自測只寫暫存夾:真正的 registry/ 沒有被寫入 VRN2_*(自測不污染鎖定)", not any(p.stat().st_mtime > _t0 for p in (HERE / "registry").glob("VRN2_*")) if (HERE / "registry").exists() else True)
    tp = Path(tempfile.mkdtemp(prefix="acc-"))
    (tp / "A_v0101.py").write_text('"""doc"""\nfrom __future__ import annotations\nimport VIA_SuperAccel_Module\nX = 1\n', encoding="utf-8")
    (tp / "B_v0101.py").write_text('#!/usr/bin/env python\n"""doc"""\nimport VeritasCeleritas_v1141 as vc\nY = 2\n', encoding="utf-8")
    (tp / "C_v0101.py").write_text('"""ok"""\n' + BRIDGE_TXT + 'Z = 3\n', encoding="utf-8")
    rc_a, la = accelfix(True, home=tp, limit=50, every=True)
    na = sorted(p.name for p in tp.glob("*_v0102.py"))
    okc = all(compile(p.read_text(encoding="utf-8"), p.name, "exec") is not None and "VIA:ACCEL-BRIDGE:v0111" in p.read_text(encoding="utf-8") for p in tp.glob("*_v0102.py"))
    chk("⓪ accelfix --all:舊橋(SUP_MDL737)與寫死 v1141 的尾版都補動態最新版號橋 · 已是動態橋的不動 · 原檔不動 · v+1 可編譯 → %s" % na, na == ["A_v0102.py", "B_v0102.py"] and okc and (tp / "A_v0101.py").read_text(encoding="utf-8").count("ACCEL-BRIDGE") == 0)
    ev_rc, ev_l = envcheck(False)
    chk("⓪ envcheck:AST 掃 import → 分必裝 / 選裝 / 隔離 · 只檢查不安裝(未帶 --install)→ %s" % (ev_l[0][:90] if ev_l else "—"), bool(ev_l) and ev_l[0].startswith("[計] 環境檢查"))
    tg = Path(tempfile.mkdtemp(prefix="rg-"))
    (tg / "VRN_ENG900_Demo_v0101.py").write_text('import os\nimport re\nBROKERS = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}\nRX = re.compile(r"\\d{4}")\nclass Box:\n    pass\ndef run(x):\n    os.environ.get("VIA_DEMO_HOME")\n    open("out_latest.json", "w")\n    return x\ndef _hidden():\n    pass\nC = \'{"schema": "Demo.v1", "fields": [{"name": "FILE"}, {"name": "ZONE"}]}\'\n', encoding="utf-8")
    r1 = register(home=tg, rd=tg / "registry", rep=tg)
    E1 = r1[2]
    nos = {e["kind"]: e["no"] for e in E1.values()}
    r2 = register(home=tg, rd=tg / "registry", rep=tg)
    (tg / "VRN_ENG900_Demo_v0101.py").write_text((tg / "VRN_ENG900_Demo_v0101.py").read_text(encoding="utf-8").replace("return x", "return x + 1").replace("class Box:\n    pass\n", ""), encoding="utf-8")
    r3 = register(home=tg, rd=tg / "registry", rep=tg)
    E3 = r3[2]
    fn = E3["FNC|VRN_ENG900_Demo.run"]
    chk("⓪ 元件登記:ENG / CLS / FNC / DICT / REGEX / PARAM / OUT / DF 各自編號(%s)· 私有函式不登 · 第二次無變更不出新版 · 函式改了號不變記版本史 · 類別刪了標退役不刪 · 版本 %d 本" % (" ".join(sorted(nos.values())), len(list((tg / "registry").glob("VRN2_Component_Register_v*.json")))),
        {"ENG", "CLS", "FNC", "DICT", "REGEX", "PARAM", "OUT", "DF"} <= set(nos) and "FNC|VRN_ENG900_Demo._hidden" not in E1 and "無變更" in r2[1][-1]
        and fn["no"] == E1["FNC|VRN_ENG900_Demo.run"]["no"] and len(fn["history"]) == 2 and E3["CLS|VRN_ENG900_Demo.Box"]["status"].startswith("退役")
        and len(list((tg / "registry").glob("VRN2_Component_Register_v*.json"))) == 2)
    chk("⓪ 基準快照路徑排除:references / baseline / _sandbox 不算衝突", not re.search(r"(?i)[\\/](?:references|baseline|_sandbox)[\\/]", "SSOT/VRN_X_v0100.json/") and bool(re.search(r"(?i)[\\/](?:references|baseline|_sandbox)[\\/]", "references/intake/VIA_X/baseline/VRN_X_v0100.json/")))
    chk("⓪ linkmap 動詞接 ENG396 最新版(有 linkmap 才跑 · 沒有照實說)", callable(linkmap_verb))
    src_fake = 'chk("⑥ 第三步 OCR:影像表格(P%d 圖區無文字層)→ 自動選 輕型單引擎 rapidocr@%s(表格提高 DPI)")'
    lab = "⑥ 第三步 OCR:影像表格(P# 圖區無文字層)→ 自動選 輕型單引擎 rapidocr@#(表格提高 DPI)"
    chk("⓪ 測試名稱骨幹比對:閘印的 P# / @# 對得上原始碼的 P%%d / @%%s(%s)" % _skel(lab)[:10], _skel(lab)[:10] in _skel(src_fake) and len(_skel(lab)[:10]) >= 4)
    chk("① p1loop 退步區塊細節直接印進貼包(區編號 · 框 · 引擎 · 首 70 字)· 自測用參數注入 · 零替換 · reconcile 無衝突時回 0", rc1 == 1 and any(l.startswith("[計] 退步細節") and "P4·FR·02·TB" in l and "Key ratios" in l for l in l1) and reconcile(False)[0] == 0)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("② 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片 · 正式流程零替換 · 自測也零替換(參數注入)", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__)
        and "setattr(" not in me.split("def selftest")[0])
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    _zt = [{"id": "P2·FL·01·TB", "kind": "表", "rows": [["", "2024", "2025F"], ["營業收入", "1,000", "1,200"], ["營業毛利", "380", "456"], ["毛利率 (%)", "38.0", "38.0"], ["營業利益", "200", "300"], ["營業利益率 (%)", "20.0", "25.0"]]}]
    _ok, _bad, _det = _acc_calc(_zt)
    _zt[0]["rows"][3][2] = "40.0"
    _ok2, _bad2, _det2 = _acc_calc(_zt)
    _ns = _acc_numset("營收 1 20,843 百萬 · 毛利率 38.0% · (457)")
    _cov = _acc_cover("投資重點 營收成長", [{"records": [{"text": "投資重點"}], "rows": [["營收", "成長"]]}])
    chk("⓪ v0215 完成驗收:① 利潤率重算 %d 過 %d 不符(竄改 2025F 毛利率 → %d 不符 · FAIL_CLOSED「%s」)③ 原文數字集合接回字距拆開的 120843 / 38 / 457 · ② 覆蓋率 %.0f%%" % (_ok, _bad, _bad2, (_det2 or [""])[0][:40], _cov * 100),
        _ok == 4 and _bad == 0 and _bad2 == 1 and _ok2 == 3 and {"120843", "38", "457"} <= _ns and _cov == 1.0)
    _inc = {"id": "P6·F·03·TB", "kind": "表", "rows": [["季度損益表"], ["", "2023", "24Q1", "2024", "2025(F)"], ["營業收入淨額", "5,839", "884", "10,125", "12,108"], ["營業毛利淨額", "1,450", "230", "2,528", "2,813"]]}
    _rat = {"id": "P7·F·03·TB", "kind": "表", "rows": [["重要財務比率分析"], ["", "2023", "2024", "2025(F)"], ["營業毛利率", "25.8", "26.5", "23.2"]]}
    _inq = {"id": "P6·F·04·TB", "kind": "表", "rows": [["季度損益表"], ["", "2023", "2024"], ["營業收入淨額", "5,839", "10,125"], ["營業成本", "4,332", "7,440"], ["營業毛利淨額", "1,450", "2,528"], ["營業毛利率", "25.8", "26.5"]]}
    _o6, _b6, _d6 = _acc_calc([_inq])
    _bil = {"id": "P1·R·05·TB", "kind": "表", "rows": [["", "2024", "2025"], ["Revenue (NT$ bn)", "421.1", "558.6"], ["Gross margin (%)", "32.4", "34.2"]]}
    _gpm = {"id": "P5·F·01·TB", "kind": "表", "rows": [["", "2024", "2025"], ["Revenue", "421,100", "558,600"], ["Gross profit", "136,580", "190,826"]]}
    _o3, _b3, _d3 = _acc_calc([_inc, _rat])
    _o4, _b4, _d4 = _acc_calc([_bil, _gpm])
    _ta = {"id": "P2·F·01·TB", "kind": "表", "rows": [["", "Mar-25A", "Dec-25A", "Dec-25A"], ["營業收入", "3,510", "5,091", "16,896"], ["營業毛利", "237", "1,923", "4,225"], ["營業毛利率", "6.8", "37.8", "25.0"]]}
    _o5, _b5, _d5 = _acc_calc([_ta])
    chk("⓪ v0216 驗收實證:跨表不一致 → 黃(%d 過 · 同表不符 %d · 跨表 %d)· 泓德毛利率 = (營收 − 營業成本) ÷ 營收(%d 過 %d 不符)· MS-2308 十億 vs 百萬兩表不混算(%d 過 %d 不符)· 凱基季度 + 年度同年取最右(%d 過 %d 不符)" % (
        _o3, _b3, sum(1 for d in _d3 if d.startswith("〔原文跨表")), _o6, _b6, _o4, _b4, _o5, _b5),
        _o3 == 1 and _b3 == 0 and sum(1 for d in _d3 if d.startswith("〔原文跨表")) == 2 and _o6 == 2 and _b6 == 0 and _b4 == 0 and _o4 == 2 and _b5 == 0 and _o5 == 1)
    chk("⓪ v0217 正式名稱 %s · 檔名家族 %s 保留(前版鏈 / 修正閘找得到)" % (DISPLAY_NAME, _STEM), DISPLAY_NAME == "VRN-2 SystemManager" and _STEM == "VRN_SystemManager" and PRIOR_PATH.name.startswith(_STEM))
    _c1 = completion(0, 18, 18, True, {"c1": {"GREEN": 16, "GRAY": 2}, "c2": {"GREEN": 15, "YELLOW": 2}, "c3": {"GREEN": 17}, "c5": {"GREEN": 14, "YELLOW": 2}, "c6": {"GRAY": 18}},
                     [{"file": "MQ-1560.pdf", "parts": {"首頁": ("RED", "首頁無文字層(影像 PDF)→ OCR 排隊")}}, {"file": "MS-1590.pdf", "parts": {"首頁": ("GREEN", "")}}])
    _c2 = completion(1, 17, 18, False, {"c1": {"RED": 1}}, [])
    chk("⓪ v0218 完成判定:全過 + 影像 PDF 待 OCR → %s(黃 %d · 例外 %s)· 退步 / 交互驗證不一致 / 驗收紅 → %s(紅 %d)· U/I 面板 %s" % (_c1["verdict"], _c1["yellow"], _c1["exceptions"], _c2["verdict"], _c2["red"], "VRN-2 完成判定" in _completion_html(_c1)),
        _c1["verdict"] == "完成" and _c1["exceptions"] == ["MQ-1560.pdf"] and _c2["verdict"] == "未完成" and _c2["red"] == 4 and "完成判定" in _completion_html(_c2))
    _fz = {"id": "P3·F·01·TB", "kind": "表", "rows": [["", "2022", "2023"], ["Revenue", "1,021,435", ",163,923"], ["Gross profit", "80,111", "84,370"], ["Gross margin", "7.8", "7.2"]]}
    _o7, _b7, _d7 = _acc_calc([_fz])
    chk("⓪ v0220 數字斷裂:「,163,923」不當數字(_acc_dec → %s)· 不再算出 84,370 ÷ 163,923 = 51%% 的誤導重算(%d 過 %d 不符)" % (_acc_dec(",163,923"), _o7, _b7),
        _acc_dec(",163,923") is None and _acc_dec("1,163,923") is not None and _b7 == 0)
    chk("⓪ v0222 驗收鎖校正:上輪標題「Sachs I Research」→ 橫幅假綠 %s · 正常標題「What's Next?」不是 %s" % (bool(_ACC_BANNER.match("Sachs I Research")), bool(_ACC_BANNER.match("What's Next? Business Extension to Power AI"))),
        bool(_ACC_BANNER.match("Sachs I Research")) and not _ACC_BANNER.match("What's Next? Business Extension to Power AI"))
    _mqz = [{"kind": "表", "engine": "rapidocr(表格重建 · 欄右緣對齊)", "rows": [["Year end", "2025A", "2026E", "2027E", "2028E"], ["Revenue(m)", "8,149", "10,591", "13,127", "15,192"],
             ["Revenue growth (%)", "16.1", "30.0", "23.9", "15.7"], ["EPSrep(TWD)", "9.3", "13.7", "19.3", "24.4"], ["EPS rep growth(%)", "30.5", "47.8", "40.3", "26.8"], ["PERrep(x)", "69.3", "46.9", "33.4", "26.4"]]}]
    _xn, _xo, _xt = _acc_ocr_xcheck(_mqz)
    _bad = [dict(_mqz[0], rows=[r if r[0] != "Revenue(m)" else ["Revenue(m)", "8,149", "16,591", "13,127", "15,192"] for r in _mqz[0]["rows"]])]
    _bn, _bo, _ = _acc_ocr_xcheck(_bad)
    chk("⓪ v0225 OCR 算術交叉驗證(MQ 實數):%d/%d 通過 · OCR 讀錯一格(10,591 → 16,591)→ %d/%d · 上輪重點含免責句 = 假綠 %s" % (_xo, _xn, _bo, _bn, bool(re.search(_ACC_DISCL, "本刊所刊載之內容僅做為參考"))),
        _xn >= 9 and _xo == _xn and _bo < _bn and bool(re.search(_ACC_DISCL, "本刊所刊載之內容僅做為參考")) and not re.search(_ACC_DISCL, "營收年增 25%"))
    _bt = {"id": "P5·F·01·TB", "kind": "表", "rows": [["NT$百萬", "Dec-23A", "Dec-24A"], ["資產總額", "87,799", "91,247"], ["負債總額", "42,803", "38,851"], ["股東權益總額", "44,996", "52,397"]]}
    _bo, _bb, _bd = _acc_calc([_bt])
    _bt2 = {"id": "P5·F·02·TB", "kind": "表", "rows": [["", "2023", "2024"], ["Total assets", "1,000", "1,200"], ["Total liabilities", "600", "700"], ["Total equity", "350", "500"]]}
    _co, _cb, _cd = _acc_calc([_bt2])
    _ra, _rb = _bi_read("Derrick Yang\nD errick.Yang@morganstanley.com +886 2 2730-2862 04 25-07 25-10 2"), _bi_read("Derrick.Yang@morganstanley.com +886 2 2730-2862")
    _cf = _bi_cmp(_bi_read("Tommy.Lai@kgi.com")["email"], _bi_read("mmy.Lai@kgi.com")["email"])
    _cx = _bi_cmp(_bi_read("allen.chang@gs.com")["email"], _bi_read("chao.wang@gs.com")["email"])
    chk("⓪ v0226 向 VRN-1 學:資產恆等式 凱基慧洋 %d 過(資產 87,799 = 42,803 + 44,996)· 不平衡判黃 %s · 雙讀 字距拆斷修復 %s · 圖表日期軸不當電話 %s · 一致 %s · 截斷 tommy/mmy %s · 不同人仍衝突 %s" % (
        _bo, [d[:20] for d in _cd], _ra["email"], _ra["tel"], _bi_cmp(_ra["email"], _rb["email"])[0], _cf[0], _cx[0]),
        _bo == 2 and _bb == 0 and _cb == 0 and any(d.startswith("〔原文恆等式〕") for d in _cd) and _ra["email"] == ["derrick.yang@morganstanley.com"] and _ra["tel"] == ["27302862"]
        and _bi_cmp(_ra["email"], _rb["email"])[0] == "VERIFIED" and _cf[0] == "VERIFIED" and _cx[0] == "CONFLICT")
    _r0 = {"file": "GS-2317 20251205.pdf", "pages": [{"pno": 1, "zones": [{"minor": "TX", "records": [{"text": "Hon Hai (2317.TW): Nov Rev +26% YoY; Buy (on CL)"}], "rows": []}]},
           {"pno": 4, "zones": [{"minor": "TB", "engine": "pdfplumber(填色框表格重建 · 期間欄對齊)", "id": "P4·F·05·TB", "rows": [["", "12/24", "12/25E"], ["EPS (NT$)", "10.79", "14.37"]]}]}]}
    _s0 = [{"stock": True, "file": "GS-2317 20251205.pdf", "ticker": "2317", "date": "2025-12-05", "broker": "Goldman Sachs", "parts": {"年度財報": ("GREEN", "")}}]
    _a0 = [{"file": "GS-2317 20251205.pdf", "c5": ("GREEN", ""), "summary": {"title": "Hon Hai (2317.TW): Nov Rev", "points": [{"text": "a"}, {"text": "b"}, {"text": "c"}, {"text": "d"}]},
            "metrics": {"target": "400.00", "current": "231.00", "upside": "73.2"}, "basic": {"analysts": ["Allen Chang"], "email_a": ["allen.k.chang@gs.com"], "email": ["VERIFIED", ""], "tel": ["VERIFIED", "1/1"]}}]
    import tempfile as _tf
    _td = Path(_tf.mkdtemp())
    _bk, _fd, _sm, _gp, _mk = _out_books([_r0], _a0, _s0, _td)
    chk("⓪ v0227 輸出冊:基本資料 %s · 年度數據 %s · 缺項 %s · 檔 %s" % ({k: _bk[0][k] for k in ("TICKER", "YFINANCE_TICKER", "ENGLISH_NAME", "RATING", "TARGET_PRICE")}, [(x["ITEM"], x["PERIOD"], x["VALUE"]) for x in _fd], _gp, sorted(p.name for p in (_td / "output").iterdir())[:3]),
        _bk[0]["YFINANCE_TICKER"] == "2317.TW" and _bk[0]["ENGLISH_NAME"] == "Hon Hai" and _bk[0]["RATING"] == "Buy" and _bk[0]["TARGET_PRICE"] == "400.00"
        and [(x["ITEM"], x["PERIOD"], x["VALUE"]) for x in _fd] == [("EPS (NT$)", "12/24", "10.79"), ("EPS (NT$)", "12/25E", "14.37")] and not _gp and (_td / "output" / "VRN2_BasicInfo_latest.csv").exists())
    _rt0 = {"file": "a.pdf", "pages": [{"pno": 1, "zones": [{"engine": "pdfplumber"}]}]}
    _rt1 = {"file": "b.pdf", "pages": [{"pno": 1, "zones": [{"engine": "pdfplumber"}, {"engine": "pypdfium2(逐格換)"}]}]}
    _rt2 = {"file": "c.pdf", "pages": [{"pno": 1, "zones": [{"engine": "rapidocr(200dpi)"}]}]}
    _rt4 = {"file": "d.pdf", "reasons": ["首頁無文字層 → OCR 排隊"], "pages": [{"pno": 1, "zones": []}]}
    _ft, _fc, _fl, _fz = _funnel([_rt0, _rt1, _rt2, _rt4], {"funnel": {"ocr_min_conf": 0.9}})
    _ob = _opbar_html(Path("/tmp"))
    chk("⓪ v0228 調節輪:%s · 燈 %s · SSOT 門檻帶入 %s · 操作列 %s" % (dict(_fc), _fz[0], "0.90" in _fl, all(k in _ob for k in ("via://VRN2/run", "複製執行指令"))),
        dict(_fc) == {"T0": 1, "T1": 1, "T2": 1, "T4": 1} and _fz[0] == "YELLOW" and "0.90" in _fl and "via://VRN2/run" in _ob and "複製執行指令" in _ob)
    _em = _bi_read("helen.chien@daiwacm-\ncathay.com.tw")["email"]
    _bad6933 = {"id": "P8·F·02·TB", "kind": "表", "rows": [["", "2020", "2021"], ["資產總額", "-25,152", "263,760"], ["負債總額", "-19,614", "249,706"], ["權益總額", "-0.54", "6.90"]]}
    _o6, _b6, _d6 = _acc_calc([_bad6933])
    chk("⓪ v0229 第 35 輪:Email 跨行接回 %s · 6933 假恆等式不比 %s · 完成判定寫出退步檔 %s" % (_em, not any("恆等式" in d for d in _d6), "Citi" in completion(1, 1, 1, False, {}, [], regress_names="Citi-3231(沒找到財報頁)")["items"][0]["detail"]),
        _em == ["helen.chien@daiwacm-cathay.com.tw"] and not any("恆等式" in d for d in _d6) and "Citi" in completion(1, 1, 1, False, {}, [], regress_names="Citi-3231(沒找到財報頁)")["items"][0]["detail"])
    print("[計] VRN-2 SystemManager v0229(VRN_SystemManager_v0229.py)自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
