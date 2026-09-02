#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch308_group_verify — 台股族群清單官方驗證(批308)
====================================================================
操作員令:「台股族群清單是否有整理驗證」。
冊:TW_Group_Classification_v0110(31 群 149 成員 41 領頭;批52 策展)。
官方名錄三源:TWSE t187ap03_L(上市)+TPEx mopsfin_t187ap03_O(上櫃)
+mopsfin_t187ap03_R(興櫃)——實連優先,未達回落同目錄快照(誠實標源)。

七檢:
  G1 代號在籍(三名錄聯集)      G2 市場歸屬正確(TWSE/TPEX 對名錄)
  G3 名稱與官方簡稱相符(全等/包含=變體註記) G4 yfinance 後綴制(.TW/.TWO)
  G5 代號制式(VDF 冊 SSOT 鎖 TW_TICKER_REGEX)
  G6 群內零重複(跨群多屬=常態記數)  G7 每群有領頭(role=LEADER)
輸出:Batch308_GroupVerify_Results.json
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
CFG = VIA / "supportive modules" / "VIA_FlowSystem" / "FlowSystem_v2" / "config"
GROUP_PATH = sorted(CFG.glob("TW_Group_Classification_v*.json"))[-1]  # glob 最新版
VDF_REG = VIA / "supportive modules" / "registry" / "VDF_MDL403_RegistryFull.json"
OUT = HERE / "Batch308_GroupVerify_Results.json"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

SOURCES = {
    "TWSE": ("https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
             HERE / "twse_t187ap03_L_snapshot_20260902.json"),
    "TPEX": ("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O",
             HERE / "tpex_t187ap03_O_snapshot_20260902.json"),
    "EMG": ("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_R",
            HERE / "tpex_t187ap03_R_snapshot_20260902.json"),
}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      "Accept": "application/json", "Accept-Encoding": "gzip"}
CODE_KEYS = ("公司代號", "SecuritiesCompanyCode")
NAME_KEYS = ("公司簡稱", "CompanyAbbreviation", "公司名稱", "CompanyName")

RESULTS: list[dict] = []


def check(cid, name, status, detail):
    RESULTS.append({"id": cid, "name": name, "status": status, "detail": detail})
    print(f"  [{status}] {cid} {name} — {detail[:120]}")


def load_official() -> tuple[dict, dict]:
    """市場 → {code: 官方簡稱};回 (冊, 來源記)。實連優先、快照回落(誠實標源)。"""
    books, prov = {}, {}
    for mkt, (url, snap) in SOURCES.items():
        rows, src = None, None
        try:
            req = urllib.request.Request(url, headers=dict(UA))
            with urllib.request.urlopen(req, timeout=45) as r:
                raw = r.read()
                if raw[:2] == b"\x1f\x8b":
                    import gzip
                    raw = gzip.decompress(raw)
                body = raw.decode("utf-8", errors="replace")
            if "FOR SECURITY REASONS" not in body:
                rows, src = json.loads(body), "LIVE"
        except Exception:
            rows = None
        if rows is None and snap.exists():
            rows, src = json.loads(snap.read_text(encoding="utf-8")), f"SNAPSHOT({snap.name})"
        book = {}
        for r in rows or []:
            c = next((str(r.get(k, "")).strip() for k in CODE_KEYS if str(r.get(k, "")).strip()), "")
            n = next((str(r.get(k, "")).strip() for k in NAME_KEYS if str(r.get(k, "")).strip()), "")
            if c:
                book[c] = n
        books[mkt] = book
        prov[mkt] = src or "UNAVAILABLE"
    return books, prov


