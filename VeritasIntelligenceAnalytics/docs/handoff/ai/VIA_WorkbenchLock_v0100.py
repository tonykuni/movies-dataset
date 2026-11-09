#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_WorkbenchLock v0100 — 審查包 HTML U/I 視覺鎖定 → 本倉自建工作台(操作員 2026-11-09 令)

正本 = review/VIA_Workbench_LockSite_v0106_4/(位元組鎖:css · 頁模板 · js · 標誌)。
本引擎不手抄視覺:`kit` 從正本 css 抽 :root token 與版面契約;`build` 用正本模板 + 本倉真資料
(五系統憲法矩陣 · 交接待辦 · 衝突冊 · 政策冊 · 盤點冊 · 進度帳 · 工具鎖冊)生成五系統頁 + hub;
`check` 驗:鎖站 sha 4/4 · 生成頁含正本 token 區塊(sha 相同)· 結構 id 齊全。

界線:審查包自己的燈與資料(OBS-*)不進本倉工作台;不執行審查包任何 .py / .ps1;唯讀本倉冊;不發號、不改燈。
燈號:RED = 來源自報 RED / OPEN / BLOCKED;GREEN = 來源自報 GREEN / VERIFIED / 檔案在;其餘 YELLOW(未跑 ≠ 綠)。

用法:
  python VIA_WorkbenchLock_v0100.py kit|build|check|all [--via <VIA>] [--out <夾>] [--open] [--files …]
  python VIA_WorkbenchLock_v0100.py --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys, pathlib as _sa_pl
    for _sa_p in [_sa_pl.Path(__file__).resolve()] + list(_sa_pl.Path(__file__).resolve().parents):
        if (_sa_p / "supportive modules").is_dir():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
    import VeritasCeleritas_v1141 as _sa  # noqa: F401
except Exception:
    _sa = None
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 網路橋(本引擎不出網;只為治理覆蓋登記,graceful) =====
try:
    import importlib as _nb_il
    _nb = _nb_il.import_module("network.VeritasAegisNexus_v1652")  # noqa: F841
except Exception:
    _nb = None
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
import base64
import datetime as _dt
import glob
import gzip
import hashlib
import html as _html
import json
import os
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0100"
ENGINE = f"VIA_WorkbenchLock_{VERSION}"
HERE = Path(__file__).resolve().parent
LOCK_REL = Path("review") / "VIA_Workbench_LockSite_v0106_4"
LOCK_FILES = {
    "css": "subsystem_v0106_4.css",
    "html": "subsystem_v0106_4.html",
    "js": "subsystem_v0106_4.js",
    "logo": "veritas_logo_header_v0105.png",
}
UI_CONTRACT_VERSION = "v0106.4"          # 正本 js 綁定的 payload 身分(decodePayload 檢 bundle.version)
CATEGORIES = ["systems", "io", "commands", "files", "environment", "policy", "conflicts", "requirements", "tests"]
REQUIRED_IDS = ["masthead", "input-rail", "inspector", "kpis", "summary-view", "verification-view",
                "management-view", "category-tabs", "workflow-chart", "view", "payload", "print-all"]
SYSTEMS = ["VCGC", "VDF", "VRN-2", "VQG", "VAP"]
SYS_TOKENS = {"VCGC": ("VCGC",), "VDF": ("VDF",), "VRN-2": ("VRN-2", "VRN2", "VRN"), "VQG": ("VQG",), "VAP": ("VAP",)}
KIT_OUT = HERE / "VIA_WorkbenchLock_kit_latest.json"
CHECK_OUT = HERE / "VIA_WorkbenchLock_check_latest.json"
PAGE_NAME = "VIA_Workbench_{sys}_latest.html"
HUB_NAME = "index.html"
WARNINGS: list[str] = []            # 不吞錯:讀不到 / 開不了的都記這裡,寫進 build / check 收據


# ---------- 小工具 ----------
def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_text(t: str) -> str:
    return sha256_bytes(t.encode("utf-8"))


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def read_jsonl(p: Path) -> list:
    rows = []
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception as exc:
                    WARNINGS.append(f"jsonl 壞列 {p.name}: {exc}")
    except Exception as exc:
        WARNINGS.append(f"jsonl 讀不到 {p}: {exc}")
    return rows


def tail_glob(via: Path, pattern: str):
    hits = sorted(glob.glob(str(via / pattern)))
    return Path(hits[-1]) if hits else None


def lamp_of(value) -> str:
    """來源字串 → RED / GREEN / YELLOW(與正本 js statusCode 同規則,外加 VERIFIED / OPEN / BLOCKED 同義)。"""
    s = str(value if value is not None else "").upper()
    if re.search(r"\b(RED|OPEN|BLOCKED|FAIL|FAILED|ERROR)\b", s):
        return "RED"
    if re.search(r"\b(GREEN|VERIFIED|PASS|OK|ACTIVE|COVERED)\b", s):
        return "GREEN"
    return "YELLOW"


def mentions(text: str, system: str) -> bool:
    t = text.upper()
    if system == "VRN-2":
        return "VRN" in t and "VRN-1" not in t.replace("VRN-2", "")
    return any(tok in t for tok in SYS_TOKENS[system])


# ---------- 鎖站 ----------
def lock_site(via: Path) -> Path:
    return via / LOCK_REL


