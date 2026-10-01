#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0183 — 薄尾:closeout 補「收尾自己弄髒自己的證據」— ⑥+ 收斂迴圈 + ② 提早攔缺欄工作項

實錄(側線 2026-10-01 · closeout 第 2 輪 co-20261001-194209):③ 六案全綠 · ④ ⑤ 已提交 · ⑦ checkpoint RED:
  ③+ 轉 VERIFIED 改了交接冊 → 相依交接冊的 numbering 案證據失效(EVIDENCE_INVALID ×4);
  ⑤ 編號工具 v0108 / v0109 換過 → CHANGED_CODE_WITHOUT_TEST;兩個 PENDING 工作項缺 owner / next / reason → PENDING_WITHOUT_NEXT。
  前兩樣是收尾「自己」造成的(先測後改冊),第三樣在 ② 就看得到,卻跑完 10 分鐘測試才在 ⑦ 紅。
本版:
  ② 先攔:PENDING_WITHOUT_NEXT 的工作項,本輪測不到它的案(或它是 BLOCKED / REVIEW)= 立刻停,印出要補的工作項(不白跑測試)
  ② 多算:PENDING 工作項有宣告案的,把那個案也排進本輪重測(過了才轉 VERIFIED;BLOCKED / REVIEW 不動)
  ⑥+ 收斂:--apply 時,checkpoint 前再跑 handoff check → 只重測被本輪自己弄失效的案 → 轉 VERIFIED → 提交;
       最多 3 圈,第 3 圈仍有失效 = RED 停(不硬 checkpoint)
其餘(⑦ checkpoint · ⑧ push · ⑨ 交接閘 · 同意閘 · 停損)照 v0182。
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
HANDOFF_SSOT = PRIOR.HANDOFF_SSOT
OUT = PRIOR.OUT
SETTLE_ROUNDS = 3
CLOSE_LINE = PRIOR.CLOSE_LINE + " · v0183:② 先攔缺欄工作項 · ⑥+ 收斂迴圈(重測被收尾自己弄失效的案)"


def __getattr__(name):
    return getattr(PRIOR, name)


git, commit, gate, affected_cases, _now = PRIOR.git, PRIOR.commit, PRIOR.gate, PRIOR.affected_cases, PRIOR._now


def verify_work_items(passed: list) -> int:
    return PRIOR.verify_work_items(passed)


# ---------------------------------------------------------------- help: current entry is this tail
_PREV_CATALOG = PRIOR.help_catalog
_PREV_SHOW = vars(PRIOR).get("_show_help_v0182")
_PATCHED: list = []


def help_catalog():
    card = _PREV_CATALOG()
    card.update(entry=Path(__file__).name, previous=PRIOR_PATH.name, closeout=CLOSE_LINE)
    return card


def _show_help_v0183():
    if _PREV_SHOW is not None:
        _PREV_SHOW()
    print("  v0183:closeout ② 先攔缺欄工作項 · ⑥+ 收斂迴圈")


def _patch_help(on: bool = True) -> None:
    """v0182 把舊版的 help 接到它身上;本版接回自己(v0182 本身不動)。on=False 還原(跑前版自測時用)。"""
    if on:
        for _m in [PRIOR, *PRIOR._chain()]:
            if vars(_m).get("help_catalog") is _PREV_CATALOG:
                _m.help_catalog = help_catalog
                _PATCHED.append((_m, "help_catalog", _PREV_CATALOG))
            if _PREV_SHOW is not None and vars(_m).get("show_current_help") is _PREV_SHOW:
                _m.show_current_help = _show_help_v0183
                _PATCHED.append((_m, "show_current_help", _PREV_SHOW))
    else:
        for _m, attr, orig in _PATCHED:
            setattr(_m, attr, orig)
        _PATCHED.clear()


_patch_help(True)


# ---------------------------------------------------------------- closeout v0183
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


