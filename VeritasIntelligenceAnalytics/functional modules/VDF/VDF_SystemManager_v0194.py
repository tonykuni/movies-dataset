#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0194 — 薄尾(v0193 以前一字不動):vv 動詞 = 三個獨立流程同時跑的「驗證 + 確認」

操作員 2026-11-27(手機):「PY activating code with accelerating module with three individual procedures simultaneously
to ensure you can reach the goal make the app pass verification and validation in a high speed way」。
本版只多一個動詞(其餘一律交給 v0193;參數 / rc 不變;只增不減):
  vv [--lanes N] [--timeout 秒] [--json]
     三個互不相干的流程同時起跑(總並行 ≤ 6:① 內部 N 道 + ② + ③;N 預設 3,上限 4):
       ① 驗證 VERIFY      全部引擎尾版 --selftest(判法照 v0184 sm_test_native:rc 0 過 · 2/3/4 缺件缺料 ≠ 壞 · 其他 = 不過;
                          缺套件改記 ABSENT)—— 從逐支依序改成 N 道並行,這是最慢的一段
       ② 確認 STRUCTURE   closeout(冊 · 編號 · 安裝 · Graphify · 備份)→ synchronizer run --no-open(頁對收據)
       ③ 確認 RUNTIME     health · bridges --json(加速器 / 網路橋)· sdd --json · 備份校驗(SHA256)
     監工:每 25 秒一行心跳;每送一支引擎前看系統負載,過熱(1 分鐘負載 > 核數 × 1.5)就先等,至少留一支在跑。
     燈:任一流程紅 = 紅;有黃(缺件 / 缺料 / 待操作員)= 黃;全綠 = 綠。主機才做得到的格(整合 · DB 驗證 · 使用者走 U/I)照實列灰。
     收據:VIA_Reports/vdf/manager/VV_latest.json · VV_ledger.jsonl(只增;不入倉)。
零網路(不設同意閘;引擎自測本來就在暫存夾)· 不碰 TA-Lib · 不寫別系統的檔。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

VERSION = "v0194"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent
LANES_DEFAULT, LANES_MAX, TOTAL_MAX = 3, 4, 6
LAMP_ORDER = {"GREEN": 0, "GRAY": 0, "YELLOW": 1, "RED": 2}
RC_LAMP = {0: "GREEN", 2: "YELLOW", 1: "RED"}


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _p(name):
    """沿前版鏈取 v0184 的現成函式(判法不重寫)。"""
    return getattr(PRIOR, name)


def worst(lamps) -> str:
    lamps = [x for x in lamps if x]
    return max(lamps, key=lambda x: LAMP_ORDER.get(x, 2)) if lamps else "GRAY"


class Beat:
    """心跳:每 every 秒印一行(--json 時印到 stderr,stdout 只留 JSON)。"""

    def __init__(self, label, every=25.0, stream=None):
        self.label, self.every, self.t0, self.stream = label, every, time.time(), stream or sys.stdout
        self.state = {}
        self._stop = threading.Event()
        self._th = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stop.wait(self.every):
            s = " · ".join(f"{k} {v}" for k, v in self.state.items())
            print(f"  [心跳] {self.label} · {time.time() - self.t0:.0f}s · {s}", file=self.stream, flush=True)

    def __enter__(self):
        self._th.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._th.join(timeout=2)


def overloaded() -> bool:
    try:
        return os.getloadavg()[0] > (os.cpu_count() or 1) * 1.5
    except (OSError, AttributeError):
        return False


# ── ① 驗證:全部引擎自測,N 道並行 ──────────────────────────────────────────
def engine_items(root: Path) -> list:
    out = []
    for fam, f in _p("sm_engines")(root).items():
        p = root / f["tail"]
        try:
            if "--selftest" in p.read_text(encoding="utf-8", errors="replace"):
                out.append((fam, p))
        except OSError:
            continue
    return out


