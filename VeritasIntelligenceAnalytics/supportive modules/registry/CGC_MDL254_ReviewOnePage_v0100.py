#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL254_ReviewOnePage v0100 — 檢視整合為一頁:各工具最新結果一頁看完 · 燈號口徑統一 · 去重 · 衝突照列 · 細節不漏

操作員(2026-10-02):「檢視指令太多頁有重複有衝突 應該整合為一頁 各細節不漏 統一」;裁定由 via-review(總檢)產出這一頁。
本支只讀各工具自己的 *_latest.json(不重跑、不改、不刪舊頁;只增不減),來源清單的正本是 VIA_ReviewOnePage_Sources_SSOT 尾版:
  ① 燈號口徑統一:GREEN / YELLOW / RED / NODATA / INFO(冊上 lamp_map)+ 過期(超過 stale 小時)= 不冒充現況,算黃並給重跑指令
  ② 每個來源一列:正主 · 原燈 → 統一燈 · 時間 · 幾小時前 · 量的是哪個提交 · 摘要 · 重跑指令;非綠明細逐條(每來源上限 40,其餘看原檔)
  ③ 衝突區:同一件事兩個來源說法不一(冊上 conflict_rules C1–C5)→ 照列兩邊 + 正主 + 實際原因
  ④ 下一步只一份:git 同步 → 紅的重跑 → 各來源自己的下一步 → 過期的重跑(逐字去重)
  ⑤ 冊外的 *_latest.json 一律列「未登錄來源」(細節不漏);via-review 的步驟燈(--steps)併進同一頁
用法(只收 VCGC):
  via-vcgc run CGC_MDL254_ReviewOnePage build [--review <via-review 本輪 json>] [--no-open] [--json]
  (via-review v0106 起跑完自己呼叫;單獨跑 = 只併各工具最新結果,不含總檢本輪)
  python CGC_MDL254_ReviewOnePage_v0100.py --selftest
輸出:VIA_Reports/review/ONEPAGE_latest.html(唯一頁)· .json · .md(貼回包)。零網路;不用 TA-Lib;不代設同意閘。
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

