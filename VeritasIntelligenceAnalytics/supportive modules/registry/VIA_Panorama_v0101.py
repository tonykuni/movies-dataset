#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_Panorama v0101 — 即時現況儀表板(薄尾;本體 v0100 原樣載入、全部公開名稱照轉)

操作員(側線 2026-09-30):「即時更新現況 HTML U/I + SYSTEM · 小字體較專業 · LAYOUT 緊湊 · LIVE LOG · HANDOVER REPORT ·
  PLOTLY DASHBOARD STYLE · 自動最佳化格式 · 矩陣式科技 · 無 SERVER 啟動後用於觀看整合狀況 · STREAMLIT 風 HTML U/I · 淺色」
本版只增兩個動詞,其餘全部轉交 v0100(scan / show / read / slice / digest / pack / chain / brief / verbs):
  dashboard [目標] [scan 參數…]                 跑一次全景(同輸入回 304 不重掃)→ 寫 dashboard_latest.html
  watch     [目標] [--interval 秒] [--rounds N]  每 N 秒一輪(預設 30 秒;Ctrl+C 停)→ 頁面自己重新載入,不用開 server
頁面:淺色 · 11px · 緊湊格線自動排版(auto-fit)· KPI 列 · Plotly(紅數趨勢 · 段 × 輪燈號矩陣 · 掃描秒數 · 標記覆蓋 · 語言分佈)
  · 段總覽矩陣 · 非綠項 · 交接報告(待辦依狀態 / 負責)· LIVE LOG(本引擎每輪一行)· 帳本末筆事件。
Plotly 用本機 python plotly 套件自帶的 plotly.min.js(複製一次到輸出夾,file:// 直接開);沒有才退 CDN;兩者都沒有 = 圖位顯示「沒有 Plotly」,表格照出。
只讀規則同 v0100:不寫目標、不執行目標;頁面只放計數 · 路徑 · 燈 · 時間,不放原文。
用法:VIA_Panorama_v0101.py watch --interval 30   → 開 <輸出夾>/dashboard_latest.html(卡上會印路徑)
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

import contextlib
import html as _html
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VIA_Panorama_v0100.py"  # 釘名:本體;不自己取尾版
_spec = importlib.util.spec_from_file_location("VIA_Panorama_v0100", HERE / PRIOR_NAME)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["VIA_Panorama_v0100"] = PRIOR
_spec.loader.exec_module(PRIOR)
globals().update({k: v for k, v in vars(PRIOR).items() if not k.startswith("_") and k not in ("main", "selftest", "VERSION", "ENGINE", "HERE")})



def __getattr__(name: str):
    """PEP 562:本版沒有的名稱一律轉給本體 v0100(薄尾整面接過來;呼叫端用舊名不會炸)。"""
    try:
        return getattr(PRIOR, name)
    except AttributeError:
        raise AttributeError(f"{__name__} 與本體 v0100 都沒有 {name}") from None


VERSION = "v0101"
ENGINE = Path(__file__).stem
PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"
STATUS = {"GREEN": "#0ca30c", "YELLOW": "#fab219", "RED": "#d03b3b", "HOLD": "#b9b8b2", "ABSENT": "#b9b8b2", "NODATA": "#b9b8b2"}
ICON = {"GREEN": "●", "YELLOW": "▲", "RED": "■", "HOLD": "◇", "ABSENT": "○", "NODATA": "○"}
LOG_NAME = "live.log"
PAGE_NAME = "dashboard_latest.html"


# ───────────────────────── 輸出夾 · 資料蒐集 ─────────────────────────

def resolve_out(target: str | None, opts: dict) -> Path:
    """與 v0100 run_scan 同一條規則算出輸出夾(不掃描)。"""
    if opts.get("out"):
        return Path(opts["out"]).expanduser().resolve()
    t = PRIOR.parse_target(target) if target else {"kind": "local", "path": str(PRIOR.default_target())}
    if t["kind"] != "local":
        return Path.cwd().resolve() / ".panorama"
    src = PRIOR.LocalSource(Path(t["path"]), use_git=not opts.get("no_git"))
    quick = {d for p in PRIOR.load_profiles().values() for d in p.get("detect", []) if src.exists(d)}
    prof = PRIOR.pick_profile(opts.get("profile"), src.root, quick)
    return PRIOR.out_dir(opts, src, prof)


def ensure_plotly(out: Path) -> str:
    """回 <script> 標籤:本機 plotly.min.js(複製一次)→ CDN 備援。"""
    dst = out / "plotly.min.js"
    if not dst.is_file():
        try:
            import plotly  # 只拿套件自帶的 js 檔,不用它的 python API
            src = Path(plotly.__file__).parent / "package_data" / "plotly.min.js"
            if src.is_file():
                shutil.copyfile(src, dst)
        except Exception as e:
            PRIOR.note(f"本機 plotly.min.js 沒有,退 CDN:{e}")
    if dst.is_file():
        return f"<script src='plotly.min.js'></script><script>window.Plotly||document.write(\"<script src='{PLOTLY_CDN}'><\\/script>\")</script>"
    return f"<script src='{PLOTLY_CDN}'></script>"


def tail_lines(path: Path, n: int) -> list:
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 256 * 1024))
            return f.read().decode("utf-8-sig", "replace").splitlines()[-n:]
    except OSError:
        return []


