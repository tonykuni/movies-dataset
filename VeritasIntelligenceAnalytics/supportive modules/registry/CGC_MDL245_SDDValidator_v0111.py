#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL245_SDDValidator v0111 — 薄尾(v0100–v0110 一字不動):X-REG 把「步釘在前版」跟「註冊冊落後」分開

實錄(2026-11-27 SDD 驗證 X-REG 紅):VDF-WKF022 的步釘 VDF_MDL008_FetchSystem_v0110.py、VDF-WKF035 的步釘 VDF_MDL004_TWFullMarketEngine_v0101.py,
     這兩家的尾版是 v0114 / v0102,元件註冊冊登的就是尾版。本體的判法是「冊上來源 ≠ 這一步指到的檔 → 註冊冊不是尾版」,
     於是把「步自己釘在前版」算成註冊冊的錯(叫人去跑 registry-sync,跑了也不會變)。
本版只改這一條的判法(操作員 2026-11-27 裁定 A 同批 · VCGC-REQ279):
  冊上來源 ≠ 這一步指到的檔時,先看這一家在同一個夾裡真正的尾版:
    冊上登的就是那個尾版、而步指到的是它的前版 → 不算註冊冊落後;另列一行 INFO「X-REG-PIN 步釘在前版」把它們點名。
    其餘照舊是紅:冊上登的不是尾版(真的落後)· 冊上登的是別的夾裡的同名檔(例:副本)· 沒註冊。
  要不要把步改成取尾版,由那本工作流冊所屬的系統決定;本檔不改任何冊。
X-REG 的 RED / GREEN 訊息其餘寫法、X-NUM 兩列、versions 表一律照本體。零網路。不用 TA-Lib。
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
TAG = "v0111"
VERBS = ("check", "real", "lock", "closeout", "--selftest")      # 動詞照前版;本版沒有新增
SHOW = 4                                                          # X-REG 訊息裡每一類點名幾個(同本體)


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


HOME = next(m for m in _chain() if _defined_in(m, "check_registration"))     # 定義這一條的那一層(本體 check() 讀它自己的全域)
_ORIG_CHECK_REG = vars(HOME)["check_registration"]


def __getattr__(name: str):
    return getattr(PRIOR, name)


def family_tail(p: Path) -> Path:
    """p 這一家在同一個夾裡版號最大的那一支;找不到別的就是 p 自己。"""
    stem = re.sub(r"_v\d+$", "", p.stem)
    pat = re.compile(re.escape(stem) + r"_v\d+$")
    cands = [q for q in p.parent.glob(stem + "_v*" + p.suffix) if pat.match(q.stem)]
    return max(cands, key=_vnum) if cands else p


def judge(paths, by_id: dict, num: dict, rel, exemption, stem_of) -> dict:
    """每個步的正主檔 → 沒註冊 · 註冊冊落後 · 步釘在前版 · 正本唯讀。只讀,不寫任何東西。"""
    out = {"unreg": [], "stale": [], "pinned": [], "canon": []}
    for p in sorted({Path(x) for x in paths if x}, key=str):
        r = rel(p)
        reg = by_id.get(stem_of(p))
        if exemption(p) and not reg and not num.get(r):
            out["canon"].append(p.name)
            continue
        if p.suffix == ".json":
            continue
        if not reg:
            out["unreg"].append(p.name)
        elif reg.get("source") != r:
            ft = family_tail(p)
            if ft != p and reg.get("source") == rel(ft):
                out["pinned"].append(f"{p.name}(尾版 {ft.name})")
            else:
                out["stale"].append(f"{p.name}(冊上 {Path(str(reg.get('source'))).name})")
    return out


