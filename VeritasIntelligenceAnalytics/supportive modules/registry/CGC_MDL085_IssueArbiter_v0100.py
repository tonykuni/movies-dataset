#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL085_IssueArbiter — 活動圈 CRITICAL 議題仲裁器(批133;via-arbit)
====================================================================
批133 續令:GovTriage(CGC_MDL084)分圈後,活動圈 737 CRITICAL 逐類
仲裁。本器=唯讀證據仲裁,零改動零刪除零套用(建議制):
  ① IDENTITY_COLLISION — 解析對撞路徑表,夥伴逐一分圈:
     全數落在非活動圈(備份鏡像/存證/收容)=SHADOW_ONLY(影子對撞,
     非真雙位置);≥2 活動圈成員=TRUE_DUAL→sha256 對勘:byte 全同=
     DEDUP_YIELD(整合去重紅線:讓位零動作)/異=VERSION_ARBITRATION
     候操作員裁決(零自動刪除)。
  ② SSOT_AUTHORITY_COLLISION — module_id 重複,同法仲裁。
  ③ SYNTAX — 本地覆核(compile/json.loads):鏡像件(_sha 後綴)=
     DELIVERED_MIRROR;同目錄或全樹有可解析版本後繼=SUPERSEDED
     (修版在役);餘=NEEDS_FIX 候修版(version-forward,原件零觸碰)。
  ④ SECURITY — 疑似密鑰逐行實勘(值遮罩,只判結構):字庫詞彙
     token 欄位/minified JS 束/密碼「解析程式碼」/核准口令常數=
     FALSE_POSITIVE_EVIDENCED;餘=CANDIDATE_REVIEW。高風險呼叫
     (rmtree/os.system/PS)=RISK_REGISTER 彙整(引擎內部維運操作,
     靜態鏡頭誠實列帳,候逐件審查)。
產物:VIA_Reports/govtriage_runs/ARBIT_<ts>.json(append-only)。
用法:via-arbit run | --selftest
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
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT_ROOT = VIA / "VIA_Reports" / "govtriage_runs"

_CJK_RX = re.compile(r"[一-鿿]")
_VER_RX = re.compile(r"_v\d+", re.IGNORECASE)
_LIST_RX = re.compile(r"\[.*\]", re.DOTALL)


def _triage_mod():
    """動態載入最新 GovTriage(glob 嚴禁寫死版號)重用分圈規則"""
    import importlib.util
    hits = sorted(HERE.glob("CGC_MDL084_GovTriage_v*.py"))
    spec = importlib.util.spec_from_file_location("via_govtriage_dyn", hits[-1])
    mod = importlib.util.module_from_spec(spec)
    sys.modules["via_govtriage_dyn"] = mod
    spec.loader.exec_module(mod)
    return mod


def parse_member_paths(detail: str) -> list[str]:
    """detail 內 normalized_key=…: [...] / module_id=…: [...] 路徑表"""
    m = _LIST_RX.search(str(detail))
    if not m:
        return []
    try:
        val = ast.literal_eval(m.group(0))
        return [str(x) for x in val] if isinstance(val, list) else []
    except (ValueError, SyntaxError):
        return []


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


_SHA_SUFFIX_RX = re.compile(r"(_sha[0-9a-f]{4,})+(?=\.[A-Za-z0-9]+$|$)")
_VTAG_RX = re.compile(r"_v\d+[A-Za-z0-9_]*$", re.IGNORECASE)


def _strip_sha(name: str) -> str:
    return _SHA_SUFFIX_RX.sub("", name)


