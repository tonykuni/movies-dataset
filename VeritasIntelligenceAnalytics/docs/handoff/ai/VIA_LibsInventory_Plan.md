# VIA libs/環境 布建計畫(由 VIA_LibsInventory_v0100.py 生成)

正本冊:`VIA_EnvGovernance_Baseline_v0104.json`(一個字沒改)· 盤冊指紋 `07671e43bd122cc3` · 2026-11-08T11:42:17Z

## 鏡像:三個一起,不是三選一

倉根 `uv.toml` 已把三個索引一起登好,uv 走 first-index:前面查無才往下走,官方 `default=true` 永遠兜底。
1. `https://pypi.tuna.tsinghua.edu.cn/simple`  (tsinghua)
2. `https://mirrors.aliyun.com/pypi/simple/`  (aliyun)
3. `https://pypi.org/simple`  (pypi-official)

所以 R2 的指令**不要**加 `UV_NO_CONFIG=1`(那會只用一個索引),讓 uv.toml 的三索引一起生效。

## R0 同意閘(只有操作員能開,這支引擎不代設)

```powershell
$env:VIA_NET_CONSENT = "YES"   # 鏡像探測 / 解析 / 安裝都在這道閘後面
```

## R1 冊修(不碰網路、不碰境、彼此不相依 —— 已在雲端這輪做掉)

**已清空** —— 冊修全部完成,衝突偵測在 R1 這一類已歸零。做了什麼看正本冊自己的紀錄:

- `change_v0103`:三件被兩個家族同時認領(目標境歧義)→ 依冊自己的 `moved_out` /
  `functional_moved_to_via` 裁決歸屬,各留一個正主
- `change_v0104`:65 件樹內真的 import、冊上卻查無的件全部落冊 ——
  58 件歸既有家族(每家族一條理由)· 5 件推不出歸屬 → `unclassified` → 黑環境待裁 ·
  2 件其實早在冊上只是 import 名 ≠ pip 名 → 新增 `import_name_map` 正本鍵
- 驗帳:冊上覆蓋率 57.2% → 100.0%;`CGC_MDL135_EnvGovernance` 尾版自測 52/52 + 5/5 沒退步

## R2 境修(要鏡像 + 同意閘 + 拓撲序 —— 桌機照下面貼上跑,不用再測)

