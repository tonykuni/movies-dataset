#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL250_LedgerUnion v0100 — 帳本聯集:拉不動時把工作站本地帳本行安全併回(只增,不取單邊)

為什麼(R35d 工作站實錄 2026-10-01):`git pull` 被兩本本地改過的帳本擋住 ——
  error: Your local changes to the following files would be overwritten by merge:
    supportive modules/registry/VIA_Lessons_Ledger_v0100.json
    supportive modules/registry/VIA_VCGC_FullCheck_Ledger_v0100.jsonl
  兩本遠端也都有新行(容器跑過 11 次提交)→ stash pop 必衝突;拉齊醫生 CGC_MDL143 的 ledger_union 只認
  VIA_AutoCode_Registry,這兩本會留衝突標記。工作站因此停在 1cb0f4958(落後 57),新引擎全沒拿到。
做法(帳本律:只增、絕不取單邊):
  1. backup --to <夾>  先把本地改過的帳本複製出去(只複製,不刪不改)
  2. 操作員 git checkout -- <帳本> 讓它回到已提交版 → git pull --ff-only 拿到新版
  3. merge --from <夾> [--apply]  把備份裡的本地行併回剛拉下來的帳本:
     · *.jsonl:逐行聯集 —— 遠端行照原序在前,備份獨有的行照原序附後;同一行不重複
     · *.json 且有 entries 清單(教訓帳等):逐筆聯集 —— 完全相同 = 一筆;同 id 同 sig(同一條教訓,次數不同)
       = 保留一筆並取較大 count;同 id 不同內容 = 兩筆都留,備份那筆 id 加 "-WS"(本地),附 ws_import 標記
     · 其他檔:不碰,列為 SKIP
  沒加 --apply = 乾跑,只印會加幾行;--apply 才寫(寫前留 .pre_union 副本在備份夾)。
VIA_FROM_VCGC:經 VCGC 跑(via-vcgc run --family core CGC_MDL250_LedgerUnion …);selftest 例外。零網路;不用 TA-Lib。
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
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENGINE = Path(__file__).stem
LEDGER_NAME_RX = re.compile(r"(Ledger|ledger|_Events|events)[^/\\]*\.(jsonl|json)$")


