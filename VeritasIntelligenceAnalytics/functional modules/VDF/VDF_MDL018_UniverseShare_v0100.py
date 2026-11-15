#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL018_UniverseShare v0100 — 統一 SSOT 分享:VDF 三代號宇宙(個股 · 指數 · 主動式台股 ETF + 判定)一份 · sha 鎖 · 各系統只讀

操作員 2026-11-15:「實測出錯一切無誤後顯示於HTML介面,然後收工收尾儲存 然後把統一的S S O T分給其他系統看要在其他系統是怎麼展現」;
選定的統一 SSOT = VDF 三代號宇宙(VDF-REQ027)。
  來源   MDL014 ThreeCodeUniverse 尾版(OUT-01:三組合一 · 照冊驗證)+ MDL010 ActiveETFList 尾版(VDF-REQ026 判定:ENG051 最新一輪)。
         本支不抓資料、不改上游;上游燈照實帶進來(種子冊 = AMBER)。
  一份   rows 照分享冊 VDF_UniverseShare_SSOT 的欄;content_sha256 = rows 的標準 JSON(sort_keys · 不轉 ASCII · 緊湊)SHA-256。
         寫 VIA_Reports/vdf/universe_share/VDF_UniverseShare_v<NNNN>.json(只增)+ _latest.json(原子寫)+ U/I。
  只讀   VCGC · VRN-2 · VQG · VAP 讀 latest → verify(重算 sha)→ 一致才用;不回寫、不改 VDF 的檔。四系統互不干涉(L123):
         本支不寫他系統的程式或冊;U/I 只「預覽」各系統拿到的那一份(照冊 views:VCGC 燈與收據 · VRN-2 / VQG 列(只帶符合的 ETF)· VAP 彙總)。
  U/I    VDF 鎖定視覺規格(VDF_UI_VisualSpec_SSOT;css sha256 驗過才套)· 三行標頭 · 實測收據(handoff test)· 統一 SSOT 摘要 · 四系統預覽。
動詞:build [--apply] | view <VCGC|VRN-2|VQG|VAP> | ui | verify [檔](只讀,不需入口標記)| --selftest。
入口:VDF System Manager 總控(VIA_FROM_VDFSM=YES)或 VCGC。零網路 · 零安裝 · 不碰 TA-Lib · 同意閘不讀不寫 · 不寫環境。
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