def collect(out: Path, opts: dict | None = None) -> dict:
    rep = json.loads((out / "panorama_latest.json").read_text(encoding="utf-8"))
    hist = [x for x in PRIOR.read_ledger(out / "universal_ledger.jsonl") if x.get("target_key") == rep.get("target_key")][-40:]
    ctx = {"rep": rep, "hist": hist, "log": tail_lines(out / LOG_NAME, 200)[::-1], "handoff": None, "events": []}
    prof = PRIOR.load_profiles().get(rep.get("profile")) or {}
    pa = (opts or {}).get("profile")
    if not prof and pa and Path(pa).is_file():  # 自帶的 profile 檔
        try:
            prof = json.loads(Path(pa).read_text(encoding="utf-8"))
        except ValueError as e:
            PRIOR.note(f"profile 檔壞:{e}")
    root = Path(rep["target"]) if rep.get("source") == "local" else None
    if root is not None and prof.get("handoff") and (root / prof["handoff"]).is_file():
        try:
            ctx["handoff"] = json.loads((root / prof["handoff"]).read_text(encoding="utf-8"))
        except ValueError as e:
            PRIOR.note(f"交接冊壞:{e}")
    if root is not None:
        for lg in prof.get("ledgers", []):
            for ln in tail_lines(root / lg, 12):
                try:
                    x = json.loads(ln)
                except ValueError:
                    PRIOR.note(f"帳本壞行略過:{Path(lg).name}")
                    continue
                ctx["events"].append({"ts": x.get("ts") or x.get("at") or "", "ledger": Path(lg).stem.replace("VIA_VCGC_", ""),
                                      "what": x.get("id") or x.get("event") or x.get("step") or "",
                                      "lamp": next((str(x.get(k)) for k in ("lamp", "verdict") if str(x.get(k)) in STATUS), ""),
                                      "note": str(x.get("summary") or x.get("file") or x.get("problems") or "")[:90]})
        ctx["events"].sort(key=lambda e: e["ts"], reverse=True)
    return ctx


# ───────────────────────── 頁面 ─────────────────────────

