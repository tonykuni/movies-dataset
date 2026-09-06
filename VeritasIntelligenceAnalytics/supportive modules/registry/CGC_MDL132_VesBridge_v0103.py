#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL132_VesBridge v0103 — VES 引擎標準化橋(批371;批372 分樹輸出槽+封存律+_superseded 排除+改名承接律;via-ves)
====================================================================
操作員令(批371;語音)「引擎跟模組整合除蟲功能:安全的先跑這個 JSON token,剩下的 AI 再來進行後續小修補測試,
節省 token;再一次提升它的能力;測試無誤後註冊導入使用」。
職權(收容原件 VES via_engine_standardizer.py 零觸碰;本橋只做「尾版鏡像+安全種子決策+雙跑」):
  ① 尾版鏡像  VIA 正本律=version-forward、舊版凍結;VES 全樹掃會把同族 v0100…v01xx 史版當「完全相同多頭」
              (雲端實錄:VDF/engine 217 個 ABSORB 卡幾乎全是史版)。本橋先建尾版鏡像樹 VIA_Reports/ves/tails_tree
              (同族 *_v####.py/.ps1 只取最大版號;排除 references/intake、VIA_RetiredEngines、_review_quarantine、
              __pycache__、output_hub、VIA_Reports、node_modules、venv、SCOPE_COPY、回滾夾),VES 只掃鏡像=零觸碰原樹。
  ② 安全種子  只對「VIA 律可確定性判定」的卡自動出決策 token(append-only 進 ves_decisions.jsonl):
              VERB_CLASSIFY=VIA 動詞冊(lane→READ/status→REPORT/upsert→WRITE/selftest→VALIDATE…);
              ABSORB_CONFIRM=橋塊/樣板函式(_via_net/_net_or_none/gate_open/chk/progress_bar/_newest…各引擎自持=設計)
              →REJECT;CLUSTER_ACCEPT=selftest 群→REJECT(各引擎自測設計)。其餘(RISK/TYPES/一般 CLUSTER)留給 AI。
  ③ 雙跑      第 1 跑出卡→種子→第 2 跑確定性套用(卡減少/merge_plan APPROVED·REJECTED/taxonomy);印卡數前後、
              閘門、沙盤 verdict、Hydra 等級;--apply 永不經本橋(操作員親打 ACTIVATION token)。
  ④ 誠實      VES 缺=SKIP;每步 rc 原話;種子決策帶「V 級:VIA 律」註記;不建議刪除;Hydra 不自降。
v0100→v0101(批372 雲端實錄:全樹 2088 尾版單跑 >10 分鐘逾時 rc124):--root 子樹各自輸出槽 out_<slug>/tails_<slug>
(決策檔仍共用 VES_DIR/ves_decisions.jsonl=上層目錄律),四大子樹可平行分跑;全樹 --root 省略=out/tails_tree 不變。
v0101→v0102(批372 VRN 實錄:316 卡中 ABSORB 240 張=_sha<hash> 上傳鏡像/瀏覽器複本 (n).py=唯讀封存非多頭):尾版鏡像
加封存律 ARCHIVE_RX(_sha[0-9a-f]{8,}|\(\d+\))=排除(與 MDL069 同律);鏡像統計印 archive 數。
v0102→v0103(批372 VRN 實錄:ABSORB 190 張中 169 個被吸收端在 _superseded 夾=整併後留位史件;其餘為 VRN_MDL004/005 舊名 vs
VRN_ENG017/018 改名承接=同碼雙名依「只增不減」刻意並存):①EXCLUDE_SEGS +_superseded/_archive/_legacy;②種子改名承接律:
canonical 與 absorbed 檔名共享 MDL### 識別且一方為 ENG### 改名=REJECT(舊名留位,shim 會反向再造多頭)。
用法:python3 CGC_MDL132_VesBridge_v0103.py run [--root <VIA 相對子樹>] [--no-seed] [--single] [--workers N] [--langs py,ps1]
      | seed-only [--out <VES out>] | --selftest
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
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VES_DIR = VIA / "VIA_Reports" / "ves"
TAILS = VES_DIR / "tails_tree"
OUT = VES_DIR / "out"
DECISIONS = VES_DIR / "ves_decisions.jsonl"        # = OUT.parent(VES 上層目錄律)
VERSION_RX = re.compile(r"^(.*)_v(\d{4})\.(py|ps1|psm1|js|ts)$")
ARCHIVE_RX = re.compile(r"(_sha[0-9a-f]{8,}|\(\d+\))\.(py|ps1|psm1|js|ts)$")   # 上傳鏡像/瀏覽器複本=唯讀封存(MDL069 同律)
EXCLUDE_SEGS = {"__pycache__", ".git", ".venv", "venv", "node_modules", "output_hub", "VIA_Reports", "SCOPE_COPY",
                "VIA_RetiredEngines", "RetiredEngines", "_review_quarantine", "rollback", "回滾", "_bytecode_originals", "site-packages",
                "_superseded", "_archive", "_legacy", "_archive_uploads"}
