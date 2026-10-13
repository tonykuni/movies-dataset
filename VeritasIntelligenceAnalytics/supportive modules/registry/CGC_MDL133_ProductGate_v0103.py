#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL133_ProductGate v0103 — 薄尾:G2「孤梭」誤報修正(R78;Register 薄尾鏈全走 + 梭名大小寫對齊)

R78(2026-10-13 唯讀審計)查到 G2 短令↔梭 長年 WARN 是**假警**;根因兩條,都在 v0102 本體,本版只蓋函式、不改前版一字:
  ① register_fns(text) 只用正則掃「最新一支」Register-VIA-Commands-v*.ps1 的 `function global:via-*`。
     但 Register 自 v0244 起是薄尾鏈:v0278 dot-source v0277 → … → v0243(本體,183 個函式);尾版 v0278 只定義 activate_vdf,
     於是 fns 幾乎是空集合,每一把 .cmd 梭都被算成「孤梭」(orphan = shims - fns),G2 永遠 WARN。
  ② shim_names(folder) 用 folder.glob("via*.cmd"):Windows 的 glob 不分大小寫,VIA-ALL.cmd / VIA-ROOTCHECK.cmd / VIA-TOWER-RESET.cmd
     以大寫字根回來,而 `shims - fns` 是分大小寫的集合差,三把批367 讓位梭(函式 via-all / via-rootcheck / via-tower-reset
     在 Register-VIA-Commands-v0243.ps1 L173 / L174 / L182)永遠對不上;Linux 上 glob 分大小寫,三把大寫梭乾脆不在集合裡。

v0102→v0103 只換兩支,蓋在真正擁有它們的那一版模組上(沿 PRIOR 鏈找 `name in vars(m)`),g2_shims 本體一字不動:
  register_fns_v0103(text=None, root=None):從 root 的 Register 尾版起沿 dot-source 鏈走(只認 `.` 開頭那一行裡的
    Register-VIA-Commands-vNNNN.ps1;註解裡提到的舊版檔名不算)、走到沒有新檔為止、防環;收鏈上每一檔的
    `function global:via-*`(與 v0102 同一條正則,只多 re.I),回小寫名稱。給 text(G2 / G8 傳尾版內文)就從那段內文起走。
  shim_names_v0103(folder=None):同 v0102 的找梭法,但明示不分大小寫(via*.cmd 與 VIA*.cmd 都算、.CMD 也算),以小寫字根去重。
  register_chain_v0103(text=None, root=None):上面兩支的底,回 {files(鏈,由新到舊), fns(鏈上全部 global 函式,小寫,
    含 activate_vdf), via(其中 via* 者), missing(dot-source 指到卻不在的檔)};REGISTER_ROOT_V0103 可暫改預設根(自測用)。
附帶:G8 短令在位 本來就共用 register_fns(同一根因、同一假警),換了底之後跟著看整條鏈;不是另外改 G8。
其餘(G1 · G3–G7 · G9 · key_scan 鑰匙守衛 · build / digest / --json / --open · 頁 + 冊 · 資格律 · ENGINE_TAG)照 v0102,
本版零重定義、零轉綁(自測 ⑤ 釘 key_scan / g6_keys 仍是 v0102 本體)。
用法:python <本檔> --selftest → 七檢(離線);其餘參數原樣交給 v0102 的 main()(它自讀 sys.argv)。
注意:build()(預設動作與 digest)會寫 registry/VIA_ProductGate_v0100.json(受追蹤冊)與產品頁;只看不寫請用 --json。
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

import importlib.util
import re
import sys
import types
from pathlib import Path

ME = Path(__file__).resolve()
HERE = ME.parent
_STEM = "CGC_MDL133_ProductGate"
TAG = "v0103"
REGISTER_GLOB_V0103 = "Register-VIA-Commands-v*.ps1"
REGISTER_ROOT_V0103 = None      # None = 前版的 VIA 根;自測暫指合成夾
_DOT_RX_V0103 = re.compile(r"^\s*\.\s.*?(Register-VIA-Commands-v\d{4}\.ps1)", re.M)   # 只認 dot-source 那一行
_FN_ALL_RX_V0103 = re.compile(r"function global:([\w-]+)", re.I)                     # 鏈上全部 global 函式
_FN_VIA_RX_V0103 = re.compile(r"function global:(via[\w-]*)", re.I)                 # v0102 同式 + re.I