def verify_lock_site(via: Path) -> dict:
    site = lock_site(via)
    sums = site / "SHA256SUMS.txt"
    out = {"site": str(LOCK_REL), "ok": False, "files": {}, "problems": []}
    if not sums.exists():
        out["problems"].append("SHA256SUMS.txt 不在")
        return out
    for line in sums.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        want, name = parts[0], parts[-1]
        p = site / name
        if not p.exists():
            out["files"][name] = "MISSING"
            out["problems"].append(f"{name} MISSING")
            continue
        got = sha256_file(p)
        out["files"][name] = "OK" if got == want else "MISMATCH"
        if got != want:
            out["problems"].append(f"{name} MISMATCH")
    for key, name in LOCK_FILES.items():
        if name not in out["files"]:
            out["problems"].append(f"{name} 未列入 SHA256SUMS")
    out["ok"] = not out["problems"]
    return out


def extract_tokens(css_text: str) -> tuple[dict, str, str]:
    """抽 :root{} 區塊 → (token dict, 區塊原文, 區塊 sha256)。手抄會漂移,抽取不會。"""
    m = re.search(r":root\s*\{[^}]*\}", css_text)
    if not m:
        return {}, "", ""
    block = m.group(0)
    tokens = {}
    for name, val in re.findall(r"(--[a-zA-Z0-9-]+)\s*:\s*([^;]+);", block):
        tokens[name] = val.strip()
    return tokens, block, sha256_text(block)


def layout_contract(html_text: str, css_text: str) -> dict:
    ids = re.findall(r'id="([^"]+)"', html_text)
    tabs = re.findall(r'data-tab="([^"]+)"', html_text)
    cats = re.findall(r'<option value="([a-z]+)">', html_text)
    media = sorted(set(re.findall(r"@media[^{]+", css_text)))
    return {
        "required_ids_present": [i for i in REQUIRED_IDS if i in ids],
        "required_ids_missing": [i for i in REQUIRED_IDS if i not in ids],
        "center_tabs": tabs,
        "management_categories": [c for c in cats if c in CATEGORIES],   # 模板 select 順序(systems 在末)
        "categories_match_js_order": sorted(c for c in cats if c in CATEGORIES) == sorted(CATEGORIES),
        "fixed_columns": ["status", "id", "ssot_name", "category", "version", "completion_time", "tools", "…", "error_detail"],
        "panels": ["input-rail(左 · 可收合)", "center(摘要 / 驗證 / 管理)", "inspector(右 · 可收合)"],
        "breakpoints": [m.strip() for m in media],
        "lamp_rule": {"RED": "2.8s 慢 pulse(reduced-motion 時靜態)", "YELLOW": "靜態", "GREEN": "靜態",
                      "red_pulse_in_css": bool(re.search(r"2\.8s", css_text))},
        "placeholders": sorted(set(re.findall(r"__[A-Z_]+__", html_text))),
    }


def kit(via: Path, write: bool = True) -> dict:
    site = lock_site(via)
    lock = verify_lock_site(via)
    css = (site / LOCK_FILES["css"]).read_text(encoding="utf-8") if (site / LOCK_FILES["css"]).exists() else ""
    tpl = (site / LOCK_FILES["html"]).read_text(encoding="utf-8") if (site / LOCK_FILES["html"]).exists() else ""
    tokens, block, block_sha = extract_tokens(css)
    manifest = read_json(site / "manifest.json", {}) or {}
    info = {
        "engine": ENGINE, "generated_utc": utc_now(), "ui_contract_version": UI_CONTRACT_VERSION,
        "lock_site": lock, "token_count": len(tokens), "tokens": tokens, "token_block_sha256": block_sha,
        "contract": layout_contract(tpl, css),
        "source": {k: manifest.get(k) for k in ("source_zip", "source_zip_sha256", "source_receipt", "visual_lock")},
        "lamp": "GREEN" if lock["ok"] and tokens and not layout_contract(tpl, css)["required_ids_missing"] else "RED",
    }
    if write:
        KIT_OUT.write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    return info


# ---------- 本倉資料 → LAST_MATRIX ----------
def _row(**kw) -> dict:
    base = {"status": "YELLOW", "id": "", "ssot_name": "", "version": "", "completion_time": "NOT_OBSERVED",
            "tools": "", "system": "", "source": "", "source_sha256": "", "kind": "", "scope": "", "error_detail": ""}
    base.update(kw)
    return base


def _src(via: Path, rel) -> tuple[str, str]:
    if not rel:
        return "", ""
    p = via / rel
    return str(rel), (sha256_file(p) if p.exists() else "")


def load_sources(via: Path) -> dict:
    s = {}
    s["constitution_path"] = Path("docs/handoff/ai/VIA_FiveSystemConstitution_latest.json")
    s["constitution"] = read_json(via / s["constitution_path"], {}) or {}
    s["handoff_path"] = Path("docs/handoff/HANDOFF_latest.json")
    s["handoff"] = read_json(via / s["handoff_path"], {}) or {}
    lp = tail_glob(via, "supportive modules/registry/VIA_Policy_Laws_SSOT_v*.json")
    s["laws_path"] = lp.relative_to(via) if lp else None
    s["laws"] = (read_json(lp, {}) or {}).get("laws", []) if lp else []
    ip = tail_glob(via, "supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v*.json")
    s["inventory_path"] = ip.relative_to(via) if ip else None
    inv = read_json(ip, {}) if ip else {}
    s["stations"] = (inv or {}).get("stations") or (inv or {}).get("items") or []
    s["progress_path"] = Path("docs/handoff/ai/VIA_FiveSystem_Progress_v0100.jsonl")
    s["progress"] = read_jsonl(via / s["progress_path"])
    s["lock_path"] = Path("supportive modules/registry/VIA_ToolVersion_Lock_v0100.json")
    s["toollock"] = read_json(via / s["lock_path"], {}) or {}
    s["evidence"] = []
    for f in sorted(glob.glob(str(via / "docs/handoff/evidence/*.json"))):
        d = read_json(Path(f), None)
        if isinstance(d, dict) and d.get("case"):
            s["evidence"].append((Path(f).relative_to(via), d))
    return s


