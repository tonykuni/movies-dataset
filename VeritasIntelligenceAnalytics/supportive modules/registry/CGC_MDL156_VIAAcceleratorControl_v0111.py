#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL156: VIA 25-accelerator control plane — v0111 asks for the versioned tool names.

v0110→v0111(R20,操作員 2026-09-28「網路工具名稱不對 … 有版本號 VeritasAegisNexus 名稱才對」)
  v0110 量的是無版號檔,在 main 上 RED 35/37:
  ① 兩件工具的「正典掛載」寫死無版號名:accelerator/VeritasCeleritas.py 是 23 行 CLI 座位,
     network/VeritasAegisNexus.py 是本體(不含 v0116 反封鎖梯)。現在改量**版號尾版**:
     Celeritas = SUP_MDL737 解析序首位(零 talib 尾版),Aegis = VeritasAegisNexus_v* 最大號
     (與 SUP_MDL740 _resolve_aegis_path 同序:network 夾先,supportive 夾後)。
  ② ⑤⑥ 解析序原本**文字剖析** SUP_MDL737 尾版裡的 CEL_CANDIDATES = (...) 字面值;
     v0109 起它不再寫死檔名,改問已載入的載入器(VIA_ACCEL.CEL_CANDIDATES),問不到才退回文字剖析。
  ③ 加速器橋全樹尺缺 10 支,正好是 Celeritas 基線冊 py_readonly(正本不准注;CGC_MDL183 已認)。
     豁免名單**讀那本冊**,不在碼裡另抄一份(L05 不立第二把尺)。
  ④ ⑦ 比對的 supportive modules/VeritasCeleritas.py 自 Z218 起由操作員裁定退役(基線冊
     immutable_b345.retired_*)。退役=不在是對的;這一對改由新增的一檢量:不在=綠,
     回到原路徑則位元必須等於冊上 evidence_sha256,否則紅。Aegis 那一對照舊比。檢數 37→38。
  角色照舊:唯讀 · 零網路 · 不安裝;名冊取 VIA_Accelerator_Roster_SSOT_v* 尾版。
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

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL156_VIAAcceleratorControl"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _prior() -> Path:
    mine = _vnum(Path(__file__))
    older = [p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < mine]
    if not older:
        raise ImportError(f"{STEM}: no version below v{mine:04d}")
    return max(older, key=_vnum)


PRIOR = _prior()
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_v{_vnum(Path(__file__)):04d}", PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)

ROOT = _PRIOR.ROOT
SUPP = ROOT / "supportive modules"
_TEXT_ORDER = _PRIOR._cel_resolve_order


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = [p for p in folder.glob(pattern) if re.search(r"_v\d+$", p.stem)]
    return max(hits, key=_vnum) if hits else None


def cel_order() -> list[str]:
    """Resolution order from the loaded loader (SUP_MDL737 tail). Text parse only if it is absent."""
    order = list(getattr(VIA_ACCEL, "CEL_CANDIDATES", None) or ())
    return order or _TEXT_ORDER()


def celeritas_tail() -> Path:
    first = next((SUPP / c for c in cel_order() if (SUPP / c).is_file()), None)
    return first or _newest(SUPP, "VeritasCeleritas_v*.py") or SUPP / "ABSENT-VeritasCeleritas-tail"


def aegis_tail() -> Path:
    for folder in (SUPP / "network", SUPP):
        hit = _newest(folder, "VeritasAegisNexus_v*.py")
        if hit:
            return hit
    return SUPP / "network" / "ABSENT-VeritasAegisNexus-tail"


def baseline() -> dict:
    book = _newest(HERE, "VIA_CeleritasPolicy_Baseline_v*.json")
    if not book:
        return {}
    try:
        return json.loads(book.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_error": f"{book.name}: {type(exc).__name__}"}


def _readonly_exempt() -> tuple:
    files = ((baseline().get("py_readonly") or {}).get("files") or [])
    why = "Celeritas 基線冊 py_readonly:正本不准注(同 CGC_MDL183 ⑦;名單在冊不在碼)"
    return tuple((f, why) for f in files)


RETIRED_REL = "supportive modules/VeritasCeleritas.py"


def retired_check() -> dict:
    ib = baseline().get("immutable_b345") or {}
    retired = next((ib[k] for k in ib if k.startswith("retired_") and isinstance(ib[k], dict)), None)
    path = ROOT / RETIRED_REL
    name = ("批575 Celeritas 正本掛載點(supportive modules/VeritasCeleritas.py)照 Z218 退役:"
            "不在=綠;回到原路徑則位元必須等於冊上 evidence_sha256")
    if ib.get("path") != RETIRED_REL or not retired:
        return _PRIOR.check(name, False, "基線冊沒有這一份的退役裁示")
    if not path.is_file():
        return _PRIOR.check(name, True, f"不在(退役 {retired.get('by', '')});正主 {celeritas_tail().name}")
    raw = path.read_bytes()
    shas = {hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()}
    ok = retired.get("evidence_sha256") in shas
    return _PRIOR.check(name, ok, "回到原路徑且位元吻合冊上證據" if ok else "回到原路徑但位元不是冊上那一份(冒名)")


_PRIOR.CELERITAS = celeritas_tail()
_PRIOR.AEGIS = aegis_tail()
_PRIOR.ROSTER_JSON = _newest(HERE, "VIA_Accelerator_Roster_SSOT_v*.json") or _PRIOR.ROSTER_JSON
_PRIOR._cel_resolve_order = cel_order
_PRIOR._ACCEL_EXEMPT = tuple(_PRIOR._ACCEL_EXEMPT) + _readonly_exempt()
_PRIOR.MOUNT_PAIRS = tuple((n, m) for n, m in _PRIOR.MOUNT_PAIRS
                           if str(m.relative_to(ROOT)).replace("\\", "/") != RETIRED_REL)
_COVERAGE = _PRIOR.coverage_checks


def coverage_checks() -> list:
    out = _COVERAGE()
    out.append(retired_check())
    return out


_PRIOR.coverage_checks = coverage_checks

for _name, _value in vars(_PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value
CELERITAS = _PRIOR.CELERITAS
AEGIS = _PRIOR.AEGIS
ROSTER_JSON = _PRIOR.ROSTER_JSON


def __getattr__(name: str):
    """Every public name of the prior version stays reachable here."""
    return getattr(_PRIOR, name)


_RUN = _PRIOR.run


def run(write: bool = True) -> dict:
    payload = _RUN(write=False)
    payload["engine"] = Path(__file__).stem
    payload["tools"] = {"accelerator": CELERITAS.name, "network": AEGIS.name, "roster": ROSTER_JSON.name}
    if write:
        _PRIOR.REPORT_DIR.mkdir(parents=True, exist_ok=True)
        _PRIOR.LATEST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _PRIOR.LATEST_HTML.write_text(_PRIOR.render_html(payload), encoding="utf-8")
    return payload


_PRIOR.run = run


def main() -> int:
    return _PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())
