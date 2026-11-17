#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL282_LocalMonitor v0100 — VCGC 現況矩陣(唯讀彙總;操作員 2026-11-17「INTEGRATE INTO VCGC AND REGISTER · 要導入加速器 · 授權自選增強工具」)。

只讀倉裡既有的冊與收據,彙成一張靜態 HTML + 貼回包 + 自報收據;不跑他系統、不改任何冊。
  run        系統 · 省 Token 與協助工具 · 輸入輸出參數 · 模組引擎 · 收據新鮮度 → LOCALMONITOR_latest.html / .json / 貼回包 / 只增帳
  selftest   暫存夾假倉 · 燈規則 · 不碰真倉(--selftest 同義)
  version    檔名 · 版號
旗標  --root <倉根>  --out <輸出夾,預設 VIA_Reports/vcgc>  --probe(另跑一次 token 動詞;唯一會執行倉內程式的選項,預設關)
邊界  只寫自己的收據夾 · 不改冊 / 號 / 他系統檔 · 不發號 · 不裝套件 · 不連網 · 不載 TA-Lib · 沒有示範資料(冊不在的區塊照實亮灰)
加速  [VIA:ACCEL-BRIDGE] 掛 VIA_SuperAccel_Module:accel_map 平行算 sha;缺席退回序跑。增強庫(可選,缺了走標準庫):orjson · psutil
燈    綠 = 有冊或收據佐證且未過期 · 黃 = 未達 / 過期 / 尾版未註冊 · 紅 = 衝突 / 檔不在 / 鎖不符 / 自報紅 · 灰 = 沒證據 / 退役 / 只知道檔在
rc    0 綠 · 2 黃 · 1 紅 · 3 找不到倉(VIA_SystemManager_Standard 的 rc 慣例)
呼叫  VIA_FROM_VCGC=YES python3 CGC_MDL149_…_vNNNN.py run CGC_MDL282_LocalMonitor run
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

import datetime as _dt
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ENGINE = "CGC_MDL282_LocalMonitor_v0100"
SKIP_DIRS = (".git", "__pycache__", "node_modules", "VIA_Reports", ".venv", "venv")
STALE_H = 48
VER_RX = re.compile(r"[-_]v(\d{4})(?=\.[A-Za-z0-9]+$)")
LN = {"g": "綠", "y": "黃", "r": "紅", "x": "灰"}
SEV = {"r": 0, "y": 1, "g": 2, "x": 3}


try:  # 增強庫(可選):有就用,沒有走標準庫
    import orjson as _orjson
except Exception:
    _orjson = None
try:
    import psutil as _psutil
except Exception:
    _psutil = None


def accel_status() -> str:
    """覆蓋率以生效計:標記在 + 執行時載得到才算。"""
    if VIA_ACCEL is None:
        return "沒掛到(走標準庫)"
    return "已掛 · accel_map " + ("可用" if hasattr(VIA_ACCEL, "accel_map") else "不在")


def pmap(fn, items):
    """平行 map(加速器 accel_map;缺席或出錯退回序跑)。回結果清單,保序。"""
    items = list(items)
    if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "accel_map") and len(items) > 1:
        try:
            out = VIA_ACCEL.accel_map(fn, items)
            if len(out) == len(items) and all(ok for ok, _ in out):
                return [r for _, r in out]
        except Exception as e:
            print("[pmap] 加速器平行失敗(%s)→ 序跑" % type(e).__name__, flush=True)
    return [fn(x) for x in items]


def now_utc() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def parse_t(s):
    m = re.match(r"(\d{4})-(\d\d)-(\d\d)[ T](\d\d):(\d\d)", str(s or ""))
    if not m:
        return None
    try:
        return _dt.datetime(*[int(x) for x in m.groups()], tzinfo=_dt.timezone.utc)
    except ValueError:
        return None


def fmt_t(s) -> str:
    d = parse_t(s)
    return d.strftime("%Y-%m-%d %H:%MZ") if d else (str(s) if s else "—")


def age_h(s):
    d = parse_t(s)
    return None if d is None else (now_utc() - d).total_seconds() / 3600.0


def worst(lamps) -> str:
    ls = [x for x in lamps if x in SEV and x != "x"]
    return min(ls, key=lambda x: SEV[x]) if ls else "x"


def norm_lamp(v) -> str:
    s = str(v or "").upper()
    if re.match(r"(GREEN|PASS|OK|GO$|VERIFIED|FREEZE_OK)", s):
        return "g"
    if re.match(r"(YELLOW|WARN|STALE|HOLD|REVIEW|PARTIAL|NODATA)", s):
        return "y"
    if re.match(r"(RED|FAIL|NO-GO|NOGO|BLOCK|ERROR|CONFLICT)", s):
        return "r"
    return "x"


def fam_of(p: str):
    m = VER_RX.search(p)
    return VER_RX.sub("", p), (int(m.group(1)) if m else None)


def load_json(p: Path):
    try:
        raw = p.read_bytes()
        if raw[:3] == b"\xef\xbb\xbf":
            raw = raw[3:]
        return _orjson.loads(raw) if _orjson is not None else json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def tail_file(folder: Path, stem: str, ext: str = ".py"):
    best, bv = None, -1
    if folder.is_dir():
        for p in folder.glob(stem + "*v[0-9][0-9][0-9][0-9]" + ext):
            m = VER_RX.search(p.name)
            if m and re.sub(r"[-_]v\d{4}" + re.escape(ext) + "$", "", p.name) == stem and int(m.group(1)) > bv:
                best, bv = p, int(m.group(1))
    return best, bv


def find_root(arg: str):
    cands = []
    if arg:
        cands.append(Path(arg))
    else:
        here = Path(__file__).resolve()
        for up in here.parents:  # 住在倉裡:往上找到 VIA 夾就是它
            if (up / "supportive modules" / "registry").is_dir():
                cands.append(up)
                break
    if os.environ.get("VIA_ROOT"):
        cands.append(Path(os.environ["VIA_ROOT"]))
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    for rel in ("OneDrive/Documents/movies-dataset", "movies-dataset", "Documents/movies-dataset", "Downloads/movies-dataset",
                "Github/movies-dataset", "OneDrive/Documents/VeritasIntelligenceAnalytics"):
        cands.append(home / rel)
    cands += [Path("C:/VeritasIntelligenceAnalytics"), Path.cwd()]
    found = []
    for c in cands:
        for via in (c / "VeritasIntelligenceAnalytics", c):
            if (via / "supportive modules" / "registry").is_dir() and via not in found:
                found.append(via)
                break
    return found