def rows_for(via: Path, system: str, s: dict) -> dict:
    M = {c: [] for c in CATEGORIES}
    con = s["constitution"]
    csrc, csha = _src(via, s["constitution_path"])
    crow = next((r for r in con.get("systems", []) if r.get("sys") == system), None)
    # systems
    if crow:
        M["systems"].append(_row(
            status=crow.get("lamp", "YELLOW"), id=crow.get("number") or "NOT_ASSIGNED", ssot_name=system,
            version=crow.get("entry_version") or "", completion_time=con.get("generated_utc", "NOT_OBSERVED"),
            tools=f"{crow.get('entry', '')} · sha8 {crow.get('entry_sha8', '')}", system=system, source=csrc,
            source_sha256=csha, kind="FIVE_SYSTEM_CONSTITUTION", scope="L125 編號憲法性 · 入口尾版 · 數冊",
            role="獨立系統 MAIN SSOT 主導(L123 對等)", numberbook_rows=crow.get("numberbook_rows"),
            integration_status="編號 = 唯一跨系統關聯(L125)", standalone_status=f"run {crow.get('run_lamp', 'NOT_OBSERVED')}" if crow.get("run_lamp") else "見 tests 類",
            error_detail=crow.get("note") or ("" if crow.get("lamp") == "GREEN" else f"憲法燈 {crow.get('lamp')}:{crow.get('constitution', '')}")))
        # io = SSOT 冊
        for i, ss in enumerate(crow.get("ssot") or []):
            tail = ss.get("tail") or ""
            M["io"].append(_row(status="GREEN" if ss.get("present") else "RED", id=f"{system}-SSOT-{i + 1:02d}",
                                ssot_name=Path(tail).name if tail else ss.get("pattern", ""), version=(re.search(r"v\d{4}", tail or "") or [""])[0] if tail else "",
                                tools=ss.get("pattern", ""), system=system, source=tail, source_sha256=sha256_file(via / tail) if tail and (via / tail).exists() else "",
                                kind="SSOT_BOOK", scope="系統自己的冊(正本歸各系統 · L122 ①)",
                                error_detail="" if ss.get("present") else "冊不在"))
        # files = 入口
        ent = crow.get("entry") or ""
        if ent:
            M["files"].append(_row(status="GREEN" if (via / ent).exists() else "RED", id=crow.get("number") or "NOT_ASSIGNED",
                                   ssot_name=Path(ent).name, version=crow.get("entry_version") or "", tools=f"{crow.get('entry_lines', 0)} 行",
                                   system=system, source=ent, source_sha256=sha256_file(via / ent) if (via / ent).exists() else "",
                                   kind="ENTRY_TAIL", scope="系統入口尾版(薄尾)", error_detail="" if (via / ent).exists() else "入口不在"))
    else:
        M["systems"].append(_row(status="YELLOW", id="NOT_ASSIGNED", ssot_name=system, system=system, kind="FIVE_SYSTEM_CONSTITUTION",
                                 scope="憲法矩陣無此列", error_detail="VIA_FiveSystemConstitution_latest.json 沒有此系統列 · NOT_OBSERVED"))
    # commands = 盤點冊站(依系統 token;VCGC = 其餘)
    isrc, isha = _src(via, s["inventory_path"])
    for st in s["stations"]:
        text = json.dumps(st, ensure_ascii=False)
        others = [o for o in SYSTEMS if o != "VCGC" and mentions(text, o)]
        hit = mentions(text, system) if system != "VCGC" else not others
        if not hit:
            continue
        M["commands"].append(_row(status="YELLOW", id=str(st.get("id", "")), ssot_name=str(st.get("name", "")),
                                  version=str(st.get("version", "")), tools=" ".join(str(a) for a in (st.get("argv") or [])),
                                  system=system, source=isrc, source_sha256=isha, kind="INVENTORY_STATION",
                                  scope="quick" if st.get("quick") else "full",
                                  error_detail="本次 build 未執行此站;以 VCGC test --quick / FunctionLedger 收據為準(未跑 ≠ 綠)"))
    # environment = 工具鎖冊(VCGC 承鎖;其他系統列自己用到的家族)
    lsrc, lsha = _src(via, s["lock_path"])
    fam_for = {"VCGC": None, "VDF": ("network", "accelerator", "frame"), "VRN-2": ("layout", "nlp", "ocr", "pdfplumber", "praddle", "accelerator"),
               "VQG": ("accelerator", "frame"), "VAP": ("accelerator",)}
    for fam, v in s["toollock"].items():
        if not isinstance(v, dict) or not v.get("path"):
            continue
        if fam_for.get(system) is not None and fam not in fam_for[system]:
            continue
        rel = str(v["path"]).replace("VeritasIntelligenceAnalytics/", "", 1)
        present = (via / rel).exists()
        M["environment"].append(_row(status="GREEN" if present else "RED", id=f"LOCK-{fam}", ssot_name=Path(rel).name,
                                     version=(re.search(r"v\d{4}", rel) or [""])[0], tools=fam, system=system, source=lsrc, source_sha256=lsha,
                                     kind="TOOL_LOCK", scope="鎖冊啟用家族(換版只經 via-vcgc tools activate)", error_detail="" if present else "鎖定路徑不在"))
    # policy = 政策冊(提到本系統或 L120/L122/L123/L125)
    psrc, psha = _src(via, s["laws_path"])
    for law in s["laws"]:
        lid = str(law.get("id", ""))
        text = f"{law.get('key', '')} {law.get('zh', '')} {law.get('cat', '')}"
        if lid in ("L120", "L122", "L123", "L125") or mentions(text, system):
            M["policy"].append(_row(status=lamp_of(law.get("status", "")), id=lid, ssot_name=str(law.get("key", "")),
                                    version=str(law.get("batch", "")), tools=str(law.get("cat", "")), system=system, source=psrc, source_sha256=psha,
                                    kind="LAW", scope=str(law.get("zh", ""))[:160], error_detail="" if lamp_of(law.get("status", "")) == "GREEN" else f"status {law.get('status')}"))
    # conflicts = 憲法矩陣 OPEN 衝突(VCGC 偵測方全列;他系統只列提到自己的)
    for c in con.get("conflicts_open", []) or []:
        what = str(c.get("what", ""))
        if system != "VCGC" and not mentions(what, system):
            continue
        M["conflicts"].append(_row(status="RED" if str(c.get("status", "")).upper() == "OPEN" else lamp_of(c.get("status")),
                                   id=str(c.get("id", "")), ssot_name=what[:80], version=str(c.get("severity", "")), tools="裁定書(L122 ④)",
                                   system=system, source=csrc, source_sha256=csha, kind="CONFLICT", scope="OPEN 期間編號留空(L125)",
                                   error_detail=what))
    # requirements = 交接待辦(提到本系統)
    hsrc, hsha = _src(via, s["handoff_path"])
    for p in s["handoff"].get("pending", []) or []:
        text = json.dumps(p, ensure_ascii=False)
        pid = str(p.get("id", ""))
        own = pid.startswith(("VCGC-", "SUP-")) if system == "VCGC" else pid.startswith(system.replace("-2", "") + "-")
        if not (own or mentions(text, system)):
            continue
        M["requirements"].append(_row(status=lamp_of(p.get("state", "")), id=pid, ssot_name=str(p.get("topic", "") or p.get("requirement", "")),
                                      version=str(p.get("requirement", "")), tools=str(p.get("owner", "")), system=system, source=hsrc, source_sha256=hsha,
                                      kind="HANDOFF_PENDING", scope=str(p.get("next", ""))[:160], completion_time=s["handoff"].get("at", "NOT_OBSERVED"),
                                      error_detail=str(p.get("reason", ""))))
    # tests = 進度帳(逐引擎實測)+ 交接證據收據
    gsrc, gsha = _src(via, s["progress_path"])
    for r in s["progress"]:
        if r.get("sys") != system:
            continue
        M["tests"].append(_row(status=r.get("run_lamp", "YELLOW"), id=f"RUN-{r.get('run_id', '')}", ssot_name=Path(str(r.get("entry", ""))).name,
                               version=str(r.get("entry_version", "")), tools=f"rc {r.get('run_rc')} · {r.get('run_secs')}s", system=system,
                               source=gsrc, source_sha256=gsha, kind="SELFTEST_RUN", scope=f"憲法 {r.get('constitution')} · 衝突 {r.get('conflicts_open')}",
                               completion_time=str(r.get("ts", "")), error_detail="" if r.get("run_lamp") == "GREEN" else f"run_lamp {r.get('run_lamp')}"))
    for rel, d in s["evidence"]:
        case = str(d.get("case", ""))
        cmd = str(d.get("command", ""))
        if system == "VCGC":
            hit = not any(mentions(case + cmd, o) for o in SYSTEMS if o != "VCGC")
        else:
            hit = mentions(case + cmd, system)
        if not hit:
            continue
        rc = str(d.get("rc", ""))
        M["tests"].append(_row(status="GREEN" if rc == "0" else ("RED" if rc else "YELLOW"), id=f"CASE-{case}", ssot_name=case,
                               version=str(d.get("case_sha256", ""))[:12], tools=cmd[:120], system=system, source=str(rel), source_sha256=sha256_file(via / rel),
                               kind="HANDOFF_RECEIPT", scope=str(d.get("scope", ""))[:160], completion_time=str(d.get("completed_at", "")),
                               error_detail="" if rc == "0" else f"rc {rc} · log {d.get('log', '')}"))
    return M


