#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL149_VeritasCentralGovernanceConsole v0174 — 薄尾:元件冊發號避開他冊已發的號(一號不得兩主)

實錄(2026-09-29 · Codex #373 P1):registry-sync --apply 把 `tool|via-in` 發成 VIA-TOOL-0194,可是引擎版本冊
  (VIA_EngineVersion_Register_v*.json;手寫,"where": "this register")早就把 0194 給了 token 引擎,編號 SSOT(TOOL-C017)·
  編號書 · 編號台帳 · 批文件都照引擎版本冊引用。再量:0179–0193 也一樣 —— 引擎版本冊 09-27 起在 VIA-TOOL 命名空間自己發號,
  沒記回元件冊計數器;元件冊 09-28 / 09-29 又把同號發給 15 支短令。共 16 號一號兩主(15 支早就撞,本批 1 支)。
根因:v0142 registry_sync 只看元件冊自己的 counters[前綴] + 1。
本尾版(只增不減;其餘原樣轉前一版):
  ① minted_elsewhere():他冊自己發的號(引擎版本冊 where = "this register" 那幾列)= 已佔用;只抄元件冊號的列(where = "inventory")不算。
  ② registry_sync():發號從「計數器 · 元件冊已用的最大號 · 他冊已發的最大號」取大再 +1,已佔的號一律跳過。
     元件冊裡和他冊撞號的那筆、或和元件冊前一筆同號的那筆,--apply 時改發新號,留 recoded_from(舊號清單)· recoded_at · recode_why。
     讓號的一律是元件冊:他冊的號已被編號書引用,元件冊短令的號沒有別處引用(實測全倉)。
     乾跑(預設)零寫,照列 collisions / recode;只有寫正本元件冊才讀他冊,暫存冊的行為和前一版一模一樣。
  ③ 鏈上每一支持有 registry_sync 的模組都換成本版(同 v0172 換 live_components 的做法):registry-sync 動詞 · --layout-only /
     --nlp-only 限定範圍的同步 · hub 委派的同步 · v0168 同步檢查的乾跑,全走同一支;原函式照舊做盤點與寫冊。
  ④ 同步檢查多報一欄 registry.recode(待改號筆數);有撞號就算「待同步」,閘印那一行提示。
  ⑤ registry-sync 動詞多印一段發號結果;--apply 之後還撞 → rc 2。
只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。零網路;不設同意閘、不裝件。不用 TA-Lib。
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

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
CODE = re.compile(r"^VIA-([A-Z]+)-(\d{4,})$")
MINTERS = (   # 在元件冊命名空間自己發號的他冊:冊(尾版律)· 列在哪 · 哪一欄等於什麼才算自己發的 · 身分欄
    {"glob": "VIA_EngineVersion_Register_v*.json", "rows": "rows", "field": "where", "value": "this register",
     "ident": ("family", "role", "file")},
)


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("vcgc_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _read(path) -> dict | None:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


def _write(path: Path, doc: dict) -> None:
    """Same bytes layout and the same atomic replace as the prior writer (indent 1 · UTF-8 · trailing newline)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _book(pattern: str, folder: Path) -> Path | None:
    hits = [p for p in Path(folder).glob(pattern) if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def split(code) -> tuple:
    m = CODE.match(str(code or ""))
    return (m.group(1), int(m.group(2))) if m else ("", -1)


def minted_elsewhere(folder: Path = HERE, minters=MINTERS) -> dict:
    """{code: "book · identity"} for every code another book minted itself in the inventory's namespace."""
    out = {}
    for m in minters:
        book = _book(m["glob"], folder)
        for r in ((_read(book) or {}).get(m["rows"]) or []) if book else []:
            code = str(r.get("code") or "")
            if r.get(m["field"]) == m["value"] and split(code)[0]:
                out.setdefault(code, f"{book.name} · " + "|".join(str(r.get(k, "")) for k in m["ident"]))
    return out


def plan_codes(inv: dict, ext: dict) -> dict:
    """Floor per prefix (counter · highest number the inventory used · highest number another book minted) and the inventory
    rows that have to give their code up: a code another book minted, or a code an earlier inventory row already holds."""
    records = (inv or {}).get("records") or []
    floor = {k: int(v) for k, v in ((inv or {}).get("counters") or {}).items()}
    for code in [r.get("code") for r in records] + list(ext):
        p, n = split(code)
        if p:
            floor[p] = max(floor.get(p, 0), n)
    held, clash = {}, []
    for r in records:
        code = str(r.get("code") or "")
        if not code:
            continue
        if code in ext:
            clash.append({"key": r.get("key"), "code": code, "other": ext[code]})
        elif code in held:
            clash.append({"key": r.get("key"), "code": code, "other": f"元件冊 · {held[code]}"})
        else:
            held[code] = r.get("key")
    return {"floor": floor, "collisions": clash}


def recode(inv: dict, ext: dict, now: str) -> list:
    """Every colliding row gets a fresh code above the floor (skipping anything held anywhere) and keeps its old codes in
    recoded_from; the counters end at the floor, so whatever the prior mints next lands above every code in every book."""
    pc = plan_codes(inv, ext)
    floor, moved = pc["floor"], []
    records = inv.get("records") or []
    taken = {str(r.get("code") or "") for r in records} | set(ext)
    by_key = {r.get("key"): r for r in records}
    for c in pc["collisions"]:
        p = split(c["code"])[0]
        n = floor.get(p, 0) + 1
        while f"VIA-{p}-{n:04d}" in taken:
            n += 1
        new = f"VIA-{p}-{n:04d}"
        floor[p] = n
        taken.add(new)
        r = by_key[c["key"]]
        r["code"] = new
        r["recoded_from"] = list(r.get("recoded_from") or []) + [c["code"]]
        r["recoded_at"] = now
        r["recode_why"] = f"{c['code']} 已由 {c['other']} 先發(一號不得兩主)"
        moved.append({"key": c["key"], "from": c["code"], "to": new})
    counters = {k: int(v) for k, v in (inv.get("counters") or {}).items()}
    for p, n in floor.items():
        if counters.get(p, 0) < n:
            counters[p] = n
    inv["counters"] = counters
    return moved


def _prior_sync():
    f = PRIOR.registry_sync
    return getattr(f, "__wrapped__", f) if getattr(f, "_v0174", False) else f


_V0142_RS = _prior_sync()     # the chain's body (v0142): live inventory · plan · atomic write — captured before any swap
_LAST: dict = {}


def _same(a, b) -> bool:
    try:
        return Path(a).resolve() == Path(b).resolve()
    except (OSError, TypeError):
        return False


def registry_sync(apply: bool = False, path: Path | None = None, external: dict | None = None) -> dict:
    """v0174: the prior sync with codes unique across books. `external` None = read the other books only for the live book."""
    path = Path(path) if path is not None else Path(PRIOR.COMPONENT_REGISTRY)
    live = _same(path, PRIOR.COMPONENT_REGISTRY)
    ext = (minted_elsewhere() if live else {}) if external is None else dict(external)
    inv = _read(path)
    before = plan_codes(inv or {}, ext)
    moved = []
    if apply and (inv is not None or ext):
        now = datetime.now().isoformat(timespec="seconds")
        doc = inv if inv is not None else {"schema": "VIA.ComponentInventory.v1", "append_only": True,
                                           "writer": "VCGC registry-sync --apply", "counters": {}, "records": []}
        old = dict(doc.get("counters") or {})
        moved = recode(doc, ext, now)
        if moved or doc.get("counters") != old or inv is None:
            doc["updated_at"] = now
            doc["records"] = sorted(doc.get("records") or [], key=lambda r: r.get("code", ""))
            path.parent.mkdir(parents=True, exist_ok=True)
            _write(path, doc)
    res = _V0142_RS(apply, path)
    after = plan_codes(_read(path) or {}, ext) if apply else before
    res.update({"external": len(ext), "collisions": after["collisions"], "floor": after["floor"], "live": live,
                "recode": moved if apply else [{"key": c["key"], "from": c["code"]} for c in before["collisions"]]})
    _LAST.clear()
    _LAST.update(res)
    return res


registry_sync._v0174 = True
registry_sync.__wrapped__ = _V0142_RS


def _chain_mods() -> list:
    return [m for m in list(sys.modules.values()) if _STEM in str(getattr(m, "__file__", "") or "")]


_V0172_SYNC = PRIOR.sync_check


def ensure() -> int:
    """Every chain module holding a registry_sync that is not a v0174 one gets this one (the verb, the scoped syncs, the hub's
    delegated sync and v0168's dry run all call their own module global); the v0172 sync check is swapped the same way."""
    n = 0
    for m in _chain_mods():
        d = m.__dict__
        f = d.get("registry_sync")
        if callable(f) and not getattr(f, "_v0174", False):
            d["registry_sync"] = registry_sync
            n += 1
        if d.get("sync_check") is _V0172_SYNC:
            d["sync_check"] = sync_check
    return n


def sync_check(key: str | None = None, _base=None) -> dict:
    ensure()
    _LAST.clear()
    out = (_base or _V0172_SYNC)(key)
    try:
        if _LAST.get("live") and _LAST.get("state") == "PLAN":
            n = len(_LAST.get("collisions") or [])
        else:
            n = len(plan_codes(_read(PRIOR.COMPONENT_REGISTRY) or {}, minted_elsewhere())["collisions"])
        reg = out.get("registry")
        if isinstance(reg, dict):
            reg["recode"] = n
        out["pending"] = bool(out.get("pending")) or n > 0
    except Exception as exc:              # the check never breaks the gate; the reason is kept, not swallowed
        out["codes_error"] = f"{type(exc).__name__}: {str(exc)[:120]}"
    return out


def report_codes(r: dict) -> int:
    """The verb's extra lines; rc 2 when codes still collide after --apply."""
    moved, clash = r.get("recode") or [], r.get("collisions") or []
    applied = r.get("state") == "APPLIED"
    print(f"  [發號] 他冊已發 {r.get('external', 0)} 號 · 撞號 {len(clash) if applied else len(moved)} 筆"
          + (f" · 本次改發 {len(moved)} 筆" if applied else ""))
    for m in moved[:40]:
        print(f"    {m['key']}:{m['from']} → {m.get('to') or '(--apply 改發)'}")
    if len(moved) > 40:
        print(f"    …另 {len(moved) - 40} 筆")
    if not applied and moved:
        print("  撞號由 --apply 改發新號(讓號的是元件冊:他冊的號已被編號書引用)")
    for c in (clash if applied else [])[:10]:
        print(f"    [仍撞] {c['key']}:{c['code']} ← {c['other']}")
    return 2 if applied and clash else 0


def _install() -> int:
    return ensure()


_PATCHED = _install()


def after_verb(args: list, rc):
    """registry-sync (any scope) prints the code lines of the sync it just ran; other verbs pass through untouched."""
    if args[:1] == ["registry-sync"] and _LAST:
        return max(rc or 0, report_codes(dict(_LAST)))
    return rc


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    _LAST.clear()
    return after_verb(args, PRIOR.main(argv))


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    def evbook(rows):
        return json.dumps({"schema": "VIA.EngineVersion.v1", "append_only": True, "rows": rows}, ensure_ascii=False)

    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        (t / "VIA_EngineVersion_Register_v0100.json").write_text(evbook([
            {"family": "old", "role": "engine", "file": "old.py", "code": "VIA-TOOL-0900", "where": "this register"}]), encoding="utf-8")
        (t / "VIA_EngineVersion_Register_v0101.json").write_text(evbook([
            {"family": "a", "role": "engine", "file": "a.py", "code": "VIA-TOOL-0005", "where": "this register"},
            {"family": "b", "role": "engine", "file": "b.py", "code": "VIA-SYS-0001", "where": "inventory"},
            {"family": "c", "role": "loader", "file": "c.py", "code": "not-a-code", "where": "this register"}]), encoding="utf-8")
        me = minted_elsewhere(t)
    chk("① 他冊自己發的號才算已佔(where = this register);只抄元件冊號的列不算;冊照尾版律取最新一本;不是號的字串不算",
        set(me) == {"VIA-TOOL-0005"} and me["VIA-TOOL-0005"].endswith("a|engine|a.py") and "_v0101" in me["VIA-TOOL-0005"], me)

    inv = {"counters": {"TOOL": 3}, "records": [
        {"key": "tool|a", "code": "VIA-TOOL-0001"}, {"key": "tool|b", "code": "VIA-TOOL-0002"},
        {"key": "tool|c", "code": "VIA-TOOL-0002"}, {"key": "tool|d", "code": "VIA-TOOL-0003"}]}
    ext = {"VIA-TOOL-0003": "EV · x", "VIA-TOOL-0007": "EV · y"}
    pc = plan_codes(inv, ext)
    chk("② 地板 = 計數器 · 元件冊最大號 · 他冊最大號取大;要讓號的 = 他冊先發的號 + 元件冊內和前一筆同號的那筆",
        pc["floor"].get("TOOL") == 7 and [(c["key"], c["code"]) for c in pc["collisions"]]
        == [("tool|c", "VIA-TOOL-0002"), ("tool|d", "VIA-TOOL-0003")]
        and "tool|b" in pc["collisions"][0]["other"] and pc["collisions"][1]["other"] == "EV · x", pc)

    moved = recode(inv, ext, "T1")
    codes = [r["code"] for r in inv["records"]]
    row_c = inv["records"][2]
    moved2 = recode(inv, {**ext, row_c["code"]: "EV · z"}, "T2")
    chk("③ 改號:撞號那筆拿地板之上的新號、舊號留 recoded_from(改兩次留兩個)· 計數器停在地板 · 全冊零重號、零他冊號",
        moved == [{"key": "tool|c", "from": "VIA-TOOL-0002", "to": "VIA-TOOL-0008"},
                  {"key": "tool|d", "from": "VIA-TOOL-0003", "to": "VIA-TOOL-0009"}]
        and codes == ["VIA-TOOL-0001", "VIA-TOOL-0002", "VIA-TOOL-0008", "VIA-TOOL-0009"]
        and moved2 == [{"key": "tool|c", "from": "VIA-TOOL-0008", "to": "VIA-TOOL-0010"}]
        and row_c["recoded_from"] == ["VIA-TOOL-0002", "VIA-TOOL-0008"] and row_c["recoded_at"] == "T2"
        and "EV · z" in row_c["recode_why"] and inv["counters"]["TOOL"] == 10
        and len({r["code"] for r in inv["records"]}) == 4
        and not plan_codes(inv, {**ext, "VIA-TOOL-0008": "EV · z"})["collisions"], moved2)

    live_path = Path(PRIOR.COMPONENT_REGISTRY)
    base = _read(live_path) or {"counters": {}, "records": []}
    tools = [r for r in base["records"] if r.get("category") == "tool" and r.get("state", "ACTIVE") == "ACTIVE"]
    held = {r.get("code") for r in base["records"]}
    ok4, note4 = False, f"元件冊正本不在位或短令不足三支(短令 {len(tools)}),拿不到真冊副本"
    ok5, note5 = False, note4
    if len(tools) >= 3:
        victim, gone = tools[0], tools[1:3]
        with tempfile.TemporaryDirectory() as td:
            rp = Path(td) / "inventory.json"
            doc = json.loads(json.dumps(base))
            doc["records"] = [r for r in doc["records"] if r.get("key") not in {g["key"] for g in gone}]
            top = int((doc.get("counters") or {}).get("TOOL", 0))
            ext4 = {victim["code"]: "EV · selftest-victim", f"VIA-TOOL-{top + 1:04d}": "EV · selftest-above"}
            _write(rp, doc)
            b0 = rp.read_bytes()
            p0 = registry_sync(False, rp, external=ext4)
            zero = rp.read_bytes() == b0
            p1 = registry_sync(True, rp, external=ext4)
            after = _read(rp) or {"records": []}
            got = {r["key"]: r["code"] for r in after["records"]}
            vrow = next((r for r in after["records"] if r.get("key") == victim["key"]), {})
            p2 = registry_sync(True, rp, external=ext4)
            got2 = {r["key"]: r["code"] for r in (_read(rp) or {"records": []})["records"]}
            _write(rp, doc)                               # B:沒有撞號,只有他冊拿了比計數器大的號 → 先抬計數器再讓前一版發號
            above = {f"VIA-TOOL-{top + 3:04d}": "EV · selftest-above-only"}
            p3 = registry_sync(True, rp, external=above)
            got3 = {r["key"]: r["code"] for r in (_read(rp) or {"records": []})["records"]}
        newc = [got.get(g["key"]) for g in gone]
        newb = [got3.get(g["key"]) for g in gone]
        ok4 = bool(
            zero and p0["state"] == "PLAN" and p0["recode"] == [{"key": victim["key"], "from": victim["code"]}]
            and p1["state"] == "APPLIED" and not p1["collisions"] and [m["key"] for m in p1["recode"]] == [victim["key"]]
            and split(got.get(victim["key"]))[1] > top + 1 and vrow.get("recoded_from") == [victim["code"]]
            and all(c and c not in ext4 and split(c)[1] > top + 1 for c in newc)
            and len(set(got.values())) == len(got) and got2 == got and not p2["recode"] and not p2["collisions"]
            and not p3["recode"] and all(c and split(c)[1] > top + 3 for c in newb) and got3.get(victim["key"]) == victim["code"])
        note4 = f"{victim['code']} → {got.get(victim['key'])} · 前一版新發 {newc} · 地板 {p1['floor'].get('TOOL')} · 只抬計數器 {newb}"

        free = sorted(c for c in minted_elsewhere() if c not in held)
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "a.json", Path(td) / "b.json"
            doc = json.loads(json.dumps(base))
            if free:
                doc["records"][0]["code"] = free[0]
            k0 = doc["records"][0].get("key")
            _write(a, doc)
            _write(b, doc)
            _V0142_RS(True, a)
            rb = registry_sync(True, b)
            ca = {r["key"]: r["code"] for r in (_read(a) or {"records": []})["records"]}
            cb = {r["key"]: r["code"] for r in (_read(b) or {"records": []})["records"]}
        ok5 = bool(free) and ca == cb and cb.get(k0) == free[0] and rb["external"] == 0 and not rb["recode"] and not rb["live"]
        note5 = f"拿 {free[:1]} · 鍵 {len(cb)}"
    chk("④ 真冊副本:乾跑零寫、照列要改的號;--apply 後零撞號 —— 撞號那筆改到他冊最大號之上、留舊號;前一版新發的號也在他冊號之上;"
        "再同步一次號碼不動;沒撞號但他冊號比計數器大 → 先抬計數器、不動任何舊號", ok4, note4)
    chk("⑤ 暫存冊(不是正本元件冊)不讀他冊:和前一版逐鍵同號,拿著他冊號的那筆也不動", ok5, note5)

    b_live = live_path.read_bytes() if live_path.exists() else b""
    pl = registry_sync(False)
    chk("⑥ 正本元件冊乾跑:零寫;元件冊與他冊零撞號(他冊手寫發號撞上元件冊 → 這裡就紅,via-vcgc registry-sync --apply 讓號)",
        (live_path.read_bytes() if live_path.exists() else b"") == b_live and pl["state"] == "PLAN" and pl["live"]
        and pl["external"] >= 1 and not pl["collisions"],
        f"他冊號 {pl['external']} · 撞 {len(pl['collisions'])}" + (f" · 例 {pl['collisions'][0]}" if pl["collisions"] else ""))

    import importlib.util as _ilu
    sp = _ilu.spec_from_file_location("vcgc_selftest_late_for_v0174", Path(_V0142_RS.__code__.co_filename))
    late = _ilu.module_from_spec(sp)
    sys.modules[sp.name] = late
    try:
        sp.loader.exec_module(late)
        n_late = ensure()
        mods = _chain_mods()
        rs_all = [m.__dict__["registry_sync"] for m in mods if callable(m.__dict__.get("registry_sync"))]
        chk("⑦ 鏈上每一支持有 registry_sync 的模組都走本版(含後載的別名模組);v0172 的同步檢查也換成本版;本版包的是原函式,不自己套自己",
            late.registry_sync is registry_sync and n_late >= 1 and bool(rs_all) and all(getattr(f, "_v0174", False) for f in rs_all)
            and not any(m.__dict__.get("sync_check") is _V0172_SYNC for m in mods)
            and not getattr(_V0142_RS, "_v0174", False) and getattr(registry_sync, "__wrapped__", None) is _V0142_RS and _PATCHED >= 1,
            f"載入時換 {_PATCHED} · 後載換 {n_late}")
    finally:
        sys.modules.pop(sp.name, None)

    def fake(key):
        return {"key": key, "registry": {"new": 0, "changed": 0, "stale": 0}, "pending": False, "aligned": True}

    def fake_dry(key):
        registry_sync(False)
        return fake(key)

    real = globals()["minted_elsewhere"]
    first = next((r.get("code") for r in base["records"] if r.get("code")), "")
    try:
        globals()["minted_elsewhere"] = lambda *a, **k: {first: "EV · selftest"}
        s1, s2 = sync_check("selftest-v0174", _base=fake), sync_check("selftest-v0174", _base=fake_dry)
    finally:
        globals()["minted_elsewhere"] = real
    s0 = sync_check("selftest-v0174", _base=fake)
    chk("⑧ 同步檢查多報 registry.recode:有撞號就算待同步(正控:自己算 · 取乾跑那一份兩條路)· 他冊照實讀時 0 筆(反控)",
        bool(first) and all((s.get("registry") or {}).get("recode") == 1 and s.get("pending") is True for s in (s1, s2))
        and (s0.get("registry") or {}).get("recode") == 0 and s0.get("pending") is False
        and not any("codes_error" in s for s in (s0, s1, s2)),
        f"正控 {s1.get('registry')} / {s2.get('registry')} · 反控 {s0.get('registry')}")

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc_plan = report_codes({"state": "PLAN", "external": 3, "collisions": [{"key": "k", "code": "VIA-TOOL-0001", "other": "EV"}],
                                "recode": [{"key": "k", "from": "VIA-TOOL-0001"}]})
        rc_ok = report_codes({"state": "APPLIED", "external": 3, "collisions": [],
                              "recode": [{"key": "k", "from": "VIA-TOOL-0001", "to": "VIA-TOOL-0009"}]})
        rc_bad = report_codes({"state": "APPLIED", "external": 3, "recode": [],
                               "collisions": [{"key": "k", "code": "VIA-TOOL-0009", "other": "EV"}]})
    txt = buf.getvalue()
    bad = {"state": "APPLIED", "external": 1, "recode": [], "collisions": [{"key": "k", "code": "VIA-TOOL-0009", "other": "EV"}]}
    saved_main = PRIOR.__dict__.get("main")

    def stub(argv=None):
        _LAST.update(bad)
        return 0

    buf2 = io.StringIO()
    try:
        PRIOR.main = stub
        with contextlib.redirect_stdout(buf2):
            rc_main, rc_other = main(["registry-sync", "--apply"]), main(["status"])
    finally:
        PRIOR.main = saved_main
    _LAST.clear()
    chk("⑨ 動詞多印發號結果:乾跑列要改的號與 --apply 提示 · 寫後列改了哪些 · 寫後還撞 = rc 2;main 只對 registry-sync 接這一段",
        (rc_plan, rc_ok, rc_bad) == (0, 0, 2) and "VIA-TOOL-0001 → (--apply 改發)" in txt and "--apply 改發新號" in txt
        and "VIA-TOOL-0001 → VIA-TOOL-0009" in txt and "[仍撞] k:VIA-TOOL-0009" in txt
        and (rc_main, rc_other) == (2, 0) and buf2.getvalue().count("[仍撞]") == 1 and PRIOR.main is saved_main,
        (rc_plan, rc_ok, rc_bad, rc_main, rc_other))

    b = Path(__file__).read_text(encoding="utf-8")
    body = b.split("\ndef selftest", 1)[0]
    chk("⑩ 抬頭 raw · 帶加速器橋 · 網路橋 · VIA_FROM_VCGC 標記;不含 TA-Lib 匯入;零網路匯入;不 push、不設同意閘;冊名不釘版號(尾版律)",
        b.split("\n", 3)[2].startswith('r"""') and "[VIA:ACCEL-BRIDGE" in b and "[VIA:NET-BRIDGE" in b and "VIA_FROM_VCGC" in b
        and not re.search(r"^\s*(?:import|from)\s+" + "ta" + r"lib\b", b, re.M)
        and not re.search(r"^\s*(?:import|from)\s+(?:requests|urllib|socket|httpx)\b", body, re.M)
        and not re.search(r"""["']push["']""", body) and not re.search(r"environ\[[\"']VIA_(?:NET|SCRAPE)_CONSENT", body)
        and not re.search(r"VIA_EngineVersion_Register_v\d{4}\.json", body))
    if not all(ok):
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    a = sys.argv[1:]
    raise SystemExit(selftest() if a == ["--selftest"] else main())
