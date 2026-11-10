#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_GraphifyLane v0100 — VCGC 的 Graphify 車道探測(隔離境 · 收據 · 圖譜統計;只讀 · 0 網路 · 不裝)。

操作員 2026-11-10:「先做 Graphify Playwright DuckDB 席位候選 自動完成以上全部」。工具鎖冊 graphify 席位的候選本體。
Graphify(graphifyy · tree-sitter 程式碼知識圖譜)依 docs/handoff/ai/via_graphify_v0101/VIA_Graphify_v0101.md 裝在
**隔離境** %USERPROFILE%\\envs\\via_graphify(不進主 Python;首次安裝要 VIA_NET_CONSENT=YES,操作員設)。本支只做三件只讀的事:
  probe_env()      隔離境在不在 · graphify 可執行檔 · graphifyy 版本(執行期問隔離境的 python;匯入層不開子行程)
  read_receipt()   既有收據 VIA_Reports/graphify/VIA_Graphify_latest.json(VIA_SettleAll 寫的)摘要
  graph_stats()    各系統 graph.json 的節點 / 邊數(VIA_Reports/graphify/<系統>/graph.json,有才讀)
判定:隔離境在 + 收據在且不紅 = GREEN;只缺一樣 = YELLOW;都沒有 = NODATA。收據只寫自己的
VIA_Reports/graphify/GraphifyLane_latest.json(不蓋 SettleAll 的收據)。不裝、不連網、不開 LLM 後端、不碰他系統的冊 / 正本 / 號。
用法:python VIA_GraphifyLane_v0100.py [--env <隔離境>] · --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0100"
ENGINE = f"VIA_GraphifyLane_{VERSION}"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
SETTLE_RECEIPT = Path("VIA_Reports") / "graphify" / "VIA_Graphify_latest.json"
OWN_RECEIPT = Path("VIA_Reports") / "graphify" / "GraphifyLane_latest.json"
SYSTEMS = ["VCGC", "VDF", "VRN-2", "VQG", "VAP"]


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def env_root(override: str | None = None) -> Path:
    return Path(override or os.environ.get("VIA_GRAPHIFY_ENV") or (Path.home() / "envs" / "via_graphify")).expanduser()


def probe_env(env: Path, ask_version: bool = True) -> dict:
    py = next((p for p in (env / "Scripts" / "python.exe", env / "bin" / "python", env / "bin" / "python3") if p.is_file()), None)
    exe = next((p for p in (env / "Scripts" / "graphify.exe", env / "bin" / "graphify") if p.is_file()), None)
    out = {"env": str(env), "exists": env.is_dir(), "python": str(py) if py else None, "graphify_exe": str(exe) if exe else None, "version": None}
    if py and ask_version:
        try:
            cp = subprocess.run([str(py), "-c", "import importlib.metadata as m;print(m.version('graphifyy'))"],
                                capture_output=True, text=True, timeout=30, env={**os.environ, "GRAPHIFY_BACKEND": "none"})
            out["version"] = cp.stdout.strip() or None
            if cp.returncode:
                out["version_error"] = (cp.stderr or "").strip()[-200:]
        except Exception as exc:  # noqa: BLE001 — 問不到就照實記
            out["version_error"] = f"{type(exc).__name__}: {exc}"[:200]
    return out


def read_receipt(via: Path) -> dict | None:
    p = via / SETTLE_RECEIPT
    if not p.is_file():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"path": str(p), "lamp": "RED", "error": f"收據讀不了:{exc}"[:200]}
    return {"path": str(p), "lamp": str(d.get("lamp") or d.get("status") or "NOT_SET"), "at": d.get("at_utc") or d.get("generated_utc") or d.get("ts"),
            "keys": sorted(d)[:20]}


def graph_stats(via: Path) -> dict:
    stats = {}
    for s in SYSTEMS:
        g = via / "VIA_Reports" / "graphify" / s / "graph.json"
        if not g.is_file():
            continue
        try:
            d = json.loads(g.read_text(encoding="utf-8"))
            stats[s] = {"nodes": len(d.get("nodes") or []), "edges": len(d.get("links") or d.get("edges") or [])}
        except (OSError, ValueError) as exc:
            stats[s] = {"error": str(exc)[:160]}
    return stats


