#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_rename_engine_v0101 — 引擎模組實體更名引擎(TOOL-065)
--------------------------------------------------------------------
v0100→v0101(批38 二期令+INCIDENT-20260819 加固):
  --commit-risky:RISKY 件更名+引用者原子改寫。事故教訓三防:
  ①撤引號整字規則(短通用字幹如 status/scope 會傷字典鍵);
  ②glob 置換加左字界(防疊字);③唯一字幹白名單閘——字幹 len≥10
  且全計畫唯一才自動改寫,否則 HOLD_AMBIGUOUS 候人工。
  站點式改寫僅認:檔名引用(stem 後接 .py)/import·from 行/glob 底。
  記憶體先改先驗(觸及 .py 全 ast.parse)→備份→落盤;敗=家族回滾。
  --undo 反轉改名+備份夾整還原。
====================================================================
操作員令(批26):優化自動編號+更名所有引擎模組。
——實體改名紅線之操作員明確解鎖令(命名冊自載條款:落地改名需
明確令)。Zero-Hydra 落法:

  ① 引用圖分析分級(不盲改):
     SAFE   = 全倉 .py/.cmd/.ps1 零外部引用該檔家族詞幹 → 可改
     RISKY  = 有引用者(啟動器 glob/import/grid 站)→ 不改,列引用者
              (改此類需同 commit 原子改寫引用者——候後續波)
     ALREADY= 檔名已canonical 開頭 → 零動作
     HOLD   = 凍結/_sha 鏡像/檢疫/rollback/venv/證據區 → 零觸碰
  ② 編號永不變:改名走命名冊鍵遷移(舊鍵 moved_to 新鍵,canonical
     /num 原封),下輪 namereg 掃描 新編=0 為驗證標準。
  ③ 可逆:每改一筆入 VIA_Rename_Ledger_v0100.json(old/new/ts),
     --undo 全數反轉(零刪除——改名=搬移非刪除)。
  ④ 逐檔 parse 閘:改前可讀、改後路徑在位才記帳。

用法:
  --plan              全倉更名計畫(分級統計+計畫檔;零動作)
  --commit            執行 SAFE 級更名(+命名冊鍵遷移+台帳)
  --scope <SYS>       限定子系統(VRN/VDF/…;與 --plan/--commit 並用)
  --undo              反轉最近一輪 commit(依台帳)
  --selftest          七檢(沙盒 fixture)
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

import ast
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REG_PATH = HERE / "VIA_Naming_Registry_v0100.json"
LEDGER_PATH = HERE / "VIA_Rename_Ledger_v0100.json"
RUNS = VIA / "VIA_Reports" / "rename_runs"
NOW = datetime.now().strftime("%Y%m%d_%H%M%S")

VER_RX = re.compile(r"([_-]v?\d{2,4}[a-z]?)$", re.IGNORECASE)
HOLD_FRAGS = ("_sha", "_review_quarantine", "__pycache__", "/vendor/",
              "package_samples", "/docs/", "quarantine", ".venv",
              "site-packages", "_via_mother_root_reconciliation_runs",
              "/rollback/", "/evidence", "knowledge/source_docs",
              "freeze", "_syntaxfix_", "rename_runs")
REF_EXTS = (".py", ".cmd", ".ps1")


def load_reg(path=None):
    return json.loads((path or REG_PATH).read_text(encoding="utf-8"))


def save_reg(reg, path=None):
    p = path or REG_PATH
    bak = p.with_suffix(f".pre_{NOW}.bak")
    if p.exists():
        bak.write_bytes(p.read_bytes())
    p.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")


def strip_ver(stem: str):
    m = VER_RX.search(stem)
    return (stem[: m.start()], m.group(1)) if m else (stem, "")


def build_ref_index(root: Path, hold_frags=HOLD_FRAGS):
    """全倉引用索引:檔 → 內文(僅 .py/.cmd/.ps1;排除 HOLD 區)。"""
    idx = {}
    for p in root.rglob("*"):
        if p.suffix.lower() not in REF_EXTS or not p.is_file():
            continue
        rp = str(p.relative_to(root)).replace("\\", "/")
        if any(f in rp for f in hold_frags):
            continue
        try:
            idx[rp] = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
    return idx


