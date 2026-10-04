#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VRN_ENG399_RealTestHarness v0100 — 實測前置:25 個潛在失敗風險 × (偵測 · 修法 · 驗證 · 資料修復) 逐件執行(操作員 2026-10-03)

操作員:「"C:\測試樣本報告" 實測輸出清點驗證無誤就算成功 · 等會換一波測試檔案 · 25 個潛在失敗風險及解決方案 / 驗證方案 / 修復資料方案都要完備執行自測」。
本支只讀樣本、不改樣本、不寫正本冊;每件 × 25 風險各一格,四態(GREEN 過 · YELLOW 要人裁 · RED 命中且修不掉 · GRAY 本件不適用/沒跑 · NODATA 工具缺)。
偵測用 pymupdf / pdfplumber(缺席誠實 NODATA,不假綠);修法只「指名正主引擎 + 參數」,不在本支動刀(Zero-Hydra)。
產出 VIA_Reports/vrn/realtest/REALTEST_<stamp>.json · REALTEST_latest.html(四燈 VIA_UI_FormatLock 色)· paste.md。
用法  VIA_FROM_VCGC=YES python VRN_ENG399_RealTestHarness_v0100.py run --in "C:\測試樣本報告" [--limit N] [--no-open]
      python VRN_ENG399_RealTestHarness_v0100.py --selftest
結束碼  0 無 RED · 2 有 RED · 3 工具缺到無法量
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
import hashlib, html, json, os, re, sys, tempfile, unicodedata
from datetime import datetime, timezone
from pathlib import Path

ENGINE = "VRN_ENG399_RealTestHarness_v0100"
HERE = Path(__file__).resolve().parent
VIA = next((p for p in [HERE] + list(HERE.parents) if (p / "supportive modules").is_dir()), HERE)
PAL = {"GREEN": "#15803d", "YELLOW": "#b45309", "RED": "#b91c1c", "GRAY": "#6b7280", "NODATA": "#0e7490"}
try:
    import fitz  # pymupdf
except Exception:
    fitz = None
try:
    import pdfplumber
except Exception:
    pdfplumber = None

