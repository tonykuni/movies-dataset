#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL253_ToolingInventory v0105 — 薄尾:SSOT 引擎全景把前版鏈算進來(PR #630 Codex P2)

病因(PR #630 Codex P2,實測確認):v0104 每個家族只解析尾版那一支。薄尾版多半只補丁,真正讀寫 SSOT 的
程式在它載入的前版裡 —— 例:CGC_MDL237_NumberingSystem_v0120 只看得到 VIA_Numbering_SSOT,v0100 本體收集器讀的
VIA_Central_Params_SSOT / VIA_Policy_Laws_SSOT / VIA_VRN_FieldSpec_SSOT … 全漏;冊查詢、引擎參數、邊界總數因此靜默少算。
修法:尾版沿前版鏈靜態走(只 ast.parse,不執行被讀的檔),鏈上每支的 SSOT 引用與參數都記到尾版名下:
  每處引用帶 file(真正所在的檔,檔:行才對得上)與 via(來自哪一支前版;尾版自己 = 空);
  自測輔助函式(_selftest_where 這類 selftest 前綴名)寫冊 = 自測夾具寫(v0104 只認 selftest 本名,前版鏈帶進來後會誤紅);
  前版裡的頂層函式被較新一版同名蓋掉的,標 shadowed「被新版蓋」(可能仍經 PRIOR 呼叫,照列不刪)。
前版連結的認法(同 VCGC `chain` 的精神,補上本倉實際出現的寫法;加速器 / 網路工具橋區塊不算):
  ① 鏈表:CHAIN_VERSIONS = ('0101', '0100') 這類四位版號清單 + 載入 → 照清單走(清單外較舊的版不走)
  ② 取前版:自家族版號樣式(stem / "_v*.py" / r"_v\d+")+ 載入(spec_from_file_location · exec · runpy · subprocess …)
     + 「版號小於自己」的比較 → 同夾同家族、版號小於自己的最大一支
  ③ 釘名:程式碼字面寫了自家族較舊的版號(<stem>_vNNNN / "_vNNNN.py";用法說明字串不算)+ 載入 → 那幾支
  都沒有 = 本體,鏈到此為止。跨家族委派(門面轉呼別的家族)不算前版鏈:那個家族的尾版自己會出卡。
v0100 … v0104 一字不動;ssot 動詞與輸出路徑不變,輸出多 file / via / shadowed 欄與「前版鏈」欄。
只讀:不執行被讀的檔、不寫他系統的檔(只寫 VCGC 自己的報表夾);零網路;不碰 TA-Lib。
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
import csv as _csv
import html as _html
import importlib.util
import io as _io
import json
import os
import re
import sys
import tempfile
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL253_ToolingInventory"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0105(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0105(p) < _vnum_v0105(__file__)), key=_vnum_v0105)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0104 → v0103 → v0102 → v0101 → v0100
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


V0100 = PRIOR.V0100
V0101 = PRIOR.V0101
VIA = PRIOR.VIA
BRIDGE_RX = re.compile(r"#\s*=+\s*\[VIA:([A-Z]+)-BRIDGE:v\d+\].*?#\s*=+\s*\[VIA:\1-BRIDGE:END\]", re.S)
LOAD_RX = re.compile(r"spec_from_file_location|\bexec\s*\(|\brunpy\.|SourceFileLoader|import_module\s*\("
                     r"|subprocess\.(?:run|call|check_call|check_output|Popen)\s*\(")
LESS_RX = re.compile(r"(\.name|\.stem|_?vnum\w*|version_of|_?ver\w*)\s*(\([^()]*\))?\s*<(?!=?\s*0\b)"
                     r"|<\s*(_?vnum\w*|version_of|_?ver\w*)\s*\(|<\s*\w*(MY|SELF|OWN)_?V(ER)?\b")
USAGE_RX = re.compile(r"python|用法|usage", re.I)
FIXTURE_FUNC_RX = re.compile(r"(^|\.)(_?selftest\w*|_?self_test\w*|test_\w*)(\.|$)")   # v0104 只認 selftest 本名;前版鏈帶進 _selftest_where 這類自測輔助(寫暫存夾)
_DIRS: dict = {}
_CHAINS: dict = {}


def _siblings(p: Path) -> dict:
    """同夾同家族的版號檔 {版號: 路徑}(家族比對不分大小寫,和 v0104 engine_files 同一把尺)。"""
    d = p.parent
    if d not in _DIRS:
        fams: dict = {}
        for q in d.glob("*.py"):
            v = V0100.version_of(q)
            if v >= 0:
                fams.setdefault(V0100.family_of(q).lower(), {})[v] = q
        _DIRS[d] = fams
    return _DIRS[d].get(V0100.family_of(p).lower(), {})


def prior_links(p: Path, src: str) -> tuple:
    """一支版號檔直接載入的自家族前版(只 ast.parse):(路徑清單, 連結種類)。沒有 = ([], "本體")。"""
    own = V0100.version_of(p)
    lower = {v: q for v, q in _siblings(p).items() if v < own}
    if own < 0 or not lower:
        return [], "本體"
    code = BRIDGE_RX.sub("", src)
    if not LOAD_RX.search(code):
        return [], "本體"
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [], f"AST 壞 L{exc.lineno}"
    spans = [(src.count("\n", 0, m.start()) + 1, src.count("\n", 0, m.end()) + 1) for m in BRIDGE_RX.finditer(src)]
    parents = {ch: n for n in ast.walk(tree) for ch in ast.iter_child_nodes(n)}
    stem = V0100.family_of(p)
    pinned, fam, explicit = set(), False, []
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and isinstance(n.value, (ast.Tuple, ast.List)) and n.value.elts and all(
                isinstance(e, ast.Constant) and isinstance(e.value, str) and re.fullmatch(r"\d{4}", e.value) for e in n.value.elts):
            explicit = [int(e.value) for e in n.value.elts]
        if not (isinstance(n, ast.Constant) and isinstance(n.value, str)) or isinstance(parents.get(n), ast.Expr):
            continue                                            # 說明字串不算
        if any(a <= n.lineno <= b for a, b in spans):
            continue                                            # 加速器 / 網路工具橋不算
        s = n.value
        if stem.lower() in s.lower():
            fam = True
            if not USAGE_RX.search(s):                          # 「用法:python3 X_v0101.py」這種說明字串不算釘名
                pinned |= {int(x) for x in re.findall(re.escape(stem) + r"[_-]v(\d{4})", s, re.I)}
        elif re.fullmatch(r"[_-]v\d{4}(\.py)?", s):
            fam = True
            pinned.add(int(s[2:6]))
        elif re.match(r"[_-]v(\*|\\d|\[0-9\])", s):
            fam = True
    listed = [lower[v] for v in explicit if v in lower]
    if listed:
        return listed, "鏈表"
    out, kinds = [], []
    if fam and LESS_RX.search(code):
        out.append(lower[max(lower)])
        kinds.append("取前版")
    pins = [lower[v] for v in sorted(pinned, reverse=True) if v in lower and lower[v] not in out]
    if pins:
        out += pins
        kinds.append("釘名")
    return out, (" + ".join(kinds) or "本體")


def prior_chain(p: Path, src: str | None = None) -> list:
    """沿前版連結走到本體:[{path, file, version, link}](由新到舊;不含自己)。讀不到 / AST 壞的那支照實停在那裡。"""
    p = Path(p)
    key = str(p.resolve())
    if key in _CHAINS:
        return _CHAINS[key]
    seen, stack, edge = {p.resolve()}, [(p, src)], {}
    while stack:
        cur, text = stack.pop()
        if text is None:
            try:
                text = cur.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                text = ""                                       # 讀不到:鏈停在這支;engine_card 讀同一支時照實記「讀不到」
        nxt, kind = prior_links(cur, text)
        for q in nxt:
            if q.resolve() not in seen:
                seen.add(q.resolve())
                edge[q] = kind
                stack.append((q, None))
    out = [{"path": q, "file": PRIOR.rel_any(q), "version": f"v{V0100.version_of(q):04d}", "link": k}
           for q, k in sorted(edge.items(), key=lambda t: -V0100.version_of(t[0]))]
    _CHAINS[key] = out
    return out


def engine_card(p: Path, idx: dict) -> dict | None:
    """一支尾版的卡(含前版鏈)。被讀的檔裡的無效跳脫字元只會讓 ast.parse 印 SyntaxWarning,解析時靜音(不改判定)。"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        return _engine_card(Path(p), idx)


def _engine_card(p: Path, idx: dict) -> dict | None:
    r = PRIOR.rel_any(p)
    try:
        src = p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as exc:
        return {"engine": p.name, "path": r, "system": PRIOR.engine_owner(r), "error": f"讀不到 {type(exc).__name__}", "refs": []}
    chain = prior_chain(p, src)
    members, chain_errors = [(p, src, "")], []
    for c in chain:
        try:
            members.append((c["path"], c["path"].read_text(encoding="utf-8-sig", errors="replace"), c["path"].name))
        except OSError as exc:
            chain_errors.append(f"{c['path'].name} 讀不到 {type(exc).__name__}")
    if not any(PRIOR.SSOT_RX.search(s) for _, s, _ in members):
        return None
    refs, dyn, sigs, flags, verbs, envs, consts, newer = [], 0, set(), set(), set(), set(), [], set()
    for q, s, via in members:
        try:
            tree = ast.parse(s)
        except SyntaxError as exc:
            if not via:
                return {"engine": p.name, "path": r, "system": PRIOR.engine_owner(r), "error": f"AST 壞 L{exc.lineno}", "refs": []}
            chain_errors.append(f"{via} AST 壞 L{exc.lineno}")
            continue
        qr = PRIOR.rel_any(q)
        if PRIOR.SSOT_RX.search(s):
            sr = PRIOR.ssot_refs(tree, idx)
            for x in sr["refs"]:
                x["file"], x["via"] = qr, via
                x["shadowed"] = bool(via) and x["func"].split(".")[0] in newer
            refs += sr["refs"]
            dyn += sr["dynamic"]
            sigs |= set(sr["signatures"])
        cli = V0100.cli_surface(s)
        flags |= set(cli.get("flags") or [])
        verbs |= set(cli.get("verbs") or [])
        try:
            envs |= set(V0101.env_vars_v0101(tree))
        except Exception as exc:  # noqa: BLE001 — 前版的抽取器出錯就照實記一筆
            envs.add(f"(抽取失敗 {type(exc).__name__}{' · ' + via if via else ''})")
        have = {k["name"] for k in consts}
        consts += [dict(k, file=qr, via=via) for k in PRIOR.module_constants(tree) if k["name"] not in have]
        newer |= {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    if not refs and not dyn:
        return None
    ver = V0100.version_of(p)
    return {"engine": p.name, "path": r, "system": PRIOR.engine_owner(r), "version": (f"v{ver:04d}" if ver >= 0 else "—"),
            "refs": refs, "dynamic": dyn, "books": sorted({x["book"] for x in refs}),
            "params": {"flags": sorted(flags), "verbs": sorted(verbs), "env": sorted(envs), "constants": consts, "signatures": sorted(sigs)},
            "chain": [{"file": c["file"], "version": c["version"], "link": c["link"]} for c in chain],
            "inherited": sum(1 for x in refs if x["via"]), "chain_errors": chain_errors, "error": ""}


def boundary_of(card: dict) -> list:
    out = []
    for x in card.get("refs") or []:
        if x["owner"] in ("?", card["system"]) or x["state"] != "OK":
            continue
        fixture = x["access"] == "write" and FIXTURE_FUNC_RX.search(x["func"] or "")
        crossing = "自測夾具寫" if fixture else ("跨界寫" if x["access"] == "write" else "跨界讀")
        out.append({"engine": card["engine"], "path": x.get("file") or card["path"], "via": x.get("via", ""), "shadowed": bool(x.get("shadowed")),
                    "engine_system": card["system"], "book": x["book"], "book_system": x["owner"], "line": x["line"], "func": x["func"],
                    "access": x["access"], "kind": crossing, "lamp": "RED" if crossing == "跨界寫" else "GREEN"})
    return out


_V0104_BUILD_MAP = PRIOR.build_map
_V0104_ENGINE_CARD = PRIOR.engine_card
_V0104_BOUNDARY_OF = PRIOR.boundary_of


def build_map(files=None, idx=None) -> dict:
    _DIRS.clear()
    _CHAINS.clear()
    m = _V0104_BUILD_MAP(files=files, idx=idx)             # 前版的 build_map 走本版的 engine_card / boundary_of(下方補丁)
    bk = {b["book"]: b for b in m["books"]}
    for b in m["books"]:
        b["pinned_old"] = []
    for c in m["engines"]:
        for x in c["refs"]:
            if x["mode"] == "pinned" and x["tail_version"] not in ("", "—") and ("v" + x["pinned_version"]) < x["tail_version"]:
                bk[x["book"]]["pinned_old"].append(f"{Path(x.get('file') or c['path']).name}:L{x['line']} 釘 v{x['pinned_version']}(尾 {x['tail_version']})")
    s = m["summary"]
    s["pinned_old"] = sum(len(b["pinned_old"]) for b in m["books"])
    s["chained_engines"] = sum(1 for c in m["engines"] if c.get("chain"))
    s["chain_files"] = sum(len(c.get("chain") or []) for c in m["engines"])
    s["inherited_refs"] = sum(c.get("inherited", 0) for c in m["engines"])
    s["shadowed_refs"] = sum(1 for c in m["engines"] for x in c["refs"] if x.get("shadowed"))
    s["chain_errors"] = sum(len(c.get("chain_errors") or []) for c in m["engines"])
    m["lamp"] = "RED" if s["cross_write"] or s["ast_errors"] else ("YELLOW" if s["absent_books"] or s["pinned_old"] or s["chain_errors"] else "GREEN")
    m["engine"] = TAG
    return m


def _patch(on: bool) -> None:
    PRIOR.engine_card = engine_card if on else _V0104_ENGINE_CARD
    PRIOR.boundary_of = boundary_of if on else _V0104_BOUNDARY_OF


_patch(True)


def query(m: dict, text: str) -> list:
    """AST 查詢(同 v0104)· 引用與常數的檔:行指到真正所在的那一支(前版鏈繼承的會標 via)。"""
    q, hits = text.lower(), []
    for c in m["engines"]:
        if q in c["engine"].lower() or q in c["path"].lower():
            hits.append({"kind": "engine", "engine": c["engine"], "path": c["path"], "line": 0, "func": "",
                         "text": f"{len(c['refs'])} 處 SSOT 引用(前版鏈繼承 {c.get('inherited', 0)})"})
        for x in c["refs"]:
            if q in x["book"].lower() or q in x["func"].lower() or q in x["literal"].lower():
                hits.append({"kind": "ssot", "engine": c["engine"], "path": x.get("file") or c["path"], "line": x["line"], "func": x["func"],
                             "text": f"{x['book']} · {x['mode']} · {x['access']}" + (f" · 經 {c['engine']}" if x.get("via") else "")
                             + (" · 被新版蓋" if x.get("shadowed") else "")})
        prm = c["params"]
        for k in ("flags", "verbs", "env"):
            for v in prm[k]:
                if q in str(v).lower():
                    hits.append({"kind": k, "engine": c["engine"], "path": c["path"], "line": 0, "func": "", "text": str(v)})
        for k in prm["constants"]:
            if q in k["name"].lower():
                hits.append({"kind": "constant", "engine": c["engine"], "path": k.get("file") or c["path"], "line": k["line"], "func": "<module>",
                             "text": f"{k['name']} = {k['value']}"})
        for s in prm["signatures"]:
            if q in s.lower():
                hits.append({"kind": "signature", "engine": c["engine"], "path": c["path"], "line": 0, "func": s.split("(", 1)[0], "text": s})
    return hits


def write_outputs(m: dict, out_dir: Path | None = None) -> dict:
    out = Path(out_dir or PRIOR.OUT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    jp, hp, cp = out / "SSOT_ENGINE_MAP_latest.json", out / "SSOT_ENGINE_MAP_latest.html", out / "SSOT_ENGINE_MAP_latest.csv"
    jp.write_text(json.dumps(m, ensure_ascii=False, indent=1, default=list), encoding="utf-8")
    buf = _io.StringIO()
    w = _csv.writer(buf)
    w.writerow(["system", "engine", "path", "file", "via", "book", "book_system", "line", "func", "mode", "access", "shadowed", "tail_version", "state"])
    for c in m["engines"]:
        for x in c["refs"]:
            w.writerow([c["system"], c["engine"], c["path"], x.get("file") or c["path"], x.get("via", ""), x["book"], x["owner"], x["line"], x["func"],
                        x["mode"], x["access"], "Y" if x.get("shadowed") else "", x["tail_version"], x["state"]])
    cp.write_text("﻿" + buf.getvalue(), encoding="utf-8")
    e = _html.escape
    s = m["summary"]

    def chain_txt(c):
        ch = c.get("chain") or []
        if not ch:
            return "—"
        return f"{len(ch)} 支({e(ch[0]['version'])} … {e(ch[-1]['version'])})· 繼承 {c.get('inherited', 0)} 處"

    eng_rows = "".join(
        f"<tr><td>{e(c['system'])}</td><td class='p'><code>{e(c['path'])}</code></td><td>{len(c['refs'])}</td><td>{chain_txt(c)}</td><td>{c['dynamic']}</td>"
        f"<td>{e(' · '.join(c['books'][:8]))}{' …' if len(c['books']) > 8 else ''}</td><td>{e(' '.join(c['params']['flags'][:10]))}</td>"
        f"<td>{e(' '.join(c['params']['env'][:6]))}</td><td>{len(c['params']['constants'])}</td></tr>"
        for c in sorted(m["engines"], key=lambda c: (-len(c["refs"]), -c["dynamic"], c["path"])))
    book_rows = "".join(
        f"<tr><td><span class='l {'GREEN' if b['state'] == 'OK' and not b['pinned_old'] else ('YELLOW' if b['state'] == 'OK' else 'RED')}'></span>{e(b['book'])}</td>"
        f"<td>{e(b['owner'])}</td><td>{e(b['tail_version'])}</td><td>{len(b['engines'])}</td><td>{e(' · '.join(b['systems']))}</td>"
        f"<td>{b.get('read', 0)}/{b.get('write', 0)}/{b.get('scan', 0)}/{b.get('ref', 0)}</td><td>{e('; '.join(b['pinned_old'][:3]))}</td></tr>" for b in m["books"])
    bnd_rows = "".join(
        f"<tr><td><span class='l {x['lamp']}'></span>{e(x['kind'])}</td><td>{e(x['engine_system'])} → {e(x['book_system'])}</td>"
        f"<td><code>{e(x['path'])}:{x['line']}</code>{(' <span class=mut>經 ' + e(x['engine']) + '</span>') if x.get('via') else ''}</td>"
        f"<td>{e(x['func'])}{' <span class=mut>(被新版蓋)</span>' if x.get('shadowed') else ''}</td><td>{e(x['book'])}</td><td>{e(x['access'])}</td></tr>"
        for x in sorted(m["boundary"], key=lambda x: (x["lamp"] != "RED", x["engine_system"], x["engine"])))
    cards = [(s["engines"], "出現 SSOT 的引擎"), (s["books"], "被引用的 SSOT 冊"), (s["refs"], "字面引用處"), (s.get("inherited_refs", 0), "其中前版鏈繼承"),
             (s.get("chained_engines", 0), "有前版鏈的引擎"), (s["dynamic"], "動態冊名(f-string)"),
             (s["cross_read"], "跨界讀(允許)"), (s["cross_write"], "跨界寫(紅)"), (s["fixture_write"], "自測夾具寫(暫存夾)"), (s["pinned_old"], "釘舊版"),
             (s["absent_books"], "冊不在"), (s["ast_errors"], "AST 壞"), (s.get("chain_errors", 0), "前版鏈讀不到 / AST 壞")]
    page = ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>SSOT 引擎全景</title><style>{PRIOR.CSS}</style></head><body><main>"
            f"<h1><span class='l {m['lamp']}'></span>SSOT 引擎全景</h1><div class='mut'>{e(m['engine'])} · {e(m['at'])} · 掃 {s['scanned']} 支尾版"
            f" · 加前版鏈 {s.get('chain_files', 0)} 支 · 只讀 AST(不執行被讀的檔)</div>"
            "<div class='cards'>" + "".join(f"<div class='c'><b>{n}</b>{e(t)}</div>" for n, t in cards) + "</div>"
            f"<div class='mut'>各系統引擎數:{e(' · '.join(f'{k} {v}' for k, v in s['by_system'].items()))}</div>"
            "<h2>引擎(凡出現 SSOT · 含前版鏈)</h2><input id='q' placeholder='篩選:系統 / 路徑 / 冊名 / 旗標 / 環境變數' oninput='f()'>"
            "<div class='tbl'><table id='t'><thead><tr><th>系統</th><th>引擎(尾版)</th><th>字面引用</th><th>前版鏈</th><th>動態名</th><th>SSOT 冊</th>"
            "<th>旗標</th><th>環境變數</th><th>常數</th></tr></thead>"
            f"<tbody>{eng_rows}</tbody></table></div>"
            "<h2>SSOT 冊彙整(讀 / 寫 / 掃 / 名字)</h2><div class='tbl'><table><thead><tr><th>冊</th><th>冊主</th><th>尾版</th><th>引擎數</th><th>系統</th>"
            f"<th>讀/寫/掃/名</th><th>釘舊版</th></tr></thead><tbody>{book_rows}</tbody></table></div>"
            "<h2>邊界(引擎系統 ≠ 冊主系統)</h2><div class='tbl'><table><thead><tr><th>類別</th><th>方向</th><th>位置</th><th>函式</th><th>冊</th><th>存取</th></tr></thead>"
            f"<tbody>{bnd_rows}</tbody></table></div>"
            "<p class='mut'>AST 查詢:<code>via-vcgc run CGC_MDL253_ToolingInventory ssot query &lt;字&gt;</code> · 一本冊 <code>ssot book &lt;冊族&gt;</code> · "
            "一支引擎 <code>ssot engine &lt;引擎&gt;</code> · 邊界 <code>ssot boundary</code>。前版鏈:尾版載入的前版(取前版 / 釘名 / 鏈表)裡的引用記在尾版名下,"
            "位置指到真正所在的那一支;「被新版蓋」= 該前版函式已被較新一版同名定義(可能仍經 PRIOR 呼叫,照列)。</p></main>"
            "<script>function f(){var q=document.getElementById('q').value.toLowerCase();"
            "document.querySelectorAll('#t tbody tr').forEach(function(r){r.style.display=r.textContent.toLowerCase().indexOf(q)>=0?'':'none'})}</script></body></html>")
    hp.write_text(page, encoding="utf-8")
    return {"json": str(jp), "html": str(hp), "csv": str(cp)}


def _line(m: dict, files: dict | None = None) -> str:
    s = m["summary"]
    return ("[SSOT 引擎全景] %s · 掃 %d 支尾版(+前版鏈 %d 支)· 出現 SSOT 的引擎 %d(%s)· 冊 %d · 引用 %d(前版鏈繼承 %d · 被新版蓋 %d)· 動態 %d"
            " · 跨界讀 %d · 跨界寫 %d · 釘舊版 %d · 冊不在 %d · AST 壞 %d · 鏈讀不到 / 壞 %d%s" % (
                m["lamp"], s["scanned"], s.get("chain_files", 0), s["engines"], " · ".join(f"{k} {v}" for k, v in s["by_system"].items()), s["books"],
                s["refs"], s.get("inherited_refs", 0), s.get("shadowed_refs", 0), s["dynamic"], s["cross_read"], s["cross_write"], s["pinned_old"],
                s["absent_books"], s["ast_errors"], s.get("chain_errors", 0), (" · 頁 " + files["html"]) if files else ""))


def ssot_main(args: list) -> int:
    js = "--json" in args
    rest = [a for a in args if a != "--json"]
    out = None
    if "--out" in rest:
        i = rest.index("--out")
        out = rest[i + 1] if i + 1 < len(rest) else None
        rest = rest[:i] + rest[i + 2:]
    verb = rest[0] if rest else "map"
    if verb not in ("map", "query", "book", "engine", "boundary") or (verb in ("query", "book", "engine") and len(rest) < 2):
        print("用法:ssot [map] [--json] [--out 夾] | ssot query <字> | ssot book <冊族> | ssot engine <引擎> | ssot boundary")
        return 2
    m = build_map()
    if verb == "map":
        files = write_outputs(m, out)
        print(json.dumps({k: v for k, v in m.items() if k in ("lamp", "summary")}, ensure_ascii=False, indent=1) if js else _line(m, files))
        return 0 if m["lamp"] != "RED" else 1
    if verb == "query":
        hits = query(m, " ".join(rest[1:]))
        if js:
            print(json.dumps(hits, ensure_ascii=False, indent=1))
        else:
            for h in hits[:200]:
                print("  %-9s %s%s · %s · %s" % (h["kind"], h["path"], (":%d" % h["line"]) if h["line"] else "", h["func"] or "—", h["text"]))
            print("[SSOT 查詢] 「%s」命中 %d 處%s" % (" ".join(rest[1:]), len(hits), "(只印前 200)" if len(hits) > 200 else ""))
        return 0
    if verb == "book":
        want = rest[1].lower()
        bs = [b for b in m["books"] if want in b["book"].lower()]
        uses = [{"engine": c["engine"], "path": x.get("file") or c["path"], "via": x.get("via", ""), "system": c["system"], "line": x["line"],
                 "func": x["func"], "mode": x["mode"], "access": x["access"], "shadowed": bool(x.get("shadowed"))}
                for c in m["engines"] for x in c["refs"] if want in x["book"].lower()]
        print(json.dumps({"books": bs, "uses": uses}, ensure_ascii=False, indent=1, default=list) if js else
              "\n".join(["  %s · 冊主 %s · 尾版 %s · 引擎 %d" % (b["book"], b["owner"], b["tail_version"], len(b["engines"])) for b in bs]
                        + ["    %s:%d · %s · %s · %s%s%s" % (u["path"], u["line"], u["func"], u["mode"], u["access"],
                                                           (" · 經 " + u["engine"]) if u["via"] else "", " · 被新版蓋" if u["shadowed"] else "")
                           for u in uses[:200]]))
        return 0 if bs else 2
    if verb == "engine":
        want = rest[1].lower()
        cs = [c for c in m["engines"] if want in c["engine"].lower() or want in c["path"].lower()]
        print(json.dumps(cs, ensure_ascii=False, indent=1) if js else "\n".join(
            "  %s(%s)· SSOT %d 處(前版鏈繼承 %d)· 鏈 %s · 冊 %s · 旗標 %s · 環境變數 %s · 常數 %d · 簽章 %s" % (
                c["path"], c["system"], len(c["refs"]), c.get("inherited", 0),
                (" → ".join(x["version"] for x in c.get("chain") or []) or "—"), ", ".join(c["books"]),
                " ".join(c["params"]["flags"]) or "—", " ".join(c["params"]["env"]) or "—", len(c["params"]["constants"]),
                "; ".join(c["params"]["signatures"][:4]) or "—") for c in cs))
        return 0 if cs else 2
    b = m["boundary"]
    print(json.dumps(b, ensure_ascii=False, indent=1) if js else "\n".join(
        ["  %-5s %s %s → %s · %s:%d · %s · %s%s" % (x["lamp"], x["kind"], x["engine_system"], x["book_system"], x["path"], x["line"], x["func"], x["book"],
                                                  (" · 經 " + x["engine"]) if x.get("via") else "") for x in b]
        + ["[SSOT 邊界] 跨界讀 %d(允許)· 跨界寫 %d(紅)" % (m["summary"]["cross_read"], m["summary"]["cross_write"])]))
    return 1 if m["summary"]["cross_write"] else 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    if argv[:1] == ["ssot"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print(json.dumps({"via": "vcgc", "engine": TAG, "state": "DENY", "why": "only via-vcgc(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
            return 2
        return ssot_main(argv[1:])
    return PRIOR.main(argv)


FIX_V0105 = {
    ("VDF_ENG900_Demo", "0100"): "\n".join([
        "import json",
        "from pathlib import Path",
        'BOOK = "VIA_Numbering_SSOT_v0100.json"',
        "",
        "",
        "def collect(home):",
        '    return json.loads(Path(home, "VIA_Numbering_SSOT_v0100.json").read_text())',
        "",
        "",
        "def keep(home):",
        '    return json.loads(Path(home, "VRN_FieldRules_SSOT_v0101.json").read_text())',
        ""]),
    ("VDF_ENG900_Demo", "0101"): "\n".join([
        "import importlib.util",
        "import re",
        "from pathlib import Path",
        "HERE = Path(__file__).resolve().parent",
        '_STEM = "VDF_ENG900_Demo"',
        "",
        "",
        "def _vnum(p):",
        '    m = re.search(r"_v(\\d{4})$", Path(p).stem)',
        "    return int(m.group(1)) if m else -1",
        "",
        "",
        'PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if _vnum(p) < _vnum(__file__)), key=_vnum)',
        'SPEC = importlib.util.spec_from_file_location("prior", PRIOR_PATH)',
        "",
        "",
        "def collect(home):",
        "    return home",
        ""]),
    ("VDF_ENG901_List", "0100"): 'import json\n\n\ndef load(h):\n    return json.load(open(h + "/VRN_FieldRules_SSOT_v0102.json"))\n',
    ("VDF_ENG901_List", "0101"): 'import json\n\n\ndef load(h):\n    return json.load(open(h + "/VDF_TableHeader_SSOT_v0100.json"))\n',
    ("VDF_ENG901_List", "0102"): "\n".join([
        "import runpy",
        "from pathlib import Path",
        "HERE = Path(__file__).resolve().parent",
        '_STEM = "VDF_ENG901_List"',
        "CHAIN_VERSIONS = ('0100',)",
        'CHAIN = [HERE / ("%s_v%s.py" % (_STEM, v)) for v in CHAIN_VERSIONS]',
        "",
        "",
        "def run():",
        "    return runpy.run_path(str(CHAIN[0]))",
        ""]),
    ("VDF_ENG902_Pin", "0100"): 'from pathlib import Path\n\n\ndef tail(h):\n    return sorted(Path(h).glob("VIA_Numbering_SSOT_v*.json"))\n',
    ("VDF_ENG902_Pin", "0101"): 'def other(h):\n    return h + "/VDF_TableHeader_SSOT_v0100.json"\n',
    ("VDF_ENG902_Pin", "0102"): "\n".join([
        "import importlib.util",
        "from pathlib import Path",
        "HERE = Path(__file__).resolve().parent",
        '_STEM = "VDF_ENG902_Pin"',
        'PRIOR_PATH = HERE / (_STEM + "_v0100.py")',
        'SPEC = importlib.util.spec_from_file_location("p", PRIOR_PATH)',
        'USAGE = "用法:python3 VDF_ENG902_Pin_v0101.py run"',
        ""]),
    ("VDF_ENG903_Body", "0100"): 'def old(h):\n    return h + "/VDF_TableHeader_SSOT_v0100.json"\n',
    ("VDF_ENG904_Fx", "0100"): 'def _selftest_where(td):\n    with open(td + "/VIA_Numbering_SSOT_v0100.json", "w") as fh:\n        fh.write("{}")\n',
    ("VRN2_DemoAction", "0100"): "X = 1\n",
    ("VRN2_DemoAction", "0106"): 'import json\n\n\ndef rules(h):\n    return json.load(open(h + "/VRN_FieldRules_SSOT_v0102.json"))\n',
    ("VRN2_DemoAction", "0107"): "\n".join([
        "import re",
        "import subprocess",
        "import sys",
        "from pathlib import Path",
        "HERE = Path(__file__).resolve().parent",
        "MY_V = 107",
        "",
        "",
        "def _prior():",
        '    cands = [p for p in HERE.glob("VRN2_DemoAction_v[0-9][0-9][0-9][0-9].py") if int(re.search(r"_v(\\d{4})", p.name).group(1)) < MY_V]',
        '    return sorted(cands)[-1] if cands else HERE / "VRN2_DemoAction_v0100.py"',
        "",
        "",
        "def main(argv):",
        "    return subprocess.call([sys.executable, str(_prior())] + argv)",
        ""]),
}


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    print(f"=== {TAG} · 薄尾自測(SSOT 引擎全景含前版鏈 · PR #630 Codex P2)===", flush=True)
    me = Path(__file__).read_text(encoding="utf-8")
    net_bridge = next(m.group(0) for m in BRIDGE_RX.finditer(me) if "NET-BRIDGE" in m.group(0))
    idx = {"VIA_Numbering_SSOT": [(100, "supportive modules/registry/VIA_Numbering_SSOT_v0100.json")],
           "VRN_FieldRules_SSOT": [(101, "supportive modules/registry/VRN_FieldRules_SSOT_v0101.json"), (102, "supportive modules/registry/VRN_FieldRules_SSOT_v0102.json")],
           "VDF_TableHeader_SSOT": [(100, "functional modules/VDF/registry/VDF_TableHeader_SSOT_v0100.json")]}
    with tempfile.TemporaryDirectory(prefix="cgc253_v0105_") as td:
        d = Path(td)
        for (stem, ver), text in FIX_V0105.items():
            (d / f"{stem}_v{ver}.py").write_text(text, encoding="utf-8")
        (d / "VDF_ENG903_Body_v0101.py").write_text("\n".join([
            "from pathlib import Path", net_bridge, "HERE = Path(__file__).resolve().parent", '_STEM = "VDF_ENG903_Body"',
            "", "", "def older():", '    return [q for q in HERE.glob(_STEM + "_v*.py") if q.name < Path(__file__).name]',
            "", "", "def own(h):", '    return h + "/VIA_Numbering_SSOT_v0100.json"', ""]), encoding="utf-8")
        _DIRS.clear()
        _CHAINS.clear()
        ca = engine_card(d / "VDF_ENG900_Demo_v0101.py", idx)
        by = {(x["book"], x["func"]): x for x in (ca or {}).get("refs", [])}
        nb = by.get(("VIA_Numbering_SSOT", "collect"), {})
        fr = by.get(("VRN_FieldRules_SSOT", "keep"), {})
        chk("① 取前版(glob + 版號小於自己 + spec 載入):尾版自己沒有 SSOT 字面,v0100 本體的引用全記到尾版名下(file / via 指 v0100)",
            ca and [c["version"] for c in ca["chain"]] == ["v0100"] and ca["chain"][0]["link"] == "取前版" and ca["inherited"] == len(ca["refs"]) == 3
            and fr.get("via") == "VDF_ENG900_Demo_v0100.py" and fr.get("file", "").endswith("VDF_ENG900_Demo_v0100.py") and fr.get("line") == 11
            and ca["engine"] == "VDF_ENG900_Demo_v0101.py", ca and (ca["chain"], [(x["book"], x["func"], x.get("via")) for x in ca["refs"]]))
        chk("② 被新版蓋:尾版重新定義 collect → v0100 的 collect 引用標 shadowed(照列不刪);keep 沒被蓋、模組層常數不標",
            nb.get("shadowed") is True and fr.get("shadowed") is False and by.get(("VIA_Numbering_SSOT", "<module>"), {}).get("shadowed") is False, (nb, fr))
        cb = engine_card(d / "VDF_ENG901_List_v0102.py", idx)
        cc = engine_card(d / "VDF_ENG902_Pin_v0102.py", idx)
        chk("③ 鏈表 CHAIN_VERSIONS=('0100',) 只走 v0100(v0101 的 VDF_TableHeader 不算);釘名 _STEM + \"_v0100.py\" 只走 v0100(用法字串裡的 v0101 不算釘名)",
            cb and [c["version"] for c in cb["chain"]] == ["v0100"] and cb["chain"][0]["link"] == "鏈表" and cb["books"] == ["VRN_FieldRules_SSOT"]
            and cc and [c["version"] for c in cc["chain"]] == ["v0100"] and cc["chain"][0]["link"] == "釘名" and cc["books"] == ["VIA_Numbering_SSOT"],
            (cb and (cb["chain"], cb["books"]), cc and (cc["chain"], cc["books"])))
        cd = engine_card(d / "VDF_ENG903_Body_v0101.py", idx)
        ce = engine_card(d / "VRN2_DemoAction_v0107.py", idx)
        chk("④ 只有網路工具橋在載入(spec_from_file_location 在橋區塊裡)= 本體,不接前版;子行程委派(subprocess + < MY_V)= 取前版 v0106",
            cd and cd["chain"] == [] and cd["books"] == ["VIA_Numbering_SSOT"]
            and ce and ce["chain"] and ce["chain"][0]["version"] == "v0106" and "取前版" in ce["chain"][0]["link"] and "VRN_FieldRules_SSOT" in ce["books"],
            (cd and cd["chain"], ce and ce["chain"]))
        files = sorted(d.glob("*.py"))
        m = build_map(files=files, idx=idx)
        s = m["summary"]
        bd = [x for x in m["boundary"] if x["engine"] == "VDF_ENG900_Demo_v0101.py" and x["book"] == "VRN_FieldRules_SSOT"]
        po = {b["book"]: b["pinned_old"] for b in m["books"]}.get("VRN_FieldRules_SSOT", [])
        fx = [x["kind"] for x in m["boundary"] if x["engine"] == "VDF_ENG904_Fx_v0100.py"]
        chk("⑤ 全景:邊界列記在尾版名下、位置指到 v0100 那一支:行 · 釘舊版訊息寫真正所在的檔 · 摘要有前版鏈繼承數 / 有鏈引擎數 · "
            "_selftest_where 這類自測輔助寫暫存夾 = 自測夾具寫(不紅)",
            bd and bd[0]["path"].endswith("VDF_ENG900_Demo_v0100.py") and bd[0]["line"] == 11 and bd[0]["kind"] == "跨界讀" and bd[0]["via"]
            and fx == ["自測夾具寫"] and s["cross_write"] == 0
            and any(p.startswith("VDF_ENG900_Demo_v0100.py:L11 釘 v0101") for p in po)
            and s["inherited_refs"] >= 6 and s["chained_engines"] == 4 and s["chain_files"] >= 5 and m["engine"] == TAG, (bd, po, fx, s))
        hits = query(m, "fieldrules")
        chk("⑥ AST 查詢:繼承來的引用 → 檔:行指到前版那一支,並標「經 尾版」",
            any(h["kind"] == "ssot" and h["path"].endswith("VDF_ENG900_Demo_v0100.py") and h["line"] == 11 and "經 VDF_ENG900_Demo_v0101.py" in h["text"] for h in hits),
            hits)
        out = write_outputs(m, d / "out")
        page = Path(out["html"]).read_text(encoding="utf-8")
        head = Path(out["csv"]).read_text(encoding="utf-8").splitlines()[0]
        chk("⑦ 輸出:csv 多 file / via / shadowed 欄 · html 有「前版鏈」欄與繼承數卡 · json 摘要有 inherited_refs",
            "file" in head and "via" in head and "shadowed" in head and "前版鏈" in page and "其中前版鏈繼承" in page
            and json.loads(Path(out["json"]).read_text(encoding="utf-8"))["summary"]["inherited_refs"] == s["inherited_refs"], head)
    _patch(False)
    try:
        old = PRIOR.build_map()
    finally:
        _patch(True)
    real = build_map()
    rs = real["summary"]
    cards = {c["path"]: c for c in real["engines"]}
    n237 = next((c for c in real["engines"] if c["engine"].startswith("CGC_MDL237_NumberingSystem_v")), {})
    want = {"VIA_Central_Params_SSOT", "VIA_Policy_Laws_SSOT", "VIA_VRN_FieldSpec_SSOT"}
    old_books = {c["path"]: set(c["books"]) for c in old["engines"]}
    lost = [n for n, b in old_books.items() if n not in cards or not b <= set(cards[n]["books"])]
    chk("⑧ 實樹:CGC_MDL237 尾版現在看得到 v0100 本體讀的 %s(Codex 舉例)· 鏈 %d 支" % (" / ".join(sorted(want)), len(n237.get("chain") or [])),
        want <= set(n237.get("books") or []) and len(n237.get("chain") or []) >= 10 and n237.get("inherited", 0) > 0, sorted(n237.get("books") or []))
    chk("⑨ 不退步:v0104 列出的 %d 支引擎與它們的冊全在(本版 %d 支 · 引用 %d → %d · 前版鏈繼承 %d · 有鏈引擎 %d · 鏈壞 %d)"
        % (len(old_books), rs["engines"], old["summary"]["refs"], rs["refs"], rs["inherited_refs"], rs["chained_engines"], rs["chain_errors"]),
        not lost and rs["engines"] >= len(old_books) and rs["refs"] >= old["summary"]["refs"] and rs["inherited_refs"] > 0, lost[:10])
    body = me.split("def selftest", 1)[0]
    chk("⑩ 加速器橋 · 網路工具橋在;只 ast.parse 不執行被讀的檔;寫檔只在 VCGC 報表夾(write_outputs 三處);不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in me and "[VIA:NET-BRIDGE" in me and not re.search(r"^\s*(import|from)\s+talib", me, re.M)
        and "exec(" not in body.replace("_spec.loader.exec_module(PRIOR)", "") and body.count(".write_text(") == 3)
    import contextlib
    buf = _io.StringIO()
    _patch(False)
    try:
        with contextlib.redirect_stdout(buf):
            rc = PRIOR.selftest()
    finally:
        _patch(True)
    for ln in [x for x in buf.getvalue().splitlines() if "[計]" in x][-4:]:
        print("  ── 前版 " + ln.strip()[:200], flush=True)
    chk("⑪ 前版 v0104 自測 rc 0(暫時拿掉本版補丁跑,跑完補回)", rc == 0, "rc %s" % rc)
    good = all(ok)
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'rc ' + str(rc)} · 合計 {'PASS' if good else 'FAIL'}", flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
