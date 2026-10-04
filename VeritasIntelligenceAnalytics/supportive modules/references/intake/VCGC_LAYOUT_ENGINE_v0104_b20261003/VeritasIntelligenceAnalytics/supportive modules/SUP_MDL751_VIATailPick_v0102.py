#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
SUP_MDL751_VIATailPick v0101 — 尾版取用正典(批590 建;批591 +bind() 工廠蓋滿 13 群)

批589 量出來 CGC 族最大的一筆整合債:**33 個家族各寫一份「取尾版」**。
批590 把它們逐支取出來按**行為**分群(不按長相),結果是 32 份定義 / **13 個行為群**:

  群 f88659f52d 10 支  newest(pattern, root)   sorted(root.glob(pattern))[-1] or None
  群 0cf7954847  6 支  newest(dirp, pat)       **參數順序相反**,外加 dirp.exists() 守衛
  群 229d9eae5e  3 支  _newest(dirp, pat)      同上但無守衛
  群 814deab1ca  2 支  _newest(pat, root)      **rglob**(遞迴),不是 glob
  群 4fbcbc161e  2 支  _newest(pat, root)      無型別註記,其餘同第一群
  群 6226e981ca  2 支  _newest(pat, d)         d.exists() 守衛
  群 2c54462eb1  1 支  newest(folder, pattern) **缺件回 `str(folder/pattern)`**,不回 None
  群 358116394a  1 支  newest(pattern, root=HERE) **濾掉 stem 含 `_sha` 的**
  群 000606dfba  1 支  newest(pat, root=VIA)   pat **帶目錄**,先 root/pat 再拆 parent/name
  群 8a121a3b6b  1 支  newest(pattern)         只有一個參數,root 固定 HERE
  群 69abf90773  1 支  _newest(dirp, pat)      **按 st_mtime 排序**,不是字典序
  群 52256fcb33  1 支  newest(pat, root=HERE)  同第一群,預設值不同
  群 c2dc24c114  1 支  _newest(d, pat)         d.is_dir() 守衛

**這 13 群不是同一件事。**最大的兩群參數順序是相反的;有兩支走 rglob;有一支缺件回
pattern 本身而不是 None;有一支**按 mtime 排序**。盲目「併成一支」等於把這些差異吃掉——
那不是整合,那是遺失(操作員令:引擎類似的整合勿遺失)。

所以正典的作法是:**一個簽章,把差異變成明示的選項**,並且用自測**逐群重放**證明
「正典帶對的選項 == 原本那一份」。證不出來的那一群,就不准遷。

  newest(root, pattern, *, recursive=False, exclude=(), on_missing=None, key="name")

**mtime 那一群要特別講**:尾版律是「同名不同版取**版號字典序**最後一個」。
按 mtime 取,會在舊版檔案被碰過(複製、chmod、還原)之後選到舊版。本正典支援 `key="mtime"`
只為了**證明等價**與相容遷移,不代表它是對的;`CGC_MDL119_SystemAPI` 那一支是否該改成
字典序,是操作員的裁定(LL90),本檔不代改、也不代判。

v0100→v0101(批591):+`bind()` 工廠。剩下的群還差**預設 root** / **rglob** /
**exclude `_sha`** / **mtime 排序** / **缺件回 pattern**;為每一種再取一個名字會變成
`newest_pr_rglob_nosha_mtime` 那種東西——13 份實作換成 13 個名字,沒有比較好。
工廠把選項留在呼叫端(看得見),回來的是**綁定不是 def**(寫 def 的話家族數不會掉,LL143)。
自測仍是十二檢(檢數沒變,變的是第⑫檢的變體數 8→14、語料組 48→84):六種 bind 走法逐種再證一次——**工廠繞出來的路也要證,不能只證直呼**。

