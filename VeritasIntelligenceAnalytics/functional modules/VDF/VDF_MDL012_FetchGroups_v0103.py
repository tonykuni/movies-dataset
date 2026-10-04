#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL012_FetchGroups v0103 — 薄尾:三大類 · 預設成員可增減 · 起始日按大類改 · U/I 輸入檔匯入(滑鼠選完 → 一鍵套用)

操作員 2026-10-04:「VDF 分大類輸入:台股及主動式台股 ETF 清單式全部抓取每日量價及籌碼資訊及月營收;台股個股財報及國際股財報是單獨擷取,
  用 2330 3324 NVDA 為 DEFAULT」「分類後的參數其他都有 DEFAULT 可增減;變動的是起始日期,可分大群改,不可單獨改」
  「自動跳出 HTML U/I 不走 SERVER」。
  · 冊 VDF_FetchGroups_SSOT_v0101(尾版):categories = TW_MARKET · FIN · MACRO · OTHER;TW_DAILY 拆 量價 / 籌碼;
    財報兩組 EDITABLE_DEFAULT(預設 2330 3324 / NVDA + 帳本增減),抓取帶 member_args(ENG082 --only · MDL006 --tickers)。
  · start [--category X --set YYYY-MM-DD|default --apply]:起始日只能按大類;--group 一律拒絕(rc 2)。
    跑時代入 {start}(e232 / e066 --start)· {years}(ENG082 --years)· AkShare 有效選單 start_date = MACRO 大類起始日。
  · ui-import <VIA_UI_Input.json> [--apply]:U/I 頁「匯出輸入」下載的檔(滑鼠選的 起始日 / 成員 / as-of)→ 算出帳本差異 → --apply 才寫;
    檔裡想改單一族群起始日 = 拒絕並說明;同一份再匯一次 = 零變更(冪等)。
