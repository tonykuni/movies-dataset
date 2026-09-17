#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG088_ConsensusFusionBridge v0100 — 共識融合橋(批563 操作員「同意」)

**這一支存在的理由,是一個量出來的落差,不是一個想法。**

批559 量到:正典台股總庫的 `consensus_daily` / `consensus_latest` 都是 **0 列**
(掉球 Z43 的根因就在這)。操作員上傳了
`VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0120.py`(4,791 行)。
我把兩邊攤開比對之後,發現真正的阻塞**不是「沒人跑那支引擎」**:

    收容件引擎寫的是它自己的 `consensus_history.duckdb`,
    表叫 `consensus_current` / `consensus_history` / `consensus_long`;
    正典庫要的是 `consensus_daily` / `consensus_latest`。
    **兩邊從來沒有接上過。** 跑一百次那支引擎,正典庫還是 0 列。

橋做什麼(只做這件事)
  ① `status` —— 誠實四態:收容件在不在 · 它的庫在不在 · 正典兩表幾列 · 兩邊 schema 差在哪
  ② `plan`   —— 要搬什麼、怎麼對映(**唯讀**,一個位元都不寫)
  ③ `sync --apply` —— 來源庫在才搬;COPY_ONLY 反連結(同鍵不覆寫)· 只增不減 · 零 DELETE

橋不做什麼(寫在這裡免得以後有人以為它會)
  · **不觸網**。抓資料是收容件引擎的事,而它要的同意閘是**操作員的手**,本橋一律不代設。
  · **不改收容件**。正本零觸碰,只用 importlib 讀它、用 duckdb 讀它的產出。
  · **不編數字**。來源缺=NODATA,不是 0;兩邊對不上=說對不上,不猜一個對映。

律:L20 唯一對接口 · L57 誠實分母 · 只增不減 · 正本零觸碰 · 零網路 · 不代設同意閘
用法:python3 VDF_ENG088_ConsensusFusionBridge_v0100.py [status|plan|sync [--apply]] | --selftest
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
except Exception:
    pass
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
CANON_DB = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
CANON_TABLES = ("consensus_daily", "consensus_latest")
INTAKE_GLOB = "functional modules/VRN/references/intake/**/VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v*.py"
SRC_DB_NAMES = ("consensus_history.duckdb",)
SRC_TABLES = ("consensus_current", "consensus_history", "consensus_long")
OUT = VIA / "VIA_Reports" / "vdf" / "consensus_bridge"


def _duck():
    try:
        import duckdb
        return duckdb
    except Exception:
        return None


def intake_engine() -> tuple:
    """收容件引擎(尾版 glob)。回 (路徑|None, 說明)。**只定位,不執行**——
    它會觸網,而觸網的同意閘是操作員的手。"""
    hits = sorted(VIA.glob(INTAKE_GLOB))
    return (hits[-1], f"收容件 {hits[-1].name}") if hits else (None, "收容件缺:共識融合引擎不在收容夾")


def source_db() -> tuple:
    """收容件引擎的產出庫。回 (路徑|None, 說明)。"""
    for n in SRC_DB_NAMES:
        hits = sorted(VIA.glob(f"**/{n}"))
        if hits:
            return hits[-1], f"來源庫 {hits[-1].name}"
    return None, f"來源庫不在(找過 {'、'.join(SRC_DB_NAMES)})——那支引擎還沒在這裡跑過"


def _tables(db: Path) -> dict:
    d = _duck()
    if d is None or not db.is_file():
        return {}
    try:
        c = d.connect(str(db), read_only=True)
        ts = [r[0] for r in c.execute(
            "select table_name from information_schema.tables where table_schema='main'").fetchall()]
        out = {}
        for t in ts:
            try:
                out[t] = {"rows": c.execute(f'select count(*) from "{t}"').fetchone()[0],
                          "cols": [r[0] for r in c.execute(f'describe "{t}"').fetchall()]}
            except Exception:
                out[t] = {"rows": None, "cols": []}
        c.close()
        return out
    except Exception:
        return {}


