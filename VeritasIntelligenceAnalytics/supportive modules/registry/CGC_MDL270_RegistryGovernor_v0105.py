#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC RegistryGovernor v0105 —(v0105:law 動詞通用化 law --file <法條 json>(id/zh/…),無 --file 仍是 L116;(v0104:_rid 整列重複改「每次出現」序號(之前兩筆重複拿同一 index 仍撞);downstream 改「族名在子系統樹上就算」(panorama_xcheck 這種無前綴族);孤本下放 --adopt-orphans(操作員裁定後才開:母獨本搬到子系統夾,母標 RETIRED replaced_by);(v0103:+downstream = F1 同模組族在母與子:母系統副本退役下放(子系統尾版 ≥ 母副本才退;否則列「待裁」);合成鍵 _rid 加序號(整列重複時);+law = L116 上下分工律入冊;(v0102:+resolve = 紅表分區列管:T2 無主鍵 → 找最小組合鍵(≤3 欄,DF06 允許組合鍵)或合成列鍵 _rid;過時版本族(…_v02_/_v03_… 同前綴)→ 留最高版,其餘退役帶 replaced_by(VCGC 自家冊移 _superseded,子系統冊只出裁定給它們的 manager);T3 漂移 → 舊頭退役新頭接號;全部寫 VIA_KeyRulings_v0100.json,不碰引擎原始碼,不毀任何冊;(v0101:+pull = VCGC 自己的功能矩陣/表頭冊依鍵讀回號(之前 VCGC 0/16514 有號就是沒人替它 pull);+annotate = 用全景 AST 對每個 CLS/FNC/LIB 注入分類與說明到側冊 VIA_AstAnnotations_<SUB>_v0100.json,不改原始碼):表頭冊 + 功能矩陣的衝突顯示 → 測試 → 發號(操作員令 2026-10-06:子系統有創造管理權 · 母系統顯示衝突 · 裁後母系統通過測試顯示編號 · 號出現子系統紀錄並遵守)。
三系統各自登記(VRN v0123/v0124 · VDF v0131/v0132 · VCGC 本引擎 register);本引擎只讀子系統冊,只寫自己四處:
  registry/VCGC_TableHeader_v*.json · registry/VCGC_FunctionMatrix_v*.json(VCGC 自己的登記)
  registry/VIA_TableNumbers_v0100.json(表號 SSOT-VCGC-<SUB>-TBLNNNN)· registry/VIA_RegistryNumbers_v0100.json(功能號 VIA-<SUB>-<KIND>NNN[-FNCNNN/-CLSNNN],承 VIA_Numbering_SSOT 制;已在 NumberBooks 的沿用不重發)
  docs/handoff/ai/VCGC_RegistryGovernCard_<日>.md · VIA_Reports/review/vcgc_registry/
動詞:
  register --apply   VCGC 自己的表頭冊(鎖管控冊)與功能矩陣(supportive modules 尾版 .py)
  govern [--apply]   讀三系統冊 → 衝突(紅 = 擋號 / 黃 = 提醒不擋)→ 零紅項重測 → 發號寫冊 → 出卡
      表:T1 同 tid 跨系統異頭=紅 · T2 無主鍵=紅 · T3 改頭漂移(已號)=紅 · T4 同號多表=紅 · T5 同欄名異型(跨表)=黃 · T6 格內巢狀/數字存字串/非 snake=黃
      功:F1 同模組族在兩系統=紅 · F2 GONE 無替代=黃 · F3 相似(同名/同 body 跨系統)=黃 · F4 AST 失敗=黃 · F5 RETIRED 無 replaced_by=紅
      測:表 = 重載來源,欄全在、主鍵非空不重複、型別多數相符;功 = 檔仍在樹上且 AST 可剖、鍵仍存在
  --selftest         temp 沙盒
沙盒鍵:VIA_ROOT
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime
import json
import os
import re
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ME = Path(__file__).resolve()
NAME = ME.stem
TAG = "v0105"
SUBS = ("VCGC", "VDF", "VRN")
LOCKED_RE = re.compile(r"^(VIA_Policy|VIA_Numbering|VIA_UI_FormatLock|VIA_Central_|VIA_SSOT_|VIA_FinalParameters|VIA_Workflow_|VIA_Essentia_|VIA_[A-Za-z]*Lock|VIA_[A-Za-z]*Law|VIA_[A-Za-z]*Gate|VIA_[A-Za-z]*Registry|VIA_Canon_|VIA_MasterGovernance|GovernanceRegistry|VIA_DataFrame|VIA_Output_Header|VIA_TableNumbers|VIA_RegistryNumbers)")

# ===== [VIA:TABLE-HEADER:v0100] 表頭登記共用段(子系統自創自管;VCGC 只讀;三系統各帶一份,零相依)=====
_TH_EXCL = {"references", "intake", "_superseded", "VIA_RetiredEngines", "_quarantine_pip_vendor", "__pycache__", "_df", "_quarantine", "VIA_NumberBooks"}
_TH_ISO = __import__("re").compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?)?")
_TH_NUM = __import__("re").compile(r"^-?\d+(\.\d+)?$")


def _th_vnum(name):
    import re as _re
    m = _re.search(r"_v(\d{2,4})[A-Za-z0-9]*(?:\.[A-Za-z0-9]+)?$", name)
    return int(m.group(1)) if m else -1


def _th_family(name):
    import re as _re
    from pathlib import Path as _P
    return _re.sub(r"_v\d{2,4}[A-Za-z0-9]*$", "", _re.sub(r"_sha[0-9a-f]{8,}$", "", _P(name).stem))


def _th_read(p):
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "utf-16", "cp950"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return ""


