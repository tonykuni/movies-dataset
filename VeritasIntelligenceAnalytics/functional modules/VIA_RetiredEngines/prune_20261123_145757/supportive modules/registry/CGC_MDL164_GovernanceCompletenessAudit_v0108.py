#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
v0107→v0108(批619 工作站實錄:同一棵樹,容器 RED 0、工作站 **RED 41**)
  操作員逐字稿:`(夾 58 · GREEN 5 · RED 41 · UNKEPT 11 · NODATA 1)`。
  容器同一支引擎同一棵樹跑出來是 `GREEN 46 · RED 0`。**一棵樹不會有兩個真相**,
  所以紅的是尺,不是樹。根因:`_sha256()` 讀的是**原始位元組**,而 Windows 上
  git 依 `core.autocrlf` 把 LF 換成 CRLF——同一個檔多出「行數」個位元組,sha 當然不符。
  `.gitattributes` 目前只對 VTR / VIA_Canonical_Units / VRN SSOT / VIA_Governance_Runtime
  四棵子樹寫了 `-text`(理由欄寫得很清楚:「manifest hashes raw bytes」),
  **`references/intake/**` 不在裡面**。
  而這件事 CGC_MDL159 在**批546 就解過**(檢⑪「行尾無關」,raw 不符就比 LF 正規化後的),
  只是那個修法沒有被帶過來——**一個病根修在一支引擎上,不叫修好**。
  v0108:raw 不符時再比 CRLF→LF 正規化的 sha;對得上就判 **EOL**(只差行尾,不算正本被動過),
  對不上才是 RED。四態變五態,tally 加總照樣等於夾數(LL112 分子分母同源)。
  **不代改 .gitattributes**:那一行會讓操作員下次 checkout 重新正規化一整片檔,
  是他的手;引擎這邊先把假紅停掉,根治那一行由他裁定。

v0106→v0107(批595 操作員令「25 個沒有 manifest 的收容夾補起來」)
  `intake` 閘的解析器兩處放寬:①認 `sha256` + **`source`** 的寫法(本樹有兩夾是這種,
  第一版認不得,於是它們落在 NODATA 裡——**NODATA 有一部分是尺不認得,不是樹沒有**);
  ②認批595 的基線冊 schema,**空夾的 `files` 是 `{}` 也算查過**——空不等於沒查過。
  補冊由 `SUP_MDL754_VIAIntakeBaseline` 另一支做:本閘是**唯讀稽核**(檢①就是零寫入倉),
  **尺不寫字,寫字的另外一支**。實測 58 夾:GREEN 23→**46** · RED 0 · UNKEPT 10→12 · **NODATA 25→0**。

CGC_MDL164_GovernanceCompletenessAudit v0100 — 制度健全度稽核(批574)

操作員令(批574):貼進一份 VIA Central Governance 的 **14 庫 + 3 自適應機制** 制度藍圖,
問「**檢查我們制度健全了嗎 不足補之**」。

【這一支怎麼判「健全」——三個條件缺一不可】
  一本冊子存在,不等於制度存在。本器對每一庫問三件事,三件都過才算 GREEN:
    ① **冊在嗎**(找得到正本檔)
    ② **有料嗎**(不是空殼)
    ③ **有活讀者嗎**(活樹上**真的有引擎在讀它**)
  第三件是關鍵:**沒有任何引擎讀的冊,不是治理,只是一個檔案**。
  這種冊本器判 **ORPHAN(孤兒冊)**——不是紅燈(它沒壞),但它也沒在治理任何東西,
  而且最危險:看起來制度很完整,實際上沒有人在執行。

【誠實五態】
  GREEN 冊在+有料+有活讀者 · ORPHAN 冊在有料但**零活讀者** · NODATA 冊在但空
  · ABSENT 冊不在 · PARTIAL 多本候選只湊齊一部分

【紀律】零網路 · 零寫入 · 沒有 --apply(本器只判定,補不補是操作員的裁定)。
        判定一律**指到檔案**:說「有」就要說得出在哪一個檔、幾筆、誰在讀。

用法:
  via-govaudit intake    收容正本零觸碰:逐夾比 sha(批594)
  via-govaudit audit     14 庫 + 4 自適應機制逐條判(批587:第 4 = VIA Essentia 能力精粹)
  via-govaudit plan      只列不健全的,附「怎麼補」
  via-govaudit spec      印出藍圖本身(操作員批574 原文)
  via-govaudit --selftest
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
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "govaudit"
SKIP = ("__pycache__", "VIA_RetiredEngines", "references/intake", "SCOPE_COPY", "node_modules",
        "VIA_Reports/")

# ── 操作員批574 藍圖:14 庫 ────────────────────────────────────────────
#   (id, 中文名, 一句話職責, 候選正本 glob(可多), 這一庫的「有料」門檻)
LIBRARIES = [
    ("policy", "政策庫", "自動化驗證規則 · 合規條件 · 安全紅線",
     ["supportive modules/registry/VIA_Policy_Laws_SSOT_v*.json"], 20),
    ("params", "參數庫", "全域與模組參數配置;防硬編碼與設定飄移",
     ["supportive modules/registry/VIA_Central_Params_SSOT_v*.json"], 3),
    ("regex", "REGEX 規則庫", "全系統字串匹配規則(代號格式/字尾對應)",
     # 批581:拆掉 VIA_Central_Synonym_Regex ——它是**同義字庫**的正本,
     # 兩本鍵零重疊、頂層綱要也不同(這裡是 total_patterns/zone_stat,那裡是 policy/regex/synonyms)。
     # 掛在這裡只是讓它被數成「多冊並存」,不是真的有兩本 REGEX 冊。
     ["supportive modules/registry/VIA_SSOT_RegexDict_v*.json"], 3),
    ("synonym", "同義字管理庫", "多源異質資料的詞彙對齊與欄位別名映射",
     # 批581:拆掉 VRN_FieldRules_SSOT ——那是 VRN **研報六欄規則**的正本
     # (頂層鍵 batch/canonical_source/owner/rules/why),跟同義字零重疊。
     ["supportive modules/registry/VIA_Central_Synonym_Regex_v*.json"], 3),
    ("logic", "邏輯庫", "可重用業務計算邏輯與公式,標準化調用",
     ["supportive modules/registry/VIA_Lib_Registry_v*.json"], 3),
    ("factor", "因子庫", "量化 · 籌碼 · 財務特徵工程的計算因子",
     ["supportive modules/registry/VIA_Feature_Catalog_v*.json"], 3),
    ("managed_mod", "納管模組庫", "通過審計 · 具模型卡的合格組件",
     ["supportive modules/registry/VIA_Component_Inventory_SSOT_v*.json"], 100),
    ("used_mod", "已用模組庫", "各管線**實際調用**的模組清單(影響分析/版本追溯)",
     # 批581:拆掉 VIA_Engine_Consolidation_Register ——那是**引擎合併候選冊**
     # (頂層鍵 candidates/groups/n_unused/never_touch),不是「用過哪些模組」。
     ["supportive modules/registry/VIA_Unified_Register_v*.json"], 3),
    ("template", "報表模板與視覺資產庫", "統一 Header / 配色 / 圖標 / 報表樣板",
     ["supportive modules/registry/VIA_UI_TemplateSSOT_v*.json",
      "supportive modules/registry/VIA_Brand_SSOT_v*.json"], 3),
    ("workflow", "工作流與任務排程庫", "Stage-Gate 執行順序 · 觸發條件 · 階段閘",
     ["supportive modules/registry/VIA_Workflow_SSOT_v*.json"], 3),
    ("endpoint", "外部端點與 API 路由庫", "官方 API 連接點 · 頻率限制 · 路由規則",
     # 批581:拆掉 VDF_ENG046_FetchMatrixRegistry.py ——**引擎不是冊**。
     # 另:v0100 已退役(逐鍵驗證 92/92 零遺失),尾版律本來就只認 v0101。
     ["supportive modules/registry/VIA_NetGate_Wiring_Register_v*.json"], 3),
    ("database", "資料庫", "結構化/非結構化儲存中心(DuckDB 湖 · 原子化 JSON)",
     ["supportive modules/registry/VIA_DB_Table_SSOT_v*.json",
      "supportive modules/registry/VIA_DataHome_SSOT_v*.json"], 10),
    ("audit_ledger", "審計帳本庫", "產物推廣與註冊表突變的不可篡改日誌",
     ["supportive modules/registry/VIA_AutoCode_Registry_v*.json"], 100),
    ("exception", "異常與修復日誌庫", "錯誤軌跡 · PS AST 自動修復紀錄",
     ["supportive modules/registry/VIA_Problem_Ledger_v*.json"], 3),
]

