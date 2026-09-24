#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VRN_ENG090_FinStatementsTemplate v0100 — 交易所財報 VRN 模板頁(制式 HTML U/I · SYNCHRONIZER 交接 · 上下自動燈號)
====================================================================
側線 2026-09-24 第十五段;主線批號由併線的手指定(L25)。
LL334 改號(第十五段(續),併 main 批735 時):原名 VRN_ENG089_FinStatementsTemplate——主線批735 先用了 VRN_ENG089
(VRN_ENG089_TemplateView),本支讓號為 VRN_ENG090;內容只換自己的名字,其餘一字不動。
操作員令(2026-09-24,原話):
  「實測無誤後結果驗證無誤後收尾並用制式模板html u/i套進去形成vrn模板都由synchonizer控制交接自適應式自動化」
  「上下的自動連結更新新增檢查機能建構須完成」
  「進行自設自修正時測修改直到成功收尾聯上 HTML NU/I 使用者測試無誤 開啟運作無誤 上下建立自貢燈心機制」

一條線(L39 引擎 → JSON → 頁;L31 對映 → 連接 → 同步 → 測試 → 除錯):
  上游  VDF_ENG082 尾版 `run --mops` 落的兩張表:tw_financial_mops(長表)· tw_financial_mops_log(擷取台帳);
        tw_listings(冊上家數)。本支**唯讀**開庫(read_only 三重試;開不了=缺料並講原因,不當成全缺)。
        「齊不齊」一律呼叫 ENG082 自己的 mops_target / mops_plan(同一套判準,不另寫;Zero-Hydra);
        新鮮度走正典 period_lag(季底與期限讀期別規則冊;LL442 不另寫期別換算)。
  本支  VIA_Reports/vrn/finstat/
          VRN_FINSTAT_latest.json          全部結構化資料 + 上下燈 + 連結(check / status / 別的工具讀這一份)
          VRN_FINSTAT_SYNC_latest.json     SYNCHRONIZER 狀態信封 v2(系統模組照套件留著 + VRN 模組 + 圖表 + 歷史列)
          VRN_FINSTAT_PROFILE_latest.json  產業範本冊同格式(modules / charts / historySchema)
          VRN_FINSTAT_HISTORY_latest.csv   歷史列(SYNCHRONIZER「匯入 CSV」直接吃)
        supportive modules/ui_support/VIA_UI_VRNFinStatements_v0100.html
          制式模板頁:配色(:root 變數)、密度對照、印章 Logo 全部**現讀** VIA_HTML_UI 套件;零外連,file:// 直開。
  下游  SYNCHRONIZER(VIA_HTML_UI/ui/VIA-SYNCHRONIZER-Standalone.html)控制交接:
          · 頁上「交接到 SYNCHRONIZER」照 SYNCHRONIZER 自己存在狀態裡的同步規則走:範圍「手動 / 只同步檢視」或
            衝突「本機優先」都不寫,改用「下載信封 → SYNCHRONIZER 匯入」;規則准才寫同源 localStorage + BroadcastChannel。
          · SYNCHRONIZER 已經是本範本、資料比本頁舊 → 頁一打開就自動更新(只往新的方向,兩頁不會互蓋);
            是別的範本 → 不動,先告訴你會換掉哪個範本,再按一次才換(系統模組照留,同 SYNCHRONIZER「取代」模式)。
          · 頁的密度 / 主題 / 字級跟著 SYNCHRONIZER 的檢視設定走(自適應)。
        中央 UI(VIA-UI-Standalone-NoServer.html)從同一份狀態收到 VRN 模組(「自定義模組」側欄,名稱帶燈)。
燈(VRN 燈號冊六盞,AST 現讀 VRN_SystemManager 尾版的 LAMPS:綠 GREEN · 缺料 NODATA · 閘 GATED · 缺件 ABSENT · 過期 STALE · 壞 RED):
  上游燈  上游引擎 · 資料庫 · 每個市場的完整度(ENG082 mops_plan 還缺幾個端點;交易所擋=缺料、閘沒開=閘)與新鮮度(正典 period_lag)
  下游燈  SYNCHRONIZER 契約(套件兩頁鍵名 / 頻道一致)· 套件完整(CGC_MDL160 template 閘)· 燈號冊 · 家族頁名冊(CGC_MDL138
          ROSTER 有沒有這支)· U/I 契約(via-workflow ui-contract 有沒有收這一頁)· 信封合 SYNCHRONIZER 規格;
          check 另驗:頁與庫同一時點 · 頁內鍵名 = 套件現讀 · 頁零外連 · 信封檔 = 頁內嵌那一份;瀏覽器端交接燈在頁上現量
自動:連結(上游尾版 / 套件 / 名冊全部現解,不釘版號)· 更新(每次 run 重產;`via-vrnui` 經家族頁名冊自動重產)·
      新增(市場 / 業別 / 季全部從庫與 ENG082 常數長出來,多一個就多一列、一個模組、一張圖,不改碼)· 檢查(check 逐條)。
動詞:
  run    [--db PATH] [--today YYYY-MM-DD] [--page PATH] [--out DIR]   產 JSON + 信封 + 範本冊 + CSV + 頁
  check  [--db PATH] [--today YYYY-MM-DD] [--page PATH] [--out DIR]   上下連結逐條檢查(不寫任何檔)
  status [--out DIR]                                                  讀上一趟的 JSON 印燈
  --selftest                                                          二十二檢(暫存夾、零網路、不碰真庫)
誠實 rc:0 全綠 · 1 壞(寫不進去 / 信封或契約壞)· 2 缺料 / 閘 / 過期 / 還缺(頁照產)· 3 缺件(上游或套件不在)· 130 中斷
律:唯讀讀庫;正本零觸碰(VIA_HTML_UI 套件只讀,一個位元組都不改);零網路;零 CDN;尾版律;只增不減;
    Zero-Hydra(判準 / 期別 / 燈號冊 / 套件鍵名與預設都讀正主,不抄第二份);零彈窗(不開瀏覽器);不設任何同意閘或金鑰。
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
# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

import ast
import base64
import csv
import fnmatch
import html
import importlib.util
import io
import json
import os
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path

VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]      # 批586:版號寫死會爛,從檔名取
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
SUPP = VIA / "supportive modules"
REG = SUPP / "registry"
UI_DIR = SUPP / "ui_support"
PAGE = UI_DIR / "VIA_UI_VRNFinStatements_v0100.html"
OUT = VIA / "VIA_Reports" / "vrn" / "finstat"
PKG = VIA / "VIA_HTML_UI"
E82_DIR = VIA / "functional modules" / "VDF" / "engine"
GLOBS = {"e82": "VDF_ENG082_FinStatements_v*.py", "vrnsys": "VRN_SystemManager_v*.py",
         "famui": "CGC_MDL138_FamilyUI_v*.py", "gate": "CGC_MDL160_UIUnifyGate_v*.py"}
UI_CONTRACTS = (VIA / "VIA_Reports" / "ui" / "UI_CONTRACT_latest.json", REG / "VIA_UI_Contract_v0100.json")
FILES = {"report": "VRN_FINSTAT_latest.json", "sync": "VRN_FINSTAT_SYNC_latest.json",
         "profile": "VRN_FINSTAT_PROFILE_latest.json", "history": "VRN_FINSTAT_HISTORY_latest.csv"}
TEMPLATE_ID = "vrn-exchange-finstatements"
TEMPLATE_NAME = "VRN 交易所財報"
SOURCE = "VRN-FINSTAT"
MID = "vrn-finstat"
REFRESH = "via-vrnui"
DOWNLOAD = "via-sync-state-v2-vrn-finstat.json"
MARKET_ZH = {"TPEX": "上櫃", "TWSE": "上市"}
ST_ZH = {"IS": "綜合損益表", "BS": "資產負債表"}
ST_SHORT = {"IS": "損益", "BS": "資產負債"}
IND_ZH = {"ci": "一般業", "basi": "金融業", "bd": "證券期貨業", "fh": "金控業", "ins": "保險業", "mim": "異業"}
KIND = {"IS": ("is", "損益家數", "bar"), "BS": ("bs", "資產負債家數", "bar"), "items": ("items", "項數", "line"),
        "eps": ("eps", "端點齊", "kpi"), "listed": ("listed", "冊上家數", "kpi")}
DOTS = {"GREEN": "🟢", "NODATA": "🟡", "STALE": "🟠", "GATED": "🔵", "ABSENT": "⚪", "RED": "🔴"}
RANK = {"GREEN": 0, "GATED": 1, "NODATA": 2, "STALE": 3, "ABSENT": 4, "RED": 5}
VIEW = {"density": "balanced", "theme": "light", "motion": True, "hints": True, "live": True, "autoApply": True,
        "paused": False, "activeTab": "即時流量", "activeNav": f"{MID}-overview"}
DATA_RX = r"資料 (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)"        # 範本名裡的資料時點(JS 用同一個式子比新舊)
_TRIES, _WAIT_S = 3, 1.0
_newest = _LIB.newest


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _literal(path: Path, name: str):
    """從原始碼語法樹取一個模組層常數(ast.literal_eval;**不執行**那支,零副作用)。"""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(f"{Path(path).name} 沒有 {name}")


def _ver(p) -> str:
    m = re.search(r"_v(\d{4})\.py$", str(p or ""))
    return f"v{m.group(1)}" if m else ""


def _rel(p) -> str:
    try:
        return Path(p).resolve().relative_to(VIA).as_posix()
    except Exception:
        return str(p)


def _href(target: Path, page: Path) -> str:
    """頁 → 目標的連結:同一顆碟用相對路徑(file:// 直開);跨碟退絕對 file:/// URI。"""
    try:
        return Path(os.path.relpath(Path(target).resolve(), Path(page).resolve().parent)).as_posix()
    except ValueError:
        return Path(target).resolve().as_uri()


def _atomic(path: Path, text: str, encoding: str = "utf-8") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    with open(tmp, "w", encoding=encoding, newline="") as f:
        f.write(text)
    os.replace(tmp, path)
    return path


def worst(states) -> str:
    s = [x for x in states if x]
    return max(s, key=lambda x: RANK.get(x, 5)) if s else "GREEN"


def rc_of(states) -> int:
    s = set(states)
    if "RED" in s:
        return 1
    if "ABSENT" in s:
        return 3
    return 0 if s <= {"GREEN"} else 2


def _link(dir_: str, id_: str, name: str, state: str, detail: str = "", path: str = "", fix: str = "") -> dict:
    return {"dir": dir_, "id": id_, "name": name, "state": state, "detail": detail, "path": path, "fix": fix}


# ── 正主現讀(燈號冊 · 套件 · 名冊 · U/I 契約 · 上游)──────────────────────────────
def lamp_book(root: Path = HERE) -> dict:
    """VRN 燈號冊(VRN_SystemManager 尾版的 LAMPS;AST 現讀,不執行它)。本支用到的燈都要在冊上。"""
    p = _newest(root, GLOBS["vrnsys"])
    if not p:
        return {"state": "ABSENT", "lamps": {}, "src": "", "why": "VRN_SystemManager 尾版不在(燈號冊缺件)"}
    try:
        lamps = dict(_literal(p, "LAMPS"))
    except Exception as exc:
        return {"state": "RED", "lamps": {}, "src": p.name, "why": f"{p.name} 讀不到 LAMPS({type(exc).__name__})"}
    missing = sorted(set(DOTS) - set(lamps))
    return {"state": "GREEN" if not missing else "RED", "lamps": lamps, "src": p.name,
            "why": "" if not missing else f"本支用到的燈不在冊上:{missing}"}


def _js_obj(txt: str | None):
    """套件裡的 JS 物件 / 陣列字面值(鍵不加引號、字串單引號、只有字串 / 數字 / 布林)→ Python。"""
    if txt is None:
        raise ValueError("套件裡找不到這一段")
    j = re.sub(r"'((?:[^'\\]|\\.)*)'", lambda m: json.dumps(m.group(1), ensure_ascii=False), txt)
    j = re.sub(r"([{,]\s*)([A-Za-z_]\w*)\s*:", r'\1"\2":', j)
    return json.loads(j)