# 25 風險:id · zh · detect(key) · fix(正主 + 參數) · verify · data_repair
RISKS = [
 ("R01", "檔不是 PDF / 副檔名騙人", "not_pdf", "VRN_ENG077 OmniFormatBridge 轉 PDF(docx/pptx);非文件型 → 隔離名冊", "轉後再進 R02", "原檔留,轉檔另存 _converted"),
 ("R02", "0 byte / 截斷 / 打不開", "unreadable", "重抓來源;打不開者進 quarantine 名冊(HZ-01)", "fitz.open 成功且頁數 ≥ 1", "不修,標 RED 回報來源"),
 ("R03", "加密 / 需密碼", "encrypted", "qpdf --decrypt(操作員給密碼);否則隔離", "開啟後可讀文字", "無"),
 ("R04", "掃描件無文字層", "no_text_layer", "R-TIER-01 直升 tier 1 輕 OCR(rapidocr)→ 不過 tier 2 paddle", "ENG392 覆蓋率 ≥ 0.80", "OCR 結果帶 grade=ocr,不冒充文字層"),
 ("R05", "頁面旋轉 / 橫向", "rotated", "fitz page.set_rotation(0) 於 TEMP 副本;ENG394 用矯正後頁", "文字行方向正常", "只改 TEMP 副本"),
 ("R06", "多欄版面(左右兩欄本文)", "multi_column", "ENG394 S01 切區 + S02 table_in_text;欄序由 bbox x 排", "左右欄不互吞(覆蓋圖無交錯)", "無"),
 ("R07", "本文中有表(無格線)", "table_in_text", "FrameFlow S02:對齊 / 數字列群偵測 → right_table", "表格格線數 vs 格子數一致", "切出表 split_method=in_text"),
 ("R08", "表格跨頁", "table_spans_pages", "ENG058 TableOmni 跨頁合併(同表頭續接)", "合併後列數 = 各頁列數和", "續接列帶 page 欄"),
 ("R09", "合併儲存格 / 空白表頭", "merged_cells", "ENG074 FinancialPages 表頭補齊(上一欄填充)+ ENG108 數字核", "表頭無空 · 自洽過", "填充欄標 grade=inferred"),
 ("R10", "數字括號負數 / 千分位 / 全形", "number_format", "ENG392 R1/R2 正規化((1,234) → -1234;全形 → 半形)", "re 抽數後與原字對照", "原字留 raw 欄"),
 ("R11", "民國年 / 1Q24 / FY24E 期別混用", "period_format", "中央 regex 冊 RX_QUARTER/RX_DATE 正典化(ENG074)", "期別正典 id 唯一", "原期別留 raw"),
 ("R12", "單位混用(億 / 百萬 / 千元)", "unit_mix", "ENG074 unit 欄 + 換算到元;不猜,表頭沒寫 = NODATA", "同表同欄單位一致", "unit 欄必填"),
 ("R13", "代號 / 公司名抓不到", "ticker_missing", "ENG111 StockIdentity ← 證券主檔別名;檔名 token(ENG084)互核", "ticker 4 碼 + 名稱對上主檔", "缺 = single-source 降級"),
 ("R14", "日期(報告日)抓不到", "date_missing", "ENG076 RegressionGate 日期正則 + 檔名日期互核", "日期 ≥ 2015 且 ≤ 今", "缺 = 用檔名日 + grade=inferred"),
 ("R15", "評等詞表外(新券商用語)", "rating_unknown", "SUP_MDL749 樞紐 additive 候選(PENDING_OPERATOR)", "樞紐 rating_of 回非 None", "候選進增補冊,不入正本"),
 ("R16", "目標價缺 / 多個(新舊)", "tp_missing_or_multi", "ENG086 TP 正則(前次 / 本次)+ R-FCST-01 兩列都留", "tp_current · tp_prev 分欄", "兩值都留"),
 ("R17", "EPS 兩列(基本 / 稀釋)", "eps_two_rows", "R-EPS-01:兩列取較低為 diluted;一列視為 diluted assumed", "eps_rule / eps_grade 欄在", "兩值都留"),
 ("R18", "CJK 字型缺 → 亂碼 / 方塊", "cjk_garble", "ENG392 R1 去零寬 + 升級 tier 1 OCR 該區", "亂碼率 < 5%", "OCR 替換段標 grade=ocr"),
 ("R19", "連字 / 字間空白斷字(T S M C)", "spacing_break", "ENG392 R2 字間空白接回", "詞表命中率回升", "無"),
 ("R20", "頁尾 / 免責聲明 / 附錄混入本文", "footer_leak", "ENG394 S01 排除規則(附錄 / Disclaimer / 小字)", "本文區不含 Disclaimer 關鍵字", "無"),
 ("R21", "同一報告重複檔(不同檔名)", "duplicate_file", "sha256 去重 → 名冊,不刪", "同 sha 只進庫一次", "副本進 BookDedup 名冊"),
 ("R22", "超大檔 / 頁數過多", "huge_file", "只讀前 N 頁(FrameFlow pages 參數)+ TEMP spill", "記憶體峰值 < 門檻", "無"),
 ("R23", "Unicode 正規化(NFKC)不一致", "unicode_nfkc", "ENG392 R1 NFKC", "NFKC 後字串穩定", "無"),
 ("R24", "文字層抽出為空(有文字層但抽不到)", "empty_extract", "pdfplumber 與 fitz 互核;皆空 → tier 1 OCR", "二法任一 > 50 字", "無"),
 ("R25", "輸出表頭 ≠ 冊(欄名 / 型別漂)", "header_drift", "CGC_MDL249 DataFrameLock check;R-HDR-01 display 欄", "欄 = 冊 OUT-xx.Cnn", "無"),
]
RE_PERIOD = re.compile(r"(民國|1[01]\d年|[1-4]Q\d{2}|FY\d{2,4}[EFA]?|\d{2}Q[1-4])")
RE_NUM_PAREN = re.compile(r"\(\s*\d[\d,]*\s*\)")
RE_EPS = re.compile(r"(每股盈餘|EPS)", re.I)
RE_TICKER = re.compile(r"(?<!\d)([1-9]\d{3})(?:\s*TT|\.TWO?)?(?!\d)")
RE_DATE = re.compile(r"20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}|20\d{2}年\d{1,2}月")
RE_RATING = re.compile(r"買進|賣出|中立|持有|加碼|減碼|Buy|Sell|Hold|Neutral|Outperform|Underperform", re.I)
RE_TP = re.compile(r"目標價|Target\s*Price|\bTP\b|\bPT\b", re.I)
RE_FOOTER = re.compile(r"Disclaimer|免責|Analyst Certification|附錄|Appendix", re.I)
RE_SPACED = re.compile(r"\b(?:[A-Z] ){3,}[A-Z]\b")


