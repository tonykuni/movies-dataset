#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL160_UIUnifyGate v0100 — U/I 畫面統一閘(批570)

操作員令(批570 續):「VIA 作為資料庫與應用介面 HTML U/I 對接;也準備 VIA VRN 的 U/I,
**設計還在進行但畫面統一**」。

【先量再定契約(不發明沒人達得到的標準)】
  本境 65 張 `VIA_UI_*.html` 實測:
    <title> 65/65 · charset 64/65 · viewport 64/65 · lang=zh 64/65 · 零彈窗 62/65
    CSS 變數 :root 61/65 · **零 CDN 56/65** · VIA 頁腳 41/65 · 深色模式 7/65
  所以契約**分三級**,不是一視同仁(一視同仁就是假陽性機器):
    **律級 (LAW)**      已經是既有律(零 CDN / 零彈窗 / charset / viewport / lang)——違反=RED
    **統一級 (UNIFY)**  操作員這一令要的「畫面統一」(主題令牌 :root / VIA 頁腳 / <title>)——缺=YELLOW
    **建議級 (ADVISORY)** 只有 7/65 達標的(深色模式)——**永遠不判紅**,只列出來當路線圖

【不代改頁】
  這些頁都是**引擎產的**。手改頁下一次再生就被蓋掉,而且會讓頁與產它的引擎對不上。
  所以本閘只做兩件:判定 + **指名該由哪一支引擎再生**。沒有 --apply,不寫任何一張頁。

用法:
  via-uiunify scan              逐頁三級判定
  via-uiunify plan              只列不合的,並指名 owner 引擎與該補什麼
  via-uiunify contract          印出契約本身(三級逐條)
  via-uiunify --selftest
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
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "uiunify"
UI_DIRS = ["supportive modules/ui_support", "VIA_Reports"]
OWNER_SCAN = ["supportive modules/registry", "functional modules/VDF/engine",
              "functional modules/VRN", "functional modules/VAP/engine"]

_CDN = re.compile(r'(?:src|href)\s*=\s*["\']https?://', re.I)
_POP = re.compile(r'\b(?:alert|confirm|prompt)\s*\(')

# (鍵, 級別, 中文, 判定)
CONTRACT = [
    ("zero_cdn",  "LAW",      "零 CDN(頁不得外連 http(s) 的 src/href)",   lambda t: not _CDN.search(t)),
    ("zero_popup", "LAW",     "零彈窗(不得 alert/confirm/prompt)",        lambda t: not _POP.search(t)),
    ("charset",   "LAW",      "宣告 UTF-8",                                lambda t: "charset=utf-8" in t.lower().replace('"', "").replace("'", "")),
    ("viewport",  "LAW",      "行動裝置 viewport",                          lambda t: 'name="viewport"' in t.lower() or "name='viewport'" in t.lower()),
    ("lang",      "LAW",      "lang=\"zh…\"",                              lambda t: 'lang="zh' in t.lower() or "lang='zh" in t.lower()),
    ("title",     "UNIFY",    "有 <title>(分頁看得出是哪一張)",            lambda t: "<title>" in t.lower()),
    ("theme_root", "UNIFY",   "CSS 變數 :root 主題令牌(畫面統一的根)",      lambda t: ":root{" in t.replace(" ", "") or ":root {" in t),
    ("via_mark",  "UNIFY",    "頁腳帶 VIA 標記(看得出是同一個系統)",        lambda t: "VIA" in t[-4000:]),
    ("dark",      "ADVISORY", "深色模式(prefers-color-scheme)——路線圖,不判紅", lambda t: "prefers-color-scheme" in t),
]
LEVEL_FAIL = {"LAW": "RED", "UNIFY": "YELLOW", "ADVISORY": "ADVISORY"}


def pages() -> list:
    out = []
    for rel in UI_DIRS:
        d = VIA / rel
        if not d.exists():
            continue
        for p in sorted(d.rglob("VIA_UI_*.html")):
            s = str(p).replace("\\", "/")
            if any(k in s for k in ("references/intake", "VIA_RetiredEngines", "SCOPE_COPY")):
                continue
            out.append(p)
    return out


def owners() -> dict:
    """頁名 → 產它的引擎(誰要再生就找誰)。找不到=誠實留空,不猜。"""
    idx = {}
    for rel in OWNER_SCAN:
        d = VIA / rel
        if not d.exists():
            continue
        for p in d.rglob("*.py"):
            s = str(p).replace("\\", "/")
            if any(k in s for k in ("references/intake", "VIA_RetiredEngines", "__pycache__")):
                continue
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in re.finditer(r'VIA_UI_[A-Za-z0-9_]+\.html', t):
                idx.setdefault(m.group(0), set()).add(p.stem.rsplit("_v", 1)[0])
    return {k: sorted(v) for k, v in idx.items()}


