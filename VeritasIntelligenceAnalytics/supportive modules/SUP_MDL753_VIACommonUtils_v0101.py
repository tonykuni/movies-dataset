#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
SUP_MDL753_VIACommonUtils v0100 — VRN 共用小工具正典(批594)

批589 量到 VRN 是三族裡整合債最重的(890 類 / 2557 跨家族)。批594 取前幾大,
照 L75 先按行為分群(AST 正規化比骨架,不比長相):

  VRN 尾版 170 支 · 定義 **68 處** · 行為群 **18 群**(全部在模組層)

  `_cel_submit` 17 處 / 4 群   Celeritas 平行提交 + 退回直呼
  `_si`         17 處 / 4 群   安全 import(回模組或 None)
  `_hash8`      14 處 / 2 群   八碼雜湊(有 xxhash 就用,沒有就 sha256)
  `_jwrite`     14 處 / 3 群   寫 JSON —— **直接接批592 的 SUP_MDL752 正典**,不另造一支
  `_argval`      3 處 / 2 群   從 argv 取旗標值
  `_num`         2 處 / 2 群   逗號千分位字串 → float / None

分群之後兩件事值得先講:

**一、`_cel_submit` 的差別在「第二層退路」。**
6+2 處只試 `_CEL._LazyPool.submit`,5+4 處會再試 `_CEL.submit`。
兩者最後都退回 `fn(*args, **kw)`,所以**只有在「有 submit 但沒有 _LazyPool」時才分得出來**。
正典把它變成明示選項 `submit_fallback`,不擅自統一。

**二、`_si` 有一群用 bare `except:`。**
`except:` 連 `KeyboardInterrupt` / `SystemExit` 都吞。import 一個會 `sys.exit()` 的模組時,
這一群會把它吃掉當成「沒有這個模組」。**那是潛在缺陷,不是風格差異。**
正典提供 `catch_all=` 讓它等價遷移,**預設是 `except Exception`**;
要不要把那 7 處改成預設值,是操作員的裁定(LL90),本檔不代改。

律:零網路;零安裝;正本零觸碰;`--selftest` 零網路且只在 tempfile 沙盒寫。
用法:python3 SUP_MDL753_VIACommonUtils_v0100.py --selftest
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

import hashlib
import importlib
import math
import sys
from pathlib import Path

VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]

#: 名字像但**不是同一件事**,不得併(照 SUP_MDL752 的慣例留名)。
NOT_SAME_THING = {
    "VRN.*.close(self)": "是類別的 property/method(取收盤價),不是檔案關閉,也不是共用小工具",
    "VRN.*.export_csv(self, out_dir)": "是類別方法,各自有自己的欄位與表頭,不是同一個 CSV 寫法",
    "VRN.*._cel_submit(fn, *args, **kw)":
        "**不得做成模組層綁定。**它讀的 `_CEL` / `_CEL_OK` 在檔頭是 `None` / `False`,"
        "真正的值是開機函式用 `global _CEL, _CEL_OK` **事後**填進去的——"
        "原版是**呼叫時**才讀,模組層綁定會在 **import 當下**把 `False` 凍住,"
        "開機之後永遠走不到 Celeritas 的池子。這跟批593 的可變預設值是同一族:"
        "**早綁了一個本來要晚讀的東西**。17 處,具名不遷。",
    "VRN_*.._argval(args, flag) 的有狀態那一版":
        "它讀寫模組層的 `_FLAG_OK_BARE` / `_BARE_FLAG_SEEN`,行為綁在那一支的狀態上;"
        "搬出來就不是同一件事。1 處,具名不遷。",
}


# ────────────────────────── 安全 import ──────────────────────────
def safe_import(name: str, *, catch_all: bool = False):
    """import 一個模組,失敗回 None。

    catch_all  True 用 bare `except:`(連 KeyboardInterrupt / SystemExit 都吞)。
               活樹有 7 處是這一種——**那是潛在缺陷**:import 一個會 `sys.exit()` 的模組時,
               它會被吃掉當成「沒有這個模組」。留這個選項只為**等價遷移**,
               預設是 `except Exception`;要不要改回預設值是操作員的裁定(LL90)。
    """
    if catch_all:
        try:
            return importlib.import_module(name)
        except BaseException:      # noqa: BLE001 — 就是要等價於活樹那 7 處的 bare except
            return None
    try:
        return importlib.import_module(name)
    except Exception:
        return None


# ────────────────────────── Celeritas 平行提交 ──────────────────────────
_CEL_CACHE: list = []


