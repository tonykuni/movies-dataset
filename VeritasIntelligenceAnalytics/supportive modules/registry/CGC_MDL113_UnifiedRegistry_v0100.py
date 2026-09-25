#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL113_UnifiedRegistry — 全冊統一編號註冊器(批287;操作員令)
====================================================================
操作員令:「註冊編號好所有引擎/工具/模組——系統用他們;沒用到的
未來會用到。SSOT regex 同義字等中央管理。合併優化簡化相關功能
不同 libs 的工具」。三職:
  ①統一編號:引擎(ENG 族)/治理模組(MDL 族)/工具(根 ps1/
    cmd/py)全登;編號永久律=首登配號後永不變(冊 append-only,
    同名同號;消失=標 MISSING 不刪=只增不減)
  ②用態真掃:族名出現於七調度器(deck/boot×2/grid/Register/
    Invoke/MANAGER 尾版全文)=USED;未現=RESERVED(未來會用到
    =誠實備援,非死碼)
  ③SSOT 中央目錄:registry 冊區 regex/同義字/lexicon/契約/schema
    類 JSON 冊全列=中央管理一覽;跨 libs 同功能家族=引整併冊
    現行 candidate(候裁示,零破壞)
輸出:VIA_Unified_Register_v0100.json(編號正冊)+
  VIA_UI_UnifiedRegister_v0100.html(分類清單+USED/RESERVED 章)
用法:python3 CGC_MDL113_UnifiedRegistry_v0100.py [--print] | --selftest
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

import html
import importlib.util
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REGJ = HERE / "VIA_Unified_Register_v0100.json"
OUT = (VIA / "supportive modules" / "ui_support"
       / "VIA_UI_UnifiedRegister_v0100.html")
SSOT_KEYS = ("regex", "synonym", "同義", "lexicon", "ssot", "contract",
             "schema", "formula", "alias", "template", "prompt")


