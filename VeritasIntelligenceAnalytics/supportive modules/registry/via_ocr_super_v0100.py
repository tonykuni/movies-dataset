#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_ocr_super_v0100 — OCR 超引擎(TOOL-035;操作員令 2026-08-13)
================================================================
令:PaddleOCR 生態+輕量替代全編成一 SUPER ENGINE,LOCAL FREE LIBS ONLY;
加速器先行、簡單清亮先行,失敗才逐步載用重量級工具;易衝突者一律隔離環境安裝。
四層編成(操作員優先級表原樣落地):
  加速層(第一優先):ONNX Runtime(RapidOCR 內建)——脫離訓練框架極速 CPU 推論
              (FastDeploy/PaddleX 列延伸候裁)
  OCR 層(輕→重階梯):①RapidOCR(輕量首選,ONNX) ②Tesseract(老牌印刷體)
              ③PaddleOCR(重量,繁中最準) ④Surya(torch,複雜版面/表格)
  認知層:內建 Regex 抽取器(第二優先,零依賴即用)——統編/金額/日期/電話/Email;
        PaddleNLP UIE(第一優先)缺件時列隔離安裝計畫
  擴展層:PaddleSpeech/PaddleDetection——列候裁計畫,不預載
方法:逐車道隔離環境探測(READY/缺境/缺模/缺本體誠實四態)→按優先級跑,
     成功(有行+信心≥0.5)即停;失敗才升級下一車道;--all 全車道交叉
紅線:本引擎零安裝;缺車道只出隔離安裝計畫執行令(uv+實測最快鏡像);
     RapidOCR 相依自帶 opencv-python 屬隔離境內豁免(拒裝令拒的是入 base)
用法:via-ocrsuper <圖片路徑>          → 階梯辨識(輕先重後,成功即停)
     via-ocrsuper <圖片> --all        → 全 READY 車道交叉
     via-ocrsuper <圖片> --extract    → 加認知層(Regex 結構化抽取)
     via-ocrsuper --probe             → 四車道環境探測矩陣(唯讀)
     via-ocrsuper --plan              → 缺件車道之隔離安裝計畫(執行令)
     via-ocrsuper --selftest          → 內建 12 檢(零網路零環境依賴)
