"""VRN2_UIAction v0103 — VRN-2 U/I 操作協定 vrn2:// 的處理器(由 ActivateVRN-2 註冊到目前使用者 HKCU · 不碰 via://)。

v0103(操作員 2026-10-21:「用 ActivateVRN-2.ps1 啟動前後端並連結 · 讓使用者在 HTML 上用 window I/O 輸入檔案夾或檔案(pdf / word / txt / image / 檔案夾)·
      分三種:個股報告/訊息 · 產業報告/展望 · 其他投資報告 · 現在進行的是個股報告/訊息,其他功能關閉」):
  vrn2://pick?kind=folder&cat=stock   Windows 原生對話框選資料夾 → 稽核(型別 / 個股範圍)→ VIA_Reports\\vrn2\\VRN2_Input_latest.json → U/I 左側「輸入」區塊 → 重開 U/I
  vrn2://pick?kind=files&cat=stock    原生對話框多選檔(pdf / docx / doc / txt / png / jpg / jpeg / tif / tiff / bmp)→ 複製到 VIA_Reports\\vrn2\\input_pick\\<時間>\\ → 同上
  vrn2://audit                        重新稽核目前輸入(不開對話框)
  cat 只開放 stock;industry / other 一律拒絕「尚未開放」(U/I 上 disabled)。啟動器 ②b 讀 VRN2_Input_latest.json 當來源夾(寫新一版 VRN2_SSOT · 管理器不動)。
  --set-source <夾> [--how <來源>] [--v2 <輸出根>]   啟動器 ②b:來源夾 → 紀錄 + 稽核(與 U/I 同一把尺)· 印 JSON(--v2 = 設定檔還沒寫之前由啟動器直接給)
  --refresh-ui                        啟動器 ⑫b:⑦ 重寫 U/I 後把輸入區塊補回(同一塊 · 不疊加)
  --audit <夾|檔…> · --selftest
  v0102 的 run / run?nopush=1 / run-clean / restore-archive 照舊(帶 VRN2_FROM_UI=1 · 新主控台)。
只接受白名單動作;路徑取自啟動器寫的 VRN2_UIAction_Config.json 與對話框實際選到的,不從網址讀路徑。
型別照 ENG397 的 EXT;本版 VRN-2 主體只擷取 PDF,非 PDF 照實記「已收下 · 本版主體只擷取 PDF」(不假裝有處理)。
個股 / 範圍外:檔名規則取管理器 v0231 的 _SK_EXCL(同一條 · 從檔案文字讀 · 不 import)+ 上輪判定 VRN2_Scope_latest.json non_stock。
測試掛鉤:VRN2_PICK_PATH(資料夾)· VRN2_PICK_FILES(以 | 分隔)· VRN2_UIACTION_DRY=1 只印 run 類指令。動作寫入 ui_actions.log。
"""

# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====
import ast
import datetime
import html as _html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

VERSION = "VRN2_UIAction v0103"
HERE = Path(__file__).resolve().parent
ACTIONS = {"run", "run-clean", "restore-archive", "pick", "audit"}
CATS = (("stock", "個股報告/訊息", True), ("industry", "產業報告/展望", False), ("other", "其他投資報告", False))   # 現在只開個股;其餘關閉(U/I 灰掉 · 處理器拒絕)
EXT = {".pdf": "PDF", ".docx": "WORD", ".doc": "WORD(舊)", ".txt": "TXT", ".png": "IMG", ".jpg": "IMG", ".jpeg": "IMG", ".tif": "IMG", ".tiff": "IMG", ".bmp": "IMG"}   # 同 ENG397 的 EXT(自測逐鍵核對)
INPUT_JSON, INPUT_HIST, UI_NAME = "VRN2_Input_latest.json", "VRN2_Input_History.jsonl", "VRN2_UI_latest.html"
_BLK_RE = re.compile(r"<!--vrn2-input-->.*?<!--/vrn2-input-->", re.S)
_EXCL_FALLBACK = r"(?i)晨會|早報|盤後|盤勢|ETF|籌碼|總經|論壇|第.場|專題|產業|[周週]報|解盤|股市分析"
_B = ("display:block;width:100%;box-sizing:border-box;margin:0 0 6px;padding:6px 8px;border:1px solid #d1d5db;border-radius:6px;background:#fff;color:#111;"
      "text-decoration:none;cursor:pointer;font:12px system-ui,'Microsoft JhengHei';text-align:left")
