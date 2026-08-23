#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_intake_v0101 — 自動化收編管線(TOOL-036;操作員令 2026-08-17)
====================================================================
令:全面檢視+分類+編號+註冊+建檔自動化(分層收編/Truth-by-Filename/
Add-Only/AST 特徵/URN 賦碼/靜態高密度報表)。
治理裁決(紅線優先於顧問文):
  ① 零刪除 — 「無情清洗」改「封存搬移」:(N) 副本先 hash 對本體,
     全同→封存組;不同→HOLD 候裁(零搬動);永不 Remove-Item
  ② 不開第三根 — Core/Plugins 落倉內受控雙層目錄(system_core/
     plugins_pool,git 版控=真 Add-Only);封存落來源側 _VIA_Intake_Archive
  ③ URN 獨立名空間 — VIA-CORE-####/VIA-PLUG-####,與 TOOL/ENG 共存
四階段:①靜態特徵提取(檔名即真理+AST 輕量掃描,零執行零 import)
       ②自動分類+URN(拓撲規則:Core/Plugin/Archive/HOLD)
       ③SSOT 註冊+實體搬移(dry-run 預設;--commit 才動;manifest+--undo)
       ④靜態高密度報表(console+JSON 存證)
v0100→v0101:掃描件 SyntaxWarning(如 invalid escape sequence)消音
——警告屬被掃檔之事,不外洩操作員主控台(工作站實測噪音勘誤)。
語法雙軌:.py=ast.parse(可同步軌;逐檔獨立)· .ps1=pwsh AST(在則跑,
缺則誠實 NOT_RUN);語法敗=列示不收編(Zero-Hydra:不碰健康命名空間)
用法:via-intake                     → dry-run 計畫+報表(預設掃 ~\Downloads)
     via-intake --root <dir>        → 指定掃描根
     via-intake --commit            → 執行搬移+註冊(寫 manifest)
     via-intake --undo <manifest>   → 整批還原
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

import ast as pyast
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
CORE_DIR = VIA / "system_core"
PLUG_DIR = VIA / "plugins_pool"
REG_P = HERE / "VIA_Intake_Registry_v0100.json"
OUT = VIA / "VIA_Reports" / "intake_runs"

DUP_RX = re.compile(r"^(?P<base>.+?)\s*\((?P<n>\d+)\)(?P<ext>\.[^.]+)?$")
VER_RX = re.compile(r"[_-]v(?P<ver>\d{3,4}[A-Z]?\d*)", re.I)
NAME_RX = re.compile(r"(?:^|[_-])VIA[_-](?P<rest>.+?)(?:[_-]v\d|\.|$)", re.I)
CORE_KEYS = ("centralgovernance", "motherroot", "mother-root", "systemmanager",
             "system-manager", "smartsync", "ssot", "idnumbering", "governance")
PLUG_KEYS = ("vdf", "vrn", "vap", "sixflow", "html", "flow", "dataforge",
             "viewport", "visuallock", "fis", "backtest", "grouprotation",
             "nullsupported", "evidencerecovery", "rehydration", "runtimereadiness",
             "blockcomment", "conflictrepair", "threelist", "gate")
ARCH_KEYS = ("_extracted", "dryrun", "readonly.zip", "_deploy")
EXTS = {".py", ".ps1", ".psm1", ".json", ".html", ".md", ".cmd", ".zip"}


def h12(p: Path) -> str:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    except Exception:
        return "?"


def py_features(p: Path):
    """AST 輕量掃描(零執行):class/def/import;語法敗誠實回報。"""
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)  # 被掃檔之警告不外洩
            tree = pyast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as exc:
        return {"syntax": "FAIL", "err": f"L{exc.lineno}: {exc.msg}"}
    cls = [n.name for n in pyast.walk(tree) if isinstance(n, pyast.ClassDef)]
    fns = [n.name for n in tree.body if isinstance(n, (pyast.FunctionDef, pyast.AsyncFunctionDef))]
    imps = sorted({(a.name if isinstance(n, pyast.Import) else n.module or "").split(".")[0]
                   for n in pyast.walk(tree) if isinstance(n, (pyast.Import, pyast.ImportFrom))
                   for a in (n.names if isinstance(n, pyast.Import) else [n])} - {""})
    return {"syntax": "OK", "classes": cls[:8], "functions": fns[:8], "imports": imps[:12]}


