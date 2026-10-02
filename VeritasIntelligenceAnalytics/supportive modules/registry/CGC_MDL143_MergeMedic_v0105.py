#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL143_MergeMedic v0105 — 薄尾:拉齊醫生的「台帳」認得 *_Ledger_v####.json/.jsonl(前版 v0104 本體照讀)

v0104→v0105(R35d 工作站實錄 2026-10-01):`git pull` 被 VIA_Lessons_Ledger_v0100.json 與
  VIA_VCGC_FullCheck_Ledger_v0100.jsonl 兩本本地改過的帳本擋住,工作站停在 1cb0f4958(落後 57)。
  醫生的髒樹律(stash → 合併 → pop)本來就對,但 pop 起衝突時只有 VIA_AutoCode_Registry 被認作「台帳」走聯集;
  這兩本被歸 MANUAL → 衝突標記留在帳本裡、stash 留存 = 操作員還是卡住。
  本版只換兩格(前版 resolve / stash_pop 在自己命名空間叫 classify / ledger_union,換掉即生效):
  · classify:VIA_*_Ledger_v####.json / .jsonl 也是 LEDGER(AutoCode 照舊)
  · ledger_union:AutoCode 型(有 ledger 清單)照前版;entries 型 .json 與逐行 .jsonl 交給 CGC_MDL250_LedgerUnion
    (只增、絕不取單邊;同 id 不同內容 → 本地那筆 id 加 -WS;同一行 / 同一筆不重複)
  其餘(分叉合併 · 同名雙物 · 再生物 · stash 律 · 誠實停)一字不動,照 v0104。
