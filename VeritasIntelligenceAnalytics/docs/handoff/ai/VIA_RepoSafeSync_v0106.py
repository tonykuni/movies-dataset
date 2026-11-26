#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_RepoSafeSync v0106 — 薄尾(v0100–v0105 一字不動):動態進度條 + 動態百分比 + 心跳

操作員 2026-11-25 主機實錄:安全同步在 OneDrive 倉上跑好幾分鐘畫面沒字 → 以為卡住按 Ctrl+C;
  之後要求「卡段沒反應,請加動態進度條及動態百分比」。
本版只換「怎麼跑 git、怎麼顯示」,同步的判法全照 v0105(先備份逐項驗過才動工作樹 · 只在 main 快轉 · main 為準):
  ① 四個階段:①抓 GitHub(fetch)②比對本機與 main(rev-parse / diff / ls-files …)③備份擋路檔 ④還原並快轉(merge)。
  ② 百分比:fetch / merge 加 --progress,讀 git 自己印的「Receiving objects: 45% (x/y)」→ 真實百分比;
     備份按檔數算;比對階段 git 不報進度 → 只顯示轉圈 + 已幾秒(不假造百分比)。
     總進度 = 依階段加權(①0–40 ②40–60 ③60–80 ④80–100),畫面標「依階段估」。
  ③ 終端機:同一行原地更新 [████░░░░] 23% · 階段 · git 自己的百分比 · 已幾秒;
     不是終端機(轉向檔案 / 日誌):階段一換、總進度每過 10%、或每 ≤30 秒印一行(心跳)。
  ④ Ctrl+C:先收掉正在跑的 git,印「還沒到 ④ 的話工作樹零改動」再結束。
回傳給呼叫端的 stderr 去掉進度行(錯誤訊息照舊可讀)。不 import 他系統;零 TA-Lib;零網路(git 自己連)。
用法同 v0100:python VIA_RepoSafeSync_v0106.py [--apply] [--repo <倉內任一路徑>] … · --selftest
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
import contextlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve()
FAMILY = "VIA_RepoSafeSync"
TAG = "VIA_RepoSafeSync v0106"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0106", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE, V0103 = PRIOR.BASE, PRIOR.V0103
_GIT_V0105, _BACKUP_V0105 = PRIOR._git, V0103._backup_all


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


STAGES = {1: ("抓 GitHub", 0, 40), 2: ("比對本機與 main", 40, 60), 3: ("備份擋路檔", 60, 80), 4: ("還原並快轉", 80, 100)}
PHASE_ZH = {"Counting objects": "計算物件", "Compressing objects": "壓縮物件", "Receiving objects": "收取物件",
            "Resolving deltas": "解析差異", "Updating files": "更新檔案", "Checking out files": "取出檔案",
            "remote: Counting objects": "遠端計算", "remote: Compressing objects": "遠端壓縮", "Enumerating objects": "列舉物件"}
PROGRESS_RX = re.compile(r"((?:remote: )?[A-Za-z][A-Za-z ]+?):\s+(\d{1,3})%(?:\s+\((\d+)/(\d+)\))?")
SPIN = "|/-\\"


def heartbeat_sec() -> int:
    try:
        v = int(os.environ.get("VIA_HEARTBEAT_SEC", "30"))
    except ValueError:
        v = 30
    return max(1, min(v, 30))


def bar(pct: float, width: int = 24) -> str:
    pct = max(0.0, min(100.0, pct))
    full = int(round(width * pct / 100))
    return "█" * full + "░" * (width - full)


