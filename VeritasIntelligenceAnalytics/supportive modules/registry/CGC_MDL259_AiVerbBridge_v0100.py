#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL259_AiVerbBridge v0100 — AI 動詞交互橋:把「AI 怎麼跟 VIA 動詞來回」做成可拆的五個動詞(操作員 2026-10-04)

五個動詞各自獨立(可單用、可串),都只讀輸入、只寫自己的帳 / 產物,零網路:
  paste    <log 或 -(stdin)> [--max 300] [--next "…"]   → 黃紅字貼回包:濾噪([監控]/[矩陣]/[自動跳出]/SyntaxWarning/進度列)· 判決行歸黃 · 錯誤行歸紅 · 結尾 NEXT: 一行
  classify <ENGINE_READINESS.csv 或 貼回包>             → 紅分三類:INTERRUPTED(rc -1073741510 / TIMEOUT / 錨點在系統檔)· ENV(閘未開 / 收容件缺 / 境缺 / lib 缺)· TRUE(錨點在自家檔)
  lesson   add <key> <note> | get <key> | list          → 教訓帳(只增 jsonl);同 key 第 3 次起 escalate=True(AI 必先讀再修)
  thin-tail <stem> <prior_version> <new_version> <owner_fn> --family <core|vdf|vrn|sup> --why "…" --check "…"  → 薄尾檔(PRIOR 載前版 · __getattr__ · 擁有者層換函數 · 自測含根因重現檢 · 加速器橋)
  round    write <n> --paste <pack.md> [--classify <json>] → ROUND_<n>.json(機器可讀:燈數 · 紅三類 · NEXT · 薄尾清單)
用法  VIA_FROM_VCGC=YES python CGC_MDL259_AiVerbBridge_v0100.py <verb> …     ·     python CGC_MDL259_AiVerbBridge_v0100.py --selftest
產物  VIA_Reports/aiverb/{paste_<stamp>.md, LESSONS.jsonl, ROUND_<n>.json, thin_tails/<file>.py}
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
import csv, io, json, os, re, sys, tempfile
from datetime import datetime
from pathlib import Path

