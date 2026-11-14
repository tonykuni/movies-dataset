#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_LakeConsole v0102 — 薄尾(v0101 · v0100 一字不動):收尾與驗證一鍵(本機 HTML 操作台)。

操作員 2026-11-14:「SELF TEST DEBUG OPTIMIZE … USER-TEST DEBUG ACTIVATE TEST DEBUG OUTPUT RESULTS VALIDATION & VERIFICATION
TEST DEBUG TIL USER CAN RUN THEM ON HTML U/I EASILY AND PERFECTLY」。

本版在 v0101(五系統啟動)之上加一排「收尾與驗證」按鈕,全部走白名單、各系統自己的入口、子行程執行:
  vdf_collect / vrn_collect     兩套管理器的自報(七處 · 健康 · 規範自查 · 啟動探測;只讀)
  vdf_health / vrn_health       兩套管理器的自檢
  vcgc_token                    VCGC 省 Token 卡(第一步)
  ssot_domains                  SSOT 領域覆蓋(15 領域 × 5 系統)
  graphify                      Graphify 車道(只讀圖譜 · 收據)
  vcgc_handoff                  交接檢查(只讀;紅就照實紅)
  vcgc_test_quick               VCGC 全功能串測(較久)
  vcgc_closeout                 收尾閘乾跑(只重測相依案;最久)
  鏈 verify_quick               自報 × 2 → 健康 × 2 → SSOT 覆蓋 → Graphify(幾分鐘內跑完)
  鏈 verify_full                五系統啟動 → verify_quick → 交接檢查(較久)
  鏈 closeout_3sys              三系統各自啟動(VCGC → VDF → VRN,各走自己的入口自測)→ 兩套管理器自報 + 自檢 → SSOT 覆蓋
命令列(操作員 2026-11-14「close out VCGC VRN VDF … HTML U/I will pop up after all of this procedure are done」):
  closeout [--no-open] [--quick]  照 closeout_3sys 逐步跑(不開伺服器)→ 寫 VIA_Reports/lake/CLOSEOUT_3SYS_latest.{json,html}
                                  → 全部跑完才自動開頁(--no-open 不開;--quick 略過三系統啟動,只跑自報 / 自檢 / 覆蓋)
