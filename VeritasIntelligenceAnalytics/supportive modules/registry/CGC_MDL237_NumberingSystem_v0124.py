#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL237_NumberingSystem v0124 — 薄尾(v0100–v0123 一字不動):需求 / 工作流 / 步的號 = 冊上代碼;已裁定的錯位照對齊帳改正

操作員 2026-11-27 裁定「對齊正確號」(VCGC-REQ277)。背景:v0104 起 WKF / STP / REQ 的號照冊上順序發,
冊上代碼不連續或兩條線同時取號就會錯位(v0104 的處理是標 RED、不改任何一邊)。11-25 起 REQ 冊有 14 條錯位:
VCGC-REQ262~264 三條互相錯開;VDF-REQ052~062 十一條都往前移 6 號(VDF-REQ046~051 跳號)。這 14 個號只出現在編號冊,倉內沒有別的檔引用。
本版三件事:
  ① 第一次發號就用冊上代碼:WKF / STP / REQ 的新列,號 = "VIA-" + 冊上代碼(那個號沒被別的活列佔用時);不再靠順序碰運氣。
  ② 已發出的錯位列,只有對齊帳 VIA_Numbering_Realign_Ledger_v0100.jsonl 上有的才改(鍵 + 舊號都要對得上):
     號改成冊上代碼,列上留 realigned_from = 舊號;帳是只增的歷史(鍵 · 舊號 · 新號 · 裁定 · 時間)。帳上沒有的錯位照舊 RED,要裁定才動。
     這一步只走專用動詞 realign --apply [--scope 檔…]:一般的 --apply --scope(只登本批)是照「號」合併的,
     舊列換號在那條路上會變成「新號一列、舊號一列」兩列並存(2026-11-27 容器實錄,已還原)。所以一般發號只對齊新列。
     realign --apply:先留底 → 直接改寫錯位列 → 再跑一次只登本批(補保留列等新列)→ 用 ③ 對留底比;遺失 / 改身分 / 重號任一不是 0 就整批還原。
  ③ audit 的「改身分」不計對齊帳上的那幾個號(另報 realigned 數);遺失 · 重號照舊,一個都不放。
不改需求冊 / 工作流冊。零網路。不用 TA-Lib。
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


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "CGC_MDL237_NumberingSystem"
ENGINE = _STEM + "_v0124"
DECLARED_KINDS = ("WKF", "STP", "REQ")
LEDGER_NAME = "VIA_Numbering_Realign_Ledger_v0100.jsonl"
LEDGER = HERE / LEDGER_NAME


def _vnum_v0124(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load_v0124(path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0124(p) < _vnum_v0124(__file__)), key=_vnum_v0124)
PRIOR = _load_v0124(PRIOR_PATH, _STEM + "_prior_for_" + ENGINE)        # v0123
BASE = PRIOR.BASE
BASE.ENGINE = ENGINE


def _chain():
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        yield m
        m = vars(m).get("PRIOR") or vars(m).get("_PRIOR")


def _defined_in(m, name: str) -> bool:
    """name 是不是「定義」在 m 這一層(函式自己的全域就是 m 的全域)。後面的薄尾常把前版的名字重新綁進自己的命名空間,
    只看名字在不在會找錯層:掛鉤掛在轉手的那一層,真正執行的那一層看不到(2026-11-27 容器實錄:稽核照舊報改身分 14,整批還原)。"""
    fn = vars(m).get(name)
    return getattr(fn, "__globals__", None) is vars(m)


AUDIT_HOME = next(m for m in _chain() if _defined_in(m, "compare") and _defined_in(m, "audit"))      # 定義 audit 與它叫的 compare 的那一層(v0108)
SCOPE_HOME = next(m for m in _chain() if _defined_in(m, "merge_scoped") and _defined_in(m, "_write_state"))   # 定義只登本批的那一層(v0109)
_PRIOR_ASSIGN = BASE.assign
_PRIOR_COMPARE = AUDIT_HOME.compare


