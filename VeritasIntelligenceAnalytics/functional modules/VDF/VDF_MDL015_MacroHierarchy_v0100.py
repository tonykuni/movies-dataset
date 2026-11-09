#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL015_MacroHierarchy v0100 — 總經序列「向下一、二階層」探索(讀冊 · 只增候選 · 不改擷取冊)。

操作員 2026-11-09:「所有總體經濟數據都要向下一階、二階層找尋有無次階級及相關資料,如 PMI、PPI、就業相關數據等;
可網路搜尋新聞或抓關鍵字,或尋找專業關鍵字後 MacroMicro 的未進入頁面就會出現一些關鍵字」「國際重要序列可容易新增」
「FED 需要 API KEY … 使用者仍須自己申請」。

做法(全部讀冊,不寫死):
  plan      離線。VDF 總經 SSOT(macro_ssot.json series_registry)的點分碼就是階層:US.Prices.PPI.FinalDemand.Goods →
            家族 PPI · 一階 FinalDemand · 二階 Goods。照 VDF_MacroKeyword_SSOT 每個家族的 code_prefixes 把冊上序列排成樹,
            標 fred_id 有無 · 是否在細項 roster · 是否已在 us_macro 表(DuckDB 在才查)· 樹冊 PARKED 原因;
            冊上宣告的一階 / 二階名稱(level1 / level2)若冊上沒有對應序列 → 候選 DECLARED_NO_SERIES(探索目標)。
  discover  連網(雙閘先行 · 永不代設):三車道
            fred     fred_series_hint 每一支 → series/categories → category/children(一階)→ category/series(二階)+ fred_search 關鍵字搜尋;
                     要 FRED_API_KEY(環境變數或輸出根 .fred_api_key;只查有沒有 · 網址與收據遮罩)。沒鑰 = SKIP 照實記。
            akshare  離線:VAKE 知識庫 vake_registry.json(有才讀)照家族關鍵字找函數 + 冊上 akshare_fns 是否登錄;只標 LANE_ONLY(AKShare 只做交叉比對)。
            web      冊上 web_sources(MacroMicro 首頁等)經網路工具 http_text 抓頁面 → 只取連結文字 / 標題中命中家族 seeds 的字做關鍵字候選(不存全文)。
            新候選只增寫進 candidates jsonl(key 去重);不碰 VDF_FetchGroups 冊 —— 要抓才由操作員 MDL012 edit <group> add <id> --apply。
  selftest  零網路 · 只在 tempfile 寫 · 假網路工具驗三車道 · 閘關 = SKIP 且不碰 environ · 鑰永不出現在輸出。

輸出:<out>/VDF_MacroHierarchy_latest.json / .md · <out>/macro_hierarchy_candidates_v0100.jsonl(只增)。預設 <out> = <VIA>/VIA_Reports/vdf/macro。
燈:plan 成(SSOT 在 · 家族 ≥ 1)= GREEN;discover 任一車道 SKIP / ABSENT / FAIL = YELLOW;SSOT 缺 = RED(rc 2)。
邊界:不 import akshare / requests;連網只經 SUP_MDL740 NetUnified(via_net_unified 尾版);不寫 environ;不改任何既有冊。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_root = _sa_Path(__file__).resolve()
    for _ in range(6):
        _sa_root = _sa_root.parent
        if (_sa_root / "VeritasIntelligenceAnalytics").is_dir() or _sa_root.name == "VeritasIntelligenceAnalytics":
            break
    _sa_dir = (_sa_root / "VeritasIntelligenceAnalytics" if (_sa_root / "VeritasIntelligenceAnalytics").is_dir() else _sa_root) / "supportive modules" / "accelerator"
    if _sa_dir.is_dir() and str(_sa_dir) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_dir))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_here = _nb_Path(__file__).resolve()
    for _nb_up in (_nb_here.parents[2], _nb_here.parents[3] if len(_nb_here.parents) > 3 else _nb_here.parents[2]):
        _nb_dir = _nb_up / "supportive modules" / "network"
        if _nb_dir.is_dir():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入;本檔的連網全經它(雙閘在工具裡 · 本檔永不代設)。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
import glob
import html as _html
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
ENGINE = "VDF_MDL015_MacroHierarchy " + VERSION
HERE = Path(__file__).resolve().parent                       # functional modules/VDF
VIA = HERE.parent.parent                                      # VeritasIntelligenceAnalytics
BOOK_GLOB = "VDF_MacroKeyword_SSOT_v[0-9][0-9][0-9][0-9].json"
TREE_GLOB = "VDF_USMacro_Tree_v[0-9][0-9][0-9][0-9].json"
ROSTER_GLOB = "VDF_USMacro_Detail_Fetch_Roster_v[0-9][0-9][0-9][0-9].json"
MACRO_SSOT_GLOB = "references/intake/VIA_VDF_SSOT_b*/macro_ssot.json"
CANDIDATES_NAME = "macro_hierarchy_candidates_v0100.jsonl"
LATEST_JSON = "VDF_MacroHierarchy_latest.json"
LATEST_MD = "VDF_MacroHierarchy_latest.md"
FRED_API = "https://api.stlouisfed.org/fred"
KEY_ENV = "FRED_API_KEY"
KEY_FILE = ".fred_api_key"
_NET_OVERRIDE = None                                          # 自測注入假網路工具
WARN_PASS = ("state", "OK")