```bash
scripts/envcheck.sh doctor                      # ① 三鏡像連通 + uv cache 體檢

# via_camelot_311（1 件）
uv venv via_camelot_311 --python 3.13
scripts/envcheck.sh resolve camelot-py   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_camelot_311 camelot-py
uv pip check --python via_camelot_311                     # ③ 裝後相容性;非 0 就停在這一境

# via_html_312（5 件）
uv venv via_html_312 --python 3.12
scripts/envcheck.sh resolve beautifulsoup4 html2text lxml readability-lxml trafilatura   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_html_312 beautifulsoup4 html2text lxml readability-lxml trafilatura
uv pip check --python via_html_312                     # ③ 裝後相容性;非 0 就停在這一境

# via_iso_ml_cuda_H（5 件）
uv venv via_iso_ml_cuda_H --python 3.11
scripts/envcheck.sh resolve funasr llama-cpp-python marker-pdf sentence-transformers transformers   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_iso_ml_cuda_H funasr llama-cpp-python marker-pdf sentence-transformers transformers
uv pip check --python via_iso_ml_cuda_H                     # ③ 裝後相容性;非 0 就停在這一境

# via_iso_quarantine（5 件）
uv venv via_iso_quarantine --python 3.12
scripts/envcheck.sh resolve crewai email-case-tracker google langgraph pdf-table-validator   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_iso_quarantine crewai email-case-tracker google langgraph pdf-table-validator
uv pip check --python via_iso_quarantine                     # ③ 裝後相容性;非 0 就停在這一境

# via_iso_scrape_H（3 件）
uv venv via_iso_scrape_H --python 3.11
scripts/envcheck.sh resolve js2py playwright selenium   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_iso_scrape_H js2py playwright selenium
uv pip check --python via_iso_scrape_H                     # ③ 裝後相容性;非 0 就停在這一境

# via_iso_webui_M（4 件）
uv venv via_iso_webui_M --python 3.12
scripts/envcheck.sh resolve pywebview streamlit streamlit-agraph streamlit-mermaid   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_iso_webui_M pywebview streamlit streamlit-agraph streamlit-mermaid
uv pip check --python via_iso_webui_M                     # ③ 裝後相容性;非 0 就停在這一境

# via_mix_api_v2_M（3 件）
uv venv via_mix_api_v2_M --python 3.12
scripts/envcheck.sh resolve fastapi redis uvicorn   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_mix_api_v2_M fastapi redis uvicorn
uv pip check --python via_mix_api_v2_M                     # ③ 裝後相容性;非 0 就停在這一境

# via_mix_ds_np2_M（10 件）
uv venv via_mix_ds_np2_M --python 3.12
scripts/envcheck.sh resolve dask datacompy joblib numba numexpr pandera ray recordlinkage scikit-learn statsmodels   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_mix_ds_np2_M dask datacompy joblib numba numexpr pandera ray recordlinkage scikit-learn statsmodels
uv pip check --python via_mix_ds_np2_M                     # ③ 裝後相容性;非 0 就停在這一境

# via_mix_http_M（1 件）
uv venv via_mix_http_M --python 3.12
scripts/envcheck.sh resolve httpx   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_mix_http_M httpx
uv pip check --python via_mix_http_M                     # ③ 裝後相容性;非 0 就停在這一境

# via_nlp（24 件）
uv venv via_nlp --python 3.12
scripts/envcheck.sh resolve ckip-transformers dateparser fasttext flashtext ftfy gensim google-re2 jellyfish jieba keybert nltk opencc pinyin pkuseg polyfuzz pyahocorasick pycorrector pypinyin quantulum3 rapidfuzz spacy sumy wtpsplit-lite yake   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_nlp ckip-transformers dateparser fasttext flashtext ftfy gensim google-re2 jellyfish jieba keybert nltk opencc pinyin pkuseg polyfuzz pyahocorasick pycorrector pypinyin quantulum3 rapidfuzz spacy sumy wtpsplit-lite yake
uv pip check --python via_nlp                     # ③ 裝後相容性;非 0 就停在這一境

# via_onnxruntime（1 件）
uv venv via_onnxruntime --python 3.12
scripts/envcheck.sh resolve onnxruntime   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_onnxruntime onnxruntime
uv pip check --python via_onnxruntime                     # ③ 裝後相容性;非 0 就停在這一境

# via_paddle_311（9 件）
uv venv via_paddle_311 --python 3.13
scripts/envcheck.sh resolve easyocr img2table onnxruntime opencv-contrib-python paddleocr pytesseract pyvips rapidocr-onnxruntime surya-ocr   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_paddle_311 easyocr img2table onnxruntime opencv-contrib-python paddleocr pytesseract pyvips rapidocr-onnxruntime surya-ocr
uv pip check --python via_paddle_311                     # ③ 裝後相容性;非 0 就停在這一境

# via_tabula_311（1 件）
uv venv via_tabula_311 --python 3.11
scripts/envcheck.sh resolve tabula-py   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_tabula_311 tabula-py
uv pip check --python via_tabula_311                     # ③ 裝後相容性;非 0 就停在這一境

# via_tools_312（9 件）
uv venv via_tools_312 --python 3.12
scripts/envcheck.sh resolve chardet keyring lz4 prefect pytest structlog transitions watchdog xxhash   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_tools_312 chardet keyring lz4 prefect pytest structlog transitions watchdog xxhash
uv pip check --python via_tools_312                     # ③ 裝後相容性;非 0 就停在這一境

# via_vap_312（8 件）
uv venv via_vap_312 --python 3.12
scripts/envcheck.sh resolve dash dash-bootstrap-components duckdb matplotlib numpy pandas plotly seaborn   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_vap_312 dash dash-bootstrap-components duckdb matplotlib numpy pandas plotly seaborn
uv pip check --python via_vap_312                     # ③ 裝後相容性;非 0 就停在這一境

# via_vdf_312（18 件）
uv venv via_vdf_312 --python 3.12
scripts/envcheck.sh resolve akshare curl-cffi duckdb fredapi google-api-python-client google-auth-oauthlib gspread gspread-dataframe imap-tools msal numpy pandas pandas-datareader plotly polars pyarrow python-calamine yfinance   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_vdf_312 akshare curl-cffi duckdb fredapi google-api-python-client google-auth-oauthlib gspread gspread-dataframe imap-tools msal numpy pandas pandas-datareader plotly polars pyarrow python-calamine yfinance
uv pip check --python via_vdf_312                     # ③ 裝後相容性;非 0 就停在這一境

# via_vrn_312（33 件）
uv venv via_vrn_312 --python 3.12
scripts/envcheck.sh resolve borb docling docx2python duckdb extract-msg fonttools markitdown numpy odfpy openpyxl-style-writer pandas pdf2image pdfminer-six pdfplumber pdfquery pdfrw pikepdf plotly pyarrow pymupdf pymupdf4llm pypdf pypdfium2 python-docx python-pptx pywin32 reportlab striprtf textract tika unstructured weasyprint xlrd   # ② 裝前衝突預測(pipgrip,免安裝)
uv pip install --python via_vrn_312 borb docling docx2python duckdb extract-msg fonttools markitdown numpy odfpy openpyxl-style-writer pandas pdf2image pdfminer-six pdfplumber pdfquery pdfrw pikepdf plotly pyarrow pymupdf pymupdf4llm pypdf pypdfium2 python-docx python-pptx pywin32 reportlab striprtf textract tika unstructured weasyprint xlrd
uv pip check --python via_vrn_312                     # ③ 裝後相容性;非 0 就停在這一境

```

