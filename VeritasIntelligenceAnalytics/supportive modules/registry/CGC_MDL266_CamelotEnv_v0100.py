#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL266_CamelotEnv v0100 — Camelot 單獨隔離境(via_camelot_311)+ 相關搭配工具:建 · 裝 · 鎖 · 驗

操作員令(2026-10-05):「增加安裝 camelot 單獨環境隔離」「camelot 相關支援搭配工具也安裝」(VCGC-REQ171)。
VCGC 的分工 = 裝工具與環境(L111;不改 VRN / VDF 正本)。境名與 python 版照環境治理冊 families.table_extraction
(target_env via_camelot_311 · python 3.13;tabula 已依同日操作員令移到 via_tabula_311,不裝這裡)。
  status   境在不在 · python 版 · 是否隔離(include-system-site-packages = false)· 每一件在不在 · 系統 gs 有沒有
  plan     只印計畫(uv venv --allow-existing 不刪境 · uv pip install 本體 + 搭配工具)
  install --apply   真裝(要連網 = 本視窗雙閘;本支只讀不代設)→ uv pip check → 鎖檔 VIA_Reports/env/camelot/camelot_env_lock.txt
  verify   在境內實讀一份自產 PDF 表(lattice 格線 + stream 文字)→ VIA_Reports/env/camelot/CAMELOT_ENV_latest.json
件(本體 + 搭配):camelot-py · pypdfium2(pdfium 後端,預設)· opencv-python-headless(格線)· pdfminer.six · pypdf · ghostscript(綁定;系統 gs 選配)·
  matplotlib(plot 除錯)· pandas · numpy · openpyxl · tabulate · chardet · click。
用法:via-vcgc run CGC_MDL266_CamelotEnv [status|plan|install --apply|verify] · --selftest。不碰 TA-Lib;不刪任何境。
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

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ENGINE = Path(__file__).stem
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENV_NAME = "via_camelot_311"                    # 環境治理冊 families.table_extraction.target_env(批382 命名律;名字裡的 311 是舊名沿用)
PYVER = "3.13"                                  # 同冊 families.table_extraction.python
OUT_DIR = VIA / "VIA_Reports" / "env" / "camelot"
# Camelot 本體 + 搭配工具(操作員令「camelot 相關支援搭配工具也安裝」);每一件寫用途,冊上可查
OPTIONAL = {"ghostscript"}                     # 要系統 gs(工作站另裝 Ghostscript)才 import 得到;缺 = 照實註記,不算紅(pdfium 是預設後端)
SKIPPED_ROOTS: list = []                        # 解析不了的境根(照實留紀錄,不吞)
PACKAGES = [
    ("camelot-py", "camelot", "PDF 表格擷取本體(lattice 格線 / stream 文字對齊)"),
    ("pypdfium2", "pypdfium2", "pdfium 頁面轉圖後端(camelot 預設,不靠系統 ghostscript)"),
    ("opencv-python-headless", "cv2", "lattice 格線偵測(無 GUI 版,伺服器 / 工作站都可)"),
    ("pdfminer.six", "pdfminer", "PDF 文字層解析(stream 與文字座標)"),
    ("pypdf", "pypdf", "分頁 / 頁面處理"),
    ("ghostscript", "ghostscript", "ghostscript 後端 Python 綁定(要系統 gs 才真能用;缺 gs 時 camelot 走 pdfium)"),
    ("matplotlib", "matplotlib", "camelot.plot 除錯圖(看格線 / 文字框)"),
    ("pandas", "pandas", "表格 DataFrame"),
    ("numpy", "numpy", "數值底層"),
    ("openpyxl", "openpyxl", "匯出 Excel"),
    ("tabulate", "tabulate", "匯出 Markdown 表"),
    ("chardet", "chardet", "文字編碼偵測"),
    ("click", "click", "camelot 命令列"),
]


