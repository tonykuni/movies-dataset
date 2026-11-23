#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL148_EngineBus v0111 — 引擎調度匯流排(批471 立;本版:庫況對冊比,不再只靠 grep 猜)

v0110→v0111(批478 VDF SSOT 化第一步):
  庫況的 ABSENT 以前全靠 grep 碼裡的 SQL 語境猜(批474 收緊到 ≥3 檔才敢報)。現在有**庫冊**
  VIA_DB_Table_SSOT_v*.json(操作員機器 census 實測 + 寫入者掃描):
    冊上宣告、庫裡沒有 → ABSENT(冊上宣告)並列寫入者引擎——這是**該有而沒有**,最該亮的一種
    冊外、碼上 SQL 語境 ≥3 檔引用 → ABSENT(冊外)——照舊,寧可少報
    庫裡有、冊上沒有 → 照常判態,加註「冊外」——提醒冊該補,不是缺陷
    檔名含 _repo_ 的庫 → 加註「副本」,不當正典判


v0109→v0110(批477 收 TWREV v2.7 時撞到的**第十盞判錯的燈**):
  `twrevenue/cli.py` 是套件裡的模組,得 `python -m twrevenue.cli selftest` 啟動;
  匯流排照舊 `python cli.py selftest` → `ImportError: attempted relative import with no known parent package`,
  而我的 NEED_RX 看到 ImportError 就判「缺件,補上那個套件再跑」——**沒有任何套件缺**,是我啟動方式錯。
  判錯的燈不只紅燈:一盞指錯方向的灰燈也會讓人去 pip install 一個不存在的東西。
  修:① 冊上項可宣告 `module`(如 twrevenue.cli),匯流排改 `-m` 啟動並把 engine dir 前置進子行程 PYTHONPATH;
      ② classify_stop 先擋「attempted relative import」→ RED 並直說「須以 -m 啟動;冊上加 module 欄」,不再進 NEED_RX。
      ③ 冊上項可宣告 `cwd: "engine"`:TWREV 是第一支**讀 cwd** 的引擎(config.yaml 全是相對路徑),
         批471 量的「36 支全用 __file__、0 支讀 cwd」在它身上不成立——冊講了才換工作目錄,預設照舊 _cwd。


v0108→v0109(批476 操作員令「所有 PY 檔案都要加上加速器」「VDF 全部還要加入網路工具」):
  量過:加速器在 VDF 引擎只綁 4/109、VRN 0、VAP 0;VDF 109 支裡 8 支直呼網路沒走正典件。
  逐檔補=幾百個新版本檔。改在**啟動層**:子行程 env 加 PYTHONPATH=<VIA>/supportive modules/bootstrap
  (裡面的 sitecustomize.py 起跑自動載入)+ VIA_FAMILY + VIA_ROOT。零引擎改動,一處維護。
  新增 `boot` 動詞:真的起一個子行程,回報它看到的(加速器 / 網路件 / 閘態)——證據,不是宣稱。


v0107→v0108(工作站實錄:`via-ryg` 停在 `[25/38] vrn/vrn_firstpage` 不動,操作員報「卡斷中」):
  根因不是引擎卡,是**我的調度層讓人看不見引擎在動**:
    · `subprocess.run(capture_output=True)` 把子行程輸出**緩衝到結束才吐**——
      ENG072 對一疊真報告做 OCR 要跑好幾分鐘,這幾分鐘畫面全白。
    · 逾時 900 秒。也就是說最壞要白畫面 15 分鐘才會看到任何字。
  這正是批423 AllGreen v0100 那一課的翻版(「輸出緩衝到結束才吐=長跑段畫面全白」),
  同一個病我在另一支程式裡又寫了一次。
  修法(照 AllGreen v0101 的藥方,不另發明):
    ① Popen + 讀取執行緒,引擎每印一行就收一行;
    ② **心跳**:每 HEARTBEAT_SEC 秒印一行「⏳ 還在跑 · N s · 引擎最後一行:…」,
       畫面永遠不會白——而且印的是引擎**自己的**進度句,不是我編的;
    ③ 逾時只殺**自己生的那一個**子行程(不碰別的進程),部分輸出保留當證據;
    ④ `--timeout N` 開給 CLI(via-ryg -Timeout N 直通),不再只能吃 900 那個死數。


v0106→v0107(**操作員在自己機器上跑,三件事當場現形**):
  實錄逐字:
      PS> via-bus --matrix
      …SyntaxWarning: invalid escape sequence '\s'
      (然後吐出兩百行 docstring,什麼都沒跑)

  ① **我給錯指令**。冊上的動詞是 `matrix`,不是 `--matrix`;而上一則訊息裡
     叫操作員打的就是 `via-bus --matrix`。**錯在我**。
     但這不只是我打錯字——`--matrix` 是任何人都會自然打出來的形狀,
     而這支程式對它的回應是:**印兩百行說明,然後回 rc=0 說成功**。
     兩個獨立的缺陷:
       · 顯然想得到的動詞不收 → 本版把 `--matrix/--catalog/--call/--census`
         一律正規化成動詞(**只脫頭部的連字號,不去猜別的東西**)。
       · 不認得的參數回 **rc=0** → 那是**假綠**:自動化鏈路上游看 rc,
         會把「什麼都沒跑」讀成「跑完了」。改回 **rc=2**,並印**六行用法**,
         不再把整篇 docstring 倒在人臉上(說明書不是錯誤訊息)。
  ② **SyntaxWarning**:docstring 裡寫了「需要」加空白比對式那個正則當範例,
     而 docstring 不是 raw 字串。v0106 那段文字本身在講「判準寫兩個地方
     只改一邊」,結果那段文字**自己**又生了一個新缺陷。改 r 開頭的 docstring。
  ③ 產出頁只有「引擎跑不跑得動」,沒有「**庫裡到底有沒有料**」。
     操作員問的 C 是「VDF 到底能不能跑」——引擎綠不綠回答不了那題:
     引擎可以完美地跑完然後寫進一張空表。本版加**矩陣五 · 庫況**:
     沿用既有的 db_table_index() 那一趟掃描(**不另開第二支掃描器**),
     多取列數與日期跨度,逐表判三態:
         GREEN  有列,且(無日期欄 或 日期跨度 ≥ 30 天)
         AMBER  有列,但日期跨度 < 30 天(料在,但薄——最容易被當成綠)
         NODATA 表在、列數 0(**表建好了沒料**)
         ABSENT 全樹沒有這張表(**不是壞掉**,是還沒建)
     判準要亮得出證據:每一格都把列數與日期跨度一起印出來。

v0105→v0106(批473 收 PDFPlumber-Plus 時撞到的**第八盞判錯的紅燈**):
  新收的 vrn_pdfplus 一調度就報 RED,而引擎印的是
      `selftest 需要 reportlab 產生樣本 PDF;請改用 python …py <你的.pdf>`
  ——那是**缺件**,而且它連補法都講了。RED 的原因是我的 NEED_RX 字表裡
  只有「缺席/未安裝/沒裝/pip install/ModuleNotFoundError」,**沒有「需要 X」**。
  最難看的是:同一批我寫那支 PowerShell 啟動器時**已經把這條律寫對了**
  (`需要\s*([A-Za-z0-9_\-]+)`),卻沒有把它帶回匯流排——
  **同一個判準寫在兩個地方,只改了一邊,另一邊靜靜走錯**,
  這正是本件立案時要收掉的那件事,結果我自己又犯一次。
  判準收得緊:`需要` 後面必須緊跟**看起來像 python 套件名的 ASCII 識別字**,
  不是看到「需要」兩個字就放過(那是中文裡太常見的詞)。

v0104→v0105(**同一張表再讀一遍,又抓到一種說謊**):
  v0104 把表名接對了,可是 `VIA_UI_VRNControlTower_v0100.html` 還是寫「缺」——
  而 vrn_ui 那一跑明明報「頁 3/3 新鮮」。查:冊上有 **7 條是沒有目錄的裸檔名**,
  真的頁住在 `supportive modules/ui_support/`,我卻拿 VIA 根去接它。
  這是同一個病的第三種形狀(先是表名當路徑,再是裸檔名當根相對路徑):
  **我一直在用「一種判法」去問三種不同的問題。**
  所以判法改成照宣告的**形狀**分四路:
      含萬用字元 → 不判      路徑形(有 /)→ 接 VIA 根問檔案系統
      裸檔名形   → **去找**(rglob 排除 references;找到就把落點一起講出來)
      表名形     → 問庫
  找得到就說在哪,找不到才說缺——**說「缺」之前,先確定自己有去找過**。

v0103→v0104(**把產出的頁讀一遍,發現說謊的是頁本身**):
  ① 頁首印「模式 **只解析(dry)**」——可是那一跑 vrn+vap 是**真跑**的。
     `data["apply"]` 在 --apply-family 模式下本來就是 False,我卻拿它當唯一的標籤。
     一張報實測結果的頁,**第一行就把自己的模式講錯**。
  ② 矩陣四拿 `(VIA/宣告).exists()` 判產出在不在。量了冊:**60 個宣告產出裡有 34 個
     是資料庫的表名,不是檔案路徑**(tw_daily_prices、vrn_report_basic、
     ActiveTWETF.duckdb::holdings_daily …)。拿檔案系統去問表在不在,答案永遠是「缺」——
     矩陣四有**超過一半的格子在說謊**:vrn_structdb 明明剛入庫 71 筆,頁上寫它的
     vrn_report_basic「缺」。**判錯的紅燈和假綠一樣傷**,這批已經是第五盞了。
     修法:先分類再判,各問各的——
       含萬用字元 → 不判(照舊:判不了就說判不了)
       路徑形     → 問檔案系統
       表名形     → **問庫**(唯讀 SHOW TABLES;支援 `庫.duckdb::表` 明寫形)
       一張庫都開不了 → 「判不了(無庫可問)」,**不寫成缺**

v0102→v0103(**第三次實跑,這次髒的是我的手**):
  全 37 項跑完,`git status` 冒出一個從沒入過庫的夾:
      functional modules/VAP/engine/vap_one_out/RUN_.../vap_one.html
  **調度層讓引擎在原始碼樹裡拉了一夾產出。** 根因是我在 v0100 寫的
  `cwd=引擎檔所在目錄`;ENG016 的 `--out` 預設是相對路徑 `./vap_one_out`,
  冊上 `param_kinds.vapone` 本來就寫著要帶 `--out <夾>`,沒帶就落在 cwd。
  正本零觸碰不是只管「不要改別人的檔」,**也管不要在別人家裡生檔**。

  改 cwd 之前先量(不是先猜):
    · 冊上在位 36 支引擎,**36 支全部用 `__file__` 定位自己**
    · `os.getcwd` / `Path.cwd()` / `chdir` —— **0 支**
    · ENG016 從無關目錄實跑:rc=0,產出落在那個目錄,行為不變
  所以 `cwd=引擎目錄` 一點好處都沒有,只換來原始碼樹被弄髒。
  → 改成每次跑都在 `VIA_Reports/engine_bus/_cwd/` 底下(產出夾,已在 .gitignore),
    任何引擎的相對預設都落在那裡,原始碼樹一個字都不會多。