def package(root: Path = PKG) -> dict:
    """VIA_HTML_UI 套件現讀(只讀,一個位元組都不改):交接要用的鍵名 / 頻道 / 系統模組 / 型別 / 樞紐欄 / slug 規則 /
    版面與同步預設 / 密度對照 / 配色 / 印章 Logo。兩頁鍵名或頻道不一致 = 契約壞(RED)。"""
    root = Path(root)
    sp, up = root / "ui" / "VIA-SYNCHRONIZER-Standalone.html", root / "ui" / "VIA-UI-Standalone-NoServer.html"
    out = {"state": "ABSENT", "root": str(root), "sync_page": str(sp), "ui_page": str(up), "why": "", "release": ""}
    if not (sp.is_file() and up.is_file()):
        out["why"] = f"套件入口頁不在:{_rel(up) if sp.is_file() else _rel(sp)}"
        return out
    s, u = sp.read_text(encoding="utf-8"), up.read_text(encoding="utf-8")

    def one(rx, text):
        m = re.search(rx, text, re.S)
        return m.group(1) if m else None
    try:
        out["sync_key"], out["sync_channel"] = one(r"\bKEY\s*=\s*['\"]([^'\"]+)['\"]", s), one(r"\bCHANNEL\s*=\s*['\"]([^'\"]+)['\"]", s)
        out["ui_key"], out["ui_channel"] = one(r"\bKEY\s*=\s*['\"]([^'\"]+)['\"]", u), one(r"\bCHANNEL\s*=\s*['\"]([^'\"]+)['\"]", u)
        out["types"] = list(_js_obj(one(r"\bTYPES\s*=\s*(\{[^}]*\})", s)))
        out["chart_types"] = _js_obj(one(r"(\[[^\]]*\])\.includes\(base\.type\)", s))
        out["pivot"] = {k: _js_obj(one(r"(\[[^\]]*\])\.includes\(pivot\.%s\)" % k, s)) for k in ("rowField", "columnField", "aggregation")}
        out["system_modules"] = [m for m in _js_obj(one(r"\bDEFAULT_MODULES\s*=\s*(\[.*?\])\s*;", s)) if m.get("system") is True]
        out["layout"] = _js_obj(one(r"\bDEFAULT_LAYOUT\s*=\s*(\{[^}]*\})", s))
        out["sync_defaults"] = _js_obj(one(r"sync:(\{scope:'all'[^}]*\})", s))
        sl = one(r"slugify\s*=\s*value\s*=>(.*?);", s) or ""
        out["slug_class"] = one(r"replace\(/(\[\^[^\]]+\])\+/g", sl)
        out["slug_max"] = int(one(r"slice\(0,(\d+)\)", sl) or 0)
        dm = re.search(r"\{\s*comfortable:\s*'([^']+)',\s*balanced:\s*'([^']+)',\s*compact:\s*'([^']+)'\s*\}", u)
        out["density"] = dict(zip(("comfortable", "balanced", "compact"), dm.groups())) if dm else {}
        out["tokens"] = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", one(r":root\s*\{([^}]*)\}", u) or ""))
    except Exception as exc:
        out["state"], out["why"] = "RED", f"套件格式讀不動({type(exc).__name__}: {str(exc)[:120]});套件換版了?重看交接契約"
        return out
    logo = root / "assets" / "via-stamp-transparent-96.webp"
    out["logo"] = ("data:image/webp;base64," + base64.b64encode(logo.read_bytes()).decode("ascii")) if logo.is_file() else ""
    try:
        out["release"] = str(json.loads((root / "manifest.json").read_text(encoding="utf-8")).get("release", ""))
    except Exception:
        out["release"] = ""
    need = [k for k in ("sync_key", "sync_channel", "ui_key", "ui_channel", "slug_class") if not out.get(k)]
    if need or not out["system_modules"] or not out["slug_max"]:
        out["state"], out["why"] = "RED", f"套件少了交接要的東西:{need or '系統模組 / slug 長度'}"
    elif (out["sync_key"], out["sync_channel"]) != (out["ui_key"], out["ui_channel"]):
        out["state"], out["why"] = "RED", (f"SYNCHRONIZER({out['sync_key']} / {out['sync_channel']})跟中央 UI"
                                            f"({out['ui_key']} / {out['ui_channel']})鍵名或頻道不一致")
    else:
        out["state"] = "GREEN"
    return out


def slug(value: str, pkg: dict) -> str:
    """跟 SYNCHRONIZER 的 slugify 同一條規則(字元類與長度都從套件現讀)。"""
    rx = (pkg or {}).get("slug_class") or r"[^a-z0-9\u4e00-\u9fff]"
    s = re.sub(rx + "+", "-", str(value or "module").strip().lower())
    return s.strip("-")[: int((pkg or {}).get("slug_max") or 48)]


_GATE = {}


def pkg_integrity(root: Path = PKG, reg: Path = REG) -> dict:
    """套件完整:借 CGC_MDL160 尾版的 template 閘(逐檔 sha256 對 manifest + 三支入口的離線契約);本支不另寫一份。"""
    p = _newest(reg, GLOBS["gate"])
    if not p:
        return {"state": "ABSENT", "src": "", "why": "CGC_MDL160 尾版不在"}
    try:
        g = _GATE.get(p) or _load("vrn89_mdl160", p)
        _GATE[p] = g
        r = g.template(root=Path(root))
    except Exception as exc:
        return {"state": "RED", "src": p.name, "why": f"{p.name} template() 跑不動({type(exc).__name__})"}
    why = [r.get("why") or ""]
    for k, zh in (("sha_drift", "內容漂移"), ("eol_converted", "換行被改"), ("missing", "缺檔")):
        if r.get(k):
            why.append(f"{zh} {len(r[k])}")
    if r.get("offline_bad"):
        why.append(f"離線契約 {r['offline_bad'][:2]}")
    return {"state": str(r.get("state") or "RED"), "src": p.name, "sha_ok": r.get("sha_ok"),
            "files": r.get("files_in_manifest"), "why": " · ".join(x for x in why if x)}


def offline_hits(text: str, reg: Path = REG) -> dict:
    """頁的離線契約:用 CGC_MDL160 的四道尺(fetch / XHR / 外部 src·href / 相對 .json)。尺不在 = None(誠實缺件)。"""
    p = _newest(reg, GLOBS["gate"])
    if not p:
        return None
    g = _GATE.get(p) or _load("vrn89_mdl160", p)
    _GATE[p] = g
    return {k: len(rx.findall(text)) for k, rx in g.OFFLINE_RX.items() if rx.findall(text)}


def roster_link(page: Path = PAGE, reg: Path = REG) -> dict:
    """家族頁名冊(CGC_MDL138 尾版 ROSTER;AST 現讀):有沒有一項的 glob 認得本支、頁指到同一頁 → via-vrnui 會自動重產。"""
    p = _newest(reg, GLOBS["famui"])
    if not p:
        return {"state": "ABSENT", "src": "", "why": "CGC_MDL138 尾版不在"}
    try:
        ro = _literal(p, "ROSTER")
    except Exception as exc:
        return {"state": "RED", "src": p.name, "why": f"{p.name} 讀不到 ROSTER({type(exc).__name__})"}
    me = Path(__file__).name
    for fam, items in (ro or {}).items():
        for i, it in enumerate(items or []):
            if fnmatch.fnmatch(me, str(it.get("glob", ""))):
                same = (VIA / str(it.get("page", ""))).resolve() == Path(page).resolve()
                return {"state": "GREEN" if same else "RED", "src": p.name, "family": fam, "index": i + 1,
                        "refresh": REFRESH if fam == "vrn" else f"via-famui {fam}", "args": it.get("args"),
                        "why": "" if same else f"名冊登錄的頁是 {it.get('page')},不是 {_rel(page)}"}
    return {"state": "ABSENT", "src": p.name, "why": f"{p.name} 的 ROSTER 沒有這支(via-vrnui 不會自動重產這一頁)"}


def uicontract_link(page: Path = PAGE, paths=UI_CONTRACTS) -> dict:
    """U/I 契約(CGC_MDL153 `via-workflow ui-contract` 產的那份):收了這一頁沒有、擁有者認到誰。讀不動的契約檔照報,不默默略過。"""
    broken = []
    for cp in paths:
        cp = Path(cp)
        if not cp.is_file():
            continue
        try:
            c = json.loads(cp.read_text(encoding="utf-8"))
        except Exception as exc:
            broken.append(f"{cp.name}({type(exc).__name__})")
            continue
        for pg in c.get("pages") or []:
            if pg.get("page") == Path(page).name:
                own = str(pg.get("owner") or "")
                ok = own.startswith(Path(__file__).stem.rsplit("_v", 1)[0])
                return {"state": "GREEN" if ok else "RED", "src": _rel(cp), "owner": own, "refresh": pg.get("refresh", ""),
                        "family": pg.get("family", ""), "why": "" if ok else f"契約認的擁有者是 {own or '(空)'}"}
    return {"state": "RED" if broken else "ABSENT", "src": " / ".join(_rel(p) for p in paths),
            "why": (f"契約檔讀不動:{'、'.join(broken)};" if broken else "") + "U/I 契約還沒收這一頁(先 run 產頁,再 via-workflow ui-contract)"}


def upstream(e82_dir: Path = E82_DIR):
    """上游 VDF_ENG082 尾版(載入它,判準用它自己的 mops_target / mops_plan)。"""
    p = _newest(e82_dir, GLOBS["e82"])
    if not p:
        return None, {"state": "ABSENT", "src": "", "version": "", "why": "上游 VDF_ENG082 尾版不在"}
    try:
        m = _load("vrn89_e82", p)
    except Exception as exc:
        return None, {"state": "RED", "src": p.name, "version": _ver(p), "why": f"{p.name} 載不起來({type(exc).__name__}: {str(exc)[:120]})"}
    need = ("mops_plan", "mops_target", "_mops_source", "_resolve_db", "MOPS_OA", "MOPS_ST", "MOPS_IND", "MOPS_TABLE", "MOPS_LOG")
    miss = [n for n in need if not hasattr(m, n)]
    if miss:
        return None, {"state": "RED", "src": p.name, "version": _ver(p), "why": f"{p.name} 少了 {miss}(上游介面變了)"}
    return m, {"state": "GREEN", "src": p.name, "version": _ver(p), "why": ""}


# ── 上游現量(唯讀)─────────────────────────────────────────────────────
def _connect_ro(dbp):
    """唯讀連線三重試(批273 不卡斷律);開不了回 (None, 因由),不拋。"""
    try:
        import duckdb
    except Exception as exc:
        return None, f"這個 python 沒有 duckdb({type(exc).__name__})"
    last = None
    for i in range(_TRIES):
        try:
            return duckdb.connect(str(dbp), read_only=True), ""
        except Exception as exc:
            last = exc
            if i + 1 < _TRIES:
                time.sleep(_WAIT_S)
    return None, f"{type(last).__name__}: {str(last)[:160]}"


_CONNECT = _connect_ro


def gather(e82, dbp, today: date) -> dict:
    """上游現量(唯讀)→ 結構化資料。判準全交給 ENG082(mops_target / mops_plan);只有 ENG082 冊上的市場交給它判齊。"""
    eps = [(st, ind) for st in e82.MOPS_ST for ind in e82.MOPS_IND]
    qe, due = e82.mops_target(today)
    d = {"db": str(dbp) if dbp else "", "db_state": "", "db_why": "", "target": {"qe": qe, "due": due}, "eps": eps,
         "markets": list(e82.MOPS_OA), "latest": [], "periods": [], "listed": {}, "latest_date": {}, "tables": [],
         "stamp": {"fetched_at": "", "n_rows": 0, "n_log": 0}, "plan": {}}
    if not dbp or not Path(dbp).is_file():
        d["db_state"], d["db_why"] = "NODATA", "庫不在(先 via-finstat run --mops;閘要你開)"
        return d
    con, err = _CONNECT(dbp)
    if con is None:
        d["db_state"], d["db_why"] = "NODATA", f"庫開不了(可能正在寫,撞鎖;等它寫完再跑)· {err}"
        return d
    try:
        tabs = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        d["tables"] = sorted(t for t in tabs if t in (e82.MOPS_TABLE, e82.MOPS_LOG, "tw_listings"))
        if e82.MOPS_LOG in tabs:
            cols = {r[0] for r in con.execute(f"DESCRIBE {e82.MOPS_LOG}").fetchall()}
            keys = ("market", "statement", "industry", "source", "state", "n_records", "n_items", "n_stored", "period", "period_end", "note", "fetched_at")
            sel = ", ".join(k if k in cols else f"NULL AS {k}" for k in keys)
            rows = con.execute(f"SELECT {sel} FROM (SELECT *, row_number() OVER (PARTITION BY source ORDER BY fetched_at DESC) AS rn_ "
                               f"FROM {e82.MOPS_LOG}) WHERE rn_ = 1 ORDER BY market, statement, industry").fetchall()
            d["latest"] = [dict(zip(keys, r)) for r in rows]
            f, n = con.execute(f"SELECT max(fetched_at), count(*) FROM {e82.MOPS_LOG}").fetchone()
            d["stamp"]["fetched_at"], d["stamp"]["n_log"] = str(f or ""), int(n or 0)
        if e82.MOPS_TABLE in tabs:
            rows = con.execute(f"SELECT market, date, period, statement, count(DISTINCT code), count(*) FROM {e82.MOPS_TABLE} "
                               f"GROUP BY ALL ORDER BY 1, 2, 4").fetchall()
            d["periods"] = [{"market": str(a or ""), "date": str(b or ""), "period": str(c or ""), "statement": str(s or ""),
                             "companies": int(n1 or 0), "items": int(n2 or 0)} for a, b, c, s, n1, n2 in rows]
            d["stamp"]["n_rows"] = int(con.execute(f"SELECT count(*) FROM {e82.MOPS_TABLE}").fetchone()[0])
            d["latest_date"] = {str(a): str(b or "") for a, b in con.execute(f"SELECT market, max(date) FROM {e82.MOPS_TABLE} GROUP BY 1").fetchall()}
        if "tw_listings" in tabs and "market" in {r[0] for r in con.execute("DESCRIBE tw_listings").fetchall()}:
            d["listed"] = {str(a): int(b or 0) for a, b in con.execute("SELECT market, count(DISTINCT code) FROM tw_listings GROUP BY 1").fetchall()}
    except Exception as exc:
        d["db_state"], d["db_why"] = "RED", f"讀庫出錯({type(exc).__name__}: {str(exc)[:160]})"
        return d
    finally:
        con.close()
    for mk in [r["market"] for r in d["latest"]] + [r["market"] for r in d["periods"]]:
        if mk and mk not in d["markets"]:
            d["markets"].append(mk)                       # 自動新增:庫裡多一個市場就多一列(不在 ENG082 冊上=不判齊)
    judged = [m for m in d["markets"] if m in e82.MOPS_OA]
    d["plan"] = {m: {"todo": [list(x) for x in todo], "why": why} for m, (todo, why) in e82.mops_plan(dbp, judged, False, today).items()}
    if not ({e82.MOPS_TABLE, e82.MOPS_LOG} & tabs):
        d["db_state"], d["db_why"] = "NODATA", f"{e82.MOPS_TABLE} / {e82.MOPS_LOG} 都還沒建(先 via-finstat run --mops;閘要你開)"
    else:
        d["db_state"] = "GREEN"
    return d


