#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL238_OperatorConsole v0101 — 操作台接上 VCGC 資料中介 + HTML U/I SYNCHRONIZER(同一把鎖,模板骨架零改動)

操作員 2026-09-28 R25:「VCGC 統合 HTML U/I 展現方式可透過 HTML U/I SYNCHORIZER 交互整合一切」。v0100 → v0101:
  ① 資料中介進操作台(CGC_MDL239 尾版,只讀、預設乾跑):
       總覽 +3 燈:VCGC 資料中介(路由幾張表 · 近期要料帳)· VRN 讀 VDF 經中介(繞道燈)· VDF 建庫計畫(VCGC→VDF)
       引擎頁 + 路由表與要料帳;驗證頁 + 繞道明細;輸出頁 + 建庫計畫(缺 / 舊的表排哪個 VDF 項;GATED = 同意閘由操作員開)
  ② SYNCHRONIZER 交互整合(VIA_HTML_UI 標準協定 via.sync.state.v2 / via.sync.v2):
       活頁 <head> 後預置本台模組(借 VRN_ENG089 尾版 PRESEED 契約;狀態信封其他欄位原樣保留)並廣播 via-state-v2;
       dock:把 synchronizer 與中央 UI 的模板**複製**到 VIA_Reports/operator_console/ui/,前者掛 VIA_REGISTER_SYNC_ADDON 外掛
       (總覽燈 · 開操作台 · 開主控台藍圖 / 全景報告 · 下載總覽 JSON);模板原文一個位元不動(寫前後比 sha,拿掉插入段 = 原文)。
  ③ 格式鎖不動:新東西只進**有資料的活頁**(總覽列、各頁補段、預置腳本);模板(無資料)與 v0100 逐位元相同 → 骨架 sha 相同 → 鎖照舊 GREEN。
  ④ 指令字串跟著最新的 Invoke-VIA-OperatorConsole-v*.ps1(不再寫死 v0100)。
其餘照 v0100(thin tail;__getattr__ 轉接)。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。零網路。
用法:同 v0100(page / template / lock / paths / apply / summary / status / parquet / extract)+ dock · broker
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

import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL238_OperatorConsole"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
ENGINE = Path(__file__).stem
VIA = _PRIOR.VIA
_e = _PRIOR._e
_lamp = _PRIOR._lamp
UI_DIR = _PRIOR.OUT / "ui"
TEMPLATE_ROOT = VIA / "VIA_HTML_UI"
DOCK_ROLES = ("centralUI", "synchronizer")
STATE_KEY = "via.sync.state.v2"
CHANNEL = "via.sync.v2"
SYNC_MODULE = {"id": "vcgc-operator-console", "name": "VCGC 操作台", "type": "dashboard", "enabled": True, "pinned": True,
               "system": False, "note": "CGC_MDL238 v0101 · 總覽三色燈 · VCGC 資料中介 · VDF 建庫計畫 · 擷取"}
_V0100 = {k: getattr(_PRIOR, k) for k in ("collect", "overview", "page_html", "write_page")}
BUILD_LAMP = {"GREEN": "OK", "PLAN": "SKIP", "GATED": "SKIP", "NODATA": "SKIP", "AMBER": "SKIP", "ABSENT": "SKIP",
              "TIMEOUT": "FAIL", "RED": "FAIL"}


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def ps_script() -> str:
    hits = sorted(VIA.glob("Invoke-VIA-OperatorConsole-v*.ps1"), key=lambda p: p.name)
    return ".\\" + (hits[-1].name if hits else "Invoke-VIA-OperatorConsole-v0100.ps1")


# ---------------------------------------------------------------- ① VCGC data broker on the console

def broker_state(home_override: str | None = None) -> dict:
    b = _PRIOR.mod("CGC_MDL239_DataBroker")
    if b is None:
        return {"ok": False, "why": "CGC_MDL239 DataBroker 尾版不在", "routes": [], "unrouted": [], "bypass": {}, "build": {}, "ledger": []}
    rts = b.routes()
    led = b.REPORTS / "LEDGER.jsonl"
    ledger = []
    if led.exists():
        for x in led.read_text(encoding="utf-8").splitlines()[-30:]:
            try:
                ledger.append(json.loads(x))
            except ValueError:
                continue
    return {"ok": True, "why": "", "engine": b.ENGINE, "routes": rts, "unrouted": b.unrouted(rts=rts),
            "bypass": b.bypass(tables=[r["table"] for r in rts]), "build": b.build(home=home_override, rts=rts), "ledger": ledger}