def scan_tails(via: Path):
    skip = set(SKIP_DIRS)
    tails, n = {}, 0
    for dp, dns, fns in os.walk(via):
        dns[:] = [d for d in dns if d not in skip and not d.startswith(".")]
        for fn in fns:
            if not fn.endswith((".py", ".ps1")):
                continue
            n += 1
            rel = os.path.relpath(os.path.join(dp, fn), via).replace("\\", "/")
            f, v = fam_of(rel)
            if v is not None and v > tails.get(f, -1):
                tails[f] = v
    return tails, n


# ---------------------------------------------------------------- 區塊
SYSTEMS = [("VCGC", "supportive modules/registry", "CGC_MDL149_VeritasCentralGovernanceConsole"),
           ("VDF", "functional modules/VDF", "VDF_SystemManager"),
           ("VRN-2", "functional modules/VRN", "VRN_SystemManager"),
           ("VQG", "functional modules/VQG", "VQG_AllInOne"),
           ("VAP", "functional modules/VAP", "VAP_SystemManager")]


def sec_systems(via: Path):
    rec = load_json(via / "docs/handoff/ai/VIA_FiveSystemConstitution_latest.json") or {}
    rts = next((rec.get(k) for k in ("generated_utc", "generated_at", "ts", "at", "utc", "time") if rec.get(k)), None)
    by = {str(r.get("sys")): r for r in rec.get("systems", []) if isinstance(r, dict)}
    rows = []
    for name, d, stem in SYSTEMS:
        p, v = tail_file(via / d, stem)
        r = by.get(name) or {}
        run, con = r.get("run") or {}, r.get("constitution") or {}
        rl, cl = norm_lamp(run.get("lamp")), norm_lamp(con.get("lamp"))
        notes = []
        if p is None:
            lamp, tail = "x", "—"
            notes.append("入口檔不在")
        else:
            tail = "v%04d" % v
            if not r:
                notes.append("沒有五系統憲法輪的收據")
            else:
                rv = str(r.get("entry_version") or "")
                if rv and rv != tail:
                    notes.append("收據是 %s 的,入口尾版已是 %s" % (rv, tail))
                    rl = "y" if rl == "g" else rl
                a = age_h(rts)
                if a is not None and a > STALE_H:
                    notes.append("收據已 %d 小時" % a)
                    rl = "y" if rl == "g" else rl
            lamp = worst([rl, cl])
        rows.append({"lamp": lamp, "sys": name, "tail": tail, "number": r.get("number") or "—",
                     "run": rl, "run_txt": ("rc %s" % run.get("rc")) if run else "沒有收據",
                     "con": cl, "con_txt": str(con.get("status") or "沒有收據") + ((" · " + "、".join(str(c.get("id")) for c in r.get("conflicts", []) if isinstance(c, dict))) if r.get("conflicts") else ""),
                     "at": fmt_t(rts), "note": ";".join(notes)})
    return rows


ROLE = {"token": "省 Token · 全景代讀(read / slice / digest / pack)", "nlp": "省 Token · NLP 摘要", "accelerator": "協助 · 加速器",
        "network": "協助 · 網路工具", "layout": "協助 · 版面", "frame": "協助 · Polars 框", "praddle": "協助 · 擷取", "pdfplumber": "協助 · PDF", "ocr": "協助 · OCR"}
EXTRA = [("協助 · 加速器橋(PY)", "supportive modules", "VIA_SuperAccel_Module.py"), ("協助 · 加速器橋(PS)", "supportive modules", "VIA_PS_Accel_Module.ps1"),
         ("協助 · PS7 範本", "supportive modules/ps7", "VeritasCeleritas.PS7.Template.ps1"), ("協助 · 工具看板", "docs/handoff/ai", "VIA_VCGCToolBoard"),
         ("協助 · 五系統互監", "docs/handoff/ai", "VIA_MutualMonitor"), ("協助 · 每日備份", "docs/handoff/ai", "VIA_DailyBackup"),
         ("協助 · 環境管理", "supportive modules/registry", "CGC_MDL240_EnvManager"), ("協助 · 環境治理", "supportive modules/registry", "CGC_MDL135_EnvGovernance"),
         ("協助 · SSOT 全景", "supportive modules/registry", "CGC_MDL247_SSOTPanorama"), ("協助 · 同義字聯集", "supportive modules/registry", "CGC_MDL176_SynonymUnion"),
         ("協助 · 編號", "supportive modules/registry", "CGC_MDL237_NumberingSystem"), ("協助 · 交接 / SDD", "supportive modules/registry", "CGC_MDL245_SDDValidator")]


def sec_tools(via: Path, tails: dict, probe: bool):
    rows = []
    reg = via / "supportive modules/registry"
    lockp, _ = tail_file(reg, "VIA_ToolVersion_Lock", ".json")
    lock = load_json(lockp) if lockp else None
    if not lock:
        rows.append({"lamp": "x", "tool": "工具鎖冊", "role": "—", "ver": "—", "state": "VIA_ToolVersion_Lock 不在,整區沒有證據", "at": "—"})
    else:
        root = via.parent
        ents = [(k, e) for k, e in lock.items() if isinstance(e, dict) and e.get("path")]
        shas = dict(zip([k for k, _ in ents], pmap(lambda ke: sha256_of(root / ke[1]["path"]) if (root / ke[1]["path"]).exists() else "", ents)))
        for key, e in ents:
            p = root / e["path"]
            st, lamp = [], "g"
            if not p.exists():
                lamp = "r"
                st.append("鎖冊指的檔不在")
            else:
                if e.get("sha256"):
                    if shas.get(key) == e["sha256"]:
                        st.append("sha 與鎖冊相符")
                    else:
                        lamp = "r"
                        st.append("sha 與鎖冊不符(鎖後被改)")
                else:
                    lamp = "y"
                    st.append("鎖冊沒記 sha")
                rel = os.path.relpath(p, via).replace("\\", "/")
                f, v = fam_of(rel)
                if v is not None and tails.get(f, v) > v:
                    lamp = "y" if lamp == "g" else lamp
                    st.append("有更新的 v%04d 還沒啟用" % tails[f])
            rows.append({"lamp": lamp, "tool": key + " · " + Path(e["path"]).name, "role": ROLE.get(key, "協助 · " + key), "ver": str(e.get("version") or "—"),
                         "state": " · ".join(st), "at": fmt_t(e.get("activated_at"))})
        for rp in lock.get("removed") or []:
            if (via / rp).exists():
                rows.append({"lamp": "y", "tool": Path(rp).name, "role": "鎖冊標移除", "ver": "—", "state": "鎖冊列為移除,檔還在(是刻意保留還是漏移,待確認):" + rp, "at": "—"})
    for role, d, stem in EXTRA:
        if stem.endswith((".py", ".ps1")):
            ok, ver = (via / d / stem).exists(), "—"
        else:
            p, v = tail_file(via / d, stem)
            ok, ver = p is not None, ("v%04d" % v if p else "—")
        rows.append({"lamp": "x", "tool": stem, "role": role, "ver": ver, "state": "檔在 · 沒有實測收據" if ok else "檔不在", "at": "—"})
    rows.append({"lamp": "x", "tool": "orjson", "role": "增強庫(可選)· JSON", "ver": getattr(_orjson, "__version__", "—") if _orjson else "—", "state": "已載入,冊與收據用它讀" if _orjson else "沒裝 · 走標準庫 json", "at": "—"})
    if _psutil:
        try:
            vm = _psutil.virtual_memory()
            free = vm.available / 2 ** 30
            rows.append({"lamp": "y" if free < 2 else "x", "tool": "psutil", "role": "增強庫(可選)· 本機資源", "ver": getattr(_psutil, "__version__", "—"),
                         "state": "可用 RAM %.1f GB / %.1f GB · CPU %d 核%s" % (free, vm.total / 2 ** 30, _psutil.cpu_count() or 0, " · 低 RAM" if free < 2 else ""), "at": "—"})
        except Exception as e:
            rows.append({"lamp": "x", "tool": "psutil", "role": "增強庫(可選)· 本機資源", "ver": "—", "state": "讀不到(%s)" % type(e).__name__, "at": "—"})
    else:
        rows.append({"lamp": "x", "tool": "psutil", "role": "增強庫(可選)· 本機資源", "ver": "—", "state": "沒裝 · 不報 RAM / CPU", "at": "—"})
    if probe:
        rows.append(probe_token(via))
    return rows


