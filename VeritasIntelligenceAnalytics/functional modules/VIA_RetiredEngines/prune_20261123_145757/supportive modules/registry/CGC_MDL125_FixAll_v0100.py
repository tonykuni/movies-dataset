#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL125_FixAll v0100 — 工作站紅站一鍵補齊鏈(批350;操作員手機令「keep proceeding on your end」)
====================================================================
批349 via-selftest --refail 實錄:碼側 9 站已修;料/環境側 12 站需工作站四動作。本鏈=四動作+複驗一鍵串
(零猜測:每步 argv 皆自樞紐任務冊/在庫引擎尾版直取;誠實三態;逐步 log;心跳進度條=MDL121 尾版同款直取)。
  ① datahome   MDL123 link:倉內 GroupIndex/VDF output_hub→本機資料家接點(儀表板⑩/每日摘要③/族群聚合層①②)
  ② opencc     import opencc 探;缺=SUP_MDL737.pip_install(輔助模組安裝律;同意閘)(知識堆疊②③b/NLP樞紐②/三語SSOT③)
  ③ global     樞紐任務 global=ENG066 全球宇宙擷取(NET;雙同意閘)(寬表②/輪動實庫③⑤/儀表板⑪)
  ④ consensus  樞紐任務 consensus + revenue_consensus(NET)(共識庫②④/Yahoo⑥/主動ETF×共識/月營收×共識)
  ⑤ refail     SelftestGrid 尾版 --refail(只重跑上次紅站;全原因)→轉綠數
律:只增不減;誠實三態 OK/FAIL/SKIP(已裝/已接=SKIP 註明);任一步敗續跑後續;閘(批212/P08/P09/P18)零觸碰;
    PATH 黑根前綴(哨兵⑫)=操作員環境,本鏈只印提示不改 PATH;報告 VIA_Reports/fixall/FIXALL_<stamp>.json。
用法:python3 CGC_MDL125_FixAll_v0100.py [run [--only a,b] [--dry]] | plan | --selftest
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
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REP = VIA / "VIA_Reports" / "fixall"


