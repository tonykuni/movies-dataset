# ML / DL 2026 本地免費庫十選 ×2 — VIA 適用性裁定 v0100

操作員令(2026-08-11):`apply machine learning / deep learning 2026 top 10 local free libs
for each. implement viable tools.`

裁定原則:**本地執行 · 免費開源 · Windows/CPU 可跑 · 中文文本可用 · 紅線相容**
(絕不代寄/不爬站/AI 只整理不發明 — ML 產出一律「建議」,人工確認才生效)。

## 一、機器學習(傳統 ML)十選

| # | 庫 | 授權 | 強項 | VIA 裁定 |
|---|---|---|---|---|
| 1 | **scikit-learn** | BSD | 分類/聚類/TF-IDF 全家桶,CPU 即跑 | ★ **核心採用**(ENG-055) |
| 2 | XGBoost | Apache-2 | 梯度提升,表格資料王者 | 二線候用(表格任務出現時) |
| 3 | LightGBM | MIT | 快速提升樹,省記憶體 | 二線候用 |
| 4 | CatBoost | Apache-2 | 類別特徵原生處理 | 二線候用 |
| 5 | statsmodels | BSD | 統計推論/時間序列 | 二線候用(FIS 家族相容) |
| 6 | pandas | BSD | 資料整備基座 | ✔ 已在 pm 鏈 venv |
| 7 | NumPy / SciPy | BSD | 數值核心 | ✔ 隨 sklearn 自帶 |
| 8 | imbalanced-learn | MIT | 類別不平衡重採樣 | 二線候用(標註長大後) |
| 9 | river | BSD | 線上/增量學習(逐輪更新) | 三線觀察(閉環成熟後) |
| 10 | mlxtend | BSD | 規則挖掘/集成工具 | 三線觀察 |

## 二、深度學習(DL)十選

| # | 庫 | 授權 | 強項 | VIA 裁定 |
|---|---|---|---|---|
| 1 | PyTorch | BSD | 研究/生產主流框架 | 候令(依賴 GB 級,現階段不裝) |
| 2 | TensorFlow + Keras 3 | Apache-2 | 部署生態完整 | 候令 |
| 3 | JAX / Flax | Apache-2 | 函數式高效能 | 候令 |
| 4 | HF Transformers | Apache-2 | 預訓練模型全庫 | 候令(離線需先下模型) |
| 5 | **sentence-transformers** | Apache-2 | 中文語意嵌入(相似度/聚類) | ★ 二線首選 — ENG-055 已留升級口 |
| 6 | ONNX Runtime | MIT | CPU 推論加速,模型可攜 | 二線候用(部署期) |
| 7 | llama.cpp(GGUF) | MIT | 本地 LLM 推論,零雲端 | 候令(信文助寫線;絕不代寄不變) |
| 8 | Ollama | MIT | 本地 LLM 一鍵執行器 | 候令(同上) |
| 9 | spaCy | MIT | 產業級 NLP 管線 | 二線候用(中文模型另下) |
| 10 | OpenVINO | Apache-2 | Intel CPU 推論加速 | 三線觀察 |

## 三、落地工具(本輪實作 = ENG-055 workops_ml_lab)

以 **scikit-learn 單庫**先落地四項可行工具 — 全部走誠實閘,ML 永不直寫狀態:

1. **probe** — 二十庫在位探測(上兩表逐一 import 驗證,落 `out/ml_probe.json`)
2. **train** — 詞庫泛化模型:以人工核准的詞庫(keywords/weak_signals/ack_terms)
   + 已判讀事實流 + Gold Set(在位時)為標註源,char n-gram TF-IDF + 邏輯迴歸;
   交叉驗證誠實報分;樣本不足=誠實 FAIL 不硬train
3. **suggest** — 對「未解析」回信出 ML 候選狀態(機率 ≥ 門檻才列,落
   `out/ml_suggestions.csv` 人工圈選;**絕不寫 reply_status**)
4. **cluster** — 未解析樣本聚類提詞:每群抽代表片語 → `out/lexicon_review.csv`
   人工填「建議狀態」→ **adopt** 動詞核准寫回 reply_parser_params.json(閉環;
   AI 只整理不發明)

升級口:`sentence-transformers` 在位時 suggest/cluster 自動改用語意嵌入
(config `ml_params.json` 可關);模型檔本地快取,零雲端推論。

## 四、治理

- ML 建議層位於 V/T/K/A/Q/E 六層**之後、之外** — 解析器本體零改動,未解析仍誠實列未解析
- 模型/建議/聚類全落 `out/`(可再生側車,不入 git)
- 行為參數全 `config/ml_params.json`;詞庫寫回僅經 adopt 人工核准路徑
- 依賴缺席=誠實 FAIL + 一行安裝指令,絕不靜默降級