def env_roots() -> list:
    """境根(同 CGC_MDL262):VIA_ENVS_ROOT → /root/envs · ~/envs · ~/anaconda3/envs · ~/miniconda3/envs;有家族境的那個優先。"""
    raw = os.environ.get("VIA_ENVS_ROOT")
    cands = [Path(p) for p in re.split(r"[;" + (":" if os.name != "nt" else "") + r"]", raw) if p] if raw else []
    home = Path.home()
    cands += [Path("/root/envs"), home / "envs", home / "anaconda3" / "envs", home / "miniconda3" / "envs"]
    out, seen = [], set()
    for c in cands:
        try:
            k = str(c.resolve())
        except OSError as exc:
            SKIPPED_ROOTS.append(f"{c}: {exc}")
            continue
        if c.is_dir() and k not in seen:
            seen.add(k)
            out.append(c)
    return sorted(out, key=lambda r: not any((r / f).is_dir() for f in ("via_vdf_312", "via_vrn_312", "via_core")))


def env_dir() -> Path:
    roots = env_roots()
    return (roots[0] if roots else Path.home() / "envs") / ENV_NAME


def env_python(env: Path) -> Path | None:
    for rel in ("bin/python", "Scripts/python.exe", "python.exe"):
        p = env / rel
        if p.exists():
            return p
    return None


def run(cmd: list, timeout: int = 1800, env: dict | None = None) -> tuple:
    try:
        p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except OSError as exc:
        return 127, str(exc)


PROBE = r"""
import importlib, json, sys, shutil, warnings
warnings.filterwarnings("ignore")
mods = %s
out = {"python": sys.version.split()[0], "prefix": sys.prefix, "base_prefix": sys.base_prefix, "mods": {}}
for m in mods:
    try:
        mod = importlib.import_module(m)
        out["mods"][m] = getattr(mod, "__version__", "ok")
    except Exception as exc:
        out["mods"][m] = "MISSING: " + type(exc).__name__
out["gs"] = shutil.which("gs") or shutil.which("gswin64c") or shutil.which("gswin32c")
print(json.dumps(out))
"""


def status(quiet: bool = False) -> dict:
    env = env_dir()
    py = env_python(env)
    cfg = env / "pyvenv.cfg"
    st = {"env": str(env), "python": str(py) if py else None, "venv": cfg.is_file(), "isolated": False, "mods": {}, "gs": None, "state": "ABSENT"}
    if cfg.is_file():
        st["isolated"] = "include-system-site-packages = false" in cfg.read_text(encoding="utf-8", errors="ignore")
    if py:
        rc, out = run([py, "-c", PROBE % json.dumps([m for _, m, _ in PACKAGES])], 300)
        try:
            j = json.loads([ln for ln in out.strip().splitlines() if ln.startswith("{")][-1])   # 只取 JSON 行(套件警告會混在後面)
            st.update({"py_version": j["python"], "mods": j["mods"], "gs": j["gs"], "own_prefix": j["prefix"] != j["base_prefix"]})
        except (ValueError, IndexError, KeyError):
            st["probe_error"] = out[-300:]
    missing = [m for m, v in st["mods"].items() if str(v).startswith("MISSING") and m not in OPTIONAL]
    st["missing"] = missing
    st["optional_missing"] = [m for m, v in st["mods"].items() if str(v).startswith("MISSING") and m in OPTIONAL]
    if py and st["mods"] and not missing and st["isolated"] and st.get("own_prefix"):
        st["state"] = "GREEN"
    elif py:
        st["state"] = "YELLOW" if st["mods"] else "RED"
    if not quiet:
        print(f"  [Camelot 境] {st['state']} · {env} · python {st.get('py_version', '-')} · 隔離 {'是' if st['isolated'] else '否'}"
              f" · 必要件 {len(st['mods']) - len(missing) - len(st['optional_missing'])}/{len(PACKAGES) - len(OPTIONAL)}" + (f" · 缺 {', '.join(missing)}" if missing else "")
              + (f" · 選配缺 {', '.join(st['optional_missing'])}(要系統 Ghostscript)" if st["optional_missing"] else "")
              + f" · 系統 gs {'有' if st['gs'] else '沒有(camelot 走 pdfium 後端,照樣能用)'}")
    return st


def write_lock(frz: str) -> Path:
    """鎖檔進倉(registry,版號檔只增):內容跟最新一版一樣就沿用,不一樣才出下一版(已發布的不改)。"""
    locks = sorted(HERE.glob("VIA_CamelotEnv_Lock_v*.txt"))
    head = f"# {ENV_NAME} · python {PYVER} · {ENGINE} · uv pip freeze · {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
    body = "".join(ln + "\n" for ln in sorted(frz.strip().splitlines()) if ln and not ln.startswith("#"))
    if locks and "".join(ln + "\n" for ln in locks[-1].read_text(encoding="utf-8").splitlines() if ln and not ln.startswith("#")) == body:
        return locks[-1]
    n = int(re.search(r"_v(\d{4})\.txt$", locks[-1].name).group(1)) + 1 if locks else 100
    p = HERE / f"VIA_CamelotEnv_Lock_v{n:04d}.txt"
    p.write_text(head + body, encoding="utf-8")
    return p