VIA_FROM_VCGC:醫生由 via-reload / via-medic / via-unstick(PS 短令)直呼,前版即無閘,本版不加;零網路(只 git);不用 TA-Lib。
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

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL143_MergeMedic"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load(stem_glob: str, default: str, tag: str):
    me = _vnum(Path(__file__)) if stem_glob.startswith(_STEM) else 10 ** 9
    path = max((p for p in HERE.glob(stem_glob) if 0 <= _vnum(p) < me), key=_vnum, default=HERE / default)
    spec = importlib.util.spec_from_file_location(tag + Path(__file__).stem, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod, path


PRIOR, _PRIOR_PATH = _load(_STEM + "_v*.py", "CGC_MDL143_MergeMedic_v0104.py", "medic_prior_for_")
UNION, _UNION_PATH = _load("CGC_MDL250_LedgerUnion_v*.py", "CGC_MDL250_LedgerUnion_v0100.py", "ledger_union_for_")


def __getattr__(name: str):
    return getattr(PRIOR, name)


ENGINE = Path(__file__).stem
LEDGER2_RX = re.compile(r"(^|/)VIA_[A-Za-z0-9_]*Ledger_v\d+\.(json|jsonl)$")
_prior_classify = PRIOR.classify
_prior_union = PRIOR.ledger_union


def classify(path: str) -> str:
    p = str(path).replace("\\", "/")
    if LEDGER2_RX.search(p):
        return "LEDGER"
    return _prior_classify(path)


def ledger_union(ours: bytes | None, theirs: bytes | None) -> tuple[bytes | None, dict]:
    """AutoCode 型照前版;entries 型 .json 與 .jsonl 交 MDL250(theirs = 遠端序在前,ours 獨有者附後;同前版慣例)。"""
    o_txt = (ours or b"").decode("utf-8", errors="replace")
    t_txt = (theirs or b"").decode("utf-8", errors="replace")
    try:
        t_obj = json.loads(t_txt) if t_txt.strip() else None
    except ValueError:
        t_obj = None
    if isinstance(t_obj, dict) and isinstance(t_obj.get("ledger"), list):
        return _prior_union(ours, theirs)
    if isinstance(t_obj, dict) and isinstance(t_obj.get("entries"), list):
        try:
            o_obj = json.loads(o_txt) if o_txt.strip() else {"entries": []}
        except ValueError:
            return None, {"ok": False, "why": "本地帳本不可解析"}
        merged, st = UNION.union_entries(t_obj, o_obj if isinstance(o_obj, dict) else {"entries": []})
        indent = 2 if t_txt.startswith('{\n  "') else 1
        return ((json.dumps(merged, ensure_ascii=False, indent=indent) + "\n").encode("utf-8"),
                {"ok": True, "theirs": st["upstream"], "added": st["added"], "total": len(merged["entries"]), "kind": "entries"})
    lines = [ln for ln in (t_txt + "\n" + o_txt).splitlines() if ln.strip()]
    if lines and all(ln.lstrip().startswith("{") for ln in lines):
        text, st = UNION.union_jsonl(t_txt, o_txt)
        return text.encode("utf-8"), {"ok": True, "theirs": st["upstream"], "added": st["added"],
                                      "total": st["upstream"] + st["added"], "kind": "jsonl"}
    return _prior_union(ours, theirs)


PRIOR.classify = classify            # 前版 resolve / stash_pop 在自己命名空間叫這兩個名字
PRIOR.ledger_union = ledger_union


def selftest() -> int:
    import os
    import subprocess
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    reg = "VeritasIntelligenceAnalytics/supportive modules/registry/"
    chk("classify:教訓帳 / 全檢帳 = LEDGER", classify(reg + "VIA_Lessons_Ledger_v0100.json") == "LEDGER"
        and classify(reg + "VIA_VCGC_FullCheck_Ledger_v0100.jsonl") == "LEDGER")
    chk("classify:AutoCode 照舊 LEDGER · 一般檔不誤收", classify(reg + "VIA_AutoCode_Registry_v0100.json") == "LEDGER"
        and classify(reg + "VIA_Handoff_Continuity_SSOT_v0100.json") != "LEDGER")
    d, info = ledger_union(b'{"a":1}\n{"a":3}\n', b'{"a":1}\n{"a":2}\n')
    chk("jsonl 聯集:遠端序在前 · 本地獨有附後", d == b'{"a":1}\n{"a":2}\n{"a":3}\n' and info["added"] == 1, d)
    d2, i2 = ledger_union(json.dumps({"entries": [{"id": "VF-9", "sig": "x"}]}).encode(),
                          json.dumps({"entries": [{"id": "VF-9", "sig": "y"}]}).encode())
    ids = [e["id"] for e in json.loads(d2)["entries"]]
    chk("entries 聯集:同 id 不同內容 → 本地加 -WS,兩筆都留", ids == ["VF-9", "VF-9-WS"], ids)
    a = {"ledger": [{"code": "A", "ts": "1", "name": "n"}]}
    d3, i3 = ledger_union(json.dumps({"ledger": [{"code": "B", "ts": "2", "name": "m"}]}).encode(), json.dumps(a).encode())
    chk("AutoCode 型照前版聯集", i3.get("ok") and len(json.loads(d3)["ledger"]) == 2)

    # 實錄重現:本地髒帳本 + 遠端也加了行 → 醫生 sync --apply 拉得動且兩邊行都在、零衝突標記
    def g(cwd, *args):
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                              env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                                   "GIT_COMMITTER_EMAIL": "t@t", "GIT_EDITOR": "true"})
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        g(td, "init", "-q", "--bare", "-b", "main", str(td / "origin.git"))
        g(td, "clone", "-q", str(td / "origin.git"), str(td / "up"))
        up = td / "up"
        g(up, "checkout", "-q", "-b", "main")
        (up / "VIA_Lessons_Ledger_v0100.json").write_text(json.dumps({"schema": "s", "entries": [{"id": "VF-1", "sig": "a"}]}, indent=2) + "\n", encoding="utf-8")
        (up / "VIA_VCGC_FullCheck_Ledger_v0100.jsonl").write_text('{"r":1}\n', encoding="utf-8")
        g(up, "add", "-A"); g(up, "commit", "-qm", "base"); g(up, "push", "-q", "origin", "main")
        g(td, "clone", "-q", str(td / "origin.git"), str(td / "ws"))
        ws = td / "ws"
        les = json.loads((up / "VIA_Lessons_Ledger_v0100.json").read_text(encoding="utf-8"))
        les["entries"].append({"id": "VF-2", "sig": "cloud"})
        (up / "VIA_Lessons_Ledger_v0100.json").write_text(json.dumps(les, indent=2) + "\n", encoding="utf-8")
        with open(up / "VIA_VCGC_FullCheck_Ledger_v0100.jsonl", "a", encoding="utf-8") as f:
            f.write('{"r":"cloud"}\n')
        (up / "new_engine.py").write_text("x = 1\n", encoding="utf-8")
        g(up, "add", "-A"); g(up, "commit", "-qm", "cloud"); g(up, "push", "-q", "origin", "main")
        lw = json.loads((ws / "VIA_Lessons_Ledger_v0100.json").read_text(encoding="utf-8"))
        lw["entries"].append({"id": "VF-2", "sig": "workstation"})
        (ws / "VIA_Lessons_Ledger_v0100.json").write_text(json.dumps(lw, indent=2) + "\n", encoding="utf-8")
        with open(ws / "VIA_VCGC_FullCheck_Ledger_v0100.jsonl", "a", encoding="utf-8") as f:
            f.write('{"r":"ws"}\n')
        g(ws, "fetch", "-q", "origin")
        ff = g(ws, "merge", "--ff-only", "origin/main")
        chk("實錄重現:本地髒帳本擋住快轉", ff.returncode != 0 and "overwritten" in (ff.stderr + ff.stdout))
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            rep = PRIOR.sync(ws, "main", apply=True, do_print=False)
        les2 = (ws / "VIA_Lessons_Ledger_v0100.json").read_text(encoding="utf-8")
        fc2 = (ws / "VIA_VCGC_FullCheck_Ledger_v0100.jsonl").read_text(encoding="utf-8")
        sigs = [e["sig"] for e in json.loads(les2)["entries"]]
        chk("醫生 sync --apply 拉得動(新檔到位)", (ws / "new_engine.py").exists(), rep.get("state"))
        chk("教訓帳兩邊都在、零衝突標記(本地同號加 -WS)", "<<<<<<<" not in les2 and sigs.count("cloud") == 1
            and sigs.count("workstation") == 1, sigs)
        chk("全檢帳兩邊行都在、零衝突標記", "<<<<<<<" not in fc2 and '{"r":"cloud"}' in fc2 and '{"r":"ws"}' in fc2, fc2)
        chk("stash 已清(全解不留殘渣)", (g(ws, "stash", "list").stdout or "").strip() == "")
    body = Path(__file__).read_text(encoding="utf-8")
    chk("帶加速器橋 · VIA_FROM_VCGC 標記 · 不匯入 TA-Lib", "[VIA:ACCEL-BRIDGE" in body and "VIA_FROM_VCGC" in body
        and not re.search(r"^\s*(import|from)\s+" + "ta" + r"lib\b", body, re.M))
    print(f"[{ENGINE} 帳本聯集] 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