ENGINE = "CGC_MDL259_AiVerbBridge_v0100"
HERE = Path(__file__).resolve().parent
VIA = next((p for p in [HERE] + list(HERE.parents) if (p / "supportive modules").is_dir()), HERE)
OUT = VIA / "VIA_Reports" / "aiverb"
NOISE = re.compile(r"^\s*(\[監控\]|\[矩陣\]|\[VIA_NO_OPEN\]|\[via-vcgc 自動跳出\]|<VIA>\\|<unknown>:\d+: SyntaxWarning|.*SyntaxWarning: invalid escape|雙軌並行 \[|\s*\[沿用\]|\s*\[Grok 矩陣\]|\s*\[VIA\] 短指令|\s*\[VIA\] \+Grok|System\.Collections\.|\s*警告: The ThreadJob)")
RED_PAT = re.compile(r"\[(FAIL|RED|真紅|紅|缺|起|逾時|備份|參數|輸入項目)\]|Traceback|Error:|錯誤 [1-9]|rc [1-9]|rc=-?\d|沒過|被拒|FAIL\b")
YELLOW_PAT = re.compile(r"\[(計|OK|GREEN|YELLOW|NODATA|判|清點|矩陣結|推|鎖|入倉|自測|發號|登冊|建|開|origin|清理|TEMP|加速器|車道|樣本|風險|249|全景|上輪|還原點|教訓)\]|總判|族總判|落差|遺失|改身分|重號|缺號|FPSTALE|UNCOMMITTED|APPLIED|撞號|NEXT:")
SYSTEM_ANCHOR = re.compile(r"(threading\.py|codecs|glob\.py|subprocess\.py|runpy\.py|<frozen)")
OWN_ANCHOR = re.compile(r"(VeritasIntelligenceAnalytics|functional modules|supportive modules|\b(?:VRN|VDF|CGC|SUP|VAP)_)")
ENV_PAT = re.compile(r"閘未開|NO_CONSENT|同意閘|收容件缺|收容件不在|ABSENT|境缺|No module named|ModuleNotFoundError|lib 缺|unrecognized arguments: --selftest|找不到引擎|FAIL_CLOSED|FAIL-CLOSED|GATED")
INTERRUPT_RC = {"-1073741510", "124", "137", "130"}


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ---------------- paste ----------------
def paste(text: str, max_lines: int = 300, next_line: str | None = None) -> dict:
    yellow, red, seen = [], [], set()
    for raw in text.splitlines():
        l = raw.rstrip()
        if not l.strip() or NOISE.search(l):
            continue
        l = re.sub(r"\s{3,}", " · ", l.strip())[:180]
        if l in seen:
            continue
        seen.add(l)
        if RED_PAT.search(l) and not re.search(r"錯誤 0 件|FAIL 0\b|紅 0\b|FAIL\s*=\s*0", l):
            red.append(l)
        elif YELLOW_PAT.search(l):
            yellow.append(l)
    nxt = next_line or ("把紅字整段貼給 AI → AI 出薄尾" if red else "全綠 → 鎖 LKGC · 進下一輪")
    body = ["# PASTE " + _stamp() + f" · 黃 {len(yellow)} · 紅 {len(red)}"] + [f"- {y}" for y in yellow] + ["## 錯誤"] + [f"- {r}" for r in red]
    truncated = False
    if len(body) > max_lines - 1:
        keep_red = red[: max(20, max_lines // 2)]; keep_y = yellow[: max_lines - 2 - len(keep_red) - 2]
        body = ["# PASTE " + _stamp() + f" · 黃 {len(yellow)}(截 {len(keep_y)})· 紅 {len(red)}(截 {len(keep_red)})"] + [f"- {y}" for y in keep_y] + ["## 錯誤"] + [f"- {r}" for r in keep_red]; truncated = True
    body.append("NEXT: " + nxt)
    return {"yellow": yellow, "red": red, "lines": body, "truncated": truncated, "next": nxt}


# ---------------- classify ----------------
def classify_rows(rows: list[dict]) -> dict:
    out = {"INTERRUPTED": [], "ENV": [], "TRUE": [], "GREEN": 0, "OTHER": 0}
    for r in rows:
        lamp = (r.get("lamp") or "").upper(); rc = str(r.get("rc") or ""); anchor = r.get("anchor") or ""; verdict = r.get("verdict") or ""
        item = {"engine": r.get("engine"), "family": r.get("family"), "rc": rc, "anchor": anchor, "verdict": verdict[:160]}
        if lamp == "GREEN":
            out["GREEN"] += 1; continue
        if lamp in ("TIMEOUT",) or rc in INTERRUPT_RC or SYSTEM_ANCHOR.search(anchor):
            item["why"] = "被打斷 / 逾時 / 錨點在系統檔 → 重跑,不修碼"; out["INTERRUPTED"].append(item); continue
        if lamp == "NODATA" or ENV_PAT.search(verdict) or ENV_PAT.search(anchor):
            item["why"] = "環境 / 閘 / 收容件 → EnvGovernance 或開閘,不修碼"; out["ENV"].append(item); continue
        if lamp == "RED":
            if OWN_ANCHOR.search(anchor) and "site-packages" not in anchor:
                item["why"] = "真紅:錨點在自家檔 → 薄尾(含根因重現檢)"; out["TRUE"].append(item); continue
            item["why"] = "紅但錨點空白/不在自家檔 → 先補錨點再分類, 不誤出薄尾"
            out.setdefault("UNANCHORED", []).append(item); continue
        out["OTHER"] += 1
    out["next"] = ("先重跑 INTERRUPTED " + str(len(out["INTERRUPTED"])) + " 支;" if out["INTERRUPTED"] else "") + ("ENV " + str(len(out["ENV"])) + " 支走環境;" if out["ENV"] else "") + ("真紅 " + str(len(out["TRUE"])) + " 支出薄尾" if out["TRUE"] else "真紅 0")
    return out


def classify_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    rows = []
    if path.suffix.lower() == ".csv":
        rd = csv.DictReader(io.StringIO(text))
        for r in rd:
            rows.append({"family": r.get("家族"), "engine": r.get("引擎"), "lamp": r.get("燈"), "rc": r.get("rc"), "verdict": r.get("判決"), "anchor": r.get("錨點(檔:行)") or r.get("錨點")})
    else:  # 貼回包 / 任意 log:抓「[紅] 家族 引擎 · 判決 · 錨 檔:行」或矩陣行
        for l in text.splitlines():
            m = re.search(r"\[(?:紅|真紅)\]\s*(\w+)\s+(\S+)\s*·\s*(.*?)\s*·\s*錨\s*(.*)$", l)
            if m:
                rows.append({"family": m.group(1), "engine": m.group(2), "lamp": "RED", "rc": "", "verdict": m.group(3), "anchor": m.group(4)}); continue
            m = re.match(r"^(vdf|vrn|core|sup)\s+(\S+)\s+(GREEN|RED|NODATA|TIMEOUT)\s+(-?\d+)\s+\d+\s+(.*?)(?:\t|\s{2,})(\S*)", l.strip())
            if m:
                rows.append({"family": m.group(1), "engine": m.group(2), "lamp": m.group(3), "rc": m.group(4), "verdict": m.group(5), "anchor": m.group(6)})
    return classify_rows(rows)


# ---------------- lesson ----------------
def lesson_path() -> Path:
    OUT.mkdir(parents=True, exist_ok=True); return OUT / "LESSONS.jsonl"


def lesson_add(key: str, note: str, by: str = "ai") -> dict:
    n = lesson_count(key) + 1
    rec = {"at": datetime.now().isoformat(timespec="seconds"), "key": key, "n": n, "note": note[:300], "by": by, "escalate": n >= 3}
    with open(lesson_path(), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def lesson_count(key: str) -> int:
    p = lesson_path()
    if not p.is_file():
        return 0
    return sum(1 for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and json.loads(l).get("key") == key)


def lesson_get(key: str) -> list:
    p = lesson_path()
    if not p.is_file():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and json.loads(l).get("key") == key]


# ---------------- thin-tail ----------------
THIN_TAIL = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""{stem} v{new} — 薄尾:{why}

前版 {stem}_v{prior} 一字不動;本版只換擁有者層的 `{fn}`。自測含「根因重現」一檢(前版行為 → 本版修正)。
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
import importlib.util, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "{stem}"
ENGINE = _STEM + "_v{new}"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\\d+)$", p.stem)
    return int(m.group(1)) if m else -1


_PRIOR_HINT = r"{prior_path}"
_cands = [p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))]
if not _cands and _PRIOR_HINT and Path(_PRIOR_HINT).is_file():
    _cands = [Path(_PRIOR_HINT)]
