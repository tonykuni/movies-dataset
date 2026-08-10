# -*- coding: utf-8 -*-
r"""WorkOps 受控正確率驗證 harness v0100(ENG-050)— 操作員「大幅提高正確率各類方法」令

FIS 受控 DGP 精神移植到郵件解析:合成語料自帶真值(ground truth)→ 丟進
「真的」生產解析器(workops_reply_parser.parse_one / detect_flags,吃真的
reply_parser_params.json 合併參數)→ 逐層計分 + 閘門裁定。

與 accuracy_benchmark(ENG-034 Gold Set)的分工:
  benchmark = 真實信件人工核對(需操作員填 gold_set.csv;衡量真實世界正確率)
  harness   = 受控合成語料零人工(真值已知;衡量解析器邏輯本身零迴歸)
  兩者互補,不互相取代。

閘門(不卡斷誠實 OK/FAIL;任一 FAIL 整體 FAIL):
  G1 逐層命中  V/T/K/A/Q/E 六層每層之受控案例 100% 判對(層別+狀態都對)
  G2 誠實閘    噪音案例 + 訊號衝突案例 → 必須回未解析(零亂判;寧漏勿錯)
  G3 旗標偵測  OOO/風險語意案例 flags 全對(含 OOO 代理人 email 擷取)
  G4 總覆蓋    可判案例全數有判讀(=G1 全過的另一面;帳面對齊防漏計)

治理:全唯讀(只寫 out/accuracy_harness_report.json);合成語料在檔內=
版本可控;參數改動(reply_parser_params.json)後重跑本 harness 即知有無迴歸。
動詞:run(預設)
"""
import io
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from workops_reply_parser import parse_one, detect_flags, load_params  # noqa: E402

OUT = HERE.parent / "out"
REPORT_P = OUT / "accuracy_harness_report.json"


def C(cid, desc, layer, status, subject="RE: 請款單進度", body="", voting=""):
    """受控案例:layer=None 代表真值=未解析(誠實閘案例)。"""
    return {"cid": cid, "desc": desc, "layer": layer, "status": status,
            "subject": subject, "body": body, "voting": voting}


CASES = [
    # ---- V 投票層 ----
    C("V01", "投票鈕中文", "V", "已完成", voting="已完成"),
    C("V02", "投票鈕英文(JSON voting_map)", "V", "進行中", voting="In Progress"),
    C("V03", "投票鈕含尾標點", "V", "卡關", voting="卡關!"),
    # ---- T token 層 ----
    C("T01", "VMT-CONFIRM 半形冒號", "T", "進行中", body="==VMT-CONFIRM== Q1:0"),
    C("T02", "VMT-CONFIRM 全形冒號", "T", "已完成", body="回覆如下 ==VMT-CONFIRM== Q1:1 謝謝"),
    C("T03", "VMT-CONFIRM idx=2", "T", "卡關", body="==VMT-CONFIRM== Q1:2"),
    # ---- K 關鍵詞層 ----
    C("K01", "關鍵詞中文完成", "K", "已完成", body="這項工作完成了,附件請參考"),
    C("K02", "關鍵詞英文 blocked", "K", "卡關", body="We are blocked on the vendor side."),
    C("K03", "關鍵詞需要協助", "K", "需要協助", body="這部分需要協助,麻煩安排時間討論"),
    C("K04", "關鍵詞已口頭說明", "K", "已口頭說明", body="已口頭說明,細節如電話中"),
    # ---- A ACK 短覆層(v0103)----
    C("A01", "極短中文收到", "A", "已回覆確認", body="收到"),
    C("A02", "極短中文好的+標點", "A", "已回覆確認", body="好的,謝謝!"),
    C("A03", "極短英文 OK", "A", "已回覆確認", body="OK!"),
    C("A04", "極短英文 Noted", "A", "已回覆確認", body="Noted."),
    C("A05", "主旨短覆(body 空)", "A", "已回覆確認", subject="RE: 請款單 - 收到", body=""),
    # ---- Q 問句層(v0103)----
    C("Q01", "全形問號短問句", "Q", "對方提問", body="想確認一下,這份報表需要包含第三季的數據嗎?"),
    C("Q02", "半形問號短問句", "Q", "對方提問", body="Which version should we use?"),
    # ---- E 弱訊號集成層(v0103)----
    C("E01", "完成弱詞 3 票", "E", "已完成", body="報告已寄出,如附件,請查收"),
    C("E02", "進行弱詞 4 票", "E", "進行中", body="我們正在安排,預計下週提供"),
    C("E03", "卡關弱詞 3 票", "E", "卡關", body="還沒收齊,等待廠商窗口,可能延後"),
    # ---- 誠實閘:噪音必須未解析 ----
    C("N01", "純轉知噪音", None, None, body="FYI"),
    C("N02", "無狀態語意長句", None, None, body="這是一封例行通知信件,內容與專案狀態語意無關"),
    C("N03", "空信體", None, None, body=""),
    C("N04", "單一弱詞低於門檻", None, None, body="明天見"),
    # ---- 誠實閘:訊號衝突必須未解析(FIS 同號過濾精神)----
    C("X01", "完成1票 vs 進行1票(同分未達門檻)", None, None, body="已寄了一部分,其餘正在補"),
    C("X02", "完成2票 vs 進行2票(同分不領先)", None, None, body="已寄出如附件,但正在安排補件"),
]

