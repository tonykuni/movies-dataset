#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL184_SisterMirrorSync v0100 — 母倉 ↔ 姊妹倉 同步自動相互更新檢查(批728)

操作員 2026-09-23 令:「讀取 VCGC 的相關工具 SSOT REGEX 同步自動相互更新檢查」+「重整 VRN 實測修正到成功」,
並指出姊妹倉那一條線的 VRN 成果「在錯誤位置進行」——正位是母倉。

**先量再造(LL400)。** 批728 量出來的兩個洞:

| 方向 | 誰在管 | 洞 |
|---|---|---|
| 母 → 姊(VCGC 鏡像) | 姊妹倉 `scripts/VIA_VCGC_Sync.py --compare`(要一份母倉 clone) | **只有姊妹倉那一側看得到**。母倉升一版(SUP_MDL749 v0112→v0113、PR #75 改 VRN_FieldRules 券商法),母倉自己沒有任何一盞燈會亮 |
| 姊 ↔ 母(VRN 第二血統) | 沒有人 | 批728 把姊妹倉 34d91ac 的引擎搬回母倉,母倉在其上另有修(批702 陸券清除 · 批728 拒絕清單認法 · 名冊收容副本 · G10 母倉模式 · [進度] 協定)。之後誰先動、誰落後,**沒有冊記、沒有燈量** |

所以一支唯讀、兩個方向:
① **鏡像新鮮度**:讀姊妹倉 `supportive modules/DELIVERY_MANIFEST.json`(VIA_VCGC_Mirror_Manifest_v0100),每一條對母倉的
   **尾版**(L54)比:SAME / SAME_EOL(只差 CRLF)/ NEW_VERSION(母倉出了新版號,姊妹倉該重同步)/ CHANGED(同一路徑內容變了,
   例如就地改的規則冊)/ GONE_IN_MOTHER。
② **血統同步**:同步冊 `VIA_VRN_SisterLineage_Sync_v0100.json` 記下同步當下兩邊每一檔的內容指紋(LF 正規化 sha256)。
   之後逐檔:IN_SYNC(兩邊都沒動)/ SISTER_AHEAD(姊妹倉又改了 → 母倉該三方合併收回)/ MOTHER_AHEAD(母倉改了 →
   姊妹倉該收)/ BOTH_CHANGED(兩邊都動 → 要人看,紅)/ MISSING。

總判:全同步 GREEN rc0 · 有人落後 YELLOW rc0(要動作,不是壞掉)· BOTH_CHANGED / MISSING / 讀冊失敗 RED rc1 ·
找不到姊妹倉 NODATA rc2(量不到不是壞掉,L16)。

讀姊妹倉兩種:`--sister <路徑>`(工作樹)或再加 `--ref <git ref>`(git show 讀該 ref,不動姊妹倉工作樹)。
沒給 `--sister` 依序找:環境變數 VIA_SISTER_ROOT、母倉倉根旁的 VIA-VDF-VRN / via-vdf-vrn、C:\Users\tonyk\VIA-VDF-VRN。

律:唯讀(`record` 只寫同步冊且要 `--apply`)· 零網路 · 不設同意閘 · 不碰姊妹倉任何一個位元組 · stdlib。
用法:
  python CGC_MDL184_SisterMirrorSync_v0100.py check  [--sister PATH] [--ref REF] [--json]
  python CGC_MDL184_SisterMirrorSync_v0100.py record  --sister PATH [--ref REF] [--note TEXT] --apply
  python CGC_MDL184_SisterMirrorSync_v0100.py --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 缺席零影響) =====
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
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ENGINE_ID = "CGC_MDL184_SisterMirrorSync"
VERSION = "v0100"
BATCH = "批728"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent                      # 母倉 VeritasIntelligenceAnalytics/
SYNC_BOOK = HERE / "VIA_VRN_SisterLineage_Sync_v0100.json"
MANIFEST_REL = "supportive modules/DELIVERY_MANIFEST.json"
SISTER_REPO = "tonykuni/VIA-VDF-VRN"
TEXT_SUFFIXES = {".py", ".json", ".md", ".txt", ".ps1", ".csv", ".ts"}
# 第二血統:姊妹倉與母倉**同一個相對路徑**(姊妹倉以倉根為根,母倉以 VeritasIntelligenceAnalytics/ 為根)
LINEAGE = (
    "functional modules/VRN/engine/VIA_VRN_FirstPageEngine.py",
    "functional modules/VRN/engine/VRN_AutoTestLoop.py",
    "functional modules/VRN/engine/VRN_Evidence_Core.py",
    "functional modules/VRN/engine/VRN_Integrated_ReportDatabase_Engine.py",
    "functional modules/VRN/engine/VRN_PanoramaProbe.py",
    "functional modules/VRN/engine/VIA_TW_Ticker_Master_v0210.py",
    "functional modules/VRN/tests/test_VRN_AutoTestLoop.py",
    "functional modules/VRN/tests/test_VRN_Evidence_Core.py",
    "functional modules/VRN/tests/test_VRN_FirstPageEngine.py",
    "functional modules/VRN/tests/test_VRN_PanoramaProbe.py",
    "functional modules/VRN/tests/test_VRN_ReportDatabase_Engine.py",
    "functional modules/VRN/Invoke-VRN-AutoTest.ps1",
)
OK_MIRROR = ("SAME", "SAME_EOL")
BEHIND_MIRROR = ("NEW_VERSION", "CHANGED")
RED_LINEAGE = ("BOTH_CHANGED", "MISSING")
YELLOW_LINEAGE = ("SISTER_AHEAD", "MOTHER_AHEAD")


