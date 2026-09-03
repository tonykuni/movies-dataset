#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flow_param_family — 參數家族解析器「一個家」(批309)
====================================================================
操作員令(批309):「參數可動態滾動,有時必須固定——整合成同一個家的
分類法」。冊:GroupIndex/flow_simulation_v0400/ssot/
VIA_FLOWROT_Method_Thresholds_v0400.json(C-01…C-22;append-only)。

三型分家(性質決定該不該動):
  Type-F 固定憲法   方法論底線/統計顯著性——任何動態結果違憲直接否決
  Type-D 強制滾動   每次校準以滾動分位/中位/IC 更新;零固定閾值
  Type-H 混合鎖定   平常滾動;觸發結構異常(L1–L5)鎖定=觸發前 20 日
                    中位數;鎖期短(C-20=4 日)後恢復——保敏感度
決策流(可直接對每參數 P 執行):
  F → 固定值 | D → 滾動值(樣本不足=誠實退回基值並標 FALLBACK)
  H → 觸發鎖定 ? 鎖值 : 滾動值
半動態不失敏:adaptive_window(base, shock_z)——|z|>2.3 視窗減半,
  不低於 C-22(15);平常維持 base。
族譜:每次 calibrate() 記錄各參數當下模式(FIXED/ROLLING/LOCKED/
  FALLBACK)、鎖定原因與時間,落 data/output/param_family_ledger.json。

API:
  load_ssot() · resolve(cid, history, state, lock_book) · evaluate_locks(state)
  adaptive_window(base, shock_z) · calibrate(histories, state) → 族譜條目
用法:--family | --calibrate <json:{histories,state}> | --selftest(八檢)
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(路徑引導版;graceful 零行為變更) =====
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

import json
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VIA = ROOT.parent.parent.parent  # VeritasIntelligenceAnalytics/
SSOT_DIR = VIA / "functional modules" / "GroupIndex" / "flow_simulation_v0400" / "ssot"
LEDGER = ROOT / "data" / "output" / "param_family_ledger.json"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")


def load_ssot() -> dict:
    hits = sorted(SSOT_DIR.glob("VIA_FLOWROT_Method_Thresholds_v*.json"))
    if not hits:
        raise FileNotFoundError("門檻冊缺(VIA_FLOWROT_Method_Thresholds_v*.json)")
    return json.loads(hits[-1].read_text(encoding="utf-8"))


def controls(ssot: dict | None = None) -> dict:
    ssot = ssot or load_ssot()
    return {c["id"]: c for c in ssot["controls"]}


