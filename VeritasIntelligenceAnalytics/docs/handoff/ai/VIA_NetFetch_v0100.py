#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_NetFetch v0100 — 資料檔下載一律走網路工具(SUP_MDL740_NetUnified 尾版 → AegisNexus;雙閘 · 重試 · 退避)。

操作員 2026-11-10:「抓資料檔案及 VCF 檔案都要導入網路工具 · 不卡段 · 動態進度條」。
  · 下載只經 NetUnified.http_bytes(url, timeout, retries, backoff);不自己開 urllib / requests。
  · 雙閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)由網路工具判;閘關 = DENIED 照實回,本支永不代設。
  · 每個檔:@@PROGRESS 進度行 · 寫到 --out 夾 · SHA-256 · 可帶 --sha 核對(不符 = RED、檔案改名 .bad 保留)。
  · 收據寫 --out/netfetch_receipt.json。不執行下載的內容。
用法:python VIA_NetFetch_v0100.py --url <URL> [--url …] --out <夾> [--sha <hex> …] [--timeout 60] [--retries 3] · --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import argparse
import datetime as _dt
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse

VERSION = "v0100"
ENGINE = f"VIA_NetFetch_{VERSION}"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
NET_DIR = VIA / "supportive modules" / "network"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


def load_net(net_dir: Path = NET_DIR):
    """網路工具尾版(SUP_MDL740_NetUnified_v*)。缺 = None(照實回,不退回自己開連線)。"""
    tails = sorted(net_dir.glob("SUP_MDL740_NetUnified_v*.py"), key=_vnum)
    if not tails:
        return None
    spec = importlib.util.spec_from_file_location("via_netunified_tail_for_netfetch", tails[-1])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def safe_name(url: str, i: int) -> str:
    n = Path(unquote(urlparse(url).path)).name or f"download_{i}"
    n = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", n)[:180]
    return n or f"download_{i}"


def fetch_all(urls: list, out: Path, shas: list | None = None, timeout: int = 60, retries: int = 3, net=None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    net = net if net is not None else load_net()
    items = []
    if net is None or not callable(getattr(net, "http_bytes", None)):
        return {"engine": ENGINE, "lamp": "RED", "reason": "網路工具 SUP_MDL740_NetUnified 尾版不在或沒有 http_bytes(不自己開連線)", "items": items}
    n = max(1, len(urls))
    for i, url in enumerate(urls):
        print(f"@@PROGRESS|{100.0 * i / n:.1f}|下載 {i + 1}/{n} · {url[:120]}", flush=True)
        rec = {"url": url}
        try:
            r = net.http_bytes(url, timeout=timeout, retries=retries, backoff=1.0)
        except Exception as exc:  # noqa: BLE001 — 單檔失敗記紅,不連累其他檔
            r = {"state": "ERROR", "error": f"{type(exc).__name__}: {exc}"[:300]}
        rec["state"] = r.get("state")
        rec["via"] = r.get("via")
        if r.get("state") == "OK" and r.get("data") is not None:
            data = bytes(r["data"])
            fn = out / safe_name(url, i)
            sha = hashlib.sha256(data).hexdigest()
            want = (shas[i].lower() if shas and i < len(shas) and shas[i] else None)
            if want and want != sha:
                fn = fn.with_name(fn.name + ".bad")
                rec["lamp"] = "RED"
                rec["why"] = f"SHA 不符:要 {want[:12]}… 得 {sha[:12]}…(保留成 .bad)"
            else:
                rec["lamp"] = "GREEN"
            fn.write_bytes(data)
            rec.update(file=str(fn), bytes=len(data), sha256=sha)
        else:
            rec["lamp"] = "YELLOW" if str(r.get("state", "")).upper() in ("DENY", "DENIED", "CLOSED", "GATE_CLOSED") else "RED"
            rec["why"] = str(r.get("error") or r.get("reason") or r.get("why") or r.get("state"))[:300]
            if rec["lamp"] == "YELLOW":
                rec["why"] += " · 網路同意閘關著(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 由操作員設,本支不代設)"
        items.append(rec)
    print(f"@@PROGRESS|100.0|下載完成 {len(items)} 個", flush=True)
    lamps = {i["lamp"] for i in items}
    lamp = "RED" if "RED" in lamps else ("YELLOW" if "YELLOW" in lamps or not items else "GREEN")
    res = {"engine": ENGINE, "lamp": lamp, "at_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "items": items,
           "boundary": "只經網路工具 · 雙閘由網路工具判、本支不代設 · 不執行下載內容"}
    (out / "netfetch_receipt.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    class FakeNet:
        def __init__(self):
            self.calls = []

        def http_bytes(self, url, timeout=30, retries=3, backoff=1.0):
            self.calls.append((url, timeout, retries))
            if "deny" in url:
                return {"state": "DENIED", "reason": "VIA_NET_CONSENT 未開"}
            if "boom" in url:
                raise OSError("reset")
            return {"state": "OK", "data": b"hello", "via": "fake"}
    with tempfile.TemporaryDirectory(prefix="via_netfetch_") as td:
        out = Path(td)
        fn = FakeNet()
        good = hashlib.sha256(b"hello").hexdigest()
        r = fetch_all(["https://x/a/data.csv", "https://x/deny.csv", "https://x/boom.csv", "https://x/b.csv"], out,
                      shas=[good, None, None, "00" * 32], timeout=7, retries=2, net=fn)
        lam = [i["lamp"] for i in r["items"]]
        chk("① 全部經網路工具 http_bytes(timeout · retries 照傳)", len(fn.calls) == 4 and fn.calls[0][1:] == (7, 2))
        chk("② SHA 對 = GREEN · 閘關 = YELLOW · 例外 = RED 不炸 · SHA 不符 = RED 存 .bad", lam == ["GREEN", "YELLOW", "RED", "RED"] and (out / "b.csv.bad").is_file(), lam)
        chk("③ 總燈 RED · 收據寫出", r["lamp"] == "RED" and (out / "netfetch_receipt.json").is_file())
        r2 = fetch_all(["https://x/a"], out, net=object())
        chk("④ 網路工具缺 http_bytes = RED 照實說、不自己開連線", r2["lamp"] == "RED" and "不自己開連線" in r2["reason"])
    tails = sorted(NET_DIR.glob("SUP_MDL740_NetUnified_v*.py"), key=_vnum)
    chk("⑤ 倉內網路工具尾版在(真的那支)", bool(tails), tails[-1].name if tails else "缺")
    import ast
    text = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(text)
    mods = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    calls = {n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "") for n in ast.walk(tree) if isinstance(n, ast.Call)}
    chk("⑥ 加速器橋在 · 沒有自己的連線(AST:不匯入 urllib.request / requests / http.client · 不呼叫 urlopen)",
        "[VIA:ACCEL-BRIDGE" in text and not {"urllib.request", "requests", "http.client", "httpx"} & mods and "urlopen" not in calls)
    good_all = all(ok)
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if good_all else 'FAIL'}")
    return 0 if good_all else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--url", action="append", default=[])
    ap.add_argument("--sha", action="append", default=[])
    ap.add_argument("--out", default="")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.url or not a.out:
        ap.error("--url 與 --out 必填")
    r = fetch_all(a.url, Path(a.out), a.sha, a.timeout, a.retries)
    print(json.dumps({k: r.get(k) for k in ("lamp", "engine", "reason")}, ensure_ascii=False))
    for i in r["items"]:
        print(f"  [{i['lamp']}] {i['url']} · {i.get('file') or i.get('why')}")
    return 0 if r["lamp"] == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main())