import hashlib
import html
import importlib.util
import json
import os
import re
import sys
import warnings
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent                 # functional modules/VDF
VIA = HERE.parent.parent                               # VeritasIntelligenceAnalytics
TAG = "VDF_MDL018_UniverseShare v" + Path(__file__).stem.rsplit("_v", 1)[-1]
SCHEMA = "VIA.VDF.UniverseShare.v1"
BOOK_GLOB = "VDF_UniverseShare_SSOT_v*.json"
SPEC_GLOB = "VDF_UI_VisualSpec_SSOT_v*.json"
LAMP_ORDER = {"GREEN": 0, "YELLOW": 1, "AMBER": 1, "GRAY": 1, "RED": 2}


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _tail(pattern: str, folder: Path = HERE) -> Path | None:
    hits = [p for p in Path(folder).glob(pattern) if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        spec.loader.exec_module(mod)
    return mod


M14 = _load(_tail("VDF_MDL014_ThreeCodeUniverse_v*.py"), "vdf_mdl014_for_mdl018")   # 三代號宇宙(OUT-01)尾版
M10 = _load(_tail("VDF_MDL010_ActiveETFList_v*.py"), "vdf_mdl010_for_mdl018")       # 主動 ETF 判定(VDF-REQ026)尾版


def load_book(folder: Path = HERE) -> tuple:
    p = _tail(BOOK_GLOB, folder)
    if p is None:
        raise FileNotFoundError("分享冊 %s 不在 %s" % (BOOK_GLOB, folder))
    return json.loads(p.read_text(encoding="utf-8")), p.name


def canonical(rows: list) -> bytes:
    return json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def content_sha(rows: list) -> str:
    return hashlib.sha256(canonical(rows)).hexdigest()


def _worst(*lamps) -> str:
    out = "GREEN"
    for lp in lamps:
        lp = "YELLOW" if lp in ("AMBER", "GRAY") else (lp or "GREEN")
        if LAMP_ORDER.get(lp, 1) > LAMP_ORDER[out]:
            out = lp
    return out


def _etf_list_rows(today: str) -> list:
    """主動 ETF 的揭露類型(國內 / 國外成分)取 MDL010 最新清單;找不到 = None(判定時照 MDL010 律:沒紀錄 = 未判)。"""
    homes = []
    if os.environ.get("VIA_VDF_FETCH_HOME"):
        homes.append(Path(os.environ["VIA_VDF_FETCH_HOME"]))
    homes.append(VIA.joinpath("VIA_Reports", "vdf_fetch", "dict"))
    for h in homes:
        p = h / M10.OUT_DIR / f"{M10.STEM}_latest.parquet"
        if p.is_file():
            try:
                import pandas as pd
                return pd.read_parquet(p).to_dict("records")
            except Exception:  # noqa: BLE001 — 清單讀不了不擋分享:揭露類型照實留空
                return []
    return []


def build_share(today: str | None = None, list_rows: list | None = None) -> dict:
    """三代號宇宙(MDL014 尾版 OUT-01)+ 主動 ETF 判定(MDL010 尾版 V8)→ 一份統一 SSOT(內容 SHA-256 鎖)。"""
    book, book_name = load_book()
    today = today or date.today().isoformat()
    rep = M14.build()
    dom = {str(r.get("ticker", "")).upper(): r.get("domestic") for r in (list_rows if list_rows is not None else _etf_list_rows(today))}
    etf = [r for r in rep["rows"] if r.get("group") == "IN-02"]
    ev = M10.load_evidence()
    q = {x["ticker"]: x for x in M10.qualify([{"date": today, "ticker": r["code"], "name": r.get("name", ""),
                                               "domestic": dom.get(str(r["code"]).upper())} for r in etf], ev)}
    v8 = M10.check_v8(list(q.values()), ev)
    keys = [c["key"] for c in book["columns"]]
    rows = []
    for r in rep["rows"]:
        x = {k: r.get(k, "") for k in keys if k not in ("qualified", "qualify_reason")}
        hit = q.get(str(r.get("code", "")).upper()) if r.get("group") == "IN-02" else None
        x["qualified"] = hit["qualified"] if hit else None
        x["qualify_reason"] = hit["reason"] if hit else ""
        rows.append({k: x.get(k) for k in keys})
    by_group, by_market = {}, {}
    for r in rows:
        by_group[r["group"]] = by_group.get(r["group"], 0) + 1
        mk = r["market"] or "未標市場"
        by_market[mk] = by_market.get(mk, 0) + 1
    etf_q = {"qualified": sum(r["qualified"] is True for r in rows if r["group"] == "IN-02"),
             "not_qualified": sum(r["qualified"] is False for r in rows if r["group"] == "IN-02"),
             "undetermined": sum(r["qualified"] is None for r in rows if r["group"] == "IN-02")}
    bundle = {"schema": SCHEMA, "engine": TAG, "book": book_name, "owner": book["owner"], "rule": book["rule"],
              "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "date": today,
              "lamp": _worst(rep["lamp"], v8["lamp"]),
              "universe": {"engine": rep["engine"], "lamp": rep["lamp"], "books": rep["books"],
                           "groups": rep["groups"], "checks": [{k: c[k] for k in ("id", "name", "lamp", "note")} for c in rep["checks"]]},
              "qualify": {"engine": M10.TAG, "lamp": v8["lamp"], "note": v8["note"], "evidence": ev.get("source"),
                          "latest_run": ev.get("latest_run"), "error": ev.get("error")},
              "counts": {"total": len(rows), "by_group": by_group, "by_market": by_market, "etf": etf_q},
              "hash": dict(book["hash"], value=content_sha(rows)), "content_sha256": content_sha(rows), "rows": rows}
    return bundle


def verify(bundle_or_path) -> dict:
    """任何系統都可以叫(只讀):重算 rows 的 SHA-256,和 content_sha256 比。"""
    b = bundle_or_path
    if not isinstance(b, dict):
        b = json.loads(Path(b).read_text(encoding="utf-8"))
    got = content_sha(b.get("rows") or [])
    return {"identical": got == b.get("content_sha256"), "stored": b.get("content_sha256"), "computed": got,
            "rows": len(b.get("rows") or []), "version": b.get("version"), "built_at": b.get("built_at")}


def view(bundle: dict, system: str, book: dict | None = None) -> dict:
    """某系統拿到的那一份(照分享冊 views);只是投影,不改內容,sha 帶著走。"""
    book = book or load_book()[0]
    v = next((x for x in book["views"] if x["system"] == system or x.get("label") == system), None)
    if v is None:
        raise KeyError("分享冊沒有 %s 的 view" % system)
    out = {"system": v.get("label") or v["system"], "row1": book["header_row1"], "row2": v["row2"], "row3": v["row3"],
           "mode": v["mode"], "why": v.get("why", ""), "content_sha256": bundle["content_sha256"], "version": bundle.get("version")}
    if v["mode"] == "rows":
        rule = v.get("filter") or {}
        keep = [r for r in bundle["rows"] if not (rule.get(r["group"]) == "qualified_only" and r["qualified"] is not True)]
        out["columns"] = v["columns"]
        out["rows"] = [{k: r.get(k) for k in v["columns"]} for r in keep]
        out["dropped"] = {"etf_not_qualified_or_undetermined": len(bundle["rows"]) - len(keep)}
    elif v["mode"] == "aggregates":
        out["aggregates"] = {"by_group": bundle["counts"]["by_group"], "by_market": bundle["counts"]["by_market"],
                             "etf": bundle["counts"]["etf"]}
    else:
        out["manifest"] = {"lamp": bundle["lamp"], "built_at": bundle["built_at"], "counts": bundle["counts"],
                           "checks": bundle["universe"]["checks"], "qualify": bundle["qualify"]}
    return out


def receipts(cases: list, root: Path = VIA) -> list:
    """實測收據(handoff test 寫的);讀不到 = 照實寫「沒有收據」。"""
    out = []
    for c in cases:
        p = root / "docs" / "handoff" / "evidence" / f"{c}.json"
        if not p.is_file():
            out.append({"case": c, "rc": None, "marker": None, "at": "", "lamp": "GRAY", "note": "沒有收據(還沒跑 handoff test)"})
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except ValueError as exc:
            out.append({"case": c, "rc": None, "marker": None, "at": "", "lamp": "RED", "note": "收據壞:%s" % exc})
            continue
        ok = d.get("rc") == 0 and d.get("target_marker_seen") is True
        out.append({"case": c, "rc": d.get("rc"), "marker": d.get("target_marker_seen"), "at": d.get("completed_at", ""),
                    "lamp": "GREEN" if ok else "RED", "note": str(d.get("scope", ""))[:140]})
    return out


def _spec_css() -> tuple:
    p = _tail(SPEC_GLOB)
    if p is None:
        return "", "規格冊不在 → 無樣式(照實)"
    s = json.loads(p.read_text(encoding="utf-8"))
    css = s.get("css") or ""
    if hashlib.sha256(css.encode("utf-8")).hexdigest() != s.get("css_sha256"):
        return "", "規格冊 css 對不上鎖(sha256)→ 不套(照實黃)"
    return css, "%s · %s · sha256 驗過" % (p.name, s.get("style_id"))


def _lamp(lp: str) -> str:
    lp = "YELLOW" if lp == "AMBER" else lp
    return '<span class="us-lamp us-%s">%s</span>' % (html.escape(str(lp).lower()), html.escape(str(lp)))


def _table(cols: list, rows: list, limit: int = 60) -> str:
    e = html.escape
    head = "".join("<th>%s</th>" % e(str(c)) for c in cols)
    def cell(c, v):
        if c == "lamp" and v:
            return _lamp(str(v))
        return e("" if v is None else str(v))
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % cell(c, r.get(c)) for c in cols) for r in rows[:limit])
    more = '<p class="us-small">只列前 %d 列 · 共 %d 列</p>' % (limit, len(rows)) if len(rows) > limit else ""
    return '<div class="us-scroll"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>%s' % (head, body, more)


