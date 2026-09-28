#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL231_MatrixPages v0101 — 多頁矩陣最後加三頁:編號總冊 · 測試狀態 · 流程圖(紅黃綠 · 版本號 · 鎖定日期時間)

操作員 2026-09-28:「每一個 vcgc vdf vrn 所用的工具 參數 ssot regex 參數 指數都有編號 全部整理列入 u/i tab 最後一頁
紅黃綠三燈顯示狀況 偵測工具 unit integration system test 狀態顯示 流程邏輯 workflow 圖像化也放最後 tabs 全都編號
邏輯路徑編號備份 附上版本號及鎖定日期」「鎖定日期還要加上時間」。
v0100 的九頁一字不動(只增不減),後面接三頁,內容全問 CGC_MDL236_NumberedCatalog 尾版(本支不另立尺):
  ⑩ 編號總冊  工具 TL · SSOT SS · regex RX · 參數表 PM · 指數/資料表 IX:編號 · 燈 · 名稱 · 版本 · 來源 · 鎖定時間(含時區)· 說明
  ⑪ 測試狀態  偵測工具 · unit(自測格子)· integration(VDF / VRN 鏈)· system(一鍵):編號 · 燈 · 項目 · 層 · 時間 · 說明
  ⑫ 流程圖    每條流程邏輯路徑 LP 一列 SVG:節點依鏈測結果上紅黃綠;列頭 = 路徑編號 · 版本(路徑備份冊)· 鎖定時間
輸出同 v0100:VIA_Reports/matrix/VIA_MATRIX_PAGES_latest.html(零 CDN 零外連)。
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

import html as _html
import importlib.util
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL231_MatrixPages"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_PRIOR = _load(PRIOR, STEM + "_prior_for_" + Path(__file__).stem)
ENGINE_TAG = f"{STEM} v{_vnum(Path(__file__)):04d}"
NEW_TABS = ("編號總冊", "測試狀態", "流程圖")
TABS = tuple(_PRIOR.TABS) + NEW_TABS
LAMP_ZH = {"GREEN": "綠", "AMBER": "黃", "RED": "紅"}
LAMP_HEX = {"GREEN": "#2da44e", "AMBER": "#d4a72c", "RED": "#cf222e"}
KIND_TITLE = (("tool", "工具 TL"), ("ssot", "SSOT 冊 SS"), ("regex", "regex RX"), ("param", "參數表 PM"), ("index", "指數 / 資料表 IX"))
_CSS_EXTRA = """
.lp{margin:0 0 12px}.lp h3{font-size:12px;margin:0 0 4px}.lp svg{max-width:100%;height:auto;background:var(--card);border:1px solid var(--line);border-radius:6px}
.lp .meta{font-size:11px;opacity:.75;margin:0 0 4px}
"""


def catalog() -> dict:
    p = max((q for q in HERE.glob("CGC_MDL236_NumberedCatalog_v*.py") if _vnum(q) >= 0), key=_vnum, default=None)
    if p is None:
        return {}
    return _load(p, "catalog_for_" + Path(__file__).stem).catalog()


def _count(rows: list) -> str:
    c = {k: sum(1 for r in rows if r["lamp"] == k) for k in LAMP_ZH}
    return f"綠 {c['GREEN']} · 黃 {c['AMBER']} · 紅 {c['RED']}"


def catalog_sections(cat: dict) -> list:
    secs = []
    for key, title in KIND_TITLE:
        rows = sorted(cat.get(key) or [], key=lambda r: ({"RED": 0, "AMBER": 1, "GREEN": 2}[r["lamp"]], r["code"]))
        secs.append((f"{title} · {len(rows)} 項 · {_count(rows)}", ["編號", "燈", "名稱", "版本", "來源", "鎖定時間", "說明"],
                     [[r["code"], LAMP_ZH[r["lamp"]], r["name"], r["version"], r["source"], r["locked_at"], r["note"]] for r in rows], 1))
    return secs


def test_sections(cat: dict) -> list:
    rows = cat.get("test") or []
    secs = []
    for layer in ("偵測工具", "unit", "integration", "system"):
        part = sorted((r for r in rows if r["version"] == layer), key=lambda r: ({"RED": 0, "AMBER": 1, "GREEN": 2}[r["lamp"]], r["code"]))
        secs.append((f"{layer} · {len(part)} 項 · {_count(part)}", ["編號", "燈", "項目", "來源", "時間", "說明"],
                     [[r["code"], LAMP_ZH[r["lamp"]], r["name"], r["source"], r["locked_at"], r["note"]] for r in part], 1))
    return secs