def freshness(table: str, latest: str, today: date) -> dict:
    """新鮮度走正典 period_lag(最新季底 → 下一季期限過了幾天;期限當天還能申報 = 0)。"""
    if not latest:
        return {"state": "NODATA", "text": "還沒有資料"}
    r = _LIB.UTILS.period_lag(table, latest, today=today)
    if r.get("state") == "PERIOD_DUE":
        lag = int(r.get("lag_days") or 0)
        return {"state": "GREEN" if lag == 0 else "STALE", "iso": r.get("iso"), "due": r.get("due"), "lag_days": lag,
                "text": f"最新季底 {r.get('iso')} · 下一季期限 {r.get('due')}" + ("" if lag == 0 else f" 已過 {lag} 日")}
    return {"state": "NODATA", "text": f"期別認不出({r.get('state')})", "raw": r}


def assess(e82, d: dict, today: date) -> tuple:
    """每個市場的燈 + 端點矩陣。回 (markets, endpoints)。"""
    n_eps = len(d["eps"])
    last = {(r["market"], r["statement"], r["industry"]): r for r in d["latest"]}
    markets, endpoints = [], []
    for m in d["markets"]:
        todo = d["plan"].get(m, {}).get("todo") if m in d["plan"] else None
        miss = {(e82.MOPS_ST.get(st, st), ind) for st, ind in (todo or [])}
        if d["db_state"] in ("NODATA", "RED") and not d["plan"]:
            comp = {"state": d["db_state"], "text": d["db_why"]}
        elif todo is None:
            comp = {"state": "NODATA", "text": "不在 ENG082 冊上(照列、不判齊)"}
        elif not todo:
            comp = {"state": "GREEN", "text": f"齊 {n_eps}/{n_eps}"}
        else:
            sts = [last.get((m, st, ind), {}).get("state") for st, ind in miss]
            if sts and all(s == "DENY" for s in sts):
                comp = {"state": "GATED", "text": f"缺 {len(todo)}/{n_eps} · 閘沒開(DENY;閘由你開)"}
            elif sts and all(s == "BLOCKED" for s in sts):
                comp = {"state": "NODATA", "text": f"缺 {len(todo)}/{n_eps} · 交易所擋(安全頁;換工作站再抓)"}
            else:
                comp = {"state": "NODATA", "text": f"缺 {len(todo)}/{n_eps}"}
        fr = freshness(e82.MOPS_TABLE, d["latest_date"].get(m, ""), today)
        rows = [p for p in d["periods"] if p["market"] == m]
        top = max((p["date"] for p in rows), default="")
        cur = [p for p in rows if p["date"] == top]
        markets.append({"market": m, "zh": MARKET_ZH.get(m, m), "completeness": comp, "freshness": fr,
                        "lamp": worst([comp["state"], fr["state"]]), "latest_period": next((p["period"] for p in cur), ""),
                        "latest_date": top, "companies": {p["statement"]: p["companies"] for p in cur},
                        "items": sum(p["items"] for p in cur), "listed": d["listed"].get(m),
                        "eps_ok": (n_eps - len(todo)) if todo is not None else None, "eps_total": n_eps if todo is not None else None,
                        "todo": [[e82.MOPS_ST.get(st, st), ind] for st, ind in (todo or [])], "why": d["plan"].get(m, {}).get("why", "")})
        seen = set()
        for st, ind in d["eps"]:
            sname = e82.MOPS_ST.get(st, st)
            seen.add((sname, ind))
            r = last.get((m, sname, ind), {})
            endpoints.append({"market": m, "statement": sname, "industry": ind, "state": r.get("state") or "未抓",
                              "n_items": r.get("n_items"), "period": r.get("period"), "fetched_at": r.get("fetched_at"),
                              "note": r.get("note") or "", "missing": (sname, ind) in miss if todo is not None else None})
        for (mk, sname, ind), r in sorted(last.items()):
            if mk == m and (sname, ind) not in seen:             # 自動新增:台帳多一個業別就多一列(ENG082 冊外=不判齊)
                endpoints.append({"market": m, "statement": sname, "industry": ind, "state": r.get("state") or "?",
                                  "n_items": r.get("n_items"), "period": r.get("period"), "fetched_at": r.get("fetched_at"),
                                  "note": r.get("note") or "", "missing": None})
    return markets, endpoints


# ── SYNCHRONIZER 信封 ────────────────────────────────────────────────────
def _mz(m: str) -> str:
    return MARKET_ZH.get(m, m)


def build_envelope(d: dict, markets: list, ups: list, downs: list, pkg: dict, book: dict, now: datetime) -> dict:
    """SYNCHRONIZER 狀態信封 v2:系統模組照套件留著(同 SYNCHRONIZER「取代」模式)+ VRN 模組(名稱帶燈)+ 圖表 + 歷史列。
    圖表只為真的有資料列的指標長(自動新增);歷史列一季一市場一指標一列,值是數字(SYNCHRONIZER normalize 會把非數字變 0)。"""
    lz = lambda k: f"{DOTS.get(k, '')}{book.get('lamps', {}).get(k, k)}"      # noqa: E731
    stamp = (d.get("stamp") or {}).get("fetched_at") or ""
    period = max((p["period"] for p in d.get("periods", [])), default="")
    tname = f"{TEMPLATE_NAME} · {period or '無資料'} · 資料 {stamp[:19] or '—'}"
    up_w, down_w = worst(x["state"] for x in ups), worst(x["state"] for x in downs)
    qe, due = (d.get("target") or {}).get("qe"), (d.get("target") or {}).get("due")
    mods = []

    def add(id_, name, type_, pinned, note):
        mods.append({"id": slug(id_, pkg), "name": name, "type": type_, "enabled": True, "pinned": pinned, "order": 0, "system": False, "note": note})
    add(f"{MID}-overview", f"VRN 財報總覽 {DOTS[up_w]}", "dashboard", True,
        f"該齊 {qe or '?'} 那一季(法定期限 {due or '?'})· " + " · ".join(f"{x['zh']} {lz(x['lamp'])}" for x in markets) + f" · 資料 {stamp[:19] or '—'}")
    for x in markets:
        cs = x["companies"]
        add(f"{MID}-{x['market']}", f"{x['zh']}財報 {DOTS[x['lamp']]}", "data", True,
            f"完整度 {lz(x['completeness']['state'])} {x['completeness']['text']} · 新鮮度 {lz(x['freshness']['state'])} {x['freshness']['text']}"
            + (f" · {x['latest_period']} 損益 {cs.get('IS', 0)} 家 · 資產負債 {cs.get('BS', 0)} 家 · {x['items']:,} 項" if x["latest_period"] else "")
            + (f" · 冊上 {x['listed']} 家" if x["listed"] else ""))
    n_miss = sum(len(x["todo"]) for x in markets)
    add(f"{MID}-plan", f"補抓計畫 {DOTS['GREEN' if not n_miss else worst(x['completeness']['state'] for x in markets)]}", "automation", False,
        ("全部端點都齊,不用補抓" if not n_miss else
         f"仍缺 {n_miss} 個端點:" + " · ".join(f"{x['zh']} {len(x['todo'])}" for x in markets if x["todo"]) + " → via-finstat run --mops(閘由你開)"))
    add(f"{MID}-links", f"上下連結 {DOTS[down_w]}", "governance", False,
        "上游 " + " · ".join(f"{u['name']} {lz(u['state'])}" for u in ups[:2]) + " · 下游 " + " · ".join(f"{w['name']} {lz(w['state'])}" for w in downs))
    add(f"{MID}-page", "VRN 財報頁", "integration", False, f"{_rel(PAGE)} · 產生 {now.strftime('%Y-%m-%d %H:%M:%S')} · 再產:{REFRESH}")
    allm = [dict(m) for m in pkg.get("system_modules", [])] + mods
    for i, m in enumerate(allm):
        m["order"] = i + 1
    hist, at = [], (qe or now.date().isoformat())
    for p in d.get("periods", []):
        if not p["date"]:
            continue
        k = KIND.get(p["statement"], (p["statement"].lower(), f"{p['statement']}家數", "bar"))
        hist.append({"date": p["date"], "moduleId": slug(f"{MID}-{p['market']}", pkg), "metric": f"{_mz(p['market'])}{k[1]}",
                     "value": p["companies"], "category": p["market"]})
    items: dict = {}
    for p in d.get("periods", []):
        if p["date"]:
            items[(p["market"], p["date"])] = items.get((p["market"], p["date"]), 0) + p["items"]
    for (m, dt), n in sorted(items.items()):
        hist.append({"date": dt, "moduleId": slug(f"{MID}-{m}", pkg), "metric": f"{_mz(m)}{KIND['items'][1]}", "value": n, "category": m})
    for x in markets:
        if x["eps_ok"] is not None:
            hist.append({"date": at, "moduleId": slug(f"{MID}-{x['market']}", pkg), "metric": f"{x['zh']}{KIND['eps'][1]}", "value": x["eps_ok"], "category": x["market"]})
        if x["listed"]:
            hist.append({"date": at, "moduleId": slug(f"{MID}-{x['market']}", pkg), "metric": f"{x['zh']}{KIND['listed'][1]}", "value": x["listed"], "category": x["market"]})
    charts, seen = [], set()
    kinds = {v[1]: v for v in KIND.values()}
    for h in hist:
        if h["metric"] in seen:
            continue
        seen.add(h["metric"])
        suffix = next((s for s in kinds if h["metric"].endswith(s)), "")
        k = kinds.get(suffix) or ("x", h["metric"], "bar")
        charts.append({"id": slug(f"{MID}-{h['category']}-{k[0]}", pkg), "name": h["metric"], "type": k[2], "metric": h["metric"], "groupBy": "date", "enabled": True})
    return {"version": 2, "updatedAt": now.astimezone().isoformat(timespec="seconds"), "source": SOURCE, "view": dict(VIEW),
            "modules": allm, "analytics": {"templateId": TEMPLATE_ID, "templateName": tname, "charts": charts, "history": hist,
                                           "pivot": {"rowField": "date", "columnField": "metric", "valueField": "value", "aggregation": "sum"}},
            "layout": dict(pkg.get("layout") or {}), "sync": dict(pkg.get("sync_defaults") or {})}


def validate(env: dict, pkg: dict) -> list:
    """信封合不合 SYNCHRONIZER 規格(型別 / 圖表型別 / 樞紐欄 / slug 規則都從套件現讀)。回問題清單,空 = 合。"""
    bad = []
    if env.get("version") != 2:
        bad.append("version 不是 2")
    if not isinstance(env.get("view"), dict) or not env.get("view"):
        bad.append("view 空(SYNCHRONIZER 會當 v1 舊檔轉,模組被換成預設)")
    mods = env.get("modules") or []
    ids = [m.get("id") for m in mods]
    if len(ids) != len(set(ids)):
        bad.append("模組 id 重複")
    for m in mods:
        miss = [k for k in ("id", "name", "type", "enabled", "pinned", "order", "system", "note") if k not in m]
        if miss:
            bad.append(f"模組 {m.get('id')} 少欄 {miss}")
        if slug(m.get("id", ""), pkg) != m.get("id"):
            bad.append(f"模組 id 經 slugify 會變:{m.get('id')}")
        if m.get("type") not in (pkg.get("types") or []):
            bad.append(f"模組 {m.get('id')} 型別 {m.get('type')} 不在套件型別")
    if [m.get("order") for m in mods] != list(range(1, len(mods) + 1)):
        bad.append("模組 order 不是 1..n")
    sys_ids = {m.get("id") for m in pkg.get("system_modules") or []}
    if not sys_ids <= {m.get("id") for m in mods if m.get("system") is True}:
        bad.append("系統模組沒留齊(取代模式要留)")
    a = env.get("analytics") or {}
    if a.get("templateId") != TEMPLATE_ID or (not re.search(DATA_RX, str(a.get("templateName", ""))) and "資料 —" not in str(a.get("templateName", ""))):
        bad.append("範本 id / 名稱(含資料時點)不對")
    hist = a.get("history") or []
    for h in hist:
        if not re.fullmatch(r"\d{4}-\d\d-\d\d", str(h.get("date", ""))) or not h.get("metric"):
            bad.append(f"歷史列日期或指標空:{h}")
        if isinstance(h.get("value"), bool) or not isinstance(h.get("value"), (int, float)):
            bad.append(f"歷史列值不是數字:{h}")
        if slug(h.get("moduleId", ""), pkg) != h.get("moduleId"):
            bad.append(f"歷史列 moduleId 經 slugify 會變:{h.get('moduleId')}")
    metrics = {h.get("metric") for h in hist}
    cids = [c.get("id") for c in a.get("charts") or []]
    if len(cids) != len(set(cids)):
        bad.append("圖表 id 重複(SYNCHRONIZER 會改名成 -2,圖就對不上)")
    for c in a.get("charts") or []:
        if c.get("type") not in (pkg.get("chart_types") or []):
            bad.append(f"圖表 {c.get('id')} 型別 {c.get('type')} 不在套件型別")
        if slug(c.get("id", ""), pkg) != c.get("id"):
            bad.append(f"圖表 id 經 slugify 會變:{c.get('id')}")
        if c.get("metric") not in metrics:
            bad.append(f"圖表 {c.get('id')} 沒有資料列")
    pv, allow = a.get("pivot") or {}, pkg.get("pivot") or {}
    for k in ("rowField", "columnField", "aggregation"):
        if pv.get(k) not in (allow.get(k) or []):
            bad.append(f"樞紐 {k}={pv.get(k)} 不在套件允許")
    return bad


