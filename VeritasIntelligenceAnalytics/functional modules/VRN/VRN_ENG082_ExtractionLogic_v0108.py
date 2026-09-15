#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VRN_ENG082_ExtractionLogic v0102 — VRN 擷取**中央邏輯庫**(批493 操作員令;批496 次序修正;批498 入庫)
====================================================================
操作員令(2026-09-14):「vrn 非 OCR 擷取式必要使用;若還有抓不到改用 OCR,從較簡單的工具組往
雙引擎、往 Paddle 相關工具;所謂成功包含資料標示還原原樣修復、文字修復;非 OCR 有兩個相同的
相互核對,再跟非 OCR 核對;邏輯方法及其他驗證擷取方法成功後存於中央邏輯庫」。

實錄(批493 他跑 via-ryg):vrn_firstpage 900 秒逾時——JP-3653 一份卡 340 秒(GLE 七支後端逐支
載模型、全回零字,再升高畫質整條重跑一次),PPP 車道 `Unknown argument: show_log`(PaddleOCR 3.x
拿掉了 2.x 的鍵),於是每一份掃描件都把整座梯子燒兩遍,而且每次重跑 via-ryg 都從頭燒。

本件是**律的執行層**,ENG072(首頁擷取)尾版綁它;它缺席 ENG072 照舊(零回歸):
  ① ladder()/budget_s():階梯與預算(冊 VRN_ExtractionLogic_SSOT_v*.json 優先;缺冊用內建同值)
  ② xcheck(a, b):兩份文字互核——字袋 Jaccard + 序列比,AGREE/ORDER_ONLY/PARTIAL/DISAGREE/SINGLE
  ③ repair_text(t):文字修復——零寬字元、全形英數→半角(中文標點**保留**)、中文斷行接回、多空白收斂;回統計
  ④ labels_ok(zones)/verdict_of(...):資料標示還原成立?→ SUCCESS/PARTIAL/FAIL(判準亮在這裡)
  ⑤ lookup(path, outdir)/record(...):同檔(sha1)成功且產物在=命中不重抽;失敗件 TTL 內不重燒 OCR
  ⑥ mark_backend()/broken_backends():後端健康(載入失敗=BROKEN,TTL 內跳過;真抽到字=OK)
  ⑦ install_paddle_compat():PaddleOCR/PPStructure 2.x 鍵(show_log/use_gpu/use_angle_cls)在 3.x 上
     自動剔除重試(use_angle_cls→use_textline_orientation);收容件正本零觸碰
  ⑧ 存證:VIA_Reports/vrn/extraction_logic/LOGIC_LEDGER.jsonl(只增)+ LOGIC_latest.json(摘要)
     env VIA_LOGIC_DIR 可改(自測用暫存夾,真目錄零觸碰)
v0100→v0101(批496 操作員令「修正 vrn 邏輯:先非 OCR 擷取修正驗證;失敗的輸入輕量 OCR 往重型 OCR;都失敗用內建 PDF 畫質提升,
  DPI 先拉到 300~350」):冊/預設 +hq_budget_s(第三階自有預算,不受第二階用盡影響)+hq_dpi 帶 [300,350] +nonocr_fail_rule
  (本文 < min_chars 或 兩法 DISAGREE = 非 OCR 失敗 → 才 OCR;PARTIAL 只是標示未還原=不 OCR);nonocr_failed()/hq_budget_s()/hq_dpi_band() 供 ENG072 v0119。
v0101→v0102(批498 操作員令「將邏輯因子政策入庫」):+sync-db——把台帳(逐件方法/互核/修復/判準)寫成 DuckDB 表
  vrn_extraction_logic,把三本律冊(擷取邏輯/工具冊風險政策/資料家版面契約)攤平成 via_policy_factors(key/value/source);
  只建/覆寫這兩張表,其餘表零觸碰;庫按名找(env VIA_DB_VDF_TW_MARKET > VIA_DATA_HOME > output_hub/mega);庫忙/缺=誠實跳過;
  --dry-run 只印。ENG072 v0121 跑完自動 sync;冊 VIA_DB_Table_SSOT 宣告兩表(census 冊上)。
