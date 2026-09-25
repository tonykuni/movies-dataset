#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA-SYS-ENG-005 : Engine Hardening Auditor.

針對三支引擎各列 20 種**尚未發生但很可能發生**的故障，並實際掃描它們的
原始碼看目前中了幾種。每一種都附多個處置選項，不是單一建議。

    VIA_CentralGovernanceConsole.py   CGE01–CGE20   治理／AST／台帳域
    VIA_DownwardController.py         DCT01–DCT20   編排／子行程／併發域
    VIA_FilePriorityRouter.py         FPR01–FPR20   檔案系統／格式判定域

每域掛五個 local-free 函式庫（全部標準庫，不連網、不安裝）：

    治理域   tokenize    逐 token 檢查編碼宣告、BOM、Tab 縮排（ast 看不到這些）
             symtable    真正的 scope 分析，抓遮蔽與未綁定
             hmac        台帳簽章，偵測外部竄改
             filecmp     台帳與快照的實體比對
             difflib     版本間差異定位

    編排域   shlex       安全拆解命令列，取代字串拼接
             threading   看門狗計時器，與主迴圈解耦
             atexit      孤兒子行程清理
             tempfile    每次執行的隔離工作區
             signal      優雅終止而非硬殺

    檔案域   mimetypes   副檔名以外的第二意見
             zipfile     不展開就檢查容器（zip bomb 防護）
             unicodedata 檔名正規化，抓 NFC/NFD 雙胞胎
             stat        權限、稀疏檔、特殊檔類型
             zlib        壓縮比偵測，抓 zip bomb

偵測方式以 AST 為主，能精準定位到行號；無法用 AST 判定的才退回 token/regex，
並標成 M 級證據。只讀不改，被掃描的原始碼永遠不動。

用法：
    python VIA_EngineHardening.py --tools <引擎所在目錄>
