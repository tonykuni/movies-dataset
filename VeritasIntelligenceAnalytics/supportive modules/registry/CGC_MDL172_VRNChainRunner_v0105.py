#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL172_VRNChainRunner v0105 — VRN 六層鏈實測(側線 2026-09-24 第四段:存證自己寫 ABSENT/NODATA/FAIL 就不准報 ok;批695:紅燈自述——「語法樹讀不出來」要講清楚是哪個檔、多大、blob 對不對 HEAD、哪個 python、錯什麼、那一行長什麼樣;批694:每個節點跑完印一行 [進度] k/N;批686:紅燈要講出為什麼紅;缺件記 ABSENT 不記紅)
v0104→v0105(側線 2026-09-24 第四段;主線批號由併線的手指定 L25):
  全格實跑時本站在側線樹上紅、在 main 的乾淨工作樹上綠——**同一份碼**,紅綠跟著機器上有沒有存證檔走。
  量到的:容器上 VIA_Reports/vrn/matrix/VRN_MATRIX_latest.json 是 ENG083 自己寫的
  `{"state":"ABSENT","why":"庫不在:…vrn_reports.duckdb…"}`;data_evidence() 只問檔在不在,檔在就 ok=True——
  **把一張「庫不在」的存證報成「驗證段有料」**,研報 0 份還掛 ok。⑪ 在有這張存證的機器上必紅(ok 且 0 份),
  在沒有存證檔的乾淨樹上必綠(不在→ok=False 有理由):燈跟著境走,不跟著碼走。
  ① data_evidence(p=None):讀進來先看存證自己的 state——ENG083 只吐 OK/ABSENT/NODATA/FAIL,**不是 OK 就不是 ok**,
     why 用存證自己的 why(前面冠上它的態);state=OK 但研報 0 份也不算 ok(本支 docstring 自己的話:0 列的綠沒有意義);
     存證不是 JSON 物件也講明;舊版存證沒有 state 鍵的照舊看研報數(向後相容)。
  ② 廿五檢 +㉖:四份合成存證(ABSENT / OK 兩份 / OK 零份 / 舊版無 state)逐一餵 data_evidence(p),
     不靠本機 VIA_Reports——這一檢在哪台機器上都同一個答案。⑪ 照舊量真存證(現在兩種境都誠實)。rc/頁/存證格式不動。
v0103→v0104(批695 工作站兩次貼回同兩盞紅,而燈只說「語法樹讀不出來(line 15)」):
  操作員 09-21 兩次貼回 via-vrnrun:SUP_MDL746 RED「語法樹讀不出來(line 15)」、CGC_MDL141 RED「語法樹讀不出來(line 13)」。
  容器把 main 上那兩支拿 3.11/3.12/3.13 三個直譯器 ast.parse 全 OK,兩行都在 docstring 裡——**紅的不是 git 上的內容**。
  那紅的是誰?燈沒講:敲的是哪個檔(尾版解析可能敲到樹上多出來的高版號)、檔多大、內容跟 git 同不同、哪個 python 在讀、
  錯的是什麼、那一行長什麼樣。我開了一段 PS 診斷塊請操作員貼,操作員貼回來的還是 via-vrnrun——**燈自己該講的,不該叫人另外量**(L16 紅燈指路)。
  ① selftest_door 抓到 SyntaxError 時,detail 講:line + 錯訊、檔名、大小、blob 前八碼與 HEAD 比(=HEAD/≠HEAD/不在 HEAD;git 缺=不比)、
     讀它的 python 版本;stdout 另印一行 `[語法樹] …` 全文(含 該行 repr、衝突標記、NUL),表格 150 字截不到的都在這行,Select-String 抓 `語法樹` 就有。
  ② blob 算法=git 的(`blob <len>\0` + 內容 sha1),CRLF 先正規化成 LF 再算(Windows autocrlf 工作樹也能對上 HEAD);raw 與 LF 兩個 id 任一同 HEAD 即「同」。
  ③ fix 欄改成三岔路:=HEAD → 問直譯器(該行/錯訊);≠HEAD → 工作樹檔≠git(git status / checkout -- 檔);不在 HEAD → 樹上多了未追蹤版號(側枝 L25)。
  ④ 廿四檢 +㉕:沙盒壞檔 → 燈講齊六樣、stdout 有 `[語法樹]` 行、run_node 記 RED;本支自己的 blob 算法對得上 git(有 git 才比)。rc/存證/頁不動。
v0102→v0103(批694 操作員三令「卡斷 · 25 個加速器 · 動態進度條及百分比」):
  run 模式每個節點跑完就印 `[進度] k/N <層> <節點> <態> <秒>`(stdout、flush)——啟動器(Invoke-VIAPython/via-vrnrun)照這行畫真百分比,
  44 節點的 V2 不再是幾分鐘的黑箱。層內並行照舊(計數上鎖);plan/--only 不印。輸出多 N 行,rc/存證/頁一字不動。廿四檢不變。
v0101→v0102(批686 工作站兩次貼回同一種眼罩):
  操作員 09-21 兩次貼回 via-vrnrun,SUP_MDL746 與 CGC_MDL141 都是 RED,而「量到什麼」那一格印的是
  `[OK] ⑨ …` 與 `[OK] ⑭ …`——**最後一行**。多檢自測的最後一行幾乎永遠是最後那一檢的 OK,
  真正紅的那一檢被它蓋住;我在批685 還照著那行把根因猜成 ⑭,猜錯了。眼罩是跑器自己戴的(LL105 同族)。
  ① `_note_of()`:rc≠0 時先給 `[FAIL]` 行(最多兩行)再接 `[計]` 行;rc=0 照舊給最後兩行。
  ② Z60:輸出裡有 `ModuleNotFoundError: No module named 'x'` → **ABSENT 並具名缺哪個套件**(缺件≠壞掉 L16;
     與 EngineBus ⑳「需要 <套件>」同律),修法指向 via-rungate --approve-install(裝=操作員的手)。
  ③ 自測檢數改成數的(ran 列表),不再寫死 22(LL332);廿四檢 +㉓㉔。

CGC_MDL172_VRNChainRunner v0101 — VRN 六層鏈實測(批671;批672 接排版規格)
====================================================================
操作員令(批671):「將 VRN 實測完畢」。

與 VDF 那條鏈(CGC_MDL170,批667)對稱,但**鏈表不寫死**:
  VDF 那支我手寫了七站;VRN 這支**直接讀批665 已覆核的六層冊**
  (VIA_VRN_LogicArchitecture_SSOT_v0100.json)——冊上 44 個節點各自帶著
  `family` / `tail` / `role` / `role_kind`,鏈就是那份冊。
  冊改了鏈跟著改,不必回來改這支(L30 一個出處;**手寫第二份鏈表就是第二顆頭**)。

一個結構上的事實,正好回答操作員批670 問的「可同時 / 依序」:
    **層是依序的(L0→L5:後一層吃前一層的產出)**
    **層內是可並行的(同層節點彼此不相依)**
所以 run 就照這個跑:逐層序列、層內並行。這不是效能選擇,是**資料流的形狀**。

第 0 站沿用批667 的兩件(操作員批667 點名):
  加速器  VIA_SuperAccel_Module
  網路    SUP_MDL740_NetUnified 尾版 → VeritasAegisNexus 正典(批402 律)
同意閘 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT **永不代設**;閘沒開=GATED 不是 RED。

誠實態(逐節點):
  GREEN   自測 rc0
  NODATA  rc≠0 但那一支自己說缺料 · 或**逾時**(沒跑完=沒有結論,不是紅燈;批616 律)
          · 或**那支根本沒有自測門**(批671 第二回;先敲門再問話,見 selftest_door)
  GATED   rc4(等閘)
  RED     真的壞
  ABSENT  冊上有、樹上尾版找不到
用法:
  via-vrnchain               → plan(只攤開六層與節點,零動作)
  via-vrnchain run           → **一句到底**:逐層跑 + 落 rich HTML MATRIX + 跳出頁
  via-vrnchain run --fast    → 每節點逾時 60s(快掃;逾時仍記 NODATA 不記紅)
  via-vrnchain run --only L2 → 只跑某一層(層名前綴即可)
  via-vrnchain run --resume  → 只重跑上回沒過的節點
  via-vrnchain --selftest    → 廿六檢(沙盒零網路;檢數用數的)