def _celeritas():
    """惰性載入正典 Celeritas(`supportive modules/VeritasCeleritas.py`);缺席回 None。"""
    if _CEL_CACHE:
        return _CEL_CACHE[0]
    mod = None
    p = Path(__file__).resolve()
    while p.parent != p:
        hits = sorted((p / "supportive modules").glob("VeritasCeleritas*.py"))
        if hits:
            import importlib.util as ilu
            try:
                spec = ilu.spec_from_file_location("VIA_CELERITAS", hits[-1])
                mod = ilu.module_from_spec(spec)
                spec.loader.exec_module(mod)
            except Exception:
                mod = None
            break
        p = p.parent
    _CEL_CACHE.append(mod)
    return mod


def cel_submit(fn, *args, _cel=None, _submit_fallback: bool = True, **kw):
    """把工作丟給 Celeritas 的暖執行緒池;拿不到就**直接呼叫**(graceful)。

    _cel             指定 Celeritas 模組(遷移現場沿用本檔原本的 `_CEL`);
                     不給就由正典自己找。給 None 且找不到 → 直呼。
    _submit_fallback True 時,`_LazyPool.submit` 不可用會再試 `_CEL.submit`。
                     活樹兩群的差別**只在這裡**,而且只有「有 submit 沒有 _LazyPool」時分得出來。
    """
    cel = _cel if _cel is not None else _celeritas()
    if cel is not None:
        pool = getattr(cel, "_LazyPool", None)
        if pool is not None:
            try:
                return pool.submit(fn, *args, **kw)
            except Exception:
                pass
        if _submit_fallback:
            sub = getattr(cel, "submit", None)
            if sub is not None:
                try:
                    return sub(fn, *args, **kw)
                except Exception:
                    pass
    return fn(*args, **kw)


# ────────────────────────── 八碼雜湊 ──────────────────────────
def hash8(s: str, *, errors: str = "strict", prefer_xxhash: bool = True) -> str:
    """八碼大寫雜湊。有 xxhash 就用(快),沒有就 sha256 —— 兩條路**結果不同**,
    所以同一棵樹上有沒有裝 xxhash 會影響雜湊值。這是活樹本來就有的性質,不是本正典引入的;
    量出來的 14 處全是這個寫法,照原樣搬。

    errors        `s.encode()` 的錯誤處理。活樹 13 處用預設(`strict`),1 處用 `replace`。
                  兩者對一般字串同解。
    prefer_xxhash False = **永遠走 sha256**。`generic_layout_engine.hash8` 是這一種——
                  它根本沒有 xxhash 分支。在裝了 xxhash 的機器上,兩條路**雜湊值不一樣**;
                  把它併成預設值等於**悄悄改掉它產生的所有 id**。這個選項就是為了不吃掉這個差異。
    """
    xx = safe_import("xxhash") if prefer_xxhash else None
    if xx is not None:
        return xx.xxh64(s.encode()).hexdigest()[:8].upper()
    return hashlib.sha256(s.encode("utf-8", errors=errors)).hexdigest()[:8].upper()


# ────────────────────────── 數字與旗標 ──────────────────────────
def num(s, *, drop=(), positive: bool = False):
    """逗號千分位字串 → float;轉不動回 None(**不拋**,因為抽取器找不到數字時的常態就是 None)。

    批597 VDF 併入:VDF 尾版有五支 `_num`,**分群之後是五個群**,不是同一件事——
      · ENG055 / ENG057  純轉換 → 不用參數(語料 28 組零差異)
      · ENG056           哨兵清單含 **'nan'**;不加 `drop` 的話 `float('nan')` 會回 nan
                         而不是 None(語料量到 2 處差異)
      · ENG063 / ENG075  只收 **正數**;不加 `positive` 的話 '0' / '-inf' / 'nan'
                         全部會被放行(語料量到 8 處差異)
    把差異寫成參數,呼叫端看得見;寫死成「大家都一樣」就是遷出行為變更。

    drop      去逗號+strip 後命中這個集合就回 None(哨兵字串,例:`('', '--', 'nan')`)
    positive  True 時只收 `f > 0`(nan > 0 為 False,所以 nan 也會被擋掉)
    """
    try:
        f = float(str(s).replace(",", ""))
    except Exception:
        return None
    if drop and str(s).replace(",", "").strip() in drop:
        return None
    if positive and not (f > 0):
        return None
    return f


