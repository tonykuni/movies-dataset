#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL227_ConsoleBlueprint v0100 — 三家族主控台藍圖引擎(左面板參數輸入 · 右面板多分頁總覽 · 對接制式 U/I 與 synchronizer)
v0100→v0101(側線 2026-09-28;操作員令「資料庫管理優化 P1+P2 開工」):接上 VIA_DBManager(CGC_MDL228)——左面板多一個 DB 家族(庫 → 表 → 欄 → 期間 → 格式 → 指令,經 via-vcgc dbm export,先乾跑);右面板多「資料庫」分頁(正庫 / 對帳副本總表 · 數量核對 · 三項儲存計畫);矩陣多一本「資料庫數量核對」。資料只讀 DataHome 一頁目錄,不掃庫。其餘一字不動(v0100 留作版史 L04)。

操作員 2026-09-28 令:「VCGC/VDF/VRN 左面板參數輸入,右面板多元展示為主、少量功能;多 TAB;所有矩陣狀況、邏輯規範、
引擎總攬、運作摘要、錯誤摘要放 TAB 1,結果往後放;第一頁儘量視覺化、現代但專業;把這些參數與介面生成一個引擎收集相關需求,
與存檔的標準可調 HTML U/I 快速對接 synchronizer。」

這一支只做三件事,全部唯讀收集、不跑任何引擎、不碰網路、不裝套件:
  ① 收集(collect):左面板的參數**只從** VIA_InputConsole_Spec 來(家族 → 群組 → 項目 → 參數種類 · 預設值);
     引擎在不在、實際會跑哪一句**只從** CGC_MDL148 EngineBus 尾版的 catalog() / call(apply=False) 來(PLAN,不動手);
     矩陣 · 律條 · 邏輯層 · 鎖冊 · 成功冊 · 基線冊讀樹上既有 JSON 冊;已修冊的尾版憑據委派 CGC_MDL158 尾版 _verify_one;
     引擎盤點委派 VIA_SYSTEM_MANAGER 尾版 do_list;運作摘要讀最近一次 CGC_MDL064 格子證據(GRID_*.json)。
     本支不另立第二把尺(L05):量不到就照實報 NODATA / ABSENT,不當綠(L16)。
  ② 藍圖(blueprint):把收到的需求寫成一本宣告式藍圖 JSON —— 左面板(家族 · 群組 · 項目 · 控制項)+ 右面板六分頁
     (① 總覽 ② 矩陣 ③ 邏輯規範 ④ 引擎 ⑤ 錯誤與待辦 ⑥ 執行結果;結果放最後)。頁面只照藍圖畫。
  ③ 對接(dock):制式 U/I(VIA_HTML_UI:launcher / centralUI / synchronizer 三入口)的**原文一個位元組都不動**,
     另寫一份副本,插入三段:synchronizer 模組冊預置(借 VRN_ENG089 尾版的 PRESEED 契約與 DEFAULT_MODULES 抽取,不另寫一份)·
     中央頁外掛(VIA_REGISTER_ADDON:KPI 卡 + 開全頁主控台)· synchronizer 外掛(VIA_REGISTER_SYNC_ADDON:狀態 + 下載藍圖)。
     模組在 synchronizer 開 / 關 / 釘選,中央頁即時跟著變(BroadcastChannel via.sync.v2)。

產出一律在 VIA_Reports/console_blueprint/(再生件,永不 commit)。
用法:
  python CGC_MDL227_ConsoleBlueprint_v0100.py build [--out 夾] [--no-dock] [--template-root 夾]
  python CGC_MDL227_ConsoleBlueprint_v0100.py blueprint        # 只收集,印摘要(零寫檔)
  python CGC_MDL227_ConsoleBlueprint_v0100.py status           # 最近一版還對嗎(OK / STALE / NONE;零寫檔)
  python CGC_MDL227_ConsoleBlueprint_v0100.py --selftest       # 沙盒自測(只寫暫存夾)
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

import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
ENGINE_TAG = "CGC_MDL227_ConsoleBlueprint v" + VERSION
SPEC = HERE / "VIA_InputConsole_Spec_v0100.json"
BOOKS = {
    "laws": HERE / "VIA_Policy_Laws_SSOT_v0100.json",
    "logic": HERE / "VIA_VRN_LogicArchitecture_SSOT_v0100.json",
    "lock": HERE / "VIA_VCGC_CloseoutLock_v0100.json",
    "ledger": HERE / "VIA_VCGC_SuccessLedger_v0100.json",
    "fixed": HERE / "VIA_PanoramaFixed_SSOT_v0100.json",
    "celeritas": HERE / "VIA_CeleritasPolicy_Baseline_v0100.json",
}
BOOK_ZH = {"spec": "參數冊 InputConsole", "laws": "政策律條冊", "logic": "VRN 邏輯架構冊", "lock": "收尾鎖冊",
           "ledger": "成功冊", "fixed": "已修冊", "celeritas": "Celeritas 基線冊", "bus": "引擎調度匯流排 MDL148",
           "panorama": "全景稽核 MDL158", "manager": "系統總管 do_list", "grid": "最近一次格子證據", "eng089": "VRN 模板 ENG089",
           "console": "輸入主控台 MDL139(參數翻譯正主)",
           "dbm": "資料庫中央管控 MDL228", "db_catalog": "資料家一頁目錄 DataHome"}
GRID_DIR = VIA / "VIA_Reports" / "selftest_runs"
OUT_DIR = VIA / "VIA_Reports" / "console_blueprint"
TEMPLATE_ROOT = VIA / "VIA_HTML_UI"
BLUEPRINT_NAME = "VIA_CONSOLE_BLUEPRINT.json"
PAGE_NAME = "VIA-Console-Blueprint.html"
ROLES = ("launcher", "centralUI", "synchronizer")
STATE_KEY = "via.sync.state.v2"
CHANNEL = "via.sync.v2"
MODULE = {"id": "vcgc-console-blueprint", "name": "VCGC/VDF/VRN 主控台藍圖", "type": "dashboard", "enabled": True,
          "pinned": True, "system": False,
          "note": "CGC_MDL227 外掛(上游:InputConsole 冊 · EngineBus 目錄 · 治理冊 · 最近一次格子)"}
#: (頁上鍵, 參數冊家族鍵, 中文)
FAMILIES = (("vcgc", "central", "VCGC 中央治理"), ("vdf", "vdf", "VDF 資料工廠"),
            ("vrn", "vrn", "VRN 研報鏈"), ("vap", "vap", "VAP 圖組"))
#: 右面板分頁:總覽第一、結果最後(操作員令)
TABS = (("overview", "總覽", "矩陣 · 邏輯規範 · 引擎總攬 · 運作摘要 · 錯誤摘要,一頁看"),
        ("matrix", "矩陣", "每一本治理矩陣逐列狀態"),
        ("logic", "邏輯規範", "政策律條(依位階)與 VRN 六層邏輯"),
        ("engines", "引擎", "參數冊每一項 → 尾版 → 在位 → 正主 MDL139 以冊上參數解析出會跑的那一句"),
        ("db", "資料庫", "正庫 / 對帳副本逐表現況 · 冊上期望 vs 實量核對 · 三項儲存計畫(只出計畫);資料只讀 DataHome 一頁目錄"),
        ("errors", "錯誤與待辦", "紅燈與待操作員裁定,逐條附來源"),
        ("results", "執行結果", "最近一次格子逐站結果"))
#: 參數種類 → 正主 CGC_MDL139.resolve_argv 讀的鍵與控制項。旗標怎麼寫(range 拆 --start/--end、codes 依 codes_style、
#: since_ym 截月、lanes → --lane …)一律由正主翻譯;本支只收值,不自己拼旗標(v0100 實測抓到自拼出 `--range`,ENG064 不認)。
#: 不在這張表的種類 = 正主不接 → 不給欄位,照實列出。
KIND_KEYS = {"range": (("start", "date"), ("end", "date")), "start": (("start", "date"),), "since": (("start", "date"),),
             "since_ym": (("start", "month"),), "days": (("days", "number"),), "codes": (("codes", "codes"),),
             "only": (("only", "text"), ("cats", "text")), "cats": (("cats", "text"),), "lanes": (("lanes", "text"),),
             "dir": (("dir", "dir"),), "code": (("code", "codes"),),
             "vapone": (("out", "dir"), ("formats", "text"), ("profile", "text"), ("config", "dir"), ("data", "dir"))}
KEY_HINT = {"end": "YYYY-MM-DD;留空 = 今天(正主規則)", "codes": "4~6 位代碼,逗號分隔(≤200);寫法依該項 codes_style",
            "lanes": "L1~L15,逗號分隔", "cats": "英文類別名,逗號分隔", "only": "FRED 序列代碼,逗號分隔;留空 = 依類別",
            "dir": "報告夾(留空 = 冊預設 ∪ incoming)", "code": "4~6 位代碼", "out": "輸出夾", "formats": "svg,html,png,pdf,plotly",
            "profile": "vap_spec_v1 | seaborn_stack_v23", "config": "stack config.json(--render 必填)", "data": "資料檔(選填)"}
SEVERITY = {"RED": 0, "AMBER": 1, "NODATA": 2, "ABSENT": 3, "GREEN": 4}


# ---------------------------------------------------------------- 讀檔(唯讀;四態照實)
def _rel(p) -> str:
    try:
        return Path(p).resolve().relative_to(VIA).as_posix()
    except (ValueError, OSError):
        return str(p)


def _read_json(path: Path) -> tuple:
    """回 (資料, 來源列)。不在 = ABSENT;讀不動 / 不是 JSON = UNREADABLE。不會拋。"""
    row = {"path": _rel(path), "state": "OK", "sha": "", "why": ""}
    try:
        raw = Path(path).read_bytes()
    except FileNotFoundError:
        row.update(state="ABSENT", why="檔不在")
        return None, row
    except OSError as exc:
        row.update(state="UNREADABLE", why=f"讀不動:{type(exc).__name__}")
        return None, row
    row["sha"] = hashlib.sha256(raw).hexdigest()[:16]
    try:
        return json.loads(raw.decode("utf-8-sig")), row
    except (ValueError, UnicodeError) as exc:
        row.update(state="UNREADABLE", why=f"不是 JSON:{type(exc).__name__}")
        return None, row


def _tail(folder: Path, glob: str):
    try:
        hits = sorted(p for p in Path(folder).glob(glob) if p.is_file())
    except OSError:
        return None
    return hits[-1] if hits else None


def _load(path, name: str):
    """載一支尾版模組(唯讀用途)。載不到回 (None, 原因)。"""
    if path is None:
        return None, "尾版不在"
    try:
        spec = importlib.util.spec_from_file_location(name, str(path))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception as exc:          # 別支的 import 期錯誤不拖垮收集:照實記
        sys.modules.pop(name, None)
        return None, f"{type(exc).__name__}: {str(exc)[:120]}"


def _src(sources: dict, key: str, row: dict) -> None:
    sources[key] = {"zh": BOOK_ZH.get(key, key), **row}


def _mod_row(path, err: str) -> dict:
    return {"path": _rel(path) if path else "", "state": "OK" if not err else ("ABSENT" if path is None else "UNREADABLE"),
            "sha": "", "why": err}


# ---------------------------------------------------------------- ① 收集
def _relargv(argv: list) -> list:
    return [("python" if i == 0 else _rel(a) if os.sep in str(a) and Path(str(a)).is_absolute() else str(a))
            for i, a in enumerate(argv or [])]


def collect_params(spec: dict | None, bus_rows: list | None, plan, resolver=None, eff_start=None) -> list:
    """參數冊 → 左面板。plan(id) = EngineBus PLAN;resolver(id) = 正主 MDL139 resolve_argv(冊上參數會跑的那一句);
    eff_start(id, group) = 正主 effective_start(起日的實際值,給欄位當提示)。三者缺席 = 照實 NODATA,不自己算。"""
    fams = []
    spec = spec or {}
    kinds = spec.get("param_kinds") or {}
    by_id = {r.get("id"): r for r in (bus_rows or [])}
    for key, skey, zh in FAMILIES:
        fam = (spec.get("families") or {}).get(skey)
        if not isinstance(fam, dict):
            fams.append({"key": key, "spec_key": skey, "zh": zh, "state": "ABSENT", "why": f"參數冊沒有 {skey} 家族",
                         "groups": [], "counts": {"items": 0, "in_place": 0, "net": 0}})
            continue
        groups, n_items, n_in, n_net = [], 0, 0, 0
        for g in fam.get("groups") or []:
            items = []
            for it in g.get("items") or []:
                iid = str(it.get("id") or "")
                bus = by_id.get(iid) or {}
                ctrls, seen, unsupported = [], set(), []
                for p in it.get("params") or []:
                    if p not in KIND_KEYS:
                        unsupported.append(p)
                        continue
                    for pkey, control in KIND_KEYS[p]:
                        if pkey in seen:
                            continue
                        seen.add(pkey)
                        ph = ""
                        if pkey == "start" and eff_start is not None:
                            try:
                                ph = eff_start(iid, g.get("id")) or "latest(引擎增量律,不帶旗標)"
                            except Exception:
                                ph = ""
                        elif pkey == "lanes":
                            ph = str(it.get("lanes_default") or "")
                        ctrls.append({"key": pkey, "kind": p, "control": control, "placeholder": ph,
                                      "hint": kinds.get(p, "") if pkey == "start" else KEY_HINT.get(pkey, kinds.get(p, ""))})
                pl = plan(iid) if bus else {}
                argv = _relargv(pl.get("argv"))
                rs = {}
                if resolver is not None:
                    try:
                        rs = resolver(iid) or {}
                    except Exception as exc:
                        rs = {"state": "UNREADABLE", "note": type(exc).__name__}
                in_place = bus.get("engine_state") == "在位"
                items.append({"id": iid, "zh": it.get("zh") or iid, "net": bool(it.get("net")),
                              "note": str(it.get("note") or "")[:160], "params": ctrls,
                              "engine": bus.get("engine") or "", "engine_glob": (it.get("engine") or {}).get("glob", ""),
                              "engine_state": "GREEN" if in_place else ("ABSENT" if bus else "NODATA"),
                              "engine_why": "" if bus else "匯流排目錄沒有這一項(或匯流排載不到)",
                              "versions": bus.get("versions") or 0, "outputs": list(it.get("outputs") or [])[:6],
                              "plan_argv": argv, "plan_state": pl.get("state") or ("NODATA" if not bus else ""),
                              "resolved_argv": _relargv(rs.get("argv")), "resolved_state": rs.get("state") or "NODATA",
                              "resolved_note": str(rs.get("note") or ("正主 MDL139 載不到" if resolver is None else ""))[:200],
                              "unsupported": unsupported})
                n_items += 1
                n_in += 1 if in_place else 0
                n_net += 1 if it.get("net") else 0
            groups.append({"id": g.get("id"), "zh": g.get("zh") or g.get("id"), "items": items})
        fams.append({"key": key, "spec_key": skey, "zh": zh, "state": "OK", "why": "", "groups": groups,
                     "counts": {"items": n_items, "in_place": n_in, "net": n_net}})
    return fams


def collect_inventory(manager) -> dict:
    """引擎盤點委派總管 do_list(同一把尺:總管頁的引擎 / 模組表也是它)。"""
    if manager is None:
        return {"state": "ABSENT", "why": "總管尾版載不到", "families": {}, "modules": 0}
    try:
        d = manager.do_list(do_print=False)
    except Exception as exc:
        return {"state": "UNREADABLE", "why": f"do_list 失敗:{type(exc).__name__}", "families": {}, "modules": 0}
    retire = getattr(manager, "RETIRE_SUBSYSTEM", "VIA_RetiredEngines")
    fam = {}
    for sub, rows in (d.get("engines") or {}).items():
        fam[sub] = {"count": len(rows or {}), "retired": sub == retire}
    return {"state": "OK", "why": "", "families": fam, "modules": len(d.get("mods") or {})}


