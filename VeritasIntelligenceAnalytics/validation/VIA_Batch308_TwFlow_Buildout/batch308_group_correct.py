#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch308_group_correct — 族群冊官方機械改正(批308;v0110 → v0111)
====================================================================
改正律(官方名錄為準,留痕不刪;append-only 尊重批52 策展):
  · 市場歸屬:官方名錄實籍≠冊載 ⇒ market 改官方、market_seed 留舊、
    yfinance 後綴同步(.TW/.TWO)、verify_note 記時(機械改正——
    上櫃轉上市等沿革,零判斷成分)。
  · 官方查無代號(如 6562/2569):不刪——official_status 標
    NOT_IN_OFFICIAL 候操作員定奪(下市/代號誤植無從機械判)。
  · 名碼錯配(如 5263 冊載僑威 vs 官方智崴):不改名——
    official_name_conflict 記官方名候操作員定奪(意向不明不代決)。
  · 名稱變體(世界先進/世界):official_abbrev 資訊性補記。
產出:TW_Group_Classification_v0111.json(v0110 原檔不動)。
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
CFG = VIA / "supportive modules" / "VIA_FlowSystem" / "FlowSystem_v2" / "config"
SRC = CFG / "TW_Group_Classification_v0110.json"
DST = CFG / "TW_Group_Classification_v0111.json"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")

CODE_KEYS = ("公司代號", "SecuritiesCompanyCode")
NAME_KEYS = ("公司簡稱", "CompanyAbbreviation", "公司名稱", "CompanyName")
SNAPS = {"TWSE": HERE / "twse_t187ap03_L_snapshot_20260902.json",
         "TPEX": HERE / "tpex_t187ap03_O_snapshot_20260902.json",
         "EMG": HERE / "tpex_t187ap03_R_snapshot_20260902.json"}


def book(mkt: str) -> dict:
    rows = json.loads(SNAPS[mkt].read_text(encoding="utf-8"))
    out = {}
    for r in rows:
        c = next((str(r.get(k, "")).strip() for k in CODE_KEYS if str(r.get(k, "")).strip()), "")
        n = next((str(r.get(k, "")).strip() for k in NAME_KEYS if str(r.get(k, "")).strip()), "")
        if c:
            out[c] = n
    return out


def main() -> int:
    g = json.loads(SRC.read_text(encoding="utf-8"))
    twse, tpex, emg = book("TWSE"), book("TPEX"), book("EMG")
    n_mkt = n_missing = n_conflict = n_var = 0
    for gname, mem in g["groups"].items():
        for m in mem:
            t = m["ticker"]
            official = ("TWSE" if t in twse else "TPEX" if t in tpex
                        else "EMG" if t in emg else None)
            off_name = twse.get(t) or tpex.get(t) or emg.get(t) or ""
            if official is None:
                m["official_status"] = "NOT_IN_OFFICIAL_20260902"
                m["verify_note"] = f"批308 官方三名錄查無({NOW})——候操作員定奪(下市/代號誤植不代判)"
                n_missing += 1
                continue
            if official in ("TWSE", "TPEX") and m.get("market") != official:
                m["market_seed"] = m.get("market")
                m["market"] = official
                m["yfinance"] = f"{t}.TW" if official == "TWSE" else f"{t}.TWO"
                m["verify_note"] = f"批308 市場歸屬官方改正({NOW}):{m['market_seed']}→{official}(轉板沿革,機械改正)"
                n_mkt += 1
            elif official == "EMG":
                m["official_status"] = "EMERGING_20260902"
                m["verify_note"] = f"批308 官方實籍=興櫃({NOW})——候操作員定奪市場欄制"
                n_missing += 1
            if off_name:
                nm = m["name"]
                base = nm.replace("-KY", "").replace("*", "")
                offb = off_name.replace("-KY", "").replace("*", "")
                if nm != off_name:
                    if base and (base in offb or offb in base):
                        m["official_abbrev"] = off_name
                        n_var += 1
                    else:
                        m["official_name_conflict"] = off_name
                        m["verify_note"] = (m.get("verify_note", "") +
                                            f";名碼錯配:官方簡稱「{off_name}」≠冊載「{nm}」候操作員定奪")
                        n_conflict += 1
    g["version"] = "1.2"
    g["generated"] = NOW
    g.setdefault("history", []).append(
        {"ts": NOW, "op": "批308 官方驗證改正",
         "market_corrected": n_mkt, "flagged_not_official": n_missing,
         "name_conflicts_flagged": n_conflict, "variants_annotated": n_var,
         "rule": "市場歸屬=官方名錄機械改正留痕;查無/名碼錯配=標旗候操作員定奪不代決"})
    DST.write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [出] {DST.name} — 市場改正 {n_mkt} · 查無/興櫃標旗 {n_missing}"
          f" · 名碼錯配標旗 {n_conflict} · 變體補記 {n_var}(v0110 原檔不動)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
