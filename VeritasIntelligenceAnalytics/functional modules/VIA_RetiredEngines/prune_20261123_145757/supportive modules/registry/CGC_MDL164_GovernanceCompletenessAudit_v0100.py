#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
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
  via-govaudit audit     14 庫 + 3 自適應機制逐條判
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
     ["supportive modules/registry/VIA_SSOT_RegexDict_v*.json",
      "supportive modules/registry/VIA_Central_Synonym_Regex_v*.json"], 3),
    ("synonym", "同義字管理庫", "多源異質資料的詞彙對齊與欄位別名映射",
     ["supportive modules/registry/VRN_FieldRules_SSOT_v*.json",
      "supportive modules/registry/VIA_Central_Synonym_Regex_v*.json"], 3),
    ("logic", "邏輯庫", "可重用業務計算邏輯與公式,標準化調用",
     ["supportive modules/registry/VIA_Lib_Registry_v*.json"], 3),
    ("factor", "因子庫", "量化 · 籌碼 · 財務特徵工程的計算因子",
     ["supportive modules/registry/VIA_Feature_Catalog_v*.json"], 3),
    ("managed_mod", "納管模組庫", "通過審計 · 具模型卡的合格組件",
     ["supportive modules/registry/VIA_Component_Inventory_SSOT_v*.json"], 100),
    ("used_mod", "已用模組庫", "各管線**實際調用**的模組清單(影響分析/版本追溯)",
     ["supportive modules/registry/VIA_Engine_Consolidation_Register_v*.json",
      "supportive modules/registry/VIA_Unified_Register_v*.json"], 3),
    ("template", "報表模板與視覺資產庫", "統一 Header / 配色 / 圖標 / 報表樣板",
     ["supportive modules/registry/VIA_UI_TemplateSSOT_v*.json",
      "supportive modules/registry/VIA_Brand_SSOT_v*.json"], 3),
    ("workflow", "工作流與任務排程庫", "Stage-Gate 執行順序 · 觸發條件 · 階段閘",
     ["supportive modules/registry/VIA_Workflow_SSOT_v*.json"], 3),
    ("endpoint", "外部端點與 API 路由庫", "官方 API 連接點 · 頻率限制 · 路由規則",
     ["functional modules/VDF/engine/VDF_ENG046_FetchMatrixRegistry*.py",
      "supportive modules/registry/VIA_NetGate_Wiring_Register_v*.json"], 3),
    ("database", "資料庫", "結構化/非結構化儲存中心(DuckDB 湖 · 原子化 JSON)",
     ["supportive modules/registry/VIA_DB_Table_SSOT_v*.json",
      "supportive modules/registry/VIA_DataHome_SSOT_v*.json"], 10),
    ("audit_ledger", "審計帳本庫", "產物推廣與註冊表突變的不可篡改日誌",
     ["supportive modules/registry/VIA_AutoCode_Registry_v*.json"], 100),
    ("exception", "異常與修復日誌庫", "錯誤軌跡 · PS AST 自動修復紀錄",
     ["supportive modules/registry/VIA_Problem_Ledger_v*.json"], 3),
]

# ── 操作員批574 藍圖:3 自適應機制(不是冊,是**機制**,所以驗的是「有沒有引擎在做」)──
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
]


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
        if p.name == Path(__file__).name:               # 不把自己算成讀者
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
    chk("② 藍圖 14 庫 + 3 機制,與操作員批574 原文對得上",
        len(LIBRARIES) == 14 and len(ADAPTIVE) == 3,
        f"庫 {len(LIBRARIES)} · 機制 {len(ADAPTIVE)}")
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
    chk("⑬ 帶加速器橋(MDL156 覆蓋閘)", "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="CGC_MDL164_GovernanceCompletenessAudit",
                                 description="制度健全度稽核(零網路;零寫入)")
    ap.add_argument("verb", nargs="?", default="audit", choices=["audit", "plan", "spec"])
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
    r = audit() if a.verb == "audit" else plan()
    write_out(f"GOVAUDIT_{a.verb.upper()}_{ts}.json", r)
    write_out(f"GOVAUDIT_{a.verb.upper()}_latest.json", r)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
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
            print(f"  [深度] **多冊並存** {len(r['twin_books'])} 處(哪一本是正本=操作員裁定,LL90):")
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