律:零網路;零安裝;正本零觸碰(只讀 glob,不寫任何檔);`--selftest` 零網路。
用法:python3 SUP_MDL751_VIATailPick_v0100.py --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
# 批590 全格當場抓到:新開的正典忘了掛這條橋,MDL156 覆蓋閘直接紅。閘是對的——
# 「全樹導入」就是全樹,新開的檔沒有豁免權;而且這種漏掉不會自己現形,要靠閘。
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

import sys
from pathlib import Path

VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]

#: 排序鍵。`name` = 尾版律(版號字典序);`mtime` = 檔案修改時間(相容用,見上文)。
_KEYS = {"name": lambda p: p.name, "mtime": lambda p: p.stat().st_mtime}


def newest(root, pattern: str, *, recursive: bool = False, exclude=(),
           on_missing=None, key: str = "name"):
    """取尾版。

    root       起點目錄(Path 或 str)。不存在 / 不是目錄 → 照 `on_missing` 處理。
    pattern    glob 樣式。**可以帶目錄**(`sub/CGC_*_v*.py`);帶目錄時自動拆 parent/name。
    recursive  True 走 rglob(遞迴子樹),False 走 glob(只看本層)。
    exclude    stem 命中任一片語就剔掉(例:`("_sha",)`)。
    on_missing 找不到時回什麼:None(預設)或 "pattern"(回 `str(root/pattern)`,
               讓下游自己判 ABSENT——MDL157 那一群靠的就是這個)。
    key        "name"(尾版律,預設)或 "mtime"(相容;見模組說明)。
    """
    if key not in _KEYS:
        raise ValueError(f"key 只能是 {sorted(_KEYS)},收到 {key!r}")
    root = Path(root)
    if "**" in str(pattern):
        # 批597:`**` 樣式以前會**靜默回 None**——`root/"**/x.py"` 的 `.parent` 是
        #   `root/"**"`,那個目錄當然不存在,`base.is_dir()` False → hits=[] → None。
        #   呼叫端看到的是「沒找到」,而不是「這支不支援」。**靜默回 None 跟假綠同一個病**
        #   (LL151)。Path.glob 本來就吃得下 `**`,所以直接交給它,不要自己拆。
        #   量過:活樹 32 個呼叫端目前**沒有人傳 `**`**,所以這是補洞不是修災情。
        base, pat = root, str(pattern)
    else:
        p = root / pattern
        base, pat = p.parent, p.name          # pattern 帶目錄時在這裡拆開
    hits = []
    try:
        if base.is_dir():
            it = base.rglob(pat) if (recursive and "**" not in pat) else base.glob(pat)
            hits = [h for h in it if not any(x in h.stem for x in exclude)]
            hits.sort(key=_KEYS[key])
    except OSError:
        hits = []                          # 權限/競態:誠實當作沒有,不炸
    if hits:
        return hits[-1]
    return str(root / pattern) if on_missing == "pattern" else None


def newest_pr(pattern: str, root, **kw):
    """**相容綁定:參數順序是 (pattern, root)。**

    批590 量到最大的兩群參數順序是**相反的**(`newest(pattern, root)` 10 支 vs
    `newest(dirp, pat)` 6 支)。與其在正典裡用「看型別猜哪個是路徑」這種魔法——猜錯就回錯檔,
    而且錯得無聲——不如把兩種順序各給一個**具名**綁定,遷移時看名字就知道自己吃哪一種。
    `newest_pr` = pattern-root;正典本尊 `newest` = root-pattern。
    """
    return newest(root, pattern, **kw)


_KEEP = object()   # 批597:bind 的 missing 預設哨兵(None 是合法回值,不能拿來當「沒給」)