def plan_cases(check_text: str, ho: dict) -> tuple:
    """② 的規劃:(要重測的案, 擋路的工作項)。
    要重測 = 發現推得的案(v0182)+ PENDING 工作項的宣告案;
    擋路 = PENDING_WITHOUT_NEXT 的工作項裡,本輪轉不成 VERIFIED 的(非 PENDING,或它的案不在本輪)。"""
    cases_spec = ho.get("test_cases") or {}
    items = [w for w in ho.get("work_items") or [] if isinstance(w, dict)]
    hit = set(affected_cases(check_text, cases_spec, items))
    hit |= {w["case"] for w in items if w.get("state") == "PENDING" and w.get("case") in cases_spec}
    order = list(cases_spec)
    cases = sorted(hit, key=order.index)
    byid = {w.get("id"): w for w in items}
    blockers = []
    for wid in re.findall(r"PENDING_WITHOUT_NEXT (\S+)", check_text):
        w = byid.get(wid, {})
        if not (w.get("state") == "PENDING" and w.get("case") in cases):
            blockers.append(wid)
    return cases, blockers


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
               "head": git("rev-parse", "--short=12", "HEAD")[1].strip(), "engine": Path(__file__).name}
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "CLOSEOUT_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        with open(OUT / "closeout_ledger.jsonl", "a", encoding="utf-8") as f:  # 只增
            f.write(json.dumps({k: res[k] for k in ("run", "at", "apply", "push", "rc", "sec", "head", "engine")}, ensure_ascii=False) + "\n")
        print(f"[VCGC closeout] {'GREEN' if rc == 0 else ('RED' if rc == 1 else 'YELLOW')} · rc {rc} · {res['sec']}s · 記錄 {d}")
        return rc

    def run_tests(cases, tag):
        passed = []
        for c in cases:
            t = time.time()
            rc, txt = sub(["handoff", "test", c], d / f"{tag}_test_{c}.log", timeout=1800)
            rec = next((json.loads(ln) for ln in txt.splitlines() if ln.startswith("{\"case\"")), {})
            ok = rc == 0 and rec.get("marker", False)
            step("③" if tag == "3" else "⑥+", f"test {c}", "GREEN" if ok else "RED", f"rc {rc} · 標記 {rec.get('marker')}", time.time() - t)
            if not ok:
                print(f"  停:{c} 沒過,不往下 checkpoint(看 {d / f'{tag}_test_{c}.log'})")
                return None
            passed.append(c)
        return passed

    print(f"[VCGC closeout] {run} · {'--apply' if apply else '乾跑(不寫冊 · 不提交)'} · {'--push' if push else '不推'} · {Path(__file__).name}", flush=True)
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
    cases, blockers = plan_cases(txt, ho)
    cases = only or cases
    head = next((ln for ln in txt.splitlines() if ln.startswith("[交接防遺漏]")), "").replace("[交接防遺漏] ", "")
    if blockers:
        step("②", "handoff check", "RED", f"工作項缺 owner/next/reason 且本輪轉不了:{','.join(blockers)} → 先在交接冊補三欄(帶理由轉態)", time.time() - t)
        print(f"  停:不白跑測試 —— checkpoint 必紅(看 {d / '2_handoff_check.log'})")
        return finish(1)
    step("②", "handoff check", "GREEN" if rc == 0 else "YELLOW", f"{head[:90]} → 要重測 {len(cases)} 案:{','.join(cases) or '無'}", time.time() - t)
    passed = []
    if not skip_tests:
        passed = run_tests(cases, "3")
        if passed is None:
            return finish(1)
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
    sdd = ms.group(1) if ms else ("GREEN" if rc == 0 else ("RED" if rc == 1 else "YELLOW"))
    step("⑥", "SDD 檢查", sdd, f"rc {rc}", time.time() - t)
    if sdd == "RED":
        print(f"  停:SDD 紅,不 checkpoint(看 {d / '6_sdd.log'})")
        return finish(1)
    if apply and not skip_tests:
        for r in range(1, SETTLE_ROUNDS + 1):
            t = time.time()
            rc, txt = sub(["handoff", "check"], d / f"6s{r}_handoff_check.log")
            ho = json.loads(HANDOFF_SSOT.read_text(encoding="utf-8"))
            again, blockers = plan_cases(txt, ho)
            if blockers:
                step("⑥+", f"收斂 {r}", "RED", f"工作項缺 owner/next/reason:{','.join(blockers)}", time.time() - t)
                return finish(1)
            if not again:
                step("⑥+", f"收斂 {r}", "GREEN", "沒有被本輪弄失效的證據", time.time() - t)
                break
            if r == SETTLE_ROUNDS:
                step("⑥+", f"收斂 {r}", "RED", f"{SETTLE_ROUNDS} 圈仍有失效:{','.join(again)} → 不硬 checkpoint", time.time() - t)
                return finish(1)
            step("⑥+", f"收斂 {r}", "YELLOW", f"本輪自己弄失效 {len(again)} 案:{','.join(again)} → 重測", time.time() - t)
            ok = run_tests(again, f"6s{r}")
            if ok is None:
                return finish(1)
            n = verify_work_items(ok)
            step("⑥+", f"收斂 {r} 提交", "GREEN", f"轉 VERIFIED {n} 項 · " + commit(f"vcgc closeout: settle {r} · 重測 {','.join(ok)}"), 0)
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
            PRIOR.PRIOR.auto_monitor(args)
    return PRIOR.PRIOR.main(args)


