#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL185_SsotBookSync v0100 — SSOT REGEX 同義字冊 同步自動相互更新檢查(批727)

操作員 2026-09-23 令:「讀取 VCGC 的相關工具 SSOT REGEX 同步自動相互更新檢查」。

**先量再造(LL400)。** 批727 把樹上所有 regex / 同義字 / 券商 / 網域冊與讀寫它們的工具全量過一遍,量出來的是:
**這些冊是各自獨立的副本,沒有任何一條自動傳遞路徑**——

| 量到的 | 證據 |
|---|---|
| RegexDict 只是全樹 regex 的**普查**(不帶同義字),只在 CGC_MDL115 `run`/`--selftest` 時**順手**重寫 | CGC_MDL115 run();批722–726 一天重新入倉 4 次 |
| 聯集冊 VIA_SSOT_SynonymUnion 存的是 09-21 那一次;之後底冊變了,**沒有一盞燈說它舊了** | CGC_MDL176 status 只跟記憶體裡的聯集比 |
| 拒絕清單(疊加層 deny_keys,操作員批413/679)**有的解析器守、有的不守** | SUP_MDL749 `resolve_synonym`:陸券名 → RESOLVED;第二血統首頁引擎:批413 已拒的一個別名 → JPM(批727 已修) |
| 兩本網域冊對同一網域寫**不同拼法**的鍵 | 正典 jpmorgan.com→JPM · 增補冊 jpmorgan.com→"J.P. MORGAN" |
| 同一本冊有 5 份實體副本,各被不同工具讀 | SYNONYM_LIBRARY ×5 · VRN_Rating_Dict ×5 · VRN_Broker_Dict ×5 |

所以這一支**一次量五條邊**,每條邊一個誠實態,不混成一個數字:
  E1 普查新鮮度    CGC_MDL115.scan() 現掃 vs 冊(不看 ts)            FRESH / STALE
  E2 聯集冊新鮮度  CGC_MDL176 baseline→intake→classify→union 現算 vs 冊(不看 ts)  FRESH / STALE
  E3 拒絕清單守不守 整本拒絕清單(疊加層 deny_keys ∪ CGC_MDL177)逐字丟進每一個券商解析器;
                   負控(合法券商)照樣要解得出來                    HOLDS / LEAK / CONTROL_LOST / ABSENT
  E4 網域冊一致    兩本網域冊共有的網域:正典化後同一個鍵         SAME / SPELLING / NONCANONICAL / CONFLICT / SIDE_DOOR
  E5 副本釘住      同名冊的實體副本:內容一致或差異全部講得出因由  IDENTICAL / EXPLAINED / DIVERGED
  E6 regex 冊一致  四本台股代號 regex 冊(中央 LOCKED · 規則冊 corrected · TickerRegexSSOT · 知識冊寬鬆式)
                   拿同一組探針逐冊判收不收                          AGREE / DISAGREE(列出哪幾個探針、哪幾本冊)
  E1 先問再生物冊(VIA_RegenArtifacts_SSOT):只登在「再生物」而不在「刻意入倉」的冊=DERIVED(本來就不入倉,舊是常態,不判黃);
     刻意入倉的冊舊了才是 STALE。

總判:有 LEAK / CONTROL_LOST / CONFLICT / SIDE_DOOR = RED rc1;有 STALE / SPELLING / NONCANONICAL / DIVERGED = YELLOW rc0;
全綠 GREEN rc0;五條都量不到 NODATA rc2。STALE 會印**正主那一支的重生指令**(自動=指令備好,寫不寫是批次/操作員的手;
本支永遠不寫任何冊)。

律:唯讀 · 零網路 · 不設同意閘 · 不重寫任何工具的判準(委派:每一條邊都問正主那一支)· stdlib。
用法:
  python CGC_MDL185_SsotBookSync_v0100.py check [--json]
  python CGC_MDL185_SsotBookSync_v0100.py --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 缺席零影響) =====
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
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import contextlib
import hashlib
import importlib.util
import io
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

ENGINE_ID = "CGC_MDL185_SsotBookSync"
VERSION = "v0100"
BATCH = "批727"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REG = VIA / "supportive modules" / "registry"
SSOT = VIA / "supportive modules" / "ssot"
R70 = VIA / "supportive modules" / "70_VRN_Rules"
VRN = VIA / "functional modules" / "VRN"

