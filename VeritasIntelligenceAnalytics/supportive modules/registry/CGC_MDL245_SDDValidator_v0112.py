#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL245_SDDValidator v0112 — 薄尾(v0100–v0111 一字不動):X-REG 不再要求「已退役的步」的正主在元件註冊冊

實錄(2026-11-27 SDD 驗證 X-REG 還紅的最後一種):VDF-WKF033 的 STP001 / STP002 指到兩支沒有版號的舊情緒引擎
     (VDF_Engine_aaii_sentiment.py · VDF_Engine_cnn_fear_greed_proxy.py)。這兩步在工作流冊上早已標 retired
     (2026-11-21 · PR #712 裁定:「不為它們另開新版(避免多頭),AAII 一律由 ENG116 負責」),但本體照樣要它們的正主在註冊冊。
     註冊冊只收帶版號的尾版,它們永遠進不去;而替它們出版號檔正好違反那則裁定。
本版只補這一條(VCGC-REQ280):
  工作流冊上寫了 retired 的步,它的正主「沒註冊」不算紅;另列一行 INFO「X-REG-RETIRED 步已退役」把它們點名。
  同一個檔只要還被任何一條沒退役的步指到,就照舊要註冊(退役的步不能替現役的步擋掉檢查)。
  已退役步的正主如果有註冊但登的不是尾版,照舊算落後(冊上有列就要對)。
  其餘(步釘前版的 INFO · 真的落後 · 登到副本 · 現役步沒註冊 · X-NUM)一律照 v0111。本檔不改任何冊。零網路。不用 TA-Lib。
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

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL245_SDDValidator"
ENGINE = Path(__file__).stem
TAG = "v0112"
VERBS = ("check", "real", "lock", "closeout", "--selftest")      # 動詞照前版;本版沒有新增
SHOW = 8                                                          # INFO 列點名幾個


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_sdd_prior_" + TAG, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def _chain() -> list:
    out, m = [], PRIOR
    while m is not None:
        out.append(m)
        m = vars(m).get("PRIOR")
    return out


def _defined_in(m, name: str) -> bool:
    fn = vars(m).get(name)
    return callable(fn) and getattr(fn, "__globals__", None) is vars(m)


JUDGE_HOME = next(m for m in _chain() if _defined_in(m, "judge"))            # v0111:它的 check_registration 讀它自己全域的 judge
HOME = JUDGE_HOME.HOME                                                       # 本體:check() 讀它自己全域的 check_registration
_PRIOR_JUDGE = vars(JUDGE_HOME)["judge"]
_PRIOR_CHECK_REG = vars(HOME)["check_registration"]                          # 目前裝在本體上的那一支(v0111 的)
_CTX = {"retired": set()}                                                    # 這一輪「只被退役步指到」的檔(check_registration 進場時填)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def retired_only(state: dict, targets: list) -> set:
    """只被 retired 的步指到的正主檔(Path)。同一個檔還被任何沒退役的步指到 → 不算。"""
    ret = {st.get("code") for _sub, w in state.get("wkfs") or [] for st in w.get("steps") or [] if st.get("retired")}
    by_path: dict = {}
    for t in targets:
        if t[3]:
            by_path.setdefault(Path(t[3]), set()).add(t[1] in ret)
    return {p for p, flags in by_path.items() if flags == {True}}


def judge(paths, by_id: dict, num: dict, rel, exemption, stem_of) -> dict:
    """照 v0111 判完,再把「只被退役步指到、而且沒註冊」的檔從 unreg 移到 retired。別的類別不動。"""
    j = _PRIOR_JUDGE(paths, by_id, num, rel, exemption, stem_of)
    uniq = {Path(x) for x in paths if x}
    ret_names = {p.name for p in uniq if p in _CTX["retired"]}
    live_names = {p.name for p in uniq if p not in _CTX["retired"]}
    move = [n for n in j["unreg"] if n in ret_names and n not in live_names]
    j["retired"] = move
    j["unreg"] = [n for n in j["unreg"] if n not in move]
    return j


def check_registration(state, rows, targets, versions: dict):
    """設好這一輪的退役名單 → 交給 v0111(它會叫到本版的 judge)→ 有被移開的就補一列 INFO。"""
    n0 = len(rows)
    keep = _CTX["retired"]
    _CTX["retired"] = retired_only(state, targets)
    try:
        _PRIOR_CHECK_REG(state, rows, targets, versions)
        by_id, num = HOME._registers()
        moved = judge([t[3] for t in targets if t[3]], by_id, num, HOME.rel, HOME.exemption, HOME.stem_of)["retired"]
    finally:
        _CTX["retired"] = keep
    if not moved:
        return None
    idx = [i for i in range(n0, len(rows)) if rows[i].get("rule") == "X-REG"]
    if not idx:
        return None
    i = idx[0]
    if rows[i].get("lamp") == "GREEN":
        rows[i]["msg"] = str(rows[i].get("msg") or "") + f";另有已退役步的正主 {len(moved)} 支不要求註冊(見 X-REG-RETIRED)"
    at = i + 1
    while at < len(rows) and rows[at].get("rule") == "X-REG-PIN":
        at += 1
    rows.insert(at, {"lamp": "INFO", "rule": "X-REG-RETIRED", "ref": "",
                     "msg": f"步已退役 {len(moved)} 支(工作流冊上標 retired;正主不要求在元件註冊冊;退役理由與接手者寫在該步上):{moved[:SHOW]}"})
    return None


JUDGE_HOME.judge = judge
HOME.check_registration = check_registration          # 本體 check() 以它自己的模組全域叫這個名字


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    import tempfile
    n = {"ok": 0, "bad": 0}

    def chk(name, cond, note=""):
        n["ok" if cond else "bad"] += 1
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] " + ENGINE + " 自測開始(暫存夾 · 不改任何冊 · 零網路)", flush=True)
    with tempfile.TemporaryDirectory(prefix="sdd_112_") as td:
        root = Path(td)
        for rel_ in ("a/Old_engine_a.py", "a/Old_engine_b.py", "a/Shared_engine.py", "a/Live_plain.py", "a/Fam_ENG001_X_v0101.py", "a/Fam_ENG001_X_v0102.py",
                     "a/Fam_ENG005_R_v0101.py", "a/Fam_ENG005_R_v0102.py", "a/Fam_ENG006_T_v0100.py"):
            (root / rel_).parent.mkdir(parents=True, exist_ok=True)
            (root / rel_).write_text("X = 1\n", encoding="utf-8")
        rel = lambda p: Path(p).relative_to(root).as_posix()                      # noqa: E731
        exemption = lambda p: ""                                                  # noqa: E731
        P = lambda s: root / s                                                    # noqa: E731
        t = lambda stp, s: ("W1", stp, None, P(s), None)                          # noqa: E731
        by_id = {"Fam_ENG001_X": {"source": "a/Fam_ENG001_X_v0102.py"},       # 現役步釘 v0101(v0111 的 INFO)
                 "Fam_ENG005_R": {"source": "a/Fam_ENG005_R_v0101.py"},       # 退役步指尾版 v0102,冊上卻是 v0101 → 落後
                 "Fam_ENG006_T": {"source": "a/Fam_ENG006_T_v0100.py"}}
        state = {"req": {}, "wkfs": [("X", {"code": "W1", "steps": [
            {"code": "S1", "retired": {"why": "裁定"}}, {"code": "S2", "retired": {"why": "裁定"}}, {"code": "S3"}, {"code": "S4"},
            {"code": "S5", "retired": {"why": "裁定"}}, {"code": "S6"}, {"code": "S7", "retired": {"why": "裁定"}}, {"code": "S8"}]})]}
        base = [t("S1", "a/Old_engine_a.py"), t("S2", "a/Old_engine_b.py"), t("S6", "a/Fam_ENG006_T_v0100.py")]
        ro = retired_only(state, base + [t("S5", "a/Shared_engine.py"), t("S3", "a/Shared_engine.py")])
        chk("① 只被退役步指到的檔才算退役;同一個檔還被沒退役的步指到 → 不算",
            ro == {P("a/Old_engine_a.py"), P("a/Old_engine_b.py")}, sorted(x.name for x in ro))
        keep = (HOME._registers, HOME.rel, HOME.exemption)

        def run(targets, fn=None):
            rows, versions = [], {}
            HOME._registers, HOME.rel, HOME.exemption = (lambda: (by_id, {})), rel, exemption
            try:
                (fn or vars(HOME)["check_registration"])(state, rows, targets, versions)
            finally:
                HOME._registers, HOME.rel, HOME.exemption = keep
            return rows
        r1 = run(base)
        xr = [r for r in r1 if r["rule"] == "X-REG"]
        xt = [r for r in r1 if r["rule"] == "X-REG-RETIRED"]
        chk("② 走本體讀的那個名字:只有退役步的正主沒註冊 → X-REG 綠,另有一列 INFO 點名兩支,緊跟在 X-REG 後面",
            len(xr) == 1 and xr[0]["lamp"] == "GREEN" and "X-REG-RETIRED" in xr[0]["msg"]
            and len(xt) == 1 and xt[0]["lamp"] == "INFO" and "Old_engine_a.py" in xt[0]["msg"] and "Old_engine_b.py" in xt[0]["msg"]
            and r1.index(xt[0]) == r1.index(xr[0]) + 1, r1[:3])
        r0 = run(base, _PRIOR_CHECK_REG_UNHOOKED)
        chk("③ 對照:同一組輸入照 v0111 的判法是紅(這一版改的就是這裡)",
            [r["lamp"] for r in r0 if r["rule"] == "X-REG"] == ["RED"] and not [r for r in r0 if r["rule"] == "X-REG-RETIRED"], r0[:2])
        r2 = run(base + [t("S3", "a/Live_plain.py")])
        x2 = [r for r in r2 if r["rule"] == "X-REG"][0]
        chk("④ 反控:現役步的正主沒註冊照舊紅,訊息只點名現役那一支;退役的仍另列 INFO",
            x2["lamp"] == "RED" and "Live_plain.py" in x2["msg"] and "Old_engine_a.py" not in x2["msg"] and len([r for r in r2 if r["rule"] == "X-REG-RETIRED"]) == 1, x2)
        r3 = run(base + [t("S5", "a/Shared_engine.py"), t("S3", "a/Shared_engine.py")])
        x3 = [r for r in r3 if r["rule"] == "X-REG"][0]
        chk("⑤ 反控:退役步與現役步指到同一個檔 → 照舊要註冊(紅)", x3["lamp"] == "RED" and "Shared_engine.py" in x3["msg"], x3)
        r4 = run(base + [t("S7", "a/Fam_ENG005_R_v0102.py")])
        x4 = [r for r in r4 if r["rule"] == "X-REG"][0]
        chk("⑥ 反控:退役步的正主有註冊但冊上不是尾版 → 照舊算落後(紅)", x4["lamp"] == "RED" and "Fam_ENG005_R_v0102.py" in x4["msg"], x4)
        r5 = run(base + [t("S8", "a/Fam_ENG001_X_v0101.py")])
        order = [r["rule"] for r in r5 if r["rule"].startswith("X-REG")]
        chk("⑦ 與 v0111 的 INFO 並存:順序是 X-REG → X-REG-PIN → X-REG-RETIRED,X-REG 綠", order == ["X-REG", "X-REG-PIN", "X-REG-RETIRED"]
            and [r for r in r5 if r["rule"] == "X-REG"][0]["lamp"] == "GREEN", order)
        r6 = run([t("S6", "a/Fam_ENG006_T_v0100.py")])
        chk("⑧ 沒有退役步的正主需要放行時,輸出與 v0111 逐列相同(不多一列、不改訊息)· 跑完退役名單清空",
            r6 == run([t("S6", "a/Fam_ENG006_T_v0100.py")], _PRIOR_CHECK_REG_UNHOOKED) and _CTX["retired"] == set(), r6[:2])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 第 3 行加速器標記且載入生效(VIA_ACCEL 非空)· 零 TA-Lib · 不 import 他系統 · 本檔沒有寫檔的呼叫",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"^\s*(import|from)\s+(VDF|VRN|VQG|VAP|VTK)", src, re.M)
        and len(re.findall(r"\.write_text\(|\.write_bytes\(|os\.replace\(", src.split("def selftest()")[0])) == 0, VIA_ACCEL is not None)
    lost = [x for x in dir(PRIOR) if not x.startswith("_") and callable(getattr(PRIOR, x)) and not hasattr(sys.modules[__name__], x)]
    chk("⑩ 前版公開名稱都還拿得到(real · check · family_tail 在內)", not lost and all(callable(getattr(sys.modules[__name__], k)) for k in ("real", "check", "family_tail")), lost[:6])
    import subprocess
    prc = subprocess.run([sys.executable, "-B", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8",
                         errors="replace", timeout=900).returncode      # 子行程:前版的自測會檢查「本體上裝的是它自己那一支」,要在沒載入本版的行程裡跑
    chk("⑪ 前版 " + PRIOR_PATH.name + " 自測照過(子行程,沒載入本版)", prc == 0, "rc " + str(prc))
    print("[計] " + ENGINE + " 本版 " + str(n["ok"]) + "/" + str(n["ok"] + n["bad"]) + " · " + ("PASS" if n["bad"] == 0 else "FAIL"))
    return 0 if n["bad"] == 0 else 1


def _PRIOR_CHECK_REG_UNHOOKED(state, rows, targets, versions):
    """自測對照用:暫時把 judge 換回 v0111 的,跑 v0111 的 check_registration,跑完裝回。"""
    JUDGE_HOME.judge = _PRIOR_JUDGE
    try:
        return _PRIOR_CHECK_REG(state, rows, targets, versions)
    finally:
        JUDGE_HOME.judge = judge


if __name__ == "__main__":
    sys.exit(main())
