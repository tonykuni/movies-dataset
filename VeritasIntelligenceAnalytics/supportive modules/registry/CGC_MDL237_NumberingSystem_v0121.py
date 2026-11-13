#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0121 — 薄尾:檔名規則閘(P2 · 不合格不給號)

操作員令(2026-11-10 / 11):「檔名依規定並註記版本號 · 自動編號註冊衝突重複檢測 · 編號功能今天算才嚴格啟用」→
規劃 VIA_RegistryUpgrade_Plan_20261110 P2;操作員「繼續做 P2 檔名規則閘」。

閘只看「這批要發號、而且還沒登過號的程式檔」(.py / .ps1);已登過號的檔、非程式檔(冊 · 文件 · 證據)照前版,一字不擋
(嚴格啟用日 2026-11-10 起的新檔才管;舊檔不回溯)。
  N1 檔名 = <族>_v<NNNN>.<py|ps1>(族:英數 · 底線 · 連字號 · 點;版號恰 4 位數)→ 不合 = FAIL
  N2 不撞同族:同一檔名(族 + 版號)已在樹上另一處(參考 / 收件 / 報表 / 退役夾除外)→ FAIL(同號兩份,誰是正本說不清)
  N3 版號只增:同夾同族已有更大的版號 → HOLD(補環要人明說:--allow-gap <檔>)
FAIL / HOLD 的檔從本批拿掉(不給號);其餘照 v0120 發號 + 收據。本批全被擋 → rc 2,一列不寫。
每個判定寫一列到只增帳 registry/VIA_RegistrationGate_v0100.jsonl(at 到分鐘 · operator · file · verdict · rules · engine)= 自動註冊 LOG。
`gate <檔…>`:只判不寫(試算)。
只收 VCGC 呼叫(經 via-vcgc run);零網路;不碰 TA-Lib;只讀子系統的檔。
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
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
VERSION = "v0121"
_STEM = "CGC_MDL237_NumberingSystem"
GATE_LOG = HERE / "VIA_RegistrationGate_v0100.jsonl"
CODE_EXT = (".py", ".ps1")
NAME_RX = re.compile(r"^(?P<fam>[A-Za-z0-9][A-Za-z0-9_.\-]*?)_v(?P<ver>\d{4})\.(?P<ext>py|ps1)$")
SKIP_PARTS = ("references", "intake", "VIA_Reports", "VIA_RetiredEngines", "_superseded_redundant", "__pycache__", ".git",
              "node_modules", "retired", "evidence")


def _vnum_v0121(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load_v0121(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0121(p) < _vnum_v0121(__file__)), key=_vnum_v0121)
PRIOR = _load_v0121(PRIOR_PATH, _STEM + "_prior_for_" + ENGINE)       # v0120(收據)
VIA_ROOT = PRIOR.VIA_ROOT


def __getattr__(name):
    return getattr(PRIOR, name)


# ---------- 閘核心(純函式,自測可注入)----------
def tree_files(root: Path | None = None) -> list:
    """VIA 樹的程式檔(相對路徑);先問 git(快),不行再走檔案系統。參考 / 收件 / 報表 / 退役夾不算。"""
    root = root or VIA_ROOT
    try:
        out = subprocess.run(["git", "ls-files", "-z", "--", "*.py", "*.ps1"], cwd=str(root), capture_output=True, timeout=120)
        names = [n for n in out.stdout.decode("utf-8", "replace").split("\0") if n] if out.returncode == 0 else None
    except Exception:
        names = None
    if names is None:
        names = [str(p.relative_to(root)).replace(os.sep, "/") for p in root.rglob("*") if p.suffix in CODE_EXT and p.is_file()]
    return [n for n in names if not any(part in SKIP_PARTS for part in Path(n).parts[:-1])]


def registered_sources(rows: dict | None = None) -> set:
    rows = PRIOR.book_rows() if rows is None else rows
    return {str(r.get("source")) for r in rows.values() if r.get("source")}


