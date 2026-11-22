#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Codex 審查狀態閘 — 在 PR 的最新 commit 上掛一個狀態「Codex 審查」,沒審完就不是綠。

  過去一週 7 次(#702 #703 #705 #712 #714 #715 · #709 連四輪)在 Codex 還沒審完、或審到的是舊 commit 時就合併,
  事後 Codex 找到問題,每次都得再開一支 PR、還原已鎖的檔、出新版號。本閘把「審完沒有」直接掛在 PR 的檢查列上:
    綠 = Codex 程式碼審查審的就是最新 commit、狀態 completed、沒有未解的 Codex 討論串;
    黃(pending)= Codex 還在審,或審的是舊 commit(Codex 只在開 PR 時自動審;推了新 commit 要留言 @codex review);
    紅(failure)= 有未解的 Codex 討論串。
  資料來源:Codex 摘要評論裡的 <!-- codex-review-state:v1 {...} --> 標記 + GraphQL reviewThreads(作者 chatgpt-codex-connector、未 resolve)。
  只讀 PR 與評論、只寫一個 commit status;不 checkout PR 的程式、不執行任何 PR 內容。

環境:GITHUB_TOKEN · GITHUB_REPOSITORY · GITHUB_EVENT_PATH(Actions 自帶)。  自測:--selftest(離線)
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(AGENTS.md:每支新 Python 帶既有加速器橋;graceful 零行為變更) =====
# 只找「本腳本所在倉」的 VIA 樹(往上找到有 .github 的那一層為止),不會載入別的 checkout(例:CI 裡 PR 的程式)。
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve().parent
    while _sa_p.parent != _sa_p and not (_sa_p / ".github").is_dir():
        _sa_p = _sa_p.parent
    _sa_dir = _sa_p / "VeritasIntelligenceAnalytics" / "supportive modules"
    if (_sa_dir / "VIA_SuperAccel_Module.py").exists():
        _sa_sys.path.insert(0, str(_sa_dir))
        import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
    else:
        VIA_ACCEL = None
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響(CI 的 sparse checkout 沒有 VIA 樹)
# ===== [VIA:ACCEL-BRIDGE:END] =====

import html
import json
import os
import re
import sys
import urllib.request

API = os.environ.get("GITHUB_API_URL", "https://api.github.com")
CONTEXT = "Codex 審查"
BOT = "chatgpt-codex-connector"
# 只認這個 App 的確切身分(不是前綴):REST 的 user.login 帶 [bot] 且 type == Bot;GraphQL 的 author.login 不帶 [bot] 且 __typename == Bot。
# (PR 717 Codex P1:前綴比對讓 chatgpt-codex-connector-evil 之類的帳號能偽造「審完」標記)
REST_LOGIN = BOT + "[bot]"


def is_codex_rest(user: dict) -> bool:
    return (user or {}).get("login") == REST_LOGIN and (user or {}).get("type") == "Bot"


def is_codex_gql(author: dict) -> bool:
    return (author or {}).get("login") == BOT and (author or {}).get("__typename") == "Bot"
MARK = re.compile(r"codex-review-state:v1\s*(\{.*?\})\s*-->", re.S)


def parse_state(body: str) -> dict | None:
    m = MARK.search(html.unescape(body or ""))
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except ValueError:
        return None


def decide(state: dict | None, head: str, unresolved: int) -> tuple:
    """(state, description) 給 commit status。description ≤ 140 字元。"""
    if unresolved > 0:
        return "failure", f"Codex 有 {unresolved} 個未解的討論串:修好並回覆、resolve 後再合併"
    cr = (state or {}).get("code_review") or {}
    sha, st = cr.get("commit_sha"), cr.get("status")
    if not state or not sha:
        return "pending", "Codex 還沒開始審這個 PR(開 PR 時會自動審;或留言 @codex review)"
    if sha != head:
        return "pending", f"Codex 審的是舊 commit {sha[:7]},最新是 {head[:7]}:留言 @codex review 再審一次"
    if st != "completed":
        return "pending", f"Codex 正在審 {head[:7]}(狀態 {st}):審完前先不要合併"
    if cr.get("has_unresolved_findings"):
        return "failure", "Codex 摘要說還有未解的發現:修好並回覆、resolve 後再合併"
    return "success", f"Codex 已審完 {head[:7]} · 沒有未解的發現"


def _req(method, url, token, data=None):
    req = urllib.request.Request(url, method=method, data=None if data is None else json.dumps(data).encode("utf-8"),
                                 headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                          "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "codex-gate"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8") or "null")


def unresolved_codex_threads(repo, number, token) -> int:
    owner, name = repo.split("/", 1)
    q = """query($o:String!,$n:String!,$p:Int!,$c:String){repository(owner:$o,name:$n){pullRequest(number:$p){
      reviewThreads(first:100,after:$c){pageInfo{hasNextPage endCursor} nodes{isResolved comments(first:1){nodes{author{login __typename}}}}}}}}"""
    cnt, cur = 0, None
    while True:
        d = _req("POST", f"{API}/graphql", token, {"query": q, "variables": {"o": owner, "n": name, "p": number, "c": cur}})
        rt = d["data"]["repository"]["pullRequest"]["reviewThreads"]
        for t in rt["nodes"]:
            who = (t["comments"]["nodes"] or [{}])[0].get("author") or {}
            if not t["isResolved"] and is_codex_gql(who):
                cnt += 1
        if not rt["pageInfo"]["hasNextPage"]:
            return cnt
        cur = rt["pageInfo"]["endCursor"]


