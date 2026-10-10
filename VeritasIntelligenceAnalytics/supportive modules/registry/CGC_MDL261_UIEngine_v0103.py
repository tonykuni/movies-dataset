#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL261_UIEngine v0103 — 薄尾:VIA 操作台(左功能可收合 · 右五頁顯示 · 白底資料總冊視覺 · 建完自動跳出)

操作員令(2026-10-10):VDF 實測後跳出 HTML U/I,左面板 = 功能、右面板 = 顯示。
  左面板唯一會變更的輸入:各大類起始日(族群冊 categories)· 國內個股財報(TW_FIN)· 國外個股財報(INTL_FIN)·
    國外個股資料(INTL_DAILY)增減 · 啟動(匯出輸入 + 指令)· 跳 VCGC / VDF 閘;各段可伸縮,整個左面板可收合。
  右面板:① 輸入矩陣(資料總冊 390 項 → 操作員大類,全選)+ 引擎狀態矩陣 + 結果矩陣 + 結果驗證摘要
          ② BASIC INFO ③ FINANCIAL DATA ④ 修正後首頁全文(一句一行 · 一標題一行 · 自動分行)+ 首頁 INFO AREA + 標題 + 四點摘要
          ⑤ SSOT / REGEX / 同義字 / 關聯註冊引擎(版本號 · 中央編號)/ 邏輯 / 輸入 / 參數 / 輸出 自動編號矩陣
  大類歸屬 · 閘門 · 指令 · 第五頁分段都讀 supportive modules/ui_support/VIA_UI_OperatorConsole_SSOT_v*.json(尾版),程式不寫死。
  四點摘要 quote-or-abstain:原句節錄,不改寫不歸納;資料只讀(VRN DuckDB read_only、報表 JSON);不連網、不寫冊。
  匯入:import 照 v0101(起始日 / 財報成員 → MDL012 ui-import);國外個股資料另走 MDL012 add / remove(同一個匯入檔,先乾跑)。
  build --open:建完自動跳出(VIA_NO_OPEN=1 不開)。其餘照 v0102。只收 VCGC 呼叫。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入;本檔零網路,橋只為全樹一致。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VDF_DIR = VIA / "functional modules" / "VDF"
VRN_DIR = VIA / "functional modules" / "VRN"
UI_DIR = VIA / "supportive modules" / "ui_support"
REPORTS = VIA / "VIA_Reports"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path() -> Path:
    """前版 = 同家族比本檔小的最大版號(不釘名,避免 PINVER)。"""
    me = _vnum(__file__)
    hits = [p for p in HERE.glob("CGC_MDL261_UIEngine_v*.py") if 0 <= _vnum(p) < me]
    return max(hits, key=_vnum)


PRIOR_PATH = _prior_path()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE           # v0100 本體:build / inject / BUILTIN / snapshot 在這裡


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


TAG = f"CGC_MDL261_UIEngine v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
_SNAPSHOT_V0102 = BASE.snapshot
BUILTIN_V0102 = PRIOR.BUILTIN_V0102 if hasattr(PRIOR, "BUILTIN_V0102") else BASE.BUILTIN

for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