# ── 冊 ────────────────────────────────────────────────────────────────────────────────────────
def _latest(folder: Path, pattern: str):
    hits = sorted(folder.glob(pattern))
    return hits[-1] if hits else None


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_books(vdf_dir: Path) -> dict:
    """關鍵字冊(必)· 樹冊(選)· 細項 roster(選)· 總經 SSOT(必;缺 = RED)。"""
    out = {"vdf_dir": str(vdf_dir)}
    kb = _latest(vdf_dir, BOOK_GLOB)
    if kb is None:
        raise FileNotFoundError("VDF_MacroKeyword_SSOT 冊缺(%s)" % vdf_dir)
    out["keyword_book"], out["keyword"] = kb.name, load_json(kb)
    tb = _latest(vdf_dir, TREE_GLOB)
    out["tree_book"], out["tree"] = (tb.name, load_json(tb)) if tb else (None, {"families": []})
    rb = _latest(vdf_dir, ROSTER_GLOB)
    out["roster_book"], out["roster"] = (rb.name, load_json(rb)) if rb else (None, {})
    ms = sorted(glob.glob(str(vdf_dir / MACRO_SSOT_GLOB)))
    if not ms:
        raise FileNotFoundError("總經 SSOT 缺(%s)" % (vdf_dir / MACRO_SSOT_GLOB))
    out["macro_ssot"] = str(Path(ms[-1]).relative_to(vdf_dir))
    out["registry"] = {k: v for k, v in (load_json(ms[-1]).get("series_registry") or {}).items() if isinstance(v, dict)}
    return out


def roster_fred_ids(roster: dict) -> set:
    ids = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("fred_id", "fred", "series_id", "id") and isinstance(v, str) and re.fullmatch(r"[A-Z0-9_]{3,30}", v):
                    ids.add(v)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(roster)
    return ids


def us_macro_series(db_home) -> set | None:
    """us_macro 表已有的 series(DuckDB 在才查;不在 = None 照實)。只讀。"""
    if not db_home:
        return None
    hits = sorted(Path(db_home).rglob("vdf_global_market.duckdb"))
    if not hits:
        return None
    try:
        import duckdb  # noqa: PLC0415
        con = duckdb.connect(str(hits[0]), read_only=True)
        try:
            return {r[0] for r in con.execute("SELECT DISTINCT series FROM us_macro").fetchall()}
        finally:
            con.close()
    except Exception:  # noqa: BLE001
        return None


# ── plan(離線樹)────────────────────────────────────────────────────────────────────────────
def build_tree(books: dict, have_series: set | None) -> dict:
    reg = books["registry"]
    roster_ids = roster_fred_ids(books["roster"])
    tree_fam = {f.get("id"): f for f in books["tree"].get("families") or []}
    families = []
    for fam in books["keyword"]["families"]:
        prefixes = tuple(fam.get("code_prefixes") or ())
        codes = sorted(c for c in reg if any(c == p or c.startswith(p + ".") for p in prefixes))
        levels = {}
        rows = []
        for c in codes:
            pref = next(p for p in prefixes if c == p or c.startswith(p + "."))
            rest = c[len(pref):].strip(".").split(".") if c != pref else []
            l1 = rest[0] if rest else "(根)"
            l2 = ".".join(rest[1:]) if len(rest) > 1 else ""
            v = reg[c]
            fid = v.get("fred_id")
            row = {"code": c, "level1": l1, "level2": l2, "fred_id": fid, "source": v.get("source"), "freq": v.get("freq"), "unit": v.get("unit"),
                   "in_roster": bool(fid and fid in roster_ids), "in_us_macro": (fid in have_series) if (have_series is not None and fid) else None}
            rows.append(row)
            levels.setdefault(l1, []).append(row)
        declared_missing = []
        names_on_file = " ".join(c.lower() for c in codes)
        for lvl, names in (("level1", fam.get("level1") or []), ("level2", fam.get("level2") or [])):
            for nm in names:
                toks = [t for t in re.split(r"[\s/·()（）]+", nm) if re.fullmatch(r"[A-Za-z0-9\-]+", t) and len(t) >= 2]
                hit = any(("." + t.lower()) in ("." + names_on_file.replace(" ", " .")) or ("." + t.lower() + ".") in (" ".join("." + c.lower() + "." for c in codes)) for t in toks)
                if not hit:
                    declared_missing.append({"level": lvl, "name": nm})
        tf = tree_fam.get(fam["id"]) or {}
        families.append({"id": fam["id"], "zh": fam.get("zh"), "code_prefixes": list(prefixes), "series_on_file": len(codes), "level1_count": len(levels),
                         "level2_count": sum(1 for r in rows if r["level2"]), "with_fred_id": sum(1 for r in rows if r["fred_id"]),
                         "in_roster": sum(1 for r in rows if r["in_roster"]), "in_us_macro": (sum(1 for r in rows if r["in_us_macro"]) if have_series is not None else None),
                         "tree_state": tf.get("state"), "tree_why": tf.get("why"), "levels": {k: [{"code": r["code"], "level2": r["level2"], "fred_id": r["fred_id"]} for r in v] for k, v in levels.items()},
                         "declared_missing": declared_missing, "akshare_fns": list(fam.get("akshare_fns") or []), "keywords": list(fam.get("keywords") or [])})
    return {"families": families, "registry_series": len(reg), "roster_fred_ids": len(roster_ids), "us_macro_queried": have_series is not None}


