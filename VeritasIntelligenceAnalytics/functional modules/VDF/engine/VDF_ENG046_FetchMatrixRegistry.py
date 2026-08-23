#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG046_FetchMatrixRegistry — VDF-390 擷取總冊機器轉錄引擎(批104)
====================================================================
職責(AI 只整理不發明;凡數字皆由解析計得,宣告值另欄存證):
  ① 解析 VDF_FetchOne_Matrix_SSOT_v0100.md(操作員批104 原樣收容件)
     → VDF_FetchOne_Matrix_Registry_v0100.json(結構化:段/項/來源/
     fetcher/頻率/欄位/引用/狀態 DONE·PROXY·TODO)
  ② 抽取台股主動式 ETF 清冊(EF-01A…X 股票24 + EF-40A…F 海外6 +
     EF-41A…G 債券7 = 37 檔)→ 與 FlowSystem TW_Active_ETF_Registry
     交叉對讀;--sync-etf 把缺漏碼補入該冊(只增不減,verified=false
     =候 TWSE 官方 OpenAPI 實連驗證;容器側不外呼=誠實邊界)
  ③ 台股個股日表 header 依批104 令另檔
     VDF_TWEquity_DailyRow_Schema_v0100.json(本引擎驗其一致性)
用法:
  py VDF_ENG046_FetchMatrixRegistry.py            # 轉錄+對讀報告
  py VDF_ENG046_FetchMatrixRegistry.py --sync-etf # 同步 ETF 冊(寫入)
  py VDF_ENG046_FetchMatrixRegistry.py --selftest # 八檢(沙盒零網路)
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

import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .../functional modules/VDF/engine
VDF = HERE.parent                               # .../functional modules/VDF
VIA = VDF.parent.parent                         # VIA 根(動態解析,嚴禁寫死)
MD_GLOB = "VDF_FetchOne_Matrix_SSOT_v*.md"      # 動態接最新版(鐵律)
REG_OUT = VDF / "VDF_FetchOne_Matrix_Registry_v0100.json"
SCHEMA_PATH_GLOB = "VDF_TWEquity_DailyRow_Schema_v*.json"
ETF_REG = (VIA / "supportive modules" / "VIA_FlowSystem" / "FlowSystem_v2"
           / "config" / "TW_Active_ETF_Registry_v0100.json")

ID_RE = re.compile(r"^\s*([A-Z]{2}-[A-Z0-9]{1,4})\s*$")
STATUS_RE = re.compile(r"(✓ DONE|📡 PROXY|✗ TODO)")
FETCHER_RE = re.compile(r"vdf_fetchers_\w+")
ETF_CODE_RE = re.compile(r"^(00\d{2,3}[AD])\s+(.+)$")
STATUS_MAP = {"✓ DONE": "DONE", "📡 PROXY": "PROXY", "✗ TODO": "TODO"}


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = sorted(folder.glob(pattern))
    return hits[-1] if hits else None


def parse_matrix(md_path: Path) -> dict:
    """收容件 → 結構化行表。段=## 標題;行=ID→名→來源/fetcher/頻率→欄位→引用+狀態。"""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    section = ""
    items, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("## "):
            section = ln[3:].strip()
            i += 1
            continue
        m = ID_RE.match(ln)
        if not m:
            i += 1
            continue
        item_id = m.group(1)
        body = []
        j = i + 1
        while j < len(lines) and not STATUS_RE.search(lines[j]):
            if lines[j].strip():
                body.append(lines[j].rstrip())
            j += 1
        status_line = lines[j] if j < len(lines) else ""
        sm = STATUS_RE.search(status_line)
        status = STATUS_MAP.get(sm.group(1)) if sm else "UNKNOWN"
        refs = status_line[:sm.start()].strip().strip("\t") if sm else ""
        name = body[0].strip() if body else ""
        source = fetcher = freq = fields = ""
        for b in body[1:]:
            if FETCHER_RE.search(b):
                parts = [p for p in b.split("\t") if p.strip()]
                fm = FETCHER_RE.search(b)
                fetcher = fm.group(0)
                source = parts[0].strip() if parts else ""
                freq = parts[-1].strip() if len(parts) >= 3 else ""
            elif not fields:
                fields = b.strip()
        items.append({"id": item_id, "section": section, "name": name,
                      "source": source, "fetcher": fetcher, "freq": freq,
                      "fields": fields, "refs": refs, "status": status})
        i = j + 1
    return {"items": items}


def extract_active_etfs(items: list[dict]) -> dict:
    """EF-01A…X / EF-40A…F / EF-41A…G → 37 檔清冊(碼·名·投信·型別)"""
    out = {"equity_tw": [], "equity_global": [], "bond": []}
    for it in items:
        iid = it["id"]
        m = ETF_CODE_RE.match(it["name"])
        if not m:
            continue
        rec = {"code": m.group(1), "name": m.group(2).strip(),
               "issuer": it["source"], "matrix_id": iid}
        if re.match(r"EF-01[A-Z]$", iid):
            rec["type"] = "股票型(台股)"
            out["equity_tw"].append(rec)
        elif re.match(r"EF-40[A-Z]$", iid):
            rec["type"] = "股票型(海外)"
            out["equity_global"].append(rec)
        elif re.match(r"EF-41[A-Z]$", iid):
            rec["type"] = "債券型"
            out["bond"].append(rec)
    return out