def _worst(states: list) -> str:
    return min(states, key=lambda s: SEVERITY.get(s, 9)) if states else "NODATA"


def collect_matrices(books: dict, panorama, fams: list) -> list:
    mats = []
    # M1 已修冊:尾版憑據逐條複驗(委派全景 _verify_one);全樹掃描類照實 NODATA
    fx = books.get("fixed")
    rows = []
    for e in (fx or {}).get("entries") or []:
        vs = []
        notes = []
        for v in e.get("verify") or []:
            if v.get("kind") == "tail_contains" and panorama is not None:
                try:
                    st, msg = panorama._verify_one(v, {}, {})
                except Exception as exc:
                    st, msg = "UNREADABLE", type(exc).__name__
                vs.append("RED" if st == "RED" else "GREEN" if st == "GREEN" else "NODATA")
                notes.append(str(msg)[:120])
            elif v.get("kind") == "tail_contains":
                vs.append("ABSENT")
                notes.append("全景尾版載不到,量不了")
            else:
                vs.append("NODATA")
                notes.append(f"{v.get('kind')}:要全樹掃描才量得到(via-panorama scan),本頁不代跑")
        rows.append({"id": e.get("id"), "zh": str(e.get("title") or e.get("what") or e.get("id")),
                     "state": _worst(vs), "note": " · ".join(dict.fromkeys(notes))[:300]})
    mats.append({"id": "fixed", "zh": "已修冊複驗", "source": "fixed", "rows": rows,
                 "state": "ABSENT" if fx is None else _worst([r["state"] for r in rows])})
    # M2 收尾鎖冊
    lk = books.get("lock")
    rows = [{"id": r.get("id"), "zh": r.get("id"), "state": str(r.get("lamp") or "NODATA").upper(),
             "note": f"{r.get('env', '')} · {str(r.get('evidence') or '')[:200]}"} for r in (lk or {}).get("locked") or []]
    rows += [{"id": r.get("id"), "zh": r.get("id"), "state": "AMBER", "note": "候操作員:" + str(r.get("why") or "")[:220]}
             for r in (lk or {}).get("held") or []]
    mats.append({"id": "lock", "zh": "收尾鎖冊", "source": "lock", "rows": rows,
                 "state": "ABSENT" if lk is None else _worst([r["state"] for r in rows])})
    # M3 成功冊
    lg = books.get("ledger")
    rows = [{"id": r.get("id"), "zh": r.get("file") or r.get("id"), "state": "GREEN",
             "note": "封存" if r.get("sealed") else "保留"} for r in (lg or {}).get("kept") or []]
    rows += [{"id": r.get("id") if isinstance(r, dict) else str(r), "zh": "", "state": "AMBER",
              "note": "候:" + (str(r.get("why") or "") if isinstance(r, dict) else "")[:200]}
             for r in (lg or {}).get("held") or []]
    mats.append({"id": "ledger", "zh": "成功冊", "source": "ledger", "rows": rows,
                 "state": "ABSENT" if lg is None else _worst([r["state"] for r in rows])})
    # M4 Celeritas 基線(既有債是操作員的手:AMBER,不是 RED)
    cb = books.get("celeritas")
    rows = []
    if cb is not None:
        debt = cb.get("ps1_debt") or {}
        n_debt = debt.get("n") if isinstance(debt, dict) else len(debt)
        rows.append({"id": "ps1_debt", "zh": "PS 既有債(L70)", "state": "AMBER" if n_debt else "GREEN",
                     "note": f"{n_debt} 支;基線外新增的一支才算紅"})
        ro = cb.get("py_readonly") or {}
        n_ro = ro.get("n") if isinstance(ro, dict) and "n" in ro else len(ro.get("files") or ro) if ro else 0
        rows.append({"id": "py_readonly", "zh": "PY 正典唯讀本", "state": "GREEN", "note": f"{n_ro} 支(逐支指名鎖冊)"})
        imm = cb.get("immutable_b345") or {}
        rows.append({"id": "immutable_b345", "zh": "b345 正本", "state": "GREEN" if imm.get("retired_20260928") else "AMBER",
                     "note": "已退役裁定在冊" if imm.get("retired_20260928") else "候裁定"})
    mats.append({"id": "celeritas", "zh": "Celeritas 基線", "source": "celeritas", "rows": rows,
                 "state": "ABSENT" if cb is None else _worst([r["state"] for r in rows])})
    # M5 參數冊 × 匯流排在位
    rows = []
    for f in fams:
        c = f["counts"]
        st = "ABSENT" if f["state"] != "OK" else ("GREEN" if c["items"] and c["in_place"] == c["items"] else
                                                  "NODATA" if not c["items"] else "RED")
        rows.append({"id": f["key"], "zh": f["zh"], "state": st, "note": f"在位 {c['in_place']}/{c['items']} · 觸網 {c['net']}"})
    mats.append({"id": "spec_bus", "zh": "參數冊 × 匯流排在位", "source": "bus", "rows": rows,
                 "state": _worst([r["state"] for r in rows])})
    for m in mats:
        cnt = {}
        for r in m["rows"]:
            cnt[r["state"]] = cnt.get(r["state"], 0) + 1
        m["counts"] = cnt
    return mats


def _plain(s: str, n: int = 120) -> str:
    s = re.sub(r"\*\*|`", "", str(s or "")).replace("\n", " ").strip()
    return s[:n] + ("…" if len(s) > n else "")


def collect_logic(books: dict) -> dict:
    laws = (books.get("laws") or {}).get("laws") or []
    rows = []
    for law in laws if isinstance(laws, list) else []:
        if not isinstance(law, dict):
            continue
        rows.append({"id": law.get("id"), "rank": law.get("rank"), "cat": law.get("cat") or "其他",
                     "key": law.get("key") or "", "text": _plain(law.get("zh") or law.get("text") or "", 160)})
    rows.sort(key=lambda r: (r["rank"] is None, r["rank"] if isinstance(r["rank"], (int, float)) else 1e9, str(r["id"])))
    by_cat = {}
    for r in rows:
        by_cat[r["cat"]] = by_cat.get(r["cat"], 0) + 1
    lg = books.get("logic") or {}
    layers = []
    for name, lay in (lg.get("layers") or {}).items():
        nodes = (lay or {}).get("nodes") or []
        layers.append({"id": name, "why": _plain((lay or {}).get("why"), 90), "n": len(nodes),
                       "nodes": [{"family": n.get("family"), "role": n.get("role"), "kind": n.get("role_kind")}
                                 for n in nodes if isinstance(n, dict)][:40]})
    return {"laws": rows, "laws_by_cat": sorted(by_cat.items(), key=lambda kv: -kv[1]),
            "layers": layers, "rule_canons": sorted((lg.get("rule_canons") or {}).keys()),
            "off_book_pending": len(lg.get("off_book_pending") or []), "built_at": lg.get("built_at"),
            "state": "ABSENT" if not books.get("laws") and not books.get("logic") else "OK"}


def collect_run(grid_dir: Path = GRID_DIR) -> tuple:
    p = _tail(grid_dir, "GRID_*.json")
    if p is None:
        return ({"state": "NODATA", "why": "還沒有格子證據(跑一次 CGC_MDL064 SelftestGrid 才有)", "rows": [], "counts": {}},
                {"path": _rel(grid_dir), "state": "ABSENT", "sha": "", "why": "沒有 GRID_*.json"})
    g, row = _read_json(p)
    if g is None:
        return {"state": "NODATA", "why": row["why"], "rows": [], "counts": {}}, row
    cnt = {k: int(g.get(k) or 0) for k in ("ok", "fail", "skip", "timeout", "not_run", "locked")}
    rows = [{"name": str(r.get("name") or ""), "state": str(r.get("state") or ""), "secs": r.get("secs"),
             "note": _plain(r.get("note") or "", 220)} for r in g.get("results") or [] if isinstance(r, dict)]
    st = "RED" if cnt["fail"] else "AMBER" if cnt["timeout"] or cnt["not_run"] or g.get("interrupted") else "GREEN"
    return ({"state": st, "why": "", "ts": g.get("ts"), "total": int(g.get("total") or len(rows)),
             "elapsed_s": g.get("elapsed_s"), "machine_factor": g.get("machine_factor"), "fast": bool(g.get("fast")),
             "interrupted": bool(g.get("interrupted")), "counts": cnt, "rows": rows, "file": p.name}, row)


def collect_errors(mats: list, run: dict, sources: dict, fams: list) -> list:
    out = []
    for r in run.get("rows") or []:
        if r["state"] in ("FAIL", "TIMEOUT"):
            out.append({"sev": "RED" if r["state"] == "FAIL" else "AMBER", "source": "最近一次格子", "id": r["name"][:80],
                        "text": r["note"], "tab": "results"})
    for m in mats:
        for r in m["rows"]:
            if r["state"] in ("RED", "AMBER"):
                out.append({"sev": r["state"], "source": m["zh"], "id": str(r["id"]), "text": r["note"], "tab": "matrix"})
    for k, s in sources.items():
        if s["state"] != "OK":
            out.append({"sev": "AMBER" if s["state"] == "ABSENT" else "RED", "source": "資料來源", "id": s["zh"],
                        "text": f"{s['state']} · {s['path']} · {s['why']}", "tab": "overview"})
    for f in fams:
        for g in f["groups"]:
            for it in g["items"]:
                if it["engine_state"] == "ABSENT":
                    out.append({"sev": "RED", "source": f"{f['zh']} 引擎", "id": it["id"],
                                "text": f"尾版不在:{it['engine_glob']}", "tab": "engines"})
    out.sort(key=lambda e: (SEVERITY.get(e["sev"], 9), e["source"], e["id"]))
    return out


def _kpis(fams, inv, mats, logic, run, errors) -> list:
    items = sum(f["counts"]["items"] for f in fams)
    inp = sum(f["counts"]["in_place"] for f in fams)
    fx = next((m for m in mats if m["id"] == "fixed"), {"counts": {}, "rows": []})
    live = sum(v["count"] for v in (inv.get("families") or {}).values() if not v["retired"])
    ret = sum(v["count"] for v in (inv.get("families") or {}).values() if v["retired"])
    reds = sum(1 for e in errors if e["sev"] == "RED")
    ambers = sum(1 for e in errors if e["sev"] == "AMBER")
    c = run.get("counts") or {}
    top = next((r for r in logic["laws"] if r["rank"] == 1), None)
    return [
        {"id": "items", "label": "參數冊項目在位", "value": f"{inp}/{items}", "num": inp, "den": items,
         "tone": "ok" if items and inp == items else "bad" if items else "nd", "foot": "EngineBus 目錄實測", "tab": "engines"},
        {"id": "inventory", "label": "引擎盤點(現役)", "value": str(live) if inv["state"] == "OK" else "—",
         "num": live, "den": live + ret, "tone": "ok" if inv["state"] == "OK" else "nd",
         "foot": f"退役存證 {ret} · 治理模組 {inv.get('modules', 0)}" if inv["state"] == "OK" else inv.get("why", ""), "tab": "engines"},
        {"id": "fixed", "label": "已修冊複驗", "value": f"{fx['counts'].get('GREEN', 0)}/{len(fx['rows'])}",
         "num": fx["counts"].get("GREEN", 0), "den": len(fx["rows"]),
         "tone": "bad" if fx["counts"].get("RED") else "warn" if fx["counts"].get("NODATA") else "ok",
         "foot": f"RED {fx['counts'].get('RED', 0)} · 待全樹掃描 {fx['counts'].get('NODATA', 0)}", "tab": "matrix"},
        {"id": "laws", "label": "政策律條", "value": str(len(logic["laws"])), "num": len(logic["laws"]), "den": len(logic["laws"]),
         "tone": "ok" if logic["laws"] else "nd", "foot": f"最高位階 {top['id']}" if top else "位階未載", "tab": "logic"},
        {"id": "grid", "label": "最近一次格子", "value": f"{c.get('ok', 0)}/{run.get('total', 0)}" if run.get("total") else "—",
         "num": c.get("ok", 0), "den": run.get("total") or 0,
         "tone": {"GREEN": "ok", "AMBER": "warn", "RED": "bad"}.get(run["state"], "nd"),
         "foot": f"FAIL {c.get('fail', 0)} · SKIP {c.get('skip', 0)}" if run.get("total") else run.get("why", ""), "tab": "results"},
        {"id": "errors", "label": "錯誤 / 待辦", "value": f"{reds} / {ambers}", "num": reds, "den": reds + ambers,
         "tone": "bad" if reds else "warn" if ambers else "ok", "foot": "紅燈 / 待操作員", "tab": "errors"},
    ]


def collect(spec_path: Path = SPEC, books: dict | None = None, grid_dir: Path = GRID_DIR,
            bus_mod=None, panorama=None, manager=None, eng089=None, console=None, load_live: bool = True,
            db_payload: dict | None = None) -> dict:
    """收集全部需求 → 藍圖(dict)。唯讀、零寫檔、不跑任何引擎。"""
    t0 = time.time()
    sources: dict = {}
    spec, row = _read_json(spec_path)
    _src(sources, "spec", row)
    loaded = {}
    for k, p in (books if books is not None else BOOKS).items():
        loaded[k], row = _read_json(p)
        _src(sources, k, row)
    if load_live:
        if bus_mod is None:
            p = _tail(HERE, "CGC_MDL148_EngineBus_v*.py")
            bus_mod, err = _load(p, "vcb_bus")
            _src(sources, "bus", _mod_row(p, err))
        if panorama is None:
            p = _tail(HERE, "CGC_MDL158_VIAPanoramaAuditRepair_v*.py")
            panorama, err = _load(p, "vcb_panorama")
            _src(sources, "panorama", _mod_row(p, err))
        if manager is None:
            p = _tail(VIA, "VIA_SYSTEM_MANAGER_v*.py")
            manager, err = _load(p, "vcb_manager")
            _src(sources, "manager", _mod_row(p, err))
        if console is None:
            p = _tail(HERE, "CGC_MDL139_InputConsole_v*.py")
            console, err = _load(p, "vcb_console")
            _src(sources, "console", _mod_row(p, err))
        if eng089 is None:
            p = _tail(VIA / "functional modules" / "VRN", "VRN_ENG089_TemplateView_v*.py")
            eng089, err = _load(p, "vcb_eng089")
            _src(sources, "eng089", _mod_row(p, err))
    if load_live and db_payload is None:
        p = _tail(HERE, "CGC_MDL228_VIADBManager_v*.py")
        dbm, err = _load(p, "vcb_dbm")
        _src(sources, "dbm", _mod_row(p, err))
        if dbm is not None:
            try:
                db_payload = dbm.ui_payload()
            except Exception as exc:
                sources["dbm"].update(state="UNREADABLE", why=f"ui_payload 失敗:{type(exc).__name__}")
    if db_payload is not None:
        ov_ = db_payload.get("overview") or {}
        _src(sources, "db_catalog", {"path": _rel(VIA / "VIA_Reports" / "datahome" / "DATAHOME_CATALOG_latest.json"),
                                     "state": "OK" if ov_.get("catalog_state") == "OK" else ov_.get("catalog_state") or "ABSENT",
                                     "sha": "", "why": ov_.get("catalog_why") or ""})
        db_payload["vcgc_cmd"] = _vcgc_cmd()
    bus_rows = None
    if bus_mod is not None:
        try:
            bus_rows = bus_mod.catalog()
        except Exception as exc:
            sources.setdefault("bus", {"zh": BOOK_ZH["bus"], "path": "", "sha": ""}).update(
                state="UNREADABLE", why=f"catalog() 失敗:{type(exc).__name__}")

    def plan(iid: str) -> dict:
        if bus_mod is None or bus_rows is None:
            return {}
        try:
            return bus_mod.call(iid, None, apply=False, catalog_rows=bus_rows)
        except Exception as exc:
            return {"state": "UNREADABLE", "why": type(exc).__name__}

    resolver = eff = None
    if console is not None and spec is not None:
        def resolver(iid):
            return console.resolve_argv(spec, iid, {})       # 冊上參數;唯讀(只檢查檔案在不在)

        def eff(iid, gid):
            return console.effective_start(spec, iid, gid, "")
    fams = collect_params(spec, bus_rows, plan, resolver, eff)
    inv = collect_inventory(manager)
    mats = collect_matrices(loaded, panorama, fams)
    if db_payload is not None:
        rows = [{"id": f"{r['db']} · {r['table']}", "zh": r["table"], "state": r["state"],
                 "note": f"冊上次 {r['rows_seen'] if r['rows_seen'] is not None else '—'} · 現在 {r['rows_now'] if r['rows_now'] is not None else '—'} · {r['why']}"}
                for r in db_payload.get("reconcile") or []]
        cnt = {}
        for r in rows:
            cnt[r["state"]] = cnt.get(r["state"], 0) + 1
        mats.append({"id": "db_reconcile", "zh": "資料庫數量核對", "source": "dbm", "rows": rows, "counts": cnt,
                     "state": _worst([r["state"] for r in rows]) if rows else "NODATA"})
    logic = collect_logic(loaded)
    run, grow = collect_run(grid_dir)
    _src(sources, "grid", grow)
    errors = collect_errors(mats, run, sources, fams)
    return {
        "schema": "VIA.ConsoleBlueprint.v1", "engine": ENGINE_TAG, "built_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "collect_secs": round(time.time() - t0, 2),
        "layout": {"left": {"title": "參數輸入", "families": [f["key"] for f in fams],
                            "controls": sorted({c for v in KIND_KEYS.values() for _, c in v}), "actions": ["複製指令", "下載參數 JSON", "重設"]},
                   "right": {"tabs": [{"id": t, "zh": zh, "desc": d} for t, zh, d in TABS]},
                   "rule": "總覽第一、結果最後;每個數字都帶來源與四態(GREEN / RED / NODATA / ABSENT),量不到不當綠"},
        "sources": sources, "families": fams, "inventory": inv, "matrices": mats, "logic": logic, "run": run,
        "errors": errors, "kpis": _kpis(fams, inv, mats, logic, run, errors),
        "bus_cmd": _bus_cmd(),
        "console_cmd": _console_cmd(),
        "db": db_payload,
        "sync": {"module": MODULE, "state_key": STATE_KEY, "channel": CHANNEL},
        "_eng089": eng089,
    }


