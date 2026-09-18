#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
SUP_MDL752_VIAJsonIO v0100 — JSON 讀寫正典(批592)

批589 的 CGC 整合債第二、三名:`load.json` 13 族 · `save.json` 12 族。
批592 照 L75 先分群(AST 正規化比骨架),結果跟 `newest` **完全不是同一種情況**:

  活樹尾版 168 支 · 定義 **20 處** · 行為群 **17 群**
  (debt 報的 83 / 35 檔含**版本史**;LL142 說過,債要以家族計不以檔計)

幾乎每一處都不一樣,而且有兩處**根本不是檔案 IO**:

  · `CGC_MDL095_DeckServer._json(self, obj, code)`   → 發 **HTTP 回應**(send_header/wfile)
  · `CGC_MDL095_DeckServer._read_json(self, cap)`    → 讀 **HTTP 請求 body**
                                                       (Content-Type 驗證 · 拒 Transfer-Encoding · 容量上限)

**這兩處不得併。**它們跟「讀一個 JSON 檔」是兩件事,只是名字長得像。
本正典把它們列成具名排除,免得下一輪又被算成整合債。

## 讀:差異只有三條軸,而且讀不改變產出 → 風險低,可以收

  encoding   `utf-8-sig` 7 處 vs `utf-8` 5 處
             **這是活的不一致**:帶 BOM 的 JSON 用 `utf-8` 讀會當場拋,
             所以同一個檔有些引擎讀得到、有些讀不到。
  缺檔/壞檔  回 `None`(多數)· 回 `{}`(VIA_AutoCodeGenerator)· **直接拋**
             (`CGC_MDL156.load_json` · `VIA_GovernanceParameterControl.read_json`)
             回 None 會把**壞檔**說成「不存在」——那是 LL138 的假的零。
             正典保留兩種,但要**明示選哪一種**,不讓它默默發生。
  先檢查     有的先 `is_file()` 再讀,有的直接讀靠 except 接住(等價,但寫法不同)

## 寫:`indent` 與尾換行是**產出契約**,不得統一

  原子寫     tmp+replace(MDL136/137 · MDL135)vs 直接寫
  indent     `1`(3 處)· `2` + **尾換行**(VIA_AutoCodeGenerator)· 無
  default    `default=str`(MDL139)
  mkdir      多數 `parents=True, exist_ok=True`

把 `indent` 統一,等於讓所有 registry JSON 的 diff 整個炸開——而且本樹的慣例
(registry JSON 用 `indent=1`、**無尾換行**)本身就是一個要守的契約。
所以寫的一側:**只併證得出位元組相同的**,差異一律留成明示選項。

律:零網路;零安裝;`--selftest` 零網路且只在 tempfile 沙盒寫。
用法:python3 SUP_MDL752_VIAJsonIO_v0100.py --selftest
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

import copy
import json
import os
import sys
from pathlib import Path

VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]

#: 名字長得像但**不是檔案 IO**,不得併(見模組說明)。留在這裡是為了讓下一輪的債表認得它們。
NOT_FILE_IO = {
    "CGC_MDL095_DeckServer._json": "發 HTTP 回應(send_response/send_header/wfile.write),不是寫檔",
    "CGC_MDL095_DeckServer._read_json": "讀 HTTP 請求 body(Content-Type 驗證 · 拒 Transfer-Encoding · 容量上限),不是讀檔",
}

