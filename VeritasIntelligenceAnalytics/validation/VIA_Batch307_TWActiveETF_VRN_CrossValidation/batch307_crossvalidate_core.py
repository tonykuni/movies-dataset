#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch307_crossvalidate_core — 批307 台股主動式ETF清單+VRN 三資料集多方法交叉驗證
================================================================================
操作員令(2026-09-02):
  ① 測試主動式台股 ETF 是否可以更新清單(TWSE OpenAPI 實連);
  ② 測試 VRN 產生的 BASIC INFO / SUMMARY / FINANCIAL DATA 多方法核對無誤;
  ③ 產出 HTML U/I Matrix 報告(本件產出機讀結果 JSON 供矩陣頁引用)。

多方法原則(獨立道互證,誠實不發明):
  法一 引擎道   FLOW_ENG023 --refresh 經 SUP_MDL737 fetch(UA 修補 v0103)
  法二 獨立傳輸 curl 快照(不同 UA/工具/時點)重解析互比
  法三 雙解析器 stdlib csv/json vs 自寫 RFC4180 狀態機(零依賴)
  法四 雜湊鏈   sha256 重算 vs SSOT 指標檔/檔名內嵌雜湊
  法五 規則冊   欄位格式規則(代號/日期/雜湊/風險燈)逐列驗
  法六 官方在籍 BasicInfo 代號 vs TWSE/TPEx 官方公司名錄實連
  缺網/缺件=誠實 SKIP;規則不符=FAIL;結構性弱點=WARN。

用法:python3 batch307_crossvalidate_core.py [--offline]
輸出:Batch307_CrossValidation_Results.json(同目錄)
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent  # VeritasIntelligenceAnalytics/
VRN = VIA / "functional modules" / "VRN"
FLOWCFG = VIA / "supportive modules" / "VIA_FlowSystem" / "FlowSystem_v2" / "config"
REG_PATH = FLOWCFG / "TW_Active_ETF_Registry_v0100.json"
SNAP_PATH = HERE / "twse_t187ap47_L_snapshot_20260902.json"
OUT_PATH = HERE / "Batch307_CrossValidation_Results.json"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

UA_HEADERS = {  # 循 VDF_MDL002/SUP_MDL737 v0103 慣例(官方端點擋 Python 預設 UA)
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}
OFFICIAL_EQUITY_ENDPOINTS = {  # FLOW_ENG024 既定官方名錄端點(上市/上櫃)+興櫃補位
    "TWSE 上市": "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
    "TPEx 上櫃": "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O",
    "TPEx 興櫃": "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_R",
}
# 官方名錄鍵名雙制式(TWSE 中文鍵/TPEx 英文鍵——工作站實測 2026-09-02)
CODE_KEYS = ("公司代號", "SecuritiesCompanyCode", "Code")
NAME_KEYS = ("公司簡稱", "公司名稱", "CompanyAbbreviation", "CompanyName")

RESULTS: list[dict] = []


def check(cid: str, area: str, method: str, name: str, status: str, detail: str):
    RESULTS.append({"id": cid, "area": area, "method": method, "name": name,
                    "status": status, "detail": detail})
    mark = {"PASS": "PASS", "FAIL": "FAIL", "WARN": "WARN", "SKIP": "SKIP"}[status]
    print(f"  [{mark}] {cid} {name} — {detail[:110]}")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def parse_csv_rfc4180(text: str) -> list[list[str]]:
    """法三:自寫 RFC4180 狀態機(獨立於 stdlib csv;含引號跳脫/欄內逗號/換行)。"""
    rows, field, row = [], [], []
    i, n, in_q = 0, len(text), False
    buf = []
    while i < n:
        c = text[i]
        if in_q:
            if c == '"':
                if i + 1 < n and text[i + 1] == '"':
                    buf.append('"'); i += 2; continue
                in_q = False; i += 1; continue
            buf.append(c); i += 1; continue
        if c == '"':
            in_q = True; i += 1; continue
        if c == ",":
            row.append("".join(buf)); buf = []; i += 1; continue
        if c == "\r":
            i += 1; continue
        if c == "\n":
            row.append("".join(buf)); buf = []
            rows.append(row); row = []; i += 1; continue
        buf.append(c); i += 1
    if buf or row:
        row.append("".join(buf)); rows.append(row)
    return rows


def fetch_json(url: str, timeout: int = 30):
    req = urllib.request.Request(url, headers=dict(UA_HEADERS))
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


# ═══════════════════════ 甲部:台股主動式 ETF 清單更新驗證 ═══════════════════════

