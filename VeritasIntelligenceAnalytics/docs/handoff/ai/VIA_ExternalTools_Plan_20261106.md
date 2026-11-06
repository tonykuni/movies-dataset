# 操作員 2026-11-06「規劃 VIA 整合 agentmemory、Ponytail、OmniRoute 等工具」· 規劃(只規劃 · 收尾期不裝 · 不新增模組)

| 工具 | 是什麼(查證)| 對 VIA 的位置 | 建議 | 風險 / 條件 |
|---|---|---|---|---|
| **Ponytail**(DietrichGebert/ponytail · MIT)| Claude Code 的 agent skill / plugin:寫碼前先走一串「要不要做」的問題梯,逼 AI 當「最省的資深工程師」,自述少寫 54–94% 程式碼。 | **不是 VIA 模組**,是操作員 Claude Code 環境的 skill。與本倉 Release Closure 規範(九頭龍禁止 · 最少輸入 · 額外複雜度 > 價值直接拒絕)完全同向。 | **可直接在操作員的 Claude Code 裝**(`/plugin marketplace add` + install,照它 README);倉裡零改動。 | 只影響 AI 行為,不碰 VIA 程式;數字是它自報。 |
| **OmniRoute**(diegosouzapw/OmniRoute · MIT · TypeScript / Next.js)| 自架 AI 閘道:一個 OpenAI 相容端點 → 160+ 供應商、多層 fallback(訂閱 → API key → 便宜 → 免費)、token 壓縮。`npm i -g omniroute` 或 docker。 | 會坐在 **VIA_MCP_Engine v0102** 管的那些 AI 平台前面(路由層),不是 VIA 子系統。 | **收尾期不接**。要接的話:獨立 Node 環境 · 只 loopback · VIA 網路政策(DENY 名單 / 同意閘)照走 · 由 MCP Engine 多一個「平台 = omniroute」設定,不改 VCGC 主控台。 | 需 Node(README 說不相容 Node 24+)· 出網 · 多一層操作與安全面;VIA 現在沒有任何模組需要「多供應商路由」。 |
| **agentmemory**(bdeva1975/agentmemory 等 · 小型個人專案)| 給 OpenAI agents 的 JSON 檔持久記憶(recall);向量搜尋 / TTL / 多 agent 是「計畫中」。PyPI 上沒有同名正式套件,只有 memory-agent(Redis / LangGraph)、agentmem、humem 等近似品。 | VIA Agent OS v0102 已有 `via-memory-manager` skill(本機 · fail-closed)。 | **不引入**:功能重疊、成熟度低、要 pip。若要「記憶」,用 Agent OS 自己的 skill。 | 第三方小專案 · 無鎖版 · 不在 VIA 工具席位。 |

## 登錄與下一步

- 本規劃登 VCGC 需求冊為 **VCGC-REQ185(RECORDED)**(本輪提交的需求冊尾版);狀態「規劃」,沒有程式變更。
- 「SYNC HERE」給的 claude.ai/code 工作階段連結本容器打不開(不是 artifact · 不是倉);請把那個階段的結論貼成文字或上傳。
- 另一單位(VRN-1 團隊倉 tonykuni/VIA-VDF-VRN · 只讀)2026-11-05 PR #82 `codex-env-vap-ssot-20261105`:把**環境隔離分類與 VAP 圖表規格納入中央治理**(`config/ssot/VIA_VAP_Chart_SSOT.via` + schema · `public/via/VIA_VAP_Chart_SSOT.py` 288 行 · `VIA_EnvManager.py` +173 · tests)。
  與本倉 VAP v0300 的 40 Canonical + 5 Composite 圖碼是同一題;**只讀參考、不抓進來**(收尾期不新增模組);要對齊時由 VAP 的 owner 決定以哪邊的 SSOT 為正本。

來源:[ponytail](https://github.com/dietrichgebert/ponytail) · [OmniRoute](https://github.com/diegosouzapw/OmniRoute) · [OmniRoute 安全評估](https://pinggy.io/blog/omniroute_ai_gateway_security/) · [agentmemory](https://github.com/bdeva1975/agentmemory)