def _vnum_v0103(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0103(p) < _vnum_v0103(ME)), key=_vnum_v0103)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


def _chain_v0103() -> list:
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = getattr(m, "PRIOR", None)
    return out


def _owner_v0103(name: str):
    for m in _chain_v0103():
        if name in vars(m):
            return m
    return None


_OWN_RF = _owner_v0103("register_fns")
_OWN_SN = _owner_v0103("shim_names")
_OWN_KS = _owner_v0103("key_scan")
_OWN_G6 = _owner_v0103("g6_keys")
_ORIG_REGISTER_FNS = _OWN_RF.register_fns if _OWN_RF else None
_ORIG_SHIM_NAMES = _OWN_SN.shim_names if _OWN_SN else None
_ORIG_KEY_SCAN = _OWN_KS.key_scan if _OWN_KS else None
_ORIG_G6 = _OWN_G6.g6_keys if _OWN_G6 else None


# ---------------------------------------------------------------- Register 薄尾鏈(只讀)
def register_chain_v0103(text: str | None = None, root: Path | None = None) -> dict:
    """沿 Register-VIA-Commands 薄尾鏈走到底 → {files, fns, via, missing}。
    text=None:從 root 的尾版(與 v0102 register_tail 同一支 newest)起走;給 text 就當尾版內文起走,root 只用來解析它 dot-source 的檔。
    只認 `.` 開頭那一行裡的 Register-VIA-Commands-vNNNN.ps1(註解提到的舊版不算);同名只走一次(防環);名稱一律小寫。"""
    root = Path(root) if root is not None else Path(REGISTER_ROOT_V0103 or PRIOR.VIA)
    files, fns, via, missing, seen = [], set(), set(), [], set()
    if text is None:
        tail = PRIOR.newest(REGISTER_GLOB_V0103, root)
        if not tail:
            return {"files": files, "fns": fns, "via": via, "missing": missing}
        todo = [(Path(tail).name, None)]
    else:
        todo = [("<text>", text)]
    while todo:
        name, body = todo.pop(0)
        if name in seen:
            continue
        seen.add(name)
        if body is None:
            p = root / name
            if not p.is_file():
                missing.append(name)
                continue
            files.append(p)
            body = p.read_text(encoding="utf-8", errors="ignore")
        fns |= {n.lower() for n in _FN_ALL_RX_V0103.findall(body)}
        via |= {n.lower() for n in _FN_VIA_RX_V0103.findall(body)}
        todo.extend((ref, None) for ref in _DOT_RX_V0103.findall(body) if ref not in seen)
    return {"files": files, "fns": fns, "via": via, "missing": missing}


def register_fns_v0103(text: str | None = None, root: Path | None = None) -> set:
    """蓋 v0102 register_fns(text):收整條 Register 薄尾鏈的 function global:via-*,回小寫名稱(G2 / G8 用)。"""
    return register_chain_v0103(text, root)["via"]


def shim_names_v0103(folder: Path | None = None) -> set:
    """蓋 v0102 shim_names(folder):via*.cmd 與 VIA*.cmd(含 .CMD)都算,以小寫字根去重;夾不在回空集合。"""
    folder = Path(folder) if folder is not None else Path(PRIOR.VIA)
    if not folder.exists():
        return set()
    return {p.stem.lower() for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".cmd" and p.stem.lower().startswith("via")}


def _patch_owners_v0103() -> dict:
    r = {"register_fns": [], "shim_names": []}
    for m in _chain_v0103():                         # 鏈上每個有這兩個名字的模組都換(g2_shims / g8_cmds 以全域名取用)
        if "register_fns" in vars(m):
            m.register_fns = register_fns_v0103
            r["register_fns"].append(Path(m.__file__).stem[-5:])
        if "shim_names" in vars(m):
            m.shim_names = shim_names_v0103
            r["shim_names"].append(Path(m.__file__).stem[-5:])
    return r