FLAG_CASES = [
    {"cid": "F01", "desc": "OOO 自動回覆+代理人擷取",
     "subject": "Automatic reply: 請款單進度", "sender": "alice@corp.com",
     "body": "I am out of office until Monday. Please contact agent@corp.com for urgent matters.",
     "ooo": True, "agent": "agent@corp.com", "risk": False},
    {"cid": "F02", "desc": "中文休假自動回覆",
     "subject": "自動回覆: 請款單進度", "sender": "bob@corp.com",
     "body": "本人休假中,緊急事項請洽同仁。", "ooo": True, "agent": "", "risk": False},
    {"cid": "F03", "desc": "風險語意雙詞命中",
     "subject": "RE: 請款單進度", "sender": "carol@corp.com",
     "body": "再無回應我們將採取 legal action 並主張違約。", "ooo": False, "agent": "", "risk": True},
    {"cid": "F04", "desc": "無旗標一般信",
     "subject": "RE: 請款單進度", "sender": "dave@corp.com",
     "body": "收到", "ooo": False, "agent": "", "risk": False},
]


def run():
    params = load_params()
    rows = []
    per_layer = {}
    g1_fail = g2_fail = 0
    for c in CASES:
        row = {"Subject": c["subject"], "VotingResponse": c["voting"], "SenderEmail": "x@corp.com"}
        got = parse_one(row, c["body"], params)
        if c["layer"] is None:
            ok = got is None
            if not ok:
                g2_fail += 1
            key = "誠實閘"
        else:
            ok = got is not None and got[0] == c["layer"] and got[1] == c["status"]
            if not ok:
                g1_fail += 1
            key = c["layer"]
        pl = per_layer.setdefault(key, {"n": 0, "ok": 0})
        pl["n"] += 1
        pl["ok"] += 1 if ok else 0
        rows.append({"cid": c["cid"], "desc": c["desc"],
                     "expect": [c["layer"], c["status"]],
                     "got": list(got) if got else None, "pass": ok})
        mark = "OK " if ok else "FAIL"
        gs = "%s/%s" % (got[0], got[1]) if got else "未解析"
        print(" [%s] %-4s %-28s → %s" % (mark, c["cid"], c["desc"], gs))
    g3_fail = 0
    frows = []
    for c in FLAG_CASES:
        row = {"Subject": c["subject"], "SenderEmail": c["sender"]}
        ooo, risks, agent = detect_flags(row, c["body"], params)
        ok = (ooo == c["ooo"]) and (bool(risks) == c["risk"]) and (agent == c["agent"])
        if not ok:
            g3_fail += 1
        frows.append({"cid": c["cid"], "desc": c["desc"],
                      "expect": {"ooo": c["ooo"], "risk": c["risk"], "agent": c["agent"]},
                      "got": {"ooo": ooo, "risk": bool(risks), "agent": agent}, "pass": ok})
        print(" [%s] %-4s %-28s → ooo=%s risk=%s agent=%s"
              % ("OK " if ok else "FAIL", c["cid"], c["desc"], ooo, bool(risks), agent or "-"))
    n_parseable = sum(1 for c in CASES if c["layer"] is not None)
    n_parsed_ok = sum(1 for r in rows if r["pass"] and r["expect"][0] is not None)
    gates = {
        "G1_逐層命中": g1_fail == 0,
        "G2_誠實閘零亂判": g2_fail == 0,
        "G3_旗標偵測": g3_fail == 0,
        "G4_可判全覆蓋": n_parsed_ok == n_parseable,
    }
    print("---------------------------------------------")
    for k in ("V", "T", "K", "A", "Q", "E", "誠實閘"):
        if k in per_layer:
            p = per_layer[k]
            print(" 層 %-4s %d/%d" % (k, p["ok"], p["n"]))
    all_pass = all(gates.values())
    for g, ok in gates.items():
        print(" [%s] %s" % ("PASS" if ok else "FAIL", g))
    print("========== 受控正確率驗證:%s(%d 案例 + %d 旗標案例)=========="
          % ("ALL PASS" if all_pass else "FAIL", len(CASES), len(FLAG_CASES)))
    OUT.mkdir(parents=True, exist_ok=True)
    rep = {"version": "v0100", "engine": "ENG-050",
           "ts": datetime.now().isoformat(timespec="seconds"),
           "params_version": "merged(reply_parser_params.json+DEFAULT)",
           "gates": {k: ("PASS" if v else "FAIL") for k, v in gates.items()},
           "per_layer": per_layer, "cases": rows, "flag_cases": frows,
           "all_pass": all_pass}
    with io.open(REPORT_P, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    print("[報告] %s" % REPORT_P)
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(run())
