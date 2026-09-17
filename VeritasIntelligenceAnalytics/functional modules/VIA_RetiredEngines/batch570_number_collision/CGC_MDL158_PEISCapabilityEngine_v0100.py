#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL158_PEISCapabilityEngine v0100 — PEIS 能力引擎(批568;VIA 這一側的掛線口)

操作員令(批568):「將 session_01FQMN8uBxreDrzmDUpPrXTG 引擎整合進來」+ PEIS 系統說明六功能
  + 「用引擎去執行以節省 TOKEN」+「你自己收留整合後啟動她」。

【先量再說 · 零九頭龍】
  PEIS 那六件功能(搜尋領域→AST 全景→聚眾→低風險合併→完整測試→鎖定→能力抽象→快速截取)
  **已經有一支寫好的正主**:`via_unified_engine.py` v0200(VIA-VIA-ENG996),6,628 行、純標準庫、
  零網路、零安裝、不改來源檔、自測 69/69。那是操作員自己另一個 session 的產出。
  所以這一批**不重寫**——重寫就是第二顆頭(零九頭龍),而且要把別人驗過的 69 檢再驗一次。
  做法是 VIA 的老規矩:**正本收容 + 一個掛線口**。

【正本零觸碰】
  正本放在 `functional modules/VIA_PEIS/references/intake/PEIS_UnifiedEngine_b568/`,
  連同 `_INTAKE_MANIFEST_b568.json`(來源 repo/commit + 每檔 md5/sha256)。
  本檔**一個 byte 都不改它**,只用 subprocess 代跑(它本來就設計成可獨立執行)。
  正本換版=收容夾換一份 + manifest 換一份,本檔的路徑解析走 glob 尾版,零維護。

【誠實四態】
  rc 0=GREEN(有重複、聚成能力、帳算得出來)· 1=RED(引擎自己報錯/守則被破)
  · 2=NODATA(掃得動但**沒有重複** —— 照 PEIS 啟動條件,無重複就不啟動整合,這不是紅燈)
  · 3=ABSENT(收容正本不在)

【紀律(寫在檔頭,因為「整合」最容易偷偷破掉)】
  · **不代設同意閘**:本檔不設任何 VIA_*_CONSENT / API key。
  · **不代裝套件**:正本是純標準庫,本檔也是;缺件就誠實 ABSENT,不裝。
  · **零網路**:自測零網路;代跑時 env 明示 VIA_NET_DISABLED=1。
  · **不改來源**:PEIS 預設 AUDIT/READ_ONLY_SOURCES,本檔**不提供 --apply**——
    能力表落地與引擎鎖定是操作員的裁定(LL90 同族),要落地請直接對正本下 `--apply`。
  · **只增不減**:能力庫與能力表 append-only,本檔只讀不刪。

用法:
  via-peis status                 收容正本在不在 · 版本 · 自測(69 檢)
  via-peis scan  [--family vdf]   INTAKE→SCAN→CLUSTER→TEST→LOCK→ANNOTATE→STORE(AUDIT)
  via-peis cards [--cap X]        能力卡 capsule(AI 只讀卡,不讀全文原始碼)
  via-peis run   <能力> [--params JSON]   快速截取層 RUN(capability, params)
  via-peis report                 token 節省帳 + CME 能力表現況
  via-peis --selftest             本掛線口自測
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
import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "peis"
STORE = REPORTS / "VIA_Capability_Store.sqlite"   # 能力庫(append-only;省略 --db 就只在記憶體=白掃)
INTAKE_GLOB = "functional modules/VIA_PEIS/references/intake/PEIS_UnifiedEngine_b*"

# 家族 → 掃描起點(只給目錄,PEIS 自己遞迴;不觸網、不改檔)
FAMILIES = {
    "vdf": ["functional modules/VDF/engine"],
    "vrn": ["functional modules/VRN"],
    "vap": ["functional modules/VAP/engine"],
    "cgc": ["supportive modules/registry"],
    "sup": ["supportive modules"],
}
# 收容件與退役件不掃:正本零觸碰,退役件不是活樹(L38 同族)
SKIP_PARTS = ("references/intake", "VIA_RetiredEngines", "__pycache__", "node_modules", ".git",
              "ASSETS/SCOPE_COPY")


