#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL179_VcgcSyncHub v0100 — VCGC 資料樞紐(對帳層)· 批697

操作員令:「there should be a vcgc synchronizer as a data hub to coordinate and sync
functions from/to vcgc from/to supportive modules and systems and outside like
one drive / google drive / dropbox」

═══ 為什麼是「對帳」不是「搬運」——理由是量到的,不是我挑的 ═══

  · CGC_MDL059_MasterHub_v0108.py:83 儲存鐵則(2026-08-12):
      「**不落 OneDrive**——資料庫/新產物一律本機正典(repo VDF\db);
        OneDrive 舊件唯讀凍結參照,候 via-store --migrate 遷回」
  · CGC_MDL123_DataHome_v0103.py:26:
      「搬=link(hash 定生死、零刪除);**複製=三副本病,不做**」
  · CGC_MDL149_...v0123.py:44 兩台機器的實錄:
      「工作站有 TOOLS_PLAN=虛境 算活元件;容器沒有=退役;
        兩邊各 --apply 一次就**互翻**(批681/682/682B **三次**)」

  三條加起來只有一個意思:這個系統**已經因為副本互相覆蓋吃過三次虧**。
  再長一支「會自己複製檔案」的樞紐,是把那個病寫進制度。
  所以本支:**看得見、算得出、指得出手該怎麼動,但自己零搬移、零寫入對端。**
  要改成真的搬,那是**鐵則的修改**,裁定權在操作員(LL90),不在我。

═══ 本支補的那個洞(量過:樹上沒有任何一支做得到)═══

  CGC_MDL144_CopyDoctor 已經認得四副本(含 OneDrive),但它只比
  **git 分支/HEAD/ahead-behind + Register 版號 + 短令在不在**。
  於是批429-W4 那個症狀——「操作員的 OneDrive 副本沒有 vdf_tw_market.duckdb」——
  **現有任何一支都照不出來**:那是檔案在不在,不是 git 前後。
  本支補的就是這一層:**逐端點、逐面、內容定址的對帳**。

═══ 端點(委派 CopyDoctor.candidate_roots(),不自己再寫一把 LL341)═══

  self        本樹(正在跑我的這一份)
  copy        另一份 VIA 樹
  cloudfolder 路徑落在雲端同步根底下的副本(onedrive / dropbox / gdrive)
              —— **注意:這不是網路端點。** 同步是雲端用戶端在做,我方零網路。
  datahome    資料家(委派 CGC_MDL123_DataHome.resolve_home())
  api         名冊上宣告的 REST 連線 —— 一律 **GATED**,理由寫在臉上:
              全樹量過,SUP_MDL740 有 0 處 Authorization / Bearer / oauth,
              AegisNexus 只有一個沒人呼叫的 HeadersBuilder.json_api(token)。
              **系統裡根本沒有憑證機制**,而 AegisNexus 是批345 不可動律。
              所以 api 端點只登記、不假裝能跑。要接,是另一批、且要先改鐵則。

═══ 繼承來的盲點(量到的,寫在臉上)═══

  CopyDoctor.candidate_roots() 只認「**父夾叫 movies-dataset\* 且裡面有 Register 冊**」的副本。
  所以一份直接攤在 `OneDrive\VeritasIntelligenceAnalytics` 底下的樹(VRN 那批模組裡
  寫死的正是這個版型)**它掃不到**,而我委派它,就把這個盲點一起繼承了。
  補法不是另寫一把掃描器(那就是 Hydra),是給一條**明路**:
  名冊 SSOT 的 endpoints[] 可以逐筆指定,掃不到的自己寫上去;
  或 env VIA_COPY_ROOTS。兩條都走,結果取聯集、去重。

═══ 兩個面 ═══

  功能面  每端點的 VIA_Component_Inventory_SSOT_v0100.json(VCGC 的唯一寫入口產物)
          比 counters 與 ACTIVE key 集合。**不猜方向**:兩端各有獨有件=真分岔,
          本支只報不裁。並且直接算出「各跑一次 registry-sync --apply 會不會互翻」。
  資料面  名冊上宣告的產物(DB_PROBES + 契約件 + 冊)逐件內容定址比對。

═══ 誠實態(判錯的紅燈和假綠一樣傷)═══

  GREEN 兩邊一致 · RED 真分岔或有 provider 衝突副本 · NODATA 端點在位但這一面沒料可比
  ABSENT 端點不在這台機器上(**不是紅**:容器本來就看不到工作站的 OneDrive)
  GATED 宣告了但缺機制 · SKIP 規則上不比 · FIRST_RUN 第一次跑,沒有基準

  逐件:SAME / DIFF / ONLY_HERE / ONLY_THERE / CLOUD_ONLY / UNREADABLE

═══ 雲端資料夾的三個誠實檢(樹上零支在做)═══

  ① **在位 ≠ 同步好。** 雲端用戶端可能暫停、離線、上傳到一半。報最新 mtime 落差。
  ② **衝突副本**:provider 自己已經放棄合併了才會生出這種檔。看到就是 RED。
     判準要嚴:衝突副本**一定跟正本並排**,所以一律要求同名正本在旁才算數
     (只認檔名樣式會把 `報告 (1).pdf` 這種瀏覽器下載誤判成衝突)。
  ③ **雲端佔位檔**(Windows Files-On-Demand):size 是真的,檔卻不在本機。
     **讀它就是觸發下載**——天真的工具會把整個 OneDrive 拉下來。
     偵測到就標 CLOUD_ONLY 並且**不開檔**。

═══ 界線 ═══

  全唯讀:零搬移、零刪除、零 force、對端**一個位元都不寫**。
  只寫自己的 VIA_Reports/synchub/。references/intake/ 正本零觸碰(硬拒,有檢釘著)。
  零網路:本支不開 socket;api 端點只登記不撥號。同意閘不代設。
  批696 LL353 的坑要避開:**本支的基準是本支自己的產物**,所以第一次跑
  一律 FIRST_RUN,永不報 RED——一道閘不可以把自己的產物當成自己的前提。
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports"
OUT = REPORTS / "synchub"
LATEST = OUT / "SYNCHUB_latest.json"

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

# ===== [VIA:TAILPICK-BRIDGE:v0100] 尾版取用正典橋(正典 SUP_MDL751_VIATailPick)=====
# 綁定不是再定義一支 def:寫 def 的話能力庫裡這一家族還在,家族數不會掉(LL143)。
import importlib.util as _tp_ilu
from pathlib import Path as _tp_Path
_TP_MOD = None
_tp_p = _tp_Path(__file__).resolve()
while _tp_p.parent != _tp_p:
    _tp_hits = sorted((_tp_p / "supportive modules").glob("SUP_MDL751_VIATailPick_v*.py"))
    if _tp_hits:
        _tp_spec = _tp_ilu.spec_from_file_location("VIA_TAILPICK", _tp_hits[-1])
        _TP_MOD = _tp_ilu.module_from_spec(_tp_spec)
        _tp_spec.loader.exec_module(_TP_MOD)
        break
    _tp_p = _tp_p.parent
if _TP_MOD is None:      # 大聲壞掉:尾版取錯是無聲的錯
    raise RuntimeError("[FAIL] 尾版取用正典缺席:supportive modules/SUP_MDL751_VIATailPick_v*.py")
_newest = _TP_MOD.bind(order="rp")
# ===== [VIA:TAILPICK-BRIDGE:END] =====

INVENTORY_REL = "supportive modules/registry/VIA_Component_Inventory_SSOT_v0100.json"
ROSTER = HERE / "VIA_SyncHub_Endpoints_SSOT_v0100.json"

# 雲端根的辨識字(小寫比對路徑片段)
CLOUD_MARKS = (
    ("onedrive", ("onedrive",)),
    ("dropbox", ("dropbox",)),
    ("gdrive", ("google drive", "googledrive", "gdrive", "my drive")),
)

# Windows Files-On-Demand 佔位檔屬性
_FA_OFFLINE = 0x1000
_FA_RECALL_ON_OPEN = 0x40000
_FA_RECALL_ON_DATA = 0x400000

