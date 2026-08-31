"""企業系統 SSOT 對齊預設庫（因欄位標準，對齊可事先完成）。

SAP（MM/PP/SD）、MS Project、Outlook/Gmail 都是標準系統，欄位名稱是已知的，
所以把「原始欄位 → 統一 Record」的對照預先內建成 preset，現場不必再對。

治理：每個 preset 標明 anchor_id_field（原始單號欄位）——這個值原封不動存進
source_ref（不改變原始編號），系統另外用 numbering 生成自己的 uid（自動編號）。
兩軌並存，可回溯。使用者仍可在 config 覆寫任何一條對照。
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

# 每個 preset：field_map（來源欄位→Record欄位）、anchor_id_field（原始單號）、note
ENTERPRISE_PRESETS = {
    # ---- SAP MM 物料管理 / 採購 ----
    "sap_mm": {
        "note": "SAP MM 採購單 / 物料主檔",
        "anchor_id_field": "EBELN",          # 採購單號（原始不動）
        "field_map": {
            "MAKTX": "title",                # 物料說明
            "MATNR": "product",              # 物料號
            "LIFNR": "actor",                # 供應商代碼
            "NAME1": "counterparts",         # 供應商名稱
            "EBELN": "source_ref",           # 採購單號
            "BEDAT": "event_time",           # 採購單日期
            "MENGE": "body",                 # 數量（併入 body 供 NLP）
            "ELIKZ": "status",               # 交貨完成註記
        },
    },
    # ---- SAP PP 生產計劃 ----
    "sap_pp": {
        "note": "SAP PP 生產訂單 / 計劃訂單",
        "anchor_id_field": "AUFNR",          # 生產訂單號
        "field_map": {
            "MATNR": "product",              # 生產物料
            "AUFNR": "source_ref",           # 生產訂單號
            "GSTRP": "event_time",           # 基本開始日
            "DISPO": "actor",                # 生產排程員
            "STTXT": "status",               # 訂單狀態文字
            "GAMNG": "body",                 # 訂單數量
        },
    },
    # ---- SAP SD 銷售與配銷 ----
    "sap_sd": {
        "note": "SAP SD 銷售訂單 / 交貨",
        "anchor_id_field": "VBELN",          # 銷售單號
        "field_map": {
            "VBELN": "source_ref",           # 銷售單據號
            "KUNNR": "actor",                # 客戶代碼
            "NAME1": "counterparts",         # 客戶名稱
            "MATNR": "product",              # 銷售物料
            "AUDAT": "event_time",           # 單據日期
            "NETWR": "body",                 # 淨值金額
            "GBSTK": "status",               # 整體處理狀態
        },
    },
    # ---- MS Project ----
    "ms_project": {
        "note": "MS Project 任務表（.xml 另存）",
        "anchor_id_field": "UID",            # 任務原生 UID
        "field_map": {
            "Name": "title",                 # 任務名稱
            "UID": "source_ref",             # 任務 UID
            "ResourceNames": "actor",        # 負責資源
            "Start": "event_time",           # 開始日
            "PercentComplete": "status",     # 完成度→狀態
            "WBS": "thread_id",              # WBS 結構碼（串接用）
            "Text1": "raw_keys",             # 自訂欄位（常放 ERP 單號）
            "Notes": "body",
        },
    },
    # ---- PLM 工程變更 ECM（最高價值：「為什麼改」）----
    "plm_ecm": {
        "note": "PLM 工程變更主檔 / ECR / ECN",
        "anchor_id_field": "ChangeNumber",   # 變更號 AENR（原始不動）
        "field_map": {
            "ChangeNumber": "source_ref",     # 變更主檔號
            "Description": "title",           # 變更說明
            "Reason": "body",                 # 變更原因（關鍵：為什麼改）
            "Requester": "actor",             # 提出人
            "ValidFrom": "event_time",        # 生效日
            "AffectedMaterial": "product",    # 受影響物料
            "Status": "status",               # 變更狀態
            "AffectedBOM": "thread_id",       # 受影響 BOM（串接鍵）
        },
    },
    # ---- PLM 物料清單 BOM ----
    "plm_bom": {
        "note": "PLM 物料清單 BOM（STKO/STPO）",
        "anchor_id_field": "BOMNumber",
        "field_map": {
            "BOMNumber": "source_ref",        # BOM 號
            "ParentMaterial": "product",      # 母件
            "Component": "title",             # 子件
            "Quantity": "body",               # 用量
            "ChangeNumber": "thread_id",      # 綁定的變更號（串 ECM）
            "ValidFrom": "event_time",
        },
    },
    # ---- Outlook ----
    "outlook": {
        "note": "Outlook 郵件（COM / PST）",
        "anchor_id_field": "EntryID",
        "field_map": {
            "Subject": "title", "SenderName": "actor", "To": "counterparts",
            "ReceivedTime": "event_time", "EntryID": "source_ref",
            "ConversationTopic": "thread_id", "Body": "body",
        },
    },
    # ---- Gmail ----
    "gmail": {
        "note": "Gmail（IMAP / API）",
        "anchor_id_field": "Message-ID",
        "field_map": {
            "Subject": "title", "From": "actor", "To": "counterparts",
            "Date": "event_time", "Message-ID": "source_ref", "Body": "body",
        },
    },
}


def list_presets() -> list:
    return [{"key": k, "note": v["note"], "anchor": v["anchor_id_field"],
             "fields": len(v["field_map"])} for k, v in ENTERPRISE_PRESETS.items()]


def apply_preset(rows, preset_key, overrides=None):
    """把來源列(dict)依 preset 對照成 Record。原始單號進 source_ref（不改），
    body 併入未對映的關鍵數值供 NLP。overrides 可覆寫任一對照。"""
    from .schema import Record
    p = ENTERPRISE_PRESETS.get(preset_key)
    if not p:
        raise KeyError(f"未知 preset：{preset_key}")
    fmap = dict(p["field_map"])
    if overrides:
        fmap.update(overrides)
    anchor = p["anchor_id_field"]
    out = []
    for row in rows:
        kw = {}
        extra = []
        for src, val in row.items():
            if src in fmap:
                tgt = fmap[src]
                v = str(val) if val is not None else ""
                # body 可能多來源，累加
                kw[tgt] = (kw.get(tgt, "") + (" " if kw.get(tgt) else "") + v) if tgt == "body" else v
            elif val not in (None, ""):
                extra.append(f"{src}={val}")     # 未對映欄位收進 body 尾端，不丟失
        if extra:
            kw["body"] = (kw.get("body", "") + "　〔" + " · ".join(extra) + "〕").strip()
        # 原始單號原封存 source_ref（若 field_map 沒指到 source_ref 就補）
        if anchor in row and not kw.get("source_ref"):
            kw["source_ref"] = str(row[anchor])
        kw["source_type"] = preset_key
        kw.setdefault("raw_keys", kw.get("title", ""))
        out.append(Record(**kw))
    return out