def collect(home_override: str | None = None) -> dict:
    d = _V0100["collect"](home_override)
    ps = ps_script()
    for k in ("cmd_apply", "cmd_pick_dirs", "cmd_run_all"):
        d[k] = str(d.get(k, "")).replace(".\\Invoke-VIA-OperatorConsole-v0100.ps1", ps)
    d["broker"] = broker_state(home_override)
    d["sync_page"] = "ui/VIA-SYNCHRONIZER-Standalone.html"
    d["engine_v0101"] = ENGINE
    return d


def overview(d: dict) -> list:
    rows = _V0100["overview"](d)
    br = d.get("broker")
    if br is None:                                  # v0100-shaped data: v0100's answer, unchanged
        return rows
    if not br.get("ok"):
        rows.append(("VCGC 資料中介", "FAIL", br.get("why", ""), "p_eng"))
        return rows
    tally = {}
    for x in br["ledger"]:
        tally[x.get("state")] = tally.get(x.get("state"), 0) + 1
    rows.append(("VCGC 資料中介", "FAIL" if tally.get("RED") else "OK",
                 f"路由 {len(br['routes'])} 張表 · 表冊有而無路由 {len(br['unrouted'])} · 近帳 "
                 + (" · ".join(f"{k} {v}" for k, v in sorted(tally.items())) or "尚無要料"), "p_eng"))
    bp = br["bypass"]
    rows.append(("VRN 讀 VDF 經中介", "OK" if bp.get("state") == "GREEN" else "SKIP", bp.get("why", ""), "p_chk"))
    bd = br["build"]
    lamps = [BUILD_LAMP.get(x["state"], "SKIP") for x in bd.get("rows") or []]
    lamp = "UNTESTED" if not lamps else ("FAIL" if "FAIL" in lamps else ("OK" if set(lamps) == {"OK"} else "SKIP"))
    rows.append(("VDF 建庫計畫(VCGC→VDF)", lamp, " · ".join(f"{k} {v}" for k, v in sorted((bd.get("tally") or {}).items()))
                 + (" · 同意閘由操作員開(本台不代設)" if (bd.get("tally") or {}).get("GATED") else ""), "p_out"))
    return rows


# ---------------------------------------------------------------- ② SYNCHRONIZER: preseed + addon

_ENG = {"mod": None, "why": "", "tried": False}


def eng089():
    """VRN_ENG089 tail: the PRESEED contract, template check and DEFAULT_MODULES reader (borrowed, not rewritten)."""
    if not _ENG["tried"]:
        _ENG["tried"] = True
        hits = sorted((VIA / "functional modules" / "VRN").glob("VRN_ENG089_TemplateView_v*.py"), key=_vnum)
        if not hits:
            _ENG["why"] = "VRN_ENG089 尾版不在"
        else:
            try:
                sp = importlib.util.spec_from_file_location("VRN_ENG089_for_" + ENGINE, hits[-1])
                m = importlib.util.module_from_spec(sp)
                sys.modules[sp.name] = m
                sp.loader.exec_module(m)
                _ENG["mod"] = m
            except Exception as exc:
                _ENG["why"] = f"VRN_ENG089 載不動 {type(exc).__name__}"
    return _ENG["mod"]


def _jsval(v) -> str:
    return json.dumps(v, ensure_ascii=False).replace("<", "\\u003c")


def _mark(block: str, edge: str) -> str:
    return "<!-- VCGC-OPERATOR-CONSOLE:" + block + ":" + edge + " -->"


def preseed_js(defaults: list) -> str:
    eng = eng089()
    src = getattr(eng, "PRESEED_JS", "") if eng else ""
    if "__MODULE__" not in src or "__DEFAULTS__" not in src:
        raise ValueError("VRN_ENG089 尾版的 PRESEED_JS 不在或改版了(沒有 __MODULE__/__DEFAULTS__)")
    js = src.replace("VRN_TEMPLATE_PRESEED", "VOC_PRESEED").replace("'VRN-TEMPLATE'", "'VCGC-OPERATOR-CONSOLE'")
    for k, v in (("__KEY__", STATE_KEY), ("__MODULE__", SYNC_MODULE), ("__DEFAULTS__", defaults)):
        js = js.replace(k, _jsval(v))
    return js


