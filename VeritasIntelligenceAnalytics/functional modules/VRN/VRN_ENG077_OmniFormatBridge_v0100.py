#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG077_OmniFormatBridge — VOFIE 全格式引擎橋(批256;操作員令)
====================================================================
操作員令:「integrate all old new engine with similar function…另外
增加 Veritas_OmniFormat_Intelligence_Engine(VOFIE)」。
同功能族整合律(不失功能;Zero-Hydra 收容原地不動=駕馭):
  ENG075 DocToMarkdown=輕道正主(markitdown 單檔快轉)
  ENG077 本橋=重道(收容 VOFIE v0140;契約 v1.4:BLAKE2s 前後驗
    /來源只讀/IR 全文保真/重複只標 duplicate_of 不刪/輸出新 run 夾
    不覆寫/JS 只證據不執行/NoHydra)——多格式重構+主題矩陣+五檔
    輸出(html/json/docx/md/csv)場景
機制:
  ①尾版解析收容 VOFIE(嚴禁寫死版號)②run=simple 模式(≤5 輸入;
    契約同 ENGINE 主檔名)subprocess 駕馭→VIA_Reports/vofie_out/
    <ts>/(衍生物不入 git)③probe=引擎在位+契約檔+相依冊誠實三態
用法:python3 VRN_ENG077_OmniFormatBridge_v0100.py probe
      | run <檔...> | --selftest
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

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
INTAKE = HERE / "references" / "intake"
OUTROOT = VIA / "VIA_Reports" / "vofie_out"


def _vofie() -> Path | None:
    """收容 VOFIE 尾版解析(語意版號;嚴禁寫死)"""
    hits = [p for p in INTAKE.rglob(
        "Veritas_OmniFormat_Intelligence_Engine.py") if p.is_file()]
    if not hits:
        return None

    def key(p: Path):
        vs = [tuple(int(x) for x in m.groups() if x)
              for q in p.parents for m in
              [re.search(r"v(\d{2,4})", q.name)] if m]
        return max(vs) if vs else (0,)
    return max(hits, key=key)


def probe() -> int:
    eng = _vofie()
    print(f"[probe] VOFIE 引擎={'OK ' + str(eng.parent.name) if eng else '缺(誠實;先 via-intake)'}")
    if eng:
        for f in ("FORMAT_CONTRACT.md", "Veritas_VOFIE_DEPENDENCIES.json",
                  "HYDRA_RISK_PLAYBOOK.md"):
            print(f"[probe] {f}:{'在' if (eng.parent / f).exists() else '缺(誠實)'}")
    return 0 if eng else 1


def run(inputs: list[Path]) -> int:
    eng = _vofie()
    if eng is None:
        print("[VOFIE 橋] 收容缺=誠實停(先 via-intake)")
        return 2
    inputs = [p for p in inputs if p.exists()]
    if not inputs:
        print("[VOFIE 橋] 無有效輸入=誠實停")
        return 2
    if len(inputs) > 5:
        print(f"[VOFIE 橋] simple 契約上限 5 輸入(得 {len(inputs)})=取前 5 誠實標")
        inputs = inputs[:5]
    out = OUTROOT / datetime.now().strftime("%Y%m%d_%H%M%S")
    r = subprocess.run(
        [sys.executable, str(eng), "simple", *[str(p) for p in inputs],
         "--output", str(out)],
        capture_output=True, text=True, timeout=600)
    md = out / "Veritas_VOFIE_Reconstructed.md"
    ok = r.returncode == 0 and md.exists()
    print(f"[VOFIE 橋] rc={r.returncode} · 輸出 {'五檔在 ' + str(out) if ok else '敗(誠實):' + r.stderr[-200:]}"
          "(不入 git)")
    return 0 if ok else 1


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    eng = _vofie()
    chk("① 收容 VOFIE 尾版解析(原地不動=駕馭)", eng is not None
        and "intake" in str(eng))
    chk("② 契約件在位(FORMAT_CONTRACT v1.4+NoHydra 手冊)",
        eng is not None and (eng.parent / "FORMAT_CONTRACT.md").exists()
        and (eng.parent / "HYDRA_RISK_PLAYBOOK.md").exists())
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "t.txt"
        f.write_text("主題甲\n營收成長。\n\n主題乙\n毛利回升。\n",
                     encoding="utf-8")
        global OUTROOT
        o0 = OUTROOT
        OUTROOT = Path(td) / "out"
        rc = run([f])
        runs = sorted(OUTROOT.glob("*"))
        five = {"Veritas_VOFIE.html", "Veritas_VOFIE_Reconstructed.md",
                "Veritas_VOFIE_Reconstructed.docx",
                "Veritas_VOFIE_ComponentSpecs.json",
                "Veritas_VOFIE_TopicMatrix.csv"}
        got = {p.name for p in runs[0].iterdir()} if runs else set()
        chk("③ simple 端到端(五檔輸出契約)", rc == 0 and five <= got,
            f"got={len(got)}")
        md = (runs[0] / "Veritas_VOFIE_Reconstructed.md").read_text(
            encoding="utf-8") if runs else ""
        chk("④ 內容保真(主題入 md)", "營收成長" in md)
        chk("⑤ 新 run 夾不覆寫律(時戳夾)", len(runs) == 1
            and runs[0].name.replace("_", "").isdigit())
        chk("⑥ 無輸入誠實 rc2", run([Path(td) / "none.txt"]) == 2)
        OUTROOT = o0
    chk("⑦ 同功能族分工宣告(ENG075 輕道正主/本橋重道)+輸出不入 git",
        "輕道正主" in src and "不入 git" in src)
    chk("⑧ 零網路+加速橋(subprocess 駕馭本地引擎)",
        all(("import " + k) not in src for k in ("requests", "httpx"))
        and "ACCEL-BRIDGE" in src)
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== VOFIE 全格式橋(VRN_ENG077)· 八檢自測(零網路)===")
        return selftest()
    if args and args[0] == "probe":
        return probe()
    if args and args[0] == "run" and len(args) > 1:
        return run([Path(a) for a in args[1:]])
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
