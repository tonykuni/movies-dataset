#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_SSOTSync v0100 — VDF 側的 SSOT / 正則 / 同義字 / 參數 / 政策 編號協作(號只由 VCGC 中央編號發;VDF 不自發號)

操作員令(2026-10-29 政策;2026-11-01 重申):「SSOT REGEX 同義字 邏輯 政策等由 VDF VRN 生成 · 經 VCGC 檢測後無衝突給予編號 ·
  VDF VRN 自動擷取編號 · 若有衝突由我跟 AI 解決後 VCGC 檢測無誤後給予編號及更新修正內容 · 子系統自動識別編號及更新內容 ·
  三個系統的 SSOT REGEX 同義字 政策 邏輯的帳本是相同的」。三系統各自獨立;本工具只做 VDF 這一側(不寫 VRN-2 / VCGC 的任何檔)。
  帳本只有一本:VCGC 中央編號(CGC_MDL237 · VIA_Numbering_SSOT / VIA_NumberBooks;號 VIA-VDF-<類>NNN)。VDF 的登記冊只是鏡像:
  ssot_id = 中央號。

  register 掃 VDF 自己「宣告」的東西 → 登記冊 registry/VDF_SSOT_Register_vNNNN.json(暫編 VDF-<類>-#### 只是 VDF 內部追蹤號,
           不是中央號;鍵不變號不變;只增不減,消失的條目標「退役(保留)」;內容有變才出新版冊)
             SSOT  VDF 夾的 VDF_*_vNNNN.json 冊(每族尾版;指紋 = 排序後 JSON 的 SHA-256 前 16)
             CFG   冊名含 Rule 的(政策 / 邏輯規則冊)→ VCGC 類 POLICY
             REGEX 冊上宣告的 *_regex / rx / pattern 欄(鍵 = 冊族 + 位置,物件有 id 用 id);同物件的 <欄>_positive / <欄>_negative
                   清單當正反例(VCGC 正則契約要正反例;沒附 = VCGC 擋下待人判)。程式裡的實作用正則不是帳本資產,不登。
             SYN   UNIFIED_ALIAS(別名 → 統一參數路徑)
             PARAM VDF_Param_Registry canonical(裁定值)+ VDF_Unified_Params 葉值 → VCGC 類 CNFG
           版本:每條一個 semver(1.0.0 起)。已有中央號後內容再變 → 升 minor、supersedes = 舊版(VCGC 規定同版不得改內容)。
  request 登記冊 → contract/VDF_NUMBER_REQUEST_latest.json:每條附 asset = VCGC 候選契約(CGC_MDL237 v0114 欄位;ssot_code 一律 null,
           候選身分 = source_id · source_pointer(= 登記鍵)· candidate_id,與檔名版號無關)+ 舊欄(key · kind · proposed_no · ssot_id 空白 …)
  apply   讀 VCGC 核發冊 VCGC_NUMBER_GRANT_latest.json({grants:{鍵: 中央號}, assets:{鍵: {code, version, source_sha256}},
           conflicts:[{key, with, why}]})→ 版本與內容都對得上才「已確認(VCGC)」;中央那版內容跟 VDF 現況不同 → 升版重送;
           衝突 →「衝突 · 待人判(VCGC)」→ contract/VDF_NUMBER_STATE_latest.json
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
ASSET_TYPE = {"SSOT": "SSOT", "CFG": "POLICY", "REGEX": "REGEX", "SYN": "SYNONYM", "PARAM": "CNFG"}
KIND_ZH = {"SSOT": "冊", "CFG": "政策冊", "REGEX": "正則", "SYN": "同義字", "PARAM": "參數"}
SCOPE = {"SSOT": "vdf.ssot", "CFG": "vdf.policy", "SYN": "vdf.unified_alias", "PARAM": "vdf.param"}
RISK = {"SSOT": "LOW", "CFG": "MED", "REGEX": "MED", "SYN": "LOW", "PARAM": "LOW"}
SOURCE_ID = "vdf-ssotsync:VDF_SSOT_Register"          # 候選身分的來源(固定;登記鍵當 source_pointer)
ENVIRONMENT = "via_core"
# VCGC 候選契約欄位(CGC_MDL237 v0114 REQUIRED_FIELDS 的抄錄,只供本檔自檢;VCGC 端才是正本)
CANDIDATE_FIELDS = ("candidate_id", "ssot_code", "asset_type", "owner", "source_id", "source_pointer", "source_sha256", "version", "supersedes",
                    "scope", "semantic_key", "name", "value", "risk_level", "environment", "libraries", "aliases", "positive", "negative")