# ── discover(三車道)──────────────────────────────────────────────────────────────────────
def mask(url: str) -> str:
    return re.sub(r"(api_key=)[^&\s]+", r"\1***", url or "")


def find_key(out_root: Path) -> bool:
    """FRED 鑰只查有沒有(環境變數 → 輸出根 .fred_api_key);值不離開本函數的呼叫鏈,不印不寫。"""
    if os.environ.get(KEY_ENV, "").strip():
        return True
    f = out_root / KEY_FILE
    return f.is_file() and bool(f.read_text(encoding="utf-8").strip())


def _key_value(out_root: Path) -> str:
    k = os.environ.get(KEY_ENV, "").strip()
    if k:
        return k
    f = out_root / KEY_FILE
    return f.read_text(encoding="utf-8").strip() if f.is_file() else ""


def _net():
    return _NET_OVERRIDE if _NET_OVERRIDE is not None else _via_net()


def _call_json(net, url: str) -> dict:
    r = net.http_json(url)
    return r if isinstance(r, dict) else {"state": "FAIL", "note": "網路工具回非 dict"}


def lane_fred(fam: dict, key: str, net, limit: int, known: set) -> dict:
    """series/categories → category/children(一階)→ category/series(二階)· series/search(關鍵字)。全部遮罩。"""
    calls, cands, states = [], [], []
    q = "&api_key=%s&file_type=json" % key

    def rec(url, r):
        calls.append({"url": mask(url), "state": r.get("state"), "note": (r.get("note") or "")[:120]})
        states.append(r.get("state"))
        return r.get("state") == "OK" and isinstance(r.get("data"), dict)
    cat_ids = {}
    for sid in fam.get("fred_series_hint") or []:
        url = "%s/series/categories?series_id=%s%s" % (FRED_API, sid, q)
        r = _call_json(net, url)
        if not rec(url, r):
            continue
        for c in r["data"].get("categories") or []:
            cat_ids[c.get("id")] = {"name": c.get("name"), "from_series": sid}
    for cid, meta in list(cat_ids.items())[:limit]:
        url = "%s/category/children?category_id=%s%s" % (FRED_API, cid, q)
        r = _call_json(net, url)
        children = (r["data"].get("categories") or []) if rec(url, r) else []
        for ch in children[:limit]:
            cands.append({"kind": "fred_category", "level": 1, "family": fam["id"], "id": "CAT%s" % ch.get("id"), "name": ch.get("name"), "parent": meta["name"], "via": meta["from_series"]})
        for cid2, nm2 in [(cid, meta["name"])] + [(ch.get("id"), ch.get("name")) for ch in children[:limit]]:
            url = "%s/category/series?category_id=%s&limit=%d&order_by=popularity&sort_order=desc%s" % (FRED_API, cid2, limit, q)
            r = _call_json(net, url)
            if not rec(url, r):
                continue
            for s in r["data"].get("seriess") or []:
                if s.get("id") in known:
                    continue
                cands.append({"kind": "fred_series", "level": 2 if cid2 != cid else 1, "family": fam["id"], "id": s.get("id"), "name": s.get("title"), "freq": s.get("frequency_short"),
                              "units": s.get("units_short"), "last_updated": s.get("last_updated"), "parent": nm2, "via": meta["from_series"]})
    for text in fam.get("fred_search") or []:
        url = "%s/series/search?search_text=%s&limit=%d%s" % (FRED_API, re.sub(r"\s+", "+", text.strip()), limit, q)
        r = _call_json(net, url)
        if not rec(url, r):
            continue
        for s in r["data"].get("seriess") or []:
            if s.get("id") not in known:
                cands.append({"kind": "fred_series", "level": 1, "family": fam["id"], "id": s.get("id"), "name": s.get("title"), "freq": s.get("frequency_short"),
                              "units": s.get("units_short"), "last_updated": s.get("last_updated"), "parent": "search:" + text, "via": "series/search"})
    st = "OK" if states and all(s == "OK" for s in states) else ("DENY" if "DENY" in states else ("FAIL" if "FAIL" in states else ("OK" if states else "SKIP")))
    return {"state": st, "calls": calls, "candidates": cands}


def vake_registry(vake_root) -> list | None:
    for p in (Path(vake_root) / "knowledge" / "vake_registry.json",):
        if p.is_file():
            try:
                d = load_json(p)
                return d if isinstance(d, list) else (d.get("entries") or list(d.values()))
            except (OSError, ValueError):
                return None
    return None


