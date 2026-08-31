#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAP_ENG011_TemplateRegistry — TPN 模板編號冊引擎(批250 立;批251 斷點清零)
====================================================================
操作員令(語音解碼):「七函式登記代碼+描述+去冗;VAP 使用者流程
逐步稽核找連接點補斷;單圖=分析視覺資產;資料連結綁模板=更新即
同步;模板關聯→同時間軸上下同步堆疊圖;雙軸各帶唯一號;模板編號
TPN-001,更新模板=引用圖全部同時更新」。
機制(append-only 台帳;hash 定生死去冗;收容 spec 原地不動):
  ①七函式冊:Workflow_Spec v023 workflow 七步(連線與更新/新增圖/
    繪好圖/儲存圖像/擷取特定圖/堆圖編排/預覽與匯出)→WF-01..07
    代碼+描述+truthBoundary;同 id 重複=去冗;連接點矩陣=每步對位
    現役引擎(缺對位=斷點誠實列)
  ②TPN 模板冊:圖庫 compose(Workbench 存檔)→單圖/雙軸模板
    TPN-001..(雙軸=每軸唯一號 TPN-xxx.AX1/AX2=L/R);data_link=
    db 來源+adapter(綁模板;資料更新→重跑 register=同 hash 冪等/
    異 hash=新版列 superseded=只增不減)
  ③複合堆疊冊:stack 成員→TPN-C001..(time_sync=true;order=
    top_to_last 同時間軸上下同步);複合存 TPN 引用非複本→
    更新成員模板=所有引用複合圖同時更新(操作員令核心)
輸出:registry/VIA_VAP_TemplateRegistry_v0100.json(append-only)
  +VIA_UI_TemplateRegistry_v0100.html 三區冊頁
用法:python3 VAP_ENG011_TemplateRegistry_v0101.py register|compose
      TPN-001,TPN-002 | --selftest
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

import hashlib
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VAP = HERE.parent
VIA = VAP.parent.parent
INTAKE = VAP / "references" / "intake"
REG = VIA / "supportive modules" / "registry" / "VIA_VAP_TemplateRegistry_v0100.json"
OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_TemplateRegistry_v0100.html"

# 連接點對位冊:七步→現役引擎/資產(缺=None=斷點誠實)
STEP_LINK = {
    "refreshRequest": "CGC_MDL095 DeckServer 橋+VDF OmniFetch(唯讀請求台帳)",
    "addChart": "VAP_ENG001 Chartlib(CH-01..24)+ENG010 runtime SSOT",
    "renderChart": "VAP_ENG003 Seaborn/Plotly 渲染道",
    "saveGovernedImage": "VAP_ENG012 GovernedImageStore(批251 補斷;sha 冪等+TPN 連結+append-only 台帳)",
    "selectSpecificSavedImage": "Workbench savedImageSelection(收容 v023)",
    "composeSharedTimeStack": "VAP v007 --panels 同時間軸堆疊(CH-09)+本冊 TPN-C",
    "explicitUserExport": "Workbench 匯出契約(收容 v023)",
}


def _h8(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False,
                                     sort_keys=True).encode()).hexdigest()[:8]


def _ver_key(p: Path) -> tuple:
    vs = [tuple(int(x) for x in m.groups() if x)
          for m in re.finditer(r"v(\d+)", p.name)]
    return max(vs) if vs else (0,)


def _newest(pat: str, root: Path) -> Path | None:
    hits = [p for p in root.rglob(pat) if p.is_file()]
    return max(hits, key=_ver_key) if hits else None


def _load_reg() -> dict:
    if REG.exists():
        return json.loads(REG.read_text(encoding="utf-8"))
    return {"functions": [], "templates": [], "composites": [],
            "note": "append-only;hash 定生死;複合存 TPN 引用非複本="
                    "更新模板=引用圖全同步"}


def _save_reg(reg: dict):
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1),
                   encoding="utf-8")


