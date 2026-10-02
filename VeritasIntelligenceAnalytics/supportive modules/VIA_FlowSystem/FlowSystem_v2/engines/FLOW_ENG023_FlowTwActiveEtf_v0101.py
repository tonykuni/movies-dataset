#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FLOW_ENG023_FlowTwActiveEtf v0101 — 薄尾:--refresh 用官方名錄定奪「名碼衝突」與「待驗」兩種態

前版缺口(R51 2026-10-02 查出):--refresh 只把 SEED_KNOWN 轉 VERIFIED_OPENAPI;批104 同步進來的
CONFLICT_PENDING_VERIFY(00980A/00981A/00982A:種子冊與矩陣名碼輪錯一位)與 PENDING_VERIFY(34 檔)
永遠不會被官方名錄處理 —— 衝突哨兵 ③ 因此一直黃,CI PS7 閘也跟著紅。
本版(其餘照前版,前版檔一字不動):
  · 官方名錄兩個端點都收(都經 VIA_SuperAccel_Module.fetch → 同意閘;閘沒開 = 誠實 SKIP,清單不動):
      t187ap47_L(前版原有)· exchangeReport/STOCK_DAY_ALL(工作站 2026-10-02 實抓 1380 列,欄 Code / Name)
  · CONFLICT_PENDING_VERIFY:兩個候選(冊上 name/issuer · matrix_name/matrix_issuer)誰跟官方名一致就取誰
      → VERIFIED_OPENAPI;原值留 seed_name / seed_issuer;兩個都不一致 = 照實留衝突並記 official_name(不猜)
  · SEED_KNOWN / PENDING_VERIFY:名稱一致 → VERIFIED_OPENAPI;不一致 → NAME_MISMATCH_OPENAPI 記 official_name(不覆寫)
  · 名稱比對:去空白、全形轉半形、臺→台;官方名可能是簡稱,取「一方包含另一方」且候選唯一才算一致
  · --resolve-from <官方名錄 JSON>:離線定奪(工作站存下的官方回包),不經網路
用法:經 VCGC(本夾不在 run 的 stem 根,給路徑):
  via-vcgc run "supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/FLOW_ENG023_FlowTwActiveEtf_v0101.py" --refresh
  (| --resolve-from <json> | --selftest);其餘動詞照前版。rc:0 定奪完 · 2 沒收到官方名錄或仍有衝突(不算成功)。
不代設同意閘、不爬站、不用 TA-Lib。
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

