#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0120 — 薄尾:註冊收據(P1 · CONST-030 缺口)

操作員令(2026-11-10):「REGISTER 成功的指令或更新的文件版本號註冊給號 · 時間詳細到分鐘 · 檔案大小 · 檔案格式 ·
自動編號註冊衝突重複檢測 · 編號功能今天算才嚴格啟用 · 取捨資料請小心」→ 規劃 VIA_RegistryUpgrade_Plan_20261110 P1;
操作員「開始做 P1 註冊收據補欄」。

做法(v0100 … v0119 一字不動;號冊一字不動):
  · 收據另立一本只增帳 registry/VIA_RegistrationReceipts_v0100.jsonl(不放進 VIA_NumberBooks,號冊讀者與 IMMUT 稽核不受影響)。
  · 每張收據:code · book · version · source · registered_at(YYYY-MM-DD HH:MM +00:00,到分鐘)· uuid · operator(AI / 操作員)·
    bytes · format(副檔名)· sha256 · kind(new 新號 / version 換版 / backfill 今日補收據)· engine(發收據的尾版)。
  · `--apply` 照前版跑完(rc 0)才比對前後號冊:新代碼或同代碼換版 → 發收據;前版 rc 非 0 一張不發。
  · 重複檢測:同 (code, version, sha256) 已有收據就不再發(重跑零新增);同 code 同 version 但 sha 不同 → 記 conflict 欄,不蓋舊收據。
  · `receipts`:嚴格啟用日(2026-11-10)起編號的列,有沒有收據 → GREEN / YELLOW(缺幾張、哪幾支);之前的列不判紅(不回溯)。
  · `receipts --backfill --apply`:只對嚴格啟用日起編號、還沒收據的列補發(kind=backfill,時間取該列 numbered_at 到分鐘)。
  · operator:`--operator <名>` 或環境變數 VIA_OPERATOR;都沒有記 "AI"。
只收 VCGC 呼叫(經 via-vcgc run);零網路;不碰 TA-Lib;只讀子系統的冊。
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

import hashlib
import importlib.util
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
VERSION = "v0120"
_STEM = "CGC_MDL237_NumberingSystem"
STRICT_FROM = "2026-11-10"                                   # 編號嚴格啟用日(操作員 2026-11-10;之前的列不回溯)
VIA_ROOT = HERE.parents[1]                                   # 號冊 source 欄以 VIA 樹為根
BOOK_DIR = HERE / "VIA_NumberBooks"
RECEIPTS = HERE / "VIA_RegistrationReceipts_v0100.jsonl"
FIELDS = ("code", "book", "version", "source", "registered_at", "uuid", "operator", "bytes", "format", "sha256", "kind", "engine")


def _vnum_v0120(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load_v0120(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0120(p) < _vnum_v0120(__file__)), key=_vnum_v0120)
PRIOR = _load_v0120(PRIOR_PATH, _STEM + "_prior_for_" + ENGINE)       # v0119


def __getattr__(name):
    return getattr(PRIOR, name)


# ---------- 收據核心 ----------
def minute(ts: str | None = None) -> str:
    """任何時間字串 → 'YYYY-MM-DD HH:MM +00:00';沒給 = 現在 UTC。缺時區的照 UTC 記(不猜在地時區)。"""
    if not ts:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M +00:00")
    s = str(ts).strip()
    m = re.match(r"(\d{4}-\d{2}-\d{2})[ T](\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?\s*(Z|[+-]\d{2}:?\d{2})?$", s)
    if not m:
        return s[:10] + " 00:00 +00:00" if re.match(r"\d{4}-\d{2}-\d{2}$", s) else ""
    tz = m.group(4) or "+00:00"
    tz = "+00:00" if tz == "Z" else (tz if ":" in tz else tz[:3] + ":" + tz[3:])
    return f"{m.group(1)} {m.group(2)}:{m.group(3)} {tz}"


