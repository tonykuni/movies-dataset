#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0197 — 薄尾(自查遺漏:易變參數(VIA_SPILL_DIR · rep)只登記名稱來源不登記值 → 登記冊內容沒變不出新版;隔離 / 傾倒 / _sha 字尾的舊腳本不掃 · 另計「待整理」· 不再點名 3624 支沒版號)(前版 v0196:版本號衝突只算有版號的冊 / 引擎(帳本 · 紀錄 · 輸出不算)· reconcile 動詞 = 不要同號出新版號(本機內容 → v+1 · 原號還原 main · 只增不減 · 先列計畫 --apply 才動)· p1loop 把退步區塊細節直接印進貼包)(前版 v0195:該註冊註冊 · 該編號編號 · 版本號寫版本號 · 每版規格存冊 · 自動建立;編號待 VCGC 核號無衝突才確認 · 本機先用 git 比對 main 抓同名不同內容的版本號衝突)(前版 v0194:退步細節追加 MD · 印 MD 路徑 · AI 讀 MD 不用截圖)(前版 v0193:實測實修迴圈 p1loop · 每輪跑 p1view → 綠燈檔案鎖定(只增不減 · 退步亮紅)· 與上一輪比較燈號 / 原因增減 · 輪次 append-only 帳本)(前版 v0192:摘要如實寫 PDF 份數 · 先切割再 pdfplumber 擷取 · 本文 / 資訊區分開 · 不亂碼 · 不能用馬上換)。
  p1view 動詞 → VRN_ENG397_P1Segment(輸入夾 = VRN 設定 input_dir · 預設 C:\\測試樣本報告)· p1view --one <檔名片段> 只看一份
  零替換(不動任何前版函式)。其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0197"