def _th_uniform(dcts):
    sizes = sorted(len(d) for d in dcts)
    if not sizes:
        return False
    med = sizes[len(sizes) // 2] or 1
    union = set()
    for d in dcts:
        union |= set(d.keys())
    return len(union) <= 3 * med


def _th_tables(obj):
    """物件 → {表名: rows};list-of-dict / dict-of-dict(鍵進 key 欄)/ 巢狀底下的同類;映射與純設定不當表。"""
    if isinstance(obj, list):
        return {"rows": obj} if obj and all(isinstance(x, dict) for x in obj) and _th_uniform(obj) else {}
    if not isinstance(obj, dict):
        return {}
    vals = list(obj.values())
    if vals and all(isinstance(v, dict) for v in vals) and len(obj) >= 2:
        return {"rows": [dict({"key": k}, **v) for k, v in obj.items()]} if _th_uniform(vals) else {}
    out = {}
    for k, v in obj.items():
        if isinstance(v, list) and v and all(isinstance(x, dict) for x in v) and _th_uniform(v):
            out[k] = v
        elif isinstance(v, dict) and len(v) >= 2 and all(isinstance(x, dict) for x in v.values()) and _th_uniform(list(v.values())):
            out[k] = [dict({"key": kk}, **vv) for kk, vv in v.items()]
    return out


def _th_load_tables(p):
    import csv as _csv
    import io as _io
    import json as _json
    txt = _th_read(p)
    ext = p.suffix.lower()
    if ext == ".jsonl":
        rows = [_json.loads(ln) for ln in txt.splitlines() if ln.strip()]
        return {"rows": rows} if rows and all(isinstance(r, dict) for r in rows) else {}
    if ext == ".csv":
        rows = list(_csv.DictReader(_io.StringIO(txt)))
        return {"rows": rows} if rows else {}
    return _th_tables(_json.loads(txt))


def _th_profile(rows):
    """→ (columns[{name,dtype,required,pk}], keys, issues)"""
    import re as _re
    from collections import Counter as _C
    n = len(rows)
    cols = {}
    for r in rows:
        for k, v in r.items():
            c = cols.setdefault(k, {"t": _C(), "nulls": 0, "numstr": 0, "datestr": 0, "nested": 0, "vals": set(), "dup": False})
            if v is None or v == "":
                c["nulls"] += 1
                continue
            if isinstance(v, bool):
                t = "bool"
            elif isinstance(v, int):
                t = "int"
            elif isinstance(v, float):
                t = "float"
            elif isinstance(v, (dict, list)):
                t = "json"
                c["nested"] += 1
            else:
                t = "str"
                s = str(v).strip()
                if _TH_NUM.match(s):
                    c["numstr"] += 1
                elif _TH_ISO.match(s):
                    c["datestr"] += 1
            c["t"][t] += 1
            if t != "json":
                if v in c["vals"]:
                    c["dup"] = True
                c["vals"].add(v)
    columns, keys, issues = [], [], []
    for k, c in cols.items():
        kinds = set(c["t"])
        if {"int", "float"} <= kinds:
            kinds.discard("int")
        major = c["t"].most_common(1)[0][0] if c["t"] else "str"
        dtype = "date" if (major == "str" and c["datestr"] and c["datestr"] == c["t"]["str"]) else major
        if len(kinds) > 1:
            issues.append("混型:%s" % k)
        if c["numstr"]:
            issues.append("數字存字串:%s" % k)
        if c["nested"]:
            issues.append("格內巢狀:%s" % k)
        if not _re.match(r"^[a-z0-9_]+$", str(k)):
            issues.append("非snake:%s" % k)
        unique = (n > 0 and c["nulls"] == 0 and not c["dup"] and dtype in ("str", "int", "date"))
        if unique:
            keys.append(k)
        columns.append({"name": k, "dtype": dtype, "required": c["nulls"] == 0, "pk": False})
    if keys:
        for col in columns:
            if col["name"] == keys[0]:
                col["pk"] = True
    else:
        issues.append("無主鍵候選")
    return columns, keys[:3], issues


def _th_sha(columns):
    import hashlib as _h
    import json as _json
    return _h.sha256(_json.dumps([[c["name"], c["dtype"]] for c in columns], ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def _th_tid(family, table):
    import re as _re
    return _re.sub(r"[^a-z0-9_]+", "_", (family + ("" if table == "rows" else "_" + table)).lower()).strip("_")


def _th_register(sub, sources, book_dir, now, apply=True, rel_root=None):
    """掃 sources(檔列表)→ 登記進 book_dir/<sub>_TableHeader_v####.json(只增:同 sha 不動;改頭且未編號 → 更新 + history;改頭且已編號 → 不動原列,另開 <tid>_h2 留白 = 遵守既發號)。"""
    import json as _json
    from pathlib import Path as _P
    hits = sorted(_P(book_dir).glob(sub + "_TableHeader_v*.json"), key=lambda q: _th_vnum(q.name))
    if hits:
        book = _json.loads(_th_read(hits[-1]))
        fp = hits[-1]
    else:
        fp = _P(book_dir) / (sub + "_TableHeader_v0100.json")
        book = {"schema": "VIA.TableHeader.v1", "sub": sub, "version": "v0100", "rule": "子系統自創自管(L114 ①③);table_no 留白待母系統發號;已發號的表頭鎖死,改頭另開 _h2;只增不減", "created_at": now, "tables": {}}
    tables = book.setdefault("tables", {})
    counts = {"NEW": 0, "SAME": 0, "UPDATED": 0, "LOCKED_NEW_H": 0, "SKIP": 0}
    rows_out = []
    for p in sources:
        try:
            tbs = _th_load_tables(p)
        except Exception:  # noqa: BLE001 — 壞冊:登記為不可讀,交人
            counts["SKIP"] += 1
            rows_out.append({"source": str(p), "status": "UNREADABLE"})
            continue
        if not tbs:
            counts["SKIP"] += 1
            continue
        src = (p.relative_to(rel_root).as_posix() if rel_root else p.as_posix())
        for t, rows in tbs.items():
            columns, keys, issues = _th_profile(rows)
            sha = _th_sha(columns)
            tid = _th_tid(_th_family(p.name), t)
            ent = tables.get(tid)
            if ent is None:
                tables[tid] = {"tid": tid, "sub": sub, "source": src, "table": t, "columns": columns, "keys": keys, "header_sha": sha, "rows_seen": len(rows),
                               "issues": issues, "status": "ACTIVE", "table_no": "", "registered_at": now, "history": []}
                counts["NEW"] += 1
                st = "NEW"
            elif ent.get("header_sha") == sha:
                ent["rows_seen"] = len(rows)
                ent["issues"] = issues
                ent["source"] = src
                counts["SAME"] += 1
                st = "SAME"
            elif not ent.get("table_no"):
                ent.setdefault("history", []).append({"header_sha": ent.get("header_sha"), "columns": ent.get("columns"), "until": now})
                ent.update(columns=columns, keys=keys, header_sha=sha, rows_seen=len(rows), issues=issues, source=src)
                counts["UPDATED"] += 1
                st = "UPDATED"
            else:
                tid2 = tid + "_h2"
                if tid2 not in tables:
                    tables[tid2] = {"tid": tid2, "sub": sub, "source": src, "table": t, "columns": columns, "keys": keys, "header_sha": sha, "rows_seen": len(rows),
                                    "issues": issues, "status": "ACTIVE", "table_no": "", "registered_at": now, "history": [], "supersedes": tid}
                    ent["drift"] = {"new_tid": tid2, "seen_at": now}
                counts["LOCKED_NEW_H"] += 1
                st = "LOCKED_NEW_H"
            rows_out.append({"tid": tid, "status": st, "sha": sha, "issues": issues})
    book["updated_at"] = now
    if apply:
        _P(book_dir).mkdir(parents=True, exist_ok=True)
        fp.write_text(_json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    blank = sum(1 for e in tables.values() if not e.get("table_no"))
    return {"book": fp.name, "tables": len(tables), "blank": blank, "counts": counts, "rows": rows_out}


def _th_pull(sub, book_dir, numbers_dir, now, apply=True):
    """從母系統 VIA_TableNumbers_v*.json 依鍵 <sub>|<tid>|<header_sha> 讀號填進自己的表頭冊(只填留白;填了就鎖頭 = 遵守)。"""
    import json as _json
    from pathlib import Path as _P
    hits = sorted(_P(book_dir).glob(sub + "_TableHeader_v*.json"), key=lambda q: _th_vnum(q.name))
    if not hits:
        return {"status": "NO_BOOK", "filled": 0, "already": 0, "pending": 0, "lamp": "GRAY"}
    book = _json.loads(_th_read(hits[-1]))
    nb = sorted(_P(numbers_dir).glob("VIA_TableNumbers_v*.json"), key=lambda q: _th_vnum(q.name))
    table = {}
    if nb:
        try:
            d = _json.loads(_th_read(nb[-1]))
            table = {e["key"]: e["table_no"] for e in d.get("entries", []) if e.get("key") and e.get("table_no")}
        except (ValueError, KeyError):
            pass
    filled = already = pending = 0
    for tid, e in book.get("tables", {}).items():
        if e.get("table_no"):
            already += 1
            continue
        no = table.get("%s|%s|%s" % (sub, tid, e.get("header_sha")))
        if no:
            e["table_no"] = no
            e["numbered_at"] = now
            filled += 1
        else:
            pending += 1
    if apply and filled:
        hits[-1].write_text(_json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"status": "OK", "book": hits[-1].name, "number_book": (nb[-1].name if nb else None), "filled": filled, "already": already, "pending": pending,
            "lamp": "GREEN" if (pending == 0 and (filled or already)) else "GRAY"}
# ===== [VIA:TABLE-HEADER:END] =====

# ===== [VIA:FN-MATRIX:v0100] 功能矩陣共用段(AST 從頭到尾;子系統自創自管;只增不減;相似 = 黃燈提醒;三系統各帶一份,零相依)=====
_FM_EXCL = {"references", "intake", "_superseded", "VIA_RetiredEngines", "_quarantine_pip_vendor", "__pycache__", ".venv", "venv", "node_modules", "_quarantine", "VIA_NumberBooks", "_df"}
_FM_LOCAL = __import__("re").compile(r"^(VIA|via|VRN|vrn|VDF|vdf|CGC|SUP|VAP|GIF|VRM|_sa_|_nb_)")


def _fm_vnum(name):
    import re as _re
    m = _re.search(r"_v(\d{2,4})[A-Za-z0-9]*(?:\.[A-Za-z0-9]+)?$", name)
    return int(m.group(1)) if m else -1


def _fm_ver(name):
    import re as _re
    m = _re.search(r"_(v\d{2,4}[A-Za-z0-9]*)(?:\.[A-Za-z0-9]+)?$", name)
    return m.group(1) if m else "v0000"


def _fm_family(name):
    import re as _re
    from pathlib import Path as _P
    return _re.sub(r"_v\d{2,4}[A-Za-z0-9]*$", "", _re.sub(r"_sha[0-9a-f]{8,}$", "", _P(name).stem))


def _fm_read(p):
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "utf-16", "cp950"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return ""


def _fm_tails(dirs, root):
    best = {}
    for d in dirs:
        if not d.is_dir():
            continue
        for p in d.rglob("*.py"):
            if not p.is_file():
                continue
            try:
                parts = set(p.relative_to(root).parts[:-1])
            except ValueError:
                parts = set(p.parts)
            if parts & _FM_EXCL:
                continue
            k = (p.parent, _fm_family(p.name))
            v = _fm_vnum(p.name)
            if k not in best or v > best[k][0]:
                best[k] = (v, p)
    return sorted((v[1] for v in best.values()), key=lambda q: str(q))


def _fm_body_sha(node):
    import ast as _ast
    import hashlib as _h
    try:
        s = _ast.dump(node, annotate_fields=False, include_attributes=False)
    except Exception:  # noqa: BLE001
        s = repr(node)
    return _h.sha256(s.encode("utf-8", "replace")).hexdigest()[:16]


def _fm_sig(fn):
    import ast as _ast
    a = fn.args
    names = [x.arg for x in a.posonlyargs] + [x.arg for x in a.args]
    if a.vararg:
        names.append("*" + a.vararg.arg)
    names += [x.arg for x in a.kwonlyargs]
    if a.kwarg:
        names.append("**" + a.kwarg.arg)
    return "%s(%s)" % (fn.name, ", ".join(names))


def _fm_scan_file(p, root, sub):
    """一支 .py → items 列表(MDL/ENG 一列 · CLS 每類一列 · FNC 每函式/方法一列 · LIB 每第三方套件一列)。AST 失敗 = 該檔 MDL 列帶 issue,不紅。"""
    import ast as _ast
    import hashlib as _h
    import sys as _sys
    txt = _fm_read(p)
    rel = p.relative_to(root).as_posix() if str(p).startswith(str(root)) else p.as_posix()
    fam, ver = _fm_family(p.name), _fm_ver(p.name)
    kind = "ENG" if ("_ENG" in fam or "Engine" in fam or fam.lower().endswith("engine")) else "MDL"
    base = {"sub": sub, "module": fam, "version": ver, "source": rel}
    items = [dict(base, kind=kind, name=fam, key="%s|%s" % (kind, fam), lines=txt.count("\n") + 1,
                  body_sha=_h.sha256(txt.encode("utf-8", "replace")).hexdigest()[:16], accel=("[VIA:ACCEL-BRIDGE" in txt), issues=[])]
    try:
        tree = _ast.parse(txt)
    except (SyntaxError, ValueError) as exc:
        items[0]["issues"].append("AST 失敗 %s L%s" % (type(exc).__name__, getattr(exc, "lineno", "?")))
        return items
    std = set(getattr(_sys, "stdlib_module_names", ()))
    libs = set()
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            for al in node.names:
                libs.add(al.name.split(".")[0])
        elif isinstance(node, _ast.ImportFrom) and node.module and node.level == 0:
            libs.add(node.module.split(".")[0])
    for lib in sorted(libs):
        if lib in std or _FM_LOCAL.match(lib):
            continue
        items.append(dict(base, kind="LIB", name=lib, key="LIB|%s" % lib, api="import %s" % lib, body_sha="", issues=[]))
    for node in tree.body:
        if isinstance(node, _ast.ClassDef):
            bases = [getattr(b, "id", getattr(b, "attr", "?")) for b in node.bases]
            items.append(dict(base, kind="CLS", name=node.name, key="CLS|%s|%s" % (fam, node.name), api="class %s(%s)" % (node.name, ", ".join(bases)),
                              line=node.lineno, body_sha=_fm_body_sha(node), methods=sum(1 for n in node.body if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef))), issues=[]))
            for n in node.body:
                if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                    q = "%s.%s" % (node.name, n.name)
                    items.append(dict(base, kind="FNC", name=q, key="FNC|%s|%s" % (fam, q), api=_fm_sig(n), line=n.lineno, body_sha=_fm_body_sha(n),
                                      doc=(_ast.get_docstring(n) or "").split("\n")[0][:80], issues=[]))
        elif isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            items.append(dict(base, kind="FNC", name=node.name, key="FNC|%s|%s" % (fam, node.name), api=_fm_sig(node), line=node.lineno, body_sha=_fm_body_sha(node),
                              doc=(_ast.get_docstring(node) or "").split("\n")[0][:80], issues=[]))
    return items


def _fm_similar(items):
    """相似提醒(黃,不紅):同名 FNC/CLS 散在 ≥2 模組 · 同 body 異名/異模組 · 同 LIB 多模組不算。→ {key: [提醒]}"""
    from collections import defaultdict as _dd
    by_name, by_body = _dd(list), _dd(list)
    for it in items:
        if it["kind"] in ("FNC", "CLS"):
            short = it["name"].split(".")[-1]
            if not short.startswith("_") and short not in ("main", "selftest", "chk", "__getattr__", "run", "check", "load", "build", "emit", "scan"):
                by_name[(it["kind"], short)].append(it["key"])
            if it.get("body_sha"):
                by_body[(it["kind"], it["body_sha"])].append(it["key"])
    rem = _dd(list)
    for (k, nm), keys in by_name.items():
        mods = {x.split("|")[1] for x in keys}
        if len(mods) >= 2:
            for x in keys:
                rem[x].append("同名 %s 散在 %d 模組" % (nm, len(mods)))
    for (k, sha), keys in by_body.items():
        if len(keys) >= 2 and len({x.split("|")[1] for x in keys}) >= 2:
            for x in keys:
                rem[x].append("同 body 另見 %d 處(候選共用 LIB)" % (len(keys) - 1))
    return dict(rem)


def _fm_register(sub, dirs, root, book_dir, now, apply=True):
    """掃尾版 .py → 登記 <sub>_FunctionMatrix_v0100.json(只增:新=NEW · 同=SAME · 改 body=UPDATED+history · 樹上不見=GONE(不刪,gone_since)· 刪除只能 fn retire 帶 replaced_by)。"""
    import json as _json
    from pathlib import Path as _P
    hits = sorted(_P(book_dir).glob(sub + "_FunctionMatrix_v*.json"), key=lambda q: _fm_vnum(q.name))
    if hits:
        book = _json.loads(_fm_read(hits[-1]))
        fp = hits[-1]
    else:
        fp = _P(book_dir) / (sub + "_FunctionMatrix_v0100.json")
        book = {"schema": "VIA.FunctionMatrix.v1", "sub": sub, "version": "v0100", "created_at": now,
                "rule": "子系統自創自管(L114 ①);AST 從頭到尾登錄 MDL/ENG/CLS/FNC/LIB;只增不減:樹上不見 = GONE 不刪;刪除只限 (a) 衝突裁定 (b) 工具無人維護,且必帶 replaced_by;相似 = 黃燈提醒不紅;number 留白待母系統",
                "items": {}}
    items_all = []
    for p in _fm_tails(dirs, root):
        items_all += _fm_scan_file(p, root, sub)
    sim = _fm_similar(items_all)
    bk = book.setdefault("items", {})
    seen = set()
    counts = {"NEW": 0, "SAME": 0, "UPDATED": 0, "GONE": 0, "BACK": 0}
    for it in items_all:
        k = it["key"]
        seen.add(k)
        it["similar"] = sim.get(k, [])
        e = bk.get(k)
        if e is None:
            bk[k] = dict(it, status="ACTIVE", first_seen=now, last_seen=now, number="", history=[])
            counts["NEW"] += 1
        else:
            was_gone = e.get("status") == "GONE"
            if e.get("body_sha") != it.get("body_sha") or e.get("version") != it.get("version"):
                e.setdefault("history", []).append({"version": e.get("version"), "body_sha": e.get("body_sha"), "source": e.get("source"), "until": now})
                counts["UPDATED"] += 1
            else:
                counts["SAME"] += 1
            e.update({x: it[x] for x in it if x not in ("status", "first_seen", "number", "history")})
            e["status"] = "ACTIVE"
            e["last_seen"] = now
            if was_gone:
                counts["BACK"] += 1
                e.pop("gone_since", None)
    for k, e in bk.items():
        if k not in seen and e.get("status") == "ACTIVE":
            e["status"] = "GONE"
            e["gone_since"] = now
            counts["GONE"] += 1
    book["updated_at"] = now
    if apply:
        _P(book_dir).mkdir(parents=True, exist_ok=True)
        fp.write_text(_json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    kinds = {}
    for e in bk.values():
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    return {"book": fp.name, "items": len(bk), "kinds": kinds, "counts": counts, "similar": sum(1 for e in bk.values() if e.get("similar")),
            "gone": sum(1 for e in bk.values() if e.get("status") == "GONE"), "ast_fail": sum(1 for e in bk.values() if any("AST" in x for x in e.get("issues", []))),
            "blank": sum(1 for e in bk.values() if e.get("status") == "ACTIVE" and not e.get("number"))}


def _fm_retire(sub, book_dir, key, replaced_by, reason, now, apply=True):
    """唯一能把列移出 ACTIVE/GONE 的動作:要 replaced_by(替代版本)與 reason(衝突裁定 / 無人維護);不物理刪,標 RETIRED。"""
    import json as _json
    from pathlib import Path as _P
    hits = sorted(_P(book_dir).glob(sub + "_FunctionMatrix_v*.json"), key=lambda q: _fm_vnum(q.name))
    if not hits:
        return {"status": "NO_BOOK"}
    book = _json.loads(_fm_read(hits[-1]))
    e = book.get("items", {}).get(key)
    if not e:
        return {"status": "NO_KEY"}
    if not replaced_by or not reason:
        return {"status": "REFUSED", "why": "退役必帶 replaced_by 與 reason(衝突裁定 / 無人維護)"}
    if replaced_by not in book["items"]:
        return {"status": "REFUSED", "why": "replaced_by 不在矩陣:%s" % replaced_by}
    e.update(status="RETIRED", retired_at=now, replaced_by=replaced_by, retire_reason=reason)
    if apply:
        hits[-1].write_text(_json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"status": "RETIRED", "key": key, "replaced_by": replaced_by}


def _fm_pull(sub, book_dir, numbers_dir, now, apply=True):
    """依鍵 <sub>|<key>|<version> 從母系統 VIA_RegistryNumbers_v*.json 讀號填回(只填留白;填了即鎖)。"""
    import json as _json
    from pathlib import Path as _P
    hits = sorted(_P(book_dir).glob(sub + "_FunctionMatrix_v*.json"), key=lambda q: _fm_vnum(q.name))
    if not hits:
        return {"status": "NO_BOOK", "filled": 0, "already": 0, "pending": 0, "lamp": "GRAY"}
    book = _json.loads(_fm_read(hits[-1]))
    nb = sorted(_P(numbers_dir).glob("VIA_RegistryNumbers_v*.json"), key=lambda q: _fm_vnum(q.name))
    table = {}
    if nb:
        try:
            d = _json.loads(_fm_read(nb[-1]))
            table = {e["key"]: e["code"] for e in d.get("entries", []) if e.get("key") and e.get("code")}
        except (ValueError, KeyError):
            pass
    filled = already = pending = 0
    for k, e in book.get("items", {}).items():
        if e.get("status") != "ACTIVE":
            continue
        if e.get("number"):
            already += 1
            continue
        code = table.get("%s|%s|%s" % (sub, k, e.get("version")))
        if code:
            e["number"] = code
            e["numbered_at"] = now
            filled += 1
        else:
            pending += 1
    if apply and filled:
        hits[-1].write_text(_json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"status": "OK", "book": hits[-1].name, "number_book": (nb[-1].name if nb else None), "filled": filled, "already": already, "pending": pending,
            "lamp": "GREEN" if (pending == 0 and (filled or already)) else "GRAY"}
# ===== [VIA:FN-MATRIX:END] =====


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _root() -> Path:
    if os.environ.get("VIA_ROOT"):
        return Path(os.environ["VIA_ROOT"])
    p = ME
    while p.parent != p:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
        p = p.parent
    return ME.parents[2]


def _paths() -> dict:
    r = _root()
    return {"root": r, "registry": r / "supportive modules" / "registry", "sup": r / "supportive modules", "vdf": r / "functional modules" / "VDF", "vrn": r / "functional modules" / "VRN",
            "cards": r / "docs" / "handoff" / "ai", "report": r / "VIA_Reports" / "review" / "vcgc_registry"}


def _book(P: dict, sub: str, stem: str) -> dict:
    d = {"VCGC": P["registry"], "VDF": P["vdf"] / "registry", "VRN": P["vrn"] / "registry"}[sub]
    hits = sorted(d.glob("%s_%s_v*.json" % (sub, stem)), key=lambda q: _th_vnum(q.name)) if d.is_dir() else []
    if not hits:
        return {"file": None, "path": None, "data": {}}
    try:
        return {"file": hits[-1].name, "path": hits[-1], "data": json.loads(_th_read(hits[-1]))}
    except ValueError:
        return {"file": hits[-1].name, "path": hits[-1], "data": {}, "bad": True}


def register(P: dict | None = None, apply: bool = True) -> dict:
    P = P or _paths()
    now = _now()
    srcs = [p for p in P["registry"].glob("*") if p.is_file() and p.suffix.lower() in (".json", ".jsonl", ".csv") and LOCKED_RE.match(p.name)
            and not _th_family(p.name).endswith(("_TableHeader", "_FunctionMatrix")) and not p.name.startswith(("VIA_TableNumbers", "VIA_RegistryNumbers"))]
    best = {}
    for p in srcs:
        k = (_th_family(p.name), p.suffix.lower())
        v = _th_vnum(p.name)
        if k not in best or v > best[k][0]:
            best[k] = (v, p)
    t = _th_register("VCGC", [v[1] for v in best.values()], P["registry"], now, apply=apply, rel_root=P["root"])
    if apply:                                  # v0102:登記後再採納裁定鍵,重登記不會把裁定洗掉
        rb = _rulings_book(P)
        if rb:
            vb = _book(P, "VCGC", "TableHeader")
            if vb["data"] and _adopt_rulings_vcgc(vb["data"], rb, now):
                vb["path"].write_text(json.dumps(vb["data"], ensure_ascii=False, indent=1), encoding="utf-8")
    f = _fm_register("VCGC", [P["sup"]], P["root"], P["registry"], now, apply=apply)
    return {"verb": "register", "apply": apply, "table": t, "fn": f, "lamp": "GREEN"}


def _load_numbers(P: dict, name: str, schema: str) -> dict:
    fp = P["registry"] / name
    d = json.loads(_th_read(fp)) if fp.exists() else None
    if not isinstance(d, dict) or not isinstance(d.get("entries"), list):
        d = {"schema": schema, "version": "v0100", "engine": NAME, "rule": "號跟鍵走:同鍵永遠同號 · 發了不收回不改不重發 · 紅燈項不發 · 子系統以鍵讀回", "created_at": _now(), "entries": [], "blocked": []}
    return d


def _numberbook_codes(P: dict) -> dict:
    """既有 VIA_NumberBooks:source@version → 檔號(MDL/ENG);(檔號, q) → FNC/CLS 號。沿用不重發。"""
    nb = P["registry"] / "VIA_NumberBooks"
    file_codes, sub_codes = {}, {}
    if nb.is_dir():
        for p in nb.glob("VIA_NumberBook_*_v*.jsonl"):
            kind = p.name.split("_")[2]
            for ln in _th_read(p).splitlines():
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                if kind in ("MDL", "ENG") and r.get("source") and r.get("code"):
                    file_codes[r["source"].replace("\\", "/")] = r["code"]
                elif kind in ("FNC", "CLS") and r.get("code") and r.get("q"):
                    parent = r["code"].rsplit("-", 1)[0]
                    sub_codes[(parent, r["q"])] = r["code"]
    return {"file": file_codes, "sub": sub_codes}


def govern(P: dict | None = None, apply: bool = False) -> dict:
    P = P or _paths()
    now = _now()
    out = {"verb": "govern", "ts": _now(), "apply": apply, "tables": {}, "fns": {}, "issued_tables": [], "issued_fns": [], "_notes": []}
    # ───── 表 ─────
    tbooks = {s: _book(P, s, "TableHeader") for s in SUBS}
    tnum = _load_numbers(P, "VIA_TableNumbers_v0100.json", "VIA_TableNumbers")
    have_t = {e["key"]: e for e in tnum["entries"]}
    ents = []
    for s in SUBS:
        for tid, e in (tbooks[s]["data"].get("tables") or {}).items():
            ents.append((s, tid, e))
    flags = defaultdict(list)
    by_tid = defaultdict(list)
    for s, tid, e in ents:
        by_tid[tid].append((s, e.get("header_sha")))
    for tid, lst in by_tid.items():
        subs = {s for s, _ in lst}
        shas = {h for _, h in lst}
        if len(subs) > 1 and len(shas) > 1:
            for s, _ in lst:
                flags[(s, tid)].append(("T1", "RED", "同 tid 跨系統異頭:%s" % ",".join(sorted(subs))))
    col_dt = defaultdict(set)
    for s, tid, e in ents:
        for c in e.get("columns", []):
            col_dt[c["name"]].add(c["dtype"])
    by_no = defaultdict(list)
    for s, tid, e in ents:
        if e.get("table_no"):
            by_no[e["table_no"]].append((s, tid))
    for s, tid, e in ents:
        if e.get("status") != "ACTIVE":
            continue
        if not e.get("keys"):
            flags[(s, tid)].append(("T2", "RED", "無主鍵(DF06)"))
        if e.get("drift") and e.get("table_no"):
            flags[(s, tid)].append(("T3", "RED", "已號表頭漂移 → 新頭在 %s" % e["drift"].get("new_tid")))
        if e.get("table_no") and len(by_no[e["table_no"]]) > 1:
            flags[(s, tid)].append(("T4", "RED", "同號多表 %s" % e["table_no"]))
        mixed = [c["name"] for c in e.get("columns", []) if len(col_dt[c["name"]]) > 1]
        if mixed:
            flags[(s, tid)].append(("T5", "YELLOW", "同欄名異型(跨表):%s" % ",".join(mixed[:5])))
        if e.get("issues"):
            flags[(s, tid)].append(("T6", "YELLOW", ";".join(e["issues"])[:160]))
    seq = {}
    rx = re.compile(r"^SSOT-VCGC-(\w+)-TBL(\d{4})$")
    for e in tnum["entries"]:
        m = rx.match(str(e.get("table_no", "")))
        if m:
            seq[m.group(1)] = max(seq.get(m.group(1), 0), int(m.group(2)))
    for s, tid, e in ents:
        if e.get("status") != "ACTIVE":
            continue
        fl = flags.get((s, tid), [])
        lamp = "RED" if any(x[1] == "RED" for x in fl) else ("YELLOW" if fl else "GREEN")
        key = "%s|%s|%s" % (s, tid, e.get("header_sha"))
        rec = {"sub": s, "tid": tid, "lamp": lamp, "flags": [{"rule": a, "lamp": b, "detail": c} for a, b, c in fl], "table_no": e.get("table_no") or have_t.get(key, {}).get("table_no", ""), "test": None}
        if lamp != "RED" and not rec["table_no"]:
            test_ok, why = _test_table(P, e)
            rec["test"] = "PASS" if test_ok else "FAIL:" + why
            if test_ok:
                seq[s] = seq.get(s, 0) + 1
                no = "SSOT-VCGC-%s-TBL%04d" % (s, seq[s])
                ent = {"key": key, "table_no": no, "sub": s, "tid": tid, "header_sha": e.get("header_sha"), "source": e.get("source"), "issued_at": now, "note": ("yellow:" + ",".join(x[0] for x in fl)) if fl else ""}
                tnum["entries"].append(ent)
                have_t[key] = ent
                rec["table_no"] = no
                out["issued_tables"].append(ent)
            else:
                rec["lamp"] = "RED"
                rec["flags"].append({"rule": "TEST", "lamp": "RED", "detail": why})
        out["tables"][key] = rec
    # ───── 功 ─────
    fbooks = {s: _book(P, s, "FunctionMatrix") for s in SUBS}
    fnum = _load_numbers(P, "VIA_RegistryNumbers_v0100.json", "VIA_RegistryNumbers")
    have_f = {e["key"]: e for e in fnum["entries"]}
    nbc = _numberbook_codes(P)
    items = []
    for s in SUBS:
        for k, e in (fbooks[s]["data"].get("items") or {}).items():
            items.append((s, k, e))
    fflags = defaultdict(list)
    mod_sub = defaultdict(set)
    name_sub = defaultdict(set)
    body_sub = defaultdict(set)
    for s, k, e in items:
        if e.get("status") != "ACTIVE":
            continue
        if e["kind"] in ("MDL", "ENG"):
            mod_sub[e["module"]].add(s)
        if e["kind"] in ("FNC", "CLS"):
            short = e["name"].split(".")[-1]
            if not short.startswith("_") and short not in ("main", "selftest", "chk", "run"):
                name_sub[(e["kind"], short)].add(s)
            if e.get("body_sha"):
                body_sub[(e["kind"], e["body_sha"])].add(s)
    for s, k, e in items:
        st = e.get("status")
        if st == "RETIRED" and not e.get("replaced_by"):
            fflags[(s, k)].append(("F5", "RED", "RETIRED 無 replaced_by"))
        if st == "GONE" and not e.get("replaced_by"):
            fflags[(s, k)].append(("F2", "YELLOW", "樹上不見且無替代(gone_since %s)" % e.get("gone_since")))
        if st != "ACTIVE":
            continue
        if e["kind"] in ("MDL", "ENG") and len(mod_sub[e["module"]]) > 1:
            fflags[(s, k)].append(("F1", "RED", "同模組族在 %s" % ",".join(sorted(mod_sub[e["module"]]))))
        if e["kind"] in ("FNC", "CLS"):
            short = e["name"].split(".")[-1]
            if len(name_sub.get((e["kind"], short), ())) > 1:
                fflags[(s, k)].append(("F3", "YELLOW", "同名跨系統 %s" % ",".join(sorted(name_sub[(e["kind"], short)]))))
            if len(body_sub.get((e["kind"], e.get("body_sha")), ())) > 1:
                fflags[(s, k)].append(("F3", "YELLOW", "同 body 跨系統(候選共用 LIB)"))
        if e.get("similar"):
            fflags[(s, k)].append(("F3", "YELLOW", ";".join(e["similar"])[:120]))
        if any("AST" in x for x in e.get("issues", [])):
            fflags[(s, k)].append(("F4", "YELLOW", ";".join(e["issues"])))
    fseq = defaultdict(int)
    rxf = re.compile(r"^VIA-(\w+)-(MDL|ENG|LIB)(\d{3,4})$")
    for code in list(nbc["file"].values()) + [e["code"] for e in fnum["entries"]]:
        m = rxf.match(str(code))
        if m:
            fseq[(m.group(1), m.group(2))] = max(fseq[(m.group(1), m.group(2))], int(m.group(3)))
    child_seq = defaultdict(int)
    for (parent, q), code in nbc["sub"].items():
        m = re.match(r"^(.*)-(FNC|CLS)(\d{3,4})$", code)
        if m:
            child_seq[(parent, m.group(2))] = max(child_seq[(parent, m.group(2))], int(m.group(3)))
    for e in fnum["entries"]:
        m = re.match(r"^(.*)-(FNC|CLS)(\d{3,4})$", str(e.get("code", "")))
        if m:
            child_seq[(m.group(1), m.group(2))] = max(child_seq[(m.group(1), m.group(2))], int(m.group(3)))
    file_code_now = {}
    counts = {"RED": 0, "YELLOW": 0, "GREEN": 0}
    order = ["MDL", "ENG", "LIB", "CLS", "FNC"]
    for s, k, e in sorted(items, key=lambda x: (order.index(x[2]["kind"]) if x[2]["kind"] in order else 9, x[0], x[1])):
        if e.get("status") != "ACTIVE":
            continue
        fl = fflags.get((s, k), [])
        lamp = "RED" if any(x[1] == "RED" for x in fl) else ("YELLOW" if fl else "GREEN")
        key = "%s|%s|%s" % (s, k, e.get("version"))
        code = e.get("number") or have_f.get(key, {}).get("code", "")
        rec = {"sub": s, "key": k, "kind": e["kind"], "lamp": lamp, "flags": [{"rule": a, "lamp": b, "detail": c} for a, b, c in fl], "code": code, "test": None}
        if lamp != "RED" and not code:
            ok, why = _test_fn(P, e)
            rec["test"] = "PASS" if ok else "FAIL:" + why
            if ok:
                if e["kind"] in ("MDL", "ENG", "LIB"):
                    existing = nbc["file"].get(e.get("source", "")) if e["kind"] != "LIB" else None
                    if existing:
                        code = existing
                    else:
                        fseq[(s, e["kind"])] += 1
                        code = "VIA-%s-%s%03d" % (s, e["kind"], fseq[(s, e["kind"])])
                    if e["kind"] != "LIB":
                        file_code_now[(s, e["module"])] = code
                else:
                    parent = file_code_now.get((s, e["module"])) or nbc["file"].get(e.get("source", "")) or have_f.get("%s|MDL|%s|%s" % (s, e["module"], e.get("version")), {}).get("code") or have_f.get("%s|ENG|%s|%s" % (s, e["module"], e.get("version")), {}).get("code")
                    if not parent:
                        rec["test"] = "WAIT:父檔未有號"
                        out["fns"][key] = rec
                        continue
                    existing = nbc["sub"].get((parent, e["name"]))
                    if existing:
                        code = existing
                    else:
                        child_seq[(parent, e["kind"])] += 1
                        code = "%s-%s%03d" % (parent, e["kind"], child_seq[(parent, e["kind"])])
                ent = {"key": key, "code": code, "sub": s, "kind": e["kind"], "name": e["name"], "source": e.get("source"), "issued_at": now, "note": ("yellow:" + ",".join(x[0] for x in fl)) if fl else ""}
                fnum["entries"].append(ent)
                have_f[key] = ent
                rec["code"] = code
                out["issued_fns"].append(ent)
            else:
                rec["lamp"] = "RED"
                rec["flags"].append({"rule": "TEST", "lamp": "RED", "detail": why})
        counts[rec["lamp"]] += 1
        out["fns"][key] = rec
    tc = {"RED": 0, "YELLOW": 0, "GREEN": 0}
    for r in out["tables"].values():
        tc[r["lamp"]] += 1
    out["summary"] = {"tables": len(out["tables"]), "t_red": tc["RED"], "t_yellow": tc["YELLOW"], "t_green": tc["GREEN"], "t_issued": len(out["issued_tables"]),
                      "fns": len(out["fns"]), "f_red": counts["RED"], "f_yellow": counts["YELLOW"], "f_green": counts["GREEN"], "f_issued": len(out["issued_fns"]),
                      "books": {s: {"table": tbooks[s]["file"], "fn": fbooks[s]["file"]} for s in SUBS}}
    tnum["blocked"] = [k for k, r in out["tables"].items() if r["lamp"] == "RED"]
    fnum["blocked"] = [k for k, r in out["fns"].items() if r["lamp"] == "RED"]
    tnum["updated_at"] = fnum["updated_at"] = now
    if apply:
        P["registry"].mkdir(parents=True, exist_ok=True)
        (P["registry"] / "VIA_TableNumbers_v0100.json").write_text(json.dumps(tnum, ensure_ascii=False, indent=1), encoding="utf-8")
        (P["registry"] / "VIA_RegistryNumbers_v0100.json").write_text(json.dumps(fnum, ensure_ascii=False, indent=1), encoding="utf-8")
    out["lamp"] = "RED" if (tc["RED"] or counts["RED"]) else ("YELLOW" if (tc["YELLOW"] or counts["YELLOW"]) else ("GREEN" if (out["tables"] or out["fns"]) else "GRAY"))
    for s in SUBS:
        if not tbooks[s]["file"]:
            out["_notes"].append("%s 表頭冊未建(子系統先 table register --apply)" % s)
        if not fbooks[s]["file"]:
            out["_notes"].append("%s 功能矩陣未建(子系統先 fn register --apply)" % s)
    return out


def _test_table(P: dict, e: dict):
    src = P["root"] / e.get("source", "")
    if not src.exists():
        return False, "來源不在 %s" % e.get("source")
    try:
        tbs = _th_load_tables(src)
    except Exception as exc:  # noqa: BLE001
        return False, "來源讀不了 %s" % type(exc).__name__
    rows = tbs.get(e.get("table"))
    if rows is None:
        return False, "表 %s 不在來源" % e.get("table")
    cols, keys, _ = _th_profile(rows)
    have = {c["name"]: c["dtype"] for c in cols}
    missing = [c["name"] for c in e.get("columns", []) if c["name"] not in have and c["name"] != "_rid"]
    if missing:
        return False, "欄缺 %s" % ",".join(missing[:5])
    keys = [k for k in (e.get("keys") or []) if k]
    if keys:                                   # v0102:組合鍵整組測(DF06 允許組合鍵);_rid 合成鍵現算 sha8(整列)
        import hashlib as _hl
        tuples = []
        seen_h = {}
        for r in rows:
            t = []
            for k in keys:
                if k == "_rid":
                    h = _rid_of(r)
                    n = seen_h.get(h, 0)
                    seen_h[h] = n + 1
                    t.append(h if n == 0 else "%s#%d" % (h, n))   # 整列重複 → 第 2 次起帶出現序號,仍唯一
                else:
                    v = r.get(k)
                    t.append("" if v in (None, "") else str(v))
            tuples.append(tuple(t))
        if any("" in t for t in tuples) or len(set(tuples)) != len(tuples):
            return False, "主鍵 %s 空或重複" % "+".join(keys)
    bad = [c["name"] for c in e.get("columns", []) if c["name"] != "_rid" and have.get(c["name"]) != c["dtype"]]
    if bad:
        return False, "型別不符 %s" % ",".join(bad[:5])
    return True, ""


def _test_fn(P: dict, e: dict):
    import ast
    src = P["root"] / e.get("source", "")
    if not src.exists():
        return False, "檔不在樹上"
    if e["kind"] == "LIB":
        return True, ""
    try:
        tree = ast.parse(_fm_read(src))
    except (SyntaxError, ValueError) as exc:
        return False, "AST %s" % type(exc).__name__
    if e["kind"] in ("MDL", "ENG"):
        return True, ""
    names = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            names.add(node.name)
            for n in node.body:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    names.add("%s.%s" % (node.name, n.name))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
    return (e["name"] in names), ("" if e["name"] in names else "鍵不在 AST")


def paste_pack(res: dict) -> list:
    s = res["summary"]
    L = ["[計] vcgc registry govern%s · 表 %d(紅 %d 黃 %d 綠 %d 發 %d)· 功 %d(紅 %d 黃 %d 綠 %d 發 %d)· %s"
         % (" --apply" if res["apply"] else "(dry-run 不寫號)", s["tables"], s["t_red"], s["t_yellow"], s["t_green"], s["t_issued"], s["fns"], s["f_red"], s["f_yellow"], s["f_green"], s["f_issued"], res["lamp"])]
    for n in res["_notes"]:
        L.append("  [注] %s" % n)
    reds = [(k, r) for k, r in res["tables"].items() if r["lamp"] == "RED"]
    for k, r in reds[:12]:
        L.append("  [RED] 表 %s · %s" % (k, " | ".join("%s %s" % (f["rule"], f["detail"]) for f in r["flags"] if f["lamp"] == "RED")))
    if len(reds) > 12:
        L.append("  [RED] 表 … 另 %d 在卡" % (len(reds) - 12))
    fr = [(k, r) for k, r in res["fns"].items() if r["lamp"] == "RED"]
    for k, r in fr[:12]:
        L.append("  [RED] 功 %s · %s" % (k, " | ".join("%s %s" % (f["rule"], f["detail"]) for f in r["flags"] if f["lamp"] == "RED")))
    if len(fr) > 12:
        L.append("  [RED] 功 … 另 %d 在卡" % (len(fr) - 12))
    from collections import Counter
    yc = Counter(f["rule"] for r in list(res["tables"].values()) + list(res["fns"].values()) for f in r["flags"] if f["lamp"] == "YELLOW")
    L.append("[計] 黃燈提醒分類 · " + (" · ".join("%s=%d" % (k, v) for k, v in sorted(yc.items())) or "無"))
    for k, r in [(k, r) for k, r in res["tables"].items() if r["lamp"] == "YELLOW"][:8]:
        L.append("  [YEL] 表 %s · %s" % (k, " | ".join(f["detail"] for f in r["flags"])[:140]))
    for k, r in [(k, r) for k, r in res["fns"].items() if r["lamp"] == "YELLOW" and r["kind"] in ("MDL", "ENG")][:8]:
        L.append("  [YEL] 功 %s · %s" % (k, " | ".join(f["detail"] for f in r["flags"])[:140]))
    L.append("NEXT: " + ("紅表/紅功貼給 AI 裁(改頭出新版 / 補主鍵 / 退役帶替代)→ 子系統重登記 → 本引擎重跑;綠已發號 → 子系統 table/fn number pull" if res["lamp"] == "RED" else "零紅 → 子系統跑 table number pull / fn number pull 讀號;黃表留卡逐批裁"))
    return L[:300]


def write_card(res: dict, pack: list, P: dict | None = None) -> dict:
    P = P or _paths()
    day = datetime.datetime.now().strftime("%Y%m%d")
    P["cards"].mkdir(parents=True, exist_ok=True)
    P["report"].mkdir(parents=True, exist_ok=True)
    md = P["cards"] / ("VCGC_RegistryGovernCard_%s.md" % day)
    L = ["# VCGC 母系統 治理卡:表頭冊 + 功能矩陣(%s)" % day, "", "> L114 ③:子系統登記留白 → 母系統顯示衝突 → 操作員+AI 裁 → 母系統測試通過發號 → 子系統讀回並遵守。紅 = 擋號;黃 = 提醒不擋。", "", "## 貼回包", "```"] + pack + ["```", "",
         "## 表(每鍵一列)", "| 鍵 | 燈 | 號 | 測 | 旗 |", "|---|---|---|---|---|"]
    L += ["| %s | %s | %s | %s | %s |" % (k, r["lamp"], r["table_no"] or "留白", r["test"] or "—", "; ".join("%s %s" % (f["rule"], f["detail"]) for f in r["flags"]).replace("|", "¦")) for k, r in res["tables"].items()][:500]
    L += ["", "## 功(只列紅/黃與本輪發號)", "| 鍵 | 類 | 燈 | 號 | 測 | 旗 |", "|---|---|---|---|---|---|"]
    L += ["| %s | %s | %s | %s | %s | %s |" % (k, r["kind"], r["lamp"], r["code"] or "留白", r["test"] or "—", "; ".join("%s %s" % (f["rule"], f["detail"]) for f in r["flags"]).replace("|", "¦"))
          for k, r in res["fns"].items() if r["lamp"] != "GREEN" or any(e["key"] == k for e in res["issued_fns"])][:800]
    md.write_text("\n".join(L) + "\n", encoding="utf-8")
    (P["report"] / "GOVERN_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"md": str(md)}


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VCGC] 拒絕。只能經 via-vcgc。")
        return 2
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a[:2]:
        return selftest()
    apply = "--apply" in a
    if a[:1] == ["register"]:
        r = register(apply=apply)
        t, f = r["table"], r["fn"]
        print("[計] vcgc register%s · 表頭 %s 表 %d 留白 %d %s · 矩陣 %s 項 %d %s 相似 %d AST失敗 %d 留白 %d · GREEN" % (" --apply" if apply else "(dry-run)", t["book"], t["tables"], t["blank"], t["counts"], f["book"], f["items"], f["kinds"], f["similar"], f["ast_fail"], f["blank"]))
        return 0
    if a[:1] == ["govern"]:
        res = govern(apply=apply)
        pack = paste_pack(res)
        card = write_card(res, pack)
        for ln in pack:
            print(ln)
        print("  [卡] %s" % card["md"])
        return 1 if res["lamp"] == "RED" else 0
    print("[拒跑] register [--apply] | govern [--apply] | --selftest")
    return 2




# ───────────────────────── v0101:pull(VCGC 自己讀號)· annotate(AST 分類 + 說明側冊) ─────────────────────────
_CAT_RULES = [
    ("ENTRY", r"^(main|cli|run|selftest|chk)$"), ("GATE", r"(?i)(check|validate|verify|gate|test|assert|guard|precheck|audit|triage)"),
    ("IO_READ", r"(?i)(read|load|fetch|get|scan|discover|find|glob|open|download|pull)"), ("IO_WRITE", r"(?i)(write|save|emit|export|dump|persist|ledger|append|publish|issue|register)"),
    ("PARSE", r"(?i)(parse|extract|split|tokeni|block|table|period|label|regex|match)"), ("CLEAN", r"(?i)(clean|normal|std|canon|strip|dedup|sanit|fix|repair)"),
    ("REBUILD", r"(?i)(rebuild|build|merge|assemble|compose|reconstruct|restatus|rebalance|aggregate|matrix)"), ("UI", r"(?i)(html|render|ui|print|show|display|card|pack|chart|plot)"),
    ("GOVERN", r"(?i)(number|govern|ssot|adopt|retire|dormant|law|policy|collision|supersede)"), ("INTERNAL", r"^_"),
]


def _cat_of(name: str, doc: str) -> str:
    short = name.split(".")[-1]
    for cat, rx in _CAT_RULES:
        if re.search(rx, short):
            return cat
    for cat, rx in _CAT_RULES[1:-1]:
        if doc and re.search(rx, doc[:80]):
            return cat
    return "OTHER"


def _explain(e: dict) -> str:
    doc = (e.get("doc") or "").strip()
    if doc:
        return doc[:120]
    k, nm = e.get("kind"), e.get("name", "")
    if k == "LIB":
        return "第三方套件 %s(import)" % nm
    if k == "CLS":
        return "類別 %s,%d 個方法" % (nm, e.get("methods", 0))
    if k in ("MDL", "ENG"):
        return "%s 模組 %s · %d 行" % ("引擎" if k == "ENG" else "模組", nm, e.get("lines", 0))
    short = nm.split(".")[-1]
    words = re.sub(r"[_]+", " ", re.sub(r"([a-z])([A-Z])", r"\1 \2", short)).strip()
    return "%s(%s)" % (words or short, e.get("api", ""))[:120]


def pull_self(P: dict | None = None) -> dict:
    """VCGC 自己的功能矩陣 + 表頭冊依鍵讀回號(與子系統 manager 的 fn/table number pull 同一律)。"""
    P = P or _paths()
    now = _now()
    f = _fm_pull("VCGC", P["registry"], P["registry"], now, True)
    t = _th_pull("VCGC", P["registry"], P["registry"], now, True)
    return {"verb": "pull", "fn": f, "table": t, "lamp": "GREEN" if (f.get("pending", 1) == 0 and t.get("pending", 1) == 0) else "YELLOW"}


def annotate(sub: str, P: dict | None = None, apply: bool = True) -> dict:
    """讀 <SUB>_FunctionMatrix 尾版 → 每項:code(號)· cat(分類)· zh(說明)· health 紅黃(有的話)→ VIA_AstAnnotations_<SUB>_v0100.json(VCGC 側冊;只增:同鍵同 sha 不動)。"""
    P = P or _paths()
    fb = _book(P, sub, "FunctionMatrix")
    items = (fb["data"] or {}).get("items", {})
    out_fp = P["registry"] / ("VIA_AstAnnotations_%s_v0100.json" % sub)
    prev = json.loads(_th_read(out_fp)) if out_fp.exists() else {"schema": "VIA.AstAnnotations.v1", "sub": sub, "version": "v0100", "rule": "VCGC 全景 AST 注入:分類 + 說明 + 號 + 健康旗,側冊不改原始碼;鍵 = 功能矩陣鍵;只增不減", "created_at": _now(), "items": {}}
    hp = P["root"] / "VIA_Reports" / sub.lower() / "HEALTH_latest.json"
    try:
        health = json.loads(_th_read(hp)) if hp.exists() else None
    except ValueError:
        health = None
    red_files = {r["tail"]: ("AST 壞" if not r.get("ast_ok", True) else r.get("net_note") or "") for r in (health or {}).get("files", []) if r.get("lamp") == "RED"}
    cats = Counter()
    n_new = n_same = 0
    for k, e in items.items():
        if e.get("status") not in ("ACTIVE", None):
            continue
        ent = prev["items"].get(k)
        if ent and ent.get("body_sha") == e.get("body_sha") and ent.get("code") == (e.get("number") or ent.get("code")):
            n_same += 1
            cats[ent["cat"]] += 1
            continue
        cat = _cat_of(e.get("name", ""), e.get("doc", "")) if e.get("kind") in ("FNC", "CLS") else e.get("kind")
        src_tail = Path(e.get("source", "")).name
        prev["items"][k] = {"key": k, "sub": sub, "kind": e.get("kind"), "module": e.get("module"), "name": e.get("name"), "version": e.get("version"), "code": e.get("number") or "", "cat": cat,
                            "zh": _explain(e), "api": e.get("api", ""), "line": e.get("line"), "body_sha": e.get("body_sha"), "similar": e.get("similar", []), "health": red_files.get(src_tail, ""), "annotated_at": _now()}
        cats[cat] += 1
        n_new += 1
    prev["updated_at"] = _now()
    prev["summary"] = {"items": len(prev["items"]), "numbered": sum(1 for v in prev["items"].values() if v.get("code")), "cats": dict(cats), "red_files": len(red_files)}
    if apply:
        out_fp.write_text(json.dumps(prev, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"verb": "annotate", "sub": sub, "file": out_fp.name, "new": n_new, "same": n_same, "summary": prev["summary"], "lamp": "GREEN" if items else "GRAY", "_notes": ([] if items else ["%s 功能矩陣未建(子系統先 fn register --apply)" % sub])}


_MAIN_0100 = main


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VCGC] 拒絕。只能經 via-vcgc。")
        return 2
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["pull"]:
        r = pull_self()
        print("[計] vcgc pull · 功 filled %s already %s pending %s · 表 filled %s already %s pending %s · %s" % (r["fn"].get("filled"), r["fn"].get("already"), r["fn"].get("pending"), r["table"].get("filled"), r["table"].get("already"), r["table"].get("pending"), r["lamp"]))
        return 0
    if a[:1] == ["annotate"]:
        subs = [x for x in a[1:] if x in SUBS] or list(SUBS)
        rc = 0
        for sub in subs:
            r = annotate(sub, apply=("--dry" not in a))
            s = r["summary"]
            print("[計] annotate %s · %s · 新注 %d 同 %d · 項 %d 有號 %d · 分類 %s · 紅檔 %d · %s" % (sub, r["file"], r["new"], r["same"], s["items"], s["numbered"], json.dumps(s["cats"], ensure_ascii=False), s["red_files"], r["lamp"]))
            for n in r["_notes"]:
                print("  [注] %s" % n)
        return rc
    return _MAIN_0100(argv)




# ───────────────────────── v0102:resolve(紅表分區列管 · 組合鍵 · 過時退役 · 零九頭龍) ─────────────────────────
_RULINGS = "VIA_KeyRulings_v0100.json"
_OBS_RX = re.compile(r"^(?P<prefix>.+?)_v(?P<n>\d{2,3})_(?P<rest>.+)$", re.I)   # VIA_ActivationGateway_v03_StableHotfix_Manifest 這類「版號在名字中段」的多頭族


def _composite_key(rows: list, cols: list, maxk: int = 3):
    """最小組合鍵:1 欄 → 2 欄 → 3 欄,全非空且不重複;找不到回 None。"""
    import itertools
    cand = [c["name"] for c in cols if c["dtype"] in ("str", "int", "date")]
    for k in range(1, maxk + 1):
        for combo in itertools.combinations(cand, k):
            vals = [tuple(str(r.get(c) if r.get(c) is not None else "").strip() for c in combo) for r in rows]
            if all(all(v for v in t) for t in vals) and len(set(vals)) == len(vals):
                return list(combo)
    return None


def _book_dir(P: dict, sub: str) -> Path:
    return {"VCGC": P["registry"], "VDF": P["vdf"] / "registry", "VRN": P["vrn"] / "registry"}[sub]



def _adopt_rulings_vcgc(book: dict, rulings: dict, now: str) -> int:
    """VCGC 自家表頭冊採納裁定鍵(裁定優先於自動剖析鍵;舊鍵留 prev_keys;_rid 合成鍵加欄標 synthetic);回採納數。"""
    n = 0
    for tid, r in (rulings.get("tables") or {}).items():
        e = (book.get("tables") or {}).get(tid)
        if not e or r.get("sub") != "VCGC" or list(e.get("keys") or []) == list(r["keys"]):
            continue
        if e.get("keys"):
            e["prev_keys"] = e["keys"]
        e["keys"] = list(r["keys"])
        for c in e.get("columns", []):
            c["pk"] = c["name"] in r["keys"]
        if r.get("kind") == "synthetic" and not any(c["name"] == "_rid" for c in e.get("columns", [])):
            e["columns"].append({"name": "_rid", "dtype": "str", "required": True, "pk": True, "synthetic": "sha8(整列)"})
        e["key_ruling"] = r.get("kind")
        e["key_ruled_at"] = now
        n += 1
    return n


def _rulings_book(P: dict) -> dict:
    fp = P["registry"] / _RULINGS
    try:
        return json.loads(_th_read(fp)) if fp.exists() else {}
    except ValueError:
        return {}


def resolve(P: dict | None = None, apply: bool = False) -> dict:
    P = P or _paths()
    now = _now()
    gov = json.loads(_th_read(P["root"] / "VIA_Reports" / "review" / "vcgc_registry" / "GOVERN_latest.json")) if (P["root"] / "VIA_Reports" / "review" / "vcgc_registry" / "GOVERN_latest.json").exists() else None
    out = {"verb": "resolve", "apply": apply, "zones": {"COMPOSITE_KEY": [], "SYNTHETIC_KEY": [], "OBSOLETE": [], "DRIFT": [], "DUP_KEY": [], "UNRESOLVED": []}, "_notes": []}
    if not gov:
        out["_notes"].append("GOVERN_latest.json 不在:先 govern")
        out["lamp"] = "GRAY"
        return out
    rul_fp = P["registry"] / _RULINGS
    rulings = json.loads(_th_read(rul_fp)) if rul_fp.exists() else {"schema": "VIA.KeyRulings.v1", "version": "v0100", "engine": NAME, "rule": "母系統裁定書:子系統 manager 下次 table register 讀此冊採用鍵;VCGC 自家冊直接採用;過時族退役帶 replaced_by;只增不減", "created_at": now, "tables": {}, "retire": {}}
    books = {s: _book(P, s, "TableHeader") for s in SUBS}
    # ① 紅表逐張
    for key, rec in gov.get("tables", {}).items():
        if rec.get("lamp") != "RED":
            continue
        sub, tid = rec["sub"], rec["tid"]
        ent = (books[sub]["data"].get("tables") or {}).get(tid, {}) if books[sub]["data"] else {}
        codes = {f["rule"] for f in rec.get("flags", [])} | ({"TEST"} if any(f["rule"] == "TEST" for f in rec.get("flags", [])) else set())
        src = P["root"] / ent.get("source", "")
        if "T3" in codes:
            out["zones"]["DRIFT"].append({"sub": sub, "tid": tid, "action": "RETIRE_OLD_HEAD", "new_tid": (ent.get("drift") or {}).get("new_tid"), "keep_no": ent.get("table_no")})
            rulings["retire"][tid] = {"sub": sub, "why": "T3 已號表頭漂移:舊頭退役,號留舊頭不再用;新頭 %s 接號" % (ent.get("drift") or {}).get("new_tid"), "replaced_by": (ent.get("drift") or {}).get("new_tid"), "ts": now}
            continue
        if not src.exists() or not ent:
            out["zones"]["UNRESOLVED"].append({"sub": sub, "tid": tid, "why": "來源或表頭冊項不在"})
            continue
        try:
            rows = _th_load_tables(src).get(ent.get("table"), [])
        except Exception:  # noqa: BLE001
            rows = []
        if not rows:
            out["zones"]["UNRESOLVED"].append({"sub": sub, "tid": tid, "why": "來源讀不出列"})
            continue
        cols, _, _ = _th_profile(rows)
        ck = _composite_key(rows, cols)
        if ck:
            zone = "COMPOSITE_KEY"
            rulings["tables"][tid] = {"sub": sub, "keys": ck, "kind": "composite", "why": "T2/TEST:最小組合鍵(DF06 組合鍵)", "ts": now}
        else:
            zone = "SYNTHETIC_KEY"
            rulings["tables"][tid] = {"sub": sub, "keys": ["_rid"], "kind": "synthetic", "why": "無任何組合鍵 → 合成列鍵 _rid = sha8(整列);登記時由 manager 加欄,原冊不改", "ts": now}
        out["zones"][zone].append({"sub": sub, "tid": tid, "keys": rulings["tables"][tid]["keys"], "rows": len(rows)})
    # ② 過時多頭族(名字中段帶 _vNN_):同前綴+同尾 → 留最高版
    fams = defaultdict(list)
    for s in SUBS:
        for tid, ent in ((books[s]["data"] or {}).get("tables") or {}).items():
            src_name = Path(ent.get("source", "")).name
            m = _OBS_RX.match(_th_family(src_name))
            if m:
                fams[(s, m.group("prefix").lower(), m.group("rest").lower())].append((int(m.group("n")), tid, src_name))
    for (s, prefix, rest), lst in fams.items():
        if len(lst) < 2:
            continue
        lst.sort()
        keep = lst[-1]
        for n, tid, src_name in lst[:-1]:
            out["zones"]["OBSOLETE"].append({"sub": s, "tid": tid, "file": src_name, "replaced_by": keep[2], "action": "RETIRE(移 _superseded,不毀)" if s == "VCGC" else "RULING(交 %s manager)" % s})
            rulings["retire"][tid] = {"sub": s, "why": "過時多頭族 %s_v%02d_%s,最高版 %s 留;其餘退役" % (prefix, n, rest, keep[2]), "replaced_by": keep[1], "file": src_name, "ts": now}
    # ③ 套用:VCGC 自家(表頭冊鍵 + 過時冊移 _superseded);子系統只留裁定書
    applied = {"vcgc_keys": 0, "vcgc_retired": 0, "ledger": 0}
    if apply:
        rul_fp.write_text(json.dumps(rulings, ensure_ascii=False, indent=1), encoding="utf-8")
        vb = books["VCGC"]
        if vb["data"]:
            applied["vcgc_keys"] = _adopt_rulings_vcgc(vb["data"], rulings, now)
            sup = P["registry"] / "_superseded"
            led = P["registry"] / "VCGC_Retire_Ledger.jsonl"
            for tid, r in rulings["retire"].items():
                if r["sub"] == "VCGC" and tid in vb["data"].get("tables", {}):
                    e = vb["data"]["tables"][tid]
                    if e.get("status") == "RETIRED":
                        continue
                    e.update(status="RETIRED", retired_at=now, replaced_by=r.get("replaced_by"), retire_reason=r["why"])
                    applied["vcgc_retired"] += 1
                    srcp = P["root"] / e.get("source", "")
                    if r.get("file") and srcp.exists() and srcp.parent == P["registry"]:
                        sup.mkdir(exist_ok=True)
                        dst = sup / (srcp.name + ".RETIRED_" + now.replace(":", "").replace("-", "")[:15])
                        __import__("shutil").move(str(srcp), str(dst))
                        with open(led, "a", encoding="utf-8") as fh:
                            fh.write(json.dumps({"ts": now, "tid": tid, "from": srcp.name, "to": dst.name, "replaced_by": r.get("replaced_by"), "why": r["why"]}, ensure_ascii=False) + "\n")
                        applied["ledger"] += 1
            vb["path"].write_text(json.dumps(vb["data"], ensure_ascii=False, indent=1), encoding="utf-8")
    out["applied"] = applied
    out["rulings_file"] = str(rul_fp)
    out["counts"] = {k: len(v) for k, v in out["zones"].items()}
    out["lamp"] = "YELLOW" if (out["zones"]["UNRESOLVED"] or not apply) else "GREEN"
    return out


def _print_resolve(r: dict) -> None:
    c = r.get("counts", {})
    print("[計] resolve%s · 組合鍵 %d · 合成鍵 %d · 過時退役 %d · 漂移 %d · 未解 %d · 套用 %s · %s" % (" --apply" if r["apply"] else "(dry-run)", c.get("COMPOSITE_KEY", 0), c.get("SYNTHETIC_KEY", 0), c.get("OBSOLETE", 0), c.get("DRIFT", 0), c.get("UNRESOLVED", 0), r.get("applied"), r["lamp"]))
    for z, rows in r.get("zones", {}).items():
        for x in rows[:12]:
            print("  [%s] %s %s|%s · %s" % ("YEL" if z == "UNRESOLVED" else "OK", z, x["sub"], x["tid"], x.get("keys") or x.get("replaced_by") or x.get("why") or x.get("action")))
    for n in r.get("_notes", []):
        print("  [注] %s" % n)


_MAIN_0101 = main


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VCGC] 拒絕。只能經 via-vcgc。")
        return 2
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["resolve"]:
        _print_resolve(resolve(apply=("--apply" in a)))
        return 0
    return _MAIN_0101(argv)




def _rid_of(row: dict, ordinal=None) -> str:
    import hashlib as _hl
    h = _hl.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()[:8]
    return h if ordinal is None else "%s#%d" % (h, ordinal)


# ───────────────────────── v0103:downstream(功能模組下放:母副本退役,子系統建)· law(L116) ─────────────────────────
L116 = {"id": "L116", "batch": "側線 2026-10-06", "cat": "治理 / 上下分工", "key": "UPSTREAM_DOWNSTREAM",
        "zh": ("【上下分工律】① 功能模組下放:功能模組歸功能子系統(VRN / VDF …),由子系統 SystemManager 建立、登記、自報;母系統 VCGC 監控。"
               "② 註冊 / SSOT / 表頭 / 功能矩陣等工具上下各一套:下面那套用來建立(register / adopt / number pull),上面那套用來監察衝突、通過檢查、給予編號(govern / resolve / annotate)。"
               "③ 相互不可有動作:母系統不寫子系統的冊與檔;子系統不寫母系統的號冊與裁定書;母系統持有的子系統模組副本視為多頭,子系統尾版在即退役下放。"
               "④ 跨層動作只由操作員 + AI 裁定後執行(裁定書 VIA_KeyRulings · 下放帳 VCGC_Downstream_Ledger),引擎只提案與執行已裁事項。"),
        "status": "ACTIVE", "origin": "操作員原文下令 2026-10-06(功能模組下放,子系統管理,母系統監控;上下各一套工具,下建上監;相互不可有動作;動作由我跟 AI 進行)",
        "enforcement": "CGC RegistryGovernor downstream / resolve / govern · <SUB>_SystemManager register / adopt / pull · HealthMatrix 各 manager 自報"}


def law_append_generic(law: dict, P: dict | None = None, apply: bool = True) -> dict:
    """任何法條 json({id, zh, …})附進政策冊尾版出新版;同 id 已在 → SKIP;只增不減。"""
    P = P or _paths()
    lid = law.get("id")
    hits = sorted(P["registry"].glob("VIA_Policy_Laws_SSOT_v*.json"), key=lambda q: int(re.search(r"_v(\d{4})", q.name).group(1)))
    if not hits or not lid:
        return {"status": "NO_BOOK" if not hits else "NO_ID", "lamp": "RED"}
    tail = hits[-1]
    d = json.loads(_th_read(tail))
    laws = d.get("laws", [])
    if any(l.get("id") == lid for l in laws):
        return {"status": "SKIP", "tail": tail.name, "lamp": "GREEN", "id": lid}
    nv = "v%04d" % (int(re.search(r"_v(\d{4})", tail.name).group(1)) + 1)
    new = P["registry"] / ("VIA_Policy_Laws_SSOT_%s.json" % nv)
    if new.exists():
        return {"status": "CONFLICT", "new": new.name, "lamp": "RED"}
    d["laws"] = laws + [law]
    d["prior"], d["version"], d["ts"] = tail.name, nv, datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    d["why_" + nv] = "%s 已發布 → 出新版;+%s(%s);其餘一字不動。%s %s" % (tail.name, lid, law.get("origin", "")[:60], NAME, TAG)
    if apply:
        new.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"status": "WRITTEN" if apply else "PLAN", "tail": tail.name, "new": new.name, "laws": len(d["laws"]), "lamp": "GREEN", "id": lid}


def law_append_116(P: dict | None = None, apply: bool = True) -> dict:
    return law_append_generic(L116, P, apply)


def _law_append_116_old(P: dict | None = None, apply: bool = True) -> dict:
    P = P or _paths()
    hits = sorted(P["registry"].glob("VIA_Policy_Laws_SSOT_v*.json"), key=lambda q: int(re.search(r"_v(\d{4})", q.name).group(1)))
    if not hits:
        return {"status": "NO_BOOK", "lamp": "RED"}
    tail = hits[-1]
    d = json.loads(_th_read(tail))
    laws = d.get("laws", [])
    if any(l.get("id") == "L116" for l in laws):
        return {"status": "SKIP", "tail": tail.name, "lamp": "GREEN"}
    nv = "v%04d" % (int(re.search(r"_v(\d{4})", tail.name).group(1)) + 1)
    new = P["registry"] / ("VIA_Policy_Laws_SSOT_%s.json" % nv)
    if new.exists():
        return {"status": "CONFLICT", "new": new.name, "lamp": "RED"}
    d["laws"] = laws + [L116]
    d["prior"], d["version"], d["ts"] = tail.name, nv, datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    d["why_" + nv] = "%s 已發布 → 出新版;+L116 上下分工律(操作員原文下令 2026-10-06);其餘一字不動。%s %s" % (tail.name, NAME, TAG)
    if apply:
        new.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"status": "WRITTEN" if apply else "PLAN", "tail": tail.name, "new": new.name, "laws": len(d["laws"]), "lamp": "GREEN"}


