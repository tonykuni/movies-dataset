# -*- coding: utf-8 -*-
"""via_governance_console_v0100.py — 中央治理台輔助工具 v0100(操作員令:Console 功能 JSON 化+母版導入+輔助工具)。

功能:載入 VIA_CentralGovernance_Console_v0100.json,逐功能驗證:
  ① 引擎在位(engine_glob 動態解析,嚴禁寫死版號)② 動詞在位(bin/<verb>.cmd)③ 資料面在位
輸出誠實矩陣(OK/WARN 逐列);--json 供母版/程式取用。exit=缺引擎數。
用法:py via_governance_console_v0100.py [--json]
"""
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
import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
CANON = HERE / "VIA_CentralGovernance_Console_v0100.json"


def check():
    d = json.loads(CANON.read_text(encoding="utf-8"))
    rows = []
    for sec in d["sections"]:
        for f in sec["functions"]:
            hits = sorted(glob.glob(str(VIA / f["engine_glob"]))) if f["engine_glob"] != "—" else []
            eng = Path(hits[-1]).name if hits else ""
            verb = f["verb"].split()[0] if f["verb"] != "—" else ""
            verb_ok = (VIA / "bin" / (verb + ".cmd")).exists() if verb else None
            data_ok = None
            dp = f.get("data", "—")
            if dp not in ("—", "") and "*" not in dp and "(" not in dp and "+" not in dp and " " not in dp:
                data_ok = (VIA / dp).exists()
            ok = bool(hits)
            rows.append({"section": sec["zh"], "id": f["id"], "zh": f["zh"], "verb": f["verb"],
                         "engine": eng, "engine_ok": ok, "verb_ok": verb_ok, "data_ok": data_ok,
                         "note": f["note"]})
    return d, rows


def main(argv):
    d, rows = check()
    missing = [r for r in rows if not r["engine_ok"]]
    if "--json" in argv:
        print(json.dumps({"schema": d["schema"], "asof": d["asof"],
                          "functions": rows, "missing_engines": len(missing)},
                         ensure_ascii=False, indent=1))
        return len(missing)
    print("=== VIA Central Governance Console v0100(%s)===" % d["asof"])
    sec = ""
    for r in rows:
        if r["section"] != sec:
            sec = r["section"]
            print("  ── %s ──" % sec)
        e = "OK " if r["engine_ok"] else "缺 "
        v = ("動詞OK" if r["verb_ok"] else "動詞缺") if r["verb_ok"] is not None else "  —  "
        dd = ("料OK" if r["data_ok"] else "料缺") if r["data_ok"] is not None else " — "
        print("  [%s] %-6s %-26s %-16s %s · %s · %s"
              % (e, r["id"], r["zh"][:26], (r["verb"] or "—")[:16], v, dd, r["engine"] or "(引擎缺席)"))
    print("  紅線 %d 條在冊 · 功能 %d · 引擎缺 %d(誠實口徑)"
          % (len(d["red_lines"]), len(rows), len(missing)))
    return len(missing)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
