#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL241_TemplateAdapter v0100 — 模板轉接器:任何設計規格自適應對接 → VIA_UI_TemplateSSOT 下一版(零 token 換模板)

操作員 2026-09-28 R26:「把 SYNCHRONIZER 內涵所有可能規格自動自適應式對接 節省最多 TOKEN 彈性更換模板」
「這個模組要有所有規格自適應式選擇 LAYOUT 多元自動化優化 規格 圖的規格等」。
樣式唯一的尺仍是 VIA_UI_TemplateSSOT(L05);本支只把外部設計檔**轉成它的下一版候選**,換不換由操作員按(寫檔要 apply):

  ① 讀:W3C 設計 token JSON(DTCG `$value` / Style Dictionary `value` / Tokens Studio 巢狀)· 平鋪 JSON · CSS `:root` 變數
        (.css 或 .html 裡的 <style>;Claude Design / 任何模板匯出的頁都行)· 另一份 VIA TemplateSSOT;別名 `{a.b}` / `var(--x)` 會解開
  ② 對:VIA_UI_TemplateAdapter_Map 尾版(同義字冊,只增不減)→ SSOT 鍵;值型別要合(顏色 / 長度 / 字型 / 數字);深色主題的鍵預設不收
  ③ 驗:顏色正規化成 #rrggbb;rem/em → px;WCAG 對比(文字 / 底 ≥ 4.5、強調色上字 ≥ 4.5)不合只標黃,不代改色(不發明)
  ④ LAYOUT 多元自動優化:左面板寬 × 表頭高 × 桌機字 × 手機字 × 斷點 逐組打分(硬條件:字 ≥ 10px、表頭放得下一行字、
     1366 寬時主區放得下表格最少欄寬、手機一定上下疊、桌機不疊);設計檔給的值是錨(偏離要扣分);取最佳,前三組列給人看
  ⑤ 圖的規格:圖高上下限依 768 / 1080 螢幕扣表頭算;資料系列色(chart-1…)收成 chart.series;刻度沿用冊值
  ⑥ 出:VIA_Reports/template_adapter/ 候選冊 + 差異 + 預覽頁(新值色票 · 對照表 · 版型打分 · 對比 · 誰會跟著換 / 誰釘死 v0100)
     apply = 把候選寫成 registry/VIA_UI_TemplateSSOT_v<下一號>.json(新版號,舊版不動);之後格式鎖要操作員 template --lock
  ⑦ 呈現對接套件(操作員:「新的功能近來也可快速對接呈現方式 顏色 設計 LAYOUT 參數應該是自動與他對接 平常就是最簡單淺色小規格自動優化」):
     新功能不寫樣式,只呼叫 spec() / css() / chart() / page(標題, 內容, module=…):值全從 TemplateSSOT 尾版來,冊缺的鍵用內建
     最簡淺色小規格補(DEFAULTS);LAYOUT 自動優化目標 = 小字(桌機 11 · 手機 10)緊湊;page(module=…) 同時把新功能登記進
     SYNCHRONIZER(via.sync.state.v2 模組冊,借 VRN_ENG089 PRESEED 契約,信封其他欄位原樣保留)。
只收 VCGC 呼叫(CLI);函式可由任何引擎匯入。零網路。用法:
  python3 CGC_MDL241_TemplateAdapter_v0100.py plan [--in <檔或夾>] [--theme light|dark] | apply | consumers | spec | demo | --selftest
  (--in 省略 = VIA_Reports/template_adapter/inbox 裡最新的一個檔)
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

import colorsys
import copy
import hashlib
import html as _html
import itertools
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "template_adapter"
INBOX = OUT / "inbox"
ENGINE = Path(__file__).stem
SSOT_GLOB = "VIA_UI_TemplateSSOT_v*.json"
MAP_GLOB = "VIA_UI_TemplateAdapter_Map_v*.json"
SCREENS = {"laptop": (1366, 768), "desktop": (1920, 1080), "phone": (390, 844)}
PROFILE = {"table_cols": 6, "min_col_px": 110, "chart_rows_px": 200}
GRID = {"panel_w_px": (220, 240, 260, 280, 300, 320), "header_h_px": (34, 38, 42, 48), "font_pc_px": (10, 11, 12, 13, 14),
        "font_mobile_px": (10, 11, 12), "breakpoint_px": (640, 768, 900, 1024)}
STEP = {"panel_w_px": 20, "header_h_px": 4, "font_pc_px": 1, "font_mobile_px": 1, "breakpoint_px": 128}


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = sorted(folder.glob(pattern), key=_vnum)
    return hits[-1] if hits else None


def _json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, TypeError):
        return None


# ---------------------------------------------------------------- ① read any source into flat {path: raw value}

def _walk_tokens(node, prefix, out: dict, order: list):
    if isinstance(node, dict):
        val = node.get("$value", node.get("value")) if ("$value" in node or ("value" in node and not isinstance(node.get("value"), dict))) else None
        if val is not None and not isinstance(val, (dict, list)):
            out[prefix] = val
            order.append(prefix)
            return
        for k, v in node.items():
            if str(k).startswith("$") or k in ("type", "description", "comment", "extensions"):
                continue
            _walk_tokens(v, f"{prefix}.{k}" if prefix else str(k), out, order)
    elif isinstance(node, (str, int, float)) and prefix:
        out[prefix] = node
        order.append(prefix)


CSS_VAR_RX = re.compile(r"--([A-Za-z0-9_\-]+)\s*:\s*([^;}{]+)")


def read_source(path: Path) -> dict:
    """Any supported file → {"kind", "tokens": {path: value}, "order": [...], "ssot": dict|None, "sha"}."""
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8-sig", errors="replace")
    sha = hashlib.sha256(raw).hexdigest()[:16]
    if Path(path).suffix.lower() in (".css", ".html", ".htm", ".scss"):
        body = text
        if Path(path).suffix.lower() in (".html", ".htm"):
            body = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", text, flags=re.S | re.I))
        toks, order = {}, []
        for block_sel, block in re.findall(r"([^{}]*)\{([^{}]*)\}", body):
            dark = re.search(r"dark", block_sel, re.I) is not None
            for k, v in CSS_VAR_RX.findall(block):
                key = ("dark." if dark else "") + k.strip()
                if key not in toks:
                    toks[key] = v.strip()
                    order.append(key)
        return {"kind": "css", "tokens": toks, "order": order, "ssot": None, "sha": sha}
    data = json.loads(text)
    if isinstance(data, dict) and str(data.get("schema", "")).startswith("VIA_UI_TEMPLATE_SSOT"):
        return {"kind": "via_ssot", "tokens": {}, "order": [], "ssot": data, "sha": sha}
    toks, order = {}, []
    _walk_tokens(data, "", toks, order)
    return {"kind": "json_tokens", "tokens": toks, "order": order, "ssot": None, "sha": sha}


