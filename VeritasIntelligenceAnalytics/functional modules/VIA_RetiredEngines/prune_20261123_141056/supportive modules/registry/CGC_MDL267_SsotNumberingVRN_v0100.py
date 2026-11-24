#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC SsotNumberingVRN v0100 — VCGC 端 SSOT 下放第二段:衝突偵測 + 發號(L111 ③⑤⑦ · 操作員裁定 2026-10-06:VRN 生成 · VCGC 偵測+編號 · 裁決歸操作員+AI)。

唯讀 VRN:只讀 functional modules/VRN/registry/VRN_SSOT_Index_v*.json 與 VRN/SSOT/ 的冊;一字不寫 VRN(L111 ②)。
只寫兩處(都是 VCGC 自己的):
  supportive modules/registry/VIA_SSOT_Numbers_VRN_v0100.json   發號冊(VRN 以鍵 number pull 讀回);只增:號跟鍵走,發了不收回、不改、不重發
  docs/handoff/ai/VCGC_SsotConflictCard_VRN_<日期>.md / .json     衝突卡(黃紅貼回包,給操作員+AI 裁)
六類偵測(每鍵):
  R1 DUP_NAME_DIFF  同名異頭:同族冊在 VRN/knowledge · VDF 夾 · 中央 registry 另有一份,頂層欄位集合不同        紅
  R2 ONE_NO_MULTI   一號多源:同一 ssot_no 綁到兩個以上的鍵                                                     紅
  R3 DUP_NO         重號:Index 的 ssot_no 與發號冊對不上(同鍵異號 / 異鍵同號)                                   紅
  R4 SOURCE_UNREG   來源未登:source 空 · central_path/local_path 不在 · 本機 sha 與 Index 登記不符(擅改未登記)   紅
  R5 REGEX_COPY     regex 跨冊拷貝:同一 pattern 字串出現在 ≥2 本 VRN 冊                                        黃
  R6 SHARED_SLICE   共用冊切片:共用族(Central_Synonym_Regex 等)不該整本在 VRN/SSOT/;出現=黃;未下放=灰註記        黃/灰
紅 = 衝突,該鍵不發號;黃 = 提醒,列卡不擋號(依 2026-10-06 規劃表);灰 = 尚未適用。
號碼制:承 VIA_SSOT_ItemNumbers 的 SSOT-<FAM>-<SUB>-<KIND>NNNN,新 KIND = BOOK(整本 SSOT 冊;只增,不動既有 KIND);
序號接現有 BOOK 最大號 +1(先掃 ItemNumbers 尾版與本發號冊,取號前掃樹 — LL119)。
動詞: detect(唯讀出卡)· issue --apply(偵測 + 零紅發號 + 寫冊 + 出卡)· --selftest(temp 沙盒)
沙盒鍵: VIA_ROOT(整棵樹根)
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
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ME = Path(__file__).resolve()
NAME = ME.stem                      # CGC_MDL###_SsotNumberingVRN_v0100(號碼由落地 PS 掃樹取)
TAG = "v0100"
_NUM_BOOK = "VIA_SSOT_Numbers_VRN_v0100.json"
_ITEM_GLOB = "VIA_SSOT_ItemNumbers_v*.json"
_SUB, _FAM, _KIND = "VRN", "VCGC", "BOOK"
_SHARED = ("VIA_Central_Synonym_Regex", "VIA_SSOT_SynonymUnion", "VIA_FinalParameters_CanonicalRegistry", "VDF_VRN_SourceFallback_AllDataRegistry")
_REGEX_KEYS = ("pattern", "regex", "re", "rx", "strict", "extraction", "catch_all")


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
    return {"root": r, "registry": r / "supportive modules" / "registry", "vrn": r / "functional modules" / "VRN",
            "vrn_ssot": r / "functional modules" / "VRN" / "SSOT", "vrn_reg": r / "functional modules" / "VRN" / "registry",
            "vrn_know": r / "functional modules" / "VRN" / "knowledge", "vdf": r / "functional modules" / "VDF",
            "cards": r / "docs" / "handoff" / "ai"}


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _vkey(name: str):
    m = re.search(r"_v(\d{4})", name)
    return int(m.group(1)) if m else -1


