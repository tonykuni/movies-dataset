#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0178 — 薄尾(操作員 2026-10-11 BASIC INFO / FINANCIAL DATA 輸出規格與驗收:
   FILENAME · TICKER · YFINANCE · BLOOMBERG · NAME(經資料庫)· BROKER · REPORT DATE · COMPANY NAME · 第一頁資訊區 REPORT DATE / RATING / TARGET PRICE / ANALYST / TITLE / EMAIL ·
   最大字標題的代號(前四碼相同)· 四碼查 TWSE / TPEx 中英文簡稱 · 檔名去掉四碼 / 簡稱 / 日期 / 券商 = 分析師 · EMAIL @ 左英文名 @ 右券商 · 評等照原文 ·
   報告尾部券商評等名稱表 · BASIC / DILUTED EPS 區分(兩列取小 = DILUTED;只一列拿歷史跟資料庫核對)· 目標價(原)/(ADJ)· 報告前一日 ADJ CLOSE · 上漲空間 ·
   FINANCIAL DATA 同義字(持續增加 · 更謹慎)· 重要科目歷史 + 預估 都做加減法測試 + 除法測試 · 全部通過才證明 VRN 成功)。
  basicinfo2 · findata 兩個動詞(auto 自動接在後面);名冊 / 評等冊 / 同義字候選 = VRN 自己的冊(只增 · 內容變才出新版)
其餘動詞照前版鏈。
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

import csv
import datetime
import hashlib
import html
import importlib.util
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0178"