其餘動詞全照 v0102 / v0101 / v0100。前版自測一律釘在冊 v0100 上跑(前版的斷言寫的是 v0100 的族群)。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / "VDF_MDL012_FetchGroups_v0102.py"
_spec = importlib.util.spec_from_file_location("VDF_MDL012_FetchGroups_v0102_for_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


V0101 = PRIOR.PRIOR
V0100 = V0101.PRIOR

TAG = f"VDF_MDL012_FetchGroups v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
for _m in (PRIOR, V0101, V0100):
    _m.TAG = TAG
_EFF_V0100 = V0100.effective_members
_SEL_V0100 = V0100.effective_selection
_GATHER_V0101 = V0101.gather
UI_INPUT_SCHEMA = "VIA_UI_Input/1"

for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


def _ledger() -> list:
    """讀帳本:路徑每次照 V0100.LEDGER 現值(v0100 的 read_ledger 預設參數是定義當下綁死的)。"""
    return V0100.read_ledger(V0100.LEDGER)


def _append(rec: dict) -> dict:
    return V0100.append_ledger(rec, V0100.LEDGER)


# ---------- 成員:EDITABLE_DEFAULT ----------
def effective_members_v0103(g: dict, ledger: list, sel: dict | None = None, matrix: dict | None = None) -> dict:
    if g.get("membership") != "EDITABLE_DEFAULT":
        return _EFF_V0100(g, ledger, sel, matrix)
    base = [str(x) for x in g.get("default_members", [])]
    sec = ((matrix or {}).get("sections") or {}).get(g.get("matrix_section", ""), {})
    for t in sec.get("tickers", []):
        if str(t) not in base:
            base.append(str(t))
    ops = V0100._ledger_ops(ledger, g["id"])
    return {"members": V0100._apply_ops(base, ops), "exclude": [], "filter": True,
            "origin": f"預設 {' '.join(g.get('default_members', []))}" + (f" + 矩陣 {len(sec.get('tickers', []))}" if sec.get("tickers") else "")
                      + f" + 帳本 {len(ops)} 筆(可增減)"}


V0100.effective_members = effective_members_v0103


# ---------- 起始日:只按大類 ----------
def category_of(book: dict, gid: str) -> dict | None:
    for c in book.get("categories", []):
        if gid in c.get("groups", []):
            return c
    return None


def current_start(book: dict, ledger: list, cat_id: str) -> str:
    c = next((x for x in book.get("categories", []) if x["id"] == cat_id), None)
    val = (c or {}).get("default_start") or "2020-01-01"
    for r in ledger:
        if r.get("kind") == "start" and r.get("category") == cat_id:
            val = (c or {}).get("default_start") if r.get("value") == "default" else r.get("value")
    return val


def starts(book: dict, ledger: list) -> dict:
    return {c["id"]: current_start(book, ledger, c["id"]) for c in book.get("categories", [])}


def _sub(args: list, ctx: dict) -> list:
    out = []
    for a in args:
        s = str(a)
        for k, v in ctx.items():
            s = s.replace("{" + k + "}", str(v))
        out.append(s)
    return out


def plan_rows_v0103(book: dict, fetch_book: dict, gids: list, as_of: str, sel_path: str | None) -> list:
    ledger = _ledger()
    sel, matrix, _, _ = V0100.load_inputs(book)
    st = starts(book, ledger)
    by_id = {r["id"]: r for r in fetch_book.get("engines", [])}
    picked, extra, sel_groups = [], {}, []
    for gid in gids:
        g = V0100.group_of(book, gid)
        cat = category_of(book, g["id"]) or {"id": "OTHER"}
        start = st.get(cat["id"], "2020-01-01")
        years = max(1, date.fromisoformat(as_of).year - date.fromisoformat(start).year + 1)
        mem = effective_members_v0103(g, ledger, sel, matrix).get("members") or []
        ctx = {"as_of": as_of, "start": start, "years": years, "members": ",".join(mem)}
        for eid in g.get("engines", []):
            if eid not in picked:
                picked.append(eid)
        for key in ("asof_args", "member_args", "start_args"):
            for k, v in (g.get(key) or {}).items():
                extra.setdefault(k, [])
                extra[k] += _sub(v, ctx)
        if g["membership"] == "EDITABLE_SELECTION":
            sel_groups.append(g["id"])
    rows = []
    for eid in picked:
        if eid not in by_id:
            rows.append({"id": eid, "missing": True})
            continue
        r = dict(by_id[eid])
        r["needs"] = [n for n in r.get("needs", []) if n in picked]
        args = list(r.get("run_args") or []) + extra.get(eid, [])
        if r.get("selection") is not None or eid == "011d":
            args = [a for a in args if a != "--selection"]
            if sel_path:
                args += ["--selection", sel_path]
            if sel_groups:
                args += ["--group", ",".join(sel_groups)]
        r["run_args"] = args
        r["as_of"] = as_of
        rows.append(r)
    return rows


V0100.plan_rows = plan_rows_v0103


def effective_selection_v0103(book: dict, gids: list, ledger: list, sel: dict) -> dict:
    out = _SEL_V0100(book, gids, ledger, sel)
    if any(c["id"] == "MACRO" for c in book.get("categories", [])):
        out["start_date"] = current_start(book, ledger, "MACRO")
    return out


V0100.effective_selection = effective_selection_v0103


def gather_v0103(home, as_of_arg=None) -> dict:
    snap = _GATHER_V0101(home, as_of_arg)
    book = V0100.load_book()
    ledger = _ledger()
    st = starts(book, ledger)
    gm = {g["id"]: g for g in snap.get("groups", [])}
    snap["categories"] = [{"id": c["id"], "zh": c["zh"], "groups": [x for x in c.get("groups", []) if x in gm], "start": st.get(c["id"]),
                           "default_start": c.get("default_start"), "note": c.get("note", "")} for c in book.get("categories", [])]
    for g in snap.get("groups", []):
        bg = V0100.group_of(book, g["id"])
        g["category"] = (category_of(book, g["id"]) or {}).get("id", "OTHER")
        g["default_members"] = bg.get("default_members", [])
    snap["start_rule"] = book.get("start_rule", "")
    snap["book"] = Path(book["_path"]).name
    return snap


V0101.gather = gather_v0103
_IO_V0101 = V0101.io_matrix


def io_matrix_v0103(book: dict, ledger: list, sel: dict, matrix: dict, as_of: str) -> list:
    """同 v0101,但 {start}/{years}/{members} 也代入,並補 起始日 · 名單參數 兩欄(細節頁要看得到真參數)。"""
    ledger = _ledger()                          # v0101 gather 傳進來的是定義當下綁死路徑讀的;一律照 V0100.LEDGER 現值
    rows = _IO_V0101(book, ledger, sel, matrix, as_of)
    st = starts(book, ledger)
    for r in rows:
        g = V0100.group_of(book, r["group"])
        start = st.get((category_of(book, g["id"]) or {}).get("id", "OTHER"), "")
        mem = effective_members_v0103(g, ledger, sel, matrix).get("members") or []
        years = max(1, date.fromisoformat(as_of).year - date.fromisoformat(start).year + 1) if start else ""
        ctx = {"as_of": as_of, "start": start, "years": years, "members": ",".join(mem)}
        r["asof_args"] = _sub([r.get("asof_args", "")], ctx)[0]
        extra = "; ".join(f"{k} {' '.join(_sub(v, ctx))}" for key in ("member_args", "start_args") for k, v in (g.get(key) or {}).items())
        if extra:
            r["asof_args"] = (r["asof_args"] + "; " if r["asof_args"] and r["asof_args"] != "(視圖截齊)" else "") + extra
        r["start"] = start
    return rows


V0101.io_matrix = io_matrix_v0103


# ---------- U/I 輸入檔匯入 ----------
def plan_ui_import(book: dict, data: dict, ledger: list, sel: dict, matrix: dict) -> dict:
    """回 {ops: [...ledger 記錄], lines: [...說明], errors: [...]}。不寫檔。"""
    ops, lines, errs = [], [], []
    if data.get("schema") != UI_INPUT_SCHEMA:
        errs.append(f"schema 不是 {UI_INPUT_SCHEMA}(收到 {data.get('schema')!r})")
        return {"ops": ops, "lines": lines, "errors": errs}
    cats = {c["id"]: c for c in book.get("categories", [])}
    for gid, v in (data.get("groups") or {}).items():
        if isinstance(v, dict) and "start" in v:
            errs.append(f"起始日只能按大類改,不能單獨改族群 {gid}(請改它所屬大類 {((category_of(book, gid) or {}).get('id'))} 的起始日)")
    for cid, v in (data.get("categories") or {}).items():
        if cid not in cats:
            errs.append(f"無此大類 {cid}")
            continue
        want = (v or {}).get("start")
        if not want:
            continue
        if want != "default":
            try:
                date.fromisoformat(want)
            except ValueError:
                errs.append(f"{cid} 起始日格式錯:{want}")
                continue
        cur = current_start(book, ledger, cid)
        tgt = cats[cid].get("default_start") if want == "default" else want
        if tgt != cur:
            ops.append({"kind": "start", "category": cid, "value": want})
            lines.append(f"[起始日] {cats[cid]['zh']}:{cur} → {tgt}")
    for gid, want in (data.get("members") or {}).items():
        try:
            g = V0100.group_of(book, gid)
        except KeyError as exc:
            errs.append(str(exc))
            continue
        if g["membership"] == "FIXED_ALL":
            errs.append(f"{g['zh']} 固定全部,不收成員")
            continue
        if g["membership"] == "EDITABLE_MATRIX":
            errs.append(f"{g['zh']} 名單在 Input_Interface_Matrix,請用 add / remove(本匯入只改帳本名單)")
            continue
        bad = [x for x in want if not re.fullmatch(r"[A-Za-z0-9_.\-^=:]+", str(x))]
        if bad:
            errs.append(f"{gid} 值不合格:{bad}")
            continue
        cur = effective_members_v0103(g, ledger, sel, matrix).get("members") or []
        want = [str(x) for x in dict.fromkeys(want)]
        for x in want:
            if x not in cur:
                ops.append({"kind": "member", "group": g["id"], "op": "add", "value": x})
                lines.append(f"[成員] {g['zh']} + {x}")
        for x in cur:
            if x not in want:
                ops.append({"kind": "member", "group": g["id"], "op": "remove", "value": x})
                lines.append(f"[成員] {g['zh']} − {x}")
    asof = data.get("as_of")
    if asof:
        cur = V0100.current_asof_setting(book, ledger)
        if asof != cur:
            try:
                V0100.resolve_asof(asof)
                ops.append({"kind": "asof", "value": asof})
                lines.append(f"[as-of] {cur} → {asof}")
            except ValueError:
                errs.append(f"as-of 格式錯:{asof}")
    return {"ops": ops, "lines": lines, "errors": errs}


def cmd_start(argv: list) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog=f"{TAG} start")
    ap.add_argument("--category"); ap.add_argument("--group"); ap.add_argument("--set"); ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    book = V0100.load_book()
    ledger = _ledger()
    if a.group:
        c = category_of(book, a.group)
        print(f"[拒絕] 起始日只能按大類改,不可單獨改 {a.group}(它屬於 {c['id'] if c else '?'}:start --category {c['id'] if c else 'X'} --set …)")
        return 2
    if not a.category:
        for c in book.get("categories", []):
            print(f"  {c['id']:<10} {c['zh']:<28} 起始日 {current_start(book, ledger, c['id'])}(預設 {c['default_start']})· 族群 {','.join(c['groups'])}")
        return 0
    if a.category not in {c["id"] for c in book.get("categories", [])}:
        print(f"[錯] 無此大類 {a.category}")
        return 2
    if not a.set:
        print(f"  {a.category} 起始日 {current_start(book, ledger, a.category)}")
        return 0
    if a.set != "default":
        date.fromisoformat(a.set)
    print(f"[起始日] {a.category}:{current_start(book, ledger, a.category)} → {a.set}")
    if not a.apply:
        print("  (只列計畫;加 --apply 才寫進成員帳本)")
        return 0
    _append({"kind": "start", "category": a.category, "value": a.set})
    print("  [OK] 已寫進帳本")
    return 0


