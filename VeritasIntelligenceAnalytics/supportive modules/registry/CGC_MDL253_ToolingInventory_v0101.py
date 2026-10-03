#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL253_ToolingInventory v0101 — 薄尾:單引擎啟動前備料卡(輸入參數 · SSOT 冊 · regex · 同義字 · 工作流步)

操作員(2026-10-03):「準備單引擎啟動 vdf 及相關輸入參數 ssot regex 同義字於 vrd system manager」→ 兩個管理員都做。
本支是兩個 SYSTEM MANAGER 共用的檢視本體(VDF_SystemManager / VRN_SystemManager 的 engine 動詞都進 engine_main),
所以只在這裡加一次,兩邊同時有;v0100 一字不動(list · check · card 照舊)。新增兩個子令(都只讀、只 ast.parse,不執行被讀的檔):
  engine params <引擎> [--json]   一支引擎的啟動前備料卡:
      ① 輸入參數:argparse add_argument(旗標 · 預設 · 型別 · 選項 · 必填 · 說明)+ add_parser 子令 + sys.argv 字面旗標
      ② 環境變數:os.environ.get / os.getenv / os.environ[…] / "X" in os.environ 讀到的名字;同意閘(VIA_NET_CONSENT · VIA_SCRAPE_CONSENT)另標
         —— AI 永不代設,只告訴你要不要在自己的視窗開
      ③ SSOT 冊:原始碼裡寫到的 .json / .jsonl 冊名(含 _v* 萬用)→ 解到樹上的尾版(冊不在 = 照實標 ABSENT)
      ④ regex:本地字面 regex(re.compile / search / match / fullmatch / findall / sub / split)條數與樣本;
         中央正則冊 VIA_Central_Synonym_Regex 尾版裡 owner 是本支的鍵;本地式子與中央某鍵完全同式 = 可委中央(黃,只列不改)
      ⑤ 同義字:委樞印記(SUP_MDL749 樞紐 · 中央同義字冊 · CGC_MDL176 聯集冊)有沒有;本地同義字表(dict 字面 ≥ 5 鍵、
         值是字串或字串串列)= 未委樞(黃,只列不改);中央 synonyms_meta 來源提到本支的鍵數
      ⑥ 工作流步:VIA_Workflow_<子系統>_SSOT 尾版裡 engine 樣式對到本檔的步;VDF 另對 VDF_InputUniverse_SSOT 尾版
         (E-xx 站 · 動詞 · 項目 · 寫入表 · 觸網 · 角色 · 被哪些 IN-xx 輸入用到)
      ⑦ 啟動:沿用 v0100 啟動前閘(紅擋 / 黃提醒)+ 短令範本(必填旗標帶 <值>)+ 先自測那一句
  engine prep [--json] [--no-page]  整個子系統每支引擎一列(同 list 的家族去重),寫 VIA_Reports/tooling/ENGINE_PARAMS_<子系統>_latest.json / .html
燈:紅 = 啟動前閘擋;黃 = 閘黃,或有本地同義字表 / 與中央同式的本地 regex / 冊不在;綠 = 都齊。程式庫(沒有 __main__)= NA。
只讀:不改任何被讀的檔;輸出只寫 VIA_Reports/tooling/(不進 git)。零網路;不用 TA-Lib;不代設同意閘。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
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

import ast
import fnmatch
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL253_ToolingInventory"
_VRX_V0101 = re.compile(r"[-_]v(\d{4})$")


def _vnum_v0101(p) -> int:
    m = _VRX_V0101.search(Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0101(p) < _vnum_v0101(__file__)), key=_vnum_v0101)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0100:盤點矩陣 · engine list / check / card
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
VIA = PRIOR.VIA
ENGINE = Path(__file__).stem
CONSENT_V0101 = ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")
RX_CALLS_V0101 = {"compile", "search", "match", "fullmatch", "findall", "finditer", "sub", "subn", "split"}
BOOK_RX_V0101 = re.compile(r"^(?:.*/)?(?P<stem>[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+?)(?P<ver>_v(?:\d{4}|\*|\[0-9\]\{4\}|(?:\[0-9\]){4}))?\.(?P<ext>jsonl?)$")
HUB_MARKS_V0101 = {"SUP_MDL749_VRNFieldRuleHub": "VRN 欄位規則樞紐", "VIA_Central_Synonym_Regex": "中央同義字 / 正則冊",
                   "CGC_MDL176_SynonymUnion": "同義字聯集器", "VIA_SSOT_SynonymUnion": "同義字聯集冊"}
BOOK_ROOTS_V0101 = ("supportive modules", "functional modules")
BOOK_KIND_V0101 = re.compile(r"(SSOT|Registry|Register|Lock|Ledger|Book|Schema|Rule|Map|Contract|Spec|Canon|Dict|Universe|Synonym|Regex|Laws|Workflow|Inventory|Header|Roster|Card)", re.I)
_BOOK_INDEX_V0101: dict = {}


