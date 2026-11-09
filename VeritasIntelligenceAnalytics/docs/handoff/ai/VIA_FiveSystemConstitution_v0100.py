# -*- coding: utf-8 -*-
"""VIA_FiveSystemConstitution v0100 —— 五系統編號憲法矩陣(政策 L125;操作員 2026-11-09)

律(L125 短版):VCGC · VDF · VRN-2 · VQG · VAP 五個系統各有自己的 MAIN() SSOT,各自主導、互不干涉;
編號預設空著,衝突(衝突冊 OPEN · L122 治理器紅)由操作員與 AI 解了、VCGC 偵測無誤發號之後,那個號才有憲法性;
五系統之間唯一的關聯就是編號;各系統引擎能實跑一個就收一個、每次都記進度、互不影響完成度。VRN-1 在倉外只讀。

本支做什麼(唯讀五系統,只寫自己的輸出與進度帳):
  ① 入口:每系統 MAIN() 尾版(glob 取最高版號)· 行數 · sha8 · 在 VIA_NumberBooks 的號(沒有 = 空號)。
  ② SSOT:每系統自己的冊(尾版路徑 · 在不在)。
  ③ 編號:號冊列數 · L122 治理器(CGC_MDL270 RegistryGovernor 尾版)dry-run:表 / 功 紅黃綠 · 留白與原因;
     不在治理器 SUBS 的系統(VQG · VAP)誠實標「未登記 L122 冊」。
  ④ 衝突:RC-1 衝突冊尾版 OPEN 項,按系統名分開點名(VRN-1 / VRN-2 分開,不寫籠統 VRN)。
  ⑤ 憲法性:GREEN = 入口有號 · 治理器該系統紅 0 · 衝突 0 · 留白 0;YELLOW = 入口有號但留白 / 黃 / 未登記治理器;RED = 入口空號或衝突 / 紅。
  ⑥ 實測:五系統各自 --selftest(子程序 · 並行 · 各自逾時 · 一個紅不影響別人);rc 0 → GREEN,逾時 124 / 其他 → RED。
  ⑦ 進度帳:docs/handoff/ai/VIA_FiveSystem_Progress_v0100.jsonl 只增(每系統每輪一列);矩陣附每系統歷史次數 · 最近一次綠 · 連綠。
  ⑧ 輸出:VIA_FiveSystemConstitution_v0100.json / .md / VIA_FiveSystemConstitution_UI.html(Atlas --vl-* 鎖定色票)。
  Codex PR 619(併入前就地修,本檔尚未上 main):P1 治理器 dry-run 擬發的號不算有號(只認落冊)· P1 --no-run 入口 sha 變了不沿用舊綠 · P1 加速器橋 / 網路橋(graceful)。

用法:
  python3 docs/handoff/ai/VIA_FiveSystemConstitution_v0100.py run [--apply] [--no-run] [--timeout 900]
      --apply  才寫輸出與進度帳(沒有 --apply = 只印)· --no-run 不跑子程序自測(只讀上一列進度)
  python3 docs/handoff/ai/VIA_FiveSystemConstitution_v0100.py --selftest   (夾具樹 · 零網路 · 只在 tempfile 寫)
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更;本檔零網路,只掛路徑) =====
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
# ===== [VIA:NET-BRIDGE:END] =====

import concurrent.futures
import datetime
import glob
import hashlib
import html
import importlib.util
import io
import contextlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ENGINE = "VIA_FiveSystemConstitution_v0100"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]                      # …/VeritasIntelligenceAnalytics
OUT_JSON = HERE / "VIA_FiveSystemConstitution_v0100.json"
OUT_MD = HERE / "VIA_FiveSystemConstitution_v0100.md"
OUT_UI = HERE / "VIA_FiveSystemConstitution_UI.html"
LEDGER = HERE / "VIA_FiveSystem_Progress_v0100.jsonl"
LAW = "L125"

# 五系統(+ VRN-1 倉外只讀列)。sub = 號冊 / 治理器的子系統縮寫;tokens = 衝突冊點名時認的字(分開命名律 L123)。
SYSTEMS = [
    {"sys": "VCGC", "sub": "VCGC", "entry": "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py",
     "selftest": ["--selftest"], "timeout": 1500, "tokens": ["VCGC", "CGC_MDL"],
     "ssot": ["supportive modules/registry/VIA_Policy_Laws_SSOT_v*.json", "supportive modules/registry/VIA_Requirements_SSOT_v*.json",
              "supportive modules/registry/VIA_Workflow_VCGC_SSOT_v*.json", "supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v*.json",
              "supportive modules/registry/VIA_Numbering_SSOT_v*.json", "supportive modules/registry/VIA_Handoff_Continuity_SSOT_v*.json"]},
    {"sys": "VDF", "sub": "VDF", "entry": "functional modules/VDF/VDF_SystemManager_v*.py",
     "selftest": ["--selftest"], "timeout": 900, "tokens": ["VDF"],
     "ssot": ["functional modules/VDF/registry/VDF_SSOT_Register_v*.json", "functional modules/VDF/VDF_FetchSystem_SSOT_v*.json",
              "functional modules/VDF/VDF_InputUniverse_SSOT_v*.json", "functional modules/VDF/VDF_DataHome_SSOT_v*.json",
              "supportive modules/registry/VIA_Workflow_VDF_SSOT_v*.json"]},
    {"sys": "VRN-2", "sub": "VRN", "entry": "functional modules/VRN/VRN_SystemManager_v*.py",
     "selftest": ["--selftest"], "timeout": 900, "tokens": ["VRN-2", "VRN2", "VRN_SystemManager", "ActivateVRN-2"],
     "ssot": ["functional modules/VRN/SSOT/VRN2_SSOT_v*.json", "functional modules/VRN/registry/VRN_SSOT_Index_v*.json",
              "functional modules/VRN/SSOT/VRN_FinLexicon_SSOT_v*.json", "functional modules/VRN/VRN_FrameFlow_SSOT_v*.json"]},
    {"sys": "VQG", "sub": "VQG", "entry": "functional modules/VQG/VQG_AllInOne_v*.py",
     "selftest": ["selftest"], "timeout": 900, "tokens": ["VQG"],
     "ssot": []},   # VQG 的連線證據(vqg_connection_manifest.json)在匯出時才產生;倉內沒有常駐登記冊 → 誠實列 0
    {"sys": "VAP", "sub": "VAP", "entry": "functional modules/VAP/VAP_SystemManager_v*.py",
     "selftest": ["--selftest"], "timeout": 600, "tokens": ["VAP", "AutoPlot"],
     "ssot": ["functional modules/VAP/VAP_Subsystem_Manifest.json", "functional modules/VAP/VAP_Param_Registry_v*.json"]},
    {"sys": "VRN-1", "sub": None, "entry": None, "selftest": None, "timeout": 0, "tokens": ["VRN-1", "VIA-VDF-VRN"],
     "ssot": [], "external": "另一團隊的倉 tonykuni/VIA-VDF-VRN · 本倉只讀它自報的結果,不跑、不寫、不出版號(L123)"},
]
GOVERNOR_GLOB = "supportive modules/registry/CGC_MDL270_RegistryGovernor_v*.py"
NUMBERBOOK_GLOB = "supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_*.jsonl"
CONFLICT_GLOB = "docs/handoff/ai/VIA_RC1_ConflictRegistry_v*.json"
ALLOWED_WRITES = (OUT_JSON, OUT_MD, OUT_UI, LEDGER)


# ───────────────────────── 小工具 ─────────────────────────
def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def vnum(p) -> int:
    m = re.search(r"_v(\d{4})(?:\.\w+)?$", Path(p).name)
    return int(m.group(1)) if m else -1


def tail(root: Path, pattern: str):
    """glob 取尾版(版號最高;沒版號的檔名直接回它自己);沒有回 None。"""
    hits = [Path(x) for x in glob.glob(str(root / pattern))]
    hits = [h for h in hits if h.is_file()]
    if not hits:
        return None
    return max(hits, key=lambda h: (vnum(h), h.name))


def sha8(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:8]


def worst(*lamps) -> str:
    order = {"RED": 3, "YELLOW": 2, "GREEN": 1, "GRAY": 0}
    best = "GRAY"
    for l in lamps:
        l = str(l or "GRAY").upper()
        if l not in order:
            l = "YELLOW"
        if order[l] > order[best]:
            best = l
    return best


def read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


# ───────────────────────── ① 入口 · 號 ─────────────────────────
def load_numberbooks(root: Path) -> list:
    rows = []
    for f in glob.glob(str(root / NUMBERBOOK_GLOB)):
        try:
            for line in Path(f).read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        pass
        except Exception:
            pass
    return rows


def number_of(rows: list, entry: Path | None) -> str:
    """入口尾版在號冊的檔號(MDL / ENG):source 以檔名結尾,或 name == 檔名去副檔名。沒有回空字串(= 空號)。"""
    if entry is None:
        return ""
    name = entry.name
    stem = entry.stem
    for r in rows:
        if r.get("kind") not in (None, "MDL", "ENG"):
            continue
        src = str(r.get("source", "")).replace("\\", "/")
        if src.endswith("/" + name) or src == name or r.get("name") == stem:
            return str(r.get("code", ""))
    return ""


def rows_per_sub(rows: list) -> dict:
    out = {}
    for r in rows:
        s = r.get("sub")
        if s:
            out[s] = out.get(s, 0) + 1
    return out


# ───────────────────────── ③ 治理器(L122)dry-run ─────────────────────────
def governor_dry(root: Path) -> dict:
    """載入 CGC_MDL270 RegistryGovernor 尾版 · govern(apply=False)· 不寫號、不寫卡。載不到 / 炸了 → 誠實回 unavailable。"""
    gp = tail(root, GOVERNOR_GLOB)
    if gp is None:
        return {"available": False, "why": "找不到 RegistryGovernor 尾版", "subs": [], "per_sub": {}}
    try:
        spec = importlib.util.spec_from_file_location("via_registry_governor_tail", gp)
        mod = importlib.util.module_from_spec(spec)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            spec.loader.exec_module(mod)
            res = mod.govern(apply=False)
    except Exception as ex:                       # noqa: BLE001 —— 誠實回報,不冒充
        return {"available": False, "why": "%s: %s" % (type(ex).__name__, str(ex)[:160]), "engine": gp.name, "subs": [], "per_sub": {}}
    per = summarize_governor(res, getattr(mod, "SUBS", ()))
    return {"available": True, "engine": gp.name, "lamp": res.get("lamp"), "subs": list(per.keys()), "per_sub": per,
            "summary": res.get("summary", {}), "notes": res.get("_notes", [])}


def summarize_governor(res: dict, subs) -> dict:
    """govern(apply=False) 的結果 → 每系統 功 / 表 紅黃綠留白。
    留白 = 沒有號 **或** 號是本輪擬發、沒落冊(res.issued_fns / issued_tables 的鍵;dry-run 下治理器會把擬發的號放進 rec,但不寫
    VIA_RegistryNumbers / VIA_TableNumbers)。只有落冊的號才算有號(Codex PR 619 P1:矩陣不得替沒發過的號背書)。"""
    per = {}
    for s in subs:
        per[s] = {"fns": 0, "f_red": 0, "f_yellow": 0, "f_green": 0, "f_blank": 0, "blank_why": {},
                  "tables": 0, "t_red": 0, "t_yellow": 0, "t_green": 0, "t_blank": 0, "proposed_unissued": 0}
    proposed_f = {e.get("key") for e in res.get("issued_fns", [])}
    proposed_t = {e.get("key") for e in res.get("issued_tables", [])}
    for key, rec in res.get("fns", {}).items():
        s = rec.get("sub")
        if s not in per:
            continue
        P = per[s]
        P["fns"] += 1
        P["f_" + str(rec.get("lamp", "YELLOW")).lower()] += 1
        unissued = key in proposed_f
        if not rec.get("code") or unissued:
            P["f_blank"] += 1
            why = "PROPOSED_UNISSUED" if unissued else (rec.get("test") or "留白").split(":")[0]
            P["blank_why"][why] = P["blank_why"].get(why, 0) + 1
            if unissued:
                P["proposed_unissued"] += 1
    for key, rec in res.get("tables", {}).items():
        s = rec.get("sub")
        if s not in per:
            continue
        P = per[s]
        P["tables"] += 1
        P["t_" + str(rec.get("lamp", "YELLOW")).lower()] += 1
        if not rec.get("table_no") or key in proposed_t:
            P["t_blank"] += 1
            if key in proposed_t:
                P["proposed_unissued"] += 1
    return per


# ───────────────────────── ④ 衝突冊 ─────────────────────────
def open_conflicts(root: Path) -> list:
    cp = tail(root, CONFLICT_GLOB)
    d = read_json(cp) if cp else None
    if not d:
        return []
    out = []
    for e in d.get("entries", []):
        st = str(e.get("status", "")).upper()
        if st.startswith("OPEN"):
            txt = " ".join(str(e.get(k, "")) for k in ("what", "evidence", "impact", "resolution_proposal", "class"))
            out.append({"id": e.get("id"), "severity": e.get("severity"), "status": e.get("status"), "what": str(e.get("what", ""))[:160], "_txt": txt})
    return out


def conflicts_for(sysdef: dict, conflicts: list) -> list:
    """按系統名點名:VRN-2 認 VRN-2 / VRN2 / VRN_SystemManager / ActivateVRN-2;VRN-1 認 VRN-1 / VIA-VDF-VRN;籠統的「VRN」不算任何一家(分不出就不猜,L123 ②)。"""
    toks = sysdef["tokens"]
    hits = []
    for c in conflicts:
        t = c["_txt"]
        if any(tok in t for tok in toks):
            hits.append({k: c[k] for k in ("id", "severity", "status", "what")})
    return hits


# ───────────────────────── ⑥ 實測(各自子程序 · 並行) ─────────────────────────
def run_selftest(root: Path, entry: Path, args: list, timeout: int, env_extra: dict | None = None) -> dict:
    env = dict(os.environ)
    env.setdefault("VIA_FROM_VCGC", "YES")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.update(env_extra or {})
    cmd = [sys.executable, str(entry)] + list(args)
    t0 = time.time()
    try:
        cp = subprocess.run(cmd, cwd=str(root), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        rc, out = cp.returncode, (cp.stdout or "") + (cp.stderr or "")
    except subprocess.TimeoutExpired as ex:
        rc, out = 124, (ex.stdout.decode("utf-8", "replace") if isinstance(ex.stdout, bytes) else (ex.stdout or "")) + "\n[逾時 %ds]" % timeout
    except Exception as ex:                       # noqa: BLE001
        rc, out = 127, "%s: %s" % (type(ex).__name__, ex)
    lines = [l for l in out.splitlines() if l.strip()]
    lamp = "GREEN" if rc == 0 else "RED"
    return {"cmd": [Path(cmd[1]).name] + list(args), "rc": rc, "secs": round(time.time() - t0, 1), "lamp": lamp,
            "last": (lines[-1][:200] if lines else ""), "lines": len(lines)}


# ───────────────────────── ⑦ 進度帳(只增) ─────────────────────────
def ledger_rows(ledger: Path) -> list:
    rows = []
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows


def ledger_append(ledger: Path, rows: list) -> int:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(rows)


def progress_of(history: list, sysname: str) -> dict:
    mine = [r for r in history if r.get("sys") == sysname]
    greens = [r for r in mine if r.get("run_lamp") == "GREEN"]
    streak = 0
    for r in reversed(mine):
        if r.get("run_lamp") == "GREEN":
            streak += 1
        else:
            break
    return {"runs": len(mine), "greens": len(greens), "last_green": (greens[-1]["ts"] if greens else None),
            "streak": streak, "last": (mine[-1] if mine else None)}


# ───────────────────────── ⑤ 憲法性 ─────────────────────────
def constitution(number: str, gov_sub: dict | None, in_governor: bool, conflicts: list, external: bool) -> tuple:
    """→ (lamp, status, why)。GRAY 只給倉外系統。"""
    if external:
        return "GRAY", "EXTERNAL_READONLY", "倉外只讀 · 不在本倉號冊 · 不發號(L123)"
    if not number:
        return "RED", "BLANK_ENTRY", "入口尾版在 VIA_NumberBooks 沒有號(空號 = 還沒有憲法性)"
    if conflicts:
        return "RED", "CONFLICT_OPEN", "衝突冊 OPEN %d 項點到本系統 → 號不生效,先裁衝突" % len(conflicts)
    if not in_governor or gov_sub is None:
        return "YELLOW", "NOT_IN_L122_GOVERNOR", "入口有號,但本系統尚未登記 L122 表頭冊 / 功能矩陣(治理器 SUBS 外)→ 只有檔號,子項無號"
    if gov_sub["f_red"] or gov_sub["t_red"]:
        return "RED", "GOVERNOR_RED", "治理器紅:功 %d · 表 %d → 擋號" % (gov_sub["f_red"], gov_sub["t_red"])
    if gov_sub["f_blank"] or gov_sub["t_blank"]:
        return "YELLOW", "PARTIAL_BLANK", "入口有號、治理器紅 0;留白 功 %d · 表 %d(%s)" % (gov_sub["f_blank"], gov_sub["t_blank"], ", ".join("%s %d" % kv for kv in sorted(gov_sub["blank_why"].items())) or "—")
    if gov_sub["f_yellow"] or gov_sub["t_yellow"]:
        return "YELLOW", "CONSTITUTIONAL_WITH_NOTES", "全有號 · 紅 0;黃提醒 功 %d · 表 %d(不擋號)" % (gov_sub["f_yellow"], gov_sub["t_yellow"])
    return "GREEN", "CONSTITUTIONAL", "入口有號 · 治理器紅 0 黃 0 · 留白 0 · 衝突 0"


# ───────────────────────── 組裝 ─────────────────────────
def build(root: Path, systems: list | None = None, do_run: bool = True, governor: bool = True, ledger: Path | None = None,
          timeout_cap: int | None = None, run_fn=run_selftest) -> tuple:
    """→ (D, new_ledger_rows)。不寫任何檔(寫在 run())。"""
    systems = systems or SYSTEMS
    ledger = ledger or LEDGER
    ts = now_utc()
    run_id = ts.replace("-", "").replace(":", "")
    nb = load_numberbooks(root)
    per_sub_rows = rows_per_sub(nb)
    gov = governor_dry(root) if governor else {"available": False, "why": "governor=False(夾具)", "subs": [], "per_sub": {}}
    confl = open_conflicts(root)
    history = ledger_rows(ledger)

    # 先解析每系統(不跑)
    recs = []
    for sd in systems:
        external = bool(sd.get("external"))
        entry = tail(root, sd["entry"]) if sd.get("entry") else None
        rec = {"sys": sd["sys"], "sub": sd["sub"], "external": external,
               "entry": (str(entry.relative_to(root)).replace("\\", "/") if entry else None),
               "entry_version": ("v%04d" % vnum(entry) if entry is not None and vnum(entry) >= 0 else None),
               "entry_sha8": (sha8(entry) if entry else None), "entry_lines": (sum(1 for _ in entry.open(encoding="utf-8", errors="replace")) if entry else 0),
               "number": number_of(nb, entry), "numberbook_rows": per_sub_rows.get(sd["sub"], 0) if sd["sub"] else 0,
               "ssot": [], "conflicts": conflicts_for(sd, confl), "note": sd.get("external", "")}
        for pat in sd.get("ssot", []):
            t = tail(root, pat)
            rec["ssot"].append({"pattern": pat, "tail": (str(t.relative_to(root)).replace("\\", "/") if t else None), "present": t is not None})
        in_gov = bool(gov.get("available")) and sd["sub"] in gov.get("subs", [])
        gsub = gov["per_sub"].get(sd["sub"]) if in_gov else None
        rec["governor"] = gsub if gsub else {"in_governor": False}
        if gsub:
            rec["governor"]["in_governor"] = True
        lamp, status, why = constitution(rec["number"], gsub, in_gov, rec["conflicts"], external)
        rec["constitution"] = {"lamp": lamp, "status": status, "why": why}
        rec["_entry_path"] = entry
        rec["_timeout"] = min(sd.get("timeout") or 900, timeout_cap) if timeout_cap else (sd.get("timeout") or 900)
        rec["_selftest"] = sd.get("selftest")
        recs.append(rec)

    # 實測:各自子程序並行(一個紅不影響別人)
    if do_run:
        todo = [r for r in recs if not r["external"] and r["_entry_path"] is not None and r["_selftest"]]
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(todo))) as ex:
            futs = {ex.submit(run_fn, root, r["_entry_path"], r["_selftest"], r["_timeout"]): r for r in todo}
            for f, r in futs.items():
                try:
                    r["run"] = f.result()
                except Exception as e:            # noqa: BLE001
                    r["run"] = {"cmd": None, "rc": 127, "secs": 0, "lamp": "RED", "last": "%s: %s" % (type(e).__name__, e), "lines": 0}
    new_rows = []
    for r in recs:
        if r["external"]:
            r["run"] = {"cmd": None, "rc": None, "secs": 0, "lamp": "GRAY", "last": "倉外只讀 · 不跑", "lines": 0}
        elif r["_entry_path"] is None:
            r["run"] = {"cmd": None, "rc": None, "secs": 0, "lamp": "RED", "last": "入口尾版不存在", "lines": 0}
        elif "run" not in r:
            prog_prev = progress_of(history, r["sys"])
            last = prog_prev["last"] or {}
            same = bool(last) and last.get("entry_sha8") == r["entry_sha8"] and last.get("entry") == r["entry"]
            if same:
                r["run"] = {"cmd": None, "rc": last.get("run_rc"), "secs": 0, "lamp": (last.get("run_lamp") or "GRAY"), "last": "--no-run · 入口 sha %s 沒變 · 沿用上一列 %s" % (r["entry_sha8"], last.get("ts") or "(無)"), "lines": 0, "reused": True}
            else:
                r["run"] = {"cmd": None, "rc": None, "secs": 0, "lamp": "YELLOW", "last": "--no-run · 入口變了(舊 %s → 新 %s)· 未測,不沿用舊結果(AGENTS.md L11 相依變了要重測)" % (last.get("entry_sha8") or "無紀錄", r["entry_sha8"]), "lines": 0, "untested": True}
        if do_run and not r["external"] and r["_entry_path"] is not None:
            new_rows.append({"ts": ts, "run_id": run_id, "sys": r["sys"], "entry": r["entry"], "entry_version": r["entry_version"], "entry_sha8": r["entry_sha8"],
                             "number": r["number"], "constitution": r["constitution"]["status"], "constitution_lamp": r["constitution"]["lamp"],
                             "conflicts_open": len(r["conflicts"]), "run_rc": r["run"]["rc"], "run_secs": r["run"]["secs"], "run_lamp": r["run"]["lamp"], "engine": ENGINE})
    all_hist = history + new_rows
    for r in recs:
        r["progress"] = progress_of(all_hist, r["sys"])
        r["lamp"] = worst(r["constitution"]["lamp"], r["run"]["lamp"]) if not r["external"] else "GRAY"
        r.pop("_entry_path", None); r.pop("_timeout", None); r.pop("_selftest", None)

    inrepo = [r for r in recs if not r["external"]]
    counts = {"systems": len(inrepo), "run_green": sum(1 for r in inrepo if r["run"]["lamp"] == "GREEN"), "run_red": sum(1 for r in inrepo if r["run"]["lamp"] == "RED"),
              "constitutional": sum(1 for r in inrepo if r["constitution"]["status"].startswith("CONSTITUTIONAL")), "blank": sum(1 for r in inrepo if not r["number"]),
              "conflict_open_total": len(confl), "ledger_rows_before": len(history), "ledger_rows_added": len(new_rows)}
    lamp = worst(*[r["lamp"] for r in inrepo]) if inrepo else "GRAY"
    D = {"engine": ENGINE, "law": LAW, "generated_utc": ts, "run_id": run_id, "root": str(root), "lamp": lamp, "counts": counts,
         "rule": {"L125": "五系統各自 MAIN() SSOT 主導;編號預設空著;衝突解了 + VCGC 偵測無誤發號 → 號才有憲法性;唯一跨系統關聯 = 編號;引擎能實跑一個收一個、每次記進度、互不影響完成度;VRN-1 倉外只讀",
                  "lamps": "憲法性:GREEN 入口有號·治理器紅0黃0·留白0·衝突0 / YELLOW 有號但留白·黃·未登記治理器 / RED 空號·衝突 OPEN·治理器紅;實測:rc 0 GREEN · 逾時 124 / 其他 RED;總燈 = 各系統(憲法性 × 實測)取最差,VRN-1 GRAY 不算"},
         "governor": {k: v for k, v in gov.items() if k != "per_sub"}, "conflicts_open": [{k: c[k] for k in ("id", "severity", "status", "what")} for c in confl],
         "systems": recs, "ledger": str(ledger.relative_to(root)).replace("\\", "/") if str(ledger).startswith(str(root)) else str(ledger),
         "writes": [str(p.relative_to(root)).replace("\\", "/") for p in ALLOWED_WRITES if str(p).startswith(str(root))],
         "not_in_scope": ["不發號、不寫任何系統的冊 / 正本 / 號冊(發號只經 VCGC run CGC_MDL237 --apply --scope · L122 治理器 --apply,都要操作員授權)",
                          "不裁衝突:衝突冊 OPEN 項只點名歸屬,解法由操作員 + AI 裁定書(L122 ④)",
                          "VRN-1 倉外:不 clone、不跑、不評分(L123)"]}
    return D, new_rows


# ───────────────────────── 輸出 ─────────────────────────
def to_md(D: dict) -> str:
    L = ["# 五系統編號憲法矩陣(%s · %s)" % (LAW, D["generated_utc"]), "",
         "> %s" % D["rule"]["L125"], "", "總燈 **%s** · 實測綠 %d/%d · 憲法性 %d/%d · 空號 %d · 衝突冊 OPEN %d · 進度帳 +%d(累計 %d)" % (
             D["lamp"], D["counts"]["run_green"], D["counts"]["systems"], D["counts"]["constitutional"], D["counts"]["systems"], D["counts"]["blank"],
             D["counts"]["conflict_open_total"], D["counts"]["ledger_rows_added"], D["counts"]["ledger_rows_before"] + D["counts"]["ledger_rows_added"]), "",
         "| 系統 | 入口 MAIN() 尾版 | 號 | 憲法性 | 治理器(功 紅/黃/綠/留白 · 表 紅/黃/綠/留白) | 衝突 OPEN | 實測 | 進度(跑/綠/連綠) |", "|---|---|---|---|---|---|---|---|"]
    for r in D["systems"]:
        g = r["governor"]
        gtxt = ("%d/%d/%d/%d · %d/%d/%d/%d" % (g["f_red"], g["f_yellow"], g["f_green"], g["f_blank"], g["t_red"], g["t_yellow"], g["t_green"], g["t_blank"])) if g.get("in_governor") else "未登記 L122 冊"
        run = r["run"]
        L.append("| %s | `%s` %s | %s | %s %s | %s | %s | %s rc %s · %ss | %d/%d/%d |" % (
            r["sys"], r["entry"] or "—", r["entry_version"] or "", r["number"] or "**空號**", r["constitution"]["lamp"], r["constitution"]["status"], gtxt,
            ", ".join(c["id"] for c in r["conflicts"]) or "0", run["lamp"], run["rc"], run["secs"], r["progress"]["runs"], r["progress"]["greens"], r["progress"]["streak"]))
    L += ["", "## 每系統", ""]
    for r in D["systems"]:
        L.append("### %s · %s" % (r["sys"], r["lamp"]))
        L.append("- 憲法性:%s —— %s" % (r["constitution"]["status"], r["constitution"]["why"]))
        L.append("- 入口:`%s`(%s 行 · sha8 %s)· 號冊列(本子系統)%d" % (r["entry"], r["entry_lines"], r["entry_sha8"], r["numberbook_rows"]))
        L.append("- SSOT 冊:" + ("; ".join("`%s`" % (s["tail"] or s["pattern"] + " ✘") for s in r["ssot"]) if r["ssot"] else "(倉內無常駐登記冊)"))
        if r["conflicts"]:
            L.append("- 衝突 OPEN:" + "; ".join("%s(%s)%s" % (c["id"], c["severity"], c["what"][:60]) for c in r["conflicts"]))
        L.append("- 實測:%s · rc %s · %ss · `%s`" % (r["run"]["lamp"], r["run"]["rc"], r["run"]["secs"], r["run"]["last"][:120]))
        if r.get("note"):
            L.append("- 註:%s" % r["note"])
        L.append("")
    L += ["## 治理器(L122 · dry-run 不寫號)", "", "- %s" % ("%s · 總燈 %s · SUBS %s" % (D["governor"].get("engine"), D["governor"].get("lamp"), ", ".join(D["governor"].get("subs", []))) if D["governor"].get("available") else "不可用:%s" % D["governor"].get("why")), ""]
    L += ["## 衝突冊 OPEN(全部)", ""] + ["- %s · %s · %s" % (c["id"], c["severity"], c["what"]) for c in D["conflicts_open"]] + ["", "## 不在範圍", ""] + ["- %s" % x for x in D["not_in_scope"]]
    return "\n".join(L) + "\n"


def to_ui(D: dict) -> str:
    e = html.escape

    def lc(x):
        x = str(x).upper()
        return "g" if x.startswith("GREEN") else "y" if x.startswith("YELLOW") else "r" if x.startswith("RED") else "k"
    chips = "".join(f"<div class='chip'><b><span class='lamp {lc(r['lamp'])}'>{e(r['lamp'])}</span> {e(r['sys'])}</b><span>{e(r['constitution']['status'])} · 實測 {e(r['run']['lamp'])} · 號 {e(r['number'] or '空號')}</span></div>" for r in D["systems"])
    rows = []
    for r in D["systems"]:
        g = r["governor"]
        gtxt = (f"功 {g['f_red']}/{g['f_yellow']}/{g['f_green']}/{g['f_blank']} · 表 {g['t_red']}/{g['t_yellow']}/{g['t_green']}/{g['t_blank']}") if g.get("in_governor") else "未登記 L122 冊"
        rows.append(f"<tr><td><b>{e(r['sys'])}</b></td><td><code>{e(r['entry'] or '—')}</code><div class='note'>{e(r['entry_version'] or '')} · {r['entry_lines']} 行 · {e(r['entry_sha8'] or '')}</div></td>"
                    f"<td>{('<code>' + e(r['number']) + '</code>') if r['number'] else '<span class=\"lamp r\">空號</span>'}</td>"
                    f"<td><span class='lamp {lc(r['constitution']['lamp'])}'>{e(r['constitution']['status'])}</span><div class='note'>{e(r['constitution']['why'])}</div></td>"
                    f"<td>{e(gtxt)}</td><td>{e(', '.join(c['id'] for c in r['conflicts']) or '0')}</td>"
                    f"<td><span class='lamp {lc(r['run']['lamp'])}'>{e(r['run']['lamp'])}</span> rc {e(str(r['run']['rc']))} · {r['run']['secs']}s<div class='note'>{e(str(r['run']['last'])[:100])}</div></td>"
                    f"<td>{r['progress']['runs']} / {r['progress']['greens']} / 連 {r['progress']['streak']}<div class='note'>{e(r['progress']['last_green'] or '—')}</div></td></tr>")
    ssot = "".join(f"<h3>{e(r['sys'])}</h3><ul>" + ("".join(f"<li><code>{e(s['tail'] or s['pattern'])}</code>{'' if s['present'] else ' ✘ 不在'}</li>" for s in r["ssot"]) or "<li class='note'>倉內無常駐登記冊</li>") + "</ul>" for r in D["systems"] if not r["external"])
    confl = "".join(f"<li><b>{e(c['id'])}</b> · {e(c['severity'])} · {e(c['what'])}</li>" for c in D["conflicts_open"]) or "<li>0</li>"
    nis = "".join(f"<li>{e(x)}</li>" for x in D["not_in_scope"])
    gov = D["governor"]
    govtxt = (f"{e(gov.get('engine'))} · dry-run · 總燈 <span class='lamp {lc(gov.get('lamp'))}'>{e(str(gov.get('lamp')))}</span> · SUBS {e(', '.join(gov.get('subs', [])))}") if gov.get("available") else f"不可用:{e(gov.get('why'))}"
    c = D["counts"]
    return f"""<title>五系統編號憲法矩陣</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root{{--vl-bg:#f7f8fa;--vl-white:#fff;--vl-ink:#15181d;--vl-muted:#5b6472;--vl-border:#d8dde5;--vl-border-soft:#eceff4;--vl-row:#fafbfd;
--vl-success-bg:#e8f6ee;--vl-success-ink:#0f5c37;--vl-warning-bg:#fdf4e3;--vl-warning-ink:#7a5410;--vl-danger-bg:#fdecec;--vl-danger-ink:#8d1f1f;--vl-gray-bg:#eef0f3;--vl-gray-ink:#4a5260;
--vl-font-cjk:"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;--vl-font-mono:ui-monospace,SFMono-Regular,Menlo,monospace;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--vl-bg:#111419;--vl-white:#181c22;--vl-ink:#e7ebf1;--vl-muted:#9aa5b4;--vl-border:#2b313a;--vl-border-soft:#22272e;--vl-row:#1d2128;
--vl-success-bg:#12301f;--vl-success-ink:#7fd6a4;--vl-warning-bg:#33270f;--vl-warning-ink:#f0c674;--vl-danger-bg:#3a1717;--vl-danger-ink:#f29c9c;--vl-gray-bg:#232830;--vl-gray-ink:#aab3c0;color-scheme:dark}}}}
:root[data-theme="dark"]{{--vl-bg:#111419;--vl-white:#181c22;--vl-ink:#e7ebf1;--vl-muted:#9aa5b4;--vl-border:#2b313a;--vl-border-soft:#22272e;--vl-row:#1d2128;
--vl-success-bg:#12301f;--vl-success-ink:#7fd6a4;--vl-warning-bg:#33270f;--vl-warning-ink:#f0c674;--vl-danger-bg:#3a1717;--vl-danger-ink:#f29c9c;--vl-gray-bg:#232830;--vl-gray-ink:#aab3c0;color-scheme:dark}}
body{{background:var(--vl-bg);color:var(--vl-ink);font-family:var(--vl-font-cjk);font-size:13px;line-height:1.55;margin:0}}
.wrap{{padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:24px;max-width:1180px;margin:0 auto}}
h1{{font-size:20px;margin:0 0 4px;text-wrap:balance}} h2{{font-size:15px;margin:22px 0 8px;border-bottom:1px solid var(--vl-border);padding-bottom:4px}} h3{{font-size:13px;margin:12px 0 4px}}
.sub{{color:var(--vl-muted);font-size:11px;margin-bottom:14px}} .law{{background:var(--vl-white);border:1px solid var(--vl-border);border-left:4px solid var(--vl-gray-ink);border-radius:8px;padding:10px 14px;margin:10px 0}}
.hdr{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:8px;margin:10px 0 18px}}
.chip{{background:var(--vl-white);border:1px solid var(--vl-border);border-radius:8px;padding:8px 12px;min-width:0}} .chip b{{display:block;font-size:14px;margin-bottom:4px}} .chip span{{color:var(--vl-muted);font-size:11px}}
.scroll{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:12px}} th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--vl-border-soft);vertical-align:top;min-width:0}} th{{color:var(--vl-muted);font-weight:600;font-size:11px;letter-spacing:.03em;text-transform:uppercase}} tr:nth-child(even) td{{background:var(--vl-row)}}
.lamp{{display:inline-block;padding:2px 8px;border-radius:6px;font-family:var(--vl-font-mono);font-size:11px;white-space:nowrap}}
.lamp.g{{background:var(--vl-success-bg);color:var(--vl-success-ink)}} .lamp.y{{background:var(--vl-warning-bg);color:var(--vl-warning-ink)}} .lamp.r{{background:var(--vl-danger-bg);color:var(--vl-danger-ink)}} .lamp.k{{background:var(--vl-gray-bg);color:var(--vl-gray-ink)}}
code{{font-family:var(--vl-font-mono);font-size:11px;background:var(--vl-gray-bg);padding:1px 4px;border-radius:4px;word-break:break-all}}
ul li{{margin-bottom:4px}} .note{{color:var(--vl-muted);font-size:11px}}
</style>
<div class="wrap">
<h1>五系統編號憲法矩陣 <span class="lamp {lc(D['lamp'])}">{e(D['lamp'])}</span></h1>
<div class="sub">{e(D['engine'])} · {e(D['generated_utc'])} · 政策 {e(LAW)} · 唯讀五系統 · 只寫自己的輸出與進度帳</div>
<div class="law"><b>{e(LAW)}</b> {e(D['rule']['L125'])}<div class="note">{e(D['rule']['lamps'])}</div></div>
<div class="hdr">{chips}</div>
<p>實測綠 <b>{c['run_green']}/{c['systems']}</b> · 憲法性 <b>{c['constitutional']}/{c['systems']}</b> · 空號 {c['blank']} · 衝突冊 OPEN {c['conflict_open_total']} · 進度帳 +{c['ledger_rows_added']}(累計 {c['ledger_rows_before'] + c['ledger_rows_added']})</p>
<h2>矩陣</h2><div class="scroll"><table><thead><tr><th>系統</th><th>入口 MAIN() 尾版</th><th>號</th><th>憲法性</th><th>L122 治理器 紅/黃/綠/留白</th><th>衝突 OPEN</th><th>實測(各自子程序)</th><th>進度 跑/綠/連綠</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>各系統自己的 SSOT 冊(正本歸各自系統 · 本支只讀)</h2>{ssot}
<h2>L122 治理器</h2><p>{govtxt}</p>
<h2>衝突冊 OPEN</h2><ul>{confl}</ul>
<h2>不在範圍</h2><ul>{nis}</ul>
<p class="note">進度帳 <code>{e(D['ledger'])}</code> 只增;每系統每輪一列,一個系統紅不擋其他系統收尾。</p>
</div>
"""


def run(apply: bool, do_run: bool = True, timeout_cap: int | None = None) -> int:
    D, new_rows = build(ROOT, do_run=do_run, timeout_cap=timeout_cap)
    c = D["counts"]
    print("[%s] 總燈 %s · 實測綠 %d/%d · 憲法性 %d/%d · 空號 %d · 衝突 OPEN %d · 進度帳 +%d" % (ENGINE, D["lamp"], c["run_green"], c["systems"], c["constitutional"], c["systems"], c["blank"], c["conflict_open_total"], len(new_rows) if apply else 0))
    for r in D["systems"]:
        print("  [%-6s] %-5s 號 %-22s 憲法性 %-26s 實測 %-5s rc %-4s %5ss · 衝突 %d · 進度 %d/%d 連 %d" % (
            r["lamp"], r["sys"], r["number"] or "空號", r["constitution"]["status"], r["run"]["lamp"], r["run"]["rc"], r["run"]["secs"], len(r["conflicts"]), r["progress"]["runs"], r["progress"]["greens"], r["progress"]["streak"]))
    if apply:
        OUT_JSON.write_text(json.dumps(D, ensure_ascii=False, indent=1), encoding="utf-8")
        OUT_MD.write_text(to_md(D), encoding="utf-8")
        OUT_UI.write_text(to_ui(D), encoding="utf-8")
        n = ledger_append(LEDGER, new_rows)
        print("  [寫] %s · %s · %s · 進度帳 +%d → %s" % (OUT_JSON.name, OUT_MD.name, OUT_UI.name, n, LEDGER.name))
    else:
        print("  [dry] 沒有 --apply:不寫輸出、不記進度")
    return 0 if D["lamp"] in ("GREEN", "YELLOW") else 1


# ───────────────────────── 自測(夾具樹 · 零網路 · 只在 tempfile 寫) ─────────────────────────
def _fixture(td: Path, vqg_rc: int = 0) -> tuple:
    root = td / "VIA"
    (root / "supportive modules/registry/VIA_NumberBooks").mkdir(parents=True)
    (root / "docs/handoff/ai").mkdir(parents=True)
    for sub, rel, body in [
        ("VCGC", "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0002.py", "import sys; print('[計] VCGC 自測 1/1 · PASS'); sys.exit(0)\n"),
        ("VDF", "functional modules/VDF/VDF_SystemManager_v0010.py", "import sys; print('VDF ok'); sys.exit(0)\n"),
        ("VRN", "functional modules/VRN/VRN_SystemManager_v0020.py", "import sys; print('VRN-2 ok'); sys.exit(0)\n"),
        ("VQG", "functional modules/VQG/VQG_AllInOne_v0003.py", "import sys; print('VQG %s'); sys.exit(%d)\n" % ("fail" if vqg_rc else "ok", vqg_rc)),
        ("VAP", "functional modules/VAP/VAP_SystemManager_v0001.py", "import sys; print('VAP ok'); sys.exit(0)\n"),
    ]:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    # 舊版也放一支,確認取尾版
    (root / "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0001.py").write_text("import sys; sys.exit(9)\n", encoding="utf-8")
    # 號冊:VCGC · VDF · VRN 入口有號;VQG · VAP 空號
    rows = [{"code": "VIA-VCGC-MDL001", "sub": "VCGC", "kind": "MDL", "name": "CGC_MDL149_VeritasCentralGovernanceConsole_v0002", "source": "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0002.py"},
            {"code": "VIA-VDF-MDL001", "sub": "VDF", "kind": "MDL", "name": "VDF_SystemManager_v0010", "source": "functional modules/VDF/VDF_SystemManager_v0010.py"},
            {"code": "VIA-VRN-MDL001", "sub": "VRN", "kind": "MDL", "name": "VRN_SystemManager_v0020", "source": "functional modules/VRN/VRN_SystemManager_v0020.py"},
            {"code": "VIA-VRN-FNC001", "sub": "VRN", "kind": "FNC", "name": "x", "source": "functional modules/VRN/VRN_SystemManager_v0020.py"}]
    (root / "supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_MDL_v0100.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    # 衝突冊:一項點名 VRN-2,一項只寫籠統 VRN(不算任何一家),一項 FIXED
    (root / "docs/handoff/ai/VIA_RC1_ConflictRegistry_v0100.json").write_text(json.dumps({"entries": [
        {"id": "CONFLICT-00001", "severity": "MEDIUM", "status": "OPEN", "what": "VRN-2 啟動器版本落差", "evidence": "", "impact": "", "resolution_proposal": "", "class": ""},
        {"id": "CONFLICT-00002", "severity": "LOW", "status": "OPEN", "what": "VRN 籠統字樣", "evidence": "", "impact": "", "resolution_proposal": "", "class": ""},
        {"id": "CONFLICT-00003", "severity": "HIGH", "status": "FIXED", "what": "VDF 已修", "evidence": "", "impact": "", "resolution_proposal": "", "class": ""}]}, ensure_ascii=False), encoding="utf-8")
    # VDF SSOT 冊一本(尾版判定)
    (root / "functional modules/VDF/registry").mkdir(parents=True, exist_ok=True)
    (root / "functional modules/VDF/registry/VDF_SSOT_Register_v0001.json").write_text("{}", encoding="utf-8")
    (root / "functional modules/VDF/registry/VDF_SSOT_Register_v0002.json").write_text("{}", encoding="utf-8")
    ledger = td / "ledger.jsonl"
    return root, ledger


def _tree_sha(root: Path, skip: Path) -> dict:
    out = {}
    for p in root.rglob("*"):
        if p.is_file() and p != skip:
            out[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, why=""):
        (ok if cond else bad).append(name + (("" if cond else " · " + why)))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, "" if cond else " · " + why), flush=True)

    with tempfile.TemporaryDirectory() as tdn:
        td = Path(tdn)
        root, ledger = _fixture(td)
        before = _tree_sha(root, skip=Path("/nonexistent"))
        D, rows = build(root, do_run=True, governor=False, ledger=ledger, timeout_cap=60)
        by = {r["sys"]: r for r in D["systems"]}
        chk("① 入口取尾版(v0002 不是 v0001)", by["VCGC"]["entry"].endswith("_v0002.py") and by["VCGC"]["entry_version"] == "v0002", str(by["VCGC"]["entry"]))
        chk("② 號:VCGC/VDF/VRN-2 有號 · VQG/VAP 空號(MDL 列才算,FNC 列不算)", by["VCGC"]["number"] == "VIA-VCGC-MDL001" and by["VRN-2"]["number"] == "VIA-VRN-MDL001" and by["VQG"]["number"] == "" and by["VAP"]["number"] == "", json.dumps({k: v["number"] for k, v in by.items()}))
        chk("③ 衝突分開命名:VRN-2 點到 00001;籠統「VRN」不算任何一家;FIXED 不算;VRN-1 0", [c["id"] for c in by["VRN-2"]["conflicts"]] == ["CONFLICT-00001"] and by["VRN-1"]["conflicts"] == [] and by["VDF"]["conflicts"] == [] and len(D["conflicts_open"]) == 2, json.dumps({k: [c["id"] for c in v["conflicts"]] for k, v in by.items()}))
        chk("④ 憲法性燈:VRN-2 RED(衝突)· VQG/VAP RED(空號)· VCGC/VDF YELLOW(有號但治理器不可用)· VRN-1 GRAY", by["VRN-2"]["constitution"]["status"] == "CONFLICT_OPEN" and by["VQG"]["constitution"]["status"] == "BLANK_ENTRY" and by["VCGC"]["constitution"]["status"] == "NOT_IN_L122_GOVERNOR" and by["VRN-1"]["constitution"]["lamp"] == "GRAY", json.dumps({k: v["constitution"]["status"] for k, v in by.items()}))
        chk("⑤ 實測各自子程序:五系統 rc 0 GREEN · VRN-1 GRAY 不跑", all(by[s]["run"]["lamp"] == "GREEN" and by[s]["run"]["rc"] == 0 for s in ("VCGC", "VDF", "VRN-2", "VQG", "VAP")) and by["VRN-1"]["run"]["lamp"] == "GRAY", json.dumps({k: v["run"]["lamp"] for k, v in by.items()}))
        chk("⑥ 進度列 = 5(倉外不記)· 欄位齊", len(rows) == 5 and all(set(("ts", "run_id", "sys", "entry", "number", "constitution", "run_rc", "run_lamp")) <= set(r) for r in rows), str(len(rows)))
        chk("⑦ build 不寫任何檔(夾具樹 sha 全同)", _tree_sha(root, skip=Path("/nonexistent")) == before)
        # 只增進度帳:第一輪寫入 → 第二輪(VQG 改紅)再寫 → 前五列原封不動、VQG 紅不影響別人、進度統計正確
        ledger_append(ledger, rows)
        first = ledger.read_text(encoding="utf-8")
        (root / "functional modules/VQG/VQG_AllInOne_v0003.py").write_text("import sys; print('VQG fail'); sys.exit(2)\n", encoding="utf-8")
        D2, rows2 = build(root, do_run=True, governor=False, ledger=ledger, timeout_cap=60)
        ledger_append(ledger, rows2)
        second = ledger.read_text(encoding="utf-8")
        by2 = {r["sys"]: r for r in D2["systems"]}
        chk("⑧ 進度帳只增:第二輪後前 5 列原封不動 · 共 10 列", second.startswith(first) and len([l for l in second.splitlines() if l.strip()]) == 10)
        chk("⑨ 一個系統紅不影響別人:VQG RED rc 2 · 其他四個仍 GREEN · 總燈 RED", by2["VQG"]["run"]["lamp"] == "RED" and by2["VQG"]["run"]["rc"] == 2 and all(by2[s]["run"]["lamp"] == "GREEN" for s in ("VCGC", "VDF", "VRN-2", "VAP")) and D2["lamp"] == "RED")
        chk("⑩ 進度統計:VQG 跑 2 綠 1 連綠 0 · VDF 跑 2 綠 2 連綠 2", by2["VQG"]["progress"]["runs"] == 2 and by2["VQG"]["progress"]["greens"] == 1 and by2["VQG"]["progress"]["streak"] == 0 and by2["VDF"]["progress"]["streak"] == 2, json.dumps({k: v["progress"] for k, v in by2.items() if k in ("VQG", "VDF")}, default=str)[:300])
        D3, rows3 = build(root, do_run=False, governor=False, ledger=ledger)
        by3 = {r["sys"]: r for r in D3["systems"]}
        chk("⑪ --no-run 沿用上一列進度(VQG RED · 不新增列)", by3["VQG"]["run"]["lamp"] == "RED" and by3["VQG"]["run"].get("reused") and rows3 == [])
        (root / "functional modules/VDF/VDF_SystemManager_v0010.py").write_text("import sys; sys.exit(9)\n", encoding="utf-8")
        D3b, _ = build(root, do_run=False, governor=False, ledger=ledger)
        by3b = {r["sys"]: r for r in D3b["systems"]}
        chk("⑪b --no-run 入口 sha 變了 → 不沿用舊綠:VDF YELLOW untested · VQG 仍沿用", by3b["VDF"]["run"]["lamp"] == "YELLOW" and by3b["VDF"]["run"].get("untested") and not by3b["VDF"]["run"].get("reused") and by3b["VQG"]["run"].get("reused"), json.dumps(by3b["VDF"]["run"], ensure_ascii=False)[:200])
        (root / "functional modules/VDF/VDF_SystemManager_v0010.py").write_text("import sys; print('VDF ok'); sys.exit(0)\n", encoding="utf-8")
        chk("⑫ SSOT 冊取尾版(VDF_SSOT_Register v0002)· 不在的標 ✘", any(s["tail"] and s["tail"].endswith("VDF_SSOT_Register_v0002.json") for s in by["VDF"]["ssot"]) and any(not s["present"] for s in by["VDF"]["ssot"]))
        # 逾時 → rc 124 RED
        (root / "functional modules/VAP/VAP_SystemManager_v0001.py").write_text("import time; time.sleep(5)\n", encoding="utf-8")
        D4, _ = build(root, systems=[s for s in SYSTEMS if s["sys"] == "VAP"], do_run=True, governor=False, ledger=ledger, timeout_cap=1)
        chk("⑬ 逾時 → rc 124 RED(不冒充綠)", D4["systems"][0]["run"]["rc"] == 124 and D4["systems"][0]["run"]["lamp"] == "RED", str(D4["systems"][0]["run"]))
        md, ui = to_md(D2), to_ui(D2)
        chk("⑭ 輸出:md 有矩陣表 · UI 用 --vl-* 色票 · 無 <html>/<body> 骨架 · 有雙主題", "| 系統 |" in md and "--vl-success-bg" in ui and "<html" not in ui and "<body" not in ui and 'data-theme="dark"' in ui and "prefers-color-scheme" in ui)
        chk("⑮ 分開命名:輸出寫 VRN-2 / VRN-1,不出現籠統「| VRN |」列", "| VRN-2 |" in md and "| VRN-1 |" in md and "| VRN |" not in md)
    fake = {"fns": {"VDF|a|v1": {"sub": "VDF", "lamp": "GREEN", "code": "VIA-VDF-MDL900", "test": "PASS"},      # dry-run 擬發(在 issued_fns)→ 留白
                    "VDF|b|v1": {"sub": "VDF", "lamp": "GREEN", "code": "VIA-VDF-MDL001", "test": None},        # 落冊的號 → 有號
                    "VDF|c|v1": {"sub": "VDF", "lamp": "YELLOW", "code": "", "test": "WAIT:父檔未有號"},
                    "VRN|d|v1": {"sub": "VRN", "lamp": "RED", "code": "", "test": "FAIL:x"}},
            "tables": {"VDF|t1|h": {"sub": "VDF", "lamp": "GREEN", "table_no": "SSOT-VCGC-VDF-TBL0009"}},
            "issued_fns": [{"key": "VDF|a|v1", "code": "VIA-VDF-MDL900"}], "issued_tables": [{"key": "VDF|t1|h", "table_no": "SSOT-VCGC-VDF-TBL0009"}]}
    g = summarize_governor(fake, ("VDF", "VRN"))
    chk("⑯b 治理器 dry-run 擬發的號不算有號:VDF 功留白 2(擬發 1 + WAIT 1)· 表留白 1(擬發)· VRN 紅 1 留白 1",
        g["VDF"]["f_blank"] == 2 and g["VDF"]["blank_why"].get("PROPOSED_UNISSUED") == 1 and g["VDF"]["blank_why"].get("WAIT") == 1 and g["VDF"]["t_blank"] == 1 and g["VDF"]["proposed_unissued"] == 2 and g["VRN"]["f_red"] == 1 and g["VRN"]["f_blank"] == 1, json.dumps(g, ensure_ascii=False)[:300])
    lamp_c, st_c, _ = constitution("VIA-VDF-MDL001", g["VDF"], True, [], False)
    chk("⑯c 擬發未落冊 → 憲法性只到 YELLOW PARTIAL_BLANK,不給 GREEN", lamp_c == "YELLOW" and st_c == "PARTIAL_BLANK", st_c)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑯ 紀律:加速器橋 · 網路橋在(from __future__ 之後)· 零網路 · 不 pip · 不設 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT · 只寫 ALLOWED_WRITES + 進度帳",
        "[VIA:ACCEL-BRIDGE:v0100]" in body and "[VIA:NET-BRIDGE:v0100]" in body and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:v0100]")
        and "VIA_NET_" + "CONSENT" not in body and "VIA_SCRAPE_" + "CONSENT" not in body and "pip install" not in body and "urllib" not in body and "requests" not in body.replace("subprocess", ""))
    # 實樹:五系統入口都解析得到(不跑子程序)
    real_ok = True
    detail = []
    for sd in SYSTEMS:
        if sd.get("entry"):
            t = tail(ROOT, sd["entry"])
            real_ok &= t is not None
            detail.append("%s=%s" % (sd["sys"], t.name if t else None))
    chk("⑰ 實樹:五系統 MAIN() 尾版都在(%s)" % " · ".join(detail), real_ok)
    n = len(ok) + len(bad)
    print("[%s] 自測 %d/%d · FAIL %d · %s" % (ENGINE, len(ok), n, len(bad), "PASS" if not bad else "FAIL: " + " / ".join(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a[:2]:
        return selftest()
    if a[:1] == ["run"]:
        cap = None
        if "--timeout" in a:
            try:
                cap = int(a[a.index("--timeout") + 1])
            except Exception:
                cap = None
        return run(apply=("--apply" in a), do_run=("--no-run" not in a), timeout_cap=cap)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
