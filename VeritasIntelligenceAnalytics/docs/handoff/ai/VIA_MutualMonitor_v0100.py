#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_MutualMonitor v0100 — 五系統互監矩陣(只讀本冊 VIA_SystemReceipt_Contract_SSOT 列的自報收據 · 正規化成同一張燈表 · 契約符合度 · 只增帳)。

操作員 2026-11-09:「VDF VRN VQG VAP 系統獨立架構可運作獨立開發完成,但互動關係要與 VCGC 的相互監控協助先建構完美,因為 VCGC 可能會持續更強化」。
  run       讀契約冊尾版 → 每系統每張收據:在 / 不在 · 燈(照冊 lamp_key + lamp_map)· 時間 · 版本 · 必填欄缺了哪些 · 時效(> stale_hours = STALE)·
            一致性(consistency_with:同系統兩張收據燈要一樣)→ 系統燈 = 該系統非 optional 收據的最差燈(缺 = GRAY · 不是綠)。
            互動表照冊 interactions 原樣攤開(誰只讀誰 · 永不做什麼)。輸出 MUTUAL_latest.json / .md / .html + mutual_ledger.jsonl(只增)。
  selftest  tempfile 假倉 · 燈對映 · 缺必填 · 過期 · 一致性 · GRAY 不升綠 · 不碰 environ · 不起子行程。
邊界:只讀;不跑任何系統的引擎;不改任何收據;他系統的燈只攤開,不代修、不代寫。
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
ENGINE = "VIA_MutualMonitor " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[2] if HERE.name == "ai" else HERE
CONTRACT_GLOB = "supportive modules/registry/VIA_SystemReceipt_Contract_SSOT_v[0-9][0-9][0-9][0-9].json"
ORDER = {"GREEN": 0, "YELLOW": 1, "GRAY": 2, "RED": 3}


def load_contract(via: Path) -> tuple:
    hits = sorted(via.glob(CONTRACT_GLOB))
    if not hits:
        raise FileNotFoundError("契約冊缺 %s" % CONTRACT_GLOB)
    return json.loads(hits[-1].read_text(encoding="utf-8")), hits[-1].name


def parse_at(v) -> datetime | None:
    if not v:
        return None
    s = str(v).strip().replace("Z", "+00:00")
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            d = datetime.strptime(s, fmt)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def first_key(d: dict, keys: list):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def normalize(via: Path, sysname: str, spec: dict, maps: dict, stale_h: float, now: datetime) -> dict:
    p = via / spec["path"]
    row = {"system": sysname, "receipt": spec["id"], "zh": spec.get("zh"), "path": spec["path"], "present": p.is_file(), "optional": bool(spec.get("optional")), "lamp": "GRAY", "raw_lamp": None,
           "at": None, "version": None, "age_hours": None, "stale": False, "missing_required": [], "note": spec.get("note", "")}
    if not p.is_file():
        row["note"] = (row["note"] + " · " if row["note"] else "") + "收據不在(本機沒跑過或系統未落檔)→ GRAY"
        return row
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        row["lamp"], row["note"] = "RED", "收據讀不了 %s" % error
        return row
    if not isinstance(d, dict):
        row["lamp"], row["note"] = "RED", "收據不是 dict"
        return row
    raw = d.get(spec["lamp_key"]) if spec.get("lamp_key") else None
    row["raw_lamp"] = raw
    if spec.get("lamp_key"):
        lm = maps.get(spec.get("lamp_map") or "", {})
        lamp = lm.get(str(raw).upper()) if lm else (str(raw).upper() if str(raw).upper() in ORDER else None)
        row["lamp"] = lamp or ("GRAY" if raw is None else "YELLOW")
        if lamp is None:
            row["note"] = (row["note"] + " · " if row["note"] else "") + "燈值「%s」不在冊的對映 → 當 %s" % (raw, row["lamp"])
    else:
        row["lamp"] = "GREEN"                                   # 無燈欄的純資料收據:在就算有自報
    at = parse_at(first_key(d, spec.get("at_keys") or []))
    row["at"] = at.isoformat() if at else None
    if at:
        row["age_hours"] = round((now - at).total_seconds() / 3600.0, 1)
        row["stale"] = row["age_hours"] > stale_h
    row["version"] = first_key(d, spec.get("version_keys") or [])
    row["missing_required"] = [k for k in spec.get("required") or [] if k not in d]
    if row["missing_required"] and row["lamp"] == "GREEN":
        row["lamp"] = "YELLOW"
    if row["stale"] and row["lamp"] == "GREEN":
        row["lamp"] = "YELLOW"
    return row


