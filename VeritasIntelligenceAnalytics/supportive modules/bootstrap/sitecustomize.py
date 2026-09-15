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
  ① 加速器(所有家族):批487 起**快取優先**——套用 via-accel --activate 存下的 17 個執行緒預算環境變數(微秒級),
     不在啟動層載 Celeritas;VIA_ACCEL_BOOT = "cache:<可用>/<冊>:<n>env" | "NOCACHE:…" | (VIA_ACCEL_FULL=1 時)"1:…"
  ③ 資料家(批490):目錄頁/MDL123 → env VIA_DATA_HOME、VIA_DB_<庫名>(引擎按名取路徑;家不在=誠實不設)
  ④ 正典工具本名掛載(批494):VeritasCeleritas / VeritasAegisNexus 惰性代理進 sys.modules;VIA_TOOLS_MOUNT 存證
  ② 網路正典件(VIA_FAMILY=vdf 時;其餘家族不掛):尾版 SUP_MDL740 →
     註冊成 sys.modules["via_net"],引擎可 `import via_net` 用 http_json/http_bytes/yf_download
     → VIA_NET_BOOT = "1" 或 "ABSENT:<原因>"
     **同意閘一個字都不碰**:gate_state 是操作員設的就是操作員設的;沒設就 fail-closed。
     也**不 monkeypatch requests**——靜靜改變別人行為,正是這套系統最恨的那種病。
  ③ 預設零輸出。VIA_BOOT_VERBOSE=1 才在 stderr 印一行。VIA_BOOT=0 整個關掉。
  ⑤ PYTHONHOME 撤除(批514 律 L32 子行程環境衛生):母殼帶著 PYTHONHOME(操作員實錄 …\uv\python\cpython-3.12-…)時,本行程起得來
     但它生的家族境子行程(C:\Python313 3.13 venv)一律載到 3.12 標準庫="SRE module mismatch"。PYTHONHOME 對 VIA 任何子行程都無正當用途
     (venv/base 各自從 python.exe 算 home),起跑就撤、記 VIA_PYTHONHOME_SCRUBBED(誠實存證);VIA_KEEP_PYTHONHOME=1 可保留。根治=操作員的手。

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


def _newest_json(dirpath, prefix):
    try:
        names = sorted(n for n in os.listdir(dirpath) if n.startswith(prefix) and n.endswith(".json"))
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


import types as _types


class _LazyTool(_types.ModuleType):
    """正典工具的惰性掛載代理(批494):掛在 sys.modules 本名下,第一次取屬性才把真檔載入並換成真模組。"""

    def __init__(self, name, path):
        super().__init__(name)
        self.__dict__["_via_path"] = path
        self.__dict__["_via_real"] = None
        self.__dict__["__file__"] = path

    def _via_load(self):
        real = self.__dict__["_via_real"]
        if real is None:
            import importlib.util
            spec = importlib.util.spec_from_file_location(self.__name__, self.__dict__["_via_path"])
            real = importlib.util.module_from_spec(spec)
            sys.modules[self.__name__] = real          # dataclass 於 3.11+ 必查 sys.modules[__module__]
            try:
                spec.loader.exec_module(real)
            except Exception:
                sys.modules[self.__name__] = self      # 載入失敗=代理留著,誠實丟例外給呼叫端
                raise
            self.__dict__["_via_real"] = real
        return real

    #: 只有這幾個 import/反射機關會探的名字不觸發載入;__version__/__all__ 這類真屬性照常載入後回答
    _NO_LOAD = frozenset({"__path__", "__wrapped__", "__signature__", "__func__", "__self__", "__origin__",
                          "__args__", "__parameters__", "__mro_entries__", "__class_getitem__", "__getstate__"})

    def __getattr__(self, item):
        if item in self._NO_LOAD:
            raise AttributeError(item)
        return getattr(self._via_load(), item)

    def __dir__(self):
        try:
            return dir(self._via_load())
        except Exception:
            return []


_NEVER_APPLY = frozenset({"PATH", "PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP", "PYTHONEXECUTABLE", "PYTHONUSERBASE", "VIRTUAL_ENV", "CONDA_PREFIX", "HOME", "USERPROFILE"})