def shared_rows(via: Path, s: dict) -> list:
    con, hand = s["constitution"], s["handoff"]
    csrc, csha = _src(via, s["constitution_path"])
    hsrc, hsha = _src(via, s["handoff_path"])
    rows = [
        _row(status=con.get("lamp", "YELLOW"), id="SHARED-CONSTITUTION", ssot_name="五系統憲法矩陣總燈", version=str(con.get("engine", "")),
             tools=json.dumps(con.get("counts", {}), ensure_ascii=False), system="VIA_SHARED", source=csrc, source_sha256=csha, kind="SHARED",
             scope="L125", completion_time=con.get("generated_utc", "NOT_OBSERVED"), error_detail="" if con.get("lamp") == "GREEN" else "憲法性 0 / 衝突 OPEN(見各系統 conflicts)"),
        _row(status=(con.get("governor") or {}).get("lamp", "YELLOW"), id="SHARED-GOVERNOR", ssot_name="L122 治理器 dry-run",
             version=str((con.get("governor") or {}).get("engine", "")), tools=json.dumps((con.get("governor") or {}).get("summary", {}), ensure_ascii=False)[:300],
             system="VIA_SHARED", source=csrc, source_sha256=csha, kind="SHARED", scope="只讀 · 不發號", error_detail=""),
        _row(status=hand.get("lamp", "YELLOW"), id="SHARED-HANDOFF", ssot_name="交接冊完整性燈(≠ 驗收)", version=str(hand.get("engine", "")),
             tools=f"closeout_lamp {hand.get('closeout_lamp')} · pending {(hand.get('summary') or {}).get('pending')}", system="VIA_SHARED",
             source=hsrc, source_sha256=hsha, kind="SHARED", scope=str(hand.get("meaning", "")), completion_time=hand.get("at", "NOT_OBSERVED"),
             error_detail="" if hand.get("closeout_lamp") == "GREEN" else f"closeout_lamp {hand.get('closeout_lamp')}:handoff 綠 ≠ 驗收"),
    ]
    vrn1 = next((r for r in con.get("systems", []) if r.get("sys") == "VRN-1"), None)
    if vrn1:
        rows.append(_row(status="YELLOW", id="SHARED-VRN-1", ssot_name="VRN-1(外倉 · 只讀)", system="VIA_SHARED", source=csrc, source_sha256=csha,
                         kind="EXTERNAL", scope="tonykuni/VIA-VDF-VRN", error_detail=str(vrn1.get("note", ""))))
    return rows


