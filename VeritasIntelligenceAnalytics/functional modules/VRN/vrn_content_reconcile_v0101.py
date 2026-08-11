#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_content_reconcile_v0101 — OCR 擷取產物 × SSOT v2 內容級對帳(唯讀;缺口診斷版)
=======================================================================
深水線①首版:報告型對帳,零寫入(落庫版候本對帳綠燈後另出 v0101+)。
對帳三層:
  A 覆蓋層:64 筆 v2 記錄 × 擷取產物在位比對(鍵=pdf_name↔source_document)
     MDL005 文字(VRN_MDL005_Text.parquet/csv)· MDL004 表格(VRN_MDL004_Tables)
     · DOCX 解析(docx_txt/*.txt)
  B 內容層:記錄之目標價/代號猜值 → 於該檔文字塊中實測可尋性
     (資訊級 CONFIRMED_IN_TEXT/NOT_FOUND,誠實不判死)
  C 總結:FULL/TEXT_ONLY/TABLE_ONLY/DOCX_TXT/NO_EXTRACTION 分佈
誠實口徑:staging 缺席=如實列 NO_EXTRACTION;pandas 缺=CSV 退路;不假綠。
用法:py vrn_content_reconcile_v0100.py [--staging DIR] [--json] [--no-open]
輸出:VIA_Reports/vrn_reconcile_runs/reconcile_<ts>.json + .html
v0101 新增(操作員機首跑 63/64 後):NO_EXTRACTION 記錄終端點名 +
difflib 最近似 pdf_name 候選診斷(自證檔名錯位原因;含 contains 關係檢測)。
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent


def load_flat(base: Path, stem: str):
    """讀扁平表:parquet 優先(pandas),退 csv(內建);回 list[dict] 或 None。"""
    pq, cs = base / f"{stem}.parquet", base / f"{stem}.csv"
    if pq.exists():
        try:
            import pandas as pd
            return pd.read_parquet(pq).to_dict("records")
        except Exception:
            pass
    if cs.exists():
        try:
            with open(cs, encoding="utf-8-sig", newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            return None
    return None


def norm(name: str) -> str:
    return (name or "").strip().lower()


def main() -> int:
    args = sys.argv[1:]
    as_json = "--json" in args
    staging = Path(args[args.index("--staging") + 1]) if "--staging" in args \
        else HERE / "staging" / "ocr_out"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    v2p = HERE / "SSOT/v2/VRN_ResearchReport_SSOT.v2.jsonl"
    records = [json.loads(l) for l in v2p.read_text(encoding="utf-8-sig").splitlines() if l.strip()]

    text_rows = load_flat(staging / "mdl005_temp", "VRN_MDL005_Text")
    table_rows = load_flat(staging / "mdl004_temp", "VRN_MDL004_Tables")
    docx_dir = staging / "docx_txt"
    docx_txts = {norm(p.stem): p for p in docx_dir.glob("*.txt")} if docx_dir.exists() else {}

    def rows_for(rows, doc):
        if not rows:
            return []
        nd = norm(doc)
        key_fields = ("pdf_name", "source_document", "source_pdf", "file_name")
        return [r for r in rows if any(norm(str(r.get(k, ""))) == nd for k in key_fields)]

    out_rows, dist = [], {}
    for rec in records:
        doc = rec.get("source_document", "")
        is_docx = doc.lower().endswith((".docx", ".doc"))
        t_blocks = rows_for(text_rows, doc)
        tb_rows = rows_for(table_rows, doc)
        d_txt = norm(Path(doc).stem) in docx_txts if is_docx else False
        if is_docx:
            status = "DOCX_TXT" if d_txt else "NO_EXTRACTION"
        elif t_blocks and tb_rows:
            status = "FULL"
        elif t_blocks:
            status = "TEXT_ONLY"
        elif tb_rows:
            status = "TABLE_ONLY"
        else:
            status = "NO_EXTRACTION"
        dist[status] = dist.get(status, 0) + 1

        # B 內容層:目標價猜值於文字塊可尋性(資訊級)
        probe = "—"
        tps = rec.get("target_price_content_guesses") or rec.get("filtered_target_price_proposals") or []
        vals = []
        for t in tps if isinstance(tps, list) else []:
            v = t.get("value") if isinstance(t, dict) else t
            if v is not None:
                vals.append(str(v).rstrip("0").rstrip(".") if "." in str(v) else str(v))
        if vals and t_blocks:
            blob = " ".join(str(b.get("text", "")) for b in t_blocks)
            hit = sum(1 for v in vals if v and v in blob)
            probe = f"目標價 {hit}/{len(vals)} 在文中尋獲"
        elif vals:
            probe = f"目標價 {len(vals)} 值候文字層({status})"
        out_rows.append({
            "source_document": doc, "status": status,
            "text_blocks": len(t_blocks), "table_rows": len(tb_rows),
            "docx_txt": d_txt, "content_probe": probe,
            "record_state": rec.get("canonical_record_state", "?"),
        })

    staged = {"mdl005": text_rows is not None and len(text_rows or []),
              "mdl004": table_rows is not None and len(table_rows or []),
              "docx_txt": len(docx_txts)}
    covered = sum(v for k, v in dist.items() if k != "NO_EXTRACTION")
    verdict = "COVERED" if dist.get("NO_EXTRACTION", 0) == 0 else "GAPS"
    payload = {"schema": "via.vrn.content_reconcile.v1", "ts": ts, "readonly": True,
               "staging": str(staging), "staging_inventory": staged,
               "records": len(records), "covered": covered, "distribution": dist,
               "verdict": verdict, "rows": out_rows}

    out_dir = VIA / "VIA_Reports" / "vrn_reconcile_runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    jp = out_dir / f"reconcile_{ts}.json"
    jp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    cls = {"FULL": "g", "DOCX_TXT": "g", "TEXT_ONLY": "o", "TABLE_ONLY": "o", "NO_EXTRACTION": "r"}
    trows = "".join(
        f"<tr><td class='small'>{r['source_document'][:46]}</td>"
        f"<td><span class='tag {cls[r['status']]}'>{r['status']}</span></td>"
        f"<td class='r mono'>{r['text_blocks']}</td><td class='r mono'>{r['table_rows']}</td>"
        f"<td class='small'>{r['content_probe']}</td></tr>" for r in out_rows)
    html = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VRN Content Reconcile {ts}</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}body{{background:#f2f1ec;color:#33403f;font-family:"Microsoft JhengHei","Segoe UI",sans-serif;font-size:clamp(9.5px,1.05vw,11px);padding:16px 20px;max-width:1080px;margin:0 auto;line-height:1.5}}
.mast{{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;border-bottom:1px solid #dcdad3;padding-bottom:10px;margin-bottom:12px}}
h1{{font-family:'Cormorant Garamond',Georgia,serif;font-size:19px;font-weight:500;letter-spacing:.055em;color:#1b1a17}}
.zh{{font-size:11px;color:#6b6860;margin-top:2px}}.num{{font-family:Consolas,monospace;font-size:9.5px;letter-spacing:.16em;color:#6b6860;text-transform:uppercase}}
.st{{font-family:Consolas,monospace;font-size:11px;text-align:right;color:#3d7a52}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #dbd9d3;border-radius:8px}}
th,td{{text-align:left;border-bottom:1px solid #ebe9e3;padding:4px 8px;vertical-align:top}}
th{{color:#6b6860;font-weight:700;font-size:9px;text-transform:uppercase;font-family:Consolas,monospace;letter-spacing:.05em}}
.r{{text-align:right}}.mono{{font-family:Consolas,monospace;font-size:.95em}}.small{{font-size:.92em;color:#6b6860}}
.tag{{display:inline-block;padding:1px 7px;border-radius:9px;font-family:Consolas,monospace;font-size:8px;font-weight:700}}
.tag.g{{background:#e6efec;color:#2c4f4a}}.tag.o{{background:#f2ecdd;color:#6f5c31}}.tag.r{{background:#f3e7e6;color:#9e2b25}}
.foot{{font-family:Consolas,monospace;font-size:9px;letter-spacing:.1em;color:#6b6860;text-transform:uppercase;text-align:center;padding:9px 0 3px}}
</style></head><body>
<div class="mast"><div><div class="num">VRN-RECONCILE · {ts} · READ-ONLY · 零落庫</div>
<h1>OCR EXTRACTION × SSOT v2 · CONTENT RECONCILE MATRIX</h1>
<div class="zh">覆蓋層+內容層對帳(鍵=pdf_name↔source_document)· 記錄 {len(records)} · 分佈 {json.dumps(dist, ensure_ascii=False)}</div></div>
<div class="st">{verdict}<br>覆蓋 {covered}/{len(records)}</div></div>
<table><tr><th>記錄(source_document)</th><th>對帳</th><th class="r">文字塊</th><th class="r">表格列</th><th>內容層探測</th></tr>{trows}</table>
<div class="foot">VERITAS REPORT NOVA · 唯讀對帳 v0100 · 落庫版候綠燈 · 存證 reconcile_{ts}.json</div>
</body></html>"""
    hp = out_dir / f"reconcile_{ts}.html"
    hp.write_text(html, encoding="utf-8")

    # v0101 缺口診斷:點名 + 最近似候選
    import difflib
    inv_names = sorted({str(r.get(k, "")) for rows in (text_rows or [], table_rows or [])
                        for r in rows for k in ("pdf_name", "source_document", "source_pdf", "file_name")
                        if r.get(k)})
    gaps = []
    for r in out_rows:
        if r["status"] != "NO_EXTRACTION":
            continue
        doc = r["source_document"]
        close = difflib.get_close_matches(doc, inv_names, n=3, cutoff=0.5)
        contains = [n for n in inv_names if norm(Path(doc).stem) in norm(n) or norm(Path(n).stem) in norm(doc)][:3]
        gaps.append({"source_document": doc, "closest": close, "contains_rel": contains})
    payload["gap_diagnostics"] = gaps

    if as_json:
        print(json.dumps({k: v for k, v in payload.items() if k != "rows"}, ensure_ascii=False))
    else:
        print(f"=== VRN 內容級對帳 v0101(唯讀;缺口診斷)· 記錄 {len(records)} · {verdict} ===")
        print(f"  [staging] {staging}")
        print(f"  [盤點] mdl005 文字列 {staged['mdl005'] or '缺'} · mdl004 表格列 {staged['mdl004'] or '缺'} · docx_txt {staged['docx_txt']}")
        print(f"  [分佈] " + " · ".join(f"{k} {v}" for k, v in sorted(dist.items())))
        for g in gaps:
            print(f"  [缺口] {g['source_document']}")
            for c in g["closest"]:
                print(f"     ≈ 最近似:{c}")
            for c in g["contains_rel"]:
                print(f"     ⊃ 包含關係:{c}")
            if not g["closest"] and not g["contains_rel"]:
                print("     (庫存中無任何近似檔名 — 該檔可能未被擷取引擎處理)")
        print(f"  報告:{hp}")
        print(f"  存證:{jp}")
    if "--no-open" not in args and not as_json and sys.platform == "win32":
        import os
        os.startfile(str(hp))  # noqa
    return 0 if verdict == "COVERED" else 1


if __name__ == "__main__":
    sys.exit(main())