def __getattr__(name):
    return getattr(PRIOR, name)


def load_ledger(path=None) -> list:
    p = Path(path) if path else LEDGER
    if not p.is_file():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _plain_lamp(row: dict) -> tuple:
    """錯位標記拿掉之後,列回到 v0104 原本給的燈與註(REQ 看狀態;WKF / STP 綠)。"""
    if row.get("kind") == "REQ":
        status = str(row.get("cat") or "").split("/", 1)[-1] if "/" in str(row.get("cat") or "") else ""
        return ("GREEN" if status == "COVERED" else "AMBER"), status
    return "GREEN", ""


def realign(state: dict, ledger: list, fresh: set) -> dict:
    """把 WKF / STP / REQ 的號對到冊上代碼。fresh = 這一輪才第一次出現的 (kind, key);ledger = 已裁定可改的舊列。
    兩種列會動:fresh 的新列(第一次發號)、對齊帳上鍵與舊號都對得上的舊列。其他錯位不動(照舊 RED)。
    動之前先算完整張對照,任何一個目標號會撞到「不動的活列」就整批不動那一個,不製造重號。"""
    rows = state["rows"]
    allow = {(e.get("kind"), e.get("key"), e.get("from")) for e in ledger}
    move = {}
    for (kind, key), r in rows.items():
        if kind not in DECLARED_KINDS or not r.get("declared") or r.get("gone_since"):
            continue
        want = "VIA-" + r["declared"]
        if r.get("code") == want:
            continue
        if (kind, key) in fresh or (kind, key, r.get("code")) in allow:
            move[(kind, key)] = want
    # 先把「誰真的能動」算到不再變,才動任何一列:被擋下的列留在原號,那個號就還有人佔著,
    # 想搬進去的列也要跟著擋(PR #770 Codex P2:只算一輪會讓另一列搬進被擋列的原號 → 重號)。
    blocked = []
    while True:
        held = {r.get("code") for k, r in rows.items() if k not in move and not r.get("gone_since")}
        wants = {}
        for k, want in move.items():
            wants.setdefault(want, []).append(k)
        stuck = sorted(k for k, want in move.items() if want in held or len(wants[want]) > 1)
        if not stuck:
            break
        for k in stuck:
            blocked.append((k[0], k[1], rows[k].get("code"), move.pop(k)))
    done = []
    for k, want in sorted(move.items()):
        r = rows[k]
        old = r["code"]
        r["code"] = want
        if isinstance(r.get("full"), str) and r["full"].startswith(old):
            r["full"] = want + r["full"][len(old):]
        if k not in fresh:
            r["realigned_from"] = old
        r["lamp"], r["note"] = _plain_lamp(r)
        done.append((k[0], k[1], old, want))
    return {"done": done, "blocked": blocked}


def assign(items: list, state: dict) -> dict:
    before = set(state["rows"])
    state = _PRIOR_ASSIGN(items, state)
    res = realign(state, [], set(state["rows"]) - before)        # 一般發號只對齊新列;舊列換號只走 realign --apply
    state["_realign"] = res
    return state


def _declared_of(key) -> str:
    """鍵裡的冊上代碼:req|VDF-REQ052@v0100 → VDF-REQ052。"""
    return str(key or "").split("|", 1)[-1].split("@", 1)[0]


def compare(before: dict, after: dict) -> dict:
    """前版的只增比對,再把「對齊帳准許的那一步」從改身分拿掉(另列 realigned)。遺失 · 重號原樣。
    准許的只有一種:這個號原本在帳上那一列(種類 · 鍵 · 舊號全對)手上,現在落在冊上代碼就是它的那一列手上。
    號在帳上但換給別的列、或原主不是帳上那一列,都照舊算改身分(PR #770 Codex P1:原判法只看號與鍵有沒有出現在帳上,
    合併後把已對齊的號改給不相干的需求也會被放行)。"""
    rep = _PRIOR_COMPARE(before, after)
    left = {(e.get("kind"), e.get("key"), e.get("from")) for e in load_ledger()}     # 帳上准許的「這一列離開這個號」
    b, a = before["codes"], after["codes"]
    sanctioned = [c for c in rep["changed_identity"]
                  if (b[c][0], b[c][1], c) in left and a[c][0] == b[c][0] and _declared_of(a[c][1]) == c[len("VIA-"):]]
    rep["changed_identity"] = [c for c in rep["changed_identity"] if c not in sanctioned]
    rep["realigned"] = len(sanctioned)
    return rep