#: 批581:**一庫兩冊分工**——同一個庫底下兩本各管一半,不是競爭的兩個正本。
#: 這種不該被算成「多冊並存」,更不該刪掉任何一本。
COMPLEMENTARY = {
    "template": ("VIA_UI_TemplateSSOT 管報表樣板 · VIA_Brand_SSOT 管品牌視覺資產"
                 "——庫名本來就是「報表模板**與視覺資產**庫」,兩本各管一半"),
    "database": ("VIA_DB_Table_SSOT 管**有哪些表** · VIA_DataHome_SSOT 管**庫放在哪**"
                 "——一個是綱要一個是位置,兩本各管一半"),
}

# ── 藍圖:自適應機制(批574 原文 3 個;批587 操作員令 +VIA Essentia = 4 個)(不是冊,是**機制**,所以驗的是「有沒有引擎在做」)──
#   (id, 中文名, 一句話, 證據:活樹上必須存在的引擎家族 glob)
ADAPTIVE = [
    ("iface", "INTERFACE 自適應快速對接", "動態綱要推斷 + 隨插即用註冊(秒級對接)",
     ["supportive modules/registry/VIA_Interface_Contract_Registry_v*.json",
      "supportive modules/registry/CGC_MDL*Iface*.py", "supportive modules/registry/CGC_MDL136_*.py"]),
    ("reconcile", "上下交互 / 向下核對", "SSOT 向下約束 + 底層向上回報,雙向交叉比對",
     ["supportive modules/registry/CGC_MDL149_*.py", "supportive modules/registry/CGC_MDL150_*.py"]),
    ("contract", "合約自適應", "欄位微幅改名時自動對齊 + 合約變更入帳本",
     ["supportive modules/registry/VIA_Engine_Contract_v*.json",
      "supportive modules/70_VRN_Rules/SUP_MDL749_*.py",
      "supportive modules/registry/VIA_Interface_Contract_Registry_v*.json"]),
    # 批587 操作員令「這個系統導入了嗎 · 用 VIA 為開頭給他一個商業化名稱 · 註冊導入獨立功能」。
    # 量出來的實況:PEIS 的技術面早就在位(收容正本 / via-peis 短令 / 自測格站 / 政策 SSOT /
    # 台帳 / 元件編號冊 30 筆),**但在這份治理藍圖上完全不存在**——中央盤點制度健全度時,
    # 它根本不在被盤點的名單上。那不叫導入,那叫「跑得起來但沒人管」。
    # 它也只有技術代號(「PEIS 能力引擎掛線口」),沒有名字。零件編號不是一個功能。
    # 本批給它名字(**VIA Essentia · 能力精粹核**)並列為第 4 自適應機制,從此進盤點。
    ("essentia", "VIA Essentia 能力精粹", "同一件事的 N 份實作聚成一個能力 + 發能力卡(AI 讀卡不讀全文)",
     # 承載件**不列收容正本**:`references/intake` 在本閘的 SKIP 裡(正本零觸碰),
     # 列了就永遠有一件「不在」→ 永遠 PARTIAL。**判錯的黃燈跟判錯的紅燈一樣傷。**
     # 收容正本在不在,由 MDL161 檢①②③ 逐檔 sha256 驗;這裡驗的是**活樹上有沒有人在做**。
     ["supportive modules/registry/VIA_Essentia_Product_SSOT_v*.json",
      "supportive modules/registry/CGC_MDL161_PEISCapabilityEngine_v*.py",
      "supportive modules/registry/CGC_MDL064_SelftestGrid_v*.py"]),
]

#: 產品身分正本:一個功能要能被叫出名字,才算是一個功能。
ESSENTIA_SSOT = "VIA_Essentia_Product_SSOT_v*.json"


def _live_files() -> list:
    out = []
    for ext in ("*.py", "*.ps1"):
        for p in VIA.rglob(ext):
            s = str(p).replace("\\", "/")
            if any(k in s for k in SKIP):
                continue
            out.append(p)
    return out


_CACHE = {"files": None, "text": {}}


_SELF_FAMILY = Path(__file__).stem.rsplit("_v", 1)[0]


def _readers(name: str, exclude: Path | None = None) -> list:
    """活樹上**真的提到這個檔名**的引擎(=有人在讀它)。零命中=孤兒冊。"""
    if _CACHE["files"] is None:
        _CACHE["files"] = _live_files()
    stem = re.sub(r"_v\d+(?=\.)", "_v*", name)          # 版號無關
    key = re.escape(name.rsplit("_v", 1)[0])
    rx = re.compile(key)
    hits = []
    for p in _CACHE["files"]:
        if exclude and p == exclude:
            continue
        if p.stem.rsplit("_v", 1)[0] == _SELF_FAMILY:   # 不把自己算成讀者
            # 批578:要排除的是**整個家族**,不是這一支檔。
            # v0100 只排掉 __file__,所以我一開 v0101,舊的 v0100 就變成每一本冊的「第二讀者」
            # ——單一讀者 3 本當場變 0,**數字自己變好看了**。自我指涉會偽造改善。
            continue
        t = _CACHE["text"].get(p)
        if t is None:
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                t = ""
            _CACHE["text"][p] = t
        if rx.search(t):
            hits.append(p.stem.rsplit("_v", 1)[0])
    return sorted(set(hits))