_PS_HEAD = "[Console]::OutputEncoding=[Text.Encoding]::UTF8; Add-Type -AssemblyName System.Windows.Forms; "
_PS_FOLDER = (_PS_HEAD + "$d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='VRN-2 · 選擇報告資料夾(個股報告/訊息)'; $d.ShowNewFolderButton=$false; "
              "if($d.ShowDialog() -eq 'OK'){ [Console]::Out.WriteLine($d.SelectedPath) }")
_PS_FILES = (_PS_HEAD + "$d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title='VRN-2 · 選擇報告檔(可多選 · pdf / word / txt / 影像)'; $d.Multiselect=$true; "
             "$d.Filter='報告 (pdf docx doc txt png jpg jpeg tif tiff bmp)|*.pdf;*.docx;*.doc;*.txt;*.png;*.jpg;*.jpeg;*.tif;*.tiff;*.bmp|所有檔案 (*.*)|*.*'; "
             "if($d.ShowDialog() -eq 'OK'){ $d.FileNames | ForEach-Object { [Console]::Out.WriteLine($_) } }")


def parse(url: str) -> tuple:
    """vrn2://<動作>?k=v&… → (動作, {k: v});不是 vrn2:// → ("", {})。"""
    u = urllib.parse.urlparse((url or "").strip().strip('"'))
    act = (u.netloc + u.path).strip("/").lower()
    q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
    return (act if u.scheme == "vrn2" else ""), q


