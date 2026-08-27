#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUP_MDL741_NetResilience — 網路韌性與封鎖診斷層(批156;via-resilience)
====================================================================
操作員令:被限流/黑名單時用工具解除限制——但誠實只求「順利通過」。
本層立場(紅線):對象=官方公開資料(TWSE/TPEX openapi、Yahoo、鉅亨等
我方有權取用之公開端點);解法=禮貌化(自適應節流)+韌性(退避重試/
端點鏡像/斷點續跑)+**對症診斷**。不做規避軍備(不繞 IP 封鎖、不解
CAPTCHA、不偽裝指紋以擊破專為擋機器人之偵測);無爬蟲解者(雲端 IP 遭
WAF 永久拒/訂閱付費牆)一律誠實標 NO_WORKAROUND→PENDING,絕不假綠。

核心=「為何失敗」分類器(classify_failure)→每類對應 remedy:
  RATE_LIMIT     429/403-throttle/爆量後空→退避+降速(禮貌,唯一正解)
  TLS_FINGERPRINT 連線重置(requests/urllib 指紋)→curl 子程序車道
  REFERER_GATE   418/需 Referer(CNN F&G 實證)→補標頭
  TRANSIENT      逾時/5xx/瞬斷→退避重試(斷點續跑保重試權)
  WAF_IP_BAN     雲端 IP 遭防火牆拒(NBS 實證)→NO_WORKAROUND
  PAYWALL        訂閱牆(AAII/S&P PMI)→NO_WORKAROUND
  NOT_FOUND      404=端點錯非封鎖→修 URL 非重試
用法:via-resilience --diagnose URL | --policy HOST | --selftest
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

import glob
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 遠端類別→(可否自動解, 對症手法, 是否禮貌節流類)
REMEDY = {
    "RATE_LIMIT": (True, "退避+降速(自適應節流;禮貌正解)", True),
    "TLS_FINGERPRINT": (True, "curl 子程序車道(繞 requests/urllib 指紋重置)", False),
    "REFERER_GATE": (True, "補 Referer/Origin 標頭", False),
    "TRANSIENT": (True, "指數退避重試(斷點續跑保重試權)", False),
    "WAF_IP_BAN": (False, "雲端 IP 遭防火牆拒=無爬蟲解→誠實 PENDING", False),
    "PAYWALL": (False, "訂閱/付費牆=無爬蟲解→誠實 PENDING", False),
    "NOT_FOUND": (False, "404 端點錯(非封鎖)→修 URL 非重試", False),
    "OK": (True, "正常", False),
    "UNKNOWN": (True, "未定=保守退避一次後誠實列", False),
}

# 已實證主機政策(節流下限秒/偏好車道/已知限制)
HOST_POLICY = {
    "www.twse.com.tw": {"floor_s": 1.2, "lane": "curl_json",
                        "note": "rwd 對 requests TLS 重置+rwd 限流;curl+1.2s"},
    "openapi.twse.com.tw": {"floor_s": 0.6, "lane": "http_json", "note": "openapi 較寬鬆"},
    "www.tpex.org.tw": {"floor_s": 1.2, "lane": "curl_json",
                        "note": "www TLS 指紋+瞬斷偶發;curl+1.2s+重試"},
    "query1.finance.yahoo.com": {"floor_s": 0.4, "lane": "raw", "note": "crumb 握手+節流"},
    "ws.api.cnyes.com": {"floor_s": 0.3, "lane": "cnyes_quote", "note": "ws 公開行情"},
    "api.stlouisfed.org": {"floor_s": 0.3, "lane": "http_json", "note": "FRED key 必帶"},
    "www.stats.gov.cn": {"floor_s": 0.0, "lane": None,
                         "note": "NBS WAF 拒雲端 IP=WAF_IP_BAN 無解"},
}


def classify_failure(status: int | None = None, body: str = "",
                     exc: str = "", elapsed_s: float | None = None) -> str:
    """為何失敗→remedy 類別(純函數;零網路;可離線測)"""
    b = (body or "").lower()
    e = (exc or "").lower()
    if status == 200 and body:
        return "OK"
    if status == 429 or "too many requests" in b or "rate limit" in b:
        return "RATE_LIMIT"
    if status == 418 or "referer" in b or "teapot" in b:
        return "REFERER_GATE"
    if status == 404 or "not found" in b:
        return "NOT_FOUND"
    if status in (402,) or "subscription" in b or "paywall" in b or "members only" in b:
        return "PAYWALL"
    # 連線層指紋/瞬斷(exc 字樣)
    if any(k in e for k in ("connection reset", "econnreset", "curl: (35",
                            "sslv3", "wrong version", "tlsv1", "handshake")):
        return "TLS_FINGERPRINT"
    if any(k in e for k in ("timed out", "timeout", "curl: (28", "read timed",
                            "connection aborted", "curl: (52", "curl: (56")):
        return "TRANSIENT"
    if status in (500, 502, 503, 504) or "gateway" in b or "unavailable" in b:
        return "TRANSIENT"
    # WAF 封鎖(常見頁面字樣或 403 含 waf/blocked)
    if status == 403 and any(k in b for k in ("waf", "blocked", "forbidden", "拒絕", "封鎖")):
        return "WAF_IP_BAN"
    if any(k in b for k in ("access denied", "your ip", "已封鎖", "attention required",
                            "cloudflare", "verify you are human", "waf")):
        return "WAF_IP_BAN"
    # JSON 端點卻回 HTML 殼(<!doctype/<html)=多為 WAF 攔截頁/導轉登入=軟封鎖
    if any(k in b for k in ("非 json:<!doctype", "非 json:<html", "<!doctype html",
                            "unusual traffic")):
        return "WAF_IP_BAN"
    if status == 403:
        # 403 未帶 WAF 字樣=多為限流保護,先當 RATE_LIMIT 禮貌退避
        return "RATE_LIMIT"
    return "UNKNOWN"


