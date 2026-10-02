#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL254_ReviewOnePage v0102 — 薄尾:多分頁 U/I(VCGC · VDF · VRN 輸出與驗證狀態)· 小字 · 矩陣自動調節

操作員 2026-10-02:「ACTIVATE VCGC VDF VRN AND OUTPUT AND VERIFY OUTPUT AND USE A HTML U/I MULTIPLE TAB U/I TO DISPLAY
THE OUTPUT AND VERIFIED STATUS OF ALL OUTPUT. 小字體 自動調節優化矩陣報告」。
本版只加一個動詞 `tabs`(build 與其餘照 v0101 一字不動):
  · 資料只讀各正主自己寫的最新結果(不重跑 · 不改 · 舊頁不刪):唯一頁來源冊 27 源(v0100 build)+ 全功能串測逐站
    (VIA_Reports/vcgc/TEST_latest.json)+ VDF 鏈逐站(vdf_chain/VDFCHAIN_latest.json)+ VRN 鏈逐站(vrn_chain/VRNCHAIN_latest.json)
    + 冊外 *_latest.json(列未登錄,不漏)。
  · 驗證口徑一把尺(VERIFY_V0102):正主報綠且不過期 = VERIFIED;黃 / 資訊 = WARN;紅 = FAIL;無資料 / 等閘 / 缺件 / 跳過 = NODATA;
    過期 = STALE(不冒充現況)。每一列都帶「誰量的 · 什麼時候 · 原燈」。
  · 分頁:總覽 · VCGC · VDF · VRN · 治理(SSOT / 交接 / 工具 / 環境 / 全景)· 全部輸出 · 下一步與衝突;網址 #分頁 可直達。
  · 小字(11px;矩陣 10.5px)· 自動調節:矩陣比容器寬就逐級縮字到 9px、夠寬再放回 12px;長欄截斷附原文提示;
    表頭點了排序 · 每頁篩選 · 燈號快篩 · 緊湊 / 標準切換。單檔零 CDN 零外連,file:// 直開。
用法(只收 VCGC):via-vcgc run CGC_MDL254_ReviewOnePage tabs [--no-open] [--json]
輸出:VIA_Reports/review/TABS_latest.html · TABS_latest.json(+ 時間戳版)。零網路;不用 TA-Lib;不代設同意閘。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None
# ===== [VIA:NET-BRIDGE:END] =====

