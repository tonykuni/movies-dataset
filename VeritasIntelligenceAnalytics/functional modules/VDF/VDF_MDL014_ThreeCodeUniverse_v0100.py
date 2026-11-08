#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL014_ThreeCodeUniverse v0100 — 一個指令 · 三種代號當輸入 · 取相關資訊(OUT-01 三組合一)

操作員 2026-11-08:「VDF 要先掌握自動生成更新台灣股票清單 + 加權指數 / 櫃買指數,
還有一個指令生成主動式台股 ETF 生成清單驗證。這些的三種代號作為輸入去取得相關資訊。」

三種代號(規則一律讀冊,不寫死在程式裡 —— 冊 VDF_InputUniverse_SSOT_v*.json):
  IN-01 TW_STOCK              個股        code_regex ^[1-9][0-9]{3}$   真相 vdf_tw_market.duckdb::tw_listings_industry
  IN-02 TW_ACTIVE_EQUITY_ETF  主動式 ETF  code_regex ^00[0-9]{3}A$     真相 ActiveTWETF.duckdb::active_tw_etf_registry
  IN-03 TW_INDEX              加權 / 櫃買  members TAIEX · TPEX          真相 VDF_TWIndex_Daily.duckdb::tw_index_daily

**本支不自己抓資料。** 抓是三支既有引擎的事(冊 VDF_FetchSystem_SSOT:009 · 010 · e232,
e232 的 needs 已寫明要等 009 / 010),本支做的是它們之外、冊上要而樹上還缺的那一段:

  ① 代號路由   任何一個代號 → 它是哪一型 · 哪個市場 · yf / bloomberg 代碼 · 誰是真相表 · 誰負責抓 ·
                 這台機器上有沒有。認不出來一律 UNKNOWN,不猜。
  ② 來源梯子   每一組照順序找料:LIVE_DB(真相庫在位)→ SEED_BOOK(倉內已驗證的種子冊)→
                 BOOK_STATIC(冊上宣告的靜態成員,只有指數適用)→ ABSENT。
                 **用到 SEED_BOOK 的組,燈最高只能到 AMBER** —— 種子冊不是當日官方真相,
                 就算它當初是 OpenAPI 驗過的也一樣:驗證時間不是今天。
  ③ 一個指令   build 把三組併成 OUT-01(欄位 / 主鍵 / 必填 / 最少列數全照冊),
                 再跑冊自己的 OUT-01 驗證律,出一盞總燈。
  ④ 誠實      ABSENT 不假填 · 低於家數下限 AMBER · 任一所 0 家 RED · 指數少一個 RED · 代號重號 RED。

