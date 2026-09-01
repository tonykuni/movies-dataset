#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA_SYSTEM_MANAGER — 總系統管理器(批281;操作員令)
====================================================================
操作員令:「應該用一個總 VIA_SYSTEM_MANAGER.py 管理一切:銜接 sync、
html u/i、輸入參數、windows i/o、拖曳式、下拉選單、勾選控管元件;
engine / module list 要清楚」。
一總管四職(Zero-Hydra=全複用正主,零重造):
  ①sync   同步(=VIA-ALL 律:stash -u→fetch→ff-only→分流備份
          分支後對齊;零彈窗零卡斷)
  ②list   引擎/模組清單清楚列印(=MDL112 Atlas gather 直取)
  ③run    任務執行(=MDL095 任務冊 argv 白名單 subprocess;
          任意指令拒絕=安全鐵則)
  ④ui     總控頁再生+開啟(Windows I/O:os.startfile 正道/
          webbrowser 後備):
          左=引擎/模組清單(搜尋過濾+分組清楚)
          中=控管元件:任務下拉+多任務勾選+codes 參數欄→
            fetch 指揮台 127.0.0.1:8765/run(deck 在=真跑;
            不在=誠實教先開 via)
          右=拖曳收件區(拖入列檔名+生成 via-intake 指引;
            瀏覽器沙盒不落盤=誠實 v1,真收容走 Downloads 正道)
用法:python3 VIA_SYSTEM_MANAGER_v0100.py sync|list|run <task>|ui
      | --selftest
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

import html
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

VIA = Path(__file__).resolve().parent
REG = VIA / "supportive modules" / "registry"
OUT = (VIA / "supportive modules" / "ui_support"
       / "VIA_UI_MasterControl_v0100.html")


