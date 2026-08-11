# -*- coding: utf-8 -*-
"""via_envmgr_nostall_v0100.py — EnvManager NoStall 加速包覆器 v0100(操作員令:卡段→20 加速器+不卡斷動態進度條)。

正本零觸碰:VIA_EnvManager.py 唯讀 import,函式復用;本器只做編排:
  ① 快速環境發現(純檔案系統,即時)
  ② 20 工作器並行(--workers 可調):每環境獨立子行程評估,硬逾時可殺(--task-timeout,預設 150s)
  ③ 動態進度條:單行 \\r 即時刷新(bar+完成數+耗時+進行中環境名+spinner)— 等待中也持續跳動,絕不靜默
  ④ 誠實彙總:OK/TIMEOUT/ERROR 逐環境列出;衝突判定復用正本 def_find_base_and_via_conflicts
  ⑤ 產出 append-only:_via_envmanager_output/VIA_EnvManager_ConflictReport_NoStall_<ts>.json(不搶正本檔名)
用法:
  py via_envmgr_nostall_v0100.py conflicts [--workers 20] [--task-timeout 150] [--env-root 路徑]
  py via_envmgr_nostall_v0100.py --probe-one <env_path>          (內部工作器模式)
"""
import concurrent.futures
import json
import subprocess
import sys
import threading
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUPP = HERE.parent  # supportive modules/
sys.path.insert(0, str(SUPP))


def load_envmanager():
    import importlib.util
    spec = importlib.util.spec_from_file_location("via_envmanager_ro", SUPP / "VIA_EnvManager.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["via_envmanager_ro"] = m  # dataclasses 型別解析需在 sys.modules 註冊
    spec.loader.exec_module(m)
    return m


def probe_one(env_path):
    """工作器模式:單環境評估(在子行程內跑;逾時由父行程硬殺)。"""
    m = load_envmanager()
    alias_map = m.def_load_alias_map()
    groups = m.def_group_aliases_by_env_name(alias_map)
    route_table = m.def_load_route_table()
    p = Path(env_path)
    aliases = groups.get(p.name, [])
    targets = []
    for a in aliases:
        targets.extend(m.def_find_route_targets_for_alias(a, route_table))
    rec = m.def_assess_single_env(p, aliases, sorted(set(targets)))
    print(json.dumps(asdict(rec), ensure_ascii=False, default=str))
    return 0


BAR_W = 26


def bar_line(done, total, t0, active, spin):
    filled = int(BAR_W * done / total) if total else BAR_W
    b = "█" * filled + "░" * (BAR_W - filled)
    act = "、".join(sorted(active)[:3]) or "—"
    if len(act) > 30:
        act = act[:30] + "…"
    return "\r  %s [%s] %d/%d · %.0fs · 執行中: %s   " % ("|/-\\"[spin % 4], b, done, total, time.time() - t0, act)


def main(argv):
    if "--probe-one" in argv:
        return probe_one(argv[argv.index("--probe-one") + 1])
    workers = int(argv[argv.index("--workers") + 1]) if "--workers" in argv else 20
    task_timeout = int(argv[argv.index("--task-timeout") + 1]) if "--task-timeout" in argv else 150

    m = load_envmanager()
    env_root = Path(argv[argv.index("--env-root") + 1]) if "--env-root" in argv else m.def_find_env_root()
    alias_map = m.def_load_alias_map()
    groups = m.def_group_aliases_by_env_name(alias_map)
    env_paths = m.def_scan_env_directories(env_root)
    known = {p.name for p in env_paths}
    for name in groups.keys():
        if name not in known:
            env_paths.append(env_root / name)
    env_paths = sorted(set(env_paths), key=lambda p: p.name.lower())
    total = len(env_paths)
    print("=== EnvManager NoStall v0100 · 環境 %d · 加速器 %d · 逾時 %ds/env ===" % (total, workers, task_timeout))
    if total == 0:
        print("  [OK ] 環境 0 個(env_root=%s)— 誠實空盤點,無衝突可判" % env_root)
        return 0

    t0 = time.time()
    active = set()
    lock = threading.Lock()
    done_n = [0]
    records, verdicts = [], []

    def run_env(p):
        with lock:
            active.add(p.name)
        try:
            cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--probe-one", str(p)],
                                capture_output=True, text=True, timeout=task_timeout)
            if cp.returncode == 0 and cp.stdout.strip():
                rec = json.loads(cp.stdout.strip().splitlines()[-1])
                return ("OK", p.name, rec)
            return ("ERROR", p.name, {"env_name": p.name, "detail": (cp.stderr or "")[-200:]})
        except subprocess.TimeoutExpired:
            return ("TIMEOUT", p.name, {"env_name": p.name, "detail": "%ds 硬逾時殺除(不卡斷)" % task_timeout})
        except Exception as e:
            return ("ERROR", p.name, {"env_name": p.name, "detail": str(e)[:200]})
        finally:
            with lock:
                active.discard(p.name)
                done_n[0] += 1

    stop = threading.Event()

    def painter():
        spin = 0
        while not stop.is_set():
            sys.stdout.write(bar_line(done_n[0], total, t0, active, spin))
            sys.stdout.flush()
            spin += 1
            stop.wait(0.3)

    th = threading.Thread(target=painter, daemon=True)
    th.start()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        for verdict, name, payload in ex.map(run_env, env_paths):
            verdicts.append((verdict, name))
            if verdict == "OK":
                records.append(payload)
    stop.set()
    th.join(timeout=1)
    sys.stdout.write(bar_line(done_n[0], total, t0, set(), 0) + "\n")

    n_ok = sum(1 for v, _ in verdicts if v == "OK")
    n_to = sum(1 for v, _ in verdicts if v == "TIMEOUT")
    n_er = total - n_ok - n_to
    for v, name in sorted(verdicts):
        if v != "OK":
            print("  [%s] %s" % (v, name))
    # 衝突判定(復用正本)
    conflicts = []
    try:
        recs = [m.def_EnvHealthRecord(**{k: r.get(k) for k in m.def_EnvHealthRecord.__dataclass_fields__}) for r in records]
        conflicts = [asdict(c) for c in m.def_find_base_and_via_conflicts(recs)]
    except Exception as e:
        print("  [WARN] 衝突判定退化(誠實列出):%s" % str(e)[:120])
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = m.def_PARAM_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / ("VIA_EnvManager_ConflictReport_NoStall_%s.json" % ts)
    out.write_text(json.dumps({"version": "nostall_v0100", "generated_at": datetime.now().isoformat(timespec="seconds"),
                               "envs_total": total, "ok": n_ok, "timeout": n_to, "error": n_er,
                               "workers": workers, "task_timeout_s": task_timeout,
                               "conflicts": conflicts, "records": records},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("  環境 OK %d · TIMEOUT %d · ERROR %d · 衝突 %d · %.0fs(串行版本可比基準=每環境最長 ~9 分)"
          % (n_ok, n_to, n_er, len(conflicts), time.time() - t0))
    print("  存證:%s" % out)
    for c in conflicts[:10]:
        print("  [衝突] %s · %s · %s" % (c.get("env_name"), c.get("severity"), c.get("category")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