def cmd_ui_import(argv: list) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog=f"{TAG} ui-import")
    ap.add_argument("file"); ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    book = V0100.load_book()
    ledger = _ledger()
    sel, matrix, _, _ = V0100.load_inputs(book)
    data = json.loads(Path(a.file).read_text(encoding="utf-8-sig"))
    p = plan_ui_import(book, data, ledger, sel, matrix)
    for e in p["errors"]:
        print(f"  [拒絕] {e}")
    for ln in p["lines"]:
        print(f"  {ln}")
    if not p["ops"]:
        print("[ui-import] 零變更" + ("(有拒絕項,見上)" if p["errors"] else "(與現況相同)"))
        return 2 if p["errors"] else 0
    if not a.apply:
        print(f"[ui-import] {len(p['ops'])} 筆待寫(只列計畫;加 --apply 才寫帳本)")
        return 2 if p["errors"] else 0
    for op in p["ops"]:
        _append(op)
    print(f"[ui-import] 已寫 {len(p['ops'])} 筆進成員帳本" + (f" · 拒絕 {len(p['errors'])} 項" if p["errors"] else ""))
    return 2 if p["errors"] else 0


# ---------- 自測 ----------
def selftest() -> int:
    import contextlib
    import io
    import shutil
    import tempfile
    res = []

    def chk(name, cond, note=""):
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""))

    keep_glob = V0100.BOOK_GLOB
    V0100.BOOK_GLOB = "VDF_FetchGroups_SSOT_v0100.json"          # 前版斷言寫的是冊 v0100 的族群 → 釘住再跑
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            prior_rc = PRIOR.selftest()
    finally:
        V0100.BOOK_GLOB = keep_glob
        for _m in (PRIOR, V0101, V0100):
            _m.TAG = TAG
    chk("① 前版自測照過(v0102 8 + v0101 8 + v0100 14;釘冊 v0100)", prior_rc == 0, buf.getvalue()[-300:])
    book = V0100.load_book()
    cats = {c["id"]: c for c in book["categories"]}
    gm = {g["id"]: g for g in book["groups"]}
    chk("② 冊 v0101:三大類(台股 · 主動式 ETF / 財報 / 總經)+ 其他 · 量價與籌碼分開打勾 · 財報預設 2330 3324 / NVDA",
        {"TW_MARKET", "FIN", "MACRO"} <= set(cats) and gm["TW_PRICE_VOL"]["membership"] == gm["TW_CHIP"]["membership"] == "FIXED_ALL"
        and gm["TW_FIN"]["default_members"] == ["2330", "3324"] and gm["INTL_FIN"]["default_members"] == ["NVDA"]
        and Path(book["_path"]).name == "VDF_FetchGroups_SSOT_v0101.json", Path(book["_path"]).name)
    sel, matrix, _, _ = V0100.load_inputs(book)
    led = [{"kind": "member", "group": "TW_FIN", "op": "add", "value": "2454"}, {"kind": "member", "group": "TW_FIN", "op": "remove", "value": "3324"}]
    e0 = effective_members_v0103(gm["TW_FIN"], [], sel, {"sections": {}})["members"]
    e1 = effective_members_v0103(gm["TW_FIN"], led, sel, {"sections": {}})["members"]
    chk("③ 預設成員可增減:預設 [2330, 3324] → 帳本 +2454 −3324 → [2330, 2454]", e0 == ["2330", "3324"] and e1 == ["2330", "2454"], (e0, e1))
    led2 = [{"kind": "start", "category": "FIN", "value": "2019-01-01"}]
    chk("④ 起始日按大類:預設照冊 · 帳本改 FIN 只動 FIN · default 還原",
        current_start(book, [], "TW_MARKET") == "2022-07-01" and current_start(book, led2, "FIN") == "2019-01-01"
        and current_start(book, led2, "MACRO") == "1990-01-01"
        and current_start(book, led2 + [{"kind": "start", "category": "FIN", "value": "default"}], "FIN") == cats["FIN"]["default_start"])
    tmp = Path(tempfile.mkdtemp(prefix="mdl012v3_"))
    keep_led = V0100.LEDGER
    try:
        V0100.LEDGER = tmp / "ledger.jsonl"
        for r in led + led2:
            _append(r)
        fb = V0100._json(V0100.tail(V0100.FETCH_GLOB))
        rows = {r["id"]: r for r in plan_rows_v0103(book, fb, ["TW_FIN", "INTL_FIN", "TW_INDEX", "SHIPPING"], "2026-10-02", "/x/sel.json")}
        chk("⑤ 跑時代入:ENG082 --only 2330,2454 --years 8(2019→2026)· MDL006 --tickers NVDA · e232 --start 台股大類起始日 --end as-of",
            rows["e082"]["run_args"][-4:] == ["--only", "2330,2454", "--years", "8"] and rows["006"]["run_args"][-2:] == ["--tickers", "NVDA"]
            and rows["e232"]["run_args"][-4:] == ["--start", "2022-07-01", "--end", "2026-10-02"], {k: v["run_args"] for k, v in rows.items()})
        es = effective_selection_v0103(book, ["SHIPPING"], _ledger(), sel)
        chk("⑥ AkShare 有效選單 start_date = 總經大類起始日", es.get("start_date") == "1990-01-01", es.get("start_date"))
        data = {"schema": UI_INPUT_SCHEMA, "categories": {"FIN": {"start": "2018-01-01"}, "TW_MARKET": {"start": "2022-07-01"}},
                "members": {"TW_FIN": ["2330", "2454", "2317"], "INTL_FIN": ["NVDA", "AAPL"]}, "as_of": "2026-10-02"}
        p = plan_ui_import(book, data, _ledger(), sel, {"sections": {}})
        kinds = sorted((o["kind"], o.get("category") or o.get("group") or "", o.get("value")) for o in p["ops"])
        chk("⑦ U/I 匯入:只算差異(TW_MARKET 起始日沒變不寫)· +2317 · +AAPL · FIN 2018 · as-of",
            kinds == sorted([("start", "FIN", "2018-01-01"), ("member", "TW_FIN", "2317"), ("member", "INTL_FIN", "AAPL"), ("asof", "", "2026-10-02")])
            and not p["errors"], (kinds, p["errors"]))
        for op in p["ops"]:
            _append(op)
        p2 = plan_ui_import(book, data, _ledger(), sel, {"sections": {}})
        bad = plan_ui_import(book, {"schema": UI_INPUT_SCHEMA, "groups": {"TW_FIN": {"start": "2010-01-01"}},
                                    "members": {"TW_PRICE_VOL": ["2330"]}}, _ledger(), sel, {"sections": {}})
        chk("⑧ 冪等(同一份再匯 = 零變更)· 單一族群改起始日 = 拒絕 · 固定全部族群不收成員",
            not p2["ops"] and not p2["errors"] and len(bad["errors"]) == 2 and not bad["ops"], (p2, bad))
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            rc_g = cmd_start(["--group", "TW_FIN", "--set", "2010-01-01", "--apply"])
        chk("⑨ start --group = 拒絕 rc 2、零寫入", rc_g == 2 and "只能按大類" in buf2.getvalue()
            and all(r.get("kind") != "start" or r.get("category") for r in _ledger()))
        home = tmp / "home"
        (home / "output_hub").mkdir(parents=True)
        snap = gather_v0103(home, "2026-10-02")
        cm = {c["id"]: c for c in snap["categories"]}
        io = {r["group"]: r for r in snap.get("io", [])}
        chk("⑪ 細節頁參數邏輯:{start} 已代入(e066 --start 其他大類起始日)· 財報帶 --only / --years 真值",
            "{start}" not in json.dumps(snap.get("io", []), ensure_ascii=False) and "--only 2330,2454,2317" in io["TW_FIN"]["asof_args"]
            and "--years 9" in io["TW_FIN"]["asof_args"] and io["INTL_DAILY"]["start"] == "2020-01-01", io.get("TW_FIN"))
        chk("⑩ U/I 快照帶大類(含當前起始日)· 族群標大類 · 財報預設成員",
            cm["FIN"]["start"] == "2018-01-01" and "TW_FIN" in cm["FIN"]["groups"]
            and next(g for g in snap["groups"] if g["id"] == "TW_FIN")["default_members"] == ["2330", "3324"]
            and next(g for g in snap["groups"] if g["id"] == "TW_CHIP")["category"] == "TW_MARKET", cm.get("FIN"))
    finally:
        V0100.LEDGER = keep_led
        shutil.rmtree(tmp, ignore_errors=True)
    ok = sum(res)
    print(f"[計] {TAG} 本版 {ok}/{len(res)} · v0102 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if ok == len(res) else 'FAIL'}")
    return 0 if ok == len(res) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    if argv and argv[0] == "start":
        return cmd_start(argv[1:])
    if argv and argv[0] == "ui-import":
        return cmd_ui_import(argv[1:])
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
