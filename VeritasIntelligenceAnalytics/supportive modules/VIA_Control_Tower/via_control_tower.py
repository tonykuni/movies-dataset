#!/usr/bin/env python3
"""VIA Control Tower v001 · 本機 HTML 控制台(zero dependencies).

Serves a local control panel (127.0.0.1 only) with one-click buttons for
every VIA action: VDF intake, AutoPlot, VRN safe-probe / lanes / live run
(auto-picks the first existing PDF from the candidate list — no manual
path editing), and the Optimizer Suite tools. Each action runs in-process
via subprocess and streams its captured output back to the page.

Usage:  python via_control_tower.py [--base <VIA dir>] [--port 8765]
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VERSION = "v001"


def find_pwsh() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


class Tower:
    def __init__(self, base: Path):
        self.base = base
        self.repo = base.parent
        self.fm = base / "functional modules"
        self.sm = base / "supportive modules"
        self.py = sys.executable
        self.rpt = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "VIA_Reports"

    # ------------------------------------------------------------- helpers
    def run(self, cmd: list[str], timeout: int = 1800) -> str:
        try:
            p = subprocess.run(cmd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               cwd=self.repo, timeout=timeout)
            out = (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.stderr.strip() else "")
            return out + f"\n[exit={p.returncode}]"
        except Exception as exc:  # noqa: BLE001 — surfaced to the UI verbatim
            return f"[TOWER-ERROR] {exc}"

    def run_pwsh_code(self, code: str, timeout: int = 1800) -> str:
        pwsh = find_pwsh()
        if not pwsh:
            return "[TOWER-ERROR] pwsh/powershell not found on PATH"
        fd, tmp = tempfile.mkstemp(suffix=".ps1")
        os.close(fd)
        Path(tmp).write_text(code, encoding="utf-8-sig")
        try:
            return self.run([pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", tmp], timeout)
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    def patched(self, script: Path, replacements: dict[str, str]) -> str:
        code = script.read_text(encoding="utf-8", errors="replace")
        for pattern, value in replacements.items():
            code = re.sub(pattern, value.replace("\\", "\\\\"), code, count=1)
        return code

    def auto_pdf(self) -> str | None:
        cand = self.fm / "VRN" / "VRN-2_StockReportCandidatePaths.txt"
        if cand.is_file():
            for line in cand.read_text(encoding="utf-8", errors="replace").splitlines():
                p = line.strip().strip('"')
                if p.lower().endswith(".pdf") and Path(p).is_file():
                    return p
        return None

    # ------------------------------------------------------------- actions
    def act_vdf(self) -> str:
        return self.run([self.py, str(self.fm / "VDF" / "engine" / "vdf_movies_intake_v001.py"),
                         "--base", str(self.base), "--source", str(self.repo / "data"),
                         "--mode", "Refresh"])

    def act_autoplot(self) -> str:
        return self.run([self.py, str(self.fm / "VAP" / "engine" / "via_autoplot_engine_v001.py"),
                         "--base", str(self.base), "--auto", "--max-charts", "40"])

    def act_vrn_probe(self) -> str:
        pwsh = find_pwsh()
        if not pwsh:
            return "[TOWER-ERROR] pwsh not found"
        return self.run([pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass",
                         "-File", str(self.fm / "VRN" / "Invoke-VRN.ps1")])

    def act_vrn_lanes(self) -> str:
        vrn = self.fm / "VRN"
        out = []
        for lane in ("Start-VRN-Lane2-IOInventory.ps1", "Start-VRN-Lane3-EngineCapability.ps1"):
            code = self.patched(vrn / lane,
                                {r'\$RelatedPath = ".*?"': f'$RelatedPath = "{vrn}"'})
            out.append(f"===== {lane} =====\n" + self.run_pwsh_code(code))
        return "\n".join(out)

    def act_vrn_run(self) -> str:
        pdf = self.auto_pdf()
        if not pdf:
            return ("[TOWER] 候選清單中找不到仍存在的 PDF。\n"
                    "請把任一研報 PDF 路徑加入 functional modules/VRN/"
                    "VRN-2_StockReportCandidatePaths.txt 後重按。")
        cand = self.sm / "60_PowerShell_Entry_Internal" / "Invoke-VRN-MQ-NoOCR-Staging-v222.ps1"
        rules = self.sm / "70_VRN_Rules"
        code = self.patched(cand, {
            r'\$BrokerHelper\s*=\s*".*?"':
                f'$BrokerHelper = "{rules / "VIS_VRN_BrokerAlias_Compatibility_v0222.py"}"',
            r'\$FallbackHelper\s*=\s*".*?"':
                f'$FallbackHelper = "{rules / "VIS_VRN_PDFTextLayerFallbackPlan_v0222.py"}"',
            r'\$TargetFile = ".*?"': f'$TargetFile = "{pdf}"',
        })
        return f"[TOWER] auto-picked PDF: {pdf}\n\n" + self.run_pwsh_code(code)

    def act_tool(self, name: str) -> str:
        opt = self.sm / "VIA_Optimizer_Suite"
        self.rpt.mkdir(parents=True, exist_ok=True)
        bundle = self.sm / "VIA_Standalone_Package_v0102" / "_supportive_bundle" / "powershell"
        pwsh = find_pwsh()
        if not pwsh:
            return "[TOWER-ERROR] pwsh not found"
        cmds = {
            "audit": [pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                      str(opt / "VIA_TurboOptimizer_v3.3_OneDrive_Coding_AISafeAudit.ps1"),
                      "-OutputRoot", str(self.rpt / "_disk_audit")],
            "panorama": [pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                         str(opt / "Invoke-VIA-FirstSightPanorama-GovernanceMatrix-v0100.ps1"),
                         "-BaseRoot", str(self.base),
                         "-DownloadRoot", str(Path.home() / "Downloads")],
            "polyglot": [pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                         str(opt / "Invoke-VIA-SafePolyglotOptimizer-AIO-v0102.ps1"),
                         "-SupportiveModulesRoot", str(self.sm),
                         "-NexusCorePath", str(bundle / "Invoke-VeritasNexusCore.ps1"),
                         "-PolyglotPath", str(bundle / "Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1"),
                         "-OutputRoot", str(self.rpt / "_polyglot"), "-SelfTest"],
        }
        return self.run(cmds[name], timeout=3600)

    def act_open(self, what: str) -> str:
        targets = {
            "workbench": self.fm / "VAP" / "ui" / "VAP_Workbench_v010.html",
            "charts": self.base / "VAP" / "output" / "index.html",
        }
        t = targets[what]
        if not t.exists():
            return f"[TOWER] 檔案不存在(先跑 AutoPlot):{t}"
        if hasattr(os, "startfile"):
            os.startfile(t)  # type: ignore[attr-defined]
            return f"[TOWER] opened {t}"
        return f"[TOWER] 請手動開啟:{t}"


ACTIONS = {
    "vdf": ("VDF Intake · Refresh", lambda t: t.act_vdf()),
    "autoplot": ("AutoPlot · 全配對繪圖", lambda t: t.act_autoplot()),
    "vrn_probe": ("VRN · Guarded SAFE PROBE", lambda t: t.act_vrn_probe()),
    "vrn_lanes": ("VRN · Lane2+Lane3 預檢", lambda t: t.act_vrn_lanes()),
    "vrn_run": ("VRN · 實彈 No-OCR Staging(自動選 PDF)", lambda t: t.act_vrn_run()),
    "audit": ("SafeAudit 磁碟稽核(無刪除)", lambda t: t.act_tool("audit")),
    "panorama": ("FirstSight 全景矩陣(唯讀)", lambda t: t.act_tool("panorama")),
    "polyglot": ("Polyglot AIO(僅報告)", lambda t: t.act_tool("polyglot")),
    "open_workbench": ("開啟 Workbench v010", lambda t: t.act_open("workbench")),
    "open_charts": ("開啟圖庫索引", lambda t: t.act_open("charts")),
}

PAGE = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA · Control Tower __VER__</title>
<style>
:root{--bg:#f2f1ec;--paper:#fff;--ink:#1b1a17;--ink2:#3a3f3e;--mut:#6b6860;
 --line:#dcdad3;--seal:#9e2b25;--teal:#3d8f8f;--violet:#7a6daa;
 --mono:"SFMono-Regular",Consolas,monospace;
 --sans:"Microsoft JhengHei","Segoe UI",system-ui,sans-serif}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);font-family:var(--sans);color:var(--ink);min-height:100vh}
.mast{background:#fff;display:flex;align-items:center;gap:21px;padding:11px 40px 10px}
.mast .seal{width:46px;height:46px;background:var(--seal);color:#f2f1ec;display:flex;
 align-items:center;justify-content:center;font-family:serif;font-size:26px;border-radius:4px}
.mast .wm{font-family:Georgia,serif;font-size:22px;letter-spacing:.1em;color:var(--ink2);white-space:nowrap}
.mast .sub{font-family:var(--mono);font-size:8.5px;letter-spacing:.36em;color:var(--mut);text-transform:uppercase}
.rule{height:1px;background:linear-gradient(to right,var(--violet) 0 34px,rgba(27,26,23,.14) 34px 100%)}
main{max-width:1100px;margin:0 auto;padding:22px 20px 40px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px;margin-bottom:18px}
button{display:flex;flex-direction:column;gap:4px;text-align:left;padding:13px 15px;background:var(--paper);
 border:1px solid var(--line);border-radius:8px;cursor:pointer;font-family:var(--sans);
 transition:transform .15s,box-shadow .15s,border-color .15s}
button:hover{transform:translateY(-2px);border-color:var(--teal);box-shadow:0 8px 24px -12px rgba(27,26,23,.25)}
button:active{transform:scale(.97)}
button.busy{opacity:.5;pointer-events:none}
button .k{font:700 10px var(--mono);letter-spacing:.1em;color:var(--teal);text-transform:uppercase}
button .t{font-size:13.5px;color:var(--ink)}
button.danger .k{color:var(--seal)}
#log{background:#1b1a17;color:#e8e6df;border-radius:8px;padding:16px 18px;font:12px/1.6 var(--mono);
 white-space:pre-wrap;word-break:break-all;min-height:180px;max-height:55vh;overflow:auto}
#status{font:700 11px var(--mono);letter-spacing:.1em;color:var(--mut);margin:0 0 8px;text-transform:uppercase}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style></head><body>
<div class="mast"><div class="seal">理</div>
 <div><div class="wm">VIA CONTROL TOWER</div>
 <div class="sub">Veritas Intelligence Analytics · one-click actions · 127.0.0.1 only</div></div></div>
<div class="rule"></div>
<main>
 <div class="grid" id="grid"></div>
 <p id="status">READY</p>
 <div id="log">按任意按鈕執行動作;輸出即時顯示於此。</div>
</main>
<script>
const ACTIONS = __ACTIONS__;
const grid = document.getElementById('grid'), log = document.getElementById('log'),
      status = document.getElementById('status');
for (const [key, label] of Object.entries(ACTIONS)) {
  const b = document.createElement('button');
  if (key === 'vrn_run' || key === 'audit') b.classList.add('danger');
  b.innerHTML = '<span class="k">' + key.replace('_',' ') + '</span><span class="t">' + label + '</span>';
  b.onclick = async () => {
    document.querySelectorAll('button').forEach(x => x.classList.add('busy'));
    status.textContent = 'RUNNING · ' + label;
    log.textContent = '[' + new Date().toLocaleTimeString() + '] ' + label + ' …\\n';
    try {
      const r = await fetch('/run/' + key, {method: 'POST'});
      log.textContent += await r.text();
    } catch (e) { log.textContent += '[FETCH-ERROR] ' + e; }
    status.textContent = 'READY';
    document.querySelectorAll('button').forEach(x => x.classList.remove('busy'));
    log.scrollTop = log.scrollHeight;
  };
  grid.appendChild(b);
}
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    tower: Tower

    def log_message(self, *_):  # quiet
        pass

    def _send(self, body: str, ctype: str = "text/plain; charset=utf-8", code: int = 200):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            labels = {k: v[0] for k, v in ACTIONS.items()}
            page = (PAGE.replace("__VER__", VERSION)
                        .replace("__ACTIONS__", json.dumps(labels, ensure_ascii=False)))
            self._send(page, "text/html; charset=utf-8")
        else:
            self._send("not found", code=404)

    def do_POST(self):
        m = re.fullmatch(r"/run/([a-z_]+)", self.path)
        if not m or m.group(1) not in ACTIONS:
            self._send("unknown action", code=404)
            return
        label, fn = ACTIONS[m.group(1)]
        self._send(fn(self.tower))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    base = Path(args.base).resolve()
    if not (base / "functional modules").is_dir():
        print(f"[TOWER] RED base invalid: {base}")
        return 2
    Handler.tower = Tower(base)
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"[TOWER] VIA Control Tower {VERSION} · http://127.0.0.1:{args.port} · base={base}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