def argval(args: list, flag: str, default=None, *, as_path: bool = False,
           quiet: bool = False, dashdash: bool = False):
    """從 argv 取旗標值。缺值=**誠實 None,不 IndexError**(批425 慣例)。

    as_path  True 回 `Path`(活樹 2 處是這一種),False 回字串。
    quiet    True 不印提示。
    default  批597 VDF 併入:VDF 三支 `_arg(a, flag, default=None)` 允許**呼叫端給預設**,
             而且活樹**是位置參數在用**(`_arg(a, "--db", str(DB_TW))`),所以這裡也放在
             `*` 前面;原本的關鍵字呼叫一個都不會壞(多一個位置槽不會少掉關鍵字)。
             正典原本一律回 None——直接換就是遷出行為變更。預設值每次回**新的一份**
             (L76:可變預設值共享過一次,位元組比不出來)。
    dashdash 批597:VDF 那三支**不會**把 `--` 開頭的下一個 token 當成「沒有值」,
             正典會。誰對誰錯不在這裡裁定(LL90),差異寫成參數讓呼叫端選。
    """
    if flag not in args:
        return _fresh(default)
    i = args.index(flag) + 1
    if i >= len(args) or (not dashdash and str(args[i]).startswith("--")):
        if not quiet:
            print(f"[旗標] {flag} 後面沒有值=忽略(誠實提示,不當作預設)")
        return _fresh(default)
    return Path(args[i]) if as_path else args[i]


def nan_safe(o):
    """`json.dumps(default=…)` 用:NaN / Inf → None,其餘 `str()`。

    活樹 `_jwrite` 有 12 處用這個、2 處用純 `str`。**差別是真的**:
    純 `str` 會把 `nan` 寫成字串 `"nan"`,下游再讀回來就變成一個看起來有值的髒資料。
    """
    return None if isinstance(o, float) and (math.isnan(o) or math.isinf(o)) else str(o)


def _fresh(v):
    """可變預設值每次回**新的一份**(L76 / LL147)。

    批597:`argval(default=...)` 讓呼叫端給預設值。如果直接把那個物件回出去,
    多個呼叫端拿到的是**同一個** list/dict,一邊 append 另一邊就跟著變——
    這正是批593 `bind_read(missing={})` 那個蟲,而且**位元組比對驗不出來**
    (差的是物件同一性,不是內容)。所以正典自己負責複製,不靠呼叫端記得。
    這一支是接 SUP_MDL752 的同名助手(綁定不另造),752 缺席就照 `_jsonio()` 那條路大聲拋。
    """
    return _jsonio()._fresh(v)


def _jsonio():
    """批592 的 JSON 讀寫正典;`_jwrite` 那 14 處直接接它,不另造一支。"""
    p = Path(__file__).resolve()
    while p.parent != p:
        hits = sorted((p / "supportive modules").glob("SUP_MDL752_VIAJsonIO_v*.py"))
        if hits:
            import importlib.util as ilu
            spec = ilu.spec_from_file_location("VIA_JSONIO", hits[-1])
            mod = ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
        p = p.parent
    raise RuntimeError("[FAIL] JSON 讀寫正典缺席:supportive modules/SUP_MDL752_VIAJsonIO_v*.py")


def bind_jwrite(*, mkdir: bool = True, default=nan_safe, quiet_fail: bool = False):
    """回一個 `_jwrite(p, data)` 綁定,底下走 SUP_MDL752。

    mkdir       活樹 11 處**沒有** mkdir、3 處有。沒有 mkdir 時,父夾不在就會拋——
                那是原本的行為,照搬。
    quiet_fail  True 時吞掉例外回 False、成功回 True(活樹 1 處是這一種)。
    """
    js = _jsonio()

    def _w(p, data):
        if quiet_fail:
            try:
                js.write(p, data, indent=2, default=default, atomic=False, mkdir=mkdir)
                return True
            except Exception:
                return False
        js.write(p, data, indent=2, default=default, atomic=False, mkdir=mkdir)
        return None
    return _w


def bind_import(**kw):
    return lambda name: safe_import(name, **kw)


def bind_cel(**kw):
    return lambda fn, *a, **k: cel_submit(fn, *a, **kw, **k)


def bind_hash8(**kw):
    return lambda s: hash8(s, **kw)


def bind_argval(**kw):
    return lambda args, flag: argval(args, flag, **kw)


