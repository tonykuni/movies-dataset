#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC BookStandardizer v0100 — VCGC 鎖管控的規則冊 / SSOT 優化 + 資料型態 DataFrame 標準化(操作員令 2026-10-06)。

承既有:VIA_Output_Header_SSOT(表頭定案冊)+ CGC_MDL249 DataFrameLock(核表 + 鎖帳)。本支不重做鎖,做三件事:
  audit               掃 VCGC 鎖管控冊(registry 的 VIA_Policy* / VIA_Numbering* / VIA_UI_FormatLock / VIA_Central_* / VIA_SSOT_* / VIA_FinalParameters* / VIA_Workflow_* /
                      VIA_Essentia_* / VIA_*Lock* / VIA_*Law* / VIA_*Gate* / VIA_*Registry* / VIA_Canon_* / VIA_MasterGovernance* / GovernanceRegistry)
                      + VDF / VRN 的 registry · SSOT · knowledge 冊(只讀,列給子系統看);每冊:形狀(TABLE / DICT_TABLE / NESTED / MAP / CONFIG / JSONL / CSV;MAP = 鍵→值映射不當表)
                      · 欄 · 型別(混型=黃 · 數字存字串=黃 · 格內巢狀=黃)· 主鍵候選 · 編碼(UTF-16 / BOM / CRLF)· 表頭定案冊有沒有這張表
  contract --apply    寫 VIA_DataFrameContract_SSOT_v0100.json(VCGC 自己的冊;已在 = SKIP):DataFrame 標準 = 列表 + 扁平欄 + 型別律 + 鍵律 + 編碼律 + 鏡像律
  propose --apply     把 audit 推得的表頭規格(欄名 · 型別 · 主鍵候選)寫進 VIA_Output_Header_SSOT_Candidates_v<新>.json(待審區:locked_by 留白,操作員+AI 裁後才進正冊)
  mirror --apply      VCGC 冊(TABLE / DICT_TABLE / JSONL / CSV 形狀)出標準扁平列 → registry/_df/<族>_<版>.rows.jsonl(原冊一字不動;巢狀格 → payload_json)
  --selftest          temp 沙盒
只寫:registry/VIA_DataFrameContract_SSOT_v0100.json · registry/VIA_Output_Header_SSOT_Candidates_v*.json · registry/_df/ · docs/handoff/ai 卡 · VIA_Reports/review/vcgc_books/。VDF/VRN 零改動。
燈:紅 = 讀不了 / JSON 壞 / UTF-16;黃 = 混型 · 數字存字串 · 格內巢狀 · 無表頭定案;綠 = 乾淨且表頭定案冊有;灰 = CONFIG(純設定,不當表)。
沙盒鍵: VIA_ROOT
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

import csv
import datetime
import io
import json
import os
import re
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

try:
    import pandas as pd  # noqa: F401
    HAS_PD = True
except ImportError:
    HAS_PD = False

ME = Path(__file__).resolve()
NAME = ME.stem
TAG = "v0100"
LOCKED_RE = re.compile(r"^(VIA_Policy|VIA_Numbering|VIA_UI_FormatLock|VIA_Central_|VIA_SSOT_|VIA_FinalParameters|VIA_Workflow_|VIA_Essentia_|VIA_[A-Za-z]*Lock|VIA_[A-Za-z]*Law|VIA_[A-Za-z]*Gate|VIA_[A-Za-z]*Registry|VIA_Canon_|VIA_MasterGovernance|GovernanceRegistry|VIA_DataFrame|VIA_Output_Header|VIA_LampLock|VIA_PlotDataLaw)")
EXCL = {"references", "intake", "_superseded", "VIA_RetiredEngines", "_quarantine_pip_vendor", "__pycache__", "VIA_NumberBooks", "_df", "_quarantine"}
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?)?")
NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")
SUBS = ("VCGC", "VDF", "VRN")
MAX_BYTES = 60_000_000

