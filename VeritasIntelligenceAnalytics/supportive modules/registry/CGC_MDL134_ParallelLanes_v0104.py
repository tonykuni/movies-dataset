#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL134_ParallelLanes v0104 — 薄尾:cmd groups · cmd which · 整合 PY 指令(consolidated)· RETIRED / DEPRECATED 亮灰

操作員令(2026-11-19):「將上述整合成數個 PY 指令導入加速器」(上述 = 212 支短令,30 支沒加速器)。
本版只加這些,前版 cmd list / check / plan / run、監工、降壓、頁 一字不動:
  cmd groups                   212 支短令依所屬系統收進四個 PY 入口(via-vcgc · via-vdf · via-vrn · via-vap):每入口支數 × 狀態 × 加速器燈;
                               另列 consolidated 的整合 PY 指令(每步 PY 尾版都要語法樹真匯入加速器,缺一 = 紅)
  cmd which <短令>             印出這支短令背後的 Python 指令(尾版路徑 + 參數);已被整合的指到整合指令;零子行程
  cmd run <整合指令>           consolidated 的 vcgc-check / vcgc-env / vcgc-repair 跟一般路由一樣跑(先降壓 → 3~6 道 → 監工)
  cmd check                    RETIRED(依律停用)與 DEPRECATED(舊外殼保留,唯讀部分已整合)亮灰並寫明去處,不再算黃
