#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VRN_ENG082_ExtractionLogic v0101 — VRN 擷取**中央邏輯庫**(批493 操作員令;批496 次序修正)
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
用法:python3 VRN_ENG082_ExtractionLogic_v0101.py [status|reset-backends] | --selftest
律:只增不減;誠實三態;零網路;零刪除(reset-backends 只清健康標記,不動台帳)。
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
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
    d["backends"][str(name)] = {"state": state, "why": str(why)[:160], "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
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


# ────────────────────────────── status · selftest ──────────────────────────────
def status() -> int:
    d = load_latest()
    s = ssot()
    print(f"[邏輯庫] {logic_dir()} · 冊 {s.get('_src', '內建')} · 階梯 {'→'.join(x['stage'] for x in s['ladder'])} · 預算 {s['budget_s']}s/件")
    files = d.get("files", {})
    by = Counter(r.get("verdict") for r in files.values())
    meth = Counter(str(r.get("method", "")).split("[", 1)[0] for r in files.values())
    print(f"  件 {len(files)}:" + " · ".join(f"{k} {v}" for k, v in sorted(by.items())) or "  件 0")
    for m, c in meth.most_common(8):
        print(f"    法 {m:32s} {c}")
    bk = d.get("backends", {})
    for n, b in sorted(bk.items()):
        print(f"  後端 {n:22s} {b.get('state'):7s} {b.get('ts', '')[:16]} {b.get('why', '')[:70]}")
    if not bk:
        print("  後端:尚無紀錄(還沒走過 OCR 車道)")
    print(f"  壞後端(TTL {s['backend_ttl_h']}h 內跳過):{broken_backends() or '無'}")
    return 0


def selftest() -> int:
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
            chk("⑪ status 印得出件數/法/後端", rc == 0 and "件 2" in buf.getvalue() and "後端" in buf.getvalue())
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
    print(f"  [計] 十三檢 OK {13 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== VRN 擷取中央邏輯庫(VRN_ENG082 v0101)· 十三檢自測(零網路;暫存夾)===")
        return selftest()
    if a and a[0] == "reset-backends":
        print(f"[邏輯庫] 清除後端健康標記 {reset_backends()} 筆(台帳不動)")
        return 0
    return status()


if __name__ == "__main__":
    sys.exit(main())