def check_registration(state, rows, targets, versions: dict):
    """先照本體跑完(X-REG · X-NUM · versions),再把 X-REG 那一列照本版的判法重寫;有釘前版的步就多一列 INFO。"""
    n0 = len(rows)
    _ORIG_CHECK_REG(state, rows, targets, versions)
    by_id, num = HOME._registers()
    j = judge([t[3] for t in targets if t[3]], by_id, num, HOME.rel, HOME.exemption, HOME.stem_of)
    for i in range(n0, len(rows)):
        if rows[i].get("rule") != "X-REG":
            continue
        canon = j["canon"]
        if j["unreg"] or j["stale"]:
            rows[i]["lamp"] = "RED"
            rows[i]["msg"] = f"未註冊 {j['unreg'][:SHOW]} · 註冊冊不是尾版(待 registry-sync --apply){j['stale'][:SHOW]}"
        else:
            rows[i]["lamp"] = "GREEN"
            rows[i]["msg"] = (f"步的正主都在元件註冊冊且登記的就是尾版({len(versions) - len(canon)} 支;帶註冊碼與時間)"
                              + (f";正本唯讀不入冊 {len(canon)} 支:{' · '.join(canon)}" if canon else ""))
        if j["pinned"]:
            rows.insert(i + 1, {"lamp": "INFO", "rule": "X-REG-PIN", "ref": "",
                                "msg": f"步釘在前版 {len(j['pinned'])} 支(冊上登的是該家族的尾版,不算註冊冊落後;要不要改成取尾版由該工作流冊的系統決定):{j['pinned'][:SHOW * 2]}"})
        break
    return None


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
    with tempfile.TemporaryDirectory(prefix="sdd_111_") as td:
        root = Path(td)
        for rel_ in ("a/Fam_ENG001_X_v0101.py", "a/Fam_ENG001_X_v0102.py", "a/Fam_ENG002_Y_v0101.py", "a/Fam_ENG002_Y_v0102.py", "a/Fam_ENG002_Y_v0103.py",
                     "home/Tool_MDL001_Z_v0105.py", "copy/Tool_MDL001_Z_v0105.py", "a/Fam_ENG003_W_v0100.py", "a/Plain_engine.py",
                     "a/Fam_ENG004_Q_v0101.py", "a/Fam_ENG004_Q_v0102.py", "a/Fam_ENG004_Q_v0102x.py", "a/Book_v0100.json", "a/Canon_v0100.py"):
            (root / rel_).parent.mkdir(parents=True, exist_ok=True)
            (root / rel_).write_text("X = 1\n", encoding="utf-8")
        rel = lambda p: Path(p).relative_to(root).as_posix()                      # noqa: E731
        stem_of = lambda p: re.sub(r"_v\d+$", "", Path(str(p)).stem)             # noqa: E731
        exemption = lambda p: "正本唯讀" if Path(p).name.startswith("Canon") else ""   # noqa: E731
        by_id = {"Fam_ENG001_X": {"source": "a/Fam_ENG001_X_v0102.py"},       # 冊 = 尾版;步釘 v0101
                 "Fam_ENG002_Y": {"source": "a/Fam_ENG002_Y_v0102.py"},       # 冊落後(尾版 v0103);步釘 v0101
                 "Tool_MDL001_Z": {"source": "copy/Tool_MDL001_Z_v0105.py"},  # 冊登的是別的夾的同名檔
                 "Fam_ENG004_Q": {"source": "a/Fam_ENG004_Q_v0102.py"}}       # 步指到尾版,冊也是尾版
        P = lambda s: root / s                                                    # noqa: E731
        j = judge([P("a/Fam_ENG001_X_v0101.py"), P("a/Fam_ENG002_Y_v0101.py"), P("home/Tool_MDL001_Z_v0105.py"), P("a/Fam_ENG003_W_v0100.py"),
                   P("a/Plain_engine.py"), P("a/Fam_ENG004_Q_v0102.py"), P("a/Book_v0100.json"), P("a/Canon_v0100.py"), None,
                   P("a/Fam_ENG001_X_v0101.py")], by_id, {}, rel, exemption, stem_of)
        chk("① 步釘前版、冊上登的是尾版 → 列進「釘前版」,不算註冊冊落後", j["pinned"] == ["Fam_ENG001_X_v0101.py(尾版 Fam_ENG001_X_v0102.py)"], j)
        chk("② 反控:冊上登的不是尾版(尾版 v0103、冊 v0102)→ 照舊算落後", "Fam_ENG002_Y_v0101.py(冊上 Fam_ENG002_Y_v0102.py)" in j["stale"], j["stale"])
        chk("③ 反控:冊上登的是別的夾裡的同名檔(副本)→ 照舊算落後", "Tool_MDL001_Z_v0105.py(冊上 Tool_MDL001_Z_v0105.py)" in j["stale"] and len(j["stale"]) == 2, j["stale"])
        chk("④ 沒註冊的照舊點名(有版號的 · 無版號的各一)", j["unreg"] == ["Fam_ENG003_W_v0100.py", "Plain_engine.py"], j["unreg"])
        chk("⑤ 步指到尾版且冊相同 → 乾淨;.json 不查註冊;正本唯讀另列;同一檔重複只算一次",
            not any("Fam_ENG004_Q" in x or "Book_" in x for k in ("unreg", "stale", "pinned") for x in j[k]) and j["canon"] == ["Canon_v0100.py"], j)
        chk("⑥ family_tail:只認「家族名 + _v數字」(v0102x 這種不算)· 沒有別版就回自己",
            family_tail(P("a/Fam_ENG004_Q_v0101.py")).name == "Fam_ENG004_Q_v0102.py" and family_tail(P("a/Plain_engine.py")).name == "Plain_engine.py")
        # 走真正的入口:本體 check() 叫的那個名字
        keep = (HOME._registers, HOME.rel, HOME.exemption)

        def run(targets):
            rows, versions = [], {}
            HOME._registers = lambda: (by_id, {})
            HOME.rel = rel
            HOME.exemption = exemption
            try:
                vars(HOME)["check_registration"]({"wkfs": [], "req": {}}, rows, targets, versions)
            finally:
                HOME._registers, HOME.rel, HOME.exemption = keep
            return rows
        t = lambda s: (None, None, None, P(s), None)                              # noqa: E731
        rows_pin = run([t("a/Fam_ENG001_X_v0101.py"), t("a/Fam_ENG004_Q_v0102.py")])
        xr = [r for r in rows_pin if r["rule"] == "X-REG"]
        xp = [r for r in rows_pin if r["rule"] == "X-REG-PIN"]
        chk("⑦ 走本體讀的那個名字:只有釘前版時 X-REG 綠,另有一列 INFO 點名,而且緊跟在 X-REG 後面",
            vars(HOME)["check_registration"] is check_registration and len(xr) == 1 and xr[0]["lamp"] == "GREEN" and len(xp) == 1 and xp[0]["lamp"] == "INFO"
            and "Fam_ENG001_X_v0101.py" in xp[0]["msg"] and rows_pin.index(xp[0]) == rows_pin.index(xr[0]) + 1, rows_pin[:3])
        rows_bad = run([t("a/Fam_ENG001_X_v0101.py"), t("home/Tool_MDL001_Z_v0105.py"), t("a/Plain_engine.py")])
        xr2 = [r for r in rows_bad if r["rule"] == "X-REG"]
        chk("⑧ 有真的落後或沒註冊時 X-REG 照舊紅,訊息點名的是那幾支而不是釘前版的",
            len(xr2) == 1 and xr2[0]["lamp"] == "RED" and "Tool_MDL001_Z_v0105.py" in xr2[0]["msg"] and "Plain_engine.py" in xr2[0]["msg"]
            and "Fam_ENG001_X" not in xr2[0]["msg"], xr2)
        rows_orig = []
        HOME._registers, HOME.rel, HOME.exemption = (lambda: (by_id, {})), rel, exemption
        try:
            _ORIG_CHECK_REG({"wkfs": [], "req": {}}, rows_orig, [t("a/Fam_ENG001_X_v0101.py"), t("a/Fam_ENG004_Q_v0102.py")], {})
        finally:
            HOME._registers, HOME.rel, HOME.exemption = keep
        chk("⑨ 對照:同一組輸入本體原判法是紅(這一版改的就是這裡)· X-NUM 列數兩邊相同",
            [r["lamp"] for r in rows_orig if r["rule"] == "X-REG"] == ["RED"]
            and len([r for r in rows_orig if r["rule"] == "X-NUM"]) == len([r for r in rows_pin if r["rule"] == "X-NUM"]), rows_orig[:2])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 第 3 行加速器標記且載入生效(VIA_ACCEL 非空)· 零 TA-Lib · 不 import 他系統 · 本檔沒有寫檔的呼叫",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"^\s*(import|from)\s+(VDF|VRN|VQG|VAP|VTK)", src, re.M)
        and len(re.findall(r"\.write_text\(|\.write_bytes\(|os\.replace\(", src.split("def selftest()")[0])) == 0, VIA_ACCEL is not None)
    lost = [x for x in dir(PRIOR) if not x.startswith("_") and callable(getattr(PRIOR, x)) and not hasattr(sys.modules[__name__], x)]
    chk("⑪ 前版公開名稱都還拿得到(real · check · lock · closeout 在內)", not lost and all(callable(getattr(sys.modules[__name__], k)) for k in ("real", "check")), lost[:6])
    prc = PRIOR.selftest() if hasattr(PRIOR, "selftest") else 0
    chk("⑫ 前版自測照過", prc == 0, "rc " + str(prc))
    print("[計] " + ENGINE + " 本版 " + str(n["ok"]) + "/" + str(n["ok"] + n["bad"]) + " · " + ("PASS" if n["bad"] == 0 else "FAIL"))
    return 0 if n["bad"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