def _bars(d: dict) -> str:
    tot = max(sum(d.values()), 1)
    out = []
    for k, n in d.items():
        w = round(100.0 * n / tot, 1)
        out.append('<div class="us-bar"><span class="us-bar-k">%s</span><span class="us-bar-t"><span style="width:%s%%"></span></span>'
                   '<span class="us-bar-n">%d</span></div>' % (html.escape(str(k)), w, n))
    return "".join(out)


def _masthead(row1: str, row2: str, row3: str, badge: str = "") -> str:
    e = html.escape
    return ('<header class="us-head"><div class="us-r1">%s</div><div class="us-r2">%s%s</div><div class="us-r3">%s</div></header>'
            % (e(row1), e(row2), (' <span class="us-badge">%s</span>' % e(badge)) if badge else "", e(row3)))


EXTRA_CSS = (".us-head{margin:0 0 14px}.us-r1{font-size:10.5px;letter-spacing:.14em;color:#6b7468}.us-r2{font-size:21px;font-weight:600;"
             "margin:2px 0}.us-r3{font-size:11.5px;color:#55605a}.us-badge{font-size:10.5px;border:1px solid #dce1d5;border-radius:5px;padding:1px 6px;"
             "vertical-align:middle;color:#55605a}.us-lamp{display:inline-block;border-radius:5px;padding:0 6px;font-size:10.5px;color:#fff}"
             ".us-green{background:#16a34a}.us-yellow{background:#f59e0b}.us-red{background:#dc2626}.us-gray{background:#9ca3af}"
             ".us-sec{background:#fffefb;border:1px solid #dedfd5;border-radius:8px;padding:14px 16px;margin:0 0 14px}"
             ".us-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:14px}"
             ".us-pane{background:#f1f3ec;border:1px solid #dce1d5;border-radius:8px;padding:14px 16px;min-width:0}"
             ".us-small{font-size:10.5px;color:#6b7468}.us-scroll{overflow-x:auto;max-width:100%}.us-mono{font-family:ui-monospace,Consolas,monospace;"
             "word-break:break-all}.us-bar{display:flex;align-items:center;gap:8px;margin:4px 0}.us-bar-k{width:7em;font-size:11px}"
             ".us-bar-t{flex:1;height:10px;background:#eeeee7;border-radius:5px;overflow:hidden}.us-bar-t span{display:block;height:100%;"
             "background:#5b7a6e}.us-bar-n{width:3em;text-align:right;font-size:11px}body{background:#f8f7f2;max-width:1280px;margin:0 auto;"
             "padding:18px 16px}")


