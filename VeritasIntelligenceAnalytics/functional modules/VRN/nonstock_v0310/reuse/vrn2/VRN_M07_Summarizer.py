#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""reuse/vrn2/VRN_M07_Summarizer — VIA NLP 轉接(給非個股摘要器 v0310 用的同名介面)。

v0310 引擎只走它的「本地抽取式」路徑:load_libraries() -> dict;extractive_summary_fallback(text, libs) -> str。
實作:本地抽取式(句子切分 · 詞頻權重 · 數字 / 百分比加權 · 不下載模型 · 不連網);
VIA 鎖版 NLP 席位 SUP_MDL866_VIAUnifiedNLPOrchestrator 在時記進 libs(路徑 · 版本),供報告層 brief_via_seat() 經它的 CLI
`text --file <暫存> --brief` 取摘要(子行程 · 一報告一次 · 失敗回空字串照實)。[VIA:NET-BRIDGE] 零網路。
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
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

_SENT = re.compile(r"(?<=[。!?！？;；])\s*|\n+")
_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9\-]{1,}|[一-鿿]{2,4}|\d+(?:\.\d+)?%?")
_STOP = set("的 了 在 是 與 及 和 或 為 也 並 之 其 以 於 將 對 等 由 從 而 但 則 可 已 均 約 較 更 至 到 上 下 中 the and of to in for on with by is are".split())


def _via_root():
    p = Path(__file__).resolve()
    while p.parent != p:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
        p = p.parent
    return None


def load_libraries() -> dict:
    libs = {"mode": "local_extractive", "model_download": False, "nlp_seat": None, "nlp_seat_path": None, "python": sys.executable}
    via = _via_root()
    try:
        lock = json.loads((via / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))
        rel = lock["nlp"]["path"].split("VeritasIntelligenceAnalytics/", 1)[-1]
        p = via / rel
        if p.is_file():
            libs["nlp_seat"], libs["nlp_seat_path"] = p.name, str(p)
    except Exception:                                       # noqa: BLE001 — 席位讀不到就 None(誠實)
        libs["nlp_seat"] = None
    return libs


def _sentences(text: str) -> list:
    return [s.strip() for s in _SENT.split(text or "") if s and len(s.strip()) >= 8]


def extractive_summary_fallback(text: str, libs: dict | None = None, max_sentences: int = 3, max_chars: int = 500) -> str:
    sents = _sentences(text)
    if not sents:
        return (text or "").strip()[:max_chars]
    toks = [t for s in sents for t in _TOKEN.findall(s.lower()) if t not in _STOP]
    freq = Counter(toks)
    scored = []
    for i, s in enumerate(sents):
        ws = [t for t in _TOKEN.findall(s.lower()) if t not in _STOP]
        if not ws:
            continue
        score = sum(freq[t] for t in ws) / (len(ws) ** 0.5)
        score += 1.5 * len(re.findall(r"\d+(?:\.\d+)?%|\d{2,}", s))        # 數字 / 百分比 = 證據句
        score += 0.5 if i == 0 else 0.0
        scored.append((score, i, s))
    top = sorted(sorted(scored, key=lambda z: -z[0])[:max_sentences], key=lambda z: z[1])
    out = " ".join(s for _, _, s in top)
    return out if len(out) <= max_chars else out[:max_chars - 1].rstrip() + "…"


def brief_via_seat(text: str, libs: dict | None = None, timeout: int = 120) -> str:
    """經 VIA NLP 席位的 CLI 取 brief(子行程 · 只讀 · 失敗回空字串);席位不在回空字串。"""
    libs = libs or load_libraries()
    p = libs.get("nlp_seat_path")
    if not p:
        return ""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(text or ""); tmp = f.name
    try:
        r = subprocess.run([sys.executable, p, "text", "--file", tmp, "--brief"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                           env=dict(os.environ, PYTHONUTF8="1", VIA_FROM_VCGC="YES"))
        return (r.stdout or "").strip()[:2000] if r.returncode in (0, 2) else ""
    except (subprocess.TimeoutExpired, OSError):
        return ""
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            tmp = tmp


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond)); print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))
    libs = load_libraries()
    chk("① load_libraries:本地抽取式 · 不下載模型 · NLP 席位 %s" % libs.get("nlp_seat"), libs["mode"] == "local_extractive" and libs["model_download"] is False)
    txt = "CSP 持續加大資本支出,每季都在上調。AI 晶片格局轉變,AI 廠商與 ASIC 廠商合作。預估 2026 年 ASIC 市場規模成長 45%,帶動聯發科(2454)與創意(3443)。免責聲明:本報告僅供參考。"
    s = extractive_summary_fallback(txt, libs)
    chk("② 抽取式摘要:取到有數字那句 · 不超過 500 字 · 不是整段照抄", "45%" in s and len(s) <= 500 and len(s) < len(txt), s[:60])
    chk("③ 空字串 / 短句不炸", extractive_summary_fallback("", libs) == "" and extractive_summary_fallback("短。", libs) == "短。")
    chk("④ 零網路:本檔不 import socket / http / urllib / requests", not re.search(r"^\s*(?:import|from)\s+(?:socket|http|urllib|requests)\b", Path(__file__).read_text(encoding="utf-8"), re.M))
    bad = len(ok) - sum(ok)
    print("[%s] reuse/vrn2 Summarizer 轉接 · %d 項 · 不過 %d" % ("PASS" if not bad else "FAIL", len(ok), bad))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(selftest())
