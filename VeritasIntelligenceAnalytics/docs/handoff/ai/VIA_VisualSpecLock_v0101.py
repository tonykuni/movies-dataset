#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_VisualSpecLock v0101 — 薄尾:Manus 線上站為最高權威 · theme(元件取主題)· audit(頁面不違反鎖定風格)

操作員令(2026-11-11):「自建平台 HTML U/I 視覺包含顏色設計 LOGO 字體大小百分百鎖定 MANUS(https://viaatlas-39ozanmz.manus.space)·
各類元件不違反其風格顏色視覺設計 · 動態調整 · 鎖定視覺怎樣去自動隨系統更動去調整 · 節省後續修改反覆耗費 token」。
實測(2026-11-11):線上站 = review/VIA_Workbench_LockSite_v0106_4 的線上版(標題 VIA Subsystem Workspaces v0106.4 · LOGO 位元組相同);
差異只有:--green #3d7a52 → #2c4f4a(= 鎖內 --g-ink)· 新增 --red #9e2b25(= 鎖內 --r-ink);字型三組一致。快照:review/VIA_Atlas_ManusLive_20261111/。
本版(v0100 一字不動):
  · 來源多一個 manus_live(快照夾);解析主題 resolved = manus_live > workbench_site > atlas_site(同名 token 以線上站為準)。
  · lock 預設寫 VIA_VisualSpecLock_v0101.json(只增;v0100 鎖照留)· 多記 resolved · fonts · logo_sha256。
  · theme [--json]       → 印 :root{…}(或 JSON)。元件產頁時呼叫 theme_vars() / theme_css():讀「最新一版鎖冊」——
                           鎖換版,所有頁面重跑就跟著換,不必逐頁改(省 token 的核心)。
  · audit <html…>        → 頁面用到的顏色 / 字體都要在鎖內;鎖外的列出來(RED)。
  · check / show 照 v0100(check 對 v0101 鎖)。
零網路(快照由操作員 / AI 另行抓進倉,本工具只讀檔);不碰 TA-Lib;不讀寫同意閘。
"""
from __future__ import annotations

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
HERE = Path(__file__).resolve().parent
_STEM = "VIA_VisualSpecLock"
LIVE_DIR = Path("review") / "VIA_Atlas_ManusLive_20261111"
DEFAULT_LOCK_V0101 = Path("docs") / "handoff" / "ai" / "VIA_VisualSpecLock_v0101.json"
AUTHORITY = ("manus_live", "workbench_site", "atlas_site")
COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)")
FONT_RE = re.compile(r"font-family\s*:\s*([^;}\"]+)")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
PRIOR.SOURCES.setdefault("manus_live", LIVE_DIR)            # v0100 extract 逐一走 SOURCES:多一個線上站來源


def __getattr__(name):
    return getattr(PRIOR, name)


def norm_color(v: str) -> str:
    v = v.strip().lower()
    if re.fullmatch(r"#[0-9a-f]{3}", v):
        v = "#" + "".join(c * 2 for c in v[1:])
    return v.replace(" ", "")


def resolve(sources: dict) -> dict:
    """同名 token 以權威序取值(線上站 > 鎖站 > Atlas 本地站)。"""
    out = {}
    for key in reversed(AUTHORITY):
        out.update((sources.get(key) or {}).get("tokens") or {})
    return dict(sorted(out.items()))


def logo_sha(via: Path) -> str | None:
    f = via / LIVE_DIR / "index.html"
    if not f.is_file():
        return None
    m = re.search(r"data:image/png;base64,([A-Za-z0-9+/=]+)", f.read_text(encoding="utf-8", errors="replace"))
    return hashlib.sha256(base64.b64decode(m.group(1))).hexdigest() if m else None


def extract(via: Path) -> dict:
    spec = PRIOR.extract(via)
    live = spec["sources"].get("manus_live") or {}
    for k, v in (live.get("tokens") or {}).items():
        if PRIOR.HEX_RE.fullmatch(v.strip()) or v.strip().startswith(("rgb", "hsl")):
            spec["palette"][f"manus_live:{k}"] = v
    spec["palette"] = dict(sorted(spec["palette"].items()))
    spec["resolved"] = resolve(spec["sources"])
    spec["fonts"] = {k: v for k, v in spec["resolved"].items() if k in ("--sans", "--serif", "--mono")}
    spec["logo_sha256"] = logo_sha(via)
    spec["authority"] = list(AUTHORITY)
    spec["version"] = VERSION
    spec["fingerprint"] = PRIOR.sha256(json.dumps({k: spec[k] for k in ("sources", "palette", "files", "resolved")},
                                                  ensure_ascii=False, sort_keys=True).encode("utf-8"))
    return spec


def latest_lock(via: Path | None = None) -> Path | None:
    d = (via or PRIOR.via_root()) / "docs" / "handoff" / "ai"
    locks = sorted(d.glob(_STEM + "_v*.json"), key=_vnum)
    return locks[-1] if locks else None


def theme_vars(lock: Path | None = None) -> dict:
    """元件取主題:最新一版鎖冊的 resolved(舊鎖沒有 resolved 就用它的 workbench_site tokens)。"""
    p = lock or latest_lock()
    if not p or not p.is_file():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    return d.get("resolved") or (d.get("sources", {}).get("workbench_site", {}).get("tokens") or {})


def theme_css(lock: Path | None = None) -> str:
    v = theme_vars(lock)
    return ":root{" + ";".join(f"{k}:{val}" for k, val in v.items()) + "}" if v else ""


def allowed(lock_spec: dict) -> tuple[set, set]:
    colors = {norm_color(v) for v in lock_spec.get("palette", {}).values()}
    colors |= {norm_color(v) for v in (lock_spec.get("resolved") or {}).values() if COLOR_RE.fullmatch(v.strip())}
    colors |= {"#ffffff", "#000000", "transparent"}
    fonts = {f.strip().strip("'\"").lower() for v in (lock_spec.get("fonts") or {}).values() for f in v.split(",")}
    fonts |= {"inherit", "monospace", "sans-serif", "serif", "system-ui"}
    return colors, fonts


def audit_text(text: str, lock_spec: dict) -> dict:
    """頁面(只看 <style> 與 style="")用到的顏色 / 字體,有沒有鎖外的。var(--x) 引用算合規。"""
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", text, re.S | re.I) + re.findall(r'style="([^"]*)"', text))
    colors, fonts = allowed(lock_spec)
    used_c = {norm_color(c) for c in COLOR_RE.findall(css)}
    used_f = {f.strip().strip("'\"").lower() for v in FONT_RE.findall(css) if "var(" not in v for f in v.split(",")}
    bad_c = sorted(c for c in used_c if c not in colors)
    bad_f = sorted(f for f in used_f if f and f not in fonts)
    return {"lamp": "GREEN" if not bad_c and not bad_f else "RED", "colors_used": len(used_c), "fonts_used": len(used_f),
            "off_palette": bad_c, "off_fonts": bad_f}


def _lock_spec(args_lock: str | None) -> dict:
    via = PRIOR.via_root()
    p = via / args_lock if args_lock else latest_lock(via)
    return json.loads(p.read_text(encoding="utf-8")) if p and p.is_file() else extract(via)


def cmd_lock(args) -> int:
    via = PRIOR.via_root()
    out = via / (args.out or DEFAULT_LOCK_V0101)
    if out.exists():
        print(f"[不覆蓋] {out.relative_to(via)} 已存在 —— 只增不減;換版請 --out …_v0102.json")
        return 1
    spec = extract(via)
    spec["locked_at"] = PRIOR.utc()
    spec["locked_by"] = _STEM + "_" + VERSION
    out.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[鎖] {out.relative_to(via)} · 檔 {len(spec['files'])} · 色 {len(spec['palette'])} · 解析 token {len(spec['resolved'])}"
          f" · LOGO {str(spec['logo_sha256'])[:12]} · 指紋 {spec['fingerprint'][:16]}")
    return 0


def cmd_check(args) -> int:
    via = PRIOR.via_root()
    lp = via / (args.lock or DEFAULT_LOCK_V0101)
    if not lp.is_file():
        print(f"[RED] 沒有鎖冊 {lp.relative_to(via)} —— 先跑 lock")
        return 1
    old = json.loads(lp.read_text(encoding="utf-8"))
    d = PRIOR.diff(old, extract(via))
    if old.get("resolved") != extract(via)["resolved"]:
        d.append("解析主題(resolved)變了")
    if d:
        print(f"[RED] 視覺規格與鎖冊不一致 {len(d)} 項:")
        for x in d[:40]:
            print("  · " + x)
        return 1
    print(f"[GREEN] 視覺規格與鎖冊一致 · 檔 {len(old.get('files', {}))} · 色 {len(old.get('palette', {}))} · 指紋 {old.get('fingerprint', '')[:16]}")
    return 0


def cmd_theme(args) -> int:
    lp = (PRIOR.via_root() / args.lock) if args.lock else None
    print(json.dumps(theme_vars(lp), ensure_ascii=False, indent=1) if args.json else theme_css(lp))
    return 0


def cmd_audit(args) -> int:
    spec = _lock_spec(args.lock)
    worst = 0
    for f in args.files:
        r = audit_text(Path(f).read_text(encoding="utf-8", errors="replace"), spec)
        worst = max(worst, r["lamp"] == "RED")
        print(f"[{r['lamp']}] {f} · 色 {r['colors_used']} · 字體 {r['fonts_used']}"
              + (f" · 鎖外色 {r['off_palette'][:8]}" if r["off_palette"] else "") + (f" · 鎖外字體 {r['off_fonts'][:6]}" if r["off_fonts"] else ""))
    return worst


def selftest() -> int:
    checks = []

    def ck(name, cond, note=""):
        checks.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note else ""))

    keep = PRIOR.SOURCES.pop("manus_live", None)
    try:
        rc0 = PRIOR.selftest()
    finally:
        if keep is not None:
            PRIOR.SOURCES["manus_live"] = keep
    ck("v0100 自測照過(來源三個 · lock 只增 · check 變了就紅)", rc0 == 0, f"rc {rc0}")
    src = {"atlas_site": {"tokens": {"--green": "#111111", "--a": "1"}}, "workbench_site": {"tokens": {"--green": "#3d7a52", "--bg": "#f2f1ec"}},
           "manus_live": {"tokens": {"--green": "#2c4f4a", "--red": "#9e2b25"}}}
    r = resolve(src)
    ck("權威序:線上站 > 鎖站 > Atlas(--green 取 #2c4f4a · 各來源獨有 token 都留)", r["--green"] == "#2c4f4a" and r["--bg"] == "#f2f1ec"
       and r["--red"] == "#9e2b25" and r["--a"] == "1", r.get("--green"))
    with tempfile.TemporaryDirectory() as td:
        lock = Path(td) / "VIA_VisualSpecLock_v0199.json"
        spec = {"palette": {"x:--bg": "#f2f1ec", "x:--ink": "#33403f"}, "resolved": {"--bg": "#f2f1ec", "--ink": "#33403f", "--sans": "'Microsoft JhengHei','Segoe UI',sans-serif"},
                "fonts": {"--sans": "'Microsoft JhengHei','Segoe UI',sans-serif"}}
        lock.write_text(json.dumps(spec), encoding="utf-8")
        css = theme_css(lock)
        ck("theme_css:從鎖冊產 :root(元件嵌入即跟鎖走)", css.startswith(":root{") and "--bg:#f2f1ec" in css and "--sans:" in css, css[:60])
        good = '<style>:root{--bg:#F2F1EC}body{background:var(--bg);color:#33403f;font-family:"Microsoft JhengHei",sans-serif}</style>'
        bad = '<style>body{color:#ff0000;font-family:Comic Sans MS}</style><div style="background:#123456"></div>'
        ag, ab = audit_text(good, spec), audit_text(bad, spec)
        ck("audit:鎖內色(大小寫 / 縮寫正規化)+ var() 引用 → GREEN", ag["lamp"] == "GREEN", ag)
        ck("audit:鎖外色(含 style=\"\" 內)與鎖外字體 → RED 並列出", ab["lamp"] == "RED" and "#ff0000" in ab["off_palette"]
           and "#123456" in ab["off_palette"] and "comic sans ms" in ab["off_fonts"], ab)
    via = PRIOR.via_root()
    if (via / LIVE_DIR / "index.html").is_file():
        live = extract(via)
        ck("真快照:線上站來源在 · --green = #2c4f4a · --red 補上 · LOGO 與鎖站 png 同位元組",
           live["sources"]["manus_live"].get("present") and live["resolved"].get("--green") == "#2c4f4a" and live["resolved"].get("--red") == "#9e2b25"
           and live["logo_sha256"] == hashlib.sha256((via / "review/VIA_Workbench_LockSite_v0106_4/veritas_logo_header_v0105.png").read_bytes()).hexdigest(),
           live["resolved"].get("--green"))
        page = (via / LIVE_DIR / "index.html").read_text(encoding="utf-8", errors="replace")
        ck("線上站自己過 audit(鎖 = 它自己,不可自相矛盾)", audit_text(page, live)["lamp"] == "GREEN", audit_text(page, live)["off_palette"][:5])
    srct = Path(__file__).read_text(encoding="utf-8")
    ck("零網路 · 不碰 TA-Lib · 不寫同意閘", not re.search(r"^\s*import\s+(requests|urllib|httpx|talib)", srct, re.M)
       and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", srct))
    print(f"[計] {_STEM} {VERSION} 本版 {sum(checks)}/{len(checks)} " + ("PASS" if all(checks) else "FAIL"))
    return 0 if all(checks) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog=_STEM + "_" + VERSION, description="視覺規格鎖(線上站為權威 · theme · audit)")
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="verb")
    p = sub.add_parser("lock"); p.add_argument("--out"); p.set_defaults(fn=cmd_lock)
    p = sub.add_parser("check"); p.add_argument("--lock"); p.set_defaults(fn=cmd_check)
    p = sub.add_parser("show"); p.set_defaults(fn=PRIOR.cmd_show)
    p = sub.add_parser("theme"); p.add_argument("--lock"); p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_theme)
    p = sub.add_parser("audit"); p.add_argument("files", nargs="+"); p.add_argument("--lock"); p.set_defaults(fn=cmd_audit)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not getattr(a, "fn", None):
        ap.print_help()
        return 0
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