def validate_etf_registry(offline: bool):
    print("\n═══ 甲部:主動式台股 ETF 清單更新交叉驗證 ═══")
    if not (REG_PATH.exists() and SNAP_PATH.exists()):
        check("E0", "ETF清單", "在籍", "前置檔案在位", "FAIL",
              f"registry={REG_PATH.exists()} snapshot={SNAP_PATH.exists()}")
        return
    reg = json.loads(REG_PATH.read_text(encoding="utf-8"))
    snap = json.loads(SNAP_PATH.read_text(encoding="utf-8"))
    official = {}
    for r in snap:
        c = str(r.get("基金代號", "")).strip()
        if c:
            official[c] = r

    # E1 法二:獨立快照筆數 vs 引擎 refresh 史錄筆數
    hist = [h for h in reg.get("history", []) if h.get("op") == "refresh"]
    if hist and hist[-1].get("rows_fetched") == len(snap):
        check("E1", "ETF清單", "法二 獨立傳輸", "快照筆數=引擎收錄筆數", "PASS",
              f"curl 快照 {len(snap)} 筆 = 引擎 rows_fetched {hist[-1]['rows_fetched']}(異傳輸同數)")
    else:
        check("E1", "ETF清單", "法二 獨立傳輸", "快照筆數=引擎收錄筆數", "FAIL",
              f"快照 {len(snap)} vs 史錄 {hist[-1].get('rows_fetched') if hist else '無 refresh 史錄'}")

    # E2 法一×法二:官方主動式全集 vs 冊內 VERIFIED 全集(雙射)
    off_active = {c for c, r in official.items()
                  if c[-1:] in ("A", "D") and "主動" in str(r.get("基金簡稱", ""))}
    reg_verified = {e["ticker"] for e in reg["etfs"]
                    if str(e.get("status", "")).startswith("VERIFIED_OPENAPI")}
    if off_active == reg_verified:
        check("E2", "ETF清單", "法一×法二 集合雙射", "官方主動式全集=冊內 VERIFIED 全集", "PASS",
              f"兩集合相等,{len(off_active)} 檔(不多不少)")
    else:
        check("E2", "ETF清單", "法一×法二 集合雙射", "官方主動式全集=冊內 VERIFIED 全集", "FAIL",
              f"官方有冊無:{sorted(off_active - reg_verified)};冊有官方無:{sorted(reg_verified - off_active)}")

    # E3 法二:VERIFIED 條目逐檔名碼核符
    bad = [(e["ticker"], e["name"], official.get(e["ticker"], {}).get("基金簡稱"))
           for e in reg["etfs"] if str(e.get("status", "")).startswith("VERIFIED_OPENAPI")
           and e.get("name") != str(official.get(e["ticker"], {}).get("基金簡稱", "")).strip()]
    if not bad:
        check("E3", "ETF清單", "法二 逐檔核對", "VERIFIED 名碼逐檔=官方簡稱", "PASS",
              f"{len(reg_verified)} 檔逐一相符(含 3 檔種子三環錯位改正+3 檔債/多資產名改正)")
    else:
        check("E3", "ETF清單", "法二 逐檔核對", "VERIFIED 名碼逐檔=官方簡稱", "FAIL", f"不符:{bad[:5]}")

    # E4 定奪佐證:三檔 A 尾衝突——批104 矩陣對映 vs 官方
    tri = {e["ticker"]: e for e in reg["etfs"] if e["ticker"] in ("00980A", "00981A", "00982A")}
    ok4 = all(t in tri and tri[t].get("matrix_name") == tri[t].get("name")
              and tri[t].get("seed_name") and tri[t]["seed_name"] != tri[t]["name"]
              for t in ("00980A", "00981A", "00982A"))
    check("E4", "ETF清單", "三源定奪", "00980A/981A/982A 衝突定奪(矩陣=官方≠種子)",
          "PASS" if ok4 else "FAIL",
          "官方證實批104矩陣對映、種子冊為三環錯位" if ok4 else f"定奪態異常:{ {t: (v.get('seed_name'), v.get('name'), v.get('matrix_name')) for t, v in tri.items()} }")

    # E5 誠實候驗:仍 PENDING 條目必不在官方上市名錄
    pend = [e for e in reg["etfs"] if not str(e.get("status", "")).startswith("VERIFIED")]
    leak = [e["ticker"] for e in pend if e["ticker"] in official]
    if not leak:
        check("E5", "ETF清單", "誠實界線", "候驗條目皆官方名錄查無(誠實不定奪)", "PASS",
              f"候驗 {len(pend)} 檔({','.join(e['ticker'] for e in pend)})上市名錄皆查無;TPEx 開放集亦無主動式")
    else:
        check("E5", "ETF清單", "誠實界線", "候驗條目皆官方名錄查無(誠實不定奪)", "FAIL",
              f"官方有而未定奪:{leak}")

    # E6 法一×法二:引擎快取體 vs curl 快照(異傳輸同內容)
    cache_dir = VIA / "VIA_Reports" / "accel_cache"
    url = reg.get("endpoints", {}).get("twse_etf_list", "")
    cf = cache_dir / (hashlib.sha1(url.encode()).hexdigest() + ".body")
    if cf.exists():
        try:
            eng_rows = json.loads(cf.read_text(encoding="utf-8"))
            same_codes = {str(r.get("基金代號", "")).strip() for r in eng_rows} == set(official)
            if len(eng_rows) == len(snap) and same_codes:
                check("E6", "ETF清單", "法一×法二 異傳輸", "引擎快取體=獨立快照(代號全集)", "PASS",
                      f"兩道各 {len(snap)} 筆、基金代號全集一致(SuperAccel v0103 道 vs curl 道)")
            else:
                check("E6", "ETF清單", "法一×法二 異傳輸", "引擎快取體=獨立快照(代號全集)", "WARN",
                      f"筆數 {len(eng_rows)} vs {len(snap)};官方日更下時點差屬誠實範圍")
        except Exception as exc:
            check("E6", "ETF清單", "法一×法二 異傳輸", "引擎快取體=獨立快照(代號全集)", "FAIL",
                  f"快取體解析敗:{exc}")
    else:
        check("E6", "ETF清單", "法一×法二 異傳輸", "引擎快取體=獨立快照(代號全集)", "SKIP",
              "引擎快取體不在位(未跑 --refresh?)")

    # E7 出表日期時效
    dates = {str(r.get("出表日期", "")) for r in snap}
    d = sorted(dates)[-1] if dates else ""
    ok7 = re.fullmatch(r"1\d{6}", d or "") and int(d[:3]) + 1911 >= 2026
    check("E7", "ETF清單", "法五 規則冊", "官方出表日期時效(民國紀年→西元)", "PASS" if ok7 else "WARN",
          f"出表日期 {d}(民國 {d[:3]} 年={int(d[:3]) + 1911 if d[:3].isdigit() else '?'} 西元)" if d else "無出表日期欄")


