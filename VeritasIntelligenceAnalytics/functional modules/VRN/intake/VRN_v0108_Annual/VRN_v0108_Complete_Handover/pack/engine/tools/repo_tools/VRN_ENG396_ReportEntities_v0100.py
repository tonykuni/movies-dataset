#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VRN_ENG396_ReportEntities v0100 — 研報本文實體:公司名稱(中英 · 最簡寫 · 局部識別)· 目標價(本次 / 調整前)· 評價法

操作員 R36e(2026-10-01):「本文可找到公司名稱中英文最簡寫局部識別」「目標價(調整前) 評價法」。規則冊 VIA_VRN_ReportEntities_SSOT_v*.json
(本支照冊讀,不另寫第二份);評價法代碼由 VIA_VRN_ValuationMethod_SSOT(VRN_ENG395 尾版 Matcher)判,表格由 VRN_ENG394 尾版還原。

一、公司名稱:名稱來源 = 檔名代號旁的中文股名 · 首頁帶代號記號的行(Wistron (3231.TW) · 神達(3706 TT))· 呼叫端給的別名。
   推形式:全名 → 去法定後綴(股份有限公司 / Co., Ltd. …)→ 去產業後綴(精密工業 / Electronics …)→ 英文連續詞段 · 字首縮寫。
   本文比對:已知形式最長優先;中文另做「局部識別」= 首字相同、依序取自全名的 2–4 字(台積電 ← 台灣積體電路製造 · 中信金 ← 中國信託金融控股),
   停用詞(中國 / 台灣 / 國際 …)不算;英文單詞形式只認大寫開頭(Delta 不吃 delta)。最簡寫 = 本文**實際出現過**的最短形式(不是推算的)。
二、目標價:成對式先跑(from A to B · to B from A · B (prev. A) · 目標價由 A 上調至 B · B 元(原 A 元))並遮掉區間,
   只給一邊的式子後跑(前次目標價 A · previous TP A · 目標價 B)。數字後接 % / x / 倍 / 年 / E / F / bn … 一律剔除(那不是價格)。
   方向 up / down / maintain / unknown;調幅 = 本次 ÷ 調整前 − 1。
三、評價法:句子有評價語境(目標價 / 評價 / 給予 / valuation / based on …)→ ENG395 判 VAL_* 代碼(需語境的詞嚴格模式不算)·
   倍數(14x / 20 倍)· 基準年(2026E / 2026 年預估 / FY26E)· 基準指標(PE→EPS · PB→BVPS …)。
   驗算:倍數 × 基準年指標 ≈ 目標價(±3%):指標值取句內明寫的(EPS of NT$21.4 / EPS 3.6 元),沒有就到本頁還原的表格找該年 EPS / BVPS;
   都找不到 = UNVERIFIED(未驗,不是錯);差超過 3% = MISMATCH(列出)。
輸出:VIA_Reports/vrn/entities/<檔>.entities.md(所有表垂直線分隔)· .entities.json · ENTITIES_latest.json。只讀來源;零網路;不用 TA-Lib;正本唯讀。
只收 VCGC 呼叫(VIA_FROM_VCGC=YES;--selftest 例外)。CLI:run --in <pdf|夾> [--pages 1|all|1-3] · text --in <txt> [--name 檔名] · --selftest
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

import importlib.util
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REG = VIA / "supportive modules" / "registry"
OUT = VIA / "VIA_Reports" / "vrn" / "entities"
ENGINE = Path(__file__).stem
SSOT_GLOB = "VIA_VRN_ReportEntities_SSOT_v*.json"
CJK = "一-鿿"
_BOOK: dict | None = None
_MODS: dict = {}


def book() -> dict:
    global _BOOK
    if _BOOK is None:
        hits = sorted(REG.glob(SSOT_GLOB))
        if not hits:
            raise FileNotFoundError("規則冊 " + SSOT_GLOB + " 不在 registry(本支不另寫第二份)")
        _BOOK = json.loads(hits[-1].read_text(encoding="utf-8"))
        _BOOK["_path"] = hits[-1].name
    return _BOOK


def _tail(stem: str):
    if stem in _MODS:
        return _MODS[stem]
    hits = sorted(HERE.glob(stem + "_v*.py"))
    mod = None
    if hits:
        spec = importlib.util.spec_from_file_location(stem.lower() + "_for_" + ENGINE, hits[-1])
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        try:
            spec.loader.exec_module(mod)
        except Exception:
            mod = None
    _MODS[stem] = mod
    return mod


