#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL241_TemplateAdapter v0101 — 薄尾:模板同步器(任何模板 convert → sync 成 VIA 自己的活 U/I · watch 自動跟 · TOP 25)

操作員 2026-09-30 R35:「HTML U/I RAW TEMPLATE WITH SYNCHRONIZER(強大到多種功能接有自動隨模板範例調整)AUTO SYNC WITH TEMPLATE
… 模板可轉換 SYNCHRONIZER 自動隨之調整變成自己的 U/I 可加 TOP 25 TO BUILD UP THIS FUNCTION」。
為什麼接在 CGC_MDL241 家族:v0100 已是「任何設計規格 → VIA_UI_TemplateSSOT 下一版候選」的正主(token 同義字冊 · LAYOUT 自動優化 ·
圖規格 · 呈現套件 · SYNCHRONIZER 預置登記),本版只補「模板本身」那一半,token 仍走 v0100 plan(同一把尺,L05):
  convert --in <.dc.html|.html|.css|.json> [--propose]
      ① 匯入:Claude Design .dc.html(<x-dc> · sc-for · sc-if · {{ 槽 }})、Standalone 綁包(__bundler/template JSON 解包,資源冊留著內嵌字型)、
         一般 .html、.css / token JSON;② 抽:CSS 變數 token → v0100 plan 出 TemplateSSOT 下一版候選(不寫 registry;--propose 才寫成
         apply 吃的那份 CANDIDATE;apply 後格式鎖要操作員 CGC_MDL238 template --lock 重鎖)· 版面區塊 · 元件盤點(結構簽章去重)· 槽位
         (純量 / 清單與欄位 / 條件 / 事件)→ VIA_Reports/template_adapter/converted/<slug>/TEMPLATE_IR.json · COMPONENTS.json
  sync [--in <檔>] [--mode auto|faithful|skeleton]
      槽 → VIA 既有報告(唯讀:全景 monitor · VCGC TEST · HANDOFF · SDD · DFLOCK · VDF/VRN 鏈 · 註冊同步 · 環境 · 功能帳 · 盤點冊 · 必用卡 ·
      輸入冊 · TemplateSSOT)。faithful = 模板原標記逐槽代入(模板 CSS 原樣帶進來,燈 / 色 / 類名自動對到模板自己的語彙);
      skeleton = 模板 CSS + 角色類名套 VIA 自己的版面(沒有槽的一般 .html 用這個)。沒對上的槽頁上標 NODATA,另列未對接報告,不造數。
      → VIA_Reports/template_adapter/synced/<slug>/VIA_UI_<slug>_latest.html(+ _skeleton)· BINDING_latest.json;總表 SYNC_INDEX_latest.html
  watch [--once] [--interval 秒] [--cycles N]   投放夾 VIA_Reports/template_adapter/inbox(操作員把匯出的「VIA HTML Universal UI.dc.html」
      丟進去):模板 sha 或資料來源 (大小, mtime) 一變才重出;inbox 空 = NODATA rc 2(不拿參考副本冒充)
  diff --a <模板|IR> --b <模板|IR> · lock --in <模板> [--apply] · top25 · sources · drop
TOP 25 能力的正本 = VIA_UI_TemplateSync_SSOT_v0100.json(同義字 / 來源 / 角色冊也在那裡);每項對一個自測檢號,自測會交叉核對。
其餘(plan / apply / spec / demo / consumers)照 v0100(thin tail;__getattr__ 轉接)。VIA_FROM_VCGC:只收 VCGC 呼叫。零網路。不用 TA-Lib。
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

import base64
import colorsys
import gzip
import hashlib
import html as _html
import importlib.util
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL241_TemplateAdapter"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "CGC_MDL241_TemplateAdapter_v0100.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("tpladapter_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


ENGINE = Path(__file__).stem
VERSION = "v" + ENGINE.rsplit("_v", 1)[-1]
VIA = PRIOR.VIA
OUT = PRIOR.OUT
BOOK_GLOB = "VIA_UI_TemplateSync_SSOT_v*.json"
LAMPS = ("GREEN", "YELLOW", "RED", "NODATA")
ORDER = {"RED": 0, "YELLOW": 1, "NODATA": 2, "GREEN": 3}
STAMP = VIA / "VIA_HTML_UI" / "assets" / "via-stamp-transparent-96.webp"
EXPR = re.compile(r"\{\{\s*([^{}]*?)\s*\}\}")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr", "param"}
_BOOK: dict | None = None


def book() -> dict:
    global _BOOK
    if _BOOK is None:
        p = PRIOR._newest(HERE, BOOK_GLOB)
        _BOOK = (PRIOR._json(p) if p else None) or {}
        _BOOK["_path"] = p.name if p else ""
    return _BOOK


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def _e(x) -> str:
    return _html.escape("" if x is None else str(x), quote=True)


def _rel(p) -> str:
    try:
        return str(Path(p).resolve().relative_to(VIA))
    except ValueError:
        return str(p)


def slug_of(name: str, sha: str = "") -> str:
    s = re.sub(r"(\.dc)?\.(html?|css|json|scss)$", "", Path(name).name, flags=re.I)
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:60]
    return s if len(s) >= 3 else ("tpl_" + (sha or _sha(name.encode()))[:8])


def lamp4(x) -> str:
    s = str(x if x is not None else "").strip().upper()
    head = re.split(r"[\s(:·|/]", s)[0] if s else ""
    for lamp, names in (book().get("lamp_alias") or {}).items():
        if head in names:
            return lamp
    return "NODATA"


def worst(lamps) -> str:
    ls = [lamp4(x) for x in lamps]
    return min(ls, key=lambda x: ORDER[x]) if ls else "NODATA"


class Html(str):
    """Trusted markup made here (pills · svg); every other value is escaped on the way out."""


class TabRef(str):
    """A tab target id carried in a row's event field; rendered as data-via-tab."""


# ---------------------------------------------------------------- T01 ingest (any template → markup + css + resources)

BUNDLE_RX = re.compile(r'<script type="__bundler/(manifest|template|ext_resources)">(.*?)</script>', re.S)


def ingest(path: Path) -> dict:
    path = Path(path)
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig", errors="replace")
    info = {"path": str(path), "name": path.name, "sha": _sha(raw), "bytes": len(raw), "kind": "html", "resources": {}}
    low = path.name.lower()
    if low.endswith((".css", ".json", ".scss")):
        info.update(kind="tokens", text=text)
        return info
    parts = dict(BUNDLE_RX.findall(text))
    if "template" in parts:
        try:
            tpl = json.loads(parts["template"])
        except ValueError:
            tpl = None
        if isinstance(tpl, str):
            try:
                man = json.loads(parts.get("manifest") or "{}")
            except ValueError:
                man = {}
            info["resources"] = {k: v for k, v in man.items() if isinstance(v, dict) and "data" in v}
            info["kind"] = "dc_bundle"
            text = tpl
    if info["kind"] == "html" and re.search(r"<x-dc\b", text):
        info["kind"] = "dc"
    info["text"] = text
    return info


def res_bytes(res: dict) -> bytes:
    raw = base64.b64decode(res.get("data") or "")
    return gzip.decompress(raw) if res.get("compressed") else raw


def split_doc(text: str) -> dict:
    m = re.search(r"<x-dc\b[^>]*>(.*?)</x-dc>", text, re.S | re.I)
    if m:
        inner = m.group(1)
        hm = re.search(r"<helmet>(.*?)</helmet>", inner, re.S | re.I)
        pre = text[:m.start()] + (hm.group(1) if hm else "")
        markup = inner[hm.end():] if hm else inner
    else:
        bm = re.search(r"<body\b[^>]*>(.*)</body>", text, re.S | re.I)
        pre = text[:bm.start()] if bm else ""
        markup = bm.group(1) if bm else text
    title = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
    css = re.findall(r"<style[^>]*>(.*?)</style>", pre, re.S | re.I)
    links = re.findall(r"<link\b[^>]*>", pre, re.I)
    head_scripts = len(re.findall(r"<script\b", pre, re.I))
    body_scripts = len(re.findall(r"<script\b", markup, re.I))
    markup = re.sub(r"<script\b[^>]*>.*?</script>", "", markup, flags=re.S | re.I)
    body_css = re.findall(r"<style[^>]*>(.*?)</style>", markup, re.S | re.I)
    return {"css": css, "body_css": body_css, "links": links, "markup": markup, "scripts_dropped": head_scripts + body_scripts,
            "title": _html.unescape(title.group(1).strip()) if title else ""}


# ---------------------------------------------------------------- DOM (stdlib html.parser; the dc language is sc-for / sc-if / {{ }})

class Node:
    __slots__ = ("tag", "attrs", "kids", "text", "parent")

    def __init__(self, tag, attrs=None, text=None, parent=None):
        self.tag, self.attrs, self.kids, self.text, self.parent = tag, attrs or [], [], text, parent

    def get(self, k, default=""):
        for a, v in self.attrs:
            if a == k:
                return v
        return default


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, [(k, v if v is not None else "") for k, v in attrs], parent=self.cur)
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(Node(tag, [(k, v if v is not None else "") for k, v in attrs], parent=self.cur))

    def handle_endtag(self, tag):
        c = self.cur
        while c is not None and c.tag != tag:
            c = c.parent
        if c is not None and c.parent is not None:
            self.cur = c.parent

    def handle_data(self, data):
        self.cur.kids.append(Node("#text", text=data, parent=self.cur))


def parse(markup: str) -> Node:
    b = _Builder()
    b.feed(markup)
    b.close()
    return b.root


def _single(s):
    m = re.fullmatch(r"\s*\{\{\s*([^{}]*?)\s*\}\}\s*", s or "")
    return m.group(1) if m else None


def _literal(expr: str):
    e = expr.strip()
    if e in ("true", "false", "null", "undefined"):
        return True, {"true": True, "false": False}.get(e)
    if re.fullmatch(r"-?\d+(\.\d+)?", e):
        return True, float(e) if "." in e else int(e)
    if len(e) >= 2 and e[0] == e[-1] and e[0] in "'\"":
        return True, e[1:-1]
    return False, None


def _classes(n: Node) -> list:
    return [c for c in re.split(r"\s+", EXPR.sub(" ", n.get("class"))) if c]


def _tokens(s: str) -> list:
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(s))
    return [t for t in re.split(r"[\s_\-.]+", s.lower()) if t]


def _norm(s) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def roles_of(n: Node, roles: dict) -> list:
    cls = _classes(n)
    out = []
    for role, spec in roles.items():
        if n.tag in (spec.get("tags") or []) or any(c == s or c.endswith("-" + s) for c in cls for s in (spec.get("classes") or [])):
            out.append(role)
    return out


def _role_class(n: Node, spec: dict) -> str:
    for c in _classes(n):
        if any(c == s or c.endswith("-" + s) for s in (spec.get("classes") or [])):
            return c
    return ""


def _text_of(n: Node, limit: int = 60) -> str:
    buf = []

    def walk(x, depth):
        if x.tag == "#text":
            buf.append(x.text)
        elif depth < 2 or not buf:
            for k in x.kids:
                if x.tag in ("style", "script"):
                    return
                walk(k, depth + 1)
    walk(n, 0)
    return re.sub(r"\s+", " ", EXPR.sub("", "".join(buf))).strip()[:limit]


# ---------------------------------------------------------------- T03 regions · T04 components · T05 slots · pages

def find_pages(root: Node, bk: dict) -> list:
    """Sibling sc-if blocks with a plain top-level predicate (≥ 2 under one parent, not inside a loop) = pages → tabs."""
    markers = set(bk.get("page_category_markers") or [])
    roles = bk.get("roles") or {}
    pages = []

    def in_loop(n):
        p = n.parent
        while p is not None:
            if p.tag == "sc-for":
                return True
            p = p.parent
        return False

    def heading(n):
        stack = list(n.kids)
        while stack:
            x = stack.pop(0)
            if x.tag == "#text":
                continue
            if "heading" in roles_of(x, roles):
                t = re.sub(r"\s+", " ", EXPR.sub("", "".join(k.text or "" for k in x.kids if k.tag == "#text"))).strip()[:40] or _text_of(x, 40)
                if t:
                    return t
            stack[0:0] = x.kids
        return ""

    def walk(n):
        cands = [k for k in n.kids if k.tag == "sc-if" and re.fullmatch(r"[A-Za-z_$][\w$]*", _single(k.get("value")) or "")]
        if len(cands) >= 2 and not in_loop(n):
            for k in cands:
                pred = _single(k.get("value"))
                pages.append({"id": re.sub(r"[^A-Za-z0-9_-]", "", pred), "pred": pred, "node": k, "parent": n,
                              "label": heading(k) or re.sub(r"^(is|show|tab)", "", pred) or pred,
                              "category": bool(set(_tokens(pred)) & markers)})
        for k in n.kids:
            if k.tag != "#text":
                walk(k)
    walk(root)
    return pages


def analyse(root: Node, css_all: str, bk: dict) -> dict:
    roles = bk.get("roles") or {}
    pages = find_pages(root, bk)
    page_of = {id(p["node"]): p["id"] for p in pages}
    ir = {"scalars": {}, "lists": {}, "conds": {}, "events": {}, "regions": {}, "components": {}, "signatures": {},
          "pages": [{k: p[k] for k in ("id", "pred", "label", "category")} for p in pages], "x_import": 0}

    def rec(expr, scope, ctx, page):
        if _literal(expr)[0]:
            return
        parts = expr.split(".")
        if parts[0] in scope:
            L = ir["lists"][scope[parts[0]]]
            f = L["fields"].setdefault(".".join(parts[1:]) or "$self", {"ctx": set(), "n": 0})
            f["ctx"].add(ctx)
            f["n"] += 1
            return
        tgt = ir["events"] if ctx == "event" else ir["conds"] if ctx == "cond" else ir["scalars"]
        s = tgt.setdefault(expr, {"ctx": set(), "n": 0, "pages": set()})
        s["ctx"].add(ctx)
        s["n"] += 1
        s["pages"].add(page or "")

    def list_kind(n):
        p, hops = n.parent, 0
        while p is not None and hops < 3:
            if p.tag in ("table", "tbody", "sc-raw-table", "sc-raw-tbody") or "grid-template-columns" in p.get("style") or "table" in roles_of(p, roles):
                return "table"
            p, hops = p.parent, hops + 1
        first = next((k for k in n.kids if k.tag != "#text"), None)
        if first is not None:
            r = roles_of(first, roles)
            for want, kind in (("tab", "tabs"), ("card", "cards"), ("lamp", "lamps"), ("chart", "chart"), ("button", "buttons")):
                if want in r:
                    return kind
        return "list"

    def walk(n, scope, page, depth):
        if n.tag == "#text":
            if n.parent is None or n.parent.tag not in ("style", "script"):
                for e in EXPR.findall(n.text or ""):
                    rec(e, scope, "text", page)
            return
        if n.tag == "sc-for":
            expr = _single(n.get("list"))
            var = n.get("as") or "item"
            new = dict(scope)
            if expr and not _literal(expr)[0]:
                parts = expr.split(".")
                if parts[0] in scope:
                    parent = scope[parts[0]]
                    lp = parent + "." + ".".join(parts[1:])
                    f = ir["lists"][parent]["fields"].setdefault(".".join(parts[1:]), {"ctx": set(), "n": 0})
                    f["ctx"].add("list")
                    f["n"] += 1
                else:
                    parent, lp = None, expr
                L = ir["lists"].setdefault(lp, {"as": var, "fields": {}, "hint": int(n.get("hint-placeholder-count") or 0),
                                                "parent": parent, "pages": set(), "kind": list_kind(n)})
                L["pages"].add(page or "")
                new[var] = lp
            for k in n.kids:
                walk(k, new, page, depth + 1)
            return
        if n.tag == "sc-if":
            expr = _single(n.get("value"))
            if expr:
                rec(expr, scope, "cond", page)
            for k in n.kids:
                walk(k, scope, page_of.get(id(n), page), depth + 1)
            return
        if n.tag == "x-import":
            ir["x_import"] += 1
        for k, v in n.attrs:
            if k.startswith("hint-"):
                continue
            if k == "ref":
                continue
            ctx = "event" if k.startswith("sc-camel-on-") or re.fullmatch(r"on[a-z]+", k) else "class" if k == "class" else "style" if k == "style" else "attr"
            for e in EXPR.findall(v or ""):
                rec(e, scope, ctx, page)
        rs = roles_of(n, roles) if n.tag != "#root" else []
        for r in rs:
            c = ir["components"].setdefault(r, {"n": 0, "classes": Counter()})
            c["n"] += 1
            rc = _role_class(n, roles[r])
            if rc:
                c["classes"][rc] += 1
            if r in ("header", "left", "tabs", "pane", "footer") and r not in ir["regions"]:
                ir["regions"][r] = {"tag": n.tag, "class": rc, "depth": depth}
        if rs:
            sig = n.tag + "." + ".".join(sorted(_classes(n))) + "[" + ",".join(k.tag for k in n.kids if k.tag != "#text")[:120] + "]"
            s = ir["signatures"].setdefault(sig, {"role": rs[0], "n": 0})
            s["n"] += 1
        for k in n.kids:
            walk(k, scope, page, depth + 1)

    walk(root, {}, "", 0)
    ir["css"] = css_facts(css_all, bk)
    return ir


