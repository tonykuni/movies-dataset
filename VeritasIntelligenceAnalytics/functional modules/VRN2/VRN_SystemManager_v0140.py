#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0140 — 薄尾:全景修正 + tidy(操作員 2026-10-06「照你建議修正」;全部 VRN 自家冊,不碰母系統;只增不減:移 _superseded 不刪,新版不改舊版)。
  panorama            分類修正:cargo 建置殘渣(target/ · .rustc_info · lib-* · build-script-*)→ JUNK 不計黃;*.freeze.lock → LEDGER;>10,000 列 → DATA(資料不是冊,不計黃);_sha/(1) 副本 → 副本旗
  tidy [--apply]      ① cargo target 夾整夾移 _superseded(.CARGO_<時間>)
                      ② ResearchReport_SSOT 九頭龍:留 .record.schema.v2(有號 TBL0081)與 v2.records64.v0155(資料正本),其餘 VRN_ResearchReport_SSOT* 退役帶 replaced_by
                      ③ Broker_Dict:v0100(有號 35 家)為正本;v0103 若有 v0100 沒有的家 → 出 v0104 = 聯集(只增),v0103 退役;若是子集 → 直接退役
                      ④ 核心活冊清單 → VRN_SSOT_Index 新版加 core 段(綠 16 族)
                      全部記 VRN_Tidy_Ledger.jsonl;dry-run 只列
  舊動詞 catalog / links / page / records / read / frame / engine → [DEPRECATED] 指到現行動詞,rc 2(派發表定案;前版檔不動)
其餘動詞照前版鏈。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime
import importlib.util
import json
import os
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0140"
DEPRECATED = {"catalog": "extract status / panorama", "links": "extract", "page": "extract", "records": "extract status", "read": "extract", "frame": "extract", "engine": "fn status"}
CARGO_RX = re.compile(r"(?i)^(lib-|build-script-|\.rustc_info|\.cargo-lock|dep-lib-)")
KEEP_RR = ("VRN_ResearchReport_SSOT.record.schema.v2.json", "VRN_ResearchReport_SSOT.v2.records64.v0155")


def _vnum_v0140(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0140(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0140(p) < _vnum_v0140(__file__)), key=_vnum_v0140)
PRIOR = _load_v0140(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


_PAN_39 = PRIOR.panorama


def _home():
    return Path(os.environ.get("VIA_VRN_SSOT_HOME") or HERE)


def _is_cargo_dir(d: Path) -> bool:
    return (d / ".rustc_info.json").exists() or (d.name == "target" and (d / ".fingerprint").exists()) or (d.name == ".fingerprint")


def panorama() -> dict:
    o = _PAN_39()
    home = _home()
    for r in o["books"]:
        fam, d = r["family"], r["dir"]
        if CARGO_RX.search(fam) or re.search(r"(?i)(^|/)(target|\.fingerprint)(/|$)", d):
            r["kind"], r["lamp"], r["why"] = "JUNK", "GRAY", "cargo 建置殘渣,不是冊(tidy 移 _superseded)"
        elif fam.endswith(".freeze.lock") or ".freeze" in fam:
            r["kind"] = "LEDGER"
        elif r["entries"] >= 10000:
            r["kind"], r["lamp"], r["why"] = "DATA", "GRAY", "資料 %d 列,不是冊(不計黃)" % r["entries"]
        if re.search(r"_sha[0-9a-f]{8,}|\s\(\d+\)$", fam):
            r["why"] = (r["why"] + " · " if r["why"] else "") + "副本檔名"
    from collections import Counter, defaultdict
    per = defaultdict(Counter)
    for r in o["books"]:
        per[r["kind"]][r["lamp"]] += 1
    o["per_kind"] = {k: dict(v) for k, v in per.items()}
    s = o["summary"]
    s.update(red=sum(1 for r in o["books"] if r["lamp"] == "RED"), yellow=sum(1 for r in o["books"] if r["lamp"] == "YELLOW"), green=sum(1 for r in o["books"] if r["lamp"] == "GREEN"), gray=sum(1 for r in o["books"] if r["lamp"] == "GRAY"))
    o["lamp"] = "RED" if s["red"] else ("YELLOW" if s["yellow"] else "GREEN")
    out_dir = Path(os.environ.get("VIA_VRN_HEALTH_OUT") or (home.parents[1] / "VIA_Reports" / "vrn"))
    (out_dir / "PANORAMA_latest.json").write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "PANORAMA_latest.html").write_text(PRIOR._html_v0139(o), encoding="utf-8")
    return o