BASE.assign = assign
AUDIT_HOME.compare = compare


def realign_books(books: dict, ledger: list) -> dict:
    """books = {冊檔名: 內容}。把對齊帳上的錯位列直接改寫(沒動的列逐位元不變 · 整本照號排序)。回 {"done": [...], "blocked": [...]};就地改 books。"""
    done, blocked = [], []
    for name in sorted(books):
        m = AUDIT_HOME.BOOK_RX.match(name)
        if not (m and m.group("kind") in DECLARED_KINDS):
            continue
        lines = [ln for ln in books[name].splitlines() if ln.strip()]
        parsed = [json.loads(ln) for ln in lines]
        state = {"rows": {(r.get("kind"), r.get("key")): r for r in parsed}}
        before = {id(r): r.get("code") for r in parsed}
        res = realign(state, ledger, set())
        done += res["done"]
        blocked += res["blocked"]
        if not res["done"]:
            continue
        out = {}
        for ln, r in zip(lines, parsed):
            out[r["code"]] = ln if before[id(r)] == r["code"] else json.dumps(r, ensure_ascii=False, separators=(",", ":"))
        if len(out) != len(lines):
            raise ValueError("realign 會製造重號:" + name)
        books[name] = "".join(out[c] + "\n" for c in sorted(out))
    return {"done": done, "blocked": blocked}


def realign_apply(files: list, out=sys.stdout) -> int:
    """realign --apply [--scope 檔…]:留底 → 改寫錯位列 → 只登本批(補新列)→ 對留底稽核;不過就整批還原。"""
    ledger = load_ledger()
    snap = AUDIT_HOME.snapshot()
    before = AUDIT_HOME._texts(snap)
    books, ssot = dict(before[0]), json.loads(json.dumps(before[1], ensure_ascii=False))
    res = realign_books(books, ledger)
    if res["blocked"]:
        print(f"[編號 · 對齊] RED · {len(res['blocked'])} 列的目標號被不動的活列佔著,一列不寫:{res['blocked'][:3]}", file=out)
        return 2
    SCOPE_HOME._remeta(ssot, books)
    SCOPE_HOME._write_state(books, ssot, snap)
    rc = PRIOR.main(["--apply", "--scope"] + list(files)) if files else 0
    rep = AUDIT_HOME.audit("寫前(對齊)", before=before, after=AUDIT_HOME.current_state())
    bad = bool(rep["missing"] or rep["changed_identity"] or rep["duplicate_codes"]) or rc != 0
    print(f"[編號 · 對齊] {'RED' if bad else 'GREEN'} · 對齊帳 {len(ledger)} 列 · 改寫 {len(res['done'])} 列 · 只登本批 rc {rc}"
          f" · 遺失 {len(rep['missing'])} · 改身分 {len(rep['changed_identity'])} · 重號 {rep['duplicate_codes']} · 已裁定對齊 {rep.get('realigned', 0)}", file=out)
    if bad:
        n = AUDIT_HOME.restore(snap)
        print(f"[編號 · 對齊] 不過 → 已整批還原 {n} 個檔", file=out)
        return 2
    return 0


