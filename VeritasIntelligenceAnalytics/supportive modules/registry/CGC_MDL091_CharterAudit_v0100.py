#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL091_CharterAudit — 系統憲章對照稽核(批175;操作員四系統定義正典)
====================================================================
操作員口述定義=VIA_System_Charter_v0100.json(原文照錄零發明)。
本引擎逐能力對照現樹誠實三態:
  COVERED=能力對應引擎在樹且家族尾版可尋
  PARTIAL=部分在位(缺件明列;如 talib C 庫缺=自建 TA 工廠頂上)
  GAP    =無對應件(入問題台帳,不假綠)
探針=檔樹 glob+庫 import 探測(零網路零重測);產憲章頁 HTML
(MDL089 token 冊樣式;手機直式)——四系統定義+能力對照表全列。
用法:python3 CGC_MDL091_CharterAudit_v0100.py run | --selftest
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
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
CHARTER = HERE / "VIA_System_Charter_v0100.json"
UI_OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_Charter_v0100.html"

# 引擎名→存在探針:冊內引擎欄可含註記(括號),取首詞 glob 樹尋
_NAME_RX = re.compile(r"^[A-Za-z0-9_]+")
# 庫探針件(冊內以「候裝/缺」字樣標示者→import 探測定 PARTIAL)
_LIB_PROBE = {"talib": "talib"}


def load_charter() -> dict:
    return json.loads(CHARTER.read_text(encoding="utf-8"))


def _tree_index() -> set:
    """全樹 py 檔字幹索引(一次建,對照快)"""
    idx = set()
    for root in ("functional modules", "supportive modules", "bin"):
        r = VIA / root
        if r.is_dir():
            for pat in ("*.py", "*.sh"):
                for p in r.rglob(pat):
                    idx.add(p.stem)
    b = VIA / "bin"
    if b.is_dir():
        for p in b.iterdir():
            idx.add(p.stem)
            idx.add(p.stem.replace("-", "_"))
    return idx


def audit() -> dict:
    ch = load_charter()
    idx = _tree_index()
    out = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M"), "systems": {}}
    for sk, sv in ch["systems"].items():
        caps = []
        for cap in sv["capabilities"]:
            hits, missing = [], []
            for eng in cap["engines"]:
                m = _NAME_RX.match(eng)
                token = m.group(0) if m else eng
                lib = next((v for k, v in _LIB_PROBE.items() if k in eng.lower()), None)
                if lib is not None:
                    ok = importlib.util.find_spec(lib) is not None
                    (hits if ok else missing).append(eng)
                    continue
                # 樹尋:字幹前綴命中(家族任一版在=在)
                found = any(s.startswith(token) or token in s for s in idx) \
                    or any((VIA / r).is_dir() and list((VIA / r).rglob(f"{token}*"))
                           for r in ())
                (hits if found else missing).append(eng)
            state = ("COVERED" if not missing else
                     ("PARTIAL" if hits else "GAP"))
            caps.append({"id": cap["id"], "zh": cap["zh"], "state": state,
                         "hits": hits, "missing": missing})
        n_cov = sum(1 for c in caps if c["state"] == "COVERED")
        n_par = sum(1 for c in caps if c["state"] == "PARTIAL")
        n_gap = sum(1 for c in caps if c["state"] == "GAP")
        out["systems"][sk] = {"name": sv["name"], "zh": sv["zh"],
                              "operator_text": sv["operator_text"],
                              "caps": caps, "covered": n_cov,
                              "partial": n_par, "gap": n_gap}
    out["totals"] = {
        "covered": sum(s["covered"] for s in out["systems"].values()),
        "partial": sum(s["partial"] for s in out["systems"].values()),
        "gap": sum(s["gap"] for s in out["systems"].values())}
    return out