def one_engine(fam: str, p: Path, timeout: int, env: dict, rc_map: dict, missing_lib) -> dict:
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, str(p), "--selftest"], cwd=tempfile.gettempdir(), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=env)
        res = rc_map.get(r.returncode, "FAIL")
        lib = missing_lib((r.stdout or "") + "\n" + (r.stderr or "")) if res == "FAIL" else ""
        row = {"family": fam, "rc": r.returncode, "result": "ABSENT" if lib else res}
        if lib:
            row["why"] = "缺套件 " + lib
    except subprocess.TimeoutExpired:
        row = {"family": fam, "rc": 124, "result": "TIMEOUT"}
    row["secs"] = round(time.time() - t0, 1)
    return row


def run_engines(items: list, lanes: int, timeout: int, env: dict, rc_map: dict, missing_lib, beat: Beat | None = None,
                guard=overloaded) -> dict:
    t0 = time.time()
    rows, running = [], [0]
    lock = threading.Lock()

    def task(it):
        while guard() and running[0] >= 1:              # 過熱:先等,至少留一支在跑
            time.sleep(1.0)
        with lock:
            running[0] += 1
        try:
            return one_engine(it[0], it[1], timeout, env, rc_map, missing_lib)
        finally:
            with lock:
                running[0] -= 1
                if beat is not None:
                    beat.state["①"] = f"{len(rows) + 1}/{len(items)}"

    with ThreadPoolExecutor(max_workers=max(1, lanes)) as ex:
        for r in ex.map(task, items):
            rows.append(r)
    fail = [r for r in rows if r["result"] in ("FAIL", "TIMEOUT")]
    soft = [r for r in rows if r["result"] in ("NODATA", "ABSENT", "GATED")]
    lamp = "RED" if fail else ("YELLOW" if soft or not rows else "GREEN")
    slow = sorted(rows, key=lambda r: -r["secs"])[:3]
    return {"lamp": lamp, "tested": len(rows), "pass": sum(1 for r in rows if r["result"] == "PASS"), "fail": fail, "soft": soft,
            "lanes": lanes, "secs": round(time.time() - t0, 1), "slowest": [(r["family"], r["secs"]) for r in slow], "rows": rows}