import glob
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENGINE = Path(__file__).stem
OUT = VIA / "VIA_Reports" / "review"
ORDER = {"RED": 5, "YELLOW": 4, "STALE": 3, "NODATA": 2, "INFO": 1, "GREEN": 0}
SHOW = {"GREEN": "GREEN", "YELLOW": "YELLOW", "RED": "RED", "NODATA": "NODATA", "INFO": "NA", "STALE": "YELLOW"}
ZH = {"GREEN": "綠", "YELLOW": "黃", "RED": "紅", "NODATA": "無資料", "INFO": "資訊", "STALE": "過期"}
LAMP_KEYS = ("lamp", "state", "verdict", "status")
TEXT_KEYS = ("id", "probe", "rule", "step", "name", "item", "key", "family", "layer", "group", "topic", "title")
NOTE_KEYS = ("note", "msg", "detail", "why", "text", "last", "fix", "next")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _newest(pattern: str) -> Path | None:
    hits = [p for p in HERE.glob(pattern) if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def book() -> dict:
    p = _newest("VIA_ReviewOnePage_Sources_SSOT_v*.json")
    if p is None:
        raise RuntimeError("VIA_ReviewOnePage_Sources_SSOT 不在(先 git pull)")
    b = json.loads(p.read_text(encoding="utf-8"))
    b["_file"] = p.name
    return b


# ---------------------------------------------------------------- ① 燈號口徑統一
def norm_lamp(v, lamp_map: dict) -> str:
    if isinstance(v, bool):
        return "GREEN" if v else "RED"
    if isinstance(v, int):                               # rc:0 綠 · 2 黃 · 其他紅(VCGC 慣例)
        return {0: "GREEN", 2: "YELLOW"}.get(v, "RED")
    s = str(v or "").strip().upper()
    for k, words in lamp_map.items():
        if s in words:
            return k
    return "NODATA" if not s else "INFO"


def worst(lamps) -> str:
    lamps = list(lamps)
    return max(lamps, key=lambda x: ORDER.get(x, 0)) if lamps else "NODATA"


def dig(d, path: str):
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def parse_time(v) -> datetime | None:
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(float(v), tz=timezone.utc)
    s = str(v).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f", "%Y%m%d_%H%M%S", "%Y-%m-%d"):
        try:
            t = datetime.strptime(s.replace("Z", "+0000") if fmt.endswith("%z") else s.rstrip("Z"), fmt)
            return t if t.tzinfo else t.replace(tzinfo=timezone.utc)   # 沒時區的照 UTC 讀(各工具寫的多是 UTC;差 8 小時照實寫在說明)
        except ValueError:
            continue
    m = re.match(r"(\d{8})_(\d{6})", s)
    if m:
        return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    return None


def _text(d: dict) -> str:
    head = " · ".join(str(d[k]) for k in TEXT_KEYS if k in d and isinstance(d[k], (str, int)) and str(d[k]).strip())[:80]
    note = next((str(d[k]) for k in NOTE_KEYS if k in d and isinstance(d[k], str) and d[k].strip()), "")
    return (head + (":" if head and note else "") + note)[:240]


def non_green(d, lamp_map: dict, depth: int = 0, out: list | None = None) -> list:
    """逐條收非綠(dict 列表裡有 lamp / state / verdict / status 的);深度 ≤ 3。"""
    out = [] if out is None else out
    if depth > 3 or len(out) >= 400:
        return out
    if isinstance(d, dict):
        lk = next((k for k in LAMP_KEYS if k in d and isinstance(d[k], (str, int)) and not isinstance(d[k], bool)), None)
        if lk and depth > 0:
            lamp = norm_lamp(d[lk], lamp_map)
            if lamp in ("RED", "YELLOW", "NODATA"):
                out.append({"lamp": lamp, "raw": str(d[lk]), "text": _text(d)})
        for v in d.values():
            if isinstance(v, (dict, list)):
                non_green(v, lamp_map, depth + 1, out)
    elif isinstance(d, list):
        for v in d[:500]:
            non_green(v, lamp_map, depth + 1, out)
    return out


def flat_next(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [v] if v.strip() else []
    if isinstance(v, dict):
        return [f"{k}:{x}" if isinstance(x, str) else f"{k}:{json.dumps(x, ensure_ascii=False)[:160]}" for k, x in v.items() if x]
    if isinstance(v, list):
        out = []
        for x in v:
            out += flat_next(x) if not isinstance(x, dict) else [_text(x) or json.dumps(x, ensure_ascii=False)[:160]]
        return out
    return [str(v)]


# ---------------------------------------------------------------- git(只讀;不 fetch)
def git(*args) -> tuple[int, str]:
    try:
        r = subprocess.run(["git", "-C", str(VIA), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        return r.returncode, r.stdout.strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)


def git_state() -> dict:
    rc, head = git("rev-parse", "--short=12", "HEAD")
    st = {"head": head if rc == 0 else "", "branch": git("rev-parse", "--abbrev-ref", "HEAD")[1]}
    for name, ref in (("upstream", "@{u}"), ("origin_main", "origin/main")):
        rc, out = git("rev-list", "--left-right", "--count", f"HEAD...{ref}")
        if rc == 0 and re.fullmatch(r"\d+\s+\d+", out):
            a, b = out.split()
            st[name] = {"ahead": int(a), "behind": int(b), "ref": git("rev-parse", "--abbrev-ref", ref)[1] if ref == "@{u}" else ref}
        else:
            st[name] = None
    st["stash"] = len([x for x in git("stash", "list")[1].splitlines() if x.strip()])
    por = [x for x in git("status", "--porcelain")[1].splitlines() if x.strip()]
    st["dirty"] = sum(1 for x in por if not x.startswith("??"))
    st["untracked"] = sum(1 for x in por if x.startswith("??"))
    st["conflicted"] = sum(1 for x in por if x[:2] in ("UU", "AA", "DU", "UD", "AU", "UA", "DD"))
    lamp = "GREEN"
    why = []
    om = st.get("origin_main")
    if st["conflicted"]:
        lamp, why = "RED", why + [f"合併衝突 {st['conflicted']} 檔"]
    if om and om["behind"]:
        lamp, why = worst([lamp, "YELLOW"]), why + [f"落後 origin/main {om['behind']} 提交(本機缺新檔 / 舊尾版)"]
    up = st.get("upstream")
    if up and up["ahead"]:
        lamp, why = worst([lamp, "YELLOW"]), why + [f"{up['ahead']} 個提交還沒推上 {up['ref']}"]
    if st["stash"] > 5:
        why.append(f"stash {st['stash']} 個(不自動清;要清由你決定)")
    st["lamp"], st["why"] = lamp, why
    return st


# ---------------------------------------------------------------- ② 每個來源一列
def read_source(src: dict, lamp_map: dict, stale_default: float, head: str, now: datetime) -> dict:
    p = VIA / src["path"]
    row = {"id": src["id"], "title": src["title"], "area": src["area"], "owner": src["owner"], "path": src["path"],
           "rerun": src.get("rerun", ""), "raw": "", "lamp": "NODATA", "at": "", "age_h": None, "stale": False,
           "head": "", "old_head": False, "summary": "", "items": [], "next": [], "extra": {}}
    if not p.is_file():
        row["summary"] = "檔不在(這台還沒跑過)"
        return row
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        row.update(lamp="RED", summary=f"讀不懂:{type(e).__name__}")
        return row
    if not isinstance(d, dict):
        d = {"rows": d}
    raw = next((dig(d, k) for k in src.get("lamp") or [] if dig(d, k) is not None), None)
    items = non_green(d, lamp_map)
    if raw is None:                                       # 冊上沒指定燈欄:用明細的最差燈(沒有明細 = 資訊)
        row["lamp"] = worst(i["lamp"] for i in items) if items else "INFO"
        row["raw"] = "(由明細推)"
    else:
        row["lamp"], row["raw"] = norm_lamp(raw, lamp_map), str(raw)
    t = next((parse_time(d.get(k)) for k in src.get("time") or [] if parse_time(d.get(k))), None) or \
        datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
    row["at"] = t.strftime("%Y-%m-%d %H:%M UTC")
    row["age_h"] = round((now - t).total_seconds() / 3600, 1)
    row["stale"] = row["age_h"] > float(src.get("stale_h") or stale_default)
    h = str(d.get("head") or "")
    if h:
        row["head"] = h[:12]
        row["old_head"] = bool(head) and not (head.startswith(h[:7]) or h.startswith(head[:7]))
    for label, key in (src.get("extra_lamp") or {}).items():
        row["extra"][label] = norm_lamp(d.get(key), lamp_map)
    row["items"] = items[:40]
    row["items_total"] = len(items)
    row["next"] = [x for k in src.get("next") or [] for x in flat_next(dig(d, k))][:12]
    cnt = {}
    for i in items:
        cnt[i["lamp"]] = cnt.get(i["lamp"], 0) + 1
    row["summary"] = " · ".join(f"{ZH[k]} {v}" for k, v in sorted(cnt.items(), key=lambda x: -ORDER[x[0]])) or "明細全綠 / 沒有明細"
    row["_data"] = d
    return row


def unregistered(sources: list) -> list:
    known = {s["path"] for s in sources}
    out = []
    for f in sorted(glob.glob(str(VIA / "VIA_Reports" / "**" / "*latest*.json"), recursive=True)):
        rel = Path(f).relative_to(VIA).as_posix()
        if rel not in known and "/handover/" not in rel:
            out.append(rel)
    return out


# ---------------------------------------------------------------- ③ 衝突區(冊上 conflict_rules)
def conflicts(rows: dict, head: str) -> list:
    out = []
    # C1 工作流引擎在不在:全景 workflow_graph 的 engine_missing 拆三類 vs SDD X-ENGINE
    sdd = rows.get("S06", {}).get("_data") or {}
    x_eng = next((r for r in sdd.get("rows") or [] if r.get("rule") == "X-ENGINE"), None)
    pan = _newest("VIA_Panorama_v*.py")
    if pan and x_eng:
        try:
            wg = _load(pan, "_mdl254_panorama").workflow_graph(VIA)
            wkf = json.loads((VIA / "supportive modules" / "registry" / wg["book"]).read_text(encoding="utf-8"))
            desc, real, req = [], [], []
            for wf in wkf.get("workflows", []):
                for st in wf.get("steps", []):
                    raw = st.get("engine") or []
                    for x in ([raw] if isinstance(raw, str) else list(raw)):
                        if isinstance(x, str) and x and not any(True for _ in VIA.glob(x)):
                            (desc if not re.search(r"[/*.]", x) else real).append(f"{st['code']}:{x}")
            for n in wg.get("nodes", []):
                if n["kind"] == "stp" and n["lamp"] == "RED" and not any(n["id"] in d for d in desc + real):
                    req.append(n["id"])
            if wg.get("engine_missing"):
                out.append({"id": "C1", "topic": "工作流引擎在不在", "a": f"全景工作流冊圖:引擎不在 {wg['engine_missing']}",
                            "b": f"SDD X-ENGINE {x_eng.get('lamp')}:{str(x_eng.get('msg'))[:60]}", "owner": "SDD X-ENGINE",
                            "truth": f"真的找不到檔 {len(real)}" + (f"({' · '.join(real[:3])})" if real else "")
                                     + f" · 引擎欄是說明文字 {len(desc)}" + (f"({' · '.join(desc[:2])})" if desc else "")
                                     + f" · 引擎在、紅的是掛的需求 MISSING {len(req)}" + (f"({' · '.join(req[:4])})" if req else ""),
                            "lamp": "RED" if real else "YELLOW"})
        except Exception as e:                              # 全景尾版讀不到不擋整頁:照實寫
            out.append({"id": "C1", "topic": "工作流引擎在不在", "a": "全景工作流冊圖讀不到", "b": str(e)[:80], "owner": "SDD X-ENGINE",
                        "truth": "C1 沒量(不冒充一致)", "lamp": "NODATA"})
    # C2 交接燈:交接閘 vs 交接快照
    s2, s3 = rows.get("S02", {}), rows.get("S03", {})
    if s2.get("lamp") and s3.get("lamp") and s2.get("_data") and s3.get("_data"):
        t2, t3 = parse_time(s2["_data"].get("at")), parse_time(s3["_data"].get("ts"))
        if (t2 and t3 and t3 < t2) or s2["lamp"] != s3["lamp"]:
            out.append({"id": "C2", "topic": "交接燈", "a": f"交接閘 {s3['lamp']} · {s3['at']}", "b": f"交接快照 {s2['lamp']} · {s2['at']}",
                        "owner": "交接快照(CGC_MDL140)", "truth": "交接閘比快照舊 → 重算 VIA_Panorama state" if t2 and t3 and t3 < t2
                        else "兩邊量的範圍不同:交接閘另看快照後的提交與 GitHub 同步", "lamp": "YELLOW"})
    # C3 全功能串測燈:閘引用 vs TEST_latest
    g = rows.get("S01", {}).get("_data") or {}
    probe = next((p for p in g.get("probes") or [] if "串測" in str(p.get("probe"))), None)
    t5 = rows.get("S05", {})
    if probe and t5.get("_data"):
        pl = norm_lamp(probe.get("lamp"), {"GREEN": ["GREEN"], "YELLOW": ["YELLOW"], "RED": ["RED"]})
        if pl != t5["lamp"]:
            out.append({"id": "C3", "topic": "全功能串測燈", "a": f"全綠閘探針 {pl}", "b": f"TEST_latest {t5['lamp']} · {t5['at']}",
                        "owner": "TEST_latest(CGC_MDL224)", "truth": "閘跑的是 --quick 子集或較舊的一輪;以 TEST_latest 為準,重跑 via-vcgc gate", "lamp": "YELLOW"})
    # C4 需求條數:需求冊尾版 vs SDD vs 交接閘冊名
    reqf = _newest("VIA_Requirements_SSOT_v*.json")
    if reqf:
        n_book = len(json.loads(reqf.read_text(encoding="utf-8")).get("requirements", []))
        n_sdd = (sdd.get("requirements") if isinstance(sdd.get("requirements"), int) else None)
        gate_book = (rows.get("S03", {}).get("_data") or {}).get("req_book")
        bad = []
        if n_sdd is not None and n_sdd != n_book:
            bad.append(f"SDD {n_sdd} 條")
        if gate_book and gate_book != reqf.name:
            bad.append(f"交接閘讀 {gate_book}")
        if bad:
            out.append({"id": "C4", "topic": "需求條數", "a": f"需求冊尾版 {reqf.name} {n_book} 條", "b": " · ".join(bad), "owner": "需求冊尾版",
                        "truth": "另一方是舊的一輪 → 重跑該來源", "lamp": "YELLOW"})
    # C5 結果是哪個提交量的
    old = [f"{r['title']}(head {r['head']})" for r in rows.values() if r.get("old_head")]
    if old:
        out.append({"id": "C5", "topic": "結果是哪個提交量的", "a": f"{len(old)} 個來源記的 head 不是目前 HEAD {head[:12]}",
                    "b": " · ".join(old[:6]), "owner": "目前 HEAD", "truth": "這些是舊提交的結果;燈照列但不冒充現況,要新結果就重跑", "lamp": "YELLOW"})
    return out


# ---------------------------------------------------------------- 組一頁
def _steps_of(review: dict) -> list:
    """via-review 的步驟欄名是 No / Step / Lamp / Rc / Note;統一成 step / name / lamp / rc / note。"""
    out = []
    for s in review.get("steps") or []:
        if isinstance(s, dict):
            out.append({"step": s.get("step", s.get("No", "")), "name": s.get("name", s.get("Step", "")), "lamp": s.get("lamp", s.get("Lamp", "")),
                        "rc": s.get("rc", s.get("Rc", "")), "note": s.get("note", s.get("Note", ""))})
    return out


def build(review: dict | None = None) -> dict:
    b = book()
    lamp_map, stale = b["lamp_map"], float(b.get("stale_hours_default", 48))
    now = datetime.now(timezone.utc)
    gs = git_state()
    rows = {s["id"]: read_source(s, lamp_map, stale, gs["head"], now) for s in b["sources"]}
    conf = conflicts(rows, gs["head"])
    review = review or {}
    steps = _steps_of(review)
    eff = []                                                 # 總判用的燈:過期算 STALE(黃),不拿舊紅當現況
    for r in rows.values():
        eff.append("STALE" if r["stale"] and r["lamp"] != "GREEN" else r["lamp"])
    lamps = [l for l in eff if l != "NODATA"] + [gs["lamp"]] + [c["lamp"] for c in conf if c["lamp"] != "NODATA"] \
        + [norm_lamp(s.get("lamp"), lamp_map) for s in steps]
    verdict = worst(lamps)
    verdict = "YELLOW" if verdict == "STALE" else verdict
    nxt, seen = [], set()

    def add(text, why):
        k = re.sub(r"\s+", " ", text).strip()
        if k and k not in seen:
            seen.add(k)
            nxt.append({"do": k, "why": why})
    om = gs.get("origin_main")
    if gs["conflicted"]:
        add("先解合併衝突(帳本只增聯集:via-medic sync --apply)", "git")
    if om and om["behind"]:
        add("git pull --ff-only(不能快轉 → via-medic sync --apply:零 force · 帳本只增聯集)", f"落後 origin/main {om['behind']}")
    up = gs.get("upstream")
    if up and up["ahead"]:
        add(f"git push(還有 {up['ahead']} 個提交沒推上 {up['ref']})", "未推")
    for r in sorted(rows.values(), key=lambda r: -ORDER[r["lamp"]]):
        if r["lamp"] == "RED" and not r["stale"] and r["rerun"]:
            add(r["rerun"], f"{r['title']} 紅")
    for r in rows.values():
        for x in r["next"]:
            add(x, r["title"])
    for r in rows.values():
        if r["stale"] and r["lamp"] != "GREEN" and r["rerun"]:
            add(r["rerun"], f"{r['title']} 過期 {r['age_h']} 小時")
    res = {"engine": ENGINE, "book": b["_file"], "at": now.strftime("%Y-%m-%d %H:%M:%S UTC"), "verdict": verdict, "git": gs,
           "sources": [{k: v for k, v in r.items() if k != "_data"} for r in rows.values()], "conflicts": conf, "steps": steps,
           "next": nxt, "unregistered": unregistered(b["sources"]),
           "review": {k: review.get(k) for k in ("stamp", "final", "overview", "red", "yellow", "anchors", "sections") if k in review}}
    tally = {}
    for l in eff:
        tally[l] = tally.get(l, 0) + 1
    res["tally"] = tally
    return res


def to_md(res: dict) -> str:
    g = res["git"]
    om = g.get("origin_main") or {}
    out = [f"# 唯一頁 · {res['verdict']} · {res['at']}", "",
           f"- HEAD {g['head']} · 分支 {g['branch']} · 對 origin/main 領先 {om.get('ahead', '?')} / 落後 {om.get('behind', '?')} · stash {g['stash']} · 未提交 {g['dirty']} · 未追蹤 {g['untracked']}",
           "- 來源燈:" + " · ".join(f"{ZH[k]} {v}" for k, v in sorted(res["tally"].items(), key=lambda x: -ORDER[x[0]])), "", "## 下一步(只一份,依序)"]
    out += [f"{i}. {n['do']}  ← {n['why']}" for i, n in enumerate(res["next"][:25], 1)] or ["- 無"]
    out += ["", "## 衝突"] + ([f"- {c['id']} {c['topic']}:{c['a']} ↔ {c['b']} → {c['truth']}(正主 {c['owner']})" for c in res["conflicts"]] or ["- 無"])
    out += ["", "## 紅 / 過期來源"]
    out += [f"- {s['id']} {s['title']} {ZH['STALE'] if s['stale'] else ZH[s['lamp']]}({s['raw']} · {s['at']} · {s['age_h']}h)· {s['summary']}"
            for s in res["sources"] if s["lamp"] in ("RED", "YELLOW") or s["stale"]] or ["- 無"]
    rv = res.get("review") or {}
    if rv:
        red, yel = rv.get("red") or [], rv.get("yellow") or []
        out += ["", f"## 總檢本輪 {rv.get('stamp', '')} · 結束碼 {rv.get('final', '?')} · 紅 {len(red)} · 黃 {len(yel)} · 錨點 {len(rv.get('anchors') or [])}"]
        out += [f"- [{s['lamp']}] {s['step']} {s['name']} · rc {s['rc']}" + (f" · {str(s['note'])[:120]}" if s['note'] else "") for s in res["steps"]]
        out += [f"- 紅:{x}" for x in red[:20]]
    if res["unregistered"]:
        out += ["", f"## 未登錄來源 {len(res['unregistered'])}"] + [f"- {u}" for u in res["unregistered"][:30]]
    return "\n".join(out) + "\n"


_JS = """<script>
(function(){var t=document.getElementById('obx');if(!t)return;function f(){var q=(t.value||'').toLowerCase();
document.querySelectorAll('.onep table.m tbody tr, .onep details').forEach(function(r){r.style.display=(!q||r.textContent.toLowerCase().indexOf(q)>=0)?'':'none';});}
t.addEventListener('input',f);
document.querySelectorAll('table.m thead th').forEach(function(th,i){th.style.cursor='pointer';th.addEventListener('click',function(){
var tb=th.closest('table').tBodies[0],rs=Array.prototype.slice.call(tb.rows),d=th.dataset.d==='1'?-1:1;th.dataset.d=d===1?'1':'0';
rs.sort(function(a,b){var x=a.cells[i].textContent,y=b.cells[i].textContent,nx=parseFloat(x),ny=parseFloat(y);
return (!isNaN(nx)&&!isNaN(ny)?nx-ny:x.localeCompare(y,'zh-Hant'))*d;});rs.forEach(function(r){tb.appendChild(r);});});});})();
</script>"""


def _table_html(rows: list, limit: int = 300) -> str:
    rows = [r for r in rows if isinstance(r, dict)][:limit]
    if not rows:
        return "<p>(無資料)</p>"
    cols = list(dict.fromkeys(k for r in rows for k in r.keys()))
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in cols)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(r.get(c, '')))[:400]}</td>" for c in cols) + "</tr>" for r in rows)
    return f"<div class='mwrap'><table class='m'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def review_details(rv: dict) -> str:
    """via-review 原多頁的每一頁 → 一個可點開的段(表就表、文字就原文);紅黃全文與錨點也在。不刪一頁內容。"""
    parts = []
    for name, val in (rv.get("sections") or {}).items():
        if isinstance(val, list):
            inner = _table_html(val) + (f"<p>(共 {len(val)} 列,這裡列前 300)</p>" if len(val) > 300 else "")
        elif isinstance(val, dict):
            inner = "".join(f"<h3>{html.escape(str(k))}</h3>" + (_table_html(v) if isinstance(v, list) else f"<pre>{html.escape(str(v))}</pre>")
                            for k, v in val.items())
        else:
            inner = f"<pre>{html.escape(str(val))}</pre>"
        parts.append(f"<details><summary><b>{html.escape(str(name))}</b></summary>{inner}</details>")
    red, yel = rv.get("red") or [], rv.get("yellow") or []
    parts.append(f"<details><summary><b>紅黃全文</b> · 紅 {len(red)} · 黃 {len(yel)}</summary><h3>紅字</h3><pre>{html.escape(chr(10).join(map(str, red)))}</pre>"
                 f"<h3>黃字</h3><pre>{html.escape(chr(10).join(map(str, yel)))}</pre></details>")
    anch = rv.get("anchors") or []
    if anch:
        parts.append(f"<details><summary><b>AST 錨點</b> · {len(anch)}(檔:行 · 類 · 定位種類)</summary>{_table_html(anch, 2000)}</details>")
    return "".join(parts)


