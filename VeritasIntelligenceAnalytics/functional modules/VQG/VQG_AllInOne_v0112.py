#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0112]
r"""VeritaQuantGuard(VQG)v0112 — v0111 薄尾(v0111 一字不改 · SHA-256 釘在 PRIOR_SHA256)。

操作員 2026-11-14:「時間 代碼 · 台股全部 主動式台股ETF · OPEN LOW HIGH CLOSE ADJ CLOSE ADJ LOW ADJ HIGH ADJ OPEN
              VOLUME / TURNOVER 原本名稱 · 扣除當沖交易另外兩個 · 請VQG協助編號分類註冊完成」
              「善用VQG來掃描全部但要分類說明 先從VRN VDF開始後向VCGC一路註冊檢查」。

本版只加一個動詞 fields(VQG 自己的行情輸入欄 · 14 欄 · 登在同一本指標登記冊 kind = input_field):
  fields                    列表(編號 · 分類 · 代碼 · 名稱 · 公式)
  fields --full             每列全欄
  fields --id <代碼>        單列(stable_id · 編號 · 原本名稱)
  fields --check            冊 ⇄ 程式對帳:14 欄一對一 · stable_id / 公式一字相同 · 不重號 · 必填欄不空 → GREEN rc 0 / RED rc 1
  fields --scan [--json]    跨系統註冊檢查,順序 VRN → VDF → VCGC:每一欄在三邊各登在哪裡(只讀對方的冊,不改)
  fields --export [夾]      掃描結果 CSV(utf-8-sig)+ MD;預設 <VIA>/VIA_Reports/vqg/price_fields
  indicators --check        前版對帳之後再加跑 fields --check(兩邊都綠才綠)
  derive(row)               還原四價與扣除當沖兩欄的算法(純函式;缺值回空、不補值)
邊界:同 v0111(零網路 · 不 import VAP / VDF · 不寫 VDF 夾);他系統的冊只當文字讀;只在 --export 寫自己的報表夾;前版被改過 → rc 2。不用 TA-Lib。
代號範圍與規則只引用 VDF 輸入冊(IN-01 台股全部 · IN-02 主動式台股 ETF),VQG 不另寫一份。
自測:python VQG_AllInOne_v0112.py selftest(本版 12 項 + v0111 自測於乾淨子行程 · 零網路 · 只在 tempfile 寫)。
"""
from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION_TAIL = "v0112"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VQG_AllInOne_v0111.py"
PRIOR_SHA256 = "c3ddf1f43c4d5d08e549a3072ccbfa2b796521a967ada7b84bc179149648cc65"   # v0111
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.is_file():
    raise SystemExit("[RED] 前版 %s 不在 %s(v0112 是 v0111 的薄尾 · 兩支要放同一夾)" % (PRIOR_NAME, HERE))
