#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL008_FetchSystem v0105 — 薄尾:live 模式 urllib 也收進鎖版網路工具 · 真流量計數

操作員 2026-10-04:「開閘授權一切 向前」「全部都要跨入最新加速器跟網路工具」。容器實抓(雙閘開)量到:
  requests(含 akshare 內部)→ 鎖版網路工具 http_bytes / post_json ✓;yfinance → 先問雙閘(= 網路工具車道④同語意)✓;
  但直接呼叫 urllib.request.urlopen 的引擎(MDL004 · ENG055 …)**繞過**網路工具;而且 live 的「網路計數」永遠 0(只算 fixture)。
  本版 live:
    ① urllib.request.urlopen → 鎖版網路工具(GET = http_bytes · 帶 data = post_json);網路工具自己內部也用 urllib
       → 執行緒旗標防重入(工具內的呼叫走原 urlopen,不遞迴)。回應物件給 read() · status · getcode() · headers。
    ② 計數:requests 改道 → requests · urllib 改道 → net · yfinance 過閘 → yf(子行程結尾「網路計數」照實印)。
    ③ 輸出歸位:75 個 ENG 家族把輸出寫死成 `VDF / "output_hub" / …`(VDF 由引擎檔位置推),live 實抓全寫進倉內 / 下載包夾,
       不進 --home。子行程裡把 `… / "output_hub"` 改成 `Path(<--home>) / "output_hub"`:頂層引擎在 compile_engine 改,
       VDF 樹內其他模組(薄尾用 spec_from_file_location 載的前版本體)在 SourceFileLoader.get_code 改。只動記憶體,原檔不動。
其餘(冊 v0103 · fill / fill-matrix / --progress · 雙閘 rc 4)照 v0104。不碰 TA-Lib;不讀寫同意閘(只問網路工具)。
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import ast
import contextlib
import importlib.util
import io
import json
import re
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0105(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0105(p) < _vnum_v0105(__file__)), key=_vnum_v0105)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0101, BASE = PRIOR.V0101, PRIOR.BASE


def __getattr__(name):
    return getattr(PRIOR, name)


_RUN_V0104 = PRIOR.run_v0104
BOOK_V0104 = HERE / "VDF_FetchSystem_SSOT_v0104.json"


def load_book_v0105(path: Path = BOOK_V0104) -> dict:
    return PRIOR.V0102.PRIOR._LOAD_BOOK_V0100(path)
_LIVE_V0100 = BASE._install_live_routes
_COMPILE_V0100 = BASE.compile_engine
_LOAD_V0104 = PRIOR.load_book_v0104
_TL = threading.local()


def run_v0105(*args, **kwargs):
    """同 v0104 run;子行程改從本版起(live 的 urllib 改道與計數在子行程裡生效),呼叫完還原。"""
    keep = PRIOR.__dict__.get("__file__")
    PRIOR.__dict__["__file__"] = str(Path(__file__).resolve())
    try:
        out = _RUN_V0104(*args, **kwargs)
    finally:
        PRIOR.__dict__["__file__"] = keep
    marks = {r["id"]: r.get("nodata_markers") or [] for r in (args[0] if args else kwargs.get("rows") or [])}
    for x in out:                                      # rc 0 卻零擷取(冊上 nodata_markers 見於日誌)→ 照實改判 NODATA(rc 2)
        if x.get("rc") == 0 and marks.get(x["id"]):
            try:
                log = Path(x["log"]).read_text(encoding="utf-8", errors="replace")
            except OSError:
                log = ""
            hit = [m for m in marks[x["id"]] if m in log]
            if hit:
                x["rc"], x["tail"] = 2, (x.get("tail") or []) + [f"[MDL008] NODATA:rc 0 但日誌見「{hit[0]}」= 零擷取(冊 nodata_markers)"]
    return out


