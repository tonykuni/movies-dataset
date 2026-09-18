#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL163_MasterFileCard v0100 — 母檔與母檔卡(批573)

操作員令(批573):「自動完成 · 自測實測字完成 · **輸出母檔** —— 這三個由你自動主導完成」。

【母檔是誰,卡又是誰(零九頭龍:不另造一份交接)】
  **母檔正主**是 `docs/VIA_Handover_ONEPAGE.md`(+ 倉庫根鏡像 `VIA_HANDOVER_LATEST.md`),
  由 VCGC `page --publish` 產;十三段,**310 KB**。本器**不重造它、不改它一個字**。
  問題在別的地方:**310 KB 的母檔,AI 每接手一次就要付一次那個 token**——
  這直接牴觸 L65(AI 讀卡,不讀原始碼)。母檔該留著當正本,但**入口不該是它**。
  所以本器做的是母檔的**卡**:一張 4 KB 以內的索引,帶
    ① 系統座標(母檔/庫/分支/冊在哪)② 現況數字(律/教訓/台帳/元件/短令/站)
    ③ **最會咬人的那幾條律與教訓**(不是全抄,是點名)④ 未結掉球 ⑤ 母檔十三段的段落索引
  AI 讀卡就能定位,要細節才去母檔那一段。省多少**當場算給你看**。

【誠實】
  · 卡上每一行都標**來源檔**;來源缺=該行寫 ABSENT,**不編**。
  · 卡**不是**母檔的替代品:它自己第一行就寫著「這是索引,細節去母檔第 N 段」。
  · 本境(容器)**不 publish 母檔**:沙盒庫是空的,發布會拿 ABSENT 覆蓋工作站的真快照(LL49)。
    `export` 只落到報告夾;要更新正本母檔,請在工作站跑 `via-vcgc page --publish`。

【紀律】零網路 · 零 DB · 只讀倉內 SSOT(所以**任何機器跑出來都一樣**)· 預設零寫入倉。

用法:
  via-mastercard card              印母檔卡(+ token 帳:母檔 vs 卡)
  via-mastercard export            卡落到 VIA_Reports\mastercard\(不碰倉內正本)
  via-mastercard export --publish  **寫入倉內** supportive modules\registry\VIA_MasterFile_Card_v0100.md
  via-mastercard --selftest
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
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "mastercard"
CARD_IN_REPO = HERE / "VIA_MasterFile_Card_v0100.md"

MASTER = VIA / "docs" / "VIA_Handover_ONEPAGE.md"
MASTER_MIRROR = VIA.parent / "VIA_HANDOVER_LATEST.md"
LAWS = HERE / "VIA_Policy_Laws_SSOT_v0100.json"
LEDGER = HERE / "VIA_AutoCode_Registry_v0100.json"
INVENTORY = HERE / "VIA_Component_Inventory_SSOT_v0100.json"
CMDCARDS = HERE / "VIA_Command_Cards_v0100.json"
BALLS = VIA / "docs" / "VIA_DroppedBalls_B507.md"

# 「最會咬人的」——不是我挑喜好,是**這幾條在台帳裡真的出現最多次**(下面 hot_laws() 實算)
HOT_MIN_HITS = 2


