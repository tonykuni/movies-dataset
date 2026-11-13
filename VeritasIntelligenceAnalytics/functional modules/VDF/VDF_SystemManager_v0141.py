#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0141 — 薄尾:ui 兩面板(操作員令 2026-10-06:左面板輸入介面 · 右面板多頁展示頁面)。自管自報,靜態一頁,不起 server(L117)。
  ui                  跑 health → table matrix → panorama(各自是前版鏈的動詞,直接呼函式不走 main)→ 寫 VIA_Reports/vdf/VDF_UI_latest.html:
                      左:子系統 · 動詞(含現行版)· 參數預設 · 輸出形狀(PS 啟動器 / 直接 python)→ 組指令 · 複製 · 重讀;健康 / 表頭 / 全景 三張小卡
                      右:頁籤 健康矩陣(母系統彙總頁)· 表頭彙整 · 全景 · 結果檔 · 本輪 PS U/I(iframe 同夾相對路徑)
                      非 VIA_NO_OPEN=1 自動開瀏覽器。沙盒鍵:VIA_VDF_HOME · VIA_VDF_HEALTH_OUT · VIA_LAUNCHER(啟動器 PS 路徑,預設 Downloads/Invoke-VIA-Launch-v0100.ps1)
其餘動詞照前版鏈。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
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


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

import datetime
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
TAG = "v0141"