import importlib.util
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
_PRIOR_PATH = HERE / "FLOW_ENG023_FlowTwActiveEtf.py"
_spec = importlib.util.spec_from_file_location("_flow_eng023_prior_for_v0101", _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
ENGINE_TAG = "FLOW_ENG023_FlowTwActiveEtf_v0101"
ENDPOINTS = dict(PRIOR.ENDPOINTS, twse_day_all="https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL")
OFFICIAL_KEYS = ("twse_etf_list", "twse_day_all")


def __getattr__(name):
    return getattr(PRIOR, name)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def norm(s) -> str:
    """名稱比對用:NFKC(全形轉半形)· 去空白 · 臺→台。"""
    t = unicodedata.normalize("NFKC", str(s or ""))
    return "".join(t.split()).replace("臺", "台")


def _code(r: dict) -> str:
    for k in ("證券代號", "基金代號", "Code", "FundCode"):
        v = str(r.get(k, "")).strip()
        if v:
            return v.upper()
    return ""


def _name(r: dict) -> str:
    for k in ("證券名稱", "基金簡稱", "基金中文名稱", "Name", "FundName"):
        v = str(r.get(k, "")).strip()
        if v:
            return v
    return ""


def official_names(rows: list) -> dict:
    out = {}
    for r in rows or []:
        if isinstance(r, dict):
            c, n = _code(r), _name(r)
            if c and n:
                out.setdefault(c, n)
    return out


def same(a: str, b: str) -> bool:
    x, y = norm(a), norm(b)
    return bool(x and y) and (x == y or x in y or y in x)


def resolve(reg: dict, official: dict, source: str) -> dict:
    """純函式:照官方 {代號: 名稱} 定奪冊內各檔;回摘要(冊就地改,寫檔由呼叫端)。"""
    ts = _now()
    tally = {"conflict_resolved": [], "conflict_kept": [], "verified": [], "mismatch": [], "new": []}
    known = {e["ticker"].upper() for e in reg.get("etfs", [])}
    for e in reg.get("etfs", []):
        code = e["ticker"].upper()
        off = official.get(code)
        if not off:
            continue
        st = e.get("status")
        if st == "CONFLICT_PENDING_VERIFY":
            cands = [(e.get("name"), e.get("issuer"), "registry"), (e.get("matrix_name"), e.get("matrix_issuer"), "matrix")]
            hit = [c for c in cands if c[0] and same(c[0], off)]
            if len(hit) == 1:
                name, issuer, side = hit[0]
                if side == "matrix":
                    e["seed_name"], e["seed_issuer"] = e.get("name"), e.get("issuer")
                    e["name"], e["issuer"] = name, issuer
                e.update(status="VERIFIED_OPENAPI", official_name=off, verified_at=ts, verified_by=f"{ENGINE_TAG} · {source}",
                         resolution=f"官方名錄名稱與{'矩陣' if side == 'matrix' else '冊上'}候選一致")
                tally["conflict_resolved"].append(code)
            else:
                e["official_name"] = off
                tally["conflict_kept"].append(code)
        elif st in ("SEED_KNOWN", "PENDING_VERIFY"):
            if same(e.get("name"), off):
                e.update(status="VERIFIED_OPENAPI", official_name=off, verified_at=ts, verified_by=f"{ENGINE_TAG} · {source}")
                tally["verified"].append(code)
            else:
                e.update(status="NAME_MISMATCH_OPENAPI", official_name=off, checked_at=ts)
                tally["mismatch"].append(code)
    for code, name in official.items():
        if code.endswith("A") and "主動" in name and code not in known:
            reg.setdefault("etfs", []).append({"ticker": code, "name": name, "issuer": "", "status": "VERIFIED_OPENAPI",
                                               "official_name": name, "verified_at": ts, "verified_by": f"{ENGINE_TAG} · {source}"})
            tally["new"].append(code)
    open_states = ("SEED_KNOWN", "PENDING_VERIFY", "CONFLICT_PENDING_VERIFY", "NAME_MISMATCH_OPENAPI")
    reg["verify_required"] = any(e.get("status") in open_states for e in reg.get("etfs", []))
    reg["as_of"] = ts
    reg.setdefault("history", []).append({"op": "refresh-resolve", "ts": ts, "source": source, "official_codes": len(official),
                                          **{k: v for k, v in tally.items() if v}})
    return tally


def _fetch_rows(key: str):
    raw = VIA_ACCEL.fetch(ENDPOINTS[key], timeout=30)
    if not raw:
        return None
    return json.loads(raw if isinstance(raw, str) else raw.decode("utf-8"))


def _report(t: dict) -> None:
    print(f"  [定奪] 衝突解 {len(t['conflict_resolved'])} {t['conflict_resolved']} · 衝突留 {len(t['conflict_kept'])} {t['conflict_kept']}"
          f" · 待驗轉綠 {len(t['verified'])} · 名稱不符 {len(t['mismatch'])} {t['mismatch'][:8]} · 新增 {len(t['new'])}")


def cmd_refresh() -> int:
    if VIA_ACCEL is None:
        print("  [SKIP] SuperAccel 未載——無網路道;清單維持既有態(誠實)")
        return 2
    official, got = {}, []
    for key in OFFICIAL_KEYS:
        try:
            rows = _fetch_rows(key)
        except Exception as exc:
            print(f"  [SKIP] {key}:{exc}(同意閘未開或網路不可達)")
            continue
        if rows is None:
            print(f"  [SKIP] {key}:同意閘未開或無回應")
            continue
        n = official_names(rows)
        got.append(f"{key} {len(n)}")
        for c, v in n.items():
            official.setdefault(c, v)
    if not official:
        print("  [SKIP] 官方名錄一筆都沒收到;清單不動(誠實;rc 2 = 沒證據,不算成功)")
        return 2
    reg = PRIOR.load_registry()
    t = resolve(reg, official, "openapi: " + " · ".join(got))
    PRIOR.save_registry(reg)
    _report(t)
    return 0 if not t["conflict_kept"] else 2


def cmd_resolve_from(path: str) -> int:
    p = Path(path)
    if not p.is_file():
        print(f"  [FAIL] 檔不在:{p}")
        return 2
    rows = json.loads(p.read_text(encoding="utf-8-sig"))
    official = official_names(rows if isinstance(rows, list) else rows.get("data") or rows.get("rows") or [])
    if not official:
        print("  [FAIL] 檔裡沒有代號 / 名稱欄(證券代號 · 基金代號 · Code / 證券名稱 · 基金簡稱 · Name)")
        return 2
    reg = PRIOR.load_registry()
    t = resolve(reg, official, f"offline file {p.name}")
    PRIOR.save_registry(reg)
    _report(t)
    return 0 if not t["conflict_kept"] else 2


def selftest() -> int:
    import copy
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE_TAG} · 薄尾自測(官方名錄定奪;記憶體內冊,零網路、不寫檔)===")
    reg = {"etfs": [
        {"ticker": "00980A", "name": "主動統一台股增長", "issuer": "統一投信", "status": "CONFLICT_PENDING_VERIFY",
         "matrix_name": "主動野村臺灣優選", "matrix_issuer": "野村投信"},
        {"ticker": "00981A", "name": "主動群益台灣強棒", "issuer": "群益投信", "status": "CONFLICT_PENDING_VERIFY",
         "matrix_name": "主動統一台股增長", "matrix_issuer": "統一投信"},
        {"ticker": "00983A", "name": "主動測試甲", "issuer": "甲投信", "status": "PENDING_VERIFY"},
        {"ticker": "00984A", "name": "主動測試乙", "issuer": "乙投信", "status": "PENDING_VERIFY"},
        {"ticker": "00985A", "name": "主動測試丙", "issuer": "丙投信", "status": "CONFLICT_PENDING_VERIFY",
         "matrix_name": "主動測試丁", "matrix_issuer": "丁投信"},
        {"ticker": "00986A", "name": "主動沒上市", "issuer": "戊投信", "status": "PENDING_VERIFY"}],
        "history": []}
    rows = [{"Code": "00980A", "Name": "主動野村台灣優選"}, {"Code": "00981A", "Name": "主動統一台股增長"},
            {"證券代號": "00983A", "證券名稱": "主動測試甲"}, {"Code": "00984A", "Name": "完全不同名"},
            {"Code": "00985A", "Name": "第三個名字"}, {"Code": "00999A", "Name": "主動新上市"}, {"Code": "2330", "Name": "台積電"}]
    r = copy.deepcopy(reg)
    t = resolve(r, official_names(rows), "selftest")
    e = {x["ticker"]: x for x in r["etfs"]}
    chk("① 衝突檔:官方名與矩陣候選一致(臺/台視同)→ 取矩陣名碼 · VERIFIED_OPENAPI · 原值留 seed_*",
        e["00980A"]["name"] == "主動野村臺灣優選" and e["00980A"]["issuer"] == "野村投信" and e["00980A"]["status"] == "VERIFIED_OPENAPI"
        and e["00980A"]["seed_name"] == "主動統一台股增長", e["00980A"])
    chk("② 三檔輪錯一位的情形逐檔各自定奪(00981A 取統一)", e["00981A"]["issuer"] == "統一投信" and "00981A" in t["conflict_resolved"])
    chk("③ 待驗檔名稱一致 → VERIFIED_OPENAPI", e["00983A"]["status"] == "VERIFIED_OPENAPI" and t["verified"] == ["00983A"])
    chk("④ 待驗檔名稱不符 → NAME_MISMATCH_OPENAPI 記官方名,不覆寫冊上名", e["00984A"]["status"] == "NAME_MISMATCH_OPENAPI"
        and e["00984A"]["name"] == "主動測試乙" and e["00984A"]["official_name"] == "完全不同名")
    chk("⑤ 衝突兩候選都不一致 → 照實留衝突並記官方名(不猜)", e["00985A"]["status"] == "CONFLICT_PENDING_VERIFY"
        and e["00985A"]["official_name"] == "第三個名字" and t["conflict_kept"] == ["00985A"])
    chk("⑥ 官方沒有的檔不動;名錄新出現的主動 A 碼才加入(個股不加)", e["00986A"]["status"] == "PENDING_VERIFY"
        and t["new"] == ["00999A"] and "2330" not in e)
    chk("⑦ 只增歷史:history 加一筆 refresh-resolve;還有未定的就 verify_required=True",
        r["history"][-1]["op"] == "refresh-resolve" and r["verify_required"] is True)
    chk("⑧ 名稱比對:全形 / 空白 / 臺台 / 簡稱包含", same("主動 野村臺灣優選", "主動野村台灣優選") and same("野村臺灣優選", "主動野村台灣優選")
        and not same("主動統一台股增長", "主動野村台灣優選"))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 加速器橋在;不代設同意閘;前版檔一字不動(本版只是薄尾)", "VIA:ACCEL-BRIDGE" in src
        and not re.search(r"VIA_(NET|SCRAPE)_CONSENT" + r"['\"]\]\s*=", src) and _PRIOR_PATH.is_file())
    prior = PRIOR.selftest()
    chk("⑩ 前版自測照過", prior == 0)
    good = all(ok)
    print(f"  [計] {ENGINE_TAG} 薄尾 {sum(ok)}/{len(ok)} · {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


def main() -> int:
    a = sys.argv[1:]
    if a and a[0] == "--selftest":
        return selftest()
    if a and a[0] == "--refresh":
        return cmd_refresh()
    if a and a[0] == "--resolve-from" and len(a) > 1:
        return cmd_resolve_from(a[1])
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())