def worst(lamps: list) -> str:
    return max(lamps, key=lambda x: ORDER.get(x, 2)) if lamps else "GRAY"


def run(via: Path, out_root: Path) -> dict:
    now = datetime.now(timezone.utc)
    contract, cname = load_contract(via)
    maps = contract.get("lamp_maps") or {}
    stale_h = float(contract.get("stale_hours", 48))
    systems, rows, consistency = {}, [], []
    for sysname, spec in (contract.get("systems") or {}).items():
        srows = [normalize(via, sysname, r, maps, stale_h, now) for r in spec.get("receipts") or []]
        rows.extend(srows)
        by_id = {r["receipt"]: r for r in srows}
        for r in spec.get("receipts") or []:
            if r.get("consistency_with") and r["id"] in by_id and r["consistency_with"] in by_id:
                a, b = by_id[r["id"]], by_id[r["consistency_with"]]
                ok = (not a["present"] or not b["present"]) or a["lamp"] == b["lamp"]
                consistency.append({"system": sysname, "a": r["id"], "b": r["consistency_with"], "consistent": ok, "a_lamp": a["lamp"], "b_lamp": b["lamp"]})
                if not ok:
                    a["lamp"] = worst([a["lamp"], "YELLOW"])
                    a["note"] = (a["note"] + " · " if a["note"] else "") + "與 %s 燈不一致(%s vs %s)" % (r["consistency_with"], a["raw_lamp"], b["raw_lamp"])
        mandatory = [r for r in srows if not r["optional"]]
        entry = sorted(p for p in via.glob(spec.get("entry_glob", "")) if p.is_file())
        systems[sysname] = {"zh": spec.get("zh"), "entry_tail": entry[-1].name if entry else None, "lamp": worst([r["lamp"] for r in mandatory]) if mandatory else "GRAY",
                            "receipts": len(srows), "present": sum(1 for r in srows if r["present"]), "missing": [r["receipt"] for r in srows if not r["present"]],
                            "stale": [r["receipt"] for r in srows if r["stale"]], "contract_conformance": {"required_ok": sum(1 for r in srows if r["present"] and not r["missing_required"]), "present": sum(1 for r in srows if r["present"])}}
    overall = worst([s["lamp"] for s in systems.values()])
    rec = {"engine": ENGINE, "at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "contract": cname, "law": contract.get("law"), "lamp": overall, "systems": systems, "receipts": rows, "consistency": consistency,
           "interactions": contract.get("interactions") or [], "gray_means": "缺收據 = GRAY(不是綠 · 不是紅):該系統沒自報或本機沒跑過;VCGC 不代寫",
           "meaning": "五系統各自自報 · VCGC 只讀攤開:%s" % " · ".join("%s %s" % (k, v["lamp"]) for k, v in systems.items())}
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "MUTUAL_latest.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    with (out_root / "mutual_ledger.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": rec["at"], "lamp": overall, "systems": {k: v["lamp"] for k, v in systems.items()}, "contract": cname}, ensure_ascii=False) + "\n")
    L = ["# 五系統互監矩陣 · %s · %s · **%s**" % (ENGINE, rec["at"], overall), "", rec["law"] or "", "", "| 系統 | 燈 | 入口尾版 | 收據 在/總 | 缺 | 過期 | 必填齊 |", "|---|---|---|---|---|---|---|"]
    for k, v in systems.items():
        L.append("| %s %s | %s | %s | %d/%d | %s | %s | %d/%d |" % (k, v["zh"], v["lamp"], v["entry_tail"] or "—", v["present"], v["receipts"], ",".join(v["missing"]) or "—", ",".join(v["stale"]) or "—", v["contract_conformance"]["required_ok"], v["contract_conformance"]["present"]))
    L += ["", "## 收據", "", "| 系統 | 收據 | 在 | 燈(原值) | 時間 | 版本 | 缺必填 | 備註 |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append("| %s | %s %s | %s | %s(%s) | %s%s | %s | %s | %s |" % (r["system"], r["receipt"], r["zh"] or "", "在" if r["present"] else "—", r["lamp"], r["raw_lamp"], r["at"] or "—", (" · %s h" % r["age_hours"]) if r["age_hours"] is not None else "", r["version"] or "—", ",".join(r["missing_required"]) or "—", (r["note"] or "").replace("|", "/")[:100]))
    L += ["", "## 互動(只讀 · 永不)", "", "| 從 | 到 | 模式 | 看什麼 | 永不 |", "|---|---|---|---|---|"] + ["| %s | %s | %s | %s | %s |" % (i["from"], i["to"], i["mode"], i["what"], i["never"]) for i in rec["interactions"]]
    L += ["", rec["gray_means"]]
    (out_root / "MUTUAL_latest.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    color = {"GREEN": "#2f7d4f", "YELLOW": "#b8860b", "RED": "#a83232", "GRAY": "#777"}
    H = ["<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VIA 互監矩陣</title><style>body{font:13px/1.5 system-ui,sans-serif;margin:24px;color:#222;background:#faf8f3}table{border-collapse:collapse;margin:8px 0 20px}td,th{border:1px solid #ddd;padding:4px 8px;text-align:left}th{background:#efece4}.l{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}</style></head><body>",
         "<h1>VIA 五系統互監矩陣 · %s</h1><p>%s · 整體 <span class='l' style='background:%s'></span>%s</p><p>%s</p>" % (html.escape(ENGINE), rec["at"], color[overall], overall, html.escape(rec["law"] or "")),
         "<table><tr><th>系統</th><th>燈</th><th>入口尾版</th><th>收據</th><th>缺</th><th>過期</th></tr>"]
    for k, v in systems.items():
        H.append("<tr><td>%s %s</td><td><span class='l' style='background:%s'></span>%s</td><td>%s</td><td>%d/%d</td><td>%s</td><td>%s</td></tr>" % (k, html.escape(v["zh"] or ""), color[v["lamp"]], v["lamp"], html.escape(v["entry_tail"] or "—"), v["present"], v["receipts"], html.escape(",".join(v["missing"]) or "—"), html.escape(",".join(v["stale"]) or "—")))
    H.append("</table><table><tr><th>系統</th><th>收據</th><th>在</th><th>燈</th><th>時間</th><th>版本</th><th>缺必填</th><th>備註</th></tr>")
    for r in rows:
        H.append("<tr><td>%s</td><td>%s</td><td>%s</td><td><span class='l' style='background:%s'></span>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (r["system"], html.escape("%s %s" % (r["receipt"], r["zh"] or "")), "在" if r["present"] else "—", color[r["lamp"]], html.escape("%s(%s)" % (r["lamp"], r["raw_lamp"])), html.escape(str(r["at"] or "—")), html.escape(str(r["version"] or "—")), html.escape(",".join(r["missing_required"]) or "—"), html.escape((r["note"] or "")[:120])))
    H.append("</table><p>%s</p></body></html>" % html.escape(rec["gray_means"]))
    (out_root / "MUTUAL_latest.html").write_text("\n".join(H), encoding="utf-8")
    return rec


def selftest() -> int:
    checks = []

    def chk(name, cond, note=""):
        checks.append((name, bool(cond), note))
        print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, (" · " + note) if note else ""), flush=True)
    env_before = dict(os.environ)
    real = sorted(VIA.glob(CONTRACT_GLOB))
    chk("① 本倉契約冊在 · 五系統都有節 · 每張收據有 path / lamp_key / required", bool(real) and set(json.loads(real[-1].read_text(encoding="utf-8"))["systems"]) == {"VCGC", "VDF", "VRN2", "VQG", "VAP"}
        and all(("path" in r and "lamp_key" in r and "required" in r) for s in json.loads(real[-1].read_text(encoding="utf-8"))["systems"].values() for r in s["receipts"]))
    with tempfile.TemporaryDirectory(prefix="mutual_") as td:
        via = Path(td)
        (via / "supportive modules/registry").mkdir(parents=True)
        (via / "supportive modules/registry" / real[-1].name).write_text(real[-1].read_text(encoding="utf-8"), encoding="utf-8")
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        w = lambda rel, obj: ((via / rel).parent.mkdir(parents=True, exist_ok=True), (via / rel).write_text(json.dumps(obj), encoding="utf-8"))  # noqa: E731
        w("VIA_Reports/vcgc/TEST_latest.json", {"lamp": "YELLOW", "at": now, "console": "CGC_MDL149_v0192.py", "counts": {}})
        w("VIA_Reports/vdf/HEALTH_latest.json", {"lamp": "YELLOW", "ts": now, "summary": {}})
        w("VIA_Reports/vdf/activate/VDF_ACTIVATE_latest.json", {"overall": "RED", "ts": "2026-01-01T00:00:00", "engine": "VDF_SystemManager v0129", "steps": []})
        w("VIA_Reports/vrn2/VRN2_CloseoutUI_latest.json", {"state": "OPEN", "at": now, "per_owner": {}, "counts": {}})
        w("VIA_Reports/vrn2/VRN2_Activate_latest.json", {"lamp": "RED", "version": "ActivateVRN-2 v0178"})
        w("VIA_Reports/vqg/VQG_ExportVAP_latest.json", {"lamp": "YELLOW", "at": now, "engine": "VeritaQuantGuard v0108", "tables": [], "vap_sources": 4})
        w("VIA_Reports/vqg/vap_export/latest.json", {"lamp": "GREEN", "at": now, "export_dir": "x", "vap_sources": 4})
        out = via / "VIA_Reports" / "mutual"
        rec = run(via, out)
        S = rec["systems"]
        chk("② 燈對映:VRN2 OPEN→RED · VDF overall RED→RED(activate)· VCGC YELLOW · VAP 缺收據 → GRAY(不是綠)", S["VRN2"]["lamp"] == "RED" and S["VDF"]["lamp"] == "RED" and S["VCGC"]["lamp"] == "YELLOW" and S["VAP"]["lamp"] == "GRAY")
        rr = {(r["system"], r["receipt"]): r for r in rec["receipts"]}
        chk("③ 過期:VDF activate 2026-01-01 → stale · 標在系統 stale 清單", rr[("VDF", "activate")]["stale"] is True and "activate" in S["VDF"]["stale"])
        chk("④ 一致性:VQG vap_latest GREEN vs export_vap YELLOW → 不一致 → vap_latest 降黃 · consistency 記錄", any(c["system"] == "VQG" and not c["consistent"] for c in rec["consistency"]) and rr[("VQG", "vap_latest")]["lamp"] == "YELLOW")
        chk("⑤ 必填:VRN2 activate 缺 at 欄不算缺(at_keys 非必填)· required 齊 → 燈照原值 RED", rr[("VRN2", "activate")]["missing_required"] == [] and rr[("VRN2", "activate")]["lamp"] == "RED")
        chk("⑥ 整體燈 = 最差(RED)· 三種輸出 + 只增帳", rec["lamp"] == "RED" and (out / "MUTUAL_latest.md").is_file() and (out / "MUTUAL_latest.html").is_file() and (out / "mutual_ledger.jsonl").read_text(encoding="utf-8").count("\n") == 1)
        w("VIA_Reports/vqg/VQG_ExportVAP_latest.json", {"lamp": "GREEN", "at": now, "engine": "VeritaQuantGuard v0108", "tables": [], "vap_sources": 4})
        w("VIA_Reports/vqg/VQG_Closeout_latest.json", {"lamp": "GREEN", "at": now, "engine": "x"})
        rec2 = run(via, out)
        chk("⑦ VQG 兩張都綠 · optional closeout 在 → VQG GREEN;帳 +1 列", rec2["systems"]["VQG"]["lamp"] == "GREEN" and (out / "mutual_ledger.jsonl").read_text(encoding="utf-8").count("\n") == 2)
        chk("⑧ 互動表照冊攤開(≥ 6 條 · 每條有 never)", len(rec2["interactions"]) >= 6 and all(i.get("never") for i in rec2["interactions"]))
        src = Path(__file__).read_text(encoding="utf-8")
        chk("⑨ 邊界:不起子行程 · 不連網 · 不寫 environ · 只讀收據", re.search(r"^\s*(import|from)\s+(subprocess|urllib|requests)\b", src, re.M) is None and not re.findall(r"os\.environ\[[^\]]+\]\s*=", src) and dict(os.environ) == env_before)
    n = sum(1 for _, ok, _ in checks if ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(checks) else "FAIL", ENGINE, n, len(checks)), flush=True)
    return 0 if n == len(checks) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv or argv[:1] == ["selftest"]:                      # VCGC 站表 / 交接案用 --selftest 旗標
        return selftest()
    ap = argparse.ArgumentParser(prog="VIA_MutualMonitor_v0100.py", description=__doc__.split("\n")[0])
    ap.add_argument("verb", choices=["run", "selftest"])
    ap.add_argument("--via", default=None)
    ap.add_argument("--out", default=None, help="輸出夾(預設 <VIA>/VIA_Reports/mutual)")
    args = ap.parse_args(argv)
    if args.verb == "selftest":
        return selftest()
    via = Path(args.via).resolve() if args.via else VIA
    out = Path(args.out) if args.out else via / "VIA_Reports" / "mutual"
    try:
        rec = run(via, out)
    except FileNotFoundError as error:
        print("[RED] %s · %s" % (ENGINE, error), flush=True)
        return 2
    print("[%s] %s · %s → %s" % (rec["lamp"], ENGINE, rec["meaning"], out / "MUTUAL_latest.md"), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