def css_facts(css: str, bk: dict) -> dict:
    """Tokens (CSS custom properties, light blocks only) · class vocabulary · modifier colours · 100vh containers · breakpoints."""
    raw, vocab, mods, vh = {}, Counter(), {}, set()
    for sel, block in re.findall(r"([^{}]*)\{([^{}]*)\}", css):
        if "@font-face" in sel:
            continue
        dark = re.search(r"dark", sel, re.I) is not None
        for k, v in PRIOR.CSS_VAR_RX.findall(block):
            if not dark and k.strip() not in raw:
                raw[k.strip()] = v.strip()
        cl = re.findall(r"\.([A-Za-z_][\w-]*)", sel)
        vocab.update(cl)
        if "100vh" in block and cl:
            vh.add(cl[-1])
        for a, b in re.findall(r"\.([A-Za-z_][\w-]*)\.([A-Za-z_][\w-]*)", sel):
            m = re.search(r"(?:color|background)[\w-]*\s*:\s*(var\(--[\w-]+\)|#[0-9a-fA-F]{3,8})", block)
            if m:
                mods.setdefault(b, m.group(1))
    res = PRIOR.resolve_aliases(raw)
    hexes = {k: PRIOR.parse_color(v) for k, v in res.items()}
    hexes = {k: v for k, v in hexes.items() if v}
    mod_hex = {}
    for b, v in mods.items():
        m = re.fullmatch(r"var\(--([\w-]+)\)", v)
        c = hexes.get(m.group(1)) if m else PRIOR.parse_color(v)
        if c:
            mod_hex[b] = c
    bps = Counter(int(x) for x in re.findall(r"max-width\s*:\s*(\d+)px", css))
    return {"vars": raw, "hex": hexes, "vocab": sorted(vocab), "mod_hex": mod_hex, "vh": sorted(vh),
            "breakpoint": bps.most_common(1)[0][0] if bps else None}


# ---------------------------------------------------------------- T08 lamp mapping (template's own vocabulary and palette)

def _hls(c: str):
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hls(r, g, b)


def _hue_dist(a: str, b: str) -> float:
    ha, la, sa = _hls(a)
    hb, lb, sb = _hls(b)
    dh = abs(ha - hb)
    return min(dh, 1 - dh) * 3 + abs(la - lb) + abs(sa - sb) * 0.5


def theme_of(facts: dict, bk: dict) -> dict:
    hexes, vocab = facts.get("hex") or {}, set(facts.get("vocab") or [])
    canon = bk.get("lamp_canon") or {}
    vocab_book = bk.get("lamp_class_vocab") or {}
    lamp_hex = {}
    for lamp in LAMPS:
        named = next((hexes[v] for v in vocab_book.get(lamp, []) if v in hexes), None)
        if named:
            lamp_hex[lamp] = named
            continue
        if lamp == "NODATA":
            cands = [(abs(_hls(c)[1] - 0.45) + _hls(c)[2], c) for c in hexes.values() if _hls(c)[2] < 0.2 and 0.25 < _hls(c)[1] < 0.7]
        else:
            cands = [(_hue_dist(c, canon[lamp]), c) for c in hexes.values() if _hls(c)[2] > 0.25 and 0.2 < _hls(c)[1] < 0.72]
        best = min(cands) if cands else None
        lamp_hex[lamp] = best[1] if best and (lamp == "NODATA" or best[0] < 0.6) else canon.get(lamp, "#64748b")
    acc = {}
    for lamp in LAMPS:
        hits = [b for b, c in (facts.get("mod_hex") or {}).items() if c == lamp_hex[lamp] and b not in ("on", "over", "z")]
        acc[lamp] = hits[0] if hits else ""
    cls = {lamp: next((v for v in vocab_book.get(lamp, []) if v in vocab), "") for lamp in LAMPS}
    zebra = next((v for v in (bk.get("derived") or {}).get("zebra_vars", []) if v in (facts.get("vars") or {})), "")
    pill = next((v for v in ("pill", "badge", "chip", "tag") if v in vocab), "")
    return {"lamp_hex": lamp_hex, "acc": acc, "lamp_cls": cls, "zebra": zebra, "pill": pill}


def pill(lamp: str, text: str, theme: dict) -> Html:
    c = (theme.get("lamp_hex") or {}).get(lamp, "#64748b")
    cls = theme.get("pill") or "via-pill"
    return Html(f"<span class='{_e(cls)} via-lamp-{lamp}' style='background:{_e(c)};color:#fff'>{_e(text)}</span>")


def svg_tally(tally: dict, theme: dict, title: str = "") -> Html:
    rows = [(k, int(tally.get(k) or 0)) for k in LAMPS]
    mx = max([n for _, n in rows] + [1])
    h = 18 * len(rows) + 4
    bars = "".join(f"<text x='0' y='{18 * i + 13}' font-size='10' fill='currentColor'>{k}</text>"
                   f"<rect x='56' y='{18 * i + 3}' width='{round(150 * n / mx, 1)}' height='12' fill='{_e(theme['lamp_hex'][k])}'></rect>"
                   f"<text x='{60 + round(150 * n / mx)}' y='{18 * i + 13}' font-size='10' fill='currentColor'>{n}</text>"
                   for i, (k, n) in enumerate(rows))
    return Html(f"<svg class='via-svg' viewBox='0 0 240 {h}' width='100%' preserveAspectRatio='xMinYMin meet' role='img' "
                f"aria-label='{_e(title)} tally' style='max-width:320px;display:block'>{bars}</svg>")


# ---------------------------------------------------------------- T06 sources (read-only) · T13 freshness · T14 error boundary

def _glob_newest(root: Path, rel: str):
    if "*" not in rel:
        return root / rel
    hits = sorted((root / Path(rel).parent).glob(Path(rel).name), key=_vnum)
    return hits[-1] if hits else root / rel.replace("*", "0100")


def _pick(d: dict, spec: str):
    for k in str(spec or "").split("|"):
        if k and d.get(k) not in (None, ""):
            return d.get(k)
    return None


def load_sources(root: Path | None = None, bk: dict | None = None, now: float | None = None) -> list:
    root, bk, now = root or VIA, bk or book(), now or time.time()
    out = []
    for spec in bk.get("sources") or []:
        p = _glob_newest(root, spec["path"])
        s = {"id": spec["id"], "name": spec.get("name", spec["id"]), "en": spec.get("en", ""), "path": spec["path"], "file": _rel(p),
             "adapter": spec.get("adapter"), "status_src": bool(spec.get("status")), "state": "ABSENT", "lamp": "NODATA", "at": "",
             "age_h": None, "stale": False, "sha": "", "rows": [], "tally": {}, "engine": "", "note": "", "data": None}
        out.append(s)
        if not p.exists():
            s["note"] = "ABSENT:來源檔不在(照實 NODATA)"
            continue
        try:
            raw = p.read_bytes()
            text = raw.decode("utf-8-sig", errors="replace")
            data = [json.loads(x) for x in text.splitlines() if x.strip()] if p.suffix == ".jsonl" else json.loads(text)
        except (OSError, ValueError) as ex:
            s.update(state="UNREADABLE", note=f"UNREADABLE:{type(ex).__name__}")
            continue
        s.update(state="OK", sha=_sha(raw), data=data)
        s["age_h"] = round((now - p.stat().st_mtime) / 3600, 1)
        s["stale"] = s["age_h"] > float(spec.get("stale_h") or bk.get("stale_h_default") or 24)
        try:
            _adapt(s, spec, data)
        except Exception as ex:  # error boundary: a malformed report never takes the page down
            s.update(state="UNREADABLE", lamp="NODATA", rows=[], note=f"UNREADABLE:{type(ex).__name__}: {ex}"[:160])
        if not s["tally"] and s["rows"]:
            s["tally"] = dict(Counter(r["status"] for r in s["rows"]))
    return out


def _adapt(s: dict, spec: dict, data):
    rm = spec.get("row_map") or {}
    ad = spec.get("adapter")
    if ad in ("rows", "chain", "handoff"):
        s["lamp"] = lamp4(data.get(spec.get("lamp_key", "lamp")))
        s["at"] = str(data.get("at") or data.get("ts") or data.get("generated") or "")
        s["engine"] = str(data.get(spec.get("engine_key", "engine")) or "")
        rows = data.get(spec.get("rows_key", "rows")) or []
        for i, r in enumerate(rows if isinstance(rows, list) else []):
            if not isinstance(r, dict):
                continue
            st = lamp4(_pick(r, rm.get("status", "status")))
            note = _pick(r, rm.get("note", "note"))
            if isinstance(note, list):
                note = " · ".join(map(str, note))
            secs = _pick(r, rm.get("secs", "secs"))
            s["rows"].append({"code": str(_pick(r, rm.get("code", "id")) or f"{s['id']}-{i + 1:02d}"), "name": str(_pick(r, rm.get("name", "name")) or ""),
                              "status": st, "note": str(note or ""), "ts": str(_pick(r, rm.get("ts", "at")) or ""),
                              "ms": round(float(secs) * 1000) if isinstance(secs, (int, float)) else None,
                              "engine": str(_pick(r, rm.get("engine", "")) or s["engine"]), "on": st == "GREEN"})
        if ad == "chain" and isinstance(data.get("tally"), dict):
            t = Counter()
            for k, v in data["tally"].items():
                t[lamp4(k)] += int(v or 0)
            s["tally"] = dict(t)
        if ad == "handoff":
            s["note"] = f"closeout {data.get('closeout_lamp', '')} · pending {len(rows)}"
            s["tally"] = dict(Counter(r["status"] for r in s["rows"])) if s["rows"] else {s["lamp"]: 1}
    elif ad == "jsonl_tail":
        tail = data[-int(spec.get("tail") or 40):]
        s["lamp"] = "GREEN" if data else "NODATA"
        s["at"] = str((data[-1] or {}).get("ts", "")) if data else ""
        for r in reversed(tail):
            s["rows"].append({"code": str(r.get("id", "")), "name": f"{r.get('event', '')} {r.get('id', '')} {r.get('version', '')}".strip(),
                              "ts": str(r.get("ts", ""))[:19].replace("T", " "), "note": str(r.get("file", "")), "status": "NODATA",
                              "engine": str(r.get("by", "")), "on": False})
    elif ad == "inventory":
        s["lamp"] = "GREEN" if data.get("stations") else "NODATA"
        s["at"] = str(data.get("ts", ""))
        for st in data.get("stations") or []:
            s["rows"].append({"code": st.get("id", ""), "name": st.get("name", ""), "role": " ".join(map(str, st.get("argv") or [])),
                              "status": "NODATA", "note": "quick" if st.get("quick") else "full", "on": False})
    elif ad == "card":
        s["lamp"] = "GREEN" if data.get("must_use") else "NODATA"
        s["at"] = str(data.get("updated_at", ""))
        for st in data.get("must_use") or []:
            s["rows"].append({"code": str(st.get("step", "")), "name": st.get("id", ""), "label": st.get("id", ""), "note": st.get("what", ""),
                              "status": "GREEN", "on": False})
    elif ad == "input":
        s["lamp"] = "GREEN" if data.get("user") is not None else "NODATA"
        s["at"] = str(data.get("ts", ""))

        def flat(prefix, v):
            if isinstance(v, dict) and v:
                for k, x in v.items():
                    flat(f"{prefix}.{k}" if prefix else k, x)
            else:
                txt = json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else str(v)
                filled = v not in ("", None, [], {})
                s["rows"].append({"key": prefix, "name": prefix, "value": txt, "status": "GREEN" if filled else "NODATA", "on": filled,
                                  "src": Path(s["file"]).name, "by": "CGC_MDL139", "code": prefix})
        flat("", data.get("user") or {})
    elif ad == "tssot":
        s["lamp"] = "GREEN" if data.get("palette") else "NODATA"
        s["at"] = str(data.get("version", ""))
        s["data"] = data


