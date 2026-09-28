#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0102 — 下市不蓋 · 上市新增 · 改名留史 · SSOT 版號與內容指紋 · 凍結鎖編號

R29(操作員:「下市個股編號不蓋 上市新增」「所有參數即使相同數據不同來源也是編號不同」「檢查 SSOT 版本編號完善」):
  ① 金融市場代號(FM):v0100 的 assign() 遇到**已下市(gone_since)的鍵又出現**時,整列換新、gone_since 被清掉——
     代號被別家公司重用時,新公司會沿用舊號並蓋掉舊名。v0102:
       · 下市列 + 名字不同 = 另一家公司重用代號 → **新鍵 `<代號>#L2`(#L3 …)= 新號**,舊號原封留著(下市不蓋)
       · 下市列 + 名字相同 = 同一家復牌 → 沿用舊號,記 `gone_history` + `revived_at`(不悄悄抹掉下市紀錄)
       · 在市列改名 → 沿用舊號,記 `name_history`(改名留史)
     全種類通用:任何下市後又出現的列都記 `gone_history` / `revived_at`。新上市 = 新鍵 = 新號(v0100 本來就如此)。
  ② 多來源:同名不同來源本來就各自一號(R29 實測 MRC / PRMT / FD / FM 共用編號 0);v0102 不改規則,只在自測守住它。
  ③ SSOT:檔名沒有 _vNNNN 的冊 v0100 一律記 v0100,內容改了看不出來 → 每列補 `declared_version`(冊內 version /
     schema_version / schemaVersion)與 `content_sha`(內容 sha256 前 12 碼);鍵不變(不為補欄位而換號)。
  ④ 凍結鎖:`*.freeze.lock.json` 不是 SSOT 冊(v0100 刻意排除),改編成 ENV 類「凍結鎖」列(只增)。
其餘整支照 v0101 / v0100(thin tail;__getattr__ 轉接)。
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

import hashlib
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL237_NumberingSystem"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
ENGINE = Path(__file__).stem
_BASE = _PRIOR._PRIOR                                   # v0100 module: build() resolves assign / ssot_items / env_items here
_ASSIGN, _SSOT, _ENV = _BASE.assign, _BASE.ssot_items, _BASE.env_items


def _norm(s) -> str:
    return re.sub(r"[\s\W_]+", "", str(s or "")).lower()


HISTORY = ("gone_history", "revived_at", "name_history", "relist_of")


def _relist_key(rows: dict, it: dict) -> str | None:
    """A symbol whose old row is delisted under another name: reuse the #Ln row that already holds this name, else the next free n."""
    base, ver = it["key"], it["version"]
    old = rows.get(("FM", f"{base}@{ver}"))
    if not (old and old.get("gone_since") and _norm(old.get("name")) != _norm(it.get("name"))):
        return None
    n = 2
    while ("FM", f"{base}#L{n}@{ver}") in rows:
        if _norm(rows[("FM", f"{base}#L{n}@{ver}")].get("name")) == _norm(it.get("name")):
            return f"{base}#L{n}"
        n += 1
    return f"{base}#L{n}"


def assign(items: list, state: dict) -> dict:
    rows = state["rows"]
    stamp = _BASE._now()
    before = {k: dict(v) for k, v in rows.items()}
    for it in items:
        if it.get("kind") != "FM":
            continue
        k2 = _relist_key(rows, it)
        if k2:
            it["relist_of"] = rows[("FM", f"{it['key']}@{it['version']}")].get("code")
            it["key"] = k2                                  # another company on a reused symbol: a new number
    state = _ASSIGN(items, state)
    for k, old in before.items():
        new = rows.get(k)
        if new is None:
            continue
        for f in HISTORY:                                   # v0100 rebuilds each row from the item: carry the story forward
            if old.get(f) and not new.get(f):
                new[f] = old[f]
        if old.get("gone_since") and not new.get("gone_since"):   # it came back: keep the delisting on record
            new["gone_history"] = list(old.get("gone_history") or []) + [old["gone_since"]]
            new["revived_at"] = stamp
        if k[0] == "FM" and old.get("name") and _norm(new.get("name")) != _norm(old.get("name")):
            new["name_history"] = list(old.get("name_history") or []) + [old["name"]]
    return state


def _declared(book) -> str:
    if isinstance(book, dict):
        for k in ("version", "schema_version", "schemaVersion", "ver"):
            v = book.get(k)
            if isinstance(v, (str, int, float)) and str(v).strip():
                return str(v)
    return ""


def ssot_items() -> list:
    out = _SSOT()
    for it in out:
        src = _BASE.VIA / str(it.get("source") or "")
        try:
            raw = src.read_bytes()
        except OSError:
            continue
        it["content_sha"] = hashlib.sha256(raw).hexdigest()[:12]
        dv = _declared(_BASE._json(src))
        if dv:
            it["declared_version"] = dv
    return out


def freeze_lock_items() -> list:
    rels = subprocess.run(["git", "ls-files", "*.freeze.lock.json"], cwd=_BASE.VIA, capture_output=True, text=True).stdout.splitlines()
    out = []
    for rel in rels:
        if any(x in rel for x in ("VIA_Reports/", "SCOPE_COPY", "references/")):
            continue
        out.append(_BASE.item("ENV", "freeze|" + rel, Path(rel).name, "凍結鎖", rel, "sha 比對(凍結檔不改)", _BASE.updated(rel)))
    return out


def env_items(envs: dict) -> list:
    out = _ENV(envs)
    have = {r.get("key") for r in out}
    return out + [r for r in freeze_lock_items() if r.get("key") not in have]


_BASE.assign, _BASE.ssot_items, _BASE.env_items = assign, ssot_items, env_items


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def main(argv=None) -> int:
    if "--selftest" in (sys.argv[1:] if argv is None else argv):
        return selftest()
    return _PRIOR.main(argv)


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    def fm(key, name):
        return {"kind": "FM", "key": key, "version": "v0100", "name": name, "cat": "股票", "sub": "VDF", "source": "s", "api": "a",
                "updated_at": "t", "lamp": "GREEN", "note": "", "cols": {}, "region": "TW", "asset": "EQT"}

    st = {"rows": {}, "subs": [], "cats": {}}
    assign([fm("1234", "甲公司"), fm("5678", "乙公司")], st)
    code_a = st["rows"][("FM", "1234@v0100")]["code"]
    assign([fm("5678", "乙公司")], st)                                   # 1234 delisted
    chk("① 下市:列留著、標 gone_since、號不動", st["rows"][("FM", "1234@v0100")].get("gone_since")
        and st["rows"][("FM", "1234@v0100")]["code"] == code_a)
    assign([fm("1234", "丙公司"), fm("5678", "乙公司")], st)            # symbol reused by another company
    old, new = st["rows"][("FM", "1234@v0100")], st["rows"].get(("FM", "1234#L2@v0100"))
    chk("① 代號被別家重用:新號 · 舊號原封(下市不蓋)", new is not None and new["code"] != code_a and old["code"] == code_a
        and old["name"] == "甲公司" and old.get("gone_since") and new.get("relist_of") == code_a, (new or {}).get("code"))
    assign([fm("1234", "丙公司"), fm("5678", "乙公司")], st)            # next run: same #L2 row, no #L3
    chk("① 重跑:別家重用的代號仍是同一個 #L2 號,不長 #L3", ("FM", "1234#L3@v0100") not in st["rows"]
        and st["rows"][("FM", "1234#L2@v0100")]["code"] == new["code"] and st["rows"][("FM", "1234#L2@v0100")].get("relist_of") == code_a)
    st2 = {"rows": {}, "subs": [], "cats": {}}
    assign([fm("2222", "丁公司")], st2)
    c2 = st2["rows"][("FM", "2222@v0100")]["code"]
    assign([fm("9999", "x")], st2)
    assign([fm("2222", "丁公司"), fm("9999", "x")], st2)                  # same company relists
    r2 = st2["rows"][("FM", "2222@v0100")]
    chk("① 同一家復牌:沿用舊號,記 gone_history / revived_at", r2["code"] == c2 and not r2.get("gone_since")
        and len(r2.get("gone_history") or []) == 1 and r2.get("revived_at"))
    assign([fm("2222", "丁公司新名"), fm("9999", "x")], st2)
    chk("① 在市改名:沿用舊號,記 name_history", st2["rows"][("FM", "2222@v0100")]["code"] == c2
        and st2["rows"][("FM", "2222@v0100")].get("name_history") == ["丁公司"])
    assign([fm("2222", "丁公司新名"), fm("9999", "x")], st2)
    r2 = st2["rows"][("FM", "2222@v0100")]
    chk("① 重跑:gone_history / name_history 跨次保留", r2.get("name_history") == ["丁公司"] and len(r2.get("gone_history") or []) == 1)
    st3 = {"rows": {}, "subs": [], "cats": {}}
    prm = lambda src: {"kind": "PRMT", "key": f"{src}|x", "version": "v1", "name": "x", "cat": "c", "sub": "CORE", "source": src,
                       "api": "a", "updated_at": "t", "lamp": "GREEN", "note": ""}
    assign([prm("A.py"), prm("B.py")], st3)
    codes = {r["code"] for r in st3["rows"].values()}
    chk("② 同名不同來源 = 不同號", len(codes) == 2)
    ss = ssot_items()
    chk("③ SSOT 每列帶內容指紋;有宣告版號的帶 declared_version", ss and all(it.get("content_sha") for it in ss)
        and any(it.get("declared_version") for it in ss), f"{len(ss)} 冊 · 有宣告版號 {sum(1 for it in ss if it.get('declared_version'))}")
    fl = freeze_lock_items()
    chk("④ 凍結鎖編成 ENV 列", len(fl) > 0 and all(r["cat"] == "凍結鎖" for r in fl), f"{len(fl)} 本")
    ok = all(results)
    print(f"  {ENGINE} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
