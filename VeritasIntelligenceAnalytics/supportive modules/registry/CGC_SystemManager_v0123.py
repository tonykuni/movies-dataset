#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_SystemManager v0123 — 薄尾(v0122 以前一字不動):launch 的總燈與三數照實(PR #773 Codex P1 · P2)

v0122 的 launch 有兩個漏洞:
  P1 加速器沒載到(VIA_ACCEL is None)時,子行程全綠就給 GREEN / rc 0;啟動行寫「沒載到(黃)」,收據卻是成功。
     → 本版:加速器沒載到,總燈最好只到 YELLOW(rc 2),NEXT 指回本檔自測。只有標記、載不到 = 假加速 = 黃(REQ266)。
  P2 找不到尾版的步記灰 rc 3,沒算進 ran,也沒進 skipped → 應 8 · 已 7 · 略過 0,三數對不上。
     → 本版:rc 3 的步列進 skipped;任何時候 應 = 已 + 略過。
為什麼不就地改 v0122:Start-VCGC-v0101.ps1(倉內與操作員下載夾兩份)都釘 v0122 的雜湊,改了 PS 會擋;
PS 叫的是家族尾版,所以出 v0123 兩份 PS 都不用動。
其餘動詞(toolbox · schedule · omniroute …)照 v0122 → v0121 原樣轉交。只動 VCGC 自己的檔與 VIA_Reports/vcgc。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
try:
    import os as _sa_os
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_hit = None
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.append(_sa_Path(_sa_os.environ["VIA_REPO"]).resolve())
    for _sa_r in _sa_roots:
        for _sa_q in (_sa_r, *_sa_r.parents):
            for _sa_c in (_sa_q / "supportive modules", _sa_q / "VeritasIntelligenceAnalytics" / "supportive modules"):
                if (_sa_c / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit:
                break
        if _sa_hit:
            break
    if _sa_hit and str(_sa_hit) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_hit))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席時照樣載得起來,但 launch 總燈最好只到黃
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_SystemManager"
VERSION = "v0123"
TAG = f"{_STEM} {VERSION}"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


_BELOW = [p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)]
if not _BELOW:   # 放錯倉:照實停,不丟例外(同 v0122)
    print(f"[RED] {HERE} 沒有 {_STEM} 前版;這份不是主工作倉。", flush=True)
    raise SystemExit(3)