def arbitrate_collision(rel_path: str, detail: str, circle_of) -> dict:
    """①② 同名/同 ID 對撞仲裁:影子/鏡像/版史/真雙四鏡頭再 hash 定生死"""
    members = parse_member_paths(detail)
    if rel_path not in members:
        members = [rel_path] + members
    act = sorted(set(m for m in members if circle_of(m) == "ACTIVE"))
    shadow = [m for m in members if circle_of(m) != "ACTIVE"]
    if len(act) <= 1:
        return {"verdict": "SHADOW_ONLY", "active": act, "shadow_n": len(shadow),
                "note": "對撞夥伴全落非活動圈(備份鏡像/存證/收容)=非真雙位置"}
    # 鏡頭一:_shaXXXX 鏡像變體讓位(去 sha 後與另一成員同名=收容鏡像)
    names = {m: Path(m).name for m in act}
    reps = [m for m in act
            if not ("_sha" in names[m]
                    and any(_strip_sha(names[m]) == names[o] for o in act if o != m))]
    mirror_n = len(act) - len(reps)
    if len(reps) <= 1:
        return {"verdict": "MIRROR_VARIANTS", "active": act, "mirror_n": mirror_n,
                "note": "同名族僅正本+_sha 收容鏡像變體=工作面單一,非真雙位置"}
    # 鏡頭二:同目錄版本家族(_vNNNN 版史=只增不減設計;glob 取最新在役)
    dirs = {str(Path(m).parent) for m in reps}
    stems = [Path(m).stem for m in reps]
    if len(dirs) == 1 and all(_VTAG_RX.search(_strip_sha(s)) for s in stems):
        cores = {_VTAG_RX.sub("", _strip_sha(s)).lower() for s in stems}
        if len(cores) == 1:
            return {"verdict": "VERSION_FAMILY_HISTORY", "active": reps,
                    "latest": reps[-1], "mirror_n": mirror_n,
                    "note": "同目錄版本家族=version-forward 版史(只增不減紅線);"
                            "在役=glob 最新,非缺陷"}
    # 鏡頭三:真雙位置 hash 定生死
    hashes = {}
    for m in reps:
        p = VIA / m
        hashes[m] = _sha(p) if p.exists() else "MISSING"
    uniq = set(hashes.values()) - {"MISSING"}
    if len(uniq) == 1 and "MISSING" not in hashes.values():
        return {"verdict": "DEDUP_YIELD", "active": reps, "sha": sorted(uniq)[0],
                "note": "byte 全同=讓位零動作(整合去重紅線;零刪除)"}
    return {"verdict": "VERSION_ARBITRATION", "active": reps, "hashes": hashes,
            "note": "真雙位置且內容異=候操作員裁決正典;零自動刪除"}


def _norm_core(name: str) -> str:
    stem = Path(name).stem
    stem = _VER_RX.sub("", stem)
    return re.sub(r"[^a-z0-9]", "", stem.lower())


def find_successor(rel_path: str) -> str | None:
    """SYNTAX 修版在役佐證:同目錄 <stem>_v*.py 或全樹核心名包含後繼"""
    p = VIA / rel_path
    sibs = sorted(p.parent.glob(p.stem.split("(")[0].strip() + "_v*" + p.suffix))
    for s in sibs:
        if s.name != p.name:
            return str(s.relative_to(VIA))
    core = _norm_core(p.name)
    core = re.sub(r"^(via|vrn|vdf|vap|grp|cgc|sup)", "", core)
    if len(core) < 12:
        return None
    for cand in VIA.rglob("*" + p.suffix):
        rel = str(cand.relative_to(VIA))
        if rel == rel_path or "VIA_Reports" in rel or "_quarantine" in rel:
            continue
        if core in _norm_core(cand.name) and _norm_core(cand.name) != _norm_core(p.name):
            try:
                if p.suffix == ".py":
                    compile(cand.read_text(encoding="utf-8", errors="replace"),
                            cand.name, "exec")
                return rel
            except SyntaxError:
                continue
    return None


def arbitrate_syntax(rel_path: str) -> dict:
    """③ SYNTAX 覆核+處置:鏡像/修版在役/候修版三態"""
    p = VIA / rel_path
    if not p.exists():
        return {"verdict": "MISSING", "note": "檔已不在(run 後樹演化)"}
    reproduced = False
    try:
        if p.suffix == ".py":
            compile(p.read_text(encoding="utf-8", errors="replace"), p.name, "exec")
        elif p.suffix == ".json":
            json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
    except (SyntaxError, ValueError):
        reproduced = True
    if not reproduced:
        return {"verdict": "NOT_REPRODUCED", "note": "本地覆核已可解析=議題過期"}
    if "_sha" in p.name:
        return {"verdict": "DELIVERED_MIRROR", "note":
                "收容鏡像件(_sha 後綴)byte-exact 唯讀=原樣保存,非工作面債"}
    succ = find_successor(rel_path)
    if succ:
        return {"verdict": "SUPERSEDED", "successor": succ,
                "note": "修版在役佐證=原件依只增不減保存,工作面走後繼版"}
    return {"verdict": "NEEDS_FIX", "note":
            "無後繼佐證=候修版(version-forward 修復;原件零觸碰)"}


