#!/usr/bin/env python3
"""VIA VCG Gateway — single PY + SSOT.

Protocols
  CodeChain : {SYSTEM}-{SUBSYSTEM}-{MODULE}-{FUNCTION}-{LIBNAME}-{LIBVER}
  KNO       : KNO-{DOMAIN}-{COUNTRY?}-{CATEGORY}-{TYPE}-{SOURCE}-{FREQ}-{VERSION}-{SEQ4}
  IDX       : IDX-{MARKET}-{COUNTRY}-{FAMILY}-{SYMBOL}-{SOURCE}-{FREQ}-{VERSION}-{SEQ4}
  PRD       : PRD-{ASSET}-{COUNTRY}-{FAMILY}-{SYMBOL}-{VENUE}-{FREQ}-{VERSION}-{SEQ4}
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


import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

PROTOCOL_CC = "AutoCode Naming Protocol v1.1"
PROTOCOL_KNO = "KNO-Unified Protocol v1.0"
SYSTEM_DEFAULT = "VIA"
ALLOWED_SYSTEMS = ("VIA",)
ALLOWED_SUBSYSTEMS = ("VRN", "VDF", "VAP")
MDL_WIDTH = 3
FNC_WIDTH = 3
SEQ_WIDTH = 4
NO_COUNTRY_DOMAINS = ("TA", "STAT", "ML")

CODECHAIN_RE = re.compile(
    r"^(?P<system>[A-Z]+)-"
    r"(?P<subsystem>[A-Z]+)-"
    r"(?P<module>MDL\d{3})-"
    r"(?P<function>FNC\d{3})-"
    r"(?P<libname>[A-Z][A-Z0-9_]*)-"
    r"V(?P<libver>\d+\.\d+)$"
)
KNO_RE = re.compile(
    r"^KNO-"
    r"(?P<domain>[A-Z]+)-"
    r"(?:(?P<country>[A-Z]+)-)?"
    r"(?P<category>[A-Z0-9_]+)-"
    r"(?P<type>[A-Z0-9_]+)-"
    r"(?P<source>[A-Z0-9]+)-"
    r"(?P<freq>[MQWDTA])-"
    r"(?P<version>V[1-5])-"
    r"(?P<seq>\d{4})$"
)
IDX_RE = re.compile(
    r"^IDX-"
    r"(?P<market>[A-Z]+)-"
    r"(?P<country>[A-Z]+)-"
    r"(?P<family>[A-Z]+)-"
    r"(?P<symbol>[A-Z0-9]+)-"
    r"(?P<source>[A-Z0-9]+)-"
    r"(?P<freq>[MQWDTA])-"
    r"(?P<version>V[1-5])-"
    r"(?P<seq>\d{4})$"
)
PRD_RE = re.compile(
    r"^PRD-"
    r"(?P<asset>[A-Z]+)-"
    r"(?P<country>[A-Z]+)-"
    r"(?P<family>[A-Z]+)-"
    r"(?P<symbol>[A-Z0-9]+)-"
    r"(?P<venue>[A-Z0-9]+)-"
    r"(?P<freq>[MQWDTA])-"
    r"(?P<version>V[1-5])-"
    r"(?P<seq>\d{4})$"
)
PROMOTE_STATES = (
    "DRAFT",
    "VALIDATED",
    "STAGED",
    "PROMOTED",
    "FROZEN",
    "RETIRED",
)
PROMOTE_TRANSITIONS = {
    "DRAFT": ("VALIDATED", "RETIRED"),
    "VALIDATED": ("STAGED", "DRAFT", "RETIRED"),
    "STAGED": ("PROMOTED", "VALIDATED", "RETIRED"),
    "PROMOTED": ("FROZEN", "RETIRED"),
    "FROZEN": ("RETIRED",),
    "RETIRED": (),
}
HERE = Path(__file__).resolve().parent
DEFAULT_SSOT = HERE / "vcg" / "ssot"


class AutoCodeError(Exception):
    """Protocol or SSOT violation."""


def now_ts() -> int:
    return int(time.time())


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def pad_mdl(index: int) -> str:
    return f"MDL{index:0{MDL_WIDTH}d}"


def pad_fnc(index: int) -> str:
    return f"FNC{index:0{FNC_WIDTH}d}"


def pad_seq(index: int) -> str:
    return f"{index:0{SEQ_WIDTH}d}"


def parse_libver(version: str) -> tuple[int, int]:
    parts = version.split(".")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        raise AutoCodeError(f"LIBVER 非法: {version}")
    return int(parts[0]), int(parts[1])


def build_codechain(
    system: str,
    subsystem: str,
    module_idx: int,
    function_idx: int,
    libname: str,
    libver: str,
) -> str:
    return (
        f"{system}-{subsystem}-{pad_mdl(module_idx)}-"
        f"{pad_fnc(function_idx)}-{libname}-V{libver}"
    )


def validate_codechain(codechain: str) -> dict[str, str]:
    match = CODECHAIN_RE.match(codechain)
    if not match:
        raise AutoCodeError(f"CodeChain 語法非法: {codechain}")
    return match.groupdict()


def validate_kno(code: str) -> dict[str, str]:
    match = KNO_RE.match(code)
    if not match:
        raise AutoCodeError(f"KNO 語法非法: {code}")
    return {k: (v or "") for k, v in match.groupdict().items()}


def validate_idx(code: str) -> dict[str, str]:
    match = IDX_RE.match(code)
    if not match:
        raise AutoCodeError(f"IDX 語法非法: {code}")
    return match.groupdict()


def validate_prd(code: str) -> dict[str, str]:
    match = PRD_RE.match(code)
    if not match:
        raise AutoCodeError(f"PRD 語法非法: {code}")
    return match.groupdict()


def build_kno(
    domain: str,
    country: str | None,
    category: str,
    typ: str,
    source: str,
    freq: str,
    version: str,
    seq: int,
) -> str:
    parts = ["KNO", domain]
    if country:
        parts.append(country)
    parts.extend([category, typ, source, freq, version, pad_seq(seq)])
    return "-".join(parts)


def kno_fingerprint(
    domain: str,
    country: str | None,
    category: str,
    typ: str,
    source: str,
    freq: str,
    version: str,
) -> str:
    mid = country or "NA"
    return f"{domain}-{mid}-{category}-{typ}-{source}-{freq}-{version}"


class SSOT:
    """Single Source of Truth paths and IO."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.registry = root / "registry"
        self.ledger = root / "ledger" / "audit.log"
        self.ver_root = root / "versions"
        self.lib = self.registry / "lib.registry.json"
        self.module = self.registry / "module.registry.json"
        self.function = self.registry / "function.registry.json"
        self.codechain = self.registry / "codechain.registry.json"
        self.artifact = self.registry / "artifact.registry.json"
        self.worldline = self.registry / "worldline.registry.json"
        self.engine = self.registry / "engine.registry.json"
        self.factor = self.registry / "factor.registry.json"
        self.taxonomy = self.registry / "kno.taxonomy.json"
        self.kno = self.registry / "kno.registry.json"
        self.index = self.registry / "index.registry.json"
        self.product = self.registry / "product.registry.json"
        self.governance = self.registry / "governance.registry.json"

    def ensure(self) -> None:
        self.registry.mkdir(parents=True, exist_ok=True)
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        for name in ("codechain", "kno", "index", "product", "governance"):
            (self.ver_root / name).mkdir(parents=True, exist_ok=True)
        if not self.ledger.exists():
            self.ledger.write_text("", encoding="utf-8")

    def ledger_write(self, entry: dict[str, Any]) -> None:
        self.ensure()
        with self.ledger.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def snapshot(self, family: str, payload: dict[str, Any], key: str) -> Path:
        self.ensure()
        out = self.ver_root / family / f"{now_ts()}_{key}.json"
        write_json(out, payload)
        return out