def excl_rule(vrn: Path) -> tuple:
    """個股範圍外的檔名規則 = 管理器 v0231 的 _SK_EXCL(從檔案文字讀同一條 · 不 import VRN-2 程式)· 找不到 → 內建備援。回 (regex, 來源)。"""
    for p in sorted(Path(vrn).glob("VRN_SystemManager_v[0-9][0-9][0-9][0-9].py")):
        try:
            m = re.search(r'_SK_EXCL = re\.compile\(r"([^"]*)"\)', p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            m = None
        if m:
            try:
                return re.compile(m.group(1)), p.name
            except re.error:
                continue
    return re.compile(_EXCL_FALLBACK), "內建備援"


def audit(paths: list, vrn: Path, v2: Path) -> dict:
    """輸入稽核(只讀 · 不動輸入):資料夾遞迴(同管理器 vrn2scope)· 型別照 EXT · PDF 依檔名規則 + 上輪判定(VRN2_Scope_latest non_stock)分 個股 / 範圍外 ·
    非 PDF 照實記「已收下 · 本版主體只擷取 PDF」· 不認得的副檔名另計。"""
    rx, rule = excl_rule(vrn)
    try:
        nons = set(json.loads((Path(v2) / "VRN2_Scope_latest.json").read_text(encoding="utf-8")).get("non_stock") or [])
    except Exception:  # noqa: BLE001
        nons = set()
    files = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files += sorted([x for x in p.rglob("*") if x.is_file()], key=lambda x: x.name)
        elif p.is_file():
            files.append(p)
    by_type, stock, out, non_pdf, other = {}, [], [], [], 0
    for f in files:
        t = EXT.get(f.suffix.lower())
        if t is None:
            other += 1
            continue
        by_type[t] = by_type.get(t, 0) + 1
        if t != "PDF":
            non_pdf.append(f.name)
        elif f.name in nons or rx.search(f.name):
            out.append(f.name)
        else:
            stock.append(f.name)
    a = {"files": len(files), "by_type": by_type, "stock": len(stock), "out_of_scope": len(out), "non_pdf": len(non_pdf), "other_type": other,
         "stock_names": stock[:200], "out_names": out[:50], "non_pdf_names": non_pdf[:50], "rule": rule, "prev_non_stock": len(nons)}
    a["line"] = audit_line(a)
    return a


def audit_line(a: dict) -> str:
    bt = a.get("by_type") or {}
    return "檔 %d(PDF %d · Word %d · TXT %d · 影像 %d%s)· 個股範圍 %d · 範圍外 %d(產業 / 其他 · 檔名規則 %s + 上輪判定 %d)· 非 PDF %d(已收下 · 本版主體只擷取 PDF)" % (
        a.get("files", 0), bt.get("PDF", 0), bt.get("WORD", 0) + bt.get("WORD(舊)", 0), bt.get("TXT", 0), bt.get("IMG", 0),
        (" · 其他型別 %d" % a["other_type"]) if a.get("other_type") else "", a.get("stock", 0), a.get("out_of_scope", 0), a.get("rule", "—"),
        a.get("prev_non_stock", 0), a.get("non_pdf", 0))


def _ps_dialog(script: str) -> tuple:
    """Windows 原生對話框(System.Windows.Forms · STA 執行緒)。回 (有沒有真的開成, 選到的路徑清單;取消 → [])。"""
    if os.name != "nt":
        return False, []
    exe = shutil.which("powershell") or shutil.which("pwsh")
    if not exe:
        return False, []
    try:
        r = subprocess.run([exe, "-NoProfile", "-STA", "-Command", script], capture_output=True, timeout=900)
    except (OSError, subprocess.SubprocessError):
        return False, []
    out = r.stdout.decode("utf-8", "replace") if r.stdout else ""
    return r.returncode == 0, [l.strip() for l in out.splitlines() if l.strip()]


def _tk_dialog(kind: str) -> list:
    """備援:tkinter 對話框(沒有桌面 / 沒有 tkinter → [])。"""
    try:
        import tkinter
        from tkinter import filedialog
    except Exception:  # noqa: BLE001
        return []
    try:
        root = tkinter.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        if kind == "folder":
            p = filedialog.askdirectory(title="VRN-2 · 選擇報告資料夾(個股報告/訊息)")
            out = [p] if p else []
        else:
            ft = [("報告", "*.pdf *.docx *.doc *.txt *.png *.jpg *.jpeg *.tif *.tiff *.bmp"), ("所有檔案", "*.*")]
            out = list(filedialog.askopenfilenames(title="VRN-2 · 選擇報告檔(可多選)", filetypes=ft))
        root.destroy()
        return out
    except Exception:  # noqa: BLE001
        return []


def pick_paths(kind: str) -> tuple:
    """window I/O:測試掛鉤(VRN2_PICK_PATH 資料夾 · VRN2_PICK_FILES 以 | 分隔)→ Windows 原生對話框 → tkinter 備援。回 (路徑清單, 用的是哪一種)。"""
    if kind == "folder" and os.environ.get("VRN2_PICK_PATH"):
        return [os.environ["VRN2_PICK_PATH"]], "測試掛鉤"
    if kind == "files" and os.environ.get("VRN2_PICK_FILES"):
        return [x for x in os.environ["VRN2_PICK_FILES"].split("|") if x], "測試掛鉤"
    ran, got = _ps_dialog(_PS_FOLDER if kind == "folder" else _PS_FILES)
    if ran:
        return got, "Windows 對話框"
    got = _tk_dialog(kind)
    return got, ("tkinter 對話框" if got else "取消 / 開不了對話框")


def stage_files(paths: list, v2: Path) -> tuple:
    """多檔 → VIA_Reports\\vrn2\\input_pick\\<時間>\\(複製 · 原檔不動)。回 (暫存夾, 份數)。"""
    d = Path(v2) / "input_pick" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    d.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in paths:
        p = Path(p)
        if p.is_file():
            shutil.copy2(str(p), str(d / p.name))
            n += 1
    return d, n


def read_input(v2: Path) -> dict:
    try:
        return json.loads((Path(v2) / INPUT_JSON).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def record_input(v2: Path, cat: str, kind: str, how: str, src: Path, picked: list, staged: int = 0, vrn: Path = None) -> dict:
    """輸入紀錄(U/I 選的 / 啟動器 --set-source 都走這裡 · 同一把稽核尺)→ VRN2_Input_latest.json + 只增的 VRN2_Input_History.jsonl。"""
    v2 = Path(v2)
    v2.mkdir(parents=True, exist_ok=True)
    label = dict((c, l) for c, l, _ in CATS).get(cat, cat)
    rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "version": VERSION, "cat": cat, "cat_label": label, "kind": kind, "how": how,
           "source_dir": str(src), "picked": [str(p) for p in picked][:200], "staged": staged, "audit": audit([src], vrn or HERE, v2)}
    rec["audit_line"] = rec["audit"]["line"]
    (v2 / INPUT_JSON).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    with (v2 / INPUT_HIST).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({k: rec[k] for k in ("ts", "cat", "kind", "how", "source_dir", "staged", "audit_line")}, ensure_ascii=False) + "\n")
    return rec