def judge(path: str, tree: list, registered: set, allow_gap: set | None = None, root: Path | None = None) -> dict:
    """一個檔 → {file, verdict PASS / FAIL / HOLD / SKIP, rules[]}。"""
    p = str(path).replace(os.sep, "/")
    name = Path(p).name
    if Path(p).suffix.lower() not in CODE_EXT:
        return {"file": p, "verdict": "SKIP", "rules": [], "why": "非程式檔(冊 · 文件 · 證據)照前版"}
    if p in registered:
        return {"file": p, "verdict": "SKIP", "rules": [], "why": "已登過號(舊檔不回溯)"}
    m = NAME_RX.match(name)
    if not m:
        return {"file": p, "verdict": "FAIL", "rules": ["N1"], "why": "檔名不合 <族>_v<NNNN>.<py|ps1>"}
    fam, ver = m.group("fam"), int(m.group("ver"))
    rules, why = [], []
    twins = [t for t in tree if Path(t).name == name and t != p]
    if twins:
        rules.append("N2")
        why.append("同族同版已在別處:" + " · ".join(twins[:3]))
    folder = str(Path(p).parent).replace(os.sep, "/")
    sib = [t for t in tree if str(Path(t).parent).replace(os.sep, "/") == folder and t != p]
    higher = sorted({int(mm.group("ver")) for t in sib for mm in [NAME_RX.match(Path(t).name)]
                     if mm and mm.group("fam") == fam and mm.group("ext") == m.group("ext") and int(mm.group("ver")) > ver})
    if higher and p not in (allow_gap or set()):
        rules.append("N3")
        why.append(f"同夾同族已有更大版號 v{higher[-1]:04d}(補環要 --allow-gap)")
    verdict = "FAIL" if "N2" in rules else ("HOLD" if rules else "PASS")
    return {"file": p, "verdict": verdict, "rules": rules, "why": " ; ".join(why), "family": fam, "version": f"v{ver:04d}"}


def gate(files: list, operator: str = "AI", allow_gap: set | None = None, tree: list | None = None,
         registered: set | None = None, log: Path | None = None, write: bool = True) -> list:
    tree = tree_files() if tree is None else tree
    registered = registered_sources() if registered is None else registered
    res = [judge(f, tree, registered, allow_gap) for f in files]
    if write:
        at = PRIOR.minute()
        with (log or GATE_LOG).open("a", encoding="utf-8", newline="\n") as fh:
            for r in res:
                if r["verdict"] != "SKIP":
                    fh.write(json.dumps({"at": at, "operator": operator, **{k: r[k] for k in ("file", "verdict", "rules", "why")},
                                         "engine": f"{_STEM} {VERSION}"}, ensure_ascii=False) + "\n")
    return res


def _print(res: list) -> None:
    for r in res:
        if r["verdict"] != "SKIP":
            print(f"  [{r['verdict']}] {r['file']}" + (f" · {','.join(r['rules'])} · {r['why']}" if r["rules"] else ""))
    c = {v: sum(1 for r in res if r["verdict"] == v) for v in ("PASS", "FAIL", "HOLD", "SKIP")}
    print(f"[檔名閘 · {VERSION}] 過 {c['PASS']} · 擋 {c['FAIL']} · 待人 {c['HOLD']} · 不管(非程式檔 / 已登號){c['SKIP']}")