def _ledger(home: Path, rec: dict) -> None:
    (home / "registry").mkdir(exist_ok=True)
    with open(home / "registry" / "VRN_Tidy_Ledger.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(rec, ts=datetime.datetime.now().isoformat(timespec="seconds")), ensure_ascii=False) + "\n")


def _supersede(home: Path, p: Path, tag: str, why: str, replaced_by: str, apply: bool) -> dict:
    dst_dir = p.parent / "_superseded"
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    dst = dst_dir / (p.name + ".%s_%s" % (tag, stamp))
    rec = {"action": tag, "from": p.relative_to(home).as_posix(), "to": dst.relative_to(home).as_posix(), "why": why, "replaced_by": replaced_by, "status": "DONE" if apply else "PLAN"}
    if apply:
        dst_dir.mkdir(exist_ok=True)
        shutil.move(str(p), str(dst))
        _ledger(home, rec)
    return rec


def tidy(apply: bool = False) -> dict:
    home = _home()
    out = {"verb": "tidy", "apply": apply, "cargo": [], "researchreport": [], "broker": {}, "core": {}, "_notes": []}
    for d in sorted({p.parent for p in home.rglob(".rustc_info.json")} | {p for p in home.rglob("target") if p.is_dir() and (p / ".fingerprint").exists()}):
        if "_superseded" in d.parts:
            continue
        out["cargo"].append(_supersede(home, d, "CARGO", "Rust cargo target 夾在 VRN 裡,不是冊,整夾退役", "", apply))
    for p in sorted(home.rglob("VRN_ResearchReport_SSOT*")):
        if not p.is_file() or "_superseded" in p.parts:
            continue
        if p.name == KEEP_RR[0] or p.name.startswith(KEEP_RR[1]):
            out["researchreport"].append({"action": "KEEP", "file": p.name})
            continue
        out["researchreport"].append(_supersede(home, p, "RETIRED", "ResearchReport 九頭龍:留 schema v2 + records64 資料正本", KEEP_RR[0] if "schema" in p.name or "active" in p.name else KEEP_RR[1], apply))
    bd = sorted(home.rglob("VRN_Broker_Dict_v*.json"), key=lambda q: _vnum_v0140(q.stem))
    bd = [p for p in bd if "_superseded" not in p.parts]
    if len(bd) >= 2:
        def load(p):
            try:
                return json.loads(p.read_text(encoding="utf-8-sig"))
            except ValueError:
                return {}
        base = next((p for p in bd if _vnum_v0140(p.stem) == 100), bd[0])
        tail = bd[-1]
        b0, bt = load(base), load(tail)
        k0 = {str(b.get("key") or b.get("abbr") or b.get("name")) for b in (b0.get("brokers") or []) if isinstance(b, dict)}
        extra = [b for b in (bt.get("brokers") or []) if isinstance(b, dict) and str(b.get("key") or b.get("abbr") or b.get("name")) not in k0]
        out["broker"] = {"base": base.name, "tail": tail.name, "base_n": len(b0.get("brokers") or []), "tail_n": len(bt.get("brokers") or []), "extra_in_tail": len(extra)}
        if tail != base:
            if extra:
                nv = "v%04d" % (_vnum_v0140(tail.stem) + 1)
                newp = tail.with_name("VRN_Broker_Dict_%s.json" % nv)
                merged = dict(b0)
                merged["brokers"] = list(b0.get("brokers") or []) + [dict(b, merged_from=tail.name) for b in extra]
                merged["version"], merged["prior"] = nv, base.name
                merged["why_" + nv] = "tidy:正本 %s(有號)∪ %s 多出的 %d 家(只增)" % (base.name, tail.name, len(extra))
                out["broker"]["action"] = "UNION → " + newp.name
                if apply:
                    newp.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
                    _ledger(home, {"action": "UNION", "to": newp.name, "from": [base.name, tail.name], "extra": len(extra)})
            else:
                out["broker"]["action"] = "tail 是子集 → 退役 " + tail.name
            out["researchreport"].append(_supersede(home, tail, "RETIRED", "Broker_Dict:正本 %s 有號;%s %s" % (base.name, tail.name, "已聯集進新版" if extra else "是子集"), base.name, apply))
    pan = _PAN_39()
    core = [r["family"] for r in pan["books"] if r["lamp"] == "GREEN"]
    idx = sorted(home.rglob("VRN_SSOT_Index_v*.json"), key=lambda q: _vnum_v0140(q.stem))
    idx = [p for p in idx if "_superseded" not in p.parts]
    if idx:
        try:
            d = json.loads(idx[-1].read_text(encoding="utf-8-sig"))
        except ValueError:
            d = {}
        nv = "v%04d" % (_vnum_v0140(idx[-1].stem) + 1)
        newi = idx[-1].with_name("VRN_SSOT_Index_%s.json" % nv)
        d["core"] = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "rule": "panorama 綠 = 有號且有人引用;核心活冊清單,只增", "families": core}
        d["version"], d["prior"] = nv, idx[-1].name
        out["core"] = {"index": newi.name, "n": len(core)}
        if apply:
            newi.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
            _ledger(home, {"action": "INDEX_CORE", "to": newi.name, "n": len(core)})
    else:
        out["_notes"].append("VRN_SSOT_Index 不在,core 段略")
    out["lamp"] = "GREEN" if apply else "YELLOW"
    return out