def _bus_cmd() -> str:
    p = _tail(HERE, "CGC_MDL148_EngineBus_v*.py")
    return f'python "{_rel(p)}"' if p else ""


def _console_cmd() -> str:
    p = _tail(HERE, "CGC_MDL139_InputConsole_v*.py")
    return f'python "{_rel(p)}"' if p else ""


def _vcgc_cmd() -> str:
    p = _tail(HERE, "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py")
    return f'python "{_rel(p)}"' if p else ""


def public(bp: dict) -> dict:
    """藍圖可序列化的那一份(拿掉執行期物件)。"""
    return {k: v for k, v in bp.items() if not k.startswith("_")}


# ---------------------------------------------------------------- ② 頁面(單一渲染器:全頁與外掛共用)
STYLE = r"""
.vcb{--bg:#f3f5f9;--panel:#fff;--panel2:#f8fafc;--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--accent:#2563eb;--accent2:#7c3aed;
--ok:#16a34a;--warn:#d97706;--bad:#dc2626;--nd:#94a3b8;--ab:#64748b;--shadow:0 1px 2px rgba(15,23,42,.06),0 4px 16px rgba(15,23,42,.05);
font:13px/1.5 "Segoe UI","Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif;color:var(--ink);background:var(--bg);
box-sizing:border-box;min-height:100vh}
@media (prefers-color-scheme:dark){.vcb{--bg:#0b1220;--panel:#111a2b;--panel2:#0f1726;--ink:#e5e7eb;--muted:#94a3b8;--line:#1f2a3d;
--shadow:0 1px 2px rgba(0,0,0,.4)}}
.vcb *,.vcb *:before,.vcb *:after{box-sizing:inherit}.vcb [hidden]{display:none!important}
.vcb-top{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding:12px 20px;background:linear-gradient(90deg,#0f172a,#1e293b);color:#e2e8f0}
.vcb-brand{display:flex;align-items:center;gap:10px;font-weight:700;font-size:15px;letter-spacing:.2px}
.vcb-logo{width:28px;height:28px;border-radius:8px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);display:grid;place-items:center;font-size:12px;color:#fff}
.vcb-meta{color:#94a3b8;font-size:12px}.vcb-legend{margin-left:auto;display:flex;gap:10px;flex-wrap:wrap;font-size:11.5px;color:#cbd5e1}
.vcb-shell{display:grid;grid-template-columns:340px minmax(0,1fr);gap:16px;padding:16px 20px;align-items:start}
.vcb-left{position:sticky;top:12px;max-height:calc(100vh - 24px);overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow)}
.vcb-left h2{font-size:13px;margin:0;padding:14px 16px 10px;display:flex;justify-content:space-between;align-items:center}
.vcb-seg{display:grid;grid-template-columns:repeat(5,1fr);gap:4px;margin:0 12px 10px;padding:4px;background:var(--panel2);border:1px solid var(--line);border-radius:10px}
.vcb-seg button{border:0;background:transparent;color:var(--muted);padding:7px 4px;border-radius:7px;font:inherit;font-weight:600;cursor:pointer}
.vcb-seg button.on{background:var(--panel);color:var(--ink);box-shadow:var(--shadow)}.vcb-seg small{display:block;font-weight:400;font-size:10.5px}
.vcb-search{margin:0 12px 8px;width:calc(100% - 24px);padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--panel2);color:var(--ink);font:inherit}
.vcb-grp{border-top:1px solid var(--line)}.vcb-grp>summary{list-style:none;cursor:pointer;padding:9px 16px;font-weight:600;display:flex;justify-content:space-between;gap:8px}
.vcb-grp>summary::-webkit-details-marker{display:none}.vcb-grp>summary:after{content:"▾";color:var(--muted)}.vcb-grp:not([open])>summary:after{content:"▸"}
.vcb-item{display:grid;grid-template-columns:18px 1fr auto;gap:8px;align-items:start;padding:6px 16px 6px 18px;cursor:pointer}
.vcb-item:hover{background:var(--panel2)}.vcb-item input{margin-top:3px}.vcb-item .t{font-size:12.5px}.vcb-item .id{font:11px ui-monospace,Consolas,monospace;color:var(--muted)}
.vcb-tags{display:flex;gap:4px;align-items:center}
.vcb-sec{padding:12px 16px;border-top:1px solid var(--line)}.vcb-sec h3{margin:0 0 8px;font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px}
.vcb-field{display:grid;gap:3px;margin-bottom:9px}.vcb-field label{font-size:12px;font-weight:600}.vcb-field .h{font-size:11px;color:var(--muted)}
.vcb-field input{padding:7px 9px;border:1px solid var(--line);border-radius:7px;background:var(--panel2);color:var(--ink);font:inherit}
.vcb-cmd{white-space:pre-wrap;word-break:break-all;background:#0f172a;color:#e2e8f0;border-radius:8px;padding:10px;font:11.5px/1.55 ui-monospace,Consolas,monospace;max-height:220px;overflow:auto;margin:0}
.vcb-btns{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.vcb-btn{border:1px solid var(--line);background:var(--panel);color:var(--ink);padding:6px 11px;border-radius:7px;font:inherit;font-weight:600;cursor:pointer}
.vcb-btn.pri{background:var(--accent);border-color:var(--accent);color:#fff}.vcb-btn:hover{filter:brightness(.97)}
.vcb-right{min-width:0}.vcb-tabs{display:flex;gap:4px;overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:5px;box-shadow:var(--shadow)}
.vcb-tab{border:0;background:transparent;padding:8px 14px;border-radius:8px;font:inherit;font-weight:600;color:var(--muted);cursor:pointer;white-space:nowrap;display:flex;gap:7px;align-items:center}
.vcb-tab.on{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff}.vcb-tab .n{font-size:10.5px;padding:0 6px;border-radius:9px;background:rgba(148,163,184,.25)}
.vcb-tab.on .n{background:rgba(255,255,255,.25)}.vcb-pane{margin-top:14px}.vcb-desc{color:var(--muted);margin:0 0 12px}
.vcb-kpis{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px}
.vcb-kpi{position:relative;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 14px 10px;box-shadow:var(--shadow);cursor:pointer;overflow:hidden}
.vcb-kpi:before{content:"";position:absolute;inset:0 auto 0 0;width:4px;background:var(--tone,var(--nd))}
.vcb-kpi .l{font-size:11.5px;color:var(--muted);font-weight:600}.vcb-kpi .v{font-size:24px;font-weight:750;letter-spacing:-.5px;margin:2px 0}
.vcb-kpi .f{font-size:11px;color:var(--muted);min-height:16px}.vcb-meter{height:5px;border-radius:3px;background:var(--line);overflow:hidden;margin:6px 0 4px}
.vcb-meter i{display:block;height:100%;background:var(--tone,var(--nd))}
.vcb-grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:12px;margin-top:12px}
.vcb-card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px;box-shadow:var(--shadow);min-width:0}
.vcb-card h4{margin:0 0 10px;font-size:13px;display:flex;justify-content:space-between;align-items:center;gap:8px}
.vcb-card h4 a{font-size:11.5px;font-weight:600;color:var(--accent);cursor:pointer;text-decoration:none}
.c4{grid-column:span 4}.c5{grid-column:span 5}.c6{grid-column:span 6}.c7{grid-column:span 7}.c8{grid-column:span 8}.c12{grid-column:span 12}
.vcb-heat{display:grid;grid-template-columns:minmax(110px,1.4fr) repeat(5,minmax(36px,1fr));gap:4px;font-size:11.5px}
.vcb-heat .hd{color:var(--muted);font-weight:600;text-align:center}.vcb-heat .rn{font-weight:600;align-self:center;cursor:pointer}
.vcb-heat .cell{height:30px;border-radius:6px;display:grid;place-items:center;font-weight:700;color:#fff}
.vcb-heat .cell.z{background:var(--panel2);color:var(--nd);font-weight:400}
.vcb-flow{display:flex;gap:0;overflow-x:auto;padding-bottom:4px}
.vcb-step{flex:1 1 88px;min-width:88px;position:relative;padding:10px 18px 10px 22px;background:var(--panel2);border:1px solid var(--line);margin-right:-1px;clip-path:polygon(0 0,calc(100% - 12px) 0,100% 50%,calc(100% - 12px) 100%,0 100%,12px 50%)}
.vcb-step:first-child{clip-path:polygon(0 0,calc(100% - 12px) 0,100% 50%,calc(100% - 12px) 100%,0 100%);padding-left:12px}
.vcb-step b{display:block;font-size:12px}.vcb-step span{font-size:11px;color:var(--muted)}.vcb-step em{font-style:normal;font-size:18px;font-weight:750;color:var(--accent)}
.vcb-bars{display:grid;gap:6px}.vcb-bar{display:grid;grid-template-columns:minmax(80px,120px) 1fr 44px;gap:8px;align-items:center;font-size:12px}
.vcb-bar .tr{height:10px;background:var(--line);border-radius:5px;overflow:hidden;display:flex}.vcb-bar .tr i{display:block;height:100%}
.vcb-bar .n{text-align:right;color:var(--muted);font-variant-numeric:tabular-nums}
.vcb-donut{display:flex;gap:16px;align-items:center;flex-wrap:wrap}.vcb-donut svg{flex:0 0 auto}
.vcb-lgd{display:grid;gap:5px;font-size:12px}.vcb-lgd div{display:flex;gap:7px;align-items:center}
.vcb-dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--nd);flex:0 0 auto}
.vcb-badge{display:inline-flex;align-items:center;gap:5px;padding:1px 8px;border-radius:20px;font-size:11px;font-weight:700;border:1px solid transparent;white-space:nowrap}
.vcb-badge.GREEN{background:rgba(22,163,74,.12);color:var(--ok)}.vcb-badge.RED{background:rgba(220,38,38,.12);color:var(--bad)}
.vcb-badge.AMBER{background:rgba(217,119,6,.13);color:var(--warn)}.vcb-badge.NODATA{background:rgba(148,163,184,.18);color:var(--muted)}
.vcb-badge.ABSENT,.vcb-badge.UNREADABLE{background:rgba(100,116,139,.12);color:var(--ab);border-color:rgba(100,116,139,.35)}
.vcb-badge.NET{background:rgba(37,99,235,.1);color:var(--accent)}.vcb-badge.OK{background:rgba(22,163,74,.12);color:var(--ok)}
.vcb-err{display:grid;gap:6px}.vcb-err div{display:grid;grid-template-columns:auto 1fr;gap:8px;align-items:start;padding:7px 9px;border-radius:8px;background:var(--panel2);font-size:12px}
.vcb-err .s{color:var(--muted);font-size:11px}
.vcb-tw{overflow:auto;border:1px solid var(--line);border-radius:10px;max-height:560px}
.vcb-t{width:100%;border-collapse:collapse;font-size:12px}.vcb-t th{position:sticky;top:0;background:var(--panel2);text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);font-size:11.5px;color:var(--muted);z-index:1}
.vcb-t td{padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}.vcb-t tr:hover td{background:var(--panel2)}.vcb-mono{font:11.5px ui-monospace,Consolas,monospace}
.vcb-chips{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}.vcb-chip{border:1px solid var(--line);background:var(--panel);padding:4px 10px;border-radius:20px;font:inherit;font-size:12px;cursor:pointer;color:var(--ink)}
.vcb-chip.on{border-color:var(--accent);color:var(--accent);background:rgba(37,99,235,.08)}
.vcb-lay{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}.vcb-lay .vcb-card ul{margin:6px 0 0;padding-left:16px;font-size:12px}
.vcb-src{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:6px}.vcb-src div{display:flex;justify-content:space-between;gap:8px;padding:6px 9px;background:var(--panel2);border-radius:7px;font-size:12px}
.vcb-empty{color:var(--muted);padding:18px;text-align:center}
.vcb-sel{width:100%;padding:7px 9px;border:1px solid var(--line);border-radius:7px;background:var(--panel2);color:var(--ink);font:inherit}
.vcb-radio{display:grid;grid-template-columns:18px 1fr auto;gap:8px;align-items:center;padding:5px 2px;cursor:pointer;font-size:12.5px}
.vcb-fmts{display:flex;flex-wrap:wrap;gap:6px}.vcb-fmts label{display:flex;gap:5px;align-items:center;border:1px solid var(--line);border-radius:7px;padding:4px 8px;font-size:12px;cursor:pointer}
.vcb-stack{display:flex;height:10px;border-radius:5px;overflow:hidden;background:var(--line)}.vcb-stack i{display:block;height:100%}
.cl2{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
@media (max-width:1280px){.vcb-kpis{grid-template-columns:repeat(3,minmax(0,1fr))}.c4,.c5,.c7{grid-column:span 6}}
@media (max-width:900px){.vcb-shell{grid-template-columns:1fr;padding:12px}.vcb-left{position:static;max-height:none}
.vcb-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.c4,.c5,.c6,.c7,.c8{grid-column:span 12}.vcb-legend{margin-left:0}}
"""