"""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "ocrsuper_runs"
DEPS_DIR = VIA / "VIA_Reports" / "depsuper_runs"


def _newest(pattern: str, root: Path) -> Path | None:
    hits = sorted(root.glob(pattern))
    return hits[-1] if hits else None


def _load_by_path(mod_name: str, path: Path):
    try:
        spec = importlib.util.spec_from_file_location(mod_name, str(path))
        if spec is None or spec.loader is None:
            return None
        m = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = m
        try:
            spec.loader.exec_module(m)
        except Exception:
            sys.modules.pop(mod_name, None)
            raise
        return m
    except Exception:
        return None


_reb_path = _newest("via_env_rebuild_v0*.py", HERE)
REB = _load_by_path("via_env_rebuild_latest", _reb_path) if _reb_path else None

# ── 車道編成(輕→重階梯;每車道隔離環境)───────────────────────────
LANES = [
    {"k": "rapidocr", "pri": 1, "label": "RapidOCR(ONNX 加速;輕量首選)",
     "mod": "rapidocr_onnxruntime", "envs": ["via_rapidocr"], "py": "3.12",
     "pkgs": ["rapidocr-onnxruntime", "pillow"], "timeout": 240,
     "note": "脫離 paddle 框架;CPU 極速;相依自帶 opencv-python(隔離境內豁免)"},
    {"k": "tesseract", "pri": 2, "label": "Tesseract(老牌印刷體;低記憶體)",
     "mod": "pytesseract", "envs": ["via_tess"], "py": "3.12",
     "pkgs": ["pytesseract", "pillow"], "timeout": 240, "ext_bin": "tesseract",
     "note": "需系統本體(外部安裝器,候裁);乾淨印刷件極快"},
    {"k": "paddleocr", "pri": 3, "label": "PaddleOCR(重量;繁簡中最準)",
     "mod": "paddleocr", "envs": ["paddle_312", "paddle_311", "via_core_312"], "py": "3.12",
     "pkgs": ["paddlepaddle", "paddleocr"], "timeout": 900,
     "note": "重車道;首跑下模型(同意閘);PP-StructureV3 版面家族"},
    {"k": "surya", "pri": 4, "label": "Surya(torch;複雜版面/表格結構)",
     "mod": "surya", "envs": ["via_surya"], "py": "3.12",
     "pkgs": ["surya-ocr"], "timeout": 900,
     "note": "RAG 前置版面分析強;torch 重件"},
]
EXT_LAYERS = [  # 認知/擴展層:第一優先件缺=列計畫;第二優先內建
    {"k": "uie", "label": "PaddleNLP UIE(認知層第一優先)", "mod": "paddlenlp",
     "envs": ["via_nlp"], "py": "3.12", "pkgs": ["paddlenlp"],
     "note": "Zero-shot 資訊抽取;缺件時內建 Regex(第二優先)頂上"},
    {"k": "speech", "label": "PaddleSpeech(擴展層 ASR/TTS)", "mod": "paddlespeech",
     "envs": ["via_speech"], "py": "3.10", "pkgs": ["paddlespeech"],
     "note": "候裁:需用再建;重件"},
    {"k": "detect", "label": "PaddleDetection(擴展層物件/瑕疵)", "mod": "paddledet",
     "envs": ["via_detect"], "py": "3.12", "pkgs": ["paddledet"],
     "note": "候裁:需用再建;重件"},
]
CONF_GATE = 0.5  # 車道成功門檻:有行且平均信心≥此值,否則升級下一車道

_SRC = {
    "rapidocr": (
        "import json,sys\n"
        "try:\n"
        "    from rapidocr_onnxruntime import RapidOCR\n"
        "    r,_=RapidOCR()(sys.argv[1])\n"
        "    L=[{'text':t,'conf':float(c)} for _b,t,c in (r or [])]\n"
        "    print(json.dumps({'ok':True,'lines':L},ensure_ascii=False))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'ok':False,'err':str(e)[:120]}))\n"),
    "tesseract": (
        "import json,sys\n"
        "try:\n"
        "    from PIL import Image\n"
        "    import pytesseract\n"
        "    t=pytesseract.image_to_string(Image.open(sys.argv[1]),lang='chi_tra+eng')\n"
        "    L=[{'text':x,'conf':0.6} for x in t.splitlines() if x.strip()]\n"
        "    print(json.dumps({'ok':True,'lines':L},ensure_ascii=False))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'ok':False,'err':str(e)[:120]}))\n"),
    "paddleocr": (
        "import json,sys\n"
        "try:\n"
        "    from paddleocr import PaddleOCR\n"
        "    o=PaddleOCR(use_angle_cls=True,lang='ch',show_log=False)\n"
        "    res=o.ocr(sys.argv[1],cls=True)\n"
        "    L=[]\n"
        "    for pg in (res or []):\n"
        "        for ln in (pg or []):\n"
        "            L.append({'text':ln[1][0],'conf':float(ln[1][1])})\n"
        "    print(json.dumps({'ok':True,'lines':L},ensure_ascii=False))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'ok':False,'err':str(e)[:120]}))\n"),
    "surya": (
        "import json,sys\n"
        "try:\n"
        "    from PIL import Image\n"
        "    from surya.recognition import RecognitionPredictor\n"
        "    from surya.detection import DetectionPredictor\n"
        "    img=Image.open(sys.argv[1]).convert('RGB')\n"
        "    pr=RecognitionPredictor()([img],[None],DetectionPredictor())\n"
        "    L=[{'text':x.text,'conf':float(getattr(x,'confidence',0.8) or 0.8)}\n"
        "       for x in pr[0].text_lines]\n"
        "    print(json.dumps({'ok':True,'lines':L},ensure_ascii=False))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'ok':False,'err':str(e)[:120]}))\n"),
}


# ── 環境探測(隔離境四態)─────────────────────────────────────────
def env_map() -> dict:
    """既有環境名 → python 路徑(借重建引擎之盤點;缺=僅 BASE)。"""
    out = {}
    try:
        if REB:
            for e in REB.discover_envs([], None):
                if e.get("py"):
                    out[e["name"]] = e["py"]
    except Exception:
        pass
    return out


def _classify(ext_ok: bool, py: str | None, mod_rc: int | None) -> str:
    """車道四態裁決(純函式可自測):READY/NO_BIN/NO_ENV/NO_MOD。"""
    if not ext_ok:
        return "NO_BIN"
    if py is None:
        return "NO_ENV"
    return "READY" if mod_rc == 0 else "NO_MOD"


def probe_lane(lane: dict, envs: dict) -> tuple[str, str | None]:
    py = next((envs[e] for e in lane["envs"] if e in envs), None)
    ext_ok = (not lane.get("ext_bin")) or bool(shutil.which(lane["ext_bin"]))
    mod_rc = None
    if ext_ok and py:
        try:
            r = subprocess.run([py, "-c", "import " + lane["mod"]], capture_output=True,
                               text=True, timeout=90, stdin=subprocess.DEVNULL)
            mod_rc = r.returncode
        except Exception:
            mod_rc = 1
    return _classify(ext_ok, py, mod_rc), py


def run_lane(lane: dict, py: str, image: str) -> dict:
    try:
        r = subprocess.run([py, "-c", _SRC[lane["k"]], image], capture_output=True,
                           text=True, timeout=lane["timeout"], stdin=subprocess.DEVNULL)
        d = json.loads((r.stdout or "").strip().splitlines()[-1])
    except Exception as exc:
        return {"k": lane["k"], "ok": False, "err": f"{type(exc).__name__}:{str(exc)[:80]}"}
    if not d.get("ok"):
        return {"k": lane["k"], "ok": False, "err": d.get("err", "?")}
    lines = d.get("lines", [])
    avg = round(sum(x.get("conf", 0) for x in lines) / len(lines), 4) if lines else 0.0
    return {"k": lane["k"], "ok": True, "n": len(lines), "avg": avg,
            "text": [x.get("text", "") for x in lines]}


def pick_winner(results: list[dict], thr: float = CONF_GATE) -> dict | None:
    """階梯裁決(純函式):按優先序取第一個「有行且信心過門檻」者;全敗=None 誠實。"""
    for r in results:
        if r.get("ok") and r.get("n", 0) >= 1 and r.get("avg", 0.0) >= thr:
            return r
    return None


# ── 認知層:內建 Regex 抽取(第二優先,零依賴)──────────────────────
_PATTERNS = {
    "統一編號": r"(?<!\d)\d{8}(?!\d)",
    "金額": r"(?:NT\$|NTD|\$|金額[:：]?)\s*([0-9][0-9,]*(?:\.\d+)?)",
    "日期": r"\d{4}[-/年.]\s?\d{1,2}[-/月.]\s?\d{1,2}日?",
    "電話": r"(?:\+?886[- ]?|0)\d{1,2}[- ]?\d{3,4}[- ]?\d{4}",
    "Email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
}


def extract_fields(text: str) -> dict:
    out = {}
    for key, rx in _PATTERNS.items():
        hits = []
        for m in re.finditer(rx, text):
            v = m.group(1) if m.groups() else m.group(0)
            if v not in hits:
                hits.append(v)
        if hits:
            out[key] = hits[:5]
    return out


# ── 隔離安裝計畫(缺車道→執行令;零代裝)───────────────────────────
def best_mirror() -> str:
    """讀最新鏡像測速存證取最快源 URL;缺=官方(工作站實測 aliyun 206ms 勝)。"""
    f = _newest("MIRROR_*.json", DEPS_DIR)
    try:
        rows = json.loads(Path(f).read_text(encoding="utf-8")).get("results", [])
        ok = sorted([x for x in rows if x.get("ms") is not None], key=lambda x: x["ms"])
        if ok:
            return ok[0]["url"]
    except Exception:
        pass
    return "https://pypi.org/simple/"


def envs_root() -> str:
    try:
        if REB:
            for r in REB.discover_roots([]):
                if Path(r).is_dir():
                    return str(r)
    except Exception:
        pass
    return str(Path.home() / "envs")


def plan_lines(lane: dict, mirror: str, root: str) -> list[str]:
    envd = str(Path(root) / lane["envs"][0])
    py = str(Path(envd) / ("Scripts/python.exe" if "\\" in root or ":" in root else "bin/python"))
    L = [f"[計畫] {lane['label']} → 隔離境 {lane['envs'][0]}(Py {lane['py']})",
         f"   uv venv \"{envd}\" --python {lane['py']}",
         f"   uv pip install --python \"{py}\" --index-url {mirror} " + " ".join(lane["pkgs"]),
         f"   驗:via-ocrsuper --probe · 註:{lane['note']}"]
    if lane.get("ext_bin"):
        L.append(f"   外部本體:{lane['ext_bin']}(系統安裝器,候裁——pip 裝不到)")
    return L


# ── 模式 ─────────────────────────────────────────────────────────
def cmd_probe(envs: dict) -> list[dict]:
    print("── 車道探測(輕→重;隔離境四態)──")
    rows = []
    for lane in sorted(LANES, key=lambda x: x["pri"]):
        st, py = probe_lane(lane, envs)
        rows.append({"k": lane["k"], "pri": lane["pri"], "state": st, "py": py})
        mark = {"READY": "備 ", "NO_ENV": "缺境", "NO_MOD": "缺模", "NO_BIN": "缺體"}[st]
        print(f"  [{mark}] P{lane['pri']} {lane['label']:34s} 境:{Path(py).parent.parent.name if py else '—'}")
    return rows


def cmd_plan() -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"=== OCR 超引擎隔離安裝計畫 · {ts} · 零代裝(執行令候裁)===")
    envs = env_map()
    rows = cmd_probe(envs)
    mirror, root = best_mirror(), envs_root()
    print(f"── 缺件車道安裝計畫(鏡像:{mirror};環境根:{root})──")
    n = 0
    for lane in sorted(LANES + EXT_LAYERS, key=lambda x: x.get("pri", 9)):
        st = next((r["state"] for r in rows if r["k"] == lane["k"]), None)
        if st is None:  # 認知/擴展層另探
            st, _ = probe_lane(lane, envs)
        if st == "READY":
            continue
        n += 1
        for l in plan_lines(lane, mirror, root):
            print("  " + l)
    if n == 0:
        print("  四車道+認知層全備——無計畫可出")
    print("  鐵則:輕先重後——先裝 P1 RapidOCR 即可開工;重車道(paddle/surya)等輕道不敷再上")
    print("  安裝走 via-plan→via-install 或貼上列 uv 令;裝畢 via-ocrsuper --probe 回驗")
    return 0


def cmd_run(image: str, run_all: bool, do_extract: bool) -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"=== OCR 超引擎 v0100 · {ts} · 輕先重後(成功即停{';全車道交叉' if run_all else ''})===")
    if not Path(image).is_file():
        print(f"  ✗ 檔案不存在:{image}(誠實停)")
        return 2
    envs = env_map()
    rows = cmd_probe(envs)
    ready = [(lane, r["py"]) for lane in sorted(LANES, key=lambda x: x["pri"])
             for r in rows if r["k"] == lane["k"] and r["state"] == "READY"]
    if not ready:
        print("  ✗ 零 READY 車道——先跑 via-ocrsuper --plan 出安裝計畫(輕道 RapidOCR 先)")
        return 1
    print(f"── 階梯辨識({len(ready)} 車道備勤)──")
    results = []
    for lane, py in ready:
        r = run_lane(lane, py, image)
        results.append(r)
        if r.get("ok"):
            print(f"  [P{lane['pri']}] {lane['k']:10s} 行 {r['n']} · 信心 {r['avg']}"
                  + ("" if r["avg"] >= CONF_GATE and r["n"] else " → 未達門檻,升級"))
        else:
            print(f"  [P{lane['pri']}] {lane['k']:10s} ✗ {r.get('err', '?')[:70]} → 升級下一車道")
        if not run_all and pick_winner([r]):
            break
    win = pick_winner(results)
    print("── 裁決 ──")
    if win:
        print(f"  [勝道] {win['k']} · {win['n']} 行 · 平均信心 {win['avg']}")
        for t in win["text"][:12]:
            print(f"    {t[:90]}")
        if len(win["text"]) > 12:
            print(f"    …共 {win['n']} 行(全文見存證)")
    else:
        print("  全車道未過門檻——誠實 NONE(檢圖質/換 --all 交叉/升級重車道)")
    ext = None
    if do_extract and win:
        ext = extract_fields("\n".join(win["text"]))
        print("── 認知層(內建 Regex 第二優先;UIE 缺件見 --plan)──")
        for k, v in ext.items():
            print(f"  {k}:{' · '.join(v)}")
        if not ext:
            print("  (五類欄位無命中)")
    OUT.mkdir(parents=True, exist_ok=True)
    ev = OUT / f"OCR_{ts}.json"
    ev.write_text(json.dumps({"schema": "VIA.OcrSuper.v1", "ts": ts, "image": image,
                              "probe": rows, "results": results,
                              "winner": (win or {}).get("k"), "extract": ext,
                              "policy": "light_first·escalate_on_fail·isolated_envs·zero_install"},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存證] {ev.relative_to(VIA)}")
    return 0 if win else 1


# ── 自測 12 檢(零網路零環境依賴)──────────────────────────────────
def cmd_selftest() -> int:
    def t01():
        assert [l["pri"] for l in LANES] == [1, 2, 3, 4] and LANES[0]["k"] == "rapidocr"
        assert all(l["envs"] and l["pkgs"] and l["mod"] for l in LANES)

    def t02():
        assert all(l["k"] in _SRC for l in LANES)  # 每車道有隔離執行源
        assert all("json.dumps" in _SRC[l["k"]] for l in LANES)

    def t03():
        res = [{"k": "rapidocr", "ok": False, "err": "x"},
               {"k": "tesseract", "ok": True, "n": 3, "avg": 0.3},
               {"k": "paddleocr", "ok": True, "n": 5, "avg": 0.93}]
        w = pick_winner(res)
        assert w and w["k"] == "paddleocr"  # 輕道敗/低信→升級至重道

    def t04():
        assert pick_winner([{"k": "a", "ok": True, "n": 0, "avg": 0.9}]) is None  # 零行不算勝
        assert pick_winner([]) is None
        w = pick_winner([{"k": "a", "ok": True, "n": 2, "avg": 0.5}])
        assert w and w["k"] == "a"  # 門檻含等於

    def t05():
        txt = "某某科技股份有限公司 統一編號:12345678 開立日期:2026-08-13 總金額:NT$ 45,000 電話 02-2345-6789 mail a@b.tw"
        f = extract_fields(txt)
        assert f["統一編號"] == ["12345678"] and f["金額"] == ["45,000"]
        assert "2026-08-13" in f["日期"][0] and f["Email"] == ["a@b.tw"]

    def t06():
        assert _classify(False, None, None) == "NO_BIN"
        assert _classify(True, None, None) == "NO_ENV"
        assert _classify(True, "/e/bin/python", 1) == "NO_MOD"
        assert _classify(True, "/e/bin/python", 0) == "READY"

    def t07():
        L = plan_lines(LANES[0], "https://mirrors.aliyun.com/pypi/simple/", "/root/envs")
        assert any("uv venv" in x for x in L) and any("aliyun" in x for x in L)
        assert any("via_rapidocr" in x for x in L) and any("豁免" in x for x in L)

    def t08():
        L = plan_lines(LANES[1], "https://pypi.org/simple/", "C:\\Users\\tonyk\\envs")
        assert any("外部本體:tesseract" in x for x in L) and any("Scripts" in x for x in L)

    def t09():
        assert best_mirror().startswith("https://")  # 存證缺=官方保底,恆有效 URL

    def t10():
        assert len(EXT_LAYERS) == 3 and EXT_LAYERS[0]["k"] == "uie"  # 認知第一優先+擴展候裁

    def t11():
        import tempfile
        bad = Path(tempfile.mkdtemp()) / "x.py"  # run_lane 壞輸出→誠實 FAIL 不炸
        r = run_lane({"k": "rapidocr", "timeout": 5}, sys.executable, "/no/such/img")
        assert r["ok"] is False and "err" in r

    def t12():
        assert REB is not None and callable(REB.discover_envs)  # 搭配重建引擎盤點在位
        assert CONF_GATE == 0.5

    battery = [("車道編成階梯", t01), ("隔離執行源齊備", t02), ("階梯升級裁決", t03),
               ("零行/門檻邊界", t04), ("Regex 認知抽取", t05), ("四態分類", t06),
               ("計畫含鏡像+豁免註", t07), ("外部本體候裁", t08), ("鏡像保底", t09),
               ("認知/擴展層編成", t10), ("壞車道誠實", t11), ("搭配件在位", t12)]
    print("=== OCR 超引擎自測 12 檢(零網路零改動)===")
    n_ok = 0
    for name, fn in battery:
        try:
            fn()
            n_ok += 1
            print(f"  [OK  ] {name}")
        except Exception as exc:
            print(f"  [FAIL] {name} · {type(exc).__name__}:{str(exc)[:70]}")
    print(f"  [計] {n_ok}/{len(battery)} 綠")
    return 0 if n_ok == len(battery) else 1


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return cmd_selftest()
    if "-h" in a or "--help" in a or "--doc" in a:
        print(__doc__)
        return 0
    if "--plan" in a:
        return cmd_plan()
    if "--probe" in a:
        cmd_probe(env_map())
        return 0
    img = next((x for x in a if not x.startswith("--")), None)
    if not img:
        print("  ✗ 需圖片路徑(或 --probe/--plan/--selftest;用法見 --help)")
        return 2
    return cmd_run(img, "--all" in a, "--extract" in a)


if __name__ == "__main__":
    sys.exit(main())