def render_block(v2: Path) -> str:
    """U/I 左側「輸入(window I/O)」區塊:三類(只有個股可選 · 另外兩類灰掉「尚未開放」)· 選擇檔案夾 / 選擇檔案 / 重新稽核(vrn2://)· 目前輸入與稽核。"""
    esc = lambda s: _html.escape(str(s if s is not None else ""))  # noqa: E731
    rec = read_input(v2)
    h = ["<!--vrn2-input--><div id='vrn2-input'><div style='font-weight:700;margin:8px 0 6px'>輸入(window I/O)</div>"]
    for c, l, on in CATS:
        h.append("<label style='display:block;margin:2px 0;font-size:12px%s'><input type='radio' name='vcat' value='%s'%s%s> %s%s</label>" % (
            "" if on else ";opacity:.55", c, " checked" if on else "", "" if on else " disabled", l, "" if on else " <small>(尚未開放)</small>"))
    h.append("<a class='vinp' data-k='folder' style=\"%s\" href='vrn2://pick?kind=folder&amp;cat=stock'>📁 選擇檔案夾…</a>" % _B)
    h.append("<a class='vinp' data-k='files' style=\"%s\" href='vrn2://pick?kind=files&amp;cat=stock'>📄 選擇檔案…(pdf / word / txt / 影像)</a>" % _B)
    h.append("<a class='vinp' data-k='audit' style=\"%s\" href='vrn2://audit'>🔎 重新稽核輸入</a>" % _B)
    if rec:
        kind = "資料夾" if rec.get("kind") == "folder" else "檔案 %d 份 → 暫存夾" % len(rec.get("picked") or [])
        h.append("<div id='vrn2-input-now' style='font-size:11px;color:#374151;line-height:1.45;margin:4px 0 8px;word-break:break-all'>目前 · %s · %s(%s)<br>%s<br>%s<br>選好後按上面「▶ 完整重跑」· %s</div>" % (
            esc(rec.get("cat_label")), esc(kind), esc(rec.get("how")), esc(rec.get("source_dir")), esc(rec.get("audit_line")), esc(rec.get("ts"))))
    else:
        h.append("<div id='vrn2-input-now' style='font-size:11px;color:#6b7280;margin:4px 0 8px'>還沒選過 · 用啟動器預設 / VRN2_SSOT 的來源夾</div>")
    h.append("<div style='color:#6b7280;font-size:11px;margin:0 0 8px'>vrn2:// 沒反應 → PowerShell:<code>$env:VRN2_SOURCE='C:\\測試樣本報告'</code> 再跑一鍵,或 <code>python ActivateVRN-2.py --source C:\\測試樣本報告</code></div>")
    h.append("</div><!--/vrn2-input-->")
    return "".join(h)