class AdaptiveThrottle:
    """禮貌化自適應節流:限流訊號→加大延遲(封頂);連續成功→溫和降速。
    這是對付 RATE_LIMIT 的唯一誠實正解(不繞、只放慢到伺服器容忍)。"""

    def __init__(self, floor_s: float = 1.0, cap_s: float = 30.0):
        self.floor = floor_s
        self.cap = cap_s
        self.cur = floor_s
        self._ok_streak = 0

    def wait(self):
        # 抖動 ±15% 避免同步尖峰(禮貌;非規避)
        jitter = self.cur * 0.15 * ((hash(str(time.time())) % 100) / 100 - 0.5) * 2
        time.sleep(max(0.0, self.cur + jitter))

    def on_result(self, category: str):
        if category == "RATE_LIMIT":
            self.cur = min(self.cap, max(self.cur * 2, self.floor * 2))
            self._ok_streak = 0
        elif category == "OK":
            self._ok_streak += 1
            if self._ok_streak >= 5 and self.cur > self.floor:
                self.cur = max(self.floor, self.cur * 0.8)  # 溫和降回下限
                self._ok_streak = 0
        # TLS/REFERER/TRANSIENT 不改節流(改車道/標頭/重試)


def _net():
    hits = sorted(glob.glob(str(HERE / "SUP_MDL740_NetUnified_v*.py")))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("via_net_741", hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules["via_net_741"] = m
    spec.loader.exec_module(m)
    return m


def host_of(url: str) -> str:
    m = re.match(r"https?://([^/]+)", url or "")
    return m.group(1) if m else ""


def policy_for(url: str) -> dict:
    return HOST_POLICY.get(host_of(url), {"floor_s": 1.0, "lane": None, "note": "無政策=保守 1.0s"})


def resilient_fetch(url: str, max_retries: int = 4, throttle: "AdaptiveThrottle | None" = None,
                    referer: str | None = None) -> dict:
    """對症韌性抓取:政策選車道→退避重試→限流自適應→無解誠實 PENDING。
    回傳含 category/remedy_applied/attempts=可審計。凡外呼走 SUP_MDL740 車道。"""
    net = _net()
    if net is None:
        return {"state": "FAIL", "note": "SUP_MDL740 缺席(統包網路工具)"}
    g = net.gate_state()
    if not g["open"]:
        return {"state": "DENY", "note": "fail-closed:同意閘未開(誠實拒絕,零網路)"}
    pol = policy_for(url)
    thr = throttle or AdaptiveThrottle(floor_s=pol.get("floor_s", 1.0))
    lane = pol.get("lane") or "curl_json"
    attempts = []
    for i in range(max_retries):
        thr.wait()
        hdrs = {"Referer": referer} if referer else None
        if lane == "curl_json":
            r = net.curl_json(url, headers=hdrs)
        elif lane == "http_json":
            r = net.http_json(url)
        else:
            r = net.curl_json(url, headers=hdrs)  # 其餘經 curl 收口
        note = r.get("note", "")
        cat = ("OK" if r.get("state") == "OK"
               else classify_failure(body=note, exc=note))
        thr.on_result(cat)
        attempts.append({"try": i + 1, "lane": lane, "category": cat,
                         "note": note[:80], "throttle_s": round(thr.cur, 2)})
        if r.get("state") == "OK":
            return {"state": "OK", "data": r.get("data"), "category": "OK",
                    "attempts": attempts, "remedy_applied": REMEDY["OK"][1]}
        auto, remedy, _ = REMEDY.get(cat, REMEDY["UNKNOWN"])
        if not auto:  # WAF_IP_BAN/PAYWALL/NOT_FOUND=無爬蟲解,立即誠實收
            return {"state": "PENDING" if cat in ("WAF_IP_BAN", "PAYWALL") else "FAIL",
                    "category": cat, "remedy_applied": remedy, "attempts": attempts,
                    "honest": "無爬蟲解=不假綠"}
        if cat == "TLS_FINGERPRINT" and lane != "curl_json":
            lane = "curl_json"  # 對症換車道
        # RATE_LIMIT/TRANSIENT/REFERER/UNKNOWN=退避重試(節流已於 on_result 放大)
    return {"state": "FAIL", "category": attempts[-1]["category"] if attempts else "UNKNOWN",
            "remedy_applied": "重試耗盡(斷點續跑保重試權;下輪再抓)",
            "attempts": attempts, "honest": "誠實計敗,不記 done"}


def diagnose(url: str) -> dict:
    """單點診斷:政策+實抓一次→分類+對症建議(供人審)"""
    net = _net()
    pol = policy_for(url)
    out = {"url": url, "host": host_of(url), "policy": pol}
    if net is None:
        out["state"] = "FAIL"
        out["note"] = "SUP_MDL740 缺席"
        return out
    if not net.gate_state()["open"]:
        out["state"] = "DENY"
        out["note"] = "同意閘未開(誠實;開閘後可診斷)"
        return out
    # 政策冊已標無解主機(lane=None)=尊重已證結論,不重探徒增流量
    if pol.get("lane") is None and "無解" in pol.get("note", ""):
        out.update({"state": "PENDING", "category": "WAF_IP_BAN",
                    "auto_resolvable": False,
                    "remedy": REMEDY["WAF_IP_BAN"][1], "is_politeness_class": False,
                    "raw_note": "政策冊已證無爬蟲解(未重探)"})
        return out
    r = net.curl_json(url)
    note = r.get("note", "")
    cat = "OK" if r.get("state") == "OK" else classify_failure(body=note, exc=note)
    auto, remedy, polite = REMEDY.get(cat, REMEDY["UNKNOWN"])
    out.update({"state": r.get("state"), "category": cat, "auto_resolvable": auto,
                "remedy": remedy, "is_politeness_class": polite, "raw_note": note[:120]})
    return out


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    # 分類器離線真值(純函數;零網路)
    cases = [
        (dict(status=429), "RATE_LIMIT"),
        (dict(status=403, body="Cloudflare attention required"), "WAF_IP_BAN"),
        (dict(status=403, body="rate protection"), "RATE_LIMIT"),
        (dict(status=418), "REFERER_GATE"),
        (dict(status=404), "NOT_FOUND"),
        (dict(body="members only subscription"), "PAYWALL"),
        (dict(exc="curl: (35) connection reset"), "TLS_FINGERPRINT"),
        (dict(exc="curl: (28) timed out"), "TRANSIENT"),
        (dict(status=503, body="gateway unavailable"), "TRANSIENT"),
        (dict(status=200, body="{}"), "OK"),
    ]
    ok = all(classify_failure(**kw) == exp for kw, exp in cases)
    chk("① 失敗分類器十例真值", ok,
        f"({sum(classify_failure(**kw)==exp for kw,exp in cases)}/10)")

    chk("② 無爬蟲解類正確標記(WAF/PAYWALL/NOT_FOUND 不自動)",
        not REMEDY["WAF_IP_BAN"][0] and not REMEDY["PAYWALL"][0]
        and not REMEDY["NOT_FOUND"][0])

    chk("③ 自動解類正確(限流/指紋/瞬斷/Referer 可自動)",
        all(REMEDY[c][0] for c in ("RATE_LIMIT", "TLS_FINGERPRINT",
                                   "TRANSIENT", "REFERER_GATE")))

    # 自適應節流:限流→加大;連五成功→降回
    thr = AdaptiveThrottle(floor_s=1.0, cap_s=30.0)
    thr.on_result("RATE_LIMIT")
    up = thr.cur
    thr.on_result("RATE_LIMIT")
    up2 = thr.cur
    for _ in range(5):
        thr.on_result("OK")
    chk("④ 自適應節流(限流倍增封頂+連五成功降速)",
        up == 2.0 and up2 == 4.0 and thr.cur < up2 and thr.cur >= thr.floor,
        f"(限流後 {up}→{up2}→降 {round(thr.cur,2)})")

    chk("⑤ 主機政策冊(TWSE/TPEX/Yahoo/NBS 在冊+NBS 標無解)",
        "www.twse.com.tw" in HOST_POLICY
        and HOST_POLICY["www.stats.gov.cn"]["lane"] is None)

    chk("⑥ policy_for/host_of 解析",
        host_of("https://www.tpex.org.tw/x?y=1") == "www.tpex.org.tw"
        and policy_for("https://openapi.twse.com.tw/v1/x")["floor_s"] == 0.6)

    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 誠實紅線宣告(不繞封鎖/不解 CAPTCHA/無解不假綠)",
        all(k in src for k in ("不繞 IP 封鎖", "不解 CAPTCHA", "絕不假綠",
                               "NO_WORKAROUND")))
    print(f"  [計] 七檢 OK {7 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 網路韌性與封鎖診斷層(SUP_MDL741)· 七檢自測 ===")
        return selftest()
    if "--policy" in args:
        h = args[args.index("--policy") + 1]
        print(json.dumps(HOST_POLICY.get(h, {"note": "無政策=保守 1.0s"}),
                         ensure_ascii=False, indent=1))
        return 0
    if "--diagnose" in args:
        url = args[args.index("--diagnose") + 1]
        print(json.dumps(diagnose(url), ensure_ascii=False, indent=1))
        return 0
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
