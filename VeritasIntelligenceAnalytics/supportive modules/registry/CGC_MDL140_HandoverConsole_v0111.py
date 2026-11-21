#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL140_HandoverConsole v0111 — 薄尾:VCGC 交接閘只算 VCGC 自己的列;VDF / VRN / VQG / VAP 的列改成「他系統 · 只讀」摘要

操作員 2026-11-21 19:41:「收斂完善整理他 獨立系統不影響VDF VRN開發」(接 19:40「VCGC好亂是否要重建比較快」→ 選收斂)。
根因(REQ237):VCGC 的交接閘把 VDF / VRN / VQG 的檔與案一起算 → 別人的開發一動,VCGC 的燈、SDD 鎖、收尾就全卡。
本版(L120 / L123:四系統對等獨立、互相只讀監控):
  ① 每一列先判歸屬:路徑在 functional modules/<VDF|VRN|VQG|VAP>/ → 該系統;代碼 / 案號以 VDF- / VRN- / VQG- / VAP- 開頭 → 該系統;
     其餘(supportive modules · docs · VCGC- / SUP- / 認不出)→ VCGC(認不出就留在 VCGC,寧嚴勿漏)。
  ② VCGC 的燈 / 驗收燈 / 下一步只看 VCGC 的列與 VCGC 的待辦;他系統的列一筆不刪,搬到 report["peer_rows"],
     並在 report["peer"] 給每個系統一行:燈 · 列數 · 依規則分 → 由各自的 SYSTEM MANAGER 處理,VCGC 不代修。
  ③ 主控台 check 照舊印 VCGC 的列,最後多印一行一系統的「他系統 · 只讀」。
  ④ 要回到舊的整棵樹判法:VIA_HANDOFF_SCOPE=ALL(只在那一次行程設)。checkpoint 走同一個 audit → 也只看 VCGC。
其餘全部照 v0110 / 前版鏈。不改任何冊、不寫 VDF / VRN 的檔。
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

import collections
import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL140_HandoverConsole"
ENGINE = Path(__file__).stem
VERSION = "v0111"
PEERS = ("VDF", "VRN", "VQG", "VAP")
_PATH_RE = re.compile(r"functional modules/(VDF|VRN|VQG|VAP)/")
_CODE_RE = re.compile(r"(?<![A-Za-z0-9])(VDF|VRN|VQG|VAP)-(?:REQ|WKF|STP|ENG|MDL)?\d")


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
VIA = PRIOR.VIA
POLICY = PRIOR.POLICY
BASE = PRIOR.BASE


def owner_of(detail) -> str:
    """一列的歸屬系統。路徑優先,再看代碼;認不出 = VCGC(寧嚴勿漏)。"""
    if isinstance(detail, dict):
        text = " ".join(str(detail.get(k, "")) for k in ("id", "path", "case", "requirement", "file", "code"))
        if not text.strip():
            text = str(detail)
    else:
        text = str(detail)
    text = text.replace("\\", "/")
    m = _PATH_RE.search(text)
    if m:
        return m.group(1)
    head = text.strip()
    m = re.match(r"(VDF|VRN|VQG|VAP)-", head)
    if m:
        return m.group(1)
    if re.match(r"(VCGC|SUP)-", head) or "supportive modules/" in text or text.startswith("docs/"):
        return "VCGC"
    m = _CODE_RE.search(text)
    return m.group(1) if m else "VCGC"


def _lamp(rows) -> str:
    lamps = [r.get("lamp") for r in rows]
    return "RED" if "RED" in lamps else "YELLOW" if lamps else "GREEN"


def apply_system_scope(report: dict) -> dict:
    if os.environ.get("VIA_HANDOFF_SCOPE", "").upper() == "ALL":
        report["scope"] = "ALL(整棵樹;VIA_HANDOFF_SCOPE=ALL)"
        return report
    mine, peer_rows = [], []
    for row in report.get("rows", []):
        o = owner_of(row.get("detail"))
        if o == "VCGC":
            mine.append(row)
        else:
            peer_rows.append(dict(row, owner=o))
    pend_mine, pend_peer = [], []
    for item in report.get("pending", []) or []:
        o = owner_of(item if isinstance(item, dict) else str(item))
        (pend_mine if o == "VCGC" else pend_peer).append(item if o == "VCGC" or not isinstance(item, dict) else dict(item, owner=o))
    peer = {}
    for s in PEERS:
        rs = [r for r in peer_rows if r["owner"] == s]
        ps = [p for p in pend_peer if isinstance(p, dict) and p.get("owner") == s]
        if rs or ps:
            peer[s] = {"lamp": _lamp(rs), "rows": len(rs), "pending": len(ps),
                       "by_rule": dict(collections.Counter(r.get("rule") for r in rs).most_common()),
                       "note": "他系統 · 只讀:由 %s 自己的 SYSTEM MANAGER 處理,VCGC 不代修" % s}
    lamp = _lamp(mine)
    report["rows"] = mine
    report["pending"] = pend_mine
    report["peer_rows"] = peer_rows
    report["peer_pending"] = pend_peer
    report["peer"] = peer
    report["scope"] = "VCGC(L120 / L123 各系統獨立;他系統的列見 peer · 只讀)"
    report["lamp"] = lamp
    report["closeout_lamp"] = ("RED" if lamp == "RED" else "YELLOW"
                               if pend_mine or lamp == "YELLOW" or report.get("z281_handover") else "GREEN")
    s = report.setdefault("summary", {})
    s["findings"] = len(mine)
    s["pending"] = len(pend_mine)
    s["peer_findings"] = len(peer_rows)
    s["peer_pending"] = len(pend_peer)
    return report