PRIOR_PATH = max(_BELOW, key=_vnum)
_spec = importlib.util.spec_from_file_location(f"cgc_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

VIA = PRIOR.VIA
OUT = PRIOR.OUT
RANK = PRIOR.RANK
_PLAIN = PRIOR._PLAIN   # 同一個清單:--plain 一設,前版 say 也不上色


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def say(msg: str, lamp: str | None = None) -> None:
    line = f"[{TAG}] {msg}"
    if lamp and not _PLAIN[0]:
        line = PRIOR._COLOR.get(lamp, "") + line + PRIOR._COLOR["END"]
    print(line, flush=True)


def tally(p: dict, allr: list) -> dict:
    """三數:應 = 計畫的步數;已 = 真的起了子行程的步(rc ≠ 3);略過 = 其餘(沒跑到的 + 找不到尾版的)。應 = 已 + 略過。"""
    planned = [p["gate"], *p["lanes"], p["post"]]
    ran = {r["name"] for r in allr if r["rc"] != 3}
    return {"should": len(planned), "ran": len(ran), "skipped": [s["name"] for s in planned if s["name"] not in ran]}


def overall(allr: list, accel_ok: bool) -> str:
    """總燈:最壞的步(灰算黃);加速器沒載到時最好只到黃。"""
    worst = max((r["lamp"] for r in allr), key=lambda x: RANK[x])
    lamp = {"RED": "RED", "GREEN": "GREEN"}.get(worst, "YELLOW")
    return "YELLOW" if (lamp == "GREEN" and not accel_ok) else lamp


def launch(argv: list, via: Path = VIA, reg: Path = HERE, self_file: Path | None = None, py: str | None = None,
           out: Path = OUT, opener=webbrowser.open, log=None, every: int | None = None, accel_ok: bool | None = None) -> int:
    log = log or say
    accel_ok = (VIA_ACCEL is not None) if accel_ok is None else bool(accel_ok)
    a = list(argv)
    if "--plain" in a:
        _PLAIN[0] = True
    full = "--full" in a
    req = int(a[a.index("--lanes") + 1]) if "--lanes" in a and a.index("--lanes") + 1 < len(a) else None
    cap = int(a[a.index("--timeout") + 1]) if "--timeout" in a and a.index("--timeout") + 1 < len(a) else 3600
    every = every or max(5, min(30, int(os.environ.get("VIA_HEARTBEAT_SEC", "20") or 20)))
    host = "主機" if os.name == "nt" else "容器"
    p = PRIOR.plan(via, reg, full, self_file or Path(__file__).resolve(), cap)
    lanes, why = PRIOR.lane_count(req)
    py = py or PRIOR.core_python()
    log(f"VCGC 啟用 · {host} · 道數 {lanes}({why})· 加速器 {'載到' if accel_ok else '沒載到(總燈最好只到黃)'} · python {py}")
    if "--plan" in a:
        for s in [p["gate"], *p["lanes"], p["post"]]:
            log(f"  [計畫] {s['name']:<8} {Path(s['file']).name if s['file'] else '找不到(灰 · 記略過)'} {' '.join(s['argv'])} · {s['why']}")
        log("NEXT: 拿掉 --plan 就照這張跑")
        return 0
    t0 = time.time()
    logdir = Path(tempfile.mkdtemp(prefix="VIA_launch_"))
    repo = via.parent
    gate = PRIOR.run_steps([p["gate"]], 1, py, repo, logdir, every, log)[0]
    results, post = [], None
    if gate["lamp"] == "RED" or gate["rc"] not in (0, 2):
        log("第一步 token 不綠:VCGC 停在這裡(CLAUDE.md:token 紅不讀政策、不開子系統)", "RED")
    else:
        results = PRIOR.run_steps(p["lanes"], lanes, py, repo, logdir, every, log)
        post = PRIOR.run_steps([p["post"]], 1, py, repo, logdir, every, log)[0]
    allr = [gate, *results] + ([post] if post else [])
    lamp = overall(allr, accel_ok)
    page = via / "VIA_Reports" / "vcgc" / "VCGC_Overview_latest.html"
    res = {"system": "VCGC", "verb": "launch", "version": VERSION, "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "host": host, "lanes_used": lanes, "lanes_why": why, "accel_loaded": accel_ok, "secs": round(time.time() - t0, 1),
           "counts": tally(p, allr), "gate_result": gate, "results": results, "post_result": post, "lamp": lamp,
           "page": str(page) if page.is_file() and post and post["rc"] == 0 else None, "logs": str(logdir),
           "note": "launch 只啟用與彙總;收尾燈只看 handoff 的 closeout_lamp(主機實跑 + 輸出驗證 + U/I)"}
    res["rc"] = {"GREEN": 0, "RED": 1}.get(lamp, 2)
    res["next"] = PRIOR._next(res)
    if not accel_ok and res["next"].startswith("via-vcgc handoff daily"):
        res["next"] = f"python \"{Path(__file__).name}\" --selftest(加速器沒載到:看第一檢;只有標記、載不到 = 假加速)"
    pack = PRIOR.pastepack(res)
    if not accel_ok:
        pack.insert(1, "  [YELLOW] accel    加速器沒載到(VIA_ACCEL is None):總燈最好只到黃")
    out.mkdir(parents=True, exist_ok=True)
    (out / "LAUNCH_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "LAUNCH_latest.txt").write_text("\n".join(pack) + "\n", encoding="utf-8")
    PRIOR.append_line(out / "LAUNCH_LEDGER.jsonl", json.dumps({k: res[k] for k in ("utc", "host", "lamp", "rc", "secs", "lanes_used", "counts", "accel_loaded")}, ensure_ascii=False))
    print("", flush=True)
    for ln in pack:
        lp = "RED" if "[RED" in ln else ("YELLOW" if ("[YELLOW" in ln or ln.startswith("NEXT:") or ln.startswith("[VCGC launch]")) else None)
        if lp:
            say(ln, lp)
        else:
            print(f"[{TAG}] {ln}", flush=True)
    log(f"收據 {out / 'LAUNCH_latest.json'} · 貼回包 {out / 'LAUNCH_latest.txt'}(黃字整段貼回 AI)")
    if res["page"] and "--no-open" not in a and os.environ.get("VIA_NO_OPEN") != "1":
        try:
            opened = opener(Path(res["page"]).as_uri())
        except Exception:  # noqa: BLE001
            opened = False
        log(f"U/I {res['page']}" + ("(已開)" if opened else "(這台開不了瀏覽器,請手動開)"))
    return res["rc"]


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] == ["launch"]:
        return launch(a[1:])
    return PRIOR.main()


_FAKE = ("import os, sys, pathlib\n"
         "a = sys.argv[1:]\n"
         "assert os.environ.get('VIA_FROM_VCGC') == 'YES'\n"
         "if a[:1] == ['token']: print('[第一步] x'); sys.exit(int(os.environ.get('FAKE_TOKEN_RC', '0')))\n"
         "if a[:1] == ['overview']:\n"
         "    p = pathlib.Path(__file__).resolve().parents[2] / 'VIA_Reports' / 'vcgc'; p.mkdir(parents=True, exist_ok=True)\n"
         "    (p / 'VCGC_Overview_latest.html').write_text('<html></html>'); print('[U/I] ok'); sys.exit(0)\n"
         "print('[假步] GREEN · fake'); sys.exit(0)\n")


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    chk("① 加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    below = [p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)]
    chk("② 前版經 glob 載入(本檔之下最大的一版)", PRIOR_PATH == max(below, key=_vnum), PRIOR_PATH.name)
    me_mod = sys.modules[__name__]
    chk("③ TAILAPI:前版公開名稱經本檔轉接(plan · run_steps · pastepack · cmd_schedule · core_python)",
        all(callable(getattr(me_mod, n, None)) for n in ("plan", "run_steps", "pastepack", "cmd_schedule", "core_python")))
    saved_no_open = os.environ.pop("VIA_NO_OPEN", None)   # 自測不吃本機狀態(LL-20261128-02)
    PRIOR.lane_count(None)   # 先讓加速器設好它自己的執行緒變數(加速器生效的正常行為),再取快照,只驗本版自己有沒有外溢
    env_before = dict(os.environ)
    try:
        with tempfile.TemporaryDirectory() as td:
            via = Path(td) / "repo" / "VeritasIntelligenceAnalytics"
            reg = via / "supportive modules" / "registry"
            ai = via / "docs" / "handoff" / "ai"
            reg.mkdir(parents=True)
            ai.mkdir(parents=True)
            for f in (reg / "CGC_MDL149_VeritasCentralGovernanceConsole_v0100.py", reg / "CGC_MDL158_Fake_v0100.py", ai / "VIA_ReworkGuard_v0100.py"):
                f.write_text(_FAKE, encoding="utf-8")
            (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps(
                {"token": {"path": "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL158_Fake_v0100.py"}}), encoding="utf-8")
            me = reg / "CGC_FakeManager_v0100.py"   # 假管理器夾具(不用本家族名,免被當成釘死前版)
            me.write_text(_FAKE, encoding="utf-8")
            out = via / "VIA_Reports" / "vcgc" / "launch"
            lines, opened = [], []
            log = lambda m, lamp=None: lines.append(m)  # noqa: E731

            def run(argv, accel):
                rc = launch(argv, via, reg, me, sys.executable, out, opened.append, log, 1, accel)
                return rc, json.loads((out / "LAUNCH_latest.json").read_text(encoding="utf-8"))

            def three(r):
                c = r["counts"]
                return c["should"] == c["ran"] + len(c["skipped"])

            rc_plan = launch(["--plan"], via, reg, me, sys.executable, out, opened.append, log, 1, True)
            chk("④ --plan:rc 0 · 不起子行程 · 不寫檔", rc_plan == 0 and not out.exists())
            rc, r = run(["--timeout", "30"], True)
            chk("⑤ 全綠 + 加速器在 → GREEN · rc 0 · accel_loaded True · 應 8 已 8 略過 0",
                rc == 0 and r["lamp"] == "GREEN" and r["accel_loaded"] is True and r["counts"] == {"should": 8, "ran": 8, "skipped": []}, str(r["counts"]))
            rc, r = run(["--timeout", "30"], False)
            pk = (out / "LAUNCH_latest.txt").read_text(encoding="utf-8").splitlines()
            chk("⑥ P1 反控:全綠但加速器沒載到 → YELLOW · rc 2 · accel_loaded False · 貼回包點名 · NEXT 指自測",
                rc == 2 and r["lamp"] == "YELLOW" and r["accel_loaded"] is False and any("加速器沒載到" in x for x in pk)
                and "--selftest" in r["next"], f"{r['lamp']} · {r['next'][:60]}")
            (ai / "VIA_ReworkGuard_v0100.py").unlink()
            rc, r = run(["--timeout", "30"], True)
            chk("⑦ P2 反控:重工守門不在 → 那步記灰 · 略過 [rework] · 應 8 = 已 7 + 略過 1 · 總燈黃",
                r["counts"] == {"should": 8, "ran": 7, "skipped": ["rework"]} and three(r) and r["lamp"] == "YELLOW" and rc == 2, str(r["counts"]))
            hdr = (out / "LAUNCH_latest.txt").read_text(encoding="utf-8").splitlines()[0]
            chk("⑧ 貼回包首行帶略過的步名", "略過 1(rework)" in hdr, hdr[:90])
            os.environ["FAKE_TOKEN_RC"] = "1"
            rc, r = run(["--timeout", "30"], True)
            os.environ.pop("FAKE_TOKEN_RC", None)
            chk("⑨ 閘紅 → 停 · rc 1 · 應 8 = 已 1 + 略過 7", rc == 1 and r["counts"]["ran"] == 1 and len(r["counts"]["skipped"]) == 7 and three(r), str(r["counts"]))
            chk("⑩ 帳只增:LAUNCH_LEDGER 四列 · 每列帶 accel_loaded",
                [("accel_loaded" in json.loads(x)) for x in (out / "LAUNCH_LEDGER.jsonl").read_text(encoding="utf-8").splitlines()] == [True] * 4)
    finally:
        os.environ.pop("FAKE_TOKEN_RC", None)
        if saved_no_open is not None:
            os.environ["VIA_NO_OPEN"] = saved_no_open
    chk("⑪ 環境變數沒外溢", {k: v for k, v in os.environ.items() if k != "VIA_NO_OPEN"} == {k: v for k, v in env_before.items() if k != "VIA_NO_OPEN"})
    env = dict(os.environ, VIA_FROM_VCGC="YES", PYTHONUTF8="1")
    env.pop("VIA_NO_OPEN", None)
    pl = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "launch", "--plan", "--plain"], capture_output=True,
                        text=True, encoding="utf-8", errors="replace", env=env, timeout=300)
    chk("⑫ 入口:launch 走本版(真倉 --plan · rc 0 · 本版標籤 · 不寫檔)", pl.returncode == 0 and f"[{TAG}]" in pl.stdout, (pl.stdout.strip().splitlines() or ["?"])[-1][:80])
    pr = subprocess.run([sys.executable, "-X", "utf8", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8",
                        errors="replace", env=env, timeout=900)
    last = (pr.stdout.strip().splitlines() or ["?"])[-1]
    chk("⑬ 直接前版自測(乾淨子行程)rc 0", pr.returncode == 0, last[:80])
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
