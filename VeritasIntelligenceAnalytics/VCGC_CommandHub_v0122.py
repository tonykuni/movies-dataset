#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VCGC_CommandHub v0122 — 薄尾(前版一字不動;v0121 號已被開著的 PR #766 用掉 → 改發 v0122):via-graph 短令真的走得到 · 舊短令 via-graphify / via-omniroute 照原意

main 尾版 v0120 實測(2026-11-27,容器):`x via-graph status` → `invalid choice: 'graph'`(主機 11-25 同一句實錄)。
  根因:v0115 的 route 掛在 v0113(_owner("dispatch") 找到的是 v0113,它也定義 dispatch),但 v0102 的 dispatch 讀的是 v0102 自己的
  main;本分支當時在 v0117 改過這層,那個提交沒進 main(#740 合併的是另一版 v0117)。
本版(不加新指令名,22 + 21 照舊):
  ① graph_route 掛在擁有 CMD 與 dispatch 的那一層(現為 v0102)的 main:x 短令 · 選單都認得 graph 與 bak 的子動詞;其餘照原路;
  ② via-graphify → via-graph(沒給子動詞 = status);via-omniroute → 只叫三系統各自入口的 omniroute(VCGC = CGC_SystemManager ·
     VDF / VRN = 各自 SystemManager 尾版),入口找不到 = 黃 · 非 0 = 紅 · 全綠才 rc 0 · --sys 縮範圍;
  ③ 短令冊:via-graphify 移到 via-graph 的 replaces;via-bak 的 help 補一句 via-omniroute。
OmniRoute 只是各系統自己的路由收據,不進引擎執行路徑;子行程叫各系統自己的入口,不 import 他系統。零 TA-Lib。不設同意閘。
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
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VCGC_CommandHub"
TAG = "VCGC_CommandHub v0122"
ROUTE_ENTRIES = (("VCGC", "CGC_SystemManager"), ("VDF", "VDF_SystemManager"), ("VRN", "VRN_SystemManager"))


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _chain_mods() -> list:
    out, m, seen = [], PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        out.append(m)
        m = vars(m).get("PRIOR") or vars(m).get("P0")
    return out


CMD_HOME = next(m for m in _chain_mods() if "CMD" in vars(m) and "dispatch" in vars(m))     # v0102:x 路與選單都叫它的 dispatch
TAIL_HOME = next(m for m in _chain_mods() if "find_tail" in vars(m) and "tool_root" in vars(m))   # v0101:找各系統尾版
_DISPATCH_PREV = CMD_HOME.dispatch
V115 = next((m for m in _chain_mods() if "cmd_graph" in vars(m) and "BAK_VERBS" in vars(m)), None)   # via-graph / via-bak 子動詞本體
_HOME_PREV = CMD_HOME.main


def graph_route(argv: list | None = None) -> int:
    """掛在 dispatch 真正讀的那一層的 main:graph 與 bak 的子動詞走本體;其餘照原路。"""
    a = list(sys.argv[1:] if argv is None else argv)
    if V115 is not None and a[:1] == ["graph"]:
        return V115.cmd_graph(a[1:])
    if V115 is not None and a[:1] == ["bak"] and a[1:2] and a[1] in V115.BAK_VERBS:
        return V115.cmd_bak_sub(a[1:])
    return _HOME_PREV(a)
_HB = vars(PRIOR).get("_PREV_HB") or PRIOR.hb_run                                          # v0116 的心跳(非建圖)
_SNAP = {k: (list(CMD_HOME.CMD[k]["replaces"]), CMD_HOME.CMD[k]["help"]) for k in ("via-bak", "via-graph") if k in CMD_HOME.CMD}
_LEGACY_SNAP = dict(CMD_HOME.LEGACY)
LEGACY_INTENT = {"via-graphify": "via-graph", "via-omniroute": "omniroute"}


def legacy_target(name: str, args: list) -> tuple:
    """舊名 → (去處, 參數)。via-graphify → graph(沒子動詞補 status);via-omniroute → omniroute;其他原樣。"""
    a = list(args)
    if name == "via-graphify":
        return "graph", (a if a and not a[0].startswith("-") else ["status", *a])
    if name == "via-omniroute":
        return "omniroute", a
    return name, a


def _pick(args: list) -> tuple:
    want, rest, i = None, [], 0
    while i < len(args):
        if args[i] == "--sys" and i + 1 < len(args):
            want = {s.strip().upper() for s in args[i + 1].split(",") if s.strip()}
            i += 2
            continue
        rest.append(args[i])
        i += 1
    return want, rest


def omniroute_all(args: list, run=None, find=None, log=print) -> int:
    """三系統各自入口的 omniroute 動詞(子行程 · 各在自己的根跑 · 只寫自己的夾)。全綠才 rc 0。"""
    run = run or _HB
    find = find or TAIL_HOME.find_tail
    want, rest = _pick(args)
    bad = sorted((want or set()) - {s for s, _ in ROUTE_ENTRIES})
    if bad:
        log("[via-omniroute] 不認得的系統 %s(只有 VCGC · VDF · VRN 有 omniroute)" % ",".join(bad), flush=True)
        return 2
    rows = []
    hb_log = lambda *a, **k: log(*(str(x).replace("[via-graph]", "[via-omniroute]") for x in a), **k)   # noqa: E731
    for sysname, fam in ROUTE_ENTRIES:
        if want and sysname not in want:
            continue
        t = find(fam)
        if not t:
            rows.append((sysname, "黃", "入口 %s 找不到(git pull 後再跑)" % fam, None))
            continue
        try:
            cp = run([sys.executable, str(t), "omniroute", *rest], cwd=str(TAIL_HOME.tool_root(Path(t))), capture_output=True,
                     text=True, timeout=900, log=hb_log)
        except subprocess.TimeoutExpired:
            rows.append((sysname, "黃", "逾時 900 秒", None))
            continue
        last = [ln for ln in (cp.stdout or "").splitlines() if ln.strip() and "SyntaxWarning" not in ln]
        rows.append((sysname, "綠" if cp.returncode == 0 else "紅", (last[-1] if last else "(沒輸出)")[:160], cp.returncode))
    for sysname, lamp, note, rc in rows:
        log("[via-omniroute] %-4s %s · rc %s · %s" % (sysname, lamp, "-" if rc is None else rc, note), flush=True)
    ok = rows and all(lamp == "綠" for _, lamp, _, _ in rows)
    log("[via-omniroute] %s · %d 系統 · 綠 %d" % ("全綠" if ok else "未全綠", len(rows), sum(r[1] == "綠" for r in rows)), flush=True)
    return 0 if ok else 1


def dispatch(name: str, args: list) -> int:
    if name in LEGACY_INTENT:
        where, a = legacy_target(name, args)
        if where == "graph":
            print("[去重] via-graphify 已併入 via-graph(%s)" % " ".join(a), file=sys.stderr)
            return CMD_HOME.main(["graph", *a])
        print("[去重] via-omniroute 照原意:只跑三系統各自的 omniroute(不連備份)", file=sys.stderr)
        return omniroute_all(a)
    return _DISPATCH_PREV(name, args)


def install() -> None:
    CMD_HOME.dispatch = dispatch
    CMD_HOME.main = graph_route
    if "via-graph" in CMD_HOME.CMD and "via-graphify" not in CMD_HOME.CMD["via-graph"]["replaces"]:
        CMD_HOME.CMD["via-bak"]["replaces"] = [x for x in CMD_HOME.CMD["via-bak"]["replaces"] if x != "via-graphify"]
        CMD_HOME.CMD["via-graph"]["replaces"] = [*CMD_HOME.CMD["via-graph"]["replaces"], "via-graphify"]
        CMD_HOME.LEGACY["via-graphify"] = "via-graph"
    h = CMD_HOME.CMD["via-bak"]["help"]
    if "via-omniroute" not in h:
        CMD_HOME.CMD["via-bak"]["help"] = h + " 舊名 via-omniroute = 只跑三系統 omniroute(--sys 縮範圍)。"


def _restore() -> None:
    CMD_HOME.dispatch = _DISPATCH_PREV
    CMD_HOME.main = _HOME_PREV
    for k, (rep, hp) in _SNAP.items():
        CMD_HOME.CMD[k]["replaces"], CMD_HOME.CMD[k]["help"] = list(rep), hp
    CMD_HOME.LEGACY.clear()
    CMD_HOME.LEGACY.update(_LEGACY_SNAP)


install()


def main(argv: list | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    import contextlib
    import io
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 7 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("① 掛在擁有短令冊與 dispatch 的那一層 · 前版比本版小 · 舊名數量不變",
        all(k in vars(CMD_HOME) for k in ("CMD", "LEGACY", "COMMANDS", "dispatch")) and CMD_HOME.dispatch is dispatch
        and 0 <= _vnum(PRIOR_PATH) < _vnum(__file__) and len(CMD_HOME.LEGACY) == len(_LEGACY_SNAP)
        and sum(len(c["replaces"]) for c in CMD_HOME.COMMANDS) == len(CMD_HOME.LEGACY), (PRIOR_PATH.name, len(CMD_HOME.LEGACY)))
    chk("② via-graphify:沒子動詞 → graph status · 有子動詞照轉 · 旗標開頭也補 status;短令冊指 via-graph",
        legacy_target("via-graphify", []) == ("graph", ["status"]) and legacy_target("via-graphify", ["build", "--sys", "VDF"]) == ("graph", ["build", "--sys", "VDF"])
        and legacy_target("via-graphify", ["--json"]) == ("graph", ["status", "--json"]) and CMD_HOME.LEGACY["via-graphify"] == "via-graph"
        and "via-graphify" in CMD_HOME.CMD["via-graph"]["replaces"] and "via-graphify" not in CMD_HOME.CMD["via-bak"]["replaces"])
    seen, keep = [], CMD_HOME.main
    calls = []
    fake_run = lambda argv, **k: calls.append([Path(argv[1]).name, *argv[2:]]) or subprocess.CompletedProcess(argv, 0, "x\nomniroute GREEN\n", "")  # noqa: E731
    keep_find = TAIL_HOME.find_tail
    with tempfile.TemporaryDirectory(prefix="vcgc_hub122_") as d:
        fakes = {fam: Path(d) / (fam + "_v0999.py") for _, fam in ROUTE_ENTRIES}
        try:
            CMD_HOME.main = lambda a=None: seen.append(list(a)) or 0
            TAIL_HOME.find_tail = lambda fam, roots=None: fakes.get(fam)
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                r = [keep(["x", "via-graphify"]), CMD_HOME.dispatch("via-graphify", ["build"])]
                r_all = omniroute_all([], run=fake_run)
                r_one = omniroute_all(["--sys", "vdf"], run=fake_run)
                r_bad = omniroute_all(["--sys", "VQG"], run=fake_run)
        finally:
            CMD_HOME.main = keep
            TAIL_HOME.find_tail = keep_find
    chk("③ x 路(PS 載入器)與選單路都把 via-graphify 送進 graph",
        r == [0, 0] and seen[:2] == [["graph", "status"], ["graph", "build"]], (r, seen))
    chk("④ via-omniroute:三系統各叫自己入口的 omniroute · --sys 縮範圍(不分大小寫)· 不認得的系統 rc 2 不叫任何入口",
        r_all == 0 and r_one == 0 and r_bad == 2 and calls == [["CGC_SystemManager_v0999.py", "omniroute"], ["VDF_SystemManager_v0999.py", "omniroute"],
                                                               ["VRN_SystemManager_v0999.py", "omniroute"], ["VDF_SystemManager_v0999.py", "omniroute"]], (r_all, r_one, r_bad, calls))
    lines = []
    miss = omniroute_all([], run=fake_run, find=lambda fam: None if fam == "VRN_SystemManager" else Path("/x") / (fam + "_v0999.py"),
                         log=lambda *a, **k: lines.append(" ".join(map(str, a))))
    red = omniroute_all(["--sys", "VCGC"], run=lambda argv, **k: subprocess.CompletedProcess(argv, 3, "boom\n", ""), log=lambda *a, **k: None)
    chk("⑤ 入口找不到 = 黃 · 總 rc 1(SKIP 不是綠)· 子行程非 0 = 紅 rc 1",
        miss == 1 and any("VRN" in x and "黃" in x for x in lines) and red == 1, (miss, red, lines[-2:]))
    got = []
    if V115 is not None:
        kg, kb = V115.cmd_graph, V115.cmd_bak_sub
        try:
            V115.cmd_graph = lambda a, **k: got.append(("graph", list(a))) or 0
            V115.cmd_bak_sub = lambda a, **k: got.append(("bak", list(a))) or 0
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                rr = [CMD_HOME.main(["x", "via-graph", "status"]), CMD_HOME.dispatch("via-graph", ["build", "--sys", "VDF"]),
                      CMD_HOME.main(["x", "via-bak", "card"])]
        finally:
            V115.cmd_graph, V115.cmd_bak_sub = kg, kb
    chk("⑦ 主機實錄重現:x via-graph / 選單 via-graph 都走到建圖本體 · via-bak card 走到子動詞(不再 invalid choice 'graph')",
        V115 is not None and CMD_HOME.main is graph_route and got == [("graph", ["status"]), ("graph", ["build", "--sys", "VDF"]), ("bak", ["card"])], got)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑥ 檔面:加速器橋 · 零 TA-Lib · 不設同意閘 · 不 import 他系統",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", body, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body) and not re.search(r"^\s*(import|from)\s+(VDF_|VRN_|VQG_|VAP_|CGC_)", body, re.M))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(dispatch 與短令冊還原成前版的)" % PRIOR_PATH.name, flush=True)
    _restore()
    try:
        rc_prior = PRIOR.selftest()
    finally:
        install()
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
