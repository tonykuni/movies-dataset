# -*- coding: utf-8 -*-
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
# ============================================================================
#  VHS_Reader.py  -  Veritas HTML Spec Reader  (VIA / VPN family)
#  M01 : HTML U/I full-spec extractor + LOCK/EDITABLE classifier
#  Stdlib only (re, json, pathlib, html.parser, argparse, datetime, hashlib)
#  Append-only (zhi-zeng-bu-jian). UTF-8 No BOM in/out.
# ============================================================================
import re
import json
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser

VHS_VERSION = "v01.0"

# ----------------------------------------------------------------------------
#  Built-in LOCK registry (VPN v3.5 visual lock). Overridable via JSON, add-only.
# ----------------------------------------------------------------------------
DEFAULT_LOCK_REGISTRY = {
    "palette": {
        "#4c78a8": "VPN.blue",
        "#9c9890": "VPN.grey",
        "#439a9a": "VPN.teal",
    },
    "fonts": {
        "dm mono": "VPN.mono",
        "dm sans": "VPN.sans",
        "syne": "VPN.display",
    },
    "header_text": [
        "VeritasIntelligenceAnalytics Environment Governance Nexus (VEGN)",
        "VERITAS INTELLIGENCE SYSTEM",
    ],
    "marker_attrs": ["data-lock", "data-locked", "data-immutable"],
    "marker_comments": ["@lock", "lock:", "immutable", "do not edit", "\u4e0d\u53ef\u6539"],
    "var_lock_keywords": ["lock", "locked", "fixed", "brand", "vpn"],
}

HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
RGB_RE = re.compile(r"rgba?\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+(?:\s*,\s*[\d.]+)?\s*\)")
VAR_RE = re.compile(r"(--[a-zA-Z0-9_-]+)\s*:\s*([^;}{]+)")
FONTFAM_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.IGNORECASE)
FONTSIZE_RE = re.compile(r"font-size\s*:\s*([^;}{]+)", re.IGNORECASE)
FONTWEIGHT_RE = re.compile(r"font-weight\s*:\s*([^;}{]+)", re.IGNORECASE)
DISPLAY_RE = re.compile(r"(?<![\w-])display\s*:\s*([^;}{]+)", re.IGNORECASE)
GRIDCOL_RE = re.compile(r"(?<![\w-])grid-template-columns\s*:\s*([^;}{]+)", re.IGNORECASE)
MAXW_RE = re.compile(r"(?<![\w-])max-width\s*:\s*([^;}{]+)", re.IGNORECASE)
GAP_RE = re.compile(r"(?<![\w-])gap\s*:\s*([^;}{]+)", re.IGNORECASE)
RADIUS_RE = re.compile(r"(?<![\w-])border-radius\s*:\s*([^;}{]+)", re.IGNORECASE)
PAD_RE = re.compile(r"(?<![\w-])padding\s*:\s*([^;}{]+)", re.IGNORECASE)
MARGIN_RE = re.compile(r"(?<![\w-])margin\s*:\s*([^;}{]+)", re.IGNORECASE)
COMMENT_RE = re.compile(r"<!--(.*?)-->", re.DOTALL)


def norm_color(c):
    c = c.strip().lower()
    if c.startswith("#") and len(c) == 4:  # expand #abc -> #aabbcc
        c = "#" + "".join(ch * 2 for ch in c[1:])
    return c


def first_font(decl):
    # first family token from a font-family declaration
    token = decl.split(",")[0].strip().strip("'\"")
    return token.lower()


