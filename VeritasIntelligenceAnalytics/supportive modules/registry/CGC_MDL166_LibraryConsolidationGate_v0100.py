#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL166:四庫整合遺漏閘(批585;操作員令「參數庫/邏輯庫/政策庫/因子庫 整合有無遺漏」)。

操作員另令「**用 PEIS 整合工具**去查同功能有無遺漏」——所以本閘不自己重刻掃描器,
直接讀 PEIS 能力庫 `VIA_Capability_Store.sqlite`(9134 能力 / 47999 函式)。

兩層判定,順序不能顛倒:
  ① **名實相符**:掛在這個庫名下的冊,內容真的是這個庫該裝的東西嗎?
     —— 這一層先過不了,第二層的數字全部沒意義。
     實測抓到:**邏輯庫掛的是 pip 安裝台帳**(`yake 0.7.3 requires click…`),不是業務計算邏輯。
  ② **整合遺漏**:PEIS 裡同語意的能力,有幾個**沒進冊**、而且**被多處重複實作**
     (members > 1 = 同一件事在 N 個地方各寫一份 = 真正的整合債)。

誠實紀律:
  · **只提候選,不寫冊**(LL90 裁定權在操作員);沒有寫入旗標
  · 語意命中用 regex,一定有噪音 → **具名噪音豁免**逐條附理由(L68)
  · 「已在冊」用字面比對,冊若用中文描述而非函式名就會低估 → **這一點寫在報告裡**,不假裝精準
  · PEIS 庫不在 = NODATA(先跑 `via-peis scan`),不是紅

用法:python3 CGC_MDL166_LibraryConsolidationGate_v0100.py [audit|plan] [--json] [--selftest]
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
import sqlite3
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "libconsol"
_PEIS_DIR = VIA / "VIA_Reports" / "peis"


def _peis_store() -> Path | None:
    """批585:PEIS 能力庫**綁掃描範圍**(MDL161 v0103),所以檔名帶範圍簽章。
    取**最新**的那一個;找不到範圍庫才回退舊的單一庫名。"""
    hits = sorted(_PEIS_DIR.glob("VIA_Capability_Store__*.sqlite"),
                  key=lambda x: x.stat().st_mtime) if _PEIS_DIR.exists() else []
    if hits:
        return hits[-1]
    legacy = _PEIS_DIR / "VIA_Capability_Store.sqlite"
    return legacy if legacy.is_file() else None


PEIS_STORE = _peis_store() or (_PEIS_DIR / "VIA_Capability_Store.sqlite")

#: 四庫 → (冊、語意 regex、**名實相符的證據鍵**、該庫裝什麼)
#: 「名實證據鍵」= 這本冊若真是該庫,頂層必須有的鍵。沒有 = 掛錯冊。
BOOKS = {
    "參數庫": {
        "path": "supportive modules/registry/VIA_Central_Params_SSOT_v*.json",
        "rx": r"param|參數|threshold|門檻|budget|預算|limit|上限|timeout|逾時",
        "identity_keys": ["books", "locked_alignment"],
        "should_hold": "全域與模組的參數**值**正本(防硬編碼與設定飄移)",
    },
    "邏輯庫": {
        "path": "supportive modules/registry/VIA_Lib_Registry_v*.json",
        "rx": r"calc|compute|formula|公式|ratio|比率|derive|推導|normali|aggregate|彙總|margin|毛利",
        "identity_keys": ["logics", "formulas", "rules", "library"],
        "should_hold": "可重用的業務計算邏輯與公式(各模組標準化調用)",
    },
    "政策庫": {
        "path": "supportive modules/registry/VIA_Policy_Laws_SSOT_v*.json",
        "rx": r"policy|policies|法遵|complian|guard|forbid|whitelist|白名單|gate_state",
        "identity_keys": ["laws", "lessons"],
        "should_hold": "自動化驗證規則 · 合規條件 · 安全紅線",
    },
    "因子庫": {
        "path": "supportive modules/registry/VIA_Feature_Catalog_v*.json",
        "rx": r"factor|因子|feature|特徵|momentum|動能|signal|訊號|indicator|指標",
        "identity_keys": ["features", "input_contract"],
        "should_hold": "量化 · 籌碼 · 財務特徵工程的計算因子",
    },
}

#: 具名噪音豁免(L68:要縮分母只能具名,而且附理由)
#: 這些名字太泛,regex 一定誤中;列出來讓人可以質疑、可以改。
NOISE = {
    "any": "Python 內建同名;不是因子也不是邏輯",
    "all": "Python 內建同名",
    "rich": "終端輸出套件名",
    "tp": "太短且多義(target price / true positive / temp)",
    "guard": "泛用守衛函式名",
    "verdict": "判定結果欄位名,不是邏輯本身",
    "ratio": "裸名太泛(要看它算什麼比率)",
    "factors": "容器名(裝因子的欄位),不是單一因子",
    "policy": "容器名(裝政策的欄位)",
    "gates": "容器名(裝閘的欄位)",
    "compliance": "容器名",
    "main": "進入點",
    "run": "進入點",
}


