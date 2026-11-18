#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL283_CardMatrixFeedback v0101 — 薄尾(v0100 一字不動):成功鎖 · 每次更新給動作主力 AI 的回饋 · 本機免費工具紀錄。

操作員 2026-11-17:「燈號全部要用白字 · 每次更新狀態回饋給動作主力 CLAUDE/CHATGPT · 鎖定成功 · 修正其他燈號項目 · LOGGING LOCAL FREE TOOLS APPLIED」。

本版加的(v0100 的兩段篩選、對帳、頁面照舊;燈的白字在模板鎖冊 v0101,本檔不帶色值):
  ① 成功鎖(成功不可丟失)
     · 檔案層:讀既有的 docs/handoff/daily/VIA_SuccessLock_Ledger_v0100.jsonl(只增帳),逐列核「檔在 + 內容雜湊(先換成 LF)相同」;
       對不上或檔不見 = 鎖不成立 → 歸退步、判定紅。本檔只讀這本帳,不寫。
     · 項目層:一個項目只要綠過就鎖進 FEEDBACK_SUCCESSLOCK_<來源>.json;之後不是綠或不見,每一輪都報退步,直到再綠或操作員 release。
       (v0100 只跟上一輪比,隔一輪就忘;鎖檔名不帶來源版號,來源引擎出新版不會把鎖清掉。)
     · 模組引擎的鍵改用家族名(v0100 用編號,家族登新版就換鍵);編號改放在版本欄。
  ② 給動作主力的更新回饋:FEEDBACK_DELTA_latest.txt —— 這一輪跟上一輪比:修好 / 新增問題 / 退步 / 不見 / 仍未解(數字完整,清單超量時寫明另幾項)。
     --actor claude|chatgpt|<名字>(或環境變數 VIA_ACTOR)寫進表頭與主力帳;Windows 上把「更新回饋 + 回饋包」放進剪貼簿(--no-clip 關)。
     兩個檔都是純文字,Claude 與 ChatGPT 讀同一份;經 VCGC MCP 唯讀門面的鍵是 vcgc/feedback 與 vcgc/feedback-delta(CGC_MDL279 v0104)。
  ③ 本機免費工具紀錄:20 個候選庫逐一記「已套用(這一輪真的用到)/ 已裝沒用到 / 未裝」與版本,進矩陣的「本機工具」區塊與
     local_free_tools_ledger.jsonl(只增)。本版實際套用:orjson(讀冊)· psutil(資源行)· jsonschema(--in 項目冊欄位驗證);都可選,缺席照跑。不裝任何套件。
  ④ 回饋包與更新回饋會離開本機,所以把使用者家目錄路徑遮成 %USERPROFILE% / ~(本機的矩陣頁與完整去向冊不遮)。
  動詞  run · selftest · spec · version · tools(只印工具狀態)· release <鍵的子字串>(把項目層的鎖放掉,另記放鎖帳)
  旗標  v0100 的 --in --out --budget --no-open,加 --actor <名> --no-clip
邊界  唯讀倉;只寫 VIA_Reports/vcgc。不發號 · 不裝套件 · 不連網 · 不載 TA-Lib。
呼叫  VIA_FROM_VCGC=YES python3 CGC_MDL149_…_vNNNN.py run CGC_MDL283_CardMatrixFeedback run --actor claude
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