class KnowledgeClassifier:
    """SSOT-driven multi-head classifier (Transformer 介面可替換)."""

    COUNTRY_HINTS = {
        "US": ("US", "USA", "UNITED STATES", "AMERICA", "美國"),
        "CN": ("CN", "CHINA", "PRC", "中國", "内地"),
        "JP": ("JP", "JAPAN", "日本"),
        "TW": ("TW", "TAIWAN", "TAIWAN", "台灣", "臺灣"),
        "EU": ("EU", "EURO", "EUROZONE", "EURO AREA", "歐洲"),
        "GLOBAL": ("GLOBAL", "WORLD", "全球"),
    }
    FREQ_HINTS = {
        "M": ("MONTHLY", "MOM", "月"),
        "Q": ("QUARTERLY", "QOQ", "季"),
        "W": ("WEEKLY", "週", "周"),
        "D": ("DAILY", "日"),
        "T": ("TICK", "INTRADAY", "分鐘"),
        "A": ("ANNUAL", "YOY", "年"),
    }
    VERSION_HINTS = {
        "V4": ("NOWCAST", "FORECAST", "PREDICT"),
        "V3": ("SEASONAL", "SA", "季調"),
        "V2": ("CLEAN", "ADJUSTED", "清洗"),
        "V5": ("ENHANCED", "VIA SPECIAL"),
        "V1": ("RAW", "原始"),
    }
    SOURCE_HINTS = {
        "ISM": ("ISM",),
        "BLS": ("BLS",),
        "BEA": ("BEA",),
        "ADP": ("ADP",),
        "ATLANTA": ("ATLANTA", "GDPNOW"),
        "FED": ("FED", "FOMC"),
        "NBS": ("NBS", "國家統計局"),
        "OECD": ("OECD",),
        "IMF": ("IMF",),
        "GS": ("GOLDMAN", " GS"),
        "TWSE": ("TWSE", "上市"),
        "SPGLOBAL": ("S&P", "SPGLOBAL", "S AND P"),
        "MARKIT": ("MARKIT", "S&P GLOBAL PMI"),
        "VIA": ("VIA",),
    }
    TOKEN_MAP = (
        ("NEWORD", "NEWORD", "PMI", "MACRO", ("NEW ORDER", "NEWORDERS", "新訂單")),
        ("HEAD", "HEAD", "PMI", "MACRO", ("MANUFACTURING PMI", "PMI HEADLINE", "製造業PMI")),
        ("CORE_CPI", "CORE_CPI", "INFLATION", "MACRO", ("CORE CPI", "核心CPI")),
        ("CPI", "CPI", "INFLATION", "MACRO", ("CPI", "通膨", "通脹")),
        ("GDP_YOY", "GDP_YOY", "GDP", "MACRO", ("GDP YOY", "GDPNOW", "GDP")),
        ("NFP", "HEAD", "NFP", "LABOR", ("NONFARM", "NFP", "非農")),
        ("ADP", "HEAD", "ADP", "LABOR", ("ADP",)),
        ("RSI", "RSI", "MOMENTUM", "TA", ("RSI",)),
        ("MACD", "MACD", "TREND", "TA", ("MACD",)),
        ("SMA", "SMA", "TREND", "TA", ("SMA", "SIMPLE MOVING")),
        ("EMA", "EMA", "TREND", "TA", ("EMA",)),
        ("ATR", "ATR", "VOLATILITY", "TA", ("ATR",)),
        ("BBANDS", "BBANDS", "VOLATILITY", "TA", ("BOLLINGER", "BBAND")),
        ("TTEST", "TTEST", "TEST", "STAT", ("T-TEST", "TTEST")),
        ("ARIMA", "ARIMA", "TS", "STAT", ("ARIMA",)),
        ("GARCH", "GARCH", "TS", "STAT", ("GARCH",)),
        ("XGBOOST", "XGBOOST", "MODEL", "ML", ("XGBOOST", "XGB")),
        ("VAR", "HIST", "VAR", "RISK", ("VALUE AT RISK", "VAR")),
    )

    def __init__(self, taxonomy: dict[str, Any]) -> None:
        self.tax = taxonomy

    def classify(self, text: str) -> dict[str, Any]:
        raw = text or ""
        blob = raw.upper()
        domain = "OTHER"
        category = "MISC"
        typ = "MISC"
        for _key, type_code, cat, dom, hints in self.TOKEN_MAP:
            if any(h in blob for h in hints):
                domain, category, typ = dom, cat, type_code
                break
        country = self._first(blob, self.COUNTRY_HINTS)
        if domain in self.tax.get("stateless_domains", list(NO_COUNTRY_DOMAINS)):
            if country is None:
                country = None
        elif country is None:
            country = "US" if any(x in blob for x in ("ISM", "BLS", "BEA", "ADP", "FED")) else None
        source = self._first(blob, self.SOURCE_HINTS) or (
            "VIA" if domain in ("TA", "STAT", "ML", "RISK") else "VIA"
        )
        freq = self._first(blob, self.FREQ_HINTS)
        if freq is None:
            freq = "D" if domain in ("TA", "STAT", "ML") else "M"
        version = self._first(blob, self.VERSION_HINTS) or "V1"
        fields = {
            "domain": domain,
            "country": country,
            "category": category,
            "type": typ,
            "source": source,
            "freq": freq,
            "version": version,
            "text": raw,
        }
        return fields

    @staticmethod
    def _first(blob: str, table: dict[str, tuple[str, ...]]) -> str | None:
        for code, hints in table.items():
            if any(h in blob for h in hints):
                return code
        return None


