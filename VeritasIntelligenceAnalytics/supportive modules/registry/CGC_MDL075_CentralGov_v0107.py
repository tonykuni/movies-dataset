#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL075_CentralGov v0107 — 薄尾:主控台 UI 規格補齊 + 函式庫四分區 + 加速器實況 + SSOT 冊 Hydra(TOOL-063)

操作員令(2026-11-14):啟動「VIA Central Governance Console:全自動沙盒測試修正治理系統」,啟用全部加速器,
掛中央 SSOT 規範庫與同義字 / Regex 治理中心,三輪全景;HTML 矩陣字體 11px、table-layout:auto、
word-wrap:break-word、四大分區、動態進度條 + 動態說明;函式庫依 MODULE / ENGINE / FUNCTION-LIB / OTHERS
四分區管控,依衝突風險建議隔離插槽(via_core · via_lib_plotly_v5 · via_engine_cuda12 …),Base 極簡。
v0100 … v0106 一字不動;六條獨立流程(P1–P5 并行唯讀 + P6 join)照 v0106 跑,本版只加:
  ① UI:字體 11px、td/th 加 word-wrap:break-word;頁首「動態進度條 + 動態說明」照本輪實測流程逐步重播
     (每步的名稱 · 狀態 · 秒數都是這一輪的實測值,不是假動畫)。
  ② 函式庫四分區:MODULE(plotly · dash · pandas · numpy · pyarrow)· ENGINE(pydantic · networkx · torch · ruff)·
     FUNCTION-LIB(grpcio · cryptography · beautifulsoup4 · cffi)· OTHERS(uv · psutil);
     版本只讀 importlib.metadata(不 import、不安裝);隔離插槽是建議,不建立 —— 裝套件 / 建環境
     一律走 VCGC InstallGate(IFC-004),本主控台不 pip、不 uv、不開 venv。
  ③ 加速器實況:Python 線 = SuperAccel(Celeritas 尾版)啟用結果(本行程內套最大加速;可用函式庫數 · 缺的照列);
     PowerShell 線 = 20 加速器冊(VIA_PS_Accel_Module)要 pwsh,沒有就照實標 NO_PWSH。
  ④ Hydra:v0106 的 Hydra 節點靠介面冊內部邊,常是 0;本版加讀 VCGC 的 SSOT 引擎全景
     (CGC_MDL253 ssot map 輸出的 SSOT_ENGINE_MAP_latest.json):一本冊被越多系統 / 引擎讀寫 = 越高耦合,
     只出重構建議,不盲修(Zero-Hydra)。全景檔不在就照實寫「無資料」。
只讀分析;寫檔只在 VIA_Reports(UI 與存證)與 v0106 原有的中央同義字冊「缺才補」;零網路;不碰 TA-Lib。
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

import importlib.metadata as _md
import importlib.util
import json
import re
import shutil
import sys
import tempfile
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL075_CentralGov"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0107(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0107(p) < _vnum_v0107(__file__)), key=_vnum_v0107)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0106(本體;六流程)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


VIA = PRIOR.VIA
REPORTS = PRIOR.REPORTS
SSOT_MAP = REPORTS / "vcgc" / "ssot_engine_map" / "SSOT_ENGINE_MAP_latest.json"
# 操作員令的四分區(2026-11-14);插槽 = 依衝突風險的建議隔離位(不建立)
LIB_PARTITIONS = {
    "MODULE": (("plotly", "via_lib_plotly_v{major}"), ("dash", "via_lib_plotly_v{major}"), ("pandas", "via_core"),
               ("numpy", "via_core"), ("pyarrow", "via_core")),
    "ENGINE": (("pydantic", "via_core"), ("networkx", "via_core"), ("torch", "via_engine_cuda12"), ("ruff", "via_tools")),
    "FUNCTION-LIB": (("grpcio", "via_lib_native"), ("cryptography", "via_lib_native"), ("beautifulsoup4", "via_core"),
                     ("cffi", "via_lib_native")),
    "OTHERS": (("uv", "base"), ("psutil", "base")),
}
SLOT_WHY = {
    "base": "Base 極簡:只放排程 / 環境建置器",
    "via_core": "純 Python、版本相容面寬 → 共用核心插槽",
    "via_lib_plotly_v{major}": "plotly / dash 主版本互鎖 → 依主版本獨立插槽",
    "via_engine_cuda12": "GPU 版 torch 綁 CUDA 12 → 獨立重型插槽,不進 Base",
    "via_lib_native": "原生編譯(C 擴充 / gRPC / OpenSSL)→ 隔離 ABI 衝突",
    "via_tools": "開發工具(lint)→ 不進執行期",
}