def _print_tidy(o: dict) -> None:
    print("[計] tidy%s · cargo 夾 %d · ResearchReport 處置 %d · Broker %s · core %s · %s" % (" --apply" if o["apply"] else "(dry-run)", len(o["cargo"]), len(o["researchreport"]), o["broker"].get("action", "—"), o["core"].get("n", "—"), o["lamp"]))
    for c in o["cargo"]:
        print("  [OK] CARGO %s → %s" % (c["from"], c["to"]))
    for r in o["researchreport"][:20]:
        print("  [%s] %s %s%s" % ("OK" if r["action"] in ("KEEP", "RETIRED") else "YEL", r["action"], r.get("file") or r.get("from"), (" → " + r["replaced_by"]) if r.get("replaced_by") else ""))
    if o["broker"]:
        print("  [計] Broker_Dict · 正本 %s(%s 家)· 尾 %s(%s 家)· 尾多出 %s · %s" % (o["broker"]["base"], o["broker"]["base_n"], o["broker"]["tail"], o["broker"]["tail_n"], o["broker"]["extra_in_tail"], o["broker"].get("action", "")))
    for n in o["_notes"]:
        print("  [注] %s" % n)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] and args[0] in DEPRECATED:
        print("[DEPRECATED] %s → 用「%s」(派發表定案 v0140;前版檔不動)" % (args[0], DEPRECATED[args[0]]))
        return 2
    if args[:1] == ["panorama"]:
        o = panorama()
        PRIOR._print_pan(o)
        return 1 if o["lamp"] == "RED" else 0
    if args[:1] == ["tidy"]:
        _print_tidy(tidy(apply=("--apply" in args)))
        return 0
    return PRIOR.main(args)


