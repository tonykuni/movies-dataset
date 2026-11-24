#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VCGC_CommandHub v0115 — 薄尾(v0100–v0114 一字不動):新短令 via-graph · via-bak 多 restore / card / check

操作員 2026-11-24:「可以用 PY 寫這個引擎然後用短指令啟動?? 強化備份功能」→ 選「多 AI 備份共顯節省 TOKEN · 一鍵還原 + 還原前驗證」·
短令 via-graph + via-bak。不另寫 Graphify 引擎:Graphify 早已併進 VCGC(CGC_MDL280_VCGCAgentOSHub · 隔離環境 · code-only ·
GRAPHIFY_BACKEND=none · 一個系統一張圖);備份是 VIA_DailyBackup 尾版。本中樞只把它們收成一行指令。

  via-graph status                       Graphify 就緒嗎 + 各系統圖在不在(圖 · 時間 · 大小)
  via-graph build --sys VDF[,VRN,…]       逐系統建圖(CGC_MDL280 graphify run)→ 每張圖寫快照 SNAPSHOT_<系統>_latest.json
                                         (倉的提交 · 工作樹改動數 · graph.json sha256 · 節點 / 連線)+ 只增帳 SNAPSHOT_ledger.jsonl;
                                         任一步不過就停(rc ≠ 0),不會像逐行貼 PS 那樣 throw 了還往下跑。不給 --sys 只列可建的系統。
  via-graph query "<問題>" [--sys S]      在既有圖上查(graphify query / path / explain · --graph 指到各系統的 graph.json);
  via-graph path "<起>" "<訖>" [--sys S]   不給 --sys = 每張圖都查一次。全部離線(GRAPHIFY_BACKEND=none)。
  via-graph explain "<節點>" [--sys S]
  via-bak restore [--stamp T] [--sys S] [--only 片段] [--apply]   一鍵還原(先驗證 · 預設乾跑 · --apply 先另存現檔)→ VIA_DailyBackup 尾版
  via-bak card                           重寫多 AI 共讀的備份卡 docs/handoff/backup/BACKUP_CARD_latest.md
  via-bak check                          對倉(同 VIA_DailyBackup check)
  via-bak(不帶子動詞)                  照 v0105:ApplyRun G 道(Graphify · OmniRoute · 備份 + check)
不 import 他系統;CGC_MDL280 是 VCGC 自己的模組(子行程呼叫);零 TA-Lib;不設同意閘。
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

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VCGC_CommandHub"
TAG = "VCGC_CommandHub v0115"
REG_DIR = HERE / "supportive modules" / "registry"
AI_DIR = HERE / "docs" / "handoff" / "ai"
GRAPH_OUT = HERE / "VIA_Reports" / "vcgc" / "agentos" / "graphify"      # = CGC_MDL280 的預設輸出夾
GRAPH_SYSTEMS = ("VRN", "VRN_Shared", "VDF", "VCGC", "VQG", "AOS")       # = CGC_MDL280 GRAPHIFY_SYSTEMS
BAK_VERBS = ("restore", "card", "check")


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
    return getattr(PRIOR, name)


def _owner(name: str):
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if name in vars(m):
            return m
        m = vars(m).get("PRIOR") or vars(m).get("P0")
    return None


DISPATCH_OWNER = _owner("dispatch")                      # v0102:CMD / COMMANDS / main(route 鏈)
_PREV_MAIN = DISPATCH_OWNER.main


def _tail(d: Path, family: str) -> Path | None:
    c = [p for p in d.glob(family + "_v*.py") if _vnum(p) >= 0]
    return max(c, key=_vnum) if c else None


def _env() -> dict:
    return dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", GRAPHIFY_BACKEND="none", GRAPHIFY_QUERY_LOG_DISABLE="1")


def _opt(args: list, name: str) -> str | None:
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else None


def _positional(args: list) -> list:
    out, skip = [], False
    for x in args:
        if skip:
            skip = False
            continue
        if x == "--sys":
            skip = True
            continue
        out.append(x)
    return out


def graph_files(out: Path = None) -> dict:
    base = out or GRAPH_OUT
    return {d.name: d / "graphify-out" / "graph.json" for d in sorted(base.glob("*")) if (d / "graphify-out" / "graph.json").is_file()}


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_state(repo: Path, run=subprocess.run) -> dict:
    """唯讀:提交 + 工作樹改動數(拿不到就照實寫 None,不擋建圖,但快照會標出來)。"""
    try:
        head = run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=60)
        st = run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return {"commit": None, "dirty": None, "why": "git 叫不起來"}
    if head.returncode != 0:
        return {"commit": None, "dirty": None, "why": (head.stderr or "").strip()[:160]}
    lines = [x for x in (st.stdout or "").splitlines() if x.strip()]
    return {"commit": head.stdout.strip(), "dirty": len(lines), "dirty_sample": lines[:10]}