RED_STATES = {"LEAK", "CONTROL_LOST", "CONFLICT", "SIDE_DOOR"}
YELLOW_STATES = {"STALE", "SPELLING", "NONCANONICAL", "DIVERGED", "DISAGREE"}
# E5:同名冊的實體副本(誰讀哪一份,冊在 docs/VIA_B727 文;此處只釘「要一致或講得出因由」)
COPY_GROUPS = {
    "SYNONYM_LIBRARY": ["supportive modules/references/intake/VIA_SSOT_SynonymUnion_b678/SYNONYM_LIBRARY.json",
                        "functional modules/VRN/references/intake/VIA_SSOT_Additive_Audit_v0100_b20260921/SYNONYM_LIBRARY.json",
                        "functional modules/VRN/references/intake/VIA_SSOT_Additive_Audit_v0100/SYNONYM_LIBRARY.json",
                        "functional modules/VRN/knowledge/SYNONYM_LIBRARY_v4.json",
                        "functional modules/VRN/knowledge/SYNONYM_LIBRARY_v3.json"],
    "VRN_Rating_Dict_v0100": ["functional modules/VRN/knowledge/VRN_Rating_Dict_v0100.json",
                              "functional modules/VRN/references/intake/VRN_SSOT_Books_b561/VRN_Rating_Dict_v0100.json",
                              "functional modules/VRN/references/intake/VIA_SSOT_Additive_Audit_v0100_b20260921/baseline/VRN_Rating_Dict_v0100.json",
                              "functional modules/VRN/references/intake/VIA_SSOT_Additive_Audit_v0100/baseline/VRN_Rating_Dict_v0100.json",
                              "supportive modules/references/intake/VIA_GrokConsole_AuroraAcorn_b383/attachments/VRN_Rating_Dict_v0100.json"],
    "VRN_Broker_Dict_v0100": ["functional modules/VRN/knowledge/VRN_Broker_Dict_v0100.json",
                              "functional modules/VRN/references/intake/VRN_SSOT_Books_b561/VRN_Broker_Dict_v0100.json",
                              "functional modules/VRN/references/intake/VIA_SSOT_Additive_Audit_v0100_b20260921/baseline/VRN_Broker_Dict_v0100.json",
                              "functional modules/VRN/references/intake/VIA_SSOT_Additive_Audit_v0100/baseline/VRN_Broker_Dict_v0100.json",
                              "supportive modules/references/intake/VIA_GrokConsole_AuroraAcorn_b383/attachments/VRN_Broker_Dict_v0100.json"],
}


# ── 小工具 ──────────────────────────────────────────────────────────────
def _json(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _ver(p: Path) -> int:
    m = re.search(r"_v(\d+)\.", p.name)
    return int(m.group(1)) if m else -1


def _load(folder: Path, pattern: str, modname: str):
    """尾版(L54)載入正主那一支;載不到回 (None, 為什麼),不退回自己算一份(LL341 委派不複製)。"""
    hits = sorted(Path(folder).glob(pattern), key=_ver)
    if not hits:
        return None, f"{pattern} 不在 {Path(folder).name}/"
    try:
        spec = importlib.util.spec_from_file_location(modname, str(hits[-1]))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[modname] = mod
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(mod)
        mod.__s185_path__ = hits[-1]
        return mod, hits[-1].name
    except Exception as exc:
        return None, f"{hits[-1].name} 載入失敗:{type(exc).__name__}: {str(exc)[:80]}"


def _norm(v) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(v or ""))).strip().casefold()


def _quiet(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **k)


def edge(name: str, state: str, detail: str = "", fix: str = "", rows=None) -> dict:
    return {"edge": name, "state": state, "detail": detail, "fix": fix, "rows": rows or []}


def diff_books(stored: dict | None, fresh: dict | None, ignore=("ts",)) -> list:
    """兩本冊頂層鍵的差(忽略 ts)。任一方不在 → None(量不到,不判)。"""
    if not isinstance(stored, dict) or not isinstance(fresh, dict):
        return None
    return [k for k in sorted(set(stored) | set(fresh)) if k not in ignore and stored.get(k) != fresh.get(k)]


# ── E1 普查新鮮度 ────────────────────────────────────────────────────────
def e1_regex_fresh() -> dict:
    m, why = _load(REG, "CGC_MDL115_SSOTRegexDict_v*.py", "_s185_m115")
    if m is None:
        return edge("E1 RegexDict 普查新鮮度", "ABSENT", why)
    stored = _json(getattr(m, "OUTJ", REG / "VIA_SSOT_RegexDict_v0100.json"))
    try:
        fresh = _quiet(m.scan)
    except Exception as exc:
        return edge("E1 RegexDict 普查新鮮度", "ABSENT", f"scan() 失敗:{type(exc).__name__}")
    d = diff_books(stored, fresh)
    if d is None:
        return edge("E1 RegexDict 普查新鮮度", "ABSENT", "冊不在或讀不出來")
    tail = (f"樣式 {stored.get('total_patterns')}→{fresh.get('total_patterns')} · "
            f"共用 {stored.get('total_shared')}→{fresh.get('total_shared')}")
    if not d:
        return edge("E1 RegexDict 普查新鮮度", "FRESH", f"現掃 = 冊(不看 ts)· {tail} · {why}")
    if regen_policy("VIA_SSOT_RegexDict_v0100.json") == "DERIVED":
        return edge("E1 RegexDict 普查新鮮度", "DERIVED",
                    f"再生物冊(不入倉,舊是常態):現掃 ≠ 冊 · {tail} · {why}")
    return edge("E1 RegexDict 普查新鮮度", "STALE", f"刻意入倉的冊舊了:變動鍵 {d} · {tail} · {why}",
                f"via-ssotregex(= python \"{getattr(m, '__s185_path__', Path('CGC_MDL115')).name}\";重寫冊與頁)")


