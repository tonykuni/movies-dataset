# VIA 環境矩陣 5D 分類與分配藍圖(v0100)

> 範圍:中高風險 100 名單(序號 1–100)+ 網路擴充 5 類 × 20(N 系列)。
> 原則:**尊重既有健康環境,只增不減**——`via_core` 與現存 via_ 工具一律不動,
> 本冊全部為「新增規劃」。與 `VIA_EnvManager.py` Gatekeeper 規則對齊
> (base 擋中高風險;via_core 僅白名單;新工具先過 EnvManager 決策)。
> 機器可讀版:`VeritasIntelligenceAnalytics/supportive modules/registry/VIA_Env_Matrix_5D_v0100.json`

## 一、5D 分類法定義

| 維度 | 代碼 | 取值 | 判斷依據 |
|------|------|------|----------|
| **D1 風險** | risk | `L` 低 / `M` 中 / `MH` 中高 / `H` 高 | 底層綁定深度、崩潰半徑、安全前科 |
| **D2 生態系** | eco | `PY` 純 Python / `C` C-C++ ext / `RS` Rust / `CU` CUDA-GPU / `JVM` / `NODE` / `BIN` 外部二進位(瀏覽器、驅動)/ `SYSC` 系統 C 庫(GDAL、HDF5、OpenSSL、libxml2) | 編譯與執行期依賴的語言棲地 |
| **D3 版本帶** | pyband | `312` / `311` / `310↓` / `ANY` | 對 Python 版本的支援成熟度 |
| **D4 變動率** | rot | `R1` 穩定(年級)/ `R2` 常變(季級)/ `R3` 極快(週級) | Breaking change 與環境腐爛速度 |
| **D5 聚合策略** | affinity | `CORE` 可進核心 / `MIX` 領域聚合 / `ISO` 一境一族 / `POLY` 跨語言(Mamba)/ `MULTI` 多版本軸心 | 相互支援性 vs 互斥性 |

**第四種風險(中高風險但常用 → 多版本軸心 `MULTI`)**:
NumPy(1.x↔2.x)、Pydantic(v1↔v2)、SQLAlchemy(1.4↔2.0)、Django(3/4/5)、
Protobuf(3.x↔4/5)、以及 **Python 直譯器本身(3.9–3.12)**——
每個軸心以「環境對」承載兩個版本,徹底避免同境互撞。

**黑名單與黑環境**:凡 `D1=H` 或 `D4=R3` 者列**黑名單**,永久禁入 `via_core`/base;
未分類的新工具一律先進**黑環境** `via_iso_quarantine`(臨時隔離艙),
通過 `envcheck full` + Micromamba dry-run 驗證後,依本冊歸艙。

## 二、序號索引(1–100,本冊為準)

> 歷次對話序號有漂移,**以本表為最終定錨**。78 原為 Ujson(與 35 重複),遞補 Msgpack。

| 段 | 序號 → 套件 |
|----|------------|
| 高風險 1–15 | 1 PyTorch、2 TensorFlow、3 Jax、4 ONNX Runtime、5 OpenCV、6 Pandas、7 Scikit-learn、8 Dask、9 PySpark、10 Polars、11 gRPCio、12 Aiohttp(+yarl+multidict)、13 FastAPI(+Pydantic)、14 Celery(+Kombu)、15 Twisted |
| 高風險 16–30 | 16 Selenium、17 Playwright、18 Scrapy、19 Pyjnius/PyO3、20 Appium、21 Cryptography、22 Paramiko、23 PyYAML、24 SQLAlchemy、25 Lxml、26 Boto3(+botocore)、27 LangChain、28 Pillow、29 Protobuf、30 Psycopg2 |
| 高風險 31–50 | 31 Cython、32 Numba、33 PyOpenSSL、34 Gevent、35 Ujson、36 Kafka-python/Confluent-kafka、37 Redis-py、38 H5py、39 PyArrow、40 PyTables、41 Django、42 Authlib/PyJWT、43 Pydantic-settings、44 Gunicorn/Uvicorn、45 Flower、46 Graphviz、47 BeautifulSoup4、48 Scrapy-Redis、49 Faker、50 Docker-py |
| 中風險 51–70 | 51 Flask、52 Marshmallow、53 HTTPX、54 DRF、55 Graphene/Strawberry、56 Pytest(+插件群)、57 Hypothesis、58 Locust、59 Robot Framework、60 Behave、61 Python-docx/pptx、62 ReportLab、63 Openpyxl/XlsxWriter、64 PyMuPDF、65 Pandocfilters、66 APScheduler、67 RQ、68 Prefect/Dagster、69 Schedule、70 Tenacity |
| 中風險 71–100 | 71 Colorama/Rich、72 Joblib、73 NetworkX、74 Fmpy、75 Watchdog、76 Inquirer、77 Arrow、78 Msgpack(遞補)、79 Simplejson、80 Click、81 Cerberus、82 Voluptuous、83 Schema、84 Dictor、85 Glom、86 Google-cloud-*、87 Azure-storage-blob、88 Firebase-admin、89 Fabric、90 Invoke、91 Psutil、92 GPUtil、93 Memory-profiler、94 Py-spy、95 Logbook、96 Pyproj、97 Shapely、98 Fiona、99 Tabulate、100 Humanize |
| 軸心 #0 | NumPy(衝突之王,MULTI 多版本軸,1.26 與 2.x 雙艙) |

