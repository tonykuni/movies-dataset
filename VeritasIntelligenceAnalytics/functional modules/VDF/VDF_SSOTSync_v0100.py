#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_SSOTSync v0100 — VDF 側的 SSOT / 正則 / 同義字 / 參數 / 政策邏輯 編號協作(與 VRN2_SSOTSync 同一份協定)

操作員令(2026-10-29 政策;2026-11-01 重申):「SSOT REGEX 同義字 邏輯 政策等由 VDF VRN 生成 · 經 VCGC 檢測後無衝突給予編號 ·
  VDF VRN 自動擷取編號 · 若有衝突由我跟 AI 解決後 VCGC 檢測無誤後給予編號及更新修正內容 · 子系統自動識別編號及更新內容 ·
  三個系統的 SSOT REGEX 同義字 政策 邏輯的帳本是相同的」。三系統各自獨立;本工具只做 VDF 這一側(不寫 VRN-2 / VCGC 的任何檔):
  register 掃 VDF 自己的東西 → 登記冊 registry/VDF_SSOT_Register_vNNNN.json(暫編 VDF-<類>-####;鍵不變號不變;只增不減,
           消失的條目標「退役(保留)」;內容有變才出新版號冊)
             SSOT  VDF 夾的 VDF_*_vNNNN.json 冊(每族尾版;指紋 = 排序後 JSON 的 SHA-256 前 16)
             CFG   冊名含 Rule 的(政策 / 邏輯規則冊)
             REGEX VDF 尾版程式 re.compile / match / search / fullmatch / findall / finditer / sub / split 的字面正則 + 冊上 *_regex / rx / pattern 欄
             SYN   ENG053 UNIFIED_ALIAS(別名 → 統一參數路徑)
             PARAM VDF_Param_Registry canonical(裁定值)+ VDF_Unified_Params 葉值
  request 登記冊 → contract/VDF_NUMBER_REQUEST_latest.json(欄位同 VRN-2:key · kind · vcgc_kind · proposed_no · ssot_id 空白 · fingerprint ·
           version · src · status;多一欄 content = 正則原文 / 同義對照 / 參數值,讓 VCGC 跨系統比內容)+ VDF 內部自撞
  apply   讀 VCGC 核發冊 VCGC_NUMBER_GRANT_latest.json({grants:{鍵或暫編號: 核發號}, conflicts:[{key, with, why}]};
           找 contract/ · <VIA>/VCGC/contract/ · <VIA>/supportive modules/registry/ · <VIA>/VIA_Reports/vcgc/)→ 登記冊填 ssot_id ·
           「已確認(VCGC)」/「衝突 · 待人判(VCGC)」→ contract/VDF_NUMBER_STATE_latest.json
  sync    register → apply → request(ActivateVDF 每輪跑)
VDF 自己的模組:VCGC 的核發冊只讀;零網路;不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib。
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


import ast
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
TAG = "VDF_SSOTSync v" + Path(__file__).stem.rsplit("_v", 1)[-1]
REQUEST_NAME = "VDF_NUMBER_REQUEST_latest.json"
STATE_NAME = "VDF_NUMBER_STATE_latest.json"
GRANT_NAME = "VCGC_NUMBER_GRANT_latest.json"
REG_GLOB = "VDF_SSOT_Register_v[0-9][0-9][0-9][0-9].json"
VCGC_KIND = {"SSOT": "SSOT", "CFG": "PLCY", "REGEX": "RGX", "SYN": "SYN", "PARAM": "PRMT"}
SHORT = {"SSOT": "SSOT", "CFG": "CFG", "REGEX": "RGX", "SYN": "SYN", "PARAM": "PRM"}
RE_FUNCS = {"compile", "match", "search", "fullmatch", "findall", "finditer", "sub", "subn", "split"}
RX_KEYS = re.compile(r"(?:^|_)(?:regex|rx|pattern)$", re.I)


def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _sha16(s) -> str:
    return hashlib.sha256((s if isinstance(s, bytes) else str(s).encode("utf-8"))).hexdigest()[:16]


def _tails(paths) -> list:
    fam = {}
    for p in paths:
        m = re.match(r"(.+)_v(\d{4})$", p.stem)
        if not m:
            continue
        k = (str(p.parent), m.group(1), p.suffix)
        if k not in fam or int(m.group(2)) > _vnum(fam[k]):
            fam[k] = p
    return sorted(fam.values())