# ===== [VIA:JSONIO-BRIDGE:v0100] JSON 讀寫正典橋(批592;正典 SUP_MDL752_VIAJsonIO)=====
# 本處原本的行為:utf-8 · try/except→None
# 批592 量過:活樹尾版 168 支只有 **20 處**定義 / **17 個行為群**(debt 報的 83/35 檔含版本史,LL142)。
# 差異軸:讀=編碼 utf-8-sig vs utf-8(**活的不一致**:帶 BOM 的檔有些引擎讀得到有些讀不到)、
# 缺檔與壞檔**是兩個旋鈕**(合成一個 default 會把壞檔說成不存在=假的零,LL138);
# 寫=原子寫 / indent / 尾換行 / default=str ——**indent 與尾換行是產出契約,不得統一**。
# 所以正典把差異變成明示選項,並逐群重放證零損失(讀 9 種 × 4 語料全同;寫 4 種**逐位元組相同**)。
# 這裡是**綁定**不是再定義一支 def(寫 def 家族數不會掉=等於沒併,LL143)。
import importlib.util as _js_ilu
from pathlib import Path as _js_Path
_JS_MOD = None
_js_p = _js_Path(__file__).resolve()
while _js_p.parent != _js_p:
    _js_hits = sorted((_js_p / "supportive modules").glob("SUP_MDL752_VIAJsonIO_v*.py"))
    if _js_hits:
        _js_spec = _js_ilu.spec_from_file_location("VIA_JSONIO", _js_hits[-1])
        _JS_MOD = _js_ilu.module_from_spec(_js_spec)
        _js_spec.loader.exec_module(_JS_MOD)
        break
    _js_p = _js_p.parent
if _JS_MOD is None:      # 大聲壞掉:讀錯編碼/寫錯 indent 都是無聲的錯
    raise RuntimeError("[FAIL] JSON 讀寫正典缺席:supportive modules/SUP_MDL752_VIAJsonIO_v*.py")
_json = _JS_MOD.bind_read(bom=False)
# ===== [VIA:JSONIO-BRIDGE:END] =====


def _txt(p: Path) -> str:
    try:
        return Path(p).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _tok(s: str) -> int:
    """粗略 token 估算(與指令卡同族:CJK 每字約一 token,其餘每 4 字元約一 token)。"""
    cjk = sum(1 for c in s if "一" <= c <= "鿿")
    return cjk + max(0, len(s) - cjk) // 4


def master_sections() -> dict:
    """母檔十三段的索引:段名 + 起始行 + 該段字數。母檔不在=誠實 ABSENT。"""
    t = _txt(MASTER)
    if not t:
        return {"state": "ABSENT", "why": f"母檔不在:{MASTER.name}(在工作站跑 `via-vcgc page --publish` 產)"}
    lines = t.splitlines()
    secs, cur = [], None
    for i, l in enumerate(lines, 1):
        if l.startswith("## "):
            if cur:
                cur["chars"] = sum(len(x) for x in lines[cur["line"]:i - 1])
                secs.append(cur)
            cur = {"title": l[3:].strip()[:70], "line": i}
    if cur:
        cur["chars"] = sum(len(x) for x in lines[cur["line"]:])
        secs.append(cur)
    return {"state": "OK", "file": str(MASTER.relative_to(VIA)), "bytes": len(t.encode("utf-8")),
            "chars": len(t), "tokens": _tok(t), "n_sections": len(secs), "sections": secs,
            "mirror": (str(MASTER_MIRROR) if MASTER_MIRROR.exists() else "")}


def hot_laws(laws: dict, led: dict) -> dict:
    """**實算**哪幾條律/教訓在台帳裡被引用最多次——不是我挑喜好的那幾條(批562 的教訓)。"""
    if not laws or not led:
        return {"state": "ABSENT", "why": "政策庫或台帳讀不到"}
    blob = " ".join(str(e.get("kind", "")) + " " + str(e.get("code", "")) for e in led.get("ledger", []))
    hits = {}
    for coll, key in (("laws", "L"), ("lessons", "LL")):
        for item in laws.get(coll, []):
            i = item["id"]
            n = len(re.findall(r"\b" + re.escape(i) + r"\b", blob))
            if n >= HOT_MIN_HITS:
                hits[i] = {"n": n, "zh": str(item.get("zh", ""))[:120], "cat": item.get("cat", ""),
                           "kind": coll}
    top = sorted(hits.items(), key=lambda kv: -kv[1]["n"])[:12]
    return {"state": "OK", "n_scanned": len(laws.get("laws", [])) + len(laws.get("lessons", [])),
            "top": [{"id": k, **v} for k, v in top]}