def lane_akshare(fam: dict, registry: list | None) -> dict:
    """離線:VAKE 知識庫(有才讀)照 seeds / keywords 找函數;冊上 akshare_fns 標 登錄 / 未登錄。只標 LANE_ONLY。"""
    if registry is None:
        return {"state": "ABSENT", "note": "VAKE 知識庫不在(VAKE_ROOT/knowledge/vake_registry.json)· AKShare 車道照實列缺", "candidates": [], "book_fns": {fn: None for fn in fam.get("akshare_fns") or []}}
    toks = [t.lower() for t in (fam.get("seeds") or []) + (fam.get("keywords") or []) if len(t) >= 3]
    fns = {}
    for e in registry:
        if not isinstance(e, dict):
            continue
        hay = " ".join(str(e.get(k, "")) for k in ("fn", "title", "category")).lower() + " " + " ".join(map(str, e.get("heading_path") or [])).lower()
        if any(t in hay for t in toks):
            fns[e.get("fn")] = {"kind": "akshare_fn", "level": 1, "family": fam["id"], "id": e.get("fn"), "name": e.get("title"), "parent": " / ".join(map(str, e.get("heading_path") or []))[:80], "via": "vake_registry", "lane": "LANE_ONLY"}
    reg_names = {e.get("fn") for e in registry if isinstance(e, dict)}
    return {"state": "OK", "candidates": list(fns.values()), "book_fns": {fn: (fn in reg_names) for fn in fam.get("akshare_fns") or []}}


_ANCHOR = re.compile(r"<(?:a|h[1-4]|li|span|title)\b[^>]*>(.*?)</(?:a|h[1-4]|li|span|title)>", re.I | re.S)
_TAG = re.compile(r"<[^>]+>")


def extract_keywords(page: str, seeds_by_family: dict, cap: int = 60) -> list:
    """只取連結 / 標題文字;命中家族 seeds 的短字串(≤ 40 字)當關鍵字;不存全文。"""
    out, seen = [], set()
    for m in _ANCHOR.finditer(page or ""):
        txt = _html.unescape(_TAG.sub("", m.group(1))).strip()
        txt = re.sub(r"\s+", " ", txt)
        if not (2 <= len(txt) <= 40):
            continue
        low = txt.lower()
        for fid, seeds in seeds_by_family.items():
            if any(s.lower() in low for s in seeds if s):
                key = (fid, low)
                if key not in seen:
                    seen.add(key)
                    out.append({"kind": "keyword", "level": 0, "family": fid, "id": "kw:" + txt, "name": txt, "via": "web"})
                break
        if len(out) >= cap:
            break
    return out


def lane_web(book: dict, net, key_ok: bool, out_root: Path) -> dict:
    """冊上 web_sources 逐一 http_text / http_json;抓到的只做關鍵字抽取。"""
    seeds = {f["id"]: list(f.get("seeds") or []) + list(f.get("keywords") or []) for f in book["families"]}
    srcs, cands, states = [], [], []
    for ws in book.get("web_sources") or []:
        url = ws.get("url") or ""
        if "{FRED_API_KEY}" in url:
            if not key_ok:
                srcs.append({"id": ws.get("id"), "url": mask(url), "state": "SKIP", "note": "要 FRED 鑰 · 沒鑰照實跳過"})
                states.append("SKIP")
                continue
            url = url.replace("{FRED_API_KEY}", _key_value(out_root))
        if ws.get("lane") == "http_json":
            r = _call_json(net, url)
            names = []
            if r.get("state") == "OK" and isinstance(r.get("data"), dict):
                names = [x.get("name") for x in (r["data"].get("releases") or []) if isinstance(x, dict)]
                page = "".join("<li>%s</li>" % _html.escape(str(n)) for n in names if n)
                cands.extend(dict(c, via=ws.get("id")) for c in extract_keywords(page, seeds))
            srcs.append({"id": ws.get("id"), "url": mask(url), "state": r.get("state"), "note": (r.get("note") or "")[:120], "items": len(names)})
        else:
            r = net.http_text(url)
            r = r if isinstance(r, dict) else {"state": "FAIL", "note": "網路工具回非 dict"}
            got = r.get("data") if r.get("state") == "OK" and isinstance(r.get("data"), str) else ""
            kws = extract_keywords(got, seeds) if got else []
            cands.extend(dict(c, via=ws.get("id")) for c in kws)
            srcs.append({"id": ws.get("id"), "url": mask(url), "state": r.get("state"), "note": (r.get("note") or "")[:120], "bytes": len(got), "keywords": len(kws)})
        states.append(r.get("state"))
    st = "OK" if states and all(s == "OK" for s in states) else ("DENY" if "DENY" in states else ("FAIL" if "FAIL" in states else ("SKIP" if states else "SKIP")))
    return {"state": st, "sources": srcs, "candidates": cands}


def append_candidates(path: Path, cands: list, at: str) -> tuple:
    """只增:key = kind|family|id;已在檔裡的不重寫。回 (新增數, 既有數)。"""
    seen = set()
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                o = json.loads(line)
                seen.add("%s|%s|%s" % (o.get("kind"), o.get("family"), o.get("id")))
            except ValueError:
                continue
    before = len(seen)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("a", encoding="utf-8") as fh:
        for c in cands:
            k = "%s|%s|%s" % (c.get("kind"), c.get("family"), c.get("id"))
            if k in seen:
                continue
            seen.add(k)
            fh.write(json.dumps(dict(c, found_at=at, engine=ENGINE), ensure_ascii=False) + "\n")
            n += 1
    return n, before