BROADCAST_JS = r"""(function () {
  'use strict';
  try {
    if (window.VOC_PRESEED !== 'ADDED' || typeof BroadcastChannel !== 'function') return;
    var st = JSON.parse(localStorage.getItem(__KEY__));
    var bc = new BroadcastChannel(__CHANNEL__);
    bc.postMessage({ type: 'via-state-v2', originId: 'vcgc-operator-console-' + Math.random().toString(36).slice(2), state: st });
    bc.close();
    window.VOC_BROADCAST = true;
  } catch (e) { window.VOC_BROADCAST = false; }
})();"""

ADDON_JS = r"""(function () {
  'use strict';
  var MID = __MODULE_ID__, NAME = __MODULE_NAME__, P = null;
  try { P = JSON.parse(document.getElementById('voc-payload').textContent); } catch (e) { P = null; }
  var C = { OK: '#16a34a', SKIP: '#d97706', FAIL: '#dc2626', UNTESTED: '#94a3b8' };
  function mount(host, api) {
    host.replaceChildren(); host.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px;align-items:center';
    var t = document.createElement('strong'); t.textContent = NAME + ' · ' + ((P && P.built_at) || '—'); host.appendChild(t);
    ((P && P.rows) || []).forEach(function (r) {
      var s = document.createElement('span'); s.className = 'addon-chip voc-lamp'; s.title = r.text || '';
      var dot = document.createElement('span');
      dot.style.cssText = 'display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:4px;background:' + (C[r.lamp] || C.UNTESTED);
      s.appendChild(dot); s.appendChild(document.createTextNode(r.item)); host.appendChild(s);
    });
    ((P && P.links) || []).forEach(function (l) {
      var a = document.createElement('a'); a.href = l.href; a.target = '_blank'; a.rel = 'noopener'; a.className = 'btn'; a.textContent = l.label; host.appendChild(a);
    });
    var b = document.createElement('button'); b.type = 'button'; b.className = 'btn'; b.textContent = '下載總覽 JSON';
    b.addEventListener('click', function () { if (api && typeof api.download === 'function') api.download('VIA_OperatorConsole_overview.json', JSON.stringify(P, null, 2), 'application/json'); });
    host.appendChild(b);
    window.VOC_SYNC_MOUNTED = true;
  }
  function register(left) {
    if (typeof window.VIA_REGISTER_SYNC_ADDON === 'function') {
      var ok = false; try { ok = window.VIA_REGISTER_SYNC_ADDON({ id: MID, name: NAME, version: '0101', mount: mount }); } catch (e) { ok = false; }
      window.VOC_SYNC_REGISTERED = ok !== false; return;
    }
    if (left > 0) setTimeout(function () { register(left - 1); }, 50); else window.VOC_SYNC_REGISTERED = false;
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { register(200); }); else register(200);
})();"""


def _fill(js: str) -> str:
    for k, v in (("__KEY__", STATE_KEY), ("__CHANNEL__", CHANNEL), ("__MODULE_ID__", SYNC_MODULE["id"]),
                 ("__MODULE_NAME__", SYNC_MODULE["name"])):
        js = js.replace(k, _jsval(v))
    return js


def _pre_block(defaults: list) -> str:
    return (_mark("preseed", "BEGIN") + "\n<script>\n" + preseed_js(defaults) + "\n</script>\n<script>\n" + _fill(BROADCAST_JS)
            + "\n</script>\n" + _mark("preseed", "END"))


