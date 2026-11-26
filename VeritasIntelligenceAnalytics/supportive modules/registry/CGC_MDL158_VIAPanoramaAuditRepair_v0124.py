#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""CGC_MDL158_VIAPanoramaAuditRepair v0124 — 薄尾(v0123 以前一字不動):hydra 前版不寫 · 已鎖不寫 · 路徑型別閘

操作員 2026-11-26:「補前版不寫,然後用 vcgc 工具修倉內 VDF」。
本版只動 hydra 的「能不能寫」判斷,其餘照 v0123:
  ① 區位多三種(一律不寫,照列發現):
     前版 —— 同夾同家族有更大版號(X_v0101 有 X_v0102 → v0101 是前版);沒版號的 X.py 而同夾有 X_vNNNN.py → 舊原件,也是前版
             (CLAUDE.md 薄尾律:前版一字不動、仍被引用的舊模組不搬)
     已鎖 —— 路徑在成功鎖定帳 VIA_SuccessLock_Ledger 尾版裡(改了 = 重工守門「已鎖被改」紅)
     凍結 —— 另加交接冊 frozen_sources 的路徑(操作員原件 byte-exact)
     副本 —— 另加 _sha<雜湊> 指紋副本
  ② 路徑型別閘(防把桌機能跑的東西修壞):
     ENCODING 自動插 encoding 只在「路徑看得出是我們自己產的 UTF-8 文字檔」時(.json .jsonl .md .html .htm .py .toml .yaml .yml .log .ps1 .txt
     的字面值,或變數名帶 json / md / html);路徑是 csv / xls / 看不出來 → 改「人工」:台灣來源常是 big5 / cp950,
     Windows 沒給 encoding 時正好讀得對,硬插 utf-8 會讀壞。
     BOM(utf-8-sig → utf-8)同一道閘:csv / 看不出來 → 人工(Excel 開 csv 要 BOM 才不亂碼)。