# ── 收據 ──────────────────────────────────────────────────────────────────────────────────────
def write_md(path: Path, rec: dict) -> None:
    L = ["# VDF 總經階層探索 · %s · %s · %s" % (rec["engine"], rec["at"], rec["lamp"]), "", rec.get("meaning", ""), "",
         "| 家族 | 冊上序列 | 一階 | 二階 | 有 fred_id | 在細項 roster | 在 us_macro | 樹冊狀態 | 冊宣告但沒序列 |", "|---|---|---|---|---|---|---|---|---|"]
    for f in rec["plan"]["families"]:
        L.append("| %s %s | %d | %d | %d | %d | %d | %s | %s | %d |" % (f["id"], f["zh"], f["series_on_file"], f["level1_count"], f["level2_count"], f["with_fred_id"], f["in_roster"],
                                                                     "—" if f["in_us_macro"] is None else f["in_us_macro"], f.get("tree_state") or "—", len(f["declared_missing"])))
    if rec.get("discover"):
        d = rec["discover"]
        L += ["", "## 探索車道", "", "| 車道 | 狀態 | 候選 | 備註 |", "|---|---|---|---|"]
        for lane in ("fred", "akshare", "web"):
            x = d["lanes"].get(lane) or {}
            L.append("| %s | %s | %d | %s |" % (lane, x.get("state", "—"), x.get("candidates", 0), (x.get("note") or "")[:80]))
        L += ["", "候選檔:`%s` · 本次新增 %d(既有 %d)。要抓才由操作員 `VDF_MDL012_FetchGroups edit <group> add <id> --apply`;AKShare 候選只做交叉比對(LANE_ONLY)。" % (d["candidates_file"], d["candidates_new"], d["candidates_before"])]
    L += ["", "## 冊宣告但冊上沒有序列(探索目標)", ""]
    for f in rec["plan"]["families"]:
        if f["declared_missing"]:
            L.append("- **%s**:%s" % (f["id"], " · ".join("%s/%s" % (m["level"], m["name"]) for m in f["declared_missing"])))
    L += ["", "規則:不改擷取冊 · 鑰只查有沒有(遮罩)· 雙閘永不代設 · AKShare 不取代 FRED。"]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def run(args) -> int:
    vdf_dir = Path(args.vdf_dir) if getattr(args, "vdf_dir", None) else HERE
    out_root = Path(args.out) if getattr(args, "out", None) else (VIA / "VIA_Reports" / "vdf" / "macro")
    out_root.mkdir(parents=True, exist_ok=True)
    at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rec = {"engine": ENGINE, "verb": args.verb, "at": at, "out": str(out_root), "steps": []}
    try:
        books = load_books(vdf_dir)
    except (FileNotFoundError, ValueError) as error:
        rec.update(lamp="RED", meaning="冊缺 · %s" % error)
        (out_root / LATEST_JSON).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        print("[RED] %s · %s" % (ENGINE, error), flush=True)
        return 2
    rec["books"] = {k: books[k] for k in ("keyword_book", "tree_book", "roster_book", "macro_ssot")}
    have = us_macro_series(getattr(args, "db_home", None))
    plan = build_tree(books, have)
    rec["plan"] = plan
    rec["steps"].append({"step": "① 樹(冊點分碼 → 家族 / 一階 / 二階)", "lamp": "GREEN", "detail": "家族 %d · 冊上序列 %d · 細項 roster fred_id %d · us_macro %s" % (
        len(plan["families"]), plan["registry_series"], plan["roster_fred_ids"], "已查" if plan["us_macro_queried"] else "未查(DuckDB 不在)")})
    lamp = "GREEN"
    if args.verb == "discover":
        net = _net()
        key_ok = find_key(out_root)
        known = {r["fred_id"] for f in plan["families"] for lv in f["levels"].values() for r in lv if r.get("fred_id")}
        lanes_req = [s.strip() for s in (args.source or "all").split(",")]
        lanes_req = ["fred", "akshare", "web"] if "all" in lanes_req else lanes_req
        fams = plan["families"] if (args.family or "all") == "all" else [f for f in plan["families"] if f["id"] in args.family.split(",")]
        kw_fams = {f["id"]: f for f in books["keyword"]["families"]}
        lanes, cands = {}, []
        if "fred" in lanes_req:
            if net is None:
                lanes["fred"] = {"state": "FAIL", "note": "VIA 網路工具不在(supportive modules/network/via_net_unified_v*.py)· 不直連", "candidates": 0}
            elif not key_ok:
                lanes["fred"] = {"state": "SKIP", "note": "沒有 FRED_API_KEY(環境變數或 %s)· 使用者自己申請後再跑;不印不猜" % (out_root / KEY_FILE), "candidates": 0}
            else:
                key = _key_value(out_root)
                sts, calls, n = [], [], 0
                for f in fams:
                    r = lane_fred(kw_fams[f["id"]], key, net, int(args.limit), known)
                    sts.append(r["state"])
                    calls.extend(r["calls"])
                    cands.extend(r["candidates"])
                    n += len(r["candidates"])
                st = "OK" if sts and all(s == "OK" for s in sts) else ("DENY" if "DENY" in sts else ("FAIL" if "FAIL" in sts else "SKIP"))
                lanes["fred"] = {"state": st, "calls": len(calls), "candidates": n, "note": {"DENY": "雙閘關(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 未設)· 本引擎不代設", "FAIL": "部分呼叫失敗(看 calls)", "OK": "", "SKIP": ""}[st], "call_log": calls[:40]}
            if "***" not in json.dumps(lanes["fred"]) and key_ok and lanes["fred"].get("calls"):
                lanes["fred"]["note"] += " · 遮罩"
        if "akshare" in lanes_req:
            reg = vake_registry(os.environ.get("VAKE_ROOT") or (Path.home() / "VAKE"))
            sts, n, book_fns = [], 0, {}
            for f in fams:
                r = lane_akshare(kw_fams[f["id"]], reg)
                sts.append(r["state"])
                cands.extend(r["candidates"])
                n += len(r["candidates"])
                book_fns[f["id"]] = r["book_fns"]
            lanes["akshare"] = {"state": "ABSENT" if reg is None else "OK", "note": "" if reg is not None else "VAKE 知識庫不在 · 照實列缺(桌機 VAKE_ROOT 有才會有)", "candidates": n, "book_fns_registered": book_fns, "lane": "LANE_ONLY(只交叉比對 · 不取代 FRED)"}
        if "web" in lanes_req:
            if net is None:
                lanes["web"] = {"state": "FAIL", "note": "VIA 網路工具不在 · 不直連", "candidates": 0}
            else:
                r = lane_web(books["keyword"], net, key_ok, out_root)
                cands.extend(r["candidates"])
                lanes["web"] = {"state": r["state"], "sources": r["sources"], "candidates": len(r["candidates"]), "note": {"DENY": "雙閘關 · 本引擎不代設", "FAIL": "部分來源失敗(看 sources)", "SKIP": "全部跳過", "OK": ""}.get(r["state"], "")}
        cpath = out_root / CANDIDATES_NAME
        n_new, n_before = append_candidates(cpath, cands, at)
        rec["discover"] = {"lanes": lanes, "candidates_file": str(cpath), "candidates_new": n_new, "candidates_before": n_before, "families": [f["id"] for f in fams], "fred_key_present": key_ok}
        bad = [k for k, v in lanes.items() if v.get("state") != "OK"]
        lamp = "YELLOW" if bad else "GREEN"
        rec["steps"].append({"step": "② 探索(%s)" % " · ".join(lanes_req), "lamp": lamp, "detail": "候選新增 %d(既有 %d)· %s" % (n_new, n_before, " · ".join("%s=%s" % (k, v.get("state")) for k, v in lanes.items()))})
    rec["lamp"] = lamp
    rec["meaning"] = {"GREEN": "樹建好%s" % (" · 三車道全 OK · 候選已只增寫入" if args.verb == "discover" else " · 要探索加 discover(雙閘 + FRED 鑰)"),
                      "YELLOW": "樹建好 · 探索有車道 SKIP / ABSENT / DENY / FAIL(看 discover.lanes;閘與鑰由操作員設)"}[lamp]
    (out_root / LATEST_JSON).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    write_md(out_root / LATEST_MD, rec)
    print("[%s] %s %s · 家族 %d · 冊上序列 %d%s → %s" % (lamp, ENGINE, args.verb, len(plan["families"]), plan["registry_series"],
                                                   (" · 候選 +%d" % rec["discover"]["candidates_new"]) if args.verb == "discover" else "", out_root / LATEST_JSON), flush=True)
    return 0


