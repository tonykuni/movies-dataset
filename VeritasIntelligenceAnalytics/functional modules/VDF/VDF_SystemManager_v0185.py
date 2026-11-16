#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0185 — 薄尾:引擎矩陣加兩欄 accel · net(每個引擎檔有沒有掛上加速器 / 網路工具,掛的是不是鎖冊上最新那一支)。

操作員 2026-11-16:「add the latest accelerator / web toolkit to cover 100% of the engines · add one more column in matrix monitor
to detect if they are employed with the latest accelerators and the web toolkit」。
本版(前版 v0184 一字不動;只換引擎矩陣的欄位表與登記函式兩個名字):
  · accel 欄:語法樹裡真的有 `import VIA_SuperAccel_Module`(不看字串 / 註解)+ 本行程載得到 + 鎖冊上的加速器檔在
      → 「生效 <鎖冊上的加速器檔名> · 標 vNNNN」;只有標記沒有匯入 → 「只有標記」;都沒有 → 「缺」;載不到 → 「載不到」。
  · net 欄:語法樹裡有網路橋(VIA_NET_TOOL_PATH 指派 + 以 via_net_unified 找檔的呼叫)→ 「生效 <網路工具檔名>」;
      沒有橋但匯入了會出網的套件(requests · httpx · urllib.request · yfinance …,含 __import__ / import_module 的延遲匯入)→ 「缺(會出網:…)」;
      沒有橋也不出網 → 「不出網」(不需要,不算缺)。
  · 總結只算尾版:加速器缺 = 紅;會出網卻沒有網路橋 = 紅(VDF 強制網路工具)。舊版號檔照實列出、不計燈(已發布的檔不就地改)。
  · JSON / CSV / HTML 三份登記冊都多這兩欄;`engine-matrix` 動詞多印一行覆蓋率並點名。
只讀自己系統的夾;鎖冊只讀(VCGC 自報)。零網路 · 不碰 TA-Lib · 不讀寫同意閘。號:前版 v0184;本版 v0185。
用法同前版;自測 python VDF_SystemManager_v0185.py --selftest。
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
import ast
import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
TAG = "v0185"
DISPLAY_NAME = "VDF SystemManager"
FAMILY = "VDF_SystemManager"
NEED_NET = True                         # True:會出網卻沒有網路橋 = 紅;False:只報黃
NEW_COLS = ("accel", "net")
ACCEL_MOD = "VIA_SuperAccel_Module"
NET_TOP = {"requests", "urllib3", "httpx", "aiohttp", "curl_cffi", "yfinance", "websocket", "websockets", "ftplib", "akshare", "fredapi",
           "pandas_datareader", "cloudscraper", "selenium", "playwright"}
NET_FULL = ("urllib.request", "http.client")
SOCK_CALLS = {"create_connection", "connect_ex", "sendto", "sendall", "gethostbyname", "getaddrinfo"}   # 只匯入 socket 不算出網;真的開連線才算
_STAMP = re.compile(r"\[VIA:ACCEL-BRIDGE:v(\d{4})\]")
_LAST = {"bridge": None}


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, "vdf_manager_prior_for_" + TAG)


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(PRIOR, name)


def _owner(name: str):
    m, seen = PRIOR, []
    while m is not None and m not in seen:
        if name in vars(m):
            return m
        seen.append(m)
        m = vars(m).get("PRIOR")
    return None


EMO = _owner("EM_COLS")                          # 引擎矩陣欄位表所在的那一版(em_csv / em_html 從它的模組上找 EM_COLS)
EM_CFG = _owner("EM_CFG").EM_CFG
_ORIG = {}


def _reg_modules() -> list:
    """前版鏈上每一個自己有 em_register 名字的模組(矩陣動詞與靜默登記各從不同模組上找它,所以每個都要換)。"""
    out, m, seen = [], PRIOR, []
    while m is not None and m not in seen:
        if callable(vars(m).get("em_register")):
            out.append(m)
        seen.append(m)
        m = vars(m).get("PRIOR")
    return out


# ────────────────── 語法樹判讀(不看字串 / 註解)──────────────────
def _netlib(name: str, libs: set) -> None:
    name = name or ""
    if name.split(".")[0] in NET_TOP:
        libs.add(name.split(".")[0])
    for full in NET_FULL:
        if name == full or name.startswith(full + "."):
            libs.add(full)


