#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_dep_super_v0101 — 依賴衝突統包引擎(TOOL-031;操作員令 2026-08-12)
=======================================================================
令:TOP 10 本地免費依賴工具 + 官方/清華/阿里三鏡像,統包一引擎(SUPER ENGINE)。
十械三防線編成(工具在則接管;缺則內建替補頂上——零安裝也能診):
  第一防線·解析主幹(源頭預防):uv / Poetry / PDM / Conda·Mamba
  第二防線·診斷照妖(衝突檢測):pipdeptree / pip check / pip-tools / Snyk CLI
     內建替補:importlib.metadata 全圖譜 + PEP 440 判定器(packaging→
     pip._vendor→迷你三層)——pip check 同義掃描+樹狀溯源,十械全缺照樣出診
  第三防線·隔離防污(多版本):pyenv(解譯器)/ Tox·Nox(執行期矩陣)
鏡像三源:official(pypi.org)/ tsinghua(清華 TUNA)/ aliyun(阿里雲)
v0100→v0101:多層同名顯示帶可辨識路徑段(實戰 672 件 base 顯示
site-packages/site-packages 分不出使用者層 vs 系統層之修)。
方法:全程唯讀零改動;裁決只印執行令不代決(候裁);安裝一律 via-plan→via-install
紅線:零安裝零落地零改組態;鏡像測速屬網路行為過同意閘(VIA_NET_CONSENT=YES;
     未同意=NOT_RUN 誠實);Snyk 只列執行令不代跑(需自備免費帳號)
用法:via-deps                     → 全景:十械矩陣+快照+衝突掃描+交叉印證+鏡像+裁決
     via-deps --why <套件>        → 逆向溯源(誰引入它;pipdeptree -r 同義內建)
     via-deps --tree <套件>       → 正向依賴樹(深度 3;互撞/缺件直標)
     via-deps --mirror            → 鏡像現況(唯讀零網路)
     via-deps --mirror-test       → 三鏡像測速排名(網路;同意閘)
     via-deps --mirror-set <源>   → 切源執行令 official/tsinghua/aliyun(不代寫)
     via-deps --preset <場景>     → 場景編成 web/ai/script(+引導安裝執行令)
     via-deps --matrix            → Tox/Nox 多版本矩陣骨架(執行期衝突實測)
     via-deps --selftest          → 內建判定器 15 檢(零網路零環境依賴)
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "depsuper_runs"
PYCMD = "py" if os.name == "nt" else "python3"


def _via_load(name: str):
    try:
        sys.path.insert(0, str(VIA / "supportive modules"))
        from VRN_SupportBridge import require  # type: ignore
        return require(name)
    except Exception:
        try:
            import importlib
            sys.path.insert(0, str(VIA / "supportive modules"))
            return importlib.import_module(name)
        except Exception:
            return None


_NET = _via_load("VIA_NetSupport")


def _consent() -> bool:
    try:
        if _NET:
            return bool(_NET.net_consent())
    except Exception:
        pass
    return os.environ.get("VIA_NET_CONSENT", "").upper() in ("YES", "1", "TRUE")