# ---------- 小工具(只讀) ----------
def _tail(folder: Path, pattern: str):
    hits = [p for p in Path(folder).glob(pattern) if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _load(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, TypeError):
        return default


def _jsonl(p) -> list:
    out = []
    try:
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    except OSError:
        pass
    return out


def _cut(v, n=240):
    s = "" if v is None else str(v)
    return s if len(s) <= n else s[: n - 1] + "…"


def _rel(p) -> str:
    try:
        return Path(p).resolve().relative_to(VIA).as_posix()
    except ValueError:
        return str(p)


def oc_book() -> dict:
    p = _tail(UI_DIR, "VIA_UI_OperatorConsole_SSOT_v*.json")
    book = _load(p, {}) if p else {}
    book["_path"] = _rel(p) if p else None
    return book


# ---------- 第一頁:輸入矩陣(資料總冊 390 項 → 操作員大類,全選) ----------
def classify(item_ids: list, cats: list) -> dict:
    """每個資料項只歸一個大類:先比 ids,再比 prefixes(依冊上順序),都沒中歸 default 類。"""
    default = next((c["id"] for c in cats if c.get("default")), cats[-1]["id"] if cats else None)
    out = {}
    for iid in item_ids:
        hit = next((c["id"] for c in cats if iid in (c.get("ids") or [])), None)
        if not hit:
            hit = next((c["id"] for c in cats if any(iid.startswith(p) for p in (c.get("prefixes") or []))), None)
        out[iid] = hit or default
    return out


def input_matrix(book: dict, vdf: dict, reg_path=None) -> dict:
    p = Path(reg_path) if reg_path else _tail(VDF_DIR, "VDF_FetchOne_Matrix_Registry_v*.json")
    reg = _load(p, {}) if p else {}
    items = reg.get("items") or []
    cats = book.get("input_categories") or []
    starts = {c.get("id"): c for c in (vdf.get("categories") or [])}
    where = classify([it.get("id") for it in items], cats)
    rows = {c["id"]: [] for c in cats}
    for it in items:
        rows.setdefault(where.get(it.get("id")), []).append({
            "id": it.get("id"), "section": it.get("section"), "name": it.get("name"), "source": it.get("source"),
            "fetcher": it.get("fetcher"), "freq": it.get("freq"), "fields": _cut(it.get("fields"), 200),
            "refs": it.get("refs"), "status": it.get("status"), "selected": True})
    out = []
    for c in cats:
        rr = rows.get(c["id"]) or []
        st = {}
        for r in rr:
            st[r["status"]] = st.get(r["status"], 0) + 1
        sc = starts.get(c.get("start_category")) or {}
        out.append({"id": c["id"], "zh": c.get("zh"), "select": c.get("select", "ALL"), "start_category": c.get("start_category"),
                    "start": sc.get("start"), "n": len(rr), "selected": sum(1 for r in rr if r["selected"]), "states": st, "items": rr})
    ids = [it.get("id") for it in items]
    return {"registry": _rel(p) if p else None, "total": len(items), "assigned": sum(c["n"] for c in out),
            "dup_ids": sorted({i for i in ids if ids.count(i) > 1}), "counts": reg.get("counts_measured") or {},
            "sections": reg.get("sections_measured") or {}, "categories": out}


# ---------- 第一頁:引擎狀態矩陣 · 結果矩陣 · 結果驗證摘要 ----------
ENGINE_COLS = ["編號", "家族", "版本", "中央編號", "啟動前閘", "備料燈", "可啟動", "自測", "上次成功_資料", "上次成功_跑測", "短令"]


def engine_matrix(path=None) -> dict:
    p = Path(path) if path else REPORTS / "vdf" / "ENGINE_MATRIX_latest.json"
    d = _load(p)
    if not isinstance(d, dict) or not d.get("rows"):
        return {"state": "NODATA", "file": _rel(p), "rows": [], "note": "還沒有引擎矩陣 → via-vcgc run VDF_SystemManager engine matrix"}
    rows = [{k: _cut(r.get(k), 80) for k in ENGINE_COLS} for r in d["rows"]]
    return {"state": "OK", "file": _rel(p), "ts": d.get("ts"), "tag": d.get("tag"), "n": len(rows), "rows": rows, "summary": d.get("summary")}


def db_check(path=None) -> dict:
    p = Path(path) if path else REPORTS / "vdf" / "DB_CHECK_latest.json"
    d = _load(p)
    if not isinstance(d, dict):
        return {"state": "NODATA", "file": _rel(p), "rows": [], "note": "還沒有資料庫檢查 → via-vcgc run VDF_SystemManager db check"}
    return {"state": "OK", "file": _rel(p), "ts": d.get("ts"), "home": d.get("home"), "lamp": d.get("lamp"),
            "summary": d.get("summary"), "rows": d.get("rows") or []}


def fetch_test(path=None) -> dict:
    p = Path(path) if path else REPORTS / "vdf" / "FETCH_TEST_latest.txt"
    try:
        txt = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"state": "NODATA", "file": _rel(p), "lines": [], "note": "還沒有離線整合實測紀錄 → 左面板 ② VDF 離線整合實測(啟動器會存這個檔)"}
    head = next((ln.strip() for ln in txt.splitlines() if "整合測試" in ln and ("PASS" in ln or "FAIL" in ln)), "")
    lines = [ln.strip() for ln in txt.splitlines() if re.match(r"\s*\[(OK|FAIL)\]\s+MDL\d+", ln)]
    verdict = "PASS" if head.endswith("PASS") else ("FAIL" if "FAIL" in head else "UNKNOWN")
    return {"state": "OK", "file": _rel(p), "verdict": verdict, "head": head, "lines": lines,
            "ts": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")}


def result_matrix(vdf: dict) -> list:
    out = []
    for g in vdf.get("groups") or []:
        s = g.get("summary") or {}
        out.append({"id": g.get("id"), "zh": g.get("zh"), "category": g.get("category"), "membership": g.get("membership"),
                    "n": g.get("n"), "worst": s.get("worst") or "NODATA", "states": s.get("states") or {},
                    "max_date": s.get("max_date"), "rows_asof": s.get("rows_asof"),
                    "tables": [{"db": r.get("db_path"), "table": r.get("table_name"), "state": r.get("state"),
                                "rows": r.get("rows_total"), "note": _cut(r.get("note"), 120)} for r in (g.get("rows") or [])]})
    return out


def _lamp_of(counts: dict) -> str:
    if counts.get("RED"):
        return "RED"
    if counts.get("YELLOW") or counts.get("NODATA"):
        return "YELLOW"
    return "GREEN" if counts else "NODATA"


def validation(inp: dict, eng: dict, db: dict, groups: list, ft: dict, vrn: dict) -> dict:
    rows = []
    ok_assign = inp["total"] > 0 and inp["assigned"] == inp["total"] and not inp["dup_ids"]
    st = inp.get("counts") or {}
    rows.append({"face": "輸入矩陣", "lamp": "GREEN" if ok_assign else "RED",
                 "value": f"{inp['assigned']} / {inp['total']} 項全選 · 大類 {len(inp['categories'])}",
                 "note": f"DONE {st.get('DONE', 0)} · PROXY {st.get('PROXY', 0)} · TODO {st.get('TODO', 0)}(冊上狀態)"})
    if eng.get("state") == "OK":
        can = sum(1 for r in eng["rows"] if str(r.get("可啟動")).strip() in ("是", "YES", "True", "✓", "GREEN"))
        selftest_ok = sum(1 for r in eng["rows"] if "PASS" in str(r.get("自測")) or str(r.get("自測")).strip() in ("✓", "GREEN", "OK"))
        rows.append({"face": "引擎狀態", "lamp": "GREEN" if can == eng["n"] else "YELLOW",
                     "value": f"可啟動 {can} / {eng['n']} · 自測過 {selftest_ok}", "note": f"矩陣 {eng.get('ts') or ''}"})
    else:
        rows.append({"face": "引擎狀態", "lamp": "NODATA", "value": "—", "note": eng.get("note")})
    if db.get("state") == "OK":
        c = {}
        for r in db["rows"]:
            c[r.get("燈") or "NODATA"] = c.get(r.get("燈") or "NODATA", 0) + 1
        rows.append({"face": "資料庫檢查", "lamp": db.get("lamp") or _lamp_of(c), "value": " · ".join(f"{k} {v}" for k, v in sorted(c.items())),
                     "note": f"家 {db.get('home') or '—'} · {db.get('ts') or ''}"})
    else:
        rows.append({"face": "資料庫檢查", "lamp": "NODATA", "value": "—", "note": db.get("note")})
    gc = {}
    for g in groups:
        gc[g["worst"]] = gc.get(g["worst"], 0) + 1
    rows.append({"face": "族群結果(as-of)", "lamp": _lamp_of(gc), "value": " · ".join(f"{k} {v}" for k, v in sorted(gc.items())),
                 "note": "NODATA = 本機資料家沒有該表(雲端容器只有快取;實際資料在工作站)"})
    rows.append({"face": "VDF 離線整合實測", "lamp": {"PASS": "GREEN", "FAIL": "RED"}.get(ft.get("verdict"), "NODATA"),
                 "value": ft.get("head") or "—", "note": ft.get("note") or f"{len(ft.get('lines') or [])} 模組 · {ft.get('ts') or ''}"})
    rows.append({"face": "VRN 報告", "lamp": "GREEN" if vrn.get("reports") else "NODATA",
                 "value": f"報告 {len(vrn.get('reports') or [])} · 首頁全文 {len(vrn.get('docs') or [])} · 摘要驗證 {sum(1 for d in vrn.get('docs') or [] if d.get('summary_ok'))}",
                 "note": vrn.get("note") or ""})
    lamps = [r["lamp"] for r in rows]
    lamp = "RED" if "RED" in lamps else "YELLOW" if ("YELLOW" in lamps or "NODATA" in lamps) else "GREEN"
    return {"lamp": lamp, "rows": rows}


# ---------- 第二~四頁:VRN BASIC INFO · FINANCIAL DATA · 首頁全文 ----------
BASIC_COLS = ["report_file", "ticker", "name_official", "broker", "broker_name_zh", "report_date", "rating_raw", "rating_code",
              "rating_direction", "target_price", "price", "upside_report", "upside_calc", "upside_state", "target_price_adj",
              "price_latest_adj", "upside_adj", "analyst_names", "report_kind", "ssot_state", "conflicts", "title_head",
              "report_age_days", "target_freshness", "extracted_at"]
INFO_LABELS = r"(?=(?:評等|投資評等|目標價|收盤價|潛在漲幅|潛在上漲|分析師|報告日期|EPS|ROE|本益比|股價|市值|產業別|發行股數|前次評等)\s*[:：(（])"
_SENT = re.compile(r"(?<=[。！？；!?])\s*|(?<=[.])\s+(?=[A-Z0-9【(（➢•])|\s*(?=➢)")
_TITLE = re.compile(r"^(【[^】]{1,40}】|#{1,4}\s.+|\d+(\.\d+){0,2}\s+\S.{0,38}|[一二三四五六七八九十]+、.{1,30})$")


# 不是標題的短行:圖表刻度數字 · 日期 · 單位 · 電話 / Email(批 R63 實測:99 / May-25 / (TWD) / 21 May 2026 被誤判成標題)
_NUMLIKE = re.compile(r"^[\d\s.,%+\-−()/xX倍元]+$")
_DATELIKE = re.compile(r"^(\d{1,2}\s+[A-Za-z]{3,9}\.?,?\s+\d{2,4}|[A-Za-z]{3,9}\.?[-\s']\d{2,4}|\d{2,4}[-/.]\d{1,2}([-/.]\d{1,2})?|\d{1,2}[A-Za-z]{2,3}\d{2}|\d{1,2}Q\d{2}[A-Z]?|[1-4]Q\d{2,4}[A-Z]?|20\d{2}[A-Z]?)$")
_UNIT = re.compile(r"^[(（]?[A-Za-z%$¥€]{1,4}[)）]?$")


def _is_title(line: str, names=()) -> bool:
    if line in names or _NUMLIKE.match(line) or _DATELIKE.match(line) or _UNIT.match(line) or "@" in line:
        return False
    if _TITLE.match(line):
        return True
    if len(line) > 24 or re.search(r"[，,。；;：:、]", line) or re.search(r"\d{3,}", line):
        return False
    return len(re.findall(r"[A-Za-z\u4e00-\u9fff]", line)) >= 3


def split_sentences(text: str, names=()) -> list:
    out = []
    names = {n.strip() for n in names if n and n.strip()}
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if _is_title(line, names):
            out.append({"kind": "title", "text": line})
            continue
        for s in _SENT.split(line):
            s = (s or "").strip()
            if s:
                out.append({"kind": "text", "text": s})
    return out


def info_lines(text: str) -> list:
    out = []
    for raw in (text or "").splitlines():
        for part in re.split(INFO_LABELS, raw):
            part = part.strip()
            if part:
                out.append(part)
    return out


def _doc_from_sidecar(p: Path) -> dict | None:
    d = _load(p)
    if not isinstance(d, dict) or not d.get("sentences"):
        return None
    heads = [h.get("text", "").strip() for h in d.get("heads") or [] if h.get("text")]
    lines = []
    for s in d.get("sentences") or []:
        s = str(s).strip()
        h = next((x for x in heads if x and s.startswith(x)), None)
        if h:
            lines.append({"kind": "title", "text": h})
            s = s[len(h):].strip()
        if s:
            lines.append({"kind": "text", "text": s})
    body = [x["text"] for x in lines if x["kind"] == "text"]
    return {"id": p.stem, "source": "首頁擷取 sidecar(VRN_ENG072)", "file": _rel(p), "title": heads[0] if heads else (body[0] if body else p.stem),
            "lines": lines, "info": info_lines(d.get("right") or ""), "info_source": "首頁右側資訊區(原文)",
            "summary": [{"text": t, "score": None} for t in body[:4]], "summary_rule": "沒有 NLP 分數 → 本文前 4 句原句",
            "summary_ok": all(t in "\n".join(d.get("sentences") or []) for t in body[:4]) and bool(body)}


def _doc_from_nlp(row: dict, basic: dict | None) -> dict:
    text = row.get("normalized_text") or ""
    b = basic or {}
    lines = split_sentences(text, re.split(r"[,;、/|]", str(b.get("analyst_names") or "")))
    pts = []
    try:
        pts = json.loads(row.get("summary_points_json") or "[]")
    except ValueError:
        pts = []
    pts = [p for p in pts if isinstance(p, dict) and p.get("text")]
    top = sorted(pts, key=lambda p: -(p.get("score") or 0))[:4]
    top.sort(key=lambda p: ((p.get("source_span") or {}).get("start") or 0))
    summary = [{"text": p["text"], "score": round(p.get("score") or 0, 3), "quoted": p["text"] in text} for p in top]
    title = (b.get("title_head") or "").strip() or next((x["text"] for x in lines if x["kind"] == "title"), "") or (lines[0]["text"] if lines else row.get("report_file"))
    info = [f"{k}:{v}" for k, v in (("券商", b.get("broker_name_zh") or b.get("broker")), ("報告日期", b.get("report_date")),
                                     ("代號 · 名稱", " ".join(x for x in (b.get("ticker"), b.get("name_official")) if x)),
                                     ("評等", b.get("rating_raw")), ("目標價", b.get("target_price")), ("收盤價(報告)", b.get("price")),
                                     ("潛在漲幅(報告)", b.get("upside_report")), ("分析師", b.get("analyst_names"))) if v not in (None, "", [])]
    return {"id": row.get("report_file"), "source": "NLP 正規化全文(vrn_nlp_text_summary)", "file": "functional modules/VRN/db/vrn_reports.duckdb",
            "title": _cut(title, 160), "lines": lines, "info": info, "info_source": "BASIC INFO 欄位組成(這份沒有首頁右側原文 sidecar)",
            "summary": summary, "summary_rule": "NLP 分數最高 4 句原句,依原文順序", "summary_ok": bool(summary) and all(s["quoted"] for s in summary),
            "summary_state": row.get("summary_state")}


def vrn_data(db_path=None, basicinfo_path=None, fin_path=None, sidecar_dir=None) -> dict:
    out = {"state": "NODATA", "sources": [], "reports": [], "basic": [], "analysts": {}, "metrics": {}, "fin": {}, "basicinfo": [], "docs": [], "note": ""}
    db = Path(db_path) if db_path else VRN_DIR / "db" / "vrn_reports.duckdb"
    basic_by = {}
    nlp_rows = []
    try:
        import duckdb
        con = duckdb.connect(str(db), read_only=True)
        try:
            have = {r[0] for r in con.execute("select table_name from information_schema.tables").fetchall()}
            if "vrn_report_basic" in have:
                cols = [r[0] for r in con.execute("describe vrn_report_basic").fetchall()]
                use = [c for c in BASIC_COLS if c in cols]
                for r in con.execute(f"select {', '.join(use)} from vrn_report_basic order by report_date desc nulls last").fetchall():
                    d = {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in zip(use, r)}
                    d = {k: (_cut(v, 300) if isinstance(v, str) else v) for k, v in d.items()}
                    out["basic"].append(d)
                    basic_by[d.get("report_file")] = d
            if "vrn_report_analyst" in have:
                for r in con.execute("select report_file, analyst_zh, analyst_en, email, phones, institution, zone, confidence from vrn_report_analyst").fetchall():
                    out["analysts"].setdefault(r[0], []).append({"zh": r[1], "en": r[2], "email": r[3], "phones": r[4], "institution": r[5],
                                                                 "zone": r[6], "confidence": round(r[7] or 0, 2)})
            if "vrn_report_metrics" in have:
                for r in con.execute("select report_file, metric, period, status, value, raw_text from vrn_report_metrics").fetchall():
                    out["metrics"].setdefault(r[0], []).append({"metric": r[1], "period": r[2], "status": r[3], "value": r[4], "raw": _cut(r[5], 160)})
            if "vrn_nlp_text_summary" in have:
                for r in con.execute("select report_file, normalized_text, summary_points_json, summary_state from vrn_nlp_text_summary").fetchall():
                    nlp_rows.append({"report_file": r[0], "normalized_text": (r[1] or "")[:30000], "summary_points_json": r[2], "summary_state": r[3]})
        finally:
            con.close()
        out["sources"].append(_rel(db))
    except Exception as exc:  # noqa: BLE001 — 照實記下為什麼沒有
        out["note"] = f"VRN 資料庫讀不到:{type(exc).__name__}: {_cut(exc, 120)}"
    bi = _load(Path(basicinfo_path) if basicinfo_path else VRN_DIR / "StockReportBasicInfo.json", [])
    if isinstance(bi, list):
        out["basicinfo"] = [{k: _cut(v, 160) for k, v in r.items() if k != "SourcePath"} for r in bi]
        out["sources"].append("functional modules/VRN/StockReportBasicInfo.json")
    fin = _load(Path(fin_path) if fin_path else VDF_DIR / "StockReportFinancialData.json", [])
    if isinstance(fin, list):
        for r in fin:
            k = Path(str(r.get("SourceFile") or "")).stem
            out["fin"].setdefault(k, []).append({"page": r.get("Page"), "table": r.get("TableIndex"), "row": r.get("RowIndex"), "col": r.get("ColumnIndex"),
                                                 "metric": _cut(r.get("MetricRaw"), 80), "period": _cut(r.get("PeriodNormalized"), 120),
                                                 "value": _cut(r.get("ValueRaw"), 120), "core": r.get("CoreMetric"),
                                                 "status": r.get("ValidationStatus"), "risk": r.get("ValidationRisk")})
        out["sources"].append("functional modules/VDF/StockReportFinancialData.json")
    sdir = Path(sidecar_dir) if sidecar_dir else REPORTS / "first_page_text"
    for p in sorted(sdir.glob("*.json")) if sdir.is_dir() else []:
        doc = _doc_from_sidecar(p)
        if doc:
            out["docs"].append(doc)
    for r in nlp_rows:
        out["docs"].append(_doc_from_nlp(r, basic_by.get(r["report_file"])))
    rep = {}
    for b in out["basic"]:
        if b.get("ticker"):
            rep[b["report_file"]] = {"id": b["report_file"], "ticker": b.get("ticker"), "name": b.get("name_official"),
                                     "broker": b.get("broker_name_zh") or b.get("broker"), "date": b.get("report_date")}
    for k in out["fin"]:
        rep.setdefault(k, {"id": k, "ticker": (out["fin"][k][0] or {}).get("ticker", ""), "name": "", "broker": "", "date": ""})
    for d in out["docs"]:
        rep.setdefault(d["id"], {"id": d["id"], "ticker": "", "name": "", "broker": "", "date": ""})
    out["reports"] = sorted(rep.values(), key=lambda r: (str(r.get("date") or ""), r["id"]), reverse=True)
    out["state"] = "OK" if out["reports"] else "NODATA"
    return out


# ---------- 第五頁:SSOT · REGEX · 同義字 · 引擎 · 邏輯 · 輸入 · 參數 · 輸出 自動編號矩陣 ----------
def _row(code, name, sub, version, source, note="", lamp=""):
    return {"code": code or "—", "name": _cut(name, 120), "sub": sub or "—", "version": version or "—",
            "source": _cut(source, 140), "note": _cut(note, 260), "lamp": lamp or ""}


def page5(book: dict, vdf: dict, eng: dict) -> dict:
    reg = HERE
    num = _load(_tail(reg, "VIA_Numbering_SSOT_v*.json") or reg / "VIA_Numbering_SSOT_v0100.json", {}) or {}
    R = num.get("rows") or {}
    books = reg / "VIA_NumberBooks"
    secs = {}
    secs["SSOT"] = [_row(r.get("code"), r.get("name_zh") or r.get("name"), r.get("sub"), r.get("version"), r.get("source"), r.get("cat"), r.get("lamp"))
                    for r in R.get("SSOT") or []]
    rg = [_row(r.get("code"), r.get("name_zh") or r.get("name"), r.get("sub"), r.get("version"), r.get("source"), r.get("cat"), r.get("lamp"))
          for r in R.get("RGX") or []]
    central = _tail(reg, "VIA_Central_Synonym_Regex_v*.json")
    cr = (_load(central, {}) or {}).get("regex") or {}
    for k, v in cr.items():
        v = v if isinstance(v, dict) else {"pattern": v}
        rg.append(_row("中央鎖", k, "CORE", central.stem.rsplit("_", 1)[-1] if central else "", _rel(central) if central else "",
                       v.get("pattern"), "GREEN" if v.get("locked") else ""))
    s05 = _tail(reg, "VRN_S05_FieldRegistry_v*.json")
    for k, v in ((_load(s05, {}) or {}).get("all_regex") or {}).items():
        v = v if isinstance(v, dict) else {"pattern": v}
        rg.append(_row("S05", k, "VRN", s05.stem.rsplit("_", 1)[-1] if s05 else "", _rel(s05) if s05 else "",
                       f"{v.get('pattern')} · 例 {len(v.get('examples_pass') or [])} 過 / {len(v.get('examples_fail') or [])} 不過"))
    secs["RGX"] = rg
    secs["SYN"] = [_row(r.get("code"), r.get("name_zh") or r.get("name"), r.get("sub"), r.get("version"), r.get("cat"),
                        " ≡ ".join((r.get("words") or [])[:8]) or r.get("note"), r.get("lamp")) for r in R.get("SYN") or []]
    estate = {r.get("中央編號"): r for r in (eng.get("rows") or []) if r.get("中央編號")}
    er = []
    for r in _jsonl(books / "VIA_NumberBook_ENG_v0100.jsonl"):
        e = estate.get(r.get("code")) or {}
        er.append(_row(r.get("code"), r.get("name"), r.get("sub"), r.get("version"), r.get("source"),
                       (f"可啟動 {e.get('可啟動')} · 自測 {e.get('自測')} · 啟動前閘 {e.get('啟動前閘')}" if e else r.get("cat")), r.get("lamp")))
    secs["ENG"] = er
    secs["LGC"] = [_row(r.get("code"), r.get("name_zh") or r.get("name"), r.get("sub"), r.get("version"), r.get("source"), r.get("cat"), r.get("lamp"))
                   for r in _jsonl(books / "VIA_NumberBook_LGC_v0100.jsonl")]
    ins = [_row("UI", f"{v.get('zh')}({k})", "VDF", "", v.get("via"), "左面板可增減", "GREEN")
           for k, v in ((book.get("editable") or {}).get("members") or {}).items()]
    for c in vdf.get("categories") or []:
        ins.append(_row("UI", f"起始日 · {c.get('zh')}({c.get('id')})", "VDF", "", "VDF_FetchGroups 冊 categories",
                        f"現在 {c.get('start')} · 預設 {c.get('default_start')} · 族群 {', '.join(c.get('groups') or [])}", "GREEN"))
    for r in vdf.get("io") or []:
        ins.append(_row(r.get("group"), f"{r.get('zh')} · 輸入 {r.get('input')}", "VDF", "", r.get("engines"),
                        f"{r.get('membership')} · 起始 {r.get('start')} · {r.get('asof_args')}"))
    secs["IN"] = ins
    secs["PRM"] = [_row(r.get("code"), r.get("name_zh") or r.get("name"), r.get("sub"), r.get("version"), r.get("source"), r.get("cat"), r.get("lamp"))
                   for r in _jsonl(books / "VIA_NumberBook_PRMT_v0100.jsonl")]
    outs = [_row(r.get("code"), r.get("name_zh") or r.get("name"), r.get("sub"), r.get("version"), r.get("source"), r.get("cat"), r.get("lamp"))
            for r in _jsonl(books / "VIA_NumberBook_FD_v0100.jsonl")]
    dbt = _tail(reg, "VIA_DB_Table_SSOT_v*.json")
    for t in (_load(dbt, {}) or {}).get("tables") or []:
        outs.append(_row("表", f"{t.get('db')} :: {t.get('table')}", "VDF", dbt.stem.rsplit("_", 1)[-1] if dbt else "", _rel(dbt) if dbt else "",
                         f"{t.get('role') or ''} · 寫入者 {t.get('writers') or '—'} · 最少列 {t.get('min_rows') or '—'}"))
    for r in vdf.get("io") or []:
        outs.append(_row(r.get("group"), f"{r.get('zh')} → 輸出", "VDF", "", r.get("output"), f"日期鍵 {r.get('date_key')} · {r.get('cadence')}"))
    secs["OUT"] = outs
    out = []
    for s in book.get("page5_sections") or []:
        rows = secs.get(s["id"]) or []
        for i, r in enumerate(rows, 1):
            r["no"] = f"{s.get('prefix', 'P5-' + s['id'])}-{i:04d}"
        subs = {}
        for r in rows:
            subs[r["sub"]] = subs.get(r["sub"], 0) + 1
        out.append({"id": s["id"], "zh": s.get("zh"), "prefix": s.get("prefix"), "n": len(rows), "subs": subs, "rows": rows})
    return {"sections": out, "numbering_book": "supportive modules/registry/VIA_Numbering_SSOT_v0100.json",
            "rule": "每段自動編號(前綴-四碼,依冊序);「編號」欄 = 中央編號冊已發的號(沒有就 —),不另發新號"}


# ---------- 閘門 · 指令 · 快照組裝 ----------
def gates(book: dict) -> list:
    out = []
    for g in book.get("gates") or []:
        p = VIA / g.get("file", "")
        out.append({**g, "exists": p.is_file(), "uri": p.resolve().as_uri() if p.is_file() else None,
                    "ts": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(timespec="minutes") if p.is_file() else None})
    return out


def oc_snapshot(snap: dict, book: dict | None = None, **paths) -> dict:
    book = book if book is not None else oc_book()
    vdf = snap.get("vdf") or {}
    inp = input_matrix(book, vdf, paths.get("reg_path"))
    eng = engine_matrix(paths.get("engine_path"))
    db = db_check(paths.get("db_path"))
    groups = result_matrix(vdf)
    ft = fetch_test(paths.get("fetch_test_path"))
    vrn = vrn_data(paths.get("vrn_db"), paths.get("basicinfo_path"), paths.get("fin_path"), paths.get("sidecar_dir"))
    members = {g["id"]: list(g.get("members") or []) for g in vdf.get("groups") or [] if g.get("id") in ("TW_FIN", "INTL_FIN", "INTL_DAILY")}
    members.update(live_members())
    return {"book": book.get("_path"), "ruling": book.get("ruling"), "input": inp, "engine": eng, "db": db, "groups": groups,
            "fetch_test": ft, "validation": validation(inp, eng, db, groups, ft, vrn), "vrn": vrn, "page5": page5(book, vdf, eng),
            "gates": gates(book), "commands": book.get("commands") or [], "editable": book.get("editable") or {},
            "members": members, "summary_policy": book.get("summary_policy"), "via_root": str(VIA)}


def snapshot_v0103(cfg: dict, home):
    snap = _SNAPSHOT_V0102(cfg, home)
    snap["oc"] = oc_snapshot(snap)
    return snap


BASE.snapshot = snapshot_v0103
PRIOR.TAG = TAG
BASE.TAG = TAG


# ---------- 匯入:起始日 / 財報成員走 v0101 import(MDL012 ui-import);國外個股資料走 MDL012 add / remove ----------
_CODE = re.compile(r"[A-Za-z0-9_.\-^=:]{1,24}")


def plan_matrix_members(mm, current: dict) -> tuple:
    """回 (ops, errs)。ops = [(op, group, [codes])];只收 editable 冊上走 add/remove 的族群(INTL_DAILY)。不寫檔。"""
    ops, errs = [], []
    if not mm:
        return ops, errs
    if not isinstance(mm, dict):
        return ops, ["matrix_members 要是物件"]
    for gid, v in mm.items():
        if gid != "INTL_DAILY":
            errs.append(f"matrix_members 不收族群 {gid}(只收 INTL_DAILY;財報成員走 vdf.members)")
            continue
        cur = set(current.get(gid) or [])
        for op in ("add", "remove"):
            vals = [str(x) for x in dict.fromkeys((v or {}).get(op) or [])]
            bad = [x for x in vals if not _CODE.fullmatch(x)]
            if bad:
                errs.append(f"{gid} {op} 值不合格:{bad}")
                continue
            vals = [x for x in vals if (x not in cur) == (op == "add")]
            if vals:
                ops.append((op, gid, vals))
    return ops, errs


def matrix_current(gid: str = "INTL_DAILY", vdf_dir: Path | None = None):
    """國外個股資料現況 = MDL012 add / remove 寫的那一份(VDF_Input_Interface_Matrix 尾版 sections.<gid>.tickers);拿不到回 None。
    批 R63 實測:原本取 VDF 快照,快照不在(新簽出 / CI / VDF 還沒跑)時現況變空集合,移除項被靜默丟掉。"""
    p = _tail(vdf_dir or VDF_DIR, "VDF_Input_Interface_Matrix_v*.json")
    d = _load(p) if p else None
    sec = ((d or {}).get("sections") or {}).get(gid) if isinstance(d, dict) else None
    return None if not isinstance(sec, dict) else [str(x) for x in sec.get("tickers") or []]


def _mdl012_module(buf=None):
    p = _tail(VDF_DIR, "VDF_MDL012_FetchGroups_v*.py")
    spec = importlib.util.spec_from_file_location("VDF_MDL012_for_ui_v0103", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    with contextlib.redirect_stdout(buf if buf is not None else io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


def _mdl012_main(argv: list) -> tuple:
    buf = io.StringIO()
    mod = _mdl012_module(buf)
    with contextlib.redirect_stdout(buf):
        rc = mod.main(argv)
    return rc or 0, buf.getvalue()


def live_members(gids=("TW_FIN", "INTL_FIN", "INTL_DAILY")) -> dict:
    """左面板成員現況 = MDL012 自己的算法(預設 + 矩陣 + 成員帳本),不靠 VDF 快照;讀不到的族群不列(頁面就不匯出它)。
    批 R63 實測:新簽出沒有快照時財報成員變空,頁面匯出空名單 = 叫 ui-import 全部移除。"""
    out = {}
    try:
        mod = _mdl012_module()
        eff = getattr(mod, "effective_members_v0103", None) or mod.effective_members
        book = mod.load_book()
        ledger = mod._ledger() if hasattr(mod, "_ledger") else mod.read_ledger(mod.LEDGER)
        sel, mat = mod.load_inputs(book)[:2]
        for gid in gids:
            e = eff(mod.group_of(book, gid), ledger, sel, mat)
            if e.get("members") is not None:
                out[gid] = [str(x) for x in e["members"]]
    except Exception:  # noqa: BLE001 — 讀不到就不列,頁面照實標「現況讀不到」
        return out
    return out


_NON_EQUITY = re.compile(r"^\^|=[XF]$")


def screen_members(data: dict, book: dict | None = None, pool: dict | None = None) -> list:
    """財報成員只收公司:族群有 pick_groups 時,候選池裡不在這些組的代號(與 ^ 指數 / =X 匯率 / =F 期貨)拒收。回拒絕訊息;不寫檔。"""
    book = book if book is not None else oc_book()
    ed = (book.get("editable") or {}).get("members") or {}
    mem = ((data.get("vdf") or {}).get("members") or {}) if isinstance(data, dict) else {}
    errs = []
    for gid, codes in mem.items():
        rule = ed.get(gid) or {}
        groups = rule.get("pick_groups")
        if not groups:
            continue
        if pool is None:
            pool = PRIOR.member_candidates()
        grp = {str(x.get("code")): x.get("group") for x in pool.get(rule.get("pick") or "INTL") or []}
        bad = [str(c) for c in codes or [] if _NON_EQUITY.search(str(c)) or (str(c) in grp and grp[str(c)] not in groups)]
        if bad:
            errs.append(f"{gid} 只收 {'/'.join(groups)}(財報只收公司),拒收:{' '.join(bad)}")
    return errs


def cmd_import_v0103(path: str, apply: bool) -> int:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    bad = screen_members(data)
    if bad:
        for e in bad:
            print(f"  [拒絕] {e}")
        print("  [拒絕] 整份不套用(不部分寫入);回頁面移掉這些代號再匯出")
        return 2
    mm = data.pop("matrix_members", None)
    BASE.WORK_DIR.mkdir(parents=True, exist_ok=True)
    tmp = BASE.WORK_DIR / "_ui_input_v0103.json"
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    rc = PRIOR.cmd_import(str(tmp), apply)
    snap_vdf = {}
    try:
        snap_vdf = PRIOR.vdf_snapshot(None) or {}
    except Exception:  # noqa: BLE001 — 拿不到現況就照空集合比(只會多列計畫,不會誤刪)
        snap_vdf = {}
    current = {g.get("id"): list(g.get("members") or []) for g in snap_vdf.get("groups") or []}
    live = matrix_current()
    if live is not None:
        current["INTL_DAILY"] = live
    elif mm:
        print("  [注意] 讀不到 VDF_Input_Interface_Matrix,國外個股資料現況改用 VDF 快照(可能過期)")
    ops, errs = plan_matrix_members(mm, current)
    for e in errs:
        print(f"  [拒絕] {e}")
    planned = {(op, x) for op, _g, vals in ops for x in vals}
    for op in ("add", "remove"):
        asked = [str(x) for x in ((mm or {}).get("INTL_DAILY") or {}).get(op) or []] if isinstance(mm, dict) else []
        skip = [x for x in dict.fromkeys(asked) if (op, x) not in planned and _CODE.fullmatch(x)]
        if skip:
            print(f"  [略過] INTL_DAILY {op} {' '.join(skip)}({'已在名單' if op == 'add' else '不在名單'})")
    for op, gid, vals in ops:
        print(f"  [國外個股資料] {gid} {'+' if op == 'add' else '−'} {' '.join(vals)}" + ("" if apply else "(計畫)"))
        if apply:
            r2, out = _mdl012_main([op, gid, *vals, "--apply"])
            print("  [MDL012] " + out.strip().replace("\n", "\n  "))
            rc = max(rc, r2)
    if errs:
        rc = max(rc, 2)
    return rc


# ---------- 內建標準範本(v0103:VIA 操作台;白底資料總冊視覺) ----------
BUILTIN_V0103 = r"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ · VIA 操作台</title>
<style>
:root{--bg:#f5f4f0;--paper:#fff;--paper2:#faf9f6;--zebra:#f6f4ef;--soft:#eceae2;--ink:#1e1d1a;--mute:#6f6b62;--line:#dbd9d3;--blue:#4c78a8;--teal:#439a9a;--up:#c96b5a;--down:#5a9e6f;--amber:#c4943a;--co:#b5291a;--r:9px;--side:308px}
*{box-sizing:border-box}html,body{margin:0}
body{background:var(--bg);color:var(--ink);font:13px/1.5 "DM Sans","Noto Sans TC","Microsoft JhengHei","PingFang TC",system-ui,sans-serif}
.mono,code,.no,.code{font-family:"DM Mono",Consolas,"Courier New",monospace}
.app{display:grid;grid-template-columns:var(--side) minmax(0,1fr);min-height:100vh}
.app.fold{grid-template-columns:46px minmax(0,1fr)}
.side{position:sticky;top:0;height:100vh;overflow:auto;background:var(--paper);border-right:1px solid var(--line);padding:12px 12px 40px}
.app.fold .side>*:not(.brand){display:none}.app.fold .brand .bt{display:none}
.app.fold .side{padding:12px 6px}.app.fold .brand{flex-direction:column}.app.fold .fold-btn{margin-left:0}
.brand{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.seal{width:30px;height:30px;border-radius:6px;background:var(--co);color:#fff;display:grid;place-items:center;font-weight:700;flex:none}
.brand .bt b{display:block;font-size:14px}.brand .bt small{color:var(--mute);font-size:11px}
.fold-btn{margin-left:auto;border:1px solid var(--line);background:var(--paper2);border-radius:6px;cursor:pointer;padding:3px 7px;font:inherit}
.side details{border:1px solid var(--line);border-radius:var(--r);margin:8px 0;background:var(--paper2)}
.side summary{cursor:pointer;padding:7px 10px;font-weight:600;list-style:none}
.side summary::-webkit-details-marker{display:none}.side summary:before{content:"▸ ";color:var(--mute)}.side details[open]>summary:before{content:"▾ "}
.side .in{padding:2px 10px 10px}
.side label{display:block;font-size:11.5px;color:var(--mute);margin:6px 0 2px}
select,button{font:inherit;color:var(--ink)}
select{width:100%;padding:5px 6px;border:1px solid var(--line);border-radius:6px;background:#fff}
.btn{display:block;width:100%;text-align:left;margin:5px 0;padding:6px 9px;border:1px solid var(--line);border-radius:7px;background:#fff;cursor:pointer}
.btn:hover{border-color:var(--blue)}.btn.pri{background:var(--blue);color:#fff;border-color:var(--blue)}
.btn small{display:block;color:var(--mute);font-size:11px;word-break:break-all}.btn.pri small{color:#e6eef7}
.chips{display:flex;flex-wrap:wrap;gap:4px;margin:4px 0}
.chip{display:inline-flex;align-items:center;gap:3px;padding:2px 3px 2px 8px;border:1px solid var(--line);border-radius:12px;background:#fff;font-size:12px}
.chip.new{border-color:var(--down);background:#eef7f0}.chip button{border:0;background:none;cursor:pointer;color:var(--up);padding:0 4px}
.gate{display:flex;align-items:center;gap:6px;margin:4px 0;font-size:12px}.gate a{color:var(--blue)}
.main{min-width:0;padding:14px 18px 60px}
.top{display:flex;flex-wrap:wrap;align-items:flex-end;gap:10px;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:8px;margin-bottom:10px}
.top h1{margin:0;font-size:19px}.top h1 small{font-size:12px;color:var(--mute);font-weight:400;margin-left:8px}
.meta{font-size:11.5px;color:var(--mute);text-align:right}
.pages{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}
.pages button{border:1px solid var(--line);background:var(--paper);border-radius:18px;padding:5px 12px;cursor:pointer}
.pages button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.pg{display:none}.pg.on{display:block}
.card{background:var(--paper);border:1px solid var(--line);border-radius:var(--r);padding:12px 14px;margin:10px 0}
.card h2{margin:0 0 8px;font-size:15px}.card h2 small{font-weight:400;color:var(--mute);font-size:12px;margin-left:6px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px}
.kpi{background:var(--paper2);border:1px solid var(--line);border-radius:8px;padding:8px 10px}.kpi b{display:block;font-size:18px}.kpi span{font-size:11.5px;color:var(--mute)}
.tw{overflow:auto;max-width:100%;border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:12px;background:#fff}
th{position:sticky;top:0;background:var(--soft);text-align:left;font-weight:600;padding:6px 8px;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:5px 8px;border-bottom:1px solid #ecebe6;vertical-align:top}
tr:nth-child(even) td{background:var(--zebra)}
td.wrap{white-space:normal;min-width:180px;overflow-wrap:anywhere}td.mono{white-space:nowrap}
.st{white-space:nowrap;font-weight:600}.st.DONE{color:var(--down)}.st.PROXY{color:var(--amber)}.st.TODO{color:var(--up)}
.lamp{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle;background:#b9b6ae}
.lp{white-space:nowrap}.lamp.GREEN{background:var(--down)}.lamp.YELLOW{background:var(--amber)}.lamp.RED{background:var(--up)}.lamp.NODATA{background:#b9b6ae}
.cat{border:1px solid var(--line);border-radius:var(--r);margin:8px 0;background:var(--paper)}
.cat>summary{cursor:pointer;padding:9px 12px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;list-style:none}
.cat>summary::-webkit-details-marker{display:none}
.cat>summary b{font-size:13.5px}.pill{border-radius:10px;padding:1px 8px;font-size:11.5px;background:var(--soft)}
.pill.ok{background:#e4f2e8;color:#2f6b40}.pill.warn{background:#f7eedb;color:#7a5a1c}.pill.bad{background:#f6e2dd;color:#8a3a2c}
.note{color:var(--mute);font-size:11.5px}
.fp{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);gap:12px}
.fp .lines{background:#fff;border:1px solid var(--line);border-radius:8px;padding:8px 10px}
.ln{display:grid;grid-template-columns:44px minmax(0,1fr);gap:6px;padding:3px 0;border-bottom:1px dashed #eeece6;white-space:normal;word-break:break-word}
.ln .no{color:var(--mute);font-size:11px;padding-top:2px}.ln.title{font-weight:700;color:var(--blue)}
.info{background:var(--paper2);border:1px solid var(--line);border-radius:8px;padding:8px 10px}.info div{padding:3px 0;border-bottom:1px dashed #e6e3dc}
.sum li{margin:6px 0}.sum .sc{color:var(--mute);font-size:11px;margin-left:6px}
.seg{display:flex;flex-wrap:wrap;gap:5px;margin:6px 0}.seg button{border:1px solid var(--line);background:#fff;border-radius:14px;padding:3px 10px;cursor:pointer;font-size:12px}
.seg button.on{background:var(--teal);border-color:var(--teal);color:#fff}
.pager{display:flex;gap:8px;align-items:center;margin:8px 0}.pager button{border:1px solid var(--line);background:#fff;border-radius:6px;padding:3px 10px;cursor:pointer}
.toast{position:fixed;right:16px;bottom:16px;background:var(--ink);color:#fff;padding:8px 12px;border-radius:8px;font-size:12px;opacity:0;transition:opacity .2s;pointer-events:none}
.toast.on{opacity:.92}
@media (max-width:900px){.app,.app.fold{grid-template-columns:1fr}.side{position:relative;height:auto;border-right:0;border-bottom:1px solid var(--line)}
 .app.fold .side>*:not(.brand){display:none}.app.fold .side{padding:10px 12px}.app.fold .brand{flex-direction:row}.app.fold .brand .bt{display:block}.app.fold .fold-btn{margin-left:auto}.fp{grid-template-columns:1fr}.main{padding:10px 12px 60px}.meta{text-align:left}}
</style></head>
<body>
<div class="app" id="app">
<aside class="side" id="side"></aside>
<main class="main"><div class="top" id="top"></div><div class="pages" id="pages"></div><div id="body"></div></main>
</div>
<div class="toast" id="toast"></div>
<script>
(function(){
var S=window.VIA||{},V=S.vdf||{},O=S.oc||{};
var $=function(q){return document.querySelector(q)};
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function lamp(l){l=l||'NODATA';return '<span class="lp"><span class="lamp '+esc(l)+'"></span>'+esc(l)+'</span>'}
function dot(l){return '<span class="lamp '+esc(l||'NODATA')+'"></span>'}
function stat(s){var m={DONE:'✓ DONE',PROXY:'📡 PROXY',TODO:'✗ TODO'};return '<span class="st '+esc(s)+'">'+esc(m[s]||s||'—')+'</span>'}
function T(rows,cols,opt){opt=opt||{};if(!rows||!rows.length)return '<div class="note">(無資料)</div>';
 var h='<div class="tw"'+(opt.max?' style="max-height:'+opt.max+'px"':'')+'><table><thead><tr>'+cols.map(function(c){return '<th>'+esc(c[1])+'</th>'}).join('')+'</tr></thead><tbody>';
 rows.forEach(function(r){h+='<tr>'+cols.map(function(c){var v=r[c[0]];var f=c[2];return '<td'+(c[3]?' class="'+c[3]+'"':'')+'>'+(f?f(v,r):esc(v==null?'—':v))+'</td>'}).join('')+'</tr>'});
 return h+'</tbody></table></div>'}
var KEY='via.ui.engine.v0103',st={};
try{st=JSON.parse(localStorage.getItem(KEY)||'{}')||{}}catch(e){st={}}
function save(){try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){}}
var CATS=V.categories||[];
st.starts=st.starts||{};CATS.forEach(function(c){if(!st.starts[c.id])st.starts[c.id]=c.start});
var MEM=O.members||{};var SIG=JSON.stringify([MEM,CATS.map(function(c){return [c.id,c.start]})]);
if(st.sig!==SIG){if(st.sig)setTimeout(function(){toast('現況已更新(套用或重建後)→ 左面板改動已重設')},300);st.mem={};st.starts={};st.sig=SIG;CATS.forEach(function(c){st.starts[c.id]=c.start})}
st.mem=st.mem||{};['TW_FIN','INTL_FIN','INTL_DAILY'].forEach(function(g){if(MEM[g]&&!st.mem[g])st.mem[g]=MEM[g].slice()});
if(st.fold===undefined)st.fold=window.innerWidth<=900;
st.page=st.page||'p1';st.p5=st.p5||'SSOT';st.p5sub=st.p5sub||'ALL';st.p5pg=st.p5pg||0;
var REPS=(O.vrn||{}).reports||[];
function repHas(id){var R=O.vrn||{};return {B:(R.basic||[]).some(function(x){return x.report_file===id}),M:!!((R.metrics||{})[id]||[]).length,F:!!((R.fin||{})[id]||[]).length,T:(R.docs||[]).some(function(x){return x.id===id})}}
function repScore(id){var h=repHas(id);return (h.B?1:0)+(h.M?1:0)+(h.F?1:0)+(h.T?1:0)}
if(!st.rep||!REPS.some(function(r){return r.id===st.rep})){var best='',bs=-1;REPS.forEach(function(r){var k=repScore(r.id);if(k>bs){bs=k;best=r.id}});st.rep=best}
function toast(t){var x=$('#toast');x.textContent=t;x.classList.add('on');setTimeout(function(){x.classList.remove('on')},1800)}
function copy(t){function fb(){var a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();try{document.execCommand('copy')}catch(e){}a.remove();toast('已複製指令')}
 if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(function(){toast('已複製指令')},fb)}else fb()}
// ---------- 左面板(功能)----------
function pickPool(g){var ed=((O.editable||{}).members||{})[g]||{};var P=S.members_pick||{};var a=P[ed.pick||'INTL']||[];
 return ed.pick_groups?a.filter(function(x){return ed.pick_groups.indexOf(x.group)>=0}):a}
function memBlock(g){var ed=((O.editable||{}).members||{})[g]||{},cur=MEM[g]||[],w=st.mem[g]||[];
 if(!MEM[g])return '<details open><summary>'+esc(ed.zh||g)+' <span class="note">現況讀不到</span></summary><div class="in"><div class="note">讀不到這個族群的現有名單(VDF 族群冊 / 成員帳本)→ 不給增減、匯出不帶它,免得送出空名單</div></div></details>';
 var pool=pickPool(g).filter(function(x){return w.indexOf(String(x.code))<0});
 return '<details open><summary>'+esc(ed.zh||g)+' <span class="note">'+w.length+' 檔</span></summary><div class="in">'
  +'<div class="chips">'+w.map(function(c){return '<span class="chip'+(cur.indexOf(c)<0?' new':'')+'">'+esc(c)+'<button title="移除" data-rm="'+esc(g)+'|'+esc(c)+'">×</button></span>'}).join('')+'</div>'
  +'<label>增加</label><select data-add="'+esc(g)+'"><option value="">+ 選一檔加入…</option>'+pool.map(function(x){return '<option value="'+esc(x.code)+'">'+esc(x.code)+' '+esc(x.name||'')+'</option>'}).join('')+'</select>'
  +'<div class="note">走 '+esc(ed.via||'')+';移除後可再加回(綠框 = 新加)</div></div></details>'}
function side(){
 var h='<div class="brand"><div class="seal">庫</div><div class="bt"><b>VIA 操作台</b><small>VCGC → VDF × VRN · 左功能 右顯示</small></div><button class="fold-btn" id="fold" title="收合 / 展開">⇔</button></div>';
 h+='<details open><summary>① 各大類起始日</summary><div class="in">'+CATS.map(function(c){var opts=(S.date_options||[]).slice();if(opts.indexOf(c.start)<0)opts.push(c.start);if(opts.indexOf(c.default_start)<0)opts.push(c.default_start);opts.sort();
   return '<label>'+esc(c.zh)+'<br><span class="note">'+esc(c.id)+' · 預設 '+esc(c.default_start)+'</span></label><select data-start="'+esc(c.id)+'">'+opts.map(function(d){return '<option'+(d===st.starts[c.id]?' selected':'')+'>'+esc(d)+'</option>'}).join('')+'</select>'}).join('')
  +'<div class="note">'+esc(V.start_rule||'起始日只能按大類改')+'</div></div></details>';
 h+=memBlock('TW_FIN')+memBlock('INTL_FIN')+memBlock('INTL_DAILY');
 var ch=diff();
 h+='<details open><summary>② 啟動 <span class="note">變更 '+ch.n+' 項</span></summary><div class="in">'
  +'<button class="btn pri" id="exp">⬇ 匯出輸入 VIA_UI_Input.json<small>'+esc(ch.text||'與現況相同')+'</small></button>'
  +(O.commands||[]).map(function(c){return '<button class="btn" data-cmd="'+esc(c.cmd)+'">'+esc(c.zh)+'<small>'+esc(c.cmd)+'</small></button>'}).join('')+'</div></details>';
 h+='<details open><summary>③ 跳到 VCGC / VDF 閘</summary><div class="in">'+(O.gates||[]).map(function(g){
   return '<div class="gate">'+dot(g.exists?'GREEN':'NODATA')+(g.exists?'<a href="'+esc(g.uri)+'" target="_blank" rel="noopener">'+esc(g.zh)+'</a>':'<span>'+esc(g.zh)+'</span>')
     +'<button class="fold-btn" data-cmd="'+esc(g.cmd)+'" title="'+esc(g.cmd)+'">指令</button></div>'}).join('')+'<div class="note">沒有檔的閘 = 還沒跑過;按「指令」複製產生它的指令</div></div></details>';
 $('#side').innerHTML=h}
function diff(){var parts=[],n=0;CATS.forEach(function(c){if(st.starts[c.id]!==c.start){n++;parts.push(c.id+' → '+st.starts[c.id])}});
 ['TW_FIN','INTL_FIN','INTL_DAILY'].forEach(function(g){var cur=MEM[g]||[],w=st.mem[g]||[];var a=w.filter(function(x){return cur.indexOf(x)<0}),r=cur.filter(function(x){return w.indexOf(x)<0});
  if(a.length){n+=a.length;parts.push(g+' +'+a.join(','))}if(r.length){n+=r.length;parts.push(g+' −'+r.join(','))}});return {n:n,text:parts.join(' · ')}}
function exportInput(){var cats={};CATS.forEach(function(c){if(st.starts[c.id]!==c.start)cats[c.id]={start:st.starts[c.id]}});
 var cur=MEM.INTL_DAILY||[],w=st.mem.INTL_DAILY||[];
 var mem={};['TW_FIN','INTL_FIN'].forEach(function(g){if(MEM[g])mem[g]=st.mem[g]});
 var data={schema:S.input_schema||'VIA_UI_Input/1',vdf:{categories:cats,members:mem},
  matrix_members:MEM.INTL_DAILY?{INTL_DAILY:{add:w.filter(function(x){return cur.indexOf(x)<0}),remove:cur.filter(function(x){return w.indexOf(x)<0})}}:{},
  from:'CGC_MDL261_UIEngine v0103',exported_at:new Date().toISOString()};
 var b=new Blob([JSON.stringify(data,null,1)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='VIA_UI_Input.json';document.body.appendChild(a);a.click();a.remove();
 toast('已下載 VIA_UI_Input.json → 按 ① 套用(先乾跑)')}
// ---------- 右面板(顯示)----------
var PAGES=[['p1','① 輸入 · 引擎 · 結果','INPUT · ENGINE · RESULT'],['p2','② BASIC INFO','VRN 報告基本資料'],['p3','③ FINANCIAL DATA','VRN 財務數據'],
 ['p4','④ 首頁全文 · INFO AREA · 摘要','一句一行 · 一標題一行'],['p5','⑤ SSOT · REGEX · 同義字 · 引擎 · 邏輯 · 輸入 · 參數 · 輸出','自動編號矩陣']];
function top(){var p=PAGES.filter(function(x){return x[0]===st.page})[0]||PAGES[0],val=(O.validation||{});
 $('#top').innerHTML='<div><div class="note">VCGC → VDF × VRN · '+esc(S.tool||'')+'</div><h1>'+esc(p[1])+'<small>'+esc(p[2])+'</small></h1></div>'
  +'<div class="meta">驗證 '+lamp(val.lamp)+'<br>建置 '+esc((S.built||'').slice(0,19))+' · AS-OF '+esc(V.as_of||'—')+'<br>冊 '+esc(O.book||'—')+'</div>';
 $('#pages').innerHTML=PAGES.map(function(x){return '<button data-pg="'+x[0]+'"'+(x[0]===st.page?' class="on"':'')+'>'+esc(x[1])+'</button>'}).join('')}
function repTag(id){var h=repHas(id);return '['+['B','M','F','T'].map(function(k){return h[k]?k:'·'}).join('')+']'}
function repSelect(){if(!REPS.length)return '<div class="note">沒有 VRN 報告(工作站跑 ⑤ VRN 報告擷取後重建)</div>';
 return '<label class="note">報告 </label><select id="rep" style="max-width:640px">'+REPS.map(function(r){return '<option value="'+esc(r.id)+'"'+(r.id===st.rep?' selected':'')+'>'+esc(repTag(r.id))+' '+esc([r.date,r.ticker,r.name,r.broker].filter(Boolean).join(' · ')||r.id)+' — '+esc(r.id)+'</option>'}).join('')+'</select> <span class="note">[B 基本資料 · M 關鍵數字 · F 財務表格 · T 首頁全文]</span>'}
function p1(){var I=O.input||{},E=O.engine||{},D=O.db||{},G=O.groups||[],VA=O.validation||{};
 var c=I.counts||{};
 var h='<div class="card"><h2>結果驗證摘要 <small>'+lamp(VA.lamp)+'</small></h2>'+T(VA.rows,[['face','面向'],['lamp','燈',lamp],['value','結果',null,'wrap'],['note','說明',null,'wrap']])+'</div>';
 h+='<div class="kpis"><div class="kpi"><b>'+esc(I.assigned)+' / '+esc(I.total)+'</b><span>輸入矩陣 · 全選</span></div><div class="kpi"><b>'+esc(c.DONE||0)+'</b><span>✓ DONE</span></div>'
  +'<div class="kpi"><b>'+esc(c.PROXY||0)+'</b><span>📡 PROXY</span></div><div class="kpi"><b>'+esc(c.TODO||0)+'</b><span>✗ TODO</span></div>'
  +'<div class="kpi"><b>'+esc(E.n||0)+'</b><span>VDF 引擎</span></div><div class="kpi"><b>'+esc(G.length)+'</b><span>擷取族群</span></div></div>';
 h+='<div class="card"><h2>輸入矩陣 · 資料總冊 Fetch Registry <small>'+esc(I.registry||'')+'</small></h2><div class="note">大類全選;起始日跟左面板 ① 的大類走;項目狀態照冊(✓ DONE · 📡 PROXY · ✗ TODO)</div>';
 (I.categories||[]).forEach(function(k){var s=k.states||{};
  h+='<details class="cat"><summary><b>'+esc(k.zh)+'</b><span class="pill ok">全選 '+esc(k.selected)+' / '+esc(k.n)+'</span><span class="pill">起始 '+esc(st.starts[k.start_category]||k.start||'—')+'('+esc(k.start_category)+')</span>'
   +'<span class="pill ok">✓ '+esc(s.DONE||0)+'</span><span class="pill warn">📡 '+esc(s.PROXY||0)+'</span><span class="pill bad">✗ '+esc(s.TODO||0)+'</span></summary>'
   +T(k.items,[['selected','選',function(v){return v?'☑':'☐'}],['id','碼',null,'mono'],['name','資料項 Item',null,'wrap'],['source','來源 Source'],['fetcher','Fetcher',null,'mono'],['freq','頻率'],['fields','主要欄位 Fields',null,'wrap'],['refs','消費模板'],['status','狀態',stat]],{max:520})+'</details>'});
 h+='</div>';
 h+='<div class="card"><h2>引擎狀態矩陣 <small>'+esc(E.file||'')+' · '+esc(E.ts||E.note||'')+'</small></h2>'+T(E.rows,[['編號','編號',null,'mono'],['家族','家族',null,'mono'],['版本','版本'],['中央編號','中央編號',null,'mono'],['啟動前閘','啟動前閘',lamp],['備料燈','備料燈',lamp],['可啟動','可啟動'],['自測','自測'],['上次成功_資料','上次成功(資料)'],['上次成功_跑測','上次成功(跑測)'],['短令','短令',null,'mono']],{max:460})+'</div>';
 h+='<div class="card"><h2>結果矩陣 · 擷取族群(as-of '+esc(V.as_of||'—')+')</h2>'+T(G,[['id','族群',null,'mono'],['zh','名稱'],['category','大類'],['membership','名單'],['n','成員'],['worst','燈',lamp],['max_date','最新日'],['rows_asof','as-of 列'],['tables','表',function(v){return (v||[]).map(function(t){return esc(t.db+' :: '+t.table)+' '+lamp(t.state)+(t.note?' <span class="note">'+esc(t.note)+'</span>':'')}).join('<br>')},'wrap']])+'</div>';
 h+='<div class="card"><h2>結果矩陣 · 資料庫檢查 <small>'+esc(D.file||'')+' · '+esc(D.ts||D.note||'')+'</small></h2>'+T(D.rows,[['庫','庫',null,'mono'],['表','表',null,'mono'],['狀態','狀態'],['燈','燈',lamp],['列數','列數'],['最少','最少'],['最新日','最新日'],['落後天','落後天'],['寫入者','寫入者',null,'wrap']],{max:420})+'</div>';
 var F=O.fetch_test||{};h+='<div class="card"><h2>VDF 離線整合實測 <small>'+esc(F.file||'')+'</small></h2><div>'+esc(F.head||F.note||'—')+'</div><div class="note mono">'+(F.lines||[]).map(esc).join('<br>')+'</div></div>';
 return h}
function curRep(){return REPS.filter(function(r){return r.id===st.rep})[0]||{}}
function p2(){var R=O.vrn||{},b=(R.basic||[]).filter(function(x){return x.report_file===st.rep})[0];
 var h='<div class="card">'+repSelect()+'</div>';
 if(b){h+='<div class="card"><h2>'+esc(b.ticker)+' '+esc(b.name_official)+' <small>'+esc(b.broker_name_zh||b.broker)+' · '+esc(b.report_date)+'</small></h2>'
  +T([b],[['rating_raw','評等'],['rating_code','評等碼'],['rating_direction','方向'],['target_price','目標價'],['price','收盤價(報告)'],['upside_report','潛在漲幅(報告)'],['upside_calc','漲幅(計算)'],['upside_state','漲幅狀態'],['target_price_adj','目標價(還原)'],['price_latest_adj','最新收盤(還原)'],['upside_adj','漲幅(還原)'],['report_kind','類型'],['ssot_state','SSOT'],['report_age_days','距今天數'],['target_freshness','目標價新鮮度']])
  +'<h2 style="margin-top:12px">分析師</h2>'+T((R.analysts||{})[st.rep],[['zh','中文'],['en','英文'],['email','Email'],['phones','電話'],['institution','機構'],['zone','區'],['confidence','信心']])+'</div>'}
 else h+='<div class="card note">這份沒有 BASIC INFO 列(只有財報表或首頁全文)</div>';
 h+='<div class="card"><h2>全部報告 BASIC INFO <small>'+esc((R.basic||[]).length)+' 列 · '+esc((R.sources||[]).join(' · '))+'</small></h2>'+T(R.basic,[['report_date','日期'],['ticker','代號',null,'mono'],['name_official','名稱'],['broker_name_zh','券商'],['rating_raw','評等'],['target_price','目標價'],['price','收盤價'],['upside_report','漲幅(報告)'],['analyst_names','分析師',null,'wrap'],['ssot_state','SSOT'],['report_file','檔',null,'wrap']],{max:520})+'</div>';
 h+='<div class="card"><h2>輸入檢核 StockReportBasicInfo <small>'+esc((R.basicinfo||[]).length)+' 列</small></h2>'+T(R.basicinfo,[['ReportDate','日期'],['Ticker','代號',null,'mono'],['CompanyName','名稱'],['Broker','券商'],['InputStatus','輸入'],['ValidationStatus','驗證'],['ValidationRisk','風險',lamp],['SourceFile','檔',null,'wrap']],{max:360})+'</div>';
 return h}
function p3(){var R=O.vrn||{},m=(R.metrics||{})[st.rep]||[],f=(R.fin||{})[st.rep]||[];
 var h='<div class="card">'+repSelect()+'</div>';
 h+='<div class="card"><h2>關鍵財務數字(報告內文) <small>'+m.length+' 列 · vrn_report_metrics</small></h2>'+T(m,[['metric','項目',null,'mono'],['period','期間'],['status','實際 / 預估'],['value','數值'],['raw','原文',null,'wrap']])+'</div>';
 var core=f.filter(function(r){return String(r.core)==='True'});
 h+='<div class="card"><h2>財務表格(逐格) <small>'+f.length+' 格 · 核心 '+core.length+' · StockReportFinancialData</small></h2>'+T(f,[['page','頁'],['table','表'],['row','列'],['col','欄'],['metric','科目',null,'wrap'],['period','期間 / 表頭',null,'wrap'],['value','值',null,'wrap'],['core','核心'],['status','驗證'],['risk','風險',lamp]],{max:560})+'</div>';
 var all=Object.keys(R.metrics||{}).length;h+='<div class="note">有關鍵數字的報告 '+all+' 份 · 有財務表格的報告 '+Object.keys(R.fin||{}).length+' 份</div>';
 return h}
function p4(){var R=O.vrn||{},docs=R.docs||[],d=docs.filter(function(x){return x.id===st.rep})[0];
 var h='<div class="card">'+repSelect()+(d?'':'<div class="note">這份報告沒有首頁全文 → 下面改選有全文的文件</div>')+'<details class="docs"'+(d?'':' open')+'><summary class="note" style="cursor:pointer">有首頁全文的文件 '+docs.length+' 份(點選切換)</summary><div class="seg">'+docs.map(function(x){return '<button data-doc="'+esc(x.id)+'"'+(d&&x.id===d.id?' class="on"':'')+'>'+esc(x.id.length>26?x.id.slice(0,26)+'…':x.id)+'</button>'}).join('')+'</div></details></div>';
 if(!d)return h;
 var n=0;
 h+='<div class="card"><h2>'+esc(d.title)+' <small>'+esc(d.source)+'</small></h2>'
  +'<div class="fp"><div><h2 style="font-size:13px">修正後首頁全文 <small>一句一行 · 一標題一行 · 自動分行 · '+d.lines.length+' 行</small></h2><div class="lines">'
  +d.lines.map(function(l){n++;return '<div class="ln'+(l.kind==='title'?' title':'')+'"><span class="no">'+(l.kind==='title'?'T':'S')+String(n).padStart(4,'0')+'</span><span>'+esc(l.text)+'</span></div>'}).join('')+'</div></div>'
  +'<div><h2 style="font-size:13px">首頁 INFO AREA <small>'+esc(d.info_source)+'</small></h2><div class="info">'+((d.info||[]).length?d.info.map(function(x){return '<div>'+esc(x)+'</div>'}).join(''):'<div class="note">(沒有資訊區文字)</div>')+'</div>'
  +'<h2 style="font-size:13px;margin-top:14px">標題</h2><div><b>'+esc(d.title)+'</b></div>'
  +'<h2 style="font-size:13px;margin-top:14px">四點摘要 <small>'+lamp(d.summary_ok?'GREEN':'YELLOW')+' '+esc(d.summary_rule)+'</small></h2><ol class="sum">'
  +(d.summary||[]).map(function(s){return '<li>'+esc(s.text).replace(/\s*➢/g,'<br>➢')+(s.score!=null?'<span class="sc">分數 '+esc(s.score)+'</span>':'')+'</li>'}).join('')+'</ol>'
  +'<div class="note">'+esc(O.summary_policy||'')+'</div></div></div></div>';
 return h}
function p5(){var P=O.page5||{},secs=P.sections||[],s=secs.filter(function(x){return x.id===st.p5})[0]||secs[0];if(!s)return '<div class="card note">沒有第五頁資料</div>';
 var rows=s.rows.filter(function(r){return st.p5sub==='ALL'||r.sub===st.p5sub}),per=200,pages=Math.max(1,Math.ceil(rows.length/per));if(st.p5pg>=pages)st.p5pg=0;
 var h='<div class="card"><h2>自動編號矩陣 <small>'+esc(P.rule||'')+'</small></h2><div class="seg">'+secs.map(function(x){return '<button data-p5="'+esc(x.id)+'"'+(x.id===s.id?' class="on"':'')+'>'+esc(x.zh)+' '+x.n+'</button>'}).join('')+'</div>'
  +'<div class="seg">'+['ALL'].concat(Object.keys(s.subs||{}).sort()).map(function(k){return '<button data-p5sub="'+esc(k)+'"'+(k===st.p5sub?' class="on"':'')+'>'+esc(k==='ALL'?'全部':k)+(k==='ALL'?'':' '+s.subs[k])+'</button>'}).join('')+'</div>'
  +'<div class="pager"><button data-p5pg="-1">◀</button><span>第 '+(st.p5pg+1)+' / '+pages+' 頁 · '+rows.length+' 列</span><button data-p5pg="1">▶</button></div>'
  +T(rows.slice(st.p5pg*per,(st.p5pg+1)*per),[['no','自動編號',null,'mono'],['code','中央編號',null,'mono'],['name','名稱',null,'wrap'],['sub','子系統'],['version','版本'],['source','來源 / 位置',null,'wrap'],['note','邏輯 / 內容 / 說明',null,'wrap'],['lamp','燈',function(v){return v?lamp(v):'—'}]],{max:640})+'</div>';
 return h}
function render(){side();top();var f={p1:p1,p2:p2,p3:p3,p4:p4,p5:p5}[st.page]||p1;$('#body').innerHTML='<div class="pg on">'+f()+'</div>';
 document.getElementById('app').classList.toggle('fold',!!st.fold);save()}
document.addEventListener('click',function(ev){var t=ev.target.closest('button,[data-pg]');if(!t)return;
 if(t.id==='fold'){st.fold=!st.fold;render();return}
 if(t.id==='exp'){exportInput();return}
 if(t.dataset.pg){st.page=t.dataset.pg;render();window.scrollTo(0,0);return}
 if(t.dataset.cmd){copy(t.dataset.cmd);return}
 if(t.dataset.rm){var a=t.dataset.rm.split('|');st.mem[a[0]]=(st.mem[a[0]]||[]).filter(function(x){return x!==a[1]});render();return}
 if(t.dataset.doc){st.rep=t.dataset.doc;render();return}
 if(t.dataset.p5){st.p5=t.dataset.p5;st.p5sub='ALL';st.p5pg=0;render();return}
 if(t.dataset.p5sub){st.p5sub=t.dataset.p5sub;st.p5pg=0;render();return}
 if(t.dataset.p5pg){st.p5pg=Math.max(0,st.p5pg+Number(t.dataset.p5pg));render();return}});
document.addEventListener('change',function(ev){var t=ev.target;
 if(t.dataset.start){st.starts[t.dataset.start]=t.value;render();return}
 if(t.dataset.add&&t.value){var g=t.dataset.add;st.mem[g]=(st.mem[g]||[]).concat([t.value]);render();return}
 if(t.id==='rep'){st.rep=t.value;render();return}});
render();
})();
</script></body></html>
"""
BASE.BUILTIN = BUILTIN_V0103
PRIOR.BUILTIN = BUILTIN_V0103


def open_page(out: Path) -> str:
    """建完自動跳出(VIA_NO_OPEN=1 不開;Windows 用 os.startfile,其他用 webbrowser)。回說明字。"""
    if os.environ.get("VIA_NO_OPEN") == "1":
        return "不開瀏覽器(VIA_NO_OPEN=1)"
    try:
        if os.name == "nt":
            os.startfile(str(out))  # noqa: S606 — 本機頁面
        else:
            import webbrowser
            webbrowser.open(out.resolve().as_uri())
        return "已跳出使用者介面"
    except Exception as exc:  # noqa: BLE001
        return f"開不了瀏覽器:{type(exc).__name__}"


# ---------- 自測 ----------
def selftest() -> int:
    import shutil
    res = []

    def chk(name, cond, note=""):
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""))

    keep_b, keep_s = BASE.BUILTIN, BASE.snapshot
    BASE.BUILTIN, BASE.snapshot = BUILTIN_V0102, _SNAPSHOT_V0102
    PRIOR.BUILTIN = BUILTIN_V0102
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            prior_rc = PRIOR.selftest()
    finally:
        BASE.BUILTIN, BASE.snapshot = keep_b, keep_s
        PRIOR.BUILTIN = keep_b
        BASE.TAG = PRIOR.TAG = TAG
    chk("① v0102 自測照過(連 v0101 · v0100 鏈;跑前版時用前版自己的範本與快照)", prior_rc == 0, buf.getvalue()[-300:])
    book = oc_book()
    cats = book.get("input_categories") or []
    where = classify(["PX-01", "PX-04C", "EF-01A", "FQ-05", "FN-01", "FN-06", "CS-01", "AI-11", "EF-12", "PX-05A", "CM-12", "CY-03", "CM-01", "US-L01", "PX-04A", "GL-04"], cats)
    chk("② 大類歸屬照冊:台股 / 指數 / 主動式 ETF · 財報 / 月營收 · 各類 ETF · 其他總經(先 ids 後 prefixes,其餘歸預設)",
        [where[k] for k in ("PX-01", "PX-04C", "EF-01A", "FQ-05")] == ["IN_TW_MARKET"] * 4
        and [where[k] for k in ("FN-01", "FN-06", "CS-01", "AI-11")] == ["IN_FIN_REV"] * 4
        and [where[k] for k in ("EF-12", "PX-05A", "CM-12", "CY-03")] == ["IN_ETF_ALL"] * 4
        and [where[k] for k in ("CM-01", "US-L01", "PX-04A", "GL-04")] == ["IN_OTHER_MACRO"] * 4, where)
    tmp = Path(tempfile.mkdtemp(prefix="mdl261v3_"))
    keep_wd = (BASE.WORK_DIR, BASE.WORK_CONFIG)
    try:
        reg = tmp / "reg.json"
        reg.write_text(json.dumps({"items": [{"id": i, "name": i, "status": s} for i, s in
                                             (("PX-01", "DONE"), ("FN-01", "DONE"), ("EF-12", "PROXY"), ("CM-01", "TODO"), ("ZZ-9", "DONE"))],
                                   "counts_measured": {"DONE": 3, "PROXY": 1, "TODO": 1}}), encoding="utf-8")
        inp = input_matrix(book, {"categories": [{"id": "TW_MARKET", "start": "2022-07-01"}]}, reg)
        chk("③ 輸入矩陣:每項只歸一類 · 全選 · 合計 = 冊上總數 · 起始日跟大類走",
            inp["total"] == 5 and inp["assigned"] == 5 and not inp["dup_ids"] and all(c["selected"] == c["n"] for c in inp["categories"])
            and next(c for c in inp["categories"] if c["id"] == "IN_TW_MARKET")["start"] == "2022-07-01", inp)
        import duckdb
        vdb = tmp / "vrn.duckdb"
        con = duckdb.connect(str(vdb))
        con.execute("create table vrn_report_basic(report_file varchar, ticker varchar, name_official varchar, broker varchar, report_date varchar, rating_raw varchar, target_price double, title_head varchar)")
        con.execute("insert into vrn_report_basic values ('R1','2330','台積電','MEGA','2026-10-01','買進',1250,'')")
        con.execute("create table vrn_report_metrics(report_file varchar, metric varchar, period varchar, status varchar, value double, raw_text varchar)")
        con.execute("insert into vrn_report_metrics values ('R1','eps','2026','ESTIMATE',48.7,'2026 年EPS 48.7')")
        text = "【本文】\n台積電第三季營收優於預期。先進製程需求強勁。目標價上調至1,250元。風險:匯率波動。\n➢ 維持買進評等。"
        pts = [{"text": "目標價上調至1,250元。", "score": 3.0, "source_span": {"start": 30}}, {"text": "台積電第三季營收優於預期。", "score": 2.0, "source_span": {"start": 6}},
               {"text": "先進製程需求強勁。", "score": 1.0, "source_span": {"start": 19}}, {"text": "➢ 維持買進評等。", "score": 0.5, "source_span": {"start": 50}},
               {"text": "風險:匯率波動。", "score": 0.1, "source_span": {"start": 40}}]
        con.execute("create table vrn_nlp_text_summary(report_file varchar, normalized_text varchar, summary_points_json varchar, summary_state varchar)")
        con.execute("insert into vrn_nlp_text_summary values (?, ?, ?, 'OK')", ["R1", text, json.dumps(pts, ensure_ascii=False)])
        con.close()
        sdir = tmp / "fp"
        sdir.mkdir()
        (sdir / "S1.json").write_text(json.dumps({"heads": [{"text": "台積電 個股報告"}], "sentences": ["台積電 個股報告台積電營收優於預期。", "毛利率58.3%。"],
                                                  "right": "評等:買進\n目標價:1,250元收盤價:1,035元潛在漲幅:20.8%"}, ensure_ascii=False), encoding="utf-8")
        fin = tmp / "fin.json"
        fin.write_text(json.dumps([{"SourceFile": "R1.pdf", "Ticker": "2330", "Page": "2", "MetricRaw": "營收", "ValueRaw": "1,000", "CoreMetric": "True"}]), encoding="utf-8")
        v = vrn_data(vdb, tmp / "none.json", fin, sdir)
        d1 = next(d for d in v["docs"] if d["id"] == "R1")
        ds = next(d for d in v["docs"] if d["id"] == "S1")
        chk("④ BASIC INFO · FINANCIAL DATA 讀得到(唯讀);報告清單 = basic ∪ 財報表 ∪ 首頁全文",
            v["state"] == "OK" and v["basic"][0]["ticker"] == "2330" and v["metrics"]["R1"][0]["value"] == 48.7 and v["fin"]["R1"][0]["metric"] == "營收"
            and {r["id"] for r in v["reports"]} == {"R1", "S1"}, v["reports"])
        chk("⑤ 首頁全文一句一行 · 一標題一行(【】與 sidecar 標題拆成獨立行)· ➢ 條列另起一行",
            [x["kind"] for x in d1["lines"]][:1] == ["title"] and d1["lines"][0]["text"] == "【本文】" and sum(1 for x in d1["lines"] if x["kind"] == "text") >= 5
            and any(x["text"].startswith("➢") for x in d1["lines"]) and ds["lines"][0] == {"kind": "title", "text": "台積電 個股報告"}, d1["lines"])
        pool = {"INTL": [{"code": "NVDA", "group": "us_jp"}, {"code": "SPY", "group": "etf"}, {"code": "^GSPC", "group": "idx"}]}
        sb = {"editable": {"members": {"INTL_FIN": {"pick": "INTL", "pick_groups": ["us_jp"]}, "INTL_DAILY": {"pick": "INTL"}}}}
        e1 = screen_members({"vdf": {"members": {"INTL_FIN": ["NVDA", "^GSPC", "SPY", "EURUSD=X", "ASML"]}}}, sb, pool)
        e2 = screen_members({"vdf": {"members": {"INTL_FIN": ["NVDA", "ASML"]}}}, sb, pool)
        chk("⑨b 國外個股財報只收公司:指數 / ETF / 匯率拒收(整份不套用);池外個股代號照收;冊上 INTL_FIN 有 pick_groups",
            len(e1) == 1 and all(x in e1[0] for x in ("^GSPC", "SPY", "EURUSD=X")) and "NVDA" not in e1[0].split("拒收:")[1] and "ASML" not in e1[0]
            and e2 == [] and (oc_book().get("editable") or {}).get("members", {}).get("INTL_FIN", {}).get("pick_groups") == ["us_jp"], e1)
        with tempfile.TemporaryDirectory() as td:
            Path(td, "VDF_Input_Interface_Matrix_v0100.json").write_text(json.dumps({"sections": {"INTL_DAILY": {"tickers": ["^GSPC", "^VIX"]}}}), encoding="utf-8")
            mc = matrix_current("INTL_DAILY", Path(td))
            ops_mc, _e = plan_matrix_members({"INTL_DAILY": {"add": ["^GDAXI"], "remove": ["^VIX"]}}, {"INTL_DAILY": mc})
        chk("⑨c 國外個股資料現況取 Input_Interface_Matrix(不靠 VDF 快照):沒快照時移除項照樣進計畫;沒檔回 None",
            mc == ["^GSPC", "^VIX"] and ("remove", "INTL_DAILY", ["^VIX"]) in ops_mc and ("add", "INTL_DAILY", ["^GDAXI"]) in ops_mc
            and matrix_current("INTL_DAILY", Path(tempfile.gettempdir()) / "_via_no_such_dir_") is None, ops_mc)
        lm = live_members()
        chk("⑨d 左面板成員現況照 MDL012 算法(預設 + 矩陣 + 帳本,不靠快照);讀不到的族群頁面不給增減、匯出不帶(不送空名單);現況變了重設本機改動",
            set(lm) == {"TW_FIN", "INTL_FIN", "INTL_DAILY"} and all(lm.values())
            and all(k in BUILTIN_V0103 for k in ("現況讀不到", "st.sig!==SIG", "if(MEM[g])mem[g]=st.mem[g]")), lm)
        neg = split_sentences("99\nMay-25\n(TWD)\n21 May 2026\n4Q25\nHelen Chen\nShare price performance", ("Helen Chen",))
        chk("⑤b 負控:圖表刻度數字 · 日期 · 單位 · 分析師姓名不判成標題;真標題照判",
            [x["kind"] for x in neg] == ["text"] * 6 + ["title"], neg)
        chk("⑥ 四點摘要 = 分數最高 4 句原句、依原文順序、逐句可在原文找到(quote-or-abstain);sidecar 取本文前 4 句",
            [s["text"] for s in d1["summary"]] == ["台積電第三季營收優於預期。", "先進製程需求強勁。", "目標價上調至1,250元。", "➢ 維持買進評等。"]
            and d1["summary_ok"] and ds["summary_ok"] and len(ds["summary"]) == 2, d1["summary"])
        chk("⑦ INFO AREA:黏在一起的標籤拆行(目標價 / 收盤價 / 潛在漲幅);沒有原文資訊區時照實標 BASIC INFO 組成",
            ds["info"] == ["評等:買進", "目標價:1,250元", "收盤價:1,035元", "潛在漲幅:20.8%"] and "BASIC INFO" in d1["info_source"], ds["info"])
        p5 = page5(book, {"categories": [], "io": []}, {"rows": []})
        nos = [r["no"] for s in p5["sections"] for r in s["rows"]]
        chk("⑧ 第五頁八段齊(SSOT · REGEX · 同義字 · 引擎 · 邏輯 · 輸入 · 參數 · 輸出);自動編號連號不重複;中央編號照冊不另發",
            [s["id"] for s in p5["sections"]] == ["SSOT", "RGX", "SYN", "ENG", "LGC", "IN", "PRM", "OUT"] and len(nos) == len(set(nos))
            and all(s["rows"][-1]["no"].endswith(f"{s['n']:04d}") for s in p5["sections"] if s["rows"]), [(s["id"], s["n"]) for s in p5["sections"]])
        ops, errs = plan_matrix_members({"INTL_DAILY": {"add": ["AAPL", "^GSPC"], "remove": ["^RUT", "NOPE"]}, "TW_FIN": {"add": ["2330"]}},
                                        {"INTL_DAILY": ["^GSPC", "^RUT"]})
        chk("⑨ 國外個股資料增減:只收 INTL_DAILY;已在的不重加、不在的不刪;財報族群不走這條",
            ops == [("add", "INTL_DAILY", ["AAPL"]), ("remove", "INTL_DAILY", ["^RUT"])] and len(errs) == 1 and "TW_FIN" in errs[0], (ops, errs))
        BASE.WORK_DIR = tmp / "work"
        BASE.WORK_CONFIG = BASE.WORK_DIR / "ui_config.json"
        home = tmp / "home"
        (home / "output_hub" / "mega").mkdir(parents=True)
        cfg = BASE.load_config(sets=[f"locations.db_root={home}"])
        with contextlib.redirect_stdout(io.StringIO()):
            snap, out, rep = BASE.build(cfg, home, tmp / "ui" / "page.html")
        page = out.read_text(encoding="utf-8")
        script = page[page.index("<script>\n(function"):]
        chk("⑩ 頁面:左功能(起始日 · 國內 / 國外財報 · 國外個股資料 · 啟動 · 跳 VCGC / VDF 閘;可收合)· 右顯示五頁依序",
            all(k in page for k in ('class="side"', "① 各大類起始日", "② 啟動", "③ 跳到 VCGC / VDF 閘", "id=\"fold\"", "data-start", "data-add", "data-rm"))
            and re.search(r"\['p1',.*\['p2','② BASIC INFO'.*\['p3','③ FINANCIAL DATA'.*\['p4',.*\['p5',", script, re.S) is not None
            and "oc" in snap and snap["oc"]["input"]["total"] > 0)
        chk("⑪ 左面板唯一會變更的輸入:起始日下拉 · 成員增減;沒有文字輸入框 / 文字區;匯出 VIA_UI_Input/1(categories · members · matrix_members)",
            not re.search(r"<input[^>]*type=\"?(text|search|number|date)", page) and "<textarea" not in page.split("<script>")[0]
            and "vdf:{categories:cats,members:mem}" in script and "['TW_FIN','INTL_FIN'].forEach(function(g){if(MEM[g])mem[g]=st.mem[g]})" in script
            and "matrix_members:MEM.INTL_DAILY?{INTL_DAILY:" in script)
        chk("⑫ 白底資料總冊視覺(#f5f4f0 · #1e1d1a · ✓ DONE / 📡 PROXY / ✗ TODO);零 CDN · 零 fetch · file:// 可開",
            all(t in page for t in ("--bg:#f5f4f0", "--ink:#1e1d1a", "✓ DONE", "📡 PROXY", "✗ TODO")) and not re.search(r'(src|href)="https?://', page)
            and "fetch(" not in script and "XMLHttpRequest" not in page)
        chk("⑬ 自動跳出:VIA_NO_OPEN=1 不開(CI / 容器)", (lambda: (os.environ.__setitem__("VIA_NO_OPEN", "1"), open_page(out))[1])() == "不開瀏覽器(VIA_NO_OPEN=1)")
        text = Path(__file__).read_text(encoding="utf-8")
        chk("⑭ 檔頭:加速器橋 · 網路橋在(__future__ 之後);不碰 TA-Lib;本檔不以目前解譯器直派子行程",
            "[VIA:ACCEL-BRIDGE:" in text and "[VIA:NET-BRIDGE:" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE:")
            and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
            and not any(isinstance(n, (__import__("ast").Import, __import__("ast").ImportFrom)) and any(a.name.split(".")[0] == "sub" + "process" for a in n.names)
                        for n in __import__("ast").walk(__import__("ast").parse(text))))
    finally:
        BASE.WORK_DIR, BASE.WORK_CONFIG = keep_wd
        shutil.rmtree(tmp, ignore_errors=True)
    ok = sum(res)
    print(f"[計] {TAG} 本版 {ok}/{len(res)} · v0102 鏈 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if ok == len(res) else 'FAIL'}")
    return 0 if ok == len(res) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    if argv and argv[0] == "import":
        if len(argv) < 2:
            print("用法:import <VIA_UI_Input.json> [--apply]")
            return 2
        return cmd_import_v0103(argv[1], "--apply" in argv)
    want_open = "--open" in argv
    argv = [a for a in argv if a != "--open"]
    rc = PRIOR.main(argv)
    if want_open and rc == 0 and argv[:1] == ["build"]:
        out = None
        if "--out" in argv and argv.index("--out") + 1 < len(argv):
            out = Path(argv[argv.index("--out") + 1])
        else:
            cfg = BASE.load_config()
            home = BASE.default_home()
            out = BASE._abs(cfg.get("output", "VIA_Reports/ui_engine/VIA_UI_Engine_latest.html"), home)
        print(f"[ui-engine] {open_page(out)} · {out}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
