#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_SSOTSync v0100 — VRN-2 側的 SSOT / Regex / 同義字 / 政策編號協作(操作員 2026-10-29 政策)。
三系統(VRN-2 / VDF / VCGC)各自獨立、互不直接影響;基層(VRN-2 / VDF)提出 SSOT · Regex · 同義字 · 政策,VCGC 也可提;
子系統提出時 SSOT ID 空白 → VCGC 偵測跨系統衝突 → 使用者 + AI 修到無誤 → VCGC 核發號碼 → 子系統看到就自動補填。
本工具只做 VRN-2 自己這一側(不寫 VDF / VCGC 的任何檔):
  request  讀 VRN-2 元件登記冊尾版(registry/VRN2_Component_Register_v*.json · ⑤ 寫的)→ 暫編(待核號)的 SSOT / REGEX / SYN / CFG / PARAM … 條目
           → contract/VRN2_NUMBER_REQUEST_latest.json(每條:鍵 · 類(VRN-2 類 + VCGC 類)· 暫編號 · ssot_id 空白 · 指紋 · 版本 · 來源)+ VRN-2 內部自撞(同鍵不同指紋)
  apply    讀 VCGC 核發冊 contract/VCGC_NUMBER_GRANT_latest.json({grants:{鍵或暫編號: 核發號}, conflicts:[{key, with, why}]};
           也看 <VIA>/VCGC/contract/ 與 <VIA>/supportive modules/registry/)→ 登記冊條目填 ssot_id · 狀態「已確認(VCGC)」/「衝突 · 待人判」
           → 內容有變才出新版登記冊(只增不減)· contract/VRN2_NUMBER_STATE_latest.json(pending / granted / conflicts)
  sync     apply → request(預設;啟動器 ⑤b 用)
  --selftest