class _Tag(HTMLParser):
    """Collect lightweight structural facts: title, h1, header text, logo, counts."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.h1 = ""
        self.header_texts = []
        self.logos = 0
        self.buttons = 0
        self.inputs = 0
        self.selects = 0
        self.toggles = 0
        self.sections = 0
        self.cards = 0
        self.tabs = 0
        self._stack = []
        self._cap = None  # 'title' or 'h1' or 'header'
        self._in_header_depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").lower()
        if tag == "title":
            self._cap = "title"
        elif tag == "h1":
            self._cap = "h1"
        elif tag in ("header",) or "header" in cls or "topbar" in cls or "masthead" in cls:
            self._in_header_depth += 1
        elif tag == "img" and self._in_header_depth > 0:
            self.logos += 1
        elif tag == "svg" and self._in_header_depth > 0:
            self.logos += 1
        if tag == "button" or a.get("role") == "button":
            self.buttons += 1
        if tag == "input":
            self.inputs += 1
            if a.get("type", "").lower() in ("checkbox", "radio"):
                self.toggles += 1
        if tag == "select":
            self.selects += 1
        if "toggle" in cls or "switch" in cls:
            self.toggles += 1
        if tag == "section" or "section" in cls:
            self.sections += 1
        if "card" in cls:
            self.cards += 1
        if "tab" in cls and "table" not in cls:
            self.tabs += 1

    def handle_endtag(self, tag):
        if tag in ("header",):
            self._in_header_depth = max(0, self._in_header_depth - 1)
        if tag == "title" and self._cap == "title":
            self._cap = None
        if tag == "h1" and self._cap == "h1":
            self._cap = None

    def handle_data(self, data):
        txt = data.strip()
        if not txt:
            return
        if self._cap == "title":
            self.title = (self.title + " " + txt).strip()
        elif self._cap == "h1":
            self.h1 = (self.h1 + " " + txt).strip()
        if self._in_header_depth > 0 and len(txt) > 1:
            self.header_texts.append(txt)


def classify_color(value, reg):
    nv = norm_color(value)
    pal = {norm_color(k): v for k, v in reg["palette"].items()}
    if nv in pal:
        return "LOCKED", "VPN palette: %s" % pal[nv]
    return "EDITABLE", "non-brand color"


def classify_font(fam, reg):
    if fam in reg["fonts"]:
        return "LOCKED", "VPN font: %s" % reg["fonts"][fam]
    return "EDITABLE", "non-brand font"


def classify_var(name, value, reg):
    low = name.lower()
    for kw in reg["var_lock_keywords"]:
        if kw in low:
            return "LOCKED", "var name keyword '%s'" % kw
    # if value resolves to a brand color -> locked
    for m in HEX_RE.findall(value) + RGB_RE.findall(value):
        st, _ = classify_color(m, reg)
        if st == "LOCKED":
            return "LOCKED", "var resolves to brand color"
    return "EDITABLE", "free token"


def classify_header(text, reg):
    t = text.strip()
    for locked in reg["header_text"]:
        if locked.lower() in t.lower() or t.lower() in locked.lower():
            return "LOCKED", "VEGN/VIS locked header string"
    return "EDITABLE", "free header text"


def spec(key, value, status, reason):
    return {"key": key, "value": value, "status": status, "reason": reason}


def scan_file(path, reg):
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    p = _Tag()
    try:
        p.feed(raw)
    except Exception:
        pass

    comments = " ".join(COMMENT_RE.findall(raw)).lower()
    has_lock_comment = any(m in comments for m in reg["marker_comments"])
    has_lock_attr = any(attr in raw.lower() for attr in reg["marker_attrs"])

    cats = {"HEADER": [], "LAYOUT": [], "COLOR": [], "TYPOGRAPHY": [],
            "DIMENSION": [], "INTERACTIVE": [], "MARKER": []}

    # ---- HEADER ----
    if p.title:
        st, rs = classify_header(p.title, reg)
        cats["HEADER"].append(spec("title", p.title, st, rs))
    if p.h1:
        st, rs = classify_header(p.h1, reg)
        cats["HEADER"].append(spec("h1", p.h1, st, rs))
    seen_h = set()
    for ht in p.header_texts[:12]:
        if ht in seen_h:
            continue
        seen_h.add(ht)
        st, rs = classify_header(ht, reg)
        cats["HEADER"].append(spec("header_text", ht, st, rs))
    cats["HEADER"].append(spec("logo_count", str(p.logos),
                               "EDITABLE", "swap allowed, keep aspect"))

    # ---- COLOR ----
    colors = {}
    for c in HEX_RE.findall(raw) + RGB_RE.findall(raw):
        nc = norm_color(c)
        colors[nc] = colors.get(nc, 0) + 1
    for c, cnt in sorted(colors.items(), key=lambda kv: -kv[1])[:40]:
        st, rs = classify_color(c, reg)
        cats["COLOR"].append(spec(c, "x%d uses" % cnt, st, rs))

    # ---- CSS VARS (mixed: color/typography/dimension parents) ----
    for name, val in VAR_RE.findall(raw):
        val = val.strip()
        st, rs = classify_var(name, val, reg)
        cats["COLOR"].append(spec(name, val, st, rs + " [css var]"))

    # ---- TYPOGRAPHY ----
    fams = {}
    for decl in FONTFAM_RE.findall(raw):
        fams[first_font(decl)] = decl.strip()
    for fam, decl in fams.items():
        st, rs = classify_font(fam, reg)
        cats["TYPOGRAPHY"].append(spec("font-family", decl, st, rs))
    for sz in sorted(set(s.strip() for s in FONTSIZE_RE.findall(raw)))[:20]:
        cats["TYPOGRAPHY"].append(spec("font-size", sz, "EDITABLE", "scale tunable"))
    for w in sorted(set(s.strip() for s in FONTWEIGHT_RE.findall(raw)))[:12]:
        cats["TYPOGRAPHY"].append(spec("font-weight", w, "EDITABLE", "weight tunable"))

    # ---- LAYOUT ----
    disp = sorted(set(s.strip() for s in DISPLAY_RE.findall(raw)))
    if disp:
        cats["LAYOUT"].append(spec("display", ", ".join(disp[:8]), "EDITABLE", "layout mode"))
    for g in sorted(set(s.strip() for s in GRIDCOL_RE.findall(raw)))[:8]:
        cats["LAYOUT"].append(spec("grid-template-columns", g, "EDITABLE", "grid structure"))
    for mw in sorted(set(s.strip() for s in MAXW_RE.findall(raw)))[:8]:
        cats["LAYOUT"].append(spec("max-width", mw, "EDITABLE", "container width"))
    for gp in sorted(set(s.strip() for s in GAP_RE.findall(raw)))[:8]:
        cats["LAYOUT"].append(spec("gap", gp, "EDITABLE", "spacing"))
    cats["LAYOUT"].append(spec("sections", str(p.sections), "EDITABLE", "count"))
    cats["LAYOUT"].append(spec("cards", str(p.cards), "EDITABLE", "count"))
    cats["LAYOUT"].append(spec("tabs", str(p.tabs), "EDITABLE", "count"))

    # ---- DIMENSION ----
    for r in sorted(set(s.strip() for s in RADIUS_RE.findall(raw)))[:12]:
        cats["DIMENSION"].append(spec("border-radius", r, "EDITABLE", "corner"))
    for pd in sorted(set(s.strip() for s in PAD_RE.findall(raw)))[:12]:
        cats["DIMENSION"].append(spec("padding", pd, "EDITABLE", "inner spacing"))
    for mg in sorted(set(s.strip() for s in MARGIN_RE.findall(raw)))[:12]:
        cats["DIMENSION"].append(spec("margin", mg, "EDITABLE", "outer spacing"))

    # ---- INTERACTIVE ----
    cats["INTERACTIVE"].append(spec("buttons", str(p.buttons), "EDITABLE", "controls"))
    cats["INTERACTIVE"].append(spec("inputs", str(p.inputs), "EDITABLE", "controls"))
    cats["INTERACTIVE"].append(spec("selects", str(p.selects), "EDITABLE", "controls"))
    cats["INTERACTIVE"].append(spec("toggles", str(p.toggles), "EDITABLE", "controls"))

    # ---- MARKER (explicit author intent) ----
    if has_lock_comment:
        cats["MARKER"].append(spec("lock-comment", "present", "LOCKED",
                                   "author marked @lock/immutable"))
    if has_lock_attr:
        cats["MARKER"].append(spec("lock-attr", "present", "LOCKED",
                                   "data-lock attribute present"))
    if not cats["MARKER"]:
        cats["MARKER"].append(spec("explicit-markers", "none", "EDITABLE",
                                   "no author lock markers"))

    locked = sum(1 for c in cats.values() for s in c if s["status"] == "LOCKED")
    editable = sum(1 for c in cats.values() for s in c if s["status"] == "EDITABLE")

    return {
        "file": Path(path).name,
        "path": str(path),
        "size_bytes": Path(path).stat().st_size,
        "sha256": hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()[:16],
        "summary": {"locked": locked, "editable": editable, "total": locked + editable},
        "categories": cats,
    }


def scan_folder(folder, reg):
    files = sorted(Path(folder).rglob("*.html"))
    out = []
    for f in files:
        if f.name.lower() in ("vhs_controlcenter.html",):
            continue  # never scan the viewer itself
        try:
            out.append(scan_file(f, reg))
        except Exception as e:
            out.append({"file": f.name, "path": str(f), "error": str(e)})
    return out


def merge_registry(base, override):
    if not override:
        return base
    out = json.loads(json.dumps(base))
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)  # add-only merge
        elif isinstance(v, list) and isinstance(out.get(k), list):
            out[k] = sorted(set(out[k]) | set(v))
        else:
            out[k] = v
    return out


def main():
    ap = argparse.ArgumentParser(description="VHS HTML Spec Reader (M01)")
    ap.add_argument("--scan", required=True, help="folder containing HTML U/I files")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--registry", default="", help="optional lock-registry JSON (add-only)")
    args = ap.parse_args()

    reg = DEFAULT_LOCK_REGISTRY
    if args.registry and Path(args.registry).exists():
        try:
            ov = json.loads(Path(args.registry).read_text(encoding="utf-8"))
            reg = merge_registry(reg, ov)
        except Exception as e:
            print("[WARN] registry load failed: %s" % e)

    files = scan_folder(args.scan, reg)
    payload = {
        "meta": {
            "tool": "VHS Reader",
            "version": VHS_VERSION,
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scan_path": str(Path(args.scan).resolve()),
            "file_count": len(files),
        },
        "lock_registry": reg,
        "files": files,
    }
    Path(args.out).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tl = sum(f.get("summary", {}).get("locked", 0) for f in files)
    te = sum(f.get("summary", {}).get("editable", 0) for f in files)
    print("[VHS] scanned %d file(s)  LOCKED=%d  EDITABLE=%d  -> %s"
          % (len(files), tl, te, args.out))


if __name__ == "__main__":
    main()