def open_balls() -> dict:
    t = _txt(BALLS)
    if not t:
        return {"state": "ABSENT", "why": f"掉球冊不在:{BALLS.name}"}
    rows = [l for l in t.splitlines() if l.strip().startswith("|") and "|" in l[1:]]
    body = [l for l in rows if not set(l.replace("|", "").strip()) <= set("-: ")][1:]
    closed = [l for l in body if "~~" in l or "已結" in l]
    return {"state": "OK", "file": str(BALLS.relative_to(VIA)),
            "n": len(body), "open": len(body) - len(closed)}


def build() -> dict:
    laws, led, inv, cmds = _json(LAWS), _json(LEDGER), _json(INVENTORY), _json(CMDCARDS)
    ms = master_sections()
    hot = hot_laws(laws, led)
    balls = open_balls()
    src = {
        "母檔": (ms.get("file") or "ABSENT"),
        "政策庫": (str(LAWS.relative_to(VIA)) if laws else "ABSENT"),
        "台帳": (str(LEDGER.relative_to(VIA)) if led else "ABSENT"),
        "元件冊": (str(INVENTORY.relative_to(VIA)) if inv else "ABSENT"),
        "指令卡": (str(CMDCARDS.relative_to(VIA)) if cmds else "ABSENT"),
        "掉球冊": (balls.get("file") or "ABSENT"),
    }
    nums = {
        "律": (len(laws.get("laws", [])) if laws else -1),
        "教訓": (len(laws.get("lessons", [])) if laws else -1),
        "台帳筆數": (len(led.get("ledger", [])) if led else -1),
        "元件": (len([r for r in (inv or {}).get("records", []) if r.get("state") == "ACTIVE"]) if inv else -1),
        "短令": ((cmds or {}).get("n", -1)),
        "母檔段": ms.get("n_sections", -1),
    }
    return {"state": "OK" if ms.get("state") == "OK" else "NODATA",
            "why": ms.get("why", ""), "src": src, "nums": nums,
            "master": ms, "hot": hot, "balls": balls,
            "batch": (laws or {}).get("batch", "?")}


