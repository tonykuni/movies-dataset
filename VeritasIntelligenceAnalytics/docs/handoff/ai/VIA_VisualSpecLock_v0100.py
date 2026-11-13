#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_VisualSpecLock v0100 — 自建平台視覺規格鎖:顏色 · 字型 · 字級尺度 · 間距 · 圓角 · 斷點 · 品牌,從鎖定正本「抽出來」並釘 sha。

操作員 2026-11-10 令「自建平台視覺鎖定等看來顏色設計規模也要記錄下額外鎖住」。
既有兩把視覺鎖只鎖了一部分:
  · VIA_WorkbenchLock(工作台 v0106.4 鎖站):kit 只抽 :root 20 個 token(色 + 字族 + 表頭高),字級 / 間距 / 圓角 / 斷點沒記。
  · VIA_VisualLock(Atlas --vl-*):只管色彩 token 與「不准生 hex」閘。
本檔補這一塊:**只讀**兩個鎖定正本 + 品牌夾 + v0102 響應式覆蓋層,抽出完整設計尺度,寫成一本版號鎖冊;
`check` 重抽一次比對鎖冊,任何一個值或檔 sha 變了就紅。不改任何正本、不連網。

動詞:
  lock  [--out <json>]   抽規格 → 寫鎖冊(只增:同名檔已存在就拒寫,要換版請出新版號檔)
  check [--lock <json>]  重抽比對鎖冊;一致 GREEN、不一致 RED(逐項列出)
  show                   印規格摘要(色盤 · 字級階 · 間距階 · 斷點)
  --selftest             夾具自測(只寫沙盒)
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
import json
import re
import shutil
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
SCHEMA = "via.visualspec.lock/1"
SOURCES = {
    "workbench_site": Path("review") / "VIA_Workbench_LockSite_v0106_4",
    "workbench_brand": Path("review") / "VIA_Workbench_Brand_v0100",
    "atlas_site": Path("review") / "VIA_Atlas_LocalSite_v0100",
}
OVERLAY = Path("docs") / "handoff" / "ai" / "VIA_WorkbenchLock_v0102.py"   # RESPONSIVE_CSS 常數
DEFAULT_LOCK = Path("docs") / "handoff" / "ai" / "VIA_VisualSpecLock_v0100.json"

VAR_RE = re.compile(r"(--[a-zA-Z0-9-]+)\s*:\s*([^;}]+)")
PROP_RE = {
    "font_size": re.compile(r"font-size\s*:\s*([^;}]+)"),
    "font_weight": re.compile(r"font-weight\s*:\s*([^;}]+)"),
    "line_height": re.compile(r"line-height\s*:\s*([^;}]+)"),
    "letter_spacing": re.compile(r"letter-spacing\s*:\s*([^;}]+)"),
    "radius": re.compile(r"border-radius\s*:\s*([^;}]+)"),
    "spacing": re.compile(r"(?:^|[;{\s])(?:padding|margin|gap|row-gap|column-gap)(?:-[a-z]+)?\s*:\s*([^;}]+)"),
    "shadow": re.compile(r"box-shadow\s*:\s*([^;}]+)"),
    "max_width": re.compile(r"max-width\s*:\s*([^;}]+)"),
}
MEDIA_RE = re.compile(r"@media\s*([^{]+)\{")
HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def via_root(start: Path | None = None) -> Path:
    p = (start or Path(__file__)).resolve()
    for q in [p] + list(p.parents):
        if (q / "supportive modules").is_dir() and (q / "review").is_dir():
            return q
    raise SystemExit("[VisualSpecLock] 找不到 VIA 根(要有 supportive modules/ 與 review/)")


def style_text(path: Path) -> str:
    """.css 全文;.html 只取 <style> 區塊與 style="" 屬性(不碰 <script>)。"""
    t = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".css":
        return t
    blocks = re.findall(r"<style[^>]*>(.*?)</style>", t, flags=re.S | re.I)
    attrs = re.findall(r'style="([^"]*)"', t, flags=re.I)
    return "\n".join(blocks + [a + ";" for a in attrs])


def overlay_css(via: Path) -> str:
    p = via / OVERLAY
    if not p.is_file():
        return ""
    m = re.search(r'RESPONSIVE_CSS\s*=\s*"""(.*?)"""', p.read_text(encoding="utf-8", errors="replace"), flags=re.S)
    return m.group(1) if m else ""


def _norm(v: str) -> str:
    return re.sub(r"\s+", " ", v.strip().replace("!important", "").strip())


def scale(css: str) -> dict:
    out = {}
    for k, rx in PROP_RE.items():
        c = Counter(_norm(m) for m in rx.findall(css) if not _norm(m).startswith("var(") or True)
        out[k] = dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))
    out["breakpoints"] = dict(sorted(Counter(_norm(m) for m in MEDIA_RE.findall(css)).items()))
    out["raw_hex_outside_root"] = sorted(set(HEX_RE.findall(re.sub(r":root\s*\{[^}]*\}", "", css))))
    return out


def root_vars(css: str) -> dict:
    out = {}
    for block in re.findall(r":root[^{]*\{([^}]*)\}", css):
        for k, v in VAR_RE.findall(block):
            out.setdefault(k, _norm(v))
    return out