def scan() -> dict:
    ps = pages()
    if not ps:
        return {"state": "ABSENT", "why": f"找不到 VIA_UI_*.html(掃了 {UI_DIRS})"}
    own = owners()
    rows, tally = [], {"GREEN": 0, "RED": 0, "YELLOW": 0, "ADVISORY": 0}
    for p in ps:
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            rows.append({"page": p.name, "state": "RED", "why": f"{type(exc).__name__}: {exc}"})
            tally["RED"] += 1
            continue
        bad = []
        for key, lvl, zh, test in CONTRACT:
            if not test(t):
                bad.append({"item": key, "level": lvl, "zh": zh})
        red = [b for b in bad if b["level"] == "LAW"]
        yel = [b for b in bad if b["level"] == "UNIFY"]
        st = "RED" if red else ("YELLOW" if yel else "GREEN")
        tally[st] += 1
        if any(b["level"] == "ADVISORY" for b in bad):
            tally["ADVISORY"] += 1
        rows.append({"page": p.name, "rel": str(p.relative_to(VIA)), "state": st,
                     "miss": bad, "owner": own.get(p.name, [])})
    return {"state": "OK", "n": len(rows), "tally": tally, "rows": rows,
            "contract_levels": {k: sum(1 for c in CONTRACT if c[1] == k)
                                for k in ("LAW", "UNIFY", "ADVISORY")},
            "note": "ADVISORY 永遠不判紅(本境只有 7/65 達標,判紅就是假陽性機器)"}


def plan() -> dict:
    sc = scan()
    if sc["state"] != "OK":
        return sc
    todo = [r for r in sc["rows"] if r["state"] in ("RED", "YELLOW")]
    for r in todo:
        r["fix"] = ("該由 " + " / ".join(r["owner"]) + " 再生"
                    if r["owner"] else "找不到 owner 引擎(誠實留空,不猜)——請操作員指認")
    return {"state": "OK" if not any(r["state"] == "RED" for r in todo) else "FAIL",
            "n_total": sc["n"], "n_todo": len(todo),
            "n_red": sum(1 for r in todo if r["state"] == "RED"),
            "n_yellow": sum(1 for r in todo if r["state"] == "YELLOW"),
            "todo": todo,
            "note": "本閘不改頁:頁是引擎產的,手改下一次再生就被蓋掉,而且會讓頁與引擎對不上"}