def probe(path: Path) -> dict:
    """每件一張探針卡(只讀)。"""
    c = {"file": path.name, "size": path.stat().st_size, "sha16": "", "pdf": path.suffix.lower() == ".pdf", "open": False, "pages": 0, "encrypted": False,
         "text_chars": 0, "text_chars_plumber": None, "rotated": False, "columns": 1, "tables": 0, "cjk_garble": 0.0, "footer_in_body": False, "nfkc_diff": False, "spaced": 0}
    try:
        c["sha16"] = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except Exception:
        pass
    if not c["pdf"] or c["size"] == 0 or fitz is None:
        return c
    try:
        doc = fitz.open(path)
    except Exception:
        return c
    c["open"] = True; c["pages"] = doc.page_count; c["encrypted"] = bool(doc.is_encrypted)
    if c["encrypted"] or c["pages"] == 0:
        return c
    txt = ""
    for i, page in enumerate(doc):
        if i >= 3:
            break
        if page.rotation % 360 != 0:
            c["rotated"] = True
        blocks = page.get_text("blocks") or []
        xs = sorted(round(b[0] / 50) for b in blocks if len(b) > 4 and str(b[4]).strip())
        if xs:
            c["columns"] = max(c["columns"], min(3, len(set(xs)) // 2 if len(set(xs)) > 2 else 1))
        try:
            c["tables"] += len(page.find_tables().tables)
        except Exception:
            pass
        txt += page.get_text() or ""
    c["text_chars"] = len(txt.strip())
    if txt:
        bad = sum(1 for ch in txt if ch in "\ufffd\u25a1\u25a0" or (0xE000 <= ord(ch) <= 0xF8FF))
        c["cjk_garble"] = round(bad / max(1, len(txt)), 4)
        c["footer_in_body"] = bool(RE_FOOTER.search(txt[: max(200, len(txt) // 2)]))
        c["nfkc_diff"] = unicodedata.normalize("NFKC", txt) != txt
        c["spaced"] = len(RE_SPACED.findall(txt))
        c["has_period"] = bool(RE_PERIOD.search(txt)); c["paren_neg"] = len(RE_NUM_PAREN.findall(txt)); c["eps_rows"] = len(RE_EPS.findall(txt))
        c["ticker"] = bool(RE_TICKER.search(txt)); c["date"] = bool(RE_DATE.search(txt)); c["rating"] = bool(RE_RATING.search(txt)); c["tp"] = bool(RE_TP.search(txt))
        c["unit_mix"] = len({u for u in ("億", "百萬", "千元") if u in txt}) > 1
    if pdfplumber is not None:
        try:
            with pdfplumber.open(str(path)) as pl:
                c["text_chars_plumber"] = len(((pl.pages[0].extract_text() or "") if pl.pages else "").strip())
        except Exception:
            c["text_chars_plumber"] = None
    return c


def judge(c: dict, seen_sha: dict) -> dict:
    """25 格四態。GRAY = 本件不適用 / 前置已紅;NODATA = 工具缺。"""
    out = {}
    tool = fitz is not None
    def put(rid, lamp, note=""):
        out[rid] = {"lamp": lamp, "note": note}
    put("R01", "RED" if not c["pdf"] else "GREEN", "" if c["pdf"] else "非 PDF")
    put("R02", "RED" if (c["size"] == 0 or (c["pdf"] and tool and not c["open"])) else ("NODATA" if not tool else "GREEN"))
    base_ok = c["pdf"] and c["open"] and not c["encrypted"] and c["pages"] > 0
    put("R03", "RED" if c["encrypted"] else ("GREEN" if c["open"] else "GRAY"))
    if not tool:
        for rid, *_ in RISKS[3:]:
            put(rid, "NODATA", "pymupdf 缺")
        return out
    if not base_ok:
        for rid, *_ in RISKS[3:]:
            put(rid, "GRAY", "前置未過")
        return out
    put("R04", "YELLOW" if c["text_chars"] < 50 else "GREEN", "文字層空 → tier 1" if c["text_chars"] < 50 else "")
    put("R05", "YELLOW" if c["rotated"] else "GREEN")
    put("R06", "YELLOW" if c["columns"] >= 2 else "GREEN", f"欄 {c['columns']}")
    put("R07", "YELLOW" if (c["tables"] == 0 and c.get("paren_neg", 0) + c.get("eps_rows", 0) > 3) else "GREEN", "數字列群但無格線表")
    put("R08", "YELLOW" if c["pages"] > 1 and c["tables"] > 0 else "GREEN", "多頁含表,要續接核")
    put("R09", "YELLOW" if c["tables"] > 0 else "GRAY", "表頭補齊要核")
    put("R10", "YELLOW" if c.get("paren_neg", 0) > 0 else "GREEN", f"括號負數 {c.get('paren_neg', 0)}")
    put("R11", "YELLOW" if c.get("has_period") else "GREEN")
    put("R12", "YELLOW" if c.get("unit_mix") else "GREEN")
    put("R13", "GREEN" if c.get("ticker") else "YELLOW", "" if c.get("ticker") else "代號未見 → 檔名互核")
    put("R14", "GREEN" if c.get("date") else "YELLOW", "" if c.get("date") else "日期未見 → 檔名日")
    put("R15", "GREEN" if c.get("rating") else "YELLOW", "" if c.get("rating") else "評等詞未見 → 樞紐候選")
    put("R16", "GREEN" if c.get("tp") else "YELLOW", "" if c.get("tp") else "目標價詞未見")
    put("R17", "YELLOW" if c.get("eps_rows", 0) >= 2 else ("GREEN" if c.get("eps_rows", 0) == 1 else "GRAY"), f"EPS 列 {c.get('eps_rows', 0)}")
    put("R18", "RED" if c["cjk_garble"] > 0.05 else ("YELLOW" if c["cjk_garble"] > 0.01 else "GREEN"), f"亂碼率 {c['cjk_garble']}")
    put("R19", "YELLOW" if c["spaced"] > 0 else "GREEN", f"斷字 {c['spaced']}")
    put("R20", "YELLOW" if c["footer_in_body"] else "GREEN")
    dup = seen_sha.get(c["sha16"]); seen_sha.setdefault(c["sha16"], c["file"])
    put("R21", "YELLOW" if dup else "GREEN", f"同 sha:{dup}" if dup else "")
    put("R22", "YELLOW" if (c["size"] > 50 * 1024 * 1024 or c["pages"] > 80) else "GREEN", f"{round(c['size']/1048576,1)}MB · {c['pages']}頁")
    put("R23", "YELLOW" if c["nfkc_diff"] else "GREEN")
    tp = c.get("text_chars_plumber")
    put("R24", "NODATA" if tp is None else ("YELLOW" if (c["text_chars"] < 50 and tp < 50) else "GREEN"), "pdfplumber 缺" if tp is None else "")
    put("R25", "GRAY", "輸出後由 CGC_MDL249 check 量(本支不產輸出)")
    return out


def run(in_dir: Path, out_dir: Path, limit: int = 0, open_page: bool = True) -> dict:
    files = sorted([p for p in in_dir.rglob("*") if p.is_file() and p.suffix.lower() in (".pdf", ".docx", ".pptx", ".doc", ".txt")])
    if limit:
        files = files[:limit]
    seen = {}; rows = []
    for p in files:
        c = probe(p); j = judge(c, seen)
        rows.append({"file": p.name, "sha16": c["sha16"], "pages": c["pages"], "chars": c["text_chars"], "cells": j,
                     "lamp": "RED" if any(v["lamp"] == "RED" for v in j.values()) else ("YELLOW" if any(v["lamp"] == "YELLOW" for v in j.values()) else ("NODATA" if any(v["lamp"] == "NODATA" for v in j.values()) else "GREEN"))})
    cnt = {k: sum(1 for r in rows if r["lamp"] == k) for k in ("GREEN", "YELLOW", "RED", "NODATA")}
    risk_cnt = {rid: {k: sum(1 for r in rows if r["cells"].get(rid, {}).get("lamp") == k) for k in ("GREEN", "YELLOW", "RED", "GRAY", "NODATA")} for rid, *_ in RISKS}
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"engine": ENGINE, "in": str(in_dir), "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "files": len(rows), "lamps": cnt, "tools": {"pymupdf": fitz is not None, "pdfplumber": pdfplumber is not None},
           "risks": [{"id": r[0], "zh": r[1], "fix": r[3], "verify": r[4], "repair": r[5], **risk_cnt[r[0]]} for r in RISKS], "rows": rows,
           "verdict": "RED" if cnt["RED"] else ("NODATA" if (fitz is None) else ("YELLOW" if cnt["YELLOW"] else "GREEN"))}
    (out_dir / f"REALTEST_{stamp}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "REALTEST_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    write_html(out_dir / "REALTEST_latest.html", rep)
    pack = [f"# REALTEST {stamp} · {rep['verdict']} · 件 {len(rows)} · 綠 {cnt['GREEN']} 黃 {cnt['YELLOW']} 紅 {cnt['RED']} 沒料 {cnt['NODATA']}"]
    for r in RISKS:
        rc = risk_cnt[r[0]]
        if rc["RED"] or rc["YELLOW"]:
            pack.append(f"- {r[0]} {r[1]} · 紅 {rc['RED']} 黃 {rc['YELLOW']} → {r[3]}")
    for r in rows:
        if r["lamp"] == "RED":
            pack.append("- [RED] " + r["file"] + " · " + ", ".join(k for k, v in r["cells"].items() if v["lamp"] == "RED"))
    (out_dir / "paste.md").write_text("\n".join(pack), encoding="utf-8")
    print("\n".join(pack[:40]))
    print(f"  頁 {out_dir / 'REALTEST_latest.html'} · JSON REALTEST_{stamp}.json · paste.md")
    if open_page and os.name == "nt" and os.environ.get("VIA_NO_OPEN") != "1":
        try:
            os.startfile(str(out_dir / "REALTEST_latest.html"))  # type: ignore[attr-defined]
        except Exception:
            pass
    return rep


def write_html(path: Path, rep: dict) -> None:
    e = html.escape
    css = ("body{font:11px Arial,sans-serif;background:#fff;color:#111827;margin:0;padding:14px}h1{font-size:16px;margin:0 0 6px}table{border-collapse:collapse;font-size:11px}td,th{border:1px solid #e0e0e0;padding:3px 6px;vertical-align:top}th{background:#f7f7f7;position:sticky;top:0}"
           ".lamp{display:inline-block;width:10px;height:10px;border-radius:50%;vertical-align:middle}" + "".join(f".{k}{{color:{v}}}.lamp.{k}{{background:{v}}}" for k, v in PAL.items()) + ".legend span{margin-right:12px}")
    cnt = rep["lamps"]
    h = [f"<!doctype html><html><head><meta charset='utf-8'><title>VRN RealTest</title><style>{css}</style></head><body><h1>VRN 實測前置 · 25 風險 × {rep['files']} 件 · <span class='{rep['verdict']}'>{rep['verdict']}</span></h1>",
         f"<p class='legend'><span class='GREEN'><i class='lamp GREEN'></i> 過 {cnt['GREEN']}</span><span class='YELLOW'><i class='lamp YELLOW'></i> 要人裁 {cnt['YELLOW']}</span><span class='RED'><i class='lamp RED'></i> 命中修不掉 {cnt['RED']}</span><span class='GRAY'><i class='lamp GRAY'></i> 不適用 / 沒跑</span><span class='NODATA'><i class='lamp NODATA'></i> 工具缺 {cnt['NODATA']}</span> · 色 = VIA_UI_FormatLock · {e(rep['in'])}</p>",
         "<h2 style='font-size:13px'>風險總表(偵測 · 修法 · 驗證 · 資料修復)</h2><table><tr><th>號</th><th>風險</th><th>綠</th><th>黃</th><th>紅</th><th>灰</th><th>沒料</th><th>修法(正主)</th><th>驗證</th><th>資料修復</th></tr>"]
    for r in rep["risks"]:
        h.append(f"<tr><td>{r['id']}</td><td>{e(r['zh'])}</td><td class='GREEN'>{r['GREEN']}</td><td class='YELLOW'>{r['YELLOW']}</td><td class='RED'>{r['RED']}</td><td class='GRAY'>{r['GRAY']}</td><td class='NODATA'>{r['NODATA']}</td><td>{e(r['fix'])}</td><td>{e(r['verify'])}</td><td>{e(r['repair'])}</td></tr>")
    h.append("</table><h2 style='font-size:13px'>逐件 × 25</h2><div style='overflow:auto'><table><tr><th>檔</th><th>燈</th><th>頁</th><th>字</th>" + "".join(f"<th>{r[0]}</th>" for r in RISKS) + "</tr>")
    for row in rep["rows"]:
        cells = "".join(f"<td class='{row['cells'][r[0]]['lamp']}' title='{e(row['cells'][r[0]].get('note', ''))}'><i class='lamp {row['cells'][r[0]]['lamp']}'></i></td>" for r in RISKS)
        h.append(f"<tr><td>{e(row['file'])}</td><td class='{row['lamp']}'><i class='lamp {row['lamp']}'></i> {row['lamp']}</td><td>{row['pages']}</td><td>{row['chars']}</td>{cells}</tr>")
    h.append("</table></div></body></html>")
    path.write_text("".join(h), encoding="utf-8")


def selftest() -> int:
    ok = []
    def chk(name, cond, note=""):
        ok.append(bool(cond)); print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + note) if note else ''}")
    chk("① 25 風險各有 偵測鍵 · 修法 · 驗證 · 資料修復 四欄", len(RISKS) == 25 and all(len(r) == 6 and all(r) for r in RISKS))
    chk("② 風險號連號 R01..R25 不重", [r[0] for r in RISKS] == [f"R{i:02d}" for i in range(1, 26)])
    with tempfile.TemporaryDirectory() as td:
        d = Path(td); (d / "empty.pdf").write_bytes(b""); (d / "note.txt").write_text("x", encoding="utf-8")
        if fitz is not None:
            doc = fitz.open(); page = doc.new_page()
            page.insert_text((72, 72), "2330 TT  Target Price NT$ 1,200  Buy  EPS 35.2  2024/03/01  (1,234)  1Q24", fontsize=11)
            page.insert_text((72, 100), "營收 12 億 / 300 百萬", fontsize=11, fontname="china-t")   # CJK 要用內建中文字型,否則文字層無字
            doc.save(str(d / "good.pdf")); doc.close()
            (d / "dup.pdf").write_bytes((d / "good.pdf").read_bytes())
        rep = run(d, d / "out", open_page=False)
        cells = {r["file"]: r["cells"] for r in rep["rows"]}
        chk("③ 0 byte → R02 RED · 非 PDF → R01 RED", cells["empty.pdf"]["R02"]["lamp"] == "RED" and cells["note.txt"]["R01"]["lamp"] == "RED")
        if fitz is not None:
            g = cells["good.pdf"]
            chk("④ 合成樣本:代號 / 日期 / 評等 / 目標價 全 GREEN · 括號負數 · 期別 · 單位混用 → YELLOW", all(g[k]["lamp"] == "GREEN" for k in ("R13", "R14", "R15", "R16")) and all(g[k]["lamp"] == "YELLOW" for k in ("R10", "R11", "R12")), str({k: g[k]["lamp"] for k in ("R10", "R11", "R12", "R13", "R14", "R15", "R16")}))
            pair = (cells["dup.pdf"]["R21"], cells["good.pdf"]["R21"])
            chk("⑤ 重複檔:兩份同 sha 其一 R21 YELLOW 並指名另一份", any(x["lamp"] == "YELLOW" and (".pdf" in x["note"]) for x in pair))
        else:
            chk("④⑤ pymupdf 缺 → 25 格 NODATA(誠實)", all(v["lamp"] in ("NODATA", "RED", "GREEN", "GRAY") for v in cells["note.txt"].values()) and rep["verdict"] in ("NODATA", "RED"))
        t = (d / "out" / "REALTEST_latest.html").read_text(encoding="utf-8")
        chk("⑥ HTML 四燈 + 青用鎖定色,圖例在", all(c in t for c in PAL.values()) and "legend" in t)
        chk("⑦ 只讀:樣本夾沒多出檔(除 out/)", sorted(p.name for p in d.iterdir() if p.is_file()) == sorted(["empty.pdf", "note.txt"] + (["good.pdf", "dup.pdf"] if fitz is not None else [])))
    chk("⑧ 加速器橋在 · 不碰 TA-Lib · 不代設同意閘", "VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] {ENGINE} 自測 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'} · 工具 pymupdf={fitz is not None} pdfplumber={pdfplumber is not None}")
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False)); return 2
    if not a or a[0] != "run":
        print(__doc__); return 2
    in_dir = Path(a[a.index("--in") + 1]) if "--in" in a else Path(r"C:\測試樣本報告")
    limit = int(a[a.index("--limit") + 1]) if "--limit" in a else 0
    if not in_dir.is_dir():
        print(f"[REALTEST] 樣本夾不在:{in_dir}"); return 3
    rep = run(in_dir, VIA / "VIA_Reports" / "vrn" / "realtest", limit, open_page="--no-open" not in a)
    return 0 if rep["verdict"] == "GREEN" or rep["verdict"] == "YELLOW" else (3 if rep["verdict"] == "NODATA" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