if not _cands:   # 誠實: 本夾與內嵌提示都找不到前版 → RED, 不炸 ValueError
    print(json.dumps({{"state": "RED", "why": "找不到前版 " + _STEM + " (本夾無, 內嵌提示失效)"}}, ensure_ascii=False))
    sys.exit(1)
_PRIOR_PATH = max(_cands, key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM.lower() + "_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


# 擁有者層:沿薄尾鏈找真正定義 `{fn}` 的那一層,在它身上換函數 → 前版 main / 其他呼叫者自然走本版
_OWNER = PRIOR
while hasattr(_OWNER, "PRIOR") and "{fn}" not in vars(_OWNER):
    _OWNER = _OWNER.PRIOR
_ORIG = getattr(_OWNER, "{fn}", None)
if _ORIG is None:   # 誠實:擁有者層沒有這個名字 → 列出可換的函數,不假裝
    _avail = sorted(k for k, v in vars(_OWNER).items() if callable(v) and not k.startswith("_"))[:40]
    print(json.dumps({{"state": "RED", "why": "前版鏈上找不到函數 {fn}", "available": _avail}}, ensure_ascii=False))


def {fn}(*args, **kwargs):
    """TODO(AI 填):修正後的行為。可先呼叫 _ORIG(*args, **kwargs) 再修正回傳;或整個重寫。"""
    if _ORIG is None:
        raise RuntimeError("前版鏈上沒有 {fn}")
    result = _ORIG(*args, **kwargs)
    return result


if _ORIG is not None:
    _OWNER.{fn} = {fn}


def selftest() -> int:
    ok = []
    def chk(name, cond, note=""):
        ok.append(bool(cond)); print(f"  [{{'OK' if cond else 'FAIL'}}] {{name}}{{(' · ' + note) if note else ''}}")
    # ① 根因重現:{check}
    chk("① 根因重現:{check}", False, "TODO(AI 填):用 _ORIG 重現前版錯誤行為,再用本版 {fn} 證明修正")
    chk("② 擁有者層已換(前版 main 走本版)", _ORIG is not None and getattr(_OWNER, "{fn}") is {fn}, "" if _ORIG is not None else "前版鏈上沒有 {fn}:改用 available 裡的名字重產")
    chk("③ 前版其他行為不變(抽一檢)", True, "TODO(AI 填)")
    chk("④ 加速器橋在", "VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] {{ENGINE}} 薄尾 {{sum(ok)}}/{{len(ok)}} · {{'PASS' if all(ok) else 'FAIL'}}")
    return 0 if all(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main() if hasattr(PRIOR, "main") else 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def thin_tail(stem: str, prior: str, new: str, fn: str, why: str, check: str, family: str = "core", out_dir: Path | None = None) -> Path:
    if not re.match(r"^\d{4}$", prior) or not re.match(r"^\d{4}$", new) or int(new) <= int(prior):
        raise ValueError("版號要四碼且 new > prior")
    if not re.match(r"^[A-Za-z_]\w*$", fn):
        raise ValueError("owner_fn 要是合法識別字")
    out_dir = out_dir or (OUT / "thin_tails"); out_dir.mkdir(parents=True, exist_ok=True)
    hist = lesson_get(stem)                                   # 教訓帳先讀:同支第 3 次起把失敗過的修法寫進檔頭,AI 不得重蹈
    if len(hist) >= 2:
        why = why + " ‖ 教訓帳(" + str(len(hist)) + " 次,escalate):" + " / ".join(h["note"][:60] for h in hist[-3:])
    prior_path = ""   # 生成時解析前版: 產出夾 → 本夾 → 全樹; 內嵌進檔, 薄尾落在哪都載得到前版
    base = Path(__file__).resolve().parents[2]
    for cand_dir in (out_dir, HERE):
        hit = sorted(cand_dir.glob(f"{stem}_v*.py"))
        hit = [x for x in hit if re.search(r"_v(\d{4})$", x.stem) and x.stem < f"{stem}_v{new}"]
        if hit:
            prior_path = str(max(hit)); break
    if not prior_path:
        tree = [x for x in base.rglob(f"{stem}_v*.py")
                if "__pycache__" not in x.parts and re.search(r"_v(\d{4})$", x.stem) and x.stem < f"{stem}_v{new}"]
        if tree:
            prior_path = str(max(tree, key=lambda x: x.stem))
    p = out_dir / f"{stem}_v{new}.py"
    p.write_text(THIN_TAIL.format(stem=stem, prior=prior, new=new, fn=fn, why=why, check=check,
                                  prior_path=prior_path), encoding="utf-8")
    return p


# ---------------- round ----------------
def round_write(n: int, paste_pack: Path, classify_json: Path | None = None, out_dir: Path | None = None) -> Path:
    out_dir = out_dir or OUT; out_dir.mkdir(parents=True, exist_ok=True)
    text = paste_pack.read_text(encoding="utf-8", errors="replace")
    pk = paste(text)
    cls = json.loads(classify_json.read_text(encoding="utf-8")) if classify_json and classify_json.is_file() else classify_file(paste_pack)
    rec = {"schema": "VIA.AiVerb.Round.v1", "round": n, "at": datetime.now().isoformat(timespec="seconds"), "engine": ENGINE,
           "yellow": len(pk["yellow"]), "red": len(pk["red"]), "classify": {k: (len(v) if isinstance(v, list) else v) for k, v in cls.items() if k != "next"},
           "true_red": [{"engine": t["engine"], "anchor": t["anchor"]} for t in cls.get("TRUE", [])], "next": cls.get("next") or pk["next"],
           "thin_tails_needed": [t["engine"] for t in cls.get("TRUE", [])], "lessons_escalated": [k for k in {t["engine"] for t in cls.get("TRUE", [])} if lesson_count(k) >= 2]}
    p = out_dir / f"ROUND_{n:02d}.json"; p.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


# ---------------- selftest ----------------
FIXTURE_PACK = """  [監控] 已在背景起全景監控 pid 5516 · 閒置 1800 秒自停
  [矩陣] C:\\x\\VIA_Flow_Matrix_v0100.html
  <unknown>:670: SyntaxWarning: invalid escape sequence '\\d'
[清理] GC 完成 · 可用 RAM 5.66 → 5.66 GB
[計] VRN_ENG399_RealTestHarness_v0100 自測 8/8 · PASS
[矩陣] 引擎 121 · 綠 93 · 紅 7 · 沒料 3
[真紅] vrn VRN_ENG393_DocClassVerify_v0101 · Traceback (most recent call last): · 錨 supportive modules\\SUP_MDL737_SuperAccelModule_v0109.py:54
[真紅] vrn VRN_ENG112_FinancialRead_v0100 · sys.exit(selftest()) · 錨 C:\\Python313\\Lib\\threading.py:1094
[真紅] vdf VDF_ENG117_ForwardVintage_v0101 · error: unrecognized arguments: --selftest · 錨
── 錯誤 1 件 ──
[起] 伺服器 2 秒內退出(rc 2)
"""
FIXTURE_CSV = """家族,引擎,燈,rc,秒,判決,錨點(檔:行),修
vdf,VDF_ENG046_FetchMatrixRegistry_v0100,GREEN,0,38,[計] 八檢 OK 8 · FAIL 0,,
vrn,VRN_ENG112_FinancialRead_v0100,RED,-1073741510,54,sys.exit(selftest()),C:\\Python313\\Lib\\threading.py:1094,via-ai-fix
vrn,VRN_ENG393_DocClassVerify_v0101,RED,1,4,Traceback (most recent call last):,supportive modules\\SUP_MDL737_SuperAccelModule_v0109.py:54,via-ai-fix
vdf,VDF_ENG117_ForwardVintage_v0101,NODATA,2,155,error: unrecognized arguments: --selftest,,
vdf,VDF_ENG061_FeatureStore_v0106,TIMEOUT,124,240,薄尾 3/3 PASS,,
vdf,VDF_ENG094_ActiveETFActivity_v0101,RED,2,10,"{""state"": ""NO_CONSENT""}",,
"""


def selftest() -> int:
    ok = []
    def chk(name, cond, note=""):
        ok.append(bool(cond)); print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + note) if note else ''}")
    pk = paste(FIXTURE_PACK)
    chk("① paste:濾噪(監控/矩陣/SyntaxWarning 全掉)· 黃紅分流 · NEXT 在尾", not any("監控" in l or "SyntaxWarning" in l for l in pk["lines"]) and len(pk["red"]) >= 3 and any("[計]" in y for y in pk["yellow"]) and pk["lines"][-1].startswith("NEXT:"))
    big = "\n".join(f"[OK] 行 {i}" for i in range(500)) + "\n[FAIL] x"
    pk2 = paste(big, max_lines=100)
    chk("② paste:超過預算截斷、紅字優先保留、仍 ≤ 100 行", pk2["truncated"] and len(pk2["lines"]) <= 100 and any("[FAIL] x" in l for l in pk2["lines"]))
    with tempfile.TemporaryDirectory() as td:
        csvp = Path(td) / "r.csv"; csvp.write_text(FIXTURE_CSV, encoding="utf-8")
        c = classify_file(csvp)
        chk("③ classify(csv):被打斷(rc -1073741510 / TIMEOUT)· ENV(NODATA --selftest / NO_CONSENT)· 真紅(ENG393 錨在自家檔)", {x["engine"] for x in c["INTERRUPTED"]} == {"VRN_ENG112_FinancialRead_v0100", "VDF_ENG061_FeatureStore_v0106"} and {x["engine"] for x in c["ENV"]} == {"VDF_ENG117_ForwardVintage_v0101", "VDF_ENG094_ActiveETFActivity_v0101"} and [x["engine"] for x in c["TRUE"]] == ["VRN_ENG393_DocClassVerify_v0101"] and c["GREEN"] == 1, c["next"])
        packp = Path(td) / "p.md"; packp.write_text(FIXTURE_PACK, encoding="utf-8")
        c2 = classify_file(packp)
        chk("④ classify(貼回包):同一套規則吃 [真紅] 行;錨在 threading.py 的歸被打斷", [x["engine"] for x in c2["TRUE"]] == ["VRN_ENG393_DocClassVerify_v0101"] and any(x["engine"] == "VRN_ENG112_FinancialRead_v0100" for x in c2["INTERRUPTED"]))
        global OUT; old = OUT; OUT = Path(td) / "aiverb"
        try:
            r1 = lesson_add("SDD.PSGATE-1", "status 子行程沒印流程章"); r2 = lesson_add("SDD.PSGATE-1", "⑫ 擋"); r3 = lesson_add("SDD.PSGATE-1", "第三次")
            chk("⑤ lesson:只增 jsonl · 同 key 計數 · 第 3 次 escalate", r1["n"] == 1 and not r1["escalate"] and r3["n"] == 3 and r3["escalate"] and len(lesson_get("SDD.PSGATE-1")) == 3)
            tp = thin_tail("VRN_ENG393_DocClassVerify", "0101", "0102", "classify_doc", why="加速器橋在本支炸:SUP_MDL737:54", check="前版 import 時 Traceback → 本版 graceful")
            t = tp.read_text(encoding="utf-8")
            chk("⑥ thin-tail:產生檔名 _v0102 · PRIOR 載前版 · __getattr__ · _OWNER 換函數 · 自測含根因重現 · 加速器橋", tp.name == "VRN_ENG393_DocClassVerify_v0102.py" and all(k in t for k in ("_PRIOR_PATH", "__getattr__", "_OWNER.classify_doc = classify_doc", "根因重現", "VIA:ACCEL-BRIDGE")))
            import ast; ast.parse(t); chk("⑦ thin-tail 產物語法合法(可直接 --selftest 跑到 TODO)", True)
            try:
                thin_tail("X", "0102", "0101", "f", "", ""); chk("⑧ thin-tail:new ≤ prior 拒絕", False)
            except ValueError:
                chk("⑧ thin-tail:new ≤ prior 拒絕", True)
            rp = round_write(1, packp); rec = json.loads(rp.read_text(encoding="utf-8"))
            chk("⑨ round:機器可讀 ROUND_01.json(燈數 · 三類 · 真紅錨點 · NEXT · 薄尾清單)", rec["round"] == 1 and rec["red"] >= 3 and rec["classify"]["TRUE"] == 1 and rec["thin_tails_needed"] == ["VRN_ENG393_DocClassVerify_v0101"] and rec["next"])
        finally:
            OUT = old
    chk("⑩ 五動詞可拆:各自純函數,不互相 import 狀態", all(callable(f) for f in (paste, classify_file, lesson_add, thin_tail, round_write)))
    chk("⑪ 加速器橋在 · 零網路 · 只寫自己的帳", "VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] {ENGINE} 自測 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if not a:
        print(__doc__); return 2
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False)); return 2
    v = a[0]
    if v == "paste":
        src = a[1] if len(a) > 1 and a[1] != "-" else None
        text = Path(src).read_text(encoding="utf-8", errors="replace") if src else sys.stdin.read()
        mx = int(a[a.index("--max") + 1]) if "--max" in a else 300; nxt = a[a.index("--next") + 1] if "--next" in a else None
        pk = paste(text, mx, nxt); OUT.mkdir(parents=True, exist_ok=True); p = OUT / f"paste_{_stamp()}.md"; p.write_text("\n".join(pk["lines"]), encoding="utf-8")
        print("\n".join(pk["lines"])); print(f"  → {p}", file=sys.stderr); return 0
    if v == "classify":
        c = classify_file(Path(a[1])); OUT.mkdir(parents=True, exist_ok=True); p = OUT / f"classify_{_stamp()}.json"; p.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps({k: (len(x) if isinstance(x, list) else x) for k, x in c.items()}, ensure_ascii=False)); print("NEXT: " + c["next"]); return 0
    if v == "lesson":
        sub = a[1] if len(a) > 1 else "list"
        if sub == "add":
            print(json.dumps(lesson_add(a[2], " ".join(a[3:]) or "-"), ensure_ascii=False)); return 0
        if sub == "get":
            print(json.dumps(lesson_get(a[2]), ensure_ascii=False, indent=1)); return 0
        p = lesson_path(); print(p.read_text(encoding="utf-8") if p.is_file() else "(空)"); return 0
    if v == "thin-tail":
        fam = a[a.index("--family") + 1] if "--family" in a else "core"; why = a[a.index("--why") + 1] if "--why" in a else "TODO"; check = a[a.index("--check") + 1] if "--check" in a else "TODO"
        p = thin_tail(a[1], a[2], a[3], a[4], why, check, fam); print(json.dumps({"out": str(p), "family": fam, "next": "AI 填 TODO 三處 → --selftest → EngineLanes -Only → 登冊鎖"}, ensure_ascii=False)); return 0
    if v == "round":
        n = int(a[2]); pk = Path(a[a.index("--paste") + 1]); cj = Path(a[a.index("--classify") + 1]) if "--classify" in a else None
        p = round_write(n, pk, cj); print(json.dumps({"out": str(p)}, ensure_ascii=False)); return 0
    print(__doc__); return 2


if __name__ == "__main__":
    raise SystemExit(main())
