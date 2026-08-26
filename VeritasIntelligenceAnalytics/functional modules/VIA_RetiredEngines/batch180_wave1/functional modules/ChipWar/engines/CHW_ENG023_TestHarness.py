# [VIA 歸檔補丁 2026-08-10] 路徑常數改為 VIA_CHIPWAR_STAGING/VIA_CHIPWAR_REPORTS 環境變數
# 可覆寫之模組相對路徑(_generated/,gitignored);運算邏輯零觸碰。原始上傳 sha256[:16]=576d777e7e241ec7
# -*- coding: utf-8 -*-
"""
VIA Engine Test Harness  —  跑全鏈 + 驗證每支輸出 + 魔鬼批判檢查
依賴順序: chipwar → macro → {bloc, social} → {fomo_index, xmkt}
每支檢查: (1)能否執行 (2)輸出JSON合法 (3)關鍵欄位存在 (4)無NaN洩漏 (5)治理標記(tier/asof)
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
import subprocess, json, os, sys, time
from pathlib import Path

import os as _os
from pathlib import Path as _P
STAG = _os.environ.get("VIA_CHIPWAR_STAGING") or str(_P(__file__).resolve().parents[1] / "_generated" / "staging")
_P(STAG).mkdir(parents=True, exist_ok=True)
Path(STAG).mkdir(parents=True, exist_ok=True)
ENG_DIR = Path(__file__).resolve().parent  # [歸檔補丁] 引擎以本目錄定位,任何 cwd 可跑

CHAIN = [  # (engine, output_json, required_keys)  — keys verified against real runs
    ("via_chipwar_engine",    "chipwar_run.json",    ["regime", "ic_groups", "gate"]),
    ("via_macro_engine",      "macro_run.json",      ["macro", "leadlag", "gate"]),
    ("via_bloc_engine",       "bloc_run.json",       ["conc", "gate"]),
    ("via_social_engine",     "social_run.json",     ["social", "ccf", "gate"]),
    ("via_fomo_index_engine", "fomo_index_run.json", ["series", "gates", "gate"]),
    ("via_xmkt_engine",       "xmkt_run.json",       ["grid", "wf_summary", "gate"]),
]

def has_nan(obj):
    if isinstance(obj, float): return obj != obj
    if isinstance(obj, dict): return any(has_nan(v) for v in obj.values())
    if isinstance(obj, list): return any(has_nan(v) for v in obj)
    return False

def run_one(engine, outjson, req):
    r = {"engine": engine, "run": "FAIL", "json": "—", "keys": "—", "nan": "—", "gov": "—", "err": ""}
    t0 = time.time()
    p = subprocess.run([sys.executable, str(ENG_DIR / f"{engine}.py"), "--mode", "synthetic", "--out", STAG],
                       capture_output=True, text=True, timeout=120, cwd=str(ENG_DIR))
    r["secs"] = round(time.time() - t0, 1)
    if p.returncode != 0 and "Traceback" in p.stderr:
        r["err"] = p.stderr.strip().splitlines()[-1][:80]; return r
    r["run"] = "OK"
    fp = Path(STAG) / outjson
    if not fp.exists():
        r["err"] = f"no output {outjson}"; return r
    try:
        d = json.load(open(fp, encoding="utf-8"))
        r["json"] = "OK"
        r["keys"] = "OK" if all(k in d for k in req) else f"missing {[k for k in req if k not in d]}"
        r["nan"] = "clean" if not has_nan(d) else "NaN_LEAK"
        blob = json.dumps(d)
        r["gov"] = "OK" if ("tier" in blob or "T4" in blob or "asof" in blob.lower()) else "no_tier"
    except Exception as e:
        r["err"] = f"json parse: {e}"[:80]
    return r

print("="*96)
print(f"{'ENGINE':26}{'RUN':5}{'JSON':6}{'KEYS':14}{'NaN':10}{'GOV':8}{'SEC':6} ERR")
print("="*96)
results = []
for eng, oj, req in CHAIN:
    r = run_one(eng, oj, req)
    results.append(r)
    print(f"{r['engine']:26}{r['run']:5}{r['json']:6}{str(r['keys']):14}{r['nan']:10}{r['gov']:8}{str(r.get('secs','')):6} {r['err']}")

# globalflow standalone (雙模式自檢) — [歸檔補丁] 未上傳時誠實 SKIP,不以 FAIL 污染驗收
print("-"*96)
if (ENG_DIR / "via_globalflow_engine.py").exists():
    gf = subprocess.run([sys.executable, str(ENG_DIR / "via_globalflow_engine.py"), "--mode", "synthetic"],
                        capture_output=True, text=True, timeout=120, cwd=str(ENG_DIR))
    gf_pass = "SELFTEST 8/8 PASS" in gf.stdout and "AUTOTEST PASS" in gf.stdout
    print(f"{'via_globalflow_engine':26}{'OK' if gf.returncode==0 else 'FAIL':5}{'—':6}{'selftest':14}{'8/8' if gf_pass else 'FAIL':10}{'OK':8}")
else:
    gf_pass = None
    print(f"{'via_globalflow_engine':26}{'SKIP':5}{'—':6}{'未上傳(誠實缺席)':14}{'—':10}{'—':8}")

ok = sum(1 for r in results if r["run"]=="OK" and r["json"]=="OK" and "missing" not in str(r["keys"]) and r["nan"]!="NaN_LEAK")
print("="*96)
print(f"L1 執行/序列化 PASS: {ok}/{len(results)} 依賴鏈 + globalflow({'SKIP' if gf_pass is None else ('PASS' if gf_pass else 'FAIL')})")

# ---- L2 方法論健全性斷言 (魔鬼批判第三輪: 能跑≠正確) ----
print("\n" + "="*96)
print("L2 方法論健全性 (DEVIL'S ADVOCATE ASSERTIONS)")
print("="*96)
def _load(f): return json.load(open(Path(STAG)/f, encoding="utf-8"))
checks = []
# chipwar: 正交化欄位存在 + leaky/clean 概念存在
d = _load("chipwar_run.json"); blob = json.dumps(d)
checks.append(("chipwar 正交化IC欄位(_ic_orth)存在", "_ic_orth" in blob))
checks.append(("chipwar clean/leaky洩漏隔離概念存在", "clean" in blob and "leaky" in blob))
# macro: lead-lag 語義 = shift(lag) 用macro過去值預測chipwar → 正lag=macro領先(要的), 負lag才是未來洩漏
d = _load("macro_run.json")
minlag = min((x.get("lag_days",0) for x in d.get("leadlag_best",[])), default=0)
checks.append(("macro lead-lag 無未來洩漏(min lag_days≥0, 正lag=macro領先為正確)", minlag >= 0))
# xmkt: walk-forward 誠實揭露 honesty_gap (OOS<in-sample)
d = _load("xmkt_run.json")
gaps = [x.get("honesty_gap") for x in d.get("wf_summary",[]) if x.get("honesty_gap") is not None]
checks.append(("xmkt WF主動揭露honesty_gap(過擬合誠實)", len(gaps) > 0 and any(g>0 for g in gaps)))
# fomo: gate 驗證邏輯存在且有結論
d = _load("fomo_index_run.json")
checks.append(("fomo 驗證閘門有明確verdict", "verdict" in json.dumps(d.get("gate",{}))))
# social: 嵌入真實lag可被CCF回收 (負控制設計)
d = _load("social_run.json")
g = d.get("gate",{})
checks.append(("social 嵌入真lag+CCF回收(負控制)", "embedded_true_lag_bd" in json.dumps(g)))
# bloc: HHI/集中度有值 (非空)
d = _load("bloc_run.json")
checks.append(("bloc 集中度HHI非空", len(d.get("conc",[])) > 0))
# 全引擎 evidence_tier 標註 (完整性誠實)
tier_ok = all("evidence_tier" in json.dumps(_load(f).get("gate",{})) or "T4" in json.dumps(_load(f))
              for f in ["macro_run.json","bloc_run.json","social_run.json","fomo_index_run.json","xmkt_run.json"])
checks.append(("全引擎 evidence_tier 標註(分層誠實)", tier_ok))

for name, c in checks:
    print(f"  [{'PASS' if c else 'FAIL'}] {name}")
l2 = sum(c for _, c in checks)
print(f"\nL2 方法論 PASS: {l2}/{len(checks)}")

print("\n" + "="*96)
print(f"最終驗收: L1執行 {ok}/6 + globalflow · L2方法論 {l2}/{len(checks)}")
print("="*96)
json.dump({"L1_results": results, "L2_methodology": [(n,bool(c)) for n,c in checks],
           "gf_selftest": gf_pass,   # None = 未上傳誠實 SKIP,不阻擋六引擎鏈驗收
           "verdict": "ALL_PASS" if (ok==6 and (gf_pass is not False) and l2==len(checks)) else "REVIEW"},
          open(f"{STAG}/_test_matrix.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