def _family(name: str) -> str:
    stem = re.sub(r"_sha[0-9a-f]{8,}$", "", Path(name).stem)
    return re.sub(r"_v\d{2,4}[A-Za-z0-9]*$", "", stem)


def _load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def _head(p: Path):
    """冊的「頭」:json=頂層鍵集合(list 則首元素鍵);csv=首列欄名;其他=None。"""
    if p.suffix.lower() == ".json":
        d = _load_json(p)
        if isinstance(d, dict):
            return tuple(sorted(d.keys()))
        if isinstance(d, list) and d and isinstance(d[0], dict):
            return tuple(sorted(d[0].keys()))
        return ("<non-object>",)
    if p.suffix.lower() == ".csv":
        try:
            return tuple(p.read_text(encoding="utf-8-sig").splitlines()[0].split(","))
        except (OSError, IndexError):
            return None
    return None


def _vrn_index(P: dict):
    hits = sorted(P["vrn_reg"].glob("VRN_SSOT_Index_v*.json"), key=lambda q: _vkey(q.name)) if P["vrn_reg"].is_dir() else []
    if not hits:
        return None, None
    return hits[-1], _load_json(hits[-1])


def _load_numbers(P: dict) -> dict:
    fp = P["registry"] / _NUM_BOOK
    d = _load_json(fp) if fp.exists() else None
    if not isinstance(d, dict) or not isinstance(d.get("entries"), list):
        d = {"schema": "VIA_SSOT_Numbers_VRN", "version": "v0100", "engine": NAME,
             "format": "SSOT-%s-%s-%sNNNN(承 VIA_SSOT_ItemNumbers 制;KIND BOOK = 整本 SSOT 冊,只增)" % (_FAM, _SUB, _KIND),
             "rule": "號跟鍵走:同鍵永遠同號 · 發了不收回不改不重發 · sha 變只記 sha_history · 紅燈鍵不發號 · 子系統以鍵 number pull 讀回",
             "created_at": _now(), "entries": [], "blocked": []}
    return d


def _max_seq(P: dict, numbers: dict) -> int:
    mx = 0
    rx = re.compile(r"^SSOT-%s-%s-%s(\d{4})$" % (_FAM, _SUB, _KIND))
    for e in numbers.get("entries", []):
        m = rx.match(str(e.get("ssot_no", "")))
        if m:
            mx = max(mx, int(m.group(1)))
    for fp in sorted(P["registry"].glob(_ITEM_GLOB)) if P["registry"].is_dir() else []:
        d = _load_json(fp)
        for it in (d or {}).get("items", []) if isinstance(d, dict) else []:
            m = rx.match(str(it.get("id", "")))
            if m:
                mx = max(mx, int(m.group(1)))
    return mx