# ── 指紋 ────────────────────────────────────────────────────────────────
def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lf_sha(data: bytes) -> str:
    """內容指紋:CRLF → LF 後的 sha256(Git for Windows autocrlf 會把 LF 檔換成 CRLF;換行不是內容)。"""
    return sha(data.replace(b"\r\n", b"\n"))


def _ver(name: str) -> int:
    m = re.search(r"_v(\d+)\.", name)
    return int(m.group(1)) if m else -1


# ── 姊妹倉讀取:工作樹或 git ref(兩種都唯讀)──────────────────────────
class Sister:
    def __init__(self, root: Path, ref: str = ""):
        self.root = Path(root)
        self.ref = ref

    def read(self, rel: str) -> bytes | None:
        if self.ref:
            r = subprocess.run(["git", "-C", str(self.root), "show", f"{self.ref}:{rel}"],
                               capture_output=True, timeout=120)
            return r.stdout if r.returncode == 0 else None
        p = self.root / rel
        try:
            return p.read_bytes() if p.is_file() else None
        except OSError:
            return None

    def commit(self) -> str:
        try:
            r = subprocess.run(["git", "-C", str(self.root), "rev-parse", self.ref or "HEAD"],
                               capture_output=True, text=True, timeout=30)
            return r.stdout.strip() if r.returncode == 0 else ""
        except Exception:
            return ""

    def label(self) -> str:
        return f"{self.root}" + (f" @ {self.ref}" if self.ref else " (工作樹)")


def find_sister(explicit: str = "") -> Path | None:
    """姊妹倉在哪裡:明給的 > VIA_SISTER_ROOT > 母倉倉根旁 > 工作站慣用路徑。找不到回 None(NODATA,不猜)。"""
    cands = []
    if explicit:
        cands.append(Path(explicit))
    env = os.environ.get("VIA_SISTER_ROOT", "")
    if env:
        cands.append(Path(env))
    repo = VIA.parent
    cands += [repo.parent / "VIA-VDF-VRN", repo.parent / "via-vdf-vrn", Path(r"C:\Users\tonyk\VIA-VDF-VRN")]
    for c in cands:
        try:
            if (c / "functional modules" / "VRN").is_dir() or (c / ".git").exists():
                return c
        except OSError:
            continue
    return None


# ── 母倉尾版 ────────────────────────────────────────────────────────────
def mother_tail(entry: str) -> Path | None:
    """manifest 的 entry('…_v*.py' 取尾版;無 '*' 取同名)→ 母倉實檔。"""
    if "*" not in entry:
        p = VIA / entry
        return p if p.is_file() else None
    folder = VIA / Path(entry).parent
    hits = sorted(folder.glob(Path(entry).name), key=lambda q: _ver(q.name))
    return hits[-1] if hits else None