# ---------------------------------------------------------------- selftest
def selftest():
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    ho = {"test_cases": {"numbering": {"dependencies": ["r/VIA_Handoff*.json"]}, "entry": {"dependencies": []}, "deck": {"dependencies": []}},
          "work_items": [{"id": "A:numbering", "case": "numbering", "state": "VERIFIED"},
                         {"id": "B:entry", "case": "entry", "state": "PENDING"},
                         {"id": "C:entry", "case": "entry", "state": "BLOCKED"},
                         {"id": "D:deck", "case": "deck", "state": "VERIFIED"}]}
    txt = ("[RED] EVIDENCE_INVALID {'id': 'A:numbering', 'why': ['dependency changed']}\n"
           "[RED] PENDING_WITHOUT_NEXT B:entry\n[RED] PENDING_WITHOUT_NEXT C:entry\n")
    cases, blockers = plan_cases(txt, ho)
    chk("② 規劃:失效證據的案 + PENDING 工作項的案都排進重測(照冊序)", cases == ["numbering", "entry"], cases)
    chk("② 先攔:BLOCKED 缺欄 = 擋路;PENDING 而本輪會測到 = 不擋(過了就轉 VERIFIED)", blockers == ["C:entry"], blockers)
    cases2, blockers2 = plan_cases("", {"test_cases": ho["test_cases"], "work_items": [w for w in ho["work_items"] if w["state"] != "PENDING"]})
    chk("沒有發現 · 沒有 PENDING = 不重測(收斂條件)", cases2 == [] and blockers2 == [], (cases2, blockers2))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥+ 收斂在 ⑦ checkpoint 前 · 有上限 · 用盡 = RED 停", src.index('"⑥+", f"收斂 {r}"') < src.index('sub(["handoff", "checkpoint"]') and SETTLE_ROUNDS == 3
        and "仍有失效" in src)
    chk("同意閘照舊:寫冊 / 提交只在 --apply · 推送只在 --push · 不強推 · 子步 VIA_VCGC_PUSH=NO",
        "if apply and pend:" in src and "if push:" in src and '"push", "origin", "HEAD"' in src and ("--" + "force") not in src
        and '"VIA_VCGC_PUSH": "NO"' in src)
    chk("停損:案沒過 / 擋路工作項 / 稽核非 0 / SDD 紅 / 收斂用盡 都不 checkpoint", src.count("return finish(1)") >= 8)
    seen, calls = [], []
    real_main, real_auto = PRIOR.PRIOR.main, PRIOR.PRIOR.auto_monitor
    PRIOR.PRIOR.main = lambda a: seen.append(list(a)) or 0
    PRIOR.PRIOR.auto_monitor = lambda a, launcher=None: calls.append(list(a)) or "stub"
    env = os.environ.get("VIA_FROM_VCGC")
    try:
        os.environ.pop("VIA_FROM_VCGC", None)
        denied = main(["closeout"])
        passthru = main(["status"])
    finally:
        PRIOR.PRIOR.main, PRIOR.PRIOR.auto_monitor = real_main, real_auto
        if env is None:
            os.environ.pop("VIA_FROM_VCGC", None)
        else:
            os.environ["VIA_FROM_VCGC"] = env
    chk("closeout 不經 VCGC 拒跑 · 拒跑也觸發監控 · 其他動詞原樣轉交", denied == 2 and calls == [["closeout"]] and seen == [["status"]] and passthru == 0,
        (seen, calls))
    card = help_catalog()
    chk("help 目前生效入口 = 本版", card.get("entry") == Path(__file__).name and card.get("previous") == PRIOR_PATH.name and "v0183" in card.get("closeout", ""))
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