**N 系列(網路擴充,各 20,代表名冊)**
- `N-A` 加速器:uvloop、orjson、msgspec、python-rapidjson、pysimdjson、faust-cchardet、charset-normalizer、aiodns、pycares、brotli、brotlicffi、zstandard、lz4、cramjam、blosc2、pycurl、asyncpg、aiomcache、hiredis、ciso8601
- `N-S` 爬蟲:pyppeteer、requests-html、autoscraper、parsel、selectolax、html5lib、extruct、feedparser、trafilatura、newspaper3k、mechanicalsoup、splinter、DrissionPage、crawlee、gazpacho、scrapling(+16/17/18/47/48 併艙)
- `N-H` HTTP:requests、urllib3、httpcore、h11、h2、hyperframe、yarl、multidict、frozenlist、aiosignal、treq、grequests、requests-toolbelt、requests-cache、niquests、websockets、websocket-client、httplib2(+12/53 併艙)
- `N-F` 偽裝:fake-useragent、fake-headers、latest-user-agents、scrapy-fake-useragent、requests-random-user-agent、undetected-chromedriver、selenium-stealth、selenium-wire、playwright-stealth、nodriver、botasaurus、camoufox、cloudscraper、cfscrape、curl-cffi、tls-client、hrequests、primp、browser-cookie3、browserforge
- `N-P` 代理:pysocks、socksio、python-socks、aiohttp-socks、httpx-socks、requests[socks]、proxy.py、mitmproxy、proxybroker2、scrapy-rotating-proxies、scrapy-proxies、rotating-free-proxies、free-proxy、proxyscrape、swiftshadow、stem、torpy、pproxy、proxy-checker、requests-ip-rotator

## 三、5D 分類總表(同簽名同列)