def profile_of(env: dict) -> dict:
    a = env["analytics"]
    return {TEMPLATE_ID: {"name": TEMPLATE_NAME, "description": "交易所 MOPS 彙總財報(VDF_ENG082)的覆蓋、完整度與新鮮度;由 VRN_ENG090 從庫產生",
                          "modules": [{k: m[k] for k in ("id", "name", "type", "note")} for m in env["modules"] if not m.get("system")],
                          "charts": [{k: c[k] for k in ("id", "name", "type", "metric", "groupBy")} for c in a["charts"]],
                          "historySchema": ["date", "module_id", "metric", "value", "category"]}}


def history_csv(env: dict) -> str:
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\r\n")
    w.writerow(["date", "module_id", "metric", "value", "category"])
    for h in env["analytics"]["history"]:
        w.writerow([h["date"], h["moduleId"], h["metric"], h["value"], h["category"]])
    return "\ufeff" + b.getvalue()


# ── 頁(制式模板)──────────────────────────────────────────────────────
_CSS = r"""
:root{__TOKENS__;--density:1;--ui-font-scale:.94}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg,#f3f5f2);color:var(--ink,#17201d);font:calc(var(--font-size,14px)*var(--ui-font-scale)) / 1.5 'Segoe UI',system-ui,-apple-system,'Noto Sans TC','Microsoft JhengHei',sans-serif}
body[data-theme=highContrast]{--ink:#000;--ink-soft:#111;--muted:#333;--line:#6b7a74;--line-strong:#2f3b36;--surface-soft:#fff}
.topbar{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;align-items:center;gap:calc(10px*var(--density));padding:calc(10px*var(--density)) 18px;background:var(--surface,#fff);border-bottom:1px solid var(--line,#dce5e0);box-shadow:var(--shadow-sm,none)}
.stamp{width:34px;height:34px;object-fit:contain}
.crumb{display:flex;gap:6px;align-items:center;color:var(--muted,#778680);font-size:.92em}.crumb strong{color:var(--ink,#17201d)}
.tools{margin-left:auto;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.btn{display:inline-flex;align-items:center;gap:6px;padding:calc(6px*var(--density)) 12px;border:1px solid var(--line-strong,#c8d5cf);border-radius:var(--radius-sm,10px);background:var(--surface,#fff);color:var(--ink-soft,#32413c);font:inherit;text-decoration:none;cursor:pointer}
.btn:hover{border-color:var(--gold,#b5822c)}.btn.primary{background:var(--accent,#b53b32);border-color:var(--accent-deep,#852820);color:#fff}
.chip{display:inline-flex;align-items:center;gap:6px;padding:3px 10px;border-radius:999px;border:1px solid var(--c,#999);background:var(--s,#f5f5f5);color:var(--c,#333);font-size:.9em;max-width:100%}
.chip:before{content:"";width:8px;height:8px;border-radius:50%;background:var(--c,#999);flex:none}
.lamp-GREEN{--c:var(--teal,#177066);--s:var(--teal-soft,#e4f2ef)}.lamp-NODATA{--c:var(--gold,#b5822c);--s:var(--gold-soft,#fbf2df)}
.lamp-STALE{--c:var(--accent,#b53b32);--s:var(--accent-soft,#f8e9e6)}.lamp-GATED{--c:var(--blue,#37698f);--s:var(--blue-soft,#e8f0f7)}
.lamp-ABSENT{--c:var(--muted,#778680);--s:var(--surface-soft,#f8faf8)}.lamp-RED{--c:var(--danger,#b33e3e);--s:var(--accent-soft,#f8e9e6)}
main{max-width:1480px;margin:0 auto;padding:calc(14px*var(--density)) 18px 28px}
.confirm{margin:10px 18px 0;padding:10px 14px;border:1px solid var(--gold,#b5822c);background:var(--gold-soft,#fbf2df);border-radius:var(--radius-sm,10px)}
.page-head{padding:calc(8px*var(--density)) 0 calc(12px*var(--density))}
.eyebrow{display:flex;align-items:center;gap:8px;color:var(--gold,#b5822c);font-size:.78em;letter-spacing:.14em;font-weight:600}
.eyebrow:before{content:"";width:26px;height:2px;background:var(--gold,#b5822c)}
h1{margin:6px 0 4px;font-size:1.55em;color:var(--ink,#17201d)}h2{margin:0 0 10px;font-size:1.05em;color:var(--ink,#17201d)}h3{margin:0 0 8px;font-size:.95em;color:var(--ink-soft,#32413c)}
.sub{color:var(--muted,#778680);margin:0}
.grid{display:grid;gap:calc(12px*var(--density));grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
.panel{background:var(--surface,#fff);border:1px solid var(--line,#dce5e0);border-radius:var(--radius-md,16px);padding:calc(14px*var(--density)) 16px;box-shadow:var(--shadow-sm,none);margin-bottom:calc(12px*var(--density));min-width:0}
.lamps ul{list-style:none;margin:0;padding:0;display:grid;gap:6px}
.lamps li{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline}.lamps li b{min-width:9em;color:var(--ink-soft,#32413c)}
.lamps small{color:var(--muted,#778680)}
.kpi{border-left:4px solid var(--c,#999)}.kpi .big{font-size:1.6em;font-weight:700;color:var(--ink,#17201d)}.kpi .row{display:flex;flex-wrap:wrap;gap:6px 16px;color:var(--ink-soft,#32413c)}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.92em}
th,td{padding:calc(5px*var(--density)) 8px;border-bottom:1px solid var(--line,#dce5e0);text-align:left;vertical-align:top;white-space:nowrap}
th{color:var(--muted,#778680);font-weight:600;background:var(--surface-soft,#f8faf8)}
td.num{text-align:right;font-variant-numeric:tabular-nums}
td.cell{border-left:3px solid var(--c,transparent);background:var(--s,transparent)}
.miss{color:var(--danger,#b33e3e);font-weight:600}
code,.cmd{font-family:ui-monospace,SFMono-Regular,Consolas,'Noto Sans Mono CJK TC',monospace;font-size:.92em}
.cmd{display:block;padding:6px 10px;margin:4px 0;background:var(--surface-tint,#f1f6f3);border:1px solid var(--line,#dce5e0);border-radius:8px;white-space:pre-wrap;word-break:break-all}
#chart{width:100%;height:auto;max-height:280px}
footer{color:var(--muted,#778680);font-size:.85em;padding:6px 0 18px}
@media (max-width:720px){.tools{margin-left:0}.lamps li b{min-width:0}h1{font-size:1.3em}main{padding:10px 12px 20px}.topbar{padding:8px 12px}}
@media print{.topbar .tools,.confirm{display:none}}
"""

_JS = r"""
(function(){
  'use strict';
  var $=function(s){return document.querySelector(s)};
  function readJson(id){try{return JSON.parse(document.getElementById(id).textContent)}catch(e){return null}}
  var ENV=readJson('vrnEnvelope'),META=readJson('vrnMeta')||{};
  var KEY=META.key,CHANNEL=META.channel,TID=META.templateId,RX=new RegExp(META.dataRx||'$^');
  var canStore=(function(){try{var k='__vrn_finstat__';localStorage.setItem(k,'1');localStorage.removeItem(k);return true}catch(e){return false}})();
  var bc=null;try{if(typeof BroadcastChannel==='function'&&CHANNEL)bc=new BroadcastChannel(CHANNEL)}catch(e){bc=null}
  var originId='vrn-finstat-'+Math.random().toString(36).slice(2,9);
  function clone(v){return JSON.parse(JSON.stringify(v))}
  function readShared(){if(!canStore||!KEY)return null;try{return JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){return null}}
  function stampOf(name){var m=RX.exec(String(name||''));return m?m[1]:''}
  function setLamp(state,text){var el=$('#handoverLamp');el.className='chip lamp-'+state;el.dataset.state=state;el.textContent=text}
  function blocked(cur){var s=(cur&&cur.sync)||{};
    if(s.scope==='manual')return 'SYNCHRONIZER 設為「手動」同步:不自動交接,請在 SYNCHRONIZER 按「匯入」選信封檔';
    if(s.scope==='view-only')return 'SYNCHRONIZER 只同步「檢視」:模組與分析不收,請改同步範圍或匯入信封檔';
    if(s.conflict==='local')return 'SYNCHRONIZER 設為「本機優先」:不收外來狀態,請在 SYNCHRONIZER 匯入信封檔';
    return ''}
  function build(cur){
    var next=clone(ENV),own=next.modules.filter(function(m){return !m.system});
    var sys=(cur&&Array.isArray(cur.modules))?cur.modules.filter(function(m){return m&&m.system===true}):[];
    if(!sys.length)sys=next.modules.filter(function(m){return m.system});
    next.modules=sys.concat(own).map(function(m,i){var c=clone(m);c.order=i+1;return c});
    if(cur&&cur.view)next.view=clone(cur.view);
    if(cur&&cur.layout)next.layout=clone(cur.layout);
    if(cur&&cur.sync){next.sync=clone(cur.sync);next.sync.revision=(Number(cur.sync.revision)||0)+1}else{next.sync.revision=(Number(next.sync.revision)||0)+1}
    next.updatedAt=new Date().toISOString();next.source=META.source||'VRN-FINSTAT';
    return next}
  function handover(auto){
    if(!ENV){setLamp('RED','交接:頁內信封讀不動(請重產本頁:'+(META.refresh||'')+')');return false}
    if(!canStore||!KEY){setLamp('ABSENT','交接:這個瀏覽器不給 localStorage,請按「下載信封」再到 SYNCHRONIZER 匯入');return false}
    var cur=readShared(),why=blocked(cur);
    if(why){setLamp('GATED','交接:'+why);return false}
    var next=build(cur);
    try{localStorage.setItem(KEY,JSON.stringify(next))}catch(e){setLamp('RED','交接:寫不進 localStorage('+e.name+')');return false}
    if(bc){try{bc.postMessage({type:'via-state-v2',originId:originId,state:clone(next)})}catch(e){}}
    setLamp('GREEN',(auto?'交接:已自動更新到本頁資料':'交接:已交給 SYNCHRONIZER')+' · rev '+next.sync.revision+' · '+new Date(next.updatedAt).toLocaleString('zh-TW',{hour12:false}));
    return true}
  function evaluate(){
    if(!ENV){setLamp('RED','交接:頁內信封讀不動');return}
    if(!canStore||!KEY){setLamp('ABSENT','交接:這個瀏覽器不給 localStorage,請按「下載信封」再到 SYNCHRONIZER 匯入');return}
    var cur=readShared();
    if(!cur){setLamp('NODATA','交接:SYNCHRONIZER 還沒有狀態 · 按「交接到 SYNCHRONIZER」');return}
    var a=cur.analytics||{},mine=stampOf(ENV.analytics.templateName),theirs=stampOf(a.templateName);
    if(a.templateId===TID){
      if(theirs===mine){setLamp('GREEN','交接:SYNCHRONIZER 已是本頁資料 · rev '+((cur.sync||{}).revision||0));return}
      if(theirs>mine){setLamp('STALE','交接:SYNCHRONIZER 的資料比本頁新('+theirs+');本頁不蓋回去,請重產本頁:'+(META.refresh||''));return}
      var why=blocked(cur);if(why){setLamp('STALE','交接:SYNCHRONIZER 還是舊資料('+(theirs||'—')+');'+why);return}
      handover(true);return}
    setLamp('NODATA','交接:SYNCHRONIZER 目前是「'+(a.templateName||a.templateId||'一般空白')+'」· 按「交接到 SYNCHRONIZER」切換')}
  function applyView(){var cur=readShared();if(!cur)return;var v=cur.view||{},d=(META.density||{})[v.density];
    if(d)document.documentElement.style.setProperty('--density',d);
    document.body.dataset.theme=v.theme||'light';
    if(cur.layout&&cur.layout.fontScale)document.documentElement.style.setProperty('--ui-font-scale',String(cur.layout.fontScale))}
  function drawChart(){
    var svg=document.getElementById('chart');if(!svg||!ENV)return;
    var rows=(ENV.analytics.history||[]).filter(function(h){return /家數$/.test(h.metric)&&!/冊上家數$/.test(h.metric)});
    if(!rows.length){svg.outerHTML='<p class="sub">尚無資料列(庫裡還沒有交易所財報)。</p>';return}
    var dates=[],mets=[];rows.forEach(function(h){if(dates.indexOf(h.date)<0)dates.push(h.date);if(mets.indexOf(h.metric)<0)mets.push(h.metric)});
    dates.sort();var max=Math.max.apply(null,rows.map(function(h){return h.value}))||1;
    var W=Math.max(360,dates.length*mets.length*34+80),H=240,L=46,B=40,T=14,gw=(W-L-10)/dates.length,bw=Math.max(8,Math.min(30,(gw-12)/mets.length));
    var col=['var(--blue,#37698f)','var(--teal,#177066)','var(--gold,#b5822c)','var(--accent,#b53b32)'];
    var s='<line x1="'+L+'" y1="'+(H-B)+'" x2="'+(W-10)+'" y2="'+(H-B)+'" stroke="var(--line-strong,#c8d5cf)"/>';
    for(var t=0;t<=4;t++){var yv=Math.round(max*t/4),y=H-B-(H-B-T)*t/4;s+='<text x="'+(L-6)+'" y="'+(y+4)+'" text-anchor="end" font-size="10" fill="var(--muted,#778680)">'+yv+'</text>'}
    dates.forEach(function(dt,i){var x0=L+i*gw+6;mets.forEach(function(m,j){var r=rows.filter(function(h){return h.date===dt&&h.metric===m})[0];if(!r)return;var h=(H-B-T)*r.value/max,x=x0+j*bw;
      s+='<rect x="'+x+'" y="'+(H-B-h)+'" width="'+(bw-3)+'" height="'+h+'" rx="3" fill="'+col[j%col.length]+'"><title>'+m+' '+dt+':'+r.value+'</title></rect>'});
      s+='<text x="'+(x0+mets.length*bw/2)+'" y="'+(H-B+16)+'" text-anchor="middle" font-size="11" fill="var(--ink-soft,#32413c)">'+dt+'</text>'});
    var lx=L;mets.forEach(function(m,j){s+='<rect x="'+lx+'" y="'+(H-12)+'" width="10" height="10" rx="2" fill="'+col[j%col.length]+'"/><text x="'+(lx+14)+'" y="'+(H-3)+'" font-size="11" fill="var(--ink-soft,#32413c)">'+m+'</text>';lx+=m.length*12+34});
    svg.setAttribute('viewBox','0 0 '+W+' '+H);svg.innerHTML=s}
  $('#handoverBtn').addEventListener('click',function(){var cur=readShared(),a=(cur&&cur.analytics)||{};
    if(cur&&a.templateId&&a.templateId!==TID&&a.templateId!=='blank'&&!blocked(cur)){$('#curTpl').textContent=a.templateName||a.templateId;$('#confirmBar').hidden=false;return}
    handover(false);applyView()});
  $('#confirmBtn').addEventListener('click',function(){$('#confirmBar').hidden=true;handover(false);applyView()});
  $('#cancelBtn').addEventListener('click',function(){$('#confirmBar').hidden=true});
  $('#downloadBtn').addEventListener('click',function(){var blob=new Blob([JSON.stringify(ENV,null,2)],{type:'application/json'}),a=document.createElement('a');
    a.href=URL.createObjectURL(blob);a.download=META.downloadName||'via-sync-state-v2.json';document.body.appendChild(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(a.href)},0)});
  window.addEventListener('storage',function(ev){if(ev.key===KEY){applyView();evaluate()}});
  if(bc)bc.onmessage=function(ev){var d=ev.data||{};if(d.originId===originId)return;if(d.type==='via-state-v2'||d.type==='via-clear-v2')setTimeout(function(){applyView();evaluate()},60)};
  drawChart();applyView();evaluate();
  window.VRN_FINSTAT={envelope:function(){return clone(ENV)},handover:handover,evaluate:evaluate,meta:META};
})();
"""