def _regex_strings(obj, acc: set, parent_key: str = ""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            _regex_strings(v, acc, str(k))
    elif isinstance(obj, list):
        for v in obj:
            _regex_strings(v, acc, parent_key)
    elif isinstance(obj, str):
        s = obj.strip()
        if len(s) >= 8 and (parent_key.lower() in _REGEX_KEYS or re.search(r"\\[dswbDSW(]|\(\?[:<!=]|\[\^?[^\]]+\]\{", s)):
            acc.add(s)


def detect(P: dict | None = None, numbers: dict | None = None) -> dict:
    P = P or _paths()
    out = {"verb": "detect", "ts": _now(), "engine": NAME, "root": str(P["root"]), "keys": {}, "global": [], "_notes": []}
    idx_fp, idx = _vrn_index(P)
    if not idx:
        out["_notes"].append("VRN_SSOT_Index 不在(VRN 先跑 ssot adopt --apply)")
        out["lamp"] = "GRAY"
        out["summary"] = {"keys": 0, "red": 0, "yellow": 0, "clean": 0}
        return out
    out["index"] = str(idx_fp)
    numbers = numbers if numbers is not None else _load_numbers(P)
    num_by_key = {e["key"]: e["ssot_no"] for e in numbers.get("entries", []) if e.get("key")}
    ents = idx.get("entries", {})
    flags: dict = {k: [] for k in ents}

    # R4 來源未登 / 擅改未登記
    for k, e in ents.items():
        src = e.get("source") or ""
        cp, lp = Path(e.get("central_path", "")), Path(e.get("local_path", ""))
        if not src:
            flags[k].append(("R4", "RED", "SOURCE_UNREG", "source 欄空"))
        if not str(cp) or not cp.exists():
            flags[k].append(("R4", "RED", "SOURCE_UNREG", "central_path 不在:%s" % cp))
        if not str(lp) or not lp.exists():
            flags[k].append(("R4", "RED", "SOURCE_UNREG", "local_path 不在:%s" % lp))
        elif e.get("sha256") and _sha(lp) != e["sha256"]:
            flags[k].append(("R4", "RED", "SOURCE_UNREG", "本機冊 sha 與 Index 登記不符(改了沒 adopt 登記)"))

    # R2 一號多源 · R3 重號
    by_no = defaultdict(list)
    for k, e in ents.items():
        if e.get("ssot_no"):
            by_no[e["ssot_no"]].append(k)
    for no, ks in by_no.items():
        if len(ks) > 1:
            for k in ks:
                flags[k].append(("R2", "RED", "ONE_NO_MULTI", "%s 同時綁 %d 鍵" % (no, len(ks))))
    rev = defaultdict(list)
    for k, no in num_by_key.items():
        rev[no].append(k)
    for k, e in ents.items():
        no_idx, no_book = e.get("ssot_no") or "", num_by_key.get(k, "")
        if no_idx and no_book and no_idx != no_book:
            flags[k].append(("R3", "RED", "DUP_NO", "Index %s ≠ 發號冊 %s" % (no_idx, no_book)))
        if no_idx and no_idx in rev and k not in rev[no_idx]:
            flags[k].append(("R3", "RED", "DUP_NO", "%s 在發號冊屬別的鍵 %s" % (no_idx, rev[no_idx][0])))

    # R1 同名異頭:同族冊在別處
    others: dict = defaultdict(list)
    scan_dirs = [P["vrn_know"], P["registry"]] + ([P["vdf"]] if P["vdf"].is_dir() else [])
    for d in scan_dirs:
        if not d.is_dir():
            continue
        for fp in d.rglob("*"):
            if fp.is_file() and fp.suffix.lower() in (".json", ".csv") and not (set(fp.parts) & {"references", "intake", "_superseded", "VIA_RetiredEngines", "_quarantine_pip_vendor"}):
                others[(_family(fp.name), fp.suffix.lower())].append(fp)
    for k, e in ents.items():
        lp = Path(e.get("local_path", ""))
        if not lp.exists():
            continue
        fam_local = _family(lp.name)
        fam_central = e.get("table") or ""
        cands = []
        for fam in {fam_local, fam_central}:
            cands += others.get((fam, lp.suffix.lower()), [])
        cp = Path(e.get("central_path", ""))
        cands = [c for c in cands if c.resolve() != lp.resolve() and c.resolve() != cp.resolve()
                 and c.parent.resolve() != cp.parent.resolve()]   # 中央同夾的舊版號是來源的前版,不算另一份
        # 同族多版只比尾版
        tail = {}
        for c in cands:
            key2 = (c.parent, _family(c.name))
            if key2 not in tail or _vkey(c.name) > _vkey(tail[key2].name):
                tail[key2] = c
        h0 = _head(lp)
        for c in tail.values():
            h1 = _head(c)
            if h0 is not None and h1 is not None and h0 != h1:
                flags[k].append(("R1", "RED", "DUP_NAME_DIFF", "同族異頭:%s(頂層欄位 %d≠%d)" % (c.relative_to(P["root"]), len(h0), len(h1))))
            elif _sha(c) != _sha(lp):
                flags[k].append(("R1", "YELLOW", "DUP_NAME_DRIFT", "同族同頭內容漂移:%s" % c.relative_to(P["root"])))

    # R5 regex 跨冊拷貝(只看 VRN/SSOT 的 json)
    pat_books: dict = defaultdict(set)
    for k, e in ents.items():
        lp = Path(e.get("local_path", ""))
        if lp.exists() and lp.suffix.lower() == ".json":
            acc: set = set()
            _regex_strings(_load_json(lp), acc)
            for s in acc:
                pat_books[s].add(k)
    copies = {s: ks for s, ks in pat_books.items() if len(ks) >= 2}
    for s, ks in copies.items():
        for k in ks:
            flags[k].append(("R5", "YELLOW", "REGEX_COPY", "pattern 另見 %d 冊:%s" % (len(ks) - 1, (s[:48] + "…") if len(s) > 48 else s)))
    out["global"].append({"rule": "R5", "lamp": "YELLOW" if copies else "GREEN", "n_patterns_copied": len(copies)})

    # R6 共用冊切片
    present = [k for k, e in ents.items() if any((e.get("table") or "").startswith(sf) for sf in _SHARED)]
    for k in present:
        flags[k].append(("R6", "YELLOW", "SHARED_SLICE", "共用族整本在 VRN/SSOT(應只下放 VRN 切片)"))
    out["global"].append({"rule": "R6", "lamp": "YELLOW" if present else "GRAY", "note": "" if present else "共用冊切片尚未下放(VRN v0122 以後);灰 = 尚未適用"})

    red = yellow = clean = 0
    for k in ents:
        fl = flags[k]
        lamp = "RED" if any(x[1] == "RED" for x in fl) else ("YELLOW" if fl else "GREEN")
        red += lamp == "RED"
        yellow += lamp == "YELLOW"
        clean += lamp == "GREEN"
        out["keys"][k] = {"lamp": lamp, "table": ents[k].get("table"), "kind": ents[k].get("kind"), "ssot_no": ents[k].get("ssot_no") or "",
                          "flags": [{"rule": a, "lamp": b, "code": c, "detail": d} for a, b, c, d in fl]}
    out["summary"] = {"keys": len(ents), "red": red, "yellow": yellow, "clean": clean}
    out["lamp"] = "RED" if red else ("YELLOW" if yellow else "GREEN")
    return out


def issue(apply: bool = False, P: dict | None = None) -> dict:
    P = P or _paths()
    numbers = _load_numbers(P)
    det = detect(P, numbers)
    out = {"verb": "issue", "ts": _now(), "apply": apply, "detect": det, "issued": [], "already": 0, "blocked": [], "_notes": list(det["_notes"])}
    if det.get("lamp") == "GRAY" and not det.get("keys"):
        out["lamp"] = "GRAY"
        return out
    have = {e["key"]: e for e in numbers["entries"] if e.get("key")}
    seq = _max_seq(P, numbers)
    idx_fp, idx = _vrn_index(P)
    ents = idx.get("entries", {})
    batch = "b" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    for k in sorted(det["keys"]):
        kv = det["keys"][k]
        e = ents.get(k, {})
        if k in have:
            out["already"] += 1
            if e.get("sha256") and have[k].get("sha256") != e["sha256"]:
                have[k].setdefault("sha_history", []).append({"sha256": have[k].get("sha256"), "until": _now()})
                have[k]["sha256"] = e["sha256"]
            continue
        if kv["lamp"] == "RED":
            out["blocked"].append({"key": k, "flags": [f["code"] for f in kv["flags"] if f["lamp"] == "RED"]})
            continue
        seq += 1
        no = "SSOT-%s-%s-%s%04d" % (_FAM, _SUB, _KIND, seq)
        rec = {"key": k, "ssot_no": no, "table": e.get("table"), "kind": e.get("kind"), "sha256": e.get("sha256"),
               "local_path": e.get("local_path"), "issued_at": _now(), "batch": batch,
               "note": ("yellow:" + ",".join(sorted({f["code"] for f in kv["flags"]}))) if kv["flags"] else ""}
        out["issued"].append(rec)
        numbers["entries"].append(rec)
        have[k] = rec
    numbers["blocked"] = out["blocked"]
    numbers["updated_at"] = _now()
    numbers["next_seq"] = seq + 1
    if apply:
        P["registry"].mkdir(parents=True, exist_ok=True)
        (P["registry"] / _NUM_BOOK).write_text(json.dumps(numbers, ensure_ascii=False, indent=1), encoding="utf-8")
        out["number_book"] = str(P["registry"] / _NUM_BOOK)
    out["lamp"] = "RED" if out["blocked"] else ("YELLOW" if (not apply and out["issued"]) else "GREEN")
    return out


def write_card(res: dict, P: dict | None = None) -> dict:
    P = P or _paths()
    det = res["detect"] if res.get("verb") == "issue" else res
    day = datetime.datetime.now().strftime("%Y%m%d")
    P["cards"].mkdir(parents=True, exist_ok=True)
    md = P["cards"] / ("VCGC_SsotConflictCard_VRN_%s.md" % day)
    js = P["cards"] / ("VCGC_SsotConflictCard_VRN_%s.json" % day)
    s = det.get("summary", {})
    L = ["# VCGC → VRN 資訊卡:SSOT 衝突偵測 + 發號(%s)" % day, "",
         "> L111:VCGC 只讀 VRN,只寫本卡與發號冊。紅 = 衝突不發號(操作員+AI 裁);黃 = 提醒不擋號;灰 = 尚未適用。", "",
         "## 計", "- 鍵 %d · 紅 %d · 黃 %d · 乾淨 %d" % (s.get("keys", 0), s.get("red", 0), s.get("yellow", 0), s.get("clean", 0))]
    if res.get("verb") == "issue":
        L.append("- 本輪發號 %d · 已有號 %d · 擋號 %d%s" % (len(res["issued"]), res["already"], len(res["blocked"]), "" if res["apply"] else "(dry-run 未寫冊)"))
    L += ["", "## 全域", ] + ["- %s %s %s" % (g["rule"], g["lamp"], g.get("note") or g.get("n_patterns_copied", "")) for g in det.get("global", [])]
    L += ["", "## 紅(每鍵一列;只攤開不裁定)", "| 鍵 | 規則 | 細節 |", "|---|---|---|"]
    n = 0
    for k, kv in sorted(det.get("keys", {}).items()):
        for f in kv["flags"]:
            if f["lamp"] == "RED":
                L.append("| %s | %s %s | %s |" % (k, f["rule"], f["code"], f["detail"].replace("|", "¦")))
                n += 1
    if not n:
        L.append("| — | — | 零紅 |")
    L += ["", "## 黃(提醒)", "| 鍵 | 規則 | 細節 |", "|---|---|---|"]
    n = 0
    for k, kv in sorted(det.get("keys", {}).items()):
        for f in kv["flags"]:
            if f["lamp"] == "YELLOW":
                L.append("| %s | %s %s | %s |" % (k, f["rule"], f["code"], f["detail"].replace("|", "¦")))
                n += 1
    if not n:
        L.append("| — | — | 零黃 |")
    if res.get("verb") == "issue" and res["issued"]:
        L += ["", "## 本輪發號", "| 號 | 鍵 |", "|---|---|"] + ["| %s | %s |" % (r["ssot_no"], r["key"]) for r in res["issued"]]
    L += ["", "NEXT: " + ("把紅表貼給 AI,裁完 VRN 出新版冊再 adopt → 本引擎重跑" if s.get("red") else "零紅 → VRN 跑 ssot number pull 讀號 · 黃表留卡,下一輪裁")]
    md.write_text("\n".join(L) + "\n", encoding="utf-8")
    js.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"md": str(md), "json": str(js)}