# 衝突副本樣式。**三種都要求同名正本在旁**才算數(見標頭 ②)。
_CONF_DROPBOX = re.compile(r"^(?P<stem>.+?) \((?:conflicted copy|.+?'s conflicted copy)[^)]*\)(?P<ext>\.[^.]*)?$", re.I)
_CONF_ONEDRIVE = re.compile(r"^(?P<stem>.+?)-(?P<host>[A-Z0-9][A-Z0-9-]{2,})(?P<ext>\.[^.]*)?$")
_CONF_GDRIVE = re.compile(r"^(?P<stem>.+?) \((?P<n>[1-9]\d?)\)(?P<ext>\.[^.]*)?$")

STATES = ("GREEN", "RED", "NODATA", "ABSENT", "GATED", "SKIP", "FIRST_RUN")


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _load(path: Path, name: str):
    """載一支姊妹模組(委派用)。缺席回 None + why,絕不拋。"""
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception as exc:
        return None, f"BROKEN {type(exc).__name__}:{str(exc)[:60]}"


def _copydoctor():
    p = _newest(HERE, "CGC_MDL144_CopyDoctor_v*.py")
    if not p:
        return None, "ABSENT CGC_MDL144_CopyDoctor_v*.py"
    return _load(Path(p), "VIA_COPYDOCTOR")


def _datahome():
    p = _newest(HERE, "CGC_MDL123_DataHome_v*.py")
    if not p:
        return None, "ABSENT CGC_MDL123_DataHome_v*.py"
    return _load(Path(p), "VIA_DATAHOME")


def _read_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def _write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


# ══════════════════════════════════════════════════════════════════════════════
# ① 端點
# ══════════════════════════════════════════════════════════════════════════════
def provider_of(path) -> str:
    """路徑落在哪一家雲端同步根底下。認不出回 ''。"""
    parts = [s.lower() for s in Path(path).parts]
    blob = " / ".join(parts)
    for name, marks in CLOUD_MARKS:
        if any(m in blob for m in marks):
            return name
    return ""


def is_via_tree(root) -> bool:
    r = Path(root)
    return (r / "supportive modules").is_dir() and (r / "functional modules").is_dir()


def roster() -> dict:
    """端點名冊 SSOT。缺席=用內建預設(不猜、不寫檔)。"""
    j = _read_json(ROSTER)
    # 判「是不是一份合法名冊」要看 endpoints **是不是 list**,不是看它空不空。
    # 批697 自審(Codex P2,對):我出的名冊本來就寫 "endpoints": [],
    # 而空清單是 falsy —— 於是我自己的載入器把我自己出的名冊丟掉、退回內建預設,
    # 操作員改 api_declared / policy 全部無效,CLI 還報「名冊不在」。
    if isinstance(j, dict) and isinstance(j.get("endpoints"), list):
        return j
    return {
        "schema": "VIA.SyncHub.Endpoints.v1",
        "ts": now_iso(),
        "policy": [
            "全唯讀:對端一個位元都不寫",
            "api 端點只登記不撥號(系統無憑證機制;AegisNexus 批345 不可動)",
            "不落 OneDrive(CGC_MDL059:83 鐵則)· 不複製(CGC_MDL123:26 三副本病)",
        ],
        "endpoints": [],       # 空=全部靠 CopyDoctor 掃出來
        "api_declared": [
            {"id": "onedrive_api", "provider": "onedrive", "why_gated": "無憑證機制(740 零 Authorization/Bearer/oauth)"},
            {"id": "gdrive_api", "provider": "gdrive", "why_gated": "無憑證機制(同上)"},
            {"id": "dropbox_api", "provider": "dropbox", "why_gated": "無憑證機制(同上)"},
        ],
        "_src": "內建預設(名冊檔不在;不自動落檔)",
    }


def endpoints() -> dict:
    """建端點清單。copy/cloudfolder 委派 CopyDoctor;datahome 委派 MDL123。"""
    eps, why = [], {}
    cd, cd_why = _copydoctor()
    roots = []
    if cd and hasattr(cd, "candidate_roots"):
        try:
            roots = [Path(r) for r in cd.candidate_roots()]
        except Exception as exc:
            why["copydoctor"] = f"BROKEN {type(exc).__name__}:{str(exc)[:60]}"
    else:
        why["copydoctor"] = cd_why or "ABSENT"
    seen = set()
    for r in roots:
        try:
            key = str(r.resolve())
        except Exception:
            key = str(r)
        if key in seen:
            continue
        seen.add(key)
        same = key == str(VIA.resolve())
        prov = provider_of(r)
        eps.append({
            "id": ("self" if same else Path(key).name or key),
            "kind": "self" if same else ("cloudfolder" if prov else "copy"),
            "provider": prov,
            "root": key,
            "present": is_via_tree(r),
        })
    # 名冊明列的端點:補 CopyDoctor 掃不到的那種版型(見標頭「繼承來的盲點」)
    for x in roster().get("endpoints", []) or []:
        rt = str(x.get("root") or "").strip()
        if not rt:
            continue
        try:
            key = str(Path(rt).resolve())
        except Exception:
            key = rt
        if key in seen:
            continue
        seen.add(key)
        prov = x.get("provider") or provider_of(rt)
        eps.append({"id": x.get("id") or Path(key).name or key,
                    "kind": x.get("kind") or ("cloudfolder" if prov else "copy"),
                    "provider": prov, "root": key, "present": is_via_tree(Path(rt)),
                    "why": "名冊明列(CopyDoctor 掃不到的版型走這條)"})
    dh, dh_why = _datahome()
    if dh and hasattr(dh, "resolve_home"):
        try:
            home, src = dh.resolve_home(VIA)
            eps.append({"id": "datahome", "kind": "datahome", "provider": provider_of(home),
                        "root": str(home), "present": Path(home).is_dir(), "why": f"來源 {src}"})
        except Exception as exc:
            why["datahome"] = f"BROKEN {type(exc).__name__}:{str(exc)[:60]}"
    else:
        why["datahome"] = dh_why or "ABSENT"
    for a in roster().get("api_declared", []):
        eps.append({"id": a["id"], "kind": "api", "provider": a.get("provider", ""),
                    "root": "", "present": False, "why": a.get("why_gated", "")})
    return {"endpoints": eps, "why": why,
            "self_root": str(VIA.resolve()),
            "n_present": sum(1 for e in eps if e.get("present"))}


# ══════════════════════════════════════════════════════════════════════════════
# ② 雲端資料夾的三個誠實檢
# ══════════════════════════════════════════════════════════════════════════════
def cloud_only(st) -> bool:
    """Windows Files-On-Demand 佔位檔。讀它=觸發下載,所以偵測到就不開檔。"""
    a = getattr(st, "st_file_attributes", 0)
    return bool(a & (_FA_OFFLINE | _FA_RECALL_ON_OPEN | _FA_RECALL_ON_DATA))


def conflict_copies(names) -> dict:
    """從一份檔名清單裡找 provider 衝突副本。

    **判準要嚴**:衝突副本一定跟正本並排,所以三種樣式都要求同名正本在旁。
    只認檔名樣式的話,`報告 (1).pdf` 這種瀏覽器下載會被誤判成 gdrive 衝突。
    """
    have = set(names)
    hits = {"dropbox": [], "onedrive": [], "gdrive_suspect": []}
    for n in names:
        for tag, rx in (("dropbox", _CONF_DROPBOX), ("onedrive", _CONF_ONEDRIVE), ("gdrive_suspect", _CONF_GDRIVE)):
            m = rx.match(n)
            if not m:
                continue
            orig = m.group("stem") + (m.group("ext") or "")
            if orig in have and orig != n:
                hits[tag].append({"file": n, "orig": orig})
                break
    return hits