def ui_html(bundle: dict, rcpts: list, book: dict | None = None) -> str:
    book = book or load_book()[0]
    e = html.escape
    css, css_note = _spec_css()
    pub = book["publisher"]
    parts = ['<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
             "<title>VDF 統一 SSOT 分享</title><style>%s</style><style>%s</style></head><body>" % (css, EXTRA_CSS),
             _masthead(book["header_row1"], pub["row2"], pub["row3"], "VDF")]
    ok = sum(1 for r in rcpts if r["lamp"] == "GREEN")
    parts.append('<section class="us-sec"><h2>實測結果 %s</h2><p class="us-small">handoff test 收據(經 VDF 自己的 manager 跑;VCGC 只記收據)· '
                 '%d / %d 綠 · 樣式 %s</p>%s</section>' % (
                     _lamp("GREEN" if ok == len(rcpts) and rcpts else ("RED" if any(r["lamp"] == "RED" for r in rcpts) else "YELLOW")),
                     ok, len(rcpts), e(css_note),
                     _table(["case", "lamp", "rc", "marker", "at", "note"], rcpts)))
    chk = bundle["universe"]["checks"]
    parts.append('<section class="us-sec"><h2>統一 SSOT %s</h2><p>版本 <b>%s</b> · 建於 %s · 共 %d 列 · 個股 %d · 主動 ETF %d · 指數 %d</p>'
                 '<p class="us-small">content_sha256 <span class="us-mono">%s</span></p><p class="us-small">%s</p>'
                 '<p>主動式台股 ETF 判定(VDF-REQ026):符合 <b>%d</b> · 不符合 <b>%d</b> · 未判 <b>%d</b> %s<br><span class="us-small">%s</span></p>%s</section>' % (
                     _lamp(bundle["lamp"]), e(str(bundle.get("version") or "—")), e(bundle["built_at"]), bundle["counts"]["total"],
                     bundle["counts"]["by_group"].get("IN-01", 0), bundle["counts"]["by_group"].get("IN-02", 0), bundle["counts"]["by_group"].get("IN-03", 0),
                     e(bundle["content_sha256"]), e(bundle["rule"]), bundle["counts"]["etf"]["qualified"], bundle["counts"]["etf"]["not_qualified"],
                     bundle["counts"]["etf"]["undetermined"], _lamp(bundle["qualify"]["lamp"]), e(bundle["qualify"]["note"]),
                     _table(["id", "lamp", "name", "note"], chk, 20)))
    panes = []
    for v in book["views"]:
        vw = view(bundle, v["system"], book)
        inner = [_masthead(book["header_row1"], vw["row2"], vw["row3"], vw["system"]),
                 '<p class="us-small">讀法:讀 %s → 重算 sha256 → 一致才用 · 只讀 · 不回寫 · %s</p>' % (e(book["bundle"]["latest"]), e(vw["why"]))]
        if vw["mode"] == "rows":
            inner.append('<p>%d 列(未列入:不符合 / 未判的主動 ETF %d 檔)</p>' % (len(vw["rows"]), vw["dropped"]["etf_not_qualified_or_undetermined"]))
            inner.append(_table(vw["columns"], vw["rows"], 25))
        elif vw["mode"] == "aggregates":
            a = vw["aggregates"]
            inner.append("<h3>各組</h3>%s<h3>各市場</h3>%s<h3>主動 ETF 判定</h3>%s" % (_bars(a["by_group"]), _bars(a["by_market"]), _bars(a["etf"])))
        else:
            m = vw["manifest"]
            inner.append('<p>總燈 %s · 建於 %s · 列 %d</p>' % (_lamp(m["lamp"]), e(m["built_at"]), m["counts"]["total"]))
            inner.append(_table(["id", "lamp", "name"], m["checks"], 20))
            inner.append(_table(["case", "lamp", "rc", "at"], rcpts))
        inner.append('<p class="us-small">sha256 <span class="us-mono">%s</span></p>' % e(vw["content_sha256"]))
        panes.append('<div class="us-pane">%s</div>' % "".join(inner))
    parts.append('<section class="us-sec"><h2>其他系統怎麼展現(同一份 SSOT · 各取所需 · 只讀)</h2><div class="us-grid">%s</div></section>' % "".join(panes))
    parts.append('<p class="us-small">%s · %s · 四系統互不干涉(L123):本頁只預覽各系統拿到的那一份,不寫進 VCGC · VRN-2 · VQG · VAP 的程式或冊。</p></body></html>'
                 % (e(TAG), e(bundle["book"])))
    return "".join(parts)