def install(apply: bool) -> int:
    env = env_dir()
    uv = shutil.which("uv")
    specs = [p for p, _, _ in PACKAGES]
    st = status(quiet=True)
    plan = []
    if not (st["venv"] and st["python"] and st.get("py_version", "").startswith(PYVER)):
        plan.append([uv or "uv", "venv", str(env), "--python", PYVER, "--allow-existing"])
    plan.append([uv or "uv", "pip", "install", "--python", str(env_python(env) or (env / "bin" / "python")), *specs])
    print(f"  [Camelot 境] 計畫(只進 {ENV_NAME} 隔離境 · 不動 base 與其他境 · 不刪任何境):")
    for c in plan:
        print("    " + " ".join(str(x) for x in c))
    if not apply:
        print("  [Camelot 境] 乾跑:加 --apply 才裝(要連網:本視窗雙閘是操作員的手,本支只讀不代設)")
        return 2
    if os.environ.get("VIA_NET_CONSENT") != "YES":
        print("  [GATED] 安裝要連網:先在本視窗開 VIA_NET_CONSENT=YES(操作員的手)→ 再跑 install --apply")
        return 4
    if not uv:
        print("  [ABSENT] 找不到 uv(環境治理用 uv 建境;先裝 uv)")
        return 3
    for c in plan:
        if c[1] == "pip":
            c[4] = str(env_python(env))
        rc, out = run(c, 3600)
        print("    " + "\n    ".join(out.strip().splitlines()[-4:]))
        if rc != 0:
            print(f"  [Camelot 境] 失敗 rc {rc}:{' '.join(str(x) for x in c[:3])}")
            return 1
    rc, out = run([uv, "pip", "check", "--python", str(env_python(env))], 300)
    print(f"  [Camelot 境] uv pip check rc {rc}:{out.strip().splitlines()[-1] if out.strip() else ''}")
    rc2, frz = run([uv, "pip", "freeze", "--python", str(env_python(env))], 300)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if rc2 == 0:
        (OUT_DIR / "camelot_env_lock.txt").write_text(frz, encoding="utf-8")
        lock = write_lock(frz)
        print(f"  [Camelot 境] 鎖檔 {lock.relative_to(VIA)}(進倉;工作站:uv venv <境根>\\{ENV_NAME} --python {PYVER} → uv pip sync 這個檔 = 同版重建)")
    return 0 if status()["state"] == "GREEN" else 1


VERIFY = r"""
import json, sys, warnings
warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import camelot
pdf = sys.argv[1]
fig, ax = plt.subplots(figsize=(6, 2.2)); ax.axis("off")
rows = [["代碼", "名稱", "收盤"], ["2330", "TSMC", "1000.5"], ["2317", "Foxconn", "212.0"], ["2454", "MediaTek", "1350.0"]]
t = ax.table(cellText=[[r[0], r[1].encode("ascii", "ignore").decode() or r[1], r[2]] for r in rows], loc="center")
t.scale(1, 1.6)
matplotlib.rcParams["pdf.fonttype"] = 42
fig.savefig(pdf); plt.close(fig)
res = {"camelot": getattr(camelot, "__version__", "?")}
for flavor in ("lattice", "stream"):
    try:
        tabs = camelot.read_pdf(pdf, pages="1", flavor=flavor)
        cells = [c for tb in tabs for row in tb.df.values.tolist() for c in row]
        res[flavor] = {"tables": tabs.n, "has_2330": any("2330" in str(c) for c in cells), "has_1350": any("1350" in str(c) for c in cells), "shape": [tb.df.shape for tb in tabs][:2]}
    except Exception as exc:
        res[flavor] = {"error": f"{type(exc).__name__}: {exc}"[:200]}
print(json.dumps(res, default=str))
"""