def build_registry(md_path: Path) -> dict:
    parsed = parse_matrix(md_path)
    items = parsed["items"]
    counts = {"DONE": 0, "PROXY": 0, "TODO": 0, "UNKNOWN": 0}
    for it in items:
        counts[it["status"]] = counts.get(it["status"], 0) + 1
    sections = {}
    for it in items:
        sections.setdefault(it["section"], 0)
        sections[it["section"]] += 1
    etfs = extract_active_etfs(items)
    return {
        "schema": "vdf-fetchone-matrix-registry-v1",
        "source_md": md_path.name,
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "provenance": "批104 操作員核定矩陣之機器轉錄;宣告值(Items 17/Domains 187/"
                      "Engines 296/Done 75…)為操作員頁面宣告,與本冊實算計數並列存證,"
                      "不互相冒充;實際可用性候 vdf_api 健康檢查回寫。",
        "counts_measured": {"total_items": len(items), **counts},
        "sections_measured": sections,
        "active_etf_roster": {
            "total": sum(len(v) for v in etfs.values()),
            "equity_tw": etfs["equity_tw"],
            "equity_global": etfs["equity_global"],
            "bond": etfs["bond"],
            "verify_policy": "清單自動驗證維護(批104):候 TWSE OpenAPI 實連比對;"
                             "容器側不外呼=誠實邊界,verified=false 直到工作站驗證波",
        },
        "governance": {
            "adj_priority": "有 adjClose 一律優先;Adj 全序列算報酬/正規化/技術指標;split 同步調 volume",
            "gap_fill": "價格缺值取前一交易日;成交量不補;混頻以低頻對齊",
            "required_fields": ["date", "value"],
            "optional_fields": ["series", "unit", "freq", "adjClose", "volume", "source", "asof"],
            "authority_order": ["官方(政府/交易所/央行)", "授權商業源", "代理(FRED proxy)", "推導模型"],
            "status_semantics": "DONE=宣告已實作;PROXY=代理源近似須標記;TODO=未接線不得視為可得",
        },
        "items": items,
    }


def sync_etf_registry(roster: dict, write: bool) -> dict:
    """FlowSystem TW_Active_ETF_Registry 交叉對讀;write=True 補缺漏(只增不減)"""
    if not ETF_REG.exists():
        return {"state": "MISSING", "note": str(ETF_REG)}
    reg = json.loads(ETF_REG.read_text(encoding="utf-8-sig"))
    by_ticker = {e.get("ticker"): e for e in reg.get("etfs", []) if isinstance(e, dict)}
    matrix_all = roster["equity_tw"] + roster["equity_global"] + roster["bond"]
    missing = [r for r in matrix_all if r["code"] not in by_ticker]
    conflicts = [r for r in matrix_all
                 if r["code"] in by_ticker
                 and by_ticker[r["code"]].get("name") not in ("", None, r["name"])]
    report = {"state": "OK", "registry_codes": len(by_ticker),
              "matrix_codes": len(matrix_all),
              "missing_in_registry": len(missing),
              "name_conflicts": len(conflicts),
              "conflict_codes": [r["code"] for r in conflicts],
              "missing_codes": [r["code"] for r in missing]}
    if write and (missing or conflicts):
        for r in missing:
            reg["etfs"].append({"ticker": r["code"], "name": r["name"],
                                "issuer": r["issuer"], "type": r["type"],
                                "source": "批104 VDF-390 矩陣(操作員核定)",
                                "status": "PENDING_VERIFY", "verified": False,
                                "verify_note": "候 TWSE OpenAPI 實連驗證(工作站波)"})
        for r in conflicts:
            # 零刪除:舊種子欄位原地保留,加註矩陣側對映+衝突狀態候實連定奪
            e = by_ticker[r["code"]]
            e["status"] = "CONFLICT_PENDING_VERIFY"
            e["matrix_name"] = r["name"]
            e["matrix_issuer"] = r["issuer"]
            e["conflict_note"] = "種子冊與批104 矩陣名碼對映不符;實連 TWSE 驗證前不定奪"
        reg.setdefault("history", []).append({
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "op": "批104 SYNC", "added": len(missing), "conflicts": len(conflicts),
            "note": "VDF-390 矩陣 37 檔清冊同步;只增不減;新增 verified=false、"
                    "名碼衝突標 CONFLICT_PENDING_VERIFY 候 TWSE 實連驗證"})
        reg["verify_required"] = True
        ETF_REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8")
        report["synced"] = len(missing)
    return report


