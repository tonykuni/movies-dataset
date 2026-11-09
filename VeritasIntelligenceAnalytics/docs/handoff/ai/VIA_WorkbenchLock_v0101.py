#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_WorkbenchLock v0101 — v0100 薄尾(v0100 一字不改 · SHA 釘住):品牌覆蓋(標誌 + icon 組),鎖的 token 區塊 / 結構 id / payload 身分照 v0100。

操作員 2026-11-09:「我們的 U/I 的 ICON 不像我們的 U/I 優雅 請協助增加」「LOGO 第二行字太小看不到 應放到略小於第一行 但不超過大生命之樹的寬度」。

做法(鎖站 review/VIA_Workbench_LockSite_v0106_4 四檔一字不動;品牌正本另放 review/VIA_Workbench_Brand_v0100/):
  --logo  <png>   預設 Brand/veritas_logo_header_v0106.png(segments.zip 四段合成 · 420×384 = 鎖定 css 的 aspect-ratio · 第二行高 = 第一行 62% · 寬 ≤ 生命樹寬 · 真透明)
  --icons <json>  預設 Brand/icons_v0100.json(細線 1.6 · 圓角端點 · 24 view · currentColor;正本 js 的 render 契約不變:每 icon = [[tag, attrs], …])
  build:頁與 hub 先照 v0100 生成,再 (a) 換 base64 標誌 (b) 換正本 js 裡的 `const ICONS = {…}` 字面 (c) 重算 CSP script-src sha256(js 變了)。
  check:v0100 全部 + 品牌:頁含新標誌 base64 · ICONS 字面 = 品牌檔 · CSP sha 與內嵌 js 一致 → 不一致 RED。
  --no-brand:關掉覆蓋(= v0100 原樣)。
自測:本版 8 項 + v0100 17 項。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys, pathlib as _sa_pl
    for _sa_p in [_sa_pl.Path(__file__).resolve()] + list(_sa_pl.Path(__file__).resolve().parents):
        if (_sa_p / "supportive modules").is_dir():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
    import VeritasCeleritas_v1141 as _sa  # noqa: F401
except Exception:
    _sa = None
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 網路橋(本引擎不出網;只為治理覆蓋登記,graceful) =====
try:
    import importlib as _nb_il
    _nb = _nb_il.import_module("network.VeritasAegisNexus_v1652")  # noqa: F841
except Exception:
    _nb = None
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
import base64
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0101"
ENGINE = f"VIA_WorkbenchLock_{VERSION}"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VIA_WorkbenchLock_v0100.py"
PRIOR_SHA256 = "0e36baa0388d93be9ab468ade4fcce9a24152594f8e7e7fbb7cb03e201d08716"
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.is_file():
    raise SystemExit("[RED] 前版 %s 不在 %s(v0101 是 v0100 的薄尾 · 兩支要放同一夾)" % (PRIOR_NAME, HERE))