def _cell(lamp: str, label: str | None = None) -> dict:
    return {"t": label or ZH.get(lamp, lamp), "s": SHOW.get(lamp, "NA")}


def write(res: dict, open_page: bool = True) -> dict:
    spec = _load(_newest("CGC_MDL173_MatrixReportSpec_v*.py"), "_mdl254_spec")
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    md = to_md(res)
    g, om = res["git"], res["git"].get("origin_main") or {}
    body = ["<div class='onep'><div class='bar'><input id='obx' placeholder='篩選:任何字(來源 / 燈 / 指令 / 檔名…)' style='min-width:24em'></div>"]
    body.append(spec.html_table(["步", "要做的事", "為什麼"], [[str(i), n["do"], n["why"]] for i, n in enumerate(res["next"], 1)] or [["—", "沒有要做的事", ""]],
                                caption="① 下一步(只一份,依序;git 同步 → 紅的重跑 → 各來源自己的下一步 → 過期的重跑)"))
    body.append(spec.html_table(["項", "值"], [
        ["燈", _cell(g["lamp"])], ["HEAD · 分支", f"{g['head']} · {g['branch']}"],
        ["對 origin/main", f"領先 {om.get('ahead', '?')} · 落後 {om.get('behind', '?')}"],
        ["上游未推", str((g.get("upstream") or {}).get("ahead", "沒有上游"))], ["stash · 未提交 · 未追蹤 · 衝突", f"{g['stash']} · {g['dirty']} · {g['untracked']} · {g['conflicted']}"],
        ["說明", " · ".join(g["why"]) or "與 origin 一致"]], caption="② Git 同步(只讀;不 fetch)"))
    rv = res.get("review") or {}
    lm = book()["lamp_map"]
    if res["steps"] or rv:
        if rv.get("overview"):
            body.append(spec.html_table(["項目", "值"], [[str(o.get("項目", "")), str(o.get("值", ""))] for o in rv["overview"] if isinstance(o, dict)],
                                        caption=f"③ 總檢本輪(via-review {rv.get('stamp', '')} · 結束碼 {rv.get('final', '?')})"))
        body.append(spec.html_table(["步", "名稱", "燈", "rc", "說明"], [[str(s["step"]), str(s["name"]), _cell(norm_lamp(s["lamp"], lm)), str(s["rc"]),
                                                                        str(s["note"])[:240]] for s in res["steps"]] or [["—", "", _cell("NODATA"), "", ""]],
                                    caption="③ 總檢步驟燈號"))
    body.append(spec.html_table(["衝突", "主題", "一方", "另一方", "實際原因", "正主", "燈"],
                                [[c["id"], c["topic"], c["a"], c["b"], c["truth"], c["owner"], _cell(c["lamp"])] for c in res["conflicts"]] or [["—", "沒有衝突", "", "", "", "", _cell("GREEN")]],
                                caption="④ 衝突(同一件事兩個來源說法不一;以正主為準)"))
    srows = []
    for s in sorted(res["sources"], key=lambda s: (-ORDER["STALE" if s["stale"] and s["lamp"] != "GREEN" else s["lamp"]], s["id"])):
        eff = "STALE" if s["stale"] and s["lamp"] != "GREEN" else s["lamp"]
        srows.append([s["id"], s["area"], s["title"], _cell(eff), s["raw"] or "—", s["at"] or "—", "" if s["age_h"] is None else str(s["age_h"]),
                      (s["head"] + (" ≠ HEAD" if s["old_head"] else "")) or "—", s["summary"],
                      " · ".join(f"{k} {ZH.get(v, v)}" for k, v in s["extra"].items()) or "—", s["owner"], s["rerun"] or "—"])
    body.append(spec.html_table(["#", "域", "來源", "統一燈", "原燈", "時間", "幾小時前", "量的提交", "非綠明細", "另燈", "正主", "重跑"], srows,
                                caption=f"⑤ 全部來源(冊 {res['book']} · 過期 = 超過時限,不冒充現況)", num_cols={6}))
    det = []
    for s in res["sources"]:
        if not s["items"]:
            continue
        lines = "".join(f"<tr><td><span class='s-{SHOW.get(i['lamp'], 'NA')}'>{ZH.get(i['lamp'])}</span></td><td>{html.escape(i['raw'])}</td>"
                        f"<td>{html.escape(i['text'])}</td></tr>" for i in s["items"])
        more = f"(共 {s['items_total']} 條,這裡列前 {len(s['items'])};全文看 {html.escape(s['path'])})" if s["items_total"] > len(s["items"]) else ""
        det.append(f"<details><summary><b>{html.escape(s['id'])} {html.escape(s['title'])}</b> · {html.escape(s['summary'])} {more}</summary>"
                   f"<div class='mwrap'><table class='m'><thead><tr><th>燈</th><th>原燈</th><th>明細</th></tr></thead><tbody>{lines}</tbody></table></div></details>")
    body.append("<div class='mwrap'><h2>⑥ 各來源非綠明細(點開;每來源前 40 條)</h2>" + "".join(det) + "</div>")
    if rv:
        body.append("<div class='mwrap'><h2>⑧ 總檢各段全文(原多頁的每一頁都在這裡;點開)</h2>" + review_details(rv) + "</div>")
    if res["unregistered"]:
        body.append(spec.html_table(["未登錄來源(冊外的 *_latest.json;不漏,登進來源冊新版後就併進上表)"], [[u] for u in res["unregistered"]], caption="⑦ 未登錄來源"))
    body.append("</div>" + _JS)
    tl = res["tally"]
    kpis = [{"label": "總判", "value": ZH[res["verdict"]], "state": SHOW[res["verdict"]]},
            {"label": "紅", "value": tl.get("RED", 0), "state": "RED" if tl.get("RED") else "GREEN"},
            {"label": "黃", "value": tl.get("YELLOW", 0), "state": "YELLOW"}, {"label": "過期", "value": tl.get("STALE", 0), "state": "YELLOW"},
            {"label": "綠", "value": tl.get("GREEN", 0), "state": "GREEN"}, {"label": "衝突", "value": len(res["conflicts"]), "state": "YELLOW" if res["conflicts"] else "GREEN"},
            {"label": "落後", "value": om.get("behind", "?"), "state": "YELLOW" if om.get("behind") else "GREEN"}]
    page = spec.page_html("".join(body), title="VIA 總檢 · 唯一頁", out=OUT / f"ONEPAGE_{stamp}.html", md=md,
                          payload={k: v for k, v in res.items()}, kpis=kpis,
                          subtitle=f"{res['at']} · HEAD {g['head']} · 來源冊 {res['book']} · {ENGINE}",
                          law="本頁只讀各工具自己的最新結果(不重跑 · 不改 · 舊頁不刪);燈號口徑統一(綠 / 黃 / 紅 / 無資料 / 資訊 / 過期);同一件事兩邊說法不一列衝突並標正主。")
    latest = OUT / "ONEPAGE_latest.html"
    latest.write_text(page.read_text(encoding="utf-8"), encoding="utf-8")
    for nm in (f"ONEPAGE_{stamp}.json", "ONEPAGE_latest.json"):
        (OUT / nm).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for nm in (f"ONEPAGE_{stamp}.md", "ONEPAGE_latest.md"):
        (OUT / nm).write_text(md, encoding="utf-8")
    if open_page and not os.environ.get("VIA_NO_OPEN") and hasattr(os, "startfile"):
        try:
            os.startfile(str(latest))                         # Windows 直開;容器 / 非 Windows 不開
        except OSError as e:
            print(f"  [頁] 沒自動開({e});自己開:{latest}")
    return {"html": latest, "md": OUT / "ONEPAGE_latest.md", "json": OUT / "ONEPAGE_latest.json"}


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    b = book()
    lm = b["lamp_map"]
    chk("① 燈號口徑統一:AMBER→黃 · OK→綠 · ABSENT→無資料 · PLAN→資訊 · rc 0/2/1", [norm_lamp(x, lm) for x in ("AMBER", "OK", "ABSENT", "PLAN", 0, 2, 1)]
        == ["YELLOW", "GREEN", "NODATA", "INFO", "GREEN", "YELLOW", "RED"])
    chk("② 時間格式都讀得懂(ISO · 空白 · 帶時區 · 20261001_222547)", all(parse_time(x) for x in (
        "2026-10-02T14:24:23+00:00", "2026-10-02 14:24:23", "2026-10-02 14:24:23 +0000", "20261001_222547_1562", "2026-09-30T09:57:23Z")))
    data = {"rows": [{"id": "X1", "lamp": "RED", "msg": "壞了"}, {"id": "X2", "state": "GREEN"}, {"probe": "p", "lamp": "AMBER", "note": "注意"}]}
    items = non_green(data, lm)
    chk("③ 非綠逐條收(綠的不收)", [i["lamp"] for i in items] == ["RED", "YELLOW"] and "壞了" in items[0]["text"], items)
    ids = [s["id"] for s in b["sources"]]
    chk("④ 來源冊:代碼唯一 · 路徑唯一 · 每條有正主", len(ids) == len(set(ids)) and len({s["path"] for s in b["sources"]}) == len(ids)
        and all(s.get("owner") for s in b["sources"]))
    res = build({"stamp": "t", "final": 0, "steps": [{"No": "①", "Step": "Git", "Lamp": "GATE", "Rc": 4, "Note": "t"}],
                 "sections": {"Git 整合": [{"狀態": "M", "檔": "a.py"}], "WORKFLOW 檢視": "x"}, "red": [], "yellow": ["y"], "anchors": [{"檔": "a.py", "行": "1"}]})
    chk("⑤ 真樹一頁:每個來源都有一列 · 總判在五態內 · 下一步去重", len(res["sources"]) == len(ids) and res["verdict"] in ORDER
        and len({n["do"] for n in res["next"]}) == len(res["next"]), res["verdict"])
    old = {"id": "S99", "title": "t", "area": "a", "owner": "o", "path": "VIA_Reports/gate/GATE_latest.json", "lamp": ["verdict"], "time": ["at"], "stale_h": 0.0001}
    r = read_source(old, lm, 48, "", datetime.now(timezone.utc))
    chk("⑥ 過期判定:超過時限的結果標過期(不冒充現況)", r["stale"] is True or r["lamp"] == "NODATA", (r["stale"], r["lamp"]))
    chk("⑦ 冊外 *_latest.json 列未登錄(不漏)", isinstance(res["unregistered"], list))
    rd = review_details(res["review"])
    chk("⑨ 總檢本輪併進同一頁:步驟欄名統一(No/Step/Lamp → step/name/lamp)· 原多頁每一頁都成可點開的段 · 閘關 GATE = 黃",
        res["steps"][0]["name"] == "Git" and norm_lamp(res["steps"][0]["lamp"], lm) == "YELLOW" and "Git 整合" in rd and "WORKFLOW 檢視" in rd and "AST 錨點" in rd)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 加速器橋 · 網路橋在;只收 VCGC;不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and "VIA_FROM_VCGC" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"[唯一頁 v0100] 自測 {sum(ok)}/{len(ok)}")
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "engine": ENGINE, "state": "DENY", "why": "only via-vcgc(VIA_FROM_VCGC=YES);短令 via-review"}, ensure_ascii=False))
        return 2
    verb, rest = (args[0], args[1:]) if args else ("build", [])
    if verb != "build":
        print(__doc__)
        return 2
    review = {}
    for flag in ("--review", "--steps"):
        if flag in rest:
            try:
                got = json.loads(Path(rest[rest.index(flag) + 1]).read_text(encoding="utf-8-sig"))
                review = got if isinstance(got, dict) else {"steps": got}
            except (IndexError, OSError, ValueError) as e:
                print(f"  [唯一頁] {flag} 讀不到({e});照沒有總檢本輪出頁")
    try:
        res = build(review)
    except RuntimeError as e:
        print(json.dumps({"engine": ENGINE, "state": "RED", "why": str(e)}, ensure_ascii=False))
        return 1
    paths = write(res, open_page="--no-open" not in rest)
    t = res["tally"]
    print(f"[唯一頁] {res['verdict']} · 來源 {len(res['sources'])}(" + " · ".join(f"{ZH[k]} {v}" for k, v in sorted(t.items(), key=lambda x: -ORDER[x[0]]))
          + f")· 衝突 {len(res['conflicts'])} · 未登錄 {len(res['unregistered'])} · 下一步 {len(res['next'])}")
    for n in res["next"][:8]:
        print(f"  [下一步] {n['do']}  ← {n['why']}")
    for c in res["conflicts"]:
        print(f"  [衝突] {c['id']} {c['topic']}:{c['truth']}")
    print(f"  [頁] {paths['html']} · 貼回包 {paths['md']}")
    if "--json" in rest:
        print(json.dumps({"verdict": res["verdict"], "tally": t, "conflicts": len(res["conflicts"])}, ensure_ascii=False))
    return {"GREEN": 0, "YELLOW": 2, "INFO": 0, "NODATA": 2}.get(res["verdict"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