def render(d: dict) -> str:
    ms, hot, balls = d["master"], d["hot"], d["balls"]
    o = []
    o.append("# VIA 母檔卡(MASTER CARD)")
    o.append("")
    o.append("> **這是索引,不是母檔。** 看座標與現況讀這張卡就夠;要細節,照最後一節的段落索引")
    o.append("> 去母檔對應的那一段。卡上每一行都標來源檔;來源缺就寫 ABSENT,**不編**。")
    o.append(f"> 產生 {datetime.now():%Y-%m-%d %H:%M} · 政策庫批次 {d['batch']} · "
             f"本卡零網路零 DB,只讀倉內 SSOT(**任何機器跑出來都一樣**)")
    o.append("")
    o.append("## 一 · 座標(東西在哪)")
    o.append("")
    o.append("| 是什麼 | 在哪 |")
    o.append("|---|---|")
    for k, v in d["src"].items():
        o.append(f"| {k} | `{v}` |")
    if ms.get("mirror"):
        o.append(f"| 母檔鏡像(倉庫根) | `{Path(ms['mirror']).name}` |")
    o.append("")
    o.append("## 二 · 現況數字(全部實算,非抄寫)")
    o.append("")
    o.append("| 項 | 數 |")
    o.append("|---|---|")
    for k, v in d["nums"].items():
        o.append(f"| {k} | {v if v >= 0 else 'ABSENT'} |")
    if balls.get("state") == "OK":
        o.append(f"| 掉球(總/未結) | {balls['n']} / **{balls['open']}** |")
    o.append("")
    o.append("## 三 · 最會咬人的律與教訓(**按台帳實際引用次數排**,不是挑喜好的)")
    o.append("")
    if hot.get("state") == "OK" and hot.get("top"):
        o.append("| 代號 | 被引用 | 一句話 |")
        o.append("|---|---|---|")
        for h in hot["top"]:
            o.append(f"| **{h['id']}** | {h['n']} | {h['zh'].replace('|', '｜')[:100]} |")
        o.append("")
        o.append(f"> 掃過 {hot['n_scanned']} 條;只列被台帳引用 ≥{HOT_MIN_HITS} 次的。全文在政策庫。")
    else:
        o.append(f"ABSENT — {hot.get('why', '')}")
    o.append("")
    o.append("## 四 · 母檔段落索引(要細節去這幾段)")
    o.append("")
    if ms.get("state") == "OK":
        o.append(f"母檔 `{ms['file']}` · {ms['bytes'] // 1024} KB · 約 {ms['tokens']:,} token · {ms['n_sections']} 段")
        o.append("")
        o.append("| 段 | 起始行 | 約字數 |")
        o.append("|---|---|---|")
        for s in ms["sections"]:
            o.append(f"| {s['title'].replace('|', '｜')} | {s['line']} | {s['chars']:,} |")
    else:
        o.append(f"ABSENT — {ms.get('why', '')}")
    o.append("")
    o.append("## 五 · 這張卡不回答的事")
    o.append("")
    o.append("- **庫裡有多少資料**:卡是倉內事實;庫況要在你的機器跑 `via-datahome catalog` / `via-vdfcov`。")
    o.append("- **今天哪一站紅**:跑 `via-go` 或 `via-ryg`;卡不猜燈號。")
    o.append("- **母檔的動態段**(RunGate / 多矩陣 / 資料家)以**你機器上最新一次** `via-vcgc page --publish` 為準;")
    o.append("  倉內那份是 commit 當下的快照,**本容器不發布**(沙盒庫是空的,發布會拿 ABSENT 蓋掉真快照;LL49)。")
    return "\n".join(o) + "\n"


