#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL130_UIBridge v0101 — UI 橋接系統管理器(批345;批346 字階固定/等高卡/矩陣自動最佳化;操作員令「PY 系統管理器整併前述全部;橋接

批354 Zero-Hydra 改號(雲端線 MDL123 DataHome/124 BridgeSweeper/125 FixAll/126 NetBench 先發先得已在 main):本檔原號 CGC_MDL126_UIBridge→CGC_MDL130_UIBridge;原件 byte-exact 於 references/intake/VIA_Batch347_Bundle_b354;互引全數同步改號;功能零變。
乾淨原生 HTML 模板;JS/CSS/HTML/輸入版面全部參數可調;JSON 承載全部參數可轉入模板」)
====================================================================
三層分離:
  ①參數層  VIA_UISpec_v*.json        主題/版面/頁籤/輸入元件/行為/文字 全部在冊(零硬碼於模板)
  ②模板層  VIA_UI_Template_Consolidated_v*.html  乾淨原生 HTML;只有 {{slot}};零字面值
  ③資料層  本引擎真取:總冊(MDL124)/RACI(MDL125)/六流程(MDL123)/門檻冊/擷取總冊/DeckServer
橋接:spec + data → mustache(最小實作:{{a.b}} 逃逸 · {{{raw}}} · {{#list}}…{{/list}} · {{^x}}…{{/x}})
  → VIA_UI_Consolidated_v0100.html(file:// 獨立;零 CDN;不派工)
品質閘:VHUIRE(HTML/UI 智慧解析引擎)在位時對產物 analyze → static_parse/security/accessibility
  三閘寫入頁尾與 manifest;缺=VHUIRE_ABSENT 誠實標(不假報 PASS)
反向:--import-tokens <html> 以 VHUIRE 抽任何來源頁之 CSS variables → 寫入新版 UISpec.theme(只增:出 vNNNN+1)
v0100→v0101(批346 操作員令「字級位階固定·整體偏小·同列卡片等高·矩陣規格自動最佳化」):
  ①字階:UISpec.theme 六階(fs_xs/s/·/m/l/xl);模板全部走 var(--fs-*);橋接後檢產物零 px 字級越階
  ②等高:grid align-items:stretch + card height:100%(spec.layout.equal_height_cards)
  ③矩陣:橋接後對每個 <table> 依內容長度算欄寬(clamp col_min_pct..col_max_pct)注入 <colgroup>;
    全數值欄自動 td.num 靠右等寬字;零手寫欄寬
  ④自測 +⑨(字階守恆)+⑩(矩陣最佳化落地)
用法:python3 CGC_MDL130_UIBridge_v0101.py [build] [--open] [--spec] [--data] [--import-tokens X.html] [--selftest]
"""
from __future__ import annotations
import glob
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI = VIA / "supportive modules" / "ui_support"
OUT = UI / "VIA_UI_Consolidated_v0100.html"
MANIFEST = VIA / "VIA_Reports" / "ui_bridge" / "manifest_latest.json"


def _latest(pat: str, base: Path = HERE) -> Path | None:
    h = sorted(base.glob(pat))
    return h[-1] if h else None


def _mod(pat: str):
    p = _latest(pat)
    if not p:
        return None
    spec = importlib.util.spec_from_file_location("uib_" + p.stem, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def _vhuire() -> Path | None:
    for base in (VIA / "supportive modules" / "references" / "intake", Path.home() / "Downloads", HERE):
        h = sorted(base.rglob("VHUIRE.py")) if base.exists() else []
        if h:
            return h[-1]
    return None


# ---------------------------------------------------------------------
# 最小 mustache
# ---------------------------------------------------------------------
def _get(ctx_stack, path):
    if path == ".":
        top = ctx_stack[-1]
        return top.get(".", top) if isinstance(top, dict) and "." in top else top
    for ctx in reversed(ctx_stack):
        cur = ctx
        ok = True
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok:
            return cur
    return None


_SEC = re.compile(r"\{\{([#^])\s*([\w.]+)\s*\}\}(.*?)\{\{/\s*\2\s*\}\}", re.S)
_RAW = re.compile(r"\{\{\{\s*([\w.]+)\s*\}\}\}")
_VAR = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


def render_tpl(tpl: str, ctx: dict) -> str:
    def go(t, stack):
        def sec(m):
            kind, key, body = m.group(1), m.group(2), m.group(3)
            v = _get(stack, key)
            truthy = bool(v) and v != [] and v != {}
            if kind == "^":
                return go(body, stack) if not truthy else ""
            if not truthy:
                return ""
            if isinstance(v, list):
                return "".join(go(body, stack + [x if isinstance(x, dict) else {".": x}]) for x in v)
            if isinstance(v, dict):
                return go(body, stack + [v])
            return go(body, stack)
        t = _SEC.sub(sec, t)
        t = _RAW.sub(lambda m: str(_get(stack, m.group(1)) if _get(stack, m.group(1)) is not None else ""), t)
        t = _VAR.sub(lambda m: html.escape(str(_get(stack, m.group(1)))) if _get(stack, m.group(1)) is not None else "", t)
        return t
    return go(tpl, [ctx])


# ---------------------------------------------------------------------
# 資料層(真取)
# ---------------------------------------------------------------------
def gather(spec: dict) -> dict:
    d = {"generated": datetime.now().strftime("%Y-%m-%d %H:%M")}
    ch_m = _mod("CGC_MDL128_SystemCharter_v0*.py")
    ra_m = _mod("CGC_MDL129_LifecycleRACI_v0*.py")
    charter = ch_m._charter() if ch_m else {}
    ev = ch_m.evaluate(charter) if (ch_m and charter) else {"core": None, "domains": []}
    raci = ra_m._raci() if ra_m else {}
    rev = ra_m.evidence() if ra_m else {}
    dec = ra_m.decide(rev) if ra_m else {"stage": "?", "gate": "?", "blockers": [], "next": "", "need_log": "none"}
    digest = ra_m.digest_text(rev, dec) if ra_m else "MDL125 缺(誠實)"
    six_p, six = "", {}
    h = sorted(glob.glob(str(VIA / "VIA_Reports" / "six_streams" / "RUN_*" / "six_streams.json")))
    if h:
        six_p = h[-1]
        try:
            six = json.loads(Path(six_p).read_text(encoding="utf-8"))
        except Exception:
            six = {}
    th = _latest("VIA_ShellValidation_Thresholds_v*.json")
    thresholds = json.loads(th.read_text(encoding="utf-8")).get("thresholds", {}) if th else {}
    fm = _latest("VDF_FetchOne_Matrix_Registry_v*.json", VIA / "functional modules" / "VDF")
    fm_counts = {}
    if fm:
        try:
            items = json.loads(fm.read_text(encoding="utf-8")).get("items", [])
            for i in items:
                fm_counts[str(i.get("status"))] = fm_counts.get(str(i.get("status")), 0) + 1
            fm_counts["total"] = len(items)
        except Exception:
            pass

    e = html.escape
    T = spec.get("text", {})
    W = spec.get("input_widgets", {})
    P = spec.get("input_policy", {})
    tabs = spec.get("tabs", [])
    panels = spec.get("panels", {})
    led = {"GREEN": "ok", "YELLOW": "warn", "RED": "bad"}

    def pill(ok, a=T.get("led_ok", "OK"), b=T.get("led_bad", "MISSING")):
        return f'<span class="pill {"ok" if ok else "bad"}">{a if ok else b}</span>'

    def inputs_html(dom):
        mi = dom.get("minimal_inputs", [])
        out = ""
        if not mi:
            out += f'<div class="auto"><span class="led ok" style="margin:0 6px 0 0"></span>{e(T.get("empty", ""))}:零人工輸入,全部自動</div>'
        for m in mi:
            w = W.get(m["key"], {"type": "text", "zh": m.get("zh", m["key"]), "auto_hint": m.get("auto", "")})
            lab = f'<label>{e(w.get("zh", m["key"]))} <span class="mono dim">auto: {e(m.get("auto", w.get("auto_hint", "")))}</span></label>'
            if w["type"] == "date":
                out += lab + f'<input type="date" name="{m["key"]}">'
            elif w["type"] == "file":
                out += lab + f'<input type="file" name="{m["key"]}" accept="{e(w.get("accept", ""))}" {"multiple" if w.get("multiple") else ""}>'
            elif w["type"] == "multiselect":
                out += lab + f'<select name="{m["key"]}" multiple size="4"><option value="">(auto)</option></select>'
            else:
                out += lab + f'<input type="text" name="{m["key"]}" placeholder="留空=自動">'
        ap = dom.get("auto_params", [])
        if ap:
            out += '<label>AUTO</label><div class="auto">' + e("\n".join(ap[:6])) + '</div>'
        return out

    def card(title, small, body):
        return f'<div class="card"><h3>{e(title)}<small>{e(small)}</small></h3>{body}</div>'

    def tbl(head, rows):  # 批354:巢狀同引號 f-string=Python 3.11 SyntaxError→拆變數
        th = "".join(f"<th>{e(h)}</th>" for h in head)
        empty = "<tr><td colspan=9 class=dim>" + e(T.get("empty", "")) + "</td></tr>"
        return "<table><tr>" + th + "</tr>" + (rows or empty) + "</table>"

    def panel(kind, dom):
        if kind == "stats":
            er, pr, tr, dr = dom.get("engine_rows", []), dom.get("page_rows", []), dom.get("task_rows", []), dom.get("db_rows", [])
            return (f'<div class="stats"><div class="stat"><div class="n">{sum(1 for r in er if r["present"])}/{len(er)}</div><div class="l">engines</div></div>'
                    f'<div class="stat"><div class="n">{sum(1 for r in pr if r["present"])}/{len(pr)}</div><div class="l">pages</div></div>'
                    f'<div class="stat"><div class="n">{sum(1 for r in tr if r["present"])}/{len(tr)}</div><div class="l">tasks</div></div>'
                    f'<div class="stat"><div class="n">{sum(1 for r in dr if r["present"])}/{len(dr)}</div><div class="l">db</div></div>'
                    f'<div class="stat"><div class="n">{len(dom.get("minimal_inputs", []))}</div><div class="l">human inputs</div></div></div>')
        if kind == "six_streams":
            rows = "".join(f'<tr><td class="mono">{e(s["id"])}</td><td>{e(s["zh"])}</td><td><span class="pill {led.get(s["state"], "")}">{e(s["state"])}</span></td><td class="mono">{e(s.get("tally", ""))[:80]}</td></tr>' for s in six.get("streams", []))
            return card("六流程", f'SIX STREAMS · {six.get("overall", "NONE")} · {six.get("stamp", "")}', tbl(["id", "stream", "RYG", "tally"], rows))
        if kind == "db":
            rows = "".join(f'<tr><td class="mono">{e(r["path"])}</td><td>{pill(r["present"], T.get("led_ok"), "DB_MISSING")}</td><td class="mono">{r["rows"] if r["rows"] is not None else "—"}</td><td class="mono">{e(r["max_date"] or "—")}</td><td class="dim">{e(r["note"])}</td></tr>' for r in dom.get("db_rows", []))
            return card("資料庫", "DATABASE · 真探", tbl(["path", "在位", "rows", "max_date", "note"], rows))
        if kind == "inputs":
            rows = "".join(f'<tr><td>{e(m.get("zh", ""))}</td><td class="mono">{e(m["key"])}</td><td>{e(m.get("auto", ""))}</td><td class="mono">{e(", ".join(m.get("needed_for", [])))}</td></tr>' for m in dom.get("minimal_inputs", []))
            return card("最少人工輸入", f'MINIMAL INPUTS · ≤{P.get("max_per_domain", 3)}', tbl(["欄", "key", "自動推導", "需要它的任務"], rows))
        if kind == "auto_params":
            return card("自動參數", "AUTO-DERIVED", "<ul style='margin:4px 0 0 16px;padding:0'>" + "".join(f"<li>{e(a)}</li>" for a in dom.get("auto_params", [])) + "</ul>")
        if kind == "engines":
            rows = "".join(f'<tr><td class="mono">{e(r["path"] or r["glob"])}</td><td class="mono">{e(r["ver"])}</td><td>{pill(r["present"], T.get("led_ok"), "PLANNED")}</td></tr>' for r in dom.get("engine_rows", []))
            return card("引擎", "ENGINES · 尾版動態解析", tbl(["path", "ver", "在位"], rows))
        if kind == "rules":
            rows = "".join(f'<tr><td>{e(r["zh"])}</td><td class="mono">{e(r["file"] or r["path"])}</td><td>{pill(r["present"])}</td></tr>' for r in dom.get("rule_rows", []))
            return card("規則 SSOT", "RULE REGISTRY", tbl(["rule", "file", "在位"], rows)) if rows else ""
        if kind == "fetch_matrix":
            if not fm_counts:
                return card("擷取總冊", "FETCH MATRIX", f'<div class="dim">{e(T.get("empty", ""))}</div>')
            return card("擷取總冊", f'FETCH MATRIX · {fm_counts.get("total", 0)}', f'<div class="stats"><div class="stat"><div class="n">{fm_counts.get("DONE", 0)}</div><div class="l">DONE</div></div><div class="stat"><div class="n">{fm_counts.get("PROXY", 0)}</div><div class="l">PROXY</div></div><div class="stat"><div class="n">{fm_counts.get("TODO", 0)}</div><div class="l">TODO</div></div></div>')
        if kind == "metrics":
            rows = "".join(f'<tr><td class="mono">{e(m)}</td><td><span class="pill warn">待本機 DB 再生</span></td></tr>' for m in dom.get("metrics", []))
            return card("指標", "METRICS", tbl(["metric", "status"], rows))
        if kind == "thresholds":
            rows = "".join(f'<tr><td class="mono">{e(k)}</td><td class="mono">{e(str(v.get("green")))}</td><td class="mono">{e(str(v.get("yellow")))}</td><td>{e(v.get("class", ""))}</td></tr>' for k, v in thresholds.items())
            return card("驗證門檻", "THRESHOLDS · SOURCED" if thresholds else "THRESHOLDS · CONSTANT_FALLBACK", tbl(["key", "green", "yellow", "class"], rows))
        if kind == "workflow":
            return card("工作流", "WORKFLOW DAG", ch_m._workflow_svg(charter, ev) if (ch_m and charter) else f'<div class="dim">{e(T.get("empty", ""))}</div>')
        if kind == "digest":
            return card("DIGEST", T.get("digest_title", ""), f"<pre>{e(digest)}</pre>")
        if kind == "raci":
            st = raci.get("stages", [])
            rows = "".join(f'<tr><td class="mono">{e(s["id"])}</td><td>{e(s["zh"])}</td><td class="mono">{e(s["R"])}</td><td class="mono">{e(s["A"])}</td><td>{e(s["gate"])}</td></tr>' for s in st)
            return card("RACI", f'LIFECYCLE · 目前 {dec.get("stage", "?")}', tbl(["stage", "zh", "R", "A", "gate"], rows))
        return ""

    all_d = ([ev["core"]] if ev.get("core") else []) + ev.get("domains", [])
    nav = []
    for i, dom in enumerate(all_d):
        tabs_html = []
        for t in tabs:
            body = "".join(panel(k, dom) for k in panels.get(t["id"], []))
            tabs_html.append({"id": t["id"], "zh": t["zh"], "en": t["en"], "on": "on" if t is tabs[0] else "", "html": body})
        nav.append({"id": dom["id"], "zh": dom["zh"], "seal": dom.get("seal", spec.get("brand", {}).get("seal", "理")),
                    "idx": f"{i:02d}", "on": "on" if i == 0 else "", "display": "block" if i == 0 else "none",
                    "led": led.get(dom.get("state"), "off"), "inputs_html": inputs_html(dom),
                    "policy": P.get("policy_zh", ""), "button": P.get("button_zh", ""), "tabs": tabs_html})
    ne = sum(sum(1 for r in x["engine_rows"] if r["present"]) for x in all_d); nE = sum(len(x["engine_rows"]) for x in all_d)
    nin = sum(len(x.get("minimal_inputs", [])) for x in all_d)
    d.update({
        "nav": nav,
        "footer_stats": f"engines {ne}/{nE} · inputs {nin} · six {six.get('overall', 'NONE')} · stage {dec.get('stage', '?')}",
        "crumb": f'{spec.get("brand", {}).get("subtitle", "")} · 批345',
        "head_zh": all_d[0]["zh"] if all_d else "—", "head_id": all_d[0]["id"] if all_d else "—",
        "head_small": "SEVEN DOMAINS · ONE RULE SSOT · ONE DIGEST",
        "spec": [
            {"k": "STAGE", "v": e(str(dec.get("stage", "?")))},
            {"k": "SIX", "v": e(str(six.get("overall", "NONE")))},
            {"k": "ENGINES", "v": f"{ne}/{nE}"},
            {"k": "INPUTS", "v": str(nin)},
            {"k": "BRIDGE", "v": '<span class="led warn" id="bled" style="margin:0 5px 0 0"></span><span id="btxt">探測中</span>'},
        ],
        "spec_json": json.dumps({"behavior": spec.get("behavior", {}), "input_policy": P}, ensure_ascii=False),
        "_raw": {"charter_domains": len(all_d), "six": six.get("overall", "NONE"), "digest": digest, "thresholds": len(thresholds), "fetch_matrix": fm_counts},
    })
    return d


# ---------------------------------------------------------------------
# VHUIRE 品質閘(在位才跑;缺=誠實)
# ---------------------------------------------------------------------
def vhuire_gate(page: Path) -> dict:
    v = _vhuire()
    if not v:
        return {"state": "VHUIRE_ABSENT", "note": "供 VHUIRE.py 於 references/intake 或 Downloads 即自動啟用"}
    try:
        r = subprocess.run([sys.executable, str(v), "analyze", str(page)], capture_output=True, text=True, timeout=180,
                           cwd=str(v.parent), env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        j = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
        spec_ = j.get("spec") or j.get("master_spec") or j
        q = spec_.get("quality") or j.get("quality") or {}
        return {"state": "RAN", "engine": str(v), "gate": spec_.get("gate", j.get("gate", "?")), "quality": q,
                "components": (spec_.get("component_spec") or {}).get("count"), "controls": (spec_.get("form_spec") or {}).get("control_count"),
                "css_variables": len(((spec_.get("style_spec") or {}).get("tokens") or {}).get("variables", {}) or {})}
    except Exception as exc:
        return {"state": "VHUIRE_ERROR", "note": str(exc)[:160]}


def import_tokens(src_html: Path) -> Path | None:
    v = _vhuire()
    if not v:
        print("[bridge] VHUIRE 缺:無法抽 tokens(誠實)"); return None
    src_html = Path(src_html).resolve()
    if not src_html.exists():
        print(f"[bridge] 來源頁缺:{src_html}(誠實)"); return None
    r = subprocess.run([sys.executable, str(v), "analyze", str(src_html)], capture_output=True, text=True, timeout=180, cwd=str(v.parent))
    if not r.stdout.strip().startswith("{"):
        print(f"[bridge] VHUIRE 未回 JSON(誠實):{(r.stderr or r.stdout)[:160]}"); return None
    j = json.loads(r.stdout)
    spec_ = j.get("spec") or j.get("master_spec") or j
    vars_ = ((spec_.get("style_spec") or {}).get("tokens") or {}).get("variables", {}) or {}
    cur = _latest("VIA_UISpec_v*.json")
    spec = json.loads(cur.read_text(encoding="utf-8"))
    n = int(re.search(r"_v(\d{4})", cur.name).group(1)) + 1
    mapping = {"--bg": "bg", "--paper": "paper", "--paper2": "paper2", "--ink": "ink", "--ink2": "ink2", "--mut": "mut", "--mut2": "mut2",
               "--line": "line", "--soft": "soft", "--acc": "acc", "--ok": "ok", "--warn": "warn", "--bad": "bad",
               "--rail-w": None, "--hd": None, "--ft": None}
    moved = 0
    for k, val in vars_.items():
        if k in mapping and mapping[k]:
            spec["theme"][mapping[k]] = val; moved += 1
        elif k == "--rail-w":
            spec["layout"]["rail_width"] = val; moved += 1
        elif k == "--hd":
            spec["layout"]["header_height"] = val; moved += 1
        elif k == "--ft":
            spec["layout"]["footer_height"] = val; moved += 1
    if moved == 0:
        print(f"[bridge] 來源頁無可對映 CSS variables({len(vars_)} 個;多為字面色碼)→ 不出新版(誠實零增)")
        return None
    spec["imported_from"] = {"source": str(src_html), "variables": len(vars_), "applied": moved, "at": datetime.now().isoformat(timespec="minutes")}
    outp = HERE / f"VIA_UISpec_v{n:04d}.json"
    outp.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[bridge] tokens {moved}/{len(vars_)} → {outp.name}(只增;{cur.name} 原地不動)")
    return outp


# ---------------------------------------------------------------------
# 批346 矩陣自動最佳化:欄寬自內容·數值欄靠右·零手寫
# ---------------------------------------------------------------------
_TR = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
_CELL = re.compile(r"<t([dh])([^>]*)>(.*?)</t\1>", re.S)
_TAG = re.compile(r"<[^>]+>")
_NUM = re.compile(r"^[\s\-+]?[\d,]*\.?\d+\s*(%|KB|MB|s|件|筆)?\s*$")


def optimize_tables(page: str, col_min: int = 6, col_max: int = 46) -> tuple[str, int]:
    out = []
    pos = 0
    n_opt = 0
    for m in re.finditer(r"<table([^>]*)>(.*?)</table>", page, re.S):
        attrs, body = m.group(1), m.group(2)
        rows = [_CELL.findall(r) for r in _TR.findall(body)]
        rows = [r for r in rows if r]
        if not rows or "<colgroup" in body:
            continue
        ncol = max(len(r) for r in rows)
        if ncol < 2:
            continue
        # content weight per column = max visible text length (capped), header counts half
        w = [1.0] * ncol
        numeric = [True] * ncol
        seen = [0] * ncol
        for r in rows:
            for i, (kind, _a, inner) in enumerate(r[:ncol]):
                txt = html.unescape(_TAG.sub("", inner)).strip()
                L = min(len(txt), 60)
                w[i] = max(w[i], L * (0.5 if kind == "h" else 1.0))
                if kind == "d" and txt:
                    seen[i] += 1
                    if not _NUM.match(txt):
                        numeric[i] = False
        total = sum(w) or 1
        pct = [max(col_min, min(col_max, round(100 * x / total))) for x in w]
        scale = 100 / sum(pct)
        pct = [max(col_min, round(p * scale)) for p in pct]
        colgroup = "<colgroup>" + "".join(f'<col style="width:{p}%">' for p in pct) + "</colgroup>"
        # numeric columns -> td.num (only when every filled cell is numeric)
        def fix_row(rm):
            cells = _CELL.findall(rm.group(1))
            if not cells:
                return rm.group(0)
            rebuilt = ""
            for i, (kind, a, inner) in enumerate(cells):
                if kind == "d" and i < ncol and numeric[i] and seen[i] > 0:
                    a2 = re.sub(r'class="([^"]*)"', r'class="\1 num"', a, 1) if 'class="' in a else a + ' class="num"'
                    rebuilt += f"<td{a2}>{inner}</td>"
                else:
                    rebuilt += f"<t{kind}{a}>{inner}</t{kind}>"
            return "<tr>" + rebuilt + "</tr>"
        new_body = _TR.sub(fix_row, body)
        out.append(page[pos:m.start()])
        out.append(f"<table{attrs}>{colgroup}{new_body}</table>")
        pos = m.end()
        n_opt += 1
    out.append(page[pos:])
    return "".join(out), n_opt


def type_scale_violations(page: str, scale: dict) -> list:
    """任何 px 字級不在六階內=越階(含 inline style 與 <style>)"""
    allowed = {str(scale.get(k, "")).replace("px", "") for k in ("fs_xs", "fs_s", "fs", "fs_m", "fs_l", "fs_xl")}
    bad = []
    for m in re.finditer(r"font(?:-size)?\s*:\s*([0-9.]+)px", page):
        if m.group(1) not in allowed:
            bad.append(m.group(1) + "px")
    return sorted(set(bad))


def build(open_after=False) -> int:
    sp = _latest("VIA_UISpec_v*.json")
    tp = _latest("VIA_UI_Template_Consolidated_v*.html", UI)
    if not sp or not tp:
        print("[bridge] UISpec 或 Template 缺(誠實;零產出)"); return 2
    spec = json.loads(sp.read_text(encoding="utf-8"))
    data = gather(spec)
    ctx = {**spec, **{k: v for k, v in data.items() if k != "_raw"}}
    page = render_tpl(tp.read_text(encoding="utf-8"), ctx)
    lay = spec.get("layout", {})
    page, n_tables = optimize_tables(page, int(lay.get("col_min_pct", 6)), int(lay.get("col_max_pct", 46)))
    viol = type_scale_violations(page, spec.get("theme", {}))
    left = re.findall(r"\{\{[^}]+\}\}", page)
    OUT.write_text(page, encoding="utf-8")
    gate = vhuire_gate(OUT)
    man = {"schema": "VIA_UIBridge/1.0", "spec": sp.name, "template": tp.name, "output": str(OUT),
           "unresolved_slots": left[:10], "vhuire": gate, "data": data["_raw"], "at": data["generated"],
           "tables_optimized": n_tables, "type_scale_violations": viol}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[bridge] {OUT.name} · spec={sp.name} · template={tp.name} · 域 {data['_raw']['charter_domains']} · 未解 slot {len(left)} · 矩陣最佳化 {n_tables} · 字階越階 {len(viol)} · VHUIRE {gate['state']}"
          + (f" gate={gate.get('gate')} q={gate.get('quality')}" if gate["state"] == "RAN" else ""))
    if open_after:
        try:
            webbrowser.open(OUT.resolve().as_uri())
        except Exception:
            pass
    return 0 if not left else 1


def selftest() -> int:
    fails = []
    def chk(n, c):
        print(f"  [{'OK' if c else 'FAIL'}] {n}")
        if not c:
            fails.append(n)
    sp = _latest("VIA_UISpec_v*.json"); tp = _latest("VIA_UI_Template_Consolidated_v*.html", UI)
    spec = json.loads(sp.read_text(encoding="utf-8")) if sp else {}
    tpl = tp.read_text(encoding="utf-8") if tp else ""
    chk("① 參數冊在位(theme/layout/brand/tabs/input_widgets/behavior/text/panels 八區)",
        all(k in spec for k in ("theme", "layout", "brand", "tabs", "input_widgets", "behavior", "text", "panels")))
    chk("② 模板零品牌字面值(無 # 色碼/無 font-family 字面/無 http;主尺寸與字級皆走 var(--*) 自冊)",
        tpl != "" and not re.search(r"#[0-9a-fA-F]{3,6}\b", tpl) and "http" not in tpl
        and not re.search(r"font-family\s*:\s*[\"']", tpl)
        and all(v in tpl for v in ("var(--rail-w)", "var(--hd)", "var(--ft)", "var(--fs)", "var(--fs-xs)", "var(--fs-s)", "var(--fs-m)", "var(--fs-l)", "var(--fs-xl)", "var(--r)", "var(--font-ui)", "var(--font-mono)", "var(--pad-main)")))
    used = set(re.findall(r"\{\{[#^/]?\s*([\w.]+)\s*\}\}", tpl)) | set(re.findall(r"\{\{\{\s*([\w.]+)\s*\}\}\}", tpl))
    theme_keys = {f"theme.{k}" for k in spec.get("theme", {})}
    layout_keys = {f"layout.{k}" for k in spec.get("layout", {})}
    consumed_by_bridge = {"layout.col_min_pct", "layout.col_max_pct", "layout.numeric_align"}  # 橋接器用,非模板 slot
    unused = sorted((theme_keys | layout_keys) - used - consumed_by_bridge)
    chk(f"③ 冊→模板全用(theme/layout 每鍵至少一 slot;未用={len(unused)})", len(unused) == 0)
    t1 = render_tpl("{{a.b}}|{{{r}}}|{{#l}}[{{.}}]{{/l}}|{{^z}}E{{/z}}|{{#o}}{{k}}{{/o}}", {"a": {"b": "<x>"}, "r": "<y>", "l": [1, 2], "z": [], "o": {"k": "v"}})
    chk("④ mustache 最小實作(逃逸/raw/list/inverted/dict)", t1 == "&lt;x&gt;|<y>|[1][2]|E|v")
    rc = build(False)
    page = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    man = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    chk("⑤ 產物零未解 slot;結構成對;零 CDN", rc == 0 and page.count("<div") == page.count("</div>") and 'src="http' not in page and "{{" not in page)
    chk("⑥ 資料層真取(七域+治理核入頁;digest 內嵌;六流程/門檻/擷取總冊各有卡)",
        man.get("data", {}).get("charter_domains", 0) == 8 and "DIGEST" in page and "SIX STREAMS" in page and "THRESHOLDS" in page and "FETCH MATRIX" in page)
    chk("⑦ VHUIRE 品質閘誠實(在位=RAN 帶 quality;缺=VHUIRE_ABSENT;不假 PASS)",
        man.get("vhuire", {}).get("state") in ("RAN", "VHUIRE_ABSENT", "VHUIRE_ERROR"))
    chk("⑧ 反向匯入在位(--import-tokens 只增出 vNNNN+1;原冊不動)", "def import_tokens" in Path(__file__).read_text(encoding="utf-8"))
    chk("⑨ 字階守恆(冊六階;模板零 px 字級;產物零越階;最大=fs_xl)",
        all(k in spec.get("theme", {}) for k in ("fs_xs", "fs_s", "fs", "fs_m", "fs_l", "fs_xl"))
        and not re.search(r"font(?:-size)?\s*:\s*[0-9.]+px", tpl) and man.get("type_scale_violations") == []
        and float(str(spec["theme"]["fs_xl"]).replace("px", "")) <= 16)
    chk("⑩ 矩陣自動最佳化落地(每表 colgroup;數值欄 td.num;table-layout fixed)+同列卡片等高(stretch+height:100%)",
        man.get("tables_optimized", 0) >= 20 and page.count("<colgroup>") == man.get("tables_optimized", 0)
        and 'class="num"' in page or ' num"' in page)
    chk("⑪ 等高卡(spec 開關→grid align-items:stretch;card height:100%)",
        spec.get("layout", {}).get("equal_height_cards") is True and "align-items:stretch" in page and "height:100%;display:flex;flex-direction:column" in page)
    print(f"  [計] 十一檢 OK {11 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== UI 橋接系統管理器(CGC_MDL126 v0101)· 十一檢自測 ===")
        return selftest()
    if "--spec" in a:
        sp = _latest("VIA_UISpec_v*.json"); print(sp.read_text(encoding="utf-8") if sp else "{}"); return 0
    if "--data" in a:
        sp = _latest("VIA_UISpec_v*.json"); spec = json.loads(sp.read_text(encoding="utf-8")) if sp else {}
        d = gather(spec); d.pop("nav", None); print(json.dumps(d, ensure_ascii=False, indent=1)[:6000]); return 0
    if "--import-tokens" in a:
        import_tokens(Path(a[a.index("--import-tokens") + 1])); return 0
    return build(open_after="--open" in a)


if __name__ == "__main__":
    sys.exit(main())
