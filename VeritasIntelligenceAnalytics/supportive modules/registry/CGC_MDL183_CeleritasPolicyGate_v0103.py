#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL183_CeleritasPolicyGate v0103 — 薄尾:無版號舊 .ps1 有帶章的版號尾版 = 版史(不算基線外新缺)

ENV MANAGER(CGC_MDL240 check · 2026-10-04 操作員「完成後請 VCGC 檢查 VCGC 及 VRN VDF 所有工具環境無衝突安裝完畢」)
A6 RED 的唯一一筆:PS 模板章基線外新缺 = Invoke-VIA-Step1-SyncAndLKGC.ps1。它已有版號尾版
Invoke-VIA-Step1-SyncAndLKGC-v0101.ps1(帶模板章);舊檔 L70 不能改。掃橋器 v0110 · 覆蓋探針 v0106 早就把
「無版號舊檔有同族 -vNNNN」當版史,只有本閘還算紅 —— 同一件事兩把尺(L05)。本版只做一件事:
v0102 掃完後,基線外新缺裡「無版號、且同夾有同族 -vNNNN / _vNNNN 尾版、尾版帶模板章」的,改記 ps.history;
尾版沒章的照紅(不放水)。**還有活冊指名呼叫它就照紅**(PR #446 Codex P1:有帶章兄弟不等於舊檔已退役):
登錄冊夾 registry 下每個 SSOT 家族的尾版 JSON,只要有非敘述欄位的字串**精確**指名舊檔名(glob 與版號名不算)= 仍是入口,
記 ps.history_blocked(附呼叫者),留在新缺;只增的 .jsonl 號冊是身分紀錄、不是呼叫者,不算;
冊本身在 retired_entries 宣告退役的檔名(只增律要保留在檔單裡,例:子系統包冊 v0103)= 該冊不算呼叫。其餘判準、基線、已還債帳全照 v0102。唯讀零網路。
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


import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL183_CeleritasPolicyGate"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("cgc_mdl183_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0101 = PRIOR.PRIOR
VERSION = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
PS_MARK = PRIOR.PS_MARK
_SCAN_V0101 = V0101.scan
_VER_RX = re.compile(r"[-_]v(\d{4})$", re.I)


def __getattr__(name):
    return getattr(PRIOR, name)


def versioned_tail_v0103(path: Path) -> Path | None:
    """無版號 .ps1 的同夾同族版號尾版(-vNNNN / _vNNNN 取最大);本身有版號或沒有同族 = None。"""
    if _VER_RX.search(path.stem):
        return None
    sibs = [p for p in path.parent.glob(path.stem + "*.ps1")
            if p != path and _VER_RX.search(p.stem) and _VER_RX.sub("", p.stem) == path.stem]
    return max(sibs, key=lambda p: int(_VER_RX.search(p.stem).group(1))) if sibs else None


_PROSE_KEYS = ("why", "evidence", "note", "scope", "reason", "requirement", "quote", "text", "topic", "next", "doc", "role",
               "batch", "source", "goal", "what", "summary", "desc", "comment", "lesson")


def _tail_books_v0103(reg: Path) -> list:
    """registry 夾每個 SSOT JSON 家族的尾版(無版號的 JSON 也算一本);.jsonl 只增號冊不收。"""
    fams = {}
    for p in reg.glob("*.json"):
        m = re.match(r"^(.*)_v(\d{4})$", p.stem)
        key, ver = (m.group(1), int(m.group(2))) if m else (p.stem, -1)
        if key not in fams or ver > fams[key][0]:
            fams[key] = (ver, p)
    return sorted(p for _, p in fams.values())


def live_callers_v0103(name: str, root: Path) -> list:
    """尾版 SSOT 冊裡非敘述欄位精確指名 name 的位置(冊名:路徑);glob / 版號名不算。"""
    rx = re.compile(r"(?<![\w.*-])" + re.escape(name) + r"(?![\w*])")
    reg = Path(root) / "supportive modules" / "registry"
    hits = []

    def walk(o, path, book):
        if isinstance(o, dict):
            for k, v in o.items():
                if not any(str(k).lower().startswith(w) for w in _PROSE_KEYS):
                    walk(v, f"{path}.{k}", book)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]", book)
        elif isinstance(o, str) and rx.search(o):
            hits.append(f"{book}:{path}")
    if reg.is_dir():
        for p in _tail_books_v0103(reg):
            try:
                book = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(book, dict) and name in (book.get("retired_entries") or []):
                continue                               # 冊自己宣告它已退役(只增律保留在檔單)= 不是呼叫
            walk(book, "", p.name)
    return hits


def scan(root: Path | None = None) -> dict:
    """同 v0102 掃描;基線外新缺裡有帶章版號尾版、且尾版冊沒有活呼叫的無版號舊檔 → ps.history;尾版沒章 / 仍被指名照紅。"""
    s = _SCAN_V0101(root)
    ps = s.get("ps")
    if not isinstance(ps, dict):
        return s
    base = Path(root) if root else V0101.VIA
    keep, hist, blocked = [], [], []
    for rp in ps.get("new_missing") or []:
        tail = versioned_tail_v0103(base / rp)
        if tail is not None and PS_MARK in tail.read_text(encoding="utf-8", errors="ignore"):
            callers = live_callers_v0103(Path(rp).name, base)
            if callers:
                blocked.append({"file": rp, "tail": str(tail.relative_to(base)).replace("\\", "/"), "callers": callers[:8]})
                keep.append(rp)
            else:
                hist.append({"file": rp, "tail": str(tail.relative_to(base)).replace("\\", "/")})
        else:
            keep.append(rp)
    ps["new_missing"], ps["history"], ps["history_blocked"] = keep, hist, blocked
    ps["state"] = "GREEN" if not keep else "RED"
    py = s.get("py") or {}
    s["state"] = "GREEN" if ps["state"] == "GREEN" and py.get("state") == "GREEN" else "RED"
    return s


