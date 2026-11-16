#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_SSOTSync v0101 — 薄尾:VDF-390 擷取總冊逐項申請中央號(依大類:總經 MRC · 市場 FM · 財報 FD)

操作員令(2026-11-14):「依大類發中央號,總經 MRC · 市場 FM · 財報 FD」。號只由 VCGC 中央編號發(VDF 不自發號);
VDF 這邊照 v0100 既有路走:登記冊(VDF 自己的帳)→ 申請(contract/VDF_NUMBER_REQUEST_latest.json)→ VCGC 收件發號 →
apply 讀回執把中央號寫回自己的登記冊。v0100 一字不動;本版只多一類條目:
  擷取項(VDF_FetchOne_Matrix_Registry_v0100 的 390 項)· 鍵 VDF:FETCH:<冊上編號>:
    大類 → 申請型別(整個大類同一型別):
      美國總經 · 領先 / 同時 / 落後 · 物價 · 財政 · 公債 · 聯準會 · 政策 · 全球總經 · 區域 → MACRO(中央 MRC)
      財報 · 三大報表 · 共識 · 評價 → FINDATA(中央 FD)
      其餘九大類 → INSTRUMENT(中央 FM)
    scope = vdf.fetchone.<mrc|fm|fd>[.<地區>](MRC / FM 的號帶地區:US / CN / TW / GLB;VCGC v0121 取 scope 最後一段)
    內容 = 冊上編號 · 大類 · 名稱 · 來源 · 頻率(內容不變 → 指紋不變 → 號不變)
只寫 VDF 自己的登記冊與申請檔(照 v0100);零網路;不碰 TA-Lib。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SSOTSync"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0101(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0101(p) < _vnum_v0101(__file__)), key=_vnum_v0101)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0100
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


FETCHONE_NAME = "VDF_FetchOne_Matrix_Registry_v0100.json"
MRC_SECTIONS = ("美國總經 · 領先", "美國總經 · 同時", "美國總經 · 落後 / 物價", "財政 · 公債", "聯準會 · 政策", "全球總經 · 區域")
FD_SECTIONS = ("財報 · 三大報表", "共識 · 評價")
CN_RX = re.compile(r"^GL-(04[A-F]?|14|15|25|33)$")
TW_RX = re.compile(r"^(PX-0[12]|PX-04C|PX-06F|EF-|FQ-|MX-(A1|A2|A3|A11|A12|D1|D2|E1)$|SE-(05|12)$)")
NEW = {"MACRO": ("MRC", "MACRO", "總經擷取項"), "INSTR": ("FM", "INSTRUMENT", "市場擷取項"), "FINDATA": ("FD", "FINDATA", "財報擷取項")}
for _k, (_c, _a, _z) in NEW.items():                     # 只增:v0100 的五類一個不動
    PRIOR.VCGC_KIND[_k] = _c
    PRIOR.SHORT[_k] = _c
    PRIOR.ASSET_TYPE[_k] = _a
    PRIOR.KIND_ZH[_k] = _z
    PRIOR.RISK[_k] = "LOW"
_HARVEST_V0100 = PRIOR.harvest
_BUILD_V0100 = PRIOR.build_asset


def kind_of(section: str) -> str:
    return "MACRO" if section in MRC_SECTIONS else ("FINDATA" if section in FD_SECTIONS else "INSTR")


def region_of(kind: str, iid: str) -> str:
    if kind == "MACRO":
        return "us" if re.match(r"^(US|FI|FD)-", iid) else ("cn" if CN_RX.match(iid) else "glb")
    if kind == "INSTR":
        return "tw" if TW_RX.match(iid) else ("us" if iid.startswith("AI-") else "glb")
    return ""


def fetchone_entries(vdf: Path = HERE) -> dict:
    p = vdf / FETCHONE_NAME
    if not p.is_file():
        PRIOR.SKIPPED.append("%s(不在)" % FETCHONE_NAME)
        return {}
    try:
        reg = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        PRIOR.SKIPPED.append("%s(%s)" % (FETCHONE_NAME, type(exc).__name__))
        return {}
    out = {}
    for it in reg.get("items") or []:
        iid, sec = str(it.get("id", "")).strip(), str(it.get("section", ""))
        if not iid:
            continue
        kind = kind_of(sec)
        content = {"id": iid, "section": sec, "name": str(it.get("name", "")), "source": str(it.get("source", "")), "freq": str(it.get("freq", "")),
                   "region": region_of(kind, iid)}
        key = "VDF:FETCH:%s" % iid
        out[key] = {"kind": kind, "key": key, "fp": PRIOR._sha16(PRIOR._canon(content)), "version": p.stem[-5:], "src": [p.name], "content": content,
                    "note": "擷取總冊 · 狀態 %s" % it.get("status", "")}
    return out


def harvest(vdf: Path = HERE) -> dict:
    items = _HARVEST_V0100(vdf)
    for k, e in fetchone_entries(vdf).items():
        items.setdefault(k, e)
    return items