def _tail(pattern: str) -> Path | None:
    d = VIA / str(Path(pattern).parent)
    hits = sorted(d.glob(Path(pattern).name)) if d.exists() else []
    return hits[-1] if hits else None


def _store() -> sqlite3.Connection | None:
    p = _peis_store()
    return sqlite3.connect(f"file:{p}?mode=ro", uri=True) if p else None


def _leaf(cap: str) -> str:
    return cap.rsplit(".", 1)[-1].rsplit("::", 1)[-1]


def audit() -> dict:
    con = _store()
    if con is None:
        return {"state": "NODATA",
                "why": f"PEIS 能力庫不在({PEIS_STORE.name})——先跑 `via-peis scan --family cgc sup vdf vrn`"}
    caps = [(r[0], r[1]) for r in con.execute(
        "select capability, members from vue_capability")]
    con.close()
    rows = []
    for zh, spec in BOOKS.items():
        p = _tail(spec["path"])
        r = {"lib": zh, "should_hold": spec["should_hold"],
             "book": str(p.relative_to(VIA)).replace("\\", "/") if p else "",
             "identity": "", "state": "", "n_book": 0,
             "n_hit": 0, "n_in_book": 0, "n_gap": 0, "top_debt": []}
        if p is None:
            r.update(state="ABSENT", identity="冊不在")
            rows.append(r)
            continue
        try:
            b = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            r.update(state="NODATA", identity=f"冊讀不出:{type(exc).__name__}")
            rows.append(r)
            continue
        # ── ① 名實相符 ─────────────────────────────────────────────────────
        top = set(b.keys()) if isinstance(b, dict) else set()
        have = [k for k in spec["identity_keys"] if k in top]
        r["n_book"] = max([len(v) for v in b.values() if isinstance(v, (list, dict))] or [0]) \
            if isinstance(b, dict) else len(b)
        if not have:
            r.update(state="MISFILED",
                     identity=f"**名實不符**:頂層鍵 {sorted(top)[:6]} 找不到任何一個 "
                              f"{spec['identity_keys']} → 掛在「{zh}」名下的不是{zh}")
        else:
            r["identity"] = f"名實相符(證據鍵 {have})"
        # ── ② 整合遺漏 ─────────────────────────────────────────────────────
        txt = json.dumps(b, ensure_ascii=False).lower()
        rx = re.compile(spec["rx"], re.I)
        hit = [(c, m) for c, m in caps if rx.search(c) and _leaf(c).lower() not in NOISE]
        inb = [(c, m) for c, m in hit if _leaf(c).lower() in txt]
        gap = [(c, m) for c, m in hit if (c, m) not in inb]
        debt = sorted([x for x in gap if x[1] > 1], key=lambda x: -x[1])[:8]
        r.update(n_hit=len(hit), n_in_book=len(inb), n_gap=len(gap),
                 top_debt=[{"cap": _leaf(c), "members": m} for c, m in debt])
        if r["state"] != "MISFILED":
            r["state"] = "GREEN" if not debt else "GAP"
        rows.append(r)
    t = {}
    for x in rows:
        t[x["state"]] = t.get(x["state"], 0) + 1
    return {"state": "OK", "n": len(rows), "tally": t, "rows": rows,
            "noise_exempt": NOISE,
            "caveat": ("「已在冊」用的是**字面比對**(能力名的尾段有沒有出現在冊的 JSON 文字裡)。"
                       "冊若用中文描述而不是函式名,這個數字會**低估**——本閘不假裝它精準。"
                       "真正該看的是 top_debt:**同一件事在 N 個地方各寫一份**,那是跑不掉的整合債。"),
            "note": "**只提候選,不寫冊**(LL90);沒有寫入旗標。"}


def plan() -> dict:
    a = audit()
    if a["state"] != "OK":
        return a
    todo = [r for r in a["rows"] if r["state"] in ("MISFILED", "GAP", "ABSENT", "NODATA")]
    for r in todo:
        r["fix"] = {
            "MISFILED": f"**先正名再談整合**:把真的「{r['lib']}」該裝的東西立一本冊(或指認既有檔),"
                        f"並把現在掛錯的那本移回它自己的庫;在那之前,整合數字沒有意義",
            "GAP": "同一件事在多處各寫一份 → 擇一為正本、其餘改呼叫它(L61 先收斂真相再動刀:"
                   "第一步零改線,只把落差攤開讓操作員裁定)",
            "ABSENT": "冊不在:先立冊(或指認既有檔當正本)",
            "NODATA": "冊讀不出:先修格式",
        }[r["state"]]
    return {"state": "OK" if not todo else "FAIL", "n_total": a["n"], "n_todo": len(todo),
            "tally": a["tally"], "todo": todo, "caveat": a["caveat"], "note": a["note"]}