def plan(root: Path, reg: dict, scope: str | None, hold_frags=HOLD_FRAGS):
    """回 (rows, dist)。row={family,old,new,cls,refs}。"""
    idx = build_ref_index(root, hold_frags)
    rows = []
    for fam_key, it in reg.get("items", {}).items():
        if it.get("moved_to"):
            continue
        if scope and it.get("sys") != scope:
            continue
        canonical = it["canonical"]
        for mem in list(it.get("members", [])):
            p = root / mem
            rp = mem.replace("\\", "/")
            if any(f in rp for f in hold_frags):
                rows.append({"family": fam_key, "old": mem, "new": None,
                             "cls": "HOLD", "refs": []})
                continue
            if not p.exists() or p.suffix.lower() != ".py":
                continue
            stem = p.stem
            if stem.startswith(canonical):
                rows.append({"family": fam_key, "old": mem, "new": None,
                             "cls": "ALREADY", "refs": []})
                continue
            if stem.startswith("test_") or stem.endswith("_test"):
                # pytest 收集契約:test_*.py 檔名本身是功能(grid 32 測實證)
                rows.append({"family": fam_key, "old": mem, "new": None,
                             "cls": "HOLD_TESTPATTERN", "refs": []})
                continue
            base, ver = strip_ver(stem)
            new_name = f"{canonical}{ver}.py"
            refs = [f for f, txt in idx.items()
                    if f != rp and base in txt][:8]
            cls = "RISKY" if refs else "SAFE"
            rows.append({"family": fam_key, "old": mem,
                         "new": str(Path(mem).with_name(new_name)).replace("\\", "/"),
                         "cls": cls, "refs": refs})
    dist = Counter(r["cls"] for r in rows)
    return rows, dist


def migrate_reg_key(reg, fam_key, old_mem, new_mem):
    """命名冊鍵遷移:編號永不變。舊鍵 moved_to,新鍵承 canonical/num。"""
    it = reg["items"][fam_key]
    new_stem = Path(new_mem).stem
    base, _ = strip_ver(new_stem)
    new_key = str(Path(new_mem).parent / base).replace("\\", "/")
    if new_key == fam_key:
        if new_mem not in it["members"]:
            it["members"].append(new_mem)
        return fam_key
    moved = dict(it)
    moved["members"] = [new_mem if m == old_mem else m for m in it["members"]]
    moved["renamed_from"] = fam_key
    reg["items"][new_key] = moved
    reg["items"][fam_key] = {**it, "moved_to": new_key}
    return new_key


def commit(root: Path, reg: dict, scope: str | None, reg_path=None,
           ledger_path=None, hold_frags=HOLD_FRAGS):
    rows, dist = plan(root, reg, scope, hold_frags)
    led = (json.loads(ledger_path.read_text(encoding="utf-8"))
           if (ledger_path or LEDGER_PATH).exists() else {"runs": []})
    ledger_path = ledger_path or LEDGER_PATH
    run = {"ts": NOW, "scope": scope or "ALL", "renames": []}
    n_ok = n_err = 0
    for r in rows:
        if r["cls"] != "SAFE":
            continue
        src, dst = root / r["old"], root / r["new"]
        try:
            if dst.exists():
                r["cls"] = "SKIP_DST_EXISTS"
                continue
            ast.parse(src.read_text(encoding="utf-8", errors="ignore"))  # 改前閘
            src.rename(dst)
            if not dst.exists():
                raise OSError("改後不在位")
            migrate_reg_key(reg, r["family"], r["old"], r["new"])
            run["renames"].append({"old": r["old"], "new": r["new"]})
            n_ok += 1
        except SyntaxError:
            r["cls"] = "HOLD_SYNTAX"  # 語法敗件不改(候 via-fixsyntax)
        except Exception as e:
            n_err += 1
            print(f"  [ERR] {r['old']}: {e}(該檔跳過,不中斷)")
    led["runs"].append(run)
    ledger_path.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
    return run, dist, n_ok, n_err