def inject(html: str, role: str, defaults: list, payload: dict | None) -> str:
    """Template text + inserted blocks (after <head>: preseed; before </body>: payload + addon). Nothing else changes."""
    head = re.search(r"<head\b[^>]*>", html, re.I)
    body_at = html.lower().rfind("</body>")
    if not head or body_at < 0:
        raise ValueError(f"{role} 找不到 <head> 或 </body>(模板改版了?)")
    at = head.end()
    out = html[:at] + _pre_block(defaults) + html[at:]
    if role != "synchronizer":
        return out
    body_at = out.lower().rfind("</body>")
    tail = (_mark("addon", "BEGIN") + "\n<script id=\"voc-payload\" type=\"application/json\">" + _jsval(payload or {})
            + "</script>\n<script>\n" + _fill(ADDON_JS) + "\n</script>\n" + _mark("addon", "END"))
    return out[:body_at] + tail + out[body_at:]


def strip_injection(html: str) -> str:
    return re.sub(r"<!-- VCGC-OPERATOR-CONSOLE:(\w+):BEGIN -->.*?<!-- VCGC-OPERATOR-CONSOLE:\1:END -->", "", html, flags=re.S)


def _links(d: dict) -> list:
    out = [{"label": "開操作台", "href": "../VIA_OperatorConsole_latest.html"}]
    rep = VIA / "VIA_Reports"
    for label, p in (("主控台藍圖", rep / "console_blueprint" / "ui" / "VIA-Console-Blueprint.html"),
                     ("全景實測報告", rep / "sweep" / "SWEEP_REPORT_latest.html")):
        if p.exists():
            out.append({"label": label, "href": os.path.relpath(p, UI_DIR).replace("\\", "/")})
    return out


def dock(d: dict, out_dir: Path | None = None, template_root: Path | None = None) -> dict:
    """Copies of the standard centralUI + synchronizer with this console's module preseeded and its addon mounted."""
    eng = eng089()
    if eng is None:
        return {"state": "BLOCKED", "why": _ENG["why"], "pages": {}}
    troot = Path(template_root or TEMPLATE_ROOT)
    chk = eng.template_check(troot)
    if not chk.get("ok"):
        return {"state": "BLOCKED", "why": "制式模板驗不過:" + str(chk.get("why")), "pages": {}}
    try:
        ent = json.loads((troot / "manifest.json").read_text(encoding="utf-8"))["canonicalEntrypoints"]
        src = {role: (troot / ent[role]).read_bytes() for role in DOCK_ROLES}
        defaults = eng.default_modules(src["synchronizer"].decode("utf-8"))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"state": "BLOCKED", "why": f"模板讀不動或改版:{type(exc).__name__}: {str(exc)[:120]}", "pages": {}}
    before = {role: hashlib.sha256(b).hexdigest() for role, b in src.items()}
    ov = overview(d)
    payload = {"engine": ENGINE, "built_at": d.get("built_at", ""), "worst": min((r[1] for r in ov), key=lambda k: _PRIOR.ORDER.get(k, 9)) if ov else "UNTESTED",
               "rows": [{"item": n, "lamp": k, "text": t, "tab": tab} for n, k, t, tab in ov], "links": _links(d)}
    ui = Path(out_dir or UI_DIR)
    ui.mkdir(parents=True, exist_ok=True)
    pages = {}
    for role in DOCK_ROLES:
        html = inject(src[role].decode("utf-8"), role, defaults, payload)
        if strip_injection(html).encode("utf-8") != src[role]:
            return {"state": "BLOCKED", "why": f"{role} 拿掉插入段後不等於模板原文(插入會改到模板)", "pages": {}}
        name = Path(ent[role]).name
        (ui / name).write_bytes(html.encode("utf-8"))
        pages[role] = str(ui / name)
    after = {role: hashlib.sha256((troot / ent[role]).read_bytes()).hexdigest() for role in DOCK_ROLES}
    return {"state": "DOCKED" if after == before else "BLOCKED", "pages": pages, "release": chk.get("release"),
            "module": SYNC_MODULE["id"], "defaults": len(defaults), "lamps": len(payload["rows"]),
            "why": "" if after == before else "模板原文在建構期間被改動(不是本支寫的;照實擋)"}


# ---------------------------------------------------------------- ③ live page = v0100 page + data-only sections