LANG_EXT = {"py": (".py",), "ps1": (".ps1", ".psm1"), "js": (".js", ".ts")}

# VIA 動詞冊(V 級:VIA 律;能力軸=VES 九軸)
VIA_VERBS = {
    "lane": "READ", "fetch": "READ", "load": "READ", "read": "READ", "probe": "READ", "get": "READ", "scan": "READ", "inventory": "READ",
    "harvest": "READ", "collect": "READ", "resolve": "READ", "latest": "READ", "newest": "READ", "roster": "READ",
    "upsert": "WRITE", "write": "WRITE", "save": "WRITE", "export": "WRITE", "persist": "WRITE", "dump": "WRITE", "mirror": "WRITE",
    "parse": "PARSE", "decode": "PARSE", "extract": "PARSE", "tokenize": "PARSE",
    "classify": "TRANSFORM", "normalize": "TRANSFORM", "transform": "TRANSFORM", "convert": "TRANSFORM", "map": "TRANSFORM", "adapt": "TRANSFORM",
    "run": "COMPUTE", "build": "COMPUTE", "compute": "COMPUTE", "calc": "COMPUTE", "backfill": "COMPUTE", "main": "COMPUTE", "plan": "COMPUTE",
    "selftest": "VALIDATE", "chk": "VALIDATE", "check": "VALIDATE", "gate": "VALIDATE", "gate_open": "VALIDATE", "verify": "VALIDATE",
    "audit": "VALIDATE", "validate": "VALIDATE", "guard": "VALIDATE", "ensure": "VALIDATE",
    "merge": "MERGE", "union": "MERGE", "consolidate": "MERGE", "reconcile": "MERGE",
    "filter": "FILTER", "select": "FILTER", "pick": "FILTER",
    "status": "REPORT", "render": "REPORT", "digest": "REPORT", "report": "REPORT", "print": "REPORT", "page": "REPORT",
    "html": "REPORT", "lamps": "REPORT", "help": "REPORT", "progress": "REPORT", "narrate": "REPORT",
}
# 橋塊/樣板函式(各引擎自持=設計;吸收成 shim 會造跨引擎匯入=Hydra)
BRIDGE_FNS = {"_via_net", "_net_or_none", "_via_load", "_newest", "_latest", "_load", "_eng063", "_eng074", "gate_open", "chk",
              "progress_bar", "_num", "_iso_date", "_roc_ym", "_prev_ym", "_ctrlc_immune", "_child_kwargs", "_tail", "_exists",
              "_tasks", "_cmds", "_q", "_mod", "_sha", "_is_link", "write_parquet", "upsert", "_ensure_dirs", "_ensure_schema"}


def ves_path() -> Path | None:
    hits = sorted((VIA / "supportive modules" / "references" / "intake").glob("VIA_VES_EngineStandardizer_b*/via_engine_standardizer.py"))
    return hits[-1] if hits else None


# ---------------------------------------------------------------- ① 尾版鏡像
def _tail_map(files: list[Path]) -> set[Path]:
    best = {}
    for p in files:
        m = VERSION_RX.match(p.name)
        if not m:
            continue
        key = (p.parent, m.group(1), m.group(3))
        v = int(m.group(2))
        if key not in best or v > best[key][0]:
            best[key] = (v, p)
    return {p for _, p in best.values()}


def build_tails(root: Path, dst: Path, langs: list[str]) -> dict:
    exts = tuple(e for l in langs for e in LANG_EXT.get(l, ()))
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in exts
             and not any(seg in EXCLUDE_SEGS for seg in p.relative_to(root).parts)
             and not ("references" in p.parts and "intake" in p.parts)]
    archived = [p for p in files if ARCHIVE_RX.search(p.name)]
    files = [p for p in files if not ARCHIVE_RX.search(p.name)]
    tails = _tail_map(files)
    keep = [p for p in files if (not VERSION_RX.match(p.name)) or p in tails]
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)

    def cp(p: Path):
        q = dst / p.relative_to(root)
        q.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, q)
        return True
    if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "accel_map") and len(keep) > 1:
        res = VIA_ACCEL.accel_map(cp, keep, workers=8)
        n_ok = sum(1 for ok, _ in res if ok)
    else:
        n_ok = sum(1 for p in keep if cp(p))
    return {"discovered": len(files) + len(archived), "superseded": len(files) - len(keep), "archived": len(archived), "copied": n_ok, "dst": str(dst)}


