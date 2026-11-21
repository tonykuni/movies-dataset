#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN-2 SystemManager v0279 — 薄尾(v0278 一字不動):VRN 自己發號、自己定案,不再等 VCGC 核號

操作員 2026-11-21 裁定:「同意 VRN 自己發號不用等 VCGC 核號」(前一則:「他們全都是獨立的系統,他們當然可以擁有自己的一套資料」)。
CLAUDE.md 待裁定第 3 項(SSOT 同一 × 互不干涉)的 VRN 編號部分就此定案:VRN 的引擎 VRN-E · 冊 VRN-B · 參數 VRN-P · 元件 VRN2-<類> 都由
VRN 管理器自己發、自己定案;VCGC 的中央編號邊界閘本來就擋 VCGC 替 VRN 正本發號(2026-11-20 實錄:VRN_ParamControl_SSOT 被擋)。
本版只換三個函式(鏈上「自己定義」這三個函式的每一版 —— 實跑載入的是 v0229 / v0231,另有 v0240 —— 用 AST 取該版原始碼、逐字替換、
在該版自己的命名空間重新編譯;前版檔一字不動;鏈是要用才載,所以掛在載入那一刻換):
  ① asset_register:冊 / 參數 / 引擎的狀態 = 「已確認(VRN 自發)」(原本 = VCGC 核發才轉已確認、否則「暫編 · 待 VCGC 核號」);
     contract/VRN_NUMBER_REQUEST_latest.json 的 pending 永遠空、規則改寫成 VRN 自己定案。
  ② register(VRN-2 元件登記冊):新登與復活都直接「已確認(VRN 自發)」;舊的「暫編」列轉成已確認(算一次內容變 → 只出一版)。
  ③ asset_lines:回報行不再寫「待 VCGC 核號 N」,改寫「VRN 自發號 · 待核 0」。
號碼本身、發號規則(鍵不變號不變 · 只增不減 · 內容變才出新版)全部照舊。其餘動詞照 v0278。
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