def summary_state(repo, number, token) -> dict | None:
    page, last = 1, None
    while True:
        cs = _req("GET", f"{API}/repos/{repo}/issues/{number}/comments?per_page=100&page={page}", token)
        for c in cs:
            if is_codex_rest(c.get("user")):
                s = parse_state(c.get("body"))
                if s:
                    last = s
        if len(cs) < 100:
            return last
        page += 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    token, repo = os.environ["GITHUB_TOKEN"], os.environ["GITHUB_REPOSITORY"]
    ev = json.load(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8"))
    number = ((ev.get("pull_request") or {}).get("number") or ((ev.get("issue") or {}).get("pull_request") and ev["issue"]["number"])
              or int((ev.get("inputs") or {}).get("pr") or 0))
    if not number:
        print("不是 PR 事件,略過")
        return 0
    pr = _req("GET", f"{API}/repos/{repo}/pulls/{number}", token)
    if pr.get("state") != "open":
        print(f"PR #{number} 不是 open,略過")
        return 0
    head = pr["head"]["sha"]
    state, desc = decide(summary_state(repo, number, token), head, unresolved_codex_threads(repo, number, token))
    _req("POST", f"{API}/repos/{repo}/statuses/{head}", token, {"state": state, "context": CONTEXT, "description": desc[:140]})
    print(f"PR #{number} · {head[:7]} · {state} · {desc}")
    return 0


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    h = "093e95c8959c6b6fb4cb04dc823d8a7cd328baaa"
    body = ('<!-- codex-pull-request-review-summary -->\n<!-- codex-review-state:v1 &#123;"code_review":&#123;"commit_sha":"%s",'
            '"has_any_findings":false,"has_unresolved_findings":false,"status":"completed"&#125;,"security_review":&#123;"status":"running"&#125;&#125; -->' % h)
    s = parse_state(body)
    chk("① 讀得懂摘要標記(含 HTML 實體 &#123;)", s and s["code_review"]["commit_sha"] == h, s)
    chk("② 審的就是最新 commit · completed · 沒有未解 → 綠", decide(s, h, 0)[0] == "success")
    chk("③ #715 情境:推了新 commit、Codex 審的是舊的 → 黃(提示 @codex review)", decide(s, "40dabb6f9" + "0" * 31, 0)[0] == "pending"
        and "@codex review" in decide(s, "40dabb6f9" + "0" * 31, 0)[1])
    run = json.loads(json.dumps(s))
    run["code_review"]["status"] = "running"
    chk("④ #712 / #714 情境:Codex 還在跑 → 黃", decide(run, h, 0)[0] == "pending")
    chk("⑤ 有未解的 Codex 討論串 → 紅(即使摘要說審完)", decide(s, h, 2)[0] == "failure")
    unr = json.loads(json.dumps(s))
    unr["code_review"]["has_unresolved_findings"] = True
    chk("⑥ 摘要自己說有未解 → 紅", decide(unr, h, 0)[0] == "failure")
    chk("⑦ 還沒有摘要評論 → 黃", decide(None, h, 0)[0] == "pending" and decide(parse_state("沒標記"), h, 0)[0] == "pending")
    chk("⑨ PR 717 Codex P1:只認確切的 Codex App 身分(前綴相同的帳號 · 不是 Bot 型別 → 不認)",
        is_codex_rest({"login": "chatgpt-codex-connector[bot]", "type": "Bot"})
        and not is_codex_rest({"login": "chatgpt-codex-connector-evil", "type": "User"})
        and not is_codex_rest({"login": "chatgpt-codex-connector[bot]", "type": "User"})
        and not is_codex_rest({"login": "chatgpt-codex-connector-evil[bot]", "type": "Bot"})
        and is_codex_gql({"login": "chatgpt-codex-connector", "__typename": "Bot"})
        and not is_codex_gql({"login": "chatgpt-codex-connector-evil", "__typename": "User"})
        and not is_codex_gql({"login": "chatgpt-codex-connector", "__typename": "User"}))
    _src = open(__file__, encoding="utf-8").read().split("def selftest", 1)[0]
    chk("⑩ 沒有前綴比對 · 加速器橋在", ".startswith(BOT)" not in _src and "[VIA:ACCEL-BRIDGE:v0100]" in _src)
    chk("⑧ 說明都 ≤ 140 字元", all(len(decide(x, y, z)[1]) <= 140 for x, y, z in ((s, h, 0), (s, "f" * 40, 0), (run, h, 0), (s, h, 9), (None, h, 0))))
    print(f"  [計] codex_gate 自測 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