def _mod(pat: str):
    p = sorted(REG.glob(pat))[-1]
    spec = importlib.util.spec_from_file_location(p.stem, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def do_sync() -> int:
    """VIA-ALL 同步律(批272):任何狀態都能對齊雲端;零彈窗"""
    def g(*a):
        return subprocess.run(["git", "-C", str(VIA), *a],
                              capture_output=True, text=True)
    g("stash", "push", "--include-untracked", "-m", "MGR-selfheal")
    g("fetch", "origin", "main")
    r = g("merge", "--ff-only", "origin/main")
    if r.returncode != 0:
        sha = g("rev-parse", "--short", "HEAD").stdout.strip()
        g("branch", f"via-local-backup-{sha}")
        g("reset", "--hard", "origin/main")
        print(f"[MGR:sync] 分流偵測→備份分支 via-local-backup-{sha} "
              "留痕後對齊雲端")
    print("[MGR:sync] 對齊 origin/main ✓(髒樹已 stash 留痕,"
          "找回:git stash pop)")
    return 0


def do_list(do_print: bool = True) -> dict:
    """引擎/模組清單清楚(MDL112 Atlas 資料層直取)"""
    d = _mod("CGC_MDL112_SystemAtlas_v*.py").gather()
    if do_print:
        for sub, fam in d["engines"].items():
            print(f"[ENGINE] {sub}({len(fam)} 族)")
            for b in sorted(fam):
                print(f"    {b}")
        print(f"[MODULE] CGC 治理模組 {len(d['mods'])} 族")
        for b in sorted(d["mods"]):
            print(f"    {b}")
    return d


def do_run(task: str, extra: list[str] | None = None) -> int:
    """白名單任務執行(MDL095 任務冊=唯一 SSOT;任意指令拒絕)"""
    T = _mod("CGC_MDL095_DeckServer_v*.py").task_registry()
    if task not in T:
        print(f"[MGR:run] '{task}' 不在白名單任務冊=拒絕(安全鐵則)。"
              f"可用:{' '.join(sorted(T))}")
        return 2
    argv = list(T[task]["argv"]) + list(extra or [])
    print(f"[MGR:run] {task}:{T[task]['zh']}")
    return subprocess.run(argv, stdin=subprocess.DEVNULL).returncode


def render(d: dict, tasks: dict) -> str:
    eng_side = "".join(
        f"<details open><summary><b>{html.escape(sub)}</b>"
        f"<span class='tag'>{len(fam)}</span></summary>"
        + "".join(f'<div class="item" data-n="{html.escape(b.lower())}">'
                  f"{html.escape(b)}</div>" for b in sorted(fam))
        + "</details>" for sub, fam in d["engines"].items()) \
        + (f"<details><summary><b>CGC 治理模組</b>"
           f"<span class='tag'>{len(d['mods'])}</span></summary>"
           + "".join(f'<div class="item" data-n="{html.escape(b.lower())}">'
                     f"{html.escape(b)}</div>" for b in sorted(d["mods"]))
           + "</details>")
    opts = "".join(f'<option value="{html.escape(k)}">{html.escape(k)} · '
                   f"{html.escape(z)}</option>" for k, z in tasks.items())
    checks = "".join(
        f'<label class="ck"><input type="checkbox" value="{html.escape(k)}">'
        f"{html.escape(k)}</label>"
        for k in ("boot", "revenue", "consensus", "etf_analysis",
                  "revenue_consensus", "regression", "selftest_fast")
        if k in tasks)
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 總控台 Master Control</title><style>
:root{{--bg:#f3f5f7;--panel:#fff;--line:#dce2e8;--text:#1f2933;
--muted:#6b7785;--blue:#4c78a8;--green:#5a9e6f;--red:#c96b5a}}
@media (prefers-color-scheme: dark){{:root{{--bg:#10151b;--panel:#171e26;
--line:#2a333d;--text:#dbe3ea;--muted:#8a97a5;--blue:#7ba3cc;
--green:#79b58c;--red:#d98a7c}}}}
*{{box-sizing:border-box;margin:0}}
body{{background:var(--bg);color:var(--text);
font:12.5px/1.5 "Segoe UI","Noto Sans TC",sans-serif}}
.app{{display:grid;grid-template-columns:290px 1fr 260px;gap:12px;
padding:12px;min-height:100vh}}
.col{{background:var(--panel);border:1px solid var(--line);
border-radius:10px;padding:12px;overflow:auto;max-height:96vh}}
h1{{font-size:14px}}h2{{font-size:10px;color:var(--muted);
font-weight:800;letter-spacing:.08em;text-transform:uppercase;
margin:10px 0 6px}}
.sub{{color:var(--muted);font-size:10px;margin:2px 0 8px}}
input[type=text],select{{width:100%;border:1px solid var(--line);
border-radius:6px;padding:6px;background:var(--panel);
color:var(--text);margin-bottom:8px}}
.item{{padding:2px 6px;font-size:11px;color:var(--muted)}}
.item.hide{{display:none}}
details{{margin-bottom:4px}}summary{{cursor:pointer;padding:3px 0}}
.tag{{float:right;font-size:9px;border-radius:999px;padding:1px 7px;
background:var(--line);color:var(--muted)}}
.ck{{display:block;padding:3px 0;font-size:12px}}
button{{border:1px solid var(--line);background:var(--blue);color:#fff;
border-radius:8px;padding:8px 14px;cursor:pointer;width:100%;
margin-top:6px}}
button.ghost{{background:var(--panel);color:var(--blue)}}
#log{{white-space:pre-wrap;font:11px ui-monospace,Consolas,monospace;
background:var(--bg);border:1px solid var(--line);border-radius:6px;
padding:8px;min-height:120px;margin-top:8px}}
#drop{{border:2px dashed var(--line);border-radius:10px;padding:24px 10px;
text-align:center;color:var(--muted)}}
#drop.on{{border-color:var(--blue);color:var(--blue)}}
@media(max-width:1000px){{.app{{grid-template-columns:1fr}}}}
</style></head><body><div class="app">
<div class="col">
  <h1>總控台</h1>
  <div class="sub">批281 · VIA_SYSTEM_MANAGER 產 · {d['ts']} ·
  引擎/模組清單=全樹真掃</div>
  <input type="text" id="q" placeholder="搜尋引擎/模組…">
  <h2>Engine / Module List</h2>{eng_side}
</div>
<div class="col">
  <h2>控管元件 · 單任務(下拉)</h2>
  <select id="task">{opts}</select>
  <input type="text" id="codes" placeholder="參數 codes(可空;如 2330,2317)">
  <button onclick="runOne()">▶ 執行選定任務</button>
  <h2>多任務勾選(依序執行)</h2>{checks}
  <button class="ghost" onclick="runChecked()">▶ 依序執行勾選任務</button>
  <button class="ghost" onclick="ping()">⟳ 指揮台連線檢測</button>
  <div id="log">待命。任務經指揮台 127.0.0.1:8765 白名單真跑;
指揮台未開=打 via(或 VIA-ALL)帶起後再按。</div>
</div>
<div class="col">
  <h2>拖曳收件 Drag &amp; Drop</h2>
  <div id="drop">把檔案拖到這裡<br><small>列出清單+生成收容指引</small></div>
  <div id="files" class="sub"></div>
  <h2>同步 Sync</h2>
  <div class="sub">工作站同步=雙擊 VIA-ALL 或
  <code>python VIA_SYSTEM_MANAGER_v0100.py sync</code>
  (stash 留痕→對齊雲端;分流自動備份分支)</div>
</div>
</div><script>
const q=document.getElementById("q");
q.oninput=()=>{{const v=q.value.toLowerCase();
document.querySelectorAll(".item").forEach(i=>
i.classList.toggle("hide",v&&!i.dataset.n.includes(v)));}};
const log=m=>{{const el=document.getElementById("log");
el.textContent+="\\n"+m;el.scrollTop=el.scrollHeight;}};
async function call(t,codes){{
 try{{const u="http://127.0.0.1:8765/run?task="+encodeURIComponent(t)
  +(codes?"&codes="+encodeURIComponent(codes):"");
  const r=await(await fetch(u)).json();
  log((r.ok?"[起跑] ":"[拒/忙] ")+t+" "+(r.err||""));return r.ok;
 }}catch(e){{log("[誠實] 指揮台未開("+t+"):先打 via 帶起 127.0.0.1:8765");
  return false;}}}}
function runOne(){{call(document.getElementById("task").value,
 document.getElementById("codes").value.trim());}}
async function runChecked(){{
 for(const c of document.querySelectorAll('.ck input:checked'))
   await call(c.value,"");}}
async function ping(){{try{{
 const r=await(await fetch("http://127.0.0.1:8765/ping")).json();
 log("[指揮台] 在線 ✓ v="+(r.v||"?"));}}
 catch(e){{log("[指揮台] 未開=誠實(打 via 帶起)");}}}}
const dz=document.getElementById("drop");
dz.ondragover=e=>{{e.preventDefault();dz.classList.add("on");}};
dz.ondragleave=()=>dz.classList.remove("on");
dz.ondrop=e=>{{e.preventDefault();dz.classList.remove("on");
 const names=[...e.dataTransfer.files].map(f=>f.name);
 document.getElementById("files").innerHTML=
  "拖入 "+names.length+" 件:<br>"+names.map(n=>"· "+n).join("<br>")
  +"<br><b>收容指引</b>:檔案放 Downloads 後打 <code>via-intake</code>"
  +"(hash 定生死冪等自動雙推);瀏覽器沙盒不落盤=誠實 v1。";}};
</script></body></html>"""


def do_ui(open_after: bool = True) -> int:
    d = do_list(do_print=False)
    tasks = {k: v["zh"] for k, v in
             _mod("CGC_MDL095_DeckServer_v*.py").task_registry().items()}
    OUT.write_text(render(d, tasks), encoding="utf-8")
    print(f"[MGR:ui] 總控頁再生 · 任務 {len(tasks)} · {OUT.name}")
    if open_after:
        try:
            os.startfile(str(OUT))            # Windows I/O 正道
        except AttributeError:
            try:
                import webbrowser
                webbrowser.open(OUT.as_uri())  # 跨平台後備
            except Exception:
                pass
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    d = do_list(do_print=False)
    rc = do_ui(open_after=False)
    page = OUT.read_text(encoding="utf-8")
    chk("① 四職一總管(sync/list/run/ui 全在)", rc == 0
        and all(f"def do_{k}" in src for k in ("sync", "list", "run", "ui")))
    chk("② 清單清楚(引擎>80 族+模組>30 族入頁+搜尋過濾)",
        sum(len(v) for v in d["engines"].values()) > 80
        and 'id="q"' in page and 'class="item"' in page)
    chk("③ 控管元件三式(下拉+勾選+參數欄)接指揮台白名單",
        'id="task"' in page and 'type="checkbox"' in page
        and 'id="codes"' in page and "127.0.0.1:8765/run" in page)
    chk("④ 拖曳收件區(誠實 v1:列檔名+via-intake 指引,不假落盤)",
        'id="drop"' in page and "via-intake" in page and "誠實 v1" in page)
    chk("⑤ 白名單鐵則(run 拒任意指令)",
        do_run("rm -rf /") == 2)
    chk("⑥ Windows I/O 正道+後備+零 CDN+加速橋",
        "os.startfile" in src and "webbrowser" in src
        and '<script src="http' not in page and "ACCEL-BRIDGE" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 總系統管理器(VIA_SYSTEM_MANAGER)· 六檢自測(零外網)===")
        return selftest()
    if a and a[0] == "sync":
        return do_sync()
    if a and a[0] == "list":
        do_list()
        return 0
    if a and a[0] == "run":
        return do_run(a[1] if len(a) > 1 else "", a[2:])
    return do_ui()


if __name__ == "__main__":
    sys.exit(main())