import ast
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "v0279"
DISPLAY_NAME = "VRN-2 SystemManager"
FAMILY = "VRN_SystemManager"
BODY_FILE = "VRN_SystemManager_v0240.py"            # 自測用的本體(實跑時鏈上真正載入的是 v0229 / v0231 —— 兩版各自定義這三個函式;一律逐版換)
_FAMILY_RX = re.compile(r"^VRN_SystemManager_v\d{4}\.py$")
SELF_STATUS = "已確認(VRN 自發)"
OLD_PENDING = "暫編 · 待 VCGC 核號"
RULING = "操作員 2026-11-21 裁定:VRN 自己發號、自己定案,不送 VCGC 核號"


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("vrn2_manager_prior_for_" + TAG, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _defines_here(m) -> bool:
    g = vars(m)
    fn = g.get("asset_register")
    f = getattr(m, "__file__", None) or ""
    return bool(g.get("_via_v0279_installed") or (callable(fn) and getattr(fn, "__code__", None) is not None
                and Path(fn.__code__.co_filename).name == Path(f).name and _FAMILY_RX.match(Path(f).name)))


def body_modules() -> list:
    """前版鏈載入後,sys.modules 裡「自己定義」asset_register 的每一版(不是從前版複製來的名稱)。"""
    out = []
    for m in list(sys.modules.values()):
        if hasattr(m, "__dict__") and "asset_register" in vars(m) and m not in out and _defines_here(m):
            out.append(m)
    return out


def _sources(path: Path) -> dict:
    src = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(src)
    want = {"asset_register", "asset_lines", "register"}
    return {n.name: ast.get_source_segment(src, n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in want}


def transformed(path: Path) -> dict:
    """三個函式的新原始碼(逐字替換;每一處都要真的命中,命中數不對就丟例外 —— 本體被改過就不要硬裝)。"""
    s = _sources(path)
    out = {}
    a, n = re.subn(r'"已確認\(VCGC\)" if grant\.get\([^)]*\) == \S+ else "暫編 · 待 VCGC 核號"', "SELF_STATUS_V0279", s["asset_register"])
    assert n == 3, "asset_register 狀態式命中 %d(應 3)" % n
    a, n = re.subn(r"暫編待 VCGC 核號", "VRN 自己發號定案(不送 VCGC 核號)", a)
    assert n >= 1, "asset_register 規則字串沒命中"
    a, n = re.subn(r"VCGC 偵測三系統無衝突後寫 VCGC_NUMBER_GRANT_latest\.json \{grants:\{key:no\}\} · VRN 讀到才轉已確認", RULING + " · pending 永遠空", a)
    assert n == 1, "核號請求規則字串命中 %d(應 1)" % n
    out["asset_register"] = a
    b, n = re.subn(r"待 VCGC 核號 %d\(contract/VRN_NUMBER_REQUEST_latest\.json\)", "VRN 自發號 · 待核 %d(" + RULING + ")", s["asset_lines"])
    assert n == 1, "asset_lines 命中 %d(應 1)" % n
    out["asset_lines"] = b
    r = s["register"]
    r, n1 = re.subn(r'"status": "暫編 · 待 VCGC 核號"', '"status": SELF_STATUS_V0279', r)
    r, n2 = re.subn(r'old\["status"\] = "暫編 · 待 VCGC 核號"', 'old["status"] = SELF_STATUS_V0279', r)
    r, n3 = re.subn(r'(\n(\s+)if old\.get\("status", ""\)\.startswith\("退役"\):)',
                    r'\n\2if old.get("status", "").startswith("暫編"):\n\2    old["status"] = SELF_STATUS_V0279\n\2    changed += 1\1', r, count=1)
    r, n4 = re.subn(r"暫編待 VCGC 核號", "VRN 自己發號定案(不送 VCGC 核號)", r)
    assert (n1, n2, n3) == (1, 1, 1) and n4 >= 1, "register 命中 %s" % ((n1, n2, n3, n4),)
    out["register"] = r
    return out


_ORIG: dict = {}
_NEW: dict = {}
INSTALLED: list = []
SKIPPED: dict = {}


def install() -> list:
    for m in body_modules():
        g = vars(m)
        if g.get("_via_v0279_installed"):
            continue
        f = Path(m.__file__)
        try:
            if f.name not in _NEW:
                _NEW[f.name] = {name: compile(code, "%s::%s(%s 改)" % (f.name, name, TAG), "exec") for name, code in transformed(f).items()}
        except (AssertionError, KeyError, SyntaxError) as exc:
            SKIPPED[f.name] = str(exc)[:160]                 # 該版字樣對不上就不硬裝,照實記
            continue
        _ORIG[id(m)] = {k: g[k] for k in ("asset_register", "asset_lines", "register") if k in g}
        g["SELF_STATUS_V0279"] = SELF_STATUS
        for code in _NEW[f.name].values():
            exec(code, g)                                # 在該版自己的命名空間定義:helper(_resolve · _spec_of · _BOOK_RX …)照用
        g["_via_v0279_installed"] = True
        INSTALLED.append("%s(%s)" % (m.__name__, f.name))
    return INSTALLED


def uninstall() -> None:
    for m in body_modules():
        g = vars(m)
        if g.get("_via_v0279_installed") and id(m) in _ORIG:
            g.update(_ORIG[id(m)])
            g["_via_v0279_installed"] = False


_ORIG_EXEC_MODULE = None


def _hook_body_loads(on: bool = True) -> None:
    """前版鏈是「要用才載」(v0270 的 extract 宿主、v0269 的 _sm_prior_module):本體 v0240 可能在本檔匯入之後才載進來。
    只在本行程:包一層 SourceFileLoader.exec_module,載完的模組是本體檔就立刻換上本版三個函式;off 還原。"""
    global _ORIG_EXEC_MODULE
    import importlib.machinery as _mach
    if on and _ORIG_EXEC_MODULE is None:
        _ORIG_EXEC_MODULE = _mach.SourceFileLoader.exec_module

        def _exec_module(self, module):
            _ORIG_EXEC_MODULE(self, module)
            if _FAMILY_RX.match(Path(getattr(module, "__file__", "") or "").name):
                install()
        _mach.SourceFileLoader.exec_module = _exec_module
    elif not on and _ORIG_EXEC_MODULE is not None:
        _mach.SourceFileLoader.exec_module = _ORIG_EXEC_MODULE
        _ORIG_EXEC_MODULE = None


_hook_body_loads(True)
install()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    import json
    import tempfile
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    print(f"=== VRN_SystemManager {TAG} 薄尾自測(VRN 自己發號定案 · 不等 VCGC 核號)===", flush=True)
    if not body_modules():                                # 前版鏈要用才載:照實載一份本體(經上面的鉤子自動換上)
        _sp = importlib.util.spec_from_file_location("vrn_body_for_selftest_" + TAG, HERE / BODY_FILE)
        _bm = importlib.util.module_from_spec(_sp)
        sys.modules[_sp.name] = _bm
        _sp.loader.exec_module(_bm)
    bm = body_modules()
    ck("① 鏈上自己定義三函式的每一版都換成本版(在該版命名空間)", bm and all(vars(m).get("_via_v0279_installed") and vars(m)["asset_register"].__code__.co_filename.endswith("(%s 改)" % TAG) for m in bm), ([m.__name__ for m in bm], SKIPPED))
    defs = [p for p in sorted(HERE.glob(FAMILY + "_v*.py")) if _vnum(p) < _vnum(__file__) and "def asset_register(" in p.read_text(encoding="utf-8", errors="replace")]
    tr = {}
    for p in defs:
        try:
            for nm, code in transformed(p).items():
                compile(code, p.name, "exec")
            tr[p.name] = "OK"
        except Exception as exc:  # noqa: BLE001
            tr[p.name] = str(exc)[:80]
    ck("①b 每一個定義三函式的前版(v0229 · v0231 · v0240 …)替換都命中、編得過", defs and all(v == "OK" for v in tr.values()), tr)
    B = [m for m in bm if Path(m.__file__).name == BODY_FILE][0]
    with tempfile.TemporaryDirectory(prefix="vrn_v0279_") as td:
        home = Path(td) / "VRN"
        (home / "SSOT").mkdir(parents=True)
        (home / "registry").mkdir()
        (home / "SSOT" / "VRN_Demo_SSOT_v0100.json").write_text('{"a": 1}', encoding="utf-8")
        (home / "registry" / "VRN_Asset_Register_v0100.json").write_text(json.dumps({"schema": "VIA.VRN.AssetRegister.v1", "engines": {}, "books": {
            "VRN_Demo_SSOT.json": {"no": "VRN-B-0007", "status": OLD_PENDING, "first_seen": "2026-11-01"}}, "params": {}, "specs": {}, "version": "v0100"}, ensure_ascii=False), encoding="utf-8")
        o1 = B.asset_register(home)
        regs = sorted((home / "registry").glob("VRN_Asset_Register_v*.json"), key=_vnum)
        d = json.loads(regs[-1].read_text(encoding="utf-8"))
        req = json.loads((home / "contract" / "VRN_NUMBER_REQUEST_latest.json").read_text(encoding="utf-8"))
        bs = d["books"].get("VRN_Demo_SSOT.json", {})
        allst = [v.get("status") for sec in ("books", "params", "engines") for v in d[sec].values()]
        ck("② 資產登記:舊「暫編 · 待 VCGC 核號」→ 已確認(VRN 自發)· 號不變(VRN-B-0007)· 全部狀態都是已確認 · 規則寫 VRN 自己定案",
           o1["changed"] and bs.get("no") == "VRN-B-0007" and bs.get("status") == SELF_STATUS and allst and all(x == SELF_STATUS for x in allst) and "VRN 自己發號" in d.get("rule", ""), (o1, bs, set(allst)))
        ck("③ 核號請求 contract/VRN_NUMBER_REQUEST_latest.json:pending 空 · 規則 = VRN 自己定案", req.get("pending") == {} and "VRN 自己發號" in req.get("rule", ""), req)
        o2 = B.asset_register(home)
        ck("④ 再跑一次:無變更、不出新版(不會每輪換版)", not o2["changed"] and len(sorted((home / "registry").glob("VRN_Asset_Register_v*.json"))) == len(regs), o2)
        lines = B.asset_lines(o2)
        ck("⑤ 回報行:不再寫「待 VCGC 核號」· 寫 VRN 自發號 · 待核 0", "待 VCGC 核號" not in lines[0] and "VRN 自發號 · 待核 0" in lines[0], lines[0])
        tg = Path(td) / "R"
        (tg / "registry").mkdir(parents=True)
        (tg / "demo_tool_v0100.py").write_text("def f():\n    return 1\n", encoding="utf-8")
        B.register(home=tg, rd=tg / "registry", rep=tg)
        f1 = sorted((tg / "registry").glob("VRN2_Component_Register_v*.json"))
        e1 = json.loads(f1[-1].read_text(encoding="utf-8"))
        live = [e["status"] for e in e1["entries"].values() if not e["status"].startswith("退役")]
        k0 = next(iter(e1["entries"]))
        e1["entries"][k0]["status"] = OLD_PENDING
        f1[-1].write_text(json.dumps(e1, ensure_ascii=False), encoding="utf-8")
        B.register(home=tg, rd=tg / "registry", rep=tg)
        f2 = sorted((tg / "registry").glob("VRN2_Component_Register_v*.json"))
        e2 = json.loads(f2[-1].read_text(encoding="utf-8"))
        B.register(home=tg, rd=tg / "registry", rep=tg)
        f3 = sorted((tg / "registry").glob("VRN2_Component_Register_v*.json"))
        rq2 = json.loads((tg / "contract" / "VRN2_NUMBER_REQUEST_latest.json").read_text(encoding="utf-8"))
        ck("⑥ 元件登記:新登直接已確認(VRN 自發)· 舊「暫編」列轉已確認且號不變 · 之後無變更不出新版 · 請號清單空",
           live and all(x == SELF_STATUS for x in live) and e2["entries"][k0]["status"] == SELF_STATUS and e2["entries"][k0]["no"] == e1["entries"][k0]["no"]
           and len(f2) == len(f1) + 1 and len(f3) == len(f2) and rq2.get("pending") == [] and "VRN 自己發號" in e2.get("rule", ""), (live[:3], len(f1), len(f2), len(f3), rq2))
    src = Path(__file__).read_text(encoding="utf-8")
    ck("⑦ 加速器橋真的匯入 · 不碰 TA-Lib · 不設同意閘 · 不含本機路徑 · 不改任何前版檔",
       "import VIA_SuperAccel_Module as VIA_ACCEL" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
       and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src) and ("C:" + "\\Users") not in src and "write_text(" not in src.split("def selftest")[0])
    uninstall()
    _hook_body_loads(False)
    try:
        rc = PRIOR.main(["--selftest"])
    finally:
        _hook_body_loads(True)
        install()
    ck(f"⑧ 前版 {PRIOR_PATH.stem} 自測照過(跑前拆本版替換,跑完裝回)", rc == 0, f"rc {rc}")
    good = all(ok)
    print(f"[計] VRN_SystemManager {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if good else 'FAIL'}", flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