# ────────────────────────── 收容正本解析(尾版律) ──────────────────────────
def intake_dir() -> Path | None:
    cands = sorted(VIA.glob(INTAKE_GLOB))
    return cands[-1] if cands else None


def engine_path() -> Path | None:
    d = intake_dir()
    if d is None:
        return None
    p = d / "via_unified_engine.py"
    return p if p.exists() else None


def manifest() -> dict:
    d = intake_dir()
    if d is None:
        return {"state": "ABSENT", "why": "收容夾不在"}
    m = sorted(d.glob("_INTAKE_MANIFEST_b*.json"))
    if not m:
        return {"state": "ABSENT", "why": "manifest 不在"}
    try:
        j = json.loads(m[-1].read_text(encoding="utf-8"))
    except Exception as exc:
        return {"state": "FAIL", "why": f"{type(exc).__name__}: {exc}"}
    return {"state": "OK", "src": m[-1].name, "batch": j.get("batch"),
            "source": j.get("source", {}), "files": j.get("files", [])}


def _env() -> dict:
    e = dict(os.environ)
    e["VIA_NET_DISABLED"] = "1"      # 零網路:代跑時明示(正本本來就不連網,這是雙保險)
    e["PYTHONUTF8"] = "1"
    e["PYTHONIOENCODING"] = "utf-8"
    return e


def call(args: list, timeout: int = 1800, cwd: Path | None = None) -> dict:
    """代跑收容正本。回 {rc, out, err};正本零觸碰——只讀它、只跑它。"""
    p = engine_path()
    if p is None:
        return {"rc": 3, "out": "", "err": "收容正本不在(誠實 ABSENT)"}
    # PEIS 的能力庫/報告是**相對 cwd** 落檔的。不指定就會散到 VIA 根目錄變成未追蹤雜訊,
    # 所以一律關進 VIA_Reports/peis(已在 .gitignore),自測則各自關進自己的暫存夾。
    REPORTS.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, str(p), *args], capture_output=True, text=True,
                       timeout=timeout, stdin=subprocess.DEVNULL,
                       cwd=str(cwd or REPORTS), env=_env())
    return {"rc": r.returncode, "out": r.stdout, "err": r.stderr}


def _json_call(args: list, timeout: int = 1800, cwd: Path | None = None) -> dict:
    r = call([*args, "--json"], timeout=timeout, cwd=cwd)
    if r["rc"] == 3:
        return {"state": "ABSENT", "why": r["err"]}
    line = ""
    for l in (r["out"] or "").strip().splitlines():
        if l.strip().startswith("{"):
            line = l.strip()
    if not line:
        # 批567 L62:敗了就給全文,不切
        return {"state": "FAIL", "rc": r["rc"], "why": (r["err"] or r["out"] or "無輸出").strip()}
    try:
        return {"state": "OK", "rc": r["rc"], "json": json.loads(line)}
    except Exception as exc:
        return {"state": "FAIL", "rc": r["rc"], "why": f"{type(exc).__name__}: {exc} / {line}"}


# ────────────────────────── 家族掃描來源 ──────────────────────────
def family_srcs(fam: str) -> list:
    out = []
    for rel in FAMILIES.get(fam, []):
        p = VIA / rel
        if p.exists():
            out.append(p)
    return out


def _live(p: Path) -> bool:
    s = str(p).replace("\\", "/")
    return not any(k in s for k in SKIP_PARTS)