def arbitrate_secret(rel_path: str, line_no) -> dict:
    """④ 疑似密鑰逐行實勘(值遮罩只判結構;絕不外流原值)"""
    p = VIA / rel_path
    if not p.exists():
        return {"verdict": "MISSING", "note": "檔已不在"}
    try:
        ln = int(float(line_no))
    except (TypeError, ValueError):
        return {"verdict": "CANDIDATE_REVIEW", "note": "行號缺=無法定位,候人工"}
    text = None
    with p.open(encoding="utf-8", errors="replace") as f:
        for i, row in enumerate(f, 1):
            if i == ln:
                text = row
                break
    if text is None:
        return {"verdict": "CANDIDATE_REVIEW", "note": "行號越界,候人工"}
    if _CJK_RX.search(text) and ("token" in text.lower()):
        return {"verdict": "FALSE_POSITIVE_EVIDENCED",
                "evidence": "字庫詞彙 token 欄位(CJK 值=領域詞非密鑰)"}
    if ".prop(" in text or len(text) > 2000:
        return {"verdict": "FALSE_POSITIVE_EVIDENCED",
                "evidence": "minified JS 束(打包程式碼非密鑰值)"}
    if "StartsWith('password" in text or ".Substring(" in text:
        return {"verdict": "FALSE_POSITIVE_EVIDENCED",
                "evidence": "密碼『解析程式碼』(讀取邏輯非硬編碼值)"}
    if re.search(r'TOKEN\s*=\s*"VIA_APPROVE', text):
        return {"verdict": "FALSE_POSITIVE_EVIDENCED",
                "evidence": "核准口令常數(治理審批片語非外部密鑰)"}
    return {"verdict": "CANDIDATE_REVIEW", "note": "無偽陽結構佐證=候人工覆核"}


