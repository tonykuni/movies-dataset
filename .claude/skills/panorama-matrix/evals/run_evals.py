#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""panorama-matrix evals:E1–E5 · E7 實跑(E6 觸發案例只列在 cases.json)。零網路;輸出全在暫存夾;結束碼 0 = 全過。"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EV = Path(__file__).resolve().parent
SKILL = EV.parent
SHIM = SKILL / "scripts" / "panorama_matrix.py"
sys.path.insert(0, str(SHIM.parent))
import panorama_matrix as shim  # noqa: E402

ok: list = []


def chk(name: str, cond: bool, note: str = "") -> None:
    ok.append(bool(cond))
    print(f"  {'✓' if cond else '✗'} {name}" + (f" · {note}" if note and not cond else ""))


def run(target: Path, out: Path, *args: str) -> tuple:
    p = subprocess.run([sys.executable, str(SHIM), str(target), "--out", str(out), *args], capture_output=True, text=True)
    rep = json.loads((out / "panorama_latest.json").read_text(encoding="utf-8")) if (out / "panorama_latest.json").is_file() else {}
    return p.returncode, rep, p.stdout


def mtimes(root: Path) -> dict:
    return {p: p.stat().st_mtime_ns for p in root.rglob("*")}


def main() -> int:
    eng = shim.find_engine()
    print(f"[panorama-matrix evals] 引擎 {eng}")
    if eng is None:
        print("  引擎 ABSENT")
        return 3
    tmp = Path(tempfile.mkdtemp(prefix="pm_evals_"))
    try:
        # E1 乾淨倉(直接掃已提交的 fixture:R1 以 mtime 為證)
        clean = EV / "fixtures" / "clean"
        before = mtimes(clean)
        rc1, _, card = run(clean, tmp / "e1", "--profile", "via-verb-engine", "--no-git")
        rc2, rep, _ = run(clean, tmp / "e1", "--profile", "via-verb-engine", "--no-git")
        D = {r["key"]: r["lamp"] for r in rep["sections"]["D"]["rows"]}
        chk("E1 首輪 rc 2(棘輪 NODATA)· 次輪 rc 0 GREEN", rc1 == 2 and rc2 == 0 and rep["verdict"] == "GREEN", f"{rc1}/{rc2}/{rep.get('verdict')}")
        chk("E1 20 檔 · 3 家族", rep["sections"]["A"]["summary"]["files"] == 20 and rep["sections"]["A"]["summary"]["families"] == 3)
        chk("E1 隔離項全 HOLD · Q1–Q4 GREEN", all(v == "HOLD" for k, v in D.items() if k.startswith("隔離 "))
            and all(v == "GREEN" for k, v in D.items() if k[:2] in ("Q1", "Q2", "Q3", "Q4")), json.dumps(D, ensure_ascii=False))
        chk("E1 R1 目標夾 mtime 一個都沒變", before == mtimes(clean))
        chk("E7 卡 ≤ 15 行", len(card.strip().splitlines()) <= 15, str(len(card.strip().splitlines())))

        # E3 隔離區壞
        rc, rep, _ = run(EV / "fixtures" / "quarantine-bad", tmp / "e3", "--profile", "via-verb-engine", "--no-git")
        lam = {r["key"][:2]: r["lamp"] for r in rep["sections"]["D"]["rows"]}
        greens = [r["key"] for s in rep["sections"].values() for r in s.get("rows", []) if r.get("lamp") == "GREEN"
                  and any(n in str(r.get("key")) for n in ("e1", "e2", "e3", "e4")) and str(r.get("key")).startswith("隔離")]
        chk("E3 Q1 RED · Q3 RED · rc 1 · 隔離項沒畫綠", rc == 1 and lam.get("Q1") == "RED" and lam.get("Q3") == "RED" and not greens,
            f"rc {rc} · {lam}")

        # E4 棘輪:語法錯 2 → 4(暫存夾生成,不把壞 .py 提交進倉)
        rat = tmp / "ratchet"
        rat.mkdir()
        for i in range(2):
            (rat / f"bad{i}.py").write_text("def f(:\n    x = 1\n", encoding="utf-8")
        run(rat, tmp / "e4", "--profile", "generic", "--no-git", "--static")
        for i in range(2, 4):
            (rat / f"bad{i}.py").write_text("def f(:\n    x = 1\n", encoding="utf-8")
        rc, rep, _ = run(rat, tmp / "e4", "--profile", "generic", "--no-git", "--static")
        led = [x for x in (tmp / "e4" / "universal_ledger.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        chk("E4 RETROGRESS · rc 1 · 帳本 2 行", rc == 1 and rep["sections"]["G"]["summary"]["verdict"] == "RETROGRESS" and len(led) == 2,
            f"rc {rc} · {rep['sections']['G']['summary']}")

        # E5 沒有 rich:在子行程把 rich 設成匯入失敗再跑引擎
        code = ("import sys,runpy;sys.modules['rich']=None;sys.argv=[sys.argv[1],*sys.argv[2:]];"
                "runpy.run_path(sys.argv[0],run_name='__main__')")
        p = subprocess.run([sys.executable, "-c", code, str(eng), str(clean), "--out", str(tmp / "e5"), "--profile",
                            str(SKILL / "profiles" / "via-verb-engine.json"), "--no-git", "--rich"], capture_output=True, text=True)
        chk("E5 沒有 rich:html · txt · json · 帳本都在 · 沒報錯", p.returncode == 2 and all((tmp / "e5" / n).is_file() for n in
            ("panorama_latest.html", "panorama_latest.txt", "panorama_latest.json", "universal_ledger.jsonl")), p.stderr[-200:])

        # E2 漂移:領先 2 · 落後 3;reflog 為證不 merge/checkout/stash
        if shutil.which("git"):
            env = {**os.environ, "GIT_AUTHOR_NAME": "e", "GIT_AUTHOR_EMAIL": "e@e", "GIT_COMMITTER_NAME": "e", "GIT_COMMITTER_EMAIL": "e@e"}

            def g(cwd, *a):
                return subprocess.run(["git", *a], cwd=str(cwd), capture_output=True, text=True, env=env)
            bare, loc, oth = tmp / "remote.git", tmp / "drift", tmp / "other"
            bare.mkdir()
            g(bare, "init", "-q", "--bare", "-b", "main")
            loc.mkdir()
            g(loc, "init", "-q", "-b", "main")
            (loc / "x_v0100.py").write_text('"""x"""\n', encoding="utf-8")
            g(loc, "add", ".")
            g(loc, "commit", "-q", "-m", "base")
            g(loc, "remote", "add", "origin", str(bare))
            g(loc, "push", "-q", "origin", "main")
            g(tmp, "clone", "-q", str(bare), str(oth))
            for i in range(3):
                (oth / f"r{i}.md").write_text(f"{i}\n", encoding="utf-8")
                if i == 2:
                    (oth / "x_v0101.py").write_text('"""x2"""\n', encoding="utf-8")
                g(oth, "add", ".")
                g(oth, "commit", "-q", "-m", f"r{i}")
            g(oth, "push", "-q", "origin", "main")
            for i in range(2):
                (loc / f"l{i}.md").write_text(f"{i}\n", encoding="utf-8")
                g(loc, "add", ".")
                g(loc, "commit", "-q", "-m", f"l{i}")
            g(loc, "fetch", "-q", "origin")
            ref = g(loc, "reflog").stdout
            rc, rep, _ = run(loc, tmp / "e2", "--profile", "generic")
            es = rep["sections"]["E"]["summary"]
            chk("E2 領先 2 · 落後 3 · 尾版不同 1 · reflog 沒變 · rc 2", es.get("ahead") == 2 and es.get("behind") == 3
                and es.get("tail_diff") == 1 and g(loc, "reflog").stdout == ref and rc == 2, f"{es} rc {rc}")
        else:
            chk("E2 git 缺席(跳過,不假綠)", True)

        # E7 設定一致:技能 profiles/*.json 與引擎旁的設定冊逐鍵相同
        side = json.loads((eng.parent / "VIA_Panorama_Profiles_v0100.json").read_text(encoding="utf-8"))["profiles"]
        mine = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (SKILL / "profiles").glob("*.json")}
        chk("E7 技能 profiles == 引擎設定冊(不漂)", mine == side, f"{sorted(mine)} vs {sorted(side)}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"  panorama-matrix evals {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