def check_schema() -> dict:
    """行表 schema 冊在位+批104 必要欄位齊備檢"""
    sp = _newest(VDF, SCHEMA_PATH_GLOB)
    if sp is None:
        return {"state": "MISSING"}
    sc = json.loads(sp.read_text(encoding="utf-8-sig"))
    cols = [c["name"] for c in sc.get("columns", [])]
    need = ["date", "ticker", "yfinance_ticker", "bloomberg_ticker", "name",
            "open", "low", "high", "close", "volume", "turnover",
            "inst_foreign_net", "inst_trust_net", "inst_dealer_net",
            "margin_balance", "short_balance", "short_to_margin_ratio",
            "margin_maintenance_ratio", "short_maintenance_ratio",
            "day_trade_value", "day_trade_ratio",
            "yf_close", "yf_adj_close", "yf_volume"]
    missing = [c for c in need if c not in cols]
    return {"state": "OK" if not missing else "FAIL", "file": sp.name,
            "columns": len(cols), "missing": missing,
            "index_db_separate": sc.get("indices", {}).get("separate_database", False)}


def run(sync: bool) -> int:
    md = _newest(VDF, MD_GLOB)
    if md is None:
        print("[FAIL] 收容件缺(VDF_FetchOne_Matrix_SSOT_v*.md)")
        return 1
    reg = build_registry(md)
    REG_OUT.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
    c = reg["counts_measured"]
    r = reg["active_etf_roster"]
    print(f"  [冊] {REG_OUT.name} · 實算 {c['total_items']} 項"
          f"(DONE {c['DONE']} · PROXY {c['PROXY']} · TODO {c['TODO']})· 段 {len(reg['sections_measured'])}")
    print(f"  [ETF] 主動式清冊:台股 {len(r['equity_tw'])} + 海外 {len(r['equity_global'])}"
          f" + 債券 {len(r['bond'])} = {r['total']} 檔")
    er = sync_etf_registry(r, write=sync)
    print(f"  [對讀] FlowSystem 冊 {er.get('registry_codes', '?')} 碼 vs 矩陣 {er.get('matrix_codes', '?')} 碼"
          f" · 缺 {er.get('missing_in_registry', '?')}"
          + (f" · 已補入 {er['synced']}(verified=false 候實連)" if er.get("synced") else
             ("(--sync-etf 可補入)" if er.get("missing_in_registry") else "")))
    sk = check_schema()
    print(f"  [schema] 行表冊 {sk.get('file', 'MISSING')} · 欄 {sk.get('columns', 0)}"
          f" · 批104 必要欄缺 {len(sk.get('missing', ['ALL']))} · 指數獨立庫={sk.get('index_db_separate')}")
    ok = (c["UNKNOWN"] == 0 and r["total"] == 37 and sk.get("state") == "OK")
    print(f"  [計] {'OK 轉錄+對讀綠' if ok else 'WARN 有黃燈,見上'}")
    return 0 if ok else 1


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    md = _newest(VDF, MD_GLOB)
    chk("① 收容件在位(glob 最新版)", md is not None, f"({md.name if md else '缺'})")
    reg = build_registry(md)
    items = reg["items"]
    c = reg["counts_measured"]
    chk("② 解析非空且零 UNKNOWN", c["total_items"] > 200 and c["UNKNOWN"] == 0,
        f"({c['total_items']} 項)")
    by_id = {it["id"]: it for it in items}
    chk("③ 錨定抽查(PX-01/FN-06/EF-42)",
        by_id.get("PX-01", {}).get("source") == "TWSE"
        and by_id.get("FN-06", {}).get("freq") == "月"
        and "37 檔" in by_id.get("EF-42", {}).get("name", ""))
    chk("④ 狀態三態計數守恆",
        c["DONE"] + c["PROXY"] + c["TODO"] == c["total_items"],
        f"(D{c['DONE']}/P{c['PROXY']}/T{c['TODO']})")
    r = reg["active_etf_roster"]
    chk("⑤ 主動 ETF 24+6+7=37",
        len(r["equity_tw"]) == 24 and len(r["equity_global"]) == 6
        and len(r["bond"]) == 7 and r["total"] == 37)
    codes = [e["code"] for grp in ("equity_tw", "equity_global", "bond") for e in r[grp]]
    chk("⑥ ETF 碼唯一+格式", len(set(codes)) == 37
        and all(re.match(r"^00\d{2,3}[AD]$", x) for x in codes))
    er = sync_etf_registry(r, write=False)
    chk("⑦ FlowSystem 冊對讀可達", er["state"] in ("OK", "MISSING"),
        f"({er.get('registry_codes', '缺冊')} 碼 · 缺 {er.get('missing_in_registry', '—')})")
    sk = check_schema()
    chk("⑧ 行表 schema 批104 欄位齊+指數獨立庫", sk.get("state") == "OK"
        and sk.get("index_db_separate") is True, f"({sk.get('columns', 0)} 欄)")
    n = 8 - len(fails)
    print(f"  [計] 八檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== ENG046 擷取總冊轉錄 · 八檢自測(沙盒零網路)===")
        return selftest()
    return run(sync="--sync-etf" in args)


if __name__ == "__main__":
    sys.exit(main())