def _node_lamps(cat: dict) -> dict:
    lamps = {}
    for r in cat.get("test") or []:
        if r["version"] == "integration" and " · " in r["name"]:
            lamps[r["name"].split(" · ", 1)[1]] = r["lamp"]
    return lamps


def path_svg(path: dict, lamps: dict, per_row: int = 6) -> str:
    nodes = [str(n) for n in path["nodes"]] or ["(空)"]
    w, h, gx, gy = 170, 34, 26, 18
    rows = (len(nodes) + per_row - 1) // per_row
    width = per_row * (w + gx) + 10
    height = rows * (h + gy) + 10
    parts = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}' width='{width}' role='img' "
             f"aria-label='{_html.escape(path['code'])}'>"]
    for i, name in enumerate(nodes):
        r, c = divmod(i, per_row)
        x, y = 5 + c * (w + gx), 5 + r * (h + gy)
        lamp = lamps.get(name)
        stroke = LAMP_HEX.get(lamp, "#8c959f")
        label = name if len(name) <= 24 else name[:23] + "…"
        parts.append(f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='6' fill='none' stroke='{stroke}' stroke-width='2'/>"
                     f"<text x='{x + 6}' y='{y + 14}' font-size='9' fill='currentColor'>{path['code']}.{i + 1:02d}</text>"
                     f"<text x='{x + 6}' y='{y + 27}' font-size='10' fill='currentColor'>{_html.escape(label)}</text>")
        if i + 1 < len(nodes):
            if c + 1 < per_row:
                parts.append(f"<line x1='{x + w}' y1='{y + h / 2}' x2='{x + w + gx - 4}' y2='{y + h / 2}' stroke='#8c959f' stroke-width='1.5'/>"
                             f"<polygon points='{x + w + gx - 4},{y + h / 2 - 3} {x + w + gx},{y + h / 2} {x + w + gx - 4},{y + h / 2 + 3}' fill='#8c959f'/>")
            else:
                parts.append(f"<line x1='{x + w / 2}' y1='{y + h}' x2='{5 + w / 2}' y2='{y + h + gy - 2}' stroke='#8c959f' stroke-dasharray='3 3'/>")
    parts.append("</svg>")
    return "".join(parts)


def flow_html(cat: dict) -> str:
    lamps = _node_lamps(cat)
    versions = cat.get("versions") or {}
    pending = {a["code"]: a for a in cat.get("backup_adds") or []}
    out = ["<p class='meta'>每條路徑一列;節點框色 = 鏈測燈(綠 / 黃 / 紅;灰 = 本機沒有鏈報告)。版本與備份時間取路徑備份冊 "
           "VIA_LogicPath_Backup;鎖定時間 = 來源冊最後一次提交(日期 時間 時區)。</p>"]
    for p in cat.get("paths") or []:
        v = versions.get(p["code"])
        ver = (v["version"] + " · 備份 " + v["backed_up_at"]) if v and v["sha"] == p["sha"] else \
              ("待備份(路徑有變,via-vcgc 跑 CGC_MDL236 --apply 追加新版號)" if p["code"] in pending else "—")
        out.append(f"<div class='lp'><h3>{_html.escape(p['code'])} · {_html.escape(p['name'])}</h3>"
                   f"<p class='meta'>版本 {_html.escape(ver)} · 鎖定 {_html.escape(p['locked_at'])} · 來源 {_html.escape(p['source'])} · "
                   f"{len(p['nodes'])} 節點 · sha {p['sha']}</p>{path_svg(p, lamps)}</div>")
    return "".join(out)