RX_KEYS = re.compile(r"(?:^|_)(?:regex|rx|pattern)$", re.I)
SKIPPED: list = []          # 上一次 harvest 略過的(讀不到的冊 · 不合法的正則 · 剖析不了的程式)— 照實報,不默吞


def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _sha(s, n=64) -> str:
    return hashlib.sha256((s if isinstance(s, bytes) else str(s).encode("utf-8"))).hexdigest()[:n]


def _sha16(s) -> str:
    return _sha(s, 16)


def _canon(o) -> str:
    return json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _bump(v: str) -> str:
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(v or ""))
    return "%d.%d.0" % (int(m.group(1)), int(m.group(2)) + 1) if m else "1.0.0"


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


# ---------------------------------------------------------------- 掃 VDF 自己宣告的東西
def harvest(vdf: Path = HERE) -> dict:
    items = {}
    SKIPPED.clear()

    def put(kind, key, fp, version=None, src=None, content=None, note=""):
        items.setdefault(key, {"kind": kind, "key": key, "fp": fp, "version": version, "src": [], "content": content, "note": note})
        if src and src not in items[key]["src"]:
            items[key]["src"].append(src)

    for p in _tails([p for p in vdf.glob("VDF_*_v[0-9][0-9][0-9][0-9].json")]):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            SKIPPED.append("%s(%s)" % (p.name, type(exc).__name__))
            continue
        fam = re.sub(r"_v\d{4}$", "", p.stem)
        kind = "CFG" if "Rule" in fam else "SSOT"
        put(kind, "VDF:%s:%s" % (SHORT[kind], fam), _sha16(_canon(d)), p.stem[-5:], p.name, {"family": fam})

        def walk(o, path=""):
            if isinstance(o, dict):
                tag = o.get("id") if isinstance(o.get("id"), str) and o.get("id").strip() else None
                base = path + (tag + "." if tag else "")
                for k, v in o.items():
                    if isinstance(v, str) and RX_KEYS.search(str(k)) and len(v) >= 2:
                        try:
                            re.compile(v)
                        except re.error as exc:
                            SKIPPED.append("%s#%s%s(壞正則:%s)" % (p.name, base, k, exc))
                            continue
                        pos = [x for x in o.get(str(k) + "_positive") or [] if isinstance(x, str) and x.strip()]
                        neg = [x for x in o.get(str(k) + "_negative") or [] if isinstance(x, str) and x.strip()]
                        anchor = base + str(k)
                        put("REGEX", "VDF:RGX:%s:%s" % (fam, anchor), _sha16(_canon([v, pos, neg])), p.stem[-5:], "%s#%s" % (p.name, anchor),
                            {"pattern": v, "positive": pos, "negative": neg, "book": fam, "anchor": anchor, "field": str(k)})
                    elif isinstance(v, (dict, list)):
                        walk(v, base + str(k) + ".")
            elif isinstance(o, list):
                for i, x in enumerate(o):
                    has_id = isinstance(x, dict) and isinstance(x.get("id"), str) and x.get("id").strip()
                    walk(x, path if has_id else "%s[%d]." % (path, i))
        walk(d)
    pys = _tails([p for p in list(vdf.glob("VDF_*_v[0-9][0-9][0-9][0-9].py")) + list((vdf / "engine").glob("VDF_*_v[0-9][0-9][0-9][0-9].py"))])
    for p in pys:
        txt = p.read_text(encoding="utf-8", errors="replace")
        if "UNIFIED_ALIAS" not in txt:
            continue
        try:
            tree = ast.parse(txt)
        except SyntaxError as exc:
            SKIPPED.append("%s(SyntaxError L%s)" % (p.name, exc.lineno))
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "UNIFIED_ALIAS" for t in n.targets) and isinstance(n.value, ast.Dict):
                try:
                    alias = ast.literal_eval(n.value)
                except ValueError:
                    SKIPPED.append("%s:UNIFIED_ALIAS L%d(不是字面字典)" % (p.name, n.lineno))
                    continue
                for a, c in sorted(alias.items()):
                    put("SYN", "VDF:SYN:%s" % a, _sha16("%s=%s" % (a, c)), None, p.name, {"alias": a, "canonical": c})
    pr = max(vdf.glob("VDF_Param_Registry_v[0-9][0-9][0-9][0-9].json"), key=_vnum, default=None)
    if pr:
        try:
            canon = json.loads(pr.read_text(encoding="utf-8")).get("canonical") or {}
        except (OSError, ValueError) as exc:
            SKIPPED.append("%s(%s)" % (pr.name, type(exc).__name__))
            canon = {}
        for name, v in sorted(canon.items()):
            val = (v or {}).get("ruling") if isinstance(v, dict) else v
            put("PARAM", "VDF:PRM:%s" % name, _sha16("%s=%s" % (name, val)), pr.stem[-5:], pr.name, {"name": name, "value": val})
    up = max(vdf.glob("VDF_Unified_Params_v[0-9][0-9][0-9][0-9].json"), key=_vnum, default=None)
    if up:
        try:
            u = json.loads(up.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            SKIPPED.append("%s(%s)" % (up.name, type(exc).__name__))
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
            put("PARAM", "VDF:PRM:unified.%s" % path, _sha16("%s=%s" % (path, _canon(val))), up.stem[-5:], up.name, {"name": "unified." + path, "value": val})
    return items


def asset_sha(e: dict) -> str:
    """候選內容指紋(只看鍵 · 指紋 · 內容;與檔名版號無關)= VCGC 候選的 source_sha256。"""
    return _sha(_canon({"key": e["key"], "fp": e["fp"], "content": e.get("content")}))


def build_asset(e: dict) -> dict:
    """登記條目 → VCGC 候選契約(CGC_MDL237 v0114);每欄只由鍵 + 內容決定,內容不變定義就不變。"""
    kind, c = e["kind"], e.get("content") or {}
    if kind in ("SSOT", "CFG"):
        skey, value, scope, aliases, pos, neg = c.get("family") or e["key"].split(":", 2)[-1], {"family": c.get("family"), "fingerprint": e["fp"]}, SCOPE[kind], [], [], []
    elif kind == "REGEX":
        skey, value, aliases = "%s.%s" % (c["book"], c["anchor"]), c["pattern"], []
        scope = "vdf.regex.%s.%s" % (re.sub(r"[^a-z0-9_]", "_", c["book"].lower()), re.sub(r"[^a-z0-9_]", "_", c["field"].lower()))
        pos, neg = list(c.get("positive") or []), list(c.get("negative") or [])
    elif kind == "SYN":
        skey, value, scope, aliases, pos, neg = str(c["alias"]), str(c["canonical"]), SCOPE[kind], [str(c["alias"])], [], []
    else:
        skey, value, scope, aliases, pos, neg = str(c["name"]), c.get("value"), SCOPE["PARAM"], [], [], []
    return {"candidate_id": re.sub(r"[^A-Za-z0-9_.:-]", "_", e["key"])[:400], "ssot_code": None, "asset_type": ASSET_TYPE[kind], "owner": "VDF",
            "source_id": SOURCE_ID, "source_pointer": e["key"], "source_sha256": asset_sha(e), "version": e.get("semver") or "1.0.0",
            "supersedes": e.get("supersedes"), "scope": scope, "semantic_key": skey or e["key"], "name": "VDF %s %s" % (KIND_ZH[kind], skey or e["key"]),
            "value": value, "risk_level": RISK[kind], "environment": ENVIRONMENT, "libraries": [], "aliases": aliases, "positive": pos, "negative": neg}


# ---------------------------------------------------------------- 登記冊(VDF 自己的鏡像帳)
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
            e = entries[key] = {"no": "VDF-%s-%04d" % (sk, used[sk]), "kind": it["kind"], "vcgc_kind": VCGC_KIND[it["kind"]], "key": key, "fp": it["fp"],
                                "version": it["version"], "src": it["src"][:5], "content": it["content"], "semver": "1.0.0", "supersedes": None,
                                "status": "暫編 · 待 VCGC 核號", "ssot_id": "", "first": ts, "last": ts, "note": it.get("note") or ""}
            e["sha256"] = asset_sha(e)
            changed += 1
            continue
        if e.get("fp") != it["fp"] or e.get("content") != it["content"] or str(e.get("status", "")).startswith("退役"):
            e.update(fp=it["fp"], version=it["version"], content=it["content"], last=ts)
            e["src"] = it["src"][:5]
            e["sha256"] = asset_sha(e)
            if e.get("ssot_id"):       # 中央已有一版 → 新內容 = 新版(同版不得改內容);中央號留著到 VCGC 發新版號
                e["supersedes"] = e.get("semver") or "1.0.0"
                e["semver"] = _bump(e["supersedes"])
                e["status"] = "內容更新 · 待 VCGC 重檢"
            elif str(e.get("status", "")).startswith("退役"):
                e["status"] = "暫編 · 待 VCGC 核號"
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
        book.update(schema="VIA.VDF.SSOTRegister.v2", at=ts, writer=TAG, prior=reg.name if reg else None, entries=entries,
                    rule="VDF 的 SSOT / 正則 / 同義字 / 參數 / 政策 鏡像帳(唯一寫入者 = VDF_SSOTSync):VDF-<類>-#### 是 VDF 內部追蹤號 · "
                         "ssot_id = VCGC 中央號(CGC_MDL237;三系統共用一本帳)· 鍵不變號不變 · 只增不減 · 內容有變才出新版冊 · semver 跟中央版本走")
        out.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    cnt = {}
    for e in entries.values():
        cnt[e["kind"]] = cnt.get(e["kind"], 0) + 1
    return {"verb": "register", "skipped": list(SKIPPED), "register": out.name, "prior": reg.name if (reg and out != reg) else None, "changed": changed,
            "entries": len(entries), "by_kind": cnt, "written": out != reg}


def grant_paths(vdf: Path = HERE) -> list:
    via = vdf.parents[1]
    return [vdf / "contract" / GRANT_NAME, via / "VCGC" / "contract" / GRANT_NAME, via / "supportive modules" / "registry" / GRANT_NAME,
            via / "VIA_Reports" / "vcgc" / GRANT_NAME]


def read_grant(vdf: Path = HERE) -> tuple:
    grants, assets, conflicts, srcs = {}, {}, [], []
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
        for k, v in (g.get("assets") or {}).items():
            if isinstance(v, dict) and v.get("code"):
                assets[k] = v
        conflicts += [c for c in g.get("conflicts") or [] if isinstance(c, dict) and c.get("key")]
    return grants, assets, conflicts, srcs


def apply(vdf: Path = HERE, inplace: bool = False) -> dict:
    """inplace=True:同一輪 sync 剛寫的新版冊直接補號,不再多出一版(冊只在內容或核號有變時增版)。"""
    reg = latest_register(vdf)
    if not reg:
        return {"verb": "apply", "lamp": "GRAY", "why": "沒有登記冊(先 register)"}
    book = json.loads(reg.read_text(encoding="utf-8"))
    entries = book.get("entries") or {}
    grants, assets, conflicts, srcs = read_grant(vdf)
    conf = {}
    for c in conflicts:
        conf.setdefault(c["key"], []).append(c)
    granted, conflicted, changed = [], [], 0
    for key, e in entries.items():
        if str(e.get("status", "")).startswith("退役"):
            continue
        hit = grants.get(key) or grants.get(e.get("no") or "")
        meta = assets.get(key) or {}
        cf = conf.get(key) or conf.get(e.get("no") or "")
        if cf:
            st = "衝突 · 待人判(VCGC)· " + " / ".join("%s:%s" % (c.get("with", "?"), c.get("why", "")) for c in cf)[:300]
            if hit and e.get("ssot_id") != hit:
                e["ssot_id"] = hit                        # 前一版的中央號照留(新版被擋不影響舊版身分)
            if e.get("status") != st:
                e["status"] = st
                changed += 1
            conflicted.append(key)
            continue
        if not hit:
            if str(e.get("status", "")).startswith("衝突"):     # VCGC 不再列衝突(人 + AI 修好了)→ 回到待核號,下一輪重送
                e["status"] = "內容更新 · 待 VCGC 重檢" if e.get("ssot_id") else "暫編 · 待 VCGC 核號"
                changed += 1
            continue
        same_ver = not meta or str(meta.get("version") or "") == str(e.get("semver") or "1.0.0")
        same_sha = not meta or not meta.get("source_sha256") or meta.get("source_sha256") == e.get("sha256")
        if e.get("ssot_id") != hit:
            e["ssot_id"] = hit
            changed += 1
        if same_ver and same_sha:
            if not str(e.get("status", "")).startswith("已確認"):
                e.update(status="已確認(VCGC)", granted_at=now())
                changed += 1
            granted.append(key)
        elif same_ver:                                   # 中央那一版的內容 ≠ VDF 現在的內容 → 升版重送(同版不得改)
            e["supersedes"] = e.get("semver") or "1.0.0"
            e["semver"] = _bump(e["supersedes"])
            e["status"] = "內容更新 · 待 VCGC 重檢"
            changed += 1
        elif not str(e.get("status", "")).startswith("內容更新"):
            e["status"] = "內容更新 · 待 VCGC 重檢"            # VDF 已出新版,中央還在舊版
            changed += 1
    out = reg
    if changed:
        out = reg if inplace else reg.with_name("VDF_SSOT_Register_v%04d.json" % (_vnum(reg) + 1))
        book.update(at=now(), prior=reg.name if out != reg else book.get("prior"), writer="%s(核號同步)" % TAG, entries=entries)
        out.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    pending = [k for k, e in entries.items() if str(e.get("status", "")).startswith(("暫編", "內容更新"))]
    state = {"engine": TAG, "verb": "apply", "at": now(), "lamp": "YELLOW" if (conflicted or pending) else "GREEN",
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
    items, seen, cids, self_c = [], {}, {}, []
    for key, e in sorted(entries.items()):
        if str(e.get("status", "")).startswith(("退役", "已確認")):
            continue
        asset = build_asset(e)
        items.append({"key": key, "entry": key, "kind": e["kind"], "vcgc_kind": e.get("vcgc_kind") or VCGC_KIND.get(e["kind"], "SSOT"), "proposed_no": e.get("no"),
                      "ssot_id": e.get("ssot_id") or "", "fingerprint": e.get("fp"), "version": e.get("semver"), "src": (e.get("src") or [None])[0],
                      "status": e.get("status"), "note": e.get("note") or "", "content": e.get("content"), "asset": asset})
        if asset["candidate_id"] in cids:
            self_c.append({"key": key, "kind": e["kind"], "why": "候選編號撞:%s 與 %s 清洗後同為 %s" % (key, cids[asset["candidate_id"]], asset["candidate_id"])})
        cids.setdefault(asset["candidate_id"], key)
        if e["kind"] == "SYN":
            a, c = (e.get("content") or {}).get("alias"), (e.get("content") or {}).get("canonical")
            if a in seen and seen[a] != c:
                self_c.append({"key": key, "kind": "SYN", "why": "同一別名 %s 對到兩個統一路徑 %s / %s" % (a, seen[a], c)})
            seen.setdefault(a, c)
    req = {"from": "VDF", "subsystem": "VDF(VIA-02 資料鍛造 · 獨立 MAIN ActivateVDF)", "engine": TAG, "ts": now(), "register": reg.name,
           "contract": "VIA.AssetCandidates.v1(CGC_MDL237 v0114 候選欄位)", "source_id": SOURCE_ID,
           "rule": "子系統提出時 ssot_code / ssot_id 空白;VCGC(CGC_MDL278 收件 → 候選冊 → CGC_MDL237 中央檢測與發號)→ 寫 VCGC_NUMBER_GRANT_latest.json "
                   "{grants:{鍵: 中央號}, assets:{鍵: {code, version, source_sha256}}, conflicts:[{key, with, why}]} → VDF apply 讀到就補 ssot_id",
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
    line = "[VDF 編號同步] %s · 登記 %d 條(%s)· 已確認 %d · 衝突待人判 %d · 待中央號 %d · 自撞 %d · 冊 %s%s · 核發冊 %s%s" % (
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

    def contract_ok(a):
        return (tuple(sorted(a)) == tuple(sorted(CANDIDATE_FIELDS)) and a["ssot_code"] is None and a["owner"] == "VDF"
                and all(isinstance(a[k], str) and a[k].strip() for k in ("candidate_id", "asset_type", "owner", "source_id", "source_pointer", "source_sha256",
                                                                             "version", "scope", "semantic_key", "name", "risk_level", "environment"))
                and re.fullmatch(r"[A-Za-z0-9_.:-]+", a["candidate_id"]) and re.fullmatch(r"[a-z0-9_.:-]+", a["scope"])
                and re.fullmatch(r"\d+\.\d+\.\d+", a["version"]) and re.fullmatch(r"[0-9a-f]{64}", a["source_sha256"])
                and re.fullmatch(r"via_[A-Za-z0-9_]+", a["environment"]) and all(isinstance(a[k], list) for k in ("libraries", "aliases", "positive", "negative")))

    print("=== %s · 自測(登記 → 候選契約請求 → 中央號核發 → 套號;只寫 VDF 自己的夾)===" % TAG)
    real = harvest(HERE)
    kinds = {}
    for it in real.values():
        kinds[it["kind"]] = kinds.get(it["kind"], 0) + 1
    rx_real = [k for k, it in real.items() if it["kind"] == "REGEX"]
    chk("① 掃本倉 VDF(只登宣告的):%s · 正則 %s" % (kinds, rx_real[:2]), all(kinds.get(k) for k in ("SSOT", "CFG", "REGEX", "SYN", "PARAM"))
        and real.get("VDF:SYN:START_DATE", {}).get("content", {}).get("canonical") == "time.start_date"
        and all(":RGX:VDF_" in k for k in rx_real), kinds)
    tmp = Path(tempfile.mkdtemp(prefix="vdf_ssot_"))
    try:
        via = tmp / "VIA"
        vdf = via / "functional modules" / "VDF"
        (vdf / "engine").mkdir(parents=True)
        (via / "supportive modules" / "registry").mkdir(parents=True)
        (vdf / "VDF_InputUniverse_SSOT_v0100.json").write_text(json.dumps({"inputs": [
            {"id": "IN-01", "code_regex": "^[1-9][0-9]{3}$", "code_regex_positive": ["2330"], "code_regex_negative": ["0050"]},
            {"id": "IN-02", "code_regex": "^00[0-9]{3}A$"}]}), encoding="utf-8")
        (vdf / "VDF_AdjPrice_Rule_SSOT_v0100.json").write_text(json.dumps({"rule": "原始永不改"}), encoding="utf-8")
        (vdf / "engine" / "VDF_ENG053_ParamEngineMap_v0100.py").write_text(
            "import re\nUNIFIED_ALIAS = {'START_DATE': 'time.start_date', 'TIMEOUT': 'fetch.timeout_s'}\nX = re.compile(r'_v(\\d{4})$')\n", encoding="utf-8")
        r1 = register(vdf)
        reg1 = json.loads((vdf / "registry" / r1["register"]).read_text(encoding="utf-8"))["entries"]
        rxk = "VDF:RGX:VDF_InputUniverse_SSOT:inputs.IN-01.code_regex"
        chk("② register:SSOT 1 · CFG 1 · REGEX 2(冊上宣告;鍵 = 冊族 + 位置(id))· SYN 2 · 程式內實作正則不登 · semver 1.0.0 · 冊 %s" % r1["register"],
            r1["by_kind"] == {"SSOT": 1, "CFG": 1, "REGEX": 2, "SYN": 2} and rxk in reg1 and reg1[rxk]["content"]["positive"] == ["2330"]
            and all(e["semver"] == "1.0.0" and len(e["sha256"]) == 64 for e in reg1.values()) and r1["register"] == "VDF_SSOT_Register_v0100.json", (r1, list(reg1)))
        r1b = register(vdf)
        chk("③ 再登記一次:沒變 → 不出新版 · 號不變", r1b["changed"] == 0 and r1b["register"] == r1["register"])
        q = request(vdf)
        rq = json.loads((vdf / "contract" / REQUEST_NAME).read_text(encoding="utf-8"))
        assets = {i["key"]: i["asset"] for i in rq["ssot_items"]}
        chk("④ request:每條附 VCGC 候選契約(%d 欄 · ssot_code null · 身分 = 來源 + 登記鍵)· 正則帶正反例 · 同義字帶別名 · 待中央號 %d" % (len(CANDIDATE_FIELDS), q["pending"]),
            rq["from"] == "VDF" and q["pending"] == 6 and all(contract_ok(a) for a in assets.values())
            and assets[rxk]["asset_type"] == "REGEX" and assets[rxk]["negative"] == ["0050"] and assets[rxk]["scope"] == "vdf.regex.vdf_inputuniverse_ssot.code_regex"
            and assets["VDF:SYN:START_DATE"]["aliases"] == ["START_DATE"] and assets["VDF:SYN:START_DATE"]["value"] == "time.start_date",
            [k for k, a in assets.items() if not contract_ok(a)])
        a0 = dict(assets)
        r1c = register(vdf)
        chk("④b 候選定義只由鍵 + 內容決定:再跑一次 request 定義一字不差(VCGC 同版不得改內容)",
            r1c["changed"] == 0 and {i["key"]: i["asset"] for i in json.loads((request(vdf) and (vdf / "contract" / REQUEST_NAME)).read_text(encoding="utf-8"))["ssot_items"]} == a0)
        syn = "VDF:SYN:START_DATE"
        g = {"grants": {syn: "VIA-VDF-SYN901", rxk: "VIA-VDF-RGX901"},
             "assets": {syn: {"code": "VIA-VDF-SYN901", "version": "1.0.0", "source_sha256": reg1[syn]["sha256"]},
                        rxk: {"code": "VIA-VDF-RGX901", "version": "1.0.0", "source_sha256": reg1[rxk]["sha256"]}},
             "conflicts": [{"key": "VDF:SYN:TIMEOUT", "with": "VRN-2", "why": "同別名對到不同統一路徑"}]}
        gp = via / "supportive modules" / "registry" / GRANT_NAME
        gp.write_text(json.dumps(g), encoding="utf-8")
        a = apply(vdf)
        reg2 = json.loads((vdf / "registry" / a["register"]).read_text(encoding="utf-8"))["entries"]
        chk("⑤ apply:中央號補進 ssot_id(版本 + 內容都對才已確認)· 衝突標待人判 · 出新版冊 %s · 狀態冊寫好" % a["register"],
            reg2[syn]["ssot_id"] == "VIA-VDF-SYN901" and reg2[syn]["status"] == "已確認(VCGC)" and reg2[rxk]["ssot_id"] == "VIA-VDF-RGX901"
            and reg2["VDF:SYN:TIMEOUT"]["status"].startswith("衝突") and a["granted"] == 2 and a["conflicts"] == 1 and (vdf / "contract" / STATE_NAME).is_file())
        q2 = request(vdf)
        chk("⑥ 已確認的不再送(待中央號 6 → %d)" % q2["pending"], q2["pending"] == 4)
        (vdf / "engine" / "VDF_ENG053_ParamEngineMap_v0100.py").write_text(
            "import re\nUNIFIED_ALIAS = {'START_DATE': 'time.begin', 'TIMEOUT': 'fetch.timeout_s'}\n", encoding="utf-8")
        (vdf / "VDF_InputUniverse_SSOT_v0100.json").write_text(json.dumps({"inputs": [{"id": "IN-02", "code_regex": "^00[0-9]{3}A$"}]}), encoding="utf-8")
        r3 = register(vdf)
        reg3 = json.loads((vdf / "registry" / r3["register"]).read_text(encoding="utf-8"))["entries"]
        a3 = {i["key"]: i["asset"] for i in json.loads(((request(vdf) and vdf / "contract" / REQUEST_NAME)).read_text(encoding="utf-8"))["ssot_items"]}
        chk("⑦ 已有中央號後內容改了 → 升版 1.0.0 → %s · supersedes 1.0.0 · 中央號照留 · 轉「內容更新 · 待 VCGC 重檢」重送;消失的正則標退役不刪" % reg3[syn]["semver"],
            reg3[syn]["semver"] == "1.1.0" and reg3[syn]["supersedes"] == "1.0.0" and reg3[syn]["ssot_id"] == "VIA-VDF-SYN901"
            and reg3[syn]["status"].startswith("內容更新") and a3[syn]["version"] == "1.1.0" and a3[syn]["supersedes"] == "1.0.0"
            and reg3[rxk]["status"].startswith("退役") and reg3[syn]["no"] == reg1[syn]["no"] and len(reg3) == len(reg2))
        g["assets"][syn] = {"code": "VIA-VDF-SYN902", "version": "1.1.0", "source_sha256": "0" * 64}
        g["grants"][syn] = "VIA-VDF-SYN902"
        gp.write_text(json.dumps(g), encoding="utf-8")
        a4 = apply(vdf)
        reg4 = json.loads((vdf / "registry" / a4["register"]).read_text(encoding="utf-8"))["entries"]
        chk("⑦b 中央那一版內容 ≠ VDF 現況(同版號、指紋不同)→ 不確認 · 升版 %s 重送" % reg4[syn]["semver"],
            reg4[syn]["semver"] == "1.2.0" and reg4[syn]["supersedes"] == "1.1.0" and reg4[syn]["status"].startswith("內容更新"))
        g["conflicts"] = []
        gp.write_text(json.dumps(g), encoding="utf-8")
        apply(vdf)
        st_to = json.loads(latest_register(vdf).read_text(encoding="utf-8"))["entries"]["VDF:SYN:TIMEOUT"]["status"]
        chk("⑦c 衝突修好(VCGC 不再列)→ 回「%s」· 下一輪重送" % st_to, st_to == "暫編 · 待 VCGC 核號"
            and "VDF:SYN:TIMEOUT" in {i["key"] for i in json.loads(((request(vdf) and vdf / "contract" / REQUEST_NAME)).read_text(encoding="utf-8"))["ssot_items"]})
        s = sync(vdf)
        chk("⑧ sync 一行:%s" % s["line"][:120], s["line"].startswith("[VDF 編號同步]") and "核發冊 " + GRANT_NAME in s["line"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑨ VDF 獨立:不匯入他系統程式 · 兩座橋在 · 不自發中央號(VIA-… 只從核發冊讀)· VCGC 核發冊只讀 · 零網路 · 同意閘不讀不寫",
        not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC|requests|httpx|urllib\.request)", src, re.M) and "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and "GRANT_NAME).write" not in body and "CONSENT" not in body and not re.search(r"[\"']VIA-%", body))
    print("[計] %s 自測 %d/%d · %s" % (TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