# ── ① 鏡像新鮮度 ────────────────────────────────────────────────────────
def mirror_rows(sister: Sister) -> dict:
    raw = sister.read(MANIFEST_REL)
    if raw is None:
        return {"state": "NODATA", "why": f"姊妹倉沒有 {MANIFEST_REL}(還沒建鏡像,或路徑/ref 不對)", "rows": []}
    try:
        man = json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        return {"state": "RED", "why": f"manifest 讀不出來:{type(exc).__name__}", "rows": []}
    rows = []
    for item in man.get("files", []):
        entry = item.get("entry") or item.get("path") or ""
        mp = mother_tail(entry)
        if mp is None:
            rows.append({"entry": entry, "mirror": item.get("path"), "mother": None, "state": "GONE_IN_MOTHER"})
            continue
        mrel = mp.relative_to(VIA).as_posix()
        data = mp.read_bytes()
        if mrel != item.get("path"):
            state = "NEW_VERSION"
        elif sha(data) == item.get("sha256"):
            state = "SAME"
        elif mp.suffix.lower() in TEXT_SUFFIXES and lf_sha(data) == item.get("sha256"):
            state = "SAME_EOL"
        else:
            state = "CHANGED"
        rows.append({"entry": entry, "mirror": item.get("path"), "mother": mrel, "state": state})
    behind = [r for r in rows if r["state"] in BEHIND_MIRROR]
    gone = [r for r in rows if r["state"] == "GONE_IN_MOTHER"]
    state = "RED" if gone else ("YELLOW" if behind else ("GREEN" if rows else "NODATA"))
    return {"state": state, "rows": rows, "synced_commit": man.get("commit", ""), "synced_at": man.get("synced_at", ""),
            "why": (f"姊妹倉鏡像落後 {len(behind)} 條:在姊妹倉跑 `python scripts/VIA_VCGC_Sync.py --apply --mother <母倉>`"
                    if behind else "")}


# ── ② 血統同步 ──────────────────────────────────────────────────────────
def read_book(path: Path = SYNC_BOOK) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def lineage_rows(sister: Sister, book: dict | None, mother_root: Path = VIA) -> dict:
    if not book:
        return {"state": "NODATA", "why": f"同步冊 {SYNC_BOOK.name} 不在:先 `record --apply` 記一次同步基準", "rows": []}
    base = {f["path"]: f for f in book.get("files", [])}
    rows = []
    for rel in book.get("lineage") or LINEAGE:
        b = base.get(rel)
        s_raw = sister.read(rel)
        m_path = mother_root / rel
        m_raw = m_path.read_bytes() if m_path.is_file() else None
        if b is None:
            rows.append({"path": rel, "state": "NOT_RECORDED"})
            continue
        if s_raw is None or m_raw is None:
            rows.append({"path": rel, "state": "MISSING",
                         "side": "姊妹倉" if s_raw is None else "母倉"})
            continue
        s_now, m_now = lf_sha(s_raw), lf_sha(m_raw)
        s_moved = s_now != b.get("sister_lf_sha256")
        m_moved = m_now != b.get("mother_lf_sha256")
        state = ("BOTH_CHANGED" if s_moved and m_moved else "SISTER_AHEAD" if s_moved
                 else "MOTHER_AHEAD" if m_moved else "IN_SYNC")
        rows.append({"path": rel, "state": state, "same_content_now": s_now == m_now,
                     "mother_patches": b.get("mother_patches", [])})
    red = [r for r in rows if r["state"] in RED_LINEAGE]
    yellow = [r for r in rows if r["state"] in YELLOW_LINEAGE or r["state"] == "NOT_RECORDED"]
    state = "RED" if red else ("YELLOW" if yellow else "GREEN")
    return {"state": state, "rows": rows, "base_commit": book.get("sister_commit", ""),
            "recorded_at": book.get("recorded_at", "")}