def norm(s: str) -> str:
    return re.sub(r"[ \t]+", " ", unicodedata.normalize("NFKC", str(s or "")))


def tidy(s: str) -> str:
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return re.sub(rf"(?<=[{CJK}]) (?=\S)|(?<=\S) (?=[{CJK}])", "", s)


def md_table(cols: list, rows: list) -> str:
    c = lambda x: tidy(x).replace("|", "\\|")  # noqa: E731
    out = ["| " + " | ".join(c(x) for x in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    out += ["| " + " | ".join(c(x) for x in (list(r) + [""] * (len(cols) - len(r)))[:len(cols)]) + " |" for r in rows]
    return "\n".join(out)


# ---------------------------------------------------------------- 一、公司名稱

def _code_of(stem: str) -> str:
    for rx in (r"[A-Za-z]{1,6}-\s*([1-9]\d{3})(?!\d)", r"[\(（]\s*([1-9]\d{3})(?=[\s,，)）_])", r"(?:^|[_\s\-])([1-9]\d{3})(?=[\s_\-](?![年]))"):
        m = re.search(rx, stem)
        if m:
            return m.group(1)
    return ""


def _strip_suffix(name: str, sufs: list, min_left: int) -> str:
    changed = True
    while changed:
        changed = False
        for s in sorted(sufs, key=len, reverse=True):
            t, s2 = name.rstrip(" ,."), s.rstrip(" ,.")
            if s2 and t.lower().endswith(s2.lower()) and len(t) - len(s2) >= min_left:
                name = t[: len(t) - len(s2)].rstrip(" ,.-")
                changed = True
                break
    return name.strip()


def _strip_industry_once(name: str, sufs: list, min_left: int) -> str:
    for s in sorted(sufs, key=len, reverse=True):
        t = name.rstrip(" ,.")
        if t.lower().endswith(s.lower()) and len(t) - len(s) >= min_left:
            return t[: len(t) - len(s)].rstrip(" ,.-").strip()
    return name


def name_forms(name: str) -> dict:
    """一個名稱 → {lang, full, legal_stripped, short_forms[], acronym}"""
    C = book()["company"]
    name = norm(name).strip(" ,")
    zstop = set(C["zh_stop_words"])
    estop = {s.lower() for s in C["en_stop_tokens"]}
    if re.search(f"[{CJK}]", name):
        legal = _strip_suffix(name, C["legal_suffix_zh"], 2)
        forms = [name, legal]
        cur = legal
        while True:
            nxt = _strip_industry_once(cur, C["industry_suffix_zh"], 2)
            if nxt == cur:
                break
            forms.append(nxt)
            cur = nxt
        return {"lang": "zh", "full": name, "legal": legal,
                "forms": list(dict.fromkeys(f for f in forms if len(f) >= 2 and f not in zstop)), "acronym": ""}
    legal = _strip_suffix(name, C["legal_suffix_en"], 3)
    toks = legal.split()
    ind = {s.lower() for s in C["industry_suffix_en"]}
    core = list(toks)
    while len(core) > 1 and core[-1].lower().strip(".,") in ind:
        core.pop()
    stop = estop
    forms = [name, legal, " ".join(core)]
    for k in range(len(core), 0, -1):                      # 連續詞段:由長到短的前綴(首詞不是停用詞、合計 ≥ 4 字母)
        span = core[:k]
        if span[0].lower() in stop and k == 1:
            continue
        if sum(ch.isalpha() for ch in "".join(span)) >= 4:
            forms.append(" ".join(span))
    skip = {x.lower() for x in C.get("acronym_skip", [])}
    caps = [t for t in name.split() if t[:1].isupper() and t.lower().strip(",") not in skip]
    acr = "".join(t[0] for t in caps) if len(caps) >= 3 else ""
    return {"lang": "en", "full": name, "legal": legal,
            "forms": list(dict.fromkeys(f for f in forms if f and f.lower() not in estop)), "acronym": acr.upper()}


def company_identity(stem: str, page1_text: str = "", aliases: list | None = None) -> dict:
    C = book()["company"]
    code = _code_of(stem)
    names = []
    if code:
        for m in re.finditer(rf"([{CJK}]{{2,8}})\s*[\(（]?\s*{code}|{code}[\s_\-]*([{CJK}]{{2,8}})", stem):
            n = m.group(1) or m.group(2)
            if n and not re.search(r"投顧|證券|投信|研究部|證期", n):
                names.append({"name": n, "source": "filename"})
    for m in re.finditer(C["ticker_mark_rx"], norm(page1_text)):
        if code and m.group("code") != code:
            continue
        n = m.group("name").strip(" -–|:")
        n = re.split(r"\s{2,}|\|", n)[-1].strip()
        if len(re.sub(r"\W", "", n)) >= 2:
            names.append({"name": n, "source": "page1_ticker_mark"})
        if not code:
            code = m.group("code")
    for a in aliases or []:
        names.append({"name": a, "source": "alias"})
    seen, uniq = set(), []
    for n in names:
        if n["name"] not in seen:
            seen.add(n["name"])
            uniq.append({**n, **name_forms(n["name"])})
    return {"code": code, "names": uniq}


def _is_subseq(s: str, full: str) -> bool:
    it = iter(full)
    return all(ch in it for ch in s)


def mentions(lines: list, ident: dict, page: int = 1) -> list:
    """本文提及:已知形式最長優先(英文單詞只認大寫開頭)+ 中文局部識別(首字相同、依序取自全名的 2–4 字)。"""
    C = book()["company"]
    zstop = set(C["zh_stop_words"])
    forms = {}
    for n in ident["names"]:
        for f in n["forms"]:
            forms.setdefault(f, ("full" if f == n["full"] else "short", n["lang"]))
        if n.get("acronym") and len(n["acronym"]) >= 3:
            forms.setdefault(n["acronym"], ("acronym", "en"))
    zfulls = [n["full"] for n in ident["names"] if n["lang"] == "zh"] + [n["legal"] for n in ident["names"] if n["lang"] == "zh"]
    alts = []
    for f in sorted(forms, key=len, reverse=True):
        e = re.escape(f)
        if forms[f][1] == "en":
            e = r"(?<![A-Za-z])" + e + r"(?![A-Za-z])"
        alts.append(e)
    rx = re.compile("|".join(alts)) if alts else None
    out = []
    for li, ln in enumerate(lines, 1):
        s = norm(ln)
        taken = []
        if rx:
            for m in rx.finditer(s):
                kind, lang = forms[m.group(0)]
                out.append({"form": m.group(0), "kind": kind, "lang": lang, "anchor": f"p{page}·L{li}", "span": [m.start(), m.end()]})
                taken.append((m.start(), m.end()))
        for full in dict.fromkeys(zfulls):
            if len(full) < 3:
                continue
            for i, ch in enumerate(s):
                if ch != full[0] or any(a <= i < b for a, b in taken):
                    continue
                for L in (4, 3, 2):
                    cand = s[i:i + L]
                    if len(cand) < L or not re.fullmatch(f"[{CJK}]+", cand) or cand in zstop or cand in forms:
                        continue
                    if _is_subseq(cand, full) and not any(a < i + L and i < b for a, b in taken):
                        out.append({"form": cand, "kind": "partial", "lang": "zh", "anchor": f"p{page}·L{li}", "span": [i, i + L]})
                        taken.append((i, i + L))
                        break
    return out


def summarize_mentions(hits: list) -> dict:
    by = {}
    for h in hits:
        e = by.setdefault(h["form"], {"form": h["form"], "kind": h["kind"], "lang": h["lang"], "count": 0, "anchors": []})
        e["count"] += 1
        if len(e["anchors"]) < 5:
            e["anchors"].append(h["anchor"])
    rows = sorted(by.values(), key=lambda e: (-e["count"], len(e["form"])))
    shortest = {}
    for lang in ("zh", "en"):
        c = [e["form"] for e in rows if e["lang"] == lang]
        shortest[lang] = min(c, key=len) if c else ""
    return {"forms": rows, "shortest": shortest, "total": sum(e["count"] for e in rows)}


# ---------------------------------------------------------------- 二、目標價

def _price(s: str):
    try:
        return float(s.replace(",", ""))
    except Exception:
        return None


def target_prices(text: str) -> dict:
    T = book()["target_price"]
    s = norm(text)
    P = T["price_rx"]
    rej = re.compile(T["reject_tail_rx"])
    taken, hits = [], []
    for pat in T["patterns"]:
        rx = pat["rx"].replace("{P1}", P.replace("(?P<v>", "(?P<p1>")).replace("{P2}", P.replace("(?P<v>", "(?P<p2>"))
        for m in re.finditer(rx, s):
            if any(a < m.end() and m.start() < b for a, b in taken):
                continue
            vals, bad = {}, ""
            for g in ("p1", "p2"):
                if g in m.groupdict() and m.group(g) is not None:
                    tail = s[m.end(g):m.end(g) + 6]
                    if rej.match(tail):
                        bad = f"{m.group(g)} 後接「{tail.strip()[:4]}」=不是價格"
                    vals[g] = _price(m.group(g))
            if bad or any(v is None or v <= 0 for v in vals.values()):
                continue
            prior = vals.get("p1") if pat.get("prior") else None
            cur = vals.get("p2") if pat.get("current") else None
            hits.append({"pattern": pat["id"], "prior": prior, "current": cur, "snippet": tidy(s[max(0, m.start() - 10):m.end() + 6])[:120],
                         "span": [m.start(), m.end()]})
            taken.append((m.start(), m.end()))
    hits.sort(key=lambda h: h["span"][0])
    paired = [h for h in hits if h["prior"] is not None and h["current"] is not None]
    cur = paired[0]["current"] if paired else next((h["current"] for h in hits if h["current"] is not None), None)
    prior = paired[0]["prior"] if paired else next((h["prior"] for h in hits if h["prior"] is not None), None)
    maintain = bool(re.search(T["maintain_rx"] + r"[^。.\n]{0,20}(?:目標價|TP|PT|target)", s))
    if cur is not None and prior is not None:
        direction = "up" if cur > prior else "down" if cur < prior else "flat"
        chg = round((cur / prior - 1) * 100, 2) if prior else None
    else:
        direction, chg = ("maintain" if maintain and cur is not None else "unknown"), None
    return {"current": cur, "prior": prior, "direction": direction, "change_pct": chg, "hits": hits}


# ---------------------------------------------------------------- 三、評價法

def _year4(y: str):
    m = re.search(r"(19|20)?(\d{2})", y or "")
    if not m:
        return None
    return int((m.group(1) or "20") + m.group(2))


def _table_metric(tables: list, metric: str, year: int):
    V = book()["valuation"]
    aliases = [a.lower() for a in V["table_metric_aliases"].get(metric, [metric])]
    for t in tables or []:
        cols = [str(c) for c in t.get("columns", [])]
        rows = t.get("rows", [])
        for ci, c in enumerate(cols):                      # 欄 = 指標、列 = 年
            if ci and any(a in c.lower() for a in aliases):
                for r in rows:
                    if _year4(str(r[0])) == year and re.search(r"(?:19|20)?\d{2}", str(r[0])) and _price(str(r[ci])) is not None:
                        return _price(str(r[ci])), f"表「{t.get('title') or ''}」欄 {c} 列 {r[0]}"
        for r in rows:                                     # 列 = 指標、欄 = 年
            if any(a in str(r[0]).lower() for a in aliases):
                for ci, c in enumerate(cols):
                    if ci and _year4(c) == year and _price(str(r[ci])) is not None:
                        return _price(str(r[ci])), f"表列 {r[0]} 欄 {c}"
    return None, ""


def valuations(text: str, tables: list | None = None, tp: dict | None = None) -> list:
    V = book()["valuation"]
    e395 = _tail("VRN_ENG395_ValuationMethodLexicon")
    e394 = _tail("VRN_ENG394_LayoutRestore")
    if e395 is None:
        return [{"state": "NODATA", "why": "VRN_ENG395 不在"}]
    mt = e395.Matcher()
    s = norm(text)
    sents = [x for _a, _b, x in e394.sentences(s)] if e394 else re.split(r"(?<=[。.!?;；])\s*", s)
    cue = re.compile(V["cue_rx"])
    mrx, yrx = re.compile(V["multiple_rx"]), re.compile(V["year_rx"])
    metric_alias = {k: v for k, v in V["table_metric_aliases"].items()}
    out = []
    for sent in sents:
        meth = [h for h in mt.match(sent) if not h["context_required"]]
        mm = mrx.search(sent)
        inferred = False
        if not meth and mm:                                   # 「14x 2026E EPS」:倍數後緊接指標詞 → 推定方法(標 inferred)
            after = sent[mm.end():mm.end() + 24].lower()
            for vid, words in (V.get("implied_method") or {}).get("map", {}).items():
                w = next((x for x in words if x.lower() in after), None)
                if w:
                    meth, inferred = [{"id": vid, "term": f"{mm.group(0)} … {w}(推定)"}], True
                    break
        if not meth or not cue.search(sent):
            continue
        mid = meth[0]["id"]
        mult = float(mm.group("m")) if mm else None
        yr = None
        if mm:
            near = [(abs(y.start() - mm.end()), y.group("y")) for y in yrx.finditer(sent)]
            yr = _year4(min(near)[1]) if near else None
        else:
            y = yrx.search(sent)
            yr = _year4(y.group("y")) if y else None
        metric = V["metric_of_method"].get(mid, "")
        val, vsrc = None, ""
        if metric in metric_alias:
            al = "|".join(re.escape(a) for a in sorted(metric_alias[metric], key=len, reverse=True))
            em = re.search(V["metric_value_rx"].replace("{ALIAS}", al), sent, re.I)
            if em and not (mm and em.start("v") == mm.start("m")):
                val, vsrc = float(em.group("v")), "句內明寫"
            elif yr:
                val, vsrc = _table_metric(tables or [], metric, yr)
        stp = target_prices(sent)["current"] or (tp or {}).get("current")
        state, implied = "UNVERIFIED", None
        if mult and val:
            implied = round(mult * val, 2)
            if stp:
                state = "VERIFIED" if abs(implied - stp) <= stp * V["check_tol"] else "MISMATCH"
        out.append({"method": mid, "method_term": meth[0]["term"], "inferred": inferred, "multiple": mult, "basis_year": yr, "metric": metric,
                    "metric_value": val, "metric_source": vsrc, "implied_tp": implied, "target_price": stp, "check": state,
                    "sentence": tidy(sent)[:200]})
    return out


# ---------------------------------------------------------------- 整份

def analyze_text(text: str, stem: str = "", page_texts: list | None = None, aliases: list | None = None) -> dict:
    pages = page_texts or [text]
    ident = company_identity(stem, pages[0], aliases)
    hits = []
    for pi, pt in enumerate(pages, 1):
        hits += mentions(pt.splitlines(), ident, pi)
    e394 = _tail("VRN_ENG394_LayoutRestore")
    tables, notes = [], []
    if e394:
        for pi, pt in enumerate(pages, 1):
            try:
                tables += [t for t in e394.text_tables(" ".join(pt.splitlines()))]
            except Exception as exc:                        # 表格還原失敗不擋實體抽取,但要留紀錄
                notes.append(f"p{pi} ENG394 text_tables {type(exc).__name__}: {str(exc)[:60]}")
    else:
        notes.append("ENG394 不在 → 表內驗算不可用")
    full = "\n".join(pages)
    tp = target_prices(full)
    vals = valuations(full, tables, tp)
    return {"name": stem, "identity": ident, "mentions": summarize_mentions(hits), "target_price": tp, "valuation": vals,
            "tables_seen": len(tables), "notes": notes}


def analyze_pdf(path: Path, pages: str = "all", aliases: list | None = None) -> dict:
    import fitz
    with fitz.open(str(path)) as doc:
        n = doc.page_count
        if pages == "all":
            sel = range(1, n + 1)
        else:
            m = re.fullmatch(r"(\d+)(?:-(\d+))?", pages or "1")
            a, b = (int(m.group(1)), int(m.group(2) or m.group(1))) if m else (1, 1)
            sel = [p for p in range(a, b + 1) if 1 <= p <= n]
        texts = [doc[p - 1].get_text("text") for p in sel]
    r = analyze_text("\n".join(texts), Path(path).stem, texts, aliases)
    r["name"] = Path(path).name
    return r


def to_markdown(r: dict) -> str:
    idt, mn, tp = r["identity"], r["mentions"], r["target_price"]
    out = [f"# 研報實體 · {r['name']}", "", f"代號 {idt['code'] or '—'} · 規則冊 {book().get('_path')} · 引擎 {ENGINE}", "", "## 公司名稱", "",
           md_table(["來源", "語言", "全名", "去法定後綴", "簡稱形式", "字首縮寫"],
                    [[n["source"], n["lang"], n["full"], n["legal"], " / ".join(n["forms"]), n.get("acronym") or ""] for n in idt["names"]]), "",
           f"最簡寫(本文實際出現):中 {mn['shortest'].get('zh') or '—'} · 英 {mn['shortest'].get('en') or '—'} · 提及 {mn['total']} 次", "",
           md_table(["形式", "類別", "語言", "次數", "據點"], [[e["form"], e["kind"], e["lang"], e["count"], " ".join(e["anchors"])] for e in mn["forms"]]),
           "", "## 目標價", "",
           md_table(["本次", "調整前", "方向", "調幅%"], [[tp["current"] if tp["current"] is not None else "—", tp["prior"] if tp["prior"] is not None else "—",
                                                  tp["direction"], tp["change_pct"] if tp["change_pct"] is not None else "—"]]), "",
           md_table(["式子", "調整前", "本次", "原文"], [[h["pattern"], h["prior"] if h["prior"] is not None else "", h["current"] if h["current"] is not None else "",
                                                  h["snippet"]] for h in tp["hits"]]), "", "## 評價法", ""]
    if r["valuation"]:
        out.append(md_table(["代碼", "命中詞", "倍數", "基準年", "指標", "指標值", "指標來源", "隱含目標價", "目標價", "驗算", "句子"],
                            [[v.get("method"), v.get("method_term"), v.get("multiple"), v.get("basis_year"), v.get("metric"), v.get("metric_value"),
                              v.get("metric_source"), v.get("implied_tp"), v.get("target_price"), v.get("check"), v.get("sentence", "")[:90]]
                             for v in r["valuation"]]))
    else:
        out.append("(本文沒有可辨識的評價句)")
    return "\n".join(str(x) for x in out) + "\n"


def write_outputs(docs: list, out: Path = OUT) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for d in docs:
        stem = Path(d["name"]).stem
        (out / f"{stem}.entities.md").write_text(to_markdown(d), encoding="utf-8")
        (out / f"{stem}.entities.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    slim = [{"name": d["name"], "code": d["identity"]["code"], "shortest": d["mentions"]["shortest"], "tp": d["target_price"]["current"],
             "tp_prior": d["target_price"]["prior"], "direction": d["target_price"]["direction"],
             "methods": sorted({v.get("method") for v in d["valuation"] if v.get("method")}),
             "checks": [v.get("check") for v in d["valuation"]]} for d in docs]
    (out / "ENTITIES_latest.json").write_text(json.dumps({"engine": ENGINE, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                                          "book": book().get("_path"), "docs": slim}, ensure_ascii=False, indent=1), encoding="utf-8")


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    given = [args[i + 1] for i, a in enumerate(args) if a == "--in" and i + 1 < len(args)]
    pages = args[args.index("--pages") + 1] if "--pages" in args and args.index("--pages") + 1 < len(args) else "all"
    docs = []
    if args[:1] == ["text"]:
        nm = args[args.index("--name") + 1] if "--name" in args else ""
        for g in given:
            r = analyze_text(Path(g).read_text(encoding="utf-8", errors="replace"), nm or Path(g).stem)
            r["name"] = Path(g).name
            docs.append(r)
    else:
        for g in given:
            p = Path(g)
            for f in (sorted(p.rglob("*.pdf")) if p.is_dir() else [p]):
                try:
                    docs.append(analyze_pdf(f, pages))
                except Exception as exc:
                    print(f"  [略過] {f.name}:{type(exc).__name__}: {str(exc)[:80]}")
    if not docs:
        print("[研報實體] 沒有輸入(--in <pdf|夾>)")
        return 2
    write_outputs(docs)
    for d in docs:
        tp = d["target_price"]
        print(f"  {d['name'][:60]} · 代號 {d['identity']['code'] or '—'} · 最簡寫 {d['mentions']['shortest']} · 目標價 {tp['current']}"
              f"(調整前 {tp['prior']} · {tp['direction']})· 評價法 {sorted({v.get('method') for v in d['valuation'] if v.get('method')})}")
    print(f"[研報實體] {len(docs)} 份 · 頁 {OUT}")
    return 0


# ---------------------------------------------------------------- selftest(夾具是本支自寫的中性句子,不存報告正文)

def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    B = book()
    chk("規則冊在 registry · 本支照冊讀", B.get("owner_engine") == "VRN_ENG396_ReportEntities")
    # 英文:鴻海
    en = ("Hon Hai Precision Industry Co., Ltd. (2317.TW)\nRaise TP from NT$270 to NT$300 on AI server upside.\n"
          "We value Hon Hai at 14x 2026E EPS of NT$21.4, in line with peers.\nHon Hai remains our top pick; Hon Hai shares look cheap.")
    r = analyze_text(en, "GS-2317 20251205")
    n = r["identity"]["names"]
    chk("英文:首頁帶代號記號的行 → 全名 · 去法定後綴 · 去產業後綴 → Hon Hai", r["identity"]["code"] == "2317" and n
        and n[0]["full"] == "Hon Hai Precision Industry Co., Ltd." and n[0]["legal"] == "Hon Hai Precision Industry" and "Hon Hai" in n[0]["forms"]
        and n[0]["acronym"] == "HHPI", n)
    chk("英文:最簡寫 = 本文實際出現的 Hon Hai(提及 ≥3)", r["mentions"]["shortest"]["en"] == "Hon Hai"
        and sum(e["count"] for e in r["mentions"]["forms"] if e["form"] == "Hon Hai") >= 3, r["mentions"])
    tp = r["target_price"]
    chk("目標價:from NT$270 to NT$300 → 本次 300 · 調整前 270 · up · +11.11%", tp["current"] == 300 and tp["prior"] == 270
        and tp["direction"] == "up" and tp["change_pct"] == 11.11, tp)
    v = r["valuation"][0] if r["valuation"] else {}
    chk("評價法:「14x 2026E EPS」推定 VAL_PE(標 inferred)· 14x · 2026 · EPS 21.4(句內)· 隱含 299.6 ≈ 300 → VERIFIED",
        v.get("method") == "VAL_PE" and v.get("inferred") is True and v.get("multiple") == 14
        and v.get("basis_year") == 2026 and v.get("metric_value") == 21.4 and v.get("check") == "VERIFIED", v)
    # 中文:南亞
    zh = ("南亞塑膠工業(1303 TT)\n目標價由60元上調至72元。\n給予2026年預估EPS 3.6元、20倍本益比評價。\n南亞第三季營收成長,南亞塑膠受惠利差擴大。")
    r = analyze_text(zh, "南亞(1303,B_買進)-CTBC260918")
    nm = [x["full"] for x in r["identity"]["names"]]
    chk("中文:檔名股名「南亞」+ 首頁「南亞塑膠工業」都收 · 全名去後綴到 南亞", "南亞" in nm and "南亞塑膠工業" in nm
        and "南亞" in next(x for x in r["identity"]["names"] if x["full"] == "南亞塑膠工業")["forms"], r["identity"])
    chk("中文:最簡寫 = 南亞", r["mentions"]["shortest"]["zh"] == "南亞", r["mentions"]["shortest"])
    tp = r["target_price"]
    chk("目標價:由 60 元上調至 72 元 → 本次 72 · 調整前 60 · +20%", tp["current"] == 72 and tp["prior"] == 60 and tp["change_pct"] == 20.0, tp)
    v = r["valuation"][0] if r["valuation"] else {}
    chk("評價法:本益比 → VAL_PE · 20 倍 · 2026 · EPS 3.6 · 隱含 72 → VERIFIED", v.get("method") == "VAL_PE" and v.get("multiple") == 20
        and v.get("basis_year") == 2026 and v.get("check") == "VERIFIED", v)
    # 局部識別
    ident = {"code": "2330", "names": [{"name": "台灣積體電路製造", "source": "alias", **name_forms("台灣積體電路製造股份有限公司")},
                                       {"name": "中國信託金融控股", "source": "alias", **name_forms("中國信託金融控股股份有限公司")}]}
    hits = mentions(["台積電第三季營收創高,台灣股市同步走強。", "中信金獲利穩健,中國市場需求回溫。", "台灣積體電路製造股份有限公司公告。"], ident)
    forms = {h["form"]: h["kind"] for h in hits}
    chk("局部識別:台積電 ← 台灣積體電路製造 · 中信金 ← 中國信託金融控股(依序取字 · 首字相同)", forms.get("台積電") == "partial" and forms.get("中信金") == "partial", forms)
    chk("停用詞不算:「台灣」「中國」不判成公司", "台灣" not in forms and "中國" not in forms, forms)
    chk("全名照收(最長優先)", forms.get("台灣積體電路製造股份有限公司") == "full", forms)
    chk("英文字首縮寫:Taiwan Semiconductor Manufacturing Company → TSMC", name_forms("Taiwan Semiconductor Manufacturing Company")["acronym"] == "TSMC")
    chk("英文單詞形式只認大寫開頭:Delta Electronics → Delta 中 · delta 不中",
        [h["form"] for h in mentions(["Delta guided up; the delta hedge was small."], {"code": "", "names": [{"name": "Delta Electronics", "source": "t", **name_forms("Delta Electronics")}]})] == ["Delta"])
    # 目標價各式
    t = target_prices("Target price NT$4,200 (prev. NT$3,600) implies 25% upside.")
    chk("(prev. A):本次 4,200 · 調整前 3,600", t["current"] == 4200 and t["prior"] == 3600, t)
    t = target_prices("前次投資建議 2025.08.06:目標價125元。本次目標價145元,評等買進。")
    chk("前次目標價 125 不當本次:本次 145 · 調整前 125", t["current"] == 145 and t["prior"] == 125, t)
    t = target_prices("目標價上調至 88 元(原目標價 75 元)。")
    chk("目標價上調至 B 元(原 A 元)", t["current"] == 88 and t["prior"] == 75 and t["direction"] == "up", t)
    t = target_prices("We cut our TP to US$45 from US$52.")
    chk("to B from A(下修)→ down", t["current"] == 45 and t["prior"] == 52 and t["direction"] == "down", t)
    t = target_prices("目標價潛在上漲空間 23%;給予 13x 2026 PER。")
    chk("剔除:目標價後接 %(上漲空間)· 13x(倍數)都不是價格", t["current"] is None and t["prior"] is None, t)
    t = target_prices("We maintain our TP at NT$500.")
    chk("維持:只有本次 → direction maintain", t["current"] == 500 and t["direction"] == "maintain", t)
    # 驗算抓錯 + 表內取指標
    txt = ("Earnings Summary Year to Net Profit Diluted EPS P/E 31 Dec (NT$M) (NT$) (x) 2025E 100 20.0 15.0 2026E 120 25.0 12.0 2027E 130 27.0 11.0\n"
           "Our TP of NT$300 is based on 14x 2026E P/E.")
    r = analyze_text(txt, "XYZ-1234 20251201")
    v = r["valuation"][0] if r["valuation"] else {}
    chk("表內取指標:2026E Diluted EPS 25.0 · 14x → 隱含 350 ≠ 300 → MISMATCH(列出)", r["tables_seen"] >= 1 and v.get("metric_value") == 25.0
        and v.get("implied_tp") == 350.0 and v.get("check") == "MISMATCH", v)
    v2 = valuations("We value the stock on a sum-of-the-parts basis.", [], {"current": 100})
    chk("沒有倍數 / 指標 → UNVERIFIED(未驗,不是錯)· SOTP 照判", v2 and v2[0]["method"] == "VAL_SOTP" and v2[0]["check"] == "UNVERIFIED", v2)
    chk("需語境的詞不算評價句:「NAV per unit」", valuations("Target price aside, the NAV per unit rose.", [], None) == [])
    md = to_markdown(analyze_text(zh, "南亞(1303,B_買進)-CTBC260918"))
    chk("輸出:公司名稱 / 目標價 / 評價法 三張表都用垂直線", md.count("|---|") >= 4 and "| 本次 | 調整前 | 方向 | 調幅% |" in md)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("帶加速器橋 · VIA_FROM_VCGC 閘 · 不匯入 TA-Lib · 不碰網路", "[VIA:ACCEL-BRIDGE" in body and 'os.environ.get("VIA_FROM_VCGC") != "YES"' in body
        and not re.search(r"^\s*(import|from)\s+(" + "ta" + r"lib|requests|urllib)\b", body, re.M))
    print(f"[VRN_ENG396 v0100 研報實體] 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())