def lib_inventory() -> list:
    """四分區函式庫:版本只讀 metadata(不 import、不安裝);uv 另看執行檔。"""
    def ver_of(dist):
        try:
            return _md.version(dist)
        except _md.PackageNotFoundError:
            return ""

    pmajor = (ver_of("plotly") or ver_of("dash") or "5").split(".")[0]   # plotly / dash 共一個插槽:跟 plotly 主版本走
    rows = []
    for part, libs in LIB_PARTITIONS.items():
        for dist, slot in libs:
            ver = ver_of(dist)
            exe = shutil.which(dist) if dist == "uv" else None
            s = slot.format(major=pmajor)
            state = "INSTALLED" if (ver or exe) else "MISSING"
            rows.append({"partition": part, "lib": dist, "version": ver or ("(執行檔)" if exe else ""), "state": state,
                         "slot": s, "slot_why": SLOT_WHY.get(slot, ""), "how": "" if state == "INSTALLED" else "VCGC InstallGate(IFC-004)申請"})
    return rows


def accel_status(apply_limits: bool = True) -> dict:
    """加速器實況:Python 線 SuperAccel(Celeritas)啟用;PowerShell 線 20 加速器冊要 pwsh。"""
    out = {"python": {"state": "ABSENT", "detail": ""}, "ps": {"state": "", "detail": ""}, "roster": []}
    acc = globals().get("VIA_ACCEL")
    if acc is not None and hasattr(acc, "activate"):
        try:
            a = acc.activate(apply_limits=apply_limits)
            out["python"] = {"state": "ACTIVE" if a.get("celeritas") else "ABSENT", "libs_available": a.get("libs_available", 0),
                             "libs_total": a.get("libs_total", 0), "capability_real": a.get("capability_real", 0),
                             "capability_total": a.get("capability_total", 0), "thread_budget": a.get("thread_budget"),
                             "mode": a.get("mode"), "applied": bool(a.get("applied")) and "err" not in (a.get("applied") or {}),
                             "missing": list(a.get("missing") or [])[:30], "detail": a.get("err") or ""}
        except Exception as exc:  # noqa: BLE001 — 加速器啟用失敗照實記,不中斷主控台
            out["python"] = {"state": "ERROR", "detail": f"{type(exc).__name__}: {str(exc)[:120]}"}
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    ps_mod = VIA / "supportive modules" / "VIA_PS_Accel_Module.ps1"
    out["ps"] = {"state": "READY" if (pwsh and ps_mod.is_file()) else ("NO_PWSH" if ps_mod.is_file() else "MODULE_MISSING"),
                 "detail": (pwsh or "沒有 pwsh / powershell(容器)") + " · " + ("VIA_PS_Accel_Module.ps1 在" if ps_mod.is_file() else "模組不在")}
    out["roster"] = [list(r) for r in getattr(PRIOR, "ACCELERATORS", [])]
    return out


