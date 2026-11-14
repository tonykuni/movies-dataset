#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VIA_VCGC_MDL262_SSOTConsistencyEngine v0103 — 薄尾:讀得到「寫在引擎程式裡」與「寫在清單式冊裡」的規則;同一概念的分歧併成一案

操作員 2026-11-14:個股與主動式 ETF 的代碼規則有好幾種寫法(MDL009 · MDL010 / ENG077 · VDF 輸入冊 · 中央冊)→「開」(開案裁定)。
v0100 只讀得到 dict 形狀的冊。這幾條規則有的寫在冊的清單裡(VDF_InputUniverse_SSOT 的 inputs[]),有的寫在引擎程式的常數裡
(SSOT_STOCK_RX = re.compile(r"...")),所以本版加兩種來源讀法,並把同一概念的多個兩兩分歧併成一案(一個概念一次裁定):
  json_list   冊裡的清單:用 id 欄找到那一項,取指定欄(式子 · 正例 · 反例)
  py_const    引擎程式裡的具名常數:只做 ast.parse(零執行 · 不匯入),取字串常數或 re.compile("…") 的第一個引數;
              薄尾家族由新到舊找第一個有這個常數的版本,並記下是哪一支
其餘(證明器 · 血緣 · 案帳 · domains · period)原樣交給前版。對他系統只讀:不執行、不匯入、不改它們的檔(L123)。
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

import ast
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_VCGC_MDL262_SSOTConsistencyEngine"
ENGINE = _STEM
TAG = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_scc_prior_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR
while "PRIOR" in vars(BASE):
    BASE = vars(BASE)["PRIOR"]


def __getattr__(name: str):
    return getattr(PRIOR, name)


def py_const(path: Path, name: str):
    """程式檔裡頂層的具名常數 → 字串(只 ast.parse,不執行、不匯入)。找不到回 None;語法壞丟 ValueError。"""
    try:
        tree = ast.parse(path.read_bytes().decode("utf-8-sig"))
    except (SyntaxError, UnicodeDecodeError) as exc:
        raise ValueError("程式檔剖析不了:%s" % str(exc)[:80])
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if not any(isinstance(t, ast.Name) and t.id == name for t in targets):
            continue
        v = node.value
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            return v.value
        if isinstance(v, ast.Call) and getattr(v.func, "attr", getattr(v.func, "id", "")) == "compile" and v.args \
                and isinstance(v.args[0], ast.Constant) and isinstance(v.args[0].value, str):
            return v.args[0].value
        raise ValueError("常數 %s 不是字串也不是 re.compile(\"…\")" % name)
    return None


def _ad_json_list(d, src) -> list:
    rows = d
    for part in [p for p in str(src.get("list_path") or "").split("/") if p]:
        rows = rows.get(part) if isinstance(rows, dict) else None
    if not isinstance(rows, list):
        raise ValueError("冊上找不到清單 %s" % src.get("list_path"))
    by = {r.get(src.get("id_field") or "id"): r for r in rows if isinstance(r, dict)}
    out = []
    for e in src.get("entries") or []:
        r = by.get(e["id"])
        v = r.get(e["field"]) if isinstance(r, dict) else None
        if not isinstance(v, str):
            raise ValueError("清單項 %s 沒有字串欄 %s" % (e["id"], e["field"]))
        out.append(BASE._asset(kind=e.get("kind") or "REGEX", key=e["key"], value=v, scope=str(e.get("scope") or ""), mode=e.get("mode"),
                               positive=[x for x in (r.get(e.get("pos_field") or "") or []) if isinstance(x, str)],
                               negative=[x for x in (r.get(e.get("neg_field") or "") or []) if isinstance(x, str)]))
    return out


