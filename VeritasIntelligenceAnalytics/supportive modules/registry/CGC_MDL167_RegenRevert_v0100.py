# -*- coding: utf-8 -*-
r"""再生物還原閘 v0100(批613)—— 跑完之後,把引擎自己長出來的東西放回去。

三次卡死同一個病根(批605 · 批606 · 批612):
  工作站跑一次 ALL-IN-ONE,再生物(報告、U/I 頁、掃樹冊)就把追蹤檔弄髒;
  沒人還原 → 下一次 `git pull` 被它擋住 → 操作員卡住 → 我送解卡工具 →
  解卡工具在拉不下來的 commit 裡 → 再卡一次。
容器這邊我每一批 commit 前都手動還原(批612 還原 30 支),**靠我記得**不是制度。

它做三件事,而且**預設一個字都不改**:
  ① 分類   把「髒的追蹤檔」分成 再生物 / 白名單(刻意入倉)/ **不明**
  ② 攤開   每一類逐檔點名,再生物附**憑什麼算再生物**的理由(L87)
  ③ apply  只有 `--apply` 才還原,而且**只還原再生物**

鐵則:
  · 未追蹤檔一根不碰(引擎根本不讀 untracked)
  · 沒對上任何樣式的 = **不明 → 不還原**。不明的東西交給操作員看,
    不是替他丟掉(只增不減)。引擎寫到原始碼 vs 他自己改的,長得一模一樣。
  · 還原前先把原檔整包複製到 VIA_Reports/regen_revert/<ts>/(第二條退路)
  · 絕不 force、絕不刪未追蹤、絕不 commit、絕不 push

rc 誠實多態:0=GREEN(沒有髒的,或全部是再生物且已依指示處理)
             1=RED(有**不明**的髒檔——那要人看) · 2=NODATA(不是 git 倉)
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(本閘零連線) =====
VIA_NET_TOOL_PATH = None


def _via_net():
    """本閘**零連線**:永遠回 None,存在只為全樹契約齊備。"""
    return None
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
BOOK_NAME = "VIA_RegenArtifacts_SSOT_v0100.json"
RC_NAME = {0: "GREEN", 1: "RED", 2: "NODATA", 3: "ABSENT"}


def _git(root: Path, *a: str) -> tuple[int, str]:
    r = subprocess.run(["git", *a], cwd=str(root), capture_output=True, text=True, errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def repo_root(start: Path) -> Path | None:
    rc, out = _git(start, "rev-parse", "--show-toplevel")
    return Path(out.strip()) if rc == 0 and out.strip() else None


def load_book(via: Path) -> dict | None:
    for c in (via / "supportive modules" / "registry" / BOOK_NAME, HERE / BOOK_NAME):
        try:
            if c.is_file():
                return json.loads(c.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def dirty_tracked(root: Path) -> list[str]:
    """只問**追蹤檔**的改動。未追蹤件連問都不問。"""
    rc, out = _git(root, "diff", "--name-only")
    if rc != 0:
        return []
    return [l.strip() for l in out.splitlines() if l.strip()]


def classify(files: list[str], book: dict) -> dict:
    pats = [(re.compile(p["rx"]), p["why"]) for p in book.get("patterns", [])]
    keep = {k["path"]: k["why"] for k in book.get("keep_even_if_matched", [])}
    regen, kept, unknown = [], [], []
    for f in files:
        if f in keep:
            kept.append({"file": f, "why": keep[f]})
            continue
        hit = next(((rx.pattern, why) for rx, why in pats if rx.search(f)), None)
        if hit:
            regen.append({"file": f, "rx": hit[0], "why": hit[1]})
        else:
            unknown.append({"file": f})
    return {"regen": regen, "kept": kept, "unknown": unknown}


def backup(root: Path, files: list[str], ts: str) -> Path:
    dst = root / "VeritasIntelligenceAnalytics" / "VIA_Reports" / "regen_revert" / ts
    for f in files:
        s = root / f
        d = dst / f
        try:
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)
        except Exception:
            pass
    return dst


def run(root: Path, book: dict, apply: bool = False, quiet: bool = False) -> dict:
    say = (lambda *a: None) if quiet else print
    files = dirty_tracked(root)
    c = classify(files, book)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    did, bak = [], None
    if apply and c["regen"]:
        bak = backup(root, [x["file"] for x in c["regen"]], ts)
        rc, out = _git(root, "checkout", "--", *[x["file"] for x in c["regen"]])
        if rc == 0:
            did = [x["file"] for x in c["regen"]]
        else:
            say("[警] git checkout 回 %d:%s" % (rc, out.strip()[:200]))
    rc = 1 if c["unknown"] else 0
    return {"root": root.as_posix(), "n_dirty": len(files), **c,
            "applied": did, "backup": bak.as_posix() if bak else "",
            "apply": apply, "rc": rc, "state": RC_NAME[rc]}


def report(rep: dict) -> None:
    print("\n=== 再生物還原閘 v%s ===" % VERSION)
    print("[倉] %s" % rep["root"])
    print("[計] 髒的追蹤檔 %d · 再生物 %d · 刻意入倉 %d · **不明 %d**"
          % (rep["n_dirty"], len(rep["regen"]), len(rep["kept"]), len(rep["unknown"])))
    for x in rep["regen"]:
        print("  [再生] %-64s %s" % (x["file"][-64:], x["why"]))
    for x in rep["kept"]:
        print("  [留下] %-64s %s" % (x["file"][-64:], x["why"]))
    for x in rep["unknown"]:
        print("  [不明] %s" % x["file"])
    if rep["unknown"]:
        print("         **不明的一律不還原。** 引擎寫到原始碼、和你自己改的,長得一模一樣——")
        print("         這裡只有你分得出來。看一眼:git diff -- <檔>")
    if rep["apply"]:
        print("[還原] %d 支(備份 %s)" % (len(rep["applied"]), rep["backup"] or "無"))
    elif rep["regen"]:
        print("[計畫] 預設零動作。要還原:加 --apply(只動再生物,動之前先整包備份)")
    print("[裁決] rc=%d (%s)" % (rep["rc"], rep["state"]))


# ══════════════════════════════════════════════════════════════════════════════
def _selftest() -> int:
    ok, bad = [], []

    def chk(n, c, why=""):
        (ok if c else bad).append(n)
        print(("  ✓ " + n) if c else "  [FAIL] %s — %s" % (n, why))

    print("🧪 CGC_MDL167 再生物還原閘 v%s --selftest(零連線;只在暫存夾造假倉)" % VERSION)

    book = load_book(VIA)
    chk("① 冊在位且每筆樣式都附非空理由(L87)",
        bool(book) and all(len(p.get("why", "").strip()) >= 8 for p in (book or {}).get("patterns", [])),
        "冊不在或有樣式沒寫理由")
    if not book:
        return 3

    with tempfile.TemporaryDirectory() as td:
        R = Path(td) / "repo"
        (R / "VeritasIntelligenceAnalytics" / "VIA_Reports").mkdir(parents=True)
        (R / "VeritasIntelligenceAnalytics" / "supportive modules" / "ui_support").mkdir(parents=True)
        (R / "VeritasIntelligenceAnalytics" / "supportive modules" / "registry").mkdir(parents=True)
        (R / "src").mkdir()
        f_rep = R / "VeritasIntelligenceAnalytics" / "VIA_Reports" / "run.json"
        f_ui = R / "VeritasIntelligenceAnalytics" / "supportive modules" / "ui_support" / "VIA_UI_X_v0100.html"
        f_led = R / "VeritasIntelligenceAnalytics" / "supportive modules" / "registry" / "VIA_AutoCode_Registry_v0100.json"
        f_src = R / "src" / "engine.py"
        for f in (f_rep, f_ui, f_led, f_src):
            f.write_text("v1\n", encoding="utf-8")
        for a in (("init", "-q", "-b", "main"), ("config", "user.email", "a@b.c"),
                  ("config", "user.name", "t"), ("add", "-A"), ("commit", "-qm", "base")):
            _git(R, *a)
        for f in (f_rep, f_ui, f_led, f_src):
            f.write_text("v2-dirty\n", encoding="utf-8")
        (R / "untracked.txt").write_text("不准碰\n", encoding="utf-8")

        r = run(R, book, apply=False, quiet=True)
        names = lambda k: sorted(Path(x["file"]).name for x in r[k])
        chk("② 分類:再生物認得出(報告夾 + U/I 頁)",
            names("regen") == ["VIA_UI_X_v0100.html", "run.json"], "regen=%s" % names("regen"))
        chk("③ 分類:刻意入倉的白名單不當成再生物(台帳是人寫件)",
            names("kept") == ["VIA_AutoCode_Registry_v0100.json"], "kept=%s" % names("kept"))
        chk("④ 分類:對不上樣式的是**不明**,不是再生物",
            names("unknown") == ["engine.py"], "unknown=%s" % names("unknown"))
        chk("⑤ 有不明 → rc=1(那要人看,不能當綠燈過去)", r["rc"] == 1, "rc=%s" % r["rc"])
        chk("⑥ 預設零動作:沒 --apply 就一個字都不改",
            f_rep.read_text(encoding="utf-8").strip() == "v2-dirty", "沒 apply 卻改了檔")

        r2 = run(R, book, apply=True, quiet=True)
        chk("⑦ --apply 只還原再生物",
            f_rep.read_text(encoding="utf-8").strip() == "v1"
            and f_ui.read_text(encoding="utf-8").strip() == "v1", "再生物沒被還原")
        chk("⑧ --apply **不碰**不明與白名單(只增不減)",
            f_src.read_text(encoding="utf-8").strip() == "v2-dirty"
            and f_led.read_text(encoding="utf-8").strip() == "v2-dirty", "動到不該動的")
        chk("⑨ 未追蹤檔一根不碰", (R / "untracked.txt").exists()
            and (R / "untracked.txt").read_text(encoding="utf-8").strip() == "不准碰")
        chk("⑩ 還原前先整包備份(第二條退路)",
            bool(r2["backup"]) and (Path(r2["backup"]) / "VeritasIntelligenceAnalytics"
                                    / "VIA_Reports" / "run.json").is_file(),
            "備份 %s" % r2["backup"])
        r3 = run(R, book, apply=False, quiet=True)
        chk("⑪ 冪等:再跑一次,再生物已乾淨,剩下的還是那支不明",
            [Path(x["file"]).name for x in r3["regen"]] == []
            and [Path(x["file"]).name for x in r3["unknown"]] == ["engine.py"],
            "regen=%s unknown=%s" % (names("regen"), names("unknown")))

    with tempfile.TemporaryDirectory() as td:
        chk("⑫ 不是 git 倉 → 誠實 NODATA,不裸噴", repo_root(Path(td)) is None)

    # 批613 自審:第一版這一檢**禁止整份原始碼出現 "commit"**——可是自測造假倉本來就要
    # `git commit`,於是它判自己紅。尺要量的是**正式路徑**,不是連測具一起管(LL159 同族)。
    src = Path(__file__).read_text(encoding="utf-8", errors="replace")
    prod = src[:src.index("def _selftest")]          # 正式路徑 = 自測段之前
    chk("⑬ 正式路徑零 force · 零刪未追蹤 · 零 commit · 零 push(測具造假倉的 commit 不算)",
        all(k not in prod for k in ("--force", "clean -", '"push"', '"commit"', '"reset"'))
        and '"checkout"' in prod,
        "正式路徑出現了不該有的 git 動詞")
    chk("⑭ 帶加速器橋與網路橋(全樹契約)",
        "[VIA:ACCEL-BRIDGE:" in src and "[VIA:NET-BRIDGE:" in src)

    rc = 1 if bad else 0
    print("[計] 十四檢 OK %d · FAIL %d → rc=%d (%s)" % (len(ok), len(bad), rc, RC_NAME[rc]))
    return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="CGC_MDL167_RegenRevert")
    ap.add_argument("verb", nargs="?", default="scan", choices=["scan", "plan", "apply"])
    ap.add_argument("--apply", action="store_true", help="真的還原(只動再生物;預設零動作)")
    ap.add_argument("--root", default="")
    ap.add_argument("--json", default="")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--self-test", dest="selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()

    start = Path(a.root).resolve() if a.root else VIA
    root = repo_root(start)
    if root is None:
        print("[NODATA] %s 不在 git 倉裡。**不是壞掉**:--root 指到倉內再跑。" % start)
        return 2
    book = load_book(VIA)
    if book is None:
        print("[ABSENT] 冊 %s 不在(supportive modules/registry 找過)" % BOOK_NAME)
        print("         **缺冊不是壞掉**:先把冊放回正典位置。誠實停,不猜樣式。")
        return 3
    rep = run(root, book, apply=(a.apply or a.verb == "apply"))
    report(rep)
    if a.json:
        try:
            Path(a.json).parent.mkdir(parents=True, exist_ok=True)
            Path(a.json).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
            print("[報告] " + a.json)
        except Exception as e:
            print("[警] 報告寫不出來(不影響裁決):%s" % e)
    return rep["rc"]


if __name__ == "__main__":
    sys.exit(main())
