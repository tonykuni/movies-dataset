#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL228_VIADBManager v0107 — 薄尾(v0106 以前一字不動):來源路徑只認檔自己的號 · UI token 讀鎖定冊正本位置

PR #751 Codex 第三輪兩筆:
  ① (P2)v0106 的「來源路徑 → 號」收第一筆:同一支 .py 在 ENV 冊也有列(環境變數的來源寫那支檔),
     ENV 冊排在 MDL 冊前 → CGC_MDL258_TempAccel_v0100 拿到 VIA-VCGC-ENV107(VIA_TEMPACCEL_DIR)而不是 MDL1564。
     本版:來源路徑對照只收「名字就是那支檔(去副檔名)」的列 —— 檔自己的實體號;環境變數 · 選項 · 政策列不算。
  ② (P1)v0105 的 _ui_tokens() 預設在引擎旁邊找 VIA_UI_Template_SSOT;VTK 副本在 VTK/syscat,旁邊沒有冊 → 頁面變數全空。
     本版:先讀正本位置 <VIA>/supportive modules/registry(唯讀),沒有才退回引擎旁邊;仍只取尾版 tokens,本檔不帶色碼。
版號說明:v0106 已被 VTK 照版號複製(VTK 視版號不可改),修改照「修改開新版」出 v0107。
其餘動詞(build · query · syscat · guard · page …)全部照前版。唯讀;不出網;零 TA-Lib;不設同意閘。
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
import json
import re
import sys
from pathlib import Path