class _RoutedResponse(io.BytesIO):
    """urlopen 的回應替身:read() · status · getcode() · geturl() · headers · 可當 context manager。"""

    def __init__(self, data: bytes, url: str, status: int, state: str):
        super().__init__(data)
        self.status, self.code, self.url, self.reason = status, status, url, state
        self.headers = {"X-VIA-Net-State": state}

    def getcode(self):
        return self.status

    def geturl(self):
        return self.url

    def info(self):
        return self.headers


def install_live_routes_v0105(nt) -> None:
    """v0100 live 改道(requests → 網路工具 · yfinance / akshare 過閘)+ urllib 改道 + 真流量計數。"""
    _LIVE_V0100(nt)
    import requests
    import urllib.error
    import urllib.request
    stats = BASE.FIX_STATS
    routed_req = requests.sessions.Session.request

    def count_req(self, method, url, *a, **k):
        if getattr(_TL, "inside", False):                  # 已在網路工具裡(工具內部的 requests)→ 不再改道計數
            return routed_req(self, method, url, *a, **k)
        stats["requests"] += 1
        _TL.inside = True                                  # 網路工具自己內部的 urllib 走原道(不重複抓)
        try:
            return routed_req(self, method, url, *a, **k)
        finally:
            _TL.inside = False
    requests.sessions.Session.request = count_req
    real_urlopen = urllib.request.urlopen

    def routed_urlopen(url, data=None, timeout=30, *a, **k):
        if getattr(_TL, "inside", False):                  # 網路工具自己的 urllib → 原道(防遞迴)
            return real_urlopen(url, data, timeout, *a, **k)
        full = url.full_url if isinstance(url, urllib.request.Request) else str(url)
        hdrs = dict(url.header_items()) if isinstance(url, urllib.request.Request) else None
        body = data if data is not None else (url.data if isinstance(url, urllib.request.Request) else None)
        _TL.inside = True
        try:
            if body is not None:
                try:
                    payload = json.loads(body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else body)
                except (ValueError, UnicodeDecodeError, AttributeError):
                    payload = body.decode("utf-8", "replace") if isinstance(body, (bytes, bytearray)) else body
                r0 = nt.post_json(full, payload=payload, headers=hdrs, timeout=int(timeout or 30))
            else:
                r0 = nt.http_bytes(full, timeout=int(timeout or 30), headers=hdrs)
        finally:
            _TL.inside = False
        stats["net"] += 1
        st = str((r0 or {}).get("state") or "")
        if st == "DENY":
            raise urllib.error.URLError("GATED:鎖版網路工具雙閘未開(不是壞掉)")
        raw = (r0 or {}).get("data")
        blob = raw if isinstance(raw, (bytes, bytearray)) else (json.dumps(raw, ensure_ascii=False).encode("utf-8")
                                                              if isinstance(raw, (dict, list)) else str(raw or "").encode("utf-8"))
        if st != "OK":
            code = 404 if st == "EMPTY" else 502
            raise urllib.error.HTTPError(full, code, f"{st}:{str((r0 or {}).get('note') or '')[:120]}", None, io.BytesIO(blob))
        return _RoutedResponse(bytes(blob), full, 200, st)
    urllib.request.urlopen = routed_urlopen
    yf = sys.modules.get("yfinance")
    for name in ("download", "Ticker", "Tickers"):
        fn = getattr(yf, name, None) if yf is not None else None
        if callable(fn):
            def counted(*a, _fn=fn, **k):
                stats["yf"] += 1
                return _fn(*a, **k)
            setattr(yf, name, counted)


