"""環境自動偵測層（Plug & Play 核心）。

門外漢不該為了「導入」跟 IT 開會。這層在啟動時自己看環境有什麼、自己接上：
  - 作業系統
  - Outlook 是否可用（你已登入的程式）
  - MS Project 是否可用
  - 常見資料夾(下載/桌面/文件)裡的 Excel/CSV/XML/附件

回傳一份「自動發現的來源清單」，pipeline 直接拿去用 —— 不需要使用者填路徑、不需要 IT。
全程只碰使用者自己有權限的東西，所以不需要任何 IT 權限或開通。
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

import os
import platform


def _try_com(progid: str) -> bool:
    try:
        import win32com.client  # type: ignore
        win32com.client.Dispatch(progid)
        return True
    except Exception:
        return False


def default_scan_roots() -> list[str]:
    home = os.path.expanduser("~")
    cands = [
        os.path.join(home, "Downloads"),
        os.path.join(home, "Desktop"),
        os.path.join(home, "OneDrive", "Desktop"),
        os.path.join(home, "Documents"),
        os.path.join(home, "下載"),
        os.path.join(home, "桌面"),
    ]
    return [c for c in cands if os.path.isdir(c)]


_PROGRESS_HINTS = ("進度", "progress", "tracker", "weekly", "工作", "底稿", "schedule")
_PLM_HINTS = ("plm", "windchill", "teamcenter", "agile", "ecn", "ecr", "bom")
_KNOWN_EXT = {".xml", ".csv", ".xlsx", ".xls", ".pdf", ".docx", ".pptx",
              ".txt", ".md", ".json", ".rtf", ".html", ".htm", ".eml",
              ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
_SKIP_DIRS = {"node_modules", ".git", "__pycache__", "ssot_store", "venv", "envs", "$recycle.bin"}


def _scan_folder(root: str, max_depth: int = 2, max_files: int = 2000) -> dict:
    """遞迴掃描（限深度），讓子資料夾的附件也被找到 → 提高涵蓋率。
    同時記錄『無法歸類』的檔案，供查核自動偵測能力。"""
    found = {"excel_csv": [], "msproject_xml": [], "plm": [], "attachments": [],
             "unclassified": [], "ext_hist": {}}
    base_depth = root.rstrip(os.sep).count(os.sep)
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d.lower() not in _SKIP_DIRS]
        if dirpath.rstrip(os.sep).count(os.sep) - base_depth >= max_depth:
            dirnames[:] = []
        for n in sorted(filenames):
            if count >= max_files:
                return found
            count += 1
            p = os.path.join(dirpath, n)
            low = n.lower()
            ext = os.path.splitext(low)[1]
            found["ext_hist"][ext] = found["ext_hist"].get(ext, 0) + 1
            if ext == ".xml":
                found["msproject_xml"].append(p)
            elif ext in (".csv", ".xlsx", ".xls"):
                (found["plm"] if any(h in low for h in _PLM_HINTS) else found["excel_csv"]).append(p)
            elif ext in (".pdf", ".docx", ".pptx", ".rtf", ".html", ".htm", ".eml",
                         ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"):
                found["attachments"].append(p)
            elif ext not in _KNOWN_EXT:
                found["unclassified"].append(p)
    return found


def probe(scan_roots: list[str] | None = None, demo_dir: str | None = None) -> dict:
    """偵測環境，回傳能力與發現的來源。"""
    info = {
        "os": platform.system(),
        "outlook": False,
        "msproject": False,
        "scan_roots": [],
        "discovered": {"excel_csv": [], "msproject_xml": [], "plm": [], "attachments": [],
                       "unclassified": [], "ext_hist": {}},
    }
    if info["os"] == "Windows":
        info["outlook"] = _try_com("Outlook.Application")
        info["msproject"] = _try_com("MSProject.Application")

    roots = scan_roots or default_scan_roots()
    # 沒掃到任何真實資料夾 → 退回示範資料夾，讓門外漢第一次就有東西看
    if not roots and demo_dir and os.path.isdir(demo_dir):
        roots = [demo_dir]
    info["scan_roots"] = roots

    for r in roots:
        part = _scan_folder(r)
        for k, v in part.items():
            if k == "ext_hist":
                for ext, c in v.items():
                    info["discovered"]["ext_hist"][ext] = info["discovered"]["ext_hist"].get(ext, 0) + c
            else:
                info["discovered"][k].extend(v)
    return info


def verify_detection(info: dict) -> dict:
    """查核自動偵測能力：回報分類涵蓋、未歸類檔案、可疑遺漏。
    讓使用者一眼確認『偵測有沒有漏看東西』。"""
    d = info["discovered"]
    classified = (len(d["excel_csv"]) + len(d["msproject_xml"]) +
                  len(d["plm"]) + len(d["attachments"]))
    total = classified + len(d["unclassified"])
    return {
        "scan_roots": info["scan_roots"],
        "total_files": sum(d["ext_hist"].values()),
        "classified": classified,
        "unclassified": len(d["unclassified"]),
        "classify_rate": round(100 * classified / total, 1) if total else 100.0,
        "ext_histogram": dict(sorted(d["ext_hist"].items(), key=lambda x: -x[1])),
        "unclassified_samples": d["unclassified"][:15],
        "outlook": info["outlook"],
        "msproject": info["msproject"],
    }


def detection_markdown(info: dict) -> str:
    v = verify_detection(info)
    L = ["## 自動偵測查核"]
    L.append(f"- 掃描位置：{', '.join(v['scan_roots']) or '（無）'}")
    L.append(f"- 檔案總數 {v['total_files']} · 已歸類 {v['classified']} · "
             f"未歸類 {v['unclassified']} · 歸類率 {v['classify_rate']}%")
    L.append(f"- Outlook {'可用' if v['outlook'] else '未偵測'} · "
             f"MS Project {'可用' if v['msproject'] else '未偵測'}")
    if v["ext_histogram"]:
        hist = " · ".join(f"{k or '無副檔名'}×{n}" for k, n in v["ext_histogram"].items())
        L.append(f"- 副檔名分布：{hist}")
    if v["unclassified_samples"]:
        L.append("- 未歸類樣本（可考慮加支援）：")
        for p in v["unclassified_samples"]:
            L.append(f"  - {os.path.basename(p)}")
    return "\n".join(L)


def build_sources(info: dict) -> list[dict]:
    """把偵測結果轉成 pipeline 能吃的 sources 清單（自動接上）。

    用『檔案層級』而非資料夾層級，避免 excel_csv 把已歸類為 PLM/XML 的同資料夾檔案重複讀取。
    每日重跑會重新偵測，新檔案下次自動納入。
    """
    sources = []
    disc = info["discovered"]

    for p in disc["excel_csv"]:
        sources.append({"type": "excel_csv", "path": p, "enabled": True, "_auto": True})

    for x in disc["msproject_xml"]:
        sources.append({"type": "msproject", "path": x, "enabled": True, "_auto": True})

    for p in disc["plm"]:
        sources.append({"type": "plm", "path": p, "enabled": True, "_auto": True})

    # Outlook：可用就自動掛上（預設近 3 個月，仍只讀你自己的信）
    if info.get("outlook"):
        sources.append({"type": "outlook_desktop", "enabled": True, "months": 3, "_auto": True})

    return sources


def summarize(info: dict) -> str:
    d = info["discovered"]
    parts = [
        f"作業系統 {info['os']}",
        f"Outlook {'可用' if info['outlook'] else '未偵測到'}",
        f"MS Project {'可用' if info['msproject'] else '未偵測到'}",
        f"Excel/CSV {len(d['excel_csv'])} 檔",
        f"MSProject XML {len(d['msproject_xml'])} 檔",
        f"PLM 匯出 {len(d['plm'])} 檔",
        f"附件 {len(d['attachments'])} 檔",
    ]
    return " · ".join(parts)
