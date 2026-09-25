# 2026-09-25 · 接手修復

- 中央 UI 明確共享通知函式，修復跨頁同步與自訂模組點擊的 toast 作用域錯誤。
- 沿用原三入口、版面及同步契約；本次為操作員授權的模板修正版。

# Changelog

## 2026-09-20

- Consolidated the standalone UI, SYNCHRONIZER, Engine Hub, industry registry, CI/CD, E2E, QA artifacts, assets, and reusable skills into one canonical VIA template.
- Added a single `VIA-Complete-System.html` launcher and a one-command complete-system quality gate.
- Added explicit canonical paths, standardization contract, manifest, and legacy reference boundary.
- Added offline deployment, file-origin testing, checksum, loopback fallback, cross-page sync, and offline E2E instructions.
- Added an optional local Streamlit companion with CSV analysis and Mermaid/Graphviz/Agraph workflow fallbacks without changing the standalone HTML runtime.