def probe_token(via: Path):
    p, v = tail_file(via / "supportive modules/registry", "CGC_MDL149_VeritasCentralGovernanceConsole")
    if p is None:
        return {"lamp": "x", "tool": "token 步實測", "role": "省 Token · 實測", "ver": "—", "state": "主控台不在", "at": "—"}
    env = dict(os.environ, VIA_FROM_VCGC="YES", PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run([sys.executable, str(p), "token"], cwd=str(via.parent), env=env, capture_output=True, timeout=240, stdin=subprocess.DEVNULL)
        out = (r.stdout or b"").decode("utf-8", "replace") + (r.stderr or b"").decode("utf-8", "replace")
        last = next((ln.strip() for ln in reversed(out.splitlines()) if "Token" in ln or "token" in ln), out.strip().splitlines()[-1] if out.strip() else "")
        lamp = {0: "g", 2: "y"}.get(r.returncode, "r")
        kind = " · 環境紅(讀檔 I/O)" if (lamp == "r" and re.search(r"I/O error|Errno 5|OSError", out)) else ""
        return {"lamp": lamp, "tool": "token 步實測 · " + p.name, "role": "省 Token · 實測", "ver": "v%04d" % v, "state": ("rc %d%s · %s" % (r.returncode, kind, last))[:260], "at": fmt_t(now_utc().isoformat())}
    except subprocess.TimeoutExpired:
        return {"lamp": "y", "tool": "token 步實測 · " + p.name, "role": "省 Token · 實測", "ver": "v%04d" % v, "state": "240 秒沒跑完(中斷,不算真紅)", "at": fmt_t(now_utc().isoformat())}


def _val(v) -> str:
    return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)


def sec_params(via: Path):
    rows = []

    def add(sysn, book, plist):
        for x in plist:
            miss = [lab for lab, k in (("號", "id"), ("版", "version"), ("註冊時間", "registered_at")) if not x.get(k)]
            why = str(x.get("why") or "")
            if miss:
                why = "缺 " + " · ".join(miss) + (";" + why if why else "")
            mut = x.get("mutable")
            rows.append({"lamp": "y" if miss else "g", "sys": sysn, "id": x.get("id") or "—", "cls": x.get("class") or "", "name": x.get("name") or "", "value": _val(x.get("value")),
                         "mut": "可動" if mut is True else ("不可動" if mut is False else "未標"), "ver": x.get("version") or "—", "at": fmt_t(x.get("registered_at")),
                         "book": x.get("book") or book, "why": why})

    vp, _ = tail_file(via / "functional modules/VDF", "VDF_ParamControl_SSOT", ".json")
    vdf = load_json(vp) if vp else None
    if vdf:
        add("VDF", vp.stem, vdf.get("params") or [])
        for cf in vdf.get("conflicts") or []:
            if str(cf.get("status", "")).upper().startswith("OPEN"):
                rows.append({"lamp": "r", "sys": "VDF", "id": cf.get("id") or "—", "cls": "參數衝突", "name": str(cf.get("what"))[:220], "value": "", "mut": "—", "ver": "—", "at": "—", "book": vp.stem, "why": str(cf.get("proposal") or "")[:220]})
    else:
        rows.append({"lamp": "x", "sys": "VDF", "id": "—", "cls": "—", "name": "VDF_ParamControl_SSOT 不在", "value": "", "mut": "—", "ver": "—", "at": "—", "book": "—", "why": "沒有參數列管冊"})
    rp, rv = tail_file(via / "functional modules/VRN", "VRN_ParamControl_SSOT", ".json")
    vrn = load_json(rp) if rp else None
    if vrn:
        plist, src = vrn.get("params"), rp.stem
        k = rv
        while not plist and k > 100:  # 前版鏈找 params(只增:新版沒抄就往前讀)
            k -= 1
            prev = load_json(rp.with_name("VRN_ParamControl_SSOT_v%04d.json" % k))
            if prev and prev.get("params"):
                plist, src = prev["params"], "VRN_ParamControl_SSOT_v%04d" % k
        add("VRN-2", src, plist or [])
        doc = vrn.get("run_params_doc") or {}
        for kk, vv in (vrn.get("run_params") or {}).items():
            rows.append({"lamp": "y", "sys": "VRN-2", "id": "—", "cls": "執行參數", "name": kk, "value": _val(vv), "mut": "可動", "ver": str(vrn.get("version") or "—") + "(冊版)", "at": fmt_t(vrn.get("ts")), "book": rp.stem, "why": "缺 號;" + str(doc.get(kk) or "")[:140]})
        for g in vrn.get("input_groups") or []:
            rows.append({"lamp": "g" if g.get("id") else "y", "sys": "VRN-2", "id": g.get("id") or "—", "cls": "輸入分群", "name": g.get("name") or g.get("key") or "", "value": _val(g.get("params")), "mut": "可動",
                         "ver": str(vrn.get("version") or "—") + "(冊版)", "at": fmt_t(vrn.get("ts")), "book": rp.stem, "why": "match " + _val(g.get("match"))[:120]})
    else:
        rows.append({"lamp": "x", "sys": "VRN-2", "id": "—", "cls": "—", "name": "VRN_ParamControl_SSOT 不在", "value": "", "mut": "—", "ver": "—", "at": "—", "book": "—", "why": "沒有參數列管冊"})
    cp, _ = tail_file(via / "supportive modules/registry", "VIA_Config_SSOT", ".json")
    cfg = load_json(cp) if cp else None
    vc, _ = tail_file(via / "supportive modules/registry", "VCGC_ParamControl_SSOT", ".json")
    vcb = load_json(vc) if vc else None
    if vcb:
        add("VCGC", vc.stem, vcb.get("params") or [])
    elif cfg:
        for grp, lab in (("program", "程式檔案夾"), ("db", "資料庫設定")):
            g = cfg.get(grp) or {}
            for kk, vv in g.items():
                if kk != "updated_at":
                    rows.append({"lamp": "y", "sys": "VCGC", "id": "—", "cls": lab, "name": grp + "." + kk, "value": _val(vv), "mut": "可動", "ver": str(cfg.get("version") or "—") + "(冊版)",
                                 "at": fmt_t(g.get("updated_at") or cfg.get("created_at")), "book": cp.stem, "why": "缺 號 · 逐項版 · 逐項註冊時間:VCGC 沒有參數列管冊,只有這本設定冊"})
    else:
        rows.append({"lamp": "x", "sys": "VCGC", "id": "—", "cls": "—", "name": "VCGC 沒有參數列管冊,設定冊也不在", "value": "", "mut": "—", "ver": "—", "at": "—", "book": "—", "why": ""})
    return rows


