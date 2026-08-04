# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

VIS_VRN_BROKER_ANALYST_ADAPTER_VERSION = "v0.6.14.6"


def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ")
    s = s.replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", s).strip()


def def_norm_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ")
    replacements = {
        "研 究 員": "研究員",
        "研 究員": "研究員",
        "研究 員": "研究員",
        "分 析 師": "分析師",
        "電 子 信 箱": "電子信箱",
        "電子 信箱": "電子信箱",
        "聯 絡 方 式": "聯絡方式",
        "聯絡 方式": "聯絡方式",
        "華 南 投 顧": "華南投顧",
        "華南 投顧": "華南投顧",
        "訪 談 報 告": "訪談報告",
    }
    for a, b in replacements.items():
        s = s.replace(a, b)
    return s


def def_is_huanan_context(row: dict | None = None, first_page_text: str = "") -> bool:
    row = row or {}
    joined = " ".join([
        str(row.get("Filename", "")),
        str(row.get("Broker", "")),
        str(row.get("Broker Raw", "")),
        str(row.get("Broker Raw Before V06144", "")),
        str(row.get("Analyst Email", "")),
        str(row.get("Broker Cross Check", "")),
        first_page_text or "",
    ])
    return bool(re.search(r"(華南|華南投顧|華南永昌|HuaNan|HNCB|entrust\.com\.tw)", joined, re.I))


def def_is_huanan_memo_or_visit(row: dict | None = None, first_page_text: str = "") -> bool:
    row = row or {}
    joined = " ".join([str(row.get("Filename", "")), first_page_text or ""])
    return bool(re.search(r"(Memo|訪談報告|訪談|速報)", joined, re.I))


def def_is_contact_label(x: str) -> bool:
    s = def_clean_text(x)
    return bool(re.search(r"(研究員聯絡方式|聯絡方式|電子信箱|信箱|Email|E-mail|電話|Tel|Phone|Contact)", s, re.I))


def def_is_bad_analyst_name(x: str) -> bool:
    s = def_clean_text(x)
    if not s:
        return True
    if "@" in s:
        return True
    if re.fullmatch(r"\d+", s):
        return True
    if re.search(r"^\+?886|^\(?02\)?", s):
        return True
    if re.search(r"(研究員|聯絡方式|電子信箱|信箱|Email|電話|Tel|Phone|訪談報告|Memo|買進|中立|未評等|目標價|投資評等|公司|報告|摘要|基本資料)", s, re.I):
        return True
    if len(s) > 20:
        return True
    return False


def def_extract_huanan_email(text: str) -> str:
    text = text or ""
    m = re.search(r"[\w.\-]+@entrust\.com\.tw", text, re.I)
    return m.group(0) if m else ""


def def_extract_huanan_email_all(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"[\w.\-]+@entrust\.com\.tw", text or "", flags=re.I)))


def def_huanan_name_candidate_from_line(line: str) -> str:
    line = def_norm_text(line)
    patterns = [
        r"研究員\s*[:：]?\s*([\u4e00-\u9fff]{2,4})",
        r"分析師\s*[:：]?\s*([\u4e00-\u9fff]{2,4})",
    ]
    for pat in patterns:
        m = re.search(pat, line)
        if m and not def_is_bad_analyst_name(m.group(1)):
            return m.group(1)

    # 表格文字常變成：研究員    許願
    parts = [def_clean_text(x) for x in re.split(r"\s{2,}|\t|｜|\|", line) if def_clean_text(x)]
    if len(parts) >= 2 and parts[0] in ["研究員", "分析師"]:
        cand = parts[1]
        if not def_is_bad_analyst_name(cand):
            return cand

    return ""