APP_JS = r"""(function () {
  'use strict';
  var COL = { GREEN: 'var(--ok)', RED: 'var(--bad)', AMBER: 'var(--warn)', NODATA: 'var(--nd)', ABSENT: 'var(--ab)', UNREADABLE: 'var(--ab)', OK: 'var(--ok)' };
  var TONE = { ok: 'var(--ok)', warn: 'var(--warn)', bad: 'var(--bad)', nd: 'var(--nd)' };
  var ZH = { GREEN: '綠', RED: '紅', AMBER: '待裁', NODATA: '無料', ABSENT: '缺件', UNREADABLE: '讀不動', OK: '可讀' };
  function esc(s) { return String(s === null || s === undefined ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function badge(st, text) { st = String(st || 'NODATA').toUpperCase(); return '<span class="vcb-badge ' + esc(st) + '">' + esc(text || (st + (ZH[st] ? ' · ' + ZH[st] : ''))) + '</span>'; }
  function dot(st) { return '<span class="vcb-dot" style="background:' + (COL[st] || 'var(--nd)') + '"></span>'; }
  function table(cols, rows) {
    if (!rows.length) return '<div class="vcb-empty">(沒有列)</div>';
    return '<div class="vcb-tw"><table class="vcb-t"><thead><tr>' + cols.map(function (c) { return '<th>' + esc(c) + '</th>'; }).join('') +
      '</tr></thead><tbody>' + rows.map(function (r) { return '<tr>' + r.map(function (v) { return '<td>' + v + '</td>'; }).join('') + '</tr>'; }).join('') + '</tbody></table></div>';
  }
  function donut(parts, total, label) {
    var R = 54, C = 2 * Math.PI * R, off = 0, segs = '';
    parts.forEach(function (p) {
      if (!p.v || !total) return;
      var len = C * p.v / total;
      segs += '<circle r="' + R + '" cx="70" cy="70" fill="none" stroke="' + p.c + '" stroke-width="18" stroke-dasharray="' + len + ' ' + (C - len) + '" stroke-dashoffset="' + (-off) + '" transform="rotate(-90 70 70)"/>';
      off += len;
    });
    return '<svg width="140" height="140" viewBox="0 0 140 140" role="img" aria-label="' + esc(label) + '"><circle r="' + R + '" cx="70" cy="70" fill="none" stroke="var(--line)" stroke-width="18"/>' + segs +
      '<text x="70" y="66" text-anchor="middle" font-size="22" font-weight="750" fill="currentColor">' + esc(total || '—') + '</text><text x="70" y="86" text-anchor="middle" font-size="11" fill="var(--muted)">' + esc(label) + '</text></svg>';
  }
  function download(name, text) {
    var b = new Blob([text], { type: 'application/json' }), a = document.createElement('a');
    a.href = URL.createObjectURL(b); a.download = name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(function () { URL.revokeObjectURL(a.href); }, 0);
  }

  function mount(host, P, opts) {
    opts = opts || {};
    var S = { fam: (P.families[0] || {}).key, tab: 'overview', sel: {}, vals: {}, q: '', filt: {}, open: {}, dbv: {} };
    function narrow() { try { return window.innerWidth <= 900; } catch (e) { return false; } }
    try { var h = (location.hash || '').replace('#', ''); if (P.layout.right.tabs.some(function (t) { return t.id === h; })) S.tab = h; } catch (e) { }
    function famOf(k) { return P.families.filter(function (f) { return f.key === k; })[0]; }
    function items(f) { var out = []; (f.groups || []).forEach(function (g) { (g.items || []).forEach(function (it) { out.push(it); }); }); return out; }
    function allItems() { var o = []; P.families.forEach(function (f) { items(f).forEach(function (it) { o.push({ f: f, it: it }); }); }); return o; }
    var errN = P.errors.filter(function (e) { return e.sev === 'RED'; }).length;

    host.innerHTML = '<div class="vcb" data-vcb-root="1"><header class="vcb-top"><div class="vcb-brand"><div class="vcb-logo">V</div>VIA 中央主控台 · VCGC / VDF / VRN</div>' +
      '<div class="vcb-meta">' + esc(P.engine) + ' · 建構 ' + esc(P.built_at) + ' · 收集 ' + esc(P.collect_secs) + 's</div>' +
      '<div class="vcb-legend">' + ['GREEN', 'AMBER', 'RED', 'NODATA', 'ABSENT'].map(function (s) { return '<span>' + dot(s) + ' ' + s + ' ' + (ZH[s] || '') + '</span>'; }).join('') + '</div></header>' +
      '<div class="vcb-shell"><aside class="vcb-left" data-vcb="left"></aside><main class="vcb-right"><nav class="vcb-tabs" role="tablist"></nav><section class="vcb-pane" data-vcb="pane"></section></main></div></div>';
    var root = host.querySelector('[data-vcb-root]'), left = root.querySelector('[data-vcb=left]'), nav = root.querySelector('.vcb-tabs'), pane = root.querySelector('[data-vcb=pane]');

    // ---------------- 左面板
    function selected() { return allItems().filter(function (x) { return S.sel[x.it.id]; }); }
    function paramsOfSel() {
      var m = {};
      selected().forEach(function (x) { (x.it.params || []).forEach(function (c) { if (!m[c.key]) m[c.key] = { c: c, who: [] }; m[c.key].who.push(x.it.id); }); });
      return m;
    }
    function q(s) { s = String(s); return /[\s"]/.test(s) ? '"' + s.replace(/"/g, '\\"') + '"' : s; }
    // 旗標怎麼寫由正主 MDL139 翻譯(argv = 唯讀解析 · run --dry = 乾跑);本頁只交鍵=值,不自己拼旗標
    function argvOf(it) {
      var kv = (it.params || []).map(function (c) { var v = S.vals[c.key]; return v ? q(c.key + '=' + v) : ''; }).filter(Boolean).join(' ');
      if (!P.console_cmd) return '(輸入主控台 MDL139 尾版不在:無法委派翻譯)';
      var lines = [P.console_cmd + ' argv --item ' + it.id + (kv ? ' ' + kv : '') + '      # 正主解析,唯讀',
                   P.console_cmd + ' run --item ' + it.id + (kv ? ' ' + kv : '') + ' --dry  # 乾跑,不動手'];
      if (!kv) lines.push('# 以冊上參數,正主解析 = ' + it.resolved_state + (it.resolved_argv.length ? ':' + it.resolved_argv.map(q).join(' ') : '') + (it.resolved_note ? '(' + it.resolved_note + ')' : ''));
      if ((it.unsupported || []).length) lines.push('# 冊上另有 ' + it.unsupported.join(', ') + ':正主翻譯器不接,本頁不給欄位');
      return lines.join('\n');
    }
    function segHtml() {
      var ov = dbOv();
      return '<div class="vcb-seg">' + P.families.map(function (x) { return '<button type="button" data-fam="' + esc(x.key) + '" class="' + (x.key === S.fam ? 'on' : '') + '">' + esc(x.key.toUpperCase()) + '<small>' + esc((x.counts || {}).items || 0) + ' 項</small></button>'; }).join('') +
        '<button type="button" data-fam="db" class="' + (S.fam === 'db' ? 'on' : '') + '">DB<small>' + esc(ov.kpi && ov.kpi.tables !== undefined ? ov.kpi.tables + ' 表' : '無目錄') + '</small></button></div>';
    }
    function renderLeft() {
      if (S.fam === 'db') { renderDbLeft(); return; }
      var f = famOf(S.fam) || { groups: [], counts: {} };
      var h = '<h2><span>參數輸入</span>' + badge(f.state === 'OK' ? 'GREEN' : 'ABSENT', f.state === 'OK' ? '參數冊' : '缺家族') + '</h2>' + segHtml() +
        '<input class="vcb-search" type="search" placeholder="搜尋項目(中文 / id)" value="' + esc(S.q) + '">';
      if (f.state !== 'OK') h += '<div class="vcb-empty">' + esc(f.why) + '</div>';
      (f.groups || []).forEach(function (g) {
        var its = (g.items || []).filter(function (it) { return !S.q || (it.zh + ' ' + it.id).toLowerCase().indexOf(S.q.toLowerCase()) >= 0; });
        if (!its.length) return;
        var anySel = its.some(function (it) { return S.sel[it.id]; }), open = S.q || anySel || S.open[g.id] || !narrow();
        h += '<details class="vcb-grp" data-grp="' + esc(g.id) + '"' + (open ? ' open' : '') + '><summary><span>' + esc(g.zh) + '</span><span class="vcb-meta">' + its.length + '</span></summary>' +
          its.map(function (it) {
            return '<label class="vcb-item" title="' + esc(it.zh + (it.note ? '\n' + it.note : '')) + '"><input type="checkbox" data-item="' + esc(it.id) + '"' + (S.sel[it.id] ? ' checked' : '') + '><span><span class="t cl2">' + esc(it.zh) + '</span><span class="id">' + esc(it.id) + '</span></span>' +
              '<span class="vcb-tags">' + (it.net ? badge('NET', '觸網') : '') + dot(it.engine_state) + '</span></label>';
          }).join('') + '</details>';
      });
      var pm = paramsOfSel(), keys = Object.keys(pm);
      h += '<div class="vcb-sec"><h3>參數(已選 ' + selected().length + ' 項)</h3>' + (keys.length ? keys.map(function (k) {
        var c = pm[k].c, v = S.vals[k] || '', t = { number: 'number' }[c.control] || 'text';
        return '<div class="vcb-field"><label>' + esc(k) + ' <span class="vcb-meta">(' + esc(c.kind) + ' · ' + pm[k].who.length + ' 項用)</span></label><input type="' + t + '" data-param="' + esc(k) + '" value="' + esc(v) + '" placeholder="' + esc(c.placeholder ? '冊上:' + c.placeholder : (c.control === 'date' ? 'YYYY-MM-DD' : c.control === 'month' ? 'YYYY-MM 或 YYYY-MM-DD' : '留空 = 冊上參數')) + '"><span class="h">' + esc(c.hint) + '</span></div>';
      }).join('') : '<div class="vcb-meta">勾選左邊的項目,這裡只出現它們用得到的參數。</div>') + '</div>';
      var cmd = selected().map(function (x) { return '# ' + x.it.id + '\n' + argvOf(x.it); }).join('\n\n');
      h += '<div class="vcb-sec"><h3>指令預覽(正主解析 / 乾跑,不動手)</h3><pre class="vcb-cmd" data-vcb="cmd">' + esc(cmd || '(先勾選項目)') + '</pre>' +
        '<div class="vcb-meta" style="margin-top:6px">旗標寫法由輸入主控台 MDL139 正主翻譯(範圍拆 --start/--end、代碼依各項寫法…);欄位留空 = 冊上參數。真跑一律經 VCGC 唯一入口。</div>' +
        '<div class="vcb-btns"><button type="button" class="vcb-btn pri" data-act="copy">複製指令</button><button type="button" class="vcb-btn" data-act="json">下載參數 JSON</button><button type="button" class="vcb-btn" data-act="reset">重設</button></div></div>';
      var keep = left.scrollTop;          // 勾選 / 改參數會重畫左面板:捲動位置留住,不跳回頂端
      left.innerHTML = h; left.scrollTop = keep;
    }
    // ---------------- DB 家族(VIA_DBManager · CGC_MDL228;經 via-vcgc dbm export,先乾跑)
    function dbOv() { return (P.db && P.db.overview) || { dbs: [], tables: [], lakes: [], kpi: {}, state: 'NODATA', catalog_why: 'VIA_DBManager(CGC_MDL228)沒有輸出' }; }
    var FMT = [['csv', 'CSV(utf-8-sig)'], ['big5', 'CSV(Big5)'], ['gsheet', 'Google Sheet'], ['md', 'Markdown'], ['json', 'JSON'], ['parquet', 'Parquet']];
    function dbExportCmd(v, t, dry) {
      var a = ['via-vcgc dbm export', '--db', q(v.db), '--table', q(t.table)];
      if (v.cols) a.push('--cols', q(v.cols));
      if (v.start) a.push('--start', v.start);
      if (v.end) a.push('--end', v.end);
      a.push('--format', v.fmt || 'csv');
      if (dry) a.push('--dry');
      return a.join(' ');
    }
    function renderDbLeft() {
      var ov = dbOv(), v = S.dbv, h = '<h2><span>資料庫匯出</span>' + badge(ov.state === 'NODATA' ? 'NODATA' : ov.stale ? 'AMBER' : 'GREEN', ov.state === 'NODATA' ? '無目錄' : ov.stale ? '目錄過期' : '目錄') + '</h2>' + segHtml();
      if (ov.state === 'NODATA') {
        h += '<div class="vcb-sec"><div class="vcb-empty">' + esc(ov.catalog_why) + '</div><pre class="vcb-cmd" data-vcb="cmd">via-datahome catalog -Tables\nvia-vcgc dbm overview</pre>' +
          '<div class="vcb-btns"><button type="button" class="vcb-btn pri" data-act="copy">複製指令</button></div></div>';
        var keep0 = left.scrollTop; left.innerHTML = h; left.scrollTop = keep0; return;
      }
      if (!v.db || !ov.dbs.some(function (d) { return d.name === v.db; })) { v.db = (ov.dbs.filter(function (d) { return d.role === '正庫'; })[0] || ov.dbs[0] || {}).name; v.table = ''; }
      h += '<input class="vcb-search" type="search" placeholder="搜尋表名" value="' + esc(S.q) + '">';
      h += '<div class="vcb-sec"><h3>① 庫</h3><select class="vcb-sel" data-dbk="db">' + ov.dbs.map(function (d) {
        return '<option value="' + esc(d.name) + '"' + (d.name === v.db ? ' selected' : '') + '>' + esc(d.name) + ' · ' + esc(d.role) + ' · ' + d.tables + ' 表 · ' + Number(d.rows).toLocaleString() + ' 列</option>';
      }).join('') + '</select></div>';
      var tabs = ov.tables.filter(function (t) { return t.db === v.db && (!S.q || String(t.table).toLowerCase().indexOf(S.q.toLowerCase()) >= 0); });
      h += '<div class="vcb-sec"><h3>② 表(' + tabs.length + ')</h3>' + (tabs.length ? tabs.map(function (t) {
        return '<label class="vcb-radio"><input type="radio" name="vcbtab" data-dbk="table" value="' + esc(t.table) + '"' + (t.table === v.table ? ' checked' : '') + '><span><b>' + esc(t.table) + '</b><br><span class="vcb-meta">' +
          Number(t.rows).toLocaleString() + ' 列' + (t.lo ? ' · ' + esc(t.lo) + ' → ' + esc(t.hi) : t.date_col ? ' · 日期欄 ' + esc(t.date_col) : ' · 無日期欄') + '</span></span>' + dot(t.state) + '</label>';
      }).join('') : '<div class="vcb-meta">(沒有符合的表)</div>') + '</div>';
      var t = ov.tables.filter(function (x) { return x.db === v.db && x.table === v.table; })[0];
      if (t) {
        var dateOk = !!(t.date_col && t.iso_dates !== false);
        h += '<div class="vcb-sec"><h3>③ 欄位</h3><div class="vcb-field"><input type="text" data-dbk="cols" value="' + esc(v.cols || '') + '" placeholder="留空 = 全部欄;逗號分隔"><span class="h">欄名由引擎以 PRAGMA 核對,不認得的整筆擋下</span></div></div>';
        h += '<div class="vcb-sec"><h3>④ 期間' + (t.date_col ? '(' + esc(t.date_col) + ')' : '') + '</h3>' + (dateOk ?
          '<div class="vcb-field"><label>起</label><input type="date" data-dbk="start" value="' + esc(v.start || '') + '" min="' + esc(t.lo) + '" max="' + esc(t.hi) + '"></div>' +
          '<div class="vcb-field"><label>迄</label><input type="date" data-dbk="end" value="' + esc(v.end || '') + '" min="' + esc(t.lo) + '" max="' + esc(t.hi) + '"><span class="h">範圍 ' + esc(t.lo) + ' → ' + esc(t.hi) + ';留空 = 不限</span></div>'
          : '<div class="vcb-meta">' + (t.date_col ? '日期欄不是西元日期(例 ' + esc(t.lo) + '):期間篩選停用,整表匯出' : '這張表沒有日期欄:期間篩選停用,整表匯出') + '</div>') + '</div>';
        h += '<div class="vcb-sec"><h3>⑤ 格式</h3><div class="vcb-fmts">' + FMT.map(function (f) {
          var cap = (P.db.caps || {})[f[0]];
          return '<label title="單次上限 ' + (cap ? Number(cap).toLocaleString() : '—') + ' 列"><input type="radio" name="vcbfmt" data-dbk="fmt" value="' + f[0] + '"' + ((v.fmt || 'csv') === f[0] ? ' checked' : '') + '>' + esc(f[1]) + '</label>';
        }).join('') + '</div>' + ((v.fmt === 'big5') ? '<div class="vcb-meta" style="margin-top:6px">Big5 放不下的字會逐字報數並寫成 ?;要原字請用 CSV(utf-8-sig)</div>' : '') +
          ((v.fmt === 'md') ? '<div class="vcb-meta" style="margin-top:6px">Markdown 只給小範圍(上限 ' + Number((P.db.caps || {}).md || 0).toLocaleString() + ' 列)</div>' : '') + '</div>';
        var cmd = '# 先乾跑:只數列數、不寫檔\n' + dbExportCmd(v, t, true) + '\n\n# 真匯出:只寫 VIA_Reports/dbmanager/exports(回讀核對列數)\n' + dbExportCmd(v, t, false);
        h += '<div class="vcb-sec"><h3>⑥ 指令(經 VCGC 唯一入口)</h3><pre class="vcb-cmd" data-vcb="cmd">' + esc(cmd) + '</pre>' +
          '<div class="vcb-meta" style="margin-top:6px">讀庫一律唯讀;約 ' + Number(t.rows).toLocaleString() + ' 列(期間篩選前)。</div>' +
          '<div class="vcb-btns"><button type="button" class="vcb-btn pri" data-act="copy">複製指令</button><button type="button" class="vcb-btn" data-act="reset">重設</button></div></div>';
      } else {
        h += '<div class="vcb-sec"><div class="vcb-meta">先在 ② 選一張表。</div><pre class="vcb-cmd" data-vcb="cmd">(先選表)</pre></div>';
      }
      var keep = left.scrollTop; left.innerHTML = h; left.scrollTop = keep;
    }
    left.addEventListener('click', function (ev) {
      var b = ev.target.closest('[data-fam]'); if (b) { S.fam = b.getAttribute('data-fam'); renderLeft(); return; }
      var a = ev.target.closest('[data-act]'); if (!a) return;
      var act = a.getAttribute('data-act'), cmd = left.querySelector('[data-vcb=cmd]').textContent;
      if (act === 'copy') { try { navigator.clipboard.writeText(cmd); a.textContent = '已複製'; setTimeout(function () { a.textContent = '複製指令'; }, 1200); } catch (e) { } }
      if (act === 'json') download('VIA_console_params.json', JSON.stringify({ schema: 'VIA.ConsoleParams.v1', family: S.fam, items: selected().map(function (x) { return x.it.id; }), params: S.vals, built_from: P.engine }, null, 2));
      if (act === 'reset') { S.sel = {}; S.vals = {}; S.dbv = {}; renderLeft(); }
    });
    left.addEventListener('toggle', function (ev) { var d = ev.target; if (d && d.hasAttribute && d.hasAttribute('data-grp')) S.open[d.getAttribute('data-grp')] = d.open; }, true);
    left.addEventListener('change', function (ev) {
      var t = ev.target;
      if (t.hasAttribute('data-dbk')) { var k = t.getAttribute('data-dbk'); S.dbv[k] = t.value; if (k === 'db') { S.dbv.table = ''; S.dbv.start = ''; S.dbv.end = ''; S.dbv.cols = ''; } if (k === 'table') { S.dbv.start = ''; S.dbv.end = ''; S.dbv.cols = ''; } renderLeft(); return; }
      if (t.hasAttribute('data-item')) { S.sel[t.getAttribute('data-item')] = t.checked; renderLeft(); }
      else if (t.hasAttribute('data-param')) { S.vals[t.getAttribute('data-param')] = t.value; renderLeft(); }
    });
    left.addEventListener('input', function (ev) {
      if (ev.target.classList.contains('vcb-search')) { S.q = ev.target.value; var pos = ev.target.selectionStart; renderLeft(); var s = left.querySelector('.vcb-search'); s.focus(); try { s.setSelectionRange(pos, pos); } catch (e) { } }
    });

    // ---------------- 右面板
    function tabCount(id) {
      if (id === 'errors') return errN; if (id === 'matrix') return P.matrices.length; if (id === 'logic') return P.logic.laws.length;
      if (id === 'engines') return allItems().length; if (id === 'results') return (P.run.rows || []).length;
      if (id === 'db') return dbOv().state === 'NODATA' ? '無目錄' : dbOv().tables.length; return '';
    }
    function renderNav() {
      nav.innerHTML = P.layout.right.tabs.map(function (t, i) {
        var n = tabCount(t.id);
        return '<button type="button" role="tab" class="vcb-tab' + (t.id === S.tab ? ' on' : '') + '" data-tab="' + esc(t.id) + '" aria-selected="' + (t.id === S.tab) + '">' + (i + 1) + ' · ' + esc(t.zh) + (n !== '' ? '<span class="n">' + esc(n) + '</span>' : '') + '</button>';
      }).join('');
    }
    nav.addEventListener('click', function (ev) { var b = ev.target.closest('[data-tab]'); if (b) go(b.getAttribute('data-tab')); });
    function go(t) { S.tab = t; renderNav(); renderPane(); try { history.replaceState(null, '', '#' + t); } catch (e) { } }
    pane.addEventListener('click', function (ev) {
      var g = ev.target.closest('[data-go]'); if (g) { go(g.getAttribute('data-go')); return; }
      var c = ev.target.closest('[data-filt]'); if (c) { var k = c.getAttribute('data-filt'), v = c.getAttribute('data-v'); S.filt[k] = S.filt[k] === v ? '' : v; renderPane(); }
    });
    pane.addEventListener('input', function (ev) {
      var t = ev.target; if (!t.hasAttribute('data-q')) return;
      var k = t.getAttribute('data-q'), pos = t.selectionStart; S.filt[k + '_q'] = t.value; renderPane();
      var n = pane.querySelector('[data-q="' + k + '"]'); if (n) { n.focus(); try { n.setSelectionRange(pos, pos); } catch (e) { } }
    });
    function chips(key, vals) {
      return '<div class="vcb-chips">' + vals.map(function (v) { return '<button type="button" class="vcb-chip' + (S.filt[key] === v[0] ? ' on' : '') + '" data-filt="' + esc(key) + '" data-v="' + esc(v[0]) + '">' + esc(v[1]) + '</button>'; }).join('') + '</div>';
    }
    function qbox(key, ph) { return '<input class="vcb-search" style="margin:0 0 10px;width:100%" data-q="' + esc(key) + '" placeholder="' + esc(ph) + '" value="' + esc(S.filt[key + '_q'] || '') + '">'; }
    function hit(key, s) { var q = (S.filt[key + '_q'] || '').toLowerCase(); return !q || String(s).toLowerCase().indexOf(q) >= 0; }

    function overview() {
      var h = '<div class="vcb-kpis">' + P.kpis.map(function (k) {
        var pct = k.den ? Math.round(100 * k.num / k.den) : 0;
        return '<div class="vcb-kpi" style="--tone:' + (TONE[k.tone] || 'var(--nd)') + '" data-go="' + esc(k.tab) + '"><div class="l">' + esc(k.label) + '</div><div class="v">' + esc(k.value) +
          '</div><div class="vcb-meter"><i style="width:' + pct + '%"></i></div><div class="f">' + esc(k.foot) + '</div></div>';
      }).join('') + '</div><div class="vcb-grid">';
      // 矩陣熱圖
      var ST = ['GREEN', 'AMBER', 'RED', 'NODATA', 'ABSENT'];
      h += '<div class="vcb-card c7"><h4><span>矩陣狀況</span><a data-go="matrix">逐列 →</a></h4><div class="vcb-heat"><div></div>' + ST.map(function (s) { return '<div class="hd">' + s + '</div>'; }).join('');
      P.matrices.forEach(function (m) {
        var mx = Math.max(1, m.rows.length);
        h += '<div class="rn" data-go="matrix">' + dot(m.state) + ' ' + esc(m.zh) + '</div>' + ST.map(function (s) {
          var n = (m.counts || {})[s] || 0;
          return n ? '<div class="cell" style="background:' + COL[s] + ';opacity:' + (0.45 + 0.55 * n / mx).toFixed(2) + '">' + n + '</div>' : '<div class="cell z">·</div>';
        }).join('');
      });
      h += '</div></div>';
      // 運作摘要
      var r = P.run, c = r.counts || {};
      h += '<div class="vcb-card c5"><h4><span>最近一次運作(格子)</span><a data-go="results">逐站 →</a></h4>';
      if (!r.total) h += '<div class="vcb-empty">' + badge('NODATA') + '<br>' + esc(r.why) + '</div>';
      else {
        var parts = [{ k: 'OK', v: c.ok, c: 'var(--ok)' }, { k: 'FAIL', v: c.fail, c: 'var(--bad)' }, { k: 'SKIP', v: c.skip, c: 'var(--nd)' }, { k: 'TIMEOUT', v: c.timeout, c: 'var(--warn)' }];
        h += '<div class="vcb-donut">' + donut(parts, r.total, '站') + '<div class="vcb-lgd">' + parts.map(function (p) { return '<div><span class="vcb-dot" style="background:' + p.c + '"></span>' + p.k + ' <b>' + (p.v || 0) + '</b></div>'; }).join('') +
          '<div class="vcb-meta">' + esc(r.ts) + ' · ' + esc(Math.round(r.elapsed_s || 0)) + 's · 機器係數 ×' + esc(r.machine_factor) + '</div>' + badge(r.state) + '</div></div>';
      }
      h += '</div>';
      // 邏輯規範
      var L = P.logic, maxc = Math.max.apply(null, [1].concat(L.laws_by_cat.map(function (x) { return x[1]; })));
      h += '<div class="vcb-card c7"><h4><span>邏輯規範 · VRN 六層鏈</span><a data-go="logic">律條與層 →</a></h4><div class="vcb-flow">' +
        (L.layers.length ? L.layers.map(function (l) { return '<div class="vcb-step" title="' + esc(l.why) + '"><b>' + esc(l.id) + '</b><em>' + l.n + '</em> <span>節點</span></div>'; }).join('') : '<div class="vcb-empty">' + badge('ABSENT') + ' 邏輯冊讀不到</div>') +
        '</div><div class="vcb-meta" style="margin:10px 0 6px">政策律條 ' + L.laws.length + ' 條(依類別)· 規則正本 ' + L.rule_canons.length + ' · 待入冊 ' + L.off_book_pending + '</div><div class="vcb-bars">' +
        L.laws_by_cat.slice(0, 6).map(function (x) { return '<div class="vcb-bar"><span>' + esc(x[0]) + '</span><span class="tr"><i style="width:' + (100 * x[1] / maxc) + '%;background:linear-gradient(90deg,var(--accent),var(--accent2))"></i></span><span class="n">' + x[1] + '</span></div>'; }).join('') + '</div></div>';
      // 引擎總攬
      h += '<div class="vcb-card c5"><h4><span>引擎總攬</span><a data-go="engines">逐項 →</a></h4><div class="vcb-bars">' + P.families.map(function (f) {
        var ok = f.counts.in_place, n = Math.max(1, f.counts.items), miss = f.counts.items - ok;   // 各家族自己的在位率(滿格 = 全在位)
        return '<div class="vcb-bar" title="觸網 ' + f.counts.net + ' 項"><span>' + esc(f.zh) + '</span><span class="tr"><i style="width:' + (100 * ok / n) + '%;background:var(--ok)"></i><i style="width:' + (100 * miss / n) + '%;background:var(--bad)"></i></span><span class="n">' + ok + '/' + f.counts.items + '</span></div>';
      }).join('') + '</div>';
      var inv = P.inventory;
      h += '<div class="vcb-meta" style="margin:10px 0 6px">樹上盤點(系統總管 do_list)' + (inv.state === 'OK' ? '' : ' · ' + badge(inv.state) + ' ' + esc(inv.why)) + '</div><div class="vcb-src">' +
        Object.keys(inv.families || {}).map(function (k) { var v = inv.families[k]; return '<div><span>' + esc(k) + (v.retired ? '(退役)' : '') + '</span><b>' + v.count + '</b></div>'; }).join('') +
        (inv.state === 'OK' ? '<div><span>治理模組</span><b>' + inv.modules + '</b></div>' : '') + '</div></div>';
      // 資料庫(VIA_DBManager)
      var dov = dbOv(), dk = dov.kpi || {};
      h += '<div class="vcb-card c12"><h4><span>資料庫 · VIA_DBManager</span><a data-go="db">逐表 · 核對 · 計畫 →</a></h4>';
      if (dov.state === 'NODATA') h += '<div class="vcb-empty">' + badge('NODATA') + ' ' + esc(dov.catalog_why) + '</div>';
      else {
        var dst = dk.states || {}, dsum = Math.max(1, (dst.GREEN || 0) + (dst.AMBER || 0) + (dst.NODATA || 0) + (dst.RED || 0));
        h += '<div class="vcb-src" style="grid-template-columns:repeat(auto-fill,minmax(130px,1fr));margin-bottom:10px">' +
          [['正庫', dk.dbs], ['對帳副本', dk.replicas], ['表', dk.tables], ['列', Number(dk.rows || 0).toLocaleString()], ['最新日', dk.latest || '—'],
           ['湖檔', dk.lake_files], ['壞檔', dk.bad_files], ['目錄', (dov.catalog_ts || '').slice(0, 16) + (dov.stale ? ' · 過期' : '')]].map(function (x) { return '<div><span>' + esc(x[0]) + '</span><b>' + esc(x[1]) + '</b></div>'; }).join('') + '</div>' +
          '<div class="vcb-stack" title="正庫逐表狀態">' + ['GREEN', 'AMBER', 'NODATA', 'RED'].map(function (s) { return dst[s] ? '<i style="width:' + (100 * dst[s] / dsum) + '%;background:' + COL[s] + '" title="' + s + ' ' + dst[s] + '"></i>' : ''; }).join('') + '</div>' +
          '<div class="vcb-meta" style="margin-top:6px">' + ['GREEN', 'AMBER', 'NODATA', 'RED'].map(function (s) { return s + ' ' + (dst[s] || 0); }).join(' · ') + '</div>';
      }
      h += '</div>';
      // 錯誤摘要
      var top = P.errors.slice(0, 8);
      h += '<div class="vcb-card c7"><h4><span>錯誤摘要(紅 ' + errN + ' · 待裁 ' + P.errors.filter(function (e) { return e.sev === 'AMBER'; }).length + ')</span><a data-go="errors">全部 →</a></h4><div class="vcb-err">' +
        (top.length ? top.map(function (e) { return '<div>' + badge(e.sev) + '<span title="' + esc(e.text) + '"><b class="cl2">' + esc(e.id) + '</b> <span class="s">· ' + esc(e.source) + '</span><span class="cl2">' + esc(e.text) + '</span></span></div>'; }).join('') : '<div class="vcb-empty">' + badge('GREEN') + ' 沒有紅燈或待辦</div>') + '</div></div>';
      // 資料來源
      h += '<div class="vcb-card c5"><h4><span>資料來源(誠實四態)</span></h4><div class="vcb-src">' + Object.keys(P.sources).map(function (k) {
        var s = P.sources[k]; return '<div title="' + esc(s.path + ' ' + s.why) + '"><span>' + esc(s.zh) + '</span>' + badge(s.state === 'OK' ? 'GREEN' : s.state, s.state === 'OK' ? '可讀' : s.state) + '</div>';
      }).join('') + '</div></div></div>';
      return h;
    }
    function matrix() {
      var st = S.filt.m || '';
      return chips('m', [['RED', '只看紅'], ['AMBER', '只看待裁'], ['NODATA', '只看無料'], ['GREEN', '只看綠']]) + P.matrices.map(function (m) {
        var rows = m.rows.filter(function (r) { return !st || r.state === st; });
        return '<div class="vcb-card" style="margin-bottom:12px"><h4><span>' + dot(m.state) + ' ' + esc(m.zh) + ' <span class="vcb-meta">· 來源 ' + esc((P.sources[m.source] || {}).path || m.source) + '</span></span>' + badge(m.state) + '</h4>' +
          table(['id', '名稱', '狀態', '說明'], rows.map(function (r) { return ['<span class="vcb-mono">' + esc(r.id) + '</span>', esc(r.zh), badge(r.state), esc(r.note)]; })) + '</div>';
      }).join('');
    }
    function logic() {
      var L = P.logic, rows = L.laws.filter(function (r) { return hit('law', r.id + ' ' + r.cat + ' ' + r.key + ' ' + r.text); });
      return '<div class="vcb-grid" style="margin-top:0"><div class="vcb-card c12"><h4><span>VRN 六層邏輯(' + esc(L.built_at || '—') + ')</span></h4><div class="vcb-lay">' + L.layers.map(function (l) {
        return '<div class="vcb-card"><b>' + esc(l.id) + '</b> <span class="vcb-meta">' + l.n + ' 節點</span><div class="vcb-meta">' + esc(l.why) + '</div><ul>' +
          l.nodes.slice(0, 8).map(function (n) { return '<li>' + esc(n.role || n.family) + ' <span class="vcb-meta">' + esc(n.kind || '') + '</span></li>'; }).join('') + (l.nodes.length > 8 ? '<li class="vcb-meta">…另 ' + (l.nodes.length - 8) + '</li>' : '') + '</ul></div>';
      }).join('') + '</div></div><div class="vcb-card c12"><h4><span>政策律條(依位階)</span></h4>' + qbox('law', '搜尋律條(id / 類別 / 內容)') +
        table(['位階', 'id', '類別', '鍵', '內容'], rows.map(function (r) { return [esc(r.rank === null || r.rank === undefined ? '—' : r.rank), '<b>' + esc(r.id) + '</b>', esc(r.cat), '<span class="vcb-mono">' + esc(r.key) + '</span>', esc(r.text)]; })) + '</div></div>';
    }
    function engines() {
      var ff = S.filt.f || '';
      var rows = allItems().filter(function (x) { return (!ff || x.f.key === ff) && hit('eng', x.it.id + ' ' + x.it.zh + ' ' + x.it.engine); });
      return chips('f', P.families.map(function (f) { return [f.key, f.zh + ' ' + f.counts.in_place + '/' + f.counts.items]; })) + qbox('eng', '搜尋項目 / 引擎') +
        table(['家族', '項目', '尾版引擎', '在位', '版數', '觸網', '參數', '正主解析(冊上參數會跑的那一句)'], rows.map(function (x) {
          var it = x.it;
          return [esc(x.f.key.toUpperCase()), '<b class="cl2" title="' + esc(it.zh) + '">' + esc(it.zh) + '</b><span class="vcb-mono vcb-meta">' + esc(it.id) + '</span>', '<span class="vcb-mono">' + esc(it.engine || it.engine_glob) + '</span>',
            badge(it.engine_state), esc(it.versions || '—'), it.net ? badge('NET', '觸網') : '—',
            esc((it.params || []).map(function (c) { return c.key; }).concat((it.unsupported || []).map(function (u) { return u + '(不接)'; })).join(', ') || '—'),
            badge({ READY: 'GREEN', NODATA: 'NODATA', UNREADABLE: 'ABSENT' }[it.resolved_state] || 'AMBER', it.resolved_state) + ' <span class="vcb-mono">' + esc((it.resolved_argv || []).join(' ')) + '</span>' + (it.resolved_note ? '<div class="vcb-meta">' + esc(it.resolved_note) + '</div>' : '')];
        }));
    }
    function errors() {
      var sv = S.filt.e || '', rows = P.errors.filter(function (e) { return (!sv || e.sev === sv) && hit('err', e.id + ' ' + e.source + ' ' + e.text); });
      return chips('e', [['RED', '紅 ' + errN], ['AMBER', '待裁 ' + P.errors.filter(function (e) { return e.sev === 'AMBER'; }).length]]) + qbox('err', '搜尋錯誤 / 來源') +
        table(['等級', '來源', '項目', '說明', ''], rows.map(function (e) { return [badge(e.sev), esc(e.source), '<b>' + esc(e.id) + '</b>', esc(e.text), '<a class="vcb-chip" data-go="' + esc(e.tab) + '">看 →</a>']; }));
    }
    function results() {
      var r = P.run, sv = S.filt.r || '';
      if (!r.total) return '<div class="vcb-card"><div class="vcb-empty">' + badge('NODATA') + '<br>' + esc(r.why) + '</div></div>';
      var c = r.counts, rows = r.rows.filter(function (x) { return (!sv || x.state === sv) && hit('res', x.name + ' ' + x.note); });
      return '<div class="vcb-card" style="margin-bottom:12px"><h4><span>格子 ' + esc(r.file) + '</span>' + badge(r.state) + '</h4><div class="vcb-meta">' + esc(r.ts) + ' · ' + r.total + ' 站 · 耗時 ' + esc(Math.round(r.elapsed_s || 0)) + 's' + (r.fast ? ' · 快速模式' : '') + (r.interrupted ? ' · 中斷' : '') + '</div></div>' +
        chips('r', [['FAIL', 'FAIL ' + (c.fail || 0)], ['TIMEOUT', 'TIMEOUT ' + (c.timeout || 0)], ['SKIP', 'SKIP ' + (c.skip || 0)], ['OK', 'OK ' + (c.ok || 0)]]) + qbox('res', '搜尋站名 / 輸出') +
        table(['站', '狀態', '秒', '尾段'], rows.map(function (x) { var st = { OK: 'GREEN', FAIL: 'RED', SKIP: 'NODATA', TIMEOUT: 'AMBER' }[x.state] || 'NODATA'; return [esc(x.name), badge(st, x.state), esc(x.secs), '<span class="vcb-meta">' + esc(x.note) + '</span>']; }));
    }
    function dbTab() {
      var ov = dbOv(), D = P.db || {};
      if (ov.state === 'NODATA') return '<div class="vcb-card"><div class="vcb-empty">' + badge('NODATA') + '<br>' + esc(ov.catalog_why) + '<br><br>工作站:<code>via-datahome catalog -Tables</code> → 再建一次主控台</div></div>';
      var h = '<div class="vcb-card" style="margin-bottom:12px"><h4><span>目錄 ' + esc(ov.catalog_ts) + (ov.age_hours !== null && ov.age_hours !== undefined ? '(' + esc(ov.age_hours) + ' 小時前)' : '') + '</span>' + badge(ov.stale ? 'AMBER' : 'GREEN', ov.stale ? '目錄過期:重跑 via-datahome catalog' : '目錄新') + '</h4>' +
        table(['角色', '庫', '表', '列', '最新日', '狀態'], ov.dbs.map(function (d) {
          return [esc(d.role), '<b>' + esc(d.name) + '</b><div class="vcb-meta">' + esc(d.rel) + (d.mb !== undefined ? ' · ' + esc(d.mb) + ' MB' : '') + '</div>', esc(d.tables), esc(Number(d.rows).toLocaleString()), esc(d.latest || '—'),
            Object.keys(d.counts || {}).map(function (s) { return badge(s, s + ' ' + d.counts[s]); }).join(' ')];
        })) + '</div>';
      var sv = S.filt.d || '', rows = ov.tables.filter(function (t) { return (!sv || t.state === sv) && hit('dbt', t.db + ' ' + t.table); });
      h += '<div class="vcb-card" style="margin-bottom:12px"><h4><span>逐表(' + ov.tables.length + ')</span></h4>' + chips('d', [['RED', '紅'], ['AMBER', '薄 / 待看'], ['NODATA', '0 列'], ['GREEN', '綠']]) + qbox('dbt', '搜尋庫 / 表') +
        table(['庫', '表', '列', '日期欄', '範圍', '哨兵', '狀態'], rows.map(function (t) {
          return ['<span class="vcb-meta">' + esc(t.db) + (t.role !== '正庫' ? ' · ' + esc(t.role) : '') + '</span>', '<b>' + esc(t.table) + '</b>', esc(Number(t.rows).toLocaleString()), esc(t.date_col || '—'),
            esc(t.lo ? t.lo + ' → ' + t.hi : '—') + (t.iso_dates === false ? ' <span class="vcb-meta">(非西元)</span>' : ''), esc(t.sentinel || ''), badge(t.state)];
        })) + '</div>';
      var rc = (D.reconcile || []).filter(function (r) { return r.state !== 'GREEN'; });
      h += '<div class="vcb-card" style="margin-bottom:12px"><h4><span>數量核對:冊上期望 vs 目錄實量(非綠 ' + rc.length + ' / ' + (D.reconcile || []).length + ')</span></h4>' +
        table(['狀態', '庫', '表', '冊上次', '現在', '說明'], rc.map(function (r) { return [badge(r.state), esc(r.db), '<b>' + esc(r.table) + '</b>', esc(r.rows_seen === null ? '—' : Number(r.rows_seen).toLocaleString()), esc(r.rows_now === null ? '—' : Number(r.rows_now).toLocaleString()), esc(r.why)]; })) + '</div>';
      var pl = D.plans || {};
      h += '<div class="vcb-grid" style="margin-top:0"><div class="vcb-card c12"><h4><span>計畫 2 · 湖的 _raw 定位(只出計畫)</span></h4>' +
        table(['湖', '年檔列', '年檔範圍', '_raw 列', '_raw 範圍', '判定', '建議'], (pl.raw || []).map(function (x) {
          return ['<b>' + esc(x.family) + '</b>', esc(Number(x.year_rows).toLocaleString()), esc(x.year_lo + ' → ' + x.year_hi), esc(Number(x.raw_rows).toLocaleString()), esc(x.raw_lo + ' → ' + x.raw_hi),
            badge(x.verdict === 'FULL_DUP' ? 'RED' : x.verdict === 'RAW_SUPERSET' ? 'AMBER' : 'NODATA', x.verdict), esc(x.advice)];
        })) + '</div><div class="vcb-card c7"><h4><span>計畫 4 · mega 時間戳檔按年合併(只出計畫)</span></h4>' +
        table(['表', '檔數', '列(合併前)', '範圍', '合併成'], (pl.mega || []).map(function (x) {
          return ['<b>' + esc(x.stem) + '</b>', esc(x.files), esc(Number(x.rows_in).toLocaleString()), esc(x.lo ? x.lo + ' → ' + x.hi : '—'), '<span class="vcb-mono">' + esc(x.target) + '</span><div class="vcb-meta">' + esc(x.note) + '</div>'];
        })) + '</div><div class="vcb-card c5"><h4><span>計畫 5 · 讀不動的 parquet(' + (pl.bad || []).length + ')</span></h4>' +
        table(['湖', '檔', '錯誤'], (pl.bad || []).map(function (x) { return [esc(x.dataset), '<span class="vcb-mono">' + esc(x.file) + '</span>', '<span class="vcb-meta">' + esc(x.error) + '</span>']; })) +
        '<div class="vcb-meta" style="margin-top:8px">處置:移到隔離夾由操作員做(L10);計畫檔 <code>via-vcgc dbm plan</code> 寫到 VIA_Reports/dbmanager</div></div></div>';
      h += '<div class="vcb-card" style="margin-top:12px"><h4><span>湖(' + ov.lakes.length + ' 夾)</span></h4>' +
        table(['資料集', '類', '檔', '列', '範圍', '壞檔'], ov.lakes.map(function (x) {
          return ['<b>' + esc(x.dataset) + '</b>', esc(x.kind), esc(x.files), esc(Number(x.rows || 0).toLocaleString()), esc(x.lo ? x.lo + ' → ' + x.hi : '—') + (x.iso_dates === false ? ' <span class="vcb-meta">(非西元)</span>' : ''), x.bad ? badge('RED', x.bad + ' 壞') : '—'];
        })) + '</div>';
      return h;
    }
    function renderPane() {
      var t = P.layout.right.tabs.filter(function (x) { return x.id === S.tab; })[0] || P.layout.right.tabs[0];
      var body = { overview: overview, matrix: matrix, logic: logic, engines: engines, db: dbTab, errors: errors, results: results }[t.id];
      pane.innerHTML = '<p class="vcb-desc">' + esc(t.desc) + '</p>' + (body ? body() : '');
      root.setAttribute('data-vcb-tab', t.id);
    }
    renderLeft(); renderNav(); renderPane();
    window.VCB_MOUNTED = true;
    return { go: go, state: S };
  }
  window.VCB = { mount: mount, payload: function () { return JSON.parse(document.getElementById('vcb-payload').textContent); } };
})();"""


