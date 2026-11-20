#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_VCGC_ApplyRun v0105 — 薄尾:`go` 一個動詞做完全部(PS 只剩一行呼叫)· 心跳帶該步最後一行 · --data-home 驗了才用
操作員 2026-11-20:「速度太慢 · 任何啟動指令都用 PY 寫 · PS 只是簡單啟動指令」,並給 VDF 資料家目錄。
桌機實錄:A-VRN-activate 心跳只印「還在跑 N 秒」,跑到 6227 秒看不出卡在哪一步,只好 Ctrl+C(結束碼 3221225786 = 0xC000013A)。
本版只加三件事(v0104 一字不動,其餘全部照前版):
  ① `go`:同步(v0100 的 sync:在 main 且乾淨才快轉)→ A 道(啟用 VDF / VRN-2,各走自己的入口)→ G,K 道(驗證)
     → 兩份貼回包合成 APPLY_GO_latest.txt 並放進剪貼簿(Windows);A 與 K 照 v0104 分兩次叫,K 才讀得到新產出。
     `--no-activate` 只跑 G,K(只驗不啟用,快)。
  ② `--data-home <夾>`:夾要真的存在才設進本行程的 VIA_DATA_HOME(子行程繼承;不寫任何檔);
     不存在 / 不是資料夾 → 當場拒絕、零寫入(不建 run 夾、不跑任何步)。
  ③ 心跳:每 30 秒那一行後面加上「該步輸出的最後一行」(去色碼、截 120 字),看得出卡在哪。
  兩輪都不各自出頁;最後把 A 與 G,K 的收據合成一份(總燈取最差)再出一張頁(PR #696 Codex P2:不讓第二輪把 A 的紅蓋成綠)。
同意閘照 v0104:本檔不設、不寫;要連網擷取由操作員在啟動那一行、只在那個行程裡設。
用法:python VIA_VCGC_ApplyRun_v0105.py go [--no-activate] [--data-home <夾>] [--lanes N] [--no-open] · --selftest
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

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_VCGC_ApplyRun"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0105", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE
VERSION = "v0105"
TAG = "VIA_VCGC_ApplyRun " + VERSION
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def __getattr__(name):
    return getattr(PRIOR, name)


def last_line(path: Path, limit: int = 120) -> str:
    """一個輸出檔最後一行非空的字(去色碼;讀不到回空字串)。只讀檔尾 8 KB,大檔也不慢。"""
    try:
        with Path(path).open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - 8192))
            chunk = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return ""
    for ln in reversed(chunk.splitlines()):
        s = ANSI.sub("", ln).strip()
        if s:
            return s[:limit]
    return ""


def run_step(st, via, logdir, beat):
    """前版 run_step 原樣;只把心跳換成「還在跑 N 秒 · 最後一行:…」。"""
    out = Path(logdir) / ("%s_%s.out" % (st.gid, st.name))

    def beat2(msg):
        if "還在跑" in str(msg):
            tail_ = last_line(out)
            if tail_:
                msg = "%s · 最後一行:%s" % (msg, tail_)
        beat(msg)
    return _PREV_RUN_STEP(st, via, logdir, beat2)


_PREV_RUN_STEP = BASE.run_step
BASE.run_step = run_step


def check_data_home(value):
    """(ok, 訊息)。沒給 = ok(照各系統自己的設定);給了就要是存在的資料夾。"""
    if value is None:
        return True, "沒給 --data-home,照各系統自己的設定"
    p = Path(value).expanduser()
    if not p.exists():
        return False, "資料家目錄不存在:%s(零寫入,沒有跑任何步)" % p
    if not p.is_dir():
        return False, "資料家目錄不是資料夾:%s(零寫入,沒有跑任何步)" % p
    return True, str(p.resolve())