def book_rows(book_dir: Path | None = None) -> dict:
    """{(book, code): row}(只讀;壞列跳過)。"""
    out = {}
    for f in sorted((book_dir or BOOK_DIR).glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict) and r.get("code"):
                out[(f.name, r["code"])] = r
    return out


SUB_RX = re.compile(r"-FNC\d{3,}(?:-FNC\d{3,})*$")      # 函式子號(FNC 冊:code · q · api · line)


def changed(before: dict, after: dict) -> list:
    """新代碼 → kind=new;同代碼換版 → kind=version;其餘不算(只刷新時間的不發收據)。
    函式子號不單發收據(去重):併入母號收據的 functions(本輪新增子號數)。"""
    res, subs = [], {}
    for k, r in after.items():
        if SUB_RX.search(r["code"]):
            if k not in before:
                parent = SUB_RX.sub("", r["code"])
                subs[parent] = subs.get(parent, 0) + 1
            continue
        old = before.get(k)
        if old is None:
            res.append((k, r, "new"))
        elif str(old.get("version") or "") != str(r.get("version") or ""):
            res.append((k, r, "version"))
    return [(k, dict(r, _functions=subs.get(r["code"], 0)), kind) for k, r, kind in res]


def file_facts(source: str, root: Path | None = None) -> dict:
    p = (root or VIA_ROOT) / str(source or "")
    if not source or not p.is_file():
        return {"bytes": None, "format": Path(str(source or "")).suffix.lstrip(".").lower() or None, "sha256": None}
    data = p.read_bytes()
    return {"bytes": len(data), "format": p.suffix.lstrip(".").lower() or None, "sha256": hashlib.sha256(data).hexdigest()}


def make_receipt(book: str, row: dict, kind: str, operator: str, at: str | None = None, root: Path | None = None) -> dict:
    rec = {"code": row["code"], "book": book, "version": row.get("version"), "source": row.get("source"),
           "registered_at": minute(at), "uuid": str(uuid.uuid4()), "operator": operator}
    rec.update(file_facts(row.get("source"), root))
    rec.update({"kind": kind, "engine": f"{_STEM} {VERSION}"})
    if row.get("_functions"):
        rec["functions"] = row["_functions"]                # 本輪新增函式子號數(子號不另發收據)
    return rec


def load_receipts(path: Path | None = None) -> list:
    p = path or RECEIPTS
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def append_receipts(recs: list, path: Path | None = None) -> dict:
    """只增;同 (code, version, sha256) 已有 → 略過(重複);同 (code, version) 不同 sha → 照發並標 conflict(不蓋舊收據)。"""
    p = path or RECEIPTS
    have = load_receipts(p)
    seen = {(r.get("code"), r.get("version"), r.get("sha256")) for r in have}
    by_cv = {}
    for r in have:
        by_cv.setdefault((r.get("code"), r.get("version")), set()).add(r.get("sha256"))
    added, dup, conflict = [], 0, 0
    for r in recs:
        key = (r["code"], r.get("version"), r.get("sha256"))
        if key in seen:
            dup += 1
            continue
        prev = by_cv.get((r["code"], r.get("version")), set()) - {r.get("sha256")}
        if prev:
            r["conflict"] = "same code+version, different sha256: " + ",".join(sorted(str(x)[:12] for x in prev))
            conflict += 1
        seen.add(key)
        by_cv.setdefault((r["code"], r.get("version")), set()).add(r.get("sha256"))
        added.append(r)
    if added:
        with p.open("a", encoding="utf-8", newline="\n") as fh:
            for r in added:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {"added": len(added), "duplicate": dup, "conflict": conflict}


def is_file_source(source) -> bool:
    """來源像檔案路徑(有副檔名)才要求 format;函式庫列(例:python stdlib)不是檔,不編格式。"""
    return bool(source) and bool(re.search(r"\.[A-Za-z0-9]{1,8}$", str(source).strip()))