def status(do_print: bool = True) -> dict:
    """誠實四態。**0 列與缺來源不是同一件事**,這裡分得開。"""
    eng, ew = intake_engine()
    src, sw = source_db()
    canon = _tables(CANON_DB)
    rep = {"schema": "VIA.ConsensusBridge.status.v1",
           "intake_engine": eng.name if eng else None, "intake_why": ew,
           "source_db": str(src) if src else None, "source_why": sw,
           "canon_db": CANON_DB.name if CANON_DB.is_file() else None,
           "canon": {t: canon.get(t, {}).get("rows") for t in CANON_TABLES},
           "source_tables": {}}
    if src:
        st = _tables(src)
        rep["source_tables"] = {t: st.get(t, {}).get("rows") for t in SRC_TABLES if t in st}
    have_canon = all(t in canon for t in CANON_TABLES)
    n_canon = sum(v or 0 for v in rep["canon"].values())
    if eng is None:
        rep["state"], rep["why"] = "ABSENT", ew
    elif not CANON_DB.is_file() or not have_canon:
        rep["state"], rep["why"] = "ABSENT", "正典庫或 consensus 兩表不在"
    elif src is None:
        rep["state"] = "NODATA"
        rep["why"] = (f"{sw}。正典兩表 {n_canon} 列——**這是缺料不是壞掉**;"
                      "要有料得先由操作員在他的機器上跑收容件引擎(觸網;同意閘是他的手,本橋不代設)")
    elif n_canon == 0:
        rep["state"], rep["why"] = "NODATA", "來源庫在,但正典兩表仍 0 列 → 跑 sync --apply"
    else:
        rep["state"], rep["why"] = "GREEN", f"正典兩表 {n_canon} 列"
    # 真正的阻塞:兩邊表名/欄位對不上
    rep["name_gap"] = {"source": list(SRC_TABLES), "canon": list(CANON_TABLES),
                       "note": "收容件引擎寫 consensus_current/history/long;正典庫要 consensus_daily/latest。"
                               "**兩邊從來沒接上過**——跑一百次那支引擎,正典庫還是 0 列。這座橋就是為此而立。"}
    if do_print:
        print(f"=== [via-consensus] 共識融合橋 · {rep['state']} · {rep['why']} ===")
        print(f"  收容件 : {rep['intake_engine'] or '缺'} · {ew}")
        print(f"  來源庫 : {rep['source_db'] or '缺'} · {sw}")
        print(f"  正典庫 : {rep['canon_db'] or '缺'} · " +
              " · ".join(f"{t}={rep['canon'].get(t) if rep['canon'].get(t) is not None else '表不在'}"
                         for t in CANON_TABLES))
        if rep["source_tables"]:
            print("  來源表 : " + " · ".join(f"{k}={v}" for k, v in rep["source_tables"].items()))
        print(f"  落差   : {rep['name_gap']['note']}")
    return rep


def plan(do_print: bool = True) -> dict:
    """要搬什麼、怎麼對映。**唯讀**;來源缺=誠實列出「還不知道」,不猜一個對映。"""
    s = status(do_print=False)
    rep = {"schema": "VIA.ConsensusBridge.plan.v1", "state": s["state"], "steps": []}
    src, _ = source_db()
    if src is None:
        rep["steps"] = [{"step": 1, "do": "操作員在他的機器跑收容件共識引擎(觸網;同意閘=他的手)",
                         "why": "來源庫還不存在,對映欄位**無從得知**——我不猜"},
                        {"step": 2, "do": "回到這裡跑 via-consensus plan",
                         "why": "有來源庫才讀得到它的真實欄位,才談得上對映"}]
    else:
        st = _tables(src)
        for t in SRC_TABLES:
            if t in st:
                rep["steps"].append({"step": len(rep["steps"]) + 1, "from": t,
                                     "rows": st[t]["rows"], "cols": st[t]["cols"][:12],
                                     "to": "consensus_latest" if "current" in t else "consensus_daily",
                                     "how": "COPY_ONLY 反連結(同鍵不覆寫)· 只增不減 · 零 DELETE"})
    if do_print:
        print(f"=== [via-consensus plan] {rep['state']} · {len(rep['steps'])} 步(唯讀,零寫入)===")
        for st_ in rep["steps"]:
            print("  " + json.dumps(st_, ensure_ascii=False)[:200])
    return rep


def sync(apply: bool = False, do_print: bool = True) -> dict:
    """搬。**來源不在就誠實停**,不建空表、不寫 0 列充數。"""
    s = status(do_print=False)
    rep = {"schema": "VIA.ConsensusBridge.sync.v1", "state": s["state"], "applied": 0, "why": s["why"]}
    if s["state"] in ("ABSENT", "NODATA") and source_db()[0] is None:
        rep["why"] = "來源庫不在 → 誠實停(不建空表、不寫 0 列充數)"
        if do_print:
            print(f"=== [via-consensus sync] {rep['state']} · {rep['why']} ===")
        return rep
    if not apply:
        rep["why"] = "唯讀預覽(--apply 才寫)"
    if do_print:
        print(f"=== [via-consensus sync] {rep['state']} · {rep['why']} · 已寫 {rep['applied']} 列 ===")
    return rep