def _jsval(v) -> str:
    """JSON 進 <script>:每個 < 寫成 \\u003c(JSON 與 JS 都合法;</script> 與 <!-- 都不會讓頁提前收尾)。
    不用 VRN_ENG089 那種 <\\!-- 拆法:\\! 不是合法的 JSON 跳脫,JSON.parse 會整份讀不動。"""
    return json.dumps(v, ensure_ascii=False).replace("<", "\\u003c")


def render_page(bp: dict) -> str:
    pub = public(bp)
    return ("<!doctype html>\n<html lang=\"zh-Hant\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>VIA 中央主控台藍圖</title><meta name=\"generator\" content=\"{ENGINE_TAG}\">"
            "<style>html,body{margin:0;padding:0}" + STYLE + "</style></head><body>"
            "<div id=\"vcb-app\"></div>\n<script id=\"vcb-payload\" type=\"application/json\">" + _jsval(pub) + "</script>\n"
            "<script>\n" + APP_JS + "\n</script>\n<script>VCB.mount(document.getElementById('vcb-app'), VCB.payload(), {standalone: true});</script>\n"
            "</body></html>\n")


# ---------------------------------------------------------------- ③ 對接制式 U/I + synchronizer
CENTRAL_JS = r"""(function () {
  'use strict';
  var MID = __MODULE_ID__, NAME = __MODULE_NAME__, VERSION = __VERSION__, KEY = __KEY__, CHANNEL = __CHANNEL__, PAGE = __PAGE__;
  var P = null;
  try { P = JSON.parse(document.getElementById('vcb-payload').textContent); } catch (e) { P = null; }
  function esc(s) { return String(s === null || s === undefined ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function mod(state) {
    try { var st = state || JSON.parse(localStorage.getItem(KEY) || 'null'), ms = st && Array.isArray(st.modules) ? st.modules : [];
      for (var i = 0; i < ms.length; i++) { if (ms[i] && ms[i].id === MID) return ms[i]; } } catch (e) { }
    return null;
  }
  function mount(host) {
    host.className = 'vcb-dock'; host.replaceChildren();
    var css = document.createElement('style');
    css.textContent = '.vcb-dock{display:block;width:100%;font:12.5px/1.5 "Segoe UI","Noto Sans TC",system-ui,sans-serif}.vcb-dock [hidden]{display:none!important}'
      + '.vcb-dk{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin:8px 0}.vcb-dk div{border:1px solid #e2e8f0;border-radius:9px;padding:8px 10px;background:#fff;border-left:4px solid var(--t,#94a3b8)}'
      + '.vcb-dk b{display:block;font-size:18px}.vcb-dk span{font-size:11px;color:#64748b}.vcb-dh{display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap}'
      + '.vcb-dh a{font-weight:700;color:#2563eb;text-decoration:none;padding:5px 10px;border:1px solid #bfdbfe;border-radius:7px;background:#eff6ff}.vcb-dt{display:flex;gap:6px;flex-wrap:wrap}'
      + '.vcb-dt a{font-size:11.5px;color:#334155;text-decoration:none;padding:3px 9px;border-radius:14px;background:#f1f5f9}';
    host.appendChild(css);
    var box = document.createElement('div'), off = document.createElement('div');
    off.textContent = NAME + ' 已在 synchronizer 停用——到 synchronizer 頁把它勾回來(請用停用,不要刪)。';
    var tone = { ok: '#16a34a', warn: '#d97706', bad: '#dc2626', nd: '#94a3b8' };
    if (!P) box.textContent = '主控台藍圖資料讀不到(建構不完整);重跑 CGC_MDL227 build。';
    else box.innerHTML = '<div class="vcb-dh"><b>' + esc(NAME) + ' · v' + esc(VERSION) + '</b><span style="color:#64748b">' + esc(P.built_at) + '</span><a href="' + esc(PAGE) + '" target="_blank" rel="noopener">開啟全頁主控台 →</a></div>'
      + '<div class="vcb-dk">' + (P.kpis || []).map(function (k) { return '<div style="--t:' + (tone[k.tone] || '#94a3b8') + '"><span>' + esc(k.label) + '</span><b>' + esc(k.value) + '</b><span>' + esc(k.foot) + '</span></div>'; }).join('') + '</div>'
      + '<div class="vcb-dt">' + (P.layout.right.tabs || []).map(function (t, i) { return '<a href="' + esc(PAGE) + '#' + esc(t.id) + '" target="_blank" rel="noopener">' + (i + 1) + ' · ' + esc(t.zh) + '</a>'; }).join('') + '</div>';
    host.appendChild(box); host.appendChild(off);
    function apply(state) { var m = mod(state), on = !m || m.enabled !== false; box.hidden = !on; off.hidden = on; host.setAttribute('data-vcb-enabled', on ? '1' : '0'); }
    apply(null);
    try { var ch = new BroadcastChannel(CHANNEL); ch.onmessage = function (ev) { var d = ev && ev.data; if (d && d.type === 'via-state-v2' && d.state) apply(d.state); if (d && d.type === 'via-clear-v2') apply(null); }; } catch (e) { }
    window.addEventListener('storage', function (ev) { if (ev.key === KEY) apply(null); });
    window.VCB_DOCK_MOUNTED = true;
  }
  function register(left) {
    if (typeof window.VIA_REGISTER_ADDON === 'function') {
      var ok = false; try { ok = window.VIA_REGISTER_ADDON({ id: MID, name: NAME, version: VERSION, mount: mount }); } catch (e) { ok = false; }
      window.VCB_DOCK_REGISTERED = ok !== false; return;
    }
    if (left > 0) setTimeout(function () { register(left - 1); }, 50); else window.VCB_DOCK_REGISTERED = false;
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { register(200); }); else register(200);
})();"""

