"""程式語言偵測與結構萃取（多語言,純 stdlib regex）。

讀懂程式碼:語言判定 + 抽出 函數/類別/匯入/行數,供智慧資產庫索引。
支援 py/js/ts/ps1/sql/java/c/cpp/go/rust/sh/rb/php/kt/swift。
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

import re

LANG_EXT = {
    "py": "Python", "js": "JavaScript", "ts": "TypeScript", "jsx": "JavaScript",
    "ps1": "PowerShell", "psm1": "PowerShell", "sql": "SQL", "java": "Java",
    "c": "C", "h": "C", "cpp": "C++", "cc": "C++", "hpp": "C++",
    "go": "Go", "rs": "Rust", "sh": "Shell", "bash": "Shell",
    "rb": "Ruby", "php": "PHP", "kt": "Kotlin", "swift": "Swift", "r": "R",
}

# 每語言的 函數 / 類別 / 匯入 樣式
_PAT = {
    "Python": {"func": r"^\s*def\s+(\w+)", "class": r"^\s*class\s+(\w+)",
               "import": r"^\s*(?:import|from)\s+([\w\.]+)"},
    "JavaScript": {"func": r"(?:function\s+(\w+)|(\w+)\s*=\s*\([^)]*\)\s*=>)",
                   "class": r"class\s+(\w+)", "import": r"(?:import|require)\s*\(?['\"]?([\w\.\-/@]+)"},
    "TypeScript": {"func": r"(?:function\s+(\w+)|(\w+)\s*=\s*\([^)]*\)\s*=>)",
                   "class": r"(?:class|interface)\s+(\w+)", "import": r"import\s+.*from\s+['\"]([\w\.\-/@]+)"},
    "PowerShell": {"func": r"^\s*function\s+([\w\-]+)", "class": r"^\s*class\s+(\w+)",
                   "import": r"(?:Import-Module|using\s+module)\s+([\w\.\-]+)"},
    "SQL": {"func": r"(?:CREATE\s+(?:OR\s+REPLACE\s+)?(?:FUNCTION|PROCEDURE)\s+(\w+))",
            "class": r"CREATE\s+TABLE\s+(\w+)", "import": r""},
    "Java": {"func": r"(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{",
             "class": r"(?:class|interface)\s+(\w+)", "import": r"^\s*import\s+([\w\.]+)"},
    "C": {"func": r"^\s*[\w\*]+\s+(\w+)\s*\([^;]*\)\s*\{", "class": r"struct\s+(\w+)",
          "import": r"#include\s+[<\"]([\w\./]+)"},
    "C++": {"func": r"^\s*[\w\*:<>]+\s+(\w+)\s*\([^;]*\)\s*\{", "class": r"(?:class|struct)\s+(\w+)",
            "import": r"#include\s+[<\"]([\w\./]+)"},
    "Go": {"func": r"^\s*func\s+(?:\([^)]*\)\s*)?(\w+)", "class": r"type\s+(\w+)\s+struct",
           "import": r"^\s*\"([\w\./\-]+)\""},
    "Rust": {"func": r"^\s*(?:pub\s+)?fn\s+(\w+)", "class": r"(?:struct|enum|trait)\s+(\w+)",
             "import": r"^\s*use\s+([\w:]+)"},
    "Shell": {"func": r"^\s*(?:function\s+)?(\w+)\s*\(\)\s*\{", "class": r"", "import": r"(?:source|\.)\s+([\w\./]+)"},
}
_DEFAULT = {"func": r"", "class": r"", "import": r""}


def detect_language(path="", text=""):
    ext = path.lower().rsplit(".", 1)[-1] if "." in path else ""
    if ext in LANG_EXT:
        return LANG_EXT[ext]
    t = text[:2000]
    if re.search(r"^\s*def\s|^\s*import\s|print\(", t, re.M):
        return "Python"
    if re.search(r"function\s|=>|const\s|require\(", t):
        return "JavaScript"
    if re.search(r"\bSELECT\b|\bCREATE TABLE\b", t, re.I):
        return "SQL"
    if re.search(r"^\s*function\s+[\w\-]+|\$\w+\s*=", t, re.M):
        return "PowerShell"
    return "unknown"


def parse_structure(text, lang=None, path=""):
    lang = lang or detect_language(path, text)
    pat = _PAT.get(lang, _DEFAULT)
    def _find(p):
        if not p:
            return []
        out = []
        for m in re.finditer(p, text, re.M):
            name = next((g for g in m.groups() if g), None) if m.groups() else None
            if name:
                out.append(name)
        return sorted(set(out))
    funcs = _find(pat["func"])
    classes = _find(pat["class"])
    imports = _find(pat["import"])
    return {"language": lang, "functions": funcs, "classes": classes,
            "imports": imports, "loc": text.count("\n") + 1,
            "func_count": len(funcs), "class_count": len(classes)}