# ---------------------------------------------------------------- ② 安全種子
def _fn_name(where: str) -> str:
    return where.rsplit(" ", 1)[-1].split(".")[-1].strip() if where else ""


MDL_RX = re.compile(r"MDL(\d{3})")
ENG_RX = re.compile(r"ENG\d{3}")


def _rename_lineage(canonical: str, absorbed: list) -> bool:
    """canonical 與所有 absorbed 檔名共享同一 MDL### 識別,且至少一方為 ENG### 改名承接=同碼雙名刻意並存"""
    files = [canonical.split(":")[0].split("/")[-1]] + [str(x).split(":")[0].split("/")[-1] for x in absorbed]
    ids = [set(MDL_RX.findall(f)) for f in files]
    if not files or not all(ids) or not set.intersection(*ids):
        return False
    return any(ENG_RX.search(f) for f in files) and any(not ENG_RX.search(f) for f in files)


def seed_decisions(cards: list[dict]) -> list[str]:
    """VIA 律可確定性判定的卡→token 行;其餘不動(留 AI)"""
    out = []
    for c in cards:
        cid, kind, ctx, opts = c.get("card", ""), c.get("kind", ""), c.get("context", {}) or {}, c.get("options", []) or []
        if kind == "VERB_CLASSIFY":
            verb = cid.replace("CARD-VERB-", "").lower()
            axis = VIA_VERBS.get(verb) or next((a for k, a in VIA_VERBS.items() if verb.startswith(k) or verb.endswith(k)), None)
            if axis and axis in opts:
                out.append(f"==VES-DECISION== {cid} {axis} V:VIA 動詞冊")
        elif kind == "ABSORB_CONFIRM":
            names = {_fn_name(ctx.get("canonical", ""))} | {_fn_name(x) for x in ctx.get("absorbed", [])}
            names.discard("")
            if names and names <= BRIDGE_FNS and "REJECT" in opts:
                out.append(f"==VES-DECISION== {cid} REJECT V:橋塊/樣板函式各引擎自持(NET/ACCEL-BRIDGE 設計);shim 轉發=跨引擎匯入 Hydra")
            elif "REJECT" in opts and _rename_lineage(ctx.get("canonical", ""), ctx.get("absorbed", [])):
                out.append(f"==VES-DECISION== {cid} REJECT V:整併改名承接(MDL###→ENG###)舊名依只增不減留位;shim 會反向再造多頭")
        elif kind == "CLUSTER_ACCEPT":
            mem = ctx.get("members", []) or []
            sigs = [str(m.get("sig", "")) for m in mem]
            if mem and all(s.startswith(("selftest(", "chk(")) for s in sigs) and "REJECT" in opts:
                out.append(f"==VES-DECISION== {cid} REJECT V:各引擎自測(selftest)為獨立設計,不合併")
    return out


def append_decisions(lines: list[str], path: Path = None) -> int:
    path = path or DECISIONS
    path.parent.mkdir(parents=True, exist_ok=True)
    have = set(path.read_text(encoding="utf-8", errors="ignore").splitlines()) if path.exists() else set()
    new = [l for l in lines if l not in have]
    if new:
        with path.open("a", encoding="utf-8") as f:
            f.write("\n".join(new) + "\n")
    return len(new)


def read_cards(out: Path) -> list[dict]:
    p = out / "ai_task_cards.jsonl"
    if not p.exists():
        return []
    rows = []
    for l in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(l))
        except Exception:
            continue
    return rows


def read_sandbox(out: Path) -> dict:
    p = out / "sandbox_report.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return {"verdict": d.get("verdict"), "hydra": (d.get("hydra") or {}).get("level"), "steps": d.get("steps"), "gates": d.get("gates")}
    except Exception:
        return {"verdict": "缺", "hydra": "缺"}