# ────────────────────────── 動詞 ──────────────────────────
def status() -> dict:
    p, m = engine_path(), manifest()
    if p is None:
        return {"state": "ABSENT", "why": "收容正本 via_unified_engine.py 不在", "manifest": m}
    v = _json_call(["version"], timeout=300)
    st = call(["selftest"], timeout=900)
    tail = [l for l in (st["out"] + st["err"]).strip().splitlines() if l.strip()][-1:]
    return {"state": "OK" if st["rc"] == 0 else "FAIL", "engine": str(p.relative_to(VIA)),
            "selftest_rc": st["rc"], "selftest_tail": " / ".join(tail),
            "version": (v.get("json") or {}) if v.get("state") == "OK" else v,
            "manifest": m}


def scan(fams: list, out_dir: Path | None = None) -> dict:
    srcs = []
    for f in fams:
        srcs += [s for s in family_srcs(f) if _live(s)]
    if not srcs:
        return {"state": "ABSENT", "why": f"家族沒有可掃的起點:{fams}"}
    args = ["ingest", "--db", str(STORE), "--root", str(VIA)]
    for s in srcs:
        args += ["--src", str(s)]
    r = _json_call(args, timeout=3600, cwd=out_dir)
    if r.get("state") != "OK":
        return r
    j = r["json"]
    c, t = j.get("counts", {}), j.get("token_ledger", {})
    # PEIS 啟動條件:無重複 → 不啟動整合(誠實 NODATA,不是紅燈)
    dup = int(c.get("collapsed", 0)) + int(c.get("near_duplicates", 0))
    return {"state": "OK" if dup > 0 else "NODATA",
            "families": fams, "srcs": [str(s.relative_to(VIA)) for s in srcs],
            "files": c.get("files"), "functions": c.get("functions"),
            "capabilities": c.get("capabilities"), "sealed": c.get("sealed"),
            "pending": c.get("pending"), "collapsed": c.get("collapsed"),
            "near": c.get("near_duplicates"), "dup_total": dup,
            "source_tokens": t.get("source_tokens"), "capsule_tokens": t.get("capsule_tokens"),
            "saved_tokens": t.get("saved_tokens"), "saved_percent": t.get("saved_percent"),
            "mode": j.get("mode"), "source_mutation": j.get("source_mutation"),
            "why": "" if dup > 0 else "零重複=照 PEIS 啟動條件不啟動整合(誠實 NODATA)"}


def _need_store() -> dict | None:
    """能力庫不在=還沒 scan 過。誠實 NODATA,不編一個空答案。"""
    if not STORE.exists():
        return {"state": "NODATA", "why": f"能力庫還沒建:先跑 via-peis scan --family vdf,vrn({STORE.name})"}
    return None


def cards(cap: str = "", out_dir: Path | None = None) -> dict:
    miss = _need_store()
    if miss:
        return miss
    a = ["capsule", "--db", str(STORE), "--root", str(VIA)] + (["--capability", cap] if cap else [])
    return _json_call(a, timeout=900, cwd=out_dir)


def _sig_order(cap: str, out_dir: Path | None = None) -> list:
    """從能力卡的簽章取參數順序:`upside(target, current)` → ['target','current']。"""
    r = cards(cap, out_dir)
    if r.get("state") != "OK":
        return []
    for c in (r.get("json") or {}).get("cards", []):
        if c.get("cap") == cap:
            sig = str(c.get("sig") or "")
            if "(" in sig and sig.endswith(")"):
                inner = sig[sig.index("(") + 1:-1]
                names = []
                for part in inner.split(","):
                    nm = part.split("=")[0].split(":")[0].strip().lstrip("*")
                    if nm:
                        names.append(nm)
                return names
    return []


