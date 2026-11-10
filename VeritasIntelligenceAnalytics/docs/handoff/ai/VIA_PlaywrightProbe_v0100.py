#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_PlaywrightProbe v0100 — VCGC 自己的離線 HTML 頁面實測(Playwright · 0 token · 0 網路)。

操作員 2026-11-10:「先做 Graphify Playwright DuckDB 席位候選 自動完成以上全部」。工具鎖冊 playwright 席位的候選本體。
做什麼:用 Playwright(Chromium)以 file:// 打開指定的 VCGC 靜態頁(工作台 / 上傳整合頁 / 矩陣頁),每頁 × 兩種寬度(桌機 1400 · 手機 390):
  · console error 與 pageerror · 任何非 file: / data: 請求一律攔下並記為違規(頁面必須 0 網路)
  · 手機寬度水平溢出(scrollWidth > clientWidth)· 可選截圖
判定:任一頁有錯誤 / 外連 / 溢出 = RED;全過 = GREEN;Playwright 沒裝 = NODATA(照實說,不代裝 —— 裝套件是操作員的手)。
收據只寫自己的:VIA_Reports/workbench/UI_Playwright_latest.json。不改被測頁,不碰他系統的冊 / 正本 / 號(L123 · L125)。
用法:python VIA_PlaywrightProbe_v0100.py --pages <夾或 .html …> [--out <截圖夾>] [--no-shot] · --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import argparse
import datetime as _dt
import json
import sys
import tempfile
from pathlib import Path

VERSION = "v0100"
ENGINE = f"VIA_PlaywrightProbe_{VERSION}"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
RECEIPT = Path("VIA_Reports") / "workbench" / "UI_Playwright_latest.json"
VIEWPORTS = {"desktop": (1400, 900), "phone": (390, 844)}


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def discover(targets: list) -> list:
    """夾 → 底下 .html(一層);檔 → 原樣。排序去重。"""
    out = []
    for t in targets:
        p = Path(t).expanduser()
        if p.is_dir():
            out += sorted(q for q in p.glob("*.html") if q.is_file())
        elif p.is_file() and p.suffix.lower() in (".html", ".htm"):
            out.append(p)
    seen, uniq = set(), []
    for p in out:
        r = p.resolve()
        if r not in seen:
            seen.add(r)
            uniq.append(r)
    return uniq


def judge(results: list) -> str:
    if not results:
        return "NODATA"
    bad = any(r.get("errors") or r.get("blocked") or r.get("overflow") or r.get("crash") for r in results)
    return "RED" if bad else "GREEN"


def _load_playwright():
    from playwright.sync_api import sync_playwright  # 執行期才載;匯入層不碰
    return sync_playwright


def probe(pages: list, shot_dir: Path | None = None, wait_ms: int = 1200, loader=_load_playwright) -> dict:
    try:
        sync_playwright = loader()
    except Exception as exc:  # noqa: BLE001 — 沒裝就照實說
        return {"lamp": "NODATA", "reason": f"Playwright 不可用({type(exc).__name__}):本支不代裝;裝套件是操作員的手", "results": []}
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            for page_path in pages:
                for vp_name, (w, h) in VIEWPORTS.items():
                    rec = {"page": str(page_path), "viewport": vp_name, "errors": [], "blocked": [], "overflow": False}
                    ctx = browser.new_context(viewport={"width": w, "height": h})
                    pg = ctx.new_page()

                    def _route(route, _rec=rec):
                        u = route.request.url
                        if u.startswith(("file:", "data:", "blob:", "about:")):
                            route.continue_()
                        else:
                            _rec["blocked"].append(u[:200])
                            route.abort()
                    pg.route("**/*", _route)
                    pg.on("console", lambda m, _rec=rec: _rec["errors"].append(m.text[:300]) if m.type == "error" else None)
                    pg.on("pageerror", lambda e, _rec=rec: _rec["errors"].append(str(e)[:300]))
                    try:
                        pg.goto(page_path.as_uri(), wait_until="load", timeout=60000)
                        pg.wait_for_timeout(wait_ms)
                        if vp_name == "phone":
                            rec["overflow"] = bool(pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"))
                        rec["title"] = pg.title()[:120]
                        if shot_dir:
                            shot_dir.mkdir(parents=True, exist_ok=True)
                            fn = shot_dir / f"{page_path.stem}_{vp_name}.png"
                            pg.screenshot(path=str(fn), full_page=False)
                            rec["shot"] = str(fn)
                    except Exception as exc:  # noqa: BLE001 — 單頁炸了記紅,不連累其他頁
                        rec["crash"] = f"{type(exc).__name__}: {str(exc)[:200]}"
                    finally:
                        ctx.close()
                    results.append(rec)
        finally:
            browser.close()
    return {"lamp": judge(results), "results": results}


def run(targets: list, shot_dir: Path | None = None, via: Path = VIA, write: bool = True) -> dict:
    pages = discover(targets)
    res = probe(pages, shot_dir) if pages else {"lamp": "NODATA", "reason": "沒有找到 .html", "results": []}
    res.update(engine=ENGINE, at_utc=utc_now(), pages=[str(p) for p in pages],
               boundary="只讀:file:// 打開 · 非本機請求一律攔下 · 不改被測頁 · 不裝套件")
    if write:
        out = via / RECEIPT
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        res["receipt"] = str(out)
    return res


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")
    with tempfile.TemporaryDirectory(prefix="via_pwprobe_") as td:
        d = Path(td)
        (d / "a.html").write_text("<!doctype html><title>a</title>", encoding="utf-8")
        (d / "b.html").write_text("<!doctype html><title>b</title>", encoding="utf-8")
        (d / "c.txt").write_text("x", encoding="utf-8")
        got = discover([d, d / "a.html"])
        chk("① discover:夾取 .html、去重、略過非 html", [p.name for p in got] == ["a.html", "b.html"], [p.name for p in got])

        def _absent():
            raise ImportError("no playwright")
        r = probe(got, loader=_absent)
        chk("② Playwright 沒裝 = NODATA 照實說、不丟例外", r["lamp"] == "NODATA" and "不代裝" in r["reason"])
        chk("③ 判定:有外連 / 錯誤 / 溢出 = RED · 全乾淨 = GREEN · 空 = NODATA",
            judge([{"blocked": ["https://x"]}]) == "RED" and judge([{"errors": ["e"]}]) == "RED"
            and judge([{"overflow": True}]) == "RED" and judge([{"errors": [], "blocked": [], "overflow": False}]) == "GREEN" and judge([]) == "NODATA")
        rr = run([d / "nope"], via=d, write=True)
        chk("④ 沒頁 = NODATA · 收據寫在自己的 VIA_Reports/workbench", rr["lamp"] == "NODATA" and (d / RECEIPT).is_file())
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋在 · 匯入層沒載 playwright", "[VIA:ACCEL-BRIDGE" in text and "playwright" not in {m.split(".")[0] for m in sys.modules})
    good = all(ok)
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pages", nargs="*", default=[], help="要測的 .html 或夾")
    ap.add_argument("--out", default="", help="截圖夾(預設不截)")
    ap.add_argument("--no-shot", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    shot = Path(a.out) if a.out and not a.no_shot else None
    r = run(a.pages or [str(VIA / "VIA_Reports" / "workbench")], shot)
    print(json.dumps({k: r.get(k) for k in ("lamp", "engine", "pages", "reason", "receipt")}, ensure_ascii=False, indent=1))
    return {"GREEN": 0, "NODATA": 0}.get(r["lamp"], 1)


if __name__ == "__main__":
    sys.exit(main())
