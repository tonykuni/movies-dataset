#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_SSOTSync v0101 — v0100 薄尾(v0100 留著一字不改):提案冊併入核號請求(操作員 2026-10-29 Gemini 對話的正則 / 同義字 / 代碼)。

v0101 只加一件事:request() 在 v0100 的登記冊條目之後,把 SSOT/VRN2_SSOT_Proposals_v*.json(最新版號)的提案條目附進 ssot_items
(proposed_no = VRN2-PROP-xxxx · ssot_id 空白 · 狀態「提案 · 待 VCGC 核號」· 指紋 = 內容 sha256 前 16),寫同一本 contract/VRN2_NUMBER_REQUEST_latest.json;
counts 多 proposals。apply / 核發冊讀法 / 狀態冊全照 v0100(VCGC 核發後 apply 補填登記冊;提案冊本身不改)。
動詞同 v0100:request | apply | sync [--vrn <VRN-2 程式夾>] · --selftest
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

TAG = "v0101"
DISPLAY_NAME = "VRN2_SSOTSync"
PRIOR_NAME = "VRN2_SSOTSync_v0100.py"
HERE = Path(__file__).resolve().parent
PROPOSALS_GLOB = "VRN2_SSOT_Proposals_v[0-9][0-9][0-9][0-9].json"


def _prior():
    for path in (HERE / PRIOR_NAME, HERE.parent / "v144" / "new" / PRIOR_NAME):
        if path.is_file():
            spec = importlib.util.spec_from_file_location("vrn2_ssotsync_prior_v0100", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))


PRIOR = _prior()
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
_native_request = PRIOR.request


def proposals_path(vrn: Path) -> Path | None:
    hits = []
    for folder in (Path(vrn) / "SSOT", Path(vrn), HERE / "SSOT", HERE):
        if folder.is_dir():
            hits += list(folder.glob(PROPOSALS_GLOB))
    hits = sorted(set(hits), key=lambda p: int(re.search(r"_v(\d{4})", p.name).group(1)))
    return hits[-1] if hits else None