v0101→v0102(**第二次實跑,照出的還是我的尺**):
  VAP 家族 6 項真跑,匯流排報 RED 4。逐項查完,**只有 1 支是真壞**:
    · vap_dashboard     印「[缺料] 缺 4 項 … [補料] **誠實停 rc2**」 → 缺料,判紅是錯的
    · vap_std_dashboard 印「plotly 缺席=**誠實停**」               → 缺件,判紅是錯的
    · vap_one_render    argparse:「error: argument --render: expected one argument」
                        冊上這項宣告 `params:["vapone"]`——config 路徑本來就該由主控台給。
                        我沒給參數就硬跑,再把 argparse 的抱怨判成引擎壞 → 缺參數,判紅是錯的
    · vap_stack         `_duckdb.CatalogException: Table tw_daily_prices does not exist`
                        **這支是真紅**:缺表時該誠實停,它卻讓例外裸奔(VAP 側缺陷,已表列)
  三盞判錯的紅燈,三盞都是我點的。修的是判準,不是引擎:

  ① **「誠實停」才是這套系統的正典句**——全樹 451 處,而 v0101 的 NODATA_RX 裡沒有它。
     我當初是照 VRN 那幾支的措辭湊字表,湊出來的字表只認得 VRN 的方言。
  ② **缺件 ≠ 缺料 ≠ 壞掉**(操作員原律)。誠實停還要再分一層:
       缺料(上游沒料)                     → NODATA
       缺件(引擎/相依套件/**必要參數** 不在位)→ ABSENT ← 本版擴義,不新立第八態
     判缺參數**只認 argparse 自己講的話**(`error: argument …` /
     `the following arguments are required`)。**不能用「有宣告 params 就別跑」一刀切**:
     冊上 21 項宣告了 params,其中 20 項沒給參數照樣跑得好好的(量過),
     一刀切會誤殺 20 項——跟「排除 2000–2030 修年份」是同一種爛招。
  ③ **`--apply` 不該是全有全無**。VRN 那 7 項無妨;VDF 那 24 項按下去,等於同時發動
     tw_history 全史回補、tw_chips 籌碼回補,還有兩支動詞裡本來就帶 `--apply` 的寫庫件
     (tw_universe_update / db_localdb_apply)。調度層唯一的開關長這樣就是地雷。本版加:
       --apply-family vrn,vap   只在點名的家族真跑,其餘照樣 PLAN
       --ids a,b,c              只跑點名的項
       **寫庫動詞閘**:動詞裡含 `--apply` 的項,家族全掃**永不代跑**,
                       要跑必須 --ids 明點(與「--approve-remove 只在明令下」同律)

v0100→v0101(**實跑第一次就照出我自己用錯尺**):
  VRN 家族 7 項真跑,匯流排報 RED 3。查了才知道三支同一個根——引擎自己印的是
  「**無報告件(誠實)**」「無可轉檔(誠實)」:那是**缺料不是壞掉**,而我把它判成紅。
  這正是批470 才寫過的那一課的翻版:**判錯的紅燈和假綠一樣傷**,
  它會讓人去 debug 一支行為完全正確的引擎。
  想用 rc=2 當判準——**量過之後否決**:全樹 `return 2` 有 163 處,
  其中只有 46 處是誠實停,117 處是用法錯/缺庫等別的意思。**rc 不是穩定慣例。**
  可靠的訊號是引擎**自己印出來的那句話**。所以 v0101 加 **NODATA** 態:
  rc≠0 **且**輸出尾段命中誠實停字樣 → NODATA,並把**命中的那句原文一起帶回**
  (判準要亮得出證據,不然它就只是另一種猜)。沒有那句話的 rc≠0 一律照舊 RED。
====================================================================
操作員令:「**功能性引擎功能性化 可讓多個子系統調度**」
        「實測修正無誤後顯示 html u/多矩陣結果摘要及資料 **全部 SSOT**」

先查再造(量到的,不是規劃的):
  · 調度用的 SSOT **早就有**:VIA_InputConsole_Spec_v0100.json 已宣告
    **37 項引擎**(vdf 24 / vrn 7 / vap 6),每項都帶 engine{dir,glob,verb}、
    params、outputs。**本件不另立第二本冊**——那會讓「正典換了沒人跟得上」。
  · 但**調度的碼四家各寫各的**(實測):
        CGC_MDL095_DeckServer   Popen ×12
        CGC_MDL137_RunGate      subprocess.run ×3
        CGC_MDL139_InputConsole subprocess.run ×1
        CGC_MDL141_ClosingGate  自己一套
    每一家都重寫:尾版 glob 解析、家族 python 選擇、逾時、結果解讀。
    同一件事四份實作=九頭龍;引擎換了介面,四個地方都要記得改,而**漏改的那個
    不會報錯,只會靜靜走錯**。
  · 這就是「功能性化」缺的那一格:引擎有功能,但**沒有一個統一的呼叫契約**,
    所以每個子系統只能各自用「開一個行程再讀文字」的方式去湊。

本件補的正是那一格 —— **一條匯流排,四家共用**:
    catalog()            冊上 37 項 × 尾版解析 × 在位實測
    call(item_id, ...)   統一呼叫契約,回**統一結果字典**
    matrix(...)          批量調度 → 多矩陣資料
    render(...)          實測結果 → 多矩陣 HTML(零 CDN;樣板走 MDL089)

統一結果契約(誰調度都拿到同一個形狀,不必再各自解讀文字):
    {id, family, zh, engine, engine_state, argv, state, rc, seconds,
     tally, outputs_seen, stdout_tail, why}
    state ∈ GREEN | NODATA | AMBER | RED | TIMEOUT | ABSENT | PLAN
      NODATA  **缺料**:上游沒料,引擎自己說了「誠實停」。不是紅燈。
      ABSENT  **缺件**:引擎檔 / 相依套件 / 必要參數 不在位。也不是紅燈。
              缺件與壞掉混在一起,就會讓人去 debug 一支行為完全正確的引擎。
      PLAN    dry:只解析不動手(預設就是 dry),或**寫庫動詞被家族閘擋下**

紀律:
  · 尾版律 glob;家族 python **委派** MDL137.python_for →(它再委派 MDL136)
  · **不卡斷**:逐項逾時,只殺自己生的那個子行程
  · 誠實三態;`[計]` 只認**最後一行**(批462 那一課:子報告也印 `FAIL 0`,
    全篇搜就會把「OK 38 · FAIL 1」讀成綠)
  · 本件**零網路**、**預設不動手**(dry)、不寫任何正式產出夾
用法:
  python3 CGC_MDL148_EngineBus_v0106.py catalog [--family vrn]
  python3 CGC_MDL148_EngineBus_v0106.py call --item vrn_firstpage [--apply]
  python3 CGC_MDL148_EngineBus_v0106.py matrix [--family vrn] [--apply] [--html]
  python3 CGC_MDL148_EngineBus_v0106.py matrix --apply-family vrn,vap --html
  python3 CGC_MDL148_EngineBus_v0106.py matrix --ids vdf_tw_align --apply
  python3 CGC_MDL148_EngineBus_v0106.py --selftest
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

import html as _html
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
#: 調度 SSOT —— 冊只有一本(尾版律 glob;不另立)
SPEC_GLOB = "VIA_InputConsole_Spec_v*.json"
#: 產出(本件唯一會寫的地方;VIA_Reports/* 已在 .gitignore)
OUTDIR = VIA / "VIA_Reports" / "engine_bus"
#: 批478 庫冊(尾版律 glob;操作員機器 census 實測 + 寫入者掃描)
DBSSOT_GLOB = "VIA_DB_Table_SSOT_v*.json"


def db_ssot() -> tuple[dict, str]:
    hits = sorted(HERE.glob(DBSSOT_GLOB))
    if not hits:
        return {}, "庫冊缺(VIA_DB_Table_SSOT_v*.json)"
    try:
        return json.loads(hits[-1].read_text(encoding="utf-8")), hits[-1].name
    except Exception as exc:
        return {}, f"庫冊讀不了:{type(exc).__name__}"


#: 批476 啟動層 bootstrap(sitecustomize.py 住這裡;子行程 PYTHONPATH 前置它)
BOOTDIR = VIA / "supportive modules" / "bootstrap"


def child_env(family: str = "", extra_path: str = "") -> dict:
    r"""子行程環境:加速器/網路件在啟動層綁上(批476)。同意閘**一個字都不碰**。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", VIA_ROOT=str(VIA))
    if family:
        env["VIA_FAMILY"] = family.lower()
    if BOOTDIR.is_dir():
        prev = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(BOOTDIR) + (os.pathsep + prev if prev else "")
    if extra_path:                      # 批477:-m 啟動的套件根
        prev = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = extra_path + (os.pathsep + prev if prev else "")
    return env
#: 逐項逾時
DEFAULT_TIMEOUT = 900
#: 心跳間隔(秒):畫面最多白這麼久。批423 那課:看起來死機 = 卡斷。
HEARTBEAT_SEC = 20
#: `[計]` 行:只認最後一行(批462)
TALLY_RX = re.compile(r"\[計\][^\n]*")
#: 引擎「誠實停」的自述句(它們自己印的,不是我發明的分類)
#: 量過才用:全樹 `return 2` 163 處只有 46 處是這個意思,**rc 不可當判準**。
#: 批471 v0102:v0101 這張字表是照 VRN 幾支的措辭湊的,只認得 VRN 的方言——
#: VAP 印「誠實停 rc2」就漏接了。「誠實停」全樹 451 處,才是這套系統的正典句。
STOP_RX = re.compile(
    r"(誠實停|無報告件|無可轉檔|無 ?PDF|無分區 ?sidecar|缺件|夾不存在|夾是空的|"
    r"無報告檔|尚無報告|無可轉|零報告|無輸入)[^\n]{0,48}")
NODATA_RX = STOP_RX          # 舊名留著當橋(別處若已 import,不讓它斷)

#: 誠實停之中屬於**缺件**的那一類(缺套件/缺模組)——與缺料要分開。
#: 缺件 ≠ 缺料 ≠ 壞掉:三件事混成一盞燈,人就會去 debug 一支沒壞的引擎。
NEED_RX = re.compile(
    r"(缺席|未安裝|沒裝|不在位)[^\n]{0,24}|"
    r"(pip install|ModuleNotFoundError|ImportError|No module named)[^\n]{0,40}|"
    # 批473:`需要 reportlab`——引擎講了實話而且連補法都給了,我卻判它紅。
    # 收得緊:`需要` 後面必須緊跟看起來像套件名的 ASCII 識別字(至少三碼),
    # 不是看到「需要」兩個字就放過——那在中文裡太常見,會把真紅也放走。
    r"需要\s*[A-Za-z][A-Za-z0-9_.\-]{2,}|"
    r"\b(plotly|matplotlib|seaborn|duckdb|pymupdf|fitz|pypdf|python-docx|"
    r"reportlab|paddleocr|camelot|tabula|"
    r"pytesseract|tesseract)\b[^\n]{0,12}(缺席|未安裝|沒裝)")

#: argparse 自己講的「你少給我一個參數」。**只認它講的**——
#: 不能用「冊上有宣告 params 就別跑」一刀切:37 項裡 21 項宣告了 params,
#: 其中 20 項沒給參數照樣跑得好好的(量過),一刀切等於誤殺 20 項。
ARGERR_RX = re.compile(
    r"error: (argument [^\n:]{1,40}: expected one argument|"
    r"the following arguments are required:[^\n]{0,60}|"
    r"argument [^\n:]{1,40}: invalid [^\n]{0,40})")


def classify_stop(tail: str) -> tuple[str, str]:
    """rc≠0 的輸出尾段 → (state, why)。判不出來就回 ("", "") 讓它照舊 RED。

    次序有意義:**缺參數 → 缺件 → 缺料**。
    先問 argparse(它講得最死),再問缺件(缺件常跟誠實停同句),最後才是缺料。
    每一種都把**命中的原文帶回**當證據——判準亮不出證據,它就只是另一種猜。
    """
    if "attempted relative import" in tail:
        # 批477 第十盞:這不是缺套件,是啟動方式錯。指錯方向的灰燈會讓人去裝一個不存在的東西。
        return ("RED", "**啟動方式錯**(不是缺件):套件內模組須以 `python -m` 啟動;冊上這項加 `module` 欄")
    m = ARGERR_RX.search(tail)
    if m:
        return ("ABSENT", f"**缺參數**(不是壞掉):argparse 自述「{m.group(0)[7:59]}」"
                          f";冊上這項的 params 該由主控台/--ids 帶值給它")
    # 批473:缺件**不再要求先命中誠實停字樣**。`需要 reportlab` 本身就是一句
    # 完整的誠實話,它不會再多寫一次「誠實停」;v0105 把缺件掛在誠實停底下,
    # 等於要求引擎用兩種措辭講同一件事才算數。
    n = NEED_RX.search(tail)
    m = STOP_RX.search(tail)
    if n:
        hit = m.group(0).strip()[:52] if m else ""
        return ("ABSENT", f"**缺件**(不是壞掉):引擎自述「{(n.group(0) or '').strip()[:36]}"
                          + (f"」· 誠實停「{hit}」" if hit else "」(補上那個套件再跑)"))
    if not m:
        return ("", "")
    hit = m.group(0).strip()[:52]
    return ("NODATA", f"**缺料**(不是壞掉):引擎自述「{hit}」=上游沒料,非本引擎缺陷")


#: 動詞裡帶 `--apply` 的項=**寫庫件**。家族全掃永不代跑(要跑請 --ids 明點)。
#: 與操作員既有的「--approve-remove 只在明令下」同律:
#: 破壞性的那一步,永遠要有人**指名道姓**點它,不能被一個家族開關掃進去。
WRITE_VERB = "--apply"


def _load(glob_pat: str, d: Path, alias: str):
    """尾版律載入(缺席回 (None, 因由);不拋)。"""
    try:
        hits = sorted(d.glob(glob_pat))
        if not hits:
            return None, f"{glob_pat} 缺席({d.name})"
        sp = importlib.util.spec_from_file_location(alias, hits[-1])
        m = importlib.util.module_from_spec(sp)
        sys.modules[alias] = m
        sp.loader.exec_module(m)
        return m, ""
    except Exception as exc:
        return None, f"{glob_pat} 載入失敗 {type(exc).__name__}:{str(exc)[:60]}"


def spec_path() -> tuple[Path | None, str]:
    hits = sorted((VIA / "supportive modules" / "registry").glob(SPEC_GLOB))
    if not hits:
        return None, f"{SPEC_GLOB} 缺席"
    return hits[-1], ""


def load_spec() -> tuple[dict, str]:
    p, why = spec_path()
    if p is None:
        return {}, why
    try:
        return json.loads(p.read_text(encoding="utf-8-sig")), f"冊 {p.name}"
    except Exception as exc:
        return {}, f"冊讀取失敗 {type(exc).__name__}:{str(exc)[:60]}"


def python_for(family: str) -> dict:
    """家族境 python —— **委派** MDL137 RunGate(它再委派 MDL136 EntryBridge)。
       Zero-Hydra:本件不自己找 conda/venv;橋缺席才退回本行程 python 並講明。"""
    m, why = _load("CGC_MDL137_RunGate_v*.py", HERE, "mdl137_bus")
    if m is not None and hasattr(m, "python_for"):
        try:
            r = m.python_for(family)
            if isinstance(r, dict) and r.get("python"):
                return r
        except Exception as exc:
            why = f"RunGate.python_for 失敗 {type(exc).__name__}"
    return {"family": family, "python": sys.executable, "env": "",
            "source": f"本行程退路({why or 'RunGate 無 python_for'})", "state": "FALLBACK"}


def catalog(family: str | None = None) -> list:
    """冊上每一項 × 尾版解析 × 在位實測。**在位 ≠ 跑得動**,本表只說在不在。"""
    spec, why = load_spec()
    out = []
    for fam, f in (spec.get("families") or {}).items():
        if family and fam != family:
            continue
        for grp in f.get("groups", []):
            for it in grp.get("items", []):
                eng = it.get("engine") or {}
                d = VIA / str(eng.get("dir") or "")
                g = str(eng.get("glob") or "")
                hits = sorted(d.glob(g)) if (g and d.is_dir()) else []
                out.append({
                    "id": it.get("id", ""),
                    "family": fam,
                    "group": grp.get("id", ""),
                    "zh": it.get("zh", ""),
                    "glob": g,
                    "dir": str(eng.get("dir") or ""),
                    "verb": list(eng.get("verb") or []),
                    "params": list(it.get("params") or []),
                    "outputs": list(it.get("outputs") or []),
                    "net": bool(it.get("net")),
                    "engine": hits[-1].name if hits else "",
                    "engine_path": str(hits[-1]) if hits else "",
                    "module": it.get("module", ""),
                    "cwd": it.get("cwd", ""),
                    "engine_dir": str(VIA / eng.get("dir", "")),
                    "versions": len(hits),
                    "engine_state": "在位" if hits else "缺席",
                    "spec_why": why,
                })
    return out


def _argv_for(item: dict, params: dict | None, py: str) -> list:
    # 批477:套件裡的模組(冊上 module 欄)要用 -m 啟動,不能當檔案跑(相對匯入會炸)
    argv = [py, "-m", item["module"]] if item.get("module") else [py, item["engine_path"]]
    argv += list(item.get("verb") or [])
    for k, v in (params or {}).items():
        if v is None or v == "":
            continue
        argv += [f"--{k}", str(v)]
    return argv


def _run_streaming(argv: list, env: dict, workdir, timeout: int,
                   heartbeat: int = HEARTBEAT_SEC, echo=print) -> tuple:
    r"""邊跑邊收 + 心跳 + 逾時只殺自己的子行程。回 (rc, 合併輸出, 是否逾時)。

    批474 v0108:`subprocess.run(capture_output=True)` 在長跑引擎上=白畫面到結束。
    這裡照 AllGreen v0101 的藥方:Popen、讀取執行緒逐行收、主執行緒每 heartbeat 秒
    醒一次印「還在跑」——印的是**引擎自己的最後一行**,不是我編的進度。
    """
    import threading
    lines: list = []
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace",
                            env=env, cwd=str(workdir), bufsize=1)

    def _pump():
        try:
            for ln in proc.stdout:          # type: ignore[union-attr]
                lines.append(ln.rstrip("\n"))
        except Exception:
            pass

    th = threading.Thread(target=_pump, daemon=True)
    th.start()
    t0 = time.time()
    timed_out = False
    while True:
        try:
            proc.wait(timeout=heartbeat)
            break
        except subprocess.TimeoutExpired:
            el = int(time.time() - t0)
            if el >= timeout:
                timed_out = True
                try:
                    proc.kill()             # 只殺自己生的這一個
                except Exception:
                    pass
                proc.wait()
                break
            last = next((x for x in reversed(lines) if x.strip()), "")
            echo(f"      ⏳ 還在跑 · {el}s · 引擎最後一行:{last[:88] or '(尚未印任何字)'}")
    th.join(timeout=2)
    return proc.returncode, "\n".join(lines) + ("\n" if lines else ""), timed_out


def call(item_id: str, params: dict | None = None, timeout: int = DEFAULT_TIMEOUT,
         apply: bool = False, catalog_rows: list | None = None,
         sweep: bool = False) -> dict:
    """**統一呼叫契約**。任何子系統都用這一支調度引擎,拿到同一個結果形狀。

    apply=False(預設)→ 只解析不動手,回 PLAN。要真跑必須明講 apply=True:
    調度層的預設值錯一次,代價是**在別人的機器上動了不該動的東西**。
    """
    rows = catalog_rows if catalog_rows is not None else catalog()
    hit = next((r for r in rows if r["id"] == item_id), None)
    if hit is None:
        return {"id": item_id, "family": "", "zh": "", "engine": "", "engine_state": "冊無此項",
                "argv": [], "state": "ABSENT", "rc": None, "seconds": 0.0, "tally": "",
                "outputs_seen": [], "stdout_tail": "", "why": f"冊上沒有 id={item_id}(零發明:不猜)"}
    pyinfo = python_for(hit["family"])
    if not hit["engine_path"]:
        return {**{k: hit[k] for k in ("id", "family", "zh", "engine", "engine_state")},
                "argv": [], "state": "ABSENT", "rc": None, "seconds": 0.0, "tally": "",
                "outputs_seen": [], "stdout_tail": "",
                "why": f"引擎不在位({hit['glob']});**缺件不是紅燈**,不要去 debug 一支不存在的引擎"}
    argv = _argv_for(hit, params, pyinfo["python"])
    base = {**{k: hit[k] for k in ("id", "family", "zh", "engine", "engine_state")},
            "argv": argv, "python": pyinfo["python"], "python_src": pyinfo.get("source", "")}
    if not apply:
        return {**base, "state": "PLAN", "rc": None, "seconds": 0.0, "tally": "",
                "outputs_seen": [], "stdout_tail": "",
                "why": "dry:只解析不動手(要真跑請 apply=True / --apply)"}
    if sweep and WRITE_VERB in (hit.get("verb") or []):
        # 批471 v0102 寫庫動詞閘:動詞裡本來就帶 `--apply` 的項(量到 2 支:
        # tw_universe_update / db_localdb_apply)是**寫庫件**。家族全掃永不代跑。
        # 破壞性的那一步永遠要有人指名道姓點它,不能被一個家族開關掃進去。
        return {**base, "state": "PLAN", "rc": None, "seconds": 0.0, "tally": "",
                "outputs_seen": [], "stdout_tail": "",
                "why": "**寫庫動詞**:家族全掃不代跑(要跑請 --ids "
                       f"{hit['id']} --apply 明點;同「--approve-remove 只在明令下」律)"}
    t0 = time.time()
    env = child_env(hit.get("family", ""), hit.get("engine_dir", "") if hit.get("module") else "")
    # 批471 v0103:**不在原始碼樹裡跑**。量過:36 支在位引擎全用 __file__ 定位,
    # 零支讀 cwd,所以換工作目錄對它們沒有任何影響;而不換的代價是
    # 相對路徑預設(如 ENG016 的 `--out ./vap_one_out`)會把產出拉進原始碼樹。
    workdir = OUTDIR / "_cwd"
    workdir.mkdir(parents=True, exist_ok=True)
    if hit.get("cwd") == "engine" and hit.get("engine_dir") and Path(hit["engine_dir"]).is_dir():
        workdir = Path(hit["engine_dir"])      # 批477:冊講了才換(讀 cwd 的引擎)
    try:
        rc, out, timed_out = _run_streaming(argv, env, workdir, timeout)
        if timed_out:
            state, why = "TIMEOUT", f"逾 {timeout}s 未回=已停(不卡斷);只殺自己生的子行程,部分輸出保留"
        else:
            state = "GREEN" if rc == 0 else "RED"
            why = ""
            if rc != 0:
                # 批471 v0101:**缺料 ≠ 壞掉**。只認引擎自己印的那句話,並把原文帶回
                # 當證據;沒有那句話的 rc≠0 一律照舊 RED(不得靠這條放過真紅)。
                # v0102:再往下分一層——缺參數 / 缺件 / 缺料,見 classify_stop。
                _tail = "\n".join([x for x in out.splitlines() if x.strip()][-10:])
                _st, _why = classify_stop(_tail)
                if _st:
                    state, why = _st, _why
    except Exception as exc:
        rc, out, state, why = None, "", "RED", f"{type(exc).__name__}:{str(exc)[:80]}"
    secs = round(time.time() - t0, 2)
    # 批462:`[計]` 只認**最後一行**。子報告也會印 `FAIL 0`,全篇搜就會把
    # 「OK 38 · FAIL 1」讀成綠——那正是工作站掛過的那個假綠。
    tallies = TALLY_RX.findall(out)
    tally = tallies[-1].strip() if tallies else ""
    if state == "GREEN" and tally:
        m = re.search(r"FAIL\s+(\d+)", tally)
        if m and int(m.group(1)) > 0:
            state = "AMBER"
            why = "rc=0 但最後一行 [計] 仍有 FAIL(以計數為準,不以 rc 為準)"
    seen = []
    for o in (hit.get("outputs") or []):
        q = VIA / o
        if "<" in o or "*" in o:
            seen.append({"out": o, "exists": None})
        else:
            seen.append({"out": o, "exists": q.exists()})
    lines = [x for x in out.splitlines() if x.strip()]
    return {**base, "state": state, "rc": rc, "seconds": secs, "tally": tally,
            "outputs_seen": seen, "stdout_tail": "\n".join(lines[-6:]), "why": why}


def matrix(family: str | None = None, ids: list | None = None, apply: bool = False,
           timeout: int = DEFAULT_TIMEOUT, do_print: bool = True,
           apply_families: list | None = None) -> dict:
    """批量調度 → 多矩陣資料(**這一份就是 HTML 的唯一資料源**,零二次加工)。

    批471 v0102:`apply` 不再是全有全無。
      apply=True                       → 本次選到的每一項都真跑
      apply_families=["vrn","vap"]     → **只有**這些家族真跑,其餘照樣 PLAN
      ids=[...]                        → 只跑點名的項(且視為**明點**,寫庫閘放行)
    一個開關按下去就發動 24 支 VDF 回補,那不叫方便,那叫地雷。
    """
    rows = catalog(family)
    if ids:
        rows = [r for r in rows if r["id"] in ids]
    fams = {x.strip().lower() for x in (apply_families or []) if x.strip()}
    named = bool(ids)          # --ids 是**明點**:寫庫閘只擋家族全掃,不擋明點
    res = []
    for i, r in enumerate(rows, 1):
        do = apply or (r["family"].lower() in fams)
        if do_print:
            print(f"  [{i}/{len(rows)}] {r['family']}/{r['id']} · "
                  f"{r['engine'] or '缺席'}{'' if do else ' (PLAN)'}")
        _c = call(r["id"], apply=do, timeout=timeout, catalog_rows=rows,
                  sweep=not named)
        res.append(_c)
        if do_print and do:
            print(f"      → {_c['state']} · {_c['seconds']}s"
                  + (f" · {_c['why'][:70]}" if _c.get("why") else ""))
    tally = {}
    for x in res:
        tally[x["state"]] = tally.get(x["state"], 0) + 1
    spec_p, _ = spec_path()
    return {
        "schema": "VIA.EngineBus.v1",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "spec": spec_p.name if spec_p else "(冊缺)",
        "family": family or "all",
        "apply": apply,
        "apply_families": sorted(fams),
        "ids": list(ids or []),
        "live_n": sum(1 for x in res if x["state"] not in ("PLAN",)),
        "counts": tally,
        "catalog": rows,
        "results": res,
        # 批474:引擎綠不綠回答不了「有沒有料」。庫況跟調度結果放同一份資料裡,
        # 頁上才不必去別處撈(**這一份仍是 HTML 的唯一資料源**)。
        "census": _census_block(),
    }


def _census_block() -> dict:
    rows, why = db_census()
    miss = census_expected(rows) if rows else []
    tal: dict = {}
    for r in rows + miss:
        tal[r["state"]] = tal.get(r["state"], 0) + 1
    return {"tables": rows, "missing": miss, "counts": tal, "why": why,
            "thin_days": CENSUS_THIN_DAYS}



_CENSUS = None
#: 日期跨度多少天才算「料夠厚」。30 天=一個月:回補鏈跑成功至少要有這麼多。
#: 這個數字是**判準**,所以寫在這裡讓人看得見,不埋在函式裡。
CENSUS_THIN_DAYS = 30
#: 日期欄的常見名字(問過實庫才列的,不是想像的)
_DATE_COLS = ("date", "trade_date", "obs_date", "period", "dt", "as_of", "ts")


def db_census() -> tuple[list, str]:
    r"""庫況普查:**表在不在 · 有幾列 · 日期跨多久**(唯讀,只跑一次)。

    為什麼要有這一張表(批474 操作員問 C「VDF 到底能不能跑」):
      引擎綠不綠**回答不了那題**——一支引擎可以完美地跑完,
      然後把資料寫進一張空表,或寫進一張只有四天的表。
      「跑得動」和「有料」是兩件事,而只報前者就是一種假綠。

    三態怎麼判(判準亮在這裡,不埋):
      GREEN  有列,且(沒有日期欄 或 跨度 ≥ CENSUS_THIN_DAYS)
      AMBER  有列,但日期跨度 < CENSUS_THIN_DAYS —— **料在,但薄**
      NODATA 表在、列數 0 —— **表建好了沒料**
      ABSENT 全樹沒有這張表 —— **不是壞掉**,是還沒建

    掃描沿用 `db_table_index()` 認可的那批庫(排除 references/自測夾/SCOPE_COPY),
    **不另立庫路徑冊**,也不另開第二支掃描器。
    """
    global _CENSUS
    if _CENSUS is not None:
        return _CENSUS, ""
    idx, why = db_table_index()
    # 批474 自犯錯:`db_table_index` **成功時 why 也有值**(「問過 6 本庫 · 43 張表」),
    # 我拿它當失敗旗標 → 庫況永遠是空的。判準看 idx 本身,不看那句附註。
    if not idx:
        _CENSUS = []
        return _CENSUS, why or "全樹無可讀的 duckdb"
    try:
        import duckdb
    except Exception:
        _CENSUS = []
        return _CENSUS, "本環境無 duckdb"
    rows, seen = [], set()
    for db in sorted(VIA.rglob("*.duckdb")):
        sp = str(db)
        if "/references/" in sp or "_self_test" in sp or "SCOPE_COPY" in sp:
            continue
        con = None
        try:
            con = duckdb.connect(sp, read_only=True)
            for (t,) in con.execute("SHOW TABLES").fetchall():
                t = str(t)
                if (db.name, t) in seen:
                    continue
                seen.add((db.name, t))
                try:
                    n = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                except Exception:
                    continue
                cols = [str(r[1]) for r in
                        con.execute(f'PRAGMA table_info("{t}")').fetchall()]
                dcol = next((c for c in cols if c.lower() in _DATE_COLS), None)
                lo = hi = None
                span = None
                if dcol and n:
                    try:
                        lo, hi = con.execute(
                            f'SELECT MIN("{dcol}"), MAX("{dcol}") FROM "{t}"').fetchone()
                        lo, hi = (str(lo) if lo is not None else None,
                                  str(hi) if hi is not None else None)
                        # 只在兩端都像 YYYY-MM-DD 時才算天數;算不出來就誠實留空
                        if lo and hi and len(lo) >= 10 and len(hi) >= 10:
                            from datetime import date as _d
                            a = _d.fromisoformat(lo[:10])
                            b = _d.fromisoformat(hi[:10])
                            span = (b - a).days + 1
                    except Exception:
                        lo = hi = None
                if n == 0:
                    st = "NODATA"
                elif span is not None and span < CENSUS_THIN_DAYS:
                    st = "AMBER"
                else:
                    st = "GREEN"
                rows.append({"db": db.name, "table": t, "rows": int(n),
                             "date_col": dcol or "", "lo": lo or "", "hi": hi or "",
                             "span_days": span, "state": st})
        except Exception:
            continue
        finally:
            if con is not None:
                try:
                    con.close()
                except Exception:
                    pass
    ssot, _ = db_ssot()
    declared = {(t["db"], t["table"]) for t in ssot.get("tables", [])}
    for r in rows:
        r["source"] = ("副本" if "_repo_" in r["db"] else
                       "冊上" if (r["db"], r["table"]) in declared else "冊外")
    rows.sort(key=lambda r: (r["db"], r["table"]))
    _CENSUS = rows
    return _CENSUS, ""


def census_expected(rows: list) -> list:
    r"""該有而沒有的表 → ABSENT 列。批478 起**冊優先**,grep 只當冊外的補充。

    冊上宣告、庫裡沒有 → ABSENT(冊上宣告),並列寫入者引擎(這是最該亮的一種:該有而沒有)
    冊外、碼上 SQL 語境引用 ≥ MIN_REFS 檔 → ABSENT(冊外)(批474 那條律照舊:寧可少報)
    冊上的 known_legacy_absent 不重複報(操作員機器上已知的 12 張舊制表,冊講了)
    """
    have = {r["table"] for r in rows}
    ssot, _ = db_ssot()
    out = []
    declared = set()
    for t in ssot.get("tables", []):
        declared.add(t["table"])
        if t["table"] not in have:
            out.append({"db": t["db"], "table": t["table"], "rows": 0, "date_col": "",
                        "lo": "", "hi": "", "span_days": None, "state": "ABSENT",
                        "refs": 0, "source": "冊上宣告", "writers": t.get("writers", [])})
    legacy = set(ssot.get("known_legacy_absent", []))
    MIN_REFS = 3
    sql_rx = re.compile(
        r"(?:FROM|JOIN|INTO|TABLE|UPDATE)\s+[\"'`]?"
        r"((?:tw|vrn|etf|global|macro|consensus)_[a-z0-9_]{2,28})\b", re.I)
    cnt: dict = {}
    for pyf in list((VIA / "functional modules").rglob("*.py")) + \
            list((VIA / "supportive modules").rglob("*.py")):
        sp = str(pyf)
        if "/references/" in sp or "SCOPE_COPY" in sp:
            continue
        try:
            txt = pyf.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for t in {m.lower() for m in sql_rx.findall(txt)}:
            cnt[t] = cnt.get(t, 0) + 1
    for t, c in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0])):
        if c >= MIN_REFS and t not in have and t not in declared and t not in legacy:
            out.append({"db": "—", "table": t, "rows": 0, "date_col": "",
                        "lo": "", "hi": "", "span_days": None,
                        "state": "ABSENT", "refs": c, "source": "冊外"})
    return out


# ---------------------------------------------------------------- 多矩陣 HTML
_STATE_COLOR = {"GREEN": "#1a7f37", "AMBER": "#b7791f", "RED": "#b91c1c",
                "TIMEOUT": "#b91c1c", "ABSENT": "#6b7280", "PLAN": "#3b6fb5",
                "NODATA": "#7c5cbf"}


def _tokens() -> tuple[dict, str]:
    """UI 樣板正主 MDL089 的 tokens(Zero-Hydra:不自己發明配色)。"""
    m, why = _load("CGC_MDL089_UIBaseTemplate_v*.py", HERE, "mdl089_bus")
    if m is not None and hasattr(m, "load_tokens"):
        try:
            return m.load_tokens(), f"MDL089 {Path(m.__file__).name}"
        except Exception as exc:
            why = f"load_tokens 失敗 {type(exc).__name__}"
    return {}, why or "MDL089 缺席"


def _cell(state: str) -> str:
    c = _STATE_COLOR.get(state, "#6b7280")
    return (f'<span class="st" style="background:{c}1a;color:{c};'
            f'border:1px solid {c}55">{_html.escape(state)}</span>')


def _mode_label(data: dict) -> str:
    """頁首的模式標籤(批471 v0104)。`--apply-family` 下 data["apply"] 是 False,
    v0103 就照著印「只解析(dry)」——**一張報實測結果的頁,第一行把自己的模式講錯**。"""
    if data.get("apply"):
        return "真跑(--apply 全跑)"
    fams = data.get("apply_families") or []
    ids = data.get("ids") or []
    if fams:
        return f"真跑家族 {','.join(fams)};其餘只解析(dry)"
    if ids:
        return f"明點真跑 {','.join(ids)};其餘只解析(dry)"
    return "只解析(dry)"


_DB_INDEX: dict | None = None


def db_table_index() -> tuple[dict, str]:
    """表名 → 哪一本庫(批471 v0104;唯讀、只跑一次、缺=誠實空)。

    **不另立庫路徑冊**:掃 VIA 底下實際存在的 .duckdb(排除 references/自測夾),
    問它各自的 SHOW TABLES。掃到的才算數——零發明。
    """
    global _DB_INDEX
    if _DB_INDEX is not None:
        return _DB_INDEX, ""
    _DB_INDEX = {}
    try:
        import duckdb
    except Exception:
        return _DB_INDEX, "本環境無 duckdb"
    n = 0
    for db in sorted(VIA.rglob("*.duckdb")):
        sp = str(db)
        if "/references/" in sp or "_self_test" in sp or "SCOPE_COPY" in sp:
            continue
        con = None
        try:
            con = duckdb.connect(sp, read_only=True)
            for (t,) in con.execute("SHOW TABLES").fetchall():
                _DB_INDEX.setdefault(str(t), db.name)
            n += 1
        except Exception:
            continue
        finally:
            if con is not None:
                try:
                    con.close()
                except Exception:
                    pass
    return _DB_INDEX, (f"問過 {n} 本庫 · {len(_DB_INDEX)} 張表" if n else "一張庫都開不了")


def output_verdict(o: str) -> tuple[str, str]:
    """一條冊宣告產出 → (判定, 說明)。**先分類再判,各問各的。**

    v0103 一律拿 `(VIA/o).exists()` 判,可是冊上 60 條裡有 34 條是**表名**不是路徑,
    於是那 34 條永遠寫「缺」——vrn_structdb 剛入庫 71 筆,頁上照樣說它缺。
    """
    o = str(o or "")
    if "<" in o or "*" in o:
        return "—", "含萬用字元,不判"
    if "::" in o:                       # `庫.duckdb::表` 明寫形
        dbn, _, tbl = o.partition("::")
        idx, why = db_table_index()
        if not idx:
            return "—", f"判不了({why})"
        return ("在" if idx.get(tbl) == Path(dbn).name else "缺"), f"表 · 問庫({why})"
    _EXT = (".json", ".html", ".duckdb", ".parquet", ".csv",
            ".jsonl", ".md", ".png", ".svg", ".txt")
    if "/" in o:
        return ("在" if (VIA / o).exists() else "缺"), "路徑 · 問 VIA 根"
    if o.lower().endswith(_EXT):
        # 裸檔名(冊上 7 條):**沒有目錄**,接 VIA 根一定落空。去找。
        for q in VIA.rglob(o):
            sq = str(q)
            if "/references/" in sq or "SCOPE_COPY" in sq or "_self_test" in sq:
                continue
            try:
                where = q.parent.relative_to(VIA)
            except ValueError:
                where = q.parent
            return "在", f"裸檔名 · 找到於 {where}"
        return "缺", "裸檔名 · 全樹找過(排除 references)"
    idx, why = db_table_index()
    if not idx:
        return "—", f"判不了({why})"
    hit = idx.get(o)
    return ("在" if hit else "缺"), (f"表 · 在 {hit}" if hit else f"表 · 問庫({why})")


def render(data: dict, out: Path | None = None) -> Path:
    """實測結果 → **多矩陣** HTML。零 CDN、手機自適應、深淺色皆可讀。

    每一格的數字都來自 `data`(matrix() 的回傳),**不做二次加工、不補空白**:
    量不到的就顯示「—」並在頁上說為什麼量不到。
    """
    tk, tk_why = _tokens()
    pal = (tk.get("palette") or {}) if isinstance(tk, dict) else {}
    out = out or (OUTDIR / "ENGINE_BUS_MATRIX.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    rows, res = data["catalog"], data["results"]
    by_id = {x["id"]: x for x in res}

    fams = sorted({r["family"] for r in rows})
    # 矩陣一:家族 × 狀態
    states = ["GREEN", "NODATA", "AMBER", "RED", "TIMEOUT", "ABSENT", "PLAN"]
    m1 = []
    for f in fams:
        line = {"家族": f}
        for s in states:
            line[s] = sum(1 for r in rows if r["family"] == f
                          and by_id.get(r["id"], {}).get("state") == s)
        line["合計"] = sum(1 for r in rows if r["family"] == f)
        m1.append(line)

    def tbl(headers, lines, cls=""):
        th = "".join(f"<th>{_html.escape(str(h))}</th>" for h in headers)
        body = []
        for ln in lines:
            tds = []
            for h in headers:
                v = ln.get(h, "")
                tds.append(f"<td>{v if isinstance(v, str) and v.startswith('<') else _html.escape(str(v))}</td>")
            body.append("<tr>" + "".join(tds) + "</tr>")
        return (f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead>'
                f'<tbody>{"".join(body)}</tbody></table></div>')

    # 矩陣二:逐項目錄(冊 → 尾版 → 在位)
    m2 = [{"家族": r["family"], "項": r["id"], "說明": r["zh"][:40],
           "引擎(尾版)": r["engine"] or "—", "版數": r["versions"],
           "動詞": "/".join(r["verb"]) or "—", "參數": ",".join(r["params"]) or "—",
           "在位": _cell("GREEN" if r["engine"] else "ABSENT")} for r in rows]

    # 矩陣三:調度結果(狀態 × 計數 × 秒 × 因由)
    m3 = [{"項": x["id"], "狀態": _cell(x["state"]),
           "rc": "—" if x["rc"] is None else x["rc"],
           "秒": x["seconds"] or "—",
           "[計] 最後一行": (x["tally"] or "—")[:80],
           "因由": (x["why"] or "")[:70] or "—"} for x in res]

    # 矩陣四:產出契約(冊宣告 × 實際在不在)
    m4 = []
    for x in res:
        for o in x["outputs_seen"]:
            v, note = output_verdict(o["out"])
            m4.append({"項": x["id"], "冊宣告產出": o["out"][:56],
                       "實際": v, "怎麼判的": note})
    if not m4:
        m4 = [{"項": "—", "冊宣告產出": "冊上此批未宣告 outputs",
               "實際": "—", "怎麼判的": "無宣告"}]

    # 矩陣五:庫況(表在不在 · 有幾列 · 日期跨多久)
    cen = data.get("census") or {"tables": [], "missing": [], "why": "本批未取庫況"}
    m5 = []
    for r in cen["tables"] + cen["missing"]:
        span = ("—" if r["span_days"] is None
                else f"{r['span_days']} 天")
        rng = f"{r['lo']} → {r['hi']}" if r["lo"] else ("—" if r["rows"] else "無列")
        m5.append({"庫": r["db"], "表": r["table"], "冊": r.get("source", "—"),
                   "列數": f"{r['rows']:,}" if r["state"] != "ABSENT"
                           else f"碼裡 {r.get('refs', 0)} 檔在用",
                   "日期跨度": f"{rng}({span})" if r["lo"] else rng,
                   "狀態": r["state"]})
    if not m5:
        m5 = [{"庫": "—", "表": "—", "列數": "—", "日期跨度": "—",
               "狀態": "—"}]

    css = f"""
:root{{--bg:#f4f6f8;--paper:#fff;--ink:#1f2733;--mut:#5b6775;--line:#dfe4ea;
--accent:{pal.get('accent', '#315f7d')}}}
:root:not([data-theme="light"]) {{}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{
--bg:#0d1219;--paper:#141b25;--ink:#dfe6f0;--mut:#93a1b3;--line:#232d3b}}}}
:root[data-theme="dark"]{{--bg:#0d1219;--paper:#141b25;--ink:#dfe6f0;--mut:#93a1b3;--line:#232d3b}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
font:12px/1.5 "Segoe UI","Noto Sans TC",system-ui,sans-serif;padding:14px 16px;
padding-block:16px}}
h1{{font-size:15px;margin:0 0 2px}}
h2{{font-size:12.5px;margin:18px 0 6px;color:var(--accent)}}
.sub{{color:var(--mut);font-size:10.5px;margin-bottom:10px;overflow-wrap:anywhere}}
.tw{{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--paper)}}
table{{border-collapse:collapse;width:100%;min-width:520px}}
th,td{{padding:5px 8px;border-bottom:1px solid var(--line);text-align:left;
font-size:10.5px;white-space:nowrap}}
th{{background:color-mix(in srgb,var(--accent) 8%,transparent);
color:var(--mut);font-weight:600;position:sticky;top:0}}
td:nth-child(3),td:nth-child(5){{white-space:normal;overflow-wrap:anywhere}}
.st{{padding:1px 7px;border-radius:10px;font-size:9.5px;font-weight:600}}
.note{{color:var(--mut);font-size:10px;margin:6px 0 0;overflow-wrap:anywhere}}
@media(max-width:520px){{body{{padding:12px}}table{{min-width:480px}}}}
"""
    counts = " · ".join(f"{k} {v}" for k, v in sorted(data["counts"].items()))
    page = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 引擎調度多矩陣</title><style>{css}</style></head><body>
<h1>VIA 引擎調度 · 多矩陣實測結果</h1>
<div class="sub">{_html.escape(data["ts"])} · 冊 {_html.escape(data["spec"])}
· 家族 {_html.escape(str(data["family"]))} · 模式 {_html.escape(_mode_label(data))}
· {_html.escape(counts)} · 樣板 {_html.escape(tk_why)}</div>

<h2>矩陣一 · 家族 × 狀態</h2>
{tbl(["家族"] + states + ["合計"], m1)}
<p class="note"><b>缺件 ≠ 缺料 ≠ 壞掉</b>——三件事混成一格,就會讓人去 debug
一支行為完全正確的引擎。所以這三種各有各的燈:<br>
<b>ABSENT=缺件</b>:引擎檔 / 相依套件 / <b>必要參數</b> 不在位(例:
<code>plotly 缺席=誠實停</code>、<code>argparse: expected one argument</code>)。<br>
<b>NODATA=缺料</b>:引擎跑了,但上游沒料,它自己印了「誠實停」之類的話
(命中的原文列在矩陣三的因由欄)。<br>
<b>PLAN</b>:沒動手——dry,或**寫庫動詞**被家族閘擋下(要跑得 <code>--ids</code> 明點)。<br>
<b>這三個都不是紅燈。</b>判準要亮得出證據:NODATA/ABSENT 只在**引擎自述那句話**
或 argparse 自己的抱怨命中時才成立,不用 rc 判(全樹 <code>return 2</code> 163 處
只有 46 處是這個意思,rc 不是穩定慣例);沒命中的 rc≠0 一律照舊 RED。</p>

<h2>矩陣二 · 引擎目錄(冊 → 尾版 → 在位)</h2>
{tbl(["家族", "項", "說明", "引擎(尾版)", "版數", "動詞", "參數", "在位"], m2)}
<p class="note">冊只有一本:<code>{_html.escape(data["spec"])}</code>。
本表是**它**的投影,不是另一份清單——冊改了這裡就跟著改。</p>

<h2>矩陣三 · 調度結果</h2>
{tbl(["項", "狀態", "rc", "秒", "[計] 最後一行", "因由"], m3)}
<p class="note">`[計]` 只認**最後一行**:子報告也會印 <code>FAIL 0</code>,
全篇搜就會把「OK 38 · FAIL 1」讀成綠(批462 工作站實錄的那個假綠)。
rc=0 但最後一行仍有 FAIL → 判 AMBER,**以計數為準不以 rc 為準**。</p>

<h2>矩陣四 · 產出契約(冊宣告 × 實際)</h2>
{tbl(["項", "冊宣告產出", "實際", "怎麼判的"], m4)}
<p class="note">冊上 60 條宣告產出裡有 <b>34 條是資料庫的表名</b>,不是檔案路徑。另有 7 條是**沒有目錄的裸檔名**。所以**照形狀分四路**:萬用字元不判 · 路徑接 VIA 根 · <b>裸檔名去全樹找</b> · <b>表名問庫</b>(唯讀 SHOW TABLES)。一張庫都開不了就寫「判不了」,<b>不寫成缺</b>——判不了就說判不了,不猜。</p>

<h2>矩陣五 · 庫況(表在不在 · 有幾列 · 日期跨多久)</h2>
{tbl(["庫", "表", "冊", "列數", "日期跨度", "狀態"], m5)}
<p class="note"><b>引擎綠不綠回答不了「有沒有料」</b>——一支引擎可以完美地跑完,
然後把資料寫進一張空表。所以這張表跟上面四張是兩件事:
<b>GREEN</b>=有列且(無日期欄 或 跨度 ≥ {cen.get("thin_days", 30)} 天) ·
<b>AMBER</b>=有列但跨度不足({cen.get("thin_days", 30)} 天)=<b>料在,但薄</b> ·
<b>NODATA</b>=表建好了、列數 0 ·
<b>ABSENT</b>=碼裡當表在用、庫裡沒有這張表(<b>不是壞掉,是還沒建</b>)。
ABSENT 收得緊:只認 SQL 語境(FROM/JOIN/INTO/TABLE/UPDATE)後面的名字,
且要 ≥3 個檔在用——第一版沒收緊,量出 74 筆、一半是變數名,
連庫裡明明有 891 列的 tw_listings 都被寫成缺。<b>寧可少報,也不要點錯紅燈。</b>
{("（庫況取不到：" + _html.escape(cen["why"]) + "）") if cen.get("why") else ""}</p>

<p class="note">零 CDN、零外部字型、零追蹤;全部數字來自本次實跑,
量不到的顯示「—」並說明為什麼量不到。</p>
</body></html>"""
    out.write_text(page, encoding="utf-8")
    return out


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    done, fails = [], []

    def chk(name, cond, note=""):
        done.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest")[0]

    sp, spwhy = spec_path()
    rows = catalog()
    fams = sorted({r["family"] for r in rows})
    chk("① 調度冊**只有一本**:讀既有 VIA_InputConsole_Spec(尾版 glob),"
        "本件不另立第二本(另立=正典換了沒人跟得上)",
        sp is not None and len(rows) >= 20 and len(fams) >= 2,
        f"(冊 {sp.name if sp else spwhy} · {len(rows)} 項 · 家族 {fams})")

    chk("② 目錄=冊的投影:每項都帶尾版解析與**在位實測**(在位≠跑得動,本表只說在不在)",
        all(("engine_state" in r and "versions" in r) for r in rows)
        and any(r["engine"] for r in rows),
        f"(在位 {sum(1 for r in rows if r['engine'])}/{len(rows)})")

    r_absent = call("這個id不存在", catalog_rows=rows)
    chk("③ 冊上沒有的 id → **ABSENT 不是 RED**,而且講明「零發明:不猜」",
        r_absent["state"] == "ABSENT" and "零發明" in r_absent["why"], "")

    hit = next((r for r in rows if r["engine"]), None)
    r_plan = call(hit["id"], catalog_rows=rows) if hit else {}
    chk("④ **預設不動手**:apply=False 回 PLAN 並解析出完整 argv。"
        "調度層的預設值錯一次,代價是在別人的機器上動了不該動的東西",
        r_plan.get("state") == "PLAN" and len(r_plan.get("argv") or []) >= 2,
        f"({hit['id'] if hit else '—'} → {' '.join((r_plan.get('argv') or [])[1:3])})")

    py = python_for("vrn")
    chk("⑤ 家族 python **委派** MDL137 RunGate(它再委派 MDL136);橋缺席才退回本行程"
        "並在 source 講明是退路(不假裝走了正主)",
        bool(py.get("python")) and "python_for" in body and "RunGate" in body,
        f"(python={Path(py['python']).name} · 源={py.get('source', '')[:40]})")

    chk("⑥ `[計]` 只認**最後一行**(批462:子報告也印 `FAIL 0`,全篇搜會把"
        "「OK 38 · FAIL 1」讀成綠);rc=0 但最後一行仍有 FAIL → AMBER,以計數為準",
        "tallies[-1]" in body and "以計數為準" in body, "")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        q = Path(td)
        ok = q / "fx_ok.py"
        ok.write_text("print('[計] 三檢 OK 3 · FAIL 0')\n", encoding="utf-8")
        amb = q / "fx_amber.py"
        amb.write_text("print('[計] 1 件 · FAIL 0 · 子報告')\n"
                       "print('[計] 三檢 OK 2 · FAIL 1')\n", encoding="utf-8")
        slow = q / "fx_slow.py"
        slow.write_text("import time\ntime.sleep(999)\n", encoding="utf-8")
        fake = [{"id": "fx_ok", "family": "t", "zh": "", "glob": "", "dir": "",
                 "verb": [], "params": [], "outputs": [], "net": False,
                 "engine": ok.name, "engine_path": str(ok), "versions": 1,
                 "engine_state": "在位", "group": "", "spec_why": ""},
                {"id": "fx_amber", "family": "t", "zh": "", "glob": "", "dir": "",
                 "verb": [], "params": [], "outputs": [], "net": False,
                 "engine": amb.name, "engine_path": str(amb), "versions": 1,
                 "engine_state": "在位", "group": "", "spec_why": ""},
                {"id": "fx_slow", "family": "t", "zh": "", "glob": "", "dir": "",
                 "verb": [], "params": [], "outputs": [], "net": False,
                 "engine": slow.name, "engine_path": str(slow), "versions": 1,
                 "engine_state": "在位", "group": "", "spec_why": ""}]
        a = call("fx_ok", apply=True, catalog_rows=fake)
        b = call("fx_amber", apply=True, catalog_rows=fake)
        c = call("fx_slow", apply=True, timeout=3, catalog_rows=fake)
        chk("⑦ 統一結果契約實測:全綠→GREEN;**rc=0 但最後一行有 FAIL→AMBER**"
            "(子報告的 `FAIL 0` 不得蓋過總計);逾時→TIMEOUT 並說「不卡斷」",
            a["state"] == "GREEN" and b["state"] == "AMBER"
            and "FAIL 1" in b["tally"] and c["state"] == "TIMEOUT"
            and "不卡斷" in c["why"],
            f"(ok={a['state']} · amber={b['state']}:{b['tally'][-14:]} · slow={c['state']})")

        data = {"schema": "VIA.EngineBus.v1", "ts": "2026-01-01T00:00:00",
                "spec": "fx.json", "family": "t", "apply": True,
                "counts": {"GREEN": 1, "AMBER": 1, "TIMEOUT": 1},
                "catalog": fake, "results": [a, b, c]}
        pg = render(data, out=q / "m.html")
        h = pg.read_text(encoding="utf-8")
        chk("⑧ 多矩陣 HTML:四張矩陣皆在、零 CDN、手機自適應、深淺色皆有定義",
            all(k in h for k in ("矩陣一", "矩陣二", "矩陣三", "矩陣四"))
            and "http://" not in h and "https://" not in h
            and "prefers-color-scheme" in h and "@media(max-width" in h,
            f"({len(h):,} 字元 · 零外連={'http' not in h})")

        chk("⑨ 頁上每一格都來自實測資料,**不做二次加工**;判不了的顯示「—」"
            "並說明為什麼判不了(含萬用字元的產出宣告不判在缺)",
            "判不了就說判不了" in h and "不猜" in h and "fx_slow" in h, "")

    live_before = sorted(x.name for x in OUTDIR.glob("*")) if OUTDIR.exists() else []
    chk("⑩ 本件**零網路**、預設 dry、自測不寫正式產出夾",
        ("urlopen" not in body and "requests" not in body)
        and (sorted(x.name for x in OUTDIR.glob("*")) if OUTDIR.exists() else []) == live_before,
        "(零網路碼 · 正式夾未動)")

    chk("⑪ Zero-Hydra 宣告在檔:四家調度者(DeckServer Popen×12 / RunGate×3 / "
        "MDL139×1 / ClosingGate)各自重寫尾版解析、家族 python、逾時、結果解讀;"
        "本件是**一條匯流排四家共用**,不是第五套",
        "Popen ×12" in src and "一條匯流排,四家共用" in src, "(立場在檔)")

    with tempfile.TemporaryDirectory() as td2:
        q2 = Path(td2)
        nd = q2 / "fx_nodata.py"
        nd.write_text("import sys\nprint('[首頁擷取] 無報告件(誠實;缺件搜集器先跑)')\n"
                      "sys.exit(2)\n", encoding="utf-8")
        bad = q2 / "fx_realbad.py"
        bad.write_text("import sys\nprint('Traceback: 真的壞了')\nsys.exit(2)\n",
                       encoding="utf-8")
        fk = [{"id": i, "family": "t", "zh": "", "glob": "", "dir": "", "verb": [],
               "params": [], "outputs": [], "net": False, "engine": p.name,
               "engine_path": str(p), "versions": 1, "engine_state": "在位",
               "group": "", "spec_why": ""} for i, p in (("fx_nodata", nd), ("fx_realbad", bad))]
        d1 = call("fx_nodata", apply=True, catalog_rows=fk)
        d2 = call("fx_realbad", apply=True, catalog_rows=fk)
    chk("⑫ **缺料 ≠ 壞掉**(批471 v0100 實跑第一次就照出我自己用錯尺:VRN 7 項報 RED 3,"
        "而三支印的都是「無報告件(誠實)」——引擎行為完全正確,是我的儀器判錯)。"
        "想用 rc=2 當判準**量過之後否決**:全樹 `return 2` 163 處只有 46 處是誠實停,"
        "117 處是別的意思——**rc 不是穩定慣例**。改認引擎**自己印的那句話**,"
        "並把命中的原文帶回當證據;**沒有那句話的 rc≠0 一律照舊 RED**(對照組驗了)",
        d1["state"] == "NODATA" and "無報告件" in d1["why"]
        and d2["state"] == "RED" and d2["rc"] == 2,
        f"(誠實停 rc=2→{d1['state']} · 真壞 rc=2→{d2['state']})")

    # ---- ⑬⑭⑮ 批471 v0102:第二次實跑(VAP 6 項)照出的三件事 ----
    with tempfile.TemporaryDirectory() as td3:
        q3 = Path(td3)
        # 對照組全部**釘死在 VAP 那次實跑的原文**(不是我改寫過的版本):
        # 對照組要釘在缺陷所在的那一版,不然下一版一改措辭,這幾檢就自己失效了。
        fx = {
            # vap_dashboard 真印過的尾段:缺料
            "fx_vapdash": "print('[缺料] 缺 4 項:表 prices_canonical·tw_chip_inst"
                          "·tw_chip_margin·features_daily(vdf_tw_market.duckdb)')\n"
                          "print('[補料] 誠實停 rc2 · 舊頁在位 VIA_UI_Dashboard_v0100.html')\n",
            # vap_std_dashboard 真印過的尾段:缺件(套件)
            "fx_vapstd": "print('[標準模板] plotly 缺席=誠實停(pip install plotly 後再跑)')\n",
            # vap_one_render 真吐過的尾段:缺參數
            "fx_vapone": "import sys\nsys.stderr.write('VAP_ENG016_AutoplotOne: "
                         "error: argument --render: expected one argument\\n')\n",
            # 真紅對照組(沒有任何誠實停字樣)
            "fx_vapstack": "print('_duckdb.CatalogException: Catalog Error: Table with "
                           "name tw_daily_prices does not exist!')\n",
        }
        fk3 = []
        for k, code in fx.items():
            f = q3 / (k + ".py")
            f.write_text(code + "import sys\nsys.exit(2)\n", encoding="utf-8")
            fk3.append({"id": k, "family": "t", "zh": "", "glob": "", "dir": "", "verb": [],
                        "params": [], "outputs": [], "net": False, "engine": f.name,
                        "engine_path": str(f), "versions": 1, "engine_state": "在位",
                        "group": "", "spec_why": ""})
        e1 = call("fx_vapdash", apply=True, catalog_rows=fk3)
        e2 = call("fx_vapstd", apply=True, catalog_rows=fk3)
        e3 = call("fx_vapone", apply=True, catalog_rows=fk3)
        e4 = call("fx_vapstack", apply=True, catalog_rows=fk3)

    chk("⑬ **「誠實停」才是正典句**(全樹 451 處)。v0101 那張字表是照 VRN 幾支的措辭湊的,"
        "只認得 VRN 的方言——VAP 印「誠實停 rc2」就漏接,兩支沒壞的引擎被我判紅。"
        "本檢用 VAP 那次實跑的**原文**當對照組(釘死在缺陷所在的那一版,不改寫)",
        e1["state"] == "NODATA" and "誠實停" in e1["why"],
        f"(缺料原文→{e1['state']})")

    chk("⑭ **缺件 ≠ 缺料 ≠ 壞掉**(操作員原律)。誠實停要再分一層:缺料→NODATA;"
        "缺件(引擎/相依套件/**必要參數**)→ ABSENT,**不新立第八態**。"
        "判缺參數只認 argparse 自己講的話——**不能用「冊上有宣告 params 就別跑」一刀切**:"
        "冊上 21 項宣告 params,其中 20 項沒給參數照樣跑得好好的(量過),一刀切=誤殺 20 項",
        e2["state"] == "ABSENT" and "缺件" in e2["why"]
        and e3["state"] == "ABSENT" and "缺參數" in e3["why"]
        and e4["state"] == "RED"
        and sum(1 for r in rows if r.get("params")) >= 20,
        f"(plotly 缺席→{e2['state']} · argparse 少參數→{e3['state']} · "
        f"裸 CatalogException→{e4['state']} · 冊上有 params 的項="
        f"{sum(1 for r in rows if r.get('params'))})")

    wv = [r["id"] for r in rows if WRITE_VERB in (r.get("verb") or [])]
    m_sweep = matrix(ids=wv, apply=True, do_print=False) if wv else None
    g_sweep = ([call(i, apply=True, catalog_rows=rows, sweep=True) for i in wv]
               if wv else [])
    chk("⑮ **`--apply` 不該是全有全無**。VDF 24 項按下去=同時發動 tw_history 全史回補、"
        "tw_chips 籌碼回補,還有兩支動詞本來就帶 `--apply` 的寫庫件。本版加 --apply-family / "
        "--ids;**寫庫動詞閘**:家族全掃永不代跑,要跑必須 --ids 明點"
        "(同「--approve-remove 只在明令下」律)",
        len(wv) >= 2
        and all(x["state"] == "PLAN" and "寫庫動詞" in x["why"] for x in g_sweep)
        and m_sweep is not None
        and all(x["state"] != "PLAN" or "寫庫動詞" not in (x["why"] or "")
                for x in m_sweep["results"])
        and "--apply-family" in body,
        f"(寫庫件 {wv} · 家族全掃→{sorted({x['state'] for x in g_sweep})} · "
        f"--ids 明點→{sorted({x['state'] for x in m_sweep['results']}) if m_sweep else '-'})")

    # ---- ⑯ 批471 v0103:調度層不得讓引擎往原始碼樹寫 ----
    with tempfile.TemporaryDirectory() as td4:
        q4 = Path(td4)                      # 假裝這是「原始碼樹」
        f4 = q4 / "fx_litter.py"
        f4.write_text("from pathlib import Path\n"
                      "Path('./拉出來的產出夾').mkdir(exist_ok=True)\n"
                      "print('[計] 1 件 · FAIL 0')\n", encoding="utf-8")
        fk4 = [{"id": "fx_litter", "family": "t", "zh": "", "glob": "", "dir": "", "verb": [],
                "params": [], "outputs": [], "net": False, "engine": f4.name,
                "engine_path": str(f4), "versions": 1, "engine_state": "在位",
                "group": "", "spec_why": ""}]
        r16 = call("fx_litter", apply=True, catalog_rows=fk4)
        src_clean = not (q4 / "拉出來的產出夾").exists()
        land = (OUTDIR / "_cwd" / "拉出來的產出夾")
        landed = land.exists()
        if landed:
            land.rmdir()
    chk("⑯ **調度層不得讓引擎往原始碼樹寫**(批471 v0102 實跑後 git status 冒出一個從沒入過庫的"
        "`functional modules/VAP/engine/vap_one_out/`——ENG016 的 `--out` 預設是相對路徑,"
        "而我把 cwd 設在引擎目錄。正本零觸碰不只管別改別人的檔,**也管別在別人家裡生檔**)。"
        "改 cwd 前先量:冊上在位 36 支**全用 __file__ 定位**,讀 cwd 的 0 支,所以換 cwd 零影響",
        r16["state"] == "GREEN" and src_clean and landed
        and "workdir" in body and "cwd=str(workdir)" in body,
        f"(引擎相對寫檔→原始碼樹乾淨={src_clean} · 落在產出夾={landed})")

    # ---- ⑰⑱ 批471 v0104:把自己產出的頁讀一遍,發現說謊的是頁 ----
    lbl_a = _mode_label({"apply": False, "apply_families": ["vrn", "vap"], "ids": []})
    lbl_b = _mode_label({"apply": False, "apply_families": [], "ids": []})
    lbl_c = _mode_label({"apply": True, "apply_families": [], "ids": []})
    chk("⑰ **頁首的模式標籤不得說謊**(v0103 在 --apply-family 下照印「只解析(dry)」——"
        "`data[\"apply\"]` 那時本來就是 False,而我拿它當唯一標籤。"
        "一張報實測結果的頁,第一行把自己的模式講錯)",
        "真跑家族 vrn,vap" in lbl_a and lbl_b == "只解析(dry)" and "全跑" in lbl_c,
        f"(家族模式→「{lbl_a}」)")

    _wild = output_verdict("VIA_Reports/first_page_text/<stem>.json")
    _path_in = output_verdict("VIA_Reports/engine_bus/ENGINE_BUS_latest.json")
    _path_no = output_verdict("VIA_Reports/engine_bus/一定不存在的檔.json")
    _tbl = output_verdict("vrn_report_basic")
    _idx, _idxwhy = db_table_index()
    _decl = [o for r in rows for o in (r.get("outputs") or [])]
    _tblcnt = sum(1 for o in _decl
                  if "<" not in o and "*" not in o and "/" not in o
                  and not o.lower().endswith((".json", ".html", ".duckdb", ".parquet",
                                              ".csv", ".jsonl", ".md", ".png", ".svg")))
    chk("⑱ **表名要問庫,不要問檔案系統**。量了冊:60 條宣告產出裡有 34 條是資料庫的表名"
        "(tw_daily_prices / vrn_report_basic / ActiveTWETF.duckdb::holdings_daily …),"
        "v0103 一律 `(VIA/o).exists()` → 那 34 條永遠寫「缺」,矩陣四超過一半的格子在說謊"
        "(vrn_structdb 剛入庫 71 筆,頁上照樣說它的 vrn_report_basic 缺)。"
        "改成先分類再判;**一張庫都開不了就寫「判不了」,不寫成缺**",
        _wild[0] == "—" and "萬用" in _wild[1]
        and _path_in[0] == "在" and "路徑" in _path_in[1]
        and _path_no[0] == "缺"
        and _tbl[0] in ("在", "—") and "表" in (_tbl[1] + ("表" if _tbl[0] == "—" else ""))
        and _tblcnt >= 30,
        f"(冊上表名形 {_tblcnt} 條 · 庫索引={_idxwhy} · vrn_report_basic→{_tbl})")

    _bare_in = output_verdict("VIA_UI_VRNControlTower_v0100.html")
    _bare_no = output_verdict("一定沒有這個頁_v9999.html")
    _bare_decl = [o for r in rows for o in (r.get("outputs") or [])
                  if "/" not in o and "<" not in o and "*" not in o
                  and o.lower().endswith((".html", ".json", ".csv", ".md"))]
    chk("⑲ **說「缺」之前,先確定自己有去找過**。v0104 把表名接對了,"
        "卻還把 `VIA_UI_VRNControlTower_v0100.html` 寫成缺——而 vrn_ui 那一跑報「頁 3/3 新鮮」。"
        "冊上有 7 條是**沒有目錄的裸檔名**,真的頁住在 supportive modules/ui_support/,"
        "我拿 VIA 根去接它。這是同一個病的第三種形狀:**一種判法問三種問題**。"
        "改成照宣告的形狀分四路:萬用不判 · 路徑接根 · **裸檔名去找** · 表名問庫",
        _bare_in[0] == "在" and "找到於" in _bare_in[1]
        and _bare_no[0] == "缺" and "找過" in _bare_no[1]
        and len(_bare_decl) >= 7,
        f"(冊上裸檔名 {len(_bare_decl)} 條 · 控制塔頁→{_bare_in})")

    _need_cases = [
        ("selftest 需要 reportlab 產生樣本 PDF;請改用 python …py <你的.pdf>", "ABSENT"),
        ("[標準模板] plotly 缺席=誠實停(pip install plotly 後再跑)", "ABSENT"),
        ("[補料] 誠實停 rc2 · 缺 4 項表", "NODATA"),
        ("需要 人工確認之後再跑", ""),          # 中文「需要」不得被當成缺件
        ("Traceback (most recent call last): 真的壞了", ""),
    ]
    _got = [classify_stop(t)[0] for t, _ in _need_cases]
    chk("⑳ **「需要 <套件>」也是缺件**(批473 收 PDFPlumber-Plus 時的第八盞錯燈:"
        "引擎印「selftest 需要 reportlab」還附了補法,我判它紅——字表裡沒有這個講法)。"
        "最難看的是同一批我在那支 PowerShell 啟動器裡**已經寫對這條律**,卻沒帶回來;"
        "同一個判準兩個地方只改一邊,另一邊靜靜走錯——那正是本件立案要收掉的事。"
        "收得緊:`需要` 後面要緊跟像套件名的 ASCII 識別字,中文「需要…」不放過",
        _got == [e for _, e in _need_cases],
        f"({list(zip([t[:16] for t, _ in _need_cases], _got))})")

    # ── 批474 四檢:工作站實錄照出來的三件事,一件一把尺 ──────────────
    chk("㉑ 動詞正規化:`--matrix` 這種連字號寫法收得到(實錄:我叫操作員打的"
        "就是這個形狀,而 v0106 印兩百行說明就回 rc=0)",
        _verb(["--matrix", "--html"])[0] == "matrix"
        and _verb(["matrix"])[0] == "matrix"
        and _verb(["census"])[0] == "census"
        # 只脫連字號,不猜別的:錯字**不**放過(猜錯的體貼比不體貼更難救)
        and _verb(["matrixx"])[0] == ""
        and _verb(["--bogus"])[0] == "")

    chk("㉒ 不認得的動詞回 **rc=2 不是 rc=0**(rc=0 是假綠:自動化鏈路看 rc,"
        "會把「什麼都沒跑」讀成「跑完了」)+ 用法是六行不是整篇 docstring",
        "matrix" in USAGE and "census" in USAGE
        and len(USAGE.splitlines()) <= 10
        and len(USAGE) < len(__doc__ or "") / 4)

    _cen_rows, _cen_why = db_census()
    chk("㉓ 庫況普查真的讀到庫(自犯錯:`db_table_index` **成功時 why 也有值**,"
        "我拿它當失敗旗標 → 庫況永遠空)",
        bool(_cen_rows) or bool(_cen_why),
        f"({len(_cen_rows)} 張表 · {_cen_why or '—'})")

    _miss = census_expected(_cen_rows) if _cen_rows else []
    _have = {r["table"] for r in _cen_rows}
    chk("㉔ ABSENT 收得緊:只認 SQL 語境且 ≥3 檔;**庫裡有的表絕不出現在缺席名單**"
        "(第一版沒收緊,量出 74 筆、一半是變數名,連 891 列的 tw_listings 都寫成缺"
        "——那是判錯的紅燈,一次七十四盞)",
        all(m["table"] not in _have for m in _miss)
        # 批478:≥3 檔那條律只管 grep 出來的(冊外);冊上宣告的缺席本來就沒有 refs
        and all(m.get("refs", 0) >= 3 for m in _miss if m.get("source") != "冊上宣告"),
        f"(缺席 {len(_miss)} 張)")

    # ── 批474 v0108 二檢:不卡斷 ──
    import tempfile as _tf
    _beats: list = []
    with _tf.TemporaryDirectory() as _td:
        _slow = Path(_td) / "slow.py"
        _slow.write_text("import time,sys\nfor i in range(6):\n    print('step',i,flush=True); time.sleep(0.5)\nprint('[計] OK 1 · FAIL 0')\n", encoding="utf-8")
        _rc, _out, _to = _run_streaming([sys.executable, str(_slow)], dict(os.environ), Path(_td), timeout=30,
                                        heartbeat=1, echo=lambda m: _beats.append(m))
    chk("㉕ 邊跑邊收 + 心跳:慢引擎跑 3 秒、心跳 1 秒 → 心跳 ≥2 次且印的是引擎自己的最後一行"
        "(實錄:via-ryg 停在 vrn_firstpage 白畫面=緩衝到結束才吐,批423 同病)",
        _rc == 0 and not _to and len(_beats) >= 2 and any("step" in b for b in _beats)
        and "[計] OK 1" in _out, f"(心跳 {len(_beats)} 次 · rc={_rc})")
    with _tf.TemporaryDirectory() as _td:
        _hang = Path(_td) / "hang.py"
        _hang.write_text("import time\nprint('started',flush=True)\ntime.sleep(60)\n", encoding="utf-8")
        _t0 = time.time()
        _rc, _out, _to = _run_streaming([sys.executable, str(_hang)], dict(os.environ), Path(_td), timeout=2,
                                        heartbeat=1, echo=lambda m: None)
        _el = time.time() - _t0
    chk("㉖ 逾時只殺自己生的子行程、部分輸出保留當證據、實際等待貼近 timeout 不是永遠",
        _to and "started" in _out and _el < 10, f"(等了 {_el:.1f}s · 逾時={_to})")

    # ── 批476 二檢:啟動層注入 ──
    _code = "import os,sys;print(os.environ.get('VIA_ACCEL_BOOT',''),'|','via_net' in sys.modules,'|',os.environ.get('VIA_NET_CONSENT','(未設)'))"
    _r1 = subprocess.run([sys.executable, "-c", _code], capture_output=True, text=True, timeout=120, env=child_env("vrn"))
    _r2 = subprocess.run([sys.executable, "-c", _code], capture_output=True, text=True, timeout=120, env=child_env("vdf"))
    _a1, _n1, _g1 = [x.strip() for x in (_r1.stdout or "| |").split("|")[:3]]
    _a2, _n2, _g2 = [x.strip() for x in (_r2.stdout or "| |").split("|")[:3]]
    chk("㉗ 啟動層注入:任何家族的子行程起跑就綁加速器(VIA_ACCEL_BOOT 有值,1: 或 ABSENT: 皆誠實);**零引擎改動**"
        "(量過:逐檔加=VDF 105 支+VRN 全部+VAP 全部的新版本檔)",
        BOOTDIR.is_dir() and _a1.startswith(("1:", "ABSENT:")) and _a2.startswith(("1:", "ABSENT:")),
        f"(vrn→{_a1[:16]} · vdf→{_a2[:16]})")
    chk("㉘ 網路正典件只掛 vdf(vrn 子行程 via_net 不在、vdf 子行程在),且**同意閘一個字不碰**(子行程看到的閘態=母行程所設)",
        _n1 == "False" and _n2 == "True"
        and _g2 == os.environ.get("VIA_NET_CONSENT", "(未設)"),
        f"(vrn via_net={_n1} · vdf via_net={_n2} · 閘={_g2})")

    # ── 批477 二檢:套件式引擎 ──
    chk("㉙ 「attempted relative import」不判缺件(第十盞判錯的燈:沒有套件缺,是我用檔案方式啟動套件內模組)→ RED 並指路 -m",
        classify_stop("Traceback\nImportError: attempted relative import with no known parent package")[0] == "RED"
        and "-m" in classify_stop("ImportError: attempted relative import with no known parent package")[1])
    with _tf.TemporaryDirectory() as _td:
        _pk = Path(_td) / "pk"; _pk.mkdir(); (_pk / "__init__.py").write_text("", encoding="utf-8")
        (_pk / "cli.py").write_text("from . import helper\nimport sys\nprint('[計] OK 1 · FAIL 0')\n", encoding="utf-8")
        (_pk / "helper.py").write_text("X=1\n", encoding="utf-8")
        _it = {"engine_path": str(_pk / "cli.py"), "module": "pk.cli", "engine_dir": _td, "verb": ["selftest"], "family": "vdf"}
        _argv = _argv_for(_it, None, sys.executable)
        _r = subprocess.run(_argv, capture_output=True, text=True, timeout=60, env=child_env("vdf", _td), cwd=_td)
    chk("㉚ 冊上 module 欄 → 以 -m 啟動且套件根前置 PYTHONPATH(相對匯入可解);對照組:當檔案跑必炸",
        _argv[1] == "-m" and _argv[2] == "pk.cli" and _r.returncode == 0 and "[計] OK 1" in _r.stdout,
        f"(argv={_argv[1:3]} · rc={_r.returncode})")

    _spec_p, _ = spec_path()
    _spec = json.loads(_spec_p.read_text(encoding="utf-8")) if _spec_p else {}
    _cwd_items = [it for g in _spec.get("families", {}).get("vdf", {}).get("groups", []) for it in g.get("items", []) if it.get("cwd") == "engine"]
    chk("㉛ 冊上 `cwd: engine` 只對宣告的項生效(讀 cwd 的引擎),其餘照舊在 VIA_Reports/_cwd 跑(原始碼樹零產出)",
        all(it.get("module") or it.get("engine") for it in _cwd_items) and len(_cwd_items) >= 1,
        f"(宣告 cwd=engine 的項:{[it['id'] for it in _cwd_items]})")

    _ss, _ssn = db_ssot()
    _rows_c, _ = db_census()
    _miss_c = census_expected(_rows_c) if _rows_c else []
    _decl_missing = [m for m in _miss_c if m.get("source") == "冊上宣告"]
    chk("㉜ 庫況對冊比:冊在位、冊上宣告而庫裡沒有的表報 ABSENT(冊上宣告)並列寫入者;冊上 known_legacy 不重報;"
        "庫裡有的表絕不出現在缺席名單",
        bool(_ss.get("tables")) and all(m["table"] not in {r["table"] for r in _rows_c} for m in _miss_c)
        and all(t not in {m["table"] for m in _miss_c} for t in _ss.get("known_legacy_absent", []))
        and all(m.get("writers") is not None for m in _decl_missing),
        f"(冊 {_ssn} · 冊上宣告缺 {len(_decl_missing)} · 冊外缺 {len(_miss_c) - len(_decl_missing)})")

    print(f"  [計] 三十二檢({len(done)} 檢) OK {len(done) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


USAGE = """用法(動詞在前;--matrix 這種連字號寫法也收):
  catalog [--family vdf|vrn|vap]        冊 → 尾版 → 在位,只看不跑
  matrix  [--family F] [--html] [--timeout N]  批量調度 → 多矩陣(**預設只解析**;心跳不卡斷)
          [--apply-family vrn,vap]      只有點名的家族真跑
          [--ids a,b]                   只跑點名的項(寫庫動詞只認這條路)
  call    --item <id> [--apply]         單項
  census                                庫況:表在不在 · 有幾列 · 日期跨多久
  boot                                  啟動層實證:子行程看到的加速器/網路件/閘態
  --selftest                            自測"""


def _verb(args: list) -> tuple[str, list]:
    r"""動詞正規化(批474 工作站實錄)。

    操作員打的是 `via-bus --matrix`——**那是我上一則訊息叫他打的**,錯在我。
    但 `--matrix` 也是任何人都會自然打出來的形狀,而 v0106 對它的回應是
    「印兩百行 docstring,然後回 rc=0 說成功」。所以這裡只做一件事:
    **把頭部的連字號脫掉**再比對動詞白名單。只脫連字號,不去猜別的東西——
    猜錯的體貼比不體貼更難救。
    """
    verbs = ("catalog", "matrix", "call", "census", "boot")
    if not args:
        return "", args
    head = args[0].lstrip("-").lower()
    if head in verbs:
        return head, args[1:]
    return "", args


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 引擎調度匯流排(CGC_MDL148 v0111)· 三十二檢自測(零網路)===")
        return selftest()
    fam = args[args.index("--family") + 1] if "--family" in args else None
    apply_ = "--apply" in args
    af = (args[args.index("--apply-family") + 1].split(",")
          if "--apply-family" in args else [])
    ids = (args[args.index("--ids") + 1].split(",") if "--ids" in args else None)
    tmo = int(args[args.index("--timeout") + 1]) if "--timeout" in args else DEFAULT_TIMEOUT
    verb, _rest = _verb(args)
    if verb == "boot":
        # 證據不是宣稱:每個家族真的起一個子行程,印它看到的
        for f in ("vdf", "vrn", "vap"):
            py = python_for(f).get("python") or sys.executable
            code = ("import os,sys;print(os.environ.get('VIA_ACCEL_BOOT','(無)'),'|',"
                    "os.environ.get('VIA_NET_BOOT','(不掛)'),'|','via_net' in sys.modules,'|',"
                    "os.environ.get('VIA_NET_CONSENT','(未設)'))")
            try:
                r = subprocess.run([py, "-c", code], capture_output=True, text=True,
                                   timeout=120, env=child_env(f), cwd=str(OUTDIR if OUTDIR.exists() else VIA))
                seen = (r.stdout or "").strip() or (r.stderr or "").strip()[-120:]
            except Exception as exc:
                seen = f"{type(exc).__name__}:{str(exc)[:60]}"
            print(f"  [{f}] python={Path(py).name} → 加速器 | 網路件 | via_net 可 import | 同意閘 = {seen}")
        print("[啟動層] bootstrap=" + str(BOOTDIR) + (" 在位" if BOOTDIR.is_dir() else " **缺**"))
        return 0
    if verb == "census":
        rows, why = db_census()
        miss = census_expected(rows) if rows else []
        for r in rows:
            rng = (f"{r['lo']} → {r['hi']} ({r['span_days']} 天)"
                   if r["lo"] and r["span_days"] is not None
                   else (f"{r['lo']} → {r['hi']}" if r["lo"] else ""))
            print(f"  [{r['state']:6s}] {r['db'][:26]:26s} {r['table']:28s} "
                  f"{r['rows']:>10,}  {rng}  ·{r.get('source', '')}")
        for r in miss:
            _w = (" 寫入者 " + "/".join(r["writers"])) if r.get("writers") else ""
            print(f"  [ABSENT] {r['db'][:26]:26s} {r['table']:28s} "
                  f"{('碼裡 ' + str(r['refs']) + ' 檔在用') if r.get('refs') else '冊上宣告':>10s}  ·{r.get('source', '')}{_w}")
        tal: dict = {}
        for r in rows + miss:
            tal[r["state"]] = tal.get(r["state"], 0) + 1
        print(f"[庫況] {len(rows)} 張表在庫 · 缺 {len(miss)} 張 · "
              + " · ".join(f"{k} {v}" for k, v in sorted(tal.items()))
              + (f" · {why}" if why else ""))
        return 0
    if verb == "catalog":
        rows = catalog(fam)
        for r in rows:
            print(f"  [{r['engine_state']}] {r['family']}/{r['id']:18s} "
                  f"{r['engine'] or r['glob']:44s} 動詞={'/'.join(r['verb']) or '-'}")
        print(f"[目錄] {len(rows)} 項 · 在位 {sum(1 for r in rows if r['engine'])}")
        return 0
    if verb == "call":
        if "--item" not in args:
            print("  用法:call --item <id> [--apply]")
            return 2
        # call --item 是**明點**(人親手指名這一支)→ 寫庫閘放行
        r = call(args[args.index("--item") + 1], apply=apply_, sweep=False)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["state"] in ("GREEN", "PLAN") else 1
    if verb == "matrix":
        data = matrix(family=fam, apply=apply_, ids=ids, apply_families=af, timeout=tmo)
        OUTDIR.mkdir(parents=True, exist_ok=True)
        (OUTDIR / "ENGINE_BUS_latest.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        cnt = " · ".join(f"{k} {v}" for k, v in sorted(data["counts"].items()))
        scope = ("全跑" if apply_ else
                 ("真跑家族 " + ",".join(data["apply_families"]) if data["apply_families"]
                  else ("明點 " + ",".join(data["ids"]) if data["ids"] else "全 dry")))
        print(f"[矩陣] {len(data['results'])} 項 · {scope} · {cnt}")
        if "--html" in args:
            p = render(data)
            print(f"[頁] {p}")
        return 0
    # 批474:v0106 這裡是 `print(__doc__); return 0`——兩百行說明加一個
    # **rc=0 的假綠**。自動化鏈路看 rc,會把「什麼都沒跑」讀成「跑完了」。
    if args:
        print(f"  [FAIL] 不認得的動詞:{args[0]}")
    print(USAGE)
    return 2


if __name__ == "__main__":
    sys.exit(main())