def build_asset(e: dict) -> dict:
    if e["kind"] not in NEW:
        return _BUILD_V0100(e)
    c = e.get("content") or {}
    code, atype, zh = NEW[e["kind"]]
    scope = "vdf.fetchone.%s" % code.lower() + (".%s" % c["region"] if c.get("region") else "")
    value = {k: c.get(k) for k in ("id", "section", "name", "source", "freq")}
    return {"candidate_id": re.sub(r"[^A-Za-z0-9_.:-]", "_", e["key"])[:400], "ssot_code": None, "asset_type": atype, "owner": "VDF",
            "source_id": PRIOR.SOURCE_ID, "source_pointer": e["key"], "source_sha256": PRIOR.asset_sha(e), "version": e.get("semver") or "1.0.0",
            "supersedes": e.get("supersedes"), "scope": scope, "semantic_key": c.get("id") or e["key"],
            "name": ("VDF %s %s %s" % (zh, c.get("id", ""), c.get("name", ""))).strip()[:200], "value": value, "risk_level": "LOW",
            "environment": PRIOR.ENVIRONMENT, "libraries": [], "aliases": [], "positive": [], "negative": []}


PRIOR.harvest = harvest
PRIOR.build_asset = build_asset


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    print(f"=== {TAG} · 薄尾自測(擷取總冊依大類申請中央號)===", flush=True)
    ent = fetchone_entries(HERE)
    by = {}
    for e in ent.values():
        by[e["kind"]] = by.get(e["kind"], 0) + 1
    secs = {}
    for e in ent.values():
        secs.setdefault(e["content"]["section"], set()).add(e["kind"])
    chk("① 390 項全收;六個總經大類 → MACRO · 財報 / 共識 → FINDATA · 其餘 → INSTR;每個大類只一種型別 · %s" % by,
        len(ent) == 390 and all(len(v) == 1 for v in secs.values()) and all(secs[s] == {"MACRO"} for s in MRC_SECTIONS)
        and all(secs[s] == {"FINDATA"} for s in FD_SECTIONS) and by.get("MACRO") == 124 and by.get("FINDATA") == 28 and by.get("INSTR") == 238, by)
    a = {k: build_asset(dict(e, semver="1.0.0", supersedes=None)) for k, e in ent.items()}
    x, y, z = a["VDF:FETCH:US-L01"], a["VDF:FETCH:PX-01"], a["VDF:FETCH:FN-01"]
    chk("② 申請列照候選契約:型別 MACRO / INSTRUMENT / FINDATA · scope 帶地區(mrc.us · fm.tw)· FD 不帶 · 中央號欄空白 · 欄位齊",
        x["asset_type"] == "MACRO" and x["scope"] == "vdf.fetchone.mrc.us" and y["asset_type"] == "INSTRUMENT" and y["scope"] == "vdf.fetchone.fm.tw"
        and z["asset_type"] == "FINDATA" and z["scope"] == "vdf.fetchone.fd" and all(v["ssot_code"] is None for v in a.values())
        and all(set(PRIOR.CANDIDATE_FIELDS) <= set(v) for v in a.values()) and len({v["candidate_id"] for v in a.values()}) == 390, (x, y, z))
    chk("③ 舊五類照 v0100(SSOT · CFG · REGEX · SYN · PARAM 的對照表沒動)",
        PRIOR.VCGC_KIND["REGEX"] == "RGX" and PRIOR.ASSET_TYPE["SYN"] == "SYNONYM" and PRIOR.SHORT["PARAM"] == "PRM" and PRIOR.harvest is harvest)
    with tempfile.TemporaryDirectory(prefix="vdfsync_v0101_") as td:
        d = Path(td)
        (d / FETCHONE_NAME).write_text(json.dumps({"items": [{"id": "US-L01", "section": "美國總經 · 領先", "name": "ISM", "status": "PROXY"},
                                                             {"id": "PX-01", "section": "價格 · 股/ETF/指數", "name": "台股上市", "status": "DONE"}]},
                                                  ensure_ascii=False), encoding="utf-8")
        r = PRIOR.register(d)
        book = json.loads((d / "registry" / r["register"]).read_text(encoding="utf-8"))
        e1 = book["entries"]["VDF:FETCH:US-L01"]
        r2 = PRIOR.register(d)
        chk("④ 登記冊(夾具):新條目 VDF-MRC-0001 / VDF-FM-0001 暫編 · 待 VCGC 核號;內容沒變再登記不出新版",
            e1["no"] == "VDF-MRC-0001" and book["entries"]["VDF:FETCH:PX-01"]["no"] == "VDF-FM-0001" and e1["vcgc_kind"] == "MRC"
            and "待 VCGC 核號" in e1["status"] and r2["written"] is False, (r, r2))
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑤ 加速器橋 · 網路工具橋在;本檔不另寫檔(登記冊 / 申請檔照 v0100 寫法);零網路;不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and ".write_text(" not in body and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    good = all(ok)
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if good else 'FAIL'}", flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