CSS = """:root{--page:#f9f9f7;--surf:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--mute:#898781;--grid:#e1e0d9;--axis:#c3c2b7;--ring:rgba(11,11,11,.10);--acc:#2a78d6}
*{box-sizing:border-box}html,body{margin:0;background:var(--page);color:var(--ink)}
body{font:11px/1.4 "Inter","Segoe UI","Noto Sans TC",system-ui,sans-serif;padding:10px 12px 18px}
.mono,code,pre,td.n{font-family:"JetBrains Mono","Cascadia Code","SF Mono",Consolas,"Noto Sans Mono CJK TC",monospace;font-variant-numeric:tabular-nums}
header{display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px;padding:6px 10px;background:var(--surf);border:1px solid var(--ring);border-radius:6px;margin-bottom:8px}
header h1{font-size:12.5px;font-weight:600;margin:0;letter-spacing:.02em}header .meta{color:var(--ink2)}header .sp{flex:1}
button{font:inherit;font-size:10.5px;padding:2px 8px;border:1px solid var(--ring);background:#fff;border-radius:4px;cursor:pointer;color:var(--ink2)}
.pill{display:inline-flex;align-items:center;gap:4px;padding:1px 7px;border-radius:9px;border:1px solid var(--ring);background:#fff;font-weight:600;white-space:nowrap}
.pill i{font-style:normal}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:6px;margin-bottom:8px}
.kpi{background:var(--surf);border:1px solid var(--ring);border-radius:6px;padding:5px 8px}
.kpi .l{color:var(--mute);font-size:10px;text-transform:uppercase;letter-spacing:.04em}.kpi .v{font-size:17px;font-weight:600;line-height:1.3}.kpi .s{color:var(--ink2);font-size:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:8px;margin-bottom:8px}
.card{background:var(--surf);border:1px solid var(--ring);border-radius:6px;padding:6px 8px;min-width:0}
.card h2{font-size:11px;font-weight:600;margin:0 0 4px;color:var(--ink2);text-transform:uppercase;letter-spacing:.05em;display:flex;gap:6px;align-items:center}
.card h2 .c{margin-left:auto;color:var(--mute);font-weight:400;text-transform:none;letter-spacing:0}
.plot{height:190px;width:100%}.plot.tall{height:230px}
.tw{max-height:260px;overflow:auto}
table{border-collapse:collapse;width:100%;table-layout:fixed}th,td{padding:2px 6px;border-bottom:1px solid var(--grid);text-align:left;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;vertical-align:top}
th{position:sticky;top:0;background:var(--surf);color:var(--mute);font-weight:500;font-size:10px;border-bottom:1px solid var(--axis)}td.n{text-align:right}
tr:hover td{background:#f1f0ec}
.log{font:10.5px/1.45 "JetBrains Mono",Consolas,monospace;background:#fff;border:1px solid var(--grid);border-radius:4px;padding:4px 6px;max-height:260px;overflow:auto;white-space:pre;color:var(--ink2)}
.nop{color:var(--mute);padding:20px 0;text-align:center}
footer{color:var(--mute);font-size:10px;margin-top:6px}
@media(max-width:520px){body{padding:8px 16px}.grid{grid-template-columns:1fr}}"""

JS = """(function(){var iv=+document.body.dataset.interval||0,left=iv,paused=false,k='via_pan_';
try{paused=localStorage.getItem(k+'pause')==='1';var y=sessionStorage.getItem(k+'y');if(y)window.scrollTo(0,+y)}catch(e){}
var cd=document.getElementById('cd'),bt=document.getElementById('pause');
function paint(){if(!cd)return;cd.textContent=iv?(paused?'已暫停':'下次更新 '+left+' 秒'):'單次(非 watch)';if(bt)bt.textContent=paused?'繼續':'暫停'}
if(bt)bt.onclick=function(){paused=!paused;left=iv;try{localStorage.setItem(k+'pause',paused?'1':'0')}catch(e){}paint()};
window.addEventListener('scroll',function(){try{sessionStorage.setItem(k+'y',String(window.scrollY))}catch(e){}});
paint();if(iv)setInterval(function(){if(paused)return;left--;if(left<=0){location.reload();return}paint()},1000)})();"""


def pill(lamp: str) -> str:
    lamp = str(lamp or "NODATA")
    return (f"<span class='pill' title='{_html.escape(lamp)}'><i style='color:{STATUS.get(lamp, '#898781')}'>{ICON.get(lamp, '○')}</i>"
            f"{_html.escape(lamp)}</span>")


def tbl(cols: list, rows: list, lamp_cols=("lamp",), num_cols=(), widths=None) -> str:
    e = _html.escape
    if not rows:
        return "<div class='nop'>(無)</div>"
    cg = "".join(f"<col style='width:{w}'>" for w in widths) if widths else ""
    h = [f"<div class='tw'><table><colgroup>{cg}</colgroup><thead><tr>" + "".join(f"<th>{e(c)}</th>" for c in cols) + "</tr></thead><tbody>"]
    for r in rows:
        tds = []
        for c in cols:
            v = r.get(c, "")
            if c in lamp_cols:
                tds.append(f"<td>{pill(v)}</td>")
            elif c in num_cols:
                tds.append(f"<td class='n'>{e(str(v))}</td>")
            else:
                tds.append(f"<td title='{e(str(v))}'>{e(str(v))}</td>")
        h.append("<tr>" + "".join(tds) + "</tr>")
    return "".join(h) + "</tbody></table></div>"


