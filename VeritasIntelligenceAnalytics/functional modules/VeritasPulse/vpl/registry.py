"""VeritasPulse module registry.

Single declarative manifest of every functional module/view. This is the
'easy to modularly adjust' surface:
  - add a feature  -> add one dict entry
  - hide a feature -> set "enabled": False
  - reorder nav    -> reorder the list
The app generator reads ENABLED entries and emits exactly those views.
Append-only friendly: never renumber ids, only add.
"""
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

MODULES = [
    # id        group     label                 icon       enabled
    {"id": "dash",   "group": "INTEL",  "label": "Dashboard",     "icon": "grid",     "enabled": True},
    {"id": "today",  "group": "EXEC",   "label": "每日清單",       "icon": "check",    "enabled": True},
    {"id": "cal",    "group": "EXEC",   "label": "月曆 Calendar",  "icon": "cal",      "enabled": True},
    {"id": "timeline","group": "EXEC",  "label": "時間軸 Timeline","icon": "dots",    "enabled": True},
    {"id": "board",  "group": "EXEC",   "label": "看板 Board",     "icon": "rows",     "enabled": True},
    {"id": "gantt",  "group": "PLAN",   "label": "甘特 Gantt",     "icon": "rows",     "enabled": True},
    {"id": "flow",   "group": "PLAN",   "label": "流程 Flow",      "icon": "flow",     "enabled": True},
    {"id": "seq",    "group": "EXEC",   "label": "燈號 Sequence",  "icon": "dots",     "enabled": True},
    {"id": "budget", "group": "FIN",    "label": "預算 Budget",    "icon": "chart",    "enabled": True},
    {"id": "ledger", "group": "FIN",    "label": "記帳 Ledger",    "icon": "coins",    "enabled": True},
    {"id": "people", "group": "PEOPLE", "label": "利害關係人",      "icon": "users",    "enabled": True},
    {"id": "contacts","group": "PEOPLE", "label": "聯絡人 Contacts","icon": "users",   "enabled": True},
    {"id": "team",   "group": "PEOPLE", "label": "團隊 Team",       "icon": "users",   "enabled": True},
    {"id": "notes",  "group": "NOTES",  "label": "筆記 Notes",      "icon": "book",    "enabled": True},
    {"id": "notebook","group": "NOTES", "label": "LLM Notebook",   "icon": "ai",      "enabled": True},
    {"id": "matrix", "group": "INTEL",  "label": "進度矩陣 Matrix", "icon": "grid",    "enabled": True},
    {"id": "connect","group": "EXEC",   "label": "連線 Connections","icon": "flow",    "enabled": True},
    {"id": "meetings","group": "MEETINGS","label": "會議 Meetings",  "icon": "users",   "enabled": True},
    {"id": "review", "group": "MEETINGS","label": "逐字稿審閱",      "icon": "check",   "enabled": True},
    {"id": "minutes","group": "MEETINGS","label": "會議紀錄 Minutes","icon": "book",    "enabled": True},
    {"id": "settings","group": "SYS",    "label": "BASE 設定",      "icon": "gauge",   "enabled": True},
    {"id": "res",    "group": "PEOPLE", "label": "資源 Resources", "icon": "gauge",    "enabled": True},
    {"id": "risk",   "group": "RISK",   "label": "風險 Risk",      "icon": "alert",    "enabled": True},
]

GROUP_LABEL = {
    "INTEL": "Intelligence", "EXEC": "執行", "PLAN": "規劃",
    "FIN": "財務", "PEOPLE": "人與關係", "RISK": "風險", "NOTES": "筆記與計畫",
    "MEETINGS": "會議", "SYS": "系統",
}


def enabled_modules():
    return [m for m in MODULES if m.get("enabled", True)]