def sec_engines(via: Path, tails: dict):
    nb = via / "supportive modules/registry/VIA_NumberBooks"
    fams = {}
    for kind in ("MDL", "ENG"):
        p, _ = tail_file(nb, "VIA_NumberBook_" + kind, ".jsonl")
        if p is None:
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                try:
                    o = json.loads(ln)
                except Exception:
                    o = None
                if not isinstance(o, dict):
                    continue  # 壞列不算家族
                src = str(o.get("source") or "")
                f, v = fam_of(src)
                try:
                    bv = int(str(o.get("version", "")).lstrip("v"))
                except ValueError:
                    bv = v if v is not None else 0
                k = (o.get("sub") or "", o.get("kind") or kind, f)
                c = fams.get(k)
                if c is None:
                    fams[k] = {"n": 1, "o": o, "bv": bv}
                else:
                    c["n"] += 1
                    if (bv, str(o.get("numbered_at"))) > (c["bv"], str(c["o"].get("numbered_at"))):
                        c["o"], c["bv"] = o, bv
    data = []
    for (sub, kind, f), c in fams.items():
        o = c["o"]
        src = str(o.get("source") or "")
        lamp = norm_lamp(o.get("lamp"))
        parts = [{"g": "已註冊", "y": "註冊黃", "r": "註冊紅", "x": "註冊燈空"}[lamp]]
        note = str(o.get("note") or "").strip()
        if note:
            parts.append(note[:90])
        where = "檔在" if (via / src).exists() else "檔不在"
        if o.get("gone_since"):
            lamp, parts = "x", ["退役(自 %s)" % fmt_t(o.get("gone_since"))] + ([note[:90]] if note else [])
        elif where == "檔不在":
            lamp = "r"
            parts.append("號冊有列但檔不在,也沒標退役")
        elif tails.get(f, -1) > c["bv"]:
            lamp = "y" if lamp == "g" else lamp
            parts.append("檔案尾版 v%04d 未註冊" % tails[f])
        name = re.sub(r"\.(py|ps1)$", "", os.path.basename(f))
        data.append([lamp, sub, kind, o.get("code") or "", name, "v%04d" % c["bv"], c["n"], " · ".join(parts), fmt_t(o.get("numbered_at")), where])
    data.sort(key=lambda r: (r[1] not in ("VCGC", "VDF", "VRN"), r[1], SEV[r[0]], r[2], r[4]))
    return data


def sec_receipts(via: Path):
    rows, seen = [], 0
    bases = [(via / "VIA_Reports", 3), (via / "docs/handoff", 2)]
    for base, depth in bases:
        if not base.is_dir():
            continue
        bl = len(base.parts)
        for dp, dns, fns in os.walk(base):
            if len(Path(dp).parts) - bl >= depth:
                dns[:] = []
            for fn in fns:
                if "latest" not in fn.lower() or not fn.lower().endswith(".json"):
                    continue
                if fn.startswith("LOCALMONITOR_"):
                    continue  # 自己的收據不回讀(避免回饋)
                p = Path(dp) / fn
                seen += 1
                try:
                    size = p.stat().st_size
                except OSError:
                    size = None
                if size is None or size > 5_000_000:
                    continue
                d = load_json(p)
                if not isinstance(d, dict):
                    continue
                lk = next((k for k in ("closeout_lamp", "lamp", "verdict", "status") if isinstance(d.get(k), str) and len(d[k]) < 60), None)
                tk = next((k for k in ("generated_utc", "generated_at", "completed_at", "ts", "at", "updated_utc", "utc", "time") if parse_t(d.get(k))), None)
                lamp = norm_lamp(d.get(lk)) if lk else "x"
                st = [("%s = %s" % (lk, d.get(lk))) if lk else "收據裡沒有燈欄位"]
                if tk:
                    a = age_h(d[tk])
                    at = fmt_t(d[tk])
                    if a is not None and a > STALE_H:
                        st.append("已 %d 小時" % a)
                        lamp = "y" if lamp == "g" else lamp
                else:
                    at = "—"
                    st.append("收據裡沒有時間欄位")
                    lamp = "y" if lamp == "g" else lamp
                rows.append({"lamp": lamp, "file": os.path.relpath(p, via).replace("\\", "/"), "state": " · ".join(st), "at": at})
    rows.sort(key=lambda r: (SEV[r["lamp"]], r["file"]))
    return rows, seen


