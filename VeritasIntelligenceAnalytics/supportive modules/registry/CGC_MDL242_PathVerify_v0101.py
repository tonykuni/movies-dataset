#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL242_PathVerify v0101 — 單一路徑驗證 + 涵蓋稽核(橋 · 四件工具 · 版本/編號/註冊時間 · 多來源 · 下市/上市 · SSOT · 計時)

R29(操作員:「PS 有無加入加速器 網路工具 LAYOUT 及所有引擎有無加入 … 確定所有引擎都有加版本號 編號 註冊時間 所有參數即使相同數據
不同來源也是編號不同 下市個股編號不蓋 上市新增 檢查 SSOT 版本編號完善 自 VCGC 更快速啟動所有」):
v0100 的頁與 JSON 照舊,多一段「⑤ 涵蓋稽核」(本支不另立尺;每列寫明是哪一把正主量的):
  C1 橋:CGC_MDL124 BridgeSweeper `--subsystems` 四系總表(全景實測步 ④ 的原句)· CGC_MDL230 工具探針 Ⓒ(CGC_MDL183 量的 PY 橋 / PS 模板章 ·
     VDF 尾版加速器橋 / 網路橋 · TA-Lib 零匯入)。網路橋只有 VDF 是法定面(VRN / VCGC 經 VCGC 資料中介拿料,刻意不直連網路)。
  C2 四件工具:ENV MANAGER A1(鎖版)/ A2(載得起來)— 加速器 · 網路 · LAYOUT · NLP。
  C3 引擎:VCGC / VDF / VRN / SUP 各自的尾版 × 編號冊(號 + numbered_at)× 註冊冊(first_seen);沒版號檔另計(多為輔助檔 / 套件)。
  C4 多來源:同名不同來源各自一號(PRMT · MRC · FD · FM · SSOT · RGX · SYN);全冊號碼不重複。
  C5 下市 / 上市:FM 冊在市 · 下市(gone_since,號不動)· 代號重用新號(#Ln)· 復牌 · 改名;守則在 CGC_MDL237 v0102 以上。
  C6 SSOT:編號冊 SSOT 列帶 content_sha / declared_version 的比例;已追蹤的 *SSOT*.json 有沒有號。
  C7 計時:唯一入口 v0104 起寫的 TIMING_latest.json(各步秒數 · 全景實測是否沿用)。
紅燈只給「壞了」:橋缺 > 0、號碼重複、同名不同來源共用號;已知欠帳(L70 舊 PS 章 · 沒註冊的舊檔)是黃燈照列。
其餘整支照 v0100(thin tail;__getattr__ 轉接)。
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

import html as _html
import importlib.util
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL242_PathVerify"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
ENGINE = Path(__file__).stem
VIA, REP, OUT, LEDGER, ORDER = _PRIOR.VIA, _PRIOR.REP, _PRIOR.OUT, _PRIOR.LEDGER, _PRIOR.ORDER
_json = _PRIOR._json
SUBSYSTEMS = (("VCGC", "supportive modules/registry"), ("VDF", "functional modules/VDF"), ("VRN", "functional modules/VRN"),
              ("SUP", "supportive modules"))
MULTI_KINDS = ("PRMT", "MRC", "FD", "FM", "SSOT", "RGX", "SYN")
RX_BRIDGE = re.compile(r"四系總表\s*(.+?)(?:\s*·\s*具名豁免|$)")
RX_PAIR = re.compile(r"([A-Z]+)/(accel|net)\s+(\d+)/(\d+)")
_ORIG = {"run": _PRIOR.run, "record": _PRIOR.record}
LAST: dict = {}


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def _row(sec, item, state, note, ruler) -> dict:
    return {"sec": sec, "item": item, "state": state, "note": note, "ruler": ruler}


# ---------------------------------------------------------------- C1 bridges · C2 tools (read the rulers' own evidence)

def bridge_rows(side: dict | None = None, probe: dict | None = None) -> list:
    side = _json(REP / "sweep" / "SWEEP_SIDE_latest.json") if side is None else side
    probe = _json(REP / "toolprobe" / "TOOLPROBE_latest.json") if probe is None else probe
    out = []
    line = next((ln for s in (side or {}).get("steps") or [] if s.get("id") == "bridge" for ln in s.get("lines") or [] if "四系總表" in ln), "")
    m = RX_BRIDGE.search(line)
    for sub, kind, done, den in RX_PAIR.findall(m.group(1) if m else ""):
        miss = int(den) - int(done)
        out.append(_row("C1 橋", f"{sub} · {'加速器' if kind == 'accel' else '網路'}橋", "GREEN" if miss == 0 else "RED",
                        f"{done}/{den}" + ("" if miss == 0 else f" · 缺 {miss}"), "CGC_MDL124 BridgeSweeper --subsystems"))
    if not out:
        out.append(_row("C1 橋", "四系橋掃", "NODATA", "全景實測側車沒有橋掃總表(先跑一次全景實測)", "CGC_MDL124 BridgeSweeper --subsystems"))
    for sec in (probe or {}).get("sections") or []:
        if not (isinstance(sec, list) and sec and str(sec[0]).startswith("Ⓒ")):
            continue
        for r in sec[2] if len(sec) > 2 else []:
            if len(r) >= 8:
                out.append(_row("C1 橋", str(r[1]), _PRIOR.LAMP.get(str(r[0]).upper(), "AMBER"), f"{r[4]}/{r[3]} · 缺 {r[6]} · {r[7]}"
                                + (f" · 不計 {r[5]}" if r[5] not in ("—", "") else ""), str(r[2]).split("(")[0]))
    return out


def tool_rows(ev: dict | None = None) -> list:
    ev = _json(REP / "env_manager" / "ENVMGR_latest.json") if ev is None else ev
    rows = [r for r in (ev or {}).get("rows") or [] if r.get("id") in ("A1", "A2")]
    out = [_row("C2 四件工具", ("鎖版 · " if r["id"] == "A1" else "載入 · ") + str(r.get("item", "")).split("·")[-1].strip(),
                _PRIOR.LAMP.get(r.get("state"), "AMBER"), str(r.get("note", ""))[:120], "CGC_MDL240 ENV MANAGER") for r in rows]
    return out or [_row("C2 四件工具", "加速器 · 網路 · LAYOUT · NLP", "NODATA", "ENVMGR_latest.json 不在(先跑 ENV MANAGER)", "CGC_MDL240 ENV MANAGER")]


# ---------------------------------------------------------------- C3 engines: version · number · register time

def _books() -> dict:
    out = defaultdict(list)
    for b in sorted((HERE / "VIA_NumberBooks").glob("VIA_NumberBook_*_v*.jsonl")):
        kind = re.sub(r"^VIA_NumberBook_|_v\d+\.jsonl$", "", b.name).split("_")[0]
        with b.open(encoding="utf-8") as f:
            out[kind] += [json.loads(line) for line in f if line.strip()]
    ssot = _json(HERE / "VIA_Numbering_SSOT_v0100.json") or {}
    for kind, rows in (ssot.get("rows") or {}).items():
        out[kind] += rows
    return out


def _register_rules():
    """The VCGC register's own scope rules (tail shape + named exclusions), read from the console tail; None when it cannot load."""
    try:
        m = _PRIOR._mod("CGC_MDL149_VeritasCentralGovernanceConsole")
        while m is not None and not hasattr(m, "_excuse"):
            m = getattr(m, "PRIOR", None) or getattr(m, "_PRIOR", None)
        return (m.TAIL_PY, m._excuse) if m is not None else None
    except Exception:
        return None


def why_unregistered(relp: str, rules) -> str:
    """Why a tail has no register row: outside the register's own rules (named exclusion / non-4-digit version) or simply not synced yet."""
    if rules is not None:
        tail_py, excuse = rules
        why = excuse(relp, None)
        if why:
            return "具名排除:" + str(why).split("、")[0][:40]
        if not tail_py.search(Path(relp).name):
            return "版號異形(非四碼;尾版律不管)"
    elif not re.search(r"_v\d{4}$", Path(relp).stem):
        return "版號異形(非四碼;尾版律不管)"
    return "待 registry-sync"


def engine_rows(books: dict | None = None, reg: dict | None = None, rules="auto") -> tuple:
    books = _books() if books is None else books
    nums = {}
    for kind in ("MDL", "ENG"):
        for r in books.get(kind, []):
            if not r.get("gone_since"):
                nums.setdefault(str(r.get("name")), (r.get("code"), r.get("numbered_at")))
    fams = set()
    if reg is None:
        reg = {}
        for r in (_json(HERE / "VIA_Component_Inventory_SSOT_v0100.json") or {}).get("records") or []:
            src = str(r.get("source") or "")
            if src.endswith(".py") and r.get("state") == "ACTIVE":
                reg.setdefault(src, r.get("first_seen") or r.get("changed_at"))
                if r.get("category") in ("module", "engine", "system"):
                    fams.add(str(r.get("identity")))
    rules = _register_rules() if rules == "auto" else rules
    out, detail = [], {}
    for sub, rel in SUBSYSTEMS:
        tails, unversioned = {}, 0
        for p in (VIA / rel).rglob("*.py"):
            sp = p.as_posix()
            if any(x in sp for x in ("/references/", "SCOPE_COPY", "__pycache__", "/tests/")) or (sub == "SUP" and "/registry/" in sp):
                continue
            if _vnum(p) < 0:
                unversioned += 1
                continue
            k = (str(p.parent), re.sub(r"_v\d+$", "", p.stem))
            if k not in tails or _vnum(p) > _vnum(tails[k]):
                tails[k] = p
        no_num, no_reg, no_time, no_ntime, why_reg = [], [], [], [], Counter()
        for p in tails.values():
            relp = p.relative_to(VIA).as_posix()
            n = nums.get(p.stem)
            if not n:
                no_num.append(p.name)
            elif not n[1]:
                no_ntime.append(p.name)
            if relp not in reg:
                w = ("同名副本(註冊冊按家族記一份)" if re.sub(r"_v\d+$", "", p.stem) in fams else why_unregistered(relp, rules))
                why_reg[w.split(":")[0]] += 1
                if w == "待 registry-sync":
                    no_reg.append(p.name)
            elif not reg[relp]:
                no_time.append(p.name)
        t = len(tails)
        n_reg = t - sum(why_reg.values())
        state = "GREEN" if not (no_num or no_reg or no_time or no_ntime) else "AMBER"
        note = (f"尾版 {t} · 有號 {t - len(no_num)}(帶編號時間 {t - len(no_num) - len(no_ntime)})· 已註冊 {n_reg}"
                f"(帶註冊時間 {n_reg - len(no_time)})" + "".join(f" · {k} {v}" for k, v in sorted(why_reg.items()) if k != "待 registry-sync")
                + f" · 待註冊 {len(no_reg)} · 沒版號檔 {unversioned}")
        if no_num or no_reg:
            note += " · 缺:" + "、".join(sorted(set(no_num + no_reg))[:6]) + (" …" if len(set(no_num + no_reg)) > 6 else "")
        out.append(_row("C3 引擎版號 · 編號 · 註冊時間", sub, state, note, "編號冊 MDL/ENG × VCGC 元件註冊冊"))
        detail[sub] = {"tails": t, "no_number": sorted(no_num), "no_register": sorted(no_reg), "outside_register_rules": dict(why_reg),
                       "no_register_time": sorted(no_time),
                       "no_number_time": sorted(no_ntime), "unversioned": unversioned}
    return out, detail


# ---------------------------------------------------------------- C4 multi-source · C5 delist/list · C6 SSOT

def multi_source_rows(books: dict | None = None) -> list:
    books = _books() if books is None else books
    out = []
    code_use = Counter()
    for kind, rows in books.items():
        code_use.update(str(r.get("code")) for r in rows if r.get("code"))
    dup = [c for c, n in code_use.items() if n > 1]
    out.append(_row("C4 多來源", "全冊號碼不重複", "GREEN" if not dup else "RED",
                    f"{sum(code_use.values())} 列 · 重複 {len(dup)}" + (":" + "、".join(dup[:5]) if dup else ""), "編號冊(CGC_MDL237)"))
    for kind in MULTI_KINDS:
        rows = books.get(kind, [])
        if not rows:
            continue
        groups = defaultdict(list)
        for r in rows:
            groups[str(r.get("name"))].append(r)
        multi = {n: g for n, g in groups.items() if len({str(x.get("source")) for x in g}) > 1}
        shared = [n for n, g in multi.items() if len({x.get("code") for x in g}) < len(g)]
        out.append(_row("C4 多來源", f"{kind} 同名不同來源", "GREEN" if not shared else "RED",
                        f"{len(rows)} 列 · 同名多來源 {len(multi)} 組 · 共用號 {len(shared)}" + (":" + "、".join(shared[:4]) if shared else ""),
                        "編號冊(CGC_MDL237)"))
    return out


def listing_rows(books: dict | None = None) -> list:
    books = _books() if books is None else books
    fm = books.get("FM", [])
    live = sum(1 for r in fm if not r.get("gone_since"))
    gone = len(fm) - live
    relist = sum(1 for r in fm if "#L" in str(r.get("key")))
    revived = sum(1 for r in fm if r.get("gone_history"))
    renamed = sum(1 for r in fm if r.get("name_history"))
    tail = _PRIOR.tail_of("CGC_MDL237_NumberingSystem")
    guard = tail is not None and _vnum(tail) >= 102
    return [_row("C5 下市 / 上市", "FM 金融市場代號", "GREEN" if guard else "AMBER",
                 f"{len(fm)} 列 · 在市 {live} · 下市 {gone}(號不動)· 代號重用新號 {relist} · 復牌 {revived} · 改名 {renamed}"
                 + ("" if guard else " · 守則尾版不在(CGC_MDL237 v0102 以上)"), (tail.name if tail else "CGC_MDL237 不在"))]


def ssot_rows(books: dict | None = None) -> list:
    books = _books() if books is None else books
    rows = books.get("SSOT", [])
    sha = sum(1 for r in rows if r.get("content_sha"))
    dv = sum(1 for r in rows if r.get("declared_version"))
    out = [_row("C6 SSOT", "SSOT 冊編號 · 內容指紋 · 宣告版號", "GREEN" if rows and sha == len(rows) else "AMBER",
                f"{len(rows)} 本有號 · 帶內容指紋 {sha} · 冊內宣告版號 {dv}(其餘冊沒寫版號,以檔名版號 + 指紋為準)", "編號冊 SSOT 列")]
    try:
        tracked = subprocess.run(["git", "ls-files", "*SSOT*.json"], cwd=VIA, capture_output=True, text=True, timeout=60).stdout.splitlines()
    except Exception:
        tracked = []
    have = {str(r.get("source")) for r in rows}
    skip = ("VIA_Reports/", "references/", "SCOPE_COPY", ".freeze.lock.json", ".local.json")
    missing = [t for t in tracked if t not in have and not any(x in t for x in skip)]
    out.append(_row("C6 SSOT", "已追蹤 *SSOT*.json 都有號", "GREEN" if not missing else "AMBER",
                    f"{len(tracked)} 檔 · 沒號 {len(missing)}(凍結鎖改記 ENV 凍結鎖;.local 本機檔不計)"
                    + (":" + "、".join(Path(m).name for m in missing[:5]) if missing else ""), "git ls-files × 編號冊"))
    return out


def timing_rows(tj: dict | None = None) -> list:
    tj = _json(REP / "operator_console" / "TIMING_latest.json") if tj is None else tj
    if not tj:
        return [_row("C7 計時", "唯一入口各步秒數", "NODATA", "TIMING_latest.json 不在(唯一入口 v0104 起才寫)", "Invoke-VIA-OperatorConsole")]
    steps = tj.get("steps") or {}
    top = sorted(steps.items(), key=lambda kv: -float(kv[1] or 0))[:4]
    return [_row("C7 計時", f"全程 {tj.get('total_sec')} 秒" + ("(全景實測沿用上一輪)" if tj.get("sweep_reused") else ""), "GREEN",
                 " · ".join(f"{k} {v}s" for k, v in top) + f" · {tj.get('at', '')}", str(tj.get("entry") or "Invoke-VIA-OperatorConsole"))]


def coverage() -> dict:
    books = _books()
    eng, detail = engine_rows(books)
    rows = bridge_rows() + tool_rows() + eng + multi_source_rows(books) + listing_rows(books) + ssot_rows(books) + timing_rows()
    tally = Counter(r["state"] for r in rows)
    return {"rows": rows, "engines": detail, "tally": dict(tally),
            "state": "RED" if tally.get("RED") else ("AMBER" if tally.get("AMBER") or tally.get("NODATA") else "GREEN")}


# ---------------------------------------------------------------- page · record · run

def coverage_html(cov: dict, lamp) -> str:
    e = _html.escape
    rows = "".join(f"<tr><td>{lamp(r['state'], r['state'])}</td><td>{e(r['sec'])}</td><td>{e(r['item'])}</td><td>{e(r['note'])}</td>"
                   f"<td>{e(r['ruler'])}</td></tr>" for r in cov["rows"])
    return (f"<h3>⑤ 涵蓋稽核(橋 · 四件工具 · 版號/編號/註冊時間 · 多來源 · 下市/上市 · SSOT · 計時)· {e(cov['state'])}</h3>"
            f"<table class='via'><tr><th>燈</th><th>段</th><th>項</th><th>量到</th><th>哪一把正主</th></tr>{rows}</table>")


class _KitProxy:
    """The template kit, with the coverage section appended to the page body (one page, one kit)."""

    def __init__(self, kit, extra: str):
        self._kit, self._extra = kit, extra

    def __getattr__(self, name):
        return getattr(self._kit, name)

    def page(self, title, body, side, **kw):
        return self._kit.page(title, body + self._extra, side, **kw)


def record(rep: dict, ledger: Path = LEDGER) -> dict:
    row = _ORIG["record"](rep, ledger=_NULL)
    cov = rep.get("coverage") or {}
    row["coverage"] = {"state": cov.get("state"), "tally": cov.get("tally"),
                       "engines": {k: {"tails": v["tails"], "no_number": len(v["no_number"]), "no_register": len(v["no_register"])}
                                   for k, v in (cov.get("engines") or {}).items()}}
    tj = _json(REP / "operator_console" / "TIMING_latest.json") or {}
    row["timing"] = {"total_sec": tj.get("total_sec"), "sweep_reused": tj.get("sweep_reused")} if tj else None
    with Path(ledger).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return row


class _Null:
    """A ledger stand-in: v0100's record() builds the row; v0101 adds coverage and writes the one line itself."""

    def open(self, *a, **k):
        import io
        return io.StringIO()


_NULL = _Null()


def run(write: bool = True, rec: bool = True) -> dict:
    rep = _ORIG["run"](write=False, rec=False)
    cov = coverage()
    rep["engine"], rep["coverage"] = ENGINE, cov
    if cov["state"] == "RED":
        rep["verdict"] = "RED"
    if write:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "PATH_VERIFY_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        kit = _PRIOR._mod("CGC_MDL241_TemplateAdapter")
        if kit is not None:
            proxy = _KitProxy(kit, coverage_html(cov, kit.lamp))
            (OUT / "PATH_VERIFY_latest.html").write_text(_PRIOR.page(rep["steps"], rep["versions"], rep["results"], rep["verdict"], proxy),
                                                         encoding="utf-8")
        with (OUT / "HISTORY.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": rep["ts"], "verdict": rep["verdict"], "coverage": cov["state"], **rep["results"]["now"]},
                               ensure_ascii=False) + "\n")
        if rec:
            rep["record"] = str(LEDGER)
            record(rep)
    LAST.clear()
    LAST.update(rep)
    return rep


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    _PRIOR.run = run                         # v0100's main() prints the path, versions and verdict from this run
    rc = _PRIOR.main(args)
    cov = LAST.get("coverage")
    if cov:
        for r in cov["rows"]:
            print(f"  {r['state']:<6} {r['sec']} · {r['item']} · {r['note'][:110]}")
        print(f"  [涵蓋稽核] {cov['state']} · " + " · ".join(f"{k} {v}" for k, v in sorted(cov["tally"].items())))
    return rc


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    side = {"steps": [{"id": "bridge", "lines": ["[橋掃] 四系總表 VDF/accel 131/131 (100.0%) · VDF/net 130/131 (99.2%) · VRN/accel 149/149 (100.0%)"
                                                  " · 具名豁免名冊 1 條"]}]}
    br = bridge_rows(side, {"sections": []})
    chk("C1 橋掃總表逐系解析;缺一支就紅", [r["state"] for r in br] == ["GREEN", "RED", "GREEN"] and br[1]["note"].endswith("缺 1"),
        " · ".join(r["item"] + " " + r["note"] for r in br))
    chk("C1 沒有橋掃總表 = NODATA(不發明數字)", bridge_rows({"steps": []}, {})[0]["state"] == "NODATA")
    books = {"PRMT": [{"code": "A1", "name": "x", "source": "a.py"}, {"code": "A2", "name": "x", "source": "b.py"}],
             "FD": [{"code": "F1", "name": "y", "source": "s1"}, {"code": "F1", "name": "y", "source": "s2"}]}
    ms = {r["item"]: r["state"] for r in multi_source_rows(books)}
    chk("C4 同名不同來源各自一號 = 綠;共用號 = 紅;全冊重號 = 紅",
        ms.get("PRMT 同名不同來源") == "GREEN" and ms.get("FD 同名不同來源") == "RED" and ms.get("全冊號碼不重複") == "RED", ms)
    fm = {"FM": [{"code": "c1", "key": "1234@v0100", "name": "甲", "gone_since": "t"}, {"code": "c2", "key": "1234#L2@v0100", "name": "丙"},
                 {"code": "c3", "key": "2222@v0100", "name": "丁", "gone_history": ["t"], "name_history": ["丁舊"]}]}
    ls = listing_rows(fm)[0]
    chk("C5 下市列號不動 · 重用新號 · 復牌 · 改名都數得到", "下市 1" in ls["note"] and "代號重用新號 1" in ls["note"] and "復牌 1" in ls["note"]
        and "改名 1" in ls["note"], ls["note"])
    cov = coverage()
    secs = {r["sec"] for r in cov["rows"]}
    chk("涵蓋稽核七段都在(真冊)", {"C1 橋", "C2 四件工具", "C3 引擎版號 · 編號 · 註冊時間", "C4 多來源", "C5 下市 / 上市", "C6 SSOT", "C7 計時"} <= secs,
        f"{len(cov['rows'])} 列 · {cov['tally']}")
    chk("C3 四個子系統都量到尾版", set(cov["engines"]) == {"VCGC", "VDF", "VRN", "SUP"} and all(v["tails"] > 0 for v in cov["engines"].values()),
        {k: v["tails"] for k, v in cov["engines"].items()})
    chk("C3 沒註冊分三種:具名排除 · 版號異形 · 待同步", why_unregistered("supportive modules/registry/X_v1.py", None).startswith("版號異形")
        and why_unregistered("supportive modules/registry/X_v0100.py", None) == "待 registry-sync"
        and why_unregistered("a/CGC_MDL190_TALibLock_v0100.py", (re.compile(r"_v\d{4}\.py$"), lambda r, e: "預防:TA-Lib" if "TALib" in r else "")).startswith("具名排除"))
    chk("C4 真冊:全冊號碼不重複", next(r for r in cov["rows"] if r["item"] == "全冊號碼不重複")["state"] == "GREEN")

    class Kit:
        @staticmethod
        def page(title, body, side, **kw):
            return body

    chk("頁:涵蓋段接在同一頁(同一個模板套件)", _KitProxy(Kit, "<h3>⑤</h3>").page("t", "<h3>①</h3>", "") == "<h3>①</h3><h3>⑤</h3>")
    rep = run(write=False, rec=False)
    chk("run:v0100 的路徑 / 版本 / 結果照舊 + coverage", all(k in rep for k in ("steps", "versions", "results", "coverage")) and rep["engine"] == ENGINE)
    ok = all(results)
    print(f"  {ENGINE} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