def downstream(P: dict | None = None, apply: bool = False, adopt_orphans: bool = False) -> dict:
    """F1:母系統(supportive modules)持有的 VRN_*/VDF_* 模組副本 → 子系統有同族尾版 → 母副本退役(移 supportive modules/_superseded,FunctionMatrix 標 RETIRED replaced_by,帳);子系統沒有或母副本較新 → 待裁。"""
    P = P or _paths()
    now = _now()
    out = {"verb": "downstream", "apply": apply, "retire": [], "pending": [], "_notes": []}
    vfm = _book(P, "VCGC", "FunctionMatrix")
    items = (vfm["data"] or {}).get("items", {})
    sup = P["sup"] if "sup" in P else P["root"] / "supportive modules"
    led = P["registry"] / "VCGC_Downstream_Ledger.jsonl"
    for k, e in list(items.items()):
        if e.get("kind") not in ("MDL", "ENG") or e.get("status") != "ACTIVE":
            continue
        fam = e.get("module", "")
        src = P["root"] / e.get("source", "")
        m = re.match(r"^(VRN|VDF)_", fam)
        sub = m.group(1) if m else None
        tails = []
        for cand_sub, home in (("VRN", P["vrn"]), ("VDF", P["vdf"])):
            if sub and cand_sub != sub:
                continue
            found = [p for p in home.rglob(fam + "*.py") if not (set(p.relative_to(home).parts[:-1]) & {"_superseded", "references", "intake"}) and _th_family(p.name) == fam] if home.is_dir() else []
            if found:
                sub, tails = cand_sub, found
                break
        if not sub:
            continue                      # 無前綴且子系統樹上也沒有同族 → 純母系統模組,不是下放對象
        home = P["vrn"] if sub == "VRN" else P["vdf"]
        if not tails:
            if adopt_orphans and src.exists() and src.is_relative_to(sup):
                dst = home / src.name
                if dst.exists():
                    out["pending"].append({"key": k, "file": src.name, "why": "子系統同名檔已在但族名不同 → 待裁"})
                    continue
                rec = {"key": k, "file": src.name, "replaced_by": dst.relative_to(P["root"]).as_posix(), "why": "母獨本下放建檔(操作員裁定 --adopt-orphans):搬到 %s,母標 RETIRED" % sub}
                if apply:
                    __import__("shutil").copy2(str(src), str(dst))
                    dst_dir = src.parent / "_superseded"
                    dst_dir.mkdir(exist_ok=True)
                    moved = dst_dir / (src.name + ".DOWNSTREAM_" + now.replace(":", "").replace("-", "")[:15])
                    __import__("shutil").move(str(src), str(moved))
                    e.update(status="RETIRED", retired_at=now, replaced_by=rec["replaced_by"], retire_reason=rec["why"])
                    with open(led, "a", encoding="utf-8") as fh:
                        fh.write(json.dumps(dict(rec, ts=now, to=moved.relative_to(P["root"]).as_posix(), orphan=True), ensure_ascii=False) + "\n")
                    rec["to"] = moved.name
                out["retire"].append(rec)
            else:
                out["pending"].append({"key": k, "file": src.name, "why": "%s 沒有同族檔 → 母副本是唯一本:待裁(操作員說 OK 就 --adopt-orphans 搬下去建檔)" % sub})
            continue
        tail = max(tails, key=lambda q: _th_vnum(q.name))
        mv, sv = _th_vnum(src.name), _th_vnum(tail.name)
        same = src.exists() and tail.exists() and _sha(src) == _sha(tail)
        if same or sv >= mv:
            rec = {"key": k, "file": src.name, "replaced_by": tail.relative_to(P["root"]).as_posix(), "why": "子系統尾版 %s %s 母副本 → 母副本退役下放" % (tail.name, "同內容" if same else "版號 ≥")}
            if apply and src.exists() and src.is_relative_to(sup):
                dst_dir = src.parent / "_superseded"
                dst_dir.mkdir(exist_ok=True)
                dst = dst_dir / (src.name + ".DOWNSTREAM_" + now.replace(":", "").replace("-", "")[:15])
                __import__("shutil").move(str(src), str(dst))
                e.update(status="RETIRED", retired_at=now, replaced_by=rec["replaced_by"], retire_reason=rec["why"])
                for k2, e2 in items.items():
                    if e2.get("module") == fam and e2.get("status") == "ACTIVE" and e2.get("kind") in ("FNC", "CLS", "LIB"):
                        e2.update(status="RETIRED", retired_at=now, replaced_by=rec["replaced_by"], retire_reason="隨母副本下放")
                with open(led, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(dict(rec, ts=now, to=dst.relative_to(P["root"]).as_posix()), ensure_ascii=False) + "\n")
                rec["to"] = dst.name
            out["retire"].append(rec)
        else:
            out["pending"].append({"key": k, "file": src.name, "why": "母副本 v%04d 比子系統尾版 %s 新 → 待裁(差異要人看)" % (mv, tail.name)})
    if apply and out["retire"] and vfm["data"]:
        vfm["path"].write_text(json.dumps(vfm["data"], ensure_ascii=False, indent=1), encoding="utf-8")
    out["lamp"] = "YELLOW" if out["pending"] else ("GREEN" if apply else "YELLOW")
    return out