def __getattr__(name):
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- ①② 輸入參數 · 環境變數
def _lit_v0101(node):
    try:
        return ast.literal_eval(node)
    except Exception:                                    # 非字面(變數 / 呼叫)就照原文列
        try:
            return "‹" + ast.unparse(node) + "›"
        except Exception:
            return "‹?›"


def cli_params_v0101(tree) -> dict:
    """argparse 參數逐條(旗標 · 預設 · 型別 · 選項 · 必填 · 說明)+ 子令。"""
    args, subs = [], []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        names = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
        if node.func.attr == "add_argument" and names:
            kw = {k.arg: k.value for k in node.keywords if k.arg}
            positional = not names[0].startswith("-")
            row = {"names": names, "positional": positional,
                   "required": bool(_lit_v0101(kw["required"])) if "required" in kw else positional and _lit_v0101(kw.get("nargs", ast.Constant(None))) not in ("?", "*")}
            for k in ("default", "choices", "nargs", "action"):
                if k in kw:
                    row[k] = _lit_v0101(kw[k])
            if "type" in kw:
                row["type"] = ast.unparse(kw["type"])
            if "help" in kw and isinstance(kw["help"], ast.Constant):
                row["help"] = str(kw["help"].value)[:120]
            args.append(row)
        elif node.func.attr == "add_parser" and names:
            subs.append(names[0])
    return {"args": args, "subparsers": sorted(set(subs))}


def env_vars_v0101(tree) -> list:
    """讀到的環境變數名(只認字面鍵)。"""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            txt = ast.unparse(f) if isinstance(f, (ast.Attribute, ast.Name)) else ""
            if txt in ("os.environ.get", "os.getenv", "environ.get", "getenv", "os.environ.pop", "os.environ.setdefault") and node.args \
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                names.add(node.args[0].value)
        elif isinstance(node, ast.Subscript) and ast.unparse(node.value) in ("os.environ", "environ") \
                and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            names.add(node.slice.value)
        elif isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], (ast.In, ast.NotIn)) \
                and isinstance(node.left, ast.Constant) and isinstance(node.left.value, str) \
                and ast.unparse(node.comparators[0]) in ("os.environ", "environ"):
            names.add(node.left.value)
    return sorted(n for n in names if re.fullmatch(r"[A-Z][A-Z0-9_]{2,60}", n))


# ---------------------------------------------------------------- ③ SSOT 冊
def book_index_v0101(via: Path | None = None) -> dict:
    """{冊名幹: [(版號, VIA 相對路徑)…]}:supportive / functional modules 底下的 .json / .jsonl(一個行程只掃一次)。"""
    via = Path(via or VIA)
    key = str(via)
    if key in _BOOK_INDEX_V0101:
        return _BOOK_INDEX_V0101[key]
    idx = {}
    for root in BOOK_ROOTS_V0101:
        base = via / root
        if not base.is_dir():
            continue
        for p in base.rglob("*.json*"):
            if p.suffix not in (".json", ".jsonl"):
                continue
            r = p.relative_to(via).as_posix()
            if PRIOR.SKIP_RX.search(r) or "/references/" in r or "/output_hub/" in r:
                continue
            m = re.match(r"^(?P<stem>.+?)(?:_v(?P<v>\d{4}))?$", p.stem)
            idx.setdefault(m.group("stem"), []).append((int(m.group("v")) if m.group("v") else -1, r))
    _BOOK_INDEX_V0101[key] = idx
    return idx


def books_v0101(tree, idx: dict) -> dict:
    """原始碼字面裡的冊名 → 尾版;f-string 冊名另計(動態,不猜)。"""
    seen, dyn = {}, 0
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            txt = "".join(v.value for v in node.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
            if re.search(r"\.jsonl?\b", txt) and re.search(r"(SSOT|Registry|Register|Lock|Ledger|Book|Schema|Rule)", txt):
                dyn += 1
            continue
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)) or len(node.value) > 200:
            continue
        m = BOOK_RX_V0101.match(node.value.replace("\\", "/"))
        if not m:
            continue
        stem = m.group("stem")
        if stem in seen or not BOOK_KIND_V0101.search(stem):      # 報告輸出(*_latest.json 等)不是冊
            continue
        hits = sorted(idx.get(stem, []))
        tail = hits[-1] if hits else None
        seen[stem] = {"book": stem, "asked": node.value[-80:], "pinned": bool(m.group("ver") and m.group("ver")[2:].isdigit()),
                      "tail": tail[1] if tail else "", "tail_version": (f"v{tail[0]:04d}" if tail and tail[0] >= 0 else ("—" if tail else "")),
                      "state": "OK" if tail else "ABSENT"}
    return {"books": sorted(seen.values(), key=lambda b: b["book"]), "dynamic": dyn}