class _HubRewriter(ast.NodeTransformer):
    """`<任何> / "output_hub"` → `__import__("pathlib").Path(<home>) / "output_hub"`(其後的 / "mega" … 照接)。"""

    def __init__(self, home: str):
        self.home, self.n = home, 0

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Div) and isinstance(node.right, ast.Constant) and node.right.value == "output_hub":
            self.n += 1
            path_call = ast.Call(func=ast.Attribute(value=ast.Call(func=ast.Name(id="__import__", ctx=ast.Load()),
                                                                   args=[ast.Constant("pathlib")], keywords=[]),
                                                    attr="Path", ctx=ast.Load()), args=[ast.Constant(self.home)], keywords=[])
            return ast.copy_location(ast.BinOp(left=path_call, op=ast.Div(), right=ast.Constant("output_hub")), node)
        return node


def rewrite_tree_v0105(tree, home) -> int:
    """舊佈局絕對路徑(v0100 同一律)+ output_hub 歸位;回改寫筆數。"""
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for pre in BASE.LEGACY_PREFIXES:
                if node.value.startswith(pre):
                    rest = [x for x in node.value[len(pre):].replace("\\", "/").split("/") if x]
                    node.value = str(Path(home, *rest))
                    n += 1
                    break
    rw = _HubRewriter(str(Path(home)))
    rw.visit(tree)
    ast.fix_missing_locations(tree)
    return n + rw.n


def compile_engine_v0105(path: Path, home: Path):
    """同 v0100 compile_engine(本體碼 · __main__ 段碼 · 改寫筆數),多 output_hub 歸位。"""
    src = Path(path).read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(src, filename=str(path))
    n = rewrite_tree_v0105(tree, home)
    body = [x for x in tree.body if not BASE._is_main_guard(x)]
    mains = [x for x in tree.body if BASE._is_main_guard(x)]
    mk = lambda stmts: compile(ast.Module(body=stmts, type_ignores=[]), str(path), "exec")  # noqa: E731
    return mk(body), mk(mains), n


HUB_STATS_V0105 = {"modules": 0, "rewrites": 0}


def install_loader_hub_v0105(home, root: Path = HERE) -> None:
    """子行程:root 樹內每個以檔案載入的 .py(含薄尾 spec_from_file_location 的前版本體)載入時照樣改寫;樹外照舊。"""
    import importlib.machinery
    loader = importlib.machinery.SourceFileLoader
    if getattr(loader.get_code, "_via_hub_v0105", False):
        return
    real_get_code = loader.get_code
    root_s = str(Path(root).resolve())

    def get_code(self, fullname):
        path = str(getattr(self, "path", "") or "")
        try:
            inside = path.endswith(".py") and str(Path(path).resolve()).startswith(root_s)
        except OSError:
            inside = False
        if not inside:
            return real_get_code(self, fullname)
        tree = ast.parse(Path(path).read_text(encoding="utf-8", errors="replace"), filename=path)
        n = rewrite_tree_v0105(tree, home)
        HUB_STATS_V0105["modules"] += 1
        HUB_STATS_V0105["rewrites"] += n
        return compile(tree, path, "exec")
    get_code._via_hub_v0105 = True
    loader.get_code = get_code


def _install_v0105() -> None:
    BASE._install_live_routes = install_live_routes_v0105
    BASE.compile_engine = compile_engine_v0105
    V0101.load_book_v0101, V0101.BOOK_V0101, BASE.load_book = load_book_v0105, BOOK_V0104, load_book_v0105
    PRIOR.load_book_v0104 = load_book_v0105
    PRIOR.run_v0104 = V0101.run_v0101 = PRIOR.V0102.run_v0102 = BASE.run = run_v0105


_install_v0105()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if args[:1] == ["_child"] and len(args) > 2:
        install_loader_hub_v0105(args[2])             # 子行程:VDF 樹內模組的 output_hub 一律歸位到 --home
        try:
            return PRIOR.main(args)
        finally:
            if HUB_STATS_V0105["modules"]:
                print(f"[MDL008] output_hub 歸位 → {Path(args[2]) / 'output_hub'} · 模組 {HUB_STATS_V0105['modules']} · 改寫 {HUB_STATS_V0105['rewrites']} 處", flush=True)
    return PRIOR.main(args)