def _broker_sections(d: dict) -> dict:
    br = d.get("broker") or {}
    if not br.get("ok"):
        why = _e(br.get("why", ""))
        return {"eng": f"<h3>VCGC 資料中介</h3><div class='note'>{_lamp('FAIL')} {why}</div>", "chk": "", "out": ""}
    rt = "".join(f"<tr><td>{_e(r['table'])}</td><td>{_e(', '.join(r['dbs']) or '—')}</td><td>"
                 + _e(" · ".join(i["id"] + ("(net)" if i["net"] else "") + ("(寫庫)" if i["write"] else "") for i in r["items"]))
                 + f"</td><td>{'冊上' if r['in_ssot'] else '—'}</td></tr>" for r in br["routes"])
    lg = "".join(f"<tr><td>{_e(x.get('ts'))}</td><td>{_e(x.get('requester'))}</td><td>{_e(x.get('table'))}</td>"
                 f"<td>{_lamp(BUILD_LAMP.get(x.get('state'), 'SKIP'), x.get('state') or '')}</td><td>{_e(x.get('rows'))}</td>"
                 f"<td>{_e(x.get('handoff') or '—')} {_e(x.get('handoff_state') or '')}</td><td>{_e(str(x.get('why') or '')[:140])}</td></tr>"
                 for x in reversed(br["ledger"]))
    eng = (f"<h3>VCGC 資料中介 · 路由({len(br['routes'])} 張表;表 → 庫 · VDF 項;只從規格冊 outputs 與庫表冊推)</h3>"
           "<div class='note'>VRN 要料 → VCGC 先唯讀讀庫(EngineBus 唯一掃描器 / Parquet 目錄)→ 不夠才轉交 VDF 項(預設乾跑;需網路的項同意閘未開 = GATED)"
           " → 結果以 Parquet 經 VCGC 回 VRN(帳本 VIA_Reports/data_broker/LEDGER.jsonl)</div>"
           f"<table><tr><th>表</th><th>庫</th><th>VDF 項</th><th>庫表冊</th></tr>{rt}</table>"
           f"<h3>最近要料帳({len(br['ledger'])})</h3><table><tr><th>時間</th><th>要料者</th><th>表</th><th>結果</th><th>列</th><th>轉交</th>"
           f"<th>一句話</th></tr>{lg}</table>")
    bp = br["bypass"]
    brow = "".join(f"<tr><td>{_lamp('SKIP', '直讀')}</td><td>{_e(x['file'])}</td><td>{_e(', '.join(x['reads']))}</td><td>{_e(', '.join(x['stores']))}</td></tr>"
                   for x in bp.get("direct") or []) + "".join(
        f"<tr><td>{_lamp('OK', '經中介')}</td><td>{_e(f)}</td><td colspan='2'></td></tr>" for f in bp.get("brokered") or [])
    chk = (f"<h3>VRN 讀 VDF 經中介(繞道燈)</h3><div class='note'>{_e(bp.get('why', ''))}</div>"
           f"<table><tr><th>態</th><th>VRN 尾版</th><th>直讀的 VDF 表</th><th>庫</th></tr>{brow}</table>")
    bd = br["build"]
    drow = "".join(f"<tr><td>{_lamp(BUILD_LAMP.get(x['state'], 'SKIP'), x['state'])}</td><td>{_e(x['table'])}</td><td>{_e(x['rows'])}</td>"
                   f"<td>{_e(x['item'] or '—')}</td><td>{_e(x['why'][:160])}</td></tr>" for x in bd.get("rows") or [])
    out = (f"<h3>VDF 建庫計畫(VCGC→VDF;庫表冊「正庫」逐張量)· {_e(' · '.join(f'{k} {v}' for k, v in sorted((bd.get('tally') or {}).items())))}</h3>"
           "<div class='note'>乾跑。真跑 = 操作台 PowerShell 問你要不要建庫(滑鼠按「是」);需網路的項要你自己先開同意閘"
           " $env:VIA_NET_CONSENT='YES'(本台不代設)。</div>"
           f"<table><tr><th>態</th><th>表</th><th>現有列</th><th>VDF 項</th><th>一句話</th></tr>{drow}</table>")
    return {"eng": eng, "chk": chk, "out": out}


_ANCHORS = {"eng": "</div><div class='pane' id='p_run'>", "chk": "</div><div class='pane' id='p_out'>",
            "out": "</div><div class='pane' id='p_db'>", "hdr": "</span></div><div class='tabs'>"}