def hydra_from_ssot_map(path: Path | None = None, top: int = 12) -> dict:
    """SSOT 冊高耦合節點(讀 VCGC SSOT 引擎全景輸出;只出建議,不盲修)。"""
    p = Path(path or SSOT_MAP)
    if not p.is_file():
        return {"source": str(p), "at": "", "nodes": [], "note": "SSOT 引擎全景輸出不在(先跑 via-vcgc run CGC_MDL253_ToolingInventory ssot)"}
    try:
        m = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"source": str(p), "at": "", "nodes": [], "note": f"讀不到:{type(exc).__name__}"}
    nodes = []
    for b in m.get("books") or []:
        ns, ne, nw = len(b.get("systems") or []), len(b.get("engines") or []), int(b.get("write") or 0)
        score = ns * 10 + ne + nw * 3
        advice = ("跨系統高扇入:改冊前先過 VCGC 編號 / 衝突閘,只出重構建議" if ns >= 3 else
                  "同系統多引擎共讀:改結構先跑引擎自測" if ne >= 5 else "低耦合")
        nodes.append({"node": b.get("book", ""), "owner": b.get("owner", ""), "systems": ns, "engines": ne, "writes": nw,
                      "score": score, "advice": advice})
    nodes.sort(key=lambda n: (-n["score"], n["node"]))
    return {"source": str(p), "at": m.get("at", ""), "engine": m.get("engine", ""), "nodes": nodes[:top],
            "note": "" if nodes else "全景裡沒有冊"}


def steps_of(pipes: dict | None, extra: dict) -> list:
    """動態進度條要重播的步驟:六流程實測 + 本版三步(都是這一輪的實測值)。"""
    out = [{"name": n, "status": st.get("status", "?"), "sec": st.get("sec", 0), "detail": st.get("err", "")}
           for n, st in (pipes or {}).items()]
    out.sort(key=lambda s: s["name"])
    out.append({"name": "P6 收尾聚合 + UI join", "status": "OK", "sec": extra.get("join_sec", 0), "detail": "紅黃綠燈 · 并行可修 / 順序依賴分流"})
    for k, label in (("libs_sec", "函式庫四分區盤點(只讀 metadata)"), ("accel_sec", "加速器啟用(Python 線)"),
                     ("hydra_sec", "SSOT 冊 Hydra 偵測(讀 SSOT 引擎全景)")):
        out.append({"name": label, "status": extra.get(k.replace("_sec", "_status"), "OK"), "sec": extra.get(k, 0), "detail": extra.get(k.replace("_sec", "_detail"), "")})
    return out


