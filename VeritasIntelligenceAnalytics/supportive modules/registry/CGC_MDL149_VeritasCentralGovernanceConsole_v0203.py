#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL149_VeritasCentralGovernanceConsole v0203 — 薄尾(v0202 一字不動):元件掃描遇到「同名兩份」登正本,VTK 的工具副本不當來源

操作員 2026-11-27 裁定「A」(VCGC-REQ279):同名兩份時登正本;VTK 自己有冊、自己發號(VTK-TOOL-####),它的副本不算 VCGC 的元件來源。
實錄:VTK 把十家工具的整條版本鏈複製進 VTK/<家>/。本體 v0142 的 _tail_files 對同名檔是「先掃到的贏」,而全樹排序 VTK/ 排最前面,
     於是 15 個家族在 VCGC 元件註冊冊的來源變成 VTK 副本(SDD 驗證 X-REG 紅;副本內容有些與正本不同,冊上記的就不是正本)。
本版只做一件事 —— 同名兩份改登正本:
  ① 正本在哪裡,讀 VTK 自己的登記冊(VTK_Register 尾版 · 只讀):每一家記著它是從哪個路徑複製來的。
     VTK/<家>/<檔> 的正本 = 那一家來源所在的夾 / <檔>。冊讀不到時退回「同名而且不在 VTK 底下的第一份」。
     正本不存在、被具名排除、或檔名不同(VTK 版本比較新 / 只有 VTK 有)→ 照舊登 VTK 那一份。
  ② 這個判法掛在「定義 _tail_files 的那一層」(用函式自己的全域找,不看名字在不在;教訓 LL-20261127-05)。
     v0167 的活元件快取另用一個快取名(舊快取是照舊判法算的,不能拿來用)。
  ③ v0195 起每一層都用子行程把舊動詞往下轉交,掛鉤帶不過去。所以舊動詞(會落到 v0194 以下同一行程那一疊的)由本版在自己的行程裡
     載入那一疊、掛好再跑;分流照 v0195–v0202 各層 main 的寫法逐條對(那幾版已發布,不會再變)。
     其餘動詞(overview · monitor status · agentos · graphify · help · 標準管理器動詞 · selftest)原樣轉交 v0202。
  ④ 經本檔取用前版公開名稱(registry_sync · live_components · _tail_files …)也先掛好再給。
  ⑤ synchronizer:同步台(v0198 / v0200)的每一步原本交給 v0197 去跑,會走到沒掛新判法的那一疊,
     books 步(sync-check)就會一直說註冊冊待同步。本版把「步驟交給誰跑」改成本檔,其餘照 v0200 的做法在同一行程叫同步台。
不寫任何檔;不出網;不碰 TA-Lib;不 import 他系統(VTK 的冊只當 JSON 讀)。
用法照舊:VIA_FROM_VCGC=YES python CGC_MDL149_VeritasCentralGovernanceConsole_v0203.py <動詞…> · --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = "v0203"
FAMILY = "CGC_MDL149_VeritasCentralGovernanceConsole"
TAG = FAMILY + " " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
OWN_FLAG = "VIA_FROM_VCGC"
COPY_ROOT = "VTK"                                   # 這個夾底下的同名檔是 VTK 系統的副本
COPY_REGISTER = "VTK_Register_v*.json"              # VTK 自己的登記冊(只讀)
LEGACY_TOP = 194                                    # 版號 ≤ 這個數的那一疊在同一行程裡往下叫;之上每層是子行程轉交
CACHE_NAME = "live_components_home"                 # v0167 活元件快取在本判法下用的名字
WRAPPER_VERBS = ("overview", "synchronizer", "agentos", "graphify", "help", "selftest", "--selftest")   # v0196–v0202 自己接的
WRAPPER_PAIRS = (("monitor", "status"),)            # v0197 只接這兩個字連在一起
SM_NATIVE_FALLBACK = ("help", "version", "health", "engines", "records", "peers", "conform", "selftest")   # v0195 讀不到時用
VERBS = ("--selftest",) + WRAPPER_VERBS[:5]         # 本版自己的動詞只有 --selftest;其餘是轉交(舊動詞清單見 help)
MARK = "_via_home_first"
_PRIOR = None
STATS = {"picked_home": 0, "calls": 0}


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path():
    cands = [p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)]
    return max(cands, key=_vnum) if cands else None