def register(intake: Path | None = None) -> int:
    intake = intake or INTAKE
    spec_p = _newest("VIA_VAP_User_Workflow_Spec_v*.json", intake)
    lib_p = _newest("VAP_Chart_Library*.json", intake)
    if spec_p is None and lib_p is None:
        print("[TPN 冊] 收容缺(spec/圖庫皆無)=誠實停")
        return 2
    reg = _load_reg()
    n_new = n_skip = 0
    # ①七函式冊(去冗=同 id 冪等)
    if spec_p:
        spec = json.loads(spec_p.read_text(encoding="utf-8-sig"))
        seen = {f["id"] for f in reg["functions"]}
        for s in spec.get("workflow", []):
            if s["id"] in seen:
                # 批251:連接點態刷新(engine_link=衍生態;斷點補上即改綠)
                ex = next(f for f in reg["functions"] if f["id"] == s["id"])
                link = STEP_LINK.get(s["id"])
                new_state = "LINKED" if link else "GAP(斷點候補)"
                if ex.get("engine_link") != link or ex.get("state") != new_state:
                    ex["engine_link"], ex["state"] = link, new_state
                    n_new += 1               # 態刷新計入異動
                else:
                    n_skip += 1
                continue
            seen.add(s["id"])                 # 冊內同 id 去冗
            link = STEP_LINK.get(s["id"])
            reg["functions"].append({
                "code": f"WF-{int(s['step']):02d}", "id": s["id"],
                "label": s.get("label", ""),
                "desc": s.get("success", ""),
                "truth_boundary": s.get("truthBoundary", ""),
                "engine_link": link,
                "state": "LINKED" if link else "GAP(斷點候補)"})
            n_new += 1
    # ②TPN 模板冊(compose→單圖/雙軸;hash 冪等/異=新版讓位)
    if lib_p:
        lib = json.loads(lib_p.read_text(encoding="utf-8-sig"))
        comp = lib.get("compose") or {}
        L = comp.get("L") or []
        Rr = comp.get("Rr") or []
        if L or Rr:
            axes = []
            if L:
                axes.append({"axis_id": "AX1", "side": "L", "series": L})
            if Rr:
                axes.append({"axis_id": "AX2", "side": "R", "series": Rr})
            body = {"kind": "dual_axis" if (L and Rr) else "single",
                    "form": comp.get("form", "line"), "axes": axes,
                    "data_link": {"sources": lib.get("db") or [],
                                  "adapter": (lib.get("connect") or {})
                                  .get("adapter")}}
            h = _h8(body)
            live = [t for t in reg["templates"] if not t.get("superseded_by")]
            same = next((t for t in live if t["hash"] == h), None)
            if same:
                n_skip += 1
            else:
                tpn = f"TPN-{len(reg['templates']) + 1:03d}"
                prev = next((t for t in live
                             if t["kind"] == body["kind"]
                             and t["form"] == body["form"]), None)
                entry = {"tpn": tpn, **body, "hash": h,
                         "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                         "note": "單圖=分析視覺資產;資料連結綁模板"}
                entry["axes"] = [{**a, "axis_id": f"{tpn}.{a['axis_id']}"}
                                 for a in axes]    # 雙軸唯一號
                reg["templates"].append(entry)
                if prev:
                    prev["superseded_by"] = tpn    # 只增不減讓位
                n_new += 1
        # ③複合堆疊(stack→TPN-C;引用制=同步更新)
        stack = comp.get("stack") or []
        if stack and reg["templates"]:
            base = reg["templates"][-1]["tpn"]
            cbody = {"members_series": stack, "base_tpn": base,
                     "time_sync": True, "order": "top_to_last"}
            ch = _h8(cbody)
            if not any(c["hash"] == ch for c in reg["composites"]):
                reg["composites"].append({
                    "tpn": f"TPN-C{len(reg['composites']) + 1:03d}",
                    **cbody, "hash": ch,
                    "note": "同時間軸上下同步;存引用非複本=成員模板"
                            "更新→本複合圖同時更新"})
                n_new += 1
            else:
                n_skip += 1
    _save_reg(reg)
    render(reg)
    gaps = sum(1 for f in reg["functions"] if f["state"].startswith("GAP"))
    print(f"[TPN 冊] 新登 {n_new} · 冪等 SKIP {n_skip} · 函式 "
          f"{len(reg['functions'])}(斷點 {gaps})· 模板 "
          f"{len(reg['templates'])} · 複合 {len(reg['composites'])}")
    return 0


def compose(tpns: list[str]) -> int:
    """複合堆疊:成員 TPN 引用(非複本)→同時間軸上下同步"""
    reg = _load_reg()
    known = {t["tpn"] for t in reg["templates"]}
    missing = [t for t in tpns if t not in known]
    if missing:
        print(f"[compose] 未知 TPN {missing}=誠實拒(先 register)")
        return 2
    cbody = {"members": tpns, "time_sync": True, "order": "top_to_last"}
    ch = _h8(cbody)
    if any(c["hash"] == ch for c in reg["composites"]):
        print("[compose] 同組合已在冊(hash 冪等)")
        return 0
    tpn = f"TPN-C{len(reg['composites']) + 1:03d}"
    reg["composites"].append({"tpn": tpn, **cbody, "hash": ch,
                              "note": "引用制=成員更新即全複合同步"})
    _save_reg(reg)
    render(reg)
    print(f"[compose] {tpn} = {' ↓ '.join(tpns)}(同時間軸;上→下)")
    return 0


def render(reg: dict):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    fr = "".join(
        f"<tr class='{'g' if f['state'] == 'LINKED' else 'r'}'>"
        f"<td><b>{f['code']}</b></td><td>{html.escape(f['label'])}</td>"
        f"<td>{html.escape(f['desc'])[:90]}</td>"
        f"<td>{html.escape(f.get('engine_link') or '—')}</td>"
        f"<td>{html.escape(f['state'])}</td></tr>"
        for f in reg["functions"])
    tr = "".join(
        f"<tr class='{'y' if t.get('superseded_by') else 'g'}'>"
        f"<td><b>{t['tpn']}</b></td><td>{t['kind']}/{t['form']}</td>"
        f"<td>{html.escape('; '.join(a['axis_id'] + '=' + ','.join(a['series']) for a in t['axes']))}</td>"
        f"<td>{html.escape(','.join(t['data_link']['sources'])[:60])}</td>"
        f"<td>{t.get('superseded_by') or '現役'}</td></tr>"
        for t in reg["templates"])
    cr = "".join(
        f"<tr class='g'><td><b>{c['tpn']}</b></td>"
        f"<td>{html.escape(' ↓ '.join(c.get('members', c.get('members_series', []))))}</td>"
        f"<td>{'同時間軸' if c['time_sync'] else '—'}</td>"
        f"<td>{html.escape(c['note'])}</td></tr>"
        for c in reg["composites"])
    OUT.write_text(f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VAP TPN 模板冊</title><style>
body{{background:#0b1220;color:#c7d3e8;font:10.5px/1.5 "Segoe UI",
"Noto Sans TC",sans-serif;padding:14px;max-width:1180px;margin:0 auto}}
h1{{font-size:14px;color:#e8eefb}}h2{{font-size:11.5px;color:#4f8ef7;margin:12px 0 4px}}
.sub{{color:#7e8db0;font-size:10px}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;color:#7e8db0;font-size:9.5px;border-bottom:1px solid #1e2a44;padding:2px 6px 2px 0}}
td{{padding:2px 6px 2px 0;border-bottom:1px dashed #1e2a44;overflow-wrap:anywhere}}
tr.g td{{color:#c7d3e8}}tr.y td{{color:#f0b429}}tr.r td{{color:#f87171}}
</style></head><body>
<h1>VAP TPN 模板編號冊(批250)</h1>
<div class="sub">{ts} · 函式 {len(reg['functions'])} · 模板
{len(reg['templates'])} · 複合 {len(reg['composites'])} · append-only ·
hash 定生死去冗 · 複合=引用制(成員模板更新=引用圖全同步)</div>
<h2>① 七函式冊+連接點矩陣(斷點=紅列誠實)</h2>
<table><thead><tr><th>代碼</th><th>函式</th><th>描述</th><th>連接引擎</th>
<th>態</th></tr></thead><tbody>{fr}</tbody></table>
<h2>② TPN 模板冊(單圖視覺資產;雙軸唯一號;資料連結)</h2>
<table><thead><tr><th>TPN</th><th>類/形</th><th>軸(唯一號=序列)</th>
<th>資料連結</th><th>態</th></tr></thead><tbody>{tr}</tbody></table>
<h2>③ 複合堆疊冊(同時間軸上→下同步)</h2>
<table><thead><tr><th>TPN-C</th><th>成員(上→下)</th><th>時間軸</th>
<th>同步律</th></tr></thead><tbody>{cr}</tbody></table>
</body></html>""", encoding="utf-8")


def selftest() -> int:
    import tempfile
    global REG, OUT
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    reg0, out0 = REG, OUT
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        REG = tdp / "reg.json"
        OUT = tdp / "page.html"
        spec = {"workflow": [
            {"step": i, "id": k, "label": k, "success": "s",
             "truthBoundary": "t"} for i, k in enumerate(
                ("refreshRequest", "addChart", "renderChart",
                 "saveGovernedImage", "selectSpecificSavedImage",
                 "composeSharedTimeStack", "explicitUserExport"), 1)]}
        (tdp / "VIA_VAP_User_Workflow_Spec_v023.json").write_text(
            json.dumps(spec), encoding="utf-8")
        lib = {"compose": {"mode": "single", "form": "line",
                           "L": ["cpi"], "Rr": ["ust10"],
                           "stack": ["ismm", "unrate"]},
               "db": ["FRED"], "connect": {"adapter": "vdf"}}
        (tdp / "VAP_Chart_Library (1).json").write_text(
            json.dumps(lib), encoding="utf-8")
        rc = register(tdp)
        reg = _load_reg()
        chk("① 七函式登記代碼+描述(WF-01..07)", rc == 0
            and len(reg["functions"]) == 7
            and reg["functions"][0]["code"] == "WF-01")
        chk("② 連接點矩陣(批251 斷點清零:七步全 LINKED;"
            "saveGovernedImage→ENG012)",
            sum(1 for f in reg["functions"]
                if f["state"] == "LINKED") == 7
            and any("ENG012" in (f.get("engine_link") or "")
                    for f in reg["functions"]
                    if f["id"] == "saveGovernedImage"))
        t = reg["templates"][0]
        chk("③ TPN 模板(雙軸各帶唯一號 TPN-001.AX1/AX2+資料連結)",
            t["tpn"] == "TPN-001" and t["kind"] == "dual_axis"
            and t["axes"][0]["axis_id"] == "TPN-001.AX1"
            and t["axes"][1]["axis_id"] == "TPN-001.AX2"
            and t["data_link"]["sources"] == ["FRED"])
        chk("④ 複合堆疊自動冊(stack→TPN-C001;同時間軸 top_to_last)",
            reg["composites"] and reg["composites"][0]["time_sync"]
            and reg["composites"][0]["order"] == "top_to_last")
        rc2 = register(tdp)
        reg2 = _load_reg()
        chk("⑤ 去冗冪等(重跑=同 id/同 hash 全 SKIP 零增)", rc2 == 0
            and len(reg2["functions"]) == 7
            and len(reg2["templates"]) == 1)
        lib["compose"]["Rr"] = ["dxy"]        # 資料連結變=新版讓位
        (tdp / "VAP_Chart_Library (1).json").write_text(
            json.dumps(lib), encoding="utf-8")
        register(tdp)
        reg3 = _load_reg()
        chk("⑥ 更新=新版+舊版 superseded(只增不減讓位)",
            len(reg3["templates"]) == 2
            and reg3["templates"][0].get("superseded_by") == "TPN-002")
        rc3 = compose(["TPN-001", "TPN-002"])
        reg4 = _load_reg()
        chk("⑦ compose 引用制(成員 TPN 引用非複本=更新即全同步)",
            rc3 == 0 and reg4["composites"][-1]["members"]
            == ["TPN-001", "TPN-002"])
        chk("⑧ 未知 TPN 誠實拒 rc2", compose(["TPN-999"]) == 2)
        page = OUT.read_text(encoding="utf-8")
        chk("⑨ 三區冊頁(函式/模板/複合;批251 零斷點)",
            all(k in page for k in ("七函式冊", "TPN 模板冊",
                                    "複合堆疊冊"))
            and "GAP" not in page)
        chk("⑩ 空收容誠實 rc2", register(tdp / "none_x") == 2)
    REG, OUT = reg0, out0
    chk("⑪ append-only+hash 宣告", "append-only" in src
        and "hash 定生死" in src)
    chk("⑫ 零網路+加速橋",
        all(("import " + k) not in src for k in ("requests", "httpx"))
        and "ACCEL-BRIDGE" in src)
    print(f"  [計] 十二檢 OK {12 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== TPN 模板編號冊(VAP_ENG011)· 十二檢自測(零網路)===")
        return selftest()
    if args and args[0] == "register":
        return register()
    if args and args[0] == "compose" and len(args) > 1:
        return compose([t.strip() for t in args[1].split(",")])
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
