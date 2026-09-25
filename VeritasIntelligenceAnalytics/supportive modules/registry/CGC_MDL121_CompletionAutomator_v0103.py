#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL121_CompletionAutomator v0103 — 未完工作冊+一鍵完工自動化(批335;批340 不卡斷心跳;批341 動態進度條;批343 步內進度)
====================================================================
操作員令:「完成一切未完工作自動化」(貼回 SyncStatus 全景台:總完成度 58.3%)。
職權:
  ledger() 未完工作冊=全實證(MDL096 gather_db/gather_runs/gather_completion
           直取零重算)+每項對映「自動化靶」(DeckServer 白名單任務鏈)或「閘」:
             ENFORCED_SKIP   批212 終止令(2020/2021 段)=永久 SKIP,解除僅憑明令
             PENDING_OPERATOR P08 e-stat appId / P09 治理 20 組 / P18 USD FX 模板
           +完工鏈計畫 plan(依賴序)+最近完工實錄
  run()    一鍵完工=依計畫序逐步 subprocess 執行(argv=DeckServer 尾版 task_registry
           白名單直取零發明;net 任務帶雙同意閘;逐步 rc/秒/三態;任一失敗記
           FAIL 續跑後續無依賴步;閘步 SKIP 誠實)→VIA_Reports/completion/
           COMPLETION_<stamp>.json;--only a,b 子集;--skip-net 離線試跑