入口:VDF System Manager 總控(VIA_FROM_VDFSM=YES)或 VCGC。本支零網路、零安裝、不代設同意閘。
動詞:classify <代號…> | build [--apply] | info <代號…> | plan | ui | --selftest
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本支零外呼,只用來報閘況。"""
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

import argparse
import html
import json
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent                 # functional modules/VDF
VIA = HERE.parent.parent                               # VeritasIntelligenceAnalytics
TAG = "VDF_MDL014_ThreeCodeUniverse v" + Path(__file__).stem.rsplit("_v", 1)[-1]
SCHEMA = "VIA.VDF.ThreeCodeUniverse.v1"

IN_SSOT_STEM = "VDF_InputUniverse_SSOT_v"
FETCH_SSOT_STEM = "VDF_FetchSystem_SSOT_v"
OUT_REL = Path("VIA_Reports") / "vdf" / "universe"
BOOK_STEM = "VDF_ThreeCodeUniverse_v"
UI_NAME = "VDF_ThreeCodeUniverse_UI.html"

# 倉內已驗證的種子冊(不是當日官方真相,所以用到它的組燈頂到 AMBER)
SEED_ETF = VIA / "supportive modules" / "VIA_FlowSystem" / "FlowSystem_v2" / "config" / "TW_Active_ETF_Registry_v0100.json"
SEED_EQ = VIA / "supportive modules" / "VIA_FlowSystem" / "FlowSystem_v2" / "config" / "TW_Equity_Registry_v0100.json"

# 真相庫(冊 inputs[*].truth 指的那幾顆)
DB_MARKET = HERE / "output_hub" / "tw_market" / "vdf_tw_market.duckdb"
DB_ETF = HERE / "output_hub" / "active_tw_etf" / "active_tw_etf_holdings" / "ActiveTWETF.duckdb"
DB_INDEX = HERE / "output_hub" / "tw_index" / "VDF_TWIndex_Daily.duckdb"

LAMPS = ("GREEN", "AMBER", "RED", "GRAY")
RANK = {"GREEN": 0, "AMBER": 1, "RED": 2, "GRAY": 1}


# ───────────────────────── 冊 ─────────────────────────
def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{4})\.", p.name)
    return int(m.group(1)) if m else -1


def tail(dirpath: Path, stem: str, ext: str = ".json") -> Path | None:
    """家族尾版(先解析再用,避免 PINVER:不把版號寫死在程式裡)。"""
    c = sorted(dirpath.glob(f"{stem}*{ext}"), key=_vnum)
    return c[-1] if c else None


def load_books(here: Path = HERE) -> tuple[dict, str, dict, str]:
    ip = tail(here, IN_SSOT_STEM)
    fp = tail(here, FETCH_SSOT_STEM)
    if ip is None:
        raise SystemExit(f"[紅] 找不到輸入範圍冊 {IN_SSOT_STEM}*.json")
    inb = json.loads(ip.read_text(encoding="utf-8"))
    fetch = json.loads(fp.read_text(encoding="utf-8")) if fp else {}
    return inb, ip.name, fetch, (fp.name if fp else "(缺)")


def inputs_by_id(inb: dict) -> dict[str, dict]:
    return {x["id"]: x for x in (inb.get("inputs") or []) if isinstance(x, dict) and x.get("id")}


def out01(inb: dict) -> dict:
    for o in (inb.get("outputs") or []):
        if isinstance(o, dict) and o.get("id") == "OUT-01":
            return o
    raise SystemExit("[紅] 冊上沒有 OUT-01(universe_list),無法知道該出哪些欄")


# ───────────────────────── ① 代號路由 ─────────────────────────
def index_aliases(in03: dict) -> dict[str, dict]:
    """指數代號的別名表全部來自冊 members:code · yf_proxy · zh 都當得了輸入。"""
    out: dict[str, dict] = {}
    for m in (in03.get("members") or []):
        if not isinstance(m, dict) or not m.get("code"):
            continue
        for k in (m.get("code"), m.get("yf_proxy"), m.get("zh")):
            if k:
                out[str(k).upper()] = m
    return out


def classify(code: str, ins: dict) -> dict:
    """一個代號 → 它是哪一型。認不出來回 UNKNOWN,不猜、不模糊比對。

    次序刻意是 指數 → 主動 ETF → 個股:指數是列舉的,比正則確定;
    而 ^[1-9][0-9]{3}$ 不會吃到 00xxxA(開頭 0 被排除),兩條正則互不重疊。
    """
    raw = str(code).strip()
    up = raw.upper()
    in01, in02, in03 = ins.get("IN-01", {}), ins.get("IN-02", {}), ins.get("IN-03", {})
    al = index_aliases(in03)
    if up in al:
        m = al[up]
        return {"code_in": raw, "type": "IN-03", "group": in03.get("group", "TW_INDEX"),
                "code": m["code"], "name": m.get("zh", ""), "market": m.get("market", ""),
                "yf_ticker": m.get("yf_proxy", ""), "bb_ticker": "",
                "truth": in03.get("truth", ""), "zh": in03.get("zh", "")}
    if re.match(str(in02.get("code_regex") or r"^00[0-9]{3}A$"), up):
        return {"code_in": raw, "type": "IN-02", "group": in02.get("group", "TW_ACTIVE_EQUITY_ETF"),
                "code": up, "name": "", "market": "TWSE",
                "yf_ticker": up + ".TW", "bb_ticker": up + " TT",
                "truth": in02.get("truth", ""), "zh": in02.get("zh", "")}
    if re.match(str(in01.get("code_regex") or r"^[1-9][0-9]{3}$"), raw):
        return {"code_in": raw, "type": "IN-01", "group": in01.get("group", "TW_STOCK"),
                "code": raw, "name": "", "market": "",
                "yf_ticker": raw + ".TW", "bb_ticker": raw + " TT",
                "truth": in01.get("truth", ""), "zh": in01.get("zh", "")}
    return {"code_in": raw, "type": "UNKNOWN", "group": "", "code": raw, "name": "", "market": "",
            "yf_ticker": "", "bb_ticker": "", "truth": "",
            "zh": "三型都不合(個股 ^[1-9][0-9]{3}$ · 主動 ETF ^00[0-9]{3}A$ · 指數 TAIEX / TPEX)—— 不猜"}


# ───────────────────────── ② 來源梯子 ─────────────────────────
def _duckdb():
    try:
        import duckdb
        return duckdb
    except Exception:
        return None


def _db_rows(db: Path, sql: str) -> tuple[list, str]:
    """唯讀查真相庫。庫不在 / duckdb 缺 / 查不動 → 一律回 ([], 原因),不假填。"""
    if not db.is_file():
        return [], f"ABSENT:{db.name} 不在"
    d = _duckdb()
    if d is None:
        return [], "ABSENT:本機沒有 duckdb(冊上是 base/engine_core,屬 R2 待裝)"
    try:
        con = d.connect(str(db), read_only=True)
        try:
            return list(con.execute(sql).fetchall()), "LIVE_DB"
        finally:
            con.close()
    except Exception as e:
        return [], f"ABSENT:查庫失敗 {type(e).__name__}: {e}"


def _seed(path: Path, key: str) -> tuple[list, dict]:
    if not path.is_file():
        return [], {"state": f"ABSENT:{path.name} 不在"}
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return [], {"state": f"ABSENT:讀不動 {type(e).__name__}"}
    rows = d.get(key) or []
    return (rows if isinstance(rows, list) else []), {
        "state": "SEED_BOOK", "book": path.name, "as_of": d.get("as_of", ""),
        "note": str(d.get("note", ""))[:160]}


def group_stock(ins: dict) -> dict:
    in01 = ins.get("IN-01", {})
    rows, st = _db_rows(DB_MARKET, "SELECT ticker, name, market, industry FROM tw_listings_industry")
    if st == "LIVE_DB":
        out = [{"code": str(r[0]), "name": str(r[1] or ""), "market": str(r[2] or ""),
                "industry": str(r[3] or ""), "source": "LIVE_DB", "state": "LISTED"} for r in rows]
        return {"id": "IN-01", "rows": out, "source": "LIVE_DB", "meta": {"db": DB_MARKET.name}}
    seed, meta = _seed(SEED_EQ, "equities")
    if seed:
        out = [{"code": str(r.get("ticker", "")), "name": str(r.get("name", "")),
                "market": str(r.get("market", "")), "industry": "",
                "source": "SEED_BOOK", "state": str(r.get("status", "SEED"))} for r in seed]
        return {"id": "IN-01", "rows": out, "source": "SEED_BOOK", "meta": meta}
    return {"id": "IN-01", "rows": [], "source": "ABSENT",
            "meta": {"state": st, "hint": "先跑 E-01 ENG055 L1 lane_listings(要同意閘)"}}


def group_etf(ins: dict) -> dict:
    rows, st = _db_rows(DB_ETF, "SELECT ticker, name, issuer, verified FROM active_tw_etf_registry")
    if st == "LIVE_DB":
        out = [{"code": str(r[0]), "name": str(r[1] or ""), "issuer": str(r[2] or ""),
                "verified": bool(r[3]), "source": "LIVE_DB", "state": "ACTIVE"} for r in rows]
        return {"id": "IN-02", "rows": out, "source": "LIVE_DB", "meta": {"db": DB_ETF.name}}
    seed, meta = _seed(SEED_ETF, "etfs")
    if seed:
        out = []
        for r in seed:
            stt = str(r.get("status", ""))
            out.append({"code": str(r.get("ticker", "")),
                        "name": str(r.get("official_name") or r.get("name") or ""),
                        "issuer": str(r.get("issuer", "")),
                        # 只有 OpenAPI 真的驗過的才算 verified;PENDING / MISMATCH 一律 False
                        "verified": stt == "VERIFIED_OPENAPI",
                        "source": "SEED_BOOK", "state": stt or "UNKNOWN"})
        meta["verified_openapi"] = sum(1 for r in out if r["verified"])
        meta["not_verified"] = len(out) - meta["verified_openapi"]
        return {"id": "IN-02", "rows": out, "source": "SEED_BOOK", "meta": meta}
    return {"id": "IN-02", "rows": [], "source": "ABSENT",
            "meta": {"state": st, "hint": "先跑 E-02 ENG077 / 擷取 010(要同意閘)"}}


def group_index(ins: dict) -> dict:
    in03 = ins.get("IN-03", {})
    members = [m for m in (in03.get("members") or []) if isinstance(m, dict) and m.get("code")]
    rows, st = _db_rows(DB_INDEX, "SELECT index_code, index_name, MAX(date) FROM tw_index_daily GROUP BY 1,2")
    have = {str(r[0]): (str(r[1] or ""), str(r[2] or "")) for r in rows} if st == "LIVE_DB" else {}
    out = []
    for m in members:
        c = str(m["code"])
        nm, last = have.get(c, ("", ""))
        out.append({"code": c, "name": nm or m.get("zh", ""), "market": m.get("market", ""),
                    "yf_ticker": m.get("yf_proxy", ""), "last_date": last,
                    "source": "LIVE_DB" if c in have else "BOOK_STATIC",
                    "state": "HAS_DAILY" if c in have else "DECLARED_NO_DAILY"})
    src = "LIVE_DB" if have and len(have) >= len(members) else ("MIXED" if have else "BOOK_STATIC")
    return {"id": "IN-03", "rows": out, "source": src,
            "meta": {"db": DB_INDEX.name, "db_state": st, "declared": len(members), "with_daily": len(have)}}


# ───────────────────────── ③ 一個指令:併成 OUT-01 + 驗 ─────────────────────────
def assemble(groups: list[dict], inb: dict) -> list[dict]:
    """照冊 OUT-01 的 columns 出列。冊上有的欄才出,冊上沒有的不自己加。"""
    cols = [c["key"] for c in (out01(inb).get("columns") or [])]
    rows, seq = [], 0
    for g in groups:
        for r in g["rows"]:
            seq += 1
            base = {
                "seq": seq, "group": g["id"], "code": r.get("code", ""), "name": r.get("name", ""),
                "market": r.get("market", ""),
                "yf_ticker": r.get("yf_ticker", (r.get("code", "") + ".TW") if g["id"] != "IN-03" else ""),
                "bb_ticker": r.get("bb_ticker", (r.get("code", "") + " TT") if g["id"] != "IN-03" else ""),
                "industry": r.get("industry", ""), "issuer": r.get("issuer", ""),
                "verified": r.get("verified", None), "last_holdings_date": r.get("last_date", ""),
                "source": r.get("source", g.get("source", "")), "state": r.get("state", ""),
            }
            rows.append({k: base.get(k, "") for k in cols} if cols else base)
    return rows


def validate(rows: list[dict], groups: list[dict], inb: dict) -> dict:
    """驗證律全部照冊 validation.per_output['OUT-01'],一條一盞燈,每盞都附證據。"""
    ins = inputs_by_id(inb)
    o1 = out01(inb)
    checks: list[dict] = []
    gm = {g["id"]: g for g in groups}

    def add(cid, name, lamp, note):
        checks.append({"id": cid, "name": name, "lamp": lamp, "note": note})

    # V1 三組都有來源(ABSENT 就是 RED,不假填)
    absent = [g["id"] for g in groups if g["source"] == "ABSENT"]
    add("V1", "三組都有來源", "RED" if absent else "GREEN",
        "ABSENT " + ("、".join(absent) if absent else "無") + " · 來源 "
        + " · ".join(f"{g['id']}={g['source']}" for g in groups))

    # V2 個股代碼律
    rx1 = str(ins.get("IN-01", {}).get("code_regex") or r"^[1-9][0-9]{3}$")
    bad1 = [r["code"] for r in rows if r.get("group") == "IN-01" and not re.match(rx1, str(r.get("code", "")))]
    add("V2", f"個股代碼律 {rx1}", "RED" if bad1 else "GREEN", f"違律 {bad1[:5]} / 共 {len(bad1)}")

    # V3 主動 ETF 代碼律 + 持股已驗證
    rx2 = str(ins.get("IN-02", {}).get("code_regex") or r"^00[0-9]{3}A$")
    e = [r for r in rows if r.get("group") == "IN-02"]
    bad2 = [r["code"] for r in e if not re.match(rx2, str(r.get("code", "")).upper())]
    add("V3", f"主動 ETF 代碼律 {rx2}", "RED" if bad2 else "GREEN", f"違律 {bad2[:5]} / 共 {len(bad2)}")
    nv = [r["code"] for r in e if r.get("verified") is not True]
    add("V4", "主動 ETF 持股已驗證", "AMBER" if nv else ("GREEN" if e else "RED"),
        f"已驗 {len(e) - len(nv)} · 未驗 {len(nv)}{(' 例 ' + str(nv[:5])) if nv else ''}")

    # V5 家數下限(冊 IN-01.floor):任一所 0 家 = RED,低於下限 = AMBER
    fl = ins.get("IN-01", {}).get("floor") or {}
    cnt = {}
    for r in rows:
        if r.get("group") == "IN-01":
            cnt[str(r.get("market", "") or "?")] = cnt.get(str(r.get("market", "") or "?"), 0) + 1
    worst, notes = "GREEN", []
    for mk in ("TWSE", "TPEX"):
        n, lim = cnt.get(mk, 0), int(fl.get(mk, 0) or 0)
        lamp = "RED" if n == 0 else ("AMBER" if lim and n < lim else "GREEN")
        notes.append(f"{mk} {n} 家 / 下限 {lim} → {lamp}")
        worst = lamp if RANK[lamp] > RANK[worst] else worst
    add("V5", "加權 / 櫃買家數下限", worst, " · ".join(notes))

    # V6 指數兩列都在
    ic = {str(r.get("code", "")) for r in rows if r.get("group") == "IN-03"}
    want = {str(m.get("code")) for m in (ins.get("IN-03", {}).get("members") or []) if isinstance(m, dict)}
    miss = sorted(want - ic)
    add("V6", "指數 TAIEX · TPEX 兩列都在", "RED" if miss else "GREEN", f"缺 {miss}" if miss else f"在 {sorted(ic)}")

    # V7 不重號(冊 keys = group + code)
    keys = [tuple(str(r.get(k, "")) for k in (o1.get("keys") or ["group", "code"])) for r in rows]
    dup = sorted({k for k in keys if keys.count(k) > 1})
    add("V7", "主鍵不重(" + "+".join(o1.get("keys") or []) + ")", "RED" if dup else "GREEN",
        f"重 {dup[:5]} / 共 {len(dup)}")

    # V8 必填欄在且不空
    req = o1.get("required") or []
    hole = [(r.get("group"), r.get("code"), k) for r in rows for k in req
            if r.get(k, "") in ("", None)]
    add("V8", "必填欄不空(" + "、".join(req) + ")", "RED" if hole else "GREEN",
        f"缺 {hole[:3]} / 共 {len(hole)}")

    # V9 最少列數
    mn = int(o1.get("min_rows") or 0)
    add("V9", f"列數 ≥ 冊上最少 {mn}", "GREEN" if len(rows) >= mn else "AMBER",
        f"實際 {len(rows)} 列" + ("" if len(rows) >= mn else " —— 上游真相庫還沒建起來,不是本支算錯"))

    # V10 種子冊天花板:用到 SEED_BOOK 的組,就不給綠
    seeded = [g["id"] for g in groups if g["source"] == "SEED_BOOK"]
    add("V10", "來源層級(SEED_BOOK 不算當日官方真相)", "AMBER" if seeded else "GREEN",
        ("用了種子冊:" + "、".join(f"{i}({gm[i]['meta'].get('as_of', '?')})" for i in seeded)
         + " —— 驗證時間不是今天,燈頂到 AMBER") if seeded else "三組都不是種子冊")

    lamp = "GREEN"
    for c in checks:
        if RANK[c["lamp"]] > RANK[lamp]:
            lamp = c["lamp"]
    return {"checks": checks, "lamp": lamp}


def build(apply: bool = False, here: Path = HERE, out_root: Path | None = None) -> dict:
    inb, in_name, fetch, fetch_name = load_books(here)
    ins = inputs_by_id(inb)
    groups = [group_stock(ins), group_etf(ins), group_index(ins)]
    rows = assemble(groups, inb)
    v = validate(rows, groups, inb)
    net = _via_net()
    rep = {
        "schema": SCHEMA, "engine": TAG, "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "books": {"input_universe": in_name, "fetch_system": fetch_name},
        "lamp": v["lamp"], "checks": v["checks"], "count": len(rows),
        "groups": [{"id": g["id"], "source": g["source"], "rows": len(g["rows"]), "meta": g["meta"]} for g in groups],
        "net_gate": {"consent_env": "VIA_NET_CONSENT",
                     "set_here": bool(os.environ.get("VIA_NET_CONSENT")),
                     "tool": ("在位" if net else "缺席"),
                     "note": "本支零外呼;抓資料是 009 / 010 / e232 的事,閘由操作員開"},
        "refresh_plan": plan_steps(fetch),
        "rows": rows,
    }
    if apply:
        root = Path(out_root or VIA)
        d = root / OUT_REL
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{BOOK_STEM}{_next_vnum(d):04d}.json"
        p.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        rep["written"] = str(p)
    return rep


def _next_vnum(d: Path) -> int:
    t = tail(d, BOOK_STEM)
    return (_vnum(t) + 1) if t is not None else 100


def plan_steps(fetch: dict) -> list[dict]:
    """重抓次序照冊 VDF_FetchSystem_SSOT 的 needs 拓撲,不是我排的。"""
    want = {"009", "010", "e232"}
    es = {e["id"]: e for e in (fetch.get("engines") or []) if isinstance(e, dict) and e.get("id") in want}
    order, placed = [], set()
    for _ in range(len(es) + 1):
        for i, e in es.items():
            if i in placed:
                continue
            if all(n in placed or n not in want for n in (e.get("needs") or [])):
                order.append(i)
                placed.add(i)
    return [{"id": i, "mdl": es[i].get("mdl", ""), "file": es[i].get("file", ""),
             "needs": es[i].get("needs", []), "run_args": es[i].get("run_args", ["run"]),
             "role": str(es[i].get("role", ""))[:90]} for i in order]


# ───────────────────────── info:代號 → 相關資訊 ─────────────────────────
def info(codes: list[str], here: Path = HERE) -> dict:
    inb, in_name, fetch, _ = load_books(here)
    ins = inputs_by_id(inb)
    groups = {g["id"]: g for g in (group_stock(ins), group_etf(ins), group_index(ins))}
    idx = {}
    for gid, g in groups.items():
        for r in g["rows"]:
            idx[(gid, str(r.get("code", "")).upper())] = r
    lanes = {e["id"]: e for e in (fetch.get("engines") or []) if isinstance(e, dict)}
    by_in = {"IN-01": "009", "IN-02": "010", "IN-03": "e232"}
    out = []
    for c in codes:
        r = classify(c, ins)
        hit = idx.get((r["type"], str(r["code"]).upper()))
        lane = lanes.get(by_in.get(r["type"], ""), {})
        r["present"] = bool(hit)
        r["present_source"] = (hit or {}).get("source", "")
        r["present_state"] = (hit or {}).get("state", "")
        if hit and hit.get("name") and not r["name"]:
            r["name"] = hit["name"]
        if hit and hit.get("market") and not r["market"]:
            r["market"] = hit["market"]
        r["fetched_by"] = {"id": lane.get("id", ""), "mdl": lane.get("mdl", ""), "file": lane.get("file", "")}
        r["group_source"] = groups.get(r["type"], {}).get("source", "")
        out.append(r)
    return {"schema": SCHEMA, "engine": TAG, "book": in_name, "codes": out,
            "note": "present=False 只代表「這台機器上這一組的料還沒建起來」,不是代號不存在"}


# ───────────────────────── U/I ─────────────────────────
def ui_html(rep: dict) -> str:
    e = html.escape
    chips = [("總燈", rep["lamp"]), ("列數", rep["count"])]
    for g in rep["groups"]:
        chips.append((g["id"], f"{g['rows']} · {g['source']}"))
    cls = {"GREEN": "ok", "AMBER": "yel", "RED": "red", "GRAY": "gry"}
    ck = "".join("<tr><td class='m'>%s</td><td class='%s'>%s</td><td>%s</td><td class='s'>%s</td></tr>"
                 % (e(c["id"]), cls.get(c["lamp"], "gry"), e(c["lamp"]), e(c["name"]), e(c["note"]))
                 for c in rep["checks"])
    gr = "".join("<tr><td class='m'>%s</td><td class='m'>%s</td><td>%d</td><td class='s'>%s</td></tr>"
                 % (e(g["id"]), e(g["source"]), g["rows"], e(json.dumps(g["meta"], ensure_ascii=False)[:200]))
                 for g in rep["groups"])
    pl = "".join("<tr><td class='m'>%s</td><td class='m'>%s</td><td class='s'>%s</td><td class='s'>%s</td></tr>"
                 % (e(s["id"]), e(s["mdl"]), e(" ".join(s["needs"]) or "—"), e(s["file"]))
                 for s in rep["refresh_plan"])
    head = [c["key"] if isinstance(c, dict) else c for c in (rep["rows"][0].keys() if rep["rows"] else [])]
    th = "".join(f"<th>{e(str(h))}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td class='s'>{e(str(r.get(h, '')))}</td>" for h in head) + "</tr>"
                 for r in rep["rows"][:300])
    return f"""<title>VDF 三代號宇宙</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root{{--vl-bg:#f7f8fa;--vl-white:#fff;--vl-ink:#15181d;--vl-muted:#5b6472;
--vl-border:#d8dde5;--vl-border-soft:#eceff4;--vl-row:#fafbfd;
--vl-success-bg:#e8f6ee;--vl-success-ink:#0f5c37;
--vl-warning-bg:#fdf4e3;--vl-warning-ink:#7a5410;
--vl-danger-bg:#fdecec;--vl-danger-ink:#8d1f1f;
--vl-font-cjk:"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;
--vl-font-mono:ui-monospace,SFMono-Regular,Menlo,monospace;
--vl-size-title:20px;--vl-size-primary:15px;--vl-size-base:13px;--vl-size-label:11px;
color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
--vl-bg:#111419;--vl-white:#181c22;--vl-ink:#e7ebf1;--vl-muted:#9aa5b4;
--vl-border:#2b313a;--vl-border-soft:#22272e;--vl-row:#1d2128;
--vl-success-bg:#12301f;--vl-success-ink:#7fd6a4;
--vl-warning-bg:#332a12;--vl-warning-ink:#e8c377;
--vl-danger-bg:#3a1a1a;--vl-danger-ink:#f0a0a0;color-scheme:dark}}}}
:root[data-theme="dark"]{{--vl-bg:#111419;--vl-white:#181c22;--vl-ink:#e7ebf1;--vl-muted:#9aa5b4;
--vl-border:#2b313a;--vl-border-soft:#22272e;--vl-row:#1d2128;
--vl-success-bg:#12301f;--vl-success-ink:#7fd6a4;
--vl-warning-bg:#332a12;--vl-warning-ink:#e8c377;
--vl-danger-bg:#3a1a1a;--vl-danger-ink:#f0a0a0;color-scheme:dark}}
body{{background:var(--vl-bg);color:var(--vl-ink);font-family:var(--vl-font-cjk);
font-size:var(--vl-size-base);margin:0}}
.wrap{{padding-left:max(16px,env(safe-area-inset-left,0px));
padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:24px;max-width:1180px;margin:0 auto}}
h1{{font-size:var(--vl-size-title);margin:0 0 4px;text-wrap:balance}}
.sub{{color:var(--vl-muted);font-size:var(--vl-size-label);margin-bottom:16px}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}}
.chip{{background:var(--vl-white);border:1px solid var(--vl-border);border-radius:8px;padding:8px 12px;min-width:0}}
.chip b{{display:block;font-size:var(--vl-size-primary);font-family:var(--vl-font-mono)}}
.chip span{{color:var(--vl-muted);font-size:var(--vl-size-label);letter-spacing:.04em}}
.card{{background:var(--vl-white);border:1px solid var(--vl-border);border-radius:10px;
padding:14px;margin-bottom:16px;min-width:0}}
h2{{font-size:var(--vl-size-primary);margin:0 0 10px}}
.scroll{{overflow-x:auto}}
table{{border-collapse:collapse;width:100%;font-size:var(--vl-size-base)}}
th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--vl-border-soft);vertical-align:top}}
th{{color:var(--vl-muted);font-size:var(--vl-size-label);letter-spacing:.04em;white-space:nowrap}}
tr:nth-child(even) td{{background:var(--vl-row)}}
td.m{{font-family:var(--vl-font-mono);white-space:nowrap}}
td.s{{color:var(--vl-muted);font-size:var(--vl-size-label)}}
td.ok{{background:var(--vl-success-bg);color:var(--vl-success-ink);font-weight:700}}
td.yel{{background:var(--vl-warning-bg);color:var(--vl-warning-ink);font-weight:700}}
td.red{{background:var(--vl-danger-bg);color:var(--vl-danger-ink);font-weight:700}}
td.gry{{color:var(--vl-muted)}}
.note{{color:var(--vl-muted);font-size:var(--vl-size-label);line-height:1.6}}
</style>
<div class="wrap">
<h1>VDF 三代號宇宙</h1>
<div class="sub">{e(rep['engine'])} · 冊 {e(rep['books']['input_universe'])} / {e(rep['books']['fetch_system'])} · {e(rep['built_at'])}</div>
<div class="chips">{''.join(f'<div class="chip"><b>{e(str(v))}</b><span>{e(str(k))}</span></div>' for k, v in chips)}</div>
<div class="card"><h2>OUT-01 驗證律(全部照冊)</h2><div class="scroll"><table>
<thead><tr><th>#</th><th>燈</th><th>檢</th><th>證據</th></tr></thead><tbody>{ck}</tbody></table></div></div>
<div class="card"><h2>三組來源梯子</h2><div class="scroll"><table>
<thead><tr><th>組</th><th>來源</th><th>列</th><th>細節</th></tr></thead><tbody>{gr}</tbody></table></div></div>
<div class="card"><h2>重抓次序(照冊 needs 拓撲)</h2><div class="scroll"><table>
<thead><tr><th>站</th><th>模組</th><th>needs</th><th>檔</th></tr></thead><tbody>{pl}</tbody></table></div></div>
<div class="card"><h2>清單(前 300 列)</h2><div class="scroll"><table>
<thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div></div>
<div class="card"><h2>沒量到的照實留白</h2>
<p class="note">同意閘 {e(str(rep['net_gate']['consent_env']))}:本機 {'有設' if rep['net_gate']['set_here'] else '沒設'} ·
網路工具 {e(rep['net_gate']['tool'])}。{e(rep['net_gate']['note'])}<br>
SEED_BOOK 是倉內已驗證的種子冊,驗證時間不是今天,所以用到它的組燈頂到 AMBER。<br>
ABSENT 一律不假填。AMBER 不是綠,RED 也不會被改寫成黃。</p></div>
</div>
"""


# ───────────────────────── 自測 ─────────────────────────
def selftest() -> int:
    ok = fail = 0

    def chk(name, cond, extra=""):
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"  ✔ {name}")
        else:
            fail += 1
            print(f"  ✘ {name}{(' —— ' + str(extra)) if extra else ''}")

    print(f"[{TAG} 自測]")
    inb, in_name, fetch, fetch_name = load_books()
    ins = inputs_by_id(inb)

    # ① 冊真的讀到了三組
    chk("① 冊上三組都在(IN-01 / IN-02 / IN-03)", all(k in ins for k in ("IN-01", "IN-02", "IN-03")), sorted(ins))
    chk("② OUT-01 欄位 / 主鍵 / 必填 / 最少列全讀到",
        bool(out01(inb).get("columns")) and bool(out01(inb).get("keys")) and out01(inb).get("min_rows"))

    # ③ 代號路由:三型正例 + 冊自己的反例
    for c, t in (("2330", "IN-01"), ("1101", "IN-01"), ("9958", "IN-01"),
                 ("00980A", "IN-02"), ("00981A", "IN-02"),
                 ("TAIEX", "IN-03"), ("TPEX", "IN-03"), ("^TWII", "IN-03"), ("加權指數", "UNKNOWN")):
        r = classify(c, ins)
        chk(f"③ {c} → {t}", r["type"] == t, r["type"])
    chk("③b 冊上 IN-03 的中文名也認得(發行量加權股價指數)",
        classify("發行量加權股價指數", ins)["type"] == "IN-03")

    # ④ 冊自己寫的反例一個都不能被收進去
    for c in (ins["IN-01"].get("code_regex_negative") or []):
        chk(f"④ 個股反例 {c} 不得判成 IN-01", classify(c, ins)["type"] != "IN-01", classify(c, ins)["type"])
    for c in (ins["IN-02"].get("code_regex_negative") or []):
        chk(f"④ ETF 反例 {c} 不得判成 IN-02", classify(c, ins)["type"] != "IN-02", classify(c, ins)["type"])
    chk("④b 兩條正則互不重疊(0050 不是個股也不是主動 ETF)",
        classify("0050", ins)["type"] == "UNKNOWN")
    chk("④c 認不出來寫 UNKNOWN 並說明三型,不猜",
        classify("ZZZZ", ins)["type"] == "UNKNOWN" and "不猜" in classify("ZZZZ", ins)["zh"])

    # ⑤ 來源梯子:庫不在 → 退種子冊 → 標 SEED_BOOK(不冒充 LIVE_DB)
    g2 = group_etf(ins)
    chk("⑤ 主動 ETF 庫不在時退到倉內種子冊", g2["source"] in ("LIVE_DB", "SEED_BOOK"), g2["source"])
    if g2["source"] == "SEED_BOOK":
        chk("⑤b 種子冊標了 as_of(驗證時間看得見)", bool(g2["meta"].get("as_of")), g2["meta"])
        chk("⑤c 只有 VERIFIED_OPENAPI 才算已驗證",
            g2["meta"].get("verified_openapi", 0) > 0
            and g2["meta"]["verified_openapi"] + g2["meta"]["not_verified"] == len(g2["rows"]),
            g2["meta"])
        chk("⑤d 未驗的沒有被寫成 verified=True",
            all(r["verified"] is (r["state"] == "VERIFIED_OPENAPI") for r in g2["rows"]))

    # ⑥ 指數組:冊上宣告的兩個一定在,沒日資料就標 DECLARED_NO_DAILY
    g3 = group_index(ins)
    codes3 = {r["code"] for r in g3["rows"]}
    chk("⑥ 指數兩個都在(TAIEX · TPEX)", {"TAIEX", "TPEX"} <= codes3, codes3)
    chk("⑥b 沒有日資料的指數照實標 DECLARED_NO_DAILY,不假裝有",
        all(r["state"] in ("HAS_DAILY", "DECLARED_NO_DAILY") for r in g3["rows"]))

    # ⑦ 併表照冊欄位,不自己加欄
    cols = [c["key"] for c in out01(inb)["columns"]]
    rows = assemble([g2, g3], inb)
    chk("⑦ 併出來的欄位 = 冊上 OUT-01 欄位(不多不少)",
        rows and list(rows[0].keys()) == cols, (list(rows[0].keys()) if rows else None))
    chk("⑦b seq 連號從 1 起", [r["seq"] for r in rows] == list(range(1, len(rows) + 1)))

    # ⑧ 驗證律:夾具跑正反面
    def fx(stock_rows, etf_rows, idx_rows, s1="LIVE_DB", s2="LIVE_DB", s3="LIVE_DB"):
        return [{"id": "IN-01", "rows": stock_rows, "source": s1, "meta": {}},
                {"id": "IN-02", "rows": etf_rows, "source": s2, "meta": {}},
                {"id": "IN-03", "rows": idx_rows, "source": s3, "meta": {}}]

    good_idx = [{"code": "TAIEX", "name": "發行量加權股價指數", "market": "TWSE", "state": "HAS_DAILY"},
                {"code": "TPEX", "name": "櫃買指數", "market": "TPEX", "state": "HAS_DAILY"}]
    many_tw = [{"code": str(1000 + i), "name": f"股{i}", "market": "TWSE", "state": "LISTED"} for i in range(900)]
    many_tp = [{"code": str(3000 + i), "name": f"櫃{i}", "market": "TPEX", "state": "LISTED"} for i in range(700)]
    good_etf = [{"code": "00980A", "name": "x", "issuer": "y", "verified": True, "state": "ACTIVE"}]

    def lamps(gs):
        gg = gs
        rr = assemble(gg, inb)
        v = validate(rr, gg, inb)
        return v["lamp"], {c["id"]: c["lamp"] for c in v["checks"]}

    lp, cc = lamps(fx(many_tw + many_tp, good_etf, good_idx))
    chk("⑧ 全合規(900+700 家 · 已驗 ETF · 兩指數)→ 總燈 GREEN", lp == "GREEN", cc)
    lp, cc = lamps(fx([], good_etf, good_idx))
    chk("⑨ 個股 0 家 → V5 RED", cc["V5"] == "RED" and lp == "RED")
    lp, cc = lamps(fx(many_tw[:10] + many_tp[:10], good_etf, good_idx))
    chk("⑩ 家數低於下限 → V5 AMBER(不是紅,也不是綠)", cc["V5"] == "AMBER")
    lp, cc = lamps(fx(many_tw + many_tp, good_etf, good_idx[:1]))
    chk("⑪ 指數少一個 → V6 RED", cc["V6"] == "RED" and lp == "RED")
    lp, cc = lamps(fx(many_tw + many_tp, [{"code": "0050", "name": "x", "verified": True, "state": "A"}], good_idx))
    chk("⑫ ETF 違代碼律 → V3 RED", cc["V3"] == "RED")
    lp, cc = lamps(fx(many_tw + many_tp, [{"code": "00980A", "name": "x", "verified": False, "state": "PENDING"}], good_idx))
    chk("⑬ ETF 未驗證 → V4 AMBER(不浮報成紅,也不給綠)", cc["V4"] == "AMBER")
    lp, cc = lamps(fx([{"code": "9999", "name": "a", "market": "TWSE", "state": "L"}] * 2 + many_tw + many_tp,
                      good_etf, good_idx))
    chk("⑭ 主鍵重號 → V7 RED", cc["V7"] == "RED")
    lp, cc = lamps(fx(many_tw + many_tp, [{"code": "00980A", "name": "", "verified": True, "state": "A"}], good_idx))
    chk("⑮ 必填 name 空 → V8 RED", cc["V8"] == "RED")
    lp, cc = lamps(fx(many_tw + many_tp, good_etf, good_idx, s1="ABSENT"))
    chk("⑯ 任一組 ABSENT → V1 RED", cc["V1"] == "RED" and lp == "RED")
    lp, cc = lamps(fx(many_tw + many_tp, good_etf, good_idx, s2="SEED_BOOK"))
    chk("⑰ 用了種子冊 → V10 AMBER 天花板(全合規也不給綠)", cc["V10"] == "AMBER" and lp == "AMBER")
    lp, cc = lamps(fx(many_tw[:5], good_etf, good_idx))
    chk("⑱ 列數不足 → V9 AMBER 且註明是上游沒建起來", cc["V9"] == "AMBER")

    # ⑲ 重抓次序照冊 needs,不是我排的
    st = plan_steps(fetch)
    ids = [s["id"] for s in st]
    chk("⑲ 重抓次序含三站", set(ids) == {"009", "010", "e232"}, ids)
    chk("⑳ e232 排在 009 / 010 之後(冊上 needs 說的)",
        ids.index("e232") > ids.index("009") and ids.index("e232") > ids.index("010"), ids)
    chk("㉑ needs 原文有被帶出來(不是我寫死的)",
        sorted(next(s for s in st if s["id"] == "e232")["needs"]) == ["009", "010"])

    # ㉒ 一個指令真的跑得起來(容器實跑,不寫檔)
    rep = build(apply=False)
    chk("㉒ build 跑完有總燈與三組", rep["lamp"] in LAMPS and len(rep["groups"]) == 3)
    chk("㉓ 本機沒設同意閘就照實記 set_here=False",
        rep["net_gate"]["set_here"] == bool(os.environ.get("VIA_NET_CONSENT")))
    chk("㉔ 報告帶冊名(可追)", rep["books"]["input_universe"] == in_name)

    # ㉕ info 路由
    i = info(["2330", "00980A", "TAIEX", "0050"])
    ty = [x["type"] for x in i["codes"]]
    chk("㉕ info 四個代號分別路由", ty == ["IN-01", "IN-02", "IN-03", "UNKNOWN"], ty)
    chk("㉖ info 每個都說得出誰負責抓",
        all(x["fetched_by"]["id"] for x in i["codes"] if x["type"] != "UNKNOWN"))
    chk("㉗ 本機沒料時 present=False,並說明那不代表代號不存在",
        all(isinstance(x["present"], bool) for x in i["codes"]) and "不是代號不存在" in i["note"])

    # ㉘ U/I 契約
    h = ui_html(build(apply=False))
    chk("㉘ U/I 不含骨架標籤", not any(t in h.lower() for t in ("<!doctype", "<html", "<body", "<head")))
    chk("㉙ U/I 色值只走 Atlas --vl-* 且兩主題都定義",
        h.count("--vl-") > 30 and "prefers-color-scheme" in h and 'data-theme="dark"' in h)
    hx = ui_html({**build(apply=False), "rows": [{"code": "<b>x</b>", "group": "IN-01"}],
                  "checks": [{"id": "V1", "name": "<i>n</i>", "lamp": "RED", "note": "<script>"}]})
    chk("㉚ U/I 逸出使用者內容", "<b>x</b>" not in hx and "&lt;b&gt;x&lt;/b&gt;" in hx)

    # ㉛ add-only:寫檔只往新版號,不覆蓋
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        r1 = build(apply=True, out_root=root)
        r2 = build(apply=True, out_root=root)
        n1, n2 = Path(r1["written"]).name, Path(r2["written"]).name
        chk("㉛ 第一次寫 v0100", n1.endswith("v0100.json"), n1)
        chk("㉜ 第二次出 v0101,不覆蓋 v0100", n2.endswith("v0101.json") and Path(r1["written"]).is_file(), n2)

    # ㉝–㉟ 三條禁令用 AST 檢,不用字面檢。
    # 字面檢在這裡是不成立的:這支檔的說明文和檢查式本身就寫著「不碰 TA-Lib」「pip install」
    # 「VIA_NET_CONSENT」這些字,字面檢會把「我宣告我不做」當成「我做了」——自己檢自己必紅。
    # 看 AST 才看得到真的有沒有做。
    import ast as _ast
    tree = _ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for n in _ast.walk(tree):
        if isinstance(n, _ast.Import):
            imported |= {al.name.split(".")[0].lower() for al in n.names}
        elif isinstance(n, _ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0].lower())
    chk("㉝ 不碰 TA-Lib(AST 匯入名裡沒有)",
        not {"talib", "ta_lib", "ta"} & imported, sorted(imported))
    chk("㉞ 不裝套件(AST 裡沒有 subprocess / os.system / runpy 這類派子行程的路)",
        not {"subprocess", "runpy"} & imported
        and not any(isinstance(n, _ast.Attribute) and n.attr in ("system", "popen", "execv", "spawnv")
                    for n in _ast.walk(tree)))
    wrote_env = []
    for n in _ast.walk(tree):
        # os.environ[...] = ... 這種寫法
        if isinstance(n, (_ast.Assign, _ast.AugAssign, _ast.AnnAssign)):
            tgts = n.targets if isinstance(n, _ast.Assign) else [n.target]
            for t in tgts:
                if isinstance(t, _ast.Subscript) and isinstance(t.value, _ast.Attribute) \
                        and t.value.attr == "environ":
                    wrote_env.append("environ[...] =")
        # os.environ.setdefault / os.putenv
        if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Attribute):
            if n.func.attr in ("setdefault", "update") and isinstance(n.func.value, _ast.Attribute) \
                    and n.func.value.attr == "environ":
                wrote_env.append("environ." + n.func.attr)
            if n.func.attr == "putenv":
                wrote_env.append("os.putenv")
    chk("㉟ 不代設同意閘(AST 裡沒有任何一處寫 environ)", not wrote_env, wrote_env)
    chk("㊱ environ 只被讀(get / 以 environ.get 取值)",
        any(isinstance(n, _ast.Call) and isinstance(n.func, _ast.Attribute) and n.func.attr == "get"
            and isinstance(n.func.value, _ast.Attribute) and n.func.value.attr == "environ"
            for n in _ast.walk(tree)))

    print(f"[計] {TAG} 自測 OK {ok} · FAIL {fail} · {'PASS' if fail == 0 else 'FAIL'}")
    return 0 if fail == 0 else 1


# ───────────────────────── 入口 ─────────────────────────
def _entry_ok() -> bool:
    return bool(os.environ.get("VIA_FROM_VDFSM") or os.environ.get("VIA_FROM_VCGC"))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    ap = argparse.ArgumentParser(prog=TAG, add_help=True)
    ap.add_argument("verb", nargs="?", default="build", choices=["classify", "build", "info", "plan", "ui"])
    ap.add_argument("codes", nargs="*")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(args)
    if not _entry_ok():
        print(f"[{TAG}] 拒絕。由 VDF System Manager 總控(或 VCGC):\n"
              f'  VIA_FROM_VDFSM=YES python3 "functional modules/VDF/VDF_MDL014_ThreeCodeUniverse_v0100.py" {a.verb}')
        return 2
    inb, _, fetch, _ = load_books()
    ins = inputs_by_id(inb)
    if a.verb == "classify":
        if not a.codes:
            print("[用法] classify <代號…>")
            return 2
        for c in a.codes:
            r = classify(c, ins)
            print(f"  {r['code_in']:>12} → {r['type']:8} {r['group']:22} {r['name'] or r['zh'][:40]}")
        return 0
    if a.verb == "info":
        if not a.codes:
            print("[用法] info <代號…>")
            return 2
        print(json.dumps(info(a.codes), ensure_ascii=False, indent=1))
        return 0
    if a.verb == "plan":
        for s in plan_steps(fetch):
            print(f"  {s['id']:5} {s['mdl']:26} needs={s['needs'] or '—'}  {s['file']}")
        print('  [閘] 實抓前操作員自己開:$env:VIA_NET_CONSENT = "YES"(本支不代設)')
        return 0
    rep = build(apply=a.apply)
    if a.verb == "ui":
        p = VIA / OUT_REL / UI_NAME
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(ui_html(rep), encoding="utf-8")
        print(f"[U/I] {p}")
        return 0
    print(f"[{TAG}] 總燈 {rep['lamp']} · 列 {rep['count']} · 冊 {rep['books']['input_universe']}")
    for g in rep["groups"]:
        print(f"  [{g['id']}] {g['rows']:>5} 列 · 來源 {g['source']:10} · {json.dumps(g['meta'], ensure_ascii=False)[:110]}")
    for c in rep["checks"]:
        print(f"  [{c['lamp']:5}] {c['id']:3} {c['name']} —— {c['note'][:150]}")
    if rep.get("written"):
        print(f"  [寫出] {rep['written']}")
    return 0 if rep["lamp"] in ("GREEN", "AMBER") else 1


if __name__ == "__main__":
    sys.exit(main())
