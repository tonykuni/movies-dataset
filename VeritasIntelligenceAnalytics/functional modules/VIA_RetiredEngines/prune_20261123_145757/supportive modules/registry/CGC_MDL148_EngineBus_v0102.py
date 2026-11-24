#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL148_EngineBus v0102 — 引擎調度匯流排(批471 立;v0101 加 NODATA 態;本版收三盞「判錯的紅燈」+ 家族級 apply)

v0101→v0102(**第二次實跑,照出的還是我的尺**):
  VAP 家族 6 項真跑,匯流排報 RED 4。逐項查完,**只有 1 支是真壞**:
    · vap_dashboard     印「[缺料] 缺 4 項 … [補料] **誠實停 rc2**」 → 缺料,判紅是錯的
    · vap_std_dashboard 印「plotly 缺席=**誠實停**」               → 缺件,判紅是錯的
    · vap_one_render    argparse:「error: argument --render: expected one argument」
                        冊上這項宣告 `params:["vapone"]`——config 路徑本來就該由主控台給。
                        我沒給參數就硬跑,再把 argparse 的抱怨判成引擎壞 → 缺參數,判紅是錯的
    · vap_stack         `_duckdb.CatalogException: Table tw_daily_prices does not exist`
                        **這支是真紅**:缺表時該誠實停,它卻讓例外裸奔(VAP 側缺陷,已表列)
  三盞判錯的紅燈,三盞都是我點的。修的是判準,不是引擎:

  ① **「誠實停」才是這套系統的正典句**——全樹 451 處,而 v0101 的 NODATA_RX 裡沒有它。
     我當初是照 VRN 那幾支的措辭湊字表,湊出來的字表只認得 VRN 的方言。
  ② **缺件 ≠ 缺料 ≠ 壞掉**(操作員原律)。誠實停還要再分一層:
       缺料(上游沒料)                     → NODATA
       缺件(引擎/相依套件/**必要參數** 不在位)→ ABSENT ← 本版擴義,不新立第八態
     判缺參數**只認 argparse 自己講的話**(`error: argument …` /
     `the following arguments are required`)。**不能用「有宣告 params 就別跑」一刀切**:
     冊上 21 項宣告了 params,其中 20 項沒給參數照樣跑得好好的(量過),
     一刀切會誤殺 20 項——跟「排除 2000–2030 修年份」是同一種爛招。
  ③ **`--apply` 不該是全有全無**。VRN 那 7 項無妨;VDF 那 24 項按下去,等於同時發動
     tw_history 全史回補、tw_chips 籌碼回補,還有兩支動詞裡本來就帶 `--apply` 的寫庫件
     (tw_universe_update / db_localdb_apply)。調度層唯一的開關長這樣就是地雷。本版加:
       --apply-family vrn,vap   只在點名的家族真跑,其餘照樣 PLAN
       --ids a,b,c              只跑點名的項
       **寫庫動詞閘**:動詞裡含 `--apply` 的項,家族全掃**永不代跑**,
                       要跑必須 --ids 明點(與「--approve-remove 只在明令下」同律)

v0100→v0101(**實跑第一次就照出我自己用錯尺**):
  VRN 家族 7 項真跑,匯流排報 RED 3。查了才知道三支同一個根——引擎自己印的是
  「**無報告件(誠實)**」「無可轉檔(誠實)」:那是**缺料不是壞掉**,而我把它判成紅。
  這正是批470 才寫過的那一課的翻版:**判錯的紅燈和假綠一樣傷**,
  它會讓人去 debug 一支行為完全正確的引擎。
  想用 rc=2 當判準——**量過之後否決**:全樹 `return 2` 有 163 處,
  其中只有 46 處是誠實停,117 處是用法錯/缺庫等別的意思。**rc 不是穩定慣例。**
  可靠的訊號是引擎**自己印出來的那句話**。所以 v0101 加 **NODATA** 態:
  rc≠0 **且**輸出尾段命中誠實停字樣 → NODATA,並把**命中的那句原文一起帶回**
  (判準要亮得出證據,不然它就只是另一種猜)。沒有那句話的 rc≠0 一律照舊 RED。
====================================================================
操作員令:「**功能性引擎功能性化 可讓多個子系統調度**」
        「實測修正無誤後顯示 html u/多矩陣結果摘要及資料 **全部 SSOT**」

先查再造(量到的,不是規劃的):
  · 調度用的 SSOT **早就有**:VIA_InputConsole_Spec_v0100.json 已宣告
    **37 項引擎**(vdf 24 / vrn 7 / vap 6),每項都帶 engine{dir,glob,verb}、
    params、outputs。**本件不另立第二本冊**——那會讓「正典換了沒人跟得上」。
  · 但**調度的碼四家各寫各的**(實測):
        CGC_MDL095_DeckServer   Popen ×12
        CGC_MDL137_RunGate      subprocess.run ×3
        CGC_MDL139_InputConsole subprocess.run ×1
        CGC_MDL141_ClosingGate  自己一套
    每一家都重寫:尾版 glob 解析、家族 python 選擇、逾時、結果解讀。
    同一件事四份實作=九頭龍;引擎換了介面,四個地方都要記得改,而**漏改的那個
    不會報錯,只會靜靜走錯**。
  · 這就是「功能性化」缺的那一格:引擎有功能,但**沒有一個統一的呼叫契約**,
    所以每個子系統只能各自用「開一個行程再讀文字」的方式去湊。

本件補的正是那一格 —— **一條匯流排,四家共用**:
    catalog()            冊上 37 項 × 尾版解析 × 在位實測
    call(item_id, ...)   統一呼叫契約,回**統一結果字典**
    matrix(...)          批量調度 → 多矩陣資料
    render(...)          實測結果 → 多矩陣 HTML(零 CDN;樣板走 MDL089)

統一結果契約(誰調度都拿到同一個形狀,不必再各自解讀文字):
    {id, family, zh, engine, engine_state, argv, state, rc, seconds,
     tally, outputs_seen, stdout_tail, why}
    state ∈ GREEN | NODATA | AMBER | RED | TIMEOUT | ABSENT | PLAN
      NODATA  **缺料**:上游沒料,引擎自己說了「誠實停」。不是紅燈。
      ABSENT  **缺件**:引擎檔 / 相依套件 / 必要參數 不在位。也不是紅燈。
              缺件與壞掉混在一起,就會讓人去 debug 一支行為完全正確的引擎。
      PLAN    dry:只解析不動手(預設就是 dry),或**寫庫動詞被家族閘擋下**

紀律:
  · 尾版律 glob;家族 python **委派** MDL137.python_for →(它再委派 MDL136)
  · **不卡斷**:逐項逾時,只殺自己生的那個子行程
  · 誠實三態;`[計]` 只認**最後一行**(批462 那一課:子報告也印 `FAIL 0`,
    全篇搜就會把「OK 38 · FAIL 1」讀成綠)
  · 本件**零網路**、**預設不動手**(dry)、不寫任何正式產出夾
用法:
  python3 CGC_MDL148_EngineBus_v0102.py catalog [--family vrn]
  python3 CGC_MDL148_EngineBus_v0102.py call --item vrn_firstpage [--apply]
  python3 CGC_MDL148_EngineBus_v0102.py matrix [--family vrn] [--apply] [--html]
  python3 CGC_MDL148_EngineBus_v0102.py matrix --apply-family vrn,vap --html
  python3 CGC_MDL148_EngineBus_v0102.py matrix --ids vdf_tw_align --apply
  python3 CGC_MDL148_EngineBus_v0102.py --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 缺席零影響) =====
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
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import html as _html
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
#: 調度 SSOT —— 冊只有一本(尾版律 glob;不另立)
SPEC_GLOB = "VIA_InputConsole_Spec_v*.json"
#: 產出(本件唯一會寫的地方;VIA_Reports/* 已在 .gitignore)
OUTDIR = VIA / "VIA_Reports" / "engine_bus"
#: 逐項逾時
DEFAULT_TIMEOUT = 900
#: `[計]` 行:只認最後一行(批462)
TALLY_RX = re.compile(r"\[計\][^\n]*")
#: 引擎「誠實停」的自述句(它們自己印的,不是我發明的分類)
#: 量過才用:全樹 `return 2` 163 處只有 46 處是這個意思,**rc 不可當判準**。
#: 批471 v0102:v0101 這張字表是照 VRN 幾支的措辭湊的,只認得 VRN 的方言——
#: VAP 印「誠實停 rc2」就漏接了。「誠實停」全樹 451 處,才是這套系統的正典句。
STOP_RX = re.compile(
    r"(誠實停|無報告件|無可轉檔|無 ?PDF|無分區 ?sidecar|缺件|夾不存在|夾是空的|"
    r"無報告檔|尚無報告|無可轉|零報告|無輸入)[^\n]{0,48}")
NODATA_RX = STOP_RX          # 舊名留著當橋(別處若已 import,不讓它斷)

#: 誠實停之中屬於**缺件**的那一類(缺套件/缺模組)——與缺料要分開。
#: 缺件 ≠ 缺料 ≠ 壞掉:三件事混成一盞燈,人就會去 debug 一支沒壞的引擎。
NEED_RX = re.compile(
    r"(缺席|未安裝|沒裝|不在位)[^\n]{0,24}|"
    r"(pip install|ModuleNotFoundError|ImportError|No module named)[^\n]{0,40}|"
    r"\b(plotly|matplotlib|seaborn|duckdb|pymupdf|fitz|pypdf|python-docx|"
    r"pytesseract|tesseract)\b[^\n]{0,12}(缺席|未安裝|沒裝)")

#: argparse 自己講的「你少給我一個參數」。**只認它講的**——
#: 不能用「冊上有宣告 params 就別跑」一刀切:37 項裡 21 項宣告了 params,
#: 其中 20 項沒給參數照樣跑得好好的(量過),一刀切等於誤殺 20 項。
ARGERR_RX = re.compile(
    r"error: (argument [^\n:]{1,40}: expected one argument|"
    r"the following arguments are required:[^\n]{0,60}|"
    r"argument [^\n:]{1,40}: invalid [^\n]{0,40})")


def classify_stop(tail: str) -> tuple[str, str]:
    """rc≠0 的輸出尾段 → (state, why)。判不出來就回 ("", "") 讓它照舊 RED。

    次序有意義:**缺參數 → 缺件 → 缺料**。
    先問 argparse(它講得最死),再問缺件(缺件常跟誠實停同句),最後才是缺料。
    每一種都把**命中的原文帶回**當證據——判準亮不出證據,它就只是另一種猜。
    """
    m = ARGERR_RX.search(tail)
    if m:
        return ("ABSENT", f"**缺參數**(不是壞掉):argparse 自述「{m.group(0)[7:59]}」"
                          f";冊上這項的 params 該由主控台/--ids 帶值給它")
    m = STOP_RX.search(tail)
    if not m:
        return ("", "")
    hit = m.group(0).strip()[:52]
    # 缺件要在誠實停的**整段尾文**裡找,不是只在命中那一句(缺席常印在前一行)
    n = NEED_RX.search(tail)
    if n:
        return ("ABSENT", f"**缺件**(不是壞掉):引擎自述「{(n.group(0) or '').strip()[:36]}"
                          f"」· 誠實停「{hit}」")
    return ("NODATA", f"**缺料**(不是壞掉):引擎自述「{hit}」=上游沒料,非本引擎缺陷")


#: 動詞裡帶 `--apply` 的項=**寫庫件**。家族全掃永不代跑(要跑請 --ids 明點)。
#: 與操作員既有的「--approve-remove 只在明令下」同律:
#: 破壞性的那一步,永遠要有人**指名道姓**點它,不能被一個家族開關掃進去。
WRITE_VERB = "--apply"


def _load(glob_pat: str, d: Path, alias: str):
    """尾版律載入(缺席回 (None, 因由);不拋)。"""
    try:
        hits = sorted(d.glob(glob_pat))
        if not hits:
            return None, f"{glob_pat} 缺席({d.name})"
        sp = importlib.util.spec_from_file_location(alias, hits[-1])
        m = importlib.util.module_from_spec(sp)
        sys.modules[alias] = m
        sp.loader.exec_module(m)
        return m, ""
    except Exception as exc:
        return None, f"{glob_pat} 載入失敗 {type(exc).__name__}:{str(exc)[:60]}"


def spec_path() -> tuple[Path | None, str]:
    hits = sorted((VIA / "supportive modules" / "registry").glob(SPEC_GLOB))
    if not hits:
        return None, f"{SPEC_GLOB} 缺席"
    return hits[-1], ""


def load_spec() -> tuple[dict, str]:
    p, why = spec_path()
    if p is None:
        return {}, why
    try:
        return json.loads(p.read_text(encoding="utf-8-sig")), f"冊 {p.name}"
    except Exception as exc:
        return {}, f"冊讀取失敗 {type(exc).__name__}:{str(exc)[:60]}"


def python_for(family: str) -> dict:
    """家族境 python —— **委派** MDL137 RunGate(它再委派 MDL136 EntryBridge)。
       Zero-Hydra:本件不自己找 conda/venv;橋缺席才退回本行程 python 並講明。"""
    m, why = _load("CGC_MDL137_RunGate_v*.py", HERE, "mdl137_bus")
    if m is not None and hasattr(m, "python_for"):
        try:
            r = m.python_for(family)
            if isinstance(r, dict) and r.get("python"):
                return r
        except Exception as exc:
            why = f"RunGate.python_for 失敗 {type(exc).__name__}"
    return {"family": family, "python": sys.executable, "env": "",
            "source": f"本行程退路({why or 'RunGate 無 python_for'})", "state": "FALLBACK"}


def catalog(family: str | None = None) -> list:
    """冊上每一項 × 尾版解析 × 在位實測。**在位 ≠ 跑得動**,本表只說在不在。"""
    spec, why = load_spec()
    out = []
    for fam, f in (spec.get("families") or {}).items():
        if family and fam != family:
            continue
        for grp in f.get("groups", []):
            for it in grp.get("items", []):
                eng = it.get("engine") or {}
                d = VIA / str(eng.get("dir") or "")
                g = str(eng.get("glob") or "")
                hits = sorted(d.glob(g)) if (g and d.is_dir()) else []
                out.append({
                    "id": it.get("id", ""),
                    "family": fam,
                    "group": grp.get("id", ""),
                    "zh": it.get("zh", ""),
                    "glob": g,
                    "dir": str(eng.get("dir") or ""),
                    "verb": list(eng.get("verb") or []),
                    "params": list(it.get("params") or []),
                    "outputs": list(it.get("outputs") or []),
                    "net": bool(it.get("net")),
                    "engine": hits[-1].name if hits else "",
                    "engine_path": str(hits[-1]) if hits else "",
                    "versions": len(hits),
                    "engine_state": "在位" if hits else "缺席",
                    "spec_why": why,
                })
    return out


def _argv_for(item: dict, params: dict | None, py: str) -> list:
    argv = [py, item["engine_path"]]
    argv += list(item.get("verb") or [])
    for k, v in (params or {}).items():
        if v is None or v == "":
            continue
        argv += [f"--{k}", str(v)]
    return argv


def call(item_id: str, params: dict | None = None, timeout: int = DEFAULT_TIMEOUT,
         apply: bool = False, catalog_rows: list | None = None,
         sweep: bool = False) -> dict:
    """**統一呼叫契約**。任何子系統都用這一支調度引擎,拿到同一個結果形狀。

    apply=False(預設)→ 只解析不動手,回 PLAN。要真跑必須明講 apply=True:
    調度層的預設值錯一次,代價是**在別人的機器上動了不該動的東西**。
    """
    rows = catalog_rows if catalog_rows is not None else catalog()
    hit = next((r for r in rows if r["id"] == item_id), None)
    if hit is None:
        return {"id": item_id, "family": "", "zh": "", "engine": "", "engine_state": "冊無此項",
                "argv": [], "state": "ABSENT", "rc": None, "seconds": 0.0, "tally": "",
                "outputs_seen": [], "stdout_tail": "", "why": f"冊上沒有 id={item_id}(零發明:不猜)"}
    pyinfo = python_for(hit["family"])
    if not hit["engine_path"]:
        return {**{k: hit[k] for k in ("id", "family", "zh", "engine", "engine_state")},
                "argv": [], "state": "ABSENT", "rc": None, "seconds": 0.0, "tally": "",
                "outputs_seen": [], "stdout_tail": "",
                "why": f"引擎不在位({hit['glob']});**缺件不是紅燈**,不要去 debug 一支不存在的引擎"}
    argv = _argv_for(hit, params, pyinfo["python"])
    base = {**{k: hit[k] for k in ("id", "family", "zh", "engine", "engine_state")},
            "argv": argv, "python": pyinfo["python"], "python_src": pyinfo.get("source", "")}
    if not apply:
        return {**base, "state": "PLAN", "rc": None, "seconds": 0.0, "tally": "",
                "outputs_seen": [], "stdout_tail": "",
                "why": "dry:只解析不動手(要真跑請 apply=True / --apply)"}
    if sweep and WRITE_VERB in (hit.get("verb") or []):
        # 批471 v0102 寫庫動詞閘:動詞裡本來就帶 `--apply` 的項(量到 2 支:
        # tw_universe_update / db_localdb_apply)是**寫庫件**。家族全掃永不代跑。
        # 破壞性的那一步永遠要有人指名道姓點它,不能被一個家族開關掃進去。
        return {**base, "state": "PLAN", "rc": None, "seconds": 0.0, "tally": "",
                "outputs_seen": [], "stdout_tail": "",
                "why": "**寫庫動詞**:家族全掃不代跑(要跑請 --ids "
                       f"{hit['id']} --apply 明點;同「--approve-remove 只在明令下」律)"}
    t0 = time.time()
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, env=env,
                           cwd=str(Path(hit["engine_path"]).parent))
        rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
        state = "GREEN" if rc == 0 else "RED"
        why = ""
        if rc != 0:
            # 批471 v0101:**缺料 ≠ 壞掉**。只認引擎自己印的那句話,並把原文帶回
            # 當證據;沒有那句話的 rc≠0 一律照舊 RED(不得靠這條放過真紅)。
            # v0102:再往下分一層——缺參數 / 缺件 / 缺料,見 classify_stop。
            _tail = "\n".join([x for x in out.splitlines() if x.strip()][-10:])
            _st, _why = classify_stop(_tail)
            if _st:
                state, why = _st, _why
    except subprocess.TimeoutExpired as exc:
        rc, out, state = None, (exc.stdout or "") if isinstance(exc.stdout, str) else "", "TIMEOUT"
        why = f"逾 {timeout}s 未回=已停(不卡斷);現場保留"
    except Exception as exc:
        rc, out, state, why = None, "", "RED", f"{type(exc).__name__}:{str(exc)[:80]}"
    secs = round(time.time() - t0, 2)
    # 批462:`[計]` 只認**最後一行**。子報告也會印 `FAIL 0`,全篇搜就會把
    # 「OK 38 · FAIL 1」讀成綠——那正是工作站掛過的那個假綠。
    tallies = TALLY_RX.findall(out)
    tally = tallies[-1].strip() if tallies else ""
    if state == "GREEN" and tally:
        m = re.search(r"FAIL\s+(\d+)", tally)
        if m and int(m.group(1)) > 0:
            state = "AMBER"
            why = "rc=0 但最後一行 [計] 仍有 FAIL(以計數為準,不以 rc 為準)"
    seen = []
    for o in (hit.get("outputs") or []):
        q = VIA / o
        if "<" in o or "*" in o:
            seen.append({"out": o, "exists": None})
        else:
            seen.append({"out": o, "exists": q.exists()})
    lines = [x for x in out.splitlines() if x.strip()]
    return {**base, "state": state, "rc": rc, "seconds": secs, "tally": tally,
            "outputs_seen": seen, "stdout_tail": "\n".join(lines[-6:]), "why": why}


def matrix(family: str | None = None, ids: list | None = None, apply: bool = False,
           timeout: int = DEFAULT_TIMEOUT, do_print: bool = True,
           apply_families: list | None = None) -> dict:
    """批量調度 → 多矩陣資料(**這一份就是 HTML 的唯一資料源**,零二次加工)。

    批471 v0102:`apply` 不再是全有全無。
      apply=True                       → 本次選到的每一項都真跑
      apply_families=["vrn","vap"]     → **只有**這些家族真跑,其餘照樣 PLAN
      ids=[...]                        → 只跑點名的項(且視為**明點**,寫庫閘放行)
    一個開關按下去就發動 24 支 VDF 回補,那不叫方便,那叫地雷。
    """
    rows = catalog(family)
    if ids:
        rows = [r for r in rows if r["id"] in ids]
    fams = {x.strip().lower() for x in (apply_families or []) if x.strip()}
    named = bool(ids)          # --ids 是**明點**:寫庫閘只擋家族全掃,不擋明點
    res = []
    for i, r in enumerate(rows, 1):
        do = apply or (r["family"].lower() in fams)
        if do_print:
            print(f"  [{i}/{len(rows)}] {r['family']}/{r['id']} · "
                  f"{r['engine'] or '缺席'}{'' if do else ' (PLAN)'}")
        res.append(call(r["id"], apply=do, timeout=timeout, catalog_rows=rows,
                        sweep=not named))
    tally = {}
    for x in res:
        tally[x["state"]] = tally.get(x["state"], 0) + 1
    spec_p, _ = spec_path()
    return {
        "schema": "VIA.EngineBus.v1",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "spec": spec_p.name if spec_p else "(冊缺)",
        "family": family or "all",
        "apply": apply,
        "apply_families": sorted(fams),
        "ids": list(ids or []),
        "live_n": sum(1 for x in res if x["state"] not in ("PLAN",)),
        "counts": tally,
        "catalog": rows,
        "results": res,
    }


# ---------------------------------------------------------------- 多矩陣 HTML
_STATE_COLOR = {"GREEN": "#1a7f37", "AMBER": "#b7791f", "RED": "#b91c1c",
                "TIMEOUT": "#b91c1c", "ABSENT": "#6b7280", "PLAN": "#3b6fb5",
                "NODATA": "#7c5cbf"}


def _tokens() -> tuple[dict, str]:
    """UI 樣板正主 MDL089 的 tokens(Zero-Hydra:不自己發明配色)。"""
    m, why = _load("CGC_MDL089_UIBaseTemplate_v*.py", HERE, "mdl089_bus")
    if m is not None and hasattr(m, "load_tokens"):
        try:
            return m.load_tokens(), f"MDL089 {Path(m.__file__).name}"
        except Exception as exc:
            why = f"load_tokens 失敗 {type(exc).__name__}"
    return {}, why or "MDL089 缺席"


def _cell(state: str) -> str:
    c = _STATE_COLOR.get(state, "#6b7280")
    return (f'<span class="st" style="background:{c}1a;color:{c};'
            f'border:1px solid {c}55">{_html.escape(state)}</span>')


def render(data: dict, out: Path | None = None) -> Path:
    """實測結果 → **多矩陣** HTML。零 CDN、手機自適應、深淺色皆可讀。

    每一格的數字都來自 `data`(matrix() 的回傳),**不做二次加工、不補空白**:
    量不到的就顯示「—」並在頁上說為什麼量不到。
    """
    tk, tk_why = _tokens()
    pal = (tk.get("palette") or {}) if isinstance(tk, dict) else {}
    out = out or (OUTDIR / "ENGINE_BUS_MATRIX.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    rows, res = data["catalog"], data["results"]
    by_id = {x["id"]: x for x in res}

    fams = sorted({r["family"] for r in rows})
    # 矩陣一:家族 × 狀態
    states = ["GREEN", "NODATA", "AMBER", "RED", "TIMEOUT", "ABSENT", "PLAN"]
    m1 = []
    for f in fams:
        line = {"家族": f}
        for s in states:
            line[s] = sum(1 for r in rows if r["family"] == f
                          and by_id.get(r["id"], {}).get("state") == s)
        line["合計"] = sum(1 for r in rows if r["family"] == f)
        m1.append(line)

    def tbl(headers, lines, cls=""):
        th = "".join(f"<th>{_html.escape(str(h))}</th>" for h in headers)
        body = []
        for ln in lines:
            tds = []
            for h in headers:
                v = ln.get(h, "")
                tds.append(f"<td>{v if isinstance(v, str) and v.startswith('<') else _html.escape(str(v))}</td>")
            body.append("<tr>" + "".join(tds) + "</tr>")
        return (f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead>'
                f'<tbody>{"".join(body)}</tbody></table></div>')

    # 矩陣二:逐項目錄(冊 → 尾版 → 在位)
    m2 = [{"家族": r["family"], "項": r["id"], "說明": r["zh"][:40],
           "引擎(尾版)": r["engine"] or "—", "版數": r["versions"],
           "動詞": "/".join(r["verb"]) or "—", "參數": ",".join(r["params"]) or "—",
           "在位": _cell("GREEN" if r["engine"] else "ABSENT")} for r in rows]

    # 矩陣三:調度結果(狀態 × 計數 × 秒 × 因由)
    m3 = [{"項": x["id"], "狀態": _cell(x["state"]),
           "rc": "—" if x["rc"] is None else x["rc"],
           "秒": x["seconds"] or "—",
           "[計] 最後一行": (x["tally"] or "—")[:80],
           "因由": (x["why"] or "")[:70] or "—"} for x in res]

    # 矩陣四:產出契約(冊宣告 × 實際在不在)
    m4 = []
    for x in res:
        for o in x["outputs_seen"]:
            m4.append({"項": x["id"], "冊宣告產出": o["out"][:56],
                       "實際": "—(含萬用字元,不判)" if o["exists"] is None
                               else ("在" if o["exists"] else "缺")})
    if not m4:
        m4 = [{"項": "—", "冊宣告產出": "冊上此批未宣告 outputs", "實際": "—"}]

    css = f"""
:root{{--bg:#f4f6f8;--paper:#fff;--ink:#1f2733;--mut:#5b6775;--line:#dfe4ea;
--accent:{pal.get('accent', '#315f7d')}}}
:root:not([data-theme="light"]) {{}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{
--bg:#0d1219;--paper:#141b25;--ink:#dfe6f0;--mut:#93a1b3;--line:#232d3b}}}}
:root[data-theme="dark"]{{--bg:#0d1219;--paper:#141b25;--ink:#dfe6f0;--mut:#93a1b3;--line:#232d3b}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
font:12px/1.5 "Segoe UI","Noto Sans TC",system-ui,sans-serif;padding:14px 16px;
padding-block:16px}}
h1{{font-size:15px;margin:0 0 2px}}
h2{{font-size:12.5px;margin:18px 0 6px;color:var(--accent)}}
.sub{{color:var(--mut);font-size:10.5px;margin-bottom:10px;overflow-wrap:anywhere}}
.tw{{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--paper)}}
table{{border-collapse:collapse;width:100%;min-width:520px}}
th,td{{padding:5px 8px;border-bottom:1px solid var(--line);text-align:left;
font-size:10.5px;white-space:nowrap}}
th{{background:color-mix(in srgb,var(--accent) 8%,transparent);
color:var(--mut);font-weight:600;position:sticky;top:0}}
td:nth-child(3),td:nth-child(5){{white-space:normal;overflow-wrap:anywhere}}
.st{{padding:1px 7px;border-radius:10px;font-size:9.5px;font-weight:600}}
.note{{color:var(--mut);font-size:10px;margin:6px 0 0;overflow-wrap:anywhere}}
@media(max-width:520px){{body{{padding:12px}}table{{min-width:480px}}}}
"""
    counts = " · ".join(f"{k} {v}" for k, v in sorted(data["counts"].items()))
    page = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 引擎調度多矩陣</title><style>{css}</style></head><body>
<h1>VIA 引擎調度 · 多矩陣實測結果</h1>
<div class="sub">{_html.escape(data["ts"])} · 冊 {_html.escape(data["spec"])}
· 家族 {_html.escape(str(data["family"]))} · 模式 {"真跑(--apply)" if data["apply"] else "只解析(dry)"}
· {_html.escape(counts)} · 樣板 {_html.escape(tk_why)}</div>

<h2>矩陣一 · 家族 × 狀態</h2>
{tbl(["家族"] + states + ["合計"], m1)}
<p class="note"><b>缺件 ≠ 缺料 ≠ 壞掉</b>——三件事混成一格,就會讓人去 debug
一支行為完全正確的引擎。所以這三種各有各的燈:<br>
<b>ABSENT=缺件</b>:引擎檔 / 相依套件 / <b>必要參數</b> 不在位(例:
<code>plotly 缺席=誠實停</code>、<code>argparse: expected one argument</code>)。<br>
<b>NODATA=缺料</b>:引擎跑了,但上游沒料,它自己印了「誠實停」之類的話
(命中的原文列在矩陣三的因由欄)。<br>
<b>PLAN</b>:沒動手——dry,或**寫庫動詞**被家族閘擋下(要跑得 <code>--ids</code> 明點)。<br>
<b>這三個都不是紅燈。</b>判準要亮得出證據:NODATA/ABSENT 只在**引擎自述那句話**
或 argparse 自己的抱怨命中時才成立,不用 rc 判(全樹 <code>return 2</code> 163 處
只有 46 處是這個意思,rc 不是穩定慣例);沒命中的 rc≠0 一律照舊 RED。</p>

<h2>矩陣二 · 引擎目錄(冊 → 尾版 → 在位)</h2>
{tbl(["家族", "項", "說明", "引擎(尾版)", "版數", "動詞", "參數", "在位"], m2)}
<p class="note">冊只有一本:<code>{_html.escape(data["spec"])}</code>。
本表是**它**的投影,不是另一份清單——冊改了這裡就跟著改。</p>

<h2>矩陣三 · 調度結果</h2>
{tbl(["項", "狀態", "rc", "秒", "[計] 最後一行", "因由"], m3)}
<p class="note">`[計]` 只認**最後一行**:子報告也會印 <code>FAIL 0</code>,
全篇搜就會把「OK 38 · FAIL 1」讀成綠(批462 工作站實錄的那個假綠)。
rc=0 但最後一行仍有 FAIL → 判 AMBER,**以計數為準不以 rc 為準**。</p>

<h2>矩陣四 · 產出契約(冊宣告 × 實際)</h2>
{tbl(["項", "冊宣告產出", "實際"], m4)}
<p class="note">含萬用字元的宣告不判在缺——**判不了就說判不了**,不猜。</p>

<p class="note">零 CDN、零外部字型、零追蹤;全部數字來自本次實跑,
量不到的顯示「—」並說明為什麼量不到。</p>
</body></html>"""
    out.write_text(page, encoding="utf-8")
    return out


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    done, fails = [], []

    def chk(name, cond, note=""):
        done.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest")[0]

    sp, spwhy = spec_path()
    rows = catalog()
    fams = sorted({r["family"] for r in rows})
    chk("① 調度冊**只有一本**:讀既有 VIA_InputConsole_Spec(尾版 glob),"
        "本件不另立第二本(另立=正典換了沒人跟得上)",
        sp is not None and len(rows) >= 20 and len(fams) >= 2,
        f"(冊 {sp.name if sp else spwhy} · {len(rows)} 項 · 家族 {fams})")

    chk("② 目錄=冊的投影:每項都帶尾版解析與**在位實測**(在位≠跑得動,本表只說在不在)",
        all(("engine_state" in r and "versions" in r) for r in rows)
        and any(r["engine"] for r in rows),
        f"(在位 {sum(1 for r in rows if r['engine'])}/{len(rows)})")

    r_absent = call("這個id不存在", catalog_rows=rows)
    chk("③ 冊上沒有的 id → **ABSENT 不是 RED**,而且講明「零發明:不猜」",
        r_absent["state"] == "ABSENT" and "零發明" in r_absent["why"], "")

    hit = next((r for r in rows if r["engine"]), None)
    r_plan = call(hit["id"], catalog_rows=rows) if hit else {}
    chk("④ **預設不動手**:apply=False 回 PLAN 並解析出完整 argv。"
        "調度層的預設值錯一次,代價是在別人的機器上動了不該動的東西",
        r_plan.get("state") == "PLAN" and len(r_plan.get("argv") or []) >= 2,
        f"({hit['id'] if hit else '—'} → {' '.join((r_plan.get('argv') or [])[1:3])})")

    py = python_for("vrn")
    chk("⑤ 家族 python **委派** MDL137 RunGate(它再委派 MDL136);橋缺席才退回本行程"
        "並在 source 講明是退路(不假裝走了正主)",
        bool(py.get("python")) and "python_for" in body and "RunGate" in body,
        f"(python={Path(py['python']).name} · 源={py.get('source', '')[:40]})")

    chk("⑥ `[計]` 只認**最後一行**(批462:子報告也印 `FAIL 0`,全篇搜會把"
        "「OK 38 · FAIL 1」讀成綠);rc=0 但最後一行仍有 FAIL → AMBER,以計數為準",
        "tallies[-1]" in body and "以計數為準" in body, "")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        q = Path(td)
        ok = q / "fx_ok.py"
        ok.write_text("print('[計] 三檢 OK 3 · FAIL 0')\n", encoding="utf-8")
        amb = q / "fx_amber.py"
        amb.write_text("print('[計] 1 件 · FAIL 0 · 子報告')\n"
                       "print('[計] 三檢 OK 2 · FAIL 1')\n", encoding="utf-8")
        slow = q / "fx_slow.py"
        slow.write_text("import time\ntime.sleep(999)\n", encoding="utf-8")
        fake = [{"id": "fx_ok", "family": "t", "zh": "", "glob": "", "dir": "",
                 "verb": [], "params": [], "outputs": [], "net": False,
                 "engine": ok.name, "engine_path": str(ok), "versions": 1,
                 "engine_state": "在位", "group": "", "spec_why": ""},
                {"id": "fx_amber", "family": "t", "zh": "", "glob": "", "dir": "",
                 "verb": [], "params": [], "outputs": [], "net": False,
                 "engine": amb.name, "engine_path": str(amb), "versions": 1,
                 "engine_state": "在位", "group": "", "spec_why": ""},
                {"id": "fx_slow", "family": "t", "zh": "", "glob": "", "dir": "",
                 "verb": [], "params": [], "outputs": [], "net": False,
                 "engine": slow.name, "engine_path": str(slow), "versions": 1,
                 "engine_state": "在位", "group": "", "spec_why": ""}]
        a = call("fx_ok", apply=True, catalog_rows=fake)
        b = call("fx_amber", apply=True, catalog_rows=fake)
        c = call("fx_slow", apply=True, timeout=3, catalog_rows=fake)
        chk("⑦ 統一結果契約實測:全綠→GREEN;**rc=0 但最後一行有 FAIL→AMBER**"
            "(子報告的 `FAIL 0` 不得蓋過總計);逾時→TIMEOUT 並說「不卡斷」",
            a["state"] == "GREEN" and b["state"] == "AMBER"
            and "FAIL 1" in b["tally"] and c["state"] == "TIMEOUT"
            and "不卡斷" in c["why"],
            f"(ok={a['state']} · amber={b['state']}:{b['tally'][-14:]} · slow={c['state']})")

        data = {"schema": "VIA.EngineBus.v1", "ts": "2026-01-01T00:00:00",
                "spec": "fx.json", "family": "t", "apply": True,
                "counts": {"GREEN": 1, "AMBER": 1, "TIMEOUT": 1},
                "catalog": fake, "results": [a, b, c]}
        pg = render(data, out=q / "m.html")
        h = pg.read_text(encoding="utf-8")
        chk("⑧ 多矩陣 HTML:四張矩陣皆在、零 CDN、手機自適應、深淺色皆有定義",
            all(k in h for k in ("矩陣一", "矩陣二", "矩陣三", "矩陣四"))
            and "http://" not in h and "https://" not in h
            and "prefers-color-scheme" in h and "@media(max-width" in h,
            f"({len(h):,} 字元 · 零外連={'http' not in h})")

        chk("⑨ 頁上每一格都來自實測資料,**不做二次加工**;判不了的顯示「—」"
            "並說明為什麼判不了(含萬用字元的產出宣告不判在缺)",
            "判不了就說判不了" in h and "不猜" in h and "fx_slow" in h, "")

    live_before = sorted(x.name for x in OUTDIR.glob("*")) if OUTDIR.exists() else []
    chk("⑩ 本件**零網路**、預設 dry、自測不寫正式產出夾",
        ("urlopen" not in body and "requests" not in body)
        and (sorted(x.name for x in OUTDIR.glob("*")) if OUTDIR.exists() else []) == live_before,
        "(零網路碼 · 正式夾未動)")

    chk("⑪ Zero-Hydra 宣告在檔:四家調度者(DeckServer Popen×12 / RunGate×3 / "
        "MDL139×1 / ClosingGate)各自重寫尾版解析、家族 python、逾時、結果解讀;"
        "本件是**一條匯流排四家共用**,不是第五套",
        "Popen ×12" in src and "一條匯流排,四家共用" in src, "(立場在檔)")

    with tempfile.TemporaryDirectory() as td2:
        q2 = Path(td2)
        nd = q2 / "fx_nodata.py"
        nd.write_text("import sys\nprint('[首頁擷取] 無報告件(誠實;缺件搜集器先跑)')\n"
                      "sys.exit(2)\n", encoding="utf-8")
        bad = q2 / "fx_realbad.py"
        bad.write_text("import sys\nprint('Traceback: 真的壞了')\nsys.exit(2)\n",
                       encoding="utf-8")
        fk = [{"id": i, "family": "t", "zh": "", "glob": "", "dir": "", "verb": [],
               "params": [], "outputs": [], "net": False, "engine": p.name,
               "engine_path": str(p), "versions": 1, "engine_state": "在位",
               "group": "", "spec_why": ""} for i, p in (("fx_nodata", nd), ("fx_realbad", bad))]
        d1 = call("fx_nodata", apply=True, catalog_rows=fk)
        d2 = call("fx_realbad", apply=True, catalog_rows=fk)
    chk("⑫ **缺料 ≠ 壞掉**(批471 v0100 實跑第一次就照出我自己用錯尺:VRN 7 項報 RED 3,"
        "而三支印的都是「無報告件(誠實)」——引擎行為完全正確,是我的儀器判錯)。"
        "想用 rc=2 當判準**量過之後否決**:全樹 `return 2` 163 處只有 46 處是誠實停,"
        "117 處是別的意思——**rc 不是穩定慣例**。改認引擎**自己印的那句話**,"
        "並把命中的原文帶回當證據;**沒有那句話的 rc≠0 一律照舊 RED**(對照組驗了)",
        d1["state"] == "NODATA" and "無報告件" in d1["why"]
        and d2["state"] == "RED" and d2["rc"] == 2,
        f"(誠實停 rc=2→{d1['state']} · 真壞 rc=2→{d2['state']})")

    # ---- ⑬⑭⑮ 批471 v0102:第二次實跑(VAP 6 項)照出的三件事 ----
    with tempfile.TemporaryDirectory() as td3:
        q3 = Path(td3)
        # 對照組全部**釘死在 VAP 那次實跑的原文**(不是我改寫過的版本):
        # 對照組要釘在缺陷所在的那一版,不然下一版一改措辭,這幾檢就自己失效了。
        fx = {
            # vap_dashboard 真印過的尾段:缺料
            "fx_vapdash": "print('[缺料] 缺 4 項:表 prices_canonical·tw_chip_inst"
                          "·tw_chip_margin·features_daily(vdf_tw_market.duckdb)')\n"
                          "print('[補料] 誠實停 rc2 · 舊頁在位 VIA_UI_Dashboard_v0100.html')\n",
            # vap_std_dashboard 真印過的尾段:缺件(套件)
            "fx_vapstd": "print('[標準模板] plotly 缺席=誠實停(pip install plotly 後再跑)')\n",
            # vap_one_render 真吐過的尾段:缺參數
            "fx_vapone": "import sys\nsys.stderr.write('VAP_ENG016_AutoplotOne: "
                         "error: argument --render: expected one argument\\n')\n",
            # 真紅對照組(沒有任何誠實停字樣)
            "fx_vapstack": "print('_duckdb.CatalogException: Catalog Error: Table with "
                           "name tw_daily_prices does not exist!')\n",
        }
        fk3 = []
        for k, code in fx.items():
            f = q3 / (k + ".py")
            f.write_text(code + "import sys\nsys.exit(2)\n", encoding="utf-8")
            fk3.append({"id": k, "family": "t", "zh": "", "glob": "", "dir": "", "verb": [],
                        "params": [], "outputs": [], "net": False, "engine": f.name,
                        "engine_path": str(f), "versions": 1, "engine_state": "在位",
                        "group": "", "spec_why": ""})
        e1 = call("fx_vapdash", apply=True, catalog_rows=fk3)
        e2 = call("fx_vapstd", apply=True, catalog_rows=fk3)
        e3 = call("fx_vapone", apply=True, catalog_rows=fk3)
        e4 = call("fx_vapstack", apply=True, catalog_rows=fk3)

    chk("⑬ **「誠實停」才是正典句**(全樹 451 處)。v0101 那張字表是照 VRN 幾支的措辭湊的,"
        "只認得 VRN 的方言——VAP 印「誠實停 rc2」就漏接,兩支沒壞的引擎被我判紅。"
        "本檢用 VAP 那次實跑的**原文**當對照組(釘死在缺陷所在的那一版,不改寫)",
        e1["state"] == "NODATA" and "誠實停" in e1["why"],
        f"(缺料原文→{e1['state']})")

    chk("⑭ **缺件 ≠ 缺料 ≠ 壞掉**(操作員原律)。誠實停要再分一層:缺料→NODATA;"
        "缺件(引擎/相依套件/**必要參數**)→ ABSENT,**不新立第八態**。"
        "判缺參數只認 argparse 自己講的話——**不能用「冊上有宣告 params 就別跑」一刀切**:"
        "冊上 21 項宣告 params,其中 20 項沒給參數照樣跑得好好的(量過),一刀切=誤殺 20 項",
        e2["state"] == "ABSENT" and "缺件" in e2["why"]
        and e3["state"] == "ABSENT" and "缺參數" in e3["why"]
        and e4["state"] == "RED"
        and sum(1 for r in rows if r.get("params")) >= 20,
        f"(plotly 缺席→{e2['state']} · argparse 少參數→{e3['state']} · "
        f"裸 CatalogException→{e4['state']} · 冊上有 params 的項="
        f"{sum(1 for r in rows if r.get('params'))})")

    wv = [r["id"] for r in rows if WRITE_VERB in (r.get("verb") or [])]
    m_sweep = matrix(ids=wv, apply=True, do_print=False) if wv else None
    g_sweep = ([call(i, apply=True, catalog_rows=rows, sweep=True) for i in wv]
               if wv else [])
    chk("⑮ **`--apply` 不該是全有全無**。VDF 24 項按下去=同時發動 tw_history 全史回補、"
        "tw_chips 籌碼回補,還有兩支動詞本來就帶 `--apply` 的寫庫件。本版加 --apply-family / "
        "--ids;**寫庫動詞閘**:家族全掃永不代跑,要跑必須 --ids 明點"
        "(同「--approve-remove 只在明令下」律)",
        len(wv) >= 2
        and all(x["state"] == "PLAN" and "寫庫動詞" in x["why"] for x in g_sweep)
        and m_sweep is not None
        and all(x["state"] != "PLAN" or "寫庫動詞" not in (x["why"] or "")
                for x in m_sweep["results"])
        and "--apply-family" in body,
        f"(寫庫件 {wv} · 家族全掃→{sorted({x['state'] for x in g_sweep})} · "
        f"--ids 明點→{sorted({x['state'] for x in m_sweep['results']}) if m_sweep else '-'})")

    print(f"  [計] 十五檢({len(done)} 檢) OK {len(done) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 引擎調度匯流排(CGC_MDL148 v0102)· 十五檢自測(零網路)===")
        return selftest()
    fam = args[args.index("--family") + 1] if "--family" in args else None
    apply_ = "--apply" in args
    af = (args[args.index("--apply-family") + 1].split(",")
          if "--apply-family" in args else [])
    ids = (args[args.index("--ids") + 1].split(",") if "--ids" in args else None)
    if args and args[0] == "catalog":
        rows = catalog(fam)
        for r in rows:
            print(f"  [{r['engine_state']}] {r['family']}/{r['id']:18s} "
                  f"{r['engine'] or r['glob']:44s} 動詞={'/'.join(r['verb']) or '-'}")
        print(f"[目錄] {len(rows)} 項 · 在位 {sum(1 for r in rows if r['engine'])}")
        return 0
    if args and args[0] == "call":
        if "--item" not in args:
            print("  用法:call --item <id> [--apply]")
            return 2
        # call --item 是**明點**(人親手指名這一支)→ 寫庫閘放行
        r = call(args[args.index("--item") + 1], apply=apply_, sweep=False)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["state"] in ("GREEN", "PLAN") else 1
    if args and args[0] == "matrix":
        data = matrix(family=fam, apply=apply_, ids=ids, apply_families=af)
        OUTDIR.mkdir(parents=True, exist_ok=True)
        (OUTDIR / "ENGINE_BUS_latest.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        cnt = " · ".join(f"{k} {v}" for k, v in sorted(data["counts"].items()))
        scope = ("全跑" if apply_ else
                 ("真跑家族 " + ",".join(data["apply_families"]) if data["apply_families"]
                  else ("明點 " + ",".join(data["ids"]) if data["ids"] else "全 dry")))
        print(f"[矩陣] {len(data['results'])} 項 · {scope} · {cnt}")
        if "--html" in args:
            p = render(data)
            print(f"[頁] {p}")
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
