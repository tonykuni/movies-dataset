#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL228_VIADBManager v0106 — 薄尾(v0105 以前一字不動):syscat 的號照來源檔對 · 系統欄讀冊上的 sys / sub

PR #751 Codex 兩筆(P2):
  ① 家族 tail_code 用「名字 → 號」一張表,同名的 LGC 卡冊列(來源是 .json 卡冊)把引擎自己的號蓋掉
     (VDF_ENG092_TWFlowsAdjConsensus → LGC007,應為 ENG005)。
  ② numbers.system 讀 'system' 欄,編號冊根本沒有 → 全空。
本版包 v0105 的 collect():建完照原樣回傳前,
  · numbers 的系統欄:有 system 用 system;否則照 sub(VCGC / VDF / VRN / VRN2→VRN / VQG / VAP / SUP);
    只有 code 的函式級列取 code 第二段;其他歸 VIA。
  · families 的 tail_code:先照「來源路徑 → 號」(來源是 .json 卡冊的不算);沒有再照名字,而且只收來源就是那支檔(或沒寫來源)的列。
版號說明:v0105 已被 VTK 照版號複製(VTK 視版號不可改),修改照「修改開新版」出 v0106;v0105 還原原樣。
其餘動詞(build · query · syscat · guard · page …)全部照 v0105。唯讀;不出網;零 TA-Lib;不設同意閘。
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

ENGINE = "CGC_MDL228_VIADBManager_v0106"
VERSION = "v0106"
HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL228_VIADBManager"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("cgc_mdl228_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


_SUBS = {"VCGC": "VCGC", "VDF": "VDF", "VRN": "VRN", "VRN2": "VRN", "VRN-2": "VRN", "VQG": "VQG", "VAP": "VAP", "SUP": "SUP"}


def norm_sys(d: dict) -> str:
    if d.get("system"):
        return str(d["system"])
    sub = str(d.get("sub") or "").upper()
    if not sub:
        m = re.match(r"VIA-([A-Z0-9]+)-", str(d.get("code") or ""))
        sub = m.group(1) if m else ""
    if sub in _SUBS:
        return _SUBS[sub]
    return "VIA" if (d.get("sys") or sub) else ""


def num_maps(recs: list) -> tuple:
    """→ (來源路徑→號, 名字→號)。.json 卡冊來源不當檔的號;名字對照只收來源就是那支檔(或沒寫來源)的列。"""
    by_src, by_name = {}, {}
    for d in recs:
        code, name = str(d.get("code") or ""), str(d.get("name") or d.get("file") or "")
        src = str(d.get("source") or "").replace("\\", "/")
        if not code:
            continue
        own = bool(src) and not src.lower().endswith(".json")
        if own:
            by_src.setdefault(src, code)
        if name and (not src or (own and src.rsplit("/", 1)[-1].rsplit(".", 1)[0] == name)):
            by_name.setdefault(name, code)
    return by_src, by_name


def fix_rows(rows: dict) -> dict:
    recs = []
    for r in rows.get("numbers") or []:
        try:
            d = json.loads(r[4])
        except (ValueError, TypeError, IndexError):
            d = {"code": r[1] if len(r) > 1 else "", "name": r[2] if len(r) > 2 else ""}
        recs.append(d)
        if len(r) > 3:
            r[3] = norm_sys(d)
    by_src, by_name = num_maps(recs)
    for f in rows.get("families") or []:
        if len(f) > 8:
            stem = Path(str(f[7])).name.rsplit(".", 1)[0]
            f[8] = by_src.get(str(f[7])) or by_name.get(stem, "")
    return rows


_ORIG_COLLECT = PRIOR.collect


def collect(via: Path, prev_stat=None) -> tuple:
    rows, three, sources = _ORIG_COLLECT(via, prev_stat)
    return fix_rows(rows), three, sources


def _install():
    PRIOR.collect = collect                         # v0105 的 build 依模組全域名叫 collect


def _uninstall():
    PRIOR.collect = _ORIG_COLLECT


_install()


def build(*a, **k):                                 # 必備 API:載入器 / 控管會叫的名字照前版轉交(collect 已換成本版)
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
    return PRIOR.main(a) if argv is not None else PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, got=None):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · %s" % str(got)[:300]), flush=True)

    chk("① 加速器真的載到(VIA_ACCEL is not None)", globals().get("VIA_ACCEL") is not None)
    recs = [{"code": "VIA-VDF-ENG005", "name": "VDF_ENG092_X_v0100", "sys": "VIA", "sub": "VDF", "source": "functional modules/VDF/VDF_ENG092_X_v0100.py"},
            {"code": "VIA-VDF-LGC007", "name": "VDF_ENG092_X_v0100", "sys": "VIA", "sub": "VDF",
             "source": "supportive modules/registry/VIA_Essentia_CardBook_CGC_v0100.json"},
            {"code": "VIA-CORE-ENG001", "name": "Y", "sys": "VIA", "sub": "CORE"}]
    rows = {"numbers": [["MDL" if i != 1 else "LGC", d["code"], d["name"], "", json.dumps(d)] for i, d in enumerate(recs)]
            + [["FNC", "VIA-VDF-ENG001-CLS001-FNC001", "f", "", json.dumps({"code": "VIA-VDF-ENG001-CLS001-FNC001"})]],
            "families": [["VDF_ENG092_X", "VDF", "functional modules/VDF", ".py", 1, "v0100", "v0100",
                          "functional modules/VDF/VDF_ENG092_X_v0100.py", "VIA-VDF-LGC007", ""]]}
    fix_rows(rows)
    chk("② 家族尾版號照來源檔:ENG005(同名 LGC 卡號不蓋過去)", rows["families"][0][8] == "VIA-VDF-ENG005", rows["families"])
    chk("③ 系統欄:sub VDF → VDF · CORE → VIA · 只有 code 的函式級列取第二段 → VDF",
        [r[3] for r in rows["numbers"]] == ["VDF", "VDF", "VIA", "VDF"], [r[3] for r in rows["numbers"]])
    chk("④ 已裝進 v0105(build 叫的 collect 是本版)· 必備 API 照前版轉交",
        PRIOR.collect is collect and all(callable(globals()[n]) for n in ("build", "query", "syscat", "guard", "main", "selftest"))
        and guard("SELECT 1") == PRIOR.guard("SELECT 1"))
    rc = PRIOR.selftest()
    chk("⑤ 前版 v0105 自測(本版裝著:舊式只有名字的號列照舊對上)照過", rc == 0, rc)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 檔面:第 3 行加速器標記 · glob 取前版 · 零 TA-Lib · 不設同意閘",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "HERE.glob(_STEM" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    n = sum(ok)
    print("[selftest] %s · %d/%d · %s" % ("GREEN" if n == len(ok) else "RED", n, len(ok), ENGINE), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
