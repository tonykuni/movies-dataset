#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VIA_LibCanon — 三庫正典轉接件(批597)
======================================================================
操作員令(批597):「整合好 VDF 的參數庫因子庫邏輯庫」。

本件的角色跟 `VIA_SuperAccel_Module` 一模一樣:**穩定名字的轉接口**,
底下用尾版律接真正的正典本體,呼叫端永遠不寫死版號。

  參數/旗標      SUP_MDL753_VIACommonUtils_v*   argval · num · hash8 · safe_import
  尾版取用       SUP_MDL751_VIATailPick_v*      newest · newest_pr · bind
  JSON 讀寫      SUP_MDL752_VIAJsonIO_v*        read · write

律:
  ① **缺席大聲拋**,不 graceful。正典不在就別假裝有——批596 學到的,
     靜默回 None 跟假綠是同一個病(LL151)。
  ② 呼叫端拿到的是**綁定**不是新的 `def`。再包一層 `def` 的話,
     能力庫裡那個家族還在,家族數不會掉=等於沒併(LL143)。
  ③ 行為差異**寫成參數**,不寫死成「大家都一樣」。批597 量到 VDF 五支
     `_num` 分群之後是**五個群**,強行併成一支就是遷出行為變更(L75)。

自測:`python3 VIA_LibCanon.py --selftest`(零網路;唯讀)
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

import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _Path

_HERE = _Path(__file__).resolve().parent

#: 轉接的三本正典(穩定鍵 → 檔名 stem 樣式)
CANON_GLOBS = {
    "utils": "SUP_MDL753_VIACommonUtils_v*.py",
    "tail": "SUP_MDL751_VIATailPick_v*.py",
    "json": "SUP_MDL752_VIAJsonIO_v*.py",
}


def _load(key: str):
    """尾版律載入正典本體;缺席=**大聲拋**(律①)。"""
    hits = sorted(_HERE.glob(CANON_GLOBS[key]))
    if not hits:
        raise ImportError(
            f"[FAIL] 三庫正典缺席:supportive modules/{CANON_GLOBS[key]}"
            "(批597 不提供 graceful 退路——正典不在就別假裝有)")
    name = hits[-1].stem
    spec = _ilu.spec_from_file_location(name, hits[-1])
    mod = _ilu.module_from_spec(spec)
    _sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod, hits[-1].name


UTILS, CANONICAL_UTILS = _load("utils")
TAIL, CANONICAL_TAIL = _load("tail")
JSONIO, CANONICAL_JSON = _load("json")

#: 直接再輸出(**綁定不是 def**,律②)
argval = UTILS.argval          # 參數庫:從 argv 取旗標值
num = UTILS.num                # 邏輯庫:逗號千分位字串 → float / None
hash8 = UTILS.hash8
safe_import = UTILS.safe_import
nan_safe = UTILS.nan_safe
bind_jwrite = UTILS.bind_jwrite

newest = TAIL.newest           # 邏輯庫:尾版取用
newest_pr = TAIL.newest_pr
bind_newest = TAIL.bind

jread = JSONIO.read            # 邏輯庫:JSON 讀寫
jwrite = JSONIO.write

CANONICAL = {"utils": CANONICAL_UTILS, "tail": CANONICAL_TAIL, "json": CANONICAL_JSON}


def selftest() -> int:
    n, fails = [0], []

    def chk(label, ok, extra=""):
        n[0] += 1
        print(f"  [{'OK' if ok else 'FAIL'}] {label}" + (f" ({extra})" if extra else ""))
        if not ok:
            fails.append(label)

    chk("① 三本正典都接得到(尾版律;版號一律動態解析不寫死)",
        all(CANONICAL.values()), " · ".join(f"{k}={v}" for k, v in CANONICAL.items()))
    chk("② 轉出的是**綁定**不是新 def(LL143:再包一層 def 的話家族數不會掉=等於沒併)",
        num is UTILS.num and newest is TAIL.newest and jwrite is JSONIO.write)
    chk("③ 缺席**大聲拋**不 graceful(律①;靜默回 None 跟假綠同一個病 LL151)",
        "raise ImportError" in _Path(__file__).read_text(encoding="utf-8")
        and "graceful" not in _Path(__file__).read_text(encoding="utf-8").split("律:")[-1].split("自測")[0].replace("不提供 graceful 退路", ""))
    # LL133:一把尺不能是它要量的東西的一部分。第一版這一檢拿**字串**比自己的原始碼,
    #   而檢查清單裡就寫著 requests / subprocess ——當場自己判自己 FAIL(批590 踩過同一個)。
    #   改成問**語法樹**:比的是真的有沒有 import 那些模組,不是檔案裡有沒有那幾個字。
    import ast as _ast
    _tree = _ast.parse(_Path(__file__).read_text(encoding="utf-8"))
    _mods = set()
    for _nd in _ast.walk(_tree):
        if isinstance(_nd, _ast.Import):
            _mods |= {a.name.split(".")[0] for a in _nd.names}
        elif isinstance(_nd, _ast.ImportFrom) and _nd.module:
            _mods.add(_nd.module.split(".")[0])
    _dirty = _mods & {"requests", "httpx", "urllib", "socket", "subprocess", "pip"}
    chk("④ 零網路/零安裝(問語法樹不是比字串;本件只做 importlib 尾版解析)",
        not _dirty, f"import 到的模組 {sorted(_mods)}" if not _dirty else f"髒 {sorted(_dirty)}")
    # ⑤ 三本各抽一個行為,確認真的是那一本在做事
    chk("⑤ num 帶參數的行為真的到得了正典(positive=True 擋掉 0/-inf/nan)",
        num("0") == 0.0 and num("0", positive=True) is None
        and num("-inf", positive=True) is None and num("nan", positive=True) is None)
    chk("⑥ argval 的 default 每次回新的一份(L76/LL147)",
        (lambda a, b: a is not b and b == [])(argval([], "--x", default=[]),
                                              argval([], "--x", default=[])))
    chk("⑦ newest 吃得下 `**`(批597 補洞:以前靜默回 None=假的「沒找到」)",
        newest(_HERE, "**/SUP_MDL753_VIACommonUtils_v*.py") is not None)
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in _sys.argv[1:]:
        print("=== 三庫正典轉接件(VIA_LibCanon 批597)· 七檢自測(零網路;唯讀)===")
        return selftest()
    print("VIA_LibCanon — 三庫正典轉接件(批597)")
    for k, v in CANONICAL.items():
        print(f"  {k:6s} → {v}")
    print("  自測:python3 VIA_LibCanon.py --selftest")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