# ────────────────────────── 自測:逐群重放 ──────────────────────────
def selftest() -> int:
    import json
    import tempfile
    n, fails = [0], []

    def chk(label, ok, extra=""):
        n[0] += 1
        print(f"  [{'OK' if ok else 'FAIL'}] {label}" + (f" ({extra})" if extra else ""))
        if not ok:
            fails.append(label)

    import ast as _ast
    tree = _ast.parse(Path(__file__).read_text(encoding="utf-8"))
    mods = set()
    for nd in _ast.walk(tree):
        if isinstance(nd, _ast.Import):
            mods |= {a.name.split(".")[0] for a in nd.names}
        elif isinstance(nd, _ast.ImportFrom) and nd.module:
            mods.add(nd.module.split(".")[0])
    chk("① 零網路零安裝:語法樹裡沒有 requests/httpx/urllib/subprocess 的 import",
        not (mods & {"requests", "httpx", "urllib", "subprocess", "socket", "http"}),
        f"(import:{sorted(mods)})")
    chk("② 名字像但不是同一件事的具名在冊(close / export_csv 是類別方法;"
        "有狀態的那版 _argval 綁在模組狀態上)",
        len(NOT_SAME_THING) == 4 and all(len(v) > 20 for v in NOT_SAME_THING.values()))

    # ── L76 同族:早綁 vs 晚讀 ──────────────────────────────────────────
    # 批594 在**出貨前**抓到的:VRN 的 `_cel_submit` 讀的是開機函式事後用 global 填進去的值。
    # 這一檢用合成語料把那個陷阱演一次,免得下一次又有人把「晚讀」綁成「早綁」。
    _state = {"ok": False, "cel": None}
    _early = _CelFrozen = _state["cel"] if _state["ok"] else None      # ← 早綁:現在就取值
    _state.update(ok=True, cel="POOL")                                  # ← 開機函式事後才填
    _late = _state["cel"] if _state["ok"] else None
    chk("②之二 **早綁不等於晚讀**(L76 同族):import 當下取值會把開機前的狀態凍住;"
        "VRN `_cel_submit` 17 處就是這一種,具名不遷",
        _early is None and _late == "POOL"
        and "_cel_submit" in " ".join(NOT_SAME_THING),
        f"(早綁 {_early} · 晚讀 {_late})")

    # ── safe_import:四群 ──
    chk("③ safe_import:找得到回模組、找不到回 None",
        safe_import("json") is not None and safe_import("no_such_mod_zzz") is None)

    class _Boom:
        def __init__(self):
            raise SystemExit(3)
    chk("④ `catch_all=True` 才吞 BaseException(活樹 7 處是 bare `except:`——"
        "**那是潛在缺陷不是風格**:會把 `sys.exit()` 吃掉當成「沒有這個模組」)",
        _eats(lambda: safe_import("json", catch_all=True), SystemExit) is False
        and _raises_base(lambda: _si_probe(False)) and not _raises_base(lambda: _si_probe(True)),
        "合成模組在 import 時 sys.exit(3):catch_all=False 讓它拋 · True 吞掉回 None")

    # ── cel_submit:兩群(有沒有第二層退路)──
    class _P:
        @staticmethod
        def submit(fn, *a, **k):
            return ("pool", fn(*a, **k))

    class _CelBoth:
        _LazyPool = _P

        @staticmethod
        def submit(fn, *a, **k):
            return ("cel", fn(*a, **k))

    class _CelSubmitOnly:
        @staticmethod
        def submit(fn, *a, **k):
            return ("cel", fn(*a, **k))
    f = lambda x: x * 2                                          # noqa: E731
    chk("⑤ cel_submit:有 _LazyPool 就走它;**兩群的差別只在「有 submit 沒有 _LazyPool」時**",
        cel_submit(f, 3, _cel=_CelBoth) == ("pool", 6)
        and cel_submit(f, 3, _cel=_CelSubmitOnly) == ("cel", 6)
        and cel_submit(f, 3, _cel=_CelSubmitOnly, _submit_fallback=False) == 6
        and cel_submit(f, 3, _cel=None) == 6 or cel_submit(f, 3, _cel=None) == ("pool", 6),
        "有池走池 · 無池有 submit:退路開=走 submit / 關=直呼")

    # ── hash8:兩群 ──
    h = hash8("測試 abc")
    _sha = hashlib.sha256("測試 abc".encode()).hexdigest()[:8].upper()
    _has_xx = safe_import("xxhash") is not None
    chk("⑥ hash8:八碼大寫、同輸入同輸出、errors=replace 對一般字串同解",
        len(h) == 8 and h.isupper() and h == hash8("測試 abc")
        and h == hash8("測試 abc", errors="replace"), h)
    chk("⑥之二 `prefer_xxhash=False` **永遠走 sha256**(有一處根本沒有 xxhash 分支;"
        "把它併成預設值,等於在裝了 xxhash 的機器上悄悄改掉它產生的所有 id)",
        hash8("測試 abc", prefer_xxhash=False) == _sha
        and ((h != _sha) if _has_xx else (h == _sha)),
        f"(本機 xxhash {'在' if _has_xx else '不在'} · 預設 {h} · 強制 sha256 {_sha})")

    # ── num / argval ──
    chk("⑦ num:逗號千分位吃得下,轉不動回 None(**不拋**)",
        num("1,234.5") == 1234.5 and num("abc") is None and num(None) is None)
    chk("⑧ argval:缺值誠實 None 不 IndexError;下一個是旗標也算缺值;as_path 回 Path",
        argval(["--a", "x"], "--a", quiet=True) == "x"
        and argval(["--a"], "--a", quiet=True) is None
        and argval(["--a", "--b"], "--a", quiet=True) is None
        and argval(["--a", "p"], "--zz", quiet=True) is None
        and isinstance(argval(["--a", "p"], "--a", as_path=True, quiet=True), Path))
    chk("⑨ nan_safe:NaN/Inf → None(純 str 會寫成字串 \"nan\",下游讀回來是髒資料)",
        nan_safe(float("nan")) is None and nan_safe(float("inf")) is None
        and nan_safe(Path("/a")) == "/a")

    # ── _jwrite 三群:逐群跟原始實作比**位元組** ──
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        payload = {"k": "值", "nan": float("nan"), "p": Path("/a")}

        def orig_nomkdir(p, data):
            Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=nan_safe),
                               encoding="utf-8")

        def orig_mkdir_str(p, data):
            Path(p).parent.mkdir(parents=True, exist_ok=True)
            Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str),
                               encoding="utf-8")
        bad = []
        for label, orig, canon, sub in (
                ("72717ae7ff·11處 無 mkdir · nan_safe", orig_nomkdir,
                 bind_jwrite(mkdir=False), "a"),
                ("57f48696c7·2處 有 mkdir · default=str", orig_mkdir_str,
                 bind_jwrite(mkdir=True, default=str), "b/c"),
                ("ea7ae6255d·1處 有 mkdir · nan_safe · 吞例外回 bool", orig_nomkdir,
                 bind_jwrite(mkdir=True, quiet_fail=True), "d/e")):
            pa, pb = t / f"{sub}_a.json", t / f"{sub}_b.json"
            pa.parent.mkdir(parents=True, exist_ok=True)
            orig(pa, payload)
            canon(pb, payload)
            if pa.read_bytes() != pb.read_bytes():
                bad.append(label)
        chk("⑩ **零損失(_jwrite)**:3 群逐群跟原始實作比**位元組**,並且底下走的是"
            "批592 的 SUP_MDL752 —— 不另造一支 JSON 寫法",
            not bad, "; ".join(bad) if bad else "位元組全同")
        chk("⑪ `quiet_fail=True` 真的吞:父夾不在也不拋,回 False",
            bind_jwrite(mkdir=False, quiet_fail=True)(t / "no" / "such" / "x.json", {}) is False)

    # ── LL147:綁定工廠不得共用可變狀態 ──
    b1, b2 = bind_argval(quiet=True), bind_argval(quiet=True)
    chk("⑫ 綁定工廠各自獨立(LL147/L76:批593 就是栽在工廠綁死一個可變物件上)",
        b1 is not b2 and b1(["--a", "1"], "--a") == "1" and b2(["--a", "2"], "--a") == "2")

    # ⑬ 批597 VDF `_num` 五群零損失 —— 對照組是**原實作逐字抄**
    #     (批592 教訓:對照組抄錯,證出來的零損失就是假的)
    def _c055(v):
        try:
            return float(str(v).replace(",", "")) if v not in (None, "", "--") else None
        except ValueError:
            return None

    def _c056(v):
        try:
            t = str(v).replace(",", "").strip()
            return float(t) if t not in ("", "--", "-", "None", "nan") else None
        except ValueError:
            return None

    def _c057(x):
        try:
            return float(str(x).replace(",", "").strip())
        except Exception:
            return None

    def _c063(v):
        try:
            f = float(str(v).replace(",", ""))
            return f if f > 0 else None
        except Exception:
            return None

    def _c075(v):
        try:
            f = float(str(v).replace(",", "").strip())
            return f if f > 0 else None
        except Exception:
            return None

    NCORP = [None, "", "--", "-", "None", "nan", "NaN", "inf", "-inf", " 1,234.5 ", "1,234",
             "0", "-3.5", "3.5", 0, -1, 2.5, True, False, [], {}, "abc", "1e3", "  ",
             "12,", ",12", float("nan"), float("inf")]
    NBIND = {"ENG055": {}, "ENG056": {"drop": ("", "--", "-", "None", "nan")},
             "ENG057": {}, "ENG063": {"positive": True}, "ENG075": {"positive": True}}
    NCTRL = {"ENG055": _c055, "ENG056": _c056, "ENG057": _c057,
             "ENG063": _c063, "ENG075": _c075}

    def _same(a, b):
        if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
            return True
        return type(a) is type(b) and a == b

    def _call(fn, *a, **k):
        try:
            return ("OK", fn(*a, **k))
        except Exception as exc:
            return ("EXC", f"{type(exc).__name__}: {exc}")

    nbad = []
    for k_, ctrl in NCTRL.items():
        for v_ in NCORP:
            x, y = _call(ctrl, v_), _call(num, v_, **NBIND[k_])
            ok_ = x[0] == y[0] and (_same(x[1], y[1]) if x[0] == "OK" else x[1] == y[1])
            if not ok_:
                nbad.append(f"{k_} {v_!r}: 原 {x} ≠ 正典 {y}")
    chk("⑬ **零損失(num)**:VDF 五支 `_num` 分群後是**五個群**(兩支純轉換、一支哨兵含 "
        "'nan'、兩支只收正數),逐群綁參數 × 28 組語料逐一同解",
        not nbad, "; ".join(nbad[:2]) if nbad else
        f"{len(NCTRL)} 群 × {len(NCORP)} 組 = {len(NCTRL) * len(NCORP)} 全同")

    # ⑭ 批597 VDF `_arg` 三支(同一群)零損失 + 預設值不得共用
    def _carg(a, flag, default=None):
        if flag in a:
            i = a.index(flag)
            if i + 1 < len(a):
                return a[i + 1]
        return default

    ACORP = [(["--a", "1"], "--a"), (["--a"], "--a"), ([], "--a"), (["--a", "--b"], "--a"),
             (["x", "--a", "y", "--a", "z"], "--a"), (["--a", ""], "--a"), (["--a", "-5"], "--a")]
    abad = []
    for a_, f_ in ACORP:
        for d_ in (None, "D", 0):
            x = _call(_carg, list(a_), f_, d_)
            y = _call(argval, list(a_), f_, default=d_, quiet=True, dashdash=True)
            if x != y:
                abad.append(f"{a_} {f_} default={d_!r}: 原 {x} ≠ 正典 {y}")
    d1 = argval([], "--x", default=[])
    d2 = argval([], "--x", default=[])
    d1.append("髒")
    chk("⑭ **零損失(argval)**:VDF 三支 `_arg` 同一群,`default=` + `dashdash=True` "
        "逐組同解;且可變預設值**每次回新的一份**(L76:兩次拿到的不得是同一個物件)",
        not abad and d1 is not d2 and d2 == [],
        "; ".join(abad[:2]) if abad else f"{len(ACORP)}×3 全同 · 預設值獨立")

    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def _si_probe(catch_all: bool):
    """合成一個「import 時就 sys.exit()」的模組,證明 bare except 會把它吃掉。"""
    import tempfile
    import types
    d = tempfile.mkdtemp()
    name = "zz_boom_mod"
    Path(d, f"{name}.py").write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
    sys.path.insert(0, d)
    sys.modules.pop(name, None)
    try:
        return safe_import(name, catch_all=catch_all)
    finally:
        sys.path.remove(d)
        sys.modules.pop(name, None)
        del types


def _raises_base(fn) -> bool:
    try:
        fn()
        return False
    except BaseException:
        return True


def _eats(fn, exc) -> bool:
    try:
        fn()
        return False
    except exc:
        return True


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print(f"=== VRN 共用小工具正典(SUP_MDL753 v{VERSION})· 十六檢自測(零網路;只在沙盒寫)===")
        return selftest()
    print(f"SUP_MDL753_VIACommonUtils v{VERSION} — VRN 共用小工具正典")
    print("  safe_import · cel_submit · hash8 · num · argval · nan_safe · bind_jwrite(→SUP_MDL752)")
    print(f"  不得併的:{sorted(NOT_SAME_THING)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