class AutoCodeEngine:
    """VCG Gateway: CodeChain + KNO + IDX + PRD + Governance."""

    def __init__(self, ssot: SSOT) -> None:
        self.ssot = ssot
        self.ssot.ensure()
        self.tax = load_json(self.ssot.taxonomy)
        self.clf = KnowledgeClassifier(self.tax)

    def generate(
        self,
        system: str,
        subsystem: str,
        libname: str,
        *,
        new_module: bool = False,
        module_code: str | None = None,
        worldline: str | None = None,
        engine: str | None = None,
        factor: str | None = None,
        created_by: str = "VCG-Gateway",
    ) -> dict[str, Any]:
        system = system.upper()
        subsystem = subsystem.upper()
        libname = libname.upper()
        self._check_ids(system, subsystem, libname)
        self._check_bindings(worldline, engine, factor)

        lib_reg = load_json(self.ssot.lib)
        module_reg = self._ensure_bucket(
            load_json(self.ssot.module), "modules", subsystem
        )
        function_reg = self._ensure_bucket(
            load_json(self.ssot.function), "functions", subsystem
        )
        chain_reg = load_json(self.ssot.codechain)
        chain_reg.setdefault("schema", "VIA.SSOT.CODECHAIN.v1.1")
        chain_reg.setdefault("codechains", [])

        libver = self._libver(lib_reg, libname)
        major, minor = parse_libver(libver)
        module_idx, module_code_out = self._next_module(
            module_reg, subsystem, new_module, module_code, created_by
        )
        function_idx, function_code = self._next_function(
            function_reg, subsystem, module_code_out, created_by
        )
        codechain = build_codechain(
            system, subsystem, module_idx, function_idx, libname, libver
        )
        validate_codechain(codechain)
        self._assert_unique(chain_reg["codechains"], "codechain", codechain)
        obj = {
            "system": system,
            "subsystem": subsystem,
            "module": {"code": module_code_out, "index": module_idx},
            "function": {"code": function_code, "index": function_idx},
            "library": {
                "name": libname,
                "version": libver,
                "major": major,
                "minor": minor,
            },
            "codechain": codechain,
            "promotion": {"state": "DRAFT", "artifact_id": None},
            "worldline": worldline,
            "engine": engine,
            "factor": factor,
            "metadata": {
                "created_at": now_ts(),
                "created_by": created_by,
                "protocol": PROTOCOL_CC,
            },
        }
        chain_reg["codechains"].append(obj)
        write_json(self.ssot.codechain, chain_reg)
        write_json(self.ssot.module, module_reg)
        write_json(self.ssot.function, function_reg)
        self.ssot.snapshot("codechain", obj, codechain)
        self.ssot.ledger_write(
            {
                "event": "codechain_generate",
                "codechain": codechain,
                "timestamp": now_ts(),
                "created_by": created_by,
            }
        )
        return obj

    def lookup(self, codechain: str) -> dict[str, Any]:
        validate_codechain(codechain)
        for item in load_json(self.ssot.codechain).get("codechains", []):
            if item.get("codechain") == codechain:
                return item
        raise AutoCodeError(f"CodeChain 不存在: {codechain}")

    def list_all(self) -> list[dict[str, Any]]:
        return list(load_json(self.ssot.codechain).get("codechains", []))

    def promote(
        self,
        codechain: str,
        target_state: str,
        *,
        artifact_kind: str = "FUNCTION",
        artifact_ref: str | None = None,
        created_by: str = "VCG-Gateway",
    ) -> dict[str, Any]:
        target_state = target_state.upper()
        if target_state not in PROMOTE_STATES:
            raise AutoCodeError(f"Promotion state 非法: {target_state}")
        chain_reg = load_json(self.ssot.codechain)
        found = self._find(chain_reg.get("codechains", []), "codechain", codechain)
        current = found.get("promotion", {}).get("state", "DRAFT")
        allowed = PROMOTE_TRANSITIONS.get(current, ())
        if target_state != current and target_state not in allowed:
            raise AutoCodeError(
                f"非法轉移 {current} → {target_state}; 允許={list(allowed)}"
            )
        art_reg = load_json(self.ssot.artifact)
        art_reg.setdefault("schema", "VIA.SSOT.ARTIFACT.v1.1")
        art_reg.setdefault("artifacts", [])
        artifact_id = found.get("promotion", {}).get("artifact_id")
        if artifact_id is None:
            artifact_id = f"ART-{len(art_reg['artifacts']) + 1:04d}"
            art_reg["artifacts"].append(
                {
                    "artifact_id": artifact_id,
                    "kind": artifact_kind.upper(),
                    "codechain": codechain,
                    "ref": artifact_ref,
                    "state": target_state,
                    "worldline": found.get("worldline"),
                    "engine": found.get("engine"),
                    "factor": found.get("factor"),
                    "metadata": {
                        "created_at": now_ts(),
                        "created_by": created_by,
                        "updated_at": now_ts(),
                    },
                }
            )
        else:
            art_obj = self._find(art_reg["artifacts"], "artifact_id", artifact_id)
            art_obj["state"] = target_state
            art_obj["metadata"]["updated_at"] = now_ts()
        found["promotion"] = {"state": target_state, "artifact_id": artifact_id}
        write_json(self.ssot.codechain, chain_reg)
        write_json(self.ssot.artifact, art_reg)
        self.ssot.snapshot("codechain", found, codechain)
        self.ssot.ledger_write(
            {
                "event": "artifact_promote",
                "codechain": codechain,
                "from": current,
                "to": target_state,
                "artifact_id": artifact_id,
                "timestamp": now_ts(),
                "created_by": created_by,
            }
        )
        return found

    def bind(
        self,
        codechain: str,
        *,
        worldline: str | None = None,
        engine: str | None = None,
        factor: str | None = None,
        created_by: str = "VCG-Gateway",
    ) -> dict[str, Any]:
        self._check_bindings(worldline, engine, factor)
        chain_reg = load_json(self.ssot.codechain)
        found = self._find(chain_reg.get("codechains", []), "codechain", codechain)
        if worldline is not None:
            found["worldline"] = worldline
        if engine is not None:
            found["engine"] = engine
        if factor is not None:
            found["factor"] = factor
        write_json(self.ssot.codechain, chain_reg)
        self.ssot.snapshot("codechain", found, codechain)
        self.ssot.ledger_write(
            {
                "event": "codechain_bind",
                "codechain": codechain,
                "worldline": found.get("worldline"),
                "engine": found.get("engine"),
                "factor": found.get("factor"),
                "timestamp": now_ts(),
                "created_by": created_by,
            }
        )
        return found

    def matrix_wef(self) -> list[dict[str, Any]]:
        rows = []
        for item in self.list_all():
            rows.append(
                {
                    "codechain": item.get("codechain"),
                    "subsystem": item.get("subsystem"),
                    "libname": item.get("library", {}).get("name"),
                    "libver": item.get("library", {}).get("version"),
                    "worldline": item.get("worldline"),
                    "engine": item.get("engine"),
                    "factor": item.get("factor"),
                    "promotion": item.get("promotion", {}).get("state"),
                    "artifact_id": item.get("promotion", {}).get("artifact_id"),
                }
            )
        return rows

    def kno_classify(self, text: str) -> dict[str, Any]:
        return self.clf.classify(text)

    def kno_generate(
        self,
        *,
        domain: str | None = None,
        country: str | None = None,
        category: str | None = None,
        typ: str | None = None,
        source: str | None = None,
        freq: str | None = None,
        version: str = "V1",
        text: str | None = None,
        force_new: bool = False,
        created_by: str = "VCG-Gateway",
    ) -> dict[str, Any]:
        inferred = self.clf.classify(text or "") if text else {}
        domain = (domain or inferred.get("domain") or "OTHER").upper()
        category = (category or inferred.get("category") or "MISC").upper()
        typ = (typ or inferred.get("type") or "MISC").upper()
        source = (source or inferred.get("source") or "VIA").upper()
        freq = (freq or inferred.get("freq") or "M").upper()
        version = (version or inferred.get("version") or "V1").upper()
        country_raw = country if country is not None else inferred.get("country")
        country = country_raw.upper() if country_raw else None
        if domain in self.tax.get("stateless_domains", list(NO_COUNTRY_DOMAINS)):
            if country is None:
                country = None
        self._validate_kno_fields(domain, country, category, typ, source, freq, version)
        fp = kno_fingerprint(domain, country, category, typ, source, freq, version)
        store = self._load_seq_store(self.ssot.kno, "VIA.SSOT.KNO.v1.0")
        if not force_new:
            for item in store["items"]:
                if item.get("fingerprint") == fp:
                    return item
        seq = int(store.get("latest_index", 0)) + 1
        code = build_kno(domain, country, category, typ, source, freq, version, seq)
        validate_kno(code)
        obj = {
            "kno": code,
            "domain": domain,
            "country": country,
            "category": category,
            "type": typ,
            "source": source,
            "freq": freq,
            "version": version,
            "seq": seq,
            "fingerprint": fp,
            "text": text,
            "metadata": {
                "created_at": now_ts(),
                "created_by": created_by,
                "protocol": PROTOCOL_KNO,
            },
        }
        store["items"].append(obj)
        store["latest_index"] = seq
        write_json(self.ssot.kno, store)
        self.ssot.snapshot("kno", obj, code)
        self.ssot.ledger_write(
            {
                "event": "kno_generate",
                "kno": code,
                "timestamp": now_ts(),
                "created_by": created_by,
            }
        )
        return obj

    def idx_generate(
        self,
        market: str,
        country: str,
        family: str,
        symbol: str,
        source: str,
        freq: str,
        version: str = "V1",
        *,
        force_new: bool = False,
        created_by: str = "VCG-Gateway",
    ) -> dict[str, Any]:
        market, country, family = market.upper(), country.upper(), family.upper()
        symbol, source, freq, version = (
            symbol.upper(),
            source.upper(),
            freq.upper(),
            version.upper(),
        )
        self._in_tax("index_markets", market)
        self._in_tax("countries", country)
        self._in_tax("index_families", family)
        self._in_tax("freqs", freq)
        self._in_tax_version(version)
        fp = f"{market}-{country}-{family}-{symbol}-{source}-{freq}-{version}"
        store = self._load_seq_store(self.ssot.index, "VIA.SSOT.IDX.v1.0")
        if not force_new:
            for item in store["items"]:
                if item.get("fingerprint") == fp:
                    return item
        seq = int(store.get("latest_index", 0)) + 1
        code = (
            f"IDX-{market}-{country}-{family}-{symbol}-"
            f"{source}-{freq}-{version}-{pad_seq(seq)}"
        )
        validate_idx(code)
        obj = {
            "index": code,
            "market": market,
            "country": country,
            "family": family,
            "symbol": symbol,
            "source": source,
            "freq": freq,
            "version": version,
            "seq": seq,
            "fingerprint": fp,
            "metadata": {
                "created_at": now_ts(),
                "created_by": created_by,
            },
        }
        store["items"].append(obj)
        store["latest_index"] = seq
        write_json(self.ssot.index, store)
        self.ssot.snapshot("index", obj, code)
        self.ssot.ledger_write(
            {
                "event": "idx_generate",
                "index": code,
                "timestamp": now_ts(),
                "created_by": created_by,
            }
        )
        return obj

    def prd_generate(
        self,
        asset: str,
        country: str,
        family: str,
        symbol: str,
        venue: str,
        freq: str,
        version: str = "V1",
        *,
        force_new: bool = False,
        created_by: str = "VCG-Gateway",
    ) -> dict[str, Any]:
        asset, country, family = asset.upper(), country.upper(), family.upper()
        symbol, venue, freq, version = (
            symbol.upper(),
            venue.upper(),
            freq.upper(),
            version.upper(),
        )
        self._in_tax("product_assets", asset)
        self._in_tax("countries", country)
        self._in_tax("product_families", family)
        self._in_tax("freqs", freq)
        self._in_tax_version(version)
        fp = f"{asset}-{country}-{family}-{symbol}-{venue}-{freq}-{version}"
        store = self._load_seq_store(self.ssot.product, "VIA.SSOT.PRD.v1.0")
        if not force_new:
            for item in store["items"]:
                if item.get("fingerprint") == fp:
                    return item
        seq = int(store.get("latest_index", 0)) + 1
        code = (
            f"PRD-{asset}-{country}-{family}-{symbol}-"
            f"{venue}-{freq}-{version}-{pad_seq(seq)}"
        )
        validate_prd(code)
        obj = {
            "product": code,
            "asset": asset,
            "country": country,
            "family": family,
            "symbol": symbol,
            "venue": venue,
            "freq": freq,
            "version": version,
            "seq": seq,
            "fingerprint": fp,
            "metadata": {
                "created_at": now_ts(),
                "created_by": created_by,
            },
        }
        store["items"].append(obj)
        store["latest_index"] = seq
        write_json(self.ssot.product, store)
        self.ssot.snapshot("product", obj, code)
        self.ssot.ledger_write(
            {
                "event": "prd_generate",
                "product": code,
                "timestamp": now_ts(),
                "created_by": created_by,
            }
        )
        return obj

    def gov_link(
        self,
        *,
        kno: str | None = None,
        codechain: str | None = None,
        index: str | None = None,
        product: str | None = None,
        role: str = "MEASURES",
        created_by: str = "VCG-Gateway",
    ) -> dict[str, Any]:
        if not any((kno, codechain, index, product)):
            raise AutoCodeError("至少提供 kno / codechain / index / product 之一")
        role = role.upper()
        self._in_tax("link_roles", role)
        if kno:
            validate_kno(kno)
            self._must_exist(load_json(self.ssot.kno).get("items", []), "kno", kno)
        if codechain:
            self.lookup(codechain)
        if index:
            validate_idx(index)
            self._must_exist(load_json(self.ssot.index).get("items", []), "index", index)
        if product:
            validate_prd(product)
            self._must_exist(
                load_json(self.ssot.product).get("items", []), "product", product
            )
        store = load_json(self.ssot.governance)
        store.setdefault("schema", "VIA.SSOT.GOV.v1.0")
        store.setdefault("links", [])
        store.setdefault("latest_index", 0)
        for row in store["links"]:
            if (
                row.get("kno") == kno
                and row.get("codechain") == codechain
                and row.get("index") == index
                and row.get("product") == product
                and row.get("role") == role
            ):
                return row
        seq = int(store.get("latest_index", 0)) + 1
        obj = {
            "link_id": f"LNK-{pad_seq(seq)}",
            "kno": kno,
            "codechain": codechain,
            "index": index,
            "product": product,
            "role": role,
            "metadata": {
                "created_at": now_ts(),
                "created_by": created_by,
            },
        }
        store["links"].append(obj)
        store["latest_index"] = seq
        write_json(self.ssot.governance, store)
        self.ssot.snapshot("governance", obj, obj["link_id"])
        self.ssot.ledger_write(
            {
                "event": "gov_link",
                "link_id": obj["link_id"],
                "timestamp": now_ts(),
                "created_by": created_by,
            }
        )
        return obj

    def gov_matrix(self) -> list[dict[str, Any]]:
        return list(load_json(self.ssot.governance).get("links", []))

    def health(self) -> dict[str, Any]:
        issues: list[str] = []
        lib_reg = load_json(self.ssot.lib).get("libraries", {})
        chains = self.list_all()
        seen: set[str] = set()
        for item in chains:
            cc = item.get("codechain", "")
            try:
                validate_codechain(cc)
            except AutoCodeError as exc:
                issues.append(str(exc))
            if cc in seen:
                issues.append(f"重複 CodeChain: {cc}")
            seen.add(cc)
            name = item.get("library", {}).get("name")
            ver = item.get("library", {}).get("version")
            if name not in lib_reg:
                issues.append(f"LIBNAME 未註冊: {name}")
            elif lib_reg[name].get("version") != ver:
                issues.append(f"LIBVER drift {cc}")
        for path, key, validator in (
            (self.ssot.kno, "kno", validate_kno),
            (self.ssot.index, "index", validate_idx),
            (self.ssot.product, "product", validate_prd),
        ):
            found: set[str] = set()
            for item in load_json(path).get("items", []):
                code = item.get(key, "")
                try:
                    validator(code)
                except AutoCodeError as exc:
                    issues.append(str(exc))
                if code in found:
                    issues.append(f"重複 {key}: {code}")
                found.add(code)
        n_kno = len(load_json(self.ssot.kno).get("items", []))
        n_idx = len(load_json(self.ssot.index).get("items", []))
        n_prd = len(load_json(self.ssot.product).get("items", []))
        n_lnk = len(load_json(self.ssot.governance).get("links", []))
        status = "GREEN" if not issues else ("YELLOW" if len(issues) < 5 else "RED")
        return {
            "status": status,
            "codechain_count": len(chains),
            "kno_count": n_kno,
            "index_count": n_idx,
            "product_count": n_prd,
            "link_count": n_lnk,
            "lib_count": len(lib_reg),
            "issues": issues,
        }

    def routes(self) -> dict[str, str]:
        return {
            "GENERATE_CC": "User → Gateway → generate → CC/Module/Function SSOT → Ledger → Version",
            "GENERATE_KNO": "Text/Fields → Classifier → Validator → kno.registry → Ledger → Version",
            "GENERATE_IDX": "Fields → Validator → index.registry → Ledger → Version",
            "GENERATE_PRD": "Fields → Validator → product.registry → Ledger → Version",
            "CLASSIFY": "Raw text → KnowledgeClassifier → fields",
            "LINK": "Gateway → gov_link → governance.registry → Ledger",
            "PROMOTE": "Gateway → promote → artifact.registry → Ledger",
            "HEALTH": "Monitor → health → RYG",
            "READ": "Subsystem → SSOT.Read",
        }

    def _validate_kno_fields(
        self,
        domain: str,
        country: str | None,
        category: str,
        typ: str,
        source: str,
        freq: str,
        version: str,
    ) -> None:
        domains = set(self.tax.get("domains", []))
        if domain not in domains:
            raise AutoCodeError(f"DOMAIN 非法: {domain}")
        if country:
            self._in_tax("countries", country)
        cats = self.tax.get("categories", {}).get(domain, [])
        if cats and category not in cats:
            raise AutoCodeError(f"CATEGORY 不屬於 {domain}: {category}")
        types = self.tax.get("types", {}).get(category, [])
        if types and typ not in types:
            raise AutoCodeError(f"TYPE 不屬於 {category}: {typ}")
        allowed_src = set()
        for group in self.tax.get("sources", {}).values():
            allowed_src.update(group)
        if source not in allowed_src:
            raise AutoCodeError(f"SOURCE 未註冊: {source}")
        self._in_tax("freqs", freq)
        self._in_tax_version(version)

    def _in_tax(self, key: str, value: str) -> None:
        allowed = self.tax.get(key, [])
        if allowed and value not in allowed:
            raise AutoCodeError(f"{key} 非法: {value}")

    def _in_tax_version(self, version: str) -> None:
        versions = self.tax.get("versions", {})
        if versions and version not in versions:
            raise AutoCodeError(f"VERSION 非法: {version}")

    def _load_seq_store(self, path: Path, schema: str) -> dict[str, Any]:
        store = load_json(path)
        store.setdefault("schema", schema)
        store.setdefault("latest_index", 0)
        store.setdefault("items", [])
        return store

    def _check_ids(self, system: str, subsystem: str, libname: str) -> None:
        if system not in ALLOWED_SYSTEMS:
            raise AutoCodeError(f"SYSTEM 非法: {system}")
        if subsystem not in ALLOWED_SUBSYSTEMS:
            raise AutoCodeError(f"SUBSYSTEM 非法: {subsystem}")
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", libname):
            raise AutoCodeError(f"LIBNAME 非法: {libname}")
        if libname.startswith("LIB") and libname[3:].isdigit():
            raise AutoCodeError("LIBNAME 不可使用數字編碼")

    def _libver(self, lib_reg: dict[str, Any], libname: str) -> str:
        libraries = lib_reg.get("libraries", {})
        if libname not in libraries:
            raise AutoCodeError(f"LIBNAME 未於 SSOT 註冊: {libname}")
        rec = libraries[libname]
        if rec.get("status") != "active":
            raise AutoCodeError(f"LIBNAME 非 active: {libname}")
        version = rec.get("version")
        if not version:
            raise AutoCodeError(f"LIBVER 缺失: {libname}")
        parse_libver(version)
        return version

    def _check_bindings(
        self,
        worldline: str | None,
        engine: str | None,
        factor: str | None,
    ) -> None:
        if worldline:
            wl = load_json(self.ssot.worldline).get("worldlines", {})
            if worldline not in wl:
                raise AutoCodeError(f"世界線未註冊: {worldline}")
        if engine:
            eng = load_json(self.ssot.engine).get("engines", {})
            if engine not in eng:
                raise AutoCodeError(f"引擎未註冊: {engine}")
        if factor:
            fct = load_json(self.ssot.factor).get("factors", {})
            if factor not in fct:
                raise AutoCodeError(f"因子未註冊: {factor}")

    def _ensure_bucket(
        self,
        registry: dict[str, Any],
        top: str,
        subsystem: str,
    ) -> dict[str, Any]:
        registry.setdefault(top, {})
        registry[top].setdefault(subsystem, {"latest_index": 0, "items": []})
        return registry

    def _next_module(
        self,
        module_reg: dict[str, Any],
        subsystem: str,
        new_module: bool,
        module_code: str | None,
        created_by: str,
    ) -> tuple[int, str]:
        bucket = module_reg["modules"][subsystem]
        items = bucket.setdefault("items", [])
        if module_code:
            for item in items:
                if item["code"] == module_code:
                    return item["index"], module_code
            raise AutoCodeError(f"MODULE 不存在: {module_code}")
        if not new_module and items:
            latest = max(items, key=lambda row: row["index"])
            return latest["index"], latest["code"]
        nxt = int(bucket.get("latest_index", 0)) + 1
        code = pad_mdl(nxt)
        items.append(
            {
                "code": code,
                "index": nxt,
                "subsystem": subsystem,
                "metadata": {"created_at": now_ts(), "created_by": created_by},
            }
        )
        bucket["latest_index"] = nxt
        return nxt, code

    def _next_function(
        self,
        function_reg: dict[str, Any],
        subsystem: str,
        module_code: str,
        created_by: str,
    ) -> tuple[int, str]:
        bucket = function_reg["functions"][subsystem]
        items = bucket.setdefault("items", [])
        nxt = int(bucket.get("latest_index", 0)) + 1
        code = pad_fnc(nxt)
        items.append(
            {
                "code": code,
                "index": nxt,
                "subsystem": subsystem,
                "module_code": module_code,
                "metadata": {"created_at": now_ts(), "created_by": created_by},
            }
        )
        bucket["latest_index"] = nxt
        return nxt, code

    @staticmethod
    def _assert_unique(items: list[dict[str, Any]], key: str, value: str) -> None:
        for item in items:
            if item.get(key) == value:
                raise AutoCodeError(f"{key} 已存在: {value}")

    @staticmethod
    def _find(items: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
        for item in items:
            if item.get(key) == value:
                return item
        raise AutoCodeError(f"{key} 不存在: {value}")

    def _must_exist(self, items: list[dict[str, Any]], key: str, value: str) -> None:
        self._find(items, key, value)


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="VIA_AutoCodeGenerator.py",
        description="VIA VCG Gateway — CodeChain × KNO × IDX × PRD",
    )
    parser.add_argument("--ssot", default=str(DEFAULT_SSOT))
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("generate", help="生成 CodeChain")
    gen.add_argument("--system", default=SYSTEM_DEFAULT)
    gen.add_argument("--subsystem", required=True)
    gen.add_argument("--libname", required=True)
    gen.add_argument("--new-module", action="store_true")
    gen.add_argument("--module-code", default=None)
    gen.add_argument("--worldline", default=None)
    gen.add_argument("--engine", default=None)
    gen.add_argument("--factor", default=None)

    look = sub.add_parser("lookup", help="讀取 CodeChain")
    look.add_argument("codechain")
    sub.add_parser("list", help="列出 CodeChain")

    bind = sub.add_parser("bind", help="綁定世界線/引擎/因子")
    bind.add_argument("codechain")
    bind.add_argument("--worldline", default=None)
    bind.add_argument("--engine", default=None)
    bind.add_argument("--factor", default=None)

    promo = sub.add_parser("promote", help="Artifact Promotion")
    promo.add_argument("codechain")
    promo.add_argument("--state", required=True)
    promo.add_argument("--kind", default="FUNCTION")
    promo.add_argument("--ref", default=None)

    clf = sub.add_parser("classify", help="KNO 分類（不寫入）")
    clf.add_argument("text")

    kno = sub.add_parser("kno", help="生成 KNO（可從文本分類）")
    kno.add_argument("--text", default=None)
    kno.add_argument("--domain", default=None)
    kno.add_argument("--country", default=None)
    kno.add_argument("--category", default=None)
    kno.add_argument("--type", dest="typ", default=None)
    kno.add_argument("--source", default=None)
    kno.add_argument("--freq", default=None)
    kno.add_argument("--version", default=None)
    kno.add_argument("--force-new", action="store_true")

    idx = sub.add_parser("idx", help="生成 IndexCode")
    idx.add_argument("--market", required=True)
    idx.add_argument("--country", required=True)
    idx.add_argument("--family", required=True)
    idx.add_argument("--symbol", required=True)
    idx.add_argument("--source", required=True)
    idx.add_argument("--freq", required=True)
    idx.add_argument("--version", default="V1")

    prd = sub.add_parser("prd", help="生成 ProductCode")
    prd.add_argument("--asset", required=True)
    prd.add_argument("--country", required=True)
    prd.add_argument("--family", required=True)
    prd.add_argument("--symbol", required=True)
    prd.add_argument("--venue", required=True)
    prd.add_argument("--freq", required=True)
    prd.add_argument("--version", default="V1")

    link = sub.add_parser("link", help="KNO × CC × IDX × PRD 治理連結")
    link.add_argument("--kno", default=None)
    link.add_argument("--codechain", default=None)
    link.add_argument("--index", default=None)
    link.add_argument("--product", default=None)
    link.add_argument("--role", default="MEASURES")

    sub.add_parser("matrix", help="世界線 × 引擎 × 因子")
    sub.add_parser("gov", help="治理連結矩陣")
    sub.add_parser("health", help="RYG")
    sub.add_parser("routes", help="全域路由")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = AutoCodeEngine(SSOT(Path(args.ssot)))
    try:
        if args.cmd == "generate":
            _print_json(
                engine.generate(
                    args.system,
                    args.subsystem,
                    args.libname,
                    new_module=args.new_module,
                    module_code=args.module_code,
                    worldline=args.worldline,
                    engine=args.engine,
                    factor=args.factor,
                )
            )
        elif args.cmd == "lookup":
            _print_json(engine.lookup(args.codechain))
        elif args.cmd == "list":
            _print_json(engine.list_all())
        elif args.cmd == "bind":
            _print_json(
                engine.bind(
                    args.codechain,
                    worldline=args.worldline,
                    engine=args.engine,
                    factor=args.factor,
                )
            )
        elif args.cmd == "promote":
            _print_json(
                engine.promote(
                    args.codechain,
                    args.state,
                    artifact_kind=args.kind,
                    artifact_ref=args.ref,
                )
            )
        elif args.cmd == "classify":
            _print_json(engine.kno_classify(args.text))
        elif args.cmd == "kno":
            _print_json(
                engine.kno_generate(
                    domain=args.domain,
                    country=args.country,
                    category=args.category,
                    typ=args.typ,
                    source=args.source,
                    freq=args.freq,
                    version=args.version,
                    text=args.text,
                    force_new=args.force_new,
                )
            )
        elif args.cmd == "idx":
            _print_json(
                engine.idx_generate(
                    args.market,
                    args.country,
                    args.family,
                    args.symbol,
                    args.source,
                    args.freq,
                    args.version,
                )
            )
        elif args.cmd == "prd":
            _print_json(
                engine.prd_generate(
                    args.asset,
                    args.country,
                    args.family,
                    args.symbol,
                    args.venue,
                    args.freq,
                    args.version,
                )
            )
        elif args.cmd == "link":
            _print_json(
                engine.gov_link(
                    kno=args.kno,
                    codechain=args.codechain,
                    index=args.index,
                    product=args.product,
                    role=args.role,
                )
            )
        elif args.cmd == "matrix":
            _print_json(engine.matrix_wef())
        elif args.cmd == "gov":
            _print_json(engine.gov_matrix())
        elif args.cmd == "health":
            _print_json(engine.health())
        elif args.cmd == "routes":
            _print_json(engine.routes())
        else:
            raise AutoCodeError(f"未知命令: {args.cmd}")
    except AutoCodeError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