| 5D 簽名(risk/eco/pyband/rot/affinity) | 序號(套件群) |
|------|------|
| H / CU+C / 311 / R2 / ISO | 1、2、3、4(深度學習驅動族) |
| H / C+SYSC / 311 / R2 / ISO | 5(OpenCV)、64(PyMuPDF) |
| MULTI / C / ANY / R2 / MULTI | #0 NumPy、13 Pydantic 軸、24 SQLAlchemy 軸、29 Protobuf、41 Django 軸 |
| MH / C / 310–312 / R2 / MIX | 6、7、8、38、39、40、72(資料科學族) |
| H / JVM / 311 / R1 / POLY | 9(PySpark)、19(Pyjnius 半邊) |
| MH / RS / 312 / R2 / MIX | 10(Polars) |
| H / C / 311 / R1 / ISO | 11(gRPCio)、30(Psycopg2)、36(Kafka 族) |
| M / PY+C / 312 / R2 / MIX | 12、53、N-H 全數(HTTP 族,yarl/multidict 三位一體同艙) |
| M / PY / 312 / R3 / MIX | 13(FastAPI+Pydantic v2)、43、44、55 |
| MH / PY / 311 / R2 / MIX | 14、45、66、67、68、69、70(任務調度族) |
| H / PY / 310↓ / R1 / ISO | 15(Twisted)、legacy 軸舊件 |
| H / BIN / 311 / R3 / ISO | 16、17、18、48、N-S 全數(瀏覽器/爬蟲族) |
| H / RS+C / 311 / R2 / POLY | 19(PyO3)、21、33、94(Rust/OpenSSL 編譯族) |
| M / NODE+BIN / 312 / R2 / POLY | 20(Appium)、nodeenv 橋 |
| MH / C+OS / 312 / R1 / ISO | 22、50、75、89、90、91、92、93(系統操作族) |
| M / C / ANY / R1 / CORE→MIX | 23(PyYAML)、25(Lxml)、28(Pillow)、47(BS4)(常用但有前科,聚合於 ETL 艙) |
| H / PY / 311 / R3 / ISO | 26、27、84、85、86、87、88(依賴鏈爆炸族:雲端 SDK 與 LLM 框架分二艙) |
| H / C+LLVM / 311 / R2 / ISO | 31(Cython)、32(Numba)(編譯器族) |
| MH / C / 311 / R2 / ISO | 34(Gevent,Monkey-Patch 危險)、35、78、79(序列化雜項) |
| M / PY+BIN / 312 / R2 / ISO | 49、56、57、58、59、60(測試族) |
| M / C+SYSC / 312 / R1 / MIX | 61、62、63、65、46(文件/報表族) |
| H / SYSC / 310 / R1 / POLY | 96、97、98(GIS 地雷族,強制 Mamba) |
| L / PY / ANY / R1 / CORE | 71、76、77、80、99、100(白名單候選,經 EnvManager 審批可進 via_core) |
| M / PY / ANY / R1 / MIX | 51、52、54、73、74、81、82、83、95(Web v1 與驗證族) |
| H / C+RS / 312 / R2 / ISO | N-A 全數(事件迴圈/編解碼加速族,會替換系統預設行為) |
| H / BIN+TLS / 311 / R3 / ISO | N-F 全數(反偵測族,腐爛率最高) |
| H / PY+OS / 311 / R2 / ISO | N-P 全數(代理/隧道族,涉網路權限) |

## 四、環境分配矩陣(5 集群 × 5 = 25 個新增環境)

### 集群一:AI 運算與大數據

| via_name | python | libs(序號) | ecosystem | risk level |
|----------|--------|-------------|-----------|------------|
| via_iso_ml_cuda_H | 3.11 | 1、2、3、4(NumPy 版本隨框架鎖定) | CUDA + C++ | H |
| via_mix_ds_np1_M | 3.10 | #0(NumPy 1.26)、6、7、8、38、40、72 | C + Fortran | MH |
| via_mix_ds_np2_M | 3.12 | #0(NumPy 2.x)、6、7、10、39 | C + Rust | MH |
| via_iso_spark_H | 3.11 | 9、36 | JVM + C(librdkafka) | H |
| via_iso_viz_M | 3.11 | 5、28、62、Matplotlib | C + SYSC(FFmpeg/freetype) | M |

### 集群二:現代化 Web、API 與雲端

| via_name | python | libs(序號) | ecosystem | risk level |
|----------|--------|-------------|-----------|------------|
| via_mix_api_v2_M | 3.12 | 13(Pydantic v2 軸)、43、44、55 | PY + Asyncio | M |
| via_mix_web_v1_M | 3.10 | 41(Django 3/4)、51、52、54、81、82、83(Pydantic v1 軸) | PY + WSGI | M |
| via_iso_cloud_H | 3.11 | 26、42、86、87、88 | PY(依賴鏈爆炸)+ Auth | H |
| via_iso_net_H | 3.11 | 11、29(Protobuf 軸)、30、37 | C-bindings | H |
| via_poly_node_M | 3.12 + Node 20 | 20、nodeenv、N-S 之 pyppeteer | NODE + BIN | M |

### 集群三:系統底層、安全與自動化

| via_name | python | libs(序號) | ecosystem | risk level |
|----------|--------|-------------|-----------|------------|
| via_poly_rust_H | 3.11 | 19、21、33、94 | Rust + OpenSSL | H |
| via_iso_compilers_H | 3.11 | 31、32(+ccache 配套) | C + LLVM | H |
| via_iso_gis_H | 3.10(Micromamba) | 96、97、98(+GDAL/GEOS/PROJ) | SYSC | H |
| via_iso_ops_M | 3.12 | 22、50、75、89、90、91、92、93 | C + OS Kernel | MH |
| via_iso_test_M | 3.12 | 49、56、57、58、59、60 | PY + WebDrivers | M |