def resolve_aliases(toks: dict) -> dict:
    """{a.b} (DTCG) and var(--x) (CSS) references, up to five hops; an unresolved alias stays raw (and fails type checks)."""
    norm = {normalize(k, []): k for k in toks}
    out = dict(toks)
    for _ in range(5):
        changed = False
        for k, v in out.items():
            if not isinstance(v, str):
                continue
            m = re.fullmatch(r"\{([^{}]+)\}", v.strip()) or re.fullmatch(r"var\(\s*--([A-Za-z0-9_\-]+)\s*(?:,[^)]*)?\)", v.strip())
            if not m:
                continue
            ref = m.group(1)
            src = ref if ref in out else norm.get(normalize(ref, []))
            if src and src != k and not (isinstance(out[src], str) and ("{" in out[src] or "var(" in out[src])):
                out[k] = out[src]
                changed = True
        if not changed:
            break
    return out


# ---------------------------------------------------------------- ② values

NAMED = {"white": "#ffffff", "black": "#000000", "transparent": None}


def parse_color(v) -> str | None:
    if not isinstance(v, str):
        return None
    s = v.strip().lower()
    if s in NAMED:
        return NAMED[s]
    m = re.fullmatch(r"#([0-9a-f]{3,8})", s)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h[:3])
        elif len(h) in (6, 8):
            h = h[:6]
        else:
            return None
        return "#" + h
    m = re.fullmatch(r"rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)(?:[\s,/]+[\d.%]+)?\s*\)", s)
    if m:
        r, g, b = (max(0, min(255, round(float(x)))) for x in m.groups())
        return f"#{r:02x}{g:02x}{b:02x}"
    m = re.fullmatch(r"hsla?\(\s*([\d.]+)(?:deg)?[\s,]+([\d.]+)%[\s,]+([\d.]+)%(?:[\s,/]+[\d.%]+)?\s*\)", s)
    if m:
        h, sat, lig = float(m.group(1)) / 360, float(m.group(2)) / 100, float(m.group(3)) / 100
        r, g, b = colorsys.hls_to_rgb(h % 1, lig, sat)
        return "#" + "".join(f"{round(x * 255):02x}" for x in (r, g, b))
    return None


def parse_length(v) -> float | None:
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    if not isinstance(v, str):
        return None
    m = re.fullmatch(r"\s*(-?[\d.]+)\s*(px|rem|em)?\s*", v)
    if not m:
        return None
    n = float(m.group(1))
    return n * 16 if m.group(2) in ("rem", "em") else n


def parse_font(v) -> str | None:
    if not isinstance(v, str) or parse_color(v) or parse_length(v) is not None:
        return None
    s = v.strip()
    return s if re.search(r"[A-Za-z]", s) and len(s) < 200 else None


def parse_number(v) -> float | None:
    x = parse_length(v)
    return x if x is not None and 0 < x < 4 else None


PARSERS = {"color": parse_color, "length": parse_length, "font": parse_font, "number": parse_number}


def luminance(hexc: str) -> float:
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return round((la + 0.05) / (lb + 0.05), 2)


# ---------------------------------------------------------------- ③ map keys

def normalize(name: str, strip: list) -> str:
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", str(name)).lower()
    s = re.sub(r"[\s_./$]+", "-", s).strip("-")
    parts = [p for p in s.split("-") if p]
    while parts and parts[0] in strip and len(parts) > 1:
        parts = parts[1:]
    return "-".join(parts)


def map_tokens(toks: dict, order: list, book: dict, theme: str = "light") -> dict:
    strip = book.get("strip_prefixes") or []
    dark = set(book.get("dark_markers") or [])
    cands = []
    for path in order:
        segs = set(re.split(r"[\s_./$\-]+", path.lower()))
        is_dark = bool(segs & dark)
        if (theme == "light" and is_dark) or (theme == "dark" and not is_dark and any((set(re.split(r"[\s_./$\-]+", p.lower())) & dark) for p in order)):
            continue
        n = normalize(re.sub(r"(?i)(^|[._\-])(dark|night|inverse)(?=[._\-]|$)", r"\1", path), strip)
        cands.append((path, n))
    mapped, used = {}, set()
    for ent in book.get("keys") or []:
        best = None
        for idx, (path, n) in enumerate(cands):
            for syn in ent["syn"]:
                sn = normalize(syn, [])
                score = 3 if n == sn else (2 if n.endswith("-" + sn) else (1 if n.startswith(sn + "-") and n.count("-") <= sn.count("-") + 1 else 0))
                if not score:
                    continue
                val = PARSERS[ent["kind"]](toks[path])
                if val is None:
                    continue
                if best is None or score > best[0] or (score == best[0] and idx < best[1]):
                    best = (score, idx, path, val, syn)
        if best:
            mapped[ent["key"]] = {"from": best[2], "raw": toks[best[2]], "value": best[3], "via": best[4], "match": best[0]}
            used.add(best[2])
    ser = book.get("series") or {}
    series = []
    if ser.get("rx"):
        rx = re.compile(ser["rx"])
        for path, n in cands:
            m = rx.match(n)
            c = parse_color(toks[path]) if m else None
            if c:
                series.append((int(m.group(1)), path, c))
                used.add(path)
    if series:
        series.sort()
        mapped[ser["key"]] = {"from": ", ".join(p for _, p, _ in series), "raw": "", "value": [c for _, _, c in series], "via": "series", "match": 3}
    unmapped = [p for p, _ in cands if p not in used]
    return {"mapped": mapped, "unmapped": unmapped}


# ---------------------------------------------------------------- ④ layout optimisation · ⑤ chart spec

