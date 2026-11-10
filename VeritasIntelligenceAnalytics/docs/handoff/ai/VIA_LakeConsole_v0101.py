#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_LakeConsole v0101 — 薄尾(v0100 一字不動):五系統啟動 via HTML U/I(操作員 2026-11-10「activate 5 system via html u/i and run」)。

① 動作白名單 +6:five_systems(VIA_FiveSystemConstitution run --apply:五系統各走自己的入口並行實測 · 記進度帳 · 矩陣 json/md/html)
   · activate_vcgc / activate_vdf / activate_vrn2 / activate_vqg / activate_vap(單系統走它自己的入口 selftest;L123:只跑、只讀它自報的結果,不寫他系統的檔);
   鏈 activate_all(逐一 VCGC → VDF → VRN-2 → VQG → VAP)。
② 燈號條 + 六盞:五系統總燈(憲法矩陣)+ 每系統一盞(實測燈 · 憲法性 · 進度 連綠 · 本台最近啟動);收據多 VIA_Reports/lake/FIVE_SYSTEMS_latest.{html,json,md}
   (五系統矩陣跑完由本台複製到 VCGC 自己的 VIA_Reports → /files 白名單可開;正本仍在 docs/handoff/ai)。
③ 頁面多「五系統」按鈕列(一鍵 = 下拉選好 + 執行;純滑鼠)· 仍是同一支 script;見證表每步的燈改用引擎自報的 step lamp(不只 rc)。
④ 子行程逾時依動作(五系統 1800 · VCGC 1500 · VDF / VRN-2 / VQG 900 · VAP 600 · 其餘照 v0100 900)· 子行程環境 VIA_FROM_VCGC=YES(五系統入口要)· 只看不寫 → five_systems 去掉 --apply。
⑤ 本台單系統啟動綁實跑的入口(帳 / 見證記 入口 · 版 · sha;燈號盞顯示實跑版與 sha;入口比矩陣新時矩陣的號 / 憲法性標成歷史值,不借舊版的號;Codex #625 P2)。
其餘(安全閘 · 單通道 · 入湖 · _inbox · /files · 自測 19 項)照 v0100;本版自測 = 前版鏈 + 本版 12 項。
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
except Exception:  # noqa: BLE001
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


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0101"
ENGINE = "VIA_LakeConsole " + VERSION
HERE = Path(__file__).resolve().parent
_PRIOR_FILE = HERE / "VIA_LakeConsole_v0100.py"
_spec = importlib.util.spec_from_file_location("VIA_LakeConsole_v0100", _PRIOR_FILE)
P = importlib.util.module_from_spec(_spec)
sys.modules["VIA_LakeConsole_v0100"] = P
_spec.loader.exec_module(P)
_prior_lamps, _prior_receipts, _prior_page_html = P.lamps, P.receipts, P.page_html
VIA, OUT_DIR, LABEL, ORDER = P.VIA, P.OUT_DIR, P.LABEL, P.ORDER

# ───────────────────────── ① 五系統動作(白名單 · 各走自己的入口) ─────────────────────────
FIVE = {  # 系統 → (入口尾版 glob, 它自己的 selftest argv, 逾時秒);與 VIA_FiveSystemConstitution v0100 SYSTEMS 同表
    "VCGC": ("supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py", ["--selftest"], 1500),
    "VDF": ("functional modules/VDF/VDF_SystemManager_v*.py", ["--selftest"], 900),
    "VRN2": ("functional modules/VRN/VRN_SystemManager_v*.py", ["--selftest"], 900),
    "VQG": ("functional modules/VQG/VQG_AllInOne_v*.py", ["selftest"], 900),
    "VAP": ("functional modules/VAP/VAP_SystemManager_v*.py", ["--selftest"], 600),
}
CONST_GLOB = "docs/handoff/ai/VIA_FiveSystemConstitution_v*.py"
CONST_OUT = {"json": "docs/handoff/ai/VIA_FiveSystemConstitution_latest.json", "md": "docs/handoff/ai/VIA_FiveSystemConstitution_latest.md", "html": "docs/handoff/ai/VIA_FiveSystemConstitution_UI.html"}
FIVE_OUT = {"json": "VIA_Reports/lake/FIVE_SYSTEMS_latest.json", "md": "VIA_Reports/lake/FIVE_SYSTEMS_latest.md", "html": "VIA_Reports/lake/FIVE_SYSTEMS_latest.html"}
NEW_ACTIONS = {"five_systems": ("五系統啟動 · 實跑(各走自己入口 · 並行 · 記進度帳 · 矩陣)", CONST_GLOB, ["run", "--apply"], FIVE_OUT["html"])}
for _s, (_g, _a, _t) in FIVE.items():
    NEW_ACTIONS["activate_" + _s.lower()] = ("啟動 %s(走它自己的入口 selftest)" % LABEL[_s], _g, _a, None)
TIMEOUTS = {"five_systems": 1800, **{"activate_" + s.lower(): t for s, (_, _, t) in FIVE.items()}}
P.ACTIONS.update(NEW_ACTIONS)
P.CHAINS["activate_all"] = ("啟動五系統(逐一走自己入口:VCGC → VDF → VRN-2 → VQG → VAP)", ["activate_" + s.lower() for s in FIVE])
P._RECEIPT_JSON[FIVE_OUT["html"]] = (FIVE_OUT["json"], lambda d: d.get("lamp"))
_SYS_KEY = {"VCGC": "VCGC", "VDF": "VDF", "VRN-2": "VRN2", "VRN2": "VRN2", "VQG": "VQG", "VAP": "VAP"}
_VER_RX = re.compile(r"_v(\d{4})\.py$")


def entry_meta(via: Path, argv: list | None) -> tuple[str | None, str | None, str | None]:
    """(入口相對路徑, 版號, sha8):記下「這一步真正跑的是哪支入口」(Codex #625 P2:本台啟動要綁到實跑的入口,不借矩陣當時的版 / 號)。"""
    if not argv or len(argv) < 2:
        return None, None, None
    p = Path(argv[1])
    try:
        rel = p.resolve().relative_to(via.resolve()).as_posix()
    except ValueError:
        rel = p.name
    m = _VER_RX.search(p.name)
    try:
        sha8 = hashlib.sha256(p.read_bytes()).hexdigest()[:8]
    except OSError:
        sha8 = None
    return rel, ("v" + m.group(1)) if m else None, sha8


def publish_five(via: Path, since: float) -> list[str]:
    """五系統矩陣正本在 docs/handoff/ai(引擎自己的 ALLOWED_WRITES);本台只把「本輪新產的」複製進 VCGC 自己的 VIA_Reports/lake 給 /files 開。"""
    out = []
    for k, src in CONST_OUT.items():
        sp = via / src
        if sp.is_file() and sp.stat().st_mtime >= since - 1:
            dp = via / FIVE_OUT[k]
            dp.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(sp, dp)
            out.append(FIVE_OUT[k])
    return out


class Runner(P.Runner):
    """v0100 Runner + 逾時依動作 · VIA_FROM_VCGC=YES · 只看不寫 → five_systems 去 --apply · 五系統跑完複製收據進 VIA_Reports/lake。"""

    def _work(self, run_id: str, steps: list[str], options: dict) -> None:
        rec = self.runs[run_id]
        self.logdir.mkdir(parents=True, exist_ok=True)
        worst = 0
        with open(rec["log"], "w", encoding="utf-8") as log:
            for s in steps:
                argv, zh = self._argv(s)
                st = {"step": s, "zh": zh, "rc": None, "secs": None, "tail": "", "receipt": None, "timeout": TIMEOUTS.get(s, 900)}
                st["entry"], st["entry_version"], st["entry_sha8"] = entry_meta(self.via, argv)
                rec["steps"].append(st)
                if argv is None:
                    st["rc"], st["tail"], st["lamp"] = 127, zh, "RED"
                    worst = 3
                    log.write("## %s · %s\n%s\n" % (s, zh, zh))
                    continue
                if options.get("dry") and s in ("toolboard", "lake_matrix"):
                    argv = argv + ["--no-write"]
                if options.get("dry") and s == "five_systems":
                    argv = [a for a in argv if a != "--apply"]  # 只看不寫:不記進度帳、不重生矩陣
                t0 = time.time()
                log.write("## %s · %s\n$ %s\n" % (s, zh, " ".join(argv)))
                log.flush()
                try:
                    p = subprocess.run(argv, cwd=str(self.via), capture_output=True, text=True, timeout=st["timeout"], stdin=subprocess.DEVNULL,
                                       env={**os.environ, "PYTHONIOENCODING": "utf-8", "VIA_FROM_VCGC": os.environ.get("VIA_FROM_VCGC", "YES")})
                    out = (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.stderr.strip() else "")
                    st["rc"] = p.returncode
                except subprocess.TimeoutExpired:
                    out, st["rc"] = "逾時 %ds" % st["timeout"], 124
                st["secs"] = round(time.time() - t0, 1)
                lines = [l for l in out.splitlines() if l.strip() and not l.startswith("<unknown>")]
                st["tail"] = "\n".join(lines[-14:])
                log.write(out + "\n")
                log.flush()
                rp = P.ACTIONS[s][3]
                if s == "five_systems":
                    copied = publish_five(self.via, t0)
                    log.write("[publish] %s\n" % (" · ".join(copied) or "本輪沒有新矩陣(只看不寫)"))
                    if not copied:
                        rp = None  # 沒新收據就不拿舊收據的燈
                if rp and (self.via / rp).exists():
                    st["receipt"] = rp
                    rec["receipts"].append(rp)
                st["lamp"] = P.step_lamp(self.via, s, st["rc"], out, rp)
                worst = max(worst, ORDER.get(st["lamp"], 2))
        rec["ended"] = P._now()
        rec["rc"] = max((s["rc"] or 0) for s in rec["steps"]) if rec["steps"] else 1
        rec["lamp"] = ["GREEN", "YELLOW", "GRAY", "RED"][worst]
        rec["state"] = "DONE"
        with open(self.ledger, "a", encoding="utf-8") as f:
            f.write(json.dumps({"at": rec["ended"], "run_id": run_id, "action": rec["action"], "rc": rec["rc"], "lamp": rec["lamp"],
                                "steps": [(s["step"], s["rc"], s["secs"], s.get("lamp"), s.get("entry"), s.get("entry_version"), s.get("entry_sha8")) for s in rec["steps"]], "options": rec["options"]}, ensure_ascii=False) + "\n")


P.Runner = Runner


# ───────────────────────── ② 燈號:五系統六盞 ─────────────────────────
def last_console_steps(via: Path) -> dict:
    """console_ledger.jsonl → {step: (at, lamp, entry, entry_version, entry_sha8)} 每步最近一次(本台啟動過的系統;帶實跑的入口)。"""
    out: dict = {}
    p = via / OUT_DIR / "console_ledger.jsonl"
    if not p.is_file():
        return out
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        for s in d.get("steps") or []:
            if isinstance(s, (list, tuple)) and len(s) >= 4 and s[3]:
                out[s[0]] = (d.get("at"), s[3], (s[4] if len(s) > 4 else None), (s[5] if len(s) > 5 else None), (s[6] if len(s) > 6 else None))
    return out


def lamps(via: Path, root: Path) -> list[dict]:
    rows = _prior_lamps(via, root)
    d = P._load(via / CONST_OUT["json"])
    last = last_console_steps(via)
    if isinstance(d, dict) and isinstance(d.get("systems"), list):
        c = d.get("counts") or {}
        at = d.get("generated_utc")
        rows.append({"key": "five", "title": "五系統(憲法矩陣)", "lamp": d.get("lamp", "GRAY"), "at": at,
                     "note": "實測綠 %s/%s · 憲法性 %s/%s · 空號 %s · 衝突 OPEN %s" % (c.get("run_green", "?"), c.get("systems", "?"), c.get("constitutional", "?"), c.get("systems", "?"), c.get("blank", "?"), c.get("conflict_open_total", "?"))})
        by = {r.get("sys"): r for r in d["systems"] if isinstance(r, dict)}
        for s in FIVE:
            r = by.get(LABEL[s]) or by.get(s) or {}
            if not r or r.get("external"):
                rows.append({"key": "sys_" + s.lower(), "title": "%s 啟動" % LABEL[s], "lamp": "GRAY", "at": None, "note": "矩陣沒有這系統的實測"})
                continue
            run, cons, prog = r.get("run") or {}, r.get("constitution") or {}, r.get("progress") or {}
            lamp, when, src = run.get("lamp", "GRAY"), at, "矩陣"
            ever, esha = r.get("entry_version"), r.get("entry_sha8")
            tile = {"key": "sys_" + s.lower(), "title": "%s 啟動" % LABEL[s], "source": "matrix", "entry_version": ever, "entry_sha8": esha}
            la = last.get("activate_" + s.lower())
            if la and la[0] and (not when or la[0] > when):
                lamp, when, src = la[1], la[0], "本台"
                ever, esha = la[3] or ever, la[4] or esha
                tile.update({"source": "console", "entry_version": ever, "entry_sha8": esha})
                same = bool(esha) and esha == r.get("entry_sha8")
                meta = ("號 %s · 憲法性 %s" % (r.get("number") or "空號", cons.get("status", "—"))) if same else \
                       ("矩陣 %s 時的號 %s · 憲法性 %s 為歷史值(實跑入口 sha %s ≠ 矩陣 %s;重跑五系統矩陣才綁新號)" % (at or "—", r.get("number") or "空號", cons.get("status", "—"), esha or "—", r.get("entry_sha8") or "—"))
                note = "%s · 入口 %s(sha %s · 實跑)· %s · 進度 %s/%s 連 %s" % (src, ever or "—", esha or "—", meta, prog.get("greens", 0), prog.get("runs", 0), prog.get("streak", 0))
            else:
                note = "%s · 入口 %s · 號 %s · 憲法性 %s · 進度 %s/%s 連 %s" % (src, ever or "—", r.get("number") or "空號", cons.get("status", "—"), prog.get("greens", 0), prog.get("runs", 0), prog.get("streak", 0))
            tile.update({"lamp": lamp, "at": when, "note": note})
            rows.append(tile)
    else:
        rows.append({"key": "five", "title": "五系統(憲法矩陣)", "lamp": "GRAY", "at": None, "note": "沒有收據(按「五系統啟動 · 實跑」)"})
        for s in FIVE:
            la = last.get("activate_" + s.lower())
            rows.append({"key": "sys_" + s.lower(), "title": "%s 啟動" % LABEL[s], "lamp": la[1] if la else "GRAY", "at": la[0] if la else None, "source": "console" if la else None,
                         "entry_version": la[3] if la else None, "entry_sha8": la[4] if la else None,
                         "note": ("本台 · 入口 %s(sha %s · 實跑)· 矩陣還沒跑,沒有號 / 憲法性" % (la[3] or "—", la[4] or "—")) if la else "還沒啟動"})
    return rows


def receipts(via: Path) -> list[dict]:
    out = _prior_receipts(via)
    for rel in (FIVE_OUT["html"], FIVE_OUT["md"], FIVE_OUT["json"]):
        p = via / rel
        if p.exists():
            out.append({"rel": rel, "bytes": p.stat().st_size, "mtime": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
    return out


# ───────────────────────── ③ 頁面:五系統按鈕列(同一支 script) ─────────────────────────
_BTNS = ('<section id="five" class="panel"><h2>五系統啟動(滑鼠一鍵 · 各走自己的入口 · VCGC 只跑不寫他系統)</h2><div class="row">'
         '<button class="primary sysbtn" data-act="five_systems">五系統並行實測 + 矩陣</button>'
         + "".join('<button class="sysbtn" data-act="activate_%s">啟動 %s</button>' % (s.lower(), LABEL[s]) for s in FIVE)
         + '<button class="sysbtn" data-act="activate_all">逐一啟動五系統</button></div>'
         '<div class="s">five_systems = VIA_FiveSystemConstitution run --apply(並行 · 記進度帳 · 矩陣 html / json / md 複製到 VIA_Reports/lake);單系統 = 該系統入口 selftest;勾「只看不寫」= 不記進度帳。</div></section>')
_ANCHOR = '<section id="lamps" class="strip"></section>'
_JS_TAIL = "  refreshLamps(); loadHistory();\n})();"
_JS_BTN = ("  [].slice.call(document.querySelectorAll('.sysbtn')).forEach(function(b){b.addEventListener('click',function(){$('act').value=b.dataset.act;$('run').click();});});\n")
if _JS_TAIL not in P.JS or "lamp(s.rc===0?'GREEN':'RED')" not in P.JS:
    raise RuntimeError("v0100 JS 錨點不在:薄尾無法注入五系統按鈕(v0100 應一字不動)")
P.JS = P.JS.replace("lamp(s.rc===0?'GREEN':'RED')", "lamp(s.lamp||(s.rc===0?'GREEN':'RED'))").replace(_JS_TAIL, _JS_BTN + _JS_TAIL)


def page_html(via: Path, root: Path, root_src: str, token: str) -> str:
    h = _prior_page_html(via, root, root_src, token)
    if _ANCHOR not in h:
        raise RuntimeError("v0100 頁面錨點不在:薄尾無法注入五系統按鈕列")
    return h.replace(_ANCHOR, _ANCHOR + _BTNS, 1).replace("VCGC 資料湖操作台</h1>", "VCGC 資料湖操作台 · 五系統啟動</h1>", 1)


P.lamps, P.receipts, P.page_html = lamps, receipts, page_html
P.ENGINE, P.VERSION = ENGINE, VERSION
serve, resolve_root, step_lamp, tail_glob = P.serve, P.resolve_root, P.step_lamp, P.tail_glob


# ───────────────────────── 自測(前版鏈 + 本版 10 項 · 真橋 · 零外網) ─────────────────────────
def selftest() -> int:
    # 前版鏈走乾淨子行程(本模組已把 v0100 的 ACTIONS / lamps / page 換成五系統版,行程內跑 v0100 自測會看到 10 盞燈而不是它預期的 4 盞)
    cp = subprocess.run([sys.executable, str(_PRIOR_FILE), "--selftest"], cwd=str(VIA), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900,
                        env={**os.environ, "PYTHONIOENCODING": "utf-8", "VIA_FROM_VCGC": "YES"})
    print((cp.stdout or "").rstrip())
    rc_prior = cp.returncode
    import urllib.request
    import urllib.error
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    def req(url, method="GET", body=None, headers=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        rq = urllib.request.Request(url, data=data, method=method, headers=headers or {})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(rq, timeout=30) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8")) if "json" in resp.headers.get("Content-Type", "") else resp.read()
        except urllib.error.HTTPError as ex:
            raw = ex.read()
            try:
                return ex.code, json.loads(raw.decode("utf-8"))
            except ValueError:
                return ex.code, raw

    def wait(url, rid, n=400):
        st = {}
        for _ in range(n):
            _, st = req(url + "status?run=" + rid)
            if st.get("state") == "DONE":
                break
            time.sleep(0.1)
        return st
    fake_const = r'''import json, sys, pathlib, hashlib
here = pathlib.Path(__file__).resolve().parent
root = here.parents[2]
apply = "--apply" in sys.argv
ENTRY = {"VCGC": "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0100.py", "VDF": "functional modules/VDF/VDF_SystemManager_v0100.py", "VRN-2": "functional modules/VRN/VRN_SystemManager_v0100.py", "VQG": "functional modules/VQG/VQG_AllInOne_v0100.py", "VAP": "functional modules/VAP/VAP_SystemManager_v0100.py"}
def sha8(rel):
    try:
        return hashlib.sha256((root / rel).read_bytes()).hexdigest()[:8]
    except OSError:
        return None
systems = [{"sys": s, "external": False, "entry": ENTRY[s], "entry_sha8": sha8(ENTRY[s]), "entry_version": "v0100", "number": "VIA-%s-MDL001" % s, "lamp": l,
            "constitution": {"lamp": "GREEN", "status": "CONSTITUTIONAL"}, "run": {"rc": 0 if l == "GREEN" else 1, "secs": 0.1, "lamp": l}, "progress": {"runs": 3, "greens": 3 if l == "GREEN" else 2, "streak": 3 if l == "GREEN" else 0}}
           for s, l in (("VCGC", "GREEN"), ("VDF", "GREEN"), ("VRN-2", "GREEN"), ("VQG", "RED"), ("VAP", "GREEN"))]
systems.append({"sys": "VRN-1", "external": True})
D = {"engine": "fake_const", "generated_utc": "2026-11-10T04:00:00Z", "lamp": "YELLOW", "counts": {"systems": 5, "run_green": 4, "constitutional": 5, "blank": 0, "conflict_open_total": 0}, "systems": systems}
print("[fake_const] 總燈 YELLOW · 實測綠 4/5")
if apply:
    (here / "VIA_FiveSystemConstitution_latest.json").write_text(json.dumps(D), encoding="utf-8")
    (here / "VIA_FiveSystemConstitution_latest.md").write_text("# fake\n", encoding="utf-8")
    (here / "VIA_FiveSystemConstitution_UI.html").write_text("<html>fake five</html>", encoding="utf-8")
else:
    print("  [dry] 沒有 --apply:不寫輸出、不記進度")
sys.exit(0)
'''
    with tempfile.TemporaryDirectory(prefix="via_console101_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        for sub in ("supportive modules/registry", "docs/handoff/ai", "functional modules/VDF", "functional modules/VRN", "functional modules/VQG", "functional modules/VAP", "VIA_Reports/backup"):
            (via / sub).mkdir(parents=True, exist_ok=True)
        kit = tail_glob(VIA, "supportive modules/VIA_ParquetLake_v*.py")
        (via / "supportive modules" / kit.name).write_text(kit.read_text(encoding="utf-8"), encoding="utf-8")
        (via / "VIA_Reports/backup/CHECK_latest.json").write_text(json.dumps({"lamp": "GREEN", "at": "2026-11-10T01:00:00Z", "meaning": "fixture"}), encoding="utf-8")
        (via / "docs/handoff/ai/VIA_FiveSystemConstitution_v0100.py").write_text(fake_const, encoding="utf-8")
        (via / "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0100.py").write_text(
            "import os, sys\nif os.environ.get('VIA_FROM_VCGC') != 'YES':\n    print('[FAIL] no VIA_FROM_VCGC'); sys.exit(3)\nprint('[PASS] fake VCGC console selftest'); sys.exit(0)\n", encoding="utf-8")
        (via / "functional modules/VDF/VDF_SystemManager_v0100.py").write_text("print('[PASS] fake VDF selftest')\n", encoding="utf-8")
        (via / "functional modules/VRN/VRN_SystemManager_v0100.py").write_text("print('fake VRN-2 selftest 5/5 (no tag)')\n", encoding="utf-8")
        (via / "functional modules/VQG/VQG_AllInOne_v0100.py").write_text("import sys\nprint('[FAIL] fake VQG selftest 11/12'); sys.exit(1)\n", encoding="utf-8")
        (via / "functional modules/VAP/VAP_SystemManager_v0100.py").write_text("print('[GREEN] fake VAP selftest')\n", encoding="utf-8")
        ready = []
        srv = serve(via, None, 0, False, ready, block=False)
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        try:
            _, url, token, runner = ready[0]
            origin = url.rstrip("/")
            good = {"Content-Type": "application/json", "Origin": origin, "Sec-Fetch-Site": "same-origin", "X-VIA-CSRF": token}
            code, page = req(url)
            html = page.decode("utf-8")
            btns = re.findall(r'class="(?:primary )?sysbtn" data-act="([a-z_0-9]+)"', html)
            chk("ⓐ 頁面:五系統按鈕列 7 顆(five_systems · 5 系統 · activate_all)全在白名單 · 仍是一支 script · 引擎名 v0101 · 下拉多 7 項",
                code == 200 and btns == ["five_systems", "activate_vcgc", "activate_vdf", "activate_vrn2", "activate_vqg", "activate_vap", "activate_all"]
                and all(b in P.ACTIONS or b in P.CHAINS for b in btns) and html.count("<script>") == 1 and ENGINE in html and html.count('<option value="activate_') == 6 and 'value="five_systems"' in html, btns)
            chk("ⓐ2 見證表每步的燈用引擎自報 step lamp(JS 注入)", "lamp(s.lamp||(s.rc===0?'GREEN':'RED'))" in html and "querySelectorAll('.sysbtn')" in html)
            code, d = req(url + "lamps")
            keys = [r["key"] for r in d["lamps"]]
            chk("ⓑ /lamps 跑前:四盞 + 五系統 1 + 每系統 5 = 10 盞 · 五系統 GRAY(沒收據)· 系統盞 GRAY 還沒啟動",
                code == 200 and len(keys) == 10 and keys[4] == "five" and keys[5:] == ["sys_vcgc", "sys_vdf", "sys_vrn2", "sys_vqg", "sys_vap"] and all(r["lamp"] == "GRAY" for r in d["lamps"][4:]), keys)
            code, d = req(url + "run", "POST", {"action": "five_systems", "options": {"dry": True}}, good)
            st = wait(url, d.get("run_id", ""))
            chk("ⓒ 五系統 只看不寫:argv 去 --apply · 引擎印 [dry] · 無收據 · 不複製 · 整件 GREEN(rc 0 無標籤)",
                code == 202 and st.get("state") == "DONE" and st["receipts"] == [] and "[dry]" in st["steps"][0]["tail"] and not (via / FIVE_OUT["json"]).exists() and st["lamp"] == "GREEN" and st["steps"][0]["timeout"] == 1800, {k: st.get(k) for k in ("lamp", "rc")})
            code, d = req(url + "run", "POST", {"action": "five_systems"}, good)
            st = wait(url, d.get("run_id", ""))
            chk("ⓓ 五系統 實跑:矩陣 json/md/html 複製進 VIA_Reports/lake · 收據 FIVE_SYSTEMS_latest.html · 步燈取矩陣 lamp YELLOW(rc 0 不假綠)· 整件 YELLOW",
                st.get("state") == "DONE" and st["rc"] == 0 and st["receipts"] == [FIVE_OUT["html"]] and st["steps"][0]["lamp"] == "YELLOW" and st["lamp"] == "YELLOW"
                and all((via / p).exists() for p in FIVE_OUT.values()), {k: st.get(k) for k in ("lamp", "rc", "receipts")})
            code, body = req(url + "files/" + FIVE_OUT["html"])
            chk("ⓔ /files 可開五系統矩陣(VIA_Reports/lake 白名單)· 收據表列出 3 份", code == 200 and b"fake five" in body and sum(1 for r in req(url + "lamps")[1]["receipts"] if "FIVE_SYSTEMS" in r["rel"]) == 3)
            _, d = req(url + "lamps")
            tiles = {r["key"]: r for r in d["lamps"]}
            chk("ⓕ /lamps 跑後:五系統 YELLOW · VCGC/VDF/VRN-2/VAP GREEN · VQG RED(來源 矩陣 · 註記 入口 / 號 / 憲法性 / 進度)",
                tiles["five"]["lamp"] == "YELLOW" and [tiles["sys_" + k]["lamp"] for k in ("vcgc", "vdf", "vrn2", "vqg", "vap")] == ["GREEN", "GREEN", "GREEN", "RED", "GREEN"]
                and tiles["sys_vqg"]["note"].startswith("矩陣") and "憲法性 CONSTITUTIONAL" in tiles["sys_vqg"]["note"], tiles["sys_vqg"]["note"])
            code, d = req(url + "run", "POST", {"action": "activate_all"}, good)
            st = wait(url, d.get("run_id", ""), 600)
            steps = {s["step"]: s for s in st.get("steps", [])}
            chk("ⓖ 鏈 activate_all:5 步各走自己入口 · VCGC 收到 VIA_FROM_VCGC=YES(rc 0)· VDF [PASS] GREEN · VRN-2 無標籤 rc 0 GREEN · VQG [FAIL] rc 1 RED · VAP [GREEN] · 整件 RED · 逾時依系統 1500/900/900/900/600",
                st.get("state") == "DONE" and len(steps) == 5 and steps["activate_vcgc"]["rc"] == 0 and steps["activate_vcgc"]["lamp"] == "GREEN" and steps["activate_vdf"]["lamp"] == "GREEN"
                and steps["activate_vrn2"]["lamp"] == "GREEN" and steps["activate_vqg"]["rc"] == 1 and steps["activate_vqg"]["lamp"] == "RED" and steps["activate_vap"]["lamp"] == "GREEN" and st["lamp"] == "RED"
                and [steps["activate_" + k]["timeout"] for k in ("vcgc", "vdf", "vrn2", "vqg", "vap")] == [1500, 900, 900, 900, 600], {k: (v["rc"], v.get("lamp")) for k, v in steps.items()})
            _, d = req(url + "lamps")
            tiles = {r["key"]: r for r in d["lamps"]}
            led = json.loads((via / OUT_DIR / "console_ledger.jsonl").read_text(encoding="utf-8").splitlines()[-1])["steps"]
            chk("ⓗ 本台啟動比矩陣新 → 系統盞改用本台結果(來源 本台 · 時間 = 帳上時間 · 入口 = 實跑的 v0100 + sha = 矩陣入口 → 號 / 憲法性照矩陣)· 帳每步帶燈 + 入口 + 版 + sha",
                all(tiles["sys_" + k]["note"].startswith("本台") and tiles["sys_" + k]["source"] == "console" for k in ("vcgc", "vdf", "vrn2", "vqg", "vap")) and tiles["sys_vqg"]["lamp"] == "RED" and tiles["sys_vcgc"]["at"] == st["ended"]
                and led[3][3] == "RED" and led[1][4] == "functional modules/VDF/VDF_SystemManager_v0100.py" and led[1][5] == "v0100" and len(led[1][6] or "") == 8
                and tiles["sys_vdf"]["entry_version"] == "v0100" and tiles["sys_vdf"]["entry_sha8"] == led[1][6]
                and "號 VIA-VDF-MDL001 · 憲法性 CONSTITUTIONAL" in tiles["sys_vdf"]["note"] and "歷史值" not in tiles["sys_vdf"]["note"], tiles["sys_vdf"]["note"])
            (via / "functional modules/VAP/VAP_SystemManager_v0101.py").write_text("print('[GREEN] fake VAP v0101 selftest')\n", encoding="utf-8")
            code, d = req(url + "run", "POST", {"action": "activate_vap"}, good)
            st4 = wait(url, d.get("run_id", ""))
            _, d = req(url + "lamps")
            t4 = {r["key"]: r for r in d["lamps"]}["sys_vap"]
            chk("ⓗ2 入口出新版(VAP v0101)後本台啟動:跑的是尾版 v0101 · 盞綁實跑入口(v0101 + 新 sha)· 矩陣的號 / 憲法性標成歷史值(sha ≠ 矩陣)· 不借舊版的號(Codex #625 P2)",
                st4.get("state") == "DONE" and st4["steps"][0]["entry_version"] == "v0101" and t4["entry_version"] == "v0101" and t4["entry_sha8"] == st4["steps"][0]["entry_sha8"]
                and "入口 v0101" in t4["note"] and "歷史值" in t4["note"] and "實跑入口 sha" in t4["note"] and "v0100" not in t4["note"].split("·")[1], t4["note"][:160])
            code, d = req(url + "run", "POST", {"action": "five_systems"}, {"Content-Type": "application/json"})
            code2, d2 = req(url + "run", "POST", {"action": "activate_vrn1"}, good)
            chk("ⓘ 安全不變:無同源 / 權杖 → 403 · VRN-1(外部倉 · 只讀)不在白名單 → 400", code == 403 and code2 == 400 and d2.get("kind") == "unknown_action")
        finally:
            srv.shutdown()
            srv.server_close()
    src = Path(__file__).read_text(encoding="utf-8")
    body_src = src.split("def selftest()")[0]
    chk("ⓙ 邊界:v0100 不就地改(薄尾 importlib)· 本版無 socket / requests 匯入 · 子行程只跑白名單尾版(sys.executable · 無 shell)· 五系統只跑不寫他系統(只複製自己的 VIA_Reports)",
        "VIA_LakeConsole_v0100.py" in src and not re.search(r"^\s*(import|from)\s+(requests|socket)\b", src, re.M) and not re.search(r"shell\s*=\s*True", body_src)
        and "self._argv(s)" in body_src and "shutil.copyfile(sp, dp)" in body_src and 'dp = via / FIVE_OUT[k]' in body_src)
    bad = len(ok) - sum(ok)
    print("[%s] %s selftest · 本版 %d/%d · 前版鏈 v0100 %s" % ("PASS" if not bad and rc_prior == 0 else "FAIL", ENGINE, sum(ok), len(ok), "PASS" if rc_prior == 0 else "FAIL"), flush=True)
    return 0 if not bad and rc_prior == 0 else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args or (args and args[0] == "selftest"):
        return selftest()
    return P.main(args)


def __getattr__(name):
    return getattr(P, name)


if __name__ == "__main__":
    sys.exit(main())