def plan_ledger(numbook=None) -> list:
    """現在編號冊上的錯位列 → 對齊帳該有的列(不寫檔)。"""
    p = Path(numbook) if numbook else HERE / "VIA_NumberBooks" / "VIA_NumberBook_REQ_v0100.jsonl"
    out = []
    for ln in (p.read_text(encoding="utf-8").splitlines() if p.is_file() else []):
        if not ln.strip():
            continue
        r = json.loads(ln)
        if r.get("declared") and not r.get("gone_since") and r.get("code") != "VIA-" + r["declared"]:
            out.append({"kind": "REQ", "key": r["key"], "declared": r["declared"], "from": r["code"], "to": "VIA-" + r["declared"]})
    return out


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if a[:1] == ["realign-plan"]:
        rows = plan_ledger()
        have = {(e["key"], e["from"]) for e in load_ledger()}
        for r in rows:
            print(("  [帳上有] " if (r["key"], r["from"]) in have else "  [待裁定] ") + f"{r['declared']}:{r['from']} → {r['to']}")
        print(f"[{ENGINE}] realign-plan · 錯位 {len(rows)} 列 · 對齊帳 {len(load_ledger())} 列(只列不寫)")
        return 0
    if a[:1] == ["realign"]:
        if "--apply" not in a:
            return main(["realign-plan"])
        files = a[a.index("--scope") + 1:] if "--scope" in a else []
        return realign_apply([f for f in files if not f.startswith("--")])
    return PRIOR.main(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:260]) if note and not cond else ""), flush=True)

    print(f"[計] {ENGINE} 自測開始(暫存資料 · 不碰真冊 · 零網路)", flush=True)

    def row(declared, code, status="PARTIAL", kind="REQ", **kw):
        return dict({"code": code, "full": f"{code} {declared} t", "kind": kind, "cat": "需求/" + status, "declared": declared,
                     "key": f"req|{declared}@v0100", "lamp": "RED", "note": "x"}, **kw)

    def st(*rs):
        return {"rows": {(r["kind"], r["key"]): dict(r) for r in rs}}

    # 三條互相錯開 + 一段往前移(含跳號)
    base = [row("VCGC-REQ264", "VIA-VCGC-REQ262"), row("VCGC-REQ262", "VIA-VCGC-REQ263"), row("VCGC-REQ263", "VIA-VCGC-REQ264"),
            row("VDF-REQ052", "VIA-VDF-REQ046"), row("VDF-REQ057", "VIA-VDF-REQ052", "COVERED"), row("VDF-REQ045", "VIA-VDF-REQ045")]
    led = [{"kind": "REQ", "key": r["key"], "from": r["code"], "to": "VIA-" + r["declared"]} for r in base[:5]]
    s1 = st(*base)
    r1 = realign(s1, led, set())
    codes1 = {r["declared"]: r["code"] for r in s1["rows"].values()}
    chk("① 帳上有的錯位全部對到冊上代碼(互相錯開的三條一次換位 · 往前移的回到原號)", all(c == "VIA-" + d for d, c in codes1.items()) and len(r1["done"]) == 5 and not r1["blocked"], codes1)
    chk("② 對齊後沒有重號 · 列數不變 · 舊號留在 realigned_from · 燈回到狀態燈", len(set(codes1.values())) == 6 and len(s1["rows"]) == 6
        and s1["rows"][("REQ", "req|VDF-REQ052@v0100")]["realigned_from"] == "VIA-VDF-REQ046"
        and s1["rows"][("REQ", "req|VDF-REQ057@v0100")]["lamp"] == "GREEN" and s1["rows"][("REQ", "req|VDF-REQ052@v0100")]["lamp"] == "AMBER"
        and s1["rows"][("REQ", "req|VDF-REQ052@v0100")]["full"].startswith("VIA-VDF-REQ052 "))
    s2 = st(*base)
    r2 = realign(s2, [], set())
    chk("③ 帳上沒有的錯位一列都不動(照舊 RED,要裁定才改)", not r2["done"] and all(s2["rows"][k] == st(*base)["rows"][k] for k in s2["rows"]))
    s3 = st(*base)
    r3 = realign(s3, [dict(led[3], **{"from": "VIA-VDF-REQ999"})], set())
    chk("④ 帳上的舊號對不上現況 → 不動(鍵與舊號都要對得上)", not r3["done"])
    s4 = st(row("VDF-REQ052", "VIA-VDF-REQ046"), row("VDF-REQ057", "VIA-VDF-REQ052"))
    r4 = realign(s4, [led[3]], set())           # 只裁定 052,057 還佔著 VIA-VDF-REQ052
    chk("⑤ 目標號被不動的活列佔著 → 這一列不動、列進 blocked,不製造重號", not r4["done"] and len(r4["blocked"]) == 1
        and s4["rows"][("REQ", "req|VDF-REQ052@v0100")]["code"] == "VIA-VDF-REQ046")
    s5 = st(row("VDF-REQ062", "VIA-VDF-REQ062", "COVERED"), row("VDF-REQ064", "VIA-VDF-REQ063"))
    r5 = realign(s5, [], {("REQ", "req|VDF-REQ064@v0100")})
    chk("⑥ 新列第一次發號就用冊上代碼(跳號也對)· 新列不留 realigned_from", s5["rows"][("REQ", "req|VDF-REQ064@v0100")]["code"] == "VIA-VDF-REQ064"
        and "realigned_from" not in s5["rows"][("REQ", "req|VDF-REQ064@v0100")] and len(r5["done"]) == 1)
    s6 = st(row("VDF-REQ001", "VIA-VDF-REQ009", kind="FNC"))
    chk("⑦ 不是 WKF / STP / REQ 的種類不碰", not realign(s6, [], {("FNC", "req|VDF-REQ001@v0100")})["done"])
    gone = row("VDF-REQ052", "VIA-VDF-REQ046", gone_since="t")
    chk("⑧ 已退役的列不碰", not realign(st(gone), led, set())["done"])
    # audit:帳上的號不算改身分;帳外的照抓;遺失 · 重號原樣
    import tempfile
    global LEDGER
    keep = LEDGER
    with tempfile.TemporaryDirectory(prefix="mdl237_v0124_") as td:
        LEDGER = Path(td) / LEDGER_NAME
        LEDGER.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in led), encoding="utf-8")
        inv_b = {"codes": {r["code"]: ("REQ", r["key"]) for r in base}, "dups": [], "rows": 6}
        inv_a = {"codes": {"VIA-" + r["declared"]: ("REQ", r["key"]) for r in base}, "dups": [], "rows": 6}
        inv_a["codes"]["VIA-VDF-REQ046"] = ("REQ", "req|VDF-REQ046@v0100")      # 保留列補上跳號
        c1 = compare(inv_b, inv_a)
        chk("⑨ audit:對齊帳上的號不算改身分(realigned 另報)· 遺失 0 · 重號 0", c1["changed_identity"] == [] and c1["missing"] == [] and c1["duplicate_codes"] == 0 and c1["realigned"] >= 4, c1)
        inv_x = {"codes": dict(inv_a["codes"], **{"VIA-VDF-REQ045": ("REQ", "req|VDF-REQ999@v0100")}), "dups": ["VIA-VDF-REQ052"], "rows": 7}
        del inv_x["codes"]["VIA-VCGC-REQ262"]
        c2 = compare(inv_b, inv_x)
        chk("⑩ audit 反控:帳外的改身分 · 遺失 · 重號照抓", "VIA-VDF-REQ045" in c2["changed_identity"] and "VIA-VCGC-REQ262" in c2["missing"] and c2["duplicate_codes"] == 1, c2)
        LEDGER.unlink()
        c3 = compare(inv_b, inv_a)
        chk("⑪ 沒有對齊帳時,同樣的改動照舊算改身分(不默默放行)", len(c3["changed_identity"]) >= 4 and c3["realigned"] == 0)
    LEDGER = keep
    dumps = lambda r: json.dumps(r, ensure_ascii=False, separators=(",", ":"))
    text0 = "".join(dumps(r) + "\n" for r in sorted(base, key=lambda r: r["code"]))
    bk = {"VIA_NumberBook_REQ_v0100.jsonl": text0, "VIA_NumberBook_FNC_VCGC_v0100.jsonl": "x\n"}
    rb = realign_books(bk, led)
    new_rows = [json.loads(x) for x in bk["VIA_NumberBook_REQ_v0100.jsonl"].splitlines()]
    same = dumps(base[5]) in bk["VIA_NumberBook_REQ_v0100.jsonl"].splitlines()
    chk("⑪b realign_books:錯位列直接改寫 · 列數不變 · 無重號 · 照號排序 · 沒動的列逐位元不變 · 別種冊不碰",
        len(rb["done"]) == 5 and len(new_rows) == 6 and len({r["code"] for r in new_rows}) == 6
        and [r["code"] for r in new_rows] == sorted(r["code"] for r in new_rows) and all(r["code"] == "VIA-" + r["declared"] for r in new_rows)
        and same and bk["VIA_NumberBook_FNC_VCGC_v0100.jsonl"] == "x\n", [r["code"] for r in new_rows])
    with tempfile.TemporaryDirectory(prefix="mdl237_v0124b_") as td:
        LEDGER = Path(td) / LEDGER_NAME
        LEDGER.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in led), encoding="utf-8")
        real_audit = AUDIT_HOME.audit("自測", before=({"VIA_NumberBook_REQ_v0100.jsonl": text0}, {}), after=({"VIA_NumberBook_REQ_v0100.jsonl": bk["VIA_NumberBook_REQ_v0100.jsonl"]}, {}))
        LEDGER.unlink()
        raw_audit = AUDIT_HOME.audit("自測", before=({"VIA_NumberBook_REQ_v0100.jsonl": text0}, {}), after=({"VIA_NumberBook_REQ_v0100.jsonl": bk["VIA_NumberBook_REQ_v0100.jsonl"]}, {}))
    LEDGER = keep
    chk("⑪e 走真正的稽核路徑(定義 audit 的那一層):有對齊帳 → 改身分 0 · 已裁定 > 0;沒有帳 → 照舊報改身分",
        real_audit["changed_identity"] == [] and real_audit.get("realigned", 0) > 0 and real_audit["duplicate_codes"] == 0
        and len(raw_audit["changed_identity"]) > 0, (real_audit.get("changed_identity"), real_audit.get("realigned"), raw_audit.get("changed_identity")))
    chk("⑪f 掛鉤掛在定義的那一層(不是轉手的那一層)", _defined_in(AUDIT_HOME, "audit") and AUDIT_HOME.audit.__globals__["compare"] is compare
        and _defined_in(SCOPE_HOME, "merge_scoped"))
    bk2 = {"VIA_NumberBook_REQ_v0100.jsonl": text0}
    chk("⑪c realign_books:沒有對齊帳 → 內容逐位元不變", not realign_books(bk2, [])["done"] and bk2["VIA_NumberBook_REQ_v0100.jsonl"] == text0)
    s7 = st(*base)
    keep_assign = globals()["_PRIOR_ASSIGN"]
    globals()["_PRIOR_ASSIGN"] = lambda items, state: state
    try:
        a7 = assign([], s7)
    finally:
        globals()["_PRIOR_ASSIGN"] = keep_assign
    chk("⑪d 一般發號(assign)不動舊的錯位列 —— 舊列換號只走 realign --apply", not a7["_realign"]["done"] and a7["rows"][("REQ", "req|VDF-REQ052@v0100")]["code"] == "VIA-VDF-REQ046")
    s8 = st(row("VCGC-REQ004", "VIA-VCGC-REQ003"), row("VCGC-REQ005", "VIA-VCGC-REQ004"), row("VCGC-REQ003", "VIA-VCGC-REQ005"))
    r8 = realign(s8, [], {("REQ", "req|VCGC-REQ005@v0100"), ("REQ", "req|VCGC-REQ003@v0100")})
    c8 = sorted(r["code"] for r in s8["rows"].values())
    chk("⑪g 被擋的列留在原號 → 想搬進那個號的列也擋(算到不再變才動)· 不製造重號", len(set(c8)) == 3 and not r8["done"] and len(r8["blocked"]) == 2, (c8, r8))
    s9 = st(row("VCGC-REQ004", "VIA-VCGC-REQ003"), row("VCGC-REQ009", "VIA-VCGC-REQ004"), row("VCGC-REQ003", "VIA-VCGC-REQ005"))
    r9 = realign(s9, [], {("REQ", "req|VCGC-REQ009@v0100"), ("REQ", "req|VCGC-REQ003@v0100")})
    chk("⑪h 同一批裡沒被牽連的新列照樣對齊(只擋有相依的)", s9["rows"][("REQ", "req|VCGC-REQ009@v0100")]["code"] == "VIA-VCGC-REQ009"
        and s9["rows"][("REQ", "req|VCGC-REQ003@v0100")]["code"] == "VIA-VCGC-REQ005" and len(r9["blocked"]) == 1)
    with tempfile.TemporaryDirectory(prefix="mdl237_v0124c_") as td:
        LEDGER = Path(td) / LEDGER_NAME
        LEDGER.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in led), encoding="utf-8")
        one = lambda key: {"codes": {"VIA-VCGC-REQ262": ("REQ", key)}, "dups": [], "rows": 1}
        u1 = compare(one("req|VCGC-REQ262@v0100"), one("req|UNAUTHORIZED@v0100"))
        u2 = compare(one("req|VCGC-REQ264@v0100"), one("req|VCGC-REQ999@v0100"))
        u3 = compare(one("req|VCGC-REQ264@v0100"), one("req|VCGC-REQ262@v0100"))
        u4 = compare({"codes": {"VIA-VCGC-REQ262": ("REQ", "req|VCGC-REQ264@v0100")}, "dups": [], "rows": 1},
                     {"codes": {"VIA-VCGC-REQ262": ("WKF", "req|VCGC-REQ262@v0100")}, "dups": [], "rows": 1})
    LEDGER = keep
    chk("⑪i audit 只放行帳上那一步:已對齊的號再改給別的列 → 照抓;原主是帳上那列但落點不是正主 → 照抓;種類不同 → 照抓;正確那一步才放行",
        u1["changed_identity"] == ["VIA-VCGC-REQ262"] and u1["realigned"] == 0 and u2["changed_identity"] == ["VIA-VCGC-REQ262"]
        and u3["changed_identity"] == [] and u3["realigned"] == 1 and u4["changed_identity"] == ["VIA-VCGC-REQ262"], (u1, u2, u3, u4))
    chk("⑫ 裝進本體:BASE.assign 與 audit 層的 compare 都是本版", BASE.assign is assign and AUDIT_HOME.compare is compare)
    chk("⑬ 加速器真的載到(VIA_ACCEL 非空)", VIA_ACCEL is not None)
    srcs = Path(__file__).read_text(encoding="utf-8")
    chk("⑭ 加速器橋在語法樹匯入 · 不含本機路徑", "import VIA_SuperAccel_Module as VIA_ACCEL" in srcs and ("C:" + "\\Users") not in srcs)
    BASE.ENGINE = PRIOR.ENGINE
    BASE.assign, AUDIT_HOME.compare = _PRIOR_ASSIGN, _PRIOR_COMPARE      # 前版鏈自測要在它自己的判法下跑
    try:
        rc_prior = PRIOR.selftest()
    finally:
        BASE.ENGINE = ENGINE
        BASE.assign, AUDIT_HOME.compare = assign, compare
    chk("⑮ 前版 v0123 自測(含它的前版鏈)rc 0 · 跑完本版的掛鉤還在", rc_prior == 0 and BASE.assign is assign and AUDIT_HOME.compare is compare, "rc %s" % rc_prior)
    n = sum(ok)
    print("[計] %s 本版 %d/%d · %s" % (ENGINE, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