class Progress:
    """一行動態進度(終端機原地更新;非終端機只在階段換 / 每 10% / 每 ≤30 秒印一行)。"""

    def __init__(self, out=None, tty=None, every=None):
        self.out = out or sys.stdout
        self.tty = self.out.isatty() if tty is None else tty
        self.every = every or heartbeat_sec()
        self.t0 = time.monotonic()
        self.stage, self.inner, self.cmd, self.spin = 0, None, "", 0
        self.last_pct, self.last_print, self.last_decile = -1.0, 0.0, -1
        self.lock = threading.Lock()
        self.lines = []                                   # 自測用:非終端機印過的行

    def total(self) -> float:
        if not self.stage:
            return 0.0
        _, a, b = STAGES[self.stage]
        frac = (self.inner[1] / 100.0) if self.inner else 0.0
        return a + (b - a) * frac

    def set_stage(self, n: int, cmd: str = "") -> None:
        with self.lock:
            if n < self.stage:                            # 只往前走(apply 裡的比對不倒退顯示)
                n = self.stage
            changed = n != self.stage
            self.stage, self.cmd = n, cmd or self.cmd
            if changed:
                self.inner = None
            self._render(force=changed)

    def set_inner(self, label: str, pct: float, cur=None, tot=None) -> None:
        with self.lock:
            changed = not self.inner or self.inner[0] != label or int(self.inner[1]) != int(pct)
            self.inner = (label, float(pct), cur, tot)
            self._render(force=changed and self.tty)

    def tick(self) -> None:
        with self.lock:
            self.spin += 1
            self._render()

    def _text(self) -> str:
        name = STAGES[self.stage][0] if self.stage else "準備"
        total = self.total()
        s = f"[同步 {self.stage or 0}/4 {name}] [{bar(total)}] 總 {total:3.0f}%(依階段估)"
        if self.inner:
            label, pct, cur, tot = self.inner
            s += f" · {label} {pct:3.0f}%" + (f" ({cur}/{tot})" if cur is not None and tot is not None else "")
        elif self.cmd:
            s += f" · {self.cmd} {SPIN[self.spin % 4]}"
        return s + f" · 已 {int(time.monotonic() - self.t0)} 秒"

    def _render(self, force: bool = False) -> None:
        now = time.monotonic()
        text = self._text()
        if self.tty:
            if force or now - self.last_print >= 0.2:
                self.out.write("\r" + text[:160].ljust(120))
                self.out.flush()
                self.last_print = now
            return
        decile = int(self.total() // 10)
        if force or decile > self.last_decile or now - self.last_print >= self.every:
            self.out.write(text + "\n")
            self.out.flush()
            self.lines.append(text)
            self.last_print, self.last_decile = now, max(decile, self.last_decile)

    def done(self, ok: bool = True, note: str = "") -> None:
        """收尾:只有成功(ok)且走到 ④ 才補成 100%;失敗 / 中斷照實留在當下的百分比並寫原因(PR #740 Codex P2)。"""
        with self.lock:
            if ok and self.stage == 4:
                self.inner = (self.inner[0] if self.inner else "完成", 100.0, None, None)
            text = self._text() + ("" if ok else " · 沒完成" + ((":" + note) if note else ""))
            if self.tty:
                self.out.write("\r" + text[:180].ljust(120) + "\n")
            else:
                self.out.write(text + "\n")
                self.lines.append(text)
            self.out.flush()


@contextlib.contextmanager
def ticking(ui, every: float = 0.25):
    """長步驟(單一大檔複製 · 夾複製 · 比對)期間背景定時 tick:終端機轉圈、非終端機每 ≤30 秒心跳(PR #740 Codex P2)。"""
    stop = threading.Event()

    def loop():
        while not stop.wait(every):
            ui.tick()
    t = threading.Thread(target=loop, daemon=True)
    t.start()
    try:
        yield
    finally:
        stop.set()
        t.join(timeout=2)


UI = None                                                 # 目前這一輪的進度(main 建;自測可換)


def _ui() -> Progress:
    global UI
    if UI is None:
        UI = Progress()
    return UI


def _sub(args: list) -> tuple:
    """git 子指令與它在 args 裡的位置(跳過 -c k=v / --no-pager 之類的全域選項)。"""
    i = 0
    while i < len(args):
        a = str(args[i])
        if a == "-c":
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        return a, i
    return "", -1


STAGE_OF = {"fetch": 1, "merge": 4, "restore": 4, "rm": 4}


def parse_progress(chunk: str):
    """從 git 的進度文字取最後一個「階段: NN% (x/y)」;沒有回 None。"""
    hit = None
    for m in PROGRESS_RX.finditer(chunk):
        hit = m
    if not hit:
        return None
    label = hit.group(1).strip()
    return PHASE_ZH.get(label, label), int(hit.group(2)), hit.group(3), hit.group(4)


def _strip_progress(text: str) -> str:
    keep = [ln for ln in re.split(r"[\r\n]+", text) if ln.strip() and not PROGRESS_RX.search(ln)]
    return "\n".join(keep)


def _git(repo, *a, check=False):
    """同 v0105(位元組讀 · UTF-8 + surrogateescape 解碼 · check 照舊),加:階段 · git 自己的百分比 · 轉圈 / 心跳 · Ctrl+C 收 git。"""
    args = list(a)
    sub, at = _sub(args)
    ui = _ui()
    stage = STAGE_OF.get(sub, 2)
    if stage == 2 and not getattr(ui, "fetched", False):  # fetch 做完之前的準備查詢全歸 ①(v0100 plan 先跑兩次 rev-parse;PR #740 Codex P2)
        stage = 1
    if sub in ("fetch", "merge") and "--progress" not in args and at >= 0:
        args.insert(at + 1, "--progress")
    ui.set_stage(stage, "git " + sub)
    proc = subprocess.Popen(["git", "-C", str(repo), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out_b, err_parts = [], []

    def read_out():
        out_b.append(proc.stdout.read())

    def read_err():
        buf = ""
        while True:
            chunk = proc.stderr.read1(512) if hasattr(proc.stderr, "read1") else proc.stderr.read(512)
            if not chunk:
                break
            err_parts.append(chunk)
            buf = (buf + chunk.decode("utf-8", "replace"))[-400:]
            got = parse_progress(buf)
            if got:
                ui.set_inner(*got)
    threads = [threading.Thread(target=read_out, daemon=True), threading.Thread(target=read_err, daemon=True)]
    for t in threads:
        t.start()
    try:
        while proc.poll() is None:
            ui.tick()
            time.sleep(0.25)
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        proc.kill()
        proc.wait()
        sys.stdout.write("\n[同步] 收到 Ctrl+C · git %s 已停 · 還沒到 ④ 還原並快轉 的話工作樹零改動;重跑同一行即可\n" % sub)
        sys.stdout.flush()
        raise
    if sub == "fetch":
        ui.fetched = True                                 # 從這裡起,不報進度的查詢才算 ② 比對
    out = (out_b[0] if out_b else b"").decode("utf-8", "surrogateescape")
    err = _strip_progress(b"".join(err_parts).decode("utf-8", "replace"))
    res = subprocess.CompletedProcess(["git", "-C", str(repo), *args], proc.returncode, out, err)
    if check and res.returncode != 0:
        raise RuntimeError(f"git {' '.join(map(str, a))} rc {res.returncode}: {(res.stderr or res.stdout).strip()[:200]}")
    return res


class _CountingShutil:
    """備份階段:每複製一個頂層項目(檔 copy2 · 夾 copytree)就往前推一格百分比。"""

    def __init__(self, total: int):
        self.total, self.n = max(1, total), 0

    def _step(self):
        self.n += 1
        _ui().set_inner("已備份", 100.0 * min(self.n, self.total) / self.total, min(self.n, self.total), self.total)

    def copy2(self, *a, **k):
        r = shutil.copy2(*a, **k)
        self._step()
        return r

    def copytree(self, *a, **k):
        r = shutil.copytree(*a, **k)
        self._step()
        return r

    def __getattr__(self, name):
        return getattr(shutil, name)


def _backup_all(root, p, bk):
    total = len(set(p["blocking_untracked"] + p["blocking_modified"]))
    ui = _ui()
    ui.set_stage(3, "備份 %d 項" % total)
    ui.set_inner("已備份", 0.0 if total else 100.0, 0, total)
    keep = V0103.shutil
    V0103.shutil = _CountingShutil(total)
    try:
        with ticking(ui):                                 # 單一大檔 / 整夾複製與逐項比對期間也有心跳
            return _BACKUP_V0105(root, p, bk)
    finally:
        V0103.shutil = keep


def install() -> None:
    for m in PRIOR._chain() + [PRIOR]:
        if "_git" in vars(m):
            m._git = _git
    V0103._backup_all = _backup_all
    PRIOR._backup_all = _backup_all                       # v0105 自測比對的是它模組全域的這個名字


def _restore() -> None:
    for m in PRIOR._chain() + [PRIOR]:
        if "_git" in vars(m):
            m._git = _GIT_V0105
    V0103._backup_all = _BACKUP_V0105
    PRIOR._backup_all = _BACKUP_V0105


install()


def main(argv=None) -> int:
    global UI
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    UI = Progress()
    print(f"[{TAG}] 開始 · 四階段:①抓 GitHub ②比對本機與 main ③備份擋路檔 ④還原並快轉(畫面在動就是在跑,不用按 Ctrl+C)", flush=True)
    try:
        rc = PRIOR.main(a)                                 # v0105:畫面不炸 · TAG · 收據
    except KeyboardInterrupt:
        UI.done(ok=False, note="Ctrl+C 中斷")
        raise
    except BaseException as exc:                           # noqa: BLE001 — 照實寫沒完成,再原樣丟出
        UI.done(ok=False, note=type(exc).__name__)
        raise
    UI.done(ok=rc == 0, note="" if rc == 0 else "rc %s" % rc)
    return rc


def selftest() -> int:
    import io
    import tempfile
    global UI
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    sink = io.StringIO()
    UI = Progress(out=sink, tty=False, every=30)
    rc0 = PRIOR.selftest()                                 # 前版整條鏈在本版的 _git 下跑(更嚴格:行為不能退)
    print(f"=== {TAG} · 薄尾自測(進度條 · 百分比 · 心跳;暫存倉 · 零網路)===", flush=True)
    chk("⓪ 前版 v0105 自測過(含 v0104 ~ v0100;底層已換成帶進度的 _git)", rc0 == 0, f"rc {rc0}")
    got = parse_progress("remote: Counting objects: 100% (5/5), done.\rReceiving objects:  45% (9/20)\rReceiving objects:  60% (12/20)")
    chk("① 解析 git 進度:取最後一個「收取物件 60% (12/20)」", got == ("收取物件", 60, "12", "20"), got)
    chk("② 回傳的 stderr 去掉進度行,錯誤訊息照留", _strip_progress("Receiving objects:  45% (9/20)\rfatal: boom\n") == "fatal: boom")
    sink = io.StringIO()
    UI = Progress(out=sink, tty=False, every=1)
    UI.set_stage(1, "git fetch")                           # 已抓完遠端之後的比對步驟
    UI.fetched = True
    with tempfile.TemporaryDirectory(prefix="repo_sync106_") as td:
        subprocess.run(["git", "init", "-q", td], check=True)
        r = _git(td, "-c", "alias.slow=!sleep 2.6", "slow")
    beats = [ln for ln in UI.lines if "git slow" in ln and "已 " in ln]
    chk("③ git 不報進度的長步驟:非終端機每 ≤1 秒(測試間隔)一行心跳 · 標階段 ② 與已幾秒 · 回傳碼照收",
        r.returncode == 0 and len(beats) >= 2 and all("2/4" in ln for ln in beats), UI.lines)
    sink = io.StringIO()
    UI = Progress(out=sink, tty=True, every=30)
    UI.set_stage(1, "git fetch")
    UI.set_inner("收取物件", 50, 10, 20)
    t1 = UI.total()
    UI.set_stage(3, "備份")
    UI.set_inner("已備份", 50, 1, 2)
    t3 = UI.total()
    UI.set_stage(2, "git diff")                            # 不倒退
    screen = sink.getvalue()
    chk("④ 終端機:同一行原地更新(\\r)· 進度條 · 總百分比依階段(fetch 50% → 20% · 備份 50% → 70%)· 階段不倒退",
        "\r" in screen and "█" in screen and "收取物件  50% (10/20)" in screen and abs(t1 - 20) < 0.01 and abs(t3 - 70) < 0.01 and UI.stage == 3,
        (t1, t3, UI.stage, screen[-200:]))
    with tempfile.TemporaryDirectory(prefix="repo_sync106b_") as td:
        t = Path(td)
        (t / "src").mkdir()
        for i in range(4):
            (t / "src" / f"f{i}.txt").write_text(str(i), encoding="utf-8")
        sink = io.StringIO()
        UI = Progress(out=sink, tty=False, every=30)
        cs = _CountingShutil(4)
        for i in range(4):
            cs.copy2(t / "src" / f"f{i}.txt", t / f"g{i}.txt")
        inner5 = UI.inner
    sink = io.StringIO()
    UI = Progress(out=sink, tty=False, every=30)
    with tempfile.TemporaryDirectory(prefix="repo_sync106c_") as td:
        subprocess.run(["git", "init", "-q", td], check=True)
        _git(td, "rev-parse", "--is-inside-work-tree")
        before = UI.stage
        UI.set_stage(1, "git fetch")
        UI.set_inner("收取物件", 100, 3, 3)
        fetch_total = UI.total()
    chk("④b fetch 之前的準備查詢歸在 ①:fetch 100% → 總 40%(不被算成 ② 的 60%)", before == 1 and abs(fetch_total - 40) < 0.01, (before, fetch_total))
    chk("⑤ 備份按檔數推百分比(4 檔 → 100% · 4/4)", inner5 == ("已備份", 100.0, 4, 4), inner5)
    with tempfile.TemporaryDirectory(prefix="repo_sync106d_") as td:
        t = Path(td)
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(t / "up.git")], check=True)
        subprocess.run(["git", "clone", "-q", str(t / "up.git"), str(t / "dev")], check=True, capture_output=True)
        for k, v in (("user.email", "t@t"), ("user.name", "t")):
            subprocess.run(["git", "-C", str(t / "dev"), "config", k, v], check=True)
        (t / "dev" / "a").write_text("a\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(t / "dev"), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(t / "dev"), "commit", "-qm", "c"], check=True)
        subprocess.run(["git", "-C", str(t / "dev"), "push", "-q", "origin", "main"], check=True, capture_output=True)
        UI = Progress(out=io.StringIO(), tty=False, every=30)
        seen = []
        _git(t / "dev", "rev-parse", "--show-toplevel"); seen.append(UI.stage)
        _git(t / "dev", "rev-parse", "--abbrev-ref", "HEAD"); seen.append(UI.stage)
        _git(t / "dev", "fetch", "origin", "main"); seen.append(UI.stage)
        _git(t / "dev", "diff", "--name-only", "HEAD"); seen.append(UI.stage)
    chk("⑦ v0100 plan 的真實順序(兩次 rev-parse → fetch → diff):fetch 前都在 ①,fetch 做完才進 ②", seen == [1, 1, 1, 2], seen)
    UI = Progress(out=io.StringIO(), tty=False, every=30)
    UI.set_stage(4, "git merge")
    UI.done(ok=False, note="rc 2")
    bad_line = UI.lines[-1]
    UI = Progress(out=io.StringIO(), tty=False, every=30)
    UI.set_stage(4, "git merge")
    UI.done(ok=True)
    good_line = UI.lines[-1]
    chk("⑧ 收尾照實:失敗 / 中斷不補成 100%、寫「沒完成」與原因;成功走到 ④ 才 100%",
        "100%" not in bad_line and "沒完成:rc 2" in bad_line and "100%" in good_line and "沒完成" not in good_line, (bad_line, good_line))
    UI = Progress(out=io.StringIO(), tty=False, every=1)
    UI.set_stage(3, "備份 1 項")
    n0 = len(UI.lines)
    with ticking(UI):
        time.sleep(2.6)                                    # 模擬單一大檔複製卡在 copy2 裡
    chk("⑨ 備份單一大檔期間也有心跳(背景定時 tick · 非終端機每 ≤1 秒測試間隔一行)", len(UI.lines) - n0 >= 2, UI.lines[n0:])
    src = HERE.read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑥ 檔面:加速器橋 · 零 TA-Lib · 不 import 他系統 · 整條前版鏈的 _git 都換成本版 · 前版一字不動",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(?:import|from)\s+(talib|CGC_|VDF_|VRN_|VQG_|VAP_)", body, re.M)
        and all(vars(m)["_git"] is _git for m in PRIOR._chain() + [PRIOR] if "_git" in vars(m)) and PRIOR_PATH.name < HERE.name)
    UI = None
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