def scan_cloud_health(root: Path, limit: int = 4000) -> dict:
    """雲端資料夾健康:衝突副本 + 佔位檔 + 最新 mtime。**零開檔**。

    批697 自審(Codex P1/P2,兩條都對):
      ② 掃到 limit 就停,而停之後**後面的目錄一次都沒看過**,函式卻照樣回 GREEN。
         真的 OneDrive/Dropbox 樹動輒超過四千件 —— 那個綠是假的保證。
         → 記 truncated,截斷就回 NODATA,並把「看過幾件」說出來。
      ③ gdrive 疑似件被算出來了,卻沒進總判(real 只收 dropbox+onedrive),
         於是 state 留在 GREEN、why 還是空的,而頁面只印 state 與 why ——
         偵測到的東西對操作員**完全隱形**。
         → 疑似件不得留在綠:升成 NODATA 並點名,但**不升 RED**(疑似就是疑似)。
    """
    out = {"state": "NODATA", "conflicts": {"dropbox": [], "onedrive": [], "gdrive_suspect": []},
           "cloud_only": 0, "files": 0, "newest_mtime": None, "why": "",
           "truncated": False, "limit": limit}
    if not root.is_dir():
        out["state"] = "ABSENT"
        out["why"] = "端點不在這台機器上(不是紅)"
        return out
    newest_m, n, co = 0.0, 0, 0
    try:
        for d, _dirs, files in os.walk(root):
            if any(m in d.replace("\\", "/") for m in ("/.git/", "/__pycache__/", "/VIA_Reports/")):
                continue
            hits = conflict_copies(files)
            for k in out["conflicts"]:
                out["conflicts"][k].extend(hits[k])
            for f in files:
                n += 1
                if n > limit:
                    break
                try:
                    st = os.stat(os.path.join(d, f))
                except Exception:
                    continue
                if cloud_only(st):
                    co += 1
                    continue            # **不開檔**:讀它就是觸發下載
                newest_m = max(newest_m, st.st_mtime)
            if n > limit:
                out["truncated"] = True
                break
    except Exception as exc:
        out["why"] = f"BROKEN {type(exc).__name__}:{str(exc)[:60]}"
        return out
    out["files"], out["cloud_only"] = n, co
    out["newest_mtime"] = datetime.fromtimestamp(newest_m).strftime("%Y-%m-%dT%H:%M:%S") if newest_m else None
    real = out["conflicts"]["dropbox"] + out["conflicts"]["onedrive"]
    sus = out["conflicts"]["gdrive_suspect"]
    if real:
        out["state"] = "RED"
        out["why"] = f"provider 已經放棄合併:衝突副本 {len(real)} 件(它自己生的,不是我判的)"
    elif out["truncated"]:
        # 綠只能發給「整棵看完」的掃描。看了前 N 件沒事,不是這棵樹沒事。
        out["state"] = "NODATA"
        out["why"] = (f"掃到上限 {limit} 件就停,後面的目錄一次都沒看過"
                      f"(已看 {n} 件,其中佔位 {co})——**乾淨的前綴不是整棵樹的保證**")
    elif sus:
        out["state"] = "NODATA"
        out["why"] = (f"Google Drive 疑似衝突 {len(sus)} 件(如 {sus[0]['file'][:40]}):"
                      "同名正本在旁,但 `(1)` 這種也可能只是瀏覽器下載——疑似不升紅,但也不准留在綠")
    else:
        out["state"] = "GREEN"
        if co:
            out["why"] = f"整棵看完 {n} 件無衝突;雲端佔位檔 {co} 件未下載(**沒讀它們**;在位≠同步好)"
        else:
            out["why"] = f"整棵看完 {n} 件:無衝突副本、無佔位檔"
    return out


# ══════════════════════════════════════════════════════════════════════════════
# ③ 功能面:元件冊對帳(**不猜方向**)
# ══════════════════════════════════════════════════════════════════════════════
def _inv_of(root: Path) -> tuple[dict, str]:
    p = Path(root) / INVENTORY_REL
    if not p.exists():
        return {}, f"元件冊不在({INVENTORY_REL})"
    j = _read_json(p)
    if not isinstance(j, dict) or "records" not in j:
        return {}, "元件冊讀不出來或格式不符——不猜"
    keys = {r.get("key") for r in j["records"] if r.get("state") == "ACTIVE" and r.get("key")}
    return {"counters": j.get("counters", {}), "keys": keys,
            "updated_at": j.get("updated_at", ""), "n": len(keys)}, ""


def function_plane(ep: dict, self_inv: dict) -> dict:
    out = {"plane": "功能面", "state": "NODATA", "why": ""}
    if ep["kind"] == "api":
        out.update(state="GATED", why=ep.get("why", "缺憑證機制"))
        return out
    if not ep.get("present"):
        out.update(state="ABSENT", why="端點不在這台機器上(不是紅)")
        return out
    if ep["kind"] == "datahome":
        out.update(state="SKIP", why="資料家沒有元件冊(規則上不比這一面)")
        return out
    inv, why = _inv_of(Path(ep["root"]))
    if not inv:
        out.update(state="NODATA", why=why)
        return out
    if not self_inv:
        out.update(state="NODATA", why="本端元件冊讀不出來——沒有基準就不判")
        return out
    only_here = self_inv["keys"] - inv["keys"]
    only_there = inv["keys"] - self_inv["keys"]
    out.update(n_here=self_inv["n"], n_there=inv["n"],
               only_here=len(only_here), only_there=len(only_there),
               both=len(self_inv["keys"] & inv["keys"]),
               sample_here=sorted(only_here)[:5], sample_there=sorted(only_there)[:5],
               updated_there=inv.get("updated_at", ""))
    if ep["kind"] == "self":
        out.update(state="GREEN", why="本端自己")
        return out
    if only_here and only_there:
        # 這正是批681/682/682B 互翻的形狀:兩邊各有獨有件,誰先 --apply 誰把對方標退役
        out.update(state="RED",
                   why=("兩端各有獨有件=**真分岔**;本支不裁(LL90)。"
                        f"警告:各跑一次 registry-sync --apply 會互翻——"
                        f"本端會把對端那 {len(only_there)} 件標 RETIRED,對端會把本端這 "
                        f"{len(only_here)} 件標 RETIRED(批681/682/682B 三次的同一個形狀)"),
                   flipflop_risk=True)
    elif only_here or only_there:
        out.update(state="RED", flipflop_risk=False,
                   why=("單邊多件(方向明確,可收斂):"
                        + (f"本端多 {len(only_here)}" if only_here else f"對端多 {len(only_there)}")))
    else:
        out.update(state="GREEN", flipflop_risk=False, why="兩端 ACTIVE key 集合完全一致")
    return out


# ══════════════════════════════════════════════════════════════════════════════
# ④ 資料面:宣告產物內容定址對帳
# ══════════════════════════════════════════════════════════════════════════════
def watch_list(deep: bool = False) -> list:
    """要對帳的宣告產物。DB 清單委派 MDL123.DB_PROBES(不自己再抄一份)。

    deep=False(預設):庫不做全檔 hash(動輒 GB)。**但也因此不准說「一致」**——見 data_plane。
    deep=True(`--deep`):庫照樣逐檔 hash,慢但判得準。
    """
    rows = []
    dh, _ = _datahome()
    probes = list(getattr(dh, "DB_PROBES", []) or []) if dh else []
    for rel in probes:
        rows.append({"cls": "庫", "rel": rel, "hash": bool(deep)})
    for rel in (INVENTORY_REL,
                "supportive modules/registry/VIA_SSOT_RegexDict_v0100.json",
                "supportive modules/registry/VIA_InputConsole_Spec_v0100.json",
                "supportive modules/ui_support/VIA_UI_MasterControl_v0100.html"):
        rows.append({"cls": "契約件", "rel": rel, "hash": True})
    return rows