def _load_new(eng, src) -> tuple:
    """→ (assets, status)。一個來源壞掉只影響自己。"""
    st = {"id": src["id"], "system": src["system"], "adapter": src["adapter"], "state": "OK", "files": [], "why": "", "n": 0}
    assets = []
    try:
        if src["adapter"] == "json_list":
            files = [f for f in BASE.tails(eng.via, src["glob"]) if f.is_file()]
            if not files:
                st["state"], st["why"] = "NODATA", "找不到檔(%s)" % src["glob"]
                return assets, st
            for f in files:
                raw = f.read_bytes()
                got = _ad_json_list(json.loads(raw.decode("utf-8-sig")), src)
                for a in got:
                    a["path"] = BASE.rel_posix(f, eng.via)
                assets.extend(got)
                st["files"].append({"path": BASE.rel_posix(f, eng.via), "version": _vnum(f), "sha": hashlib.sha256(raw).hexdigest()})
        elif src["adapter"] == "py_const":
            fam = sorted((f for f in eng.via.glob(src["glob"]) if f.is_file()), key=_vnum, reverse=True)
            if not fam:
                st["state"], st["why"] = "NODATA", "找不到檔(%s)" % src["glob"]
                return assets, st
            seen = {}
            for e in src.get("entries") or []:
                hit = None
                for f in fam:                     # 薄尾家族:由新到舊找第一個定義這個常數的版本
                    v = py_const(f, e["name"])
                    if v is not None:
                        hit = (f, v)
                        break
                if hit is None:
                    raise ValueError("家族裡沒有任何一版定義常數 %s" % e["name"])
                f, v = hit
                a = BASE._asset(kind="REGEX", key=e["key"], value=v, scope=str(e.get("scope") or ""), mode=e.get("mode"))
                a["path"] = BASE.rel_posix(f, eng.via)
                assets.append(a)
                seen[f] = True
            for f in seen:
                st["files"].append({"path": BASE.rel_posix(f, eng.via), "version": _vnum(f), "sha": hashlib.sha256(f.read_bytes()).hexdigest()})
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError) as exc:
        st["state"], st["why"] = "INVALID", str(exc)[:160]
        return [], st
    for a in assets:
        a["src"] = src["id"]
        if a["sys"] == "?":
            a["sys"] = src["system"]
        a["vsha"] = BASE.sha(BASE.canon([a["value"], sorted(a["aliases"])]))[:16]
    st["n"] = len(assets)
    return assets, st


NEW_ADAPTERS = ("json_list", "py_const")
_V0100_LOAD = BASE.Engine.load
_V0100_DETECT = BASE.Engine.detect


def load(self, extra=None):
    path, book = BASE.Engine.sources_book(self)
    mine = [s for s in book.get("sources") or [] if s.get("adapter") in NEW_ADAPTERS]
    if not mine:
        return _V0100_LOAD(self, extra)
    slim = dict(book, sources=[s for s in book.get("sources") or [] if s.get("adapter") not in NEW_ADAPTERS])
    self.sources_book = lambda: (path, slim)         # 只在這一次呼叫裡把新型來源先拿掉,交給本體讀舊型的
    try:
        data = _V0100_LOAD(self, extra)
    finally:
        del self.sources_book
    for src in mine:
        assets, st = _load_new(self, src)
        data["assets"].extend(assets)
        data["status"].append(st)
    return data


def detect(self, data):
    """本體照跑,再把同一概念的多個兩兩分歧併成一案(一個概念一次裁定;案號仍是內容定址)。"""
    det = _V0100_DETECT(self, data)
    groups, keep = {}, {}
    for cid, c in det["cases"].items():
        m = re.match(r"概念 ([^:]+):", c["summary"]) if c["type"] == "RGX_CONCEPT_DIVERGE" else None
        if m:
            groups.setdefault(m.group(1), []).append(c)
        else:
            keep[cid] = c
    for cname, cs in sorted(groups.items()):
        cs.sort(key=lambda c: c["case"])
        parts = []
        for c in cs:
            for p in c["parts"]:
                if p not in parts:
                    parts.append(p)
        ident = {"type": "RGX_CONCEPT_DIVERGE", "concept": cname, "parts": sorted([p["sys"], p["src"], p["key"]] for p in parts)}
        cid = "SCC-" + BASE.sha(ident)[:10].upper()
        lines = [re.sub(r"^概念 [^:]+:", "", c["summary"]) for c in cs]
        keep[cid] = {"case": cid, "type": "RGX_CONCEPT_DIVERGE", "sev": "RED" if any(c["sev"] == "RED" for c in cs) else "YELLOW", "family": "正則",
                     "identity": ident, "parts": parts,
                     "summary": "概念 %s:%d 個來源寫法、%d 處兩兩不等價 ‖ %s" % (cname, len(parts), len(cs), " ‖ ".join(lines)),
                     "evidence_fp": BASE.sha(sorted(c["evidence_fp"] for c in cs))[:16],
                     "suggest": "一個概念一次裁定:選一式當正本(其餘改別名或出新版對齊),或分範疇並存並各自註明用途",
                     "sources_ok": all(c.get("sources_ok", True) for c in cs)}
    det["cases"] = keep
    return det