def canon(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


# ── PEP 440 迷你判定器(第三層替補;packaging 全缺時獨挑)─────────────
_PRE_RANK = {"a": 0, "alpha": 0, "b": 1, "beta": 1, "c": 2, "rc": 2, "pre": 2, "preview": 2}
_VER_RX = re.compile(
    r"^v?(?:(\d+)!)?(\d+(?:\.\d+)*)"
    r"(?:[-_.]?(a|b|c|rc|alpha|beta|pre|preview)[-_.]?(\d*))?"
    r"(?:[-_.]?(?:post|rev|r)[-_.]?(\d*)|-(\d+))?"
    r"(?:[-_.]?dev[-_.]?(\d*))?"
    r"(?:\+([a-z0-9]+(?:[-_.][a-z0-9]+)*))?$", re.I)


def _mini_rel_raw(v: str) -> tuple:
    m = _VER_RX.match(v.strip().lower())
    if not m:
        raise ValueError(v)
    return tuple(int(x) for x in m.group(2).split("."))


def _mini_key(v: str) -> tuple:
    m = _VER_RX.match(v.strip().lower())
    if not m:
        raise ValueError(v)
    epoch = int(m.group(1) or 0)
    rel = tuple(int(x) for x in m.group(2).split("."))
    while len(rel) > 1 and rel[-1] == 0:
        rel = rel[:-1]
    pre_l, pre_n = m.group(3), m.group(4)
    post_n = m.group(5) if m.group(5) is not None else m.group(6)
    dev_n = m.group(7)
    if pre_l is None and post_n is None and dev_n is not None:
        pre_k = (-2,)  # 1.0.dev1 < 1.0a1
    elif pre_l is None:
        pre_k = (1,)
    else:
        pre_k = (-1, _PRE_RANK[pre_l], int(pre_n or 0))
    post_k = (0, int(post_n or 0)) if post_n is not None else (-1,)
    dev_k = (0, int(dev_n or 0)) if dev_n is not None else (1,)
    return (epoch, rel, pre_k, post_k, dev_k)


def _mini_cmp(a: str, b: str) -> int:
    ka, kb = _mini_key(a), _mini_key(b)
    return (ka > kb) - (ka < kb)


def _mini_contains(spec: str, ver: str) -> bool:
    for clause in [c.strip() for c in spec.split(",") if c.strip()]:
        m = re.match(r"^(===|==|!=|<=|>=|~=|<|>)\s*(.+?)\s*$", clause)
        if not m:
            raise ValueError(clause)
        op, target = m.group(1), m.group(2)
        if op == "===":
            if ver.strip() != target:
                return False
            continue
        if target.endswith(".*") and op in ("==", "!="):
            want = _mini_rel_raw(target[:-2])
            got = _mini_rel_raw(ver)
            got = (got + (0,) * len(want))[:len(want)]
            if (op == "==") != (got == want):
                return False
            continue
        if op == "~=":
            want = _mini_rel_raw(target)
            if len(want) < 2:
                raise ValueError(clause)
            if _mini_cmp(ver, target) < 0:
                return False
            got = _mini_rel_raw(ver)
            got = (got + (0,) * (len(want) - 1))[:len(want) - 1]
            if got != want[:-1]:
                return False
            continue
        c = _mini_cmp(ver, target)
        if not {"==": c == 0, "!=": c != 0, ">=": c >= 0, "<=": c <= 0, ">": c > 0, "<": c < 0}[op]:
            return False
    return True


def _pep440():
    """判定器三層:packaging → pip._vendor.packaging → 迷你(誠實標示來源)。"""
    import importlib
    for mod, tag in (("packaging", "packaging"), ("pip._vendor.packaging", "pip._vendor")):
        try:
            V = importlib.import_module(mod + ".version")
            S = importlib.import_module(mod + ".specifiers")
            return tag, (lambda spec, ver, _V=V, _S=S:
                         _S.SpecifierSet(spec).contains(_V.Version(ver), prereleases=True))
        except Exception:
            continue
    return "迷你替補", _mini_contains


# ── 需求解析 + 環境標記求值(Requires-Dist 全式)──────────────────
_REQ_RX = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(\[[^\]]*\])?\s*(.*)$")
_TOK_RX = re.compile(
    r'"[^"]*"|\'[^\']*\'|\(|\)|===|==|!=|<=|>=|~=|<|>|\bnot\s+in\b|\bin\b|\band\b|\bor\b|[A-Za-z_][A-Za-z0-9_.]*')


def parse_req(raw: str):
    """一條 Requires-Dist → (canon 名, 規格串, 標記串|None);解析不了→None(誠實計數)。"""
    body, _, marker = raw.partition(";")
    m = _REQ_RX.match(body.strip())
    if not m:
        return None
    spec = m.group(3).strip()
    if spec.startswith("(") and spec.endswith(")"):
        spec = spec[1:-1].strip()
    if spec.startswith("@"):
        spec = ""  # URL 直指:不判版本
    return (canon(m.group(1)), spec, marker.strip() or None)


def _marker_env() -> dict:
    import platform
    return {
        "python_version": ".".join(platform.python_version_tuple()[:2]),
        "python_full_version": platform.python_version(),
        "sys_platform": sys.platform,
        "platform_system": platform.system(),
        "platform_machine": platform.machine(),
        "platform_python_implementation": platform.python_implementation(),
        "implementation_name": sys.implementation.name,
        "os_name": os.name,
        "platform_release": platform.release(),
        "extra": "",  # 不知安裝時所點 extra——extra 條件一律跳(與 pip check 同義)
    }


def eval_marker(marker: str, env: dict) -> bool:
    """極簡標記求值(and/or/括號/比較/in);無法判→raise(呼叫端計未判,誠實)。"""
    toks = [re.sub(r"\s+", " ", t) for t in _TOK_RX.findall(marker)]
    if not toks:
        raise ValueError("空標記")
    i = 0

    def take():
        nonlocal i
        if i >= len(toks):
            raise ValueError("斷尾")
        t = toks[i]
        i += 1
        return t

    def peek():
        return toks[i] if i < len(toks) else None

    def val(t):
        if t and t[0] in "\"'":
            return t[1:-1]
        if t in env:
            return str(env[t])
        raise ValueError("未知變數 " + str(t))

    def atom():
        if peek() == "(":
            take()
            v = expr_or()
            if take() != ")":
                raise ValueError("括號不閉")
            return v
        lv, op, rv = val(take()), take(), val(take())
        if op == "in":
            return lv in rv
        if op == "not in":
            return lv not in rv
        if op == "===":
            return lv == rv
        if op in ("==", "!=", ">=", "<=", ">", "<"):
            try:
                c = _mini_cmp(lv, rv)  # 版本型優先(3.11 > 3.9 字串比會錯)
            except Exception:
                c = (lv > rv) - (lv < rv)
            return {"==": c == 0, "!=": c != 0, ">=": c >= 0, "<=": c <= 0, ">": c > 0, "<": c < 0}[op]
        raise ValueError("未知運算 " + op)

    def expr_and():
        v = atom()
        while peek() == "and":
            take()
            v2 = atom()
            v = v and v2
        return v

    def expr_or():
        v = expr_and()
        while peek() == "or":
            take()
            v2 = expr_and()
            v = v or v2
        return v

    out = expr_or()
    if i != len(toks):
        raise ValueError("殘 token")
    return bool(out)