ENGINE = "CGC_MDL228_VIADBManager_v0107"
VERSION = "v0107"
HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL228_VIADBManager"
UI_STEM = "VIA_UI_Template_SSOT"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("cgc_mdl228_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE
PAGE_MOD = PRIOR.PRIOR            # v0105:page 叫的 _ui_tokens 在它的模組全域


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _stem(s: str) -> str:
    s = str(s or "").replace("\\", "/").rsplit("/", 1)[-1]
    return re.sub(r"\.(py|ps1|psm1|cmd|bat|sh)$", "", s, flags=re.I)


def num_maps(recs: list) -> tuple:
    """→ (來源路徑→號, 名字→號)。只收檔自己的實體列:來源不是 .json 卡冊,而且名字(去副檔名)就是來源檔名;
    沒寫來源的列只進名字對照。環境變數 · 選項 · 政策等「來源指向某支檔」的列不當那支檔的號。"""
    by_src, by_name = {}, {}
    for d in recs:
        code, name = str(d.get("code") or ""), str(d.get("name") or d.get("file") or "")
        src = str(d.get("source") or "").replace("\\", "/")
        if not code:
            continue
        own = bool(src) and not src.lower().endswith(".json") and bool(name) and _stem(name) == _stem(src)
        if own:
            by_src.setdefault(src, code)
        if name and (not src or own):
            by_name.setdefault(_stem(name), code)
    return by_src, by_name


def registry_dir(start: Path = HERE) -> Path:
    """VIA 樹的鎖定冊正本位置(<VIA>/supportive modules/registry);找不到回 start。"""
    p = Path(start).resolve()
    for q in (p, *p.parents):
        if (q / "supportive modules" / "registry").is_dir():
            return q / "supportive modules" / "registry"
    return Path(start)


_ORIG_UI_TOKENS = PAGE_MOD._ui_tokens


def _ui_tokens(reg: Path = None) -> tuple:
    """視覺值只取鎖定冊 VIA_UI_Template_SSOT 尾版 tokens:先正本位置(唯讀),沒有才退回引擎旁邊。"""
    for r in ([Path(reg)] if reg is not None else []) + [registry_dir(HERE), HERE]:
        if sorted(Path(r).glob(UI_STEM + "_v[0-9][0-9][0-9][0-9].json")):
            return _ORIG_UI_TOKENS(Path(r))
    return _ORIG_UI_TOKENS(Path(reg) if reg is not None else HERE)


_ORIG_NUM_MAPS = PRIOR.num_maps


def _install():
    PRIOR.num_maps = num_maps                       # v0106 的 fix_rows 依模組全域名叫 num_maps
    PAGE_MOD._ui_tokens = _ui_tokens                # v0105 的 page 依模組全域名叫 _ui_tokens


def _uninstall():
    PRIOR.num_maps = _ORIG_NUM_MAPS
    PAGE_MOD._ui_tokens = _ORIG_UI_TOKENS


_install()


def norm_sys(d: dict) -> str:
    return PRIOR.norm_sys(d)


def fix_rows(rows: dict) -> dict:
    return PRIOR.fix_rows(rows)


def collect(*a, **k):                               # 必備 API:照前版轉交(fix_rows 已用本版 num_maps)
    return PRIOR.collect(*a, **k)


def build(*a, **k):
    return PRIOR.build(*a, **k)


def query(*a, **k):
    return PRIOR.query(*a, **k)


def syscat(*a, **k):
    return PRIOR.syscat(*a, **k)


def guard(*a, **k):
    return PRIOR.guard(*a, **k)


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, got=None):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · %s" % str(got)[:300]), flush=True)

    chk("① 加速器真的載到(VIA_ACCEL is not None)", globals().get("VIA_ACCEL") is not None)
    src = "supportive modules/registry/CGC_MDL258_TempAccel_v0100.py"
    recs = [{"code": "VIA-VCGC-ENV107", "name": "VIA_TEMPACCEL_DIR", "kind": "ENV", "sub": "VCGC", "source": src},
            {"code": "VIA-VCGC-MDL1564", "name": "CGC_MDL258_TempAccel_v0100", "kind": "MDL", "sub": "VCGC", "source": src},
            {"code": "VIA-VDF-LGC007", "name": "VDF_ENG092_X_v0100", "sub": "VDF",
             "source": "supportive modules/registry/VIA_Essentia_CardBook_CGC_v0100.json"},
            {"code": "VIA-VDF-ENG005", "name": "VDF_ENG092_X_v0100", "sub": "VDF", "source": "functional modules/VDF/VDF_ENG092_X_v0100.py"}]
    rows = {"numbers": [[d.get("kind", "MDL"), d["code"], d["name"], "", json.dumps(d)] for d in recs],
            "families": [["CGC_MDL258_TempAccel", "VCGC", "supportive modules/registry", ".py", 1, "v0100", "v0100", src, "", ""],
                         ["VDF_ENG092_X", "VDF", "functional modules/VDF", ".py", 1, "v0100", "v0100",
                          "functional modules/VDF/VDF_ENG092_X_v0100.py", "", ""]]}
    fix_rows(rows)
    chk("② 同一支檔 ENV 列排在前:家族號仍是檔自己的 MDL1564(不是 ENV107)", rows["families"][0][8] == "VIA-VCGC-MDL1564", rows["families"][0])
    chk("③ 前版案例照舊:ENG092 → ENG005(同名 LGC 卡號不蓋)", rows["families"][1][8] == "VIA-VDF-ENG005", rows["families"][1])
    chk("④ 已裝進前版(fix_rows 叫本版 num_maps · page 叫本版 _ui_tokens)· 必備 API 照前版轉交",
        PRIOR.num_maps is num_maps and PAGE_MOD._ui_tokens is _ui_tokens
        and all(callable(globals()[n]) for n in ("collect", "build", "query", "syscat", "guard", "main", "selftest"))
        and guard("SELECT 1") == PRIOR.guard("SELECT 1"))
    with tempfile.TemporaryDirectory() as td:
        via = Path(td) / "VIA"
        reg, cp = via / "supportive modules" / "registry", via / "VTK" / "syscat"
        reg.mkdir(parents=True)
        cp.mkdir(parents=True)
        (reg / (UI_STEM + "_v0100.json")).write_text(json.dumps({"tokens": {"bg": "old"}}), encoding="utf-8")
        (reg / (UI_STEM + "_v0101.json")).write_text(json.dumps({"tokens": {"bg": "tail", "txt": "t"}}), encoding="utf-8")
        g = globals()
        here0 = g["HERE"]
        try:
            g["HERE"] = cp
            root, name = _ui_tokens()
        finally:
            g["HERE"] = here0
        chk("⑤ 引擎在副本夾(旁邊沒冊):讀正本位置的尾版 tokens(--bg:tail)",
            name == UI_STEM + "_v0101.json" and "--bg:tail" in root and "--txt:t" in root, (root, name))
        root2, name2 = _ui_tokens(Path(td) / "nowhere")
        chk("⑥ 現役 registry 照舊找到鎖定冊(不回灰)", name2.startswith(UI_STEM) and root2.startswith(":root{"), (root2[:80], name2))
    rc = PRIOR.selftest()
    chk("⑦ 前版 v0106 自測(含 v0105 全套)本版裝著照過", rc == 0, rc)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 檔面:第 3 行加速器標記 · glob 取前版 · 零 TA-Lib · 不設同意閘",
        text.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "HERE.glob(_STEM" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", text, re.M))
    n = sum(ok)
    print("[selftest] %s · %d/%d · %s" % ("GREEN" if n == len(ok) else "RED", n, len(ok), ENGINE), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