def build_views(srcs: list, ir: dict | None, theme: dict, bk: dict, out_dir: Path, extra: dict | None = None) -> dict:
    by = {s["id"]: s for s in srcs}
    st_srcs = [s for s in srcs if s["status_src"]]
    lamp_all = worst([s["lamp"] for s in st_srcs])
    stale = [s for s in st_srcs if s["stale"]]
    nod = [s for s in st_srcs if s["state"] != "OK"]
    V = {"status_line": f"{lamp_all} · 來源 {len(st_srcs)} · STALE {len(stale)} · NODATA {len(nod)} · {_utc()}"}
    tier = lambda s: "NODATA" if s["state"] != "OK" else "STALE" if s["stale"] else "MEASURED"
    age = lambda s: "—" if s["age_h"] is None else f"{s['age_h']}h"
    tally_txt = lambda s: " · ".join(f"{k[0]}{s['tally'].get(k, 0)}" for k in LAMPS if s["tally"].get(k)) or "—"
    V["sources"] = [{"code": s["id"].upper(), "name": s["name"], "en": s["en"], "status": s["lamp"], "tier": tier(s), "on": s["lamp"] == "GREEN",
                     "note": s["note"] or s["file"], "age": age(s),
                     "lines": [{"k": "時間 at", "v": s["at"] or "—"}, {"k": "距今 age", "v": age(s)}, {"k": "sha", "v": s["sha"] or "—"},
                               {"k": "筆數 rows", "v": str(len(s["rows"]))}]} for s in srcs]
    V["kpis"] = [{"code": s["id"].upper(), "label": s["name"], "name": s["name"], "value": s["lamp"] + (" · STALE" if s["stale"] else ""),
                  "note": f"{tally_txt(s)} · {age(s)}" if s["state"] == "OK" else s["note"], "status": s["lamp"], "on": s["lamp"] == "GREEN"}
                 for s in st_srcs]
    V["summary"] = [{"code": s["id"].upper(), "name": s["name"], "tally": tally_txt(s), "status": s["lamp"], "age": age(s), "engine": s["engine"] or "—",
                     "score": (f"{round(100 * s['tally'].get('GREEN', 0) / max(1, sum(s['tally'].values())))}%" if s["tally"] else "—"),
                     "on": s["lamp"] == "GREEN"} for s in st_srcs]
    cats = []
    for s in st_srcs:
        if not s["rows"] and s["state"] != "OK":
            continue
        items = [{**r, "score": r.get("ms") if r.get("ms") is not None else "—"} for r in s["rows"][:60]]
        cats.append({"code": s["id"].upper(), "name": s["name"], "en": s["en"], "status": s["lamp"],
                     "kpis": [{"code": k, "label": k, "name": k, "value": s["tally"].get(k, 0), "status": k, "note": s["name"], "on": k == "GREEN"}
                              for k in LAMPS],
                     "items": items, "cols": [{"label": k, "name": k, "code": k} for k in LAMPS],
                     "rows": [{"name": r["name"] or r["code"], "code": r["code"], "status": r["status"],
                               "cells": [{"mark": "●" if r["status"] == k else "", "status": k if r["status"] == k else "", "code": k} for k in LAMPS]}
                              for r in items[:40]]})
    V["categories"] = cats
    V["tests"] = [dict(r) for r in (by.get("test") or {}).get("rows", [])]
    V["validation"] = [{**r, "value": r["status"]} for r in (by.get("sdd") or {}).get("rows", [])]
    V["pending"] = [dict(r) for r in (by.get("handoff") or {}).get("rows", [])]
    V["logs"] = [dict(r) for r in (by.get("ledger") or {}).get("rows", [])]
    tests = {r["code"]: r for r in V["tests"]}
    V["engines"] = [{**r, **({"status": tests[r["code"]]["status"], "ms": tests[r["code"]]["ms"], "on": tests[r["code"]]["status"] == "GREEN"}
                            if r["code"] in tests else {})} for r in (by.get("inventory") or {}).get("rows", [])]
    V["pipeline"] = [dict(r) for r in (by.get("card") or {}).get("rows", [])]
    V["params"] = [dict(r) for r in (by.get("input") or {}).get("rows", [])]
    V["charts"] = [{"code": s["id"].upper(), "title": s["name"], "name": s["name"], "chart": svg_tally(s["tally"], theme, s["name"]),
                    "spec": "lamp tally · " + ", ".join(f"{k}={s['tally'].get(k, 0)}" for k in LAMPS), "status": s["lamp"]}
                   for s in st_srcs if s["tally"]]
    ts = (by.get("tssot") or {}).get("data") or {}
    ch = ts.get("chart") or {}
    dash = ts.get("dashboard") or {}
    V["chart_spec"] = [{"name": k, "value": json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else str(v), "note": f"{ts.get('version', '')} {src}"}
                       for k, v, src in (("series", ch.get("series"), "chart"), ("axis_px", ch.get("axis_px"), "chart"),
                                         ("tick_intervals", dash.get("tick_intervals"), "dashboard"),
                                         ("chart_min_h_px", dash.get("chart_min_h_px"), "dashboard"),
                                         ("chart_max_h_px", dash.get("chart_max_h_px"), "dashboard")) if v is not None]
    V["palettes"] = [{"code": ts.get("version", ""), "label": f"TemplateSSOT {ts.get('version', '')}", "name": ts.get("version", ""), "on": True,
                      "swatch": [{"color": c} for c in list((ts.get("palette") or {}).values())[:8] if isinstance(c, str) and c.startswith("#")]}] if ts else []
    V["palette_label"] = f"TemplateSSOT {ts.get('version')}" if ts else None
    V["top25"] = [{"code": t["id"], "no": t["id"], "name": t["name"], "note": t["why"], "status": lamp4(t["status"]), "value": t["status"],
                   "on": t["status"] == "IMPLEMENTED"} for t in bk.get("top25") or []]
    V["drop_hint"] = f"投放夾 {(bk.get('drop') or {}).get('inbox', '')} · .dc.html / .html"
    links = []
    for ln in bk.get("links") or []:
        p = VIA / ln["path"]
        if p.exists():
            links.append({"code": ln["code"], "name": ln["name"], "href": os.path.relpath(p, out_dir), "status": "GREEN", "on": True})
    V["links"] = links
    V["bindings"] = []
    V["progress"] = None
    for k, v in (extra or {}).items():
        V[k] = v
    return V


# ---------------------------------------------------------------- T06 binding · T07 unmapped · T09 table fields

def _view_index(views: dict, bk: dict) -> dict:
    idx = {}
    for v, syns in (bk.get("views") or {}).items():
        for s in syns:
            idx.setdefault(_norm(s), v)
    for v in views:
        idx.setdefault(_norm(v), v)
    return idx


def match_view(name: str, views: dict, bk: dict):
    idx = _view_index(views, bk)
    ab = bk.get("abbrev") or {}
    cnt, lsx = set(bk.get("count_suffix") or []), set(bk.get("list_suffix") or [])

    def base(s):
        v = idx.get(_norm(s)) or idx.get(_norm(s) + "s") or ab.get(_norm(s))
        return v if v in views else None
    v = base(name)
    if v:
        return v, "synonym"
    toks = _tokens(name)
    if len(toks) >= 2 and toks[-1] in cnt:
        b = base("".join(toks[:-1]))
        if b and isinstance(views.get(b), list):
            return b + "#count", "count"
    if len(toks) >= 2 and toks[-1] in lsx:
        b = base("".join(toks[:-1]))
        if b:
            return b, "list-suffix"
    return None, "沒有對應的 VIA 來源(同義字 / 縮寫 / 計數尾碼都沒對上)"


def match_field(f: str, keys: set, bk: dict, ctx: set, view: str):
    der = bk.get("derived") or {}
    fl = f.lower()
    if f in keys:
        return f
    for canon, syns in (bk.get("field_syn") or {}).items():
        if fl in [x.lower() for x in syns] and canon in keys:
            return canon
    if ctx and ctx <= {"event"}:
        return "derived:pick" if view == "tabs" else "event"
    if f.endswith(der.get("class_style_suffix", "Cs")) or fl == "cs":
        return "derived:cs"
    for kind, names in (("on", der.get("on_fields")), ("tick", der.get("tick_fields")), ("arrow", der.get("arrow_fields")),
                        ("acc", der.get("accent_fields")), ("color", der.get("color_fields")), ("badge", der.get("badge_fields"))):
        if f in (names or []) and (kind in ("arrow", "on", "tick") or "status" in keys):
            return "derived:" + kind
    return None


def _presentational(ctx: set) -> bool:
    return bool(ctx) and ctx <= {"class", "style"}


def bind(ir: dict, views: dict, bk: dict) -> dict:
    pages = {p["id"]: p for p in ir.get("pages") or []}
    cat_pages = {pid for pid, p in pages.items() if p["category"]}
    cat_sample = (views.get("categories") or [{}])[0] if views.get("categories") else {}
    pfx = set(bk.get("page_scope_prefix") or [])
    res = {"scalars": {}, "lists": {}, "conds": {}, "unmapped": [], "presentational": [], "events": sorted(ir.get("events") or {})}

    def page_field(name):
        toks = _tokens(name)
        if len(toks) >= 2 and toks[0] in pfx:
            f = "".join(toks[1:])
            m = match_field(f, set(cat_sample), bk, set(), "categories")
            if m and not m.startswith("derived"):
                return m
        return None

    for name, s in sorted((ir.get("scalars") or {}).items()):
        in_cat = s["pages"] and s["pages"] <= cat_pages
        pf = page_field(name) if in_cat and cat_sample else None
        if pf:
            res["scalars"][name] = {"view": "page:" + pf, "how": "category-page"}
            continue
        v, how = match_view(name, views, bk)
        if v and views.get(v.split("#")[0]) is None and "#count" not in v:
            v, how = None, "來源在但沒值(NODATA)"
        res["scalars"][name] = {"view": v, "how": how}
        if not v:
            (res["presentational"] if _presentational(s["ctx"]) else res["unmapped"]).append(
                {"slot": name, "kind": "presentational" if _presentational(s["ctx"]) else "scalar", "why": how})
    for name, s in sorted((ir.get("conds") or {}).items()):
        if name in {p["pred"] for p in pages.values()}:
            res["conds"][name] = {"view": "page", "how": "page"}
            continue
        v, how = match_view(name, views, bk)
        res["conds"][name] = {"view": v, "how": how}
        if not v:
            res["unmapped"].append({"slot": name, "kind": "cond", "why": how})
    for lp in sorted(ir.get("lists") or {}, key=lambda x: x.count(".")):
        L = ir["lists"][lp]
        rows = None
        if L["parent"]:
            pb = res["lists"].get(L["parent"]) or {}
            f = lp.split(".", 1)[1]
            canon = (pb.get("fields") or {}).get(f)
            prow = next((r for r in (pb.get("sample") or []) if isinstance(r, dict) and isinstance(r.get(canon), list) and r.get(canon)), None)
            rows = prow.get(canon) if prow else ([] if canon else None)
            view = f"{pb.get('view')}.{canon}" if canon else None
            how = "nested" if canon else "上層清單沒有這個欄"
        else:
            pf = page_field(lp) if L["pages"] and L["pages"] <= cat_pages and cat_sample else None
            if pf:
                view, how = "page:" + pf, "category-page"
                rows = cat_sample.get(pf) or []
            else:
                view, how = match_view(lp, views, bk)
                rows = views.get(view) if view else None
                if view and not isinstance(rows, list):
                    view, how, rows = None, "對上的來源不是清單", None
        ent = {"view": view, "how": how, "fields": {}, "sample": rows or [], "rows": len(rows or []), "kind": L["kind"]}
        res["lists"][lp] = ent
        if not view:
            res["unmapped"].append({"slot": lp, "kind": "list", "why": how})
            for f, meta in sorted(L["fields"].items()):
                if not _presentational(meta["ctx"]) and not meta["ctx"] <= {"event"}:
                    res["unmapped"].append({"slot": f"{lp}[].{f}", "kind": "field", "why": "清單沒對上,欄位跟著 NODATA"})
            continue
        keys = set()
        for r in (rows or [])[:50]:
            if isinstance(r, dict):
                keys |= set(r)
        for f, meta in sorted(L["fields"].items()):
            if f == "$self":
                ent["fields"][f] = "$self"
                continue
            head = f.split(".")[0]
            m = match_field(head, keys, bk, meta["ctx"], (view or "").split(".")[0])
            if not keys and m and not m.startswith("derived") and m != "event":
                m = None
            ent["fields"][f] = m
            if m == "event":
                continue
            if not m:
                kind = "presentational" if _presentational(meta["ctx"]) else "field"
                (res["presentational"] if kind == "presentational" else res["unmapped"]).append(
                    {"slot": f"{lp}[].{f}", "kind": kind, "why": "清單有對上,但來源列沒有這個欄(也不是衍生欄)" if keys else "來源清單目前 0 列(NODATA)"})
    data_total = (len([1 for n, s in (ir.get("scalars") or {}).items() if not _presentational(s["ctx"])])
                  + len(ir.get("lists") or {}) + sum(1 for L in (ir.get("lists") or {}).values() for f, m in L["fields"].items()
                                                     if not _presentational(m["ctx"]) and not m["ctx"] <= {"event"})
                  + len([c for c in (ir.get("conds") or {}) if c not in {p["pred"] for p in pages.values()}]))
    un = len(res["unmapped"])
    res["coverage"] = {"bound": max(0, data_total - un), "total": data_total, "pct": round(100 * (data_total - un) / data_total, 1) if data_total else 100.0}
    return res


def binding_rows(b: dict) -> list:
    rows = []
    for k, v in b["scalars"].items():
        rows.append({"code": k, "name": v["view"] or "—", "note": v["how"], "status": "GREEN" if v["view"] else "NODATA", "value": "scalar"})
    for k, v in b["lists"].items():
        rows.append({"code": k + "[]", "name": v["view"] or "—", "note": f"{v['how']} · {v['rows']} 列 · {v['kind']}",
                     "status": "GREEN" if v["view"] else "NODATA", "value": "list"})
    for u in b["unmapped"]:
        if u["kind"] == "field":
            rows.append({"code": u["slot"], "name": "—", "note": u["why"], "status": "NODATA", "value": "field"})
    return rows


# ---------------------------------------------------------------- T20 offline sanitising (fonts · images · imports)

def _data_uri(mime: str, raw: bytes) -> str:
    return f"data:{mime};base64," + base64.b64encode(raw).decode()