# ── 環境圖譜(內建 pipdeptree/pip check 同義層)────────────────────
def get_dists_full():
    """全發行版盤點:eff=生效層(sys.path 首見即勝)· dups=多層同名(互撞風險)。"""
    from importlib.metadata import distributions
    eff, seen = {}, {}
    for d in distributions():
        try:
            name = canon((d.metadata["Name"] or "").strip())
            if not name:
                continue
            p = getattr(d, "_path", None)
            root = str(Path(str(p)).parent) if p is not None else "?"
            ver = d.version or "0"
            lst = seen.setdefault(name, [])
            if root not in [x["root"] for x in lst]:
                lst.append({"ver": ver, "root": root})
            if name not in eff:
                eff[name] = {"ver": ver, "root": root, "requires": list(d.requires or [])}
        except Exception:
            continue
    dups = {n: lst for n, lst in seen.items() if len(lst) > 1}
    return eff, dups


def _live_reqs(info: dict, menv: dict):
    """標記過濾後的活性需求 [(目標, 規格)];未判條數另計(誠實)。"""
    out, unev = [], 0
    for raw in info.get("requires", []):
        pr = parse_req(raw)
        if pr is None:
            unev += 1
            continue
        tgt, spec, marker = pr
        if marker:
            try:
                if not eval_marker(marker, menv):
                    continue
            except Exception:
                unev += 1
                continue
        out.append((tgt, spec))
    return out, unev


def analyze(eff: dict, menv: dict, contains) -> dict:
    """全圖譜衝突掃描(pip check 同義):缺件/版本互撞/逆向邊/未判計數。"""
    missing, mismatch, unev = [], [], 0
    rev: dict[str, list] = {}
    for name, info in eff.items():
        live, u = _live_reqs(info, menv)
        unev += u
        for tgt, spec in live:
            rev.setdefault(tgt, []).append((name, spec))
            if tgt not in eff:
                missing.append({"pkg": tgt, "spec": spec, "by": name})
            elif spec:
                try:
                    ok = contains(spec, eff[tgt]["ver"])
                except Exception:
                    unev += 1
                    continue
                if not ok:
                    mismatch.append({"pkg": tgt, "installed": eff[tgt]["ver"], "spec": spec, "by": name})
    return {"missing": missing, "mismatch": mismatch, "rev": rev, "unevaluated": unev}


# ── 十械三防線編成 ───────────────────────────────────────────────
ARSENAL = [
    ("uv",         1, ("uv",),                          ("uv",),         "Rust 極速解析;pip/pip-tools/venv 全替代"),
    ("poetry",     1, ("poetry",),                      ("poetry",),     "確定性解析;裝前窮舉間接依賴先鎖死衝突"),
    ("pdm",        1, ("pdm",),                         ("pdm",),        "PEP 582 現代管理;多版本衝突深析"),
    ("conda",      1, ("mamba", "micromamba", "conda"), ("conda",),      "二進位層(CUDA/MKL/C++ 動態庫)衝突歸它"),
    ("pipdeptree", 2, ("pipdeptree",),                  ("pipdeptree",), "樹狀視覺化;Required vs Installed 直標"),
    ("pip check",  2, (),                               ("pip",),        "內建體檢;毀損依賴一鍵掃"),
    ("pip-tools",  2, ("pip-compile",),                 ("pip-tools",),  "pip-compile 鎖版;解析期先暴露衝突"),
    ("snyk",       2, ("snyk",),                        (),              "免費層安全掃描;間接依賴漏洞與衝突"),
    ("pyenv",      3, ("pyenv",),                       (),              "解譯器多版本切換;Runtime 衝突隔離"),
    ("tox/nox",    3, ("tox", "nox"),                   ("tox", "nox"),  "多環境矩陣;執行期衝突實測"),
]
LINES = {1: "第一防線·解析主幹", 2: "第二防線·診斷照妖", 3: "第三防線·隔離防污"}


def arsenal_scan(eff: dict) -> list:
    rows = []
    for key, line, whichs, dist_names, note in ARSENAL:
        w = next((x for x in whichs if shutil.which(x)), None)
        dv = next((eff[canon(x)]["ver"] for x in dist_names if canon(x) in eff), None)
        rows.append({"tool": key, "line": line, "present": bool(w or dv),
                     "via": (f"PATH:{w}" if w else (f"庫 {dv}" if dv else "缺")), "note": note})
    return rows


# ── 鏡像三源 ─────────────────────────────────────────────────────
MIRRORS = {
    "official": ("官方 PyPI", "https://pypi.org/simple/"),
    "tsinghua": ("清華 TUNA", "https://pypi.tuna.tsinghua.edu.cn/simple/"),
    "aliyun":   ("阿里雲",   "https://mirrors.aliyun.com/pypi/simple/"),
}
_CONDA_CH = {
    "tsinghua": ["https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main",
                 "https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge"],
    "aliyun":   ["https://mirrors.aliyun.com/anaconda/pkgs/main",
                 "https://mirrors.aliyun.com/anaconda/cloud/conda-forge"],
}


