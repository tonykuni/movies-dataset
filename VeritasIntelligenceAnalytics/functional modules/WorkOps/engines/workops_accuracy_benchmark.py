# -*- coding: utf-8 -*-
r"""WorkOps Gold Set 準確度基準 v0100(ENG-030)— v0200 RC 驗收 Gate E 補強落地

操作員令(2026/08/09 整合補強):RC 驗收清單 Gate E —「以真實授權工作郵件建立人工核對
Gold Set,跑 workops_accuracy_benchmark;絕不可只憑信心分數宣稱生產準確度」。
本引擎把該 Gate 落到 run-local 線:量測的是「系統歸戶/判讀 vs 人工標註」的實證準確度。

流程(mouse-light,同命名核對迴圈模式):
  template → out/gold_set_template.csv(現行系統歸戶+狀態判讀快照;
             第三組欄「正確…(空=同意)」由操作員核對修正)
  → 操作員存為 out/gold_set.csv
  → run → 以「當前」系統結果對人工標註計分(不是對快照 — 快照只是標註起點):
     歸戶準確率 · 狀態判讀準確率 · 逐訊號層校準表(哪一層在實戰最準/最弱)
  → out/accuracy_report.json + 誠實列出每筆錯判(編號+期望+實得)

治理:Gold Set=人工最高真相;錯判清單即校正候選(可回饋 wop apply 學習記憶);
標註「空=同意快照」誠實記入樣本;無標註無報告 — 絕不用信心分數冒充準確度。
"""
import argparse, csv, io, json, sys
from collections import Counter
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE   = Path(__file__).resolve().parent
OUT    = HERE.parent / "out"
REG_P  = OUT / "wop_registry.json"
RS_P   = OUT / "reply_status.json"
TPL_P  = OUT / "gold_set_template.csv"
GOLD_P = OUT / "gold_set.csv"
REP_P  = OUT / "accuracy_report.json"


def load_json(p, default):
    if Path(p).exists():
        try:
            return json.loads(Path(p).read_text(encoding="utf-8-sig"))
        except Exception:
            return default
    return default


def current_state():
    reg = load_json(REG_P, {})
    thr2wop = reg.get("thr2wop", {})
    labels = {wid: pj.get("label", "") for wid, pj in reg.get("projects", {}).items()}
    # 逐 THR 證據層(registry history ATTACH 值 = "THR-xxxxx · <證據鏈>")
    layer = {}
    for pj in reg.get("projects", {}).values():
        for h in pj.get("history", []):
            if h.get("action") == "ATTACH":
                v = h.get("value", "")
                thr = v.split(" · ")[0].strip()
                ev = v.split(" · ", 1)[1] if " · " in v else ""
                tok = ev.split(" ")[0] if ev else ""
                if thr and thr not in layer:
                    layer[thr] = tok or "?"
    status = load_json(RS_P, {}).get("status", {})
    return thr2wop, labels, layer, status


def cmd_template():
    thr2wop, labels, layer, status = current_state()
    if not thr2wop:
        print("[FAIL] wop_registry 無歸戶 — 先跑 via-workops all(或 wop propose)")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    with io.open(TPL_P, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["THR", "系統WOP", "系統名稱", "系統狀態判讀",
                    "正確WOP(空=同意)", "正確名稱(空=同意)", "正確狀態(空=同意)"])
        for thr in sorted(thr2wop):
            wid = thr2wop[thr]
            st = (status.get(thr) or {}).get("status", "")
            w.writerow([thr, wid, labels.get(wid, ""), st, "", "", ""])
    print("[樣板] %d 筆現行歸戶 → %s" % (len(thr2wop), TPL_P))
    print("[核對] 錯的填正確值、對的留空(=同意)→ 另存 %s → via-workops accuracy run" % GOLD_P.name)
    return 0


def cmd_run(csvpath):
    p = Path(csvpath) if csvpath else GOLD_P
    if not p.exists():
        print("[FAIL] Gold Set 不在位:%s(先 accuracy template 產樣板核對)" % p)
        return 1
    thr2wop, labels, layer, status = current_state()
    rows = []
    with io.open(p, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("[FAIL] Gold Set 空檔")
        return 1
    n = wop_ok = wop_n = st_ok = st_n = agree = 0
    errors = []
    by_layer = {}
    for r in rows:
        thr = (r.get("THR") or "").strip()
        if not thr:
            continue
        n += 1
        exp_wop = (r.get("正確WOP(空=同意)") or "").strip() or (r.get("系統WOP") or "").strip()
        if not (r.get("正確WOP(空=同意)") or "").strip():
            agree += 1
        cur_wop = thr2wop.get(thr, "")
        wop_n += 1
        lay = layer.get(thr, "?")
        bl = by_layer.setdefault(lay, [0, 0])
        bl[1] += 1
        if cur_wop == exp_wop:
            wop_ok += 1
            bl[0] += 1
        else:
            errors.append({"thr": thr, "kind": "歸戶", "expected": exp_wop,
                           "got": cur_wop or "(未歸戶)", "layer": lay})
        exp_st = (r.get("正確狀態(空=同意)") or "").strip() or (r.get("系統狀態判讀") or "").strip()
        if exp_st:
            cur_st = (status.get(thr) or {}).get("status", "")
            st_n += 1
            if cur_st == exp_st:
                st_ok += 1
            else:
                errors.append({"thr": thr, "kind": "狀態", "expected": exp_st,
                               "got": cur_st or "(無判讀)", "layer": lay})
    rep = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "gold_rows": n, "agree_blank": agree,
        "assignment_accuracy": round(wop_ok / wop_n, 4) if wop_n else None,
        "status_accuracy": round(st_ok / st_n, 4) if st_n else None,
        "per_layer": {k: {"ok": v[0], "n": v[1], "acc": round(v[0] / v[1], 4)}
                      for k, v in sorted(by_layer.items())},
        "errors": errors,
        "honest_note": "準確度=對人工 Gold Set 實測;空=同意快照樣本佔 %d/%d — 絕不以信心分數宣稱生產準確度(Gate E)" % (agree, n),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    REP_P.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[基準] 樣本 %d(空=同意 %d)· 歸戶準確 %s · 狀態準確 %s" % (
        n, agree,
        ("%.1f%%" % (100 * rep["assignment_accuracy"])) if wop_n else "—",
        ("%.1f%%" % (100 * rep["status_accuracy"])) if st_n else "—"))
    for k, v in sorted(by_layer.items(), key=lambda kv: -kv[1][1]):
        print("   層 %-6s %3d/%3d = %.1f%%" % (k, v[0], v[1], 100 * v[0] / v[1]))
    if errors:
        print("[錯判] %d 筆(前 5):" % len(errors))
        for e in errors[:5]:
            print("   %s %s:期望 %s / 實得 %s(%s 層)" % (e["thr"], e["kind"], e["expected"], e["got"], e["layer"]))
        print("[回饋] 錯判即校正候選 — 可入 wop_confirm.csv 走 apply 學習記憶")
    print("[報告] → %s" % REP_P)
    return 0


def main():
    ap = argparse.ArgumentParser(description="Gate E Gold Set 準確度基準(人工標註實測,絕不用信心分數冒充)")
    ap.add_argument("command", nargs="?", default="template", choices=["template", "run"])
    ap.add_argument("arg1", nargs="?", default="")
    a = ap.parse_args()
    return cmd_template() if a.command == "template" else cmd_run(a.arg1)


if __name__ == "__main__":
    sys.exit(main())
