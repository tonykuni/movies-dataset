# VIA Streamlit Companion

這是 VIA 標準化模板的**可選本機 Python companion**。它將使用者附件中的 Streamlit、CSV 分析、Mermaid、Graphviz 與 Agraph 工作流方案整理成一個可直接啟動的資料應用程式。

## 邊界

`ui/VIA-UI-Standalone-NoServer.html` 與 `ui/VIA-SYNCHRONIZER-Standalone.html` 仍是 canonical runtime。Streamlit companion 不會被嵌入 HTML，也不會改變 `file://`、`localStorage`、`BroadcastChannel`、CSV、JSON 或 SpreadsheetML 的正式契約。只有在需要 Python 資料分析、工作流探索或後續 AI／模型 integration 時，才啟動這個 optional-local 模組。

## 安裝

在可連網的 build host 準備依賴：

```bash
python3 -m pip install -r requirements-optional.txt
```

離線主機不要重新下載套件；請把已準備好的 Python environment 或 wheel media 一併帶入。這個 companion 不會在啟動時自動 pip install。

## 啟動

```bash
bash run_companion.sh
```

預設只綁定 `127.0.0.1:8501`。可用環境變數調整：

```bash
STREAMLIT_PORT=8502 STREAMLIT_ADDRESS=127.0.0.1 bash run_companion.sh
```

## 功能

左側控制面板可選擇三種工作流後端：

| 後端 | 技術 | 互動方式 | 備註 |
|---|---|---|---|
| Mermaid | Mermaid text | 靜態流程圖 | 預設 safe text mode；可在控制面板手動啟用實驗性 component |
| Graphviz | DOT | 靜態佈局 | 使用本機 Graphviz runtime；失敗時顯示 DOT |
| Agraph | Vis.js network | 拖曳、縮放 | 未安裝套件時顯示 nodes／edges 表格 |

CSV 分析只使用使用者匯入的真實 CSV，不產生隨機或虛構資料。若存在數值欄位，會以 Streamlit 原生 line chart 顯示趨勢，並提供 UTF-8-SIG CSV 下載。

Mermaid 預設只顯示可攜式語法，避免 optional third-party iframe 在不同 Streamlit／瀏覽器版本出現 SVG console warning。若已確認本機環境相容，可在控制面板勾選「啟用 Mermaid component（實驗性）」來使用 `streamlit-mermaid`。

## 與 VIA state 的後續接點

這個 companion 目前採獨立資料輸入，避免 Python server 改變 canonical local-only runtime。未來若要與 VIA state 整合，建議使用明確的 JSON export/import 或檔案交換，不要讓 Streamlit 直接寫入另一個瀏覽器 page 的 localStorage。任何新增 bridge 都必須保持 version 2 state schema、未知欄位保留與 deterministic validator。