def figures(ctx: dict) -> dict:
    """Plotly 圖(資料 + 版面);單一 y 軸、細線 2px、點 8px、格線淡、hover 預設開。"""
    rep, hist = ctx["rep"], ctx["hist"]
    s = rep["sections"]
    base = {"margin": {"l": 34, "r": 8, "t": 4, "b": 26}, "paper_bgcolor": "#fcfcfb", "plot_bgcolor": "#fcfcfb",
            "font": {"size": 10, "color": "#52514e", "family": "Inter, Segoe UI, Noto Sans TC, sans-serif"},
            "xaxis": {"gridcolor": "#e1e0d9", "linecolor": "#c3c2b7", "zeroline": False, "tickfont": {"size": 9}, "nticks": 6, "automargin": True},
            "yaxis": {"gridcolor": "#e1e0d9", "linecolor": "#c3c2b7", "zeroline": False, "tickfont": {"size": 9}, "rangemode": "tozero"},
            "hoverlabel": {"bgcolor": "#ffffff", "bordercolor": "#c3c2b7", "font": {"size": 10, "color": "#0b0b0b"}}, "showlegend": False}
    xs = [x.get("at", "")[5:19].replace("T", " ") for x in hist]  # 到秒:同一分鐘兩輪不疊在同一點
    figs = {}
    line = {"color": "#2a78d6", "width": 2}
    figs["reds"] = {"data": [{"type": "scatter", "mode": "lines+markers", "x": xs, "y": [x.get("reds", 0) for x in hist], "line": line,
                              "marker": {"size": 8, "color": "#2a78d6", "line": {"color": "#fcfcfb", "width": 2}},
                              "hovertemplate": "%{x}<br>紅 %{y}<extra></extra>"}], "layout": base}
    figs["secs"] = {"data": [{"type": "scatter", "mode": "lines+markers", "x": xs, "y": [x.get("sec", 0) for x in hist], "line": line,
                              "marker": {"size": 8, "color": "#2a78d6", "line": {"color": "#fcfcfb", "width": 2}},
                              "hovertemplate": "%{x}<br>%{y} 秒<extra></extra>"}], "layout": base}
    order = {"GREEN": 0.5, "HOLD": 1.5, "ABSENT": 1.5, "NODATA": 1.5, "YELLOW": 2.5, "RED": 3.5}
    secs = [k for k in "ABCDEFG"]
    z = [[order.get((x.get("sections") or {}).get(k, "NODATA"), 1.5) for x in hist] for k in secs]
    txt = [[((x.get("sections") or {}).get(k, "") or "·")[:1] for x in hist] for k in secs]
    hm = dict(base, margin={"l": 22, "r": 6, "t": 4, "b": 26}, yaxis=dict(base["yaxis"], autorange="reversed", rangemode=None, gridcolor="rgba(0,0,0,0)"),
              xaxis=dict(base["xaxis"], gridcolor="rgba(0,0,0,0)", showticklabels=len(xs) <= 14))
    figs["matrix"] = {"data": [{"type": "heatmap", "x": xs, "y": secs, "z": z, "text": txt, "texttemplate": "%{text}",
                                "textfont": {"size": 9, "color": "#0b0b0b"}, "zmin": 0, "zmax": 4, "showscale": False, "xgap": 2, "ygap": 2,
                                "colorscale": [[0, STATUS["GREEN"]], [0.25, STATUS["GREEN"]], [0.25, STATUS["HOLD"]], [0.5, STATUS["HOLD"]],
                                               [0.5, STATUS["YELLOW"]], [0.75, STATUS["YELLOW"]], [0.75, STATUS["RED"]], [1, STATUS["RED"]]],
                                "hovertemplate": "%{x} · 段 %{y} · %{text}<extra></extra>"}], "layout": hm}
    cov = [r for r in s["C"]["rows"] if (r.get("have", 0) + r.get("miss", 0)) > 0]
    pct = [round(100.0 * r["have"] / (r["have"] + r["miss"]), 1) for r in cov]
    hb = dict(base, margin={"l": 86, "r": 30, "t": 4, "b": 22}, xaxis=dict(base["xaxis"], range=[0, 105], ticksuffix="%"),
              yaxis=dict(base["yaxis"], autorange="reversed", gridcolor="rgba(0,0,0,0)", rangemode=None))
    figs["cover"] = {"data": [{"type": "bar", "orientation": "h", "y": [r["key"] for r in cov], "x": pct, "marker": {"color": "#2a78d6"},
                               "text": [f"{p}%" for p in pct], "textposition": "outside", "cliponaxis": False, "textfont": {"size": 9, "color": "#52514e"},
                               "customdata": [[r["have"], r["miss"]] for r in cov],
                               "hovertemplate": "%{y}<br>有 %{customdata[0]} · 缺 %{customdata[1]} · %{x}%<extra></extra>"}], "layout": dict(hb, bargap=0.35)}
    langs = s["A"]["rows"][:10]
    lb = dict(base, margin={"l": 54, "r": 40, "t": 4, "b": 22}, yaxis=dict(base["yaxis"], autorange="reversed", gridcolor="rgba(0,0,0,0)", rangemode=None))
    figs["langs"] = {"data": [{"type": "bar", "orientation": "h", "y": [r["key"] for r in langs], "x": [r["files"] for r in langs],
                               "marker": {"color": "#2a78d6"}, "text": [f"{r['files']:,}" for r in langs], "textposition": "outside", "cliponaxis": False,
                               "textfont": {"size": 9, "color": "#52514e"},
                               "customdata": [[r["tails"], r["old"]] for r in langs],
                               "hovertemplate": "%{y}<br>檔 %{x:,} · 尾版 %{customdata[0]:,} · 舊版 %{customdata[1]:,}<extra></extra>"}],
                     "layout": dict(lb, bargap=0.35)}
    return figs