def write_out(name: str, payload) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    p = REPORTS / name
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def selftest() -> int:
    fails, n = [], [0]

    def chk(name, cond, note=""):
        n[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 四庫逐條有:冊路徑 · 語意尺 · **名實證據鍵** · 該庫裝什麼",
        len(BOOKS) == 4 and all(
            {"path", "rx", "identity_keys", "should_hold"} <= set(v) and v["identity_keys"]
            for v in BOOKS.values()), f"({list(BOOKS)})")
    chk("② 具名噪音豁免逐條附理由(L68:要縮分母只能具名)",
        len(NOISE) >= 10 and all(v for v in NOISE.values()), f"({len(NOISE)} 條)")
    a = audit()
    chk("③ PEIS 能力庫缺席=誠實 NODATA 並指路(不是紅、也不假裝算得出來)",
        a["state"] in ("OK", "NODATA") and (a["state"] == "OK" or "via-peis scan" in a["why"]),
        f"({a['state']})")
    if a["state"] == "OK":
        chk("④ **名實相符先判**:掛錯冊要判 MISFILED,而不是去報它的整合數字",
            all(r["identity"] for r in a["rows"])
            and all(r["state"] != "GREEN" for r in a["rows"] if "名實不符" in r["identity"]),
            "(" + " · ".join(f"{r['lib']}={r['state']}" for r in a["rows"]) + ")")
        chk("⑤ 整合債看的是**多處重複實作**(members>1),不是「冊上沒有」就算債",
            all(all(d["members"] > 1 for d in r["top_debt"]) for r in a["rows"]))
        chk("⑥ 報告要自己講出尺的極限(字面比對會低估),不假裝精準",
            "低估" in a["caveat"] and "字面比對" in a["caveat"])
    chk("⑦ **只提候選,不寫冊**(LL90):無寫入旗標、不改任何 SSOT",
        ("add_argument(" + chr(34) + "--app" + "ly" + chr(34)) not in src
        and "SSOT" in src)
    chk("⑧ 零網路", not re.search(r"^\s*(?:import|from)\s+(urllib|requests|httpx|aiohttp)", src, re.M))
    chk("⑨ 讀 PEIS 是**唯讀開庫**(mode=ro),絕不寫它的能力庫", "mode=ro" in src)
    p = plan()
    chk("⑩ plan 每一列講得出下一步,且 MISFILED 的下一步是『先正名再談整合』",
        all("fix" in r for r in p.get("todo", []))
        and all("先正名" in r["fix"] for r in p.get("todo", []) if r["state"] == "MISFILED"),
        f"(待辦 {p.get('n_todo', 0)})")
    chk("⑪ 帶加速器橋(MDL156 覆蓋閘)", "[VIA:ACCEL-BRIDGE" in src)
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="CGC_MDL166_LibraryConsolidationGate",
                                 description="四庫整合遺漏閘(讀 PEIS 能力庫;零網路;不寫冊)")
    ap.add_argument("verb", nargs="?", default="audit", choices=["audit", "plan"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    r = audit() if a.verb == "audit" else plan()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_out(f"LIBCONSOL_{a.verb.upper()}_{ts}.json", r)
    write_out(f"LIBCONSOL_{a.verb.upper()}_latest.json", r)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
        return 0
    if r["state"] == "NODATA":
        print(f"[CGC_MDL166 v{VERSION}] NODATA · {r['why']}")
        return 2
    print(f"[CGC_MDL166 v{VERSION}] {a.verb} · 四庫 · " +
          " · ".join(f"{k} {v}" for k, v in sorted(r["tally"].items())))
    print("  " + r["caveat"])
    print("  " + r["note"] + "\n")
    for x in (r["rows"] if a.verb == "audit" else r["todo"]):
        print(f"  [{x['state']:<8}] {x['lib']}  ← 該裝:{x['should_hold']}")
        print(f"             冊 {x['book'].split('/')[-1]}({x['n_book']} 筆)· {x['identity']}")
        if x.get("n_hit"):
            print(f"             PEIS 同語意能力 {x['n_hit']} · 已在冊 {x['n_in_book']} · **候選遺漏 {x['n_gap']}**")
        for d in x.get("top_debt", []):
            print(f"               · {d['cap']:<34} 被 {d['members']} 處各寫一份")
        if "fix" in x:
            print(f"             → {x['fix']}")
        print()
    return 0 if r.get("state") == "OK" and not r.get("n_todo") else 2


if __name__ == "__main__":
    raise SystemExit(main())
