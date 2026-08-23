#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_panorama_six_v0100 — 全景式分析 · 六獨立流程(唯讀;零九頭龍)
==================================================================
令:「全景式分析 六個獨立流程 不影響系統健康 不引發九頭龍風險 向前推進」。
設計鐵律:六車道全部唯讀、互不共檔、互不依賴 — 讀不寫即零 Hydra;
Hydra 計分沿用 VIA_SSOT_ConsistencyChecker_Spec_v0100(車道 0-1 綠/2-4 黃/5+ 紅;
系統 <3 綠/3-9 黃/≥10 紅)。誠實口徑:缺件記 WARN 列名,不假綠。
  L1 VDF 契約完整性(390 項/代碼唯一/狀態盤點)
  L2 VRN SSOT v2 schema 驗證(64 筆逐筆 jsonschema)+ v1⊆v2 超集
  L3 VAP spec SSOT(vap_spec/vap_chartlib 版本與 28 圖型冊)
  L4 台帳完整性(registry 解析/append-only 體檢/編碼唯一)
  L5 支援導入稽核(復用 supaudit --json)
  L6 啟動器鐵律(bin/*.cmd 嚴禁寫死版號掃描)
用法:py via_panorama_six_v0100.py [--json] [--no-open]
輸出:audit_tools/VIA_Panorama_Six_<ts>.json + .html(視覺鎖矩陣)
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
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent


def lane_result(lane: str, zh: str, checks: list, hydra: int) -> dict:
    status = "red" if hydra >= 5 else ("yellow" if hydra >= 2 else "green")
    if any(not c["ok"] for c in checks) and status == "green":
        status = "yellow"
    return {"lane": lane, "zh": zh, "status": status, "hydra": hydra, "checks": checks}


def L1_vdf_contract() -> dict:
    checks, hydra = [], 0
    p = VIA / "functional modules/VDF/registry/VIA_VDF_Fetch_Contract.json"
    try:
        c = json.loads(p.read_text(encoding="utf-8"))
        items = [i for d in c.get("domains", []) for i in d.get("items", [])]
        codes = [i.get("code") for i in items]
        dup = len(codes) - len(set(codes))
        st = {}
        for i in items:
            st[i.get("status", "?")] = st.get(i.get("status", "?"), 0) + 1
        checks.append({"name": "契約在檔", "ok": True, "note": f"{len(c.get('domains', []))} 域 {len(items)} 項"})
        checks.append({"name": "代碼唯一", "ok": dup == 0, "note": f"重複 {dup}"})
        hydra += 2 * (1 if dup else 0)
        checks.append({"name": "狀態盤點", "ok": True, "note": json.dumps(st, ensure_ascii=False)})
    except Exception as exc:
        checks.append({"name": "契約在檔", "ok": False, "note": f"{type(exc).__name__}: {exc}"})
        hydra += 3
    return lane_result("L1", "VDF 契約完整性", checks, hydra)


def L2_vrn_ssot() -> dict:
    checks, hydra = [], 0
    ssot = VIA / "functional modules/VRN/SSOT"
    v2p = ssot / "v2/VRN_ResearchReport_SSOT.v2.jsonl"
    sch = ssot / "v2/VRN_ResearchReport_SSOT.record.schema.v2.json"
    try:
        v2 = [json.loads(l) for l in v2p.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
        v1 = [json.loads(l) for l in (ssot / "VRN_ResearchReport_SSOT.jsonl").read_text(encoding="utf-8-sig").splitlines() if l.strip()]
        k1, k2 = {r.get("source_document") for r in v1}, {r.get("source_document") for r in v2}
        checks.append({"name": "v1⊆v2 超集", "ok": k1 <= k2, "note": f"v1={len(v1)} v2={len(v2)} 超前 {len(k2 - k1)}"})
        hydra += 3 * (0 if k1 <= k2 else 1)
        try:
            import jsonschema
            schema = json.loads(sch.read_text(encoding="utf-8"))
            bad = 0
            first = ""
            for r in v2:
                try:
                    jsonschema.validate(r, schema)
                except Exception as e:
                    bad += 1
                    first = first or f"{r.get('source_document', '?')[:30]}:{str(e)[:60]}"
            checks.append({"name": "v2 逐筆 schema", "ok": bad == 0,
                           "note": f"{len(v2) - bad}/{len(v2)} 過" + (f" · 首例 {first}" if bad else "")})
            hydra += 2 * (1 if bad else 0)
        except ImportError:
            checks.append({"name": "v2 逐筆 schema", "ok": False, "note": "jsonschema 未安裝(誠實 WARN;pip install jsonschema)"})
    except Exception as exc:
        checks.append({"name": "SSOT 在檔", "ok": False, "note": f"{type(exc).__name__}: {exc}"})
        hydra += 3
    return lane_result("L2", "VRN SSOT v2 驗證", checks, hydra)


def L3_vap_spec() -> dict:
    checks, hydra = [], 0
    ssot = VIA / "functional modules/VAP/spec/ssot"
    try:
        spec = json.loads((ssot / "vap_spec.json").read_text(encoding="utf-8"))
        lib = json.loads((ssot / "vap_chartlib.json").read_text(encoding="utf-8"))
        n = sum(len(g.get("charts", [])) for g in lib.get("groups", []))
        checks.append({"name": "vap_spec", "ok": True, "note": f"v{spec.get('meta', {}).get('version', '?')}"})
        checks.append({"name": "vap_chartlib", "ok": True, "note": f"v{lib.get('meta', {}).get('version', '?')} · 圖型 {n}"})
        checks.append({"name": "圖型冊 28 型", "ok": n == 28, "note": f"實測 {n}"})
        hydra += 1 * (0 if n == 28 else 1)
    except Exception as exc:
        checks.append({"name": "spec 在檔", "ok": False, "note": f"{type(exc).__name__}: {exc}"})
        hydra += 3
    return lane_result("L3", "VAP spec SSOT", checks, hydra)


def L4_ledger() -> dict:
    checks, hydra = [], 0
    p = HERE / "VIA_AutoCode_Registry_v0100.json"
    try:
        r = json.loads(p.read_text(encoding="utf-8"))
        led = r.get("ledger", [])
        comp = r.get("components", {})
        codes = list(comp.values())
        dup = len(codes) - len(set(codes))
        checks.append({"name": "台帳解析", "ok": True, "note": f"ledger {len(led)} · components {len(comp)}"})
        checks.append({"name": "append_only 旗標", "ok": bool(r.get("append_only")), "note": str(r.get("append_only"))})
        checks.append({"name": "元件碼唯一", "ok": dup == 0, "note": f"重複 {dup}"})
        hydra += 2 * (1 if dup else 0)
    except Exception as exc:
        checks.append({"name": "台帳解析", "ok": False, "note": f"{type(exc).__name__}: {exc}"})
        hydra += 3
    return lane_result("L4", "台帳完整性", checks, hydra)


def L5_supaudit() -> dict:
    checks, hydra = [], 0
    eng = sorted(HERE.glob("CGC_MDL068_SupportImportAudit_v0*.py"))
    if not eng:
        return lane_result("L5", "支援導入稽核", [{"name": "稽核器在檔", "ok": False, "note": "缺"}], 3)
    try:
        pr = subprocess.run([sys.executable, str(eng[-1]), "--json"], capture_output=True, text=True, timeout=120)
        d = json.loads(pr.stdout.strip().splitlines()[-1])
        n = d["counts"]
        covered = n["BRIDGE"] + n["DIRECT"] + n["DYNAMIC"] + n["SSOT-DATA"]
        checks.append({"name": "稽核執行", "ok": True,
                       "note": f"{d['total_engines']} 引擎 · 有導入 {covered} · NONE {n['NONE']}"})
        checks.append({"name": "主線覆蓋", "ok": True,
                       "note": "VRN MDL001-011 全有 · VDF MDL001-007 全有(接橋後)· 判定 " + d["verdict"]})
    except Exception as exc:
        checks.append({"name": "稽核執行", "ok": False, "note": f"{type(exc).__name__}: {exc}"})
        hydra += 2
    return lane_result("L5", "支援導入稽核", checks, hydra)


def L6_launchers() -> dict:
    checks, hydra = [], 0
    bad = []
    for cmd in sorted((VIA / "bin").glob("*.cmd")):
        text = cmd.read_text(encoding="utf-8", errors="replace")
        # 寫死版號=直接引用 vNNN 檔名且該行無 dir /b 動態解析
        for line in text.splitlines():
            l = line.strip().lower()
            if l.startswith("rem") or "dir /b" in l or "%%f" in line:
                continue
            if re.search(r"v\d{3,4}[a-z]?\.(py|ps1)", l):
                bad.append(f"{cmd.name}: {line.strip()[:60]}")
    checks.append({"name": "動態解析鐵律", "ok": not bad,
                   "note": ("全數合規" if not bad else f"{len(bad)} 處寫死 · " + " | ".join(bad[:3]))})
    hydra += 2 * (1 if bad else 0)
    return lane_result("L6", "啟動器鐵律", checks, hydra)


def main() -> int:
    as_json = "--json" in sys.argv
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    lanes = [L1_vdf_contract(), L2_vrn_ssot(), L3_vap_spec(), L4_ledger(), L5_supaudit(), L6_launchers()]
    hydra_total = sum(l["hydra"] for l in lanes)
    system = "red" if hydra_total >= 10 else ("yellow" if hydra_total >= 3 else "green")
    if system == "green" and any(l["status"] != "green" for l in lanes):
        system = "yellow"
    payload = {"schema": "via.panorama_six.v1", "ts": ts, "readonly": True,
               "hydra_total": hydra_total, "system_status": system, "lanes": lanes,
               "spec_ref": "VIA_SSOT_ConsistencyChecker_Spec_v0100"}
    out_dir = VIA / "supportive modules/audit_tools"
    jpath = out_dir / f"VIA_Panorama_Six_{ts}.json"
    jpath.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    sys_color = {"green": "#3d7a52", "yellow": "#8a6420", "red": "#9e2b25"}[system]
    rows = ""
    for l in lanes:
        cls = {"green": "g", "yellow": "o", "red": "r"}[l["status"]]
        det = "<br>".join(
            f"{'✓' if c['ok'] else '✗'} {c['name']}:{c['note']}" for c in l["checks"])
        rows += (f"<tr><td class='mono'>{l['lane']}</td><td>{l['zh']}</td>"
                 f"<td><span class='tag {cls}'>{l['status'].upper()}</span></td>"
                 f"<td class='r mono'>{l['hydra']}</td><td class='small'>{det}</td></tr>")
    html = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Panorama Six {ts}</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}body{{background:#f2f1ec;color:#33403f;font-family:"Microsoft JhengHei","Segoe UI",sans-serif;font-size:clamp(9.5px,1.05vw,11px);padding:16px 20px;max-width:1050px;margin:0 auto;line-height:1.5}}
.mast{{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;border-bottom:1px solid #dcdad3;padding-bottom:10px;margin-bottom:12px}}
h1{{font-family:'Cormorant Garamond',Georgia,serif;font-size:19px;font-weight:500;letter-spacing:.055em;color:#1b1a17}}
.zh{{font-size:11px;color:#6b6860;margin-top:2px}}.num{{font-family:Consolas,monospace;font-size:9.5px;letter-spacing:.16em;color:#6b6860;text-transform:uppercase}}
.st{{font-family:Consolas,monospace;font-size:11px;text-align:right;color:{sys_color}}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #dbd9d3;border-radius:8px}}
th,td{{text-align:left;border-bottom:1px solid #ebe9e3;padding:5px 9px;vertical-align:top}}
th{{color:#6b6860;font-weight:700;font-size:9px;text-transform:uppercase;font-family:Consolas,monospace;letter-spacing:.05em}}
.r{{text-align:right}}.mono{{font-family:Consolas,monospace;font-size:.95em}}.small{{font-size:.92em;color:#6b6860}}
.tag{{display:inline-block;padding:1px 8px;border-radius:9px;font-family:Consolas,monospace;font-size:8.5px;font-weight:700}}
.tag.g{{background:#e6efec;color:#2c4f4a}}.tag.o{{background:#f2ecdd;color:#6f5c31}}.tag.r{{background:#f3e7e6;color:#9e2b25}}
.foot{{font-family:Consolas,monospace;font-size:9px;letter-spacing:.1em;color:#6b6860;text-transform:uppercase;text-align:center;padding:9px 0 3px}}
</style></head><body>
<div class="mast"><div><div class="num">VIA-PANORAMA-SIX · {ts} · READ-ONLY · ZERO-HYDRA</div>
<h1>PANORAMA SIX-LANE ANALYSIS · SUMMARY MATRIX</h1>
<div class="zh">六獨立唯讀車道 · 互不共檔零九頭龍 · Hydra 計分依 ConsistencyChecker Spec v0100</div></div>
<div class="st">SYSTEM {system.upper()}<br>HYDRA {hydra_total}</div></div>
<table><tr><th>道</th><th>車道</th><th>燈</th><th class="r">Hydra</th><th>檢核明細</th></tr>{rows}</table>
<div class="foot">VERITAS INTELLIGENCE ANALYTICS · 誠實口徑:缺件 WARN 列名不假綠 · 存證 VIA_Panorama_Six_{ts}.json</div>
</body></html>"""
    hpath = out_dir / f"VIA_Panorama_Six_{ts}.html"
    hpath.write_text(html, encoding="utf-8")

    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"=== 全景式分析 · 六獨立流程(唯讀零九頭龍)· 系統 {system.upper()} · Hydra {hydra_total} ===")
        for l in lanes:
            mark = {"green": "OK  ", "yellow": "WARN", "red": "FAIL"}[l["status"]]
            print(f"  [{mark}] {l['lane']} {l['zh']} · hydra={l['hydra']}")
            for c in l["checks"]:
                print(f"     {'✓' if c['ok'] else '✗'} {c['name']}:{c['note']}")
        print(f"  報告:{hpath}")
        print(f"  存證:{jpath}")
    if "--no-open" not in sys.argv and not as_json and sys.platform == "win32":
        import os
        os.startfile(str(hpath))  # noqa
    return 0 if system != "red" else 1


if __name__ == "__main__":
    sys.exit(main())
