#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_WorkbenchLock v0102 — v0101 薄尾(v0101 一字不改 · SHA 釘住):響應式覆蓋層(一支 <style> · 鎖站 CSS / JS / 結構 / CSP 全不動)。

操作員 2026-11-09:「HTML U/I 響應式設計 · 水平 PC 自動最佳化 · 垂直手機自動最佳化 · HEADER 鎖定固定 · 字體大小用現在 Claude 介面大小剛好 ·
階層大小優化 · 自動調節大小 · 三種面板共用一個 HEADER」。

做法:v0101 build 完(鎖站渲染 + 品牌)→ 每頁 + hub 在 </head> 前插一支 `<style id="via-responsive-v0102">`(CSP 本來就 style-src 'unsafe-inline',不必重算;
內嵌 js 一字不動 → script-src sha 不變):
  字級   html 基準 clamp(14px, 0.35vw + 13px, 15.5px)(= Claude 介面正文 14–15.5px)· 行高 1.5 · 鎖站的 9 / 10 px 小字全提到 0.78–0.9rem 的階層
  階層   h1 1.35rem · h2 1.15rem · h3 1rem · 表頭 0.8rem · 表身 0.86rem · 標籤 / 提示 0.78rem · 按鈕 0.85rem;全用 rem → 隨基準自動縮放
  HEADER 一個 #masthead 給三面板(輸入 · 中央 · 證據)共用:position sticky · top 0 · 固定高 --head(64px / 手機 56px)· 標誌限高;rail / 面板頭的 sticky 位移照 --head 跟著走
  PC     ≥ 1100px:三欄 grid(14–16rem · 1fr · 17–19rem)· 兩側 rail sticky 在 header 下
  平板   720–1099px:兩欄(輸入 + 中央)· 證據面板整列落下
  手機   < 720px:單欄 · rail 不 sticky · KPI 兩欄 · 表格橫向可捲(頁面不橫捲)· 標誌 40px
check:每頁 + hub 都有且只有一支 v0102 style、內容 sha 與引擎內建一致、CSP script-src sha 仍 = 內嵌 js(由 v0101 check 驗)。
自測:python VIA_WorkbenchLock_v0102.py --selftest(本版 7 項 + v0101 自測;只在 tempfile 寫)。
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

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0102"
ENGINE = f"VIA_WorkbenchLock_{VERSION}"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VIA_WorkbenchLock_v0101.py"
PRIOR_SHA256 = "66a591ccacb27dcb10ca1758502450c30bdcd681e79bdeb54f838832dc68b9fd"   # v0101(PR #621)
_pp = HERE / PRIOR_NAME
if not _pp.is_file():
    raise SystemExit(f"[RED] 前版 {PRIOR_NAME} 不在 {HERE}")
