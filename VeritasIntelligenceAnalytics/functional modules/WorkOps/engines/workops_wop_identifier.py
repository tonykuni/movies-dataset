# -*- coding: utf-8 -*-
r"""WorkOps WOP 識別歸戶引擎 v0107(ENG-028)— 規劃書 M1+M2:bottom-up 多訊號融合 → WOP 專案化+賦號

v0107(產品化令 2026/08/09):sheet_aliases 增 TheirCode(對方編號/客戶案號/PO no…)—
  對方編號永不改、只對照:辨識後原值原樣保留同列,供板面與 AI 控管表提示詞對照欄使用;
  置於 ProjectCode 之前,避免「對方編號」被「編號」模糊吸入。板 v0118 $SheetAlias PS 複本同步。

v0106(操作員 SSOT 彙整去重令 2026/08/09):
  共用詞彙收斂 — regex/正規化/清單載入一律 import workops_lexicon(去重正本);
  S9 機構名訊號 — org_lexicon.json(族群 149 家+SuperBOM 38 機構,SSOT 附件萃取):
  主旨或寄件顯示名含機構名 → 中票進融合(不強判);
  domains 動詞 — 收割寄件網域+內文 URL 網域+常見寄件顯示名 → out/domain_candidates.csv
  提議清單(操作員核對後貼入 domain_map=L5 白名單;爬站不做 — run-local 紅線,
  郵件上方機構名+網域已足萃取)。

v0105(操作員四維擷取對照令):L1 內文代號補全 — 主旨漏帶代號時掃 BODY_SNIPPET
  (scanrange 索引;唯讀既有匯出,零新增觸碰):內文代號屬「已知代號」(控管表/學習
  記憶/既有 WOP 鍵)才確定性直判;未知內文代號僅弱票進融合 — 內文比主旨雜,不硬錨。

v0104(操作員 準確度報告 v1.0 掛載令):八層路由瀑布 — 由精準至模糊,逐層命中即終止:
  L0 雜訊池(bulk+noise 規則→專用槽 wop_noise.csv 可回顧,不刪不分類)
  L2 已確認串(人工確認=最高真相,置於 L1 前 — 鐵律①)→ L1 主旨案號錨點(100%)
  L3/L4 product_code_map.json 規則(domain+主旨 regex+附件 AND 組合→強制歸戶)
  L5 網域白名單(domain_map 確定性直判)→ L6 相似已核對名(difflib ≥ fuzzy_threshold
  高票進融合,分歧仍問 — 不強判)→ L7 附件指紋(規則 attach_regex 輔助票)
  → L8 加權融合(既有)= 唯一產生人工候選之處。逐層命中分佈落 wop_route_stats.json。
  路由序 routing_priority 可調(參數=JSON);錯誤的永久錨定比校正更貴 — 相似度永不強判。

v0103(操作員 Gemini 研究令 2026/08/09):
  S4 資料夾訊號轉正 — 你在 Outlook 手動分信=免費人工標註:讀最新 scanrange RUN 之
  01_mail_index.csv(FOLDER_NAME/CONVERSATION_ID),資料夾名含 WOP 編號/代號=強票,
  一般自建資料夾名=中票(系統資料夾黑名單排除);異質控管表表頭映射(alias 字典,
  案號/Trace_ID/承辦人等自動對齊)。

v0102(操作員 ONE POWERSHELL 令):apply 吸收預設確認檔後改名 wop_confirm.applied.<ts>.csv
  (只增不減不刪檔;防重複吸收)— ALL 總指揮可安全自動吸收。實跑戰果:AUTO 129/87 案/ASK 0。

v0101(操作員實跑 2026/08/08:AUTO 0 · ASK 129 — 個人信箱無控管表時全數進人工佇列):
  已核對名稱=操作員親手核對過的訊號(等同人工確認)→ 獨立權重 s3_approved 直接 AUTO;
  未核對提議名維持弱票進 ASK;佇列按信心分數排序(最有把握的先看)。能全自動的絕不半自動。

操作員裁決(2026/08/08 M365 規劃書 v1.3):補強註冊功能/工具 · 整合所有工具 · 建立 U/I。
規劃書 Phase 0:接通 S1–S8 訊號源 → 融合投票 → AUTO/ASK/QUARANTINE 三層分流 →
WopConfirmQueue.html(mouse-only:預選+chips+全部接受)→ WOP 賦號 registry。

訊號源(本版接通;缺料誠實降級,絕不硬判):
  S1 主旨代號叢集   [A-Z]{2,6}-\d{2,6} regex(指揮板③頁同式)
  S2 控管表         ProjectCode 對上 = 最強票(top-down 知識正門)
  S3 命名帳本       THR→CASE(thr_case_map)→ 已核對/提議名稱(ENG-023 正本)
  S5 寄件網域       identifier_params.json domain_map(操作員可增列);未對映網域弱票
  S6 收件組合       pending.csv TO 網域(同對口圈弱票)
  S7 案件互鏈       同 CASE 之 THR 已有 WOP → 強票歸同案(thr_case_map v0101 既有)
  LEARN 學習記憶    wop_confirmations.jsonl:每次人工確認 = 訓練資料 → 同類下次 AUTO
                    (規劃書「手動量單調遞減」機制)

分流(權重/門檻全在 identifier_params.json — 參數=JSON 鐵律):
  AUTO       最佳票 ≥ auto_threshold 且領先次佳 ≥ margin → 直接歸戶賦號,零人工
  ASK        有訊號但分歧/不足 → WopConfirmQueue.html 滑鼠一鍵確認
  QUARANTINE 訊號不足 → 留置,新郵件累積後自動重判(F10:留置可見不成黑洞)

賦號(M2):WOP-#### 沿用板側 workops_id_ledger.json(seq_wop + map["WOP|鍵"])—
  單一序號源不碰撞(F11);編號一經賦予永不變;wop_registry.json 存專案中繼資料
  (label/狀態/THR 成員/證據鏈/history,append-only)。Outlook 原件零觸碰。

動詞:propose(預設)/ apply [csv] / list / status
  propose → 融合分流 + 產 out/WopConfirmQueue.html
  apply   → 讀 out/wop_confirm.csv(UI 下載或手填:THR,WOP鍵,名稱)→ 確認入帳
            + append wop_confirmations.jsonl(學習記憶)
治理:唯讀;side-car;只增不減;誠實逐段回報。
"""
import argparse, csv, difflib, io, json, re, sqlite3, sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from workops_lexicon import (CODE_RE, PREFIX_RE, TAG_RE, WOPID_RE, norm_subj, subj_code,
                             load_bulk_patterns, is_bulk, load_org_lexicon, extract_url_domains)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE     = Path(__file__).resolve().parent            # engines/