def page_html(data, t) -> str:
    html = _V0100["page_html"](data, t)
    if not data or "broker" not in data:                  # template / v0100-shaped data: v0100's bytes exactly
        return html
    for k, a in _ANCHORS.items():
        if html.count(a) != 1:
            raise ValueError(f"v0100 頁面錨點 {k} 出現 {html.count(a)} 次(骨架改版了?)")
    sec = _broker_sections(data)
    for k in ("eng", "chk", "out"):
        html = html.replace(_ANCHORS[k], sec[k] + _ANCHORS[k])
    html = html.replace(_ANCHORS["hdr"], f" · {_e(ENGINE)} · <a href='{_e(data.get('sync_page', ''))}'>SYNCHRONIZER</a>" + _ANCHORS["hdr"])
    try:
        eng = eng089()
        defaults = eng.default_modules((TEMPLATE_ROOT / "ui" / "VIA-SYNCHRONIZER-Standalone.html").read_text(encoding="utf-8")) if eng else []
        pre = _pre_block(defaults)
    except (OSError, ValueError) as exc:
        pre = f"<!-- VCGC-OPERATOR-CONSOLE:preseed:SKIP {type(exc).__name__} -->"
    head = re.search(r"<head\b[^>]*>", html, re.I)
    return html[:head.end()] + pre + html[head.end():]


def write_page(home_override: str | None = None) -> dict:
    """v0100's writer, collecting once: page (v0100 skeleton + data-only sections) → then the docked synchronizer copies."""
    t = _PRIOR.tokens()
    data = collect(home_override)
    data["format_lock"] = _PRIOR.format_lock()
    _PRIOR.OUT.mkdir(parents=True, exist_ok=True)
    _PRIOR.PAGE.write_text(page_html(data, t), encoding="utf-8")
    ov = overview(data)
    br = data["broker"]
    return {"page": str(_PRIOR.PAGE), "format_lock": data["format_lock"]["state"], "overview": {n: k for n, k, _, _ in ov},
            "domestic": len(data["inputs"]["domestic"]), "foreign": len(data["inputs"]["foreign"]), "views": len(data["views"]),
            "parquet_tables": len(data["plan"]), "dock": dock(data),
            "broker": {"routes": len(br.get("routes") or []), "bypass": (br.get("bypass") or {}).get("state"),
                       "build": (br.get("build") or {}).get("tally")}}


_PRIOR.collect, _PRIOR.overview, _PRIOR.page_html, _PRIOR.write_page = collect, overview, page_html, write_page


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    verb = args[0] if args else "page"
    home = _PRIOR._arg(args, "--home") or None
    if verb == "dock":
        r = dock(collect(home))
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["state"] == "DOCKED" else 1
    if verb == "broker":
        br = broker_state(home)
        print(json.dumps({"routes": len(br.get("routes") or []), "unrouted": len(br.get("unrouted") or []),
                          "bypass": (br.get("bypass") or {}).get("why"), "build": (br.get("build") or {}).get("tally"),
                          "ledger": len(br.get("ledger") or []), "why": br.get("why", "")}, ensure_ascii=False, indent=1))
        return 0 if br.get("ok") else 1
    return _PRIOR.main(args)