順序規矩(冊 rounds.R2):base 端移除**必須**等目標境 `uv pip check` 綠了才做,
且逐件印令經 `via-envgov ... --approve-remove`,不批次、不自動。

## R3 收尾

- 每境 `uv pip lock` → LKGC 晉升;`uv cache prune`(候裁)
- 重跑 `VIA_LibsInventory_v0100.py audit --apply` → 衝突 RED 應歸零,盤冊出新版號
- 只能出令、本機量不到的(GRAY):
  - `L10_OWN_MODULE_MISSING:VRN_SupportBridge`
  - `L10_OWN_MODULE_MISSING:VIA_SafeFix_PathRegistry`
  - `L10_OWN_MODULE_MISSING:VIS_UltimateAccelerator_V10`
  - `L10_OWN_MODULE_MISSING:via_net`
  - `L10_OWN_MODULE_MISSING:VDF_D2_DataEngines_v1`
  - `L10_OWN_MODULE_MISSING:VIS_UltimateAccelerator_V12_MEGA`
  - `L10_OWN_MODULE_MISSING:VRN_VDFCacheReader_v0101`
  - `L10_OWN_MODULE_MISSING:via_docforge_textlab`
  - `L10_OWN_MODULE_MISSING:via_support_bridge`
  - `L8_NAMING_LAW:camelot_311`
  - `L8_NAMING_LAW:paddle_311`
  - `L8_NAMING_LAW:paddle_312`
  - `L8_NAMING_LAW:vmt_pm`

## 這份計畫沒有做到的事(照實寫)

- 鏡像連通:GRAY_NOT_RUN(探測屬網路行為過同意閘;本引擎不代設)
- 實際安裝:NONE(裝件一律經 VCGC via-envgov tools --apply --approve)
- 所以 R2 的每一條指令都是**沒跑過**的;R1 是跑過並自測過的。黃不是綠,GRAY 更不是綠。
