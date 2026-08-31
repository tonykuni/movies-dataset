# 第三方免費工具清單

本專案不複製或重新授權下列工具；安裝器只從官方套件通路安裝。各工具仍受自己的授權條款約束。

|   # | 工具                                      | 執行環境     | 引擎角色                        |    預設改檔 | 授權             |
| --: | ----------------------------------------- | ------------ | ------------------------------- | ----------: | ---------------- |
|   1 | Prettier                                  | Node.js      | 預設主格式化器                  |          是 | MIT              |
|   2 | markdownlint-cli2                         | Node.js      | 規則修復與驗證                  |          是 | MIT              |
|   3 | remark／remark-cli                        | Node.js      | GFM AST 解析驗證                |          否 | MIT              |
|   4 | prettier-plugin-lint-md                   | Node.js      | 中文排版插件                    |  是，可停用 | MIT              |
|   5 | mdast-util-from-markdown                  | Node.js      | 第二 AST 解析層                 |          否 | MIT              |
|   6 | rumdl                                     | Rust／Python | 高速檢查；可選主格式化器        |          否 | MIT              |
|   7 | PyMarkdownLnt                             | Python       | 嚴格規格檢查                    |          否 | MIT              |
|   8 | mdformat                                  | Python       | CommonMark 檢查；可選主格式化器 |          否 | MIT              |
|   9 | markdown-table-fixer                      | Python       | MD060 表格驗證；可選修復        |  否，可啟用 | Apache-2.0       |
|  10 | Prettydiff                                | JavaScript   | 隔離的舊版可選轉接器            |          否 | 依實際版本       |
|  11 | Pandoc                                    | Haskell／Lua | AST 驗證；可選轉換器            |          否 | GPL-2.0-or-later |
|  12 | mdBook                                    | Rust         | 文件網站建置器                  |  僅輸出目錄 | MPL-2.0          |
|  13 | CSpell 9.8.0                              | Node.js      | 離線拼字與自訂字典              |          否 | MIT              |
|  14 | remark-preset-lint-recommended 7.0.1      | Node.js      | AST 推薦規則集                  |          否 | MIT              |
|  15 | remark-lint-no-undefined-references 5.0.2 | Node.js      | 連結定義與 callout 相容驗證     |          否 | MIT              |
|  16 | mdformat-gfm 1.0.0                        | Python       | GFM 格式擴充                    | 隨 mdformat | MIT              |
|  17 | mdformat-frontmatter 2.1.2                | Python       | YAML front matter 擴充          | 隨 mdformat | MIT              |
|  18 | mdit-py-plugins 0.6.1                     | Python       | 獨立擴充解析驗證                |          否 | MIT              |

另附本專案自己的 Node AST worker、Rust `mdscan`、Go `mdlinkcheck`、Lua filter 與 PowerShell 入口；它們不是額外第三方套件。

## 編排原則

Prettier、rumdl、mdformat、Pandoc 使用不同 Markdown 方言與序列化策略，因此引擎一次只允許一個主格式化器，其餘轉為唯讀驗證，避免表格、引用連結、HTML、MyST、數學式或微軟 callout 被連續改寫。

Prettydiff 缺少可穩定核對的現行 Markdown CLI 套件，因此只保留明確隔離的 legacy adapter，不列入安裝或自動流程。DavidAnson 的有效工具則透過 `markdownlint-cli2` 與底層 `markdownlint` 規則納入。