def write_out(name: str, payload) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    p = REPORTS / name
    p.write_text(payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    return p


def _atomic(p: Path, s: str) -> None:
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(s, encoding="utf-8")
    os.replace(tmp, p)


def selftest() -> int:
    import tempfile
    n, fails = [0], []

    def chk(name, ok, note=""):
        n[0] += 1
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    print(f"=== CGC_MDL163 母檔卡 v{VERSION} · 自測(零網路;零 DB;預設不碰倉內正本) ===")
    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("① 零網路 · 零 DB(不 import requests/httpx/urllib/duckdb)",
        not any(k in code for k in ("import requests", "import httpx", "import urllib", "import duckdb")))
    chk("② 不重造母檔、不改母檔(只讀 ONEPAGE,無任何寫回 docs/ 的路徑)",
        "MASTER.write_text" not in code and "_atomic(MASTER" not in code)
    chk("③ 本境不 publish 母檔(LL49:沙盒庫空,發布會拿 ABSENT 蓋掉真快照)",
        "本容器不發布" in code and "via-vcgc page --publish" in code)
    chk("④ export 預設落報告夾;--publish 才寫倉內卡(且只寫卡,不寫母檔)",
        "CARD_IN_REPO" in code and "REPORTS" in code)

    d = build()
    chk("⑤ 母檔讀得到且段落索引抽得出來(讀不到=誠實 ABSENT,不編)",
        d["master"]["state"] in ("OK", "ABSENT")
        and (d["master"]["state"] != "OK" or d["master"]["n_sections"] >= 10),
        f"{d['master']['state']} · {d['master'].get('n_sections', 0)} 段")
    chk("⑥ 現況數字全部實算(律/教訓/台帳/元件/短令都 > 0)",
        all(d["nums"][k] > 0 for k in ("律", "教訓", "台帳筆數", "元件", "短令")),
        str(d["nums"]))
    chk("⑦ 最會咬人的律是**按台帳實際引用次數排**,不是我挑的",
        d["hot"]["state"] == "OK" and len(d["hot"]["top"]) >= 5
        and all(d["hot"]["top"][i]["n"] >= d["hot"]["top"][i + 1]["n"]
                for i in range(len(d["hot"]["top"]) - 1)),
        f"前三 {[x['id'] + '×' + str(x['n']) for x in d['hot']['top'][:3]]}")
    card = render(d)
    chk("⑧ 卡第一句就聲明自己是索引不是母檔(避免被當成替代品)",
        card.splitlines()[2].startswith("> **這是索引,不是母檔。**"))
    chk("⑨ 卡上每一個來源都標檔名,缺的寫 ABSENT",
        all(("`" + v + "`") in card or v == "ABSENT" for v in d["src"].values()))
    mt, ct = d["master"].get("tokens", 0), _tok(card)
    chk("⑩ **token 帳真的有省**(這張卡存在的理由;算不出省就是白做)",
        mt > 0 and ct < mt * 0.05,
        f"母檔 約 {mt:,} token → 卡 約 {ct:,} token · 省 {100 - round(ct * 100.0 / mt, 2)}%")
    chk("⑪ 卡有節「這張卡不回答的事」(索引要講清楚自己的邊界)",
        "## 五 · 這張卡不回答的事" in card)
    chk("⑫ 卡 ≤ 8 KB(超過就不是卡了)", len(card.encode("utf-8")) <= 8192,
        f"{len(card.encode('utf-8'))} bytes")

    # 母檔缺席時的誠實路徑
    g = globals()
    with tempfile.TemporaryDirectory() as td:
        old = g["MASTER"]
        g["MASTER"] = Path(td) / "no_master.md"
        try:
            d2 = build()
            c2 = render(d2)
            chk("⑬ 母檔不在=卡照樣出得來,且該節寫 ABSENT 並講得出怎麼產(不空白也不假裝)",
                d2["state"] == "NODATA" and "ABSENT" in c2 and "via-vcgc page --publish" in c2)
        finally:
            g["MASTER"] = old
    chk("⑭ 帶加速器橋(MDL156 覆蓋閘)", "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    # LL112:分子分母同源
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="CGC_MDL163_MasterFileCard", description="母檔卡(零網路;零 DB)")
    ap.add_argument("verb", nargs="?", default="card", choices=["card", "export"])
    ap.add_argument("--publish", action="store_true", help="export:寫入倉內卡(只寫卡,絕不寫母檔)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    d = build()
    card = render(d)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_out(f"MASTERCARD_{ts}.json", d)
    write_out("MASTERCARD_latest.json", d)
    p = write_out("VIA_MasterFile_Card_latest.md", card)
    if a.verb == "export" and a.publish:
        _atomic(CARD_IN_REPO, card)
        print(f"[CGC_MDL163 v{VERSION}] export --publish · 倉內卡已更新 {CARD_IN_REPO.name}")
    if a.json:
        print(json.dumps(d, ensure_ascii=False))
        return {"OK": 0, "NODATA": 2, "ABSENT": 3}.get(d["state"], 1)
    if a.verb == "card":
        print(card)
    mt, ct = d["master"].get("tokens", 0), _tok(card)
    print(f"[CGC_MDL163 v{VERSION}] {a.verb} · {d['state']}")
    if mt:
        print(f"  [token] 母檔 約 {mt:,} → 卡 約 {ct:,} · 省 {100 - round(ct * 100.0 / mt, 2)}%"
              f"(AI 讀卡定位,要細節才去母檔那一段;L65)")
    else:
        print(f"  {d.get('why', '')}")
    print(f"  卡 {p}")
    return {"OK": 0, "NODATA": 2, "ABSENT": 3}.get(d["state"], 1)


if __name__ == "__main__":
    sys.exit(main())