import html
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
PRIOR_PATH = HERE / "CGC_MDL254_ReviewOnePage_v0101.py"
_spec = importlib.util.spec_from_file_location("CGC_MDL254_ReviewOnePage_prior_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0101(它再裝進 v0100)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BODY = PRIOR.PRIOR                                      # v0100:VIA · OUT · build · ZH · ORDER · _load · _newest
VIA = BODY.VIA
OUT = BODY.OUT

VERIFY_V0102 = {"GREEN": "VERIFIED", "OK": "VERIFIED", "PASS": "VERIFIED",
                "YELLOW": "WARN", "INFO": "WARN", "AMBER": "WARN",
                "RED": "FAIL", "FAIL": "FAIL",
                "NODATA": "NODATA", "GATED": "NODATA", "ABSENT": "NODATA", "SKIP": "NODATA", "NOT_RUN": "NODATA",
                "STALE": "STALE"}
VORDER_V0102 = {"FAIL": 4, "STALE": 3, "WARN": 2, "NODATA": 1, "VERIFIED": 0}
VZH_V0102 = {"VERIFIED": "已驗證", "WARN": "警示", "FAIL": "失敗", "NODATA": "無資料", "STALE": "過期"}
SYSTEM_OF_AREA_V0102 = {"VCGC": "VCGC", "VDF": "VDF", "VRN": "VRN"}


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _read(rel: str):
    p = VIA / rel
    try:
        return json.loads(p.read_text(encoding="utf-8")), p
    except (OSError, ValueError):
        return None, p


def verify_of(lamp: str, stale: bool = False) -> str:
    """驗證口徑一把尺:正主燈 + 是否過期 → VERIFIED / WARN / FAIL / NODATA / STALE。"""
    if stale and lamp != "GREEN":
        return "STALE"
    return VERIFY_V0102.get(str(lamp or "").upper(), "NODATA")


def collect(res: dict) -> dict:
    """把唯一頁 build 的結果 + 串測逐站 + 兩條鏈逐站,收成同一種列:{sys, kind, id, name, lamp, verify, at, by, detail, path}。"""
    rows = []
    for s in res["sources"]:
        lamp = s["lamp"]
        rows.append({"sys": SYSTEM_OF_AREA_V0102.get(s["area"], "治理"), "group": s["area"], "kind": "輸出檔",
                     "id": s["id"], "name": s["title"], "lamp": lamp, "verify": verify_of(lamp, s["stale"]),
                     "at": s.get("at", ""), "age_h": s.get("age_h"), "by": s.get("owner", ""), "detail": s.get("summary", ""),
                     "path": s["path"], "rerun": s.get("rerun", "")})
    test, tp = _read("VIA_Reports/vcgc/TEST_latest.json")
    tmeta = {}
    if isinstance(test, dict):
        tmeta = {"at": test.get("at"), "run": test.get("run"), "head": test.get("head"), "counts": test.get("counts"),
                 "secs": test.get("secs"), "parallel": test.get("parallel"), "lamp": test.get("lamp")}
        for r in test.get("rows") or []:
            rows.append({"sys": "VCGC", "group": "全功能串測", "kind": "功能站", "id": r["id"], "name": r.get("name", r["id"]),
                         "lamp": r["lamp"], "verify": verify_of(r["lamp"]), "at": r.get("at", ""), "age_h": None,
                         "by": test.get("door", ""), "detail": str(r.get("last", ""))[:300], "secs": r.get("secs"),
                         "path": r.get("log", ""), "rerun": f"via-vcgc test --only {r['id']}"})
    chains = {}
    for sysname, rel, key in (("VDF", "VIA_Reports/vdf_chain/VDFCHAIN_latest.json", "id"),
                              ("VRN", "VIA_Reports/vrn_chain/VRNCHAIN_latest.json", "layer")):
        d, p = _read(rel)
        if not isinstance(d, dict):
            chains[sysname] = {"state": "NODATA", "why": f"{rel} 不在(這台還沒跑過鏈)"}
            continue
        chains[sysname] = {"at": d.get("generated"), "rc_name": d.get("rc_name"), "tally": d.get("tally"),
                           "consent": d.get("consent"), "secs": d.get("secs"), "mode": d.get("mode"), "path": rel}
        for i, st in enumerate(d.get("stages") or [], 1):
            sid = f"{st.get(key, '')}" + (f" · {i:02d}" if key == "layer" else "")
            rows.append({"sys": sysname, "group": f"{sysname} 鏈", "kind": "鏈站", "id": sid, "name": st.get("name", ""),
                         "lamp": st.get("state", "NODATA"), "verify": verify_of(st.get("state", "NODATA")),
                         "at": d.get("generated", ""), "age_h": None, "by": "CGC_MDL170" if sysname == "VDF" else "CGC_MDL172",
                         "detail": (str(st.get("detail", "")) + (" ↳ " + str(st["fix"]) if st.get("fix") else ""))[:400],
                         "secs": st.get("secs"), "path": str(st.get("evidence") or ""),
                         "rerun": "via-vdfchain run --resume" if sysname == "VDF" else "via-vrnchain run --resume"})
    for u in res.get("unregistered") or []:
        rows.append({"sys": "治理", "group": "未登錄", "kind": "未登錄輸出", "id": "—", "name": Path(u).name, "lamp": "INFO",
                     "verify": "NODATA", "at": "", "age_h": None, "by": "(冊外)", "detail": "冊外的 *_latest.json:登進來源冊新版後才有燈",
                     "path": u, "rerun": ""})
    summ = {}
    for r in rows:
        s = summ.setdefault(r["sys"], {k: 0 for k in VORDER_V0102})
        s[r["verify"]] += 1
    return {"rows": rows, "test": tmeta, "chains": chains, "summary": summ, "verdict": res["verdict"], "at": res["at"],
            "git": res["git"], "next": res["next"], "conflicts": res["conflicts"], "book": res["book"]}


_CSS_V0102 = """
.vt{--fs:11px;--mfs:10.5px;font-size:var(--fs)}
.vt .tabs{display:flex;flex-wrap:wrap;gap:2px;border-bottom:1px solid var(--line,#8884);margin:6px 0 8px;position:sticky;top:0;background:var(--bg,#fff);z-index:3}
.vt .tabs button{font:inherit;font-size:11.5px;border:1px solid transparent;border-bottom:none;background:none;color:inherit;padding:4px 10px;cursor:pointer;border-radius:5px 5px 0 0;opacity:.75}
.vt .tabs button[aria-selected=true]{border-color:var(--line,#8884);background:var(--card,#8881);opacity:1;font-weight:600}
.vt .tabs .n{font-size:10px;opacity:.75;margin-left:4px}
.vt section{display:none}.vt section.on{display:block}
.vt .tools{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:4px 0 6px}
.vt .tools input{font:inherit;padding:2px 6px;min-width:18em;border:1px solid var(--line,#8886);border-radius:4px;background:transparent;color:inherit}
.vt .chip{font:inherit;font-size:10.5px;border:1px solid var(--line,#8886);border-radius:10px;padding:1px 8px;background:none;color:inherit;cursor:pointer}
.vt .chip.off{opacity:.35;text-decoration:line-through}
.vt .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:6px;margin:4px 0 10px}
.vt .card{border:1px solid var(--line,#8884);border-radius:6px;padding:6px 8px}
.vt .card h4{margin:0 0 3px;font-size:12px}
.vt .vbar{display:flex;align-items:stretch;height:7px;border-radius:4px;overflow:hidden;margin:4px 0;background:#8882}
.vt .vbar i{display:block;height:7px;flex:none}
.vt .tw{overflow-x:auto;max-width:100%;border:1px solid var(--line,#8883);border-radius:5px}
.vt table.vm{border-collapse:collapse;width:100%;font-size:var(--mfs);line-height:1.35}
.vt table.vm th{position:sticky;top:0;background:var(--card,#eee);text-align:left;font-weight:600;padding:2px 5px;cursor:pointer;white-space:nowrap;user-select:none}
.vt table.vm td{padding:1px 5px;border-top:1px solid #8882;vertical-align:top;max-width:22em;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.vt table.vm td:nth-child(10){max-width:30em}.vt table.vm td:nth-child(11){max-width:16em;direction:rtl;text-align:left}
.vt.std table.vm td{white-space:normal}
.vt table.vm tr:hover td{background:#8881}
.vt .v{display:inline-block;min-width:4.6em;text-align:center;border-radius:3px;padding:0 4px;font-weight:600;font-size:10px}
.vt .v-VERIFIED{background:#1a7f3722;color:#1a7f37}.vt .v-WARN{background:#9a670022;color:#9a6700}
.vt .v-FAIL{background:#cf222e22;color:#cf222e}.vt .v-NODATA{background:#6e778122;color:#6e7781}.vt .v-STALE{background:#8250df22;color:#8250df}
.vt i.VERIFIED{background:#1a7f37}.vt i.WARN{background:#bf8700}.vt i.FAIL{background:#cf222e}.vt i.NODATA{background:#8c959f}.vt i.STALE{background:#8250df}
@media (prefers-color-scheme:dark){.vt .v-VERIFIED{color:#3fb950}.vt .v-WARN{color:#d29922}.vt .v-FAIL{color:#f85149}.vt .v-NODATA{color:#8b949e}.vt .v-STALE{color:#a371f7}}
.vt .muted{opacity:.7}.vt .fsz{font-size:10px;opacity:.7}
"""

_JS_V0102 = r"""
<script>(function(){
var root=document.querySelector('.vt');if(!root)return;
var tabs=root.querySelectorAll('.tabs button'),secs=root.querySelectorAll('section');
function show(id){tabs.forEach(function(b){b.setAttribute('aria-selected',b.dataset.t===id?'true':'false')});
secs.forEach(function(s){s.classList.toggle('on',s.id===id)});try{history.replaceState(null,'','#'+id)}catch(e){}
try{localStorage.setItem('via_tabs_last',id)}catch(e){}fit();}
tabs.forEach(function(b){b.addEventListener('click',function(){show(b.dataset.t)})});
var start=(location.hash||'').slice(1);if(!start){try{start=localStorage.getItem('via_tabs_last')||''}catch(e){start=''}}
if(!document.getElementById(start))start=secs[0].id;
/* 自動調節:矩陣比容器寬 → 逐級縮字(最小 9px);夠寬 → 放回(最大 12px) */
function fit(){root.querySelectorAll('section.on .tw').forEach(function(w){var t=w.querySelector('table');if(!t)return;
var fs=parseFloat(w.dataset.fs||'10.5');t.style.fontSize=fs+'px';var g=0;
while(t.scrollWidth>w.clientWidth+1&&fs>9&&g<12){fs-=0.5;t.style.fontSize=fs+'px';g++}
while(t.scrollWidth<w.clientWidth*0.82&&fs<12&&g<24){fs+=0.5;t.style.fontSize=fs+'px';if(t.scrollWidth>w.clientWidth){fs-=0.5;t.style.fontSize=fs+'px';break}g++}
w.dataset.fs=fs;var lab=w.previousElementSibling&&w.previousElementSibling.querySelector('.fsz');if(lab)lab.textContent='字級 '+fs+'px(自動)';});}
var rt;window.addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(fit,120)});
/* 篩選 + 燈號快篩 */
root.querySelectorAll('section').forEach(function(sec){var box=sec.querySelector('input.q'),chips=sec.querySelectorAll('.chip');
function apply(){var q=(box&&box.value||'').toLowerCase(),off={};chips.forEach(function(c){if(c.classList.contains('off'))off[c.dataset.v]=1});
sec.querySelectorAll('table.vm tbody tr').forEach(function(r){var ok=(!q||r.textContent.toLowerCase().indexOf(q)>=0)&&!off[r.dataset.v];r.style.display=ok?'':'none'});}
if(box)box.addEventListener('input',apply);chips.forEach(function(c){c.addEventListener('click',function(){c.classList.toggle('off');apply()})});});
/* 表頭排序 */
root.querySelectorAll('table.vm thead th').forEach(function(th,i){th.addEventListener('click',function(){var tb=th.closest('table').tBodies[0],
rs=Array.prototype.slice.call(tb.rows),d=th.dataset.d==='1'?-1:1;th.dataset.d=d===1?'1':'0';
rs.sort(function(a,b){var x=a.cells[i].dataset.k||a.cells[i].textContent,y=b.cells[i].dataset.k||b.cells[i].textContent,nx=parseFloat(x),ny=parseFloat(y);
if(!isNaN(nx)&&!isNaN(ny))return (nx-ny)*d;return x.localeCompare(y,'zh-Hant')*d});rs.forEach(function(r){tb.appendChild(r)})})});
var den=root.querySelector('#den');if(den)den.addEventListener('click',function(){root.classList.toggle('std');den.textContent=root.classList.contains('std')?'緊湊':'標準(換行)';fit()});
show(start);
})();</script>
"""


def _e(x) -> str:
    return html.escape("" if x is None else str(x))


def _bar(c: dict) -> str:
    n = sum(c.values()) or 1
    return "<div class='vbar'>" + "".join(f"<i class='{k}' style='width:{100 * v / n:.2f}%' title='{VZH_V0102[k]} {v}'></i>"
                                        for k, v in sorted(c.items(), key=lambda x: -VORDER_V0102[x[0]]) if v) + "</div>"


def _counts_line(c: dict) -> str:
    return " · ".join(f"<span class='v v-{k}'>{VZH_V0102[k]} {v}</span>" for k, v in sorted(c.items(), key=lambda x: -VORDER_V0102[x[0]]) if v)


def _matrix(rows: list, cols: list) -> str:
    """cols:(表頭, 取值函式, 排序鍵函式|None)。列帶 data-v(驗證態)給燈號快篩。"""
    head = "".join(f"<th>{_e(h)}</th>" for h, _f, _k in cols)
    body = []
    for r in sorted(rows, key=lambda r: (-VORDER_V0102[r["verify"]], r["sys"], r["group"], str(r["id"]))):
        tds = []
        for _h, f, k in cols:
            v = f(r)
            key = f" data-k='{_e(k(r))}'" if k else ""
            raw = re.sub(r"<[^>]+>", "", v) if isinstance(v, str) else str(v)
            tds.append(f"<td{key} title='{_e(raw[:600])}'>{v}</td>")
        body.append(f"<tr data-v='{r['verify']}'>{''.join(tds)}</tr>")
    return f"<div class='tw'><table class='vm'><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"


def _tools(n: int) -> str:
    chips = "".join(f"<button class='chip' data-v='{k}'>{VZH_V0102[k]}</button>" for k in VORDER_V0102)
    return (f"<div class='tools'><input class='q' placeholder='篩選(任何字:站 / 燈 / 明細 / 檔名…)'>{chips}"
            f"<span class='muted'>{n} 列 · 點表頭排序 · 點燈號隱藏該態</span><span class='fsz'></span></div>")


COLS_V0102 = [
    ("驗證", lambda r: f"<span class='v v-{r['verify']}'>{VZH_V0102[r['verify']]}</span>", lambda r: VORDER_V0102[r["verify"]]),
    ("原燈", lambda r: _e(r["lamp"]), None),
    ("系統", lambda r: _e(r["sys"]), None),
    ("類", lambda r: _e(r["group"]), None),
    ("站 / 來源", lambda r: _e(r["id"]), None),
    ("名稱", lambda r: _e(r["name"]), None),
    ("秒", lambda r: _e(r.get("secs") if r.get("secs") is not None else ""), lambda r: r.get("secs") if r.get("secs") is not None else -1),
    ("量於", lambda r: _e(r.get("at", "")), None),
    ("正主", lambda r: _e(r.get("by", "")), None),
    ("量到什麼 / 為什麼", lambda r: _e(r.get("detail", "")), None),
    ("檔 / 證據", lambda r: _e(r.get("path", "")), None),
    ("重跑", lambda r: f"<code>{_e(r.get('rerun', ''))}</code>", None),
]


def render(data: dict) -> str:
    rows = data["rows"]
    sysnames = ["VCGC", "VDF", "VRN", "治理"]
    by = {s: [r for r in rows if r["sys"] == s] for s in sysnames}
    total = {k: 0 for k in VORDER_V0102}
    for r in rows:
        total[r["verify"]] += 1
    tabs = [("ov", "總覽", len(rows))] + [(s.lower() if s != "治理" else "gov", s, len(by[s])) for s in sysnames] + \
        [("all", "全部輸出", len(rows)), ("nx", "下一步 · 衝突", len(data["next"]) + len(data["conflicts"]))]
    out = ["<div class='vt'><div class='tabs' role='tablist'>"]
    out += [f"<button role='tab' data-t='{t}'>{_e(n)}<span class='n'>{c}</span></button>" for t, n, c in tabs]
    out.append("<button id='den' class='chip' style='margin-left:auto'>標準(換行)</button></div>")
    # 總覽
    cards = []
    for s in sysnames:
        c = data["summary"].get(s, {k: 0 for k in VORDER_V0102})
        n = sum(c.values())
        worst = max((k for k, v in c.items() if v), key=lambda k: VORDER_V0102[k], default="NODATA")
        extra = ""
        if s in ("VDF", "VRN"):
            ch = data["chains"].get(s, {})
            extra = (f"<div class='muted'>鏈 {_e(ch.get('rc_name', ch.get('state', '')))} · {_e(ch.get('at', ''))} · "
                     f"同意閘 {_e((ch.get('consent') or {}).get('VIA_NET_CONSENT') or '未開')}</div>")
        if s == "VCGC" and data["test"]:
            t = data["test"]
            par = t.get("parallel") or {}
            extra = (f"<div class='muted'>串測 {_e(t.get('lamp'))} · {_e(t.get('at'))} · {_e(t.get('secs'))}s"
                     f"{' · 並行 ' + _e(par.get('jobs')) if par else ''}</div>")
        cards.append(f"<div class='card'><h4>{_e(s)} <span class='v v-{worst}'>{VZH_V0102[worst]}</span></h4>{_bar(c)}"
                     f"<div>{n} 項 · 已驗證 {c['VERIFIED']}({(100 * c['VERIFIED'] / n if n else 0):.0f}%)</div>"
                     f"<div>{_counts_line(c)}</div>{extra}</div>")
    worst_all = max((k for k, v in total.items() if v), key=lambda k: VORDER_V0102[k], default="NODATA")
    g = data["git"]
    ov = [f"<section id='ov'><div class='cards'><div class='card'><h4>全部輸出 <span class='v v-{worst_all}'>{VZH_V0102[worst_all]}</span></h4>"
          f"{_bar(total)}<div>{len(rows)} 項 · 已驗證 {total['VERIFIED']}({100 * total['VERIFIED'] / max(1, len(rows)):.0f}%)</div>"
          f"<div>{_counts_line(total)}</div><div class='muted'>唯一頁總判 {_e(data['verdict'])} · HEAD {_e(g.get('head'))} · {_e(data['at'])}</div></div>"
          + "".join(cards) + "</div>"]
    ov.append("<p class='muted'>驗證口徑:正主自己報綠且沒過期 = 已驗證;黃 / 資訊 = 警示;紅 = 失敗;無資料 / 等閘 / 缺件 / 跳過 = 無資料;"
              "超過時限 = 過期(不冒充現況)。本頁只讀各正主寫的最新結果,不重跑、不改。</p>")
    nonv = [r for r in rows if r["verify"] in ("FAIL", "STALE", "WARN")]
    ov.append(f"<h3>要看的(失敗 · 過期 · 警示)</h3>{_tools(len(nonv))}{_matrix(nonv, COLS_V0102)}</section>")
    out += ov
    for s in sysnames:
        sid = s.lower() if s != "治理" else "gov"
        out.append(f"<section id='{sid}'>{_tools(len(by[s]))}{_matrix(by[s], COLS_V0102)}</section>")
    out.append(f"<section id='all'>{_tools(len(rows))}{_matrix(rows, COLS_V0102)}</section>")
    nx = "".join(f"<tr data-v='WARN'><td>{i}</td><td><code>{_e(n['do'])}</code></td><td>{_e(n['why'])}</td></tr>" for i, n in enumerate(data["next"], 1))
    cf = "".join(f"<tr data-v='WARN'><td>{_e(c.get('id'))}</td><td>{_e(c.get('topic'))}</td><td>{_e(c.get('a'))} ↔ {_e(c.get('b'))}</td>"
                 f"<td>{_e(c.get('truth'))}</td><td>{_e(c.get('owner'))}</td></tr>" for c in data["conflicts"])
    out.append("<section id='nx'><h3>下一步(只一份,依序)</h3><div class='tools'><span class='fsz'></span></div>"
               f"<div class='tw'><table class='vm'><thead><tr><th>#</th><th>要做的事</th><th>為什麼</th></tr></thead><tbody>{nx or '<tr><td colspan=3>沒有要做的事</td></tr>'}</tbody></table></div>"
               "<h3>衝突(同一件事兩個來源說法不一)</h3><div class='tools'><span class='fsz'></span></div>"
               f"<div class='tw'><table class='vm'><thead><tr><th>代碼</th><th>主題</th><th>兩邊</th><th>實際</th><th>正主</th></tr></thead>"
               f"<tbody>{cf or '<tr><td colspan=5>無衝突</td></tr>'}</tbody></table></div></section>")
    out.append("</div>")
    return f"<style>{_CSS_V0102}</style>" + "".join(out) + _JS_V0102


def write_tabs(data: dict, open_page: bool = True) -> dict:
    spec = BODY._load(BODY._newest("CGC_MDL173_MatrixReportSpec_v*.py"), "_mdl254_spec_v0102")
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    total = {k: 0 for k in VORDER_V0102}
    for r in data["rows"]:
        total[r["verify"]] += 1
    kpis = [{"label": "已驗證", "value": total["VERIFIED"], "state": "GREEN"},
            {"label": "失敗", "value": total["FAIL"], "state": "RED" if total["FAIL"] else "GREEN"},
            {"label": "過期", "value": total["STALE"], "state": "YELLOW" if total["STALE"] else "GREEN"},
            {"label": "警示", "value": total["WARN"], "state": "YELLOW" if total["WARN"] else "GREEN"},
            {"label": "無資料", "value": total["NODATA"], "state": "NODATA"},
            {"label": "全部", "value": len(data["rows"]), "state": "GREEN"}]
    page = spec.page_html(render(data), title="VIA · VCGC / VDF / VRN 輸出與驗證", out=OUT / f"TABS_{stamp}.html",
                          kpis=kpis, payload={"summary": data["summary"], "at": data["at"]},
                          subtitle=f"{data['at']} · HEAD {data['git'].get('head')} · 來源冊 {data['book']} · {ENGINE}",
                          law="只讀各正主自己寫的最新結果(不重跑 · 不改 · 舊頁不刪);驗證口徑一把尺;同意閘 AI 不代設(鏈上記的是當次實際狀態)。")
    latest = OUT / "TABS_latest.html"
    latest.write_text(page.read_text(encoding="utf-8"), encoding="utf-8")
    for nm in (f"TABS_{stamp}.json", "TABS_latest.json"):
        (OUT / nm).write_text(json.dumps(data, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if open_page and not os.environ.get("VIA_NO_OPEN") and hasattr(os, "startfile"):
        try:
            os.startfile(str(latest))
        except OSError as e:
            print(f"  [頁] 沒自動開({e});自己開:{latest}")
    return {"html": latest, "json": OUT / "TABS_latest.json", "total": total}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if not args or args[0] != "tabs":
        return PRIOR.main(argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "engine": ENGINE, "state": "DENY", "why": "only via-vcgc(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    try:
        res = BODY.build({})
    except RuntimeError as e:
        print(json.dumps({"engine": ENGINE, "state": "RED", "why": str(e)}, ensure_ascii=False))
        return 1
    data = collect(res)
    paths = write_tabs(data, open_page="--no-open" not in args)
    t = paths["total"]
    print(f"[多分頁] 輸出 {len(data['rows'])} 項 · " + " · ".join(f"{VZH_V0102[k]} {v}" for k, v in sorted(t.items(), key=lambda x: -VORDER_V0102[x[0]])))
    for s, c in data["summary"].items():
        print(f"  [{s}] " + " · ".join(f"{VZH_V0102[k]} {v}" for k, v in sorted(c.items(), key=lambda x: -VORDER_V0102[x[0]]) if v))
    print(f"  [頁] {paths['html']}")
    if "--json" in args:
        print(json.dumps({"total": t, "summary": data["summary"]}, ensure_ascii=False))
    return 1 if t["FAIL"] else (2 if t["STALE"] or t["WARN"] else 0)


def selftest() -> int:
    rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("⑬ 前版 v0101 自測全過(過期判定 · 唯一頁)", rc == 0)
    m = [verify_of(x) for x in ("GREEN", "YELLOW", "RED", "GATED", "ABSENT", "INFO")] + [verify_of("RED", True), verify_of("GREEN", True)]
    chk("⑭ 驗證口徑一把尺:綠=已驗證 · 黃/資訊=警示 · 紅=失敗 · 等閘/缺件=無資料 · 過期非綠=過期 · 綠不因時間變過期",
        m == ["VERIFIED", "WARN", "FAIL", "NODATA", "NODATA", "WARN", "STALE", "VERIFIED"], m)
    fake = {"rows": [{"sys": s, "group": "g", "kind": "k", "id": f"{s}-{i}", "name": "n<b>", "lamp": l, "verify": verify_of(l),
                      "at": "t", "by": "o", "detail": "d", "path": "p", "rerun": "r", "secs": i}
                     for s in ("VCGC", "VDF", "VRN", "治理") for i, l in enumerate(("GREEN", "RED", "NODATA"))],
            "test": {"lamp": "GREEN", "at": "t", "secs": 1, "parallel": {"jobs": 4}}, "chains": {"VDF": {"rc_name": "GREEN"}, "VRN": {}},
            "summary": {}, "verdict": "YELLOW", "at": "t", "git": {"head": "abc"}, "next": [{"do": "x", "why": "y"}], "conflicts": [], "book": "b"}
    for r in fake["rows"]:
        fake["summary"].setdefault(r["sys"], {k: 0 for k in VORDER_V0102})[r["verify"]] += 1
    page = render(fake)
    secs = re.findall(r"<section id='([a-z]+)'", page)
    chk("⑮ 七個分頁(總覽 · VCGC · VDF · VRN · 治理 · 全部輸出 · 下一步衝突)· 每頁有矩陣 · 列帶驗證態",
        secs == ["ov", "vcgc", "vdf", "vrn", "gov", "all", "nx"] and page.count("<table class='vm'>") == 8 and "data-v='FAIL'" in page, secs)
    chk("⑯ 小字(11px / 矩陣 10.5px)· 自動調節(縮到 9px · 放回 12px)· 排序 · 篩選 · 燈號快篩 · 文字已轉義",
        "--fs:11px" in page and "fs>9" in page and "fs<12" in page and "localeCompare" in page and "input.q" in page
        and "n&lt;b&gt;" in page and "<b>" not in page.split("<style>")[0])
    chk("⑰ 單檔零外連(沒有 http(s):// 資源)", not re.search(r"(src|href)=['\"]https?://", page))
    with tempfile.TemporaryDirectory() as td:
        keep = globals()["OUT"]
        try:
            globals()["OUT"] = Path(td)
            got = write_tabs(fake, open_page=False)
            html_ok = got["html"].is_file() and "<section id='vdf'>" in got["html"].read_text(encoding="utf-8")
        finally:
            globals()["OUT"] = keep
    chk("⑱ 經頁殼 CGC_MDL173 出檔(TABS_latest.html · .json);暫存夾試寫,實樹報告夾不動", html_ok)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑲ 加速器橋 · 網路橋在;tabs 只收 VCGC;不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and "VIA_FROM_VCGC" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"[唯一頁 v0102] 自測 {sum(ok)}/{len(ok)}")
    return 0 if rc == 0 and all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
