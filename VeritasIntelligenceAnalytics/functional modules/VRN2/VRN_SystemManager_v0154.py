#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0154 — 薄尾:檔名完整擷取邏輯(操作員 2026-10-10)+ VDF 兩份總清單(唯讀)。
  總清單只有兩份(VDF 產):① 全台股清單 ② 主動式台股 ETF 清單
     lists          預設只讀 VDF 公布的清單(契約路徑:lists --use <路徑> 登記,存 VRN_Config)或 VRN 快取 —— 找 / 維護清單是 VDF 的工作(操作員 2026-10-10 暫停 VRN 端搜尋)
     lists --scan   (保留功能)在 VDF 樹找這兩份(檔名 + 內容嗅探:≥800 個四碼 = 全台股;00xxxA ≥3 = 主動 ETF;csv · json · parquet · DuckDB 表皆可,唯讀)
                    → VRN 自家快取 SSOT/VRN_MasterList_v####.json(來源指紋變了才出新版 = 自動更新;VDF 不在時用快取)
  檔名切割(fname 只判檔名,秒級;prep 也改用這套):
     檔名 → 連續中文 · 連續英文 · 連續數字 三種 run
     認領順序:yfinance 形(2330.TW)→ Bloomberg 形(3706 TT / 3014TT)→ 報告日(YYYYMMDD · 民國 1YYMMDD · YYMMDD · CTBC/中信+MMDD)
              → 代號(四碼或 00xxx(A),有清單就以清單為準;年份不算)→ 券商(冊的 aliases,中文可在連續中文裡局部比對,英文要整段;順帶吃掉 投顧/證券/證期/期貨/投信/研究部)
              → 股票名稱(有代號:清單名稱在檔名裡局部比對,可吃簡稱與 -KY;無代號:清單名稱反查,非個股文件不反查)
     剩餘:去掉 代號 · 日期 · 券商 · 名稱 之後剩下的每一段都保留,標類型(評等 · 文件類型 · 期間 · 年份 · 人名? · 數字 · 副本序號 · 其他)→ 留給下一步跟第一頁對照
     券商一律顯示英文簡稱(冊的 abbr;冊沒有才用內建種子,標黃)
     三種代號:代號 · yfinance(上市 .TW / 上櫃 .TWO,主動 ETF .TW)· Bloomberg(<代號> TT)· 名稱 = 清單名稱
  產出:fname → VIA_Reports/vrn/prep/FNAME_MATRIX_latest.html(跳出)+ FNAME_latest.csv + json;prep 的矩陣多「切割」與「剩餘」兩欄
其餘動詞照前版鏈。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
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
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0154"