def write_bundle(bundle: dict, out_root: Path | None = None, book: dict | None = None) -> dict:
    book = book or load_book()[0]
    d = Path(out_root or VIA) / book["bundle"]["dir"]
    d.mkdir(parents=True, exist_ok=True)
    nv = max([_vnum(p) for p in d.glob("VDF_UniverseShare_v*.json")] + [0]) + 1
    bundle["version"] = "v%04d" % nv
    text = json.dumps(bundle, ensure_ascii=False, indent=1) + "\n"
    vp = d / book["bundle"]["versioned"].replace("{NNNN}", "%04d" % nv)
    lp = d / book["bundle"]["latest"]
    for p in (vp, lp):
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, p)                             # 原子寫:讀的人不會讀到半份
    up = d / book["bundle"]["ui"]
    up.write_text(ui_html(bundle, receipts(book["evidence_cases"]), book), encoding="utf-8")
    return {"versioned": str(vp), "latest": str(lp), "ui": str(up)}


def _entry_ok() -> bool:
    return bool(os.environ.get("VIA_FROM_VDFSM") or os.environ.get("VIA_FROM_VCGC"))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    verb = args[0] if args else "build"
    if verb == "verify":                               # 只讀:任何系統都可以叫
        book = load_book()[0]
        p = Path(args[1]) if len(args) > 1 else VIA / book["bundle"]["dir"] / book["bundle"]["latest"]
        if not p.is_file():
            print("[%s] verify · 沒有 %s(先 build --apply)" % (TAG, p))
            return 2
        r = verify(p)
        print("[%s] verify · %s · %s · 列 %d · stored %s · computed %s" % (TAG, "IDENTICAL" if r["identical"] else "DIFFERENT",
                                                                         r["version"], r["rows"], r["stored"][:16], r["computed"][:16]))
        return 0 if r["identical"] else 1
    if not _entry_ok():
        print("[%s] 拒絕。由 VDF System Manager 總控(VIA_FROM_VDFSM=YES)或 VCGC;verify 不必(只讀)" % TAG)
        return 2
    if verb not in ("build", "view", "ui"):
        print("[%s] 未知動詞 %s(build [--apply] | view <VCGC|VRN-2|VQG|VAP> | ui | verify [檔] | --selftest)" % (TAG, verb))
        return 2
    b = build_share()
    if verb == "view":
        if len(args) < 2:
            print("[用法] view <VCGC|VRN-2|VQG|VAP>")
            return 2
        print(json.dumps(view(b, args[1]), ensure_ascii=False, indent=1)[:20000])
        return 0
    print("[%s] %s · 列 %d · 個股 %d · 主動 ETF %d(符合 %d · 不符合 %d · 未判 %d)· 指數 %d · sha %s" % (
        TAG, b["lamp"], b["counts"]["total"], b["counts"]["by_group"].get("IN-01", 0), b["counts"]["by_group"].get("IN-02", 0),
        b["counts"]["etf"]["qualified"], b["counts"]["etf"]["not_qualified"], b["counts"]["etf"]["undetermined"],
        b["counts"]["by_group"].get("IN-03", 0), b["content_sha256"][:16]))
    for c in b["universe"]["checks"]:
        print("  [%-6s] %-4s %s · %s" % (c["lamp"], c["id"], c["name"], str(c["note"])[:110]))
    print("  [%-6s] V8   %s" % (b["qualify"]["lamp"], b["qualify"]["note"][:150]))
    if verb == "ui" or "--apply" in args:
        w = write_bundle(b)
        print("  [寫出] %s\n  [寫出] %s\n  [U/I] %s" % (w["versioned"], w["latest"], w["ui"]))
    return 0 if b["lamp"] != "RED" else 1