def _vnum_v0178(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0178(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0178(p) < _vnum_v0178(__file__)), key=_vnum_v0178)
PRIOR = _load_v0178(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


_rep, _home = _resolve("_rep"), _resolve("_home")
MKT = {"上市": "TWSE", "上櫃": "TPEx", "興櫃": "ESB", "TWSE": "TWSE", "TSE": "TWSE", "SII": "TWSE", "TPEX": "TPEx", "OTC": "TPEx", "ROTC": "ESB", "ESB": "ESB", "EMERGING": "ESB"}
SUF = {"TWSE": ".TW", "TPEx": ".TWO", "ESB": ".TWO"}


def _jl(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _book_write(d: Path, stem: str, body: dict, rule: str) -> str:
    d.mkdir(parents=True, exist_ok=True)
    hits = sorted(d.glob(stem + "_v*.json"), key=_vnum_v0178)
    if hits and (_jl(hits[-1]) or {}).get("body") == body:
        return hits[-1].name + "(無變更)"
    nv = "v%04d" % ((_vnum_v0178(hits[-1]) + 1) if hits else 100)
    (d / ("%s_%s.json" % (stem, nv))).write_text(json.dumps({"version": nv, "prior": hits[-1].name if hits else None, "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                                                              "rule": rule, "body": body}, ensure_ascii=False, indent=1), encoding="utf-8")
    return "%s_%s.json" % (stem, nv)


# ───────── 台股名冊(VRN 唯讀 · 依欄值認欄 · 價格表後綴反推市場別)─────────
def _vdb() -> Path:
    vr = _resolve("via_roots")
    try:
        return Path(vr()["vdf_database"]) if vr else Path("")
    except Exception:  # noqa: BLE001
        return Path("")


def tw_roster(vdb: Path = None) -> dict:
    vdb = vdb or _vdb()
    files = sorted(p for p in vdb.glob("*.parquet") if re.search(r"listing|tpex|twse|otc|price|roster", p.name, re.I)) if vdb and vdb.is_dir() else []
    cache = _rep() / "_cache" / "TW_ROSTER_v178.json"
    sig = hashlib.sha1("|".join("%s:%d:%d" % (p.name, p.stat().st_size, int(p.stat().st_mtime)) for p in files).encode()).hexdigest()[:16]
    c = _jl(cache) or {}
    if c.get("sig") == sig and c.get("codes"):
        return c
    out, src = {}, []
    try:
        import duckdb  # noqa: WPS433
        con = duckdb.connect()
    except Exception as exc:  # noqa: BLE001
        return {"codes": {}, "src": [], "why": "duckdb 不在 %s" % type(exc).__name__}
    for p in files:
        try:
            cols = [r[0] for r in con.execute("describe select * from read_parquet('%s')" % str(p).replace("'", "''")).fetchall()]
            sample = con.execute("select * from read_parquet('%s') using sample 4000 rows" % str(p).replace("'", "''")).fetchall()
        except Exception:  # noqa: BLE001
            continue
        if not sample:
            continue
        stat = {}
        for i, cn in enumerate(cols):
            vals = [str(r[i]).strip() for r in sample if r[i] is not None and str(r[i]).strip()]
            if not vals:
                continue
            n = len(vals)
            stat[cn] = {"code": sum(1 for v in vals if re.fullmatch(r"\d{4,6}[A-Z]?", v)) / n, "suffix": sum(1 for v in vals if re.fullmatch(r"\d{4,6}[A-Z]?\.(TW|TWO)", v, re.I)) / n,
                        "mkt": sum(1 for v in vals if v.upper() in MKT) / n, "cjk": sum(1 for v in vals if re.search(r"[\u4e00-\u9fff]", v)) / n, "avg": sum(len(v) for v in vals) / n,
                        "uniq": len(set(vals)) / n, "ascii": sum(1 for v in vals if re.fullmatch(r"[A-Za-z][A-Za-z0-9 .&\-'()]+", v)) / n}
        code = max((c2 for c2 in stat if stat[c2]["code"] >= 0.8), key=lambda c2: stat[c2]["uniq"], default=None)
        suf = max((c2 for c2 in stat if stat[c2]["suffix"] >= 0.5), key=lambda c2: stat[c2]["suffix"], default=None)
        mkt = max((c2 for c2 in stat if stat[c2]["mkt"] >= 0.6), key=lambda c2: stat[c2]["mkt"], default=None)
        cnn = max((c2 for c2 in stat if c2 not in (code, mkt) and stat[c2]["cjk"] >= 0.6 and stat[c2]["avg"] <= 12 and stat[c2]["uniq"] >= 0.3), key=lambda c2: stat[c2]["uniq"], default=None)
        enn = max((c2 for c2 in stat if c2 not in (code, mkt, cnn, suf) and stat[c2]["ascii"] >= 0.7 and stat[c2]["avg"] >= 3 and stat[c2]["code"] < 0.2), key=lambda c2: stat[c2]["uniq"], default=None)
        if suf:
            for (v,) in con.execute('select distinct "%s" from read_parquet(\'%s\')' % (suf, str(p).replace("'", "''"))).fetchall():
                m = re.fullmatch(r"(\d{4,6}[A-Z]?)\.(TW|TWO)", str(v or "").strip(), re.I)
                if m:
                    e = out.setdefault(m.group(1), {})
                    e.setdefault("market", "TPEx" if m.group(2).upper() == "TWO" else "TWSE")
                    e["suffix"] = "." + m.group(2).upper()
            src.append("%s(後綴欄 %s)" % (p.name, suf))
        if code and (cnn or enn or mkt):
            sel = ", ".join('"%s"' % x for x in (code, cnn, enn, mkt) if x)
            for row in con.execute("select distinct %s from read_parquet('%s')" % (sel, str(p).replace("'", "''"))).fetchall():
                rr = dict(zip([x for x in (code, cnn, enn, mkt) if x], row))
                k = str(rr[code]).strip()
                if not re.fullmatch(r"\d{4,6}[A-Z]?", k):
                    continue
                e = out.setdefault(k, {})
                if cnn and rr.get(cnn):
                    e.setdefault("cn", str(rr[cnn]).strip())
                if enn and rr.get(enn):
                    e.setdefault("en", str(rr[enn]).strip())
                if mkt and rr.get(mkt) and str(rr[mkt]).strip().upper() in MKT:
                    e["market"] = MKT[str(rr[mkt]).strip().upper()]
                    e.setdefault("suffix", SUF[e["market"]])
            src.append("%s(代號 %s · 中 %s · 英 %s · 市場 %s)" % (p.name, code, cnn or "—", enn or "—", mkt or "—"))
    res = {"sig": sig, "codes": out, "src": src, "n": len(out), "with_market": sum(1 for v in out.values() if v.get("market")), "with_en": sum(1 for v in out.values() if v.get("en"))}
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return res


# ───────── 報告尾部:券商完整評等名稱表 ─────────
def rating_terms() -> list:
    md = _resolve("_MASTER") or {}
    terms = []
    for name, e in (md.get("RATING_LIST") or {}).items():
        for a in e.get("aliases", []):
            if len(a) >= 3 or re.search(r"[\u4e00-\u9fff]", a):
                terms.append((a, name, e.get("code")))
    return sorted(set(terms), key=lambda t: -len(t[0]))


def tail_rating_book(rows: list, pages: int = 3) -> dict:
    """每家券商:報告最後幾頁(小字)出現的評等名稱 → VRN_BrokerRating_Book(只增 · 內容變才出新版)。"""
    import pdfplumber  # noqa: WPS433
    terms = rating_terms()
    per = defaultdict(Counter)
    nrep = Counter()
    for r in rows:
        p = r.get("path")
        if not p or not Path(p).exists() or not str(p).lower().endswith(".pdf"):
            continue
        try:
            with pdfplumber.open(p) as pdf:
                txt = " ".join((pg.extract_text() or "") for pg in pdf.pages[-pages:])
        except Exception:  # noqa: BLE001
            continue
        b = r.get("broker") or "?"
        nrep[b] += 1
        for a, name, code in terms:
            if re.search(r"(?<![A-Za-z])" + re.escape(a) + r"(?![A-Za-z])", txt, re.I):
                per[b][a] += 1
    body = {b: {"terms": sorted(c), "reports": nrep[b]} for b, c in per.items()}
    f = _book_write((_home or (lambda: HERE))() / "knowledge", "VRN_BrokerRating_Book", body, "報告尾部小字評等名稱表 → 每家券商評等原文(只增 · 內容變才出新版)")
    return {"body": body, "file": f}



# ───────── BASIC INFO v2(欄序照操作員規格;規格外的稽核欄放最後)─────────
COLS2 = ["FILENAME", "TICKER", "YF_TICKER", "BBG_TICKER", "NAME_DB", "BROKER", "REPORT_DATE", "COMPANY_NAME", "P1_REPORT_DATE", "RATING", "TARGET_PRICE", "ANALYST", "TITLE", "EMAIL",
         "TP_ADJ", "ADJ_CLOSE_BEFORE", "UPSIDE_PCT", "NAME_EN_DB", "MARKET", "EMAIL_NAME", "EMAIL_BROKER", "ANALYST_FROM_FILENAME", "CODES_IN_TITLE", "RATING_IN_BROKER_TABLE"]
ZH2 = {"FILENAME": "檔名", "TICKER": "代號", "YF_TICKER": "yfinance", "BBG_TICKER": "Bloomberg", "NAME_DB": "名稱(資料庫)", "BROKER": "券商", "REPORT_DATE": "報告日", "COMPANY_NAME": "公司名(報告)",
       "P1_REPORT_DATE": "首頁報告日", "RATING": "評等(原文)", "TARGET_PRICE": "目標價(原)", "ANALYST": "分析師", "TITLE": "職稱", "EMAIL": "EMAIL", "TP_ADJ": "目標價(ADJ)",
       "ADJ_CLOSE_BEFORE": "報告前一日 ADJ CLOSE", "UPSIDE_PCT": "上漲空間%", "NAME_EN_DB": "英文簡稱(資料庫)", "MARKET": "市場別", "EMAIL_NAME": "EMAIL 還原英文名", "EMAIL_BROKER": "EMAIL 網域券商",
       "ANALYST_FROM_FILENAME": "檔名推分析師", "CODES_IN_TITLE": "標題代號", "RATING_IN_BROKER_TABLE": "評等在券商評等表"}
_CODE_RX = [r"(\d{4,6})\s*(?:TT|TW)\b", r"(\d{4,6})\.(?:TW|TWO)\b", r"[（(](\d{4,6})(?:\s*(?:TT|TW|\.TW|\.TWO))?[)）]", r"(?<!\d)(\d{4,6})\s*[\u4e00-\u9fff]{2,}", r"[\u4e00-\u9fff]{2,}\s*(\d{4,6})(?!\d)"]
_DROP = r"(個股報告|個股介紹報告|訪談速報|研究部|證期|投顧|證券|Takeaway|Note|Memo|初次評等|晨會|TT|KY|買進|中立|持有|增加持股|未評等)"


def codes_in_title(pg: dict) -> list:
    tb = [b for b in pg.get("blocks", []) if b.get("kind") == "text" and b.get("text")]
    mx = max((float(b.get("size") or 0) for b in tb), default=0)
    bl = sorted((b for b in tb if mx and float(b.get("size") or 0) >= 0.8 * mx), key=lambda b: -float(b.get("size") or 0))[:3]     # 只看最大字(≥ 最大字級 80%)
    txt = " ".join(b.get("text", "") for b in bl)
    found = []
    for rx in _CODE_RX:
        for m in re.finditer(rx, txt):
            c = m.group(1)
            if c not in found and not (len(c) == 4 and c.startswith(("19", "20")) and re.search(r"%s\s*(?:年|[FEA]\b)" % c, txt)):
                found.append(c)
    return found


def email_name(email: str) -> str:
    loc = (email or "").split("@")[0]
    parts = [p for p in re.split(r"[._\-]+", loc) if p]
    return " ".join(p.capitalize() for p in parts) if len(parts) >= 2 else loc


def _broker_aliases(book) -> list:
    out = set()

    def walk(x):
        if isinstance(x, str):
            if len(x) >= 2:
                out.add(x)
        elif isinstance(x, dict):
            for k, v in x.items():
                walk(k)
                walk(v)
        elif isinstance(x, (list, tuple, set)):
            for v in x:
                walk(v)
    walk(book)
    return sorted(out, key=len, reverse=True)


def analyst_from_filename(fn: str, code: str, names: list, aliases: list) -> str:
    s = Path(fn).stem
    for a in aliases:
        if len(a) >= 2 and not re.fullmatch(r"[A-Za-z]{1,2}", a):
            s = re.sub(re.escape(a), " ", s, flags=re.I)
    for n in [x for x in names if x]:
        s = s.replace(n, " ")
    s = re.sub(r"\d+(?:\.\d+)?", " ", s)
    s = re.sub(_DROP, " ", s, flags=re.I)
    toks = [t for t in re.split(r"[_\-\s()（）,，【】\[\]\.+&]+", s) if t]
    c = [t for t in toks if re.fullmatch(r"[\u4e00-\u9fff]{2,4}", t)]
    return "; ".join(dict.fromkeys(c))


def _safe_dom(dom, domain: str, book) -> str:
    try:
        return dom(domain, book) or ""
    except Exception:  # noqa: BLE001    字典格式不符 → 降級(不崩)
        return ""


def basicinfo2_run(ro: dict = None, book=None) -> dict:
    d = _resolve("_latest_l2_dir")("")
    if not d:
        return {"err": "找不到上一輪 layout 的逐檔結果"}
    rep = _rep()
    b1 = {r["fields"]["FILENAME"]["value"]: r for r in (_jl(rep / "basicinfo" / "BASIC_INFO_latest.json") or {}).get("records", [])}
    ro = ro if ro is not None else tw_roster()
    codes = ro.get("codes") or {}
    book = book if book is not None else (_resolve("load_brokers_v154") or (lambda: ({}, [])))()[0]
    aliases = _broker_aliases(book)
    dom = _resolve("domain_broker") or (lambda a, b: "")
    rb = sorted(((_home or (lambda: HERE))() / "knowledge").glob("VRN_BrokerRating_Book_v*.json"), key=_vnum_v0178)
    rbook = ((_jl(rb[-1]) or {}).get("body") or {}) if rb else {}
    F = lambda v, st, src, ck="": {"value": v, "status": st, "source": src, "check": ck}  # noqa: E731
    recs = []
    for p in sorted(d.glob("*.json")):
        j = _jl(p) or {}
        row, info = j.get("row") or {}, j.get("info") or {}
        fn = row.get("file")
        if not fn:
            continue
        r1 = (b1.get(fn) or {}).get("fields") or {}
        g = lambda k: r1.get(k) or F(None, "GRAY", "—", "BASIC v1 沒有")  # noqa: E731
        code = row.get("code") or ""
        e = codes.get(code) or {}
        pg1 = (j.get("pages") or [{}])[0]
        cit = codes_in_title(pg1)
        p1txt = " ".join(b.get("text", "") for b in pg1.get("blocks", []) if b.get("kind") == "text")
        out = {}
        out["FILENAME"] = F(fn, "GREEN", "檔名")
        out["CODES_IN_TITLE"] = F(", ".join(cit), "GREEN" if code and any(c[:4] == code[:4] for c in cit) else ("YELLOW" if not cit else "RED"), "首頁最大字",
                                  "前四碼 = 檔名代號" if code and any(c[:4] == code[:4] for c in cit) else ("標題沒代號" if not cit else "標題代號 ≠ 檔名 %s" % code))
        t1 = g("TICKER")
        out["TICKER"] = F(code, "GREEN" if (e and out["CODES_IN_TITLE"]["status"] == "GREEN") else t1["status"], "檔名 + 資料庫 + 標題", ("資料庫有 · " if e else "資料庫沒有 · ") + out["CODES_IN_TITLE"]["check"])
        mk = e.get("market")
        out["MARKET"] = F(mk or "", "GREEN" if mk else "YELLOW", "資料庫(TWSE / TPEx)" if mk else "—", "" if mk else "資料庫沒認出市場別")
        yf = code + (e.get("suffix") or SUF.get(mk or "", "")) if code else ""
        out["YF_TICKER"] = F(yf or g("YF_TICKER")["value"], "GREEN" if (code and e.get("suffix")) else "YELLOW", "資料庫市場別" if e.get("suffix") else "v1(預設 .TW)", "上市 .TW / 上櫃 .TWO")
        out["BBG_TICKER"] = F(code + " TT" if code else "", out["TICKER"]["status"], "代號")
        out["NAME_DB"] = F(e.get("cn") or g("NAME")["value"], "GREEN" if e.get("cn") else "YELLOW", "資料庫中文簡稱" if e.get("cn") else "v1")
        out["NAME_EN_DB"] = F(e.get("en") or "", "GREEN" if e.get("en") else "GRAY", "資料庫英文簡稱" if e.get("en") else "—")
        out["BROKER"] = g("BROKER")
        out["REPORT_DATE"] = g("REPORT_DATE")
        cn = e.get("cn") or row.get("name") or ""
        out["COMPANY_NAME"] = F(cn if cn and cn in p1txt else (row.get("name") or ""), "GREEN" if cn and cn in p1txt else "YELLOW", "首頁內文", "資料庫簡稱出現在首頁" if cn and cn in p1txt else "首頁沒看到資料庫簡稱")
        out["P1_REPORT_DATE"] = F(info.get("date_p1") or "", "GREEN" if info.get("date_p1") else "YELLOW", "首頁資訊區")
        raw = info.get("rating_raw") or info.get("rating") or ""
        rc = (_resolve("_rating_code") or (lambda a, b: (None, "")))(raw, "")
        terms = (rbook.get(row.get("broker") or "") or {}).get("terms") or []
        inb = bool(raw) and any(raw.lower() == t.lower() for t in terms)
        out["RATING"] = F(raw, "GREEN" if raw and rc[0] is not None else ("YELLOW" if raw else g("RATING")["status"]), "首頁資訊區(原文)", ("評等清單 %s(碼 %s)" % (rc[1], rc[0])) if rc[0] is not None else "評等清單沒有")
        out["RATING_IN_BROKER_TABLE"] = F("是" if inb else ("否" if terms else "—"), "GREEN" if inb else ("YELLOW" if terms else "GRAY"), "報告尾部評等表", "該券商評等名稱 %d 個" % len(terms) if terms else "還沒有該券商評等表")
        out["TARGET_PRICE"] = g("TP_ORIGINAL")
        ans = [a for a in info.get("analysts", []) if isinstance(a, dict)]
        names = [a.get("name") for a in ans if a.get("name")]
        ems = [a.get("email") for a in ans if a.get("email")]
        en = [email_name(x) for x in ems]
        out["EMAIL_NAME"] = F("; ".join(en), "GREEN" if en else "GRAY", "EMAIL @ 左")
        eb = sorted({(_safe_dom(dom, x.split("@")[1], book) or "?") for x in ems if "@" in x})
        out["EMAIL_BROKER"] = F("; ".join(eb), "GREEN" if eb and (row.get("broker") in eb) else ("RED" if eb and "?" not in eb else ("YELLOW" if eb else "GRAY")), "EMAIL @ 右",
                                "= 券商" if eb and row.get("broker") in eb else ("≠ 券商 %s" % row.get("broker") if eb else ""))
        af = analyst_from_filename(fn, code, [cn, row.get("name") or "", e.get("en") or ""], aliases)
        out["ANALYST_FROM_FILENAME"] = F(af, "GREEN" if af and any(af in (n or "") or (n or "") in af for n in names) else ("YELLOW" if af else "GRAY"), "檔名去代號 / 簡稱 / 日期 / 券商")
        hit = bool(names) and (out["ANALYST_FROM_FILENAME"]["status"] == "GREEN" or any(x.lower().replace(" ", "") in (" ".join(names)).lower().replace(" ", "") for x in en if " " in x))
        out["ANALYST"] = F("; ".join(names) or af or "; ".join(en), "GREEN" if hit or (names and ems) else ("YELLOW" if (names or af or en) else "GRAY"), "首頁資訊區" if names else ("檔名" if af else "EMAIL"),
                           "中 / 英文名至少一個" + (" · 檔名或 EMAIL 互證" if hit else ""))
        out["TITLE"] = g("TITLE")
        out["EMAIL"] = g("EMAIL")
        out["TP_ADJ"] = g("TP_ADJ")
        out["ADJ_CLOSE_BEFORE"] = g("ADJ_CLOSE_BEFORE")
        out["UPSIDE_PCT"] = g("UPSIDE_PCT")
        lamp = max((x["status"] for k, x in out.items() if k in COLS2[:17]), key=lambda s: {"RED": 3, "YELLOW": 2, "GRAY": 1, "GREEN": 0}[s])
        recs.append({"lamp": lamp, "fields": {k: out[k] for k in COLS2}})
    out_d = rep / "basicinfo"
    out_d.mkdir(parents=True, exist_ok=True)
    (out_d / "BASIC_INFO_V2_latest.json").write_text(json.dumps({"columns": COLS2, "roster": {k: ro.get(k) for k in ("n", "with_market", "with_en", "src")}, "records": recs}, ensure_ascii=False, indent=1, default=str),
                                                     encoding="utf-8")
    cp = out_d / "BASIC_INFO_V2_latest.csv"
    with cp.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLS2)
        for r in recs:
            w.writerow(["" if r["fields"][k]["value"] is None else r["fields"][k]["value"] for k in COLS2])
    try:
        import duckdb  # noqa: WPS433
        duckdb.connect().execute("copy (select * from read_csv_auto('%s', header=true, all_varchar=true)) to '%s' (format parquet)" % (str(cp).replace("'", "''"), str(cp.with_suffix(".parquet")).replace("'", "''")))
    except Exception:  # noqa: BLE001
        pass
    page, L = _resolve("_page"), (_resolve("_L") or {})
    if page:
        cell = lambda f: "<span title='%s · %s'><i style='background:%s;display:inline-block;width:8px;height:8px;border-radius:50%%;margin-right:3px'></i>%s</span>" % (  # noqa: E731
            html.escape(str(f["source"])), html.escape(str(f["check"])), L.get(f["status"], "#9ca3af"), html.escape("" if f["value"] is None else str(f["value"]))[:50])
        (out_d / "BASIC_INFO_V2_latest.html").write_text(page("BASIC INFO v2 · 欄序照操作員規格 · 每欄一燈(滑鼠停看來源 / 驗證)", "名冊 %s 碼(市場別 %s · 英文 %s)· %s" % (
            ro.get("n", 0), ro.get("with_market", 0), ro.get("with_en", 0), html.escape(" · ".join(ro.get("src") or [])[:300])), [ZH2[k] for k in COLS2],
            [(r["lamp"], [cell(r["fields"][k]) for k in COLS2]) for r in recs]), encoding="utf-8")
    st = Counter(f["status"] for r in recs for k, f in r["fields"].items() if k in COLS2[:17])
    return {"n": len(recs), "status": dict(st), "roster": {k: ro.get(k) for k in ("n", "with_market", "with_en", "src")}, "red": [(r["fields"]["FILENAME"]["value"], k) for r in recs for k, f in r["fields"].items()
                                                                                                                                    if f["status"] == "RED"], "html": str(out_d / "BASIC_INFO_V2_latest.html")}



# ───────── FINANCIAL DATA:EPS 基本 / 稀釋 · 加減法 + 除法測試(歷史 + 預估)· 同義字候選 ─────────
_GROWTH_BASE = {"rev_growth": "revenue", "revenue_growth": "revenue", "sales_growth": "revenue", "ni_growth": "net_income", "eps_growth": "eps", "op_growth": "operating_income",
                "oi_growth": "operating_income", "gp_growth": "gross_profit"}


def ptype(per: str) -> str:
    return "預估" if re.search(r"(?i)(\d)(E|F|CT|e|f)\b|\((E|F)\)|est|forecast|預估|預測", str(per)) else "歷史"


def _pkey(per: str):
    s = str(per).upper()
    m = re.search(r"(?:19|20)(\d{2})", s) or re.search(r"(?:FY|DEC-|MAR-|JUN-|SEP-)(\d{2})", s) or re.search(r"(\d{2})Q[1-4]|[1-4]Q(\d{2})", s)
    if not m:
        return None
    yy = int(next(g for g in m.groups() if g))
    q = re.search(r"([1-4])Q|Q([1-4])", s)
    return (yy, int(next(g for g in q.groups() if g)) if q else 0)


def db_eps(vdb: Path = None) -> dict:
    """資料庫歷史 EPS(唯讀 · 依欄名 + 值認欄):{代號: {年: {"basic": v, "diluted": v, "eps": v}}}。"""
    vdb = vdb or _vdb()
    out = {}
    files = sorted(p for p in vdb.glob("*.parquet") if re.search(r"income|eps|fin|fundamental|statement|profit|ratio", p.name, re.I)) if vdb and vdb.is_dir() else []
    try:
        import duckdb  # noqa: WPS433
        con = duckdb.connect()
    except Exception:  # noqa: BLE001
        return out
    for p in files:
        try:
            cols = [r[0] for r in con.execute("describe select * from read_parquet('%s')" % str(p).replace("'", "''")).fetchall()]
        except Exception:  # noqa: BLE001
            continue
        epc = [c for c in cols if re.search(r"(?i)eps|每股盈餘", c)]
        code = next((c for c in cols if re.search(r"(?i)^(code|stock_id|ticker|symbol|公司代號|證券代號|代號)$", c)), None)
        per = next((c for c in cols if re.search(r"(?i)^(year|fy|period|date|年度|期別)$", c)), None)
        if not epc or not code or not per:
            continue
        for row in con.execute("select \"%s\", \"%s\", %s from read_parquet('%s')" % (code, per, ", ".join('"%s"' % c for c in epc), str(p).replace("'", "''"))).fetchall():
            k = re.sub(r"\.TWO?$", "", str(row[0]).strip())
            y = re.search(r"(?:19|20)(\d{2})", str(row[1]))
            if not y:
                continue
            e = out.setdefault(k, {}).setdefault(int(y.group(1)), {})
            for c, v in zip(epc, row[2:]):
                try:
                    fv = float(v)                              # 資料庫常存 Decimal → 一律轉 float
                except (TypeError, ValueError):
                    continue
                e["diluted" if re.search(r"(?i)dilut|稀釋", c) else ("basic" if re.search(r"(?i)basic|基本", c) else "eps")] = fv
    return out


def eps_classify(rows: list, code: str = "", dbe: dict = None) -> list:
    idx = [i for i, r in enumerate(rows) if (r.get("std") == "eps" or re.search(r"(?i)\beps\b|每股盈餘", str(r.get("label_raw") or ""))) and not re.search(r"(?i)growth|成長|yoy|%", str(r.get("label_raw") or ""))]
    res = {}
    plain = []
    for i in idx:
        lab = str(rows[i].get("label_raw") or "")
        if re.search(r"(?i)dilut|稀釋", lab):
            res[i] = ("DILUTED_EPS", "名稱寫明稀釋")
        elif re.search(r"(?i)basic|基本", lab):
            res[i] = ("BASIC_EPS", "名稱寫明基本")
        else:
            plain.append(i)
    vals = lambda i: {c["period"]: c["value"] for c in rows[i].get("cells") or [] if isinstance(c.get("value"), (int, float))}  # noqa: E731
    if len(plain) >= 2:
        a, b = plain[0], plain[1]
        va, vb = vals(a), vals(b)
        com = [p for p in va if p in vb]
        smaller_a = sum(1 for p in com if va[p] < vb[p]) >= sum(1 for p in com if vb[p] < va[p])
        res[a if smaller_a else b] = ("DILUTED_EPS", "兩列 EPS · 數字小的 = 稀釋")
        res[b if smaller_a else a] = ("BASIC_EPS", "兩列 EPS · 數字大的 = 基本")
        for i in plain[2:]:
            res[i] = ("EPS_UNSURE", "第三列以上 EPS · 未分")
    elif len(plain) == 1:
        i = plain[0]
        db = (dbe or {}).get(code) or {}
        if not db:
            res[i] = ("EPS_UNSURE", "資料庫沒有 %s 的歷史 EPS · 未分" % (code or "?"))
        else:
            hit_d = hit_b = tot = 0
            for per, v in vals(i).items():
                k = _pkey(per)
                if ptype(per) != "歷史" or not k or k[1] or k[0] not in db:
                    continue
                tot += 1
                ref = db[k[0]]
                hit_d += 1 if ref.get("diluted") is not None and abs(ref["diluted"] - v) <= max(0.011, abs(v) * 0.01) else 0
                hit_b += 1 if ref.get("basic") is not None and abs(ref["basic"] - v) <= max(0.011, abs(v) * 0.01) else 0
            if tot and hit_d == tot:
                res[i] = ("DILUTED_EPS", "歷史 %d 期 = 資料庫稀釋 EPS → 改標稀釋" % tot)
            elif tot and hit_b == tot:
                res[i] = ("BASIC_EPS", "歷史 %d 期 = 資料庫基本 EPS" % tot)
            else:
                res[i] = ("EPS_UNSURE", "歷史對不上資料庫(稀釋 %d / 基本 %d / 共 %d)· 未分" % (hit_d, hit_b, tot))
    return [(i, res[i][0], res[i][1]) for i in sorted(res)]


def fin_tests(rows: list) -> list:
    M = defaultdict(dict)
    for r in rows:
        if r.get("std"):
            for c in r.get("cells") or []:
                if isinstance(c.get("value"), (int, float)) and c["period"] not in M[r["std"]]:
                    M[r["std"]][c["period"]] = float(c["value"])
    out = []
    tol = lambda x: max(1.0, abs(x) * 0.015)  # noqa: E731
    pers = sorted({p for v in M.values() for p in v}, key=lambda p: (_pkey(p) or (0, 0)))
    for p in pers:
        g = lambda k: M.get(k, {}).get(p)  # noqa: E731
        T = lambda rule, ok, det: out.append({"rule": rule, "kind": "加減法" if "=" in rule and "/" not in rule and "成長" not in rule else "除法", "period": p, "ptype": ptype(p),  # noqa: E731
                                              "status": "PASS" if ok else "FAIL", "detail": det})
        if None not in (g("revenue"), g("cogs"), g("gross_profit")):
            c = g("revenue") - abs(g("cogs"))
            T("毛利 = 營收 − 成本", abs(c - g("gross_profit")) <= tol(g("gross_profit")), "%s vs %s" % (g("gross_profit"), round(c, 2)))
        if None not in (g("gross_profit"), g("opex"), g("operating_income")):
            c = g("gross_profit") - abs(g("opex"))
            T("營益 = 毛利 − 營業費用", abs(c - g("operating_income")) <= tol(g("operating_income")), "%s vs %s" % (g("operating_income"), round(c, 2)))
        if None not in (g("operating_income"), g("nonop_income"), g("pretax_income")):
            c = g("operating_income") + g("nonop_income")
            T("稅前 = 營益 + 業外", abs(c - g("pretax_income")) <= tol(g("pretax_income")), "%s vs %s" % (g("pretax_income"), round(c, 2)))
        if None not in (g("pretax_income"), g("tax"), g("net_income")):
            a = g("pretax_income") - abs(g("tax"))
            ok = min(abs(a - g("net_income")), abs(a - abs(g("minority_interest") or 0) - g("net_income"))) <= max(tol(g("net_income")), abs(g("pretax_income")) * 0.05)
            T("淨利 ≈ 稅前 − 稅(− 少數)", ok, "%s vs %s" % (g("net_income"), round(a, 2)))
        if None not in (g("total_assets"), g("total_liabilities"), g("equity")):
            c = g("total_liabilities") + g("equity")
            T("資產 = 負債 + 權益", abs(c - g("total_assets")) <= tol(g("total_assets")), "%s vs %s" % (g("total_assets"), round(c, 2)))
        for mk, nk, zh in (("gross_margin", "gross_profit", "毛利率"), ("operating_margin", "operating_income", "營益率"), ("net_margin", "net_income", "淨利率")):
            if g("revenue") and g(mk) is not None and g(nk) is not None:
                c = g(nk) / g("revenue") * 100
                v = g(mk) * 100 if abs(g(mk)) <= 1.5 and abs(c) > 1.5 else g(mk)
                T("%s = %s / 營收" % (zh, zh[:-1]), abs(c - v) <= 0.6, "%s vs %.2f" % (g(mk), c))
    for gk, base in _GROWTH_BASE.items():
        if gk not in M or base not in M:
            continue
        bp = sorted((p for p in M[base] if _pkey(p)), key=lambda p: _pkey(p))
        for a, b in zip(bp, bp[1:]):
            ka, kb = _pkey(a), _pkey(b)
            if ka[1] or kb[1] or kb[0] != ka[0] + 1 or b not in M[gk] or not M[base][a]:     # 只驗年度前後期(季度 QoQ / YoY 看不出 → 不硬驗)
                continue
            c = (M[base][b] / M[base][a] - 1) * 100
            v = M[gk][b] * 100 if abs(M[gk][b]) <= 1.5 and abs(c) > 1.5 else M[gk][b]
            out.append({"rule": "%s 成長 = 本期 / 前期 − 1" % base, "kind": "除法", "period": b, "ptype": ptype(b), "status": "PASS" if abs(c - v) <= 1.0 else "FAIL", "detail": "%s vs %.2f" % (M[gk][b], c)})
    return out



def syn_candidates(tables: list) -> dict:
    cnt, reps, smp = Counter(), defaultdict(set), {}
    for fn, t in tables:
        for lab in t.get("unmatched_labels") or []:
            l2 = str(lab).strip()
            if not l2 or re.fullmatch(r"[\d,.%()\-\s]+", l2) or len(l2) > 40:
                continue
            cnt[l2] += 1
            reps[l2].add(fn)
            smp.setdefault(l2, "%s · %s" % (fn[:30], t.get("id")))
    body = {"candidates": {k: {"n": cnt[k], "reports": len(reps[k]), "sample": smp[k]} for k, _ in cnt.most_common(200)},
            "lexicon_issues": [{"alias": "EPS growth", "std_now": "ni_growth", "why": "EPS 成長率 ≠ 淨利成長率(股本變動時不同)→ 建議另立 eps_growth(待操作員確認 · 不自動改)"}]}
    f = _book_write((_home or (lambda: HERE))() / "knowledge", "VRN_FinSynonym_Candidates", body, "沒對到標準鍵的科目名 · 只列不自動加(更謹慎)· 操作員確認後才進 FinLexicon")
    return {"file": f, "n": len(body["candidates"])}


def findata_run() -> dict:
    rep = _rep()
    dbe = db_eps()
    tables, recs, cells, tests, docs = [], [], [], [], set()
    for f in sorted((rep / "restore").glob("*.json")) if (rep / "restore").is_dir() else []:
        if f.name.startswith("RESTORE_"):
            continue
        dj = _jl(f) or {}
        meta = dj.get("document_meta") or {}
        fn, code = meta.get("file") or f.stem, str(meta.get("ticker") or "")
        docs.add(fn)
        for t in dj.get("tables", []):
            if t.get("status") == "未過" or not t.get("rows"):
                continue
            tables.append((fn, t))
            ec = eps_classify(t["rows"], code, dbe)
            cls = {i: (c, w) for i, c, w in ec}
            for i, r in enumerate(t["rows"]):
                for c in r.get("cells") or []:
                    cells.append({"file": fn, "table": t.get("id"), "std": (cls[i][0].lower() if i in cls else r.get("std") or ""), "label_raw": r.get("label_raw"), "eps_class": cls[i][0] if i in cls else "",
                                  "period": c.get("period"), "ptype": ptype(c.get("period")), "value": c.get("value")})
            ts = fin_tests(t["rows"])
            for x in ts:
                tests.append(dict(x, file=fn, table=t.get("id")))
            recs.append({"file": fn, "table": t.get("id"), "category": t.get("category"), "status": t.get("status"), "eps": [{"row": i, "class": c, "why": w} for i, c, w in ec],
                         "tests": len(ts), "fail": sum(1 for x in ts if x["status"] == "FAIL"), "pass_all": bool(ts) and all(x["status"] == "PASS" for x in ts)})
    sc = syn_candidates(tables)
    out = rep / "findata"
    out.mkdir(parents=True, exist_ok=True)
    (out / "FINDATA_latest.json").write_text(json.dumps({"tables": recs, "db_eps_codes": len(dbe)}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    for name, rows_, cols in (("FINDATA_CELLS", cells, ["file", "table", "std", "label_raw", "eps_class", "period", "ptype", "value"]),
                              ("FINDATA_TESTS", tests, ["file", "table", "rule", "kind", "period", "ptype", "status", "detail"])):
        cp = out / ("%s_latest.csv" % name)
        with cp.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows_)
        try:
            import duckdb  # noqa: WPS433
            duckdb.connect().execute("copy (select * from read_csv_auto('%s', header=true, all_varchar=true)) to '%s' (format parquet)" % (str(cp).replace("'", "''"), str(cp.with_suffix(".parquet")).replace("'", "''")))
        except Exception:  # noqa: BLE001
            pass
    K = Counter((x["kind"], x["ptype"], x["status"]) for x in tests)
    byrule = defaultdict(Counter)
    for x in tests:
        byrule[x["rule"]][x["status"]] += 1
    NEED = [("加減法", "歷史"), ("加減法", "預估"), ("除法", "歷史"), ("除法", "預估")]
    per = defaultdict(lambda: {"pass": set(), "fail": 0})
    for x in tests:
        if x["status"] == "PASS":
            per[x["file"]]["pass"].add((x["kind"], x["ptype"]))
        else:
            per[x["file"]]["fail"] += 1
    rep_ok = {fn: (per[fn]["fail"] == 0 and all(k in per[fn]["pass"] for k in NEED)) for fn in docs}      # 四類都有且全過才算(沒測到 ≠ 通過)
    missing = {"%s×%s" % k: sum(1 for fn in docs if k not in per[fn]["pass"]) for k in NEED}
    page = _resolve("_page")
    if page:
        rows_h = [("GREEN" if not c["FAIL"] else ("RED" if c["FAIL"] > c["PASS"] else "YELLOW"), [rule, c["PASS"], c["FAIL"], " | ".join("%s·%s·%s" % (x["file"][:22], x["period"], x["detail"])
                                                                                                                                for x in tests if x["rule"] == rule and x["status"] == "FAIL")[:200]]) for rule, c in sorted(byrule.items())]
        (out / "FINDATA_latest.html").write_text(page("FINANCIAL DATA · EPS 基本 / 稀釋 · 加減法 + 除法測試(歷史 + 預估)· 全部通過才算 VRN 成功", "表 %d · 格 %d · 資料庫 EPS %d 檔 · 同義字候選 %d(只列)" % (
            len(recs), len(cells), len(dbe), sc["n"]), ["規則", "過", "不符", "不符例(前幾個)"], rows_h), encoding="utf-8")
    ec = Counter(e["class"] for r in recs for e in r["eps"])
    return {"tables": len(recs), "cells": len(cells), "eps": dict(ec), "db_eps": len(dbe), "K": {"%s|%s|%s" % k: v for k, v in K.items()}, "byrule": {k: dict(v) for k, v in byrule.items()},
            "tables_tested": sum(1 for r in recs if r["tests"]), "tables_pass": sum(1 for r in recs if r["pass_all"]), "reports_tested": len(rep_ok), "reports_pass": sum(1 for v in rep_ok.values() if v),
            "missing": missing, "reports_with_fail": sum(1 for fn in docs if per[fn]["fail"]),
            "syn": sc, "html": str(out / "FINDATA_latest.html"), "fails": [x for x in tests if x["status"] == "FAIL"]}


def _lines_v178(bi: dict, fd: dict, rb: dict) -> list:
    L = []
    st = bi.get("status") or {}
    ro = bi.get("roster") or {}
    L.append("[計] BASIC INFO v2 · %d 份 · 綠 %d 黃 %d 紅 %d 灰 %d · 名冊 %s 碼(市場別 %s · 英文 %s)· 券商評等冊 %s" % (bi.get("n", 0), st.get("GREEN", 0), st.get("YELLOW", 0), st.get("RED", 0),
                                                                                                     st.get("GRAY", 0), ro.get("n", 0), ro.get("with_market", 0), ro.get("with_en", 0), rb.get("file", "—")))
    for fn, k in (bi.get("red") or [])[:8]:
        L.append("[計] BASIC v2 紅 · %s · %s" % (fn[:34], k))
    K = Counter()
    for k, v in (fd.get("K") or {}).items():
        K[tuple(k.split("|"))] = v
    ep = fd.get("eps") or {}
    L.append("[計] FINANCIAL DATA · 表 %d · 格 %d · EPS 稀釋 %d · 基本 %d · 未分 %d(資料庫歷史 EPS %s)" % (fd.get("tables", 0), fd.get("cells", 0), ep.get("DILUTED_EPS", 0), ep.get("BASIC_EPS", 0),
                                                                                       ep.get("EPS_UNSURE", 0), ("%d 檔" % fd["db_eps"]) if fd.get("db_eps") else "沒有 → 單列 EPS 只能標未分"))
    for kind in ("加減法", "除法"):
        L.append("[計] %s測試 · 歷史 過 %d / 不符 %d · 預估 過 %d / 不符 %d" % (kind, K[(kind, "歷史", "PASS")], K[(kind, "歷史", "FAIL")], K[(kind, "預估", "PASS")], K[(kind, "預估", "FAIL")]))
    for rule, c in sorted((fd.get("byrule") or {}).items(), key=lambda kv: -kv[1].get("FAIL", 0))[:8]:
        if c.get("FAIL"):
            ex = [x for x in fd.get("fails", []) if x["rule"] == rule][:2]
            L.append("[計] 不符 · %s × %d · 例 %s" % (rule, c["FAIL"], " | ".join("%s·%s·%s·%s" % (x["file"][:22], x["table"], x["period"], x["detail"]) for x in ex)))
    ok = bool(fd.get("reports_tested")) and fd.get("reports_pass") == fd.get("reports_tested") and not (bi.get("status") or {}).get("RED")
    L.append("[計] VRN 成功判定 · 報告 %d/%d(加減法 / 除法 × 歷史 / 預估 四類都有且全過)· 表全過 %d/%d · BASIC v2 紅 %d → %s" % (fd.get("reports_pass", 0), fd.get("reports_tested", 0),
             fd.get("tables_pass", 0), fd.get("tables_tested", 0), (bi.get("status") or {}).get("RED", 0), "成功" if ok else "未成功(全部報告四類都過才算)"))
    if fd.get("missing"):
        L.append("[計] 缺測(報告數 · 沒測到 ≠ 通過)· " + " · ".join("%s %d" % kv for kv in fd["missing"].items()) + " · 有不符的報告 %d" % fd.get("reports_with_fail", 0))
    L.append("[計] 同義字候選 · %d 個(只列 · 不自動加 · 更謹慎)· %s · 詞庫疑點 EPS growth → ni_growth(待確認)" % ((fd.get("syn") or {}).get("n", 0), (fd.get("syn") or {}).get("file", "—")))
    return L


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] in (["basicinfo2"], ["findata"]) or (args[:1] == ["auto"] and "--resume" not in args):
        rc = PRIOR.main(args) if args[:1] == ["auto"] else 0
        d = _resolve("_latest_l2_dir")("")
        rows = [((_jl(p) or {}).get("row") or {}) for p in sorted(d.glob("*.json"))] if d else []
        rbp = sorted(((_home or (lambda: HERE))() / "knowledge").glob("VRN_BrokerRating_Book_v*.json"), key=_vnum_v0178)
        rb = {"file": rbp[-1].name + "(沿用)"} if (rbp and d and rbp[-1].stat().st_mtime > d.stat().st_mtime) else tail_rating_book(rows)
        bi = basicinfo2_run() if args[:1] != ["findata"] else {}
        fd = findata_run() if args[:1] != ["basicinfo2"] else {}
        L = _lines_v178(bi or {}, fd or {}, rb)
        for l in L:
            print(l)
        for k, o in (("BASIC v2", bi), ("FINDATA", fd)):
            if (o or {}).get("html"):
                print("  [U/I] %s" % o["html"])
        if args[:1] == ["auto"]:
            pk = _rep() / "auto" / "VRN_AI_PACK_latest.md"
            if pk.exists():
                old = [l for l in pk.read_text(encoding="utf-8").splitlines() if l.strip()]
                nxt = [l for l in old if l.startswith("NEXT:")] or ["NEXT: 依本包修 → 再跑 auto"]
                body = [l for l in old if not l.startswith("NEXT:")] + L
                pk.write_text("\n".join(body[:299] + nxt[:1]) + "\n", encoding="utf-8")
                ac = _resolve("aiverb_compress")
                if ac:
                    dst, note = ac(pk, nxt[0].replace("NEXT: ", ""))
                    print("[計] AI 包(含 BASIC v2 / FINANCIAL DATA)· %s" % note)
        return rc
    return PRIOR.main(args)



def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    td = Path(tempfile.mkdtemp(prefix="vrn178-"))
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_HEALTH_OUT", "VIA_SPILL_DIR")}
    try:
        import duckdb
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        vdb = td / "vdb"
        vdb.mkdir()
        con = duckdb.connect()
        con.execute("""create table l as select * from (values ('3653','健策','Jentech','sii'), ('6488','環球晶','GlobalWafers','otc'), ('2330','台積電','TSMC','sii')) t("公司代號", "公司簡稱", "英文簡稱", "市場別")""")
        con.execute("copy l to '%s' (format parquet)" % (vdb / "tw__tw_listings.parquet"))
        con.execute("create table pr as select * from (values ('6488.TWO', 500.0), ('3653.TW', 1200.0)) t(ticker, close)")
        con.execute("copy pr to '%s' (format parquet)" % (vdb / "tw__tw_daily_prices.parquet"))
        con.execute("create table ep as select * from (values ('2330', 2023, 32.34, 32.34), ('2330', 2024, 45.25, 45.25), ('3653', 2024, 25.1, 24.8)) t(stock_id, year, eps_basic, eps_diluted)")
        con.execute("copy ep to '%s' (format parquet)" % (vdb / "tw__tw_income.parquet"))
        ro = tw_roster(vdb)
        cs = ro["codes"]
        chk("① 名冊(依欄值認欄 · 市場別 sii / otc 認得 · 價格表後綴反推):3653 健策 Jentech TWSE .TW · 6488 環球晶 TPEx .TWO",
            cs["3653"].get("cn") == "健策" and cs["3653"].get("en") == "Jentech" and cs["3653"].get("market") == "TWSE" and cs["6488"].get("suffix") == ".TWO" and cs["6488"].get("market") == "TPEx")
        pg = {"blocks": [{"kind": "text", "size": 22, "text": "健策 3653 TT:2025年營收創高"}, {"kind": "text", "size": 9, "text": "內文 2330"}]}
        chk("② 標題最大字找代號:3653 TT → 3653(年份 2025 不當代號 · 小字 2330 不看)", codes_in_title(pg) == ["3653"])
        af = analyst_from_filename("凱基投顧_2891 中信金_施志鴻_20260519.pdf", "2891", ["中信金"], ["凱基投顧", "凱基", "KGI"])
        af2 = analyst_from_filename("欣銓(3264,B_買進)-CTBC260918.pdf", "3264", ["欣銓"], ["CTBC", "中信"])
        chk("③ 檔名去券商 / 代號 / 簡稱 / 日期 → 剩下的是分析師:「%s」· 中信檔名沒分析師 →「%s」· EMAIL sharon.shih → %s" % (af, af2, email_name("sharon.shih@morganstanley.com")),
            af == "施志鴻" and af2 == "" and email_name("sharon.shih@morganstanley.com") == "Sharon Shih" and email_name("ytliu@kgi.com") == "ytliu")
        R = lambda lab, std, vals: {"label_raw": lab, "std": std, "cells": [{"period": k, "value": v} for k, v in vals.items()]}  # noqa: E731
        e1 = eps_classify([R("EPS", "eps", {"2024A": 2.6, "2025F": 3.0}), R("EPS", "eps", {"2024A": 2.5, "2025F": 2.9})])
        e2 = eps_classify([R("Diluted EPS (NT$)", "eps", {"2024A": 2.5}), R("Basic EPS", "eps", {"2024A": 2.6})])
        dbe = db_eps(vdb)
        e3 = eps_classify([R("EPS", "eps", {"2023A": 32.34, "2024A": 45.25, "2025F": 60.0})], "2330", dbe)
        e4 = eps_classify([R("EPS", "eps", {"2024A": 5.0})], "9999", dbe)
        chk("④ EPS:兩列取小 = 稀釋 · 名稱寫明照名稱 · 只一列 → 歷史 2 期對上資料庫稀釋 → 改標稀釋 · 資料庫沒有 → 未分",
            [c for _, c, _ in e1] == ["BASIC_EPS", "DILUTED_EPS"] and [c for _, c, _ in e2] == ["DILUTED_EPS", "BASIC_EPS"] and e3[0][1] == "DILUTED_EPS" and "2 期" in e3[0][2] and e4[0][1] == "EPS_UNSURE")
        good = [R("Revenue", "revenue", {"2024A": 1000, "2025F": 1200}), R("COGS", "cogs", {"2024A": -600, "2025F": -700}), R("Gross profit", "gross_profit", {"2024A": 400, "2025F": 500}),
                R("Opex", "opex", {"2024A": 200, "2025F": 250}), R("Operating income", "operating_income", {"2024A": 200, "2025F": 250}), R("GM %", "gross_margin", {"2024A": 40.0, "2025F": 41.67}),
                R("Revenue growth", "rev_growth", {"2025F": 20.0})]
        t1 = fin_tests(good)
        bad = [dict(r) for r in good]
        bad[2] = R("Gross profit", "gross_profit", {"2024A": 400, "2025F": 450})
        t2 = fin_tests(bad)
        ks = Counter((x["kind"], x["ptype"], x["status"]) for x in t1)
        chk("⑤ 加減法 + 除法測試 歷史 + 預估 都做:全過(加減 歷史 %d / 預估 %d · 除法 歷史 %d / 預估 %d · 含成長率 1200/1000 − 1 = 20%%)· 毛利改 450 → 加減法和毛利率都不符" % (
            ks[("加減法", "歷史", "PASS")], ks[("加減法", "預估", "PASS")], ks[("除法", "歷史", "PASS")], ks[("除法", "預估", "PASS")]),
            t1 and all(x["status"] == "PASS" for x in t1) and ks[("加減法", "預估", "PASS")] >= 2 and ks[("除法", "預估", "PASS")] >= 2 and any("成長" in x["rule"] for x in t1)
            and sum(1 for x in t2 if x["status"] == "FAIL") >= 2)
        rp = td / "rep" / "restore"
        rp.mkdir(parents=True)
        rows_full = good + [R("Net income", "net_income", {"2024A": 150, "2025F": 190}), R("NM %", "net_margin", {"2024A": 15.0, "2025F": 15.83})]
        (rp / "01_a.json").write_text(json.dumps({"document_meta": {"file": "A.pdf", "ticker": "1111"}, "tables": [{"id": "T1", "status": "還原無誤", "rows": rows_full}]}, ensure_ascii=False), encoding="utf-8")
        (rp / "02_b.json").write_text(json.dumps({"document_meta": {"file": "B.pdf", "ticker": "2222"}, "tables": [{"id": "T1", "status": "還原無誤", "rows": [R("P/E", "pe", {"2025F": 12.0})]}]}, ensure_ascii=False), encoding="utf-8")
        fdx = findata_run()
        chk("⑩ VRN 成功判定嚴格:A 四類都有且全過 → 成功 · B 只有本益比(沒有可測科目)→ 不算成功(沒測到 ≠ 通過)→ 報告 %d/%d · 缺測 %s" % (fdx["reports_pass"], fdx["reports_tested"], fdx["missing"]),
            fdx["reports_tested"] == 2 and fdx["reports_pass"] == 1 and fdx["missing"]["加減法×歷史"] == 1)
        home = td / "VRN"
        (home / "knowledge").mkdir(parents=True)
        saved_home = globals().get("_home")
        globals()["_home"] = lambda: home  # noqa: E731
        try:
            s1 = syn_candidates([("a.pdf", {"id": "T1", "unmatched_labels": ["營業外淨額", "123", "營業外淨額"]})])
            s2 = syn_candidates([("a.pdf", {"id": "T1", "unmatched_labels": ["營業外淨額", "123", "營業外淨額"]})])
            from reportlab.pdfgen import canvas
            pdf = td / "MS-2308 20251128.pdf"
            c = canvas.Canvas(str(pdf))
            c.drawString(50, 700, "Investment thesis")
            c.showPage()
            c.setFont("Helvetica", 6)
            c.drawString(50, 700, "Stock Ratings: Overweight (O) Equal-weight (E) Underweight (U) Not-Rated (NR)")
            c.save()
            rb = tail_rating_book([{"path": str(pdf), "broker": "MS"}])
            chk("⑥ 同義字候選只列不自動加(第二次內容沒變不出新版 · 數字標籤濾掉)· 報告尾部評等表 → MS:%s" % ", ".join((rb["body"].get("MS") or {}).get("terms", [])),
                s1["file"].endswith("_v0100.json") and "無變更" in s2["file"] and {"Overweight", "Underweight"} <= set((rb["body"].get("MS") or {}).get("terms", [])))
            stage = td / "VIA_progress" / "ps_x" / "spill" / "vrn_stage_r1" / "layout_l2"
            stage.mkdir(parents=True)
            (stage / "a.json").write_text(json.dumps({"row": {"file": "凱基投顧_6488 環球晶_施志鴻_20260519.pdf", "code": "6488", "name": "環球晶", "broker": "KGI"},
                                                      "info": {"rating_raw": "Outperform", "rating": "Buy", "date_p1": "2026-05-19", "analysts": [{"name": "施志鴻", "email": "zhihong.shih@kgi.com", "title": "分析師"}]},
                                                      "pages": [{"blocks": [{"kind": "text", "size": 20, "text": "環球晶 (6488 TT) 擴產"}, {"kind": "text", "size": 9, "text": "環球晶 營收"}]}]}, ensure_ascii=False), encoding="utf-8")
            os.environ["VIA_SPILL_DIR"] = str(td / "VIA_progress" / "ps_new" / "spill")
            (td / "rep" / "basicinfo").mkdir(parents=True)
            (td / "rep" / "basicinfo" / "BASIC_INFO_latest.json").write_text(json.dumps({"records": [{"fields": {"FILENAME": {"value": "凱基投顧_6488 環球晶_施志鴻_20260519.pdf", "status": "GREEN", "source": "", "check": ""},
                                                                                                                  "TP_ORIGINAL": {"value": 600.0, "status": "GREEN", "source": "", "check": ""}}}]}, ensure_ascii=False), encoding="utf-8")
            bi = basicinfo2_run(ro=ro, book={"KGI": {"unified": True, "aliases": ["凱基投顧", "凱基", "KGI"]}})
            js = _jl(td / "rep" / "basicinfo" / "BASIC_INFO_V2_latest.json")
            r0 = js["records"][0]["fields"]
            hdr = (td / "rep" / "basicinfo" / "BASIC_INFO_V2_latest.csv").read_text(encoding="utf-8-sig").splitlines()[0].split(",")
            chk("⑦ BASIC INFO v2:欄序照規格 · 標題代號 6488 = 檔名 · yfinance 6488.TWO(上櫃)· 名稱 環球晶 / GlobalWafers · 評等照原文 Outperform · 檔名分析師 施志鴻 = 首頁 · TP 600",
                hdr == COLS2 and r0["TICKER"]["status"] == "GREEN" and r0["YF_TICKER"]["value"] == "6488.TWO" and r0["NAME_DB"]["value"] == "環球晶" and r0["NAME_EN_DB"]["value"] == "GlobalWafers"
                and r0["RATING"]["value"] == "Outperform" and r0["ANALYST_FROM_FILENAME"]["value"] == "施志鴻" and r0["ANALYST_FROM_FILENAME"]["status"] == "GREEN" and r0["TARGET_PRICE"]["value"] == 600.0)
        finally:
            globals()["_home"] = saved_home
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑨ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0178 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