收據與冊都在 VRN-2 自己的夾;VCGC 的核發冊只讀。
"""
from __future__ import annotations
import argparse
import datetime
import json
import os
import re
import sys
import tempfile
from pathlib import Path
TAG = "v0100"
DISPLAY_NAME = "VRN2_SSOTSync"
HERE = Path(__file__).resolve().parent
VCGC_KIND = {"SSOT": "SSOT", "REGEX": "RGX", "SYN": "SYN", "CFG": "PLCY", "PARAM": "PRMT", "DICT": "SSOT", "LIST": "SSOT", "ENG": "ENG", "MDL": "MDL", "CLS": "CLS", "FNC": "FNC", "MGR": "MDL", "PS": "TOOL", "IN": "IDX", "OUT": "IDX", "DF": "FD", "ENV": "ENV"}
REQUEST_KINDS = ("SSOT", "REGEX", "SYN", "CFG", "PARAM", "DICT", "LIST")        # 政策說的「SSOT REGEX 同義字 政策庫」這一類先送;程式類(ENG / MDL …)也送但分開列
REQUEST_NAME = "VRN2_NUMBER_REQUEST_latest.json"
GRANT_NAME = "VCGC_NUMBER_GRANT_latest.json"
STATE_NAME = "VRN2_NUMBER_STATE_latest.json"
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass


def say(line: str) -> None:
    print(line, flush=True)


def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{4})\.json$", p.name)
    return int(m.group(1)) if m else -1


def latest_register(vrn: Path) -> Path | None:
    hits = sorted((vrn / "registry").glob("VRN2_Component_Register_v[0-9][0-9][0-9][0-9].json"), key=_vnum) if (vrn / "registry").is_dir() else []
    return hits[-1] if hits else None


def via_root(vrn: Path) -> Path | None:
    for p in [vrn] + list(vrn.parents):
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
    return None


def grant_paths(vrn: Path) -> list:
    out = [vrn / "contract" / GRANT_NAME]
    root = via_root(vrn)
    if root:
        out += [root / "VCGC" / "contract" / GRANT_NAME, root / "supportive modules" / "registry" / GRANT_NAME, root / "VIA_Reports" / "vcgc" / GRANT_NAME]
    return out


def read_grant(vrn: Path) -> tuple:
    """合併所有找得到的核發冊(只讀)。回 (grants{鍵: 核發號}, conflicts[list], 來源路徑清單)。"""
    grants, conflicts, srcs = {}, [], []
    for gp in grant_paths(vrn):
        if not gp.is_file():
            continue
        try:
            g = json.loads(gp.read_text(encoding="utf-8-sig"))
        except Exception:  # noqa: BLE001
            continue
        srcs.append(str(gp))
        for k, v in (g.get("grants") or {}).items():
            if isinstance(v, str) and v.strip():
                grants[k] = v.strip()
        for c in g.get("conflicts") or []:
            if isinstance(c, dict) and c.get("key"):
                conflicts.append(c)
    return grants, conflicts, srcs


def _entry_keys(ek: str, e: dict) -> list:
    return [x for x in (e.get("no"), ek, e.get("key")) if x]


def apply(vrn: Path) -> dict:
    """核發冊 → 登記冊:填 ssot_id · 狀態;內容有變才出新版;寫 STATE。"""
    reg = latest_register(vrn)
    if not reg:
        return {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "apply", "at": now(), "lamp": "GRAY", "why": "沒有元件登記冊(先跑啟動器 ⑤)", "register": None}
    book = json.loads(reg.read_text(encoding="utf-8"))
    entries = book.get("entries") or {}
    grants, conflicts, srcs = read_grant(vrn)
    conf_by_key = {}
    for c in conflicts:
        conf_by_key.setdefault(c["key"], []).append(c)
    granted, conflicted, changed = [], [], 0
    for ek, e in entries.items():
        if not isinstance(e, dict) or str(e.get("status", "")).startswith("退役"):
            continue
        keys = _entry_keys(ek, e)
        hit = next((grants[k] for k in keys if k in grants), None)
        conf = next((conf_by_key[k] for k in keys if k in conf_by_key), None)
        if hit:
            if e.get("ssot_id") != hit or "已確認" not in str(e.get("status", "")):
                e["ssot_id"] = hit
                e["status"] = "已確認(VCGC)"
                e["granted_at"] = now()
                changed += 1
            granted.append(ek)
        elif conf:
            why = " / ".join("%s:%s" % (c.get("with", "?"), c.get("why", "")) for c in conf)[:300]
            st = "衝突 · 待人判(VCGC)· " + why
            if e.get("status") != st:
                e["status"] = st
                e["ssot_id"] = ""
                changed += 1
            conflicted.append(ek)
        else:
            if e.get("ssot_id") not in (None, ""):
                pass
            elif "ssot_id" not in e:
                e["ssot_id"] = ""
                changed += 1
    pending = [ek for ek, e in entries.items() if isinstance(e, dict) and str(e.get("status", "")).startswith("暫編")]
    new_reg = None
    if changed:
        nv = _vnum(reg) + 1
        new_reg = reg.with_name("VRN2_Component_Register_v%04d.json" % nv)
        book.update(at=now(), prior=reg.name, writer="%s %s(核號同步)" % (DISPLAY_NAME, TAG), entries=entries)
        new_reg.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    lamp = "YELLOW" if conflicted else "GREEN"
    state = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "apply", "at": now(), "lamp": lamp, "register": (new_reg or reg).name, "prior_register": reg.name if new_reg else None,
             "grant_sources": srcs, "granted": len(granted), "conflicts": len(conflicted), "pending": len(pending), "changed": changed,
             "conflict_keys": conflicted[:50], "pending_keys": pending[:50]}
    (vrn / "contract").mkdir(parents=True, exist_ok=True)
    (vrn / "contract" / STATE_NAME).write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    return state


def request(vrn: Path) -> dict:
    """登記冊 → 核號請求(enriched):暫編條目 + VRN-2 內部自撞。"""
    reg = latest_register(vrn)
    if not reg:
        return {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "request", "at": now(), "lamp": "GRAY", "why": "沒有元件登記冊(先跑啟動器 ⑤)"}
    book = json.loads(reg.read_text(encoding="utf-8"))
    entries = book.get("entries") or {}
    items, prog, seen_key = [], [], {}
    self_conflicts = []
    for ek, e in sorted(entries.items()):
        if not isinstance(e, dict) or str(e.get("status", "")).startswith(("退役", "已確認")):
            continue
        kind = e.get("kind") or ek.split("|", 1)[0]
        item = {"key": e.get("key") or ek, "entry": ek, "kind": kind, "vcgc_kind": VCGC_KIND.get(kind, "SSOT"), "proposed_no": e.get("no"), "ssot_id": e.get("ssot_id") or "",
                "fingerprint": e.get("fp"), "version": e.get("version"), "src": e.get("src"), "status": e.get("status"), "note": e.get("note") or ""}
        (items if kind in REQUEST_KINDS else prog).append(item)
        k2 = (kind, e.get("key"))
        if k2 in seen_key and seen_key[k2] != e.get("fp"):
            self_conflicts.append({"key": e.get("key"), "kind": kind, "fingerprints": [seen_key[k2], e.get("fp")]})
        seen_key.setdefault(k2, e.get("fp"))
    req = {"from": "VRN-2", "subsystem": "VRN-2(VIA-03 VRN 家族 · 獨立 MAIN)", "engine": "%s %s" % (DISPLAY_NAME, TAG), "ts": now(), "register": reg.name,
           "rule": "子系統提出時 ssot_id 空白;VCGC 偵測三系統衝突 → 使用者 + AI 修到無誤 → VCGC 寫 contract/VCGC_NUMBER_GRANT_latest.json {grants:{鍵或暫編號: 核發號}, conflicts:[{key, with, why}]} → VRN-2 apply 自動補填;VRN-2 不寫 VDF / VCGC 的檔",
           "pending": [i["proposed_no"] for i in items + prog if i["proposed_no"]], "ssot_items": items, "program_items": prog, "self_conflicts": self_conflicts,
           "counts": {"ssot_like": len(items), "program": len(prog), "self_conflicts": len(self_conflicts)}}
    (vrn / "contract").mkdir(parents=True, exist_ok=True)
    (vrn / "contract" / REQUEST_NAME).write_text(json.dumps(req, ensure_ascii=False, indent=1), encoding="utf-8")
    req["lamp"] = "YELLOW" if self_conflicts else "GREEN"
    return req


def sync(vrn: Path) -> dict:
    a = apply(vrn)
    r = request(vrn)
    lamp = "RED" if a.get("lamp") == "RED" else ("YELLOW" if "YELLOW" in (a.get("lamp"), r.get("lamp")) else ("GRAY" if a.get("lamp") == "GRAY" else "GREEN"))
    out = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "sync", "at": now(), "lamp": lamp, "apply": a, "request": {k: r[k] for k in ("counts", "pending", "self_conflicts", "register") if k in r}}
    return out


def print_result(r: dict) -> None:
    v = r.get("verb")
    if v == "sync":
        a, q = r["apply"], r["request"]
        if a.get("lamp") == "GRAY":
            say("[計] %s · sync · GRAY · %s" % (r["engine"], a.get("why")))
            return
        say("[計] %s · sync · %s · 核發 %d · 衝突 %d · 待核號 %d(SSOT 類 %d · 程式類 %d)· 自撞 %d · 登記冊 %s%s · 核發冊 %s" % (
            r["engine"], r["lamp"], a["granted"], a["conflicts"], a["pending"], q["counts"]["ssot_like"], q["counts"]["program"], q["counts"]["self_conflicts"],
            a["register"], ("(新版 · 前版 %s)" % a["prior_register"]) if a.get("prior_register") else "", (" · ".join(a["grant_sources"]) or "尚無(VCGC 還沒核發)")))
        for k in a.get("conflict_keys", [])[:8]:
            say("  [YEL] 衝突待人判:%s" % k)
        for c in q.get("self_conflicts", [])[:8]:
            say("  [YEL] VRN-2 內部同鍵不同指紋:%s(%s)" % (c["key"], c["kind"]))
    else:
        say(json.dumps({k: v_ for k, v_ in r.items() if k not in ("ssot_items", "program_items")}, ensure_ascii=False)[:600])


# ===== selftest =====
def selftest() -> int:
    oks, fails = [], []

    def chk(label, cond):
        (oks if cond else fails).append(label)
        say("  [%s] %s" % ("OK" if cond else "FAIL", label))

    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "VIA"
        (root / "supportive modules" / "registry").mkdir(parents=True)
        (root / "functional modules").mkdir(parents=True)
        vrn = root / "functional modules" / "VRN2"
        (vrn / "registry").mkdir(parents=True)
        E = {"SSOT|VRN2_SSOT": {"no": "VRN2-SSOT-0001", "kind": "SSOT", "key": "VRN2_SSOT", "status": "暫編 · 待 VCGC 核號", "fp": "aaa", "version": "v0101", "src": "VRN2_SSOT_v0101.json"},
             "REGEX|VRN_ENG397._TP": {"no": "VRN2-REGEX-0001", "kind": "REGEX", "key": "VRN_ENG397._TP", "status": "暫編 · 待 VCGC 核號", "fp": "bbb", "version": "v0127", "src": "VRN_ENG397_P1Segment_v0127.py"},
             "SYN|VRN_FinLexicon": {"no": "VRN2-SYN-0001", "kind": "SYN", "key": "VRN_FinLexicon", "status": "暫編 · 待 VCGC 核號", "fp": "ccc", "version": "v0107", "src": "VRN_FinLexicon_SSOT_v0107.json"},
             "ENG|VRN_ENG397_P1Segment": {"no": "VRN2-ENG-0001", "kind": "ENG", "key": "VRN_ENG397_P1Segment", "status": "暫編 · 待 VCGC 核號", "fp": "ddd", "version": "v0127", "src": "VRN_ENG397_P1Segment_v0127.py"},
             "SYN|Old": {"no": "VRN2-SYN-0002", "kind": "SYN", "key": "Old", "status": "退役(現役尾版已不含 · 保留不刪)", "fp": "eee"}}
        (vrn / "registry" / "VRN2_Component_Register_v0100.json").write_text(json.dumps({"schema": "VIA.VRN2.ComponentRegister.v1", "entries": E}, ensure_ascii=False), encoding="utf-8")
        r0 = sync(vrn)
        q0 = json.loads((vrn / "contract" / REQUEST_NAME).read_text(encoding="utf-8"))
        chk("① 沒有核發冊:全部待核號 · 請求 SSOT 類 3(SSOT / REGEX / SYN)· 程式類 1 · ssot_id 空白 · 退役不送", r0["lamp"] == "GREEN" and r0["apply"]["pending"] == 4 and q0["counts"]["ssot_like"] == 3 and q0["counts"]["program"] == 1
            and all(i["ssot_id"] == "" for i in q0["ssot_items"]) and "Old" not in json.dumps(q0, ensure_ascii=False) and q0["ssot_items"][0]["vcgc_kind"] in ("SSOT", "RGX", "SYN"))
        chk("①b 沒變就不出新版登記冊(只加 ssot_id 空欄算變 → 出 v0101 一次)", (vrn / "registry" / "VRN2_Component_Register_v0101.json").is_file() and not (vrn / "registry" / "VRN2_Component_Register_v0102.json").is_file())
        r0b = sync(vrn)
        chk("①c 再跑一次:登記冊不再長版", latest_register(vrn).name == "VRN2_Component_Register_v0101.json" and r0b["apply"]["changed"] == 0)
        # VCGC 核發冊:一條用暫編號、一條用鍵;一條衝突
        (root / "VCGC" / "contract").mkdir(parents=True)
        (root / "VCGC" / "contract" / GRANT_NAME).write_text(json.dumps({"ts": now(), "grants": {"VRN2-SSOT-0001": "VIA-03-SSOT-014", "VRN_ENG397._TP": "VIA-03-RGX-007"},
                                                                       "conflicts": [{"key": "VRN_FinLexicon", "with": "VDF", "why": "同義字 '營收' 兩系統定義不同"}]}, ensure_ascii=False), encoding="utf-8")
        r1 = sync(vrn)
        reg = json.loads(latest_register(vrn).read_text(encoding="utf-8"))["entries"]
        chk("② 核發:暫編號鍵 / 原鍵都認 → ssot_id 補填 · 已確認;衝突 → 待人判 · 黃;新版登記冊 v0102", r1["lamp"] == "YELLOW" and reg["SSOT|VRN2_SSOT"]["ssot_id"] == "VIA-03-SSOT-014" and reg["REGEX|VRN_ENG397._TP"]["status"] == "已確認(VCGC)"
            and reg["SYN|VRN_FinLexicon"]["status"].startswith("衝突") and latest_register(vrn).name == "VRN2_Component_Register_v0102.json" and r1["apply"]["granted"] == 2 and r1["apply"]["conflicts"] == 1)
        q1 = json.loads((vrn / "contract" / REQUEST_NAME).read_text(encoding="utf-8"))
        chk("③ 請求只剩沒核發的(衝突的仍在 · 已確認的不再送)· pending 2", {i["key"] for i in q1["ssot_items"]} == {"VRN_FinLexicon"} and len(q1["pending"]) == 2)
        st = json.loads((vrn / "contract" / STATE_NAME).read_text(encoding="utf-8"))
        chk("④ STATE 收據:granted 2 · conflicts 1 · pending 1 · 核發冊來源是 VCGC 的", st["granted"] == 2 and st["conflicts"] == 1 and st["pending"] == 1 and any("VCGC" in s for s in st["grant_sources"]))
        # VRN-2 內部自撞:同鍵不同指紋
        E2 = json.loads(latest_register(vrn).read_text(encoding="utf-8"))
        E2["entries"]["DICT|VRN_Broker"] = {"no": "VRN2-DICT-0001", "kind": "DICT", "key": "VRN_Broker", "status": "暫編 · 待 VCGC 核號", "fp": "f1"}
        E2["entries"]["DICT|VRN_Broker#2"] = {"no": "VRN2-DICT-0002", "kind": "DICT", "key": "VRN_Broker", "status": "暫編 · 待 VCGC 核號", "fp": "f2"}
        (vrn / "registry" / "VRN2_Component_Register_v0103.json").write_text(json.dumps(E2, ensure_ascii=False), encoding="utf-8")
        r2 = sync(vrn)
        chk("⑤ 內部自撞(同鍵不同指紋)→ 列進 self_conflicts · 黃", r2["request"]["counts"]["self_conflicts"] == 1 and r2["lamp"] == "YELLOW")
        chk("⑥ 沒登記冊 → GRAY 不動作", sync(Path(td) / "nowhere")["apply"]["lamp"] == "GRAY")
        chk("⑦ 不寫 VCGC 的檔(核發冊原樣)", json.loads((root / "VCGC" / "contract" / GRANT_NAME).read_text(encoding="utf-8"))["grants"]["VRN2-SSOT-0001"] == "VIA-03-SSOT-014" and not list((root / "VCGC").rglob("VRN2_*")))
    say("[計] %s %s --selftest · OK %d · FAIL %d" % (DISPLAY_NAME, TAG, len(oks), len(fails)))
    return 0 if not fails else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="VRN2_SSOTSync_%s" % TAG)
    ap.add_argument("verb", nargs="?", choices=["sync", "apply", "request"], default="sync")
    ap.add_argument("--vrn", default=None, help="VRN-2 程式夾(登記冊 registry/ 與 contract/ 所在 · 預設本檔所在夾)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    vrn = Path(a.vrn).resolve() if a.vrn else HERE
    r = {"sync": sync, "apply": apply, "request": request}[a.verb](vrn)
    print_result(r)
    return {"GREEN": 0, "YELLOW": 2, "GRAY": 0, "RED": 1}.get(r.get("lamp"), 1)


if __name__ == "__main__":
    sys.exit(main())