def _env() -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.setdefault(OWN_FLAG, "YES")                     # 只補本系統自己的入口旗標
    return env


def forward(args: list) -> int:
    """v0196–v0202 與標準管理器自己接的動詞:原樣轉交 v0202(子行程 · rc 不變)。"""
    pp = _prior_path()
    if pp is None:
        print("[%s] ABSENT · 要轉交的檔不在(動詞 %s)" % (TAG, args[:1]))
        return 3
    return subprocess.run([sys.executable, str(pp), *args], env=_env()).returncode


def _prior_module():
    global _PRIOR
    if _PRIOR is None:
        pp = _prior_path()
        if pp is None:
            raise AttributeError("前版不在")
        spec = importlib.util.spec_from_file_location(FAMILY + "_prior_for_" + Path(__file__).stem, pp)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _PRIOR = mod
    return _PRIOR


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。先把「同名兩份登正本」掛好再給,經本檔取 registry_sync 等拿到的就是新判法。"""
    if name.startswith("__"):
        raise AttributeError(name)
    ensure_home_first()
    return getattr(_prior_module(), name)


# ---------- ① 正本在哪裡 ----------
def copy_homes(via: Path) -> dict:
    """讀 VTK 登記冊尾版:{家: 正本所在的夾(VIA 相對路徑)}。同一家多列取最後一列(冊只增)。讀不到回空。"""
    hits = sorted((p for p in (Path(via) / COPY_ROOT).glob(COPY_REGISTER) if re.search(r"_v\d{4}$", p.stem)), key=lambda p: p.stem)
    if not hits:
        return {}
    try:
        rows = json.loads(hits[-1].read_text(encoding="utf-8")).get("rows") or []
    except (OSError, ValueError, AttributeError):
        return {}
    out = {}
    for r in rows if isinstance(rows, list) else []:
        src = ((r or {}).get("source") or {}).get("path") if isinstance(r, dict) else None
        fam = (r or {}).get("family") if isinstance(r, dict) else None
        if isinstance(fam, str) and isinstance(src, str) and "/" in src.replace("\\", "/"):
            out[fam] = src.replace("\\", "/").rsplit("/", 1)[0]
    return out


def _rel(body, q: Path) -> str:
    return q.relative_to(body.VIA).as_posix()


def is_copy(rel: str) -> bool:
    return rel.startswith(COPY_ROOT + "/")


def home_of(body, q: Path, homes: dict, exclude=None):
    """VTK 副本 q 的正本(Path)或 None。先照 VTK 登記冊;對不到就找同名而且不在 VTK 底下、沒被具名排除的第一份。"""
    rel = _rel(body, q)
    parts = rel.split("/")
    if len(parts) >= 3 and parts[1] in homes:
        cand = Path(body.VIA) / homes[parts[1]] / "/".join(parts[2:])
        crel = cand.relative_to(body.VIA).as_posix() if cand.is_file() else ""
        if crel and not is_copy(crel) and not body._excuse(crel, exclude):
            return cand
    for p in body._all_tail_py():
        if p.name == q.name:
            prel = _rel(body, p)
            if not is_copy(prel) and not body._excuse(prel, exclude):
                return p
    return None


def make_home_first(body, orig):
    """包住本體的 _tail_files:結果裡來源在 VTK 的家族,有同名正本就換成正本。其餘一律照原結果。"""
    def _tail_files(exclude=None):
        fams = orig(exclude)
        STATS["calls"] += 1
        copies = {s: q for s, q in fams.items() if is_copy(_rel(body, q))}
        if copies:
            homes = copy_homes(Path(body.VIA))
            for stem, q in copies.items():
                h = home_of(body, q, homes, exclude)
                if h is not None:
                    fams[stem] = h
                    STATS["picked_home"] += 1
        return fams
    setattr(_tail_files, MARK, True)
    _tail_files.__wrapped__ = orig
    _tail_files.__doc__ = orig.__doc__
    return _tail_files


# ---------- ② 掛在定義層 ----------
def _defined_in(mod, name: str) -> bool:
    fn = getattr(mod, "__dict__", {}).get(name)
    return callable(fn) and getattr(fn, "__globals__", None) is mod.__dict__


def _chain_modules() -> list:
    return [m for m in list(sys.modules.values()) if FAMILY in str(getattr(m, "__file__", "") or "") and m is not sys.modules.get(__name__)]


def ensure_home_first() -> dict:
    """把整疊載進來,在定義 _tail_files 的那一層掛上新判法;活元件快取換名。可重複呼叫(已掛的不再掛)。"""
    P = _prior_module()
    getattr(P, "_tail_files")                           # 逼前版鏈一路載到本體
    bodies = hooked = rewrapped = 0
    for m in _chain_modules():
        if not (_defined_in(m, "_all_tail_py") and callable(m.__dict__.get("_tail_files"))):
            continue                                    # 本體 = 自己定義全樹掃描的那一層
        bodies += 1
        cur = m.__dict__["_tail_files"]
        if getattr(cur, MARK, False):
            continue
        neu = make_home_first(m, cur)
        for other in _chain_modules():                  # 別層若把原函式另綁了一個名字,一起換(它們各讀各的全域)
            if other.__dict__.get("_tail_files") is cur:
                other.__dict__["_tail_files"] = neu
        hooked += 1
    old = {}
    for m in _chain_modules():
        w = m.__dict__.get("live_components")
        if callable(w) and getattr(w, "__wrapped__", None) is not None and not getattr(w, MARK, False):
            old[id(w)] = w
    for w in old.values():
        factory = getattr(w, "__globals__", {}).get("cached")
        if not callable(factory):
            continue
        neu = factory(w.__wrapped__, name=CACHE_NAME)
        setattr(neu, MARK, True)
        for m in _chain_modules():
            if m.__dict__.get("live_components") is w:
                m.__dict__["live_components"] = neu
                rewrapped += 1
    return {"bodies": bodies, "hooked": hooked, "rewrapped": rewrapped}


# ---------- ③ 分流 ----------
def sm_native() -> tuple:
    try:
        v = getattr(_prior_module(), "SM_NATIVE")
        return tuple(v) if v else SM_NATIVE_FALLBACK
    except Exception:  # noqa: BLE001  前版載不到就用內建那一組(分流不能因此壞掉)
        return SM_NATIVE_FALLBACK


def is_legacy(args: list, native=None) -> bool:
    """這組參數會不會落到 v0194 以下那一疊。逐條對 v0202 → v0195 各層 main 的寫法。"""
    if not args:
        return False                                    # 空參數 = help(各層接)
    verb = args[0]
    if verb in WRAPPER_VERBS:
        return False
    if any(tuple(args[:len(p)]) == p for p in WRAPPER_PAIRS):
        return False
    if verb in (native if native is not None else sm_native()) and "--legacy" not in args:
        return False                                    # v0195 標準管理器自己接
    return True


def legacy_module():
    """同一行程那一疊最上面那一版(版號 = LEGACY_TOP)已載入的模組;沒有回 None。"""
    want = None
    for p in HERE.glob(FAMILY + "_v*.py"):
        if _vnum(p) == LEGACY_TOP:
            want = p.resolve()
    if want is None:
        return None
    for m in _chain_modules():
        if os.path.realpath(str(m.__file__)) == os.path.realpath(str(want)) and callable(m.__dict__.get("main")):
            return m
    return None


def legacy_main(args: list) -> int:
    """在本行程把舊動詞跑完:載入那一疊 → 掛好 → 叫它的 main。參數 / 入口旗標 / rc 與子行程轉交時相同(--legacy 照 v0195 拿掉)。"""
    st = ensure_home_first()
    mod = legacy_module()
    if mod is None or st["bodies"] < 1:
        print("[%s] 找不到同一行程那一疊(v%04d)或掃描本體,改走原本的子行程轉交 · 同名兩份的判法這一次沒有生效" % (TAG, LEGACY_TOP), file=sys.stderr)
        return forward(args)
    os.environ.setdefault(OWN_FLAG, "YES")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True
    clean = [a for a in args if a != "--legacy"]
    sys.argv = [sys.argv[0]] + clean
    try:
        rc = mod.main(clean)
    except SystemExit as e:
        rc = e.code
    if rc is None:
        return 0
    if isinstance(rc, int):
        return rc
    print(rc, file=sys.stderr)
    return 1


def synchronizer(args: list) -> int:
    """同步台照 v0200 的做法在本行程叫;只把步驟的執行檔從 v0197 換成本檔(步驟裡的舊動詞才會帶新判法)。找不到同步台就原樣轉交。"""
    try:
        P = _prior_module()
        owner = P.sync_owner()
        cfg = dict(P.sync_config(owner), prior=Path(__file__).resolve()) if owner is not None else None
    except AttributeError:
        owner = cfg = None
    if owner is None or cfg is None:
        return forward(["synchronizer", *args])
    os.environ.setdefault(OWN_FLAG, "YES")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    return owner.sy_command(cfg, args)


def help_extra() -> None:
    print("  [%s] 元件掃描:同名兩份登正本(VTK 的工具副本不當來源;正本位置讀 VTK_Register 尾版)。" % VERSION)


# ---------- 自測 ----------
def selftest() -> int:
    import tempfile
    import types
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(暫存樹 · 不寫真樹 · 零網路)" % TAG, flush=True)
    native = SM_NATIVE_FALLBACK
    leg = [["status"], ["registry-sync", "--apply"], ["run", "CGC_MDL237_NumberingSystem", "audit"], ["handoff", "check"], ["test", "--quick"],
           ["token"], ["functions"], ["ssot", "panorama"], ["sdd", "check"], ["monitor"], ["monitor", "start"], ["health", "--legacy"], ["zzz"]]
    not_leg = [[], ["help"], ["overview"], ["overview", "--open"], ["synchronizer", "plan"], ["agentos", "x"], ["graphify"], ["monitor", "status"],
               ["selftest"], ["--selftest"], ["selftest", "--legacy"], ["health"], ["version"], ["conform"]]
    chk("T1 分流:舊動詞 %d 組落到同一行程那一疊 · 各層自己接的 %d 組照舊轉交" % (len(leg), len(not_leg)),
        all(is_legacy(a, native) for a in leg) and not any(is_legacy(a, native) for a in not_leg),
        ([a for a in leg if not is_legacy(a, native)], [a for a in not_leg if is_legacy(a, native)]))
    wr = sorted(p for p in HERE.glob(FAMILY + "_v*.py") if LEGACY_TOP < _vnum(p) < _vnum(__file__))
    srcs = {p.name: p.read_text(encoding="utf-8", errors="replace") for p in wr}
    top = [p for p in HERE.glob(FAMILY + "_v*.py") if _vnum(p) == LEGACY_TOP]
    top_src = top[0].read_text(encoding="utf-8", errors="replace") if top else ""
    chk("T2 分流的前提還成立:v%04d 之上 %d 版每一版都用子行程轉交 · v%04d 在同一行程叫前版" % (LEGACY_TOP, len(wr), LEGACY_TOP),
        len(wr) >= 8 and all("subprocess.run([sys.executable" in s for s in srcs.values()) and "load_prior().main(args)" in top_src,
        [n for n, s in srcs.items() if "subprocess.run([sys.executable" not in s])
    with tempfile.TemporaryDirectory(prefix="cgc149_203_") as td:
        fx = Path(td) / "VeritasIntelligenceAnalytics"
        files = {
            "VTK/token/CGC_MDL900_Tool_v0101.py": "X = 'vtk'\n",
            "supportive modules/registry/CGC_MDL900_Tool_v0101.py": "X = 'home'\n",
            "VTK/accel/Accel_v0100.py": "X = 'vtk'\n",
            "functional modules/VRN/intake/pack/Accel_v0100.py": "X = 'intake copy'\n",
            "supportive modules/Accel_v0100.py": "X = 'home'\n",
            "VTK/VTK_Manager_v0100.py": "X = 'vtk only'\n",
            "VTK/ocr/Ocr_v0102.py": "X = 'vtk newer'\n",
            "supportive modules/registry/Ocr_v0101.py": "X = 'home older'\n",
            "VTK/layout/sub/Part_v0100.py": "X = 'vtk'\n",
            "supportive modules/rules/sub/Part_v0100.py": "X = 'home'\n",
            "VTK/frame/Frame_v0100.py": "X = 'vtk'\n",
            "supportive modules/references/Frame_v0100.py": "X = 'excluded home'\n",
            "VTK/nlp/Nlp_v0100.py": "X = 'vtk'\n",
            "functional modules/VDF/Nlp_v0100.py": "X = 'not in register'\n",
        }
        for rel, text in files.items():
            p = fx / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        reg = {"rows": [
            {"family": "token", "source": {"path": "supportive modules/old_place/CGC_MDL900_Tool_v0100.py"}},
            {"family": "token", "source": {"path": "supportive modules/registry/CGC_MDL900_Tool_v0101.py"}},
            {"family": "accel", "source": {"path": "supportive modules/Accel_v0100.py"}},
            {"family": "layout", "source": {"path": "supportive modules/rules/Hub_v0100.py"}},
            {"family": "frame", "source": {"path": "supportive modules/references/Frame_v0100.py"}},
            {"family": "ocr", "source": {"path": "supportive modules/registry/Ocr_v0101.py"}},
            "壞列", {"family": 3}]}
        (fx / "VTK" / "VTK_Register_v0100.json").write_text(json.dumps(reg, ensure_ascii=False), encoding="utf-8")
        tail_re = re.compile(r"_v\d{4}\.py$")

        def fake_body():
            b = types.SimpleNamespace(VIA=fx)
            b._all_tail_py = lambda: sorted(fx.rglob("*_v????.py"))
            b._excuse = lambda rel, exclude=None: "收容" if "references/" in rel else ""

            def first_wins(exclude=None):
                fams = {}
                for q in b._all_tail_py():
                    rel = q.relative_to(fx).as_posix()
                    if b._excuse(rel, exclude) or not tail_re.search(q.name):
                        continue
                    stem = tail_re.sub("", q.name)
                    if stem not in fams or q.name > fams[stem].name:
                        fams[stem] = q
                return fams
            b._tail_files = first_wins
            return b
        b = fake_body()
        before = {s: q.relative_to(fx).as_posix() for s, q in b._tail_files().items()}
        after = {s: q.relative_to(fx).as_posix() for s, q in make_home_first(b, b._tail_files)().items()}
        chk("T3 對照:原判法 6 個同名家族全登到 VTK 那一份(先掃到的贏)",
            all(before[s].startswith("VTK/") for s in ("CGC_MDL900_Tool", "Accel", "Part", "Frame", "Nlp", "Ocr", "VTK_Manager")), before)
        chk("T4 同名兩份 → 登 VTK 登記冊寫的正本(同一家多列取最後一列;子夾裡的檔照相對位置找)",
            after["CGC_MDL900_Tool"] == "supportive modules/registry/CGC_MDL900_Tool_v0101.py" and after["Part"] == "supportive modules/rules/sub/Part_v0100.py", after)
        chk("T5 有別的同名副本排在前面時,登的是登記冊寫的那一份,不是先掃到的收件副本", after["Accel"] == "supportive modules/Accel_v0100.py", after["Accel"])
        chk("T6 只有 VTK 有的 · VTK 版本比正本新的 · 正本被具名排除的 → 照舊登 VTK",
            after["VTK_Manager"] == "VTK/VTK_Manager_v0100.py" and after["Ocr"] == "VTK/ocr/Ocr_v0102.py" and after["Frame"] == "VTK/frame/Frame_v0100.py", after)
        chk("T7 登記冊沒有這一家 → 退回同名而且不在 VTK 底下的第一份", after["Nlp"] == "functional modules/VDF/Nlp_v0100.py", after["Nlp"])
        (fx / "VTK" / "VTK_Register_v0100.json").write_text("{壞掉", encoding="utf-8")
        broke = {s: q.relative_to(fx).as_posix() for s, q in make_home_first(b, b._tail_files)().items()}
        chk("T8 登記冊壞掉也不炸:全部退回同名第一份(Accel 這時拿到的是排前面的那一份,照實)",
            copy_homes(fx) == {} and broke["CGC_MDL900_Tool"].startswith("supportive modules/") and broke["Accel"] == "functional modules/VRN/intake/pack/Accel_v0100.py", broke)
        # 真正的本體:把它的 VIA 指到暫存樹,從本檔的轉接口打進去
        st = ensure_home_first()
        body = [m for m in _chain_modules() if _defined_in(m, "_all_tail_py") and getattr(m.__dict__.get("_tail_files"), MARK, False)]
        chk("T9 掛在定義層:本體找到 1 層 · 掛的是函式自己的全域那一層 · 再叫一次不重複掛",
            len(body) == 1 and st["bodies"] == 1 and ensure_home_first()["hooked"] == 0
            and not getattr(body[0].__dict__["_tail_files"].__wrapped__, MARK, False), (st, len(body)))
        if body:
            B = body[0]
            keep_via, keep_cache = B.VIA, dict(B._TAIL_CACHE)
            (fx / "VTK" / "VTK_Register_v0100.json").write_text(json.dumps(reg, ensure_ascii=False), encoding="utf-8")
            try:
                B.VIA = fx
                B._TAIL_CACHE.clear()
                real = {s: q.relative_to(fx).as_posix() for s, q in sys.modules[__name__].__getattr__("_tail_files")().items()}
                B._TAIL_CACHE.clear()
                real_orig = {s: q.relative_to(fx).as_posix() for s, q in B.__dict__["_tail_files"].__wrapped__().items()}
            finally:
                B.VIA = keep_via
                B._TAIL_CACHE.clear()
                B._TAIL_CACHE.update(keep_cache)
            chk("T10 走真正的本體(v0142 的掃描 + 具名排除):經本檔取到的 _tail_files 登正本;同一個本體的原函式登 VTK(反控)",
                real.get("CGC_MDL900_Tool") == "supportive modules/registry/CGC_MDL900_Tool_v0101.py" and real.get("Accel") == "supportive modules/Accel_v0100.py"
                and real.get("VTK_Manager") == "VTK/VTK_Manager_v0100.py" and real.get("Frame") == "VTK/frame/Frame_v0100.py"
                and real_orig.get("CGC_MDL900_Tool", "").startswith("VTK/") and real_orig.get("Accel", "").startswith("VTK/"), (real, real_orig))
        else:
            chk("T10 走真正的本體", False, "本體沒找到")
    lc = [m.__dict__.get("live_components") for m in _chain_modules() if callable(m.__dict__.get("live_components"))]
    stale = [w for w in lc if getattr(w, "__wrapped__", None) is not None and not getattr(w, MARK, False)]
    chk("T11 活元件快取:鏈上帶快取的 live_components 全換成本判法的快取名(舊判法算的快取不會被拿來用)", lc and not stale, len(stale))
    seen = []
    keep = (globals()["forward"], globals()["legacy_main"])
    globals()["forward"] = lambda a: seen.append(("forward", list(a))) or 11
    globals()["legacy_main"] = lambda a: seen.append(("legacy", list(a))) or 22
    keep_sync = globals()["synchronizer"]
    globals()["synchronizer"] = lambda a: seen.append(("sync", list(a))) or 33
    try:
        r1, r2, r3, r4 = main(["overview"]), main(["registry-sync"]), main(["health", "--legacy"]), main(["synchronizer", "check"])
    finally:
        globals()["forward"], globals()["legacy_main"] = keep
        globals()["synchronizer"] = keep_sync
    chk("T12 main:overview 轉交 v0202 · registry-sync 與 health --legacy 走同一行程那一疊 · synchronizer 由本檔接 · rc 原樣帶回",
        (r1, r2, r3, r4) == (11, 22, 22, 33) and seen == [("forward", ["overview"]), ("legacy", ["registry-sync"]), ("legacy", ["health", "--legacy"]), ("sync", ["check"])],
        (seen, r1, r2, r3, r4))
    took = []
    fake_owner = types.SimpleNamespace(sy_command=lambda cfg, a: took.append((dict(cfg), list(a))) or 5)
    fake_p = types.SimpleNamespace(sync_owner=lambda: fake_owner, sync_config=lambda o: {"prior": Path("old_prior.py"), "steps": ["books"], "version": "v0203"})
    keep_pm, keep_fw = globals()["_prior_module"], globals()["forward"]
    globals()["_prior_module"] = lambda: fake_p
    try:
        rc_sync = synchronizer(["run", "--steps", "books"])
        fake_p.sync_owner = lambda: None
        globals()["forward"] = lambda a: took.append(("forward", list(a))) or 6
        rc_none = synchronizer(["check"])
    finally:
        globals()["_prior_module"], globals()["forward"] = keep_pm, keep_fw
    chk("T12b synchronizer:步驟的執行檔換成本檔(其餘設定照舊 · rc 帶回);找不到同步台就原樣轉交",
        rc_sync == 5 and took[0][0]["prior"] == Path(__file__).resolve() and took[0][0]["steps"] == ["books"] and took[0][1] == ["run", "--steps", "books"]
        and rc_none == 6 and took[1] == ("forward", ["synchronizer", "check"]), (took, rc_sync, rc_none))
    got = []
    stub = types.SimpleNamespace(main=lambda a: got.append((list(a), list(sys.argv[1:]))) or None, __file__="x")
    keep2, keep_argv = globals()["legacy_module"], list(sys.argv)
    globals()["legacy_module"] = lambda: stub
    try:
        rc_none = legacy_main(["status", "--legacy", "--json"])
        stub.main = lambda a: (_ for _ in ()).throw(SystemExit(3))
        rc_exit = legacy_main(["status"])
    finally:
        globals()["legacy_module"] = keep2
        sys.argv = keep_argv
    chk("T13 legacy_main:--legacy 拿掉 · sys.argv 跟著參數 · 回 None 算 0 · SystemExit(3) 帶回 3",
        got == [(["status", "--json"], ["status", "--json"])] and rc_none == 0 and rc_exit == 3, (got, rc_none, rc_exit))
    P = _prior_module()
    lost = [n for n in dir(P) if not n.startswith("_") and callable(getattr(P, n)) and not hasattr(sys.modules[__name__], n)]
    chk("T14 前版公開名稱都還拿得到(經本檔轉接;registry_sync · live_components 在內)",
        not lost and callable(sys.modules[__name__].registry_sync) and callable(sys.modules[__name__].live_components), lost[:6])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T15 第 3 行加速器標記且載入生效(VIA_ACCEL 非空)· 零 TA-Lib · 不 import 他系統 · 本檔沒有寫檔的呼叫",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"^\s*(import|from)\s+(VDF|VRN|VQG|VAP|VTK)", src, re.M)
        and len(re.findall(r"\.write_text\(|\.write_bytes\(|os\.replace\(", src.split("def selftest()")[0])) == 0,
        "VIA_ACCEL %s" % (VIA_ACCEL is not None))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("--selftest", "selftest") and "--legacy" not in args:
        return selftest()
    if args[:1] == ["synchronizer"]:
        return synchronizer(args[1:])
    if is_legacy(args):
        return legacy_main(args)
    rc = forward(args)
    if not args or args[0] == "help":
        help_extra()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