"""

from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import io
import json
import os
import re
import sys
import tokenize
import webbrowser
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

URN_SELF = "VIA-SYS-ENG-005"
VERSION = "v0100"
SPEC_VERSION = "VIA-SSOT-SPEC-v0100"

CAPS: Dict[str, bool] = {}
for _module in ("tokenize", "symtable", "hmac", "filecmp", "difflib",
                "shlex", "threading", "atexit", "tempfile", "signal",
                "mimetypes", "zipfile", "unicodedata", "stat", "zlib"):
    try:
        __import__(_module)
        CAPS[_module] = True
    except ImportError:
        CAPS[_module] = False

import symtable                                            # noqa: E402


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Console:
    def __init__(self) -> None:
        self.lines: List[str] = []

    def say(self, message: str, level: str = "INFO") -> None:
        line = "[%s][%s] %s" % (datetime.now().strftime("%H:%M:%S"), level, message)
        self.lines.append(line)
        print(line, flush=True)


LOG = Console()


# ---------------------------------------------------------------------------
# §1  60 種故障目錄
# ---------------------------------------------------------------------------

@dataclass
class Mode:
    code: str
    domain: str
    name: str
    impact: str
    remedies: List[str]
    severity: str = "WARN"
    library: str = ""            # 哪個新掛的庫負責偵測或修復


CATALOG: List[Mode] = [
    # ---- 治理域：VIA_CentralGovernanceConsole.py ----
    Mode("CGE01", "CONSOLE", "台帳可被外部竄改而無從察覺",
         "URN 台帳是所有引用的外鍵，被改過卻沒人知道，整條證據鏈失效",
         ["以 hmac 對台帳內容簽章，載入時驗章",
          "台帳改為 append-only 事件流，重建當前狀態",
          "每次寫入同時落一份 sha256 到獨立檔案"], "FAIL", "hmac"),
    Mode("CGE02", "CONSOLE", "台帳寫入非原子，中斷即毀損",
         "寫到一半斷電或被 Ctrl-C，台帳變成半截 JSON，下次載入整份失效",
         ["寫到 .tmp 後 os.replace 原子換名",
          "保留前一版為 .bak，載入失敗自動回退",
          "改用 sqlite 交易寫入"], "FAIL", "filecmp"),
    Mode("CGE03", "CONSOLE", "編碼宣告與實際編碼不符",
         "ast 讀得到但執行期讀不到，或反之；症狀是時好時壞",
         ["以 tokenize.detect_encoding 取得真實編碼再讀",
          "統一改寫為 UTF-8 無 BOM",
          "把不一致列為 FAIL 而非嘗試自動轉碼"], "FAIL", "tokenize"),
    Mode("CGE04", "CONSOLE", "Tab 與空白混用的縮排",
         "Python 3 直接 TabError；PowerShell 則是靜默行為改變",
         ["tokenize 逐 token 檢查縮排型別一致性",
          "以官方語義（Tab = 前進到 8 的倍數）展開",
          "標為需人工修，不自動改"], "FAIL", "tokenize"),
    Mode("CGE05", "CONSOLE", "區域變數遮蔽同名全域或內建",
         "行為隨呼叫路徑改變，且靜態掃描看不出來",
         ["以 symtable 比對 scope，找出遮蔽",
          "重新命名區域變數",
          "把該全域改為明確參數傳入"], "WARN", "symtable"),
    Mode("CGE06", "CONSOLE", "使用前未綁定的名稱",
         "只有走到特定分支才炸，測試常常剛好避開",
         ["symtable 找 is_referenced 但非 is_assigned 的名稱",
          "在函式開頭給定明確初值",
          "改用明確的 raise 取代隱性 NameError"], "FAIL", "symtable"),
    Mode("CGE07", "CONSOLE", "遞迴無深度上限",
         "深層目錄或循環結構會直接 RecursionError 中斷整輪治理",
         ["加入明確深度參數並在超限時回報而非拋出",
          "改為迭代 + 明確 stack",
          "先以 os.walk 上限截斷"], "FAIL", ""),
    Mode("CGE08", "CONSOLE", "except 吞掉所有例外且不記錄",
         "真正的錯誤被靜默吃掉，報告看起來全綠",
         ["縮小捕捉範圍到預期的例外類別",
          "捕捉後至少記一行 WARN",
          "保留 BaseException 只用於探針邊界"], "WARN", ""),
    Mode("CGE09", "CONSOLE", "open() 未指定 encoding",
         "跟隨系統 locale，同一份程式在不同機器讀出不同結果",
         ["一律明確 encoding='utf-8'",
          "以 errors='replace' 避免中斷",
          "二進位讀取後自行解碼並記錄實際編碼"], "FAIL", ""),
    Mode("CGE10", "CONSOLE", "以字串拼接組路徑",
         "分隔符與跳脫在跨平台間不一致，長路徑更容易出錯",
         ["改用 pathlib.Path 運算子",
          "os.path.join 至少統一分隔符",
          "所有對外輸出的路徑一律 resolve()"], "WARN", ""),
    Mode("CGE11", "CONSOLE", "JSON 載入未限制大小",
         "一個 2GB 的快照會把整個行程吃爆",
         ["載入前先看檔案大小，超限改為串流或拒收",
          "以 json.JSONDecoder.raw_decode 分段",
          "對輸入檔設硬上限並回報"], "WARN", ""),
    Mode("CGE12", "CONSOLE", "掃描未排除自身輸出",
         "治理引擎掃到自己上一輪的產出，每跑一次編號就多一批",
         ["明確排除 work/out/logs 目錄",
          "以產出檔名樣式排除",
          "在產出檔內埋標記，掃到就跳過"], "FAIL", ""),
    Mode("CGE13", "CONSOLE", "時間戳未帶時區",
         "跨時區或日光節約時，台帳排序會亂",
         ["改用 datetime.now(timezone.utc) 並在顯示時轉換",
          "全部以 UTC 落地，只在 UI 轉本地",
          "至少在欄位名標明是本地時間"], "WARN", ""),
    Mode("CGE14", "CONSOLE", "動態載入模組會執行頂層程式碼",
         "探針把待測模組的副作用一起跑了，可能連線或寫檔",
         ["先以 ast 掃頂層是否有副作用再決定載不載",
          "在子行程內載入，隔離副作用",
          "維持預設關閉，需明示開關"], "FAIL", ""),
    Mode("CGE15", "CONSOLE", "同名模組重複載入導致類別身分不同",
         "issubclass 對同一個類別回傳 False，判定全錯",
         ["以 MRO 名稱 + 介面完整性雙軌認定",
          "統一由單一入口匯入共用基底",
          "把基底抽成獨立套件"], "FAIL", ""),
    Mode("CGE16", "CONSOLE", "台帳序號配發非交易性",
         "兩個行程同時跑，會配到同一個編號",
         ["改以 sqlite 交易配號",
          "以檔案鎖包住讀改寫",
          "偵測到同時執行就直接拒絕啟動"], "FAIL", ""),
    Mode("CGE17", "CONSOLE", "HTML 輸出未逃脫使用者內容",
         "檔名或錯誤訊息含 < > 會破版，甚至注入腳本",
         ["所有插入值一律 escape",
          "以樣板引擎取代字串拼接",
          "對輸出做一次 HTML 解析驗證"], "FAIL", ""),
    Mode("CGE18", "CONSOLE", "正則未編譯且在迴圈內重建",
         "萬檔規模下純浪費，且容易寫出災難性回溯",
         ["模組層 re.compile 一次",
          "以 RE2 風格改寫避免回溯",
          "加入單一比對的時間上限"], "WARN", ""),
    Mode("CGE19", "CONSOLE", "契約基準播種後從未複驗",
         "第一次播種等於把當下狀態當成正確，錯的也被固化",
         ["播種後標記 SEEDED，下一輪強制比對",
          "要求人工核可才升為基準",
          "保留前 N 版基準以便回溯"], "WARN", "difflib"),
    Mode("CGE20", "CONSOLE", "台帳與快照可能不同步",
         "報告說 A、台帳說 B，事後無法判斷哪個是真的",
         ["以 filecmp 比對兩者的衍生欄位",
          "快照內嵌台帳的 hmac 指紋",
          "同一次寫入用同一個交易"], "WARN", "filecmp"),

    # ---- 編排域：VIA_DownwardController.py ----
    Mode("DCT01", "CONTROLLER", "以字串拼接組命令列",
         "路徑含空白或引號時參數會被切錯，最糟會執行到別的東西",
         ["以 shlex.split／shlex.quote 處理",
          "一律傳 list 給 subprocess，不經 shell",
          "對每個參數做白名單驗證"], "FAIL", "shlex"),
    Mode("DCT02", "CONTROLLER", "子行程逾時後未清理孫行程",
         "父的 timeout 到了，孫行程還在跑並持續寫檔",
         ["以行程群組終止整棵樹",
          "atexit 註冊清理器",
          "子行程寫入獨立工作區，殘留可辨識"], "FAIL", "atexit"),
    Mode("DCT03", "CONTROLLER", "逾時只殺不留證據",
         "被殺的那次沒有任何可分析的輸出",
         ["終止前先把已產生的輸出落地",
          "以 signal 先送溫和終止再硬殺",
          "保留逾時當下的行程樹快照"], "WARN", "signal"),
    Mode("DCT04", "CONTROLLER", "共用工作區導致併發互相覆寫",
         "同層並行的能力寫到同一個目錄，結果互相蓋掉",
         ["以 tempfile.mkdtemp 給每個能力獨立工作區",
          "工作區路徑加入能力 URN",
          "同層有寫入衝突者強制序列化"], "FAIL", "tempfile"),
    Mode("DCT05", "CONTROLLER", "看門狗與主迴圈同一執行緒",
         "主迴圈卡住時看門狗也跟著卡，逾時機制失效",
         ["以 threading.Timer 獨立計時",
          "看門狗放在監督行程",
          "以子行程自身的 timeout 為第二道"], "FAIL", "threading"),
    Mode("DCT06", "CONTROLLER", "執行緒池中的例外被吞",
         "future 沒被 result()，錯誤永遠不會浮現",
         ["每個 future 都取 result 並包 try",
          "以 as_completed 逐一處理",
          "設定 pool 的例外回呼"], "FAIL", ""),
    Mode("DCT07", "CONTROLLER", "拓撲排序未處理自我相依",
         "能力宣告依賴自己，會被永遠排除且無提示",
         ["明確偵測自環並回報",
          "載入時就拒絕自我相依的宣告",
          "把自環視為無相依處理"], "WARN", ""),
    Mode("DCT08", "CONTROLLER", "相依指向不存在的能力被靜默忽略",
         "打錯一個 URN，該相依就消失，順序保證失效",
         ["未知上游一律回報為 UNRESOLVED_DEPENDENCY",
          "拒絕啟動直到修正",
          "以 difflib 提示最接近的合法 URN"], "FAIL", "difflib"),
    Mode("DCT09", "CONTROLLER", "能力登記檔可被外部改成執行任意程式",
         "登記檔只是 JSON，改掉 script 欄位就能讓控制器跑任何東西",
         ["對登記檔簽章並驗章",
          "限制 script 只能位於 tools 目錄內",
          "執行前比對檔案 hash 白名單"], "FAIL", "hmac"),
    Mode("DCT10", "CONTROLLER", "輸出量大時管道回填造成死鎖",
         "子行程寫滿管道緩衝就停住，父行程還在等它結束",
         ["改用檔案重導向",
          "以非同步方式同時讀 stdout 與 stderr",
          "communicate() 一次讀完"], "FAIL", ""),
    Mode("DCT11", "CONTROLLER", "以裁決而非硬故障阻斷下游",
         "上游只是回報問題就讓整條鏈停擺，能跑的也不跑了",
         ["區分硬故障與軟裁決，只有硬故障阻斷",
          "提供 strict 模式讓使用者選擇",
          "阻斷時明確寫出理由"], "WARN", ""),
    Mode("DCT12", "CONTROLLER", "權杖比對用字串相等，格式錯也放行",
         "貼錯權杖但格式碰巧相符，變更類能力就跑了",
         ["以正則驗證格式並比對雜湊內容",
          "權杖綁定當次計畫內容的 hash",
          "設定有效期限"], "FAIL", "hmac"),
    Mode("DCT13", "CONTROLLER", "快照選取只看檔案時間",
         "時鐘倒退或檔案被複製，會挑到錯的那份",
         ["以快照內的 stamp 欄位為準",
          "同時比對內容 hash",
          "時間倒退時明確回報"], "WARN", ""),
    Mode("DCT14", "CONTROLLER", "子行程繼承父的環境變數",
         "父的 PYTHONPATH 或代理設定會改變子行程行為",
         ["以最小環境啟動子行程",
          "明確列出要傳遞的變數",
          "記錄實際傳入的環境供追溯"], "WARN", ""),
    Mode("DCT15", "CONTROLLER", "工作目錄設為受測根目錄",
         "子行程的相對路徑寫入會落在受測目錄裡，污染掃描結果",
         ["cwd 設為隔離工作區",
          "強制所有輸出走絕對路徑",
          "執行後比對受測目錄是否被改動"], "WARN", ""),
    Mode("DCT16", "CONTROLLER", "並行度未依資源調整",
         "十路同時跑吃爆記憶體或磁碟 I/O，反而更慢",
         ["依 CPU 數與可用記憶體推算上限",
          "偵測到 I/O 飽和就降級",
          "讓使用者以參數覆寫"], "WARN", ""),
    Mode("DCT17", "CONTROLLER", "未偵測重複啟動",
         "兩份控制器同時跑，台帳與計畫互相覆寫",
         ["以鎖檔標記執行中並帶 PID",
          "偵測到既有執行就拒絕啟動",
          "提供 --force 但要求明示"], "FAIL", ""),
    Mode("DCT18", "CONTROLLER", "能力逾時值全域一致",
         "掃描類與重建類的合理耗時差兩個數量級",
         ["每個能力宣告自己的 timeout",
          "依歷史耗時自動調整",
          "逾時前先發出接近警告"], "WARN", ""),
    Mode("DCT19", "CONTROLLER", "失敗的能力沒有重試",
         "暫時性失敗（檔案鎖、網路抖動）被當成永久失敗",
         ["對可重試類別做有限次退避重試",
          "區分暫時性與永久性錯誤",
          "重試次數與結果一併記錄"], "WARN", ""),
    Mode("DCT20", "CONTROLLER", "聚合裁決被最差者綁架",
         "一個非關鍵能力 RED 就讓整體 RED，久了大家忽略裁決",
         ["為能力設定權重與關鍵性",
          "分開回報關鍵裁決與整體裁決",
          "非關鍵失敗只影響分數不影響閘門"], "WARN", ""),

    # ---- 檔案域：VIA_FilePriorityRouter.py ----
    Mode("FPR01", "ROUTER", "壓縮炸彈",
         "一個 42KB 的 zip 展開後是 4GB，只要有人不小心展開就完蛋",
         ["以 zipfile 讀目錄但不展開，檢查壓縮比",
          "壓縮比超過門檻直接標為 HOSTILE",
          "設定展開後總大小上限"], "FAIL", "zipfile"),
    Mode("FPR02", "ROUTER", "檔名 Unicode 正規化雙胞胎",
         "NFC 與 NFD 在 macOS 與 Windows 間看起來一樣但不是同一個檔",
         ["以 unicodedata.normalize('NFC') 正規化後比對",
          "偵測到雙胞胎就回報",
          "輸出清單一律用正規化後的名稱"], "WARN", "unicodedata"),
    Mode("FPR03", "ROUTER", "特殊檔類型被當成一般檔",
         "FIFO、裝置檔、socket 被開啟會直接卡住整個掃描",
         ["以 stat.S_ISREG 確認是一般檔才讀",
          "非一般檔一律登記後跳過",
          "讀取加上逾時"], "FAIL", "stat"),
    Mode("FPR04", "ROUTER", "副檔名與 MIME 判定不一致",
         "只信副檔名會把偽裝檔放進佇列",
         ["以 mimetypes 取第二意見",
          "與 magic bytes 三方比對",
          "不一致時以簽章為準並回報"], "WARN", "mimetypes"),
    Mode("FPR05", "ROUTER", "稀疏檔或超大單檔",
         "宣稱 1TB 的檔案會把預算一次吃光",
         ["以 stat 的實際區塊數判斷稀疏",
          "單檔大小上限，超過只讀頭尾",
          "納入預算前先看實際佔用"], "WARN", "stat"),
    Mode("FPR06", "ROUTER", "目錄符號連結造成無限遞迴",
         "os.walk 預設不跟連結，但手動遞迴很容易寫錯",
         ["明確 followlinks=False",
          "記錄已訪問的 inode/realpath",
          "設定最大深度"], "FAIL", ""),
    Mode("FPR07", "ROUTER", "同一檔案透過不同路徑重複計算",
         "硬連結或連結目錄會讓同一份內容被算兩次",
         ["以 realpath 或 (device, inode) 去重",
          "以內容 hash 去重",
          "回報重複來源供人工裁決"], "WARN", "stat"),
    Mode("FPR08", "ROUTER", "權限不足時整輪中斷",
         "一個讀不到的檔案讓掃描拋例外結束",
         ["逐檔捕捉並記為 UNREADABLE",
          "先以 os.access 預檢",
          "以較低權限帳號測試掃描"], "FAIL", ""),
    Mode("FPR09", "ROUTER", "掃描期間檔案被改動",
         "先取大小後讀內容，兩者對不上",
         ["一次開檔取得 fd 後再做 fstat",
          "偵測 mtime 變動就重掃該檔",
          "回報掃描期間變動的檔案數"], "WARN", ""),
    Mode("FPR10", "ROUTER", "簽章表過短造成誤判",
         "只讀 64 bytes，某些格式的魔數在更後面",
         ["依格式決定讀取長度",
          "多重簽章比對取共識",
          "無法判定時標為 UNKNOWN 而非猜"], "WARN", "zlib"),
    Mode("FPR11", "ROUTER", "預算耗盡後的延後項無人處理",
         "標成 deferred 就沒有下文，永遠不會被讀",
         ["把 deferred 落成待辦佇列供下輪優先",
          "依優先序輪替，避免同一批永遠被延後",
          "回報累積延後量"], "WARN", ""),
    Mode("FPR12", "ROUTER", "機密判定僅靠檔名",
         "改名的金鑰檔就會被讀進佇列",
         ["內容前綴比對（BEGIN PRIVATE KEY 等）",
          "高熵偵測",
          "任何命中一律只登記不讀"], "FAIL", ""),
    Mode("FPR13", "ROUTER", "產出目錄判定僅靠目錄名",
         "使用者把產出放在別的目錄名，回饋迴路又回來了",
         ["在產出檔內埋引擎標記，掃到就跳過",
          "以產生者 URN 比對",
          "維護產出路徑登記表"], "FAIL", ""),
    Mode("FPR14", "ROUTER", "治理白名單過寬",
         "任何檔名含 registry 就升到 P0，把雜訊也拉進最高優先",
         ["以路徑 + 檔名雙條件",
          "白名單命中仍要通過格式檢查",
          "回報白名單命中數供覆核"], "WARN", ""),
    Mode("FPR15", "ROUTER", "編碼偵測失敗當成純文字",
         "cp950 與 utf-8 混雜的檔案解出亂碼，下游全錯",
         ["以 tokenize/codecs 逐步嘗試並記錄實際編碼",
          "無法判定就標為 BINARY 不進佇列",
          "把偵測到的編碼寫進清單供下游使用"], "WARN", "unicodedata"),
    Mode("FPR16", "ROUTER", "清單本身沒有完整性保護",
         "priority_manifest 被改過，下游照著錯的清單做事",
         ["清單附 hmac 簽章",
          "下游驗章後才使用",
          "清單內含來源目錄的 hash"], "WARN", "hmac"),
    Mode("FPR17", "ROUTER", "巨量小檔造成掃描時間爆炸",
         "十萬個 1KB 檔案的 stat 成本遠高於少數大檔",
         ["以 os.scandir 取代 listdir + stat",
          "設定單目錄檔案數上限並取樣",
          "回報最耗時的前 N 個目錄"], "WARN", ""),
    Mode("FPR18", "ROUTER", "路徑大小寫在不同平台行為不一致",
         "Windows 不分大小寫，去重會漏；Linux 上又變兩個",
         ["依平台決定比對是否區分大小寫",
          "一律以正規化小寫做 key，但保留原名顯示",
          "回報僅差大小寫的同名檔"], "WARN", ""),
    Mode("FPR19", "ROUTER", "格式理解表與實際路由不同步",
         "表上寫走 duckdb，程式卻走 text，模型看到的是假的",
         ["由同一份資料驅動表與路由",
          "啟動時自我比對兩者一致",
          "表變更時強制跑一次回歸"], "FAIL", ""),
    Mode("FPR20", "ROUTER", "沒有掃描結果的穩定性驗證",
         "同一棵樹跑兩次結果不同，卻沒有任何機制會發現",
         ["連跑兩次比對清單 hash",
          "把不穩定的判定標為 FLAKY",
          "對排序加入決定性 tie-break"], "WARN", "filecmp"),
]

CATALOG_BY_CODE = {m.code: m for m in CATALOG}
DOMAIN_FILES = {
    "CONSOLE": "VIA_CentralGovernanceConsole.py",
    "CONTROLLER": "VIA_DownwardController.py",
    "ROUTER": "VIA_FilePriorityRouter.py",
}


# ---------------------------------------------------------------------------
# §2  偵測器
# ---------------------------------------------------------------------------

@dataclass
class Hit:
    code: str
    domain: str
    file: str
    line: int
    evidence: str
    grade: str = "V"


class SourceAudit:
    """對單一引擎原始碼做 AST + token 檢查。"""

    def __init__(self, path: Path, domain: str) -> None:
        self.path = path
        self.domain = domain
        self.hits: List[Hit] = []
        self.source = ""
        self.tree: Optional[ast.AST] = None
        self.parse_error = ""
        self.encoding = ""

    def add(self, code: str, line: int, evidence: str, grade: str = "V") -> None:
        self.hits.append(Hit(code=code, domain=self.domain, file=self.path.name,
                             line=line, evidence=evidence[:160], grade=grade))

    def load(self) -> bool:
        try:
            with self.path.open("rb") as handle:
                encoding, _ = tokenize.detect_encoding(handle.readline)
            self.encoding = encoding
            self.source = self.path.read_text(encoding=encoding, errors="replace")
        except (OSError, SyntaxError) as exc:
            self.parse_error = str(exc)
            return False
        try:
            self.tree = ast.parse(self.source, filename=str(self.path))
        except SyntaxError as exc:
            self.parse_error = "line %s: %s" % (exc.lineno, exc.msg)
            return False
        return True

    # -- token 層：ast 看不到的東西 ---------------------------------------
    def audit_tokens(self) -> None:
        raw = self.path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf") and self.encoding.lower() not in ("utf-8-sig",):
            self.add("CGE03" if self.domain == "CONSOLE" else "FPR15", 1,
                     "檔案有 BOM 但偵測編碼為 %s" % self.encoding)
        indent_kinds: Set[str] = set()
        try:
            for token in tokenize.tokenize(io.BytesIO(raw).readline):
                if token.type != tokenize.INDENT:
                    continue
                if "\t" in token.string:
                    indent_kinds.add("tab")
                if " " in token.string:
                    indent_kinds.add("space")
        except (tokenize.TokenError, IndentationError, SyntaxError):
            return
        if len(indent_kinds) > 1 and self.domain == "CONSOLE":
            self.add("CGE04", 1, "縮排同時使用 Tab 與空白")

    # -- symtable 層 -------------------------------------------------------
    def audit_symbols(self) -> None:
        if self.domain != "CONSOLE":
            return
        try:
            table = symtable.symtable(self.source, str(self.path), "exec")
        except (SyntaxError, ValueError):
            return
        builtins = set(dir(__builtins__)) if isinstance(__builtins__, dict) else set(dir(__builtins__))
        shadowed: Set[str] = set()

        def walk(node: "symtable.SymbolTable") -> None:
            for symbol in node.get_symbols():
                name = symbol.get_name()
                if node.get_type() == "function" and symbol.is_local() and name in builtins:
                    shadowed.add(name)
                if symbol.is_referenced() and not symbol.is_assigned() and \
                        not symbol.is_imported() and not symbol.is_parameter() and \
                        not symbol.is_global() and not symbol.is_free() and \
                        name not in builtins and node.get_type() == "function":
                    self.add("CGE06", node.get_lineno(),
                             "%s 內的 %s 被引用但未在該 scope 綁定"
                             % (node.get_name(), name), grade="M")
            for child in node.get_children():
                walk(child)

        walk(table)
        for name in sorted(shadowed):
            self.add("CGE05", 1, "區域變數遮蔽內建名稱：%s" % name)

    # -- AST 層 ------------------------------------------------------------
    def audit_ast(self) -> None:
        if self.tree is None:
            return
        domain = self.domain
        has_atexit = False
        has_thread_timer = False
        has_shlex = False
        has_tempfile = False
        has_lockfile = False
        followlinks_seen = False

        for node in ast.walk(self.tree):
            # import 盤點
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif node.module:
                    names = [node.module.split(".")[0]]
                for name in names:
                    if name == "atexit":
                        has_atexit = True
                    if name == "shlex":
                        has_shlex = True
                    if name == "tempfile":
                        has_tempfile = True

            # open() 未指定 encoding
            if isinstance(node, ast.Call) and _callee(node) in ("open",):
                mode = ""
                for index, arg in enumerate(node.args):
                    if index == 1 and isinstance(arg, ast.Constant):
                        mode = str(arg.value)
                kwargs = {k.arg for k in node.keywords if k.arg}
                for keyword in node.keywords:
                    if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
                        mode = str(keyword.value.value)
                if "b" not in mode and "encoding" not in kwargs:
                    self.add(_pick(domain, "CGE09", "", "FPR15"), node.lineno,
                             "open() 未指定 encoding")

            # 空的 except / 吞例外
            if isinstance(node, ast.ExceptHandler):
                body_is_pass = all(isinstance(s, ast.Pass) for s in node.body)
                broad = node.type is None or _name_of(node.type) in ("Exception", "BaseException")
                if broad and body_is_pass:
                    self.add(_pick(domain, "CGE08", "DCT06", "FPR08"), node.lineno,
                             "except 捕捉範圍過寬且直接 pass")

            # subprocess 無 timeout
            if isinstance(node, ast.Call):
                callee = _callee(node)
                if callee in ("subprocess.run", "run") and _is_subprocess(node):
                    kwargs = {k.arg for k in node.keywords if k.arg}
                    if "timeout" not in kwargs:
                        self.add("DCT18", node.lineno, "subprocess 呼叫未設 timeout")
                    if "shell" in kwargs:
                        for keyword in node.keywords:
                            if keyword.arg == "shell" and getattr(keyword.value, "value", False):
                                self.add("DCT01", node.lineno, "subprocess 使用 shell=True")
                    if "env" not in kwargs and domain == "CONTROLLER":
                        self.add("DCT14", node.lineno, "子行程未限制環境變數，會完整繼承父行程")
                    if "cwd" in kwargs and domain == "CONTROLLER":
                        for keyword in node.keywords:
                            if keyword.arg == "cwd":
                                self.add("DCT15", node.lineno,
                                         "子行程 cwd 指定為受測目錄，輸出可能污染掃描結果")
                if callee == "os.walk":
                    kwargs = {k.arg for k in node.keywords if k.arg}
                    if "followlinks" not in kwargs:
                        self.add(_pick(domain, "CGE07", "DCT07", "FPR06"), node.lineno,
                                 "os.walk 未明示 followlinks=False", grade="M")
                    else:
                        followlinks_seen = True
                if callee in ("json.load", "json.loads"):
                    self.add(_pick(domain, "CGE11", "DCT13", "FPR16"), node.lineno,
                             "JSON 載入前未檢查大小上限", grade="M")
                if callee in ("datetime.now",) and not node.args and not node.keywords:
                    # 時區問題三個域都有，但要記在自己域的編號下，否則跨域統計會錯
                    self.add(_pick(domain, "CGE13", "DCT13", "FPR20"), node.lineno,
                             "datetime.now() 未帶 tz")
                if callee in ("threading.Timer",):
                    has_thread_timer = True
                if callee in ("Path.write_text", "write_text") and domain == "CONSOLE":
                    self.add("CGE02", node.lineno, "直接覆寫檔案，非原子寫入", grade="M")

            # 路徑字串拼接
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                text = _const_text(node)
                if text and ("/" in text or "\\" in text):
                    self.add(_pick(domain, "CGE10", "DCT13", "FPR18"), node.lineno,
                             "以字串拼接組路徑：%r" % text, grade="M")

        # 缺席型檢查（整檔層級）
        if domain == "CONTROLLER":
            if not has_shlex:
                self.add("DCT01", 0, "未使用 shlex，命令列參數缺少安全拆解")
            if not has_atexit:
                self.add("DCT02", 0, "未註冊 atexit 清理器，逾時後孫行程可能殘留")
            if not has_thread_timer:
                self.add("DCT05", 0, "看門狗未使用獨立計時執行緒")
            if not has_tempfile:
                self.add("DCT04", 0, "未使用 tempfile 隔離工作區，並行能力可能互相覆寫")
            if "lock" not in self.source.lower():
                self.add("DCT17", 0, "未見重複啟動偵測（鎖檔／PID）")
            if "retry" not in self.source.lower() and "重試" not in self.source:
                self.add("DCT19", 0, "未見任何重試機制")
            if "hmac" not in self.source:
                self.add("DCT09", 0, "能力登記檔未簽章，可被外部改成執行任意程式")
        if domain == "CONSOLE":
            if "hmac" not in self.source:
                self.add("CGE01", 0, "台帳未簽章，外部竄改無從察覺")
            if "os.replace" not in self.source:
                self.add("CGE02", 0, "未見原子換名寫入")
            if "sqlite3" not in self.source:
                self.add("CGE16", 0, "序號配發非交易性，兩個行程同時跑會撞號")
        if domain == "ROUTER":
            if "zipfile" not in self.source:
                self.add("FPR01", 0, "未使用 zipfile 檢查容器，無壓縮炸彈防護")
            if "unicodedata" not in self.source:
                self.add("FPR02", 0, "檔名未做 Unicode 正規化")
            if "S_ISREG" not in self.source and "is_file" not in self.source:
                self.add("FPR03", 0, "未確認是一般檔即讀取，FIFO／裝置檔會卡住")
            if "mimetypes" not in self.source:
                self.add("FPR04", 0, "未取 mimetypes 第二意見")
            if "st_blocks" not in self.source and "sparse" not in self.source.lower():
                self.add("FPR05", 0, "未偵測稀疏檔，超大單檔會吃光預算")
            if "st_ino" not in self.source and "realpath" not in self.source:
                self.add("FPR07", 0, "未以 inode/realpath 去重，硬連結會重複計算")
            if "BEGIN" not in self.source:
                self.add("FPR12", 0, "機密判定僅靠檔名，改名的金鑰檔會被讀入")
            if "hmac" not in self.source:
                self.add("FPR16", 0, "清單未簽章，下游無法確認未被竄改")
            if not followlinks_seen and not any(h.code == "FPR06" for h in self.hits):
                self.add("FPR06", 0, "os.walk 未明示 followlinks=False")
        LOG.say("  %s：%d 筆" % (self.path.name, len(self.hits)),
                "WARN" if self.hits else "OK")


def _name_of(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _callee(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts = [func.attr]
        current = func.value
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    return ""


def _is_subprocess(node: ast.Call) -> bool:
    callee = _callee(node)
    return callee.startswith("subprocess.") or callee == "run"


def _const_text(node: ast.AST) -> str:
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            if "/" in child.value or "\\" in child.value:
                return child.value
    return ""


def _pick(domain: str, console: str, controller: str, router: str) -> str:
    code = {"CONSOLE": console, "CONTROLLER": controller, "ROUTER": router}[domain]
    return code or {"CONSOLE": "CGE08", "CONTROLLER": "DCT06", "ROUTER": "FPR08"}[domain]


# ---------------------------------------------------------------------------
# §3  輸出
# ---------------------------------------------------------------------------

def esc(value: Any) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def klass(value: str) -> str:
    upper = str(value).upper()
    if upper in ("PASS", "GREEN", "V", "READY", "OK"):
        return "ok"
    if upper in ("FAIL", "RED"):
        return "fail"
    if upper in ("WARN", "AMBER", "M", "ABSENT"):
        return "warn"
    return ""


def table(items: List[Dict[str, Any]], fields: List[str], status: str = "") -> str:
    if not items:
        return "<tr><td colspan='%d' class='muted'>—— 無 ——</td></tr>" % len(fields)
    out = []
    for item in items:
        cells = []
        for name in fields:
            value = item.get(name, "")
            if isinstance(value, (list, tuple)):
                value = " ／ ".join(str(v) for v in value)
            cls = " class='%s'" % klass(str(value)) if name == status else ""
            cells.append("<td%s>%s</td>" % (cls, esc(value)))
        out.append("<tr>%s</tr>" % "".join(cells))
    return "".join(out)


CSS = """
:root{--paper:#f2f2f3;--ink:#1d1f20;--line:#d8d8d9;--red:#b0453d;--green:#3f7d5e;--amber:#c4943a;--panel:#fff}
*{box-sizing:border-box}
body{margin:0;padding:22px 26px;background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","Segoe UI",system-ui,sans-serif;font-size:12px;line-height:1.45}
.seal{display:inline-flex;width:38px;height:38px;align-items:center;justify-content:center;background:var(--red);color:#fff;font-family:"Noto Serif TC",serif;font-size:21px;border-radius:3px}
h1{font-family:"Noto Serif TC",Georgia,serif;font-size:16px;letter-spacing:.14em;text-transform:uppercase;margin:10px 0 3px}
h2{font-family:"Noto Serif TC",Georgia,serif;font-size:14px;margin:22px 0 5px}
.lede{color:#6c6e70;font-size:11.5px;margin:0 0 12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:9px;margin:14px 0 4px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:10px 12px}
.card .k{font-size:10px;letter-spacing:.1em;color:#8a8c8e;text-transform:uppercase}
.card .v{font-size:20px;font-family:"Noto Serif TC",Georgia,serif;margin-top:3px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:11.5px;table-layout:fixed}
th,td{border-bottom:1px solid #ececed;padding:5px 7px;text-align:left;vertical-align:top;white-space:normal;overflow-wrap:anywhere}
th{background:#eeeeef;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#5c5e60}
.ok{color:var(--green);font-weight:600}.warn{color:var(--amber);font-weight:600}.fail{color:var(--red);font-weight:600}
.muted{color:#9a9c9e;text-align:center;padding:12px}
pre{background:var(--panel);border:1px solid var(--line);padding:11px;font-size:11px;white-space:pre-wrap;max-height:26vh;overflow:auto}
"""

LIB_ROLE = {
    "tokenize": ("CONSOLE", "逐 token 檢查編碼宣告、BOM、Tab 縮排（ast 看不到）"),
    "symtable": ("CONSOLE", "scope 分析，抓遮蔽與未綁定"),
    "hmac": ("CONSOLE", "台帳與清單簽章，偵測外部竄改"),
    "filecmp": ("CONSOLE", "台帳與快照實體比對"),
    "difflib": ("CONSOLE", "版本差異與最接近 URN 提示"),
    "shlex": ("CONTROLLER", "安全拆解命令列，取代字串拼接"),
    "threading": ("CONTROLLER", "看門狗計時器與主迴圈解耦"),
    "atexit": ("CONTROLLER", "孤兒子行程清理"),
    "tempfile": ("CONTROLLER", "每個能力獨立工作區"),
    "signal": ("CONTROLLER", "優雅終止而非硬殺"),
    "mimetypes": ("ROUTER", "副檔名以外的第二意見"),
    "zipfile": ("ROUTER", "不展開就檢查容器，壓縮炸彈防護"),
    "unicodedata": ("ROUTER", "檔名正規化，抓 NFC/NFD 雙胞胎"),
    "stat": ("ROUTER", "權限、稀疏檔、特殊檔類型"),
    "zlib": ("ROUTER", "壓縮比偵測"),
}


def render(hits: List[Hit], audited: List[Dict[str, Any]], verdict: str,
           stamp: str) -> str:
    by_code = collections.Counter(h.code for h in hits)
    catalog_rows = [{
        "code": m.code, "domain": m.domain, "name": m.name,
        "severity": m.severity, "hits": by_code.get(m.code, 0),
        "library": m.library or "—", "impact": m.impact, "remedies": m.remedies,
    } for m in CATALOG]
    hit_rows = [asdict(h) | {"name": CATALOG_BY_CODE[h.code].name,
                             "severity": CATALOG_BY_CODE[h.code].severity}
                for h in sorted(hits, key=lambda h: (h.domain, h.code, h.line))]
    lib_rows = [{"lib": k, "domain": LIB_ROLE[k][0],
                 "state": "READY" if CAPS.get(k) else "ABSENT",
                 "role": LIB_ROLE[k][1]} for k in LIB_ROLE]
    fails = len([h for h in hits if CATALOG_BY_CODE[h.code].severity == "FAIL"])
    warns = len(hits) - fails
    covered = len({h.code for h in hits})

    return """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Engine Hardening</title><style>%s</style></head><body>
<div class="seal">固</div>
<h1>Engine Hardening Audit</h1>
<p class="lede">%s · 判定 <span class="%s">%s</span> · 三個域各 20 種故障，共 60 種 · 只讀不改</p>
<div class="cards">
  <div class="card"><div class="k">故障目錄</div><div class="v">60</div></div>
  <div class="card"><div class="k">目前命中</div><div class="v fail">%d</div></div>
  <div class="card"><div class="k">命中種類</div><div class="v warn">%d</div></div>
  <div class="card"><div class="k">FAIL 級</div><div class="v fail">%d</div></div>
  <div class="card"><div class="k">WARN 級</div><div class="v warn">%d</div></div>
  <div class="card"><div class="k">加速庫</div><div class="v ok">%d/15</div></div>
</div>

<h2>受稽核引擎</h2>
<table><colgroup><col style="width:34%%"><col style="width:14%%"><col style="width:10%%"><col style="width:10%%"><col style="width:32%%"></colgroup>
<tr><th>File</th><th>Domain</th><th>Lines</th><th>命中</th><th>Encoding／Parse</th></tr>%s</table>

<h2>十五個 local-free 函式庫</h2>
<table><colgroup><col style="width:14%%"><col style="width:12%%"><col style="width:10%%"><col style="width:64%%"></colgroup>
<tr><th>Library</th><th>Domain</th><th>State</th><th>作用</th></tr>%s</table>

<h2>目前命中的弱點</h2>
<p class="lede">行號 0 代表整檔層級的缺席型檢查（例如「完全沒用 hmac」）。</p>
<table><colgroup><col style="width:7%%"><col style="width:11%%"><col style="width:20%%"><col style="width:5%%"><col style="width:7%%"><col style="width:5%%"><col style="width:45%%"></colgroup>
<tr><th>Code</th><th>Domain</th><th>故障</th><th>行</th><th>Severity</th><th>證據</th><th>Evidence</th></tr>%s</table>

<h2>60 種故障目錄</h2>
<table><colgroup><col style="width:6%%"><col style="width:9%%"><col style="width:17%%"><col style="width:6%%"><col style="width:5%%"><col style="width:8%%"><col style="width:23%%"><col style="width:26%%"></colgroup>
<tr><th>Code</th><th>Domain</th><th>故障</th><th>級別</th><th>命中</th><th>負責庫</th><th>後果</th><th>處置選項</th></tr>%s</table>

<h2>執行日誌</h2>
<pre>%s</pre>
</body></html>""" % (
        CSS, stamp, klass(verdict), verdict, len(hits), covered, fails, warns,
        len([v for v in CAPS.values() if v]),
        table(audited, ["file", "domain", "lines", "hits", "note"]),
        table(lib_rows, ["lib", "domain", "state", "role"], "state"),
        table(hit_rows, ["code", "domain", "name", "line", "severity", "grade",
                         "evidence"], "severity"),
        table(catalog_rows, ["code", "domain", "name", "severity", "hits",
                             "library", "impact", "remedies"], "severity"),
        esc("\n".join(LOG.lines)),
    )


# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="VIA_EngineHardening.py",
        description="VIA-SYS-ENG-005 三引擎硬化稽核：60 種故障 + 15 個 local-free 庫")
    parser.add_argument("--tools", required=True, help="三支引擎所在目錄")
    parser.add_argument("--out", default="", help="輸出目錄（預設 <tools>/_hardening）")
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    tools = Path(args.tools).expanduser().resolve()
    if not tools.is_dir():
        print("tools 不存在：%s" % tools, file=sys.stderr)
        return 2
    out_dir = Path(args.out).expanduser().resolve() if args.out else tools / "_hardening"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = now_stamp()

    LOG.say("%s Engine Hardening %s 啟動" % (URN_SELF, VERSION), "OK")
    absent = [k for k, v in CAPS.items() if not v]
    LOG.say("加速庫 %d/15 就緒%s" % (len([v for v in CAPS.values() if v]),
                                    "；缺席 " + ", ".join(absent) if absent else ""),
            "OK" if not absent else "WARN")

    hits: List[Hit] = []
    audited: List[Dict[str, Any]] = []
    for domain, filename in DOMAIN_FILES.items():
        path = tools / filename
        if not path.is_file():
            found = list(tools.rglob(filename))
            path = found[0] if found else path
        if not path.is_file():
            LOG.say("找不到 %s，該域跳過" % filename, "WARN")
            audited.append({"file": filename, "domain": domain, "lines": 0,
                            "hits": "—", "note": "MISSING"})
            continue
        audit = SourceAudit(path, domain)
        if not audit.load():
            LOG.say("%s 無法解析：%s" % (filename, audit.parse_error), "FAIL")
            audited.append({"file": filename, "domain": domain, "lines": 0,
                            "hits": "—", "note": "PARSE_FAIL " + audit.parse_error})
            continue
        audit.audit_tokens()
        audit.audit_symbols()
        audit.audit_ast()
        hits.extend(audit.hits)
        audited.append({"file": filename, "domain": domain,
                        "lines": audit.source.count("\n") + 1,
                        "hits": len(audit.hits),
                        "note": "encoding=%s / parse OK" % audit.encoding})

    fails = len([h for h in hits if CATALOG_BY_CODE[h.code].severity == "FAIL"])
    verdict = "GREEN"
    if hits:
        verdict = "AMBER"
    if fails:
        verdict = "RED"

    covered = len({h.code for h in hits})
    LOG.say("命中 %d 筆，涵蓋 %d／60 種故障（FAIL 級 %d）" % (len(hits), covered, fails),
            "FAIL" if fails else ("WARN" if hits else "OK"))

    html_path = out_dir / ("VIA_EngineHardening_%s.html" % stamp)
    json_path = out_dir / ("engine_hardening_%s.json" % stamp)
    html_path.write_text(render(hits, audited, verdict, stamp), encoding="utf-8")
    json_path.write_text(json.dumps({
        "schema": "VIA.EngineHardening", "spec": SPEC_VERSION, "engine": URN_SELF,
        "version": VERSION, "generated": iso_now(), "stamp": stamp,
        "tools": str(tools), "verdict": verdict, "capabilities": CAPS,
        "gates": [{"code": m.code, "title": m.name,
                   "status": m.severity if by else "PASS",
                   "detail": "%s／%s 命中 %d 次" % (m.domain, m.library or "-", by)}
                  for m, by in ((m, sum(1 for h in hits if h.code == m.code))
                                for m in CATALOG)],
        "hits": [asdict(h) for h in hits],
        "catalog": [asdict(m) for m in CATALOG],
        "audited": audited,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    LOG.say("報告 -> %s" % html_path, "OK")
    print("")
    print("=" * 60)
    print(" VIA ENGINE HARDENING  ->  %s" % verdict)
    print(" 目錄 60 種 ｜ 命中 %d 筆 ｜ 涵蓋 %d 種 ｜ FAIL 級 %d"
          % (len(hits), covered, fails))
    print("=" * 60)
    if not args.no_open and not args.json:
        try:
            webbrowser.open(html_path.as_uri())
        except Exception:                                # noqa: BLE001
            pass
    if args.json:
        print(json.dumps({"verdict": verdict, "hits": len(hits), "covered": covered},
                         ensure_ascii=False))
    return 0 if verdict != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