邊界:VDF / VRN 的短令只列、只查,不經本檔跑(它們走自己的管理員);VCGC 的整合指令只用唯讀動詞,寫入步驟照舊叫原短令。
零網路 · 不碰 TA-Lib · 不寫冊。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入;本檔零網路,橋只為全樹一致。"""
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
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL134_ParallelLanes"
TAG = "v0104"
ENTRY_OF = {"VCGC": "via-vcgc", "CORE": "via-vcgc", "VDF": "via-vdf", "VRN": "via-vrn", "VAP": "via-vap"}
QUIET_STATES = {"RETIRED": "依律停用", "DEPRECATED": "已整合"}


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + TAG, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

_PRIOR_FIND = PRIOR.find_route
_PRIOR_CHECK = PRIOR.check_routes
_PRIOR_CMD_MAIN = PRIOR.cmd_main


def __getattr__(name):
    return getattr(PRIOR, name)


def find_route(book: dict, name: str):
    """先找短令路由,再找整合指令(consolidated);整合指令一律當 PY 路由跑。"""
    r = _PRIOR_FIND(book, name)
    if r is not None:
        return r
    for c in book.get("consolidated", []):
        if c.get("name", "").lower() == name.lower():
            return dict(c, state="PY", owner="VCGC")
    return None


def check_routes(book: dict, names: list | None = None, root: Path | None = None) -> list:
    rows = _PRIOR_CHECK(book, names, root)
    by = {r["name"]: r for r in book.get("routes", [])}
    for row in rows:
        r = by.get(row["name"], {})
        if r.get("state") in QUIET_STATES:
            go = r.get("replaced_by")
            row["lamp"] = "GRAY"
            row["detail"] = QUIET_STATES[r["state"]] + ":" + ("改用 via-lanes cmd run " + go + " · " if go else "") + (r.get("reason") or "")
    return rows


def check_consolidated(book: dict, root: Path | None = None) -> list:
    """整合指令每一步:尾版在 · ast.parse · compile · 語法樹真匯入加速器;缺一 = 紅。"""
    rows = []
    for c in book.get("consolidated", []):
        bad, notes = [], []
        for s in c.get("steps", []):
            t = PRIOR.tail_of(s, root)
            if t is None:
                bad.append(s["id"] + " 尾版不在(" + s.get("glob", "") + ")")
                continue
            ok, why = PRIOR.accel_in_ast(t)
            notes.append(s["id"] + "=" + t.name)
            if not ok:
                bad.append(s["id"] + " " + why)
        rows.append({"name": c["name"], "entry": c.get("entry", "via-vcgc"), "title": c.get("title", ""), "replaces": c.get("replaces", []),
                     "lamp": "RED" if bad or not c.get("steps") else "GREEN", "detail": ";".join(bad) if bad else " · ".join(notes)})
    return rows


def groups(book: dict, root: Path | None = None) -> dict:
    rows = check_routes(book, None, root)
    by = {r["name"]: r for r in book.get("routes", [])}
    ent = {}
    for row in rows:
        r = by.get(row["name"], {})
        e = r.get("entry") or ENTRY_OF.get(r.get("owner", ""), "via-vcgc")
        g = ent.setdefault(e, {"total": 0, "state": {}, "lamp": {}, "red": []})
        g["total"] += 1
        g["state"][r.get("state", "?")] = g["state"].get(r.get("state", "?"), 0) + 1
        g["lamp"][row["lamp"]] = g["lamp"].get(row["lamp"], 0) + 1
        if row["lamp"] == "RED":
            g["red"].append(row["name"])
    cons = check_consolidated(book, root)
    tn = PRIOR.three_numbers(book)
    red = any(g["red"] for g in ent.values()) or any(c["lamp"] == "RED" for c in cons)
    yellow = any(g["lamp"].get("YELLOW") for g in ent.values())
    return {"three": tn, "entries": ent, "consolidated": cons,
            "lamp": "RED" if red or tn["lamp"] != "GREEN" else ("YELLOW" if yellow else "GREEN")}


def cmd_groups(book: dict, echo=print, root: Path | None = None) -> int:
    g = groups(book, root)
    tn = g["three"]
    echo("[cmd groups] " + g["lamp"] + " · 短令 應掃 " + str(tn["should"]) + " · 已掃 " + str(tn["scanned"]) + " · 略過 " + str(tn["skipped"])
         + " · 收進 " + str(len(g["entries"])) + " 個 PY 入口 + " + str(len(g["consolidated"])) + " 個整合 PY 指令")
    for e in sorted(g["entries"]):
        x = g["entries"][e]
        echo("  " + e.ljust(9) + str(x["total"]).rjust(4) + " 支 · " + " ".join(k + " " + str(v) for k, v in sorted(x["state"].items()))
             + " · 燈 " + " ".join(k + " " + str(v) for k, v in sorted(x["lamp"].items())) + ((" · 紅:" + "、".join(x["red"])) if x["red"] else ""))
    for c in g["consolidated"]:
        echo("  " + c["lamp"].ljust(7) + c["name"].ljust(12) + c["title"] + " · 取代 " + "、".join(c["replaces"]) + " · " + c["detail"][:160])
    return 1 if g["lamp"] == "RED" else (2 if g["lamp"] == "YELLOW" else 0)


def which(book: dict, name: str, root: Path | None = None) -> dict:
    r = find_route(book, name)
    if r is None:
        return {"name": name, "found": False}
    go = r.get("replaced_by")
    out = {"name": r["name"], "found": True, "state": r.get("state"), "entry": r.get("entry") or ENTRY_OF.get(r.get("owner", ""), "via-vcgc"),
           "replaced_by": go, "reason": r.get("reason", ""), "python": []}
    for s in r.get("steps", []):
        t = PRIOR.tail_of(s, root)
        out["python"].append({"id": s["id"], "file": str(t) if t else None, "args": s.get("args", []), "needs": s.get("needs", [])})
    return out


def cmd_which(book: dict, name: str, echo=print, root: Path | None = None) -> int:
    w = which(book, name, root)
    if not w["found"]:
        echo("[cmd which] 冊上沒有 " + name + "(零子行程)")
        return 2
    echo("[cmd which] " + w["name"] + " · " + str(w["state"]) + " · 入口 " + w["entry"] + ((" · 改用 via-lanes cmd run " + w["replaced_by"]) if w["replaced_by"] else ""))
    for p in w["python"]:
        echo("  " + p["id"].ljust(10) + ("python " + Path(p["file"]).name + " " + " ".join(p["args"]) if p["file"] else "尾版不在")
             + ((" · 等 " + "、".join(p["needs"])) if p["needs"] else ""))
    if not w["python"]:
        echo("  (沒有 Python 步:" + (w["reason"] or "PS 本職 / 轉呼叫") + ")")
    return 0


def install():
    PRIOR.find_route = find_route          # 前版 cmd run / plan 經模組全域找路由 → 換上會找整合指令的版本
    PRIOR.check_routes = check_routes      # 前版 cmd check 經模組全域 → RETIRED / DEPRECATED 亮灰
    PRIOR.TAG = TAG


def cmd_main(a: list) -> int:
    install()
    verb = a[0] if a else "list"
    if verb in ("groups", "which"):
        book = PRIOR.load_book()
        if book.get("_path") is None:
            print("[cmd] RED · 路由冊 " + PRIOR.ROUTE_BOOK_PAT + " 不在(零子行程)")
            return 1
        if verb == "groups":
            return cmd_groups(book)
        if len(a) < 2:
            print("[cmd] 用法:cmd which <短令>(零子行程)")
            return 2
        return cmd_which(book, a[1])
    return _PRIOR_CMD_MAIN(a)


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== " + _STEM + " " + TAG + " · 薄尾自測(cmd groups · which · 整合指令 · 退役亮灰)===")
        return selftest()
    if a and a[0] == "cmd":
        return cmd_main(a[1:])
    return PRIOR.main()


def selftest() -> int:
    rc_prior = PRIOR.selftest()            # 前版自測(本版還沒 install,前版行為原樣)
    n = {"ok": 0, "bad": 0}

    def chk(name, cond, note=""):
        n["ok" if cond else "bad"] += 1
        print("  " + ("✓" if cond else "✗") + " " + name + ((" · " + str(note)) if note and not cond else ""))
    quiet = lambda *_a, **_k: None  # noqa: E731
    with tempfile.TemporaryDirectory(prefix="via_lanes_v0104_") as td:
        root = Path(td)
        (root / "eng").mkdir()
        bridge = "try:\n    import VIA_SuperAccel_Module as VIA_ACCEL\nexcept Exception:\n    VIA_ACCEL = None\n"
        (root / "eng" / "OK_v0100.py").write_text(bridge + "print('ok')\n", encoding="utf-8")
        (root / "eng" / "NOB_v0100.py").write_text("print('no bridge')\n", encoding="utf-8")
        st = lambda i, g, **k: dict({"id": i, "dir": "eng", "glob": g}, **k)  # noqa: E731
        book = {"_path": str(root / "book.json"), "inventory": {"should_scan": 5, "skipped": []},
                "routes": [{"name": "via-a", "owner": "VCGC", "entry": "via-vcgc", "state": "PY_ALREADY", "steps": [st("e1", "OK_v*.py")]},
                           {"name": "via-b", "owner": "VDF", "entry": "via-vdf", "state": "PY_ALREADY", "steps": [st("e1", "OK_v*.py")]},
                           {"name": "via-old", "owner": "CORE", "state": "DEPRECATED", "replaced_by": "vcgc-x", "reason": "唯讀部分已整合"},
                           {"name": "via-tl", "owner": "VCGC", "state": "RETIRED", "reason": "L50"},
                           {"name": "via-todo", "owner": "CORE", "state": "TODO", "reason": "下一批"}],
                "consolidated": [{"name": "vcgc-x", "entry": "via-vcgc", "title": "整合", "replaces": ["via-old"],
                                  "steps": [st("s1", "OK_v*.py"), st("s2", "OK_v*.py", needs=["s1"])]},
                                 {"name": "vcgc-bad", "entry": "via-vcgc", "title": "壞", "replaces": [], "steps": [st("s1", "NOB_v*.py")]}]}
        rows = {r["name"]: r for r in check_routes(book, None, root)}
        chk("① DEPRECATED / RETIRED 亮灰並寫明去處(不再算黃)", rows["via-old"]["lamp"] == "GRAY" and "vcgc-x" in rows["via-old"]["detail"]
            and rows["via-tl"]["lamp"] == "GRAY" and rows["via-todo"]["lamp"] == "YELLOW", {k: v["lamp"] for k, v in rows.items()})
        g = groups(book, root)
        chk("② groups:依入口分(via-vcgc 4 · via-vdf 1)· 三數對得上", g["entries"]["via-vcgc"]["total"] == 4 and g["entries"]["via-vdf"]["total"] == 1
            and g["three"]["lamp"] == "GREEN", g["entries"])
        cs = {c["name"]: c["lamp"] for c in g["consolidated"]}
        chk("③ 整合指令每步都要語法樹真匯入加速器:缺橋那支 = 紅 → 總燈紅", cs == {"vcgc-x": "GREEN", "vcgc-bad": "RED"} and g["lamp"] == "RED", cs)
        r = find_route(book, "vcgc-x")
        chk("④ find_route 找得到整合指令,而且當 PY 跑", r is not None and r["state"] == "PY")
        jobs, miss = PRIOR.build_jobs(r, [], sys.executable, root)
        chk("⑤ 整合指令建步:兩步 · s2 等 s1 · 沒有缺件", [j["id"] for j in jobs] == ["s1", "s2"] and jobs[1]["needs"] == ["s1"] and not miss, jobs)
        w = which(book, "via-old", root)
        chk("⑥ which:被整合的短令指到整合指令;整合指令列出 Python 尾版", w["replaced_by"] == "vcgc-x" and which(book, "vcgc-x", root)["python"][0]["file"].endswith("OK_v0100.py"))
        install()
        chk("⑦ install 後前版 cmd run 也找得到整合指令(dry,零子行程)",
            PRIOR.cmd_run(book, "vcgc-x", ["--dry"], echo=quiet, root=root) == 0)
    real = PRIOR.load_book()
    if real.get("_path"):
        g = groups(real)
        chk("⑧ 真路由冊:212 支三數對得上 · 四個入口 · 整合指令每步尾版都在且帶橋",
            g["three"]["lamp"] == "GREEN" and set(g["entries"]) <= {"via-vcgc", "via-vdf", "via-vrn", "via-vap"}
            and all(c["lamp"] == "GREEN" for c in g["consolidated"]), [(c["name"], c["detail"][:80]) for c in g["consolidated"] if c["lamp"] != "GREEN"])
    passed = rc_prior == 0 and n["bad"] == 0
    print("[計] " + _STEM + " " + TAG + " 本版 " + str(n["ok"]) + "/" + str(n["ok"] + n["bad"]) + " · 前版 " + ("PASS" if rc_prior == 0 else "FAIL") + " · " + ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