def bind(*, order: str = "rp", root_default=None, stringify: bool = False,
         attr: str | None = None, missing=_KEEP, **kw):
    """回一個**綁好選項**的取用器,給遷移現場用。

    批591:13 群裡只有前幾群能靠 `newest` / `newest_pr` 兩個名字蓋住。剩下的還差
    **預設 root**(`root=HERE` / `root=VIA` / 只吃一個參數)、**rglob**、**exclude `_sha`**、
    **mtime 排序**、**缺件回 pattern**。為每一種再取一個名字會變成一堆
    `newest_pr_rglob_nosha_mtime` ——那只是把 13 份實作換成 13 個名字,沒有比較好。
    所以給一個工廠:選項寫在呼叫端、看得見,而且回來的是**綁定**不是 `def`
    (再寫一個 `def` 的話,能力庫裡那一家族還在,家族數不會掉=等於沒併,LL143)。

    order         "rp" = (root, pattern) · "pr" = (pattern, root)
    root_default  呼叫端省略 root 時用它(對到 `root=HERE` / `root=VIA` 那幾群)
    attr          命中時回 `getattr(path, attr)`(目前只准 "name" / "stem" / "suffix";
                  VDF_ENG073 那一群要的是**檔名字串**,不是整條路徑——`stringify=True`
                  給的是 `str(path)`,兩者不一樣,分不清就會遷出行為變更)
    missing       找不到時回什麼(預設 `_KEEP` = 照 `newest` 的 `on_missing` 回;
                  VDF_ENG073 那一群缺件回的是空字串 `""`,不是 None)
    stringify     回 `str` 不回 `Path`(MDL157 那一群:缺件時回 `str(folder/pattern)`
                  讓下游自己判 ABSENT,所以命中時也得是 str,型別不能兩樣)
    kw            直接轉給 `newest`:recursive / exclude / on_missing / key
    """
    if attr is not None and attr not in ("name", "stem", "suffix"):
        raise ValueError(f'attr 只能是 name/stem/suffix,收到 {attr!r}')
    if order not in ("rp", "pr"):
        raise ValueError(f"order 只能是 'rp' 或 'pr',收到 {order!r}")

    def _pick(a, b=None):
        if order == "rp":
            root, pattern = a, b
        else:
            pattern, root = a, b
        if root is None:
            root = root_default
        if root is None:
            raise TypeError("沒有給 root,也沒有 root_default")
        r = newest(root, pattern, **kw)
        if r is None or (isinstance(r, str) and not r):
            return r if missing is _KEEP else missing
        if attr:
            r = getattr(Path(r), attr)
        return str(r) if stringify and r is not None else r
    return _pick