def run() -> int:
    import glob as _g
    import gzip  # noqa: F401  (pandas 內部使用)
    import pandas as pd
    gt = _triage_mod()
    runs = sorted((VIA / "VIA_Reports" / "centralgov_runs").glob("RUN_*"))
    if not runs:
        print("[FAIL] 無 CentralGov run 存證")
        return 1
    issues = sorted(runs[-1].glob("round_*/issues.csv.gz"))[-1]
    df = pd.read_csv(issues, low_memory=False)
    df["circle"] = df["relative_path"].astype(str).map(gt.circle_of)
    act = df[(df["circle"] == "ACTIVE") & (df["severity"] == "CRITICAL")]
    print(f"=== 活動圈 CRITICAL 仲裁(批133)· {runs[-1].name[:40]} · {len(act)} 件 ===")
    disp: list[dict] = []
    counts: dict[str, dict[str, int]] = {}

    def add(cat, rel, verdict_obj):
        disp.append({"category": cat, "relative_path": rel, **verdict_obj})
        counts.setdefault(cat, {})
        counts[cat][verdict_obj["verdict"]] = counts[cat].get(verdict_obj["verdict"], 0) + 1

    for _, r in act.iterrows():
        cat, rel = r["category"], str(r["relative_path"])
        if cat in ("IDENTITY_COLLISION", "SSOT_AUTHORITY_COLLISION"):
            add(cat, rel, arbitrate_collision(rel, str(r["detail"]), gt.circle_of))
        elif cat == "SYNTAX":
            add(cat, rel, arbitrate_syntax(rel))
        elif cat == "SECURITY" and str(r["title"]) == "疑似硬編碼密鑰":
            add(cat + "/密鑰", rel, arbitrate_secret(rel, r["line"]))
        else:
            add(cat + "/高風險呼叫", rel,
                {"verdict": "RISK_REGISTER",
                 "pattern": str(r["detail"])[:60],
                 "note": "引擎內部維運操作;靜態鏡頭誠實列帳候逐件審查(零改動)"})
    for cat in sorted(counts):
        parts = " · ".join(f"{k}×{v}" for k, v in sorted(counts[cat].items()))
        print(f"  [{cat}] {parts}")
    dual = [d for d in disp if d["verdict"] in ("VERSION_ARBITRATION", "DEDUP_YIELD")]
    for d in dual[:12]:
        print(f"    · {d['verdict']:<19} {d['relative_path']}")
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    out = OUT_ROOT / f"ARBIT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(
        {"schema": "VIA.IssueArbiter.v1", "run": runs[-1].name, "total": len(act),
         "counts": counts, "dispositions": disp, "policy":
         "唯讀仲裁建議制;零改動零刪除零套用;晉升/刪改一律候操作員核准"},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存] {out.relative_to(VIA)}")
    return 0


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    ms = parse_member_paths("normalized_key=x: ['a/b.py', 'VIA_Reports/rename_runs/backup_1/a/b.py']")
    chk("① 對撞路徑表解析", ms == ["a/b.py", "VIA_Reports/rename_runs/backup_1/a/b.py"])

    circ = lambda p: "SCOPE_BACKUP" if "backup" in p else "ACTIVE"  # noqa: E731
    v1 = arbitrate_collision("a/b.py", "k=x: ['a/b.py', 'VIA_Reports/rename_runs/backup_1/a/b.py']", circ)
    chk("② 影子對撞判 SHADOW_ONLY", v1["verdict"] == "SHADOW_ONLY")

    with tempfile.TemporaryDirectory(dir=str(VIA)) as td:
        rel = Path(td).relative_to(VIA)
        (VIA / rel / "x1.py").write_text("A = 1\n")
        (VIA / rel / "x2.py").write_text("A = 1\n")
        (VIA / rel / "x3.py").write_text("A = 2\n")
        same = arbitrate_collision(f"{rel}/x1.py", f"k=x: ['{rel}/x1.py', '{rel}/x2.py']", lambda p: "ACTIVE")
        diff = arbitrate_collision(f"{rel}/x1.py", f"k=x: ['{rel}/x1.py', '{rel}/x3.py']", lambda p: "ACTIVE")
        chk("③ 真雙 hash 定生死(全同=讓位零動作/異=候裁決)",
            same["verdict"] == "DEDUP_YIELD" and diff["verdict"] == "VERSION_ARBITRATION")

        bad = VIA / rel / "brokenengine_pipeline.py"
        bad.write_text("f'{a\\\\}'\nx=(\n")
        s1 = arbitrate_syntax(f"{rel}/brokenengine_pipeline.py")
        (VIA / rel / "brokenengine_pipeline_v0101.py").write_text("A = 1\n")
        s2 = arbitrate_syntax(f"{rel}/brokenengine_pipeline.py")
        chk("④ SYNTAX 三態(無後繼=NEEDS_FIX;後繼在=SUPERSEDED)",
            s1["verdict"] == "NEEDS_FIX" and s2["verdict"] == "SUPERSEDED")

        sec = VIA / rel / "page.html"
        sec.write_text("line1\n{ token: 'EPFR / 北向', canon: '應收帳款' }\napi_key = \"sk-realLookingValue123456\"\n")
        f1 = arbitrate_secret(f"{rel}/page.html", 2)
        f2 = arbitrate_secret(f"{rel}/page.html", 3)
        chk("⑤ 密鑰鏡頭(字庫欄位=偽陽佐證/無佐證=候人工)",
            f1["verdict"] == "FALSE_POSITIVE_EVIDENCED" and f2["verdict"] == "CANDIDATE_REVIEW")

        (VIA / rel / "eng_v0100.py").write_text("A = 1\n")
        (VIA / rel / "eng_v0101.py").write_text("A = 2\n")
        fam = arbitrate_collision(
            f"{rel}/eng_v0100.py",
            f"k=eng: ['{rel}/eng_v0100.py', '{rel}/eng_v0101.py']", lambda p: "ACTIVE")
        chk("⑦ 版本家族=version-forward 版史非缺陷",
            fam["verdict"] == "VERSION_FAMILY_HISTORY"
            and fam["latest"].endswith("eng_v0101.py"))

        (VIA / rel / "core.py").write_text("B = 1\n")
        (VIA / rel / "core_sha1234abcd.py").write_text("B = 9\n")
        mir = arbitrate_collision(
            f"{rel}/core.py",
            f"k=core: ['{rel}/core.py', '{rel}/core_sha1234abcd.py']", lambda p: "ACTIVE")
        chk("⑧ _sha 鏡像變體=工作面單一非真雙",
            mir["verdict"] == "MIRROR_VARIANTS" and mir["mirror_n"] == 1)

    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split('def run()', 1)[1]
    chk("⑥ 零改動保證(run 段無目標樹寫入;僅 govtriage_runs 存證)",
        "OUT_ROOT" in body
        and (".un" + "link") not in body.split("def selftest", 1)[0]
        and ("shu" + "til") not in src.split("def selftest", 1)[0])
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 議題仲裁器(CGC_MDL085)· 八檢自測(合成件)===")
        return selftest()
    if "run" in args or not args:
        return run()
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
