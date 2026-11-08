#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_LibsInventory v0101 — 薄尾:布建計畫補 PowerShell 版(同一份閉包,只換殼)

**為什麼是薄尾而不是改 v0100**:v0100 已經併進 main 且有一份鎖住的成功收據
(`C-libsinventory-v0100.json`:rc 0 · marker true · 記著當時的來源 SHA)。
就地改它等於讓那份收據指向一支已經不存在的程式 —— 已鎖成功來源要維持原樣(AGENTS.md 四)。
我上一輪就是直接改了 v0100,Codex 在 PR #612 判 P1,判得對。所以還原 v0100,把增補放這裡。

v0100 做的事一行都不重做:全樹 AST 普查 → 冊上五來源對帳 → 十類離線衝突 → 三鏡像布建計畫。
動詞 scan / audit / ui / all 照原樣轉接,本版只換 `plan` 這一段的產物。

本版多出來的只有一件:**計畫同時出 bash 與 PowerShell 兩版**。
倉內本來就有 `scripts/envcheck.ps1`(與 .sh 同功能),桌機是 Windows / PowerShell 7,
只給 bash 等於沒給。順手把踩過的兩個坑寫進計畫:
  ① `$env:VIA_NET_CONSENT` 只活在那一個 PowerShell 視窗,關掉就沒了。
  ② 文件裡的 JSON / 設定片段是**檔案內容,不是指令** —— 貼進提示字元必 ParserError
     (實錄:操作員把 `.mcp.json` 片段貼進去,PowerShell 回「未預期的語彙基元 ':'」。
      那是我把 JSON 當成可貼指令印出來造成的,所以留成一條自測。)

動詞:scan | audit [--apply] | plan | ui | all [--apply] | --selftest
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

# ===== [VIA:NET-BRIDGE:v0100] VIA 網路工具橋(零外呼;本支根本不出網) =====
try:
    import VIA_NetTools_Module as VIA_NET  # noqa: N816
except Exception:
    VIA_NET = None
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "VIA_LibsInventory v" + Path(__file__).stem.rsplit("_v", 1)[-1]
_STEM = "VIA_LibsInventory_v"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{4})\.py$", p.name)
    return int(m.group(1)) if m else -1


