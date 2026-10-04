# -*- coding: utf-8 -*-
"""CGC_MDL257 AiVerbLadder v0100 — AI 梯次指令引擎 (一步通過才能下一步, 每步回報互動)。
輸入 = 指定引擎 (python 檔)。梯次固定 13 段:
  TEST1→DEBUG1→OPTIMIZE→TEST2→DEBUG2→CONSOLIDATE→TEST3→DEBUG3→USER-TEST→DEBUG4→ACTIVATE→TEST4→DEBUG5
規則: 每次呼叫只推「下一段」; 該段 FAIL/WAIT 就停在原地, 重跑同段直到過; 不可跳段。
狀態存 VIA_Reports/aiverb/LADDER_<引擎名>.json (只增歷史)。
各段語意 (離線 · 只讀引擎 · 絕不改目標):
  TESTn      : python <引擎> --selftest; rc=0 且無 FAIL 行 = PASS。
  DEBUGn     : 上一 TEST 綠 -> PASS(無待修); 紅 -> 印診斷 (尾段輸出+語法+未定義名) 並重驗 selftest, 仍紅 = FAIL。
  OPTIMIZE   : 標準化體檢 (可解析/模組說明/公開說明/無未定義名) 全過 = PASS; 否則列修條。
  CONSOLIDATE: 檔內同軀體指紋重複函式 = 0 才 PASS; 否則列重複組。
  USER-TEST  : 人工閘 — 帶 --userok "<備註>" 才 PASS, 否則 WAIT (印給使用者的測試指引)。
  ACTIVATE   : 帶 --approve 才記啟用 (sha256+時間入帳), 否則 WAIT。不自動部署, 置換仍走 promote。
用法:
  python CGC_MDL257_AiVerbLadder_v0100.py <引擎.py> step [--userok 備註] [--approve]
  python CGC_MDL257_AiVerbLadder_v0100.py <引擎.py> status
  python CGC_MDL257_AiVerbLadder_v0100.py <引擎.py> reset
  python CGC_MDL257_AiVerbLadder_v0100.py --selftest
"""
from __future__ import annotations

<<<<<<< HEAD
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

=======
>>>>>>> @{-1}
import ast
import builtins
import hashlib
import json
import os
import re
import subprocess
import sys
import datetime as dt
from pathlib import Path

SEQ = ["TEST1", "DEBUG1", "OPTIMIZE", "TEST2", "DEBUG2", "CONSOLIDATE",
       "TEST3", "DEBUG3", "USER-TEST", "DEBUG4", "ACTIVATE", "TEST4", "DEBUG5"]
STEP_SEC = int(os.environ.get("VIA_LADDER_SEC", "90"))


def _state_dir() -> Path:
    root = Path(os.environ.get("VIA_ROOT", Path(__file__).resolve().parent))
    d = root / "VIA_Reports" / "aiverb"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _state_path(engine: Path) -> Path:
    return _state_dir() / ("LADDER_%s.json" % re.sub(r"[^\w.-]", "_", engine.stem))


def _load(engine: Path) -> dict:
    p = _state_path(engine)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {"engine": str(engine), "seq": SEQ, "cursor": 0, "stages": {}, "history": []}


def _save(engine: Path, st: dict) -> None:
    _state_path(engine).write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------- 各段檢核 ---------------------
def _run_selftest(engine: Path) -> dict:
    try:
        proc = subprocess.run([sys.executable, str(engine), "--selftest"],
                              capture_output=True, text=True, timeout=STEP_SEC)
    except subprocess.TimeoutExpired:
        return {"ok": False, "rc": 124, "tail": ["(看門狗) selftest 超過 %ds" % STEP_SEC]}
    lines = [l for l in (proc.stdout + "\n" + proc.stderr).splitlines() if l.strip()]
    fails = [l for l in lines if "FAIL" in l and not re.search(r"(^|\s)0 FAIL", l)]  # 計分行 0 FAIL 不算紅
    return {"ok": proc.returncode == 0 and not fails, "rc": proc.returncode,
            "tail": (fails or lines)[-6:]}


def _undefined_names(engine: Path) -> list:
    text = engine.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [{"name": "(語法錯誤)", "line": exc.lineno or 0}]
    defined = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__spec__", "__package__"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            a = node.args
            defined |= {x.arg for x in a.args + a.kwonlyargs + a.posonlyargs}
            defined |= {x.arg for x in (a.vararg, a.kwarg) if x}
        elif isinstance(node, ast.Import):
            defined |= {(x.asname or x.name).split(".")[0] for x in node.names}
        elif isinstance(node, ast.ImportFrom):
            defined |= {(x.asname or x.name) for x in node.names}
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            defined.add(node.id)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            defined.add(node.name)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            defined |= {n.id for n in ast.walk(node.target) if isinstance(n, ast.Name)}
        elif isinstance(node, ast.comprehension):
            defined |= {n.id for n in ast.walk(node.target) if isinstance(n, ast.Name)}
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars is not None:
                    defined |= {n.id for n in ast.walk(item.optional_vars) if isinstance(n, ast.Name)}
        elif isinstance(node, ast.Global):
            defined |= set(node.names)
    out, seen = [], set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) \
                and node.id not in defined and node.id not in seen:
            seen.add(node.id)
            out.append({"name": node.id, "line": node.lineno})
    return out[:10]