def _canon(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def union_jsonl(upstream: str, local: str) -> tuple[str, dict]:
    """逐行聯集:遠端行照原序,本地獨有行照原序附後。空行略過;結尾留一個換行。"""
    up = [ln for ln in upstream.splitlines() if ln.strip()]
    seen = set(up)
    add = []
    for ln in local.splitlines():
        if ln.strip() and ln not in seen:
            add.append(ln)
            seen.add(ln)
    out = up + add
    return ("\n".join(out) + "\n") if out else "", {"upstream": len(up), "added": len(add)}


def union_entries(upstream: dict, local: dict, key: str = "entries") -> tuple[dict, dict]:
    """逐筆聯集(教訓帳型):完全相同 = 一筆;同 id 同 sig = 一筆取大 count;同 id 不同內容 = 本地那筆 id 加 -WS。"""
    up = list(upstream.get(key) or [])
    have = {_canon(e) for e in up}
    by_id = {}
    for i, e in enumerate(up):
        if isinstance(e, dict) and e.get("id") is not None:
            by_id.setdefault(str(e["id"]), i)
    stats = {"upstream": len(up), "added": 0, "count_merged": 0, "id_suffixed": 0, "identical": 0}
    for e in local.get(key) or []:
        c = _canon(e)
        if c in have:
            stats["identical"] += 1
            continue
        if isinstance(e, dict) and e.get("id") is not None and str(e["id"]) in by_id:
            j = by_id[str(e["id"])]
            u = up[j]
            if isinstance(u, dict) and u.get("sig") is not None and u.get("sig") == e.get("sig"):
                if isinstance(e.get("count"), int) and isinstance(u.get("count"), int) and e["count"] > u["count"]:
                    u = dict(u)
                    u["count"] = e["count"]
                    for k in ("ts", "head"):
                        if e.get(k):
                            u[k + "_ws"] = e[k]
                    up[j] = u
                    stats["count_merged"] += 1
                else:
                    stats["identical"] += 1
                have.add(c)
                continue
            e = dict(e)
            e["id"] = str(e["id"]) + "-WS"
            e["ws_import"] = True
            stats["id_suffixed"] += 1
        up.append(e)
        have.add(c)
        if isinstance(e, dict) and e.get("id") is not None:
            by_id.setdefault(str(e["id"]), len(up) - 1)
        stats["added"] += 1
    out = dict(upstream)
    out[key] = up
    return out, stats


def merge_file(target: Path, backup: Path, apply: bool) -> dict:
    if not target.exists():
        return {"file": target.name, "state": "SKIP", "why": "倉內沒有同名帳本(不代建)"}
    if target.suffix == ".jsonl":
        text, st = union_jsonl(target.read_text(encoding="utf-8"), backup.read_text(encoding="utf-8"))
    elif target.suffix == ".json":
        try:
            up = json.loads(target.read_text(encoding="utf-8"))
            lo = json.loads(backup.read_text(encoding="utf-8"))
        except ValueError as exc:
            return {"file": target.name, "state": "FAIL", "why": f"JSON 解析失敗(含衝突標記?):{exc}"}
        if not (isinstance(up, dict) and isinstance(up.get("entries"), list) and isinstance(lo, dict)):
            return {"file": target.name, "state": "SKIP", "why": "不是 entries 型帳本(不猜結構)"}
        merged, st = union_entries(up, lo)
        indent = 2 if target.read_text(encoding="utf-8").startswith('{\n  "') else 1
        text = json.dumps(merged, ensure_ascii=False, indent=indent) + "\n"
    else:
        return {"file": target.name, "state": "SKIP", "why": "非 .json/.jsonl"}
    state = "NOCHANGE" if not st.get("added") and not st.get("count_merged") else ("WROTE" if apply else "WOULD_ADD")
    if apply and state == "WROTE":
        shutil.copy2(target, backup.with_name(backup.name + ".pre_union"))
        target.write_text(text, encoding="utf-8", newline="\n")
    return {"file": target.name, "state": state, **st}


def find_target(name: str) -> Path | None:
    hits = [p for p in VIA.rglob(name) if ".git" not in p.parts and "VIA_Reports" not in p.parts]
    return hits[0] if len(hits) == 1 else (sorted(hits, key=lambda p: len(p.parts))[0] if hits else None)


def do_merge(src: Path, apply: bool) -> int:
    if not src.is_dir():
        print(f"[帳本聯集] NODATA · 備份夾不在:{src}")
        return 2
    files = [p for p in sorted(src.iterdir()) if p.is_file() and p.suffix in (".json", ".jsonl")]
    if not files:
        print(f"[帳本聯集] NODATA · 備份夾沒有 .json/.jsonl:{src}")
        return 2
    rc = 0
    for b in files:
        t = find_target(b.name)
        r = merge_file(t, b, apply) if t else {"file": b.name, "state": "SKIP", "why": "倉內找不到同名檔"}
        rc = 1 if r["state"] == "FAIL" else rc
        extra = " · ".join(f"{k} {v}" for k, v in r.items() if k not in ("file", "state"))
        print(f"  [{r['state']:<9}] {r['file']} · {extra}")
    print(f"[帳本聯集] {'已寫' if apply else '乾跑(加 --apply 才寫)'} · 備份夾 {src}")
    return rc


def do_backup(dst: Path) -> int:
    r = subprocess.run(["git", "-C", str(VIA), "status", "--porcelain"], capture_output=True, text=True, encoding="utf-8")
    rows = [ln[3:].strip().strip('"') for ln in (r.stdout or "").splitlines() if ln[:2].strip() == "M"]
    led = [p for p in rows if LEDGER_NAME_RX.search(p)]
    if not led:
        print("[帳本備份] 沒有改過的帳本(免備份)")
        return 0
    dst.mkdir(parents=True, exist_ok=True)
    root = Path(subprocess.run(["git", "-C", str(VIA), "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip())
    for rel in led:
        src = root / rel
        shutil.copy2(src, dst / src.name)
        print(f"  [備份] {rel} → {dst / src.name}")
    print(f"[帳本備份] {len(led)} 本 → {dst}(只複製;下一步 git checkout -- 這幾本 → git pull → merge --from 這夾 --apply)")
    return 0


def _opt(a: list, flag: str):
    return a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else None


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    up = '{"a":1}\n{"a":2}\n'
    lo = '{"a":1}\n{"a":3}\n'
    t, st = union_jsonl(up, lo)
    chk("jsonl:遠端照序 + 本地獨有附後 · 同行不重複", t == '{"a":1}\n{"a":2}\n{"a":3}\n' and st == {"upstream": 2, "added": 1}, t)
    U = {"schema": "x", "entries": [{"id": "VF-1", "sig": "s1", "count": 2}, {"id": "VF-2", "sig": "s2", "count": 1}]}
    L = {"schema": "x", "entries": [{"id": "VF-1", "sig": "s1", "count": 5, "ts": "T"},
                                    {"id": "VF-2", "sig": "OTHER", "count": 1},
                                    {"id": "VF-3", "sig": "s3", "count": 1},
                                    {"id": "VF-1", "sig": "s1", "count": 2}]}
    m, st2 = union_entries(U, L)
    ids = [e["id"] for e in m["entries"]]
    chk("entries:同 id 同 sig = 一筆取大 count(2→5)", m["entries"][0]["count"] == 5 and st2["count_merged"] == 1, m["entries"][0])
    chk("entries:同 id 不同內容 = 兩筆都留,本地加 -WS", "VF-2-WS" in ids and "VF-2" in ids and st2["id_suffixed"] == 1, ids)
    chk("entries:本地獨有照加 · 完全相同不重複", "VF-3" in ids and ids.count("VF-1") == 1 and st2["identical"] == 1, st2)
    chk("entries:其他欄位(schema)不動", m["schema"] == "x")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        tgt = td / "X_Ledger.jsonl"
        tgt.write_text(up, encoding="utf-8")
        bk = td / "bk"
        bk.mkdir()
        (bk / "X_Ledger.jsonl").write_text(lo, encoding="utf-8")
        r0 = merge_file(tgt, bk / "X_Ledger.jsonl", apply=False)
        chk("乾跑不寫檔", r0["state"] == "WOULD_ADD" and tgt.read_text(encoding="utf-8") == up)
        r1 = merge_file(tgt, bk / "X_Ledger.jsonl", apply=True)
        chk("--apply 寫入且留 .pre_union 副本", r1["state"] == "WROTE" and (bk / "X_Ledger.jsonl.pre_union").exists()
            and tgt.read_text(encoding="utf-8").count("\n") == 3)
        r2 = merge_file(tgt, bk / "X_Ledger.jsonl", apply=True)
        chk("冪等:再跑一次 NOCHANGE", r2["state"] == "NOCHANGE")
        bad = td / "Y_Ledger.json"
        bad.write_text('{"entries": [\n<<<<<<< HEAD\n', encoding="utf-8")
        (bk / "Y_Ledger.json").write_text('{"entries": []}', encoding="utf-8")
        chk("帶衝突標記的帳本 = FAIL(不猜、不寫)", merge_file(bad, bk / "Y_Ledger.json", apply=True)["state"] == "FAIL")
    body = Path(__file__).read_text(encoding="utf-8")
    chk("帶加速器橋 · VIA_FROM_VCGC 標記 · 不匯入 TA-Lib", "[VIA:ACCEL-BRIDGE" in body and "VIA_FROM_VCGC" in body
        and not re.search(r"^\s*(import|from)\s+" + "ta" + r"lib\b", body, re.M))
    print(f"[{ENGINE}] 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "engine": ENGINE, "state": "DENY", "why": "only via-vcgc(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    if a and a[0] == "merge":
        src = _opt(a, "--from")
        return do_merge(Path(src) if src else Path(""), "--apply" in a) if src else (print("用法:merge --from <備份夾> [--apply]") or 2)
    if a and a[0] == "backup":
        dst = _opt(a, "--to") or str(VIA / "VIA_Reports" / "ledger_backup" / datetime.now().strftime("%Y%m%d_%H%M%S"))
        return do_backup(Path(dst))
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