只讀程式碼結構;不執行被掃的檔;不出網;不用 TA-Lib;不設同意閘。舊主控台字串門:"read" "slice" "digest" --if-etag def pack_payload。
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
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL158_VIAPanoramaAuditRepair"
_HYDRA_VER3 = "v0124"
TAG = f"{_STEM} {_HYDRA_VER3}"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("panorama_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V122 = PRIOR.PRIOR                                    # hydra 本體所在(panorama / apply / report 的全域在這裡)
VERBS = dict(PRIOR.VERBS)          # 動詞表照前版:"read" "slice" "digest" "pack" "tools" "verbs" … hydra
VERBS["hydra"] = (PRIOR.VERBS["hydra"][0], PRIOR.VERBS["hydra"][1],
                  PRIOR.VERBS["hydra"][2] + ";v0124:前版 · 已鎖 · 凍結原件 · 指紋副本不寫;ENCODING / BOM 只在路徑看得出是 UTF-8 文字檔時自動修")


def __getattr__(name: str):
    return getattr(PRIOR, name)


def pack_payload(root, limit: int = 200) -> dict:
    """整夾索引:原樣轉交前版鏈(明寫在本檔,讓只認字串的舊門也看得到)。"""
    return PRIOR.pack_payload(root, limit)


# ---------------------------------------------------------------- ① 前版 · 已鎖 · 凍結 · 指紋副本
_VER = re.compile(r"^(?P<fam>.+)_v(?P<n>\d{4})$")
_SHA = re.compile(r"_sha[0-9a-f]{6,}$")


def prior_version(p: Path) -> bool:
    m = _VER.match(p.stem)
    if m:
        return any(_vnum(q) > int(m.group("n")) for q in p.parent.glob(m.group("fam") + "_v*.py"))
    return any(_VER.match(q.stem) for q in p.parent.glob(p.stem + "_v*.py"))


def _via_root(p: Path):
    for q in p.resolve().parents:
        if q.name == "VeritasIntelligenceAnalytics" and (q / "supportive modules").is_dir():
            return q
    return None


_BOOKS = {}


def locked_and_frozen(via: Path) -> tuple:
    """(成功鎖定帳上的路徑集合, 交接冊 frozen_sources 路徑集合);都以 VIA 根為基準的 posix 相對路徑。"""
    if via in _BOOKS:
        return _BOOKS[via]
    locked, frozen = set(), set()
    leds = sorted((via / "docs" / "handoff" / "daily").glob("VIA_SuccessLock_Ledger_v*.jsonl"), key=_vnum)
    if leds:
        for ln in leds[-1].read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if r.get("path"):
                locked.add(str(r["path"]).replace("\\", "/"))
    hp = via / "supportive modules" / "registry" / "VIA_Handoff_Continuity_SSOT_v0100.json"
    if hp.is_file():
        try:
            fs = json.loads(hp.read_text(encoding="utf-8")).get("frozen_sources") or {}
            frozen = {str(k).replace("\\", "/") for k in (fs if isinstance(fs, (dict, list)) else [])}
        except ValueError:
            pass
    _BOOKS[via] = (locked, frozen)
    return _BOOKS[via]


def extra_zone(abspath: Path) -> str:
    if _SHA.search(abspath.stem):
        return "副本"
    via = _via_root(abspath)
    if via is not None:
        rel = abspath.resolve().relative_to(via).as_posix()
        locked, frozen = locked_and_frozen(via)
        if rel in frozen:
            return "凍結"
        if rel in locked:
            return "已鎖"
    if prior_version(abspath):
        return "前版"
    return ""


# ---------------------------------------------------------------- ② 路徑型別閘
SAFE_SUFFIX = (".json", ".jsonl", ".md", ".html", ".htm", ".py", ".toml", ".yaml", ".yml", ".log", ".ps1", ".txt")
UNSAFE_SUFFIX = (".csv", ".tsv", ".xls", ".xlsx", ".dat")
SAFE_NAME = re.compile(r"(json|_md\b|md_|html|yaml|toml|manifest|summary|ledger|receipt|log)", re.I)


def _path_expr(call: ast.Call):
    fn = call.func
    if isinstance(fn, ast.Name) and fn.id == "open":
        return call.args[0] if call.args else None
    if isinstance(fn, ast.Attribute) and fn.attr in ("read_text", "write_text"):
        return fn.value
    return None


def path_kind(expr) -> str:
    """→ "safe" / "unsafe" / "unknown"。只看字面值副檔名與名字提示,不猜。"""
    if expr is None:
        return "unknown"
    lits, names = [], []
    for n in ast.walk(expr):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            lits.append(n.value.lower())
        elif isinstance(n, ast.Name):
            names.append(n.id)
        elif isinstance(n, ast.Attribute):
            names.append(n.attr)
    if any(s.endswith(UNSAFE_SUFFIX) or any(u + "\"" in s for u in UNSAFE_SUFFIX) for s in lits) or any(re.search(r"csv|xls", x, re.I) for x in names):
        return "unsafe"
    if any(s.endswith(SAFE_SUFFIX) for s in lits):
        return "safe"
    if any(SAFE_NAME.search(x) for x in names):
        return "safe"
    return "unknown"


def gate_auto(src: str, findings: list) -> None:
    """ENCODING / BOM 的 auto 只留路徑型別 safe 的;其餘改人工並寫理由(原地改 findings)。"""
    autos = [x for x in findings if x.get("fix") == "auto" and x["cls"] in ("ENCODING", "BOM")]
    if not autos:
        return
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    for x in autos:
        call = None
        if x["cls"] == "ENCODING" and x.get("node"):
            call = next((c for c in calls if [c.end_lineno, c.end_col_offset] == list(x["node"])), None)
        elif x["cls"] == "BOM" and x.get("node"):
            l1, c1 = x["node"][0], x["node"][1]
            call = next((c for c in calls for k in c.keywords if k.arg == "encoding" and getattr(k.value, "lineno", 0) == l1
                         and getattr(k.value, "col_offset", -1) == c1), None)
        kind = path_kind(_path_expr(call)) if call is not None else "unknown"
        x["path_kind"] = kind
        if kind != "safe":
            x["fix"] = "manual"
            x["why_manual"] = "路徑型別" + ("是 csv / 試算表" if kind == "unsafe" else "看不出來") + "(可能是 big5 來源或 Excel 要 BOM)→ 人工"


# ---------------------------------------------------------------- 裝進 hydra
ZONES = tuple(PRIOR.ZONES) + ("前版", "已鎖")


def panorama(targets: list, workers: int = 0) -> dict:
    pan = _PREV_PAN(targets, workers)
    for z in ZONES:
        pan["zones"].setdefault(z, 0)
        pan["zone_files"].setdefault(z, 0)
    moved, srcs = {}, {}
    for rel, ab in pan["_files"].items():
        if any(x["file"] == rel and x.get("zone", "正本") == "正本" for x in pan["findings"]) or True:
            z = extra_zone(Path(ab))
            if z:
                moved[rel] = z
    for rel, z in moved.items():
        pan["zone_files"]["正本"] = max(0, pan["zone_files"]["正本"] - 1) if pan["zone_files"].get("正本") else 0
        pan["zone_files"][z] = pan["zone_files"].get(z, 0) + 1
    by_file = {}
    for x in pan["findings"]:
        by_file.setdefault(x["file"], []).append(x)
    for rel, fs in by_file.items():
        z = moved.get(rel)
        if z and all(x.get("zone", "正本") == "正本" for x in fs):
            for x in fs:
                pan["zones"]["正本"] -= 1
                pan["zones"][z] = pan["zones"].get(z, 0) + 1
                x["zone"], x["mode"] = z, f"不寫({z})"
                if x["fix"] == "auto":
                    x["fix"] = "skip"
        elif any(x["fix"] == "auto" for x in fs):
            try:
                srcs[rel] = V122._read(Path(pan["_files"][rel]))[0]
                gate_auto(srcs[rel], fs)
            except OSError:
                pass
    keep = lambda r: moved.get(r) is None  # noqa: E731
    pan["groups"]["不寫"] = sorted(set(pan["groups"].get("不寫", [])) | {r for r in moved if r in by_file})
    pan["groups"]["A"] = [r for r in pan["groups"]["A"] if keep(r)]
    pan["groups"]["B"] = [r for r in pan["groups"]["B"] if keep(r)]
    return pan


_PREV_PAN = V122.panorama
V122.panorama = panorama
V122.TAG = TAG


def report(before, fix, after) -> dict:
    rep = _PREV_REP(before, fix, after)
    rep["auto_fixable"] = sum(1 for x in before["findings"] if x["fix"] == "auto")
    rep["gated_manual"] = sum(1 for x in before["findings"] if x.get("path_kind") in ("unsafe", "unknown"))
    return rep


_PREV_REP = V122.report
V122.report = report


def _uninstall():
    V122.panorama, V122.report, V122.TAG = _PREV_PAN, _PREV_REP, PRIOR.TAG


def _install():
    V122.panorama, V122.report, V122.TAG = panorama, report, TAG


# ---------------------------------------------------------------- 入口
def print_verbs() -> int:
    e = '$E'
    print(f"[{TAG} 動詞表] {len(VERBS)} 個 · {e} = 鎖冊 token 那一支")
    for k, (use, when, what) in VERBS.items():
        print(f"  {k:<10} python3 \"{e}\" {use}")
        print(f"             何時:{when} · 做什麼:{what}")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if argv == ["--selftest"]:
        return selftest()
    if argv[:1] == ["verbs"]:
        return print_verbs()
    if argv[:1] == ["hydra"]:
        return PRIOR.hydra(argv[1:])
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    with tempfile.TemporaryDirectory() as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        eng = via / "functional modules" / "VDF" / "engine"
        (via / "supportive modules" / "registry").mkdir(parents=True)
        (via / "docs" / "handoff" / "daily").mkdir(parents=True)
        eng.mkdir(parents=True)
        files = {
            "X_v0100.py": "import json\n\n\ndef r(p):\n    return json.loads(open(p + '.json').read())\n",
            "X_v0101.py": "import json\n\n\ndef r(p):\n    return json.loads(open(p + '.json').read())\n",
            "Old.py": "open('a.json').read()\n",
            "Old_v0100.py": "open('a.json').read()\n",
            "Lk_v0100.py": "open('b.json').read()\n",
            "Sha_sha1a2b3c4d.py": "open('c.json').read()\n",
            "Csv_v0100.py": "import csv\n\n\ndef r(p):\n    return list(csv.reader(open(p + '.csv')))\n",
            "Unk_v0100.py": "def r(src):\n    return open(src).read()\n",
            "Bom_v0100.py": "def w(p, s):\n    open(p, 'w', encoding='utf-8-sig').write(s)\n\n\ndef j(p, s):\n    open('out.json', 'w', encoding='utf-8-sig').write(s)\n",
        }
        for k, v in files.items():
            (eng / k).write_text(v, encoding="utf-8")
        (via / "docs" / "handoff" / "daily" / "VIA_SuccessLock_Ledger_v0100.jsonl").write_text(
            json.dumps({"path": "functional modules/VDF/engine/Lk_v0100.py", "version": "v0100"}) + "\n", encoding="utf-8")
        (via / "supportive modules" / "registry" / "VIA_Handoff_Continuity_SSOT_v0100.json").write_text(
            json.dumps({"frozen_sources": {"functional modules/VDF/engine/Old.py": "x"}}), encoding="utf-8")
        _BOOKS.clear()
        pan = V122.panorama([str(eng)], 2)
        zf = {}
        for x in pan["findings"]:
            zf.setdefault(x["file"], x.get("zone"))
        chk("② 前版:X_v0100(有 X_v0101)· 已鎖:Lk_v0100(鎖帳)· 凍結:Old.py(frozen_sources)· 指紋副本:_sha… · 尾版 X_v0101 = 正本",
            zf.get("X_v0100.py") == "前版" and zf.get("Lk_v0100.py") == "已鎖" and zf.get("Old.py") == "凍結"
            and zf.get("Sha_sha1a2b3c4d.py") == "副本" and zf.get("X_v0101.py") == "正本", zf)
        auto = {(x["file"], x["line"]): x["fix"] for x in pan["findings"] if x["cls"] in ("ENCODING", "BOM")}
        chk("③ 路徑型別閘:.json 字面值 → 自動;csv → 人工;看不出來(open(src))→ 人工;BOM 寫 out.json → 自動、寫不明路徑 → 人工",
            auto.get(("X_v0101.py", 5)) == "auto" and auto.get(("Csv_v0100.py", 5)) == "manual" and auto.get(("Unk_v0100.py", 2)) == "manual"
            and auto.get(("Bom_v0100.py", 6)) == "auto" and auto.get(("Bom_v0100.py", 2)) == "manual", auto)
        chk("④ 分組只剩正本裡的檔;前版 / 已鎖 / 凍結 / 副本 列進「不寫」",
            not ({"X_v0100.py", "Lk_v0100.py", "Old.py", "Sha_sha1a2b3c4d.py"} & set(pan["groups"]["A"] + pan["groups"]["B"]))
            and {"X_v0100.py", "Lk_v0100.py", "Old.py"} <= set(pan["groups"]["不寫"]), pan["groups"])
        h0 = {k: hashlib.sha256((eng / k).read_bytes()).hexdigest() for k in files}
        fx = V122.apply(pan, [str(eng)], 2)
        h1 = {k: hashlib.sha256((eng / k).read_bytes()).hexdigest() for k in files}
        changed = sorted(k for k in files if h0[k] != h1[k])
        chk("⑤ --apply 只動正本裡的 safe 項:X_v0101 · Old_v0100(Old.py 的尾版)讀 .json · Bom_v0100 寫 out.json;前版 / 已鎖 / 凍結 / 副本 / csv / 不明 位元不變",
            changed == ["Bom_v0100.py", "Old_v0100.py", "X_v0101.py"] and "encoding='utf-8')" in (eng / "Bom_v0100.py").read_text(encoding="utf-8").split("def j")[1]
            and "encoding='utf-8-sig')" in (eng / "Bom_v0100.py").read_text(encoding="utf-8").split("def j")[0], [changed, fx["results"]])
        out = Path(td) / "rep.json"
        rc = V122.hydra([str(eng), "--out", str(out), "--max", "1"])
        rep = json.loads(out.read_bytes().decode("utf-8"))["report"]
        chk("⑥ 戰報:zones 有 前版 / 已鎖 · gated_manual 計數 · 橫幅寫本版", "前版" in rep["zones"] and "已鎖" in rep["zones"]
            and rep.get("gated_manual", 0) >= 3 and rep["tool"] == TAG and rc in (0, 1, 2), rep.get("zones"))
    chk("⑦ VERBS 前版全在(含 hydra)", set(PRIOR.VERBS) <= set(VERBS))
    import contextlib
    import io
    _uninstall()
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc_p = PRIOR.selftest()
    finally:
        _install()
    tail = [ln for ln in buf.getvalue().splitlines() if ln.strip()][-1:] or [""]
    chk("⑧ 前版 v0123 鏈自測(本版換裝卸下)照過", rc_p == 0, tail[0][:200])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 檔面:第 3 行加速器標記 · glob 取前版 · 零 TA-Lib · 不設同意閘 · 字串門字樣在",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "HERE.glob(_STEM" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M)
        and all(w in src for w in ('"read"', '"slice"', '"digest"', "--if-etag", "def pack_payload")))
    print(f"[計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 2


if __name__ == "__main__":
    raise SystemExit(main())