def _vnum_v0141(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0141(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0141(p) < _vnum_v0141(__file__)), key=_vnum_v0141)
PRIOR = _load_v0141(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ===== [VIA:SM-UI2:v0100] 子系統兩面板 U/I(左:輸入介面 — 選動詞/參數 → 組指令、複製;右:多頁展示 — 健康 / 表頭 / 全景 / 結果 / 本輪 PS U/I;靜態一頁,不起 server)=====
def sm_ui2(sub, home, out_dir, now, verbs, launcher_hint):
    import json as _json
    import html as _h
    from pathlib import Path as _P
    def rd(name):
        p = out_dir / name
        try:
            return _json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else None
        except ValueError:
            return None
    h, hm, pan = rd("HEALTH_latest.json"), rd("HEADER_MATRIX_latest.json"), rd("PANORAMA_latest.json")
    LAMP = {"GREEN": "#16a34a", "YELLOW": "#f59e0b", "RED": "#dc2626", "GRAY": "#9ca3af"}
    def lp(l):
        return "<i class='lp %s' style='background:%s'></i>" % (l, LAMP.get(l, LAMP["GRAY"]))
    tail = max(home.glob(sub + "_SystemManager_v*.py"), key=lambda q: q.name).name if list(home.glob(sub + "_SystemManager_v*.py")) else sub + "_SystemManager_v????.py"
    presets = {"ui": [], "health": [], "panorama": [], "table matrix": [], "table register": ["--apply"], "fn register": ["--apply"], "table number pull": [], "fn number pull": [], "dormant": ["--apply"], "tidy": ["--apply"], "extract": ["--limit", "20"], "extract triage": [], "extract status": []}
    verb_names = sorted(set(list(verbs.keys()) + list(presets.keys())))
    opts = "".join("<option value='%s'>%s%s</option>" % (_h.escape(v), _h.escape(v), (" @" + verbs[v]["current"]) if v in verbs else "") for v in verb_names)
    presets_js = _json.dumps(presets, ensure_ascii=False)
    hcard = ""
    if h:
        m = h["summary"]
        hcard = "<div class='card'>%s<b>健康</b> <small>%s</small><div class='kv'>檔族 %d(紅 %d 黃 %d 綠 %d)· 有號 %d · 登記 %d · 功 %d/%d · 表 %d/%d · lib 缺 %d</div></div>" % (lp(h["lamp"]), h["ts"], m["files"], m["red"], m["yellow"], m["green"], m["numbered"], m["registered"], m["fn_numbered"], m["fn_items"], m["tables_numbered"], m["tables"], m["libs_missing"])
    else:
        hcard = "<div class='card'>%s<b>健康</b><div class='kv'>尚未跑 health</div></div>" % lp("GRAY")
    pcard = ("<div class='card'>%s<b>全景</b> <small>%s</small><div class='kv'>冊族 %d(紅 %d 黃 %d 綠 %d 灰 %d)· 動詞 %d · 工作流 %d</div></div>" % (lp(pan["lamp"]), pan["ts"], pan["summary"]["books"], pan["summary"]["red"], pan["summary"]["yellow"], pan["summary"]["green"], pan["summary"]["gray"], pan["summary"]["verbs"], pan["summary"]["workflows"])) if pan else "<div class='card'>%s<b>全景</b><div class='kv'>尚未跑 panorama</div></div>" % lp("GRAY")
    tcard = ("<div class='card'>%s<b>表頭</b> <small>%s</small><div class='kv'>表 %d · %s</div></div>" % (lp(hm["lamp"]), hm["ts"], len(hm["rows"]), " ".join("%s=%d" % kv for kv in sorted(hm.get("per_cat", {}).items())))) if hm else "<div class='card'>%s<b>表頭</b><div class='kv'>尚未跑 table matrix</div></div>" % lp("GRAY")
    results = sorted(out_dir.glob("RESULT_*_latest.json"), key=lambda q: q.stat().st_mtime, reverse=True)[:15]
    rtr = "".join("<tr><td>%s</td><td>%s</td></tr>" % (_h.escape(p.name), __import__("datetime").datetime.fromtimestamp(p.stat().st_mtime).strftime("%m-%d %H:%M")) for p in results) or "<tr><td colspan='2' class='dim'>無</td></tr>"
    review = out_dir.parents[0] / "review"
    last_ps = sorted(review.glob("ps_*/VC_UI.html"), key=lambda q: q.stat().st_mtime, reverse=True)[:1] if review.is_dir() else []
    ps_src = ("../review/%s/VC_UI.html" % last_ps[0].parent.name) if last_ps else ""
    page = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%(sub)s U/I</title>
<style>
:root{--line:#e0e0e0;--panel:#f7f7f7;--txt:#1f2937;--dim:#6b7280;--acc:#2563eb}
body{font-family:"Microsoft JhengHei UI","Segoe UI",Arial;color:var(--txt);margin:0;font-size:12px;background:#fff;height:100vh;display:grid;grid-template-columns:320px 1fr;grid-template-rows:auto 1fr}
header{grid-column:1/3;padding:8px 12px;border-bottom:1px solid var(--line);display:flex;gap:12px;align-items:center}header h1{font-size:15px;margin:0}header small{color:var(--dim)}
aside{border-right:1px solid var(--line);padding:10px;overflow:auto;background:var(--panel)}main{display:flex;flex-direction:column;overflow:hidden}
label{display:block;font-size:11px;color:var(--dim);margin:8px 0 2px}select,input,textarea{width:100%%;box-sizing:border-box;font:12px Consolas,monospace;padding:4px 6px;border:1px solid var(--line);border-radius:6px;background:#fff}
button{padding:4px 10px;border:1px solid var(--line);background:#fff;border-radius:6px;cursor:pointer;font-size:11px;margin:6px 4px 0 0}button.p{background:var(--acc);color:#fff;border-color:var(--acc)}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:6px 8px;margin:6px 0;font-size:11.5px}.kv{color:var(--txt)}.dim{color:var(--dim)}
.tabs{display:flex;gap:4px;padding:6px 10px;border-bottom:1px solid var(--line);flex-wrap:wrap}.tabs button.on{background:#111827;color:#fff;border-color:#111827}
.pages{flex:1;position:relative}.page{position:absolute;inset:0;display:none;overflow:auto;padding:0}.page.on{display:block}iframe{width:100%%;height:100%%;border:0}
table{border-collapse:collapse;width:100%%}th,td{border:1px solid var(--line);padding:2px 5px;text-align:left}th{background:#111827;color:#fff}
.lp{display:inline-block;width:11px;height:11px;border-radius:50%%;vertical-align:middle;margin-right:4px}.lp.RED{animation:bl 2.4s ease-in-out infinite}@keyframes bl{0%%,100%%{opacity:1}50%%{opacity:.25}}
@media(max-width:800px){body{grid-template-columns:1fr;grid-template-rows:auto auto 1fr}aside{border-right:0;border-bottom:1px solid var(--line);max-height:40vh}}
</style></head><body>
<header><h1>%(sub)s · %(tail)s</h1><small>%(now)s · 左:輸入介面(組指令 → 複製到 PowerShell)· 右:多頁展示 · 靜態頁不起 server(L117)· <span style="color:#16a34a">●</span>綠 <span style="color:#f59e0b">●</span>黃 <span style="color:#dc2626">●</span>紅 <span style="color:#9ca3af">●</span>灰</small></header>
<aside>
  <label>子系統</label><input id="sub" value="%(sub)s" readonly>
  <label>動詞(現行版)</label><select id="verb" onchange="pre()">%(opts)s</select>
  <label>參數(空白分隔)</label><input id="args" placeholder="--limit 20">
  <label>輸出形狀</label><select id="shape"><option value="ps">PS 啟動器(落地 + 加速器 + 開 U/I)</option><option value="py">直接 python(省一層,不開 U/I)</option></select>
  <button class="p" onclick="gen()">組指令</button><button onclick="copyit()">複製</button><button onclick="reload()">重讀右側</button>
  <label>指令</label><textarea id="cmd" rows="6" readonly></textarea>
  <div class="dim" style="margin-top:6px">貼到 PowerShell 執行;跑完按「重讀右側」。</div>
  %(hcard)s%(tcard)s%(pcard)s
</aside>
<main>
  <div class="tabs"><button class="on" onclick="tab(0,this)">健康</button><button onclick="tab(1,this)">表頭彙整</button><button onclick="tab(2,this)">全景</button><button onclick="tab(3,this)">結果檔</button><button onclick="tab(4,this)">本輪 PS U/I</button></div>
  <div class="pages">
    <div class="page on"><iframe id="f0" src="../review/vcgc_health/HEALTH_MATRIX_latest.html"></iframe></div>
    <div class="page"><iframe id="f1" src="HEADER_MATRIX_latest.html"></iframe></div>
    <div class="page"><iframe id="f2" src="PANORAMA_latest.html"></iframe></div>
    <div class="page" style="padding:10px"><table><thead><tr><th>結果檔</th><th>時間</th></tr></thead><tbody>%(rtr)s</tbody></table></div>
    <div class="page"><iframe id="f4" src="%(ps_src)s"></iframe></div>
  </div>
</main>
<script>
var PRE=%(presets_js)s, LAUNCH=%(launcher)s, PY=%(py)s;
function pre(){var v=document.getElementById('verb').value;document.getElementById('args').value=(PRE[v]||[]).join(' ');gen()}
function gen(){var v=document.getElementById('verb').value,a=document.getElementById('args').value.trim(),s=document.getElementById('shape').value,c='';
 if(s==='ps'){var va=a?(" -VerbArgs @("+a.split(/\\s+/).map(function(x){return "'"+x+"'"}).join(',')+")"):'';c='pwsh -ExecutionPolicy Bypass -File "'+LAUNCH+'" -Sub %(sub)s -Verb "'+v+'"'+va}
 else{c='python "'+PY+'" '+v+(a?' '+a:'')}
 document.getElementById('cmd').value=c}
function copyit(){gen();var t=document.getElementById('cmd');t.select();try{navigator.clipboard.writeText(t.value)}catch(e){document.execCommand('copy')}}
function tab(i,b){document.querySelectorAll('.page').forEach(function(p,j){p.classList.toggle('on',i===j)});document.querySelectorAll('.tabs button').forEach(function(x){x.classList.remove('on')});b.classList.add('on')}
function reload(){location.reload()}
pre();
</script></body></html>""" % {"sub": sub, "tail": _h.escape(tail), "now": now, "opts": opts, "hcard": hcard, "tcard": tcard, "pcard": pcard, "rtr": rtr, "ps_src": ps_src, "presets_js": presets_js, "launcher": _json.dumps(launcher_hint), "py": _json.dumps(str(home / tail))}
    fp = out_dir / (sub + "_UI_latest.html")
    fp.write_text(page, encoding="utf-8")
    return fp
# ===== [VIA:SM-UI2:END] =====


def ui() -> dict:
    home = Path(os.environ.get("VIA_VDF_HOME") or HERE)
    out_dir = Path(os.environ.get("VIA_VDF_HEALTH_OUT") or (home.parents[1] / "VIA_Reports" / "vdf"))
    out_dir.mkdir(parents=True, exist_ok=True)
    steps = {}
    for name, fn in (("health", getattr(PRIOR, "health", None)), ("table_matrix", getattr(PRIOR, "table_matrix", None)), ("panorama", getattr(PRIOR, "panorama", None))):
        try:
            steps[name] = "OK" if (fn and fn() is not None) else "缺動詞"
        except Exception as exc:  # noqa: BLE001 — 一段壞不擋整頁,誠實記
            steps[name] = "%s:%s" % (type(exc).__name__, str(exc)[:80])
    try:
        pan = json.loads((out_dir / "PANORAMA_latest.json").read_text(encoding="utf-8-sig"))
        verbs = pan.get("verbs", {})
    except (OSError, ValueError):
        verbs = {}
    launcher = os.environ.get("VIA_LAUNCHER") or str(Path(os.environ.get("USERPROFILE") or "~").expanduser() / "Downloads" / "Invoke-VIA-Launch-v0100.ps1")
    fp = sm_ui2("VDF", home, out_dir, datetime.datetime.now().isoformat(timespec="seconds"), verbs, launcher)
    opened = False
    if os.environ.get("VIA_NO_OPEN") != "1" and os.name == "nt":
        try:
            os.startfile(str(fp))  # type: ignore[attr-defined]
            opened = True
        except OSError:
            pass
    lamp = "GREEN" if all(v == "OK" for v in steps.values()) else "YELLOW"
    return {"verb": "ui", "html": str(fp), "steps": steps, "opened": opened, "lamp": lamp}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["ui"]:
        u = ui()
        print("[計] VDF ui · %s · %s · 已開 %s · %s" % (u["html"], " ".join("%s=%s" % kv for kv in u["steps"].items()), u["opened"], u["lamp"]))
        print("  [U/I] %s" % u["html"])
        return 0
    return PRIOR.main(args)


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="vdfui2-"))
    home = td / "functional modules" / "VDF"
    (home / "registry").mkdir(parents=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VDF_HOME", "VIA_VDF_HEALTH_OUT", "VIA_NO_OPEN")}
    os.environ.update({"VIA_VDF_HOME": str(home), "VIA_VDF_HEALTH_OUT": str(td / "VIA_Reports" / "vdf"), "VIA_NO_OPEN": "1"})
    (home / "VDF_SystemManager_v0100.py").write_text("import sys\ndef main(argv=None):\n    args = list(sys.argv[1:] if argv is None else argv)\n    if args[:1] == ['intake']:\n        return 0\n    return 2\n", encoding="utf-8")
    u = ui()
    htm = Path(u["html"]).read_text(encoding="utf-8")
    chk("① 兩面板:aside 輸入(動詞 select · 參數 · 形狀 · 組指令/複製)· main 頁籤 5 頁(健康/表頭/全景/結果/本輪 PS)", "<aside>" in htm and "id=\"verb\"" in htm and "組指令" in htm and (htm.count('<div class="page"') + htm.count('<div class="page on"')) == 5 and "HEADER_MATRIX_latest.html" in htm and "PANORAMA_latest.html" in htm)
    chk("② 動詞表含 intake@v0100 與預設動詞 ui/extract · 指令模板含啟動器與 python 兩形", "intake @v0100" in htm and "<option value='extract'" in htm and "Invoke-VIA-Launch" in htm and "python \\\"" in htm or ("python" in htm and "LAUNCH=" in htm))
    chk("③ 三段 health/table_matrix/panorama 都跑或誠實記缺 · 四色 · 不開(VIA_NO_OPEN)", set(u["steps"]) == {"health", "table_matrix", "panorama"} and all(c in htm for c in ("#16a34a", "#f59e0b", "#dc2626", "#9ca3af")) and not u["opened"])
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("④ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 帶加速器橋 · NET/LIB 橋 · UI2 共用段", "[VIA:ACCEL-BRIDGE:v0100]" in body and "[VIA:SM-UI2:v0100]" in body and "[VIA:NET-BRIDGE:v0100]" in body and "[VIA:LIB-BRIDGE:v0100]" in body)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VDF_SystemManager_v0141 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