def ps_syntax(paths: list[Path]):
    """pwsh AST 批次語法道(缺 pwsh 誠實 NOT_RUN)。"""
    pw = shutil.which("pwsh")
    if not pw or not paths:
        return {str(p): "NOT_RUN(pwsh 缺)" if not pw else "NOT_RUN" for p in paths}
    lst = "\n".join(str(p) for p in paths)
    script = ('Get-Content -LiteralPath $env:VIA_PSLIST | ForEach-Object { '
              '$e=$null;[void][System.Management.Automation.Language.Parser]::ParseFile($_,[ref]$null,[ref]$e);'
              '"$_`t$($e.Count)" }')
    import os
    import tempfile
    fd, tmp = tempfile.mkstemp(suffix=".txt")
    os.close(fd)  # Windows 鎖修(缺陷二前例)
    try:
        Path(tmp).write_text(lst, encoding="utf-8")
        env = dict(os.environ, VIA_PSLIST=tmp)
        r = subprocess.run([pw, "-NoProfile", "-Command", script], capture_output=True,
                           text=True, timeout=600, env=env, stdin=subprocess.DEVNULL)
        out = {}
        for line in r.stdout.splitlines():
            if "\t" in line:
                f, n = line.rsplit("\t", 1)
                out[f] = "OK" if n.strip() == "0" else f"FAIL({n.strip()} 錯)"
        return {str(p): out.get(str(p), "NOT_RUN") for p in paths}
    except Exception as exc:
        return {str(p): f"NOT_RUN({type(exc).__name__})" for p in paths}
    finally:
        try:
            Path(tmp).unlink()
        except OSError:
            pass


def classify(name: str) -> tuple[str, str]:
    low = name.lower()
    for k in ARCH_KEYS:
        if k in low:
            return "ARCHIVE", f"檔名含 {k}"
    if low.endswith(".zip"):
        return "ARCHIVE", "過渡壓縮包"
    if any(k in low for k in CORE_KEYS):
        return "CORE", "核心引擎鍵詞"
    if any(k in low for k in PLUG_KEYS):
        return "PLUG", "業務模組鍵詞"
    return "PLUG", "預設模組層(候升級)"


def parse_name(name: str):
    ver = VER_RX.search(name)
    m = NAME_RX.search(name)
    action = (m.group("rest") if m else Path(name).stem).strip("_-")
    return {"action": action[:60], "version": ver.group("ver") if ver else "—"}


def load_reg():
    if REG_P.exists():
        try:
            return json.loads(REG_P.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"schema": "VIA.IntakeRegistry.v1", "namespace": "VIA-CORE/VIA-PLUG(獨立名空間,與 TOOL/ENG 共存)",
            "modules": {}, "ledger": []}


def next_urn(reg: dict, tier: str) -> str:
    pre = f"VIA-{tier}"
    n = sum(1 for u in reg["modules"] if u.startswith(pre)) + 1
    return f"{pre}-{n:04d}"