def regen_policy(name: str, book: dict | None = None) -> str:
    """再生物冊(MDL167 的冊)怎麼說這本:KEPT(刻意入倉)· DERIVED(只登再生物)· TRACKED(兩邊都沒登=一般追蹤檔)。"""
    book = book if book is not None else (_json(REG / "VIA_RegenArtifacts_SSOT_v0100.json") or {})
    if any(str(k.get("path", "")).endswith("/" + name) for k in book.get("keep_even_if_matched", []) or []):
        return "KEPT"
    if any(re.search(str(p.get("rx", "")), "VeritasIntelligenceAnalytics/supportive modules/registry/" + name)
           for p in book.get("patterns", []) or []):
        return "DERIVED"
    return "TRACKED"


# ── E2 聯集冊新鮮度 ──────────────────────────────────────────────────────
def e2_union_fresh() -> dict:
    m, why = _load(REG, "CGC_MDL176_SynonymUnion_v*.py", "_s185_m176")
    if m is None:
        return edge("E2 SynonymUnion 聯集冊新鮮度", "ABSENT", why)
    try:
        base = _quiet(m.baseline)
        lib = _quiet(m.intake)
        if not lib:
            return edge("E2 SynonymUnion 聯集冊新鮮度", "ABSENT", "收容件(b678 SYNONYM_LIBRARY)缺席")
        rows = _quiet(m.classify, base, lib)
        fresh = _quiet(m.union, base, lib, rows)
    except Exception as exc:
        return edge("E2 SynonymUnion 聯集冊新鮮度", "ABSENT", f"現算失敗:{type(exc).__name__}: {str(exc)[:80]}")
    stored = _json(getattr(m, "UNION_OUT", REG / "VIA_SSOT_SynonymUnion_v0100.json"))
    d = diff_books(stored, fresh)
    if d is None:
        return edge("E2 SynonymUnion 聯集冊新鮮度", "ABSENT", "聯集冊不在或讀不出來")
    if not d:
        return edge("E2 SynonymUnion 聯集冊新鮮度", "FRESH", f"現算 = 冊(不看 ts)· 冊時 {stored.get('ts')} · {why}")
    return edge("E2 SynonymUnion 聯集冊新鮮度", "STALE", f"現算 ≠ 冊:變動鍵 {d} · 冊時 {stored.get('ts')} · {why}",
                f"python \"{getattr(m, '__s185_path__', Path('CGC_MDL176')).name}\" plan --apply(只增不減由它自己先證,不過就 fail-closed)")


# ── E3 拒絕清單守不守 ────────────────────────────────────────────────────
def deny_list() -> tuple:
    out = set()
    hits = sorted(SSOT.glob("VIA_FinancialInstitution_Overlay_v*.json"), key=_ver)
    for k in ((_json(hits[-1]) or {}).get("deny_keys", []) if hits else []):
        if str(k).strip():
            out.add(str(k).strip())
    purge, _ = _load(REG, "CGC_MDL177_ChinaBrokerPurge_v*.py", "_s185_m177")
    for attr in ("CN_ALIAS", "CN_CANON"):
        for k in (getattr(purge, attr, ()) or ()) if purge is not None else ():
            if str(k).strip():
                out.add(str(k).strip())
    return tuple(sorted(out, key=lambda x: (-len(x), x)))


CONTROLS = ("凱基", "摩根士丹利", "中國信託", "國泰證期", "Morgan Stanley", "CLSA")


def probe_resolvers(resolvers: list, denied: tuple, controls: tuple = CONTROLS) -> list:
    """每一個解析器:整本拒絕清單不得解出券商;負控至少要解出一個(否則是把合法券商一起關掉了)。"""
    rows = []
    for name, fn, why in resolvers:
        if fn is None:
            rows.append({"resolver": name, "state": "ABSENT", "leaks": [], "why": why})
            continue
        leaks, errs = [], []
        for k in denied:
            try:
                got = fn(k)
            except Exception as exc:
                errs.append(f"{k}:{type(exc).__name__}")
                continue
            if got and str(got).upper() != "DENIED":
                leaks.append(f"{k}→{got}")
        ok_controls = []
        for c in controls:
            try:
                if fn(c):
                    ok_controls.append(c)
            except Exception:
                pass
        state = "LEAK" if leaks else ("CONTROL_LOST" if controls and not ok_controls else "HOLDS")
        rows.append({"resolver": name, "state": state, "leaks": leaks[:12], "n_leak": len(leaks),
                     "controls_ok": len(ok_controls), "errors": errs[:3], "why": why})
    return rows