SYNC_JS = r"""(function () {
  'use strict';
  var MID = __MODULE_ID__, NAME = __MODULE_NAME__, VERSION = __VERSION__, PAGE = __PAGE__;
  var P = null;
  try { P = JSON.parse(document.getElementById('vcb-payload').textContent); } catch (e) { P = null; }
  function mount(host, api) {
    host.replaceChildren(); host.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px;align-items:center';
    var k = {}; ((P && P.kpis) || []).forEach(function (x) { k[x.id] = x.value; });
    var label = document.createElement('span');
    label.textContent = NAME + ' v' + VERSION + ' · 在位 ' + (k.items || '—') + ' · 格子 ' + (k.grid || '—') + ' · 紅/待裁 ' + (k.errors || '—');
    host.appendChild(label);
    var a = document.createElement('a'); a.href = PAGE; a.target = '_blank'; a.rel = 'noopener'; a.className = 'btn'; a.textContent = '開啟主控台'; host.appendChild(a);
    var btn = document.createElement('button'); btn.className = 'btn'; btn.type = 'button'; btn.textContent = '下載藍圖';
    btn.addEventListener('click', function () { if (api && typeof api.download === 'function') api.download('VIA_CONSOLE_BLUEPRINT.json', JSON.stringify(P, null, 2), 'application/json'); });
    host.appendChild(btn);
    window.VCB_SYNC_MOUNTED = true;
  }
  function register(left) {
    if (typeof window.VIA_REGISTER_SYNC_ADDON === 'function') {
      var ok = false; try { ok = window.VIA_REGISTER_SYNC_ADDON({ id: MID, name: NAME, version: VERSION, mount: mount }); } catch (e) { ok = false; }
      window.VCB_SYNC_REGISTERED = ok !== false; return;
    }
    if (left > 0) setTimeout(function () { register(left - 1); }, 50); else window.VCB_SYNC_REGISTERED = false;
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { register(200); }); else register(200);
})();"""


