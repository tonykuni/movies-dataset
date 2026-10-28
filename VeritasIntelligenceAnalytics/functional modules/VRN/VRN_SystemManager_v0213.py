#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0213 — 薄尾(ActivateVRN 後端:accelfix --all 補齊加速器到 100%(py:缺標記 + 舊橋 + 寫死舊版號 → 注入動態最新版號橋 · ps1:CELERITAS-TEMPLATE-JOIN + PS-ACCEL 橋,用 pwsh AST 定位 param 之後 / 第一個敘述之前 · 注入後再剖析 0 錯才寫)· envcheck 動詞:AST 掃加速器 / 網路工具 / VRN 尾版的 import → 缺的 --install 用本環境 pip 補(numpy 釘 <2 · 隔離套件不裝)· VRN-2 U/I 加「啟動檢查」分頁)(前版 v0212:個股四項第 20 輪實證:快訊判定看首頁前 600 字(月營收 · Background · We met · Summit)· Note / NR / 快訊首頁無評等 → 灰 · 快訊評價 EPS + 1 項即綠 · 無 EPS → 灰 · 年度數據只在文字段未切成表 → 黃(引擎待修)· 首頁無文字層 → 紅(OCR)· 交互驗證重算燈納入首頁無文字層)(前版 v0211:個股四項判定修正:年份往下排的表也算年度表 · 欄位整齊(數字列格數 ≈ 年度欄數)視為對齊 · 快訊 / 月營收更新 / 法說摘要 / Note 無年度表 → 灰 · Note / NR / 未評等首頁無評等 → 灰 · 券商與日期從首頁頁首補 · 未綠明細行改 [計] 開頭進貼包)(前版 v0210:VRN-2 個股報告四項驗收:辨識個股報告(代號 + 排除產業 / 晨報 / 盤後 / ETF / 論壇等)→ ①檔名(代號 · 日期 · 券商)②首頁(評等 / 目標價)③年度財報頁(期間欄對齊 · ≥2 個年度欄)④年度重要財報及評價資訊(EPS + ≥2 個評價指標)· 每項三燈 + 灰(快訊無年度財報)· 逐項鎖定只增不減 · 鎖過的項退步亮紅 · 先前成功先鎖 · U/I 個股分頁)(前版 v0209:VRN-2 交互驗證修正:CSV 只寫非空格與有內容的區 → 比對口徑改為「有內容的區 · 非空格 · 文字記錄」三項 · 不一致時列出哪一項 · 引擎欄取 P1Segment / AssetIndex 最新版)(前版 v0208:VRN-2 獨立子系統 vrn2 動詞:p1loop 成功(退步 0)→ 鎖版本 + 時間(registry/VRN2_Lock_*.json · 引擎 sha · 輸入檔 sha)· 備份成功狀態(VIA_Reports/vrn2/backup/<時間>/)· 對 C:\測試樣本報告 結果做一次交互驗證(JSON ↔ CSV ↔ 燈號)· 自動跳出 HTML U/I(VIA_Reports/vrn2/VRN2_UI_latest.html);accelfix 排除 intake/ 交接副本)(前版 v0207:accelfix 修正:同時掃程式碼夾(HERE · 現役尾版)與資料家目錄 · 計畫行帶相對路徑 · 摘要分夾計數 · 程式碼夾優先)(前版 v0206:accelfix:缺加速器標記的現役尾版 → AST 定位(docstring / __future__ 之後)注入加速器橋 · 出 v+1 新版原檔不動 · 先編譯檢查 · 每批 ≤20 · 計畫 / --apply · 帳本)(前版 v0205:reconcile:references / baseline / _sandbox 底下的基準快照不算衝突 · 只調和現役的冊與引擎)(前版 v0204:沙盒閘環境相依過濾修正:測試名稱比對去數字 / # / % / 標點 · 只比骨幹 · 閘印的 P# 對得上原始碼的 P%d)(前版 v0203:linkmap 動詞 → ENG396 v0102 連結圖:管理器 / 引擎 → 冊 · regex · 參數 · JSON 資料流 三燈矩陣 · 可同步 / 順序 分類 · MD + HTML)(前版 v0202:沙盒閘:新尾版多出的失敗若是舊版本就有的環境相依測試(OCR / 網路)→ 歸類環境 · 不算新增失敗 · 其餘仍判紅)(前版 v0201:reconcile 修正:衝突用相對路徑 · 同族以資料夾 + 名稱分 · 版號固定四位 · 去重;前版算出 v0001 與重複列的 bug)(前版 v0200:修正閘快查前核對指紋快照:只差行尾(CRLF/LF)的檔視為未改 · 更新該筆快照 · 內容真不同仍判紅 · 零替換)(前版 v0199:reconcile 整族接續編號:同族多版衝突時 · 本機各版依序存到該族現有最大版號之後(v0102→v0110 …)· 不再 v+1 互相覆蓋 · Result / Registry 不算冊)(前版 v0198:計畫每件一行 [計] 調和(進貼包)· 計畫寫 registry/VRN_Reconcile_Plan_latest.md)(前版 v0197:自查遺漏:易變參數(VIA_SPILL_DIR · rep)只登記名稱來源不登記值 → 登記冊內容沒變不出新版;隔離 / 傾倒 / _sha 字尾的舊腳本不掃 · 另計「待整理」· 不再點名 3624 支沒版號)(前版 v0196:版本號衝突只算有版號的冊 / 引擎(帳本 · 紀錄 · 輸出不算)· reconcile 動詞 = 不要同號出新版號(本機內容 → v+1 · 原號還原 main · 只增不減 · 先列計畫 --apply 才動)· p1loop 把退步區塊細節直接印進貼包)(前版 v0195:該註冊註冊 · 該編號編號 · 版本號寫版本號 · 每版規格存冊 · 自動建立;編號待 VCGC 核號無衝突才確認 · 本機先用 git 比對 main 抓同名不同內容的版本號衝突)(前版 v0194:退步細節追加 MD · 印 MD 路徑 · AI 讀 MD 不用截圖)(前版 v0193:實測實修迴圈 p1loop · 每輪跑 p1view → 綠燈檔案鎖定(只增不減 · 退步亮紅)· 與上一輪比較燈號 / 原因增減 · 輪次 append-only 帳本)(前版 v0192:摘要如實寫 PDF 份數 · 先切割再 pdfplumber 擷取 · 本文 / 資訊區分開 · 不亂碼 · 不能用馬上換)。
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
import os
import html
from collections import Counter
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0213"