def run_cap(cap: str, params: str = "", out_dir: Path | None = None) -> dict:
    """快速截取層 RUN(capability, params)。

    批568 實測:正本沙箱車道是 `def_execute_guarded(..., list(payload or []))`——
    傳**陣列**沒問題(`--args '[180,120]'` → result 0.5),傳**物件**就變成把 key 當引數
    (`list({'target':..})` = `['target','current']` → TypeError)。
    可是操作員寫的 PEIS 規格用的正是物件:`RUN(math, {symbol: "2330"})`。
    正本零觸碰,所以轉接放在這裡:物件依**能力卡的簽章順序**攤成位置引數再送 --args;
    簽章讀不到就不猜——原樣送 --params,並把正本的話原封回報(L62 敗站不截斷)。
    """
    miss = _need_store()
    if miss:
        return miss
    a = ["run", "--capability", cap, "--db", str(STORE), "--root", str(VIA)]
    lane = ""
    if params:
        try:
            v = json.loads(params)
        except Exception:
            return {"state": "FAIL", "why": f"--params 不是合法 JSON:{params}"}
        if isinstance(v, list):
            a += ["--args", json.dumps(v, ensure_ascii=False)]
            lane = "args(陣列直送)"
        elif isinstance(v, dict):
            order = _sig_order(cap, out_dir)
            if order and all(k in v for k in order):
                a += ["--args", json.dumps([v[k] for k in order], ensure_ascii=False)]
                lane = f"args(依卡上簽章順序攤平:{order})"
            else:
                a += ["--params", params]
                miss_k = [k for k in order if k not in v] if order else []
                lane = ("params(原樣送;簽章讀不到=不猜)" if not order
                        else f"params(原樣送;物件缺 {miss_k}=不猜)")
        else:
            a += ["--args", json.dumps([v], ensure_ascii=False)]
            lane = "args(純量包成單一引數)"
    r = _json_call(a, timeout=900, cwd=out_dir)
    if lane:
        r["lane"] = lane
    return r


def report(out_dir: Path | None = None) -> dict:
    miss = _need_store()
    if miss:
        return miss
    return _json_call(["report", "--db", str(STORE), "--root", str(VIA)], timeout=900, cwd=out_dir)


def write_out(name: str, payload: dict) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    p = REPORTS / name
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