def main() -> int:
    args = sys.argv[1:]
    if "--undo" in args:
        mf = Path(args[args.index("--undo") + 1])
        plan = json.loads(mf.read_text(encoding="utf-8"))
        n = 0
        for mv in reversed(plan.get("moves", [])):
            src, dst = Path(mv["to"]), Path(mv["from"])
            if src.exists() and not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                n += 1
        print(f"[undo] 還原 {n}/{len(plan.get('moves', []))} 件(既存目標誠實略過)")
        return 0

    commit = "--commit" in args
    root = Path(args[args.index("--root") + 1]) if "--root" in args else Path.home() / "Downloads"
    if not root.is_dir():
        print(f"[FAIL] 掃描根不存在:{root}")
        return 1
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    arch = root / "_VIA_Intake_Archive"
    reg = load_reg()
    print(f"=== 自動化收編管線 v0100 · {root} · {'COMMIT' if commit else 'DRY-RUN(--commit 才動)'} ===")
    print("── ① 靜態特徵提取(檔名即真理+AST 零執行)──")

    cands = [p for p in sorted(root.iterdir()) if p.is_file() and p.suffix.lower() in EXTS
             and ("via" in p.name.lower())
             and not p.name.startswith(("VIA_Intake_Manifest", "VIA_Tidy_Manifest", "_VIA_"))]
    print(f"  [掃] VIA 族候選 {len(cands)} 件(副檔名 {'/'.join(sorted(e.strip('.') for e in EXTS))})")

    # (N) 副本家族:hash 對本體——全同=封存組;不同=HOLD 候裁;本體缺=以最新副本為主件
    families: dict[str, list[Path]] = {}
    for p in cands:
        m = DUP_RX.match(p.name)
        base = (m.group("base") + (m.group("ext") or "")) if m else p.name
        families.setdefault(base, []).append(p)
    primaries, dup_arch, holds = [], [], []
    for base, members in families.items():
        base_p = root / base
        prim = base_p if base_p in members else sorted(members, key=lambda x: x.stat().st_mtime)[-1]
        ph = h12(prim)
        primaries.append(prim)
        for m_ in members:
            if m_ == prim:
                continue
            (dup_arch if h12(m_) == ph else holds).append(m_)

    # 語法雙軌(只驗主件)
    py_files = [p for p in primaries if p.suffix == ".py"]
    ps_files = [p for p in primaries if p.suffix in (".ps1", ".psm1")]
    feats = {str(p): py_features(p) for p in py_files}
    ps_res = ps_syntax(ps_files)
    n_ps_fail = sum(1 for v in ps_res.values() if v.startswith("FAIL"))
    n_py_fail = sum(1 for v in feats.values() if v.get("syntax") == "FAIL")
    print(f"  [語法] py {len(py_files)} 件(敗 {n_py_fail})· ps1 {len(ps_files)} 件"
          f"(敗 {n_ps_fail};{'pwsh 道' if shutil.which('pwsh') else 'pwsh 缺=NOT_RUN 誠實'})"
          f" · 語法敗=可同步軌逐檔獨立修,本輪不收編(Zero-Hydra)")

    print("── ② 自動分類+URN(拓撲規則)──")
    plan_moves, registered, archived, syntax_hold = [], [], [], []
    for p in primaries:
        tier, why = classify(p.name)
        syn = feats.get(str(p), {}).get("syntax") or ("FAIL" if ps_res.get(str(p), "").startswith("FAIL") else "OK")
        if syn == "FAIL":
            syntax_hold.append((p, feats.get(str(p), {}).get("err") or ps_res.get(str(p), "")))
            continue
        if tier == "ARCHIVE":
            archived.append(p)
            plan_moves.append({"from": str(p), "to": str(arch / "transitional" / p.name), "why": why})
            continue
        meta = parse_name(p.name)
        urn = next_urn(reg, tier)
        dest = (CORE_DIR if tier == "CORE" else PLUG_DIR) / p.name
        reg["modules"][urn] = {"id": urn, "filename": p.name, "tier": tier, "why": why,
                               "action": meta["action"], "version": meta["version"],
                               "sha12": h12(p), "bytes": p.stat().st_size,
                               "ast": feats.get(str(p), {"syntax": ps_res.get(str(p), "—")}),
                               "from": str(p), "dest": str(dest),
                               "status": "MOVED" if commit else "PLANNED", "ts": ts}
        registered.append((urn, p, tier, meta))
        plan_moves.append({"from": str(p), "to": str(dest), "why": f"{tier}·{why}", "urn": urn})
    for p in dup_arch:
        plan_moves.append({"from": str(p), "to": str(arch / "dup_identical" / p.name), "why": "副本全同本體"})

    print(f"  [分類] CORE {sum(1 for u, *_ in registered if u.startswith('VIA-CORE'))} · "
          f"PLUG {sum(1 for u, *_ in registered if u.startswith('VIA-PLUG'))} · "
          f"封存 {len(archived) + len(dup_arch)}(過渡 {len(archived)}+全同副本 {len(dup_arch)})· "
          f"HOLD 候裁 {len(holds)}(副本內容≠本體,零搬動)· 語法敗 {len(syntax_hold)}")
    for p in holds[:6]:
        print(f"     ⚠ HOLD:{p.name[:70]}")
    for p, e in syntax_hold[:6]:
        print(f"     ✗ 語法敗:{p.name[:56]} · {str(e)[:40]}")

    print("── ③ SSOT 註冊+實體搬移(Add-Only)──")
    mf = root / f"VIA_Intake_Manifest_{ts}.json"
    mf.write_text(json.dumps({"schema": "VIA.IntakeManifest.v1", "ts": ts, "root": str(root),
                              "mode": "commit" if commit else "dry_run", "moves": plan_moves,
                              "holds": [str(p) for p in holds],
                              "syntax_hold": [[str(p), str(e)[:120]] for p, e in syntax_hold]},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    if commit:
        done = skip = 0
        for mv in plan_moves:
            src, dst = Path(mv["from"]), Path(mv["to"])
            if not src.exists() or dst.exists():
                skip += 1
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            done += 1
        reg["ledger"].append({"ts": ts, "root": str(root), "moved": done, "skipped": skip,
                              "registered": len(registered), "holds": len(holds)})
        REG_P.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  [搬] {done} 件歸位 · 略過 {skip} · 註冊表 {REG_P.name}(append-only)")
        print(f"  [單] {mf.name}(--undo 可整批還原;零刪除)")
    else:
        print(f"  [dry-run] 零搬動零註冊 · 計畫單 {mf.name} · 確認後:via-intake --commit")

    print("── ④ 靜態高密度報表 ──")
    print(f"  Total Scanned: {len(cands)} · Registered: {len(registered)} · "
          f"Archived: {len(archived) + len(dup_arch)} · HOLD: {len(holds) + len(syntax_hold)}")
    for urn, p, tier, meta in registered[:16]:
        print(f"  {urn} | {meta['action'][:44]:<44} | v{meta['version']:<6} | {'ACTIVE' if commit else 'PLANNED'}")
    if len(registered) > 16:
        print(f"  …共 {len(registered)} 件(全清單見存證)")
    OUT.mkdir(parents=True, exist_ok=True)
    ev = OUT / f"INTAKE_{ts}.json"
    ev.write_text(json.dumps({"schema": "VIA.Intake.v1", "ts": ts, "root": str(root),
                              "scanned": len(cands), "registered": [u for u, *_ in registered],
                              "archived": len(archived) + len(dup_arch),
                              "holds": [str(p) for p in holds],
                              "syntax_hold": [[str(p), str(e)[:120]] for p, e in syntax_hold],
                              "policy": "zero_delete·add_only·dry_run_default·no_third_root·urn_namespace"},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存證] {ev.relative_to(VIA)}")
    print("  [鐵則] 零刪除(封存搬移+manifest+--undo)· HOLD 候裁不代決 · 語法敗不收編")
    return 0


if __name__ == "__main__":
    sys.exit(main())