def _scrub_pythonhome(note):
    r"""批514 Z15 根因:母殼(PowerShell 視窗/profile/via_core 啟動)帶著 PYTHONHOME=…\uv\python\cpython-3.12-…;
    本行程(base/via_core 3.12)起得來,它生的家族境子行程(C:\Python313 3.13 venv)卻一律載 3.12 標準庫 → "SRE module mismatch"。
    PYTHONHOME 對 VIA 的任何子行程都沒有正當用途(venv/base 各自從自己的 python.exe 算 home),所以起跑就從本行程環境撤掉
    (本行程自己早已用完它),子行程永不繼承;撤了什麼寫在 VIA_PYTHONHOME_SCRUBBED(誠實存證,RunGate/VCGC 讀得到)。
    VIA_KEEP_PYTHONHOME=1 可保留(嵌入式、自知在做什麼的人)。根治=操作員的手:殼層/profile/使用者環境變數把它拿掉。"""
    ph = os.environ.get("PYTHONHOME")
    if ph and os.environ.get("VIA_KEEP_PYTHONHOME") != "1":
        os.environ.pop("PYTHONHOME", None)
        os.environ["VIA_PYTHONHOME_SCRUBBED"] = ph
        note.append("PYTHONHOME 撤(子行程不繼承):" + ph[:70])


