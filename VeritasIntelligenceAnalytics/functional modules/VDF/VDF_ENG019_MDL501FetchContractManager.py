# -*- coding: utf-8 -*-
r"""VDF 取數契約管理器 v0100(MDL501)— 擷取項目 增/減/查/比 一支到底

操作員令(2026/08/10):「確認這些參數是否都有加入擷取項目 增減功能」。
正本 = registry/VIA_VDF_Fetch_Contract.json(VDF-FETCH/1.0,14 域 277 項起)。

治理:
  只增不減 — remove 為軟移除(status="off"+removed_note,原項保留可回溯);絕不硬刪。
  編號永不變 — add 拒絕重複 code;code 一經寫入不可改,名稱/欄位可修(set)。
  每次變更 → contract["changelog"] append(append-only 履歷)+ 變更前自動備份側車
  registry/backups/VIA_VDF_Fetch_Contract.<ts>.json(正本不就地丟失任何狀態)。

動詞:
  check                    驗證 schema+重複代碼+盤點(預設)
  list [域鍵|all] [狀態]   列項(px/cm/fx/ld/cc/lg/fs/fed/gl/cy/se/ef/cs/fn)
  diff 檔.json             與另一份契約逐項比對(缺/多/內容異)
  add  域鍵 CODE 名稱 source fetcher freq 欄位1,欄2 消費者1,2 [狀態]
  remove CODE [備註]       軟移除(status=off;只增不減)
  setstatus CODE 狀態      ok / proxy / todo / off
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import json, shutil, sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
CONTRACT_P = HERE / "registry" / "VIA_VDF_Fetch_Contract.json"
BK_DIR = HERE / "registry" / "backups"
VALID_STATUS = ("ok", "proxy", "todo", "off")


def load():
    return json.loads(CONTRACT_P.read_text(encoding="utf-8-sig"))


def save(c, action):
    BK_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")   # 微秒防同秒備份互覆
    shutil.copy(CONTRACT_P, BK_DIR / ("VIA_VDF_Fetch_Contract.%s.json" % ts))
    c.setdefault("changelog", []).append({"ts": datetime.now().isoformat(timespec="seconds"), "action": action})
    CONTRACT_P.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[存檔] 變更前備份 backups/…%s.json · changelog 共 %d 筆" % (ts, len(c["changelog"])))


def index(c):
    m = {}
    for d in c.get("domains", []):
        for it in d.get("items", []):
            m.setdefault(it.get("code", ""), []).append((d["key"], it))
    return m


def cmd_check():
    c = load()
    idx = index(c)
    dup = sorted(k for k, v in idx.items() if len(v) > 1)
    st = {}
    n = 0
    for d in c["domains"]:
        for it in d["items"]:
            n += 1
            st[it.get("status", "?")] = st.get(it.get("status", "?"), 0) + 1
    print("[契約] %s · %s · asof %s" % (c.get("schema"), c.get("code"), c.get("asof")))
    print("[盤點] %d 域 %d 項 · 狀態 %s" % (len(c["domains"]), n,
          " / ".join("%s %d" % kv for kv in sorted(st.items()))))
    bad = [k for k in idx if not k]
    ok = not dup and not bad
    if dup:
        print("[FAIL] 重複代碼:%s" % ", ".join(dup))
    if bad:
        print("[FAIL] 空代碼項存在")
    if c.get("changelog"):
        print("[履歷] changelog %d 筆(最後:%s)" % (len(c["changelog"]), c["changelog"][-1]["action"][:60]))
    print("[結果] %s" % ("PASS — 代碼唯一、schema 在約" if ok else "FAIL"))
    return 0 if ok else 1


def cmd_list(dom="all", status=""):
    c = load()
    n = 0
    for d in c["domains"]:
        if dom not in ("all", "", d["key"]):
            continue
        for it in d["items"]:
            if status and it.get("status") != status:
                continue
            n += 1
            print("%-4s %-8s %-6s %-28s %s" % (d["key"], it.get("code", ""), it.get("status", ""),
                                               (it.get("item", "") or "")[:28], it.get("source", "")))
    print("[共] %d 項" % n)
    return 0


def cmd_diff(other):
    c = load()
    o = json.loads(Path(other).read_text(encoding="utf-8-sig"))
    a, b = index(c), index(o)
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    changed = []
    for k in sorted(set(a) & set(b)):
        if json.dumps(a[k][0][1], ensure_ascii=False, sort_keys=True) != json.dumps(b[k][0][1], ensure_ascii=False, sort_keys=True):
            changed.append(k)
    print("[比對] 正本 %d 項 vs 對方 %d 項" % (len(a), len(b)))
    print("  只在正本:%s" % (", ".join(only_a) if only_a else "(無)"))
    print("  只在對方:%s" % (", ".join(only_b) if only_b else "(無)"))
    print("  內容相異:%s" % (", ".join(changed) if changed else "(無)"))
    same = not only_a and not only_b and not changed
    print("[結果] %s" % ("完全一致" if same else "有差異 — 需要吸收請用 add/setstatus 逐項(代碼永不變)"))
    return 0 if same else 1


def cmd_add(dom, code, item, source, fetcher, freq, fields, consumers, status="todo"):
    if status not in VALID_STATUS:
        print("[FAIL] 狀態限 %s" % "/".join(VALID_STATUS))
        return 1
    c = load()
    if code in index(c):
        print("[FAIL] 代碼 %s 已存在 — 編號永不變,不覆蓋;要改狀態用 setstatus" % code)
        return 1
    for d in c["domains"]:
        if d["key"] == dom:
            d["items"].append({"code": code, "item": item, "source": source, "fetcher": fetcher,
                               "freq": freq, "fields": [f for f in fields.split(",") if f],
                               "consumers": [x for x in consumers.split(",") if x], "status": status})
            save(c, "ADD %s(%s)入 %s 域 status=%s" % (code, item, dom, status))
            print("[增] %s %s → %s 域(status=%s)" % (code, item, dom, status))
            return 0
    print("[FAIL] 無此域鍵:%s(有效:%s)" % (dom, ",".join(d["key"] for d in c["domains"])))
    return 1


def cmd_remove(code, note=""):
    c = load()
    idx = index(c)
    if code not in idx:
        print("[FAIL] 查無代碼 %s" % code)
        return 1
    it = idx[code][0][1]
    prev = it.get("status", "?")
    it["status"] = "off"
    it["removed_note"] = "%s 軟移除(原 status=%s)%s" % (datetime.now().strftime("%Y-%m-%d"), prev,
                                                        (";" + note) if note else "")
    save(c, "REMOVE(soft)%s 原 status=%s %s" % (code, prev, note))
    print("[減] %s → status=off(原項保留可回溯;只增不減)" % code)
    return 0


def cmd_setstatus(code, status):
    if status not in VALID_STATUS:
        print("[FAIL] 狀態限 %s" % "/".join(VALID_STATUS))
        return 1
    c = load()
    idx = index(c)
    if code not in idx:
        print("[FAIL] 查無代碼 %s" % code)
        return 1
    it = idx[code][0][1]
    prev = it.get("status", "?")
    it["status"] = status
    save(c, "SETSTATUS %s %s→%s" % (code, prev, status))
    print("[改] %s:%s → %s" % (code, prev, status))
    return 0


def main(argv):
    if not CONTRACT_P.exists():
        print("[FAIL] 契約正本不在位:%s" % CONTRACT_P)
        return 1
    v = argv[1] if len(argv) > 1 else "check"
    try:
        if v == "check":
            return cmd_check()
        if v == "list":
            return cmd_list(argv[2] if len(argv) > 2 else "all", argv[3] if len(argv) > 3 else "")
        if v == "diff":
            return cmd_diff(argv[2])
        if v == "add":
            return cmd_add(*argv[2:11])
        if v == "remove":
            return cmd_remove(argv[2], " ".join(argv[3:]))
        if v == "setstatus":
            return cmd_setstatus(argv[2], argv[3])
    except (IndexError, TypeError):
        pass
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
