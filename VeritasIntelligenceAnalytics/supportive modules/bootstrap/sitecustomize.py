# -*- coding: utf-8 -*-
r"""
VIA 啟動層 bootstrap(批476 立;操作員令「所有 PY 檔案都要加上加速器」「VDF 全部還要加入網路工具」)

為什麼放這裡而不是逐檔加一行:
  量過:加速器 SUP_MDL737 在 VDF 引擎只綁 4/109,VRN 0,VAP 0。逐檔補=幾百個 .py,
  尾版律要幾百個新版本檔,正本零觸碰也守不住,而且以後每支新引擎還要記得加。
  Python 起跑時會自動 import 路徑上的 `sitecustomize`,所以只要啟動器把本目錄
  塞進子行程的 PYTHONPATH,**每一支 .py 起跑就綁上**——零檔案改動,一處維護。
  操作員第 5 條「必要時同功能以最小代價整合」,這就是最小代價。

做什麼(全部包在 try 裡;bootstrap 絕不能讓任何引擎起不來):
  ① 加速器(所有家族):尾版 SUP_MDL737 → activate(apply_limits=True)
     → 環境變數 VIA_ACCEL_BOOT = "1:<可用>/<冊總數>" 或 "ABSENT:<原因>"
  ② 網路正典件(VIA_FAMILY=vdf 時;其餘家族不掛):尾版 SUP_MDL740 →
     註冊成 sys.modules["via_net"],引擎可 `import via_net` 用 http_json/http_bytes/yf_download
     → VIA_NET_BOOT = "1" 或 "ABSENT:<原因>"
     **同意閘一個字都不碰**:gate_state 是操作員設的就是操作員設的;沒設就 fail-closed。
     也**不 monkeypatch requests**——靜靜改變別人行為,正是這套系統最恨的那種病。
  ③ 預設零輸出。VIA_BOOT_VERBOSE=1 才在 stderr 印一行。VIA_BOOT=0 整個關掉。

怎麼證明有綁上:`python3 CGC_MDL148_EngineBus_v*.py boot` 起一個子行程回報它看到的。
"""
import os
import sys


def _via_root():
    r = os.environ.get("VIA_ROOT")
    if r and os.path.isdir(r):
        return r
    # 本檔在 <VIA>/supportive modules/bootstrap/ → 往上兩層
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def _newest(dirpath, prefix):
    try:
        names = sorted(n for n in os.listdir(dirpath)
                       if n.startswith(prefix) and n.endswith(".py"))
    except Exception:
        return None
    return os.path.join(dirpath, names[-1]) if names else None


def _load(path, name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _boot():
    if os.environ.get("VIA_BOOT", "1") == "0":
        return
    if os.environ.get("VIA_ACCEL_BOOT"):      # 子行程再往下生子行程:不重做
        return
    root = _via_root()
    fam = (os.environ.get("VIA_FAMILY") or "").lower()
    note = []
    # ① 加速器
    try:
        p = _newest(os.path.join(root, "supportive modules"), "SUP_MDL737_SuperAccelModule_v")
        if not p:
            raise FileNotFoundError("SUP_MDL737_SuperAccelModule_v*.py 缺")
        acc = _load(p, "via_accel")
        r = acc.activate(apply_limits=True)
        if r.get("celeritas"):
            os.environ["VIA_ACCEL_BOOT"] = f"1:{r.get('libs_available', 0)}/{r.get('libs_total', 0)}"
        else:
            os.environ["VIA_ACCEL_BOOT"] = "ABSENT:" + str(r.get("err") or "Celeritas 缺")[:80]
        note.append("加速器 " + os.environ["VIA_ACCEL_BOOT"])
    except Exception as exc:
        os.environ["VIA_ACCEL_BOOT"] = f"ABSENT:{type(exc).__name__}:{str(exc)[:60]}"
        note.append("加速器 " + os.environ["VIA_ACCEL_BOOT"])
    # ② 網路正典件(只掛 vdf;同意閘不碰)
    if fam == "vdf":
        try:
            p = _newest(os.path.join(root, "supportive modules", "network"), "SUP_MDL740_NetUnified_v")
            if not p:
                raise FileNotFoundError("SUP_MDL740_NetUnified_v*.py 缺")
            _load(p, "via_net")
            os.environ["VIA_NET_BOOT"] = "1"
            note.append("網路正典件 via_net 在位(閘態照操作員所設)")
        except Exception as exc:
            os.environ["VIA_NET_BOOT"] = f"ABSENT:{type(exc).__name__}:{str(exc)[:60]}"
            note.append("網路正典件 " + os.environ["VIA_NET_BOOT"])
    if os.environ.get("VIA_BOOT_VERBOSE") == "1":
        sys.stderr.write("  [VIA boot] " + " · ".join(note) + "\n")


def _chain_shadowed():
    r"""批483:本檔靠 PYTHONPATH 前置生效,會**遮住**發行版自帶的 sitecustomize
    (Debian/Ubuntu 的 /usr/lib/python3.x/sitecustomize.py 裝的是 apport 崩潰掛鉤)。
    遮住別人的東西還不吭聲,就是這套系統最恨的那種靜靜走錯。所以接力:
    在 sys.path 上找**下一個**同名檔(排除本目錄),找到就以 runpy 執行它。找不到=正常。
    """
    import runpy
    here = os.path.dirname(os.path.abspath(__file__))
    for d in list(sys.path):
        if not d or os.path.abspath(d) == here:
            continue
        cand = os.path.join(d, "sitecustomize.py")
        if os.path.isfile(cand):
            try:
                runpy.run_path(cand, run_name="sitecustomize_shadowed")
                os.environ["VIA_BOOT_CHAINED"] = cand
            except Exception as exc:
                os.environ["VIA_BOOT_CHAINED"] = f"FAIL:{type(exc).__name__}"
            break


try:
    _boot()
except Exception:
    pass
try:
    _chain_shadowed()
except Exception:
    pass