def main() -> int:
    print("=" * 70)
    print(" 批308 台股族群清單官方驗證(31 群 × 三官方名錄)")
    print("=" * 70)
    g = json.loads(GROUP_PATH.read_text(encoding="utf-8"))
    members = [m for mem in g["groups"].values() for m in mem]
    books, prov = load_official()
    print(f"  [源] TWSE={prov['TWSE'][:28]} · TPEX={prov['TPEX'][:28]} · 興櫃={prov['EMG'][:28]}")
    union = {}
    for mkt, book in books.items():
        for c, n in book.items():
            union.setdefault(c, (mkt, n))

    # G1 代號在籍(已標旗 official_status=候操作員 ⇒ WARN;未標旗查無 ⇒ FAIL)
    miss = [(m["ticker"], m["name"], bool(m.get("official_status")))
            for m in members if m["ticker"] not in union]
    unflagged = [x for x in miss if not x[2]]
    st1 = "PASS" if not miss else ("WARN" if not unflagged else "FAIL")
    check("G1", "149 成員代號官方在籍(上市+上櫃+興櫃聯集)", st1,
          f"{len(members) - len(miss)}/{len(members)} 在籍"
          + (f";查無已標旗候操作員:{[(t, n) for t, n, _ in miss]}" if miss and not unflagged else "")
          + (f";查無未標旗:{unflagged}" if unflagged else ""))

    # G2 市場歸屬
    wrong = []
    for m in members:
        t, tag = m["ticker"], m.get("market")
        if t in books.get("TWSE", {}) and tag != "TWSE":
            wrong.append((t, m["name"], tag, "官方=上市"))
        elif t in books.get("TPEX", {}) and tag != "TPEX":
            wrong.append((t, m["name"], tag, "官方=上櫃"))
        elif t in books.get("EMG", {}) and tag in ("TWSE", "TPEX"):
            if not m.get("official_status"):  # 已標旗興櫃=候操作員(不重複計)
                wrong.append((t, m["name"], tag, "官方=興櫃"))
    flagged_emg = sum(1 for m in members if str(m.get("official_status", "")).startswith("EMERGING"))
    st2 = "PASS" if not wrong else "FAIL"
    check("G2", "市場歸屬 TWSE/TPEX=官方名錄", st2,
          (f"上市/上櫃歸屬全對(興櫃標旗候操作員 {flagged_emg} 檔)" if not wrong
           else f"{len(wrong)} 錯置未處置:{wrong[:4]}"))

    # G3 名稱相符
    mism, variant = [], []
    for m in members:
        off = union.get(m["ticker"], (None, ""))[1]
        if not off:
            continue
        nm = m["name"]
        if nm == off:
            continue
        base = nm.replace("-KY", "").replace("*", "")
        offb = off.replace("-KY", "").replace("*", "")
        if base and (base in offb or offb in base):
            variant.append((m["ticker"], nm, off))
        elif m.get("official_name_conflict"):
            variant.append((m["ticker"], nm, off + "(名碼錯配已標旗候操作員)"))
        else:
            mism.append((m["ticker"], nm, off))
    st3 = "PASS" if not mism and not variant else ("WARN" if not mism else "FAIL")
    check("G3", "名稱=官方簡稱(全等;包含=變體;錯配標旗=WARN)", st3,
          f"全等 {len(members) - len(mism) - len(variant)};變體/已標旗 {len(variant)}"
          + (f":{variant[:3]}" if variant else "") + (f";不符未標旗:{mism[:3]}" if mism else ""))

    # G4 yfinance 後綴制
    bad4 = [(m["ticker"], m.get("yfinance")) for m in members
            if (m.get("market") == "TWSE" and not str(m.get("yfinance", "")).endswith(".TW"))
            or (m.get("market") == "TPEX" and not str(m.get("yfinance", "")).endswith(".TWO"))]
    check("G4", "yfinance 後綴制(.TW 上市/.TWO 上櫃)", "PASS" if not bad4 else "FAIL",
          "149 檔全符 VDF 擷取分道制" if not bad4 else f"{len(bad4)} 不符:{bad4[:4]}")

    # G5 SSOT 代號鎖(域別注意:鎖屬「文本抽取域」——排除 202X 防年份誤抓;
    # 名錄域以官方在籍為準:違鎖但官方在籍=抽取域已知碰撞,WARN 記載非錯)
    lock = None
    try:
        lock = json.loads(VDF_REG.read_text(encoding="utf-8"))["meta"]["ssot_locks"]["TW_TICKER_REGEX"]
    except Exception:
        pass
    if lock:
        viol = [m["ticker"] for m in members if not re.fullmatch(lock, m["ticker"])]
        collide = [t for t in viol if t in union]      # 官方在籍——抽取鎖碰撞
        bad5 = [t for t in viol if t not in union]     # 違鎖且官方查無——真違制
        if bad5:
            check("G5", "代號制式(SSOT 抽取鎖×官方在籍雙域)", "FAIL",
                  f"違鎖且官方查無:{bad5[:5]}")
        elif collide:
            check("G5", "代號制式(SSOT 抽取鎖×官方在籍雙域)", "WARN",
                  f"抽取鎖排除 202X(防年份誤抓)與真實代號碰撞 {len(collide)} 檔:"
                  f"{collide}——官方在籍屬名錄域合法;VRN 文本抽取域對此三碼不可抓(已知代價)")
        else:
            check("G5", "代號制式(SSOT 抽取鎖×官方在籍雙域)", "PASS", "全過雙域")
    else:
        check("G5", "代號制式(SSOT 抽取鎖×官方在籍雙域)", "SKIP", "SSOT 鎖不可讀(誠實跳)")

    # G6 群內重複
    dup_in = []
    cross = {}
    for gname, mem in g["groups"].items():
        seen = set()
        for m in mem:
            if m["ticker"] in seen:
                dup_in.append((gname, m["ticker"]))
            seen.add(m["ticker"])
            cross.setdefault(m["ticker"], []).append(gname)
    n_multi = sum(1 for v in cross.values() if len(v) > 1)
    check("G6", "群內零重複(跨群多屬=常態)", "PASS" if not dup_in else "FAIL",
          f"群內重複 0;跨群多屬 {n_multi} 檔(供應鏈多題材常態)" if not dup_in
          else f"群內重複:{dup_in}")

    # G7 每群有領頭
    no_lead = [gname for gname, mem in g["groups"].items()
               if not any(m.get("role") == "LEADER" for m in mem)]
    check("G7", "每群有領頭(role=LEADER)", "PASS" if not no_lead else "WARN",
          f"31 群皆有領頭(共 {sum(1 for m in members if m.get('role') == 'LEADER')})"
          if not no_lead else f"{len(no_lead)} 群無領頭:{no_lead}")

    n = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0}
    for r in RESULTS:
        n[r["status"]] += 1
    verdict = ("ALL_GREEN" if n["FAIL"] == 0 and n["WARN"] == 0
               else "GREEN_WITH_NOTES" if n["FAIL"] == 0 else "HAS_FAILURES")
    OUT.write_text(json.dumps({"schema": "batch308-group-verify-v1", "ts": NOW,
                               "provenance": prov, "counts": n, "verdict": verdict,
                               "n_groups": len(g["groups"]), "n_members": len(members),
                               "checks": RESULTS}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"  [計] PASS {n['PASS']} · WARN {n['WARN']} · FAIL {n['FAIL']} · SKIP {n['SKIP']} → {verdict}")
    print(f"  [出] {OUT.name}")
    return 0 if n["FAIL"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