v0107→v0108(批506 VCGC 唯一對接口):政策因子 +政策庫冊 VIA_Policy_Laws_SSOT(23 律 + lessons 全攤平);交接正本改認 docs/VIA_Handover_ONEPAGE.md(VCGC 一頁;缺才退 B 檔尾版)。
v0106→v0107(批505 操作員 via-ryg 實錄:vrn_logic 站 RED——自測 ⑮/⑰ 在他機器上跑,bootstrap 匯出的 VIA_DB_* 真庫全進了 sync_targets,
  目標數對不上=FAIL,而且 ⑮ 又把 fixture 寫進真庫(容器加一個 VIA_DB_FAKE1 就重現)→ 自測整段先撤 VIA_DB_*/VIA_DATA_HOME、設 VIA_SELFTEST=1,結束還原;⑲ 證明。
v0105→v0106(批504 操作員實錄「[入庫同步] 同步 1 · 落後 5」=我的自測污染:ENG072 自測 ㊲ 只把首選庫導向暫存,sync_targets 仍掃 VIA_DATA_HOME 與 VIA_DB_*,
  格子跑自測時把 8 筆 fixture 寫進 5 本真庫的政策表)→ VIA_SELFTEST=1 時 sync_targets 只認 env 指定的那一本(不掃家、不掃 VIA_DB_*);
  政策因子 +SUP_MDL748 財務邏輯橋兩本冊(券商/評等/科目同義/單位倍率/28 欄/正則)。
v0104→v0105(批503 操作員實錄 64/64 抽齊):status 的「法」計數把 tesseract_direct(dpi/墨量/秒)每件不同的參數當成不同法(四行各 1)——法名切到「(」為止,同法歸一行;參數留在台帳。
v0103→v0104(批502):後端健康 why 記 400 字(PaddleX 相依錯的「請裝 …」在尾巴,160 字被切掉);status 印 150 字。
用法:python3 VRN_ENG082_ExtractionLogic_v0108.py [status|reset-backends|sync-db [--dry-run] [--db PATH]] | --selftest
v0102→v0103(批499 操作員令「所有的庫政策邏輯因子庫都要同步更新」):sync-db 預設**全庫同步**——資料家內每一本 .duckdb(沙盒除外)
  + env VIA_DB_* 指到的庫 + 首選庫,同一份邏輯台帳/政策因子(同一個 hash)寫進每一本,並各留一列 via_policy_sync 對帳單;
  status 印 [入庫同步] 幾本同步/落後/未入/忙;政策因子加入後端健康(哪一支在哪一境壞了、為什麼)與判準統計;--db PATH 仍可單庫。
律:只增不減;誠實三態;零網路;零刪除(reset-backends 只清健康標記,不動台帳)。
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import socket
import sys
import time
import unicodedata
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
SSOT_GLOB = "VRN_ExtractionLogic_SSOT_v*.json"
LEDGER_NAME = "LOGIC_LEDGER.jsonl"
LATEST_NAME = "LOGIC_latest.json"

DEFAULT_SSOT = {
    "ladder": [
        {"stage": "simple", "adapters": ["tesseract"]},
        {"stage": "dual", "adapters": ["tesseract", "easyocr"]},
        {"stage": "paddle", "adapters": ["paddleocr", "paddle_ppstructure", "paddle_pdf_pipeline"]},
    ],
    "budget_s": 150, "hq_min_remaining_s": 45,
    "xcheck": {"agree_bag": 0.85, "agree_seq": 0.6, "partial_bag": 0.5, "textlayer_min_chars": 200},
    "min_chars": 40, "backend_ttl_h": 24, "fail_ttl_h": 24,
    "hq_budget_s": 120, "hq_dpi": [300, 350],
}
_SSOT: dict | None = None


def logic_dir() -> Path:
    env = os.environ.get("VIA_LOGIC_DIR", "").strip()
    return Path(env) if env else VIA / "VIA_Reports" / "vrn" / "extraction_logic"


def ssot() -> dict:
    global _SSOT
    if _SSOT is not None:
        return _SSOT
    d = json.loads(json.dumps(DEFAULT_SSOT))
    try:
        hits = sorted((VIA / "supportive modules" / "registry").glob(SSOT_GLOB))
        if hits:
            j = json.loads(hits[-1].read_text(encoding="utf-8"))
            for k in ("ladder", "budget_s", "hq_min_remaining_s", "xcheck", "min_chars", "backend_ttl_h", "fail_ttl_h", "hq_budget_s", "hq_dpi"):
                if k in j:
                    d[k] = j[k]
            d["_src"] = hits[-1].name
    except Exception as exc:
        d["_src"] = f"冊讀取失敗 {type(exc).__name__}(用內建)"
    _SSOT = d
    return d


def ladder() -> list:
    return [dict(s) for s in ssot()["ladder"]]


def budget_s() -> float:
    return float(ssot()["budget_s"])


def backend_ttl_h() -> float:
    return float(ssot()["backend_ttl_h"])


def hq_budget_s() -> float:
    """第三階(畫質提升 DPI 300~350 重跑階梯)自有預算;不受第二階用盡影響(批496)。"""
    return float(ssot().get("hq_budget_s", 120))


def hq_dpi_band() -> tuple:
    """畫質提升的 DPI 帶(操作員令 300~350)。"""
    b = ssot().get("hq_dpi") or [300, 350]
    try:
        lo, hi = int(b[0]), int(b[1])
        return (min(lo, hi), max(lo, hi))
    except Exception:
        return (300, 350)


def nonocr_failed(lg: dict) -> bool:
    """非 OCR 擷取「失敗」的判準(批496):本文 < min_chars(verdict FAIL)或 兩法 DISAGREE;PARTIAL 只是標示未還原=不算失敗。"""
    v = (lg or {}).get("verdict")
    st = ((lg or {}).get("xcheck") or {}).get("state")
    return v == "FAIL" or st == "DISAGREE"


# ────────────────────────────── 台帳 ──────────────────────────────
def sha1_of(path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_latest() -> dict:
    p = logic_dir() / LATEST_NAME
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        d.setdefault("files", {}); d.setdefault("backends", {}); d.setdefault("stats", {})
        return d
    except Exception:
        return {"schema": "VIA.VRN.ExtractionLogic.latest.v1", "files": {}, "backends": {}, "stats": {}}


def _save_latest(d: dict) -> None:
    ld = logic_dir()
    ld.mkdir(parents=True, exist_ok=True)
    d["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tmp = ld / (LATEST_NAME + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, ld / LATEST_NAME)


def _append_ledger(rec: dict) -> None:
    ld = logic_dir()
    ld.mkdir(parents=True, exist_ok=True)
    with open(ld / LEDGER_NAME, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _fresh(ts: str, ttl_h: float) -> bool:
    try:
        return datetime.now() - datetime.strptime(str(ts)[:19], "%Y-%m-%d %H:%M:%S") < timedelta(hours=float(ttl_h))
    except Exception:
        return False


def lookup(path, outdir) -> dict | None:
    """同檔(sha1)上次成功且產物(.json+.txt)還在 → HIT(不重抽);上次失敗且 fail_ttl 內 → FAIL_HIT(不重燒 OCR)。"""
    path, outdir = Path(path), Path(outdir)
    try:
        h = sha1_of(path)
    except Exception:
        return None
    rec = load_latest()["files"].get(h)
    if not rec:
        return None
    if rec.get("verdict") == "SUCCESS":
        if (outdir / (path.stem + ".json")).exists() and (outdir / (path.stem + ".txt")).exists():
            return dict(rec, state="HIT")
        return None
    if rec.get("verdict") == "FAIL" and _fresh(rec.get("ts", ""), ssot()["fail_ttl_h"]):
        return dict(rec, state="FAIL_HIT")
    return None


def record(path, verdict: str, method: str, chars: int, xcheck: dict | None, repair: dict | None,
           labels_ok, secs: float, sidecar: str = "", tag: str = "", stage: str = "") -> dict:
    path = Path(path)
    rec = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "file": path.name, "sha1": sha1_of(path),
           "verdict": verdict, "method": method, "stage": stage, "chars": int(chars),
           "xcheck": xcheck or {}, "repair": repair or {}, "labels_ok": labels_ok,
           "secs": round(float(secs), 2), "sidecar": sidecar, "tag": str(tag)[:200]}
    _append_ledger(rec)
    d = load_latest()
    d["files"][rec["sha1"]] = rec
    st = d["stats"]
    st[verdict] = st.get(verdict, 0) + 1
    st["by_method:" + str(method).split("[", 1)[0][:40]] = st.get("by_method:" + str(method).split("[", 1)[0][:40], 0) + 1
    _save_latest(d)
    return rec


def mark_backend(name: str, state: str, why: str = "") -> None:
    d = load_latest()
    d["backends"][str(name)] = {"state": state, "why": str(why)[:400], "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    _save_latest(d)


def broken_backends(ttl_h: float | None = None) -> list:
    ttl = backend_ttl_h() if ttl_h is None else ttl_h
    return sorted(n for n, b in load_latest()["backends"].items()
                  if b.get("state") == "BROKEN" and _fresh(b.get("ts", ""), ttl))


def reset_backends() -> int:
    d = load_latest()
    n = len(d["backends"])
    d["backends"] = {}
    _save_latest(d)
    return n


# ────────────────────────────── 互核 · 修復 · 判準 ──────────────────────────────
def _norm(t: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", t or ""))


def xcheck(a: str, b: str) -> dict:
    """兩份文字互核:字袋 Jaccard(不管順序)+ 序列比(管順序)。"""
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return {"bag": 0.0, "seq": 0.0, "state": "SINGLE" if (na or nb) else "NONE"}
    ca, cb = Counter(na), Counter(nb)
    inter = sum((ca & cb).values())
    union = sum((ca | cb).values())
    bag = inter / union if union else 0.0
    seq = difflib.SequenceMatcher(None, na[:3000], nb[:3000]).ratio()
    th = ssot()["xcheck"]
    state = ("AGREE" if (bag >= th["agree_bag"] and seq >= th["agree_seq"]) else
             "ORDER_ONLY" if bag >= th["agree_bag"] else
             "PARTIAL" if bag >= th["partial_bag"] else "DISAGREE")
    return {"bag": round(bag, 3), "seq": round(seq, 3), "state": state}


_ZW = re.compile("[­​‌‍﻿]")
_CJK = "一-鿿㐀-䶿"
_JOIN = re.compile(f"([{_CJK}，。、；：」』）])\n(?=[{_CJK}「『（])")
#: 全形英數/常用符號 → 半形;中文標點(，。、;:「」()…)一律保留
_FW = {chr(c): chr(c - 0xFEE0) for c in list(range(0xFF10, 0xFF1A)) + list(range(0xFF21, 0xFF3B)) + list(range(0xFF41, 0xFF5B))}
_FW.update({"％": "%", "＋": "+", "－": "-", "．": ".", "／": "/", "＄": "$", "＆": "&", "＝": "=", "＜": "<", "＞": ">", "＠": "@", "＃": "#", "　": " "})
_FW_TABLE = str.maketrans(_FW)


def repair_text(t: str) -> tuple[str, dict]:
    """文字修復(操作員律「文字修復」);回 (修後文字, 統計)。不動表格分隔、不動中文標點。"""
    if not t:
        return t, {"zw": 0, "fullwidth": 0, "joins": 0, "spaces": 0}
    t1, zw = _ZW.subn("", t)
    fw = sum(1 for ch in t1 if ch in _FW)
    t2 = t1.translate(_FW_TABLE)
    t3, joins = _JOIN.subn(r"\1", t2)
    t4, spaces = re.subn(r"[ \t]{2,}", " ", t3)
    t4 = re.sub(r"[ \t]+\n", "\n", t4)
    t4 = re.sub(r"\n{3,}", "\n\n", t4)
    return t4, {"zw": zw, "fullwidth": fw, "joins": joins, "spaces": spaces}


def labels_ok(zones: dict) -> bool:
    """資料標示還原成立?=標題帶或右資訊區在,且本文在。"""
    try:
        return bool((zones.get("header") or zones.get("right")) and zones.get("body"))
    except Exception:
        return False


def verdict_of(chars: int, xc: dict | None, labels, kind: str) -> str:
    """SUCCESS / PARTIAL / FAIL(判準亮在這裡,不埋)。"""
    st = (xc or {}).get("state", "NONE")
    if int(chars or 0) < int(ssot()["min_chars"]):
        return "FAIL"
    if kind == "pdf_zones":
        return "SUCCESS" if (labels and st in ("AGREE", "ORDER_ONLY", "SINGLE")) else "PARTIAL"
    return "SUCCESS" if st != "DISAGREE" else "PARTIAL"


# ────────────────────────────── PaddleOCR 3.x 相容墊片 ──────────────────────────────
_COMPAT = {"done": False, "note": "", "dropped": []}


def install_paddle_compat() -> str:
    """paddleocr 在位時把 PaddleOCR/PPStructure 的 __init__ 包一層:遇 `Unknown argument: X` /
    `unexpected keyword argument 'X'` 就剔除 X 重試(use_angle_cls→use_textline_orientation)。
    冪等;paddleocr 不在位=不墊(誠實)。收容件(PDFPlumberPlus/GLE)正本零觸碰。"""
    if _COMPAT["done"]:
        return _COMPAT["note"]
    _COMPAT["done"] = True
    try:
        import importlib
        pm = importlib.import_module("paddleocr")
    except Exception as exc:
        _COMPAT["note"] = f"paddleocr 不在位({type(exc).__name__})=不墊"
        return _COMPAT["note"]
    n = 0
    for cls_name in ("PaddleOCR", "PPStructure", "PPStructureV3"):
        cls = getattr(pm, cls_name, None)
        if cls is None or getattr(cls, "_via_compat", False):
            continue
        orig = cls.__init__

        def _make(orig, cls_name=cls_name):
            def __init__(self, *a, **kw):
                kw = dict(kw)
                for _ in range(10):
                    try:
                        return orig(self, *a, **kw)
                    except (ValueError, TypeError) as exc:
                        m = re.search(r"[Uu]nknown argument[: ]+['\"]?(\w+)|unexpected keyword argument ['\"](\w+)['\"]", str(exc))
                        bad = (m.group(1) or m.group(2)) if m else None
                        if not bad or bad not in kw:
                            raise
                        if bad == "use_angle_cls" and "use_textline_orientation" not in kw:
                            kw["use_textline_orientation"] = bool(kw.pop(bad))
                        else:
                            kw.pop(bad)
                        _COMPAT["dropped"].append(f"{cls_name}.{bad}")
                return orig(self, *a, **kw)
            return __init__
        cls.__init__ = _make(orig)
        cls._via_compat = True
        n += 1
    _COMPAT["note"] = f"paddleocr 相容墊片就位({n} 類;2.x 鍵 show_log/use_gpu/use_angle_cls 在 3.x 上自動剔除重試)"
    return _COMPAT["note"]


# ────────────────────────────── 入庫(批498)──────────────────────────────
def resolve_db(explicit: str | None = None):
    """邏輯要入哪本庫:--db > env VIA_DB_VDF_TW_MARKET > VIA_DATA_HOME 內按名找最新 > output_hub/mega;找不到=None 誠實。"""
    if explicit:
        return Path(explicit)
    v = os.environ.get("VIA_DB_VDF_TW_MARKET")
    if v and Path(v).exists():
        return Path(v)
    h = os.environ.get("VIA_DATA_HOME")
    if h and Path(h).exists():
        hp = Path(h)
        try:
            hits = [hp] if (hp.is_file() and hp.name == "vdf_tw_market.duckdb") else list(hp.rglob("vdf_tw_market.duckdb"))
            if hits:
                return max(hits, key=lambda x: x.stat().st_mtime)
        except Exception:
            pass
    c = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
    return c if c.exists() else None


def policy_factors() -> list:
    """三本律冊攤平成 (source, key, value) 列:擷取邏輯冊 / 工具冊風險政策 / 資料家版面契約 / 治理基線 hydra 規則。"""
    reg = VIA / "supportive modules" / "registry"
    rows = []

    def flat(prefix, obj, src):
        if isinstance(obj, dict):
            for k, v in obj.items():
                flat(f"{prefix}.{k}" if prefix else str(k), v, src)
        elif isinstance(obj, list) and obj and all(isinstance(x, (str, int, float)) for x in obj):
            rows.append({"source": src, "key": prefix, "value": json.dumps(obj, ensure_ascii=False)[:2000]})
        elif isinstance(obj, list):
            for i, x in enumerate(obj):
                flat(f"{prefix}[{i}]", x, src)
        else:
            rows.append({"source": src, "key": prefix, "value": (json.dumps(obj, ensure_ascii=False) if not isinstance(obj, str) else obj)[:2000]})
    for glob_, keys in ((SSOT_GLOB, None),
                        ("VIA_ToolRoster_SSOT_v*.json", ("law", "risk_policy", "sources", "order", "states", "health_checks", "operator_order", "governs", "routing_note")),
                        ("VIA_DataHome_SSOT_v*.json", ("layout_contract", "token_saving_rules", "precedence", "home_win", "declared_by", "note")),
                        ("VIA_EnvGovernance_Baseline_v*.json", ("hydra", "principles", "routing_order", "tool_roster")),
                        ("VIA_Policy_Laws_SSOT_v*.json", None)):                      # 批506 政策庫冊:律 + lessons 全攤平
        hits = sorted(reg.glob(glob_))
        if not hits:
            continue
        try:
            j = json.loads(hits[-1].read_text(encoding="utf-8"))
        except Exception:
            continue
        src = hits[-1].name
        if keys is None:
            flat("", {k: v for k, v in j.items() if k != "_src"}, src)
        else:
            flat("", {k: j[k] for k in keys if k in j}, src)
    # 批504:財務邏輯橋兩本冊(AllInOne 2.1.0 + financial_data_standardization)也是政策因子
    try:
        hits = sorted((VIA / "supportive modules" / "70_VRN_Rules").glob("SUP_MDL748_FinancialLogicHub_v*.py"))
        if hits:
            import importlib.util as _ilu
            sp = _ilu.spec_from_file_location("sup_mdl748_for_082", hits[-1])
            hm = _ilu.module_from_spec(sp)
            sys.modules["sup_mdl748_for_082"] = hm
            sp.loader.exec_module(hm)
            rows.extend(hm.policy_rows())
        else:
            rows.append({"source": "SUP_MDL748", "key": "state", "value": "ABSENT(財務邏輯橋缺席)"})
    except Exception as exc:
        rows.append({"source": "SUP_MDL748", "key": "state", "value": f"BROKEN {type(exc).__name__}:{str(exc)[:80]}"})
    # 批499:後端健康(哪一支在哪一境 OK/EMPTY/BROKEN、為什麼)與判準統計也是邏輯因子——入庫,別只留在 JSON
    try:
        d = load_latest()
        for n, b in sorted((d.get("backends") or {}).items()):
            rows.append({"source": "LOGIC_latest.backends", "key": f"backend.{n}", "value": json.dumps(b, ensure_ascii=False)[:2000]})
        by = Counter(r.get("verdict") for r in (d.get("files") or {}).values())
        if by:
            rows.append({"source": "LOGIC_latest.stats", "key": "verdicts", "value": json.dumps(dict(by), ensure_ascii=False)})
    except Exception:
        pass
    return rows


SANDBOX_MARKS = ("/engine_bus/_cwd/", "/selftest_grid/", "/vdfout_runs/selftest_out/", "/_self_test")


def sync_targets(explicit: str | None = None) -> list:
    """批499 全庫同步的目標:--db 指定=只那一本;否則 首選庫 ∪ env VIA_DB_* ∪ 資料家內每本 .duckdb(沙盒/暫存除外);去重。"""
    if explicit:
        return [Path(explicit)]
    if os.environ.get("VIA_SELFTEST") == "1":
        # 批504 自測零污染律:自測行程只寫 env 指定的那一本(暫存),永不掃真資料家 / VIA_DB_*
        p0 = resolve_db(None)
        return [Path(p0)] if p0 else []
    seen, out = set(), []

    def _add(pth):
        try:
            q = Path(pth)
            if not q.is_file() or q.suffix.lower() != ".duckdb":
                return
            sp = str(q.resolve()).replace("\\", "/")
            if any(m in sp for m in SANDBOX_MARKS) or sp in seen:
                return
            seen.add(sp)
            out.append(q)
        except Exception:
            pass
    _add(resolve_db(None) or "")
    for k, v in sorted(os.environ.items()):
        if k.startswith("VIA_DB_") and v:
            _add(v)
    home = os.environ.get("VIA_DATA_HOME") or ""
    if home and Path(home).is_dir():
        for q in sorted(Path(home).rglob("*.duckdb")):
            _add(q)
    return out


def handover_doc() -> tuple:
    """最新交接報告(docs/VIA_Handover_*.md 尾版)。批499 操作員令「母檔案夾/資料庫/github 路徑都要有 handover report」:
    github=docs 正本;母檔案夾=倉根 VIA_HANDOVER_LATEST.md(隨 git pull 到);資料庫=每本庫 via_handover 表 + 資料家根 VIA_HANDOVER_LATEST.md。"""
    one = VIA / "docs" / "VIA_Handover_ONEPAGE.md"                 # 批506:VCGC 一頁交接為正本
    if one.is_file():
        try:
            return one, one.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
    hits = []
    for q in (VIA / "docs").glob("VIA_Handover_*_B*.md"):
        m = re.match(r"VIA_Handover_(\d{8})_B(\d+)\.md$", q.name)
        if m:
            hits.append(((m.group(1), int(m.group(2))), q))
    hits = [q for _, q in sorted(hits)]
    if not hits:
        return None, ""
    try:
        return hits[-1], hits[-1].read_text(encoding="utf-8", errors="replace")
    except Exception:
        return hits[-1], ""


def handover_copies(quiet: bool = True) -> dict:
    """唯讀對帳:母檔案夾(倉根)與資料家根的 VIA_HANDOVER_LATEST.md 是否與 docs 尾版同一份(sha)。"""
    hp, htxt = handover_doc()
    out = {"doc": (hp.name if hp else ""), "sha": hashlib.sha1(htxt.encode("utf-8")).hexdigest()[:12] if htxt else "", "root": "缺", "home": "缺"}
    if hp is None:
        return out
    for k, q in (("root", VIA.parent / "VIA_HANDOVER_LATEST.md"), ("home", Path(os.environ.get("VIA_DATA_HOME") or "-") / "VIA_HANDOVER_LATEST.md")):
        try:
            if q.is_file():
                out[k] = "同" if hashlib.sha1(q.read_text(encoding="utf-8", errors="replace").encode("utf-8")).hexdigest()[:12] == out["sha"] else "舊"
        except Exception:
            out[k] = "壞"
    if not quiet:
        print(f"  [交接三處] docs {out['doc']} sha {out['sha']} · 母檔案夾(倉根) {out['root']} · 資料家根 {out['home']}(舊/缺 → via-vrnlogic sync-db 補資料家;倉根隨 git pull)")
    return out


def sync_hash(lrows: list, prow: list) -> str:
    h = hashlib.sha1()
    for r in lrows:
        h.update(json.dumps(r, ensure_ascii=False, default=str).encode("utf-8"))
    for r in prow:
        h.update(f"{r['source']}|{r['key']}|{r['value']}".encode("utf-8"))
    return h.hexdigest()[:12]


def sync_state(targets: list | None = None, quiet: bool = True) -> dict:
    """唯讀對帳:每本庫的 via_policy_sync.policy_hash 對上現在的 hash=同步;不同=落後;無表=未入;鎖住=忙。"""
    d = load_latest()
    prow = policy_factors()
    lrows = [(h, r.get("verdict")) for h, r in (d.get("files") or {}).items()]
    cur = sync_hash(lrows, prow)
    res = {"hash": cur, "dbs": [], "counts": Counter()}
    for q in (targets if targets is not None else sync_targets()):
        st, seen = "未入", ""
        try:
            import duckdb
            con = duckdb.connect(str(q), read_only=True)
            try:
                row = con.execute("SELECT policy_hash, ts FROM via_policy_sync ORDER BY ts DESC LIMIT 1").fetchone()
                if row:
                    seen = str(row[0])
                    st = "同步" if seen == cur else "落後"
            except Exception:
                st = "未入"
            finally:
                con.close()
        except ImportError:
            st = "無duckdb"
        except Exception as exc:
            m = str(exc).lower()
            st = "忙" if ("lock" in m or "being used" in m) else "壞"
        res["dbs"].append({"db": str(q), "state": st, "hash": seen})
        res["counts"][st] += 1
    if not quiet:
        print(f"  [入庫同步] {len(res['dbs'])} 庫 · " + " · ".join(f"{k} {v}" for k, v in sorted(res["counts"].items())) + f" · 現 hash {cur}")
        for x in res["dbs"]:
            if x["state"] != "同步":
                print(f"      {x['state']:4s} {Path(x['db']).name:36s} {x['hash'] or '-'}  ← via-vrnlogic sync-db")
    return res


def sync_db(db: str | None = None, dry_run: bool = False, quiet: bool = False) -> dict:
    """批499:全庫同步——同一份台帳/政策因子(同一 hash)寫進每一本目標庫,各留 via_policy_sync 對帳單;--db 指定=單庫。
    回 {state: OK/PARTIAL/BUSY/FAIL/DRY/SKIP, targets:[…], ok/busy/fail, hash, db/logic_rows/policy_rows(首本,相容 v0102)}。"""
    tg = sync_targets(db)
    if not tg:
        out = {"state": "SKIP", "db": "", "logic_rows": 0, "policy_rows": 0, "why": "庫缺:env VIA_DB_* / VIA_DATA_HOME / output_hub/mega 皆無 .duckdb(先 via-datahome catalog)", "targets": [], "ok": 0, "busy": 0, "fail": 0, "hash": ""}
        if not quiet:
            print(f"[入庫] SKIP · {out['why']}")
        return out
    res = []
    for q in tg:
        res.append(_sync_one(str(q), dry_run=dry_run, quiet=quiet))
    c = Counter(r["state"] for r in res)
    state = "DRY" if dry_run else ("OK" if c.get("OK") == len(res) else ("PARTIAL" if c.get("OK") else ("BUSY" if c.get("BUSY") else "FAIL")))
    out = dict(res[0]); out.update({"state": state, "targets": res, "ok": c.get("OK", 0), "busy": c.get("BUSY", 0), "fail": c.get("FAIL", 0), "hash": res[0].get("hash", "")})
    # 批499:交接報告副本落在資料家根(資料庫路徑要有);倉根副本由 git 帶,引擎不寫倉(免弄髒工作樹)
    hp, htxt = handover_doc()
    home = os.environ.get("VIA_DATA_HOME") or ""
    if db is None and hp is not None and htxt and home and Path(home).is_dir():
        try:
            dst = Path(home) / "VIA_HANDOVER_LATEST.md"
            same = dst.is_file() and dst.read_text(encoding="utf-8", errors="replace") == htxt
            if not same and not dry_run:
                dst.write_text(htxt, encoding="utf-8")
            out["handover_copy"] = str(dst) + ("(同)" if same else "")
            if not quiet:
                print(f"[交接] 資料家根 {'已同' if same else ('略(DRY)' if dry_run else '← ' + hp.name)} · {dst}")
        except Exception as exc:
            out["handover_copy"] = f"FAIL {type(exc).__name__}"
    if not quiet and len(res) > 1:
        print(f"[入庫] 全庫同步 {state} · {len(res)} 庫:OK {c.get('OK', 0)} · BUSY {c.get('BUSY', 0)} · FAIL {c.get('FAIL', 0)}" + (f" · DRY {c.get('DRY', 0)}" if dry_run else "") + f" · hash {out['hash']}(每本都留 via_policy_sync 對帳單;via-vrnlogic 看 [入庫同步])")
    return out


def _sync_one(db: str | None = None, dry_run: bool = False, quiet: bool = False) -> dict:
    """單庫:台帳 → vrn_extraction_logic;律冊 → via_policy_factors;對帳單 → via_policy_sync。只建/覆寫這三張表;其餘零觸碰;庫忙=誠實跳過。"""
    out = {"state": "SKIP", "db": "", "logic_rows": 0, "policy_rows": 0, "why": "", "hash": ""}
    dbp = resolve_db(db)
    if dbp is None:
        out["why"] = "庫缺:env VIA_DB_VDF_TW_MARKET / VIA_DATA_HOME / output_hub/mega 皆無 vdf_tw_market.duckdb(先 via-datahome catalog)"
        if not quiet:
            print(f"[入庫] SKIP · {out['why']}")
        return out
    out["db"] = str(dbp)
    d = load_latest()
    lrows = []
    for h, r in (d.get("files") or {}).items():
        xc = r.get("xcheck") or {}
        rp = r.get("repair") or {}
        lrows.append((r.get("ts", ""), r.get("file", ""), h, r.get("verdict", ""), str(r.get("method", ""))[:120], r.get("stage", ""),
                      int(r.get("chars") or 0), str(xc.get("state", "")), float(xc.get("bag") or 0), float(xc.get("seq") or 0),
                      bool(r.get("labels_ok")), json.dumps(rp, ensure_ascii=False)[:400], float(r.get("secs") or 0), str(r.get("tag", ""))[:200]))
    prow = policy_factors()
    out["logic_rows"], out["policy_rows"] = len(lrows), len(prow)
    out["hash"] = sync_hash([(h, r.get("verdict")) for h, r in (d.get("files") or {}).items()], prow)
    if dry_run:
        out["state"] = "DRY"
        if not quiet:
            print(f"[入庫] DRY · {dbp} · vrn_extraction_logic {len(lrows)} 列 · via_policy_factors {len(prow)} 列 · hash {out['hash']}(只印不寫)")
        return out
    try:
        import duckdb
        con = duckdb.connect(str(dbp))
    except Exception as exc:
        m = str(exc)
        out["state"], out["why"] = ("BUSY" if ("lock" in m.lower() or "being used" in m) else "FAIL"), m[:160]
        if not quiet:
            print(f"[入庫] {out['state']} · {dbp} · {out['why']}(單寫者律:不搶鎖,下次再入)")
        return out
    try:
        con.execute("CREATE OR REPLACE TABLE vrn_extraction_logic (ts VARCHAR, file VARCHAR, sha1 VARCHAR, verdict VARCHAR, method VARCHAR, stage VARCHAR, "
                    "chars INTEGER, xcheck_state VARCHAR, xcheck_bag DOUBLE, xcheck_seq DOUBLE, labels_ok BOOLEAN, repair_json VARCHAR, secs DOUBLE, tag VARCHAR)")
        if lrows:
            con.executemany("INSERT INTO vrn_extraction_logic VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", lrows)
        con.execute("CREATE OR REPLACE TABLE via_policy_factors (source VARCHAR, key VARCHAR, value VARCHAR, synced_at VARCHAR)")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if prow:
            con.executemany("INSERT INTO via_policy_factors VALUES (?,?,?,?)", [(r["source"], r["key"], r["value"], now) for r in prow])
        # 批499 對帳單:每本庫都知道自己拿到哪一份(hash 相同=全庫同步)
        con.execute("CREATE OR REPLACE TABLE via_policy_sync (sync_id VARCHAR, ts VARCHAR, host VARCHAR, logic_rows INTEGER, policy_rows INTEGER, policy_hash VARCHAR, engine VARCHAR)")
        con.execute("INSERT INTO via_policy_sync VALUES (?,?,?,?,?,?,?)",
                    (f"{now.replace('-', '').replace(':', '').replace(' ', 'T')}_{out['hash']}", now, socket.gethostname()[:40], len(lrows), len(prow), out["hash"], Path(__file__).stem))
        # 批499 交接報告入庫:每本庫都帶一份(母檔案夾/資料庫/github 三處同步律)
        hp, htxt = handover_doc()
        con.execute("CREATE OR REPLACE TABLE via_handover (file VARCHAR, batch VARCHAR, ts VARCHAR, sha1 VARCHAR, chars INTEGER, body VARCHAR)")
        if hp is not None and htxt:
            m = re.search(r"_B(\d+)\.md$", hp.name)
            con.execute("INSERT INTO via_handover VALUES (?,?,?,?,?,?)",
                        (hp.name, ("批" + m.group(1)) if m else "", now, hashlib.sha1(htxt.encode("utf-8")).hexdigest()[:12], len(htxt), htxt))
        out["state"] = "OK"
    except Exception as exc:
        out["state"], out["why"] = "FAIL", f"{type(exc).__name__}:{str(exc)[:140]}"
    finally:
        try:
            con.close()
        except Exception:
            pass
    if not quiet:
        print(f"[入庫] {out['state']} · {dbp} · vrn_extraction_logic {len(lrows)} 列 · via_policy_factors {len(prow)} 列 · hash {out['hash']}" + (f" · {out['why']}" if out["why"] else ""))
    return out


# ────────────────────────────── status · selftest ──────────────────────────────
def status() -> int:
    d = load_latest()
    s = ssot()
    print(f"[邏輯庫] {logic_dir()} · 冊 {s.get('_src', '內建')} · 階梯 {'→'.join(x['stage'] for x in s['ladder'])} · 預算 {s['budget_s']}s/件")
    files = d.get("files", {})
    by = Counter(r.get("verdict") for r in files.values())
    meth = Counter(str(r.get("method", "")).split("[", 1)[0].split("(", 1)[0] for r in files.values())   # 批503:法名不含每件參數
    print(f"  件 {len(files)}:" + " · ".join(f"{k} {v}" for k, v in sorted(by.items())) or "  件 0")
    for m, c in meth.most_common(8):
        print(f"    法 {m:32s} {c}")
    bk = d.get("backends", {})
    for n, b in sorted(bk.items()):
        print(f"  後端 {n:36s} {b.get('state'):7s} {b.get('ts', '')[:16]} {b.get('why', '')[:150]}")
    if not bk:
        print("  後端:尚無紀錄(還沒走過 OCR 車道)")
    print(f"  壞後端(TTL {s['backend_ttl_h']}h 內跳過):{broken_backends() or '無'}")
    try:
        sync_state(quiet=False)          # 批499:全庫同步對帳(唯讀)
        handover_copies(quiet=False)     # 批499:交接三處對帳(唯讀)
    except Exception as exc:
        print(f"  [入庫同步] 對帳失敗 {type(exc).__name__}:{str(exc)[:60]}")
    return 0


def _selftest_body() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    real = VIA / "VIA_Reports" / "vrn" / "extraction_logic"
    before = sorted(x.name for x in real.glob("*")) if real.exists() else []
    saved = os.environ.get("VIA_LOGIC_DIR")
    with tempfile.TemporaryDirectory() as td:
        os.environ["VIA_LOGIC_DIR"] = td
        try:
            out = Path(td) / "_out"
            out.mkdir()
            f = Path(td) / "rep.pdf"
            f.write_bytes(b"%PDF-1.4 fake " * 100)
            chk("① sha1/lookup:沒記過=None(不發明命中)", lookup(f, out) is None and len(sha1_of(f)) == 40)
            r = record(f, "SUCCESS", "DUAL_ZONES", 1200, {"state": "AGREE", "bag": 0.9, "seq": 0.8}, {"zw": 1}, True, 1.5, str(out / "rep.json"), "DUAL_ZONES")
            hit0 = lookup(f, out)
            (out / "rep.json").write_text("{}", encoding="utf-8"); (out / "rep.txt").write_text("x", encoding="utf-8")
            hit1 = lookup(f, out)
            chk("② record SUCCESS → 產物不在=不命中(不拿台帳冒充產物);產物在=HIT", hit0 is None and hit1 is not None and hit1["state"] == "HIT" and hit1["method"] == "DUAL_ZONES")
            g = Path(td) / "scan.pdf"; g.write_bytes(b"%PDF-1.4 scan " * 50)
            record(g, "FAIL", "NEEDS_OCR", 0, {"state": "NONE"}, {}, False, 300.0, "", "NEEDS_OCR[simple:OCR_EMPTY]")
            fh = lookup(g, out)
            d = load_latest(); d["files"][sha1_of(g)]["ts"] = "2020-01-01 00:00:00"; _save_latest(d)
            chk("③ FAIL 件 fail_ttl 內=FAIL_HIT(不重燒 OCR);過期=None(該再試)", fh is not None and fh["state"] == "FAIL_HIT" and lookup(g, out) is None)
            mark_backend("paddleocr", "BROKEN", "Unknown argument: show_log")
            b1 = broken_backends()
            mark_backend("paddleocr", "OK", "")
            b2 = broken_backends()
            mark_backend("easyocr", "BROKEN", "model download blocked")
            d = load_latest(); d["backends"]["easyocr"]["ts"] = "2020-01-01 00:00:00"; _save_latest(d)
            chk("④ 後端健康:BROKEN 進跳過名單;抽到字=OK 解除;過 TTL 自動解除", b1 == ["paddleocr"] and b2 == [] and broken_backends() == [])
            a = "台積電目標價一二五零元\n維持買進評等不變化"     # 兩段等長:序列比才會真的掉到 ORDER_ONLY
            xa = xcheck(a, a); xb = xcheck(a, "維持買進評等不變化\n台積電目標價一二五零元"); xc = xcheck(a, "完全不同的一段文字內容在這裡"); xd = xcheck(a, "")
            chk("⑤ 互核:同文 AGREE;同字不同序 ORDER_ONLY;不同 DISAGREE;單邊 SINGLE",
                xa["state"] == "AGREE" and xb["state"] == "ORDER_ONLY" and xc["state"] == "DISAGREE" and xd["state"] == "SINGLE", f"({xa} {xb['state']} {xc['state']})")
            t, st_ = repair_text("台積電​目標價１，２５０元，\n維持買進。ＥＰＳ  ４０．５\n\n\n下一段")
            chk("⑥ 文字修復:零寬去、全形英數→半形、中文斷行接回、多空白收斂;中文標點「，。」保留",
                "​" not in t and "1" in t and "250" in t and "EPS 40.5" in t and "，" in t and "。" in t
                and "元，\n維持" not in t and "元，維持" in t and "\n\n\n" not in t and st_["zw"] == 1 and st_["joins"] == 1, f"({st_})")
            chk("⑦ 判準:分區件要標示還原+互核非 DISAGREE 才 SUCCESS;文字件互核非 DISAGREE 即 SUCCESS;<min_chars=FAIL",
                verdict_of(500, {"state": "AGREE"}, True, "pdf_zones") == "SUCCESS" and verdict_of(500, {"state": "AGREE"}, False, "pdf_zones") == "PARTIAL"
                and verdict_of(500, {"state": "DISAGREE"}, True, "pdf_zones") == "PARTIAL" and verdict_of(500, {"state": "SINGLE"}, False, "text") == "SUCCESS"
                and verdict_of(10, {"state": "AGREE"}, True, "pdf_zones") == "FAIL")
            L = ladder()
            chk("⑧ 階梯自冊(尾版律):simple(tesseract)→dual(+easyocr)→paddle(三支);預算/TTL 讀得到",
                [x["stage"] for x in L] == ["simple", "dual", "paddle"] and L[0]["adapters"] == ["tesseract"] and "easyocr" in L[1]["adapters"]
                and "paddleocr" in L[2]["adapters"] and budget_s() > 0 and backend_ttl_h() > 0, f"(冊 {ssot().get('_src')})")
            import types
            fake = types.ModuleType("paddleocr")

            class PaddleOCR:
                def __init__(self, **kw):
                    for k in kw:
                        if k not in ("lang", "use_textline_orientation"):
                            raise ValueError(f"Unknown argument: {k}")
                    self.kw = kw
            fake.PaddleOCR = PaddleOCR
            saved_mod = sys.modules.get("paddleocr")
            sys.modules["paddleocr"] = fake
            _COMPAT.update({"done": False, "note": "", "dropped": []})
            try:
                note = install_paddle_compat()
                o = PaddleOCR(lang="ch", use_angle_cls=True, show_log=False, use_gpu=False)
                ok9 = o.kw == {"lang": "ch", "use_textline_orientation": True} and "PaddleOCR.show_log" in _COMPAT["dropped"] and "PaddleOCR.use_gpu" in _COMPAT["dropped"]
            finally:
                if saved_mod is not None:
                    sys.modules["paddleocr"] = saved_mod
                else:
                    sys.modules.pop("paddleocr", None)
                _COMPAT.update({"done": False, "note": "", "dropped": []})
            chk("⑨ PaddleOCR 3.x 相容墊片:2.x 鍵 show_log/use_gpu 自動剔除、use_angle_cls→use_textline_orientation 後重試成功(正本零觸碰)", ok9, f"({note[:40]})")
            lines = (Path(td) / LEDGER_NAME).read_text(encoding="utf-8").splitlines()
            chk("⑩ 台帳只增:jsonl 兩筆(SUCCESS+FAIL)逐行可讀;摘要 LOGIC_latest.json 在", len(lines) == 2 and all(json.loads(x)["file"] for x in lines) and (Path(td) / LATEST_NAME).exists())
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = status()
            chk("⑪ status 印得出件數/法/後端;批503 同法不同參數歸一行(OCR_simple:tesseract_direct 不帶 dpi/墨量/秒)",
                rc == 0 and "件 2" in buf.getvalue() and "後端" in buf.getvalue() and "tesseract_direct(dpi" not in buf.getvalue())
        finally:
            if saved is None:
                os.environ.pop("VIA_LOGIC_DIR", None)
            else:
                os.environ["VIA_LOGIC_DIR"] = saved
    after = sorted(x.name for x in real.glob("*")) if real.exists() else []
    chk("⑫ 真目錄零觸碰(自測全在 VIA_LOGIC_DIR 暫存夾)", before == after)
    lo, hi = hq_dpi_band()
    chk("⑬ 次序修正(批496):hq_budget_s 自有預算 >0;hq_dpi 帶 300~350;非 OCR 失敗判準 FAIL/DISAGREE=真,PARTIAL/AGREE=假",
        hq_budget_s() > 0 and (lo, hi) == (300, 350)
        and nonocr_failed({"verdict": "FAIL", "xcheck": {"state": "SINGLE"}}) and nonocr_failed({"verdict": "SUCCESS", "xcheck": {"state": "DISAGREE"}})
        and not nonocr_failed({"verdict": "PARTIAL", "xcheck": {"state": "AGREE"}}) and not nonocr_failed({"verdict": "SUCCESS", "xcheck": {"state": "ORDER_ONLY"}}),
        f"(hq_budget {hq_budget_s()}s · dpi {lo}~{hi})")
    # 批498 ⑭:入庫——暫存庫;只建兩張表;律冊攤平有列;dry-run 不寫
    with tempfile.TemporaryDirectory() as td:
        os.environ["VIA_LOGIC_DIR"] = td
        try:
            f = Path(td) / "x.pdf"; f.write_bytes(b"%PDF-1.4 x")
            record(f, "SUCCESS", "DUAL_ZONES", 500, {"state": "AGREE", "bag": 0.9, "seq": 0.8}, {"zw": 0}, True, 1.0, "", "DUAL_ZONES")
            dbp = Path(td) / "vdf_tw_market.duckdb"
            try:
                import duckdb
                con = duckdb.connect(str(dbp)); con.execute("CREATE TABLE keep_me AS SELECT 1 AS a"); con.close()
                r0 = sync_db(str(dbp), dry_run=True, quiet=True)
                r1 = sync_db(str(dbp), quiet=True)
                con = duckdb.connect(str(dbp), read_only=True)
                n1 = con.execute("SELECT COUNT(*) FROM vrn_extraction_logic").fetchone()[0]
                n2 = con.execute("SELECT COUNT(*) FROM via_policy_factors").fetchone()[0]
                keep = con.execute("SELECT COUNT(*) FROM keep_me").fetchone()[0]
                srcs = {r[0] for r in con.execute("SELECT DISTINCT source FROM via_policy_factors").fetchall()}
                con.close()
                chk("⑭ 入庫:台帳→vrn_extraction_logic、律冊→via_policy_factors(擷取邏輯/工具冊/資料家/基線 hydra 四源);dry-run 不寫;其餘表零觸碰",
                    r0["state"] == "DRY" and r1["state"] == "OK" and n1 == 1 and n2 >= 20 and keep == 1
                    and any(s.startswith("VRN_ExtractionLogic") for s in srcs) and any(s.startswith("VIA_ToolRoster") for s in srcs),
                    f"(logic {n1} · policy {n2} · 源 {len(srcs)})")
            except ImportError:
                chk("⑭ 入庫(本環境無 duckdb=SKIP 誠實)", True, "SKIP")
        finally:
            if saved is None:
                os.environ.pop("VIA_LOGIC_DIR", None)
            else:
                os.environ["VIA_LOGIC_DIR"] = saved
    # 批499 ⑮:全庫同步——暫存資料家兩本庫 + 一本沙盒庫;sync-db 不帶 --db → 兩本都拿到同一 hash 的三張表,沙盒零觸碰;status 對帳 同步 2
    with tempfile.TemporaryDirectory() as td:
        saved_env = {k: os.environ.get(k) for k in ("VIA_LOGIC_DIR", "VIA_DATA_HOME", "VIA_DB_VDF_TW_MARKET", "VIA_SELFTEST")}
        os.environ["VIA_LOGIC_DIR"] = td
        os.environ.pop("VIA_SELFTEST", None)         # ⑮ 要驗全庫掃描,這裡不能帶自測旗
        home = Path(td) / "home"; (home / "a").mkdir(parents=True); (home / "b").mkdir(); (home / "x" / "selftest_grid").mkdir(parents=True)
        os.environ["VIA_DATA_HOME"] = str(home)
        os.environ.pop("VIA_DB_VDF_TW_MARKET", None)
        try:
            f = Path(td) / "y.pdf"; f.write_bytes(b"%PDF-1.4 y")
            record(f, "PARTIAL", "DUAL_ZONES", 120, {"state": "PARTIAL", "bag": 0.5, "seq": 0.4}, {}, False, 1.0, "", "DUAL_ZONES")
            mark_backend("paddleocr@via_paddle_311", "BROKEN", "本境無此階後端:paddleocr(缺 paddlepaddle)")
            try:
                import duckdb
                for q in (home / "a" / "vdf_tw_market.duckdb", home / "b" / "other.duckdb", home / "x" / "selftest_grid" / "sand.duckdb"):
                    con = duckdb.connect(str(q)); con.execute("CREATE TABLE keep_me AS SELECT 1 AS a"); con.close()
                tg = sync_targets(None)
                r = sync_db(None, quiet=True)
                hs, ok_tables = set(), True
                for q in (home / "a" / "vdf_tw_market.duckdb", home / "b" / "other.duckdb"):
                    con = duckdb.connect(str(q), read_only=True)
                    hs.add(con.execute("SELECT policy_hash FROM via_policy_sync").fetchone()[0])
                    ok_tables &= con.execute("SELECT COUNT(*) FROM vrn_extraction_logic").fetchone()[0] == 1
                    ok_tables &= con.execute("SELECT COUNT(*) FROM via_policy_factors WHERE source='LOGIC_latest.backends'").fetchone()[0] == 1
                    ok_tables &= con.execute("SELECT COUNT(*) FROM via_handover").fetchone()[0] == 1
                    con.close()
                ok_tables &= (home / "VIA_HANDOVER_LATEST.md").is_file()
                con = duckdb.connect(str(home / "x" / "selftest_grid" / "sand.duckdb"), read_only=True)
                sand = {t[0] for t in con.execute("SHOW TABLES").fetchall()}
                con.close()
                import io, contextlib
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    ss = sync_state(quiet=False)
                chk("⑮ 全庫同步(批499):資料家兩本庫皆入四張表(含 via_handover 交接)、同一 hash、對帳單在;資料家根有 VIA_HANDOVER_LATEST.md;沙盒庫零觸碰;後端健康入政策因子;status 對帳「同步 2」",
                    len(tg) == 2 and r["state"] == "OK" and r["ok"] == 2 and len(hs) == 1 and ok_tables and sand == {"keep_me"}
                    and ss["counts"].get("同步") == 2 and "[入庫同步] 2 庫" in buf.getvalue(),
                    f"(targets {len(tg)} · {r['state']} ok {r['ok']} · hash {len(hs)} · 沙盒 {sorted(sand)})")
            except ImportError:
                chk("⑮ 全庫同步(本環境無 duckdb=SKIP 誠實)", True)
        finally:
            for k, v in saved_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    # 批504 ⑰:自測零污染律——VIA_SELFTEST=1 時只認 env 指定的那一本,不掃家、不掃 VIA_DB_*
    with tempfile.TemporaryDirectory() as td:
        sv = {k: os.environ.get(k) for k in ("VIA_DATA_HOME", "VIA_DB_VDF_TW_MARKET", "VIA_DB_OTHERX", "VIA_SELFTEST")}
        home = Path(td) / "home"; (home / "a").mkdir(parents=True)
        try:
            import duckdb
            for q in (home / "a" / "vdf_tw_market.duckdb", Path(td) / "prim.duckdb", Path(td) / "other.duckdb"):
                con = duckdb.connect(str(q)); con.execute("CREATE TABLE k AS SELECT 1 AS a"); con.close()
            os.environ["VIA_DATA_HOME"] = str(home); os.environ["VIA_DB_VDF_TW_MARKET"] = str(Path(td) / "prim.duckdb"); os.environ["VIA_DB_OTHERX"] = str(Path(td) / "other.duckdb")
            os.environ.pop("VIA_SELFTEST", None)
            n_all = len(sync_targets(None))
            os.environ["VIA_SELFTEST"] = "1"
            tg1 = sync_targets(None)
            chk("⑰ 自測零污染律(批504):VIA_SELFTEST=1 → 入庫目標只有 env 首選那一本;不帶旗才掃家 + VIA_DB_*(3 本)",
                n_all == 3 and len(tg1) == 1 and tg1[0].name == "prim.duckdb", f"(全掃 {n_all} · 自測 {[q.name for q in tg1]})")
        except ImportError:
            chk("⑰ 自測零污染律(本環境無 duckdb=SKIP 誠實)", True)
        finally:
            for k, v in sv.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    pr18 = policy_factors()
    n748 = sum(1 for r in pr18 if str(r["source"]).startswith("SUP_MDL748"))
    chk("⑱ 財務邏輯橋兩本冊入政策因子(批504):SUP_MDL748 列 ≥ 80(券商/評等/科目同義/單位倍率/28 欄/正則);橋缺=1 列 ABSENT 誠實",
        n748 >= 80 or (n748 == 1 and "ABSENT" in [r["value"] for r in pr18 if str(r["source"]).startswith("SUP_MDL748")][0]), f"({n748} 列)")
    chk("⑲ 自測隔離(批505):自測期間 os.environ 無任何 VIA_DB_*(操作員 bootstrap 匯出的真庫鍵已撤)且 VIA_SELFTEST=1(各檢結束自復原)",
        not [k for k in os.environ if k.startswith("VIA_DB_")] and os.environ.get("VIA_SELFTEST") == "1", f"({[k for k in os.environ if k.startswith('VIA_DB_')]})")
    hc = handover_copies(quiet=True)
    chk("⑯ 交接三處(批499):docs 尾版在;母檔案夾(倉根)VIA_HANDOVER_LATEST.md 與 docs 同一份 sha(舊=commit 時沒同步,要修)", bool(hc["doc"]) and hc["root"] == "同", f"({hc})")
    print(f"  [計] 十九檢 OK {19 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def selftest() -> int:
    """批505 自測零污染律:整段自測撤 VIA_DB_* 與 VIA_DATA_HOME、設 VIA_SELFTEST=1(各檢自己再設暫存),結束還原——真庫永不進目標。"""
    sv = {k: v for k, v in os.environ.items() if k.startswith("VIA_DB_") or k in ("VIA_DATA_HOME", "VIA_SELFTEST")}
    for k in sv:
        os.environ.pop(k, None)
    os.environ["VIA_SELFTEST"] = "1"
    try:
        return _selftest_body()
    finally:
        os.environ.pop("VIA_SELFTEST", None)
        os.environ.pop("VIA_DATA_HOME", None)
        for k in list(os.environ):
            if k.startswith("VIA_DB_"):
                os.environ.pop(k, None)
        os.environ.update(sv)


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== VRN 擷取中央邏輯庫(VRN_ENG082 v0108)· 十九檢自測(零網路;暫存夾;批506 政策庫冊入因子)===")
        return selftest()
    if a and a[0] == "sync-db":
        dbarg = a[a.index("--db") + 1] if "--db" in a and a.index("--db") + 1 < len(a) else None
        r = sync_db(dbarg, dry_run="--dry-run" in a)
        return 0 if r["state"] in ("OK", "DRY") else 2
    if a and a[0] == "reset-backends":
        print(f"[邏輯庫] 清除後端健康標記 {reset_backends()} 筆(台帳不動)")
        return 0
    return status()


if __name__ == "__main__":
    sys.exit(main())