#: **證不過所以沒遷**(L75)。目前為空——留這個表是為了下一次:
#: 遷不動的一律留名字、留理由,不留一句「之後再說」。
NOT_MIGRATED: dict[str, str] = {}
#: 曾經進過上表、批593 查清根因後補遷完成的。留著是因為**根因比結果值錢**。
RESOLVED = {
    "VIA_AutoCodeGenerator_v0100.load_json":
        "批592 遷完 CGC_MDL155 檢④⑨ 由綠轉紅(計數累加)。批593 根因:"
        "原本 `if not path.exists(): return {}` **每次都是新的空 dict**,"
        "遷成 `bind_read(missing={})` 之後那個 `{}` 是工廠建立時求值的**同一個物件**,"
        "而呼叫端 `chain_reg[\"codechains\"].append(obj)` 直接改它——"
        "第二次呼叫就拿到被改過的那一份。**位元組零損失全過卻還是壞了**,"
        "因為差異不在 dumps 的輸出,在『回傳值是不是同一個物件』。"
        "修法:`_fresh()` 對可變容器回 deepcopy;自測 ⑤之二 釘住。",
}

def _fresh(v):
    """可變的預設值每次都給**新的一份**。

    批593 根因:`VIA_AutoCodeGenerator.load_json` 原本是 `if not path.exists(): return {}`
    ——**每次呼叫都是一個新的空 dict**。我把它遷成 `bind_read(missing={})`,那個 `{}` 是在
    **工廠建立時**求值的**同一個物件**,而呼叫端會直接改它:

        chain_reg = load_json(self.ssot.codechain)
        chain_reg.setdefault("codechains", [])
        chain_reg["codechains"].append(obj)        # ← 改到的是綁在工廠裡的那一個

    於是第二次呼叫拿到的是被改過的那一份,計數一路累加
    (`index_count 2` · `product_count 3` · `LNK-0004`),`CGC_MDL155` 檢④⑨ 由綠轉紅。
    **位元組層級的零損失自測全過,卻還是壞了**——因為差異不在 dumps 的輸出,
    在「回傳值是不是同一個物件」。這就是 Python 的可變預設值坑,只是換了一件外套。
    """
    return copy.deepcopy(v) if isinstance(v, (dict, list, set, bytearray)) else v


_MISSING = object()
#: 明示的「請拋出來」哨兵。寫 `missing=RAISE` 比寫 `strict=True` 更看得出是哪一半要拋。
RAISE = object()


def read(path, *, missing=None, broken=None, bom: bool = True, strict: bool = False):
    """讀一個 JSON 檔。**缺檔與壞檔是兩件事,兩個旋鈕。**

    第一版我把它們合成一個 `default`,自測的零損失檢當場打臉:
    `VIA_AutoCodeGenerator.load_json` 是**缺檔回 `{}`、壞檔直接拋**——
    一個 `default` 表達不出來。**回 default 會把壞檔說成「不存在」,那是 LL138 的假的零。**

    missing 檔案不在時回什麼;給 `RAISE` 就拋(預設 None)
    broken  檔案在但 parse 不了時回什麼;給 `RAISE` 就拋(預設 None)
    bom     True 用 `utf-8-sig`(吃得下帶 BOM 的檔);False 用 `utf-8`
            ——活樹那條不一致就在這裡:同一個帶 BOM 的檔,有些引擎讀得到有些讀不到。
    strict  True = `missing=RAISE, broken=RAISE` 的簡寫(覆蓋前兩個)
    """
    if strict:
        missing = broken = RAISE
    enc = "utf-8-sig" if bom else "utf-8"
    p = Path(path) if path else None
    if p is None or not p.is_file():
        if missing is RAISE:
            return json.loads(Path(path).read_text(encoding=enc))   # 讓它用原生錯誤拋
        return _fresh(missing)
    try:
        return json.loads(p.read_text(encoding=enc))
    except Exception:
        if broken is RAISE:
            raise
        return _fresh(broken)