PRIOR_SHA_OK = hashlib.sha256(_pp.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == PRIOR_SHA256
_spec = importlib.util.spec_from_file_location("via_workbenchlock_v0101_for_v0102", _pp)
BASE = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = BASE
_spec.loader.exec_module(BASE)
V0 = BASE.BASE                       # v0100(鎖站 · 渲染 · check)


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(BASE, name)


STYLE_ID = "via-responsive-v0102"
RESPONSIVE_CSS = """
/* VIA_WorkbenchLock v0102 · 響應式覆蓋層(鎖站 CSS 不動 · 只加這一支)· 操作員 2026-11-09 */
:root{--via-fs:clamp(14px,0.35vw + 13px,15.5px);--head:64px;--brand-logo-height:48px}
html{font-size:var(--via-fs) !important}
body{line-height:1.5;-webkit-text-size-adjust:100%}
h1{font-size:1.35rem !important;line-height:1.25}h2{font-size:1.15rem !important;line-height:1.3}h3{font-size:1rem !important}
#masthead{position:sticky;top:0;z-index:40;min-height:var(--head);height:var(--head);box-sizing:border-box;padding:6px 20px;align-items:center;gap:14px}
#masthead .brand{display:flex;align-items:center;gap:12px;min-width:0}
#masthead .brand-logo{height:var(--brand-logo-height);width:auto;max-width:28vw}
#masthead h1{font-size:1.15rem !important;margin:0}#masthead .subtitle{font-size:.86rem !important}
.hub-link,.global-link,.rail-home{font-size:.82rem !important}
.rail label{font-size:.78rem !important}.hint{font-size:.78rem !important}.button,.export-button{font-size:.85rem !important}
.kpi span{font-size:.8rem !important}.tabs button,.category-tabs button{font-size:.85rem !important}
th{font-size:.8rem !important}td{font-size:.86rem !important}dd,.summary-list dd,.verify-list dd{font-size:.86rem !important}
.notice,.review-note{font-size:.82rem !important}.center-footer,.track p,.shared-row,.workflow-edges{font-size:.78rem !important}
.workflow-node .node-name{font-size:.82rem !important}.subtitle{font-size:.86rem !important}
.rail{top:calc(var(--head) + 10px);max-height:calc(100dvh - var(--head) - 20px)}
.center-panel-head{top:var(--head)}
.workspace{gap:14px;padding:10px 18px 24px}
@media (min-width:1100px){.workspace{grid-template-columns:minmax(14rem,16rem) minmax(0,1fr) minmax(17rem,19rem)}
 .workspace.hide-input{grid-template-columns:minmax(0,1fr) minmax(17rem,19rem)}.workspace.hide-evidence{grid-template-columns:minmax(14rem,16rem) minmax(0,1fr)}
 .workspace.hide-input.hide-evidence{grid-template-columns:minmax(0,1fr)}}
@media (min-width:720px) and (max-width:1099px){.workspace,.workspace.hide-evidence{grid-template-columns:minmax(13rem,15rem) minmax(0,1fr) !important}
 .evidence-rail{grid-column:1 / -1;position:static;max-height:none}.workspace.hide-input,.workspace.hide-input.hide-evidence{grid-template-columns:minmax(0,1fr) !important}}
@media (max-width:719px){:root{--head:56px;--brand-logo-height:40px}
 #masthead{padding:6px 12px;flex-wrap:nowrap}#masthead h1{font-size:1rem !important}#masthead .subtitle{display:none}
 .workspace,.workspace.hide-input,.workspace.hide-evidence,.workspace.hide-input.hide-evidence{grid-template-columns:minmax(0,1fr) !important;gap:10px;padding:8px 10px 20px}
 .rail,.evidence-rail{position:static;max-height:none}.center-panel-head{top:var(--head)}
 .kpis{grid-template-columns:repeat(2,minmax(0,1fr))}
 .center-panel table,.rail table{display:block;max-width:100%;overflow-x:auto}
 body{overflow-x:hidden}}
"""
CSS_SHA256 = hashlib.sha256(RESPONSIVE_CSS.encode("utf-8")).hexdigest()
_STYLE_RX = re.compile(r'<style id="%s">.*?</style>\n?' % STYLE_ID, re.S)


def apply_responsive(html: str) -> tuple[str, dict]:
    """</head> 前插(或換成)本版 style;冪等。不碰 <script> · CSP。"""
    html = _STYLE_RX.sub("", html)
    block = '<style id="%s">%s</style>\n' % (STYLE_ID, RESPONSIVE_CSS)
    if "</head>" in html:
        html = html.replace("</head>", block + "</head>", 1)
        return html, {"injected": True, "css_sha256": CSS_SHA256}
    return html, {"injected": False, "why": "no </head>"}


def build(via: Path, out: Path, open_after: bool = False, logo: str = "", icons: str = "", no_brand: bool = False, no_responsive: bool = False) -> dict:
    res = BASE.build(via, out, open_after=False, logo=logo, icons=icons, no_brand=no_brand)
    if res.get("lamp") != "GREEN" or no_responsive:
        res["responsive"] = {"applied": False, "why": "no-responsive" if no_responsive else "v0101 build 不綠"}
        return res
    files = sorted({Path(v["file"]) for v in res["pages"].values()} | {Path(res["hub"])} | set(out.glob("*.html")))   # 五頁 + hub(index.html 與 Hub_latest 兩份都要)
    pages = {}
    for f in files:
        html2, rec = apply_responsive(f.read_text(encoding="utf-8"))
        f.write_text(html2, encoding="utf-8")
        pages[f.name] = rec
    res["responsive"] = {"applied": True, "engine": ENGINE, "style_id": STYLE_ID, "css_sha256": CSS_SHA256, "pages": pages,
                         "rules": "字級 clamp(14,15.5)px · header sticky 64/56px 三面板共用 · PC 三欄 / 平板兩欄 / 手機單欄 · 階層 rem"}
    (out / "api" / "responsive.json").write_text(json.dumps(res["responsive"], ensure_ascii=False, indent=1), encoding="utf-8")
    if open_after:
        try:
            import os
            if os.name == "nt":
                os.startfile(res["hub"])  # type: ignore[attr-defined]
            else:
                import webbrowser
                webbrowser.open(Path(res["hub"]).as_uri())
        except Exception as exc:  # noqa: BLE001
            V0.WARNINGS.append(f"open 失敗: {exc}")
    return res


def check(via: Path, files=None, out: Path | None = None, write: bool = True, logo: str = "", icons: str = "", no_brand: bool = False, no_responsive: bool = False) -> dict:
    res = BASE.check(via, files=files, out=out, write=False, logo=logo, icons=icons, no_brand=no_brand)
    res["engine"] = ENGINE
    if no_responsive:
        res["responsive"] = {"checked": False}
    else:
        rows = []
        for fr in res["files"]:
            f = Path(fr["file"])
            r = {"file": f.name, "blocks": 0, "css_sha_ok": None}
            if f.exists():
                t = f.read_text(encoding="utf-8", errors="replace")
                blocks = _STYLE_RX.findall(t)
                r["blocks"] = len(blocks)
                r["css_sha_ok"] = len(blocks) == 1 and hashlib.sha256(re.search(r'<style id="%s">(.*?)</style>' % STYLE_ID, blocks[0], re.S).group(1).encode("utf-8")).hexdigest() == CSS_SHA256
                if not r["css_sha_ok"]:
                    fr["lamp"] = "RED"
            rows.append(r)
        res["responsive"] = {"checked": True, "css_sha256": CSS_SHA256, "pages": rows}
    res["lamp"] = "GREEN" if res["lock_site"]["ok"] and res["files"] and all(x["lamp"] == "GREEN" for x in res["files"]) else "RED"
    if write:
        V0.CHECK_OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def selftest() -> int:
    checks = []

    def chk(name, cond, note=""):
        checks.append((name, bool(cond), note))
        print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, (" · " + note) if note else ""), flush=True)
    chk("① 前版 v0101 SHA 釘住 · 鎖站 v0100 仍在鏈上", PRIOR_SHA_OK and hasattr(V0, "lock_site"))
    h = "<html><head><meta http-equiv=\"Content-Security-Policy\" content=\"script-src 'sha256-AAA'; style-src 'unsafe-inline'\"></head><body><header id=\"masthead\"></header><script>const ICONS = {};</script>\n</body></html>"
    h1, r1 = apply_responsive(h)
    h2, _ = apply_responsive(h1)
    chk("② 注入在 </head> 前 · 冪等(兩次仍一支)· CSP / script 一字不動", r1["injected"] and h1.count('id="%s"' % STYLE_ID) == 1 and h2 == h1 and "sha256-AAA" in h2 and "const ICONS = {};" in h2)
    chk("③ CSS:基準 clamp 14–15.5px · header sticky + --head · 三段 media(≥1100 · 720–1099 · <720)· 鎖站 9/10px 選擇器全覆蓋到 rem",
        "clamp(14px" in RESPONSIVE_CSS and "#masthead{position:sticky" in RESPONSIVE_CSS and RESPONSIVE_CSS.count("@media") == 3
        and all(s in RESPONSIVE_CSS for s in (".rail label", "th{font-size", "td{font-size", ".kpi span", ".center-footer", ".workflow-edges", ".export-button")) and RESPONSIVE_CSS.count("!important") >= 20)
    via = V0.resolve_via("")
    with tempfile.TemporaryDirectory(prefix="wbl0102_") as td:
        out = Path(td) / "wb"
        res = build(via, out)
        ok_build = res.get("lamp") == "GREEN" and res.get("responsive", {}).get("applied") is True
        pages = list(res.get("pages", {}).values())
        files = [Path(v["file"]) for v in pages] + ([Path(res["hub"])] if res.get("hub") else [])
        files = sorted(out.glob("*.html"))
        chk("④ build:v0101 綠 → 五頁 + hub(index + Hub_latest)都插一支 v0102 style · api/responsive.json 在", ok_build and len(files) >= 6 and all(f.read_text(encoding="utf-8").count('id="%s"' % STYLE_ID) == 1 for f in files) and (out / "api" / "responsive.json").is_file())
        res2 = build(via, out)
        chk("⑤ 重 build 冪等(仍一支)", res2.get("lamp") == "GREEN" and all(f.read_text(encoding="utf-8").count('id="%s"' % STYLE_ID) == 1 for f in files))
        c = check(via, files=files, out=out, write=False)
        chk("⑥ check 綠:每頁 css sha 一致 · 品牌三項(v0101)仍過 · CSP 仍 = 內嵌 js", c["lamp"] == "GREEN" and all(p["css_sha_ok"] for p in c["responsive"]["pages"]) and c["brand"]["checked"])
        f0 = files[0]
        f0.write_text(f0.read_text(encoding="utf-8").replace("--via-fs:clamp(14px", "--via-fs:clamp(9px"), encoding="utf-8")
        c2 = check(via, files=files, out=out, write=False)
        chk("⑦ 篡改 CSS → 該頁紅 · 整體 RED", c2["lamp"] == "RED" and c2["responsive"]["pages"][0]["css_sha_ok"] is False)
    n = sum(1 for _, ok, _ in checks if ok)
    print("  == v0102 %d/%d" % (n, len(checks)), flush=True)
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        prior_rc = BASE.selftest()
    good = n == len(checks) and prior_rc == 0
    print("[%s] %s selftest · 本版 %d/%d · 前版鏈 v0101 %s" % ("PASS" if good else "FAIL", ENGINE, n, len(checks), "PASS" if prior_rc == 0 else "FAIL"), flush=True)
    return 0 if good else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv or argv[:1] == ["selftest"]:
        return selftest()
    ap = argparse.ArgumentParser(prog=ENGINE, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verb", nargs="?", default="all", choices=["kit", "build", "check", "all"])
    ap.add_argument("--via", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--files", nargs="*")
    ap.add_argument("--logo", default="")
    ap.add_argument("--icons", default="")
    ap.add_argument("--no-brand", action="store_true")
    ap.add_argument("--no-responsive", action="store_true", help="不加響應式層(= v0101 原樣)")
    a = ap.parse_args(argv)
    via = V0.resolve_via(a.via)
    out = Path(a.out).resolve() if a.out else via / "VIA_Reports" / "workbench"
    rc = 0
    if a.verb in ("kit", "all"):
        info = V0.kit(via)
        print(f"[kit] {info['lamp']} · 鎖站 {'OK' if info['lock_site']['ok'] else info['lock_site']['problems']} · token {info['token_count']}")
        rc |= info["lamp"] != "GREEN"
    if a.verb in ("build", "all"):
        res = build(via, out, open_after=a.open, logo=a.logo, icons=a.icons, no_brand=a.no_brand, no_responsive=a.no_responsive)
        if res["lamp"] != "GREEN":
            print(f"[build] RED · {res.get('reason')}")
            return 1
        for k, v in res["pages"].items():
            print(f"[build] {k:5s} rows {sum(v['rows'].values()):4d}")
        r = res.get("responsive") or {}
        print(f"[build] 品牌 {'套用' if (res.get('brand') or {}).get('applied') else '未套'} · 響應式 {'套用 ' + r.get('css_sha256', '')[:12] if r.get('applied') else '未套'} · hub → {res['hub']}")
    if a.verb in ("check", "all"):
        chk = check(via, files=[Path(f) for f in a.files] if a.files else None, out=out, logo=a.logo, icons=a.icons, no_brand=a.no_brand, no_responsive=a.no_responsive)
        for f in chk["files"]:
            print(f"[check] {f['lamp']:5s} {Path(f['file']).name}")
        print(f"[check] {chk['lamp']} · 品牌 {'驗' if chk['brand'].get('checked') else '略'} · 響應式 {'驗' if chk['responsive'].get('checked') else '略'} → {V0.CHECK_OUT.name}")
        rc |= chk["lamp"] != "GREEN"
    return int(rc)


if __name__ == "__main__":
    sys.exit(main())