def _install_v0103() -> None:
    V0101.scan = scan                  # v0101 的 report 讀模組層 scan
    PRIOR.scan = scan


_install_v0103()
report = V0101.report


def selftest() -> int:
    rc = PRIOR.selftest()            # v0101 八檢 + v0102 加檢照跑;④ 量實樹,以本版的版史規則量(同掃橋器 v0110 · 探針 v0106)
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' (' + note + ')') if note else ''}")

    print(f"=== {_STEM} {VERSION} 薄尾加檢(無版號舊 .ps1 有帶章尾版 = 版史)===")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "x").mkdir()
        (root / "x" / "Old.ps1").write_text("Write-Host 1\n", encoding="utf-8")
        (root / "x" / "Old-v0101.ps1").write_text(f"# {PS_MARK}\nWrite-Host 1\n", encoding="utf-8")
        (root / "x" / "Bad.ps1").write_text("Write-Host 2\n", encoding="utf-8")
        (root / "x" / "Bad-v0102.ps1").write_text("Write-Host 2\n", encoding="utf-8")
        (root / "x" / "Lone.ps1").write_text("Write-Host 3\n", encoding="utf-8")
        (root / "x" / "Older.ps1").write_text("Write-Host 4\n", encoding="utf-8")
        s = scan(root)
        ps = s.get("ps") or {}
        nm = set(ps.get("new_missing") or [])
        chk("⑬ 無版號舊檔 + 帶章版號尾版 = 版史(不紅);尾版也沒章 · 沒同族 · 只是前綴相同 照紅",
            s.get("state") != "NODATA" and [h["file"] for h in ps.get("history") or []] == ["x/Old.ps1"]
            and {"x/Bad.ps1", "x/Bad-v0102.ps1", "x/Lone.ps1", "x/Older.ps1"} <= nm and "x/Old.ps1" not in nm,
            f"版史 {ps.get('history')} · 新缺 {sorted(nm)}")
        reg = root / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (reg / "VIA_Bundle_SSOT_v0101.json").write_text(json.dumps({"files": ["x/Old.ps1"]}), encoding="utf-8")
        (reg / "VIA_Bundle_SSOT_v0102.json").write_text(json.dumps({"files": ["x/Old-v0101.ps1", "x/Old.ps1"], "why_v0102": "x/Old.ps1 退役"}), encoding="utf-8")
        (reg / "VIA_Inv_SSOT_v0101.json").write_text(json.dumps({"deps": ["x/Old*.ps1"], "note": "Old.ps1"}), encoding="utf-8")
        (reg / "VIA_NumberBook_MDL_v0100.jsonl").write_text(json.dumps({"source": "x/Old.ps1"}) + "\n", encoding="utf-8")
        s2 = scan(root)
        ps2 = s2.get("ps") or {}
        b2 = [b for b in ps2.get("history_blocked") or [] if b["file"] == "x/Old.ps1"]
        (reg / "VIA_Bundle_SSOT_v0103.json").write_text(json.dumps({"files": ["x/Old-v0101.ps1", "x/Old.ps1"], "retired_entries": ["Old.ps1"]}), encoding="utf-8")
        s3 = scan(root)
        ps3 = s3.get("ps") or {}
        chk("⑯ 活冊仍指名舊檔 = 照紅(history_blocked 附呼叫者);只看各家族尾版冊 · 敘述欄 / glob / .jsonl 號冊不算;尾版冊宣告 retired_entries(檔單照只增保留)後才歸版史(PR #446 Codex P1)",
            "x/Old.ps1" in (ps2.get("new_missing") or []) and b2 and b2[0]["callers"] == ["VIA_Bundle_SSOT_v0102.json:.files[1]"]
            and "x/Old.ps1" not in (ps3.get("new_missing") or []) and [h["file"] for h in ps3.get("history") or []] == ["x/Old.ps1"],
            f"呼叫者 {b2[0]['callers'] if b2 else None}")
    live = scan()
    lps = live.get("ps") or {}
    chk("⑭ 實樹:Invoke-VIA-Step1-SyncAndLKGC.ps1 歸版史(尾版 -v0101 帶章 · 子系統包冊 v0103 宣告退役入口);基線外新缺 0",
        any(h["file"] == "Invoke-VIA-Step1-SyncAndLKGC.ps1" for h in lps.get("history") or []) and not lps.get("new_missing"),
        f"新缺 {lps.get('new_missing')}")
    chk("⑮ report 與模組層 scan 同一把尺(v0101 report 讀本版 scan)", V0101.scan is scan and PRIOR.scan is scan)
    ok = rc == 0 and all(results)
    print(f"  [計] {VERSION} 薄尾 {sum(results)}/{len(results)} · v0102 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    print(f"=== Celeritas 產出契約閘 {VERSION}(薄尾 · 無版號舊 .ps1 有帶章尾版 = 版史 · 執法 L102)===")
    return report()


if __name__ == "__main__":
    raise SystemExit(main())