PRIOR_SHA_OK = hashlib.sha256(PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == PRIOR_SHA256
_spec = importlib.util.spec_from_file_location("via_workbenchlock_v0100_for_v0101", PRIOR_PATH)
BASE = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = BASE
_spec.loader.exec_module(BASE)


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(BASE, name)


BRAND_REL = Path("review") / "VIA_Workbench_Brand_v0100"
BRAND_LOGO = "veritas_logo_header_v0106.png"
BRAND_ICONS = "icons_v0100.json"
_CSP_RX = re.compile(r"script-src 'sha256-([A-Za-z0-9+/=]+)'")
_SCRIPT_RX = re.compile(r"<script>(.*)</script>\s*</body>", re.S)


def brand_paths(via: Path, logo: str = "", icons: str = "") -> dict:
    d = via / BRAND_REL
    return {"logo": Path(logo) if logo else d / BRAND_LOGO, "icons": Path(icons) if icons else d / BRAND_ICONS}


def icons_literal(icons_json: dict) -> str:
    """品牌 json → 正本 js 的 `const ICONS = {…}` 字面(每 icon = [[tag, attrs], …];style 併進每個 attrs,個別 attrs 可覆蓋)。"""
    style = icons_json.get("style") or {}
    parts = []
    for name, elems in (icons_json.get("icons") or {}).items():
        es = []
        for tag, attrs in elems:
            merged = {**style, **attrs}
            es.append("[%s, {%s}]" % (json.dumps(tag), ", ".join("%s:%s" % (json.dumps(k), json.dumps(str(v))) for k, v in merged.items())))
        parts.append("%s: [%s]" % (name, ", ".join(es)))
    return "const ICONS = { " + ", ".join(parts) + " }"


def find_icons_literal(js: str) -> tuple[int, int]:
    i = js.index("const ICONS = ")
    j = i + len("const ICONS = ")
    depth = 0
    for k in range(j, len(js)):
        c = js[k]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i, k + 1
    raise ValueError("ICONS literal not closed")


def csp_sha(script_text: str) -> str:
    return base64.b64encode(hashlib.sha256(script_text.encode("utf-8")).digest()).decode("ascii")


def apply_brand(html: str, old_logo_b64: str, new_logo_b64: str, icons_js: str | None) -> tuple[str, dict]:
    """渲染後套品牌:換標誌 base64;換內嵌 js 的 ICONS 字面並重算 CSP sha。回 (html, 收據)。"""
    rec = {"logo_replaced": 0, "icons_replaced": False, "csp_updated": False}
    if old_logo_b64 and new_logo_b64 and old_logo_b64 in html:
        rec["logo_replaced"] = html.count(old_logo_b64)
        html = html.replace(old_logo_b64, new_logo_b64)
    if icons_js:
        m = _SCRIPT_RX.search(html)
        if m and "const ICONS = " in m.group(1):
            js = m.group(1)
            a, b = find_icons_literal(js)
            new_js = js[:a] + icons_js + js[b:]
            html = html[:m.start(1)] + new_js + html[m.end(1):]
            rec["icons_replaced"] = True
            new_sha = csp_sha(new_js)
            if _CSP_RX.search(html):
                html = _CSP_RX.sub("script-src 'sha256-%s'" % new_sha, html, count=1)
                rec["csp_updated"] = True
    return html, rec


def build(via: Path, out: Path, open_after: bool = False, logo: str = "", icons: str = "", no_brand: bool = False) -> dict:
    res = BASE.build(via, out, open_after=False)
    if res.get("lamp") != "GREEN" or no_brand:
        res["brand"] = {"applied": False, "why": "no-brand" if no_brand else "v0100 build 不綠"}
        return res
    bp = brand_paths(via, logo, icons)
    site = BASE.lock_site(via)
    old_b64 = base64.b64encode((site / BASE.LOCK_FILES["logo"]).read_bytes()).decode("ascii")
    new_b64 = base64.b64encode(bp["logo"].read_bytes()).decode("ascii") if bp["logo"].is_file() else ""
    icons_js = icons_literal(json.loads(bp["icons"].read_text(encoding="utf-8"))) if bp["icons"].is_file() else None
    brand = {"applied": True, "logo": str(bp["logo"]), "logo_sha256": BASE.sha256_file(bp["logo"]) if bp["logo"].is_file() else None,
             "icons": str(bp["icons"]), "icons_sha256": BASE.sha256_file(bp["icons"]) if bp["icons"].is_file() else None, "pages": {}}
    files = [Path(v["file"]) for v in res["pages"].values()] + [Path(res["hub"])]
    for f in files:
        html = f.read_text(encoding="utf-8")
        html2, rec = apply_brand(html, old_b64, new_b64, icons_js)
        f.write_text(html2, encoding="utf-8")
        brand["pages"][f.name] = rec
    res["brand"] = brand
    (out / "api" / "brand.json").write_text(json.dumps(brand, ensure_ascii=False, indent=1), encoding="utf-8")
    if open_after:
        try:
            import os
            if os.name == "nt":
                os.startfile(res["hub"])  # type: ignore[attr-defined]
            else:
                import webbrowser
                webbrowser.open(Path(res["hub"]).as_uri())
        except Exception as exc:
            BASE.WARNINGS.append(f"open 失敗: {exc}")
    return res


def check(via: Path, files=None, out: Path | None = None, write: bool = True, logo: str = "", icons: str = "", no_brand: bool = False) -> dict:
    res = BASE.check(via, files=files, out=out, write=False)
    res["engine"] = ENGINE
    if no_brand:
        res["brand"] = {"checked": False}
    else:
        bp = brand_paths(via, logo, icons)
        new_b64 = base64.b64encode(bp["logo"].read_bytes()).decode("ascii") if bp["logo"].is_file() else ""
        icons_js = icons_literal(json.loads(bp["icons"].read_text(encoding="utf-8"))) if bp["icons"].is_file() else None
        rows = []
        for fr in res["files"]:
            f = Path(fr["file"])
            r = {"file": f.name, "logo": None, "icons": None, "csp": None}
            if f.exists():
                t = f.read_text(encoding="utf-8", errors="replace")
                r["logo"] = bool(new_b64) and new_b64 in t
                m = _SCRIPT_RX.search(t)
                if m and "const ICONS = " in m.group(1):
                    js = m.group(1)
                    a, b = find_icons_literal(js)
                    r["icons"] = (js[a:b] == icons_js) if icons_js else None
                    cm = _CSP_RX.search(t)
                    r["csp"] = bool(cm) and cm.group(1) == csp_sha(js)
                else:
                    r["icons"], r["csp"] = None, None                      # hub 無內嵌 js
                ok = bool(r["logo"]) and r["icons"] is not False and r["csp"] is not False
                if not ok:
                    fr["lamp"] = "RED"
            rows.append(r)
        res["brand"] = {"checked": True, "logo": str(bp["logo"]), "icons": str(bp["icons"]), "pages": rows}
    res["lamp"] = "GREEN" if res["lock_site"]["ok"] and res["files"] and all(x["lamp"] == "GREEN" for x in res["files"]) else "RED"
    if write:
        BASE.CHECK_OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def selftest() -> int:
    via = BASE.resolve_via("")
    ok = total = 0

    def t(name, cond):
        nonlocal ok, total
        total += 1
        ok += bool(cond)
        print(f"  {'PASS' if cond else 'FAIL'} {name}")

    print(f"[{ENGINE} selftest]")
    t("① 前版 v0100 SHA 釘住", PRIOR_SHA_OK)
    bp = brand_paths(via)
    t("② 品牌正本在:標誌 png 420×384 · icons json 含正本六名", bp["logo"].is_file() and bp["icons"].is_file()
      and {"search", "sliders", "layers", "reset", "download", "grid"} <= set(json.loads(bp["icons"].read_text(encoding="utf-8"))["icons"]))
    try:
        from PIL import Image
        im = Image.open(bp["logo"])
        t("③ 標誌尺寸 = 鎖定 css aspect-ratio 420/384 · RGBA 透明", im.size == (420, 384) and im.mode == "RGBA" and (im.getchannel("A").getextrema()[0] == 0))
    except Exception as exc:  # noqa: BLE001
        t("③ 標誌尺寸(PIL 不在:%s)" % exc, False)
    lit = icons_literal({"style": {"fill": "none"}, "icons": {"x": [["path", {"d": "M1 1"}]]}})
    t("④ icons 字面:style 併進 attrs · 格式 = 正本契約", lit == 'const ICONS = { x: [["path", {"fill":"none", "d":"M1 1"}]] }')
    js = (BASE.lock_site(via) / BASE.LOCK_FILES["js"]).read_text(encoding="utf-8")
    a, b = find_icons_literal(js)
    t("⑤ 正本 js 的 ICONS 字面可定位(以 } 配對 · 後接 ;)", js[a:a + 14] == "const ICONS = " and js[b:b + 1] == ";")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "wb"
        res = build(via, out)
        br = res.get("brand") or {}
        t("⑥ build:五頁 + hub 都換標誌 · 五頁換 ICONS 並更新 CSP", br.get("applied") and all(v["logo_replaced"] >= 1 for v in br["pages"].values())
          and all(v["icons_replaced"] and v["csp_updated"] for k, v in br["pages"].items() if k != BASE.HUB_NAME))
        chk = check(via, out=out, write=False)
        t("⑦ check 綠(v0100 全部 + 品牌三項)", chk["lamp"] == "GREEN" and all(p["logo"] for p in chk["brand"]["pages"]))
        p = out / BASE.PAGE_NAME.format(sys="VQG")
        p.write_text(p.read_text(encoding="utf-8").replace("stroke-linecap", "stroke-linecap-x", 1), encoding="utf-8")
        chk2 = check(via, out=out, write=False)
        t("⑧ 篡改內嵌 js(icons)→ CSP 不符 → check 紅", chk2["lamp"] == "RED")
    print(f"  == {ok}/{total}")
    rc0 = BASE.selftest()
    good = ok == total and rc0 == 0
    print(f"[{'PASS' if good else 'FAIL'} ] {ENGINE} selftest · 本版 {ok}/{total} · 前版 v0100 {'PASS' if rc0 == 0 else 'FAIL'}")
    return 0 if good else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog=ENGINE, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verb", nargs="?", default="all", choices=["kit", "build", "check", "all"])
    ap.add_argument("--via", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--files", nargs="*")
    ap.add_argument("--logo", default="", help="品牌標誌 png(預設 review/VIA_Workbench_Brand_v0100/%s)" % BRAND_LOGO)
    ap.add_argument("--icons", default="", help="icon 組 json(預設 review/VIA_Workbench_Brand_v0100/%s)" % BRAND_ICONS)
    ap.add_argument("--no-brand", action="store_true", help="不套品牌(= v0100 原樣)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    via = BASE.resolve_via(a.via)
    out = Path(a.out).resolve() if a.out else via / "VIA_Reports" / "workbench"
    rc = 0
    if a.verb in ("kit", "all"):
        info = BASE.kit(via)
        print(f"[kit] {info['lamp']} · 鎖站 {'OK' if info['lock_site']['ok'] else info['lock_site']['problems']} · token {info['token_count']}")
        rc |= info["lamp"] != "GREEN"
    if a.verb in ("build", "all"):
        res = build(via, out, open_after=a.open, logo=a.logo, icons=a.icons, no_brand=a.no_brand)
        if res["lamp"] != "GREEN":
            print(f"[build] RED · {res.get('reason')}")
            return 1
        for k, v in res["pages"].items():
            print(f"[build] {k:5s} rows {sum(v['rows'].values()):4d}")
        b = res.get("brand") or {}
        print(f"[build] 品牌 {'套用' if b.get('applied') else '未套'} · 標誌 {Path(b.get('logo', '')).name} · icons {Path(b.get('icons', '')).name} · hub → {res['hub']}")
    if a.verb in ("check", "all"):
        chk = check(via, files=[Path(f) for f in a.files] if a.files else None, out=out, logo=a.logo, icons=a.icons, no_brand=a.no_brand)
        for f in chk["files"]:
            print(f"[check] {f['lamp']:5s} {Path(f['file']).name}")
        print(f"[check] {chk['lamp']} · 品牌 {'驗' if chk['brand'].get('checked') else '略'} → {BASE.CHECK_OUT.name}")
        rc |= chk["lamp"] != "GREEN"
    return int(rc)


if __name__ == "__main__":
    sys.exit(main())