class Offline:
    def __init__(self, resources: dict, bk: dict):
        self.res, self.bk = resources or {}, bk
        self.max_img = int((bk.get("budget") or {}).get("inline_image_max_bytes") or 300000)
        self.stats = Counter()
        self._stamp = None

    def stamp(self) -> str:
        if self._stamp is None:
            self._stamp = _data_uri("image/webp", STAMP.read_bytes()) if STAMP.exists() else ""
        return self._stamp

    def url(self, ref: str) -> str:
        ref = ref.strip().strip("'\"")
        if ref.startswith("data:"):
            return ref
        if ref in self.res:
            r = self.res[ref]
            raw = res_bytes(r)
            if r.get("mime", "").startswith("image/") and len(raw) > self.max_img:
                self.stats["images_replaced_by_via_stamp"] += 1
                return self.stamp()
            self.stats["resources_inlined"] += 1
            return _data_uri(r.get("mime") or "application/octet-stream", raw)
        if re.match(r"(?i)(https?:)?//", ref):
            self.stats["remote_urls_dropped"] += 1
            return ""
        return ref

    def css(self, css: str) -> str:
        n0 = len(re.findall(r"@import\b", css))
        css = re.sub(r"@import\b[^;]*;", "", css)
        self.stats["imports_dropped"] += n0

        def face(m):
            block = m.group(0)
            urls = re.findall(r"url\(\s*([^)]*?)\s*\)", block)
            latin = "U+0000-00FF" in block or "unicode-range" not in block
            if not urls or not latin or not all(u.strip("'\"") in self.res for u in urls):
                self.stats["fonts_dropped"] += 1
                return ""
            self.stats["fonts_inlined"] += 1
            return re.sub(r"url\(\s*([^)]*?)\s*\)", lambda u: f'url("{self.url(u.group(1))}")', block)
        css = re.sub(r"@font-face\s*\{[^}]*\}", face, css)
        css = re.sub(r"url\(\s*([^)]*?)\s*\)", lambda u: (lambda v: f'url("{v}")' if v else "none")(self.url(u.group(1))), css)
        return re.sub(r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/", "", css)


# ---------------------------------------------------------------- render: faithful (template markup, slots bound) · skeleton

class Renderer:
    def __init__(self, conv: dict, views: dict, binding: dict, theme: dict, off: Offline, bk: dict):
        self.ir, self.views, self.b, self.theme, self.off, self.bk = conv["ir"], views, binding, theme, off, bk
        self.pages = {id(p["node"]): p for p in conv["pages"]}
        self.page_parents = {id(p["parent"]) for p in conv["pages"]}
        self.tabs_bound = any(v["view"] == "tabs" for v in binding["lists"].values())
        self.stats = Counter()
        self.first_page = None
        self.page_ids = []

    # -- values
    def resolve(self, expr: str, scope: dict, ctx: str):
        lit = _literal(expr)
        if lit[0]:
            return True, lit[1]
        parts = expr.split(".")
        if parts[0] in scope:
            it = scope[parts[0]]
            return self.field(it, parts[1:], ctx)
        ent = (self.b["lists"].get(expr) if ctx == "list" else None) or self.b["scalars"].get(expr) or self.b["conds"].get(expr) \
            or self.b["lists"].get(expr)
        if not ent or not ent.get("view"):
            return False, None
        v = ent["view"]
        if v.startswith("page:"):
            pg = scope.get("$page")
            if pg is None:
                return False, None
            return True, pg.get(v[5:])
        if v.endswith("#count"):
            return True, len(self.views.get(v[:-6]) or [])
        val = self.views.get(v)
        return (val is not None), val

    def field(self, it: dict, rest: list, ctx: str):
        row, lp = it["row"], it["lp"]
        if not rest:
            return True, row
        fields = (self.b["lists"].get(lp) or {}).get("fields") or {}
        canon = fields.get(".".join(rest)) or fields.get(rest[0])
        if not canon or canon == "event":
            return False, None
        if canon == "$self":
            return True, row
        if canon.startswith("derived:"):
            return True, self.derived(canon[8:], rest[0], it, ctx)
        if not isinstance(row, dict):
            return False, None
        val = row.get(canon)
        for p in rest[1:]:
            val = val.get(p) if isinstance(val, dict) else None
        return (val is not None), val

    def derived(self, kind: str, fname: str, it: dict, ctx: str):
        row, i, n = it["row"], it["i"], it["n"]
        row = row if isinstance(row, dict) else {}
        lamp = lamp4(row.get("status")) if row.get("status") else "NODATA"
        th = self.theme
        if kind == "pick":
            return row.get("pick")
        if kind == "on":
            return bool(row.get("on"))
        if kind == "tick":
            return "✓" if row.get("on") else ""
        if kind == "arrow":
            return i < n - 1
        if kind == "acc":
            return th["acc"].get(lamp, "")
        if kind == "color":
            return th["lamp_hex"].get(lamp)
        if kind == "badge":
            return pill(lamp, str(row.get("value") if row.get("value") not in (None, "") and fname != "badge" else lamp), th) if row.get("status") else ""
        base = fname[:-2].lower() if fname.endswith("Cs") else ""
        der = self.bk.get("derived") or {}
        onish = set(der.get("on_fields") or []) | set(der.get("tick_fields") or [])
        if ctx == "style":
            if base == "row":
                return f"background:var(--{th['zebra']});" if th["zebra"] and i % 2 else ""
            if base in ("bar", "prog"):
                sc = row.get("score")
                try:
                    pct = float(str(sc).rstrip("%"))
                except (TypeError, ValueError):
                    return ""
                return f"width:{max(2, min(100, pct))}%;background:{th['lamp_hex'].get(lamp)};"
            if base in ("card",) or not row.get("status"):
                return ""
            return f"color:{th['lamp_hex'].get(lamp)};"
        if base in onish:
            return "on" if row.get("on") else ""
        if base == "row":
            return ""
        if base in ("card", "acc", "tone"):
            return th["acc"].get(lamp, "")
        return th["lamp_cls"].get(lamp, "") if row.get("status") else ""

    # -- markup
    def nodata(self, what: str) -> str:
        self.stats["nodata_marks"] += 1
        return f"<span class='via-nodata' title='未對接槽 unmapped: {_e(what)}'>NODATA</span>"

    def text(self, s: str, scope: dict) -> str:
        out, pos = [], 0
        for m in EXPR.finditer(s):
            out.append(_e(s[pos:m.start()]))
            ok, v = self.resolve(m.group(1), scope, "text")
            if not ok:
                out.append(self.nodata(m.group(1)))
            elif isinstance(v, Html):
                out.append(v)
            elif v is None or v is False or v is True or isinstance(v, (list, dict)):
                out.append("")
            else:
                out.append(_e(v))
            pos = m.end()
        out.append(_e(s[pos:]))
        return "".join(out)

    def attrs(self, n: Node, scope: dict, extra: list | None = None) -> str:
        out = []
        for k, v in n.attrs:
            if k.startswith("hint-") or k == "ref":
                continue
            if k.startswith("sc-camel-on-") or re.fullmatch(r"on[a-z]+", k):
                e = _single(v)
                ok, val = self.resolve(e, scope, "event") if e else (False, None)
                if ok and isinstance(val, TabRef):
                    out += [("data-via-tab", str(val)), ("tabindex", "0"), ("aria-controls", "via-page-" + str(val))]
                else:
                    self.stats["events_static"] += 1
                continue
            if k.startswith("sc-camel-"):
                k = re.sub(r"-([a-z])", lambda m: m.group(1).upper(), k[9:])
            ctx = "class" if k == "class" else "style" if k == "style" else "attr"
            if EXPR.search(v or ""):
                one = _single(v)
                if one is not None:
                    ok, val = self.resolve(one, scope, ctx)
                    if not ok or val is None or val is False:
                        self.stats["attrs_dropped"] += 0 if ok else 1
                        continue
                    v = "" if val is True else str(val)
                else:
                    def sub(m):
                        ok, val = self.resolve(m.group(1), scope, ctx)
                        return "" if not ok or val in (None, False, True) or isinstance(val, (list, dict)) else str(val)
                    v = EXPR.sub(sub, v)
            if k == "style":
                v = re.sub(r"url\(\s*([^)]*?)\s*\)", lambda u: (lambda x: f'url("{x}")' if x else "none")(self.off.url(u.group(1))), v)
            if k in ("src", "href", "poster") and v:
                v = self.off.url(v) if (v in self.off.res or re.match(r"(?i)(https?:)?//", v)) and k != "href" else v
                if not v:
                    continue
            if k == "class":
                v = " ".join(v.split())
            out.append((k, v))
        out += extra or []
        return "".join(f' {k}="{_e(v)}"' for k, v in out)

    def el(self, n: Node, scope: dict, extra: list | None = None) -> str:
        t = n.tag
        if t == "#text":
            if n.parent is not None and n.parent.tag in ("style", "script"):
                return self.off.css(n.text) if n.parent.tag == "style" else ""
            return self.text(n.text or "", scope)
        if t == "sc-for":
            return self.for_(n, scope)
        if t == "sc-if":
            return self.if_(n, scope)
        if t == "x-import":
            return self.nodata("x-import " + n.get("from"))
        if t in ("script", "link", "meta", "helmet"):
            return ""
        real = t[7:] if t.startswith("sc-raw-") else t
        a = self.attrs(n, scope, extra)
        gm = re.search(r"repeat\((\d+),", n.get("style"))
        if gm:                                                     # the designer fixed N columns for N sample items → follow the live count
            fix = self.grid_count(n, scope, int(gm.group(1)))
            if fix is not None:
                a = a.replace(f"repeat({gm.group(1)},", f"repeat({fix},", 1)
                self.stats["grid_adapted"] += 1
        if real in VOID:
            return f"<{real}{a}>"
        inner = "".join(self.el(k, scope) for k in n.kids)
        if id(n) in self.page_parents and not self.tabs_bound:
            inner = self.tabbar() + inner
        return f"<{real}{a}>{inner}</{real}>"

    def grid_count(self, n: Node, scope: dict, want: int):
        """A fixed repeat(N, …) grid whose repeated cells come from a list previewed with N placeholders → the list's live length."""
        stack = [(k, 0) for k in n.kids]
        while stack:
            x, d = stack.pop(0)
            if x.tag == "sc-for" and int(x.get("hint-placeholder-count") or -1) == want:
                expr = _single(x.get("list"))
                ok, seq = self.resolve(expr, scope, "list") if expr else (False, None)
                return len(seq) if ok and isinstance(seq, list) and seq and len(seq) != want else None
            if d < 3 and x.tag != "#text" and "grid-template-columns" not in x.get("style"):
                stack += [(k, d + 1) for k in x.kids]
        return None

    def for_(self, n: Node, scope: dict) -> str:
        expr = _single(n.get("list"))
        var = n.get("as") or "item"
        ok, seq = self.resolve(expr, scope, "list") if expr else (False, None)
        head = (expr or "").split(".")[0]
        lp = (scope[head]["lp"] + "." + expr.split(".", 1)[1]) if head in scope and "." in (expr or "") else (expr or "")
        if not ok or not isinstance(seq, list):
            self.stats["lists_nodata"] += 1
            return self.nodata(f"{expr}[]")
        out = []
        for i, row in enumerate(seq):
            sc = dict(scope)
            sc[var] = {"row": row, "i": i, "n": len(seq), "lp": lp}
            first = True
            for k in n.kids:
                if first and k.tag != "#text" and not k.tag.startswith("sc-"):
                    out.append(self.el(k, sc, [("data-via-row", lp)]))
                    first = False
                else:
                    out.append(self.el(k, sc))
        self.stats["rows_rendered"] += len(seq)
        return "".join(out)

    def page_list(self) -> list:
        out = []
        for p in sorted(self.pages.values(), key=lambda p: self.ir_page_order(p)):
            if p["category"] and self.views.get("categories"):
                for c in self.views["categories"]:
                    out.append((f"{p['id']}-{c['code']}", f"{c['name']}", p, c))
            else:
                out.append((p["id"], p["label"], p, None))
        return out

    def ir_page_order(self, p):
        return [x["id"] for x in self.ir["pages"]].index(p["id"]) if p["id"] in [x["id"] for x in self.ir["pages"]] else 0

    def tabbar(self) -> str:
        pl = self.page_list()
        btn = "".join(f"<button type='button' class='via-tab{' on' if i == 0 else ''}' data-via-tab='{_e(pid)}' aria-controls='via-page-{_e(pid)}' "
                      f"tabindex='{0 if i == 0 else -1}'>{_e(lab)}</button>" for i, (pid, lab, _, _) in enumerate(pl))
        return f"<nav class='via-tabbar' role='tablist'>{btn}</nav>"

    def if_(self, n: Node, scope: dict) -> str:
        p = self.pages.get(id(n))
        if p:
            out = []
            targets = [(f"{p['id']}-{c['code']}", c) for c in self.views.get("categories") or []] if p["category"] and self.views.get("categories") else [(p["id"], None)]
            for pid, cat in targets:
                sc = dict(scope)
                sc["$page"] = cat
                on = self.first_page is None
                if on:
                    self.first_page = pid
                self.page_ids.append(pid)
                inner = "".join(self.el(k, sc) for k in n.kids)
                out.append(f"<div class='via-page{' on' if on else ''}' data-via-page='{_e(pid)}' id='via-page-{_e(pid)}' role='tabpanel'>{inner}</div>")
            return "".join(out)
        expr = _single(n.get("value"))
        ok, val = self.resolve(expr, scope, "cond") if expr else (False, None)
        if not ok:
            self.stats["conds_nodata"] += 1
            return ""
        return "".join(self.el(k, scope) for k in n.kids) if val else ""


def tabs_view(conv: dict, views: dict) -> list:
    rows = []
    for p in conv["pages"]:
        if p["category"] and views.get("categories"):
            rows += [{"code": f"{p['id']}-{c['code']}", "label": c["name"], "name": c["name"], "status": c["status"]} for c in views["categories"]]
        else:
            rows.append({"code": p["id"], "label": p["label"], "name": p["label"]})
    for i, r in enumerate(rows):
        r.update(on=i == 0, pick=TabRef(r["code"]))
    return rows


def render_skeleton(conv: dict, views: dict, theme: dict, binding: dict, title: str) -> str:
    """Template CSS + the template's own role classes on VIA's layout (for templates without slots, or as the second view)."""
    ir = conv["ir"]
    R = ir.get("regions") or {}
    comp = ir.get("components") or {}
    cls = lambda role, d: (R.get(role) or {}).get("class") or d
    ccls = lambda role, d: (comp.get(role) or {}).get("classes", Counter()).most_common(1)[0][0] if (comp.get(role) or {}).get("classes") else d
    hdr, left, tabs, pane = cls("header", "via-hd"), cls("left", "via-side"), cls("tabs", "via-tabs"), cls("pane", "via-pane-x")
    card, table, tab = ccls("card", "via-card"), ccls("table", "via"), ccls("tab", "")
    lampc = lambda s, t: pill(lamp4(s), t, theme)

    def tbl(rows, cols):
        if not rows:
            return "<p class='via-nodata-block'>NODATA · 0 列</p>"
        head = "".join(f"<th>{_e(c)}</th>" for c, _ in cols)
        body = "".join("<tr data-via-row='t'>" + "".join(f"<td>{lampc(r.get(k), r.get(k)) if k == 'status' else _e(r.get(k, ''))}</td>" for _, k in cols)
                       + "</tr>" for r in rows)
        return f"<div class='via-tw'><table class='{_e(table)}'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"

    def cards(rows):
        return "<div class='via-sk-cards'>" + "".join(
            f"<div class='{_e(card)} {_e(theme['acc'].get(lamp4(r.get('status')), ''))}' data-via-row='k'><div class='via-sk-k'>{_e(r.get('label') or r.get('name'))}</div>"
            f"<div class='via-sk-v' style='color:{_e(theme['lamp_hex'][lamp4(r.get('status'))])}'>{_e(r.get('value'))}</div>"
            f"<div class='via-sk-n'>{_e(r.get('note', ''))}</div></div>" for r in rows) + "</div>"
    charts = "<div class='via-sk-charts'>" + "".join(f"<figure class='{_e(card)} via-sk-fig' data-via-row='c'><figcaption>{_e(c['title'])}</figcaption>{c['chart']}</figure>"
                                                     for c in views.get("charts") or []) + "</div>"
    pages = [("overview", "總覽 Overview", cards(views.get("kpis") or []) + charts
              + tbl(views.get("summary") or [], [("來源", "name"), ("燈", "status"), ("tally", "tally"), ("綠比", "score"), ("距今", "age"), ("引擎", "engine")]))]
    for c in views.get("categories") or []:
        pages.append((c["code"].lower(), c["name"], cards(c["kpis"]) + tbl(c["items"], [("代碼", "code"), ("項", "name"), ("燈", "status"), ("說明", "note")])))
    pages.append(("sources", "來源 Sources", tbl(views.get("sources") or [], [("來源", "name"), ("燈", "status"), ("層", "tier"), ("距今", "age"), ("檔", "note")])))
    pages.append(("binding", "對接 Binding", tbl(views.get("bindings") or [], [("槽", "code"), ("VIA 來源", "name"), ("燈", "status"), ("怎麼對上", "note")])))
    pages.append(("top25", "TOP 25", tbl(views.get("top25") or [], [("編號", "code"), ("能力", "name"), ("狀態", "value"), ("為什麼", "note")])))
    tb = "".join(f"<button type='button' class='{_e(tab)} via-tab{' on' if i == 0 else ''}' data-via-tab='{pid}' aria-controls='via-page-{pid}' "
                 f"tabindex='{0 if i == 0 else -1}'>{_e(lab)}</button>" for i, (pid, lab, _) in enumerate(pages))
    body = "".join(f"<section class='{_e(pane)} via-page{' on' if i == 0 else ''}' data-via-page='{pid}' id='via-page-{pid}' role='tabpanel'>"
                   f"<h2 class='via-sk-h'>{_e(lab)}</h2>{html}</section>" for i, (pid, lab, html) in enumerate(pages))
    side = "".join(f"<div class='via-sk-src' data-via-row='s'>{lampc(s['status'], s['status'][0] if s['status'] else '?')} {_e(s['name'])}"
                   f"{' <b class=via-stale>STALE</b>' if s['tier'] == 'STALE' else ''}</div>" for s in views.get("sources") or [])
    links = "".join(f"<a class='via-sk-link' href='{_e(ln['href'])}'>{_e(ln['name'])}</a>" for ln in views.get("links") or [])
    return (f"<div class='via-sk'><header class='{_e(hdr)} via-sk-hd'><b>{_e(title)}</b><span class='via-sk-status'>{_e(views.get('status_line'))}</span></header>"
            f"<div class='via-sk-body'><aside class='{_e(left)} via-sk-side'><div class='via-sk-h'>來源 Sources</div>{side}"
            f"<div class='via-sk-h'>連結 Links</div>{links or '<span class=via-nodata>NODATA</span>'}</aside>"
            f"<main class='via-sk-main'><nav class='{_e(tabs)} via-tabbar' role='tablist'>{tb}</nav>{body}</main></div></div>")


# ---------------------------------------------------------------- page chrome · T15 guard · T16 dark · T18 print · T19 filter · T22 provenance

def derive_dark(hexes: dict) -> dict:
    out = {}
    for k, c in hexes.items():
        h, lum, s = _hls(c)
        if s < 0.2:
            lum2 = min(0.93, max(0.07, 1 - lum))
        else:
            lum2 = min(0.72, lum + 0.18) if lum < 0.55 else lum
        r, g, b = colorsys.hls_to_rgb(h, lum2, s)
        out[k] = "#" + "".join(f"{round(x * 255):02x}" for x in (r, g, b))
    return out


JS = r"""(function(){var d=document,R=d.documentElement;R.classList.add('via-js');
var tabs=[].slice.call(d.querySelectorAll('[data-via-tab]')),pages=[].slice.call(d.querySelectorAll('[data-via-page]'));
function show(id,push){var ids=pages.map(function(p){return p.getAttribute('data-via-page')});if(ids.indexOf(id)<0)id=ids.length?ids[0]:null;
pages.forEach(function(p){p.classList.toggle('on',p.getAttribute('data-via-page')===id)});
tabs.forEach(function(t){var on=t.getAttribute('data-via-tab')===id;t.classList.toggle('on',on);t.setAttribute('aria-selected',on?'true':'false');t.tabIndex=on?0:-1});
if(push&&id){try{history.replaceState(null,'','#tab='+encodeURIComponent(id))}catch(e){location.hash='tab='+encodeURIComponent(id)}}}
tabs.forEach(function(t,i){t.setAttribute('role','tab');t.addEventListener('click',function(){show(t.getAttribute('data-via-tab'),true)});
t.addEventListener('keydown',function(e){var k=e.key,j=-1;if(k==='ArrowRight')j=(i+1)%tabs.length;else if(k==='ArrowLeft')j=(i-1+tabs.length)%tabs.length;
else if(k==='Home')j=0;else if(k==='End')j=tabs.length-1;else if(k==='Enter'||k===' '){show(t.getAttribute('data-via-tab'),true);e.preventDefault();return}
if(j>=0){tabs[j].focus();show(tabs[j].getAttribute('data-via-tab'),true);e.preventDefault()}})});
var m=/tab=([^&]+)/.exec(location.hash||'');show(m?decodeURIComponent(m[1]):null,false);
window.addEventListener('hashchange',function(){var m=/tab=([^&]+)/.exec(location.hash||'');if(m)show(decodeURIComponent(m[1]),false)});
var f=d.getElementById('via-filter');if(f)f.addEventListener('input',function(){var q=f.value.trim().toLowerCase();
[].forEach.call(d.querySelectorAll('[data-via-row]'),function(r){if(!r.hasAttribute('data-via-disp'))r.setAttribute('data-via-disp',r.style.display||'');
r.style.display=(!q||r.textContent.toLowerCase().indexOf(q)>=0)?r.getAttribute('data-via-disp'):'none'})});
var tb=d.getElementById('via-theme');if(tb)tb.addEventListener('click',function(){R.setAttribute('data-theme',R.getAttribute('data-theme')==='dark'?'light':'dark')});
})();"""


def chrome_css(facts: dict, theme: dict, bk: dict, pal: dict) -> str:
    hexes = facts.get("hex") or {}
    dark = derive_dark(hexes)
    bp = facts.get("breakpoint") or 768
    padvar = next((k for k in (facts.get("vars") or {}) if k in ("pad", "gutter", "padding", "space-page", "page-pad")), "")
    bg, tx, ln = pal.get("bg") or "#ffffff", pal.get("text") or "#1f2937", pal.get("border") or "#d0d3d8"
    vh = ",".join("." + c for c in facts.get("vh") or [])
    return ("/* VIA template sync chrome (" + ENGINE + ") */"
            "img,svg,video,canvas{max-width:100%}"
            ".via-nodata{display:inline-block;font:600 9px ui-monospace,monospace;letter-spacing:.4px;color:#64748b;border:1px dashed #94a3b8;padding:0 3px;vertical-align:middle}"
            ".via-nodata-block{color:#64748b;font:12px ui-monospace,monospace}"
            ".via-pill{font:600 10px ui-monospace,monospace;padding:1px 6px;white-space:nowrap}"
            ".via-js [data-via-page]:not(.on){display:none!important}"
            ".via-tabbar{display:flex;flex-wrap:wrap;gap:4px;margin:0 0 8px;position:relative;z-index:2147482000}.via-tabbar .via-tab{font:inherit;cursor:pointer;border:1px solid " + ln + ";background:" + bg + ";color:" + tx + ";padding:4px 10px}"
            ".via-tabbar .via-tab.on{background:" + tx + ";color:" + bg + "}"
            "[data-via-tab]:focus-visible{outline:2px solid " + theme["lamp_hex"]["YELLOW"] + ";outline-offset:1px}"
            "table th{position:sticky;top:0;z-index:1}"
            ".via-tw{overflow-x:auto;max-width:100%}"
            ".via-dock{position:fixed;right:8px;bottom:8px;z-index:2147483000;max-width:calc(100vw - 16px);font:11px/1.4 system-ui,'Noto Sans TC',sans-serif;"
            "background:" + bg + ";color:" + tx + ";border:1px solid " + ln + ";box-shadow:0 2px 10px rgba(0,0,0,.15)}"
            ".via-dock summary{cursor:pointer;padding:5px 9px;list-style:none;white-space:nowrap}.via-dock summary::-webkit-details-marker{display:none}"
            ".via-dock .via-dock-b{padding:6px 9px;border-top:1px solid " + ln + ";display:flex;flex-direction:column;gap:5px;max-width:320px}"
            ".via-dock input{font:inherit;padding:3px 6px;border:1px solid " + ln + ";width:100%;box-sizing:border-box}"
            ".via-dock button{font:inherit;cursor:pointer;border:1px solid " + ln + ";background:" + bg + ";color:" + tx + ";padding:2px 8px}"
            ".via-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px;vertical-align:middle}"
            ".via-report{overflow-wrap:anywhere;padding:12px 16px;background:" + bg + ";color:" + tx + ";font:11px/1.5 system-ui,'Noto Sans TC',sans-serif;border-top:2px solid " + ln + "}"
            ".via-report table{border-collapse:collapse;width:100%}.via-report th,.via-report td{border:1px solid " + ln + ";padding:2px 6px;text-align:left;vertical-align:top;word-break:break-word}"
            ".via-report th{background:" + bg + "}"
            ".via-stale{font:700 9px ui-monospace,monospace;color:#fff;background:" + theme["lamp_hex"]["YELLOW"] + ";padding:0 4px}"
            ".via-sk{display:flex;flex-direction:column;min-height:100vh}.via-sk-hd{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:8px 16px}"
            ".via-sk-status{font:11px ui-monospace,monospace;opacity:.8}.via-sk-body{display:flex;flex:1;min-height:0}"
            ".via-sk-side{flex:0 0 auto;padding:8px 12px;min-width:0}.via-sk-main{flex:1;min-width:0;padding:8px 16px}"
            ".via-sk-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;margin:0 0 8px}"
            ".via-sk-charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px;margin:0 0 8px}"
            ".via-sk-fig{margin:0;padding:6px 8px;min-width:0}.via-sk-fig figcaption{font-weight:700;margin:0 0 4px}"
            ".via-sk-k{font-weight:700}.via-sk-v{font:700 14px ui-monospace,monospace}.via-sk-n{opacity:.75;font-size:10px;word-break:break-word}"
            ".via-sk-h{font-weight:700;margin:8px 0 4px}.via-sk-src{padding:2px 0}.via-sk-link{display:block;padding:2px 0}"
            ".via-sk table td,.via-sk table th{word-break:break-word}"
            f"@media (max-width:{bp}px){{.via-sk-body{{flex-direction:column}}.via-sk-side{{width:auto!important}}}}"
            "@media (max-width:480px){" + (f":root{{--{padvar}:16px}}" if padvar else "") +
            ".via-sk-main,.via-sk-hd,.via-report{padding-left:16px;padding-right:16px}.via-dock{right:8px;left:8px}"
            ".via-dock summary{white-space:normal}}"
            ":root[data-theme=dark]{" + "".join(f"--{k}:{v};" for k, v in dark.items()) + "}"
            ":root[data-theme=dark] body{background:" + (dark.get(next((k for k, v in hexes.items() if v == bg), ""), "#111") if hexes else "#111") + "}"
            "@media print{.via-dock{display:none!important}.via-js [data-via-page]{display:block!important}"
            "*{overflow:visible!important}" + (vh + "{height:auto!important}" if vh else "") + "table th{position:static}}")


def assemble(title: str, css_parts: list, body: str, preseed: str, prov: dict, report_html: str, dock_html: str) -> str:
    prov_json = json.dumps(prov, ensure_ascii=False).replace("<", "\\u003c")
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{_e(title)}</title>{preseed}" + "".join(f"<style>{c}</style>" for c in css_parts if c) +
            f"</head><body>{body}{report_html}{dock_html}"
            f"<script type='application/json' id='via-provenance'>{prov_json}</script><script>{JS}</script></body></html>")