def optimise_layout(anchor: dict, profile: dict = PROFILE, screens: dict = SCREENS) -> dict:
    """Score every combination; hard rules first, then readability · main-area share · header fit · distance from anchors."""
    lw, lh = screens["laptop"]
    pw = screens["phone"][0]
    rows = []
    for combo in itertools.product(*(GRID[k] for k in GRID)):
        c = dict(zip(GRID, combo))
        scale = c["font_pc_px"] / 11
        main = lw - c["panel_w_px"]
        need = profile["table_cols"] * profile["min_col_px"] * scale
        why_not = []
        if c["font_mobile_px"] < 10 or c["font_pc_px"] < 10:
            why_not.append("字 < 10px")
        if c["font_mobile_px"] > c["font_pc_px"]:
            why_not.append("手機字比桌機大")
        if c["header_h_px"] < c["font_pc_px"] * 2.6:
            why_not.append("表頭放不下一行字")
        if main < need:
            why_not.append(f"1366 寬主區 {main}px < 表格 {round(need)}px")
        if not (pw < c["breakpoint_px"] < lw):
            why_not.append("斷點要讓手機疊、桌機不疊")
        if why_not:
            continue
        score = 0.0
        score -= abs(c["font_pc_px"] - 11) * 2 + abs(c["font_mobile_px"] - 10) * 1.5     # default = small, compact (operator R26)
        score += main / lw * 10
        score -= abs(c["header_h_px"] - c["font_pc_px"] * 3.3) / 4
        for k, v in c.items():
            a = anchor.get(k)
            if isinstance(a, (int, float)):
                score -= abs(v - a) / STEP[k] * (3.0 if anchor.get("_from_design", {}).get(k) else 1.0)
        rows.append({**c, "score": round(score, 2), "main_px_1366": main})
    rows.sort(key=lambda r: -r["score"])
    return {"best": rows[0] if rows else None, "top": rows[:3], "feasible": len(rows),
            "total": len(list(itertools.product(*(GRID[k] for k in GRID))))}


def chart_spec(header_h: int, screens: dict = SCREENS, profile: dict = PROFILE) -> dict:
    lo = max(240, round((screens["laptop"][1] - header_h - profile["chart_rows_px"]) * 0.75 / 10) * 10)
    hi = max(lo + 40, round((screens["desktop"][1] - header_h - profile["chart_rows_px"]) * 0.55 / 10) * 10)
    return {"chart_min_h_px": lo, "chart_max_h_px": hi}


# ---------------------------------------------------------------- ⑥ plan · apply

def _set(d: dict, dotted: str, value):
    head, _, tail_ = dotted.partition(".")
    if not tail_:
        d[head] = value
        return
    d.setdefault(head, {})
    _set(d[head], tail_, value)


def _get(d: dict, dotted: str):
    cur = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def consumers() -> dict:
    """Live tails that read the SSOT: follow = glob the newest version · pinned = name v0100 literally (will not follow)."""
    follow, pinned = [], []
    tails = {}
    for p in VIA.rglob("*.py"):
        sp = str(p)
        if "/VIA_Reports/" in sp or "/references/" in sp or "SCOPE_COPY" in sp:
            continue
        stem = re.sub(r"_v\d+$", "", p.stem)
        key = (str(p.parent), stem)
        if key not in tails or _vnum(p) > _vnum(tails[key]):
            tails[key] = p
    for p in sorted(tails.values()):
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if p.name == Path(__file__).name:
            continue
        if "VIA_UI_TemplateSSOT_v*" in t:
            follow.append(p.name)
        elif "VIA_UI_TemplateSSOT_v0100" in t:
            pinned.append(p.name)
    return {"follow": follow, "pinned": pinned}