WORKOPS  = HERE.parent
OUT      = WORKOPS / "out"
PARAMS_P = HERE / "identifier_params.json"
LEDGER_P = OUT / "workops_id_ledger.json"
REG_P    = OUT / "wop_registry.json"
CONF_P   = OUT / "wop_confirmations.jsonl"
QUEUE_P  = OUT / "WopConfirmQueue.html"
CONFIRM_CSV = OUT / "wop_confirm.csv"
MAILS_P  = OUT / "mails.csv"
PEND_P   = OUT / "pending.csv"
NAMING_P = OUT / "workops_naming.json"
THRMAP_P = OUT / "thr_case_map.json"
DB_P     = OUT / "deep" / "engine_out" / "super_engine.db"
BULK_P   = HERE / "bulk_senders.txt"
PCMAP_P  = HERE / "product_code_map.json"
NOISE_P  = OUT / "wop_noise.csv"
STATS_P  = OUT / "wop_route_stats.json"

DEFAULT_PARAMS = {
    "weights": {"s1_code": 3.0, "s2_sheet": 4.0, "s3_name": 2.0, "s3_approved": 4.5,
                "s4_folder": 2.5, "s4_folder_strong": 4.0,
                "s5_domain": 1.5, "s6_recipient": 1.0, "s7_case": 3.5, "s9_org": 2.0, "learned": 5.0},
    "auto_threshold": 4.0, "margin": 1.5, "ask_threshold": 1.0,
    "min_group_mails": 1, "domain_map": {}, "bulk_skip": True,
    "routing_priority": ["L0", "L2", "L1", "L3", "L5"],
    "fuzzy_threshold": 0.90,
    "folder_blacklist": ["收件匣", "inbox", "寄件備份", "sent", "垃圾", "junk", "deleted",
                         "刪除", "封存", "archive", "rss", "草稿", "drafts", "行事曆",
                         "calendar", "連絡人", "contacts", "工作", "tasks", "記事",
                         "notes", "同步處理", "outbox", "重要", "clutter"],
    "sheet_aliases": {
        "TheirCode": ["theircode", "對方編號", "對方案號", "對方代號", "客戶編號", "客戶案號",
                      "供應商編號", "來文編號", "來文文號", "貴司編號", "客編",
                      "po no", "po number", "ref no", "reference no", "their ref"],
        "ProjectCode": ["projectcode", "專案代號", "案號", "案件編號", "代號", "編號",
                        "trace_id", "wop_id", "tracking no", "trackingno", "code", "id"],
        "ProjectName": ["projectname", "專案名稱", "案名", "名稱", "項目", "project",
                        "task", "activity", "主題", "作業步驟"]
    },
}



def sheet_normalize(rows, params):
    """v0103:異質表頭映射 — 各行各業欄名對齊 ProjectCode/ProjectName(對不上保留原名)。"""
    if not rows:
        return rows
    aliases = params.get("sheet_aliases", DEFAULT_PARAMS["sheet_aliases"])
    src_cols = list(rows[0].keys())
    col_map = {}
    used = set()
    for src in src_cols:
        k = (src or "").strip().lower()
        for std, al in aliases.items():
            if std in used:
                continue
            if k in al or any(a in k for a in al):
                col_map[src] = std
                used.add(std)
                break
    if not col_map:
        return rows
    out = []
    for r in rows:
        nr = {}
        for c, v in r.items():
            nr[col_map.get(c, c)] = v
        out.append(nr)
    return out