# ── selftest ──────────────────────────────────────────────────────────────────────────────────
class _FakeNet:
    """假網路工具:記錄每個網址;依路徑回固定 JSON / 頁面;state 可控(OK / DENY)。"""

    def __init__(self, state="OK"):
        self.state, self.urls = state, []

    def http_json(self, url, timeout=30):
        self.urls.append(url)
        if self.state != "OK":
            return {"state": self.state, "note": "closed"}
        if "/series/categories" in url:
            return {"state": "OK", "data": {"categories": [{"id": 32455, "name": "ISM Manufacturing"}]}}
        if "/category/children" in url:
            return {"state": "OK", "data": {"categories": [{"id": 1, "name": "New Orders"}, {"id": 2, "name": "Prices"}]}}
        if "/category/series" in url:
            return {"state": "OK", "data": {"seriess": [{"id": "NAPMNOI", "title": "ISM New Orders", "frequency_short": "M", "units_short": "Index"}, {"id": "NEWSUB1", "title": "Sub index 1", "frequency_short": "M", "units_short": "Index"}]}}
        if "/series/search" in url:
            return {"state": "OK", "data": {"seriess": [{"id": "SRCH1", "title": "Searched PMI", "frequency_short": "M", "units_short": "Index"}]}}
        if "/releases" in url:
            return {"state": "OK", "data": {"releases": [{"name": "ISM Manufacturing Report"}, {"name": "Employment Situation"}]}}
        return {"state": "FAIL", "note": "unknown"}

    def http_text(self, url, timeout=30):
        self.urls.append(url)
        if self.state != "OK":
            return {"state": self.state, "note": "closed"}
        return {"state": "OK", "data": "<html><title>財經M平方</title><a href='/x'>美國 ISM 製造業 PMI</a><li>非農就業人數</li><h2>CPI 通膨</h2><a>無關連結</a><p>很長很長的正文不取</p></html>"}


