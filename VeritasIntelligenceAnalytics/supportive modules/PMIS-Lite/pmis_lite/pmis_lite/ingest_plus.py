"""末日級統一入口(整合 ingest_engine + 新增能力)。

讀各類(含 json/xml/html/md/code/eml) → 修復(亂碼+表格) → 可驗證擷取幅度
→ 讀懂(程式碼結構/表格/實體) → 轉智慧資產庫 → 全景報告。
只增不減:不改 ingest_engine,新增格式擴充與編排。純 stdlib、離線。
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
import re

from . import ingest_engine as ie
from . import code_parse as cp
from . import table_repair as tr
from . import smart_asset as sa

_CODE_EXT = set(cp.LANG_EXT.keys())
_TEXTY = {"json", "xml", "html", "htm", "md", "markdown", "eml", "yaml", "yml", "ini", "cfg"}


def detect_format_plus(path):
    ext = path.lower().rsplit(".", 1)[-1] if "." in path else ""
    if ext in _CODE_EXT:
        return "code"
    if ext in _TEXTY:
        return ext
    return ie.detect_format(path)


def _read_text(path):
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5", "latin-1"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", "replace")


def extract_code(path):
    text = _read_text(path)
    st = cp.parse_structure(text, path=path)
    a = ie._audit_new(f"code:{path}")
    units = []
    # 每個函數/類別 → 一個單元(可被智慧資產索引)
    for fn in st["functions"]:
        units.append({"text": f"[{st['language']}] function {fn}", "source": path, "kind": "code_func"})
    for cl in st["classes"]:
        units.append({"text": f"[{st['language']}] class {cl}", "source": path, "kind": "code_class"})
    if not units:                                  # 至少產一個檔級摘要單元
        units.append({"text": f"[{st['language']}] {os.path.basename(path)} · {st['loc']} loc", "source": path})
    a["seen"] = len(units)
    a["extracted"] = len(units)
    a["meta"] = st
    return units, a


def extract_texty(path, fmt):
    text = _read_text(path)
    a = ie._audit_new(f"{fmt}:{path}")
    units = []
    if fmt in ("json", "yaml", "yml"):
        try:
            obj = json.loads(text) if fmt == "json" else None
            if isinstance(obj, list):
                for it in obj:
                    units.append({"text": json.dumps(it, ensure_ascii=False)[:500], "source": path})
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    units.append({"text": f"{k}: {json.dumps(v, ensure_ascii=False)[:400]}", "source": path})
        except Exception:
            pass
    if fmt in ("html", "htm"):
        text = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", text)
        text = re.sub(r"(?s)<[^>]+>", " ", text)
    if fmt == "eml":                               # 郵件檔:抽 From/Subject/Body
        for key in ("From", "To", "Subject", "Date"):
            m = re.search(rf"(?im)^{key}:\s*(.+)$", text)
            if m:
                units.append({"text": f"{key}: {m.group(1).strip()}", "source": path, "kind": "email_hdr"})
    if not units:                                  # 其餘:切段落成單元
        for para in re.split(r"\n\s*\n", text):
            p = para.strip()
            if p:
                units.append({"text": p[:500], "source": path})
    a["seen"] = len(units)
    a["extracted"] = len(units)
    return units, a


def extract_any_plus(path):
    fmt = detect_format_plus(path)
    if fmt == "code":
        return extract_code(path)
    if fmt in _TEXTY:
        return extract_texty(path, fmt)
    return ie.extract_any(path)                    # 回退到既有引擎(docx/xlsx/csv/text/image/pdf)


def doomsday_intake(paths, out_json=None):
    """統一末日入口:擷取→修復→驗證幅度→讀懂→智慧資產庫→報告。"""
    all_units, audits = [], []
    for p in paths:
        u, a = extract_any_plus(p)
        all_units.extend(u)
        audits.append(a)
    # 修復:亂碼 + 空白
    vr = ie.validate_correct(all_units)
    # 去重
    uniq, dd = ie.dedup(all_units)
    # 可驗證擷取幅度
    guarantee = ie.guarantee_report(audits)
    # 轉智慧資產庫
    db = sa.build_asset_db(uniq)
    report = {
        "files": len(paths),
        "guarantee": guarantee,           # 擷取幅度可驗證(gap=0 才 PASS)
        "repair": vr,                     # 修復統計 + 無資料流失
        "dedup": dd,
        "asset_db": {"total": db["stats"]["total"], "by_kind": db["stats"]["by_kind"],
                     "by_grade": db["stats"]["by_grade"], "validation": db["stats"]["validation"]},
        "smart_assets": db["records"],
        "intake_pass": guarantee["guarantee_pass"] and vr["verify_pass"]
        and db["stats"]["validation"]["verify_pass"],
    }
    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    return report, db