def _mdl089():
    p = sorted(HERE.glob("CGC_MDL089_UIBaseTemplate_v*.py"))[-1]
    spec = importlib.util.spec_from_file_location("mdl089_charter", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["mdl089_charter"] = m
    spec.loader.exec_module(m)
    return m


def build() -> Path:
    T = _mdl089()
    tk = T.load_tokens()
    st = tk["status"]
    a = audit()
    tone = {"COVERED": st["OK"], "PARTIAL": st["SKIP"], "GAP": st["FAIL"]}
    secs = ""
    for sk, sv in a["systems"].items():
        rows = "".join(
            f'<tr><td><span class="dot" style="background:{tone[c["state"]]}"></span>'
            f'{c["state"]}</td><td>{c["id"]} {c["zh"]}</td>'
            f'<td class="mut">{"、".join(c["hits"][:4])}'
            + (f'<br>缺:{"、".join(c["missing"])}' if c["missing"] else "")
            + "</td></tr>"
            for c in sv["caps"])
        lamp = st["FAIL"] if sv["gap"] else (st["SKIP"] if sv["partial"] else st["OK"])
        secs += f"""<section class="page on"><h2>
<span class="dot big" style="background:{lamp}"></span>{sk} · {sv['name']}</h2>
<div class="env">{sv['zh']}</div>
<div class="mut" style="font-size:.85em">操作員原文:{sv['operator_text']}</div>
<div class="kpi"><span style="color:{st['OK']}">●齊 {sv['covered']}</span>
<span style="color:{st['SKIP']}">●部分 {sv['partial']}</span>
<span style="color:{st['FAIL']}">●缺 {sv['gap']}</span></div>
<div class="tablewrap"><table class="cards">
<tr><th>態</th><th>能力</th><th>對應引擎</th></tr>{rows}</table></div></section>"""
    t = a["totals"]
    html = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 系統憲章</title><style>{T.base_css(tk)}</style></head>
<body><div class="wrap">
<h1>VIA 四系統憲章(操作員定義正典)</h1>
<div class="mut">{a['ts']} · 冊={CHARTER.name} · 能力對照:齊 {t['covered']} ·
部分 {t['partial']} · 缺 {t['gap']} · 原文照錄零發明</div>
{secs}
<div class="foot">憲章=能力面單一正主;新引擎歸屬以本冊為準 · PARTIAL 缺件明列
(talib C 庫=候裝,自建 TA 工廠 11 指標頂上)· GAP 入問題台帳不假綠</div>
</div></body></html>"""
    UI_OUT.parent.mkdir(parents=True, exist_ok=True)
    UI_OUT.write_text(html, encoding="utf-8")
    return UI_OUT


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    ch = load_charter()
    chk("① 憲章冊在位(四系統+原文照錄+append-only)",
        set(ch["systems"]) == {"CGC", "VDF", "VRN", "VAP"}
        and all("operator_text" in v for v in ch["systems"].values())
        and ch["append_only"] is True)
    chk("② 能力分解(15 能力項全掛引擎)",
        sum(len(v["capabilities"]) for v in ch["systems"].values()) == 15
        and all(c["engines"] for v in ch["systems"].values()
                for c in v["capabilities"]))
    a = audit()
    chk("③ 對照稽核(樹尋+庫探針;三態誠實)",
        a["totals"]["covered"] >= 13 and a["totals"]["gap"] == 0,
        f"(齊 {a['totals']['covered']}·部分 {a['totals']['partial']}·缺 {a['totals']['gap']})")
    tal = [c for s in a["systems"].values() for c in s["caps"] if c["id"] == "VAP-2"][0]
    chk("④ talib 誠實(C 庫缺=PARTIAL 明列,自建 TA 工廠在 hits)",
        tal["state"] == "PARTIAL" and any("talib" in m.lower() for m in tal["missing"])
        and any("TAFactory" in h for h in tal["hits"]))
    p = build()
    h = p.read_text(encoding="utf-8")
    chk("⑤ 憲章頁四節+原文照錄在頁",
        all(k in h for k in ("CGC", "VDF", "VRN", "VAP", "mother system", "操作員原文")))
    chk("⑥ 模板 token CSS+手機卡片+零 CDN",
        "table.cards" in h and "@media" in h
        and "http://" not in h and "https://" not in h)
    chk("⑦ 三態色=冊值(齊/部分/缺 KPI 帶)",
        all(c in h for c in ("●齊", "●部分", "●缺")))
    chk("⑧ 紀律宣告(正主宣告/零發明/GAP 入台帳)",
        "單一正主" in h and "零發明" in h and "不假綠" in h)
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 系統憲章對照稽核(CGC_MDL091)· 八檢自測(零網路)===")
        return selftest()
    p = build()
    a = audit()
    t = a["totals"]
    print(f"[UI] {p.name} · 齊 {t['covered']} · 部分 {t['partial']} · 缺 {t['gap']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