# ────────────────────────── 自測:13 群逐群重放 ──────────────────────────
#: 每一群的**原始實作**原樣抄進來當對照組,外加「正典要帶什麼選項才等價」。
#: 這不是裝飾:併之前要能證明「換過去之後結果一模一樣」,證不出來的不准遷。
def _variants():
    P = Path
    return [
        ("f88659f52d·10支 newest(pattern, root) → 相容綁定 newest_pr",
         lambda pattern, root: (sorted(P(root).glob(pattern)) or [None])[-1],
         lambda pattern, root: newest_pr(pattern, root)),
        ("0cf7954847·6支 newest(dirp, pat) +exists 守衛",
         lambda pattern, root: ((sorted(P(root).glob(pattern)) if P(root).exists() else []) or [None])[-1],
         lambda pattern, root: newest(root, pattern)),
        ("814deab1ca·2支 _newest(pat, root) **rglob**",
         lambda pattern, root: (sorted(P(root).rglob(pattern)) or [None])[-1],
         lambda pattern, root: newest(root, pattern, recursive=True)),
        ("2c54462eb1·1支 缺件回 str(folder/pattern)",
         lambda pattern, root: (str(sorted(P(root).glob(pattern))[-1])
                                if sorted(P(root).glob(pattern)) else str(P(root) / pattern)),
         lambda pattern, root: (lambda r: str(r) if r is not None else r)(
             newest(root, pattern, on_missing="pattern"))),
        ("358116394a·1支 濾掉 stem 含 `_sha`",
         lambda pattern, root: ([h for h in sorted(P(root).glob(pattern)) if "_sha" not in h.stem]
                                or [None])[-1],
         lambda pattern, root: newest(root, pattern, exclude=("_sha",))),
        ("000606dfba·1支 pat 帶目錄,先 root/pat 再拆",
         lambda pattern, root: ((sorted((P(root) / pattern).parent.glob((P(root) / pattern).name))
                                 if (P(root) / pattern).parent.exists() else []) or [None])[-1],
         lambda pattern, root: newest(root, pattern)),
        ("69abf90773·1支 **按 st_mtime 排序**",
         lambda pattern, root: (sorted(P(root).glob(pattern), key=lambda q: q.stat().st_mtime)
                                or [None])[-1],
         lambda pattern, root: newest(root, pattern, key="mtime")),
        ("c2dc24c114·1支 is_dir 守衛",
         lambda pattern, root: ((sorted(P(root).glob(pattern)) if P(root).is_dir() else []) or [None])[-1],
         lambda pattern, root: newest(root, pattern)),
        # 批591:改走 bind() 的那幾群,逐群再證一次(工廠繞出來的路也要證,不能只證直呼)
        ("bind rp·0cf7954847+229d9eae5e+c2dc24c114 (dirp, pat)",
         lambda pattern, root: (sorted(P(root).glob(pattern)) or [None])[-1],
         lambda pattern, root: bind(order="rp")(root, pattern)),
        ("bind pr·4fbcbc161e+6226e981ca (pat, root)",
         lambda pattern, root: (sorted(P(root).glob(pattern)) or [None])[-1],
         lambda pattern, root: bind(order="pr")(pattern, root)),
        ("bind pr+recursive·814deab1ca rglob",
         lambda pattern, root: (sorted(P(root).rglob(pattern)) or [None])[-1],
         lambda pattern, root: bind(order="pr", recursive=True)(pattern, root)),
        ("bind pr+exclude·358116394a 濾 _sha",
         lambda pattern, root: ([h for h in sorted(P(root).glob(pattern)) if "_sha" not in h.stem]
                                or [None])[-1],
         lambda pattern, root: bind(order="pr", exclude=("_sha",))(pattern, root)),
        ("bind rp+key=mtime·69abf90773",
         lambda pattern, root: (sorted(P(root).glob(pattern), key=lambda q: q.stat().st_mtime)
                                or [None])[-1],
         lambda pattern, root: bind(order="rp", key="mtime")(root, pattern)),
        ("bind rp+on_missing+stringify·2c54462eb1 缺件回 str(folder/pattern)",
         lambda pattern, root: (str(sorted(P(root).glob(pattern))[-1])
                                if sorted(P(root).glob(pattern)) else str(P(root) / pattern)),
         lambda pattern, root: bind(order="rp", on_missing="pattern", stringify=True)(root, pattern)),
        ("bind pr+root_default·8a121a3b6b 只吃一個參數",
         lambda pattern, root: (sorted(P(root).glob(pattern)) or [None])[-1],
         lambda pattern, root: bind(order="pr", root_default=root)(pattern)),
    ]