# ---------------------------------------------------------------- ④⑤ regex · 同義字
def central_v0101(via: Path | None = None) -> tuple:
    hits = sorted((Path(via or VIA) / "supportive modules" / "registry").glob("VIA_Central_Synonym_Regex_v*.json"), key=_vnum_v0101)
    if not hits:
        return None, {}
    try:
        return hits[-1], json.loads(hits[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return hits[-1], {}


def regex_v0101(tree, family: str, eid: str, central: dict) -> dict:
    local = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in RX_CALLS_V0101 \
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "re" and node.args \
                and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            local.append(node.args[0].value)
    uniq = list(dict.fromkeys(local))
    creg = (central or {}).get("regex") or {}
    by_pat = {}
    for k, v in creg.items():
        if isinstance(v, dict) and v.get("pattern"):
            by_pat.setdefault(v["pattern"], []).append(k)
    fam_l, eid_l = family.lower(), eid.lower()
    owned = sorted(k for k, v in creg.items() if isinstance(v, dict)
                   and (fam_l in str(v.get("owner", "")).lower() or eid_l in str(v.get("owner", "")).lower().replace("_", "")))
    same = sorted({k for p in uniq for k in by_pat.get(p, [])})
    return {"local": len(local), "local_unique": len(uniq), "samples": uniq[:6], "central_owned": owned, "same_as_central": same}


def synonyms_v0101(tree, src: str, family: str, eid: str, central: dict) -> dict:
    tables = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or not isinstance(node.value, ast.Dict):
            continue
        d = node.value
        if len(d.keys) < 5 or not all(isinstance(k, ast.Constant) and isinstance(k.value, str) for k in d.keys):
            continue
        def _strish(v):
            return (isinstance(v, ast.Constant) and isinstance(v.value, str)) or (
                isinstance(v, (ast.List, ast.Tuple, ast.Set)) and v.elts and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in v.elts))
        if not all(_strish(v) for v in d.values):
            continue
        tgt = node.targets[0] if isinstance(node, ast.Assign) else node.target
        tables.append({"name": ast.unparse(tgt)[:60], "keys": len(d.keys), "line": node.lineno})
    marks = sorted(v for k, v in HUB_MARKS_V0101.items() if k in src)
    meta = (central or {}).get("synonyms_meta") or {}
    fam_l, eid_l = family.lower(), eid.lower()
    mentioned = sorted(k for k, v in meta.items() if isinstance(v, dict) and (fam_l in str(v.get("source", "")).lower()
                                                                               or eid_l in str(v.get("source", "")).lower()))
    return {"delegated": marks, "local_tables": tables, "central_keys_from_this": mentioned}


# ---------------------------------------------------------------- ⑥ 工作流步 · VDF 輸入範圍
def _book_tail_v0101(folder: Path, pattern: str):
    hits = sorted(folder.glob(pattern), key=_vnum_v0101)
    return hits[-1] if hits else None


def workflow_v0101(sub: str, path: str, via: Path | None = None) -> dict:
    via = Path(via or VIA)
    wf = _book_tail_v0101(via / "supportive modules" / "registry", f"VIA_Workflow_{sub}_SSOT_v*.json")
    steps = []
    if wf:
        try:
            for w in json.loads(wf.read_text(encoding="utf-8")).get("workflows") or []:
                for s in w.get("steps") or []:
                    eng = s.get("engine")
                    pats = eng if isinstance(eng, list) else [eng] if isinstance(eng, str) else []
                    if any(fnmatch.fnmatch(path, p) for p in pats):
                        steps.append({"code": s.get("code"), "name": s.get("name", ""), "verb": s.get("verb", "")})
        except (OSError, ValueError):
            pass
    out = {"book": wf.name if wf else "", "steps": steps}
    if sub == "VDF":
        ub = _book_tail_v0101(via / "functional modules" / "VDF", "VDF_InputUniverse_SSOT_v*.json")
        uni = []
        if ub:
            try:
                u = json.loads(ub.read_text(encoding="utf-8"))
                for e in u.get("engines") or []:
                    if isinstance(e, dict) and isinstance(e.get("engine"), str) and fnmatch.fnmatch(path, e["engine"]):
                        ins = [i.get("id") for i in u.get("inputs") or [] if isinstance(i, dict)
                               and (e.get("id") in (i.get("engines") or [])
                                    or fnmatch.fnmatch(path, str((i.get("reader") or {}).get("engine", "")) or "\0"))]
                        uni.append({k: e.get(k) for k in ("id", "verb", "item", "wkf", "writes", "net", "role")} | {"inputs": ins})
            except (OSError, ValueError):
                pass
        out["universe_book"] = ub.name if ub else ""
        out["universe"] = uni
    return out


# ---------------------------------------------------------------- 薄尾鏈:尾版常只蓋一兩個函式,參數 / 冊 / regex 在本體
def chain_files_v0101(path: Path) -> list:
    """尾版 → 本體的實際連結鏈(問鎖版全景的 _link:glob 取前版 = 下一個較小版;exec 本體 / 釘名 vNNNN = 跳到那一版;本體 = 停)。"""
    path = Path(path)
    m = re.match(r"^(?P<stem>.+)_v(?P<v>\d{4})$", path.stem)
    if not m or PRIOR._PAN is None or not hasattr(PRIOR._PAN, "_link"):
        return [path]
    stem = m.group("stem")
    fam = {int(re.search(r"_v(\d{4})$", q.stem).group(1)): q for q in path.parent.glob(stem + "_v*.py")
           if re.fullmatch(re.escape(stem) + r"_v\d{4}", q.stem)}
    out, cur, seen = [], path, set()
    while cur is not None and cur not in seen and len(out) < 30:
        seen.add(cur)
        out.append(cur)
        link = PRIOR._PAN._link(cur.read_text(encoding="utf-8", errors="replace"), stem, cur.name)
        v = _vnum_v0101(cur)
        jump = re.search(r"v(\d{4})", link)
        if link.startswith(("exec 本體", "釘名")) and jump:
            cur = fam.get(int(jump.group(1)))
        elif link.startswith("glob"):
            lower = [k for k in fam if k < v]
            cur = fam[max(lower)] if lower else None
        else:
            cur = None
    return out


# ---------------------------------------------------------------- 一支引擎的備料卡
def params_card_v0101(row: dict, sub: str, central: dict | None = None, idx: dict | None = None) -> dict:
    sub = sub.upper()
    p = VIA / row["path"]
    chain = chain_files_v0101(p)
    srcs, mods, parse_err = [], [], ""
    for q in chain:                                      # 新到舊;同名參數 / 冊取最新那一版的
        txt = q.read_text(encoding="utf-8", errors="replace")
        try:
            mods.extend(ast.parse(txt).body)
        except SyntaxError as e:
            parse_err = parse_err or f"{q.name} SyntaxError L{e.lineno}"
        srcs.append(txt)
    src = "\n".join(srcs)
    tree = ast.Module(body=mods, type_ignores=[]) if mods else None
    g = PRIOR.gate(row, sub)
    if central is None:
        _, central = central_v0101()
    if idx is None:
        idx = book_index_v0101()
    cli = cli_params_v0101(tree) if tree else {"args": [], "subparsers": []}
    _seen_args = set()
    cli["args"] = [a for a in cli["args"] if not (a["names"][0] in _seen_args or _seen_args.add(a["names"][0]))]
    envs = env_vars_v0101(tree) if tree else []
    bk = books_v0101(tree, idx) if tree else {"books": [], "dynamic": 0}
    rx = regex_v0101(tree, row["family"], row["eid"], central) if tree else {"local": 0, "local_unique": 0, "samples": [], "central_owned": [], "same_as_central": []}
    sy = synonyms_v0101(tree, src, row["family"], row["eid"], central) if tree else {"delegated": [], "local_tables": [], "central_keys_from_this": []}
    wf = workflow_v0101(sub, row["path"])
    surf = {"verbs": set(row["verbs"]), "flags": set(row["flags"])}
    for txt in srcs[1:]:                                 # 子令 / 字面旗標也沿鏈收(v0100 只讀尾版那一支)
        cs = PRIOR.cli_surface(txt)
        surf["verbs"].update(cs["verbs"])
        surf["flags"].update(cs["flags"])
    surf = {k: sorted(v) for k, v in surf.items()}
    need = [a for a in cli["args"] if a["required"]]
    tpl = g["launch"]["short"] + "".join(f" {a['names'][0]} <值>" if not a["positional"] else f" <{a['names'][0]}>" for a in need
                                         if a["names"][0] not in g["launch"]["short"].split())
    notes = []
    if sy["local_tables"] and not sy["delegated"]:
        notes.append(f"本地同義字表 {len(sy['local_tables'])} 張未委樞(只列不改)")
    if rx["same_as_central"]:
        notes.append("本地 regex 與中央同式:" + " · ".join(rx["same_as_central"][:4]) + "(可委中央;只列不改)")
    absent = [b["book"] for b in bk["books"] if b["state"] == "ABSENT"]
    if absent:
        notes.append("冊不在樹上:" + " · ".join(absent[:4]))
    if parse_err:
        notes.append("讀不過:" + parse_err)
    consent = [e for e in envs if e in CONSENT_V0101]
    lamp = "RED" if g["lamp"] == "RED" else ("NA" if g["lamp"] == "NA" else ("YELLOW" if g["lamp"] == "YELLOW" or notes else "GREEN"))
    return {"sub": sub, "eid": row["eid"], "family": row["family"], "version": row["version"], "path": row["path"], "code": row["code"],
            "chain": [f"v{_vnum_v0101(q):04d}" for q in chain],
            "lamp": lamp, "gate": {"lamp": g["lamp"], "block": g["block"], "warn": g["warn"]}, "notes": notes,
            "params": {"cli": cli, "verbs": surf["verbs"], "flags": surf["flags"], "env": envs, "consent": consent},
            "ssot": bk, "regex": rx, "synonyms": sy, "workflow": wf,
            "launch": dict(g["launch"], template=tpl,
                           consent_note=("要在你自己的視窗開 " + " / ".join(consent) + "(AI 永不代設)") if consent else "")}


# ---------------------------------------------------------------- 動詞
def _print_card_v0101(c: dict, tag: str) -> None:
    print(f"[{tag} 單引擎備料] {c['lamp']} · {c['eid']} {c['family']} {c['version']} · 編號 {c['code']} · {c['path']}")
    if len(c.get("chain") or []) > 1:
        print(f"  [薄尾鏈] {' → '.join(c['chain'])}(參數 / 冊 / regex / 同義字從整條鏈收;同名取新版)")
    for b in c["gate"]["block"]:
        print("  [擋] " + b)
    cli = c["params"]["cli"]
    print(f"  ① 輸入參數 argparse {len(cli['args'])} 條" + (f" · 子令 {' '.join(cli['subparsers'])}" if cli["subparsers"] else "")
          + (f" · 子令 {' '.join(c['params']['verbs'][:14])}" if c["params"]["verbs"] else "")
          + (f" · 字面旗標 {' '.join(c['params']['flags'][:14])}" if c["params"]["flags"] else ""))
    for a in cli["args"][:20]:
        extra = " · ".join(f"{k}={a[k]!r}"[:60] for k in ("default", "choices", "type", "nargs", "action") if k in a)
        print(f"     {'*' if a['required'] else ' '} {' / '.join(a['names'])}" + (f"  {extra}" if extra else "") + (f"  — {a['help']}" if a.get("help") else ""))
    print(f"  ② 環境變數 {' · '.join(c['params']['env']) or '—'}" + (f"  [同意閘] {c['launch']['consent_note']}" if c["params"]["consent"] else ""))
    print(f"  ③ SSOT 冊 {len(c['ssot']['books'])} 本" + (f" · 動態冊名 {c['ssot']['dynamic']} 處(不猜)" if c["ssot"]["dynamic"] else ""))
    for b in c["ssot"]["books"][:15]:
        print(f"     {'✓' if b['state'] == 'OK' else '✗'} {b['book']} → {b['tail'] or 'ABSENT'}" + (" (釘版)" if b["pinned"] else ""))
    r = c["regex"]
    print(f"  ④ regex 本地 {r['local']} 條(不重複 {r['local_unique']})· 中央屬本支 {len(r['central_owned'])} 鍵"
          + (f" · 與中央同式 {' '.join(r['same_as_central'])}" if r["same_as_central"] else ""))
    s = c["synonyms"]
    print(f"  ⑤ 同義字 委樞 {' · '.join(s['delegated']) or '無'} · 本地表 {len(s['local_tables'])} 張"
          + "".join(f" [{t['name']} {t['keys']} 鍵 L{t['line']}]" for t in s["local_tables"][:4])
          + f" · 中央同義字來源提到本支 {len(s['central_keys_from_this'])} 鍵")
    w = c["workflow"]
    print(f"  ⑥ 工作流步 {' · '.join(x['code'] for x in w['steps']) or '—'}({w['book'] or '冊不在'})")
    for u in w.get("universe") or []:
        print(f"     輸入範圍 {u['id']} {u.get('verb') or ''} → {u.get('item') or ''} · 輸入 {' '.join(u['inputs']) or '—'} · 觸網 {u.get('net')} · {u.get('role') or ''}")
    for n in c["notes"]:
        print("  [黃] " + n)
    print(f"  ⑦ [啟動] {c['launch']['template']}   (先自測:{c['launch']['selftest']})")


def prep_v0101(sub: str, write: bool = True, out_dir: Path | None = None) -> dict:
    sub = sub.upper()
    rows = PRIOR.engines(sub)
    gates = PRIOR.list_gates(rows, sub)
    by_fam = {}
    for r in rows:
        by_fam.setdefault(r["family"], []).append(r)
    _, central = central_v0101()
    idx = book_index_v0101()
    cards = []
    for g in gates:
        one, _ = PRIOR.resolve(by_fam[g["family"]], g["family"])
        c = params_card_v0101(one or by_fam[g["family"]][0], sub, central, idx)
        c["launch"]["short"] = g["launch"]["short"]                     # 同號異名改全名的那一套照 list
        cards.append(c)
    lamps = {k: sum(1 for c in cards if c["lamp"] == k) for k in ("GREEN", "YELLOW", "RED", "NA")}
    summary = {"engines": len(cards), "lamps": lamps,
               "with_cli": sum(1 for c in cards if c["params"]["cli"]["args"] or c["params"]["flags"]),
               "with_books": sum(1 for c in cards if c["ssot"]["books"]),
               "local_synonym_tables": sum(len(c["synonyms"]["local_tables"]) for c in cards),
               "delegated": sum(1 for c in cards if c["synonyms"]["delegated"]),
               "regex_same_as_central": sum(1 for c in cards if c["regex"]["same_as_central"]),
               "consent": sum(1 for c in cards if c["params"]["consent"])}
    doc = {"sub": sub, "at": time.strftime("%Y-%m-%d %H:%M:%S"), "by": ENGINE, "summary": summary, "cards": cards}
    if write:
        od = Path(out_dir or PRIOR.OUT)
        od.mkdir(parents=True, exist_ok=True)
        (od / f"ENGINE_PARAMS_{sub}_latest.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        doc["page"] = str(write_params_page_v0101(doc, od))
    return doc


def write_params_page_v0101(doc: dict, out_dir: Path) -> Path:
    spec = PRIOR._load(PRIOR._newest("CGC_MDL173_MatrixReportSpec_v*.py"), "_mdl253_spec_v0101")
    rows = []
    for c in doc["cards"]:
        cli = c["params"]["cli"]
        rows.append([{"t": c["lamp"], "s": c["lamp"]}, c["eid"], c["family"], c["version"],
                     f"{len(cli['args'])} 條" + (f" · {' '.join(cli['subparsers'])}" if cli["subparsers"] else ""),
                     " ".join(c["params"]["env"])[:80] or "—",
                     " · ".join(f"{b['book']}{'' if b['state'] == 'OK' else '✗'}" for b in c["ssot"]["books"])[:160] or "—",
                     f"本地 {c['regex']['local_unique']} · 中央 {len(c['regex']['central_owned'])}" + (f" · 同式 {len(c['regex']['same_as_central'])}" if c["regex"]["same_as_central"] else ""),
                     (" · ".join(c["synonyms"]["delegated"]) or "未委樞") + (f" · 本地表 {len(c['synonyms']['local_tables'])}" if c["synonyms"]["local_tables"] else ""),
                     " ".join(x["code"] for x in c["workflow"]["steps"])[:60] + (" " + " ".join(u["id"] for u in c["workflow"].get("universe") or []) if c["workflow"].get("universe") else "") or "—",
                     c["launch"]["template"], "; ".join(c["gate"]["block"] + c["notes"])[:200] or "—"])
    s = doc["summary"]
    body = spec.html_table(["燈", "引擎號", "家族", "版本", "輸入參數", "環境變數", "SSOT 冊(✗=不在)", "regex", "同義字", "工作流步 / 輸入範圍", "單引擎啟動", "擋 / 提醒"],
                           rows, caption=f"{doc['sub']} 單引擎備料:{s['engines']} 支(點表頭排序)", center_cols={0})
    kpis = [{"label": "引擎", "value": s["engines"], "state": "NA"}, {"label": "綠", "value": s["lamps"]["GREEN"], "state": "GREEN"},
            {"label": "黃", "value": s["lamps"]["YELLOW"], "state": "YELLOW"}, {"label": "紅(擋)", "value": s["lamps"]["RED"], "state": "RED" if s["lamps"]["RED"] else "GREEN"},
            {"label": "本地同義字表", "value": s["local_synonym_tables"], "state": "YELLOW" if s["local_synonym_tables"] else "GREEN"}]
    return spec.page_html(body, title=f"{doc['sub']} 單引擎備料(參數 · SSOT · regex · 同義字)", out=out_dir / f"ENGINE_PARAMS_{doc['sub']}_latest.html",
                          kpis=kpis, payload={"summary": s}, md="", subtitle=f"{doc['at']} · engine prep · {ENGINE}",
                          law="只讀(ast.parse,不執行);本地同義字表 / 與中央同式的 regex 只列不改;同意閘 AI 永不代設。")


def engine_main(sub: str, args: list, tag: str) -> int:
    verb, rest = (args[0], list(args[1:])) if args else ("list", [])
    if verb not in ("params", "prep"):
        return PRIOR.engine_main(sub, list(args), tag)
    as_json = "--json" in rest
    rest = [a for a in rest if a not in ("--json", "--no-page")]
    try:
        rows = PRIOR.engines(sub.upper())
    except RuntimeError as e:
        print(json.dumps({"engine_params": {"sub": sub.upper(), "lamp": "RED", "why": str(e)}}, ensure_ascii=False))
        return 1
    if verb == "prep":
        doc = prep_v0101(sub, write="--no-page" not in args)
        s = doc["summary"]
        if as_json:
            print(json.dumps({"engine_prep": {k: v for k, v in doc.items() if k != "cards"}}, ensure_ascii=False))
        else:
            print(f"[{tag} 單引擎備料] {doc['sub']} {s['engines']} 支 · 綠 {s['lamps']['GREEN']} · 黃 {s['lamps']['YELLOW']} · 紅 {s['lamps']['RED']} · 庫 {s['lamps']['NA']}"
                  f" · 有參數 {s['with_cli']} · 讀冊 {s['with_books']} · 委樞 {s['delegated']} · 本地同義字表 {s['local_synonym_tables']}"
                  f" · regex 與中央同式 {s['regex_same_as_central']} 支 · 要同意閘 {s['consent']} 支")
            for c in doc["cards"]:
                mark = {"GREEN": "綠", "YELLOW": "黃", "RED": "紅", "NA": "庫"}[c["lamp"]]
                print(f"  {mark} {c['eid']:<7} {c['family'][:40]:<40} 參數 {len(c['params']['cli']['args']):>2} · 冊 {len(c['ssot']['books']):>2}"
                      f" · regex {c['regex']['local_unique']:>2} · 同義字 {'委' if c['synonyms']['delegated'] else ('本地' if c['synonyms']['local_tables'] else '—')}"
                      f" → {c['launch']['template']}")
            if doc.get("page"):
                print(f"  [頁] {doc['page']}")
        return 1 if s["lamps"]["RED"] else 0
    if not rest:
        print("用法:engine params <引擎號 | 全名 | 名稱片段> [--json]")
        return 3
    row, cands = PRIOR.resolve(rows, rest[0])
    if row is None:
        print(json.dumps({"engine_params": {"sub": sub.upper(), "key": rest[0], "lamp": "NODATA" if not cands else "AMBIGUOUS",
                                            "candidates": [{"eid": c["eid"], "family": c["family"]} for c in cands]}}, ensure_ascii=False))
        return 3
    c = params_card_v0101(row, sub)
    if not as_json:
        _print_card_v0101(c, tag)
    print(json.dumps({"engine_params": c}, ensure_ascii=False))
    return {"GREEN": 0, "YELLOW": 2, "RED": 1, "NA": 2}[c["lamp"]]


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    rc = PRIOR.selftest()
    print(f"=== {ENGINE} · 薄尾自測(單引擎備料:參數 · 環境變數 · SSOT · regex · 同義字 · 工作流步)===")
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("① 前版 v0100 自測過(list · check · card 照舊)", rc == 0, f"rc {rc}")
    demo = ("import argparse, os, re\n"
            "SYN = {'買進': 'BUY', '加碼': 'BUY', '賣出': 'SELL', '減碼': 'SELL', '持有': 'HOLD'}\n"
            "BOOK = 'supportive modules/registry/VIA_Central_Synonym_Regex_v*.json'\n"
            "UNI = 'VDF_InputUniverse_SSOT_v0101.json'\n"
            "GONE = 'VIA_NoSuchBook_SSOT_v0100.json'\n"
            "def main():\n    ap = argparse.ArgumentParser()\n    sp = ap.add_subparsers()\n    sp.add_parser('daily')\n"
            "    ap.add_argument('--date', default='2026-10-01', help='資料日')\n    ap.add_argument('--market', choices=['TWSE', 'TPEX'], required=True)\n"
            "    ap.add_argument('target')\n    if os.environ.get('VIA_NET_CONSENT') != 'YES' or 'VIA_DEMO_FLAG' in os.environ:\n        return 2\n"
            "    return bool(re.match(r'^[1-9]\\d{3}$', '2330')) and re.compile('abc')\n")
    tree = ast.parse(demo)
    cli = cli_params_v0101(tree)
    by = {a["names"][0]: a for a in cli["args"]}
    chk("② 輸入參數:旗標 · 預設 · 選項 · 必填 · 說明 · 位置參數 · 子令",
        by["--date"].get("default") == "2026-10-01" and by["--date"]["required"] is False and by["--date"].get("help") == "資料日"
        and by["--market"].get("choices") == ["TWSE", "TPEX"] and by["--market"]["required"] is True
        and by["target"]["positional"] and by["target"]["required"] and cli["subparsers"] == ["daily"], cli)
    envs = env_vars_v0101(tree)
    chk("③ 環境變數:get / in 都認;同意閘名字照實列", envs == ["VIA_DEMO_FLAG", "VIA_NET_CONSENT"], envs)
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        reg = t / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        for n in ("VIA_Central_Synonym_Regex_v0101.json", "VIA_Central_Synonym_Regex_v0102.json"):
            (reg / n).write_text("{}", encoding="utf-8")
        (t / "functional modules" / "VDF").mkdir(parents=True)
        (t / "functional modules" / "VDF" / "VDF_InputUniverse_SSOT_v0103.json").write_text("{}", encoding="utf-8")
        idx = book_index_v0101(t)
    bk = {b["book"]: b for b in books_v0101(tree, idx)["books"]}
    chk("④ SSOT 冊:萬用 _v* 與釘版名都解到樹上尾版;冊不在 = ABSENT",
        bk["VIA_Central_Synonym_Regex"]["tail"].endswith("_v0102.json") and bk["VDF_InputUniverse_SSOT"]["tail_version"] == "v0103"
        and bk["VDF_InputUniverse_SSOT"]["pinned"] and bk["VIA_NoSuchBook_SSOT"]["state"] == "ABSENT", {k: (v["tail_version"], v["state"]) for k, v in bk.items()})
    cen = {"regex": {"TW_TICKER": {"pattern": r"^[1-9]\d{3}$", "owner": "VDF_ENG999_Demo"}, "X": {"pattern": "zzz", "owner": "other"}},
           "synonyms_meta": {"RATING_BUY": {"source": "union of vdf_eng999_demo"}}}
    rx = regex_v0101(tree, "VDF_ENG999_Demo", "ENG999", cen)
    sy = synonyms_v0101(tree, demo, "VDF_ENG999_Demo", "ENG999", cen)
    chk("⑤ regex:本地字面條數 · 中央屬本支的鍵 · 與中央同式(可委中央,只列)",
        rx["local"] == 2 and rx["central_owned"] == ["TW_TICKER"] and rx["same_as_central"] == ["TW_TICKER"], rx)
    chk("⑥ 同義字:本地表(≥ 5 鍵、值是字串)抓到 · 沒委樞印記 · 中央來源提到本支",
        sy["local_tables"] and sy["local_tables"][0]["name"] == "SYN" and sy["delegated"] == ["中央同義字 / 正則冊"]
        and sy["central_keys_from_this"] == ["RATING_BUY"], sy)
    try:
        vdf_rows = PRIOR.engines("VDF")
        one, _ = PRIOR.resolve(vdf_rows, "VDF_ENG055_OmniFetch")
        c55 = params_card_v0101(one, "VDF") if one else {}
        uni = (c55.get("workflow") or {}).get("universe") or []
        chk("⑦ 實樹 VDF:ENG055 備料卡 → 輸入範圍冊 E-01(IN-01 用到)· 工作流步 · 啟動短令 via-vdfeng",
            bool(one) and any(u["id"] == "E-01" and "IN-01" in u["inputs"] for u in uni) and c55["launch"]["template"].startswith("via-vdfeng"),
            (c55.get("lamp"), [u["id"] for u in uni], c55.get("launch", {}).get("template")))
        chk("⑦b 薄尾鏈:ENG055 尾版只蓋閘,參數在本體 → 鏈走到 exec 的本體(v0118)· 收到本體的旗標(--lane …)/ 環境變數",
            bool(one) and len(c55["chain"]) >= 2 and c55["chain"][-1] == "v0118"
            and (c55["params"]["cli"]["args"] or c55["params"]["env"]) and "--lane" in c55["params"]["flags"],
            (c55.get("chain"), len(c55["params"]["cli"]["args"]), c55["params"]["env"][:6], c55["params"]["flags"][:8]))
        vrn_rows = PRIOR.engines("VRN")
        one, _ = PRIOR.resolve(vrn_rows, "VRN_ENG398_PraddleExtractor")
        c398 = params_card_v0101(one, "VRN") if one else {}
        chk("⑧ 實樹 VRN:ENG398 備料卡 → 有輸入參數(argparse 或字面旗標)· 短令 via-vrneng",
            bool(one) and (c398["params"]["cli"]["args"] or c398["params"]["flags"]) and c398["launch"]["template"].startswith("via-vrneng"),
            (c398.get("lamp"), len(c398.get("params", {}).get("cli", {}).get("args", [])), [b["book"] for b in c398.get("ssot", {}).get("books", [])][:3]))
        with tempfile.TemporaryDirectory() as tmp:
            doc = prep_v0101("VRN", write=True, out_dir=Path(tmp))
            wrote = (Path(tmp) / "ENGINE_PARAMS_VRN_latest.json").is_file() and (Path(tmp) / "ENGINE_PARAMS_VRN_latest.html").is_file()
        chk("⑨ prep:整個子系統一支一列 · json + html 落地(暫存夾)· 燈數加總 = 支數",
            wrote and doc["summary"]["engines"] > 10 and sum(doc["summary"]["lamps"].values()) == doc["summary"]["engines"], doc["summary"])
    except RuntimeError as e:
        chk("⑦–⑨ 全景鎖版不在 → 照實跳過(不冒充)", False, str(e))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 加速器橋 · 網路橋在 · 不碰 TA-Lib · 不代設同意閘 · 只讀(無寫被讀檔的呼叫)",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"'](VIA_NET_CONSENT|VIA_SCRAPE_CONSENT)[\"']\]\s*=(?!=)", src))
    print(f"  [計] {ENGINE} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'rc=' + str(rc)} · 合計 {'PASS' if all(ok) and rc == 0 else 'FAIL'}")
    return 0 if all(ok) and rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