def live_resolvers() -> list:
    out = []
    ov, why = _load(SSOT, "VIA_FinancialInstitution_Overlay_v*.py", "_s185_overlay")
    out.append(("疊加層閘 resolve_broker", (lambda k: "DENIED" if ov.resolve_broker(k).get("deny") else
                                           (ov.resolve_broker(k).get("key") or None)) if ov else None, why))
    m15, why = _load(R70, "SUP_MDL015_VISVRNBrokerAliasFullList_v*.py", "_s185_m015")

    def _m15(k):
        r = m15.def_normalize_broker_name(f"本報告由{k}研究部出具")
        return getattr(r, "canonical", None) if r else None
    out.append(("SUP_MDL015 券商別名全清單", _m15 if m15 else None, why))
    hub, why = _load(R70, "SUP_MDL749_VRNFieldRuleHub_v*.py", "_s185_hub")

    def _hub(k):
        r = _quiet(hub.resolve_synonym, k, "broker")
        if r.get("status") == "DENIED":
            return "DENIED"
        return r.get("canonical") if r.get("status") == "RESOLVED" else None
    out.append(("SUP_MDL749 增補冊 resolve_synonym(broker)", _hub if hub else None, why))
    m176, why = _load(REG, "CGC_MDL176_SynonymUnion_v*.py", "_s185_m176b")

    def _u(k):
        r = _quiet(m176.resolve, "broker", k)
        return None if r.get("state") in ("DENIED", "NODATA") else r.get("canonical")
    out.append(("CGC_MDL176 聯集 resolve(broker)", _u if m176 else None, why))
    fpe_mod, why = _load(VRN / "engine", "VIA_VRN_FirstPageEngine.py", "_s185_fpe")
    fpe = None
    if fpe_mod is not None:
        try:
            fpe = _quiet(fpe_mod.FirstPageEngine)
        except Exception as exc:
            fpe, why = None, f"FirstPageEngine() 失敗:{type(exc).__name__}"
    core = getattr(fpe_mod, "EVIDENCE_CORE", None) if fpe_mod is not None else None
    out.append(("第二血統 證據核心 broker_evidence(頁面層)",
                (lambda k: core.broker_evidence([f"本報告由{k}研究部出具"], fpe.brd.b).get("broker")) if (core and fpe) else None,
                why if not core else "VRN_Evidence_Core(經首頁引擎)"))
    out.append(("第二血統 首頁引擎 broker_normalize(檔名層)",
                (lambda k: fpe.brd.broker_normalize(k)) if fpe else None, why))
    return out


def e3_deny() -> dict:
    denied = deny_list()
    if not denied:
        return edge("E3 拒絕清單在每一個解析器都守", "ABSENT", "拒絕清單兩個來源都讀不到")
    rows = probe_resolvers(live_resolvers(), denied)
    red = [r for r in rows if r["state"] in RED_STATES]
    absent = [r for r in rows if r["state"] == "ABSENT"]
    state = "LEAK" if any(r["state"] == "LEAK" for r in rows) else ("CONTROL_LOST" if red else
                                                                     ("ABSENT" if len(absent) == len(rows) else "HOLDS"))
    detail = f"拒絕清單 {len(denied)} 名 × 解析器 {len(rows)} 支 · " + " · ".join(
        f"{r['resolver']}={r['state']}" + (f"({r['n_leak']})" if r.get("n_leak") else "") for r in rows)
    fix = ("漏的那一支在回傳前過拒絕閘(疊加層 deny_keys ∪ CGC_MDL177;最長者勝 批681);名單不抄進解析器(L30)"
           if red else "")
    return edge("E3 拒絕清單在每一個解析器都守", state, detail, fix, rows)


# ── E4 網域冊一致 ────────────────────────────────────────────────────────
def _canon_index(inst: dict) -> dict:
    idx = {}
    regs = (inst or {}).get("registries") or {}
    for grp in ("domestic_brokers", "foreign_brokers"):
        for key, spec in (regs.get(grp) or {}).items():
            for name in [key, spec.get("ssot_key", ""), spec.get("english_name", ""), spec.get("chinese_name", "")] + \
                    list(spec.get("aliases") or []):
                n = re.sub(r"[\s.\-_&]", "", _norm(name))
                if n:
                    idx.setdefault(n, key)
    for old, new in ((inst or {}).get("key_migration_map") or {}).items():
        idx[re.sub(r"[\s.\-_&]", "", _norm(old))] = new
    return idx


def compare_domains(inst_dom: dict, add_map: dict, deny_domains: dict, canon_idx: dict) -> list:
    rows = []

    def canon(v):
        return canon_idx.get(re.sub(r"[\s.\-_&]", "", _norm(v)))
    for d in sorted(set(inst_dom) & set(add_map)):
        a, b = str(inst_dom[d]), str(add_map[d])
        if a == b:
            st = "SAME"
        elif canon(b) is None:
            st = "NONCANONICAL"
        elif canon(a) == canon(b) or a == canon(b):
            st = "SPELLING"
        else:
            st = "CONFLICT"
        rows.append({"domain": d, "state": st, "institution": a, "addendum": b, "canonical": canon(b)})
    for d in sorted(set(add_map) - set(inst_dom)):
        if canon(add_map[d]) is None and str(add_map[d]).upper() != "DENIED":
            rows.append({"domain": d, "state": "NONCANONICAL", "institution": None, "addendum": add_map[d], "canonical": None})
    for d in sorted(deny_domains or {}):
        for src_name, src in (("正典", inst_dom), ("增補冊", add_map)):
            v = src.get(d)
            if v and str(v).upper() != "DENIED":
                rows.append({"domain": d, "state": "SIDE_DOOR", "institution": inst_dom.get(d), "addendum": add_map.get(d),
                             "canonical": v, "why": f"拒絕網域在{src_name}還解得出 {v}"})
    return rows