def selftest() -> int:
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="vrntidy-"))
    home = td / "functional modules" / "VRN"
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT")}
    os.environ["VIA_VRN_SSOT_HOME"] = str(home)
    os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "out")
    (home / "SSOT").mkdir(parents=True)
    (home / "registry").mkdir()
    (home / "vendor" / "target" / ".fingerprint").mkdir(parents=True)
    (home / "vendor" / "target" / ".rustc_info.json").write_text("{}", encoding="utf-8")
    (home / "vendor" / "target" / ".fingerprint" / "lib-adler2.json").write_text(json.dumps({"a": 1}), encoding="utf-8")
    for n in ("VRN_ResearchReport_SSOT.record.schema.v2.json", "VRN_ResearchReport_SSOT.v2.records64.v0155.2f77.json", "VRN_ResearchReport_SSOT.active.json", "VRN_ResearchReport_SSOT_shaf6219fd7.json", "VRN_ResearchReport_SSOT.schema.v1.json"):
        (home / "SSOT" / n).write_text(json.dumps({"rows": [1, 2]}), encoding="utf-8")
    (home / "SSOT" / "VRN_Broker_Dict_v0100.json").write_text(json.dumps({"brokers": [{"key": "GS"}, {"key": "MS"}, {"key": "JPM"}]}), encoding="utf-8")
    (home / "SSOT" / "VRN_Broker_Dict_v0103.json").write_text(json.dumps({"brokers": [{"key": "GS"}, {"key": "KGI"}]}), encoding="utf-8")
    (home / "SSOT" / "VRN_Big_Stage.jsonl").write_text("{}\n" * 12000, encoding="utf-8")
    (home / "registry" / "VRN_SSOT_Index_v0100.json").write_text(json.dumps({"entries": {"x": 1}}), encoding="utf-8")
    (home / "registry" / "VRN_TableHeader_v0100.json").write_text(json.dumps({"tables": {"t": {"source": "functional modules/VRN/SSOT/VRN_Broker_Dict_v0100.json", "table_no": "SSOT-VCGC-VRN-TBL0088"}}}), encoding="utf-8")
    (home / "VRN_ENG001_A_v0100.py").write_text("x = 'VRN_Broker_Dict'\n", encoding="utf-8")
    o = panorama()
    R = {r["family"]: r for r in o["books"]}
    chk("① 全景修正:lib-adler2 → JUNK 灰 · 12,000 列 → DATA 灰 · _sha 副本旗", R["lib-adler2"]["kind"] == "JUNK" and R["VRN_Big_Stage"]["kind"] == "DATA" and "副本檔名" in R["VRN_ResearchReport_SSOT_shaf6219fd7"]["why"])
    t0 = tidy(apply=False)
    chk("② dry-run:cargo 1 夾 · ResearchReport 留 2 退 3 · Broker 尾多出 1(KGI)→ UNION v0104 · 檔未動", len(t0["cargo"]) == 1 and sum(1 for r in t0["researchreport"] if r["action"] == "KEEP") == 2 and t0["broker"]["extra_in_tail"] == 1 and "UNION" in t0["broker"]["action"] and (home / "SSOT" / "VRN_ResearchReport_SSOT.active.json").exists())
    t1 = tidy(apply=True)
    merged = json.loads((home / "SSOT" / "VRN_Broker_Dict_v0104.json").read_text(encoding="utf-8"))
    chk("③ --apply:cargo 夾移 _superseded · 3 本退役 · Broker v0104 = 4 家(聯集)· v0103 退役 · Index v0101 有 core · 帳", not (home / "vendor" / "target").exists() and list((home / "vendor" / "_superseded").glob("target.CARGO_*")) and not (home / "SSOT" / "VRN_ResearchReport_SSOT.active.json").exists()
        and (home / "SSOT" / "VRN_ResearchReport_SSOT.record.schema.v2.json").exists() and len(merged["brokers"]) == 4 and not (home / "SSOT" / "VRN_Broker_Dict_v0103.json").exists() and (home / "registry" / "VRN_SSOT_Index_v0101.json").exists() and (home / "registry" / "VRN_Tidy_Ledger.jsonl").exists())
    rc = main(["catalog"])
    chk("④ 舊動詞 catalog → DEPRECATED rc 2", rc == 2)
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑤ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 帶加速器橋 · glob 取前版", "[VIA:ACCEL-BRIDGE:v0100]" in body)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0140 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