def proposal_items(vrn: Path) -> tuple:
    p = proposals_path(vrn)
    if not p:
        return [], None
    try:
        book = json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return [], p
    items = []
    for e in book.get("entries") or []:
        if not isinstance(e, dict) or not e.get("key"):
            continue
        fp = hashlib.sha256(json.dumps(e.get("value"), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
        kind = e.get("kind") or "SSOT"
        items.append({"key": e["key"], "entry": "%s|%s" % (kind, e["key"]), "kind": kind, "vcgc_kind": PRIOR.VCGC_KIND.get(kind, "SSOT"), "proposed_no": e.get("proposed_no"), "ssot_id": e.get("ssot_id") or "",
                      "fingerprint": fp, "version": book.get("version"), "src": p.name, "status": e.get("status") or "提案 · 待 VCGC 核號", "note": e.get("note") or "", "proposal": True})
    return items, p


def request(vrn: Path) -> dict:
    """v0100 request → 再附提案冊條目(同一本請求冊重寫)。"""
    vrn = Path(vrn)
    req = _native_request(vrn)
    items, p = proposal_items(vrn)
    if not items:
        req.setdefault("counts", {})["proposals"] = 0
        return req
    path = vrn / "contract" / PRIOR.REQUEST_NAME
    if req.get("lamp") == "GRAY" or not path.is_file():
        book = {"from": "VRN-2", "subsystem": "VRN-2(VIA-03 VRN 家族 · 獨立 MAIN)", "engine": "%s %s" % (DISPLAY_NAME, TAG), "ts": PRIOR.now(), "register": "(沒有登記冊 · 只有提案冊)",
                "rule": "子系統提出時 ssot_id 空白;VCGC 偵測三系統衝突 → 使用者 + AI 修到無誤 → VCGC 核發 → VRN-2 apply 自動補填", "pending": [], "ssot_items": [], "program_items": [], "self_conflicts": [], "counts": {"ssot_like": 0, "program": 0, "self_conflicts": 0}}
    else:
        book = json.loads(path.read_text(encoding="utf-8"))
    seen = {i.get("entry") for i in book.get("ssot_items") or []}
    added = [i for i in items if i["entry"] not in seen]
    book["ssot_items"] = (book.get("ssot_items") or []) + added
    book["pending"] = (book.get("pending") or []) + [i["proposed_no"] for i in added if i.get("proposed_no")]
    book.setdefault("counts", {})["ssot_like"] = len(book["ssot_items"])
    book["counts"]["proposals"] = len(items)
    book["proposals_book"] = p.name
    book["engine"] = "%s %s" % (DISPLAY_NAME, TAG)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    req.update({k: book[k] for k in ("pending", "ssot_items", "counts", "proposals_book")})
    req["lamp"] = "YELLOW" if (req.get("self_conflicts") or []) else "GREEN"
    return req


PRIOR.request = request   # v0100 的 sync() 走它自己 globals 裡的 request → 改綁成本版(薄尾規則:不 rebind 包裝,直接指派)
sync = PRIOR.sync


def selftest() -> int:
    import tempfile
    bad = []

    def chk(label, cond):
        PRIOR.say(("[PASS] " if cond else "[FAIL] ") + label)
        if not cond:
            bad.append(label)

    src = HERE / "VRN2_SSOT_Proposals_v0100.json"
    chk("① 提案冊在本夾 · 9 條 · ssot_id 全空 · proposed_no VRN2-PROP-xxxx · 含三形式代號 / 電話 / 評等 / 目標價 / 職稱", src.is_file() and (lambda b: len(b["entries"]) == 9 and all(e["ssot_id"] == "" and e["proposed_no"].startswith("VRN2-PROP-") for e in b["entries"]) and {e["key"] for e in b["entries"]} >= {"TW_TICKER_TWSE", "TW_TICKER_YFINANCE", "TW_TICKER_BLOOMBERG", "PHONE_TAIPEI_HK", "RATING_CODE", "TARGET_PRICE", "ANALYST_TITLE"})(json.loads(src.read_text(encoding="utf-8"))))
    book = json.loads(src.read_text(encoding="utf-8"))
    rx = {e["key"]: e["value"] for e in book["entries"] if e["kind"] == "REGEX"}
    chk("② 正則可編譯且樣本對:2330 / 0050 / 00878B → TWSE · 2330.TW / 6488.TWO → YF · 2330 TT → BB · +886 2 2326 8179 / (02) 2345-6789 / +852 2345 6789 → 電話;2330.TW 不是 TWSE 形式",
        bool(re.match(rx["TW_TICKER_TWSE"], "2330")) and bool(re.match(rx["TW_TICKER_TWSE"], "0050")) and bool(re.match(rx["TW_TICKER_TWSE"], "00878B")) and not re.match(rx["TW_TICKER_TWSE"], "2330.TW")
        and bool(re.match(rx["TW_TICKER_YFINANCE"], "2330.TW")) and bool(re.match(rx["TW_TICKER_YFINANCE"], "6488.TWO")) and bool(re.match(rx["TW_TICKER_BLOOMBERG"], "2330 TT"))
        and all(re.search(rx["PHONE_TAIPEI_HK"], s) for s in ("+886 2 2326 8179", "(02) 2345-6789", "+852 2345 6789", "02-2345-6789")) and not re.search(rx["PHONE_TAIPEI_HK"], "12345678901"))
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "VIA"
        (root / "supportive modules" / "registry").mkdir(parents=True)
        (root / "functional modules").mkdir(parents=True)
        vrn = root / "functional modules" / "VRN2"
        (vrn / "registry").mkdir(parents=True)
        (vrn / "SSOT").mkdir()
        (vrn / "SSOT" / "VRN2_SSOT_Proposals_v0100.json").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        r0 = sync(vrn)
        q0 = json.loads((vrn / "contract" / PRIOR.REQUEST_NAME).read_text(encoding="utf-8"))
        chk("③ 沒有登記冊只有提案冊:請求冊照寫 · 9 條提案 · pending 9 · counts.proposals 9 · 來源冊名", (vrn / "contract" / PRIOR.REQUEST_NAME).is_file() and q0["counts"]["proposals"] == 9 and len(q0["ssot_items"]) == 9 and len(q0["pending"]) == 9 and q0["proposals_book"] == "VRN2_SSOT_Proposals_v0100.json" and all(i["ssot_id"] == "" and i["proposal"] for i in q0["ssot_items"]))
        E = {"SSOT|VRN2_SSOT": {"no": "VRN2-SSOT-0001", "kind": "SSOT", "key": "VRN2_SSOT", "status": "暫編 · 待 VCGC 核號", "fp": "aaa", "version": "v0101", "src": "VRN2_SSOT_v0101.json"},
             "ENG|VRN_ENG397_P1Segment": {"no": "VRN2-ENG-0001", "kind": "ENG", "key": "VRN_ENG397_P1Segment", "status": "暫編 · 待 VCGC 核號", "fp": "ddd", "version": "v0127", "src": "VRN_ENG397_P1Segment_v0127.py"}}
        (vrn / "registry" / "VRN2_Component_Register_v0100.json").write_text(json.dumps({"schema": "VIA.VRN2.ComponentRegister.v1", "entries": E}, ensure_ascii=False), encoding="utf-8")
        r1 = sync(vrn)
        q1 = json.loads((vrn / "contract" / PRIOR.REQUEST_NAME).read_text(encoding="utf-8"))
        chk("④ 有登記冊:v0100 的 1 條 SSOT + 1 條程式 + 9 條提案 → ssot_items 10 · program 1 · pending 11 · sync 綠", r1["lamp"] == "GREEN" and q1["counts"]["ssot_like"] == 10 and q1["counts"]["program"] == 1 and q1["counts"]["proposals"] == 9 and len(q1["pending"]) == 11 and r1["request"]["counts"]["proposals"] == 9)
        r2 = sync(vrn)
        q2 = json.loads((vrn / "contract" / PRIOR.REQUEST_NAME).read_text(encoding="utf-8"))
        chk("⑤ 再跑一次:每輪重寫 · 不疊加(仍 10 / 11)· 提案冊沒被改", q2["counts"]["ssot_like"] == 10 and len(q2["pending"]) == 11 and (vrn / "SSOT" / "VRN2_SSOT_Proposals_v0100.json").read_text(encoding="utf-8") == src.read_text(encoding="utf-8"))
        (vrn / "SSOT" / "VRN2_SSOT_Proposals_v0100.json").unlink()
        r3 = sync(vrn)
        q3 = json.loads((vrn / "contract" / PRIOR.REQUEST_NAME).read_text(encoding="utf-8"))
        chk("⑥ 沒有提案冊(且本夾也沒有時才會 0):counts.proposals 存在 · v0100 行為不變", "proposals" in q3["counts"] and q3["counts"]["ssot_like"] >= 1 and r3["lamp"] == "GREEN")
    PRIOR.say("[%s] %s %s --selftest · 6 項 · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, TAG, len(bad)))
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())