def e4_domains() -> dict:
    inst = _json(SSOT / "VIA_Financial_Institution_SSOT_v0100.json")
    rfr = _json(REG / "VIA_VRN_ReportFieldRules_SSOT_v0100.json")
    if not inst or not rfr:
        return edge("E4 兩本網域冊一致", "ABSENT", "正典或增補冊不在")
    raw_dom = inst.get("domains") or (inst.get("registries") or {}).get("domains") or {}
    inst_dom = {d: (s.get("broker_ssot_key") if isinstance(s, dict) else s) for d, s in raw_dom.items()}
    bda = rfr.get("broker_domains_addendum") or {}
    add_map = bda.get("map") or {}
    deny_domains = (bda.get("deny_domains") or {}).get("map") or {}
    rows = compare_domains(inst_dom, add_map, deny_domains, _canon_index(inst))
    states = {r["state"] for r in rows}
    state = next((s for s in ("SIDE_DOOR", "CONFLICT", "NONCANONICAL", "SPELLING") if s in states), "SAME")
    cnt = {s: sum(1 for r in rows if r["state"] == s) for s in sorted(states)}
    detail = f"共有網域 {len(set(inst_dom) & set(add_map))} · " + " · ".join(f"{k} {v}" for k, v in cnt.items())
    ex = [f"{r['domain']}:{r['institution']}|{r['addendum']}" for r in rows if r["state"] in ("SPELLING", "NONCANONICAL", "CONFLICT", "SIDE_DOOR")][:6]
    fix = ("增補冊的值改寫成正典鍵(只改拼法不改歸屬;VIA_VRN_ReportFieldRules_SSOT broker_domains_addendum.map)"
           if state in ("SPELLING", "NONCANONICAL") else ("兩冊歸屬不同=要操作員裁" if state == "CONFLICT" else
                                                           ("拒絕網域不得在任何冊解出券商" if state == "SIDE_DOOR" else "")))
    return edge("E4 兩本網域冊一致", state, detail + (" · 例 " + " ; ".join(ex) if ex else ""), fix, rows)


# ── E5 副本釘住 ──────────────────────────────────────────────────────────
def _triples(lib: dict) -> set:
    out = set()
    for scope, keys in ((lib or {}).get("scopes") or {}).items():
        for k, ents in (keys or {}).items():
            for e in ents or []:
                if isinstance(e, dict) and e.get("canonical"):
                    out.add((scope, _norm(k), str(e["canonical"]).upper()))
    return out