PATCHED_V0103 = _patch_owners_v0103()


# ---------------------------------------------------------------- 入口
def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if argv is not None:
        sys.argv = [sys.argv[0]] + a                 # v0102 的 main() 無參數、自讀 sys.argv
    return PRIOR.main()


def selftest() -> int:
    import ast
    import shutil
    import tempfile
    global REGISTER_ROOT_V0103
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s %s · 薄尾自測(R78 G2 孤梭誤報修正;七檢)===" % (_STEM, TAG))
    g2g = getattr(PRIOR.g2_shims, "__globals__", {})
    g8g = getattr(PRIOR.g8_cmds, "__globals__", {})
    chk("① 前版鏈:PRIOR = %s;register_fns / shim_names 的擁有版已換成本版(g2_shims 取用的全域名就是它們)" % PRIOR_PATH.stem,
        0 <= _vnum_v0103(PRIOR_PATH) < _vnum_v0103(ME) and _OWN_RF is not None and _OWN_SN is not None
        and _OWN_RF.register_fns is register_fns_v0103 and _OWN_SN.shim_names is shim_names_v0103
        and g2g.get("register_fns") is register_fns_v0103 and g2g.get("shim_names") is shim_names_v0103
        and g8g.get("register_fns") is register_fns_v0103 and PRIOR.register_fns is register_fns_v0103
        and _ORIG_REGISTER_FNS is not register_fns_v0103 and _ORIG_SHIM_NAMES is not shim_names_v0103,
        "換在 " + str(PATCHED_V0103))
    ch = register_chain_v0103()
    names = [q.name for q in ch["files"]]
    tail = PRIOR.register_tail()
    last_body = ch["files"][-1].read_text(encoding="utf-8", errors="ignore") if ch["files"] else ""
    want = {"via-all", "via-rootcheck", "via-tower-reset", "activate_vdf"}
    chk("② 鏈走到底:從尾版起沿 dot-source 走到 v0243(終點無 dot-source、無缺檔)、收 via-all / via-rootcheck / via-tower-reset / activate_vdf(全小寫)",
        bool(names) and tail is not None and names[0] == Path(tail).name and "Register-VIA-Commands-v0243.ps1" in names and len(names) >= 2
        and not ch["missing"] and not _DOT_RX_V0103.search(last_body) and want <= ch["fns"] and ch["via"] <= ch["fns"]
        and all(n == n.lower() for n in ch["fns"]) and (ch["via"] & want) == want - {"activate_vdf"},
        "%s → … → %s(%d 檔)· 函式 %d(via* %d)· 缺檔 %s" % (names[0] if names else "—", names[-1] if names else "—", len(names), len(ch["fns"]), len(ch["via"]), ch["missing"] or "無"))
    sh = shim_names_v0103(PRIOR.VIA)
    fns = ch["via"]
    three = set(PRIOR.YIELDED_SHIMS)
    orphan = sh - fns
    lack = fns - sh - three
    old_sh = _ORIG_SHIM_NAMES(PRIOR.VIA) if _ORIG_SHIM_NAMES else set()
    chk("③ 梭名小寫:三把大寫梭(VIA-ALL / VIA-ROOTCHECK / VIA-TOWER-RESET)在集合裡、不再是孤梭",
        bool(sh) and all(s == s.lower() for s in sh) and three <= sh and not (three & orphan),
        "梭 %d(v0102 法 %d,含小寫三把 %d)· 函式 %d · 孤梭 %d · 缺梭 %d" % (len(sh), len(old_sh), len(three & old_sh), len(fns), len(orphan), len(lack)))
    td = Path(tempfile.mkdtemp(prefix="pg_v0103_"))
    keep_root = REGISTER_ROOT_V0103
    try:
        v1 = 'function global:via-x { "x" }\n. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0002.ps1")\n'          # 回指尾版 = 環
        v2 = '# 舊版見 Register-VIA-Commands-v0000.ps1(只是註解,不是 dot-source)\n. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0001.ps1")\nfunction global:Activate_Y { }\n'
        (td / "Register-VIA-Commands-v0001.ps1").write_text(v1, encoding="utf-8")
        (td / "Register-VIA-Commands-v0002.ps1").write_text(v2, encoding="utf-8")
        (td / "VIA-X.cmd").write_text("@echo x\n", encoding="utf-8")
        c = register_chain_v0103(None, td)
        REGISTER_ROOT_V0103 = td
        g2 = PRIOR.g2_shims(v2, td)
        REGISTER_ROOT_V0103 = keep_root
        chk("④ 合成鏈(暫存夾):v0002 dot-source v0001、只 v0001 定義 via-x → 鏈找到 via-x;環不卡、註解裡的 v0000 不追;大寫 VIA-X.cmd 配對 → 真 G2 = OK(v0102 法:fns 空、梭看不到 via-x)",
            register_fns_v0103(None, td) == {"via-x"} and register_fns_v0103(v2, td) == {"via-x"} and c["fns"] == {"via-x", "activate_y"}
            and [q.name for q in c["files"]] == ["Register-VIA-Commands-v0002.ps1", "Register-VIA-Commands-v0001.ps1"] and not c["missing"]
            and shim_names_v0103(td) == {"via-x"} and g2["state"] == "OK" and "孤梭" not in g2["evidence"]
            and (_ORIG_REGISTER_FNS(v2) == set() if _ORIG_REGISTER_FNS else False) and ("via-x" not in _ORIG_SHIM_NAMES(td) if _ORIG_SHIM_NAMES else False),
            "G2 %s · %s" % (g2["state"], g2["evidence"][:100]))
    finally:
        REGISTER_ROOT_V0103 = keep_root
        shutil.rmtree(td, ignore_errors=True)
    body = ME.read_text(encoding="utf-8")
    rebind_rx = re.compile(r"\." + "key_scan" + r"\s*=|\." + "g6_keys" + r"\s*=")
    chk("⑤ G6 鑰匙守衛不動:key_scan / g6_keys 仍是 %s 本體(未轉綁、本檔無重定義、g6_keys 取用的 key_scan 仍是原件)" % PRIOR_PATH.stem,
        _OWN_KS is not None and _ORIG_KEY_SCAN is not None and _OWN_KS.key_scan is _ORIG_KEY_SCAN and PRIOR.key_scan is _ORIG_KEY_SCAN
        and PRIOR.g6_keys is _ORIG_G6 and Path(PRIOR.key_scan.__code__.co_filename).resolve() == PRIOR_PATH.resolve()
        and getattr(PRIOR.g6_keys, "__globals__", {}).get("key_scan") is _ORIG_KEY_SCAN
        and "def " + "key_scan" not in body and "def " + "g6_keys" not in body and not rebind_rx.search(body))
    prior_body = PRIOR_PATH.read_text(encoding="utf-8")
    b0, b1 = "[VIA:ACCEL-BRIDGE:v0100]", "[VIA:ACCEL-BRIDGE:END] ====="
    bridge = prior_body[prior_body.index("# ===== " + b0):prior_body.index(b1) + len(b1)]
    tree = ast.parse(body)
    banned = ("sub" + "process", "ur" + "llib", "req" + "uests", "soc" + "ket", "ta" + "lib", "ht" + "tp")
    chk("⑥ 檔頭:from __future__ 第一、加速器橋緊接其後且與 v0102 逐字同;不碰 TA-Lib、不派子行程、零網路",
        body.index("from __future__ import annotations") < body.index("# ===== " + b0) < body.index(b1) and bridge in body
        and not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any(((x.name or "") if isinstance(n, ast.Import) else (n.module or "")).split(".")[0] in banned for x in n.names)
                    for n in ast.walk(tree)))
    print("  ── 前版 %s 自測(原樣跑;頁 / 冊改指暫存夾,不寫追蹤檔)──" % PRIOR_PATH.stem)
    prc = PRIOR.selftest()
    chk("⑦ 前版 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0, "rc " + str(prc))
    print("  [計] %s_%s 薄尾 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