def _e(x) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def _json_script(obj) -> str:
    """內嵌 JSON:每個 `<` 都寫成 `\\u003c`(JSON 合法跳脫)——資料裡的 `</script>`、`<!--<script` 都關不掉、也帶不偏這個 script。"""
    return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def render_page(rep: dict, env: dict, pkg: dict, book: dict, page: Path) -> str:
    lamps = book.get("lamps") or {}

    def chip(state, text=""):
        return f'<span class="chip lamp-{_e(state)}">{_e(lamps.get(state, state))}{(" · " + _e(text)) if text else ""}</span>'

    def lis(links):
        return "".join(f'<li>{chip(x["state"])}<b>{_e(x["name"])}</b><span>{_e(x["detail"])}</span>'
                       + (f'<small>→ {_e(x["fix"])}</small>' if x.get("fix") and x["state"] != "GREEN" else "") + "</li>" for x in links)
    sp, up = Path(pkg.get("sync_page") or PKG / "ui" / "VIA-SYNCHRONIZER-Standalone.html"), Path(pkg.get("ui_page") or PKG / "ui" / "VIA-UI-Standalone-NoServer.html")
    tgt = rep.get("target") or {}
    kpis = []
    for x in rep["markets"]:
        cs = x["companies"]
        kpis.append(f'<div class="panel kpi lamp-{_e(x["lamp"])}"><h3>{_e(x["zh"])}({_e(x["market"])})· {chip(x["lamp"])}</h3>'
                    f'<div class="big">{_e(x["latest_period"] or "—")}</div><div class="row">'
                    f'<span>損益 {_e(cs.get("IS", 0))} 家</span><span>資產負債 {_e(cs.get("BS", 0))} 家</span>'
                    f'<span>冊上 {_e(x["listed"] if x["listed"] is not None else "?")} 家</span><span>{x["items"]:,} 項</span>'
                    f'<span>端點 {_e(x["eps_ok"] if x["eps_ok"] is not None else "—")}/{_e(x["eps_total"] or "—")}</span></div>'
                    f'<p class="sub">完整度 {chip(x["completeness"]["state"], x["completeness"]["text"])}</p>'
                    f'<p class="sub">新鮮度 {chip(x["freshness"]["state"], x["freshness"]["text"])}</p></div>')
    mk = [x["market"] for x in rep["markets"]]
    ep_rows = []
    for key in sorted({(e["statement"], e["industry"]) for e in rep["endpoints"]}, key=lambda k: (k[0] != "IS", k[0], list(IND_ZH).index(k[1]) if k[1] in IND_ZH else 99, k[1])):
        cells = []
        for m in mk:
            e = next((z for z in rep["endpoints"] if z["market"] == m and (z["statement"], z["industry"]) == key), None)
            if e is None:
                cells.append('<td class="cell">—</td>')
                continue
            st = {"OK": "GREEN", "DENY": "GATED", "未抓": "ABSENT"}.get(e["state"], "NODATA" if e["state"] in ("EMPTY", "UNPARSED", "BLOCKED", "FAIL", "ABSENT", "UNSAVED") else "RED")
            cells.append(f'<td class="cell lamp-{st}" title="{_e(e["note"])}">{_e(e["state"])}'
                         f'{(" · " + format(int(e["n_items"]), ",") + " 項") if e.get("n_items") else ""}'
                         f'{(" · " + _e(str(e["fetched_at"])[:16])) if e.get("fetched_at") else ""}'
                         f'{" · <span class=miss>缺</span>" if e["missing"] else ""}</td>')
        ep_rows.append(f'<tr><td>{_e(ST_ZH.get(key[0], key[0]))}</td><td>{_e(IND_ZH.get(key[1], key[1]))} <code>{_e(key[1])}</code></td>{"".join(cells)}</tr>')
    per_rows = "".join(f'<tr><td>{_e(MARKET_ZH.get(p["market"], p["market"]))}</td><td>{_e(p["period"])}</td><td>{_e(p["date"])}</td>'
                       f'<td>{_e(ST_ZH.get(p["statement"], p["statement"]))}</td><td class="num">{p["companies"]:,}</td><td class="num">{p["items"]:,}</td></tr>'
                       for p in rep["periods"]) or '<tr><td colspan="6">庫裡還沒有交易所財報(先 via-finstat run --mops;閘要你開)</td></tr>'
    todo = []
    for x in rep["markets"]:
        if x["todo"]:
            names = " · ".join(f"{ST_SHORT.get(s, s)} {IND_ZH.get(i, i)}" for s, i in x["todo"])
            todo.append(f'<li>{chip(x["completeness"]["state"])} <b>{_e(x["zh"])} 還缺 {len(x["todo"])} 個端點</b>:{_e(names)}<br><small>{_e(x["why"])}</small></li>')
    todo_html = ("<ul>" + "".join(todo) + "</ul>") if todo else f'<p>{chip("GREEN", "全部端點都齊,不用補抓")}</p>'
    cmds = [f"via-finstat run --mops --dry        # 先看計畫(只查庫,不抓)",
            f"via-finstat run --mops              # 只抓還缺的端點(閘由你開)",
            f"via-finstat status                  # 覆蓋與各端點最近一次",
            f"{REFRESH}                           # 重產本頁(家族頁名冊)",
            f"python \"functional modules/VRN/{Path(__file__).name}\" check   # 上下連結逐條檢查"]
    link_rows = "".join(f'<tr><td>{"上游" if x["dir"] == "up" else "下游"}</td><td>{_e(x["name"])}</td><td>{chip(x["state"])}</td>'
                        f'<td style="white-space:normal">{_e(x["detail"])}</td><td><code>{_e(x["path"])}</code></td></tr>' for x in rep["up"] + rep["down"])
    meta = {"key": pkg.get("sync_key"), "channel": pkg.get("sync_channel"), "templateId": TEMPLATE_ID, "source": SOURCE,
            "density": pkg.get("density") or {}, "downloadName": DOWNLOAD, "dataRx": DATA_RX, "dataStamp": rep["stamp"],
            "generated": rep["generated"], "engine": Path(__file__).name, "refresh": REFRESH, "e82": rep.get("e82", {}).get("src", "")}
    tokens = ";".join(f"{k}:{v.strip()}" for k, v in (pkg.get("tokens") or {}).items() if re.fullmatch(r"--[\w-]+", k) and "<" not in v and "}" not in v)
    css = _CSS.replace("__TOKENS__", tokens or "--bg:#f3f5f2")
    logo = f'<img class="stamp" src="{_e(pkg["logo"])}" alt="VIA">' if pkg.get("logo") else ""
    return (f'<!doctype html>\n<html lang="zh-Hant" data-generator="{_e(Path(__file__).name)}">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n<meta name="via-refresh" content="{REFRESH}">\n'
            f'<meta name="via-owner" content="{_e(Path(__file__).stem)}">\n<meta name="via-template" content="{TEMPLATE_ID}">\n'
            f'<title>VRN 交易所財報 · 模板頁</title>\n<style>{css}</style>\n</head>\n<body>\n'
            f'<header class="topbar">{logo}<div class="crumb"><span>VRN 模板</span><span>/</span><strong>交易所財報</strong></div>'
            f'<div class="tools"><span id="handoverLamp" class="chip lamp-NODATA" data-state="NODATA">交接:檢查中</span>'
            f'<button id="handoverBtn" class="btn primary" type="button">交接到 SYNCHRONIZER</button>'
            f'<button id="downloadBtn" class="btn" type="button">下載信封(SYNCHRONIZER 匯入用)</button>'
            f'<a class="btn" id="openSync" href="{_e(_href(sp, page))}" target="_blank" rel="noopener">開 SYNCHRONIZER</a>'
            f'<a class="btn" id="openUi" href="{_e(_href(up, page))}" target="_blank" rel="noopener">開中央 UI</a></div></header>\n'
            f'<div id="confirmBar" class="confirm" hidden>SYNCHRONIZER 目前是「<b id="curTpl"></b>」範本。交接會換成「{TEMPLATE_NAME}」'
            f'(系統模組照留、其他自定義模組換掉,同 SYNCHRONIZER「取代」模式)。 '
            f'<button id="confirmBtn" class="btn primary" type="button">確定交接</button> <button id="cancelBtn" class="btn" type="button">取消</button></div>\n'
            f'<main>\n<section class="page-head"><div class="eyebrow">VRN · EXCHANGE MOPS · SYNCHRONIZER</div>'
            f'<h1>交易所彙總財報 · VRN 模板</h1>'
            f'<p class="sub">該齊 {_e(tgt.get("qe") or "?")} 那一季(法定期限 {_e(tgt.get("due") or "?")})· 資料時點 {_e(rep["stamp"]["fetched_at"] or "—")}'
            f' · 產生 {_e(rep["generated"])} · 上游 {_e(rep.get("e82", {}).get("src") or "—")} · 套件 {_e(pkg.get("release") or "—")}</p></section>\n'
            f'<div class="grid lamps"><section class="panel"><h2>上游燈(資料)</h2><ul>{lis(rep["up"])}</ul></section>'
            f'<section class="panel"><h2>下游燈(交接與登錄)</h2><ul>{lis(rep["down"])}</ul></section></div>\n'
            f'<div class="grid">{"".join(kpis)}</div>\n'
            f'<section class="panel"><h2>端點矩陣(市場 × 報表 × 業別;擷取台帳各端點最近一次)</h2><div class="scroll"><table id="endpointMatrix">'
            f'<thead><tr><th>報表</th><th>業別</th>{"".join(f"<th>{_e(MARKET_ZH.get(m, m))}</th>" for m in mk)}</tr></thead><tbody>{"".join(ep_rows)}</tbody></table></div></section>\n'
            f'<section class="panel"><h2>各季家數與項數</h2><svg id="chart" role="img" aria-label="各季家數" viewBox="0 0 360 240"></svg>'
            f'<div class="scroll"><table id="periodTable"><thead><tr><th>市場</th><th>季</th><th>季底</th><th>報表</th><th>家數</th><th>項數</th></tr></thead>'
            f'<tbody>{per_rows}</tbody></table></div></section>\n'
            f'<section class="panel"><h2>還缺什麼、怎麼補</h2>{todo_html}{"".join(f"<code class=cmd>{_e(c)}</code>" for c in cmds)}</section>\n'
            f'<section class="panel"><h2>上下連結</h2><div class="scroll"><table id="linkTable"><thead><tr><th>方向</th><th>連結</th><th>燈</th><th>說明</th><th>路徑</th></tr></thead>'
            f'<tbody>{link_rows}</tbody></table></div></section>\n'
            f'<footer>頁內嵌快照 · 零網路 · 零外連 · 資料庫只讀 · 產生器 {_e(Path(__file__).name)} · 判準 {_e(rep.get("e82", {}).get("src") or "—")} mops_plan · '
            f'新鮮度 正典 period_lag · 燈號冊 {_e(book.get("src") or "—")} · 再產 {REFRESH}</footer>\n</main>\n'
            f'<script type="application/json" id="vrnEnvelope">{_json_script(env)}</script>\n'
            f'<script type="application/json" id="vrnMeta">{_json_script(meta)}</script>\n'
            f'<script>{_JS}</script>\n</body>\n</html>\n')