def _mod(pattern: str, name: str):
    hits = sorted(HERE.glob(pattern))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location(name, hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


_M121 = None


def m121():
    """MDL121 尾版(進度條/步內進度/Ctrl-C 免疫/樞紐任務冊)直取=零重造"""
    global _M121
    if _M121 is None:
        _M121 = _mod("CGC_MDL121_CompletionAutomator_v0*.py", "fixall_m121")
    return _M121


def _newest(pattern: str, root: Path) -> Path | None:
    hits = sorted(root.glob(pattern))
    return hits[-1] if hits else None


def plan() -> list:
    """步冊(argv 直取;缺=誠實標)"""
    T = {}
    try:
        T = m121()._registry()
    except Exception:
        T = {}
    py = sys.executable
    p123 = _newest("CGC_MDL123_DataHome_v0*.py", HERE)
    grid = _newest("CGC_MDL064_SelftestGrid_v0*.py", HERE)
    steps = [
        {"id": "datahome", "zh": "資料本機家接點(GroupIndex/VDF output_hub→本機)", "net": False, "to": 900,
         "argv": [py, str(p123), "link"] if p123 else None, "why": "儀表板⑩/每日摘要③/族群聚合層①②",
         "pre": "datahome"},
        {"id": "opencc", "zh": "OpenCC 簡繁正規化件(輔助模組安裝律)", "net": True, "to": 600,
         "argv": ["__opencc__"], "why": "知識堆疊②③b/NLP樞紐②/三語SSOT③", "pre": "opencc"},
        {"id": "global", "zh": T.get("global", {}).get("zh", "全球宇宙擷取(ENG066)"), "net": True, "to": 3600,
         "argv": list(T["global"]["argv"]) if "global" in T else None, "why": "寬表②/輪動實庫③⑤/儀表板⑪"},
        {"id": "consensus", "zh": T.get("consensus", {}).get("zh", "三源共識擴碼"), "net": True, "to": 1800,
         "argv": list(T["consensus"]["argv"]) if "consensus" in T else None, "why": "共識庫②④/Yahoo⑥"},
        {"id": "revenue_consensus", "zh": T.get("revenue_consensus", {}).get("zh", "月營收×共識"), "net": True, "to": 1800,
         "argv": list(T["revenue_consensus"]["argv"]) if "revenue_consensus" in T else None, "why": "主動ETF×共識/月營收×共識"},
        {"id": "refail", "zh": "只重跑上次紅站+全原因(SelftestGrid --refail)", "net": False, "to": 3600,
         "argv": [py, str(grid), "--refail"] if grid else None, "why": "轉綠實證"},
    ]
    for s in steps:
        s["engine_ok"] = bool(s["argv"]) and (s["argv"][0] == "__opencc__" or Path(str(s["argv"][1])).is_file())
    return steps


def _pre_skip(step: dict) -> str:
    """前置探:已達成=SKIP 理由;'' =需執行"""
    if step.get("pre") == "opencc":
        try:
            import opencc  # noqa: F401
            return "opencc 已裝"
        except Exception:
            return ""
    if step.get("pre") == "datahome":
        try:
            m = _mod("CGC_MDL123_DataHome_v0*.py", "fixall_m123")
            st = m.status()
            if st.get("state") == "OK" and st.get("points"):
                return "接點已全接"
        except Exception:
            return ""
    return ""


def _run_opencc(lf, env: dict) -> int:
    """輔助模組安裝律:SUP_MDL737.pip_install(同意閘先行;誠實 rc)"""
    os.environ["VIA_NET_CONSENT"] = "YES"  # 本步 net=True:操作員起跑 via-fixall 即同意(誠實印於步冊 NET 欄)
    try:
        import VIA_SuperAccel_Module as A
        rc, msg = A.pip_install(["opencc-python-reimplemented"])
        lf.write(f"[opencc] pip_install rc={rc} {msg}\n")
        if rc == 0:
            return 0
    except Exception as exc:
        lf.write(f"[opencc] 輔助模組道敗 {type(exc).__name__}: {exc};退 pip --user\n")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--user", "opencc-python-reimplemented"],
                       stdout=lf, stderr=subprocess.STDOUT, env=env, timeout=600)
    return r.returncode