def plan(src_path: Path, theme: str = "light", write: bool = True, base: dict | None = None, book: dict | None = None) -> dict:
    base_p = _newest(HERE, SSOT_GLOB)
    base = copy.deepcopy(base if base is not None else (_json(base_p) or {}))
    book = book if book is not None else (_json(_newest(HERE, MAP_GLOB)) or {})
    src = read_source(src_path)
    cand = copy.deepcopy(base)
    replaced, mapped, unmapped = {}, {}, []
    if src["ssot"] is not None:                                   # another VIA SSOT: take its values key by key (only keys it has)
        for sec in ("palette", "status", "font", "space", "radius", "layout", "dashboard", "chart"):
            for k, v in (src["ssot"].get(sec) or {}).items():
                dotted = f"{sec}.{k}"
                if _get(base, dotted) != v:
                    replaced[dotted] = _get(base, dotted)
                    _set(cand, dotted, v)
                mapped[dotted] = {"from": dotted, "raw": v, "value": v, "via": "via_ssot", "match": 3}
    else:
        toks = resolve_aliases(src["tokens"])
        m = map_tokens(toks, src["order"], book, theme)
        mapped, unmapped = m["mapped"], m["unmapped"]
        for dotted, hit in mapped.items():
            v = hit["value"]
            if dotted.endswith("_px") or dotted in ("radius.card", "radius.tab", "space.gap", "layout.max_width", "chart.axis_px"):
                v = round(v) if dotted.endswith("_px") or dotted == "chart.axis_px" else f"{round(v)}px"
            if _get(base, dotted) != v:
                replaced[dotted] = _get(base, dotted)
            _set(cand, dotted, v)
    dash = cand.get("dashboard") or {}
    design_keys = {k.split(".", 1)[1] for k in mapped if k.startswith("dashboard.")}
    anchor = {k: dash.get(k) for k in GRID}
    anchor["_from_design"] = {k: (k in design_keys) for k in GRID}
    lay = optimise_layout(anchor)
    if lay["best"]:
        for k in GRID:
            if dash.get(k) != lay["best"][k]:
                replaced.setdefault(f"dashboard.{k}", _get(base, f"dashboard.{k}"))
            _set(cand, f"dashboard.{k}", lay["best"][k])
    cs = chart_spec(int(_get(cand, "dashboard.header_h_px") or 38))
    for k, v in cs.items():
        if f"dashboard.{k}" in mapped:                             # the design said so: keep it, only flag if out of range
            continue
        if _get(cand, f"dashboard.{k}") != v:
            replaced.setdefault(f"dashboard.{k}", _get(base, f"dashboard.{k}"))
        _set(cand, f"dashboard.{k}", v)
    chart = cand.setdefault("chart", {})
    chart.setdefault("series", [(cand.get("status") or {}).get(k) for k in ("OK", "SKIP", "FAIL", "UNTESTED")])
    chart.setdefault("axis_px", max(9, int(_get(cand, "dashboard.font_pc_px") or 11) - 1))
    chart["tick_intervals"] = _get(cand, "dashboard.tick_intervals") or [1, 2, 2.5, 5, 10]
    warn = []
    pal = cand.get("palette") or {}
    for a, b, need, zh in (("text", "bg", 4.5, "文字 / 底"), ("text", "surface", 4.5, "文字 / 卡片"), ("accent_text", "accent", 4.5, "強調色上的字")):
        ca, cb = parse_color(pal.get(a)), parse_color(pal.get(b))
        if ca and cb and contrast(ca, cb) < need:
            warn.append(f"{zh} 對比 {contrast(ca, cb)} < {need}(WCAG AA)")
    for k, c in (cand.get("status") or {}).items():
        cc = parse_color(c)
        if cc and contrast(cc, "#ffffff") < 3:
            warn.append(f"燈色 {k} 在白底對比 {contrast(cc, '#ffffff')} < 3(燈號辨識)")
    nxt = f"v{(_vnum(base_p) if base_p else 99) + 1:04d}"
    cand["version"] = nxt
    cand["adapter"] = {"engine": ENGINE, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "source": str(src_path), "source_sha": src["sha"],
                       "source_kind": src["kind"], "theme": theme, "from_version": base.get("version"),
                       "replaced": replaced, "mapped": {k: {x: v[x] for x in ("from", "via", "match")} for k, v in mapped.items()},
                       "unmapped": unmapped[:200], "layout_top": lay["top"], "layout_feasible": f"{lay['feasible']}/{lay['total']}",
                       "contrast_warnings": warn}
    rep = {"engine": ENGINE, "ts": cand["adapter"]["ts"], "next_version": nxt, "base": base_p.name if base_p else None,
           "source": str(src_path), "source_kind": src["kind"], "source_sha": src["sha"], "mapped": len(mapped), "unmapped": len(unmapped),
           "changed": len(replaced), "layout": lay, "chart": cs, "warnings": warn, "consumers": consumers() if write else {},
           "state": "PLAN" if mapped else "NODATA"}
    if write:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "CANDIDATE_TemplateSSOT.json").write_text(json.dumps(cand, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (OUT / "PLAN_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        (OUT / "PREVIEW_latest.html").write_text(preview(base, cand, mapped, unmapped, lay, warn, rep), encoding="utf-8")
    rep["candidate"] = cand
    return rep


def apply(target_dir: Path = HERE) -> dict:
    cand = _json(OUT / "CANDIDATE_TemplateSSOT.json")
    rep = _json(OUT / "PLAN_latest.json")
    if not cand or not rep:
        return {"state": "NODATA", "why": "沒有候選(先 plan)"}
    base_p = _newest(target_dir, SSOT_GLOB)
    if base_p and rep.get("base") != base_p.name:
        return {"state": "STALE", "why": f"候選是對 {rep.get('base')} 做的,現在尾版是 {base_p.name}(重跑 plan)"}
    out = target_dir / f"VIA_UI_TemplateSSOT_{cand['version']}.json"
    if out.exists():
        return {"state": "EXISTS", "why": f"{out.name} 已在(版號只增;重跑 plan 會取下一號)"}
    out.write_text(json.dumps(cand, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"state": "WRITTEN", "file": str(out), "next": "格式鎖會變紅:確認頁面後跑 CGC_MDL238 template --lock 重鎖(操作員的手)"}


def preview(base: dict, cand: dict, mapped: dict, unmapped: list, lay: dict, warn: list, rep: dict) -> str:
    e = lambda x: _html.escape(str(x if x is not None else ""))
    pal, st, dash = cand.get("palette") or {}, cand.get("status") or {}, cand.get("dashboard") or {}
    sw = lambda c: f"<span style='display:inline-block;width:14px;height:14px;border:1px solid #999;vertical-align:middle;background:{e(c)}'></span>"
    rows = "".join(f"<tr><td>{e(k)}</td><td>{e(v['from'])}</td><td>{e(v['via'])}</td>"
                   f"<td>{sw(v['value']) if isinstance(v['value'], str) and str(v['value']).startswith('#') else ''} {e(v['value'])}</td>"
                   f"<td>{e(_get(base, k))}</td></tr>" for k, v in mapped.items())
    lays = "".join(f"<tr><td>{i + 1}</td>" + "".join(f"<td>{e(r[k])}</td>" for k in GRID) + f"<td>{e(r['main_px_1366'])}</td><td>{e(r['score'])}</td></tr>"
                   for i, r in enumerate(lay["top"]))
    series = "".join(sw(c) for c in (cand.get("chart") or {}).get("series") or [] if c)
    cons = rep.get("consumers") or {}
    lamps = "".join(f"<span style='margin-right:10px'>{sw(c)} {e(k)}</span>" for k, c in st.items())
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>模板轉接預覽</title><style>body{{margin:0;font-family:{e(dash.get('font_family'))};font-size:{e(dash.get('font_pc_px'))}px;"
            f"background:{e(dash.get('color_bg'))};color:{e(pal.get('text'))}}}.wrap{{display:flex;min-height:100vh}}"
            f"aside{{width:{e(dash.get('panel_w_px'))}px;background:{e(dash.get('color_panel_bg'))};border-right:1px solid {e(dash.get('color_border'))};padding:8px}}"
            f"main{{flex:1;padding:8px;min-width:0}}.hd{{height:{e(dash.get('header_h_px'))}px;display:flex;align-items:center;font-weight:bold;"
            f"border-bottom:1px solid {e(dash.get('color_border'))}}}table{{border-collapse:collapse;width:100%;margin:6px 0}}"
            f"td,th{{border:1px solid {e(dash.get('color_grid'))};padding:3px 6px;text-align:left}}.warn{{background:{e(dash.get('alert_bg'))};padding:6px}}"
            f"@media (max-width:{e(dash.get('breakpoint_px'))}px){{.wrap{{flex-direction:column}}aside{{width:auto}}body{{font-size:{e(dash.get('font_mobile_px'))}px}}}}"
            "</style></head><body><div class='wrap'>"
            f"<aside><div class='hd'>左面板 {e(dash.get('panel_w_px'))}px</div><p>來源:{e(rep['source_kind'])} · sha {e(rep['source_sha'])}</p>"
            f"<p>對上 {rep['mapped']} · 沒對上 {rep['unmapped']} · 會改 {rep['changed']} 個值</p><p>{lamps}</p><p>圖系列色 {series}</p></aside>"
            f"<main><div class='hd'>模板轉接預覽 · {e(rep['base'])} → {e(rep['next_version'])}(候選,未寫)</div>"
            + ("".join(f"<div class='warn'>{e(w)}</div>" for w in warn) or "<p>對比檢查:全過</p>")
            + f"<h3>對照(SSOT 鍵 ← 設計檔鍵)</h3><table><tr><th>SSOT 鍵</th><th>來源鍵</th><th>同義字</th><th>新值</th><th>舊值</th></tr>{rows}</table>"
            f"<h3>LAYOUT 自動優化(可行 {lay['feasible']}/{lay['total']} 組;前三)</h3><table><tr><th>#</th>"
            + "".join(f"<th>{e(k)}</th>" for k in GRID) + f"<th>1366 主區</th><th>分數</th></tr>{lays}</table>"
            f"<h3>圖規格</h3><p>高 {e(dash.get('chart_min_h_px'))}–{e(dash.get('chart_max_h_px'))}px · 軸字 {e((cand.get('chart') or {}).get('axis_px'))}px · "
            f"刻度 {e((cand.get('chart') or {}).get('tick_intervals'))}</p>"
            f"<h3>誰會跟著換</h3><p>跟隨尾版 {len(cons.get('follow') or [])} 支 · 釘死 v0100 {len(cons.get('pinned') or [])} 支(不會跟,要各自換版)"
            f":{e(', '.join((cons.get('pinned') or [])[:12]))}</p>"
            f"<h3>沒對上的鍵({len(unmapped)})</h3><p>{e(', '.join(unmapped[:80]))}</p></main></div></body></html>")



# ---------------------------------------------------------------- ⑦ presentation kit: new features dock here, zero styling of their own

DEFAULTS = {                                              # simplest light, small spec: only fills keys the SSOT lacks
    "palette": {"bg": "#ffffff", "surface": "#ffffff", "border": "#e5e7eb", "line": "#f1f5f9", "text": "#1f2937", "mut": "#94a3b8",
                "sub": "#475569", "accent": "#111827", "accent_text": "#ffffff", "warn_bg": "#fef9c3", "warn_border": "#fde047"},
    "status": {"OK": "#15803d", "FAIL": "#b91c1c", "SKIP": "#a16207", "UNTESTED": "#64748b"},
    "font": {"family": "system-ui, 'Segoe UI', 'Noto Sans TC', sans-serif", "line_height": 1.4},
    "radius": {"card": "6px", "tab": "5px"}, "space": {"gap": "6px"}, "layout": {"tap_min_px": 36},
    "dashboard": {"font_family": "system-ui, 'Segoe UI', 'Noto Sans TC', sans-serif", "font_pc_px": 11, "font_mobile_px": 10, "panel_w_px": 240,
                  "header_h_px": 36, "breakpoint_px": 768, "chart_min_h_px": 280, "chart_max_h_px": 380, "color_bg": "#ffffff",
                  "color_panel_bg": "#f8fafc", "color_border": "#e5e7eb", "color_grid": "#eef2f7", "alert_bg": "#fff7e6", "input_border": "#d1d5db",
                  "tick_intervals": [1, 2, 2.5, 5, 10]},
}
STATE_KEY, CHANNEL = "via.sync.state.v2", "via.sync.v2"


def _merge(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in extra.items():
        if isinstance(v, dict):
            out[k] = _merge(out.get(k) or {}, v) if isinstance(out.get(k), dict) or k not in out else out[k]
        elif k not in out or out[k] in (None, ""):
            out[k] = v
    return out


def spec(book: dict | None = None) -> dict:
    """The one presentation spec for any page: newest TemplateSSOT, gaps filled by DEFAULTS, layout checked (re-optimised only
    when the book's layout breaks a hard rule), chart spec derived. No engine should need a colour of its own."""
    book = book if book is not None else (_json(_newest(HERE, SSOT_GLOB)) or {})
    sp = _merge(DEFAULTS, {})
    sp = _merge(book, sp) if book else sp
    d = sp["dashboard"]
    anchor = {k: d.get(k) for k in GRID}
    anchor["_from_design"] = {k: True for k in GRID}
    lay = optimise_layout(anchor)
    feasible_now = lay["best"] is not None and all(lay["best"][k] == d.get(k) for k in GRID)
    if lay["best"] and not feasible_now and not any(all(r[k] == d.get(k) for k in GRID) for r in lay["top"]):
        for k in GRID:
            d[k] = lay["best"][k]
    sp["layout_check"] = "book" if feasible_now else "optimised"
    ch = sp.setdefault("chart", {})
    ch.setdefault("series", [c for c in (sp["status"].get("OK"), "#2563eb", sp["status"].get("SKIP"), "#7c3aed", sp["status"].get("FAIL"),
                                         "#0891b2", sp["status"].get("UNTESTED")) if c])
    ch.setdefault("axis_px", max(9, int(d["font_pc_px"]) - 1))
    ch.setdefault("tick_intervals", d.get("tick_intervals") or [1, 2, 2.5, 5, 10])
    ch.setdefault("min_h_px", d.get("chart_min_h_px"))
    ch.setdefault("max_h_px", d.get("chart_max_h_px"))
    return sp


def css(sp: dict | None = None) -> str:
    """Standard kit CSS (class names .via-*): shell with collapsible left panel, header, tabs, tables, lamps, cards, charts, mobile stack."""
    sp = sp or spec()
    p, st, d, r = sp["palette"], sp["status"], sp["dashboard"], sp.get("radius") or {}
    lamps = "".join(f".via-lamp.{k}{{background:{v}}}" for k, v in st.items())
    return (f":root{{--via-bg:{d['color_bg']};--via-panel:{d['color_panel_bg']};--via-border:{d['color_border']};--via-grid:{d['color_grid']};"
            f"--via-text:{p['text']};--via-sub:{p['sub']};--via-mut:{p['mut']};--via-accent:{p['accent']};--via-accent-text:{p['accent_text']};"
            f"--via-alert:{d['alert_bg']};--via-input:{d['input_border']};--via-pw:{d['panel_w_px']}px;--via-hh:{d['header_h_px']}px;"
            f"--via-fs:{d['font_pc_px']}px;--via-fs-m:{d['font_mobile_px']}px;--via-r:{r.get('card', '6px')};"
            f"--via-chart-min:{d['chart_min_h_px']}px;--via-chart-max:{d['chart_max_h_px']}px}}"
            f"*{{box-sizing:border-box}}body{{margin:0;background:var(--via-bg);color:var(--via-text);font-family:{d['font_family']};"
            f"font-size:var(--via-fs);line-height:{(sp.get('font') or {}).get('line_height', 1.4)}}}"
            ".via-wrap{display:flex;min-height:100vh}.via-side{width:var(--via-pw);flex:0 0 var(--via-pw);background:var(--via-panel);"
            "border-right:1px solid var(--via-border);padding:6px 8px}.via-side.collapsed{display:none}.via-main{flex:1;min-width:0;padding:6px 8px}"
            ".via-hd{height:var(--via-hh);display:flex;align-items:center;gap:8px;font-weight:600;border-bottom:1px solid var(--via-border)}"
            ".via-tabs{display:flex;flex-wrap:wrap;gap:4px;margin:6px 0}.via-tabs button{font:inherit;border:1px solid var(--via-border);"
            f"background:var(--via-bg);color:var(--via-text);border-radius:{r.get('tab', '5px')};padding:3px 8px;cursor:pointer}}"
            ".via-tabs button.on{background:var(--via-accent);color:var(--via-accent-text)}.via-pane{display:none}.via-pane.on{display:block}"
            "table.via{border-collapse:collapse;width:100%;margin:4px 0}table.via th,table.via td{border:1px solid var(--via-grid);padding:2px 6px;"
            "text-align:left;vertical-align:top}table.via th{background:var(--via-panel)}.via-note{color:var(--via-sub)}"
            ".via-card{border:1px solid var(--via-border);border-radius:var(--via-r);padding:6px 8px;margin:4px 0;background:var(--via-bg)}"
            ".via-warn{background:var(--via-alert);padding:4px 8px;border-radius:var(--via-r)}"
            ".via-lamp{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:4px;vertical-align:middle}" + lamps +
            ".via-chart{min-height:var(--via-chart-min);max-height:var(--via-chart-max);width:100%}"
            f"@media (max-width:{d['breakpoint_px']}px){{.via-wrap{{flex-direction:column}}.via-side{{width:auto;flex:none;border-right:0;"
            "border-bottom:1px solid var(--via-border)}body{font-size:var(--via-fs-m)}}")


def chart(n_series: int = 1, sp: dict | None = None) -> dict:
    """Chart spec for any new chart: colours cycle through the book's series, height clamps, ticks and axis font from the book."""
    sp = sp or spec()
    ch = sp["chart"]
    ser = [c for c in ch["series"] if c] or ["#2563eb"]
    return {"colors": [ser[i % len(ser)] for i in range(max(1, n_series))], "min_h_px": ch["min_h_px"], "max_h_px": ch["max_h_px"],
            "axis_px": ch["axis_px"], "tick_intervals": ch["tick_intervals"], "grid": sp["dashboard"]["color_grid"],
            "font_family": sp["dashboard"]["font_family"]}


def lamp(state: str, text: str = "") -> str:
    k = {"GREEN": "OK", "OK": "OK", "AMBER": "SKIP", "SKIP": "SKIP", "NODATA": "UNTESTED", "RED": "FAIL", "FAIL": "FAIL"}.get(str(state).upper(), "UNTESTED")
    return f"<span class='via-lamp {k}'></span>{_html.escape(str(text or state))}"


def _preseed(module: dict) -> str:
    """Register the feature in the SYNCHRONIZER module book (ENG089 PRESEED contract; other envelope fields untouched)."""
    hits = sorted((VIA / "functional modules" / "VRN").glob("VRN_ENG089_TemplateView_v*.py"), key=_vnum)
    if not hits:
        return ""
    try:
        import importlib.util
        sp_ = importlib.util.spec_from_file_location("VRN_ENG089_for_" + ENGINE, hits[-1])
        eng = importlib.util.module_from_spec(sp_)
        sys.modules[sp_.name] = eng
        sp_.loader.exec_module(eng)
        sync = (VIA / "VIA_HTML_UI" / "ui" / "VIA-SYNCHRONIZER-Standalone.html").read_text(encoding="utf-8")
        defaults = eng.default_modules(sync)
        js = eng.PRESEED_JS
    except Exception:                                       # no contract = no preseed; the page itself still renders
        return ""
    if "__MODULE__" not in js:
        return ""
    val = lambda v: json.dumps(v, ensure_ascii=False).replace("<", "\\u003c")
    js = js.replace("VRN_TEMPLATE_PRESEED", "VIA_KIT_PRESEED").replace("'VRN-TEMPLATE'", val(module.get("id", "via-kit")))
    for k, v in (("__KEY__", STATE_KEY), ("__MODULE__", module), ("__DEFAULTS__", defaults)):
        js = js.replace(k, val(v))
    return "<script>" + js + "</script>"


def page(title: str, body_html: str, side_html: str = "", module: dict | None = None, sp: dict | None = None) -> str:
    """A whole page for a new feature: kit CSS from the book + optional left panel + optional SYNCHRONIZER registration."""
    sp = sp or spec()
    mod = None
    if module:
        mod = {"type": "dashboard", "enabled": True, "pinned": False, "system": False, "note": "", **module}
    e = _html.escape
    side = f"<aside class='via-side' id='via-side'>{side_html}</aside>" if side_html else ""
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{e(title)}</title>{_preseed(mod) if mod else ''}<style>{css(sp)}</style></head><body><div class='via-wrap'>{side}"
            f"<main class='via-main'><div class='via-hd'>{e(title)}</div>{body_html}</main></div></body></html>")


def _inbox_latest() -> Path | None:
    if not INBOX.exists():
        return None
    files = [p for p in INBOX.iterdir() if p.is_file() and p.suffix.lower() in (".json", ".css", ".html", ".htm", ".scss")]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def _arg(args, name, default=""):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    verb = args[0] if args else "plan"
    if verb == "spec":
        sp = spec()
        print(json.dumps({k: sp[k] for k in ("palette", "status", "dashboard", "chart", "layout_check") if k in sp}, ensure_ascii=False, indent=1))
        return 0
    if verb == "demo":
        OUT.mkdir(parents=True, exist_ok=True)
        ch = chart(3)
        body = ("<div class='via-card'>" + lamp("GREEN", "範例:新功能 A 綠") + " · " + lamp("AMBER", "缺料 黃") + " · " + lamp("RED", "壞 紅") + "</div>"
                "<table class='via'><tr><th>項</th><th>值</th></tr><tr><td>圖系列色</td><td>" + " ".join(
                    f"<span class='via-lamp' style='background:{c}'></span>{c}" for c in ch["colors"]) + "</td></tr>"
                f"<tr><td>圖高</td><td>{ch['min_h_px']}–{ch['max_h_px']}px · 軸字 {ch['axis_px']}px</td></tr></table>")
        p = OUT / "KIT_DEMO_latest.html"
        p.write_text(page("新功能對接範例(呈現套件)", body, "<div class='via-note'>左面板(寬度來自冊)</div>",
                          module={"id": "via-kit-demo", "name": "呈現套件範例"}), encoding="utf-8")
        print(json.dumps({"page": str(p)}, ensure_ascii=False))
        return 0
    if verb == "consumers":
        print(json.dumps(consumers(), ensure_ascii=False, indent=1))
        return 0
    if verb == "apply":
        r = apply()
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["state"] == "WRITTEN" else 2
    if verb == "plan":
        src = Path(_arg(args, "--in")) if _arg(args, "--in") else _inbox_latest()
        if src and src.is_dir():
            src = max((p for p in src.iterdir() if p.is_file()), key=lambda p: p.stat().st_mtime, default=None)
        if not src or not src.exists():
            print(json.dumps({"state": "NODATA", "why": f"沒有設計檔(放進 {INBOX} 或 --in <檔>)"}, ensure_ascii=False))
            return 2
        r = plan(src, theme=_arg(args, "--theme", "light"))
        r.pop("candidate", None)
        b = r["layout"]["best"] or {}
        print(f"[模板轉接] {r['state']} · {r['base']} → {r['next_version']}(候選)· 對上 {r['mapped']} · 沒對上 {r['unmapped']} · 改 {r['changed']} 值"
              f" · LAYOUT 最佳 面板 {b.get('panel_w_px')} 表頭 {b.get('header_h_px')} 字 {b.get('font_pc_px')}/{b.get('font_mobile_px')} 斷點 {b.get('breakpoint_px')}"
              f" · 圖高 {r['chart']['chart_min_h_px']}–{r['chart']['chart_max_h_px']} · 對比警示 {len(r['warnings'])}"
              f" · 跟隨 {len(r['consumers'].get('follow') or [])} / 釘死 {len(r['consumers'].get('pinned') or [])}")
        print(f"  預覽 {OUT / 'PREVIEW_latest.html'}")
        return 0 if r["state"] == "PLAN" else 2
    print(__doc__)
    return 2


def selftest() -> int:
    import tempfile
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE} · 自測(夾具設計檔;不寫 registry)===")
    base = _json(_newest(HERE, SSOT_GLOB)) or {}
    book = _json(_newest(HERE, MAP_GLOB)) or {}
    chk("⓪ 對照冊與 SSOT 尾版都在", bool(base.get("dashboard")) and len(book.get("keys") or []) >= 30, f"{len(book.get('keys') or [])} 鍵")
    chk("① 顏色正規化:#abc · rgb() · hsl() · #rrggbbaa", parse_color("#abc") == "#aabbcc" and parse_color("rgb(21,128,61)") == "#15803d"
        and parse_color("hsl(0,100%,50%)") == "#ff0000" and parse_color("#11223344") == "#112233" and parse_color("12px") is None)
    chk("① 長度:rem → px;字型不收成顏色", parse_length("0.75rem") == 12 and parse_length("260px") == 260 and parse_font("#fff") is None
        and parse_font("'Inter', sans-serif") == "'Inter', sans-serif")
    with tempfile.TemporaryDirectory() as td:
        dt = Path(td) / "design.tokens.json"
        dt.write_text(json.dumps({"color": {"background": {"$value": "#fafafa"}, "foreground": {"$value": "#18181b"},
                                            "primary": {"$value": "{color.brand.600}"}, "brand": {"600": {"$value": "#4f46e5"}},
                                            "on-primary": {"$value": "#ffffff"},
                                            "status": {"success": {"$value": "rgb(22,163,74)"}, "danger": {"$value": "#dc2626"},
                                                       "warning": {"$value": "#d97706"}, "neutral": {"$value": "#6b7280"}},
                                            "chart": {"1": {"$value": "#2563eb"}, "2": {"$value": "#16a34a"}, "3": {"$value": "#f59e0b"}},
                                            "dark": {"background": {"$value": "#000000"}}},
                                  "font": {"family": {"$value": "'Inter', 'Noto Sans TC', sans-serif"}, "size": {"base": {"$value": "0.8125rem"}}},
                                  "layout": {"sidebar-width": {"$value": "280px"}, "header-height": {"$value": "44px"}}}), encoding="utf-8")
        r = plan(dt, write=False, base=base, book=book)
        c = r["candidate"]
        chk("② DTCG token(含別名 {color.brand.600})→ 配色 · 燈 · 字型全對上", c["palette"]["bg"] == "#fafafa" and c["palette"]["accent"] == "#4f46e5"
            and c["status"]["OK"] == "#16a34a" and c["status"]["FAIL"] == "#dc2626" and c["dashboard"]["font_family"].startswith("'Inter'"),
            f"對上 {r['mapped']}")
        chk("② 深色主題的鍵預設不收(dark.background 沒蓋掉淺色底)", c["dashboard"]["color_bg"] == "#fafafa")
        chk("⑤ 圖系列色 chart-1…3 依序收成 chart.series", c["chart"]["series"] == ["#2563eb", "#16a34a", "#f59e0b"])
        b = r["layout"]["best"]
        chk("④ LAYOUT 優化:設計給的面板 280 · 表頭 44 當錨(可行才留);硬條件全過", b and b["panel_w_px"] == 280 and b["header_h_px"] in (42, 48)
            and b["font_pc_px"] >= 10 and 390 < b["breakpoint_px"] < 1366, json.dumps({k: b[k] for k in GRID}) if b else "無解")
        chk("④ 前三組版型與可行數都列出", len(r["layout"]["top"]) == 3 and r["layout"]["feasible"] > 3, r["layout"]["feasible"])
        chk("⑤ 圖高依螢幕算且 min < max", c["dashboard"]["chart_min_h_px"] < c["dashboard"]["chart_max_h_px"], r["chart"])
        chk("⑥ 下一版號只增;舊值記在 adapter.replaced(只增不減)", c["version"] == f"v{_vnum(_newest(HERE, SSOT_GLOB)) + 1:04d}"
            and c["adapter"]["replaced"].get("palette.bg") == base["palette"]["bg"])
        css_file = Path(td) / "claude_design.html"
        css_file.write_text("<html><head><style>:root{--color-bg:#ffffff;--color-text:#111111;--color-success:#059669;--sidebar-width:17.5rem;"
                       "--radius-md:12px;--font-sans:'Geist',system-ui}\n@media (prefers-color-scheme:dark){:root{--color-bg:#000}}"
                       ".dark{--color-bg:#0b0b0b}</style></head><body></body></html>", encoding="utf-8")
        r2 = plan(css_file, write=False, base=base, book=book)
        c2 = r2["candidate"]
        chk("① HTML 裡的 CSS :root 變數(Claude Design / 任何模板頁)也讀得到;.dark 區塊不收", c2["palette"]["bg"] == "#ffffff"
            and c2["status"]["OK"] == "#059669" and c2["radius"]["card"] == "12px" and c2["dashboard"]["panel_w_px"] == 280, f"對上 {r2['mapped']}")
        low = Path(td) / "low.json"
        low.write_text(json.dumps({"background": "#ffffff", "text": "#cccccc"}), encoding="utf-8")
        r3 = plan(low, write=False, base=base, book=book)
        chk("③ 對比不足只標黃,不代改色", any("文字 / 底" in w for w in r3["warnings"]) and r3["candidate"]["palette"]["text"] == "#cccccc")
        r4 = plan(_newest(HERE, SSOT_GLOB), write=False, base=base, book=book)
        chk("① 另一份 VIA SSOT 直接逐鍵收(同值 = 零改動)", r4["source_kind"] == "via_ssot" and not any(k.startswith("palette") for k in r4["candidate"]["adapter"]["replaced"]))
        global OUT
        keep = OUT
        OUT = Path(td) / "out"
        try:
            plan(dt, base=base, book=book)
            reg = Path(td) / "reg"
            reg.mkdir()
            (reg / _newest(HERE, SSOT_GLOB).name).write_text(json.dumps(base), encoding="utf-8")
            a = apply(reg)
            a2 = apply(reg)
            html_ok = (OUT / "PREVIEW_latest.html").exists() and "LAYOUT 自動優化" in (OUT / "PREVIEW_latest.html").read_text(encoding="utf-8")
        finally:
            OUT = keep
        chk("⑥ apply 寫新版號檔(舊版不動);再 apply 同號拒寫;預覽頁在", a["state"] == "WRITTEN" and a2["state"] in ("EXISTS", "STALE") and html_ok, a.get("file", a))
    cons = consumers()
    chk("⑥ 誰會跟著換:跟隨尾版 / 釘死 v0100 都量得出", len(cons["follow"]) >= 1, f"跟隨 {len(cons['follow'])} · 釘死 {len(cons['pinned'])}")
    sp = spec()
    chk("⑦ spec():冊值優先,冊缺的鍵由最簡淺色小規格補;圖規格齊", sp["palette"]["bg"] == base["palette"]["bg"]
        and sp["dashboard"]["font_pc_px"] == base["dashboard"]["font_pc_px"] and len(sp["chart"]["series"]) >= 4 and sp["chart"]["min_h_px"])
    bare = spec(book={})
    chk("⑦ 冊不在 → 全用最簡淺色小規格(白底 · 11/10px)", bare["dashboard"]["color_bg"] == "#ffffff" and bare["dashboard"]["font_pc_px"] == 11
        and bare["dashboard"]["font_mobile_px"] == 10)
    kit_css = css(sp)
    chk("⑦ css():值全出自 spec(冊的底色 · 面板寬 · 燈色都在)", base["dashboard"]["color_bg"] in kit_css and f"{sp['dashboard']['panel_w_px']}px" in kit_css
        and all(v in kit_css for v in base["status"].values()))
    pg = page("新功能", "<table class='via'><tr><td>x</td></tr></table>", "左", module={"id": "feat-x", "name": "功能 X"})
    chk("⑦ page():一行對接 = 套件樣式 + 左面板 + 登記進 SYNCHRONIZER(模組 id 在預置腳本裡)", "via-wrap" in pg and "feat-x" in pg
        and STATE_KEY in pg and "VIA_KIT_PRESEED" in pg)
    ch3 = chart(9)
    chk("⑦ chart():系列色循環不斷 · 圖高 · 軸字 · 刻度", len(ch3["colors"]) == 9 and ch3["min_h_px"] < ch3["max_h_px"] and ch3["axis_px"] >= 9)
    chk("④ 預設優化目標 = 小規格:無錨時選桌機 11 · 手機 10", optimise_layout({})["best"]["font_pc_px"] == 11
        and optimise_layout({})["best"]["font_mobile_px"] == 10)
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    try:
        chk("不經 VCGC 就拒跑", main(["plan"]) == 2)
    finally:
        if keep is not None:
            os.environ["VIA_FROM_VCGC"] = keep
    ok = all(results)
    print(f"  [計] {len(results)} 檢 OK {sum(results)} · FAIL {len(results) - sum(results)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