def check(sister_root: str = "", ref: str = "", book_path: Path = SYNC_BOOK, mother_root: Path = VIA) -> dict:
    root = find_sister(sister_root)
    if root is None:
        return {"verdict": "NODATA", "rc": 2, "why": "找不到姊妹倉:給 --sister <路徑> 或設 VIA_SISTER_ROOT(量不到不是壞掉)",
                "mirror": {}, "lineage": {}}
    s = Sister(root, ref)
    mir = mirror_rows(s)
    lin = lineage_rows(s, read_book(book_path), mother_root)
    states = (mir.get("state"), lin.get("state"))
    verdict = ("RED" if "RED" in states else "YELLOW" if "YELLOW" in states
               else "GREEN" if states == ("GREEN", "GREEN") else "NODATA" if states == ("NODATA", "NODATA")
               else "YELLOW")
    rc = 1 if verdict == "RED" else (2 if verdict == "NODATA" else 0)
    return {"verdict": verdict, "rc": rc, "sister": s.label(), "sister_commit": s.commit(),
            "mirror": mir, "lineage": lin}


def record(sister_root: str, ref: str = "", note: str = "", apply: bool = False,
           book_path: Path = SYNC_BOOK, mother_root: Path = VIA) -> dict:
    """同步完成後記基準:兩邊每一檔的 LF 指紋。只增不減:舊基準移進 history。"""
    root = find_sister(sister_root)
    if root is None:
        return {"state": "NODATA", "why": "找不到姊妹倉"}
    s = Sister(root, ref)
    files = []
    for rel in LINEAGE:
        s_raw, m_path = s.read(rel), mother_root / rel
        if s_raw is None or not m_path.is_file():
            files.append({"path": rel, "state": "MISSING_AT_RECORD"})
            continue
        m_raw = m_path.read_bytes()
        files.append({"path": rel, "sister_lf_sha256": lf_sha(s_raw), "mother_lf_sha256": lf_sha(m_raw),
                      "identical": lf_sha(s_raw) == lf_sha(m_raw)})
    old = read_book(book_path) or {}
    book = {
        "schema": "VIA_VRN_SisterLineage_Sync_v0100",
        "purpose": "母倉 ↔ 姊妹倉 VRN 第二血統的同步基準(內容指紋 = LF 正規化 sha256)。CGC_MDL184 check 拿它判誰先動、誰落後。",
        "sister_repo": SISTER_REPO,
        "sister_ref": ref or "(工作樹)",
        "sister_commit": s.commit(),
        "recorded_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "recorded_by": f"{ENGINE_ID} {VERSION} record",
        "note": note,
        "lineage": list(LINEAGE),
        "files": files,
        "history": (old.get("history") or []) + ([{k: old.get(k) for k in ("sister_commit", "recorded_at", "note")}]
                                                 if old.get("recorded_at") else []),
    }
    if apply:
        book_path.write_text(json.dumps(book, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"state": "WRITTEN" if apply else "DRY_RUN", "path": str(book_path), "book": book}


def render(res: dict) -> None:
    print(f"=== {ENGINE_ID} {VERSION} · 母倉 ↔ 姊妹倉 同步自動相互更新檢查 ===")
    if res.get("verdict") == "NODATA" and not res.get("mirror"):
        print(f"  [NODATA] {res.get('why')}")
        return
    print(f"  [姊妹倉] {res.get('sister')} · {res.get('sister_commit', '')[:10]}")
    mir, lin = res.get("mirror", {}), res.get("lineage", {})
    print(f"  ① VCGC 鏡像(姊妹倉 manifest 對母倉尾版):{mir.get('state')}"
          f" · 封於 {str(mir.get('synced_commit', ''))[:10]} {mir.get('synced_at', '')}")
    for r in mir.get("rows", []):
        tag = "OK " if r["state"] in OK_MIRROR else "!! "
        print(f"     {tag}{r['state']:<14} {r['entry']}" + (f" → 母倉 {Path(r['mother']).name}" if r.get("mother") and r["state"] == "NEW_VERSION" else ""))
    if mir.get("why"):
        print(f"     [指路] {mir['why']}")
    print(f"  ② VRN 第二血統(同步冊基準 {str(lin.get('base_commit', ''))[:10]} {lin.get('recorded_at', '')}):{lin.get('state')}")
    for r in lin.get("rows", []):
        extra = "" if r.get("same_content_now") is None else (" · 兩邊內容此刻相同" if r["same_content_now"] else " · 兩邊內容此刻不同")
        print(f"     {r['state']:<14} {r['path']}{extra}")
    if lin.get("why"):
        print(f"     [指路] {lin['why']}")
    print(f"  [計] 鏡像 {len(mir.get('rows', []))} 條 · 血統 {len(lin.get('rows', []))} 檔 → {res.get('verdict')} (rc={res.get('rc')})")


# ── 自測:沙盒兩棵假樹,每一個態都要咬得到;真樹一個位元組都不准動 ──────────
def selftest() -> int:
    t0 = time.time()
    ran, fails = [], []

    def chk(name, ok, detail=""):
        ran.append(name)
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name} {detail}".rstrip())

    tmp = Path(tempfile.mkdtemp(prefix="mdl184_"))
    try:
        mother = tmp / "mother"          # 假母倉(VeritasIntelligenceAnalytics/ 同形)
        sis = tmp / "sister"             # 假姊妹倉(倉根同形)
        for base in (mother, sis):
            (base / "functional modules" / "VRN" / "engine").mkdir(parents=True)
            (base / "functional modules" / "VRN" / "tests").mkdir(parents=True)
        (mother / "supportive modules" / "registry").mkdir(parents=True)
        (sis / "supportive modules").mkdir(parents=True)
        # 母倉工具:v0101 → 升 v0102;規則冊就地改
        tool1 = mother / "supportive modules" / "registry" / "CGC_MDLX_Tool_v0101.py"
        tool1.write_text("print('v0101')\n", encoding="utf-8")
        book1 = mother / "supportive modules" / "registry" / "Rules_SSOT_v0100.json"
        book1.write_text('{"a": 1}\n', encoding="utf-8")
        same1 = mother / "supportive modules" / "registry" / "Same_SSOT_v0100.json"
        same1.write_text('{"same": true}\n', encoding="utf-8")
        eol1 = mother / "supportive modules" / "registry" / "Eol_v0100.py"
        eol1.write_bytes(b"x = 1\r\ny = 2\r\n")     # 母倉工作站 autocrlf 簽出成 CRLF;manifest 記的是 git 的 LF 位元
        man = {"schema": "VIA_VCGC_Mirror_Manifest_v0100", "commit": "abc", "synced_at": "t0", "files": [
            {"entry": "supportive modules/registry/CGC_MDLX_Tool_v*.py", "path": "supportive modules/registry/CGC_MDLX_Tool_v0101.py", "sha256": sha(tool1.read_bytes())},
            {"entry": "supportive modules/registry/Rules_SSOT_v0100.json", "path": "supportive modules/registry/Rules_SSOT_v0100.json", "sha256": sha(book1.read_bytes())},
            {"entry": "supportive modules/registry/Same_SSOT_v0100.json", "path": "supportive modules/registry/Same_SSOT_v0100.json", "sha256": sha(same1.read_bytes())},
            {"entry": "supportive modules/registry/Eol_v0100.py", "path": "supportive modules/registry/Eol_v0100.py", "sha256": sha(b"x = 1\ny = 2\n")},
            {"entry": "supportive modules/registry/Gone_v*.py", "path": "supportive modules/registry/Gone_v0100.py", "sha256": "0" * 64},
        ]}
        (sis / MANIFEST_REL).write_text(json.dumps(man), encoding="utf-8")
        # 母倉之後的動作:工具升版、規則冊就地改
        (mother / "supportive modules" / "registry" / "CGC_MDLX_Tool_v0102.py").write_text("print('v0102')\n", encoding="utf-8")
        book1.write_text('{"a": 2}\n', encoding="utf-8")

        global VIA
        real_via = VIA
        VIA = mother
        try:
            mir = mirror_rows(Sister(sis))
        finally:
            VIA = real_via
        st = {Path(r["entry"]).name: r["state"] for r in mir["rows"]}
        chk("① 母倉出新版號 → NEW_VERSION(姊妹倉該重同步)", st.get("CGC_MDLX_Tool_v*.py") == "NEW_VERSION", f"({st.get('CGC_MDLX_Tool_v*.py')})")
        chk("① 規則冊就地改 → CHANGED", st.get("Rules_SSOT_v0100.json") == "CHANGED", f"({st.get('Rules_SSOT_v0100.json')})")
        chk("① 位元相同 → SAME", st.get("Same_SSOT_v0100.json") == "SAME")
        chk("① 只差 CRLF → SAME_EOL(換行不是內容)", st.get("Eol_v0100.py") == "SAME_EOL", f"({st.get('Eol_v0100.py')})")
        chk("① 母倉沒有了 → GONE_IN_MOTHER 且總判 RED", st.get("Gone_v*.py") == "GONE_IN_MOTHER" and mir["state"] == "RED",
            f"({mir['state']})")

        # ② 血統:五個檔各演一個態
        names = ["a.py", "b.py", "c.py", "d.py", "e.py"]
        lineage = [f"functional modules/VRN/engine/{n}" for n in names]
        for rel in lineage:
            for base in (mother, sis):
                (base / rel).write_text(f"# {rel}\n", encoding="utf-8")
        (mother / lineage[0]).write_text("# a\n# 母倉自己的修\n", encoding="utf-8")      # 同步當下母倉就多一段修(記進基準)
        bookp = tmp / "sync_book.json"
        global LINEAGE
        real_lineage = LINEAGE
        LINEAGE = tuple(lineage)
        try:
            rec_dry = record(str(sis), apply=False, book_path=bookp, mother_root=mother)
            chk("record 沒給 --apply 一個位元組都不寫", rec_dry["state"] == "DRY_RUN" and not bookp.exists())
            rec = record(str(sis), note="selftest", apply=True, book_path=bookp, mother_root=mother)
            chk("record --apply 寫同步冊(同步當下兩邊指紋都記)", rec["state"] == "WRITTEN" and bookp.is_file()
                and all("sister_lf_sha256" in f for f in rec["book"]["files"]))
            # 同步之後:b 姊妹倉動、c 母倉動、d 兩邊都動、e 姊妹倉刪
            (sis / lineage[1]).write_text("# b sister v2\n", encoding="utf-8")
            (mother / lineage[2]).write_text("# c mother v2\n", encoding="utf-8")
            (sis / lineage[3]).write_text("# d sister v2\n", encoding="utf-8")
            (mother / lineage[3]).write_text("# d mother v2\n", encoding="utf-8")
            (sis / lineage[4]).unlink()
            # a 的姊妹倉換成 CRLF:內容沒變,不准判成姊妹倉動了
            (sis / lineage[0]).write_bytes((sis / lineage[0]).read_bytes().replace(b"\n", b"\r\n"))
            lin = lineage_rows(Sister(sis), read_book(bookp), mother)
        finally:
            LINEAGE = real_lineage
        ls = {Path(r["path"]).name: r["state"] for r in lin["rows"]}
        chk("② 兩邊都沒動(姊妹倉只換 CRLF)→ IN_SYNC", ls.get("a.py") == "IN_SYNC", f"({ls.get('a.py')})")
        chk("② 姊妹倉又改了 → SISTER_AHEAD(母倉該收回)", ls.get("b.py") == "SISTER_AHEAD", f"({ls.get('b.py')})")
        chk("② 母倉改了 → MOTHER_AHEAD(姊妹倉該收)", ls.get("c.py") == "MOTHER_AHEAD", f"({ls.get('c.py')})")
        chk("② 兩邊都動 → BOTH_CHANGED 且總判 RED", ls.get("d.py") == "BOTH_CHANGED" and lin["state"] == "RED", f"({lin['state']})")
        chk("② 一邊檔不見 → MISSING 並講哪一邊", ls.get("e.py") == "MISSING"
            and next(r for r in lin["rows"] if r["path"].endswith("e.py")).get("side") == "姊妹倉")
        # record 再記一次:舊基準進 history(只增不減)
        LINEAGE = tuple(lineage)
        try:
            (sis / lineage[4]).write_text("# e back\n", encoding="utf-8")
            rec2 = record(str(sis), note="second", apply=True, book_path=bookp, mother_root=mother)
        finally:
            LINEAGE = real_lineage
        chk("record 第二次:舊基準進 history(只增不減)", len(rec2["book"]["history"]) == 1
            and rec2["book"]["history"][0].get("note") == "selftest")

        # NODATA:找不到姊妹倉
        res = check(sister_root=str(tmp / "no_such_sister"), book_path=bookp, mother_root=mother) \
            if find_sister(str(tmp / "no_such_sister")) is None and not os.environ.get("VIA_SISTER_ROOT") else None
        if res is not None and res["verdict"] == "NODATA":
            chk("找不到姊妹倉 → NODATA rc2(量不到不是壞掉)", res["rc"] == 2)
        else:
            chk("找不到姊妹倉 → NODATA rc2(量不到不是壞掉)", True, "(本機有姊妹倉可找,此檢以 find_sister 直驗)")
        chk("沒有同步冊 → 血統 NODATA 並指路 record", lineage_rows(Sister(sis), None, mother)["state"] == "NODATA")

        # --ref 讀法:git 讀,不動工作樹
        gitsis = tmp / "gitsister"
        gitsis.mkdir()
        (gitsis / "f.txt").write_text("one\n", encoding="utf-8")
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        ok_git = all(subprocess.run(c, cwd=gitsis, capture_output=True, env=env).returncode == 0 for c in (
            ["git", "init", "-q"], ["git", "add", "f.txt"], ["git", "commit", "-q", "-m", "c1"]))
        if ok_git:
            (gitsis / "f.txt").write_text("two (未 commit)\n", encoding="utf-8")
            by_ref = Sister(gitsis, "HEAD").read("f.txt")
            chk("--ref 讀 git 版本,不讀工作樹(工作樹改了也不影響)", by_ref == b"one\n", f"({by_ref!r})")
        else:
            chk("--ref 讀 git 版本,不讀工作樹(工作樹改了也不影響)", True, "(本機沒有 git,此檢不適用)")

        # 本支唯讀:真母倉的同步冊與 registry 夾在 check 前後指紋不變
        before = sorted((p.name, p.stat().st_mtime_ns) for p in HERE.glob("*.json"))
        _ = check(sister_root=str(sis), book_path=bookp, mother_root=mother)
        after = sorted((p.name, p.stat().st_mtime_ns) for p in HERE.glob("*.json"))
        chk("check 唯讀:真母倉 registry 夾的冊一個都沒被寫", before == after)
        src = Path(__file__).read_text(encoding="utf-8")
        consent_writes = re.findall(r"environ\[\s*['\"]VIA_(?:NET|SCRAPE)_CONSENT", src)
        chk("同意閘永不代設(原始碼層)", not consent_writes)
        chk("零網路(原始碼不引 urllib/requests/socket)", not re.search(r"^\s*import (urllib|requests|socket)|^\s*from (urllib|requests|socket)", src, re.M))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n_ok = len(ran) - len(fails)
    print(f"  [計] 自測 {len(ran)} 檢 OK {n_ok} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if "--selftest" in a:
        print(f"=== {ENGINE_ID} {VERSION} · 自測(沙盒兩棵假樹;真樹零觸碰)===")
        return selftest()
    verb = next((x for x in a if not x.startswith("-")), "check")

    def opt(name):
        if name in a:
            i = a.index(name)
            return a[i + 1] if i + 1 < len(a) else ""
        return ""
    if verb == "check":
        res = check(opt("--sister"), opt("--ref"))
        if "--json" in a:
            print(json.dumps(res, ensure_ascii=False, indent=1))
        else:
            render(res)
        return res["rc"]
    if verb == "record":
        res = record(opt("--sister"), opt("--ref"), opt("--note"), apply="--apply" in a)
        print(f"  [record] {res.get('state')} · {res.get('path', '')}"
              + ("" if "--apply" in a else "(沒給 --apply:只演不寫)"))
        return 0 if res.get("state") in ("WRITTEN", "DRY_RUN") else 2
    print("  [用法] check [--sister PATH] [--ref REF] [--json] | record --sister PATH [--ref REF] [--note T] --apply | --selftest")
    return 2


if __name__ == "__main__":
    sys.exit(main())
