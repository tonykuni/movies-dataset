#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0183 — 薄尾:`closeout` 一個指令掌控整個收尾(交接閘 → 重測 → 註冊 → 編號 → SDD → checkpoint → 推上 GitHub)

操作員(側線 2026-10-01):「做一次優化補不足之處 推上去自動完成 auto sync to github」「與 vcgc 結合掌控一切」
實錄(同批):AI 收尾要手打九步(handoff check → 逐案 handoff test → registry-sync → 編號 → audit → SDD → checkpoint → 提交 → push),
  漏一步交接快照就落後(9/30 14:01 之後 49 提交沒 checkpoint;需求冊沒登)。本版把九步收進 VCGC 一個動詞:
  closeout [--apply] [--push] [--cases a,b] [--skip-tests]
    ① 交接閘(VIA_Panorama 尾版 state)前
    ② handoff check → 從發現自動算出要重測的案(EVIDENCE_INVALID 的工作項 → 案;CHANGED_CODE_WITHOUT_TEST 的檔 → 相依命中的案)
    ③ 逐案 handoff test(任一案失敗 = 停,不 checkpoint)
    ④ registry-sync 乾跑;有待註冊:--apply 才套用並提交
    ⑤ --apply:編號 --apply --scope → audit(遺失 / 改身分 / 重號任一非 0 = 停)→ 提交
    ⑥ SDD 檢查(RED = 停,不 checkpoint)
    ⑦ --apply:handoff checkpoint → 提交收據 · 交接冊 · 只增帳
    ⑧ --push:git push origin HEAD(不強推 · 不改歷史;被拒照實回紅)
    ⑨ 交接閘(後)· 前後對比一行
  沒帶 --apply = 只跑測試與乾跑,印出要下的指令(同意閘:寫冊 / 提交 / 推送都要操作員明打旗標)。
  每步完整輸出落 VIA_Reports/closeout/<輪號>/<步>.log,螢幕每步一行(省 Token);總表 CLOSEOUT_latest.json。
  子步一律以子行程跑本版(VIA_PANORAMA_AUTO=0 · VIA_VCGC_PUSH=NO,推送只由 ⑧ 決定);收尾完照 v0182 觸發一次監控。
其餘照 v0182。
合併註(2026-10-01):本版原在側線編為 v0182,與 main 的 v0181(活元件盤點快取鑰)撞號 → 側線三版順移 v0182–v0184,
  前版鏈接到 main 的 v0181(快取鑰修正保留);邏輯不變。
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

import fnmatch
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
REPO = VIA.parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
PRIOR_PATH = max(p for p in HERE.glob(_STEM + "_v*.py") if p.name < Path(__file__).name)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0183", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
HANDOFF_SSOT = HERE / "VIA_Handoff_Continuity_SSOT_v0100.json"
OUT = VIA / "VIA_Reports" / "closeout"
COMMIT_PATHS = ["VeritasIntelligenceAnalytics/docs/handoff", "VeritasIntelligenceAnalytics/supportive modules/registry"]
CLOSE_LINE = ("closeout [--apply] [--push] [--cases a,b]  一個指令收尾:交接閘 → 自動算重測案 → handoff test → registry-sync → 編號 → SDD"
              " → checkpoint → 推上 GitHub(寫冊 / 提交 / 推送要明打旗標)")


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


# ---------------------------------------------------------------- help: current entry is this tail
_PREV_CATALOG = PRIOR.help_catalog
_PREV_SHOW = vars(PRIOR).get("_show_help_v0183")
_PATCHED: list = []


def help_catalog():
    card = _PREV_CATALOG()
    card.update(entry=Path(__file__).name, previous=PRIOR_PATH.name, closeout=CLOSE_LINE)
    return card


def _show_help_v0184():
    if _PREV_SHOW is not None:
        _PREV_SHOW()
    print("  " + CLOSE_LINE)