# ────────────────────────── 自測 ──────────────────────────
def selftest() -> int:
    n = [0]
    fails = []

    def chk(name, ok, note=""):
        n[0] += 1
        mark = "OK" if ok else "FAIL"
        if not ok:
            fails.append(name)
        # 批567 L62:敗的那一條註記不截斷
        print(f"  [{mark}] {name}" + (f" ({note})" if note else ""))

    print(f"=== CGC_MDL158 PEIS 能力引擎 v{VERSION} · 掛線口自測(零網路;不改來源) ===")
    d, p, m = intake_dir(), engine_path(), manifest()
    chk("① 收容正本在位(尾版 glob;夾+引擎+manifest 三件齊)",
        d is not None and p is not None and m.get("state") == "OK",
        f"({d.name if d else 'ABSENT'} · {len(m.get('files', []))} 檔)")

    src_ok = m.get("source", {})
    chk("② manifest 記得來源 repo/commit(說得出這支引擎打哪來,不是憑空長出來的)",
        bool(src_ok.get("repo")) and len(str(src_ok.get("commit", ""))) >= 12,
        f"({src_ok.get('repo')} @ {str(src_ok.get('commit'))[:12]})")

    ok_hash = True
    import hashlib
    for f in m.get("files", []):
        q = (d / f["name"]) if d else None
        if q is None or not q.exists() or hashlib.sha256(q.read_bytes()).hexdigest() != f["sha256"]:
            ok_hash = False
    chk("③ 正本零觸碰:每一檔的 sha256 與 manifest 逐字相符", ok_hash,
        f"({len(m.get('files', []))} 檔比對)")

    st = status()
    chk("④ 收容正本自己的 69 檢跑得過(不是我說它好,是它自己報)",
        st.get("state") == "OK" and st.get("selftest_rc") == 0, st.get("selftest_tail", ""))

    ver = st.get("version") or {}
    chk("⑤ 引擎身份卡讀得到(協定/規格/門檻齊)",
        isinstance(ver, dict) and bool(ver), f"({str(ver)[:90]}…)" if ver else "")

    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("⑥ 本掛線口零網路、零安裝(不 import requests/httpx/urllib;不呼叫 pip/conda)",
        not any(k in code for k in ("import requests", "import httpx", "import urllib",
                                    "pip install", "conda install")))
    chk("⑦ 不代設同意閘(本檔不寫任何 VIA_*_CONSENT / API key)",
        "CONSENT" not in code.replace("VIA_*_CONSENT", "").replace("不代設任何 VIA", ""))
    chk("⑧ 不提供 --apply:能力表落地與引擎鎖定是操作員的裁定,不由本口代行",
        '"--apply"' not in code and "'--apply'" not in code)
    chk("⑨ 代跑時明示零網路旗標",
        'e["VIA_NET_DISABLED"] = "1"' in code)
    chk("⑩ 掃描排除收容件與退役件(正本零觸碰 · 退役件不是活樹)",
        all(k in SKIP_PARTS for k in ("references/intake", "VIA_RetiredEngines")))
    chk("⑪ 帶加速器橋(MDL156 v0104 覆蓋閘)",
        "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))

    # 真跑一次:拿一個最小的合成語料,驗四態與帳都對得起來
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        (t / "a.py").write_text(
            "def calc_total(xs):\n    s = 0\n    for x in xs:\n        s += x\n    return s\n",
            encoding="utf-8")
        (t / "b.py").write_text(
            "def compute_total(values):\n    acc = 0\n    for v in values:\n        acc += v\n    return acc\n",
            encoding="utf-8")
        r = _json_call(["ingest", "--src", str(t), "--db", str(t / "s.sqlite"), "--root", str(t)],
                       timeout=900, cwd=t)
        j = (r.get("json") or {})
        c = j.get("counts", {})
        chk("⑫ 合成語料真跑:兩支換名同義實作被聚成一個能力(這就是『低風險無損耗合併』的證據)",
            r.get("state") == "OK" and int(c.get("collapsed", 0)) >= 1,
            f"(檔 {c.get('files')} · 函式 {c.get('functions')} · 能力 {c.get('capabilities')} · 折疊 {c.get('collapsed')})")
        chk("⑬ 真跑不改來源(mode=READ_ONLY_SOURCES 且 source_mutation=False)",
            j.get("mode") == "READ_ONLY_SOURCES" and j.get("source_mutation") is False,
            f"({j.get('mode')} / {j.get('source_mutation')})")
        before = sorted((x.name, x.read_bytes()) for x in (t / "a.py", t / "b.py"))
        chk("⑭ 真跑後兩支來源檔位元組不變(不是看旗標,是真的比 bytes)",
            before == sorted((x.name, x.read_bytes()) for x in (t / "a.py", t / "b.py")))
        tl = j.get("token_ledger", {})
        chk("⑮ token 帳算得出來且誠實(小語料可能為負也照報,不為了好看放寬)",
            isinstance(tl.get("source_tokens"), int) and "saved_tokens" in tl,
            f"(原文 {tl.get('source_tokens')} → capsule {tl.get('capsule_tokens')} · 省 {tl.get('saved_percent')}%)")

        # 零重複語料 → 啟動條件不成立 → NODATA,不是紅燈
        t2 = t / "solo"
        t2.mkdir()
        (t2 / "only.py").write_text("def z_unique_thing(q):\n    return q\n", encoding="utf-8")
        r2 = _json_call(["ingest", "--src", str(t2), "--db", str(t2 / "s2.sqlite"), "--root", str(t2)],
                        timeout=900, cwd=t2)
        c2 = (r2.get("json") or {}).get("counts", {})
        chk("⑯ 啟動條件:零重複語料 → 折疊 0(照 PEIS 規則不啟動整合;掛線口報 NODATA 不報紅)",
            r2.get("state") == "OK" and int(c2.get("collapsed", 0)) == 0,
            f"(折疊 {c2.get('collapsed')} · 近似 {c2.get('near_duplicates')})")

    with tempfile.TemporaryDirectory() as td3:
        t3 = Path(td3)
        (t3 / "c.py").write_text("def sum_values(xs):\n    return sum(xs)\n", encoding="utf-8")
        db3 = t3 / "k.sqlite"
        _json_call(["ingest", "--src", str(t3), "--db", str(db3), "--root", str(t3)], timeout=900, cwd=t3)
        rep3 = _json_call(["report", "--db", str(db3), "--root", str(t3)], timeout=900, cwd=t3)
        chk("⑰ 能力庫真的落地、且落地後 report/cards 讀得到(省略 --db 只在記憶體=白掃一場,這是本口第一版踩過的坑)",
            db3.exists() and rep3.get("state") == "OK",
            f"(db {db3.exists()} · report {rep3.get('state')})")

    if STORE.exists():
        ro = run_cap("misc.upside", '{"target": 180, "current": 120}')
        ra = run_cap("misc.upside", "[180, 120]")
        chk("⑱ 快速截取層 RUN(capability, params):物件道與陣列道給同一個答案(物件道靠卡上簽章攤平,正本零觸碰)",
            ro.get("state") == "OK" and ra.get("state") == "OK"
            and (ro.get("json") or {}).get("result") == (ra.get("json") or {}).get("result"),
            f"(物件 {(ro.get('json') or {}).get('result')} · 陣列 {(ra.get('json') or {}).get('result')} · 車道 {ro.get('lane')})")
    else:
        chk("⑱ 快速截取層 RUN:能力庫還沒建,誠實跳過(不假裝綠)", True, "能力庫不在=先跑 via-peis scan")

    chk("⑲ 家族起點都在活樹上(vdf/vrn/vap/cgc/sup 五族;不在的誠實缺,不編)",
        all(isinstance(v, list) and v for v in FAMILIES.values())
        and sum(1 for f in FAMILIES if family_srcs(f)) >= 4,
        f"({[f for f in FAMILIES if family_srcs(f)]})")

    # LL112:分子分母要數同一件事。檢數一律由 n[0] 推導,不寫死——
    # 本檔第一版就寫死「二十檢」而實跑 19(中間漏了一個標籤號),當場被這行抓到。
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="CGC_MDL158_PEISCapabilityEngine", description="PEIS 能力引擎掛線口")
    ap.add_argument("verb", nargs="?", default="status",
                    choices=["status", "scan", "cards", "run", "report"])
    ap.add_argument("cap", nargs="?", default="")
    ap.add_argument("--family", default="", help="vdf|vrn|vap|cgc|sup(逗號分隔;預設 vdf,vrn)")
    ap.add_argument("--params", default="", help="RUN(capability, params) 的 params(JSON)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if a.verb == "status":
        r = status()
    elif a.verb == "scan":
        fams = [x.strip() for x in (a.family or "vdf,vrn").split(",") if x.strip()]
        r = scan(fams)
    elif a.verb == "cards":
        r = cards(a.cap)
    elif a.verb == "run":
        if not a.cap:
            print("  [絕] run 要給能力名:via-peis run <能力> [--params JSON]")
            return 1
        r = run_cap(a.cap, a.params)
    else:
        r = report()

    p = write_out(f"PEIS_{a.verb.upper()}_{ts}.json", r)
    write_out(f"PEIS_{a.verb.upper()}_latest.json", r)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        st = r.get("state", "?")
        print(f"[CGC_MDL158 v{VERSION}] {a.verb} · {st}")
        for k in ("files", "functions", "capabilities", "sealed", "pending", "collapsed", "near",
                  "source_tokens", "capsule_tokens", "saved_tokens", "saved_percent", "why",
                  "engine", "selftest_tail"):
            if k in r and r[k] not in (None, ""):
                print(f"  {k:>16} : {r[k]}")
        print(f"  存證 {p.name}")
    return {"OK": 0, "NODATA": 2, "ABSENT": 3}.get(r.get("state"), 1)


if __name__ == "__main__":
    sys.exit(main())