# ---------------------------------------------------------------- 輸出
CSS = """:root{--bg:#f5f4f0;--panel:#fff;--line:#dbd9d3;--hair:#eceae2;--txt:#1e1d1a;--dim:#6b6a66;--zebra:#f6f4ef;--chip:#faf9f6;--seal:#b5291a;--seal-bg:#f6e9e7;--g:#16a34a;--y:#f59e0b;--r:#dc2626;--x:#9ca3af;
--mono:"DM Mono","Noto Sans TC",Consolas,"Cascadia Mono",monospace;--sans:"DM Sans","Noto Sans TC","Microsoft JhengHei UI",system-ui,sans-serif;--serif:"Syne","DM Sans","Noto Sans TC",sans-serif;--fs:12px;--fn:10.5px}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:400 var(--fs)/1.5 var(--sans)}.wrap{max-width:1180px;margin:0 auto;padding:18px 14px 40px}
header{border-bottom:1px solid var(--line);padding-bottom:10px;margin-bottom:12px}.caps{font:400 var(--fn)/1.4 var(--mono);letter-spacing:.08em;color:var(--dim);text-transform:uppercase}
h1{font:700 20px/1.25 var(--serif);margin:4px 0 6px}h2{font:700 14.5px/1.3 var(--sans);margin:0 0 6px}.note{font-size:var(--fn);color:var(--dim)}.mono{font-family:var(--mono)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 10px 8px;margin:0 0 10px}
.verdict{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;background:var(--seal-bg);border:1px solid var(--line);border-left:4px solid var(--seal);border-radius:8px;padding:8px 10px;margin:0 0 10px}
.verdict b{font:700 14.5px/1.2 var(--sans);color:var(--seal)}.scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:var(--fs)}
th,td{border-bottom:1px solid var(--hair);padding:5px 6px;text-align:left;vertical-align:top;overflow-wrap:anywhere}
th{font:700 var(--fn)/1.3 var(--sans);color:var(--dim);background:var(--chip);border-bottom:1px solid var(--line);white-space:nowrap}
tbody tr:nth-child(even) td{background:var(--zebra)}td.l,th.l{width:44px;white-space:nowrap}td.k{white-space:nowrap;font-weight:700}
.lamp{display:inline-block;min-width:30px;padding:1px 7px;border-radius:999px;font:700 var(--fn)/1.5 var(--sans);color:#fff;text-align:center}
.g{background:var(--g)}.y{background:var(--y);color:#1e1d1a}.r{background:var(--r);animation:bl 2.4s ease-in-out infinite}.x{background:var(--x)}
@keyframes bl{0%,100%{opacity:1}50%{opacity:.35}}@media (prefers-reduced-motion:reduce){.r{animation:none}}
.nav{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 0}.nav a{font:500 var(--fn)/1 var(--mono);color:var(--txt);text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:5px 9px;background:var(--panel)}
.bar{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:end;margin:6px 0 8px}.bar label{display:flex;flex-direction:column;gap:2px;font:700 var(--fn)/1.2 var(--sans);color:var(--dim)}
.bar select,.bar input{font:400 var(--fs)/1.2 var(--sans);padding:5px 7px;border:1px solid var(--line);border-radius:6px;background:var(--panel);color:var(--txt);min-width:110px}.bar input{min-width:200px}
.box{max-height:560px;overflow:auto;border:1px solid var(--hair);border-radius:6px}.box thead th{position:sticky;top:0;z-index:1}
button{font:700 var(--fn)/1 var(--sans);padding:6px 10px;border:1px solid var(--txt);border-radius:6px;background:var(--txt);color:#fff;cursor:pointer;margin-top:6px}button[hidden]{display:none}
a:focus-visible,select:focus-visible,input:focus-visible,button:focus-visible{outline:2px solid var(--txt);outline-offset:1px}"""

JS = """(function(){var D=__DATA__,LN={g:'綠',y:'黃',r:'紅',x:'灰'},shown=200;
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
var fs=document.getElementById('fs'),fk=document.getElementById('fk'),fl=document.getElementById('fl'),fq=document.getElementById('fq'),eb=document.getElementById('eb'),fc=document.getElementById('fc'),more=document.getElementById('more');
function pick(){var s=fs.value,k=fk.value,l=fl.value,q=fq.value.trim().toLowerCase();return D.filter(function(r){return(!s||r[1]===s)&&(!k||r[2]===k)&&(!l||r[0]===l)&&(!q||(r[3]+' '+r[4]+' '+r[7]).toLowerCase().indexOf(q)>=0)})}
function draw(){var a=pick(),h='';for(var i=0;i<Math.min(a.length,shown);i++){var r=a[i];h+='<tr><td class="l"><span class="lamp '+r[0]+'">'+LN[r[0]]+'</span></td><td class="k">'+esc(r[1])+'</td><td>'+esc(r[2])+'</td><td class="mono">'+esc(r[3])+'</td><td class="mono">'+esc(r[4])+'</td><td class="mono">'+esc(r[5])+'</td><td>'+r[6]+'</td><td>'+esc(r[7])+'</td><td class="mono">'+esc(r[8])+'</td><td>'+esc(r[9])+'</td></tr>'}
eb.innerHTML=h||'<tr><td colspan="10" class="note">沒有符合的列</td></tr>';fc.textContent='符合 '+a.length+' 列 · 顯示 '+Math.min(a.length,shown);more.hidden=a.length<=shown}
[fs,fk,fl].forEach(function(e){e.addEventListener('change',function(){shown=200;draw()})});fq.addEventListener('input',function(){shown=200;draw()});more.addEventListener('click',function(){shown+=200;draw()});
var pf=document.getElementById('pf');if(pf)pf.addEventListener('change',function(){var v=pf.value;document.querySelectorAll('#pt tbody tr').forEach(function(tr){tr.hidden=!!v&&tr.getAttribute('data-s')!==v})});draw()})();"""


def E(s) -> str:
    return html.escape(str(s), quote=True)


def lamp(c) -> str:
    return '<span class="lamp %s">%s</span>' % (c, LN[c])


def cut(s, n=70) -> str:
    s = str(s)
    return E(s) if len(s) <= n else '<span title="%s">%s…</span>' % (E(s[:600]), E(s[:n]))


def count(rows, key="lamp"):
    c = {"g": 0, "y": 0, "r": 0, "x": 0}
    for r in rows:
        c[r[key] if isinstance(r, dict) else r[0]] += 1
    return c