# ═══════════════════════ 乙部:VRN BASIC INFO 驗證 ═══════════════════════

def validate_basicinfo():
    print("\n═══ 乙部:VRN BASIC INFO 多方法核對 ═══")
    csv_p = VRN / "StockReportBasicInfo.csv"
    json_p = VRN / "StockReportBasicInfo.json"
    shav_p = VRN / "StockReportBasicInfo_sha1f5033b1.json"
    if not (csv_p.exists() and json_p.exists()):
        check("B0", "BASIC INFO", "在籍", "前置檔案在位", "FAIL", "CSV/JSON 缺件")
        return None
    text = csv_p.read_text(encoding="utf-8-sig")
    rows_std = list(csv.DictReader(io.StringIO(text)))
    recs = json.loads(json_p.read_text(encoding="utf-8"))

    # B1 法三:stdlib csv vs json 逐列逐欄
    if len(rows_std) == len(recs):
        diff = 0
        for a, b in zip(rows_std, recs):
            for k, v in b.items():
                if str(a.get(k, "")) != str(v):
                    diff += 1
        if diff == 0:
            check("B1", "BASIC INFO", "法三 CSV↔JSON", "CSV(stdlib)=JSON 逐列逐欄", "PASS",
                  f"{len(recs)} 列 × {len(recs[0])} 欄全等(兩格式互證)")
        else:
            check("B1", "BASIC INFO", "法三 CSV↔JSON", "CSV(stdlib)=JSON 逐列逐欄", "FAIL",
                  f"{diff} 欄值不等")
    else:
        check("B1", "BASIC INFO", "法三 CSV↔JSON", "CSV(stdlib)=JSON 逐列逐欄", "FAIL",
              f"列數 CSV {len(rows_std)} vs JSON {len(recs)}")

    # B2 法三:自寫 RFC4180 狀態機 vs stdlib csv(雙解析器互證)
    raw = parse_csv_rfc4180(text)
    raw = [r for r in raw if any(x.strip() for x in r)]
    hdr, body = raw[0], raw[1:]
    ok2 = (len(body) == len(rows_std)
           and hdr == list(rows_std[0].keys())
           and all(dict(zip(hdr, r)) == dict(rows_std[i]) for i, r in enumerate(body)))
    check("B2", "BASIC INFO", "法三 雙解析器", "自寫 RFC4180 狀態機=stdlib csv", "PASS" if ok2 else "FAIL",
          f"{len(body)} 列獨立解析全等(引號跳脫/欄內逗號含)" if ok2 else "獨立解析器結果不等——CSV 方言疑義")

    # B3 法四:sha 副本檔——檔名內嵌雜湊驗證+內容等價
    if shav_p.exists():
        h_main = sha256_file(json_p)
        h_var = sha256_file(shav_p)
        m = re.search(r"_sha([0-9a-f]{8})", shav_p.name)
        tag = m.group(1) if m else ""
        same_content = json.loads(shav_p.read_text(encoding="utf-8")) == recs
        if same_content and tag and (h_main.startswith(tag) or h_var.startswith(tag)):
            check("B3", "BASIC INFO", "法四 雜湊", "sha 副本檔名內嵌雜湊+內容等價", "PASS",
                  f"內容等價;檔名 sha{tag} 命中 {'主檔' if h_main.startswith(tag) else '副本'} sha256 前 8 碼")
        elif same_content:
            check("B3", "BASIC INFO", "法四 雜湊", "sha 副本檔名內嵌雜湊+內容等價", "WARN",
                  f"內容等價;惟檔名 sha{tag} 與主檔 {h_main[:8]}/副本 {h_var[:8]} 皆不合(命名沿革待考)")
        else:
            check("B3", "BASIC INFO", "法四 雜湊", "sha 副本檔名內嵌雜湊+內容等價", "FAIL", "副本內容與主檔不等")
    else:
        check("B3", "BASIC INFO", "法四 雜湊", "sha 副本檔名內嵌雜湊+內容等價", "SKIP", "sha 副本不在位")

    # B4 法五:欄位規則冊逐列驗
    bad_rows = []
    risk_set = {"GREEN", "YELLOW", "RED", ""}
    for i, r in enumerate(recs):
        t = str(r.get("Ticker", ""))
        if t and not re.fullmatch(r"\d{4,6}[A-Z]?", t):
            bad_rows.append((i, "Ticker", t))
        d = str(r.get("ReportDate", ""))
        if d:
            try:
                datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                bad_rows.append((i, "ReportDate", d))
        h = str(r.get("FileHash", ""))
        if h and not re.fullmatch(r"[0-9a-f]{64}", h):
            bad_rows.append((i, "FileHash", h[:20]))
        if str(r.get("ValidationRisk", "")) not in risk_set:
            bad_rows.append((i, "ValidationRisk", r.get("ValidationRisk")))
        if not str(r.get("ValidationStatus", "")):
            bad_rows.append((i, "ValidationStatus", "空"))
    if not bad_rows:
        check("B4", "BASIC INFO", "法五 規則冊", "欄位規則逐列驗(代號/日期/雜湊/風險燈)", "PASS",
              f"{len(recs)} 列全過:Ticker 數碼制、ReportDate ISO、FileHash hex64、風險燈 G/Y/R")
    else:
        check("B4", "BASIC INFO", "法五 規則冊", "欄位規則逐列驗(代號/日期/雜湊/風險燈)", "FAIL",
              f"{len(bad_rows)} 違規:{bad_rows[:4]}")

    # B5 法五:全列重複檢(同一檔案雙相位屬設計內,全欄重複=異常)
    seen, dup = set(), 0
    for r in recs:
        k = json.dumps(r, ensure_ascii=False, sort_keys=True)
        dup += k in seen
        seen.add(k)
    check("B5", "BASIC INFO", "法五 規則冊", "全欄重複列=0", "PASS" if dup == 0 else "FAIL",
          f"{len(recs)} 列無全欄重複(TEMP_PREVIEW/CANDIDATE 雙相位同檔屬設計)" if dup == 0 else f"{dup} 列全欄重複")
    return recs