def _mark(block: str, edge: str) -> str:
    return "<!-- VCGC-CONSOLE-BLUEPRINT:" + block + ":" + edge + " -->"


def _fill(js: str, defaults: list) -> str:
    for k, v in (("__KEY__", STATE_KEY), ("__CHANNEL__", CHANNEL), ("__MODULE__", MODULE), ("__DEFAULTS__", defaults),
                 ("__MODULE_ID__", MODULE["id"]), ("__MODULE_NAME__", MODULE["name"]), ("__VERSION__", VERSION),
                 ("__PAGE__", PAGE_NAME)):
        js = js.replace(k, _jsval(v))
    return js


def _preseed_js(eng089) -> str:
    """synchronizer 模組冊預置:借 VRN_ENG089 尾版的 PRESEED 契約(同一段 JS),只換掉它自己的名字。"""
    src = getattr(eng089, "PRESEED_JS", "")
    if "__MODULE__" not in src or "__DEFAULTS__" not in src:
        raise ValueError("VRN_ENG089 尾版的 PRESEED_JS 不在或改版了(沒有 __MODULE__/__DEFAULTS__)")
    return src.replace("VRN_TEMPLATE_PRESEED", "VCB_PRESEED").replace("'VRN-TEMPLATE'", "'VCGC-CONSOLE-BLUEPRINT'")


def inject(html: str, pub: dict, defaults: list, role: str, preseed: str) -> str:
    """模板原文 + 插入段(<head> 之後:預置;</body> 之前:資料 + 外掛)。其餘一個字元都不動。launcher 只預置。"""
    head = re.search(r"<head\b[^>]*>", html, re.I)
    body_at = html.lower().rfind("</body>")
    if not head or body_at < 0:
        raise ValueError(f"{role} 找不到 <head> 或 </body>(模板改版了?)")
    pre = _mark("preseed", "BEGIN") + "\n<script>\n" + _fill(preseed, defaults) + "\n</script>\n" + _mark("preseed", "END")
    at = head.end()
    if role == "launcher":
        return html[:at] + pre + html[at:]
    tail = (_mark("addon", "BEGIN") + "\n<script id=\"vcb-payload\" type=\"application/json\">" + _jsval(pub) + "</script>\n<script>\n"
            + _fill(CENTRAL_JS if role == "centralUI" else SYNC_JS, defaults) + "\n</script>\n" + _mark("addon", "END"))
    return html[:at] + pre + html[at:body_at] + tail + html[body_at:]


def strip_injection(html: str) -> str:
    for block in ("preseed", "addon"):
        b, e = _mark(block, "BEGIN"), _mark(block, "END")
        i, j = html.find(b), html.find(e)
        if i >= 0 and j > i:
            html = html[:i] + html[j + len(e):]
    return html


def _write(p: Path, data: bytes) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".vcbtmp")
    tmp.write_bytes(data)
    os.replace(tmp, p)


def dock(bp: dict, out_dir: Path, template_root: Path | None = None) -> dict:
    """對接制式 U/I:三入口副本 + 插入段;模板原文零改動(寫前後比 sha)。"""
    eng = bp.get("_eng089")
    if eng is None:
        return {"state": "BLOCKED", "why": "VRN_ENG089 尾版載不到:沒有 PRESEED 契約與模板驗證可借(不另寫一份)", "pages": {}}
    troot = Path(template_root or TEMPLATE_ROOT)
    chk = eng.template_check(troot)
    if not chk.get("ok"):
        return {"state": "BLOCKED", "why": "制式模板驗不過:" + str(chk.get("why") or chk.get("rows")), "pages": {}}
    try:
        man = json.loads((troot / "manifest.json").read_text(encoding="utf-8"))
        ent = man["canonicalEntrypoints"]
        src = {role: (troot / ent[role]).read_bytes() for role in ROLES}
        defaults = eng.default_modules(src["synchronizer"].decode("utf-8"))
        preseed = _preseed_js(eng)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"state": "BLOCKED", "why": f"模板讀不動或改版:{type(exc).__name__}: {str(exc)[:120]}", "pages": {}}
    before = {role: hashlib.sha256(b).hexdigest() for role, b in src.items()}
    pub = public(bp)
    ui = Path(out_dir) / "ui"
    pages = {}
    for role in ROLES:
        html = inject(src[role].decode("utf-8"), pub, defaults, role, preseed)
        if strip_injection(html).encode("utf-8") != src[role]:
            return {"state": "BLOCKED", "why": f"{role} 拿掉插入段後不等於模板原文(插入會改到模板)", "pages": {}}
        name = Path(ent[role]).name
        _write(ui / name, html.encode("utf-8"))
        pages[role] = "ui/" + name
    _write(ui / PAGE_NAME, render_page(bp).encode("utf-8"))
    pages["console"] = "ui/" + PAGE_NAME
    after = {role: hashlib.sha256((troot / ent[role]).read_bytes()).hexdigest() for role in ROLES}
    return {"state": "DOCKED" if after == before else "BLOCKED", "pages": pages, "release": chk.get("release"),
            "module": MODULE["id"], "defaults": len(defaults),
            "why": "" if after == before else "模板原文在建構期間被改動(不是本支寫的;照實擋)"}


def build(out_dir: Path | None = None, template_root: Path | None = None, do_dock: bool = True, bp: dict | None = None) -> dict:
    out = Path(out_dir or OUT_DIR)
    bp = bp or collect()
    pub = public(bp)
    _write(out / BLUEPRINT_NAME, json.dumps(pub, ensure_ascii=False, indent=1).encode("utf-8"))
    _write(out / PAGE_NAME, render_page(bp).encode("utf-8"))
    res = {"state": "BUILT", "rc": 0, "out": str(out), "blueprint": BLUEPRINT_NAME, "page": PAGE_NAME,
           "sources_bad": [k for k, s in bp["sources"].items() if s["state"] != "OK"]}
    if do_dock:
        d = dock(bp, out, template_root)
        res["dock"] = d
        if d["state"] != "DOCKED":
            res["rc"] = 1
    return res


def status(out_dir: Path | None = None) -> dict:
    """最近一版還對嗎:藍圖記的來源 sha 對現在 → OK / STALE;沒建過 = NONE。零寫檔。"""
    out = Path(out_dir or OUT_DIR)
    old, row = _read_json(out / BLUEPRINT_NAME)
    if old is None:
        return {"state": "NONE" if row["state"] == "ABSENT" else "DRIFT", "rc": 2 if row["state"] == "ABSENT" else 1, "why": row["why"]}
    changed = []
    for k, s in (old.get("sources") or {}).items():
        if not s.get("sha") or not s.get("path"):
            continue                      # 模組 / 沒有 sha 的來源不比(每次收集都重載)
        p = Path(s["path"]) if Path(s["path"]).is_absolute() else VIA / s["path"]   # 照藍圖自己記的路徑重讀
        _, now = _read_json(p)
        if now["sha"] != s["sha"]:
            changed.append(k)
    return {"state": "STALE" if changed else "OK", "rc": 1 if changed else 0, "built_at": old.get("built_at"), "changed": changed}