def offline_scan(html: str) -> dict:
    """T20: what would reach the network if this page were opened."""
    ext_src = re.findall(r"""<(?:script|img|iframe|source|video|audio|embed)\b[^>]*\bsrc\s*=\s*["']?(?:https?:)?//""", html, re.I)
    ext_link = re.findall(r"""<link\b[^>]*\bhref\s*=\s*["']?(?:https?:)?//""", html, re.I)
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I)
                    + [_html.unescape(x) for x in re.findall(r"""\sstyle\s*=\s*"([^"]*)\"""", html)]
                    + [_html.unescape(x) for x in re.findall(r"""\sstyle\s*=\s*'([^']*)'""", html)])
    js = "\n".join(re.findall(r"<script(?![^>]*application/json)[^>]*>(.*?)</script>", html, re.S | re.I))
    ext_url = re.findall(r"""url\(\s*["']?(?:https?:)?//""", css, re.I)
    imports = re.findall(r"@import\b", css)
    js_net = re.findall(r"\bfetch\s*\(|XMLHttpRequest|WebSocket\s*\(|EventSource\s*\(|importScripts\s*\(", js)
    anchors = re.findall(r"""<a\b[^>]*\bhref\s*=\s*["']?https?://""", html, re.I)
    bad = len(ext_src) + len(ext_link) + len(ext_url) + len(imports) + len(js_net)
    return {"ext_src": len(ext_src), "ext_link": len(ext_link), "ext_url": len(ext_url), "imports": len(imports), "js_net": len(js_net),
            "external_anchor_links": len(anchors), "violations": bad, "lamp": "GREEN" if bad == 0 else "RED"}


def perf(html: str, bk: dict) -> dict:
    b = bk.get("budget") or {}
    size = len(html.encode("utf-8"))
    nodes = len(re.findall(r"<[a-zA-Z]", html))
    lamp = "GREEN" if size <= b.get("html_bytes_green", 1500000) and nodes <= b.get("dom_nodes_green", 6000) else \
        "YELLOW" if size <= b.get("html_bytes_yellow", 3000000) else "RED"
    return {"bytes": size, "elements": nodes, "lamp": lamp}


# ---------------------------------------------------------------- convert · sync · lock · diff · watch

def _jsonable(ir: dict) -> dict:
    def fix(x):
        if isinstance(x, set):
            return sorted(x)
        if isinstance(x, Counter):
            return dict(x.most_common())
        if isinstance(x, dict):
            return {k: fix(v) for k, v in x.items()}
        if isinstance(x, list):
            return [fix(v) for v in x]
        return x
    return fix(ir)