BASE.Engine.load = load
BASE.Engine.detect = detect


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK " if cond else "NG ", name, (" · " + str(note)[:240]) if note and not cond else ""))

    print("=== %s %s · 薄尾自測(清單式冊 · 程式常數 · 概念併案)===" % (ENGINE, TAG))
    with tempfile.TemporaryDirectory(prefix="via_scc_src_") as td:
        via = Path(td)
        reg = BASE._fixture(via)
        vdf = via / "functional modules" / "VDF"
        marker = via / "EXECUTED.txt"
        (vdf / "VDF_X_v0100.py").write_text('import re\nSTOCK_RX = re.compile(r"^(?!0)(?!202[1-9])(?!2030)([1-9]\\d{3})$")\nPLAIN = "^\\\\d{5}A$"\nNUM = 5\n', encoding="utf-8")
        (vdf / "VDF_X_v0101.py").write_text('open(r"%s", "w").write("x")\nraise SystemExit(9)\n' % str(marker).replace("\\", "/"), encoding="utf-8")
        (vdf / "VDF_In_SSOT_v0100.json").write_text(json.dumps({"inputs": [
            {"id": "IN-01", "code_regex": "^[1-9][0-9]{3}$", "pos": ["2330"], "neg": ["0050"]}, {"id": "IN-02", "code_regex": "^00[0-9]{3}A$"}]}), encoding="utf-8")
        book = json.loads((reg / "VIA_SSOT_ConsistencyEngine_Sources_SSOT_v0100.json").read_text(encoding="utf-8"))
        book["concepts"] = {"tw_stock_ticker": {"parent": "ticker", "members": ["TW_TICKER", "VDF_IN01", "VDF_X.STOCK_RX"]},
                            "tw_active_etf_ticker": {"parent": "ticker", "members": ["VDF_IN02", "VDF_X.PLAIN"]}}
        book["sources"] += [
            {"id": "vdf.in", "system": "VDF", "adapter": "json_list", "glob": "functional modules/VDF/VDF_In_SSOT_v[0-9][0-9][0-9][0-9].json",
             "list_path": "inputs", "id_field": "id", "entries": [
                 {"id": "IN-01", "key": "VDF_IN01", "field": "code_regex", "pos_field": "pos", "neg_field": "neg"},
                 {"id": "IN-02", "key": "VDF_IN02", "field": "code_regex"}]},
            {"id": "vdf.x", "system": "VDF", "adapter": "py_const", "glob": "functional modules/VDF/VDF_X_v[0-9][0-9][0-9][0-9].py",
             "entries": [{"name": "STOCK_RX", "key": "VDF_X.STOCK_RX"}, {"name": "PLAIN", "key": "VDF_X.PLAIN"}]}]
        (reg / "VIA_SSOT_ConsistencyEngine_Sources_SSOT_v0100.json").write_text(json.dumps(book, ensure_ascii=False), encoding="utf-8")
        eng = BASE.Engine(via)
        data = eng.load()
        by = {a["key"]: a for a in data["assets"]}
        chk("① 清單式冊:用 id 找到那一項,式子與正反例都讀到", by.get("VDF_IN01", {}).get("value") == "^[1-9][0-9]{3}$" and by["VDF_IN01"]["positive"] == ["2330"]
            and by["VDF_IN01"]["negative"] == ["0050"] and by["VDF_IN02"]["value"] == "^00[0-9]{3}A$")
        chk("② 程式常數:re.compile(r\"…\") 與純字串都取得到", by.get("VDF_X.STOCK_RX", {}).get("value") == r"^(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})$"
            and by.get("VDF_X.PLAIN", {}).get("value") == r"^\d{5}A$")
        chk("③ 薄尾家族由新到舊找:尾版沒有這個常數,取到前一版並記下是哪一支", by["VDF_X.STOCK_RX"]["path"].endswith("VDF_X_v0100.py"))
        chk("④ 零執行:尾版一匯入就會寫檔並結束,剖析後那個檔沒有出現", not marker.exists())
        st = {s["id"]: s for s in data["status"]}
        chk("⑤ 新來源的狀態與檔案指紋照記(給案帳的來源水位用)", st["vdf.in"]["state"] == "OK" and st["vdf.x"]["state"] == "OK"
            and st["vdf.in"]["files"][0]["path"].startswith("functional modules/VDF/") and len(st["vdf.x"]["files"][0]["sha"]) == 64)
        det = eng.detect(data)
        cc = [c for c in det["cases"].values() if c["type"] == "RGX_CONCEPT_DIVERGE"]
        names = sorted(c["identity"].get("concept") for c in cc)
        chk("⑥ 同一概念的多處分歧併成一案(一個概念一案)", names == ["tw_active_etf_ticker", "tw_stock_ticker"], names)
        stock = next((c for c in cc if c["identity"].get("concept") == "tw_stock_ticker"), {})
        chk("⑦ 併案裡每個來源都在、每處分歧都帶見證字串", {p["key"] for p in stock.get("parts", [])} >= {"TW_TICKER", "VDF_IN01", "VDF_X.STOCK_RX"}
            and stock.get("summary", "").count("‖") >= 2 and '"' in stock.get("summary", ""))
        chk("⑧ 帶起點負向前瞻的式子證得出來(年區 2021–2030 被排除)", "2021" in stock.get("summary", "") or "202" in stock.get("summary", ""), stock.get("summary", "")[:300])
        again = eng.detect(eng.load())
        chk("⑨ 併案的案號重跑不變(冪等)", sorted(again["cases"]) == sorted(det["cases"]))
        book["sources"][-1]["entries"].append({"name": "NOPE", "key": "VDF_X.NOPE"})
        book["sources"].append({"id": "vdf.num", "system": "VDF", "adapter": "py_const", "glob": "functional modules/VDF/VDF_X_v[0-9][0-9][0-9][0-9].py",
                                "entries": [{"name": "NUM", "key": "VDF_X.NUM"}]})
        book["sources"].append({"id": "vdf.gone", "system": "VDF", "adapter": "json_list", "glob": "functional modules/VDF/NoSuch_v[0-9][0-9][0-9][0-9].json",
                                "list_path": "inputs", "entries": []})
        (reg / "VIA_SSOT_ConsistencyEngine_Sources_SSOT_v0100.json").write_text(json.dumps(book, ensure_ascii=False), encoding="utf-8")
        d2 = BASE.Engine(via).load()
        s2 = {s["id"]: s for s in d2["status"]}
        chk("⑩ 常數找不到 / 不是字串 → 該來源 INVALID;檔不在 → NODATA;別的來源照讀",
            s2["vdf.x"]["state"] == "INVALID" and s2["vdf.num"]["state"] == "INVALID" and s2["vdf.gone"]["state"] == "NODATA"
            and s2["vdf.in"]["state"] == "OK" and s2["vcgc.central"]["state"] == "OK", {k: v["state"] for k, v in s2.items()})
        (vdf / "VDF_X_v0102.py").write_text("def broken(:\n", encoding="utf-8")
        d3 = BASE.Engine(via).load()
        chk("⑪ 家族裡有一支語法壞掉 → 該來源 INVALID 並寫明原因,不當成沒事", {s["id"]: s for s in d3["status"]}["vdf.x"]["state"] == "INVALID")
    src = Path(__file__).read_text(encoding="utf-8").split("def selftest")[0]
    chk("⑫ 加速器橋在;自測以外不寫檔、不匯入他系統程式(只 ast.parse)", "VIA:ACCEL-BRIDGE" in src and "ast.parse" in src
        and not re.search(r"\.write_text\(|\.write_bytes\(|os\.replace|exec_module\((?!PRIOR)", src))
    print("[%s %s 薄尾自測] %d/%d %s" % (ENGINE, TAG, sum(ok), len(ok), "PASS" if all(ok) else "FAIL"))
    rc = PRIOR.selftest()
    return rc if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
