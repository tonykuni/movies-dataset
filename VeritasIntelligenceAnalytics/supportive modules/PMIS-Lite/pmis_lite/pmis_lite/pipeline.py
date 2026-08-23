"""主流程（第一大階段）：擷取→整理修復→編號→分析歸類→重整為可追蹤資料庫。

擷取(多來源+附件) → 治亂碼/文字修復 → 自動編號(穩定身分)
  → 術語探勘(候選佇列) → 分類 → 利害關係人 → 追蹤事項
  → 增量入庫 + 與上一版比對 → 完整性驗證(不可遺漏) → Markdown + pptx 草稿

啟動印 AUP 提醒。完整性驗證若有未解釋遺漏 → 報 FAIL，逼你正視。
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
import os
from datetime import datetime

import pandas as pd

from .schema import Record
from .numbering import content_hash, make_uid
from .classify import classify_record
from .store import ParquetStore
from .normalize.terms import TermStore, mine_candidates
from .completeness import CompletenessReport
from .stakeholders import build_registry
from .actions import extract_actions
from .attachments import extract_attachment
from .textrepair import clean_email_text
from .adapters import (
    ExcelCsvAdapter, MSProjectAdapter, PLMExportAdapter, OutlookDesktopAdapter,
    MailIMAPAdapter, SupplementAdapter, enrich_records,
)


def _build_adapter(src, base_dir, audit):
    t = src.get("type")
    def _p(key):
        p = src.get(key, "")
        return p if os.path.isabs(p) else os.path.join(base_dir, p)
    if t == "excel_csv":
        return ExcelCsvAdapter(_p("path"), audit=audit)
    if t == "msproject":
        return MSProjectAdapter(_p("path"), audit=audit)
    if t == "plm":
        return PLMExportAdapter(_p("path"), field_map=src.get("field_map"), audit=audit)
    if t == "outlook_desktop":
        return OutlookDesktopAdapter(months=src.get("months"),
                                     attachment_dir=os.path.join(base_dir, "sample_data/attachments"),
                                     audit=audit)
    if t == "mail_imap":
        # 自動直讀信箱（用使用者自己的認證；不可用時安靜略過）
        return MailIMAPAdapter(provider=src.get("provider", "gmail"),
                               user=src.get("user", ""), token=src.get("token", ""),
                               lookback_days=src.get("lookback_days", 180),
                               folder=src.get("folder", "INBOX"))
    if t == "supplement" and src.get("mode", "record") == "record":
        return SupplementAdapter(_p("path"), mode="record")
    if t == "enterprise":
        from .adapters import EnterpriseAdapter
        return EnterpriseAdapter(_p("path"), src.get("preset",""), src.get("overrides"), audit=audit)
    if t == "mail_jsonl":
        from .adapters import JsonlMailAdapter
        return JsonlMailAdapter(_p("path"), audit=audit)
    return None


def run(config_path):
    base_dir = os.path.dirname(os.path.abspath(config_path))
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)

    print("=" * 70)
    print("REMINDER:", cfg.get("_AUP_REMINDER", "").split("。")[0] + "。")
    print("=" * 70)

    num = cfg["numbering"]
    term_store = TermStore(seed=cfg.get("terms", {}).get("seed", {}))
    audit = CompletenessReport()

    # ---- 0. Plug & Play：自動偵測環境與來源（門外漢零設定）----
    sources = list(cfg.get("sources", []))
    detect_md = ""
    if cfg.get("auto_detect"):
        from .autodetect import probe, build_sources, summarize, detection_markdown
        demo = os.path.join(base_dir, "sample_data")
        info = probe(scan_roots=cfg.get("scan_roots"), demo_dir=demo)
        auto_src = build_sources(info)
        detect_md = detection_markdown(info)
        print(f"  [auto] 偵測：{summarize(info)}")
        print(f"  [auto] 自動接上 {len(auto_src)} 個來源")
        seen = {(s.get("type"), s.get("path")) for s in auto_src}
        for s in sources:
            if s.get("enabled") and (s.get("type"), s.get("path")) not in seen:
                auto_src.append(s)
        sources = auto_src
        if info["discovered"]["attachments"]:
            att_dir = os.path.dirname(info["discovered"]["attachments"][0])
            cfg.setdefault("attachments", {})
            cfg["attachments"].update({"dir": att_dir, "enabled": True})

    # ---- 1. 擷取 + 編號 ----
    records = []
    for src in sources:
        if not src.get("enabled"):
            continue
        adapter = _build_adapter(src, base_dir, audit)
        if adapter is None:
            print(f"  [skip] 來源 {src.get('type')} 未實作")
            continue
        print(f"  [read] 來源 {src.get('type')} ...")
        for rec in adapter.read():
            identity = content_hash(rec.title, rec.actor)
            rec.uid = make_uid(num["prefix"], num["domain"], identity, num.get("hash_len", 6))
            records.append(rec)

    # ---- 1b. 附件擷取（各類文件 → 文字，併入 SSOT）----
    att_cfg = cfg.get("attachments", {})
    if att_cfg.get("enabled"):
        att_dir = att_cfg.get("dir", "")
        if not os.path.isabs(att_dir):
            att_dir = os.path.join(base_dir, att_dir)
        if os.path.isdir(att_dir):
            aa = audit.audit("attachments")
            for fn in sorted(os.listdir(att_dir)):
                fpath = os.path.join(att_dir, fn)
                if not os.path.isfile(fpath):
                    continue
                aa.seen += 1
                res = extract_attachment(fpath)
                if not res.ok:

                    aa.failures.append((fn, res.reason))
                    continue
                rec = Record(source_type="attachment")
                rec.title = f"[附件] {fn}"
                rec.body, _ = clean_email_text(res.text)
                rec.source_ref = f"attachment::{fn}"
                rec.raw_keys = f"ext={res.ext} | chars={res.chars}"
                identity = content_hash(rec.title, rec.actor)
                rec.uid = make_uid(num["prefix"], num["domain"], identity, num.get("hash_len", 6))
                records.append(rec)
                aa.extracted += 1

    print(f"  擷取 {len(records)} 筆事件（含附件）")

    # ---- 1c. 額外資訊注入（enrich 既有 Record，append-only 不覆寫原文）----
    sup_cfg = cfg.get("supplement", {})
    if sup_cfg.get("enabled") and sup_cfg.get("path"):
        sup_path = sup_cfg["path"]
        if not os.path.isabs(sup_path):
            sup_path = os.path.join(base_dir, sup_path)
        if os.path.exists(sup_path):
            n = enrich_records(records, sup_path)
            print(f"  額外資訊注入：附加 {n} 筆人工補充（append-only，不覆寫原文）")

    # ---- 2. 術語探勘 ----
    mining = cfg.get("mining", {})
    candidates = mine_candidates(records, term_store,
                                 min_frequency=mining.get("min_frequency", 2),
                                 min_confidence=mining.get("min_confidence", 0.55),
                                 stopwords=set(mining.get("stopwords", [])))
    print(f"  探勘出 {len(candidates)} 個同義字候選（待人工核可）")

    # ---- 3. 分類（多道遞進）+ 變動指紋 ----
    from .classify import classify_all, seed_buckets_from_data
    from .keywords import generate_keyword_candidates
    from .panorama import build_panorama, panorama_markdown
    # 泛用自舉：分類桶先從來源資料自動長出來
    seed_buckets_from_data(records, cfg.setdefault("classification", {}), dims=("product", "topic"))
    cls = classify_all(records, cfg.get("classification", {}), normalize_fn=term_store.normalize)
    for rec in records:
        if not rec.status:
            rec.status = "未標示"
        rec.thread_id = rec.product or "未分類"
        rec.content_hash = content_hash(rec.body, rec.status, rec.event_time)
    prate = cls["stats"].get("product", {}).get("rate", 0)
    pst = cls["stats"].get("product", {})
    print(f"  歸類率(產品) {prate}%　[關鍵字 {pst.get('kw',0)} · 討論串 {pst.get('thread',0)} · 模糊 {pst.get('fuzzy',0)} · 未分類 {pst.get('unclassified',0)}]")

    # 關鍵字自動生成（SSOT 自動維護候選，待核可）
    kw_candidates = generate_keyword_candidates(records, cfg.get("classification", {}), dim="product")
    print(f"  關鍵字自動生成：{len(kw_candidates)} 個候選（待核可，核可後歸類率自動提升）")

    # 全景分析
    panorama = build_panorama(records)

    # ---- 4. 利害關係人 + 追蹤事項 ----
    registry = build_registry(records)
    actions = extract_actions(records)
    print(f"  利害關係人 {len(registry)} 位 · 追蹤事項 {len(actions)} 件")

    # ---- 5. 增量入庫 + 比對 ----
    out = cfg.get("output", {})
    store_dir = out.get("store_dir", "ssot_store")
    if not os.path.isabs(store_dir):
        store_dir = os.path.join(base_dir, store_dir)
    store = ParquetStore(store_dir)
    df = pd.DataFrame([r.to_dict() for r in records])
    stats = store.upsert(df)
    print(f"  入庫：新增 {stats['added']}、變更 {stats['updated']}、未出現 {stats['stale']}、總計 {stats['total']}")

    # ---- 6. 完整性驗證 ----
    o = audit.overall()
    print(f"  完整性驗證：{o['status']}　涵蓋率 {o['coverage_pct']}%　未解釋遺漏 {o['unexplained_gap']}")

    # ---- 7. 產出 ----
    md = _build_markdown(df, candidates, stats, registry, actions, audit, cfg, detect_md,
                         cls["stats"], kw_candidates, panorama_markdown(panorama))
    if out.get("markdown", True):
        md_path = os.path.join(store_dir, f"weekly_summary_{datetime.now():%Y%m%d}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"  Markdown 摘要：{md_path}")

    with open(os.path.join(store_dir, "term_candidates.json"), "w", encoding="utf-8") as f:
        json.dump([c.__dict__ for c in candidates], f, ensure_ascii=False, indent=2)
    with open(os.path.join(store_dir, "keyword_candidates.json"), "w", encoding="utf-8") as f:
        json.dump(kw_candidates, f, ensure_ascii=False, indent=2)
    with open(os.path.join(store_dir, "stakeholders.json"), "w", encoding="utf-8") as f:
        json.dump({k: {**v.__dict__, "projects": sorted(v.projects)} for k, v in registry.items()},
                  f, ensure_ascii=False, indent=2)
    with open(os.path.join(store_dir, "action_items.json"), "w", encoding="utf-8") as f:
        json.dump([a.__dict__ for a in actions], f, ensure_ascii=False, indent=2)

    pptx_path = None
    try:
        from .slides import build_deck
        pptx_path = os.path.join(store_dir, f"weekly_deck_{datetime.now():%Y%m%d}.pptx")
        build_deck(df, stats, pptx_path, template=out.get("pptx_template"))
        print(f"  簡報草稿：{pptx_path}")
    except Exception as e:
        print(f"  [warn] 簡報草稿略過：{e}")

    return {"records": records, "candidates": candidates, "stats": stats, "markdown": md,
            "df": df, "registry": registry, "actions": actions, "audit": audit, "pptx": pptx_path,
            "classify_stats": cls["stats"], "keyword_candidates": kw_candidates, "panorama": panorama}


def _build_markdown(df, candidates, stats, registry, actions, audit, cfg, detect_md="",
                    classify_stats=None, kw_candidates=None, panorama_md=""):
    L = []
    L.append("# 本週工作進度 SSOT 摘要")
    L.append(f"_產生於 {datetime.now():%Y-%m-%d %H:%M} · 本機處理 · 共 {len(df)} 筆事件_\n")

    L.append(audit.to_markdown() + "\n")
    if detect_md:
        L.append(detect_md + "\n")

    if classify_stats and classify_stats.get("product"):
        s = classify_stats["product"]
        L.append("## 歸類率（產品）")
        L.append(f"- **{s['rate']}%**　救回來源：關鍵字 {s['kw']} · 討論串傳播 {s['thread']} · "
                 f"模糊指派 {s['fuzzy']} · 未分類 {s['unclassified']}\n")

    if panorama_md:
        L.append(panorama_md + "\n")

    L.append("## 進度變化（對比上一版）")
    L.append(f"- 新增 **{stats['added']}** · 變更 **{stats['updated']}** · 本次未出現 **{stats['stale']}**\n")

    if len(df):
        L.append("## 分產品列管")
        for prod, g in df.groupby("product"):
            L.append(f"### {prod or '未分類'}（{len(g)} 項）")
            for _, r in g.iterrows():
                st = f" `{r['status']}`" if r["status"] else ""
                tp = f" · {r['topic']}" if r["topic"] else ""
                who = f" · {r['actor']}" if r["actor"] else ""
                L.append(f"- **[{r['uid']}]** {r['title']}{st}{tp}{who}")
            L.append("")

        L.append("## 狀態總覽 (Pivot)")
        pivot = pd.pivot_table(df, index="product", columns="status",
                               values="uid", aggfunc="count", fill_value=0)
        L.append("```"); L.append(pivot.to_string()); L.append("```\n")

    if actions:
        L.append("## 追蹤事項（自動擷取）")
        L.append("| 編號 | 事項 | 負責 | 期限 |")
        L.append("|---|---|---|---|")
        for a in actions:
            L.append(f"| {a.uid} | {a.text} | {a.owner} | {a.due or '—'} |")
        L.append("")

    if registry:
        L.append("## 利害關係人登錄（僅工作事實）")
        L.append("| 對象 | 單位 | 寄件 | 收件 | 參與度(客觀) | 關聯案 |")
        L.append("|---|---|---|---|---|---|")
        for s in sorted(registry.values(), key=lambda x: -x.total()):
            projs = ", ".join(sorted(p for p in s.projects if p)) or "—"
            L.append(f"| {s.handle} | {s.unit or '—'} | {s.as_sender} | {s.as_recipient} | {s.engagement} | {projs} |")
        L.append("")

    L.append("## 術語候選（待你核可，系統不自動合併）")
    if candidates:
        L.append("| 候選詞 | 提議正規詞 | 信心 | 訊號 |")
        L.append("|---|---|---|---|")
        for c in candidates:
            L.append(f"| {c.surface} | {c.canonical} | {c.confidence} | {', '.join(c.signals)} |")
    else:
        L.append("_本次無新候選。_")

    if kw_candidates:
        L.append("\n## 關鍵字自動生成（待核可 → 核可後歸類率自動提升）")
        L.append("| 分類桶 | 建議關鍵字 | 鑑別分數 | 出現 |")
        L.append("|---|---|---|---|")
        for c in kw_candidates[:20]:
            L.append(f"| {c['bucket']} | {c['term']} | {c['score']} | {c['count']} |")
    return "\n".join(L)