def extract(via: Path) -> dict:
    sources, files = {}, {}
    for key, rel in SOURCES.items():
        d = via / rel
        if not d.is_dir():
            sources[key] = {"path": rel.as_posix(), "present": False}
            continue
        css_all, fl = [], {}
        for f in sorted(d.rglob("*")):
            if not f.is_file() or f.name.startswith("."):
                continue
            b = f.read_bytes()
            fl[f.relative_to(via).as_posix()] = sha256(b)
            if f.suffix.lower() in (".css", ".html"):
                css_all.append(style_text(f))
        css = "\n".join(css_all)
        files.update(fl)
        sources[key] = {"path": rel.as_posix(), "present": True, "files": len(fl),
                        "tokens": root_vars(css), "scale": scale(css)}
    ov = overlay_css(via)
    sources["responsive_overlay_v0102"] = {"path": OVERLAY.as_posix(), "present": bool(ov),
                                           "css_sha256": sha256(ov.encode("utf-8")) if ov else None,
                                           "scale": scale(ov) if ov else {}}
    brand = via / SOURCES["workbench_brand"] / "icons_v0100.json"
    if brand.is_file():
        try:
            sources["workbench_brand"]["icons_manifest"] = sorted(json.loads(brand.read_text(encoding="utf-8")).keys())[:60]
        except (OSError, ValueError):
            pass
    palette = {}
    for key in ("workbench_site", "atlas_site"):
        for k, v in (sources.get(key, {}).get("tokens") or {}).items():
            if HEX_RE.fullmatch(v.strip()) or v.strip().startswith(("rgb", "hsl")):
                palette[f"{key}:{k}"] = v
    spec = {"schema": SCHEMA, "version": VERSION, "sources": sources, "palette": dict(sorted(palette.items())),
            "files": dict(sorted(files.items()))}
    spec["fingerprint"] = sha256(json.dumps({k: spec[k] for k in ("sources", "palette", "files")},
                                            ensure_ascii=False, sort_keys=True).encode("utf-8"))
    return spec


def diff(old: dict, new: dict) -> list:
    out = []
    for f in sorted(set(old.get("files", {})) | set(new.get("files", {}))):
        a, b = old.get("files", {}).get(f), new.get("files", {}).get(f)
        if a != b:
            out.append(f"檔 {f}:{(a or '缺')[:12]} → {(b or '缺')[:12]}")
    for k in sorted(set(old.get("palette", {})) | set(new.get("palette", {}))):
        a, b = old.get("palette", {}).get(k), new.get("palette", {}).get(k)
        if a != b:
            out.append(f"色 {k}:{a} → {b}")
    for key in sorted(set(old.get("sources", {})) | set(new.get("sources", {}))):
        sa, sb = old.get("sources", {}).get(key, {}), new.get("sources", {}).get(key, {})
        if sa.get("tokens") != sb.get("tokens"):
            out.append(f"token {key} 變了")
        if sa.get("scale") != sb.get("scale"):
            out.append(f"尺度 {key} 變了(字級 / 間距 / 圓角 / 斷點)")
        if sa.get("css_sha256") != sb.get("css_sha256"):
            out.append(f"覆蓋層 {key} css sha 變了")
    return out


def cmd_lock(args) -> int:
    via = via_root()
    out = via / (args.out or DEFAULT_LOCK)
    if out.exists():
        print(f"[不覆蓋] {out.relative_to(via)} 已存在 —— 只增不減;要換版請出新版號檔(--out …_v0101.json)")
        return 1
    spec = extract(via)
    spec["locked_at"] = utc()
    spec["locked_by"] = "VIA_VisualSpecLock_" + VERSION
    out.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[鎖] {out.relative_to(via)} · 檔 {len(spec['files'])} · 色 {len(spec['palette'])} · 指紋 {spec['fingerprint'][:16]}")
    return 0


def cmd_check(args) -> int:
    via = via_root()
    lp = via / (args.lock or DEFAULT_LOCK)
    if not lp.is_file():
        print(f"[RED] 沒有鎖冊 {lp.relative_to(via)} —— 先跑 lock")
        return 1
    old = json.loads(lp.read_text(encoding="utf-8"))
    d = diff(old, extract(via))
    if d:
        print(f"[RED] 視覺規格與鎖冊不一致 {len(d)} 項:")
        for x in d[:40]:
            print("  · " + x)
        return 1
    print(f"[GREEN] 視覺規格與鎖冊一致 · 檔 {len(old.get('files', {}))} · 色 {len(old.get('palette', {}))} · 指紋 {old.get('fingerprint', '')[:16]}")
    return 0


def cmd_show(args) -> int:
    spec = extract(via_root())
    print(f"[色盤] {len(spec['palette'])}")
    for k, v in spec["palette"].items():
        print(f"  {k:<40} {v}")
    for key, s in spec["sources"].items():
        sc = s.get("scale") or {}
        if not sc:
            continue
        print(f"[{key}] 字級 {list(sc.get('font_size', {}))[:12]}")
        print(f"   間距 {list(sc.get('spacing', {}))[:12]}")
        print(f"   圓角 {list(sc.get('radius', {}))[:8]} · 斷點 {list(sc.get('breakpoints', {}))}")
    return 0