def render_dashboard(ctx: dict, interval: int, plotly_tag: str) -> str:
    e = _html.escape
    rep, hist = ctx["rep"], ctx["hist"]
    s = rep["sections"]
    a, g = s["A"]["summary"], s["G"]["summary"]
    prev, now = g.get("prev"), g.get("now")
    delta = "—" if prev is None else (f"{now - prev:+d} 對上輪")
    cov = {r["key"]: r for r in s["C"]["rows"]}

    def covtxt(k):
        r = cov.get(k)
        return ("—", "") if not r or not (r["have"] + r["miss"]) else (r["cover"], f"{r['have']}/{r['have'] + r['miss']} · HOLD {r['hold']}")
    ho = ctx["handoff"] or {}
    pend = ho.get("pending") or []
    kpis = [("總判", pill(rep["verdict"]), f"rc {rep['rc']} · {rep['sec']}s"), ("紅", f"<span class='mono'>{now}</span>", delta),
            ("檔數", f"<span class='mono'>{a['files']:,}</span>", f"略過 {sum(a['skipped'].values()):,}"),
            ("尾版 / 家族", f"<span class='mono'>{a['tails']:,}</span>", f"家族 {a['families']:,} · 舊版 {a['old']:,}"),
            ("ACCEL 覆蓋", covtxt("ACCEL")[0], covtxt("ACCEL")[1]), ("NET 覆蓋", covtxt("NET")[0], covtxt("NET")[1]),
            ("交接待辦", f"<span class='mono'>{len(pend)}</span>" if ho else "—", pill(ho.get("lamp", "NODATA")) if ho else "沒有交接冊"),
            ("驗收 closeout", pill(ho.get("closeout_lamp", "NODATA")) if ho else "—", "交接綠 ≠ 驗收")]
    kh = "".join(f"<div class='kpi'><div class='l'>{e(l)}</div><div class='v'>{v}</div><div class='s'>{sv}</div></div>" for l, v, sv in kpis)
    ov = [{"段": k, "名稱": PRIOR.SECTION_NAMES[k], "lamp": s[k]["lamp"], "紅": s[k].get("red_n", 0),
           "非綠": sum(1 for r in s[k].get("rows", []) if r.get("lamp") not in ("GREEN", "HOLD"))} for k in PRIOR.SECTIONS if k in s]
    bad = [{"段": k, "項": r.get("key", ""), "lamp": r.get("lamp"),
            "值": r.get("value") or (f"{r.get('have')}/{r.get('have', 0) + r.get('miss', 0)}" if "have" in r else r.get("n", "")),
            "說明": r.get("note") or r.get("first_missing") or ""}
           for k in "CDEFB" for r in sorted(s[k].get("rows", []), key=lambda r: -PRIOR.SEVER.get(r.get("lamp"), 0))
           if r.get("lamp") in ("RED", "YELLOW", "ABSENT")][:60]
    by_state = {}
    for p in pend:
        by_state[p.get("state", "?")] = by_state.get(p.get("state", "?"), 0) + 1
    prow = [{"id": p.get("id", ""), "狀態": p.get("state", ""), "負責": p.get("owner", ""), "主題": p.get("topic", ""), "下一步": p.get("next", "")}
            for p in sorted(pend, key=lambda p: ({"BLOCKED": 0, "MISSING": 1, "PENDING": 2, "PARTIAL": 3}.get(p.get("state"), 9), p.get("id", "")))]
    sm = ho.get("summary") or {}
    figs = figures(ctx)
    run_at = rep.get("at", "")
    upd = datetime.now(timezone.utc).isoformat(timespec="seconds")
    log = "\n".join(ctx["log"]) or "(還沒有 LIVE LOG:用 watch 或 dashboard 跑一輪)"
    ev = [{"時間": x["ts"][5:19].replace("T", " "), "帳本": x["ledger"], "事件": x["what"], "lamp": x["lamp"] or "NODATA", "說明": x["note"]}
          for x in ctx["events"][:24]]

    def card(title, body, count=""):
        return f"<div class='card'><h2>{e(title)}<span class='c'>{e(count)}</span></h2>{body}</div>"
    plot = lambda k, tall=False: f"<div id='fig_{k}' class='plot{' tall' if tall else ''}'></div>"  # noqa: E731
    h = [f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
         f"<title>VIA Panorama Live</title><style>{CSS}</style>{plotly_tag}",
         (f"<noscript><meta http-equiv='refresh' content='{interval}'></noscript>" if interval else ""), "</head>",
         f"<body data-interval='{int(interval)}'>",
         f"<header><h1>VIA Panorama · Live</h1>{pill(rep['verdict'])}<span class='meta mono'>{e(rep['target'])}</span>"
         f"<span class='meta'>{e(rep['profile'])} · {e(','.join(rep['scopes']))} · sha16 <span class='mono'>{e(rep['sha16'])}</span></span>"
         f"<span class='sp'></span><span class='meta'>掃描 {e(run_at[11:19])}Z · 頁 {e(upd[11:19])}Z</span>"
         f"<span id='cd' class='meta mono'></span><button id='pause' type='button'>暫停</button></header>",
         f"<div class='kpis'>{kh}</div>",
         "<div class='grid'>",
         card("紅數趨勢", plot("reds"), f"{len(hist)} 輪"), card("段 × 輪 燈號矩陣", plot("matrix"), "G ● · Y ▲ · R ■ · 灰 = HOLD/NODATA"),
         card("掃描秒數", plot("secs"), "304 不重掃不入帳"), "</div><div class='grid'>",
         card("標記覆蓋(尾版 · 範圍內)", plot("cover", True), rep["sections"]["C"]["summary"].get("tier", "")),
         card("語言分佈 前 10", plot("langs", True), f"{len(s['A']['rows'])} 種"),
         card("段總覽矩陣", tbl(["段", "名稱", "lamp", "紅", "非綠"], ov, num_cols=("紅", "非綠"), widths=["28px", "auto", "84px", "36px", "40px"])),
         "</div><div class='grid'>",
         card("非綠項(B–F)", tbl(["段", "項", "lamp", "值", "說明"], bad, widths=["28px", "34%", "84px", "90px", "auto"]), f"{len(bad)} 項"),
         card("交接報告 HANDOVER", (f"<div class='meta' style='margin-bottom:4px'>{pill(ho.get('lamp'))} 驗收 {pill(ho.get('closeout_lamp'))} · "
                                   f"需求 {sm.get('requirements', '—')} · 監看檔 {sm.get('watched_files', '—')} · 可重用 {sm.get('reusable', '—')} · "
                                   f"發現 {sm.get('findings', '—')} · at <span class='mono'>{e(str(ho.get('at', ''))[:19])}</span> · "
                                   + " · ".join(f"{e(k)} {v}" for k, v in sorted(by_state.items())) + "</div>"
                                   + tbl(["id", "狀態", "負責", "主題", "下一步"], prow, lamp_cols=(), widths=["118px", "70px", "22%", "16%", "auto"]))
              if ho else "<div class='nop'>這個目標的 profile 沒有交接冊</div>", f"待辦 {len(pend)}"),
         "</div><div class='grid'>",
         card("LIVE LOG", f"<div class='log'>{e(log)}</div>", f"{len(ctx['log'])} 行 · 新在上"),
         card("帳本末筆事件", tbl(["時間", "帳本", "事件", "lamp", "說明"], ev, widths=["92px", "92px", "26%", "84px", "auto"]), f"{len(ev)} 筆"),
         "</div>",
         f"<footer>VIA_Panorama {VERSION}(本體 v0100)· 只讀 · 不執行目標 · 頁面不含原文 · etag <span class='mono'>{e(rep.get('etag', ''))}</span>"
         f" · JSON panorama_latest.json · 帳本 universal_ledger.jsonl · LOG {LOG_NAME}</footer>",
         "<script>var F=" + json.dumps(figs, ensure_ascii=False) + ";"
         "var C={displayModeBar:false,responsive:true};"
         "for(var k in F){var el=document.getElementById('fig_'+k);if(!el)continue;"
         "if(window.Plotly){Plotly.newPlot(el,F[k].data,F[k].layout,C)}else{el.innerHTML=\"<div class='nop'>沒有 Plotly(本機套件與 CDN 都不在)</div>\"}}</script>",
         f"<script>{JS}</script></body></html>"]
    return "\n".join(h)