誠實 rc:0 GREEN · 1 RED · 2 NODATA · 3 ABSENT · 4 GATED
"""
# 批672:v0100 的 _CSS / _JS 在這一版**刪掉**了——頁殼改由 CGC_MDL173 排版規格供應。
#   留著沒人用的那一份 CSS 不是「備份」,是第二份規格;下次有人改它,兩份就開始走鐘。

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

import ast
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
BOOK = HERE / "VIA_VRN_LogicArchitecture_SSOT_v0100.json"
NET_DIR = VIA / "supportive modules" / "network"
REPORTS = VIA / "VIA_Reports" / "vrn_chain"
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
_SELF_FAMILY = Path(__file__).stem.rsplit("_v", 1)[0]

RC_NAME = {0: "GREEN", 1: "RED", 2: "NODATA", 3: "ABSENT", 4: "GATED", 5: "SKIP"}
STATE_ORDER = ("RED", "GATED", "NODATA", "ABSENT", "SKIP", "GREEN")
STATE_STYLE = {"GREEN": "bold green", "RED": "bold red", "NODATA": "yellow",
               "ABSENT": "dim", "GATED": "bold cyan", "SKIP": "dim"}
CONSENT_ENV = "VIA_NET_CONSENT"
SCRAPE_ENV = "VIA_SCRAPE_CONSENT"
DEFAULT_TIMEOUT = 180
FAST_TIMEOUT = 60
POOL = 4                    # 層內並行度。開太大在單機上只是互相搶 CPU,不是更快


def rel(p) -> str:
    try:
        return str(Path(p).relative_to(VIA)).replace("\\", "/")
    except (ValueError, TypeError):
        return str(p)


def newest(folder: Path, pattern: str) -> Path | None:
    try:
        hits = sorted(folder.glob(pattern))
    except OSError:
        return None
    return hits[-1] if hits else None


def stage(layer, name, state, detail="", fix="", secs=None, evidence="") -> dict:
    return {"layer": layer, "name": name, "state": state, "detail": detail,
            "fix": fix, "secs": secs, "evidence": evidence}


# ── 鏈表 = 已覆核的六層冊(不手寫第二份)──────────────────────────────
def load_chain() -> tuple[list, str]:
    """從批665 已覆核的六層冊讀鏈。回 (層序清單, 冊的身分句)。

    冊上每個節點帶 tail(尾版實路徑),所以這支**不需要自己解尾版**——
    解尾版的正主是建冊器,它已經解過了。再解一次就是第二把尺。
    """
    if not BOOK.exists():
        return [], f"冊不在:{rel(BOOK)}"
    try:
        d = json.loads(BOOK.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return [], f"冊讀不開:{str(exc)[:60]}"
    who = (f"{d.get('built_by') or d.get('version')} 建於 "
           f"{d.get('built_at') or d.get('ts')}")
    out = []
    for lname in sorted((d.get("layers") or {})):
        nodes = []
        for n in (d["layers"][lname].get("nodes") or []):
            nodes.append({"family": n.get("family"), "tail": n.get("tail"),
                          "role": n.get("role") or "", "kind": n.get("role_kind") or "",
                          "also": n.get("also_layers") or []})
        out.append({"layer": lname, "nodes": nodes})
    return out, who


# ── 第 0 站:掛載 ───────────────────────────────────────────────────────
def mount_accel() -> dict:
    p = VIA / "supportive modules" / "VIA_SuperAccel_Module.py"
    if not p.exists():
        return stage("L-", "加速器掛載", "ABSENT", "VIA_SuperAccel_Module.py 不在",
                     "樹不完整:git pull", evidence=rel(p))
    if VIA_ACCEL is None:
        return stage("L-", "加速器掛載", "RED", "檔在但本支的加速器橋沒掛上",
                     "看本檔 [VIA:ACCEL-BRIDGE] 段", evidence=rel(p))
    have = [n for n in ("accel_map", "fetch", "celeritas", "activate")
            if hasattr(VIA_ACCEL, n)]
    return stage("L-", "加速器掛載", "GREEN" if len(have) >= 3 else "NODATA",
                 f"可用道 {'·'.join(have)}", "", evidence=rel(p))


def mount_net() -> dict:
    p = newest(NET_DIR, "SUP_MDL740_NetUnified_v*.py")
    if not p:
        return stage("L-", "網路工具掛載", "ABSENT", "SUP_MDL740_NetUnified_v*.py 不在",
                     "樹不完整:git pull", evidence=rel(NET_DIR))
    aegis = "?"
    try:
        spec = importlib.util.spec_from_file_location("vrnchain_net", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules["vrnchain_net"] = m
        spec.loader.exec_module(m)
        ap = m._resolve_aegis_path()
        aegis = rel(Path(ap)) if ap else "(找不到 AegisNexus 正典)"
    except Exception as exc:
        return stage("L-", "網路工具掛載", "RED", f"載入炸了:{str(exc)[:70]}",
                     "先單跑該支 --selftest", evidence=rel(p))
    consent = os.environ.get(CONSENT_ENV, "")
    det = f"{p.name} · 後端 {aegis} · 閘一={consent or '未開'}"
    if consent.upper() != "YES":
        return stage("L-", "網路工具掛載", "GATED",
                     det + " —— **同意閘未開=缺料不是壞掉**;AI 永不代設",
                     f"要觸網才需要:$env:{CONSENT_ENV}='YES'", evidence=rel(p))
    return stage("L-", "網路工具掛載", "GREEN", det, "", evidence=rel(p))


# ── 逐節點跑(層內並行、層間序列)────────────────────────────────────
def _fam_python() -> str:
    root = os.environ.get("VIA_ENV_ROOT", "")
    if root:
        d = Path(root)
        for cand in sorted(d.glob("via_vrn_*")):
            for sub in ("Scripts/python.exe", "Scripts/python3.exe",
                        "python.exe", "bin/python", "bin/python3", "python"):
                if (cand / sub).exists():
                    return str(cand / sub)
    return sys.executable


# ── 自測門探針(批671 第二回;先疑尺不疑樹 L93)────────────────────────
#   第一回我拿 `--selftest` 去問冊上每一支,然後照 rc 判燈。量出來 RED 4。
#   逐支看才知道**四盞裡沒有一盞是真紅**:
#     ENG057/ENG056/ENG052 根本沒有「自測」這扇門——`--selftest` 被它們當成
#     檔名樣式吃進去,然後誠實地回「收件夾無匹配」(rc=1)。那是**我問錯問題**。
#   更傷的是反方向:ENG050 沒有門,`--selftest` 被吃掉後它跑了自己的預設動作、
#   rc=0——於是我給了一盞**假綠**。判錯的紅燈和假綠一樣傷,這一次兩邊同時發生。
#   所以量之前先問一句:**這支到底有沒有這扇門?** 沒有門就不要敲,
#   誠實記 NODATA(量不到),不要拿沒門的牆當紅燈,也不要拿回音當綠燈。
#   走 AST 不走 regex(LL311:寫 regex 去讀 code 永遠會在跳脫上斷)。
_AST_FIX: dict[str, str] = {}   # 檔 → 修法(selftest_door 算好,run_node 放進 fix 欄)


def _blob_id(raw: bytes) -> str:
    """git 的 blob id(`blob <len>\\0` + 內容 sha1)前八碼——跟 `git rev-parse HEAD:<檔>` 直接對。"""
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()[:8]


def _git_blob(p: Path, ref: str) -> str:
    """<ref> 上同一路徑的 blob 前八碼;沒 git / 不在 → ""。只讀,零觸碰樹。"""
    try:
        r = subprocess.run(["git", "rev-parse", "--verify", "-q", f"{ref}:./{p.name}"],
                           capture_output=True, text=True, timeout=10, cwd=str(p.parent))
        return r.stdout.strip()[:8] if r.returncode == 0 else ""
    except Exception:
        return ""


def _head_blob(p: Path) -> str:
    return _git_blob(p, "HEAD")


def _upstream_blob(p: Path) -> tuple[str, str]:
    """(上游 ref 名, blob 前八碼)。上游=@{u};沒設就找 origin/<本地分支名>;再沒有就 origin/main。都沒有 → ("", "")。
    工作站是 `git pull origin <分支>` 拉的,@{u} 常常沒設,但 origin/<分支> 會被順手更新——那才是「容器推上來的內容」。"""
    refs = ["@{u}"]
    try:
        r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True,
                           text=True, timeout=10, cwd=str(p.parent))
        cur = r.stdout.strip()
        if r.returncode == 0 and cur and cur != "HEAD":
            refs.append(f"origin/{cur}")
    except Exception:
        pass
    refs.append("origin/main")
    for ref in refs:
        b = _git_blob(p, ref)
        if b:
            return ref, b
    return "", ""


def _ast_fail_note(p: Path, exc: SyntaxError) -> tuple[str, str, str]:
    """(表格 detail ≤150 字, stdout 全文行, 修法)。批695:紅燈自己講清楚,不叫人另外開檔量。
    工作站實錄:兩支「語法樹讀不出來(line 15 / line 13)」,容器同檔三個直譯器全 OK——
    真相是併了另一條線的同名新版號檔(加/加衝突),衝突標記留在樹上;燈只講 line,誰都猜不到。"""
    try:
        raw = p.read_bytes()
    except OSError:
        raw = b""
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    ln = exc.lineno or 0
    at = repr(lines[ln - 1][:80]) if 0 < ln <= len(lines) else "(超出檔尾)"
    marker = "\n<<<<<<< " in text or text.startswith("<<<<<<< ")
    nul = b"\x00" in raw
    ids = {_blob_id(raw), _blob_id(raw.replace(b"\r\n", b"\n"))}
    head = _head_blob(p)
    up_ref, up = _upstream_blob(p)
    rp = rel(p)
    if marker:
        verdict = "衝突標記 有(加/加併線沒解完,檔裡夾著 <<<<<<< / ======= / >>>>>>>)"
        fix = (f"取上游版再 commit:`git checkout {up_ref or 'origin/<分支>'} -- \"{rp}\"`;"
               "全樹再掃一次 `git grep -l '^<<<<<<< '`(其他帶標記的檔一併取上游版)")
    elif nul:
        verdict = "含 NUL(檔半寫/佔位;OneDrive 常見)"
        fix = f"取上游版:`git checkout {up_ref or 'origin/<分支>'} -- \"{rp}\"`"
    elif up and up in ids:
        verdict = f"blob {up}=上游 {up_ref}(內容同 git → 問直譯器)"
        fix = "內容跟上游一模一樣還讀不出來 → 是直譯器/版本:看 stdout `[語法樹]` 行的錯訊與該行,拿同一支 python 單跑 `python -c \"import ast;ast.parse(open(r'<檔>',encoding='utf-8').read())\"`"
    elif up:
        if head and head in ids:
            verdict = f"blob {_blob_id(raw)}=HEAD ≠上游 {up_ref} {up}(本地 commit 跟上游不同)"
        elif head:
            verdict = f"blob {_blob_id(raw)}≠HEAD {head} ≠上游 {up}(工作樹檔被改過/半寫)"
        else:
            verdict = f"blob {_blob_id(raw)} 不在 HEAD ≠上游 {up}(未追蹤覆蓋)"
        fix = f"取上游版:`git checkout {up_ref} -- \"{rp}\"`(本地 commit 不同就再 commit 一次)"
    elif head and head in ids:
        verdict = f"blob {head}=HEAD(上游 ref 找不到,無法比;內容同本地 git)"
        fix = "`git fetch origin` 後重跑;或拿 stdout `[語法樹]` 行的錯訊看直譯器"
    elif head:
        verdict = f"blob {_blob_id(raw)}≠HEAD {head}(工作樹檔被改過/半寫)"
        fix = f"`git checkout -- \"{rp}\"` 還原成 HEAD 版"
    else:
        verdict = f"blob {_blob_id(raw)} 不在 HEAD(樹上多出來的版號/無 git)"
        fix = "這支不是 git 上的檔:樹上多了未追蹤的版號(側枝 L25)——刪或移走,讓尾版解析敲回 git 上那支"
    pyv = sys.version.split()[0]
    msg = (exc.msg or "").strip()
    detail = f"語法樹讀不出來(line {ln})· {p.name} {len(raw)}B · {verdict.split('(')[0]} · py {pyv} · {msg[:40]}"
    full = (f"[語法樹] {p.name} line {ln} · {msg} · {len(raw)}B · {verdict}"
            f" · HEAD {head or '不在'} · 上游 {(up_ref + ' ' + up) if up else '找不到'}"
            f" · py {pyv} {sys.executable} · 該行 {at} · NUL {'有' if nul else '無'} · 修法 {fix}")
    return detail, full, fix


def selftest_door(p: Path) -> tuple[bool | None, str]:
    """回 (有門?, 為什麼)。None = 語法樹讀不出來(那是另一件事,不是沒門)。"""
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as exc:
        detail, full, fix = _ast_fail_note(p, exc)
        print("  " + full, flush=True)   # 表格 150 字截不到的,這一行全講(Select-String 抓 語法樹)
        _AST_FIX[str(p)] = fix
        return None, detail
    except Exception as exc:  # 讀檔本身壞掉
        return None, f"{type(exc).__name__}: {str(exc)[:60]}"
    # 字面量剛好等於旗標本身:add_argument("--selftest") / "--selftest" in sys.argv /
    #   argv[1] == "--selftest" / {"--selftest": ...} 四種寫法一次收齊。
    # docstring 也是 Constant,但沒有哪份 docstring 會**整份剛好等於**這九個字。
    flag = "--" + "self" + "test"          # L133:別讓這支掃到自己這一行
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and n.value == flag:
            return True, "有自測門"
    return False, "沒有自測門"


# ── 尾版解析(批671 第三回;冊記的是當時的尾版,不是永遠的尾版)────────
#   實錄:我把 ENG059 修成 v0101 之後,鏈量出來還是紅——因為冊上那一行
#   釘著 `..._v0100.py`,鏈照著冊去敲,敲到的是**我剛剛修好的那支的前一版**。
#   尾版律(最新 _vNNNN 為準)在這裡不是偏好,是「你到底量到誰」的問題。
#   作法:照冊找檔,但**用 glob 解析到同名家族的尾版**;冊落後時不偷偷換掉——
#   把「冊 v0100 · 樹 v0101」印在那一格的註記上(冊與樹的落差要看得見,不是補掉)。
_VER = re.compile(r"^(?P<stem>.+?)_v(?P<num>\d{4})(?P<ext>\.py)$")


def resolve_tail(tail: str) -> tuple[Path | None, str]:
    """回 (要敲的檔, 冊樹落差註記)。落差註記為空字串=冊與樹一致。"""
    if not tail:
        return None, ""
    p0 = VIA / tail
    m = _VER.match(Path(tail).name)
    if not m:
        return (p0 if p0.exists() else None), ""
    sibs = sorted(p0.parent.glob(f"{m.group('stem')}_v[0-9][0-9][0-9][0-9].py"))
    if not sibs:
        return (p0 if p0.exists() else None), ""
    newest = sibs[-1]
    if newest.name == p0.name:
        return newest, ""
    return newest, f"【冊落後】冊 {p0.name} · 樹尾版 {newest.name} —— `via-vrnbook build` 重建冊"



# ── 排版規格:向 CGC_MDL173 **整支取用**(批672;L30 一個出處)──────────
#   批669–671 一口氣做了四支會落頁的引擎,四支各自帶一份 CSS。四份幾乎一樣但不是
#   同一份:字級 13/12.5/13 各有各的。操作員說「字小」的那一刻,要改的地方有四個——
#   **規格散在四處就不是規格**。這裡不自備第二份,只呼叫(LL316:抄到函式才算)。
def _spec_mod():
    """回 CGC_MDL173 尾版模組;缺席回 None(缺件要說出來,不偷偷長一份自己的)。"""
    import importlib.util
    cands = sorted(Path(__file__).resolve().parent.glob("CGC_MDL173_MatrixReportSpec_v*.py"))
    if not cands:
        return None
    try:
        sp = importlib.util.spec_from_file_location("via_matrixspec", cands[-1])
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        return m
    except Exception:
        return None


def _note_of(lines: list, rc: int) -> str:
    """批686:「量到什麼」——rc≠0 先給 [FAIL] 行(最多兩行)再接 [計] 行;rc=0 照舊最後兩行。
    最後一行幾乎永遠是最後一檢的 OK,紅的那一檢會被它蓋住(工作站兩次貼回都只看得到 [OK] ⑨/⑭)。"""
    if not lines:
        return f"rc={rc}"
    if rc == 0:
        return " / ".join(lines[-2:])[:180]
    fails = [l for l in lines if l.startswith("[FAIL]")]
    tally = [l for l in lines if l.startswith("[計]")]
    if fails:
        return " / ".join(fails[:2] + tally[-1:])[:260]
    return " / ".join(lines[-2:])[:180]


_MISSING_MOD_RX = re.compile(r"No module named '([^']+)'")


def _missing_module(lines: list) -> str:
    """批686(Z60):輸出裡有 ModuleNotFoundError 就回缺的套件名;沒有回空。"""
    for l in lines:
        m = _MISSING_MOD_RX.search(l)
        if m:
            return m.group(1)
    return ""


def run_node(layer: str, node: dict, timeout: int) -> dict:
    fam = node.get("family") or "?"
    tail = node.get("tail") or ""
    p, lag = resolve_tail(tail)
    if p is not None:
        tail = rel(p)
    if not p or not p.exists():
        return stage(layer, fam, "ABSENT", f"冊上有、樹上找不到:{tail}",
                     "`via-vrnbook build` 重建冊;或 git pull", evidence=tail)
    door, why = selftest_door(p)
    if door is False:
        # **不敲**。敲沒門的牆,回音不是綠也不是紅——是我自己的聲音。
        return stage(layer, fam, "NODATA",
                     f"{why} —— `--selftest` 會被它當檔名/參數吃進去,"
                     "**量不到不是壞掉**(這一格的紅與綠都不作數)",
                     "給該支補 --selftest 門;或在冊上標免測並附理由(L87 豁免必附理由)",
                     0.0, tail)
    if door is None:
        return stage(layer, fam, "RED", why,
                     _AST_FIX.get(str(p)) or "看 stdout `[語法樹]` 行(錯訊 · 該行 · blob 對 HEAD/上游 · 修法)",
                     0.0, tail)
    env = dict(os.environ)
    env.update({"VIA_NO_OPEN": "1", "PYTHONUTF8": "1", "PYTHONWARNINGS": "ignore"})
    t0 = time.time()
    try:
        r = subprocess.run([_fam_python(), str(p), "--selftest"], capture_output=True,
                           text=True, timeout=timeout, stdin=subprocess.DEVNULL,
                           cwd=str(p.parent), env=env)
    except subprocess.TimeoutExpired:
        # 批616 律:**逾時不是紅**。沒跑完=沒有結論,算紅等於編造一個沒量到的結論。
        return stage(layer, fam, "NODATA",
                     f"逾時 {timeout}s —— **沒跑完=沒有結論**,不是紅燈",
                     "單跑看它卡在哪;或 run(不加 --fast)放寬逾時",
                     round(time.time() - t0, 1), tail)
    except Exception as exc:
        return stage(layer, fam, "RED", f"{type(exc).__name__}: {str(exc)[:70]}",
                     "單跑該支 --selftest 看根因", round(time.time() - t0, 1), tail)
    secs = round(time.time() - t0, 1)
    lines = [l.strip() for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()]
    note = _note_of(lines, r.returncode)                 # 批686:紅燈先講 [FAIL] 行
    if lag:
        note = lag + " / " + note
    if r.returncode == 0:
        return stage(layer, fam, "GREEN", note, "", secs, tail)
    _mod = _missing_module(lines)
    if _mod:                                             # 批686(Z60):缺件≠壞掉(L16)
        return stage(layer, fam, "ABSENT",
                     f"缺件 {_mod}(ModuleNotFoundError;缺件≠壞掉 L16)/ " + note[:120],
                     f"裝進家族境=你的手:via-rungate --family vrn --approve-install(或 pip install {_mod})",
                     secs, tail)
    if r.returncode == 4:
        return stage(layer, fam, "GATED", note + " —— 等閘,不是壞掉",
                     f"$env:{CONSENT_ENV}='YES'", secs, tail)
    if r.returncode == 2 or "NODATA" in note or "缺料" in note:
        return stage(layer, fam, "NODATA", note + "(缺料不是壞掉)",
                     "照它點的名補料", secs, tail)
    return stage(layer, fam, "RED", note + f"(rc={r.returncode})",
                 "單跑該支 --selftest 看根因", secs, tail)


# ── 實際數據的驗證舉證(操作員批671 追加)──────────────────────────────
def data_evidence(p: Path | None = None) -> dict:
    """**引擎會跑** 跟 **資料是對的** 是兩件事。這一段量的是後者。

    來源是 ENG083 驗證矩陣的既有存證(零重跑;它已經逐格判過了),
    外加正典七表的實際列數——**一個「全綠」如果庫裡是 0 列,那個綠沒有意義**。

    v0105:存證**自己的態**要算數——ENG083 寫的是 OK/ABSENT/NODATA/FAIL,不是 OK 就不是 ok
    (why 用存證自己的);OK 但 0 份研報也不是 ok。`p` 給自測 ㉖ 餵合成存證(預設=本機那一張)。
    """
    out = {"ok": False, "why": "", "n_reports": 0, "n_cols": 0,
           "tally": {}, "per_col": {}, "rows": [], "db": "", "age": None,
           "tables": []}
    p = Path(p) if p else VIA / "VIA_Reports" / "vrn" / "matrix" / "VRN_MATRIX_latest.json"
    if not p.exists():
        out["why"] = f"驗證矩陣存證不在:{rel(p)};先跑 via-vrnmatrix"
        return out
    try:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        out["why"] = f"存證讀不開:{str(exc)[:60]}"
        return out
    try:
        out["age"] = round((time.time() - p.stat().st_mtime) / 86400.0, 1)
    except OSError:
        pass
    out["evidence"] = rel(p)
    if not isinstance(d, dict):
        out["why"] = f"存證不是 JSON 物件({type(d).__name__}):{rel(p)};重跑 via-vrnmatrix"
        return out
    # v0105:檔在 ≠ 有料。ENG083 自己判過「庫不在/零列/讀壞」,那個判決要照轉,不准蓋成 ok
    st = str(d.get("state") or "").strip().upper()
    if st and st != "OK":
        out["why"] = f"存證態 {st}:{d.get('why') or '(存證沒寫理由)'}"
        return out
    if not d.get("n_reports"):
        out["why"] = (f"存證 0 份研報(state={st or '無'});一個 0 列的綠沒有意義——"
                      f"鏈跑完再跑 via-vrnmatrix")
        return out
    out.update({"ok": True, "n_reports": d.get("n_reports", 0),
                "n_cols": d.get("n_cols", 0), "tally": d.get("tally") or {},
                "per_col": d.get("per_col") or {}, "db": d.get("db", ""),
                "evidence": rel(p)})
    # 逐列舉證:每份研報 × 每欄一格,連同該格的理由一起帶走(L96 舉證要能整份帶走)
    for r_ in (d.get("rows") or []):
        cells = r_.get("cells") or {}
        out["rows"].append({
            "report": r_.get("report"),
            "cells": {k: {"state": (v or {}).get("state") if isinstance(v, dict) else v,
                          "why": (v or {}).get("why", "") if isinstance(v, dict) else ""}
                      for k, v in cells.items()}})
    for h in (d.get("db_heads") or []):
        out["tables"].append({"path": h.get("path"), "rows": h.get("rows"),
                              "why": h.get("why"), "mtime": h.get("mtime")})
    return out


def collect(do_run=False, timeout=DEFAULT_TIMEOUT, only="", resume=False) -> dict:
    t0 = time.time()
    chain, who = load_chain()
    rows = [mount_accel(), mount_net()]
    prev = {}
    if resume:
        lp = REPORTS / "VRNCHAIN_latest.json"
        if lp.exists():
            try:
                for x in (json.loads(lp.read_text(encoding="utf-8")).get("stages") or []):
                    prev[(x.get("layer"), x.get("name"))] = x
            except Exception:
                prev = {}
    _total = sum(len(l_["nodes"]) for l_ in chain)
    _done = [0]
    _lock = threading.Lock()

    def _run_and_report(lname_, n_):
        r_ = run_node(lname_, n_, timeout)
        with _lock:
            _done[0] += 1
            _sec = r_.get("secs")
            print(f"  [進度] {_done[0]}/{_total} {lname_} {str(n_.get('family') or '?')[:32]} {r_.get('state')}" + (f" {_sec}s" if _sec else ""), flush=True)
        return r_

    for lay in chain:
        lname = lay["layer"]
        if only and not lname.startswith(only):
            for n in lay["nodes"]:
                rows.append(stage(lname, n.get("family") or "?", "SKIP",
                                  f"--only {only} 過濾掉", "", evidence=n.get("tail") or ""))
            continue
        if not do_run:
            for n in lay["nodes"]:
                rows.append(stage(lname, n.get("family") or "?", "SKIP",
                                  f"{n.get('role') or ''} · {n.get('kind') or ''}"
                                  " · plan 只攤開零動作", "", evidence=n.get("tail") or ""))
            continue
        todo, keep = [], []
        for n in lay["nodes"]:
            k = (lname, n.get("family") or "?")
            if resume and prev.get(k, {}).get("state") == "GREEN":
                old = dict(prev[k])
                old["detail"] = "上一回已綠,--resume 跳過:" + str(old.get("detail", ""))[:100]
                keep.append(old)
            else:
                todo.append(n)
        # **層內並行**(節點彼此不相依);層與層之間序列(後一層吃前一層的產出)
        if todo:
            with ThreadPoolExecutor(max_workers=POOL) as ex:
                got = list(ex.map(lambda n: _run_and_report(lname, n), todo))
        else:
            got = []
        rows.extend(keep + got)
    tally = {s: sum(1 for r_ in rows if r_["state"] == s) for s in STATE_ORDER}
    rc = (1 if tally["RED"] else (3 if tally["ABSENT"] else
          (4 if tally["GATED"] else (2 if tally["NODATA"] else 0))))
    return {"schema": "VIA.VRNChain.v1", "version": VERSION, "batch": 671,
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
            "host": os.environ.get("COMPUTERNAME") or os.uname().nodename,
            "python": sys.version.split()[0], "family_python": _fam_python(),
            "book": who, "layers": [l["layer"] for l in chain],
            "mode": ("run" if do_run else "plan") + ("+resume" if resume else "")
                    + (f"+only:{only}" if only else ""),
            "timeout": timeout,
            "consent": {CONSENT_ENV: os.environ.get(CONSENT_ENV, ""),
                        SCRAPE_ENV: os.environ.get(SCRAPE_ENV, "")},
            "tally": tally, "rc": rc, "rc_name": RC_NAME[rc],
            "data": data_evidence(),
            "secs": round(time.time() - t0, 1), "stages": rows}


# ── Markdown 舉證(頁上那顆按鍵吐的就是這份;伺服端也吐得出來)────────
def to_markdown(rep: dict) -> str:
    """同一份資料的 MD 版。**頁上按鍵與這支產生的是同一份** —— 兩份會走鐘。

    所以頁上的 JS 不自己拼 MD,它拿的是本函式在產頁時就算好、內嵌進頁裡的字串。
    """
    t = rep["tally"]
    d = rep.get("data") or {}
    L = [f"# VRN 六層鏈 · 實測與驗證舉證報告(批671)", "",
         f"- 產生:{rep['generated']} · 主機 `{rep['host']}` · python {rep['python']}",
         f"- 模式:`{rep['mode']}` · 每節點逾時 {rep['timeout']}s",
         f"- 鏈表出處:**已覆核的六層冊**({rep['book']})——鏈不是手寫的",
         f"- 同意閘:`{CONSENT_ENV}`={rep['consent'][CONSENT_ENV] or '未開'}"
         f"(AI 永不代設)", "",
         "## 一 · 引擎鏈(層依序 · 層內並行)", "",
         f"GREEN {t['GREEN']} · RED {t['RED']} · GATED {t['GATED']} · "
         f"NODATA {t['NODATA']} · ABSENT {t['ABSENT']} · SKIP {t['SKIP']}"
         f" → **{rep['rc_name']}**", "",
         "| 層 | 節點 | 態 | 秒 | 量到什麼 |", "|---|---|---|--:|---|"]
    for r_ in rep["stages"]:
        L.append(f"| {r_['layer']} | {r_['name']} | **{r_['state']}** | "
                 f"{r_.get('secs') or ''} | {str(r_.get('detail'))[:150]} |")
    L += ["", "## 二 · 實際數據的驗證狀況", ""]
    if not d.get("ok"):
        L += [f"> **{d.get('why') or '無存證'}**", ""]
    else:
        L += [f"- 研報 **{d['n_reports']}** 份 × 欄 **{d['n_cols']}**"
              f" · 存證 `{d.get('evidence')}` · 齡 {d.get('age')} 天",
              f"- 庫:`{d.get('db')}`", "",
              "| 格數統計 | " + " | ".join(d["tally"]) + " |",
              "|---|" + "---|" * len(d["tally"]),
              "| 計 | " + " | ".join(str(v) for v in d["tally"].values()) + " |", "",
              "### 逐欄", "", "| 欄 | " + " | ".join(
                  sorted({k for v in d["per_col"].values()
                          if isinstance(v, dict) for k in v})) + " |"]
        keys = sorted({k for v in d["per_col"].values() if isinstance(v, dict) for k in v})
        L.append("|---|" + "---|" * len(keys))
        for col, v in d["per_col"].items():
            if isinstance(v, dict):
                L.append(f"| {col} | " + " | ".join(str(v.get(k, 0)) for k in keys) + " |")
        L += ["", "### 逐列舉證(每份研報 × 每欄)", ""]
        cols = list(d["per_col"].keys())
        L.append("| 研報 | " + " | ".join(cols) + " |")
        L.append("|---|" + "---|" * len(cols))
        for r_ in d["rows"]:
            cells = r_.get("cells") or {}
            L.append(f"| {r_.get('report')} | " + " | ".join(
                str((cells.get(c) or {}).get("state") or "—") for c in cols) + " |")
        if d.get("tables"):
            L += ["", "### 正典表實際列數", "", "| 表/庫 | 列 | 說明 |", "|---|--:|---|"]
            for x in d["tables"]:
                L.append(f"| `{x.get('path')}` | {x.get('rows')} | {x.get('why')} |")
    L += ["", "## 三 · 律", "",
          "- 逾時 = **沒跑完 = 沒有結論**,不是紅燈(批616)",
          "- GATED = 等閘,缺料不是壞掉;同意閘 AI 永不代設",
          "- 「引擎會跑」與「資料是對的」是兩件事 —— 一個全綠如果庫裡 0 列,那個綠沒有意義",
          ""]
    return "\n".join(L)


# ── 主控台(rich;缺 rich 降級但講出來)──────────────────────────────
def _rich(record=False, width=200):
    try:
        from rich.console import Console
        return Console(record=record, width=width), True
    except Exception:
        return None, False


def render(rep: dict) -> bool:
    con, ok = _rich()
    t = rep["tally"]
    d = rep.get("data") or {}
    if not ok:
        print(f"=== VRN 六層鏈 · 批671 v{rep['version']}(rich 缺席,降級)===")
        for r_ in rep["stages"]:
            print(f"  [{r_['state']:<6}] {r_['layer']:<14} {r_['name'][:34]:<34} "
                  f"{str(r_.get('secs') or ''):>6}  {str(r_.get('detail'))[:70]}")
        print(f"  [計] GREEN {t['GREEN']} · RED {t['RED']} · GATED {t['GATED']} · "
              f"NODATA {t['NODATA']} · ABSENT {t['ABSENT']} → {rep['rc_name']}")
        print("  [律] rich 未安裝 → 降級(**不代裝套件**);降級有講出來。")
        return False
    from rich import box
    from rich.panel import Panel
    from rich.table import Table
    con.print(Panel.fit(
        f"[bold]VRN 六層鏈 · 實測與驗證舉證[/bold] · 批671 · v{rep['version']}\n"
        f"鏈表出處:**已覆核的六層冊**({rep['book']})—— 鏈不是手寫的\n"
        f"模式 {rep['mode']} · 逾時 {rep['timeout']}s · 主機 {rep['host']}\n"
        f"同意閘 {CONSENT_ENV}={rep['consent'][CONSENT_ENV] or '未開'}"
        f" [dim](AI 永不代設)[/dim]\n"
        f"[bold green]GREEN {t['GREEN']}[/] · [bold red]RED {t['RED']}[/] · "
        f"[bold cyan]GATED {t['GATED']}[/] · [yellow]NODATA {t['NODATA']}[/] · "
        f"[dim]ABSENT {t['ABSENT']} · SKIP {t['SKIP']}[/] → [bold]{rep['rc_name']}[/]",
        title="VERITAS INTELLIGENCE ANALYTICS · VRN", border_style="cyan"))
    for lname in rep["layers"]:
        sub = [r_ for r_ in rep["stages"] if r_["layer"] == lname]
        if not sub:
            continue
        tb = Table(title=f"{lname}({len(sub)} 節點 · 層內並行)", box=box.SIMPLE_HEAVY,
                   header_style="bold cyan", title_style="bold", pad_edge=False)
        for h in ("節點", "態", "秒", "量到什麼"):
            tb.add_column(h, overflow="fold")
        for r_ in sub:
            tb.add_row(r_["name"], f"[{STATE_STYLE.get(r_['state'], '')}]{r_['state']}[/]",
                       str(r_.get("secs") or ""), str(r_.get("detail"))[:150])
        con.print(tb)
    if d.get("ok"):
        tb = Table(title=f"實際數據驗證:研報 {d['n_reports']} × 欄 {d['n_cols']}"
                         f"(存證齡 {d.get('age')} 天)",
                   box=box.SIMPLE_HEAVY, header_style="bold cyan", title_style="bold")
        keys = sorted({k for v in d["per_col"].values() if isinstance(v, dict) for k in v})
        tb.add_column("欄")
        for k in keys:
            tb.add_column(k)
        for col, v in d["per_col"].items():
            if isinstance(v, dict):
                tb.add_row(col, *[str(v.get(k, 0)) for k in keys])
        con.print(tb)
    else:
        con.print(f"[yellow]實際數據驗證:{d.get('why')}[/]")
    return True


# ── 同一頁:引擎鏈 + 數據驗證 + 逐列舉證 + MD/JSON 按鍵 ──────────────



def write_html(rep: dict, out: Path | None = None) -> Path:
    """同一頁:引擎鏈 + 數據驗證 + 逐列舉證,頁上三顆鍵轉 MD / JSON。

    頁上的 MD **不是 JS 現拼的**,是本支產頁時就算好內嵌進去的同一份
    (`to_markdown()`)——JS 自己拼一份就是第二顆頭,而且兩份一定會走鐘。
    零 CDN 零外連;JS 全內嵌;`file://` 直開可用。
    """
    out = out or (REPORTS / "VIA_VRN_Chain_Evidence_v0100.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    esc = (lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    t = rep["tally"]
    d = rep.get("data") or {}
    md = to_markdown(rep)
    M = _spec_mod()
    if M is None:
        print("  [NODATA] CGC_MDL173 排版規格缺席 → 不落頁(不自備第二份 CSS)")
        return out
    h = ["<h2>一 · 引擎鏈(層依序 · 層內並行)</h2>"]
    for lname in rep["layers"]:
        sub = [r_ for r_ in rep["stages"] if r_["layer"] == lname]
        if not sub:
            continue
        h.append(f"<h3>{esc(lname)} · {len(sub)} 節點</h3>"
                 "<div class='mwrap'><table class='m'><thead>"
                 "<tr><th>節點</th><th>態</th><th>秒</th><th>量到什麼</th>"
                 "<th>下一步</th><th>出處</th></tr></thead><tbody>")
        for r_ in sub:
            h.append(f"<tr><td>{esc(r_['name'])}</td>"
                     f"<td class='c s-{esc(r_['state'])}'>{esc(r_['state'])}</td>"
                     f"<td class='n'>{esc(r_.get('secs') or '')}</td>"
                     f"<td>{esc(r_.get('detail'))}</td><td>{esc(r_.get('fix'))}</td>"
                     f"<td>{esc(r_.get('evidence'))}</td></tr>")
        h.append("</tbody></table></div>")
    h.append("<h2>二 · 實際數據的驗證狀況</h2>")
    if not d.get("ok"):
        h.append(f"<p class='NODATA'>{esc(d.get('why') or '無存證')}</p>")
    else:
        h.append(f"<div class='sub'>研報 <b>{d['n_reports']}</b> 份 × 欄 <b>{d['n_cols']}</b>"
                 f" · 存證 {esc(d.get('evidence'))} · 齡 {d.get('age')} 天<br>"
                 f"庫 {esc(d.get('db'))}</div>")
        h.append("<div class='mwrap'><table class='m'><thead><tr><th>格數統計</th>"
                 + "".join(f"<th>{esc(k)}</th>" for k in d["tally"]) + "</tr></thead>"
                 "<tbody><tr><td>計</td>"
                 + "".join(f"<td class='n s-{esc(k)}'>{esc(v)}</td>"
                           for k, v in d["tally"].items())
                 + "</tr></tbody></table></div>")
        keys = sorted({k for v in d["per_col"].values() if isinstance(v, dict) for k in v})
        h.append("<h3>逐欄</h3><div class='mwrap'><table class='m'><thead><tr><th>欄</th>"
                 + "".join(f"<th>{esc(k)}</th>" for k in keys) + "</tr></thead><tbody>")
        for col, v in d["per_col"].items():
            if isinstance(v, dict):
                h.append(f"<tr><td>{esc(col)}</td>" + "".join(
                    f"<td class='n s-{esc(k)}'>{esc(v.get(k, 0))}</td>" for k in keys) + "</tr>")
        h.append("</tbody></table></div>")
        if d.get("tables"):
            h.append("<h3>正典表實際列數</h3><div class='mwrap'><table class='m'><thead>"
                     "<tr><th>表/庫</th><th>列</th><th>說明</th><th>改動時間</th>"
                     "</tr></thead><tbody>")
            for x in d["tables"]:
                h.append(f"<tr><td>{esc(x.get('path'))}</td>"
                         f"<td class='n'>{esc(x.get('rows'))}</td>"
                         f"<td>{esc(x.get('why'))}</td><td>{esc(x.get('mtime'))}</td></tr>")
            h.append("</tbody></table></div>")
        cols = list(d["per_col"].keys())
        h.append(f"<h2>三 · 逐列舉證({len(d['rows'])} 份研報 × {len(cols)} 欄)</h2>"
                 "<div class='mwrap'><table class='m'><thead><tr><th>研報</th>"
                 + "".join(f"<th>{esc(c)}</th>" for c in cols) + "</tr></thead><tbody>")
        for r_ in d["rows"]:
            cells = r_.get("cells") or {}
            tds = []
            for c in cols:
                cc = cells.get(c) or {}
                st = str(cc.get("state") or "—")
                why = str(cc.get("why") or "")
                tds.append(f"<td class='c s-{esc(st)}' title='{esc(why)}'>{esc(st)}"
                           + (f"<br><span class='sub'>{esc(why[:60])}</span>" if why else "")
                           + "</td>")
            h.append(f"<tr><td>{esc(r_.get('report'))}</td>" + "".join(tds) + "</tr>")
        h.append("</tbody></table></div>")
    law = ("逾時 = <b>沒跑完 = 沒有結論</b>,不是紅燈(批616)。<br>"
           "沒有自測門的支**不敲**——回音不是綠也不是紅,是自己的聲音(批671 LL317)。<br>"
           "GATED = 等閘,缺料不是壞掉;同意閘 AI 永不代設。<br>"
           "「引擎會跑」與「資料是對的」是兩件事 —— "
           "<b>一個全綠如果庫裡 0 列,那個綠沒有意義</b>。")
    kpis = [{"label": k, "value": t[k], "state": k}
            for k in ("GREEN", "RED", "GATED", "NODATA", "ABSENT")]
    kpis.append({"label": "總判", "value": rep["rc_name"], "state": rep["rc_name"]})
    M.page_html("".join(h), title="VRN 六層鏈 · 實測與驗證舉證報告 · 批671",
                subtitle=(f"產生 {rep['generated']} · 主機 {rep['host']} · "
                          f"python {rep['python']} · 模式 {rep['mode']} · 逾時 {rep['timeout']}s"
                          f" | 鏈表出處:已覆核的六層冊({rep['book']})—— 鏈不是手寫的"
                          f" | 同意閘 {CONSENT_ENV}="
                          f"{rep['consent'][CONSENT_ENV] or '未開'}(AI 永不代設)"),
                md=md, payload=rep, kpis=kpis, law=law, out=out)
    return out


def write_log(rep: dict) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    body = json.dumps(rep, ensure_ascii=False, indent=1)
    (REPORTS / f"VRNCHAIN_{ts}.json").write_text(body, encoding="utf-8")
    (REPORTS / "VRNCHAIN_latest.json").write_text(body, encoding="utf-8")
    (REPORTS / "VRNCHAIN_latest.md").write_text(to_markdown(rep), encoding="utf-8")
    t = rep["tally"]
    with (REPORTS / "VRNCHAIN_LEDGER.tsv").open("a", encoding="utf-8") as f:
        f.write(f"{rep['generated']}\t{rep['mode']}\t{rep['rc_name']}\tGREEN={t['GREEN']}"
                f"\tRED={t['RED']}\tGATED={t['GATED']}\tNODATA={t['NODATA']}"
                f"\tABSENT={t['ABSENT']}\tsecs={rep['secs']}\n")
    return REPORTS / "VRNCHAIN_latest.json"


# ── 自測十九檢(沙盒零網路)──────────────────────────────────────────
def selftest() -> int:
    import tempfile
    t0 = time.time()
    fails = []

    ran = []                               # 批686:檢數用數的,不寫死(LL332)

    def chk(name, cond, note=""):
        ran.append(name)
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    rep = collect(do_run=False)            # plan:零動作
    rows = rep["stages"]
    chain, who = load_chain()
    # ① 鏈表**真的來自冊**,不是手寫的(手寫第二份就是第二顆頭)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest(")[0]
    hard = re.findall(r"VRN_ENG\d{3}_[A-Za-z]+", body)
    chk("鏈表來自冊,不手寫節點",
        len(chain) == 6 and "VIA_VRN_LogicArchitecture" in body and not hard,
        f"(層 {len(chain)} · 本體寫死節點 {len(hard)})")
    # ② 六層齊、層序固定(L0→L5 是資料流不是排版)
    chk("六層齊且依序", [c["layer"] for c in chain] == sorted(c["layer"] for c in chain)
        and len(chain) == 6, f"({[c['layer'][:3] for c in chain]})")
    # ③ 每個節點都有尾版路徑(冊上沒路徑=鏈跑不動)
    noタ = [n["family"] for c in chain for n in c["nodes"] if not n.get("tail")]
    chk("節點逐個有尾版路徑", not noタ, f"(缺 {noタ[:3]})")
    # ④ 燈號只有六種
    bad = [r_["state"] for r_ in rows if r_["state"] not in STATE_ORDER]
    chk("燈號只有六種(誠實態)", not bad, f"(越界 {bad[:3]})")
    # ⑤ 合計=逐列
    chk("合計=逐列", sum(rep["tally"].values()) == len(rows),
        f"({sum(rep['tally'].values())} vs {len(rows)})")
    # ⑥ plan 零動作:一個子行程都不起
    chain_rows = [r_ for r_ in rows if r_["layer"].startswith("L") and r_["layer"] != "L-"]
    chk("plan 零動作", all(r_["state"] in ("SKIP", "ABSENT") for r_ in chain_rows)
        and all(r_.get("secs") is None for r_ in chain_rows), f"({len(chain_rows)} 節點)")
    # ⑦ 同意閘只讀不設(原始碼層咬死)
    w = re.findall(r"environ\s*\[\s*['\"]VIA_(?:NET|SCRAPE)_CONSENT['\"]\s*\]\s*=", src)
    w += re.findall(r"environ\.setdefault\(\s*['\"]VIA_(?:NET|SCRAPE)_CONSENT", src)
    chk("同意閘永不代設(原始碼層)", not w, f"(寫入點 {len(w)})")
    # ⑧ 閘沒開 → 網路站 GATED 不是 RED
    netr = next((r_ for r_ in rows if "網路工具" in r_["name"]), None)
    if os.environ.get(CONSENT_ENV, "").upper() != "YES":
        chk("閘未開=GATED 不是 RED", netr and netr["state"] in ("GATED", "ABSENT"),
            f"({netr['state'] if netr else '?'})")
    else:
        chk("閘未開=GATED 不是 RED", True, "(本境閘已開,此檢不適用)")
    # ⑨ 逾時記 NODATA 不記紅(批616;拿假引擎咬)
    with tempfile.TemporaryDirectory() as td:
        slow = Path(td) / "slow_v0100.py"
        # 批671 第二回:假引擎**必須有門**,否則探針先攔下來、逾時那條路根本沒走到——
        #   那就是一個永遠為真的負向測試(批670 已經踩過一次)。
        slow.write_text('import sys, time\nif "--selftest" in sys.argv:\n    time.sleep(30)\n', encoding="utf-8")
        got = run_node("L9_試", {"family": "slow", "tail": str(slow.relative_to(VIA))
                                 if str(slow).startswith(str(VIA)) else ""}, 1)
        # tail 不在 VIA 底下時會走 ABSENT,那也是誠實;兩種都不可以是 RED
        chk("逾時/不在 一律不記紅", got["state"] in ("NODATA", "ABSENT"), f"({got['state']})")
    # ⑩ 真跑一個**必綠**的假引擎,確認 GREEN 路徑通
    with tempfile.TemporaryDirectory() as td:
        d2 = VIA / "VIA_Reports" / "_vrnchain_probe"
        d2.mkdir(parents=True, exist_ok=True)
        ok_py = d2 / "ok_v0100.py"
        # 沒帶旗標時刻意回 9:這樣「綠」只可能來自我真的把 --selftest 遞進去了,
        #   不可能來自它跑了自己的預設動作(批671 的假綠就是這樣長出來的)。
        ok_py.write_text('import sys\nif "--selftest" in sys.argv:\n    print("[計] 假引擎 OK")\n    sys.exit(0)\nsys.exit(9)\n', encoding="utf-8")
        try:
            got2 = run_node("L9_試", {"family": "ok", "tail": rel(ok_py)}, 30)
            chk("GREEN 路徑通", got2["state"] == "GREEN" and got2["secs"] is not None,
                f"({got2['state']})")
        finally:
            try:
                ok_py.unlink()
                d2.rmdir()
            except OSError:
                pass
    # ⑪ 數據驗證段:有存證就要帶得出研報數與逐列;沒存證要誠實說為什麼
    d = rep["data"]
    chk("數據驗證段誠實",
        (d["ok"] and d["n_reports"] > 0 and len(d["rows"]) == d["n_reports"])
        or (not d["ok"] and len(str(d["why"])) > 8),
        f"(ok={d['ok']} · 研報 {d['n_reports']} · 逐列 {len(d['rows'])})")
    # ⑫ **引擎綠 ≠ 資料對**:兩段必須分開統計,不准互相頂替
    chk("引擎鏈與數據驗證分兩段統計",
        "data" in rep and "tally" in rep and "tally" in rep["data"]
        and rep["tally"] is not rep["data"].get("tally"),
        "(一個全綠如果庫裡 0 列,那個綠沒有意義)")
    # ⑬ MD 與頁上按鍵吐的是**同一份**(JS 不自己拼)
    md = to_markdown(rep)
    with tempfile.TemporaryDirectory() as td:
        p = write_html(rep, Path(td) / "e.html")
        html = p.read_text(encoding="utf-8")
        # 批672:頁殼換成 CGC_MDL173 排版規格,鍵的名字跟著規格走(vmd/vjson/vcopy)。
        #   咬的還是同一件事:**頁上那份 MD 就是 to_markdown 產的那一份**,JS 不自己拼。
        chk("頁上 MD = to_markdown 同一份(JS 不自己拼)",
            json.dumps(md, ensure_ascii=False) in html
            and "const VIA_MD=" in html and "function vdl(" in html,
            f"(MD {len(md)} 字)")
        # ⑭ 三顆鍵都在,而且零外連、零外部 script src
        head = html.split("</head>")[0]
        chk("三顆鍵在位且零外連",
            all(k in html for k in ("vmd()", "vjson()", "vcopy()"))
            and "http://" not in head and "https://" not in head
            and "<script src" not in html and "cdn.jsdelivr" not in html,
            f"({len(html)} 字)")
        # ⑮ 逐列舉證真的在頁上(不是只有摘要)
        n_rep = d["n_reports"] if d["ok"] else 0
        chk("逐列舉證在同一頁",
            (not n_rep) or (html.count("<tr>") >= n_rep), f"(研報 {n_rep} · tr {html.count('<tr>')})")
    # ⑯ MD 結構齊(三段標題 + 表頭)
    chk("MD 三段齊", all(s in md for s in ("## 一 · 引擎鏈", "## 二 · 實際數據",
                                           "## 三 · 律")), "")
    # ⑰ 存證四件(JSON 時間戳 / latest / MD / 台帳 append-only)
    with tempfile.TemporaryDirectory() as td:
        global REPORTS
        keep, REPORTS = REPORTS, Path(td)
        try:
            lp = write_log(rep)
            write_log(rep)
            led = (Path(td) / "VRNCHAIN_LEDGER.tsv").read_text(encoding="utf-8")
            chk("存證四件 + 台帳 append-only",
                lp.exists() and (Path(td) / "VRNCHAIN_latest.md").exists()
                and len(list(Path(td).glob("VRNCHAIN_2*.json"))) >= 1
                and led.count("\n") == 2, f"(台帳 {led.count(chr(10))} 行)")
        finally:
            REPORTS = keep
    # ⑱ --only 過濾:非該層一律 SKIP,不是偷偷不列
    rep2 = collect(do_run=False, only="L2")
    off = [r_ for r_ in rep2["stages"] if r_["layer"].startswith("L") and r_["layer"] != "L-"
           and not r_["layer"].startswith("L2")]
    chk("--only 過濾掉的仍具名列出(不是偷偷消失)",
        bool(off) and all(r_["state"] == "SKIP" and "過濾" in r_["detail"] for r_ in off),
        f"(非 L2 節點 {len(off)} 個全 SKIP)")
    # ⑲ rc 與燈一致
    t = rep["tally"]
    want = (1 if t["RED"] else (3 if t["ABSENT"] else
            (4 if t["GATED"] else (2 if t["NODATA"] else 0))))
    chk("rc 與燈一致", rep["rc"] == want, f"(rc={rep['rc']} 應 {want})")
    # ⑳ 自測門探針兩個方向都要準:有門的說有,沒門的說沒有。
    #   拿本支自己咬「有門」(它確實有 --selftest),拿一支沙盒假檔咬「沒門」。
    _me = Path(__file__)
    d_yes, _ = selftest_door(_me)
    _d3 = VIA / "VIA_Reports" / "_vrnchain_probe"
    _d3.mkdir(parents=True, exist_ok=True)
    _sb = _d3 / "no_door_v0100.py"
    # 這支 rc=0 —— **假綠那個方向**就靠它咬:沒門卻回 0,絕不可以被記成 GREEN。
    _sb.write_text("import sys\nprint('我沒有自測門,我只是跑了我的預設動作')\nsys.exit(0)\n",
                   encoding="utf-8")
    try:
        d_no, _ = selftest_door(_sb)
        chk("自測門探針兩向皆準(有門說有 · 沒門說沒有)",
            d_yes is True and d_no is False, f"(本支={d_yes} · 沙盒假檔={d_no})")
        # ㉑ 沒門的支**不准敲**,而且不准記成綠也不准記成紅——只能是 NODATA。
        #   批671 第一回實錄:ENG057/056/052 沒門被記成 RED(假紅),
        #   ENG050 沒門卻因為跑了預設動作 rc=0 被記成 GREEN(假綠)。兩個方向同時錯。
        _g = run_node("L9_試", {"family": "no_door", "tail": rel(_sb)}, 30)
        chk("沒門的支記 NODATA(rc=0 也不准記綠)",
            _g["state"] == "NODATA" and _g["secs"] == 0.0, f"({_g['state']})")
    finally:
        try:
            _sb.unlink()
            _d3.rmdir()
        except OSError:
            pass
    # ㉒ 冊釘著舊版號時,要敲的是**樹上的尾版**,而且落差要印出來不是吞掉。
    #   批671 實錄:ENG059 修成 v0101,鏈照冊敲 v0100,於是「修好的那支」量出來還是紅。
    _d4 = VIA / "VIA_Reports" / "_vrnchain_probe"
    _d4.mkdir(parents=True, exist_ok=True)
    _old = _d4 / "tailprobe_v0100.py"
    _new = _d4 / "tailprobe_v0101.py"
    # 舊版:有門但**必敗**;新版:有門且必過。敲錯人就會紅,騙不過去。
    _old.write_text('import sys\nif "--selftest" in sys.argv:\n    sys.exit(1)\n', encoding="utf-8")
    _new.write_text('import sys\nif "--selftest" in sys.argv:\n'
                    '    print("[計] 尾版假引擎 OK")\n    sys.exit(0)\n', encoding="utf-8")
    try:
        _g4 = run_node("L9_試", {"family": "tailprobe", "tail": rel(_old)}, 30)
        chk("冊釘舊版號 → 敲樹上尾版,且落差印在註記上",
            _g4["state"] == "GREEN" and "v0101" in _g4.get("evidence", "")
            and "冊落後" in _g4.get("detail", ""),
            f"({_g4['state']} · {_g4.get('evidence','')[-12:]})")
    finally:
        for _f in (_old, _new):
            try:
                _f.unlink()
            except OSError:
                pass
        try:
            _d4.rmdir()
        except OSError:
            pass
    # ㉓ 批686:紅燈要講出為什麼紅——多檢自測 rc≠0 時「量到什麼」先給 [FAIL] 行再給 [計] 行,
    #   不是最後一行(最後一行幾乎永遠是最後一檢的 OK;工作站兩次貼回都被它蓋住)。
    # ㉔ 批686(Z60):ModuleNotFoundError → ABSENT 並具名套件,不記 RED(缺件≠壞掉 L16)。
    _d5 = VIA / "VIA_Reports" / "_vrnchain_probe"
    _d5.mkdir(parents=True, exist_ok=True)
    _redp = _d5 / "redprobe_v0100.py"
    _modp = _d5 / "modprobe_v0100.py"
    _redp.write_text('import sys\nif "--selftest" in sys.argv:\n'
                     '    print("  [OK] ① 第一檢過")\n    print("  [FAIL] ② 第二檢壞了(這才是根因)")\n'
                     '    print("  [OK] ③ 最後一檢過")\n    print("  [計] 三檢 OK 2 · FAIL 1")\n    sys.exit(1)\n',
                     encoding="utf-8")
    _modp.write_text('import sys\nif "--selftest" in sys.argv:\n'
                     '    import no_such_pkg_b686\n    sys.exit(0)\n', encoding="utf-8")
    try:
        _g5 = run_node("L9_試", {"family": "redprobe", "tail": rel(_redp)}, 30)
        chk("rc≠0 的量到什麼=先 [FAIL] 行再 [計] 行,不是最後一行的 [OK]",
            _g5["state"] == "RED" and _g5["detail"].startswith("[FAIL] ② 第二檢壞了")
            and "[計] 三檢 OK 2 · FAIL 1" in _g5["detail"] and "③ 最後一檢過" not in _g5["detail"],
            f"({_g5['state']} · {_g5['detail'][:60]})")
        _g6 = run_node("L9_試", {"family": "modprobe", "tail": rel(_modp)}, 30)
        chk("ModuleNotFoundError → ABSENT 並具名套件(缺件≠壞掉;裝=操作員的手)",
            _g6["state"] == "ABSENT" and "no_such_pkg_b686" in _g6["detail"]
            and "approve-install" in _g6.get("fix", ""),
            f"({_g6['state']} · {_g6['detail'][:50]})")
    finally:
        for _f in (_redp, _modp):
            try:
                _f.unlink()
            except OSError:
                pass
        try:
            _d5.rmdir()
        except OSError:
            pass
    # ㉕ 批695:語法樹讀不出來的燈要自己講齊——檔·大小·blob 對 HEAD·python·錯什麼·那一行。
    #   工作站兩次貼回「語法樹讀不出來(line 15)」,容器同檔三個直譯器全 OK;燈不講是誰、
    #   內容同不同 git,就只能叫人另外開檔量——那是燈的失職,不是操作員的。
    import contextlib
    import io
    _d6 = VIA / "VIA_Reports" / "_vrnchain_probe"
    _d6.mkdir(parents=True, exist_ok=True)
    _bad = _d6 / "astprobe_v0100.py"
    _bad.write_text("import sys\ndef broken(:\n    pass\n", encoding="utf-8")
    try:
        _buf = io.StringIO()
        with contextlib.redirect_stdout(_buf):
            _door6, _why6 = selftest_door(_bad)
            _g6 = run_node("L9_試", {"family": "astprobe", "tail": rel(_bad)}, 30)
        _out6 = _buf.getvalue()
        _pyv = sys.version.split()[0]
        chk("語法樹讀不出來要講齊(line·檔·大小·blob 對 HEAD/上游·python·錯訊;stdout [語法樹] 行含該行/NUL/修法;記 RED)",
            _door6 is None and "語法樹讀不出來(line 2)" in _why6 and "astprobe_v0100.py" in _why6
            and "B · blob " in _why6 and f"py {_pyv}" in _why6
            and "[語法樹] astprobe_v0100.py line 2" in _out6 and "該行 'def broken(:'" in _out6
            and "NUL 無" in _out6
            and "修法" in _out6
            and _g6["state"] == "RED" and "blob" in _g6["detail"] and "側枝 L25" in _g6.get("fix", ""),
            f"({_g6['state']} · {_why6[:60]})")
        _mk = _d6 / "markerprobe_v0100.py"
        _mk.write_text("<<<<<<< HEAD\nX = 1\n=======\nX = 2\n>>>>>>> theirs\n", encoding="utf-8")
        _buf2 = io.StringIO()
        with contextlib.redirect_stdout(_buf2):
            _g7 = run_node("L9_試", {"family": "markerprobe", "tail": rel(_mk)}, 30)
        _mk.unlink()
        chk("衝突標記留在檔裡 → 燈說「衝突標記 有」並指「取上游版」(工作站兩盞紅的真相,不是 line 幾)",
            _g7["state"] == "RED" and "衝突標記 有" in _g7["detail"] and "git checkout" in _g7.get("fix", "")
            and "[語法樹] markerprobe_v0100.py" in _buf2.getvalue(),
            f"({_g7['state']} · {_g7['detail'][:70]})")
        _hb = _head_blob(_me)
        if _hb:
            _rawme = _me.read_bytes()
            chk("blob 算法對得上 git(本支 HEAD blob = 自算 blob;CRLF 先正規化)",
                _hb in {_blob_id(_rawme), _blob_id(_rawme.replace(b"\r\n", b"\n"))},
                f"(HEAD {_hb} · 自算 {_blob_id(_rawme)})")
        else:
            chk("blob 算法對得上 git(本支 HEAD blob = 自算 blob;CRLF 先正規化)", True,
                "(本支不在 HEAD 或無 git,此檢不適用——新版號未 commit 前必然如此)")
    finally:
        try:
            _bad.unlink()
            _d6.rmdir()
        except OSError:
            pass
    # ㉖ 側線 2026-09-24 第四段:存證自己的態要算數。四份合成存證,不靠本機 VIA_Reports——
    #   v0104 的 ⑪ 量的是本機那一張,所以在有「ABSENT 存證」的機器上紅、在乾淨樹上綠(燈跟著境走)。
    _ev_cases = {
        "absent": {"state": "ABSENT", "why": "庫不在:合成_vrn_reports.duckdb"},
        "ok2": {"state": "OK", "n_reports": 2, "n_cols": 3, "tally": {"GREEN": 6}, "db": "合成.duckdb",
                "rows": [{"report": "a.pdf", "cells": {"eps": {"state": "GREEN", "why": "對得上"}}},
                         {"report": "b.pdf", "cells": {"eps": "GREEN"}}]},
        "ok0": {"state": "OK", "n_reports": 0, "rows": []},
        "legacy": {"n_reports": 1, "rows": [{"report": "legacy.pdf", "cells": {}}]},
        "notobj": [1, 2, 3],
    }
    _ev_got = {}
    with tempfile.TemporaryDirectory() as td:
        for _k, _v in _ev_cases.items():
            _evp = Path(td) / f"{_k}.json"
            _evp.write_text(json.dumps(_v, ensure_ascii=False), encoding="utf-8")
            _ev_got[_k] = data_evidence(_evp)
    _a, _g, _z, _l, _n = (_ev_got[k] for k in ("absent", "ok2", "ok0", "legacy", "notobj"))
    chk("存證自己的態算數(ABSENT/零份/非物件 不報 ok 且講理由;OK 兩份照帶逐列;舊版無 state 看研報數)",
        (not _a["ok"] and "ABSENT" in _a["why"] and "庫不在" in _a["why"])
        and (_g["ok"] and _g["n_reports"] == 2 and len(_g["rows"]) == 2
             and _g["rows"][0]["cells"]["eps"]["state"] == "GREEN")
        and (not _z["ok"] and "0 份" in _z["why"])
        and (_l["ok"] and _l["n_reports"] == 1 and len(_l["rows"]) == 1)
        and (not _n["ok"] and "不是 JSON 物件" in _n["why"]),
        f"(ABSENT→{_a['ok']} · OK2→{_g['ok']}/{_g['n_reports']} · OK0→{_z['ok']} · "
        f"舊→{_l['ok']} · 非物件→{_n['ok']})")
    n_ok = len(ran) - len(fails)
    print(f"  [計] 廿六檢({len(ran)} 檢) OK {n_ok} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        print(f"=== VRN 六層鏈 v{VERSION} · 廿六檢(沙盒零網路)===")
        return selftest()
    verb = next((x for x in a if not x.startswith("-")), "plan")
    if verb not in ("plan", "run", "html"):
        print(f"  [用法] plan | run [--fast|--only LN|--resume] | html(收到 {verb!r})")
        return 2
    only = ""
    if "--only" in a:
        i = a.index("--only")
        if i + 1 < len(a):
            only = a[i + 1]
    timeout = FAST_TIMEOUT if "--fast" in a else DEFAULT_TIMEOUT
    print(f"=== VRN 六層鏈 · {verb}{'+fast' if '--fast' in a else ''}"
          f"{'+resume' if '--resume' in a else ''}{('+only:' + only) if only else ''} ===")
    rep = collect(do_run=(verb != "plan"), timeout=timeout, only=only,
                  resume="--resume" in a)
    render(rep)
    lp = write_log(rep)
    if verb in ("run", "html"):
        p = write_html(rep)
        print(f"\n  [頁] {rel(p)}(同一頁:引擎鏈 + 數據驗證 + 逐列舉證;"
              f"頁上三顆鍵轉 MD / JSON;零 CDN 零外連,file:// 直開)")
        if not os.environ.get("VIA_NO_OPEN"):
            try:
                import webbrowser
                webbrowser.open(p.as_uri())
            except Exception:
                pass
    print(f"  [紀錄] {rel(lp)} + VRNCHAIN_latest.md + VRNCHAIN_<時間戳>.json + LEDGER.tsv")
    if rep["rc"] == 4:
        print(f"  [律] GATED≠壞掉:要觸網的在等同意閘。$env:{CONSENT_ENV}='YES' 再 "
              f"`via-vrnchain run --resume` —— **AI 永不代設**。")
    print("  [律] 「引擎會跑」與「資料是對的」是兩件事:上表第一段是引擎,"
          "第二三段才是資料。**一個全綠如果庫裡 0 列,那個綠沒有意義。**")
    return rep["rc"]


if __name__ == "__main__":
    sys.exit(main())