def _stat_row(root: Path, rel: str, do_hash: bool) -> dict:
    p = Path(root) / rel
    try:
        st = p.stat()
    except FileNotFoundError:
        return {"state": "MISSING"}
    except Exception as exc:
        return {"state": "UNREADABLE", "why": f"{type(exc).__name__}:{str(exc)[:40]}"}
    if cloud_only(st):
        # **不開檔**:讀它就是觸發下載
        return {"state": "CLOUD_ONLY", "size": st.st_size,
                "mtime": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%dT%H:%M:%S"),
                "why": "雲端佔位檔(在位≠在本機;沒讀它)"}
    row = {"state": "OK", "size": st.st_size,
           "mtime": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%dT%H:%M:%S")}
    if do_hash and st.st_size <= (64 << 20):
        try:
            h = hashlib.sha256()
            with open(p, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            row["sha256"] = h.hexdigest()
        except Exception as exc:
            row["why"] = f"hash 失敗 {type(exc).__name__}"
    return row


def data_plane(ep: dict, self_rows: dict, deep: bool = False) -> dict:
    out = {"plane": "資料面", "state": "NODATA", "items": [], "why": ""}
    if ep["kind"] == "api":
        out.update(state="GATED", why=ep.get("why", "缺憑證機制"))
        return out
    if not ep.get("present") and ep["kind"] != "datahome":
        out.update(state="ABSENT", why="端點不在這台機器上(不是紅)")
        return out
    if ep["kind"] == "datahome":
        out.update(state="SKIP", why="資料家走 MDL123 的 link 模型,不在本支對帳範圍")
        return out
    root = Path(ep["root"])
    same, diff, only_here, only_there, cloud, bad, unver = 0, 0, 0, 0, 0, 0, 0
    for w in watch_list(deep):
        there = _stat_row(root, w["rel"], w["hash"])
        here = self_rows.get(w["rel"], {"state": "MISSING"})
        v = {"cls": w["cls"], "rel": w["rel"], "here": here.get("state"), "there": there.get("state")}
        if there["state"] == "CLOUD_ONLY" or here.get("state") == "CLOUD_ONLY":
            v["verdict"] = "CLOUD_ONLY"; cloud += 1
        elif there["state"] == "UNREADABLE" or here.get("state") == "UNREADABLE":
            v["verdict"] = "UNREADABLE"; bad += 1
        elif here.get("state") == "OK" and there["state"] == "MISSING":
            v["verdict"] = "ONLY_HERE"; only_here += 1
        elif here.get("state") == "MISSING" and there["state"] == "OK":
            v["verdict"] = "ONLY_THERE"; only_there += 1
        elif here.get("state") == "MISSING" and there["state"] == "MISSING":
            v["verdict"] = "BOTH_MISSING"
        elif w["hash"] and here.get("sha256") and there.get("sha256"):
            ok = here["sha256"] == there["sha256"]
            v["verdict"] = "SAME" if ok else "DIFF"
            v["sha_here"], v["sha_there"] = here["sha256"][:12], there["sha256"][:12]
            same, diff = same + int(ok), diff + int(not ok)
        else:
            # 批697 自審(Codex P1,**這條最重**):size 相等 ≠ 內容相同。
            #   DuckDB 改資料常常是就地改頁,**總長度一個位元組都不變**。
            #   舊寫法在這裡直接判 SAME → 整面 GREEN,
            #   於是這支樞紐會漏掉**它唯一存在理由**的那件事:一邊的庫舊了。
            #   改法:size 不同=DIFF(確定);size 相同=**UNVERIFIED**(沒量過就不准說一致),
            #   整面因此落到 NODATA 而不是 GREEN。要判準就 `--deep` 逐檔 hash。
            sz_h, sz_t = here.get("size"), there.get("size")
            v["size_here"], v["size_there"] = sz_h, sz_t
            if sz_h != sz_t:
                v["verdict"] = "DIFF"
                v["by"] = "size 不同(確定分岔)"
                diff += 1
            else:
                v["verdict"] = "UNVERIFIED"
                v["by"] = "size 相同但沒做內容比對——DuckDB 就地改頁不改長度,所以**不判一致**(要判用 --deep)"
                unver += 1
        out["items"].append(v)
    out.update(same=same, diff=diff, only_here=only_here, only_there=only_there,
               cloud_only=cloud, unreadable=bad, unverified=unver, deep=bool(deep))
    if ep["kind"] == "self":
        out.update(state="GREEN", why="本端自己")
    elif diff or only_here or only_there:
        out.update(state="RED",
                   why=(f"內容分岔:不同 {diff} · 只有本端 {only_here} · 只有對端 {only_there}"
                        + (f" · 雲端佔位 {cloud}" if cloud else "")
                        + (f" · 未驗 {unver}" if unver else "")
                        + "(批429-W4 的那個症狀就是這一欄)"))
    elif cloud or unver:
        bits = []
        if unver:
            bits.append(f"未驗 {unver} 件(庫 size 相同但沒比內容;`--deep` 才逐檔 hash)")
        if cloud:
            bits.append(f"雲端佔位 {cloud} 件未下載(**沒讀它們**)")
        out.update(state="NODATA", why=" · ".join(bits) + " —— 沒量過就不判一致,也不判分岔")
    else:
        out.update(state="GREEN",
                   why=("宣告產物逐件內容一致" + ("(--deep:庫也逐檔 hash 過)" if deep else "")))
    return out


# ══════════════════════════════════════════════════════════════════════════════
# ⑤ 對帳總成
# ══════════════════════════════════════════════════════════════════════════════
def reconcile(deep: bool = False) -> dict:
    eps = endpoints()
    self_inv, self_why = _inv_of(VIA)
    self_rows = {w["rel"]: _stat_row(VIA, w["rel"], w["hash"]) for w in watch_list(deep)}
    base = _read_json(LATEST)
    first_run = not isinstance(base, dict) or not base.get("endpoints")
    rows = []
    for ep in eps["endpoints"]:
        r = dict(ep)
        r["功能面"] = function_plane(ep, self_inv)
        r["資料面"] = data_plane(ep, self_rows, deep)
        r["雲端"] = (scan_cloud_health(Path(ep["root"])) if ep["kind"] == "cloudfolder"
                     else {"state": "SKIP", "why": "非雲端資料夾端點"})
        rows.append(r)
    lamps = [r[k]["state"] for r in rows for k in ("功能面", "資料面", "雲端")]
    verdict = ("RED" if "RED" in lamps else
               "NODATA" if "NODATA" in lamps else "GREEN")
    out = {"schema": "VIA.SyncHub.Reconcile.v1", "module": Path(__file__).name,
           "version": VERSION, "ts": now_iso(), "self_root": eps["self_root"],
           "self_inventory": {"n": self_inv.get("n", 0), "why": self_why} if not self_inv else
                             {"n": self_inv["n"], "updated_at": self_inv.get("updated_at", "")},
           "endpoints": rows, "why": eps["why"], "deep": bool(deep),
           "verdict": verdict,
           "first_run": first_run}
    if first_run:
        # 批696 LL353:本支的基準是本支自己的產物 —— 一道閘不可以把自己的產物當成自己的前提
        out["verdict"] = "FIRST_RUN" if verdict == "GREEN" else verdict
        out["first_run_note"] = ("第一次跑,沒有前次基準可比趨勢(本次仍是真量的當下態)。"
                                 "基準是本支自己的產物,所以第一次一律不因『沒有基準』報紅(LL353)")
    return out


def collect() -> dict:
    """VCGC SUBSYS_PORT 契約:與三支 *_SystemManager 同形,永不拋。"""
    try:
        r = reconcile()
    except Exception as exc:
        return {"state": f"BROKEN {type(exc).__name__}:{str(exc)[:60]}", "rc": 1,
                "src": Path(__file__).name, "ts": now_iso(), "lamps": {}, "links": []}
    present = [e for e in r["endpoints"] if e.get("present")]
    return {"state": r["verdict"], "rc": {"GREEN": 0, "FIRST_RUN": 0, "RED": 1, "NODATA": 2}.get(r["verdict"], 2),
            "src": Path(__file__).name, "ts": r["ts"], "mode": "對帳(唯讀;零搬移)",
            "lamps": {e["id"]: {"功能面": e["功能面"]["state"], "資料面": e["資料面"]["state"],
                                "雲端": e["雲端"]["state"]} for e in r["endpoints"]},
            "links": [e["root"] for e in present],
            "link_counts": {"端點": len(r["endpoints"]), "在位": len(present)},
            "bridge": {"copydoctor": "委派", "datahome": "委派", "tailpick": "綁定"},
            "why": r.get("why", {})}


# ══════════════════════════════════════════════════════════════════════════════
# ⑥ 列印 / 頁
# ══════════════════════════════════════════════════════════════════════════════
_MARK = {"GREEN": "🟢", "RED": "🔴", "NODATA": "⚪", "ABSENT": "⚫", "GATED": "🟣",
         "SKIP": "⬜", "FIRST_RUN": "🟡"}


def do_status(rest: list) -> int:
    r = reconcile(deep="--deep" in rest)
    print(f"=== VCGC 資料樞紐(對帳層)· MDL179 v{VERSION} · {r['verdict']} · {r['ts']} ===")
    print(f"  [界線] 全唯讀 · 對端零寫入 · 零搬移 · 零網路 —— 不落 OneDrive(MDL059:83)"
          f"· 不複製(MDL123:26)")
    print(f"  [本端] {r['self_root']} · 元件冊 ACTIVE {r['self_inventory'].get('n', 0)} 件"
          + (" · --deep(庫逐檔 hash)" if r.get("deep") else " · 淺比(庫不做全檔 hash;--deep 才逐檔)"))
    for e in r["endpoints"]:
        head = f"  {_MARK.get(e['功能面']['state'], '?')} {e['id']:<26} {e['kind']:<12}"
        if e.get("provider"):
            head += f" [{e['provider']}]"
        print(head)
        for plane in ("功能面", "資料面", "雲端"):
            p = e[plane]
            if p["state"] == "SKIP" and plane == "雲端":
                continue
            line = f"      {_MARK.get(p['state'], '?')} {plane} {p['state']}"
            if p.get("why"):
                line += f" · {p['why']}"
            print(line[:250])
    if r.get("first_run"):
        print(f"  [FIRST_RUN] {r['first_run_note']}")
    for k, v in (r.get("why") or {}).items():
        print(f"  [委派] {k}:{v}")
    _write_json(LATEST, r)
    _write_json(OUT / f"SYNCHUB_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", r)
    print(f"  [存證] {LATEST}")
    print("  下一步:發現分岔**不代搬**——本支只報。要動手是 via-copies 指路,或操作員自己決定正本。")
    return {"GREEN": 0, "FIRST_RUN": 0, "RED": 1, "NODATA": 2}.get(r["verdict"], 2)


def do_endpoints(rest: list) -> int:
    e = endpoints()
    print(f"=== 端點名冊 · MDL179 v{VERSION} · {len(e['endpoints'])} 個 · 在位 {e['n_present']} ===")
    for x in e["endpoints"]:
        print(f"  {x['kind']:<12} {x['id']:<26} 在位 {str(x['present']):<5} "
              f"{x.get('provider', '') or '-':<9} {x['root'][:70]}")
        if x.get("why"):
            print(f"      · {x['why']}")
    print(f"  名冊來源:{roster().get('_src', str(ROSTER))}")
    return 0


def page(publish: bool = False) -> str:
    r = reconcile()
    css = ("body{font-family:system-ui,'Noto Sans TC',sans-serif;margin:18px;background:#fbfcfb;color:#1a1f1a}"
           "h1{font-size:17px;margin:0 0 4px} .sub{color:#667;font-size:11.5px}"
           "table{border-collapse:collapse;width:100%;font-size:11.5px;margin-top:8px}"
           "th{text-align:left;font-weight:600;border-bottom:1px solid #dde;padding:4px 8px 4px 0}"
           "td{border-bottom:1px solid #eef0ee;padding:4px 8px 4px 0;vertical-align:top}"
           ".GREEN{color:#1a7f37;font-weight:700} .RED{color:#b42318;font-weight:700}"
           ".NODATA{color:#8a6d00} .ABSENT{color:#667} .GATED{color:#7c3aed} "
           ".SKIP{color:#99a} .FIRST_RUN{color:#8a6d00;font-weight:700}"
           ".card{background:#fff;border:1px solid #e6e9e6;border-radius:7px;padding:10px 12px;margin-top:10px}")
    rows = []
    for e in r["endpoints"]:
        for plane in ("功能面", "資料面", "雲端"):
            p = e[plane]
            if plane == "雲端" and p["state"] == "SKIP":
                continue
            rows.append(f"<tr><td>{e['id']}</td><td>{e['kind']}</td><td>{e.get('provider') or '—'}</td>"
                        f"<td>{plane}</td><td class='{p['state']}'>{p['state']}</td>"
                        f"<td>{(p.get('why') or '')[:220]}</td></tr>")
    html = (f"<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'>"
            f"<title>VCGC 資料樞紐(對帳層)</title><style>{css}</style></head><body>"
            f"<h1>VCGC 資料樞紐 · 對帳層 <span class='sub'>MDL179 v{VERSION} · "
            f"<span class='{r['verdict']}'>{r['verdict']}</span> · 產於 {r['ts']}</span></h1>"
            f"<div class='sub'>全唯讀 · 對端零寫入 · 零搬移 · 零網路 · 零 CDN。"
            f"不落 OneDrive(CGC_MDL059:83 鐵則)· 不複製(CGC_MDL123:26 三副本病)。"
            f"發現分岔只報不裁(LL90)。</div>"
            f"<div class='card'><h3>端點 × 面</h3><table>"
            f"<tr><th>端點</th><th>種類</th><th>雲端家</th><th>面</th><th>態</th><th>理由</th></tr>"
            f"{''.join(rows)}</table></div>"
            f"<div class='sub'>誠實態:GREEN 一致 · RED 真分岔 · NODATA 量不到 · "
            f"ABSENT 端點不在這台機器(不是紅)· GATED 缺機制 · SKIP 規則上不比 · "
            f"FIRST_RUN 第一次跑沒有基準(LL353:一道閘不可以把自己的產物當成自己的前提)</div>"
            f"</body></html>")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "VIA_UI_SyncHub_v0100.html").write_text(html, encoding="utf-8")
    if publish:
        (VIA / "supportive modules" / "ui_support" / "VIA_UI_SyncHub_v0100.html").write_text(html, encoding="utf-8")
    return html


# ══════════════════════════════════════════════════════════════════════════════
# ⑦ 自測(零網路 · 零寫入對端 · 正負控全合成)
# ══════════════════════════════════════════════════════════════════════════════
def selftest() -> int:
    import tempfile
    import traceback
    checks = []

    def chk(name, cond, note=""):
        checks.append((name, bool(cond)))
        print(f"  [{'OK ' if cond else 'FAIL'}] {name}" + (f" {note}" if note else ""))

    # ① 雲端家辨識:路徑片段比對,認得三家,認不出回空(不猜)
    try:
        got = {provider_of(r"C:\Users\x\OneDrive\VeritasIntelligenceAnalytics"),
               provider_of("/home/x/Dropbox/via"), provider_of("/home/x/Google Drive/via"),
               provider_of("/home/x/plain/via")}
        chk("① 雲端家辨識:onedrive/dropbox/gdrive 三家認得;認不出回空字串(不猜成某一家)",
            got == {"onedrive", "dropbox", "gdrive", ""}, f"({sorted(got)})")
    except Exception as exc:
        checks.append(("① 例外", False)); print("  [FAIL] ①", type(exc).__name__, exc)

    # ② 衝突副本:**一正一負**。正=有同名正本在旁才算;負=沒正本在旁一律不算
    try:
        pos = conflict_copies([
            "via.duckdb", "via (conflicted copy tony 2026-09-20).duckdb",      # dropbox 真衝突
            "reg.json", "reg-DESKTOP-A1B2C3.json",                             # onedrive 真衝突
            "報告.pdf", "報告 (1).pdf",                                          # gdrive 疑似
        ])
        neg = conflict_copies([
            "報告 (1).pdf",                       # 只有它自己,沒有「報告.pdf」→ 不是衝突,是下載
            "my-REPORT.json",                     # 沒有 my.json 在旁 → 不是衝突
            "x (conflicted copy a 2026).txt",     # 沒有 x.txt 在旁 → 不算
        ])
        ok = (len(pos["dropbox"]) == 1 and len(pos["onedrive"]) == 1 and len(pos["gdrive_suspect"]) == 1
              and not neg["dropbox"] and not neg["onedrive"] and not neg["gdrive_suspect"])
        chk("② 衝突副本判準要嚴(一正三負):三種樣式都**要求同名正本在旁**才算;"
            "沒正本在旁的 `報告 (1).pdf` 是瀏覽器下載不是衝突(只認檔名樣式會誤判)",
            ok, f"(正 db{len(pos['dropbox'])}/od{len(pos['onedrive'])}/gd{len(pos['gdrive_suspect'])} · "
                f"負 {sum(len(v) for v in neg.values())})")
    except Exception as exc:
        checks.append(("② 例外", False)); print("  [FAIL] ②", type(exc).__name__, exc)

    # ③ 雲端佔位檔:三個屬性位任一個中就算;沒有 st_file_attributes(非 Windows)一律 False
    try:
        class _St:
            def __init__(self, a=0):
                self.st_file_attributes = a
        class _NoAttr:
            pass
        ok = (cloud_only(_St(_FA_OFFLINE)) and cloud_only(_St(_FA_RECALL_ON_OPEN))
              and cloud_only(_St(_FA_RECALL_ON_DATA)) and not cloud_only(_St(0))
              and not cloud_only(_NoAttr()))
        chk("③ 雲端佔位檔:OFFLINE / RECALL_ON_OPEN / RECALL_ON_DATA 三位任一即是;"
            "位為 0 或非 Windows(無此屬性)一律 False(不把普通檔誤判成佔位檔)", ok)
    except Exception as exc:
        checks.append(("③ 例外", False)); print("  [FAIL] ③", type(exc).__name__, exc)

    # ④ 佔位檔**不開檔**:給一個假的 stat 讓 _stat_row 走 CLOUD_ONLY,證明它沒讀內容
    try:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "a").mkdir()
            f = root / "a" / "big.bin"; f.write_bytes(b"X" * 32)
            opened = []
            real_open = __builtins__["open"] if isinstance(__builtins__, dict) else __builtins__.open
            import builtins as _b
            def _spy(p, *a, **k):
                opened.append(str(p)); return real_open(p, *a, **k)
            _sv_stat = os.stat
            def _fake_stat(p, *a, **k):
                st = _sv_stat(p, *a, **k)
                class _W:
                    st_size = st.st_size; st_mtime = st.st_mtime
                    st_file_attributes = _FA_RECALL_ON_DATA
                return _W()
            os.stat = _fake_stat; _b.open = _spy
            try:
                row = _stat_row(root, "a/big.bin", True)
            finally:
                os.stat = _sv_stat; _b.open = real_open
        chk("④ 佔位檔**不開檔**(讀它就是觸發下載,天真的工具會把整個 OneDrive 拉下來):"
            "state=CLOUD_ONLY、無 sha256、而且全程零次 open()",
            row["state"] == "CLOUD_ONLY" and "sha256" not in row and not opened,
            f"(state={row['state']} · open 次數 {len(opened)})")
    except Exception as exc:
        checks.append(("④ 例外", False)); print("  [FAIL] ④", type(exc).__name__, exc); traceback.print_exc()

    # ⑤ 功能面**不猜方向**:兩端各有獨有件=RED 且標 flipflop_risk(批681/682/682B 的形狀)
    try:
        sf = {"counters": {}, "keys": {"a", "b", "c"}, "n": 3, "updated_at": ""}
        with tempfile.TemporaryDirectory() as td:
            other = Path(td) / "other"
            (other / "supportive modules" / "registry").mkdir(parents=True)
            (other / "functional modules").mkdir()
            inv = {"schema": "VIA.ComponentInventory.v1", "counters": {},
                   "records": [{"key": k, "state": "ACTIVE"} for k in ("b", "c", "z")],
                   "updated_at": "2026-09-22T00:00:00"}
            (other / INVENTORY_REL).write_text(json.dumps(inv, ensure_ascii=False), encoding="utf-8")
            ep = {"id": "t", "kind": "copy", "root": str(other), "present": True}
            two = function_plane(ep, sf)
            inv["records"] = [{"key": k, "state": "ACTIVE"} for k in ("a", "b", "c")]
            (other / INVENTORY_REL).write_text(json.dumps(inv, ensure_ascii=False), encoding="utf-8")
            same = function_plane(ep, sf)
            inv["records"] = [{"key": k, "state": "ACTIVE"} for k in ("a", "b", "c", "z")]
            (other / INVENTORY_REL).write_text(json.dumps(inv, ensure_ascii=False), encoding="utf-8")
            one = function_plane(ep, sf)
        ok = (two["state"] == "RED" and two.get("flipflop_risk") is True
              and two["only_here"] == 1 and two["only_there"] == 1
              and same["state"] == "GREEN" and same.get("flipflop_risk") is False
              and one["state"] == "RED" and one.get("flipflop_risk") is False)
        chk("⑤ 功能面不猜方向:兩端各有獨有件=RED+flipflop_risk(各跑一次 registry-sync --apply "
            "就互翻——批681/682/682B 三次的同一個形狀);單邊多件=RED 但方向明確可收斂;"
            "集合相同=GREEN", ok,
            f"(雙向 {two['state']}/{two.get('flipflop_risk')} · 單向 {one['state']}/{one.get('flipflop_risk')}"
            f" · 相同 {same['state']})")
    except Exception as exc:
        checks.append(("⑤ 例外", False)); print("  [FAIL] ⑤", type(exc).__name__, exc); traceback.print_exc()

    # ⑥ ABSENT 不是紅:端點不在這台機器上要走 ABSENT,而且總判不得因此變 RED
    try:
        gone = {"id": "g", "kind": "cloudfolder", "root": "/definitely/not/here", "present": False}
        f6 = function_plane(gone, {"keys": {"a"}, "n": 1})
        d6 = data_plane(gone, {})
        c6 = scan_cloud_health(Path("/definitely/not/here"))
        chk("⑥ ABSENT 不是紅:端點不在這台機器上(容器本來就看不到工作站的 OneDrive)→ "
            "三面全 ABSENT,不報 RED", f6["state"] == "ABSENT" and d6["state"] == "ABSENT"
            and c6["state"] == "ABSENT", f"({f6['state']}/{d6['state']}/{c6['state']})")
    except Exception as exc:
        checks.append(("⑥ 例外", False)); print("  [FAIL] ⑥", type(exc).__name__, exc)

    # ⑦ api 端點一律 GATED,而且理由要說得出是「缺機制」不是「壞了」
    try:
        a = {"id": "onedrive_api", "kind": "api", "root": "", "present": False, "why": "無憑證機制"}
        f7, d7 = function_plane(a, {"keys": set(), "n": 0}), data_plane(a, {})
        chk("⑦ api 端點只登記不撥號:一律 GATED(不是 RED 也不是 ABSENT)——"
            "系統裡沒有憑證機制,而 AegisNexus 是批345 不可動律",
            f7["state"] == "GATED" and d7["state"] == "GATED" and "憑證" in f7["why"])
    except Exception as exc:
        checks.append(("⑦ 例外", False)); print("  [FAIL] ⑦", type(exc).__name__, exc)

    # ⑧ 零搬移零刪除 —— 界線寫在程式碼裡,不是寫在註解裡。
    #   LL133 自指:第一版這一檢把禁用字**直接寫成字面值**,於是它在原始碼裡找到了自己,
    #   一跑就紅(批695 同意閘那把尺踩過同一個坑)。而且它**咬了兩層**:先是 needle 清單,
    #   修掉之後換成檢自己的說明文字裡那個字又被找到。修法是讓尺看不到自己:
    #   needle 一律**執行期拼**出來,字面值永不出現在檔裡。規則一個字都沒放寬。
    try:
        src = Path(__file__).read_text(encoding="utf-8")
        body = src.split('"""', 2)[-1]          # 排掉標頭 docstring(它會講到這些字)
        banned = ["shutil." + "copy", "shutil." + "move", "rm" + "tree",
                  "os." + "remove", "os." + "unlink", "Path." + "unlink", "os." + "rename("]
        bad = [w for w in banned if w in body]
        # 唯一的寫入原件 os.replace 只准出現在 _write_json 裡(寫我自己的存證,不是對端)
        atom = "os." + "replace("
        seg = body.split("def _write_json")[1].split("\ndef ")[0] if "def _write_json" in body else ""
        n_all, n_seg = body.count(atom), seg.count(atom)
        chk("⑧ 零搬移零刪除(界線寫在程式碼裡):七個破壞性原件(複製/搬移/整夾刪/刪檔/改名)全數不得出現;"
            "唯一的寫入原件 os.replace **只准在 _write_json 裡**(寫我自己的存證,對端一個位元都不寫)",
            not bad and n_all >= 1 and n_all == n_seg,
            f"(禁用字命中 {bad or '無'} · os.replace 全檔 {n_all} 次/都在 _write_json {n_seg} 次)")
    except Exception as exc:
        checks.append(("⑧ 例外", False)); print("  [FAIL] ⑧", type(exc).__name__, exc)

    # ⑨ 零網路:不得 import 任何 http 客戶端(端點是檔案系統,不是網路)
    try:
        src = Path(__file__).read_text(encoding="utf-8")
        body = src.split('"""', 2)[-1]
        nets = [k for k in ("requests", "httpx", "aiohttp", "urllib.request", "socket")
                if ("import " + k) in body]
        chk("⑨ 零網路:雲端資料夾是**檔案系統端點**,同步是雲端用戶端在做,我方零 socket",
            not nets, f"(命中 {nets or '無'})")
    except Exception as exc:
        checks.append(("⑨ 例外", False)); print("  [FAIL] ⑨", type(exc).__name__, exc)

    # ⑩ 正本零觸碰:watch 清單不得含 references/intake
    try:
        rels = [w["rel"] for w in watch_list()]
        chk("⑩ 正本零觸碰:對帳清單不得含 references/intake(正本只讀不比、更不寫)",
            not any("references/intake" in r for r in rels), f"(清單 {len(rels)} 件)")
    except Exception as exc:
        checks.append(("⑩ 例外", False)); print("  [FAIL] ⑩", type(exc).__name__, exc)

    # ⑪ LL353:第一次跑沒有基準,不得因此報紅(本支的基準是本支自己的產物)
    try:
        sv = globals()["LATEST"]
        with tempfile.TemporaryDirectory() as td:
            globals()["LATEST"] = Path(td) / "nope.json"
            try:
                r = reconcile()
            finally:
                globals()["LATEST"] = sv
        ok = r["first_run"] is True and r["verdict"] != "RED" or (r["first_run"] and r["verdict"] == "RED"
             and any(e["功能面"]["state"] == "RED" or e["資料面"]["state"] == "RED" for e in r["endpoints"]))
        chk("⑪ LL353 一道閘不可以把自己的產物當成自己的前提:基準檔不在 → first_run=True,"
            "**不因為沒有基準而報紅**(真的有分岔才紅,那是另一回事)",
            r["first_run"] is True and ok, f"(first_run={r['first_run']} · 判 {r['verdict']})")
    except Exception as exc:
        checks.append(("⑪ 例外", False)); print("  [FAIL] ⑪", type(exc).__name__, exc); traceback.print_exc()

    # ⑫ collect() 契約:永不拋,狀態字在誠實態內
    try:
        c = collect()
        chk("⑫ VCGC SUBSYS_PORT 契約:collect() 永不拋、帶 state/rc/src/ts/lamps/links,"
            "state 在誠實態集合內(與三支 *_SystemManager 同形)",
            isinstance(c, dict) and all(k in c for k in ("state", "rc", "src", "ts", "lamps", "links"))
            and (c["state"] in STATES or c["state"].startswith("BROKEN")),
            f"(state={c.get('state')} rc={c.get('rc')} 端點 {c.get('link_counts', {})})")
    except Exception as exc:
        checks.append(("⑫ 例外", False)); print("  [FAIL] ⑫", type(exc).__name__, exc)

    # ⑬ 頁:零 CDN 零外鏈
    try:
        h = page(publish=False)
        chk("⑬ 頁零 CDN 零外鏈(house 律)", "http://" not in h and "https://" not in h,
            f"({len(h)} 字)")
    except Exception as exc:
        checks.append(("⑬ 例外", False)); print("  [FAIL] ⑬", type(exc).__name__, exc)

    # ⑭ 委派不自寫:端點解析要走 CopyDoctor、資料家要走 MDL123、尾版要走 TailPick(LL341/LL143)
    try:
        src = Path(__file__).read_text(encoding="utf-8")
        body = src.split('"""', 2)[-1]
        ok = ("CGC_MDL144_CopyDoctor_v*.py" in body and "CGC_MDL123_DataHome_v*.py" in body
              and "SUP_MDL751_VIATailPick_v*.py" in body and "\ndef newest(" not in body)
        chk("⑭ 委派不自寫(LL341/LL143):副本解析→CGC_MDL144 · 資料家→CGC_MDL123 · "
            "尾版→SUP_MDL751 綁定;本支不自己再定義一支 newest()", ok)
    except Exception as exc:
        checks.append(("⑭ 例外", False)); print("  [FAIL] ⑭", type(exc).__name__, exc)

    # ⑮ 名冊明路:CopyDoctor 掃不到的版型,名冊逐筆指定要吃得到(補繼承來的盲點)
    try:
        import tempfile as _tf15
        with _tf15.TemporaryDirectory() as td:
            od = Path(td) / "OneDrive" / "VeritasIntelligenceAnalytics"   # 沒有 movies-dataset 父夾
            (od / "supportive modules").mkdir(parents=True)
            (od / "functional modules").mkdir()
            sv = globals()["roster"]
            globals()["roster"] = lambda: {"endpoints": [{"id": "od_manual", "root": str(od)}],
                                           "api_declared": [], "_src": "自測合成"}
            try:
                e = endpoints()
            finally:
                globals()["roster"] = sv
        row = next((x for x in e["endpoints"] if x["id"] == "od_manual"), None)
        chk("⑮ 名冊明路(補繼承來的盲點):CopyDoctor 只認『父夾叫 movies-dataset* 且有 Register 冊』,"
            "所以直接攤在 OneDrive\\VeritasIntelligenceAnalytics 的樹它掃不到;"
            "名冊 endpoints[] 逐筆指定要吃得到,而且雲端家要從路徑認出來",
            row is not None and row["present"] is True and row["provider"] == "onedrive"
            and row["kind"] == "cloudfolder",
            f"({row and (row['kind'], row['provider'], row['present'])})")
    except Exception as exc:
        checks.append(("⑮ 例外", False)); print("  [FAIL] ⑮", type(exc).__name__, exc)

    # ⑯ 登錄面(LL199):加速器橋在位 + 自測門在位。批697 實錄:第一版漏了加速器橋,
    #   全樹雙橋稽核當場把活件分母從 841/842 照成「加速殘 1」——那一件就是我。
    #   第四面(短令 via-hub)在 .ps1 裡,L70 要逐次許可,所以本支做不到,誠實列為缺口。
    try:
        src = Path(__file__).read_text(encoding="utf-8")
        chk("⑯ 登錄面(LL199):加速器橋在位 · 自測門在位 · 格子站另在 CGC_MDL064 開;"
            "第四面短令在 .ps1(L70 逐次許可)本支做不到——誠實列為缺口,不假裝四面齊",
            "[VIA:ACCEL-BRIDGE:v0100]" in src and "--selftest" in src)
    except Exception as exc:
        checks.append(("⑯ 例外", False)); print("  [FAIL] ⑯", type(exc).__name__, exc)

    # ── 批697 自審修(Codex 四條,逐條加檢;一正一負)────────────────────────
    # ⑰ size 相等不准判一致(P1,最重):DuckDB 就地改頁不改長度
    try:
        import tempfile as _tf17
        with _tf17.TemporaryDirectory() as td:
            a, b = Path(td) / "A", Path(td) / "B"
            for r in (a, b):
                (r / "supportive modules").mkdir(parents=True); (r / "functional modules").mkdir()
            rel = "db.duckdb"
            (a / rel).write_bytes(b"X" * 64)
            (b / rel).write_bytes(b"Y" * 64)          # 同長度、不同內容
            sv = globals()["watch_list"]
            globals()["watch_list"] = lambda deep=False: [{"cls": "庫", "rel": rel, "hash": bool(deep)}]
            try:
                hs = {rel: _stat_row(a, rel, False)}
                shallow = data_plane({"id": "t", "kind": "copy", "root": str(b), "present": True}, hs, False)
                hd = {rel: _stat_row(a, rel, True)}
                deep = data_plane({"id": "t", "kind": "copy", "root": str(b), "present": True}, hd, True)
            finally:
                globals()["watch_list"] = sv
        ok = (shallow["items"][0]["verdict"] == "UNVERIFIED" and shallow["state"] == "NODATA"
              and shallow.get("unverified") == 1 and shallow.get("same", 0) == 0
              and deep["items"][0]["verdict"] == "DIFF" and deep["state"] == "RED")
        chk("⑰ size 相等**不准**判一致(Codex P1;DuckDB 就地改頁不改總長度):同長不同內容 → "
            "淺比 UNVERIFIED + 整面 NODATA(絕不 SAME/GREEN);--deep 逐檔 hash → DIFF + RED。"
            "漏掉這條,這支樞紐就會漏掉它唯一存在理由的那件事",
            ok, f"(淺 {shallow['items'][0]['verdict']}/{shallow['state']} · "
                f"深 {deep['items'][0]['verdict']}/{deep['state']})")
    except Exception as exc:
        checks.append(("⑰ 例外", False)); print("  [FAIL] ⑰", type(exc).__name__, exc); traceback.print_exc()

    # ⑱ 掃描截斷不准發綠(P1)+ ⑲ gdrive 疑似不准留在綠(P2)
    try:
        import tempfile as _tf18
        with _tf18.TemporaryDirectory() as td:
            big = Path(td) / "big"; big.mkdir()
            for i in range(12):
                (big / f"f{i}.txt").write_text("x", encoding="utf-8")
            trunc = scan_cloud_health(big, limit=5)
            full = scan_cloud_health(big, limit=999)
            gd = Path(td) / "gd"; gd.mkdir()
            (gd / "報告.pdf").write_text("a", encoding="utf-8")
            (gd / "報告 (1).pdf").write_text("b", encoding="utf-8")
            sus = scan_cloud_health(gd, limit=999)
            od = Path(td) / "od"; od.mkdir()
            (od / "reg.json").write_text("a", encoding="utf-8")
            (od / "reg-DESKTOP-A1B2C3.json").write_text("b", encoding="utf-8")
            real = scan_cloud_health(od, limit=999)
        chk("⑱ 掃到上限就停 → **不准發綠**(Codex P1;真的 OneDrive 樹動輒破四千件,"
            "乾淨的前綴不是整棵樹的保證):截斷 NODATA 且說得出看了幾件;整棵看完才 GREEN",
            trunc["state"] == "NODATA" and trunc["truncated"] is True and "上限" in trunc["why"]
            and full["state"] == "GREEN" and full["truncated"] is False,
            f"(截斷 {trunc['state']}/truncated={trunc['truncated']} · 完整 {full['state']})")
        chk("⑲ gdrive 疑似件**不准留在綠**(Codex P2;算出來卻沒進總判=對操作員完全隱形):"
            "疑似 → NODATA 並點名;確定衝突(dropbox/onedrive)→ RED。疑似不升紅,但也不留綠",
            sus["state"] == "NODATA" and "疑似" in sus["why"] and len(sus["conflicts"]["gdrive_suspect"]) == 1
            and real["state"] == "RED",
            f"(疑似 {sus['state']} · 確定 {real['state']})")
    except Exception as exc:
        checks.append(("⑱⑲ 例外", False)); print("  [FAIL] ⑱⑲", type(exc).__name__, exc); traceback.print_exc()

    # ⑳ 名冊 endpoints 是空清單也要收(P2;我自己出的名冊就寫空清單)
    try:
        import tempfile as _tf20
        with _tf20.TemporaryDirectory() as td:
            p = Path(td) / "r.json"
            p.write_text(json.dumps({"schema": "VIA.SyncHub.Endpoints.v1", "endpoints": [],
                                     "api_declared": [{"id": "只有這一筆", "provider": "x",
                                                       "why_gated": "自測"}]},
                                    ensure_ascii=False), encoding="utf-8")
            sv = globals()["ROSTER"]
            globals()["ROSTER"] = p
            try:
                got = roster()
            finally:
                globals()["ROSTER"] = sv
            bad = Path(td) / "bad.json"; bad.write_text("{}", encoding="utf-8")
            globals()["ROSTER"] = bad
            try:
                fallback = roster()
            finally:
                globals()["ROSTER"] = sv
        chk("⑳ 名冊 endpoints 是**空清單也要收**(Codex P2):判準看它是不是 list,不是看它空不空——"
            "舊寫法把我自己出的那份名冊(endpoints: [])當成不存在,操作員改 api_declared/policy 全部無效;"
            "真的缺鍵才退回內建預設",
            got.get("api_declared", [{}])[0].get("id") == "只有這一筆"
            and fallback.get("_src", "").startswith("內建預設"),
            f"(讀到名冊 api_declared {len(got.get('api_declared', []))} 筆 · 缺鍵時退預設 "
            f"{fallback.get('_src', '')[:12]})")
    except Exception as exc:
        checks.append(("⑳ 例外", False)); print("  [FAIL] ⑳", type(exc).__name__, exc); traceback.print_exc()

    n_ok = sum(1 for _, c in checks if c)
    print(f"  [計] {n_ok}/{len(checks)} 檢 OK")
    return 0 if n_ok == len(checks) else 1