def undo(root: Path, ledger_path=None):
    lp = ledger_path or LEDGER_PATH
    if not lp.exists():
        print("  [SKIP] 無改名台帳")
        return 0, []
    led = json.loads(lp.read_text(encoding="utf-8"))
    if not led["runs"]:
        print("  [SKIP] 台帳空")
        return 0, []
    run = led["runs"][-1]
    undone = []
    for r in reversed(run["renames"]):
        src, dst = root / r["new"], root / r["old"]
        if src.exists() and not dst.exists():
            src.rename(dst)
            undone.append(r)
    bdir = root / run["backup_dir"] if run.get("backup_dir") else None
    if bdir and bdir.exists():
        import shutil
        new2old = {r["new"]: r["old"] for r in run.get("renames", [])}
        for f in bdir.rglob("*"):
            if f.is_file():
                rel = str(f.relative_to(bdir)).replace("\\", "/")
                shutil.copy2(f, root / new2old.get(rel, rel))
        undone.append({"restored_edits": len(run.get("edits", {}))})
    run["undone_at"] = NOW
    lp.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(undone), undone


def _layered_replace(text, old_stem, new_stem, base_old, base_new):
    """站點式引用改寫(加固版):檔名引用/import·from/glob 底三類;
    引號整字規則已撤(INCIDENT-20260819);glob 帶左字界。回 (新文, n)。"""
    import re as _re
    n = 0
    for s_old, s_new in ((old_stem, new_stem), (base_old, base_new)):
        if s_old == s_new:
            continue
        rx_file = _re.compile(r"(?<![A-Za-z0-9_])" + _re.escape(s_old) + r"(?=\.py\b)")
        text, k = rx_file.subn(s_new, text)
        n += k
        rx_imp = _re.compile(r"(?m)^(\s*(?:import|from)\s+)" + _re.escape(s_old)
                             + r"(?![A-Za-z0-9_])")
        text, k = rx_imp.subn(r"\g<1>" + s_new, text)
        n += k
    for suf in ("_v0*", "_v*"):
        rx_g = _re.compile(r"(?<![A-Za-z0-9_])" + _re.escape(base_old) + _re.escape(suf))
        text, k = rx_g.subn(base_new + suf, text)
        n += k
    return text, n