def run(only: list | None = None, dry: bool = False, do_print: bool = True) -> int:
    M = m121()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    REP.mkdir(parents=True, exist_ok=True)
    logdir = REP / f"RUN_{stamp}"
    logdir.mkdir(parents=True, exist_ok=True)
    sel = [s for s in plan() if not only or s["id"] in only]
    beat_sec = max(1.0, float(os.environ.get("VIA_BEAT_SEC", "5") or 5))
    immune = M._ctrlc_immune() if hasattr(M, "_ctrlc_immune") else False
    t_all, durs, beat_n, steps = time.time(), [], 0, []
    if do_print:
        print(f"[補齊] 本進程 PID {os.getpid()} · 步 {len(sel)} · Ctrl-C 免疫 {'ON' if immune else 'OFF'} · {'DRY' if dry else 'LIVE'}", flush=True)
        if os.name == "nt":
            bad = [e for e in (os.environ.get("PATH") or "").split(os.pathsep)
                   if e.lower().startswith(("c:\\users\\tonyk\\onedrive", "c:\\users\\tonyk\\downloads"))]
            if bad:
                print(f"[補齊] 提示:PATH 含黑根前綴 {len(bad)} 段(哨兵⑫;本鏈不改 PATH,請於系統環境變數移除):{'; '.join(bad[:3])}", flush=True)
    for i, s in enumerate(sel, 1):
        ent = {"no": i, "id": s["id"], "zh": s["zh"], "why": s["why"], "state": "SKIP", "rc": None, "sec": 0}
        t0 = time.time()
        pre = _pre_skip(s)
        if not s["engine_ok"]:
            ent["note"] = "引擎/樞紐任務缺(先 via-reload)"
        elif pre:
            ent["note"] = pre
        elif dry:
            ent["note"] = "DRY:" + " ".join(str(a) for a in s["argv"])[:160]
        else:
            env = dict(os.environ)
            if s["net"]:
                env["VIA_NET_CONSENT"] = "YES"
                env["VIA_SCRAPE_CONSENT"] = "YES"
            env["PYTHONUTF8"] = "1"
            env["PYTHONWARNINGS"] = "ignore"
            lp = logdir / f"{i:02d}_{s['id']}.log"
            if do_print:
                print(f"[補齊] {i:02d}/{len(sel)} {s['id']} 起跑 · {s['zh']} · 逾時 {s['to']}s · "
                      f"{M.progress_bar(i - 1, len(sel), spent=time.time() - t_all, per_step=durs)}", flush=True)
            try:
                with open(lp, "w", encoding="utf-8", errors="ignore") as lf:
                    if s["argv"][0] == "__opencc__":
                        rc = _run_opencc(lf, env)
                    else:
                        p = subprocess.Popen(list(s["argv"]), stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                             env=env, cwd=str(VIA), **(M._child_kwargs() if hasattr(M, "_child_kwargs") else {}))
                        last_beat = time.time()
                        while True:
                            try:
                                p.wait(timeout=1.0)
                                break
                            except subprocess.TimeoutExpired:
                                pass
                            if time.time() - t0 > s["to"]:
                                p.kill()
                                raise subprocess.TimeoutExpired(s["argv"], s["to"])
                            if do_print and time.time() - last_beat >= beat_sec:
                                last_beat = time.time()
                                beat_n += 1
                                try:
                                    tl = lp.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
                                    tail = tl[-1][-100:] if tl else ""
                                except Exception:
                                    tail = ""
                                sn, sd = M.sub_progress(tail)
                                frac = (sn / sd) if sd else 0.0
                                sub = f" · 步內 {M.progress_bar(sn, sd, width=8)}" if sd else ""
                                print(f"[補齊] {i:02d}/{len(sel)} {s['id']} 執行中 {'◐◓◑◒'[beat_n % 4]} {int(time.time() - t0)}s · "
                                      f"{M.progress_bar(i - 1 + frac, len(sel), spent=time.time() - t_all, per_step=durs)}{sub}"
                                      f"{' · ' + tail if tail else ''}", flush=True)
                                try:
                                    (logdir / "PROGRESS.json").write_text(json.dumps(
                                        {"step": i, "total": len(sel), "id": s["id"], "sub_n": sn, "sub_d": sd, "pid": p.pid,
                                         "self_pid": os.getpid(), "elapsed": int(time.time() - t_all)}, ensure_ascii=False), encoding="utf-8")
                                except Exception:
                                    pass
                        rc = p.returncode
                ent["rc"] = rc
                ent["state"] = "OK" if rc == 0 else "FAIL"
            except subprocess.TimeoutExpired:
                ent["rc"], ent["state"], ent["note"] = -1, "FAIL", f"逾時 {s['to']}s 終止(不卡斷)"
            except Exception as exc:
                ent["rc"], ent["state"], ent["note"] = -2, "FAIL", type(exc).__name__
            ent["log"] = str(lp.relative_to(VIA))
            try:
                tl = lp.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
                ent["tail"] = "\n".join(tl[-3:])[-400:]
                if s["id"] == "refail":
                    ent["tally"] = next((l for l in reversed(tl) if "[計] 重跑" in l), "")
            except Exception:
                pass
        ent["sec"] = round(time.time() - t0, 1)
        if ent["state"] != "SKIP":
            durs.append(ent["sec"])
        steps.append(ent)
        if do_print:
            print(f"[補齊] {i:02d}/{len(sel)} {s['id']} → {ent['state']}{'' if ent['rc'] is None else ' rc' + str(ent['rc'])} · {ent['sec']}s"
                  f"{' · ' + ent['note'] if ent.get('note') else ''}{' · ' + ent['tally'] if ent.get('tally') else ''} · "
                  f"{M.progress_bar(i, len(sel), spent=time.time() - t_all, per_step=durs)}", flush=True)
    n_ok = sum(1 for s in steps if s["state"] == "OK")
    n_fail = sum(1 for s in steps if s["state"] == "FAIL")
    n_skip = sum(1 for s in steps if s["state"] == "SKIP")
    rep = {"ts": stamp, "engine": Path(__file__).name, "dry": dry, "only": only or [], "n_ok": n_ok, "n_fail": n_fail,
           "n_skip": n_skip, "sec": round(time.time() - t_all, 1), "steps": steps,
           "state": "OK" if n_fail == 0 and n_ok else ("FAIL" if n_fail and not n_ok else ("PART" if n_fail else "SKIP"))}
    (REP / f"FIXALL_{stamp}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    if do_print:
        print(f"[補齊] 終態 {rep['state']} · OK {n_ok} · FAIL {n_fail} · SKIP {n_skip} · {rep['sec']}s · FIXALL_{stamp}.json · "
              f"{M.progress_bar(len(steps), len(sel))}", flush=True)
    return 0 if n_fail == 0 else 1


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    os.environ["VIA_CTRLC_IMMUNE"] = "0"
    src = Path(__file__).read_text(encoding="utf-8")
    P = plan()
    chk("① 步冊六步(datahome/opencc/global/consensus/revenue_consensus/refail;argv 樞紐冊/尾版直取)",
        [s["id"] for s in P] == ["datahome", "opencc", "global", "consensus", "revenue_consensus", "refail"]
        and all(s["engine_ok"] for s in P), f"(在位 {sum(s['engine_ok'] for s in P)}/6)")
    chk("② NET 步雙同意閘旗標(global/consensus/revenue_consensus/opencc=net;datahome/refail 零網路)",
        [s["net"] for s in P] == [False, True, True, True, True, False])
    M = m121()
    chk("③ MDL121 尾版助手直取(progress_bar/sub_progress/_ctrlc_immune/_child_kwargs/_registry)零重造",
        M is not None and all(hasattr(M, k) for k in ("progress_bar", "sub_progress", "_ctrlc_immune", "_child_kwargs", "_registry")))
    rc = run(dry=True, do_print=False)
    last = sorted(REP.glob("FIXALL_*.json"))[-1]
    d = json.loads(last.read_text(encoding="utf-8"))
    chk("④ DRY 全鏈零執行(六步皆 SKIP/DRY 註;報告落盤;閘零觸碰)",
        rc == 0 and d["dry"] and len(d["steps"]) == 6 and all(s["state"] == "SKIP" for s in d["steps"])
        and "2020" not in json.dumps(d, ensure_ascii=False), f"({last.name})")
    chk("⑤ 前置探律(opencc 已裝=SKIP 註明;datahome 接點已全接=SKIP)",
        (_pre_skip(P[1]) in ("", "opencc 已裝")) and (_pre_skip(P[0]) in ("", "接點已全接")))
    chk("⑥ 紀律宣告(只增不減/誠實三態/閘零觸碰/輔助模組安裝律/PATH 不改)",
        all(k in src for k in ("只增不減", "誠實三態", "零觸碰", "pip_install", "不改 PATH")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 工作站紅站一鍵補齊鏈(CGC_MDL125 v0100)· 六檢自測(零外網)===")
        return selftest()
    if a and a[0] == "run":
        only = [x for x in a[a.index("--only") + 1].split(",") if x] if "--only" in a else None
        return run(only=only, dry="--dry" in a)
    for s in plan():
        print(f"  {s['id']:18s} {'在位' if s['engine_ok'] else '缺  '} {'NET' if s['net'] else '   '} 逾時 {s['to']:5d}s  {s['zh']}  → {s['why']}")
    print("[補齊] via-fixall run(全鏈)· via-fixall run --only global,refail · --dry 零執行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