def write_out(name: str, payload) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    p = REPORTS / name
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def selftest() -> int:
    import tempfile
    n, fails = [0], []

    def chk(name, ok, note=""):
        n[0] += 1
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    print(f"=== CGC_MDL160 U/I 畫面統一閘 v{VERSION} · 自測(零網路;不改任何一張頁) ===")
    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("① 零網路、零寫頁(不 import requests/httpx/urllib;無 write_text 寫 .html)",
        not any(k in code for k in ("import requests", "import httpx", "import urllib"))
        and ".html\").write_text" not in code and "p.write_text(h" not in code)
    chk("② 沒有 --apply(頁是引擎產的,不代改)", '"--apply"' not in code and "'--apply'" not in code)
    chk("③ 契約分三級,且 ADVISORY 永不判紅(本境只有 7/65 達標;一視同仁就是假陽性機器)",
        {c[1] for c in CONTRACT} == {"LAW", "UNIFY", "ADVISORY"}
        and LEVEL_FAIL["ADVISORY"] == "ADVISORY")

    # 合成三張頁:全合 / 破律 / 只缺統一級
    with tempfile.TemporaryDirectory() as td:
        g = globals()
        d = Path(td) / "supportive modules" / "ui_support"
        d.mkdir(parents=True)
        good = ('<!doctype html><html lang="zh-Hant"><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width"><title>好頁</title>'
                '<style>:root{--fg:#111}@media (prefers-color-scheme:dark){:root{--fg:#eee}}</style>'
                '<body>內容</body><footer>VIA</footer></html>')
        (d / "VIA_UI_Good_v0100.html").write_text(good, encoding="utf-8")
        (d / "VIA_UI_Cdn_v0100.html").write_text(
            good.replace("<body>", '<script src="https://cdn.example.com/x.js"></script><body>'), encoding="utf-8")
        (d / "VIA_UI_Plain_v0100.html").write_text(
            '<!doctype html><html lang="zh-Hant"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width"><body>只有內容</body></html>', encoding="utf-8")
        old_via, old_dirs, old_own = g["VIA"], g["UI_DIRS"], g["OWNER_SCAN"]
        g["VIA"], g["UI_DIRS"], g["OWNER_SCAN"] = Path(td), ["supportive modules/ui_support"], []
        try:
            sc = scan()
            by = {r["page"]: r for r in sc["rows"]}
            chk("④ 全合的頁=GREEN", by["VIA_UI_Good_v0100.html"]["state"] == "GREEN")
            chk("⑤ 外連 CDN=**RED**(律級;零 CDN 是既有律)",
                by["VIA_UI_Cdn_v0100.html"]["state"] == "RED"
                and any(m["item"] == "zero_cdn" for m in by["VIA_UI_Cdn_v0100.html"]["miss"]))
            chk("⑥ 只缺主題令牌/頁腳/標題=**YELLOW**,不冒充 RED(畫面統一是新令,不是舊律)",
                by["VIA_UI_Plain_v0100.html"]["state"] == "YELLOW"
                and not any(m["level"] == "LAW" for m in by["VIA_UI_Plain_v0100.html"]["miss"]),
                str([m["item"] for m in by["VIA_UI_Plain_v0100.html"]["miss"]]))
            chk("⑦ 缺深色模式不影響燈號(ADVISORY 只列不判)",
                any(m["item"] == "dark" for m in by["VIA_UI_Plain_v0100.html"]["miss"])
                and by["VIA_UI_Plain_v0100.html"]["state"] != "RED")
            pl = plan()
            chk("⑧ plan 只列不合的,並對每一張講得出下一步",
                pl["n_total"] == 3 and pl["n_todo"] == 2 and all("fix" in r for r in pl["todo"]))
            chk("⑨ 找不到 owner 引擎=誠實留空並請操作員指認(不猜)",
                all("不猜" in r["fix"] for r in pl["todo"]))
        finally:
            g["VIA"], g["UI_DIRS"], g["OWNER_SCAN"] = old_via, old_dirs, old_own

    real = scan()
    chk("⑩ 掃得到本庫的真實頁(≥40 張)", real["state"] == "OK" and real["n"] >= 40,
        f"{real.get('n')} 張 · GREEN {real['tally']['GREEN']} · YELLOW {real['tally']['YELLOW']} · RED {real['tally']['RED']}")
    chk("⑪ owner 對照查得到(頁要再生時找得到人)",
        sum(1 for r in real["rows"] if r["owner"]) >= 20,
        f"查得到 owner {sum(1 for r in real['rows'] if r['owner'])} 張")
    chk("⑫ 帶加速器橋(MDL156 覆蓋閘)", "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="CGC_MDL160_UIUnifyGate", description="U/I 畫面統一閘(零網路;不改頁)")
    ap.add_argument("verb", nargs="?", default="scan", choices=["scan", "plan", "contract"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.verb == "contract":
        print(f"[CGC_MDL160 v{VERSION}] 畫面統一契約(三級)")
        for key, lvl, zh, _t in CONTRACT:
            print(f"  [{lvl:<8}] {key:<12} {zh}")
        print("  註:LAW 違反=RED · UNIFY 缺=YELLOW · ADVISORY 永遠不判紅(只當路線圖)")
        return 0
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    r = scan() if a.verb == "scan" else plan()
    write_out(f"UIUNIFY_{a.verb.upper()}_{ts}.json", r)
    write_out(f"UIUNIFY_{a.verb.upper()}_latest.json", r)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    elif a.verb == "scan":
        t = r["tally"]
        print(f"[CGC_MDL160 v{VERSION}] scan · {r['state']} · {r['n']} 張頁")
        print(f"  GREEN {t['GREEN']} · YELLOW {t['YELLOW']} · **RED {t['RED']}** "
              f"(另有 {t['ADVISORY']} 張缺 ADVISORY 項目,不判紅)")
    else:
        print(f"[CGC_MDL160 v{VERSION}] plan · {r['state']} · 共 {r['n_total']} 張 · "
              f"待修 {r['n_todo']}(RED {r['n_red']} · YELLOW {r['n_yellow']})")
        for x in r["todo"][:40]:
            miss = " · ".join(f"{m['item']}({m['level']})" for m in x["miss"] if m["level"] != "ADVISORY")
            print(f"  [{x['state']:<6}] {x['page']:<44} 缺 {miss}")
            print(f"           → {x['fix']}")
        print(f"  註:{r['note']}")
    return {"OK": 0, "NODATA": 2, "ABSENT": 3}.get(r.get("state"), 1)


if __name__ == "__main__":
    sys.exit(main())