def _vnum_v0197(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0197(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0197(p) < _vnum_v0197(__file__)), key=_vnum_v0197)
PRIOR = _load_v0197(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


def _mod_v0197(tag: str):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if vars(mod).get("TAG") == tag:
            return mod
        mod = vars(mod).get("PRIOR")
    return PRIOR


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


_BOOK_RX = re.compile(r"(?i)synonym|regex|pattern|dict|lexicon|rules?|config|masterlist|book|ssot|roster|register(?!_v)|ledger|lock", re.I)


def _spec_of(p: Path) -> str:
    """每個版本的規格 = 檔案第一行說明(py docstring 第一行 / json 的 description · rule · schema)。"""
    try:
        if p.suffix == ".py":
            t = p.read_text(encoding="utf-8", errors="replace")
            m = re.search(r'"""\s*(.+?)\s*(?:\n|""")', t)
            return (m.group(1) if m else "")[:160]
        if p.suffix == ".json":
            d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            if isinstance(d, dict):
                return str(d.get("description") or d.get("rule") or d.get("schema") or d.get("title") or "")[:160]
    except Exception:  # noqa: BLE001
        return ""
    return ""


def _git_conflicts(home: Path) -> list:
    """本機先做一層衝突偵測:GitHub main 上同名的 VRN 檔 · 內容不同 = 版本號衝突(上次 v0151 / v0152 撞名就是這種)。沒有 git → 空清單(灰)。"""
    import subprocess
    try:
        top = subprocess.run(["git", "-C", str(home), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=20).stdout.strip()
        if not top:
            return []
        rel = str(home.resolve().relative_to(Path(top).resolve())).replace("\\", "/")
        out = subprocess.run(["git", "-C", top, "ls-tree", "-r", "origin/main", "--", rel], capture_output=True, text=True, timeout=60).stdout
        bad = []
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) != 2 or not parts[1].endswith((".py", ".json", ".ps1")):
                continue
            nm = Path(parts[1]).name
            if not re.search(r"_v\d{3,4}", nm) or re.search(r"(?i)ledger|manifest|evidence|audit|report|_latest|lock|register|progress|cache", nm):
                continue                                           # v0196:只算有版號的冊 / 引擎 · 帳本 / 紀錄 / 輸出不算
            sha = parts[0].split()[2]
            lp = Path(top) / parts[1]
            if lp.exists():
                mine = subprocess.run(["git", "-C", top, "hash-object", str(lp)], capture_output=True, text=True, timeout=20).stdout.strip()
                if mine and mine != sha:
                    bad.append(Path(parts[1]).name)
        return bad
    except Exception:  # noqa: BLE001
        return []


def asset_register(home: Path = None) -> dict:
    """資產登記冊(v0195):引擎(沿用 VRN-E · 暫編待 VCGC 確認)+ 冊 VRN-B + 參數 VRN-P + 每版規格(只增不減)· 核號請求 contract/VRN_NUMBER_REQUEST_latest.json · VCGC 核發 VCGC_NUMBER_GRANT_latest.json 後轉已確認。"""
    import datetime
    import hashlib
    home = Path(home or (_resolve("_home") or (lambda: HERE))())
    rd, cd = home / "registry", home / "contract"
    rd.mkdir(parents=True, exist_ok=True)
    cd.mkdir(parents=True, exist_ok=True)
    vn = lambda p: (lambda m: int(m.group(1)) if m else -1)(re.search(r"_v(\d{4})", Path(p).stem))  # noqa: E731
    hits = sorted(rd.glob("VRN_Asset_Register_v*.json"), key=vn)
    prev = {}
    if hits:
        try:
            prev = json.loads(hits[-1].read_text(encoding="utf-8"))
        except ValueError:
            prev = {}
    grant = {}
    for gp in (cd / "VCGC_NUMBER_GRANT_latest.json", home.parent.parent / "VCGC" / "contract" / "VCGC_NUMBER_GRANT_latest.json"):
        if gp.exists():
            try:
                grant.update(json.loads(gp.read_text(encoding="utf-8")).get("grants") or {})
            except ValueError:
                pass
    eng_hits = sorted(rd.glob("VRN_Engine_Register_v*.json"), key=vn)
    engines = {}
    if eng_hits:
        try:
            engines = json.loads(eng_hits[-1].read_text(encoding="utf-8")).get("engines") or {}
        except ValueError:
            engines = {}
    skip = re.compile(r"[\\/](?:_superseded|__pycache__|\.git|VIA_Reports|restore|restore_learned|_p1view_out|contract)[\\/]|_latest\.|Register_v\d|Ledger")   # 登記冊 / 帳本 / 契約 / latest 不是資產
    tidy_rx = re.compile(r"(?i)[\\/](?:_?quarantine|隔離|_dump|_raw|archive|_old|backup|_backup)[\\/]|_sha[0-9a-f]{6,}\.")   # v0197:隔離 / 傾倒 / _sha 字尾 = 待整理 · 不掃
    allf = [p for p in home.rglob("*") if p.is_file() and p.suffix in (".py", ".json") and not skip.search(str(p))]
    pending_tidy = sum(1 for p in allf if tidy_rx.search(str(p)))
    files = [p for p in allf if not tidy_rx.search(str(p))]
    sha8 = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()[:8]  # noqa: E731
    specs = dict((prev.get("specs") or {}))
    nover = []
    for p in files:
        m = re.search(r"^(.*)_v(\d{3,4})$", p.stem)
        fam = (m.group(1) if m else p.stem) + p.suffix
        ver = ("v" + m.group(2).zfill(4)) if m else "(無版號)"
        if not m and p.suffix == ".py" and not p.name.startswith("_"):
            nover.append(p.name)
        specs.setdefault(fam, {})
        if ver not in specs[fam]:
            specs[fam][ver] = {"spec": _spec_of(p), "sha8": sha8(p), "bytes": p.stat().st_size, "date": datetime.date.fromtimestamp(p.stat().st_mtime).isoformat()}
    books = dict(prev.get("books") or {})
    bused = [int(v["no"][6:10]) for v in books.values() if re.match(r"VRN-B-\d{4}", str(v.get("no", "")))]
    nb = max(bused, default=0) + 1
    for p in sorted(files):
        if p.suffix == ".json" and "registry" in p.parts and "Register" in p.name:
            continue
        if not (_BOOK_RX.search(p.stem) and ("SSOT" in p.parts or "knowledge" in p.parts or "registry" in p.parts or p.suffix == ".json" or _BOOK_RX.search(p.stem))):
            continue
        if "SystemManager" in p.name or "ENG3" in p.name:
            continue
        m = re.search(r"^(.*)_v(\d{3,4})$", p.stem)
        fam = (m.group(1) if m else p.stem) + p.suffix
        old = books.get(fam) or {}
        no = old.get("no")
        if not no:
            no = "VRN-B-%04d" % nb
            nb += 1
        books[fam] = {"no": no, "kind": "冊(SSOT / regex / 同義字 / 字典 / 規則 / 設定)", "tail": p.name, "version": ("v" + m.group(2).zfill(4)) if m else "(無版號)", "domain": str(p.parent.relative_to(home)) if p.parent != home else ".",
                      "sha8": sha8(p), "status": "已確認(VCGC)" if grant.get(fam) == no else "暫編 · 待 VCGC 核號", "first_seen": old.get("first_seen") or datetime.date.today().isoformat()}
    params = dict(prev.get("params") or {})
    pused = [int(v["no"][6:10]) for v in params.values() if re.match(r"VRN-P-\d{4}", str(v.get("no", "")))]
    npn = max(pused, default=0) + 1
    for k, getter in (("input_dir", lambda: str((_resolve("input_dir") or (lambda: ""))())), ("home", lambda: str(home)), ("rep", lambda: str((_resolve("_rep") or (lambda: ""))())),
                      ("VIA_ROOTS_BASE", lambda: os.environ.get("VIA_ROOTS_BASE", "")), ("VIA_DB_ROOT", lambda: os.environ.get("VIA_DB_ROOT", "")), ("VIA_VRN_SSOT_HOME", lambda: os.environ.get("VIA_VRN_SSOT_HOME", "")),
                      ("VIA_SPILL_DIR", lambda: os.environ.get("VIA_SPILL_DIR", ""))):
        try:
            val = getter()
        except Exception:  # noqa: BLE001
            val = ""
        old = params.get(k) or {}
        no = old.get("no") or ("VRN-P-%04d" % npn)
        if not old.get("no"):
            npn += 1
        if k in ("VIA_SPILL_DIR", "rep"):
            val = "(易變 · 每輪不同 · 只登記名稱與來源)"                  # v0197:易變值不登記 → 內容沒變不出新版
        params[k] = {"no": no, "value": val, "source": "環境變數" if k.startswith("VIA_") else "管理器", "status": "已確認(VCGC)" if grant.get(k) == no else "暫編 · 待 VCGC 核號"}
    eng = {k: dict(no=v.get("no"), version=v.get("version"), status="已確認(VCGC)" if grant.get(k) == v.get("no") else "暫編 · 待 VCGC 核號", versions=sorted(specs.get(k, {}).keys()))
           for k, v in engines.items() if isinstance(v, dict)}
    conflicts = _git_conflicts(home)
    pending = {k: v["no"] for sec in (eng, books, params) for k, v in sec.items() if v.get("no") and "暫編" in v.get("status", "")}
    body = {"schema": "VIA.VRN.AssetRegister.v1", "engines": eng, "books": books, "params": params, "specs": specs, "no_version": sorted(nover), "version_conflicts_vs_main": conflicts, "pending_tidy": pending_tidy}
    chg = {k: body[k] for k in body if k != "schema"} != {k: prev.get(k) for k in body if k != "schema"}
    nv = "v%04d" % ((vn(hits[-1]) + 1) if hits else 100)
    if chg:
        body.update(version=nv, prior=hits[-1].name if hits else None, ts=datetime.datetime.now().isoformat(timespec="seconds"),
                    rule="資產登記冊(唯一寫入者 VRN SystemManager):引擎沿用 VRN-E · 冊 VRN-B · 參數 VRN-P · 編號只在冊裡 · 暫編待 VCGC 核號 · 每版規格只增不減 · 內容變才出新版")
        (rd / ("VRN_Asset_Register_%s.json" % nv)).write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    (cd / "VRN_NUMBER_REQUEST_latest.json").write_text(json.dumps({"from": "VRN_SystemManager", "ts": datetime.datetime.now().isoformat(timespec="seconds"), "pending": pending,
                                                                    "rule": "VCGC 偵測三系統無衝突後寫 VCGC_NUMBER_GRANT_latest.json {grants:{key:no}} · VRN 讀到才轉已確認"}, ensure_ascii=False, indent=1), encoding="utf-8")
    cnt = lambda sec: (sum(1 for v in sec.values() if "已確認" in v.get("status", "")), sum(1 for v in sec.values() if "暫編" in v.get("status", "")))  # noqa: E731
    return {"file": ("VRN_Asset_Register_%s.json" % nv) if chg else (hits[-1].name + "(無變更)" if hits else "—"), "changed": chg, "engines": cnt(eng), "books": cnt(books), "params": cnt(params),
            "specs": sum(len(v) for v in specs.values()), "no_version": nover, "conflicts": conflicts, "pending": len(pending), "pending_tidy": pending_tidy}


def asset_lines(o: dict) -> list:
    L = ["[計] 資產登記(%s)· 引擎 已確認 %d / 暫編 %d · 冊 已確認 %d / 暫編 %d · 參數 已確認 %d / 暫編 %d · 版本規格 %d 筆 · 待 VCGC 核號 %d(contract/VRN_NUMBER_REQUEST_latest.json)" % (
        o["file"], *o["engines"], *o["books"], *o["params"], o["specs"], o["pending"])]
    if o["no_version"]:
        L.append("[計] 沒版號的 py %d:%s(該寫版本號)" % (len(o["no_version"]), " · ".join(o["no_version"][:6])))
    if o.get("pending_tidy"):
        L.append("[計] 待整理(隔離 / 傾倒 / _sha 字尾舊腳本 · 未掃 · 未點名)%d 支" % o["pending_tidy"])
    if o["conflicts"]:
        L.append("[RED] 版本號衝突(GitHub main 同名不同內容)%d:%s → 不要同號 · 出新版號" % (len(o["conflicts"]), " · ".join(o["conflicts"][:6])))
    return L


def reconcile(apply: bool = False) -> tuple:
    """不要同號 · 出新版號(v0196):同版號內容不同 → 本機內容另存 v+1 · 原號還原成 main 的內容 · 兩邊都保留 · 先列計畫 · --apply 才動 · 每步寫帳本。"""
    import datetime
    import subprocess
    home = Path((_resolve("_home") or (lambda: HERE))())
    conf = _git_conflicts(home)
    if not conf:
        return 0, ["[計] 版本號衝突 0 · 不用調和"]
    try:
        top = subprocess.run(["git", "-C", str(home), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:  # noqa: BLE001
        top = ""
    L, done = ["[計] 版本號衝突調和 %s · %d 件(本機內容 → v+1 · 原號還原 main · 只增不減)" % ("執行" if apply else "計畫(不動檔 · 加 --apply 才執行)", len(conf))], []
    for nm in conf[:60]:
        p = next(home.rglob(nm), None)
        if not p:
            continue
        m = re.search(r"^(.*_v)(\d{3,4})(\..+)$", nm)
        if not m:
            continue
        nv = "%s%0*d%s" % (m.group(1), len(m.group(2)), int(m.group(2)) + 1, m.group(3))
        np_ = p.with_name(nv)
        L.append("  %s → 本機內容存為 %s · %s 還原 main%s" % (nm, nv, nm, "(已存在 · 跳過)" if np_.exists() else ""))
        if apply and not np_.exists() and top:
            try:
                np_.write_bytes(p.read_bytes())
                rel = str(p.resolve().relative_to(Path(top).resolve())).replace("\\", "/")
                r = subprocess.run(["git", "-C", top, "checkout", "origin/main", "--", rel], capture_output=True, text=True, timeout=60)
                done.append({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "file": nm, "new_version": nv, "restored_from": "origin/main", "rc": r.returncode})
            except Exception as exc:  # noqa: BLE001
                L.append("[RED] 調和失敗 %s · %s" % (nm, type(exc).__name__))
    if apply:
        rd = home / "registry"
        rd.mkdir(parents=True, exist_ok=True)
        with (rd / "VRN_Reconcile_Ledger.jsonl").open("a", encoding="utf-8") as fh:
            for d in done:
                fh.write(json.dumps(d, ensure_ascii=False) + "\n")
        L.append("[計] 調和完成 %d 件 · 帳本 registry/VRN_Reconcile_Ledger.jsonl" % len(done))
    return 0, L


def p1loop(one: str = "", rep=None, prior=None) -> tuple:
    """v0196:退步區塊細節直接印進貼包(≤12 行)· 不用開 MD。rep / prior 只供自測注入 · 不替換任何函式(零頭)。"""
    rc, lines = (prior or PRIOR.p1loop)(one)
    try:
        pv = (Path(rep) if rep else Path(_resolve("_rep")())) / "p1view"
        reg = [l for l in lines if l.startswith("[RED] 鎖定過的檔案退步")]
        if reg:
            res = {r["file"]: r for r in json.loads((pv / "P1VIEW_latest.json").read_text(encoding="utf-8"))}
            names = re.findall(r"([^|:]+?\.pdf)\(", reg[0])
            n = 0
            for nm in names:
                r = next((v for k, v in res.items() if k.startswith(nm.strip()[:20])), None)
                for pg in (r or {}).get("pages") or []:
                    for z in pg["zones"]:
                        if n < 12 and (z.get("needs_ocr") or (z["minor"] == "TB" and pg["pno"] > 1 and "期間欄" not in (z.get("engine") or ""))):
                            txt = " ".join(x["text"] for x in z.get("records") or []) or " | ".join(" ".join(c for c in row if c) for row in (z.get("rows") or [])[:3])
                            lines.append("[計] 退步細節 %s · %s | %s·%s | %s | %s | 亂碼 %s 常用 %s | %s" % (r["file"][:22], z["id"], z["major"], z["minor_zh"], [int(v) for v in z["bbox"]], z.get("engine", ""), z.get("garbled", 0), z.get("common", ""), txt[:70]))
                            n += 1
    except Exception as exc:  # noqa: BLE001
        lines.append("[計] 退步細節印出失敗 · %s" % type(exc).__name__)
    return rc, lines


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["reconcile"]:
        rc, lines = reconcile("--apply" in args)
        for l in lines:
            print(l)
        return rc
    if args[:1] == ["register2"]:
        for l in asset_lines(asset_register()):
            print(l)
        return 0
    if args[:1] in (["p1view"], ["p1loop"]):
        one = args[args.index("--one") + 1] if "--one" in args and args.index("--one") + 1 < len(args) else ""
        rc, lines = (p1loop if args[0] == "p1loop" else _resolve("p1view"))(one)
        for l in lines:
            print(l)
    else:
        rc = _mod_v0197("v0194").main(args)                    # v0197:其他動詞走 v0194 的 main(避免 v0195 / v0196 的登記鉤子重複登記)
    if args and args[0] not in ("selfgate", "ui", "reconcile") and not args[0].startswith("-"):
        try:
            for l in asset_lines(asset_register()):               # v0195:任何動詞跑完自動登記(內容沒變不出新版)
                print(l)
        except Exception as exc:  # noqa: BLE001
            print("[計] 資產登記失敗 · %s" % type(exc).__name__)
    return rc


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    import json
    import tempfile
    td = Path(tempfile.mkdtemp(prefix="p1loop-"))
    (td / "p1view").mkdir()
    (td / "p1view" / "P1VIEW_latest.json").write_text(json.dumps([{"file": "Citi-5904 20260916.pdf", "lamp": "YELLOW", "reasons": ["財報表沒對到期間欄 1/7"], "pages": [{"pno": 1, "zones": []}, {"pno": 4, "zones": [{"id": "P4·FR·02·TB", "major": "FR", "minor": "TB", "minor_zh": "財報表", "bbox": [300, 100, 560, 400], "engine": "pdfplumber", "garbled": 0, "common": 0.95, "rows": [["Key ratios"], ["ROE (%)", "12.1", "13.4"]]}]}]}]), encoding="utf-8")
    rc1, l1 = p1loop(rep=td, prior=lambda one="": (1, ["[RED] 鎖定過的檔案退步 1:Citi-5904 20260916.pdf(財報表沒對到期間欄 1/7)"]))
    ta = Path(tempfile.mkdtemp(prefix="areg2-"))
    (ta / "registry").mkdir()
    (ta / "VRN_X_v0100.py").write_text('"""x"""\n', encoding="utf-8")
    (ta / "old_tool_sha0123456789ab.py").write_text("y = 1\n", encoding="utf-8")
    os.environ["VIA_SPILL_DIR"] = str(ta / "run1")
    a1 = asset_register(ta)
    os.environ["VIA_SPILL_DIR"] = str(ta / "run2")
    a2 = asset_register(ta)
    chk("⓪ 易變參數(VIA_SPILL_DIR 換值)不出新版(第二次無變更 %s)· _sha 字尾舊腳本不點名(沒版號 %s)· 待整理 %d" % (not a2["changed"], a1["no_version"], a1["pending_tidy"]),
        a1["changed"] and not a2["changed"] and "old_tool_sha0123456789ab.py" not in a1["no_version"] and a1["pending_tidy"] == 1 and _mod_v0197("v0194").TAG == "v0194")
    chk("① p1loop 退步區塊細節直接印進貼包(區編號 · 框 · 引擎 · 首 70 字)· 自測用參數注入 · 零替換 · reconcile 無衝突時回 0", rc1 == 1 and any(l.startswith("[計] 退步細節") and "P4·FR·02·TB" in l and "Key ratios" in l for l in l1) and reconcile(False)[0] == 0)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("② 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片 · 正式流程零替換 · 自測也零替換(參數注入)", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__)
        and "setattr(" not in me.split("def selftest")[0])
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0197 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