def bridge_scan(text: str) -> dict:
    out = {"syntax": True, "accel_import": False, "stamp": None, "net_bridge": False, "net_libs": []}
    marks = [int(x) for x in _STAMP.findall("\n".join(text.splitlines()[:80]))]
    out["stamp"] = ("v%04d" % max(marks)) if marks else None
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        out["syntax"] = False
        return out
    libs, net_assign, net_call, sock_use, sock_imp = set(), False, False, False, False
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                out["accel_import"] = out["accel_import"] or a.name == ACCEL_MOD
                sock_imp = sock_imp or a.name == "socket"
                _netlib(a.name, libs)
        elif isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            out["accel_import"] = out["accel_import"] or mod == ACCEL_MOD
            sock_imp = sock_imp or mod == "socket"
            _netlib(mod, libs)
            for a in n.names:
                _netlib(mod + "." + a.name, libs)
        elif isinstance(n, ast.Call):
            fn = n.func.id if isinstance(n.func, ast.Name) else (n.func.attr if isinstance(n.func, ast.Attribute) else "")
            args = list(n.args) + [k.value for k in n.keywords]
            consts = [a.value for a in args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            net_call = net_call or any("via_net_unified" in c.lower() for c in consts)
            if fn in ("__import__", "import_module") and consts:
                _netlib(consts[0], libs)
            recv = n.func.value.id if isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) else ""
            if fn in SOCK_CALLS or (fn == "socket" and (recv or isinstance(n.func, ast.Name))):
                sock_use = True
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            net_assign = net_assign or any(isinstance(t, ast.Name) and t.id == "VIA_NET_TOOL_PATH" for t in targets)
    if sock_imp and sock_use:
        libs.add("socket")
    out["net_bridge"] = bool(net_assign and net_call)
    out["net_libs"] = sorted(libs)
    return out


def runtime(root=None) -> dict:
    """鎖冊上最新的加速器 / 網路工具(只讀)+ 本行程載不載得到加速器橋。"""
    root = Path(root or VIA_ROOT)
    out = {"accel_loaded": VIA_ACCEL is not None, "accel_tool": None, "net_tool": None, "lock": None}
    locks = sorted((root / "supportive modules" / "registry").glob("VIA_ToolVersion_Lock_v*.json"))
    book = {}
    if locks:
        out["lock"] = locks[-1].name
        try:
            book = json.loads(locks[-1].read_text(encoding="utf-8"))
        except (OSError, ValueError):
            book = {}
    for fam, key in (("accelerator", "accel_tool"), ("network", "net_tool")):
        rel = str((book.get(fam) or {}).get("path") or "")
        if rel and (root.parent / rel).is_file():
            out[key] = Path(rel).stem
    return out


def verdict(scan: dict, rt: dict) -> tuple:
    if not scan["syntax"]:
        return "語法錯", "語法錯"
    stamp = " · 標 " + (scan["stamp"] or "無")
    if scan["accel_import"]:
        accel = ("生效 " + rt["accel_tool"] + stamp) if (rt["accel_loaded"] and rt["accel_tool"]) else ("載不到" + stamp)
    else:
        accel = "只有標記" if scan["stamp"] else "缺"
    if scan["net_bridge"]:
        net = ("生效 " + rt["net_tool"]) if rt["net_tool"] else "載不到"
    elif scan["net_libs"]:
        net = "缺(會出網:" + ",".join(scan["net_libs"][:3]) + ")"
    else:
        net = "不出網"
    return accel, net