def _standardize(engine: Path) -> list:
    """OPTIMIZE 段體檢; 回傳待修清單 (空=滿分)。"""
    fix = []
    text = engine.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return ["L%s 語法錯誤" % exc.lineno]
    if not ast.get_docstring(tree):
        fix.append("缺模組 docstring")
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) \
                and not node.name.startswith("_") and not ast.get_docstring(node):
            fix.append("公開 %s L%d 缺 docstring" % (node.name, node.lineno))
    holes = _undefined_names(engine)
    fix += ["未定義名 %s L%d" % (h["name"], h["line"]) for h in holes]
    return fix[:15]


def _dups(engine: Path) -> list:
    """CONSOLIDATE 段: 檔內同簽章同軀體 (去 docstring 正規化) 的重複函式組。"""
    try:
        tree = ast.parse(engine.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return [{"fp": "syntax", "names": ["(語法錯誤)"]}]
    seen: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = [n for n in node.body if not (isinstance(n, ast.Expr)
                    and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str))]
            sig = ",".join(a.arg for a in node.args.args)
            fp = hashlib.sha256((sig + "||".join(ast.dump(n) for n in body)).encode()).hexdigest()[:12]
            seen.setdefault(fp, []).append("%s L%d" % (node.name, node.lineno))
    return [{"fp": fp, "names": names} for fp, names in seen.items() if len(names) > 1][:10]


# ---------------------------------------------- 梯次推進 ---------------------
def run_stage(engine: Path, stage: str, userok: str = "", approve: bool = False) -> dict:
    kind = re.sub(r"\d+$", "", stage)
    if kind == "TEST":
        r = _run_selftest(engine)
        return {"verdict": "PASS" if r["ok"] else "FAIL",
                "evidence": ["rc %s" % r["rc"]] + r["tail"],
                "next_hint": "過 → step 進下一段" if r["ok"] else "紅 → 看 evidence 修引擎後重跑同段"}
    if kind == "DEBUG":
        r = _run_selftest(engine)
        if r["ok"]:
            return {"verdict": "PASS", "evidence": ["無待修 (selftest 綠)"], "next_hint": "step 進下一段"}
        diag = ["[診斷] selftest rc %s" % r["rc"]] + r["tail"]
        diag += ["[未定義名] %s L%d" % (h["name"], h["line"]) for h in _undefined_names(engine)]
        return {"verdict": "FAIL", "evidence": diag[:12],
                "next_hint": "把診斷丟給 AI 修 (薄尾新版), 換檔後重跑同段"}
    if kind == "OPTIMIZE":
        fix = _standardize(engine)
        return {"verdict": "PASS" if not fix else "FAIL",
                "evidence": fix or ["標準化滿分 (說明/語法/無未定義名)"],
                "next_hint": "step 進下一段" if not fix else "照清單補 docstring/修名, 重跑同段"}
    if kind == "CONSOLIDATE":
        dups = _dups(engine)
        ev = ["重複組 %s: %s" % (d["fp"], " = ".join(d["names"])) for d in dups]
        return {"verdict": "PASS" if not dups else "FAIL",
                "evidence": ev or ["無同軀體重複函式"],
                "next_hint": "step 進下一段" if not dups else "併成一份 canonical 後重跑同段"}
    if kind == "USER-TEST":
        if userok:
            return {"verdict": "PASS", "evidence": ["人工測試確認: %s" % userok[:80]],
                    "next_hint": "step 進下一段"}
        return {"verdict": "WAIT",
                "evidence": ["請在你的環境實跑此引擎 (正常流程+一個故意錯的輸入)",
                             "確認後: step --userok \"你的結論一句話\""],
                "next_hint": "等人工確認"}
    if kind == "ACTIVATE":
        if approve:
            sha = hashlib.sha256(engine.read_bytes()).hexdigest()[:16]
            return {"verdict": "PASS",
                    "evidence": ["已記啟用 sha256=%s" % sha, "置換上位仍走 promote 促轉 (白名單+回滾)"],
                    "next_hint": "step 進收尾 TEST", "sha": sha}
        return {"verdict": "WAIT",
                "evidence": ["啟用需明示核可: step --approve", "啟用只記帳, 不自動部署"],
                "next_hint": "等核可"}
    return {"verdict": "FAIL", "evidence": ["未知段 %s" % stage], "next_hint": "reset"}


def step(engine: Path, userok: str = "", approve: bool = False) -> dict:
    st = _load(engine)
    if st["cursor"] >= len(SEQ):
        return {"stage": "DONE", "verdict": "DONE", "cursor": st["cursor"],
                "evidence": ["梯次 13/13 全過 — 引擎完訓"], "next_hint": "reset 可重走"}
    stage = SEQ[st["cursor"]]
    out = run_stage(engine, stage, userok, approve)
    row = {"ts": dt.datetime.now().isoformat(), "stage": stage, **out}
    st["stages"][stage] = out["verdict"]
    st["history"].append(row)
    if out["verdict"] == "PASS":
        st["cursor"] += 1
    _save(engine, st)
    return {"stage": stage, "cursor": st["cursor"], "total": len(SEQ), **out}


