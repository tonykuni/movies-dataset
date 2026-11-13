#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL012_FetchGroups v0109 — 薄尾:子引擎輸出即時串流 + 心跳(不再「卡住不動」)

操作員(2026-11-13 桌機實跑 ENG239 v0101 run --all):清單步(MDL009 全台股清單 · MDL010 主動 ETF 清單)跑起來後畫面完全不動,
以為卡死按了 Ctrl+C。根因:v0107 launch_child 用 subprocess.run(stdout=PIPE) 把子引擎輸出整段收住,跑完才寫 log;
每支最長 1800 秒期間終端一行都沒有。本版只換「起子行程」這一件事(契約一字不變:同參數 · 同回傳欄位 · 同 log 檔):
  ① 子引擎每一行即時印出(前綴 [道] 引擎碼;過長截斷),同時寫進同一個 log 檔(跑完照舊有全文)。
  ② 心跳:子引擎沒有新輸出時,每 15 秒(VIA_FG_HEARTBEAT_S 可調)印一行「執行中 Ns · 最後輸出 Ns 前 · 最後一行」,看得出在跑。
  ③ 逾時照 v0107(冊列 timeout_s 比上限長就用列的)→ 結束整個子行程 · rc 124(照實紅,不冒充)。
其餘(族群 · 分道 · 守門 · 清單先跑 · 頁 · 各動詞)全照前版鏈。VDF 自己的模組:不代設同意閘 · 零 TA-Lib · 不裝套件。
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG_V0109 = f"VDF_MDL012_FetchGroups v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
LINE_MAX_V0109 = 180