# ---------- 生成 ----------
def envelope(bundle: dict) -> dict:
    raw = json.dumps(bundle, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(raw, mtime=0)
    return {"encoding": "gzip+base64", "raw_bytes": len(raw), "raw_sha256": sha256_bytes(raw), "gzip_bytes": len(gz),
            "gzip_sha256": sha256_bytes(gz), "base64": base64.b64encode(gz).decode("ascii")}


def csp_for(script_text: str) -> str:
    digest = base64.b64encode(hashlib.sha256(script_text.encode("utf-8")).digest()).decode("ascii")
    return (f"default-src 'none'; script-src 'sha256-{digest}'; style-src 'unsafe-inline'; img-src data:; "
            "connect-src 'none'; base-uri 'none'; form-action 'none'")


def render_page(site: Path, system: str, bundle: dict, hub_href: str) -> str:
    tpl = (site / LOCK_FILES["html"]).read_text(encoding="utf-8")
    css = (site / LOCK_FILES["css"]).read_text(encoding="utf-8")
    js = (site / LOCK_FILES["js"]).read_text(encoding="utf-8").replace("__SYSTEM__", system)
    logo = base64.b64encode((site / LOCK_FILES["logo"]).read_bytes()).decode("ascii")
    page = tpl.replace("__CSP__", csp_for(js)).replace("__CSS__", css).replace("__BRAND_LOGO__", logo)
    page = page.replace("__PAYLOAD__", json.dumps(envelope(bundle), separators=(",", ":"))).replace("__JS__", js)
    page = page.replace("__SYSTEM__", system)
    # 只換連結目標與自報標籤,不動樣式 / 結構(鎖的是 css token 區塊 + 結構 id)
    page = page.replace('href="subsystems-v0106.4.html"', f'href="{hub_href}"')
    page = page.replace('href="governance-preview-v0105.3.html"', 'href="VIA_WorkbenchLock_check_latest.json"')
    page = page.replace("Global/common governance · existing read-only route", "本倉 check 收據(json)")
    page = page.replace("v0106.4 CANDIDATE</span>", f"本倉自建 · {ENGINE}</span>")
    page = page.replace("ACTUAL · RED / BLOCKED</span>", f"五系統總燈 · {bundle.get('source', {}).get('constitution_lamp', 'NOT_OBSERVED')}</span>")
    page = page.replace("VIA · ARCHITECTURE BASELINE · 2026-11-05 · ENGINE v0103",
                        f"VIA · 自建工作台 · {bundle.get('source', {}).get('generated_utc', '')[:10]} · {ENGINE}")
    page = page.replace("v0106.4 CANDIDATE · original snapshot", f"{ENGINE} · 本倉冊快照 · main {bundle.get('source', {}).get('main', '')}")
    page = page.replace("GitHub health 由 parent 外部提供；此頁只標示原始 snapshot provenance。", "資料全部來自本倉自己的冊(來源與 SHA 在 Inspector);未跑的站是黃,不是綠。")
    return page


def render_hub(site: Path, pages: dict, s: dict, info: dict) -> str:
    css = (site / LOCK_FILES["css"]).read_text(encoding="utf-8")
    logo = base64.b64encode((site / LOCK_FILES["logo"]).read_bytes()).decode("ascii")
    con = s["constitution"]
    e = _html.escape
    cards = ""
    rows = ""
    for sysname in SYSTEMS:
        M = pages[sysname]["bundle"]["LAST_MATRIX"]
        n = sum(len(v) for v in M.values())
        red = sum(1 for v in M.values() for r in v if r["status"] == "RED")
        green = sum(1 for v in M.values() for r in v if r["status"] == "GREEN")
        crow = next((r for r in con.get("systems", []) if r.get("sys") == sysname), {}) or {}
        lamp = crow.get("lamp", "YELLOW")
        fn = PAGE_NAME.format(sys=sysname)
        cards += (f'<div class="kpi"><span class="icon"></span><strong>{e(sysname)}</strong>'
                  f'<span>{n} rows · RED {red} · GREEN {green}</span></div>')
        rows += (f'<tr class="matrix-row"><td><div class="status-cell"><span class="status-dot {lamp.lower()}" aria-label="{lamp}"></span>'
                 f'<span class="status-label">{lamp}</span></div></td><td class="code">{e(crow.get("number") or "NOT_ASSIGNED")}</td>'
                 f'<td>{e(sysname)}</td><td class="code">{e(crow.get("entry_version") or "")}</td><td>{e(str(crow.get("constitution", "")))}</td>'
                 f'<td>{n}</td><td>{red}</td><td>{green}</td><td><a href="{fn}">{fn}</a></td></tr>')
    vrn1 = next((r for r in con.get("systems", []) if r.get("sys") == "VRN-1"), None)
    if vrn1:
        rows += ('<tr class="matrix-row"><td><div class="status-cell"><span class="status-dot yellow" aria-label="GRAY"></span>'
                 '<span class="status-label">GRAY</span></div></td><td class="code">—</td><td>VRN-1</td><td></td><td>外倉只讀(L123)</td>'
                 f'<td>0</td><td>0</td><td>0</td><td>{e(str(vrn1.get("note", "")))}</td></tr>')
    lock = info["lock_site"]
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'">
<title>VIA Workbench Hub · {ENGINE}</title><style>{css}</style></head>
<body>
<header id="masthead"><div class="brand"><img class="brand-logo" src="data:image/png;base64,{logo}" alt="Veritas Intelligence Analytics">
<div class="brand-copy"><p class="eyebrow">VIA · 自建工作台 HUB · {e(info['generated_utc'][:10])} · {ENGINE}</p>
<h1>VIA 五系統自建工作台</h1><p class="subtitle">視覺鎖定正本 {e(LOCK_REL.name)} · token {info['token_count']} · 區塊 sha {e(info['token_block_sha256'][:12])}</p></div></div>
<div class="mast-actions"><span class="badge candidate">本倉真資料</span><span class="badge {'success' if lock['ok'] else 'danger'}">鎖站 {'4/4 OK' if lock['ok'] else 'RED'}</span>
<span class="badge lock">ENG049 v0102 VISUAL LOCK</span></div></header>
<div class="review-note" role="status">五系統對等獨立(L123):每頁一個系統,資料只來自該系統自己的冊與本倉收據;VRN-1 外倉只讀。未跑 ≠ 綠。</div>
<div class="workspace" id="workspace"><main class="center" style="grid-column:1/-1"><section class="kpis" id="kpis">{cards}</section>
<section class="center-panel"><div class="center-panel-head" id="center-panel-head"><h2>五系統總表 · 來自 VIA_FiveSystemConstitution_latest.json</h2><span class="micro">總燈 {e(str(con.get('lamp', 'NOT_OBSERVED')))}</span></div>
<div id="view" role="region"><div class="table-wrap"><table><thead><tr><th>燈號</th><th>編號</th><th>系統</th><th>入口版</th><th>憲法</th><th>rows</th><th>RED</th><th>GREEN</th><th>頁面</th></tr></thead><tbody>{rows}</tbody></table></div></div></section>
<footer class="center-footer">鎖定抽取自正本 css 的 :root 區塊;生成頁 check 必須含同一區塊(sha 相同)。審查包自己的燈與資料不在本工作台。</footer></main></div>
</body></html>
"""


def build(via: Path, out: Path, open_after: bool = False) -> dict:
    site = lock_site(via)
    info = kit(via, write=True)
    if not info["lock_site"]["ok"]:
        return {"lamp": "RED", "reason": "鎖站 sha 不過,不生成", "lock_site": info["lock_site"]}
    s = load_sources(via)
    out.mkdir(parents=True, exist_ok=True)
    main_sha = ""
    try:
        import subprocess
        main_sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(via), capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception as exc:
        WARNINGS.append(f"git rev-parse 不可用: {exc}")
    shared = shared_rows(via, s)
    pages = {}
    for sysname in SYSTEMS:
        M = rows_for(via, sysname, s)
        bundle = {"version": UI_CONTRACT_VERSION, "workbench_engine": ENGINE, "system": sysname, "LAST_MATRIX": M,
                  "SHARED_EVIDENCE": shared, "SHARED_CANDIDATE_OR_SESSION_OBSERVATIONS": {}, "DATABASE_HISTORICAL_GOVERNANCE": {},
                  "source": {"engine": ENGINE, "generated_utc": info["generated_utc"], "main": main_sha,
                             "constitution_lamp": s["constitution"].get("lamp", "NOT_OBSERVED"),
                             "books": {"constitution": str(s["constitution_path"]), "handoff": str(s["handoff_path"]),
                                       "laws": str(s["laws_path"]), "inventory": str(s["inventory_path"]), "progress": str(s["progress_path"]),
                                       "tool_lock": str(s["lock_path"])},
                             "lock_site": str(LOCK_REL), "token_block_sha256": info["token_block_sha256"]}}
        html_text = render_page(site, sysname, bundle, HUB_NAME)
        fn = out / PAGE_NAME.format(sys=sysname)
        fn.write_text(html_text, encoding="utf-8")
        pages[sysname] = {"file": str(fn), "bundle": bundle, "rows": {c: len(v) for c, v in M.items()}}
    hub = out / HUB_NAME
    hub.write_text(render_hub(site, pages, s, info), encoding="utf-8")
    res = {"lamp": "GREEN", "engine": ENGINE, "generated_utc": info["generated_utc"], "out": str(out), "hub": str(hub),
           "pages": {k: {"file": v["file"], "rows": v["rows"]} for k, v in pages.items()}}
    if open_after:
        try:
            if os.name == "nt":
                os.startfile(str(hub))  # type: ignore[attr-defined]
            else:
                import webbrowser
                webbrowser.open(hub.as_uri())
        except Exception as exc:
            WARNINGS.append(f"open 失敗: {exc}")
    res["warnings"] = list(WARNINGS)
    return res


# ---------- 閘 ----------
def check(via: Path, files: list[Path] | None = None, out: Path | None = None, write: bool = True) -> dict:
    site = lock_site(via)
    lock = verify_lock_site(via)
    css = (site / LOCK_FILES["css"]).read_text(encoding="utf-8") if (site / LOCK_FILES["css"]).exists() else ""
    tokens, block, block_sha = extract_tokens(css)
    if files is None:
        base = out or (via / "VIA_Reports" / "workbench")
        files = [base / PAGE_NAME.format(sys=x) for x in SYSTEMS] + [base / HUB_NAME]
    results = []
    for f in files:
        f = Path(f)
        r = {"file": str(f), "exists": f.exists(), "token_block": False, "ids_missing": [], "payload_identity": None, "lamp": "RED"}
        if f.exists():
            t = f.read_text(encoding="utf-8", errors="replace")
            r["token_block"] = block in t and bool(block)
            is_hub = f.name == HUB_NAME
            need = ["masthead", "kpis", "view"] if is_hub else REQUIRED_IDS
            ids = set(re.findall(r'id="([^"]+)"', t))
            r["ids_missing"] = [i for i in need if i not in ids]
            if not is_hub:
                m = re.search(r'<script id="payload" type="application/json">(.*?)</script>', t, re.S)
                try:
                    env = json.loads(m.group(1)) if m else {}
                    gz = base64.b64decode(env.get("base64", ""))
                    ok_gz = sha256_bytes(gz) == env.get("gzip_sha256")
                    raw = gzip.decompress(gz)
                    ok_raw = sha256_bytes(raw) == env.get("raw_sha256")
                    b = json.loads(raw)
                    r["payload_identity"] = bool(ok_gz and ok_raw and b.get("version") == UI_CONTRACT_VERSION and b.get("system") and b.get("LAST_MATRIX"))
                except Exception:
                    r["payload_identity"] = False
            ok = r["token_block"] and not r["ids_missing"] and (is_hub or r["payload_identity"])
            r["lamp"] = "GREEN" if ok else "RED"
        results.append(r)
    lamp = "GREEN" if lock["ok"] and results and all(x["lamp"] == "GREEN" for x in results) else "RED"
    res = {"engine": ENGINE, "checked_utc": utc_now(), "lock_site": lock, "token_block_sha256": block_sha, "token_count": len(tokens),
           "files": results, "lamp": lamp, "warnings": list(WARNINGS)}
    if write:
        CHECK_OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


# ---------- 自測 ----------
def selftest() -> int:
    via = resolve_via("")
    ok = 0
    total = 0

    def t(name, cond):
        nonlocal ok, total
        total += 1
        ok += bool(cond)
        print(f"  {'PASS' if cond else 'FAIL'} {name}")

    print(f"[{ENGINE} selftest]")
    lock = verify_lock_site(via)
    t("① 鎖站 SHA256SUMS 4/4", lock["ok"] and len(lock["files"]) == 4)
    toks, block, bsha = extract_tokens("x{} :root { --bg: #fff; --ink:#000 ; } .a{}")
    t("② 抽 token(2 個 · 區塊 sha 64 位)", toks == {"--bg": "#fff", "--ink": "#000"} and len(bsha) == 64)
    info = kit(via, write=False)
    t("③ kit:正本 token ≥ 18 · 必要 id 0 缺 · 三分頁", info["token_count"] >= 18 and not info["contract"]["required_ids_missing"]
      and info["contract"]["center_tabs"] == ["summary", "verification", "management"])
    t("④ 九分類與正本 js CATEGORY_ORDER 同集合(模板 select 順序不同是正本自己的)", info["contract"]["categories_match_js_order"] and len(info["contract"]["management_categories"]) == 9)
    env = envelope({"version": UI_CONTRACT_VERSION, "a": "中文"})
    raw = gzip.decompress(base64.b64decode(env["base64"]))
    t("⑤ 信封 gzip+base64+sha 往返", json.loads(raw)["a"] == "中文" and sha256_bytes(raw) == env["raw_sha256"])
    t("⑥ 燈號規則:OPEN→RED · VERIFIED→GREEN · PENDING→YELLOW · 空→YELLOW",
      lamp_of("OPEN") == "RED" and lamp_of("VERIFIED") == "GREEN" and lamp_of("PENDING") == "YELLOW" and lamp_of("") == "YELLOW")
    t("⑦ 系統辨識:VRN-2 不吃 VRN-1 · VQG 不吃 VAP", mentions("VRN-1 外倉", "VRN-2") is False and mentions("VRN-2 車道", "VRN-2") and not mentions("VAP v0300", "VQG"))
    t("⑧ CSP sha256 格式", re.match(r"^default-src 'none'; script-src 'sha256-[A-Za-z0-9+/=]{44}'", csp_for("alert(1)")) is not None)
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "wb"
        res = build(via, out)
        t("⑨ build 真資料:五頁 + hub · 每頁 systems 1 列", res["lamp"] == "GREEN" and all((out / PAGE_NAME.format(sys=x)).exists() for x in SYSTEMS)
          and (out / HUB_NAME).exists() and all(res["pages"][x]["rows"]["systems"] == 1 for x in SYSTEMS))
        chk = check(via, out=out, write=False)
        t("⑩ check 綠:token 區塊 + id + payload 身分", chk["lamp"] == "GREEN" and all(f["lamp"] == "GREEN" for f in chk["files"]))
        p = out / PAGE_NAME.format(sys="VCGC")
        p.write_text(p.read_text(encoding="utf-8").replace("--bg: #f2f1ec", "--bg: #ffffff"), encoding="utf-8")
        chk2 = check(via, out=out, write=False)
        t("⑪ 篡改 token → check 紅", chk2["lamp"] == "RED" and next(f for f in chk2["files"] if f["file"].endswith("VCGC_latest.html"))["token_block"] is False)
        q = out / PAGE_NAME.format(sys="VDF")
        q.write_text(q.read_text(encoding="utf-8").replace('id="inspector"', 'id="inspector-x"'), encoding="utf-8")
        chk3 = check(via, out=out, write=False)
        t("⑫ 刪結構 id → check 紅", "inspector" in next(f for f in chk3["files"] if f["file"].endswith("VDF_latest.html"))["ids_missing"])
        vcgc = res["pages"]["VCGC"]["rows"]
        t("⑬ VCGC 頁:policy 含 L125 · conflicts 列 = 憲法 OPEN 數", vcgc["policy"] >= 4 and vcgc["conflicts"] == len((load_sources(via)["constitution"].get("conflicts_open") or [])))
        hub_text = (out / HUB_NAME).read_text(encoding="utf-8")
        _, site_block, _ = extract_tokens((lock_site(via) / LOCK_FILES["css"]).read_text(encoding="utf-8"))
        t("⑭ hub 含五系統 + VRN-1 只讀列 + 正本 token 區塊", all(x in hub_text for x in SYSTEMS) and "VRN-1" in hub_text and site_block in hub_text)
    print(f"  == {ok}/{total}")
    return 0 if ok == total else 1


# ---------- CLI ----------
def resolve_via(root: str) -> Path:
    if root:
        return Path(root).resolve()
    for p in [HERE] + list(HERE.parents):
        if (p / "supportive modules").is_dir() and (p / "review").is_dir():
            return p
    return HERE.parents[2]


def make_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog=ENGINE, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verb", nargs="?", default="all", choices=["kit", "build", "check", "all"])
    ap.add_argument("--via", default="", help="VIA 根(預設自動找)")
    ap.add_argument("--out", default="", help="輸出夾(預設 <VIA>/VIA_Reports/workbench)")
    ap.add_argument("--open", action="store_true", help="build 後開 hub(Windows 用預設瀏覽器)")
    ap.add_argument("--files", nargs="*", help="check:要過閘的頁(不給就檢預設輸出夾)")
    ap.add_argument("--selftest", action="store_true")
    return ap


def main(argv=None) -> int:
    a = make_parser().parse_args(argv)
    if a.selftest:
        return selftest()
    via = resolve_via(a.via)
    out = Path(a.out).resolve() if a.out else via / "VIA_Reports" / "workbench"
    rc = 0
    if a.verb in ("kit", "all"):
        info = kit(via)
        print(f"[kit] {info['lamp']} · 鎖站 {'OK' if info['lock_site']['ok'] else info['lock_site']['problems']} · token {info['token_count']} · 區塊 sha {info['token_block_sha256'][:16]} → {KIT_OUT.name}")
        rc |= info["lamp"] != "GREEN"
    if a.verb in ("build", "all"):
        res = build(via, out, open_after=a.open)
        if res["lamp"] != "GREEN":
            print(f"[build] RED · {res.get('reason')}")
            return 1
        for k, v in res["pages"].items():
            print(f"[build] {k:5s} rows {sum(v['rows'].values()):4d} · " + " ".join(f"{c}:{n}" for c, n in v["rows"].items()))
        print(f"[build] hub → {res['hub']}")
    if a.verb in ("check", "all"):
        chk = check(via, files=[Path(f) for f in a.files] if a.files else None, out=out)
        for f in chk["files"]:
            print(f"[check] {f['lamp']:5s} {Path(f['file']).name} · token {f['token_block']} · 缺 id {f['ids_missing']} · payload {f['payload_identity']}")
        print(f"[check] {chk['lamp']} · 鎖站 {'OK' if chk['lock_site']['ok'] else chk['lock_site']['problems']} → {CHECK_OUT.name}")
        rc |= chk["lamp"] != "GREEN"
    return int(rc)


if __name__ == "__main__":
    sys.exit(main())