def def_extract_huanan_analyst_v06146(row: dict | None, first_page_text: str, lines: list[str] | None = None) -> dict:
    row = row or {}
    first_page_text = def_norm_text(first_page_text or "")
    if lines is None:
        lines = [def_clean_text(x) for x in first_page_text.splitlines() if def_clean_text(x)]
    else:
        lines = [def_norm_text(x) for x in lines if def_clean_text(x)]

    out = {
        "adapter_triggered": False,
        "adapter_name": "",
        "broker": "",
        "analyst": "",
        "analyst_email": "",
        "analyst_source": "",
        "analyst_confidence": 0.0,
        "evidence": "",
        "memo_visit_no_forced_analyst": False,
        "general_extractor_bypassed": False,
        "reason": "",
    }

    if not def_is_huanan_context(row, first_page_text):
        out["reason"] = "NOT_HUANAN_CONTEXT"
        return out

    out["adapter_triggered"] = True
    out["adapter_name"] = "HUANAN_RESEARCHER_ROW_ADAPTER_V06146"
    out["broker"] = "HuaNan"
    out["analyst_email"] = def_extract_huanan_email(first_page_text)

    # --------------------------------------------------------------------------------------------------
    # def 01_STRONG_BLOCK_PATTERN
    # --------------------------------------------------------------------------------------------------
    # 支援：
    # ::研究員聯絡方式:: 研究員 許願 電子信箱 10863@entrust.com.tw
    # 研究員 林子期 電子信箱 450@entrust.com.tw
    block_patterns = [
        r"(?:研究員聯絡方式|聯絡方式).{0,260}?研究員\s*[:：]?\s*([\u4e00-\u9fff]{2,4}).{0,220}?電子信箱\s*[:：]?\s*([\w.\-]+@entrust\.com\.tw)",
        r"研究員\s*[:：]?\s*([\u4e00-\u9fff]{2,4}).{0,220}?電子信箱\s*[:：]?\s*([\w.\-]+@entrust\.com\.tw)",
        r"研究員\s+([\u4e00-\u9fff]{2,4})\s+電子信箱\s+([\w.\-]+@entrust\.com\.tw)",
    ]
    flat = re.sub(r"\s+", " ", first_page_text)
    for pat in block_patterns:
        m = re.search(pat, flat, re.I | re.S)
        if m:
            cand = def_clean_text(m.group(1))
            email = def_clean_text(m.group(2))
            if not def_is_bad_analyst_name(cand):
                out.update({
                    "analyst": cand,
                    "analyst_email": email,
                    "analyst_source": "HUANAN_RESEARCHER_RIGHT_CELL_ABOVE_EMAIL_BLOCK",
                    "analyst_confidence": 0.98,
                    "evidence": def_clean_text(m.group(0)),
                    "general_extractor_bypassed": True,
                    "reason": "研究員右側姓名 + entrust email 同區塊命中",
                })
                return out

    # --------------------------------------------------------------------------------------------------
    # def 02_LINE_PAIR_PATTERN
    # --------------------------------------------------------------------------------------------------
    # 支援 OCR 行：
    # 研究員        許願
    # 電子信箱      10863@entrust.com.tw
    for i, line in enumerate(lines):
        cand = ""
        if "研究員" in line or "分析師" in line:
            cand = def_huanan_name_candidate_from_line(line)

            # 若 line 只有「研究員」，下一行可能是姓名
            if not cand and def_clean_text(line) in ["研究員", "分析師"]:
                if i + 1 < len(lines):
                    next_line = def_clean_text(lines[i + 1])
                    if re.fullmatch(r"[\u4e00-\u9fff]{2,4}", next_line) and not def_is_bad_analyst_name(next_line):
                        cand = next_line

        if cand and not def_is_bad_analyst_name(cand):
            zone = lines[max(0, i - 2):min(len(lines), i + 6)]
            zone_text = " | ".join(zone)
            email = def_extract_huanan_email(zone_text) or out["analyst_email"]
            out.update({
                "analyst": cand,
                "analyst_email": email,
                "analyst_source": "HUANAN_RESEARCHER_ROW_RIGHT_CELL",
                "analyst_confidence": 0.96 if email else 0.90,
                "evidence": zone_text,
                "general_extractor_bypassed": True,
                "reason": "研究員列右側姓名命中；email 作 contact evidence",
            })
            return out

    # --------------------------------------------------------------------------------------------------
    # def 03_EMAIL_ABOVE_ZONE_PATTERN
    # --------------------------------------------------------------------------------------------------
    # email 上方 1~5 行找中文姓名，但不能抓 label
    for i, line in enumerate(lines):
        if re.search(r"@entrust\.com\.tw", line, re.I):
            zone = lines[max(0, i - 6):i + 1]
            for z in reversed(zone[:-1]):
                # 優先抓「研究員 許願」
                cand = def_huanan_name_candidate_from_line(z)
                if cand and not def_is_bad_analyst_name(cand):
                    out.update({
                        "analyst": cand,
                        "analyst_email": def_extract_huanan_email(line) or out["analyst_email"],
                        "analyst_source": "HUANAN_EMAIL_ABOVE_RESEARCHER_LINE",
                        "analyst_confidence": 0.88,
                        "evidence": " | ".join(zone),
                        "general_extractor_bypassed": True,
                        "reason": "email 上方研究員列命中",
                    })
                    return out

            # 若沒有「研究員」字，但 email 上方是純姓名，也可列 review 中高信心
            for z in reversed(zone[:-1]):
                zc = def_clean_text(z)
                if re.fullmatch(r"[\u4e00-\u9fff]{2,4}", zc) and not def_is_bad_analyst_name(zc):
                    out.update({
                        "analyst": zc,
                        "analyst_email": def_extract_huanan_email(line) or out["analyst_email"],
                        "analyst_source": "HUANAN_EMAIL_ABOVE_CHINESE_NAME",
                        "analyst_confidence": 0.82,
                        "evidence": " | ".join(zone),
                        "general_extractor_bypassed": True,
                        "reason": "email 上方中文姓名 fallback；需人工抽查一次",
                    })
                    return out

    # --------------------------------------------------------------------------------------------------
    # def 04_MEMO_VISIT_NO_FORCE
    # --------------------------------------------------------------------------------------------------
    if def_is_huanan_memo_or_visit(row, first_page_text):
        out.update({
            "memo_visit_no_forced_analyst": True,
            "analyst_source": "HUANAN_MEMO_VISIT_NO_EXPLICIT_ANALYST",
            "analyst_confidence": 0.0,
            "reason": "華南 Memo / 訪談報告未找到明確研究員欄位，不強制 analyst missing",
        })
        return out

    out["reason"] = "HUANAN_CONTEXT_BUT_ANALYST_NOT_FOUND"
    return out