def write_snapshot(system: str, out: Path, git: dict) -> dict:
    rec = json.loads((out / ("VIA_Graphify_%s_latest.json" % system)).read_text(encoding="utf-8"))
    g = Path(rec["graph"])
    snap = {"schema": "VIA-GRAPH-SNAPSHOT/1.0", "tool": TAG, "system": system, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_commit": git.get("commit"), "working_tree_changes": git.get("dirty"), "working_tree_sample": git.get("dirty_sample", []),
            "graph": str(g), "graph_sha256": _sha(g), "nodes": rec.get("nodes"), "edges": rec.get("edges"),
            "version": rec.get("version"), "mode": rec.get("mode"), "receipt_at": rec.get("at")}
    (out / ("SNAPSHOT_%s_latest.json" % system)).write_text(json.dumps(snap, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with open(out / "SNAPSHOT_ledger.jsonl", "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({k: snap[k] for k in ("at", "system", "source_commit", "working_tree_changes", "graph_sha256", "nodes", "edges")},
                           ensure_ascii=False) + "\n")
    return snap


def _mdl280_exe():
    t = _tail(REG_DIR, "CGC_MDL280_VCGCAgentOSHub")
    if t is None:
        return None, None
    spec = importlib.util.spec_from_file_location("cgc_mdl280_for_hub115", t)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return t, m.graphify_exe()


def cmd_graph(args: list, run=subprocess.run, out: Path = None) -> int:
    out = out or GRAPH_OUT
    sub = args[0] if args else "status"
    rest = args[1:]
    mdl = _tail(REG_DIR, "CGC_MDL280_VCGCAgentOSHub")
    if mdl is None:
        print("[via-graph] 找不到 CGC_MDL280_VCGCAgentOSHub 尾版 → 先 git pull")
        return 3
    if sub == "status":
        rc = run([sys.executable, str(mdl), "graphify", "status"], env=_env(), cwd=str(HERE)).returncode
        files = graph_files(out)
        for s in GRAPH_SYSTEMS:
            p = files.get(s)
            snap = out / ("SNAPSHOT_%s_latest.json" % s)
            print("  %-10s %s" % (s, ("有圖 · %.1f MB · %s%s" % (p.stat().st_size / 1e6, datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                                                               " · 有快照" if snap.is_file() else " · 沒快照")) if p else "沒圖(via-graph build --sys %s)" % s))
        return rc
    if sub == "build":
        want = [s for s in (_opt(rest, "--sys") or "").split(",") if s]
        if not want:
            print("[via-graph] build 要指定系統(一次一張,大夾吃記憶體):--sys %s" % ",".join(GRAPH_SYSTEMS))
            return 2
        bad = [s for s in want if s not in GRAPH_SYSTEMS]
        if bad:
            print("[via-graph] 不認識的系統:%s(可用 %s)" % (bad, ",".join(GRAPH_SYSTEMS)))
            return 2
        git = git_state(HERE.parent, run=run)
        if git.get("commit") is None:
            print("[via-graph] [YELLOW] 讀不到倉的提交(%s)→ 照建圖,快照的 source_commit 會是空的" % git.get("why"))
        for s in want:
            print("[via-graph] 建圖 %s(CGC_MDL280 graphify run · code-only · 離線)" % s, flush=True)
            rc = run([sys.executable, str(mdl), "graphify", "run", "--system", s, "--out", str(out.parent)], env=_env(), cwd=str(HERE)).returncode
            receipt = out / ("VIA_Graphify_%s_latest.json" % s)
            ok = rc == 0 and receipt.is_file() and json.loads(receipt.read_text(encoding="utf-8")).get("lamp") == "GREEN"
            if not ok:
                print("[via-graph] [RED] %s 建圖沒完成(rc %s · 收據 %s)→ 停,後面的系統不跑" % (s, rc, "在" if receipt.is_file() else "不在"))
                return rc or 1
            snap = write_snapshot(s, out, git)
            print("[via-graph] [GREEN] %s · 節點 %s · 連線 %s · 圖 sha %s · 提交 %s · 工作樹改動 %s" % (
                s, snap["nodes"], snap["edges"], snap["graph_sha256"][:12], (snap["source_commit"] or "—")[:12], snap["working_tree_changes"]))
        return 0
    if sub in ("query", "path", "explain"):
        pos = _positional(rest)
        need = 2 if sub == "path" else 1
        if len(pos) < need:
            print('[via-graph] 用法:via-graph %s %s [--sys S]' % (sub, '"<起>" "<訖>"' if sub == "path" else '"<文字>"'))
            return 2
        files = graph_files(out)
        sysf = _opt(rest, "--sys")
        targets = {sysf: files[sysf]} if sysf and sysf in files else ({} if sysf else files)
        if not targets:
            print("[via-graph] 沒有可查的圖%s → via-graph build --sys <系統>" % (("(%s 沒圖)" % sysf) if sysf else ""))
            return 3
        _t, exe = _mdl280_exe()
        if exe is None:
            print("[via-graph] 這台沒有 Graphify 隔離環境 → via-vcgc graphify status 看怎麼裝")
            return 3
        worst = 0
        for s, g in targets.items():
            print("── %s · %s ──" % (s, g), flush=True)
            rc = run([str(exe), sub, *pos[:need], "--graph", str(g)], env=_env(), cwd=str(HERE)).returncode
            worst = max(worst, rc)
        return worst
    print("[via-graph] 動詞:status · build --sys S · query \"<文字>\" · path \"<起>\" \"<訖>\" · explain \"<節點>\"(可加 --sys S)")
    return 2


def cmd_bak_sub(args: list, run=subprocess.run) -> int:
    t = _tail(AI_DIR, "VIA_DailyBackup")
    if t is None:
        print("[via-bak] 找不到 VIA_DailyBackup 尾版 → 先 git pull")
        return 3
    return run([sys.executable, str(t), *args], env=_env(), cwd=str(HERE)).returncode


def route(argv: list | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["graph"]:
        return cmd_graph(a[1:])
    if a[:1] == ["bak"] and a[1:2] and a[1] in BAK_VERBS:
        return cmd_bak_sub(a[1:])
    return _PREV_MAIN(a)


DISPATCH_OWNER.main = route
if "via-graph" not in DISPATCH_OWNER.CMD:
    DISPATCH_OWNER.COMMANDS.append({
        "name": "via-graph", "group": "維護", "title": "程式碼知識圖譜(Graphify · 離線)", "target": ["graph"],
        "plugin": "CGC_MDL280_VCGCAgentOSHub 尾版 graphify(隔離環境 · code-only · GRAPHIFY_BACKEND=none)",
        "help": "status 看就緒與各系統圖;build --sys VDF 建圖並寫快照(提交 · 工作樹改動數 · 圖 sha256);"
                "query / path / explain 在既有圖上查(不給 --sys = 每張圖都查)。一次一個系統,大夾吃記憶體。",
        "examples": ["via-graph status", "via-graph build --sys VDF", 'via-graph query "parquet align" --sys VDF',
                     'via-graph path "VDF_SystemManager" "DataPlane" --sys VDF', 'via-graph explain "launch_run" --sys VCGC'],
        "replaces": []})
    DISPATCH_OWNER.CMD["via-graph"] = DISPATCH_OWNER.COMMANDS[-1]
_BAK = DISPATCH_OWNER.CMD.get("via-bak")
if _BAK is not None and "via-bak restore" not in _BAK.get("examples", []):
    _BAK["examples"] = list(_BAK.get("examples", [])) + ["via-bak check", "via-bak restore", "via-bak restore --apply --sys VCGC", "via-bak card"]
    _BAK["help"] = (_BAK.get("help", "") + " · 子動詞:check 對倉 · restore 一鍵還原(先驗證 · 預設乾跑 · --apply 先另存現檔)· "
                    "card 重寫多 AI 共讀的備份卡(docs/handoff/backup/BACKUP_CARD_latest.md)")


def main(argv: list | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["graph"]:
        return cmd_graph(a[1:])
    if a[:1] == ["bak"] and a[1:2] and a[1] in BAK_VERBS:
        return cmd_bak_sub(a[1:])
    return PRIOR.main(a)


def selftest() -> int:
    import contextlib
    import io
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 6 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 via-graph 登記 · via-bak 範例多 restore / card / check · route 換在 v0102 那一層",
        "via-graph" in DISPATCH_OWNER.CMD and DISPATCH_OWNER.main is route
        and "via-bak restore" in DISPATCH_OWNER.CMD["via-bak"]["examples"] and PRIOR_PATH.name == "VCGC_CommandHub_v0114.py")
    calls = []

    def fake(argv, **kw):
        calls.append(list(argv))
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
    with contextlib.redirect_stdout(io.StringIO()):
        rc = cmd_bak_sub(["restore", "--sys", "VCGC"], run=fake)
    chk("T2 via-bak restore → VIA_DailyBackup 尾版 restore(參數原樣)", rc == 0 and calls and calls[-1][1].endswith(".py")
        and "VIA_DailyBackup_v" in calls[-1][1] and calls[-1][2:] == ["restore", "--sys", "VCGC"], calls[-1:])
    with tempfile.TemporaryDirectory(prefix="hub115_") as td:
        out = Path(td) / "graphify"
        (out / "VDF" / "graphify-out").mkdir(parents=True)
        g = out / "VDF" / "graphify-out" / "graph.json"
        g.write_text('{"nodes": [1, 2], "links": [1]}', encoding="utf-8")

        def fake_build(argv, **kw):
            calls.append(list(argv))
            if argv[:2] == ["git", "-C"]:
                return type("R", (), {"returncode": 0, "stdout": "abc123\n" if "rev-parse" in argv else " M a.py\n", "stderr": ""})()
            if "run" in argv and "--system" in argv:
                (out / "VIA_Graphify_VDF_latest.json").write_text(json.dumps({"lamp": "GREEN", "nodes": 2, "edges": 1, "graph": str(g),
                                                                               "version": "graphify 0.9.100", "at": "now"}), encoding="utf-8")
            return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        with contextlib.redirect_stdout(io.StringIO()):
            rc_none = cmd_graph(["build"], run=fake_build, out=out)
            rc_b = cmd_graph(["build", "--sys", "VDF"], run=fake_build, out=out)
        snap = json.loads((out / "SNAPSHOT_VDF_latest.json").read_text(encoding="utf-8")) if (out / "SNAPSHOT_VDF_latest.json").is_file() else {}
        chk("T3 build 不給 --sys 不亂跑(rc 2);--sys VDF → 建圖後寫快照(提交 · 工作樹改動數 · 圖 sha256 · 節點)+ 只增帳",
            rc_none == 2 and rc_b == 0 and snap.get("source_commit") == "abc123" and snap.get("working_tree_changes") == 1
            and snap.get("graph_sha256") == _sha(g) and snap.get("nodes") == 2 and (out / "SNAPSHOT_ledger.jsonl").is_file(), snap)

        def fake_fail(argv, **kw):
            calls.append(list(argv))
            if argv[:2] == ["git", "-C"]:
                return type("R", (), {"returncode": 0, "stdout": "abc\n", "stderr": ""})()
            return type("R", (), {"returncode": 1, "stdout": "", "stderr": ""})()
        (out / "VIA_Graphify_VRN_latest.json").unlink(missing_ok=True)
        n0 = len(calls)
        with contextlib.redirect_stdout(io.StringIO()):
            rc_f = cmd_graph(["build", "--sys", "VRN,VDF"], run=fake_fail, out=out)
        ran = [c for c in calls[n0:] if "--system" in c]
        chk("T4 建圖失敗就停:第一個系統紅 → rc ≠ 0、後面的系統不跑", rc_f != 0 and len(ran) == 1 and "VRN" in ran[0], ran)
        keep = _mdl280_exe
        globals()["_mdl280_exe"] = lambda: (None, Path("/fake/graphify"))
        n0 = len(calls)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                rc_q = cmd_graph(["query", "parquet align", "--sys", "VDF"], run=fake, out=out)
        finally:
            globals()["_mdl280_exe"] = keep
        q = calls[n0:]
        chk("T5 query 帶 --graph 指到該系統的 graph.json · 離線(GRAPHIFY_BACKEND=none)",
            rc_q == 0 and q and q[0][1:3] == ["query", "parquet align"] and q[0][-2:] == ["--graph", str(g)] and _env()["GRAPHIFY_BACKEND"] == "none", q)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("T6 檔面:加速器橋 · 零 TA-Lib · 不設同意閘 · 不 import 他系統",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", body, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body) and not re.search(r"^\s*(import|from)\s+(VDF_|VRN_|VQG_|VAP_)", body, re.M))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(route 還原成前版的)" % PRIOR_PATH.name, flush=True)
    DISPATCH_OWNER.main = _PREV_MAIN
    try:
        rc_prior = PRIOR.selftest()
    finally:
        DISPATCH_OWNER.main = route
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