CONTRACT = {
    "schema": "VIA.DataFrameContract.SSOT.v1", "version": "v0100", "engine": NAME, "append_only": True,
    "purpose": "VIA 三系統所有資料冊 / 輸出表 / 需求冊 / 發號冊的 DataFrame 標準(操作員令 2026-10-06:資料型態 DATAFRAME 都要標準化);承 VIA_Output_Header_SSOT(表頭定案)與 CGC_MDL249(鎖帳)",
    "laws": [
        {"id": "DF01", "zh": "形狀律:一冊 = 一張或數張表;表 = rows 列表,每列扁平 dict,同一表每列同一組欄;dict-of-dicts 轉表時外層鍵進 `key` 欄"},
        {"id": "DF02", "zh": "欄名律:snake_case ASCII,不含空白與符號;中文欄名保留在表頭冊 zh 欄,不當程式鍵"},
        {"id": "DF03", "zh": "型別律:一欄一型(str / int / float / bool / date / datetime / json);數字不存字串;布林不存 'Y'/'N' 或 0/1 字串;缺值 = null,不用 '' / '-' / 'N/A'"},
        {"id": "DF04", "zh": "時間律:date = 'YYYY-MM-DD';datetime = ISO-8601 含時區(+08:00 或 Z);不用 Excel 序號 / 民國年 / 'YYYYMMDD' 字串當程式鍵"},
        {"id": "DF05", "zh": "巢狀律:格內不放 dict / list;必要時整塊 JSON 存 `payload_json` 字串欄,並在表頭冊註明"},
        {"id": "DF06", "zh": "鍵律:每表至少一主鍵欄(或組合鍵),非空且不重複;跨冊引用以鍵不以列序;SSOT 冊的鍵 = 子系統|來源|表(L108 ②)"},
        {"id": "DF07", "zh": "治理欄律:每列帶 sub(VCGC/VDF/VRN)· version · status(ACTIVE/DEPRECATED/RETIRED/DORMANT)· updated_at;只增不減,改版出新 version 不改舊列"},
        {"id": "DF08", "zh": "檔案律:UTF-8 無 BOM · LF · JSON 用 ensure_ascii=False indent 1;大冊(>5 萬列)用 .jsonl 一列一 JSON;CSV 僅作交換,主本不用 CSV"},
        {"id": "DF09", "zh": "鏡像律:主本可保原形狀;VCGC 出標準扁平鏡像 registry/_df/<族>_<版>.rows.jsonl 供 pandas.read_json(lines=True) 直讀;鏡像是衍生品,不手改"},
        {"id": "DF10", "zh": "定案律:表進 VIA_Output_Header_SSOT 才算定案,CGC_MDL249 鎖帳;未定案的表由本引擎列入 Candidates(待審區,locked_by 留白)→ 操作員+AI 裁 → 進正冊"},
        {"id": "DF11", "zh": "子系統律:VDF / VRN 的冊由各自 SystemManager 依本契約出新版;VCGC 只讀、只列、只鏡像,不改子系統冊(L111 ② / L114 ①)"},
    ],
    "dtype_names": ["str", "int", "float", "bool", "date", "datetime", "json"],
    "status_values": ["ACTIVE", "DEPRECATED", "RETIRED", "DORMANT"],
    "created_at": None,
}


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _root() -> Path:
    if os.environ.get("VIA_ROOT"):
        return Path(os.environ["VIA_ROOT"])
    p = ME
    while p.parent != p:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
        p = p.parent
    return ME.parents[2]


def _paths() -> dict:
    r = _root()
    return {"root": r, "registry": r / "supportive modules" / "registry", "vdf": r / "functional modules" / "VDF", "vrn": r / "functional modules" / "VRN",
            "cards": r / "docs" / "handoff" / "ai", "report": r / "VIA_Reports" / "review" / "vcgc_books"}


def _vnum(name: str) -> int:
    m = re.search(r"_v(\d{2,4})[A-Za-z0-9]*(?:\.[A-Za-z0-9]+)?$", name)
    return int(m.group(1)) if m else -1


def _ver(name: str) -> str:
    m = re.search(r"_(v\d{2,4}[A-Za-z0-9]*)(?:\.[A-Za-z0-9]+)?$", name)
    return m.group(1) if m else "v0000"


def _family(name: str) -> str:
    stem = re.sub(r"_sha[0-9a-f]{8,}$", "", Path(name).stem)
    return re.sub(r"_v\d{2,4}[A-Za-z0-9]*$", "", stem)


def _rel(p: Path, P: dict) -> str:
    try:
        return p.relative_to(P["root"]).as_posix()
    except ValueError:
        return p.as_posix()


def _sub_of(p: Path, P: dict) -> str:
    s = str(p)
    if s.startswith(str(P["vrn"])):
        return "VRN"
    if s.startswith(str(P["vdf"])):
        return "VDF"
    return "VCGC"


def _skip(p: Path, P: dict) -> bool:
    try:
        parts = set(p.relative_to(P["root"]).parts[:-1])
    except ValueError:
        parts = set(p.parts)
    return bool(parts & EXCL)


def _tails(dirs, P: dict, exts, recursive) -> list:
    best: dict = {}
    for d in dirs:
        if not d.is_dir():
            continue
        for p in (d.rglob("*") if recursive else d.glob("*")):
            if not p.is_file() or p.suffix.lower() not in exts or _skip(p, P):
                continue
            k = (p.parent, _family(p.name), p.suffix.lower())
            v = _vnum(p.name)
            if k not in best or v > best[k][0]:
                best[k] = (v, p)
    return sorted((v[1] for v in best.values()), key=lambda q: str(q))


