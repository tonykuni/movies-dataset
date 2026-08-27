#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_rename_engine_v0100 — 引擎模組實體更名引擎(TOOL-065)
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
              "freeze", "_syntaxfix_")
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
    run["undone_at"] = NOW
    lp.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(undone), undone


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
    ok, total = 0, 7
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
    if "--commit" in a:
        return cmd_commit(scope)
    if "--undo" in a:
        return cmd_undo()
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
