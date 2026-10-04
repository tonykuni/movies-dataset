#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL140_HandoverConsole v0105 — 薄尾:收據雜湊的換行正規化補齊文字檔類型(.html · .css · .js · …)

實錄(2026-10-05,PR #462 CI):`VCGC-REQ152:vdf_fetch_groups_v0102` 在 Windows 全綠閘判 EVIDENCE_INVALID。
  查明兩個原因,分開修:
  ① CI 本身:gate job 的 sparse checkout 沒簽出 `.html` → ui_templates 範本不在 → 「dependency changed」+「-1 gone」。
     修在工作流(.github/workflows/via-master-control-ui.yml 補 ui_templates 路徑),不在本檔。
  ② 本檔:v0101 sha() 只對 .py/.ps1/.json/.jsonl/.md/.yml/.txt/.log 做 CRLF→LF;Git for Windows 預設 autocrlf=true,
     工作站簽出的 .html/.css/.js 等文字檔是 CRLF → Linux 開的收據到工作站一律「dependency changed」。
  本版:sha() 的文字類型補上 TEXT_SUFFIXES_V0105(含 v0101 原有的);LF 檔雜湊不變 → 既有收據全部照舊有效。
  裝進 v0101 的模組全域(audit · run_case · evidence_status 都查它),其餘照 v0104。只收 VCGC 呼叫。零網路。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import hashlib
import importlib.util
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL140_HandoverConsole"
ENGINE = Path(__file__).stem
VERSION = "v0105"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
VIA = PRIOR.VIA
POLICY = PRIOR.POLICY
BASE = PRIOR.BASE                               # v0101:sha 定義處;audit / run_case / evidence_status 都查它的模組全域
_V0101_SHA = BASE.sha

# v0101 原有 8 類 + Windows autocrlf 會轉換的其餘文字檔(UI 範本 · 前端 · 表格文字 · 設定 · PS 模組)
TEXT_SUFFIXES_V0105 = frozenset({
    ".py", ".ps1", ".json", ".jsonl", ".md", ".yml", ".txt", ".log",
    ".yaml", ".html", ".htm", ".css", ".js", ".mjs", ".svg", ".xml", ".csv", ".tsv",
    ".psm1", ".psd1", ".toml", ".ini", ".cfg", ".sql",
})


def __getattr__(name: str):
    return getattr(PRIOR, name)


def sha(path):
    """文字檔先 CRLF→LF 再雜湊(Git 在 Windows 可能簽出成 CRLF);二進位原位元組。LF 檔結果與 v0101 相同。"""
    data = Path(path).read_bytes()
    if Path(path).suffix.lower() in TEXT_SUFFIXES_V0105:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


BASE.sha = sha                                  # v0101 全域 → 本版(v0102 走 PRIOR.sha、v0103/v0104 走 BASE.sha,都同一個模組屬性)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print("[DENY] VCGC entry required")
            return 2
        return selftest()
    return PRIOR.main(argv)


def selftest():
    rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        lf, crlf = b"<html>\n<body>x</body>\n</html>\n", b"<html>\r\n<body>x</body>\r\n</html>\r\n"
        (t / "a.html").write_bytes(lf); (t / "b.html").write_bytes(crlf)
        chk("① .html:CRLF 與 LF 同雜湊(Windows autocrlf 簽出不再判 dependency changed)", sha(t / "a.html") == sha(t / "b.html"))
        chk("② LF 檔雜湊 = v0101(既有收據照舊有效)", sha(t / "a.html") == _V0101_SHA(t / "a.html"))
        for ext in (".py", ".json", ".md"):
            (t / ("c" + ext)).write_bytes(crlf); (t / ("d" + ext)).write_bytes(lf)
        chk("③ v0101 原有 8 類照舊正規化", all(sha(t / ("c" + e)) == sha(t / ("d" + e)) == _V0101_SHA(t / ("c" + e)) for e in (".py", ".json", ".md")))
        (t / "e.png").write_bytes(crlf); (t / "f.png").write_bytes(lf)
        chk("④ 二進位(.png)不正規化:位元組不同 = 雜湊不同", sha(t / "e.png") != sha(t / "f.png") and sha(t / "e.png") == _V0101_SHA(t / "e.png"))
        (t / "g.CSS").write_bytes(crlf); (t / "h.css").write_bytes(lf)
        chk("⑤ 副檔名大小寫不拘(.CSS = .css)", sha(t / "g.CSS") == sha(t / "h.css"))
    chk("⑥ 已裝進 v0101 模組全域(audit · evidence_status 走本版)", BASE.sha is sha)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 檔頭:加速器橋 · 網路橋在(__future__ 之後)· 不碰 TA-Lib",
        "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE")
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    passed = rc == 0 and all(ok)
    print(f"[交接 {VERSION}] 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'FAIL'} · CRLF 正規化 · {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