def _take(args: list, flag: str) -> tuple[list, list]:
    """取出 flag 後面的檔(到下一個 -- 旗標為止),回 (檔, 剩下的 args)。"""
    if flag not in args:
        return [], args
    i = args.index(flag)
    j = i + 1
    while j < len(args) and not args[j].startswith("--"):
        j += 1
    return args[i + 1:j], args[:i] + args[j:]


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["--selftest"]:
        return selftest(deep="--deep" in args)
    operator, args = PRIOR._operator(args)
    gaps, args = _take(args, "--allow-gap")
    if args[:1] == ["gate"]:
        res = gate(args[1:], operator, set(gaps), write=False)
        _print(res)
        return 0 if all(r["verdict"] in ("PASS", "SKIP") for r in res) else 1
    if "--apply" in args and "--scope" in args:
        i = args.index("--scope")
        ref = args[args.index("--base") + 1] if "--base" in args and args.index("--base") + 1 < len(args) else None
        listed = [a for a in args[i + 1:] if not a.startswith("--") and a != ref]
        if listed:
            res = gate(listed, operator, set(gaps))
            _print(res)
            keep = [r["file"] for r in res if r["verdict"] in ("PASS", "SKIP")]
            if not keep:
                print(f"[檔名閘 · {VERSION}] 本批全被擋:一列不寫(rc 2)· 帳 {GATE_LOG.name}")
                return 2
            rest = [a for a in args[:i + 1]] + keep + [a for a in args[i + 1:] if a.startswith("--") or a == ref]
            args = (["--operator", operator] if operator != "AI" else []) + rest
            return PRIOR.main(args)
    return PRIOR.main((["--operator", operator] if operator != "AI" else []) + args)