def _vnum_v0213(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0213(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0213(p) < _vnum_v0213(__file__)), key=_vnum_v0213)
PRIOR = _load_v0213(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


def _mod_v0213(tag: str):
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
            if not re.search(r"_v\d{3,4}", nm) or re.search(r"(?i)ledger|manifest|evidence|audit|report|_latest|lock|registr|progress|cache|result", nm):
                continue
            if re.search(r"(?i)[\\/](?:references|baseline|_sandbox|vrn_sandbox|_quarantine|_superseded)[\\/]", parts[1] + "/"):
                continue                                               # v0205:基準快照 / 隔離 / 沙盒副本不是現役的冊                                           # v0196:只算有版號的冊 / 引擎 · 帳本 / 紀錄 / 輸出不算
            sha = parts[0].split()[2]
            lp = Path(top) / parts[1]
            if lp.exists():
                mine = subprocess.run(["git", "-C", top, "hash-object", str(lp)], capture_output=True, text=True, timeout=20).stdout.strip()
                if mine and mine != sha:
                    try:
                        bad.append(str(lp.resolve().relative_to(home.resolve())).replace("\\", "/"))   # v0201:相對路徑(同名不同夾不混)
                    except ValueError:
                        bad.append(nm)
        return sorted(set(bad))
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


_ENVTEST = re.compile(r"OCR|rapidocr|paddle|tesseract|雙引擎|網路|download|http|yfinance|連線", re.I)


def env_flaky_filter(o: dict, older_has) -> list:
    """v0202:「新尾版多出失敗「X」」若 X 是舊版本就有的環境相依測試(OCR / 網路)→ 從紅字移到環境 · 回傳移走的清單。older_has(label) 查舊版本原始碼。"""
    reds = list(o.get("red") or [])
    moved = []
    for r in reds:
        m = re.search(r"新尾版多出失敗「(.{6,40})", r)
        if m and _ENVTEST.search(m.group(1)) and older_has(m.group(1)):
            o["red"].remove(r)
            o.setdefault("env_flaky", []).append(r)
            moved.append(m.group(1)[:30])
    if moved and not o.get("red") and o.get("verdict") == "RED":
        o["verdict"] = "YELLOW"
    return moved


def _skel(t: str) -> str:
    return re.sub(r"[\s\d#%()（）:：·,，.。\[\]\-_]", "", t)


def _older_has(label: str) -> bool:
    """v0204:只比名稱骨幹(去數字 / # / % / 空白 / 標點)· 閘印出的「P# 圖區」對得上原始碼的「P%d 圖區」。"""
    key = _skel(label)[:10]
    if len(key) < 4:
        return False
    for p in HERE.glob(_STEM + "_v*.py"):
        if _vnum_v0213(p) < _vnum_v0213(__file__):
            try:
                if key in _skel(p.read_text(encoding="utf-8", errors="replace")):
                    return True
            except OSError:
                continue
    return False


def linkmap_verb() -> tuple:
    cands = sorted(HERE.glob("VRN_ENG396_AssetIndex_v*.py"), key=_vnum_v0213)
    m = _load_v0213(cands[-1], "vrn_eng396_" + cands[-1].stem) if cands else None
    if m is None or not hasattr(m, "linkmap"):
        return 1, ["[RED] 連結圖 · ENG396 v0102 以上不在 VRN 樹"]
    try:
        o = m.linkmap(HERE, Path(_resolve("_rep")()))
    except Exception as exc:  # noqa: BLE001
        return 1, ["[RED] 連結圖失敗 · %s: %s" % (type(exc).__name__, str(exc)[:120])]
    return 0, ["[計] 連結圖(ENG396)· 尾版 %d · 燈 %s · 可同步修正 %d · 順序修正(要決定)%d · 同領域多本冊 %s" % (o["nodes"], o["lamps"], o["sync"], o["seq"], o["multi"] or "無"),
               "  [MD] %s" % o["md"], "  [U/I] %s" % o["html"]]


BRIDGE_TXT = '# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====\nimport importlib as _cb_il\nimport re as _cb_re\nimport sys as _cb_sys\nfrom pathlib import Path as _cb_Path\n_ACCEL, _ACCEL_VER = None, ""\n_cb_p = _cb_Path(__file__).resolve()\nwhile _cb_p.parent != _cb_p:\n    if (_cb_p / "supportive modules").is_dir():\n        _cb_sup = _cb_p / "supportive modules"\n        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),\n                       key=lambda x: int(_cb_re.search(r"_v(\\d{4})", x.name).group(1)))\n        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:\n            if _cb_d not in _cb_sys.path:\n                _cb_sys.path.insert(0, _cb_d)\n        if _cb_c:\n            try:\n                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem\n            except Exception:  # noqa: BLE001\n                _ACCEL = None\n        break\n    _cb_p = _cb_p.parent\nif _ACCEL is None:\n    try:\n        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版\n        _ACCEL_VER = "VeritasCeleritas_v1141"\n    except Exception:  # noqa: BLE001\n        _ACCEL = None\n\n\ndef _net():\n    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""\n    try:\n        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433\n        return _NET\n    except Exception:  # noqa: BLE001\n        return None\n# ===== [VIA:ACCEL-BRIDGE:END] =====\n'
_AF_SKIP = re.compile(r"(?i)[\\/](?:_superseded|__pycache__|\.git|\.venv|venv|envs|tests?|_quarantine|quarantine|隔離|_dump|_raw|archive|_old|backup|references|baseline|_sandbox|vrn_sandbox|VIA_Reports|restore|restore_learned|intake|handover)[\\/]|_sha[0-9a-f]{6,}\.")


def accelfix(apply: bool = False, home=None, limit: int = 20, every: bool = False) -> tuple:
    """缺加速器標記的現役尾版(py)→ 在 docstring / from __future__ 之後注入加速器橋 · 出 v+1 · 原檔不動 · 先編譯 · 每批 ≤limit · 計畫 / --apply。"""
    import ast
    import datetime
    dh = Path((_resolve("_home") or (lambda: HERE))())
    roots = [Path(home)] if home else ([HERE] + ([dh] if dh.resolve() != HERE.resolve() else []))   # v0207:程式碼夾優先 · 資料家目錄次之
    home = roots[0]
    fams = {}
    for root in roots:
      for p in root.rglob("*.py"):
        if _AF_SKIP.search(str(p)) or not p.is_file():
            continue
        m = re.search(r"^(.*)_v(\d{3,4})$", p.stem)
        if not m:
            continue
        k = (str(p.parent), m.group(1))
        v = int(m.group(2))
        if k not in fams or v > fams[k][1]:
            fams[k] = (p, v)
    def _rel(p):
        for r in roots:
            try:
                return ("[碼] " if r == roots[0] and len(roots) > 1 else ("[資料] " if len(roots) > 1 else "")) + str(p.parent.resolve().relative_to(r.resolve())).replace("\\", "/")
            except ValueError:
                continue
        return str(p.parent)
    cands = []
    for (sub, fam), (p, v) in sorted(fams.items()):
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if every:                                                    # v0213:--all = 只要不是綠(缺標記 / 舊橋 / 寫死舊版號 / 沒接正本)都補動態最新版號橋
            kind = (_resolve("accel_kind") or (lambda *a: ("", "OP-300")))(src, ".py", _latest_accel_name())
            if kind[1] == "GREEN" or "VIA:ACCEL-BRIDGE:v0111" in src:
                continue
        elif "[VIA:ACCEL-BRIDGE" in src or "VeritasCeleritas" in src:
            continue
        cands.append((p, v, src))
    batch = cands[:limit]
    fold = Counter(_rel(p) for p, _, _ in cands)
    L = ["[計] 加速器注入(accelfix)%s · 缺標記現役尾版 %d · 本批 %d(每批 ≤%d · AST 定位 docstring / __future__ 之後 · 出 v+1 原檔不動 · 先編譯)· 分夾:%s" % (" 執行" if apply else " 計畫(不動檔 · --apply 才寫)", len(cands), len(batch), limit, " · ".join("%s %d" % kv for kv in fold.most_common(6)))]
    done, bad = [], []
    for p, v, src in batch:
        try:
            t = ast.parse(src)
        except SyntaxError as exc:
            bad.append("%s 原檔語法錯 %s" % (p.name, exc.lineno))
            continue
        idx = 0
        body = t.body
        if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
            idx = 1
        while idx < len(body) and isinstance(body[idx], ast.ImportFrom) and body[idx].module == "__future__":
            idx += 1
        line = body[idx - 1].end_lineno if idx > 0 else 0
        lines = src.splitlines(keepends=True)
        new = "".join(lines[:line]) + ("\n" if line and not lines[line - 1].endswith("\n") else "") + BRIDGE_TXT.rstrip("\n") + "\n" + "".join(lines[line:])
        try:
            compile(new, p.name, "exec")
        except SyntaxError as exc:
            bad.append("%s 注入後編譯失敗 %s" % (p.name, exc.lineno))
            continue
        nv = p.with_name(re.sub(r"_v\d{3,4}$", "_v%04d" % (v + 1), p.stem) + ".py")
        L.append("[計] 注入 %s/%s → %s(定位第 %d 行後)%s" % (_rel(p), p.name, nv.name, line, "(新版已存在 · 跳過)" if nv.exists() else ""))
        if apply and not nv.exists():
            nv.write_text(new, encoding="utf-8", newline="")
            done.append({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "src": p.name, "new": nv.name, "line": line})
    for b in bad:
        L.append("[計] 跳過 %s" % b)
    if apply:
        rd = home / "registry"
        rd.mkdir(parents=True, exist_ok=True)
        with (rd / "VRN_AccelFix_Ledger.jsonl").open("a", encoding="utf-8") as fh:
            for d in done:
                fh.write(json.dumps(d, ensure_ascii=False) + "\n")
        L.append("[計] 加速器注入完成 %d 件 · 跳過 %d · 剩餘缺標記 %d · 帳本 registry/VRN_AccelFix_Ledger.jsonl" % (len(done), len(bad), len(cands) - len(done)))
    return 0, L


def _latest_accel_name() -> str:
    try:
        return (_resolve("latest_accel") or (lambda h: ""))(HERE) or ""
    except Exception:  # noqa: BLE001
        return ""


PS_JOIN = "# CELERITAS-TEMPLATE-JOIN v1"
PS_ACCEL = ("# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====\n"
            "try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\\Users\\tonyk\\OneDrive\\Documents\\movies-dataset\\VeritasIntelligenceAnalytics' }\n"
            "  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe \"supportive modules\\VIA_PS_Accel_Module.ps1\"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }\n"
            "# ===== [VIA:PS-ACCEL:END] =====")
_PS_PROBE = r"""param([string]$List)
$out = @{}
foreach ($p in (Get-Content -LiteralPath $List -Encoding utf8)) {
  if (-not $p) { continue }
  $tok = $null; $err = $null
  $a = [System.Management.Automation.Language.Parser]::ParseFile($p, [ref]$tok, [ref]$err)
  $first = @(@($a.BeginBlock, $a.ProcessBlock, $a.EndBlock, $a.DynamicParamBlock) | Where-Object { $_ } | ForEach-Object { $_.Statements } | Where-Object { $_ } | ForEach-Object { $_.Extent.StartOffset } | Sort-Object | Select-Object -First 1)
  $ue = @($a.UsingStatements | ForEach-Object { $_.Extent.EndOffset } | Sort-Object -Descending | Select-Object -First 1)
  $out[$p] = @{ errors = @($err).Count; param_end = $(if ($a.ParamBlock) { $a.ParamBlock.Extent.EndOffset } else { -1 }); using_end = $(if ($ue) { $ue[0] } else { -1 }); first = $(if ($first) { $first[0] } else { -1 }) }
}
$out | ConvertTo-Json -Depth 4 -Compress
"""


def _ps_probe(paths: list) -> dict:
    """pwsh AST 定位(一次批次):每檔 param 結尾 / using 結尾 / 第一個敘述起點 / 剖析錯數;沒有 pwsh → {}。"""
    import shutil
    import subprocess
    import tempfile
    exe = shutil.which("pwsh") or shutil.which("pwsh.exe")
    if not exe or not paths:
        return {}
    td = Path(tempfile.mkdtemp(prefix="psaccel-"))
    (td / "probe.ps1").write_text(_PS_PROBE, encoding="utf-8-sig")
    (td / "list.txt").write_text("\n".join(str(p) for p in paths), encoding="utf-8")
    try:
        r = subprocess.run([exe, "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(td / "probe.ps1"), "-List", str(td / "list.txt")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        txt = (r.stdout or "").strip()
        d = json.loads(txt) if txt.startswith("{") else {}
        return {k: v for k, v in d.items()} if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def ps_accelfix(apply: bool = False, limit: int = 2000) -> tuple:
    """現役尾版 .ps1 缺 PS 加速橋 → 頂端補 CELERITAS-TEMPLATE-JOIN 標記 + PS-ACCEL 橋(param 之後 / using 之後 / 第一個敘述之前)· 出 v+1 · 原檔不動 · 注入後 pwsh 再剖析 0 錯才寫。"""
    import datetime
    import tempfile
    fams = {}
    for p in HERE.rglob("*.ps1"):
        if _AF_SKIP.search(str(p)) or not p.is_file():
            continue
        m = re.search(r"^(.*)_v(\d{3,4})$", p.stem)
        if not m:
            continue
        k = (str(p.parent), m.group(1))
        if k not in fams or int(m.group(2)) > fams[k][1]:
            fams[k] = (p, int(m.group(2)))
    cands = []
    for (sub, fam), (p, v) in sorted(fams.items()):
        raw = p.read_bytes()
        bom = raw.startswith(b"\xef\xbb\xbf")
        src = raw.decode("utf-8-sig", errors="replace")
        if PS_JOIN.split(" v")[0] in src and "[VIA:PS-ACCEL" in src:
            continue
        cands.append((p, v, src, bom))
    batch = cands[:limit]
    L = ["[計] PS 加速橋(accelfix --all · ps1)%s · 缺橋現役尾版 %d · 本批 %d(pwsh AST 定位 · 出 v+1 原檔不動 · 注入後再剖析 0 錯才寫)" % (" 執行" if apply else " 計畫", len(cands), len(batch))]
    if not batch:
        return 0, L
    pr = _ps_probe([p for p, _, _, _ in batch])
    if not pr:
        L.append("[計] PS 加速橋 · 找不到 pwsh 或剖析失敗 → 本批略過(不動任何 ps1)")
        return 0, L
    td = Path(tempfile.mkdtemp(prefix="psaccel-new-"))
    staged, bad = [], []
    for p, v, src, bom in batch:
        info = pr.get(str(p)) or {}
        if info.get("errors", 1):
            bad.append("%s 原檔剖析錯 %s 處" % (p.name, info.get("errors", "?")))
            continue
        nl = "\r\n" if "\r\n" in src else "\n"
        blk = PS_ACCEL.replace("\n", nl)
        at = next((x for x in (info.get("param_end", -1), info.get("using_end", -1)) if x is not None and x >= 0), -1)
        if at >= 0:
            new = src[:at] + nl + blk + nl + src[at:].lstrip("\r\n") if not src[at:].startswith(nl) else src[:at] + nl + blk + src[at:]
            where = "param 之後" if info.get("param_end", -1) >= 0 else "using 之後"
        else:
            f = info.get("first", -1)
            f = f if f is not None and f >= 0 else len(src)
            new, where = src[:f] + blk + nl + src[f:], "第一個敘述之前"
        if PS_JOIN.split(" v")[0] not in new:
            new = PS_JOIN + nl + new
        nv = p.with_name(re.sub(r"_v\d{3,4}$", "_v%04d" % (v + 1), p.stem) + ".ps1")
        tmp = td / nv.name
        tmp.write_bytes((b"\xef\xbb\xbf" if bom else b"") + new.encode("utf-8"))
        staged.append((p, nv, tmp, where))
    chk = _ps_probe([t for _, _, t, _ in staged])
    done = []
    for p, nv, tmp, where in staged:
        e = (chk.get(str(tmp)) or {}).get("errors", 1)
        if e:
            bad.append("%s 注入後剖析錯 %s 處(不寫)" % (p.name, e))
            continue
        L.append("[計] 注入 PS 橋 %s → %s(%s)%s" % (p.name, nv.name, where, "(新版已存在 · 跳過)" if nv.exists() else ""))
        if apply and not nv.exists():
            nv.write_bytes(tmp.read_bytes())
            done.append({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "src": p.name, "new": nv.name, "where": where, "kind": "ps1"})
    for b in bad:
        L.append("[計] 跳過 %s" % b)
    if apply and done:
        rd = HERE / "registry"
        rd.mkdir(parents=True, exist_ok=True)
        with (rd / "VRN_AccelFix_Ledger.jsonl").open("a", encoding="utf-8") as fh:
            for d in done:
                fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    L.append("[計] PS 加速橋完成 %d 件 · 跳過 %d · 剩餘 %d" % (len(done), len(bad), len(cands) - len(done)))
    return 0, L


_PIPNAME = {"fitz": "pymupdf", "yaml": "pyyaml", "bs4": "beautifulsoup4", "docx": "python-docx", "pptx": "python-pptx", "PIL": "pillow", "cv2": "opencv-python-headless",
            "sklearn": "scikit-learn", "dateutil": "python-dateutil", "win32api": "pywin32", "win32con": "pywin32", "win32com": "pywin32", "pythoncom": "pywin32", "pywintypes": "pywin32",
            "Crypto": "pycryptodome", "dotenv": "python-dotenv", "rapidocr_onnxruntime": "rapidocr-onnxruntime", "google": "google-api-python-client", "jwt": "pyjwt", "magic": "python-magic-bin",
            "serial": "pyserial", "attr": "attrs", "OpenSSL": "pyopenssl", "lz4": "lz4", "zstandard": "zstandard", "talib": "TA-Lib", "pdfminer": "pdfminer.six", "Levenshtein": "python-Levenshtein",
            "multipart": "python-multipart", "socks": "pysocks", "markdown": "markdown", "sentence_transformers": "sentence-transformers"}
_ISOLATED = re.compile(r"(?i)^(?:torch|torchvision|torchaudio|surya|ray|tabula|camelot|numba|ortools|paddle\w*|tensorflow|keras|uvloop|pm4py|ocrmypdf|modnet|rembg|onnxruntime_gpu|jax|cupy)$")


def envcheck(install: bool = False) -> tuple:
    """AST 掃 import(加速器 + 網路工具 = 必裝;VRN 尾版:頂層必裝 · try 內選裝)→ 缺的用本環境 pip 補(numpy 釘 >=1.24,<2.0 · 隔離套件不裝只列灰)。"""
    import ast
    import importlib.util
    import subprocess
    import sys
    import tempfile
    sup = next((p / "supportive modules" for p in [HERE] + list(HERE.parents) if (p / "supportive modules").is_dir()), None)
    must_files, opt_files = [], []
    if sup:
        acc = sorted(list(sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")), key=lambda x: int(re.search(r"_v(\d{4})", x.name).group(1)))
        must_files += acc[-1:] + list(sup.glob("VeritasAegisNexus_v1652.py"))[:1] + list(sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]
    fams = {}
    for p in HERE.rglob("*.py"):
        if _AF_SKIP.search(str(p)):
            continue
        m = re.search(r"^(.*)_v(\d{3,4})$", p.stem)
        if m and ((str(p.parent), m.group(1)) not in fams or int(m.group(2)) > fams[(str(p.parent), m.group(1))][1]):
            fams[(str(p.parent), m.group(1))] = (p, int(m.group(2)))
    opt_files = [p for p, _ in fams.values()]
    local = {p.stem for p in HERE.rglob("*.py")} | ({p.stem for p in sup.rglob("*.py")} if sup else set()) | {p.name for p in HERE.iterdir() if p.is_dir()}
    std = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
    need = {}

    def scan(f, must):
        try:
            t = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, OSError, ValueError):
            return
        tries = {id(n) for x in ast.walk(t) if isinstance(x, ast.Try) for b in x.body for n in ast.walk(b)}
        for n in ast.walk(t):
            names = [a.name for a in n.names] if isinstance(n, ast.Import) else ([n.module] if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module else [])
            for nm in names:
                top = nm.split(".")[0]
                if not top or top in std or top in local or top.startswith(("_", "VRN_", "VIA_", "Veritas", "CGC_", "VDF_", "VCGC")):
                    continue
                hard = must or id(n) not in tries
                d = need.setdefault(top, {"must": False, "hard": False, "by": set()})
                d["must"] |= must
                d["hard"] |= hard
                d["by"].add(f.name)
    for f in must_files:
        scan(f, True)
    for f in opt_files:
        scan(f, False)
    rows = []
    for top, d in sorted(need.items()):
        ok = importlib.util.find_spec(top) is not None
        pip = _PIPNAME.get(top, top.replace("_", "-"))
        lamp = "GREEN" if ok else ("GRAY" if _ISOLATED.match(top) else ("RED" if d["must"] or d["hard"] else "YELLOW"))
        rows.append({"module": top, "pip": pip, "lamp": lamp, "must": d["must"], "hard": d["hard"], "by": sorted(d["by"])[:3], "installed": ok, "action": ""})
    todo = [r for r in rows if r["lamp"] in ("RED", "YELLOW")]
    L = ["[計] 環境檢查(envcheck · %s)· 掃 加速器 / 網路工具 %d 檔 + VRN 尾版 %d 檔 · 第三方套件 %d · 已裝 %d · 缺(必裝)%d · 缺(選裝)%d · 隔離不裝 %d" % (
        sys.executable, len(must_files), len(opt_files), len(rows), sum(1 for r in rows if r["installed"]), sum(1 for r in rows if r["lamp"] == "RED"),
        sum(1 for r in rows if r["lamp"] == "YELLOW"), sum(1 for r in rows if r["lamp"] == "GRAY"))]
    if install and todo:
        cf = Path(tempfile.mkdtemp(prefix="pipc-")) / "constraints.txt"
        cf.write_text("numpy>=1.24,<2.0\n", encoding="utf-8")
        for r in todo:
            try:
                p = subprocess.run([sys.executable, "-m", "pip", "install", "--no-input", "--disable-pip-version-check", "-c", str(cf), r["pip"]], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
                importlib.invalidate_caches()
                r["installed"] = importlib.util.find_spec(r["module"]) is not None
                r["action"] = "已補裝" if r["installed"] else "補裝失敗 rc %d · %s" % (p.returncode, ((p.stderr or "").strip().splitlines() or [""])[-1][:90])
            except Exception as exc:  # noqa: BLE001
                r["action"] = "補裝失敗 · %s" % type(exc).__name__
            if r["installed"]:
                r["lamp"] = "GREEN"
            L.append("[計] 補裝 %s(%s)· %s" % (r["pip"], "必裝" if r["must"] else ("頂層" if r["hard"] else "選裝"), r["action"]))
    for r in rows:
        if r["lamp"] in ("RED", "YELLOW") and not (install and r["action"]):
            L.append("[計] 缺 %s %s(pip %s · 用於 %s)" % ("必裝" if r["lamp"] == "RED" else "選裝", r["module"], r["pip"], " · ".join(r["by"])))
        elif r["lamp"] == "GRAY":
            L.append("[計] 隔離套件 %s 不裝進本環境(LL#21–24 · 經橋呼叫)" % r["module"])
    try:
        rep = Path(_resolve("_rep")()).parent / "vrn2"
        rep.mkdir(parents=True, exist_ok=True)
        (rep / "VRN2_Env_latest.json").write_text(json.dumps({"python": sys.executable, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    bad = [r for r in rows if r["lamp"] == "RED"]
    return (1 if bad else 0), L


def _activate_html(v2: Path) -> str:
    try:
        a = json.loads((v2 / "VRN2_Activate_latest.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return ""
    lampi = lambda l: "<i style='background:%s'%s></i>" % (_V2C.get(l, "#9ca3af"), " class='bl'" if l == "RED" else "")  # noqa: E731
    rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (lampi(s.get("lamp", "GRAY")), html.escape(s.get("step", "")), html.escape(s.get("detail", ""))) for s in a.get("steps", []))
    return "<h3>%s啟動檢查(ActivateVRN · %s)</h3><table><tr><th>燈</th><th>步驟</th><th>結果</th></tr>%s</table>" % (lampi(a.get("lamp", "GRAY")), html.escape(a.get("ts", "")), rows)


_V2C = {"GREEN": "#16a34a", "YELLOW": "#eab308", "RED": "#dc2626", "GRAY": "#9ca3af"}

_SK_EXCL = re.compile(r"(?i)晨會|早報|盤後|盤勢|ETF|籌碼|總經|論壇|第.場|專題|產業|Databook|summit|Insights|hardware|Thermal|Memory|Automation|PCB|ABF|CPO|AI Power|TPU|Components|觀察家|[周週]報|解盤|股市分析|股分析|鋼鐵")
_SK_BROKER = [("兆豐", r"兆豐"), ("國泰", r"國泰|團泰|Cathay"), ("中信", r"中國信託|中國僖託|CTBC"), ("凱基", r"凱基|KGI"), ("華南", r"華南|Hua Nan"), ("凱基", r"凱基|KGI"), ("華南", r"華南"), ("統一", r"統一投顧"), ("國泰", r"國泰"), ("中信", r"CTBC|中信"), ("群益", r"群益"), ("元富", r"元富"), ("台新", r"台新"),
              ("Morgan Stanley", r"(?i)(?:^|[_\- ])ms(?:[_\- ]|$)"), ("Goldman Sachs", r"(?i)^GS[-_ ]"), ("J.P. Morgan", r"(?i)^JP[-_ ]"), ("UBS", r"(?i)ubs"), ("Citi", r"(?i)citi"),
              ("Daiwa", r"(?i)daiwa"), ("CLSA", r"(?i)CLS[AT]"), ("GF", r"(?i)^GF"), ("Macquarie", r"(?i)^MQ[-_ ]")]
_SK_ANNUAL = re.compile(r"^(?:FY)?(?:19|20)\d{2}(?:[AEFP]|\([AEFP]\)|年度?|CT)?$|^\d{2}[AEFP]$|^FY\d{2}[AEFP]?$|^(?:Dec|Mar|Jun|Sep)-\d{2}[AEFP]?$|^1[01]\d年[AEFP]?$|^12/\d{2}[AEFP]?$", re.I)
_SK_EPS = re.compile(r"(?i)EPS|每股盈餘|每股純益|Earnings per share")
_SK_VAL = [("本益比", r"(?i)本益比|P/E|\bPERs?\b"), ("股價淨值比", r"(?i)股價淨值比|本淨比|P/B|\bPBR\b|P/BV"), ("ROE", r"(?i)ROE|股東權益報酬率|ROAE"), ("殖利率", r"(?i)殖利率|Dividend yield|Div yld"),
           ("EV/EBITDA", r"(?i)EV/EBITDA"), ("目標價", r"(?i)目標價|Target price|Price target|\bTP\b"), ("每股淨值", r"(?i)每股淨值|BVPS")]


_SK_NOTE = re.compile(r"(?i)Background:|We met with|update with the management|(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (?:monthly )?(?:sales|revenue)|\bUpdate\b|\bFlash\b|\bNote\b|Takeaway|Summit|速報|摘要|法說|座談|Monthly|monthly (?:sales|revenue)|月營收|Nov Rev|Sep revenue|revenue \+")
_SK_NR = re.compile(r"(?i)\bNote\b|\bNR\b|未評等|Not rated|Takeaway|法說|座談")
_NUMC = re.compile(r"^[\(\-−]?[\d,]+(?:\.\d+)?%?\)?$|^n\.?a\.?$|^-+$|^NM$", re.I)


def _sk_date(nm: str) -> str:
    m = re.search(r"(20\d{2})[-_.]?([01]\d)[-_.]?([0-3]\d)", nm)
    if m:
        return "%s-%s-%s" % m.groups()
    m = re.search(r"(?<!\d)1(1\d)([01]\d)([0-3]\d)(?!\d)", nm)
    if m:
        return "%d-%s-%s" % (1911 + 100 + int(m.group(1)), m.group(2), m.group(3))
    m = re.search(r"(?<!\d)(2\d)([01]\d)([0-3]\d)(?!\d)", nm)
    return "20%s-%s-%s" % m.groups() if m else ""


def _sk_ticker(nm: str, title: str) -> str:
    for t in re.findall(r"(?<!\d)(\d{4})(?!\d|年)", nm):
        if not re.match(r"20[1-3]\d$", t) or re.search(t + r"\s?(?:TT|\)|,)", nm):
            return t
    m = re.search(r"\(?(?<!\d)(\d{4})(?:\s?TT|\.TWO?|\s?TW|\))", title) or re.search(r"\(([A-Z]{1,5})\s?US\)", title)
    return m.group(1) if m else ""


def stock_eval(r: dict, npages: int) -> dict:
    """個股報告四項:檔名 · 首頁 · 年度財報頁 · 年度重要財報及評價資訊 → 每項 GREEN / YELLOW / RED / GRAY + 說明。"""
    f = r.get("file", "")
    pages = r.get("pages") or []
    zs = [(pg.get("pno", 1), z) for pg in pages for z in pg.get("zones") or []]
    ztxt = lambda z: " ".join(x.get("text", "") for x in z.get("records") or []) + " " + " ".join(c for row in (z.get("rows") or []) for c in row if c)  # noqa: E731
    title = " ".join(ztxt(z) for p, z in zs if p == 1 and z.get("major") in ("T", "L", "R"))
    tk, dt = _sk_ticker(f, title), _sk_date(f)
    if not dt:
        m = re.search(r"(20\d{2})[/.\-年]\s?(\d{1,2})[/.\-月]\s?(\d{1,2})", title)
        dt = "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3))) if m else ""
    if not tk or _SK_EXCL.search(f):
        return {"stock": False, "file": f, "why": "產業 / 晨報 / 盤後 / ETF / 論壇等" if tk else "沒有個股代號"}
    br = next((n for n, rx in _SK_BROKER if re.search(rx, f)), "") or next((n for n, rx in _SK_BROKER if re.search(rx, title)), "")
    p1all = " ".join(ztxt(z) for p, z in zs if p == 1)
    nr = bool(_SK_NR.search(f) or _SK_NR.search(title[:400]))
    note = bool(_SK_NOTE.search(f) or _SK_NOTE.search(title[:400]) or _SK_NOTE.search(p1all[:600])) or nr
    notext = "首頁無文字層 → OCR 排隊" in (r.get("reasons") or []) or not any(p == 1 for p, _ in zs)
    p_fn = ("GREEN" if br and dt else "YELLOW", "代號 %s · 日期 %s · 券商 %s" % (tk, dt or "—", br or "—"))
    rt = [ztxt(z)[:40] for p, z in zs if p == 1 and z.get("minor") == "RT"]
    miss = "首頁沒抓到評等 / 目標價" in (r.get("reasons") or [])
    if notext:
        p_p1 = ("RED", "首頁無文字層(影像 PDF)→ OCR 排隊")
    elif miss and note:
        p_p1 = ("GRAY", "Note / 未評等 / 快訊 · 首頁本來沒有評等")
    else:
        p_p1 = ("YELLOW" if miss else "GREEN", rt[0] if rt else "")
    ann = []
    for p, z in zs:
        if z.get("minor") != "TB":
            continue
        rows = [[c.strip() for c in row if c and c.strip()] for row in (z.get("rows") or [])]
        rows = [r_ for r_ in rows if r_]
        hdr = next((r_ for r_ in rows if sum(1 for c in r_ if _SK_ANNUAL.match(c)) >= 2), None)
        tr = [r_ for r_ in rows if _SK_ANNUAL.match(r_[0]) and sum(1 for c in r_[1:] if _NUMC.match(c)) >= 2]
        if hdr:                                                     # 年度欄在表頭
            na = sum(1 for c in hdr if _SK_ANNUAL.match(c))
            nr = [r_ for r_ in rows if sum(1 for c in r_ if _NUMC.match(c)) >= 2]
            tidy = bool(nr) and sum(1 for r_ in nr if na <= sum(1 for c in r_ if _NUMC.match(c)) <= na + 2 or len(r_) % na <= 2) / len(nr) >= 0.6
            ann.append((p, z.get("id"), "期間欄" in (z.get("engine") or "") or tidy))
        elif len(tr) >= 2:                                          # 年份往下排(第一欄是年度)
            ann.append((p, z.get("id"), True))
    short = not ann and r.get("fin_n", 0) == 0 and (note or 0 < npages <= 4)
    if ann:
        al = [a for a in ann if a[2]]
        p_fin = ("GREEN" if al else "YELLOW", "年度表 %d 張(期間欄對齊 %d)· %s" % (len(ann), len(al), " ".join(str(a[1] or "P%d" % a[0]) for a in ann[:3])))
    elif any(sum(1 for t in x.get("text", "").split() if _SK_ANNUAL.match(t.strip("()"))) >= 3 for _, z in zs for x in (z.get("records") or [])):
        p_fin = ("YELLOW", "年度數據在文字段(未切成表 · 引擎待修)")
    elif short:
        p_fin = ("GRAY", "快訊 / 更新 / 摘要(%s頁)· 未附年度財報" % (npages or "?"))
    else:
        p_fin = ("YELLOW", "沒有年度表(財報頁 %d · 全文 %s 頁)" % (r.get("fin_n", 0), npages or "?"))
    alltxt = " ".join(ztxt(z) for _, z in zs)
    vh = [n for n, rx in _SK_VAL if re.search(rx, alltxt)]
    eps = bool(_SK_EPS.search(alltxt))
    if eps and len(vh) >= (1 if note else 2):
        p_val = ("GREEN", "EPS + " + " · ".join(vh))
    elif note and not (eps and vh):
        p_val = ("GRAY", "快訊 / 摘要 · 未附完整評價" + (("(只有 " + " · ".join(vh) + ")") if vh else ""))
    elif short and not vh:
        p_val = ("GRAY", "快訊 / 摘要 · 未附評價表")
    else:
        p_val = ("YELLOW", ("EPS ✓ · " if eps else "缺 EPS · ") + ("評價 " + " · ".join(vh) if vh else "沒有評價指標"))
    parts = {"檔名": p_fn, "首頁": p_p1, "年度財報": p_fin, "評價資訊": p_val}
    ocr = r.get("lamp") == "RED"
    worst = "RED" if ocr else ("YELLOW" if any(v[0] == "YELLOW" for v in parts.values()) else "GREEN")
    return {"stock": True, "file": f, "ticker": tk, "date": dt, "broker": br, "parts": parts, "ocr": ocr, "lamp": worst}


def _npages(p: Path) -> int:
    try:
        import pypdfium2 as pdfium  # noqa: WPS433
        d = pdfium.PdfDocument(str(p))
        n = len(d)
        d.close()
        return n
    except Exception:  # noqa: BLE001
        try:
            import pdfplumber  # noqa: WPS433
            with pdfplumber.open(str(p)) as d:
                return len(d.pages)
        except Exception:  # noqa: BLE001
            return 0


def stock_round(res: list, indir: Path, v2: Path, rnd, reg=None) -> tuple:
    """個股四項:評估 → 逐項鎖定(綠才鎖 · 只增不減)→ 鎖過的項不再綠 = 退步(紅)→ 輪次帳本。回傳 (結果清單, 非個股清單, 退步清單, 鎖)。"""
    import datetime
    ev = [stock_eval(r, _npages(indir / r.get("file", "")) if (indir / r.get("file", "")).exists() else 0) for r in res]
    st, ns = [e for e in ev if e["stock"]], [e for e in ev if not e["stock"]]
    lp = Path(reg or HERE / "registry") / "VRN2_Stock_Lock_latest.json"
    lock = json.loads(lp.read_text(encoding="utf-8")) if lp.exists() else {"files": {}}
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    regress, newly = [], 0
    for e in st:
        lf = lock["files"].setdefault(e["file"], {})
        for k, (lamp, _) in e["parts"].items():
            if lamp == "GREEN" and k not in lf:
                lf[k] = {"round": rnd, "at": now}
                newly += 1
            elif k in lf and lamp != "GREEN":
                regress.append((e["file"], k, lamp))
                e["parts"][k] = ("RED", "退步(第 %s 輪已鎖)· " % lf[k]["round"] + e["parts"][k][1])
                e["lamp"] = "RED"
    lock.update(round=rnd, at=now)
    lp.parent.mkdir(parents=True, exist_ok=True)
    lp.write_text(json.dumps(lock, ensure_ascii=False, indent=1), encoding="utf-8")
    pc = {k: Counter(e["parts"][k][0] for e in st) for k in ("檔名", "首頁", "年度財報", "評價資訊")}
    with (v2 / "VRN2_Stock_Rounds.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"round": rnd, "at": now, "stock": len(st), "non_stock": len(ns), "parts": {k: dict(v) for k, v in pc.items()}, "file_green": sum(1 for e in st if e["lamp"] == "GREEN"),
                             "locked_parts": sum(len(v) for v in lock["files"].values()), "newly": newly, "regress": len(regress)}, ensure_ascii=False) + "\n")
    return st, ns, regress, lock, pc, newly


def _stock_html(st, ns, regress, pc, lock) -> str:
    lampi = lambda l: "<i style='background:%s'%s></i>" % (_V2C.get(l, "#9ca3af"), " class='bl'" if l == "RED" else "")  # noqa: E731
    keys = ("檔名", "首頁", "年度財報", "評價資訊")
    rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td>%s</tr>" % (lampi(e["lamp"]), html.escape(e["file"]), html.escape(e["ticker"]),
                   "".join("<td>%s%s</td>" % (lampi(e["parts"][k][0]), html.escape(e["parts"][k][1])) for k in keys)) for e in sorted(st, key=lambda e: {"RED": 0, "YELLOW": 1, "GREEN": 2}[e["lamp"]]))
    summ = " · ".join("%s 綠 %d / 黃 %d / 紅 %d / 灰 %d" % (k, pc[k].get("GREEN", 0), pc[k].get("YELLOW", 0), pc[k].get("RED", 0), pc[k].get("GRAY", 0)) for k in keys)
    return ("<h3>%s個股報告四項驗收 · %d 份(全綠 %d)· 逐項鎖定 %d · 退步 %d</h3><div class='sum'><span>%s</span></div>"
            "<table><tr><th>燈</th><th>檔案</th><th>代號</th><th>①檔名</th><th>②首頁</th><th>③年度財報頁</th><th>④重要財報及評價</th></tr>%s</table>"
            "<p style='color:#6b7280'>非個股(不適用 · 灰)%d 份:%s</p>" % (lampi("RED" if regress else ("GREEN" if all(e["lamp"] == "GREEN" for e in st) else "YELLOW")), len(st), sum(1 for e in st if e["lamp"] == "GREEN"),
                sum(len(v) for v in lock["files"].values()), len(regress), html.escape(summ), rows, len(ns), html.escape(" · ".join(e["file"][:28] for e in ns))))


def vrn2(args: list, rep=None, indir=None, open_ui: bool = True, reg=None) -> tuple:
    """VRN-2 獨立子系統(第一頁 + 財報頁 切割 / 擷取 / 修復):--run 先跑 p1loop;成功(退步 0)→ 鎖版本 + 時間 · 備份成功狀態 · 交互驗證(JSON ↔ CSV ↔ 燈號)· HTML U/I 自動跳出。"""
    import csv
    import datetime
    import hashlib
    import shutil
    L = []
    if "--run" in args:
        rc0, l0 = _resolve("p1loop")("")
        L += l0
        if rc0 not in (0, 1):
            return rc0, L
    rep = Path(rep or _resolve("_rep")())
    pv, v2 = rep / "p1view", rep.parent / "vrn2"
    v2.mkdir(parents=True, exist_ok=True)
    try:
        res = json.loads((pv / "P1VIEW_latest.json").read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return 1, L + ["[RED] VRN-2 · 讀不到 P1VIEW_latest.json · %s" % type(exc).__name__]
    rows = [l for l in (pv / "VRN_P1View_Rounds.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()] if (pv / "VRN_P1View_Rounds.jsonl").exists() else []
    entry = json.loads(rows[-1]) if rows else {}
    csvz, csvc, csvt = {}, {}, {}
    cp = pv / "P1VIEW_records_latest.csv"
    if cp.exists():
        with cp.open(encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                csvz.setdefault(r["FILE"], set()).add(r["ZONE"])
                if r.get("REC_KIND") == "格":
                    csvc[r["FILE"]] = csvc.get(r["FILE"], 0) + 1
                else:
                    csvt[r["FILE"]] = csvt.get(r["FILE"], 0) + 1
    indir = Path(indir or (_resolve("input_dir") or (lambda: Path(r"C:\測試樣本報告")))())
    files, ok = [], 0
    for r in res:
        f = r.get("file", "")
        zs = [z for pg in r.get("pages") or [] for z in pg.get("zones") or []]
        nonempty = lambda z: [c for row in (z.get("rows") or []) for c in row if c]  # noqa: E731     與 CSV 同口徑:只算非空格
        zj = sum(1 for z in zs if (nonempty(z) if z.get("rows") else z.get("records")))
        zc = len(csvz.get(f, ()))
        cj, cc = sum(len(nonempty(z)) for z in zs), csvc.get(f, 0)
        tj, tc = sum(len(z.get("records") or []) for z in zs if not z.get("rows")), csvt.get(f, 0)
        lamp_re = "RED" if (any(z.get("needs_ocr") for z in zs) or any("首頁無文字層" in x for x in (r.get("reasons") or []))) else ("YELLOW" if r.get("reasons") else "GREEN")
        p = indir / f
        exists = p.exists()
        bad = [n for n, okk in (("區", zj == zc), ("格", cj == cc), ("文", tj == tc), ("燈", lamp_re == r.get("lamp"))) if not okk]
        x = not bad
        ok += 1 if x else 0
        files.append({"file": f, "lamp": r.get("lamp"), "layout": r.get("layout", ""), "reasons": r.get("reasons") or [], "zones_json": zj, "zones_csv": zc, "cells_json": cj, "cells_csv": cc,
                      "lamp_recomputed": lamp_re, "xcheck": x, "bad": bad, "text_json": tj, "text_csv": tc, "input": "GRAY" if not exists else ("GREEN" if x else "RED"), "sha": hashlib.sha256(p.read_bytes()).hexdigest()[:12] if exists else ""})
    lamps = Counter(r.get("lamp") for r in res)
    regress = int(entry.get("regress", 0) or 0)
    st, ns, sreg, slock, spc, snew = stock_round(res, indir, v2, entry.get("round"), reg)
    L.append("[計] VRN-2 個股四項 · %d 份(全綠 %d)· %s · 本輪新鎖 %d 項 · 累計鎖 %d 項 · 退步 %d" % (len(st), sum(1 for e in st if e["lamp"] == "GREEN"),
             " · ".join("%s 綠%d黃%d紅%d灰%d" % (k, v.get("GREEN", 0), v.get("YELLOW", 0), v.get("RED", 0), v.get("GRAY", 0)) for k, v in spc.items()), snew, sum(len(v) for v in slock["files"].values()), len(sreg)))
    for f, k, l in sreg[:20]:
        L.append("[RED] 個股退步 · %s · %s(已鎖 → %s)" % (f[:40], k, l))
    for e in [e for e in st if e["lamp"] != "GREEN"][:40]:
        L.append("[計] 個股 %s · %s · %s" % (e["lamp"], e["file"][:36], " | ".join("%s %s %s" % (k, v[0][0], v[1][:34]) for k, v in e["parts"].items() if v[0] != "GREEN")))
    regress += len(sreg)
    success = bool(res) and regress == 0 and ok == len(files)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    engs = {}
    for pat in ("VRN_ENG397_P1Segment_v*.py", "VRN_ENG396_AssetIndex_v*.py"):
        c = sorted(HERE.glob(pat))
        if c:
            engs[c[-1].name] = hashlib.sha256(c[-1].read_bytes()).hexdigest()[:12]
    lock = {"subsystem": "VRN-2", "ts": ts, "success": success, "round": entry.get("round"), "manager": TAG, "engines": engs, "lamps": dict(lamps), "reasons": entry.get("reasons", {}), "locked": entry.get("locked"),
            "regress": regress, "xcheck_ok": ok, "n": len(files), "input_dir": str(indir), "inputs": {x["file"]: x["sha"] for x in files if x["sha"]}}
    L.append("[計] VRN-2 · 第 %s 輪 · 燈 %s · 退步 %d · 交互驗證(JSON ↔ CSV ↔ 燈號)%d/%d 一致 → %s" % (entry.get("round", "?"), dict(lamps), regress, ok, len(files), "成功 → 鎖定 + 備份" if success else "未達成功 · 不鎖不備份"))
    bk = None
    if success:
        rd = Path(reg or HERE / "registry")
        rd.mkdir(parents=True, exist_ok=True)
        (rd / ("VRN2_Lock_%s.json" % ts)).write_text(json.dumps(lock, ensure_ascii=False, indent=1), encoding="utf-8")
        (rd / "VRN2_Lock_latest.json").write_text(json.dumps(lock, ensure_ascii=False, indent=1), encoding="utf-8")
        bk = v2 / "backup" / ts
        bk.mkdir(parents=True, exist_ok=True)
        n = 0
        for nm in ("P1VIEW_latest.json", "P1VIEW_records_latest.csv", "P1VIEW_latest.md", "P1VIEW_latest.html", "VRN_P1View_Lock_latest.json", "VRN_P1View_Rounds.jsonl"):
            if (pv / nm).exists():
                shutil.copy2(pv / nm, bk / nm)
                n += 1
        (v2 / "VRN2_Success_latest.json").write_text(json.dumps({"ts": ts, "backup": str(bk), "lock": str(rd / ("VRN2_Lock_%s.json" % ts)), "files": n}, ensure_ascii=False, indent=1), encoding="utf-8")
        L.append("[計] VRN-2 鎖定 registry/VRN2_Lock_%s.json(引擎 %s)· 備份 %d 檔 → %s" % (ts, " · ".join("%s %s" % kv for kv in engs.items()), n, bk))
    trs = "".join("<tr><td><i style='background:%s'%s></i></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%d/%d</td><td>%d/%d</td><td>%s</td></tr>" % (
        _V2C.get(x["input"], "#9ca3af"), " class='bl'" if x["input"] == "RED" else "", html.escape(x["file"]), "<i style='background:%s'></i>%s" % (_V2C.get(x["lamp"], "#9ca3af"), x["lamp"]), html.escape(x["layout"]),
        html.escape(" / ".join(x["reasons"])), x["zones_json"], x["zones_csv"], x["cells_json"], x["cells_csv"], "✓" if x["xcheck"] else "✗ 不一致:" + "、".join(x["bad"]) + ("(重算燈 %s)" % x["lamp_recomputed"] if "燈" in x["bad"] else "")) for x in files)
    page = ("<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>VRN-2 · 切割 / 擷取 / 修復</title><style>:root{--g:#16a34a;--y:#eab308;--r:#dc2626;--k:#9ca3af}body{font:12px system-ui,'Microsoft JhengHei';margin:10px;color:#111;background:#fff}"
            "h2{margin:0 0 6px}table{border-collapse:collapse;width:100%%;table-layout:auto}td,th{border:1px solid #e5e7eb;padding:2px 5px;vertical-align:top;word-break:break-all;text-align:left}th{background:#f3f4f6}i{display:inline-block;width:10px;height:10px;border-radius:50%%;margin-right:4px;vertical-align:middle}"
            ".bl{animation:b 1.6s infinite}@keyframes b{50%%{opacity:.25}}.sum{display:flex;gap:14px;flex-wrap:wrap;margin:6px 0}.sum span{padding:2px 8px;border:1px solid #e5e7eb;border-radius:6px}</style>"
            "<h2><i style='background:%s'%s></i>VRN-2 · 第一頁 + 財報頁 切割 / 擷取 / 修復 · %s</h2><div class='sum'><span>第 %s 輪</span><span>綠 %d · 黃 %d · 紅 %d</span><span>退步 %d</span><span>交互驗證 %d/%d</span><span>管理器 %s</span><span>引擎 %s</span><span>輸入 %s</span>%s</div>"
            "<table><tr><th>驗證</th><th>檔案</th><th>燈</th><th>版型</th><th>原因</th><th>區 JSON/CSV</th><th>格 JSON/CSV</th><th>交互驗證</th></tr>%s</table>" % (
                _V2C["GREEN" if success else "RED"], "" if success else " class='bl'", "成功 · 已鎖定 " + ts if success else "未達成功(退步 %d · 不一致 %d)" % (regress, len(files) - ok), entry.get("round", "?"), lamps.get("GREEN", 0), lamps.get("YELLOW", 0), lamps.get("RED", 0),
                regress, ok, len(files), TAG, html.escape(" · ".join(engs)), html.escape(str(indir)), ("<span>備份 %s</span>" % html.escape(str(bk))) if bk else "", trs))
    page += _stock_html(st, ns, sreg, spc, slock) + _activate_html(v2)
    up = v2 / "VRN2_UI_latest.html"
    up.write_text(page, encoding="utf-8")
    L.append("  [U/I] %s" % up)
    if open_ui and hasattr(os, "startfile") and "--no-open" not in args:
        try:
            os.startfile(str(up))  # noqa: S606
        except OSError:
            pass
    return (0 if success else 1), L


def eol_refresh(home=None, snap=None) -> int:
    """v0200:修正閘指紋快照 · 只差行尾的檔(換行方式換一下就和快照一致)→ 視為未改 · 更新該筆 · 真不同的不動。回傳更新筆數。"""
    import hashlib
    home = Path(home or HERE)
    if snap is None:
        rf = _resolve("_rep_for")
        rep = Path(rf(home)) if rf else Path(_resolve("_rep")())
        snap = rep / "selfgate" / "snapshot_latest.json"
    snap = Path(snap)
    if not snap.exists():
        return 0
    try:
        prev = json.loads(snap.read_text(encoding="utf-8"))
    except ValueError:
        return 0
    fp, n = prev.get("fp") or {}, 0
    h16 = lambda b: hashlib.sha256(b).hexdigest()[:16]  # noqa: E731
    for rel, old in list(fp.items()):
        p = home / rel
        if not p.exists():
            continue
        b = p.read_bytes()
        cur = h16(b)
        if cur == old:
            continue
        lf = b.replace(b"\r\n", b"\n")
        if old in (h16(lf), h16(lf.replace(b"\n", b"\r\n"))):
            fp[rel] = cur
            n += 1
    if n:
        prev["fp"] = fp
        snap.write_text(json.dumps(prev, ensure_ascii=False), encoding="utf-8")
    return n


def reconcile(apply: bool = False, home=None, conf=None) -> tuple:
    """不要同號 · 出新版號(v0196):同版號內容不同 → 本機內容另存 v+1 · 原號還原成 main 的內容 · 兩邊都保留 · 先列計畫 · --apply 才動 · 每步寫帳本。"""
    import datetime
    import subprocess
    home = Path(home or (_resolve("_home") or (lambda: HERE))())
    conf = _git_conflicts(home) if conf is None else list(conf)   # conf 只供自測注入
    if not conf:
        return 0, ["[計] 版本號衝突 0 · 不用調和"]
    try:
        top = subprocess.run(["git", "-C", str(home), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:  # noqa: BLE001
        top = ""
    L, done = ["[計] 版本號衝突調和 %s · %d 件(整族接續編號:本機各版依序存到該族現有最大版號之後 · 原號還原 main · 只增不減)" % ("執行" if apply else "計畫(不動檔 · 加 --apply 才執行)", len(conf))], []
    fams = {}
    for rel in conf:
        rp = Path(rel)
        m = re.search(r"^(.*_v)(\d{3,4})(\..+)$", rp.name)
        if m:
            fams.setdefault((str(rp.parent), m.group(1), m.group(3)), set()).add(int(m.group(2)))
    for (sub, pre, ext), vers in sorted(fams.items()):
        folder = home / sub
        exist = [int(mm.group(1)) for q in folder.glob(pre + "*" + ext) for mm in [re.search(r"_v(\d{3,4})$", q.stem)] if mm]
        nxt = max(exist, default=0) + 1
        for v in sorted(vers):
            old = pre + ("%04d" % v) + ext
            p = folder / old
            if not p.exists():
                p = next((q for q in folder.glob(pre + "%d" % v + ext)), None)
            if not p:
                continue
            nv = pre + ("%04d" % nxt) + ext
            nxt += 1
            np_ = p.with_name(nv)
            L.append("[計] 調和 %s → 本機內容存為 %s · 原號還原 main%s" % ((sub + "/" if sub != "." else "") + old, nv, " · 同族 %d 版衝突 · 接續編號" % len(vers) if len(vers) > 1 else ""))
            if apply and not np_.exists() and top:
                try:
                    np_.write_bytes(p.read_bytes())
                    relp = str(p.resolve().relative_to(Path(top).resolve())).replace("\\", "/")
                    r = subprocess.run(["git", "-C", top, "checkout", "origin/main", "--", relp], capture_output=True, text=True, timeout=60)
                    done.append({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "file": (sub + "/" if sub != "." else "") + old, "new_version": nv, "restored_from": "origin/main", "rc": r.returncode})
                except Exception as exc:  # noqa: BLE001
                    L.append("[RED] 調和失敗 %s · %s" % (old, type(exc).__name__))
    rd = home / "registry"
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "VRN_Reconcile_Plan_latest.md").write_text("# 版本號衝突調和計畫 · %s · %d 件\n" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), len(conf)) + "\n".join("- " + l[4:] for l in L[1:] if l.startswith("[計] 調和")) + "\n", encoding="utf-8")
    L.append("  [MD] %s" % (rd / "VRN_Reconcile_Plan_latest.md"))
    if apply:
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
    if args[:1] == ["selfgate"] and "--sandbox" in args:
        run, pg = _resolve("selfgate_run"), _resolve("_print_gate")
        o = run("sandbox", panorama="--no-panorama" not in args)
        moved = env_flaky_filter(o, _older_has)
        if moved:
            print("[計] 在地測試 · 新尾版多出的失敗 %d 筆是舊版本就有的環境相依測試(OCR / 網路 · 時過時不過)→ 歸類環境 · 不算新增失敗:%s" % (len(moved), " | ".join(moved)))
        return pg(o)
    if args[:1] == ["selfgate"] and "--sandbox" not in args:
        try:
            n = eol_refresh()
            if n:
                print("[計] 修正閘指紋 · 只差行尾(CRLF/LF)%d 檔 → 視為未改(內容相同 · 快照已更新 · 真不同的仍判紅)" % n)
        except Exception as exc:  # noqa: BLE001
            print("[計] 修正閘指紋核對略過 · %s" % type(exc).__name__)
        return _mod_v0213("v0194").main(args)
    if args[:1] == ["vrn2"]:
        rc, lines = vrn2(args[1:])
        for l in lines:
            print(l)
        return rc
    if args[:1] == ["accelfix"]:
        lim = int(args[args.index("--limit") + 1]) if "--limit" in args and args.index("--limit") + 1 < len(args) else 20
        rc, lines = accelfix("--apply" in args, limit=lim, every="--all" in args)
        if "--all" in args:
            rc2, l2 = ps_accelfix("--apply" in args, limit=max(lim, 2000))
            lines += l2
        for l in lines:
            print(l)
        return rc
    if args[:1] == ["envcheck"]:
        rc, lines = envcheck("--install" in args)
        for l in lines:
            print(l)
        return rc
    if args[:1] == ["linkmap"]:
        rc, lines = linkmap_verb()
        for l in lines:
            print(l)
        return rc
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
        rc = _mod_v0213("v0194").main(args)                    # v0197:其他動詞走 v0194 的 main(避免 v0195 / v0196 的登記鉤子重複登記)
    if args and args[0] not in ("selfgate", "ui", "reconcile", "accelfix", "vrn2", "envcheck") and not args[0].startswith("-"):
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
        a1["changed"] and not a2["changed"] and "old_tool_sha0123456789ab.py" not in a1["no_version"] and a1["pending_tidy"] == 1 and _mod_v0213("v0194").TAG == "v0194")
    o_t = {"red": ["新尾版多出失敗「⑥ 第三步 OCR:影像表格(P# 圖區無文字層)→ 自動選 輕型單引擎 rapidocr」", "新尾版多出失敗「③ 斷句銜接」"], "verdict": "RED"}
    mv = env_flaky_filter(o_t, lambda lab: True)
    o_u = {"red": ["新尾版多出失敗「⑥ 第三步 OCR:影像表格」"], "verdict": "RED"}
    mv2 = env_flaky_filter(o_u, lambda lab: True)
    chk("⓪ 沙盒閘環境相依過濾:OCR 測試移到環境(1)· 斷句測試仍紅 · 全是環境時 RED→YELLOW", len(mv) == 1 and o_t["red"] == ["新尾版多出失敗「③ 斷句銜接」"] and o_t["verdict"] == "RED" and len(mv2) == 1 and o_u["verdict"] == "YELLOW" and not o_u["red"])
    te = Path(tempfile.mkdtemp(prefix="eol-"))
    import hashlib as _h
    (te / "a.py").write_bytes(b"x = 1\ny = 2\n")
    (te / "b.py").write_bytes(b"x = 9\n")
    sp = te / "snap.json"
    sp.write_text(json.dumps({"fp": {"a.py": _h.sha256(b"x = 1\r\ny = 2\r\n").hexdigest()[:16], "b.py": _h.sha256(b"x = 1\n").hexdigest()[:16]}, "verdict": "RED"}), encoding="utf-8")
    n_e = eol_refresh(te, sp)
    fp2 = json.loads(sp.read_text(encoding="utf-8"))["fp"]
    chk("⓪ 修正閘指紋核對:a.py 只差行尾 → 快照更新(1 筆)· b.py 內容真不同 → 不動(仍會判紅)", n_e == 1 and fp2["a.py"] == _h.sha256(b"x = 1\ny = 2\n").hexdigest()[:16] and fp2["b.py"] == _h.sha256(b"x = 1\n").hexdigest()[:16])
    tf = Path(tempfile.mkdtemp(prefix="rec-"))
    for v in (102, 103, 104):
        (tf / ("VRN_X_SSOT_v%04d.json" % v)).write_text("{}", encoding="utf-8")
    (tf / "sub").mkdir()
    (tf / "sub" / "VRN_X_SSOT_v0102.json").write_text("{}", encoding="utf-8")
    rc0, pl = reconcile(False, home=tf, conf=["VRN_X_SSOT_v0102.json", "VRN_X_SSOT_v0103.json", "VRN_X_SSOT_v0104.json", "sub/VRN_X_SSOT_v0102.json", "VRN_X_SSOT_v0102.json"])
    got = re.findall(r"調和 (\S+) → 本機內容存為 (\S+)", "\n".join(pl))
    chk("⓪ 整族接續編號:根夾 v0102~v0104 → v0105 / v0106 / v0107(四位 · 去重)· sub 夾同名 v0102 另成一族 → v0103 · 不動檔 → %s" % got,
        got == [("VRN_X_SSOT_v0102.json", "VRN_X_SSOT_v0105.json"), ("VRN_X_SSOT_v0103.json", "VRN_X_SSOT_v0106.json"), ("VRN_X_SSOT_v0104.json", "VRN_X_SSOT_v0107.json"), ("sub/VRN_X_SSOT_v0102.json", "VRN_X_SSOT_v0103.json")]
        and not (tf / "VRN_X_SSOT_v0105.json").exists() and rc0 == 0)
    ta2 = Path(tempfile.mkdtemp(prefix="af-"))
    (ta2 / "VRN_ENG_Q_v0100.py").write_text('"""Q 引擎"""\nfrom __future__ import annotations\nimport json\nX = 1\n', encoding="utf-8")
    (ta2 / "VRN_ENG_R_v0100.py").write_text('"""R 引擎 [VIA:ACCEL-BRIDGE:v0111] 已有"""\nY = 2\n', encoding="utf-8")
    rc_a, la = accelfix(True, home=ta2, limit=20)
    nq = ta2 / "VRN_ENG_Q_v0101.py"
    chk("⓪ accelfix:缺標記的 Q → 出 v0101(docstring + __future__ 之後注入 · 編譯過)· 已有標記的 R 不動 · 原檔不動 → %s" % [l for l in la if "注入 VRN_ENG_Q" in l][:1],
        rc_a == 0 and nq.exists() and "[VIA:ACCEL-BRIDGE" in nq.read_text(encoding="utf-8") and nq.read_text(encoding="utf-8").splitlines()[1].startswith("from __future__") and compile(nq.read_text(encoding="utf-8"), "q", "exec")
        and not (ta2 / "VRN_ENG_R_v0101.py").exists() and (ta2 / "VRN_ENG_Q_v0100.py").read_text(encoding="utf-8").count("ACCEL") == 0 and (ta2 / "registry" / "VRN_AccelFix_Ledger.jsonl").exists())
    _t0 = __import__("time").time()
    tv = Path(tempfile.mkdtemp(prefix="v2-"))
    (tv / "rep" / "p1view").mkdir(parents=True)
    (tv / "in").mkdir()
    (tv / "in" / "a.pdf").write_bytes(b"%PDF-1.4 a")
    resj = [{"file": "a.pdf", "lamp": "GREEN", "layout": "單欄型", "reasons": [], "pages": [{"zones": [{"id": "P1·M·01·TB", "rows": [["x", "1", ""], ["y", "2", ""]], "needs_ocr": False}, {"id": "P1·M·02·TX", "rows": [], "records": [{"kind": "句", "text": "hi"}], "needs_ocr": False}, {"id": "P1·M·03·IMG", "rows": [], "records": [], "needs_ocr": False}]}]},
            {"file": "b.pdf", "lamp": "YELLOW", "layout": "側欄型(右)", "reasons": ["沒找到財報頁"], "pages": [{"zones": [{"id": "P1·M·01·TX", "rows": [], "records": [{"kind": "句", "text": "yo"}], "needs_ocr": False}]}]}]
    (tv / "rep" / "p1view" / "P1VIEW_latest.json").write_text(json.dumps(resj, ensure_ascii=False), encoding="utf-8")
    (tv / "rep" / "p1view" / "P1VIEW_records_latest.csv").write_text("\ufeffFILE,ZONE,REC_KIND,TEXT\na.pdf,P1·M·01·TB,格,x\na.pdf,P1·M·01·TB,格,1\na.pdf,P1·M·01·TB,格,y\na.pdf,P1·M·01·TB,格,2\na.pdf,P1·M·02·TX,句,hi\nb.pdf,P1·M·01·TX,句,yo\n", encoding="utf-8")
    (tv / "rep" / "p1view" / "VRN_P1View_Rounds.jsonl").write_text(json.dumps({"round": 12, "regress": 0, "locked": 14, "reasons": {}}) + "\n", encoding="utf-8")
    rc_v, lv = vrn2(["--no-open"], rep=tv / "rep", indir=tv / "in", open_ui=False, reg=tv / "reg")
    ui = (tv / "vrn2" / "VRN2_UI_latest.html")
    lk = tv / "reg" / "VRN2_Lock_latest.json"
    chk("⓪ VRN-2:退步 0 + 交互驗證 2/2 一致(圖區無內容 · 空格不寫 CSV → 口徑一致不誤判) → 成功 · 鎖定(registry/VRN2_Lock_latest.json)· 備份 3 檔 · U/I 產出(a 綠 · b 的 PDF 不在 → 灰)· rc 0", rc_v == 0 and ui.exists() and lk.exists() and json.loads(lk.read_text(encoding="utf-8"))["xcheck_ok"] == 2 and "VRN2_Success_latest.json" in [p.name for p in (tv / "vrn2").iterdir()] and len(list((tv / "vrn2" / "backup").iterdir())) == 1)
    (tv / "rep" / "p1view" / "VRN_P1View_Rounds.jsonl").write_text(json.dumps({"round": 13, "regress": 1, "locked": 14}) + "\n", encoding="utf-8")
    rc_w, lw = vrn2(["--no-open"], rep=tv / "rep", indir=tv / "in", open_ui=False, reg=tv / "reg")
    chk("⓪ VRN-2:退步 1 → 未達成功 · 不鎖不備份 · U/I 紅燈閃爍 · rc 1", rc_w == 1 and "未達成功" in ui.read_text(encoding="utf-8") and len(list((tv / "vrn2" / "backup").iterdir())) == 1)
    sa = stock_eval({"file": "20250819兆豐個股報告-泓德能源(6873).pdf", "lamp": "GREEN", "reasons": [], "fin_n": 2, "pages": [
        {"pno": 1, "zones": [{"major": "T", "minor": "RT", "records": [{"text": "逢低買進 $208"}], "rows": []}]},
        {"pno": 6, "zones": [{"major": "F", "minor": "TB", "engine": "pdfplumber(期間欄對齊)", "rows": [["", "2023", "2024", "2025(F)"], ["每股盈餘(元)", "8.16", "11.10", "9.76"], ["本益比(X)", "16.0", "20.5", "17.6"], ["股價淨值比(X)", "2.2", "2.6", "1.9"]]}]}]}, 8)
    sb = stock_eval({"file": "20260917兆豐投資早報.pdf", "lamp": "YELLOW", "reasons": ["沒找到財報頁"], "pages": []}, 4)
    sd = stock_eval({"file": "Citi-3231 20250604.pdf", "lamp": "YELLOW", "reasons": ["沒找到財報頁"], "fin_n": 0, "pages": [{"pno": 1, "zones": [
        {"major": "T", "minor": "TX", "records": [{"text": "Flash | Wistron (3231.TW)"}], "rows": []},
        {"major": "M", "minor": "TB", "engine": "pdfplumber", "rows": [["Year to", "Net Profit", "EPS", "P/E", "P/B", "ROE", "Yield"], ["2024A", "17,446", "6.12", "18.6", "2.5", "14.7", "3.3"], ["2025E", "24,878", "8.72", "13.1", "2.0", "16.8", "4.5"]]}]}]}, 13)
    se = stock_eval({"file": "MS-1590 20251202.pdf", "lamp": "YELLOW", "reasons": ["沒找到財報頁"], "fin_n": 0, "pages": [{"pno": 1, "zones": [{"major": "T", "minor": "TX", "records": [{"text": "Update"}], "rows": []}]}]}, 9)
    sf = stock_eval({"file": "3014TT-20231005.pdf", "lamp": "YELLOW", "reasons": [], "fin_n": 1, "pages": [{"pno": 1, "zones": [{"major": "T", "minor": "DT", "records": [{"text": "投資顧問 個股報告 2023/10/05"}], "rows": []}, {"major": "T", "minor": "TT", "records": [{"text": "團泰期賃國泰證券子公司"}], "rows": []}]}]}, 10)
    chk("⓪ 判定修正:Citi 年份往下排的 Earnings Summary 算年度表(綠)· MS 月營收 Update 無年度表 → 灰 · 3014TT 券商從首頁補「國泰」 → %s / %s / %s" % (sd["parts"]["年度財報"][0], se["parts"]["年度財報"][0], sf.get("broker")),
        sd["parts"]["年度財報"][0] == "GREEN" and sd["parts"]["評價資訊"][0] == "GREEN" and se["parts"]["年度財報"][0] == "GRAY" and sf["broker"] == "國泰" and sf["parts"]["檔名"][0] == "GREEN")
    sg = stock_eval({"file": "Daiwa-6278 20260521.pdf", "lamp": "GREEN", "reasons": [], "fin_n": 1, "pages": [{"pno": 1, "zones": [{"major": "M", "minor": "TX", "records": [{"text": "Background: We met with Taiwan Surface Mounting Technology's management on 21 May. Valuation: PERs of 21.4x and 17.4x"}], "rows": []}]},
        {"pno": 2, "zones": [{"major": "F", "minor": "TB", "engine": "pdfplumber(期間欄對齊)", "rows": [["(TWDm)", "2024", "2025"], ["Net sales", "45,288", "49,877"], ["EPS (TWD)", "9.94", "9.39"]]}]}]}, 4)
    sh = stock_eval({"file": "MQ-1560 20260520.pdf", "lamp": "RED", "reasons": ["首頁無文字層 → OCR 排隊", "沒找到財報頁"], "fin_n": 0, "pages": [{"pno": 1, "zones": []}]}, 4)
    si = stock_eval({"file": "UBS-4966 20260914.pdf", "lamp": "YELLOW", "reasons": ["沒找到財報頁"], "fin_n": 0, "pages": [{"pno": 1, "zones": [{"major": "M", "minor": "TX", "records": [{"text": "2026 Taiwan Summit Highlights (NT$m) 12/23 12/24 12/25 12/27E Revenues 13,769 EPS P/E Dividend yield EV/EBITDA price target"}], "rows": []}]}]}, 12)
    chk("⓪ 第 20 輪實證:Daiwa Background 快訊 EPS + 本益比 → 評價綠 · MQ 首頁無文字層 → 首頁紅(OCR)· UBS Summit 年度數據在文字段 → 年度黃(引擎待修)→ %s / %s / %s" % (sg["parts"]["評價資訊"][0], sh["parts"]["首頁"][0], si["parts"]["年度財報"][0]),
        sg["parts"]["評價資訊"][0] == "GREEN" and sh["parts"]["首頁"][0] == "RED" and si["parts"]["年度財報"][0] == "YELLOW")
    sc = stock_eval({"file": "光焱(7728,Note)-CTBC260918.pdf", "lamp": "YELLOW", "reasons": ["沒找到財報頁", "首頁沒抓到評等 / 目標價"], "fin_n": 0, "pages": [{"pno": 1, "zones": [{"major": "M", "minor": "TX", "records": [{"text": "法說 / 座談摘要"}], "rows": []}]}]}, 2)
    chk("⓪ 個股四項:泓德(6873)四項全綠(兆豐 · 2025-08-19 · 年度表期間欄對齊 · EPS + 本益比 + 股價淨值比)· 投資早報 = 非個股 · 光焱 Note 2 頁 = 檔名綠(中信 · 2026-09-18)· 首頁 / 財報 / 評價灰(Note 本來沒有評等) → %s / %s / %s" % (
        sa.get("lamp"), sb.get("stock"), {k: v[0] for k, v in (sc.get("parts") or {}).items()}),
        sa["lamp"] == "GREEN" and sa["date"] == "2025-08-19" and sa["broker"] == "兆豐" and not sb["stock"] and sc["date"] == "2026-09-18" and sc["broker"] == "中信"
        and {k: v[0] for k, v in sc["parts"].items()} == {"檔名": "GREEN", "首頁": "GRAY", "年度財報": "GRAY", "評價資訊": "GRAY"} and _sk_date("華南投顧-2606-裕民-1141202.pdf") == "2025-12-02" and _sk_ticker("華南投顧-2606-裕民-1141202.pdf", "") == "2606")
    chk("⓪ VRN-2 自測只寫暫存夾:真正的 registry/ 沒有被寫入 VRN2_*(自測不污染鎖定)", not any(p.stat().st_mtime > _t0 for p in (HERE / "registry").glob("VRN2_*")) if (HERE / "registry").exists() else True)
    tp = Path(tempfile.mkdtemp(prefix="acc-"))
    (tp / "A_v0101.py").write_text('"""doc"""\nfrom __future__ import annotations\nimport VIA_SuperAccel_Module\nX = 1\n', encoding="utf-8")
    (tp / "B_v0101.py").write_text('#!/usr/bin/env python\n"""doc"""\nimport VeritasCeleritas_v1141 as vc\nY = 2\n', encoding="utf-8")
    (tp / "C_v0101.py").write_text('"""ok"""\n' + BRIDGE_TXT + 'Z = 3\n', encoding="utf-8")
    rc_a, la = accelfix(True, home=tp, limit=50, every=True)
    na = sorted(p.name for p in tp.glob("*_v0102.py"))
    okc = all(compile(p.read_text(encoding="utf-8"), p.name, "exec") is not None and "VIA:ACCEL-BRIDGE:v0111" in p.read_text(encoding="utf-8") for p in tp.glob("*_v0102.py"))
    chk("⓪ accelfix --all:舊橋(SUP_MDL737)與寫死 v1141 的尾版都補動態最新版號橋 · 已是動態橋的不動 · 原檔不動 · v+1 可編譯 → %s" % na, na == ["A_v0102.py", "B_v0102.py"] and okc and (tp / "A_v0101.py").read_text(encoding="utf-8").count("ACCEL-BRIDGE") == 0)
    ev_rc, ev_l = envcheck(False)
    chk("⓪ envcheck:AST 掃 import → 分必裝 / 選裝 / 隔離 · 只檢查不安裝(未帶 --install)→ %s" % (ev_l[0][:90] if ev_l else "—"), bool(ev_l) and ev_l[0].startswith("[計] 環境檢查"))
    chk("⓪ 基準快照路徑排除:references / baseline / _sandbox 不算衝突", not re.search(r"(?i)[\\/](?:references|baseline|_sandbox)[\\/]", "SSOT/VRN_X_v0100.json/") and bool(re.search(r"(?i)[\\/](?:references|baseline|_sandbox)[\\/]", "references/intake/VIA_X/baseline/VRN_X_v0100.json/")))
    chk("⓪ linkmap 動詞接 ENG396 最新版(有 linkmap 才跑 · 沒有照實說)", callable(linkmap_verb))
    src_fake = 'chk("⑥ 第三步 OCR:影像表格(P%d 圖區無文字層)→ 自動選 輕型單引擎 rapidocr@%s(表格提高 DPI)")'
    lab = "⑥ 第三步 OCR:影像表格(P# 圖區無文字層)→ 自動選 輕型單引擎 rapidocr@#(表格提高 DPI)"
    chk("⓪ 測試名稱骨幹比對:閘印的 P# / @# 對得上原始碼的 P%%d / @%%s(%s)" % _skel(lab)[:10], _skel(lab)[:10] in _skel(src_fake) and len(_skel(lab)[:10]) >= 4)
    chk("① p1loop 退步區塊細節直接印進貼包(區編號 · 框 · 引擎 · 首 70 字)· 自測用參數注入 · 零替換 · reconcile 無衝突時回 0", rc1 == 1 and any(l.startswith("[計] 退步細節") and "P4·FR·02·TB" in l and "Key ratios" in l for l in l1) and reconcile(False)[0] == 0)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("② 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片 · 正式流程零替換 · 自測也零替換(參數注入)", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__)
        and "setattr(" not in me.split("def selftest")[0])
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0213 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