def render(width: int = 150, out: Path = None, side_path: Path = None, runall_path: Path = None, rep: dict | None = None) -> dict:
    out = out or _PRIOR.OUT
    side_path = side_path or _PRIOR.SIDE
    runall_path = runall_path or _PRIOR.RUNALL
    tail = _PRIOR.sweep_tail()
    style = dict(getattr(tail, "STYLE", {}) or {})
    style.update({"守住": "green", "回歸": "bold red", "未量": "dim", "可加鎖": "cyan",
                  "綠": "bold green", "黃": "bold yellow", "紅": "bold red"})
    cell = getattr(tail, "_cell", lambda v: "" if v is None else str(v))
    if rep is None:
        side = _PRIOR._load_json(side_path)
        if tail is None or side is None:
            rep = {"sections": [("總覽", ["狀態"], [["ABSENT · " + ("CGC_MDL229 尾版不在" if tail is None else f"側車不在:{side_path}(先跑一次全景)")]], None)],
                   "verdict": "ABSENT", "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "head": ""}
        else:
            rep = tail.build(side)
    vdf, vrn = _PRIOR._load_json(_PRIOR.VDF_CHAIN), _PRIOR._load_json(_PRIOR.VRN_CHAIN)
    book, book_name = _PRIOR.lock_book()
    lock = _PRIOR.lock_check(book, _PRIOR.lamp_states(rep.get("sections") or []), _PRIOR.chain_states(vdf, "id"), _PRIOR.chain_states(vrn, "name"))
    runall = _PRIOR._load_json(runall_path)
    pages = _PRIOR.build_pages(rep, lock, book_name, runall)
    cat = catalog()
    pages["編號總冊"] = catalog_sections(cat) if cat else [("編號總冊", ["狀態"], [["CGC_MDL236 尾版不在"]], None)]
    pages["測試狀態"] = test_sections(cat) if cat else [("測試狀態", ["狀態"], [["CGC_MDL236 尾版不在"]], None)]
    raw = {"流程圖": flow_html(cat) if cat else "<p>CGC_MDL236 尾版不在</p>"}
    verdict = "RED" if lock["regress"] else rep.get("verdict", "")
    title = f"VIA 多頁矩陣 · {verdict} · {rep.get('ts', '')} · HEAD {rep.get('head', '')}"
    nav, panels, engine = [], [], "rich"
    for name in TABS:
        if name in raw:
            frag, n = raw[name], len(cat.get("paths") or [])
        else:
            frag, engine = _PRIOR._render_tab(pages[name], width, style, cell) if pages.get(name) else ("<p>(本頁本次沒有內容)</p>", engine)
            n = len(lock["regress"]) if name == "鎖" else sum(len(s[2] or []) for s in pages.get(name) or [])
        nav.append(f"<button role='tab' aria-selected='false'>{_html.escape(name)}<span class='n'>{n}</span></button>")
        panels.append(f"<section role='tabpanel' aria-label='{_html.escape(name)}'>{frag}</section>")
    doc = ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
           f"<title>VIA 多頁矩陣</title><style>{_PRIOR._CSS}{_CSS_EXTRA}</style></head><body><header><h1>{_html.escape(title)}</h1><nav role='tablist'>"
           + "".join(nav) + "</nav></header><main>" + "".join(panels) + "</main>"
           + f"<footer>{ENGINE_TAG} · {engine} · 零 CDN 零外連 · 鎖冊 {_html.escape(book_name or '不在')}</footer><script>{_PRIOR._JS}</script></body></html>")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / _PRIOR.PAGE_NAME
    path.write_text(doc, encoding="utf-8")
    return {"path": str(path), "engine": engine, "verdict": verdict, "regress": lock["regress"], "add": lock["add"],
            "held": lock["held"], "unmeasured": lock["unmeasured"], "tabs": {t: (len(pages[t]) if t in pages else 1) for t in TABS},
            "numbered": sum(len(cat.get(k) or []) for k in ("tool", "ssot", "regex", "param", "index", "test")) + len(cat.get("paths") or [])}


_PRIOR_RENDER = _PRIOR.render
_PRIOR.render = render
_SELFTEST = _PRIOR.selftest


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def main(argv=None) -> int:
    return _PRIOR.main(argv)


def selftest() -> int:
    import tempfile
    _PRIOR.render = _PRIOR_RENDER                   # v0100's own checks measure v0100's shape
    try:
        rc = _SELFTEST()
    finally:
        _PRIOR.render = render
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    with tempfile.TemporaryDirectory() as td:
        rep = {"sections": [("① 總覽", ["燈"], [["GREEN"]], 0)], "verdict": "GREEN", "ts": "t", "head": "h"}
        res = render(out=Path(td), rep=rep)
        page = Path(res["path"]).read_text(encoding="utf-8")
    chk("⑫ 十二頁:v0100 九頁照舊 + 編號總冊 · 測試狀態 · 流程圖 在最後", list(res["tabs"])[-3:] == list(NEW_TABS) and len(res["tabs"]) == 12)
    chk("⑬ 編號總冊有 TL / SS / RX / PM / IX 五類編號", all(f">{p}-0" in page or f"{p}-0" in page for p in ("TL", "SS", "RX", "PM", "IX")))
    chk("⑭ 測試狀態分 偵測工具 / unit / integration / system", all(k in page for k in ("偵測工具", "unit", "integration", "system")))
    chk("⑮ 流程圖是 SVG,每條路徑有 LP 編號與鎖定時間", page.count("<svg") >= 1 and "LP-0" in page and "鎖定 " in page)
    chk("⑯ 零外連(沒有 http(s) 資源)", not re.search(r"(src|href)=['\"]https?://", page))
    ok = rc == 0 and all(results)
    print(f"  {ENGINE_TAG} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'} · 編號 {res['numbered']}")
    return 0 if ok else 1




if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