def status(engine: Path) -> dict:
    st = _load(engine)
    return {"engine": st["engine"], "cursor": st["cursor"], "total": len(SEQ),
            "ladder": [{"stage": s, "state": st["stages"].get(s, "灰(沒跑)")} for s in SEQ]}


# ---------------------------------------------- selftest ---------------------
def selftest() -> tuple:
    """自測: 用臨時好/壞引擎走關鍵段。"""
    import tempfile
    p = f = 0

    def ck(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [PASS] ladder: %s" % name)
        else:
            f += 1
            print("  [FAIL] ladder: %s" % name)

    box = Path(tempfile.mkdtemp())
    os.environ["VIA_ROOT"] = str(box)
    good = box / "good_engine.py"
    good.write_text('"""好引擎。"""\nimport sys\n\n\ndef run(x):\n    """跑。"""\n    return x\n\n\n'
                    'if __name__ == "__main__":\n    print("[計] 1 PASS / 0 FAIL")\n    sys.exit(0)\n',
                    encoding="utf-8")
    bad = box / "bad_engine.py"
    bad.write_text('"""壞引擎。"""\nimport sys\n\n\ndef run(x):\n    """跑。"""\n    return ghost\n\n\n'
                   'if __name__ == "__main__":\n    print("FAIL boom")\n    sys.exit(1)\n',
                   encoding="utf-8")
    r = step(good)
    ck("TEST1 pass on good", r["stage"] == "TEST1" and r["verdict"] == "PASS")
    r = step(good)
    ck("DEBUG1 auto-pass", r["stage"] == "DEBUG1" and r["verdict"] == "PASS")
    r = step(good)
    ck("OPTIMIZE pass (docstrings ok)", r["stage"] == "OPTIMIZE" and r["verdict"] == "PASS", )
    for _ in range(3):
        r = step(good)  # TEST2 DEBUG2 CONSOLIDATE
    ck("reach TEST3 after consolidate", r["stage"] == "CONSOLIDATE" and r["verdict"] == "PASS")
    for _ in range(2):
        r = step(good)  # TEST3 DEBUG3
    r = step(good)
    ck("USER-TEST waits", r["stage"] == "USER-TEST" and r["verdict"] == "WAIT")
    r = step(good)
    ck("USER-TEST blocks until userok (不跳段)", r["stage"] == "USER-TEST")
    r = step(good, userok="本機實測 OK")
    ck("USER-TEST passes with userok", r["verdict"] == "PASS")
    r = step(good)   # DEBUG4
    r = step(good)
    ck("ACTIVATE waits for approve", r["stage"] == "ACTIVATE" and r["verdict"] == "WAIT")
    r = step(good, approve=True)
    ck("ACTIVATE passes with approve", r["verdict"] == "PASS" and "sha" in r)
    r = step(good)
    r = step(good)
    ck("ladder DONE 13/13", step(good)["stage"] == "DONE")
    # 壞引擎: TEST1 擋住, 不放行
    r = step(bad)
    ck("TEST1 fail on bad", r["stage"] == "TEST1" and r["verdict"] == "FAIL")
    r = step(bad)
    ck("stuck at TEST1 (一步不過不放行)", r["stage"] == "TEST1")
    s = status(bad)
    ck("status shows grey stages", s["cursor"] == 0 and s["ladder"][2]["state"] == "灰(沒跑)")
    print("[計] %d PASS / %d FAIL" % (p, f))
    return p, f


def main() -> None:
    argv = sys.argv[1:]
    if argv and argv[0] == "--selftest":
        _, fails = selftest()
        sys.exit(0 if fails == 0 else 1)
    if len(argv) < 2 or argv[1] not in ("step", "status", "reset"):
        print(__doc__)
        sys.exit(2)
    engine = Path(argv[0]).resolve()
    if not engine.is_file():
        print("[錯] 引擎不存在: %s" % engine)
        sys.exit(2)
    cmd = argv[1]
    userok = ""
    approve = "--approve" in argv
    if "--userok" in argv:
        i = argv.index("--userok")
        userok = argv[i + 1] if i + 1 < len(argv) else "OK"
    if cmd == "reset":
        _state_path(engine).unlink(missing_ok=True)
        print("[梯次] 歸零: %s" % engine.name)
        return
    if cmd == "status":
        s = status(engine)
        print("[梯次] %s · %d/%d" % (engine.name, s["cursor"], s["total"]))
        for row in s["ladder"]:
            print("  %-11s %s" % (row["stage"], row["state"]))
        return
    out = step(engine, userok, approve)
    print("[段] %s · %s · %d/%d" % (out["stage"], out["verdict"], out["cursor"], out["total"]))
    for line in out["evidence"]:
        print("  " + str(line))
    print("NEXT: " + out["next_hint"])
    sys.exit(0 if out["verdict"] in ("PASS", "DONE") else 3 if out["verdict"] == "WAIT" else 1)


if __name__ == "__main__":
    main()
