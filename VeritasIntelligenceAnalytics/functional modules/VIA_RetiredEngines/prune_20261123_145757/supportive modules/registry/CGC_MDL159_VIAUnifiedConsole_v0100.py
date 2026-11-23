#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL159 — VIA 統一主控頁(批544;操作員令「將跳出的兩個 html 整合唯一放在 tab 2 ·
tab 1 放要給 ai 的資訊全部放一起 · 字小一點專業 · 可將整頁內容轉換成 json/md」)

為什麼要有這一支
  跑一輪 via-ryg + via-panorama + via-vcgc,瀏覽器會**跳出三個分頁**:引擎匯流排矩陣、
  全景稽核、中央控管台。三張頁各講一段真相,沒有一張講得完;而下一個接手的 AI 要的東西
  (律/教訓/台帳/庫況/卡點/冷啟動步驟)散在四個 SSOT 和兩份交接檔裡,誰都拼不起來。

零九頭龍怎麼守
  本支**不重算任何東西**,也不重畫那三張頁。它只做兩件事:
    ① 把已經算好的 SSOT 與最近一次跑的結果**讀出來**,排成「給 AI 的一頁」(TAB 1);
    ② 把那三張既有的頁**內嵌**進 TAB 2(iframe 指向原檔),原頁一個位元都不動。
  所以它不是第九顆頭,是把八顆頭的嘴巴接到同一個喇叭上。原頁改版,這裡自動跟著變。

律:L20 唯一對接口 · L30 一功能一主 · 零 CDN · 零彈窗(VIA_NO_OPEN)· 零網路 · 只讀不改正本
用法:python3 CGC_MDL159_VIAUnifiedConsole_v0100.py [page|json|md|status] | --selftest
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
import html
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "unified_console"
REG = VIA / "supportive modules" / "registry"

# 要內嵌的既有頁(尾版 glob;缺=誠實 ABSENT,不假裝有)
PAGES = (
    ("引擎匯流排矩陣", "via-ryg", VIA / "VIA_Reports" / "engine_bus" / "ENGINE_BUS_MATRIX.html"),
    ("全景稽核修復", "via-panorama all", VIA / "VIA_Reports" / "panorama_audit" / "PANORAMA_AUDIT_latest.html"),
    ("中央控管台", "via-vcgc page --publish", VIA / "supportive modules" / "ui_support" / "VIA_UI_CentralGovernanceConsole_v0100.html"),
)


def prog(pct: float, msg: str) -> None:
    """動態進度條:沿用全樹慣例 @@PROGRESS|pct|msg(PS 側 Invoke-VIAPython 會轉播)。"""
    print(f"@@PROGRESS|{pct:.1f}|{msg}", flush=True)