def _entries(p: Path) -> int:
    """冊裡有幾筆(json:最大的那個 list/dict;py:視為 1 支引擎)。"""
    if p.suffix == ".py":
        return 1
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return -1
    if isinstance(d, list):
        return len(d)
    return max([len(v) for v in d.values() if isinstance(v, (list, dict))] or [0])


def audit() -> dict:
    rows = []
    for lid, zh, why, globs, floor in LIBRARIES:
        # 逐 glob 記命中,**不要只數檔**:
        #   第一版我寫 `len(found) < len(globs)`,一個 glob 命中兩檔就能掩蓋另一個 glob 命中零檔,
        #   於是「候選兩本只有一本在」照樣判 GREEN——假綠。改成逐 glob 看有沒有命中。
        by_glob, found = {}, []
        for g in globs:
            hits = [f for f in sorted(VIA.glob(g))
                    if not any(k in str(f).replace("\\", "/") for k in SKIP)]
            by_glob[g] = [str(f.relative_to(VIA)) for f in hits]
            found += hits
        miss_globs = [g for g, h in by_glob.items() if not h]
        if not found:
            rows.append({"kind": "庫", "id": lid, "zh": zh, "why": why, "state": "ABSENT",
                         "files": [], "entries": 0, "readers": [],
                         "note": "找不到正本冊(候選 glob:" + " · ".join(globs) + ")"})
            continue
        best = max(found, key=lambda f: (_entries(f), f.name))
        n = _entries(best)
        rd = _readers(best.name, exclude=best)
        if n < 0:
            st, note = "NODATA", "冊在但讀不出內容(格式壞?)"
        elif n < floor:
            st, note = "NODATA", f"冊在但只有 {n} 筆(門檻 {floor})=空殼"
        elif not rd:
            st, note = "ORPHAN", "**零活讀者**:冊在、有料,但活樹上沒有任何引擎讀它=不是治理,是一個檔案"
        else:
            st, note = "GREEN", ""
            # **深度**:綠了不代表穩。只有一支引擎讀的冊,刪掉那一支就變孤兒;
            #   名實不符(冊名說的事跟內容不是同一件)更會讓人以為驗過了。兩者都標出來,但不改燈號
            #   ——它們沒壞,只是**薄**。把薄的講白,比多一盞紅燈有用。
            if len(rd) == 1:
                note = f"**單一讀者**({rd[0]}):那一支一動,這本冊就變孤兒"
        if miss_globs and st == "GREEN":
            st, note = "PARTIAL", ("候選 " + str(len(globs)) + " 件有 " + str(len(miss_globs)) +
                                   " 件不在:" + " · ".join(miss_globs))
        rows.append({"kind": "庫", "id": lid, "zh": zh, "why": why, "state": st,
                     "files": [str(f.relative_to(VIA)) for f in found], "primary": str(best.relative_to(VIA)),
                     "by_glob": by_glob, "miss_globs": miss_globs,
                     "entries": n, "readers": rd[:8], "n_readers": len(rd), "note": note})

    for aid, zh, why, globs in ADAPTIVE:
        by_glob, found = {}, []
        for g in globs:
            hits = [f for f in sorted(VIA.glob(g))
                    if not any(k in str(f).replace("\\", "/") for k in SKIP)]
            by_glob[g] = [str(f.relative_to(VIA)) for f in hits]
            found += hits
        miss_globs = [g for g, h in by_glob.items() if not h]
        if not found:
            st, note = "ABSENT", "機制沒有任何承載件(候選:" + " · ".join(globs) + ")"
        elif miss_globs:
            st, note = "PARTIAL", ("承載件 " + str(len(globs)) + " 件有 " + str(len(miss_globs)) +
                                   " 件不在:" + " · ".join(miss_globs))
        else:
            st, note = "GREEN", ""
        rows.append({"kind": "機制", "id": aid, "zh": zh, "why": why, "state": st,
                     "files": [str(f.relative_to(VIA)) for f in found][:4],
                     "by_glob": by_glob, "miss_globs": miss_globs,
                     "entries": len(found), "readers": [], "n_readers": 0, "note": note})

    t = {k: sum(1 for r in rows if r["state"] == k)
         for k in ("GREEN", "PARTIAL", "ORPHAN", "NODATA", "ABSENT")}
    sole = [r["zh"] for r in rows if r["kind"] == "庫" and r.get("n_readers") == 1]
    # 雙冊:同一件事有兩本候選都在,而**主本比副本薄**——那通常代表真相其實在副本那邊
    twin = []
    for r in rows:
        if r["kind"] != "庫" or len(r.get("files", [])) < 2:
            continue
        others = [f for f in r["files"] if f != r.get("primary")]
        twin.append({"zh": r["zh"], "primary": r.get("primary"), "others": others,
                     "why": "同一件事有多本冊並存;哪一本是正本要由操作員裁定(LL90)"})
    return {"state": "OK" if not t["ABSENT"] else "NODATA",
            "n": len(rows), "n_lib": len(LIBRARIES), "n_adaptive": len(ADAPTIVE),
            "tally": t, "sole_reader": sole, "twin_books": twin, "rows": rows,
            "note": ("ORPHAN=冊在有料但零活讀者。**它不是紅燈(沒壞),但它也沒在治理任何東西**——"
                     "而且最危險:看起來制度完整,實際上沒人在執行")}


def _top(p: Path) -> list:
    """頂層鍵(看一眼就知道兩本是不是同一種東西)。"""
    if p.suffix == ".py":
        return ["<py>"]
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return ["<讀不出>"]
    return sorted(map(str, d.keys()))[:8] if isinstance(d, dict) else [f"<list:{len(d)}>"]


def _keys(p: Path) -> set:
    """冊裡「有哪些條目」的鍵集合。dict→最大那層的鍵;list→逐筆取 id/name/key。

    拿來做兩本冊的**交集/差集**——「哪一本是正本」操作員要看的是這個,
    不是兩個筆數(40 筆 vs 12 筆看不出誰蓋得住誰)。
    """
    if p.suffix == ".py":
        return set()
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return set()
    if isinstance(d, list):
        return {str(x.get("id") or x.get("name") or x.get("key") or i)
                for i, x in enumerate(d) if isinstance(x, dict)}
    best, keys = -1, set()
    for v in d.values():
        if isinstance(v, dict) and len(v) > best:
            best, keys = len(v), set(map(str, v.keys()))
        elif isinstance(v, list) and len(v) > best:
            best = len(v)
            keys = {str(x.get("id") or x.get("name") or x.get("key") or i)
                    for i, x in enumerate(v) if isinstance(x, dict)}
    return keys


