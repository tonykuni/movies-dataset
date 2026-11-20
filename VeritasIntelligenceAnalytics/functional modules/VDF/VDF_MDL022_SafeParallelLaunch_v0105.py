#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL022_SafeParallelLaunch v0105 — 薄尾(v0104 以前一字不動):yf-global = 全球指數與商品自 2018 起的安全分道擷取。

操作員 2026-11-20:「我要抓取所有股票指數及其他 YFINANCE 的商品數據自 2018 開始抓取 · 現在的 VDF 是否安裝加速器 ·
啟動時是否可看 CPU/DRAM 的狀況先降壓然後 3~5 步驟開始擷取儘快 · 給我一個快但安全的擷取指令用 PY 寫用短指令啟動 ·
啟動前做全面修正測試檢查」「被用工具若現在工具不堪用則用備用工具或整合或取代 輸入輸出不變」。

  yf-global [--slots auto|3|4|5] [--start 2018-01-01] [--end D] [--data-home <夾>] [--dry] [--force]
            [--max-wait 180] [--cpu-soft 70] [--cpu-hard 90] [--mem-floor-gb 2] [--timeout 7200]

① 全面檢查(先過才跑;紅就停,--force 只略過「非同意閘」的紅):
   擷取引擎 VDF_ENG066 尾版自測 · 宇宙冊尾版代號數 · 加速器與網路工具橋閘(本系統既有 bridge-gate)·
   網路工具主路 yahoo_chart 與備用 yf_history 都在 · duckdb / psutil · 資料家與正庫(位置 · 開不開得了 = 有沒有被別的程式鎖住)·
   資料家磁碟與 TEMP 剩餘 · 兩道同意閘(只看;沒開就停,本檔不代設)。
② 降壓:本行程與子行程降優先序 · 數學庫執行緒 = CPU ÷ 道數 · 暫存全走 TEMP(本機,不在 OneDrive)· 先印一次 CPU / DRAM,
   再等系統靜下來(CPU ≤ cpu-soft 且 DRAM 可用 ≥ mem-floor;最多 max-wait 秒)。
③ 擷取:道數 = 機器能力夾在 3~5(--slots 可指定)· 宇宙冊代號輪流分成 N 份,每道一份,寫各自的 TEMP 暫存庫
   (DuckDB 一本庫一個寫入者,各道不碰正庫)· 監工每 5 秒量 CPU / DRAM:連兩次過熱減一道並暫停最新子行程,冷卻恢復。
④ 合併:各道跑完(不論燈)→ 單一寫入者只補缺鍵併進正庫(既有列零觸碰)。
⑤ 覆蓋:應抓 · 有資料 · 無資料(逐一點名;缺一不綠)· 收據 VIA_Reports/vdf/launch/VDF_YFGlobal_latest.json。
rc:0 全綠 · 2 有黃(無資料 / 略過)· 1 有紅(檢查沒過 / 合併紅)。不安裝、不刪資料、不寫同意閘;本檔自己不出網(出網的是擷取引擎)。
其餘動詞(run · check · bridge-gate)原樣交給 v0104。自測:py -3 VDF_MDL022_SafeParallelLaunch_v0105.py --selftest
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(本啟動器零連線,橋只為全樹契約齊備) =====
VIA_NET_TOOL_PATH = None


def _via_net():
    """本啟動器**零連線**:出網的是它起的擷取引擎(各自帶網路橋與雙閘);本函式永遠回 None。"""
    return None
# ===== [VIA:NET-BRIDGE:END] =====
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

SYSTEM = "VDF"
STEM = "VDF_MDL022_SafeParallelLaunch"
VERSION = "v0105"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / f"{STEM}_v0104.py"
MIN_SLOTS, MAX_SLOTS = 3, 5          # 操作員 2026-11-20:擷取 3~5 道
LIMITS = {"cpu_soft": 70.0, "cpu_hard": 90.0, "mem_floor_gb": 2.0}


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


P = _load(PRIOR_PATH, "vdf_launch_prior_for_" + VERSION)      # v0104(入口標記)→ v0103 → v0102 → v0101(降壓 · 監工)
B = P.B


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(P, name)