PRIOR_SHA_OK = hashlib.sha256(PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == PRIOR_SHA256
_spec = importlib.util.spec_from_file_location("vqg_v0111_for_v0112", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v
V11 = PRIOR
V7 = PRIOR.V7                         # v0107(via_root)


def __getattr__(name):
    """前版公開面照轉(尾版不少名字)。"""
    return getattr(PRIOR, name)


FIELD_KIND = "input_field"
FIELD_COLUMNS = (("編號", "no"), ("分類", "category"), ("欄位名稱", "name_zh"), ("原本名稱", "original_name"), ("公式", "formula"),
                 ("型別", "dtype"), ("單位", "unit"), ("時間參數", "time_params"), ("VDF 來源欄", "vdf_columns"), ("範圍", "universe"),
                 ("參數", "params"), ("pros", "pros"), ("cons", "cons"), ("替代", "alternatives"))

# 行情輸入欄(順序照操作員列的;公式字串要與冊一字相同)
INPUT_FIELDS = {
    "date": {"stable_id": "VQG.IN.DATE", "formula": "date = trading day, YYYY-MM-DD", "vdf": ("date",)},
    "ticker": {"stable_id": "VQG.IN.TICKER", "formula": "ticker = code in VDF input book IN-01 (all TW stocks) or IN-02 (active TW ETF)", "vdf": ("ticker",)},
    "open": {"stable_id": "VQG.IN.OPEN", "formula": "open = VDF daily row open (as published, unadjusted)", "vdf": ("open",)},
    "low": {"stable_id": "VQG.IN.LOW", "formula": "low = VDF daily row low (as published, unadjusted)", "vdf": ("low",)},
    "high": {"stable_id": "VQG.IN.HIGH", "formula": "high = VDF daily row high (as published, unadjusted)", "vdf": ("high",)},
    "close": {"stable_id": "VQG.IN.CLOSE", "formula": "close = VDF daily row close (as published, unadjusted)", "vdf": ("close",)},
    "adj_close": {"stable_id": "VQG.IN.ADJ_CLOSE", "formula": "adj_close = VDF yf_adj_close (as sourced, not recomputed)", "vdf": ("yf_adj_close",)},
    "adj_low": {"stable_id": "VQG.IN.ADJ_LOW", "formula": "adj_low = low * yf_adj_close / yf_close", "vdf": ("low", "yf_adj_close", "yf_close")},
    "adj_high": {"stable_id": "VQG.IN.ADJ_HIGH", "formula": "adj_high = high * yf_adj_close / yf_close", "vdf": ("high", "yf_adj_close", "yf_close")},
    "adj_open": {"stable_id": "VQG.IN.ADJ_OPEN", "formula": "adj_open = open * yf_adj_close / yf_close", "vdf": ("open", "yf_adj_close", "yf_close")},
    "volume": {"stable_id": "VQG.IN.VOLUME", "formula": "volume = VDF daily row volume (shares, as published)", "vdf": ("volume",)},
    "turnover": {"stable_id": "VQG.IN.TURNOVER", "formula": "turnover = VDF daily row turnover (TWD, as published)", "vdf": ("turnover",)},
    "volume_ex_daytrade": {"stable_id": "VQG.IN.VOLUME_EX_DAYTRADE", "formula": "volume_ex_daytrade = volume - day_trade_volume", "vdf": ("volume", "day_trade_volume")},
    "turnover_ex_daytrade": {"stable_id": "VQG.IN.TURNOVER_EX_DAYTRADE", "formula": "turnover_ex_daytrade = turnover - day_trade_value", "vdf": ("turnover", "day_trade_value")},
}
RAW_FIELDS = tuple(k for k, v in INPUT_FIELDS.items() if len(v["vdf"]) == 1)
DERIVED_FIELDS = tuple(k for k in INPUT_FIELDS if k not in RAW_FIELDS)
UNIVERSE_IDS = ("IN-01", "IN-02")


# ── 算法(純函式 · 缺值回空 · 不補值)────────────────────────────────────────────────────────────
def _num(v):
    if isinstance(v, bool) or v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def derive(row: dict) -> dict:
    """一列 VDF 日列(欄名照 VDF)→ VQG 14 欄。原始欄原值帶出;還原四價用同一來源的還原比例;扣除當沖用相減。"""
    out = {"date": row.get("date"), "ticker": row.get("ticker")}
    flags = []
    for k in ("open", "low", "high", "close", "volume", "turnover"):
        out[k] = row.get(k)
    adj, ref = _num(row.get("yf_adj_close")), _num(row.get("yf_close"))
    out["adj_close"] = row.get("yf_adj_close")
    factor = (adj / ref) if adj is not None and ref is not None and ref > 0 else None
    if factor is None:
        flags.append("no_adj_factor")
    for k in ("low", "high", "open"):
        x = _num(row.get(k))
        out["adj_" + k] = (x * factor) if x is not None and factor is not None else None
    for name, a, b in (("volume_ex_daytrade", "volume", "day_trade_volume"), ("turnover_ex_daytrade", "turnover", "day_trade_value")):
        x, y = _num(row.get(a)), _num(row.get(b))
        if x is None or y is None:
            out[name] = None
            flags.append(name + ":missing_input")
        elif x - y < 0:
            out[name] = None
            flags.append(name + ":negative")
        else:
            out[name] = int(x - y) if name.startswith("volume") else x - y
    out["_flags"] = flags
    return {k: out[k] for k in list(INPUT_FIELDS) + ["_flags"]}


# ── 冊 ⇄ 程式 ────────────────────────────────────────────────────────────────────────────────
def field_rows(book: dict) -> list:
    return [e for e in (book.get("entries") or []) if e.get("kind") == FIELD_KIND]


def fields_check(book: dict) -> dict:
    rows = field_rows(book)
    bad = []
    by_key = {}
    for e in rows:
        k = e.get("code_key")
        if k in by_key:
            bad.append("同一欄登記兩次:%s" % k)
        by_key[k] = e
        for f in ("no", "stable_id", "category", "name_zh", "formula", "time_params", "dtype", "unit", "original_name"):
            if not str(e.get(f) or "").strip():
                bad.append("必填欄空:%s · %s" % (e.get("stable_id") or e.get("no"), f))
        if e.get("original_name") != k:
            bad.append("原本名稱與 code_key 不同:%s" % k)
    for k, spec in INPUT_FIELDS.items():
        e = by_key.get(k)
        if e is None:
            bad.append("程式有、冊沒登記:輸入欄 %s(%s)" % (k, spec["stable_id"]))
            continue
        if e.get("stable_id") != spec["stable_id"]:
            bad.append("stable_id 不同:%s 冊 %s ≠ 程式 %s" % (k, e.get("stable_id"), spec["stable_id"]))
        if e.get("formula") != spec["formula"]:
            bad.append("公式不同:%s(冊與程式要一字相同)" % spec["stable_id"])
        if tuple(e.get("vdf_columns") or ()) != tuple(spec["vdf"]):
            bad.append("VDF 來源欄不同:%s 冊 %s ≠ 程式 %s" % (k, e.get("vdf_columns"), list(spec["vdf"])))
    bad += ["冊上有、程式沒有:輸入欄 %s" % k for k in by_key if k not in INPUT_FIELDS]
    nos = [e.get("no") for e in (book.get("entries") or [])]
    ids = [e.get("stable_id") for e in (book.get("entries") or [])]
    bad += ["重號 編號:%s" % n for n in sorted({n for n in nos if nos.count(n) > 1})]
    bad += ["重號 stable_id:%s" % n for n in sorted({n for n in ids if ids.count(n) > 1})]
    return {"lamp": "RED" if bad else "GREEN", "register": Path(book.get("_path", "?")).name, "rows": len(rows),
            "code": len(INPUT_FIELDS), "problems": bad}


# ── 跨系統註冊檢查(VRN → VDF → VCGC;只讀對方的冊)────────────────────────────────────────────────
def _vnum_any(p: Path) -> int:
    m = re.search(r"_v(\d{4})\.[a-z]+$", p.name)
    return int(m.group(1)) if m else -1


def _tail(folder: Path, pattern: str) -> Path | None:
    hits = sorted(folder.glob(pattern), key=_vnum_any) if folder.is_dir() else []
    return hits[-1] if hits else None


def _read_json(p: Path | None):
    if p is None:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def via_home() -> Path | None:
    try:
        v = V7.via_root(None)
    except Exception:  # noqa: BLE001
        v = None
    if v:
        return Path(v)
    return HERE.parents[1] if len(HERE.parents) > 1 and (HERE.parents[1] / "functional modules").is_dir() else None


VRN_BOOKS = (("SSOT", "VRN_FieldSpec_SSOT_v*.json"), ("SSOT", "VRN_S05_FieldRegistry_v*.json"), ("knowledge", "VRN_FinData_Synonym_v*.json"))


def scan(book: dict, via: Path | None = None) -> dict:
    via = via or via_home()
    out = {"via": str(via) if via else None, "order": ["VRN", "VDF", "VCGC"], "sources": {}, "universe": [], "rows": [], "problems": []}
    if via is None:
        out["lamp"] = "NODATA"
        out["problems"].append("找不到 VIA 根(三邊的冊讀不到)")
        return out
    fm = via / "functional modules"
    # VRN:欄位冊裡有沒有同名鍵
    vrn_hits = {}
    for sub, pat in VRN_BOOKS:
        p = _tail(fm / "VRN" / sub, pat)
        out["sources"]["VRN:" + pat] = p.name if p else None
        if p is None:
            continue
        try:
            text = p.read_text(encoding="utf-8-sig", errors="replace")
        except OSError as error:
            out["sources"]["VRN:" + pat] = "%s(讀不到:%s)" % (p.name, type(error).__name__)
            continue
        for k in set(INPUT_FIELDS) | {c for v in INPUT_FIELDS.values() for c in v["vdf"]}:
            if re.search(r'"%s"' % re.escape(k), text):
                vrn_hits.setdefault(k, []).append(p.name)
    # VDF:日列欄冊 + 輸入冊
    sp = _tail(fm / "VDF", "VDF_TWEquity_DailyRow_Schema_v*.json")
    schema = _read_json(sp) or {}
    out["sources"]["VDF:日列欄冊"] = sp.name if sp else None
    vdf_cols = {c.get("name"): c for c in (schema.get("columns") or []) if isinstance(c, dict)}
    ip = _tail(fm / "VDF", "VDF_InputUniverse_SSOT_v*.json")
    ub = _read_json(ip) or {}
    out["sources"]["VDF:輸入冊"] = ip.name if ip else None
    for i in ub.get("inputs") or []:
        if i.get("id") in UNIVERSE_IDS:
            out["universe"].append({"id": i.get("id"), "group": i.get("group"), "zh": i.get("zh"), "code_regex": i.get("code_regex")})
    if len(out["universe"]) != len(UNIVERSE_IDS):
        out["problems"].append("VDF 輸入冊缺範圍:%s" % ", ".join(sorted(set(UNIVERSE_IDS) - {u["id"] for u in out["universe"]})))
    # VCGC:中央欄位編號冊
    np_ = _tail(via / "supportive modules" / "registry" / "VIA_NumberBooks", "VIA_NumberBook_FD_v*.jsonl")
    out["sources"]["VCGC:欄位編號冊"] = np_.name if np_ else None
    central = {}
    if np_ is not None:
        try:
            lines = np_.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            lines = []
        bad_lines = 0
        for ln in lines:
            try:
                r = json.loads(ln)
            except ValueError:
                bad_lines += 1
                r = None
            if isinstance(r, dict) and r.get("sub") == "VDF" and sp is not None and str(r.get("source", "")).endswith(sp.name):
                central[r.get("name")] = r.get("code")
        if bad_lines:
            out["sources"]["VCGC:欄位編號冊讀不動的行"] = bad_lines
    mine = {e.get("code_key"): e for e in field_rows(book)}
    for k, spec in INPUT_FIELDS.items():
        e = mine.get(k) or {}
        ups = list(spec["vdf"])
        miss_vdf = [c for c in ups if c not in vdf_cols]
        miss_no = [c for c in ups if c in vdf_cols and c not in central]
        derived = k in DERIVED_FIELDS
        if miss_vdf:
            lamp, state = "RED", "VDF 日列欄冊沒有:%s" % ", ".join(miss_vdf)
        elif miss_no:
            lamp, state = "YELLOW", "VDF 有欄、中央沒編號:%s" % ", ".join(miss_no)
        else:
            lamp, state = "GREEN", ("衍生欄 · 上游 %d 欄三邊齊" % len(ups)) if derived else "原始欄 · VDF 有欄 · 中央有號"
        out["rows"].append({
            "no": e.get("no", ""), "stable_id": spec["stable_id"], "name": k, "category": e.get("category", ""), "name_zh": e.get("name_zh", ""),
            "kind": "衍生" if derived else "原始", "formula": spec["formula"],
            "vrn": "; ".join("%s@%s" % (c, "+".join(vrn_hits[c])) for c in [k] + [u for u in ups if u != k] if c in vrn_hits) or "未登記(VRN 的欄位冊沒有這個欄名)",
            "vdf": "; ".join("%s(%s · %s)" % (c, vdf_cols[c].get("zh", ""), vdf_cols[c].get("dtype", "")) if c in vdf_cols else "%s(無)" % c for c in ups),
            "vcgc": "; ".join("%s=%s" % (c, central[c]) if c in central else "%s=未編號" % c for c in ups),
            "vqg": "已登記 %s" % e.get("no") if e else "未登記", "lamp": lamp if e else "RED", "state": state if e else "VQG 冊沒有這一列"})
    worst = [r["lamp"] for r in out["rows"]]
    out["lamp"] = "RED" if "RED" in worst or out["problems"] else "YELLOW" if "YELLOW" in worst else "GREEN"
    out["counts"] = {x: worst.count(x) for x in ("GREEN", "YELLOW", "RED")}
    return out


SCAN_COLUMNS = (("編號", "no"), ("分類", "category"), ("欄位名稱", "name_zh"), ("原本名稱", "name"), ("原始/衍生", "kind"), ("公式", "formula"),
                ("VRN", "vrn"), ("VDF", "vdf"), ("VCGC 中央號", "vcgc"), ("VQG", "vqg"), ("燈", "lamp"), ("說明", "state"), ("代碼", "stable_id"))


def export_scan(rep: dict, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = "VQG_PriceFields_" + VERSION_TAIL
    head = [c for c, _ in SCAN_COLUMNS]
    with open(out_dir / (stem + ".csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        for r in rep["rows"]:
            w.writerow([r.get(k, "") for _, k in SCAN_COLUMNS])
    md = ["# VQG 行情輸入欄 · 跨系統註冊檢查(%s · %s)" % (VERSION_TAIL, rep.get("lamp")), "",
          "範圍:" + " ; ".join("%s %s %s" % (u["id"], u.get("zh") or "", u.get("code_regex") or "") for u in rep.get("universe") or []), "",
          "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rep["rows"]:
        md.append("| " + " | ".join(str(r.get(k, "")).replace("|", "\\|") for _, k in SCAN_COLUMNS) + " |")
    (out_dir / (stem + ".md")).write_text("\n".join(md) + "\n", encoding="utf-8")
    return {"csv": str(out_dir / (stem + ".csv")), "md": str(out_dir / (stem + ".md")), "rows": len(rep["rows"])}


def _cellv(v) -> str:
    if isinstance(v, (list, tuple)):
        return " ; ".join(str(x) for x in v) if v else "—"
    return str(v) if v not in (None, "") else "—"


def fields(argv: list) -> int:
    try:
        book = V11.load_register()
    except (OSError, ValueError) as error:
        print("[RED] VQG %s fields · %s" % (VERSION_TAIL, error), flush=True)
        return 1
    if "--check" in argv:
        c = fields_check(book)
        print("[%s] VQG %s 行情輸入欄對帳 · %s · 冊 %d 列 · 程式 %d 欄 · 問題 %d" % (c["lamp"], VERSION_TAIL, c["register"], c["rows"], c["code"], len(c["problems"])), flush=True)
        for p in c["problems"]:
            print("  [RED] " + p, flush=True)
        return 0 if c["lamp"] == "GREEN" else 1
    if "--scan" in argv or "--export" in argv:
        rep = scan(book)
        if "--json" in argv:
            print(json.dumps(rep, ensure_ascii=False, indent=1), flush=True)
        else:
            print("[%s] VQG %s 行情輸入欄 · 跨系統註冊檢查(VRN → VDF → VCGC)· %d 欄 · %s" % (rep["lamp"], VERSION_TAIL, len(rep["rows"]), rep.get("counts", {})), flush=True)
            for u in rep.get("universe") or []:
                print("  範圍 %s %s · 代號規則照 VDF 輸入冊 %s" % (u["id"], u.get("zh") or "", u.get("code_regex") or ""), flush=True)
            for r in rep["rows"]:
                print("  [%-6s] %-8s %-6s %-22s VRN:%s ‖ VDF:%s ‖ VCGC:%s ‖ %s" % (r["lamp"], r["no"], r["category"], r["name"], r["vrn"], r["vdf"], r["vcgc"], r["state"]), flush=True)
            for p in rep["problems"]:
                print("  [RED] " + p, flush=True)
        if "--export" in argv:
            i = argv.index("--export")
            nxt = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("-") else None
            via = via_home()
            out = Path(nxt) if nxt else ((via / "VIA_Reports" / "vqg" / "price_fields") if via else Path.cwd() / "VIA_Reports" / "vqg" / "price_fields")
            r = export_scan(rep, out)
            print("[GREEN] VQG %s 行情輸入欄匯出 · %d 列 → %s · %s" % (VERSION_TAIL, r["rows"], r["csv"], r["md"]), flush=True)
        return 0 if rep["lamp"] == "GREEN" else (1 if rep["lamp"] in ("RED", "NODATA") else 0)
    rows = field_rows(book)
    only = argv[argv.index("--id") + 1] if "--id" in argv and argv.index("--id") + 1 < len(argv) else None
    if only:
        rows = [e for e in rows if only in (e.get("stable_id"), e.get("no"), e.get("code_key"))]
        if not rows:
            print("[RED] 冊上沒有輸入欄 %s" % only, flush=True)
            return 1
    print("VQG 行情輸入欄 %s · %s · %d 欄" % (book.get("version"), Path(book["_path"]).name, len(field_rows(book))), flush=True)
    for e in rows:
        if only or "--full" in argv:
            print("─" * 72, flush=True)
            for label, k in FIELD_COLUMNS:
                print("  %-10s %s" % (label, _cellv(e.get(k))), flush=True)
            print("  %-10s %s" % ("代碼", e.get("stable_id")), flush=True)
        else:
            print("  %-8s %-6s %-28s %-14s %s" % (e.get("no"), e.get("category"), e.get("stable_id"), e.get("name_zh"), e.get("formula")), flush=True)
    return 0


def selftest() -> int:
    ok = total = 0

    def chk(label, cond, note=""):
        nonlocal ok, total
        total += 1
        ok += bool(cond)
        print("  [%s] %s%s" % ("PASS" if cond else "FAIL", label, (" · " + str(note)) if note else ""), flush=True)
    print("[VQG %s selftest]" % VERSION_TAIL, flush=True)
    cp = subprocess.run([sys.executable, str(PRIOR_PATH), "selftest"], cwd=str(HERE), capture_output=True, text=True, encoding="utf-8", errors="replace",
                        timeout=3000, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    prior_lines = [l for l in (cp.stdout or "").splitlines() if l.strip().startswith(("[PASS]", "[FAIL]"))]
    chk("① 前版 v0111 SHA-256 釘住(一字未改)", PRIOR_SHA_OK)
    book = V11.load_register()
    rows = field_rows(book)
    chk("② 冊尾版有行情輸入欄 14 列 · 編號接在既有列之後不重號", len(rows) == 14 and len({e["no"] for e in book["entries"]}) == len(book["entries"]),
        "%s · %d 列" % (Path(book["_path"]).name, len(book["entries"])))
    c = fields_check(book)
    chk("③ 冊 ⇄ 程式對帳 GREEN(14 欄一對一 · stable_id / 公式 / VDF 來源欄一字相同)", c["lamp"] == "GREEN", c["problems"][:3])
    b = copy.deepcopy(book)
    next(e for e in b["entries"] if e.get("code_key") == "adj_open")["formula"] += " "
    chk("④ 公式差一個字 → RED", any("公式不同" in p and "ADJ_OPEN" in p for p in fields_check(b)["problems"]))
    b = copy.deepcopy(book)
    b["entries"] = [e for e in b["entries"] if e.get("code_key") != "turnover_ex_daytrade"]
    chk("⑤ 刪掉一列 → RED(程式有、冊沒登記)", any("turnover_ex_daytrade" in p for p in fields_check(b)["problems"]))
    b = copy.deepcopy(book)
    b["entries"].append(dict(rows[0], code_key="vwap", original_name="vwap", stable_id="VQG.IN.VWAP", no="VQG-998"))
    chk("⑥ 冊多一列程式沒有 → RED", any("冊上有、程式沒有" in p and "vwap" in p for p in fields_check(b)["problems"]))
    d = derive({"date": "2026-11-13", "ticker": "2330", "open": 100.0, "low": 95.0, "high": 110.0, "close": 105.0, "volume": 1000, "turnover": 104000.0,
                "yf_close": 105.0, "yf_adj_close": 94.5, "day_trade_volume": 300, "day_trade_value": 31000.0})
    chk("⑦ 算法:還原比例 0.9 → 還原開 90 · 高 99 · 低 85.5;扣除當沖 量 700 · 值 73000;原始欄原值帶出",
        all(abs(d[k] - v) < 1e-9 for k, v in (("adj_open", 90.0), ("adj_high", 99.0), ("adj_low", 85.5), ("turnover_ex_daytrade", 73000.0)))
        and d["volume_ex_daytrade"] == 700 and d["adj_close"] == 94.5 and d["close"] == 105.0 and d["volume"] == 1000 and not d["_flags"]
        and list(d)[:14] == list(INPUT_FIELDS), d["_flags"])
    d2 = derive({"date": "2026-11-13", "ticker": "00981A", "open": 10.0, "low": 9.0, "high": 11.0, "close": 10.5, "volume": 100, "turnover": 1000.0,
                 "yf_close": 0, "yf_adj_close": 10.5, "day_trade_volume": None, "day_trade_value": 2000.0})
    chk("⑧ 缺值不補:yf_close 為 0 → 還原三價空;當沖量缺 → 空(不當 0);相減為負 → 空並標記",
        d2["adj_open"] is None and d2["adj_high"] is None and d2["adj_low"] is None and d2["volume_ex_daytrade"] is None and d2["turnover_ex_daytrade"] is None
        and "no_adj_factor" in d2["_flags"] and "volume_ex_daytrade:missing_input" in d2["_flags"] and "turnover_ex_daytrade:negative" in d2["_flags"], d2["_flags"])
    with tempfile.TemporaryDirectory() as td:
        via = Path(td)
        (via / "functional modules" / "VDF").mkdir(parents=True)
        (via / "functional modules" / "VRN" / "SSOT").mkdir(parents=True)
        nb = via / "supportive modules" / "registry" / "VIA_NumberBooks"
        nb.mkdir(parents=True)
        names = ["date", "ticker", "open", "low", "high", "close", "volume", "turnover", "day_trade_volume", "day_trade_value", "yf_close", "yf_adj_close"]
        (via / "functional modules" / "VDF" / "VDF_TWEquity_DailyRow_Schema_v0100.json").write_text(
            json.dumps({"columns": [{"name": n, "zh": n, "dtype": "DOUBLE"} for n in names if n != "day_trade_value"]}), encoding="utf-8")
        (via / "functional modules" / "VDF" / "VDF_InputUniverse_SSOT_v0100.json").write_text(
            json.dumps({"inputs": [{"id": "IN-01", "group": "TW_STOCK", "zh": "股", "code_regex": "^A$"}, {"id": "IN-02", "group": "ETF", "zh": "基", "code_regex": "^B$"}]}), encoding="utf-8")
        (via / "functional modules" / "VRN" / "SSOT" / "VRN_FieldSpec_SSOT_v0100.json").write_text(json.dumps({"fields": {"close": {}}}), encoding="utf-8")
        (nb / "VIA_NumberBook_FD_v0100.jsonl").write_text("\n".join(json.dumps(
            {"code": "VIA-VDF-FD%03d" % i, "name": n, "sub": "VDF", "source": "functional modules/VDF/VDF_TWEquity_DailyRow_Schema_v0100.json"})
            for i, n in enumerate(names, 1) if n != "ticker") + "\n", encoding="utf-8")
        rep = scan(book, via)
        by = {r["name"]: r for r in rep["rows"]}
        chk("⑨ 掃描順序 VRN → VDF → VCGC · 14 欄都有一列 · 範圍兩組取自 VDF 輸入冊", rep["order"] == ["VRN", "VDF", "VCGC"] and len(rep["rows"]) == 14
            and [u["id"] for u in rep["universe"]] == ["IN-01", "IN-02"], rep["order"])
        chk("⑩ 掃描分得出三種狀態:齊 = GREEN · VDF 有欄中央沒號 = YELLOW(ticker)· VDF 沒這欄 = RED(day_trade_value)· VRN 有登的照列",
            by["open"]["lamp"] == "GREEN" and by["ticker"]["lamp"] == "YELLOW" and by["turnover_ex_daytrade"]["lamp"] == "RED"
            and by["close"]["vrn"].startswith("close@") and by["open"]["vrn"].startswith("未登記") and rep["lamp"] == "RED",
            {k: by[k]["lamp"] for k in ("open", "ticker", "turnover_ex_daytrade")})
        r = export_scan(rep, via / "out")
        with open(r["csv"], encoding="utf-8-sig") as fh:
            crow = list(csv.reader(fh))
        chk("⑪ 匯出 CSV + MD · 14 列 · 沒寫進 VDF / VRN 夾", len(crow) - 1 == 14 and Path(r["md"]).read_text(encoding="utf-8").count("\n| VQG-") == 14
            and sorted(p.name for p in (via / "functional modules" / "VDF").iterdir()) == ["VDF_InputUniverse_SSOT_v0100.json", "VDF_TWEquity_DailyRow_Schema_v0100.json"])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 本檔:第 3 行加速器橋 · 零網路 import · 不 import VDF / VAP · 無 TA-Lib",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0112]"
        and not re.search(r"^\s*(import|from)\s+(urllib|requests|socket|http|httpx|aiohttp|talib|VDF_|VAP_)", src, re.M))
    prior_ok = cp.returncode == 0
    for l in prior_lines[-3:]:
        print("    前版 " + l.strip(), flush=True)
    if not prior_ok and not prior_lines:
        print("    前版沒有跑起來:" + ((cp.stdout or cp.stderr or "").strip().splitlines() or ["(無輸出)"])[-1][:160], flush=True)
    good = ok == total and prior_ok
    print("[%s] VQG %s selftest · 本版 %d/%d · 前版鏈 v0111 %s" % ("PASS" if good else "FAIL", VERSION_TAIL, ok, total, "PASS" if prior_ok else "FAIL"), flush=True)
    return 0 if good else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = next((a for a in argv if not a.startswith("-")), "scan")
    if cmd in ("selftest", "test") or "--selftest" in argv:
        try:
            return selftest()
        except Exception as error:  # noqa: BLE001
            print("[FAIL] VQG %s selftest 中斷 · %s: %s" % (VERSION_TAIL, type(error).__name__, str(error)[:200]), flush=True)
            return 1
    if not PRIOR_SHA_OK:
        print("[RED] VQG %s 前版 %s 被改過(SHA-256 不符)· 停" % (VERSION_TAIL, PRIOR_NAME), flush=True)
        return 2
    if cmd == "fields":
        return fields(argv)
    if cmd == "indicators" and "--check" in argv:
        rc = V11.main(argv)
        return max(rc, fields(["fields", "--check"]))
    if "--help" in argv or "-h" in argv:
        rc = V11.main(argv)
        print("v0112:fields [--full | --id <代碼> | --check | --scan [--json] | --export [夾]](VQG 行情輸入欄 · 跨系統註冊檢查)", flush=True)
        return rc
    return V11.main(argv)


if __name__ == "__main__":
    sys.exit(main())