def books() -> dict:
    """批578:**多冊並存**逐處攤開,給操作員一眼能裁定的對照表。

    本器**不裁定**(LL90 同義的裁定權在操作員),只把四件事擺出來:
      ① 各本幾筆 ② 鍵的交集與各自獨有 ③ 誰在讀哪一本 ④ 誰比較新
    再加一句白話結論(例如「主冊被另一本完全包住」=正本可能選錯了)。
    """
    a = audit()
    pairs, singles = [], []
    for r in a["rows"]:
        if r.get("kind") != "庫":
            continue
        files = [VIA / x for x in r.get("files", [])]
        if r.get("n_readers") == 1:
            singles.append({"zh": r["zh"], "book": r.get("files", [""])[0],
                            "reader": r["readers"][0], "entries": r.get("entries")})
        if len(files) < 2:
            continue
        main = VIA / r.get("primary", r["files"][0])       # 主 = 稽核判定的正本(不是 glob 順序)
        others = [f for f in files if f != main]
        mk, mn = _keys(main), _entries(main)
        for o in others:
            ok, on = _keys(o), _entries(o)
            only_m, only_o, both = mk - ok, ok - mk, mk & ok
            if not mk and not ok:
                verdict = "兩本都不是鍵值冊(或讀不出鍵),要靠人看內容"
            elif mk and not only_m:
                verdict = "**主冊被另一本完全包住**——正本可能選錯了(另一本才是全集)"
            elif ok and not only_o:
                verdict = "另一本是主冊的子集——併回主冊後可退役"
            elif not both:
                verdict = ("**兩本的鍵沒有任何重疊**——很可能根本是兩件不同的冊,"
                           "而不是同一本的兩個版本。請確認它們該不該掛在同一個庫名下;"
                           "若是兩件事,那這一處就不是『多冊並存』,是**名冊分類錯了**")
            else:
                verdict = f"兩邊各有獨有鍵(主 {len(only_m)} · 另 {len(only_o)})——要逐鍵裁定"
            kind_ = ("分工" if r["id"] in COMPLEMENTARY
                     else ("真並存" if both else "分類錯"))
            if kind_ == "分工":
                verdict = "**一庫兩冊分工,不是並存**:" + COMPLEMENTARY[r["id"]]
            pairs.append({
                "zh": r["zh"], "pair_kind": kind_,
                "main": str(main.relative_to(VIA)).replace("\\", "/"),
                "other": str(o.relative_to(VIA)).replace("\\", "/"),
                "main_entries": mn, "other_entries": on,
                "both": len(both), "only_main": sorted(only_m)[:8], "only_other": sorted(only_o)[:8],
                "n_only_main": len(only_m), "n_only_other": len(only_o),
                "main_readers": _readers(main.name, exclude=main)[:6],
                "other_readers": _readers(o.name, exclude=o)[:6],
                "newer": ("主" if main.stat().st_mtime >= o.stat().st_mtime else "另"),
                "main_top": _top(main), "other_top": _top(o),
                "verdict": verdict,
            })
    real = [p for p in pairs if p["pair_kind"] == "真並存"]
    return {"state": "OK", "n_pairs": len(pairs), "n_real": len(real),
            "n_split": sum(1 for p in pairs if p["pair_kind"] == "分工"),
            "n_misfiled": sum(1 for p in pairs if p["pair_kind"] == "分類錯"),
            "n_libs": len({p["zh"] for p in pairs}),      # 庫數(有幾個庫是多冊)
            "n_single_reader": len(singles),
            "pairs": pairs, "single_reader": singles,
            "note": ("批581 分三類:**真並存**(鍵有重疊=同一件事兩個版本,要裁定)· "
                     "**分工**(一庫兩冊各管一半,本來就該並存)· "
                     "**分類錯**(鍵零重疊=根本是兩本不同的冊,掛錯庫了)。"
                     "沒有寫入旗標,不改任何冊。")}


# ── 批579:自我指涉閘(LL133 的系統化落地)──────────────────────────────────
#: 「在回答『誰引用 X』」的判定器,如果沒有把**自己的家族**排掉,
#: 只要它的說明文字或設定表提到 X,它就會把自己算成引用者。
#: 批578 在 MDL164 自己身上就是這樣:一開 v0101,舊的 v0100 變成每本冊的第二讀者,
#: 「單一讀者 3 本」當場變 0 ——**版本號造出來的假進步**。
_SR_SCAN = re.compile(r"rglob\(\s*[\"']\*\.py[\"']|glob\(\s*[\"']\*\*/\*\.py[\"']"
                      r"|_live_files\(|_live_tail_py\(|py_files\(")
_SR_ANSWER = re.compile(r"\breaders?\b|\bowners?\b|\bcallers?\b|referenc|used_by|\bmention"
                        r"|讀者|呼叫者|引用")
_SR_GENERIC = re.compile(r"_SELF_FAMILY|stem\.rsplit\(\s*[\"']_v[\"']\s*,\s*1\s*\)\[0\]\s*==")
#: WEAK_SELF 要的是「**在掃描迴圈裡**用 __file__ 把自己跳過」,
#: 不是「檔案裡出現 __file__ 這個字」——批579 第一版就是後者,
#: 於是把 MDL157 拿 __file__ 解版號、MDL158 在自測裡拿 __file__ 當樣本,都誤判成 WEAK_SELF。
#: **判錯的狀態和判錯的紅燈一樣傷。**
_SR_WEAK = re.compile(r"==\s*Path\(__file__\)(?:\.name)?[\s\S]{0,120}?\bcontinue\b"
                      r"|Path\(__file__\)(?:\.name)?\s*==[\s\S]{0,120}?\bcontinue\b")

#: 批579 現況基線(**棘輪**):名單內的是既有債,列成待辦;
#: 名單**之外**再冒出一支沒排自己的引用判定器 = 紅燈。新寫的一律要排自己。
SELFREF_BASELINE = {
    "VIA_SYSTEM_MANAGER", "CGC_MDL069_SystemManager", "CGC_MDL075_CentralGov",
    "CGC_MDL092_ConsolidationAudit", "CGC_MDL106_GovConsole", "CGC_MDL115_SSOTRegexDict",
    "CGC_MDL124_BridgeSweeper", "CGC_MDL135_EnvGovernance", "CGC_MDL148_EngineBus",
    "CGC_MDL153_WorkflowComposer", "CGC_MDL156_VIAAcceleratorControl",
    "via_bridge_sweeper", "via_central_gov",
    "CGC_MDL157_VIAUniqueEntryControl", "CGC_MDL158_VIAPanoramaAuditRepair",
}


# ────────────────────── 批594:收容正本零觸碰閘 ──────────────────────
#: 批594 我自己踩的:寫遷移腳本時掃 `functional modules/VRN` **沒帶排除清單**,
#: 當場改到 `references/intake/GenericLayoutEngine_.../generic_layout_engine.py`
#: ——**收容正本**。還原了,但這件事不該靠我記得,要有閘。
#: 這一支逐夾比 sha:對得上=GREEN、對不上=RED 並指名、沒有可用的 sha=**NODATA 並指名**
#: (沒有 manifest 的夾**不算綠**——假的綠跟假的紅一樣傷)。
import hashlib as _hl