def receipt_complete(r: dict) -> bool:
    if not all(r.get(f) not in (None, "") for f in ("uuid", "operator", "registered_at")):
        return False
    if not re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} [+-]\d{2}:\d{2}$", str(r.get("registered_at") or "")):
        return False
    return r.get("format") not in (None, "") or not is_file_source(r.get("source"))


def strict_rows(rows: dict) -> dict:
    return {k: r for k, r in rows.items() if str(r.get("numbered_at") or "")[:10] >= STRICT_FROM}


def check(rows: dict | None = None, receipts: list | None = None) -> dict:
    rows = book_rows() if rows is None else rows
    receipts = load_receipts() if receipts is None else receipts
    have = {(r.get("code"), str(r.get("version") or "")) for r in receipts}
    strict = strict_rows(rows)
    missing = sorted(r["code"] for r in strict.values() if (r["code"], str(r.get("version") or "")) not in have)
    incomplete = sorted(r.get("code") for r in receipts if not receipt_complete(r))
    lamp = "GREEN" if not missing and not incomplete else "YELLOW"
    return {"lamp": lamp, "strict_from": STRICT_FROM, "strict_rows": len(strict), "receipts": len(receipts),
            "missing": missing, "incomplete": incomplete,
            "conflict": sorted(r["code"] for r in receipts if r.get("conflict"))}


def backfill(operator: str, apply: bool, rows: dict | None = None, path: Path | None = None, root: Path | None = None) -> dict:
    rows = book_rows() if rows is None else rows
    rep = check(rows, load_receipts(path))
    miss = set(rep["missing"])
    recs = [make_receipt(b, r, "backfill", operator, r.get("numbered_at"), root)
            for (b, c), r in strict_rows(rows).items() if c in miss]
    res = append_receipts(recs, path) if apply else {"added": 0, "duplicate": 0, "conflict": 0}
    res.update({"candidates": len(recs), "apply": apply})
    return res


# ---------- CLI ----------
def _operator(args: list) -> tuple[str, list]:
    if "--operator" in args:
        i = args.index("--operator")
        name = args[i + 1] if i + 1 < len(args) else ""
        args = args[:i] + args[i + 2:]
        return (name or "AI"), args
    return (os.environ.get("VIA_OPERATOR") or "AI"), args


def cmd_receipts(args: list, operator: str) -> int:
    if "--backfill" in args:
        res = backfill(operator, "--apply" in args)
        print(f"[收據 · 補發 {STRICT_FROM} 起] 候選 {res['candidates']} · 寫入 {res['added']} · 重複略過 {res['duplicate']} · "
              f"同號同版不同 sha {res['conflict']}" + ("" if res["apply"] else " · 試算(加 --apply 才寫)"))
    rep = check()
    print(f"[收據 · {VERSION}] {rep['lamp']} · 嚴格啟用日 {STRICT_FROM} 起編號 {rep['strict_rows']} 列 · 收據 {rep['receipts']} 張 · "
          f"缺 {len(rep['missing'])} · 欄不全 {len(rep['incomplete'])} · 衝突 {len(rep['conflict'])}"
          + (" · 缺:" + " · ".join(rep["missing"][:8]) + (" …" if len(rep["missing"]) > 8 else "") if rep["missing"] else ""))
    if "--json" in args:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    return 0


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["--selftest"]:
        return selftest(deep="--deep" in args)
    operator, args = _operator(args)
    if args[:1] == ["receipts"]:
        return cmd_receipts(args[1:], operator)
    if "--apply" not in args:
        return PRIOR.main(args)
    before = book_rows()
    rc = PRIOR.main(args)
    if rc != 0:
        print(f"[收據 · {VERSION}] 前版 rc {rc}:一張不發", file=sys.stderr)
        return rc
    recs = [make_receipt(b, r, kind, operator) for (b, _c), r, kind in changed(before, book_rows())]
    res = append_receipts(recs)
    print(f"[收據 · {VERSION}] 新號 / 換版 {len(recs)} · 寫入 {res['added']} · 重複略過 {res['duplicate']} · 同號同版不同 sha {res['conflict']}"
          f" · 帳 {RECEIPTS.name}")
    return rc