def classify_index(url: str) -> str:
    u = (url or "").lower()
    if "pypi.tuna.tsinghua" in u:
        return "tsinghua"
    if "mirrors.aliyun" in u:
        return "aliyun"
    if "pypi.org" in u:
        return "official"
    return "other"


def pip_conf_files() -> list:
    files = []
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            files.append(Path(appdata) / "pip" / "pip.ini")
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        files += [Path(xdg) / "pip" / "pip.conf", Path.home() / ".pip" / "pip.conf"]
    files.append(Path(sys.prefix) / ("pip.ini" if os.name == "nt" else "pip.conf"))
    return files


def effective_index():
    envv = os.environ.get("PIP_INDEX_URL")
    if envv:
        return "環境變數 PIP_INDEX_URL", envv
    import configparser
    for f in pip_conf_files():
        try:
            if f.is_file():
                cp = configparser.ConfigParser()
                cp.read(f, encoding="utf-8")
                for sec in ("global", "install"):
                    if cp.has_option(sec, "index-url"):
                        return f"組態 {f}", cp.get(sec, "index-url")
        except Exception:
            continue
    return "預設(未另設)", MIRRORS["official"][1]


def _probe(url: str, timeout: float = 6.0):
    """單鏡像測速:HEAD 優先,405/403 落 GET 讀 2KB;回 (毫秒|None, 註)。"""
    import urllib.error
    import urllib.request
    hdr = {"User-Agent": "via-deps/0100"}
    t0 = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers=hdr),
                                    timeout=timeout) as r:
            return round((time.time() - t0) * 1000), f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        if e.code not in (403, 405, 501):
            return None, f"HTTP {e.code}"
    except Exception as e:
        return None, str(e)[:60]
    try:
        t0 = time.time()
        with urllib.request.urlopen(urllib.request.Request(url + "pip/", headers=hdr),
                                    timeout=timeout) as r:
            r.read(2048)
            return round((time.time() - t0) * 1000), f"HTTP {r.status}(GET)"
    except Exception as e:
        return None, str(e)[:60]


# ── 場景編成 ─────────────────────────────────────────────────────
PRESETS = {
    "web": ("常規 Web/軟體開發",
            [("主幹", "uv——解析/venv/鎖版一把抓(百倍速)"),
             ("排錯", "pipdeptree + pip check(缺席時本引擎內建圖譜頂上)"),
             ("隔離", "pyenv 多解譯器(舊件不支援新 Python 之解)")],
            ["{P} -m pip install --user uv pipdeptree pip-tools"],
            ["uv venv && uv pip compile requirements.in -o requirements.txt",
             "uv pip sync requirements.txt", "via-deps(全景衝突掃描收尾)"]),
    "ai": ("AI/數據科學",
           [("主幹", "Mamba/Conda——CUDA·MKL·C++ 二進位衝突歸它管"),
            ("排錯", "pipdeptree + pip check(pip 層與 conda 層交叉對照)"),
            ("隔離", "tox 多版本矩陣(via-deps --matrix 出骨架)")],
           ["{P} -m pip install --user pipdeptree", "conda install -c conda-forge mamba(或裝 Miniforge)"],
           ["mamba env create -f environment.yml", "via-deps(pip 疊裝後即掃)",
            "via-deps --why 衝突套件(鎖定引入鏈)"]),
    "script": ("自動化腳本",
               [("主幹", "pip-tools 鎖版(輕量;或直上 uv)"),
                ("排錯", "pip check(每次裝後一鍵體檢)"),
                ("隔離", "nox 任務矩陣(Python 寫組態,腳本族群好上手)")],
               ["{P} -m pip install --user pip-tools nox"],
               ["pip-compile requirements.in && pip-sync requirements.txt",
                "{P} -m pip check", "via-deps --tree 主套件(依賴樹核對)"]),
}