# ---------------------------------------------------------------- ③ 雙跑
def run_ves(ves: Path, root: Path, out: Path, workers: int, langs: str, log: Path) -> int:
    env = dict(os.environ, PYTHONUTF8="1", VIA_NO_OPEN="1")
    with log.open("a", encoding="utf-8") as lf:
        r = subprocess.run([sys.executable, str(ves), "--root", str(root), "--out", str(out), "--no-ml-probe", "--workers", str(workers),
                            "--langs", langs], stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env, cwd=str(VIA))
    return r.returncode


def run(args: list[str]) -> int:
    def opt(name, default=None):
        return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default
    ves = ves_path()
    if ves is None:
        print("[SKIP] VES 收容件缺(VIA_VES_EngineStandardizer_b*;先 via-reload)")
        return 3
    root = VIA / opt("--root", ".") if opt("--root") else VIA
    global TAILS, OUT
    if root != VIA:
        slug = re.sub(r"[^A-Za-z0-9]+", "_", str(root.relative_to(VIA))).strip("_")[:40]
        TAILS, OUT = VES_DIR / f"tails_{slug}", VES_DIR / f"out_{slug}"
    workers = int(opt("--workers", str(max(1, min(4, (os.cpu_count() or 2) - 1)))))
    langs = opt("--langs", "py,ps1")
    seed = "--no-seed" not in args
    single = "--single" in args
    VES_DIR.mkdir(parents=True, exist_ok=True)
    log = VES_DIR / f"ves_bridge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    t0 = time.time()
    print(f"=== VES 橋(MDL132)· root {root.relative_to(VIA) if root != VIA else 'VIA'} · 尾版鏡像 → 第 1 跑 → 安全種子 → 第 2 跑 ===", flush=True)
    m = build_tails(root, TAILS, langs.split(","))
    print(f"  [鏡像] 發現 {m['discovered']} · 史版排除 {m['superseded']} · 封存副本排除 {m['archived']} · 尾版複製 {m['copied']} → {TAILS.name}", flush=True)
    rc1 = run_ves(ves, TAILS, OUT, workers, langs, log)
    cards1 = read_cards(OUT)
    sb1 = read_sandbox(OUT)
    kinds = {}
    for c in cards1:
        kinds[c.get("kind")] = kinds.get(c.get("kind"), 0) + 1
    print(f"  [第1跑] rc={rc1} · 卡 {len(cards1)} {kinds} · 沙盤 {sb1.get('verdict')} · Hydra {sb1.get('hydra')} · {time.time() - t0:.0f}s", flush=True)
    if rc1 != 0 or not cards1:
        print(f"  [計] 第 1 跑 rc={rc1};卡 {len(cards1)};log {log.name}", flush=True)
        return 1 if rc1 else 0
    if not seed:
        print(f"  [計] --no-seed:卡留 AI;log {log.name}", flush=True)
        return 0
    lines = seed_decisions(cards1)
    n_new = append_decisions(lines)
    print(f"  [種子] 安全決策 {len(lines)} 行(新增 {n_new};V 級 VIA 律)→ {DECISIONS.relative_to(VIA)}", flush=True)
    if single:
        print(f"  [計] --single:留 AI 後續;log {log.name}", flush=True)
        return 0
    rc2 = run_ves(ves, TAILS, OUT, workers, langs, log)
    cards2 = read_cards(OUT)
    sb2 = read_sandbox(OUT)
    kinds2 = {}
    for c in cards2:
        kinds2[c.get("kind")] = kinds2.get(c.get("kind"), 0) + 1
    print(f"  [第2跑] rc={rc2} · 卡 {len(cards1)}→{len(cards2)} {kinds2} · 沙盤 {sb2.get('verdict')} · Hydra {sb2.get('hydra')}", flush=True)
    print(f"  [計] 種子 {len(lines)} · 卡 {len(cards1)}→{len(cards2)}(留 AI {len(cards2)})· 沙盤 {sb2.get('verdict')} · {time.time() - t0:.0f}s · 摘要 {OUT.relative_to(VIA)}/VES_SUMMARY.md · --apply 須操作員親打 token", flush=True)
    return 0 if rc2 == 0 else 1


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "tree"
        (root / "eng").mkdir(parents=True)
        for n in ("E_v0100.py", "E_v0101.py", "E_v0102.py", "plain.py", "S_v0100.ps1", "S_v0101.ps1", "plain_sha1234abcd.py", "plain (1).py"):
            (root / "eng" / n).write_text("def f():\n    return 1\n", encoding="utf-8")
        (root / "references" / "intake" / "x").mkdir(parents=True)
        (root / "references" / "intake" / "x" / "o.py").write_text("x=1", encoding="utf-8")
        (root / "eng" / "_superseded").mkdir()
        (root / "eng" / "_superseded" / "old.py").write_text("x=1", encoding="utf-8")
        (root / "VIA_RetiredEngines").mkdir()
        (root / "VIA_RetiredEngines" / "r.py").write_text("x=1", encoding="utf-8")
        m = build_tails(root, Path(td) / "tails", ["py", "ps1"])
        got = sorted(p.name for p in (Path(td) / "tails").rglob("*") if p.is_file())
        chk("① 尾版鏡像(同族只取最大版;無版號直通;intake/退役排除;_sha 鏡像/(n) 複本封存排除;零觸碰原樹)",
            got == ["E_v0102.py", "S_v0101.ps1", "plain.py"] and m["superseded"] == 3 and m["archived"] == 2 and (root / "eng" / "E_v0100.py").exists(), str(got))
        cards = [{"card": "CARD-VERB-lane", "kind": "VERB_CLASSIFY", "options": ["READ", "WRITE", "REPORT", "OTHER"]},
                 {"card": "CARD-VERB-zzz", "kind": "VERB_CLASSIFY", "options": ["READ", "OTHER"]},
                 {"card": "CARD-I001", "kind": "ABSORB_CONFIRM", "options": ["ACCEPT", "REJECT"], "context": {"canonical": "A.py:53 _via_net", "absorbed": ["B.py:51 _via_net"]}},
                 {"card": "CARD-I002", "kind": "ABSORB_CONFIRM", "options": ["ACCEPT", "REJECT"], "context": {"canonical": "A.py:1 load_prices", "absorbed": ["B.py:2 load_prices"]}},
                 {"card": "CARD-I003", "kind": "ABSORB_CONFIRM", "options": ["ACCEPT", "REJECT"], "context": {"canonical": "VRN_MDL005_OCRFetchingPDFText_v1.py:5 _jwrite", "absorbed": ["VRN_ENG018_MDL005OCRFetchingPDFText.py:6 _jwrite"]}},
                 {"card": "CARD-C001", "kind": "CLUSTER_ACCEPT", "options": ["ACCEPT", "REJECT"], "context": {"members": [{"sig": "selftest()"}, {"sig": "selftest()"}]}},
                 {"card": "CARD-RISK-FN-1", "kind": "RISK_CONFIRM", "options": ["TRUE", "FALSE_POSITIVE"]}]
        lines = seed_decisions(cards)
        chk("② 安全種子(動詞冊 lane→READ;未知動詞不猜;橋塊 _via_net→REJECT;一般多頭留 AI;改名承接 MDL005↔ENG018→REJECT;selftest 群→REJECT;RISK 留 AI)",
            len(lines) == 4 and lines[0].startswith("==VES-DECISION== CARD-VERB-lane READ") and "CARD-I001 REJECT" in lines[1] and "CARD-I003 REJECT" in lines[2] and "CARD-C001 REJECT" in lines[3]
            and all(re.match(r"==VES-DECISION==\s+\S+\s+\S+", l) for l in lines), str(lines)[:120])
        dp = Path(td) / "ves_decisions.jsonl"
        n1 = append_decisions(lines, dp)
        n2 = append_decisions(lines, dp)
        chk("③ append-only 冪等(重複行不再追加;舊行不改)", n1 == 4 and n2 == 0 and len(dp.read_text(encoding="utf-8").splitlines()) == 4)
    chk("④ VES 收容件在位或誠實 SKIP", ves_path() is None or ves_path().exists())
    chk("⑤ 決策檔位置=VES 上層目錄律(out.parent)", DECISIONS.parent == OUT.parent)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 紀律宣告(零觸碰原樹/--apply 不經本橋/不建議刪除/Hydra 不自降/V 級註記)",
        all(k in src for k in ("零觸碰原樹", "--apply 永不經本橋", "不建議刪除", "Hydra 不自降", "V:VIA 動詞冊")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== VES 橋(CGC_MDL132 v0103)· 六檢自測 ===")
        return selftest()
    if a and a[0] == "seed-only":
        out = Path(a[a.index("--out") + 1]) if "--out" in a else OUT
        lines = seed_decisions(read_cards(out))
        n = append_decisions(lines, out.parent / "ves_decisions.jsonl")
        print(f"  [種子] {len(lines)} 行(新增 {n})→ {out.parent / 'ves_decisions.jsonl'}")
        return 0
    if not a or a[0] == "run" or a[0].startswith("--"):
        return run([x for x in a if x != "run"])
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