# ---------- 自測(暫存夾 · 不碰真冊)----------
def selftest(deep: bool = False) -> int:
    import tempfile
    checks = []

    def chk(name, cond, note=""):
        checks.append((name, bool(cond)))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note else ""))

    print(f"=== {_STEM} {VERSION} · 薄尾自測(註冊收據 · 暫存夾 · 零外呼)===")
    chk("時間到分鐘(含時區)", minute("2026-11-10 16:28:08 +0000") == "2026-11-10 16:28 +00:00"
        and minute("2026-11-10T01:02:03Z") == "2026-11-10 01:02 +00:00" and minute("2026-11-10") == "2026-11-10 00:00 +00:00",
        minute("2026-11-10 16:28:08 +0000"))
    chk("現在時間格式", re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} \+00:00$", minute()) is not None, minute())
    with tempfile.TemporaryDirectory() as td:
        root, books = Path(td) / "via", Path(td) / "via" / "books"
        books.mkdir(parents=True)
        src = root / "functional modules" / "X" / "X_ENG001_Demo_v0101.py"
        src.parent.mkdir(parents=True)
        src.write_bytes(b"print('demo')\n")
        bk = books / "VIA_NumberBook_ENG_v0100.jsonl"
        old = {"code": "VIA-X-ENG001", "version": "v0100", "source": "functional modules/X/X_ENG001_Demo_v0100.py",
               "numbered_at": "2026-11-01 10:00:00 +0000"}
        bk.write_text(json.dumps(old) + "\n", encoding="utf-8")
        before = book_rows(books)
        new = {"code": "VIA-X-ENG002", "version": "v0101", "source": "functional modules/X/X_ENG001_Demo_v0101.py",
               "numbered_at": "2026-11-10 16:28:08 +0000"}
        bump = dict(old, version="v0101", source=new["source"])
        bk.write_text(json.dumps(bump) + "\n" + json.dumps(new) + "\n", encoding="utf-8")
        after = book_rows(books)
        ch = changed(before, after)
        chk("比對:新號 = new · 換版 = version", sorted(k for _k, _r, k in ch) == ["new", "version"], [k for _k, _r, k in ch])
        chk("只刷新不發", changed(after, after) == [])
        fnc = {("FNC.jsonl", "VIA-X-ENG002-FNC001"): {"code": "VIA-X-ENG002-FNC001", "q": "main"},
               ("FNC.jsonl", "VIA-X-ENG002-FNC001-FNC001"): {"code": "VIA-X-ENG002-FNC001-FNC001", "q": "main._v"}}
        ch2 = changed(before, {**after, **fnc})
        chk("函式子號不單發 · 併入母號 functions", len(ch2) == 2
            and make_receipt(bk.name, [r for _k, r, _x in ch2 if r["code"] == "VIA-X-ENG002"][0], "new", "AI", None, root)
            .get("functions") == 2)
        rec = make_receipt(bk.name, new, "new", "AI", None, root)
        chk("收據欄齊(uuid · operator · 分鐘 · bytes · format · sha256)",
            all(rec.get(f) not in (None, "") for f in FIELDS) and rec["bytes"] == 14 and rec["format"] == "py"
            and rec["sha256"] == hashlib.sha256(b"print('demo')\n").hexdigest(), rec["sha256"][:12])
        miss_src = make_receipt(bk.name, dict(new, source="nope/none_v0100.py"), "new", "AI", None, root)
        chk("來源檔不在 → bytes / sha 留空不編", miss_src["bytes"] is None and miss_src["sha256"] is None and miss_src["format"] == "py")
        rp = Path(td) / "receipts.jsonl"
        r1 = append_receipts([rec], rp)
        r2 = append_receipts([make_receipt(bk.name, new, "new", "AI", None, root)], rp)
        chk("重跑零新增(同 code · 版 · sha)", r1["added"] == 1 and r2 == {"added": 0, "duplicate": 1, "conflict": 0}, r2)
        src.write_bytes(b"print('changed')\n")
        r3 = append_receipts([make_receipt(bk.name, new, "new", "AI", None, root)], rp)
        lines = rp.read_text(encoding="utf-8").splitlines()
        chk("同號同版內容不同 → 標 conflict · 舊收據不蓋", r3["conflict"] == 1 and len(lines) == 2
            and json.loads(lines[0])["sha256"] == rec["sha256"] and "conflict" in json.loads(lines[1]))
        rep = check(after, [])
        chk("嚴格啟用日前的列不判(只判今天起)", rep["strict_rows"] == 1 and rep["missing"] == ["VIA-X-ENG002"]
            and rep["lamp"] == "YELLOW", rep["missing"])
        rp2 = Path(td) / "r2.jsonl"
        dry = backfill("AI", False, after, rp2, root)
        chk("補發試算不寫", dry["candidates"] == 1 and dry["added"] == 0 and not rp2.exists())
        res = backfill("AI", True, after, rp2, root)
        got = load_receipts(rp2)
        chk("補發:kind=backfill · 時間取 numbered_at 到分鐘", res["added"] == 1 and got[0]["kind"] == "backfill"
            and got[0]["registered_at"] == "2026-11-10 16:28 +00:00")
        chk("補發後 GREEN", check(after, got)["lamp"] == "GREEN")
        chk("欄不全的收據 → YELLOW", check(after, [dict(got[0], registered_at="2026-11-10")])["lamp"] == "YELLOW")
        lib = {"uuid": "u", "operator": "AI", "registered_at": "2026-11-10 16:52 +00:00", "source": "python stdlib", "format": None}
        chk("函式庫列(非檔)不要求格式 · 檔案列缺格式才算不全", receipt_complete(lib)
            and not receipt_complete(dict(lib, source="a/b_v0100.py")))
        chk("號冊一字不動", bk.read_text(encoding="utf-8") == json.dumps(bump) + "\n" + json.dumps(new) + "\n")
    os.environ.pop("VIA_OPERATOR", None)
    chk("operator:--operator 優先,否則 AI", _operator(["x", "--operator", "Tony"]) == ("Tony", ["x"]) and _operator(["x"]) == ("AI", ["x"]))
    chk("收據帳不在號冊夾(號冊讀者 / IMMUT 不受影響)", RECEIPTS.parent != BOOK_DIR and not RECEIPTS.name.startswith("VIA_NumberBook_"))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("尾版保有前版公開名稱(TAILAPI · 經 __getattr__ 轉接)", all(getattr(sys.modules[__name__], n, None) is not None for n in names),
        f"{len(names)} 支")
    chk("不碰 TA-Lib · 不寫同意閘", ("ta" + "lib") not in Path(__file__).read_text(encoding="utf-8").replace("TA-Lib", "")
        and "VIA_NET_CONSENT\"] =" not in Path(__file__).read_text(encoding="utf-8"))
    if deep:
        rc0 = PRIOR.selftest()
        chk(f"前版 {PRIOR_PATH.stem[-5:]} 自測過(--deep)", rc0 == 0, f"rc {rc0}")
    ok = sum(c for _n, c in checks)
    print(f"[計] {_STEM} {VERSION} 本版 {ok}/{len(checks)} " + ("PASS" if ok == len(checks) else "FAIL")
          + ("" if deep else " · 前版自測另跑(--selftest --deep,約數分鐘)"))
    return 0 if ok == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
