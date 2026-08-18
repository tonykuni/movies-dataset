# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# -*- coding: utf-8 -*-
# WorkOps 語料橋 v0100 — 把平台各式郵件匯出 CSV 轉為超級引擎可食格式
# 背景(操作員 2026/08/08 實跑):via-workops engine --input out 讀到 0 封 —
#   email_super_engine 的 CSV loader 期望欄位 subject/sender|from/to/cc/date|received/body|content,
#   而指揮板 mails.csv 用 SenderEmail/EventDate(無 body)、TimeRange 匯出用 SENDER_ADDRESS/EVENT_TIME/BODY_SNIPPET。
# 本橋自動辨識來源 schema(依標頭),統一映射為引擎欄位,輸出 corpus/corpus.csv。
# 治理:唯讀來源;不改兩端引擎正本(正本不就地修改);輸出可重生。
import argparse, csv, io, os, sys, glob

ENGINE_FIELDS = ["subject", "sender", "to", "cc", "date", "body", "source"]

# 來源欄名 → 引擎欄名(全小寫比對;左邊列出各世代別名)
ALIASES = {
    "subject": ["subject"],
    "sender":  ["sender", "from", "senderemail", "sender_address", "sender_email", "senderaddress"],
    "to":      ["to", "recipients", "to_recipients"],
    "cc":      ["cc"],
    "date":    ["date", "received", "eventdate", "event_time", "received_time", "receivedtime", "senton", "sent_time"],
    "body":    ["body", "content", "body_snippet", "bodypreview", "body_preview"],
}

def norm_date(v):
    v = (v or "").strip()
    if not v:
        return ""
    # 常見格式統一為 YYYY-MM-DD HH:MM:SS(引擎可解析)
    v = v.replace("/", "-")
    if len(v) == 16:  # YYYY-MM-DD HH:MM
        v += ":00"
    return v[:19]

def map_row(row):
    low = {k.strip().lower(): (v or "") for k, v in row.items() if k}
    out = {}
    for tgt, names in ALIASES.items():
        val = ""
        for n in names:
            if low.get(n):
                val = low[n]
                break
        out[tgt] = norm_date(val) if tgt == "date" else val
    return out

def collect(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += sorted(glob.glob(os.path.join(p, "**", "*.csv"), recursive=True))
        elif os.path.isfile(p) and p.lower().endswith(".csv"):
            files.append(p)
    # 排除自身輸出與非郵件表
    skip = ("corpus.csv", "kpi_history", "recipients", "reconcile", "stakeholders",
            "02_folder", "03_scan", "workops_id")
    return [f for f in files if not any(s in os.path.basename(f).lower() for s in skip)]

def main():
    ap = argparse.ArgumentParser(description="WorkOps 語料橋:郵件匯出 CSV → 引擎語料 corpus.csv")
    ap.add_argument("--inputs", nargs="+", required=True, help="來源 CSV 檔或資料夾(可多個)")
    ap.add_argument("--outdir", default="corpus", help="輸出資料夾(預設 corpus/)")
    a = ap.parse_args()
    files = collect(a.inputs)
    os.makedirs(a.outdir, exist_ok=True)
    out_path = os.path.join(a.outdir, "corpus.csv")
    n_in, n_out, n_body = 0, 0, 0
    seen = set()
    with io.open(out_path, "w", encoding="utf-8-sig", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=ENGINE_FIELDS)
        w.writeheader()
        for f in files:
            try:
                with io.open(f, "r", encoding="utf-8-sig", errors="replace") as fi:
                    for row in csv.DictReader(fi):
                        n_in += 1
                        m = map_row(row)
                        if not m["subject"] and not m["body"]:
                            continue
                        key = (m["subject"], m["sender"], m["date"])
                        if key in seen:
                            continue
                        seen.add(key)
                        m["source"] = os.path.basename(f)
                        if m["body"]:
                            n_body += 1
                        w.writerow(m)
                        n_out += 1
            except Exception as e:
                print("[略過] %s: %s" % (f, e), file=sys.stderr)
    print("[語料橋] 來源 %d 檔 / 讀入 %d 列 → 輸出 %d 封(含 body %d)→ %s"
          % (len(files), n_in, n_out, n_body, out_path))
    if n_out and not n_body:
        print("[提示] 語料無 body — scanrange 加 -IncludeBodySnippet $true 可補內文,NLP 分析更有料")
    return 0

if __name__ == "__main__":
    sys.exit(main())