def _vnum_v0109(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path() -> Path:
    """前版 = 同家族比本檔小的最大版號(不釘名)。"""
    me = _vnum_v0109(__file__)
    return max((p for p in HERE.glob("VDF_MDL012_FetchGroups_v*.py") if 0 <= _vnum_v0109(p) < me), key=_vnum_v0109)


PRIOR_PATH = _prior_path()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0109", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


def _chain() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


def _owner_of(name: str):
    """沿前版鏈找「name 定義在自己模組裡」的那一版(= launch_child / run_parallel 的本體)。"""
    for m in _chain():
        f = vars(m).get(name)
        if callable(f) and getattr(f, "__module__", None) == m.__name__:
            return m
    return None


V0107 = _owner_of("run_parallel")                                # 並行擷取本體:run_parallel 每次起子行程讀它模組的 LAUNCH
_LAUNCH_BEFORE_V0109 = vars(V0107)["LAUNCH"] if V0107 is not None else None


def _hb_seconds() -> float:
    try:
        return max(0.2, float(os.environ.get("VIA_FG_HEARTBEAT_S", "15")))
    except ValueError:
        return 15.0


def launch_child_v0109(mdl008: Path, r: dict, mode: str, home: Path, logs: Path, timeout: int, env: dict, out=None) -> dict:
    """同 v0107 launch_child 契約(參數 · 回傳欄位 · log 檔);差別:子引擎輸出逐行即時印 + 沒輸出時定時心跳。"""
    out = out or (lambda s: print(s, flush=True))
    lane = (env or {}).get("VIA_FG_LANE") or "-"
    tag = f"[{lane}] {r['id']}"
    log = logs / f"{r['id']}_{mode}.log"
    want = int(r.get("timeout_s") or 0)
    t_out = max(int(timeout), want) if want else int(timeout)
    hb = _hb_seconds()
    t0 = time.time()
    lines, last = [], {"t": t0, "line": ""}
    out(f"    {tag} 起 · 逾時上限 {t_out}s · 心跳每 {hb:g}s")
    try:
        p = subprocess.Popen([sys.executable, "-X", "utf8", "-u", str(mdl008), "_child", r["id"], str(home), mode, "--", *r.get("run_args", [])],
                             stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                             errors="replace", env=dict(env or os.environ, PYTHONUNBUFFERED="1"), cwd=str(home.parent))
    except OSError as e:
        txt = f"{type(e).__name__}: {e}"
        log.write_text(txt, encoding="utf-8")
        return {"id": r["id"], "mdl": r.get("mdl"), "rc": 127, "sec": round(time.time() - t0, 1), "log": str(log), "tail": [txt], "timeout_s": t_out}

    def reader():
        for ln in p.stdout:
            ln = ln.rstrip("\r\n")
            lines.append(ln)
            if ln.strip():
                last["t"], last["line"] = time.time(), ln.strip()
                out(f"    │ {tag} {ln[:LINE_MAX_V0109]}")

    th = threading.Thread(target=reader, daemon=True)
    th.start()
    rc, next_hb = None, t0 + hb
    while rc is None:
        try:
            rc = p.wait(timeout=min(1.0, hb))
        except subprocess.TimeoutExpired:
            now = time.time()
            if now - t0 > t_out:
                p.kill()
                p.wait()
                rc = 124
                out(f"    {tag} 逾時 {t_out}s → 結束子行程(rc 124)")
                break
            if now >= next_hb and now - last["t"] >= hb:
                out(f"    ♥ {tag} 執行中 {now - t0:.0f}s · 最後輸出 {now - last['t']:.0f}s 前"
                    + (f" · {last['line'][:80]}" if last["line"] else " · 尚無輸出"))
                next_hb = now + hb
            elif now >= next_hb:
                next_hb = now + hb
    th.join(timeout=5)
    txt = "\n".join(lines)
    log.write_text(txt, encoding="utf-8")
    tail = [ln for ln in lines if ln.strip()][-3:]
    return {"id": r["id"], "mdl": r.get("mdl"), "rc": rc, "sec": round(time.time() - t0, 1), "log": str(log), "tail": tail, "timeout_s": t_out}


if V0107 is not None:
    vars(V0107)["LAUNCH"] = launch_child_v0109                   # run_parallel 從這裡起子行程;v0107 自測的替身照樣會暫換再換回


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")
    chk("① 找到並行擷取本體(run_parallel 所在版)且 LAUNCH 已換成本版串流起法", V0107 is not None and vars(V0107)["LAUNCH"] is launch_child_v0109,
        getattr(V0107, "__name__", None))
    os.environ["VIA_FG_HEARTBEAT_S"] = "0.5"
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        fake = td / "fake_mdl008.py"
        fake.write_text("import sys, time\nargs = sys.argv[1:]\nrid = args[1]\n"
                        "if rid == 'quiet':\n    time.sleep(2.2); print('done-quiet'); sys.exit(0)\n"
                        "if rid == 'talk':\n    [print('row', i, flush=True) or time.sleep(0.2) for i in range(4)]; sys.exit(3)\n"
                        "if rid == 'hang':\n    time.sleep(30)\n", encoding="utf-8")
        home, logs = td / "home", td / "logs"
        home.mkdir()
        logs.mkdir()
        said = []
        env = dict(os.environ, VIA_FG_LANE="lists")
        r1 = launch_child_v0109(fake, {"id": "quiet", "mdl": "009"}, "live", home, logs, 60, env, out=said.append)
        hbs = [s for s in said if "♥" in s]
        chk("② 子引擎沒輸出時有心跳(0.5s 一次 · 2.2s 內至少 2 行)· 收尾行照印 · rc 0",
            len(hbs) >= 2 and any("done-quiet" in s for s in said) and r1["rc"] == 0, (len(hbs), r1["rc"]))
        said.clear()
        r2 = launch_child_v0109(fake, {"id": "talk", "mdl": "010"}, "live", home, logs, 60, env, out=said.append)
        live = [s for s in said if "│ [lists] talk row" in s]
        logtxt = Path(r2["log"]).read_text(encoding="utf-8")
        chk("③ 每行即時印出(前綴 [道] 碼)· log 檔有全文 · rc 照傳(3)· 回傳欄位同 v0107",
            len(live) == 4 and logtxt.count("row") == 4 and r2["rc"] == 3
            and set(r2) == {"id", "mdl", "rc", "sec", "log", "tail", "timeout_s"}, (len(live), r2["rc"], sorted(r2)))
        said.clear()
        t0 = time.time()
        r3 = launch_child_v0109(fake, {"id": "hang", "mdl": "009"}, "live", home, logs, 2, env, out=said.append)
        chk("④ 逾時 → 結束子行程 · rc 124 · 不等滿 30s", r3["rc"] == 124 and time.time() - t0 < 10, (r3["rc"], round(time.time() - t0, 1)))
        r4 = launch_child_v0109(td / "nope" / "x.py", {"id": "quiet"}, "live", home, logs, 5, env, out=said.append)
        chk("⑤ 子引擎檔不在 → python 回非 0(照實紅,不冒充)", r4["rc"] not in (0, None), r4["rc"])
    os.environ.pop("VIA_FG_HEARTBEAT_S", None)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 帶加速器橋 · 網路橋 · 不代設同意閘 · 零 TA-Lib", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and "environ[\"VIA_NET" + "_CONSENT\"] =" not in src and "import " + "talib" not in src)
    print(f"  前版鏈 {PRIOR_PATH.name} selftest ↓")
    rc = PRIOR.selftest()
    chk("⑦ 前版鏈自測 rc 0;跑完 LAUNCH 仍是本版", rc == 0 and vars(V0107)["LAUNCH"] is launch_child_v0109, rc)
    good = all(ok)
    print(f"  [計] {TAG_V0109} 本版 {sum(ok)}/{len(ok)} · 前版鏈 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