_PREV_AUDIT = BASE.audit
LAST = {}


def audit(via=VIA, policy=None, baseline=None, require_baseline=True):
    rep = apply_system_scope(_PREV_AUDIT(via, policy, baseline, require_baseline))
    LAST["report"] = rep
    return rep


BASE.audit = audit


def __getattr__(name: str):
    return getattr(PRIOR, name)


def peer_lines(report: dict) -> list:
    out = []
    for s, p in (report.get("peer") or {}).items():
        rules = " · ".join("%s %d" % (k, v) for k, v in list(p["by_rule"].items())[:4])
        out.append("[他系統 · 只讀] %s %s · 列 %d · 待辦 %d · %s → 由 %s 自己處理,不計入 VCGC 燈" % (s, p["lamp"], p["rows"], p["pending"], rules or "—", s))
    return out


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print("[DENY] VCGC entry required")
            return 2
        return selftest()
    rc = PRIOR.main(argv)
    if "--json" not in args and LAST.get("report"):
        for line in peer_lines(LAST["report"]):
            print(line)
    return rc


def selftest():
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s %s 自測開始(本版 7 項 · 再前版 %s)" % (_STEM, VERSION, PRIOR_PATH.name), flush=True)
    chk("S1 歸屬:路徑 / 代碼 / 案號三種寫法都分得對,認不出留 VCGC",
        owner_of("functional modules/VDF/engine/VDF_ENG054_TWDailyBackfill_v0114.py") == "VDF"
        and owner_of("functional modules\\VRN\\VRN_ENG072_FirstPageText_v0134.py") == "VRN"
        and owner_of({"id": "VDF-REQ012:C-x", "why": ["dependency changed"]}) == "VDF"
        and owner_of({"id": "VCGC-REQ243:C-applyrun-v0104"}) == "VCGC"
        and owner_of("supportive modules/registry/CGC_MDL283_CardMatrixFeedback_v0109.py") == "VCGC"
        and owner_of("supportive modules/70_VRN_Rules/SUP_MDL749_VRNFieldRuleHub_v0117.py") == "VCGC"
        and owner_of("VQG-REQ003") == "VQG" and owner_of("某個認不出的東西") == "VCGC")
    rep = {"rows": [{"lamp": "RED", "rule": "CHANGED_CODE_WITHOUT_TEST", "detail": "functional modules/VDF/a_v0101.py"},
                    {"lamp": "RED", "rule": "EVIDENCE_INVALID", "detail": {"id": "VRN-REQ001:c", "why": ["x"]}},
                    {"lamp": "YELLOW", "rule": "REQ_CHANGED", "detail": "VCGC-REQ001"}],
           "pending": [{"id": "VDF-REQ009", "next": "n"}, {"id": "VCGC-REQ243:host", "next": "m"}], "summary": {}}
    os.environ.pop("VIA_HANDOFF_SCOPE", None)
    r = apply_system_scope({k: (list(v) if isinstance(v, list) else dict(v)) for k, v in rep.items()})
    chk("S2 VCGC 的燈只看 VCGC 的列:他系統兩個紅不讓 VCGC 變紅(剩自己的黃)", r["lamp"] == "YELLOW" and len(r["rows"]) == 1, r["lamp"])
    chk("S3 他系統的列一筆不刪:搬進 peer_rows · 每系統一行(燈 · 列數 · 規則)", len(r["peer_rows"]) == 2
        and r["peer"]["VDF"]["lamp"] == "RED" and r["peer"]["VRN"]["rows"] == 1 and r["peer"]["VDF"]["pending"] == 1, r.get("peer"))
    chk("S4 待辦也分開:VCGC 只留自己的 · 驗收燈照 VCGC 待辦判", [p["id"] for p in r["pending"]] == ["VCGC-REQ243:host"]
        and r["closeout_lamp"] == "YELLOW" and r["summary"]["peer_findings"] == 2)
    os.environ["VIA_HANDOFF_SCOPE"] = "ALL"
    try:
        r2 = apply_system_scope({k: (list(v) if isinstance(v, list) else dict(v)) for k, v in rep.items()})
    finally:
        os.environ.pop("VIA_HANDOFF_SCOPE", None)
    chk("S5 VIA_HANDOFF_SCOPE=ALL = 舊的整棵樹判法(三列全留)", len(r2["rows"]) == 3 and "peer" not in r2)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("S6 檔面:第 3 行加速器標記 · 零 TA-Lib · 不寫同意閘 · audit 已接上(checkpoint 同一把尺)",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src) and BASE.audit is audit)
    prior_rc = PRIOR.selftest()
    chk("S7 前版 %s 自測照過" % PRIOR_PATH.name, prior_rc == 0, prior_rc)
    n = sum(ok)
    print("[計] %s %s 自測 %d/%d · %s" % (_STEM, VERSION, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