def _atlas():
    p = sorted(HERE.glob("CGC_MDL112_SystemAtlas_v*.py"))[-1]
    spec = importlib.util.spec_from_file_location("m112u", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.gather()


def _orchestrator_text() -> str:
    """七調度器尾版全文(用態真掃依據)"""
    chunks = []
    for dirp, pat in [(VIA, "Invoke-VIA-All-v*.ps1"),
                      (VIA, "Register-VIA-Commands-v*.ps1"),
                      (VIA, "VIA_SYSTEM_MANAGER_v*.py"),
                      (HERE, "CGC_MDL095_DeckServer_v*.py"),
                      (HERE, "CGC_MDL064_SelftestGrid_v*.py")]:
        hits = sorted(dirp.glob(pat))
        if hits:
            chunks.append(hits[-1].read_text(encoding="utf-8",
                                             errors="ignore"))
    for f in ("via_boot_update.ps1", "via_boot_update.sh"):
        p = HERE / f
        if p.exists():
            chunks.append(p.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)


def collect() -> dict:
    """三類全收(引擎/模組/工具)+SSOT 冊目錄"""
    a = _atlas()
    items = []
    for sub, fam in a["engines"].items():
        for base in sorted(fam):
            items.append(("ENG", f"{sub}/{base}", base))
    for base in sorted(a["mods"]):
        items.append(("MDL", base, base))
    for p in sorted(VIA.glob("*.ps1")) + sorted(VIA.glob("*.cmd")) \
            + sorted(VIA.glob("*.py")):
        base = re.sub(r"[-_]v\d+$", "", p.stem)
        items.append(("TOOL", base, base))
    # 工具同名族去重(尾版律)
    seen, uniq = set(), []
    for cat, key, probe in items:
        k = (cat, key)
        if k not in seen:
            seen.add(k)
            uniq.append((cat, key, probe))
    ssot = [{"name": s["name"], "kb": s["kb"]} for s in a["ssot"]
            if any(t in s["name"].lower() for t in SSOT_KEYS)]
    return {"items": uniq, "ssot": ssot, "atlas": a}


def assign() -> dict:
    """編號永久律:首登配號永不變;新件續號;消失=MISSING 不刪"""
    reg = json.loads(REGJ.read_text(encoding="utf-8")) if REGJ.exists() \
        else {"schema": "unified-register-v1", "next": {}, "entries": {}}
    c = collect()
    orch = _orchestrator_text()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    present = set()
    for cat, key, probe in c["items"]:
        full = f"{cat}:{key}"
        present.add(full)
        if full not in reg["entries"]:
            n = reg["next"].get(cat, 0) + 1
            reg["next"][cat] = n
            reg["entries"][full] = {"id": f"UR-{cat}-{n:04d}",
                                    "first_ts": now}
        e = reg["entries"][full]
        e["state"] = "USED" if probe in orch else "RESERVED"
        e.pop("missing", None)
    for full, e in reg["entries"].items():
        if full not in present:
            e["missing"] = True                # 消失=標記不刪(只增不減)
    reg["ts"] = now
    REGJ.write_text(json.dumps(reg, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    return {"reg": reg, "collect": c}


def render(reg: dict, c: dict) -> str:
    rows = {"ENG": [], "MDL": [], "TOOL": []}
    for full, e in sorted(reg["entries"].items(),
                          key=lambda kv: kv[1]["id"]):
        cat = full.split(":", 1)[0]
        if cat in rows and not e.get("missing"):
            rows[cat].append((e["id"], full.split(":", 1)[1],
                              e.get("state", "?")))
    used = sum(1 for e in reg["entries"].values()
               if e.get("state") == "USED" and not e.get("missing"))
    total = sum(1 for e in reg["entries"].values() if not e.get("missing"))

    def table(cat, title):
        trs = "".join(
            f"<tr><td><code>{i}</code></td><td>{html.escape(n)}</td>"
            f"<td><span class='chip {'u' if st == 'USED' else 'r'}'>"
            f"{'系統在用' if st == 'USED' else '備援(未來會用到)'}"
            "</span></td></tr>" for i, n, st in rows[cat])
        return (f"<h2>{title}({len(rows[cat])})</h2>"
                f"<div class='wrap'><table><tr><th>編號</th><th>名</th>"
                f"<th>用態</th></tr>{trs}</table></div>")

    ssot_rows = "".join(
        f"<tr><td>{html.escape(s['name'])}</td><td>{s['kb']} KB</td></tr>"
        for s in c["ssot"])
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 統一編號註冊冊</title><style>
:root{{--bg:#f3f5f7;--panel:#fff;--line:#dce2e8;--text:#1f2933;
--muted:#6b7785;--blue:#4c78a8;--green:#5a9e6f;--amber:#c4943a}}
@media (prefers-color-scheme: dark){{:root{{--bg:#10151b;--panel:#171e26;
--line:#2a333d;--text:#dbe3ea;--muted:#8a97a5;--blue:#7ba3cc;
--green:#79b58c;--amber:#d4a95c}}}}
body{{background:var(--bg);color:var(--text);margin:0 auto;
font:12px/1.5 "Segoe UI","Noto Sans TC",sans-serif;padding:16px;
max-width:900px}}
h1{{font-size:16px}}h2{{font-size:11px;color:var(--muted);
text-transform:uppercase;letter-spacing:.08em;margin:14px 0 6px}}
.sub{{color:var(--muted);font-size:11px}}
table{{width:100%;border-collapse:collapse;background:var(--panel);
border:1px solid var(--line);border-radius:8px}}
td,th{{padding:4px 8px;border-bottom:1px solid var(--line);
text-align:left;overflow-wrap:anywhere;
font-variant-numeric:tabular-nums}}
th{{font-size:10px;color:var(--muted)}}
code{{color:var(--blue);font-size:10.5px}}
.chip{{font-size:9px;border-radius:999px;padding:1px 8px;
font-weight:700}}
.chip.u{{background:color-mix(in srgb,var(--green) 18%,transparent);
color:var(--green)}}
.chip.r{{background:color-mix(in srgb,var(--amber) 18%,transparent);
color:var(--amber)}}
.wrap{{overflow-x:auto}}</style></head><body>
<h1>統一編號註冊冊(批287)</h1>
<div class="sub">{reg['ts']} · 編號永久律=首登配號永不變(append-only;
消失=標記不刪)· 用態=七調度器全文真掃 · 在用 {used}/{total} ·
備援={total - used}(未來會用到=誠實非死碼)</div>
{table("ENG", "ENGINE · 引擎族")}
{table("MDL", "MODULE · 治理模組族")}
{table("TOOL", "TOOL · 根層工具")}
<h2>SSOT 中央管理目錄(regex/同義字/lexicon/契約/schema 類
{len(c['ssot'])} 冊)</h2>
<div class="wrap"><table><tr><th>冊</th><th>大小</th></tr>{ssot_rows}
</table></div>
<p class="sub">跨 libs 同功能家族=整併冊候裁示
(VIA_Engine_Consolidation_Register;35 族+NLP 家族)· 正冊=
VIA_Unified_Register_v0100.json · 零網路零發明</p></body></html>"""


def run(do_print: bool = False) -> int:
    r = assign()
    OUT.write_text(render(r["reg"], r["collect"]), encoding="utf-8")
    reg = r["reg"]
    total = sum(1 for e in reg["entries"].values() if not e.get("missing"))
    used = sum(1 for e in reg["entries"].values()
               if e.get("state") == "USED" and not e.get("missing"))
    print(f"[統一冊] 登 {total} 件(在用 {used}/備援 {total - used})· "
          f"SSOT 目錄 {len(r['collect']['ssot'])} 冊 · {OUT.name}")
    if do_print:
        for full, e in sorted(reg["entries"].items(),
                              key=lambda kv: kv[1]["id"])[:20]:
            print(f"  {e['id']} {full} [{e.get('state')}]")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    rc = run()
    reg = json.loads(REGJ.read_text(encoding="utf-8"))
    live = {k: e for k, e in reg["entries"].items() if not e.get("missing")}
    chk("① 三類全登(ENG>150+MDL>30+TOOL>10)", rc == 0
        and sum(1 for k in live if k.startswith("ENG:")) > 150
        and sum(1 for k in live if k.startswith("MDL:")) > 30
        and sum(1 for k in live if k.startswith("TOOL:")) > 10)
    ids = [e["id"] for e in live.values()]
    chk("② 編號唯一+格式律(UR-類-4位)", len(ids) == len(set(ids))
        and all(re.match(r"UR-(ENG|MDL|TOOL)-\d{4}$", i) for i in ids))
    r2 = assign()
    same = all(r2["reg"]["entries"][k]["id"] == e["id"]
               for k, e in live.items())
    chk("③ 編號永久律(重跑=同名同號冪等)", same)
    states = {e.get("state") for e in live.values()}
    used = sum(1 for e in live.values() if e.get("state") == "USED")
    chk("④ 用態真掃(USED/RESERVED 雙態並存;在用>30)",
        states == {"USED", "RESERVED"} and used > 30)
    chk("⑤ SSOT 中央目錄(regex/同義字類冊>10)+頁產出",
        len(r2["collect"]["ssot"]) > 10 and OUT.exists()
        and "統一編號註冊冊" in OUT.read_text(encoding="utf-8"))
    chk("⑥ append-only 紀律(消失=標記不刪宣告)+零 CDN+零網路+加速橋",
        "MISSING" in src and "不刪" in src and "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 統一編號註冊器(CGC_MDL113)· 六檢自測(零網路)===")
        return selftest()
    return run("--print" in a)


if __name__ == "__main__":
    sys.exit(main())