def _esc(x) -> str:
    return (str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


_V0106_BUILD_UI = PRIOR.build_ui
EXTRA_CSS = ("td,th{word-wrap:break-word}"
             "#live{background:var(--card);border:1px solid var(--hair);padding:8px 12px;margin:0 0 10px}"
             "#live .bar{height:10px}#live .bar i{width:0;animation:none;transition:width .35s ease}"
             "#narr{font-size:11px;min-height:1.5em}#steps li.ok{color:var(--green)}#steps li.fail{color:var(--seal)}"
             "#steps li.wait{color:#8a877f}.tag{display:inline-block;padding:0 4px;border:1px solid var(--hair);border-radius:3px;font-size:10px}")


def build_ui(scan, gov, fin, pipes=None, extra=None) -> str:
    extra = extra or {}
    html = _V0106_BUILD_UI(scan, gov, fin, pipes)
    html = html.replace("font:12px/1.55", "font:11px/1.5", 1).replace("</style>", EXTRA_CSS + "</style>", 1)
    html = html.replace("v0104 · ", f"{_esc(TAG)} · ", 1)
    steps = steps_of(pipes, extra)
    live = ("<div id='live'><b>動態進度</b> <span class='tag' id='pct'>0%</span>"
            "<div class='bar'><i id='pbar'></i></div><div id='narr'>準備重播本輪實測流程…</div>"
            "<ol id='steps'>" + "".join(f"<li class='wait'>{_esc(s['name'])}</li>" for s in steps) + "</ol></div>")
    html = html.replace("<h2>動態說明(三輪)</h2>", live + "<h2>動態說明(三輪)</h2>", 1)
    libs = extra.get("libs") or []
    lib_rows = "".join(
        f"<tr><td>{_esc(r['partition'])}</td><td class='mono'>{_esc(r['lib'])}</td><td>{_esc(r['version'] or '—')}</td>"
        f"<td><span class='dot {'g' if r['state'] == 'INSTALLED' else 'y'}'></span>{_esc(r['state'])}</td><td class='mono'>{_esc(r['slot'])}</td>"
        f"<td>{_esc(r['slot_why'])}</td><td>{_esc(r['how'])}</td></tr>" for r in libs)
    acc = extra.get("accel") or {}
    py, ps = acc.get("python") or {}, acc.get("ps") or {}
    acc_rows = (f"<tr><td>Python 線(SuperAccel · Celeritas)</td><td><span class='dot {'g' if py.get('state') == 'ACTIVE' else 'r'}'></span>{_esc(py.get('state', ''))}</td>"
                f"<td>可用函式庫 {py.get('libs_available', 0)}/{py.get('libs_total', 0)} · 能力 {py.get('capability_real', 0)}/{py.get('capability_total', 0)}"
                f" · 執行緒 {_esc(py.get('thread_budget'))} · 模式 {_esc(py.get('mode'))} · 最大加速{'已套' if py.get('applied') else '未套'}"
                f"{(' · 缺:' + _esc(', '.join(py.get('missing') or []))) if py.get('missing') else ''}{(' · ' + _esc(py.get('detail'))) if py.get('detail') else ''}</td></tr>"
                f"<tr><td>PowerShell 線(20 加速器冊 · VIA_PS_Accel_Module)</td><td><span class='dot {'g' if ps.get('state') == 'READY' else 'y'}'></span>{_esc(ps.get('state', ''))}</td>"
                f"<td>{_esc(ps.get('detail', ''))}</td></tr>")
    hy = extra.get("hydra") or {}
    hy_rows = "".join(
        f"<tr><td class='mono'>{_esc(n['node'])}</td><td>{_esc(n['owner'])}</td><td>{n['systems']}</td><td>{n['engines']}</td><td>{n['writes']}</td>"
        f"<td><span class='dot {'r' if n['systems'] >= 3 else 'y' if n['engines'] >= 5 else 'g'}'></span>{_esc(n['advice'])}</td></tr>"
        for n in hy.get("nodes") or []) or f"<tr><td colspan=6>{_esc(hy.get('note') or '無')}</td></tr>"
    more = ("<h2>函式庫四分區 · 建議隔離插槽(只讀;不安裝 · 不建環境)</h2>"
            "<table><tr><th>分區</th><th>函式庫</th><th>版本</th><th>態</th><th>建議插槽</th><th>為何隔離</th><th>缺時怎麼補</th></tr>" + lib_rows + "</table>"
            "<h2>加速器實況(本輪啟用結果)</h2><table><tr><th>線</th><th>態</th><th>細節</th></tr>" + acc_rows + "</table>"
            f"<h2>Hydra · SSOT 冊高耦合節點(來源 {_esc(Path(hy.get('source', '')).name)} · {_esc(hy.get('at', ''))};只出建議,不盲修)</h2>"
            "<table><tr><th>冊</th><th>冊主</th><th>系統數</th><th>引擎數</th><th>寫入處</th><th>建議</th></tr>" + hy_rows + "</table>")
    script = ("<script>(function(){var S=" + json.dumps(steps, ensure_ascii=False) + ";"
              "var tot=S.reduce(function(a,s){return a+Math.max(0.2,+s.sec||0)},0),acc=0,i=0;"
              "var li=document.querySelectorAll('#steps li'),bar=document.getElementById('pbar'),"
              "pct=document.getElementById('pct'),nar=document.getElementById('narr');"
              "function nx(){if(i>=S.length){nar.textContent='完成:'+S.length+' 步 · 失敗 '+S.filter(function(s){return s.status!=='OK'}).length+' 步(本輪實測重播)';return}"
              "var s=S[i];acc+=Math.max(0.2,+s.sec||0);var p=Math.round(acc/tot*100);bar.style.width=p+'%';pct.textContent=p+'%';"
              "nar.textContent='▶ '+s.name+' · '+s.status+' · '+s.sec+'s'+(s.detail?' · '+s.detail:'');"
              "li[i].className=s.status==='OK'?'ok':'fail';li[i].textContent=s.name+' · '+s.status+' · '+s.sec+'s';i++;"
              "setTimeout(nx,Math.min(900,250+Math.max(0.2,+s.sec||0)*30))}setTimeout(nx,200)})();</script>")
    return html.replace("</body></html>", more + script + "</body></html>", 1)


def _patch(on: bool) -> None:
    PRIOR.build_ui = build_ui if on else _V0106_BUILD_UI


_patch(True)


def _timed(fn, *a):
    t0 = time.time()
    try:
        return fn(*a), "OK", round(time.time() - t0, 1), ""
    except Exception as exc:  # noqa: BLE001 — 單步失敗照實記,不拖垮整輪
        return None, "FAIL", round(time.time() - t0, 1), f"{type(exc).__name__}: {str(exc)[:80]}"


def collect() -> tuple:
    """六流程(v0106)+ 本版三步;回 (scan, gov, fin, pipes, extra)。"""
    scan, gov, fin, pipes = PRIOR.run_pipelines()
    t0 = time.time()
    extra: dict = {}
    extra["libs"], extra["libs_status"], extra["libs_sec"], extra["libs_detail"] = _timed(lib_inventory)
    extra["accel"], extra["accel_status"], extra["accel_sec"], extra["accel_detail"] = _timed(accel_status, True)
    extra["hydra"], extra["hydra_status"], extra["hydra_sec"], extra["hydra_detail"] = _timed(hydra_from_ssot_map)
    extra["join_sec"] = round(time.time() - t0, 1)
    return scan, gov, fin, pipes, extra


def cmd_run(open_ui: bool = True) -> int:
    scan, gov, fin, pipes, extra = collect()
    log = PRIOR._log
    log(f"  [R1] OK {scan['n_ok']} · 語法敗 {scan['n_bad']}")
    log(f"  [R2] SSOT {sum(1 for v in gov['ssot'].values() if v['status'] == 'OK')}/{len(gov['ssot'])} · Regex 衝突 {len(gov['regex_conflicts'])}"
        f" · Hydra(介面冊){len(gov['hydra_top'])} · Hydra(SSOT 冊)高耦合 {sum(1 for n in (extra['hydra'] or {}).get('nodes', []) if n['systems'] >= 3)}"
        f" · 熱插拔槽 {len(gov['hotplug'])}")
    libs = extra["libs"] or []
    log(f"  [函式庫] 四分區 {len(libs)} 項 · 已裝 {sum(1 for r in libs if r['state'] == 'INSTALLED')} · 缺 {sum(1 for r in libs if r['state'] != 'INSTALLED')}"
        f"(缺的走 VCGC InstallGate,本主控台不安裝)")
    acc = extra["accel"] or {}
    log(f"  [加速器] Python {acc.get('python', {}).get('state')} · 函式庫 {acc.get('python', {}).get('libs_available', 0)}/{acc.get('python', {}).get('libs_total', 0)}"
        f" · PowerShell 20 加速器冊 {acc.get('ps', {}).get('state')}")
    PRIOR.DICT_PATH.exists() or PRIOR.DICT_PATH.write_text(json.dumps(PRIOR.CENTRAL_DICT, ensure_ascii=False, indent=1), encoding="utf-8")
    PRIOR.RUNS.mkdir(parents=True, exist_ok=True)
    ev = PRIOR.RUNS / f"CENTRALGOV_{PRIOR.NOW}.json"
    ev.write_text(json.dumps({"engine": TAG, "scan": {"n_ok": scan["n_ok"], "n_bad": scan["n_bad"],
                                                      "bad": [r for r in scan["rows"] if r["status"] != "OK"]},
                              "gov": gov, "final": fin, "pipelines": pipes, "extra": extra}, ensure_ascii=False, indent=1, default=str),
                  encoding="utf-8")
    PRIOR.UI_PATH.write_text(build_ui(scan, gov, fin, pipes, extra), encoding="utf-8")
    log(f"  [出] {PRIOR.UI_PATH}")
    log(f"  [存證] {ev}")
    for s, v in fin["per_subsystem"].items():
        log(f"    {s}:{v['n']} 件 · 異常 {v['bad']} · {v['light']}")
    if open_ui:
        try:
            import webbrowser
            opened = webbrowser.open(PRIOR.UI_PATH.as_uri())
        except Exception as exc:  # noqa: BLE001 — 開不了瀏覽器(容器 / 無桌面)照實說
            opened = False
            log(f"  [UI] 瀏覽器開不了:{type(exc).__name__}")
        log(f"  [UI] {'已開' if opened else '沒開(無桌面);頁在上面的路徑'}")
    return 0


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if "--ssot" in a:
        return PRIOR.cmd_ssot()
    if "--regex" in a:
        return PRIOR.cmd_regex()
    return cmd_run(open_ui="--no-open" not in a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    print(f"=== {TAG} · 薄尾自測(UI 規格 · 函式庫四分區 · 加速器實況 · SSOT 冊 Hydra)===", flush=True)
    libs = lib_inventory()
    part = {r["lib"]: r["partition"] for r in libs}
    slot = {r["lib"]: r["slot"] for r in libs}
    want = {"plotly": "MODULE", "dash": "MODULE", "pandas": "MODULE", "numpy": "MODULE", "pyarrow": "MODULE",
            "pydantic": "ENGINE", "networkx": "ENGINE", "torch": "ENGINE", "ruff": "ENGINE",
            "grpcio": "FUNCTION-LIB", "cryptography": "FUNCTION-LIB", "beautifulsoup4": "FUNCTION-LIB", "cffi": "FUNCTION-LIB",
            "uv": "OTHERS", "psutil": "OTHERS"}
    chk("① 函式庫四分區照操作員令 15 項(MODULE 5 · ENGINE 4 · FUNCTION-LIB 4 · OTHERS 2);torch → via_engine_cuda12 · plotly / dash → via_lib_plotly_v<主版> · uv / psutil → base;"
        "版本只讀 metadata,缺的標 MISSING + InstallGate",
        part == want and slot["torch"] == "via_engine_cuda12" and slot["plotly"].startswith("via_lib_plotly_v") and slot["dash"] == slot["plotly"]
        and slot["uv"] == slot["psutil"] == "base" and all(r["state"] in ("INSTALLED", "MISSING") for r in libs)
        and all(r["how"] for r in libs if r["state"] == "MISSING"), (part, slot))
    with tempfile.TemporaryDirectory(prefix="cgc075_v0107_") as td:
        fx = Path(td) / "map.json"
        fx.write_text(json.dumps({"at": "2026-11-14T00:00:00+00:00", "engine": "fixture", "books": [
            {"book": "A_SSOT", "owner": "VCGC", "systems": ["VCGC", "VDF", "VRN"], "engines": ["e1", "e2"], "write": 1},
            {"book": "B_SSOT", "owner": "VDF", "systems": ["VDF"], "engines": [f"e{i}" for i in range(6)], "write": 0},
            {"book": "C_SSOT", "owner": "VRN", "systems": ["VRN"], "engines": ["e1"], "write": 0}]}), encoding="utf-8")
        hy = hydra_from_ssot_map(fx)
        none = hydra_from_ssot_map(Path(td) / "absent.json")
        chk("② Hydra 讀 SSOT 引擎全景:跨 3 系統的冊排第一(建議不盲修)· 同系統多引擎次之 · 全景不在照實寫無資料",
            [n["node"] for n in hy["nodes"]] == ["A_SSOT", "B_SSOT", "C_SSOT"] and "不盲修" not in hy["nodes"][2]["advice"]
            and "只出重構建議" in hy["nodes"][0]["advice"] and not none["nodes"] and "不在" in none["note"], (hy, none))
    acc = accel_status(apply_limits=False)
    chk("③ 加速器實況:Python 線回 ACTIVE / ABSENT / ERROR 之一 · PowerShell 線沒 pwsh 照實 NO_PWSH · 20 加速器冊對映照 v0106",
        acc["python"]["state"] in ("ACTIVE", "ABSENT", "ERROR") and acc["ps"]["state"] in ("READY", "NO_PWSH", "MODULE_MISSING")
        and (acc["ps"]["state"] != "READY" or bool(shutil.which("pwsh") or shutil.which("powershell"))) and len(acc["roster"]) >= 6, acc["ps"])
    scan, gov, fin, pipes = PRIOR.run_pipelines()
    extra = {"libs": libs, "accel": acc, "hydra": hydra_from_ssot_map(), "join_sec": 0.1, "libs_sec": 0.0, "accel_sec": 0.2, "hydra_sec": 0.0}
    html = build_ui(scan, gov, fin, pipes, extra)
    steps = steps_of(pipes, extra)
    chk("④ UI 規格:字體 11px · table-layout:auto · word-wrap:break-word · 四大分區 · 紅黃綠燈 · 動態進度條 + 動態說明(重播本輪 %d 步實測)" % len(steps),
        "font:11px" in html and "font:12px" not in html and "table-layout:auto" in html and "word-wrap:break-word" in html
        and all(f"<h2>{p} 分區</h2>" in html for p in ("MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS"))
        and "dot g" in html and "id='pbar'" in html and "id='narr'" in html and "var S=" in html
        and "函式庫四分區" in html and "加速器實況" in html and "Hydra · SSOT 冊高耦合節點" in html and TAG in html)
    chk("⑤ 六流程照 v0106 跑(P1–P5)+ 本版三步都進動態步驟;每步帶實測秒數與狀態",
        sum(1 for s in steps if s["name"].startswith("P")) >= 6 and all("sec" in s and s["status"] in ("OK", "FAIL") for s in steps)
        and any("函式庫" in s["name"] for s in steps) and any("加速器" in s["name"] for s in steps), [s["name"] for s in steps])
    with tempfile.TemporaryDirectory(prefix="cgc075_ui_") as td:
        out = Path(td) / "ui.html"
        out.write_text(html, encoding="utf-8")
        chk("⑥ 頁面寫得出來(單檔、零 CDN)", out.stat().st_size > 2000 and "fonts.googleapis" not in html and "cdn." not in html)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑦ 加速器橋 · 網路工具橋在;不安裝(沒有 pip / uv / venv 呼叫)· 不執行被讀的檔 · 不碰 TA-Lib;寫檔只在 VIA_Reports 與「缺才補」的中央同義字冊",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"pip\s+install|\"pip\"|'pip'|uv\s+(pip|venv)|subprocess", body) and "exec(" not in body
        and body.count(".write_text(") == 3)
    import contextlib
    import io
    buf = io.StringIO()
    _patch(False)
    try:
        with contextlib.redirect_stdout(buf):
            rc = PRIOR.selftest()
    finally:
        _patch(True)
    last = [x for x in buf.getvalue().splitlines() if "[計]" in x][-1:]
    for ln in last:
        print("  ── 前版 " + ln.strip()[:200], flush=True)
    chk("⑧ 前版 v0106 自測 rc 0(暫時拿掉本版補丁跑,跑完補回)", rc == 0, "rc %s" % rc)
    good = all(ok)
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'rc ' + str(rc)} · 合計 {'PASS' if good else 'FAIL'}", flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