_MF_GLOBS = ("_INTAKE_MANIFEST*.json", "_INTAKE_BASELINE_b*.json",
             "*manifest*.json", "*MANIFEST*.json", "manifest.json")


def _sha256(p: Path) -> str:
    h = _hl.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _sha256_lf(p: Path) -> str:
    """CRLF→LF 正規化後的 sha(批619;CGC_MDL159 批546 同一個修法,這裡是把它帶過來)。
    只用在 raw 已經不符的時候——**先信原始位元組,正規化是第二問,不是第一問**。"""
    h = _hl.sha256()
    h.update(p.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def _manifest_pairs(mf: Path, root: Path) -> list:
    """manifest → [(檔案, 期望 sha)]。本樹有好幾種寫法,認得的才回,認不得就回空(NODATA)。"""
    try:
        j = json.loads(mf.read_text(encoding="utf-8"))
    except Exception:
        return []
    out = []
    files = j.get("files")
    if isinstance(files, dict):                      # {path: sha} 或 {path: {sha256: …}}
        for k, v in files.items():
            s = v.get("sha256") if isinstance(v, dict) else v
            if isinstance(s, str) and len(s) >= 32:
                out.append((root / k, s.lower()))
    elif isinstance(files, list):                    # [{path, sha256}, …]
        for it in files:
            if isinstance(it, dict) and isinstance(it.get("sha256"), str):
                nm = it.get("path") or it.get("name") or it.get("file")
                if nm:
                    out.append((root / nm, it["sha256"].lower()))
    # 批595:本樹還有兩夾是 `sha256` + **`source`**(不是 `source_path`)的寫法,
    # 第一版認不得,於是它們落在 NODATA 裡——**NODATA 的有一半是尺不認得,不是樹沒有**。
    s1, sp = (j.get("sha256"),
              j.get("source_path") or j.get("source") or j.get("file") or j.get("name"))
    if isinstance(s1, str) and len(s1) >= 32 and sp:
        # L71 跨作業系統同解律——**我自己又踩一次**:`source_path` 多半是操作員工作站的
        # Windows 絕對路徑(`C:\Users\...\x.json`),在 Linux 上 `Path(...).name` 會回整串,
        # 於是每一夾都判「檔案不見了」=假紅。比對前先把分隔符正規化。
        nm = str(sp).replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
        if nm:
            out.append((root / nm, s1.lower()))
    return out


def intake(root: Path | None = None) -> dict:
    """收容正本零觸碰:逐夾比 sha。**沒有可用 sha 的夾不算綠,誠實 NODATA 並指名。**

    批619:`root` 只給自測用——沒有沙盒就只能拿實樹當證據,
    而實樹在容器裡全是 LF,永遠證不出 CRLF 那條路走不走得通(L83:半條路不算跑過)。"""
    base = root or VIA
    rows = []
    for d in sorted(base.rglob("references/intake/*")):
        if not d.is_dir() or "__pycache__" in str(d):
            continue
        pairs = []
        for g in _MF_GLOBS:
            for mf in sorted(d.glob(g)):
                pairs += _manifest_pairs(mf, d)
            if pairs:
                break
        rel = str(d.relative_to(base)).replace("\\", "/")
        if not pairs:
            # 批595 的基線冊:空夾的 `files` 是 `{}`,沒有 pair 可比,但它**查過了**。
            # 判成 NODATA 等於說「沒查過」——空不等於沒查過。
            if any(json.loads(mf.read_text(encoding="utf-8")).get("schema")
                   == "VIA.Intake.Baseline.v1"
                   for mf in d.glob("_INTAKE_BASELINE_b*.json")):
                rows.append({"dir": rel, "n": 0, "state": "GREEN",
                             "changed": [], "missing": []})
                continue
            rows.append({"dir": rel, "state": "NODATA",
                         "why": "沒有 manifest,或 manifest 裡沒有認得的 sha 寫法"})
            continue
        bad, gone, eol = [], [], []
        for f, want in pairs:
            if not f.is_file():
                gone.append(f.name)
            elif _sha256(f) == want:
                continue
            elif _sha256_lf(f) == want:
                # 批619:只差行尾。Windows 的 core.autocrlf 幹的,不是人動的。
                # 判紅會讓 41 個夾同時亮紅燈——那不是警報,那是噪音,而且會淹掉真的紅。
                eol.append(f.name)
            else:
                bad.append(f.name)
        # **RED 只留給「檔案在、sha 對不上」**——那才叫正本被改。
        # 檔案不在(多半是操作員上傳的 .zip 原件解開後沒留)是另一回事:
        # 那是 manifest 與樹的記帳落差,不是有人動了正本。混成同一盞紅=判錯的紅燈。
        # 次序就是嚴重度:真被動過 > 原件沒留 > 只差行尾 > 全同。
        st = ("RED" if bad else "UNKEPT" if gone else "EOL" if eol else "GREEN")
        rows.append({"dir": rel, "n": len(pairs), "state": st,
                     "changed": bad[:6], "missing": gone[:6], "eol": eol[:6],
                     "n_eol": len(eol)})
    tal = {k: sum(1 for r in rows if r["state"] == k)
           for k in ("GREEN", "RED", "UNKEPT", "EOL", "NODATA")}
    red = [r for r in rows if r["state"] == "RED"]
    return {"state": "OK" if not red else "FAIL", "tally": tal, "dirs": len(rows),
            "red": red[:20], "nodata": [r["dir"] for r in rows if r["state"] == "NODATA"][:20],
            "eol": [{"dir": r["dir"], "n": r.get("n_eol", 0)}
                    for r in rows if r["state"] == "EOL"][:20],
            "unkept": [{"dir": r["dir"], "missing": r["missing"]}
                       for r in rows if r["state"] == "UNKEPT"][:20],
            "why": ("收容正本零觸碰。**RED 只給「檔案在、sha 對不上」**——那才叫正本被改;"
                    "UNKEPT 是原件(多半是上傳的 .zip)解開後沒留,是記帳落差不是有人動正本;"
                    "EOL 是**只差行尾**(Windows core.autocrlf 把 LF 換 CRLF,raw sha 自然不符),"
                    "CRLF→LF 正規化後對得上就不算正本被動過(批619;CGC_MDL159 批546 同一個修法);"
                    "NODATA 是沒有可比的 sha,**不算綠**(LL138:假的綠跟假的零同一件事)。")}


def selfref() -> dict:
    """掃尾版活檔,找「在回答『誰引用 X』卻沒把自己家族排掉」的判定器。

    三態(**NO_EXCLUDE 不等於一定壞**,所以不直接判紅,走棘輪):
      SAFE        排掉整個家族(泛用寫法或自家族字面)
      WEAK_SELF   只排掉 `__file__` 這一支——一開新版號,舊版就變成引用者(批578 實例)
      NO_EXCLUDE  完全沒排自己
    """
    # 尾版律(L68:分母不得把同一件事數很多遍)——舊版也會命中,
    # 不套尾版律會量出 130 支,其中一百多支是同一支引擎的歷史版號。
    fam_: dict = {}
    for q in _live_files():
        # 「未納管暫存區」不進分母(具名豁免;L68 要有理由):
        # new modules engines/ 是還沒進 supportive/functional 的件,它們還不是活引擎。
        if q.suffix != ".py" or "new modules engines" in str(q).replace("\\", "/"):
            continue
        fam_.setdefault(str(q.parent) + "/" + re.sub(r"_v\d{4}\.py$", "", q.name), []).append(q)
    rows = []
    for p in [sorted(v, key=lambda x: x.name)[-1] for v in fam_.values()]:
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if not _SR_SCAN.search(txt) or not _SR_ANSWER.search(txt):
            continue
        myfam = re.sub(r"_v\d{4}$", "", p.stem)
        lit = re.compile(r"startswith\(\s*[\"']" + re.escape(myfam[:18]))
        st = ("SAFE" if (_SR_GENERIC.search(txt) or lit.search(txt))
              else ("WEAK_SELF" if _SR_WEAK.search(txt) else "NO_EXCLUDE"))
        rows.append({"family": myfam, "file": str(p.relative_to(VIA)).replace("\\", "/"),
                     "state": st, "in_baseline": myfam in SELFREF_BASELINE})
    rows.sort(key=lambda r: (r["state"] != "SAFE", r["family"]))
    news = [r for r in rows if r["state"] != "SAFE" and not r["in_baseline"]]
    tally = {k: sum(1 for r in rows if r["state"] == k) for k in ("SAFE", "WEAK_SELF", "NO_EXCLUDE")}
    return {"state": "OK" if not news else "FAIL", "n": len(rows), "tally": tally,
            "rows": rows, "new_offenders": news,
            "note": ("NO_EXCLUDE 本身**不等於一定壞**——只有當它的說明文字或設定表提到它在數的那個名字時"
                     "才會自己算自己。所以走**棘輪**:基線內的是既有債(逐支改),"
                     "基線外再冒出一支 = 紅燈。新寫的判定器一律要排掉自己的家族(LL133)。")}


def plan() -> dict:
    a = audit()
    todo = [r for r in a["rows"] if r["state"] != "GREEN"]
    for r in todo:
        if r["state"] == "ABSENT":
            r["fix"] = "先立冊(或指認既有檔當正本);立完要有引擎讀它,否則只是多一個孤兒"
        elif r["state"] == "ORPHAN":
            r["fix"] = "**接線**:讓至少一支活引擎讀它,並把「讀不到就誠實 ABSENT」寫進那支引擎"
        elif r["state"] == "NODATA":
            r["fix"] = "冊在但空/壞:先補內容或修格式,再談接線"
        else:
            r["fix"] = "候選件只湊齊一部分:把缺的那幾件補上或從候選裡拿掉(不要留著假裝有)"
    return {"state": "OK", "n_total": a["n"], "n_todo": len(todo), "tally": a["tally"],
            "todo": todo, "note": "本器只判定;補不補、怎麼補是操作員的裁定(沒有 --apply)"}


def write_out(name: str, payload) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    p = REPORTS / name
    p.write_text(payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    return p


def _no_apply_flag() -> bool:
    """本器沒有寫入旗標。

    要檢查「原始碼裡沒有某個字」,**檢查句本身不能把那個字寫進去**——
    批578 這一批已經被自我指涉咬過三次(MDL160 的 owner、MDL164 的 readers、還有這裡),
    所以這個字用組的,不直接出現在檔案裡。
    """
    needle = "add_argument(" + chr(34) + "--" + "app" + "ly" + chr(34)
    return needle not in Path(__file__).read_text(encoding="utf-8")


def selftest() -> int:
    n, fails = [0], []

    def chk(name, ok, note=""):
        n[0] += 1
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    print(f"=== CGC_MDL164 制度健全度稽核 v{VERSION} · 自測(零網路;零寫入) ===")
    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("① 零網路 · 零寫入倉 · 沒有 --apply(只判定,補不補是操作員的裁定)",
        not any(k in code for k in ("import requests", "import httpx", "import urllib"))
        and '"--apply"' not in code and "'--apply'" not in code)
    chk("② 藍圖 14 庫 + 4 機制(批574 原文 3 機制;批587 操作員令把 VIA Essentia 列為第 4)",
        len(LIBRARIES) == 14 and len(ADAPTIVE) == 4
        and [m[0] for m in ADAPTIVE][-1] == "essentia",
        f"庫 {len(LIBRARIES)} · 機制 {len(ADAPTIVE)} · {[m[0] for m in ADAPTIVE]}")
    _ess = sorted(HERE.glob(ESSENTIA_SSOT))
    _ej = {}
    if _ess:
        try:
            _ej = json.loads(_ess[-1].read_text(encoding="utf-8"))
        except Exception:
            _ej = {}
    _pr, _eng = _ej.get("product") or {}, _ej.get("engine") or {}
    _entry_hits = sorted(HERE.glob(_eng.get("entry", "___none___")))
    chk("②之二 產品身分正本在位:一個功能要叫得出名字才算一個功能(名稱 · 一句話 · 動詞 · 保證 · 引擎指得到尾版)",
        bool(_ess) and _pr.get("name", "").startswith("VIA ") and bool(_pr.get("name_zh"))
        and len(_ej.get("verbs") or []) >= 5 and len(_ej.get("guarantees") or []) >= 5
        and bool(_entry_hits),
        f"({_pr.get('name', '無')} / {_pr.get('name_zh', '')} · 動詞 {len(_ej.get('verbs') or [])} · "
        f"保證 {len(_ej.get('guarantees') or [])} · 引擎尾版 {_entry_hits[-1].name if _entry_hits else '指不到'})")

    _ik = intake()
    chk("②之三 **收容正本零觸碰閘**:逐夾比 sha;沒有可用 sha 的夾誠實 NODATA 不算綠"
        "(批594 我自己踩的——遷移腳本掃 VRN 沒帶排除清單,當場改到收容正本)",
        _ik.get("state") in ("OK", "FAIL") and _ik.get("dirs", 0) > 0
        and sum(_ik["tally"].values()) == _ik["dirs"]
        and all(not r.get("changed") for r in _ik.get("unkept", [])),
        f"(夾 {_ik.get('dirs')} · GREEN {_ik['tally']['GREEN']} · RED {_ik['tally']['RED']} · "
        f"UNKEPT {_ik['tally']['UNKEPT']} · EOL {_ik['tally']['EOL']} · "
        f"NODATA {_ik['tally']['NODATA']})")

    # ②之四 批619:CRLF 不是汙染。工作站 RED 41 / 容器 RED 0 是同一棵樹——
    #   一棵樹不會有兩個真相,所以紅的是尺。沙盒把三條路都走一次:
    #   原樣=GREEN · 只換行尾=EOL(不是紅)· 真的改字=RED。
    import tempfile as _tf
    with _tf.TemporaryDirectory() as _td:
        _sb = Path(_td)
        _body = b"alpha\nbeta\ngamma\n"
        _want = _hl.sha256(_body).hexdigest()

        def _mk(name: str, data: bytes):
            _dd = _sb / "references" / "intake" / name
            _dd.mkdir(parents=True)
            (_dd / "x.py").write_bytes(data)
            (_dd / "_INTAKE_MANIFEST.json").write_text(
                json.dumps({"files": {"x.py": _want}}), encoding="utf-8")

        _mk("same", _body)
        _mk("crlf", _body.replace(b"\n", b"\r\n"))
        _mk("real", b"alpha\nbeta\nDELTA\n")
        _r = intake(_sb)
        _t = _r["tally"]
        chk("②之四 **CRLF 不算正本被動過**(批619:工作站 RED 41 vs 容器 RED 0,"
            "紅的是尺不是樹;CGC_MDL159 批546 早就解過,只是沒帶過來)",
            _t["GREEN"] == 1 and _t["EOL"] == 1 and _t["RED"] == 1
            and _r["state"] == "FAIL" and _r["red"][0]["dir"].endswith("real"),
            f"(原樣 GREEN {_t['GREEN']} · 只換行尾 EOL {_t['EOL']}(不是紅)· "
            f"真的改字 RED {_t['RED']})")

    chk("③ 每一庫都寫得出一句話職責與候選正本(不能只有名字)",
        all(len(w) >= 6 and g for _i, _z, w, g, _f in LIBRARIES))

    a = audit()
    chk("④ 判定到每一列都指得到檔(說「有」就要說得出在哪)",
        all(r["files"] or r["state"] == "ABSENT" for r in a["rows"]),
        f"{a['n']} 列")
    chk("⑤ 三個條件缺一不可:冊在 · 有料 · **有活讀者**(第三件是 ORPHAN 的判準)",
        "ORPHAN" in code and "零活讀者" in code
        and all(("n_readers" in r) for r in a["rows"] if r["kind"] == "庫"))
    g = [r for r in a["rows"] if r["state"] == "GREEN" and r["kind"] == "庫"]
    chk("⑥ 判 GREEN 的庫,每一本都真的有活讀者(綠燈不是免費的)",
        all(r["n_readers"] >= 1 for r in g), f"GREEN 庫 {len(g)} 本")
    chk("⑦ 讀者掃描不把自己算成讀者(不然每一本都會假綠)",
        "不把自己算成讀者" in code and Path(__file__).name not in str(
            [r["readers"] for r in a["rows"]]))
    chk("⑧ 四態齊全且加總等於列數(分子分母同源;LL112)",
        sum(a["tally"].values()) == a["n"], str(a["tally"]))
    p = plan()
    chk("⑨ plan 只列不健全的,而且每一列都講得出怎麼補",
        p["n_todo"] == a["n"] - a["tally"]["GREEN"] and all("fix" in r for r in p["todo"]))
    chk("⑩ ORPHAN 明講「不是紅燈但也沒在治理」(最危險的那一種要講白)",
        "不是紅燈" in a["note"] and "沒人在執行" in a["note"])
    chk("⑪ PARTIAL 比的是**逐 glob 有沒有命中**,不是檔數(第一版比檔數=一個 glob 兩檔掩蓋另一個零檔的假綠)",
        "miss_globs" in code and "不要只數檔" in code
        and all("by_glob" in r for r in a["rows"]))
    chk("⑫ 深度指標:單一讀者與多冊並存都要點名(綠燈不代表穩;薄要講白)",
        "sole_reader" in a and "twin_books" in a
        and all(("單一讀者" in r["note"]) for r in a["rows"]
                if r["kind"] == "庫" and r.get("n_readers") == 1),
        f"單一讀者 {len(a.get('sole_reader', []))} 本 · 多冊並存 {len(a.get('twin_books', []))} 處")
    b = books()
    chk("⑭ books 把多冊並存逐處攤開:主/另 各幾筆 · 共有鍵 · 各自獨有 · 誰讀誰 · 誰較新 · 一句可裁定的結論",
        b["state"] == "OK" and b["n_pairs"] >= 1
        and all(set(p) >= {"main", "other", "both", "n_only_main", "n_only_other",
                           "main_readers", "other_readers", "newer", "verdict",
                           "main_top", "other_top"} for p in b["pairs"]),
        f"(多冊並存 {b['n_libs']} 個庫 / {b['n_pairs']} 組對照 · 單一讀者 {b['n_single_reader']} 本)")
    chk("⑮ 自我指涉排除的是**整個家族**,不是這一支檔——"
        "否則一開新版號,舊版就變成每一本冊的第二讀者,單一讀者當場歸零(**數字自己變好看**)",
        _SELF_FAMILY == Path(__file__).stem.rsplit("_v", 1)[0]
        and not any(r.startswith(_SELF_FAMILY)
                    for row in audit()["rows"] for r in row.get("readers", [])),
        f"(自家族 {_SELF_FAMILY})")
    chk("⑯ books 只攤開不裁定:無 --apply,且結論句一律以「請確認 / 要逐鍵裁定 / 可退役」收尾,"
        "不替操作員決定哪一本是正本(LL90)",
        _no_apply_flag() and all(p["verdict"] for p in b["pairs"]))
    sr = selfref()
    _b = books()
    chk("⑲ 批581 操作員令「找到真的、刪掉舊的」落地:**真並存 = 0**"
        "(舊本已退役;分類錯的候選已拆;剩下的都是一庫兩冊分工)",
        _b["n_real"] == 0 and _b["n_misfiled"] == 0,
        f"(真並存 {_b['n_real']} · 分工 {_b['n_split']} · 分類錯 {_b['n_misfiled']})")
    chk("⑳ 退役不是硬刪:退役夾有 manifest,逐本記 sha256 · 逐鍵零遺失的證明 · 復原指令",
        (VIA / "VIA_RetiredEngines/batch581_dupbooks/manifest.json").is_file()
        and all(k in json.loads((VIA / "VIA_RetiredEngines/batch581_dupbooks/manifest.json")
                                .read_text(encoding="utf-8"))["items"][0]
                for k in ("sha256", "proof", "live_readers", "restore")))
    chk("⑰ 自我指涉閘(LL133 棘輪):基線外不得再冒出「回答誰引用卻沒排掉自己家族」的判定器",
        sr["state"] == "OK",
        f"(共 {sr['n']} 支 · SAFE {sr['tally']['SAFE']} · WEAK_SELF {sr['tally']['WEAK_SELF']} · "
        f"NO_EXCLUDE {sr['tally']['NO_EXCLUDE']} · 基線外 {len(sr['new_offenders'])})")
    chk("⑱ 偵測器自己必須是 SAFE(否則它就是在示範反例)",
        any(r["family"] == _SELF_FAMILY and r["state"] == "SAFE" for r in sr["rows"]),
        f"({_SELF_FAMILY})")
    chk("⑬ 帶加速器橋(MDL156 覆蓋閘)", "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="CGC_MDL164_GovernanceCompletenessAudit",
                                 description="制度健全度稽核(零網路;零寫入)")
    ap.add_argument("verb", nargs="?", default="audit", choices=["audit", "plan", "spec", "books", "selfref", "intake"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.verb == "spec":
        print(f"[CGC_MDL164 v{VERSION}] 制度藍圖(操作員批574 原文)· {len(LIBRARIES)} 庫 + {len(ADAPTIVE)} 機制")
        for i, (lid, zh, why, _g, _f) in enumerate(LIBRARIES, 1):
            print(f"  {i:>2}. [庫  ] {zh:<14} {why}")
        for i, (aid, zh, why, _g) in enumerate(ADAPTIVE, 1):
            print(f"   {i}. [機制] {zh:<14} {why}")
        return 0
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    r = ({"audit": audit, "books": books, "selfref": selfref}.get(a.verb) or plan)()
    write_out(f"GOVAUDIT_{a.verb.upper()}_{ts}.json", r)
    write_out(f"GOVAUDIT_{a.verb.upper()}_latest.json", r)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
        return 0
    if a.verb == "intake":
        r = intake()
        tl = r["tally"]
        print(f"[CGC_MDL164 v{VERSION}] intake · 收容夾 {r['dirs']} · "
              f"GREEN {tl['GREEN']} · **RED {tl['RED']}** · UNKEPT {tl['UNKEPT']} · "
              f"EOL {tl['EOL']} · NODATA {tl['NODATA']}")
        for x in r.get("eol", []):
            print(f"  [EOL   ] {x['dir']} · {x['n']} 件只差行尾(core.autocrlf;不算正本被動過)")
        print(f"  {r['why']}")
        for x in r["red"]:
            print(f"  [RED   ] {x['dir']}")
            if x.get("changed"):
                print(f"           被改過:{', '.join(x['changed'])}")
            if x.get("missing"):
                print(f"           不見了:{', '.join(x['missing'])}")
        for x in r.get("unkept", []):
            print(f"  [UNKEPT] {x['dir']}  原件沒留:{', '.join(x['missing'])}")
        for d0 in r["nodata"]:
            print(f"  [NODATA] {d0}  沒有可比的 sha —— **不算綠**")
        return 0 if r["state"] == "OK" else 1
    if a.verb == "selfref":
        tl = r["tally"]
        print(f"[CGC_MDL164 v{VERSION}] selfref · 在回答「誰引用」的判定器 {r['n']} 支 · "
              f"SAFE {tl['SAFE']} · WEAK_SELF {tl['WEAK_SELF']} · NO_EXCLUDE {tl['NO_EXCLUDE']}")
        print("  " + r["note"] + "\n")
        for x in r["rows"]:
            if x["state"] == "SAFE":
                continue
            tag = "既有債" if x["in_baseline"] else "**新增!**"
            print(f"  [{x['state']:<10}] {tag:<8} {x['file']}")
        if r["new_offenders"]:
            print(f"\n  **基線外新增 {len(r['new_offenders'])} 支** —— 新寫的判定器一律要排掉自己的家族(LL133)")
        else:
            print("\n  基線外 0 支(棘輪守住了)")
        return 0
    if a.verb == "books":
        print(f"[CGC_MDL164 v{VERSION}] books · **真並存 {r['n_real']}** · 分工 {r['n_split']} · "
              f"分類錯 {r['n_misfiled']} · 單一讀者 {r['n_single_reader']} 本")
        print("  " + r["note"] + "\n")
        for p in r["pairs"]:
            print(f"  [{p['zh']}]  較新={p['newer']}")
            print(f"     主 {p['main']}  {p['main_entries']} 筆 · 讀者 {', '.join(p['main_readers']) or '無'}")
            print(f"        頂層鍵 {p['main_top']}")
            print(f"     另 {p['other']}  {p['other_entries']} 筆 · 讀者 {', '.join(p['other_readers']) or '無'}")
            print(f"        頂層鍵 {p['other_top']}")
            print(f"     共有鍵 {p['both']} · 主獨有 {p['n_only_main']} · 另獨有 {p['n_only_other']}")
            print(f"     → {p['verdict']}\n")
        if r["single_reader"]:
            print("  [單一讀者](那一支引擎一動,這本冊就變孤兒)")
            for s in r["single_reader"]:
                print(f"     {s['zh']:<16} {s['entries']} 筆 · 唯一讀者 {s['reader']}")
                print("        補法二選一:讓第二支**真的**去讀它(不是為了湊數字掛一行 import),"
                      "或承認它是那一支的私有設定、從治理冊降級。**哪一種是操作員的判斷。**")
        return 0
    if a.verb == "audit":
        t = r["tally"]
        print(f"[CGC_MDL164 v{VERSION}] audit · {r['n_lib']} 庫 + {r['n_adaptive']} 機制")
        print(f"  GREEN {t['GREEN']} · PARTIAL {t['PARTIAL']} · **ORPHAN {t['ORPHAN']}** "
              f"· NODATA {t['NODATA']} · ABSENT {t['ABSENT']}")
        print("")
        for x in r["rows"]:
            head = f"  [{x['state']:<7}] {x['kind']} {x['zh']:<20}"
            tail = (f"{x['entries']:>6} 筆 · 讀者 {x['n_readers']}" if x["kind"] == "庫"
                    else f"承載件 {x['entries']}")
            print(head + tail)
            print(f"            {x.get('primary') or (x['files'][0] if x['files'] else '—')}")
            if x["readers"]:
                print(f"            讀者:{' · '.join(x['readers'][:5])}")
            if x["note"]:
                print(f"            {x['note']}")
        if r.get("sole_reader"):
            print(f"\n  [深度] **單一讀者** {len(r['sole_reader'])} 本:{' · '.join(r['sole_reader'])}")
            print("         綠燈是真的,但那一支引擎一動,這幾本就變孤兒。")
        if r.get("twin_books"):
            # 批582:批581 之後這兩處已經判定是**分工**(各管一半),不是要裁定的並存;
            # 深度行原本沿用舊措辭「多冊並存…操作員裁定」,與 books 三分類不一致=同一件事兩種說法。
            print(f"  [深度] **一庫兩冊(分工,不是並存)** {len(r['twin_books'])} 處 —— "
                  f"詳見 `books`(真並存 / 分工 / 分類錯 三分類):")
            for x in r["twin_books"]:
                print(f"         {x['zh']}:主 {x['primary']}")
                for o in x["others"]:
                    print(f"                  另 {o}")
        print(f"\n  註:{r['note']}")
    else:
        print(f"[CGC_MDL164 v{VERSION}] plan · 共 {r['n_total']} 項 · **待補 {r['n_todo']}**")
        for x in r["todo"]:
            print(f"  [{x['state']:<7}] {x['zh']:<20} {x['note']}")
            print(f"            → {x['fix']}")
        print(f"  註:{r['note']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