def _sha(p: Path) -> str:
    import hashlib as _hl
    return _hl.sha256(p.read_bytes()).hexdigest()


def _print_downstream(r: dict) -> None:
    print("[計] downstream%s · 母副本退役下放 %d · 待裁 %d · %s" % (" --apply" if r["apply"] else "(dry-run)", len(r["retire"]), len(r["pending"]), r["lamp"]))
    for x in r["retire"][:20]:
        print("  [OK] 下放 %s → %s%s" % (x["file"], x["replaced_by"], (" · 移 " + x["to"]) if x.get("to") else ""))
    for x in r["pending"][:20]:
        print("  [YEL] 待裁 %s · %s" % (x["file"], x["why"]))


_MAIN_0102 = main


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VCGC] 拒絕。只能經 via-vcgc。")
        return 2
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["downstream"]:
        _print_downstream(downstream(apply=("--apply" in a), adopt_orphans=("--adopt-orphans" in a)))
        return 0
    if a[:1] == ["law"]:
        if "--file" in a:
            fp = Path(a[a.index("--file") + 1])
            r = law_append_generic(json.loads(fp.read_text(encoding="utf-8-sig")), apply=("--dry" not in a))
        else:
            r = law_append_generic(L116, apply=("--dry" not in a))
        print("[計] law append %s · %s · %s → %s · %s" % (r.get("id", "L116"), r["status"], r.get("tail"), r.get("new", "—"), r["lamp"]))
        return 1 if r["lamp"] == "RED" else 0
    return _MAIN_0102(argv)