# ---------------------------------------------------------------- 掃 VDF 自己的東西
SKIPPED: list = []          # 上一次 harvest 略過的(讀不到的冊 · 不合法的正則 · 剖析不了的程式)— 照實報,不默吞


def harvest(vdf: Path = HERE) -> dict:
    items = {}
    SKIPPED.clear()

    def put(kind, key, fp, version=None, src=None, content=None, note=""):
        items.setdefault(key, {"kind": kind, "key": key, "fp": fp, "version": version, "src": [], "content": content, "note": note})
        if src and src not in items[key]["src"]:
            items[key]["src"].append(src)

    books = _tails([p for p in vdf.glob("VDF_*_v[0-9][0-9][0-9][0-9].json")])
    for p in books:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            SKIPPED.append("%s(%s)" % (p.name, type(exc).__name__))
            continue
        fam = re.sub(r"_v\d{4}$", "", p.stem)
        kind = "CFG" if "Rule" in fam else "SSOT"
        put(kind, "VDF:%s:%s" % (SHORT[kind], fam), _sha16(json.dumps(d, ensure_ascii=False, sort_keys=True)), p.stem[-5:], p.name)

        def walk(o, path=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    if isinstance(v, str) and RX_KEYS.search(str(k)) and len(v) >= 2:
                        try:
                            re.compile(v)
                        except re.error as exc:
                            SKIPPED.append("%s#%s%s(壞正則:%s)" % (p.name, path, k, exc))
                            continue
                        put("REGEX", "VDF:RGX:" + _sha16(v), _sha16(v), None, "%s#%s%s" % (p.name, path, k), v)
                    else:
                        walk(v, path + str(k) + ".")
            elif isinstance(o, list):
                for x in o:
                    walk(x, path)
        walk(d)
    pys = _tails([p for p in list(vdf.glob("VDF_*_v[0-9][0-9][0-9][0-9].py")) + list((vdf / "engine").glob("VDF_*_v[0-9][0-9][0-9][0-9].py"))])
    for p in pys:
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError as exc:
            SKIPPED.append("%s(SyntaxError L%s)" % (p.name, exc.lineno))
            continue
        for n in ast.walk(tree):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in RE_FUNCS and isinstance(n.func.value, ast.Name)
                    and n.func.value.id == "re" and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)):
                pat = n.args[0].value
                if len(pat) < 2:
                    continue
                put("REGEX", "VDF:RGX:" + _sha16(pat), _sha16(pat), None, "%s:%d" % (p.name, n.lineno), pat)
            if (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "UNIFIED_ALIAS" for t in n.targets) and isinstance(n.value, ast.Dict)):
                try:
                    alias = ast.literal_eval(n.value)
                except ValueError:
                    alias = {}
                for a, c in sorted(alias.items()):
                    put("SYN", "VDF:SYN:%s" % a, _sha16("%s=%s" % (a, c)), None, p.name, {"alias": a, "canonical": c})
    pr = max(vdf.glob("VDF_Param_Registry_v[0-9][0-9][0-9][0-9].json"), key=_vnum, default=None)
    if pr:
        try:
            canon = json.loads(pr.read_text(encoding="utf-8")).get("canonical") or {}
        except (OSError, ValueError):
            canon = {}
        for name, v in sorted(canon.items()):
            val = (v or {}).get("ruling") if isinstance(v, dict) else v
            put("PARAM", "VDF:PRM:%s" % name, _sha16("%s=%s" % (name, val)), pr.stem[-5:], pr.name, {"name": name, "value": val})
    up = max(vdf.glob("VDF_Unified_Params_v[0-9][0-9][0-9][0-9].json"), key=_vnum, default=None)
    if up:
        try:
            u = json.loads(up.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            u = {}

        def leaves(o, path=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ("schema", "note"):
                        continue
                    yield from leaves(v, path + k + ".")
            else:
                yield path[:-1], o
        for path, val in leaves(u):
            put("PARAM", "VDF:PRM:unified.%s" % path, _sha16("%s=%s" % (path, json.dumps(val, ensure_ascii=False, sort_keys=True))), up.stem[-5:], up.name,
                {"name": path, "value": val})
    return items


# ---------------------------------------------------------------- 登記冊(VDF 自己的帳本)
def latest_register(vdf: Path = HERE) -> Path | None:
    hits = sorted((vdf / "registry").glob(REG_GLOB), key=_vnum) if (vdf / "registry").is_dir() else []
    return hits[-1] if hits else None


def register(vdf: Path = HERE, items: dict | None = None) -> dict:
    items = harvest(vdf) if items is None else items
    reg = latest_register(vdf)
    book = json.loads(reg.read_text(encoding="utf-8")) if reg else {"entries": {}}
    entries = book.get("entries") or {}
    used = {}
    for e in entries.values():
        m = re.match(r"VDF-([A-Z]+)-(\d{4})$", str(e.get("no") or ""))
        if m:
            used[m.group(1)] = max(used.get(m.group(1), 0), int(m.group(2)))
    changed, ts = 0, now()
    for key in sorted(items):
        it = items[key]
        e = entries.get(key)
        if e is None:
            sk = SHORT[it["kind"]]
            used[sk] = used.get(sk, 0) + 1
            entries[key] = {"no": "VDF-%s-%04d" % (sk, used[sk]), "kind": it["kind"], "vcgc_kind": VCGC_KIND[it["kind"]], "key": key, "fp": it["fp"],
                            "version": it["version"], "src": it["src"][:5], "content": it["content"], "status": "暫編 · 待 VCGC 核號", "ssot_id": "",
                            "first": ts, "last": ts, "note": it.get("note") or ""}
            changed += 1
            continue
        if e.get("fp") != it["fp"] or str(e.get("status", "")).startswith("退役"):
            e.update(fp=it["fp"], version=it["version"], content=it["content"], last=ts)
            e["src"] = it["src"][:5]
            if str(e.get("status", "")).startswith(("已確認", "退役")):        # 內容改了 → 重新送 VCGC 檢測(核發號保留給 VCGC 決定沿用或改)
                e["status"] = "內容更新 · 待 VCGC 重檢"
            changed += 1
    for key, e in entries.items():
        if key not in items and not str(e.get("status", "")).startswith("退役"):
            e["status"] = "退役(保留)"
            e["last"] = ts
            changed += 1
    out = reg
    if changed or reg is None:
        nv = (_vnum(reg) + 1) if reg else 100
        out = vdf / "registry" / ("VDF_SSOT_Register_v%04d.json" % nv)
        out.parent.mkdir(parents=True, exist_ok=True)
        book.update(schema="VIA.VDF.SSOTRegister.v1", at=ts, writer=TAG, prior=reg.name if reg else None, entries=entries,
                    rule="VDF 的 SSOT / 正則 / 同義字 / 參數 / 政策邏輯帳本(唯一寫入者 = VDF_SSOTSync):暫編 VDF-<類>-#### · 鍵不變號不變 · 只增不減 · "
                         "ssot_id = VCGC 核發號(三系統共用帳本的號)· 內容有變才出新版號冊")
        out.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    cnt = {}
    for e in entries.values():
        cnt[e["kind"]] = cnt.get(e["kind"], 0) + 1
    return {"verb": "register", "skipped": list(SKIPPED), "register": out.name, "prior": reg.name if (reg and out != reg) else None, "changed": changed, "entries": len(entries), "by_kind": cnt,
            "written": out != reg}


def grant_paths(vdf: Path = HERE) -> list:
    via = vdf.parents[1]
    return [vdf / "contract" / GRANT_NAME, via / "VCGC" / "contract" / GRANT_NAME, via / "supportive modules" / "registry" / GRANT_NAME,
            via / "VIA_Reports" / "vcgc" / GRANT_NAME]


def read_grant(vdf: Path = HERE) -> tuple:
    grants, conflicts, srcs = {}, [], []
    for gp in grant_paths(vdf):
        if not gp.is_file():
            continue
        try:
            g = json.loads(gp.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            srcs.append("%s(讀不到:%s)" % (gp, type(exc).__name__))      # 照實列在一行裡,不默吞
            continue
        srcs.append(str(gp))
        for k, v in (g.get("grants") or {}).items():
            if isinstance(v, str) and v.strip():
                grants[k] = v.strip()
        conflicts += [c for c in g.get("conflicts") or [] if isinstance(c, dict) and c.get("key")]
    return grants, conflicts, srcs


def apply(vdf: Path = HERE, inplace: bool = False) -> dict:
    """inplace=True:同一輪 sync 剛寫的新版冊直接補號,不再多出一版(冊只在內容或核號有變時增版)。"""
    reg = latest_register(vdf)
    if not reg:
        return {"verb": "apply", "lamp": "GRAY", "why": "沒有登記冊(先 register)"}
    book = json.loads(reg.read_text(encoding="utf-8"))
    entries = book.get("entries") or {}
    grants, conflicts, srcs = read_grant(vdf)
    conf = {}
    for c in conflicts:
        conf.setdefault(c["key"], []).append(c)
    granted, conflicted, changed = [], [], 0
    for key, e in entries.items():
        if str(e.get("status", "")).startswith("退役"):
            continue
        hit = grants.get(key) or grants.get(e.get("no") or "")
        cf = conf.get(key) or conf.get(e.get("no") or "")
        if hit and not cf:
            if e.get("ssot_id") != hit or not str(e.get("status", "")).startswith("已確認"):
                e.update(ssot_id=hit, status="已確認(VCGC)", granted_at=now())
                changed += 1
            granted.append(key)
        elif cf:
            st = "衝突 · 待人判(VCGC)· " + " / ".join("%s:%s" % (c.get("with", "?"), c.get("why", "")) for c in cf)[:300]
            if e.get("status") != st:
                e.update(status=st)
                changed += 1
            conflicted.append(key)
    out = reg
    if changed:
        out = reg if inplace else reg.with_name("VDF_SSOT_Register_v%04d.json" % (_vnum(reg) + 1))
        book.update(at=now(), prior=reg.name, writer="%s(核號同步)" % TAG, entries=entries)
        out.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    pending = [k for k, e in entries.items() if str(e.get("status", "")).startswith(("暫編", "內容更新"))]
    state = {"engine": TAG, "verb": "apply", "at": now(), "lamp": "YELLOW" if conflicted else ("GREEN" if not pending else "YELLOW"),
             "register": out.name, "prior_register": reg.name if out != reg else None, "grant_sources": srcs, "granted": len(granted), "conflicts": len(conflicted),
             "pending": len(pending), "changed": changed, "conflict_keys": conflicted[:50], "pending_keys": pending[:50]}
    (vdf / "contract").mkdir(parents=True, exist_ok=True)
    (vdf / "contract" / STATE_NAME).write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    return state


def request(vdf: Path = HERE) -> dict:
    reg = latest_register(vdf)
    if not reg:
        return {"verb": "request", "lamp": "GRAY", "why": "沒有登記冊(先 register)"}
    entries = json.loads(reg.read_text(encoding="utf-8")).get("entries") or {}
    items, seen, self_c = [], {}, []
    for key, e in sorted(entries.items()):
        if str(e.get("status", "")).startswith(("退役", "已確認")):
            continue
        items.append({"key": key, "entry": key, "kind": e["kind"], "vcgc_kind": e.get("vcgc_kind") or VCGC_KIND.get(e["kind"], "SSOT"), "proposed_no": e.get("no"),
                      "ssot_id": e.get("ssot_id") or "", "fingerprint": e.get("fp"), "version": e.get("version"), "src": (e.get("src") or [None])[0],
                      "status": e.get("status"), "note": e.get("note") or "", "content": e.get("content")})
        if e["kind"] == "SYN":
            a = (e.get("content") or {}).get("alias")
            c = (e.get("content") or {}).get("canonical")
            if a in seen and seen[a] != c:
                self_c.append({"key": key, "kind": "SYN", "why": "同一別名 %s 對到兩個統一路徑 %s / %s" % (a, seen[a], c)})
            seen.setdefault(a, c)
    req = {"from": "VDF", "subsystem": "VDF(VIA-02 資料鍛造 · 獨立 MAIN ActivateVDF)", "engine": TAG, "ts": now(), "register": reg.name,
           "rule": "子系統提出時 ssot_id 空白;VCGC 偵測三系統衝突 → 使用者 + AI 修到無誤 → VCGC 寫 VCGC_NUMBER_GRANT_latest.json {grants:{鍵或暫編號: 核發號}, "
                   "conflicts:[{key, with, why}]} → VDF apply 讀到就補 ssot_id(三系統共用帳本的號)",
           "pending": [i["proposed_no"] for i in items], "ssot_items": items, "program_items": [], "self_conflicts": self_c,
           "counts": {"ssot_like": len(items), "program": 0, "self_conflicts": len(self_c)}}
    (vdf / "contract").mkdir(parents=True, exist_ok=True)
    (vdf / "contract" / REQUEST_NAME).write_text(json.dumps(req, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return {"verb": "request", "lamp": "YELLOW" if self_c else "GREEN", "pending": len(items), "self_conflicts": len(self_c), "file": str(vdf / "contract" / REQUEST_NAME)}


def sync(vdf: Path = HERE) -> dict:
    r = register(vdf)
    a = apply(vdf, inplace=bool(r.get("written")))
    q = request(vdf)
    lamp = "YELLOW" if "YELLOW" in (a.get("lamp"), q.get("lamp")) else a.get("lamp", "GREEN")
    line = "[VDF 編號同步] %s · 登記 %d 條(%s)· 核發 %d · 衝突 %d · 待核號 %d · 自撞 %d · 冊 %s%s · 核發冊 %s%s" % (
        lamp, r["entries"], " · ".join("%s %d" % kv for kv in sorted(r["by_kind"].items())), a.get("granted", 0), a.get("conflicts", 0), a.get("pending", 0),
        q.get("self_conflicts", 0), a.get("register") or r["register"], "(新版)" if (r.get("prior") or a.get("prior_register")) else "",
        " · ".join(Path(x).name for x in a.get("grant_sources") or []) or "尚無(VCGC 還沒核發)",
        (" · 略過 %d(%s)" % (len(r["skipped"]), " ; ".join(r["skipped"][:3]))) if r.get("skipped") else "")
    return {"verb": "sync", "lamp": lamp, "register": r, "apply": a, "request": q, "line": line}


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    verb = a[0] if a else "sync"
    fn = {"register": register, "request": request, "apply": apply, "sync": sync}.get(verb)
    if fn is None:
        print("用法:python %s register | request | apply | sync · --selftest" % Path(__file__).name)
        return 2
    r = fn()
    print(r["line"] if "line" in r else json.dumps(r, ensure_ascii=False, indent=1, default=str))
    return 0 if r.get("lamp") in ("GREEN", "YELLOW", None) else 1


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s · 自測(登記 → 請求 → 核發 → 套號;只寫 VDF 自己的夾)===" % TAG)
    real = harvest(HERE)
    kinds = {}
    for it in real.values():
        kinds[it["kind"]] = kinds.get(it["kind"], 0) + 1
    chk("① 掃本倉 VDF:%s" % kinds, all(kinds.get(k) for k in ("SSOT", "CFG", "REGEX", "SYN", "PARAM")) and "VDF:SYN:START_DATE" in real
        and real["VDF:SYN:START_DATE"]["content"]["canonical"] == "time.start_date", kinds)
    tmp = Path(tempfile.mkdtemp(prefix="vdf_ssot_"))
    try:
        via = tmp / "VIA"
        vdf = via / "functional modules" / "VDF"
        (vdf / "engine").mkdir(parents=True)
        (via / "supportive modules" / "registry").mkdir(parents=True)
        (vdf / "VDF_InputUniverse_SSOT_v0100.json").write_text(json.dumps({"code_regex": "^[1-9]\\d{3}$", "x": 1}), encoding="utf-8")
        (vdf / "VDF_AdjPrice_Rule_SSOT_v0100.json").write_text(json.dumps({"rule": "原始永不改"}), encoding="utf-8")
        (vdf / "engine" / "VDF_ENG053_ParamEngineMap_v0100.py").write_text(
            "import re\nUNIFIED_ALIAS = {'START_DATE': 'time.start_date', 'TIMEOUT': 'fetch.timeout_s'}\nX = re.compile(r'^00\\d{3}A$')\n", encoding="utf-8")
        r1 = register(vdf)
        reg1 = json.loads((vdf / "registry" / r1["register"]).read_text(encoding="utf-8"))["entries"]
        nos = sorted(e["no"] for e in reg1.values())
        chk("② register:SSOT 1 · CFG 1 · REGEX 2(冊上 code_regex + 程式 re.compile)· SYN 2 · 暫編 VDF-<類>-#### · 冊 %s" % r1["register"],
            r1["by_kind"] == {"SSOT": 1, "CFG": 1, "REGEX": 2, "SYN": 2} and "VDF-RGX-0001" in nos and r1["register"] == "VDF_SSOT_Register_v0100.json", (r1, nos))
        r1b = register(vdf)
        chk("③ 再登記一次:沒變 → 不出新版 · 號不變", r1b["changed"] == 0 and r1b["register"] == r1["register"])
        q = request(vdf)
        rq = json.loads((vdf / "contract" / REQUEST_NAME).read_text(encoding="utf-8"))
        chk("④ request:欄位同 VRN-2(key · kind · vcgc_kind · proposed_no · ssot_id 空白 · fingerprint)+ content · from VDF · 待核號 %d" % q["pending"],
            rq["from"] == "VDF" and q["pending"] == 6 and all(i["ssot_id"] == "" and i["proposed_no"] and i["fingerprint"] for i in rq["ssot_items"])
            and any(i["kind"] == "REGEX" and i["content"] == "^00\\d{3}A$" for i in rq["ssot_items"]))
        syn_key = "VDF:SYN:START_DATE"
        rx_no = next(e["no"] for e in reg1.values() if e["kind"] == "REGEX")
        (via / "supportive modules" / "registry" / GRANT_NAME).write_text(json.dumps({"grants": {syn_key: "VIA-SYN-0007", rx_no: "VIA-RGX-0042"},
                                                                                     "conflicts": [{"key": "VDF:SYN:TIMEOUT", "with": "VRN-2",
                                                                                                    "why": "同別名對到不同統一路徑"}]}), encoding="utf-8")
        a = apply(vdf)
        reg2 = json.loads((vdf / "registry" / a["register"]).read_text(encoding="utf-8"))["entries"]
        chk("⑤ apply:核發號補進 ssot_id(依鍵或暫編號都認)· 衝突標待人判 · 出新版冊 %s · 狀態冊寫好" % a["register"],
            reg2[syn_key]["ssot_id"] == "VIA-SYN-0007" and reg2[syn_key]["status"] == "已確認(VCGC)" and any(e["ssot_id"] == "VIA-RGX-0042" for e in reg2.values())
            and reg2["VDF:SYN:TIMEOUT"]["status"].startswith("衝突") and a["granted"] == 2 and a["conflicts"] == 1 and (vdf / "contract" / STATE_NAME).is_file())
        q2 = request(vdf)
        chk("⑥ 已確認的不再送(待核號 6 → %d)" % q2["pending"], q2["pending"] == 4)
        (vdf / "engine" / "VDF_ENG053_ParamEngineMap_v0100.py").write_text(
            "import re\nUNIFIED_ALIAS = {'START_DATE': 'time.begin', 'TIMEOUT': 'fetch.timeout_s'}\n", encoding="utf-8")
        r3 = register(vdf)
        reg3 = json.loads((vdf / "registry" / r3["register"]).read_text(encoding="utf-8"))["entries"]
        chk("⑦ 內容改了 → 已確認的轉「內容更新 · 待 VCGC 重檢」· 消失的正則標「退役(保留)」不刪 · 號不變",
            reg3[syn_key]["status"].startswith("內容更新") and reg3[syn_key]["no"] == reg1[syn_key]["no"]
            and any(e["status"].startswith("退役") for e in reg3.values() if e["kind"] == "REGEX") and len(reg3) == len(reg2))
        s = sync(vdf)
        chk("⑧ sync 一行:%s" % s["line"][:110], s["line"].startswith("[VDF 編號同步]") and "核發冊 " + GRANT_NAME in s["line"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑨ VDF 獨立:不匯入他系統程式 · 兩座橋在 · VCGC 核發冊只讀(本檔不寫 grant)· 零網路 · 同意閘不讀不寫",
        not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC|requests|httpx|urllib\.request)", src, re.M) and "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and "GRANT_NAME).write" not in body and "CONSENT" not in body)
    print("[計] %s 自測 %d/%d · %s" % (TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