def _boot():
    if os.environ.get("VIA_BOOT", "1") == "0":
        return
    # 批489 操作員實錄:via-boot 的 [vdf] 印「網路件(不掛)· via_net False」——因為父行程(匯流排本身也在啟動層下跑)
    # 已設 VIA_ACCEL_BOOT,第一版在這裡整段 return,連 vdf 該掛的網路件都跳掉;子行程印的還是父行程的值。
    # 改:每個行程都各做各的(環境變數本來就 setdefault、網路件本來就依 VIA_FAMILY),不靠「父做過就跳」。
    root = _via_root()
    fam = (os.environ.get("VIA_FAMILY") or "").lower()
    note = []
    try:
        _scrub_pythonhome(note)
    except Exception:
        pass
    # ① 加速器——批487 改**快取優先**(操作員實錄:via-boot 每次動不了)。
    #   量過:載 Celeritas 一次要拉進 numpy/pandas/duckdb/pyarrow 共 95 個模組,容器(11 個庫)+190ms,
    #   操作員機器(88 件冊全裝)是每支 python 指令前面一大段空白。加速的**效果**其實只是那 17 個
    #   執行緒預算環境變數(OMP_NUM_THREADS…),而 `via-accel --activate` 早就把它們存在
    #   VIA_Reports/accel_activation/ACCEL_ACTIVATION_*.json 的 applied 裡。
    #   起跑時只套用快取(微秒級),永不在啟動層載 Celeritas;沒快取=誠實標 NOCACHE(跑一次 via-accel 即可);
    #   VIA_ACCEL_FULL=1 才走舊的完整 activate(給 via-accel 自己或想強制的人)。
    try:
        if os.environ.get("VIA_ACCEL_FULL") == "1":
            p = _newest(os.path.join(root, "supportive modules"), "SUP_MDL737_SuperAccelModule_v")
            if not p:
                raise FileNotFoundError("SUP_MDL737_SuperAccelModule_v*.py 缺")
            acc = _load(p, "via_accel")
            r = acc.activate(apply_limits=True)
            os.environ["VIA_ACCEL_BOOT"] = (f"1:{r.get('libs_available', 0)}/{r.get('libs_total', 0)}"
                                            if r.get("celeritas") else "ABSENT:" + str(r.get("err") or "Celeritas 缺")[:80])
        else:
            cache = _newest_json(os.path.join(root, "VIA_Reports", "accel_activation"), "ACCEL_ACTIVATION_")
            if cache:
                import json
                with open(cache, "r", encoding="utf-8") as fh:
                    r = json.load(fh)
                n = 0
                # 批509 護欄:快取只准套執行緒預算類變數;PYTHON*/PATH/VIRTUAL_ENV/CONDA_PREFIX 永不從快取套(套錯版 PYTHONHOME/PYTHONPATH=
                #   子行程家族境 python 起跑就 "SRE module mismatch";操作員實錄 via_vdf_312/via_vrn_312 全站同病)
                for k, v in (r.get("applied") or {}).items():
                    if isinstance(k, str) and k.isupper() and v is not None and k not in os.environ and not k.startswith("PYTHON") and k not in _NEVER_APPLY:
                        os.environ[k] = str(v); n += 1
                os.environ["VIA_ACCEL_BOOT"] = f"cache:{r.get('libs_available', 0)}/{r.get('libs_total', 0)}:{n}env"
            else:
                os.environ["VIA_ACCEL_BOOT"] = "NOCACHE:跑一次 via-accel 即有快取"
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
    # ③ 資料家(批490 操作員宣告 C:\\Users\\tonyk\\VIA System\\via_database):把「庫在哪」放進 env,引擎按名取路徑,不寫死。
    #   快取優先:目錄頁 VIA_Reports/datahome/DATAHOME_CATALOG_latest.json(via-datahome catalog 產)→ VIA_DATA_HOME + VIA_DB_<庫名大寫>;
    #   沒目錄頁才載 MDL123 尾版 resolve_home()(純標準庫,毫秒級);家不在=誠實標缺,不設。已設者一律尊重。
    try:
        if not os.environ.get("VIA_DATA_HOME"):
            import json
            cat = os.path.join(root, "VIA_Reports", "datahome", "DATAHOME_CATALOG_latest.json")
            home, how, n = None, "", 0
            if os.path.isfile(cat):
                with open(cat, "r", encoding="utf-8") as fh:
                    j = json.load(fh)
                if j.get("home") and os.path.exists(j["home"]):
                    home, how = j["home"], "目錄頁"
                    for name, path in (j.get("by_name") or {}).items():
                        k = "VIA_DB_" + "".join(ch if ch.isalnum() else "_" for ch in os.path.splitext(name)[0]).upper()
                        if os.path.exists(path) and k not in os.environ:
                            os.environ[k] = str(path); n += 1
            if home is None:
                p = _newest(os.path.join(root, "supportive modules", "registry"), "CGC_MDL123_DataHome_v")
                if p:
                    h, src = _load(p, "via_datahome").resolve_home()
                    if os.path.exists(str(h)):
                        home, how = str(h), "MDL123 " + str(src)
                    else:
                        os.environ["VIA_DATAHOME_BOOT"] = f"ABSENT:{h}({src})"
            if home is not None:
                os.environ["VIA_DATA_HOME"] = home
                os.environ["VIA_DATAHOME_BOOT"] = f"{how}:{home}:{n}庫"
        else:
            os.environ.setdefault("VIA_DATAHOME_BOOT", "env:" + os.environ["VIA_DATA_HOME"])
        note.append("資料家 " + os.environ.get("VIA_DATAHOME_BOOT", "缺"))
    except Exception as exc:
        os.environ["VIA_DATAHOME_BOOT"] = f"ABSENT:{type(exc).__name__}:{str(exc)[:60]}"
        note.append("資料家 " + os.environ["VIA_DATAHOME_BOOT"])
    # ④ 兩件正典工具**以本名掛載**(批494 操作員令「未經過我同意…這兩個是我指令唯一的加速器及網路工具,重新掛載」):
    #   批487 為解 via-boot 卡住,把啟動層改成只套快取不載 Celeritas——那等於沒經同意把加速器從每個行程卸下。
    #   現在每個行程都把 VeritasCeleritas / VeritasAegisNexus 掛進 sys.modules(惰性代理:首次取屬性才真載入,
    #   起跑零等待;`import VeritasCeleritas` 在任何 VIA 行程都直接可用);VIA_ACCEL_FULL=1 仍是起跑就真點亮。
    #   正典路徑同 SUP_MDL737 CEL_CANDIDATES / SUP_MDL740 AEGIS 正典序;橋(737/740)留作橋,工具只認這兩件。
    try:
        mounted = []
        for name, rels in (("VeritasCeleritas", ("supportive modules/VeritasCeleritas.py",
                                                 "supportive modules/50_Protection_Acceleration/VeritasCeleritas.py",
                                                 "supportive modules/accelerator/VeritasCeleritas.py")),
                           ("VeritasAegisNexus", ("supportive modules/network/VeritasAegisNexus.py",
                                                  "supportive modules/VeritasAegisNexus.py"))):
            real = sys.modules.get(name)
            if real is not None and not isinstance(real, _LazyTool):
                mounted.append(f"{name}=loaded"); continue
            path = next((os.path.join(root, r) for r in rels if os.path.isfile(os.path.join(root, r))), None)
            if not path:
                mounted.append(f"{name}=ABSENT"); continue
            if real is None:
                sys.modules[name] = _LazyTool(name, path)
            mounted.append(f"{name}=lazy:{path}")
        os.environ["VIA_TOOLS_MOUNT"] = ";".join(mounted)
        note.append("正典工具 " + " · ".join(m.split("=")[0] + "(" + m.split("=")[1].split(":")[0] + ")" for m in mounted))
    except Exception as exc:
        os.environ["VIA_TOOLS_MOUNT"] = f"ABSENT:{type(exc).__name__}:{str(exc)[:60]}"
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