def _load_prior():
    """家族前一版(先解析再用,不把版號寫死 → 不踩 PINVER)。"""
    me = _vnum(Path(__file__))
    cands = [p for p in HERE.glob(f"{_STEM}*.py") if -1 < _vnum(p) < me]
    if not cands:
        raise SystemExit(f"[紅] 找不到 {_STEM}*.py 的前版")
    p = sorted(cands, key=_vnum)[-1]
    spec = importlib.util.spec_from_file_location("via_libsinventory_prior", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, p.name


PRIOR, PRIOR_NAME = _load_prior()


def __getattr__(name):
    """PEP 562:本版沒定義的名稱一律轉接前版(薄尾不假裝自己重寫了全部)。"""
    return getattr(PRIOR, name)


# ───────────────────────── PowerShell 版布建段 ─────────────────────────
# 切進點挑「這份計畫沒有做到的事」那個標題之前 —— 和前一輪就地改時的位置一樣,
# 讀計畫的人不用重新找。找不到那個標題就補在最後(不靜默吞掉)。
_ANCHOR = "## 這份計畫沒有做到的事"


def ps_section(book: dict, bl: dict) -> str:
    """R2 的 PowerShell 版:**同一份相依閉包**,只換殼。

    閉包一律向前版要(`env_closure` 的正本在那裡),不在這裡重算 —— 重算就會有兩個正本。
    """
    clo = PRIOR.env_closure(book.get("rows", []), bl) if book.get("rows") is not None else {}
    if not clo:
        clo = {e: list(p) for e, p in (book.get("env_closure") or {}).items()}
    out: list[str] = []
    A = out.append
    A("## R2(Windows PowerShell 版 · 同一份閉包,只換殼)")
    A("")
    A("倉內本來就有 `scripts/envcheck.ps1`(與 .sh 同功能,相容 PowerShell 5.1 / 7),所以桌機直接用這份。")
    A("")
    A("```powershell")
    A('$env:VIA_NET_CONSENT = "YES"   # 同意閘:只有操作員能開')
    A(".\\scripts\\envcheck.ps1 doctor                 # ① 三鏡像連通 + uv cache 體檢")
    A("")
    for env, pkgs in clo.items():
        if not pkgs:
            continue
        py = PRIOR._env_python(env, bl)
        q = " ".join(pkgs)
        A(f"# {env}({len(pkgs)} 件 · python {py})")
        A(f"uv venv {env} --python {py}")
        A(f".\\scripts\\envcheck.ps1 resolve {q}")
        A(f"uv pip install --python {env} {q}")
        A(f"uv pip check --python {env}")
        A("")
    A("```")
    A("")
    A("**PowerShell 的兩個坑**(踩過:操作員把 .mcp.json 的 JSON 片段貼進提示字元,PowerShell 回"
      " ParserError「運算式或陳述式中有未預期的語彙基元 ':'」):")
    A("")
    A("- `$env:VIA_NET_CONSENT` **只活在那一個 PowerShell 視窗**。關掉視窗就沒了,下次要重設。")
    A("  要跨視窗請自己決定是否持久化(`setx`)—— 同意閘要不要常開是操作員的裁量,引擎不代決。")
    A("- 本文件裡的 JSON / 設定片段(例如 `.mcp.json` 的內容)**是檔案內容,不是指令**,")
    A("  貼進提示字元一定 ParserError。只有 ```powershell 區塊裡的那些才是可貼的指令。")
    A("")
    A("")                      # 插入點前留一個空行,不然會貼到下一個標題上
    return "\n".join(out)


def plan_text(book: dict, bl: dict) -> str:
    """前版的計畫 + PowerShell 段。前版那段文字一個字不改。"""
    base = PRIOR.plan_text(book, bl)
    sec = ps_section(book, bl)
    if _ANCHOR in base:
        i = base.index(_ANCHOR)
        return base[:i] + sec + base[i:]
    return base.rstrip("\n") + "\n\n" + sec


def cmd_plan(args) -> int:
    bl, _ = PRIOR.load_baseline()
    book = PRIOR._load_book()
    out = HERE / PRIOR.PLAN_NAME
    out.write_text(plan_text(book, bl), encoding="utf-8")
    print(f"[計畫] {out}(bash + PowerShell 兩版)")
    r = book.get("rounds", {})
    print(f"[輪次] R1 {len(r.get('R1', []))} · R2 {len(r.get('R2', []))} · R3 {len(r.get('R3', []))}")
    return 0


# ───────────────────────── 自測 ─────────────────────────
def selftest() -> int:
    ok = fail = 0

    def chk(name, cond, extra=""):
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"  ✔ {name}")
        else:
            fail += 1
            print(f"  ✘ {name}{(' —— ' + str(extra)) if extra else ''}")

    print(f"[{TAG} 自測 · 薄尾於 {PRIOR_NAME}]")

    # ① 薄尾本分:前版自測仍全過、公開名稱全轉接
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.selftest()
    chk("① 前版自測仍全過(rc 0)", rc == 0, f"rc={rc}")
    for nm in ("norm", "declared_index", "pip_of", "scan_tree", "build_rows", "detect",
               "rounds_assign", "env_closure", "make_book", "write_book", "ui_html",
               "cmd_scan", "cmd_audit", "cmd_ui", "load_baseline", "_env_python"):
        chk(f"② 轉接前版 {nm}", callable(getattr(sys.modules[__name__], nm, None)), nm)

    # ③ v0100 原樣不動:本版沒有改到它(位元比對 —— 這就是 Codex #612 P1 的那條律)
    prior_src = (HERE / PRIOR_NAME).read_bytes()
    chk("③ 前版檔案本版沒碰(薄尾不就地改已鎖成功來源)",
        b"## R2(Windows PowerShell" not in prior_src,
        "前版裡出現了本版該負責的段落 → 代表又就地改了 v0100")

    # ④ 夾具:拿前版自測同一份冊(families 正本鍵是 members)
    fx = {
        "base": {"toolchain": ["uv"], "engine_core": ["duckdb", "numpy"],
                 "low_risk_allow": ["typer"], "never_in_base_families": ["ocr"]},
        "families": {
            "ocr": {"members": ["paddleocr"], "target_env": "via_paddle_311", "python": "3.13"},
            "docs": {"members": ["pymupdf", "pdfplumber"], "target_env": "via_vrn_312", "python": "3.12"},
        },
        "family_env_core": {"via_vrn_312": ["pymupdf", "duckdb"]},
        "package_env_overrides": {},
        "naming_law": {"renames": {}},
        "mirror_chain": {"order": ["https://a/simple", "https://b/simple", "https://pypi.org/simple"],
                         "labels": ["tsinghua", "aliyun", "pypi-official"]},
        "env_layout": {"via_vrn_312": {"python": "3.12"}},
        "rounds": {"max_rounds": 3},
    }
    idx = PRIOR.declared_index(fx)

    def row(imp, pip=None, layer="主層"):
        pip = pip or PRIOR.norm(imp)
        return {"import": imp, "pip": pip, "mapped": True, "layer": layer,
                "declared": idx.get(pip, []), "nfiles": 1, "lanes": ["VDF"]}

    rr = [row("pymupdf", layer="ABSENT"), row("paddleocr", layer="主層")]
    bk = PRIOR.make_book(rr, PRIOR.detect(rr, fx), fx, "fx.json", 7)
    pt = plan_text(bk, fx)
    base_pt = PRIOR.plan_text(bk, fx)

    # ⑤ 前版那段一個字不改(新段是「插進去」,不是「改寫」)
    chk("⑤ 前版計畫的每一行都還在(只插入,不改寫)",
        all(ln in pt for ln in base_pt.splitlines() if ln.strip()))
    chk("⑥ 兩版都出:bash 的 envcheck.sh 與 PowerShell 的 envcheck.ps1",
        "envcheck.sh" in pt and "envcheck.ps1" in pt)
    chk("⑦ PowerShell 版用 .ps1 不用 .sh(不要叫 Windows 跑 bash)",
        ".\\scripts\\envcheck.ps1 doctor" in pt)
    chk("⑧ 新段插在「沒有做到的事」之前(位置和讀的人預期的一樣)",
        _ANCHOR in pt and pt.index("## R2(Windows PowerShell") < pt.index(_ANCHOR))
    chk("⑧b 插入處留空行(不貼到下一個標題上)", "\n\n" + _ANCHOR in pt)

    # ⑨–⑩ 兩個踩過的坑都寫進計畫
    chk("⑨ 提醒 $env: 只活在那一個視窗(關掉同意閘就沒了)",
        "只活在那一個 PowerShell 視窗" in pt)
    chk("⑩ 提醒設定片段不是指令(JSON 貼進提示字元會 ParserError)",
        "是檔案內容,不是指令" in pt and "ParserError" in pt)

    # ⑪ 同一份閉包:bash 段與 PowerShell 段裝的套件完全一樣(只換殼,不換內容)
    def pkgs_after(marker: str, text: str) -> set[str]:
        seg = text.split(marker, 1)[1]
        got: set[str] = set()
        for ln in seg.splitlines():
            if ln.startswith("uv pip install --python "):
                got |= set(ln.split()[4:])
        return got
    bash_pkgs = pkgs_after("## R2", base_pt)
    ps_pkgs = pkgs_after("## R2(Windows PowerShell", pt)
    chk("⑪ PowerShell 段與 bash 段的套件集合完全一致(同一份閉包)",
        bash_pkgs == ps_pkgs and bash_pkgs, f"bash={sorted(bash_pkgs)} ps={sorted(ps_pkgs)}")
    chk("⑫ PowerShell 段的 python 版本也照冊上取",
        all(f"--python {v['python']}" in pt for v in fx["env_layout"].values()))

    # ⑬ 同意閘仍然留給操作員(本版不代設)
    import ast as _ast
    tree = _ast.parse(Path(__file__).read_text(encoding="utf-8"))
    wrote_env = [1 for n in _ast.walk(tree)
                 if isinstance(n, _ast.Assign)
                 and any(isinstance(t, _ast.Subscript) and isinstance(t.value, _ast.Attribute)
                         and t.value.attr == "environ" for t in n.targets)]
    chk("⑬ 不代設同意閘(AST:沒有一處寫 os.environ[...])", not wrote_env)
    calls = [n for n in _ast.walk(tree) if isinstance(n, _ast.Call)
             and isinstance(n.func, _ast.Attribute) and n.func.attr in ("run", "Popen",
                                                                        "check_call", "system")]
    chk("⑭ 本版不派任何子行程、不裝任何東西", not calls, len(calls))
    imported = {a.name.split(".")[0] for n in _ast.walk(tree) if isinstance(n, _ast.Import)
                for a in n.names}
    chk("⑮ 不碰 TA-Lib", not {"talib", "ta_lib"} & imported, sorted(imported))

    print(f"[計] {TAG} 自測 OK {ok} · FAIL {fail} · {'PASS' if fail == 0 else 'FAIL'}")
    return 0 if fail == 0 else 1


# ───────────────────────── 入口 ─────────────────────────
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=f"{TAG}(薄尾:計畫補 PowerShell 版)")
    ap.add_argument("verb", nargs="?", default="audit",
                    choices=["scan", "audit", "plan", "ui", "all"])
    ap.add_argument("--apply", action="store_true", help="真的寫盤冊")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(list(sys.argv[1:] if argv is None else argv))
    if a.selftest:
        return selftest()
    if a.verb == "scan":
        return PRIOR.cmd_scan(a)
    if a.verb == "audit":
        return PRIOR.cmd_audit(a)
    if a.verb == "plan":
        return cmd_plan(a)
    if a.verb == "ui":
        return PRIOR.cmd_ui(a)
    rc = PRIOR.cmd_audit(a)
    return rc or cmd_plan(a) or PRIOR.cmd_ui(a)


if __name__ == "__main__":
    sys.exit(main())