def _tally(res: dict) -> None:
    det = res["detect"] if res.get("verb") == "issue" else res
    s = det.get("summary", {})
    g = {x["rule"]: x for x in det.get("global", [])}
    print("[計] vcgc ssot detect 鍵=%d 紅=%d 黃=%d 乾淨=%d · R5 拷貝 pattern=%s · R6 %s · %s"
          % (s.get("keys", 0), s.get("red", 0), s.get("yellow", 0), s.get("clean", 0),
             g.get("R5", {}).get("n_patterns_copied", "-"), g.get("R6", {}).get("lamp", "-"), det.get("lamp")))
    if res.get("verb") == "issue":
        print("[計] vcgc ssot issue%s 發號=%d 已有號=%d 擋號=%d · %s"
              % (" --apply" if res["apply"] else "(dry-run)", len(res["issued"]), res["already"], len(res["blocked"]), res["lamp"]))
        for b in res["blocked"]:
            print("  [RED] 擋號 %s · %s" % (b["key"], ",".join(b["flags"])))
    for k, kv in sorted(det.get("keys", {}).items()):
        for f in kv["flags"]:
            if f["lamp"] == "RED":
                print("  [RED] %s · %s %s · %s" % (k, f["rule"], f["code"], f["detail"]))
    for n in res.get("_notes", []):
        print("  [注] %s" % n)
    if res.get("card"):
        print("  [卡] %s" % res["card"]["md"])


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VCGC] 拒絕。只能經 via-vcgc。")
        return 2
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a[:2]:
        return selftest()
    as_json = "--json" in a
    a = [x for x in a if x != "--json"]
    if a[:1] == ["detect"]:
        res = detect()
    elif a[:1] == ["issue"]:
        res = issue(apply=("--apply" in a))
    else:
        print("[拒跑] detect | issue [--apply] | --selftest")
        return 2
    if res.get("lamp") != "GRAY" or res.get("keys") or res.get("detect"):
        try:
            res["card"] = write_card(res)
        except OSError as exc:
            res.setdefault("_notes", []).append("卡寫入失敗 %s" % type(exc).__name__)
    if as_json:
        print(json.dumps(res, ensure_ascii=False))
    _tally(res)
    return 1 if res.get("lamp") == "RED" else 0