# ---------- 自測(注入樹 · 暫存帳 · 不碰真冊)----------
def selftest(deep: bool = False) -> int:
    import tempfile
    checks = []

    def chk(name, cond, note=""):
        checks.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note else ""))

    print(f"=== {_STEM} {VERSION} · 薄尾自測(檔名規則閘 · 注入樹 · 暫存帳 · 零外呼)===")
    tree = ["functional modules/X/X_ENG001_Demo_v0100.py", "functional modules/X/X_ENG001_Demo_v0101.py",
            "functional modules/X/X_ENG001_Demo_v0103.py", "functional modules/Y/Y_MDL002_Tool_v0100.py",
            "functional modules/Z/Y_MDL002_Tool_v0100.py"]
    reg = {"functional modules/X/X_ENG001_Demo_v0100.py"}
    j = lambda f, gap=None: judge(f, tree + [f], reg, gap)
    chk("N1 合格名 → PASS", j("functional modules/X/X_ENG001_Demo_v0104.py")["verdict"] == "PASS")
    chk("N1 沒版號 / 三位數版號 / 大寫副檔名 → FAIL",
        all(j(f)["verdict"] == "FAIL" and j(f)["rules"] == ["N1"] for f in
            ("functional modules/X/X_ENG001_Demo.py", "functional modules/X/X_ENG001_Demo_v104.py", "functional modules/X/X_ENG001_Demo_v0104.PY")),
        [j(f)["verdict"] for f in ("functional modules/X/X_ENG001_Demo.py",)])
    n2 = judge("functional modules/Y/Y_MDL002_Tool_v0100.py", tree, set())
    chk("N2 同族同版在別處 → FAIL(撞號)", n2["verdict"] == "FAIL" and "N2" in n2["rules"], n2["why"][:60])
    n3 = j("functional modules/X/X_ENG001_Demo_v0102.py")
    chk("N3 同夾同族已有更大版號 → HOLD", n3["verdict"] == "HOLD" and n3["rules"] == ["N3"], n3["why"])
    chk("N3 --allow-gap 明說補環 → PASS", j("functional modules/X/X_ENG001_Demo_v0102.py", {"functional modules/X/X_ENG001_Demo_v0102.py"})["verdict"] == "PASS")
    chk("已登過號的舊檔不回溯 → SKIP", j("functional modules/X/X_ENG001_Demo_v0100.py")["verdict"] == "SKIP")
    chk("非程式檔(冊 / 文件)照前版 → SKIP", j("supportive modules/registry/VIA_Policy_Laws_SSOT_v0117.json")["verdict"] == "SKIP")
    chk("族名可帶點與連字號(via_net_unified · VIA-X)", j("supportive modules/network/via-net.unified_v0102.py")["verdict"] == "PASS")
    chk("參考 / 收件 / 報表夾的同名副本不算撞號", not [t for t in tree_files(Path("/nonexistent-root-for-test"))]
        and "references" in SKIP_PARTS and "intake" in SKIP_PARTS)
    with tempfile.TemporaryDirectory() as td:
        lg = Path(td) / "gate.jsonl"
        res = gate(["functional modules/X/X_ENG001_Demo_v0104.py", "functional modules/X/X_ENG001_Demo.py",
                    "supportive modules/registry/A_v0100.json"], "AI", None, tree, reg, lg)
        lines = [json.loads(x) for x in lg.read_text(encoding="utf-8").splitlines()]
        chk("LOG:只增 · 每個判定一列(SKIP 不記)· 時間到分鐘 · operator · engine",
            len(lines) == 2 and {x["verdict"] for x in lines} == {"PASS", "FAIL"}
            and re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} \+00:00$", lines[0]["at"]) and lines[0]["operator"] == "AI"
            and lines[0]["engine"].endswith(VERSION), len(lines))
        gate(["functional modules/X/X_ENG001_Demo_v0102.py"], "Tony", None, tree, reg, lg, write=False)
        chk("gate 試算不寫帳", len(lg.read_text(encoding="utf-8").splitlines()) == 2)
    seen = {}
    keep_main, keep_gate = PRIOR.main, globals()["gate"]
    PRIOR.main = lambda a: seen.update(args=list(a)) or 0
    try:
        globals()["gate"] = lambda files, op, gaps, **k: [judge(f, tree + list(files), reg, gaps) for f in files]
        rc = main(["--apply", "--scope", "functional modules/X/X_ENG001_Demo_v0104.py", "functional modules/X/X_ENG001_Demo.py",
                   "supportive modules/registry/A_v0100.json"])
        chk("--apply --scope:擋下的檔拿掉,其餘交前版發號", rc == 0 and seen.get("args") == ["--apply", "--scope",
            "functional modules/X/X_ENG001_Demo_v0104.py", "supportive modules/registry/A_v0100.json"], seen.get("args"))
        seen.clear()
        rc2 = main(["--apply", "--scope", "functional modules/X/X_ENG001_Demo.py"])
        chk("本批全被擋 → rc 2 · 前版不跑(一列不寫)", rc2 == 2 and not seen, rc2)
        rc3 = main(["--apply", "--scope", "functional modules/X/X_ENG001_Demo_v0102.py", "--allow-gap", "functional modules/X/X_ENG001_Demo_v0102.py"])
        chk("--allow-gap 旗標取出後不混進範圍", rc3 == 0 and seen.get("args") == ["--apply", "--scope", "functional modules/X/X_ENG001_Demo_v0102.py"],
            seen.get("args"))
        seen.clear()
        main(["--apply", "--scope", "functional modules/X/X_ENG001_Demo_v0104.py", "--operator", "Tony"])
        chk("operator 照傳給前版收據", seen.get("args", [])[:2] == ["--operator", "Tony"], seen.get("args"))
    finally:
        PRIOR.main, globals()["gate"] = keep_main, keep_gate
    real = tree_files()
    chk("真樹可讀(git ls-files)· 前版 v0120 在列", f"supportive modules/registry/{PRIOR_PATH.name}" in real, f"{len(real)} 支")
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("尾版保有前版公開名稱(TAILAPI · 經 __getattr__ 轉接)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("不碰 TA-Lib · 不寫同意閘", not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src))
    if deep:
        rc0 = PRIOR.selftest(deep=False)
        chk("前版 v0120 自測過", rc0 == 0, f"rc {rc0}")
    print(f"[計] {_STEM} {VERSION} 本版 {sum(checks)}/{len(checks)} " + ("PASS" if all(checks) else "FAIL")
          + ("" if deep else " · 前版自測另跑(--selftest --deep)"))
    return 0 if all(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