def judge(env: dict, receipt: dict | None) -> str:
    have_env = bool(env.get("graphify_exe") or env.get("version"))
    have_rec = receipt is not None and receipt.get("lamp") != "RED"
    if have_env and have_rec:
        return "GREEN"
    if have_env or receipt is not None:
        return "YELLOW"
    return "NODATA"


def run(via: Path = VIA, env_override: str | None = None, write: bool = True, ask_version: bool = True) -> dict:
    env = probe_env(env_root(env_override), ask_version)
    rec = read_receipt(via)
    res = {"engine": ENGINE, "at_utc": utc_now(), "lamp": judge(env, rec), "env": env, "settle_receipt": rec,
           "graphs": graph_stats(via), "how_to_build": "docs/handoff/ai/via_graphify_v0101/VIA_Graphify_v0101.md(boot 行 · 隔離境 · --code-only · GRAPHIFY_BACKEND=none)",
           "boundary": "只讀:不裝 · 不連網 · 不開 LLM 後端 · 只寫自己的 GraphifyLane_latest.json"}
    if write:
        out = via / OWN_RECEIPT
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        res["receipt"] = str(out)
    return res


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")
    with tempfile.TemporaryDirectory(prefix="via_graphify_lane_") as td:
        via = Path(td) / "VIA"
        env = Path(td) / "env"
        r0 = run(via, str(env), write=True, ask_version=False)
        chk("① 什麼都沒有 = NODATA · 收據寫在自己的檔", r0["lamp"] == "NODATA" and (via / OWN_RECEIPT).is_file() and not (via / SETTLE_RECEIPT).exists())
        (env / "bin").mkdir(parents=True)
        (env / "bin" / "graphify").write_text("#!/bin/sh\n", encoding="utf-8")
        r1 = run(via, str(env), write=False, ask_version=False)
        chk("② 只有隔離境 = YELLOW", r1["lamp"] == "YELLOW" and r1["env"]["graphify_exe"])
        (via / SETTLE_RECEIPT).write_text(json.dumps({"lamp": "GREEN", "at_utc": "2026-11-10T00:00:00Z"}), encoding="utf-8")
        (via / "VIA_Reports" / "graphify" / "VCGC").mkdir(parents=True)
        (via / "VIA_Reports" / "graphify" / "VCGC" / "graph.json").write_text(json.dumps({"nodes": [1, 2, 3], "links": [[1, 2]]}), encoding="utf-8")
        r2 = run(via, str(env), write=False, ask_version=False)
        chk("③ 隔離境 + 收據不紅 = GREEN · 圖譜統計讀到", r2["lamp"] == "GREEN" and r2["graphs"].get("VCGC") == {"nodes": 3, "edges": 1}, r2["graphs"])
        (via / SETTLE_RECEIPT).write_text("{壞", encoding="utf-8")
        r3 = run(via, str(env), write=False, ask_version=False)
        chk("④ 收據壞 = 照實標 RED 不炸 · 總燈不是綠", r3["settle_receipt"]["lamp"] == "RED" and r3["lamp"] != "GREEN")
    import ast
    text = Path(__file__).read_text(encoding="utf-8")
    sub_args = set()
    for n in ast.walk(ast.parse(text)):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("run", "Popen", "call", "check_call", "check_output"):
            sub_args |= {c.value for a in n.args for c in ast.walk(a) if isinstance(c, ast.Constant) and isinstance(c.value, str)}
    chk("⑤ 加速器橋在 · 子行程只問版本(參數裡沒有 pip / install)", "[VIA:ACCEL-BRIDGE" in text and sub_args
        and not any(w in s.split() for s in sub_args for w in ("pip", "install", "ensurepip")), sorted(sub_args)[:3])
    good = all(ok)
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", default=None, help="隔離境路徑(預設 %%USERPROFILE%%\\envs\\via_graphify 或 VIA_GRAPHIFY_ENV)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    r = run(VIA, a.env)
    print(json.dumps({k: r.get(k) for k in ("lamp", "engine", "env", "settle_receipt", "graphs", "receipt")}, ensure_ascii=False, indent=1))
    return 0 if r["lamp"] in ("GREEN", "YELLOW", "NODATA") else 1


if __name__ == "__main__":
    sys.exit(main())