# ── 模式:全景掃描(預設)──────────────────────────────────────────
def cmd_sweep() -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"=== 依賴衝突統包引擎 v0101 · {ts} · 唯讀零改動(十械三防線+三鏡像)===")
    print("── ① 十械三防線(在=接管;缺=內建替補頂上)──")
    eff, dups = get_dists_full()
    rows = arsenal_scan(eff)
    for ln in (1, 2, 3):
        sub = [r for r in rows if r["line"] == ln]
        n_in = sum(1 for r in sub if r["present"])
        cells = " · ".join(f"{r['tool']}:{'在(' + r['via'] + ')' if r['present'] else '缺'}" for r in sub)
        print(f"  [{LINES[ln]}] {cells} → {n_in}/{len(sub)}")
    if not any(r["present"] for r in rows if r["line"] == 1):
        print(f"  裁:主幹全缺——建議首選 uv(執行令:{PYCMD} -m pip install --user uv;走 via-install)")
    print("── ② 環境快照 ──")
    import platform
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    n_layers = len({i["root"] for i in eff.values()})
    print(f"  Python {platform.python_version()} · {'venv' if in_venv else '基座環境'} · 解譯器 {sys.executable}")
    print(f"  發行版 {len(eff)} · site 層 {n_layers} · 多層同名 {len(dups)} 件")
    src, contains = _pep440()
    menv = _marker_env()
    print(f"── ③ 衝突掃描(內建圖譜;判定器:{src})──")
    r = analyze(eff, menv, contains)
    n_mis, n_mm = len(r["missing"]), len(r["mismatch"])
    print(f"  缺件 {n_mis} 條 · 版本互撞 {n_mm} 條 · 標記未判 {r['unevaluated']} 條 · 多層重複 {len(dups)} 件")
    for m in r["mismatch"][:10]:
        print(f"   ✗ [互撞] {m['pkg']} 裝 {m['installed']} ↔ {m['by']} 需 {m['spec']}")
    for m in r["missing"][:10]:
        print(f"   ✗ [缺件] {m['pkg']}{m['spec'] or ''} ← {m['by']} 要而未裝")
    if n_mm > 10 or n_mis > 10:
        print(f"   …其餘見存證(互撞 {n_mm}/缺件 {n_mis} 全清單)")
    for n, lst in list(dups.items())[:5]:
        vers = " / ".join(f"{x['ver']}@{'/'.join(Path(x['root']).parts[-2:])}" for x in lst[:3])
        print(f"   ~ [多層] {n}:{vers}(首見層勝;診斷:via-install --doctor)")
    print("── ④ pip check 交叉印證 ──")
    pc_n = None
    if canon("pip") in eff:
        try:
            pr = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True,
                                text=True, timeout=180, stdin=subprocess.DEVNULL)
            lines = [l for l in pr.stdout.splitlines() if l.strip()]
            pc_n = 0 if pr.returncode == 0 else len(lines)
            print(f"  pip 判 {pc_n} 條 vs 內建判 {n_mis + n_mm} 條 → "
                  + ("相互印證" if pc_n == n_mis + n_mm else "有出入(extra/標記判法差異屬常態,兩邊皆誠實)"))
            for l in lines[:5]:
                print(f"   · {l[:110]}")
        except Exception as exc:
            print(f"  pip check 未跑成({type(exc).__name__})——內建掃描獨挑(誠實)")
    else:
        print("  pip 缺——內建掃描獨挑(誠實)")
    print("── ⑤ 鏡像現況(唯讀)──")
    isrc, iurl = effective_index()
    fam = classify_index(iurl)
    print(f"  生效源:{MIRRORS.get(fam, ('其他', ''))[0] if fam != 'other' else '其他'}({iurl})· 出處:{isrc}")
    uvi = os.environ.get("UV_DEFAULT_INDEX") or os.environ.get("UV_INDEX_URL")
    print(f"  uv 源:{uvi or '未另設(隨官方)'} · condarc:{'在' if (Path.home() / '.condarc').is_file() else '無'}"
          f" · 測速 --mirror-test · 切源 --mirror-set tsinghua|aliyun|official")
    print("── ⑥ 裁決 ──")
    verdict = "RED" if (n_mis or n_mm) else ("YELLOW" if (dups or r["unevaluated"]) else "GREEN")
    print(f"  [{verdict}] 互撞 {n_mm} · 缺件 {n_mis} · 多層 {len(dups)} · 未判 {r['unevaluated']}")
    if n_mis or n_mm:
        bad = sorted({m["pkg"] for m in r["mismatch"]} | {m["pkg"] for m in r["missing"]})
        for p in bad[:5]:
            print(f"  [溯源令] via-deps --why {p}")
        if canon("pipdeptree") in eff:
            print(f"  [深掘令] {PYCMD} -m pipdeptree -r -p {bad[0]}(pipdeptree 在,可再證)")
        wants: dict[str, list] = {}
        for m in r["mismatch"]:
            wants.setdefault(m["pkg"], []).append((m["by"], m["spec"]))
        for p, ws in list(wants.items())[:5]:
            print(f"  [候裁] {p} 裝 {eff[p]['ver']};各方需求:" + " · ".join(f"{b}要{s}" for b, s in ws[:4])
                  + " ——版本選邊操作員裁,安裝走 via-plan→via-install")
    else:
        print("  無互撞無缺件——維持:動手裝新件前一律 via-plan 先實測")
    OUT.mkdir(parents=True, exist_ok=True)
    ev = OUT / f"DEPS_{ts}.json"
    ev.write_text(json.dumps({
        "schema": "VIA.DepSuper.v1", "ts": ts, "mode": "sweep", "engine": src,
        "arsenal": rows, "dists_total": len(eff), "layers": n_layers,
        "conflicts": {"missing": r["missing"], "mismatch": r["mismatch"],
                      "dup_layers": {k: v for k, v in dups.items()}, "unevaluated": r["unevaluated"]},
        "pip_check": pc_n, "mirror": {"source": isrc, "url": iurl, "family": fam},
        "verdict": verdict, "policy": "readonly·zero_change·commands_only·consent_gated_net"},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存證] {ev.relative_to(VIA)}")
    return 1 if verdict == "RED" else 0


# ── 模式:逆向溯源 / 正向樹 ───────────────────────────────────────
def _chain_up(rev: dict, start: str, limit: int = 6) -> list:
    path, cur, seen = [start], start, {start}
    while limit > 0:
        parents = rev.get(cur) or []
        nxt = next((p for p, _ in parents if p not in seen), None)
        if not nxt:
            break
        path.append(nxt)
        seen.add(nxt)
        cur = nxt
        limit -= 1
    return path


def cmd_why(pkg: str) -> int:
    c = canon(pkg)
    eff, _ = get_dists_full()
    src, contains = _pep440()
    r = analyze(eff, _marker_env(), contains)
    print(f"=== 逆向溯源:{c}(判定器:{src})===")
    if c in eff:
        print(f"  安裝:{eff[c]['ver']} · 層:{eff[c]['root']}")
    else:
        print("  未安裝(誰在要它,如下)")
    wants = r["rev"].get(c) or []
    if not wants:
        print("  無人聲明依賴——頂層自裝件或孤兒(可考慮清理)")
        return 0 if c in eff else 1
    n_bad = 0
    for by, spec in wants[:20]:
        ok = c in eff and (not spec or _safe_contains(contains, spec, eff[c]["ver"]))
        if not ok:
            n_bad += 1
        chain = _chain_up(r["rev"], by)
        tail = "" if r["rev"].get(chain[-1]) else " ←(頂層)"
        print(f"   · {by} {eff.get(by, {}).get('ver', '?')} 需 {c}{spec or '(任意)'} → {'OK' if ok else '✗衝突'}")
        print(f"     鏈:{' ← '.join(chain)}{tail}")
    if len(wants) > 20:
        print(f"   …共 {len(wants)} 方需求")
    return 1 if (n_bad or c not in eff) else 0


def _safe_contains(contains, spec: str, ver: str) -> bool:
    try:
        return contains(spec, ver)
    except Exception:
        return True  # 判不了不誣告(誠實:未判以 OK 計,sweep 另有未判計數)


def cmd_tree(pkg: str, depth: int = 3) -> int:
    c = canon(pkg)
    eff, _ = get_dists_full()
    src, contains = _pep440()
    menv = _marker_env()
    print(f"=== 正向依賴樹:{c} · 深度 {depth}(判定器:{src})===")
    if c not in eff:
        print("  ✗ 未安裝——無樹可展(誠實)")
        return 1
    print(f"  {c} {eff[c]['ver']}")
    bad = [0]

    def walk(name: str, d: int, prefix: str, seen: frozenset):
        live, _u = _live_reqs(eff[name], menv)
        show = live[:12]
        for idx, (tgt, spec) in enumerate(show):
            last = idx == len(show) - 1 and len(live) <= 12
            branch = "└─" if last else "├─"
            if tgt not in eff:
                mark = "✗缺件"
                bad[0] += 1
            elif spec and not _safe_contains(contains, spec, eff[tgt]["ver"]):
                mark = f"裝 {eff[tgt]['ver']} ✗互撞"
                bad[0] += 1
            else:
                mark = f"裝 {eff[tgt]['ver'] if tgt in eff else '?'} OK"
            print(f"  {prefix}{branch} {tgt}{spec or ''} → {mark}")
            if tgt in eff and d > 1 and tgt not in seen:
                walk(tgt, d - 1, prefix + ("   " if last else "│  "), seen | {tgt})
        if len(live) > 12:
            print(f"  {prefix}└─ …共 {len(live)} 條(前 12 示)")

    walk(c, depth, "", frozenset({c}))
    print(f"  [計] 樹內異常 {bad[0]} 條")
    return 1 if bad[0] else 0


# ── 模式:鏡像 ────────────────────────────────────────────────────
def cmd_mirror() -> int:
    print("=== 鏡像現況(唯讀零網路)===")
    isrc, iurl = effective_index()
    fam = classify_index(iurl)
    print(f"  pip 生效源:{iurl}")
    print(f"    歸類:{MIRRORS[fam][0] if fam in MIRRORS else '其他/自建'} · 出處:{isrc}")
    uvi = os.environ.get("UV_DEFAULT_INDEX") or os.environ.get("UV_INDEX_URL")
    print(f"  uv 環境變數:{uvi or '未設(UV_DEFAULT_INDEX)'}")
    rc = Path.home() / ".condarc"
    print(f"  condarc:{str(rc) + ' 在' if rc.is_file() else '無(conda 走預設源)'}")
    print("  可用三源:")
    for k, (label, url) in MIRRORS.items():
        print(f"   · {k:8s} {label} {url}")
    print("  測速:via-deps --mirror-test(網路;同意閘)· 切源:via-deps --mirror-set <源>")
    return 0


def cmd_mirror_test() -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"=== 三鏡像測速 · {ts} ===")
    if not _consent():
        print("  NOT_RUN(測速屬網路行為,同意閘關)——同意後本視窗即時生效:")
        print('    PowerShell:$env:VIA_NET_CONSENT="YES" · bash:export VIA_NET_CONSENT=YES')
        return 0
    results = []
    for k, (label, url) in MIRRORS.items():
        ms, note = _probe(url)
        results.append({"mirror": k, "label": label, "url": url, "ms": ms, "note": note})
        print(f"  [{'OK  ' if ms is not None else 'FAIL'}] {k:8s} {label} · {str(ms) + ' ms' if ms is not None else '—'} · {note}")
    ok = sorted([x for x in results if x["ms"] is not None], key=lambda x: x["ms"])
    if ok:
        best = ok[0]
        print(f"  [裁] 最快:{best['mirror']}({best['ms']} ms)——切源執行令:via-deps --mirror-set {best['mirror']}")
    else:
        print("  [裁] 三源皆不通(代理/防火牆?)——誠實 FAIL,不亂裁")
    OUT.mkdir(parents=True, exist_ok=True)
    ev = OUT / f"MIRROR_{ts}.json"
    ev.write_text(json.dumps({"schema": "VIA.DepSuper.v1", "ts": ts, "mode": "mirror_test",
                              "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存證] {ev.relative_to(VIA)}")
    return 0


def cmd_mirror_set(name: str) -> int:
    if name not in MIRRORS:
        print(f"  ✗ 未知鏡像 {name}——可選:{' / '.join(MIRRORS)}")
        return 2
    label, url = MIRRORS[name]
    print(f"=== 切源執行令:{name}({label})——引擎不代寫組態,操作員貼跑(紅線)===")
    print("  [pip 永久]")
    print(f"    {PYCMD} -m pip config set global.index-url {url}")
    print(f"    還原:{PYCMD} -m pip config unset global.index-url")
    print("  [pip 單次(不落組態)]")
    print(f"    {PYCMD} -m pip install -i {url} <套件>")
    print("  [uv]")
    if name == "official":
        print("    PowerShell:Remove-Item Env:UV_DEFAULT_INDEX · bash:unset UV_DEFAULT_INDEX")
    else:
        print(f'    PowerShell:setx UV_DEFAULT_INDEX "{url}" · bash:export UV_DEFAULT_INDEX={url}')
    print(f"    單次:uv pip install --index-url {url} <套件>")
    print("  [poetry]")
    if name == "official":
        print("    poetry source remove tsinghua|aliyun(移除即回官方)")
    else:
        print(f"    poetry source add --priority=primary {name} {url}")
    print("  [pdm]")
    if name == "official":
        print("    pdm config --delete pypi.url")
    else:
        print(f"    pdm config pypi.url {url}")
    print("  [conda]")
    if name == "official":
        print("    conda config --remove-key channels(回預設 defaults)")
    else:
        print("    ~/.condarc 增列(anaconda 鏡像):")
        for ch in _CONDA_CH[name]:
            print(f"      - {ch}")
    print("  貼跑後驗證:via-deps --mirror(現況)· via-deps --mirror-test(實測)")
    return 0


# ── 模式:場景編成 / 多版本矩陣 ───────────────────────────────────
def cmd_preset(scene: str) -> int:
    if scene not in PRESETS:
        print(f"  ✗ 未知場景 {scene}——可選:{' / '.join(PRESETS)}")
        return 2
    title, lines_, boot, flow = PRESETS[scene]
    print(f"=== 場景編成:{title} ===")
    for tag, txt in lines_:
        print(f"  [{tag}] {txt}")
    print("  引導安裝(執行令;安裝一律走 via-plan→via-install 先實測):")
    for b in boot:
        print(f"    {b.replace('{P}', PYCMD)}")
    print("  日常工作流:")
    for i, f in enumerate(flow, 1):
        print(f"    {'①②③④⑤'[i - 1]} {f.replace('{P}', PYCMD)}")
    print("  鏡像加速(擇需):via-deps --mirror-test → via-deps --mirror-set <最快源>")
    return 0


def cmd_matrix() -> int:
    print("=== Tox/Nox 多版本矩陣骨架(執行期衝突實測;貼入專案根)===")
    print("  [tox.ini]")
    for l in ("[tox]", "envlist = py310, py311, py312", "skip_missing_interpreters = true", "",
              "[testenv]", "deps = -r requirements.txt", "commands =",
              "    python -m pip check", "    python -m pytest -q"):
        print(f"    {l}")
    print("  [noxfile.py]")
    for l in ("import nox", "", "@nox.session(python=['3.10', '3.11', '3.12'])",
              "def tests(session):", "    session.install('-r', 'requirements.txt')",
              "    session.run('python', '-m', 'pip', 'check')",
              "    session.run('python', '-m', 'pytest', '-q')"):
        print(f"    {l}")
    print("  解譯器多版本由 pyenv 供應:pyenv install 3.10 3.11 3.12 · pyenv local 3.12")
    print("  (Windows 用 pyenv-win;或 uv python install 3.10 3.11 3.12 亦可供矩陣)")
    return 0


# ── 模式:自測 15 檢(零網路零環境依賴)────────────────────────────
def cmd_selftest() -> int:
    SENV = {"python_version": "3.11", "python_full_version": "3.11.9", "sys_platform": "linux",
            "platform_system": "Linux", "platform_machine": "x86_64",
            "platform_python_implementation": "CPython", "implementation_name": "cpython",
            "os_name": "posix", "platform_release": "6.0", "extra": ""}
    FAKE = {
        "webapp": {"ver": "1.0", "requires": [
            "framework>=2.0", "ghostlib>=1.0",
            'winonly>=1 ; sys_platform == "win32"', "speed (>=2.0) ; extra == 'fast'"]},
        "framework": {"ver": "1.5", "requires": ["util>=1.0"]},
        "util": {"ver": "2.3", "requires": []},
        "speed": {"ver": "1.0", "requires": []},
    }
    src, contains = _pep440()

    def t01():
        assert _mini_cmp("1.0", "1.1") < 0 and _mini_cmp("1.0", "1.0.0") == 0 and _mini_cmp("2.10", "2.9") > 0

    def t02():
        order = ["1.0.dev1", "1.0a1", "1.0b2", "1.0rc1", "1.0", "1.0.post1", "1.1"]
        for a, b in zip(order, order[1:]):
            assert _mini_cmp(a, b) < 0, f"{a}<{b}"

    def t03():
        for fn in (contains, _mini_contains):
            assert fn(">=1.2", "1.3") and not fn(">=1.2,<2", "2.0") and fn("!=3.0", "3.1")

    def t04():
        assert _mini_contains("==1.*", "1.9") and not _mini_contains("==1.*", "2.0")
        assert not _mini_contains("!=1.*", "1.5") and _mini_contains("!=1.*", "2.0")

    def t05():
        assert _mini_contains("~=2.2", "2.5") and not _mini_contains("~=2.2", "3.0")
        assert _mini_contains("~=1.4.5", "1.4.9") and not _mini_contains("~=1.4.5", "1.5.0")

    def t06():
        assert parse_req('requests (>=2.0) ; extra == "sec"') == ("requests", ">=2.0", 'extra == "sec"')
        assert parse_req("Pillow_SIMD[avx2]>=9.0")[0] == "pillow-simd"
        assert parse_req("pkg @ https://x/y.whl")[1] == ""

    def t07():
        assert eval_marker('python_version >= "3.8"', SENV) is True
        assert eval_marker('sys_platform == "win32"', SENV) is False

    def t08():
        m = '(sys_platform == "win32" or sys_platform == "linux") and python_version < "4.0"'
        assert eval_marker(m, SENV) is True
        assert eval_marker('python_version >= "3.10" and python_version < "3.11"', SENV) is False

    def t09():
        assert eval_marker('extra == "fast"', SENV) is False  # extra 不知→跳(pip check 同義)

    def t10():
        r = analyze(FAKE, SENV, contains)
        assert [m["pkg"] for m in r["missing"]] == ["ghostlib"]

    def t11():
        r = analyze(FAKE, SENV, contains)
        assert len(r["mismatch"]) == 1 and r["mismatch"][0]["pkg"] == "framework"
        assert r["mismatch"][0]["installed"] == "1.5" and r["mismatch"][0]["by"] == "webapp"

    def t12():
        clean = {"a": {"ver": "1.0", "requires": ["b>=1.0"]}, "b": {"ver": "1.2", "requires": []}}
        r = analyze(clean, SENV, contains)
        assert not r["missing"] and not r["mismatch"]  # 潔淨零誤報;speed(extra)未列互撞見 t11 計 1

    def t13():
        r = analyze(FAKE, SENV, contains)
        assert ("webapp", ">=2.0") in r["rev"]["framework"] and ("framework", ">=1.0") in r["rev"]["util"]
        assert _chain_up(r["rev"], "framework") == ["framework", "webapp"]

    def t14():
        assert len(ARSENAL) == 10 and {l for _, l, *_ in ARSENAL} == {1, 2, 3}
        assert set(MIRRORS) == {"official", "tsinghua", "aliyun"}
        assert all(u.startswith("https://") for _, u in MIRRORS.values()) and len(PRESETS) == 3

    def t15():
        eff, _dups = get_dists_full()
        analyze(eff, _marker_env(), contains)  # 真環境煙測:不炸即過(衝突多寡屬 sweep 裁)

    battery = [("版序基本", t01), ("預發全序", t02), ("判定雙引擎", t03), ("萬用 ==/!=", t04),
               ("相容 ~=", t05), ("需求解析三式", t06), ("標記真偽", t07), ("標記布林括號", t08),
               ("extra 跳判", t09), ("圖譜缺件", t10), ("圖譜互撞", t11), ("潔淨零誤報", t12),
               ("逆溯邊+鏈", t13), ("編成完整", t14), ("真環境煙測", t15)]
    print(f"=== 依賴統包引擎自測 15 檢(判定器:{src};零網路零改動)===")
    n_ok = 0
    for name, fn in battery:
        try:
            fn()
            n_ok += 1
            print(f"  [OK  ] {name}")
        except Exception as exc:
            print(f"  [FAIL] {name} · {type(exc).__name__}:{str(exc)[:70]}")
    print(f"  [計] {n_ok}/{len(battery)} 綠")
    return 0 if n_ok == len(battery) else 1


# ── 入口 ─────────────────────────────────────────────────────────
def _arg_after(args: list, flag: str):
    try:
        return args[args.index(flag) + 1]
    except (ValueError, IndexError):
        return None


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return cmd_selftest()
    if "-h" in a or "--help" in a or "--doc" in a:
        print(__doc__)
        return 0
    for flag, fn in (("--why", cmd_why), ("--tree", cmd_tree),
                     ("--mirror-set", cmd_mirror_set), ("--preset", cmd_preset)):
        if flag in a:
            val = _arg_after(a, flag)
            if not val:
                print(f"  ✗ {flag} 需帶參數(用法見 --help)")
                return 2
            return fn(val)
    if "--mirror-test" in a:
        return cmd_mirror_test()
    if "--mirror" in a:
        return cmd_mirror()
    if "--matrix" in a:
        return cmd_matrix()
    return cmd_sweep()


if __name__ == "__main__":
    sys.exit(main())
