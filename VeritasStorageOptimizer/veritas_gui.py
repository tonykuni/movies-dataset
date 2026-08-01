#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Veritas Storage Optimizer - Desktop GUI (2026 Edition)
======================================================
EMBEDDED single-file system: stdlib http.server backend + animated HTML
front-end (VIA house style). Wraps the dual cleaning engines:

  - Python engine : engine/veritas_cleaner.py  (stdlib, streaming hash)
  - Node.js engine: engine/veritas_cleaner.js  (Node v18+, stream hash)

Rules honored:
  * Zero external dependencies (Python standard library only)
  * Dry-Run is the default mode; live delete needs an explicit switch +
    front-end confirm dialog
  * Root / home-ancestor targets are refused (system protection guard)
  * Append-only activity log + per-run audit log under logs/
  * Inline self-test: `python veritas_gui.py --self-test`

Usage:
  python veritas_gui.py                # serve on 127.0.0.1:8867 and open browser
  python veritas_gui.py --port 9000 --no-browser
  python veritas_gui.py --self-test
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
ENGINE_DIR = APP_ROOT / "engine"
PY_ENGINE = ENGINE_DIR / "veritas_cleaner.py"
JS_ENGINE = ENGINE_DIR / "veritas_cleaner.js"
LOG_DIR = APP_ROOT / "logs"
ACTIVITY_LOG = LOG_DIR / "gui_activity.log"

DEFAULT_PORT = 8867
ITEM_RE = re.compile(r"^\[(?P<reason>.+?)\] (?P<size>[\d.]+ [KMGTP]?B) -> (?P<path>.+)$")
EMPTY_DIR_RE = re.compile(r"^\[Empty Directory\] -> (?P<path>.+)$")
FREED_RE = re.compile(r"^(?:Total Space to Free|Potential Space Released): (?P<size>.+)$")


# ---- Logging (append-only) --------------------------------------------------
def write_log(msg: str, level: str = "INFO") -> None:
    LOG_DIR.mkdir(exist_ok=True)
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} | {level:<5} | {msg}"
    try:
        with open(ACTIVITY_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
    print(line, flush=True)


# ---- System protection guard -------------------------------------------------
def refuse_target(raw: str) -> str:
    """Return a refusal reason, or '' when the target is acceptable.

    Refuses filesystem roots and any ancestor of the home directory
    (e.g. '/', '/home', 'C:\\', 'C:\\Users') plus home itself — a cleanup
    sweep across those would be catastrophic. Subfolders of home are fine.
    """
    if not raw or not raw.strip():
        return "目標路徑為空"
    p = Path(raw).expanduser()
    try:
        p = p.resolve()
    except OSError:
        return "路徑無法解析"
    if not p.is_dir():
        return "目標資料夾不存在"
    if str(p) == p.anchor:
        return "拒絕:不可對檔案系統根目錄執行"
    home = Path.home().resolve()
    if p == home or p in home.parents:
        return "拒絕:不可對使用者家目錄或其上層執行(請選擇子資料夾)"
    return ""


# ---- Environment detection ---------------------------------------------------
def probe_version(cmd: list) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr) else ""
    except (OSError, subprocess.TimeoutExpired, IndexError):
        return ""


def get_env_snapshot() -> dict:
    node = shutil.which("node")
    return {
        "Python": sys.executable,
        "PythonVer": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "Node": node or "",
        "NodeVer": probe_version([node, "--version"]) if node else "",
        "PyEngine": PY_ENGINE.exists(),
        "JsEngine": JS_ENGINE.exists(),
        "GenTime": f"{datetime.now():%Y-%m-%d %H:%M:%S}",
    }


# ---- Engine invocation ---------------------------------------------------------
def parse_engine_output(stdout: str) -> dict:
    items, empty_dirs, freed = [], [], ""
    for line in stdout.splitlines():
        line = line.strip()
        m = EMPTY_DIR_RE.match(line)
        if m:
            empty_dirs.append(m.group("path"))
            continue
        m = ITEM_RE.match(line)
        if m:
            items.append({"reason": m.group("reason"), "size": m.group("size"), "path": m.group("path")})
            continue
        m = FREED_RE.match(line)
        if m:
            freed = m.group("size")
    return {"items": items, "emptyDirs": empty_dirs, "freedHuman": freed}