def _patch_help(on: bool = True) -> None:
    """v0182 把舊版的 help 接到它身上;本版接回自己(v0182 本身不動)。on=False 還原(跑前版自測時用)。"""
    if on:
        for _m in _chain()[1:]:
            if vars(_m).get("help_catalog") is _PREV_CATALOG:
                _m.help_catalog = help_catalog
                _PATCHED.append((_m, "help_catalog", _PREV_CATALOG))
            if _PREV_SHOW is not None and vars(_m).get("show_current_help") is _PREV_SHOW:
                _m.show_current_help = _show_help_v0184
                _PATCHED.append((_m, "show_current_help", _PREV_SHOW))
    else:
        for _m, attr, orig in _PATCHED:
            setattr(_m, attr, orig)
        _PATCHED.clear()


_patch_help(True)


# ---------------------------------------------------------------- closeout
def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sub(argv: list, log: Path, timeout: int = 1800) -> tuple:
    """子行程跑本版主控台(不觸發監控 · 不自動推);完整輸出落檔,回 (rc, 文字)。"""
    env = {**os.environ, "VIA_FROM_VCGC": "YES", "VIA_PANORAMA_AUTO": "0", "VIA_VCGC_PUSH": "NO", "VIA_NO_OPEN": "1"}
    try:
        p = subprocess.run([sys.executable, str(Path(__file__).resolve()), *argv], cwd=str(REPO), capture_output=True, timeout=timeout,
                           env=env, stdin=subprocess.DEVNULL)
        rc, txt = p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        rc, txt = 124, f"逾時 {timeout}s(誠實)"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(txt, encoding="utf-8")
    return rc, txt


def git(*args, timeout: int = 300) -> tuple:
    try:
        p = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL)
        return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 124, "逾時"


def commit(message: str) -> str:
    """只提交收尾會動到的兩夾;沒有變動 = 不提交(誠實回 clean)。"""
    git("add", "-A", "--", *COMMIT_PATHS)
    rc, _ = git("diff", "--cached", "--quiet")
    if rc == 0:
        return "clean"
    rc, out = git("commit", "-q", "-m", message)
    return "committed" if rc == 0 else f"commit 失敗:{out.strip()[-120:]}"


def affected_cases(check_text: str, cases: dict, work_items: list) -> list:
    """handoff check 的發現 → 要重測的案(依交接冊的工作項與案相依)。"""
    wi = {w["id"]: w.get("case") for w in work_items if isinstance(w, dict)}
    hit = set()
    for m in re.finditer(r"EVIDENCE_INVALID \{'id': '([^']+)'", check_text):
        c = wi.get(m.group(1)) or m.group(1).split(":")[-1]
        if c in cases:
            hit.add(c)
    changed = re.findall(r"CHANGED_CODE_WITHOUT_TEST (.+)", check_text)
    for f in (x.strip() for x in changed):
        for name, spec in cases.items():
            if any(fnmatch.fnmatch(f, d) for d in spec.get("dependencies") or []):
                hit.add(name)
    order = list(cases)
    return sorted(hit, key=order.index)