def _quantile(vals: list, q: float) -> float:
    xs = sorted(vals)
    if not xs:
        raise ValueError("empty")
    pos = (len(xs) - 1) * q
    lo, hi = int(pos), min(int(pos) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def adaptive_window(base: int, shock_z: float = 0.0, ssot: dict | None = None) -> int:
    """半動態不失敏:|shock|>2.3 ⇒ 視窗減半(不低於 C-22);平常 base。"""
    c = controls(ssot)
    floor = int(c.get("C-22", {}).get("value", 15))
    if abs(shock_z) > 2.3:
        return max(floor, base // 2)
    return base


def evaluate_locks(state: dict, ssot: dict | None = None) -> list[str]:
    """依冊載 L1–L5 規則評估觸發(規則語法:abs(x)>k / x<k / x==VAL)。缺量=不觸發(誠實)。"""
    ssot = ssot or load_ssot()
    fired = []
    for t in ssot.get("lock_triggers", []):
        rule = t["rule"].replace(" ", "")
        m = re.fullmatch(r"abs\((\w+)\)>([\d.]+)", rule)
        if m:
            v = state.get(m.group(1))
            if v is not None and abs(float(v)) > float(m.group(2)):
                fired.append(t["id"])
            continue
        m = re.fullmatch(r"(\w+)<(-?[\d.]+)", rule)
        if m:
            v = state.get(m.group(1))
            if v is not None and float(v) < float(m.group(2)):
                fired.append(t["id"])
            continue
        m = re.fullmatch(r"(\w+)==(\w+)", rule)
        if m and str(state.get(m.group(1))) == m.group(2):
            fired.append(t["id"])
    return fired


def _lock_applies(ctrl: dict, fired: list[str], state: dict) -> bool:
    """控項自身 lock.trigger 命中?(對映 L 規則或直接條件)。"""
    trig = str(ctrl.get("lock", {}).get("trigger", ""))
    if not trig:
        return False
    if trig.startswith("group_as_median_abs_z"):
        return "L3" in fired
    if trig.startswith("regime=="):
        return "L5" in fired
    if trig.startswith("n_obs<"):
        n = state.get("n_obs")
        L = ctrl.get("value", 5)
        return n is not None and n < 2 * L + 8
    return False


def resolve(cid: str, history: list | None = None, state: dict | None = None,
            lock_book: dict | None = None, ssot: dict | None = None) -> dict:
    """單參數決策流:F 固定 → D 滾動 → H 條件鎖。回 {value, mode, why}。"""
    ssot = ssot or load_ssot()
    c = controls(ssot)
    if cid not in c:
        return {"id": cid, "value": None, "mode": "UNKNOWN", "why": "冊無此控項(誠實)"}
    ctrl = c[cid]
    base = ctrl.get("value")
    ptype = ctrl.get("param_type", "F")
    state = state or {}
    lock_book = lock_book if lock_book is not None else {}
    if ptype == "F":
        return {"id": cid, "value": base, "mode": "FIXED", "why": "Type-F 憲法"}
    # Type-H:先看鎖
    if ptype == "H":
        if cid in lock_book and lock_book[cid].get("remaining", 0) > 0:
            lb = lock_book[cid]
            lb["remaining"] -= 1
            return {"id": cid, "value": lb["value"], "mode": "LOCKED",
                    "why": f"鎖定中({lb['reason']};餘 {lb['remaining']} 日)"}
        fired = evaluate_locks(state, ssot)
        if _lock_applies(ctrl, fired, state):
            lk = ctrl.get("lock", {})
            hold = int(lk.get("hold_days", c.get("C-20", {}).get("value", 4)))
            lv = lk.get("lock_value", "pre_trigger_median_20d")
            if lv == "pre_trigger_median_20d":
                hist = [h for h in (history or [])[-21:-1] if h is not None]
                val = statistics.median(hist) if len(hist) >= 5 else base
            else:
                val = lv
            if hold > 0:
                lock_book[cid] = {"value": val, "remaining": hold - 1,
                                  "reason": ",".join(fired) or lk.get("trigger", ""), "since": NOW}
            return {"id": cid, "value": val, "mode": "LOCKED",
                    "why": f"觸發 {','.join(fired) or lk.get('trigger', '')}(鎖 {hold} 日)"}
    # Type-D / 未鎖之 H:滾動
    roll = ctrl.get("rolling", {})
    stat = roll.get("stat", "quantile")
    hist = [h for h in (history or []) if h is not None]
    win = int(roll.get("window", 60))
    if stat == "quantile":
        if len(hist) < 8:
            return {"id": cid, "value": base, "mode": "FALLBACK",
                    "why": f"樣本 {len(hist)}<8 誠實退回基值"}
        val = _quantile(hist[-win:], float(roll.get("q", 0.5)))
        if "floor" in roll:
            val = max(val, float(roll["floor"]))
        return {"id": cid, "value": round(val, 4), "mode": "ROLLING",
                "why": f"滾動 P{int(float(roll.get('q', 0.5)) * 100)}(視窗 {min(len(hist), win)})"}
    if stat in ("ic_weight", "rank_ic_weight"):
        # history=[{"ic_lead":x,"ic_att":y}...]:領先性權重=|IC_lead|/(|IC_lead|+|IC_att|),有界
        pairs = [h for h in (history or []) if isinstance(h, dict)]
        if len(pairs) < 8:
            return {"id": cid, "value": base, "mode": "FALLBACK", "why": "IC 樣本<8 誠實退回基值"}
        a = abs(statistics.mean(p.get("ic_lead", 0.0) for p in pairs[-win:]))
        b = abs(statistics.mean(p.get("ic_att", 0.0) for p in pairs[-win:]))
        w = a / (a + b) if (a + b) > 0 else base
        lo, hi = roll.get("bounds", [0.0, 1.0])
        return {"id": cid, "value": round(min(max(w, lo), hi), 4), "mode": "ROLLING",
                "why": f"Rank-IC 定權(|IC_lead| {a:.3f} vs |IC_att| {b:.3f};界 [{lo},{hi}])"}
    if stat == "in_group_rank_pct":
        return {"id": cid, "value": base, "mode": "ROLLING",
                "why": f"族群內排名律(掉出前 {int(float(roll.get('threshold', 0.3)) * 100)}% 連 {base} 日)"}
    return {"id": cid, "value": base, "mode": "FALLBACK", "why": f"未知滾動統計 {stat}"}


def calibrate(histories: dict, state: dict, lock_book: dict | None = None,
              ssot: dict | None = None, write: bool = True) -> dict:
    """全家校準:逐參數解析,出族譜條目(哪些動態/哪些鎖定/原因/時間)。"""
    ssot = ssot or load_ssot()
    lock_book = lock_book if lock_book is not None else {}
    fired = evaluate_locks(state, ssot)
    rows = [resolve(cid, histories.get(cid), state, lock_book, ssot)
            for cid in controls(ssot)]
    modes = {}
    for r in rows:
        modes[r["mode"]] = modes.get(r["mode"], 0) + 1
    entry = {"ts": NOW, "ssot": ssot["ssot_id"], "fired_triggers": fired, "modes": modes,
             "params": rows, "lock_book": lock_book,
             "state_snapshot": {k: v for k, v in state.items() if isinstance(v, (int, float, str))}}
    if write:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        book = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {"entries": []}
        book["entries"].append(entry)
        LEDGER.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    return entry


# ─────────────────────────── 命令 ───────────────────────────

def cmd_family() -> int:
    ssot = load_ssot()
    print(f"  ═ 參數家族({ssot['ssot_id']} · {ssot['asof']})═")
    for t in ("F", "D", "H"):
        print(f"  [Type-{t}] {ssot['family_doctrine'][t]}")
        for c in ssot["controls"]:
            if c.get("param_type") == t:
                roll = c.get("rolling", {})
                extra = (f" 滾動 {roll.get('stat')} q={roll.get('q')} w={roll.get('window')}" if roll else "")
                lk = c.get("lock", {})
                extra += (f" 鎖:{lk.get('trigger')}→{lk.get('lock_value')}/{lk.get('hold_days')}日" if lk else "")
                print(f"    {c['id']:<6} {c['name']:<22} 基值 {c['value']}{extra}")
    print(f"  [鎖觸] {'; '.join(t['id'] + ':' + t['rule'] for t in ssot['lock_triggers'])}")
    return 0


def cmd_calibrate(path: str) -> int:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    e = calibrate(cfg.get("histories", {}), cfg.get("state", {}))
    print(f"  [校準] 模式 {e['modes']} · 觸發 {e['fired_triggers'] or '無'} · 族譜 {LEDGER.name}")
    for r in e["params"]:
        print(f"    {r['id']:<6} {str(r['value']):<8} {r['mode']:<9} {r['why']}")
    return 0


def selftest() -> int:
    ok, total = 0, 8
    ssot = load_ssot()
    c = controls(ssot)
    # ① 冊載三型齊全+新控項在位
    if all(c[k]["param_type"] == t for k, t in (("C-02", "F"), ("C-03", "D"), ("C-05", "H"))) \
       and "C-01b" in c and c["C-01b"]["value"] == 0.55 and "C-16" in c:
        ok += 1; print("  [PASS] 冊載三型分家+C-01b/C-16 新控項在位")
    else:
        print("  [FAIL] 冊載")
    # ② F 固定
    r = resolve("C-02", history=[0.5] * 100, state={"clean_mkt_z": 9}, ssot=ssot)
    if r["mode"] == "FIXED" and r["value"] == 0.05:
        ok += 1; print("  [PASS] Type-F 憲法優先(任何狀態皆固定)")
    else:
        print(f"  [FAIL] F:{r}")
    # ③ D 滾動分位+樣本閘
    r1 = resolve("C-03", history=[0.1, 0.2, 0.3], ssot=ssot)
    r2 = resolve("C-03", history=[i / 100 for i in range(1, 101)], ssot=ssot)
    if r1["mode"] == "FALLBACK" and r2["mode"] == "ROLLING" and 0.85 < r2["value"] < 0.95:
        ok += 1; print("  [PASS] Type-D 滾動分位(P80)+樣本<8 誠實 FALLBACK")
    else:
        print(f"  [FAIL] D:{r1}/{r2}")
    # ④ D 下限(C-01 floor 0.30)
    r = resolve("C-01", history=[0.1] * 60, ssot=ssot)
    if r["mode"] == "ROLLING" and r["value"] == 0.30:
        ok += 1; print("  [PASS] Type-D 滾動值受冊載下限保護(C-01 floor 0.30)")
    else:
        print(f"  [FAIL] floor:{r}")
    # ⑤ H 平常滾動
    lb = {}
    r = resolve("C-05", history=[0.5 + i * 0.005 for i in range(60)], state={"group_as_median_z": 0.3},
                lock_book=lb, ssot=ssot)
    if r["mode"] == "ROLLING" and not lb:
        ok += 1; print("  [PASS] Type-H 平常滾動(無觸發不鎖)")
    else:
        print(f"  [FAIL] H roll:{r}")
    # ⑥ H 觸發鎖定=觸發前 20 日中位數+鎖期倒數
    hist = [0.60] * 40 + [0.70] * 20 + [0.95]
    lb = {}
    r = resolve("C-05", history=hist, state={"group_as_median_z": 3.1}, lock_book=lb, ssot=ssot)
    r_next = resolve("C-05", history=hist, state={"group_as_median_z": 0.0}, lock_book=lb, ssot=ssot)
    if r["mode"] == "LOCKED" and r["value"] == 0.70 and r_next["mode"] == "LOCKED" \
       and lb["C-05"]["remaining"] == 2:
        ok += 1; print("  [PASS] Type-H 觸發 L3 鎖定(值=觸發前 20 日中位 0.70;鎖 4 日倒數)")
    else:
        print(f"  [FAIL] H lock:{r}/{r_next}/{lb}")
    # ⑦ Risk-Off 鎖 C-13 領先性權重→0.35;IC 定權有界
    r = resolve("C-13", history=[{"ic_lead": 0.08, "ic_att": 0.02}] * 30, state={"regime": "RISK_OFF"}, lock_book={}, ssot=ssot)
    r2 = resolve("C-13", history=[{"ic_lead": 0.08, "ic_att": 0.02}] * 30, state={"regime": "RISK_ON"}, lock_book={}, ssot=ssot)
    if r["mode"] == "LOCKED" and r["value"] == 0.35 and r2["mode"] == "ROLLING" and r2["value"] == 0.60:
        ok += 1; print("  [PASS] C-13 Risk-Off 鎖 0.35;Risk-On Rank-IC 定權受界 [0.30,0.60]")
    else:
        print(f"  [FAIL] C-13:{r}/{r2}")
    # ⑧ 加速視窗不失敏
    if adaptive_window(60, 0.5, ssot) == 60 and adaptive_window(60, 3.0, ssot) == 30 \
       and adaptive_window(20, 3.0, ssot) == 15:
        ok += 1; print("  [PASS] 加速視窗(Shock 減半、不低於 C-22=15)")
    else:
        print("  [FAIL] 視窗")
    print(f"  [計] {ok}/{total} 檢通過")
    return 0 if ok == total else 1


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "--selftest":
        return selftest()
    if a[0] == "--family":
        return cmd_family()
    if a[0] == "--calibrate" and len(a) > 1:
        return cmd_calibrate(a[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