def _vnum_v0154(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0154(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0154(p) < _vnum_v0154(__file__)), key=_vnum_v0154)
PRIOR = _load_v0154(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _resolve(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return vars(mod)[name]
        mod = vars(mod).get("PRIOR")
    return None


_home, _rep, _vdf_home = PRIOR._home, PRIOR._rep, PRIOR._vdf_home
_ORIG_LOAD_BROKERS, _ORIG_LOAD_ROSTER = PRIOR.load_brokers, PRIOR.load_roster      # 套用前先存原函式(避免自己呼叫自己)

# ───────── 兩份總清單(VDF 唯讀)→ VRN 快取 ─────────
_CODE_KEYS = PRIOR._CODE_KEYS + ("etf代號", "基金代號", "證券代碼", "stock_code", "ticker_tw", "代碼")
_NAME_KEYS = PRIOR._NAME_KEYS + ("etf名稱", "基金名稱", "fund_name", "etf_name", "證券簡稱", "name_cn", "簡稱")
PRIOR._CODE_KEYS, PRIOR._NAME_KEYS = _CODE_KEYS, _NAME_KEYS
_LIST_FILE_RX = re.compile(r"(?i)(stock|list|universe|roster|listing|company|basic|etf|active|instrument|identity|master|ticker|security|證券|股票|上市|上櫃|主動)")
_ACTIVE_RX = re.compile(r"^00\d{3,4}A$")


def _rows_from_duckdb(p: Path, roster: dict, src: str) -> list:
    out = []
    try:
        import duckdb  # noqa: WPS433
        con = duckdb.connect(str(p), read_only=True)
    except Exception:  # noqa: BLE001
        return out
    try:
        for sch, tb in con.execute("select table_schema, table_name from information_schema.tables").fetchall():
            cols = [r[0] for r in con.execute("select column_name from information_schema.columns where table_schema=? and table_name=?", [sch, tb]).fetchall()]
            low = {c.lower(): c for c in cols}
            cc = next((low[k.lower()] for k in _CODE_KEYS if k.lower() in low), None)
            nc = next((low[k.lower()] for k in _NAME_KEYS if k.lower() in low), None)
            if not cc:
                continue
            sel = [cc] + [c for c in (nc, next((low[k.lower()] for k in PRIOR._MKT_KEYS if k.lower() in low), None), next((low[k.lower()] for k in PRIOR._EN_KEYS if k.lower() in low), None)) if c]
            r0 = {}
            for row in con.execute('select %s from "%s"."%s" limit 200000' % (", ".join('"%s"' % c for c in sel), sch, tb)).fetchall():
                d = dict(zip(sel, row))
                PRIOR._add_rec(r0, d.get(cc), d.get(nc, ""), PRIOR._pick(d, PRIOR._EN_KEYS), PRIOR._pick(d, PRIOR._MKT_KEYS), src)
            out.append(("%s#%s.%s" % (p.name, sch, tb), r0))
    except Exception:  # noqa: BLE001
        pass
    finally:
        try:
            con.close()
        except Exception:  # noqa: BLE001
            pass
    return out


def _rows_from_parquet(p: Path, src: str) -> dict:
    r0 = {}
    try:
        import duckdb  # noqa: WPS433
        rel = duckdb.sql("select * from read_parquet('%s') limit 200000" % str(p).replace("'", "''"))
        cols = rel.columns
        for row in rel.fetchall():
            d = dict(zip(cols, row))
            code = PRIOR._pick(d, _CODE_KEYS)
            if code:
                PRIOR._add_rec(r0, code, PRIOR._pick(d, _NAME_KEYS), PRIOR._pick(d, PRIOR._EN_KEYS), PRIOR._pick(d, PRIOR._MKT_KEYS), src)
    except Exception:  # noqa: BLE001
        try:
            import pandas as pd  # noqa: WPS433
            df = pd.read_parquet(p)
            for d in df.head(200000).to_dict("records"):
                code = PRIOR._pick(d, _CODE_KEYS)
                if code:
                    PRIOR._add_rec(r0, code, PRIOR._pick(d, _NAME_KEYS), PRIOR._pick(d, PRIOR._EN_KEYS), PRIOR._pick(d, PRIOR._MKT_KEYS), src)
        except Exception:  # noqa: BLE001
            pass
    return r0


def find_master_lists(paths: list | None = None) -> dict:
    """paths 給定 = 只讀 VDF 公布的清單(契約,預設路);paths=None = 掃 VDF 樹(保留功能,只在 lists --scan 時用;那是 VDF 的工作)。"""
    vdf = _vdf_home()
    cands = []
    if paths is not None:
        cands = [Path(x) for x in paths if Path(x).is_file()]
    elif vdf.is_dir():
        for p in vdf.rglob("*"):
            try:
                if p.is_file() and p.suffix.lower() in (".csv", ".json", ".parquet", ".duckdb", ".db") and _LIST_FILE_RX.search(p.name) and not any(x.startswith(("_superseded", "_quarantine")) for x in p.parts) and p.stat().st_size < 2 * 1024 ** 3:
                    cands.append(p)
            except OSError:
                continue
    cands = sorted(cands, key=lambda q: q.stat().st_mtime, reverse=True)[:150] if paths is None else cands
    scored = []
    for p in cands:
        tables = []
        if p.suffix.lower() in (".duckdb", ".db"):
            tables = _rows_from_duckdb(p, {}, "VDF")
        elif p.suffix.lower() == ".parquet":
            tables = [(p.name, _rows_from_parquet(p, "VDF"))]
        else:
            r0 = {}
            PRIOR._load_table(p, r0, "VDF")
            tables = [(p.name, r0)]
        for label, r0 in tables:
            n4 = sum(1 for c in r0 if re.fullmatch(r"[1-9]\d{3}", c))
            na = sum(1 for c in r0 if _ACTIVE_RX.fullmatch(c))
            named = sum(1 for v in r0.values() if v.get("name"))
            mk = sum(1 for v in r0.values() if v.get("market"))
            if n4 or na:
                scored.append({"label": label, "path": str(p), "mtime": p.stat().st_mtime, "n4": n4, "active": na, "named": named, "market": mk, "rows": r0})
    stock = max((x for x in scored if x["n4"] >= 800), key=lambda x: (x["n4"], x["named"], x["mtime"]), default=None)
    act = max((x for x in scored if x["active"] >= 3 and (re.search(r"(?i)active|主動", x["label"]) or x["active"] >= max(3, x["n4"]))), key=lambda x: (x["active"], x["mtime"]), default=None)
    if act is None:
        act = max((x for x in scored if x["active"] >= 3), key=lambda x: (x["active"], x["mtime"]), default=None)
    return {"stock": stock, "active": act, "candidates": sorted(({k: v for k, v in x.items() if k != "rows"} for x in scored), key=lambda x: -(x["n4"] + x["active"]))[:12], "searched": len(cands)}


def _cache_tail():
    hits = sorted((_home() / "SSOT").glob("VRN_MasterList_v*.json"), key=lambda q: _vnum_v0154(q.stem))
    return hits[-1] if hits else None


def _contract_paths() -> list:
    cfg = (_resolve("config_get") or (lambda: {}))()
    env = [x for x in (os.environ.get("VIA_VRN_MASTER_LISTS") or "").split(";") if x.strip()]
    return env or list(cfg.get("master_lists") or [])


def master_lists(refresh: bool = True, use_vdf: bool = True, scan: bool = False) -> dict:
    """回傳 {code: {name, en, market, kind(stock|active_etf), src}};來源 live(VDF 公布的清單)/ cache(VRN 快取)/ none。
    預設不掃 VDF 樹(VDF 的工作):只讀契約路徑(lists --use 登記)或快取;scan=True 才掃(保留)。"""
    paths = None if scan else _contract_paths()
    empty = {"stock": None, "active": None, "candidates": [], "searched": 0}
    found = find_master_lists(paths) if (refresh and use_vdf and (scan or paths)) else empty
    tail = _cache_tail()
    cache = json.loads(tail.read_text(encoding="utf-8")) if tail else None
    if found["stock"] or found["active"]:
        entries = {}
        for kind, x in (("stock", found["stock"]), ("active_etf", found["active"])):
            if not x:
                continue
            for c, v in x["rows"].items():
                if (kind == "stock" and re.fullmatch(r"[1-9]\d{3}|00\d{2,4}[A-Z]?", c)) or (kind == "active_etf" and _ACTIVE_RX.fullmatch(c)):
                    e = entries.setdefault(c, {"name": v.get("name", ""), "en": v.get("en", ""), "market": v.get("market", ""), "kind": "active_etf" if _ACTIVE_RX.fullmatch(c) else kind})
                    for k in ("name", "en", "market"):
                        if not e[k] and v.get(k):
                            e[k] = v[k]
        srcs = [{"kind": k, "file": x["label"], "path": x["path"], "mtime": datetime.datetime.fromtimestamp(x["mtime"]).isoformat(timespec="seconds"), "codes": x["n4"] if k == "stock" else x["active"], "named": x["named"], "market": x["market"]} for k, x in (("stock", found["stock"]), ("active_etf", found["active"])) if x]
        fp = hashlib.sha256(json.dumps(entries, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]
        if not cache or cache.get("fingerprint") != fp:
            nv = "v%04d" % ((_vnum_v0154(tail.stem) + 1) if tail else 100)
            (_home() / "SSOT").mkdir(parents=True, exist_ok=True)
            newp = _home() / "SSOT" / ("VRN_MasterList_%s.json" % nv)
            newp.write_text(json.dumps({"schema": "VIA.VRN.MasterList.v1", "version": nv, "prior": tail.name if tail else None, "ts": datetime.datetime.now().isoformat(timespec="seconds"), "fingerprint": fp, "rule": "VDF 兩份總清單(全台股 · 主動式台股 ETF)的 VRN 唯讀快取;來源變了才出新版", "sources": srcs, "entries": entries}, ensure_ascii=False, indent=1), encoding="utf-8")
            cache_name, updated = newp.name, True
        else:
            cache_name, updated = tail.name, False
        return {"entries": entries, "origin": "live", "sources": srcs, "cache": cache_name, "updated": updated, "candidates": found["candidates"], "searched": found["searched"]}
    if cache:
        return {"entries": cache.get("entries", {}), "origin": "cache", "sources": cache.get("sources", []), "cache": tail.name, "updated": False, "candidates": found["candidates"], "searched": found["searched"]}
    return {"entries": {}, "origin": "none", "sources": [], "cache": None, "updated": False, "candidates": found["candidates"], "searched": found["searched"]}


# ───────── 檔名切割 ─────────
_RUN_RX = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]+|[A-Za-z]+|\d+")
_SEED_ABBR = {"Goldman Sachs": "GS", "Morgan Stanley": "MS", "UBS": "UBS", "Citi": "Citi", "Daiwa": "Daiwa", "J.P. Morgan": "JPM", "CLSA": "CLSA", "Macquarie": "MQ", "GF Securities": "GF",
              "兆豐": "MEGA", "華南": "HNS", "群益": "CSC", "統一": "PSC", "國泰": "CT", "中信": "CTBC", "凱基": "KGI", "台新": "TSC", "元大": "YT", "富邦": "FB", "永豐": "SJP",
              "高盛": "GS", "摩根士丹利": "MS", "瑞銀": "UBS", "花旗": "Citi", "大和": "Daiwa", "摩根大通": "JPM", "里昂": "CLSA", "里昂證券": "CLSA", "麥格理": "MQ", "廣發": "GF"}
_BROKER_SUFFIX = ("研究部", "投顧", "證券", "證期", "期貨", "投信", "研究")
_RATING_SEED = ["強力買進", "初次評等", "增加持股", "降低持股", "未評等", "區間操作", "維持", "買進", "中立", "賣出", "持有", "評等", "NR", "OW", "UW", "Buy", "Sell", "Hold", "Neutral", "Overweight", "Underweight", "Outperform", "Underperform", "Note", "N", "B"]
_DOCTYPE_SEED = ["個股介紹報告", "個股報告", "訪談速報", "晨會報告", "盤後分析", "投資早報", "產業專題", "專題報告", "總經評析", "籌碼追蹤", "盤勢分析", "盤勢重點", "市場觀察家", "日股分析", "美股分析", "港股分析", "晨間解盤", "論壇", "周報", "週報", "早報", "Memo", "Takeaway", "update", "Thoughts", "Monthly", "Databook", "Summit", "Insights"]


def _ratings() -> list:
    words = list(_RATING_SEED)
    for p in sorted((_home() / "knowledge").glob("VRN_Rating_Dict_v*.json"))[-1:]:
        try:
            d = json.loads(p.read_text(encoding="utf-8-sig"))

            def walk(o):
                if isinstance(o, dict):
                    for k, v in o.items():
                        if isinstance(k, str) and 1 <= len(k) <= 8:
                            words.append(k)
                        walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
                elif isinstance(o, str) and 1 <= len(o) <= 8:
                    words.append(o)
            walk(d)
        except (OSError, ValueError):
            pass
    return sorted({w for w in words if w and not re.fullmatch(r"[\d.]+", w)}, key=len, reverse=True)


def _abbr_of(book: dict, canon: str) -> tuple:
    """券商一律英文簡稱:冊 abbr → 同別名在冊裡其他條的 abbr → 種子 → 英文別名;都沒有才回空(標黃),絕不回中文。"""
    e = book.get(canon) or {}
    if e.get("abbr"):
        return e["abbr"], "冊"
    al2ab = {}
    for c2, e2 in book.items():
        if e2.get("abbr"):
            for a in e2.get("aliases", {}):
                al2ab.setdefault(a.lower(), e2["abbr"])
            al2ab.setdefault(c2.lower(), e2["abbr"])
    for a in sorted(e.get("aliases", {}), key=len):
        if a.lower() in al2ab:
            return al2ab[a.lower()], "冊(同別名)"
    for key in [canon] + sorted(e.get("aliases", {}), key=len):
        if key in _SEED_ABBR:
            return _SEED_ABBR[key], "種子"
    for a in sorted(e.get("aliases", {}), key=len):
        if a.isascii() and re.fullmatch(r"[A-Za-z][A-Za-z.&]{1,9}", a):
            return a, "英文別名"
    return (canon if canon.isascii() else ""), "—"


def load_brokers_v154() -> tuple:
    book, used = _ORIG_LOAD_BROKERS()
    for p in sorted(set(list((_home() / "knowledge").glob("VRN_Broker_Dict_v*.json")) + list(_home().glob("VRN_Broker_Dict_v*.json")))):
        try:
            d = json.loads(p.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        for sec in (v for v in (d.values() if isinstance(d, dict) else []) if isinstance(v, dict)):
            for canon, ent in sec.items():
                if isinstance(ent, dict) and isinstance(ent.get("abbr"), str) and ent["abbr"].strip() and canon in book:
                    book[canon].setdefault("abbr", ent["abbr"].strip())
    return book, used


def _date_claim(s: str, mtime: float):
    """回傳 (日期, 來源, span) 或 None;只認第一個合法的。"""
    pats = [(r"(?<!\d)(20\d{2})([-_.]?)(\d{2})\2(\d{2})(?!\d)", "YYYYMMDD", lambda m: (m.group(1), m.group(3), m.group(4))),
            (r"(?<!\d)(1[01]\d)(\d{2})(\d{2})(?!\d)", "民國 1YYMMDD", lambda m: (int(m.group(1)) + 1911, m.group(2), m.group(3))),
            (r"(?<!\d)(\d{2})(\d{2})(\d{2})(?!\d)", "YYMMDD", lambda m: (2000 + int(m.group(1)), m.group(2), m.group(3)) if 15 <= int(m.group(1)) <= 35 else (0, 0, 0)),
            (r"(?:(?<=CTBC)|(?<=中信))(\d{2})(\d{2})(?!\d)", "CTBC+MMDD(年取檔案時間)", lambda m: (datetime.date.fromtimestamp(mtime or time.time()).year, m.group(1), m.group(2)))]
    for rx, src, f in pats:
        for m in re.finditer(rx, s):
            y, mo, d = f(m)
            dt = PRIOR._valid_date(y, mo, d) if y else None
            if dt:
                return dt.isoformat(), "檔名 " + src, m.span()
    return None


def fname_parse(fn: str, master: dict, book: dict, mtime: float = 0.0, ratings: list | None = None) -> dict:
    s = Path(fn).stem
    claims = []

    def free(a, b):
        return all(b <= x[0] or a >= x[1] for x in claims)

    def claim(a, b, t, lab=""):
        claims.append((a, b, t, lab or t))
    out = {"code": "", "code_src": "", "market": "", "yf": "", "bbg": "", "name": "", "name_check": "", "name_file": "", "broker": "", "broker_canon": "", "broker_alias": "", "broker_src": "", "abbr_src": "",
           "date": "", "date_src": "", "kind_list": "", "code_unlisted": ""}
    m = re.search(r"\s*[\(（](\d{1,2})[\)）]\s*$", s)
    if m:
        claim(m.start(), m.end(), "copy", "副本序號")
    m = re.search(r"(?<![\dA-Za-z])(\d{4,6}[A-Z]?)\.(TWO|TW)(?![A-Za-z])", s, re.I)
    if m:
        claim(*m.span(1), "code")
        claim(m.span(1)[1], m.end(), "yfx", ".%s" % m.group(2).upper())
        out.update(code=m.group(1).upper(), code_src="檔名 yfinance 形", market="TPEx" if m.group(2).upper() == "TWO" else "TWSE")
    if not out["code"]:
        m = re.search(r"(?<![\d])(\d{4,6}[A-Z]?)\s?(TT)(?![A-Za-z])", s)
        if m and free(*m.span()):
            claim(*m.span(1), "code")
            claim(*m.span(2), "bbgx", "TT")
            out.update(code=m.group(1), code_src="檔名 Bloomberg 形")
    dc = _date_claim(s, mtime)
    if dc and free(*dc[2]):
        claim(*dc[2], "date")
        out.update(date=dc[0], date_src=dc[1])
    if not out["code"]:
        unl = []
        for m in re.finditer(r"(?<![\dA-Za-z.])(00\d{3,4}[A-Z]?|[1-9]\d{3})(?!\d)", s):
            if not free(*m.span()):
                continue
            c = m.group(1)
            if s[m.end():m.end() + 1] == "年" or (re.fullmatch(r"(19|20)\d{2}", c) and c not in master):
                continue
            if master and c not in master:
                unl.append(c)
                continue
            claim(*m.span(), "code")
            out.update(code=c, code_src="檔名代號" + (" · 清單 ✓" if master else "(無清單可驗)"))
            break
        if not out["code"] and unl:
            out["code_unlisted"] = unl[0]
    def claim_name(nm: str, how: str) -> bool:
        cands = [nm, nm.replace("-KY", ""), nm.replace("-KY", "").replace("KY", "")]
        base = nm.replace("-KY", "").replace("*", "")
        cands += [base[:k] for k in range(len(base) - 1, 1, -1)] if re.fullmatch(r"[\u4e00-\u9fff]+", base) else []
        for v in [x for i, x in enumerate(cands) if x and len(x) >= 2 and x not in cands[:i]]:
            flags = re.I if v.isascii() else 0
            rx = (r"(?<![A-Za-z])" + re.escape(v) + r"(?![a-z])") if v.isascii() else re.escape(v)
            for mm in re.finditer(rx, s, flags):
                a, b = mm.span()
                if not free(a, b):
                    continue
                ext = 0
                while b < len(s) and ext < 3 and re.match(r"[\u4e00-\u9fff]", s[b]) and free(b, b + 1) and v != nm:
                    b += 1
                    ext += 1
                k = re.match(r"\s?-?KY", s[b:])
                if k and free(b, b + k.end()):
                    b += k.end()
                claim(a, b, "name")
                out["name_file"] = s[a:b]
                out["name_check"] = how + ("" if v == nm else "(簡稱/變體)")
                return True
        return False
    def claim_broker():
        best = None
        for canon, e in book.items():
            for a, src in e["aliases"].items():
                if len(a) < 2:
                    continue
                for mm in re.finditer(PRIOR._alias_rx(a), s, flags=re.I if a.isascii() else 0):
                    if free(*mm.span()) and (best is None or len(a) > best[0] or (len(a) == best[0] and mm.start() < best[1])):
                        best = (len(a), mm.start(), mm.end(), canon, a, src)
        if best:
            a0, b0 = best[1], best[2]
            grown = True
            while grown:
                grown = False
                for suf in _BROKER_SUFFIX:
                    if s.startswith(suf, b0) and free(b0, b0 + len(suf)):
                        b0 += len(suf)
                        grown = True
                        break
            claim(a0, b0, "broker")
            ab, asrc = _abbr_of(book, best[3])
            out.update(broker=ab, broker_canon=best[3], broker_alias=best[4], broker_src=best[5], abbr_src=asrc)

    nonstock = _resolve("_nonstock_type") or (lambda n: "")
    if not out["code"]:
        claim_broker()          # 無代號:先認券商,再反查名稱(「統一投顧」不誤中統一 1216)
    if out["code"]:
        ent = master.get(out["code"]) or {}
        out.update(kind_list={"stock": "全台股", "active_etf": "主動 ETF"}.get(ent.get("kind", ""), "清單無" if master else ""))
        if ent.get("name"):
            out["name"] = ent["name"]
            if not claim_name(ent["name"], "✓"):
                out["name_check"] = "檔名無名稱(清單 %s)" % ent["name"]
        if not out["market"]:
            out["market"] = ent.get("market", "") or ("TWSE" if ent.get("kind") == "active_etf" else "")
    elif master and not nonstock(fn):
        hits = []
        for c, ent in master.items():
            nm = ent.get("name", "")
            if len(nm.replace("-KY", "")) >= 2 and re.search(r"[\u4e00-\u9fff]", nm):
                for v in (nm, nm.replace("-KY", "")):
                    for mm in re.finditer(re.escape(v), s):
                        if free(*mm.span()):
                            hits.append((len(v), c, v))
        if not hits:
            toks = [(mm.group(), mm.span()) for mm in re.finditer(r"[A-Za-z]{4,}", s) if free(*mm.span())]
            first = {}
            for c, ent in master.items():
                w = re.split(r"[\s,.\-]+", (ent.get("en") or "").strip())
                if w and len(w[0]) >= 4:
                    first.setdefault(w[0].lower(), c)
                if ent.get("name", "").isascii() and len(ent.get("name", "").replace("-KY", "")) >= 4:
                    first.setdefault(ent["name"].replace("-KY", "").lower(), c)
            for t, sp in toks:
                if t.lower() in first:
                    hits.append((len(t), first[t.lower()], t))
        if hits:
            n, c, v = max(hits)
            ent = master[c]
            out.update(code=c, code_src="清單反查(%s)" % v, name=ent.get("name", ""), market=ent.get("market", "") or ("TWSE" if ent.get("kind") == "active_etf" else ""), kind_list={"stock": "全台股", "active_etf": "主動 ETF"}.get(ent.get("kind", ""), ""))
            claim_name(v, "反查") or claim_name(ent.get("name", ""), "反查")
    if out["code"] and not out["broker"]:
        claim_broker()          # 有代號:清單名稱先認(ETF「主動統一…」的統一不被當券商),再認券商
    if out["code"] and not out["name"]:
        for rx in (PRIOR._NAME_BEFORE, PRIOR._NAME_AFTER, PRIOR._NAME_AFTER_EN):
            mm = rx.search(s)
            if mm and free(*mm.span(1)):
                claim(*mm.span(1), "name")
                out.update(name_file=mm.group(1), name=mm.group(1), name_check="只有檔名(清單無此代號)" if master else "只有檔名(無清單)")
                break
    if out["code"]:
        out["yf"] = out["code"] + {"TWSE": ".TW", "TPEx": ".TWO"}.get(out["market"], "")
        out["bbg"] = out["code"] + " TT"
    for mm in re.finditer(r"\d[QH]\d{2}|[QH][1-4]\d{0,2}(?![A-Za-z])|\d{1,2}月", s):
        if free(*mm.span()):
            claim(*mm.span(), "rem", "期間")
    for mm in re.finditer(r"[+\-]?\d+\.\d+%?|[+\-]\d+%?|\d+%", s):
        if free(*mm.span()):
            claim(*mm.span(), "rem", "數字")
    rts = ratings if ratings is not None else _ratings()
    rem = []
    for mm in _RUN_RX.finditer(s):
        a, b = mm.span()
        segs, pos = [], a
        for x in sorted(c for c in claims if c[0] < b and c[1] > a):
            if x[0] > pos:
                segs.append((pos, x[0]))
            pos = max(pos, x[1])
        if pos < b:
            segs.append((pos, b))
        for a2, b2 in segs:
            t = s[a2:b2]
            if not t.strip():
                continue
            lab = "其他"
            if t.isdigit():
                lab = "年份" if (len(t) == 4 and s[b2:b2 + 1] == "年") else "數字"
            elif any((r == t) if r.isascii() else (r in t) for r in rts) and (not t.isascii() or t in rts):
                lab = "評等"
            elif any((d.lower() == t.lower()) if d.isascii() else (d in t) for d in _DOCTYPE_SEED):
                lab = "文件類型"
            elif re.fullmatch(r"[\u4e00-\u9fff]{2,3}", t) and (a2 == 0 or not re.match(r"[\u4e00-\u9fff]", s[a2 - 1])) and (b2 == len(s) or not re.match(r"[\u4e00-\u9fff]", s[b2])) and re.search(r"[_\s\-]|^", s[max(0, a2 - 1):a2] or "^") and re.search(r"[_\s\-]|$", s[b2:b2 + 1] or "$"):
                lab = "人名?"
            claim(a2, b2, "rem", lab)
            rem.append((t, lab))
    for x in sorted(claims):
        if x[2] == "rem" and x[3] in ("期間", "數字") and (s[x[0]:x[1]], x[3]) not in rem:
            rem.append((s[x[0]:x[1]], x[3]))
    chips = []
    pos = 0
    for x in sorted(claims):
        if x[0] < pos:
            continue
        if x[0] > pos and s[pos:x[0]].strip():
            chips.append((s[pos:x[0]], "sep", ""))
        chips.append((s[x[0]:x[1]], x[2], x[3]))
        pos = x[1]
    if pos < len(s) and s[pos:].strip():
        chips.append((s[pos:], "sep", ""))
    out["chips"] = chips
    out["remainder_tokens"] = rem
    out["remainder"] = " · ".join(t for t, _ in rem)
    out["runs"] = len(_RUN_RX.findall(s))
    return out


def _parse_date_v154(name: str, mtime: float) -> tuple:
    dc = _date_claim(Path(name).stem, mtime)
    return (dc[0], dc[1]) if dc else (datetime.date.fromtimestamp(mtime or time.time()).isoformat(), "檔案時間(非報告日)")


_ML_CACHE = {}


def _parse_name_fields_v154(name: str, roster: dict, book: dict) -> dict:
    f = fname_parse(name, roster, book, ratings=_ML_CACHE.get("ratings"))
    return f


def _load_roster_v154(use_vdf: bool = True) -> tuple:
    ml = master_lists(refresh=True, use_vdf=use_vdf)
    _ML_CACHE["ml"] = ml
    _ML_CACHE["ratings"] = _ratings()
    used = [{"file": x["file"], "sys": "VDF(唯讀)·%s" % ("全台股" if x["kind"] == "stock" else "主動ETF"), "added": x["codes"]} for x in ml["sources"]]
    if ml["origin"] == "cache":
        used = [{"file": ml["cache"], "sys": "VRN 快取(VDF 不在)", "added": len(ml["entries"])}]
    if ml["origin"] == "none":
        r, u = _ORIG_LOAD_ROSTER(False)
        return r, [dict(x, sys="VRN 備援(找不到 VDF 總清單)") for x in u]
    return ml["entries"], used


def _lamp_notes(r: dict) -> list:
    y = []
    if str(r.get("date_src", "")).startswith("檔案時間"):
        y.append("報告日用檔案時間")
    if not r.get("broker_canon"):
        y.append("券商未判出")
    elif not r.get("broker", "").isascii() or r.get("abbr_src") == "—":
        y.append("券商無英文簡稱(補 Broker_Dict abbr)")
    elif r.get("abbr_src") in ("種子", "英文別名") or r.get("broker_src") != "冊":
        y.append("券商英文簡稱冊未收")
    if not r.get("kind"):
        if not r.get("code"):
            y.append("個股代號未判出" + ("(檔名有 %s 但清單無)" % r["code_unlisted"] if r.get("code_unlisted") else ""))
        else:
            if not r.get("yf", "").endswith((".TW", ".TWO")):
                y.append("市場別未知(.TW/.TWO 待定)")
            if str(r.get("name_check", "")).startswith(("檔名無名稱", "只有檔名")):
                y.append(r["name_check"])
    return y


def fname_run(d: Path, use_vdf: bool = True) -> dict:
    now = datetime.datetime.now()
    rep = _rep() / "prep"
    rep.mkdir(parents=True, exist_ok=True)
    master, used = _load_roster_v154(use_vdf)
    ml = _ML_CACHE.get("ml", {})
    book, bsrc = load_brokers_v154()
    rts = _ML_CACHE.get("ratings") or _ratings()
    nonstock = _resolve("_nonstock_type") or (lambda n: "")
    files = sorted(p for p in d.rglob("*") if p.is_file() and not p.name.startswith("~$")) if d.is_dir() else []
    rows = []
    for p in files:
        mt = p.stat().st_mtime
        f = fname_parse(p.name, master, book, mt, rts)
        if not f["date"]:
            f["date"], f["date_src"] = datetime.date.fromtimestamp(mt).isoformat(), "檔案時間(非報告日)"
        r = dict(f, file=p.name, path=str(p), ext=p.suffix.lower(), kb=round(p.stat().st_size / 1024, 1), type=p.suffix.lower().lstrip(".").upper(), kind=nonstock(p.name) if not f["code"] else "")
        notes = _lamp_notes(r)
        r["notes"] = notes
        r["lamp"] = "YELLOW" if notes else "GREEN"
        rows.append(r)
    stock = [r for r in rows if not r["kind"]]
    s = {"ts": now.isoformat(timespec="seconds"), "dir": str(d), "files": len(rows), "date_from_name": sum(1 for r in rows if r["date_src"].startswith("檔名")), "stock_reports": len(stock), "with_code": sum(1 for r in stock if r["code"]),
         "with_yf": sum(1 for r in stock if r["yf"].endswith((".TW", ".TWO"))), "with_name": sum(1 for r in stock if r["name"]), "broker": sum(1 for r in rows if r["broker"]), "broker_book": sum(1 for r in rows if r["broker"] and r["abbr_src"] == "冊" and r["broker_src"] == "冊"),
         "remainder": sum(1 for r in rows if r["remainder"]), "nonstock": len(rows) - len(stock), "lamps": dict(Counter(r["lamp"] for r in rows)), "master_origin": ml.get("origin", "none"), "master_sources": ml.get("sources", []), "master_cache": ml.get("cache"),
         "master_updated": ml.get("updated", False), "master_n": len(master), "candidates": ml.get("candidates", []), "searched": ml.get("searched", 0), "roster_src": used, "brokers": len(book)}
    (rep / "FNAME_latest.json").write_text(json.dumps({"summary": s, "rows": rows}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    cols = ["lamp", "file", "date", "date_src", "code", "code_src", "yf", "bbg", "name", "name_check", "broker", "broker_canon", "broker_alias", "remainder", "kind", "notes"]
    with (rep / "FNAME_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(dict(r, notes=";".join(r["notes"])))
    page = rep / "FNAME_MATRIX_latest.html"
    page.write_text(_matrix_html(s, rows, names_only=True), encoding="utf-8")
    lamp = "YELLOW" if s["lamps"].get("YELLOW") else ("GREEN" if rows else "GRAY")
    return {"verb": "fname", "summary": s, "rows": rows, "html": str(page), "lamp": lamp}


_CHIP = {"date": "#dbeafe", "code": "#ede9fe", "yfx": "#ede9fe", "bbgx": "#ede9fe", "broker": "#ffedd5", "name": "#dcfce7", "copy": "#f3f4f6", "rem": "#f9fafb", "sep": "transparent"}
_CHIP_ZH = {"date": "報告日", "code": "代號", "yfx": "yfinance 尾", "bbgx": "Bloomberg 尾", "broker": "券商", "name": "名稱", "copy": "副本序號"}


def _matrix_html(s: dict, rows: list, names_only: bool = False) -> str:
    e = html.escape
    L = {"GREEN": "var(--lamp-green,#16a34a)", "YELLOW": "var(--lamp-yellow,#eab308)", "RED": "var(--lamp-red,#dc2626)", "GRAY": "var(--lamp-gray,#9ca3af)"}
    order = {"RED": 0, "YELLOW": 1, "GREEN": 2, "GRAY": 3}

    def lp(l):
        return "<i class='lp %s' style='background:%s'></i>" % (l, L.get(l, "#9ca3af"))

    def chips(r):
        out = []
        for t, ty, lab in r.get("chips", []):
            if ty == "sep":
                out.append("<span class='sep'>%s</span>" % e(t))
            else:
                tip = _CHIP_ZH.get(ty, lab)
                out.append("<span class='ch' style='background:%s;%s' title='%s'>%s</span>" % (_CHIP.get(ty, "#f3f4f6"), "border:1px dashed #d1d5db" if ty == "rem" else "", e(tip), e(t)))
        return "".join(out)

    def remtd(r):
        return " ".join("<span class='rt'>%s<sub>%s</sub></span>" % (e(t), e(l)) for t, l in r.get("remainder_tokens", [])) or "<span class='d'>—</span>"
    pct = lambda a, b: ("%.0f%%" % (100.0 * a / b)) if b else "—"  # noqa: E731
    trs = []
    for r in sorted(rows, key=lambda x: (order.get(x.get("lamp"), 9), x["file"])):
        extra = "" if names_only else "<td class='n'>%s</td><td class='d'>%s</td><td class='d'>%s</td><td class='d'>%s</td>" % (r.get("kb", ""), e(r.get("spec", "")), e(r.get("convert", "") or r.get("convert_err", "") or "—"), e(r.get("read", "")))
        code_cell = e(r.get("code") or ("n/a · " + r["kind"] if r.get("kind") else "—"))
        trs.append("<tr data-l='%s'><td>%s</td><td class='f' title='%s'>%s</td><td class='cut'>%s</td><td>%s<div class='d'>%s</div></td><td>%s<div class='d'>%s</div></td><td>%s</td><td>%s</td><td>%s<div class='d'>%s</div></td><td><b>%s</b><div class='d'>%s</div></td><td class='rem'>%s</td>%s<td class='d'>%s</td></tr>" % (
            r.get("lamp", "GRAY"), lp(r.get("lamp", "GRAY")), e(r.get("path", "")), e(r["file"]), chips(r), e(r.get("date", "") or "—"), e(r.get("date_src", "")), code_cell, e(r.get("code_src", "") + (" · " + r["kind_list"] if r.get("kind_list") else "")),
            e(r.get("yf", "") or "—"), e(r.get("bbg", "") or "—"), e(r.get("name", "") or "—"), e(r.get("name_check", "")), e(r.get("broker", "") or "—"), e((r.get("broker_canon", "") + " · " + r.get("broker_alias", "")) if r.get("broker") else ""), remtd(r), extra, e(";".join(r.get("notes", [])))))
    srcs = s.get("master_sources") or []
    ml_txt = " · ".join("%s %s(%s 碼 · 名 %s · 市場別 %s · %s)" % ("全台股" if x["kind"] == "stock" else "主動ETF", x["file"], x["codes"], x.get("named", "?"), x.get("market", "?"), x.get("mtime", "")) for x in srcs) or "沒找到"
    ml_lamp = "GREEN" if len(srcs) == 2 and s.get("master_origin") == "live" else ("YELLOW" if srcs or s.get("master_origin") == "cache" else "RED")
    cards = [("檔", s["files"], "非個股 %d" % s["nonstock"]), ("報告日來自檔名", pct(s["date_from_name"], s["files"]), "%d 檔" % s["date_from_name"]), ("個股報告", s["stock_reports"], ""),
             ("代號", pct(s["with_code"], s["stock_reports"]), "%d 檔" % s["with_code"]), ("yfinance", pct(s["with_yf"], s["stock_reports"]), "%d 檔" % s["with_yf"]), ("名稱", pct(s["with_name"], s["stock_reports"]), "%d 檔" % s["with_name"]),
             ("券商(英文簡稱)", pct(s["broker"], s["files"]), "冊內 %d" % s["broker_book"]), ("剩餘待對照", s["remainder"], "留給第一頁對照")]
    card_html = "".join("<div class='card'><div class='k'>%s</div><div class='v'>%s</div><div class='d'>%s</div></div>" % (e(k), e(str(v)), e(str(d))) for k, v, d in cards)
    cand = "".join("<tr><td class='d'>%s</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td></tr>" % (e(c["label"]), c["n4"], c["active"], c["named"], c["market"]) for c in s.get("candidates", [])[:8])
    css = ("body{font-family:'Microsoft JhengHei UI','Segoe UI',Arial;font-size:12px;color:#1f2937;background:var(--bg,#fafafa);margin:0;padding:12px}h1{font-size:16px;margin:0 0 4px}.meta{color:#6b7280;font-size:11px;margin-bottom:6px}"
           ".cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:6px;margin:6px 0 8px}.card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:6px 8px}.card .k{color:#6b7280;font-size:11px}.card .v{font-size:17px;font-weight:700}"
           ".ml{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:6px 8px;margin-bottom:8px}.bar button{font-size:11px;margin-right:4px;padding:2px 8px;border:1px solid #d1d5db;background:#fff;border-radius:6px;cursor:pointer}.wrap{overflow-x:auto}"
           "table{border-collapse:collapse;width:100%;background:#fff}th,td{border:1px solid #eceff3;padding:2px 5px;text-align:left;vertical-align:top}th{background:#111827;color:#fff;position:sticky;top:0;font-weight:600}td.n{text-align:right}td.f{max-width:220px;word-break:break-all}"
           ".d{color:#6b7280;font-size:10.5px}.lp{display:inline-block;width:11px;height:11px;border-radius:50%;vertical-align:middle;margin-right:3px}.lp.RED{animation:bl 2.4s ease-in-out infinite}@keyframes bl{0%,100%{opacity:1}50%{opacity:.25}}"
           ".cut{min-width:240px}.ch{display:inline-block;border-radius:4px;padding:0 3px;margin:1px 1px}.sep{color:#9ca3af}.rem .rt{display:inline-block;background:#f9fafb;border:1px dashed #d1d5db;border-radius:4px;padding:0 3px;margin:1px}.rt sub{color:#9ca3af;font-size:9px;margin-left:2px}"
           ".legend span{display:inline-block;border-radius:4px;padding:0 5px;margin-right:4px;font-size:11px}")
    js = "function f(l){document.querySelectorAll('tbody.m tr').forEach(function(t){t.style.display=(!l||t.dataset.l===l)?'':'none'})}"
    head = "<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>VRN 檔名擷取矩陣</title><style>" + css + "</style><script>" + js + "</script></head><body>"
    legend = "".join("<span style='background:%s'>%s</span>" % (_CHIP[k], v) for k, v in (("date", "報告日"), ("code", "代號"), ("broker", "券商"), ("name", "名稱"))) + "<span style='background:#f9fafb;border:1px dashed #d1d5db'>剩餘(標類型)</span>"
    extra_th = "" if names_only else "<th>KB</th><th>規格</th><th>轉換</th><th>讀取</th>"
    return head + ("<h1>VRN 檔名完整擷取 · 切割 → 認領(日期 · 代號 · 券商 · 名稱)→ 剩餘留待第一頁對照</h1><div class='meta'>%s · 夾 %s · 燈 %s</div>"
                   "<div class='ml'>%s <b>總清單</b>(VDF 唯讀 → VRN 快取 %s%s):%s · 合計 %d 碼 · 搜尋 %d 檔"
                   "<table style='margin-top:4px'><thead><tr><th>候選</th><th>四碼</th><th>主動ETF</th><th>有名稱</th><th>有市場別</th></tr></thead><tbody>%s</tbody></table></div>"
                   "<div class='cards'>%s</div><div class='meta legend'>切割色:%s</div>"
                   "<div class='bar'><button onclick=\"f('')\">全部</button><button onclick=\"f('YELLOW')\">只看黃</button><button onclick=\"f('GREEN')\">只看綠</button><button onclick=\"f('RED')\">只看紅</button></div>"
                   "<div class='wrap'><table><thead><tr><th>燈</th><th>檔名</th><th>切割</th><th>報告日</th><th>代號</th><th>yfinance</th><th>Bloomberg</th><th>名稱</th><th>券商</th><th>剩餘(對照第一頁)</th>%s<th>備註</th></tr></thead><tbody class='m'>%s</tbody></table></div>"
                   "<div class='meta' style='margin-top:8px'>綠 = 日期來自檔名 · 券商英文簡稱在冊 ·(個股)代號在清單 · yfinance 有 .TW/.TWO · 名稱對得上;黃 = 其中有缺或來源弱;非個股文件代號欄 n/a 不算缺。剩餘的每一段都保留並標類型,下一步跟第一頁對照。</div></body></html>") % (
        e(s["ts"]), e(s["dir"]), " · ".join("%s%s %d" % (lp(k), k, v) for k, v in sorted(s.get("lamps", {}).items(), key=lambda kv: order.get(kv[0], 9))),
        lp(ml_lamp), e(s.get("master_cache") or "無"), " · 本次更新" if s.get("master_updated") else "", e(ml_txt), s.get("master_n", 0), s.get("searched", 0), cand, card_html, legend, extra_th, "".join(trs))


def _prep_html_v154(man: dict) -> str:
    s0, rows = man["summary"], man["rows"]
    ml = _ML_CACHE.get("ml", {})
    stock = [r for r in rows if r.get("type") != "不支援" and not r.get("kind")]
    for r in rows:
        if r.get("type") != "不支援":
            r.setdefault("chips", [])
    s = {"ts": s0["ts"], "dir": s0["dir"], "files": s0["files"], "nonstock": s0.get("nonstock", 0), "date_from_name": s0.get("date_from_name", 0), "stock_reports": len(stock), "with_code": sum(1 for r in stock if r.get("code")),
         "with_yf": sum(1 for r in stock if str(r.get("yf", "")).endswith((".TW", ".TWO"))), "with_name": sum(1 for r in stock if r.get("name")), "broker": sum(1 for r in rows if r.get("broker")), "broker_book": sum(1 for r in rows if r.get("broker") and r.get("abbr_src") == "冊" and r.get("broker_src") == "冊"),
         "remainder": sum(1 for r in rows if r.get("remainder")), "lamps": s0.get("lamps", {}), "master_origin": ml.get("origin", "none"), "master_sources": ml.get("sources", []), "master_cache": ml.get("cache"), "master_updated": ml.get("updated", False),
         "master_n": len(ml.get("entries", {})), "candidates": ml.get("candidates", []), "searched": ml.get("searched", 0)}
    return _matrix_html(s, rows, names_only=False)


# 套進前版 prep:日期 · 名稱欄位 · 名冊 · 券商 · 矩陣(只換函式,不複製 prep 本體)
PRIOR.parse_date = _parse_date_v154
PRIOR.parse_name_fields = _parse_name_fields_v154
PRIOR.load_roster = _load_roster_v154
PRIOR.load_brokers = load_brokers_v154
PRIOR._prep_html = _prep_html_v154


def _print_fname(o: dict) -> None:
    s = o["summary"]
    print("[計] VRN fname · 檔 %d · 報告日來自檔名 %d · 個股 %d(代號 %d · yfinance %d · 名稱 %d)· 非個股 %d · 券商 %d(冊內簡稱 %d)· 剩餘待對照 %d · %s" % (s["files"], s["date_from_name"], s["stock_reports"], s["with_code"], s["with_yf"], s["with_name"], s["nonstock"], s["broker"], s["broker_book"], s["remainder"], o["lamp"]))
    srcs = s["master_sources"]
    print("[計] 總清單 · 來源 %s · 快取 %s%s · %d 碼 · %s" % (s["master_origin"], s["master_cache"] or "無", "(本次更新)" if s["master_updated"] else "", s["master_n"], " · ".join("%s=%s(%s 碼 · 市場別 %s)" % ("全台股" if x["kind"] == "stock" else "主動ETF", x["file"], x["codes"], x.get("market", "?")) for x in srcs) or "沒找到"))
    if len(srcs) < 2:
        for c in s["candidates"][:6]:
            print("  [YEL] 候選 %s · 四碼 %s · 主動ETF %s · 名稱 %s · 市場別 %s" % (c["label"], c["n4"], c["active"], c["named"], c["market"]))
    for k, v in Counter(n for r in o["rows"] for n in r["notes"]).most_common(10):
        print("  [YEL] %s · %d 檔" % (k, v))
    print("  [U/I] %s" % o["html"])
    print("NEXT: %s" % ("檔名擷取全綠 → prep 轉換 / 讀取" if o["lamp"] == "GREEN" else "看矩陣黃:總清單缺 → 告訴我 VDF 清單在哪;券商簡稱冊未收 → 補 Broker_Dict abbr;其餘逐檔看切割"))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()

    def opt(flag, default=None):
        return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default
    if args[:1] == ["fname"] and len(args) >= 2 and "--dir" not in args and Path(args[-1]).is_dir():
        args = args[:-1] + ["--dir", args[-1]]
    if args[:1] == ["fname"]:
        cfg = (_resolve("config_get") or (lambda: {}))()
        o = fname_run(Path(opt("--dir") or cfg.get("input_dir") or r"C:\測試樣本報告"), use_vdf=("--no-vdf" not in args))
        _print_fname(o)
        return 0
    if args[:2] == ["lists", "--use"] and len(args) >= 3:
        cs = _resolve("config_set")
        cur = list(((_resolve("config_get") or (lambda: {}))()).get("master_lists") or [])
        for x in args[2:]:
            if x not in cur:
                cur.append(x)
        cs("master_lists", cur) if cs else None
        print("[計] VRN lists · 契約路徑登記 %d 個(VDF 公布的總清單)· GREEN" % len(cur))
        for x in cur:
            print("  [%s] %s" % ("OK" if Path(x).is_file() else "YEL", x))
        return 0
    if args[:1] == ["lists"]:
        ml = master_lists(refresh=True, use_vdf=True, scan=("--scan" in args))
        if not ("--scan" in args) and not _contract_paths():
            print("  [注] 預設不掃 VDF 樹(那是 VDF 的工作);VDF 公布清單後用 lists --use <路徑> 登記;要找可跑 lists --scan(保留功能)")
        print("[計] VRN lists · 搜尋 VDF %d 檔 · 來源 %s · 快取 %s%s · %d 碼 · %s" % (ml["searched"], ml["origin"], ml["cache"] or "無", "(本次更新)" if ml["updated"] else "", len(ml["entries"]), "GREEN" if len(ml["sources"]) == 2 else ("YELLOW" if ml["entries"] else "RED")))
        for x in ml["sources"]:
            print("  [OK] %s · %s · %s 碼 · 有名稱 %s · 有市場別 %s · %s" % ("全台股" if x["kind"] == "stock" else "主動ETF", x["file"], x["codes"], x.get("named"), x.get("market"), x["path"]))
        for c in ml["candidates"][:10]:
            print("  [YEL] 候選 %s · 四碼 %s · 主動ETF %s · 名稱 %s · 市場別 %s" % (c["label"], c["n4"], c["active"], c["named"], c["market"]))
        return 0
    if args[:1] == ["ui"]:
        rc = PRIOR.main(args)
        page = _rep() / "VRN_UI_latest.html"
        if page.exists():
            h = page.read_text(encoding="utf-8", errors="replace")
            if "via://VRN/fname" not in h:
                h = h.replace(">開矩陣結果</a></div>", ">開矩陣結果</a><a href='via://VRN/fname' style='display:inline-block;padding:4px 10px;border:1px solid var(--border,#e0e0e0);border-radius:6px;text-decoration:none;margin-left:6px'>只判檔名(秒級)</a></div>", 1)
                page.write_text(h, encoding="utf-8")
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

    td = Path(tempfile.mkdtemp(prefix="vrnfn-"))
    home = td / "functional modules" / "VRN"
    (home / "knowledge").mkdir(parents=True)
    (home / "SSOT").mkdir()
    vdf = td / "functional modules" / "VDF" / "output_hub" / "export"
    vdf.mkdir(parents=True)
    rep = td / "VIA_Reports" / "vrn"
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT", "VIA_VDF_HOME")}
    os.environ.update({"VIA_VRN_SSOT_HOME": str(home), "VIA_VRN_HEALTH_OUT": str(rep), "VIA_VDF_HOME": str(td / "functional modules" / "VDF")})
    real = {"3706": ("神達", "上市"), "3653": ("健策", "上市"), "2891": ("中信金", "上市"), "6933": ("AMAX-KY", "上櫃"), "6768": ("志強-KY", "上市"), "4171": ("瑞基", "上櫃"), "2330": ("台積電", "上市"), "5274": ("信驊", "上櫃"), "1216": ("統一", "上市"),
            "7728": ("光焱科技", "上櫃"), "6526": ("達發", "上櫃"), "3038": ("全台", "上市"), "2637": ("慧洋-KY", "上市")}
    with (vdf / "vdf_tw_stock_list_all.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["stock_id", "name", "market", "name_en"])
        for c, (n, m) in real.items():
            w.writerow([c, n, m, "ASPEED Technology" if c == "5274" else ""])
        for i in range(1000, 1900):
            if str(i) not in real:
                w.writerow([str(i), "測%04d" % i, "上市", ""])
    (vdf / "VDF_ActiveETF_List_v0100.json").write_text(json.dumps([{"code": "00980A", "name": "主動野村臺灣優選", "market": "上市"}, {"code": "00981A", "name": "主動統一台股增長"}, {"code": "00982A", "name": "主動群益台灣強棒"}], ensure_ascii=False), encoding="utf-8")
    (home / "knowledge" / "VRN_Broker_Dict_v0100.json").write_text(json.dumps({"brokers": {"凱基": {"abbr": "KGI", "aliases": ["凱基", "凱基投顧"]}, "中信": {"abbr": "CTBC", "aliases": ["CTBC", "中信投顧"]}, "國泰": {"abbr": "CT", "aliases": ["國泰", "國泰證券"]}, "統一": {"abbr": "PSC", "aliases": ["統一投顧"]}},
                                                                           "brokers_extended": {"大和": {"abbr": "Daiwa", "aliases": ["Daiwa", "大和"]}, "摩根大通": {"abbr": "JPM", "aliases": ["摩根大通", "J.P. Morgan"]}}}, ensure_ascii=False), encoding="utf-8")
    ml0 = master_lists()
    ml = master_lists(scan=True)
    ml2 = master_lists(scan=True)
    chk("⓪ 預設不掃 VDF 樹(VDF 的工作)· 無契約無快取 → none", ml0["origin"] == "none" and ml0["searched"] == 0)
    chk("① 兩份總清單(lists --scan 保留):全台股(≥800 四碼)+ 主動 ETF(00xxxA)· VRN 快取 v0100 · 再跑指紋同不出新版", ml["origin"] == "live" and len(ml["sources"]) == 2 and ml["cache"] == "VRN_MasterList_v0100.json" and ml["updated"] and not ml2["updated"] and ml["entries"]["00980A"]["kind"] == "active_etf")
    shutil.move(str(td / "functional modules" / "VDF"), str(td / "VDF_gone"))
    ml3 = master_lists()
    chk("② 預設 / VDF 不在 → 用 VRN 快取(VRN 獨立)", ml3["origin"] == "cache" and "3706" in ml3["entries"])
    os.environ["VIA_VRN_MASTER_LISTS"] = str(td / "VDF_gone" / "output_hub" / "export" / "vdf_tw_stock_list_all.csv")
    ml4 = master_lists()
    os.environ.pop("VIA_VRN_MASTER_LISTS", None)
    chk("②b 契約路徑(VDF 公布的清單)→ 只讀那份", ml4["origin"] == "live" and ml4["searched"] == 1 and len(ml4["sources"]) == 1)
    shutil.move(str(td / "VDF_gone"), str(td / "functional modules" / "VDF"))
    book, _ = load_brokers_v154()
    master = ml["entries"]
    rts = _ratings()
    T = lambda fn: fname_parse(fn, master, book, datetime.datetime(2026, 9, 15).timestamp(), rts)  # noqa: E731
    cases = [("【國泰證期研究部】神達(3706 TT)-初次評等買進(+30.4_)-大顯神威，營運騰達-20250822.pdf", "3706", "3706.TW", "神達", "CT", "2025-08-22", ["初次評等買進", "大顯神威", "營運騰達"]),
             ("3653健策凱基投顧 向子慧 (3).txt", "3653", "3653.TW", "健策", "KGI", "", ["向子慧"]),
             ("凱基投顧_2891 中信金_施志鴻_20260519.pdf", "2891", "2891.TW", "中信金", "KGI", "2026-05-19", ["施志鴻"]),
             ("6933_AMAX-KY_個股介紹報告.pdf", "6933", "6933.TWO", "AMAX-KY", "", "", ["個股介紹報告"]),
             ("260914_daiwa_aspeed.pdf", "5274", "5274.TWO", "信驊", "Daiwa", "2026-09-14", []),
             ("第一場 2026年投資大趨勢 - 華南投顧 -1141201.pdf", "", "", "", "HNS", "2025-12-01", ["2026", "投資大趨勢"]),
             ("群益3Q26論壇_MIC_物理AI趨勢下人形機器人發展趨勢.pdf", "", "", "", "CSC", "", ["3Q26", "論壇"]),
             ("主動式ETF籌碼追蹤-CTBC0915.pdf", "", "", "", "CTBC", "2026-09-15", ["籌碼追蹤"]),
             ("20251204兆豐個股報告-志強-KY(6768).pdf", "6768", "6768.TW", "志強-KY", "MEGA", "2025-12-04", ["個股報告"]),
             ("統一投顧-20251209投資早報.pdf", "", "", "", "PSC", "2025-12-09", ["投資早報"]),
             ("JP-2330 20250718.pdf", "2330", "2330.TW", "台積電", "JPM", "2025-07-18", []),
             ("光焱(7728,Note)-CTBC260918.pdf", "7728", "7728.TWO", "光焱科技", "CTBC", "2026-09-18", ["Note"]),
             ("凱基投顧_6526 達發科技_劉宇程_20260917.pdf", "6526", "6526.TWO", "達發", "KGI", "2026-09-17", ["劉宇程"]),
             ("00981A主動統一台股增長月報.pdf", "00981A", "00981A.TW", "主動統一台股增長", "", "", ["月報"])]
    bad = []
    for fn, code, yf, nm, br, dt, rem_has in cases:
        g = T(fn)
        if g["code"] != code or g["yf"] != yf or (nm and g["name"] != nm) or g["broker"] != br or (dt and g["date"] != dt) or any(x not in g["remainder"] for x in rem_has) or (code and g["bbg"] != code + " TT"):
            bad.append("%s→%s|%s|%s|%s|%s|[%s]" % (fn[:18], g["code"], g["yf"], g["name"], g["broker"], g["date"], g["remainder"]))
    chk("③ 檔名完整擷取 14 例(切割 · 局部比對 · 券商英文簡稱 · 清單驗代號 · 剩餘保留)%s" % ("" if not bad else " · " + " ‖ ".join(bad)), not bad)
    g = T("凱基投顧_2891 中信金_施志鴻_20260519.pdf")
    labs = dict((t, l) for t, l in g["remainder_tokens"])
    g2 = T("【國泰證期研究部】神達(3706 TT)-初次評等買進(+30.4_)-大顯神威，營運騰達-20250822.pdf")
    l2 = dict((t, l) for t, l in g2["remainder_tokens"])
    book["國泰證券"] = {"aliases": {"國泰證券": "冊", "國泰證期": "冊"}}
    g3 = T("【國泰證期研究部】神達(3706 TT)-初次評等買進(+30.4_)-大顯神威.pdf")
    chk("④ 剩餘標類型:施志鴻 = 人名? · 初次評等買進 = 評等 · +30.4 整段數字 · 券商吃掉「證期研究部」· 「統一投顧」不誤認統一 1216 · 冊裡無 abbr 的「國泰證券」借同別名 → CT(不顯示中文)", labs.get("施志鴻") == "人名?" and l2.get("初次評等買進") == "評等" and l2.get("+30.4") == "數字" and "研究部" not in g2["remainder"] and T("統一投顧-20251209投資早報.pdf")["code"] == "" and g3["broker"] == "CT" and g3["broker"].isascii())
    inp = td / "inbox"
    inp.mkdir()
    for fn, *_ in cases:
        (inp / fn).write_bytes(b"%PDF-1.4\n%%EOF\n")
    o = fname_run(inp)
    chk("⑤ fname:矩陣 HTML(切割 · 剩餘欄)· csv · json · 秒級", Path(o["html"]).exists() and "剩餘(對照第一頁)" in Path(o["html"]).read_text(encoding="utf-8") and (rep / "prep" / "FNAME_latest.csv").exists() and o["summary"]["files"] == len(cases))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑥ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    chk("⑦ 帶加速器橋", "[VIA:ACCEL-BRIDGE:v0100]" in Path(__file__).read_text(encoding="utf-8"))
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0154 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