def to_clipboard(text: str) -> str:
    """Windows 才放剪貼簿(PowerShell Set-Clipboard 讀暫存檔,中文不亂碼);其他系統照實回「沒放」。"""
    if os.name != "nt":
        return "非 Windows,沒放剪貼簿"
    ps = shutil.which("pwsh") or shutil.which("powershell")
    if not ps:
        return "找不到 PowerShell,沒放剪貼簿"
    import tempfile
    fd, tmp = tempfile.mkstemp(prefix="via_go_", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        cmd = "Set-Clipboard -Value (Get-Content -Raw -Encoding UTF8 -LiteralPath '%s')" % tmp.replace("'", "''")
        rc = subprocess.run([ps, "-NoProfile", "-Command", cmd], capture_output=True, timeout=60).returncode
        return "已放進剪貼簿" if rc == 0 else "放剪貼簿失敗(結束碼 %s)" % rc
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def _read_res(outdir: Path):
    try:
        return json.loads((outdir / "APPLY_latest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def merge_results(a: dict, b: dict) -> dict:
    """A 道與 G,K 道兩輪收據合成一份:步驟全列、總燈取最差、同步行用 A 那一輪量的(G,K 那輪沒再量)。"""
    steps = list(a.get("steps") or []) + list(b.get("steps") or [])
    sync = a.get("sync") or b.get("sync") or {"lamp": "灰", "line": "沒有量"}
    lamps = [s.get("lamp") for s in steps] + ([b["omniroute"][0]] if b.get("omniroute") else [])
    lamp = "紅" if any(x in ("紅", "逾時") for x in lamps) else "黃" if ("黃" in lamps or sync.get("lamp") == "黃") else "綠"
    bad = [s for s in steps if s.get("lamp") in ("紅", "逾時")]
    nxt = ("先看紅的 %d 步:%s" % (len(bad), " · ".join(s.get("name", "?") for s in bad[:5]))) if bad else (
        "看黃的步" if lamp == "黃" else "全綠;照實是容器或桌機哪一台跑的要寫明")
    res = dict(b)
    res.update(tool=TAG, lamp=lamp, only=list(a.get("only") or []) + list(b.get("only") or []), sync=sync,
               notes=list(a.get("notes") or []) + list(b.get("notes") or []), steps=steps, next=nxt,
               lanes_why="A 道 %s · G,K 道 %s" % (a.get("lanes_why", "—"), b.get("lanes_why", "—")),
               logdir="%s ; %s" % (a.get("logdir", "—"), b.get("logdir", "—")))
    return res


def go_core(via: Path, activate: bool, data_home, want, open_page: bool, runner=None, outdir: Path | None = None) -> int:
    ok, msg = check_data_home(data_home)
    if not ok:
        print("[%s] 拒跑 · %s" % (TAG, msg), flush=True)
        return 2
    if data_home is not None:
        os.environ["VIA_DATA_HOME"] = msg          # 只在本行程(子行程繼承);不寫任何檔
    print("[%s] 資料家目錄 · %s" % (TAG, msg), flush=True)
    runner = runner or BASE.run
    outdir = outdir or via / "VIA_Reports" / "vcgc" / "apply"
    res_a = None
    if activate:
        # 兩輪都不出頁、不開頁;最後把兩輪收據合成一份再出一張頁(不然第二輪會把 A 道的紅蓋掉,頁面看起來是綠的)
        runner(via, ["A"], want, open_page=False, page=False, outdir=outdir)
        res_a = _read_res(outdir)
        for ext in ("txt", "json"):
            if (outdir / ("APPLY_latest." + ext)).is_file():
                shutil.copyfile(outdir / ("APPLY_latest." + ext), outdir / ("APPLY_A_latest." + ext))
    runner(via, ["G", "K"], want, open_page=False, page=False, outdir=outdir, do_sync=not activate)
    res_b = _read_res(outdir)
    if res_b is None and res_a is None:
        print("[%s] go · 兩輪都沒有收據(APPLY_latest.json)· 紅" % TAG, flush=True)
        return 1
    if res_a is None and activate:
        res_a = {"steps": [{"group": "A", "name": "A-收據", "rc": None, "lamp": "紅", "secs": 0, "hits": ["A 道沒有產出收據"]}],
                 "only": ["A"], "notes": [], "sync": None}
    res = merge_results(res_a, res_b or {"steps": [{"group": "K", "name": "GK-收據", "rc": None, "lamp": "紅", "secs": 0,
                                                     "hits": ["G,K 道沒有產出收據"]}], "only": ["G", "K"], "notes": []}) if activate else res_b
    res["at"] = res.get("at") or time.strftime("%Y-%m-%dT%H:%M:%S")
    pg = BASE.write_outputs(via, outdir, res, True, open_page)          # 合成後的收據 · 貼回包 · 頁面(一份)
    lamp = res["lamp"]
    worst = {"綠": 0, "黃": 2}.get(lamp, 1)
    body = (outdir / "APPLY_latest.txt").read_text(encoding="utf-8", errors="replace")
    text = "# /go 貼回包 · %s · 總燈 %s · %s\n" % (TAG, lamp, "A 道(啟用)+ G,K 道(驗證)" if activate else "只驗證 G,K 道") + body
    (outdir / "APPLY_GO_latest.txt").write_text(text, encoding="utf-8")
    clip = to_clipboard(text)
    print("[%s] go 總燈 %s · 貼回包 %s · %s%s" % (TAG, lamp, outdir / "APPLY_GO_latest.txt", clip, (" · 頁 %s" % pg) if pg else ""), flush=True)
    return worst


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note and not cond else ""), flush=True)

    with tempfile.TemporaryDirectory(prefix="applyrun_v0105_") as td:
        t = Path(td)
        f = t / "x.out"
        f.write_text("line one\n\x1b[93m[計] 第 3 份 / 19 · OCR 中\x1b[0m\n\n", encoding="utf-8")
        chk("① 最後一行:去色碼、跳過空行", last_line(f) == "[計] 第 3 份 / 19 · OCR 中", last_line(f))
        chk("② 檔不在 → 空字串(不丟例外)", last_line(t / "nope.out") == "")
        got = []
        st = BASE.Step("A", "demo", None, [], 5, own=True)
        logdir = t / "logs"
        logdir.mkdir()
        (logdir / "A_demo.out").write_text("正在處理 MQ-1560\n", encoding="utf-8")

        def fake_prev(st_, via_, logdir_, beat_):
            beat_("A · demo 還在跑 30 秒")
            beat_("A · demo 開始")
            return st_
        global _PREV_RUN_STEP
        saved = _PREV_RUN_STEP
        _PREV_RUN_STEP = fake_prev
        try:
            run_step(st, t, logdir, got.append)
        finally:
            _PREV_RUN_STEP = saved
        chk("③ 心跳「還在跑」那行帶最後一行;其他行原樣", got == ["A · demo 還在跑 30 秒 · 最後一行:正在處理 MQ-1560", "A · demo 開始"], got)
        calls = []
        lamp_of = {"A": "黃", "G": "綠"}

        def fake_run(via, only, want, open_page=True, page=True, outdir=None, do_sync=True):
            calls.append((tuple(only), do_sync, os.environ.get("VIA_DATA_HOME"), page, open_page))
            outdir.mkdir(parents=True, exist_ok=True)
            lp = lamp_of["A" if "A" in only else "G"]
            res = {"tool": "fake", "at": "2026-11-20T00:00:00", "lamp": lp, "only": list(only), "lanes": 1, "lanes_why": "1 道",
                   "sync": {"lamp": "綠", "line": "fake sync"}, "notes": ["# 道 %s" % ",".join(only)],
                   "steps": [{"group": only[0], "name": "%s-step" % only[0], "rc": 0 if lp == "綠" else 1, "lamp": lp, "secs": 1, "hits": ["h"]}],
                   "omniroute": None, "next": "x", "logdir": "L-%s" % only[0]}
            (outdir / "APPLY_latest.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
            (outdir / "APPLY_latest.txt").write_text("# 道 %s\nNEXT: x\n" % ",".join(only), encoding="utf-8")
            return 2 if lp == "黃" else 1 if lp == "紅" else 0
        out = t / "apply"
        before_env = os.environ.get("VIA_DATA_HOME")
        rc = go_core(t, True, str(t / "不存在的夾"), None, False, runner=fake_run, outdir=out)
        chk("④ --data-home 不存在 → 拒跑 rc 2 · 零寫入(沒建輸出夾、沒跑任何步、環境沒改)",
            rc == 2 and not out.exists() and not calls and os.environ.get("VIA_DATA_HOME") == before_env)
        home = t / "vdf_database"
        home.mkdir()
        try:
            rc = go_core(t, True, str(home), None, False, runner=fake_run, outdir=out)
        finally:
            if before_env is None:
                os.environ.pop("VIA_DATA_HOME", None)
            else:
                os.environ["VIA_DATA_HOME"] = before_env
        txt = (out / "APPLY_GO_latest.txt").read_text(encoding="utf-8")
        chk("⑤ go:先 A 再 G,K(分兩次叫)· 第二次不再同步 · 子行程看得到資料家目錄 · 兩輪都不各自出頁 / 開頁",
            [c[0] for c in calls] == [("A",), ("G", "K")] and calls[1][1] is False and calls[0][2] == str(home.resolve())
            and all(c[3] is False and c[4] is False for c in calls), calls)
        chk("⑥ 兩輪合成一份貼回包(A 那份另存 APPLY_A_latest.*)· 總燈取最差(黃)",
            rc == 2 and "# 道 A" in txt and "# 道 G,K" in txt and "總燈 黃" in txt and (out / "APPLY_A_latest.txt").is_file()
            and (out / "APPLY_A_latest.json").is_file(), txt[:300])
        lamp_of.update(A="紅", G="綠")
        calls.clear()
        rc = go_core(t, True, None, None, False, runner=fake_run, outdir=out)
        merged = json.loads((out / "APPLY_latest.json").read_text(encoding="utf-8"))
        chk("⑥b Codex P2 情境:A 紅 · G,K 綠 → 最後的 APPLY_latest.json 也是紅、兩輪步驟都在(不被第二輪蓋成綠)· rc 1",
            rc == 1 and merged["lamp"] == "紅" and [s["name"] for s in merged["steps"]] == ["A-step", "G-step"], (rc, merged.get("lamp")))
        calls.clear()
        rc = go_core(t, False, None, None, False, runner=fake_run, outdir=out)
        chk("⑦ --no-activate:只跑 G,K · 會同步", [c[0] for c in calls] == [("G", "K")] and calls[0][1] is True and rc == 0, calls)
    chk("⑧ 已裝進 v0100 模組全域(run_group 叫到的是本版 run_step)", BASE.run_step is run_step)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 加速器橋真的匯入 · 不碰 TA-Lib · 不設也不寫同意閘 · 不含本機路徑",
        "import VIA_SuperAccel_Module as VIA_ACCEL" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src) and ("C:" + "\\Users") not in src)
    BASE.run_step = _PREV_RUN_STEP
    try:
        rc_prior = PRIOR.selftest()
    finally:
        BASE.run_step = run_step
    chk("⑩ 前版 %s 自測照過" % PRIOR_PATH.stem, rc_prior == 0, rc_prior)
    good = all(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if good else "FAIL", TAG, sum(ok), len(ok)))
    return 0 if good else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a == ["--selftest"]:
        return selftest()
    if a[:1] == ["go"]:
        want, dh = None, None
        if "--lanes" in a:
            try:
                want = int(a[a.index("--lanes") + 1])
            except (IndexError, ValueError):
                print("[%s] --lanes 要給數字" % TAG)
                return 2
        if "--data-home" in a:
            i = a.index("--data-home")
            if i + 1 >= len(a) or a[i + 1].startswith("--"):
                print("[%s] --data-home 要給資料夾路徑" % TAG)
                return 2
            dh = a[i + 1]
        via = BASE.find_via()
        if via is None:
            print("[%s] 找不到 VIA 夾(要有 supportive modules/registry)" % TAG)
            return 1
        return go_core(via, "--no-activate" not in a, dh, want, open_page="--no-open" not in a)
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