律:只增不減;誠實三態 OK/FAIL/SKIP 不假綠;閘=零自動解除;log 逐步落盤。
供應:DeckServer 尾版任務 complete_all(=本檔 run;PROG 進度=步數)、MDL119
/api/completion、MDL120 系統總台「07 完工自動化」視圖、via-complete 短令。
v0100→v0101(批340 工作站實錄「via-complete run 卡斷」):run() 由 subprocess.run 靜默阻塞改
Popen+每 5s 心跳(步序/耗時/log 尾行;flush)+逾時 kill;每步起跑即印;PROG 正則不變(心跳行
無「→ OK/FAIL/SKIP」不誤計)。PS 側=Invoke-VIA-Complete 啟動器(分離工人+直播尾讀;PS-ACCEL)。
v0101→v0102(批341 操作員令「PY指令導入加入引擎 動態進度條」):起跑/心跳/結果/終態四類行尾接動態進度條
progress_bar(done,total)=[■■■□□□] 03/16 19% · 已耗 s · 預估剩餘 s(依已完成步均耗時;零步時「—」);
心跳行 +旋轉符 ◐◓◑◒ 表活;心跳間隔 env VIA_BEAT_SEC(預設 5;下限 1);ACCEL-BRIDGE 既掛(批102 全樹)。
PROG 正則(DeckServer)不變:結果行仍以「[完工] NN/NN id → 三態」起首,進度條只接尾。
v0102→v0103(批343 工作站實錄「backfill 執行中 539s 主條 00/16 0% 好像沒有進度」):步內進度=心跳時
自步 log 尾行擷取分數(如「[批 2/4]」「回 40/40 檔」取首個 n/m)→主條依 (i-1+n/m)/total 連續推進(不再
卡 0%)+心跳行印「步內 [■■□□] 2/4」;PROGRESS.json 每心跳落 RUN_<stamp>/(step/sub/elapsed;供啟動器/UI 讀);
起跑行印「工人 PID」;PROG 正則不變。
用法:python3 CGC_MDL121_CompletionAutomator_v0103.py [plan|ledger|run [--only a,b] [--skip-net]] | --selftest
"""
from __future__ import annotations
import re
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
REP = VIA / "VIA_Reports" / "completion"

# 完工鏈計畫(依賴序;id=DeckServer 白名單任務;timeout 秒;why=完成何項未完工作)
STEPS = [
    ("backfill", "歷史回補 2022/2023 段續跑到齊", 4 * 3600, "VDF 價格庫 2022/2023 段"),
    ("group_class", "族群分類×價格指數(+輪動快照成員冊=族群聚合層/月營收榜之契約)", 3600, "族群分類×輪動(分類存證)+成員冊"),
    ("boot", "全鏈日更(調整層+因子庫+族群聚合層重建)", 2 * 3600, "調整層+因子庫/族群聚合層"),
    ("revenue", "月營收 MOPS 增量", 1800, "月營收庫"),
    ("revenue_groups", "族群月營收榜", 600, "族群聚合層(月營收面)"),
    ("consensus", "三源共識擴碼", 1800, "三源共識庫"),
    ("etf_fetch", "主動 ETF 持股抓取", 1800, "主動 ETF 分類(持股面)"),
    ("etf_enrich", "持股×共識增益", 900, "主動 ETF 分類(共識面)"),
    ("etf_analysis", "主動 ETF×共識分析", 900, "主動 ETF 分類(分析存證)"),
    ("revenue_consensus", "月營收×共識四象限", 900, "月營收(共識面)"),
    ("group_backtest", "族群回測", 1800, "族群分類×輪動(回測存證)"),
    ("story_rotation", "故事族群輪動橋接 v0.5", 2400, "族群分類×輪動(v0.5 缺口冊)"),
    ("std_dashboard", "VAP 標準儀表板", 900, "VAP 儀表板"),
    ("selftest_fast", "沙盒 grid 全矩陣自測", 3600, "沙盒 grid 綠燈率"),
    ("ui", "重生全部 UI", 1200, "連結網頁面"),
    ("system_ui", "系統總台六主體快照再生", 600, "系統總台"),
]
# 閘冊(零自動解除;誠實列)
GATES = [
    {"id": "批212 終止令", "state": "ENFORCED_SKIP", "sub": "VDF 2020/2021 段",
     "why": "操作員終止令=永久 SKIP;解除僅憑操作員明令出新版(本自動化零觸碰)"},
    {"id": "P08", "state": "PENDING_OPERATOR", "sub": "日本 CPI/PPI 車道(e-stat)",
     "why": "e-stat appId 未供=無法自動;操作員供 key 後車道即通"},
    {"id": "P09", "state": "PENDING_OPERATOR", "sub": "批133 治理議題 20 組",
     "why": "候操作員裁決=非機器可完;冊在治理矩陣"},
    {"id": "P18", "state": "AWAITING_OPERATOR", "sub": "USD FX & Rates 模板",
     "why": "批218 紅線=未經明令不碰"},
]
# 完成度列→自動化靶(MDL096 完成度冊 sub 名→任務鏈)
AUTO_MAP = {
    "VDF 價格庫 2023 段": ["backfill"], "VDF 價格庫 2022 段": ["backfill"],
    "VDF 2020/2021 段": None,  # 閘
    "調整層+因子庫": ["boot"], "族群聚合層": ["group_class", "boot", "revenue_groups"],
    "月營收庫(MOPS 官方)": ["revenue"], "三源共識庫": ["consensus"],
    "沙盒 grid 綠燈率": ["selftest_fast"],
}


def _mod(pat: str, dirp: Path = HERE):
    p = sorted(dirp.glob(pat))[-1]
    spec = importlib.util.spec_from_file_location(p.stem, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[p.stem] = m
    spec.loader.exec_module(m)
    return m


def _registry() -> dict:
    try:
        return _mod("CGC_MDL095_DeckServer_v0*.py").task_registry()
    except Exception:
        return {}


def _latest_report() -> dict | None:
    hits = sorted(REP.glob("COMPLETION_*.json"), key=lambda p: p.stat().st_mtime) if REP.exists() else []
    if not hits:
        return None
    try:
        d = json.loads(hits[-1].read_text(encoding="utf-8"))
        d["file"] = hits[-1].name
        return d
    except Exception:
        return None


def plan(registry: dict | None = None) -> list:
    T = registry if registry is not None else _registry()
    out = []
    for i, (tid, zh, to, why) in enumerate(STEPS, 1):
        t = T.get(tid)
        exists = bool(t) and (t["argv"][0] != sys.executable or (len(t["argv"]) > 1 and Path(str(t["argv"][1])).is_file()))
        out.append({"no": i, "id": tid, "zh": zh, "why": why, "timeout": to,
                    "net": bool(t and t.get("net")), "in_registry": bool(t), "engine_ok": exists})
    return out


def ledger() -> dict:
    """未完工作冊(全實證直取;缺=誠實)"""
    d = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "state": "OK"}
    try:
        m96 = _mod("CGC_MDL096_SyncStatus_v0*.py")
        db = m96.gather_db()
        runs = m96.gather_runs()
        comp = m96.gather_completion(db, runs)
    except Exception as exc:
        d["state"] = "FAIL"
        d["reason"] = f"MDL096 直取失敗:{type(exc).__name__}: {str(exc)[:160]}"
        comp = {"rows": [], "overall": None}
    T = _registry()
    items = []
    for r in comp.get("rows", []):
        auto = AUTO_MAP.get(r["sub"], [])
        gate = next((g for g in GATES if g["sub"] == r["sub"]), None)
        items.append({"sub": r["sub"], "pct": r["pct"], "now": r["now"], "next": r["next"],
                      "auto": [a for a in (auto or []) if a in T],
                      "gate": gate["state"] if gate else "",
                      "done": (r["pct"] or 0) >= 100.0,
                      "state": ("DONE" if (r["pct"] or 0) >= 100.0 else
                                (gate["state"] if gate else ("AUTO" if auto else "MANUAL")))})
    d["overall"] = comp.get("overall")
    d["items"] = items
    d["n_auto"] = sum(1 for x in items if x["state"] == "AUTO")
    d["n_done"] = sum(1 for x in items if x["done"])
    d["gates"] = GATES
    d["plan"] = plan(T)
    d["n_steps"] = len(STEPS)
    d["last_run"] = _latest_report()
    return d

_SPIN = "◐◓◑◒"


_FRAC = re.compile(r"(?<![\d.])(\d{1,6})\s*/\s*(\d{1,6})(?![\d.])")


def sub_progress(tail: str) -> tuple:
    """步內分數:尾行首個 n/m(m>0,n<=m)→(n,m);無=(0,0)"""
    for m in _FRAC.finditer(tail or ""):
        n, d = int(m.group(1)), int(m.group(2))
        if d > 0 and n <= d:
            return n, d
    return 0, 0


def progress_bar(done: int, total: int, width: int = 16, spent: float | None = None, per_step: list | None = None) -> str:
    """動態進度條(批341):[■■■□□□] 03/16 19% · 已耗 12s · 預估剩餘 48s(依已完成步均耗時)"""
    total = max(int(total), 1)
    done = min(max(float(done), 0.0), float(total))
    fill = int(width * done / total)
    bar = "■" * fill + "□" * (width - fill)
    pct = int(100 * done / total)
    out = f"[{bar}] {int(done):02d}/{total:02d} {pct:3d}%"
    if spent is not None:
        out += f" · 已耗 {int(spent)}s"
        eta = "—"
        if per_step:
            avg = sum(per_step) / len(per_step)
            eta = f"{int(max(avg * (total - done), 0))}s"
        out += f" · 預估剩餘 {eta}"
    return out


def run(only: list | None = None, skip_net: bool = False, do_print: bool = True) -> int:
    T = _registry()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    REP.mkdir(parents=True, exist_ok=True)
    logdir = REP / f"RUN_{stamp}"
    logdir.mkdir(parents=True, exist_ok=True)
    steps, t_all, durs, beat_n = [], time.time(), [], 0
    beat_sec = max(1.0, float(os.environ.get("VIA_BEAT_SEC", "5") or 5))
    sel = [s for s in STEPS if not only or s[0] in only]
    if only:
        bad = [o for o in only if o not in {s[0] for s in STEPS}]
        if bad:
            print(f"[完工] 未知步驟 {bad}(冊:{','.join(s[0] for s in STEPS)})=拒")
            return 2
    for i, (tid, zh, to, why) in enumerate(sel, 1):
        t = T.get(tid)
        ent = {"no": i, "id": tid, "zh": zh, "why": why, "state": "SKIP", "rc": None, "sec": 0}
        if not t:
            ent["note"] = "不在樞紐白名單(先 git pull)"
        elif skip_net and t.get("net"):
            ent["note"] = "--skip-net 離線試跑=NET 任務跳過"
        elif t["argv"][0] == sys.executable and (len(t["argv"]) < 2 or not Path(str(t["argv"][1])).is_file()):
            ent["note"] = "引擎檔缺"
        else:
            env = dict(os.environ)
            if t.get("net"):
                env["VIA_NET_CONSENT"] = "YES"
                env["VIA_SCRAPE_CONSENT"] = "YES"
            env["PYTHONWARNINGS"] = "ignore:Unverified HTTPS request"
            lp = logdir / f"{i:02d}_{tid}.log"
            t0 = time.time()
            if do_print:
                print(f"[完工] {i:02d}/{len(sel)} {tid} 起跑 · {zh} · 逾時 {to}s · log {lp.name} · "
                      f"{progress_bar(i - 1, len(sel), spent=time.time() - t_all, per_step=durs)}", flush=True)
            try:
                with open(lp, "w", encoding="utf-8", errors="ignore") as lf:
                    p = subprocess.Popen(list(t["argv"]), stdout=lf, stderr=subprocess.STDOUT,
                                         stdin=subprocess.DEVNULL, env=env, cwd=str(VIA))
                    last_beat = time.time()
                    if do_print:
                        print(f"[完工] {i:02d}/{len(sel)} {tid} 工人 PID {p.pid}", flush=True)
                    while True:
                        try:
                            p.wait(timeout=1.0)
                            break
                        except subprocess.TimeoutExpired:
                            pass
                        if time.time() - t0 > to:
                            p.kill()
                            raise subprocess.TimeoutExpired(t["argv"], to)
                        if do_print and time.time() - last_beat >= beat_sec:  # 批340:心跳=不卡斷;批341:進度條
                            last_beat = time.time()
                            try:
                                tail = lp.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
                                tail = tail[-1][-100:] if tail else ""
                            except Exception:
                                tail = ""
                            beat_n += 1
                            sn, sd = sub_progress(tail)
                            frac = (sn / sd) if sd else 0.0
                            sub = f" · 步內 {progress_bar(sn, sd, width=8)}" if sd else ""
                            print(f"[完工] {i:02d}/{len(sel)} {tid} 執行中 {_SPIN[beat_n % 4]} {int(time.time() - t0)}s · "
                                  f"{progress_bar(i - 1 + frac, len(sel), spent=time.time() - t_all, per_step=durs)}{sub}"
                                  f"{' · ' + tail if tail else ''}", flush=True)
                            try:
                                (logdir / "PROGRESS.json").write_text(json.dumps(
                                    {"step": i, "total": len(sel), "id": tid, "sub_n": sn, "sub_d": sd, "pid": p.pid,
                                     "step_sec": int(time.time() - t0), "elapsed": int(time.time() - t_all),
                                     "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, ensure_ascii=False), encoding="utf-8")
                            except Exception:
                                pass
                ent["rc"] = p.returncode
                ent["state"] = "OK" if p.returncode == 0 else "FAIL"
            except subprocess.TimeoutExpired:
                ent["rc"] = -1
                ent["state"] = "FAIL"
                ent["note"] = f"逾時 {to}s 終止(不卡斷)"
            except Exception as exc:
                ent["rc"] = -2
                ent["state"] = "FAIL"
                ent["note"] = f"{type(exc).__name__}"
            ent["sec"] = round(time.time() - t0, 1)
            durs.append(ent["sec"])
            ent["log"] = str(lp.relative_to(VIA))
            try:
                ent["tail"] = "\n".join(lp.read_text(encoding="utf-8", errors="ignore").strip().splitlines()[-3:])[-400:]
            except Exception:
                pass
        steps.append(ent)
        if do_print:
            print(f"[完工] {i:02d}/{len(sel)} {tid} → {ent['state']}"
                  f"{'' if ent['rc'] is None else ' rc' + str(ent['rc'])} · {ent['sec']}s"
                  f"{' · ' + ent['note'] if ent.get('note') else ''} · "
                  f"{progress_bar(i, len(sel), spent=time.time() - t_all, per_step=durs)}", flush=True)
    n_ok = sum(1 for s in steps if s["state"] == "OK")
    n_fail = sum(1 for s in steps if s["state"] == "FAIL")
    n_skip = sum(1 for s in steps if s["state"] == "SKIP")
    rep = {"ts": stamp, "engine": Path(__file__).name, "only": only or [], "skip_net": skip_net,
           "n_ok": n_ok, "n_fail": n_fail, "n_skip": n_skip, "sec": round(time.time() - t_all, 1),
           "state": "OK" if n_fail == 0 and n_ok else ("FAIL" if n_fail and not n_ok else ("PART" if n_fail else "SKIP")),
           "gates": GATES, "steps": steps}
    (REP / f"COMPLETION_{stamp}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    if do_print:
        print(f"[完工] 終態 {rep['state']} · OK {n_ok} · FAIL {n_fail} · SKIP {n_skip} · {rep['sec']}s · "
              f"閘 {len(GATES)} 件零觸碰 · COMPLETION_{stamp}.json · {progress_bar(len(steps), len(sel))}")
    return 0 if n_fail == 0 else 1


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    T = _registry()
    pl = plan(T)
    chk("① 完工鏈計畫(16 步依賴序;白名單直取;引擎在位)",
        len(pl) == 16 and pl[0]["id"] == "backfill" and pl[-1]["id"] == "system_ui"
        and all(p["in_registry"] for p in pl) and all(p["engine_ok"] for p in pl),
        f"(在冊 {sum(p['in_registry'] for p in pl)}/16 · 引擎 {sum(p['engine_ok'] for p in pl)}/16)")
    L = ledger()
    chk("② 未完工作冊(MDL096 實證直取;每列自動靶/閘/三態)",
        L.get("state") == "OK" and len(L["items"]) >= 8 and L.get("overall") is not None
        and any(x["state"] == "AUTO" for x in L["items"])
        and any(x["state"] == "ENFORCED_SKIP" for x in L["items"]),
        f"(總完成度 {L.get('overall')}% · AUTO {L.get('n_auto')} · DONE {L.get('n_done')})")
    chk("③ 閘冊零自動解除(批212/P08/P09/P18 全列;run 不含 2020/2021 段步)",
        len(GATES) == 4 and all(g["state"] in ("ENFORCED_SKIP", "PENDING_OPERATOR", "AWAITING_OPERATOR") for g in GATES)
        and "2020" not in " ".join(s[0] for s in STEPS))
    rc = run(only=["revenue_groups"], do_print=False)
    last = _latest_report()
    chk("④ run 子集真跑(revenue_groups 本機;COMPLETION 存證+步 log 落盤)",
        rc == 0 and last and last["steps"][0]["id"] == "revenue_groups" and last["steps"][0]["state"] == "OK"
        and (VIA / last["steps"][0]["log"]).exists(),
        f"({last and last.get('file')} · {last and last['steps'][0]['sec']}s)")
    rc2 = run(only=["nope"], do_print=False)
    chk("⑤ 未知步驟拒(rc2)+--skip-net 離線試跑=NET 步 SKIP 誠實", rc2 == 2
        and run(only=["backfill"], skip_net=True, do_print=False) == 0
        and _latest_report()["steps"][0]["state"] == "SKIP")
    chk("⑥ 紀律宣告(只增不減/誠實三態/閘零解除/雙同意閘/不卡斷逾時/加速橋)",
        all(k in src for k in ("只增不減", "誠實", "零自動解除", "VIA_NET_CONSENT", "TimeoutExpired", "ACCEL-BRIDGE")))
    pb = progress_bar(3, 16, spent=12.0, per_step=[4.0, 4.0, 4.0])
    chk("⑦ 動態進度條(■□ 16 格/步數/百分比/已耗/預估剩餘;邊界 0 與 total;PROG 正則行首不變)",
        pb.startswith("[■■■□") and "03/16" in pb and " 18%" in pb and "已耗 12s" in pb and "預估剩餘 52s" in pb
        and progress_bar(0, 16).endswith("00/16   0%") and progress_bar(16, 16).startswith("[" + "■" * 16 + "]")
        and progress_bar(0, 0).endswith("00/01   0%") and "預估剩餘 —" in progress_bar(0, 5, spent=1.0)
        and re.match(r"^\[完工\] \d+/\d+ \S+ → (?:OK|FAIL|SKIP)", "[完工] 01/16 backfill → OK rc0 · 1.0s · " + pb) is not None,
        pb)
    chk("⑧ 步內進度(尾行 n/m 擷取;主條連續推進;無分數=0;PROGRESS.json 律宣告)",
        sub_progress("    [批 2/4] +9560 列·回 40/40 檔") == (2, 4) and sub_progress("abc") == (0, 0)
        and sub_progress("2026/09/03 done 3/10") == (3, 10) and sub_progress("x 5/3 y 1/2") == (1, 2)
        and progress_bar(0.5, 16).startswith("[" + "■" * 0) and "  3%" in progress_bar(0.5, 16)
        and progress_bar(1.5, 16).startswith("[■□") and "PROGRESS.json" in src,
        progress_bar(0.5, 16))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 未完工作冊+一鍵完工自動化(CGC_MDL121 v0103)· 八檢自測(零外網)===")
        return selftest()
    if a and a[0] == "run":
        only = None
        if "--only" in a:
            only = [x for x in a[a.index("--only") + 1].split(",") if x]
        return run(only=only, skip_net="--skip-net" in a)
    if a and a[0] == "ledger":
        print(json.dumps(ledger(), ensure_ascii=False, indent=1, default=str))
        return 0
    L = ledger()
    print(f"[完工冊] 總完成度 {L.get('overall')}% · 項 {len(L['items'])} · AUTO {L['n_auto']} · DONE {L['n_done']} · 閘 {len(GATES)}")
    for x in L["items"]:
        print(f"  {x['state']:16s} {x['pct']:6.1f}%  {x['sub']:20s} {x['now']}  → {'/'.join(x['auto']) or x['gate'] or '手動'}")
    print("[完工鏈]", " → ".join(f"{p['no']}.{p['id']}{'(NET)' if p['net'] else ''}" for p in L["plan"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