def commit_risky(root, reg, scope, reg_path=None, ledger_path=None, hold_frags=HOLD_FRAGS):
    """RISKY 原子改寫:唯一字幹白名單閘+站點式改寫+備份回滾。"""
    import shutil
    from collections import Counter as _Counter
    rows, dist = plan(root, reg, scope, hold_frags)
    idx = build_ref_index(root, hold_frags)
    ledger_path = ledger_path or LEDGER_PATH
    led = (json.loads(ledger_path.read_text(encoding="utf-8"))
           if ledger_path.exists() else {"runs": []})
    bak_dir = root / "VIA_Reports" / "rename_runs" / f"backup_{NOW}"
    backed = {}
    run = {"ts": NOW, "mode": "risky", "run_scope": scope or "ALL",
           "renames": [], "edits": {}, "backup_dir": str(bak_dir.relative_to(root))}
    _fam_of_base = {}
    for _r in rows:
        if _r.get("old"):
            _fam_of_base.setdefault(strip_ver(Path(_r["old"]).stem)[0], set()).add(_r["family"])
    base_count = _Counter({b: len(fs) for b, fs in _fam_of_base.items()})
    n_ok = n_hold = n_fail = 0

    def backup(rp):
        if rp in backed:
            return
        dst = bak_dir / rp
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rp, dst)
        backed[rp] = str(dst)

    for r in rows:
        if r["cls"] != "RISKY":
            continue
        old_rp, new_rp = r["old"], r["new"]
        old_stem = Path(old_rp).stem
        base_old, _v = strip_ver(old_stem)
        if len(base_old) < 10 or base_count[base_old] > 1:
            n_hold += 1
            continue                      # HOLD_AMBIGUOUS:短字幹/同字幹禁自動
        if ((root / old_rp).parent / "__init__.py").exists():
            n_hold += 1
            continue                      # HOLD_PACKAGE:套件內檔名=API(相對匯入)
        import re as _re2
        _imp_rx = _re2.compile(r"(?m)^\s*(?:import|from)\s+(?:"
                               + _re2.escape(Path(old_rp).stem) + "|"
                               + _re2.escape(base_old) + r")(?![A-Za-z0-9_])")
        if any(_imp_rx.search(txt) for rp2, txt in idx.items() if rp2 != old_rp):
            n_hold += 1
            continue                      # HOLD_IMPORTED:被 import 者=模組身分,改名需別名語意
        srcp = root / old_rp
        if not srcp.exists() or (root / new_rp).exists():
            continue
        new_stem = Path(new_rp).stem
        base_new, _ = strip_ver(new_stem)
        staged = {}
        gate_ok = True
        for ref_rp, text in idx.items():
            if ref_rp == old_rp or base_old not in text:
                continue
            new_text, k = _layered_replace(text, old_stem, new_stem, base_old, base_new)
            if k == 0:
                continue
            if ref_rp.endswith(".py"):
                try:
                    ast.parse(new_text)
                except SyntaxError:
                    gate_ok = False
                    break
            staged[ref_rp] = (new_text, k)
        if not gate_ok:
            n_fail += 1
            continue
        try:
            ast.parse(srcp.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        try:
            for ref_rp, (new_text, k) in staged.items():
                backup(ref_rp)
                (root / ref_rp).write_text(new_text, encoding="utf-8")
                idx[ref_rp] = new_text
                run["edits"][ref_rp] = run["edits"].get(ref_rp, 0) + k
            srcp.rename(root / new_rp)
            if old_rp in idx:
                idx[new_rp] = idx.pop(old_rp)
            migrate_reg_key(reg, r["family"], old_rp, new_rp)
            run["renames"].append({"old": old_rp, "new": new_rp})
            n_ok += 1
        except Exception:
            for ref_rp in staged:
                if ref_rp in backed:
                    shutil.copy2(backed[ref_rp], root / ref_rp)
            if (root / new_rp).exists() and not srcp.exists():
                (root / new_rp).rename(srcp)
            n_fail += 1
    led["runs"].append(run)
    ledger_path.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
    return run, n_ok, n_hold, n_fail


def cmd_commit_risky(scope):
    reg = load_reg()
    run, n_ok, n_hold, n_fail = commit_risky(VIA, reg, scope)
    save_reg(reg)
    print(f"  [二期] 更名 {n_ok} · HOLD_AMBIGUOUS(短/同字幹候人工) {n_hold} · 敗回滾 {n_fail}")
    print(f"  [改寫] 引用者 {len(run['edits'])} 檔 {sum(run['edits'].values())} 處 · 備份 {run['backup_dir']}")
    print("  [雙閘] 續跑 grid --fast FAIL 0+namereg 新編 0;不過即 --undo")
    return 0


def cmd_plan(scope):
    reg = load_reg()
    rows, dist = plan(VIA, reg, scope)
    RUNS.mkdir(parents=True, exist_ok=True)
    ev = RUNS / f"RENAMEPLAN_{NOW}.json"
    ev.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [計畫] SAFE {dist.get('SAFE',0)} · RISKY {dist.get('RISKY',0)}"
          f" · ALREADY {dist.get('ALREADY',0)} · HOLD {dist.get('HOLD',0)} · 存證 {ev.name}")
    for r in rows[:12]:
        if r["cls"] == "SAFE":
            print(f"    SAFE {r['old']} → {Path(r['new']).name}")
    risky = [r for r in rows if r["cls"] == "RISKY"]
    for r in risky[:6]:
        print(f"    RISKY {r['old']} ← 引用:{'、'.join(Path(x).name for x in r['refs'][:3])}")
    if len(risky) > 6:
        print(f"    …RISKY 另 {len(risky)-6} 件(見存證)")
    print("  [則] SAFE 才 --commit;RISKY 需原子改寫引用者候後續波;編號永不變")
    return 0


def cmd_commit(scope):
    reg = load_reg()
    run, dist, n_ok, n_err = commit(VIA, reg, scope)
    save_reg(reg)
    print(f"  [更名] 完成 {n_ok} · 錯 {n_err} · RISKY 未動 {dist.get('RISKY',0)}"
          f" · ALREADY {dist.get('ALREADY',0)}")
    print(f"  [台帳] {LEDGER_PATH.name} run@{run['ts']}(--undo 可逆)")
    print("  [驗證標準] 續跑 iface+namereg 應 新編=0(編號永不變實證)")
    return 0


def cmd_undo():
    n, _ = undo(VIA)
    print(f"  [反轉] {n} 筆改名還原(台帳留痕)")
    if n:
        print("  [注意] 命名冊鍵遷移不自動反轉——重跑 namereg 前先確認;鍵歷史 append-only 無損")
    return 0