def patch_ui(v2: Path) -> tuple:
    """把輸入區塊放進 U/I 左側面板(「開啟」標題之前)· 已有就換掉同一塊(不疊加)· 先寫暫存檔再換。回 (成功, 說明)。"""
    ui = Path(v2) / UI_NAME
    if not ui.exists():
        return False, "找不到 U/I %s" % ui
    page = ui.read_text(encoding="utf-8")
    blk = render_block(v2)
    if _BLK_RE.search(page):
        page = _BLK_RE.sub(lambda m: blk, page, count=1)
        where = "換掉同一塊"
    else:
        k = page.find("<div style='font-weight:700;margin:8px 0 6px'>開啟</div>", page.find("id='vrn2panel'"))
        if k < 0:
            k = page.rfind("</body>")
        if k < 0:
            page += blk
        else:
            page = page[:k] + blk + page[k:]
        where = "新放進面板"
    tmp = ui.with_name(ui.name + ".inp.tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(ui)
    return True, "U/I 輸入區塊 %s(三類 · 只開個股報告/訊息)" % where


def open_ui(v2: Path) -> str:
    up = Path(v2) / UI_NAME
    if not up.exists():
        return "找不到 U/I"
    if os.environ.get("VIA_NO_OPEN") == "1" or not hasattr(os, "startfile"):
        return "%s(沒有自動開啟)" % up
    try:
        os.startfile(str(up))  # noqa: S606
        return "%s(已重新開啟)" % up
    except OSError as exc:
        return "%s(開不了 %s)" % (up, type(exc).__name__)


def pick(cfg: dict, v2: Path, q: dict, vrn: Path = None) -> int:
    """vrn2://pick?kind=folder|files&cat=stock:只開個股;對話框選 → (多檔先複製到暫存夾)→ 紀錄 + 稽核 → U/I 區塊 → 重開 U/I。回 0 選好 / 取消 · 2 參數錯 · 3 尚未開放。"""
    v2, vrn = Path(v2), Path(vrn or HERE)
    cat, kind = (q.get("cat") or "stock").lower(), (q.get("kind") or "folder").lower()
    label = dict((c, l) for c, l, _ in CATS).get(cat, cat)
    if cat not in [c for c, _, on in CATS if on]:
        _log(v2, "拒絕 · 尚未開放", cat)
        print("[YELLOW] %s 尚未開放(現在只做 個股報告/訊息)" % label)
        return 3
    if kind not in ("folder", "files"):
        print("[RED] kind 只接受 folder / files")
        return 2
    paths, how = pick_paths(kind)
    paths = [p for p in paths if Path(p).exists()]
    if not paths:
        _log(v2, "取消 · pick %s" % kind, how)
        print("[GRAY] 沒有選到(%s)· 輸入不變" % how)
        return 0
    staged = 0
    if kind == "files":
        src, staged = stage_files(paths, v2)
    else:
        src = Path(paths[0])
    rec = record_input(v2, cat, kind, "U/I 選的 · " + how, src, paths, staged, vrn)
    ok, msg = patch_ui(v2)
    where = open_ui(v2) if ok else "—"
    _log(v2, "pick %s · %s · %s" % (kind, label, src), {"picked": len(paths), "staged": staged, "audit": rec["audit_line"], "ui": msg})
    print("[GREEN] 輸入 · %s · %s · %s" % (label, src, rec["audit_line"]))
    print("[計] %s · %s" % (msg, where))
    return 0


def run_action(cfg: dict, v2: Path, act: str, q: dict) -> int:
    """v0102 的動作照舊:run / run?nopush=1 / run-clean / restore-archive → 新主控台開啟動器(VRN2_FROM_UI=1)。VRN2_UIACTION_DRY=1 只印指令。"""
    v2 = Path(v2)
    nopush = bool(q.get("nopush"))
    env = dict(os.environ, VRN2_FROM_UI="1")
    if nopush:
        env["VIA_VRN2_NO_PUSH"] = "1"
    cmd = [cfg["python"], cfg["launcher"]] + (["--restore-archive"] if act == "restore-archive" else [])
    cleared = []
    if act == "run-clean" and os.environ.get("VRN2_UIACTION_DRY") != "1":
        for d in ("p1_cache", "acc_cache"):
            if (v2 / d).is_dir():
                shutil.rmtree(str(v2 / d), ignore_errors=True)
                cleared.append(d)
    if os.environ.get("VRN2_UIACTION_DRY") == "1":
        print(json.dumps({"act": act, "nopush": nopush, "cmd": cmd, "clear": ["p1_cache", "acc_cache"] if act == "run-clean" else [], "from_ui": env.get("VRN2_FROM_UI")}, ensure_ascii=False))
        return 0
    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0) if os.name == "nt" else 0
    subprocess.Popen(cmd, env=env, cwd=str(Path(cfg["launcher"]).parent), creationflags=flags)
    _log(v2, act + (" · 不上船" if nopush else "") + ((" · 清快取 " + "、".join(cleared)) if cleared else ""), cmd)
    return 0


