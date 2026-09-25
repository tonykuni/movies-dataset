"""末日級格式無關擷取引擎（stdlib 優先，永不崩，抓不到必有原因）。

處理 word/excel/text/csv/image 內部未知內容，回答五問並吐 JSON：
  1. 保證全抓？—— 每個單元都稽核，未擷取必有原因；unexplained_gap=0 才算保證。
  2. 各型別校正驗證 —— mojibake 修復、編碼偵測、CSV 分隔嗅探，修完再驗無資料流失。
  3. 無遺漏去重 —— content_hash 去重，完整性 gate 確認無遺漏。
  4. 有意義分類再分類 —— auto_ssot 自舉桶＋多道分類。
  5. 重點摘要 —— 抽取式關鍵句＋高鑑別詞。

設計：docx/xlsx 用 zipfile+XML 自解（不依賴 python-docx/openpyxl），image 無 OCR 時
誠實標記 needs-OCR（不假裝抓到）。全程 try/except，任何檔壞掉只記原因不中斷。
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

import csv as _csv
import io
import json
import re
import zipfile

from .encoding import repair_mojibake
from .numbering import content_hash

# ── 格式偵測（副檔名 + magic bytes）──────────────────────────
_MAGIC = [
    (b"PK\x03\x04", "zip"),        # docx/xlsx/zip
    (b"\x89PNG", "png"),
    (b"\xff\xd8\xff", "jpg"),
    (b"GIF8", "gif"),
    (b"%PDF", "pdf"),
]


def detect_format(path: str) -> str:
    ext = path.lower().rsplit(".", 1)[-1] if "." in path else ""
    try:
        with open(path, "rb") as f:
            head = f.read(8)
    except Exception:
        return ext or "unknown"
    magic = next((name for sig, name in _MAGIC if head.startswith(sig)), "")
    if ext in ("docx",) and magic == "zip":
        return "docx"
    if ext in ("xlsx",) and magic == "zip":
        return "xlsx"
    if magic in ("png", "jpg", "gif"):
        return "image"
    if magic == "pdf" or ext == "pdf":
        return "pdf"
    if ext in ("csv", "tsv"):
        return "csv"
    if ext in ("txt", "md", "log"):
        return "text"
    return ext or magic or "unknown"


def _strip_xml(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


# ── 各型別擷取（回傳 units + 稽核）──────────────────────────
def _audit_new(name):
    return {"source": name, "seen": 0, "extracted": 0, "failures": []}


def extract_docx(path):
    """zip+XML 自解 Word：段落文字 + 表格 cell + 圖片標記。"""
    a = _audit_new("docx:" + path)
    units = []
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", "replace")
            media = [n for n in z.namelist() if n.startswith("word/media/")]
    except Exception as e:
        a["failures"].append(("whole_file", f"error:無法開啟 {e}"))
        return units, a
    # 段落：以 </w:p> 切，抽 <w:t>
    paras = xml.split("</w:p>")
    for i, p in enumerate(paras):
        a["seen"] += 1
        txt = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, re.DOTALL))
        txt = _strip_xml(txt).strip()
        if txt:
            units.append({"text": txt, "kind": "paragraph", "ref": f"p{i}"})
            a["extracted"] += 1
        else:
            a["failures"].append((f"p{i}", "structural:空段落"))
    for m in media:
        a["seen"] += 1
        a["failures"].append((m, "recoverable:image/needs-OCR"))   # 誠實標記
    return units, a


def extract_xlsx(path):
    """zip+XML 自解 Excel：sharedStrings + 每個 sheet 的非空 cell。"""
    a = _audit_new("xlsx:" + path)
    units = []
    try:
        with zipfile.ZipFile(path) as z:
            shared = []
            if "xl/sharedStrings.xml" in z.namelist():
                ss = z.read("xl/sharedStrings.xml").decode("utf-8", "replace")
                shared = [_strip_xml(x).strip() for x in re.findall(r"<si>(.*?)</si>", ss, re.DOTALL)]
            sheets = [n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml", n)]
            for sh in sheets:
                body = z.read(sh).decode("utf-8", "replace")
                for c in re.findall(r"<c\b[^>]*>.*?</c>|<c\b[^>]*/>", body, re.DOTALL):
                    a["seen"] += 1
                    ref = (re.search(r'r="([A-Z]+\d+)"', c) or [None, sh])[1]
                    is_s = 't="s"' in c
                    v = re.search(r"<v>(.*?)</v>", c, re.DOTALL)
                    txt = ""
                    if v:
                        raw = _strip_xml(v.group(1)).strip()
                        txt = shared[int(raw)] if (is_s and raw.isdigit() and int(raw) < len(shared)) else raw
                    else:
                        it = re.search(r"<t[^>]*>(.*?)</t>", c, re.DOTALL)
                        txt = _strip_xml(it.group(1)).strip() if it else ""
                    if txt:
                        units.append({"text": txt, "kind": "cell", "ref": ref})
                        a["extracted"] += 1
                    else:
                        a["failures"].append((ref, "structural:空儲存格"))
    except Exception as e:
        a["failures"].append(("whole_file", f"error:無法開啟 {e}"))
    return units, a


def extract_csv(path):
    a = _audit_new("csv:" + path)
    units = []
    raw = _read_bytes_text(path)
    if raw is None:
        a["failures"].append(("whole_file", "error:無法解碼"))
        return units, a
    try:
        dialect = _csv.Sniffer().sniff(raw[:2048]) if raw.strip() else _csv.excel
    except Exception:
        dialect = _csv.excel
    for i, row in enumerate(_csv.reader(io.StringIO(raw), dialect)):
        a["seen"] += 1
        cells = [c.strip() for c in row if c and c.strip()]
        if cells:
            units.append({"text": " | ".join(cells), "kind": "row", "ref": f"r{i}"})
            a["extracted"] += 1
        else:
            a["failures"].append((f"r{i}", "structural:空列"))
    return units, a


def extract_text(path):
    a = _audit_new("text:" + path)
    units = []
    raw = _read_bytes_text(path)
    if raw is None:
        a["failures"].append(("whole_file", "error:無法解碼"))
        return units, a
    for i, line in enumerate(raw.splitlines()):
        a["seen"] += 1
        t = line.strip()
        if t:
            units.append({"text": t, "kind": "line", "ref": f"L{i}"})
            a["extracted"] += 1
        else:
            a["failures"].append((f"L{i}", "structural:空行"))
    return units, a


def extract_image(path):
    a = _audit_new("image:" + path)
    a["seen"] = 1
    a["failures"].append((path, "recoverable:image/needs-OCR"))   # 無 OCR 時誠實標記，不假裝
    return [], a


def _read_bytes_text(path):
    """編碼偵測解碼（chardet 有就用，否則多編碼嘗試）。回 str 或 None。"""
    try:
        b = open(path, "rb").read()
    except Exception:
        return None
    try:
        import chardet
        enc = chardet.detect(b).get("encoding") or "utf-8"
        return b.decode(enc, "replace")
    except Exception:
        for enc in ("utf-8-sig", "utf-8", "big5", "cp950", "gb18030", "latin-1"):
            try:
                return b.decode(enc)
            except Exception:
                continue
    return b.decode("utf-8", "replace")


_EXTRACTORS = {"docx": extract_docx, "xlsx": extract_xlsx, "csv": extract_csv,
               "text": extract_text, "image": extract_image}


def extract_any(path):
    fmt = detect_format(path)
    fn = _EXTRACTORS.get(fmt)
    if not fn:
        a = _audit_new(f"{fmt}:{path}")
        a["seen"] = 1
        a["failures"].append((path, f"recoverable:未支援格式 {fmt}"))
        return [], a
    try:
        return fn(path)
    except Exception as e:                       # 末日：任何檔壞掉只記原因不中斷
        a = _audit_new(f"{fmt}:{path}")
        a["failures"].append((path, f"error:擷取例外 {e}"))
        return [], a


# ── 1. 完整性保證（指標）──────────────────────────────────
def _categorize(reason):
    if reason.startswith("structural"):
        return "structural"
    if reason.startswith("recoverable"):
        return "recoverable"
    return "error"


def guarantee_report(audits):
    seen = sum(a["seen"] for a in audits)
    extracted = sum(a["extracted"] for a in audits)
    cats = {"structural": 0, "recoverable": 0, "error": 0}
    for a in audits:
        for _, reason in a["failures"]:
            cats[_categorize(reason)] += 1
    explained = cats["structural"] + cats["recoverable"] + cats["error"]
    unexplained = seen - extracted - explained
    return {
        "seen": seen, "extracted": extracted,
        "coverage_pct": round(100 * extracted / seen, 1) if seen else 100.0,
        "failures_by_cause": cats,
        "unexplained_gap": unexplained,
        "guarantee_pass": unexplained == 0,       # 每個未擷取都有原因才「保證全抓」
    }


# ── 2. 校正驗證 ───────────────────────────────────────────
def validate_correct(units):
    corrections = 0
    for u in units:
        before = u["text"]
        after = repair_mojibake(before)
        after = re.sub(r"[ \t]+", " ", after).strip()
        if after != before:
            corrections += 1
        u["text"] = after
    # 驗證：修復不得把有字變空（資料流失防呆）
    lost = sum(1 for u in units if not u["text"])
    return {"corrections": corrections, "data_loss": lost, "verify_pass": lost == 0}


# ── 3. 去重（content_hash）────────────────────────────────
def dedup(units):
    seen, uniq, dups = {}, [], 0
    for u in units:
        h = content_hash(u["text"])
        u["hash"] = h
        if h in seen:
            dups += 1
        else:
            seen[h] = True
            uniq.append(u)
    return uniq, {"total": len(units), "unique": len(uniq), "duplicates": dups}


# ── 4. 有意義分類 ─────────────────────────────────────────
def classify_units(units, dims=("topic",), seed=None):
    from .schema import Record
    from .classify import classify_all, seed_buckets_from_data
    from .autocode import mint_universal_id
    recs = [Record(title=u["text"][:40], body=u["text"], uid=u["hash"]) for u in units]
    cls = {d: dict((seed or {}).get(d, {})) for d in dims}     # 可注入行業骨架 → 有意義分類
    seed_buckets_from_data(recs, cls, dims=dims)
    classify_all(recs, cls)
    for r in recs:
        r.uid = mint_universal_id(r, "file", getattr(r, dims[0], "") or "")
    hits = sum(1 for r in recs if getattr(r, dims[0], ""))
    for u, r in zip(units, recs):
        u["class"] = getattr(r, dims[0], "")
    return {"buckets": {d: len(cls.get(d, {})) for d in dims},
            "classified": hits, "coded": len(recs), "total": len(recs)}


# ── 5. 重點摘要（抽取式）──────────────────────────────────
_IMPORTANT = ["需", "請", "務必", "截止", "deadline", "決定", "問題", "風險",
              "延遲", "異常", "變更", "確認", "核准", "客戶", "交期"]


def summarize(units, top_terms=8, max_points=6):
    from collections import Counter
    text = " ".join(u["text"] for u in units)
    words = re.findall(r"[A-Za-z]{3,}|[\u4e00-\u9fff]{2,4}", text)
    terms = [w for w, _ in Counter(words).most_common(top_terms)]
    points = []
    for u in units:
        if any(k in u["text"] for k in _IMPORTANT) or re.search(r"\d{4}[-/]\d", u["text"]):
            points.append(u["text"][:80])
        if len(points) >= max_points:
            break
    return {"key_terms": terms, "key_points": points}


# ── 主流程：吐 JSON（parameters + data）─────────────────────
def run_ingest(paths, dims=("topic",), out_json=None, seed=None, dedup_on=True, csv_path=None):
    all_units, audits = [], []
    for p in paths:
        units, a = extract_any(p)
        all_units.extend(units)
        audits.append(a)
    guarantee = guarantee_report(audits)
    correction = validate_correct(all_units)
    if dedup_on:
        uniq, dd = dedup(all_units)
    else:
        for u in all_units:
            u["hash"] = content_hash(u["text"])
        uniq, dd = all_units, {"total": len(all_units), "unique": len(all_units), "duplicates": 0, "mode": "no-dedup"}
    number_all(uniq)
    classification = classify_units(uniq, dims=dims, seed=seed)
    if csv_path:
        to_csv(uniq, csv_path)
    summary = summarize(uniq)
    result = {
        "parameters": {
            "files": len(paths), "dims": list(dims),
            "guarantee": guarantee, "correction": correction,
            "dedup": dd, "classification": classification,
        },
        "completeness": guarantee,
        "data": [{"seq": u.get("seq",""), "text": u["text"], "kind": u["kind"], "ref": u["ref"],
                  "hash": u["hash"], "class": u.get("class", "")} for u in uniq],
        "csv_path": csv_path,
        "summary": summary,
    }
    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    return result

def number_all(units, prefix="VIS"):
    """不去重，逐筆給流水號（分別編號）。"""
    for i, u in enumerate(units, 1):
        u["seq"] = f"{prefix}-{i:04d}"
    return units


def to_csv(units, csv_path):
    """輸出 CSV，UTF-8-BOM（解決中文編碼問題）。"""
    import csv as _c
    cols = ["seq", "ref", "kind", "class", "hash", "text"]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = _c.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for u in units:
            w.writerow({k: u.get(k, "") for k in cols})
    return csv_path