def verify() -> int:
    py = env_python(env_dir())
    if not py:
        print("  [Camelot 驗證] ABSENT:境不在 → install --apply")
        return 3
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "v.py"
        f.write_text(VERIFY, encoding="utf-8")
        rc, out = run([py, f, str(Path(td) / "table.pdf")], 600)
    try:
        r = json.loads([ln for ln in out.strip().splitlines() if ln.startswith("{")][-1])
    except (ValueError, IndexError):
        print(f"  [Camelot 驗證] RED rc {rc}:{out[-400:]}")
        return 1
    ok = all(isinstance(r.get(fl), dict) and r[fl].get("has_2330") and r[fl].get("has_1350") for fl in ("lattice", "stream"))
    print(f"  [Camelot 驗證] {'GREEN' if ok else 'RED'} · camelot {r.get('camelot')} · 實讀自產 PDF 表:"
          + " · ".join(f"{fl} {json.dumps(r.get(fl), ensure_ascii=False)}" for fl in ("lattice", "stream")))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rep = {"engine": ENGINE, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "env": str(env_dir()), "status": status(quiet=True), "verify": r, "ok": ok}
    (OUT_DIR / "CAMELOT_ENV_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0 if ok else 1


def selftest() -> int:
    res = []

    def chk(name, ok, note=""):
        res.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' (' + str(note) + ')') if note else ''}")

    print(f"=== {ENGINE} · Camelot 隔離境自測(零網路 · 不裝不刪)===")
    chk("① 境名 / python 版照環境治理冊(table_extraction → via_camelot_311 · 3.13)", ENV_NAME == "via_camelot_311" and PYVER == "3.13")
    book = sorted(HERE.glob("VIA_EnvGovernance_Baseline_v*.json"))
    fam = (json.loads(book[-1].read_text(encoding="utf-8")).get("families") or {}).get("table_extraction", {}) if book else {}
    chk("② 冊上的家族件全在安裝清單(本體 + 搭配工具;tabula 已移 via_tabula_311 不裝這裡)",
        {"camelot-py", "pdfminer.six", "ghostscript"} <= {p for p, _, _ in PACKAGES} and "tabula-py" not in {p for p, _, _ in PACKAGES}
        and fam.get("target_env") == ENV_NAME, book[-1].name if book else "無冊")
    keep = os.environ.pop("VIA_NET_CONSENT", None)
    try:
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_dry = install(apply=False)
            rc_gate = install(apply=True)
        out = buf.getvalue()
    finally:
        if keep is not None:
            os.environ["VIA_NET_CONSENT"] = keep
    chk("③ 乾跑只印計畫(rc 2);沒開雙閘 = GATED(rc 4)不裝;計畫只進本境、帶 --allow-existing 不刪境",
        rc_dry == 2 and rc_gate == 4 and ENV_NAME in out and "pip install" in out, (rc_dry, rc_gate))
    src = Path(__file__).read_text(encoding="utf-8")
    import ast
    tree = ast.parse(src)
    talib = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Import) and any(a.name.split(".")[0] == "talib" for a in n.names)]
    writes = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Store)
              and isinstance(n.slice, ast.Constant) and str(n.slice.value).endswith("_CONSENT")
              and not any(isinstance(f, ast.FunctionDef) and f.name == "selftest" and f.lineno <= n.lineno <= f.end_lineno for f in tree.body)]
    chk("④ 加速器橋在 · 不碰 TA-Lib · selftest 外不寫 *_CONSENT(AI 永不代設)", "[VIA:ACCEL-BRIDGE:v0100]" in src and not talib and not writes, (talib, writes))
    st = status(quiet=True)
    chk("⑤ status 照實:境在 → 回 python 版 / 件數 / 隔離;境不在 = ABSENT(不假綠)", st["state"] in ("GREEN", "YELLOW", "RED", "ABSENT"), st["state"])
    ok = all(res)
    print(f"  [計] {ENGINE} 自測 {sum(res)}/{len(res)} · {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    verb = a[0] if a else "status"
    if verb == "status":
        st = status()
        return {"GREEN": 0, "YELLOW": 2}.get(st["state"], 1)
    if verb == "plan":
        return install(apply=False)
    if verb == "install":
        return install(apply="--apply" in a)
    if verb == "verify":
        return verify()
    print("  用法:status | plan | install [--apply] | verify | --selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