def selftest() -> int:
    checks = []

    def ck(name, cond, note=""):
        checks.append((name, bool(cond), note))

    tmp = Path(tempfile.mkdtemp(prefix="vspec_"))
    try:
        via = tmp / "via"
        (via / "supportive modules").mkdir(parents=True)
        site = via / SOURCES["workbench_site"]
        site.mkdir(parents=True)
        (site / "a.css").write_text(":root{--bg:#0b1020;--ink:#e8eefc;--sans:Inter,sans-serif}\n"
                                    ".x{font-size:14px;padding:8px 12px;border-radius:6px;gap:8px}\n"
                                    "@media (max-width: 720px){.x{font-size:13px}}\n.y{color:#ff0000}\n", encoding="utf-8")
        (site / "a.html").write_text('<style>.h{font-size:20px;margin:0}</style><div style="padding:4px"></div>'
                                     "<script>var s='font-size:99px'</script>", encoding="utf-8")
        atlas = via / SOURCES["atlas_site"]
        atlas.mkdir(parents=True)
        (atlas / "index.html").write_text("<style>:root{--vl-bg:#ffffff;--vl-accent:rgb(1,2,3)}</style>", encoding="utf-8")
        ovp = via / OVERLAY
        ovp.parent.mkdir(parents=True)
        ovp.write_text('RESPONSIVE_CSS = """@media (max-width: 480px){.x{padding:4px}}"""\n', encoding="utf-8")
        spec = extract(via)
        ws = spec["sources"]["workbench_site"]
        ck("抽到 :root token", ws["tokens"].get("--bg") == "#0b1020" and "--sans" in ws["tokens"])
        ck("字級尺度含 css 與 html <style> 與 style 屬性",
           set(ws["scale"]["font_size"]) >= {"14px", "13px", "20px"})
        ck("<script> 內字串不算", "99px" not in ws["scale"]["font_size"])
        ck("間距含 padding / gap / style 屬性", {"8px 12px", "8px", "4px"} <= set(ws["scale"]["spacing"]))
        ck("圓角 / 斷點抽到", "6px" in ws["scale"]["radius"] and "(max-width: 720px)" in ws["scale"]["breakpoints"])
        ck(":root 外寫死 hex 被列出", "#ff0000" in ws["scale"]["raw_hex_outside_root"])
        ck("色盤含兩鎖站(hex 與 rgb)", spec["palette"].get("atlas_site:--vl-accent") == "rgb(1,2,3)"
           and spec["palette"].get("workbench_site:--bg") == "#0b1020")
        ck("響應式覆蓋層有 sha 與斷點", spec["sources"]["responsive_overlay_v0102"]["css_sha256"]
           and "(max-width: 480px)" in spec["sources"]["responsive_overlay_v0102"]["scale"]["breakpoints"])
        ck("缺的來源誠實標 present False", spec["sources"]["workbench_brand"]["present"] is False)
        ck("指紋穩定(同輸入兩次一樣)", extract(via)["fingerprint"] == spec["fingerprint"])
        # lock / check / 不覆蓋
        old_root = globals()["via_root"]
        globals()["via_root"] = lambda start=None: via
        try:
            ns = argparse.Namespace(out=None, lock=None)
            ck("lock 寫鎖冊", cmd_lock(ns) == 0 and (via / DEFAULT_LOCK).is_file())
            ck("lock 只增:第二次拒寫", cmd_lock(ns) == 1)
            ck("check 一致 → GREEN", cmd_check(ns) == 0)
            (site / "a.css").write_text((site / "a.css").read_text(encoding="utf-8").replace("#0b1020", "#0b1021"), encoding="utf-8")
            ck("改一個色 → check RED", cmd_check(ns) == 1)
            d = diff(json.loads((via / DEFAULT_LOCK).read_text(encoding="utf-8")), extract(via))
            ck("RED 逐項列出(色 + 檔)", any(x.startswith("色 workbench_site:--bg") for x in d) and any(x.startswith("檔 ") for x in d))
        finally:
            globals()["via_root"] = old_root
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ok = sum(1 for _, c, _ in checks if c)
    for name, c, note in checks:
        if not c:
            print(f"  [FAIL] {name}" + (f" — {note}" if note else ""))
    print(f"[計] VIA_VisualSpecLock {VERSION} 自測 {ok}/{len(checks)} · " + ("PASS" if ok == len(checks) else "FAIL"))
    return 0 if ok == len(checks) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="VIA_VisualSpecLock_" + VERSION, description="自建平台視覺規格鎖(只讀正本)")
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="verb")
    p = sub.add_parser("lock")
    p.add_argument("--out")
    p.set_defaults(fn=cmd_lock)
    p = sub.add_parser("check")
    p.add_argument("--lock")
    p.set_defaults(fn=cmd_check)
    p = sub.add_parser("show")
    p.set_defaults(fn=cmd_show)
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if not getattr(args, "fn", None):
        ap.print_help()
        return 0
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