# ---------------------------------------------------------------- 自測(沙盒:只寫暫存夾)
def _fake_template(root: Path) -> None:
    ui = root / "ui"
    ui.mkdir(parents=True)
    pages = {
        "launcher": "<!doctype html><html><head><meta charset=\"utf-8\"><title>L</title></head><body><a href=\"S.html\">s</a></body></html>\n",
        "centralUI": "<!doctype html><html><head><meta charset=\"utf-8\"></head><body><div id=\"addonSlotBody\"></div>"
                     "<script>window.VIA_REGISTER_ADDON=function(a){var h=document.createElement('div');a.mount(h,{});return true;};</script></body></html>\n",
        "synchronizer": "<!doctype html><html><head></head><body><script>const DEFAULT_MODULES=[{id:'m1',name:'甲',type:'dashboard',enabled:true}];"
                        "window.VIA_REGISTER_SYNC_ADDON=function(a){return true;};</script></body></html>\n",
    }
    names = {"launcher": "L.html", "centralUI": "C.html", "synchronizer": "S.html"}
    files = []
    for role, html in pages.items():
        b = html.encode("utf-8")
        (ui / names[role]).write_bytes(b)
        files.append({"path": "ui/" + names[role], "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
    (root / "manifest.json").write_text(json.dumps({"schema": "VIA.STANDARD.TEMPLATE", "release": "T",
                                                    "canonicalEntrypoints": {r: "ui/" + n for r, n in names.items()},
                                                    "files": files}), encoding="utf-8")


def selftest() -> int:
    print(f"=== {ENGINE_TAG} · 主控台藍圖自測(沙盒;零網路;不跑任何引擎)===")
    res = []

    def chk(name, ok, note=""):
        res.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        spec = {"param_kinds": {"start": "--start YYYY-MM-DD", "days": "--days N", "dir": "--dir <夾>"},
                "defaults": {"start": "2023-07-01", "days": 20},
                "user": {"starts": {"a1": "2024-01-02"}, "group_starts": {"g1": "2023-09-01"}, "days": {}, "vrn_dir": "C:\\樣本",
                         "tw_codes": {"TWSE": ["2330"], "TPEX": []}},
                "families": {"vdf": {"groups": [{"id": "g1", "zh": "群一", "items": [
                    {"id": "a1", "zh": "項一", "params": ["start", "days"], "net": True, "engine": {"glob": "X_v*.py"}},
                    {"id": "a2", "zh": "項二", "params": ["range", "weird"], "engine": {"glob": "Y_v*.py"}}]}]},
                    "vrn": {"input": {"dir_default": "in"}, "groups": [{"id": "p", "zh": "管線", "items": [
                        {"id": "b1", "zh": "報告", "params": ["dir"], "engine": {"glob": "Z_v*.py"}}]}]}}}
        sp = t / "spec.json"
        sp.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        bus_rows = [{"id": "a1", "engine": "X_v0102.py", "engine_state": "在位", "versions": 2},
                    {"id": "b1", "engine": "", "engine_state": "缺", "versions": 0}]

        class Bus:
            @staticmethod
            def catalog():
                return bus_rows

            @staticmethod
            def call(iid, params, apply=False, catalog_rows=None):
                assert apply is False
                return {"state": "PLAN", "argv": ["/usr/bin/python3", str(VIA / "e" / "X_v0102.py"), "run"]}

        # ① 參數冊 → 左面板(只給正主會接的鍵;提示值來自正主 effective_start)
        spec_l, _ = _read_json(sp)

        def fake_resolver(iid):
            if iid == "a1":
                return {"state": "READY", "argv": ["/usr/bin/python3", str(VIA / "e" / "X_v0102.py"), "run", "--start", "2024-01-02", "--days", "20"]}
            return {"state": "NEED_DIR", "argv": [], "note": "報告夾裡沒有報告件"}

        fams = collect_params(spec_l, bus_rows, lambda i: Bus.call(i, None) if i == "a1" else {}, fake_resolver,
                              lambda iid, gid: {"a1": "2024-01-02"}.get(iid) or {"g1": "2023-09-01"}.get(gid, ""))
        f_vdf = next(f for f in fams if f["key"] == "vdf")
        a1 = f_vdf["groups"][0]["items"][0]
        a2 = f_vdf["groups"][0]["items"][1]
        b1 = next(f for f in fams if f["key"] == "vrn")["groups"][0]["items"][0]
        k1 = [(c["key"], c["control"], c["placeholder"]) for c in a1["params"]]
        chk("① 左面板只從參數冊來、只給正主 resolve_argv 會接的鍵;起日提示 = 正主 effective_start(項目 > 群組 > 冊預設)",
            k1 == [("start", "date", "2024-01-02"), ("days", "number", "")] and a2["params"][0]["placeholder"] == "2023-09-01"
            and [c["key"] for c in b1["params"]] == ["dir"] and a1["net"] is True, f"{k1} · a2 {a2['params'][0]['placeholder']}")
        chk("② range 拆成 start / end 兩欄(不給 --range);正主不接的種類不給欄位、照實列出",
            [c["key"] for c in a2["params"]] == ["start", "end"] and a2["unsupported"] == ["weird"], f"{[c['key'] for c in a2['params']]} · 不接 {a2['unsupported']}")
        chk("③ 引擎在位 / PLAN 從 EngineBus;冊上參數會跑的那一句從正主 MDL139;路徑去機器前綴、python 不寫死",
            a1["engine_state"] == "GREEN" and b1["engine_state"] == "ABSENT" and a2["engine_state"] == "NODATA"
            and a1["plan_argv"] == ["python", "e/X_v0102.py", "run"]
            and a1["resolved_argv"] == ["python", "e/X_v0102.py", "run", "--start", "2024-01-02", "--days", "20"]
            and b1["resolved_state"] == "NEED_DIR" and "--' + c." not in APP_JS,
            f"{a1['resolved_argv']} · b1 {b1['resolved_state']}")
        missing = [f for f in fams if f["key"] == "vcgc"][0]
        chk("④ 參數冊少一個家族 → 那一家族 ABSENT(說原因),其餘照畫", missing["state"] == "ABSENT" and "central" in missing["why"])

        # ⑤ 四態:冊不在 / 壞 → 來源照實,矩陣 ABSENT 不當綠;格子沒有 → NODATA
        (t / "bad.json").write_text("{壞", encoding="utf-8")
        books = {k: t / "nope.json" for k in BOOKS}
        books["lock"] = t / "bad.json"
        bp = collect(sp, books, t / "nogrid", bus_mod=Bus, panorama=None, manager=None, eng089=None, load_live=False)
        mstate = {m["id"]: m["state"] for m in bp["matrices"]}
        chk("⑤ 誠實四態:冊不在=ABSENT · 壞 JSON=UNREADABLE · 矩陣不因缺冊變綠 · 沒有格子證據=NODATA",
            bp["sources"]["laws"]["state"] == "ABSENT" and bp["sources"]["lock"]["state"] == "UNREADABLE"
            and mstate["fixed"] == "ABSENT" and mstate["lock"] == "ABSENT" and bp["run"]["state"] == "NODATA"
            and bp["inventory"]["state"] == "ABSENT", f"{mstate} · run {bp['run']['state']}")

        # ⑥ 已修冊:全樹掃描類 → NODATA,不當綠;tail_contains 委派全景
        class Pano:
            @staticmethod
            def _verify_one(v, a, b):
                return ("GREEN", "憑據齊") if v.get("markers") == ["ok"] else ("RED", "少了")

        fx = {"entries": [{"id": "F1", "verify": [{"kind": "tail_contains", "markers": ["ok"]}]},
                          {"id": "F2", "verify": [{"kind": "class_zero", "cls": "ACCEL"}]},
                          {"id": "F3", "verify": [{"kind": "tail_contains", "markers": ["x"]}, {"kind": "class_zero"}]}]}
        ms = collect_matrices({"fixed": fx}, Pano, fams)
        fr = {r["id"]: r["state"] for r in ms[0]["rows"]}
        chk("⑥ 已修冊:尾版憑據委派全景 _verify_one;全樹掃描類=NODATA(不代跑、不當綠);一條紅整列紅",
            fr == {"F1": "GREEN", "F2": "NODATA", "F3": "RED"} and ms[0]["state"] == "RED", str(fr))

        # ⑦ 格子 → 運作摘要 + 錯誤摘要(紅在前)
        gd = t / "grid"
        gd.mkdir()
        (gd / "GRID_20260101_000000.json").write_text(json.dumps({"ts": "old", "total": 1, "ok": 1, "results": []}), encoding="utf-8")
        (gd / "GRID_20260928_010101.json").write_text(json.dumps({
            "ts": "20260928_010101", "total": 3, "ok": 1, "fail": 1, "skip": 0, "timeout": 1,
            "results": [{"name": "甲站", "state": "OK", "secs": 1}, {"name": "乙站", "state": "FAIL", "secs": 2, "note": "壞了"},
                        {"name": "丙站", "state": "TIMEOUT", "secs": 9}]}), encoding="utf-8")
        run, _ = collect_run(gd)
        errs = collect_errors(ms, run, {}, fams)
        chk("⑦ 運作摘要讀最新一份格子(照檔名時間);FAIL→紅、TIMEOUT→待裁;錯誤摘要紅在前、逐條帶來源",
            run["ts"] == "20260928_010101" and run["state"] == "RED" and errs and errs[0]["sev"] == "RED"
            and any(e["id"] == "乙站" and e["sev"] == "RED" for e in errs) and any(e["id"] == "丙站" and e["sev"] == "AMBER" for e in errs)
            and any(e["id"] == "b1" and e["tab"] == "engines" for e in errs), f"{run['state']} · 前 3 {[(e['sev'], e['id']) for e in errs[:3]]}")

        # ⑧ 分頁:總覽第一、結果最後;總覽六塊都在頁裡
        tabs = [x["id"] for x in bp["layout"]["right"]["tabs"]]
        page = render_page(bp)
        chk("⑧ 右面板分頁:① 總覽 … ⑦ 執行結果(結果放最後;v0101 資料庫分頁在錯誤之前);總覽 = KPI · 矩陣 · 運作 · 邏輯 · 引擎 · 錯誤 · 來源",
            tabs[0] == "overview" and tabs[-1] == "results" and len(tabs) == 7 and tabs.index("db") == tabs.index("errors") - 1
            and all(s in APP_JS for s in ("矩陣狀況", "最近一次運作", "邏輯規範", "引擎總攬", "錯誤摘要", "資料來源")), str(tabs))

        # ⑨ 頁:零外部資源;資料不會提前收尾 <script>
        bp_x = dict(bp)
        bp_x["errors"] = [{"sev": "RED", "source": "x", "id": "</script><script>alert(1)</script>", "text": "<!--", "tab": "errors"}]
        page_x = render_page(bp_x)
        payload = page_x.split('<script id="vcb-payload" type="application/json">', 1)[1].split("</script>", 1)[0]
        chk("⑨ 單頁零外部資源(無 http(s) 的 src/href);資料裡的 </script> 與 <!-- 被拆開,載回來原字不變",
            not re.search(r"(src|href)=[\"']https?://", page) and "</script><script>alert" not in payload
            and json.loads(payload)["errors"][0]["id"] == "</script><script>alert(1)</script>")

        # ⑩ 對接:模板原文零改動;拿掉插入段 = 原文;預置模組與 DEFAULT_MODULES 從模板抽
        troot = t / "tpl"
        _fake_template(troot)
        before = {p.name: p.read_bytes() for p in (troot / "ui").iterdir()}

        class Eng:
            PRESEED_JS = ("(function(){var KEY=__KEY__,MOD=__MODULE__,DEFAULTS=__DEFAULTS__;"
                          "window.VRN_TEMPLATE_PRESEED='X';var s='VRN-TEMPLATE';})();")

            @staticmethod
            def template_check(root):
                m = json.loads((Path(root) / "manifest.json").read_text(encoding="utf-8"))
                ok = all(hashlib.sha256((Path(root) / f["path"]).read_bytes()).hexdigest() == f["sha256"] for f in m["files"])
                return {"ok": ok, "release": m.get("release"), "why": "" if ok else "sha 不對"}

            @staticmethod
            def default_modules(html):
                return [{"id": "m1", "name": "甲", "type": "dashboard", "enabled": True}]

        bp["_eng089"] = Eng
        out = t / "out"
        r = build(out, troot, True, bp)
        after = {p.name: p.read_bytes() for p in (troot / "ui").iterdir()}
        c_html = (out / "ui" / "C.html").read_text(encoding="utf-8")
        s_html = (out / "ui" / "S.html").read_text(encoding="utf-8")
        l_html = (out / "ui" / "L.html").read_text(encoding="utf-8")
        chk("⑩ 對接制式 U/I:三入口副本 + 全頁主控台;模板原文位元組零改動;拿掉插入段 = 原文;中央頁掛 VIA_REGISTER_ADDON、"
            "synchronizer 掛 VIA_REGISTER_SYNC_ADDON、launcher 只預置;預置模組 id 與 DEFAULT_MODULES 從模板來",
            r["dock"]["state"] == "DOCKED" and before == after
            and strip_injection(c_html).encode("utf-8") == before["C.html"] and strip_injection(l_html).encode("utf-8") == before["L.html"]
            and "VIA_REGISTER_ADDON" in c_html and "VIA_REGISTER_SYNC_ADDON" in s_html and "vcb-payload" not in l_html
            and MODULE["id"] in l_html and "'m1'" not in c_html and '"m1"' in c_html and "VRN_TEMPLATE_PRESEED" not in c_html
            and (out / "ui" / PAGE_NAME).is_file() and (out / BLUEPRINT_NAME).is_file(), f"{r['dock'].get('pages')}")
        # 反面:模板 sha 對不上 / ENG089 缺 → BLOCKED,不寫半套
        (troot / "ui" / "C.html").write_text("<html><head></head><body>改過</body></html>", encoding="utf-8")
        r_bad = dock(bp, t / "out2", troot)
        bp["_eng089"] = None
        r_none = dock(bp, t / "out3", troot)
        chk("⑪ 反面控制:模板被改(sha 對不上)→ BLOCKED 不寫;ENG089 載不到 → BLOCKED 並講原因(不另寫一份預置契約)",
            r_bad["state"] == "BLOCKED" and not (t / "out2" / "ui").exists() and r_none["state"] == "BLOCKED" and "ENG089" in r_none["why"],
            f"{r_bad['why'][:40]} · {r_none['why'][:40]}")
        st = status(out)
        chk("⑫ status:剛建好 = OK(來源 sha 對得上);沒建過 = NONE rc2", st["state"] == "OK" and status(t / "none")["state"] == "NONE",
            str(st))

    # ⑬ 活樹唯讀收集:四家族都在參數冊、每項在匯流排目錄;零寫檔
    snap = {p: p.stat().st_mtime_ns for p in [SPEC, *BOOKS.values()] if p.exists()}
    live = collect()
    fams_ok = {f["key"]: f["state"] for f in live["families"]}
    n_items = sum(f["counts"]["items"] for f in live["families"])
    live_items = [it for f in live["families"] for g in f["groups"] for it in g["items"]]
    th = next((it for it in live_items if it["id"] == "tw_history"), None)
    chk("⑬ 活樹:正主解析出來的指令沒有任何一項帶 --range(ENG064 不認);tw_history 冊上參數 = --start … --end …",
        not any("--range" in it["resolved_argv"] for it in live_items)
        and (th is None or th["resolved_state"] != "READY" or ("--start" in th["resolved_argv"] and "--end" in th["resolved_argv"])),
        f"tw_history {th['resolved_state'] if th else '不在'} {' '.join(th['resolved_argv'][2:]) if th else ''}")
    chk("⑭ 活樹唯讀收集:VCGC/VDF/VRN/VAP 四家族都從參數冊來 · 每一項都有匯流排判定 · 收集不寫任何冊",
        all(v == "OK" for v in fams_ok.values()) and n_items > 0
        and all(it["engine_state"] in ("GREEN", "ABSENT", "NODATA") for f in live["families"] for g in f["groups"] for it in g["items"])
        and snap == {p: p.stat().st_mtime_ns for p in snap},
        f"{fams_ok} · {n_items} 項 · 收集 {live['collect_secs']}s · 來源不可讀 {[k for k, s in live['sources'].items() if s['state'] != 'OK']}")
    # ⑮ v0101:DB 家族 / 資料庫分頁吃 VIA_DBManager 的統一輸出(沙盒家:正主 MDL123 catalog → MDL228 ui_payload;不碰真庫)
    dbm, e1 = _load(_tail(HERE, "CGC_MDL228_VIADBManager_v*.py"), "vcb_dbm_selftest")
    dh, e2 = _load(_tail(HERE, "CGC_MDL123_DataHome_v*.py"), "vcb_dh_selftest")
    if dbm is None or dh is None:
        chk("⑮ v0101 資料庫分頁接 VIA_DBManager", False, f"載不到:{e1 or e2}")
    else:
        try:
            import duckdb  # noqa: F401
            has_duck = True
        except Exception:
            has_duck = False
        if not has_duck:
            print("  [SKIP] ⑮ 本環境沒有 duckdb:沙盒家建不了(誠實 SKIP)")
        else:
            with tempfile.TemporaryDirectory() as td4:
                t4 = Path(td4)
                home = dbm._mk_home(t4)
                cat = dh.catalog(via=t4, home=str(home), do_print=False, write=False)
                sp4 = t4 / "spec.json"
                sp4.write_text(json.dumps({"families": {}}), encoding="utf-8")
                nob = {k: t4 / "nope.json" for k in BOOKS}
                bpd = collect(sp4, nob, t4 / "nogrid", load_live=False, db_payload=dbm.ui_payload(cat))
                bpn = collect(sp4, nob, t4 / "nogrid", load_live=False, db_payload=dbm.ui_payload(None, "ABSENT", "目錄頁不在"))
                pg = render_page(bpd)
                mrec = next((m for m in bpd["matrices"] if m["id"] == "db_reconcile"), None)
                chk("⑮ v0101 DB 家族 / 資料庫分頁吃 VIA_DBManager 統一輸出:正庫與對帳副本分開 · 核對進矩陣 · 匯出指令經 via-vcgc dbm export(先乾跑);目錄不在 = NODATA 照實",
                    bpd["db"]["overview"]["kpi"]["dbs"] == 1 and bpd["db"]["overview"]["kpi"]["replicas"] == 1 and mrec is not None
                    and "via-vcgc dbm export" in pg and "--dry" in pg and bpn["db"]["overview"]["state"] == "NODATA"
                    and next(m for m in bpn["matrices"] if m["id"] == "db_reconcile")["state"] == "NODATA"
                    and bpd["sources"]["db_catalog"]["state"] == "OK" and bpn["sources"]["db_catalog"]["state"] == "ABSENT",
                    f"正庫 {bpd['db']['overview']['kpi']['dbs']} · 副本 {bpd['db']['overview']['kpi']['replicas']} · 核對 {len(mrec['rows']) if mrec else 0} 列")
    ok = sum(res)
    print(f"  [計] {len(res)} 檢 OK {ok} · FAIL {len(res) - ok}")
    return 0 if ok == len(res) else 1


# ---------------------------------------------------------------- CLI
def _arg(args: list, flag: str):
    return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else None


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if "--selftest" in args or args[0] == "selftest":
        return selftest()
    verb = args[0]
    if verb == "blueprint":
        bp = collect()
        pub = public(bp)
        if "--json" in args:
            print(json.dumps(pub, ensure_ascii=False, indent=1))
            return 0
        print(f"[{ENGINE_TAG}] 收集 {pub['collect_secs']}s")
        for k in pub["kpis"]:
            print(f"  {k['label']}:{k['value']}  ({k['foot']})")
        bad = {k: s["state"] for k, s in pub["sources"].items() if s["state"] != "OK"}
        print(f"  來源:{len(pub['sources'])} 個 · 不可讀 {bad or '無'}")
        print(f"  分頁:{' → '.join(t['zh'] for t in pub['layout']['right']['tabs'])}")
        return 0
    if verb == "build":
        out = _arg(args, "--out")
        troot = _arg(args, "--template-root")
        r = build(Path(out) if out else None, Path(troot) if troot else None, "--no-dock" not in args)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return r["rc"]
    if verb == "status":
        r = status(Path(_arg(args, "--out")) if _arg(args, "--out") else None)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return r["rc"]
    print(f"不認得的動詞:{verb}(build / blueprint / status / --selftest)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