def load_folder_map():
    """v0103 S4:最新 scanrange RUN 的 conv→自建資料夾名;v0104 併回附件檔名(L7)。"""
    root = OUT / "deep" / "scanrange"
    if not root.exists():
        return {}, {}
    runs = sorted([d for d in root.iterdir() if d.is_dir() and d.name.startswith("RUN_")])
    if not runs:
        return {}, {}
    m, am, bm, fm = {}, {}, {}, {}
    for r in read_csv(runs[-1] / "01_mail_index.csv"):
        cid = (r.get("CONVERSATION_ID") or "").strip()
        fn = (r.get("FOLDER_NAME") or "").strip()
        an = (r.get("ATTACHMENT_NAMES") or "").strip()
        bs = (r.get("BODY_SNIPPET") or "").strip()
        fr = (r.get("FROM") or "").strip()
        if cid and fn and cid not in m:
            m[cid] = fn
        if cid and an and cid not in am:
            am[cid] = an
        if cid and bs and cid not in bm:
            bm[cid] = bs[:600]
        if cid and fr and cid not in fm:
            fm[cid] = fr
    return m, am, bm, fm


def load_product_rules():
    """v0104 L3/L4:product_code_map.json 啟用規則(enabled!=false);缺席回空。"""
    d = load_json(PCMAP_P, {})
    out = []
    for r in d.get("rules", []):
        if not isinstance(r, dict) or r.get("enabled") is False or not r.get("code"):
            continue
        try:
            r["_subj_re"] = re.compile(r["subject_regex"], re.IGNORECASE) if r.get("subject_regex") else None
            r["_att_re"] = re.compile(r["attach_regex"], re.IGNORECASE) if r.get("attach_regex") else None
        except re.error:
            continue                                  # 壞 regex 隔離不阻斷
        out.append(r)
    return out


def rule_match(rule, subj, dom, attach):
    """規則所列條件全命中才算中(AND 組合=L4)。"""
    hit = False
    if rule.get("domain"):
        if rule["domain"].lower() not in (dom or ""):
            return False
        hit = True
    if rule.get("_subj_re") is not None:
        if not rule["_subj_re"].search(subj or ""):
            return False
        hit = True
    if rule.get("_att_re") is not None:
        if not rule["_att_re"].search(attach or ""):
            return False
        hit = True
    return hit


def folder_blacklisted(name, params):
    n = (name or "").strip().lower()
    return any(b in n for b in params.get("folder_blacklist", []))


def now():
    return datetime.now().isoformat(timespec="seconds")


def load_params():
    if PARAMS_P.exists():
        try:
            p = json.loads(PARAMS_P.read_text(encoding="utf-8-sig"))
            merged = dict(DEFAULT_PARAMS)
            merged.update({k: v for k, v in p.items() if k in DEFAULT_PARAMS or k == "weights"})
            w = dict(DEFAULT_PARAMS["weights"]); w.update(p.get("weights", {}))
            merged["weights"] = w
            return merged
        except Exception as e:
            print("[注意] 參數檔讀取失敗用內建預設:%s" % e)
    return dict(DEFAULT_PARAMS)


def load_json(p, default):
    if Path(p).exists():
        try:
            return json.loads(Path(p).read_text(encoding="utf-8-sig"))
        except Exception:
            return default
    return default