def _arg(argv: list, key: str, default: str = "") -> str:
    return argv[argv.index(key) + 1] if key in argv and argv.index(key) + 1 < len(argv) else default


def main(argv: list) -> int:
    if "--selftest" in argv:
        return selftest()
    cfg_p = HERE / "VRN2_UIAction_Config.json"
    if "--v2" in argv:                                                     # 啟動器叫的(②b 在 ⑥c 寫設定檔之前):輸出根直接給
        cfg, v2 = {}, Path(_arg(argv, "--v2"))
    else:
        try:
            cfg = json.loads(cfg_p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            print("[RED] 找不到 %s(請先執行一次 ActivateVRN-2)" % cfg_p)
            return 2
        v2 = Path(cfg["v2"])
    if "--audit" in argv:                                                  # 只稽核 · 印 JSON(不寫紀錄)
        print(json.dumps(audit(argv[argv.index("--audit") + 1:], HERE, v2), ensure_ascii=False))
        return 0
    if "--set-source" in argv:                                             # 啟動器 ②b:來源夾 → 紀錄 + 稽核(同一把尺)· 印 JSON
        src = Path(_arg(argv, "--set-source"))
        rec = record_input(v2, "stock", "folder", _arg(argv, "--how", "啟動器"), src, [src])
        print(json.dumps({k: rec[k] for k in ("ts", "cat", "kind", "how", "source_dir", "audit", "audit_line")}, ensure_ascii=False))
        return 0
    if "--refresh-ui" in argv:                                             # 啟動器 ⑫b:⑦ 重寫 U/I 後把輸入區塊補回
        ok, msg = patch_ui(v2)
        print(("[GREEN] " if ok else "[YELLOW] ") + msg)
        return 0 if ok else 1
    act, q = parse(argv[1] if len(argv) > 1 else "")
    if act not in ACTIONS:
        _log(v2, "拒絕", argv[1:] if len(argv) > 1 else "")
        print("[RED] 不支援的動作:%s(只允許 %s)" % (act or "空", "、".join(sorted(ACTIONS))))
        return 2
    if act == "pick":
        return pick(cfg, v2, q)
    if act == "audit":                                                     # 重新稽核目前輸入(不開對話框)
        rec = read_input(v2)
        src = rec.get("source_dir")
        if not src:
            books = sorted((HERE / "SSOT").glob("VRN2_SSOT_v[0-9][0-9][0-9][0-9].json"), key=lambda p: int(re.search(r"_v(\d{4})", p.name).group(1)))
            try:
                src = json.loads(books[-1].read_text(encoding="utf-8")).get("source_dir") if books else ""
            except Exception:  # noqa: BLE001
                src = ""
        if not src:
            print("[YELLOW] 沒有輸入紀錄也沒有 VRN2_SSOT 來源夾 · 先「選擇檔案夾」")
            return 1
        rec = record_input(v2, rec.get("cat") or "stock", rec.get("kind") or "folder", "重新稽核", Path(src), rec.get("picked") or [src], rec.get("staged", 0))
        ok, msg = patch_ui(v2)
        _log(v2, "audit · %s" % src, rec["audit_line"])
        print("[GREEN] %s · %s" % (src, rec["audit_line"]))
        print("[計] %s · %s" % (msg, open_ui(v2) if ok else "—"))
        return 0
    return run_action(cfg, v2, act, q)


def _log(v2: Path, what: str, detail) -> None:
    try:
        Path(v2).mkdir(parents=True, exist_ok=True)
        with (Path(v2) / "ui_actions.log").open("a", encoding="utf-8") as fh:
            fh.write("%s · %s · %s\n" % (datetime.datetime.now().isoformat(timespec="seconds"), what, json.dumps(detail, ensure_ascii=False, default=str) if not isinstance(detail, str) else detail))
    except OSError:
        pass


def selftest() -> int:
    import tempfile
    ok = tot = 0

    def chk(name, cond):
        nonlocal ok, tot
        tot += 1
        ok += bool(cond)
        print("  [%s] %s" % ("OK" if cond else "FAIL", name))
    chk("vrn2:// 解析:pick 帶 kind / cat · run?nopush=1 · 不是 vrn2 → 空",
        parse("vrn2://pick?kind=folder&cat=stock") == ("pick", {"kind": "folder", "cat": "stock"}) and parse("vrn2://run?nopush=1") == ("run", {"nopush": "1"})
        and parse("http://x/run")[0] == "" and parse("vrn2://restore-archive") == ("restore-archive", {}))
    e397 = sorted(HERE.glob("VRN_ENG397_P1Segment_v[0-9][0-9][0-9][0-9].py"))
    if e397:
        m = re.search(r"^EXT = (\{.*\})$", e397[-1].read_text(encoding="utf-8"), re.M)
        chk("型別表與 %s 的 EXT 逐鍵相同" % e397[-1].name, bool(m) and ast.literal_eval(m.group(1)) == EXT)
    keep = {k: os.environ.get(k) for k in ("VRN2_PICK_PATH", "VRN2_PICK_FILES", "VRN2_UIACTION_DRY", "VIA_NO_OPEN")}
    with tempfile.TemporaryDirectory(prefix="uia103-") as td:
        t = Path(td)
        vrn, v2, src = t / "VRN", t / "v2", t / "src"
        (vrn / "SSOT").mkdir(parents=True)
        (src / "sub").mkdir(parents=True)
        v2.mkdir()
        (vrn / "VRN_SystemManager_v0231.py").write_text('_SK_EXCL = re.compile(r"(?i)晨會|專題|產業|[周週]報")\n', encoding="utf-8")
        for n in ("A-2330 20250718.pdf", "B-6669 20251001.pdf", "20260916兆豐台灣產業專題-航太產業.pdf", "債券ETF周報.pdf", "note.txt", "memo.docx", "scan.png", "old.doc", "x.xlsx"):
            (src / n).write_bytes(b"x")
        (src / "sub" / "C-1319 20231011.pdf").write_bytes(b"x")
        (v2 / "VRN2_Scope_latest.json").write_text(json.dumps({"non_stock": ["B-6669 20251001.pdf"]}), encoding="utf-8")
        a = audit([src], vrn, v2)
        chk("稽核:遞迴 10 檔 · 型別照 EXT · 個股 2(A · sub/C)· 範圍外 3(專題 · ETF周報 · 上輪判定 B)· 非 PDF 4 · 其他型別 1 · 規則取自 v0231 → %s" % a["line"][:60],
            a["files"] == 10 and a["stock"] == 2 and a["out_of_scope"] == 3 and a["non_pdf"] == 4 and a["other_type"] == 1
            and a["by_type"] == {"PDF": 5, "TXT": 1, "WORD": 1, "IMG": 1, "WORD(舊)": 1} and a["rule"] == "VRN_SystemManager_v0231.py" and "sub" not in " ".join(a["stock_names"]))
        chk("v0231 不在 → 內建備援規則", excl_rule(t)[1] == "內建備援")
        cfg = {"python": sys.executable, "launcher": str(t / "ActivateVRN-2.py"), "v2": str(v2), "version": "x", "handler": "VRN2_UIAction_v0103.py"}
        (t / "ActivateVRN-2.py").write_text("print('x')\n", encoding="utf-8")
        (v2 / UI_NAME).write_text("<html><body><div id='vrn2panel'><div style='font-weight:700;margin-bottom:8px'>VRN-2 操作</div><a class='vact' data-a='run' href='vrn2://run'>▶ 完整重跑</a>"
                                  "<label><input type='checkbox' id='vnopush'> 這次不上船 GitHub</label><div style='font-weight:700;margin:8px 0 6px'>開啟</div></div><h2>a</h2></body></html>", encoding="utf-8")
        os.environ["VIA_NO_OPEN"] = "1"
        os.environ["VRN2_PICK_PATH"] = str(src)
        rc1 = pick(cfg, v2, {"kind": "folder", "cat": "stock"}, vrn)
        rec = read_input(v2)
        page = (v2 / UI_NAME).read_text(encoding="utf-8")
        chk("vrn2://pick 資料夾(掛鉤)→ 紀錄 VRN2_Input_latest.json(來源 = 選的夾 · 稽核在裡面)· U/I 面板補上輸入區塊(「開啟」之前 · 三類 · 只有個股可選 · 另外兩類 disabled)",
            rc1 == 0 and rec["source_dir"] == str(src) and rec["kind"] == "folder" and rec["audit"]["stock"] == 2 and page.count("id='vrn2-input'") == 1
            and page.count("name='vcat'") == 3 and page.count(" disabled") == 2 and page.count(" checked") == 1 and page.index("vrn2-input") < page.index("開啟</div>")
            and "vrn2://pick?kind=folder&amp;cat=stock" in page and "vrn2://pick?kind=files&amp;cat=stock" in page and "vrn2://audit" in page and str(src) in page)
        patch_ui(v2)
        page2 = (v2 / UI_NAME).read_text(encoding="utf-8")
        chk("再補一次 → 換掉同一塊(不疊加)· 面板其他按鈕不動", page2.count("id='vrn2-input'") == 1 and page2.count("vrn2://run'") == 1 and page2.count("vnopush") == 1 and "<h2>a</h2>" in page2)
        os.environ.pop("VRN2_PICK_PATH", None)
        os.environ["VRN2_PICK_FILES"] = "|".join([str(src / "A-2330 20250718.pdf"), str(src / "note.txt"), str(src / "scan.png"), str(src / "missing.pdf")])
        rc2 = pick(cfg, v2, {"kind": "files", "cat": "stock"}, vrn)
        rec2 = read_input(v2)
        chk("vrn2://pick 檔案(掛鉤 3 檔在 + 1 不在)→ 複製到 input_pick\\<時間>\\(原檔不動)· 稽核 PDF 1 · 非 PDF 2 · 歷史 2 筆",
            rc2 == 0 and rec2["kind"] == "files" and rec2["staged"] == 3 and Path(rec2["source_dir"]).parent.name == "input_pick" and rec2["audit"]["stock"] == 1
            and rec2["audit"]["non_pdf"] == 2 and (src / "note.txt").exists() and len((v2 / INPUT_HIST).read_text(encoding="utf-8").splitlines()) == 2)
        rc3 = pick(cfg, v2, {"kind": "folder", "cat": "industry"}, vrn)
        rc4 = pick(cfg, v2, {"kind": "folder", "cat": "other"}, vrn)
        rc5 = pick(cfg, v2, {"kind": "zip", "cat": "stock"}, vrn)
        chk("產業報告/展望 · 其他投資報告 → 拒絕(尚未開放 · rc 3)· kind 不對 → rc 2 · 紀錄不變", rc3 == 3 and rc4 == 3 and rc5 == 2 and read_input(v2)["kind"] == "files")
        os.environ.pop("VRN2_PICK_FILES", None)
        rc6 = pick(cfg, v2, {"kind": "folder", "cat": "stock"}, vrn)
        chk("沒有掛鉤、也開不了對話框(非 Windows / 無桌面)→ 當取消 · rc 0 · 紀錄不變", rc6 == 0 and read_input(v2)["kind"] == "files")
        rec3 = record_input(v2, "stock", "folder", "啟動器 --source", src, [src], vrn=vrn)
        chk("啟動器 --set-source 走同一支稽核 · how 記來源 · 區塊顯示它", rec3["how"] == "啟動器 --source" and rec3["audit"]["stock"] == 2 and "啟動器 --source" in render_block(v2))
        os.environ["VRN2_UIACTION_DRY"] = "1"
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_action(cfg, v2, "run", {"nopush": "1"})
            run_action(cfg, v2, "run-clean", {})
            run_action(cfg, v2, "restore-archive", {})
        plans = [json.loads(l) for l in buf.getvalue().splitlines() if l.startswith("{")]
        chk("v0102 動作照舊:run?nopush=1 → 不上船 · run-clean 清 p1_cache / acc_cache · restore-archive 帶 --restore-archive · 都帶 VRN2_FROM_UI",
            len(plans) == 3 and plans[0]["nopush"] and plans[1]["clear"] == ["p1_cache", "acc_cache"] and plans[2]["cmd"][-1] == "--restore-archive" and all(p["from_ui"] == "1" for p in plans))
    for k, v in keep.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    print("[計] %s 自測 %d/%d · %s" % (VERSION, ok, tot, "PASS" if ok == tot else "FAIL"))
    return 0 if ok == tot else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