def selftest() -> int:
    import tempfile
    saved = {k: getattr(_PRIOR, k) for k in _V0100}
    for k, f in _V0100.items():                          # v0100's own checks measure v0100
        setattr(_PRIOR, k, f)
    try:
        rc = _PRIOR.selftest()
    finally:
        for k, f in saved.items():
            setattr(_PRIOR, k, f)
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    t = _PRIOR.tokens()
    tpl = page_html(None, t)
    chk("⑫ 模板(無資料)與 v0100 逐位元相同 → 骨架 sha 不變 → 格式鎖照舊", tpl == _V0100["page_html"](None, t)
        and _PRIOR.format_lock()["state"] in ("GREEN", "ABSENT"), _PRIOR.skeleton_sha(tpl))
    fake = {"status": {"gate": "[流程] 政策過", "chains": [], "tools": []}, "format_lock": {"state": "GREEN"}, "folders": {"data_ok": True},
            "lock": {}, "inputs": {"ok": True}, "broker": {
                "ok": True, "routes": [{"table": "tw_daily_prices", "dbs": ["vdf_tw_market"], "in_ssot": True,
                                        "items": [{"id": "tw_prices_inc", "net": True, "write": False}]}], "unrouted": ["x::y"],
                "bypass": {"state": "AMBER", "why": "直讀 1", "direct": [{"file": "VRN_X_v0100.py", "reads": ["tw_listings"], "stores": ["vdf_tw_market.duckdb"]}],
                           "brokered": ["VRN_ENG086_FirstPageLogicBridge_v0118.py"]},
                "build": {"rows": [{"table": "tw_daily_prices", "state": "GATED", "rows": 0, "item": "tw_prices_inc", "why": "不在 → GATED"}],
                          "tally": {"GATED": 1}},
                "ledger": [{"ts": "2026-09-28 17:00:00", "requester": "VRN_ENG086", "table": "tw_listings", "state": "GATED", "rows": 0,
                            "handoff": "tw_prices_inc", "handoff_state": "GATED", "why": "<b>x</b>"}]}}
    ov = {n: k for n, k, _, _ in overview(fake)}
    chk("⑬ 總覽 +3 燈:資料中介綠 · 繞道黃 · 建庫 GATED 黃(同意閘由操作員開)",
        ov.get("VCGC 資料中介") == "OK" and ov.get("VRN 讀 VDF 經中介") == "SKIP" and ov.get("VDF 建庫計畫(VCGC→VDF)") == "SKIP")
    bad = {**fake, "broker": {**fake["broker"], "build": {"rows": [{"table": "t", "state": "RED", "rows": 0, "item": "i", "why": ""}], "tally": {"RED": 1}}}}
    chk("⑭ 建庫計畫有紅 → 總覽紅(不被黃蓋掉)", {n: k for n, k, _, _ in overview(bad)}.get("VDF 建庫計畫(VCGC→VDF)") == "FAIL")
    full = {**fake, "inputs": _PRIOR.inputs_state(), "built_at": "2026-09-28 17:00:00", "sync_page": "ui/VIA-SYNCHRONIZER-Standalone.html"}
    live = page_html(full, t)
    chk("⑮ 活頁:路由表 · 要料帳 · 繞道明細 · 建庫計畫進各自的頁;帳裡的字照樣跳脫(不注入)",
        "VCGC 資料中介 · 路由" in live and "VRN_X_v0100.py" in live and "VDF 建庫計畫" in live and "<b>x</b>" not in live
        and live.index("VCGC 資料中介 · 路由") < live.index("id='p_run'") < live.index("繞道燈") < live.index("id='p_out'")
        < live.index("VDF 建庫計畫(VCGC→VDF;") < live.index("id='p_db'"))
    chk("⑯ 活頁加入 via.sync.v2:預置本台模組(狀態信封其他欄位原樣保留;借 ENG089 契約)+ 廣播 via-state-v2",
        "VOC_PRESEED" in live and SYNC_MODULE["id"] in live and "'via-state-v2'" in live and STATE_KEY in live)
    with tempfile.TemporaryDirectory() as td:
        r = dock({**full}, out_dir=Path(td))
        ok_pages = r["state"] == "DOCKED" and all(Path(p).exists() for p in r["pages"].values())
        sync_txt = Path(r["pages"].get("synchronizer", td)).read_text(encoding="utf-8") if ok_pages else ""
        src = (TEMPLATE_ROOT / "ui" / "VIA-SYNCHRONIZER-Standalone.html").read_bytes()
        chk("⑰ dock:synchronizer + 中央 UI 複本;外掛經 VIA_REGISTER_SYNC_ADDON 掛上;拿掉插入段 = 模板原文;模板一個位元不動",
            ok_pages and "VIA_REGISTER_SYNC_ADDON({ id: MID" in sync_txt and "voc-payload" in sync_txt
            and strip_injection(sync_txt).encode("utf-8") == src, f"{r['state']} · 燈 {r.get('lamps')} · {r.get('why', '')}")
    chk("⑱ 指令字串跟著最新的 PowerShell 操作台(不寫死 v0100)", ps_script().startswith(".\\Invoke-VIA-OperatorConsole-v"), ps_script())
    ok = rc == 0 and all(results)
    print(f"  {ENGINE} selftest +{sum(results)}/{len(results)} · v0100 rc={rc} · {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