# ── 組一趟 ──────────────────────────────────────────────────────────────
def compose(db=None, today: date | None = None, page: Path = PAGE, *, e82_dir: Path = E82_DIR, pkg_root: Path = PKG,
            reg: Path = REG, vrn_root: Path = HERE, contracts=UI_CONTRACTS, now: datetime | None = None) -> dict:
    """上游現量 + 下游現解 → (報告, 信封, 套件, 燈號冊)。不寫檔。"""
    today, now = today or date.today(), now or datetime.now()
    e82, eng = upstream(e82_dir)
    book, pkg = lamp_book(vrn_root), package(pkg_root)
    ups = [_link("up", "e82", "上游引擎 VDF_ENG082", eng["state"], f"{eng['src'] or '—'}(判準 mops_target / mops_plan 用它自己的)" + (f" · {eng['why']}" if eng["why"] else ""),
                 _rel(e82_dir), "拉最新 main;ENG082 是 VDF 家族的引擎")]
    if e82 is None:
        d = {"db": str(db or ""), "db_state": "ABSENT", "db_why": eng["why"], "target": {}, "eps": [], "markets": [], "latest": [], "periods": [],
             "listed": {}, "latest_date": {}, "tables": [], "stamp": {"fetched_at": "", "n_rows": 0, "n_log": 0}, "plan": {}}
        markets, endpoints = [], []
    else:
        dbp = e82._resolve_db(str(db) if db else None)
        d = gather(e82, dbp, today)
        markets, endpoints = assess(e82, d, today)
        ups.append(_link("up", "db", "資料庫(唯讀)", d["db_state"], (d["db_why"] or f"表 {', '.join(d['tables']) or '—'} · 長表 {d['stamp']['n_rows']:,} 項 · 台帳 {d['stamp']['n_log']} 筆"),
                         d["db"] or "(沒找到)", "via-finstat run --mops(閘由你開)"))
        for x in markets:
            ups.append(_link("up", f"market:{x['market']}", f"{x['zh']} 完整度", x["completeness"]["state"], x["completeness"]["text"], "tw_financial_mops_log",
                             "via-finstat run --mops(只補還缺的端點)"))
            ups.append(_link("up", f"fresh:{x['market']}", f"{x['zh']} 新鮮度", x["freshness"]["state"], x["freshness"]["text"], "tw_financial_mops",
                             "下一季公告後 via-finstat run --mops"))
    integ, ro, uc = pkg_integrity(pkg_root, reg), roster_link(page, reg), uicontract_link(page, contracts)
    downs = [_link("down", "contract", "SYNCHRONIZER 契約", pkg["state"],
                   (f"鍵名 {pkg.get('sync_key')} · 頻道 {pkg.get('sync_channel')}(中央 UI 同)" if pkg["state"] == "GREEN" else pkg["why"]),
                   _rel(pkg["sync_page"]), "重看 VIA_HTML_UI 套件版本;本支現讀,重跑 run 即跟上"),
             _link("down", "integrity", "套件完整", integ["state"], f"{integ.get('src') or '—'} · sha256 {integ.get('sha_ok', '?')}/{integ.get('files', '?')}"
                   + (f" · {integ['why']}" if integ.get("why") else ""), _rel(pkg_root), "via-uiunify template(看治法)"),
             _link("down", "lampbook", "燈號冊", book["state"], f"{book.get('src') or '—'} · {len(book.get('lamps') or {})} 盞" + (f" · {book['why']}" if book["why"] else ""),
                   _rel(vrn_root), "VRN_SystemManager 尾版的 LAMPS"),
             _link("down", "roster", "家族頁名冊", ro["state"], (f"{ro['src']} {ro.get('family')} 第 {ro.get('index')} 項 → {ro.get('refresh')} 會自動重產"
                                                            if ro["state"] == "GREEN" else ro["why"]), _rel(reg), "CGC_MDL138 新版 ROSTER 加這一項"),
             _link("down", "uicontract", "U/I 契約", uc["state"], (f"{uc['src']} · 擁有者 {uc.get('owner')} · 家族 {uc.get('family')}" if uc["state"] == "GREEN" else uc["why"]),
                   uc.get("src", ""), "via-workflow ui-contract")]
    rep = {"schema": "VIA.VRN.FinStatementsTemplate.v1", "engine": Path(__file__).name, "version": VERSION,
           "generated": now.strftime("%Y-%m-%d %H:%M:%S"), "today": today.isoformat(), "db": d["db"], "stamp": d["stamp"], "target": d["target"],
           "e82": eng, "markets": markets, "endpoints": endpoints, "periods": d["periods"], "plan": d["plan"], "up": ups, "down": downs,
           "page": _rel(page), "lamp_book": book.get("src", ""), "package": {k: pkg.get(k) for k in ("state", "release", "sync_key", "sync_channel", "why")}}
    env = build_envelope(d, markets, ups, downs, pkg, book, now)
    bad = validate(env, pkg) if pkg.get("types") and pkg.get("system_modules") else ["套件不在或讀不動,信封沒有系統模組可留"]
    rep["down"].append(_link("down", "envelope", "信封合 SYNCHRONIZER 規格", "GREEN" if not bad else ("ABSENT" if pkg["state"] == "ABSENT" else "RED"),
                             ("模組 {} · 圖表 {} · 歷史列 {}".format(len(env["modules"]), len(env["analytics"]["charts"]), len(env["analytics"]["history"])) if not bad
                              else "; ".join(bad[:4])), "", "回報給我(信封規格對不上是本支的錯)"))
    rep["template"] = {"id": TEMPLATE_ID, "name": env["analytics"]["templateName"]}
    rep["verdict_up"], rep["verdict_down"] = worst(x["state"] for x in rep["up"]), worst(x["state"] for x in rep["down"])
    return {"report": rep, "envelope": env, "package": pkg, "book": book, "problems": bad}


def run(db=None, today: date | None = None, page: Path = PAGE, out: Path = OUT, do_print: bool = True, **kw) -> int:
    t0 = time.time()
    c = compose(db, today, page, **kw)
    rep, env, pkg, book = c["report"], c["envelope"], c["package"], c["book"]
    out = Path(out)
    rep["files"] = {k: _rel(out / v) for k, v in FILES.items()}
    try:
        _LIB.jwrite(out / FILES["sync"], env, indent=1, newline=True)
        _LIB.jwrite(out / FILES["profile"], profile_of(env), indent=1, newline=True)
        _atomic(out / FILES["history"], history_csv(env))
        _atomic(page, render_page(rep, env, pkg, book, page))
        rep["elapsed_s"] = round(time.time() - t0, 2)
        _LIB.jwrite(out / FILES["report"], rep, indent=1, newline=True)
    except OSError as exc:
        print(f"[FAIL] 寫不進去:{type(exc).__name__}: {exc}")
        return 1
    ups = [x["state"] for x in rep["up"]]
    rc = rc_of(ups + [x["state"] for x in rep["down"] if x["id"] in ("contract", "envelope")])      # 資料燈 + 交接契約 + 信封;登錄類燈由 check 管
    rep["rc"] = rc
    _LIB.jwrite(out / FILES["report"], rep, indent=1, newline=True)
    if do_print:
        tg = rep.get("target") or {}
        print(f"[VRN 財報模板] VRN_ENG090 v{VERSION} · 上游 {rep['e82'].get('src') or '—'} · 庫 {rep['db'] or '—'} · 今天 {rep['today']}"
              f"(該齊 {tg.get('qe') or '?'} 那一季,期限 {tg.get('due') or '?'})")
        for x in rep["up"]:
            print(f"  [{x['state']:<6}] 上 {x['name']}:{x['detail']}")
        for x in rep["down"]:
            print(f"  [{x['state']:<6}] 下 {x['name']}:{x['detail']}")
        print(f"  [落檔] 頁 {_rel(page)} · 信封 {rep['files']['sync']} · 範本冊 {rep['files']['profile']} · 歷史 CSV {rep['files']['history']} · 報告 {rep['files']['report']}")
        print("  [交接] 開頁按「交接到 SYNCHRONIZER」;或在 SYNCHRONIZER 按「匯入 JSON/CSV/Excel」選信封檔")
        n_sys = sum(1 for m in env["modules"] if m.get("system"))
        print(f"[VRN 財報模板計] {worst(ups)} · 模組 {n_sys}+{len(env['modules']) - n_sys} · 圖表 {len(env['analytics']['charts'])} · "
              f"歷史列 {len(env['analytics']['history'])} · {rep['elapsed_s']}s · rc={rc}")
    return rc


def _embedded(text: str, id_: str):
    m = re.search(r'<script type="application/json" id="%s">(.*?)</script>' % re.escape(id_), text, re.S)
    return json.loads(m.group(1)) if m else None


def check(db=None, today: date | None = None, page: Path = PAGE, out: Path = OUT, do_print: bool = True, **kw) -> dict:
    """上下連結逐條檢查(不寫任何檔)。上游同 run 現量;下游另驗:頁在不在 · 頁與庫同一時點 · 頁內鍵名 = 套件現讀 ·
    頁內信封合規格 · 頁零外連 · 信封檔 = 頁內嵌那一份。"""
    c = compose(db, today, page, **kw)
    rep, pkg = c["report"], c["package"]
    downs = [x for x in rep["down"] if x["id"] != "envelope"]
    page, out = Path(page), Path(out)
    if not page.is_file():
        downs.append(_link("down", "page", "VRN 財報頁", "ABSENT", "頁還沒產", _rel(page), f"{REFRESH} 或本支 run"))
    else:
        t = page.read_text(encoding="utf-8")
        env_p, meta = _embedded(t, "vrnEnvelope"), _embedded(t, "vrnMeta") or {}
        same = (meta.get("dataStamp") or {}) == rep["stamp"] and meta.get("e82", "") == (rep["e82"].get("src") or "")
        downs.append(_link("down", "page_sync", "頁與庫同一時點", "GREEN" if same else "STALE",
                           (f"資料 {rep['stamp']['fetched_at'] or '—'} · 長表 {rep['stamp']['n_rows']:,} 項" if same else
                            f"頁 {(meta.get('dataStamp') or {}).get('fetched_at') or '—'}({meta.get('e82') or '—'})≠ 庫 {rep['stamp']['fetched_at'] or '—'}({rep['e82'].get('src') or '—'})"),
                           _rel(page), f"{REFRESH} 或本支 run(重產)"))
        kc = (meta.get("key"), meta.get("channel")) == (pkg.get("sync_key"), pkg.get("sync_channel"))
        downs.append(_link("down", "page_key", "頁內鍵名 = 套件現讀", "GREEN" if kc and pkg["state"] == "GREEN" else ("ABSENT" if pkg["state"] == "ABSENT" else "RED"),
                           f"頁 {meta.get('key')} / {meta.get('channel')} · 套件 {pkg.get('sync_key')} / {pkg.get('sync_channel')}", _rel(page), "本支 run(重產)"))
        bad = validate(env_p or {}, pkg) if pkg.get("types") and pkg.get("system_modules") else ["套件不在或讀不動"]
        downs.append(_link("down", "page_env", "頁內信封合 SYNCHRONIZER 規格", "GREEN" if not bad else ("ABSENT" if pkg["state"] == "ABSENT" else "RED"),
                           "合" if not bad else "; ".join(bad[:3]), _rel(page), "本支 run(重產)"))
        hits = offline_hits(t, kw.get("reg", REG))
        downs.append(_link("down", "offline", "頁零外連", "ABSENT" if hits is None else ("GREEN" if not hits else "RED"),
                           "CGC_MDL160 四道尺 0 命中" if hits == {} else (f"命中 {hits}" if hits else "CGC_MDL160 不在(尺缺件)"), _rel(page), "回報給我"))
        ef = out / FILES["sync"]
        if not ef.is_file():
            downs.append(_link("down", "envfile", "信封檔 = 頁內嵌", "ABSENT", "信封檔不在", _rel(ef), "本支 run"))
        else:
            try:
                same_env = json.loads(ef.read_text(encoding="utf-8")) == env_p
            except Exception:
                same_env = False
            downs.append(_link("down", "envfile", "信封檔 = 頁內嵌", "GREEN" if same_env else "STALE",
                               "同一趟" if same_env else "信封檔跟頁不是同一趟產的(或被改過)", _rel(ef), "本支 run(兩個一起重產)"))
    rep["down"] = downs
    states = [x["state"] for x in rep["up"] + downs]
    rep["rc"] = rc_of(states)
    if do_print:
        print(f"=== [VRN_ENG090 v{VERSION}] 上下連結檢查 · 庫 {rep['db'] or '—'} · 頁 {_rel(page)} ===")
        for x in rep["up"] + downs:
            print(f"  [{x['state']:<6}] {'上' if x['dir'] == 'up' else '下'} {x['name']}:{x['detail']}" + (f"  → {x['fix']}" if x["state"] != "GREEN" and x.get("fix") else ""))
        print(f"  [計] 上 {len(rep['up'])} · 下 {len(downs)} · 最壞 {worst(states)} → rc{rep['rc']}")
    return rep


def status(out: Path = OUT) -> int:
    p = Path(out) / FILES["report"]
    if not p.is_file():
        print(f"[VRN 財報模板] 還沒跑過(NODATA):{_rel(p)} 不在 → 本支 run 或 {REFRESH}")
        return 2
    rep = json.loads(p.read_text(encoding="utf-8"))
    print(f"[VRN 財報模板] 上一趟 {rep.get('generated')} · 上游 {rep.get('verdict_up')} · 下游 {rep.get('verdict_down')} · rc {rep.get('rc')} · 範本 {(rep.get('template') or {}).get('name')}")
    for x in rep.get("markets") or []:
        print(f"  [{x['lamp']:<6}] {x['zh']}:完整度 {x['completeness']['text']} · 新鮮度 {x['freshness']['text']}")
    return int(rep.get("rc", 2))