import datetime as _dt
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ENGINE = "CGC_MDL283_CardMatrixFeedback_v0101"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL283_CardMatrixFeedback_v0100.py"
_PRIOR_FILE = HERE / PRIOR_NAME
_spec = importlib.util.spec_from_file_location("CGC_MDL283_CardMatrixFeedback_v0100", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL283_CardMatrixFeedback_v0100"] = PRIOR
_spec.loader.exec_module(PRIOR)
PRIOR.ENGINE = ENGINE  # 表頭與帳寫本版
E, LN, CN, cut = PRIOR.E, PRIOR.LN, PRIOR.CN, PRIOR.cut
LEDGER_REL = "docs/handoff/daily/VIA_SuccessLock_Ledger_v0100.jsonl"
VER_IN_TEXT = re.compile(r"_v\d{4}")
HOME_RX = [(re.compile(r"[A-Za-z]:\\Users\\[^\\/\s·]+"), "%USERPROFILE%"), (re.compile(r"/(?:home|Users)/[^/\s·]+"), "~")]
# (顯示名, import 名, 發行名, 用途, 本版有沒有接)
FREE_TOOLS = [("orjson", "orjson", "orjson", "讀冊與快照", True), ("psutil", "psutil", "psutil", "本機資源行", True),
              ("jsonschema", "jsonschema", "jsonschema", "--in 項目冊欄位驗證", True), ("duckdb", "duckdb", "duckdb", "資料庫矩陣", False),
              ("polars", "polars", "polars", "大冊彙總", False), ("pyarrow", "pyarrow", "pyarrow", "parquet 列數與 schema", False),
              ("msgspec", "msgspec", "msgspec", "冊列型別驗證", False), ("pydantic", "pydantic", "pydantic", "收據結構檢查", False),
              ("pandera", "pandera", "pandera", "輸出表頭驗證", False), ("deepdiff", "deepdiff", "deepdiff", "同名異內容逐欄比", False),
              ("rapidfuzz", "rapidfuzz", "rapidfuzz", "相似檔名偵測", False), ("networkx", "networkx", "networkx", "相依圖與修正順序", False),
              ("libcst", "libcst", "libcst", "精準 AST 改寫", False), ("radon", "radon", "radon", "複雜度指標", False),
              ("GitPython", "git", "GitPython", "本機對 origin 差異", False), ("watchdog", "watchdog", "watchdog", "檔案一變就重算", False),
              ("diskcache", "diskcache", "diskcache", "雜湊與解析快取", False), ("xxhash", "xxhash", "xxhash", "快速指紋", False),
              ("pytest", "pytest", "pytest", "測試統一跑法", False), ("hypothesis", "hypothesis", "hypothesis", "正則性質測試", False)]
USED = set()
ITEM_SCHEMA = {"type": "object", "required": ["lamp"], "properties": {
    "section": {"type": "string"}, "system": {"type": "string"}, "id": {"type": ["string", "number"]}, "title": {"type": "string"},
    "detail": {"type": "string"}, "ver": {"type": "string"}, "at": {"type": "string"}, "needs": {"type": "boolean"},
    "lamp": {"enum": ["g", "y", "r", "x", "green", "yellow", "red", "gray", "GREEN", "YELLOW", "RED", "GRAY", "綠", "黃", "紅", "灰"]}}}
CTX = {"via": None, "out": None, "extras": False, "famkey": False, "actor": "", "clip": False, "lock": None, "lock_path": None, "lock_new": 0,
       "delta": [], "notes": [], "src": ""}
_O = {"assemble": PRIOR.assemble, "stage1": PRIOR.stage1, "write_out": PRIOR.write_out, "render": PRIOR.render}


def mask(s: str) -> str:
    for rx, to in HOME_RX:
        s = rx.sub(to, s)
    return s


def jload(p: Path):
    """讀 JSON:有 orjson 用它(記為已套用),沒有走標準庫。"""
    b = p.read_bytes()
    try:
        import orjson
        USED.add("orjson")
        return orjson.loads(b)
    except ImportError:
        return json.loads(b.decode("utf-8"))


def stable_slug(source: str) -> str:
    return re.sub(r"[^\w.-]+", "_", VER_IN_TEXT.sub("", source))[:60] or "default"


def sha_lf(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


# ---------------- ③ 本機免費工具 ----------------
def tools_state():
    out = []
    for name, imp, dist, use, wired in FREE_TOOLS:
        try:
            have = importlib.util.find_spec(imp) is not None
        except (ImportError, ValueError):
            have = False
        ver = ""
        if have:
            try:
                ver = importlib.metadata.version(dist)
            except importlib.metadata.PackageNotFoundError:
                ver = "版本讀不到"
        state = "已套用" if name in USED else ("已裝 · 這一輪沒用到" if have and wired else ("已裝 · 本引擎還沒接" if have else "未裝 · 可選"))
        out.append({"name": name, "have": have, "ver": ver, "use": use, "wired": wired, "state": state})
    return out


def tools_items(ts):
    return [{"section": "本機工具", "system": "VCGC", "lamp": "g" if t["state"] == "已套用" else "x", "id": t["name"], "title": t["name"],
             "ver": t["ver"], "detail": "%s · %s" % (t["state"], t["use"])} for t in ts]


def resource_line() -> str:
    try:
        import psutil
        USED.add("psutil")
        vm = psutil.virtual_memory()
        return "[資源] RAM 可用 %.1f / %.1f GB · CPU %d 核" % (vm.available / 2 ** 30, vm.total / 2 ** 30, psutil.cpu_count() or 0)
    except ImportError:
        return "[資源] 未量(沒有 psutil)"


def validate_items(raw):
    """--in 項目冊的欄位驗證(有 jsonschema 才做)。不合的項目照樣留著,只在回饋包點名。"""
    try:
        import jsonschema
    except ImportError:
        return "欄位驗證沒做(沒有 jsonschema)"
    USED.add("jsonschema")
    v = jsonschema.Draft7Validator(ITEM_SCHEMA)
    bad = ["第 %d 列 %s" % (i + 1, cut(next(v.iter_errors(r)).message, 60)) for i, r in enumerate(raw) if isinstance(r, dict) and not v.is_valid(r)]
    return ("欄位驗證 %d 列不合(項目照留):%s" % (len(bad), cut(";".join(bad), 220))) if bad else "欄位驗證全合"


# ---------------- ① 成功鎖 ----------------
def ledger_items(via: Path, ledger: Path = None):
    """檔案層:既有成功鎖定帳逐列核雜湊。回原始項目(區塊「成功鎖」)。"""
    ledger = ledger or (via / LEDGER_REL)
    if not ledger.exists():
        return [{"section": "成功鎖", "system": "VCGC", "lamp": "x", "id": LEDGER_REL, "title": "成功鎖定帳", "detail": "帳不在,沒有證據"}]
    rows = {}
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                r = json.loads(line)
                rows[r["path"]] = r  # 同一檔取最後一列(只增帳:後列蓋前列的鎖)
            except (ValueError, KeyError):
                rows["壞列 %d" % len(rows)] = {"path": "(帳裡有一列讀不懂)", "bad": True}

    def one(r):
        code = str(r.get("vcgc_code") or "")
        base = {"section": "成功鎖", "system": (code.split("-") + ["", ""])[1] or "VCGC", "id": r["path"], "title": os.path.basename(r["path"]),
                "ver": str(r.get("version") or ""), "at": str(r.get("locked_at") or "")}
        if r.get("bad"):
            return dict(base, lamp="y", detail="帳列讀不懂,待確認")
        f = via / r["path"]
        if not f.is_file():
            return dict(base, lamp="r", detail="鎖不成立:鎖定的檔不見了 · %s" % cut(r.get("what"), 60))
        now = sha_lf(f)
        if now != r.get("sha256_lf"):
            return dict(base, lamp="r", detail="鎖不成立:鎖定後內容變了(鎖 %s → 現 %s)· %s" % (str(r.get("sha256_lf"))[:12], now[:12], cut(r.get("what"), 60)))
        return dict(base, lamp="g", detail="鎖還在 · %s · 證據 %s · %s" % (cut(r.get("what"), 60), cut(r.get("evidence"), 60), cut(r.get("scope"), 40)))
    return PRIOR.pmap(one, list(rows.values()))


def stage1(items, prev):
    items = _O["stage1"](items, prev)
    lock = CTX.get("lock")
    if lock:
        now = {it["key"] for it in items}
        for k in sorted(set(lock) - now):
            sec, sysn, name = (k.split("|", 2) + ["", ""])[:3]
            items.append({"section": sec or "未分區", "system": sysn or "—", "lamp": "r", "id": name, "title": name or k, "ver": "", "at": "", "needs": False,
                          "gone": True, "key": k, "was": "g", "rules": ["S3", "S5"], "selected": True,
                          "detail": "已鎖定的成功不見了(鎖於 %s)" % lock[k].get("since", "?")})
        for it in items:
            if it["key"] in lock and it["lamp"] != "g" and "S5" not in it["rules"]:
                it["rules"].append("S5")
                it["selected"], it["was"] = True, "g"
                it["detail"] += " · 曾鎖定為綠(%s)" % lock[it["key"]].get("since", "?")
    for it in items:
        if it["section"] == "成功鎖" and it["lamp"] == "r" and "S5" not in it["rules"]:
            it["rules"].append("S5")
            it["selected"], it["was"] = True, "g"
    return items


def assemble(raw, source, prev, budget=300, peer=None):
    raw = list(raw)
    CTX["notes"] = []
    CTX["res_line"] = resource_line()  # 先量,工具狀態才知道 psutil 這一輪有沒有用到
    for r in raw:  # 模組引擎的鍵改用家族名:v0100 用編號當鍵,家族每登一個新版編號就換,會被看成「舊的不見、新的出現」,鎖也跟著失效
        if CTX.get("famkey") and isinstance(r, dict) and r.get("section") == "模組引擎" and r.get("title") and r.get("id") != r.get("title"):
            r["ver"] = ("%s %s" % (r.get("ver") or "", r.get("id") or "")).strip()
            r["id"] = r["title"]
    if CTX.get("src"):
        CTX["notes"].append(validate_items(raw))
    if CTX.get("out") is not None:
        lp = CTX["out"] / ("FEEDBACK_SUCCESSLOCK_%s.json" % stable_slug(source))
        CTX["lock_path"] = lp
        try:
            CTX["lock"] = jload(lp) if lp.exists() else {}
        except ValueError:
            CTX["lock"] = {}
            CTX["notes"].append("成功鎖檔讀不懂,這一輪當成空的(舊檔沒動)")
    if CTX.get("extras") and CTX.get("via") is not None:
        raw += ledger_items(CTX["via"])
        raw += tools_items(tools_state())
    res = _O["assemble"](raw, source, prev, budget, peer)
    lock = CTX.get("lock")
    if lock is not None:
        byk = {it["key"]: it for it in res["items"]}
        res["checks"]["鎖定的成功都有交代(仍綠或已報退步)"] = all(k in byk and (byk[k]["lamp"] == "g" or byk[k].get("cls") == "REG") for k in lock)
        fresh = [it["key"] for it in res["items"] if it["lamp"] == "g" and not it.get("gone") and it["key"] not in lock]
        CTX["lock_new"] = len(fresh)
        CTX["lock_fresh"] = fresh
        if not all(res["checks"].values()):
            res["ok"], res["lamp"] = False, "r"
            res["why"] = "對帳不符:" + "、".join(k for k, v in res["checks"].items() if not v)
            res["head"][1] = "[判定] RED · " + res["why"]
    return res


# ---------------- ② 給動作主力的更新回饋 ----------------
def delta_lines(res, prev, actor):
    items = [it for it in res["items"]]
    head = ["# 給動作主力 %s 的更新回饋 · %s · 來源 %s" % (actor, res["stamp"], res["source"]),
            "[判定] %s · %s" % ({"g": "GREEN", "y": "YELLOW", "r": "RED"}[res["lamp"]], res["why"])]
    lock = CTX.get("lock") or {}
    reg = [it for it in items if it.get("cls") == "REG"]
    lock_line = "[成功鎖] 項目層累計 %d · 本輪新鎖 %d · 鎖不成立或退步 %d" % (len(lock) + CTX.get("lock_new", 0), CTX.get("lock_new", 0), len(reg))

    def row(it, was=None):
        return "%s/%s · %s%s · %s" % (it["system"], it["section"], cut(it["title"], 70), ("(%s→%s)" % (LN.get(was, "沒有"), LN[it["lamp"]])) if was is not None or prev is not None else "", cut(it["detail"], 110))

    def block(tag, rows, cap):
        out = ["[%s] %s" % (tag, r) for r in rows[:cap]]
        if len(rows) > cap:
            out.append("[%s] …另 %d 項,在矩陣用「%s」篩或看 FEEDBACK_FULL_latest.jsonl" % (tag, len(rows) - cap, tag))
        return out
    body = []
    if prev is None:
        body.append("[這一輪跟上一輪比] 沒有上一輪(第一輪);請直接讀 FEEDBACK_latest.txt")
        fixed = new = []
    else:
        cur = [it for it in items if not it.get("gone")]
        fixed = [it for it in cur if it["lamp"] == "g" and prev.get(it["key"]) in ("r", "y", "x")]
        new = [it for it in cur if it["lamp"] in ("r", "y") and prev.get(it["key"]) in (None, "g") and it.get("cls") != "REG"]
        gone = [it for it in items if it.get("gone")]
        still = [it for it in cur if it["lamp"] in ("r", "y") and prev.get(it["key"]) in ("r", "y")]
        body.append("[這一輪跟上一輪比] 修好 %d(非綠→綠)· 新增問題 %d · 退步 %d · 不見 %d · 仍未解 %d(紅 %d · 黃 %d)" % (
            len(fixed), len(new), len(reg), len(gone), len(still), sum(it["lamp"] == "r" for it in still), sum(it["lamp"] == "y" for it in still)))
        body += block("修好", [row(it, prev.get(it["key"])) for it in fixed], 20)
        body += block("新增", [row(it, prev.get(it["key"])) for it in new], 30)
    body += block("退步", [row(it, "g") for it in reg], 30)
    body.append("[仍待處理] " + (" · ".join("%s %d" % (CN[c], n) for c, n in res["by_cls"].items() if n) or "沒有"))
    body += [lock_line, "[規則] 綠的已鎖,不要重驗;先處理退步,再真紅;待裁等操作員;每項細節在 FEEDBACK_latest.txt,包裡沒逐列的在完整去向冊",
             "NEXT: " + res["next"]]
    return [mask(x) for x in head + body], {"fixed": len(fixed), "new": len(new), "reg": len(reg)}


def write_out(out: Path, res, pack, page, slug):
    snap = out / ("FEEDBACK_SNAPSHOT_%s.json" % slug)
    prev = None
    if snap.exists():
        try:
            prev = jload(snap)
        except ValueError:
            prev = None
    actor = CTX.get("actor") or "未指定(--actor claude|chatgpt 或環境變數 VIA_ACTOR)"
    ts = tools_state()
    delta, dn = delta_lines(res, prev, actor)
    CTX["delta"] = delta
    extra = ["[主力] %s · 更新回饋在 FEEDBACK_DELTA_latest.txt(修好 %d · 新增 %d · 退步 %d)" % (actor, dn["fixed"], dn["new"], dn["reg"]), delta[-3 if delta[-3].startswith("[成功鎖]") else -2],
             "[工具] 已套用 %s · 已裝沒用到 %s · 未裝 %d 個" % (
                 "、".join("%s %s" % (t["name"], t["ver"]) for t in ts if t["state"] == "已套用") or "無",
                 "、".join(t["name"] for t in ts if t["have"] and t["state"] != "已套用") or "無", sum(not t["have"] for t in ts)), CTX.get("res_line") or resource_line()]
    extra += ["[註] " + n for n in CTX.get("notes") or []]
    pack = [mask(x) for x in pack[:2] + extra + pack[2:]]
    final = _O["write_out"](out, res, pack, page, slug)
    (out / "FEEDBACK_DELTA_latest.txt").write_text("\n".join(delta) + "\n", encoding="utf-8")
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(str(out / "feedback_actor_ledger.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"at": stamp, "engine": ENGINE, "actor": CTX.get("actor") or "", "lamp": res["lamp"], "by_class": {CN[c]: n for c, n in res["by_cls"].items()}, **dn}, ensure_ascii=False) + "\n")
    with open(str(out / "local_free_tools_ledger.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"at": stamp, "engine": ENGINE, "applied": ["%s %s" % (t["name"], t["ver"]) for t in ts if t["state"] == "已套用"],
                            "installed_unused": [t["name"] for t in ts if t["have"] and t["state"] != "已套用"], "missing": [t["name"] for t in ts if not t["have"]]}, ensure_ascii=False) + "\n")
    if res["ok"] and CTX.get("lock") is not None and CTX.get("lock_path") is not None:
        lock = dict(CTX["lock"])
        for k in CTX.get("lock_fresh") or []:
            lock[k] = {"since": res["stamp"]}
        CTX["lock_path"].write_text(json.dumps(lock, ensure_ascii=False), encoding="utf-8")
    if CTX.get("clip") and os.name == "nt":
        try:
            subprocess.run(["clip"], input=("\n".join(delta + [""] + final)).encode("utf-16"), check=True, timeout=20)
            print("[剪貼簿] 更新回饋 + 回饋包已放進剪貼簿,直接貼給 %s" % actor, flush=True)
        except (OSError, subprocess.SubprocessError) as e:
            print("[剪貼簿] 放不進去(%s),請開 FEEDBACK_DELTA_latest.txt 複製" % type(e).__name__, flush=True)
    return final


def render(res, cards, pack, css, tpl_note, accel) -> str:
    page = _O["render"](res, cards, pack, css, tpl_note, accel)
    mark = '<section class="card" id="mx">'
    if CTX.get("delta") and page.count(mark) == 1:
        box = ('<section class="card"><h2>給動作主力的更新回饋(這一輪跟上一輪比)</h2><div class="note">檔 FEEDBACK_DELTA_latest.txt · Windows 上已連同回饋包放進剪貼簿</div>'
               '<pre class="pack">%s</pre></section>') % E("\n".join(CTX["delta"]))
        page = page.replace(mark, box + mark)
    return page


PRIOR.assemble, PRIOR.stage1, PRIOR.write_out, PRIOR.render = assemble, stage1, write_out, render


def __getattr__(name):  # 薄尾轉接:v0100 的公開名稱照樣拿得到
    return getattr(PRIOR, name)


def release(out: Path, needle: str) -> int:
    n = 0
    for lp in sorted(out.glob("FEEDBACK_SUCCESSLOCK_*.json")):
        lock = jload(lp)
        hit = [k for k in lock if needle in k]
        if hit:
            for k in hit:
                lock.pop(k)
            lp.write_text(json.dumps(lock, ensure_ascii=False), encoding="utf-8")
            with open(str(out / "successlock_release_ledger.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps({"at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "file": lp.name, "needle": needle, "released": hit}, ensure_ascii=False) + "\n")
            n += len(hit)
    print("[放鎖] 子字串「%s」放掉 %d 個項目層的鎖(成功鎖定帳不受影響)" % (needle, n))
    return 0 if n else 2


def selftest() -> int:
    fails = []

    def chk(name, cond, got=None):
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · 得到 %r" % (got,)), flush=True)
        if not cond:
            fails.append(name)
    saved = dict(CTX)
    CTX.update(via=None, out=None, extras=False, famkey=False, lock=None, src="", actor="")
    chk("v0100 的自測在本版掛上後仍全過", PRIOR.selftest() == 0)
    tmp = Path(tempfile.mkdtemp(prefix="via_cmf101_st_"))
    try:
        raw = [{"section": "引擎", "system": "VCGC", "lamp": "g", "id": "a", "title": "A", "detail": "已註冊"},
               {"section": "引擎", "system": "VCGC", "lamp": "g", "id": "b", "title": "B", "detail": "已註冊"},
               {"section": "引擎", "system": "VDF", "lamp": "y", "id": "c", "title": "C", "detail": "尾版未註冊"},
               {"section": "參數", "system": "VCGC", "lamp": "y", "id": "p", "title": "db.path", "detail": "值 C:\\Users\\someone\\OneDrive\\x.duckdb · 缺 號"}]
        CTX.update(out=tmp, actor="claude")
        r1 = assemble(raw, "selftest_v0100 來源", None, 300)
        chk("鎖檔名不帶來源版號", CTX["lock_path"].name == "FEEDBACK_SUCCESSLOCK_selftest_來源.json", CTX["lock_path"].name)
        p1 = write_out(tmp, r1, list(r1["head"]), lambda p: render(r1, PRIOR.cards_of(r1), p, "", "自測", "自測"), "st")
        lock = json.loads(CTX["lock_path"].read_text(encoding="utf-8"))
        chk("第一輪:兩個綠進項目層的鎖", sorted(lock) == ["引擎|VCGC|a", "引擎|VCGC|b"], sorted(lock))
        chk("回饋包有主力、成功鎖、工具、資源四行", all(any(x.startswith(t) for x in p1) for t in ("[主力] claude", "[成功鎖]", "[工具]", "[資源]")))
        chk("回饋包遮掉家目錄路徑", "someone" not in "\n".join(p1) and "%USERPROFILE%" in "\n".join(p1))
        chk("完整去向冊(留在本機)不遮", "someone" in (tmp / "FEEDBACK_FULL_latest.jsonl").read_text(encoding="utf-8"))
        d1 = (tmp / "FEEDBACK_DELTA_latest.txt").read_text(encoding="utf-8")
        chk("第一輪的更新回饋說沒有上一輪", "沒有上一輪" in d1 and d1.strip().splitlines()[-1].startswith("NEXT:"))
        raw2 = [dict(raw[0], lamp="y", detail="尾版未註冊"), dict(raw[2], lamp="g", detail="已註冊"), raw[3],
                {"section": "引擎", "system": "VRN", "lamp": "r", "id": "n", "title": "N", "detail": "檔不在"}]  # a 綠→黃 · b 不見 · c 修好 · n 新紅
        (tmp / "FEEDBACK_SNAPSHOT_st.json").unlink()  # 連上一輪快照都沒有,只靠鎖
        r2 = assemble(raw2, "selftest_v0102 來源", None, 300)
        k2 = {it["key"]: it for it in r2["items"]}
        chk("沒有上一輪快照,鎖過的綠變黃仍報退步", k2["引擎|VCGC|a"]["cls"] == "REG", k2["引擎|VCGC|a"].get("cls"))
        chk("鎖過的綠不見了,補成退步列進矩陣", k2.get("引擎|VCGC|b", {}).get("gone") and k2["引擎|VCGC|b"]["cls"] == "REG")
        chk("有退步:判定紅、對帳仍相符(含成功鎖那一條)", r2["lamp"] == "r" and r2["ok"] and len(r2["checks"]) == 6, r2["checks"])
        (tmp / "FEEDBACK_SNAPSHOT_st.json").write_text(json.dumps({"引擎|VCGC|a": "g", "引擎|VCGC|b": "g", "引擎|VDF|c": "y", "參數|VCGC|p": "y"}), encoding="utf-8")
        write_out(tmp, r2, list(r2["head"]), lambda p: render(r2, PRIOR.cards_of(r2), p, "", "自測", "自測"), "st")
        d2 = (tmp / "FEEDBACK_DELTA_latest.txt").read_text(encoding="utf-8")
        chk("更新回饋:修好 1 · 新增 1 · 退步 2 · 仍未解 1", "修好 1(非綠→綠)· 新增問題 1 · 退步 2 · 不見 1 · 仍未解 1" in d2, d2.splitlines()[2])
        chk("更新回饋逐列點名修好的與新增的", "[修好] VDF/引擎 · C" in d2 and "[新增] VRN/引擎 · N" in d2 and d2.count("[退步]") == 2)
        lock = json.loads(CTX["lock_path"].read_text(encoding="utf-8"))
        chk("退步的鎖不會被悄悄拿掉,新修好的加鎖", "引擎|VCGC|a" in lock and "引擎|VCGC|b" in lock and "引擎|VDF|c" in lock)
        page = (tmp / "WORKPLATFORM_latest.html").read_text(encoding="utf-8")
        chk("頁面多一塊給動作主力的更新回饋", "給動作主力的更新回饋" in page and page.count("</script>") == 2)
        chk("release 放掉指定的鎖並記帳", release(tmp, "VCGC|b") == 0 and "引擎|VCGC|b" not in json.loads(CTX["lock_path"].read_text(encoding="utf-8"))
            and (tmp / "successlock_release_ledger.jsonl").exists())
        # 檔案層:成功鎖定帳
        via = tmp / "via"
        (via / "m").mkdir(parents=True)
        (via / "m" / "ok_v0100.py").write_bytes(b"x = 1\r\ny = 2\r\n")  # 鎖的是 LF 版雜湊,CRLF 檔也要算相符
        (via / "m" / "chg_v0100.py").write_bytes(b"changed\n")
        led = tmp / "led.jsonl"
        led.write_text("\n".join(json.dumps(r) for r in [
            {"path": "m/ok_v0100.py", "version": "0100", "vcgc_code": "VIA-VDF-MDL001", "sha256_lf": hashlib.sha256(b"x = 1\ny = 2\n").hexdigest(), "what": "w", "evidence": "e"},
            {"path": "m/chg_v0100.py", "version": "0100", "vcgc_code": "VIA-VRN-MDL002", "sha256_lf": "0" * 64, "what": "w", "evidence": "e"},
            {"path": "m/gone_v0100.py", "version": "0100", "vcgc_code": "VIA-VCGC-MDL003", "sha256_lf": "1" * 64, "what": "w", "evidence": "e"}]), encoding="utf-8")
        li = {x["id"]: x for x in ledger_items(via, led)}
        chk("檔案層:相符綠(換行不同不算變)· 內容變紅 · 檔不見紅 · 系統取自編號", (li["m/ok_v0100.py"]["lamp"], li["m/chg_v0100.py"]["lamp"], li["m/gone_v0100.py"]["lamp"], li["m/ok_v0100.py"]["system"]) == ("g", "r", "r", "VDF"))
        CTX.update(out=None, lock=None)
        r3 = assemble(list(li.values()), "st3", None, 300)
        chk("檔案層鎖不成立一律歸退步", sum(1 for it in r3["items"] if it["cls"] == "REG") == 2 and r3["lamp"] == "r")
        CTX.update(famkey=True)
        e1 = assemble([{"section": "模組引擎", "system": "VCGC", "lamp": "g", "id": "VIA-VCGC-MDL0001", "title": "Fam(MDL)", "ver": "v0100", "detail": "已註冊"}], "st4", None, 300)
        e2 = assemble([{"section": "模組引擎", "system": "VCGC", "lamp": "g", "id": "VIA-VCGC-MDL0002", "title": "Fam(MDL)", "ver": "v0101", "detail": "已註冊"}], "st4", {e1["items"][0]["key"]: "g"}, 300)
        chk("模組引擎家族登新版(編號換了)鍵不變,不算不見也不算新出現", e1["items"][0]["key"] == "模組引擎|VCGC|Fam(MDL)" and len(e2["items"]) == 1 and not e2["items"][0]["selected"] and "MDL0002" in e2["items"][0]["ver"])
        ts = tools_state()
        chk("工具清單 20 個,已套用的一定是裝了的", len(ts) == 20 and all(t["have"] for t in ts if t["state"] == "已套用"))
        chk("工具帳與主力帳都有寫(只增)", (tmp / "local_free_tools_ledger.jsonl").read_text(encoding="utf-8").count("\n") == 2 and (tmp / "feedback_actor_ledger.jsonl").exists())
        CTX.update(src="x")
        note = validate_items([{"lamp": "g"}, {"lamp": "purple"}, {"title": "沒燈"}])
        chk("項目冊欄位驗證(有 jsonschema 才做)", ("2 列不合" in note) if "jsonschema" in USED else ("沒做" in note), note)
        v = PRIOR.find_via()
        if v is not None:
            css, tnote, tl = PRIOR.template(v)
            chk("模板鎖尾版 v0101:燈四色一律白字", tl == "g" and "TemplateLock_v0101" in tnote and "color:var(--panel);text-align:center}" in css and ".y{background:var(--lamp-yellow)}" in css, tnote)
        chk("本檔原始碼沒有色碼", not re.search(r"#[0-9a-fA-F]{6}\b", Path(__file__).read_text(encoding="utf-8")))
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)
        CTX.clear()
        CTX.update(saved)
    print("[selftest] %s · %d 敗 · %s · 加速器 %s" % ("GREEN" if not fails else "RED", len(fails), ENGINE, PRIOR.accel_status()), flush=True)
    return 0 if not fails else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    def opt(name):
        if name in args:
            i = args.index(name)
            return args[i + 1] if i + 1 < len(args) else ""
        return ""
    verb = args[0] if args and not args[0].startswith("-") else ("selftest" if "--selftest" in args else "run")
    if verb == "selftest":
        return selftest()
    if verb == "version":
        print("%s · %s(薄尾,本體 %s)" % (Path(__file__).name, ENGINE, PRIOR_NAME))
        return 0
    if verb == "spec":
        print(__doc__)
        print(PRIOR.__doc__)
        return 0
    if verb == "tools":
        for t in tools_state():
            print("%-11s %-10s %s · %s" % (t["name"], t["ver"] or "—", t["state"], t["use"]))
        return 0
    via = PRIOR.find_via(opt("--root"))
    if via is None:
        print("[紅] 找不到 VIA 夾")
        return 3
    out = Path(opt("--out")) if opt("--out") else via / "VIA_Reports" / "vcgc"
    if verb == "release":
        needle = args[1] if len(args) > 1 and not args[1].startswith("-") else ""
        if not needle:
            print("用法:release <鍵的子字串>(鍵長得像 區塊|系統|項目)")
            return 2
        return release(out, needle)
    if verb != "run":
        print("動詞:run · selftest · spec · version · tools · release")
        return 2
    try:
        budget = int(opt("--budget") or 300)
    except ValueError:
        budget = 300
    CTX.update(via=via, out=out, extras=not opt("--in"), famkey=not opt("--in"), src=opt("--in"), actor=(opt("--actor") or os.environ.get("VIA_ACTOR") or "").strip(), clip="--no-clip" not in args)
    return PRIOR.run(via, out, opt("--in"), budget, "--no-open" in args)


if __name__ == "__main__":
    sys.exit(main())
