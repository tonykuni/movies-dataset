#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0108 — 薄尾:溢寫模式時記憶體閘不等(操作員令 2026-10-19:「自動修改 VDF 讓溢寫模式時不用等 · 用最快的方法完成指令」)

  工作站實跑(launcher v0104 · ActivateVDF v0105):16 GB 只剩 620 / 1,142 MB 可用 → 每一步起跑前都卡記憶體閘
  (可用 < 總量 10% ≈ 1,608 MB = 壓力)滿 600 秒,等的時候一行不印 → 40 分鐘裡約 30 分鐘在空等、看起來像當機。
  但記憶體少的時候 v0100 本來就已經開溢寫(子行程 TMP / TEMP / POLARS_TEMP_DIR / VIA_DUCKDB_TEMP_DIR 指本輪 temp 夾 ·
  DuckDB 上限壓到 256 MB 起 · VIA_SPILL_TO_DISK=1),v0107(PR #536)再讓每個 duckdb.connect() 真的補上 temp_directory /
  memory_limit / threads(溢寫落本機 TEMP)—— 溢寫模式下再等記憶體只是浪費時間。
本版(疊在 v0107 上;v0107 號碼已由 PR #536 用掉,本變更改出 v0108 · 只增不改):
  ① 本輪起跑時資源計畫是溢寫模式(plan["spill"]:可用 < 保留 1,024 + 每條 1,024 × 3 條 ≈ 4 GB)→ 記憶體閘不等:
     有壓力也直接起這一步,印一行「[溢寫不等] 步名 · 可用 X MB」(不再空白 10 分鐘);沒壓力照常直接起。
  ② 不是溢寫模式 → 一字不改照 v0101 gate_wait(壓力就等,最多 600 秒,Ctrl+C 立刻放手)。
  ③ VIA_ACT_SPILL_NOWAIT=0 → 關掉本版行為(溢寫模式也照等)。
  ④ 總覽 JSON 多一節 spill_nowait(是否溢寫模式 · 起跑可用 · 沒等的步與當下可用)· 總覽頁多一張「溢寫不等」卡 ·
     落檔的 schema / tag 標 v0108 · 跑完印一行 · 頁面長路徑(本輪 temp 夾 · 清點頁 · 模組路徑)手機寬折行(不撐出橫捲)。
  ⑤ 資料庫流程等擷取流程寫完才開庫(DuckDB 一檔一次只准一個行程寫)不是記憶體閘 → 照舊等(保資料)。
  做法:只換 v0101 模組的 gate_wait(它的 run_step 起步前查模組全域)與前版鏈的 optimize_resources / write_report / render_html 外包一層;
  前版檔一字不動 · 只在本版 activate 跑的那一輪生效(前版自測不受影響)· v0107 的記憶體 / TEMP 鉤與起跑實測照跑。
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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

import html
import importlib.util
import os
import re
import sys
import tempfile
import threading
import time
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL013_ActivateVDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0108(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0108(p) < _vnum_v0108(__file__)), key=_vnum_v0108)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():                    # 同 v0102:前版鏈只擋載入那一刻的編譯警告
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100 = PRIOR.V0100


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain_modules() -> list:
    """本版的前版鏈(v0107 → v0106 → … → v0100)。"""
    m, out = PRIOR, []
    for _ in range(16):
        out.append(m)
        m = vars(m).get("PRIOR")
        if m is None:
            break
    return out


_GATE_WAIT_V0101 = PRIOR.gate_wait                 # v0101 定義的那一支(v0102 起的薄尾只是把名字抄進自己的全域)
_V0101 = _GATE_WAIT_V0101.__globals__              # v0101 模組全域:它的 run_step 起步前在這裡查 gate_wait
_OPT_PRIOR = V0100.optimize_resources              # = v0107 的(本輪多做記憶體 / TEMP 起跑實測)
_WRITE_REPORT_PRIOR = V0100.write_report           # = v0107 的(本輪標 v0107 再交 v0106 落檔 · 含資料庫清點)
_RENDER_PRIOR = V0100.render_html                  # = v0107 的(記憶體 / TEMP 卡 · 資料庫清點)
_V0106 = vars(PRIOR).get("PRIOR")                  # v0106:本輪總覽最後經它的 _WRITE_REPORT_V0100 落檔
_SPILL = {"armed": False, "on": False, "avail_mb": None, "skipped": []}
_SPILL_LOCK = threading.Lock()


def spill_nowait_enabled() -> bool:
    return str(os.environ.get("VIA_ACT_SPILL_NOWAIT", "1")).strip() not in ("0", "no", "NO", "false", "False")


def optimize_resources(want: int = 3, stamp: str | None = None, root: Path | None = None) -> dict:
    """同 v0107 optimize_resources;本版 activate 跑的那一輪記下資源計畫是不是溢寫模式。"""
    res = _OPT_PRIOR(want=want, stamp=stamp, root=root)
    with _SPILL_LOCK:
        if _SPILL["armed"]:
            _SPILL["on"] = bool((res.get("plan") or {}).get("spill")) and spill_nowait_enabled()
            _SPILL["avail_mb"] = (res.get("mem") or {}).get("avail_mb")
    return res


def gate_wait(gate, who: str, max_wait: float = 600.0) -> float:
    """溢寫模式 → 不等(有壓力也直接起 · 印一行);不是溢寫模式 → 照 v0101(壓力就等,最多 max_wait 秒,Ctrl+C 立刻放手)。"""
    with _SPILL_LOCK:
        on = _SPILL["armed"] and _SPILL["on"]
    if gate is None or not on:
        return _GATE_WAIT_V0101(gate, who, max_wait)
    if not gate.ok.is_set():
        s = [x for x in getattr(gate, "samples", []) if x is not None]
        avail = s[-1] if s else None
        with _SPILL_LOCK:
            _SPILL["skipped"].append({"who": who, "avail_mb": avail})
        _V0101["_say"](f"  [溢寫不等] {who} · 可用 {avail if avail is not None else '?'} MB(記憶體閘有壓力)· 溢寫模式直接起跑 · TEMP / DuckDB 溢寫已開")
    return 0.0


def spill_card(sp: dict | None) -> str:
    """總覽頁的「溢寫不等」卡(本輪溢寫模式才有)。"""
    if not sp or not sp.get("spill_mode"):
        return ""
    sk = sp.get("skipped") or []
    who = "、".join(html.escape(str(x.get("who"))) for x in sk[:12]) + (" …" if len(sk) > 12 else "")
    return (f'<section id="spill-nowait" class="card" style="margin:12px 0"><b>溢寫不等</b> '
            f'<span class="lamp" style="background:#1a7f37">ON</span><br>'
            f'本輪溢寫模式(起跑可用 {html.escape(str(sp.get("avail_mb_at_start")))} MB)· 記憶體閘沒等的步 {len(sk)} 個'
            + (f":{who}" if who else "")
            + '<br><span class="mut">記憶體少時直接起跑,暫存落本機 TEMP(DuckDB / Polars 溢寫)· 資料庫等擷取寫完才開庫照舊 · '
              'VIA_ACT_SPILL_NOWAIT=0 可關(改回照記憶體閘等)</span></section>')


PAGE_CSS8 = "section.card,li,p{overflow-wrap:anywhere;min-width:0}"   # 長路徑(v0107 記憶體 / TEMP 卡 · 清點頁 · 模組路徑)在手機寬不撐出橫捲


def render_html(card: dict, ui_dir: Path) -> str:
    h = _RENDER_PRIOR(card, ui_dir).replace("</style>", PAGE_CSS8 + "</style>", 1)
    sec = spill_card(card.get("spill_nowait"))
    if not sec:
        return h
    for key in ('<section id="db-inventory"', '<div class="wrap"><table>'):
        i = h.find(key)
        if i >= 0:
            return h[:i] + sec + h[i:]
    return h.replace("</body>", sec + "</body>")


def write_report(card: dict, ui_dir: Path | None = None) -> dict:
    """同前版總覽落檔;本版那一輪多一節 spill_nowait,落檔的 schema / tag 標 v0108。"""
    with _SPILL_LOCK:
        armed = _SPILL["armed"]
        if armed:
            card["spill_nowait"] = {"enabled": spill_nowait_enabled(), "spill_mode": _SPILL["on"], "avail_mb_at_start": _SPILL["avail_mb"],
                                    "skipped": list(_SPILL["skipped"]), "tag": TAG}
    prev = vars(_V0106).get("_WRITE_REPORT_V0100") if (armed and _V0106 is not None) else None
    if prev is None:
        return _WRITE_REPORT_PRIOR(card, ui_dir) if ui_dir is not None else _WRITE_REPORT_PRIOR(card)

    def _stamp_then_write(c, u=None):              # 最內層(v0107 標完之後)再標本版,才交 v0100 原版寫
        c["schema"], c["tag"] = "VDF_ActivateVDF_v0108", TAG
        return prev(c, u) if u is not None else prev(c)
    _V0106._WRITE_REPORT_V0100 = _stamp_then_write
    try:
        return _WRITE_REPORT_PRIOR(card, ui_dir) if ui_dir is not None else _WRITE_REPORT_PRIOR(card)
    finally:
        _V0106._WRITE_REPORT_V0100 = prev


_V0101["gate_wait"] = gate_wait                    # v0101 run_step 查模組全域 → 換上本版(前版檔一字不動)
for _m in _chain_modules():                        # 前版鏈各自叫模組全域的 optimize_resources → 換上本版(冪等)
    if "optimize_resources" in vars(_m):
        _m.optimize_resources = optimize_resources
V0100.render_html = render_html
V0100.write_report = write_report
_ACTIVATE_PRIOR = PRIOR.activate


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0107 activate;這一輪溢寫模式時記憶體閘不等;跑完印一行。"""
    keep = PRIOR.TAG
    PRIOR.TAG = TAG
    with _SPILL_LOCK:
        _SPILL.update(armed=True, on=False, avail_mb=None, skipped=[])
    try:
        card = _ACTIVATE_PRIOR(opt, manager, py, temp)
    finally:
        PRIOR.TAG = keep
        with _SPILL_LOCK:
            sp = dict(_SPILL, skipped=list(_SPILL["skipped"]))
            _SPILL.update(armed=False, on=False)
    if sp["on"]:
        print(f"  [溢寫不等] 本輪溢寫模式(起跑可用 {sp['avail_mb']} MB)· 記憶體閘沒等的步 {len(sp['skipped'])} 個"
              + (":" + "、".join(x["who"] for x in sp["skipped"][:8]) if sp["skipped"] else "") + " · VIA_ACT_SPILL_NOWAIT=0 可關", flush=True)
    return card


for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    global _RENDER_PRIOR, _WRITE_REPORT_PRIOR
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note != "" else ""), flush=True)
    print(f"=== {TAG} · 薄尾自測(溢寫模式時記憶體閘不等;沙盒 · 零網路)===", flush=True)
    keep_env = os.environ.get("VIA_ACT_SPILL_NOWAIT")
    try:
        state = {"m": {"avail_mb": 300, "total_mb": 16000}}
        g = V0100.MemGate(reader=lambda: state["m"], interval=0.05).start()
        try:
            os.environ.pop("VIA_ACT_SPILL_NOWAIT", None)
            with _SPILL_LOCK:
                _SPILL.update(armed=True, on=True, avail_mb=300, skipped=[])
            t0 = time.time()
            w = _V0101["run_step"].__globals__["gate_wait"](g, "lists_run_009", 5.0)
            dt = time.time() - t0
            chk("㉟ 溢寫模式 + 記憶體閘有壓力(可用 300 / 16,000 MB)→ 不等(直接起)· 記一筆沒等的步 · v0101 run_step 用的就是本版 gate_wait",
                w == 0.0 and dt < 0.5 and _SPILL["skipped"] and _SPILL["skipped"][0]["who"] == "lists_run_009" and not g.waits
                and _V0101["run_step"].__globals__["gate_wait"] is gate_wait and PRIOR.run_step is _V0101["run_step"], f"{round(dt, 2)} 秒 · {_SPILL['skipped'][:1]}")
            with _SPILL_LOCK:
                _SPILL.update(on=False, skipped=[])
            t0 = time.time()
            gate_wait(g, "db_check", 0.4)
            dt = time.time() - t0
            chk("㊱ 不是溢寫模式 + 有壓力 → 照 v0101 等(本測最多 0.4 秒)· 記在記憶體閘的等待", 0.35 <= dt < 2 and g.waits and g.waits[-1]["who"] == "db_check", round(dt, 2))
            with _SPILL_LOCK:
                _SPILL.update(armed=False, on=True)
            t0 = time.time()
            gate_wait(g, "fetch_run_all", 0.4)
            dt = time.time() - t0
            chk("㊲ 不是本版 activate 那一輪(前版自測 / 直接叫)→ 照 v0101 等(溢寫旗標不生效)", 0.35 <= dt < 2, round(dt, 2))
            state["m"] = {"avail_mb": 9000, "total_mb": 16000}
            time.sleep(0.15)
            with _SPILL_LOCK:
                _SPILL.update(armed=True, on=True, skipped=[])
            t0 = time.time()
            gate_wait(g, "engine_list", 5.0)
            chk("㊳ 溢寫模式但沒壓力 → 直接起 · 不印也不記", time.time() - t0 < 0.3 and not _SPILL["skipped"])
        finally:
            g.close()
            with _SPILL_LOCK:
                _SPILL.update(armed=False, on=False, avail_mb=None, skipped=[])
        os.environ["VIA_ACT_SPILL_NOWAIT"] = "0"
        off = spill_nowait_enabled()
        os.environ.pop("VIA_ACT_SPILL_NOWAIT", None)
        chk("㊴ VIA_ACT_SPILL_NOWAIT=0 → 關掉本版行為 · 沒設 = 開", off is False and spill_nowait_enabled() is True)
        with tempfile.TemporaryDirectory() as td:
            with _SPILL_LOCK:
                _SPILL.update(armed=True, on=False, avail_mb=None, skipped=[])
            res = V0100.optimize_resources(want=3, stamp="20261019_200000", root=Path(td))
            with _SPILL_LOCK:
                rec = (_SPILL["on"], _SPILL["avail_mb"])
                _SPILL.update(armed=False, on=False, avail_mb=None)
            wired = [m for m in _chain_modules() if "optimize_resources" in vars(m)]
            chk("㊵ 起跑資源計畫 → 記下溢寫模式(= plan[\"spill\"])與起跑可用記憶體 · 前版鏈叫的 optimize_resources 都是本版(包 v0107 的起跑實測)",
                rec == (bool(res["plan"]["spill"]), res["mem"]["avail_mb"]) and V0100.optimize_resources is optimize_resources
                and all(m.optimize_resources is optimize_resources for m in wired) and _OPT_PRIOR is not optimize_resources,
                f"spill={res['plan']['spill']} · 可用 {res['mem']['avail_mb']} MB · 換上 {len(wired)} 個模組")
        keep_r, keep_w = _RENDER_PRIOR, _WRITE_REPORT_PRIOR
        got = {}
        try:
            _RENDER_PRIOR = lambda c, u: '<html><style></style><body><section id="mem-temp"></section><section id="db-inventory"></section></body></html>'
            sp = {"spill_mode": True, "avail_mb_at_start": 620, "skipped": [{"who": "fetch_run_all"}, {"who": "lists_run_<x>"}]}
            page = render_html({"spill_nowait": sp}, Path(td))
            page_off = render_html({"spill_nowait": dict(sp, spill_mode=False)}, Path(td))
            _WRITE_REPORT_PRIOR = lambda c, u=None: got.update(c) or c
            with _SPILL_LOCK:
                _SPILL.update(armed=True, on=True, avail_mb=620, skipped=[{"who": "db_check", "avail_mb": 610}])
            write_report({"lamp": "GREEN"})
            with _SPILL_LOCK:
                _SPILL.update(armed=False, on=False, avail_mb=None, skipped=[])
            got_off = {}
            _WRITE_REPORT_PRIOR = lambda c, u=None: got_off.update(c) or c
            write_report({"lamp": "GREEN"})
        finally:
            _RENDER_PRIOR, _WRITE_REPORT_PRIOR = keep_r, keep_w
        i_m, i_s, i_d = page.find('id="mem-temp"'), page.find('id="spill-nowait"'), page.find('id="db-inventory"')
        chk("㊶ 總覽:本版那一輪 JSON 多 spill_nowait(溢寫模式 · 起跑可用 · 沒等的步)· 頁面「溢寫不等」卡在記憶體 / TEMP 卡之後、資料庫清點之前 · 步名跳脫 · 長路徑折行 CSS · 不是溢寫模式 / 不在本輪 → 不加卡",
            0 <= i_m < i_s < i_d and page.count(PAGE_CSS8) == 1 and PAGE_CSS8 in page_off and "lists_run_&lt;x&gt;" in page and "沒等的步 2 個" in page and 'id="spill-nowait"' not in page_off
            and (got.get("spill_nowait") or {}).get("skipped") == [{"who": "db_check", "avail_mb": 610}] and got["spill_nowait"]["avail_mb_at_start"] == 620
            and "spill_nowait" not in got_off and V0100.render_html is render_html and V0100.write_report is write_report,
            f"卡位置 {i_m} < {i_s} < {i_d}")
        chk("㊷ 前版必須是 v0107(記憶體 / TEMP 鉤 · PR #536)· 它的前版 v0106 有 _WRITE_REPORT_V0100(本版落檔標 v0108 用)",
            Path(PRIOR_PATH).stem.endswith("_v0107") and hasattr(PRIOR, "probe_memtemp") and _V0106 is not None and "_WRITE_REPORT_V0100" in vars(_V0106),
            Path(PRIOR_PATH).name)
    finally:
        if keep_env is None:
            os.environ.pop("VIA_ACT_SPILL_NOWAIT", None)
        else:
            os.environ["VIA_ACT_SPILL_NOWAIT"] = keep_env
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("㊸ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
        "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    n_ok = sum(ok)
    print(f"  [計] {TAG} 本版 {n_ok}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    if not all(ok):
        return 1
    rc1 = PRIOR.selftest()
    return rc1 if rc1 in (0, 1, 2, 3) else 1        # 前版紅照實回(同 v0102 / v0107)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    opt = V0100.parse(argv)
    if opt.verb != "run":
        return V0100.main(argv)
    card = activate(opt)
    return {"GREEN": 0, "YELLOW": 2, "INTERRUPTED": 130}.get(card["lamp"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
