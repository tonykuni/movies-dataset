#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
v0101→v0102(批689B 操作員令「與總管系統 SSOT REGEX 同義字 上傳更新只增不減不衝突 整合好」):
  +第八域 **同義字(ssot)**:總管視角讀 CGC_MDL176 聯集冊(只增不減 tally · 拒絕 · 正典鍵對映裁定 · 沒過閘的活支)
  與 SUP_MDL749 增補冊(多義=候操作員裁定 · 候選=REVIEWABLE 未安裝)。只讀冊與模組自報,**不重算聯集、不寫任何冊**。
  燈:冊在=GREEN(待裁定是候,不是壞;逐項印出);MDL176 缺=ABSENT;聯集冊缺=NODATA。入 rc 範圍(RC_SCOPE)。廿七檢 +㉖㉗。

VRN_SystemManager v0101 — VRN 子系統管理對接口(批681 立;批682 雙模式 + 兩線紀錄索引)
v0100→v0101(批682 操作員令「將這兩個 session 的 VRN 資訊全數擷取過來;這個系統單獨處理 VRN,可為獨立系統可為子系統;VRN_SystemManager 掌握上下對接」):
  ① 雙模式:`mode()` 現量——VCGC(VIA 唯一對接口)在位且載得起=**subsystem**(子系統:五面/七處/掉球經 VCGC 讀);不在或 `--standalone`=**standalone**
     (獨立系統:四庫+鏈快照+交接照讀,尾版家族改自家 glob 並講明,VIA 的面一律標 STANDALONE 不代讀、不猜)。兩種模式六域都要能讀,自測㉓ 兩種都跑。
  ② +records 域(read records / `records` 動詞):兩線 VRN 紀錄**索引**——血脈由 git 尾註 `Claude-Session:` 量出來(哪個 session · 幾筆 commit · 批號範圍),
     VRN 文(docs 檔名含 VRN 或提及 ≥8 次)、收容包(references/intake 逐夾)、活線(遠端分支);全部是指標不是複本(L05)。
  ③ +㉓㉔㉕ 三檢(雙模式 · 紀錄索引 · 側線件在位:ENG088 / SUP_MDL749≥v0111 / 單元測試);廿二→廿五檢。

VRN_SystemManager v0100 — VRN 子系統管理對接口(批681;操作員令「設立 VRN_SystemManager.py 上下銜接 VIA,管理子系統的政策/邏輯/因子/參數;以後讀取就從 VIA 往下透過 VRN_System 作為管理對接口;自適應、智慧化、上下資訊自動更新的連結」)

位置:VIA ─(L20 唯一對接口 VCGC CGC_MDL149)─► **本口** ─► VRN 四庫 + 引擎面 + 交接
  上行(向 VIA 報):六域燈 · 連結表 · 七處自審 · 快照 VIA_Reports/vrn_system/VRN_SYSTEM_latest.json
                  (VCGC v0118 起 logic()/factors() 一律經本口 read();對接口缺席=ABSENT 誠實,不退回舊路)
  下行(管 VRN):政策 policy(律/lessons 的 VRN 子集 · ENG082 政策因子)
               邏輯 logic (VIA_VRN_LogicArchitecture 索引冊 + 守門(委派 via_vrn_logic_book.do_check)· ENG082 邏輯庫 LOGIC_latest)
               因子 factor(SUP_MDL748 policy_rows;AllInOne + FDS 兩本冊)
               參數 param (via_params_central.BOOKS 的 VRN 子集 + 各樞紐**自報**的中央冊常數:SUP_MDL749.SSOT / CGC_MDL176.UNION_OUT / CGC_MDL115.OUTJ / 疊加層 / 正典)
               引擎 engine(六層鏈最新一跑(讀 MDL172 快照,不重跑)· 尾版家族(同 VCGC._tail_files 一把尺)· 規格/格子/短令/Deck/元件冊 五面)
               交接 handover(ENG082 交接三處 hash · 逐批紀錄 · 掉球清單 · 一頁交接批號 vs 律冊批號)

自適應連結(不是一本會過期的冊):每一條連結都在**呼叫當下**現解尾版(L04)、現算 sha、現量年齡;
  `sync` 對上一次快照逐條判 NEW / CHANGED / GONE / SAME;快照只落 VIA_Reports(不入 git),`--apply` 才寫。
Zero-Hydra(L05):本口**不複製**任何規則或參數——政策讀律冊、邏輯呼叫索引冊守門與 ENG082、因子呼叫 SUP_MDL748、
  參數子集取自 via_params_central.BOOKS(抄到函式才算出處,LL316)、引擎五面呼叫 VCGC 的讀器;同一判準只寫一處。
誠實四態(L16)+ 兩態:GREEN / NODATA(缺料)/ GATED(閘)/ ABSENT(缺件)/ STALE(過期:指標非尾版、一頁比律冊舊)/ RED(壞)。
  缺件≠缺料≠過期≠壞掉:六層鏈在容器判 RED 的那些站,本口分列「import 缺件 / 缺料 / 其餘」——**不改鏈跑器的燈,只把它拆開講**(LL324 尺只講它量過的事)。
  本口 rc 只看四庫+交接的連結(冊在不在、守門綠不綠、一頁過不過期);引擎面的燈是鏈跑器的判準,照抄不折進 rc。
零網路 · 零寫庫 · 零 CDN · 預設只讀(status/catalog/links/read 一個位元都不寫;sync --apply 只寫 VIA_Reports/vrn_system)。
自測零污染(L17):VIA_SELFTEST=1 期間快照夾由 VIA_VRNSYS_REPORTS 指向暫存,真 VIA_Reports 一個位元不動。

用法:python3 VRN_SystemManager_v0101.py [status|catalog|links|records|read <policy|logic|factor|param|engine|handover|records|upstream> [key] [--full]|sync [--apply]|page] [--json] [--standalone] | --selftest
  rc:0 GREEN · 1 RED(冊缺 / 守門紅 / 讀器炸)· 2 STALE 或 NODATA(過期或缺料——不是壞)
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
# 綁定不是再定義一支 def(LL143):讀=utf-8-sig · 缺檔/壞檔都回 None(本口對兩者都誠實標 ABSENT/BROKEN)。
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

HERE = Path(__file__).resolve().parent            # functional modules/VRN
VIA = HERE.parent.parent
ROOT = VIA.parent
REG = VIA / "supportive modules" / "registry"
RULES = VIA / "supportive modules" / "70_VRN_Rules"
SSOT_DIR = VIA / "supportive modules" / "ssot"
ME = Path(__file__).stem                          # VRN_SystemManager_v0100
FAMILY = ME.rsplit("_v", 1)[0]                    # VRN_SystemManager
VERSION = ME.rsplit("_v", 1)[-1]                  # 由檔名讀出(尾版律;寫死會爛 LL:批586)
VIA_TAG = f"{FAMILY} v{VERSION}"
BORN = "批681"
DOMAINS = ("policy", "logic", "factor", "param", "engine", "handover", "records", "ssot")
DOMAIN_ZH = {"policy": "政策", "logic": "邏輯", "factor": "因子", "param": "參數", "engine": "引擎", "handover": "交接", "records": "紀錄", "ssot": "同義字"}
BATCHES = "批681→批682"
_FORCE_STANDALONE = {"on": False}   # --standalone:硬把 VIA 當成不在(自測㉓ 也走這裡)
RC_SCOPE = ("policy", "logic", "factor", "param", "handover", "ssot")   # 引擎面的燈是鏈跑器的判準,不折進本口 rc;批689B +同義字
LAMPS = {"GREEN": "綠", "NODATA": "缺料", "GATED": "閘", "ABSENT": "缺件", "STALE": "過期", "RED": "壞"}
VRN_DIRS = ("functional modules/VRN", "supportive modules/70_VRN_Rules")
SEVEN = ("spec", "grid", "register", "deck", "manager", "inventory", "handover")


def REPORTS() -> Path:
    """快照夾。自測期間由 VIA_VRNSYS_REPORTS 指向暫存(L17 零污染)。"""
    o = os.environ.get("VIA_VRNSYS_REPORTS")
    return Path(o) if o else (VIA / "VIA_Reports" / "vrn_system")


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