# ══════════════════════════════════════════════════════════════════════════════
# ⑧ CLI
# ══════════════════════════════════════════════════════════════════════════════
KNOWN_FLAGS = {"--selftest", "--publish", "--json", "--deep", "--help", "-h"}
VERBS = {"status", "endpoints", "page", "diff"}


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print(f"=== CGC_MDL179 VcgcSyncHub v{VERSION} 自測(零網路 · 零寫入對端)===")
        return selftest()
    if "-h" in args or "--help" in args:
        print(__doc__)
        return 0
    bad = [a for a in args if a.startswith("-") and a not in KNOWN_FLAGS]
    if bad:
        print(f"  [停] 未知旗標 {bad}(fail-closed:不靜默照跑)")
        return 2
    verb = next((a for a in args if not a.startswith("-")), "status")
    rest = [a for a in args if a != verb]
    if verb not in VERBS:
        print(f"  [停] 未知動詞 {verb!r};可用:{sorted(VERBS)}")
        return 2
    if verb == "endpoints":
        return do_endpoints(rest)
    if verb == "page":
        page(publish="--publish" in rest)
        print(f"  [頁] {OUT / 'VIA_UI_SyncHub_v0100.html'}"
              + ("  + ui_support(已發佈)" if "--publish" in rest else "(未發佈;--publish 才進 ui_support)"))
        return 0
    if verb == "diff":
        r = reconcile(deep="--deep" in rest)
        print(json.dumps(r, ensure_ascii=False, indent=1)[:4000])
        return {"GREEN": 0, "FIRST_RUN": 0, "RED": 1, "NODATA": 2}.get(r["verdict"], 2)
    return do_status(rest)


if __name__ == "__main__":
    sys.exit(main())