def selftest() -> int:
    import tempfile
    ok, total = 0, 10
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "eng").mkdir()
        (root / "bin").mkdir()
        (root / "eng/loose_tool_v0100.py").write_text("x = 1\n", encoding="utf-8")
        (root / "eng/hub_core_v0100.py").write_text("y = 2\n", encoding="utf-8")
        (root / "bin/run-hub.cmd").write_text("py hub_core_v0100.py\n", encoding="utf-8")
        (root / "eng/SYS_ENG003_Done_v0100.py").write_text("z = 3\n", encoding="utf-8")
        reg = {"items": {
            "eng/loose_tool": {"sys": "SYS", "kind": "ENG", "num": 1,
                               "canonical": "SYS_ENG001_LooseTool",
                               "members": ["eng/loose_tool_v0100.py"]},
            "eng/hub_core": {"sys": "SYS", "kind": "ENG", "num": 2,
                             "canonical": "SYS_ENG002_HubCore",
                             "members": ["eng/hub_core_v0100.py"]},
            "eng/SYS_ENG003_Done": {"sys": "SYS", "kind": "ENG", "num": 3,
                                    "canonical": "SYS_ENG003_Done",
                                    "members": ["eng/SYS_ENG003_Done_v0100.py"]},
        }, "counters": {"SYS_ENG": 3}}
        rows, dist = plan(root, reg, None, hold_frags=("__pycache__",))
        if dist == Counter({"SAFE": 1, "RISKY": 1, "ALREADY": 1}):
            ok += 1; print("  [PASS] 分級:SAFE/RISKY(啟動器引用)/ALREADY")
        else:
            print(f"  [FAIL] 分級 {dist}")
        lp = root / "ledger.json"
        run, dist2, n_ok, n_err = commit(root, reg, None, ledger_path=lp,
                                         hold_frags=("__pycache__",))
        if n_ok == 1 and (root / "eng/SYS_ENG001_LooseTool_v0100.py").exists() \
                and not (root / "eng/loose_tool_v0100.py").exists():
            ok += 1; print("  [PASS] SAFE 更名落地(canonical+版尾保留)")
        else:
            print("  [FAIL] 更名")
        if (root / "eng/hub_core_v0100.py").exists():
            ok += 1; print("  [PASS] RISKY 未動(啟動器不破)")
        else:
            print("  [FAIL] RISKY 被動")
        it_new = reg["items"].get("eng/SYS_ENG001_LooseTool")
        it_old = reg["items"]["eng/loose_tool"]
        if it_new and it_new["num"] == 1 and it_new["canonical"] == "SYS_ENG001_LooseTool" \
                and it_old.get("moved_to") == "eng/SYS_ENG001_LooseTool" \
                and reg["counters"]["SYS_ENG"] == 3:
            ok += 1; print("  [PASS] 命名冊鍵遷移:編號永不變+舊鍵 moved_to 留痕")
        else:
            print("  [FAIL] 鍵遷移")
        led = json.loads(lp.read_text(encoding="utf-8"))
        if led["runs"][-1]["renames"] == [{"old": "eng/loose_tool_v0100.py",
                                           "new": "eng/SYS_ENG001_LooseTool_v0100.py"}]:
            ok += 1; print("  [PASS] 改名台帳(old/new 可逆紀錄)")
        else:
            print("  [FAIL] 台帳")
        n_undo, _ = undo(root, ledger_path=lp)
        if n_undo == 1 and (root / "eng/loose_tool_v0100.py").exists():
            ok += 1; print("  [PASS] --undo 全反轉(零刪除搬移)")
        else:
            print("  [FAIL] undo")
        (root / "eng/broken_v0100.py").write_text("def f(:\n", encoding="utf-8")
        reg["items"]["eng/broken"] = {"sys": "SYS", "kind": "ENG", "num": 4,
                                      "canonical": "SYS_ENG004_Broken",
                                      "members": ["eng/broken_v0100.py"]}
        run3, _, n3, _ = commit(root, reg, None, ledger_path=lp,
                                hold_frags=("__pycache__",))
        if (root / "eng/broken_v0100.py").exists():
            ok += 1; print("  [PASS] 語法敗件不改(候 via-fixsyntax,parse 閘)")
        else:
            print("  [FAIL] parse 閘")
    # 8-10 二期(加固版:glob 專屬可名/import·套件·短字幹三 HOLD/undo 映射)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "eng").mkdir(); (root / "bin").mkdir(); (root / "VIA_Reports").mkdir()
        (root / "eng" / ("rotation_flywheel" + "_v0100.py")).write_text("R = 1\n", encoding="utf-8")
        gl = '("rotation_flywheel' + '_v0*.py")'
        (root / "bin/run-rot.cmd").write_text("for %%f in " + gl + " do py %%f\n", encoding="utf-8")
        (root / "eng/rotation_gearbox_v0100.py").write_text("G = 1\n", encoding="utf-8")
        (root / "eng/uses_gearbox.py").write_text("import rotation_gearbox_v0100\n", encoding="utf-8")
        (root / "eng/pkgzone").mkdir()
        (root / "eng/pkgzone/__init__.py").write_text("", encoding="utf-8")
        (root / "eng/pkgzone/availability_probe.py").write_text("A = 1\n", encoding="utf-8")
        (root / "eng/tiny.py").write_text("T = 1\n", encoding="utf-8")
        reg2 = {"items": {
            "eng/rotation_flywheel": {"sys": "SYS", "kind": "ENG", "num": 5,
                                      "canonical": "SYS_ENG005_RotationFlywheel",
                                      "members": ["eng/rotation_flywheel_v0100.py"]},
            "eng/rotation_gearbox": {"sys": "SYS", "kind": "ENG", "num": 6,
                                     "canonical": "SYS_ENG006_RotationGearbox",
                                     "members": ["eng/rotation_gearbox_v0100.py"]},
            "eng/pkgzone/availability_probe": {"sys": "SYS", "kind": "ENG", "num": 7,
                                               "canonical": "SYS_ENG007_AvailabilityProbe",
                                               "members": ["eng/pkgzone/availability_probe.py"]},
            "eng/tiny": {"sys": "SYS", "kind": "ENG", "num": 8,
                         "canonical": "SYS_ENG008_Tiny", "members": ["eng/tiny.py"]},
            "eng/uses_gearbox": {"sys": "SYS", "kind": "ENG", "num": 9,
                                 "canonical": "SYS_ENG009_UsesGearbox",
                                 "members": ["eng/uses_gearbox.py"]},
        }, "counters": {"SYS_ENG": 9}}
        (root / "bin/use-tiny.cmd").write_text("py tiny.py\n", encoding="utf-8")
        (root / "bin/use-pkg.cmd").write_text("py availability_probe.py\n", encoding="utf-8")
        lp2 = root / "ledger.json"
        run, n_ok2, n_hold2, n_f2 = commit_risky(root, reg2, None, ledger_path=lp2,
                                                 hold_frags=("__pycache__", "VIA_Reports"))
        cmdt = (root / "bin/run-rot.cmd").read_text(encoding="utf-8")
        if (root / "eng/SYS_ENG005_RotationFlywheel_v0100.py").exists() and \
                "SYS_ENG005_RotationFlywheel_v0*.py" in cmdt:
            ok += 1; print("  [PASS] 二期:glob 專屬引用族更名+啟動器原子改寫")
        else:
            print(f"  [FAIL] 二期改寫 {cmdt!r}")
        held_ok = (root / "eng/rotation_gearbox_v0100.py").exists() \
            and (root / "eng/pkgzone/availability_probe.py").exists() \
            and (root / "eng/tiny.py").exists() and n_hold2 >= 3 \
            and "import rotation_gearbox_v0100" in (root / "eng/uses_gearbox.py").read_text(encoding="utf-8")
        if held_ok:
            ok += 1; print("  [PASS] 三 HOLD:被 import 者/套件內檔/短字幹全數零觸碰")
        else:
            print(f"  [FAIL] HOLD 態 n_hold={n_hold2}")
        undo(root, ledger_path=lp2)
        if (root / "eng/rotation_flywheel_v0100.py").exists() and \
                "rotation_flywheel_v0*.py" in (root / "bin/run-rot.cmd").read_text(encoding="utf-8"):
            ok += 1; print("  [PASS] 二期 undo 全還原(new→old 映射)")
        else:
            print("  [FAIL] 二期 undo")
    print(f"  [計] {ok}/{total} 檢通過")
    return 0 if ok == total else 1


def main() -> int:
    a = sys.argv[1:]
    scope = None
    if "--scope" in a:
        i = a.index("--scope")
        scope = a[i + 1] if len(a) > i + 1 else None
    if "--selftest" in a:
        return selftest()
    if "--plan" in a:
        return cmd_plan(scope)
    if "--commit-risky" in a:
        return cmd_commit_risky(scope)
    if "--commit" in a:
        return cmd_commit(scope)
    if "--undo" in a:
        return cmd_undo()
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