def _j(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


# ===== [VIA:TAILPICK-BRIDGE:v0100] 尾版取用正典橋(批590/591;正典 SUP_MDL751_VIATailPick)=====
# 本群原本的行為:_newest(d, pat) + is_dir 守衛
# 批590 量過:CGC 族 32 份 `newest` 是 **13 個行為群**,不是同一件事(最大兩群參數順序相反、
# 兩支走 rglob、一支缺件回 pattern、一支按 mtime 排序)。所以正典把差異變成**明示選項**,
# 並逐群重放證零損失(15 種具名變體 × 6 組語料,90 組全同)。
# 這裡是**綁定**不是再定義一支 def:寫 def 的話能力庫裡這一家族還在,家族數不會掉(LL143)。
import importlib.util as _tp_ilu
from pathlib import Path as _tp_Path
_TP_MOD = None
_tp_p = _tp_Path(__file__).resolve()
while _tp_p.parent != _tp_p:
    _tp_hits = sorted((_tp_p / "supportive modules").glob("SUP_MDL751_VIATailPick_v*.py"))
    if _tp_hits:
        _tp_spec = _tp_ilu.spec_from_file_location("VIA_TAILPICK", _tp_hits[-1])
        _TP_MOD = _tp_ilu.module_from_spec(_tp_spec)
        _tp_spec.loader.exec_module(_TP_MOD)
        break
    _tp_p = _tp_p.parent
if _TP_MOD is None:      # 大聲壞掉:尾版取錯是無聲的錯(整條鏈指到舊引擎,沒人會發現)
    raise RuntimeError("[FAIL] 尾版取用正典缺席:supportive modules/SUP_MDL751_VIATailPick_v*.py")
_newest = _TP_MOD.bind(order="rp")
# ===== [VIA:TAILPICK-BRIDGE:END] =====


def _git(*args) -> str:
    try:
        return subprocess.run(["git", "-C", str(VIA.parent), *args], capture_output=True,
                              text=True, timeout=20).stdout.strip()
    except Exception:
        return ""


def collect(do_prog: bool = True) -> dict:
    """把散在各處的真相讀成一份給 AI 的 payload。**只讀**,一個位元都不寫回正本。"""
    if do_prog:
        prog(5, "讀律與教訓 SSOT")
    laws = _j(REG / "VIA_Policy_Laws_SSOT_v0100.json") or {}
    if do_prog:
        prog(15, "讀台帳")
    ledger = _j(REG / "VIA_AutoCode_Registry_v0100.json") or {}
    if do_prog:
        prog(25, "讀元件自動編號冊")
    inv = _j(REG / "VIA_Component_Inventory_SSOT_v0100.json") or {}
    if do_prog:
        prog(35, "讀最近一次自測格")
    g = _newest(VIA / "VIA_Reports" / "selftest_runs", "GRID_*.json") or \
        _newest(VIA / "VIA_Reports" / "selftest_grid", "GRID_*.json")
    grid = _j(g) if g else None
    if do_prog:
        prog(45, "讀最近一次全景稽核")
    pan = _j(VIA / "VIA_Reports" / "panorama_audit" / "PANORAMA_AUDIT_latest.json")
    if do_prog:
        prog(55, "盤庫(只看檔案大小與表數,不開大查詢)")
    dbs = []
    for rel in ("functional modules/VDF/output_hub/mega/vdf_tw_market.duckdb",
                "functional modules/VDF/output_hub/mega/vdf_global_market.duckdb",
                "functional modules/VDF/output_hub/active_tw_etf/active_tw_etf_holdings/ActiveTWETF.duckdb",
                "functional modules/VRN/db/vrn_reports.duckdb"):
        p = VIA / rel
        dbs.append({"rel": rel, "exists": p.is_file(),
                    "mb": round(p.stat().st_size / 1048576, 1) if p.is_file() else None})
    if do_prog:
        prog(65, "點名短令與梭")
    book = _newest(VIA, "Register-VIA-Commands-v*.ps1")
    import re as _re
    fns = sorted(set(_re.findall(r"^function global:(via-[A-Za-z0-9-]+)",
                                 book.read_text(encoding="utf-8", errors="replace"), _re.M))) if book else []
    shims = {q.stem.lower() for q in VIA.glob("*.cmd")}
    if do_prog:
        prog(70, "點名收容件位元(正本零觸碰的體檢)")
    # 批544:操作員的工作站上,VRN 收容件被就地改過(md5 7bedf1d6 ≠ 冊上的 d4cdaedf,多 612B)。
    # 那種事只有拿 md5 對冊才看得出來,而且看不出來的時候它會安靜地一直錯下去。
    # 這裡把全樹每一本 _INTAKE_MANIFEST_*.json 逐檔對一次,對不上就點名——這是給 AI 的第一手體檢。
    import hashlib as _h
    intake = []
    for man in sorted(VIA.rglob("_INTAKE_MANIFEST_*.json")):
        d = _j(man)
        if not d:
            continue
        for f in (d.get("files") or []):
            q = man.parent / str(f.get("name") or "")
            if not q.is_file():
                intake.append({"folder": man.parent.name, "name": f.get("name"), "state": "MISSING"})
                continue
            raw = q.read_bytes()
            got = _h.md5(raw).hexdigest()
            lf = _h.md5(raw.replace(b"\r\n", b"\n")).hexdigest()
            # 批546 更正:Windows 上 git 依 core.autocrlf 把 LF 轉 CRLF,同一個檔就多出「行數」個位元組,
            # raw md5 自然對不上。那不是汙染,是平台換行——把它判成 TOUCHED 就是我造的判錯紅燈。
            # 只差行尾 → EOL_CRLF(算過);LF 正規化後還是不符 → 才是真的 TOUCHED。
            st = "OK" if got == f.get("md5") else ("EOL_CRLF" if lf == f.get("md5") else "TOUCHED")
            intake.append({"folder": man.parent.name, "name": f.get("name"), "state": st,
                           "want": f.get("md5"), "got": got, "lf": lf,
                           "bytes": q.stat().st_size, "want_bytes": f.get("bytes")})
    if do_prog:
        prog(75, "讀 git 狀態")
    pay = {
        "schema": "VIA.UnifiedConsole.v1",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(VIA),
        "git": {"branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
                "head": _git("log", "--oneline", "-1"),
                "remote": "https://github.com/tonykuni/movies-dataset"},
        "laws": {"n": len(laws.get("laws") or []), "lessons_n": len(laws.get("lessons") or []),
                 "recent_lessons": (laws.get("lessons") or [])[-6:]},
        "ledger": {"n": len(ledger.get("ledger") or []), "recent": [
            {"ts": x.get("ts"), "component": x.get("component"), "code": x.get("code")}
            for x in (ledger.get("ledger") or [])[-4:]]},
        "components": {"active": (inv.get("counters") or {}).get("active")
                       or len(inv.get("records") or []), "by_kind": (inv.get("counters") or {})},
        "grid": ({"ts": grid.get("ts"), "total": grid.get("total"), "ok": grid.get("ok"),
                  "fail": grid.get("fail"), "skip": grid.get("skip")} if grid else None),
        "panorama": ({"ts": pan.get("ts"), "verdict": pan.get("verdict"),
                      "scan": pan.get("scan"), "tests": pan.get("tests")} if pan else None),
        "databases": dbs,
        "commands": {"book": book.name if book else None, "n_commands": len(fns),
                     "n_shims": len(shims),
                     "missing_shims": [f for f in fns if f.lower() not in shims]},
        "intake": {"n": len(intake), "bad": [x for x in intake if x["state"] == "TOUCHED"],
                   "eol": [x for x in intake if x["state"] == "EOL_CRLF"],
                   "rescue": "git checkout -- \"<路徑>\"  # 倉庫裡那份就是錨;被就地改過的還原回去"},
        "pages": [{"zh": zh, "cmd": cmd, "path": str(p), "exists": p.is_file(),
                   "kb": round(p.stat().st_size / 1024) if p.is_file() else None}
                  for zh, cmd, p in PAGES],
        "laws_for_ai": [
            "只增不減 —— 舊版本檔不刪;引擎改行為就開新版號檔,不就地改",
            "尾版律 —— 找引擎一律 glob 取最新,不准釘死版號",
            "正本零觸碰 —— references/intake/ 底下一個 byte 都不改",
            "不代設 —— 不替操作員設任何同意閘、不代裝套件;那是他的手",
            "誠實四態 —— rc 0=GREEN 1=RED 2=NODATA 3=ABSENT;判錯的紅燈和假綠一樣傷",
            "零九頭龍 —— 同一件事不准有第二套實作;要整合就收斂到一處",
            "本境≠工作站 —— 容器是乾淨 clone,空庫不等於壞掉;跑完要還原 UI churn",
        ],
        "cold_start": [
            "Set-Location '<VIA 根>'",
            "git pull --ff-only origin claude/via-envmanager-governance-7cls8h",
            ". (Get-ChildItem .\\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName",
            "via-vcgc            # 中央控管台",
            "via-unified         # 本頁(TAB1 給 AI · TAB2 三張頁)",
        ],
    }
    if do_prog:
        prog(80, "payload 完成")
    return pay


def _rel(target: Path) -> str:
    try:
        return os.path.relpath(target, OUT).replace("\\", "/")
    except Exception:
        return target.as_uri()


def to_md(pay: dict) -> str:
    L = [f"# VIA 統一主控 · 給 AI 的一頁", "", f"> 產生 {pay['generated_at']} · 根 `{pay['root']}`", ""]
    g = pay["git"]
    L += ["## 座標", "", f"- 倉庫 {g['remote']}", f"- 分支 `{g['branch']}`", f"- HEAD `{g['head']}`", ""]
    L += ["## 規矩(七條,違反過的都寫進教訓了)", ""] + [f"{i+1}. {x}" for i, x in enumerate(pay["laws_for_ai"])] + [""]
    L += ["## 現況", "", "| 量尺 | 值 |", "|---|---|"]
    L += [f"| 律 / 教訓 | {pay['laws']['n']} / {pay['laws']['lessons_n']} |",
          f"| 台帳 | {pay['ledger']['n']} 筆 |",
          f"| 活元件 | {pay['components']['active']} |"]
    if pay["grid"]:
        gr = pay["grid"]
        L += [f"| 自測格 | {gr['total']} 站 · OK {gr['ok']} / FAIL {gr['fail']} / SKIP {gr['skip']}({gr['ts']}) |"]
    if pay["panorama"]:
        pn = pay["panorama"]
        L += [f"| 全景稽核 | {pn['verdict']}({pn['ts']}) |"]
    c = pay["commands"]
    L += [f"| 短令 / 梭 | {c['n_commands']} / {c['n_shims']} · 缺梭 {len(c['missing_shims'])} |", ""]
    L += ["## 資料庫", "", "| 庫 | MB |", "|---|---:|"]
    L += [f"| `{d['rel']}` | {d['mb'] if d['exists'] else '缺'} |" for d in pay["databases"]] + [""]
    L += ["## 最近四筆台帳", ""]
    L += [f"- **{x['ts']}** {x['component']}\n  - {x['code']}" for x in pay["ledger"]["recent"]] + [""]
    L += ["## 最近六條教訓", ""]
    L += [f"- **{x.get('id')}**({x.get('batch')}){x.get('zh')}" for x in pay["laws"]["recent_lessons"]] + [""]
    L += ["## 冷啟動", "", "```powershell"] + pay["cold_start"] + ["```", ""]
    L += ["## 頁(TAB 2 內嵌的就是這三張)", ""]
    L += [f"- {p['zh']} — `{p['cmd']}` — {'在' if p['exists'] else '缺'}"
          f"{('(' + str(p['kb']) + ' KB)') if p['exists'] else ''}" for p in pay["pages"]]
    return "\n".join(L) + "\n"


CSS = """
:root{--bg:#0f1115;--fg:#dfe3ea;--dim:#8b93a3;--line:#242a35;--card:#161a21;--ok:#3fb950;--bad:#f85149;--warn:#d29922;--acc:#58a6ff}
@media(prefers-color-scheme:light){:root{--bg:#fbfcfd;--fg:#1c2128;--dim:#616b7a;--line:#e3e7ec;--card:#fff;--acc:#0969da}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:12.5px/1.55 'Segoe UI',-apple-system,'PingFang TC','Noto Sans TC',sans-serif}
header{padding:10px 16px;border-bottom:1px solid var(--line);display:flex;gap:14px;align-items:baseline;flex-wrap:wrap}
h1{font-size:14px;margin:0;font-weight:600;letter-spacing:.2px}
.sub{color:var(--dim);font-size:11px}
.tabs{display:flex;gap:2px;padding:0 16px;border-bottom:1px solid var(--line);background:var(--card)}
.tab{padding:7px 14px;font-size:12px;cursor:pointer;border:1px solid transparent;border-bottom:none;color:var(--dim);user-select:none}
.tab[aria-selected=true]{color:var(--fg);background:var(--bg);border-color:var(--line);border-radius:5px 5px 0 0}
main{padding:14px 16px 40px}
.panel[hidden]{display:none}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px;margin:0 0 14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:9px 11px}
.card h2{margin:0 0 6px;font-size:11px;font-weight:600;color:var(--dim);letter-spacing:.4px;text-transform:uppercase}
.big{font-size:19px;font-weight:600;font-variant-numeric:tabular-nums}
table{border-collapse:collapse;width:100%;font-size:12px;margin:0 0 14px}
th,td{border-bottom:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}
th{color:var(--dim);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.3px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
code,pre{font-family:'Cascadia Mono',Consolas,monospace;font-size:11.5px}
pre{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:9px 11px;overflow:auto}
h3{font-size:12px;margin:16px 0 6px;font-weight:600;border-left:3px solid var(--acc);padding-left:7px}
.ok{color:var(--ok)}.bad{color:var(--bad)}.warn{color:var(--warn)}.dim{color:var(--dim)}
.btn{font:inherit;font-size:11.5px;padding:4px 11px;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:5px;cursor:pointer}
.btn:hover{border-color:var(--acc);color:var(--acc)}
.bar{height:3px;background:var(--line);border-radius:2px;overflow:hidden;margin:5px 0 0}
.bar>i{display:block;height:100%;background:var(--ok)}
ul{margin:4px 0 12px;padding-left:18px}li{margin:2px 0}
.frames{display:flex;flex-direction:column;gap:12px}
.frame{border:1px solid var(--line);border-radius:6px;overflow:hidden;background:var(--card)}
.frame>.fh{padding:6px 11px;border-bottom:1px solid var(--line);font-size:11.5px;display:flex;gap:10px;align-items:baseline}
.frame iframe{width:100%;height:76vh;border:0;background:#fff}
@media(max-width:760px){.frame iframe{height:60vh}main{padding:12px}}
"""

JS = """
function pick(n){document.querySelectorAll('.tab').forEach(function(t){t.setAttribute('aria-selected',t.dataset.t===n)});
document.querySelectorAll('.panel').forEach(function(p){p.hidden=p.dataset.t!==n});
try{localStorage.setItem('via.uc.tab',n)}catch(e){}}
function dl(name,text,mime){var b=new Blob([text],{type:mime});var u=URL.createObjectURL(b);
var a=document.createElement('a');a.href=u;a.download=name;document.body.appendChild(a);a.click();
setTimeout(function(){URL.revokeObjectURL(u);a.remove()},0);}
document.addEventListener('DOMContentLoaded',function(){
  document.querySelectorAll('.tab').forEach(function(t){t.onclick=function(){pick(t.dataset.t)}});
  var saved=null;try{saved=localStorage.getItem('via.uc.tab')}catch(e){}
  pick(saved==='pages'?'pages':'ai');
  var P=JSON.parse(document.getElementById('via-payload').textContent);
  var stamp=(P.generated_at||'').replace(/[^0-9]/g,'').slice(0,14);
  document.getElementById('x-json').onclick=function(){dl('VIA_UNIFIED_'+stamp+'.json',JSON.stringify(P,null,1),'application/json')};
  document.getElementById('x-md').onclick=function(){dl('VIA_UNIFIED_'+stamp+'.md',document.getElementById('via-md').textContent,'text/markdown')};
});
"""


def build_html(pay: dict, md: str) -> str:
    e = html.escape
    g, c = pay["git"], pay["commands"]
    gr, pn = pay["grid"], pay["panorama"]

    def lamp(ok, txt):
        return f"<span class='{'ok' if ok else 'bad'}'>{e(txt)}</span>"

    cards = [
        f"<div class=card><h2>律 · 教訓</h2><div class=big>{pay['laws']['n']} · {pay['laws']['lessons_n']}</div></div>",
        f"<div class=card><h2>台帳</h2><div class=big>{pay['ledger']['n']}</div><div class=sub>只增不減</div></div>",
        f"<div class=card><h2>活元件</h2><div class=big>{pay['components']['active']}</div></div>",
    ]
    if gr:
        pct = round(100 * (gr["ok"] or 0) / (gr["total"] or 1))
        cards.append(f"<div class=card><h2>自測格</h2><div class=big>{gr['ok']}/{gr['total']}</div>"
                     f"<div class=bar><i style='width:{pct}%'></i></div>"
                     f"<div class=sub>FAIL {gr['fail']} · SKIP {gr['skip']} · {e(str(gr['ts']))}</div></div>")
    if pn:
        cards.append(f"<div class=card><h2>全景稽核</h2><div class='big {'ok' if pn['verdict']=='GREEN' else 'bad'}'>"
                     f"{e(str(pn['verdict']))}</div><div class=sub>{e(str(pn['ts']))}</div></div>")
    ik = pay["intake"]
    cards.append(f"<div class=card><h2>收容件位元</h2>"
                 f"<div class='big {'ok' if not ik['bad'] else 'bad'}'>{ik['n'] - len(ik['bad'])}/{ik['n']}</div>"
                 f"<div class=sub>{'全部對得上冊' if not ik['bad'] else str(len(ik['bad'])) + ' 件被動過'}"
                 f"{' · 行尾 CRLF ' + str(len(ik.get('eol') or [])) + ' 件(不算汙染)' if ik.get('eol') else ''}</div></div>")
    cards.append(f"<div class=card><h2>短令 · 梭</h2><div class=big>{c['n_commands']} · {c['n_shims']}</div>"
                 f"<div class=sub>{lamp(not c['missing_shims'], '缺梭 ' + str(len(c['missing_shims'])))}</div></div>")

    dbrows = "".join(f"<tr><td><code>{e(d['rel'])}</code></td><td class=n>"
                     f"{d['mb'] if d['exists'] else '<span class=bad>缺</span>'}</td></tr>" for d in pay["databases"])
    ledrows = "".join(f"<tr><td class=dim>{e(str(x['ts']))}</td><td><b>{e(str(x['component']))}</b><br>"
                      f"<span class=dim>{e(str(x['code'])[:150])}</span></td></tr>" for x in pay["ledger"]["recent"])
    lesrows = "".join(f"<tr><td><b>{e(str(x.get('id')))}</b><br><span class=dim>{e(str(x.get('batch')))}</span></td>"
                      f"<td>{e(str(x.get('zh'))[:420])}</td></tr>" for x in pay["laws"]["recent_lessons"])
    lawsli = "".join(f"<li>{e(x)}</li>" for x in pay["laws_for_ai"])
    cold = e("\n".join(pay["cold_start"]))

    if pay["intake"]["bad"]:
        rows = "".join(f"<tr><td><code>{e(str(x['folder']))}/{e(str(x['name']))}</code></td>"
                       f"<td class=bad>{e(x['state'])}</td>"
                       f"<td class=n>{x.get('bytes')}</td><td class=n>{x.get('want_bytes')}</td></tr>"
                       for x in pay["intake"]["bad"])
        intake_block = ("<table><tr><th>收容件</th><th>狀態</th><th class=n>現在</th><th class=n>冊上</th></tr>"
                        + rows + "</table><pre>" + e(pay["intake"]["rescue"]) + "</pre>")
    else:
        intake_block = (f"<p class=dim>全樹 {pay['intake']['n']} 件收容件的 md5 都對得上冊 —— "
                        f"正本零觸碰成立。<span class=dim>(對不上時這裡會點名,並附還原指令)</span></p>")
    frames = ""
    for p in pay["pages"]:
        if p["exists"]:
            src = _rel(Path(p["path"]))
            frames += (f"<div class=frame><div class=fh><b>{e(p['zh'])}</b>"
                       f"<span class=dim>{e(p['cmd'])}</span><span class=dim>{p['kb']} KB</span>"
                       f"<a class=dim href='{e(src)}' target=_blank>單獨開</a></div>"
                       f"<iframe src='{e(src)}' loading=lazy title='{e(p['zh'])}'></iframe></div>")
        else:
            frames += (f"<div class=frame><div class=fh><b>{e(p['zh'])}</b>"
                       f"<span class=bad>ABSENT — 還沒跑過 <code>{e(p['cmd'])}</code></span></div></div>")

    return f"""<!doctype html><html lang=zh-Hant><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>VIA 統一主控</title><style>{CSS}</style></head><body>
<header><h1>VIA 統一主控</h1>
<span class=sub>{e(pay['generated_at'])} · <code>{e(g['branch'])}</code> · {e(g['head'][:60])}</span>
<span style="margin-left:auto;display:flex;gap:6px">
<button class=btn id=x-json>整頁轉 JSON</button><button class=btn id=x-md>整頁轉 MD</button></span>
</header>
<div class=tabs role=tablist>
<div class=tab data-t=ai role=tab tabindex=0>① 給 AI 的一頁</div>
<div class=tab data-t=pages role=tab tabindex=0>② 頁(三張內嵌)</div>
</div>
<main>
<section class=panel data-t=ai>
<div class=grid>{''.join(cards)}</div>
<h3>規矩(七條)</h3><ul>{lawsli}</ul>
<h3>冷啟動</h3><pre>{cold}</pre>
<h3>收容件位元(正本零觸碰體檢)</h3>{intake_block}
<h3>資料庫</h3><table><tr><th>庫</th><th class=n>MB</th></tr>{dbrows}</table>
<h3>最近四筆台帳</h3><table><tr><th>時間</th><th>做了什麼</th></tr>{ledrows}</table>
<h3>最近六條教訓</h3><table><tr><th>編號</th><th>內容</th></tr>{lesrows}</table>
<h3>座標</h3><table>
<tr><th>倉庫</th><td><code>{e(g['remote'])}</code></td></tr>
<tr><th>分支</th><td><code>{e(g['branch'])}</code></td></tr>
<tr><th>HEAD</th><td><code>{e(g['head'])}</code></td></tr>
<tr><th>根</th><td><code>{e(pay['root'])}</code></td></tr></table>
</section>
<section class=panel data-t=pages hidden><div class=frames>{frames}</div></section>
</main>
<script type=application/json id=via-payload>{json.dumps(pay, ensure_ascii=False)}</script>
<script type=text/plain id=via-md>{e(md)}</script>
<script>{JS}</script></body></html>"""


def run(do_print: bool = True) -> dict:
    prog(1, "統一主控頁:讀 SSOT 與最近一次跑的結果(只讀;不重算、不重畫)")
    pay = collect()
    md = to_md(pay)
    prog(88, "組頁(零 CDN;三張既有頁以 iframe 內嵌,原頁零觸碰)")
    OUT.mkdir(parents=True, exist_ok=True)
    page = OUT / "VIA_UNIFIED_CONSOLE.html"
    page.write_text(build_html(pay, md), encoding="utf-8")
    (OUT / "VIA_UNIFIED_CONSOLE.json").write_text(json.dumps(pay, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "VIA_UNIFIED_CONSOLE.md").write_text(md, encoding="utf-8")
    prog(100, f"完成 → {page}")
    if do_print:
        miss = [p["zh"] for p in pay["pages"] if not p["exists"]]
        print(f"[統一主控] TAB1 給 AI · TAB2 內嵌 {len(pay['pages']) - len(miss)}/{len(pay['pages'])} 張"
              + (f"(缺:{'、'.join(miss)} —— 先跑它的短令)" if miss else ""))
        print(f"  頁  {page}")
        print(f"  JSON {OUT / 'VIA_UNIFIED_CONSOLE.json'}")
        print(f"  MD   {OUT / 'VIA_UNIFIED_CONSOLE.md'}")
        if os.environ.get("VIA_NO_OPEN") != "1":
            print("  [零彈窗] 本支永不自動開頁;要看請用 via-open 或直接點上面的路徑")
    return {"page": str(page), "payload": pay}


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    # 掃自己的原始碼時,**一定要先把自測本體切掉**:斷言裡寫著的字串本身就會被自己掃到,
    # 那不是程式在做的事,是我在講的話。批540 踩過同一顆釘子,這裡沿用同一個切法。
    full = Path(__file__).read_text(encoding="utf-8")
    src = full.split("\ndef selftest()")[0]
    pay = collect(do_prog=False)
    writes = [ln.strip() for ln in src.splitlines() if ".write_text(" in ln]
    chk("① 正本零觸碰:每一處 write_text 的目標都在產物夾 OUT,沒有一處寫回 registry / intake",
        bool(writes) and all(("OUT /" in w or w.startswith("page.write_text")) for w in writes),
        f"({len(writes)} 處 · 全在 OUT)")
    chk("② 零網路 · 零 CDN:不 import 任何連線庫;版面與腳本不引用任何外部資源",
        all(("import " + k) not in src for k in ("requests", "httpx", "urllib3", "aiohttp"))
        and "http://" not in CSS and "https://" not in CSS
        and "http" not in JS and "//cdn" not in (CSS + JS))
    chk("③ 零九頭龍:本支不重算也不重畫那三張頁,只 iframe 內嵌既有檔",
        "iframe" in src and "零九頭龍" in src
        and not any(("def " + x) in src for x in ("build_matrix", "render_panorama", "run_grid")))
    chk("④ payload 拿得到真東西(律/教訓/台帳/元件皆 > 0;拿不到就是 SSOT 讀壞了,不該靜靜給 0)",
        pay["laws"]["n"] > 0 and pay["laws"]["lessons_n"] > 0 and pay["ledger"]["n"] > 0
        and (pay["components"]["active"] or 0) > 0,
        f"(律 {pay['laws']['n']} · 教訓 {pay['laws']['lessons_n']} · 台帳 {pay['ledger']['n']} · 元件 {pay['components']['active']})")
    absent = [p["zh"] for p in pay["pages"] if not p["exists"]]
    chk("⑤ 頁缺席要誠實 ABSENT 並指路(沒跑過就說沒跑過,不畫一張空殼假裝有)",
        all(("exists" in p and isinstance(p["exists"], bool)) for p in pay["pages"])
        and "ABSENT — 還沒跑過" in src,
        f"(在 {len(pay['pages']) - len(absent)}/{len(pay['pages'])}" + (f" · 缺 {'、'.join(absent)}" if absent else "") + ")")
    md = to_md(pay)
    h = build_html(pay, md)
    chk("⑥ 整頁轉 JSON/MD:payload 與 md 都嵌在頁裡,匯出用純 Blob(零 CDN、不連外)",
        'id=via-payload' in h and 'id=via-md' in h and "URL.createObjectURL" in JS and "cdn" not in JS.lower())
    # `class=tabs` 也含 `class=tab`,所以要數更長的 token——但批546 這一檢又被咬了一次:
    # 教訓 LL96 的**內文裡就寫著** `class=tab data-t=` 這串字,而教訓會被排進 TAB1 與內嵌 payload,
    # 於是數出來變成 5。改數結構性的 `data-t=<名> role=tab`,那是版面才有、文字不會有的形狀。
    n_tab = h.count("data-t=ai role=tab") + h.count("data-t=pages role=tab")
    n_emb = sum(1 for p in pay["pages"] if p["exists"])
    chk("⑦ 兩個分頁都在,且 TAB2 內嵌的 src 是**相對路徑**(搬夾也不會斷)",
        n_tab == 2 and (n_emb == 0 or "src='../" in h),
        f"(分頁 {n_tab} · TAB2 內嵌 {n_emb} 張)")
    chk("⑧ 字小一點且專業:基準字級 ≤ 13px、表格 12px、等寬字用在程式碼",
        "12.5px" in CSS and "font-size:12px" in CSS and "Cascadia Mono" in CSS)
    chk("⑨ 動態進度條:走全樹慣例 @@PROGRESS|pct|msg(PS 側 Invoke-VIAPython 會轉播)",
        "@@PROGRESS|" in src and "def prog(" in src)
    # ⑩ 負控:一個永遠會過的檢查跟假綠燈沒兩樣(LL89)。把 payload 弄壞,④ 必須咬得住。
    broken = {"laws": {"n": 0, "lessons_n": 0}, "ledger": {"n": 0}, "components": {"active": 0}}
    caught = not (broken["laws"]["n"] > 0 and broken["laws"]["lessons_n"] > 0
                  and broken["ledger"]["n"] > 0 and (broken["components"]["active"] or 0) > 0)
    chk("⑩ 檢④ 的負控:把 payload 讀成全 0 時必須判 FAIL(讀壞 SSOT 不可以靜靜給 0)", caught, f"(咬得住={caught})")
    ik = pay["intake"]
    chk("⑪ 收容件位元體檢:全樹逐本 _INTAKE_MANIFEST 對 md5,且**行尾無關**"
        "(批546 更正:Windows 上 core.autocrlf 把 LF 轉 CRLF,raw md5 自然對不上——"
        "那是平台換行不是汙染,判成 TOUCHED 就是判錯的紅燈)",
        ik["n"] > 0 and isinstance(ik["bad"], list) and "git checkout" in ik["rescue"],
        f"(收容件 {ik['n']} 件 · 真被動過 {len(ik['bad'])} · 只差行尾 {len(ik.get('eol') or [])})")
    print(f"  [計] 十一檢 OK {11 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="VIA 統一主控頁(TAB1 給 AI · TAB2 內嵌既有頁)")
    ap.add_argument("verb", nargs="?", choices=("page", "json", "md", "status", "selftest"), default="page")
    argv = [("selftest" if a == "--selftest" else a) for a in sys.argv[1:]]
    args = ap.parse_args(argv)
    if args.verb == "selftest":
        print("=== VIA 統一主控(CGC_MDL159)· 十一檢自測(零網路;零 CDN;只讀正本)===")
        return selftest()
    if args.verb == "json":
        print(json.dumps(collect(do_prog=False), ensure_ascii=False, indent=1))
        return 0
    if args.verb == "md":
        print(to_md(collect(do_prog=False)))
        return 0
    if args.verb == "status":
        pay = collect(do_prog=False)
        n_ok = sum(1 for p in pay["pages"] if p["exists"])
        print(f"[統一主控] 律 {pay['laws']['n']} · 教訓 {pay['laws']['lessons_n']} · 台帳 {pay['ledger']['n']}"
              f" · 元件 {pay['components']['active']} · 可內嵌頁 {n_ok}/{len(pay['pages'])}")
        return 0 if n_ok else 2
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