def selftest() -> int:
    global _NET_OVERRIDE
    checks = []

    def chk(name, cond, note=""):
        checks.append((name, bool(cond), note))
        print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, (" · " + note) if note else ""), flush=True)
    env_before = dict(os.environ)
    with tempfile.TemporaryDirectory(prefix="mdl015_") as td:
        td = Path(td)
        vdf = td / "VDF"
        (vdf / "references/intake/VIA_VDF_SSOT_b999").mkdir(parents=True)
        reg = {"_c": "comment", "US.Business.ISM.Mfg.PMI": {"fred_id": "NAPM", "source": "ISM", "freq": "Monthly", "unit": "Index"},
               "US.Business.ISM.Mfg.NewOrders": {"fred_id": "NAPMNOI", "source": "ISM"}, "US.Business.ISM.Svc.PMI": {"fred_id": "NMFCI", "source": "ISM"},
               "US.Prices.PPI.FinalDemand": {"fred_id": "PPIFID", "source": "BLS"}, "US.Prices.PPI.FinalDemand.Goods": {"fred_id": "WPSFD49207", "source": "BLS"},
               "US.Labor.NFP": {"fred_id": "PAYEMS", "source": "BLS"}}
        (vdf / "references/intake/VIA_VDF_SSOT_b999/macro_ssot.json").write_text(json.dumps({"series_registry": reg}), encoding="utf-8")
        book = load_json(HERE / sorted(HERE.glob(BOOK_GLOB))[-1].name) if sorted(HERE.glob(BOOK_GLOB)) else None
        chk("① 本倉關鍵字冊在 · 家族 ≥ 5 · 每家族有 code_prefixes / level1 / level2 / seeds", book is not None and len(book["families"]) >= 5 and all(k in f for f in book["families"] for k in ("code_prefixes", "level1", "level2", "seeds")))
        (vdf / "VDF_MacroKeyword_SSOT_v0100.json").write_text(json.dumps(book, ensure_ascii=False), encoding="utf-8")
        (vdf / "VDF_USMacro_Tree_v0100.json").write_text(json.dumps({"families": [{"id": "pmi", "state": "PARKED", "why": "HTTP 400"}]}), encoding="utf-8")
        (vdf / "VDF_USMacro_Detail_Fetch_Roster_v0100.json").write_text(json.dumps({"sections": {"pmi": [{"fred_id": "NAPMNOI"}]}}), encoding="utf-8")
        books = load_books(vdf)
        plan = build_tree(books, {"NAPM"})
        pmi = next(f for f in plan["families"] if f["id"] == "pmi")
        ppi = next(f for f in plan["families"] if f["id"] == "ppi")
        chk("② 點分碼成樹:pmi 冊上 3 · 一階 Mfg/Svc=2 · 二階 3(PMI 本體 · NewOrders · Svc PMI);ppi 一階 FinalDemand · 二階 Goods", pmi["series_on_file"] == 3 and pmi["level1_count"] == 2 and pmi["level2_count"] == 3 and ppi["level2_count"] == 1 and "Goods" in json.dumps(ppi["levels"]) and "NewOrders" in json.dumps(pmi["levels"]["Mfg"]))
        chk("③ 標記:in_roster(NAPMNOI)=1 · in_us_macro(NAPM)=1 · 樹冊 PARKED 帶進來", pmi["in_roster"] == 1 and pmi["in_us_macro"] == 1 and pmi["tree_state"] == "PARKED")
        chk("④ 冊宣告但沒序列 → declared_missing(pmi 的二階「生產 / 就業 …」在列 · 不假填)", any(m["level"] == "level2" for m in pmi["declared_missing"]) and all(isinstance(m["name"], str) for m in pmi["declared_missing"]))
        out = td / "out"
        out.mkdir()
        ns = argparse.Namespace(verb="plan", vdf_dir=str(vdf), out=str(out), db_home=None, source="all", family="all", limit=5)
        rc = run(ns)
        rec = load_json(out / LATEST_JSON)
        chk("⑤ plan:rc 0 · GREEN · 收據 + md 寫在 out", rc == 0 and rec["lamp"] == "GREEN" and (out / LATEST_MD).is_file() and rec["plan"]["registry_series"] == 6)
        fake = _FakeNet("OK")
        _NET_OVERRIDE = fake
        (out / KEY_FILE).write_text("SECRET_KEY_123\n", encoding="utf-8")
        ns.verb, ns.source, ns.family = "discover", "fred,web", "pmi"
        rc = run(ns)
        rec = load_json(out / LATEST_JSON)
        blob = json.dumps(rec) + (out / LATEST_MD).read_text(encoding="utf-8") + (out / CANDIDATES_NAME).read_text(encoding="utf-8")
        chk("⑥ discover fred:series/categories → children(一階 2)→ category/series(二階)+ search · 已知 NAPMNOI 不重列", rec["discover"]["lanes"]["fred"]["state"] == "OK" and any(u.endswith("file_type=json") and "/category/children" in u for u in fake.urls)
            and "NEWSUB1" in blob and "SRCH1" in blob and '"id": "NAPMNOI", "name"' not in blob)
        chk("⑦ 鑰永不出現在收據 / md / 候選;網址遮罩 api_key=***", "SECRET_KEY_123" not in blob and "api_key=***" in blob and any("api_key=SECRET_KEY_123" in u for u in fake.urls))
        chk("⑧ web:只取連結 / 標題命中 seeds 的字(ISM PMI · 非農 · CPI)· 正文不取 · via=來源 id", rec["discover"]["lanes"]["web"]["state"] == "OK" and "美國 ISM 製造業 PMI" in blob and "非農就業人數" in blob and "很長很長" not in blob)
        n1 = sum(1 for _ in (out / CANDIDATES_NAME).open(encoding="utf-8"))
        rc = run(ns)
        n2 = sum(1 for _ in (out / CANDIDATES_NAME).open(encoding="utf-8"))
        rec2 = load_json(out / LATEST_JSON)
        chk("⑨ 候選只增去重:第二次 discover 新增 0 · 檔列數不變", n1 == n2 and rec2["discover"]["candidates_new"] == 0 and rec2["discover"]["candidates_before"] == n1)
        _NET_OVERRIDE = _FakeNet("DENY")
        rc = run(ns)
        rec3 = load_json(out / LATEST_JSON)
        chk("⑩ 雙閘關:車道 DENY · 燈 YELLOW · rc 0 · 本引擎不碰 environ", rc == 0 and rec3["lamp"] == "YELLOW" and rec3["discover"]["lanes"]["fred"]["state"] == "DENY" and dict(os.environ) == env_before)
        (out / KEY_FILE).unlink()
        _NET_OVERRIDE = _FakeNet("OK")
        ns.source = "fred,akshare"
        os.environ.pop(KEY_ENV, None)
        rc = run(ns)
        rec4 = load_json(out / LATEST_JSON)
        chk("⑪ 沒鑰:fred SKIP(不呼叫)· akshare 知識庫不在 = ABSENT · 燈 YELLOW", rec4["discover"]["lanes"]["fred"]["state"] == "SKIP" and rec4["discover"]["lanes"]["akshare"]["state"] == "ABSENT" and rec4["lamp"] == "YELLOW")
        vr = td / "VAKE" / "knowledge"
        vr.mkdir(parents=True)
        (vr / "vake_registry.json").write_text(json.dumps([{"fn": "macro_usa_ism_pmi", "title": "美国ISM制造业PMI", "category": "macro", "heading_path": ["宏观", "美国", "PMI"]}, {"fn": "stock_zh_a_hist", "title": "A股历史", "category": "stock", "heading_path": ["股票"]}]), encoding="utf-8")
        os.environ["VAKE_ROOT"] = str(td / "VAKE")
        try:
            rc = run(ns)
            rec5 = load_json(out / LATEST_JSON)
        finally:
            os.environ.pop("VAKE_ROOT", None)
        ak = rec5["discover"]["lanes"]["akshare"]
        chk("⑫ VAKE 知識庫在:關鍵字命中 macro_usa_ism_pmi(股票函數不收)· 冊上函數登錄旗標 · LANE_ONLY", ak["state"] == "OK" and ak["candidates"] >= 1 and ak["book_fns_registered"]["pmi"].get("macro_usa_ism_pmi") is True and "LANE_ONLY" in ak["lane"] and "stock_zh_a_hist" not in (out / CANDIDATES_NAME).read_text(encoding="utf-8"))
        src = Path(__file__).read_text(encoding="utf-8")
        chk("⑬ 邊界:不 import 第三方網路 / akshare 套件 · 不寫 environ(只有自測區一處)· 連網只經 _via_net",
            re.search(r"^\s*(import|from)\s+(akshare|requests|urllib|httpx|aiohttp)\b", src, re.M) is None and len(re.findall(r"os\.environ\[[^\]]+\]\s*=", src)) == 1 and "_via_net()" in src)
        chk("⑭ 環境變數原樣", dict(os.environ) == env_before)
    _NET_OVERRIDE = None
    n_pass = sum(1 for _, ok, _ in checks if ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n_pass == len(checks) else "FAIL", ENGINE, n_pass, len(checks)), flush=True)
    return 0 if n_pass == len(checks) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv or argv[:1] == ["selftest"]:                      # VCGC 站表 / 交接案用 --selftest 旗標
        return selftest()
    ap = argparse.ArgumentParser(prog="VDF_MDL015_MacroHierarchy_v0100.py", description=__doc__.split("\n")[0])
    ap.add_argument("verb", choices=["plan", "discover", "selftest"])
    ap.add_argument("--vdf-dir", dest="vdf_dir", default=None, help="VDF 夾(預設 = 本檔所在夾)")
    ap.add_argument("--out", default=None, help="輸出夾(預設 <VIA>/VIA_Reports/vdf/macro)")
    ap.add_argument("--db-home", dest="db_home", default=None, help="VDF 資料庫家(有 vdf_global_market.duckdb 才查 us_macro)")
    ap.add_argument("--source", default="all", help="discover 車道:fred,akshare,web 或 all")
    ap.add_argument("--family", default="all", help="家族 id(逗號)或 all")
    ap.add_argument("--limit", default=20, type=int, help="FRED 每層最多幾筆")
    args = ap.parse_args(argv)
    if args.verb == "selftest":
        return selftest()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