def decorate(summary, root):
    """登記冊三份檔補上 accel / net 兩欄與覆蓋總結(只算尾版)。"""
    files = (summary or {}).get("files") or {}
    jp = Path(files.get("json") or "")
    if not jp.is_file():
        return summary
    body = json.loads(jp.read_text(encoding="utf-8"))
    rt = runtime(root if (Path(root) / "supportive modules").is_dir() else None)
    rows = body.get("rows") or {}
    acc_bad, net_bad, acc_ok, net_ok, net_na, tails = [], [], 0, 0, 0, 0
    for key, r in rows.items():
        if r.get("state") == "消失":
            r["accel"], r["net"] = "", ""
            continue
        p = Path(root) / str(r.get("path") or "")
        try:
            sc = bridge_scan(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            r["accel"], r["net"] = "讀不到", "讀不到"
            continue
        r["accel"], r["net"] = verdict(sc, rt)
        if r.get("tail"):
            tails += 1
            acc_ok += r["accel"].startswith("生效")
            net_ok += r["net"].startswith("生效")
            net_na += r["net"] == "不出網"
            if not r["accel"].startswith("生效"):
                acc_bad.append("%s(%s)" % (key, r["accel"].split(" · ")[0]))
            if not (r["net"].startswith("生效") or r["net"] == "不出網"):
                net_bad.append("%s(%s)" % (key, r["net"]))
    br = {"tails": tails, "accel_ok": acc_ok, "accel_bad": acc_bad, "net_ok": net_ok, "net_not_needed": net_na, "net_bad": net_bad,
          "accel_tool": rt["accel_tool"], "net_tool": rt["net_tool"], "accel_loaded": rt["accel_loaded"], "lock": rt["lock"], "need_net": NEED_NET,
          "lamp": "RED" if (acc_bad or (net_bad and NEED_NET)) else ("YELLOW" if net_bad else ("GREEN" if tails else "GRAY"))}
    summ = dict(body.get("summary") or {})
    summ["bridge"] = br
    order = {"GRAY": 0, "GREEN": 1, "YELLOW": 2, "RED": 3}
    if order.get(br["lamp"], 0) > order.get(summ.get("lamp"), 0):
        summ["lamp"] = br["lamp"]
    body["summary"] = summ
    EMO.em_write(jp, json.dumps(body, ensure_ascii=False, indent=1))
    if files.get("csv"):
        EMO.em_write(Path(files["csv"]), EMO.em_csv(body), bom=True)
    if files.get("html"):
        EMO.em_write(Path(files["html"]), EMO.em_html(body))
    out = dict(summary)
    out["bridge"], out["lamp"] = br, summ["lamp"]
    _LAST["bridge"] = br
    return out


def _wrap(orig):
    def em_register(root, *a, **k):
        summ = orig(root, *a, **k)
        try:
            return decorate(summ, root)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:      # 補欄失敗不擋登記本身,照實記在摘要上
            if isinstance(summ, dict):
                summ["bridge_error"] = "%s:%s" % (type(exc).__name__, str(exc)[:120])
            return summ
    em_register._bridge_cols = True
    return em_register


def _installed() -> bool:
    mods = _reg_modules()
    return bool(mods) and all(getattr(m.em_register, "_bridge_cols", False) for m in mods)


def install() -> None:
    if _ORIG:
        return
    if callable(vars(PRIOR).get("install")):
        PRIOR.install()
    _ORIG.update(regs=[(m, m.em_register) for m in _reg_modules()], cols=EMO.EM_COLS)
    for m, fn in _ORIG["regs"]:
        m.em_register = _wrap(fn)
    EMO.EM_COLS = tuple(c for c in _ORIG["cols"] if c != "path") + NEW_COLS + tuple(c for c in _ORIG["cols"] if c == "path")


def uninstall() -> None:
    if not _ORIG:
        return
    for m, fn in _ORIG["regs"]:
        m.em_register = fn
    EMO.EM_COLS = _ORIG["cols"]
    _ORIG.clear()


install()


def bridge_line(br: dict) -> str:
    if not br:
        return "[橋] 這一輪沒有量到(登記冊沒寫出來)"
    s = "[橋] %s · 尾版 %d · 加速器生效 %d/%d(%s)· 網路工具 生效 %d · 不出網 %d · 缺 %d(%s)" % (
        br["lamp"], br["tails"], br["accel_ok"], br["tails"], br["accel_tool"] or "鎖冊上的加速器檔不在", br["net_ok"], br["net_not_needed"],
        len(br["net_bad"]), br["net_tool"] or "鎖冊上的網路工具檔不在")
    if br["accel_bad"]:
        s += "\n  加速器沒生效:" + " · ".join(br["accel_bad"][:30])
    if br["net_bad"]:
        s += "\n  會出網卻沒有網路橋:" + " · ".join(br["net_bad"][:30])
    return s


# ────────────────── 動詞 ──────────────────
def collect() -> dict:
    """VCGC 子系統對接口(照前版 · 只讀)· served_by 記本版 · 多帶橋覆蓋總結。"""
    out = PRIOR.collect()
    if isinstance(out, dict):
        out = dict(out)
        sb = dict(out.get("served_by") or {})
        sb["tail"] = FAMILY + "_" + TAG
        out["served_by"] = sb
        if _LAST["bridge"]:
            out["bridge"] = _LAST["bridge"]
    return out


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"] or "--selftest" in args[:1]:
        return selftest()
    rc = PRIOR.main(args)
    if args[:1] == ["engine-matrix"]:
        br = _LAST["bridge"]
        print(bridge_line(br), file=sys.stderr if "--json" in args else sys.stdout, flush=True)
        if br and br["lamp"] == "RED":
            return 1
        if br and br["lamp"] == "YELLOW":
            return max(int(rc or 0), 2)
    return rc


def selftest() -> int:
    print("[計] %s %s 自測開始(本版 + 前版 %s)" % (DISPLAY_NAME, TAG, PRIOR_PATH.name), flush=True)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)
    blk = "# [VIA:ACCEL-BRIDGE:v0111]\ntry:\n    import " + ACCEL_MOD + " as VIA_ACCEL\nexcept Exception:\n    VIA_ACCEL = None\n"
    netb = ("VIA_NET_TOOL_PATH = None\ntry:\n    from pathlib import Path as _p\n    _h = sorted(_p('.').glob('via_net_unified_v*.py'))\n"
            "    VIA_NET_TOOL_PATH = str(_h[-1]) if _h else None\nexcept Exception:\n    VIA_NET_TOOL_PATH = None\n")
    a = bridge_scan(blk + "x = 1\n")
    b = bridge_scan("# [VIA:ACCEL-BRIDGE:v0111]\ns = 'import " + ACCEL_MOD + "'\n")
    c = bridge_scan('"""文件裡提到 via_net_unified 與 import requests"""\nVIA_NET_TOOL_PATH = None\nx = "requests"\n')
    d = bridge_scan(blk + netb + "import requests\n")
    e = bridge_scan(blk + "import json\ndef f():\n    import urllib.request\n    m = __import__('yfinance')\n    from urllib import parse\n")
    f = bridge_scan("def (:\n")
    g = bridge_scan("import socket as _sk\n_o = _sk.socket.connect\n_sk.socket.connect = lambda *a: None\n")
    h = bridge_scan("import socket\ns = socket.socket()\ns.connect(('h', 1))\n")
    chk("B1 加速器看語法樹:真的 import 才算 · 字串裡寫 import 不算(只有標記)· 標記版號讀得到",
        a["accel_import"] and a["stamp"] == "v0111" and not b["accel_import"] and b["stamp"] == "v0111")
    chk("B2 網路橋看語法樹:指派 + 找檔呼叫才算 · 文件字串 / 空指派 / 字串 'requests' 不算橋也不算出網",
        d["net_bridge"] and d["net_libs"] == ["requests"] and not c["net_bridge"] and c["net_libs"] == [])
    chk("B3 會出網的套件:函式內匯入 · __import__ 延遲匯入 · urllib.request 都抓到;urllib.parse 不算;只匯入 socket 來擋連線不算、真的開 socket 才算",
        e["net_libs"] == ["urllib.request", "yfinance"] and not e["net_bridge"] and g["net_libs"] == [] and h["net_libs"] == ["socket"],
        (e["net_libs"], g["net_libs"], h["net_libs"]))
    rt = {"accel_loaded": True, "accel_tool": "ACC_v9", "net_tool": "NET_v9"}
    chk("B4 判讀:生效帶工具檔名與標記 · 只有標記 · 缺 · 載不到 · 會出網沒橋 = 缺 · 不出網不算缺 · 語法錯照實",
        verdict(a, rt) == ("生效 ACC_v9 · 標 v0111", "不出網") and verdict(b, rt)[0] == "只有標記" and verdict(c, rt) == ("缺", "不出網")
        and verdict(d, rt)[1] == "生效 NET_v9" and verdict(e, rt)[1] == "缺(會出網:urllib.request,yfinance)"
        and verdict(a, dict(rt, accel_loaded=False))[0].startswith("載不到") and verdict(f, rt) == ("語法錯", "語法錯"),
        (verdict(a, rt), verdict(e, rt)))
    install()
    chk("B5 換裝在位:鏈上每個 em_register 都是本版 · 欄位表多 accel / net(path 仍在最後)",
        _installed() and EMO.EM_COLS[-3:] == ("accel", "net", "path"))
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        own = root / EM_CFG["dir"]
        own.mkdir(parents=True)
        pre = EM_CFG["prefixes"][0]
        (own / (pre + "ENG951_Good_v0100.py")).write_text(blk + "x = 1\n", encoding="utf-8")
        (own / (pre + "ENG952_NoAccel_v0100.py")).write_text("x = 1\n", encoding="utf-8")
        (own / (pre + "ENG953_NetNoBridge_v0100.py")).write_text(blk + "import requests\n", encoding="utf-8")
        (own / (pre + "ENG954_NetOk_v0100.py")).write_text(blk + netb + "import requests\n", encoding="utf-8")
        (own / (pre + "ENG954_NetOk_v0099.py")).write_text("x = 0\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = EMO.em_cmd(["--no-git"], root)
        od = _owner("em_out_dir").em_out_dir(root)
        stem = EM_CFG.get("stem", EM_CFG["system"])
        data = json.loads((od / ("%s_EngineMatrix_latest.json" % stem)).read_text(encoding="utf-8"))
        csv_head = (od / ("%s_EngineMatrix_latest.csv" % stem)).read_text(encoding="utf-8-sig").splitlines()[0]
        page = (od / ("%s_EngineMatrix_latest.html" % stem)).read_text(encoding="utf-8")
    rows = data.get("rows") or {}
    get = lambda n: next((r for k, r in rows.items() if n in k and r.get("tail")), {})          # noqa: E731
    br = (data.get("summary") or {}).get("bridge") or {}
    chk("B6 實跑 engine-matrix(暫存夾):每列有 accel / net · 缺的點名 · 舊版號列照列但不計燈 · 三份檔都多兩欄",
        rc in (0, 2) and get("ENG951").get("accel") in ("缺", "載不到 · 標 v0111") or get("ENG951").get("accel", "").startswith(("生效", "載不到"))
        and get("ENG952").get("accel") == "缺" and get("ENG953").get("net", "").startswith("缺(會出網") and get("ENG951").get("net") == "不出網"
        and br.get("tails") == 4 and any("ENG952" in x for x in br.get("accel_bad", [])) and any("ENG953" in x for x in br.get("net_bad", []))
        and not any("v0099" in x for x in br.get("accel_bad", [])) and all("accel" in r and "net" in r for r in rows.values())
        and ",accel,net," in csv_head and "<th>accel</th>" in page and "<th>net</th>" in page, (br, csv_head))
    chk("B7 總燈:加速器缺 = 紅" + (";會出網沒網路橋 = 紅" if NEED_NET else ";會出網沒網路橋只報黃(本系統只強制加速器)"),
        br.get("lamp") == "RED" and (data.get("summary") or {}).get("lamp") == "RED" and "加速器沒生效" in bridge_line(br))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("B8 檔面:第 3 行加速器標記 · 自己的語法樹量得到加速器橋 · 零 TA-Lib · 不寫同意閘 · 沒有本機路徑",
        text.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and bridge_scan(text)["accel_import"] and not bridge_scan(text)["net_libs"]
        and "import " + "talib" not in text and "_CONSENT\"] " + "=" not in text and "/" + "home/" not in text and "\\" + "Users" not in text)
    print("  ── 前版 %s 自測(本版換裝卸下)──" % PRIOR_PATH.name, flush=True)
    uninstall()
    try:
        prior_rc = int(PRIOR.selftest() or 0)
    finally:
        install()
    chk("B9 前版 %s 自測照過 · 跑完本版又換上" % PRIOR_PATH.name, prior_rc == 0 and _installed(), prior_rc)
    n = sum(ok)
    print("[計] %s %s(%s_%s.py)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, FAMILY, TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["provenance"] and callable(getattr(PRIOR, "provenance", None)):     # 同前版:provenance 先於任何 --selftest 攔截
        sys.exit(PRIOR.provenance(sys.argv[2:]))
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))