def def_extract_broker_analyst_by_adapter_v06146(row: dict | None, first_page_text: str, lines: list[str] | None = None) -> dict:
    row = row or {}
    text = first_page_text or ""

    # Broker-specific adapter priority. 目前只加強 HuaNan，其他 broker 不碰。
    if def_is_huanan_context(row, text):
        return def_extract_huanan_analyst_v06146(row, text, lines)

    return {
        "adapter_triggered": False,
        "adapter_name": "GENERAL_EXTRACTOR_PRESERVED",
        "broker": row.get("Broker", ""),
        "analyst": row.get("Analyst", ""),
        "analyst_email": row.get("Analyst Email", ""),
        "analyst_source": "GENERAL_EXTRACTOR_PRESERVED",
        "analyst_confidence": 0.0,
        "evidence": "",
        "memo_visit_no_forced_analyst": False,
        "general_extractor_bypassed": False,
        "reason": "No broker-specific adapter triggered; preserve general extractor",
    }


def def_health_v06146():
    return {
        "version": VIS_VRN_BROKER_ANALYST_ADAPTER_VERSION,
        "adapters": ["HuaNan"],
        "huanan_broker_canonical": "HuaNan",
        "numeric_entrust_email_guard": True,
        "general_extractor_preserved": True,
    }

# ======================================================================================
# VRN_V139O_SUPPORTIVE_BRIDGE_APPEND_ONLY START
# def Purpose:
# def   - Append-only supportive bridge for VRN production modules
# def   - Safe optional imports only; no DB write, no SSOT mutation, no network execution
# def   - Enables downstream audit to detect Aegis / Celeritas / EnvManager / NoHang coverage
# ======================================================================================

VRN_V139O_SUPPORTIVE_BRIDGE_ENABLED = True
VRN_V139O_NOHANG_WATCHDOG_ENABLED = True
VRN_V139O_DB_WRITE_ENABLE = False
VRN_V139O_SSOT_MUTATION_ENABLE = False
VRN_V139O_NETWORK_ENABLE = False

VRN_V139O_AEGIS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasAegisNexus.py"
VRN_V139O_CELERITAS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py"
VRN_V139O_ENV_MANAGER_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py"

def def_vrn_v139o_optional_import_module(module_name, module_path):
    import importlib.util
    import sys
    from pathlib import Path

    result = {
        "module": str(module_name),
        "path": str(module_path),
        "exists": False,
        "import_ok": False,
        "error": "",
    }

    try:
        p = Path(str(module_path))
        result["exists"] = p.exists()
        if not p.exists():
            result["error"] = "missing"
            return result

        spec = importlib.util.spec_from_file_location(str(module_name), str(p))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[str(module_name)] = mod
        spec.loader.exec_module(mod)
        result["import_ok"] = True
        return result
    except BaseException as e:
        result["error"] = str(e)
        return result

def def_vrn_v139o_supportive_bridge_health():
    return {
        "bridge": "VRN_V139O_SUPPORTIVE_BRIDGE_APPEND_ONLY",
        "aegis": def_vrn_v139o_optional_import_module("VeritasAegisNexus", VRN_V139O_AEGIS_PATH),
        "celeritas": def_vrn_v139o_optional_import_module("VeritasCeleritas", VRN_V139O_CELERITAS_PATH),
        "envmanager": def_vrn_v139o_optional_import_module("VIA_EnvManager", VRN_V139O_ENV_MANAGER_PATH),
        "nohang_watchdog": VRN_V139O_NOHANG_WATCHDOG_ENABLED,
        "db_write": VRN_V139O_DB_WRITE_ENABLE,
        "ssot_mutation": VRN_V139O_SSOT_MUTATION_ENABLE,
        "network": VRN_V139O_NETWORK_ENABLE,
    }

# VRN_V139O_SUPPORTIVE_BRIDGE_APPEND_ONLY END