# ── ② ③:前版動詞(子行程;判法照前版)───────────────────────────────────
def verb(args: list, timeout: int = 1800) -> tuple:
    env = dict(os.environ, PYTHONWARNINGS="ignore", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT"):
        env.pop(k, None)
    try:
        r = subprocess.run([sys.executable, str(PRIOR_PATH), *args], cwd=str(HERE), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=env)
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", "[逾時]"


def first_json(text: str) -> dict:
    try:
        d, _ = json.JSONDecoder().raw_decode(text[text.index("{"):])
        return d if isinstance(d, dict) else {}
    except ValueError:
        return {}


def proc_structure(root: Path) -> dict:
    t0 = time.time()
    rc, out, _err = verb(["closeout", "--json"])
    co = first_json(out)
    rc2, out2, _ = verb(["synchronizer", "run", "--no-open"])
    sync_line = next((ln for ln in out2.splitlines() if "synchronizer]" in ln), f"rc {rc2}")
    parts = {"closeout": co.get("lamp") or RC_LAMP.get(rc, "RED"), "synchronizer": RC_LAMP.get(rc2, "RED")}
    yellow = {k: v for k, v in (co.get("parts") or {}).items() if v != "GREEN"}
    return {"lamp": worst(parts.values()), "parts": parts, "closeout_not_green": yellow, "sync": sync_line.strip()[:160],
            "receipt": co.get("receipt"), "secs": round(time.time() - t0, 1)}


def proc_runtime(root: Path) -> dict:
    t0 = time.time()
    rc_h, out_h, _ = verb(["health"])
    rc_b, out_b, _ = verb(["bridges", "--json"])
    rc_s, out_s, _ = verb(["sdd", "--json"])
    b, s = first_json(out_b), first_json(out_s)
    try:
        bk = _p("v73_backup")(root, check_only=True)
    except Exception as exc:  # noqa: BLE001
        bk = {"lamp": "YELLOW", "why": f"{type(exc).__name__}"}
    parts = {"health": RC_LAMP.get(rc_h, "RED"), "bridges": b.get("lamp") or RC_LAMP.get(rc_b, "RED"),
             "sdd": s.get("lamp") or RC_LAMP.get(rc_s, "RED"), "backup_check": bk.get("lamp", "YELLOW")}
    return {"lamp": worst(parts.values()), "parts": parts, "sdd_operator_items": [x.get("step") for x in s.get("known_open", [])],
            "backup": {k: bk.get(k) for k in ("zip", "files", "bad", "why") if k in bk}, "secs": round(time.time() - t0, 1)}


def run_three(procs: dict, beat: Beat | None = None) -> dict:
    """三個流程同時起跑;回 {名: 結果};任一流程丟例外照實記紅(不吞)。"""
    out = {}
    with ThreadPoolExecutor(max_workers=len(procs)) as ex:
        futs = {k: ex.submit(fn) for k, fn in procs.items()}
        for k, f in futs.items():
            try:
                out[k] = f.result()
            except Exception as exc:  # noqa: BLE001
                out[k] = {"lamp": "RED", "error": f"{type(exc).__name__}: {str(exc)[:160]}"}
            if beat is not None:
                beat.state[k] = out[k].get("lamp")
    return out


HOST_ONLY = {"INTEGRATION": "launch --run 會擷取寫庫 → 主機做", "DB": "db check → db verify 要主機的 via_database",
             "USER_TEST": "操作員用滑鼠走 U/I"}


def cmd_vv(args: list) -> int:
    as_json = "--json" in args
    lanes = LANES_DEFAULT
    if "--lanes" in args:
        lanes = int(args[args.index("--lanes") + 1])
    lanes = max(1, min(LANES_MAX, lanes, TOTAL_MAX - 2))
    timeout = int(args[args.index("--timeout") + 1]) if "--timeout" in args else 120
    root = _p("sm_via_root")()
    stream = sys.stderr if as_json else sys.stdout
    t0 = time.time()
    items = engine_items(root)
    print(f"[{TAG}] vv · 三個獨立流程同時起跑:① 驗證 {len(items)} 支引擎自測({lanes} 道)∥ ② 結構確認 ∥ ③ 執行面確認"
          f" · 加速器 {'載到' if VIA_ACCEL is not None else '沒載到'}", file=stream, flush=True)
    env, rc_map, miss = _p("sm_child_env")(), _p("SM_TEST_RC"), _p("sm_missing_lib")
    with Beat(f"{TAG} vv", stream=stream) as beat:
        res = run_three({"① 驗證": lambda: run_engines(items, lanes, timeout, env, rc_map, miss, beat),
                         "② 結構確認": lambda: proc_structure(root),
                         "③ 執行面確認": lambda: proc_runtime(root)}, beat)
    lamp = worst(r.get("lamp") for r in res.values())
    rep = {"manager": TAG, "at": _p("sm_utc")(), "lamp": lamp, "wall_secs": round(time.time() - t0, 1),
           "accel_loaded": VIA_ACCEL is not None, "lanes": lanes,
           "procedures": {k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in res.items()},
           "host_only_gray": HOST_ONLY, "where": "容器 / 本機(看執行的那台)"}
    out = _p("v73_out")(root)
    (out / "VV_latest.json").write_text(json.dumps({**rep, "engine_rows": res.get("① 驗證", {}).get("rows", [])},
                                                   ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    with open(out / "VV_ledger.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"at": rep["at"], "lamp": lamp, "wall_secs": rep["wall_secs"],
                            **{k: v.get("lamp") for k, v in res.items()}}, ensure_ascii=False) + "\n")
    if as_json:
        print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
    else:
        v = res.get("① 驗證", {})
        print(f"[{TAG}] vv {lamp} · 牆鐘 {rep['wall_secs']}s")
        print(f"  ① 驗證 {v.get('lamp')} · 測 {v.get('tested')} · 過 {v.get('pass')} · 不過 {len(v.get('fail', []))} · "
              f"缺件/缺料 {len(v.get('soft', []))} · {v.get('secs')}s({v.get('lanes')} 道)· 最慢 {v.get('slowest')}")
        for r in v.get("fail", []):
            print(f"     [不過] {r['family']} · rc {r['rc']}")
        s2, s3 = res.get("② 結構確認", {}), res.get("③ 執行面確認", {})
        print(f"  ② 結構確認 {s2.get('lamp')} · {s2.get('parts')} · 非綠 {s2.get('closeout_not_green')} · {s2.get('secs')}s")
        print(f"  ③ 執行面確認 {s3.get('lamp')} · {s3.get('parts')} · 待操作員 {s3.get('sdd_operator_items')} · {s3.get('secs')}s")
        for k, why in HOST_ONLY.items():
            print(f"  ⚪ {k} · {why}")
        print(f"[收據] {(out / 'VV_latest.json').relative_to(root)}")
    return _p("SM_RC").get(lamp, 1)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 6 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存夾 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到(VIA_ACCEL is not None)· 第 3 行標記 · 網路橋在", VIA_ACCEL is not None
        and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_NET_TOOL_PATH is not None)
    rc_map = {0: "PASS", 2: "NODATA", 3: "ABSENT", 4: "GATED"}
    with tempfile.TemporaryDirectory(prefix="vdf_vv_") as td:
        d = Path(td)
        body = {"ok": "sys.exit(0)", "bad": "sys.exit(1)", "nodata": "sys.exit(2)",
                "lib": "sys.stderr.write(\"ModuleNotFoundError: No module named 'fxlibzz'\\n\");sys.exit(1)"}
        items = []
        for k, code in body.items():
            p = d / f"FX_{k}_v0100.py"
            p.write_text(f"import sys,time\ntime.sleep(1.0)\n# --selftest\n{code}\n", encoding="utf-8")
            items.append((f"FX_{k}", p))

        def miss(text):
            m = re.search(r"No module named '([\w.]+)'", text)
            return m.group(1) if m else ""
        t0 = time.time()
        r = run_engines(items, 4, 30, dict(os.environ), rc_map, miss, guard=lambda: False)
        dt = time.time() - t0
        got = {x["family"]: x["result"] for x in r["rows"]}
        chk("T2 判法照 v0184:0 過 · 2 缺料 · 缺套件記 ABSENT · 其他不過 → 燈紅",
            got == {"FX_ok": "PASS", "FX_bad": "FAIL", "FX_nodata": "NODATA", "FX_lib": "ABSENT"} and r["lamp"] == "RED", got)
        chk("T3 並行:4 支各睡 1 秒,4 道牆鐘 < 2.5 秒(逐支要 4 秒以上)", dt < 2.5, round(dt, 2))
        calls = {"n": 0}

        def hot():
            calls["n"] += 1
            return calls["n"] < 3
        r2 = run_engines(items[:1], 2, 30, dict(os.environ), rc_map, miss, guard=hot)
        chk("T4 監工:過熱時先等、至少留一支 —— 第一支照跑不卡死", r2["tested"] == 1 and r2["rows"][0]["result"] == "PASS", r2)
    t0 = time.time()
    res = run_three({"a": lambda: (time.sleep(1.0), {"lamp": "GREEN"})[1], "b": lambda: (time.sleep(1.0), {"lamp": "YELLOW"})[1],
                     "c": lambda: (_ for _ in ()).throw(RuntimeError("boom"))})
    dt = time.time() - t0
    chk("T5 三個流程同時跑(各 1 秒 → 牆鐘 < 1.8 秒);流程丟例外照實記紅不吞", dt < 1.8 and res["c"]["lamp"] == "RED"
        and "boom" in res["c"]["error"] and worst(r["lamp"] for r in res.values()) == "RED", (round(dt, 2), res))
    chk("T6 燈的合併:灰不壓綠 · 黃壓綠 · 紅壓黃", worst(["GREEN", "GRAY"]) == "GREEN" and worst(["GREEN", "YELLOW"]) == "YELLOW"
        and worst(["YELLOW", "RED", "GREEN"]) == "RED")
    rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    chk("T7 前版 v0193 自測照過(含整條前版鏈)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["vv"]:
        return cmd_vv(a[1:])
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