def build(via: Path, out: Path, probe: bool, others: list):
    steps = ["定位", "掃檔", "系統", "工具", "參數", "引擎", "收據", "輸出"]

    def prog(i):
        print("[%d/%d] %-4s %3d%%" % (i + 1, len(steps), steps[i], int((i + 1) * 100 / len(steps))), flush=True)

    prog(0)
    accel = accel_status()
    git = "—"
    try:
        gb = subprocess.run(["git", "-C", str(via.parent), "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, timeout=20, stdin=subprocess.DEVNULL)
        gs = subprocess.run(["git", "-C", str(via.parent), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=20, stdin=subprocess.DEVNULL)
        if gb.returncode == 0 and gs.returncode == 0:
            git = gb.stdout.strip() + "@" + gs.stdout.strip()
    except Exception as e:
        git = "—(%s)" % type(e).__name__
    prog(1)
    tails, nfiles = scan_tails(via)
    prog(2)
    S = sec_systems(via)
    prog(3)
    T = sec_tools(via, tails, probe)
    prog(4)
    P = sec_params(via)
    prog(5)
    G = sec_engines(via, tails)
    prog(6)
    R, rseen = sec_receipts(via)
    prog(7)
    cs, ct, cp, cr = count(S), count(T), count(P), count(R)
    cg = {"g": 0, "y": 0, "r": 0, "x": 0}
    per = {}
    for r in G:
        cg[r[0]] += 1
        d = per.setdefault(r[1], {"fam": 0, "g": 0, "y": 0, "r": 0, "x": 0})
        d["fam"] += 1
        d[r[0]] += 1
    reasons = []
    if cs["r"]:
        reasons.append("系統紅 %d" % cs["r"])
    if ct["r"]:
        reasons.append("工具鎖紅 %d" % ct["r"])
    if cp["r"]:
        reasons.append("參數衝突 %d" % cp["r"])
    if cg["r"]:
        reasons.append("號冊有列但檔不在 %d" % cg["r"])
    if cr["r"]:
        reasons.append("收據自報紅 %d" % cr["r"])
    if reasons:
        verdict, vl = "NO-GO", "r"
    else:
        ys = [("系統黃 %d" % cs["y"]) if cs["y"] else "", ("工具黃 %d" % ct["y"]) if ct["y"] else "", ("參數缺號 %d" % cp["y"]) if cp["y"] else "", ("尾版未註冊 %d" % cg["y"]) if cg["y"] else "", ("收據過期 %d" % cr["y"]) if cr["y"] else ""]
        reasons = [y for y in ys if y]
        verdict, vl = ("HOLD", "y") if reasons else (("GO", "g") if cs["g"] else ("HOLD(沒有證據)", "x"))
    stamp = now_utc().strftime("%Y-%m-%d %H:%MZ")
    # ---- HTML
    srow = "".join('<tr><td class="l">%s</td><td class="k">%s</td><td class="mono">%s</td><td class="mono">%s</td><td>%s %s</td><td>%s %s</td><td class="mono">%s</td><td class="note">%s</td></tr>' % (
        lamp(r["lamp"]), E(r["sys"]), E(r["tail"]), E(r["number"]), lamp(r["run"]), E(r["run_txt"]), lamp(r["con"]), E(r["con_txt"]), E(r["at"]), E(r["note"])) for r in S)
    trow = "".join('<tr><td class="l">%s</td><td>%s</td><td class="mono">%s</td><td class="mono">%s</td><td>%s</td><td class="mono">%s</td></tr>' % (
        lamp(r["lamp"]), E(r["role"]), E(r["tool"]), E(r["ver"]), E(r["state"]), E(r["at"])) for r in sorted(T, key=lambda r: SEV[r["lamp"]]))
    prow = "".join('<tr data-s="%s"><td class="l">%s</td><td class="k">%s</td><td class="mono">%s</td><td>%s</td><td>%s</td><td class="mono">%s</td><td>%s</td><td class="mono">%s</td><td class="mono">%s</td><td class="note">%s</td><td class="note">%s</td></tr>' % (
        E(r["sys"]), lamp(r["lamp"]), E(r["sys"]), E(r["id"]), E(r["cls"]), cut(r["name"], 60), cut(r["value"], 60), E(r["mut"]), E(r["ver"]), E(r["at"]), E(r["book"]), cut(r["why"], 90)) for r in P)
    subs = sorted(per, key=lambda s: (s not in ("VCGC", "VDF", "VRN"), -per[s]["fam"]))
    erow = "".join("<tr><td class=\"k\">%s</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td></tr>" % (E(s), per[s]["fam"], per[s]["g"], per[s]["y"], per[s]["r"], per[s]["x"]) for s in subs)
    opts = "".join('<option value="%s">%s</option>' % (E(s), E(s)) for s in subs)
    rrow = "".join('<tr><td class="l">%s</td><td class="mono">%s</td><td>%s</td><td class="mono">%s</td></tr>' % (lamp(r["lamp"]), E(r["file"]), E(r["state"]), E(r["at"])) for r in R[:120])
    empty = '<tr><td colspan="12" class="note">這一區沒有可讀的冊或收據</td></tr>'
    page = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>VIA 現況矩陣 · VCGC LocalMonitor</title><style>%s</style></head><body><div class="wrap">
<header><div class="caps">Veritas Intelligence Analytics · VCGC 唯讀監控</div><h1>VIA 現況矩陣</h1>
<div class="note mono">%s · 倉 %s · git %s · 掃 %d 支 py / ps1 · 加速器橋 %s · %s</div>
<nav class="nav" aria-label="分區"><a href="#sys">① 系統</a><a href="#tool">② 省 Token 與協助工具</a><a href="#io">③ 輸入 / 輸出 / 參數 / 時間</a><a href="#eng">④ 模組 / 引擎</a><a href="#rec">⑤ 收據新鮮度</a></nav></header>
<div class="verdict">%s<b>%s</b><span>%s</span></div>
<div class="card" id="sys"><h2>① 系統</h2><div class="scroll"><table><thead><tr><th class="l">燈</th><th>系統</th><th>入口尾版</th><th>號</th><th>實跑(自報)</th><th>憲法性(引擎自報)</th><th>收據時間</th><th>狀態說明</th></tr></thead><tbody>%s</tbody></table></div>
<div class="note">來源:入口尾版取自磁碟;實跑與憲法性取自 docs/handoff/ai/VIA_FiveSystemConstitution_latest.json。收據超過 %d 小時或不是現在這版入口的,綠降成黃。</div></div>
<div class="card" id="tool"><h2>② 省 Token 工具與協助工具</h2><div class="scroll"><table><thead><tr><th class="l">燈</th><th>角色</th><th>工具</th><th>鎖版</th><th>狀態說明</th><th>啟用時間</th></tr></thead><tbody>%s</tbody></table></div>
<div class="note">綠 = 鎖冊 VIA_ToolVersion_Lock 的 sha 與磁碟上的檔相符。灰 = 只知道檔在,沒有實測收據(檔在不等於能用)。要實測省 Token 步,加 --probe。</div></div>
<div class="card" id="io"><h2>③ 輸入 / 輸出 / 參數 / 時間範圍</h2><div class="bar"><label>系統<select id="pf"><option value="">全部</option><option>VCGC</option><option>VDF</option><option>VRN-2</option></select></label></div>
<div class="box"><table id="pt"><thead><tr><th class="l">燈</th><th>系統</th><th>號</th><th>類</th><th>名稱</th><th>現值</th><th>可動</th><th>版</th><th>註冊時間</th><th>來源冊</th><th>狀態說明</th></tr></thead><tbody>%s</tbody></table></div>
<div class="note">燈只看號 · 版 · 註冊時間三樣齊不齊(齊 = 綠 · 缺 = 黃 · 參數衝突 OPEN = 紅),不代表值是對的。本頁只讀;要改參數請走該系統自己的管理器。</div></div>
<div class="card" id="eng"><h2>④ 模組 / 引擎(一個家族一列,取號冊裡最高版)</h2><div class="scroll"><table><thead><tr><th>系統</th><th>家族</th><th>綠</th><th>黃</th><th>紅</th><th>灰(退役)</th></tr></thead><tbody>%s</tbody></table></div>
<div class="bar"><label>系統<select id="fs"><option value="">全部</option>%s</select></label><label>類<select id="fk"><option value="">全部</option><option>MDL</option><option>ENG</option></select></label>
<label>燈<select id="fl"><option value="">全部</option><option value="r">紅</option><option value="y">黃</option><option value="g">綠</option><option value="x">灰</option></select></label>
<label>找(名稱 / 號 / 說明)<input id="fq" type="search" autocomplete="off"></label><span class="note" id="fc" role="status"></span></div>
<div class="box"><table><thead><tr><th class="l">燈</th><th>系統</th><th>類</th><th>編號</th><th>名稱</th><th>版本號</th><th>版數</th><th>狀態說明</th><th>註冊時間</th><th>落點</th></tr></thead><tbody id="eb"></tbody></table></div>
<button type="button" id="more" hidden>再顯示 200 列</button>
<div class="note">來源:VCGC 號冊 VIA_NumberBook_MDL / ENG。綠只代表註冊狀態,不等於測試通過。黃 = 檔案尾版比號冊新;紅 = 號冊有列但檔不在也沒標退役;灰 = 退役。</div></div>
<div class="card" id="rec"><h2>⑤ 收據新鮮度(*latest*.json,共讀到 %d 份)</h2><div class="box"><table><thead><tr><th class="l">燈</th><th>收據</th><th>狀態說明</th><th>收據時間</th></tr></thead><tbody>%s</tbody></table></div>
<div class="note">燈照收據自己寫的;沒有時間欄位或超過 %d 小時的綠降成黃;沒有燈欄位的是灰。最多列 120 份,紅黃在前。</div></div>
</div><script>%s</script></body></html>""" % (
        CSS, E(stamp), E(str(via.parent)), E(git), nfiles, E(accel), E(ENGINE), lamp(vl), E(verdict), E(" · ".join(reasons) or "沒有紅黃"),
        srow or empty, STALE_H, trow or empty, prow or empty, erow or empty, opts, rseen, rrow or empty, STALE_H,
        JS.replace("__DATA__", json.dumps(G, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")))
    # ---- 貼回包(≤ 60 行)
    L = ["# VIA 現況矩陣 貼回包 · %s · %s" % (stamp, ENGINE), "# 倉 %s · git %s · 加速器橋 %s%s" % (via.parent, git, accel, (" · 另有 %d 份倉沒有用" % len(others)) if others else ""),
         "[判定] %s — %s" % (verdict, " · ".join(reasons[:4]) or "沒有紅黃")]
    for r in S:
        L.append("[系統] %s %s %s · 實跑 %s %s · 憲法 %s %s%s" % (LN[r["lamp"]], r["sys"], r["tail"], LN[r["run"]], r["run_txt"], LN[r["con"]], r["con_txt"][:60], (" · " + r["note"]) if r["note"] else ""))
    three = "[三數] 程式檔 應掃 %d · 已掃 %d · 略過夾 %s 與隱藏夾;收據 應讀 %d · 已讀 %d · 略過 %d(過大或不是物件);號冊家族 %d" % (nfiles, nfiles, " ".join(SKIP_DIRS), rseen, len(R), rseen - len(R), len(G))
    L.insert(3, three)
    L.append("[工具] 綠 %d · 黃 %d · 紅 %d · 灰 %d" % (ct["g"], ct["y"], ct["r"], ct["x"]))
    L += ["[工具] %s %s · %s" % (LN[r["lamp"]], r["tool"], r["state"][:110]) for r in T if r["lamp"] in "ry"][:8]
    ps = {}
    for r in P:
        d = ps.setdefault(r["sys"], {"n": 0, "g": 0, "y": 0, "r": 0, "x": 0})
        d["n"] += 1
        d[r["lamp"]] += 1
    L += ["[參數] %s %d 列 · 綠 %d · 黃 %d · 紅 %d · 灰 %d" % (s, d["n"], d["g"], d["y"], d["r"], d["x"]) for s, d in ps.items()]
    L += ["[參數] 紅 %s %s · %s" % (r["sys"], r["id"], r["name"][:100]) for r in P if r["lamp"] == "r"][:4]
    L += ["[引擎] %s 家族 %d · 綠 %d · 黃 %d · 紅 %d · 灰 %d" % (s, per[s]["fam"], per[s]["g"], per[s]["y"], per[s]["r"], per[s]["x"]) for s in subs[:6]]
    L += ["[引擎] %s %s %s %s · %s" % (LN[r[0]], r[1], r[3], r[4], r[7][:80]) for r in G if r[0] in "ry" and r[1] in ("VCGC", "VDF", "VRN")][:12]
    L.append("[收據] 讀到 %d 份 · 綠 %d · 黃 %d · 紅 %d · 灰 %d" % (rseen, cr["g"], cr["y"], cr["r"], cr["x"]))
    L += ["[收據] 紅 %s · %s" % (r["file"], r["state"][:90]) for r in R if r["lamp"] == "r"][:8]
    nxt = "先處理紅:" + reasons[0] if vl == "r" else ("補黃:" + reasons[0] if vl == "y" else "沒有待辦")
    L = L[:59] + ["NEXT: " + nxt]
    out.mkdir(parents=True, exist_ok=True)
    (out / "LOCALMONITOR_latest.html").write_text(page, encoding="utf-8")
    (out / "LOCALMONITOR_PASTE_latest.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    summary = {"engine": ENGINE, "generated_utc": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"), "root": str(via.parent), "git": git, "lamp": {"r": "RED", "y": "YELLOW", "g": "GREEN", "x": "GRAY"}[vl], "verdict": verdict, "reasons": reasons,
               "counts": {"systems": cs, "tools": ct, "params": cp, "engines": cg, "receipts": cr}, "files_scanned": nfiles, "three_numbers": three, "accel": accel, "other_roots": [str(o) for o in others]}
    (out / "LOCALMONITOR_latest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(out / "local_monitor_ledger.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps({k: summary[k] for k in ("generated_utc", "engine", "root", "git", "lamp", "verdict", "counts")}, ensure_ascii=False) + "\n")
    print("===== PASTE BEGIN =====")
    print("\n".join(L))
    print("===== PASTE END =====")
    print("[U/I] " + str(out / "LOCALMONITOR_latest.html"))
    return {"r": 1, "y": 2}.get(vl, 0)


def selftest() -> int:
    ok = []

    def chk(name, cond, got=None):
        ok.append(bool(cond))
        print("  %s %s%s" % ("PASS" if cond else "FAIL", name, "" if cond else " → %r" % (got,)))

    with tempfile.TemporaryDirectory() as td:
        via = Path(td) / "repo" / "VeritasIntelligenceAnalytics"
        reg = via / "supportive modules/registry"
        (reg / "VIA_NumberBooks").mkdir(parents=True)
        (via / "functional modules/VDF").mkdir(parents=True)
        (reg / "CGC_MDL001_A_v0100.py").write_text("x=1\n", encoding="utf-8")
        (reg / "CGC_MDL001_A_v0101.py").write_text("x=2\n", encoding="utf-8")
        (reg / "CGC_MDL002_B_v0100.py").write_text("x=1\n", encoding="utf-8")
        tool = reg / "CGC_MDL158_T_v0100.py"
        tool.write_text("t=1\n", encoding="utf-8")
        rows = [{"code": "VIA-VCGC-MDL1", "sub": "VCGC", "kind": "MDL", "source": "supportive modules/registry/CGC_MDL001_A_v0100.py", "version": "v0100", "lamp": "GREEN", "numbered_at": "2026-11-01 00:00:00 +0000"},
                {"code": "VIA-VCGC-MDL2", "sub": "VCGC", "kind": "MDL", "source": "supportive modules/registry/CGC_MDL002_B_v0100.py", "version": "v0100", "lamp": "GREEN", "numbered_at": "2026-11-01 00:00:00 +0000"},
                {"code": "VIA-VCGC-MDL3", "sub": "VCGC", "kind": "MDL", "source": "supportive modules/registry/CGC_MDL003_C_v0100.py", "version": "v0100", "lamp": "GREEN", "numbered_at": "2026-11-01 00:00:00 +0000"},
                {"code": "VIA-VCGC-MDL4", "sub": "VCGC", "kind": "MDL", "source": "supportive modules/registry/CGC_MDL004_D_v0100.py", "version": "v0100", "lamp": "GREEN", "numbered_at": "2026-11-01 00:00:00 +0000", "gone_since": "2026-11-02 00:00:00 +0000"}]
        (reg / "VIA_NumberBooks/VIA_NumberBook_MDL_v0100.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps({"token": {"version": "v0100", "path": "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL158_T_v0100.py", "sha256": sha256_of(tool)},
                                                                         "nlp": {"version": "v0100", "path": "VeritasIntelligenceAnalytics/supportive modules/registry/NOPE_v0100.py", "sha256": "0" * 64}}), encoding="utf-8")
        (via / "functional modules/VDF/VDF_ParamControl_SSOT_v0100.json").write_text(json.dumps({"params": [{"name": "a", "id": "VDF-PAR-001", "version": "v0100", "registered_at": "2026-11-01T00:00:00Z", "mutable": False}, {"name": "b"}],
                                                                                              "conflicts": [{"id": "PC-001", "what": "w", "status": "OPEN"}]}), encoding="utf-8")
        tails, _ = scan_tails(via)
        G = {r[4]: r for r in sec_engines(via, tails)}
        chk("① 檔案尾版比號冊新 → 黃", G["CGC_MDL001_A"][0] == "y", G["CGC_MDL001_A"])
        chk("② 已註冊且檔在 → 綠", G["CGC_MDL002_B"][0] == "g")
        chk("③ 號冊有列但檔不在 → 紅", G["CGC_MDL003_C"][0] == "r")
        chk("④ 標退役 → 灰(不是紅)", G["CGC_MDL004_D"][0] == "x")
        T = {r["tool"].split(" · ")[0]: r for r in sec_tools(via, tails, False)}
        chk("⑤ 鎖冊 sha 相符 → 綠", T["token"]["lamp"] == "g", T["token"])
        chk("⑥ 鎖冊指的檔不在 → 紅", T["nlp"]["lamp"] == "r")
        tool.write_text("t=2\n", encoding="utf-8")
        chk("⑦ 鎖後被改 → 紅", {r["tool"].split(" · ")[0]: r for r in sec_tools(via, tails, False)}["token"]["lamp"] == "r")
        P = sec_params(via)
        chk("⑧ 參數三要素齊 綠 · 缺 黃 · 衝突 OPEN 紅", [r["lamp"] for r in P if r["sys"] == "VDF"] == ["g", "y", "r"], [r["lamp"] for r in P])
        chk("⑨ 冊不在的系統照實灰,不補示範列", [r["lamp"] for r in P if r["sys"] in ("VRN-2", "VCGC")] == ["x", "x"])
        S = sec_systems(via)
        chk("⑩ 沒有收據的系統不是綠", all(r["lamp"] != "g" for r in S))
        before = sorted(str(p.relative_to(via)) + ":" + sha256_of(p) for p in via.rglob("*") if p.is_file())
        rc = build(via, Path(td) / "out", False, [])
        after = sorted(str(p.relative_to(via)) + ":" + sha256_of(p) for p in via.rglob("*") if p.is_file())
        chk("⑪ 跑完倉內一個位元都沒變(唯讀)", before == after)
        chk("⑫ 有紅 → rc 1,輸出四個檔在倉外", rc == 1 and all((Path(td) / "out" / n).exists() for n in ("LOCALMONITOR_latest.html", "LOCALMONITOR_latest.json", "LOCALMONITOR_PASTE_latest.txt", "local_monitor_ledger.jsonl")), rc)
        paste = (Path(td) / "out/LOCALMONITOR_PASTE_latest.txt").read_text(encoding="utf-8").splitlines()
        chk("⑬ 貼回包 ≤ 60 行且末行 NEXT:", len(paste) <= 60 and paste[-1].startswith("NEXT:"), len(paste))
        chk("⑭ 貼回包帶三數(應掃 / 已掃 / 略過)", any(ln.startswith("[三數]") and "應掃" in ln and "已掃" in ln and "略過" in ln for ln in paste))
        chk("⑮ pmap 保序且等於序跑", pmap(lambda x: x * 2, [1, 2, 3, 4]) == [2, 4, 6, 8])
        rc2 = build(via, via / "VIA_Reports" / "vcgc", False, [])
        own = sorted(str(p.relative_to(via)).replace("\\", "/") for p in via.rglob("*") if p.is_file() and "VIA_Reports" in p.parts)
        chk("⑯ 預設落點只在 VIA_Reports/vcgc,且不回讀自己的收據", rc2 == 1 and all(o.startswith("VIA_Reports/vcgc/") for o in own) and not any("LOCALMONITOR" in r["file"] for r in sec_receipts(via)[0]), own)
    print("[selftest] %d/%d %s" % (sum(ok), len(ok), "PASS" if all(ok) else "FAIL"))
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    verb = a[0] if a and not a[0].startswith("-") else "run"

    def opt(name):
        return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else ""

    if verb == "selftest" or "--selftest" in a:
        return selftest()
    if verb == "version":
        print("%s · %s" % (Path(__file__).name, ENGINE))
        return 0
    if verb != "run":
        print(__doc__)
        return 0
    roots = find_root(opt("--root"))
    if not roots:
        print("[%s] 找不到 VIA 倉(找過 OneDrive\\Documents\\movies-dataset 等常見位置)。請加 --root <倉根>。" % ENGINE)
        return 3
    out = Path(opt("--out")) if opt("--out") else roots[0] / "VIA_Reports" / "vcgc"
    return build(roots[0], out, "--probe" in a, roots[1:])


if __name__ == "__main__":
    sys.exit(main())
