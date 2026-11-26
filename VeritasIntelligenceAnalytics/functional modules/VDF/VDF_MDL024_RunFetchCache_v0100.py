#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL024_RunFetchCache v0100 — 同一輪擷取共用回應快取(同一個請求只真的送一次)

操作員 2026-11-26「YES FOR ALL」核准第 1 項:同一個 API 不重複擷取、速度最快化,但不合併引擎。
盤點:VDF 擷取引擎多半直接用 requests / urllib(requests.get 69 處 · urlopen 64 處),不經同一支網路工具,
所以快取放在「子行程的 HTTP 呼叫」這一層:MDL022 開跑時設 env VIA_VDF_RUN_CACHE=<本輪快取夾>,
並把本輪產生的掛鉤夾(TEMP 下,內含 sitecustomize.py)排在 PYTHONPATH 最前面;之後這一輪所有 python 子行程
(擷取引擎、它們再開的子行程)一啟動就裝上本檔的 install()。
規則(只快取「重抓也一定一樣」的):
  · 只收 GET、沒有 body、不是 stream、回 200、內容 ≤ 上限(預設 64 MB);POST / 錯誤 / 超大一律不收、照常送。
  · 鍵 = sha256(最終網址 + 排序後的請求標頭,不含 User-Agent / Cookie);網址不寫進檔(金鑰可能在網址裡)。
  · 寫檔:暫存名 + os.replace 原子換檔;兩道同時抓同一個網址最多各送一次,不會讀到半個檔。
  · 快取只活這一輪:夾在本機 TEMP(不在 OneDrive、不離開這台電腦),MDL022 收尾時刪掉,只留計數收據。
  · 同意閘:本檔不設、不繞;命中的內容都是本輪閘開著時真的抓回來的。
  · 鏈接:PYTHONPATH 上本來就有的 sitecustomize 照樣執行(掛鉤裝完再找下一個 sitecustomize 執行)。
動詞:stats <夾>(只讀計數)· --selftest(本機 127.0.0.1 假伺服器,零外網)。
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

import hashlib
import io
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_MDL024_RunFetchCache"
VERSION = "v0100"
TAG = f"{STEM} {VERSION}"
ENV_DIR = "VIA_VDF_RUN_CACHE"
ENV_MAX = "VIA_VDF_RUN_CACHE_MAX_MB"
SKIP_HEADERS = {"user-agent", "cookie"}
STATS = "_stats.jsonl"
KEEP_HEADERS = ("content-type", "content-encoding", "last-modified", "date")
LOCK_WAIT_S = 120                                   # 別道正在抓同一個鍵:最多等這麼久
LOCK_STALE_S = 600                                  # 鎖檔比這舊 = 持鎖的行程已死,拆掉


def max_bytes() -> int:
    try:
        return int(float(os.environ.get(ENV_MAX, "64")) * 1024 * 1024)
    except ValueError:
        return 64 * 1024 * 1024


def cache_key(url: str, headers=None) -> str:
    items = sorted((str(k).lower(), str(v)) for k, v in (headers or {}).items() if str(k).lower() not in SKIP_HEADERS)
    return hashlib.sha256(json.dumps([url, items], ensure_ascii=False).encode("utf-8")).hexdigest()


def _host(url: str) -> str:
    try:
        from urllib.parse import urlsplit
        return urlsplit(url).hostname or "?"
    except Exception:
        return "?"