_ABSENT_RX = re.compile(r"ModuleNotFoun|No module named|ImportError|缺件|缺席|不可用|不在位|缺[(=]|套件缺")   # ModuleNotFoun:鏈跑器的 detail 會截斷,截斷了也要認得出
_NODATA_RX = re.compile(r"誠實停|無報告|沒有自測門|缺料|NODATA|無可轉檔|0 件|件 0")
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
    spec = importlib.util.spec_from_file_location(f"vrnsys_{key}", path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[f"vrnsys_{key}"] = m
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(m)
    _MODS[k] = m
    return m


def _vcgc():
    if _FORCE_STANDALONE["on"]:
        return None
    return _mod("vcgc", newest(REG, "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"))


def mode() -> str:
    """獨立系統 / 子系統(批682):VCGC 在位且載得起=subsystem;不在或 --standalone=standalone。現量,不是設定。"""
    if _FORCE_STANDALONE["on"]:
        return "standalone"
    try:
        return "subsystem" if _vcgc() is not None else "standalone"
    except Exception:
        return "standalone"


def _book_mod():
    return _mod("book", newest(REG, "via_vrn_logic_book_v*.py"))


def _eng082():
    return _mod("eng082", newest(HERE, "VRN_ENG082_ExtractionLogic_v*.py"))


def _m748():
    return _mod("m748", newest(RULES, "SUP_MDL748_FinancialLogicHub_v*.py"))


def _params_central():
    return _mod("vpc", newest(REG, "via_params_central_v*.py"))


def _is_vrn_path(s) -> bool:
    s = str(s).replace("\\", "/")
    return any(d in s for d in VRN_DIRS)


# ────────────────────────── 下行六域(只讀) ──────────────────────────
def read_policy(key: str | None = None) -> dict:
    p = newest(REG, "VIA_Policy_Laws_SSOT_v*.json")
    j = _json(p) if p else None
    if not j:
        return {"state": "ABSENT", "why": "supportive modules/registry/VIA_Policy_Laws_SSOT_v*.json 缺", "via": VIA_TAG}
    laws, lessons = list(j.get("laws") or []), list(j.get("lessons") or [])

    def _vrn(x):
        return "VRN" in (str(x.get("cat") or "") + str(x.get("zh") or ""))
    out = {"state": "GREEN", "src": p.name, "path": rel(p), "sha12": sha12(p), "age_h": age_h(p),
           "batch": j.get("batch"), "ts": j.get("ts"), "laws": len(laws), "lessons": len(lessons),
           "vrn_laws": [x.get("id") for x in laws if _vrn(x)], "vrn_lessons": [x.get("id") for x in lessons if _vrn(x)],
           "last_law": (laws[-1].get("id") if laws else None), "last_lesson": (lessons[-1].get("id") if lessons else None), "via": VIA_TAG}
    try:
        m = _eng082()
        out["policy_rows"] = len(m.policy_factors()) if m else None
    except Exception as exc:
        out["policy_rows"] = f"BROKEN {type(exc).__name__}"
    if key:
        hit = next((x for x in laws + lessons if str(x.get("id", "")).upper() == key.upper()), None)
        out["key"], out["hit"] = key, hit
        if not hit:
            out["state"], out["why"] = "NODATA", f"{key} 不在律冊(律 {len(laws)} · lessons {len(lessons)})"
    return out


def read_logic(key: str | None = None) -> dict:
    """索引冊 + 守門(委派)+ ENG082 邏輯庫。回傳形狀與 VCGC v0117 logic() 相容(state/src/files/verdicts/backends/broken/policy_rows/sync/handover)。"""
    out = {"state": "OK", "via": VIA_TAG}
    bp = REG / "VIA_VRN_LogicArchitecture_SSOT_v0100.json"
    bj = _json(bp)
    if not bj:
        book = {"state": "ABSENT", "path": rel(bp)}
    else:
        layers = bj.get("layers") or {}
        book = {"state": "GREEN", "path": rel(bp), "sha12": sha12(bp), "age_h": age_h(bp), "version": bj.get("version"),
                "built_by": bj.get("built_by"), "built_at": bj.get("built_at"), "batch": bj.get("batch"), "layers": len(layers),
                "pointers": sum(len(v.get("nodes") or []) for v in layers.values() if isinstance(v, dict)),
                "off_book_pending": len(bj.get("off_book_pending") or []), "known_gaps": len(bj.get("known_gaps") or [])}
    guard = {"state": "ABSENT", "why": "supportive modules/registry/via_vrn_logic_book_v*.py 缺"}
    try:
        bm = _book_mod()
        if bm:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = bm.do_check()
            line = next((ln.strip() for ln in buf.getvalue().splitlines() if "指標" in ln), "")
            guard = {"state": "GREEN" if rc == 0 else "RED", "rc": rc, "line": line, "src": Path(bm.__file__).name}
    except Exception as exc:
        guard = {"state": "RED", "why": f"{type(exc).__name__}:{str(exc)[:80]}"}
    p = newest(HERE, "VRN_ENG082_ExtractionLogic_v*.py")
    if not p:
        out.update({"state": "ABSENT", "why": "functional modules/VRN/VRN_ENG082_ExtractionLogic_v*.py 缺"})
    else:
        try:
            m = _eng082()
            d = m.load_latest()
            files = d.get("files") or {}
            by: dict = {}
            for r in files.values():
                by[r.get("verdict")] = by.get(r.get("verdict"), 0) + 1
            out.update({"src": p.name, "files": len(files), "verdicts": by,
                        "backends": {k: v.get("state") for k, v in (d.get("backends") or {}).items()},
                        "broken": list(m.broken_backends()), "policy_rows": len(m.policy_factors())})
            try:
                ss = m.sync_state(quiet=True)
                out["sync"] = {"hash": ss.get("hash"), "counts": dict(ss.get("counts") or {}), "dbs": len(ss.get("dbs") or [])}
            except Exception as exc:
                out["sync"] = {"state": f"BROKEN {type(exc).__name__}"}
            try:
                out["handover"] = m.handover_copies(quiet=True)
            except Exception:
                pass
            out["latest"] = "OK" if files else "NODATA"     # 件 0 = 缺料(容器),不是壞
        except Exception as exc:
            out.update({"state": f"BROKEN {type(exc).__name__}:{str(exc)[:60]}"})
    out["book"], out["guard"] = book, guard
    if out["state"] == "OK" and guard.get("state") == "RED":
        out["state"] = "RED"
    if out["state"] == "OK" and book["state"] == "ABSENT":
        out["state"] = "ABSENT"
    if key:
        table = {"book": book, "guard": guard, "latest": {k: out.get(k) for k in ("files", "verdicts", "backends", "broken", "sync", "latest")}}
        out["key"], out["hit"] = key, table.get(key)
        if out["hit"] is None:
            out["why"] = f"{key} 不是 logic 的鍵(book|guard|latest)"
    return out


def read_factor(key: str | None = None) -> dict:
    """SUP_MDL748 policy_rows。回傳形狀與 VCGC v0117 factors() 相容(state/src/rows/by_source/mounts)。"""
    p = newest(RULES, "SUP_MDL748_FinancialLogicHub_v*.py")
    if not p:
        return {"state": "ABSENT", "why": "supportive modules/70_VRN_Rules/SUP_MDL748_FinancialLogicHub_v*.py 缺", "via": VIA_TAG}
    try:
        m = _m748()
        rows = m.policy_rows()
        by: dict = {}
        for r in rows:
            by[r["source"]] = by.get(r["source"], 0) + 1
        m.allinone()
        m.fds()
        out = {"state": "OK" if rows else "NODATA", "src": p.name, "path": rel(p), "sha12": sha12(p), "rows": len(rows),
               "by_source": by, "mounts": dict(m._M.get("why") or {}), "via": VIA_TAG}
        if key:
            sub = [r for r in rows if key.lower() in (str(r.get("source", "")) + " " + str(r.get("key", ""))).lower()]
            out["key"], out["hits"], out["hit"] = key, len(sub), (sub[:20] or None)
            if not sub:
                out["state"], out["why"] = "NODATA", f"{key} 在 {len(rows)} 列政策因子裡零命中"
        return out
    except Exception as exc:
        return {"state": f"BROKEN {type(exc).__name__}", "src": p.name, "via": VIA_TAG}


def param_books() -> list:
    """VRN 參數冊清單 = via_params_central.BOOKS 的 VRN 子集(抄到函式才算出處 LL316)+ 各樞紐**自報**的中央冊常數。"""
    books, seen = [], set()
    try:
        vpc = _params_central()
    except Exception:
        vpc = None
    for b in (getattr(vpc, "BOOKS", None) or []):
        s = (str(b.get("id", "")) + " " + str(b.get("path", ""))).upper()
        if "VRN" in s and b.get("path") not in seen:
            books.append({"id": b["id"], "path": b["path"], "domain": b.get("domain"), "src": "via_params_central.BOOKS", "note": b.get("note", "")})
            seen.add(b["path"])
    hubs = []
    for key, pat, const, note in (("m749", "SUP_MDL749_VRNFieldRuleHub_v*.py", "SSOT", "中央規則正本(六欄規則樞紐 SUP_MDL749.SSOT)"),
                                  ("m176", "CGC_MDL176_SynonymUnion_v*.py", "UNION_OUT", "同義字聯集冊(批678;CGC_MDL176.UNION_OUT)"),
                                  ("m115", "CGC_MDL115_SSOTRegexDict_v*.py", "OUTJ", "SSOT Regex 中央冊(批628;CGC_MDL115.OUTJ)")):
        folder = RULES if key == "m749" else REG
        try:
            m = _mod(key, newest(folder, pat))
            if m is not None and getattr(m, const, None):
                hubs.append((pat.split("_v*")[0].split("_", 2)[-1].upper() + "_" + const, Path(getattr(m, const)), f"{pat.split('_v*')[0]}.{const}", note))
        except Exception:
            pass
    ov = newest(SSOT_DIR, "VIA_FinancialInstitution_Overlay_v*.json")
    if ov:
        hubs.append(("VIA_FININST_OVERLAY", ov, "ssot glob 尾版", "金融機構疊加層(操作員裁決層;拒絕清單先行)"))
    hubs.append(("VIA_FININST_SSOT", SSOT_DIR / "VIA_Financial_Institution_SSOT_v0100.json", "正典 READ_ONLY(L22)", "金融機構正典(唯讀;零觸碰)"))
    for hid, hp, src, note in hubs:
        r = rel(hp)
        if r not in seen:
            books.append({"id": hid, "path": r, "domain": "HUB", "src": src, "note": note})
            seen.add(r)
        else:   # 同一本冊兩個出處(名冊 + 樞紐常數):只增不減,兩個出處都留,不去重成一個
            for b in books:
                if b["path"] == r:
                    b.setdefault("also_src", []).append(src)
    return books


def _book_summary(j) -> str:
    if isinstance(j, dict):
        return " · ".join(f"{k}={len(v) if isinstance(v, (list, dict)) else str(v)[:24]}" for k, v in list(j.items())[:8])
    if isinstance(j, list):
        return f"list {len(j)}"
    return type(j).__name__


def read_param(key: str | None = None, full: bool = False) -> dict:
    rows = []
    for b in param_books():
        p = VIA / b["path"]
        r = dict(b)
        r["exists"] = p.is_file()
        if r["exists"]:
            r.update({"state": "GREEN", "sha12": sha12(p), "size": p.stat().st_size, "age_h": age_h(p)})
        else:
            r["state"] = "ABSENT"
        rows.append(r)
    absent = [r["id"] for r in rows if r["state"] == "ABSENT"]
    out = {"state": "GREEN" if (rows and not absent) else ("ABSENT" if absent else "NODATA"), "books": rows, "n": len(rows), "absent": absent, "via": VIA_TAG}
    if key:
        hit = next((r for r in rows if r["id"].upper() == key.upper() or r["path"].endswith(key)), None)
        out["key"], out["hit"] = key, hit
        if not hit:
            out["state"], out["why"] = "NODATA", f"{key} 不在 VRN 參數冊清單({len(rows)} 本;read param 看清單)"
        elif hit["exists"]:
            j = _json(VIA / hit["path"])
            hit["summary"] = _book_summary(j)
            if full:
                hit["content"] = j
    return out


def _head1(p: Path) -> str:
    try:
        for ln in p.read_text(encoding="utf-8", errors="replace").splitlines()[:14]:
            t = ln.strip().strip('"').strip("r").strip('"').strip()
            if t and not t.startswith(("#!", "# -*-", "#", '"""', "r'''")) and len(t) > 12:
                return re.sub(r"\s+", " ", t)[:160]
    except Exception:
        pass
    return ""


def read_engine(key: str | None = None) -> dict:
    out = {"state": "NODATA", "via": VIA_TAG}
    cp = VIA / "VIA_Reports" / "vrn_chain" / "VRNCHAIN_latest.json"
    cj = _json(cp)
    if not cj:
        out["chain"] = {"state": "NODATA", "why": "VIA_Reports/vrn_chain/VRNCHAIN_latest.json 不在(via-vrnchain run)", "src": rel(cp)}
    else:
        stages = [s for s in (cj.get("stages") or []) if isinstance(s, dict)]
        split = {"ABSENT": 0, "NODATA": 0, "RED": 0, "GATED": 0}
        for st in stages:
            if str(st.get("state")) == "RED":
                c = classify(1, str(st.get("detail", "")) + " " + str(st.get("fix", "")))
                split[c] = split.get(c, 0) + 1
        out["chain"] = {"state": str(cj.get("rc_name") or "?"), "generated": cj.get("generated"), "age_h": age_h(cp), "tally": cj.get("tally") or {},
                        "stages": len(stages), "red_split": split, "book": cj.get("book"), "mode": cj.get("mode"), "src": rel(cp),
                        "data": {k: (cj.get("data") or {}).get(k) for k in ("ok", "why", "n_reports")}}
        out["state"] = lamp_of(out["chain"]["state"])
    fams: dict = {}
    try:
        v = _vcgc()
        for stem, q in (v._tail_files() if v else {}).items():
            if _is_vrn_path(q):
                fams[stem] = rel(q)
        out["families_ruler"] = "VCGC._tail_files"
    except Exception:
        pass
    if not fams:
        for d in VRN_DIRS:
            for q in sorted((VIA / d).glob("*_v????.py")):
                fams[re.sub(r"_v\d{4}$", "", q.stem)] = rel(q)      # sorted → 後者覆蓋前者 = 尾版
        out["families_ruler"] = "own glob(standalone:VIA 不在,講明)"
    faces: dict = {}
    try:
        v = _vcgc()
        if v is None:
            raise LookupError("STANDALONE")
        sp = v.spec_items()
        faces["spec"] = [i["id"] for i in sp.get("items", []) if i.get("family") == "vrn"]
        gr = v.grid_stations()
        faces["grid"] = [s["name"][:48] for s in gr.get("stations", []) if _is_vrn_path(s.get("path", "")) or "VRN" in s.get("name", "")]
        rg = v.register_cmds()
        faces["register"] = [c["cmd"] for c in rg.get("cmds", []) if "vrn" in c["cmd"].lower() or "VRN" in str(c.get("usage") or "")]
        dk = v.deck_tasks()
        faces["deck"] = [k for k, t in dk.get("tasks", {}).items() if "vrn" in k.lower() or any(w in str(t.get("zh", "")) for w in ("VRN", "研報", "研究報告"))]
        inv = v.component_registry()
        faces["inventory_active"] = sum(1 for r in inv.get("records", []) if r.get("state", "ACTIVE") == "ACTIVE" and _is_vrn_path(r.get("source", "")))
    except LookupError:
        faces["state"] = "STANDALONE:VIA 不在,五面(規格/格子/短令/Deck/元件冊)是 VIA 的面,不代讀不猜"
    except Exception as exc:
        faces["state"] = f"ABSENT VCGC {type(exc).__name__}"
    out["mode"] = mode()
    # 批682 操作員令「實測樣本(隨時更新):C:\\測試樣本報告」:樣本夾只讀冊上 user.vrn_dir(報告夾律唯一正本=MDL139;--dir > user.vrn_dir > dir_default),
    #   本口不另存一份路徑;在不在本機現量——工作站路徑在容器 ABSENT 是誠實,不是壞。
    sp_ = _json(REG / "VIA_InputConsole_Spec_v0100.json") or {}
    vrn_dir = str(((sp_.get("user") or {}).get("vrn_dir") or "")).strip()
    dflt = str((((sp_.get("families") or {}).get("vrn") or {}).get("input") or {}).get("dir_default") or "")
    here = Path(vrn_dir) if vrn_dir else (VIA / dflt if dflt else None)
    n_files = sum(1 for q in here.iterdir() if q.is_file()) if (here and here.is_dir()) else None
    out["samples"] = {"vrn_dir": vrn_dir or f"(未設;冊 dir_default {dflt})", "src": "VIA_InputConsole_Spec user.vrn_dir(via-console set vrn-dir=)",
                      "state": ("GREEN" if n_files else ("NODATA" if here and here.is_dir() else "ABSENT")), "files_here": n_files,
                      "why": ("" if (here and here.is_dir()) else "本機不在(工作站路徑;隨時更新,由操作員維護)")}
    out["families"], out["families_detail"] = len(fams), fams
    out["faces"] = {k: (len(v) if isinstance(v, list) else v) for k, v in faces.items()}
    out["faces_detail"] = {k: v for k, v in faces.items() if isinstance(v, list)}
    if key:
        fam = next((f for f in fams if f.upper() == key.upper() or f.upper().startswith(key.upper())), None)
        if fam:
            q = VIA / fams[fam]
            out["key"], out["hit"] = key, {"family": fam, "tail": fams[fam], "sha12": sha12(q), "age_h": age_h(q), "head": _head1(q),
                                          "in_spec": any(fam in str(i) for i in faces.get("spec", [])) or fam.lower() in json.dumps(faces.get("spec", [])).lower(),
                                          "in_grid": any(fam in n for n in faces.get("grid", [])), "in_register": any(fam.lower()[:12] in c for c in faces.get("register", []))}
        else:
            out["key"], out["hit"], out["why"] = key, None, f"{key} 不是 VRN 尾版家族({len(fams)} 族)"
    return out


def read_handover() -> dict:
    out = {"state": "GREEN", "via": VIA_TAG}
    try:
        m = _eng082()
        out["copies"] = m.handover_copies(quiet=True) if m else {"state": "ABSENT"}
    except Exception as exc:
        out["copies"] = {"state": f"BROKEN {type(exc).__name__}"}
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
            m = re.search(r"批(\d+)", p.read_text(encoding="utf-8", errors="replace")[:400])
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
    nums = [int(m.group(1)) for q in VIA.glob("docs/VIA_B*_*.md") for m in [re.match(r"VIA_B(\d+)", q.name)] if m]
    out["latest_b_doc"] = max(nums) if nums else None
    if ob is None:
        out["state"], out["why"] = "ABSENT", "docs/VIA_Handover_ONEPAGE.md 缺或無批號"
    elif lawb and ob < lawb:
        out["state"], out["why"] = "STALE", f"一頁交接 批{ob} < 律冊 批{lawb}(L15 三處同一份但都舊;via-vcgc page --publish 未跑)"
    elif out["onepage"]["same"] is False:
        out["state"], out["why"] = "STALE", "docs ONEPAGE 與倉根 VIA_HANDOVER_LATEST.md 不同一份(L15)"
    return out


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
        out["vcgc"] = {"src": Path(v.__file__).name, "version": getattr(v, "VERSION", "?"), "delegates": callable(getattr(v, "_vrnsys", None))}
        try:
            out["spec"] = any(i.get("id") == "vrn_system" for i in v.spec_items().get("items", []))
            out["grid"] = any(FAMILY in str(s.get("path", "")) for s in v.grid_stations().get("stations", []))
            out["register"] = any(c.get("cmd") == "via-vrnsys" for c in v.register_cmds().get("cmds", []))
            out["deck"] = "vrn_system" in v.deck_tasks().get("tasks", {})
            out["manager"] = FAMILY in (v.manager_names().get("engines") or {})
            rec = next((r for r in v.component_registry().get("records", []) if r.get("identity") == FAMILY and r.get("state", "ACTIVE") == "ACTIVE"), None)
            out["inventory"] = (rec or {}).get("code") or False
        except Exception as exc:
            out["faces_error"] = type(exc).__name__
    else:
        out.setdefault("vcgc", "ABSENT")
    mp = newest(VIA, "VIA_SYSTEM_MANAGER_v*.py")
    out["via_manager"] = mp.name if mp else "ABSENT"
    docs = sorted(VIA.glob("docs/VIA_B*_*.md"))[-20:]
    out["handover"] = any(FAMILY in q.read_text(encoding="utf-8", errors="replace") for q in docs)
    out["seven"] = {k: out.get(k, False) for k in SEVEN}
    out["done"] = sum(1 for k in SEVEN if out.get(k))
    return out


# ────────────────────────── 紀錄索引(批682:兩線 VRN 資訊,指標不複本) ──────────────────────────
def _git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return ""


def lineage(limit: int = 600) -> dict:
    """血脈由 git 尾註量出來:每個 Claude-Session 幾筆 commit、批號範圍、最新/最早主題(newest-first)。"""
    raw = _git("log", "--all", f"-n{limit}", "--format=%H%x1f%s%x1f%b%x1e")
    sessions: dict = {}
    for rec in raw.split("\x1e"):
        parts = rec.strip("\n").split("\x1f")
        if len(parts) < 3:
            continue
        sha, subj, body = parts[0].strip(), parts[1].strip(), parts[2]
        m = re.search(r"Claude-Session:\s*https?://\S+/(session_[A-Za-z0-9]+)", body)
        sid = m.group(1) if m else "(無 Claude-Session 尾註)"
        s = sessions.setdefault(sid, {"commits": 0, "batch_hits": [], "latest": subj[:72], "earliest": subj[:72], "shas": []})
        s["commits"] += 1
        s["earliest"] = subj[:72]
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
        try:
            n = q.read_text(encoding="utf-8", errors="replace").count("VRN")
        except Exception:
            continue
        if "VRN" in q.name or n >= 8:
            rows.append({"doc": (rel(q) if str(q).startswith(str(VIA)) else "../docs/" + q.name), "vrn_mentions": n, "sha12": sha12(q), "age_h": age_h(q), "bytes": q.stat().st_size})
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
    out["lines"] = {"current": _git("rev-parse", "--abbrev-ref", "HEAD").strip(), "remote_heads": len(heads), "vrn_named": [h for h in heads if "vrn" in h.lower()]}
    if not out["lineage"]:
        out["state"], out["why"] = "NODATA", "git log 讀不到(不是倉或歷史為空)"
    if key:
        table = {"lineage": out["lineage"], "docs": out["docs"], "intake": out["intake"], "lines": out["lines"]}
        out["key"], out["hit"] = key, table.get(key)
        if out["hit"] is None:
            out["why"] = f"{key} 不是 records 的鍵(lineage|docs|intake|lines)"
    return out


# ────────────────────────── 連結 · 快照 · 差異 ──────────────────────────
def read_ssot(key: str | None = None) -> dict:
    """批689B:同義字(總管視角)。聯集冊 VIA_SSOT_SynonymUnion(CGC_MDL176 產)+ 樞紐增補冊(SUP_MDL749 additive)。
    只讀冊與模組自報:不重算聯集、不寫冊。待裁定的東西逐項端上來(多義/候選/沒過閘),它們是候,不是壞。"""
    out: dict = {"state": "ABSENT", "via": VIA_TAG, "union": {}, "additive": {}, "pending": {}, "why": ""}
    m176 = newest(REG, "CGC_MDL176_SynonymUnion_v*.py")
    if m176 is None:
        out["why"] = "CGC_MDL176_SynonymUnion_v*.py 缺席(聯集閘=同義字唯一寫入口)"
        return out
    out["src"] = m176.name
    book = REG / "VIA_SSOT_SynonymUnion_v0100.json"
    d = None
    if book.is_file():
        try:
            d = json.loads(book.read_text(encoding="utf-8"))
        except Exception:
            d = None
    if not d:
        out["state"], out["why"] = "NODATA", f"聯集冊 {book.name} 不在(先 via-py vrn CGC_MDL176 status 產冊)"
    else:
        rul = d.get("rulings") or []
        out["union"] = {"path": rel(book), "batch": d.get("batch"), "ts": d.get("ts"), "tally": d.get("tally"),
                        "counts": d.get("counts"), "rulings": len(rul),
                        "rulings_by_kind": _count(r.get("kind") or r.get("state") for r in rul),
                        "deny": len(d.get("deny") or []), "deny_leak": len(d.get("deny_leak") or []),
                        "gate_bypass": list(d.get("gate_bypass") or []), "unverified": len(d.get("unverified") or []),
                        "book_defects": len(d.get("book_defects") or [])}
        out["state"] = "GREEN"
    # 樞紐增補冊(多義=按來源可判,裁定權在操作員;候選=未安裝)
    hub = newest(VIA / "supportive modules" / "70_VRN_Rules", "SUP_MDL749_VRNFieldRuleHub_v*.py")
    add_: dict = {"state": "ABSENT", "why": "SUP_MDL749 缺席"}
    if hub is not None:
        try:
            mod = _mod("vrn_hub_for_sysmgr", hub)
            A = mod.additive_library()
            if A.get("state") == "OK":
                cf = mod.additive_conflicts(A["lib"])
                cd = mod.additive_candidates(lib=A["lib"], path=A["path"])
                sc = mod.additive_scopes(A["lib"])
                add_ = {"state": "OK", "book": Path(A["path"]).name, "keys": sum(sc.values()), "scopes": len(sc),
                        "polysemy": cf.get("n"), "candidates": len(cd.get("candidates") or []), "candidates_state": cd.get("state")}
            else:
                add_ = {"state": A.get("state"), "why": A.get("why")}
            bg = getattr(mod, "broker_gate", None)
            add_["broker_gate"] = bg() if bg else {"state": "ABSENT", "why": "樞紐 < v0112 無 broker_gate"}
        except Exception as exc:
            add_ = {"state": "RED", "why": f"樞紐讀不動 {type(exc).__name__}:{str(exc)[:60]}"}
    out["additive"] = add_
    out["pending"] = {"多義待裁定": add_.get("polysemy"), "候選未安裝": add_.get("candidates"),
                      "沒過拒絕閘的活支": len(out["union"].get("gate_bypass") or []),
                      "拒絕清單": out["union"].get("deny"), "正典鍵對映裁定": (out["union"].get("rulings_by_kind") or {}).get("KEY_ALIAS")}
    if key:
        return {"state": out["state"], "key": key, "value": out.get(key), "via": VIA_TAG}
    return out


def _count(it) -> dict:
    c: dict = {}
    for k in it:
        c[str(k)] = c.get(str(k), 0) + 1
    return c


def links(s: dict) -> list:
    """全部上下連結攤成一列一條(現解、現算、現量;不釘版號)。"""
    L: list = []

    def add(kind, id_, path, state, **kw):
        p = None
        if path:
            p = Path(path) if str(path).startswith("/") or (len(str(path)) > 1 and str(path)[1] == ":") else (VIA / path)
        L.append({"kind": kind, "id": id_, "path": (rel(p) if p else ""), "state": lamp_of(state),
                  "sha12": (sha12(p) if p and p.is_file() else ""), "age_h": (age_h(p) if p and p.is_file() else None), **kw})
    po = s["policy"]
    add("book", "policy:laws", po.get("path"), po.get("state"), domain="policy", batch=po.get("batch"))
    lo = s["logic"]
    add("book", "logic:index", lo["book"].get("path"), lo["book"].get("state"), domain="logic", version=lo["book"].get("version"))
    add("guard", "logic:guard", "", lo["guard"].get("state"), domain="logic", line=lo["guard"].get("line") or lo["guard"].get("why"))
    add("engine", "logic:ENG082", ("functional modules/VRN/" + lo["src"]) if lo.get("src") else "", lo.get("state"), domain="logic", latest=lo.get("latest"))
    fa = s["factor"]
    add("engine", "factor:SUP_MDL748", fa.get("path"), fa.get("state"), domain="factor", rows=fa.get("rows"))
    for b in s["param"]["books"]:
        add("book", "param:" + b["id"], b["path"], b["state"], domain="param", src=b["src"])
    en = s["engine"]
    add("report", "engine:chain", en["chain"].get("src"), en["chain"].get("state"), domain="engine", tally=en["chain"].get("tally"), red_split=en["chain"].get("red_split"))
    for fam, path in sorted((en.get("families_detail") or {}).items()):
        add("engine", "engine:" + fam, path, "GREEN", domain="engine")
    sm = en.get("samples") or {}
    L.append({"kind": "input", "id": "engine:samples", "path": str(sm.get("vrn_dir", "")), "state": lamp_of(sm.get("state")), "sha12": "", "age_h": None, "domain": "engine", "files_here": sm.get("files_here")})
    ho = s["handover"]
    add("doc", "handover:onepage", "docs/VIA_Handover_ONEPAGE.md", ho.get("state"), domain="handover", batch=(ho.get("onepage") or {}).get("docs_batch"))
    add("doc", "handover:root", str(ROOT / "VIA_HANDOVER_LATEST.md"), ho.get("state"), domain="handover", batch=(ho.get("onepage") or {}).get("root_batch"))
    for r in (s.get("records") or {}).get("docs") or []:
        add("doc", "records:" + Path(r["doc"]).name, r["doc"] if not r["doc"].startswith("../") else str(ROOT / r["doc"][3:]), "GREEN", domain="records", vrn_mentions=r["vrn_mentions"])
    for r in (s.get("records") or {}).get("intake") or []:
        add("intake", "records:intake:" + r["intake"], "functional modules/VRN/references/intake/" + r["intake"], "GREEN", domain="records", files=r["files"])
    ss = s.get("ssot") or {}
    add("engine", "ssot:CGC_MDL176", ("supportive modules/registry/" + ss["src"]) if ss.get("src") else "", ("GREEN" if ss.get("src") else "ABSENT"), domain="ssot")
    add("book", "ssot:union", (ss.get("union") or {}).get("path"), ss.get("state"), domain="ssot", tally=(ss.get("union") or {}).get("tally"), gate_bypass=len((ss.get("union") or {}).get("gate_bypass") or []))
    add("book", "ssot:additive", "", (ss.get("additive") or {}).get("state"), domain="ssot", polysemy=(ss.get("additive") or {}).get("polysemy"), candidates=(ss.get("additive") or {}).get("candidates"))
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
    s: dict = {"schema": "VIA.VRN.SystemManager.v1", "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "me": ME, "version": VERSION, "born": BORN}
    s["policy"], s["logic"], s["factor"] = read_policy(), read_logic(), read_factor()
    s["param"], s["engine"], s["handover"] = read_param(), read_engine(), read_handover()
    s["records"] = read_records()
    s["ssot"] = read_ssot()                                                  # 批689B 第八域
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
    prev = _json(REPORTS() / "VRN_SYSTEM_latest.json") or {}
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
def to_markdown(s: dict) -> str:
    o = [f"# VRN 子系統管理對接口 · {VIA_TAG}({BORN})· {s['ts']}", "",
         f"> 上接 VIA(VCGC {((s['upstream'].get('vcgc') or {}) if isinstance(s['upstream'].get('vcgc'), dict) else {}).get('src', 'ABSENT')})· 下管 VRN 四庫 + 引擎面 + 交接 · 本口 rc {s['rc']} {s['rc_name']}(只看四庫+交接;引擎面照抄鏈跑器)· 連結 {len(s['links'])} · {s['link_counts']}", "",
         "## 一 · 六域現況", "", "| 域 | 燈 | 正本 / 讀法 | 現況 |", "|---|---|---|---|"]
    po, lo, fa, pa, en, ho = (s[d] for d in ("policy", "logic", "factor", "param", "engine", "handover"))   # records 另讀(批682 七域)
    o.append(f"| 政策 | {s['lamps']['policy']} | {po.get('path', '')} · read policy [id] | 律 {po.get('laws')} · lessons {po.get('lessons')} · VRN 律 {len(po.get('vrn_laws') or [])} · VRN lessons {len(po.get('vrn_lessons') or [])} · 批 {po.get('batch')} · 尾 {po.get('last_law')}/{po.get('last_lesson')} · 政策因子 {po.get('policy_rows')} |")
    o.append(f"| 邏輯 | {s['lamps']['logic']} | {lo['book'].get('path', '')} + {lo.get('src', 'ENG082 缺')} · read logic book/guard/latest | 索引 {lo['book'].get('version')} 層 {lo['book'].get('layers')} 指標 {lo['book'].get('pointers')} · 守門 {lo['guard'].get('state')} {lo['guard'].get('line') or lo['guard'].get('why') or ''} · 邏輯庫 件 {lo.get('files')} {lo.get('verdicts')} · 同步 {lo.get('sync')} |")
    o.append(f"| 因子 | {s['lamps']['factor']} | {fa.get('path', '')} · read factor [字] | {fa.get('rows')} 列 {fa.get('by_source')} · 掛載 {fa.get('mounts')} |")
    o.append(f"| 參數 | {s['lamps']['param']} | via_params_central.BOOKS VRN 子集 + 樞紐自報 · read param [id] [--full] | 冊 {pa.get('n')} · 缺 {pa.get('absent')} |")
    ch = en.get("chain") or {}
    sm = en.get("samples") or {}
    o.append(f"| 樣本 | {lamp_of(sm.get('state'))} | 冊 user.vrn_dir(via-console set vrn-dir=)· 實測樣本夾隨時更新 | {sm.get('vrn_dir')} · 本機檔數 {sm.get('files_here')} · {sm.get('why') or '在位'} |")
    o.append(f"| 引擎 | {s['lamps']['engine']}(鏈跑器判準) | VIA_Reports/vrn_chain/VRNCHAIN_latest.json · read engine [family] | 鏈 {ch.get('state')} {ch.get('tally')} · RED 拆:{ch.get('red_split')} · 尾版家族 {en.get('families')}({en.get('families_ruler')})· 五面 {en.get('faces')} |")
    op = ho.get("onepage") or {}
    rc_ = s.get("records") or {}
    o.append(f"| 紀錄 | {s['lamps'].get('records', '-')} | git 尾註 + docs + references/intake · read records [lineage|docs|intake|lines] | session {len(rc_.get('lineage') or {})} · VRN 文 {len(rc_.get('docs') or [])} · 收容包 {len(rc_.get('intake') or [])} · 活線 {(rc_.get('lines') or {}).get('remote_heads')} · 模式 {s.get('mode')} |")
    o.append(f"| 交接 | {s['lamps']['handover']} | ENG082 三處 + docs + 掉球 · read handover | 一頁 批{op.get('docs_batch')} vs 律冊 批{op.get('laws_batch')} 同 {op.get('same')} · 逐批 {ho.get('latest_batch_doc')} · B 文 {ho.get('latest_b_doc')} · 掉球 {ho.get('dropped_balls')} · {ho.get('why', '')} |")
    _ss = s.get("ssot") or {}
    _su, _sa, _sp = _ss.get("union") or {}, _ss.get("additive") or {}, _ss.get("pending") or {}
    o.append(f"| 同義字 | {s['lamps'].get('ssot', '-')} | CGC_MDL176 聯集冊 + SUP_MDL749 增補冊 · read ssot [union|additive|pending] | 聯集 {_su.get('tally')} · 拒 {_su.get('deny')} · 裁定 {_su.get('rulings_by_kind')} · 沒過閘 {len(_su.get('gate_bypass') or [])} 支 · 多義 {_sa.get('polysemy')} · 候選 {_sa.get('candidates')} · 券商閘 {(_sa.get('broker_gate') or {}).get('state')}(待裁定=候不是壞) |")
    up = s["upstream"]
    o += ["", "## 一之二 · 兩線血脈(git 尾註量出來的;批682)", "", "| session | commit | 批號範圍 | 最新主題 |", "|---|---|---|---|"]
    for sid, v in sorted((rc_.get("lineage") or {}).items(), key=lambda kv: -kv[1].get("commits", 0)):
        o.append(f"| {sid} | {v.get('commits')} | {v.get('batch_min')}–{v.get('batch_max')}({v.get('batched_commits')}) | {v.get('latest')} |")
    o += ["", "## 二 · 上行七處自審(不假綠)", "", "| 處 | 在 | 說明 |", "|---|---|---|"]
    zh = {"spec": "規格項 vrn_system", "grid": "格子站(newest VRN_SystemManager_v*)", "register": "短令 via-vrnsys(L70 未許可前=否)", "deck": "Deck 任務 vrn_system", "manager": "Manager 正式名稱", "inventory": "中央元件冊(registry-sync --apply 後有號)", "handover": "交接段(docs/VIA_B*)"}
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
    o += ["", "## 律", "", "- L20 唯一對接口:VIA 往下讀 VRN 一律經本口;本口不複製任何規則(L05)。",
          "- L16 缺件≠缺料≠過期≠壞掉:鏈跑器的 RED 本口拆成 import 缺件 / 缺料 / 其餘,燈不改、只拆開講。",
          "- L04 尾版律:每一條連結呼叫當下現解,不釘版號;L17 自測零污染;零網路 · 零寫庫 · 零 CDN。"]
    return "\n".join(o) + "\n"


def to_html(s: dict, md: str, out: Path) -> Path:
    """矩陣式報告(批672 規格):能借 CGC_MDL173 的殼與表就借(同一份 css),借不到就自帶最小殼;兩條路都零 CDN。"""
    rows6 = []
    for d in DOMAINS:
        x = s[d]
        rows6.append([DOMAIN_ZH[d], {"t": s["lamps"][d], "s": s["lamps"][d]}, str(x.get("why") or x.get("path") or x.get("src") or "")[:120]])
    rows7 = [[k, "✅" if s["upstream"]["seven"].get(k) else "❌", str(s["upstream"].get(k))[:60]] for k in SEVEN]
    rowsL = [[l.get("domain"), l["kind"], l["id"], {"t": l["state"], "s": l["state"]}, l["path"], l["sha12"], str(l["age_h"] if l["age_h"] is not None else "-")] for l in s["links"]]
    kpis = [f"rc {s['rc']} {s['rc_name']}", f"連結 {len(s['links'])}", " · ".join(f"{k} {v}" for k, v in s["link_counts"].items())]
    try:
        m = _mod("m173", newest(REG, "CGC_MDL173_MatrixReportSpec_v*.py"))
        if m is None:
            raise RuntimeError("MDL173 缺")
        body = (m.html_table(["域", "燈", "正本 / 現況"], rows6, caption="一 · 六域現況", center_cols={1})
                + m.html_table(["處", "在", "說明"], rows7, caption="二 · 上行七處自審(不假綠)", center_cols={1})
                + m.html_table(["域", "種", "id", "燈", "路徑", "sha12", "齡 h"], rowsL, caption=f"三 · 連結表({len(rowsL)})", center_cols={3}, num_cols={6}))
        return m.page_html(body, title=f"VRN 子系統管理對接口 · {VIA_TAG}", subtitle=f"{s['ts']} · {BORN} · 上接 VCGC · 下管四庫 · 零 CDN", md=md,
                           payload={k: v for k, v in s.items() if k != "links"}, kpis=kpis, law="L20 唯一對接口 · L05 零 Hydra · L16 誠實四態 · L04 尾版律", out=out)
    except Exception:
        def tbl(h, rows):
            def cell(c):
                return _html.escape(str(c.get("t") if isinstance(c, dict) else c))
            return ("<table><tr>" + "".join(f"<th>{_html.escape(x)}</th>" for x in h) + "</tr>"
                    + "".join("<tr>" + "".join(f"<td>{cell(c)}</td>" for c in r) + "</tr>" for r in rows) + "</table>")
        page = ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
                f"<title>VRN 子系統管理對接口 {VIA_TAG}</title><style>body{{font-family:system-ui,sans-serif;font-size:10.5px;margin:12px;background:#0f172a;color:#e5e7eb}}"
                "table{border-collapse:collapse;margin:8px 0}td,th{border:1px solid #334155;padding:2px 6px;text-align:left}h1{font-size:15px}h2{font-size:12px}</style></head><body>"
                f"<h1>VRN 子系統管理對接口 · {VIA_TAG} · {s['ts']} · {' · '.join(kpis)}</h1>"
                "<h2>一 · 六域現況</h2>" + tbl(["域", "燈", "正本 / 現況"], rows6) + "<h2>二 · 上行七處自審</h2>" + tbl(["處", "在", "說明"], rows7)
                + f"<h2>三 · 連結表({len(rowsL)})</h2>" + tbl(["域", "種", "id", "燈", "路徑", "sha12", "齡 h"], rowsL)
                + "<p>MDL173 殼缺席 → 最小殼(講明);零 CDN 零外連。</p></body></html>")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")
        return out


def write_outputs(s: dict) -> dict:
    d = REPORTS()
    d.mkdir(parents=True, exist_ok=True)
    md = to_markdown(s)
    (d / "VRN_SYSTEM_latest.json").write_text(json.dumps(s, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    (d / "VRN_SYSTEM_latest.md").write_text(md, encoding="utf-8")
    page = to_html(s, md, d / f"VIA_VRN_SystemManager_v{VERSION}.html")
    with (d / "LEDGER.tsv").open("a", encoding="utf-8") as f:
        f.write("\t".join([s["ts"], VIA_TAG, s["rc_name"], str(len(s["links"])), json.dumps(s.get("diff") or {}, ensure_ascii=False), json.dumps(s["lamps"], ensure_ascii=False)]) + "\n")
    return {"json": rel(d / "VRN_SYSTEM_latest.json"), "md": rel(d / "VRN_SYSTEM_latest.md"), "html": rel(page), "ledger": rel(d / "LEDGER.tsv")}


# ────────────────────────── 統一讀口(VIA 往下讀 VRN 一律經此) ──────────────────────────
READERS = {"policy": read_policy, "logic": read_logic, "factor": read_factor, "param": read_param, "engine": read_engine, "handover": read_handover, "records": read_records, "ssot": read_ssot, "upstream": upstream}


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
    """下行目錄:每一域 正本在哪 · 怎麼讀 · 上游誰在吃(讀器現解,不是寫死的表)。"""
    s = collect()
    up = "VCGC status/onepage/page(v0118 起經本口)"
    return [
        {"domain": "policy", "zh": "政策", "canon": s["policy"].get("path"), "verb": "read policy [id]", "consumer": up, "lamp": s["lamps"]["policy"]},
        {"domain": "logic", "zh": "邏輯", "canon": f"{s['logic']['book'].get('path')} + {s['logic'].get('src')} + 守門 {s['logic']['guard'].get('src', '')}", "verb": "read logic [book|guard|latest]", "consumer": up + " 邏輯庫 一行", "lamp": s["lamps"]["logic"]},
        {"domain": "factor", "zh": "因子", "canon": s["factor"].get("path"), "verb": "read factor [字]", "consumer": up + " 因子庫 一行", "lamp": s["lamps"]["factor"]},
        {"domain": "param", "zh": "參數", "canon": f"{s['param'].get('n')} 本(via_params_central.BOOKS VRN 子集 + 樞紐自報)", "verb": "read param [id] [--full]", "consumer": "via-params / 各引擎自讀(本口只列不改)", "lamp": s["lamps"]["param"]},
        {"domain": "engine", "zh": "引擎", "canon": s["engine"]["chain"].get("src"), "verb": "read engine [family]", "consumer": "格子 / 匯流排 / via-vrnchain(本口只讀快照)", "lamp": s["lamps"]["engine"]},
        {"domain": "handover", "zh": "交接", "canon": "ENG082 handover_copies + docs/VIA_Handover_ONEPAGE.md + docs/VIA_DroppedBalls_B*.md", "verb": "read handover", "consumer": "VCGC 交接段 / 接手 AI", "lamp": s["lamps"]["handover"]},
        {"domain": "ssot", "zh": "同義字", "canon": (s["ssot"].get("union") or {}).get("path"), "verb": "read ssot [union|additive|pending]", "consumer": "VCGC VRN 系統管理段 / SUP_MDL749 · ENG086 券商閘 / 操作員裁定(多義·候選)", "lamp": s["lamps"].get("ssot")},
        {"domain": "upstream", "zh": "上行", "canon": str(s["upstream"].get("vcgc")), "verb": "read upstream", "consumer": "七處自審:" + json.dumps(s["upstream"]["seven"], ensure_ascii=False), "lamp": "GREEN" if isinstance(s["upstream"].get("vcgc"), dict) else "ABSENT"},
    ]


# ────────────────────────── 畫面 ──────────────────────────
def _print_status(s: dict) -> None:
    print(f"[VRN_SystemManager] {VIA_TAG} · {BATCHES} · 模式 {s.get('mode')} · {s['ts']} · 上接 VCGC {((s['upstream'].get('vcgc') or {}) if isinstance(s['upstream'].get('vcgc'), dict) else {}).get('src', 'ABSENT')} · 下管四庫+引擎面+交接")
    po, lo, fa, pa, en, ho = (s[d] for d in ("policy", "logic", "factor", "param", "engine", "handover"))   # records 另讀(批682 七域)
    print(f"  政策 {s['lamps']['policy']:6s} 律 {po.get('laws')} · lessons {po.get('lessons')} · VRN 律 {len(po.get('vrn_laws') or [])} / lessons {len(po.get('vrn_lessons') or [])} · 批 {po.get('batch')} · 尾 {po.get('last_law')}/{po.get('last_lesson')} · 政策因子 {po.get('policy_rows')}")
    print(f"  邏輯 {s['lamps']['logic']:6s} 索引 {lo['book'].get('version')} 層 {lo['book'].get('layers')} 指標 {lo['book'].get('pointers')} · 守門 {lo['guard'].get('state')} {lo['guard'].get('line') or lo['guard'].get('why') or ''} · 邏輯庫 {lo.get('src', 'ABSENT')} 件 {lo.get('files')} {lo.get('verdicts')} · 同步 {lo.get('sync')}")
    print(f"  因子 {s['lamps']['factor']:6s} {fa.get('rows')} 列 {fa.get('by_source')} · 掛載 {fa.get('mounts')}")
    print(f"  參數 {s['lamps']['param']:6s} 冊 {pa.get('n')} · 缺 {pa.get('absent')} · 出處 via_params_central.BOOKS VRN 子集 + 樞紐自報")
    ch = en.get("chain") or {}
    print(f"  引擎 {s['lamps']['engine']:6s} 鏈 {ch.get('state')} {ch.get('tally')} · RED 拆 {ch.get('red_split')}(缺件≠壞掉;燈照抄鏈跑器)· 尾版家族 {en.get('families')} · 五面 {en.get('faces')}")
    sm = en.get("samples") or {}
    print(f"  樣本 {sm.get('state', '-'):6s} 實測樣本夾 {sm.get('vrn_dir')} · 本機檔數 {sm.get('files_here')} · {sm.get('why') or '在位'}(出處 {sm.get('src')})")
    op = ho.get("onepage") or {}
    print(f"  交接 {s['lamps']['handover']:6s} 一頁 批{op.get('docs_batch')} vs 律冊 批{op.get('laws_batch')} 同 {op.get('same')} · 逐批 {ho.get('latest_batch_doc')} · B 文 {ho.get('latest_b_doc')} · 掉球 {ho.get('dropped_balls')} {('· ' + ho['why']) if ho.get('why') else ''}")
    rc_ = s.get("records") or {}
    ln = rc_.get("lineage") or {}
    print(f"  紀錄 {s['lamps'].get('records', '-'):6s} session {len(ln)}(commit {sum(v.get('commits', 0) for v in ln.values())})· VRN 文 {len(rc_.get('docs') or [])} · 收容包 {len(rc_.get('intake') or [])} · 活線 {(rc_.get('lines') or {}).get('remote_heads')}(本線 {(rc_.get('lines') or {}).get('current')})")
    ss = s.get("ssot") or {}
    _u, _a, _p = ss.get("union") or {}, ss.get("additive") or {}, ss.get("pending") or {}
    print(f"  同義字 {s['lamps'].get('ssot', '-'):5s} 聯集冊 {_u.get('tally')} · 拒 {_u.get('deny')} · 裁定 {_u.get('rulings_by_kind')} · 沒過閘 {len(_u.get('gate_bypass') or [])} 支 · 增補冊 {_a.get('state')} {_a.get('keys')} 詞 多義 {_a.get('polysemy')} 候選 {_a.get('candidates')} · 券商閘 {(_a.get('broker_gate') or {}).get('state')}(拒 {(_a.get('broker_gate') or {}).get('deny')})· 待裁定=候不是壞(出處 {ss.get('src')})")
    up = s["upstream"]
    print(f"  上行 七處 {up.get('done')}/{len(SEVEN)} {json.dumps(up.get('seven'), ensure_ascii=False)} · VCGC 委派 {(up.get('vcgc') or {}).get('delegates') if isinstance(up.get('vcgc'), dict) else '-'} · 總管理器 {up.get('via_manager')}")
    print(f"  [計] 連結 {len(s['links'])} · {s['link_counts']} · 本口 rc {s['rc']} {s['rc_name']}(只看四庫+交接;引擎面不折進 rc)" + (f" · 差異 {s['diff']}" if s.get("diff") else ""))


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
    if verb == "records":
        r = read_records()
        print(f"  模式 {r['mode']} · session {len(r['lineage'])} · VRN 文 {len(r['docs'])} · 收容包 {len(r['intake'])} · 活線 {r['lines'].get('remote_heads')}(本線 {r['lines'].get('current')})")
        for sid, v in sorted(r["lineage"].items(), key=lambda kv: -kv[1]["commits"]):
            print(f"    {sid:34s} commit {v['commits']:4d} · 批 {v['batch_min']}–{v['batch_max']}({v['batched_commits']})· 最新:{v['latest']}")
        for d in r["docs"]:
            print(f"    文 {d['doc']}(VRN×{d['vrn_mentions']} · {d['bytes']} B)")
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
            print("  用法:read <policy|logic|factor|param|engine|handover|upstream> [key] [--full]")
            return 2
        r = read(a[1], a[2] if len(a) > 2 else None, full)
        print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
        return 0 if lamp_of(r.get("state")) in ("GREEN",) else (2 if lamp_of(r.get("state")) in ("NODATA", "STALE", "GATED") else 1)
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


# ────────────────────────── 自測(廿二檢;零網路;只寫暫存) ──────────────────────────
def selftest() -> int:
    import tempfile
    fails: list = []
    src = Path(__file__).read_text(encoding="utf-8", errors="replace")
    body = src.split("def selftest(")[0]        # 自測不讀自測本身的字串(LL:批504/506 自我引用誤判)

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    print(f"=== VRN 子系統管理對接口({VIA_TAG})· 廿七檢自測(零網路;只寫暫存)===")
    os.environ["VIA_SELFTEST"] = "1"
    real_dir = VIA / "VIA_Reports" / "vrn_system"
    marker_before = sorted(p.name for p in real_dir.glob("*")) if real_dir.is_dir() else []
    with tempfile.TemporaryDirectory() as td:
        os.environ["VIA_VRNSYS_REPORTS"] = td
        try:
            chk("① 尾版律:版號由檔名讀出,不寫死(VERSION 四碼 · FAMILY 無版號)", re.fullmatch(r"\d{4}", VERSION) is not None and FAMILY == "VRN_SystemManager" and ("VERSION = ME.rsplit" in body), f"({VIA_TAG})")
            chk("② 兩座正典橋在位:加速器橋(ACCEL-BRIDGE 標記 · 缺席零影響)+ JSON 讀寫正典橋(bind_read 綁定不是 def)", "[VIA:ACCEL-BRIDGE:v0100]" in body and "[VIA:JSONIO-BRIDGE:v0100]" in body and callable(_json), f"(ACCEL {'在' if VIA_ACCEL is not None else '缺席(graceful)'})")
            s = collect()
            chk("③ 六域齊 + 每域一盞燈且燈名出自燈號冊(len(LAMPS) 現場數,不寫死)", set(s["lamps"]) == set(DOMAINS) and all(v in LAMPS for v in s["lamps"].values()) and len(LAMPS) == 6, f"({s['lamps']})")
            po = s["policy"]
            chk("④ 政策:律冊在位 · 律/lessons 都 >0 · VRN 子集 >0 · sha12 十二碼 · 政策因子委派 ENG082", po["state"] == "GREEN" and po["laws"] > 0 and po["lessons"] > 0 and len(po["vrn_laws"]) > 0 and len(po["sha12"]) == 12 and "policy_factors()" in body, f"(律 {po['laws']} · lessons {po['lessons']} · VRN 律 {len(po['vrn_laws'])})")
            lo = s["logic"]
            chk("⑤ 邏輯:索引冊在位(層 6 · 指標 >0)· 守門委派 via_vrn_logic_book.do_check(不重寫守門)· ENG082 尾版在位 · 件 0 = latest NODATA 不是壞", lo["book"]["state"] == "GREEN" and lo["book"]["layers"] == 6 and lo["book"]["pointers"] > 0 and lo["guard"].get("rc") in (0, 1) and "bm.do_check()" in body and lo.get("src", "").startswith("VRN_ENG082") and lo.get("latest") in ("OK", "NODATA"), f"(守門 {lo['guard'].get('state')} · {lo['guard'].get('line')} · 件 {lo.get('files')})")
            fa = s["factor"]
            chk("⑥ 因子:委派 SUP_MDL748.policy_rows(不抄冊);列數 >0 或誠實 ABSENT/NODATA", ("policy_rows()" in body) and (fa["state"] in ("OK", "NODATA", "ABSENT") or str(fa["state"]).startswith("BROKEN")) and (fa.get("rows", 0) > 0 or fa["state"] != "OK"), f"({fa['state']} · {fa.get('rows')} 列)")
            pa = s["param"]
            vpc = _params_central()
            ids_central = {b["id"] for b in getattr(vpc, "BOOKS", [])} if vpc else set()
            sub = [b for b in pa["books"] if b["src"] == "via_params_central.BOOKS"]
            chk("⑦ 參數:VRN 子集 ⊆ via_params_central.BOOKS(抄到函式才算出處 LL316)· 樞紐自報常數(SUP_MDL749.SSOT / MDL176.UNION_OUT / MDL115.OUTJ)在列 · 冊 >10 本", len(sub) > 10 and all(b["id"] in ids_central for b in sub) and all(any(h in json.dumps(b, ensure_ascii=False) for b in pa["books"]) for h in ("SUP_MDL749", "CGC_MDL176", "CGC_MDL115")), f"(冊 {pa['n']} · 中央子集 {len(sub)} · 缺 {pa['absent']})")
            en = s["engine"]
            chk("⑧ 引擎:尾版家族用 VCGC._tail_files 同一把尺(VCGC 缺席才退自家 glob 並講明)· VRN 家族 >50 · 五面計數齊 · 實測樣本夾只讀冊 user.vrn_dir 且態 ∈ 燈號冊(本機不在=ABSENT 誠實)", en.get("families_ruler") == "VCGC._tail_files" and en["families"] > 50 and all(k in en["faces"] for k in ("spec", "grid", "register", "deck", "inventory_active")) and lamp_of((en.get("samples") or {}).get("state")) in LAMPS and "user.vrn_dir" in (en.get("samples") or {}).get("src", ""), f"(家族 {en['families']} · 五面 {en['faces']} · 樣本 {(en.get('samples') or {}).get('vrn_dir')} {(en.get('samples') or {}).get('state')})")
            table = [(0, "", "GREEN"), (1, "import fitz / ModuleNotFoundError: No module named 'fitz'", "ABSENT"), (1, "VIA_NET_CONSENT 未設 GATED", "GATED"), (2, "無報告件(誠實)", "NODATA"), (1, "Traceback KeyError", "RED"), (4, "", "GATED")]
            chk("⑨ 四態表驅動:rc0→GREEN · import 缺件→ABSENT · 閘→GATED · 誠實停/rc2→NODATA · 其餘→RED(負控:壞就是壞)", all(classify(rc, t) == exp for rc, t, exp in table), "")
            ch = en.get("chain") or {}
            chk("⑩ 引擎面照抄鏈跑器的燈、只拆不改:chain 快照在則 red_split 各鍵 ∈ 燈號冊且總和 == tally.RED;不在則 NODATA 誠實", (ch.get("state") == "NODATA") or (all(k in LAMPS for k in (ch.get("red_split") or {})) and sum((ch.get("red_split") or {}).values()) == int((ch.get("tally") or {}).get("RED", 0))), f"(鏈 {ch.get('state')} · RED 拆 {ch.get('red_split')} · tally {ch.get('tally')})")
            chk("⑪ 本口 rc 只看四庫+交接(RC_SCOPE 不含 engine):引擎面 RED 不折進 rc", "engine" not in RC_SCOPE and rc_of(s) == s["rc"], f"(rc {s['rc']} {s['rc_name']} · 引擎燈 {s['lamps']['engine']})")
            n0 = len(list(Path(td).glob("*")))
            s1 = sync(apply=False)
            chk("⑫ sync 乾跑一個位元都不寫(暫存夾前後檔數相同)且 diff 全 NEW(無上次快照)", len(list(Path(td).glob("*"))) == n0 and s1["diff"]["NEW"] == len(s1["links"]) and s1["diff"]["SAME"] == 0 and not s1["written"], f"(NEW {s1['diff']['NEW']})")
            s2 = sync(apply=True)
            outs = s2.get("outputs") or {}
            files = sorted(p.name for p in Path(td).glob("*"))
            page = (Path(td) / f"VIA_VRN_SystemManager_v{VERSION}.html").read_text(encoding="utf-8", errors="replace")
            chk("⑬ sync --apply 落三件 + 台帳(json/md/html/LEDGER.tsv)且頁零 CDN 零外連", {"VRN_SYSTEM_latest.json", "VRN_SYSTEM_latest.md", f"VIA_VRN_SystemManager_v{VERSION}.html", "LEDGER.tsv"} <= set(files) and "http://" not in page and "https://" not in page and "<script src" not in page, f"({files})")
            s3 = sync(apply=False)
            chk("⑭ 第二次 sync 對上一次快照全 SAME(NEW 0 · GONE 0 · CHANGED 0)", s3["diff"]["SAME"] == len(s3["links"]) and s3["diff"]["NEW"] == 0 and s3["diff"]["GONE"] == 0 and s3["diff"]["CHANGED"] == 0, f"({s3['diff']})")
            lp = Path(td) / "VRN_SYSTEM_latest.json"
            j = json.loads(lp.read_text(encoding="utf-8"))
            j["links"][0]["sha12"] = "deadbeef0000"
            j["links"].append({"id": "ghost:link", "kind": "book", "path": "x", "state": "GREEN", "sha12": "", "age_h": None})
            lp.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
            s4 = sync(apply=False)
            chk("⑮ 差異負控:改一條 sha → CHANGED 1;快照多一條鬼連結 → GONE 1(會過的檢等於沒有檢 LL89)", s4["diff"]["CHANGED"] == 1 and s4["diff"]["GONE"] == 1 and "ghost:link" in s4["diff_ids"]["GONE"], f"({s4['diff']})")
            r1, r2 = read("policy", "L11"), read("policy", "L99999")
            chk("⑯ 統一讀口 read('policy','L11') 命中且回 id;讀不存在的 id → NODATA 不炸;每個回傳都署名 via", (r1.get("hit") or {}).get("id") == "L11" and r2["state"] == "NODATA" and r1["via"] == VIA_TAG and r2["via"] == VIA_TAG, f"({(r1.get('hit') or {}).get('id')} · {r2['state']})")
            pid = next((b["id"] for b in pa["books"] if b["exists"] and b["src"] == "via_params_central.BOOKS"), None)
            r3, r4 = read("param", pid), read("param", pid, full=True)
            chk("⑰ read param <id> 回摘要不回內容,--full 才回內容;讀不存在的域 → NODATA", pid is not None and "content" not in (r3.get("hit") or {}) and "summary" in (r3.get("hit") or {}) and "content" in (r4.get("hit") or {}) and read("nosuch")["state"] == "NODATA", f"({pid})")
            up = s["upstream"]
            chk("⑱ 上行七處自審回七鍵且不假綠:Register 短令未登(L70)必須 False;VCGC 在位時 delegates 為 bool", set(up["seven"]) == set(SEVEN) and up["seven"]["register"] is False and (not isinstance(up.get("vcgc"), dict) or isinstance(up["vcgc"].get("delegates"), bool)), f"({up['done']}/{len(SEVEN)} · {up['seven']})")
            code = re.sub(r"#.*", "", body)
            chk("⑲ 零網路(原始碼無 requests/urllib.request/http.client/socket 呼叫;排除註解與自測段)", not re.search(r"\b(requests\.|urllib\.request|http\.client|socket\.)", code), "")
            chk("⑳ 零寫庫(原始碼無 duckdb.connect / CREATE TABLE / INSERT INTO;只讀快照)", not re.search(r"duckdb\.connect|CREATE TABLE|INSERT INTO", code), "")
            md = (Path(td) / "VRN_SYSTEM_latest.md").read_text(encoding="utf-8")
            chk("㉑ 一頁 MD 六域每域一行(表列)+ 七處表 + 連結表;燈名全出自燈號冊", all(f"| {DOMAIN_ZH[d]} |" in md for d in DOMAINS) and "七處自審" in md and f"連結表({len(s['links'])}" in md and all(l["state"] in LAMPS for l in s["links"]), f"({len(md)} 字)")
            ho = s["handover"]
            _FORCE_STANDALONE["on"] = True
            try:
                sa = collect()
            finally:
                _FORCE_STANDALONE["on"] = False
            chk("㉓ 雙模式:--standalone 下六域照讀、mode=standalone、五面標 STANDALONE 不代讀、尾版家族改自家 glob 並講明、上行 vcgc=STANDALONE;關掉後回 subsystem(VCGC 在位時)",
                sa["mode"] == "standalone" and set(sa["lamps"]) == set(DOMAINS) and str(sa["engine"]["faces"].get("state", "")).startswith("STANDALONE") and "standalone" in sa["engine"].get("families_ruler", "")
                and sa["upstream"].get("vcgc") == "STANDALONE" and sa["engine"]["families"] > 50 and (mode() == "subsystem" or _vcgc() is None),
                f"(standalone 家族 {sa['engine']['families']} · 五面 {sa['engine']['faces'].get('state', '')[:22]} · 現在 {mode()})")
            rcd = s["records"]
            chk("㉔ 紀錄索引:血脈由 git 尾註量出(本 session 在列且 ≥2 個 session)· VRN 文含本批全景文 · 收容包含側線 b20260921 · 指標不複本",
                rcd["state"] == "GREEN" and len(rcd["lineage"]) >= 2 and any("session_" in k for k in rcd["lineage"]) and any("VIA_VRN_Panorama_20260921" in d["doc"] for d in rcd["docs"])
                and any("VIA_SSOT_Additive_Audit_v0100_b20260921" in i["intake"] for i in rcd["intake"]) and all("content" not in d for d in rcd["docs"]),
                f"(session {len(rcd['lineage'])} · 文 {len(rcd['docs'])} · 收容包 {len(rcd['intake'])})")
            fams = s["engine"].get("families_detail") or {}
            t749 = fams.get("SUP_MDL749_VRNFieldRuleHub", "")
            chk("㉕ 側線件在位(批682 原樣收進):VRN_ENG088 家族在 · SUP_MDL749 尾版 ≥ v0111 · 單元測試 test_vrn_ssot_additive 在",
                "VRN_ENG088_SsotAdditiveBridge" in fams and re.search(r"_v(\d{4})\.py$", t749) is not None and int(re.search(r"_v(\d{4})\.py$", t749).group(1)) >= 111 and (REG / "tests" / "test_vrn_ssot_additive_v0100.py").is_file(),
                f"(749 尾版 {Path(t749).name if t749 else '缺'})")
            chk("㉒ 交接三處 hash 委派 ENG082.handover_copies(不重算);一頁批號 < 律冊批號 → STALE 而不是 RED(過期≠壞)", "handover_copies(quiet=True)" in body and isinstance(ho.get("copies"), dict) and (ho["state"] != "RED") and (ho["state"] != "STALE" or (ho["onepage"]["docs_batch"] or 0) < (ho["onepage"]["laws_batch"] or 0) or ho["onepage"].get("same") is False), f"({ho['state']} · 一頁 批{ho['onepage'].get('docs_batch')} vs 律冊 批{ho['onepage'].get('laws_batch')})")
        finally:
            os.environ.pop("VIA_VRNSYS_REPORTS", None)
            os.environ.pop("VIA_SELFTEST", None)
    # ㉖㉗ 批689B:第八域同義字——讀得到聯集冊與增補冊;待裁定逐項端上;MDL176 缺=ABSENT 不炸
    _ss = read_ssot()
    _u26 = _ss.get("union") or {}
    chk("㉖ 同義字域:聯集冊 tally(SAME/ADD/CONFLICT/DENIED)+ 拒絕清單 ≥10 + 正典鍵對映裁定 + 沒過閘的活支列得出;增補冊多義/候選端上;券商閘 OK;燈 GREEN 且入 rc 範圍",
        _ss.get("state") == "GREEN" and isinstance(_u26.get("tally"), dict) and {"SAME", "ADD"} <= set(_u26["tally"])
        and int(_u26.get("deny") or 0) >= 10 and (_u26.get("rulings_by_kind") or {}).get("KEY_ALIAS")
        and isinstance(_u26.get("gate_bypass"), list) and (_ss.get("additive") or {}).get("state") == "OK"
        and ((_ss.get("additive") or {}).get("broker_gate") or {}).get("state") == "OK"
        and "ssot" in RC_SCOPE and "ssot" in DOMAINS,
        f"(tally {_u26.get('tally')} · 拒 {_u26.get('deny')} · 裁定 {_u26.get('rulings_by_kind')} · 沒過閘 {len(_u26.get('gate_bypass') or [])} · 多義 {(_ss.get('additive') or {}).get('polysemy')} · 候選 {(_ss.get('additive') or {}).get('candidates')})")
    _keep_newest = globals()["newest"]
    try:
        globals()["newest"] = lambda folder, pat: (None if "CGC_MDL176" in pat else _keep_newest(folder, pat))
        _abs = read_ssot()
    finally:
        globals()["newest"] = _keep_newest
    chk("㉗ MDL176 缺席 → 同義字域 ABSENT 講因由(不炸、不編);read('ssot','pending') 走 key 路",
        _abs.get("state") == "ABSENT" and "CGC_MDL176" in str(_abs.get("why")) and read("ssot", "pending").get("key") == "pending",
        f"({_abs.get('state')} · {str(_abs.get('why'))[:40]})")
    marker_after = sorted(p.name for p in real_dir.glob("*")) if real_dir.is_dir() else []
    if marker_before != marker_after:
        fails.append("零污染")
        print(f"  [FAIL] 自測零污染:真 VIA_Reports/vrn_system 被自測動過 {marker_before} → {marker_after}")
    print(f"  [計] 廿七檢 OK {27 - len([f for f in fails if f != '零污染'])} · FAIL {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