def write(path, obj, *, indent=1, ensure_ascii: bool = False, atomic: bool = True,
          mkdir: bool = True, default=_MISSING, newline: bool = False) -> Path:
    """寫一個 JSON 檔。**`indent` 與 `newline` 是產出契約,預設值不代表「對」。**

    indent      縮排;本樹 registry JSON 的慣例是 `1`。傳 None 就是不縮排。
    atomic      True 走 tmp + `os.replace`(讀者永不見半檔);False 直接寫。
    mkdir       True 先 `mkdir(parents=True, exist_ok=True)`。
    default     `json.dumps` 的 `default=`(MDL139 那一處是 `str`);不傳就不帶這個參數。
    newline     True 在結尾補一個 `\n`(VIA_AutoCodeGenerator 那一處是 `indent=2` + 尾換行)。
    """
    p = Path(path)
    kw = {"ensure_ascii": ensure_ascii, "indent": indent}
    if default is not _MISSING:
        kw["default"] = default
    body = json.dumps(obj, **kw) + ("\n" if newline else "")
    if mkdir:
        p.parent.mkdir(parents=True, exist_ok=True)
    if atomic:
        tmp = p.with_suffix(p.suffix + f".tmp{os.getpid()}")
        tmp.write_text(body, encoding="utf-8")
        os.replace(tmp, p)
    else:
        p.write_text(body, encoding="utf-8")
    return p


def bind_read(**kw):
    """回一個綁好選項的讀取器(遷移現場用;**綁定不是 def**,見 LL143)。

    呼叫端若還吃第二個位置參數(`_read_json(path, default)` 那一群),
    它會蓋掉 `missing` 與 `broken` ——原本那一群就是這個語意。
    """
    def _r(path, *a):
        kw2 = dict(kw)
        if a:
            kw2["missing"] = kw2["broken"] = a[0]
        return read(path, **kw2)
    return _r


def bind_write(**kw):
    """回一個綁好選項的寫入器。"""
    return lambda path, obj: write(path, obj, **kw)


# ────────────────────────── 自測:15 個檔案 IO 群逐群重放 ──────────────────────────
def _variants_read():
    """對照組=**原始實作原樣抄**,try/except 一個都不能省。

    第一版我把 try/except 寫掉了,零損失檢當場報「原 EXC ≠ 正典 None」——
    紅的是對照組不是正典。**對照組抄錯,證出來的零損失就是假的。**
    """
    P, J = Path, json

    def _g(fn, fallback=None):
        try:
            return fn()
        except Exception:
            return fallback

    return [
        ("fca967a4ad·3處 _read_json(p) utf-8-sig · try/except→None",
         lambda p: _g(lambda: J.loads(P(p).read_text(encoding="utf-8-sig"))),
         lambda p: read(p)),
        ("f729499f36·1處 _json(p) utf-8 · try/except→None",
         lambda p: _g(lambda: J.loads(P(p).read_text(encoding="utf-8"))),
         lambda p: read(p, bom=False)),
        ("334e3ae71e·1處 _json(p) utf-8-sig + is_file 守衛 · try/except→None",
         lambda p: _g(lambda: J.loads(P(p).read_text(encoding="utf-8-sig"))
                      if p and P(p).is_file() else None),
         lambda p: read(p)),
        ("1b44587e70·1處 _read_json(path, default) utf-8-sig · try/except→default",
         lambda p: _g(lambda: J.loads(P(p).read_text(encoding="utf-8-sig"))),
         lambda p: read(p)),
        ("36db37f486·1處 load_json(path) utf-8-sig + is_file · try/except→None",
         lambda p: _g(lambda: J.loads(P(p).read_text(encoding="utf-8-sig"))
                      if P(p).is_file() else None),
         lambda p: read(p)),
        ("deef4a0dc0·1處 load_json(path) utf-8-sig · try/except→None",
         lambda p: _g(lambda: J.loads(P(p).read_text(encoding="utf-8-sig"))),
         lambda p: read(p)),
        ("d0eb840896·1處 load_json(path) utf-8 · **缺檔壞檔都拋**",
         lambda p: J.loads(P(p).read_text(encoding="utf-8")),
         lambda p: read(p, bom=False, strict=True)),
        ("06cd762033·1處 read_json(path) open() · **缺檔壞檔都拋**",
         lambda p: J.load(P(p).open("r", encoding="utf-8")),
         lambda p: read(p, bom=False, strict=True)),
        ("e6fc620ef2·1處 load_json(path) · **缺檔回 {} 但壞檔拋**(一個 default 表達不出來)",
         lambda p: ({} if not P(p).exists() else J.loads(P(p).read_text(encoding="utf-8"))),
         lambda p: read(p, bom=False, missing={}, broken=RAISE)),
    ]