# ───────────────────────── 動詞 ─────────────────────────

def one_round(target: str | None, opts: dict, out: Path, interval: int) -> tuple:
    """跑一輪(同輸入 304 不重掃)→ LIVE LOG 一行 → 重寫頁面。回 (rc, 一行摘要)。"""
    t0 = time.time()
    o = dict(opts, out=str(out))
    latest = out / "panorama_latest.json"
    if latest.is_file():
        try:
            o["if_etag"] = json.loads(latest.read_text(encoding="utf-8")).get("etag")
        except ValueError:
            PRIOR.note("上一份 JSON 讀不到,整輪重掃")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.run_scan(target, o)
    first = (buf.getvalue().strip().splitlines() or [""])[0]
    kind = "304 " if "304" in first else "scan"
    if not latest.is_file():
        line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}  {kind}  rc {rc}  {first[:120]}"
        with open(out / LOG_NAME, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return rc, line
    rep = json.loads(latest.read_text(encoding="utf-8"))
    reds = sum(v.get("red_n", 0) for k, v in rep["sections"].items() if k in "ABCDEF")
    line = (f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}  {kind}  {rep['verdict']:<6} rc {rc}  紅 {reds:<3} "
            f"{time.time() - t0:5.1f}s  sha16 {rep.get('sha16', '')[:12]}  etag {rep.get('etag', '')}")
    out.mkdir(parents=True, exist_ok=True)
    with open(out / LOG_NAME, "a", encoding="utf-8") as f:  # 只增
        f.write(line + "\n")
    page = render_dashboard(collect(out, opts), interval, ensure_plotly(out))
    tmp = out / (PAGE_NAME + ".tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(out / PAGE_NAME)  # 原子替換:瀏覽器重新載入時不會讀到半頁
    return rc, line


def dashboard(target: str | None, opts: dict) -> int:
    out = resolve_out(target, opts)
    out.mkdir(parents=True, exist_ok=True)
    rc, line = one_round(target, opts, out, 0)
    print(f"[{ENGINE} dashboard] {line}\n  頁 {out / PAGE_NAME}")
    return rc


def watch(target: str | None, opts: dict) -> int:
    interval = max(5, int(opts.get("interval") or 30))
    rounds = int(opts.get("rounds") or 0)
    out = resolve_out(target, opts)
    out.mkdir(parents=True, exist_ok=True)
    print(f"[{ENGINE} watch] 每 {interval} 秒一輪 · 頁 {out / PAGE_NAME}(瀏覽器直接開,會自己重新載入;Ctrl+C 停)")
    n, rc = 0, 2
    try:
        while True:
            n += 1
            t0 = time.time()
            rc, line = one_round(target, opts, out, interval)
            print("  " + line, flush=True)
            if rounds and n >= rounds:
                break
            time.sleep(max(0.0, interval - (time.time() - t0)))
    except KeyboardInterrupt:
        print(f"  停 · {n} 輪")
    return rc


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a and a[0] in ("--selftest", "selftest"):
        return selftest()
    if a and a[0] in ("dashboard", "watch"):
        verb, rest = a[0], a[1:]
        extra = {}
        for key in ("--interval", "--rounds"):
            if key in rest:
                i = rest.index(key)
                extra[key[2:]] = int(rest[i + 1]) if i + 1 < len(rest) and rest[i + 1].isdigit() else 0
                del rest[i:i + 2]
        opts, pos = PRIOR.parse_opts(rest)
        opts.update(extra)
        return (dashboard if verb == "dashboard" else watch)(pos[0] if pos else None, opts)
    return PRIOR.main(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  {'✓' if cond else '✗'} {name}" + (f" · {note}" if note and not cond else ""))
    print(f"=== {ENGINE} 自測(薄尾;先跑本體 v0100)===")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prc = PRIOR.selftest()
    chk("本體 v0100 自測", prc == 0, buf.getvalue().strip().splitlines()[-1] if buf.getvalue().strip() else "")
    missing = [k for k in vars(PRIOR) if not k.startswith("_") and k not in globals()]
    chk("尾版不少公開名稱(TAILAPI)", not missing, " · ".join(missing[:5]))
    tmp = Path(tempfile.mkdtemp(prefix="via_pan101_"))
    try:
        t = tmp / "t"
        (t / "docs").mkdir(parents=True)
        for v in (100, 101):
            (t / f"fam_v{v:04d}.py").write_text(f'"""fam {v}"""\nSECRET_VALUE = {v}\n', encoding="utf-8")
        (t / "docs" / "handoff.json").write_text(json.dumps({"lamp": "GREEN", "closeout_lamp": "YELLOW", "at": "2026-09-30T00:00:00+00:00",
                                                             "summary": {"requirements": 3}, "pending": [
                                                                 {"id": "X-REQ001", "state": "BLOCKED", "owner": "AI", "topic": "t", "next": "n"}]}), encoding="utf-8")
        (t / "led.jsonl").write_text(json.dumps({"ts": "2026-09-30T00:00:00+00:00", "id": "step1", "lamp": "RED", "summary": "s"}) + "\n", encoding="utf-8")
        prof = {"name": "t101", "scopes": {"ALL": ["*"]}, "default_scopes": ["ALL"], "markers": [], "handoff": "docs/handoff.json", "ledgers": ["led.jsonl"]}
        pf = tmp / "p.json"
        pf.write_text(json.dumps(prof), encoding="utf-8")
        before = {p: p.stat().st_mtime_ns for p in t.rglob("*")}
        out = tmp / "out"
        with contextlib.redirect_stdout(io.StringIO()):
            rc1 = watch(str(t), {"profile": str(pf), "out": str(out), "no_git": True, "interval": 5, "rounds": 1})
            rc2 = dashboard(str(t), {"profile": str(pf), "out": str(out), "no_git": True})
        page = (out / PAGE_NAME).read_text(encoding="utf-8")
        log = (out / LOG_NAME).read_text(encoding="utf-8").splitlines()
        chk("watch 一輪 + dashboard 一輪:頁與 LIVE LOG 都在 · 第二輪 304", (out / PAGE_NAME).is_file() and len(log) == 2
            and " scan " in log[0] and "304" in log[1], " | ".join(log))
        chk("頁:Plotly 五圖 · KPI · 交接報告 · LIVE LOG · 帳本事件", all(x in page for x in (
            "fig_reds", "fig_matrix", "fig_secs", "fig_cover", "fig_langs", "class='kpis'", "X-REQ001", "LIVE LOG", "step1")))
        chk("頁:淺色 · 11px · 自動重新載入(watch 輪有 interval;單次為 0)", "#fcfcfb" in page and "11px" in page
            and "data-interval='0'" in page)
        chk("頁不含原文 · 目標 mtime 沒變", "SECRET_VALUE" not in page and before == {p: p.stat().st_mtime_ns for p in t.rglob("*")})
        chk("Plotly 走本機檔或 CDN(不空)", "plotly" in page.lower() and ((out / "plotly.min.js").is_file() or PLOTLY_CDN in page))
        chk("rc 同 v0100 規則(帳本末筆 RED → 總判 RED = 1;304 沿用上一份 rc)", rc1 == 1 and rc2 == 1, f"{rc1}/{rc2}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