def convert(path: Path, out: Path | None = None, propose: bool = False, bk: dict | None = None) -> dict:
    out, bk = out or OUT, bk or book()
    path = Path(path)
    info = ingest(path)
    slug = slug_of(path.name, info["sha"])
    cd = out / "converted" / slug
    cd.mkdir(parents=True, exist_ok=True)
    tok_src = path
    if info["kind"] == "dc_bundle":
        tok_src = cd / "template.decoded.html"
        tok_src.write_text(info["text"], encoding="utf-8")
    doc = split_doc(info["text"]) if info["kind"] != "tokens" else {"css": [info["text"]] if path.suffix.lower() in (".css", ".scss") else [],
                                                                   "body_css": [], "links": [], "markup": "", "scripts_dropped": 0, "title": ""}
    root = parse(doc["markup"])
    css_all = "\n".join(doc["css"] + doc["body_css"])
    ir = analyse(root, css_all, bk)
    pages = find_pages(root, bk)
    try:
        rep = PRIOR.plan(tok_src, write=propose)
    except Exception as ex:  # tokens are optional for the UI; the report says why
        rep = {"state": "NODATA", "why": f"{type(ex).__name__}: {ex}"[:200], "candidate": {}, "warnings": [], "mapped": 0, "unmapped": 0,
               "next_version": "", "layout": {"best": None}}
    cand = rep.pop("candidate", {}) or {}
    if cand:
        (cd / "CANDIDATE_TemplateSSOT.json").write_text(json.dumps(cand, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    comps = {r: {"n": c["n"], "classes": dict(c["classes"].most_common(8))} for r, c in ir["components"].items()}
    dup = [{"signature": s, "role": v["role"], "n": v["n"]} for s, v in ir["signatures"].items() if v["n"] > 1]
    lists = {lp: {"kind": L["kind"], "hint": L["hint"], "fields": sorted(L["fields"]), "parent": L["parent"]} for lp, L in ir["lists"].items()}
    body = {"schema": "VIA.TemplateIR.v1", "engine": ENGINE, "source": _rel(path), "name": path.name, "kind": info["kind"], "sha": info["sha"],
            "bytes": info["bytes"], "title": doc["title"], "regions": ir["regions"], "components": comps,
            "component_library": {"unique": len(ir["signatures"]), "repeated": sorted(dup, key=lambda x: -x["n"])[:40]},
            "slots": {"scalars": {k: sorted(v["ctx"]) for k, v in ir["scalars"].items()}, "lists": lists,
                      "conds": sorted(ir["conds"]), "events": sorted(ir["events"])},
            "pages": ir["pages"], "x_import": ir["x_import"],
            "tokens": {"vars": ir["css"]["vars"], "n_vars": len(ir["css"]["vars"]), "breakpoint": ir["css"]["breakpoint"], "vh": ir["css"]["vh"],
                       "ssot_next": rep.get("next_version"), "mapped": rep.get("mapped"), "unmapped": rep.get("unmapped"),
                       "layout_best": (rep.get("layout") or {}).get("best"), "contrast_warnings": rep.get("warnings") or [],
                       "state": rep.get("state"), "proposed": bool(propose and cand)},
            "offline": {"links_dropped": len(doc["links"]), "scripts_dropped": doc["scripts_dropped"], "resources": len(info["resources"])}}
    body["ir_sha"] = _sha(json.dumps({**{k: body[k] for k in ("regions", "components", "slots", "pages")}, "vars": body["tokens"]["vars"]},
                                     sort_keys=True, ensure_ascii=False, default=str).encode())
    (cd / "TEMPLATE_IR.json").write_text(json.dumps(body, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    (cd / "COMPONENTS.json").write_text(json.dumps({"components": comps, "library": body["component_library"], "lists": lists},
                                                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"info": {k: v for k, v in info.items() if k not in ("text", "resources")}, "resources": info["resources"], "doc": doc, "root": root,
            "ir": ir, "pages": pages, "irdoc": body, "plan": rep, "candidate": cand, "dir": cd, "slug": slug}


def lock_state(conv: dict) -> dict:
    p = conv["dir"] / "TEMPLATE_LOCK.json"
    lk = PRIOR._json(p) if p.exists() else None
    if not lk:
        return {"state": "NONE", "why": "還沒鎖(lock --in <模板> --apply;操作員的手)"}
    same = lk.get("sha") == conv["info"]["sha"] and lk.get("ir_sha") == conv["irdoc"]["ir_sha"]
    return {"state": "OK" if same else "DRIFT", "locked_at": lk.get("at"), "locked_sha": lk.get("sha"), "now_sha": conv["info"]["sha"],
            "why": "" if same else "模板或其 IR 與鎖不同:確認新頁後由操作員 lock --apply 重鎖"}


def lock(path: Path, apply_: bool = False, out: Path | None = None) -> dict:
    conv = convert(path, out)
    st = lock_state(conv)
    if not apply_:
        return {"state": "DRY", "now": st, "would_write": str(conv["dir"] / "TEMPLATE_LOCK.json")}
    rec = {"engine": ENGINE, "at": _utc(), "source": _rel(path), "sha": conv["info"]["sha"], "ir_sha": conv["irdoc"]["ir_sha"],
           "by": os.environ.get("VIA_OPERATOR", "operator")}
    (conv["dir"] / "TEMPLATE_LOCK.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"state": "LOCKED", **rec}


def ir_diff(a: dict, b: dict) -> dict:
    sa, sb = a.get("slots") or {}, b.get("slots") or {}
    ka, kb = set(sa.get("scalars") or {}) | set(sa.get("lists") or {}), set(sb.get("scalars") or {}) | set(sb.get("lists") or {})
    ta, tb = (a.get("tokens") or {}).get("vars") or {}, (b.get("tokens") or {}).get("vars") or {}
    ca, cb = a.get("components") or {}, b.get("components") or {}
    comp = {r: [(ca.get(r) or {}).get("n", 0), (cb.get(r) or {}).get("n", 0)] for r in sorted(set(ca) | set(cb))
            if (ca.get(r) or {}).get("n", 0) != (cb.get(r) or {}).get("n", 0)}
    d = {"slots_added": sorted(kb - ka), "slots_removed": sorted(ka - kb), "components": comp,
         "tokens_changed": {k: [ta[k], tb[k]] for k in sorted(set(ta) & set(tb)) if ta[k] != tb[k]},
         "tokens_added": sorted(set(tb) - set(ta)), "tokens_removed": sorted(set(ta) - set(tb)),
         "pages": [[p["id"] for p in a.get("pages") or []], [p["id"] for p in b.get("pages") or []]]}
    d["same"] = not (d["slots_added"] or d["slots_removed"] or comp or d["tokens_changed"] or d["tokens_added"] or d["tokens_removed"]
                     or d["pages"][0] != d["pages"][1])
    return d


def _ir_of(p: Path, out: Path | None) -> dict:
    p = Path(p)
    if p.suffix == ".json":
        j = PRIOR._json(p) or {}
        if j.get("schema") == "VIA.TemplateIR.v1":
            return j
    return convert(p, out)["irdoc"]


def sync(path: Path, out: Path | None = None, mode: str = "auto", root: Path | None = None, bk: dict | None = None, write_index: bool = True) -> dict:
    out, bk = out or OUT, bk or book()
    t0 = time.time()
    conv = convert(path, out, bk=bk)
    ir = conv["ir"]
    facts = ir["css"]
    theme = theme_of(facts, bk)
    sd = out / "synced" / conv["slug"]
    sd.mkdir(parents=True, exist_ok=True)
    srcs = load_sources(root, bk)
    views = build_views(srcs, ir, theme, bk, sd)
    views["tabs"] = tabs_view(conv, views)
    b = bind(ir, views, bk)
    views["bindings"] = binding_rows(b)
    views["progress"] = f"已對接 {b['coverage']['bound']}/{b['coverage']['total']} 槽 · {b['coverage']['pct']}%"
    b = bind(ir, views, bk)                                  # second pass: bindings / progress now carry values
    views["bindings"] = binding_rows(b)
    views["progress"] = f"已對接 {b['coverage']['bound']}/{b['coverage']['total']} 槽 · {b['coverage']['pct']}%"
    has_slots = bool(ir["scalars"] or ir["lists"])
    # layout auto-choice: the template's own markup leads only when it can show real data (≥ 30 % of data slots bound);
    # otherwise VIA's skeleton in the template's look leads and the faithful copy is still written next to it
    faithful = has_slots and mode != "skeleton"
    primary_v = "faithful" if faithful and (mode == "faithful" or b["coverage"]["pct"] >= 30) else "skeleton"
    mode_why = ("操作員指定" if mode != "auto" else "沒有槽 → 骨架" if not has_slots else
                f"覆蓋 {b['coverage']['pct']}% {'≥' if primary_v == 'faithful' else '<'} 30% → {primary_v} 為主頁")
    off = Offline(conv["resources"], bk)
    tpl_css = [off.css(c) for c in conv["doc"]["css"]]
    pal = (conv["candidate"] or {}).get("palette") or {}
    kit = PRIOR.css(PRIOR.spec())
    ch_css = chrome_css(facts, theme, bk, pal)
    title_base = conv["doc"]["title"] if conv["doc"]["title"] and conv["doc"]["title"] != "Bundled Page" else Path(path).name
    lk = lock_state(conv)
    mod = {"id": "via-tpl-" + conv["slug"].lower(), "name": "模板同步 " + conv["slug"], "type": "dashboard", "enabled": True, "pinned": False,
           "system": False, "note": f"{ENGINE} sync"}
    try:
        preseed = PRIOR._preseed(mod)
    except Exception:
        preseed = ""
    outputs = {}
    for variant in (["faithful", "skeleton"] if faithful else ["skeleton"]):
        r = Renderer(conv, views, b, theme, off, bk)
        if variant == "faithful":
            body = "".join(r.el(k, {}) for k in conv["root"].kids)
            css_parts = tpl_css + [ch_css]
        else:
            body = render_skeleton(conv, views, theme, b, title_base)
            css_parts = [kit] + tpl_css + [ch_css]
        prov = {"engine": ENGINE, "version": VERSION, "utc": _utc(), "variant": variant, "template": _rel(path), "template_sha": conv["info"]["sha"],
                "ir_sha": conv["irdoc"]["ir_sha"], "binding_book": book().get("_path"), "coverage": b["coverage"], "lock": lk["state"],
                "sources": {s["id"]: {"state": s["state"], "sha": s["sha"], "age_h": s["age_h"], "lamp": s["lamp"], "stale": s["stale"]} for s in srcs}}
        un = b["unmapped"]
        rep_rows = "".join(f"<tr><td>{_e(u['slot'])}</td><td>{_e(u['kind'])}</td><td>{_e(u['why'])}</td></tr>" for u in un)
        src_rows = "".join(f"<tr><td><span class='via-dot' style='background:{_e(theme['lamp_hex'][s['lamp']])}'></span>{_e(s['lamp'])}"
                           f"{' <b class=via-stale>STALE</b>' if s['stale'] else ''}</td><td>{_e(s['name'])}</td><td>{_e(s['state'])}</td>"
                           f"<td>{_e('—' if s['age_h'] is None else str(s['age_h']) + 'h')}</td><td>{_e(s['file'])}</td><td>{_e(s['sha'] or '—')}</td></tr>" for s in srcs)
        report = (f"<section class='via-report' id='via-unmapped'><h3>模板同步報告 · Template sync report</h3>"
                  f"<p>對接覆蓋 {b['coverage']['bound']}/{b['coverage']['total']}({b['coverage']['pct']}%)· 未對接 {len(un)} · "
                  f"呈現型槽(class/style,不算資料){len(b['presentational'])} · 靜態化的互動事件 {len(b['events'])} · 格式鎖 {_e(lk['state'])}</p>"
                  + (f"<div class='via-tw'><table><thead><tr><th>未對接槽 unmapped slot</th><th>種類</th><th>原因</th></tr></thead><tbody>{rep_rows}</tbody></table></div>" if un else "<p>未對接槽:0</p>")
                  + f"<h4>資料來源 Sources(唯讀)</h4><div class='via-tw'><table><thead><tr><th>燈</th><th>來源</th><th>狀態</th><th>距今</th><th>檔</th><th>sha</th></tr></thead>"
                  f"<tbody>{src_rows}</tbody></table></div>"
                  f"<footer class='via-prov'>出處 provenance · {_e(ENGINE)} {_e(VERSION)} · {_e(prov['utc'])} · 模板 {_e(_rel(path))} sha {_e(conv['info']['sha'])}"
                  f" · IR {_e(conv['irdoc']['ir_sha'])} · {_e(variant)} · 同義冊 {_e(prov['binding_book'])}</footer></section>")
        lamp_now = worst([s["lamp"] for s in srcs if s["status_src"]])
        dock = (f"<details class='via-dock'><summary><span class='via-dot' style='background:{_e(theme['lamp_hex'][lamp_now])}'></span>VIA 同步 · "
                f"{_e(lamp_now)} · 未對接 {len(un)}</summary><div class='via-dock-b'><div>{_e(views['status_line'])}</div>"
                f"<div>{_e(views['progress'])}</div><input id='via-filter' type='search' placeholder='篩選 filter rows' aria-label='filter rows'>"
                f"<div><button type='button' id='via-theme'>淺 / 深 theme</button> <a href='#via-unmapped'>報告 report</a></div></div></details>")
        html = assemble(f"{title_base} · VIA", css_parts, body, preseed, prov, report, dock)
        name = f"VIA_UI_{conv['slug']}_latest.html" if variant == primary_v else f"VIA_UI_{conv['slug']}_{variant}_latest.html"
        (sd / name).write_text(html, encoding="utf-8")
        # T24 round trip: the rendered page re-converted keeps the template's tokens and regions
        rt_doc = split_doc(html)
        rt_facts = css_facts("\n".join(rt_doc["css"]), bk)
        tv = {k: v for k, v in facts["vars"].items() if not k.startswith("via-")}
        rt_vars = {k: v for k, v in rt_facts["vars"].items() if not k.startswith("via-")}
        rt_regions = set(analyse(parse(rt_doc["markup"]), "", bk)["regions"]) if variant == "faithful" else set()
        outputs[variant] = {"file": str(sd / name), "offline": offline_scan(html), "perf": perf(html, bk), "stats": dict(r.stats),
                            "pages": r.page_ids if variant == "faithful" else None,
                            "roundtrip": {"tokens_same": all(rt_vars.get(k) == v for k, v in tv.items()),
                                          "regions_same": (rt_regions >= set(ir["regions"])) if variant == "faithful" else None}}
    contrast = []
    bgc = PRIOR.parse_color(pal.get("bg") or "") or "#ffffff"
    for lamp, c in theme["lamp_hex"].items():
        ratio = PRIOR.contrast(c, bgc)
        contrast.append({"pair": f"lamp {lamp} / bg", "ratio": ratio, "need": 3.0, "ok": ratio >= 3.0})
    for w in (conv["plan"].get("warnings") or []):
        contrast.append({"pair": w, "ratio": None, "need": 4.5, "ok": False})
    tx, bgd = PRIOR.parse_color(pal.get("text") or ""), PRIOR.parse_color(pal.get("bg") or "")
    dk = derive_dark(facts.get("hex") or {})
    dark_pair = None
    if tx and bgd:
        name_of = lambda c: next((k for k, v in (facts.get("hex") or {}).items() if v == c), None)
        nt, nb = name_of(tx), name_of(bgd)
        if nt and nb:
            dark_pair = PRIOR.contrast(dk[nt], dk[nb])
    primary = outputs[primary_v]
    probs = []
    if any(o["offline"]["violations"] for o in outputs.values()):
        probs.append(("RED", "離線違規(外部資源)"))
    if b["unmapped"]:
        probs.append(("YELLOW", f"未對接 {len(b['unmapped'])} 槽"))
    if lk["state"] == "DRIFT":
        probs.append(("YELLOW", "模板與鎖不同(DRIFT)"))
    if primary["perf"]["lamp"] != "GREEN":
        probs.append((primary["perf"]["lamp"], "效能預算"))
    lamp = worst([p[0] for p in probs]) if probs else "GREEN"
    rep = {"schema": "VIA.TemplateSync.v1", "engine": ENGINE, "utc": _utc(), "template": _rel(path), "slug": conv["slug"], "kind": conv["info"]["kind"],
           "lamp": lamp, "problems": [p[1] for p in probs], "mode": primary_v, "mode_why": mode_why, "outputs": outputs,
           "coverage": b["coverage"], "unmapped": b["unmapped"], "presentational": b["presentational"], "events_static": b["events"],
           "lists": {k: {x: v[x] for x in ("view", "how", "rows", "kind", "fields")} for k, v in b["lists"].items()},
           "scalars": b["scalars"], "pages": [p["id"] for p in ir["pages"]], "regions": ir["regions"],
           "components": conv["irdoc"]["components"], "library": conv["irdoc"]["component_library"]["unique"],
           "theme": theme, "contrast": contrast, "dark_text_bg_ratio": dark_pair, "lock": lk, "offline_rewrites": dict(off.stats),
           "tokens": {k: conv["irdoc"]["tokens"][k] for k in ("ssot_next", "mapped", "unmapped", "state", "proposed", "breakpoint")},
           "sources": [{k: s[k] for k in ("id", "name", "state", "lamp", "age_h", "stale", "sha", "file", "note")} for s in srcs],
           "secs": round(time.time() - t0, 2)}
    (sd / "BINDING_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    if write_index:
        write_sync_index(out)
    return rep


def write_sync_index(out: Path | None = None) -> Path:
    out = out or OUT
    rows = []
    for p in sorted((out / "synced").glob("*/BINDING_latest.json")):
        j = PRIOR._json(p) or {}
        rows.append(j)
    body = ("<div style='overflow-x:auto;max-width:100%'><table class='via'><tr><th>燈</th><th>模板</th><th>種類</th><th>模式</th><th>覆蓋</th><th>未對接</th><th>離線</th><th>大小</th><th>頁</th><th>時間</th></tr>"
            + "".join(f"<tr data-via-row='i'><td>{PRIOR.lamp(j.get('lamp', 'NODATA'), j.get('lamp', ''))}</td><td>{_e(j.get('template'))}</td><td>{_e(j.get('kind'))}</td>"
                      f"<td>{_e(j.get('mode'))}</td><td>{_e((j.get('coverage') or {}).get('pct'))}%</td><td>{len(j.get('unmapped') or [])}</td>"
                      f"<td>{_e(' / '.join(o['offline']['lamp'] for o in (j.get('outputs') or {}).values()))}</td>"
                      f"<td>{_e(' / '.join(str(o['perf']['bytes']) for o in (j.get('outputs') or {}).values()))}</td>"
                      f"<td>" + " ".join(f"<a href='{_e(os.path.relpath(o['file'], out))}'>{_e(v)}</a>" for v, o in (j.get('outputs') or {}).items()) +
                      f"</td><td>{_e(j.get('utc'))}</td></tr>" for j in rows) + "</table></div>"
            + f"<p class='via-note' style='overflow-wrap:anywhere'>投放夾 {_e((book().get('drop') or {}).get('inbox'))} · 同義 / 來源 / TOP25 冊 {_e(book().get('_path'))} · {_e(ENGINE)}</p>")
    html = PRIOR.page("模板同步總表 Template sync index", body, module={"id": "via-tpl-index", "name": "模板同步總表"})
    p = out / "SYNC_INDEX_latest.html"
    p.write_text(html, encoding="utf-8")
    (out / "SYNC_INDEX_latest.json").write_text(json.dumps([{k: j.get(k) for k in ("template", "slug", "lamp", "mode", "coverage", "utc")} for j in rows],
                                                           ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return p


def drop_files(inbox: Path | None = None, bk: dict | None = None) -> list:
    bk = bk or book()
    inbox = inbox or (VIA / (bk.get("drop") or {}).get("inbox", "VIA_Reports/template_adapter/inbox"))
    pats = tuple((bk.get("drop") or {}).get("patterns") or [".dc.html", ".html", ".htm"])
    if not inbox.exists():
        return []
    return sorted(p for p in inbox.iterdir() if p.is_file() and p.name.lower().endswith(pats))


def _source_sig(root: Path | None = None, bk: dict | None = None) -> dict:
    root, bk = root or VIA, bk or book()
    sig = {}
    for spec in bk.get("sources") or []:
        p = _glob_newest(root, spec["path"])
        try:
            st = p.stat()
            sig[spec["id"]] = f"{st.st_size}:{st.st_mtime_ns}:{p.name}"
        except OSError:
            sig[spec["id"]] = "ABSENT"
    return sig


def watch(inbox: Path | None = None, out: Path | None = None, once: bool = True, interval: float = 5.0, cycles: int = 0,
          root: Path | None = None, bk: dict | None = None, log=print) -> dict:
    out, bk = out or OUT, bk or book()
    inbox = inbox or (VIA / (bk.get("drop") or {}).get("inbox", "VIA_Reports/template_adapter/inbox"))
    inbox.mkdir(parents=True, exist_ok=True)
    state_p = out / "WATCH_STATE.json"
    n, last = 0, {"state": "NODATA"}
    while True:
        n += 1
        tpls = drop_files(inbox, bk)
        if not tpls:
            ref = VIA / ((bk.get("drop") or {}).get("reference_copy") or "")
            last = {"state": "NODATA", "cycle": n, "inbox": str(inbox), "why": f"投放夾沒有模板(放「{(bk.get('drop') or {}).get('expected')}」進去)",
                    "reference_copy": _rel(ref) if ref.exists() else None, "synced": [], "skipped": []}
            log(f"[模板同步 watch] NODATA · 投放夾 {inbox} 是空的" + (f" · 參考副本在 {_rel(ref)}(不自動拿來用;要試 sync --in 它)" if ref.exists() else ""))
        else:
            prev = PRIOR._json(state_p) or {}
            src_sig = _source_sig(root, bk)
            data_changed = prev.get("sources") != src_sig
            tsig = {p.name: _sha(p.read_bytes()) for p in tpls}
            todo = [p for p in tpls if data_changed or (prev.get("templates") or {}).get(p.name) != tsig[p.name]]
            done = []
            for p in todo:
                r = sync(p, out, root=root, bk=bk, write_index=False)
                done.append({"template": p.name, "lamp": r["lamp"], "coverage": r["coverage"]["pct"], "unmapped": len(r["unmapped"])})
                log(f"[模板同步 watch] {p.name} → {r['lamp']} · 覆蓋 {r['coverage']['pct']}% · 未對接 {len(r['unmapped'])}")
            if done or not (out / "SYNC_INDEX_latest.html").exists():
                write_sync_index(out)
            state_p.parent.mkdir(parents=True, exist_ok=True)
            state_p.write_text(json.dumps({"templates": tsig, "sources": src_sig, "utc": _utc(), "engine": ENGINE}, ensure_ascii=False, indent=1),
                               encoding="utf-8")
            last = {"state": "SYNCED" if done else "UNCHANGED", "cycle": n, "inbox": str(inbox), "synced": done,
                    "skipped": [p.name for p in tpls if p not in todo], "data_changed": data_changed}
            if not done:
                log(f"[模板同步 watch] 沒變 · 模板 {len(tpls)} · 資料來源沒動(sha / mtime)")
        if once or (cycles and n >= cycles):
            return last
        time.sleep(max(0.5, interval))


# ---------------------------------------------------------------- CLI

def _arg(args, name, default=""):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    verb = a[0] if a else ""
    if verb not in ("convert", "sync", "watch", "diff", "lock", "top25", "sources", "drop"):
        return PRIOR.main(a)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    bk = book()
    if verb == "top25":
        rows = bk.get("top25") or []
        if "--json" in a:
            print(json.dumps(rows, ensure_ascii=False, indent=1))
        else:
            for t in rows:
                print(f"  {t['id']} [{t['status']:<11}] {t['name']} · 檢 {t['check']}")
            c = Counter(t["status"] for t in rows)
            print(f"[TOP25] {len(rows)} 項 · " + " · ".join(f"{k} {v}" for k, v in c.items()) + f" · 冊 {bk.get('_path')}")
        return 0
    if verb == "sources":
        for s in load_sources():
            print(f"  {s['lamp']:<7} {'STALE ' if s['stale'] else ''}{s['id']:<14} {s['state']:<10} {s['age_h'] if s['age_h'] is not None else '—':>6}h  {s['file']}")
        return 0
    if verb == "drop":
        inbox = VIA / (bk.get("drop") or {}).get("inbox", "")
        fs = drop_files()
        print(json.dumps({"inbox": str(inbox), "exists": inbox.exists(), "templates": [p.name for p in fs],
                          "state": "READY" if fs else "NODATA", "expected": (bk.get("drop") or {}).get("expected")}, ensure_ascii=False, indent=1))
        return 0 if fs else 2
    if verb == "convert":
        src = _arg(a, "--in")
        if not src or not Path(src).exists():
            print(json.dumps({"state": "NODATA", "why": "convert --in <模板檔>"}, ensure_ascii=False))
            return 2
        c = convert(Path(src), propose="--propose" in a)
        d = c["irdoc"]
        print(f"[模板轉換] {d['kind']} · {d['name']} · sha {d['sha']} · IR {d['ir_sha']} · 區塊 {','.join(d['regions']) or '—'} · 元件 "
              + " ".join(f"{k}{v['n']}" for k, v in d["components"].items()) + f" · 元件庫 {d['component_library']['unique']}"
              f" · 槽 純量 {len(d['slots']['scalars'])} 清單 {len(d['slots']['lists'])} 條件 {len(d['slots']['conds'])} 事件 {len(d['slots']['events'])}"
              f" · 分頁 {len(d['pages'])} · token {d['tokens']['n_vars']} → TemplateSSOT {d['tokens']['ssot_next']} 候選"
              f"(對上 {d['tokens']['mapped']};{'已寫成 apply 用候選' if d['tokens']['proposed'] else '只在 converted/ 夾;要進 apply 加 --propose'})")
        print(f"  IR {c['dir'] / 'TEMPLATE_IR.json'}")
        return 0
    if verb == "sync":
        src = _arg(a, "--in")
        targets = [Path(src)] if src else drop_files()
        if not targets or not all(p.exists() for p in targets):
            print(json.dumps({"state": "NODATA", "why": f"沒有模板:sync --in <檔> 或放進投放夾 {(bk.get('drop') or {}).get('inbox')}"}, ensure_ascii=False))
            return 2
        worst_rc = 0
        for p in targets:
            r = sync(p, mode=_arg(a, "--mode", "auto"))
            o = r["outputs"][r["mode"]]
            print(f"[模板同步] {r['lamp']} · {p.name} · {r['mode']} · 覆蓋 {r['coverage']['bound']}/{r['coverage']['total']}({r['coverage']['pct']}%)"
                  f" · 未對接 {len(r['unmapped'])} · 離線 {o['offline']['lamp']} · {o['perf']['bytes']} B · 鎖 {r['lock']['state']} · {r['secs']}s")
            for v, oo in r["outputs"].items():
                print(f"  {v}: {oo['file']}")
            worst_rc = max(worst_rc, {"GREEN": 0, "YELLOW": 2, "NODATA": 2, "RED": 1}[r["lamp"]])
        print(f"  總表 {OUT / 'SYNC_INDEX_latest.html'}")
        return worst_rc
    if verb == "watch":
        try:
            r = watch(once="--once" in a, interval=float(_arg(a, "--interval", "5") or 5), cycles=int(_arg(a, "--cycles", "0") or 0))
        except KeyboardInterrupt:
            print("[模板同步 watch] 停(Ctrl-C)")
            return 0
        return 0 if r["state"] in ("SYNCED", "UNCHANGED") else 2
    if verb == "diff":
        pa, pb = _arg(a, "--a"), _arg(a, "--b")
        if not (pa and pb and Path(pa).exists() and Path(pb).exists()):
            print(json.dumps({"state": "NODATA", "why": "diff --a <模板|IR> --b <模板|IR>"}, ensure_ascii=False))
            return 2
        d = ir_diff(_ir_of(Path(pa), None), _ir_of(Path(pb), None))
        print(json.dumps(d, ensure_ascii=False, indent=1))
        return 0
    if verb == "lock":
        src = _arg(a, "--in")
        if not src or not Path(src).exists():
            print(json.dumps({"state": "NODATA", "why": "lock --in <模板> [--apply]"}, ensure_ascii=False))
            return 2
        print(json.dumps(lock(Path(src), "--apply" in a), ensure_ascii=False, indent=1))
        return 0
    return 2


# ---------------------------------------------------------------- selftest (fixtures only; never writes registry or the real VIA_Reports)

FIXTURE_DC = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Fixture UI</title><script src="./support.js"></script></head><body><x-dc><helmet>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans" rel="stylesheet">
<style>@import url("https://example.invalid/x.css");
:root{--bg:#f2f1ec;--paper:#ffffff;--ink:#1a1a17;--line:#d0d3d8;--zebra:#f6f4ef;--up:#9e2b25;--dn:#3c6660;--am:#b0842e;--gy:#7d7a73;--pad:12px}
body{background:var(--bg);color:var(--ink)} .app-root{height:100vh;overflow:hidden}
.ucc-head{padding:8px} .ucc-left{width:260px} .tabs{display:flex} .tab.on{font-weight:700} .pane{padding:var(--pad)}
.card{border-left:3px solid var(--gy)} .card.up{border-left-color:var(--up)} .card.dn{border-left-color:var(--dn)} .card.am{border-left-color:var(--am)}
.log .ok{color:#8fc9b4} .log .wn{color:#d8b25e} .log .er{color:#d98b83} .log .in{color:#c9c6bd} .pill{color:#fff}
.bg-img{background:url("https://cdn.example.invalid/bg.png")}
@media(max-width:860px){.ucc-left{width:auto}}
</style></helmet>
<div class="app-root"><header class="ucc-head"><h1>Fixture</h1><div>{{ runStat }}</div><div>引擎 {{ engN }} · {{ mysteryN }}</div></header>
<aside class="ucc-left"><sc-for list="{{ subs }}" as="s" hint-placeholder-count="3"><a href="{{ s.href }}">{{ s.name }}</a></sc-for>
<div class="log"><sc-for list="{{ logs }}" as="l" hint-placeholder-count="4"><div class="l {{ l.lvCs }}"><span>{{ l.ts }}</span>{{ l.txt }}</div></sc-for></div>
<div class="bogus"><sc-for list="{{ widgets }}" as="w" hint-placeholder-count="5"><span>{{ w.name }}</span></sc-for></div></aside>
<div class="ucc-right"><div class="tabs"><sc-for list="{{ tabs }}" as="t"><span sc-camel-on-click="{{ t.pick }}" class="tab {{ t.onCs }}">{{ t.label }}</span></sc-for></div>
<div class="pane"><sc-if value="{{ isT1 }}"><div class="hd">Overview</div>
<div class="grid"><sc-for list="{{ vKpis }}" as="k"><div class="card {{ k.acc }}"><div>{{ k.label }}</div><div style="{{ k.vCs }}">{{ k.value }}</div></div></sc-for></div>
<div style="display:grid;grid-template-columns:repeat(5,64px)"><sc-for list="{{ vKpis }}" as="h" hint-placeholder-count="5"><b>{{ h.label }}</b></sc-for></div>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr"><sc-for list="{{ valRows }}" as="v"><div style="display:contents"><div style="{{ v.rowCs }}">{{ v.id }}</div><div>{{ v.badge }}</div><div>{{ v.flux }}</div></div></sc-for></div>
<sc-for list="{{ gallery }}" as="g"><div class="chart">{{ g.title }}{{ g.chart }}</div></sc-for></sc-if>
<sc-if value="{{ isCat }}"><div class="hd">{{ catName }}</div><sc-for list="{{ catItems }}" as="c"><div><span class="pill" style="background:{{ c.color }}">{{ c.status }}</span>{{ c.name }}</div></sc-for></sc-if>
<sc-if value="{{ isEnd }}"><div class="hd">End</div><sc-for list="{{ ssot }}" as="s"><div>{{ s.name }} <sc-for list="{{ s.lines }}" as="l"><i>{{ l.k }}={{ l.v }}</i></sc-for></div></sc-for></sc-if>
</div></div><footer class="ucc-foot"><span class="bg-img" style="background-image:url(&quot;RES-IMG&quot;)"></span><img src="https://cdn.example.invalid/x.png"></footer></div>
<script type="text/x-dc">class C { state(){ return { widgets:[{name:'DEMO-FAKE-WIDGET'}] } } }</script>
</x-dc></body></html>"""


def _fixture_root(td: Path, stale_h: float = 0.0) -> Path:
    root = td / "VIA"
    now = time.time()

    def put(rel, obj, age_h=0.0, raw=None):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(raw if raw is not None else json.dumps(obj, ensure_ascii=False), encoding="utf-8")
        os.utime(p, (now - age_h * 3600, now - age_h * 3600))
    put("VIA_Reports/panorama/monitor_latest.json", {"engine": "fixture", "at": "2026-09-30T00:00:00Z", "verdict": "GREEN",
                                                     "rows": [{"track": "A", "lamp": "GREEN", "value": "ok"}, {"track": "B", "lamp": "RED", "value": "bad"}]})
    put("VIA_Reports/vcgc/TEST_latest.json", {"door": "fixture", "lamp": "YELLOW", "rows": [{"id": "V-x", "name": "x", "lamp": "YELLOW", "secs": 1.5, "last": "note"}]},
        age_h=stale_h)
    put("VIA_Reports/sdd/SDD_CHECK_latest.json", {"lamp": "GREEN", "rows": [{"lamp": "GREEN", "rule": "X-COL", "msg": "fine"}, {"lamp": "YELLOW", "rule": "X-UP", "msg": "one way"}]})
    put("VIA_Reports/vdf_chain/VDFCHAIN_latest.json", None, raw="{not json")
    put("supportive modules/registry/VIA_VCGC_FunctionLedger_v0100.jsonl", None,
        raw="\n".join(json.dumps({"ts": f"2026-09-30T0{i}:00:00+00:00", "event": "changed", "id": f"py:e{i}", "version": "v0101"}) for i in range(3)))
    return root


def selftest() -> int:
    import contextlib
    import io
    import tempfile
    results, ids = [], {}

    def chk(cid, name, ok, note=""):
        results.append(bool(ok))
        ids.setdefault(cid, []).append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {cid} {name}{(' · ' + str(note)) if note and not ok else ''}")
    print(f"=== {ENGINE} · 自測(夾具模板 + 夾具來源;不寫 registry、不寫真的 VIA_Reports)===")
    bk = book()
    # prior selftest must not gain failures
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prior_rc = PRIOR.selftest()
    prior_fail = [ln for ln in buf.getvalue().splitlines() if "[FAIL]" in ln]
    chk("C00", "前版 v0100 自測照過(薄尾載入不改它的行為)", prior_rc == 0 and not prior_fail, " / ".join(prior_fail)[:200])
    chk("C00", "TOP25 冊:25 項 · T01..T25 · 狀態只用 IMPLEMENTED / PARTIAL / PLANNED · 每項有檢號",
        [t["id"] for t in bk.get("top25") or []] == [f"T{i:02d}" for i in range(1, 26)]
        and all(t["status"] in ("IMPLEMENTED", "PARTIAL", "PLANNED") and re.fullmatch(r"C\d\d", t.get("check", "")) for t in bk["top25"]))
    keep_out, keep_prior_out = globals()["OUT"], PRIOR.OUT
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        out = td / "out"
        PRIOR.OUT = out                                          # plan(--propose) lands in the temp tree too
        globals()["OUT"] = out
        try:
            dc = td / "Fixture UI.dc.html"
            dc.write_text(FIXTURE_DC, encoding="utf-8")
            font = gzip.compress(b"wOF2-fixture-font-bytes")
            img = base64.b64encode(b"\x89PNG" + b"0" * 400000).decode()
            tpl_bundled = FIXTURE_DC.replace("</style></helmet>", "@font-face{font-family:'X';src:url(\"RES-FONT\") format('woff2');"
                                             "unicode-range:U+0000-00FF}@font-face{font-family:'X';src:url(\"RES-FONT\");unicode-range:U+0400-045F}</style></helmet>")
            bundle = td / "Fixture-Standalone.html"
            bundle.write_text("<!DOCTYPE html><html><head><title>Bundled Page</title></head><body><script>/*loader*/</script>"
                              "<script type=\"__bundler/manifest\">" + json.dumps({"RES-FONT": {"mime": "font/woff2", "compressed": True,
                                                                                               "data": base64.b64encode(font).decode()},
                                                                                  "RES-IMG": {"mime": "image/png", "compressed": False, "data": img}})
                              + "</script><script type=\"__bundler/template\">" + json.dumps(tpl_bundled).replace("</", "<\\u002F")
                              + "</script></body></html>", encoding="utf-8")
            info = ingest(bundle)
            chk("C01", "綁包 __bundler/template 解包 → dc 標記 + 資源冊;.dc.html 直接認得", info["kind"] == "dc_bundle" and "<x-dc>" in info["text"]
                and len(info["resources"]) == 2 and ingest(dc)["kind"] == "dc")
            c1 = convert(dc, out, propose=True)
            d1 = c1["irdoc"]
            chk("C02", "token → TemplateSSOT 下一版候選(--propose 只寫到 OUT;registry 不動)", d1["tokens"]["ssot_next"] and (out / "CANDIDATE_TemplateSSOT.json").exists()
                and (c1["dir"] / "CANDIDATE_TemplateSSOT.json").exists() and not (HERE / f"VIA_UI_TemplateSSOT_{d1['tokens']['ssot_next']}.json").exists(),
                d1["tokens"])
            chk("C03", "版面區塊:header · left · tabs · pane · footer 都判出", {"header", "left", "tabs", "pane", "footer"} <= set(d1["regions"]), d1["regions"])
            chk("C04", "元件盤點(卡 / 燈 / 圖 / 表)+ 結構簽章去重", all(k in d1["components"] for k in ("card", "lamp", "log"))
                and d1["component_library"]["unique"] >= 5 and (c1["dir"] / "COMPONENTS.json").exists(), d1["components"])
            sl = d1["slots"]
            chk("C05", "槽位:純量 · 清單(含巢狀 ssot.lines)· 條件 · 事件都抽到", {"runStat", "engN"} <= set(sl["scalars"]) and "ssot.lines" in sl["lists"]
                and {"isT1", "isCat"} <= set(sl["conds"]) and "logs" in sl["lists"] and [p["id"] for p in d1["pages"]] == ["isT1", "isCat", "isEnd"])
            root = _fixture_root(td, stale_h=50)
            with contextlib.redirect_stdout(io.StringIO()):
                r = sync(dc, out, root=root, bk=bk)
            fh = Path(r["outputs"]["faithful"]["file"]).read_text(encoding="utf-8")
            chk("C06", "活資料對接:runStat / engN / logs / vKpis / valRows / gallery / ssot 都對上 VIA 來源",
                r["scalars"]["runStat"]["view"] == "status_line" and r["scalars"]["engN"]["view"] == "engines#count"
                and all(r["lists"][k]["view"] for k in ("logs", "vKpis", "valRows", "gallery", "ssot", "tabs")) and "X-COL" in fh and "py:e2" in fh)
            un = {u["slot"] for u in r["unmapped"]}
            chk("C07", "未對接槽照實列出並標 NODATA;模板示範資料一個字都不用", {"mysteryN", "widgets", "valRows[].flux"} <= un
                and "DEMO-FAKE-WIDGET" not in fh and "via-nodata" in fh and r["lamp"] == "YELLOW", sorted(un))
            th = r["theme"]
            chk("C08", "燈號對映:四態對到模板類名 ok/wn/er/in、色相最近的 --up/--dn/--am、卡片修飾 up/dn/am",
                th["lamp_cls"] == {"GREEN": "ok", "YELLOW": "wn", "RED": "er", "NODATA": "in"} and th["lamp_hex"]["RED"] == "#9e2b25"
                and th["lamp_hex"]["GREEN"] == "#3c6660" and th["acc"]["YELLOW"] == "am" and th["acc"]["RED"] == "up", th)
            chk("C09", "表格自動對接:欄位同義(v.id→code)+ 衍生欄(rowCs 斑馬 · badge 燈 · onCs)", r["lists"]["valRows"]["fields"].get("id") == "code"
                and r["lists"]["valRows"]["fields"].get("rowCs") == "derived:cs" and "background:var(--zebra);" in fh and "via-lamp-YELLOW" in fh)
            chk("C10", "圖槽:tally 畫成內嵌 SVG,系列色取模板色票", "<svg class=\"via-svg\"" in fh.replace("'", "\"") and th["lamp_hex"]["RED"] in fh)
            pages = r["outputs"]["faithful"]["pages"]
            chk("C11", "分頁:兄弟 sc-if → 分頁;分類頁依來源數複製;tabs 清單帶 data-via-tab;深連結 + 鍵盤 JS 在",
                pages[0] == "isT1" and sum(1 for p in pages if p.startswith("isCat-")) >= 3 and 'data-via-tab="isT1"' in fh
                and "ArrowRight" in fh and "#tab=" in fh, pages)
            chk("C11", "版面自動調整:設計者按 5 個樣本寫死的 repeat(5,…) 格線跟著活資料列數改", "repeat(5," not in fh.split("<body>", 1)[-1].split("via-report")[0]
                and r["outputs"]["faithful"]["stats"].get("grid_adapted", 0) >= 1, r["outputs"]["faithful"]["stats"])
            chk("C12", "SYNCHRONIZER 登記:via.sync.state.v2 預置腳本在頁頭", PRIOR.STATE_KEY in fh and "via-tpl-fixture_ui" in fh.lower())
            srcs = {s["id"]: s for s in r["sources"]}
            chk("C13", "新鮮度:50h 前的 TEST 標 STALE(燈不改色)", srcs["test"]["stale"] and srcs["test"]["lamp"] == "YELLOW" and not srcs["panorama"]["stale"]
                and "via-stale" in fh)
            chk("C14", "錯誤邊界:壞 JSON = UNREADABLE、沒檔 = ABSENT,都 NODATA,頁照出", srcs["vdf_chain"]["state"] == "UNREADABLE"
                and srcs["dflock"]["state"] == "ABSENT" and srcs["dflock"]["lamp"] == "NODATA" and len(fh) > 1000)
            chk("C15", "手機護欄:img/svg 限寬、寬表內捲、≤480px 16px 邊距(--pad 覆寫)", "--pad:16px" in fh and "max-width:100%" in fh and ".via-tw{overflow-x:auto" in fh)
            chk("C16", "深色 token 推導 + 切換鈕(模板寫死色不動 → PARTIAL)", ":root[data-theme=dark]{--bg:" in fh and "id='via-theme'" in fh
                and derive_dark({"bg": "#ffffff"})["bg"] < "#333333")
            chk("C17", "對比檢:燈色 / 底逐項量,不足只標", len(r["contrast"]) >= 4 and all("ratio" in c for c in r["contrast"]))
            chk("C18", "列印 CSS:分頁攤開、浮動列藏、100vh 容器自動高", "@media print{" in fh and ".app-root{height:auto!important}" in fh)
            chk("C19", "篩選 + 黏頂表頭:清單列掛 data-via-row、篩選框、th sticky", 'data-via-row="logs"' in fh and "id='via-filter'" in fh
                and "table th{position:sticky" in fh)
            chk("C20", "離線:外部 link / script / @import / 遠端 url() / 外部 img 全拿掉;0 違規", r["outputs"]["faithful"]["offline"]["violations"] == 0
                and r["outputs"]["skeleton"]["offline"]["violations"] == 0 and "googleapis" not in fh and "example.invalid" not in fh,
                r["outputs"]["faithful"]["offline"])
            with contextlib.redirect_stdout(io.StringIO()):
                rb = sync(bundle, out, root=root, bk=bk)
            bh = Path(rb["outputs"]["faithful"]["file"]).read_text(encoding="utf-8")
            chk("C20", "綁包:拉丁字型內嵌(data:font)、非拉丁子集丟、大圖換 VIA 印章", "data:font/woff2;base64," in bh
                and rb["offline_rewrites"].get("fonts_dropped", 0) >= 1 and rb["offline_rewrites"].get("images_replaced_by_via_stamp", 0) >= 1
                and rb["outputs"]["faithful"]["offline"]["violations"] == 0, rb["offline_rewrites"])
            chk("C20", "效能預算量得出(bytes · 元素數 · 燈)", r["outputs"]["faithful"]["perf"]["bytes"] > 0 and r["outputs"]["faithful"]["perf"]["lamp"] in LAMPS)
            chk("C21", "鎖:沒鎖 = NONE;lock --apply 後 OK;模板一改 = DRIFT(黃)", r["lock"]["state"] == "NONE")
            lk = lock(dc, apply_=True, out=out)
            dc.write_text(FIXTURE_DC.replace("--pad:12px", "--pad:14px"), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                r2 = sync(dc, out, root=root, bk=bk)
            chk("C21", "改模板後 sync 標 DRIFT 並列問題", lk["state"] == "LOCKED" and r2["lock"]["state"] == "DRIFT" and any("DRIFT" in p for p in r2["problems"]))
            chk("C22", "出處:引擎版號 · UTC · 模板 sha · IR sha · 來源 sha 內嵌 JSON", 'id="via-provenance"' in fh.replace("'", '"') and d1["sha"] in fh
                and d1["ir_sha"] in fh and ENGINE in fh)
            dd = ir_diff(d1, convert(dc, out)["irdoc"])
            chk("C23", "版本差異:只改 --pad → tokens_changed 只有 pad", dd["tokens_changed"] == {"pad": ["12px", "14px"]} and not dd["slots_added"]
                and not dd["same"], dd)
            chk("C23", "同一份比自己 = same", ir_diff(d1, d1)["same"])
            chk("C24", "往返冪等:同步頁再轉一次 token 不變、區塊角色都在", r["outputs"]["faithful"]["roundtrip"]["tokens_same"]
                and r["outputs"]["faithful"]["roundtrip"]["regions_same"], r["outputs"]["faithful"]["roundtrip"])
            inbox = td / "inbox"
            logs = []
            w0 = watch(inbox, out, once=True, root=root, bk=bk, log=logs.append)
            (inbox / "VIA HTML Universal UI.dc.html").write_text(FIXTURE_DC, encoding="utf-8")
            w1 = watch(inbox, out, once=True, root=root, bk=bk, log=logs.append)
            w2 = watch(inbox, out, once=True, root=root, bk=bk, log=logs.append)
            p = root / "VIA_Reports/panorama/monitor_latest.json"
            p.write_text(json.dumps({"verdict": "RED", "rows": []}), encoding="utf-8")
            os.utime(p, (time.time() + 5, time.time() + 5))
            w3 = watch(inbox, out, once=True, root=root, bk=bk, log=logs.append)
            chk("C25", "投放夾:空 = NODATA;放進去自動同步;沒變不重出;資料一動重出", w0["state"] == "NODATA" and w1["state"] == "SYNCED"
                and w2["state"] == "UNCHANGED" and w3["state"] == "SYNCED" and w3["data_changed"]
                and (out / "synced" / "VIA_HTML_Universal_UI" / "VIA_UI_VIA_HTML_Universal_UI_latest.html").exists(), [w0["state"], w1["state"], w2["state"], w3["state"]])
            plain = td / "plain.html"
            plain.write_text("<html><head><style>:root{--bg:#fff;--text:#111}.card{border:1px solid #ccc}</style>"
                             "<script src='https://cdn.example.invalid/plotly.js'></script></head><body><main class='content'><div class='card'>x</div></main></body></html>",
                             encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                rp = sync(plain, out, root=root, bk=bk)
            sk = Path(rp["outputs"]["skeleton"]["file"]).read_text(encoding="utf-8")
            chk("C03", "沒有槽的一般 .html → 骨架模式:模板角色類名(card)套 VIA 版面,外部 script 拿掉", rp["mode"] == "skeleton" and "class=\"card" in sk.replace("'", '"')
                and "cdn.example.invalid" not in sk and rp["outputs"]["skeleton"]["offline"]["violations"] == 0)
            chk("C06", "總表 SYNC_INDEX 列出每份模板", (out / "SYNC_INDEX_latest.html").exists() and "plain.html" in (out / "SYNC_INDEX_latest.html").read_text(encoding="utf-8"))
        finally:
            PRIOR.OUT = keep_prior_out
            globals()["OUT"] = keep_out
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            deny = main(["sync"])
        chk("C00", "不經 VCGC 就拒跑(新動詞)", deny == 2)
    finally:
        if keep is not None:
            os.environ["VIA_FROM_VCGC"] = keep
    body = Path(__file__).read_text(encoding="utf-8")
    chk("C00", "帶加速器橋 · VIA_FROM_VCGC 標記 · 不匯入 TA-Lib", "[VIA:ACCEL-BRIDGE" in body and "VIA_FROM_VCGC" in body
        and not re.search(r"^\s*(import|from)\s+" + "ta" + r"lib\b", body, re.M))
    missing = [t["id"] for t in bk.get("top25") or [] if t["status"] in ("IMPLEMENTED", "PARTIAL") and not (ids.get(t["check"]) and all(ids[t["check"]]))]
    chk("C00", "TOP25 交叉核對:每個 IMPLEMENTED / PARTIAL 的檢號都在本自測且全過", not missing, missing)
    n_ok = sum(results)
    print(f"[模板轉接 {VERSION}] 自測 {n_ok}/{len(results)} {'PASS' if all(results) else 'FAIL'}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