def run_engine(engine: str, target: str, max_mb: float, execute: bool) -> dict:
    started = time.monotonic()
    env = get_env_snapshot()
    if engine == "node" and not env["Node"]:
        return {"ok": False, "error": "系統未偵測到 node,請改用 Python 引擎"}
    reason = refuse_target(target)
    if reason:
        write_log(f"REFUSED target='{target}' reason='{reason}'", "WARN")
        return {"ok": False, "error": reason}

    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audit = LOG_DIR / f"veritas_audit_{engine}_{stamp}.log"
    target_path = str(Path(target).expanduser().resolve())

    if engine == "node":
        cmd = [env["Node"], str(JS_ENGINE)]
    else:
        cmd = [sys.executable, str(PY_ENGINE)]
    cmd += ["--dir", target_path, "--max-mb", str(max_mb), "--log", str(audit)]
    if execute:
        cmd.append("--execute")

    write_log(f"RUN engine={engine} execute={execute} maxMB={max_mb} target={target_path}")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=3600)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "引擎執行逾時 (1 小時)"}

    parsed = parse_engine_output(proc.stdout)
    result = {
        "ok": proc.returncode == 0,
        "execute": execute,
        "engine": engine,
        "target": target_path,
        "items": parsed["items"],
        "emptyDirs": parsed["emptyDirs"],
        "totalFiles": len(parsed["items"]),
        "freedHuman": parsed["freedHuman"],
        "logPath": str(audit),
        "elapsedSec": round(time.monotonic() - started, 2),
        "output": proc.stdout[-8000:],
        "stderr": proc.stderr[-2000:],
        "genTime": f"{datetime.now():%Y-%m-%d %H:%M:%S}",
    }
    verb = "CLEAN" if execute else "SCAN "
    write_log(f"{verb} engine={engine} files={result['totalFiles']} "
              f"freed={result['freedHuman'] or '0'} rc={proc.returncode} "
              f"elapsed={result['elapsedSec']}s")
    return result