# ---------------------------------------------------------------- 自測(沙盒 · 零網路)
def selftest() -> int:
    import shutil
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}")

    print(f"=== {TAG} · 自測(統一 SSOT 分享:一份 · sha 鎖 · 各系統只讀投影;沙盒 · 零網路)===")
    book, bname = load_book()
    systems = [v.get("label") or v["system"] for v in book["views"]]
    chk("① 分享冊 %s:四系統 view(%s)· 讀法(重算 sha · 只讀 · 不回寫)· 欄含判定" % (bname, " · ".join(systems)),
        systems == ["VCGC", "VRN-2", "VQG", "VAP"] and "不回寫" in book["rule"] and {"qualified", "qualify_reason"} <= {c["key"] for c in book["columns"]})
    r1 = [{"b": 1, "a": "x"}, {"a": "y", "b": None}]
    r2 = [{"a": "x", "b": 1}, {"b": None, "a": "y"}]
    chk("② sha 律:同內容鍵序不同 → 同 sha;改一格 → 不同", content_sha(r1) == content_sha(r2) and content_sha(r1) != content_sha([{"a": "x", "b": 2}, r1[1]]))
    tmp = Path(tempfile.mkdtemp(prefix="vdf_share_"))
    keep_ov = list(M10._EVIDENCE_ROOT_OVERRIDE)
    try:
        import pandas as pd
        ev_root = tmp / "etf_root"
        (ev_root / M10.EVIDENCE_PARQUET).parent.mkdir(parents=True)
        b0 = build_share("2026-11-15", list_rows=[])
        etf_codes = [r["code"] for r in b0["rows"] if r["group"] == "IN-02"]
        good, bad = etf_codes[0], etf_codes[1]
        pd.DataFrame([{"run_at": "2026-11-14 18:00:01", "etf_ticker": good, "status": "PASS", "holding_count": 50, "portfolio_date": "2026-11-14", "errors": ""},
                      {"run_at": "2026-11-14 18:00:02", "etf_ticker": bad, "status": "FAIL", "holding_count": 0, "portfolio_date": None, "errors": "HTTP 404"}]
                     ).to_parquet(ev_root / M10.EVIDENCE_PARQUET, index=False)
        M10._EVIDENCE_ROOT_OVERRIDE[:] = [ev_root]
        b = build_share("2026-11-15", list_rows=[])
        tpex = [r for r in b["rows"] if r["group"] == "IN-01" and r["market"] == "TPEX"]
        e = {r["code"]: r for r in b["rows"] if r["group"] == "IN-02"}
        chk("③ 實建(MDL014 尾版 OUT-01 %d 列 · MDL010 尾版判定):列數一致 · %s 符合 · %s 不符合(附錯誤)· 其餘未判 · 上櫃 yf 全 .TWO · 指數 / 個股判定空"
            % (b0["counts"]["total"], good, bad),
            b["counts"]["total"] == b0["counts"]["total"] and e[good]["qualified"] is True and e[bad]["qualified"] is False
            and "HTTP 404" in e[bad]["qualify_reason"] and b["counts"]["etf"]["undetermined"] == len(etf_codes) - 2
            and all(r["yf_ticker"].endswith(".TWO") for r in tpex)
            and all(r["qualified"] is None for r in b["rows"] if r["group"] != "IN-02") and verify(b)["identical"], b["counts"])
        out = tmp / "out"
        w = write_bundle(b, out, book)
        r_ok = verify(w["latest"])
        t = json.loads(Path(w["latest"]).read_text(encoding="utf-8"))
        t["rows"][0]["name"] = t["rows"][0]["name"] + "x"
        (tmp / "tampered.json").write_text(json.dumps(t, ensure_ascii=False), encoding="utf-8")
        r_bad = verify(tmp / "tampered.json")
        w2 = write_bundle(build_share("2026-11-15", list_rows=[]), out, book)
        chk("④ 寫出:版本檔 + latest(原子寫)+ U/I;latest 驗 IDENTICAL · 改一格 → DIFFERENT;再寫一次版號 +1(只增)",
            r_ok["identical"] and not r_bad["identical"] and Path(w["ui"]).is_file() and w["versioned"].endswith("v0001.json")
            and w2["versioned"].endswith("v0002.json") and Path(w["versioned"]).is_file(), (r_ok, r_bad, w, w2))
        vr, vq, vc, va = (view(b, s, book) for s in ("VRN-2", "VQG", "VCGC", "VAP"))
        etf_vr = {r["code"] for r in vr["rows"] if r["group"] == "IN-02"}
        chk("⑤ 各系統投影:VRN-2 / VQG 只帶符合的 ETF(%s)· 個股 / 指數全帶 · VCGC 只看燈與收據不帶列 · VAP 只拿彙總(加總 = 總列)· 全帶同一 sha" % good,
            etf_vr == {good} and {r["code"] for r in vq["rows"] if r["group"] == "IN-02"} == {good}
            and len(vr["rows"]) == b["counts"]["total"] - len(etf_codes) + 1 and "rows" not in vc and vc["manifest"]["counts"]["total"] == b["counts"]["total"]
            and sum(va["aggregates"]["by_group"].values()) == b["counts"]["total"]
            and len({vr["content_sha256"], vq["content_sha256"], vc["content_sha256"], va["content_sha256"], b["content_sha256"]}) == 1)
        page = Path(w["ui"]).read_text(encoding="utf-8")
        css, css_note = _spec_css()
        chk("⑥ U/I:三行標頭 × 5(VDF 發佈 + 四系統預覽)· 實測收據表 · sha 印出 · 套 VDF 鎖定樣式(%s)· 不載外部腳本" % css_note,
            page.count("VERITAS INTELLIGENCE ANALYTICS") == 5 and "實測結果" in page and b["content_sha256"] in page
            and all(x in page for x in ("Veritas Central Governance Console", "Veritas ReportNova", "VeritaQuantGuard", "VeritasAutoPlot"))
            and bool(css) and css in page and "<script" not in page.lower(), css_note)
    finally:
        M10._EVIDENCE_ROOT_OVERRIDE[:] = keep_ov
        shutil.rmtree(tmp, ignore_errors=True)
    rc = receipts(["__no_such_case__"])
    chk("⑦ 沒有收據 → GRAY「還沒跑 handoff test」(不假綠)", rc[0]["lamp"] == "GRAY" and rc[0]["rc"] is None)
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def selftest", 1)[0]
    chk("⑧ VDF 獨立:不匯入他系統程式 · 兩座橋在 · 同意閘不讀不寫 · 不碰 TA-Lib · 不寫環境 · 只寫自己的輸出夾",
        not re.search(r"^\s*(import|from)\s+(talib|CGC_|VRN_|VRN2_|VQG_|VAP_|VCGC)", text, re.M) and "[VIA:ACCEL-BRIDGE" in text
        and "[VIA:NET-BRIDGE" in text and not re.search(r"environ[\[.][^\n]{0,16}VIA_(NET|SCRAPE)_CON" + "SENT", body)
        and not re.search(r"os\.environ\[[^\]]*\]\s*=(?!=)|os\.environ\.(pop|setdefault|update)\(", body))
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