def selftest() -> int:
    import os
    import tempfile
    n, fails = [0], []

    def chk(label, ok, extra=""):
        n[0] += 1
        print(f"  [{'OK' if ok else 'FAIL'}] {label}" + (f" ({extra})" if extra else ""))
        if not ok:
            fails.append(label)

    # LL133:一把尺不能是它要量的東西的一部分。第一版這三檢是拿**字串**比自己的原始碼,
    # 而檢查標籤裡就寫著 `import requests` / `open(` / `CONSENT` ——三檢當場自己判自己 FAIL。
    # 改成問**語法樹**:比的是真的有沒有那個 import、那個呼叫,不是檔案裡有沒有那幾個字。
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

    api = next(nd for nd in tree.body
               if isinstance(nd, _ast.FunctionDef) and nd.name == "newest")
    writes = {getattr(c.func, "attr", getattr(c.func, "id", "")) for c in _ast.walk(api)
              if isinstance(c, _ast.Call)}
    chk("② 正本零觸碰:對外 API `newest` 只讀不寫(自測在 tempfile 沙盒造語料不算倉內寫)",
        not (writes & {"open", "write_text", "write_bytes", "mkdir", "unlink", "rename",
                       "copy", "copy2", "rmtree", "utime"}),
        f"(呼叫:{sorted(x for x in writes if x)})")

    envset = [nd for nd in _ast.walk(tree)
              if isinstance(nd, _ast.Subscript)
              and getattr(getattr(nd.value, "attr", None), "__str__", str)() == "environ"]
    chk("③ 不代設同意閘:語法樹裡沒有 os.environ[...] 指派(同意閘是操作員的手)",
        not envset and not any(isinstance(nd, _ast.Call)
                               and getattr(nd.func, "attr", "") == "putenv"
                               for nd in _ast.walk(tree)))

    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        (t / "sub").mkdir()
        for name in ("CGC_MDL001_X_v0100.py", "CGC_MDL001_X_v0102.py", "CGC_MDL001_X_v0009.py",
                     "CGC_MDL001_X_v0101_sha.py"):
            (t / name).write_text("#", encoding="utf-8")
        (t / "sub" / "CGC_MDL001_X_v0999.py").write_text("#", encoding="utf-8")
        # mtime 刻意做成**跟版號相反**:v0100 最新。字典序與 mtime 兩把尺在這裡會給不同答案,
        # 這正是要證明的重點——它們本來就不是同一個規則。
        os.utime(t / "CGC_MDL001_X_v0100.py", (10 ** 9, 2 * 10 ** 9))
        os.utime(t / "CGC_MDL001_X_v0102.py", (10 ** 9, 10 ** 9))

        chk("④ 尾版律:同名不同版取版號字典序最後一個(v0102 > v0101 > v0100 > v0009)",
            getattr(newest(t, "CGC_MDL001_X_v0*.py"), "name", None) == "CGC_MDL001_X_v0102.py",
            str(getattr(newest(t, "CGC_MDL001_X_v0*.py"), "name", None)))
        chk("⑤ 缺件回 None(預設)· 回 pattern(on_missing=\"pattern\")",
            newest(t, "NOPE_v*.py") is None
            and newest(t, "NOPE_v*.py", on_missing="pattern") == str(t / "NOPE_v*.py"))
        chk("⑥ 目錄不存在不炸,誠實當作沒有",
            newest(t / "no_such_dir", "*.py") is None)
        chk("⑦ recursive=True 才看子樹(v0999 在 sub/ 底下)",
            getattr(newest(t, "CGC_MDL001_X_v0*.py", recursive=True), "name", None)
            == "CGC_MDL001_X_v0999.py"
            and getattr(newest(t, "CGC_MDL001_X_v0*.py"), "name", None) == "CGC_MDL001_X_v0102.py")
        chk("⑧ exclude 剔掉 stem 命中的(`_sha` 那一支不算尾版)",
            "_sha" not in str(newest(t, "CGC_MDL001_X_v01*.py", exclude=("_sha",))))
        chk("⑨ pattern 帶目錄時自動拆 parent/name",
            getattr(newest(t, "sub/CGC_MDL001_X_v0*.py"), "name", None) == "CGC_MDL001_X_v0999.py")
        chk("⑩ key=\"mtime\" 與 key=\"name\" 在本語料給**不同**答案"
            "(證明它們本來就不是同一把尺,不是同一件事)",
            getattr(newest(t, "CGC_MDL001_X_v010*.py", key="mtime"), "name", None)
            == "CGC_MDL001_X_v0100.py"
            and getattr(newest(t, "CGC_MDL001_X_v010*.py"), "name", None) != "CGC_MDL001_X_v0100.py")
        chk("⑪ key 只收 name/mtime,亂給要當場報錯不默默吃掉",
            _raises(lambda: newest(t, "*.py", key="whatever")))

        # ── 零損失證明:13 群裡有具名差異的 8 種,逐種拿原始實作跟正典對答案 ──
        cases = [("CGC_MDL001_X_v0*.py", t), ("CGC_MDL001_X_v01*.py", t),
                 ("NOPE_v*.py", t), ("*.py", t / "sub"), ("*.py", t / "no_such_dir"),
                 ("sub/CGC_MDL001_X_v0*.py", t)]
        bad = []
        for label, orig, canon in _variants():
            for pattern, root in cases:
                try:
                    a = orig(pattern, root)
                except Exception as exc:
                    a = f"EXC:{type(exc).__name__}"
                try:
                    b = canon(pattern, root)
                except Exception as exc:
                    b = f"EXC:{type(exc).__name__}"
                if str(a) != str(b):
                    bad.append(f"{label} · {pattern} @ {root.name or root} · 原 {a} ≠ 正典 {b}")
        chk(f"⑫ **零損失**:{len(_variants())} 種具名變體 × {len(cases)} 組語料,"
            f"原始實作與正典逐一同解(證不出來的不准遷)",
            not bad, "; ".join(bad[:2]) if bad else f"{len(_variants()) * len(cases)} 組全同")

        # ⑬ 批597:`**` 樣式以前靜默回 None——那不是「沒找到」,是「這支不支援」卻裝成沒找到
        deep = Path(td) / "deep_root" / "a" / "b"
        deep.mkdir(parents=True, exist_ok=True)
        (deep / "Z_v0700.py").write_text("x", encoding="utf-8")
        dr = Path(td) / "deep_root"
        native = sorted(dr.glob("**/*.py"))
        chk("⑬ `**` 樣式與原生 Path.glob 同解(批597 補洞:以前拆 parent/name "
            "會把 `root/**` 當成一個不存在的目錄 → 靜默回 None=假的「沒找到」)",
            bool(native) and newest(dr, "**/*.py") == native[-1],
            f"原生 {native[-1].name if native else '-'} / 正典 "
            f"{getattr(newest(dr, '**/*.py'), 'name', None)}")

        # ⑭ 批597:bind 的 attr/missing —— VDF_ENG073 那一群要的是**檔名**與**空字串**,
        #     stringify=True 給的是整條路徑,分不清就會遷出行為變更
        e73 = bind(order="rp", attr="name", missing="")
        e73_bad = []
        for d, pat in ((Path(td) / "empty_dir", "*.py"), (Path(td), "*.py"), (Path(td), "a_v*.py")):
            d.mkdir(parents=True, exist_ok=True)
            hit = sorted(d.glob(pat))
            ctrl = hit[-1].name if hit else ""          # 對照組=原實作逐字抄
            got = e73(d, pat)
            if ctrl != got or type(ctrl) is not type(got):
                e73_bad.append(f"{d.name}/{pat} 原 {ctrl!r} ≠ 正典 {got!r}")
        chk("⑭ bind(attr=\"name\", missing=\"\") 覆蓋 VDF_ENG073 群(回檔名字串、"
            "缺件回空字串)· attr 亂給要當場報錯",
            not e73_bad and _raises(lambda: bind(attr="parent")),
            "; ".join(e73_bad[:2]) if e73_bad else "三組語料全同")

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
        print(f"=== 尾版取用正典(SUP_MDL751 v{VERSION})· 十四檢自測(零網路;唯讀)===")
        return selftest()
    print(f"SUP_MDL751_VIATailPick v{VERSION} — 尾版取用正典")
    print("  newest(root, pattern, *, recursive=False, exclude=(), on_missing=None, key=\"name\")")
    print("  自測:python3 SUP_MDL751_VIATailPick_v0100.py --selftest")
    return 0


if __name__ == "__main__":
    sys.exit(main())