# =============================================================================
#  FRONTEND (VIA house style: animated cards, mode switch, toast, progress)
# =============================================================================
HTML_TPL = r"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Veritas Storage Optimizer</title>
<style>
:root{--fg:#0f172a;--muted:#64748b;--line:#e6e8ee;--card:rgba(255,255,255,.78);--shadow:0 10px 30px rgba(15,23,42,.10);
--blue:#4C72B0;--green:#55A868;--red:#C44E52;--purple:#8172B2;--yellow:#CCB974;--cyan:#64B5CD;
--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans TC",Arial,sans-serif;--mono:ui-monospace,Menlo,Consolas,monospace;}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{font-family:var(--sans);color:var(--fg);position:relative;overflow-x:hidden;background:#f6f8fc;}
body::before{content:"";position:fixed;inset:-20%;z-index:-1;background:
radial-gradient(40% 40% at 15% 20%,rgba(76,114,176,.20),transparent 60%),
radial-gradient(40% 40% at 85% 15%,rgba(100,181,205,.18),transparent 60%),
radial-gradient(45% 45% at 75% 85%,rgba(129,114,178,.16),transparent 60%),
radial-gradient(40% 40% at 20% 90%,rgba(85,168,104,.15),transparent 60%);
filter:blur(10px);animation:drift 22s ease-in-out infinite alternate;}
@keyframes drift{0%{transform:translate3d(0,0,0) scale(1)}100%{transform:translate3d(0,-3%,0) scale(1.06)}}
.wrap{max-width:1020px;margin:0 auto;padding:24px}
.hdr{display:flex;align-items:center;gap:12px;margin-bottom:14px}
.live{width:12px;height:12px;border-radius:999px;background:var(--green);box-shadow:0 0 0 0 rgba(85,168,104,.6);animation:pulse 1.8s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(85,168,104,.55)}70%{box-shadow:0 0 0 12px rgba(85,168,104,0)}100%{box-shadow:0 0 0 0 rgba(85,168,104,0)}}
h1{font-size:19px;margin:0;letter-spacing:.2px}.meta{font-size:12px;color:var(--muted)}
.card{border:1px solid var(--line);border-radius:18px;background:var(--card);backdrop-filter:blur(14px);box-shadow:var(--shadow);
padding:18px;margin-bottom:16px;opacity:0;transform:translateY(10px);animation:rise .55s cubic-bezier(.2,.7,.2,1) forwards}
.card:nth-child(2){animation-delay:.05s}.card:nth-child(3){animation-delay:.10s}.card:nth-child(4){animation-delay:.15s}
@keyframes rise{to{opacity:1;transform:none}}
.card h2{margin:0 0 12px;font-size:15px}
.field{display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap}
.field label{font-size:13px;font-weight:600;min-width:110px}
input[type=text],input[type=number]{flex:1;min-width:220px;border:1px solid var(--line);border-radius:12px;padding:10px 13px;font-size:13px;font-family:var(--mono);background:#fff}
input[type=number]{flex:0 1 140px;min-width:110px}
input:focus{outline:2px solid rgba(76,114,176,.35);border-color:var(--blue)}
.badge{display:inline-flex;align-items:center;gap:6px;padding:4px 9px;border-radius:999px;border:1px solid var(--line);font-size:11px}
.badge.ok{border-color:rgba(85,168,104,.45);background:rgba(85,168,104,.10);color:#2f6e44}
.badge.warn{border-color:rgba(204,185,116,.55);background:rgba(204,185,116,.14);color:#7a6a2a}
.bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:8px}
button{cursor:pointer;border:1px solid var(--line);background:#fff;border-radius:13px;padding:11px 17px;font-size:14px;font-weight:700;position:relative;overflow:hidden;transition:transform .12s,border-color .2s,box-shadow .2s}
button:hover{border-color:var(--blue);box-shadow:0 4px 14px rgba(76,114,176,.18)}button:active{transform:scale(.97)}
button.primary{background:linear-gradient(135deg,#4C72B0,#5b86c9);color:#fff;border:none}
button:disabled{opacity:.5;cursor:not-allowed}
.rp{position:absolute;border-radius:50%;transform:scale(0);background:rgba(255,255,255,.5);animation:rp .6s ease-out}
@keyframes rp{to{transform:scale(3.5);opacity:0}}
.switch{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;background:#fff}
.switch button{border:none;border-radius:0;padding:9px 15px;font-size:13px}.switch button.act{background:var(--blue);color:#fff}
.switch button.actred{background:var(--red);color:#fff}
.prog{height:10px;border-radius:999px;background:rgba(15,23,42,.07);overflow:hidden;margin:10px 0 6px;display:none}
.prog>i{display:block;height:100%;width:0;background:linear-gradient(90deg,#4C72B0,#64B5CD);transition:width .4s ease}
.phase{font-size:12px;color:var(--muted);min-height:16px}
.result{font-family:var(--mono);font-size:12px;background:#0b1220;color:#e5e7eb;padding:14px;border-radius:13px;white-space:pre-wrap;max-height:380px;overflow:auto}
.muted{color:var(--muted);font-size:12px}
.stat{display:inline-block;margin-right:18px}.stat b{font-size:19px;color:var(--blue)}
.toast{position:fixed;right:22px;bottom:22px;background:#0b1220;color:#fff;padding:13px 17px;border-radius:13px;box-shadow:0 12px 30px rgba(0,0,0,.3);
font-size:13px;opacity:0;transform:translateY(16px);transition:.35s;z-index:9}.toast.show{opacity:1;transform:none}
.toast.ok{border-left:4px solid var(--green)}.toast.err{border-left:4px solid var(--red)}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}body::before{animation:none}}
</style></head><body><div class="wrap">

<div class="hdr"><div class="live"></div><div><h1>Veritas Storage Optimizer</h1>
<div class="meta">雙引擎儲存清理 · 2-Pass Hash 重複比對 · 串流雜湊 · 127.0.0.1:__PORT__</div></div></div>

<div class="card"><h2>引擎環境 (Engine Environment)</h2>
  <div id="env" class="muted">偵測中...</div>
</div>

<div class="card"><h2>掃描設定 (Scan Configuration)</h2>
  <div class="field"><label>目標資料夾</label><input type="text" id="dir" placeholder="/path/to/clean 或 C:\path\to\clean"></div>
  <div class="field"><label>大檔閾值 (MB)</label><input type="number" id="maxmb" value="200" min="1" step="50">
    <span class="muted">超過此容量的檔案將被標記刪除</span></div>
  <div class="field"><label>清理引擎</label>
    <div class="switch"><button id="engPy" class="act" onclick="setEngine('python')">Python (標準庫)</button><button id="engJs" onclick="setEngine('node')">Node.js (v18+)</button></div>
  </div>
  <div class="muted">保護名單:.git / .svn / .venv / node_modules / $RECYCLE.BIN / System Volume Information 一律跳過;根目錄與家目錄上層一律拒絕。</div>
</div>

<div class="card"><h2>執行</h2>
  <div class="bar">
    <span class="muted">模式:</span>
    <div class="switch"><button id="mScan" class="act" onclick="setExec(false)">僅掃描 Dry-Run (安全)</button><button id="mExec" onclick="setExec(true)">實體刪除</button></div>
    <button class="primary" id="btnRun" onclick="runClean()">▶ 開始掃描 (Dry-Run)</button>
  </div>
  <div class="prog" id="prog"><i id="progBar"></i></div>
  <div class="phase" id="phase"></div>
  <div style="margin:10px 0 8px">
    <span class="stat"><b id="stFiles">0</b> 標記檔案</span>
    <span class="stat"><b id="stDirs">0</b> 空資料夾</span>
    <span class="stat"><b id="stFreed">0 B</b> 可釋放容量</span>
  </div>
  <div class="result" id="out">就緒。先以 Dry-Run 檢視預計刪除清單,確認後再切換「實體刪除」。</div>
  <div class="muted" style="margin-top:8px" id="logpath">Log (append-only):__LOGPATH__</div>
</div>

</div>
<div class="toast" id="toast"></div>
<script>
"use strict";
var EXEC=false, ENGINE="python", ENV=null;
function $(s){return document.querySelector(s);}
function toast(msg,type){var t=$("#toast");t.textContent=msg;t.className="toast show "+(type||"ok");
  setTimeout(function(){t.className="toast "+(type||"ok");},2600);}
function phase(txt,pct){$("#phase").textContent=txt;$("#progBar").style.width=pct+"%";}
function setEngine(e){
  if(e==="node"&&ENV&&!ENV.Node){toast("未偵測到 node,無法切換","err");return;}
  ENGINE=e;$("#engPy").classList.toggle("act",e==="python");$("#engJs").classList.toggle("act",e==="node");}
function setExec(v){EXEC=v;
  $("#mScan").classList.toggle("act",!v);
  $("#mExec").classList.toggle("actred",v);$("#mExec").classList.toggle("act",false);
  $("#btnRun").textContent=v?"▶ 開始清理 (實體刪除)":"▶ 開始掃描 (Dry-Run)";}
async function loadEnv(){
  try{var r=await fetch("/api/env");ENV=await r.json();
    $("#env").innerHTML=
     '<span class="badge ok">Python: '+ENV.PythonVer+'</span> '+
     '<span class="badge '+(ENV.Node?"ok":"warn")+'">Node.js: '+(ENV.Node?ENV.NodeVer:"未偵測")+'</span> '+
     '<span class="badge '+(ENV.PyEngine?"ok":"warn")+'">Py Engine: '+(ENV.PyEngine?"就緒":"缺失")+'</span> '+
     '<span class="badge '+(ENV.JsEngine?"ok":"warn")+'">JS Engine: '+(ENV.JsEngine?"就緒":"缺失")+'</span>';
    if(!ENV.Node){$("#engJs").disabled=true;}
  }catch(e){$("#env").textContent="環境偵測失敗: "+e;}
}
async function runClean(){
  var dir=$("#dir").value.trim(), maxmb=parseFloat($("#maxmb").value);
  if(!dir){toast("請先輸入目標資料夾","err");return;}
  if(!(maxmb>0)){toast("大檔閾值必須為正數","err");return;}
  if(EXEC && !confirm("⚠ 實體刪除模式\n\n目標: "+dir+"\n將永久刪除暫存檔、超過 "+maxmb+" MB 的大檔與重複檔案。\n此動作無法復原。確定要繼續嗎?")) return;
  $("#btnRun").disabled=true;$("#prog").style.display="block";
  phase("階段 1/3 · 遍歷檔案樹 (2-Pass 候選收集)...",25);
  try{
    var r=await fetch("/api/run",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({dir:dir,maxMB:maxmb,engine:ENGINE,execute:EXEC})});
    phase("階段 2/3 · 串流 Hash 重複比對...",65);
    var d=await r.json();
    if(!d.ok){throw new Error(d.error||d.stderr||"engine failed");}
    $("#stFiles").textContent=d.totalFiles;
    $("#stDirs").textContent=d.emptyDirs.length;
    $("#stFreed").textContent=d.freedHuman||"0 B";
    var s="["+(d.execute?"EXECUTE":"DRY-RUN")+"] engine="+d.engine+"  "+d.genTime+"  ("+d.elapsedSec+"s)\n";
    s+="Target: "+d.target+"\n可釋放容量: "+(d.freedHuman||"0 B")+"\n\n[標記清單]\n";
    var max=Math.min(d.items.length,500);
    for(var i=0;i<max;i++){var it=d.items[i];s+="  ["+it.reason+"] "+it.size+"  "+it.path+"\n";}
    if(d.items.length>max){s+="  ... 其餘 "+(d.items.length-max)+" 筆詳見稽核日誌\n";}
    s+="\n[空資料夾] "+d.emptyDirs.length+" 個\n";
    s+="\n稽核日誌: "+d.logPath+"\n";
    $("#out").textContent=s;
    phase("階段 3/3 · 完成 ✓",100);
    toast((d.execute?"清理完成":"掃描完成")+" · "+d.totalFiles+" 檔案 · "+(d.freedHuman||"0 B"),"ok");
  }catch(e){$("#out").textContent="執行失敗: "+e.message;phase("失敗",0);toast("執行失敗","err");}
  setTimeout(function(){$("#prog").style.display="none";phase("",0);},1200);
  $("#btnRun").disabled=false;
}
document.addEventListener("click",function(ev){var b=ev.target.closest("button");if(!b)return;
  var c=document.createElement("span");c.className="rp";var z=Math.max(b.clientWidth,b.clientHeight);
  c.style.width=c.style.height=z+"px";c.style.left=(ev.offsetX-z/2)+"px";c.style.top=(ev.offsetY-z/2)+"px";
  b.appendChild(c);setTimeout(function(){c.remove();},600);});
loadEnv();
</script></body></html>
"""


def render_html(port: int) -> str:
    return HTML_TPL.replace("__PORT__", str(port)).replace("__LOGPATH__", str(ACTIVITY_LOG))


# =============================================================================
#  BACKEND (loopback http.server)
# =============================================================================
class VeritasHandler(BaseHTTPRequestHandler):
    server_version = "VeritasGUI/1.0"
    html_body = ""

    def log_message(self, fmt, *args):  # quiet default request spam
        pass

    def _send(self, body: str, ctype: str = "application/json; charset=utf-8", code: int = 200):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self._send(self.html_body, "text/html; charset=utf-8")
        elif self.path == "/api/env":
            self._send(json.dumps(get_env_snapshot()))
        else:
            self._send('{"error":"not found"}', code=404)

    def do_POST(self):
        if self.path != "/api/run":
            self._send('{"error":"not found"}', code=404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            result = run_engine(
                engine=str(req.get("engine", "python")),
                target=str(req.get("dir", "")),
                max_mb=float(req.get("maxMB", 200)),
                execute=bool(req.get("execute", False)),
            )
            self._send(json.dumps(result))
        except Exception as exc:  # surface as JSON, never a broken socket
            write_log(f"Request error /api/run: {exc}", "ERROR")
            self._send(json.dumps({"ok": False, "error": str(exc)}), code=500)


def serve(port: int, open_browser: bool) -> None:
    VeritasHandler.html_body = render_html(port)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), VeritasHandler)
    url = f"http://127.0.0.1:{port}/"
    write_log(f"Backend listening: {url}")
    print(f"\n==> Veritas Storage Optimizer is live at {url}")
    print("==> Ctrl+C in this window to stop the server.\n")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        write_log("Backend stopped.")


# =============================================================================
#  EMBEDDED SELF-TEST  (--self-test)
# =============================================================================
def run_self_test() -> bool:
    import tempfile

    print("\n== Veritas Storage Optimizer  Self-Test ==")
    tests = []

    def add(name, ok):
        tests.append((name, bool(ok)))

    html = render_html(9123)
    add("HTML tokens substituted", "__PORT__" not in html and "9123" in html)
    add("HTML structurally balanced", html.count("<html") == 1 and html.count("</html>") == 1)

    add("Guard rejects filesystem root", refuse_target(Path.home().anchor or "/") != "")
    add("Guard rejects home directory", refuse_target(str(Path.home())) != "")
    add("Guard rejects home ancestor", refuse_target(str(Path.home().parent)) != "")
    add("Guard rejects empty", refuse_target("") != "")

    sample = ("[Temp File] 10.00 B -> /x/a.tmp\n"
              "[Duplicate of a.dat] 50.00 KB -> /x/b.dat\n"
              "[Empty Directory] -> /x/empty\n"
              "Total Space to Free: 3.05 MB\n")
    parsed = parse_engine_output(sample)
    add("Parser extracts item rows", len(parsed["items"]) == 2 and parsed["items"][0]["reason"] == "Temp File")
    add("Parser extracts empty dirs", parsed["emptyDirs"] == ["/x/empty"])
    add("Parser extracts freed size", parsed["freedHuman"] == "3.05 MB")

    env = get_env_snapshot()
    add("Env detects Python version", bool(env["PythonVer"]))
    add("Env locates Python engine", env["PyEngine"])

    # Sandbox round-trip: dry-run marks but keeps files, execute removes them
    with tempfile.TemporaryDirectory(prefix="veritas_selftest_") as tmp:
        sand = Path(tmp) / "sand"
        sand.mkdir()
        (sand / "junk.tmp").write_text("x")
        (sand / "orig.dat").write_bytes(b"A" * 4096)
        (sand / "copy.dat").write_bytes(b"A" * 4096)
        guard_ok = refuse_target(str(sand)) == ""
        add("Guard accepts sandbox subdir", guard_ok)

        dry = run_engine("python", str(sand), 200, execute=False)
        add("Dry-run engine exits ok", dry.get("ok"))
        add("Dry-run marks temp + duplicate", dry.get("totalFiles") == 2)
        add("Dry-run leaves files intact", (sand / "junk.tmp").exists() and (sand / "copy.dat").exists())

        live = run_engine("python", str(sand), 200, execute=True)
        add("Execute engine exits ok", live.get("ok"))
        survivors = sum(1 for f in ("orig.dat", "copy.dat") if (sand / f).exists())
        add("Execute removes marked files",
            not (sand / "junk.tmp").exists() and survivors == 1)

    npass = sum(1 for _, ok in tests if ok)
    for name, ok in tests:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"-- {npass}/{len(tests)} PASS --")
    write_log(f"SELFTEST {npass}/{len(tests)} PASS")
    return npass == len(tests)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Veritas Storage Optimizer GUI 2026")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Loopback port (default 8867)")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open the browser")
    parser.add_argument("--self-test", action="store_true", help="Run embedded self-test and exit")
    args = parser.parse_args()

    if not PY_ENGINE.exists():
        print(f"[Fatal] Missing engine script: {PY_ENGINE}", file=sys.stderr)
        sys.exit(1)

    if args.self_test:
        sys.exit(0 if run_self_test() else 1)

    serve(args.port, open_browser=not args.no_browser)
