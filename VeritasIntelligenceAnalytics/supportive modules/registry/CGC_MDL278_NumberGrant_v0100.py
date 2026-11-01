#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL278_NumberGrant v0100 — VCGC 收件:子系統(VDF · VRN-2 · VRN)的核號請求 → 候選冊 → CGC_MDL237 中央檢測與發號 → 核發冊

操作員政策(2026-10-29;2026-11-01 重申):「SSOT REGEX 同義字 邏輯 政策等由 VDF VRN 生成 · 經 VCGC 檢測後無衝突給予編號 · VDF VRN 自動擷取編號 ·
  若有衝突由我跟 AI 解決後 VCGC 檢測無誤後給予編號及更新修正內容 · 子系統自動識別編號及更新內容 · 三個系統的 SSOT REGEX 同義字 政策 邏輯的帳本是相同的」。
這是 VCGC 自己的模組(四系統對等,L123):只讀子系統的請求檔,不寫 VDF / VRN-2 / VRN 的任何檔。
本檔不發號:號只由 CGC_MDL237 中央編號(VIA_Numbering_SSOT / VIA_NumberBooks;VIA-<子系統>-<類>NNN)發,三系統共用這一本帳
(CGC_MDL237 v0114「reuse central allocator, never invent IDs」)。本檔做三件事:
  check(預設,零寫):蒐集請求 → 候選契約驗證(CGC_MDL237 validate_candidate)→ 跨系統衝突(中央檢測只比同 owner 同 scope;
       這裡補:同一別名在不同系統對到不同目標 · 同一正則語意鍵在不同系統寫法不同)→ 合併進候選冊試算 → CGC_MDL237 make_plan 檢測。
  intake --apply:合併後的候選冊寫成新版號檔 VIA_AssetCandidates_SSOT_vNNNN.json(舊資產照留;同身分換新版;契約不合 / 跨系統衝突的不收)。
       之後:提交候選冊 → via-vcgc run CGC_MDL237_NumberingSystem manager sync --apply(中央發號,唯一寫號者)。
  grant --apply:讀中央已發的號 → VCGC_NUMBER_GRANT_latest.json({grants:{登記鍵 · 候選編號 · 暫編號: 中央號},
       assets:{登記鍵: {code, version, source_sha256}}, conflicts:[{key, system, with, why}]};內容沒變不重寫;來源記相對路徑)。
       子系統各自用自己的 SSOTSync apply 讀(VDF_SSOTSync · VRN2_SSOTSync)。
  請求檔:<VIA>/functional modules/*/contract/*_NUMBER_REQUEST_latest.json · <VIA>/VCGC/contract/;條目要附 asset(候選契約)才收,
       沒附的照實列「無候選契約」(待該系統升級)。
零網路;不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib。
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

import datetime
import importlib.util
import json
import re
import sys
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
ENGINE = "CGC_MDL278_NumberGrant"
TAG = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
GRANT_NAME = "VCGC_NUMBER_GRANT_latest.json"
CENTRAL_GLOB = "CGC_MDL237_NumberingSystem_v[0-9][0-9][0-9][0-9].py"
SYS_OWNER = {"VDF": "VDF", "VRN-2": "VRN", "VRN2": "VRN", "VRN": "VRN", "VCGC": "VCGC"}
SYNC_SOURCE = re.compile(r"^[a-z0-9]+-ssotsync:")       # 子系統 SSOTSync 送來的候選(其餘是操作員提案,不進核發冊)
_C = None


def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def central():
    """CGC_MDL237 中央編號尾版(VCGC 自己的模組;只用它的候選契約 · 檢測 · 中央狀態讀取)。"""
    global _C
    if _C is None:
        hits = sorted(HERE.glob(CENTRAL_GLOB), key=_vnum)
        if not hits:
            raise RuntimeError("找不到 CGC_MDL237_NumberingSystem 尾版")
        sp = importlib.util.spec_from_file_location("_vcgc278_central_" + hits[-1].stem, hits[-1])
        mod = importlib.util.module_from_spec(sp)
        sys.modules[sp.name] = mod
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            sp.loader.exec_module(mod)
        _C = mod
    return _C


def _rel(f, via: Path) -> str:
    """VIA 樹內相對路徑(正斜線):核發冊入版控,不寫本機絕對路徑(工作站 / 容器同一份)。"""
    try:
        return Path(f).resolve().relative_to(Path(via).resolve()).as_posix()
    except ValueError:
        return Path(f).name


def request_files(via: Path = VIA) -> list:
    out = sorted((via / "functional modules").glob("*/contract/*_NUMBER_REQUEST_latest.json"))
    out += sorted((via / "VCGC" / "contract").glob("*_NUMBER_REQUEST_latest.json")) if (via / "VCGC" / "contract").is_dir() else []
    return out


def load_requests(via: Path = VIA) -> list:
    reqs = []
    for f in request_files(via):
        try:
            r = json.loads(f.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            reqs.append({"from": f.parent.parent.name, "file": str(f), "error": "%s: %s" % (type(exc).__name__, exc), "items": [], "no_contract": 0})
            continue
        raw = [x for x in list(r.get("ssot_items") or []) + list(r.get("program_items") or []) if isinstance(x, dict)]
        items = [x for x in raw if isinstance(x.get("asset"), dict) and x.get("key")]
        no_contract = len(raw) - len(items) if raw else len([x for x in r.get("pending") or [] if isinstance(x, str)])
        reqs.append({"from": r.get("from") or f.parent.parent.name, "file": str(f), "items": items, "no_contract": no_contract,
                     "self_conflicts": r.get("self_conflicts") or []})
    return reqs


def newest_book(book_dir: Path) -> Path | None:
    hits = sorted(Path(book_dir).glob(central().BOOK_PATTERN), key=_vnum)
    return hits[-1] if hits else None


def cross_conflicts(items: list) -> list:
    """中央檢測只比同 owner 同 scope;三系統共用帳本要再比跨系統:同一別名 → 不同目標 · 同一正則語意鍵 → 不同寫法。"""
    C, out = central(), []
    groups = {}
    for it in items:
        a = it["asset"]
        if a["asset_type"] == "SYNONYM":
            for w in a["aliases"]:
                groups.setdefault(("SYN", C.normalized(w)), []).append(it)
        elif a["asset_type"] == "REGEX":
            groups.setdefault(("RGX", C.normalized(a["semantic_key"])), []).append(it)
    for (kind, term), grp in sorted(groups.items()):
        systems = {g["_sys"] for g in grp}
        vals = {C.normalized(str(g["asset"]["value"])) if kind == "SYN" else str(g["asset"]["value"]) for g in grp}
        if len(systems) > 1 and len(vals) > 1:
            for g in grp:
                others = sorted({"%s:%s" % (o["_sys"], o["asset"]["value"]) for o in grp if o["_sys"] != g["_sys"]})
                out.append({"key": g["key"], "system": g["_sys"], "with": " / ".join(others)[:200],
                            "why": ("同一別名 %s 在不同系統對到不同目標" if kind == "SYN" else "同一正則語意鍵 %s 在不同系統寫法不同") % term})
    return out


def plan(via: Path = VIA, book_dir: Path = HERE, registered: list | None = None, legacy: list | None = None) -> dict:
    C = central()
    bp = newest_book(book_dir)
    prior = C.read_book(bp) if bp else {"schema": "VIA.AssetCandidates.v1", "version": "1.0.0", "assets": []}
    reqs = load_requests(via)
    items = [dict(it, _sys=rq["from"]) for rq in reqs for it in rq["items"]]
    conflicts, bad = [], set()

    def conflict(it, with_, why):
        conflicts.append({"key": it["key"], "system": it["_sys"], "proposed_no": it.get("proposed_no"), "with": with_, "why": why})
        bad.add((it["_sys"], it["key"]))
    for it in items:
        try:
            C.validate_candidate(it["asset"])
        except (ValueError, TypeError, KeyError) as exc:
            conflict(it, "VCGC 候選契約(CGC_MDL237)", "候選契約不合:%s" % exc)
            continue
        if it["asset"]["owner"] != SYS_OWNER.get(it["_sys"], it["asset"]["owner"]):
            conflict(it, "VCGC 收件", "owner %s 不是送件系統 %s" % (it["asset"]["owner"], it["_sys"]))
    cross = cross_conflicts([it for it in items if (it["_sys"], it["key"]) not in bad])
    for c in cross:
        conflicts.append(dict(c, proposed_no=None))
        bad.add((c["system"], c["key"]))
    merged = list(prior["assets"])
    index = {C.identity(a): i for i, a in enumerate(merged)}
    added = replaced = 0
    good = [it for it in items if (it["_sys"], it["key"]) not in bad]
    for it in good:
        a, idn = it["asset"], C.identity(it["asset"])
        if idn not in index:
            index[idn] = len(merged)
            merged.append(a)
            added += 1
        elif merged[index[idn]] != a:
            merged[index[idn]] = a
            replaced += 1
    over = len(merged) > C.MAX_CANDIDATES
    if registered is None:
        registered = list(C.BASE.load_state()["rows"].values())
        legacy = [r for r in registered if not r.get("asset_intake") and r.get("kind") in ("SYN", "RGX")]
    cp = C.make_plan(merged[:C.MAX_CANDIDATES], registered, legacy or [])
    res = {C.identity(a): r for a, r in zip(merged, cp["results"])}
    states = {}
    for it in good:
        r = res.get(C.identity(it["asset"])) or {"state": "OVER_LIMIT", "reasons": ["CANDIDATE_LIMIT"]}
        states[r["state"]] = states.get(r["state"], 0) + 1
        if r["state"] not in ("READY", "REGISTERED"):
            conflict(it, "VCGC 中央檢測(CGC_MDL237)", "%s:%s" % (r["state"], " · ".join(r.get("reasons") or [])))
    return {"requests": [{"from": r["from"], "file": r["file"], "items": len(r["items"]), "no_contract": r.get("no_contract", 0), "error": r.get("error")}
                         for r in reqs],
            "items": items, "conflicts": conflicts, "cross": len(cross), "states": states, "prior_book": bp, "prior": prior, "merged": merged,
            "added": added, "replaced": replaced, "over_limit": over, "registered": registered}


def intake(via: Path = VIA, apply: bool = False, book_dir: Path = HERE, registered: list | None = None, legacy: list | None = None) -> dict:
    p = plan(via, book_dir, registered, legacy)
    changed = p["merged"] != p["prior"]["assets"]
    out = None
    if apply and changed and not p["over_limit"]:
        bp = p["prior_book"]
        out = Path(book_dir) / ("VIA_AssetCandidates_SSOT_v%04d.json" % ((_vnum(bp) + 1) if bp else 100))
        m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(p["prior"].get("version") or "1.0.0"))
        ver = "%d.%d.0" % (int(m.group(1)), int(m.group(2)) + 1) if (m and bp) else "1.0.0"
        out.write_text(json.dumps({"schema": "VIA.AssetCandidates.v1", "version": ver, "assets": p["merged"]}, ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
    p.update(verb="intake", changed=changed, applied=apply, book_out=str(out) if out else None)
    p["line"] = _line(p, via, ("候選冊寫成 %s(下一步:提交 → via-vcgc run CGC_MDL237_NumberingSystem manager sync --apply)" % out.name) if out else
                      ("超過候選上限 %d,不寫" % central().MAX_CANDIDATES if p["over_limit"] else ("候選冊不變" if apply else "乾跑(--apply 才寫)")))
    return p


def central_codes(registered: list) -> dict:
    """中央已發的子系統候選號:登記鍵(source_pointer)→ 最新版的 {code, version, source_sha256, candidate_id, source_id}。"""
    C, latest = central(), {}
    for r in registered:
        ca = r.get("candidate_asset")
        if not (r.get("asset_intake") and isinstance(ca, dict) and SYNC_SOURCE.match(str(ca.get("source_id") or ""))):
            continue
        k = str(ca.get("source_pointer"))
        if k not in latest or C.version_key(ca["version"]) > C.version_key(latest[k]["version"]):
            latest[k] = {"code": r.get("code"), "version": ca["version"], "source_sha256": ca.get("source_sha256"), "candidate_id": ca.get("candidate_id"),
                         "source_id": ca.get("source_id")}
    return latest


def grant(via: Path = VIA, apply: bool = False, grant_path: Path | None = None, book_dir: Path = HERE, registered: list | None = None,
          legacy: list | None = None) -> dict:
    p = plan(via, book_dir, registered, legacy)
    gp = Path(grant_path or (HERE / GRANT_NAME))
    codes = central_codes(p["registered"])
    grants, assets = {}, {}
    for k, v in sorted(codes.items()):
        grants[k] = v["code"]
        grants[v["candidate_id"]] = v["code"]
        assets[k] = {"code": v["code"], "version": v["version"], "source_sha256": v["source_sha256"]}
    for it in p["items"]:
        if it["key"] in codes and it.get("proposed_no"):
            grants[it["proposed_no"]] = codes[it["key"]]["code"]
    srcs = sorted(_rel(r["file"], via) for r in p["requests"])
    body = {"grants": dict(sorted(grants.items())), "assets": dict(sorted(assets.items())), "conflicts": p["conflicts"]}
    old = {}
    if gp.is_file():
        try:
            old = json.loads(gp.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            old = {"_unreadable": True}                          # 讀不到 → 視為有變,重寫(舊檔不是正本;中央號才是)
    changed = any(body[k] != (old.get(k) or ({} if k != "conflicts" else [])) for k in body) or srcs != (old.get("sources") or [])
    if apply and changed:
        gp.parent.mkdir(parents=True, exist_ok=True)
        gp.write_text(json.dumps(dict({"schema": "VIA.VCGC.NumberGrant.v2", "engine": "%s %s" % (ENGINE, TAG), "ts": now(),
                                       "rule": "號只由 CGC_MDL237 中央編號發(三系統共用一本帳);本冊是中央號的投影:登記鍵 / 候選編號 / 暫編號 → 中央號;"
                                               "assets 給版本與內容指紋(子系統對得上才確認);conflicts = 跨系統衝突 · 契約不合 · 中央檢測擋下(人 + AI 修好後重跑)",
                                       "sources": srcs}, **body), ensure_ascii=False, indent=1), encoding="utf-8")
    p.update(verb="grant", changed=changed, applied=apply, grant_file=str(gp), central_codes=len(codes))
    p["line"] = _line(p, via, ("寫入核發冊" if changed else "核發冊不變") if apply else "乾跑(--apply 才寫)")
    return p


def _line(p: dict, via: Path, tail: str) -> str:
    warn = p["conflicts"] or p["over_limit"] or any(r.get("no_contract") or r.get("error") for r in p["requests"])
    reqs = " · ".join("%s %d%s%s" % (r["from"], r["items"], " · 無候選契約 %d(待該系統升級)" % r["no_contract"] if r.get("no_contract") else "",
                                      " · 讀不到 %s" % r["error"] if r.get("error") else "") for r in p["requests"]) or "無"
    st = " · ".join("%s %d" % kv for kv in sorted(p["states"].items())) or "—"
    extra = " · 中央號 %d" % p["central_codes"] if "central_codes" in p else ""
    return "[VCGC 核號] %s · 請求 %d 份(%s)· 候選冊 %s %d → %d(新 %d · 改 %d)· 中央檢測 %s · 衝突待人判 %d(跨系統 %d)%s · %s" % (
        "YELLOW" if warn else "GREEN", len(p["requests"]), reqs, p["prior_book"].name if p["prior_book"] else "無", len(p["prior"]["assets"]),
        len(p["merged"]), p["added"], p["replaced"], st, len(p["conflicts"]), p["cross"], extra, tail)


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    verb = a[0] if a and not a[0].startswith("--") else "check"
    if verb not in ("check", "intake", "grant"):
        print("用法:python %s check | intake [--apply] | grant [--apply] [--json] · --selftest" % Path(__file__).name)
        return 2
    if verb == "grant":
        r = grant(apply="--apply" in a)
    else:
        r = intake(apply=(verb == "intake" and "--apply" in a))
    if "--json" in a:
        print(json.dumps({k: v for k, v in r.items() if k not in ("items", "merged", "prior", "registered")}, ensure_ascii=False, indent=1, default=str))
    else:
        print(r["line"])
        for c in r["conflicts"][:30]:
            print("  [待人判] %s · %s · 對 %s · %s" % (c["system"], c["key"], c["with"], c["why"]))
    return 0


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s %s · 自測(兩系統請求 → 契約 / 跨系統衝突 → 候選冊 → 中央檢測 → 中央號投影)===" % (ENGINE, TAG))
    C = central()
    chk("① 中央編號尾版在(%s)· 有候選契約 / 檢測 / 身分函式" % Path(C.__file__).name,
        all(callable(getattr(C, n, None)) for n in ("validate_candidate", "make_plan", "identity", "read_book", "normalized", "version_key")))

    def asset(sys_, key, atype, scope, skey, value, aliases=(), pos=(), neg=(), version="1.0.0", **kw):
        a = {"candidate_id": re.sub(r"[^A-Za-z0-9_.:-]", "_", key), "ssot_code": None, "asset_type": atype, "owner": SYS_OWNER[sys_],
             "source_id": "%s-ssotsync:Register" % sys_.lower().replace("-", ""), "source_pointer": key, "source_sha256": format(abs(hash(key + str(value))), "x").rjust(64, "0")[:64],
             "version": version, "supersedes": None, "scope": scope, "semantic_key": skey, "name": "%s %s" % (sys_, skey), "value": value,
             "risk_level": "LOW", "environment": "via_core", "libraries": [], "aliases": list(aliases), "positive": list(pos), "negative": list(neg)}
        a.update(kw)
        return a
    tmp = Path(tempfile.mkdtemp(prefix="vcgc_ng278_"))
    try:
        via = tmp / "VIA"
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        prior_asset = asset("VDF", "operator:twse_start", "INPT", "daily.start", "start_date", "2026-01-02", source_id="operator-proposal:1")
        (reg / "VIA_AssetCandidates_SSOT_v0100.json").write_text(json.dumps({"schema": "VIA.AssetCandidates.v1", "version": "1.0.0", "assets": [prior_asset]}),
                                                                encoding="utf-8")

        def req(sys_, folder, items):
            d = via / "functional modules" / folder / "contract"
            d.mkdir(parents=True, exist_ok=True)
            (d / ("%s_NUMBER_REQUEST_latest.json" % folder)).write_text(json.dumps({"from": sys_, "ssot_items": items}), encoding="utf-8")
        vdf_items = [
            {"key": "VDF:SYN:START_DATE", "proposed_no": "VDF-SYN-0001", "asset": asset("VDF", "VDF:SYN:START_DATE", "SYNONYM", "vdf.unified_alias", "START_DATE",
                                                                                     "time.start_date", aliases=["START_DATE"])},
            {"key": "VDF:SYN:TIMEOUT", "proposed_no": "VDF-SYN-0002", "asset": asset("VDF", "VDF:SYN:TIMEOUT", "SYNONYM", "vdf.unified_alias", "TIMEOUT",
                                                                                  "fetch.timeout_s", aliases=["TIMEOUT"])},
            {"key": "VDF:RGX:IN-01", "proposed_no": "VDF-RGX-0001", "asset": asset("VDF", "VDF:RGX:IN-01", "REGEX", "vdf.regex.code", "IN-01", "^[1-9][0-9]{3}$",
                                                                                pos=["2330"], neg=["0050"])},
            {"key": "VDF:RGX:IN-02", "proposed_no": "VDF-RGX-0002", "asset": asset("VDF", "VDF:RGX:IN-02", "REGEX", "vdf.regex.code", "IN-02", "^00[0-9]{3}A$")},
            {"key": "VDF:PRM:BAD", "proposed_no": "VDF-PRM-0001", "asset": asset("VDF", "VDF:PRM:BAD", "CNFG", "vdf.param", "BAD", 1, ssot_code="VIA-VDF-PRMT001")},
            {"key": "VDF:PRM:TIMEOUT_S", "proposed_no": "VDF-PRM-0002", "asset": asset("VDF", "VDF:PRM:TIMEOUT_S", "CNFG", "vdf.param", "TIMEOUT_S", 30)}]
        req("VDF", "VDF", vdf_items)
        req("VRN-2", "VRN2", [{"key": "SYN|timeout", "proposed_no": "VRN2-SYN-0001",
                               "asset": asset("VRN-2", "SYN|timeout", "SYNONYM", "vrn2.alias", "timeout", "http.timeout", aliases=["timeout"])}])
        (via / "functional modules" / "VRN" / "contract").mkdir(parents=True)
        (via / "functional modules" / "VRN" / "contract" / "VRN_NUMBER_REQUEST_latest.json").write_text(json.dumps({"from": "VRN", "pending": ["VRN-E-0001"]}),
                                                                                                         encoding="utf-8")
        r = intake(via, apply=False, book_dir=reg, registered=[], legacy=[])
        why = {(c["system"], c["key"]): c["why"] for c in r["conflicts"]}
        chk("② 跨系統衝突:同一別名 TIMEOUT 在 VDF → fetch.timeout_s、VRN-2 → http.timeout → 兩邊都不收、列待人判(中央檢測只比同 owner 同 scope,這裡補)",
            "不同目標" in why.get(("VDF", "VDF:SYN:TIMEOUT"), "") and "不同目標" in why.get(("VRN-2", "SYN|timeout"), ""), why)
        chk("③ 契約不合不收:子系統自填中央號(CENTRAL_CODE_MUST_BE_NULL)· 正則沒附正反例(REGEX_CONTRACT)",
            "CENTRAL_CODE_MUST_BE_NULL" in why.get(("VDF", "VDF:PRM:BAD"), "") and "REGEX_CONTRACT" in why.get(("VDF", "VDF:RGX:IN-02"), ""), why)
        chk("④ 中央檢測(CGC_MDL237 make_plan):其餘 READY %s · 舊格式(只有 pending 號)照實列「無候選契約」· 黃燈" % r["states"],
            r["states"].get("READY") == 3 and "無候選契約 1" in r["line"] and r["line"].startswith("[VCGC 核號] YELLOW"), r["line"])
        r2 = intake(via, apply=True, book_dir=reg, registered=[], legacy=[])
        book = json.loads((reg / "VIA_AssetCandidates_SSOT_v0101.json").read_text(encoding="utf-8"))
        ids = [a["candidate_id"] for a in book["assets"]]
        chk("⑤ intake --apply:候選冊出新版號檔 v0101(舊版不動 · 舊資產照留 · 收 3 條)· 中央 read_book 讀得過 · 冊版 %s" % book["version"],
            r2["book_out"] and ids[0] == "operator:twse_start" and len(ids) == 4 and C.read_book(reg / "VIA_AssetCandidates_SSOT_v0101.json")
            and json.loads((reg / "VIA_AssetCandidates_SSOT_v0100.json").read_text(encoding="utf-8"))["assets"] == [prior_asset] and book["version"] == "1.1.0", ids)
        r3 = intake(via, apply=True, book_dir=reg, registered=[], legacy=[])
        chk("⑥ 再收一次:沒變 → 不出新版", not r3["changed"] and not (reg / "VIA_AssetCandidates_SSOT_v0102.json").exists())
        st_asset = vdf_items[0]["asset"]
        rows = [{"code": "VIA-VDF-SYN777", "asset_intake": True, "candidate_asset": st_asset, "definition_sha256": C.digest(st_asset)},
                {"code": "VIA-VDF-INPT001", "asset_intake": True, "candidate_asset": prior_asset, "definition_sha256": C.digest(prior_asset)}]
        g = grant(via, apply=True, grant_path=reg / GRANT_NAME, book_dir=reg, registered=rows, legacy=[])
        gf = json.loads((reg / GRANT_NAME).read_text(encoding="utf-8"))
        chk("⑦ grant:中央號投影 — 登記鍵 / 候選編號 / 暫編號 → VIA-VDF-SYN777 · assets 帶版本與指紋 · 操作員提案不進 · 衝突照列 · 來源相對路徑",
            gf["grants"].get("VDF:SYN:START_DATE") == gf["grants"].get("VDF-SYN-0001") == gf["grants"].get(st_asset["candidate_id"]) == "VIA-VDF-SYN777"
            and gf["assets"]["VDF:SYN:START_DATE"] == {"code": "VIA-VDF-SYN777", "version": "1.0.0", "source_sha256": st_asset["source_sha256"]}
            and "operator:twse_start" not in gf["grants"] and any(c["key"] == "VDF:SYN:TIMEOUT" for c in gf["conflicts"])
            and all(not str(x).startswith("/") for x in gf["sources"]) and g["changed"], gf)
        g2 = grant(via, apply=True, grant_path=reg / GRANT_NAME, book_dir=reg, registered=rows, legacy=[])
        chk("⑧ 再核一次:中央號沒變 → 核發冊不重寫(REGISTERED 不再列衝突)", not g2["changed"] and g2["states"].get("REGISTERED") == 1, g2["states"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    writes = sorted(set(re.findall(r"(\w+)\.write_text\(", body)))
    chk("⑨ 不發號(號只由 CGC_MDL237 中央發;本檔沒有任何 VIA-<…> 號碼產生式)· 寫檔點只有候選冊(out)與核發冊(gp)· 子系統請求只讀 · 加速器橋在 · 零網路 · 同意閘不讀不寫 · %s" % writes,
        writes == ["gp", "out"] and not re.search(r"[\"']VIA-%|VIA-\{", body) and "VIA:ACCEL-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+(requests|httpx|urllib\.request|VDF_|VRN_)", src, re.M) and "CONSENT" not in body)
    print("[計] %s_%s 自測 %d/%d · %s" % (ENGINE, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
