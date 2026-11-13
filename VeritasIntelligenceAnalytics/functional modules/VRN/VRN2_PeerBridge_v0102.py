#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN2_PeerBridge v0102 — 薄尾:prove 一項都沒驗到時講原因(VRN-1 版本 · 每項為何不能借)

桌機實錄(操作員貼回 2026-11-11 02:16):`prove` → 「[prove] YELLOW · VRN-1 樹未被動到:True ·」—— 找到了 VRN-1,
但可驗的借用工具 0 項,畫面沒說為什麼。借用(BORROWED)要求 VRN-1 那支檔的 sha256 = 整合冊釘的指紋;
指紋是照 VRN-1 origin/main 0993c2d(2026-11-05,PR #82)釘的,桌機 VRN-1 倉若停在舊版或有本機改動,就全部落回 GAP。
本版只改 prove 的回報(驗法 · 收據 · 不動 VRN-1 樹全照 v0101):
  · 0 項時列出:VRN-1 根 · 它的 HEAD 提交 · 各能力為何不能借(borrow_why_not,例:指紋變了 冊 xxx · 現 yyy)· 狀態計數
  · 給下一步:在 VRN-1 倉 `git pull`(只更新那份 clone,不改 VRN-1 的 GitHub),再跑 prove。
VRN-1 一律只讀(L123);不碰 TA-Lib;不讀寫同意閘;零網路。
"""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

VERSION = "v0102"
HERE = Path(__file__).resolve().parent
_STEM = "VRN2_PeerBridge"
PINNED_VRN1 = "0993c2d"                                   # 整合冊指紋所依的 VRN-1 origin/main(2026-11-05 PR #82)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
B = PRIOR.B


def __getattr__(name):
    return getattr(PRIOR, name)


def vrn1_head(root: Path | None) -> str:
    if not root:
        return ""
    try:
        p = subprocess.run(["git", "-C", str(root), "log", "-1", "--format=%h %cs"], capture_output=True, text=True, timeout=30)
        return p.stdout.strip() if p.returncode == 0 else ""
    except Exception:
        return ""


def explain(via: Path, rec: dict) -> list:
    """prove 0 項時的原因行(只讀)。"""
    if rec.get("rows"):
        return []
    root = Path(rec["vrn1_root"]) if rec.get("vrn1_root") else None
    lines = []
    if root:
        head = vrn1_head(root)
        lines.append(f"  VRN-1 根 {root} · HEAD {head or '(讀不到 git)'} · 指紋依 {PINNED_VRN1}"
                     + ("" if head.startswith(PINNED_VRN1) else " ← 版本不同,指紋多半對不上"))
    m = PRIOR.gap_matrix(via)
    lines.append("  狀態 " + " · ".join(f"{k} {v}" for k, v in m.get("counts", {}).items()))
    why = [(r["cap"], r.get("borrow_why_not")) for r in m.get("rows", []) if r.get("state") == "GAP" and r.get("borrow_why_not")]
    for cap, w in why[:8]:
        lines.append(f"  · {cap:<20}{w}")
    if len(why) > 8:
        lines.append(f"  · … 另 {len(why) - 8} 項")
    if root:
        lines.append(f"  下一步:git -C \"{root}\" pull(只更新這份 clone)→ 再跑 prove;若 VRN-1 有本機改動,先 git -C \"{root}\" status 看清楚")
    return lines


def cmd_prove(args=None) -> int:
    via = B.via_root()
    rec = PRIOR.prove(via)
    for x in rec.get("rows", []):
        print(f"  {x['result']:<5}{x['cap']:<20}{x['vrn1_engine'][:40]:<42}rc {x['rc']} · {' | '.join(x['tail'])[:90]}")
    print(f"[prove {VERSION}] {rec['lamp']} · VRN-1 樹未被動到:{rec.get('vrn1_untouched')} · 驗了 {len(rec.get('rows', []))} 項"
          + (f" · {rec['why']}" if rec.get("why") else ""))
    for ln in explain(via, rec):
        print(ln)
    if rec.get("rows"):
        out = via / PRIOR.PROVE_DIR_REL / f"VRN2_Prove_{rec['ts'].replace(':', '').replace('-', '')}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        import json
        out.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"[收據] {out}")
    return 0 if rec["lamp"] == "GREEN" else 1


def selftest() -> int:
    checks = []

    def ck(name, cond, note=""):
        checks.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note else ""))

    rc0 = PRIOR.selftest()
    ck("v0101 自測照過(v0100 43 項 + v0101 22 項)", rc0 == 0, f"rc {rc0}")
    keep = PRIOR.gap_matrix
    PRIOR.gap_matrix = lambda via: {"counts": {"MATCH": 14, "BORROWED": 0, "GAP": 2},
                                    "rows": [{"cap": "pivot.db", "state": "GAP", "borrow_why_not": "指紋變了:冊 aaaaaaaaaaaa · 現 bbbbbbbbbbbb"},
                                             {"cap": "output.verify", "state": "GAP", "borrow_why_not": "VRN-1 側檔不在"},
                                             {"cap": "x.match", "state": "MATCH"}]}
    try:
        lines = explain(Path("."), {"rows": [], "vrn1_root": str(Path("/nonexistent-vrn1"))})
    finally:
        PRIOR.gap_matrix = keep
    txt = "\n".join(lines)
    ck("0 項時:列 VRN-1 根 · HEAD · 指紋依據版本", "VRN-1 根" in txt and PINNED_VRN1 in txt and "版本不同" in txt, lines[0][:60] if lines else "")
    ck("0 項時:逐項列不能借的原因(指紋變了 · 檔不在)· 只列 GAP", "指紋變了" in txt and "VRN-1 側檔不在" in txt and "x.match" not in txt)
    ck("0 項時:給下一步(只 pull 那份 clone)", "pull" in txt and "只更新這份 clone" in txt)
    ck("有驗到項目時不囉嗦", explain(Path("."), {"rows": [{"cap": "a"}]}) == [])
    src = Path(__file__).read_text(encoding="utf-8")
    ck("VRN-1 只讀:本版不寫 VRN-1 樹(無 write / unlink 指向 VRN-1)", "vrn1_root\"]) / " not in src)
    ck("不碰 TA-Lib · 不寫同意閘", not re.search(r"^\s*(import|from)\s+talib", src, re.M)
       and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    ck("尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    print(f"[自測 {VERSION}] {sum(checks)}/{len(checks)} " + ("PASS" if all(checks) else "FAIL"))
    return 0 if all(checks) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if args[:1] == ["prove"]:
        PRIOR._route_prior()
        return cmd_prove(args[1:])
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())