# ── 自測 ─────────────────────────────────────────────────────────────────
def broken_envs(env: dict) -> list:
    """驗器正控用:六種各壞一處的信封(值是字串 / 日期空 / 圖表 id 重複 / 模組型別亂 / 系統模組沒留 / view 空)。"""
    import copy
    out = []
    b = copy.deepcopy(env); b["analytics"]["history"][0]["value"] = str(b["analytics"]["history"][0]["value"]); out.append(b)
    b = copy.deepcopy(env); b["analytics"]["history"][0]["date"] = ""; out.append(b)
    b = copy.deepcopy(env); b["analytics"]["charts"].append(dict(b["analytics"]["charts"][0])); out.append(b)
    b = copy.deepcopy(env); b["modules"][-1]["type"] = "weird"; out.append(b)
    b = copy.deepcopy(env); b["modules"] = [m for m in b["modules"] if not m.get("system")]
    for i, m in enumerate(b["modules"]):
        m["order"] = i + 1
    out.append(b)
    b = copy.deepcopy(env); b["view"] = {}; out.append(b)
    return out


def selftest() -> int:
    import hashlib
    import shutil
    import tempfile
    fails, n = [], [0]

    def chk(name, cond, note=""):
        n[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    try:
        import duckdb
    except Exception:
        print("  [SKIP] 這個 python 沒有 duckdb:自測要建暫存庫,誠實跳過(NODATA)")
        return 2
    global _CONNECT
    e82, eng = upstream()
    if e82 is None:
        print(f"  [SKIP] 上游 ENG082 不在:{eng['why']}(ABSENT)")
        return 3
    today = date(2026, 9, 24)
    now = datetime(2026, 9, 24, 20, 0, 0)
    eps = [(st, ind) for st in e82.MOPS_ST for ind in e82.MOPS_IND]

    def mkdb(p: Path, markets=("TPEX", "TWSE"), blocked=(), fetched="2026-09-20 10:00:00", extra_ind=None, extra_period=False, evil=False, denied=()):
        con = duckdb.connect(str(p))
        con.execute(f"CREATE TABLE {e82.MOPS_TABLE} ({e82.MOPS_SCHEMA})")
        con.execute(f"CREATE TABLE {e82.MOPS_LOG} ({e82.MOPS_LOG_SCHEMA})")
        con.execute("CREATE TABLE tw_listings (code VARCHAR, name VARCHAR, market VARCHAR)")
        for m in markets:
            for c in ("1101", "1102", "1103"):
                con.execute("INSERT INTO tw_listings VALUES (?, ?, ?)", [f"{m[:1]}{c}", "<script>alert(1)</script>" if evil else "某公司", m])
            for st, ind in eps:
                sname = e82.MOPS_ST[st]
                src = e82._mops_source(m, st, ind)
                if m in blocked or m in denied:
                    con.execute(f"INSERT INTO {e82.MOPS_LOG} VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                [m, sname, ind, src, "BLOCKED" if m in blocked else "DENY", None, 0, 0, None, None, "安全頁" if m in blocked else "閘沒開", fetched])
                    continue
                n_items = 4 if ind == "ci" else 0
                for c in (("1101", "1102") if ind == "ci" else ()):
                    for item in ("營業收入", "淨利") if sname == "IS" else ("資產總計", "負債總計"):
                        con.execute(f"INSERT INTO {e82.MOPS_TABLE} (date, code, name, market, industry, statement, basis, item, value, unit, period, report_date, source, fetched_at) "
                                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                    ["2026-06-30", f"{m[:1]}{c}", "<script>alert(1)</script>" if evil else "某公司", m, ind, sname, "YTD" if sname == "IS" else "POINT",
                                     item, 1.0, "仟元", "2026Q2", "115/08/10", src, fetched])
                con.execute(f"INSERT INTO {e82.MOPS_LOG} VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                            [m, sname, ind, src, "OK", 3 if n_items else 1, n_items, n_items, "2026Q2" if n_items else None, "2026-06-30" if n_items else None,
                             "ok", fetched])
            if extra_ind:
                con.execute(f"INSERT INTO {e82.MOPS_LOG} VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [m, "IS", extra_ind, f"x_{m}_{extra_ind}", "OK", 1, 0, 0, None, None, "新業別", fetched])
            if evil:                                                  # 市場代號 / 業別 / 備註都是惡意字串(自動新增會把它帶進頁與信封)
                bad = "</script><script>alert(1)</script>"
                con.execute(f"INSERT INTO {e82.MOPS_LOG} VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [bad, "IS", "<img src=x onerror=alert(3)>", "evil_src", "OK", 1, 1, 1,
                                                                                         "2026Q2", "2026-06-30", "<!--<script>alert(2)", fetched])
                con.execute(f"INSERT INTO {e82.MOPS_TABLE} (date, code, name, market, industry, statement, basis, item, value, unit, period, report_date, source, fetched_at) "
                            "VALUES ('2026-06-30', 'E1', ?, ?, 'ci', 'IS', 'YTD', '營業收入', 1.0, '仟元', '2026Q2', '115/08/10', 'evil_src', ?)", [bad, bad, fetched])
                evil = False                                          # 只插一次
            if extra_period:
                con.execute(f"INSERT INTO {e82.MOPS_TABLE} (date, code, name, market, industry, statement, basis, item, value, unit, period, report_date, source, fetched_at) "
                            "VALUES ('2026-03-31', ?, '某公司', ?, 'ci', 'IS', 'YTD', '營業收入', 1.0, '仟元', '2026Q1', '115/05/10', 'old', '2026-05-20 10:00:00')", [f"{m[:1]}1101", m])
        con.close()
        return p

    def md5(p: Path) -> str:
        return hashlib.md5(Path(p).read_bytes()).hexdigest()

    with tempfile.TemporaryDirectory(prefix="vrn89_") as td:
        T = Path(td)
        reg = T / "reg"
        reg.mkdir()
        (T / "vrn").mkdir()
        famsrc = _newest(REG, GLOBS["famui"])
        gatesrc = _newest(REG, GLOBS["gate"])
        vsys = _newest(HERE, GLOBS["vrnsys"])
        shutil.copyfile(gatesrc, reg / gatesrc.name)
        shutil.copyfile(vsys, T / "vrn" / vsys.name)
        page = T / "ui" / "VIA_UI_VRNFinStatements_v0100.html"
        roster_ok = "ROSTER = " + repr({"vrn": [{"zh": "VRN 交易所財報模板", "dir": "functional modules/VRN", "glob": "VRN_ENG090_FinStatementsTemplate_v*.py",
                                                  "args": ["run"], "page": str(page), "timeout": 300, "python": "family", "data_gate": True}]}) + "\n"
        (reg / "CGC_MDL138_FamilyUI_v0999.py").write_text(roster_ok, encoding="utf-8")
        contract = T / "UI_CONTRACT_latest.json"
        contract.write_text(json.dumps({"pages": [{"page": page.name, "owner": Path(__file__).name, "family": "vrn", "refresh": ""}]}, ensure_ascii=False), encoding="utf-8")
        kw = {"reg": reg, "vrn_root": T / "vrn", "contracts": (contract,), "now": now}

        # ① 全齊:兩市場 24 端點都在期限之後抓成功 → 上游全綠 rc0;寫五個檔、零寫到暫存夾外
        db1 = mkdb(T / "full.duckdb")
        h1 = md5(db1)
        out1 = T / "out1"
        buf = io.StringIO()
        import contextlib
        holder = duckdb.connect(str(db1), read_only=True)          # 旁邊有人唯讀開著(工作站常態):本支也只能唯讀,設成讀寫就開不了
        try:
            with contextlib.redirect_stdout(buf):
                rc = run(db1, today, page, out1, **kw)
        finally:
            holder.close()
        rep = json.loads((out1 / FILES["report"]).read_text(encoding="utf-8"))
        chk("① 全齊(兩市場 24 端點期限後抓成功)→ 上游全綠 · rc0 · 五個檔落在指定夾", rc == 0 and rep["verdict_up"] == "GREEN"
            and all((out1 / f).is_file() for f in FILES.values()) and page.is_file(), f"(rc {rc} · 上 {rep['verdict_up']} · 下 {rep['verdict_down']})")
        chk("② 唯讀:旁邊有人唯讀開著照樣跑得動(同組態才共存)· run 前後暫存庫 md5 相同(判準交給 ENG082 mops_plan,它也只讀)", md5(db1) == h1 and rc == 0)
        env = json.loads((out1 / FILES["sync"]).read_text(encoding="utf-8"))
        pkg = package()
        sysm = [m for m in env["modules"] if m.get("system")]
        chk("③ 信封合 SYNCHRONIZER 規格(型別 / 圖表型別 / 樞紐 / slug 全從套件現讀);系統模組 = 套件 DEFAULT_MODULES 的 system 那幾個、排最前;"
            "驗器正控:值是字串 / 日期空 / 圖表 id 重複 / 模組型別亂 / 系統模組沒留 / view 空 六種壞信封都抓得到",
            not validate(env, pkg) and [m["id"] for m in sysm] == [m["id"] for m in pkg["system_modules"]] and env["modules"][:len(sysm)] == sysm
            and all(validate(b, pkg) for b in broken_envs(env)),
            f"(問題 {validate(env, pkg)[:2]} · 系統 {len(sysm)} · 全部 {len(env['modules'])})")
        hist = env["analytics"]["history"]
        mets = {h["metric"] for h in hist}
        chk("④ 歷史列一市場一季一指標一列、值是數字;圖表只為有資料列的指標長(不空畫)",
            {"上櫃損益家數", "上櫃資產負債家數", "上櫃項數", "上櫃端點齊", "上櫃冊上家數", "上市損益家數"} <= mets
            and all(isinstance(h["value"], int) for h in hist) and {c["metric"] for c in env["analytics"]["charts"]} == mets
            and next(h["value"] for h in hist if h["metric"] == "上櫃損益家數") == 2 and next(h["value"] for h in hist if h["metric"] == "上櫃端點齊") == 12
            and next(h["value"] for h in hist if h["metric"] == "上櫃項數") == 8,
            f"(列 {len(hist)} · 指標 {len(mets)} · 圖 {len(env['analytics']['charts'])})")
        t = page.read_text(encoding="utf-8")
        hits = offline_hits(t, reg)
        chk("⑤ 頁零外連(CGC_MDL160 四道尺 0 命中;正控:塞一個 fetch( 尺就抓到)· 頁內信封 == 信封檔 · 頁內鍵名 / 頻道 = 套件現讀 · 配色變數現讀套件 :root",
            hits == {} and offline_hits("<script>fetch('x')</script>", reg) == {"fetch(": 1}
            and _embedded(t, "vrnEnvelope") == env and (_embedded(t, "vrnMeta") or {}).get("key") == pkg["sync_key"]
            and (_embedded(t, "vrnMeta") or {}).get("channel") == pkg["sync_channel"] and "--teal:" in t and "__TOKENS__" not in t,
            f"(命中 {hits})")
        ck = check(db1, today, page, out1, do_print=False, **kw)
        chk("⑥ check:頁與庫同一時點 · 名冊 / U/I 契約 / 套件 / 燈號冊 / 頁內信封 / 信封檔全綠 → rc0",
            ck["rc"] == 0 and all(x["state"] == "GREEN" for x in ck["down"]), f"(下 {[(x['id'], x['state']) for x in ck['down'] if x['state'] != 'GREEN']})")

        # ⑦ 部分:上市 12 端點被交易所擋 → 上市完整度 NODATA「缺 12/12 · 交易所擋」,rc2,頁照產;模組名帶燈
        db2 = mkdb(T / "part.duckdb", blocked=("TWSE",))
        out2 = T / "out2"
        with contextlib.redirect_stdout(io.StringIO()):
            rc2 = run(db2, today, page, out2, **kw)
        rep2 = json.loads((out2 / FILES["report"]).read_text(encoding="utf-8"))
        tw = next(x for x in rep2["markets"] if x["market"] == "TWSE")
        env2 = json.loads((out2 / FILES["sync"]).read_text(encoding="utf-8"))
        chk("⑦ 上市 12 端點被擋 → 上市完整度 缺料「缺 12/12 · 交易所擋」· rc2 · 頁照產 · 上市模組名帶 🟡、上櫃帶 🟢",
            rc2 == 2 and tw["completeness"]["state"] == "NODATA" and "缺 12/12" in tw["completeness"]["text"] and "交易所擋" in tw["completeness"]["text"]
            and any(m["id"] == "vrn-finstat-twse" and "🟡" in m["name"] for m in env2["modules"]) and any(m["id"] == "vrn-finstat-tpex" and "🟢" in m["name"] for m in env2["modules"]),
            f"(rc {rc2} · {tw['completeness']['text']})")
        chk("⑧ 被擋的市場沒有家數資料 → 不長它的家數圖(只長端點齊 KPI);補抓計畫模組寫出要補幾個、用哪一令",
            not any(c["metric"] == "上市損益家數" for c in env2["analytics"]["charts"]) and any(c["metric"] == "上市端點齊" for c in env2["analytics"]["charts"])
            and next(h["value"] for h in env2["analytics"]["history"] if h["metric"] == "上市端點齊") == 0
            and any(m["id"] == "vrn-finstat-plan" and "仍缺 12" in m["note"] and "via-finstat run --mops" in m["note"] for m in env2["modules"]))

        db2b = mkdb(T / "deny.duckdb", denied=("TWSE",))
        with contextlib.redirect_stdout(io.StringIO()):
            rc2b = run(db2b, today, page, T / "out2b", **kw)
        tw2 = next(x for x in json.loads((T / "out2b" / FILES["report"]).read_text(encoding="utf-8"))["markets"] if x["market"] == "TWSE")
        chk("⑨ 上市 12 端點是閘沒開(DENY)→ 完整度 閘「閘沒開(閘由你開)」、不是缺料 · rc2", rc2b == 2 and tw2["completeness"]["state"] == "GATED" and "閘沒開" in tw2["completeness"]["text"],
            f"({tw2['completeness']['text']})")

        # ⑨ 新鮮度:同一庫撥到 11/20(第三季期限 11/14 已過)→ 新鮮度過期、完整度也缺(ENG082 判舊季)
        with contextlib.redirect_stdout(io.StringIO()):
            rc3 = run(db1, date(2026, 11, 20), page, T / "out3", **kw)
        rep3 = json.loads((T / "out3" / FILES["report"]).read_text(encoding="utf-8"))
        tp = next(x for x in rep3["markets"] if x["market"] == "TPEX")
        chk("⑩ 撥到 11/20:新鮮度 過期「已過 6 日」(正典 period_lag)· 完整度照 ENG082 判「缺 12/12」· 市場燈取最壞(過期 > 缺料)· rc2",
            rc3 == 2 and tp["freshness"]["state"] == "STALE" and "已過 6 日" in tp["freshness"]["text"] and tp["completeness"]["state"] == "NODATA"
            and tp["lamp"] == "STALE" and rep3["verdict_up"] == "STALE",
            f"({tp['freshness']['text']} · {tp['completeness']['text']})")

        # ⑩ 自動新增:台帳多一個業別、長表多一季 → 端點矩陣、歷史列、圖表自己長出來(不改碼)
        db4 = mkdb(T / "grow.duckdb", extra_ind="zz", extra_period=True)
        with contextlib.redirect_stdout(io.StringIO()):
            run(db4, today, page, T / "out4", **kw)
        rep4 = json.loads((T / "out4" / FILES["report"]).read_text(encoding="utf-8"))
        env4 = json.loads((T / "out4" / FILES["sync"]).read_text(encoding="utf-8"))
        chk("⑪ 自動新增:台帳多一個業別 zz → 端點矩陣多一列(冊外不判齊);長表多一季 2026Q1 → 歷史列多那一季(一個指標一張圖,不重複);KPI 取最新一季;判齊不受影響",
            any(e["industry"] == "zz" and e["missing"] is None for e in rep4["endpoints"])
            and {h["date"] for h in env4["analytics"]["history"] if h["metric"] == "上櫃損益家數"} == {"2026-03-31", "2026-06-30"}
            and rep4["verdict_up"] == "GREEN" and not validate(env4, pkg)
            and next(x for x in rep4["markets"] if x["market"] == "TPEX")["latest_period"] == "2026Q2", f"(問題 {validate(env4, pkg)[:2]})")

        # ⑪ 庫不在 / 撞鎖 → 缺料並講原因,不是「缺 12/12」;頁照產
        with contextlib.redirect_stdout(io.StringIO()):
            rc5 = run(T / "nope.duckdb", today, page, T / "out5", **kw)
        rep5 = json.loads((T / "out5" / FILES["report"]).read_text(encoding="utf-8"))
        _CONNECT = lambda dbp: (None, "IOException: Could not set lock on file")      # noqa: E731
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                rc6 = run(db1, today, page, T / "out6", **kw)
        finally:
            _CONNECT = _connect_ro
        rep6 = json.loads((T / "out6" / FILES["report"]).read_text(encoding="utf-8"))
        chk("⑫ 庫不在 → 缺料「先 via-finstat run --mops」rc2;撞鎖 → 缺料「撞鎖」rc2(不當成全缺、不喊 缺 12/12)",
            rc5 == 2 and "run --mops" in rep5["up"][1]["detail"] and rc6 == 2 and "撞鎖" in rep6["up"][1]["detail"]
            and not any("缺 12/12" in x["completeness"]["text"] for x in rep6["markets"]), f"({rep6['up'][1]['detail'][:40]})")

        # ⑫ 上游缺件:ENG082 夾是空的 → 上游 ABSENT、rc3、頁照產(誠實)
        (T / "empty").mkdir()
        with contextlib.redirect_stdout(io.StringIO()):
            rc7 = run(db1, today, page, T / "out7", e82_dir=T / "empty", **kw)
        rep7 = json.loads((T / "out7" / FILES["report"]).read_text(encoding="utf-8"))
        chk("⑬ 上游 ENG082 不在 → 上游燈 缺件 · rc3 · 頁照產(不假裝有資料)", rc7 == 3 and rep7["up"][0]["state"] == "ABSENT" and page.is_file())

        # ⑬ check 抓得到下游斷線:庫多寫一筆 → 頁過期;名冊沒登錄 → 缺件;信封檔被改 → 過期;套件鍵名變了 → 壞
        with contextlib.redirect_stdout(io.StringIO()):
            run(db1, today, page, out1, **kw)
        con = duckdb.connect(str(db1))
        con.execute(f"INSERT INTO {e82.MOPS_LOG} (market, statement, industry, source, state, n_items, n_stored, fetched_at) VALUES ('TPEX','IS','ci','x','OK',0,0,'2026-09-21 09:00:00')")
        con.close()
        ck2 = check(db1, today, page, out1, do_print=False, **kw)
        chk("⑭ 庫比頁新 → 「頁與庫同一時點」過期 · rc2", next(x for x in ck2["down"] if x["id"] == "page_sync")["state"] == "STALE" and ck2["rc"] == 2)
        (reg / "CGC_MDL138_FamilyUI_v0999.py").write_text("ROSTER = {'vrn': []}\n", encoding="utf-8")
        ef = out1 / FILES["sync"]
        ef.write_text(ef.read_text(encoding="utf-8").replace("VRN 財報總覽", "被改過"), encoding="utf-8")
        ck3 = check(db1, today, page, out1, do_print=False, **kw)
        st3 = {x["id"]: x["state"] for x in ck3["down"]}
        chk("⑮ 名冊沒這支 → 缺件(via-vrnui 不會重產)· 信封檔跟頁不同 → 過期 · rc3", st3.get("roster") == "ABSENT" and st3.get("envfile") == "STALE" and ck3["rc"] == 3, f"({st3})")
        (reg / "CGC_MDL138_FamilyUI_v0999.py").write_text(roster_ok, encoding="utf-8")
        fake = T / "pkg"
        (fake / "ui").mkdir(parents=True)
        for q in ("VIA-SYNCHRONIZER-Standalone.html", "VIA-UI-Standalone-NoServer.html"):
            shutil.copyfile(PKG / "ui" / q, fake / "ui" / q)
        sp = fake / "ui" / "VIA-SYNCHRONIZER-Standalone.html"
        sp.write_text(re.sub(r"(\bKEY\s*=\s*')via\.sync\.state\.v2'", r"\1via.sync.state.v3'", sp.read_text(encoding="utf-8"), count=1), encoding="utf-8")
        ck4 = check(db1, today, page, out1, do_print=False, pkg_root=fake, **kw)
        st4 = {x["id"]: x["state"] for x in ck4["down"]}
        with contextlib.redirect_stdout(io.StringIO()):
            rc4 = run(db1, today, T / "ui_fake" / page.name, T / "out_fake", pkg_root=fake, **kw)
        chk("⑯ 套件把 SYNCHRONIZER 鍵名換成 v3(中央 UI 沒換)→ 契約壞 · 頁內鍵名 ≠ 套件 → 壞 · check 與 run 都 rc1(不默默交接到沒人聽的鍵)",
            st4.get("contract") == "RED" and st4.get("page_key") == "RED" and ck4["rc"] == 1 and rc4 == 1, f"({st4.get('contract')} · {st4.get('page_key')} · run rc {rc4})")
        chk("⑰ 套件完整閘借 CGC_MDL160:真套件 sha256 全對 GREEN;假套件沒有 manifest → 缺件", st3.get("integrity") == "GREEN" and st4.get("integrity") == "ABSENT")
        with contextlib.redirect_stdout(io.StringIO()):
            run(db1, today, page, out1, **kw)
        tp_ = page.read_text(encoding="utf-8")
        page.write_text(tp_.replace('"key":"via.sync.state.v2"', '"key":"via.sync.state.v1"').replace('"key": "via.sync.state.v2"', '"key": "via.sync.state.v1"'), encoding="utf-8")
        ck5 = check(db1, today, page, out1, do_print=False, **kw)
        st5 = {x["id"]: x["state"] for x in ck5["down"]}
        chk("⑱ 套件照舊、頁卻是舊鍵名產的(v1)→ 頁內鍵名 壞 · rc1(交接會寫到沒人聽的鍵)", st5.get("contract") == "GREEN" and st5.get("page_key") == "RED" and ck5["rc"] == 1,
            f"({st5.get('page_key')})")
        with contextlib.redirect_stdout(io.StringIO()):
            run(db1, today, page, out1, **kw)
        bad_owner = T / "UI_CONTRACT_bad.json"
        bad_owner.write_text(json.dumps({"pages": [{"page": page.name, "owner": "CGC_MDL999_Other_v0100.py", "family": "vrn"}]}), encoding="utf-8")
        broken = T / "UI_CONTRACT_broken.json"
        broken.write_text("{not json", encoding="utf-8")
        (T / "vrn2").mkdir()
        (T / "vrn2" / "VRN_SystemManager_v0999.py").write_text("LAMPS = {'GREEN': '綠', 'NODATA': '缺料', 'GATED': '閘', 'ABSENT': '缺件', 'RED': '壞'}\n", encoding="utf-8")
        kw2 = dict(kw, contracts=(bad_owner,), vrn_root=T / "vrn2")
        ck6 = check(db1, today, page, out1, do_print=False, **kw2)
        st6 = {x["id"]: x["state"] for x in ck6["down"]}
        ck7 = check(db1, today, page, out1, do_print=False, **dict(kw, contracts=(broken,)))
        u7 = next(x for x in ck7["down"] if x["id"] == "uicontract")
        chk("⑲ U/I 契約認的擁有者不是本支 → 壞 · 契約檔讀不動 → 壞並講檔名(不默默當沒收)· 燈號冊少一盞(過期)→ 壞",
            st6.get("uicontract") == "RED" and st6.get("lampbook") == "RED" and u7["state"] == "RED" and "UI_CONTRACT_broken.json" in u7["detail"],
            f"({st6.get('uicontract')} · {st6.get('lampbook')} · {u7['state']})")

        # ⑰ 跳脫:庫裡的市場代號 / 業別 / 備註是惡意字串(自動新增會把它帶進 KPI、矩陣、信封模組名)
        db8 = mkdb(T / "evil.duckdb", evil=True)
        with contextlib.redirect_stdout(io.StringIO()):
            run(db8, today, page, T / "out8", **kw)
        t8 = page.read_text(encoding="utf-8")
        env8 = json.loads((T / "out8" / FILES["sync"]).read_text(encoding="utf-8"))
        chk("⑳ 惡意字串進得了頁與信封但全跳脫:頁上只有自己那 3 個 <script、只有印章那 1 個 <img · HTML 見 &lt;/script&gt; · 內嵌 JSON 讀回 == 信封檔(字串原樣保留)",
            t8.count("<script") == 3 and t8.count("<img") == 1 and "<img src=x" not in t8 and "&lt;/script&gt;&lt;script&gt;alert(1)" in t8
            and _embedded(t8, "vrnEnvelope") == env8 and any("alert(1)" in m["name"] for m in env8["modules"]),
            f"(<script × {t8.count('<script')})")

        # ⑱ status 讀上一趟;沒跑過 = 缺料 rc2
        with contextlib.redirect_stdout(io.StringIO()):
            s_ok, s_no = status(out2), status(T / "none")
        chk("㉑ status 讀上一趟 JSON(rc 照那一趟)· 沒跑過 → 缺料 rc2", s_ok == 2 and s_no == 2)
    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    mods = {a.name.split(".")[0] for nd in ast.walk(tree) if isinstance(nd, ast.Import) for a in nd.names} | \
           {nd.module.split(".")[0] for nd in ast.walk(tree) if isinstance(nd, ast.ImportFrom) and nd.module}
    chk("㉒ 零網路 / 零安裝(語法樹:沒有 requests / urllib / socket / subprocess / pip)· 紀律宣告在(唯讀 / 正本零觸碰 / 零 CDN / 尾版律 / Zero-Hydra / ACCEL-BRIDGE)",
        not (mods & {"requests", "httpx", "urllib", "socket", "subprocess", "pip"})
        and all(k in src for k in ("唯讀", "正本零觸碰", "零 CDN", "尾版律", "Zero-Hydra", "ACCEL-BRIDGE")), f"({sorted(mods & {'requests', 'urllib', 'socket', 'subprocess'})})")
    print(f"  [計] 二十二檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def _argval(a: list, flag: str, default=None):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a):
            return a[i + 1]
    return default


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a or (a and a[0] == "selftest"):
        print(f"=== VRN_ENG090 交易所財報 VRN 模板頁 v{VERSION} · 二十二檢自測(暫存夾 · 零網路 · 不碰真庫)===")
        return selftest()
    verb = a[0] if a and not a[0].startswith("--") else "run"
    try:
        td = _argval(a, "--today")
        today = date.fromisoformat(td) if td else None
    except ValueError:
        print(f"[用法] --today 要 YYYY-MM-DD,收到 {td!r}")
        return 2
    db, page, out = _argval(a, "--db"), Path(_argval(a, "--page") or PAGE), Path(_argval(a, "--out") or OUT)
    try:
        if verb == "run":
            return run(db, today, page, out)
        if verb == "check":
            return check(db, today, page, out)["rc"]
        if verb == "status":
            return status(out)
        print(f"[用法] 動詞 {verb!r} 不認得。可用:run | check | status | --selftest")
        return 2
    except KeyboardInterrupt:
        print("[中斷] 已停(已寫的檔是完整的一份:原子寫入)")
        return 130


if __name__ == "__main__":
    sys.exit(main())