燈:管理器的 rc 2 是「黃」(例:同意閘未開是操作員的手),不是行程失敗,所以這幾個動作的 rc 依它們自己的約定換燈;
其他動作照 v0100 規則(引擎自報 > rc;行程失敗不可能綠 / 黃)。
邊界:同 v0101(127.0.0.1 · 同源權杖 · 單通道 · 不出網 · 不代設同意閘 · 不寫他系統的冊)。
用法:python docs/handoff/ai/VIA_LakeConsole_v0102.py serve   (自動開頁;按「快速驗證」)
"""
from __future__ import annotations
# [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 零行為變更)
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
    VIA_ACCEL = None
# [VIA:ACCEL-BRIDGE:END]

import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

VERSION = "v0102"
ENGINE = "VIA_LakeConsole " + VERSION
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_FILE = max((p for p in HERE.glob("VIA_LakeConsole_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("VIA_LakeConsole_prior_for_v0102", _PRIOR_FILE)
Q = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = Q
_spec.loader.exec_module(Q)
P = Q.P                                   # v0100 本體(ACTIONS · CHAINS · step_lamp · serve 在這一層)
VIA = P.VIA

CONSOLE = "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
VDF_MGR = "functional modules/VDF/VDF_SystemManager_v*.py"
VRN_MGR = "functional modules/VRN/VRN_SystemManager_v*.py"
SSOT_ENG = "supportive modules/registry/VIA_VCGC_MDL262_SSOTConsistencyEngine_v*.py"
NEW_ACTIONS = {  # 動作 → (中文, 入口 glob, argv, 收據頁)
    "vdf_collect": ("VDF 管理器自報(七處 · 健康 · 規範 · 啟動探測)", VDF_MGR, ["collect"], None),
    "vrn_collect": ("VRN 管理器自報(七處 · 健康 · 規範)", VRN_MGR, ["collect"], None),
    "vdf_health": ("VDF 管理器自檢", VDF_MGR, ["health"], None),
    "vrn_health": ("VRN 管理器自檢", VRN_MGR, ["health"], None),
    "vcgc_token": ("VCGC 省 Token 卡(第一步)", CONSOLE, ["token"], None),
    "ssot_domains": ("SSOT 領域覆蓋(15 領域 × 5 系統)", SSOT_ENG, ["domains"], None),
    "graphify": ("Graphify 圖譜車道(只讀)", "docs/handoff/ai/VIA_GraphifyLane_v*.py", [], None),
    "vcgc_handoff": ("交接檢查(只讀)", CONSOLE, ["handoff", "check"], None),
    "vcgc_test_quick": ("VCGC 全功能串測(較久)", CONSOLE, ["test", "--quick"], None),
    "vcgc_closeout": ("收尾閘乾跑(只重測相依案 · 最久)", CONSOLE, ["closeout"], None),
}
TIMEOUTS = {"vdf_collect": 300, "vrn_collect": 300, "vdf_health": 300, "vrn_health": 300, "vcgc_token": 300, "ssot_domains": 600,
            "graphify": 900, "vcgc_handoff": 1200, "vcgc_test_quick": 3600, "vcgc_closeout": 5400}
#: rc 依該入口自己的約定換燈(管理器:0 綠 · 1 紅 · 2 黃 · 3 缺件;領域覆蓋:引擎說明「有缺口 rc 1」→ 黃,不是執行失敗)
RC_LAMP = {"vdf_collect": {0: "GREEN", 1: "RED", 2: "YELLOW", 3: "GRAY"}, "vrn_collect": {0: "GREEN", 1: "RED", 2: "YELLOW", 3: "GRAY"},
           "vdf_health": {0: "GREEN", 1: "RED", 2: "YELLOW"}, "vrn_health": {0: "GREEN", 1: "RED", 2: "YELLOW"},
           "ssot_domains": {0: "GREEN", 1: "YELLOW"}}
CHAINS = {"verify_quick": ("快速驗證(兩套管理器自報 + 自檢 · SSOT 覆蓋 · Graphify)", ["vdf_collect", "vrn_collect", "vdf_health", "vrn_health", "ssot_domains", "graphify"]),
          "verify_full": ("完整驗證(五系統啟動 → 快速驗證 → 交接檢查)", ["five_systems", "vdf_collect", "vrn_collect", "vdf_health", "vrn_health", "ssot_domains", "graphify", "vcgc_handoff"]),
          "closeout_3sys": ("三系統收尾(VCGC · VDF · VRN 各自啟動 → 自報 · 自檢 → SSOT 覆蓋)",
                            ["activate_vcgc", "activate_vdf", "activate_vrn2", "vdf_collect", "vrn_collect", "vdf_health", "vrn_health", "ssot_domains"])}

P.ACTIONS.update(NEW_ACTIONS)
P.CHAINS.update(CHAINS)
Q.TIMEOUTS.update(TIMEOUTS)
_prior_step_lamp = P.step_lamp


def step_lamp(via: Path, step: str, rc, out: str, receipt) -> str:
    """本版動作:引擎印了 [GREEN|YELLOW|RED|GRAY|PASS|FAIL] 就照它;沒有就照該入口的 rc 約定。其他動作照前版。"""
    if step in RC_LAMP and rc is not None:
        m = P._TAG_RX.search(out or "")
        if m:
            lamp = {"PASS": "GREEN", "FAIL": "RED"}.get(m.group(1), m.group(1))
            if rc in RC_LAMP[step] and lamp in ("GREEN", "YELLOW") and RC_LAMP[step][rc] in ("YELLOW", "RED", "GRAY"):
                lamp = RC_LAMP[step][rc]       # 標籤說綠、rc 說黃 / 紅 → 取較差
            return lamp if lamp in P.ORDER else "GRAY"
        return RC_LAMP[step].get(rc, "RED")
    return _prior_step_lamp(via, step, rc, out, receipt)


P.step_lamp = step_lamp

_BTNS = ('<section id="verify" class="panel"><h2>收尾與驗證(滑鼠一鍵 · 各走自己的入口 · 只讀為主)</h2><div class="row">'
         '<button class="primary sysbtn" data-act="closeout_3sys">三系統收尾</button><button class="sysbtn" data-act="verify_quick">快速驗證</button>'
         '<button class="sysbtn" data-act="vdf_collect">VDF 自報</button><button class="sysbtn" data-act="vrn_collect">VRN 自報</button>'
         '<button class="sysbtn" data-act="vdf_health">VDF 自檢</button><button class="sysbtn" data-act="vrn_health">VRN 自檢</button>'
         '<button class="sysbtn" data-act="ssot_domains">SSOT 覆蓋</button><button class="sysbtn" data-act="graphify">Graphify</button>'
         '<button class="sysbtn" data-act="vcgc_token">省 Token 卡</button><button class="sysbtn" data-act="vcgc_handoff">交接檢查</button>'
         '<button class="sysbtn" data-act="vcgc_test_quick">串測(較久)</button><button class="sysbtn" data-act="vcgc_closeout">收尾閘乾跑(最久)</button>'
         '<button class="sysbtn" data-act="verify_full">完整驗證(較久)</button></div>'
         '<div class="s">黃燈多半是操作員的手(例:同意閘未開、待裁定);紅燈點開見證表看最後幾行。單通道:一次跑一個動作。</div></section>')
_ANCHOR = '<section id="five" class="panel">'
_prior_page_html = P.page_html


def page_html(via: Path, root: Path, root_src: str, token: str) -> str:
    h = _prior_page_html(via, root, root_src, token)
    if _ANCHOR not in h:
        raise RuntimeError("v0101 頁面錨點不在:薄尾無法注入收尾與驗證按鈕列")
    return h.replace(_ANCHOR, _BTNS + _ANCHOR, 1).replace("· 五系統啟動</h1>", "· 五系統啟動 · 收尾驗證</h1>", 1)


P.page_html = page_html
P.ENGINE, P.VERSION = ENGINE, VERSION
serve = P.serve


def selftest() -> int:
    cp = subprocess.run([sys.executable, str(_PRIOR_FILE), "--selftest"], cwd=str(VIA), capture_output=True, text=True, encoding="utf-8", errors="replace",
                        timeout=1800, env={**os.environ, "PYTHONIOENCODING": "utf-8", "VIA_FROM_VCGC": "YES"})
    print((cp.stdout or "").rstrip()[-1500:])
    import urllib.request
    import urllib.error
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note and not cond else ""))

    def req(url, method="GET", body=None, headers=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        rq = urllib.request.Request(url, data=data, method=method, headers=headers or {})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(rq, timeout=30) as resp:
                raw = resp.read()
                return resp.status, json.loads(raw.decode("utf-8")) if "json" in resp.headers.get("Content-Type", "") else raw
        except urllib.error.HTTPError as ex:
            raw = ex.read()
            try:
                return ex.code, json.loads(raw.decode("utf-8"))
            except ValueError:
                return ex.code, raw

    print("[%s selftest]" % ENGINE)
    chk("① 前版 v0101 自測照過(乾淨子行程)", cp.returncode == 0, (cp.stdout or "")[-200:])
    chk("② 新動作 10 個都在白名單 · 兩條鏈在 · 入口都解析得到", all(k in P.ACTIONS for k in NEW_ACTIONS) and all(k in P.CHAINS for k in CHAINS)
        and all(P.tail_glob(VIA, v[1]) for v in NEW_ACTIONS.values()), [k for k, v in NEW_ACTIONS.items() if not P.tail_glob(VIA, v[1])])
    chk("③ 鏈的每一步都在白名單(含 closeout_3sys 三系統各自啟動)", all(s in P.ACTIONS for _, (_, steps) in CHAINS.items() for s in steps)
        and {"activate_vcgc", "activate_vdf", "activate_vrn2"} <= set(CHAINS["closeout_3sys"][1]))
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td:
        fake = Path(td)
        rep = {"engine": ENGINE, "at": "t", "lamp": "YELLOW", "verdict": "v", "why": "黃:vdf_collect", "secs": 1.0,
               "steps": [{"step": "vdf_collect", "zh": "z<", "system": "VDF", "lamp": "YELLOW", "rc": 2, "secs": 1.0, "tail": "a&b"}],
               "systems": {"VDF": {"lamp": "YELLOW", "notes": ["vdf_collect YELLOW"]}}}
        h = report_html(rep)
        chk("③b 收尾報告頁:燈 · 系統卡 · 步驟表都在,內容有跳脫(< & 不破版)", "三系統收尾報告" in h and "z&lt;" in h and "a&amp;b" in h and 'class="p YELLOW"' in h)
        os.environ["VIA_NO_OPEN"] = "1"
        chk("③c 沒有桌面時照實不開頁(不假裝開了)", _open(fake / "x.html", lambda *_: None) is False)
    chk("④ 燈:管理器 rc 2 → 黃(不是行程失敗);rc 1 → 紅;印了 [RED] 就紅", step_lamp(VIA, "vdf_collect", 2, "x", None) == "YELLOW"
        and step_lamp(VIA, "vdf_collect", 1, "x", None) == "RED" and step_lamp(VIA, "ssot_domains", 0, "[RED] x", None) == "RED"
        and step_lamp(VIA, "ssot_domains", 1, "[SSOT 領域涵蓋] YELLOW · 有缺口", None) == "YELLOW" and step_lamp(VIA, "ssot_domains", 124, "逾時", None) == "RED"
        and step_lamp(VIA, "vdf_collect", 2, "[GREEN] x", None) == "YELLOW")
    chk("⑤ 其他動作照前版規則(rc 1 + 自稱綠 → 紅)", step_lamp(VIA, "kit_selftest", 1, "[GREEN]", None) == "RED")
    ready = []
    srv = serve(VIA, None, 0, False, ready, block=False)
    import threading
    th = threading.Thread(target=srv.serve_forever, daemon=True)     # 同 v0100 / v0101 自測:serve(block=False) 只建好伺服器,要另起執行緒服務
    th.start()
    try:
        _, url, token, runner = ready[0]
        origin = url.rstrip("/")
        st, body = req(url)
        page = body.decode("utf-8") if isinstance(body, bytes) else ""
        chk("⑥ 頁面:收尾與驗證按鈕列在 · 下拉選單有新動作與兩條鏈", st == 200 and 'id="verify"' in page and 'value="verify_quick"' in page
            and all('value="%s"' % k in page for k in NEW_ACTIONS), st)
        good = {"Content-Type": "application/json", "Origin": origin, "Sec-Fetch-Site": "same-origin", "X-VIA-CSRF": token}
        st2, r = req(url + "run", "POST", {"action": "vrn_collect"}, good)
        rid = (r or {}).get("run_id") if isinstance(r, dict) else None
        s = {}
        for _ in range(3000):
            _, s = req(url + "status?run=" + str(rid))
            if isinstance(s, dict) and s.get("state") == "DONE":
                break
            time.sleep(0.1)
        step = ((s or {}).get("steps") or [{}])[0]
        chk("⑦ 實跑 vrn_collect:DONE · 燈是引擎自報(綠 / 黃)· 見證表有入口版號", isinstance(s, dict) and s.get("state") == "DONE" and step.get("lamp") in ("GREEN", "YELLOW")
            and (step.get("entry_version") or "").startswith("v"), (s.get("state") if isinstance(s, dict) else s, step.get("lamp"), step.get("tail", "")[-160:]))
        st3, r3 = req(url + "run", "POST", {"action": "nope_action"}, good)
        chk("⑧ 白名單外的動作 → 拒(不執行)", isinstance(r3, dict) and not r3.get("ok"), r3)
        st4, _ = req(url + "run", "POST", {"action": "vrn_collect"}, {"Content-Type": "application/json"})
        chk("⑨ 沒有同源權杖 → 拒", st4 in (401, 403), st4)
    finally:
        srv.shutdown()
        srv.server_close()
    n = sum(ok)
    print("[計] %s 自測 %d/%d %s" % (ENGINE, n, len(ok), "PASS" if n == len(ok) else "FAIL"))
    return 0 if n == len(ok) else 1


REPORT_JSON = "VIA_Reports/lake/CLOSEOUT_3SYS_latest.json"
REPORT_HTML = "VIA_Reports/lake/CLOSEOUT_3SYS_latest.html"
SYSTEM_OF = {"activate_vcgc": "VCGC", "activate_vdf": "VDF", "activate_vrn2": "VRN", "vdf_collect": "VDF", "vrn_collect": "VRN",
             "vdf_health": "VDF", "vrn_health": "VRN", "ssot_domains": "VCGC"}
_WORST = {"GREEN": 0, "YELLOW": 1, "GRAY": 2, "RED": 3}


def run_steps(via: Path, steps: list, echo=print) -> list:
    """逐步跑(單通道 · 子行程 · 各走自己的入口);每步的燈照 step_lamp(引擎自報 > 入口 rc 約定 > rc)。"""
    out = []
    for s in steps:
        zh, pat, args, receipt = P.ACTIONS[s]
        eng = P.tail_glob(via, pat)
        row = {"step": s, "zh": zh, "system": SYSTEM_OF.get(s, "VCGC"), "entry": eng.name if eng else None}
        if not eng:
            row.update(rc=127, lamp="RED", secs=0, tail="入口不在:" + pat)
            out.append(row)
            echo("  [RED   ] %-14s 入口不在" % s)
            continue
        argv = [sys.executable, str(eng)] + list(args)
        t0 = time.time()
        try:
            p = subprocess.run(argv, cwd=str(via), capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
                               timeout=TIMEOUTS.get(s) or Q.TIMEOUTS.get(s, 900), env={**os.environ, "PYTHONIOENCODING": "utf-8", "VIA_FROM_VCGC": "YES"})
            txt, rc = (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if (p.stderr or "").strip() else ""), p.returncode
        except subprocess.TimeoutExpired:
            txt, rc = "逾時", 124
        lines = [l for l in txt.splitlines() if l.strip() and not l.startswith("<unknown>")]
        tally = [l.strip() for l in lines if re.search(r"\[計\]|\[(GREEN|YELLOW|RED|PASS|FAIL)\]", l)]
        row.update(rc=rc, secs=round(time.time() - t0, 1), lamp=P.step_lamp(via, s, rc, txt, receipt),
                   tail=(tally[-1] if tally else (lines[-1] if lines else ""))[:300])
        out.append(row)
        echo("  [%-6s] %-14s %6.1fs · %s" % (row["lamp"], s, row["secs"], row["tail"][:110]))
    return out


def _esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def report_html(rep: dict) -> str:
    css = (":root{--bg:#f3f5f8;--card:#fff;--ink:#18212d;--mut:#5d6978;--line:#d5dbe3;--g:#17753f;--gb:#dff2e6;--y:#8a5a00;--yb:#f8ecd0;--r:#b3261e;--rb:#f9dedb;--n:#5d6978;--nb:#e9edf2}"
           "@media (prefers-color-scheme:dark){:root{--bg:#11161d;--card:#19202a;--ink:#e6ebf2;--mut:#98a4b3;--line:#2f3946;--g:#6fd598;--gb:#16311f;--y:#e6bb5c;--yb:#3a2e12;--r:#f2948b;--rb:#3d1c1a;--n:#98a4b3;--nb:#242d39;color-scheme:dark}}"
           "*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.6 'Noto Sans TC','PingFang TC','Microsoft JhengHei',system-ui,sans-serif}"
           ".w{max-width:1100px;margin:0 auto;padding:20px 16px 36px;display:flex;flex-direction:column;gap:16px}h1{font-size:21px;margin:0}.m{color:var(--mut);font-size:12.5px}"
           ".v{border-radius:10px;padding:14px 16px;border:1px solid var(--line)}.v b{font-size:19px}"
           ".GREEN{background:var(--gb);color:var(--g)}.YELLOW{background:var(--yb);color:var(--y)}.RED{background:var(--rb);color:var(--r)}.GRAY{background:var(--nb);color:var(--n)}"
           ".sys{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.c{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;min-width:0}"
           ".p{display:inline-block;border-radius:4px;padding:1px 8px;font-size:12px;font-weight:600}table{border-collapse:collapse;width:100%}th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;font-size:13px}"
           "th{color:var(--mut);font-weight:500}td.n{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;white-space:nowrap}.t{overflow-x:auto}.tl{word-break:break-word;color:var(--mut);font-size:12.5px}")
    zh = {"GREEN": "綠", "YELLOW": "黃", "RED": "紅", "GRAY": "灰"}
    cards = "".join('<div class="c"><b>%s</b> <span class="p %s">%s</span><div class="m">%s</div></div>' % (s, v["lamp"], zh.get(v["lamp"], v["lamp"]), _esc(" · ".join(v["notes"]))) for s, v in rep["systems"].items())
    rows = "".join('<tr><td>%s</td><td>%s</td><td><span class="p %s">%s</span></td><td class="n">%s</td><td class="n">%s</td><td class="tl">%s</td></tr>' % (
        _esc(r["system"]), _esc(r["zh"]), r["lamp"], zh.get(r["lamp"], r["lamp"]), r["rc"], r["secs"], _esc(r["tail"])) for r in rep["steps"])
    return ('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>三系統收尾報告</title><style>%s</style></head><body><div class="w">'
            '<h1>三系統收尾報告</h1><div class="m">%s · %s · 共 %d 步 · %.0f 秒</div>'
            '<div class="v %s"><b>%s</b><div>%s</div></div><div class="sys">%s</div>'
            '<div class="c t"><table><thead><tr><th>系統</th><th>步驟</th><th>燈</th><th>rc</th><th>秒</th><th>結果(最後一行判決)</th></tr></thead><tbody>%s</tbody></table></div>'
            '<div class="m">每步都是該系統自己的入口以子行程執行;燈 = 引擎自報(黃多半是操作員的手,例:同意閘未開)。這份報告只讀,不改任何系統的冊。</div></div></body></html>'
            % (css, _esc(rep["at"]), _esc(ENGINE), len(rep["steps"]), rep["secs"], rep["lamp"], _esc(rep["verdict"]), _esc(rep["why"]), cards, rows))


def closeout(via: Path = None, open_page: bool = True, quick: bool = False, echo=print) -> dict:
    via = via or VIA
    steps = [s for s in CHAINS["closeout_3sys"][1] if not (quick and s.startswith("activate_"))]
    echo("[%s] 三系統收尾 · %d 步(%s)" % (ENGINE, len(steps), "快速:略過啟動" if quick else "含三系統各自啟動"))
    t0 = time.time()
    res = run_steps(via, steps, echo)
    systems = {}
    for r in res:
        s = systems.setdefault(r["system"], {"lamp": "GREEN", "notes": []})
        if _WORST.get(r["lamp"], 2) > _WORST.get(s["lamp"], 2):
            s["lamp"] = r["lamp"]
        s["notes"].append("%s %s" % (r["step"], r["lamp"]))
    worst = max((_WORST.get(r["lamp"], 2) for r in res), default=3)
    lamp = ["GREEN", "YELLOW", "GRAY", "RED"][worst]
    verdict = {"GREEN": "三系統收尾:全部通過", "YELLOW": "三系統收尾:可用,有待操作員處理的黃燈", "GRAY": "三系統收尾:有步驟沒有資料", "RED": "三系統收尾:有紅燈,未驗收"}[lamp]
    why = "紅:" + "、".join(r["step"] for r in res if r["lamp"] == "RED") if lamp == "RED" else (
        "黃:" + "、".join(r["step"] for r in res if r["lamp"] == "YELLOW") if lamp == "YELLOW" else "每一步都綠")
    rep = {"engine": ENGINE, "at": P._now(), "lamp": lamp, "verdict": verdict, "why": why, "secs": round(time.time() - t0, 1), "steps": res, "systems": systems}
    (via / REPORT_JSON).parent.mkdir(parents=True, exist_ok=True)
    (via / REPORT_JSON).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    (via / REPORT_HTML).write_text(report_html(rep), encoding="utf-8")
    echo("[%s] %s · %s · %s" % (lamp, verdict, why, REPORT_HTML))
    if open_page:
        rep["opened"] = _open(via / REPORT_HTML, echo)
    return rep


def _open(path: Path, echo=print) -> bool:
    """全部跑完才開頁;沒有桌面(容器 / CI)就照實說沒開。"""
    headless = sys.platform.startswith("linux") and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    if headless or os.environ.get("VIA_NO_OPEN") == "1":
        echo("  [note] 這台沒有桌面(或 VIA_NO_OPEN=1),不跳頁;報告在 " + str(path))
        return False
    import webbrowser
    ok = webbrowser.open(path.resolve().as_uri())
    echo("  [note] 已開頁:" + str(path) if ok else "  [note] 開頁失敗,請手動開 " + str(path))
    return bool(ok)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args or (args and args[0] == "selftest"):
        return selftest()
    if args[:1] == ["closeout"]:
        rep = closeout(VIA, open_page="--no-open" not in args, quick="--quick" in args)
        return {"GREEN": 0, "YELLOW": 0, "GRAY": 2}.get(rep["lamp"], 1)
    return P.main(args)


def __getattr__(name):
    return getattr(Q, name)


if __name__ == "__main__":
    sys.exit(main())