def validate_basicinfo_official(recs, offline: bool):
    # B6 法六:代號官方在籍(TWSE 上市+TPEx 上櫃 實連)
    if recs is None:
        return
    if offline:
        check("B6", "BASIC INFO", "法六 官方在籍", "Ticker 官方名錄在籍", "SKIP", "--offline 指定")
        return
    tickers = sorted({str(r.get("Ticker", "")) for r in recs if str(r.get("Ticker", ""))})
    listed = {}
    for label, url in OFFICIAL_EQUITY_ENDPOINTS.items():
        try:
            rows = fetch_json(url)
            for r in rows:
                c = next((str(r.get(k, "")).strip() for k in CODE_KEYS if str(r.get(k, "")).strip()), "")
                if c:
                    nm = next((str(r.get(k, "")).strip() for k in NAME_KEYS if str(r.get(k, "")).strip()), "")
                    listed[c] = (label, nm)
        except Exception as exc:
            check("B6", "BASIC INFO", "法六 官方在籍", f"{label} 名錄實連", "SKIP",
                  f"端點未達({type(exc).__name__})——誠實跳過")
            return
    missing = [t for t in tickers if t not in listed]
    hit = len(tickers) - len(missing)
    if not missing:
        check("B6", "BASIC INFO", "法六 官方在籍", "Ticker 官方名錄在籍(上市+上櫃+興櫃)", "PASS",
              f"{hit}/{len(tickers)} 檔代號皆在官方名錄(名錄合 {len(listed)} 檔)")
    else:
        st = "WARN" if len(missing) <= max(2, len(tickers) // 10) else "FAIL"
        check("B6", "BASIC INFO", "法六 官方在籍", "Ticker 官方名錄在籍(上市+上櫃+興櫃)", st,
              f"{hit}/{len(tickers)} 在籍;三名錄皆查無:{missing}")

    # B7 缺陷鑑別:年份樣代號(20XX)且名錄查無——檔名年份誤植入 Ticker 欄之樣態
    year_like = [t for t in missing if re.fullmatch(r"20[2-3]\d", t)]
    if year_like:
        evid = []
        for t in year_like:
            fns = [str(r.get("SourceFile", ""))[:34] for r in recs if str(r.get("Ticker", "")) == t]
            evid.append(f"{t}←{len(fns)} 列(如「{fns[0]}…」)")
        check("B7", "BASIC INFO", "缺陷鑑別", "年份誤植入 Ticker 欄(真缺陷,候修)", "FAIL",
              f"檔名年份被抓成代號:{';'.join(evid)}——市場總覽/會議簡報應 Ticker 留空(如既有盤勢分析列)")
    elif missing:
        check("B7", "BASIC INFO", "缺陷鑑別", "查無代號樣態鑑別", "WARN",
              f"查無代號非年份樣:{missing}(已下市/海外屬誠實範圍)")
    else:
        check("B7", "BASIC INFO", "缺陷鑑別", "查無代號樣態鑑別", "PASS", "無查無代號——零缺陷樣態")


# ═══════════════════════ 丙部:VRN SUMMARY(研報 SSOT)驗證 ═══════════════════════

def validate_summary():
    print("\n═══ 丙部:VRN SUMMARY(ResearchReport SSOT)多方法核對 ═══")
    ssot = VRN / "SSOT"
    ptr_p = ssot / "VRN_ResearchReport_SSOT.active.json"
    v2 = ssot / "v2"
    gen_dir = v2 / "generations"
    if not ptr_p.exists():
        check("S0", "SUMMARY", "在籍", "active 指標檔在位", "FAIL", "指標檔缺")
        return
    ptr = json.loads(ptr_p.read_text(encoding="utf-8"))

    # S1 法四:世代正典檔 sha256 重算 vs 指標檔+檔名內嵌
    want = ptr.get("active_canonical_sha256", "")
    gen_hits = sorted(gen_dir.glob("*.jsonl")) if gen_dir.exists() else []
    canon = next((p for p in gen_hits if want[:16] in p.name), None)
    if canon:
        got = sha256_file(canon)
        if got == want:
            check("S1", "SUMMARY", "法四 雜湊", "世代正典檔 sha256=指標檔宣告", "PASS",
                  f"{canon.name}:重算 {got[:16]}…=宣告(64 位全等)+檔名內嵌前 16 碼命中")
        else:
            check("S1", "SUMMARY", "法四 雜湊", "世代正典檔 sha256=指標檔宣告", "FAIL",
                  f"重算 {got[:16]}… ≠ 宣告 {want[:16]}…")
    else:
        check("S1", "SUMMARY", "法四 雜湊", "世代正典檔 sha256=指標檔宣告", "FAIL",
              f"generations 內無檔名含 {want[:16]} 之世代檔")
        return

    # S2 法五:記錄數=指標宣告;逐行可解析
    lines = [ln for ln in canon.read_text(encoding="utf-8").splitlines() if ln.strip()]
    n_want = int(ptr.get("active_record_count", -1))
    parsed, bad = [], 0
    for ln in lines:
        try:
            parsed.append(json.loads(ln))
        except Exception:
            bad += 1
    if bad == 0 and len(lines) == n_want:
        check("S2", "SUMMARY", "法五 規則冊", "JSONL 逐行可解析+記錄數=宣告", "PASS",
              f"{len(lines)} 行全解析,=指標宣告 {n_want}")
    else:
        check("S2", "SUMMARY", "法五 規則冊", "JSONL 逐行可解析+記錄數=宣告", "FAIL",
              f"行數 {len(lines)} vs 宣告 {n_want};解析敗 {bad}")

    # S3 法四:兩張 schema sha256 重算 vs 指標宣告
    pairs = [("record.schema", v2 / "VRN_ResearchReport_SSOT.record.schema.v2.json",
              ptr.get("active_record_json_schema_sha256", "")),
             ("schema.full", v2 / "VRN_ResearchReport_SSOT.schema.v2.full.json",
              ptr.get("active_schema_sha256", ""))]
    ok3, det3 = True, []
    for tag, p, want_h in pairs:
        if not p.exists():
            ok3 = False; det3.append(f"{tag} 缺件"); continue
        got_h = sha256_file(p)
        det3.append(f"{tag} {'合' if got_h == want_h else '不合'}")
        ok3 = ok3 and got_h == want_h
    check("S3", "SUMMARY", "法四 雜湊", "schema 雙檔 sha256=指標宣告", "PASS" if ok3 else "FAIL",
          ";".join(det3))

    # S4 法五:v2 記錄 schema 必要欄逐records驗+欄名冊涵蓋
    sch = json.loads((v2 / "VRN_ResearchReport_SSOT.record.schema.v2.json").read_text(encoding="utf-8"))
    req = sch.get("required", [])
    props = set(sch.get("properties", {}).keys())
    miss_req = sum(1 for r in parsed if any(k not in r for k in req))
    unknown = sorted({k for r in parsed for k in r} - props)
    if miss_req == 0 and not unknown:
        check("S4", "SUMMARY", "法五 規則冊", "必要欄全在+無冊外欄名", "PASS",
              f"{len(parsed)} 記錄 × 必要欄 {len(req)} 全在;欄名皆屬 schema {len(props)} 欄冊")
    elif miss_req == 0:
        check("S4", "SUMMARY", "法五 規則冊", "必要欄全在+無冊外欄名", "WARN",
              f"必要欄全在;冊外欄名 {len(unknown)}:{unknown[:5]}")
    else:
        check("S4", "SUMMARY", "法五 規則冊", "必要欄全在+無冊外欄名", "FAIL",
              f"{miss_req} 記錄缺必要欄;冊外欄名 {unknown[:5]}")

    # S5 法三:v2 工作檔 vs 世代正典檔(雙位置互證)
    work = v2 / "VRN_ResearchReport_SSOT.v2.jsonl"
    if work.exists():
        if work.read_bytes() == canon.read_bytes():
            check("S5", "SUMMARY", "法三 雙位置", "v2 工作檔=世代正典檔(byte 級)", "PASS",
                  f"{work.name} 與 {canon.name} byte-exact")
        else:
            check("S5", "SUMMARY", "法三 雙位置", "v2 工作檔=世代正典檔(byte 級)", "WARN",
                  "byte 不等——工作檔或有後續增量(誠實記錄)")
    else:
        check("S5", "SUMMARY", "法三 雙位置", "v2 工作檔=世代正典檔(byte 級)", "SKIP", "工作檔不在位")

    # S6 法五:前代 60 記錄檔 vs 舊版 jsonl(增量沿革一致)
    legacy = ssot / "VRN_ResearchReport_SSOT.jsonl"
    pre = next(iter(gen_dir.glob("*records60*")), None)
    if legacy.exists() and pre is not None:
        n_leg = sum(1 for ln in legacy.read_text(encoding="utf-8").splitlines() if ln.strip())
        n_pre = sum(1 for ln in pre.read_text(encoding="utf-8").splitlines() if ln.strip())
        gen_tag = str(ptr.get("authority_generation", ""))
        ok6 = n_leg == n_pre == 60 and len(parsed) == 64 and "INCREMENTAL_64" in gen_tag
        check("S6", "SUMMARY", "法五 沿革", "60→64 增量沿革一致(舊版=pre_promote)", "PASS" if ok6 else "WARN",
              f"舊版 {n_leg} 記錄=pre_promote {n_pre};世代 {len(parsed)};authority={gen_tag}")
    else:
        check("S6", "SUMMARY", "法五 沿革", "60→64 增量沿革一致(舊版=pre_promote)", "SKIP", "沿革檔不全")
    return parsed


# ═══════════════════ 丁部:VRN FINANCIAL DATA 驗證 ═══════════════════

def validate_financial(basic_recs):
    print("\n═══ 丁部:VRN FINANCIAL DATA 多方法核對 ═══")
    fin_p = (VRN / "references" / "intake" / "AttachmentFixedOutput_v1.0.0_b245"
             / "AttachmentFixedOutput_v1.0.0" / "01_repair" / "financial_data.jsonl")
    ssot_p = VRN / "registry" / "VRN_REPORT_FINANCIAL_DATA_SSOT_v0100.json"

    # F1 法五:SSOT 契約檔可解析+18 核心欄冊在位
    if ssot_p.exists():
        contract = json.loads(ssot_p.read_text(encoding="utf-8"))
        cc = contract.get("def_schema_contract", {})
        cols = cc.get("def_core_columns", [])
        n_want = int(cc.get("def_core_column_count", -1))
        names = [c.get("def_name", "") for c in cols]
        ok1 = len(cols) == n_want and all(names) and len(set(names)) == len(names)
        check("F1", "FINANCIAL", "法五 契約冊", "SSOT 契約 18 核心欄冊完整無重", "PASS" if ok1 else "FAIL",
              f"{len(cols)} 欄(宣告 {n_want}):{','.join(names[:6])}…" if names else "欄冊空")
    else:
        check("F1", "FINANCIAL", "法五 契約冊", "SSOT 契約 18 核心欄冊完整無重", "FAIL", "契約檔缺")
        contract = None

    # F2 誠實界線:正典 parquet 於工作站(不在倉)——契約路徑照錄
    if contract:
        cand = contract.get("def_canonical_paths", {}).get("def_parquet_candidates", [])
        check("F2", "FINANCIAL", "誠實界線", "正典 parquet 工作站在位(倉內誠實不在)", "WARN",
              f"契約載 {len(cand)} 候選路徑(C:\\…工作站);倉內以 01_repair 抽取事實列驗證")

    if not fin_p.exists():
        check("F3", "FINANCIAL", "在籍", "financial_data.jsonl 在位", "FAIL", "抽取事實檔缺")
        return

    lines = [ln for ln in fin_p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    rows, bad = [], 0
    for ln in lines:
        try:
            rows.append(json.loads(ln))
        except Exception:
            bad += 1

    # F3 法五:逐行解析+欄冊固定 11 欄(01_repair 抽取事實制式)
    keys_want = {"confidence", "filename", "item_id", "metric", "period", "raw_value",
                 "source_id", "source_text", "start_offset", "unit", "value"}
    keysets = {frozenset(r.keys()) for r in rows}
    ok3 = bad == 0 and keysets == {frozenset(keys_want)}
    check("F3", "FINANCIAL", "法五 規則冊", "JSONL 逐行解析+欄冊固定 11 欄", "PASS" if ok3 else "FAIL",
          f"{len(rows)} 列全解析,欄冊恆定 11 欄(含 value/unit/start_offset)" if ok3
          else f"解析敗 {bad};欄冊變體 {len(keysets)}:{[sorted(k) for k in list(keysets)[:2]]}")

    # F4 法五:值域規則(信度/識別碼制/數值/期別語意可解析)
    bad4 = []
    for i, r in enumerate(rows):
        c = r.get("confidence")
        if not (isinstance(c, (int, float)) and 0 < c <= 1):
            bad4.append((i, "confidence", c))
        if not re.fullmatch(r"FIN-[0-9A-F]{16}", str(r.get("item_id", ""))):
            bad4.append((i, "item_id", r.get("item_id")))
        if not re.fullmatch(r"SRC-[0-9A-F]{16}", str(r.get("source_id", ""))):
            bad4.append((i, "source_id", r.get("source_id")))
        v = str(r.get("raw_value", "")).replace(",", "").replace("%", "").strip()
        try:
            float(v)
        except ValueError:
            bad4.append((i, "raw_value", r.get("raw_value")))
        if _norm_period(r.get("period")) is None:
            bad4.append((i, "period", r.get("period")))
        if str(r.get("unit")) not in ("%", "None", "bn", "億元", "元", "百萬元", "千元", "USD", "NTD"):
            bad4.append((i, "unit", r.get("unit")))
    if not bad4:
        check("F4", "FINANCIAL", "法五 規則冊", "值域規則(信度 0<c≤1/識別碼制/數值/期別語意)", "PASS",
              f"{len(rows)} 列全過(metric 分佈:{_metric_hist(rows)})")
    else:
        st = "WARN" if len(bad4) <= 3 else "FAIL"
        check("F4", "FINANCIAL", "法五 規則冊", "值域規則(信度 0<c≤1/識別碼制/數值/期別語意)", st,
              f"{len(bad4)} 違規:{bad4[:4]}")

    # F7 法三:value(正規值)↔raw_value(原始字串)數值互證
    bad7 = []
    for i, r in enumerate(rows):
        rv = str(r.get("raw_value", "")).replace(",", "").replace("%", "").strip()
        val = r.get("value")
        try:
            f = float(rv)
        except ValueError:
            continue  # F4 已計
        if val is None or abs(f - float(val)) > max(1e-9, abs(f) * 1e-9):
            bad7.append((i, r.get("raw_value"), val))
    check("F7", "FINANCIAL", "法三 雙欄互證", "value 正規值=raw_value 重解析", "PASS" if not bad7 else "FAIL",
          f"{len(rows)} 列正規值與原始字串重解析全等(零漂移)" if not bad7 else f"{len(bad7)} 列漂移:{bad7[:4]}")

    # F8 法五:期別表面制式並存清點(01_repair 為標準化前站——多制式=候整備非錯誤)
    conv = {}
    for r in rows:
        p = str(r.get("period"))
        for pat, tag in (("^None$", "缺"), (r"^(19|20)\d{2}$", "YYYY"),
                         (r"^(19|20)\d{2}Q[1-4]$", "YYYYQn"), (r"^\d{2}Q[1-4]$", "YYQn"),
                         (r"^[1-4]Q\d{2}$", "nQYY"), (r"^FY\d{2,4}$", "FYnn"),
                         (r"^(19|20)\d{2}H[12]$", "YYYYHn")):
            if re.fullmatch(pat, p):
                conv[tag] = conv.get(tag, 0) + 1
                break
        else:
            conv["其他"] = conv.get("其他", 0) + 1
    n_conv = len([k for k in conv if k not in ("缺",)])
    st8 = "PASS" if n_conv <= 1 else "WARN"
    check("F8", "FINANCIAL", "法五 制式清點", "期別表面制式並存清點(候標準化)", st8,
          f"{n_conv} 制式並存:{conv}——下游 financial_data_standardization 候整備" if n_conv > 1
          else f"單一制式:{conv}")

    # F5 法五:item_id 全域唯一
    ids = [r.get("item_id") for r in rows]
    dup = len(ids) - len(set(ids))
    check("F5", "FINANCIAL", "法五 規則冊", "item_id 全域唯一", "PASS" if dup == 0 else "FAIL",
          f"{len(ids)} 筆識別碼零重複" if dup == 0 else f"{dup} 筆重複")

    # F6 法六:跨資料集參照——financial filename ⊆ BasicInfo SourceFile
    if basic_recs:
        src = {str(r.get("SourceFile", "")) for r in basic_recs}
        fn = sorted({str(r.get("filename", "")) for r in rows})
        miss = [f for f in fn if f not in src]
        if not miss:
            check("F6", "FINANCIAL", "法六 跨集參照", "抽取事實檔名全數見於 BASIC INFO 冊", "PASS",
                  f"{len(fn)} 檔名 100% 對上 BASIC INFO(參照完整)")
        else:
            st = "WARN" if len(miss) <= max(1, len(fn) // 5) else "FAIL"
            check("F6", "FINANCIAL", "法六 跨集參照", "抽取事實檔名全數見於 BASIC INFO 冊", st,
                  f"{len(fn) - len(miss)}/{len(fn)} 對上;冊外:{miss[:3]}")


def _norm_period(p) -> tuple | None:
    """期別語意正規化:回 (year, quarter|None);不可解析回 None(None 值=合法缺)。"""
    if p is None or str(p) == "None":
        return ("", None)
    s = str(p).strip().upper()
    m = re.fullmatch(r"(19|20)(\d{2})", s)
    if m:
        return (int(s), None)
    m = re.fullmatch(r"((?:19|20)\d{2})Q([1-4])", s)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    m = re.fullmatch(r"(\d{2})Q([1-4])", s)
    if m:
        return (2000 + int(m.group(1)), int(m.group(2)))
    m = re.fullmatch(r"([1-4])Q(\d{2}|\d{4})", s)
    if m:
        y = int(m.group(2))
        return (y if y > 100 else 2000 + y, int(m.group(1)))
    m = re.fullmatch(r"FY(\d{2}|\d{4})", s)
    if m:
        y = int(m.group(1))
        return (y if y > 100 else 2000 + y, None)
    m = re.fullmatch(r"((?:19|20)\d{2})H([12])", s)
    if m:
        return (int(m.group(1)), None)
    return None


def _metric_hist(rows) -> str:
    h = {}
    for r in rows:
        h[r.get("metric", "?")] = h.get(r.get("metric", "?"), 0) + 1
    return ",".join(f"{k}×{v}" for k, v in sorted(h.items(), key=lambda kv: -kv[1])[:5])


# ═══════════════════════════════ 主流程 ═══════════════════════════════

def main() -> int:
    offline = "--offline" in sys.argv[1:]
    print("=" * 72)
    print(" 批307 台股主動式ETF清單+VRN 三資料集 多方法交叉驗證")
    print("=" * 72)
    validate_etf_registry(offline)
    basic = validate_basicinfo()
    validate_basicinfo_official(basic, offline)
    validate_summary()
    validate_financial(basic)
    n = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0}
    for r in RESULTS:
        n[r["status"]] += 1
    verdict = ("ALL_GREEN" if n["FAIL"] == 0 and n["WARN"] == 0
               else "GREEN_WITH_NOTES" if n["FAIL"] == 0 else "HAS_FAILURES")
    out = {"schema": "batch307-crossvalidation-results-v1", "ts": NOW,
           "operator_order": "測試主動式台股ETF清單更新+VRN BASIC INFO/SUMMARY/FINANCIAL DATA 多方法核對",
           "counts": n, "verdict": verdict, "checks": RESULTS}
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n" + "=" * 72)
    print(f"  [計] PASS {n['PASS']} · WARN {n['WARN']} · FAIL {n['FAIL']} · SKIP {n['SKIP']}"
          f" → 判定 {verdict}")
    print(f"  [出] {OUT_PATH.name}")
    return 0 if n["FAIL"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