def _fingerprint(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def compare_copies(name: str, docs: dict, denied_norm: set) -> dict:
    """docs:{相對路徑: 已解析的 JSON 或 None}。第一份是參照。SYNONYM_LIBRARY 比三元組,其餘比內容指紋。"""
    present = {p: d for p, d in docs.items() if d is not None}
    if len(present) < 2:
        return {"group": name, "state": "ABSENT" if not present else "IDENTICAL", "rows": [], "why": f"在位 {len(present)} 份"}
    ref_path = next(iter(present))
    rows = []
    if name == "SYNONYM_LIBRARY":
        ref = _triples(present[ref_path])
        for p, d in present.items():
            t = _triples(d)
            gone, extra = ref - t, t - ref
            unexplained = [x for x in gone if x[1] not in denied_norm and _norm(x[2]) not in denied_norm]
            st = "IDENTICAL" if not gone and not extra else ("EXPLAINED" if not unexplained and not extra else "DIVERGED")
            rows.append({"copy": p, "state": st, "missing_vs_ref": len(gone), "extra_vs_ref": len(extra),
                         "unexplained_missing": len(unexplained)})
    else:
        fps = {p: _fingerprint(d) for p, d in present.items()}
        ref_fp = fps[ref_path]
        for p, fp in fps.items():
            rows.append({"copy": p, "state": "IDENTICAL" if fp == ref_fp else "DIVERGED", "fingerprint": fp})
    states = {r["state"] for r in rows}
    state = "DIVERGED" if "DIVERGED" in states else ("EXPLAINED" if "EXPLAINED" in states else "IDENTICAL")
    return {"group": name, "state": state, "rows": rows, "reference": ref_path}


def e5_copies() -> dict:
    denied_norm = {_norm(x) for x in deny_list()}
    groups = []
    for name, paths in COPY_GROUPS.items():
        docs = {p: _json(VIA / p) for p in paths}
        groups.append(compare_copies(name, docs, denied_norm))
    states = {g["state"] for g in groups}
    state = "DIVERGED" if "DIVERGED" in states else ("EXPLAINED" if "EXPLAINED" in states else
                                                     ("ABSENT" if states == {"ABSENT"} else "IDENTICAL"))
    detail = " · ".join(f"{g['group']}={g['state']}" + (
        f"(差 {sum(1 for r in g['rows'] if r['state'] == 'DIVERGED')}/{len(g['rows'])} 份)" if g["state"] == "DIVERGED" else "")
        for g in groups)
    fix = "差異講不出因由的副本:裁定哪一份是正本,其餘改指向它(alias_source),不再各讀各的" if state == "DIVERGED" else ""
    return edge("E5 同名冊副本釘住", state, detail, fix, groups)


# ── E6 regex 冊一致 ──────────────────────────────────────────────────────
TICKER_PROBES = ("2330", "1101", "0050", "00878", "00981A", "2026", "123", "12345", "2330.TW")


def _dig(o, *path):
    for k in path:
        o = (o or {}).get(k) if isinstance(o, dict) else None
    return o


def ticker_books() -> list:
    """(冊, 鍵, 式);讀不到的冊不列(不代寫一條式)。"""
    out = []
    c = _json(REG / "VIA_Central_Synonym_Regex_v0100.json")
    rx = _dig(c, "regex", "TW_TICKER_LOCKED", "pattern")
    if rx:
        out.append(("VIA_Central_Synonym_Regex", "TW_TICKER_LOCKED", rx))
    fr = _json(REG / "VRN_FieldRules_SSOT_v0100.json")
    rx = _dig(fr, "rules", "ticker", "corrected", "TW_TICKER")
    if rx:
        out.append(("VRN_FieldRules_SSOT", "rules.ticker.corrected.TW_TICKER", rx))
    hits = sorted(SSOT.glob("VRN_TickerRegexSSOT_v[0-9][0-9][0-9][0-9].json"), key=_ver)
    rx = _dig(_json(hits[-1]) if hits else None, "rules", "TW_TICKER_REGEX")
    if rx:
        out.append((hits[-1].stem, "rules.TW_TICKER_REGEX", rx))
    kn = _json(VRN / "knowledge" / "VRN_TickerDate_Regex_v0100.json")
    rx = _dig(kn, "ticker_patterns", "LOOSE_TW_TICKER")
    if rx:
        out.append(("VRN_TickerDate_Regex(寬鬆式)", "ticker_patterns.LOOSE_TW_TICKER", rx))
    return out


def compare_regex_books(books: list, probes: tuple = TICKER_PROBES) -> dict:
    matrix = {}
    for name, key, rx in books:
        try:
            cre = re.compile(rx)
            matrix[name] = {p: bool(cre.fullmatch(p)) for p in probes}
        except re.error as exc:
            matrix[name] = {"__error__": str(exc)}
    split = [p for p in probes if len({m.get(p) for m in matrix.values() if "__error__" not in m}) > 1]
    rows = [{"probe": p, "accept": sorted(n for n, m in matrix.items() if m.get(p)),
             "reject": sorted(n for n, m in matrix.items() if m.get(p) is False)} for p in split]
    return {"matrix": matrix, "split": split, "rows": rows}


def e6_regex_books() -> dict:
    books = ticker_books()
    if len(books) < 2:
        return edge("E6 台股代號 regex 冊一致", "ABSENT", f"讀得到的冊 {len(books)} 本(至少兩本才比得了)")
    cmp = compare_regex_books(books)
    names = " · ".join(f"{n}「{k}」" for n, k, _ in books)
    if not cmp["split"]:
        return edge("E6 台股代號 regex 冊一致", "AGREE", f"{len(books)} 本冊對 {len(TICKER_PROBES)} 個探針判法相同 · {names}")
    ex = " ; ".join(f"{r['probe']}:收 {len(r['accept'])} 本 / 拒 {len(r['reject'])} 本" for r in cmp["rows"][:6])
    return edge("E6 台股代號 regex 冊一致", "DISAGREE",
                f"{len(books)} 本冊在 {len(cmp['split'])} 個探針上判法不同 · {ex} · {names}",
                "各冊的範疇是不同的操作員裁定(批628 三平台九型含 ETF · 2026-08-04 四碼首碼非零範疇凍結 · 寬鬆式不入 LOCKED 圈);"
                "要不要收斂成一本=操作員裁,本支只把分歧攤開", cmp["rows"])


# ── 總判 ────────────────────────────────────────────────────────────────
def check() -> dict:
    edges = [e1_regex_fresh(), e2_union_fresh(), e3_deny(), e4_domains(), e5_copies(), e6_regex_books()]
    states = [e["state"] for e in edges]
    if any(s in RED_STATES for s in states):
        verdict, rc = "RED", 1
    elif any(s in YELLOW_STATES for s in states):
        verdict, rc = "YELLOW", 0
    elif all(s == "ABSENT" for s in states):
        verdict, rc = "NODATA", 2
    else:
        verdict, rc = "GREEN", 0
    return {"engine": ENGINE_ID, "version": VERSION, "verdict": verdict, "rc": rc, "edges": edges}


def render(res: dict) -> None:
    print(f"=== {ENGINE_ID} {VERSION} · SSOT REGEX 同義字冊 同步自動相互更新檢查 ===")
    for e in res["edges"]:
        print(f"  [{e['state']:<12}] {e['edge']}")
        print(f"      {e['detail'][:300]}")
        for r in e.get("rows", []):
            if isinstance(r, dict) and r.get("state") in RED_STATES:
                print(f"      !! {r.get('resolver') or r.get('domain')}: {r.get('state')} "
                      f"{', '.join(r.get('leaks', [])[:8]) or r.get('why', '')}")
        if e.get("fix"):
            print(f"      [指路] {e['fix']}")
    print(f"  [計] {len(res['edges'])} 條邊 · " + " · ".join(e["state"] for e in res["edges"]) + f" → {res['verdict']} (rc={res['rc']})")


# ── 自測:每一個態都要咬得到(夾具);真樹只讀 ───────────────────────────
def selftest() -> int:
    t0 = time.time()
    ran, fails = [], []

    def chk(name, ok, detail=""):
        ran.append(name)
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name} {detail}".rstrip())

    # E1/E2 比冊邏輯
    chk("① 冊 = 現算(只差 ts)→ 不算變動", diff_books({"a": 1, "ts": "t1"}, {"a": 1, "ts": "t2"}) == [])
    chk("② 冊 ≠ 現算 → 點名變動鍵", diff_books({"a": 1, "b": 2, "ts": "x"}, {"a": 1, "b": 3, "ts": "y"}) == ["b"])
    chk("③ 冊不在 → None(量不到不判)", diff_books(None, {"a": 1}) is None)
    # E3 解析器探針
    denied = ("禁甲名", "禁乙名")        # 夾具名(真拒絕名只從冊讀,原始碼一個都不寫;CGC_MDL177 verify 會把寫出來的當活資料)
    tight = ("守得住", lambda k: None if k in denied else ("KGI" if k == "凱基" else None), "")
    leaky = ("會漏", lambda k: "XX" if k == "禁甲名" else ("KGI" if k == "凱基" else None), "")
    blind = ("全關", lambda k: None, "")
    absent = ("不在", None, "載不到")
    rows = probe_resolvers([tight, leaky, blind, absent], denied, controls=("凱基",))
    st = {r["resolver"]: r["state"] for r in rows}
    chk("④ 拒絕名全擋、負控解得出 → HOLDS", st["守得住"] == "HOLDS")
    chk("⑤ 拒絕名被解出 → LEAK 並具名", st["會漏"] == "LEAK" and rows[1]["leaks"] == ["禁甲名→XX"], f"({rows[1]['leaks']})")
    chk("⑥ 連合法券商都解不出 → CONTROL_LOST(把好人一起關掉也是錯)", st["全關"] == "CONTROL_LOST")
    chk("⑦ 解析器載不到 → ABSENT(不是漏)", st["不在"] == "ABSENT")
    chk("⑧ 回 'DENIED' 字樣不算漏", probe_resolvers([("d", lambda k: "DENIED" if k in denied else "KGI", "")],
                                                   denied, controls=("凱基",))[0]["state"] == "HOLDS")
    # E4 網域
    idx = {"jpm": "JPM", "jpmorgan": "JPM", "j.p.morgan": "JPM", "jpmorgan": "JPM", "ms": "MS", "morganstanley": "MS",
           "kgi": "KGI"}
    idx = {re.sub(r"[\s.\-_&]", "", k): v for k, v in idx.items()}
    rows = compare_domains({"a.com": "KGI", "b.com": "JPM", "c.com": "MS", "d.com": "KGI", "x.hk": "XX"},
                           {"a.com": "KGI", "b.com": "J.P. MORGAN", "c.com": "WHO KNOWS", "d.com": "MS", "x.hk": "DENIED"},
                           {"x.hk": "DENIED", "y.hk": "DENIED"}, idx)
    by = {(r["domain"], r["state"]) for r in rows}
    chk("⑨ 同鍵 → SAME", ("a.com", "SAME") in by)
    chk("⑩ 拼法不同同一家 → SPELLING", ("b.com", "SPELLING") in by)
    chk("⑪ 增補冊的值不是任何正典鍵 → NONCANONICAL", ("c.com", "NONCANONICAL") in by)
    chk("⑫ 兩冊歸屬不同 → CONFLICT", ("d.com", "CONFLICT") in by)
    chk("⑬ 拒絕網域在正典還解得出 → SIDE_DOOR", ("x.hk", "SIDE_DOOR") in by)
    # E5 副本
    lib = {"scopes": {"broker": {"凱基": [{"canonical": "KGI"}], "禁甲名": [{"canonical": "XX"}]}}}
    purged = {"scopes": {"broker": {"凱基": [{"canonical": "KGI"}]}}}
    drift = {"scopes": {"broker": {"凱基": [{"canonical": "KGI"}], "新詞": [{"canonical": "NEW"}]}}}
    g = compare_copies("SYNONYM_LIBRARY", {"ref": lib, "same": lib, "purged": purged}, {_norm("禁甲名")})
    chk("⑭ 副本少的全是拒絕名 → EXPLAINED(批702 清除有因由)", g["state"] == "EXPLAINED", f"({g['state']})")
    g = compare_copies("SYNONYM_LIBRARY", {"ref": lib, "drift": drift}, {_norm("禁甲名")})
    chk("⑮ 副本多出講不出因由的詞 → DIVERGED", g["state"] == "DIVERGED")
    g = compare_copies("VRN_Rating_Dict_v0100", {"a": {"x": 1}, "b": {"x": 1}, "c": {"x": 2}}, set())
    chk("⑯ 一般冊比內容指紋:不同 → DIVERGED", g["state"] == "DIVERGED" and sum(r["state"] == "DIVERGED" for r in g["rows"]) == 1)
    chk("⑰ 副本只剩一份 → 不判 DIVERGED", compare_copies("x", {"a": {"x": 1}, "b": None}, set())["state"] == "IDENTICAL")
    # E1 再生物冊政策
    pol = {"patterns": [{"rx": "/registry/VIA_SSOT_RegexDict"}], "keep_even_if_matched": [{"path": "a/b/VIA_Kept_v0100.json"}]}
    chk("⑱a 只登再生物 → DERIVED(舊是常態,不判黃)", regen_policy("VIA_SSOT_RegexDict_v0100.json", pol) == "DERIVED")
    pol["keep_even_if_matched"].append({"path": "x/registry/VIA_SSOT_RegexDict_v0100.json"})
    chk("⑱b 同時登刻意入倉 → KEPT(舊了才算 STALE)", regen_policy("VIA_SSOT_RegexDict_v0100.json", pol) == "KEPT")
    chk("⑱c 兩邊都沒登 → TRACKED", regen_policy("Other_v0100.json", pol) == "TRACKED")
    # E6 regex 冊
    cmp = compare_regex_books([("A", "k", r"^[1-9]\d{3}$"), ("B", "k", r"^(?:[1-9]\d{3}|00\d{2,4})$")], ("2330", "0050"))
    chk("⑱d 兩本冊對 0050 判法不同 → 分歧只列 0050", cmp["split"] == ["0050"] and cmp["rows"][0]["accept"] == ["B"])
    cmp = compare_regex_books([("A", "k", r"^[1-9]\d{3}$"), ("B", "k", r"(?<!\d)([1-9]\d{3})(?!\d)")], ("2330", "123"))
    chk("⑱e 同一語意不同寫法 → 無分歧", cmp["split"] == [])
    chk("⑱f 壞式不當成「全拒」混進比對", "__error__" in compare_regex_books([("A", "k", "(")], ("1",))["matrix"]["A"])
    # 真樹唯讀 + 紀律
    # ⑱ 唯讀:**本行程寫入守衛**——check() 期間任何寫檔企圖(本支或它載入的正主)都記下並擋掉。
    #   第一版比 registry/ssot 兩夾的 mtime,在全格子並行時被**別站**合法的寫入咬到(量到的是格子,不是本支)。
    import builtins
    _writes = []
    _real_open, _real_wt, _real_wb = builtins.open, Path.write_text, Path.write_bytes

    def _guard_open(file, mode="r", *a, **k):
        if any(c in str(mode) for c in "wax+"):
            _writes.append(str(file))
            raise PermissionError(f"MDL185 自測寫入守衛:{file}")
        return _real_open(file, mode, *a, **k)

    def _guard_write(self, *a, **k):
        _writes.append(str(self))
        raise PermissionError(f"MDL185 自測寫入守衛:{self}")
    builtins.open, Path.write_text, Path.write_bytes = _guard_open, _guard_write, _guard_write
    try:
        live = check()
    finally:
        builtins.open, Path.write_text, Path.write_bytes = _real_open, _real_wt, _real_wb
    chk("⑱ check 唯讀(本行程寫入守衛:任何寫檔企圖都記下並擋掉;不受格子並行的別站影響)", not _writes,
        f"(寫入企圖 {_writes[:3]})" if _writes else "")
    chk("⑲ 六條邊每條都有態(真樹實跑)", len(live["edges"]) == 6 and all(e["state"] for e in live["edges"]),
        "(" + " · ".join(e["state"] for e in live["edges"]) + ")")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑳ 同意閘永不代設(原始碼層)", not re.findall(r"environ\[\s*['\"]VIA_(?:NET|SCRAPE)_CONSENT", src))
    chk("㉑ 零網路(原始碼不引 urllib/requests/socket)",
        not re.search(r"^\s*(import|from) (urllib|requests|socket)", src, re.M))
    scan_src = src
    for c in CONTROLS:                   # 合法的較長名(摩根士丹利)含拒絕的短名不算抄——最長者勝 批681
        scan_src = scan_src.replace(c, " ")
    spelled = [n for n in deny_list() if (re.search(r"[\u4e00-\u9fff]", n) or len(n) >= 5) and n in scan_src]
    chk("㉒ 原始碼不抄拒絕名單(名單只從冊讀,L30;CJK 名與 ≥5 字拉丁名一個都不寫)", "deny_keys" in src and not spelled,
        f"(寫出來的 {spelled[:4]})" if spelled else "")
    n_ok = len(ran) - len(fails)
    print(f"  [計] 自測 {len(ran)} 檢 OK {n_ok} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if "--selftest" in a:
        print(f"=== {ENGINE_ID} {VERSION} · 自測(夾具每態都咬 + 真樹唯讀實跑)===")
        return selftest()
    verb = next((x for x in a if not x.startswith("-")), "check")
    if verb != "check":
        print("  [用法] check [--json] | --selftest")
        return 2
    res = check()
    if "--json" in a:
        print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    else:
        render(res)
    return res["rc"]


if __name__ == "__main__":
    sys.exit(main())