def _governed_books(P: dict) -> list:
    out = []
    for p in _tails([P["registry"]], P, {".json", ".jsonl", ".csv"}, False):
        if LOCKED_RE.match(p.name):
            out.append(p)
    for d in (P["vdf"], P["vrn"]):
        for sub in ("registry", "SSOT", "knowledge", "dict"):
            out += _tails([d / sub], P, {".json", ".jsonl", ".csv"}, True)
    return out


def _decode(raw: bytes) -> tuple:
    enc = "utf-8"
    bom = raw.startswith(b"\xef\xbb\xbf")
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        enc = "utf-16"
    try:
        txt = raw.decode("utf-8-sig" if enc == "utf-8" else "utf-16")
    except UnicodeDecodeError:
        try:
            txt = raw.decode("cp950")
            enc = "cp950"
        except UnicodeDecodeError:
            return None, enc, bom, False
    return txt, enc, bom, ("\r\n" in txt[:20000])


def _is_scalar(v) -> bool:
    return v is None or isinstance(v, (str, int, float, bool))


def _uniform(dcts) -> bool:
    """dict-of-dicts 當表的條件:內層鍵集合夠一致(聯集 ≤ 3 × 中位鍵數);否則是映射(鍵 → 值),不當表。"""
    sizes = sorted(len(d) for d in dcts)
    if not sizes:
        return False
    med = sizes[len(sizes) // 2] or 1
    union = set()
    for d in dcts:
        union |= set(d.keys())
    return len(union) <= 3 * med


def _shape(obj):
    """→ (shape, tables{name: rows})"""
    if isinstance(obj, list):
        if obj and all(isinstance(x, dict) for x in obj):
            return "TABLE", {"rows": obj}
        return "LIST", {}
    if isinstance(obj, dict):
        vals = list(obj.values())
        if vals and all(isinstance(v, dict) for v in vals) and len(obj) >= 2:
            return ("DICT_TABLE", {"rows": [dict({"key": k}, **v) for k, v in obj.items()]}) if _uniform(vals) else ("MAP", {})
        tables = {k: v for k, v in obj.items() if isinstance(v, list) and v and all(isinstance(x, dict) for x in v) and _uniform(v)}
        dtables = {k: [dict({"key": kk}, **vv) for kk, vv in v.items()] for k, v in obj.items() if isinstance(v, dict) and v and all(isinstance(x, dict) for x in v.values()) and len(v) >= 2 and _uniform(list(v.values()))}
        tables.update({k: v for k, v in dtables.items() if k not in tables})
        if tables:
            return "NESTED", tables
        if all(_is_scalar(v) for v in vals):
            return "CONFIG", {}
        return "NESTED", {}
    return "SCALAR", {}


def _col_profile(rows: list) -> dict:
    cols: dict = {}
    n = len(rows)
    for r in rows:
        for k, v in r.items():
            c = cols.setdefault(k, {"types": Counter(), "nulls": 0, "numstr": 0, "datestr": 0, "nested": 0, "distinct": set()})
            if v is None or v == "":
                c["nulls"] += 1
                continue
            t = type(v).__name__
            if isinstance(v, bool):
                t = "bool"
            elif isinstance(v, (dict, list)):
                t = "json"
                c["nested"] += 1
            elif isinstance(v, str):
                if NUM_RE.match(v.strip()):
                    c["numstr"] += 1
                elif ISO_RE.match(v):
                    c["datestr"] += 1
            c["types"][t] += 1
            if len(c["distinct"]) < n + 1 and _is_scalar(v):
                c["distinct"].add(v)
    out = {}
    for k, c in cols.items():
        kinds = set(c["types"])
        if "int" in kinds and "float" in kinds:
            kinds = (kinds - {"int"})
        mixed = len(kinds) > 1
        major = c["types"].most_common(1)[0][0] if c["types"] else "null"
        dtype = {"str": ("date" if c["datestr"] and c["datestr"] == c["types"].get("str", 0) else "str"), "int": "int", "float": "float", "bool": "bool", "json": "json"}.get(major, major)
        out[k] = {"dtype": dtype, "mixed": mixed, "types": dict(c["types"]), "nulls": c["nulls"], "numeric_as_str": c["numstr"], "nested_cells": c["nested"],
                  "unique": (len(c["distinct"]) == n - c["nulls"] and c["nulls"] == 0 and n > 0), "snake": bool(re.match(r"^[a-z0-9_]+$", str(k)))}
    return out


def _header_book(P: dict) -> dict:
    hits = sorted(P["registry"].glob("VIA_Output_Header_SSOT_v*.json"), key=lambda q: _vnum(q.name)) if P["registry"].is_dir() else []
    if not hits:
        return {"file": None, "tables": {}, "sources": set()}
    try:
        d = json.loads(hits[-1].read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {"file": hits[-1].name, "tables": {}, "sources": set()}
    tables = d.get("tables", {}) if isinstance(d, dict) else {}
    srcs = set()
    for t in (tables.values() if isinstance(tables, dict) else tables):
        if isinstance(t, dict):
            for k in ("source", "path", "file"):
                v = t.get(k)
                if isinstance(v, str):
                    srcs.add(Path(v).name)
                elif isinstance(v, dict) and isinstance(v.get("path"), str):
                    srcs.add(Path(v["path"]).name)
    return {"file": hits[-1].name, "tables": tables, "sources": srcs}


def audit(P: dict | None = None) -> dict:
    P = P or _paths()
    hb = _header_book(P)
    out = {"verb": "audit", "engine": NAME, "ts": _now(), "root": str(P["root"]), "pandas": HAS_PD, "header_book": hb["file"], "header_tables": len(hb["tables"]), "rows": [], "_notes": []}
    for p in _governed_books(P):
        sub = _sub_of(p, P)
        rec = {"sub": sub, "file": _rel(p, P), "family": _family(p.name), "version": _ver(p.name), "ext": p.suffix.lower(), "bytes": p.stat().st_size,
               "shape": None, "tables": {}, "enc": None, "bom": False, "crlf": False, "in_header_book": (p.name in hb["sources"] or _family(p.name) in {_family(s) for s in hb["sources"]}), "lamp": "GRAY", "why": []}
        if p.stat().st_size > MAX_BYTES:
            rec.update(lamp="GRAY")
            rec["why"].append("超過 %dMB 不剖" % (MAX_BYTES // 1_000_000))
            out["rows"].append(rec)
            continue
        txt, enc, bom, crlf = _decode(p.read_bytes())
        rec.update(enc=enc, bom=bom, crlf=crlf)
        if txt is None:
            rec.update(lamp="RED")
            rec["why"].append("讀不了(編碼)")
            out["rows"].append(rec)
            continue
        if enc == "utf-16":
            rec["why"].append("UTF-16(DF08 要 UTF-8)")
        if bom:
            rec["why"].append("BOM")
        if crlf:
            rec["why"].append("CRLF")
        tables = {}
        try:
            if rec["ext"] == ".jsonl":
                rows = [json.loads(ln) for ln in txt.splitlines() if ln.strip()]
                rec["shape"] = "JSONL"
                tables = {"rows": rows} if rows and all(isinstance(r, dict) for r in rows) else {}
            elif rec["ext"] == ".csv":
                rows = list(csv.DictReader(io.StringIO(txt)))
                rec["shape"] = "CSV"
                tables = {"rows": rows} if rows else {}
            else:
                obj = json.loads(txt)
                rec["shape"], tables = _shape(obj)
        except (ValueError, csv.Error) as exc:
            rec.update(lamp="RED")
            rec["why"].append("剖析失敗 %s" % type(exc).__name__)
            out["rows"].append(rec)
            continue
        yellow = False
        for tname, rows in tables.items():
            prof = _col_profile(rows)
            keys = [k for k, c in prof.items() if c["unique"] and c["dtype"] in ("str", "int")]
            issues = []
            if any(c["mixed"] for c in prof.values()):
                issues.append("混型欄 %d" % sum(1 for c in prof.values() if c["mixed"]))
            if any(c["numeric_as_str"] for c in prof.values()):
                issues.append("數字存字串欄 %d" % sum(1 for c in prof.values() if c["numeric_as_str"]))
            if any(c["nested_cells"] for c in prof.values()):
                issues.append("格內巢狀欄 %d" % sum(1 for c in prof.values() if c["nested_cells"]))
            if not keys:
                issues.append("無主鍵候選")
            if any(not c["snake"] for c in prof.values()):
                issues.append("非 snake_case 欄 %d" % sum(1 for c in prof.values() if not c["snake"]))
            rec["tables"][tname] = {"rows": len(rows), "cols": len(prof), "key_candidates": keys[:3], "issues": issues,
                                    "columns": {k: {"dtype": c["dtype"], "mixed": c["mixed"], "nulls": c["nulls"]} for k, c in list(prof.items())[:60]}}
            if issues:
                yellow = True
        if any(w.startswith("UTF-16") for w in rec["why"]):
            rec["lamp"] = "RED"
        elif rec["shape"] in ("CONFIG", "SCALAR", "LIST", "MAP") or (rec["shape"] == "NESTED" and not tables):
            rec["lamp"] = "GRAY"
            rec["why"].append("非表形狀 %s(純設定/巢狀,不當 DataFrame)" % rec["shape"])
        elif yellow or not rec["in_header_book"]:
            rec["lamp"] = "YELLOW"
            if not rec["in_header_book"]:
                rec["why"].append("表頭定案冊無此表")
            rec["why"] += ["%s:%s" % (t, ";".join(v["issues"])) for t, v in rec["tables"].items() if v["issues"]]
        else:
            rec["lamp"] = "GREEN"
        out["rows"].append(rec)
    per = {s: Counter() for s in SUBS}
    for r in out["rows"]:
        per[r["sub"]][r["lamp"]] += 1
        per[r["sub"]]["books"] += 1
    out["per"] = {s: dict(per[s]) for s in SUBS}
    order = {"RED": 3, "YELLOW": 2, "GREEN": 1, "GRAY": 0}
    out["lamp"] = max((r["lamp"] for r in out["rows"]), key=lambda x: order[x]) if out["rows"] else "GRAY"
    if not HAS_PD:
        out["_notes"].append("本直譯器無 pandas,型別推斷用純 python(結論相同,鏡像不出 parquet)")
    return out


def contract(P: dict | None = None, apply: bool = True) -> dict:
    P = P or _paths()
    fp = P["registry"] / "VIA_DataFrameContract_SSOT_v0100.json"
    if fp.exists():
        return {"verb": "contract", "status": "SKIP", "file": str(fp), "lamp": "GREEN"}
    d = dict(CONTRACT, created_at=_now())
    if apply:
        P["registry"].mkdir(parents=True, exist_ok=True)
        fp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"verb": "contract", "status": "WRITTEN" if apply else "PLAN", "file": str(fp), "laws": len(d["laws"]), "lamp": "GREEN"}


def propose(res: dict, P: dict | None = None, apply: bool = True) -> dict:
    P = P or _paths()
    hits = sorted(P["registry"].glob("VIA_Output_Header_SSOT_Candidates_v*.json"), key=lambda q: _vnum(q.name)) if P["registry"].is_dir() else []
    nv = "v%04d" % (_vnum(hits[-1].name) + 1 if hits else 100)
    fp = P["registry"] / ("VIA_Output_Header_SSOT_Candidates_%s.json" % nv)
    cands = {}
    for r in res["rows"]:
        if r["lamp"] in ("RED", "GRAY") or r["in_header_book"]:
            continue
        for t, v in r["tables"].items():
            tid = re.sub(r"[^a-z0-9_]+", "_", (r["family"] + ("_" + t if t != "rows" else "")).lower()).strip("_")
            cands[tid] = {"subsystem": r["sub"], "source": r["file"], "table": t, "rows_seen": v["rows"], "keys": v["key_candidates"],
                          "columns": [{"name": k, "dtype": c["dtype"], "required": c["nulls"] == 0, "pk": (k in v["key_candidates"][:1])} for k, c in v["columns"].items()],
                          "issues": v["issues"], "locked_by": "", "ruling": ""}
    d = {"schema": "VIA.OutputHeaderCandidates.v1", "version": nv, "engine": NAME, "ts": _now(), "prior": (hits[-1].name if hits else None),
         "rule": "待審區:locked_by 與 ruling 留白;操作員+AI 裁後由 VCGC 併入 VIA_Output_Header_SSOT 新版,CGC_MDL249 才鎖;子系統冊由子系統自己依 DataFrameContract 出新版(DF11)",
         "n": len(cands), "tables": cands}
    if apply and cands:
        fp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"verb": "propose", "status": ("WRITTEN" if (apply and cands) else ("EMPTY" if not cands else "PLAN")), "file": (str(fp) if cands else None), "n": len(cands), "lamp": "GREEN" if cands else "GRAY"}


def _flat(v):
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return v


def mirror(res: dict, P: dict | None = None, apply: bool = True) -> dict:
    P = P or _paths()
    outdir = P["registry"] / "_df"
    done, skipped = [], 0
    for r in res["rows"]:
        if r["sub"] != "VCGC" or r["lamp"] in ("RED", "GRAY") or not r["tables"]:
            skipped += 1
            continue
        src = P["root"] / r["file"]
        try:
            txt, _, _, _ = _decode(src.read_bytes())
            if r["ext"] == ".jsonl":
                tables = {"rows": [json.loads(ln) for ln in txt.splitlines() if ln.strip()]}
            elif r["ext"] == ".csv":
                tables = {"rows": list(csv.DictReader(io.StringIO(txt)))}
            else:
                _, tables = _shape(json.loads(txt))
        except (OSError, ValueError, csv.Error):
            continue
        for t, rows in tables.items():
            dest = outdir / ("%s_%s%s.rows.jsonl" % (r["family"], r["version"], "" if t == "rows" else "." + t))
            if apply:
                outdir.mkdir(parents=True, exist_ok=True)
                with open(dest, "w", encoding="utf-8", newline="\n") as fh:
                    for i, row in enumerate(rows):
                        fh.write(json.dumps(dict({"_row": i, "_sub": r["sub"], "_book": r["family"], "_version": r["version"]}, **{k: _flat(v) for k, v in row.items()}), ensure_ascii=False) + "\n")
            done.append({"book": r["family"], "table": t, "rows": len(rows), "mirror": _rel(dest, P)})
    return {"verb": "mirror", "status": "WRITTEN" if apply else "PLAN", "n": len(done), "skipped": skipped, "done": done, "lamp": "GREEN" if done else "GRAY"}


def paste_pack(res: dict, extra: list) -> list:
    per = res["per"]
    L = ["[計] vcgc books · %s · 總燈 %s · " % (res["ts"], res["lamp"]) + " · ".join("%s 冊 %d 紅 %d 黃 %d 綠 %d 灰 %d" % (s, per[s].get("books", 0), per[s].get("RED", 0), per[s].get("YELLOW", 0), per[s].get("GREEN", 0), per[s].get("GRAY", 0)) for s in SUBS)
         + " · 表頭定案冊 %s(%d 表)· pandas %s" % (res["header_book"] or "不在", res["header_tables"], res["pandas"])]
    for r in [x for x in res["rows"] if x["lamp"] == "RED"][:15]:
        L.append("  [RED] %s %s · %s" % (r["sub"], r["file"], ";".join(r["why"])))
    shapes = Counter((r["sub"], r["shape"] or "UNREADABLE") for r in res["rows"])
    L.append("[計] 形狀 · " + " · ".join("%s:%s=%d" % (s, sh, n) for (s, sh), n in sorted(shapes.items())))
    yel = [x for x in res["rows"] if x["lamp"] == "YELLOW"]
    for r in yel[:40]:
        L.append("  [YEL] %s %s · %s" % (r["sub"], Path(r["file"]).name, ";".join(r["why"])[:140]))
    if len(yel) > 40:
        L.append("  [YEL] … 另 %d 冊在卡" % (len(yel) - 40))
    L += extra
    for n in res.get("_notes", []):
        L.append("  [注] %s" % n)
    L.append("NEXT: 紅 → 出新版冊轉 UTF-8/修 JSON;黃 → 看 Candidates 待審區,操作員+AI 裁表頭後併入 Output_Header_SSOT 讓 MDL249 鎖;VDF/VRN 冊由各自 manager 依 DataFrameContract 出新版")
    return L[:300]


def write_card(res: dict, pack: list, P: dict | None = None) -> dict:
    P = P or _paths()
    day = datetime.datetime.now().strftime("%Y%m%d")
    P["cards"].mkdir(parents=True, exist_ok=True)
    P["report"].mkdir(parents=True, exist_ok=True)
    md = P["cards"] / ("VCGC_BookStandardCard_%s.md" % day)
    L = ["# VCGC 規則冊 / SSOT 優化 + DataFrame 標準化 卡(%s)" % day, "", "> 唯讀 VDF/VRN。紅 = 要修;黃 = 待裁;灰 = 非表。契約 VIA_DataFrameContract_SSOT_v0100 DF01–DF11。", "", "## 貼回包", "```"] + pack + ["```", "", "## 每冊", "| 子系統 | 冊 | 形狀 | 表 | 編碼 | 表頭定案 | 燈 | 原因 |", "|---|---|---|---|---|---|---|---|"]
    for r in res["rows"]:
        L.append("| %s | %s | %s | %s | %s%s%s | %s | %s | %s |" % (r["sub"], Path(r["file"]).name, r["shape"], ", ".join("%s(%d×%d)" % (t, v["rows"], v["cols"]) for t, v in r["tables"].items()) or "—",
                                                               r["enc"], " BOM" if r["bom"] else "", " CRLF" if r["crlf"] else "", "有" if r["in_header_book"] else "無", r["lamp"], ";".join(r["why"]).replace("|", "¦")))
    md.write_text("\n".join(L) + "\n", encoding="utf-8")
    (P["report"] / "BOOKS_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"md": str(md)}


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VCGC] 拒絕。只能經 via-vcgc。")
        return 2
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a[:2]:
        return selftest()
    apply = "--apply" in a
    verb = a[0] if a else ""
    if verb not in ("audit", "contract", "propose", "mirror"):
        print("[拒跑] audit | contract --apply | propose --apply | mirror --apply | --selftest")
        return 2
    extra = []
    if verb == "contract":
        c = contract(apply=apply)
        print("[計] contract %s · %s · %s" % (c["status"], c["file"], c["lamp"]))
        return 0
    res = audit()
    if verb == "propose":
        pr = propose(res, apply=apply)
        extra.append("[計] propose 表頭候選 %d 表 · %s · %s" % (pr["n"], pr["status"], pr.get("file") or "—"))
    elif verb == "mirror":
        mr = mirror(res, apply=apply)
        extra.append("[計] mirror VCGC 冊鏡像 %d 表 · 略過 %d · %s" % (mr["n"], mr["skipped"], mr["status"]))
    pack = paste_pack(res, extra)
    card = write_card(res, pack)
    for ln in pack:
        print(ln)
    print("  [卡] %s" % card["md"])
    return 1 if res["lamp"] == "RED" else 0


def _w(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, bytes):
        p.write_bytes(obj)
    else:
        p.write_text(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="cgcbook-"))
    os.environ["VIA_ROOT"] = str(td)
    P = _paths()
    reg, vrn, vdf = P["registry"], P["vrn"], P["vdf"]
    chk("① 沙盒:VIA_ROOT 指 temp", all(str(v).startswith(str(td)) for v in P.values()))
    _w(reg / "VIA_Policy_Laws_SSOT_v0106.json", {"schema": "x", "laws": [{"id": "L1", "zh": "a", "rank": 1}, {"id": "L2", "zh": "b", "rank": "2"}], "lessons": [{"id": "LL1", "zh": "c"}]})   # NESTED 兩表;rank 混型
    _w(reg / "VIA_SSOT_Numbers_VRN_v0100.json", {"entries": [{"key": "k1", "ssot_no": "S1", "sha256": "a"}, {"key": "k2", "ssot_no": "S2", "sha256": "b"}]})                                # NESTED 一表乾淨
    _w(reg / "VIA_UI_FormatLock_v0101.json", {"tokens": {"lamp_RED": "#dc2626", "lamp_GREEN": "#16a34a"}, "font": "Arial"})                                                              # NESTED 無表 → 灰
    _w(reg / "VIA_LampLock_v0100.json", {"a": 1, "b": "x"})                                                                                                                             # CONFIG → 灰
    _w(reg / "VIA_Central_Synonym_Regex_v0107.json", {"ticker": {"pattern": r"\d{4}", "zh": "代號"}, "price": {"pattern": r"\d+", "zh": "價"}})                                           # DICT_TABLE
    _w(reg / "VIA_Numbering_Ledger_v0100.jsonl", '{"code":"A","n":"12"}\n{"code":"B","n":13}\n')                                                                                          # JSONL 數字存字串+混型
    _w(reg / "VIA_EntryLock_v0100.json", b"\xff\xfe" + '{"x":1}'.encode("utf-16-le"))                                                                                                     # UTF-16 → 紅
    _w(reg / "VIA_Canon_Registry_v0100.json", "{bad json")                                                                                                                                # 壞 JSON → 紅
    _w(reg / "VIA_Output_Header_SSOT_v0101.json", {"tables": {"ssot_numbers_vrn": {"source": "supportive modules/registry/VIA_SSOT_Numbers_VRN_v0100.json", "columns": []}}})            # 定案冊含 Numbers_VRN
    _w(reg / "NotGoverned_v0100.json", {"rows": [{"a": 1}]})                                                                                                                              # 不在鎖管控名單
    _w(vrn / "SSOT" / "VRN_DocClass_SSOT_v0101.json", {"rows": [{"Report File": "a.pdf", "cls": "個股"}, {"Report File": "b.pdf", "cls": "產業"}]})                                        # VRN:非 snake 欄
    _w(vdf / "registry" / "VDF_Universe_v0100.csv", "ticker,name\n2330,台積電\n2317,鴻海\n")                                                                                             # VDF CSV
    res = audit(P)
    R = {Path(r["file"]).name: r for r in res["rows"]}
    chk("② 名單:鎖管控 8 冊 + 定案冊本身 1 + VRN 1 + VDF 1;NotGoverned 不計", len(res["rows"]) == 11 and "NotGoverned_v0100.json" not in R and res["per"]["VRN"]["books"] == 1 and res["per"]["VDF"]["books"] == 1)
    chk("③ 形狀:Policy=NESTED 2 表 · Synonym=DICT_TABLE · Ledger=JSONL · Universe=CSV · UI_FormatLock/LampLock=灰",
        R["VIA_Policy_Laws_SSOT_v0106.json"]["shape"] == "NESTED" and len(R["VIA_Policy_Laws_SSOT_v0106.json"]["tables"]) == 2 and R["VIA_Central_Synonym_Regex_v0107.json"]["shape"] == "DICT_TABLE"
        and R["VIA_Numbering_Ledger_v0100.jsonl"]["shape"] == "JSONL" and R["VDF_Universe_v0100.csv"]["shape"] == "CSV" and R["VIA_UI_FormatLock_v0101.json"]["lamp"] == "GRAY" and R["VIA_LampLock_v0100.json"]["lamp"] == "GRAY")
    chk("④ 型別律:Policy rank 混型黃 · Ledger n 數字存字串+混型黃 · DocClass 非 snake 欄黃", any("混型" in w for w in R["VIA_Policy_Laws_SSOT_v0106.json"]["why"]) and any("數字存字串" in w for w in R["VIA_Numbering_Ledger_v0100.jsonl"]["why"]) and any("snake" in w for w in R["VRN_DocClass_SSOT_v0101.json"]["why"]))
    chk("⑤ 紅:UTF-16 紅 · 壞 JSON 紅", R["VIA_EntryLock_v0100.json"]["lamp"] == "RED" and R["VIA_Canon_Registry_v0100.json"]["lamp"] == "RED")
    chk("⑥ 定案冊比對:Numbers_VRN 在冊且乾淨 → 綠;Synonym 乾淨但無定案 → 黃", R["VIA_SSOT_Numbers_VRN_v0100.json"]["lamp"] == "GREEN" and R["VIA_SSOT_Numbers_VRN_v0100.json"]["in_header_book"] and R["VIA_Central_Synonym_Regex_v0107.json"]["lamp"] == "YELLOW")
    chk("⑦ 主鍵候選:Numbers_VRN key · Synonym key · Universe ticker", R["VIA_SSOT_Numbers_VRN_v0100.json"]["tables"]["entries"]["key_candidates"][:1] == ["key"] and "key" in R["VIA_Central_Synonym_Regex_v0107.json"]["tables"]["rows"]["key_candidates"] and "ticker" in R["VDF_Universe_v0100.csv"]["tables"]["rows"]["key_candidates"])
    c1 = contract(P, apply=True)
    c2 = contract(P, apply=True)
    cf = json.loads((reg / "VIA_DataFrameContract_SSOT_v0100.json").read_text(encoding="utf-8"))
    chk("⑧ contract:寫入 11 律 · 再跑 SKIP", c1["status"] == "WRITTEN" and c2["status"] == "SKIP" and len(cf["laws"]) == 11 and cf["laws"][0]["id"] == "DF01")
    pr = propose(res, P, apply=True)
    cd = json.loads(Path(pr["file"]).read_text(encoding="utf-8"))
    chk("⑨ propose:只收黃冊(紅/灰/已定案不收)· locked_by 留白 · Policy 兩表各一候選 · VRN/VDF 冊也列(給子系統看)",
        pr["status"] == "WRITTEN" and all(t["locked_by"] == "" for t in cd["tables"].values()) and "via_policy_laws_ssot_laws" in cd["tables"] and "via_policy_laws_ssot_lessons" in cd["tables"]
        and "via_ssot_numbers_vrn" not in cd["tables"] and any(t["subsystem"] == "VRN" for t in cd["tables"].values()))
    before = {str(x): x.stat().st_size for x in (vrn.rglob("*")) if x.is_file()} | {str(x): x.stat().st_size for x in (vdf.rglob("*")) if x.is_file()}
    mr = mirror(res, P, apply=True)
    after = {str(x): x.stat().st_size for x in (vrn.rglob("*")) if x.is_file()} | {str(x): x.stat().st_size for x in (vdf.rglob("*")) if x.is_file()}
    mfiles = sorted(q.name for q in (reg / "_df").glob("*.rows.jsonl"))
    lines = (reg / "_df" / "VIA_Policy_Laws_SSOT_v0106.laws.rows.jsonl").read_text(encoding="utf-8").splitlines()
    row0 = json.loads(lines[0])
    chk("⑩ mirror:只鏡 VCGC 可表冊 · Policy 出 laws/lessons 兩鏡像 · 列帶 _row/_sub/_book/_version · 原冊與 VDF/VRN 一字不動",
        mr["n"] >= 4 and "VIA_Policy_Laws_SSOT_v0106.laws.rows.jsonl" in mfiles and "VIA_Policy_Laws_SSOT_v0106.lessons.rows.jsonl" in mfiles and not any(m.startswith(("VRN_", "VDF_")) for m in mfiles)
        and row0["_sub"] == "VCGC" and row0["_row"] == 0 and before == after
        and json.loads((reg / "VIA_Policy_Laws_SSOT_v0106.json").read_text(encoding="utf-8"))["laws"][1]["rank"] == "2")
    pack = paste_pack(res, [])
    card = write_card(res, pack, P)
    chk("⑪ 貼回包 ≤300 行 · 結尾 NEXT: · 卡在", len(pack) <= 300 and pack[-1].startswith("NEXT:") and Path(card["md"]).exists())
    body = ME.read_text(encoding="utf-8")
    chk("⑫ 帶加速器橋 · VIA_FROM_VCGC 閘 · 無 pandas 也能跑(純 python 後援)", "[VIA:ACCEL-BRIDGE:v0100]" in body and "VIA_FROM_VCGC" in body and "HAS_PD" in body)
    os.environ.pop("VIA_ROOT", None)
    shutil.rmtree(td, ignore_errors=True)
    print("[計] %s 自測 %d/%d · %s" % (NAME, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