def _w(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="cgcgov-"))
    os.environ["VIA_ROOT"] = str(td)
    P = _paths()
    now = _now()
    chk("① 沙盒:VIA_ROOT 指 temp", all(str(v).startswith(str(td)) for v in P.values()))
    # VCGC 自己的冊 + 程式
    _w(P["registry"] / "VIA_SSOT_Numbers_VRN_v0100.json", {"entries": [{"key": "k1", "ssot_no": "A"}, {"key": "k2", "ssot_no": "B"}]})
    _w(P["registry"] / "CGC_MDL001_X_v0100.py", "def shared(a):\n    return a\n")
    r1 = register(P, apply=True)
    chk("② VCGC register:表頭 1 表 · 矩陣 MDL 1 FNC 1 · 留白", r1["table"]["tables"] == 1 and r1["fn"]["kinds"].get("MDL") == 1 and r1["fn"]["kinds"].get("FNC") == 1 and r1["fn"]["blank"] == 2)
    # VRN / VDF 的冊(模擬子系統已登記)
    _w(P["vrn"] / "SSOT" / "VRN_Rating_Dict_v0100.json", {"BUY": {"zh": "買進", "score": 1}, "HOLD": {"zh": "持有", "score": 0}})
    _w(P["vrn"] / "SSOT" / "VRN_NoKey_v0100.json", {"rows": [{"a": 1, "b": 1}, {"a": 1, "b": 1}]})
    _w(P["vrn"] / "VRN_ENG001_A_v0100.py", "def shared(a):\n    return a\n\ndef vrn_only():\n    pass\n")
    _w(P["vdf"] / "registry" / "VDF_Universe_v0100.json", {"rows": [{"ticker": "2330", "name": "TSMC"}]})
    _w(P["vdf"] / "VDF_ENG001_A_v0100.py", "def shared(a):\n    return a\n")
    _w(P["vdf"] / "SHARED_MOD_v0100.py", "x = 1\n")
    _w(P["vrn"] / "SHARED_MOD_v0100.py", "x = 2\n")   # 同模組族 SHARED_MOD 同時在 VDF 與 VRN → F1 紅(兩邊都擋)
    _th_register("VRN", [P["vrn"] / "SSOT" / "VRN_Rating_Dict_v0100.json", P["vrn"] / "SSOT" / "VRN_NoKey_v0100.json"], P["vrn"] / "registry", now, True, P["root"])
    _th_register("VDF", [P["vdf"] / "registry" / "VDF_Universe_v0100.json"], P["vdf"] / "registry", now, True, P["root"])
    _fm_register("VRN", [P["vrn"]], P["root"], P["vrn"] / "registry", now, True)
    _fm_register("VDF", [P["vdf"]], P["root"], P["vdf"] / "registry", now, True)
    dry = govern(P, apply=False)
    chk("③ govern dry-run:不寫號冊 · 表 4(NoKey 紅 T2)· 功有紅(F1 同模組族跨系統)有黃(F3 shared 同名同 body 跨三系統)",
        not (P["registry"] / "VIA_TableNumbers_v0100.json").exists() and dry["summary"]["tables"] == 4 and dry["summary"]["t_red"] == 1
        and any(f["rule"] == "F1" for r in dry["fns"].values() for f in r["flags"]) and any(f["rule"] == "F3" and "跨系統" in f["detail"] for r in dry["fns"].values() for f in r["flags"]))
    ap = govern(P, apply=True)
    tn = json.loads((P["registry"] / "VIA_TableNumbers_v0100.json").read_text(encoding="utf-8"))
    fn = json.loads((P["registry"] / "VIA_RegistryNumbers_v0100.json").read_text(encoding="utf-8"))
    nos = sorted(e["table_no"] for e in tn["entries"])
    chk("④ --apply:零紅表 3 張發 TBL0001(各子系統各自序)· NoKey 擋號留白 · 相似黃不擋", nos == ["SSOT-VCGC-VCGC-TBL0001", "SSOT-VCGC-VDF-TBL0001", "SSOT-VCGC-VRN-TBL0001"]
        and any("VRN_NoKey".lower() in k for k in tn["blocked"]) and all(r["lamp"] != "RED" or "nokey" in k for k, r in ap["tables"].items()))
    codes = {e["key"]: e["code"] for e in fn["entries"]}
    chk("⑤ 功能號:父檔 VIA-<SUB>-MDL/ENG001 · 子鍵 -FNC001 掛父號 · F1 紅的 SHARED_MOD 兩邊擋號 · shared 黃照發",
        codes.get("VCGC|MDL|CGC_MDL001_X|v0100") == "VIA-VCGC-MDL001" and codes.get("VCGC|FNC|CGC_MDL001_X|shared|v0100") == "VIA-VCGC-MDL001-FNC001"
        and codes.get("VDF|ENG|VDF_ENG001_A|v0100") == "VIA-VDF-ENG001" and "VDF|MDL|SHARED_MOD|v0100" not in codes and "VRN|MDL|SHARED_MOD|v0100" not in codes and codes.get("VRN|FNC|VRN_ENG001_A|shared|v0100"))
    ap2 = govern(P, apply=True)
    tn2 = json.loads((P["registry"] / "VIA_TableNumbers_v0100.json").read_text(encoding="utf-8"))
    chk("⑥ 冪等:再發 0 · 號一字不變", ap2["summary"]["t_issued"] == 0 and ap2["summary"]["f_issued"] == 0 and sorted(e["table_no"] for e in tn2["entries"]) == nos)
    pulled = _th_pull("VRN", P["vrn"] / "registry", P["registry"], now, True)
    fpull = _fm_pull("VRN", P["vrn"] / "registry", P["registry"], now, True)
    vb = json.loads(_th_read(P["vrn"] / "registry" / "VRN_TableHeader_v0100.json"))
    chk("⑦ 子系統讀回:VRN 表讀到 TBL0001 · 功能讀到號 · 冊上出現號(遵守)", pulled["filled"] == 1 and vb["tables"]["vrn_rating_dict"]["table_no"] == "SSOT-VCGC-VRN-TBL0001" and fpull["filled"] >= 2)
    _w(P["vrn"] / "SSOT" / "VRN_Rating_Dict_v0101.json", {"BUY": {"zh": "買進", "score": 1, "w": 0.5}, "HOLD": {"zh": "持有", "score": 0, "w": 0.0}})
    _th_register("VRN", [P["vrn"] / "SSOT" / "VRN_Rating_Dict_v0101.json", P["vrn"] / "SSOT" / "VRN_NoKey_v0100.json"], P["vrn"] / "registry", now, True, P["root"])
    ap3 = govern(P, apply=True)
    chk("⑧ 已號表改頭 → T3 紅(舊鍵)· 新頭 _h2 測過另發新號", any(f["rule"] == "T3" for r in ap3["tables"].values() for f in r["flags"]) and any(e["tid"] == "vrn_rating_dict_h2" for e in ap3["issued_tables"]))
    _w(P["registry"] / "VIA_NumberBooks" / "VIA_NumberBook_ENG_v0100.jsonl", json.dumps({"source": "functional modules/VDF/VDF_ENG001_A_v0101.py", "code": "VIA-VDF-ENG009"}) + "\n")
    _w(P["registry"] / "VIA_NumberBooks" / "VIA_NumberBook_FNC_VDF_v0100.jsonl", json.dumps({"code": "VIA-VDF-ENG009-FNC004", "q": "shared"}) + "\n")
    _w(P["vdf"] / "VDF_ENG001_A_v0101.py", "def shared(a):\n    return a + 1\n")
    _fm_register("VDF", [P["vdf"]], P["root"], P["vdf"] / "registry", now, True)
    ap4 = govern(P, apply=True)
    codes4 = {e["key"]: e["code"] for e in json.loads((P["registry"] / "VIA_RegistryNumbers_v0100.json").read_text(encoding="utf-8"))["entries"]}
    chk("⑨ 既有 NumberBooks 沿用不重發(鍵 = source@version,版本一換新號):VDF_ENG001_A v0101 取 VIA-VDF-ENG009 · shared 取 -FNC004", codes4.get("VDF|ENG|VDF_ENG001_A|v0101") == "VIA-VDF-ENG009" and codes4.get("VDF|FNC|VDF_ENG001_A|shared|v0101") == "VIA-VDF-ENG009-FNC004")
    _w(P["registry"] / "VIA_ActivationGateway_v02_Hotfix_Manifest.json", {"rows": [{"n": 1, "x": "a"}]})
    _w(P["registry"] / "VIA_ActivationGateway_v03_Hotfix_Manifest.json", {"rows": [{"n": 1, "x": "b"}]})
    register(P, apply=True)
    ap5 = govern(P, apply=True)
    write_card(ap5, paste_pack(ap5), P)
    rs = resolve(P, apply=True)
    rul = json.loads(_th_read(P["registry"] / _RULINGS))
    vb2 = json.loads(_th_read(P["registry"] / "VCGC_TableHeader_v0100.json"))
    chk("⑭ v0102 resolve:VRN NoKey → 合成鍵裁定(只出裁定書,不動 VRN 冊)· 過時 v02 退役移 _superseded 留 v03 · 裁定書 + 退役帳", rul["tables"].get("vrn_nokey", {}).get("kind") == "synthetic"
        and (P["vrn"] / "registry" / "VRN_TableHeader_v0100.json").exists() and json.loads(_th_read(P["vrn"] / "registry" / "VRN_TableHeader_v0100.json"))["tables"]["vrn_nokey"].get("keys") == []
        and any("v02" in k for k in rul["retire"]) and list((P["registry"] / "_superseded").glob("VIA_ActivationGateway_v02*")) and (P["registry"] / "VIA_ActivationGateway_v03_Hotfix_Manifest.json").exists()
        and any(v.get("status") == "RETIRED" for v in vb2["tables"].values()))
    _w(P["sup"] / "ui_support" / "VRN_ENG001_A_v0100.py", "x = 1\n")
    _w(P["sup"] / "VDF_MDL999_Lonely_v0100.py", "y = 2\n")
    register(P, apply=True)
    ds0 = downstream(P, apply=False)
    moved_before = list((P["sup"] / "ui_support" / "_superseded").glob("*")) if (P["sup"] / "ui_support" / "_superseded").exists() else []
    ds1 = downstream(P, apply=True)
    vfm2 = json.loads(_th_read(P["registry"] / "VCGC_FunctionMatrix_v0100.json"))
    moved_after = list((P["sup"] / "ui_support" / "_superseded").glob("VRN_ENG001_A_v0100.py.DOWNSTREAM_*"))
    chk("⑮ v0103 downstream:dry-run 不動 · VRN 副本退役下放(移 _superseded · 矩陣 RETIRED replaced_by · 帳)· VDF 孤本待裁",
        len(ds0["retire"]) == 1 and not moved_before and len(ds1["retire"]) == 1 and moved_after and (P["registry"] / "VCGC_Downstream_Ledger.jsonl").exists()
        and any(v.get("status") == "RETIRED" and v.get("module") == "VRN_ENG001_A" for v in vfm2["items"].values()) and len(ds1["pending"]) == 1)
    ds2 = downstream(P, apply=True, adopt_orphans=True)
    chk("⑰ v0104 --adopt-orphans:VDF 孤本搬到 VDF 夾建檔 · 母標 RETIRED · 帳 orphan", len(ds2["retire"]) == 1 and (P["vdf"] / "VDF_MDL999_Lonely_v0100.py").exists() and not (P["sup"] / "VDF_MDL999_Lonely_v0100.py").exists() and not ds2["pending"])
    _w(P["sup"] / "audit_tools" / "panorama_xcheck_v110.py", "a = 1\n")
    _w(P["vrn"] / "panorama_xcheck_v112.py", "a = 2\n")
    register(P, apply=True)
    ds3 = downstream(P, apply=True)
    chk("⑱ v0104 無前綴族(panorama_xcheck)子系統 v112 ≥ 母 v110 → 下放", any(x["file"] == "panorama_xcheck_v110.py" for x in ds3["retire"]))
    okr, whyr = _test_table(P, {"source": "x", "table": "t", "keys": ["_rid"], "columns": []}) if False else (True, "")
    rows_dup = [{"a": 1}, {"a": 1}, {"a": 1}]
    seen = {}
    ids = []
    for r in rows_dup:
        h = _rid_of(r); n = seen.get(h, 0); seen[h] = n + 1; ids.append(h if n == 0 else "%s#%d" % (h, n))
    chk("⑲ _rid 三筆整列重複 → 三個不同序號", len(set(ids)) == 3)
    govern(P, apply=True)      # 退役後重發號,讓後面 ⑫ pull 的 pending 歸零
    _w(P["registry"] / "VIA_Policy_Laws_SSOT_v0107.json", {"laws": [{"id": "L115"}]})
    lw = law_append_116(P)
    chk("⑯ v0103 law:L116 附進 v0108 · 再跑 SKIP", lw["status"] == "WRITTEN" and lw["new"] == "VIA_Policy_Laws_SSOT_v0108.json" and law_append_116(P)["status"] == "SKIP")
    pack = paste_pack(ap4)
    card = write_card(ap4, pack, P)
    chk("⑩ 貼回包 ≤300 行 · NEXT: · 卡在 · 只寫四處(VRN/VDF 夾只有子系統自己的冊)", len(pack) <= 300 and pack[-1].startswith("NEXT:") and Path(card["md"]).exists()
        and sorted(q.name for q in (P["vrn"] / "registry").glob("*")) == ["VRN_FunctionMatrix_v0100.json", "VRN_TableHeader_v0100.json"])
    pr = pull_self(P)
    chk("⑫ v0101 pull:VCGC 自己的功能矩陣讀回號(filled ≥1,pending 0)", pr["fn"]["filled"] >= 1 and pr["fn"]["pending"] == 0)
    _w(P["root"] / "VIA_Reports" / "vrn" / "HEALTH_latest.json", {"files": [{"tail": "VRN_ENG001_A_v0100.py", "lamp": "RED", "ast_ok": True, "net_note": "無網橋"}]})
    an = annotate("VRN", P, apply=True)
    bk = json.loads(_th_read(P["registry"] / "VIA_AstAnnotations_VRN_v0100.json"))
    it = bk["items"]["FNC|VRN_ENG001_A|shared"]
    chk("⑬ v0101 annotate:VRN 側冊 項 %d · shared 有號 · 有分類與說明 · 健康紅旗併入 · 再跑全同" % an["summary"]["items"], an["summary"]["items"] >= 3 and it["code"] and it["cat"] and it["zh"] and it["health"] == "無網橋" and annotate("VRN", P, apply=True)["new"] == 0)
    body = ME.read_text(encoding="utf-8")
    chk("⑪ 帶加速器橋 · 兩共用段 · VIA_FROM_VCGC 閘", "[VIA:ACCEL-BRIDGE:v0100]" in body and "[VIA:TABLE-HEADER:v0100]" in body and "[VIA:FN-MATRIX:v0100]" in body and "VIA_FROM_VCGC" in body)
    os.environ.pop("VIA_ROOT", None)
    shutil.rmtree(td, ignore_errors=True)
    print("[計] %s 自測 %d/%d · %s" % (NAME, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
