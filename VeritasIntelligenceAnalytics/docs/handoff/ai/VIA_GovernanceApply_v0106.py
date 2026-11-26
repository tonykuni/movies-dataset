#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_GovernanceApply v0106 — 薄尾(v0100–v0105 一字不動):PR #747 Codex 三筆審查

  ① (P1)apply 的成敗只看車道燈:驗證段(新版自測 rc ≠ 0 · ReworkGuard RED · 編號稽核遺失 / 改身分 / 重號 / XCODE / DUPREG ≠ 0 ·
     加速器生效 🔴)全寫進 extra 文字,`rep["rows"]` 只有車道 → 驗證不過照樣 rc 0、還印「提交推送」。
     → 本版把驗證結果逐項判讀;有任何一項不過,報告多一條「verify」車道(每項一筆 FAIL)→ 燈 RED → apply 回 1、
       NEXT 印「看 [🔴] 行修好再跑」;verify 動詞也照同一判法回 1。讀不到稽核計數(只有 rc)也算不過(不冒充過)。
  ② (P2)快取鍵只看 `git status --porcelain` 的狀態字:已改的檔再改一次,狀態字不變 → 鍵不變 → 沿用舊的驗證結果。
     → 鍵另加「工作樹內容雜湊」:`git diff HEAD` 全文 + 未追蹤檔的內容雜湊(VIA_Reports 產物照舊不算)。
  ③ (P2)參數解耦橋範本 `_VDF_VIA_ROOT_REL`:有設 VIA_ROOT(資料根)但該子夾還沒建時,會掉回程式根。
     → 範本改成:有設 VIA_ROOT 就以它為準(子夾不在也回它底下);沒設才找程式根。之後用 param 車道注入的新版都用新範本。
     已注入的 7 支引擎(#745 鎖定)不改:現行所有入口都把 VIA_ROOT 設成 VIA 樹本身(= 程式根),兩條路回同一個路徑。
零網路 · 零 TA-Lib · 不 import 他系統 · 不讀寫同意閘。用法同前:plan · apply [--lanes …] · verify · --fresh · selftest。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import hashlib
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VIA_GovernanceApply"
TAG = "VIA_GovernanceApply v0106"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0106", PRIOR_PATH)
V5 = importlib.util.module_from_spec(_spec)                # v0105(V5.P = v0100 本體 · V5.V2 = v0102)
sys.modules[_spec.name] = V5
_spec.loader.exec_module(V5)
P, V2 = V5.P, V5.V2


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(V5, name)


# ── ① 驗證結果判讀 ────────────────────────────────────────────────
LAST = {"fail": []}
_AUDIT_KEYS = ("遺失", "改身分", "重號", "XCODE", "DUPREG")


def judge(ex: dict) -> list:
    """回 [(項目, 原因)];空 = 驗證全過。"""
    bad = []
    for name, rc in re.findall(r"(\S+) rc (-?\d+)", str(ex.get("新版自測") or "")):
        if int(rc) != 0:
            bad.append(("新版自測", f"{name} rc {rc}"))
    rg = str(ex.get("ReworkGuard") or "")
    if rg and (re.search(r"\bRED\b|沒有判決行", rg) or re.fullmatch(r"rc [1-9]\d*", rg.strip())):
        bad.append(("ReworkGuard", rg[:160]))
    au = ex.get("編號稽核")
    if au is not None:
        au = str(au)
        nums = {k: [int(n) for n in re.findall(rf"{k}\s*(\d+)", au)] for k in _AUDIT_KEYS}
        if not any(nums.values()):
            bad.append(("編號稽核", f"讀不到稽核計數:{au[:120]}"))
        else:
            over = [f"{k} {max(v)}" for k, v in nums.items() if v and max(v) > 0]
            if over:
                bad.append(("編號稽核", " · ".join(over)))
    acc = str(ex.get("加速器生效") or "")
    if acc.startswith("🔴"):
        bad.append(("加速器生效", acc[:160]))
    return bad


_PREV_VERIFY = P.verify


def verify(via: Path, new_files: list) -> dict:
    ex = _PREV_VERIFY(via, new_files)
    LAST["fail"] = judge(ex)
    ex["驗證判定"] = ("🔴 不過:" + " | ".join(f"{a} {b}" for a, b in LAST["fail"])) if LAST["fail"] else "🟢 全過"
    return ex


_PREV_REPORT = P.report


def report(via: Path, plan: dict, results, extra=None) -> dict:
    if results is not None and LAST["fail"]:
        plan = {**plan, "lanes": {**plan["lanes"], "verify": {"lane": "verify", "should": len(LAST["fail"]),
                                                               "can": len(LAST["fail"]), "items": [], "skipped": []}}}
        results = {**results, "verify": [{"state": "FAIL", "file": a, "why": b} for a, b in LAST["fail"]]}
    return _PREV_REPORT(via, plan, results, extra)


# ── ② 快取鍵加內容雜湊 ────────────────────────────────────────────
_PREV_KEY = V2.state_key


def content_digest(via: Path) -> str:
    h = hashlib.sha256()
    d = subprocess.run(["git", "-C", str(via), "diff", "HEAD", "--binary", "--", ".", ":(exclude)VIA_Reports"],
                       capture_output=True).stdout
    h.update(d)
    un = subprocess.run(["git", "-C", str(via), "ls-files", "--others", "--exclude-standard", "-z"], capture_output=True).stdout
    for rel in sorted(x for x in un.decode("utf-8", "replace").split("\0") if x and not x.startswith("VIA_Reports/")):
        h.update(rel.encode("utf-8"))
        try:
            h.update(hashlib.sha256((via / rel).read_bytes()).digest())
        except OSError:
            h.update(b"?")
    return h.hexdigest()[:20]


def state_key(via: Path, salt: str = "") -> str:
    return hashlib.sha256(f"{_PREV_KEY(via, salt)}|{content_digest(via)}".encode("utf-8")).hexdigest()[:20]


# ── ③ 參數解耦橋範本:VIA_ROOT 有設就以它為準 ─────────────────────
_OLD_TAIL = ("    for _gp_r in roots:\n        if (_gp_r / rel).exists():\n            return str(_gp_r / rel)\n"
             "    return str((roots[-1] if roots else _gp_P(__file__).resolve().parent) / rel)\n")
_NEW_TAIL = ("    if _gp_os.environ.get(\"VIA_ROOT\"):\n        return str(roots[0] / rel)                  # 設了資料根就以它為準(子夾不在也一樣)\n"
             "    return str((roots[-1] if roots else _gp_P(__file__).resolve().parent) / rel)\n")
PARAM_BLOCK_FIXED = P.PARAM_BLOCK.replace(_OLD_TAIL, _NEW_TAIL) if _OLD_TAIL in P.PARAM_BLOCK else None


def _install():
    P.verify, P.report, V2.state_key = verify, report, state_key
    if PARAM_BLOCK_FIXED:
        P.PARAM_BLOCK = PARAM_BLOCK_FIXED
    P.TAG = TAG
    V5.TAG = TAG                                         # v0105 main 的起跑行用它自己的 TAG


_install()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 7 項 · 前版 %s 在子行程)" % (TAG, PRIOR_PATH.name), flush=True)
    good = {"新版自測": "a.py rc 0", "ReworkGuard": "[VIA_ReworkGuard v0103] check YELLOW · 掃 3 檔",
            "編號稽核": "[編號只增稽核] YELLOW · 遺失 0 · 改身分 0 · 重號 0 | GREEN  DUPREG         0 | GREEN  XCODE          0",
            "加速器生效": "🟢 PY 生效 3/3"}
    badx = {"新版自測": "a.py rc 0 · b.py rc 1", "ReworkGuard": "[VIA_ReworkGuard v0103] check RED · R2",
            "編號稽核": "遺失 0 · 改身分 0 · 重號 2 | DUPREG 0 | XCODE 1", "加速器生效": "🔴 PY 生效 1/2"}
    jb = judge(badx)
    chk("T1 判讀:全過 → 空;自測 rc 1 · ReworkGuard RED · 重號 2 / XCODE 1 · 加速器 🔴 → 四項都抓到",
        judge(good) == [] and [a for a, _ in jb] == ["新版自測", "ReworkGuard", "編號稽核", "加速器生效"]
        and "重號 2" in jb[2][1] and "XCODE 1" in jb[2][1], jb)
    chk("T2 稽核只有 rc(讀不到計數)→ 算不過;ReworkGuard 只回 rc 1 → 算不過",
        [a for a, _ in judge({"編號稽核": "rc 1", "ReworkGuard": "rc 1"})] == ["ReworkGuard", "編號稽核"])
    with tempfile.TemporaryDirectory(prefix="gov106_") as td:
        via = Path(td)
        keep_dir = Path.cwd()
        try:
            LAST["fail"] = [("編號稽核", "重號 2")]
            plan = {"at": "t", "secs": 0, "lanes": {"net": {"lane": "net", "should": 0, "can": 0, "items": [], "skipped": []}}}
            os.chdir(td)
            rep = report(via, plan, {"net": []}, {"驗證判定": "🔴"})
            LAST["fail"] = []
            rep2 = report(via, plan, {"net": []}, {"驗證判定": "🟢"})
        finally:
            os.chdir(keep_dir)
        lamps = {r["lane"]: r["lamp"] for r in rep["rows"]}
        chk("T3 驗證不過 → 報告多 verify 車道且 RED(apply 的 bad 判式會回 1);全過 → 沒有 verify 車道",
            lamps.get("verify") == "RED" and all(r["lane"] != "verify" for r in rep2["rows"]), lamps)
        subprocess.run(["git", "init", "-q", str(via)], check=True)
        subprocess.run(["git", "-C", str(via), "-c", "user.email=fx@fx", "-c", "user.name=fx", "commit", "-q", "--allow-empty", "-m", "fx"], check=True)
        (via / "a.py").write_text("x = 1\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(via), "add", "a.py"], check=True)
        subprocess.run(["git", "-C", str(via), "-c", "user.email=fx@fx", "-c", "user.name=fx", "commit", "-q", "-m", "a"], check=True)
        (via / "a.py").write_text("x = 2\n", encoding="utf-8")
        k1, o1 = state_key(via, "t"), _PREV_KEY(via, "t")
        (via / "a.py").write_text("x = 3\n", encoding="utf-8")
        k2, o2 = state_key(via, "t"), _PREV_KEY(via, "t")
        (via / "u.py").write_text("y = 1\n", encoding="utf-8")
        k3 = state_key(via, "t")
        (via / "u.py").write_text("y = 2\n", encoding="utf-8")
        k4 = state_key(via, "t")
        (via / "VIA_Reports").mkdir(exist_ok=True)
        (via / "VIA_Reports" / "r.txt").write_text("r", encoding="utf-8")
        k5 = state_key(via, "t")
        chk("T4 快取鍵:已改檔再改(狀態字不變)→ 舊鍵相同、新鍵不同;未追蹤檔內容變 → 鍵變;VIA_Reports 產物不算",
            o1 == o2 and k1 != k2 and k3 != k4 and k4 == k5, (o1 == o2, k1 != k2, k3 != k4, k4 == k5))
        root = via / "data_root"
        code = via / "code"
        (code / "supportive modules").mkdir(parents=True)
        m = re.search(r"def _VDF_VIA_ROOT_REL\(rel\):.*?\n(?=\n\ndef |\Z)", (PARAM_BLOCK_FIXED or "").replace("{{", "{").replace("}}", "}"), re.S)
        (code / "tpl_probe.py").write_text(m.group(0) if m else "", encoding="utf-8")
        tspec = importlib.util.spec_from_file_location("gov106_tpl_probe", code / "tpl_probe.py")
        tpl = importlib.util.module_from_spec(tspec)
        tspec.loader.exec_module(tpl)
        keep_env = os.environ.get("VIA_ROOT")
        try:
            os.environ["VIA_ROOT"] = str(root)
            got = tpl._VDF_VIA_ROOT_REL("module/VDF/dict") if m else None
            os.environ.pop("VIA_ROOT", None)
            got2 = tpl._VDF_VIA_ROOT_REL("module/VDF/dict") if m else None
        finally:
            if keep_env is not None:
                os.environ["VIA_ROOT"] = keep_env
            else:
                os.environ.pop("VIA_ROOT", None)
        chk("T5 範本:設了 VIA_ROOT 但子夾還不在 → 仍回 VIA_ROOT 底下;沒設 → 回程式根底下(範本已換進 P.PARAM_BLOCK)",
            PARAM_BLOCK_FIXED is not None and P.PARAM_BLOCK is PARAM_BLOCK_FIXED
            and got == str(root / "module/VDF/dict") and got2 == str(code / "module/VDF/dict"), (got, got2))
    cp = subprocess.run([sys.executable, "-B", str(PRIOR_PATH), "selftest"], capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=1800)
    chk("T6 前版 %s 自測照過(子行程)" % PRIOR_PATH.name, cp.returncode == 0, [x for x in cp.stdout.splitlines() if "FAIL" in x][:3])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T7 第 3 行加速器標記且載入生效(VIA_ACCEL 非空)· 零 TA-Lib · 不 import 他系統 · 不設同意閘",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"^\s*(import|from)\s+(VDF|VRN|VQG|VAP)", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    n = sum(ok)
    print("[計] %s 自測 %d/%d %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("selftest", "--selftest"):
        return selftest()
    if args and args[0] in ("-h", "--help", "help"):
        print(__doc__)
    LAST["fail"] = []
    rc = V5.main(args)
    if args and args[0] == "verify" and LAST["fail"] and rc == 0:
        print("[🔴 RED - CRITICAL ERROR] 驗證不過:" + " | ".join(f"{a} {b}" for a, b in LAST["fail"]), flush=True)
        print("NEXT: 修好上列再跑 verify(不要提交)", flush=True)
        return 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