def _stat(root: Path, event: str, url: str, nbytes: int = 0) -> None:
    try:
        line = json.dumps({"e": event, "host": _host(url), "b": int(nbytes), "pid": os.getpid()}) + "\n"
        with open(root / STATS, "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        pass


def load(root: Path, key: str):
    body, meta = root / f"{key}.body", root / f"{key}.json"
    if not (body.is_file() and meta.is_file()):
        return None
    try:
        return body.read_bytes(), json.loads(meta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def store(root: Path, key: str, content: bytes, meta: dict) -> bool:
    if len(content) > max_bytes():
        return False
    tag = f".{os.getpid()}.{time.time_ns()}.sdd_tmp"
    try:
        for name, data in ((f"{key}.body", content), (f"{key}.json", json.dumps(meta).encode("utf-8"))):
            tmp = root / (name + tag)
            tmp.write_bytes(data)
            os.replace(tmp, root / name)
        return True
    except OSError:
        return False


def _acquire(root: Path, key: str):
    """同鍵跨行程鎖(O_CREAT | O_EXCL):拿到回鎖檔路徑;別道持有回 None。過舊的鎖視為死鎖拆掉再試一次。"""
    lk = root / f"{key}.lock"
    for _ in range(2):
        try:
            fd = os.open(str(lk), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return lk
        except FileExistsError:
            try:
                if time.time() - lk.stat().st_mtime <= LOCK_STALE_S:
                    return None
                lk.unlink()
            except OSError:
                return None
        except OSError:
            return None
    return None


def _wait(root: Path, key: str, limit: float = None):
    """等持鎖的那一道存好:有內容就回;鎖放掉了還沒內容(它抓失敗 / 不能收)→ None。"""
    end = time.time() + (LOCK_WAIT_S if limit is None else limit)
    lk = root / f"{key}.lock"
    while time.time() < end:
        hit = load(root, key)
        if hit or not lk.exists():
            return hit or load(root, key)
        time.sleep(0.05)
    return None


def fetch_once(root: Path, key: str, url: str, fetch, make_hit):
    """同一個鍵整輪只真的送一次:先查 → 拿鎖(拿不到就等別道存好)→ 拿到鎖後再查一次 → 送 → 存 → 放鎖。
    fetch() 回 (給呼叫端的物件, 可快取的內容 bytes 或 None, meta)。"""
    hit = load(root, key)
    if hit:
        _stat(root, "hit", url, len(hit[0]))
        return make_hit(*hit)
    lk = _acquire(root, key)
    if lk is None:
        hit = _wait(root, key)
        if hit:
            _stat(root, "hit", url, len(hit[0]))
            return make_hit(*hit)
        lk = _acquire(root, key)
    try:
        if lk is not None:
            hit = load(root, key)
            if hit:
                _stat(root, "hit", url, len(hit[0]))
                return make_hit(*hit)
        obj, body, meta = fetch()
        if body is not None:
            saved = store(root, key, body, meta)
            _stat(root, "miss_stored" if saved else "miss_big", url, len(body))
        return obj
    finally:
        if lk is not None:
            try:
                lk.unlink()
            except OSError:
                pass


def install(root=None) -> bool:
    """在本行程裝上快取(requests.Session.request · urllib.request.urlopen)。沒設 env 或夾不在 → 什麼都不做。"""
    raw = root or os.environ.get(ENV_DIR) or ""
    if not raw or not Path(raw).is_dir():
        return False
    root = Path(raw)
    _install_urllib(root)
    _install_requests(root)
    return True


def _install_urllib(root: Path) -> None:
    import email
    import http.client
    import urllib.request
    import urllib.response
    if getattr(urllib.request.urlopen, "_vdf_run_cache", False):
        return
    orig = urllib.request.urlopen

    def urlopen(url, data=None, *a, **kw):
        req = url if isinstance(url, urllib.request.Request) else None
        full = req.full_url if req else str(url)
        method = (req.get_method() if req else ("POST" if data is not None else "GET")).upper()
        if method != "GET" or data is not None or (req is not None and req.data is not None):
            return orig(url, data, *a, **kw)
        key = cache_key(full, dict(req.header_items()) if req else {})

        def make_hit(body, meta):
            msg = email.message_from_string("".join(f"{k}: {v}\n" for k, v in (meta.get("headers") or {}).items()),
                                            _class=http.client.HTTPMessage)
            return urllib.response.addinfourl(io.BytesIO(body), msg, meta.get("url") or full, 200)

        def fetch():
            resp = orig(url, data, *a, **kw)
            code = getattr(resp, "status", None) or resp.getcode()
            if code != 200:
                return resp, None, None
            body = resp.read()
            hdrs = {k: v for k, v in resp.headers.items() if k.lower() in KEEP_HEADERS}
            return (urllib.response.addinfourl(io.BytesIO(body), resp.headers, resp.geturl(), 200), body,
                    {"headers": hdrs, "url": resp.geturl()})

        return fetch_once(root, key, full, fetch, make_hit)

    urlopen._vdf_run_cache = True
    urllib.request.urlopen = urlopen


def _install_requests(root: Path) -> None:
    try:
        import requests
        from requests.structures import CaseInsensitiveDict
    except Exception:
        return
    S = requests.sessions.Session
    if getattr(S.request, "_vdf_run_cache", False):
        return
    orig = S.request

    def request(self, method, url, params=None, data=None, headers=None, cookies=None, files=None, auth=None,
                timeout=None, allow_redirects=True, proxies=None, hooks=None, stream=None, verify=None, cert=None, json=None):
        def call():
            return orig(self, method, url, params=params, data=data, headers=headers, cookies=cookies, files=files,
                        auth=auth, timeout=timeout, allow_redirects=allow_redirects, proxies=proxies, hooks=hooks,
                        stream=stream, verify=verify, cert=cert, json=json)
        if str(method).upper() != "GET" or data or json is not None or files or stream:
            return call()
        try:
            prep = requests.Request("GET", url, params=params).prepare()
            merged = dict(self.headers or {})
            merged.update(headers or {})
            key = cache_key(prep.url, merged)
        except Exception:
            return call()
        def make_hit(body, meta):
            r = requests.models.Response()
            r.status_code, r._content, r.url, r.reason = 200, body, meta.get("url") or prep.url, "OK"
            r.headers = CaseInsensitiveDict(meta.get("headers") or {})
            r.encoding = meta.get("encoding")
            r.request = prep
            return r

        def fetch():
            r = call()
            if r.status_code != 200:
                return r, None, None
            hdrs = {k: v for k, v in r.headers.items() if k.lower() in ("content-type", "last-modified", "date")}
            return r, r.content, {"headers": hdrs, "url": r.url, "encoding": r.encoding}

        return fetch_once(root, key, prep.url, fetch, make_hit)

    request._vdf_run_cache = True
    S.request = request


HOOK_SRC = """# generated by {tag} for one run; deleted when the run ends
import importlib.util as _u, os as _o, sys as _s
try:
    _sp = _u.spec_from_file_location("VDF_RunFetchCache_hook", {mod!r})
    _m = _u.module_from_spec(_sp)
    _sp.loader.exec_module(_m)
    _m.install()
except Exception:
    pass
_me = _o.path.dirname(_o.path.abspath(__file__))
for _d in list(_s.path):
    _f = _o.path.join(_d or ".", "sitecustomize.py")
    if _d and _o.path.abspath(_d) != _me and _o.path.isfile(_f):
        try:
            _sp2 = _u.spec_from_file_location("sitecustomize_chained", _f)
            _sp2.loader.exec_module(_u.module_from_spec(_sp2))
        except Exception:
            pass
        break
"""


def prepare(base=None) -> tuple:
    """建本輪快取夾與掛鉤夾 → (快取夾, 掛鉤夾)。都在本機 TEMP。"""
    base = Path(base or tempfile.gettempdir()) / "via_vdf_run_cache"
    base.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix=time.strftime("%Y%m%d_%H%M%S_"), dir=base))
    hook = root / "_hook"
    hook.mkdir()
    (hook / "sitecustomize.py").write_text(HOOK_SRC.format(tag=TAG, mod=str(Path(__file__).resolve())), encoding="utf-8")
    return root, hook


def child_env(root: Path, hook: Path, env=None) -> dict:
    env = dict(os.environ if env is None else env)
    env[ENV_DIR] = str(root)
    env["PYTHONPATH"] = str(hook) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


def stats(root) -> dict:
    out = {"hit": 0, "miss_stored": 0, "miss_big": 0, "bytes_saved": 0, "by_host": {}}
    p = Path(root) / STATS
    if p.is_file():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            ev = e.get("e")
            if ev in out:
                out[ev] += 1
            h = out["by_host"].setdefault(e.get("host") or "?", {"hit": 0, "sent": 0})
            if ev == "hit":
                out["bytes_saved"] += int(e.get("b") or 0)
                h["hit"] += 1
            else:
                h["sent"] += 1
    out["requests"] = out["hit"] + out["miss_stored"] + out["miss_big"]
    out["hit_pct"] = round(100.0 * out["hit"] / out["requests"], 1) if out["requests"] else 0.0
    return out


def cleanup(root) -> None:
    import shutil
    shutil.rmtree(root, ignore_errors=True)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if args[:1] == ["stats"] and len(args) > 1:
        print(json.dumps(stats(Path(args[1])), ensure_ascii=False, indent=1))
        return 0
    print(f"{TAG} · 動詞:stats <夾> · --selftest(由 VDF_MDL022 v0112 每輪自動接上,不需手動)")
    return 0


def selftest() -> int:
    import http.server
    import subprocess
    import threading
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, VIA_NET_TOOL_PATH)
    served = {"n": 0}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            served["n"] += 1
            served[self.path] = served.get(self.path, 0) + 1
            if self.path.startswith("/slow"):
                time.sleep(0.6)
            code = 404 if self.path.startswith("/missing") else 200
            body = json.dumps({"path": self.path, "n": served["n"]}).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            self.do_GET()

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        import requests  # noqa: F401
        have_req = True
    except ImportError:
        have_req = False
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        other = td / "other_site"
        other.mkdir()
        (other / "sitecustomize.py").write_text("import os\nos.environ['VDF_CHAIN_SEEN'] = '1'\n", encoding="utf-8")
        root, hook = prepare(td)
        env = child_env(root, hook, dict(os.environ, PYTHONPATH=str(other)))
        for k in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
            env.pop(k, None)
        env["NO_PROXY"] = env["no_proxy"] = "127.0.0.1,localhost"
        child = (
            "import json,os,sys,urllib.request\n"
            "u=sys.argv[1]\n"
            "a=json.loads(urllib.request.urlopen(u+'/q?x=1',timeout=5).read())\n"
            "try:\n import requests\n b=requests.get(u+'/r',params={'y':2},timeout=5).json()\nexcept ImportError:\n b={'n':-1}\n"
            "try:\n urllib.request.urlopen(u+'/missing',timeout=5)\nexcept Exception:\n pass\n"
            "c=json.loads(urllib.request.urlopen(urllib.request.Request(u+'/p',data=b'z'),timeout=5).read())\n"
            "print(json.dumps({'a':a['n'],'b':b['n'],'c':c['n'],'chain':os.environ.get('VDF_CHAIN_SEEN')}))\n")
        outs = []
        for _ in range(2):
            p = subprocess.run([sys.executable, "-c", child, base], env=env, capture_output=True, text=True, timeout=60)
            outs.append(json.loads((p.stdout.strip().splitlines() or ["{}"])[-1]) if p.returncode == 0 else {"err": p.stderr[-400:]})
        st = stats(root)
        first, second = outs
        chk("① 兩個獨立子行程打同一個 GET:第二個直接讀快取(伺服器值與第一次相同)",
            "err" not in first and "err" not in second and second.get("a") == first.get("a"), outs)
        chk("② requests.get(含 params)同樣命中" + ("" if have_req else "(本境沒裝 requests:略過)"),
            (second.get("b") == first.get("b")) if have_req else True, outs)
        chk("③ POST 不快取:兩次都真的送(值不同)", second.get("c") != first.get("c"), outs)
        chk("④ 404 不收進快取 · 計數:命中 ≥ 1 · 真送的有記 · 沒有殘留暫存檔",
            st["hit"] >= 1 and st["miss_stored"] >= 1 and not any(Path(root).glob("*.sdd_tmp"))
            and len(list(Path(root).glob("*.body"))) == (2 if have_req else 1), st)
        chk("⑤ 原本的 sitecustomize 照樣執行(鏈接)", first.get("chain") == "1" and second.get("chain") == "1", outs)
        chk("⑥ 檔名只有雜湊(網址不落檔)· 鍵不含 User-Agent / Cookie",
            all(len(f.stem) == 64 for f in Path(root).glob("*.body"))
            and cache_key("u", {"User-Agent": "a", "Cookie": "x"}) == cache_key("u", {"User-Agent": "b"}))
        racer = ("import sys,urllib.request\n"
                 "u=sys.argv[1]\n"
                 "try:\n import requests\n requests.get(u+'/slow-r',timeout=30).content\nexcept ImportError:\n pass\n"
                 "urllib.request.urlopen(u+'/slow-u',timeout=30).read()\n")
        procs = [subprocess.Popen([sys.executable, "-c", racer, base], env=env, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.PIPE, text=True) for _ in range(4)]
        errs = [p.communicate(timeout=120)[1] for p in procs]
        rcs = [p.returncode for p in procs]
        chk("⑨ 4 道同時抓同一個還沒快取的 GET(伺服器慢 0.6 秒):伺服器各只收到 1 次 · 其他道等鎖後讀快取 · 鎖檔不留",
            rcs == [0, 0, 0, 0] and served.get("/slow-u") == 1 and served.get("/slow-r", 1 if not have_req else 0) == 1
            and not any(Path(root).glob("*.lock")), (rcs, {k: v for k, v in served.items() if k.startswith("/slow")}, errs[-1][-300:]))
        lk = _acquire(Path(root), "k" * 64)
        os.utime(lk, (time.time() - LOCK_STALE_S - 5,) * 2)
        lk2 = _acquire(Path(root), "k" * 64)
        held = _acquire(Path(root), "k" * 64)
        chk("⑩ 過舊的鎖(持鎖行程已死)會被拆掉重拿;新鮮的鎖拿不到", lk2 is not None and held is None, (lk2, held))
        lk2.unlink()
        env2 = dict(env)
        env2.pop(ENV_DIR)
        p = subprocess.run([sys.executable, "-c", "import urllib.request;print(getattr(urllib.request.urlopen,'_vdf_run_cache',False))"],
                           env=env2, capture_output=True, text=True, timeout=60)
        chk("⑦ 沒設 env → 掛鉤什麼都不裝(照常連線)", p.stdout.strip() == "False", p.stdout + p.stderr[-200:])
        cleanup(root)
        chk("⑧ 收尾刪除本輪快取夾", not Path(root).exists())
    srv.shutdown()
    src = Path(__file__).read_text(encoding="utf-8")
    chk("檔面:第 3 行加速器標記 · 雙橋在 · 不設同意閘 · 不含本機路徑",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M)
        and "C:\\Users\\" + "tonyk" not in src)
    print(f"[selftest] {TAG} {len(ok)}/{len(ok) + len(bad)} " + ("PASS" if not bad else "FAIL · " + " · ".join(bad)), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