def engine_path() -> Path:
    hits = [p for p in (HERE / "engine").glob("VDF_ENG066_GlobalUniverse_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum)


def clamp_slots(want, res: dict) -> int:
    """--slots 指定就夾在 3~5;auto = 機器能力(前版 auto_slots)夾在 3~5。"""
    if want not in (None, "", "auto"):
        return max(MIN_SLOTS, min(MAX_SLOTS, int(want)))
    return max(MIN_SLOTS, min(MAX_SLOTS, B.auto_slots(res)))


def _opt(args, flag, default=None):
    return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default


# ── ① 全面檢查 ─────────────────────────────────────────────────────────
def preflight(a: dict, run=subprocess.run, eng=None) -> list:
    """回 [(項目, 燈, 說明)];紅 = 不跑。每一項各自獨立量,一項壞不擋其他項的量測。"""
    out = []

    def add(item, lamp, detail):
        out.append((item, lamp, detail))
    py = sys.executable
    ep = engine_path()
    st = run([py, "-B", str(ep), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    last = [ln for ln in (st.stdout or "").splitlines() if "[計]" in ln][-1:] or [(st.stdout or "")[-120:]]
    add("擷取引擎自測", "GREEN" if st.returncode == 0 else "RED", f"{ep.name} · {last[0].strip()}")
    try:
        E = eng or _load(ep, "vdf_e066_for_" + VERSION)
        syms, pend = E.pick_symbols(None)
        add("宇宙冊", "GREEN" if syms else "RED", f"{E.roster_path().name} · {len(syms)} 檔 · 候源類 {len(pend)}")
    except Exception as exc:  # noqa: BLE001
        E, syms = None, []
        add("宇宙冊", "RED", f"讀不到:{type(exc).__name__} {str(exc)[:100]}")
    bg = run([py, "-B", str(PRIOR_PATH), "bridge-gate"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    tail_ln = [ln for ln in (bg.stdout or "").splitlines() if ln.strip()][-1:] or [""]
    add("加速器與網路工具橋閘", "GREEN" if bg.returncode == 0 else ("YELLOW" if bg.returncode == 2 else "RED"), tail_ln[0].strip()[:160])
    try:
        net = E.PRIOR._net() if E else None
        both = net is not None and hasattr(net, "yahoo_chart") and hasattr(net, "yf_history")
        add("網路工具主路 / 備用", "GREEN" if both else "RED",
            f"{Path(getattr(net, '__file__', '?')).name} · yahoo_chart {'在' if hasattr(net, 'yahoo_chart') else '缺'} · yf_history {'在' if hasattr(net, 'yf_history') else '缺'}")
    except Exception as exc:  # noqa: BLE001
        add("網路工具主路 / 備用", "RED", f"載不到:{type(exc).__name__} {str(exc)[:100]}")
    for lib in ("duckdb", "psutil"):
        found = importlib.util.find_spec(lib) is not None
        add(f"套件 {lib}", "GREEN" if found else ("RED" if lib == "duckdb" else "YELLOW"),
            "在" if found else ("缺(經 VCGC 安裝閘裝,本檔不裝)" if lib == "duckdb" else "缺:CPU / DRAM 改用標準庫粗量"))
    home, why = B.resolve_data_home(a.get("data_home"))
    a["data_home_resolved"] = str(home) if home else None
    if E:
        db, dwhy = E.resolve_db(None, str(home) if home else None)
        a["db"] = str(db)
        lamp, note = "GREEN", "新庫(第一次會建)"
        if db.is_file():
            try:
                import duckdb
                c = duckdb.connect(str(db), read_only=True)
                n = c.execute("SELECT count(*) FROM global_daily").fetchone()[0] if c.execute(
                    "SELECT count(*) FROM information_schema.tables WHERE table_name='global_daily'").fetchone()[0] else 0
                c.close()
                note = f"既有 {n:,} 列"
            except Exception as exc:  # noqa: BLE001 — 開不了多半是被別的程式鎖住
                lamp, note = "RED", f"開不了({type(exc).__name__}:{str(exc)[:80]})· 先關掉開著這本庫的程式"
        add("資料家與正庫", lamp, f"家 {home or '(沒找到 → 用前版位置)'}({why})· 庫 {db}({dwhy})· {note}")
        probe = Path(db).parent
        while not probe.exists() and probe.parent != probe:
            probe = probe.parent
        free = shutil.disk_usage(probe).free / 2 ** 30
        add("資料家磁碟剩餘", "GREEN" if free >= 2 else "RED", f"{free:.1f} GB(要 ≥ 2 GB)")
    res = B.resources(B.temp_root())
    add("TEMP 剩餘", "GREEN" if (res.get("temp_free_gb") or 99) >= 2 else "RED", f"{res.get('temp_free_gb')} GB · {B.temp_root()}")
    gates = {k: os.environ.get(k, "") for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    opened = all(v == "YES" for v in gates.values())
    add("同意閘(只看)", "GREEN" if opened else "RED",
        " · ".join(f"{k}={'YES' if v == 'YES' else (v or '未設')}" for k, v in gates.items()) + ("" if opened else " · 本視窗由操作員自己開,本檔不代設"))
    return out


def build_jobs(a: dict, slots: int, lane_dir: Path, py: str = sys.executable) -> list:
    ep = str(engine_path())
    se = ["--start", a["start"]] + (["--end", a["end"]] if a.get("end") else [])
    lanes = [lane_dir / f"lane_{k}_of_{slots}.duckdb" for k in range(1, slots + 1)]
    jobs = [{"id": f"lane{k}", "title": f"③ 擷取第 {k}/{slots} 道(主路 yahoo_chart · 備用 yf_history · 寫 TEMP 暫存庫)",
             "cmd": [py, "-B", ep, "lane", "--part", f"{k}/{slots}", "--lane-db", str(lanes[k - 1])] + se,
             "needs": [], "soft": (3,), "timeout": a["timeout"]} for k in range(1, slots + 1)]
    target = ["--db", a["db"]] if a.get("db") else []
    jobs.append({"id": "merge", "title": "④ 合併:單一寫入者只補缺鍵併進正庫", "cmd": [py, "-B", ep, "merge", "--from"] + [str(x) for x in lanes] + target,
                 "needs": [], "after": [f"lane{k}" for k in range(1, slots + 1)], "soft": (2,), "timeout": 3600})
    jobs.append({"id": "coverage", "title": "⑤ 覆蓋:應抓 · 有資料 · 無資料", "cmd": [py, "-B", ep, "coverage", "--start", a["start"]] + target,
                 "needs": ["merge"], "soft": (2,), "timeout": 900})
    return jobs


def _print_rows(rows: list) -> None:
    for item, lamp, detail in rows:
        print(f"  {lamp:<6} {item:<14} {detail}", flush=True)


def cmd_yf_global(args: list, pre=None, sup_cls=None) -> int:
    a = {"start": _opt(args, "--start", "2018-01-01"), "end": _opt(args, "--end"), "data_home": _opt(args, "--data-home"),
         "timeout": float(_opt(args, "--timeout", 7200)), "max_wait": float(_opt(args, "--max-wait", 180))}
    lim = dict(LIMITS, cpu_soft=float(_opt(args, "--cpu-soft", LIMITS["cpu_soft"])), cpu_hard=float(_opt(args, "--cpu-hard", LIMITS["cpu_hard"])),
               mem_floor_gb=float(_opt(args, "--mem-floor-gb", LIMITS["mem_floor_gb"])))
    t0 = time.time()
    print(f"===== [{TAG}] yf-global · 全球指數與商品 {a['start']} 起 · 先檢查 → 降壓 → 3~5 道 → 合併 → 覆蓋 =====", flush=True)
    res0 = B.resources(B.temp_root())
    print(f"  [現況] CPU {res0.get('cpu_pct')}% · DRAM 可用 {res0.get('mem_avail_gb')} / {res0.get('mem_total_gb')} GB · 核心 {res0.get('cpus')}"
          f" · TEMP 可用 {res0.get('temp_free_gb')} GB · 量法 {res0.get('via')}", flush=True)
    print("  [① 全面檢查]", flush=True)
    rows = (pre or preflight)(a)
    _print_rows(rows)
    reds = [r for r in rows if r[1] == "RED"]
    gate_red = [r for r in reds if r[0].startswith("同意閘")]
    if reds and (gate_red or "--force" not in args):
        print(f"[{TAG}] RED · 檢查沒過 {len(reds)} 項:{' · '.join(r[0] for r in reds)} · 沒有起任何擷取"
              + ("" if gate_red else "(非同意閘的紅可加 --force 照跑,照實記)"), flush=True)
        return 1
    slots = clamp_slots(_opt(args, "--slots", "auto"), res0)
    if "--dry" in args:
        print(f"[{TAG}] DRY · 檢查過 · 會開 {slots} 道 · 正庫 {a.get('db')} · 沒有起任何擷取", flush=True)
        return 0
    print(f"  [② 降壓] 優先序 {B.lower_priority()}", flush=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    tr = B.temp_root() / f"yf_global_{stamp}"
    (tr / "tmp").mkdir(parents=True, exist_ok=True)
    env = P.with_entry(B.calm_env(slots, tr))
    w = B.wait_calm(lim, a["max_wait"])
    print(f"  [② 降壓] 等了 {w['waited_s']:.0f}s · CPU {w['cpu_pct']}% · DRAM 可用 {w['mem_avail_gb']} GB"
          + (" · 到上限仍熱 → 照跑(監工會再減道)" if w["forced"] else " · 系統已靜"), flush=True)
    jobs = build_jobs(a, slots, tr / "lanes")
    (tr / "lanes").mkdir(parents=True, exist_ok=True)
    print(f"  [③ 擷取] {slots} 道同時起(上限 {MAX_SLOTS};過熱自動減道)· 暫存 {tr}", flush=True)
    sup = (sup_cls or B.Supervisor)(jobs, slots, env, tr / "logs", lim)
    r = sup.run(deadline_s=a["timeout"] + 3600)
    lamps = [j.get("lamp", "RED") for j in r["jobs"]]
    lamp = "RED" if "RED" in lamps else ("YELLOW" if "YELLOW" in lamps else "GREEN")
    receipt = {"tag": TAG, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "lamp": lamp, "slots": slots, "final_slots": r["final_slots"],
               "start": a["start"], "db": a.get("db"), "temp": str(tr), "wall_s": r["wall_s"], "preflight": rows,
               "jobs": [{k: j.get(k) for k in ("id", "lamp", "rc", "sec", "last", "log")} for j in r["jobs"]], "events": r["events"]}
    try:
        od = B.out_dir()
        od.mkdir(parents=True, exist_ok=True)
        (od / "VDF_YFGlobal_latest.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        where = od / "VDF_YFGlobal_latest.json"
    except OSError as exc:
        where = f"(收據沒寫成:{type(exc).__name__})"
    print("  [總結]", flush=True)
    for j in r["jobs"]:
        print(f"  {j.get('lamp', 'RED'):<6} {j['id']:<8} rc {j.get('rc')} · {j.get('sec')}s · {str(j.get('last', ''))[:150]}", flush=True)
    print(f"[{TAG}] {lamp} · {slots} 道(結束時 {r['final_slots']})· 降壓事件 {len(r['events'])} · 全程 {time.time() - t0:.0f}s · 收據 {where}", flush=True)
    return {"GREEN": 0, "YELLOW": 2}.get(lamp, 1)


# ── 自測 ───────────────────────────────────────────────────────────────
def selftest() -> int:
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)
    print(f"[計] {TAG} 自測開始(假工作 · 不出網 · 不碰正庫)", flush=True)
    ck("Y1 道數夾在 3~5:auto 依機器 · 指定 9 → 5 · 指定 1 → 3",
       clamp_slots("auto", {"cpus": 2, "mem_avail_gb": 1}) == 3 and clamp_slots("9", {}) == 5 and clamp_slots("1", {}) == 3
       and clamp_slots("auto", {"cpus": 32, "mem_avail_gb": 64}) == 5)
    a = {"start": "2018-01-01", "end": None, "timeout": 60, "db": "X.duckdb"}
    jobs = build_jobs(a, 4, Path("L"))
    ids = [j["id"] for j in jobs]
    m = next(j for j in jobs if j["id"] == "merge")
    ck("Y2 工作圖:4 道各一份 → merge 等全部跑完(after,不論燈)→ coverage 要 merge 綠",
       ids == ["lane1", "lane2", "lane3", "lane4", "merge", "coverage"] and m["after"] == ["lane1", "lane2", "lane3", "lane4"]
       and m["needs"] == [] and jobs[-1]["needs"] == ["merge"] and "--part" in jobs[0]["cmd"] and "1/4" in jobs[0]["cmd"])
    ck("Y3 擷取道只寫 TEMP 暫存庫,正庫只出現在 merge / coverage",
       all("X.duckdb" not in " ".join(j["cmd"]) for j in jobs[:4]) and "X.duckdb" in " ".join(m["cmd"]))
    rows_red = [("同意閘(只看)", "RED", "未設"), ("宇宙冊", "GREEN", "")]
    rc_gate = cmd_yf_global(["--force"], pre=lambda a: rows_red, sup_cls=None)
    ck("Y4 同意閘沒開 = 停(--force 也不跳過)· 沒起任何工作", rc_gate == 1)
    rows_eng = [("擷取引擎自測", "RED", "x"), ("同意閘(只看)", "GREEN", "")]
    ck("Y5 其他紅 = 停;--force 才照跑", cmd_yf_global([], pre=lambda a: rows_eng) == 1)
    started = {}

    class FakeSup:
        def __init__(self, jobs, slots, env, logs, lim):
            started.update(jobs=jobs, slots=slots, env=env, lim=lim)

        def run(self, deadline_s=None):
            return {"jobs": [dict(j, lamp="GREEN", rc=0, sec=0.1, last="ok") for j in started["jobs"]], "events": [], "final_slots": started["slots"],
                    "wall_s": 0.1}
    import tempfile
    saved = (B.wait_calm, B.lower_priority, B.out_dir, B.temp_root)
    with tempfile.TemporaryDirectory(prefix="vdf_m22_v0105_") as td:
        B.wait_calm = lambda lim, mw: {"waited_s": 0.0, "forced": False, "cpu_pct": 10.0, "mem_avail_gb": 8.0}
        B.lower_priority = lambda: "測試不改"
        B.out_dir = lambda: Path(td) / "out"
        B.temp_root = lambda: Path(td) / "temp"
        try:
            green = [("同意閘(只看)", "GREEN", ""), ("宇宙冊", "GREEN", "")]
            rc_ok = cmd_yf_global(["--slots", "4", "--timeout", "60"], pre=lambda a: green, sup_cls=FakeSup)
            receipt_ok = (Path(td) / "out" / "VDF_YFGlobal_latest.json").is_file()
        finally:
            B.wait_calm, B.lower_priority, B.out_dir, B.temp_root = saved
        env = started.get("env", {})
        ck("Y6 檢查過 → 降壓環境(執行緒上限 · TEMP 在暫存根下)+ 入口標記 → 4 道起跑 · 全綠 rc 0 · 收據寫在報告夾",
           rc_ok == 0 and started.get("slots") == 4 and bool(env.get("OMP_NUM_THREADS")) and env.get("VIA_CENTRAL_ENTRY") == "1"
           and env.get("TMP", "").startswith(str(Path(td) / "temp")) and receipt_ok, (rc_ok, env.get("TMP")))
    text = Path(__file__).read_text(encoding="utf-8")
    ck("Y7 檔面:加速器橋 · 網路橋 · 不寫同意閘 · 不 pip · 沒有本機路徑",
       "[VIA:ACCEL-BRIDGE:v0100]" in text and "[VIA:NET-BRIDGE:v0100]" in text and "_CONSENT\"] " + "=" not in text
       and "pip " + "install" not in text and "\\" + "Users" not in text)
    pr = subprocess.run([sys.executable, "-B", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    ck(f"Y8 前版 {PRIOR_PATH.name} 自測照過(另起行程)", pr.returncode == 0, (pr.stdout or "")[-240:])
    n = sum(ok)
    print(f"[計] {STEM} {VERSION} 自測 {n}/{len(ok)} {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if args[:1] == ["yf-global"]:
        return cmd_yf_global(args[1:])
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    return P.main(args)


if __name__ == "__main__":
    sys.exit(main())