def verify_work_items(passed: list) -> int:
    """本輪 handoff test 通過的案 → 其下 PENDING 工作項轉 VERIFIED(掛收據);其他狀態一律不動。"""
    ho = json.loads(HANDOFF_SSOT.read_text(encoding="utf-8"))
    n = 0
    for w in ho.get("work_items") or []:
        if isinstance(w, dict) and w.get("case") in passed and w.get("state") == "PENDING":
            w["state"], w["receipt"] = "VERIFIED", f"docs/handoff/evidence/{w['case']}.json"
            n += 1
    if n:
        ho["updated_at"] = _now()
        HANDOFF_SSOT.write_text(json.dumps(ho, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return n


def gate(log: Path) -> str:
    tails = sorted(HERE.glob("VIA_Panorama_v*.py"))
    if not tails:
        return "交接閘 ABSENT(VIA_Panorama 不在)"
    env = {**os.environ, "VIA_PANORAMA_AUTO": "0"}
    try:
        p = subprocess.run([sys.executable, str(tails[-1]), "state"], cwd=str(VIA), capture_output=True, timeout=300, env=env, stdin=subprocess.DEVNULL)
        txt = (p.stdout + p.stderr).decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        txt = "逾時"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(txt, encoding="utf-8")
    first = (txt.strip().splitlines() or [""])[0]
    return first.split("] ", 1)[-1] if "] " in first else first


def closeout(args: list) -> int:
    apply, push = "--apply" in args, "--push" in args
    skip_tests = "--skip-tests" in args
    only = args[args.index("--cases") + 1].split(",") if "--cases" in args and args.index("--cases") + 1 < len(args) else None
    run = "co-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    d = OUT / run
    rows, t0 = [], time.time()

    def step(sid, name, lamp, note, sec):
        rows.append({"step": sid, "name": name, "lamp": lamp, "note": note, "sec": round(sec, 1)})
        print(f"  {sid:<2} {name:<16} {lamp:<6} {sec:6.1f}s · {note}"[:220], flush=True)

    def finish(rc):
        after = gate(d / "9_gate_after.log")
        step("⑨", "交接閘(後)", "GREEN" if " GREEN" in after else ("RED" if " RED" in after else "YELLOW"), after, 0)
        res = {"run": run, "at": _now(), "apply": apply, "push": push, "rc": rc, "sec": round(time.time() - t0, 1), "steps": rows,
               "head": git("rev-parse", "--short=12", "HEAD")[1].strip()}
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "CLOSEOUT_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        with open(OUT / "closeout_ledger.jsonl", "a", encoding="utf-8") as f:  # 只增
            f.write(json.dumps({k: res[k] for k in ("run", "at", "apply", "push", "rc", "sec", "head")}, ensure_ascii=False) + "\n")
        print(f"[VCGC closeout] {'GREEN' if rc == 0 else ('RED' if rc == 1 else 'YELLOW')} · rc {rc} · {res['sec']}s · 記錄 {d}")
        return rc

    print(f"[VCGC closeout] {run} · {'--apply' if apply else '乾跑(不寫冊 · 不提交)'} · {'--push' if push else '不推'}", flush=True)
    t = time.time()
    before = gate(d / "1_gate_before.log")
    step("①", "交接閘(前)", "RED" if " RED" in before else ("GREEN" if " GREEN" in before else "YELLOW"), before, time.time() - t)
    t = time.time()
    rc, txt = sub(["handoff", "check"], d / "2_handoff_check.log")
    try:
        ho = json.loads(HANDOFF_SSOT.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        step("②", "handoff check", "RED", f"交接冊讀不到:{e}", time.time() - t)
        return finish(1)
    cases = only or affected_cases(txt, ho.get("test_cases") or {}, ho.get("work_items") or [])
    head = next((ln for ln in txt.splitlines() if ln.startswith("[交接防遺漏]")), "").replace("[交接防遺漏] ", "")
    step("②", "handoff check", "GREEN" if rc == 0 else "YELLOW", f"{head[:90]} → 要重測 {len(cases)} 案:{','.join(cases) or '無'}", time.time() - t)
    passed = []
    if not skip_tests:
        for c in cases:
            t = time.time()
            rc, txt = sub(["handoff", "test", c], d / f"3_test_{c}.log", timeout=1800)
            rec = next((json.loads(ln) for ln in txt.splitlines() if ln.startswith("{\"case\"")), {})
            ok = rc == 0 and rec.get("marker", False)
            step("③", f"test {c}", "GREEN" if ok else "RED", f"rc {rc} · 標記 {rec.get('marker')}", time.time() - t)
            if not ok:
                print(f"  停:{c} 沒過,不往下 checkpoint(看 {d / f'3_test_{c}.log'})")
                return finish(1)
            passed.append(c)
    if apply and passed:
        t = time.time()
        n = verify_work_items(passed)
        step("③+", "工作項轉 VERIFIED", "GREEN", f"{n} 項(只轉本輪實測通過的案底下 PENDING 的;BLOCKED 不動)", time.time() - t)
    t = time.time()
    rc, txt = sub(["registry-sync"] + (["--apply"] if apply else []), d / "4_registry.log")
    m = re.search(r"新 (\d+) · 變更 (\d+) · 退役 (\d+)", txt)
    pend = m and any(int(x) for x in m.groups())
    note = f"新 {m.group(1)} · 變 {m.group(2)} · 退役 {m.group(3)}" if m else "讀不到計數"
    if apply and pend:
        note += " · " + commit("vcgc closeout: registry-sync --apply")
    step("④", "registry-sync", "GREEN" if not pend or apply else "YELLOW", note + ("" if apply or not pend else " → 要套用:closeout --apply"), time.time() - t)
    if apply:
        t = time.time()
        git("fetch", "-q", "origin", "main")
        rc, txt = sub(["run", "CGC_MDL237_NumberingSystem", "--apply", "--scope"], d / "5_numbering.log")
        rc2, txt2 = sub(["run", "CGC_MDL237_NumberingSystem", "audit"], d / "5_numbering_audit.log")
        a = re.search(r"遺失 (\d+) · 改身分 (\d+) · 重號 (\d+)", txt2)
        clean = bool(a) and not any(int(x) for x in a.groups())
        note = (f"遺失 {a.group(1)} · 改身分 {a.group(2)} · 重號 {a.group(3)}" if a else "稽核讀不到") + (" · " + commit("vcgc closeout: numbering --apply --scope") if clean else "")
        step("⑤", "編號 + 稽核", "GREEN" if clean else "RED", note, time.time() - t)
        if not clean:
            return finish(1)
    t = time.time()
    rc, txt = sub(["run", "CGC_MDL245_SDDValidator", "check"], d / "6_sdd.log")
    ms = re.search(r"\[SDD 驗證\] (GREEN|YELLOW|RED)", txt)
    sdd = ms.group(1) if ms else ("GREEN" if rc == 0 else ("RED" if rc == 1 else "YELLOW"))  # 讀不到燈才看結束碼
    step("⑥", "SDD 檢查", sdd, f"rc {rc}", time.time() - t)
    if sdd == "RED":
        print(f"  停:SDD 紅,不 checkpoint(看 {d / '6_sdd.log'})")
        return finish(1)
    if apply:
        t = time.time()
        rc, txt = sub(["handoff", "checkpoint"], d / "7_checkpoint.log")
        note = f"rc {rc} · " + commit("vcgc closeout: handoff checkpoint · 收據 · 只增帳")
        step("⑦", "checkpoint+提交", "GREEN" if rc in (0, 2) else "RED", note, time.time() - t)
        if rc not in (0, 2):
            return finish(1)
    else:
        step("⑦", "checkpoint", "YELLOW", "乾跑不寫:要收尾 → via-vcgc closeout --apply [--push]", 0)
    if push:
        t = time.time()
        rc, out = git("push", "origin", "HEAD", timeout=600)
        step("⑧", "推上 GitHub", "GREEN" if rc == 0 else "RED", "已推" if rc == 0 else f"被拒(不強推):{out.strip()[-120:]}", time.time() - t)
        if rc != 0:
            return finish(1)
    return finish(0 if apply else 2)


# ---------------------------------------------------------------- main
def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["closeout"]:
        try:
            if os.environ.get("VIA_FROM_VCGC") != "YES":
                print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
                return 2
            return closeout(args[1:])
        finally:
            PRIOR.auto_monitor(args)
    return PRIOR.main(args)


# ---------------------------------------------------------------- selftest
def selftest():
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    check = ("[RED] EVIDENCE_INVALID {'id': 'VCGC-REQ075:handoff', 'why': ['x']}\n[RED] EVIDENCE_INVALID {'id': 'VCGC-REQ079:sdd', 'why': []}\n"
             "[RED] CHANGED_CODE_WITHOUT_TEST supportive modules/registry/VIA_Panorama_v0104.py\n[RED] CHANGED_CODE_WITHOUT_TEST zzz/none.py\n")
    cases = {"handoff": {"dependencies": ["a/*.py"]}, "sdd": {"dependencies": []}, "monitor": {"dependencies": ["supportive modules/registry/VIA_Panorama_v*.py"]},
             "deck": {"dependencies": ["b/*.py"]}}
    wi = [{"id": "VCGC-REQ075:handoff", "case": "handoff"}, {"id": "VCGC-REQ079:sdd", "case": "sdd"}]
    got = affected_cases(check, cases, wi)
    chk("② handoff check 發現 → 要重測的案(工作項對案 + 改過的檔對相依;照冊序;不相干的檔不算)", got == ["handoff", "sdd", "monitor"], got)
    seen, real_main = [], PRIOR.main
    calls, real_auto = [], PRIOR.auto_monitor
    PRIOR.main = lambda a: seen.append(list(a)) or 0
    PRIOR.auto_monitor = lambda a, launcher=None: calls.append(list(a)) or "stub"
    env = os.environ.get("VIA_FROM_VCGC")
    try:
        os.environ.pop("VIA_FROM_VCGC", None)
        denied = main(["closeout"])
        passthru = main(["status"])
    finally:
        PRIOR.main, PRIOR.auto_monitor = real_main, real_auto
        if env is None:
            os.environ.pop("VIA_FROM_VCGC", None)
        else:
            os.environ["VIA_FROM_VCGC"] = env
    chk("closeout 不經 VCGC 拒跑 · 拒跑也觸發監控 · 其他動詞原樣轉交 v0182", denied == 2 and calls == [["closeout"]] and seen == [["status"]]
        and passthru == 0, (seen, calls))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("同意閘:寫冊 / 提交只在 --apply · 推送只在 --push · 不強推 · 子步 VIA_VCGC_PUSH=NO",
        "if apply and pend:" in src and "if push:" in src and '"push", "origin", "HEAD"' in src and ("--" + "force") not in src  # 拆開組:這行自己不算
        and '"VIA_VCGC_PUSH": "NO"' in src)
    chk("停損:案沒過 / 稽核非 0 / SDD 紅 都不 checkpoint", src.count("return finish(1)") >= 4)
    import tempfile
    global HANDOFF_SSOT
    keep_ssot = HANDOFF_SSOT
    with tempfile.TemporaryDirectory() as td:
        HANDOFF_SSOT = Path(td) / "h.json"
        HANDOFF_SSOT.write_text(json.dumps({"work_items": [{"id": "a", "case": "monitor", "state": "PENDING"}, {"id": "b", "case": "monitor", "state": "BLOCKED"},
                                                          {"id": "c", "case": "deck", "state": "PENDING"}]}), encoding="utf-8")
        n = verify_work_items(["monitor"])
        st = {w["id"]: w["state"] for w in json.loads(HANDOFF_SSOT.read_text(encoding="utf-8"))["work_items"]}
    HANDOFF_SSOT = keep_ssot
    chk("工作項:只轉本輪通過的案底下 PENDING → VERIFIED;BLOCKED 與沒跑的案不動", n == 1 and st == {"a": "VERIFIED", "b": "BLOCKED", "c": "PENDING"}, st)
    chk("提交只收兩夾(docs/handoff · registry)· 沒變動不空提交", COMMIT_PATHS == ["VeritasIntelligenceAnalytics/docs/handoff",
                                                                     "VeritasIntelligenceAnalytics/supportive modules/registry"] and '"diff", "--cached", "--quiet"' in src)
    card = help_catalog()
    chk("help 目前生效入口 = 本版 · 多一行 closeout", card.get("entry") == Path(__file__).name and "closeout" in card and card.get("previous") == PRIOR_PATH.name)
    chk("加速器橋 · 網路橋在", "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src)
    print(f"  VCGC v0183 selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    if not all(ok):
        return 1
    _patch_help(False)  # 前版自測核的是「help 接在 v0182」:暫時還原,跑完再接回本版
    try:
        return PRIOR.selftest()
    finally:
        _patch_help(True)


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