def _variants_write():
    J = json
    return [
        ("022cfce3a7·2處 原子寫 indent=1",
         lambda p, o: (p.parent.mkdir(parents=True, exist_ok=True),
                       p.with_suffix(p.suffix + ".t").write_text(
                           J.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8"),
                       os.replace(p.with_suffix(p.suffix + ".t"), p))[-1],
         lambda p, o: write(p, o, indent=1)),
        ("8f8e1eccc4·1處 indent=1 + default=str",
         lambda p, o: (p.parent.mkdir(parents=True, exist_ok=True),
                       p.write_text(J.dumps(o, ensure_ascii=False, indent=1, default=str),
                                    encoding="utf-8"))[-1],
         lambda p, o: write(p, o, indent=1, default=str, atomic=False)),
        ("8860f89958·1處 open() 直接寫 indent=1",
         lambda p, o: (p.parent.mkdir(parents=True, exist_ok=True),
                       J.dump(o, p.open("w", encoding="utf-8"), ensure_ascii=False, indent=1))[-1],
         lambda p, o: write(p, o, indent=1, atomic=False)),
        ("43ab675807·1處 indent=2 + **尾換行**",
         lambda p, o: (p.parent.mkdir(parents=True, exist_ok=True),
                       p.write_text(J.dumps(o, indent=2, ensure_ascii=False) + "\n",
                                    encoding="utf-8"))[-1],
         lambda p, o: write(p, o, indent=2, atomic=False, newline=True)),
    ]


def selftest() -> int:
    import ast as _ast
    import tempfile
    n, fails = [0], []

    def chk(label, ok, extra=""):
        n[0] += 1
        print(f"  [{'OK' if ok else 'FAIL'}] {label}" + (f" ({extra})" if extra else ""))
        if not ok:
            fails.append(label)

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
    chk("② 名字像但不是檔案 IO 的兩處**具名在冊**(DeckServer 的 HTTP 回應與請求 body),"
        "免得下一輪又被算成整合債",
        len(NOT_FILE_IO) == 2 and all("HTTP" in v for v in NOT_FILE_IO.values()),
        f"({sorted(NOT_FILE_IO)})")
    chk("②之二 遷不動的一律**留名字留理由**(L75);查清根因補遷的留在 RESOLVED,"
        "因為**根因比結果值錢**",
        all(len(v) > 60 for v in NOT_MIGRATED.values())
        and all(len(v) > 60 for v in RESOLVED.values()) and len(RESOLVED) >= 1,
        f"(未遷 {sorted(NOT_MIGRATED) or '無'} · 已補遷 {sorted(RESOLVED)})")

    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        good, bom, bad, gone = t / "g.json", t / "b.json", t / "x.json", t / "nope.json"
        payload = {"k": "值", "n": 1}
        good.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        bom.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8-sig")
        bad.write_text("{ 這不是 JSON", encoding="utf-8")

        chk("③ BOM:`bom=True` 讀得到帶 BOM 的檔,`bom=False` 讀不到"
            "(這就是活樹那條不一致——同一個檔有些引擎讀得到有些讀不到)",
            read(bom) == payload and read(bom, bom=False) is None,
            f"(sig {read(bom)} · utf8 {read(bom, bom=False)})")
        chk("④ **缺檔與壞檔是兩個旋鈕**:可以缺檔回 {} 而壞檔照樣拋"
            "(合成一個 default 就表達不出來,而且會把壞檔說成不存在=假的零)",
            read(gone) is None and read(bad) is None
            and read(gone, missing={}) == {} and read(bad, broken=[]) == []
            and read(gone, missing={}, broken=RAISE) == {}
            and _raises(lambda: read(bad, missing={}, broken=RAISE)))
        _b = bind_read(bom=False, missing={})
        _one, _two = _b(gone), _b(gone)
        _one["x"] = 1
        chk("⑤之二 **可變預設值每次都要是新的一份**(批593 根因:呼叫端 append 回傳值,"
            "把綁在工廠裡的那個 dict 改掉,下一次就拿到被改過的——計數一路累加)",
            _two == {} and _one is not _two and _b(gone) == {},
            f"(第一次改成 {_one} · 第二次 {_two} · 第三次 {_b(gone)})")
        chk("⑤ `strict=True` 缺檔壞檔**直接拋**(回 default 會把壞檔說成不存在=假的零)",
            _raises(lambda: read(gone, strict=True)) and _raises(lambda: read(bad, strict=True))
            and read(good, strict=True) == payload)

        bad_rows = []
        for label, orig, canon in _variants_read():
            for src in (good, bom, gone, bad):
                try:
                    a = orig(src)
                except Exception as exc:
                    a = f"EXC:{type(exc).__name__}"
                try:
                    b = canon(src)
                except Exception as exc:
                    b = f"EXC:{type(exc).__name__}"
                if repr(a) != repr(b):
                    bad_rows.append(f"{label} · {src.name} · 原 {a!r} ≠ 正典 {b!r}")
        chk(f"⑥ **零損失(讀)**:{len(_variants_read())} 種具名變體 × 語料(正常/BOM/缺檔/壞檔)"
            f"逐一同解", not bad_rows, "; ".join(bad_rows[:2]) if bad_rows else "全同")

        bad_w = []
        for label, orig, canon in _variants_write():
            pa, pb = t / "wa" / "o.json", t / "wb" / "o.json"
            orig(pa, payload)
            canon(pb, payload)
            if pa.read_bytes() != pb.read_bytes():
                bad_w.append(f"{label} · 位元組不同")
        chk(f"⑦ **零損失(寫)**:{len(_variants_write())} 種具名變體,產出檔**逐位元組相同**"
            f"(indent 與尾換行是產出契約,併錯了 registry 的 diff 會整個炸開)",
            not bad_w, "; ".join(bad_w[:2]) if bad_w else "位元組全同")

        chk("⑧ 原子寫:tmp 檔用完不留(讀者永不見半檔,也不留垃圾)",
            (write(t / "at.json", payload, atomic=True).exists()
             and not list((t).glob("at.json.tmp*"))))
        chk("⑨ `indent` 不預設成「對的那個」:同一份資料三種 indent 給三種位元組",
            len({write(t / f"i{i}.json", payload, indent=i).read_bytes()
                 for i in (1, 2, 4)}) == 3)
        chk("⑩ 綁定工廠回的是綁定不是 def(LL143:寫 def 的話家族數不會掉)",
            bind_read(bom=False)(good) == payload
            and bind_write(indent=2)(t / "bw.json", payload).exists())

    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except Exception:
        return True


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print(f"=== JSON 讀寫正典(SUP_MDL752 v{VERSION})· 十一檢自測(零網路;只在沙盒寫)===")
        return selftest()
    print(f"SUP_MDL752_VIAJsonIO v{VERSION} — JSON 讀寫正典")
    print("  read(path, *, missing=None, broken=None, bom=True, strict=False)")
    print("  write(path, obj, *, indent=1, ensure_ascii=False, atomic=True, mkdir=True,"
          " default=…, newline=False)")
    print(f"  不得併的兩處(不是檔案 IO):{sorted(NOT_FILE_IO)}")
    print(f"  證不過所以沒遷:{sorted(NOT_MIGRATED) or '無'}")
    print(f"  查清根因後補遷:{sorted(RESOLVED)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