### 集群四:任務調度、資料工程與邊緣隔離

| via_name | python | libs(序號) | ecosystem | risk level |
|----------|--------|-------------|-----------|------------|
| via_mix_task_M | 3.11 | 14、34、45、66、67、68、69、70 | PY + Redis/MQ | MH |
| via_mix_etl_M | 3.12 | 23、25、46、47、61、63、64、65 | C-Parsers + SYSC | M |
| via_iso_llm_H | 3.11 | 27、84、85 | PY(R3 極快更新) | H |
| via_iso_legacy_H | 3.9/3.10 | 15、24(SQLAlchemy 1.4 軸)、41(Django 3.x 軸)、NumPy 1.x 舊件 | PY | H |
| via_audit_L | 3.12 | Top 8 檢測工具 + uv + micromamba + poetry + 35/78/79 驗證用 | PY | L |

### 集群五:高併發網路與反爬對抗(新增)

| via_name | python | libs(序號/名冊) | ecosystem | risk level |
|----------|--------|-----------------|-----------|------------|
| via_iso_accel_H | 3.12 | N-A × 20(uvloop、orjson、asyncpg…) | C + Rust(替換事件迴圈/編解碼) | H |
| via_iso_scrape_H | 3.11 | 16、17、18、48、N-S 名冊 | BIN(Chromium/Gecko) | H |
| via_mix_http_M | 3.12 | 12、53、N-H 名冊 | PY + TLS/OpenSSL | M |
| via_iso_stealth_H | 3.11 | N-F × 20(JA3/TLS 指紋) | BIN + TLS | H(R3) |
| via_iso_proxy_H | 3.11 | N-P × 20(SOCKS/隧道/輪換) | PY + OS 網路 | H |

**基座(既有,不動)**:`via_core`(3.12,白名單:71、76、77、80、91、99、100 類 L 級,
經 EnvManager `plan-install` 審批後才進);**黑環境**:`via_iso_quarantine`(3.12,常備空艙,
新工具驗證週轉用,隨時可整艙重建)。

## 五、Python 多版本分配原則

| 版本 | 環境 | 理由 |
|------|------|------|
| 3.12 | core、audit、api_v2、ops、etl、test、http、accel、node、ds_np2 | 現代純 Python 與 Rust 輪最快 |
| 3.11 | ml_cuda、spark、viz、cloud、net、task、llm、rust、compilers、scrape、stealth、proxy | 二進位輪支援最穩的主力帶 |
| 3.10 | ds_np1、web_v1、gis | NumPy 1.x / Django 3-4 / GDAL 成熟帶 |
| 3.9 | legacy | 安全下限,只收時代眼淚 |

```powershell
# uv 多版本一鍵建艙(走 uv.toml 鏡像鏈:清華 → 阿里 → 官方兜底)
uv venv C:\Users\tonyk\envs\via_mix_ds_np2_M --python 3.12
uv venv C:\Users\tonyk\envs\via_iso_ml_cuda_H --python 3.11
uv pip install --python C:\Users\tonyk\envs\via_iso_ml_cuda_H\Scripts\python.exe torch numpy
```

## 六、執行 SOP(四步驗證法 × 本 repo 工具鏈)

1. **預檢**:`envcheck.sh info <pkg>` + `envcheck.sh resolve <pkg>`(裝前需求與衝突預測,不動環境)。
2. **模擬**:`uv pip install --dry-run`(pip 生態)或 `Invoke-VIA-MicromambaResolver.ps1`(conda 生態 SAT dry-run)。
3. **建置**:`uv venv --python <版本>` + 鏡像鏈安裝;GIS/跨語言艙改 micromamba。
4. **驗證與存證**:`envcheck.sh fast`(逐艙)→ `python VIA_MambaBridge_v0100.py merge`
   → 衝突入 `VIA_EnvManager_ConflictReport.json`,史錄入 History JSONL;
   艙位異動寫回 `VIA_Env_Matrix_5D_v0100.json` 的 `assignments`(只增不減)。