def _w(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, str):
        p.write_text(obj, encoding="utf-8")
    else:
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


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

    td = Path(tempfile.mkdtemp(prefix="cgcssot-"))
    os.environ["VIA_ROOT"] = str(td)
    P = _paths()
    chk("① 沙盒:VIA_ROOT 指 temp,所有路徑都在 temp 下", all(str(v).startswith(str(td)) for v in P.values()))
    # 中央 + VRN 夾具
    _w(P["registry"] / "VIA_VRN_DocClass_SSOT_v0101.json", {"classes": ["個股"], "rx": {"pattern": r"(?<!\d)([1-9]\d{3})(?!\d)"}})
    _w(P["registry"] / "VRN_S05_FieldRegistry_v0102.json", {"fields": {"TICKER": {"pattern": r"(?<!\d)([1-9]\d{3})(?!\d)"}}})
    _w(P["registry"] / "VRN_Verified_Module_Registry_v0100.json", {"rows": [1]})
    _w(P["registry"] / "VRN_Verified_Module_Registry_v0100.csv", "a,b\n1,2\n")
    _w(P["registry"] / "VRN_Plain_SSOT_v0100.json", {"x": 1})
    _w(P["registry"] / "VIA_SSOT_ItemNumbers_v0100.json", {"items": [{"id": "SSOT-VCGC-VRN-BOOK0003"}, {"id": "SSOT-VCGC-VRN-WKFL0013"}]})
    for src, dst in (("VIA_VRN_DocClass_SSOT_v0101.json", "VRN_DocClass_SSOT_v0101.json"),
                     ("VRN_S05_FieldRegistry_v0102.json", "VRN_S05_FieldRegistry_v0102.json"),
                     ("VRN_Verified_Module_Registry_v0100.json", "VRN_Verified_Module_Registry_v0100.json"),
                     ("VRN_Verified_Module_Registry_v0100.csv", "VRN_Verified_Module_Registry_v0100.csv"),
                     ("VRN_Plain_SSOT_v0100.json", "VRN_Plain_SSOT_v0100.json")):
        P["vrn_ssot"].mkdir(parents=True, exist_ok=True)
        shutil.copy2(P["registry"] / src, P["vrn_ssot"] / dst)
    # knowledge 同族異頭(R1 紅)+ 一本缺 local(R4 紅)
    _w(P["vrn_know"] / "VRN_Plain_SSOT_v0099.json", {"x": 1, "y": 2})
    ents = {}

    def ent(key, table, fname, kind="own", sha=None):
        lp = P["vrn_ssot"] / fname
        ents[key] = {"key": key, "subsystem": "VRN", "source": "central_registry", "table": table, "kind": kind,
                     "local_path": str(lp), "central_path": str(P["registry"] / (table + fname[fname.rfind("_v"):])) if table.startswith("VIA_") else str(P["registry"] / fname),
                     "central_version": "v0100", "sha256": sha or (_sha(lp) if lp.exists() else "deadbeef"), "ssot_no": ""}
    ent("VRN|central_registry|VIA_VRN_DocClass_SSOT", "VIA_VRN_DocClass_SSOT", "VRN_DocClass_SSOT_v0101.json")
    ent("VRN|central_registry|VRN_S05_FieldRegistry", "VRN_S05_FieldRegistry", "VRN_S05_FieldRegistry_v0102.json")
    ent("VRN|central_registry|VRN_Verified_Module_Registry", "VRN_Verified_Module_Registry", "VRN_Verified_Module_Registry_v0100.json")
    ent("VRN|central_registry|VRN_Verified_Module_Registry|csv", "VRN_Verified_Module_Registry", "VRN_Verified_Module_Registry_v0100.csv")
    ent("VRN|central_registry|VRN_Plain_SSOT", "VRN_Plain_SSOT", "VRN_Plain_SSOT_v0100.json")
    ent("VRN|central_registry|VRN_Missing_SSOT", "VRN_Missing_SSOT", "VRN_Missing_SSOT_v0100.json")
    _w(P["vrn_reg"] / "VRN_SSOT_Index_v0100.json", {"schema": "VRN_SSOT_Index", "entries": ents})
    det = detect(P)
    K = det["keys"]
    chk("② 唯讀 VRN:detect 後 VRN 夾檔數不變", len(list(P["vrn_ssot"].iterdir())) == 5 and len(list(P["vrn_reg"].iterdir())) == 1)
    chk("③ R4 來源未登:缺 local 的鍵紅", K["VRN|central_registry|VRN_Missing_SSOT"]["lamp"] == "RED"
        and any(x["code"] == "SOURCE_UNREG" for x in K["VRN|central_registry|VRN_Missing_SSOT"]["flags"]))
    chk("④ R1 同名異頭:knowledge 同族頂層欄位不同 → 紅", any(x["code"] == "DUP_NAME_DIFF" for x in K["VRN|central_registry|VRN_Plain_SSOT"]["flags"]))
    chk("⑤ R5 regex 跨冊拷貝:同 pattern 在 DocClass 與 S05 → 兩鍵黃、不紅",
        K["VRN|central_registry|VIA_VRN_DocClass_SSOT"]["lamp"] == "YELLOW" and K["VRN|central_registry|VRN_S05_FieldRegistry"]["lamp"] == "YELLOW"
        and all(x["code"] == "REGEX_COPY" for x in K["VRN|central_registry|VIA_VRN_DocClass_SSOT"]["flags"]))
    chk("⑥ 同族 json/csv 兩鍵都乾淨(鍵帶 ext 不互撞)", K["VRN|central_registry|VRN_Verified_Module_Registry"]["lamp"] == "GREEN"
        and K["VRN|central_registry|VRN_Verified_Module_Registry|csv"]["lamp"] == "GREEN")
    chk("⑦ 計:鍵 6 · 紅 2 · 黃 2 · 乾淨 2 · R6 灰(未下放)", det["summary"] == {"keys": 6, "red": 2, "yellow": 2, "clean": 2}
        and [g for g in det["global"] if g["rule"] == "R6"][0]["lamp"] == "GRAY")
    dry = issue(apply=False, P=P)
    chk("⑧ issue dry-run:擬發 4(黃不擋)· 擋 2 · 冊未寫", len(dry["issued"]) == 4 and len(dry["blocked"]) == 2 and not (P["registry"] / _NUM_BOOK).exists())
    ap = issue(apply=True, P=P)
    book = _load_json(P["registry"] / _NUM_BOOK)
    nos = sorted(e["ssot_no"] for e in book["entries"])
    chk("⑨ issue --apply:接 ItemNumbers BOOK0003 之後 → 0004..0007 · 冊寫入 · 擋號 2 留白",
        nos == ["SSOT-VCGC-VRN-BOOK0004", "SSOT-VCGC-VRN-BOOK0005", "SSOT-VCGC-VRN-BOOK0006", "SSOT-VCGC-VRN-BOOK0007"]
        and len(book["blocked"]) == 2 and book["next_seq"] == 8)
    ap2 = issue(apply=True, P=P)
    book2 = _load_json(P["registry"] / _NUM_BOOK)
    chk("⑩ 冪等:再發 0 · 已有 4 · 號一字不變", len(ap2["issued"]) == 0 and ap2["already"] == 4
        and sorted(e["ssot_no"] for e in book2["entries"]) == nos)
    # 號跟鍵走:冊內容改(sha 變),號不變只記 history
    e_doc = ents["VRN|central_registry|VIA_VRN_DocClass_SSOT"]
    _w(P["vrn_ssot"] / "VRN_DocClass_SSOT_v0101.json", {"classes": ["個股", "產業"]})
    e_doc["sha256"] = _sha(P["vrn_ssot"] / "VRN_DocClass_SSOT_v0101.json")
    _w(P["vrn_reg"] / "VRN_SSOT_Index_v0100.json", {"schema": "VRN_SSOT_Index", "entries": ents})
    ap3 = issue(apply=True, P=P)
    book3 = _load_json(P["registry"] / _NUM_BOOK)
    doc = [e for e in book3["entries"] if e["key"] == "VRN|central_registry|VIA_VRN_DocClass_SSOT"][0]
    chk("⑪ 號跟鍵走:冊改版 sha 變 → 號不變 · sha_history +1 · 不重發", doc["ssot_no"] == "SSOT-VCGC-VRN-BOOK0004"
        and len(doc.get("sha_history", [])) == 1 and len(ap3["issued"]) == 0)
    # R3 重號:Index 自填一個別鍵的號
    ents["VRN|central_registry|VRN_Plain_SSOT"]["ssot_no"] = "SSOT-VCGC-VRN-BOOK0004"
    _w(P["vrn_reg"] / "VRN_SSOT_Index_v0100.json", {"schema": "VRN_SSOT_Index", "entries": ents})
    d3 = detect(P)
    chk("⑫ R3 重號:Index 手抄別鍵的號 → 紅 DUP_NO", any(x["code"] == "DUP_NO" for x in d3["keys"]["VRN|central_registry|VRN_Plain_SSOT"]["flags"]))
    card = write_card(ap3, P)
    txt = Path(card["md"]).read_text(encoding="utf-8")
    chk("⑬ 衝突卡:md+json 落 docs/handoff/ai · 含紅表/黃表/發號表 · 結尾 NEXT:",
        Path(card["json"]).exists() and "## 紅" in txt and "## 黃" in txt and txt.rstrip().splitlines()[-1].startswith("NEXT:"))
    chk("⑭ 只寫兩處:registry 新增 1 冊(發號冊)· VRN/SSOT 與 Index 由夾具改,引擎未另寫",
        (P["registry"] / _NUM_BOOK).exists() and len(list(P["registry"].glob("VIA_SSOT_Numbers_*"))) == 1)
    body = ME.read_text(encoding="utf-8")
    chk("⑮ 帶加速器橋 · VIA_FROM_VCGC 閘", "[VIA:ACCEL-BRIDGE:v0100]" in body and "VIA_FROM_VCGC" in body)
    os.environ.pop("VIA_ROOT", None)
    shutil.rmtree(td, ignore_errors=True)
    print("[計] %s 自測 %d/%d · %s" % (NAME, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