def selftest() -> int:
    import urllib.request
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    PRIOR.run_v0104 = _RUN_V0104                       # 前版自測驗前版自己的子行程鏈
    BASE._install_live_routes = _LIVE_V0100
    BASE.compile_engine = _COMPILE_V0100
    PRIOR.load_book_v0104 = _LOAD_V0104
    PRIOR._install_v0104()                             # 前版自測驗前版自己的冊(v0103)
    try:
        rc0 = PRIOR.selftest()
    finally:
        _install_v0105()
    print(f"=== {TAG} · 薄尾自測(live urllib 改道進鎖版網路工具 · 防重入 · 真流量計數)===")
    chk("① v0104 自測過(冊 v0103 · fill --progress · 詳細矩陣 · 網路工具真橋)", rc0 == 0, f"rc {rc0}")
    import requests
    keep_req, keep_url = requests.sessions.Session.request, urllib.request.urlopen
    keep_yf = sys.modules.get("yfinance")
    keep_stats = dict(BASE.FIX_STATS)
    calls = []

    class _NT:
        def gate_state(self):
            return {"open": True}

        def http_bytes(self, url, timeout=30, headers=None):
            calls.append(("GET", url))
            inner = urllib.request.urlopen("data:text/plain,inner-ok").read()     # 工具自己也用 urllib(防重入要走原道)
            return {"state": "OK", "data": b"routed:" + inner}

        def post_json(self, url, payload=None, headers=None, timeout=30):
            calls.append(("POST", url, payload))
            return {"state": "OK", "data": {"echo": payload}}
    try:
        for k in BASE.FIX_STATS:
            BASE.FIX_STATS[k] = 0
        install_live_routes_v0105(_NT())
        body = urllib.request.urlopen("https://example.invalid/a", timeout=5).read()
        post = urllib.request.urlopen(urllib.request.Request("https://example.invalid/b", data=b'{"x": 1}')).read()
        r = requests.get("https://example.invalid/c", timeout=5)
        stats = dict(BASE.FIX_STATS)
    finally:
        requests.sessions.Session.request, urllib.request.urlopen = keep_req, keep_url
        if keep_yf is not None:
            sys.modules["yfinance"] = keep_yf
        BASE.FIX_STATS.update(keep_stats)
    chk("② live:urllib GET → 網路工具 http_bytes(工具內的 urllib 走原道,不遞迴)", body == b"routed:inner-ok" and ("GET", "https://example.invalid/a") in calls, body[:30])
    chk("③ live:urllib 帶 data → 網路工具 post_json(JSON 照解)", json.loads(post) == {"echo": {"x": 1}} and ("POST", "https://example.invalid/b", {"x": 1}) in calls)
    chk("④ live:requests 照 v0100 改道且計數 · urllib 計數(真流量不再是 0)· 工具內部呼叫不重複改道(一請求一抓)",
        r.status_code == 200 and stats["requests"] == 1 and stats["net"] == 2 and len([c for c in calls if c[0] == "GET"]) == 2, (stats, len(calls)))
    chk("⑤ 呼叫完原 urlopen / requests 還原(自測不污染行程)", urllib.request.urlopen is keep_url and requests.sessions.Session.request is keep_req)
    import importlib.machinery
    import tempfile
    keep_gc = importlib.machinery.SourceFileLoader.get_code
    with tempfile.TemporaryDirectory() as tmp:
        root, home = Path(tmp) / "VDF", Path(tmp) / "home"
        (root / "engine").mkdir(parents=True)
        (root / "engine" / "Body_v0100.py").write_text("from pathlib import Path\nVDF = Path(__file__).resolve().parent.parent\n"
                                                      "OUT = VDF / 'output_hub' / 'mega'\nDB = VDF / 'output_hub' / 'mega' / 'x.duckdb'\n", encoding="utf-8")
        (root / "engine" / "Tail_v0101.py").write_text("import importlib.util\nfrom pathlib import Path\n"
                                                      "_s = importlib.util.spec_from_file_location('body_t', Path(__file__).with_name('Body_v0100.py'))\n"
                                                      "B = importlib.util.module_from_spec(_s); _s.loader.exec_module(B)\n"
                                                      "TOP = Path(__file__).resolve().parent.parent / 'output_hub'\n", encoding="utf-8")
        outside = Path(tmp) / "elsewhere.py"
        outside.write_text("from pathlib import Path\nX = Path('/r') / 'output_hub'\n", encoding="utf-8")
        try:
            install_loader_hub_v0105(str(home), root=root)
            body, mains, n_top = compile_engine_v0105(root / "engine" / "Tail_v0101.py", home)
            g = {"__name__": "t", "__file__": str(root / "engine" / "Tail_v0101.py")}
            exec(body, g)
            so = importlib.util.spec_from_file_location("outside_t", outside)
            mo = importlib.util.module_from_spec(so)
            so.loader.exec_module(mo)
        finally:
            importlib.machinery.SourceFileLoader.get_code = keep_gc
        chk("⑦ output_hub 歸位:頂層引擎(compile_engine)與薄尾載的前版本體(get_code)都改到 --home/output_hub;樹外模組不動;原檔不改",
            g["TOP"] == home / "output_hub" and g["B"].OUT == home / "output_hub" / "mega" and g["B"].DB == home / "output_hub" / "mega" / "x.duckdb"
            and n_top == 1 and mo.X == Path("/r") / "output_hub" and "'output_hub'" in (root / "engine" / "Body_v0100.py").read_text(encoding="utf-8"),
            (str(g["TOP"]), str(g["B"].OUT)))
    chk("⑧ 呼叫完 SourceFileLoader.get_code 還原(自測不污染行程)", importlib.machinery.SourceFileLoader.get_code is keep_gc)
    bk = load_book_v0105()
    E = {r["id"]: r for r in bk["engines"]}
    import ast as _a
    defs = {(n.name, n.lineno) for n in _a.walk(_a.parse((HERE / E["e054"]["file"]).read_text(encoding="utf-8"))) if isinstance(n, _a.FunctionDef)}
    chk("⑨ 冊 v0104:e054 → 回補工人 v0109(AST 位置對得上)· e056 / e057 / e063 相依 e054 · MDL011 有 nodata 標記",
        E["e054"]["file"].endswith("_v0109.py") and all((f["name"], f["line"]) in defs for f in E["e054"]["fetch_functions"])
        and all("e054" in E[k]["needs"] for k in ("e056", "e057", "e063")) and E["011"].get("nodata_markers")
        and [r["id"] for r in PRIOR.BASE.ordered(bk["engines"])].index("e054") < [r["id"] for r in PRIOR.BASE.ordered(bk["engines"])].index("e056"))
    with tempfile.TemporaryDirectory() as tmp:
        lg = Path(tmp) / "011_live.log"
        lg.write_text("[WARN] schedule-run: no default_selection.json yet (save one from the console)\n", encoding="utf-8")
        keep_run = _RUN_V0104
        globals()["_RUN_V0104"] = lambda rows, *a, **k: [{"id": "011", "mdl": "MDL011", "rc": 0, "sec": 0.1, "log": str(lg), "tail": []}]
        try:
            res = run_v0105([E["011"]], "live", Path(tmp))
        finally:
            globals()["_RUN_V0104"] = keep_run
    chk("⑩ rc 0 但日誌見 nodata 標記 → 照實改判 NODATA rc 2(不再假綠)", res[0]["rc"] == 2 and "NODATA" in res[0]["tail"][-1], res[0]["rc"])
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋 · 網路橋(模組層 VIA_NET_TOOL_PATH + def _via_net)在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "def _via_net" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · v0104 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