def read_csv(p):
    if not Path(p).exists():
        return []
    try:
        with io.open(p, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def control_sheet_rows(params=None):
    for cand in (WORKOPS / "control_sheet.csv",
                 WORKOPS.parent.parent / "control_sheet.csv"):   # 板 v0112 同式:庫根後備
        rows = read_csv(cand)
        if rows:
            return sheet_normalize(rows, params or DEFAULT_PARAMS)   # v0103:表頭映射
    return []


def load_confirmations():
    """學習記憶:domain→鍵、code→鍵、thr→鍵(最新一筆為準;append-only 檔)。"""
    by_dom, by_code, by_thr = {}, {}, {}
    if CONF_P.exists():
        for ln in CONF_P.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
            except Exception:
                continue                       # F19:壞列隔離不阻斷
            k = r.get("wop_key") or ""
            if not k:
                continue
            if r.get("domain"):
                by_dom[r["domain"]] = k
            if r.get("code"):
                by_code[r["code"]] = k
            if r.get("thr"):
                by_thr[r["thr"]] = k
    return by_dom, by_code, by_thr


def load_ledger():
    led = load_json(LEDGER_P, None)
    if not isinstance(led, dict) or "map" not in led:
        led = {"seq_wop": 0, "seq_thr": 0, "map": {}}
    led.setdefault("seq_wop", 0); led.setdefault("seq_thr", 0); led.setdefault("map", {})
    return led


def save_ledger(led):
    LEDGER_P.parent.mkdir(parents=True, exist_ok=True)
    tmp = LEDGER_P.with_suffix(".tmp")                  # F13:原子寫,永不原地覆寫
    tmp.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(LEDGER_P)


def load_registry():
    reg = load_json(REG_P, None)
    if not isinstance(reg, dict) or "projects" not in reg:
        reg = {"version": "v0100", "append_only": True, "projects": {}, "thr2wop": {}}
    reg.setdefault("projects", {}); reg.setdefault("thr2wop", {})
    return reg


def save_registry(reg):
    REG_P.parent.mkdir(parents=True, exist_ok=True)
    tmp = REG_P.with_suffix(".tmp")
    tmp.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(REG_P)


def ensure_wop_id(led, key):
    """M2 賦號:沿用板側帳本 map["WOP|鍵"] — 單一序號源;編號一經賦予永不變。"""
    mk = "WOP|" + key
    if mk in led["map"]:
        return led["map"][mk], False
    led["seq_wop"] = int(led.get("seq_wop", 0)) + 1
    wid = "WOP-%04d" % led["seq_wop"]
    led["map"][mk] = wid
    return wid, True


# ---------------------------------------------------------------- signal fusion
def gather(params):
    """每 THR 收集訊號票 → {thr: {"votes": {鍵: 分}, "why": {鍵: [訊號...]}, "subj", "sender"}}"""
    w = params["weights"]
    bulk_pats = load_bulk_patterns(BULK_P) if params.get("bulk_skip", True) else []
    led = load_ledger()
    conv2thr = {k[4:]: v for k, v in led["map"].items() if k.startswith("THR|")}

    mails = read_csv(MAILS_P)
    by_conv = {}
    for r in mails:
        cid = (r.get("ConversationID") or "").strip()
        if cid:
            by_conv.setdefault(cid, []).append(r)

    sheet = control_sheet_rows(params)
    sheet_codes = {}
    for r in sheet:
        c = (r.get("ProjectCode") or "").strip().upper()
        if c:
            sheet_codes[c] = (r.get("ProjectName") or "").strip()

    naming = load_json(NAMING_P, {}).get("entries", {})
    thrmap = load_json(THRMAP_P, {}).get("map", {})
    dom_map = {k.lower(): v for k, v in params.get("domain_map", {}).items()}
    lrn_dom, lrn_code, lrn_thr = load_confirmations()

    pend = read_csv(PEND_P)
    pend_to = {}
    for r in pend:
        cid = (r.get("CASE_ID") or "").strip()
        to = (r.get("TO") or "").strip()
        if cid and to:
            pend_to[cid] = to

    reg = load_registry()
    case2wopkey = {}
    id2key = {}
    for wid, pj in reg["projects"].items():
        id2key[wid] = pj["key"]
        for t in pj.get("thr", []):
            c = thrmap.get(t)
            if c:
                case2wopkey.setdefault(c, pj["key"])
    folder_map, attach_map, body_map, from_map = load_folder_map()
    org_names, _orgmeta = load_org_lexicon()
    known_codes = set(sheet_codes) | set(lrn_code)
    for _k in id2key.values():
        if _k.startswith("CODE:"):
            known_codes.add(_k[5:])
    prules = load_product_rules()
    fuzzy_cut = float(params.get("fuzzy_threshold", 0.90))
    appr_norm = {}
    for _cs, _e in naming.items():
        if _e.get("approved"):
            appr_norm[norm_subj(_e["approved"])] = _e["approved"]
    route_order = params.get("routing_priority", DEFAULT_PARAMS["routing_priority"])

    sig = {}
    noise = []
    for conv, thr in conv2thr.items():
        rows = by_conv.get(conv, [])
        subj = rows[0].get("Subject", "") if rows else ""
        sender = rows[0].get("SenderEmail", "") if rows else ""
        dom0 = (sender.split("@")[-1] or "").lower() if "@" in (sender or "") else ""
        att0 = attach_map.get(conv, "")
        # ---- L0 雜訊池:bulk 樣式 + noise 規則 → 專用槽(可回顧,不刪不分類)----
        if rows and is_bulk(sender, bulk_pats):
            noise.append({"thr": thr, "subj": subj, "sender": sender, "slot": "NOISE-BULK"})
            continue
        nz = next((r for r in prules if r.get("noise") and rule_match(r, subj, dom0, att0)), None)
        if nz:
            noise.append({"thr": thr, "subj": subj, "sender": sender, "slot": nz["code"]})
            continue
        votes, why = Counter(), {}

        def vote(key, pts, tag):
            if not key:
                return
            votes[key] += pts
            why.setdefault(key, []).append(tag)

        code = subj_code(subj)
        if code:
            vote("CODE:" + code, w["s1_code"], "S1 主旨代號 " + code)
            if code in sheet_codes:
                vote("CODE:" + code, w["s2_sheet"], "S2 控管表 " + (sheet_codes[code] or code))
            if code in lrn_code:
                vote(lrn_code[code], w["learned"], "LEARN 代號記憶")
        else:
            bcode = subj_code(body_map.get(conv, ""))
            if bcode and bcode not in known_codes:        # v0105:未知內文代號=弱票不硬錨
                vote("CODE:" + bcode, w["s1_code"] * 0.6, "S1 內文代號(弱) " + bcode)
        case = thrmap.get(thr, "")
        if case:
            ent = naming.get(case) or {}
            if ent.get("approved"):                      # v0101:已核對名=人工確認級訊號
                vote("NAME:" + ent["approved"], w.get("s3_approved", 4.5), "S3 已核對名 " + ent["approved"])
            elif ent.get("proposed"):
                vote("NAME:" + ent["proposed"], w["s3_name"], "S3 提議名(未核對) " + ent["proposed"])
            if case in case2wopkey:
                vote(case2wopkey[case], w["s7_case"], "S7 同案互鏈 " + case)
        dom = (sender.split("@")[-1] or "").lower() if "@" in (sender or "") else ""
        if dom:
            if dom in dom_map:
                vote("DOM:" + dom_map[dom], w["s5_domain"], "S5 網域對映 " + dom)
            if dom in lrn_dom:
                vote(lrn_dom[dom], w["learned"], "LEARN 網域記憶 " + dom)
        fol = folder_map.get(conv, "")
        if fol and not folder_blacklisted(fol, params):
            wm = WOPID_RE.search(fol.upper())
            fcode = subj_code(fol)
            if wm and wm.group(0) in id2key:
                vote(id2key[wm.group(0)], w.get("s4_folder_strong", 4.0), "S4 資料夾含編號 " + fol)
            elif fcode:
                vote("CODE:" + fcode, w.get("s4_folder_strong", 4.0), "S4 資料夾含代號 " + fol)
            else:
                vote("NAME:" + fol[:40], w.get("s4_folder", 2.5), "S4 自建資料夾 " + fol)
        to = pend_to.get(conv, "")
        tdom = (to.split("@")[-1] or "").lower() if "@" in to else ""
        if tdom:
            if tdom in dom_map:
                vote("DOM:" + dom_map[tdom], w["s6_recipient"], "S6 對口網域 " + tdom)
            if tdom in lrn_dom:
                vote(lrn_dom[tdom], w["learned"], "LEARN 對口記憶 " + tdom)
        if thr in lrn_thr:
            vote(lrn_thr[thr], w["learned"] * 2, "LEARN 本串人工確認")
        # ---- L6 相似已核對名(difflib;高票進融合,分歧仍問 — 不強判)----
        ns = norm_subj(subj)
        if ns and appr_norm:
            close = difflib.get_close_matches(ns, list(appr_norm), n=1, cutoff=fuzzy_cut)
            if close:
                vote("NAME:" + appr_norm[close[0]], w.get("s3_approved", 4.5),
                     "L6 相似已核對名 " + appr_norm[close[0]])
        # ---- L7 附件指紋(規則 attach_regex 輔助票)----
        for pr in prules:
            if pr.get("noise") or pr.get("_att_re") is None:
                continue
            if rule_match(pr, subj, dom0, att0):
                vote("PC:" + pr["code"], w.get("s4_folder", 2.5), "L7 附件指紋 " + pr["code"])
        # ---- S9 機構名訊號(org_lexicon;主旨+寄件顯示名;中票不強判)----
        s9text = subj + " " + from_map.get(conv, "")
        n_hit = 0
        for onm in org_names:
            if onm in s9text:
                vote("ORG:" + onm, w.get("s9_org", 2.0), "S9 機構名 " + onm)
                n_hit += 1
                if n_hit >= 2:
                    break
        # ---- 確定性路由(命中即終止;序列 routing_priority)----
        route = None
        for layer in route_order:
            if layer == "L2" and thr in lrn_thr:
                route = (lrn_thr[thr], "L2", "")
            elif layer == "L1":
                c1 = subj_code(subj)
                if c1:
                    route = ("CODE:" + c1, "L1", sheet_codes.get(c1, ""))
                else:
                    cb = subj_code(body_map.get(conv, ""))
                    if cb and cb in known_codes:          # v0105:內文代號限已知才直判
                        route = ("CODE:" + cb, "L1", sheet_codes.get(cb, ""))
            elif layer in ("L3", "L4"):
                pr = next((r for r in prules if not r.get("noise") and rule_match(r, subj, dom0, att0)), None)
                if pr:
                    route = ("PC:" + pr["code"], "L3", pr.get("name", ""))
            elif layer == "L5" and dom0 and dom0 in dom_map:
                route = ("DOM:" + dom_map[dom0], "L5", dom_map[dom0])
            if route:
                break
        if route:
            why.setdefault(route[0], []).append(route[1] + " 確定性路由")
        sig[thr] = {"votes": votes, "why": why, "subj": subj, "sender": sender,
                    "route": route}
    return sig, sheet_codes, naming, noise


def classify(sig, params):
    auto, ask, quarantine, layer_hits = {}, {}, [], Counter()
    for thr, d in sorted(sig.items()):
        if d.get("route"):
            auto[thr] = d["route"][0]
            layer_hits[d["route"][1]] += 1
            continue
        votes = d["votes"]
        if not votes:
            quarantine.append(thr)
            layer_hits["L8-留置"] += 1
            continue
        ranked = votes.most_common()
        best_key, best = ranked[0]
        second = ranked[1][1] if len(ranked) > 1 else 0.0
        if best >= params["auto_threshold"] and (best - second) >= params["margin"]:
            auto[thr] = best_key
            layer_hits["L8-融合AUTO"] += 1
        elif best >= params["ask_threshold"]:
            ask[thr] = ranked
            layer_hits["L8-候選"] += 1
        else:
            quarantine.append(thr)
            layer_hits["L8-留置"] += 1
    return auto, ask, quarantine, layer_hits


def wop_label(key, sheet_codes, naming):
    if key.startswith("CODE:"):
        c = key[5:]
        return sheet_codes.get(c) or c
    if key.startswith(("NAME:", "DOM:", "PC:", "ORG:")):
        return key[key.index(":") + 1:]
    return key


def assign(reg, led, thr, key, label, status, evidence):
    wid, fresh = ensure_wop_id(led, key)
    pj = reg["projects"].get(wid)
    if pj is None:
        pj = {"key": key, "label": label, "status": status, "thr": [],
              "history": [{"ts": now(), "action": "CREATE", "value": key}]}
        reg["projects"][wid] = pj
    if status == "confirmed" and pj.get("status") != "confirmed":
        pj["status"] = "confirmed"                      # 只升不降
        pj["history"].append({"ts": now(), "action": "CONFIRM", "value": ""})
    if label and pj.get("status") != "confirmed" and pj.get("label") != label:
        pj["label"] = label
    if thr not in pj["thr"]:
        pj["thr"].append(thr)
        pj["history"].append({"ts": now(), "action": "ATTACH", "value": thr + (" · " + evidence if evidence else "")})
    old = reg["thr2wop"].get(thr)
    reg["thr2wop"][thr] = wid
    return wid, fresh, old not in (None, wid)


# ---------------------------------------------------------------- queue UI
def build_queue_html(ask, quarantine, sig, sheet_codes, naming):
    """mouse-only 確認佇列:預選+chips+全部接受+下載確認檔(規劃書 §02 ASK 分流 UI)。"""
    items = []
    for thr, ranked in sorted(ask.items(), key=lambda kv: -kv[1][0][1]):   # v0101:信心高者先看
        d = sig[thr]
        items.append({
            "thr": thr, "subj": d["subj"][:90], "sender": d["sender"],
            "cands": [{"key": k, "score": round(s, 1),
                       "label": wop_label(k, sheet_codes, naming),
                       "why": " · ".join(d["why"].get(k, []))} for k, s in ranked[:4]],
        })
    q_items = [{"thr": t, "subj": sig[t]["subj"][:90], "sender": sig[t]["sender"]} for t in quarantine]
    data = json.dumps({"generated": now(), "ask": items, "quarantine": q_items},
                      ensure_ascii=False).replace("</", "<\\/")
    html = QUEUE_TEMPLATE.replace("__WOP_DATA__", data)
    QUEUE_P.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_P.write_text(html, encoding="utf-8")
    return len(items), len(q_items)


QUEUE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WOP 歸戶確認佇列 · mouse-only</title>
<style>
body{font-family:"Segoe UI","Microsoft JhengHei",sans-serif;background:#f5f4f0;color:#1b1a17;margin:0;padding:18px;font-size:13.5px}
h1{font-size:17px;margin:0 0 2px}
.sub{color:#8a877f;font-size:12px;margin-bottom:12px}
.banner{background:#fff8e7;border:1px solid #e3d9b8;border-left:4px solid #bf8f33;border-radius:8px;padding:9px 13px;margin:10px 0;font-size:12.5px}
.card{background:#fff;border:1px solid #dedbd2;border-radius:10px;padding:11px 14px;margin:9px 0}
.thr{font-family:Consolas,monospace;font-weight:700;color:#4c78a8}
.subj{margin:3px 0 7px}
.snd{color:#8a877f;font-size:11.5px}
.chip{display:inline-block;border:1.5px solid #c9c5ba;border-radius:16px;padding:5px 13px;margin:3px 6px 3px 0;cursor:pointer;font-size:12.5px;background:#fff;user-select:none}
.chip.on{border-color:#4f9465;background:#eef5ef;box-shadow:inset 0 0 0 1px #4f9465}
.chip small{color:#8a877f;margin-left:5px}
.why{color:#8a877f;font-size:11px;margin:2px 0 0}
.topbar{position:sticky;top:0;background:#f5f4f0;padding:8px 0;z-index:5;display:flex;gap:10px;flex-wrap:wrap;align-items:center}
button{border:1px solid #c9c5ba;border-radius:8px;padding:8px 16px;font-size:13px;cursor:pointer;background:#fff}
button.primary{background:#1e5c2f;color:#fff;border-color:#1e5c2f;font-weight:700}
.qz{opacity:.8}
.count{font-weight:700}
.done{color:#1e5c2f;font-weight:700}
@media (prefers-reduced-motion: no-preference){.chip{transition:all .12s ease}.chip:hover{transform:translateY(-1px)}}
</style></head><body>
<h1>WOP 歸戶確認佇列(mouse-only)</h1>
<div class="sub" id="sub"></div>
<div class="banner">分歧件才會出現在這裡 — 每列已預選模型最可能答案;不同意就點別的 chip。完成後「下載確認檔」→ 存到 WorkOps\\out\\wop_confirm.csv → 回 PowerShell 跑 via-workops wop apply。每次確認都是訓練資料,同類案下次直接自動歸戶。</div>
<div class="topbar">
 <button class="primary" id="acceptAll">全部接受預選建議</button>
 <button id="dl">下載確認檔 wop_confirm.csv</button>
 <span id="st"></span>
</div>
<div id="list"></div>
<h1 style="margin-top:18px;font-size:15px">留置區 QUARANTINE(訊號不足;新郵件累積後自動重判)</h1>
<div id="qlist" class="qz"></div>
<script>
var DATA = __WOP_DATA__;
var PICK = {};
function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
document.getElementById("sub").textContent="生成 "+DATA.generated+" · 待確認 "+DATA.ask.length+" 串 · 留置 "+DATA.quarantine.length+" 串";
function renderList(){
 var h="";
 DATA.ask.forEach(function(it,i){
  h+="<div class='card'><span class='thr'>"+esc(it.thr)+"</span><div class='subj'>"+esc(it.subj)+"</div><div class='snd'>"+esc(it.sender)+"</div>";
  it.cands.forEach(function(c,j){
   var on=(PICK[it.thr]===c.key)?" on":"";
   h+="<span class='chip"+on+"' data-thr='"+esc(it.thr)+"' data-key='"+esc(c.key)+"'>"+esc(c.label)+"<small>"+c.score+"</small></span>";
   if(on)h+="<div class='why'>"+esc(c.why)+"</div>";
  });
  h+="</div>";
 });
 if(!DATA.ask.length)h="<div class='card done'>沒有分歧件 — 全部已自動歸戶 ✔</div>";
 document.getElementById("list").innerHTML=h;
 document.querySelectorAll(".chip").forEach(function(ch){
  ch.addEventListener("click",function(){PICK[ch.dataset.thr]=ch.dataset.key;renderList();stat();});});
}
function stat(){
 var n=Object.keys(PICK).length;
 document.getElementById("st").innerHTML="<span class='count'>"+n+"/"+DATA.ask.length+"</span> 已選";
}
document.getElementById("acceptAll").addEventListener("click",function(){
 DATA.ask.forEach(function(it){if(it.cands.length&&!PICK[it.thr])PICK[it.thr]=it.cands[0].key;});
 renderList();stat();
});
document.getElementById("dl").addEventListener("click",function(){
 var lines=["THR,WOP鍵,名稱"];
 DATA.ask.forEach(function(it){
  var k=PICK[it.thr];if(!k)return;
  var c=it.cands.filter(function(x){return x.key===k;})[0]||{};
  lines.push('"'+it.thr+'","'+String(k).replace(/"/g,"'")+'","'+String(c.label||"").replace(/"/g,"'")+'"');
 });
 var csv="\\ufeff"+lines.join("\\r\\n");
 try{
  var a=document.createElement("a");
  a.href=URL.createObjectURL(new Blob([csv],{type:"text/csv"}));
  a.download="wop_confirm.csv";a.click();
 }catch(e){window.prompt("複製後另存 wop_confirm.csv:",csv);}
});
var qh="";
DATA.quarantine.forEach(function(q){qh+="<div class='card'><span class='thr'>"+esc(q.thr)+"</span><div class='subj'>"+esc(q.subj)+"</div><div class='snd'>"+esc(q.sender)+"</div></div>";});
if(!DATA.quarantine.length)qh="<div class='card'>留置區空 ✔</div>";
document.getElementById("qlist").innerHTML=qh;
renderList();stat();
</script></body></html>
"""


# ---------------------------------------------------------------- verbs
def cmd_propose():
    if not MAILS_P.exists():
        print("[FAIL] out\\mails.csv 不在位 — 先跑 via-workops(板掃描)")
        return 1
    params = load_params()
    sig, sheet_codes, naming, noise = gather(params)
    if not sig and not noise:
        print("[空] 帳本無 THR 串 — 先跑 via-workops(板會賦 THR 編號)")
        return 0
    auto, ask, quarantine, layer_hits = classify(sig, params)
    led = load_ledger()
    reg = load_registry()
    n_auto = n_new = 0
    for thr, key in sorted(auto.items()):
        d = sig[thr]
        rt = d.get("route")
        label = (rt[2] if rt and rt[2] else "") or wop_label(key, sheet_codes, naming)
        evidence = " · ".join(d["why"].get(key, []))
        wid, fresh, moved = assign(reg, led, thr, key, label, "auto", evidence)
        n_auto += 1
        if fresh:
            n_new += 1
    save_ledger(led)
    save_registry(reg)
    n_ask, n_q = build_queue_html(ask, quarantine, sig, sheet_codes, naming)
    # ---- L0 雜訊槽落盤(可回顧;每輪重寫快照)----
    if noise:
        layer_hits["L0-雜訊"] = len(noise)
        with io.open(NOISE_P, "w", encoding="utf-8-sig", newline="") as f:
            wn = csv.writer(f)
            wn.writerow(["THR", "槽位", "寄件者", "主旨"])
            for z in noise:
                wn.writerow([z["thr"], z["slot"], z["sender"], z["subj"]])
    # ---- 逐層命中分佈(KPI:L8 佔比萎縮=系統在學)----
    STATS_P.write_text(json.dumps({"ts": now(), "hits": dict(layer_hits),
                                   "total": len(sig), "noise": len(noise)},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
    dist = " · ".join("%s %d" % (k, v) for k, v in sorted(layer_hits.items()))
    print("[歸戶] THR %d 串:AUTO %d(新 WOP %d)· ASK %d · 留置 %d · 雜訊槽 %d"
          % (len(sig), n_auto, n_new, n_ask, n_q, len(noise)))
    print("[路由] " + (dist if dist else "(無)") + " → %s" % STATS_P.name)
    print("[專案] WOP 共 %d 案 → %s" % (len(reg["projects"]), REG_P))
    if n_ask:
        print("[確認] 開 %s 滑鼠一鍵清空(預選+chips+全部接受)→ 下載 wop_confirm.csv → via-workops wop apply" % QUEUE_P)
    else:
        print("[確認] 無分歧件 — 全自動歸戶完成")
    return 0


def cmd_apply(csvpath):
    p = Path(csvpath) if csvpath else CONFIRM_CSV
    if not p.exists():
        print("[FAIL] 確認檔不在位:%s(佇列頁「下載確認檔」後存到 out\\)" % p)
        return 1
    params = load_params()
    sig, sheet_codes, naming, _noise = gather(params)
    led = load_ledger()
    reg = load_registry()
    n_ok = n_skip = 0
    CONF_P.parent.mkdir(parents=True, exist_ok=True)
    with io.open(CONF_P, "a", encoding="utf-8") as logf:
        for row in read_csv(p):
            thr = (row.get("THR") or "").strip()
            key = (row.get("WOP鍵") or row.get("WOP") or "").strip()
            name = (row.get("名稱") or "").strip()
            if not thr or not key:
                n_skip += 1
                continue
            d = sig.get(thr, {"subj": "", "sender": "", "why": {}})
            label = name or wop_label(key, sheet_codes, naming)
            wid, fresh, moved = assign(reg, led, thr, key, label, "confirmed", "人工確認")
            dom = (d["sender"].split("@")[-1] or "").lower() if "@" in (d.get("sender") or "") else ""
            rec = {"ts": now(), "thr": thr, "wop_key": key, "wop_id": wid,
                   "domain": dom, "code": subj_code(d.get("subj", ""))}
            logf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n_ok += 1
    save_ledger(led)
    save_registry(reg)
    print("[確認] 入帳 %d 筆 · 略過 %d · 學習記憶 append → %s" % (n_ok, n_skip, CONF_P))
    if n_ok and p.resolve() == CONFIRM_CSV.resolve():      # v0102:吸收後改名防重複(不刪檔)
        done = CONFIRM_CSV.with_name("wop_confirm.applied.%s.csv" % datetime.now().strftime("%Y%m%d_%H%M%S"))
        p.rename(done)
        print("[歸檔] 確認檔已吸收改名 → %s" % done.name)
    print("[效果] 同網域/同代號下次 propose 直接 AUTO(手動遞減)· wop propose 重跑可見")
    return 0


def cmd_list():
    reg = load_registry()
    if not reg["projects"]:
        print("[空] 尚無 WOP 專案 — 先跑 via-workops wop propose")
        return 0
    for wid in sorted(reg["projects"]):
        pj = reg["projects"][wid]
        mark = "✔" if pj.get("status") == "confirmed" else ("◎" if pj.get("status") == "auto" else "…")
        print("%s %s · %s · THR %d 串 · %s" % (mark, wid, pj.get("label", ""), len(pj.get("thr", [])), pj.get("key", "")))
    return 0


def cmd_domains():
    """v0106:網域收割 — 寄件網域+內文 URL 網域+常見寄件顯示名 → 提議清單(不爬站)。"""
    params = load_params()
    mails = read_csv(MAILS_P)
    if not mails:
        print("[FAIL] out\\mails.csv 不在位 — 先跑 via-workops(板掃描)")
        return 1
    _fm_folder, _fm_att, body_map, from_map = load_folder_map()
    bulk_pats = load_bulk_patterns(BULK_P)
    dom_map = {k.lower() for k in params.get("domain_map", {})}
    agg = {}
    for r in mails:
        sender = (r.get("SenderEmail") or "").strip()
        conv = (r.get("ConversationID") or "").strip()
        subj = (r.get("Subject") or "").strip()
        doms = []
        if "@" in sender and not is_bulk(sender, bulk_pats):
            doms.append(sender.split("@")[-1].lower())
        doms += extract_url_domains(body_map.get(conv, ""))
        disp = from_map.get(conv, "")
        for d in doms:
            if not d or d in dom_map:
                continue
            a = agg.setdefault(d, {"n": 0, "names": Counter(), "subj": subj})
            a["n"] += 1
            if disp:
                a["names"][disp] += 1
    if not agg:
        print("[空] 無新網域候選(全數已在 domain_map 或無語料)")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    outp = OUT / "domain_candidates.csv"
    rows = sorted(agg.items(), key=lambda kv: -kv[1]["n"])
    with io.open(outp, "w", encoding="utf-8-sig", newline="") as f:
        wcsv = csv.writer(f)
        wcsv.writerow(["網域", "件數", "常見寄件名稱(建議單位名)", "例主旨"])
        for d, a in rows:
            top = a["names"].most_common(1)
            wcsv.writerow([d, a["n"], top[0][0] if top else "", a["subj"][:60]])
    print("[收割] 新網域候選 %d 個 → %s" % (len(rows), outp))
    for d, a in rows[:10]:
        top = a["names"].most_common(1)
        print("   %-30s %3d 件  %s" % (d, a["n"], top[0][0] if top else ""))
    print("[下一步] 核對後把「網域: 單位名」貼入 engines\\identifier_params.json 的 domain_map — 即成 L5 白名單直判")
    return 0


def cmd_status():
    reg = load_registry()
    n = len(reg["projects"])
    nc = sum(1 for p in reg["projects"].values() if p.get("status") == "confirmed")
    nt = len(reg["thr2wop"])
    nconf = 0
    if CONF_P.exists():
        nconf = sum(1 for ln in CONF_P.read_text(encoding="utf-8").splitlines() if ln.strip())
    print("[WOP] 專案 %d(人工確認 %d)· THR 歸戶 %d 串 · 學習記憶 %d 筆" % (n, nc, nt, nconf))
    print("[UI ] %s%s" % (QUEUE_P, "(在位)" if QUEUE_P.exists() else "(propose 後生成)"))
    return 0


def main():
    ap = argparse.ArgumentParser(description="WOP 識別歸戶:多訊號融合→AUTO/ASK/QUARANTINE→賦號(編號永不變)")
    ap.add_argument("command", nargs="?", default="propose",
                    choices=["propose", "apply", "list", "status", "domains"])
    ap.add_argument("arg1", nargs="?", default="")
    a = ap.parse_args()
    if a.command == "propose":
        return cmd_propose()
    if a.command == "apply":
        return cmd_apply(a.arg1)
    if a.command == "list":
        return cmd_list()
    if a.command == "domains":
        return cmd_domains()
    return cmd_status()


if __name__ == "__main__":
    sys.exit(main())