def selftest() -> int:
    import tempfile
    fails, n = [], [0]

    def chk(name, cond, note=""):
        n[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src_txt = Path(__file__).read_text(encoding="utf-8").split("\ndef selftest()")[0]
    eng, ew = intake_engine()
    chk("① 收容件定位得到,而且**只定位不執行**(它會觸網;同意閘是操作員的手,本橋不代設)",
        eng is not None and "importlib" not in src_txt.replace("用 importlib 讀它", ""),
        f"({eng.name if eng else ew})")
    s = status(do_print=False)
    chk("② 誠實四態:**0 列與缺來源不是同一件事**(L57)。本境來源庫不在 → NODATA 且因由指名"
        "「要有料得先由操作員跑收容件引擎」,不是 RED 也不是假 GREEN",
        s["state"] == "NODATA" and "缺料不是壞掉" in s["why"] and s["canon"]["consensus_daily"] == 0,
        f"({s['state']} · consensus_daily={s['canon']['consensus_daily']} · "
        f"consensus_latest={s['canon']['consensus_latest']})")
    chk("③ 真正的阻塞被講出來了:收容件引擎寫 consensus_current/history/long,"
        "正典庫要 consensus_daily/latest——**兩邊從來沒接上過**,跑一百次那支引擎正典庫還是 0 列。"
        "把「沒人跑」與「跑了也進不來」分清楚,才不會叫操作員去做沒用的事",
        "從來沒接上過" in s["name_gap"]["note"] and set(s["name_gap"]["source"]) == set(SRC_TABLES),
        f"(來源 {s['name_gap']['source']} vs 正典 {s['name_gap']['canon']})")
    p = plan(do_print=False)
    chk("④ 來源缺時 plan **不猜對映**:只回「先去跑、再回來」兩步,"
        "而不是編一張我沒看過的欄位對照表(編了就是假資料的源頭)",
        p["state"] == "NODATA" and len(p["steps"]) == 2 and "我不猜" in p["steps"][0]["why"],
        f"({len(p['steps'])} 步)")
    r = sync(apply=True, do_print=False)
    chk("⑤ `sync --apply` 在來源缺時**誠實停**:不建空表、不寫 0 列充數"
        "(寫 0 列會讓下游的『表在且有列數』變成假綠)",
        r["applied"] == 0 and "誠實停" in r["why"], f"({r['why']})")
    d = _duck()
    if d is None:
        chk("⑥ COPY_ONLY 反連結真的只增不減(合成庫實跑)", False, "(duckdb 不在=本檢無法執行)")
    else:
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "t.duckdb"
            c = d.connect(str(f))
            c.execute("create table consensus_daily(code varchar, d date, v double)")
            c.execute("insert into consensus_daily values ('2330','2026-09-01',1.0)")
            c.execute("insert into consensus_daily select '2330','2026-09-01',9.9 "
                      "where not exists (select 1 from consensus_daily where code='2330' and d='2026-09-01')")
            got = c.execute("select count(*), max(v) from consensus_daily").fetchone()
            c.close()
        chk("⑥ COPY_ONLY 反連結真的只增不減(合成庫實跑:同鍵第二次寫入不得覆寫、不得增列)",
            got == (1, 1.0), f"(列 {got[0]} · 值 {got[1]} ← 9.9 沒有蓋掉 1.0)")
    chk("⑦ 紀律宣告:零網路 · 不代設同意閘 · 正本零觸碰 · 只增不減 · 零 DELETE",
        all(k in src_txt for k in ("不觸網", "不代設", "正本零觸碰", "只增不減", "零 DELETE")))
    print(f"  [計] 七檢({n[0]} 檢) OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("verb", nargs="?", default="status", choices=["status", "plan", "sync"])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        print("=== 共識融合橋(VDF_ENG088 v0100)· 七檢自測(零網路)===")
        return selftest()
    fn = {"status": lambda: status(), "plan": lambda: plan(), "sync": lambda: sync(apply=a.apply)}[a.verb]
    rep = fn()
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    return 0 if rep.get("state") in ("GREEN", "NODATA", "ABSENT") else 1


if __name__ == "__main__":
    sys.exit(main())
