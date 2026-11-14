<!-- converted from VIA_TW_SubGroup_SSOT_v0100.xlsx -->

## Sheet: 00_README
| 項目 | 值 |  |
| --- | --- | --- |
| 版本 | VIA_SubGroup_SSOT_v0100 |  |
| 資料截止 | 2026-08-17 |  |
| L1 大類數 | 14 |  |
| L2 次族群數 | 77 |  |
| 成員筆數(含跨族群) | 378 |  |
| 個股數(去重四碼) | 301 |  |
| 跨族群個股數 | 60 |  |
| 市場別 LOCKED 筆數 | 185 |  |
| 市場別 PENDING 筆數 | 193 |  |
| 來源 S1 覆蓋 | 133 檔 → 0 遺漏 |  |
| 來源 S2 覆蓋 | 203 檔 → 0 遺漏 |  |
| 國際同業筆數 | 110 |  |
| 原檔問題數 | 19 |  |
| 編號 | 規則 | 說明 |
| R01 | 三種分類法不可混用 | Method A 角色(Leader/Peer/Laggard) × Method B 規模流動性 × Method C 資本主導力，三軸獨立輸出，不可合併成單一標籤。 |
| R02 | 門檻一律 Dynamic Criteria | 0.40 / 0.50 / 0.85 僅作為文件 Base Quantile，系統內不得硬編碼；q_t 依市場狀態、波動、廣度、樣本數與 FDR 動態調整。 |
| R03 | 無別即歸一 | 同一 L2 內 Leader/Peer/Laggard 若無顯著區隔，該 L2 標記 INVALID，不得硬切。 |
| R04 | Laggard 收錄但不入指數 | 族群指數 = Leader + Peer 之 Normalized ADJ Close 平均；Laggard 標註 ✕指數。 |
| R05 | 一股多族群 → 主/次歸屬 | 同一四碼可屬多個 L2，但僅一個 PRIMARY；其餘 SECONDARY 不重複計入族群指數（Duplicate_Counting_Risk）。 |
| R06 | 代碼三碼同源 | TW_TICKER 四碼 → yfinance .TW/.TWO → Bloomberg 'TT'，前四位必相同，禁止反寫覆蓋。 |
| R07 | 市場別待驗證需標記 | 市場別非來自上傳檔案者標 PENDING，交由 CGE --fetch-tw（TWSE t187ap03_L / TPEX mopsfin_t187ap03_O）核對後升 LOCKED。 |
| R08 | 只增不減 | 本 SSOT 只增節點；成員退出以 status=DORMANT 標記，不得刪除歷史。 |
## Sheet: 10_族群樹
| L1 | L2 | L3功能格 | 成員數 | 核心數 |
| --- | --- | --- | --- | --- |
| A 上游材料 | A1 玻纖布 / 玻纖紗 | AI 高階 Low-Dk / Low-CTE / T-Glass 骨架材料 | 6 | 4 |
| A 上游材料 | A2 銅箔基板 CCL | Ultra / Super Low Loss 銅箔基板與膠片 | 6 | 3 |
| A 上游材料 | A3 銅箔 / 樹脂 / 化工基材 | CCL 上游銅箔與環氧樹脂 | 5 | 2 |
| A 上游材料 | A4 半導體化學品 / 光阻 / 耗材 | 先進製程與先進封裝濕製程耗材、通路 | 8 | 4 |
| A 上游材料 | A5 矽晶圓 / 靶材 / 研磨材 | 晶圓、再生晶圓、CMP 與靶材 | 5 | 3 |
| B 載板與 PCB | B1 ABF / FC-BGA 載板 | 高階 IC 載板（AI GPU / ASIC 專用） | 4 | 3 |
| B 載板與 PCB | B2 BT 載板 / 記憶體載板 | BT 樹脂載板、記憶體與射頻模組載板 | 4 | 0 |
| B 載板與 PCB | B3 AI 高速板 / HDI / 主板 PCB | AI 伺服器 UBB / OAM / Switch 主板 | 8 | 3 |
| B 載板與 PCB | B4 軟板 FPC | 軟性印刷電路板與軟硬結合板 | 5 | 2 |
| B 載板與 PCB | B5 PCB 設備 / 鑽針 / 檢測 | PCB 與載板製程設備、AOI、雷射鑽孔 | 7 | 4 |
| C 半導體製造與封裝 | C1 晶圓代工 | 邏輯與特殊製程晶圓代工 | 4 | 4 |
| C 半導體製造與封裝 | C2 先進封裝設備 (CoWoS / SoIC) | 濕製程、點膠、挑晶、壓膜、測試整合設備 | 10 | 7 |
| C 半導體製造與封裝 | C3 廠務 / 無塵室 / 機電工程 | 晶圓廠與資料中心建置工程 | 7 | 5 |
| C 半導體製造與封裝 | C4 封測 OSAT | 封裝與測試代工 | 10 | 4 |
| C 半導體製造與封裝 | C5 測試介面 / 探針卡 / 測試座 | HBM 與 AI 晶片高頻測試界面 | 5 | 3 |
| C 半導體製造與封裝 | C6 材料分析 / 驗證檢測 | MA / FA 微結構分析與可靠度驗證 | 3 | 3 |
| D 記憶體 | D1 HBM / 高頻寬記憶體 | 台廠僅為介面 IP / 封測外溢受惠 | 3 | 0 |
| D 記憶體 | D2 DRAM / NOR / 利基記憶體 | 傳統 DRAM 與利基記憶體受排擠效應 | 4 | 3 |
| D 記憶體 | D3 記憶體模組 / 控制 IC | 模組廠與 NAND 控制晶片 | 5 | 4 |
| E IC 設計與 IP | E1 AI ASIC 設計服務 | CSP 自研晶片 NRE + Turnkey | 5 | 3 |
| E IC 設計與 IP | E2 矽智財 IP | 介面 IP、CPU 核心、eNVM | 5 | 3 |
| E IC 設計與 IP | E3 高速傳輸 / 介面 IC | USB4 / PCIe / Retimer / BMC | 4 | 3 |
| E IC 設計與 IP | E4 電源管理 IC (PMIC) | DDR5 / NPU / GPU 供電晶片 | 4 | 3 |
| E IC 設計與 IP | E5 消費 / 網通 IC 設計 | SoC、驅動 IC、乙太網路 IC | 6 | 3 |
| F AI 伺服器系統 | F1 AI OEM / ODM 整機櫃 (L10/L11) | 整櫃系統整合與液冷測試 | 7 | 5 |
| F AI 伺服器系統 | F2 主機板 / GPU 基板 (L6) | 板級代工，毛利率高於整機 | 5 | 3 |
| F AI 伺服器系統 | F3 機殼 / 機櫃 / 結構件 | 液冷機櫃鈑金、壓鑄與 5U 機殼 | 6 | 3 |
| F AI 伺服器系統 | F4 滑軌 / 導軌 / 精密機構 | 重載液冷機櫃盲插滑軌 | 2 | 1 |
| F AI 伺服器系統 | F5 連接器 / 高速線材 / 端子 | NVLink、224G 高速連接與 DAC/AEC 線材 | 5 | 3 |
| G AI 散熱 | G1 水冷板 / CDU / 液冷系統 | Cold Plate 與冷卻液分配裝置 | 5 | 3 |
| G AI 散熱 | G2 均熱片 / VC / 熱管 | 晶片第一層導熱介面 | 5 | 3 |
| G AI 散熱 | G3 快接頭 QD / 閥件 / 泵浦 | 零漏水關鍵件，認證門檻最高 | 3 | 3 |
| G AI 散熱 | G4 風扇 / 馬達 | 高風壓高轉速風扇與 BLDC 馬達 | 4 | 1 |
| G AI 散熱 | G5 熱交換器 / 漏液感測 | CDU 內板式熱交換與防漏偵測 | 3 | 1 |
| G AI 散熱 | G6 浸沒式 / 兩相散熱 | 單相 / 兩相浸沒式機櫃與介質 | 4 | 1 |
| H AI 電力與機房 | H1 伺服器電源 PSU / 電源模組 | 3kW–8kW 高瓦數電源 | 6 | 3 |
| H AI 電力與機房 | H2 BBU 備援電池模組 | 機櫃斷電保護電池包 | 6 | 4 |
| H AI 電力與機房 | H3 重電 / 變壓器 / 開關設備 | 資料中心與電網供電設備 | 7 | 4 |
| H AI 電力與機房 | H4 UPS / 機房基礎設施 | 不斷電系統與機房監控 | 4 | 1 |
| H AI 電力與機房 | H5 電線電纜 / 匯流排 | 高壓電纜與 Busbar | 3 | 2 |
| I 光通訊與矽光子 | I1 CPO 共封裝光學 / 光引擎 | COUPE 平台與 51.2T 以上共封裝 | 3 | 1 |
| I 光通訊與矽光子 | I2 FAU 光纖陣列 / 精密光學耦合 | 微米級光纖對準貼合 | 3 | 1 |
| I 光通訊與矽光子 | I3 雷射源 / 三五族磊晶 | InP / GaAs 外部雷射光源 | 3 | 2 |
| I 光通訊與矽光子 | I4 光收發模組 / 光被動元件 | 800G / 1.6T 可插拔光模組 | 6 | 3 |
| I 光通訊與矽光子 | I5 交換器 / 白牌網通設備 | 800G Switch 與資料中心網通 | 6 | 1 |
| J 被動元件 | J1 MLCC 積層陶瓷電容 | 高容值、車用與 AI 高階 MLCC | 5 | 4 |
| J 被動元件 | J2 晶片電阻 Chip Resistor | 厚膜 / 薄膜精密電阻 | 4 | 3 |
| J 被動元件 | J3 電感 / TLVR / 磁性元件 | AI 供電架構 TLVR 與一體成型電感 | 7 | 3 |
| J 被動元件 | J4 鋁電解 / 固態電容 | AI 伺服器與 AI PC 電源端儲能 | 4 | 3 |
| J 被動元件 | J5 保護元件 | 熱敏 / 壓敏 / 過電流保護 | 3 | 3 |
| J 被動元件 | J6 石英 / 頻率元件 | TCXO / OCXO 與石英振盪器 | 3 | 2 |
| J 被動元件 | J7 LTCC / 高頻被動模組 | 低軌衛星與毫米波高頻元件 | 3 | 1 |
| J 被動元件 | J8 變壓器 / PoE 磁性元件 | 伺服器與網通高功率變壓器 | 3 | 2 |
| J 被動元件 | J9 被動元件材料 / 設備 | 陶瓷粉末、陶瓷基板、調阻與包裝設備 | 4 | 1 |
| K AI PC 與消費電子 | K1 AI PC 品牌 | Copilot+ / NPU ≥40 TOPS 品牌機 | 4 | 2 |
| K AI PC 與消費電子 | K2 NB / PC 代工 ODM | 美系品牌 AI PC 代工 | 5 | 2 |
| K AI PC 與消費電子 | K3 AI PC 零組件 · IC | USB4 / PMIC / 觸控 / Wi-Fi 7 | 7 | 5 |
| K AI PC 與消費電子 | K4 AI PC 零組件 · 散熱機構 | 超薄熱導管與高密度風扇 | 4 | 1 |
| K AI PC 與消費電子 | K5 AI PC 零組件 · 電池電源 | 高容量鋰電池模組與快充 | 4 | 2 |
| K AI PC 與消費電子 | K6 AI PC 零組件 · 記憶體模組 | LPDDR5X 與 SSD 模組 | 4 | 0 |
| L 其他科技族群 | L1 光學鏡頭 / CIS | 手機、車用鏡頭與感測封裝 | 6 | 3 |
| L 其他科技族群 | L2 低軌衛星 / 衛星通訊 | 地面站、天線與射頻前端 | 6 | 3 |
| L 其他科技族群 | L3 軍工航太 | 航太結構件、無人機與國防系統 | 6 | 3 |
| L 其他科技族群 | L4 機器人 / 自動化 | 傳動元件、機械手臂與智慧製造 | 7 | 4 |
| L 其他科技族群 | L5 電動車 / 車用零組件 | 傳動、車用連接器與功率元件 | 5 | 3 |
| L 其他科技族群 | L6 資安 / 系統整合 | SI、資安服務與雲端維運 | 5 | 4 |
| L 其他科技族群 | L7 工控 / 物流 / 供應鏈周邊 | 工業電腦與科技物流 | 5 | 2 |
| L 其他科技族群 | L8 生技醫療 | CDMO、新藥與學名藥 | 5 | 3 |
| M 傳產輪動 | M1 貨櫃航運 | 遠洋貨櫃三雄 | 3 | 3 |
| M 傳產輪動 | M2 散裝航運 | 海岬型 / 輕便型散裝 | 7 | 3 |
| M 傳產輪動 | M3 航空 | 客貨運航空 | 3 | 3 |
| M 傳產輪動 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 熱軋、冷軋與不鏽鋼 | 6 | 3 |
| M 傳產輪動 | M5 鋼鐵 · 條鋼 / 型鋼 | 鋼筋、條鋼與型鋼 | 5 | 2 |
| M 傳產輪動 | M6 金融 | 金控與銀行 | 5 | 5 |
| M 傳產輪動 | M7 觀光餐飲 | 餐飲連鎖、旅行社與飯店 | 5 | 4 |
| M 傳產輪動 | M8 傳產材料 / 其他 | 橡塑膠與傳產材料 | 3 | 0 |
| Z 待歸類 | Z1 待歸類 / 來源殘留 | 來源檔案有、分類樹尚未定義功能格者 | 3 | 0 |
## Sheet: 20_成員名冊
| L1 | L2 | 個股 | TW_TICKER | 市場 | 市場驗證 | YFINANCE | BLOOMBERG | 定位 | 歸屬 | 計入族群指數 | MethodA角色(來源) | MethodB規模(來源) | 來源 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A 上游材料 | A1 玻纖布 / 玻纖紗 | 建榮 | 5340 | 上櫃 | PENDING | 5340.TWO | 5340 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| A 上游材料 | A1 玻纖布 / 玻纖紗 | 富喬 | 1815 | 上市 | PENDING | 1815.TW | 1815 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| A 上游材料 | A1 玻纖布 / 玻纖紗 | 台玻 | 1802 | 上市 | PENDING | 1802.TW | 1802 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| A 上游材料 | A1 玻纖布 / 玻纖紗 | 德宏 | 5475 | 上櫃 | PENDING | 5475.TWO | 5475 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| A 上游材料 | A1 玻纖布 / 玻纖紗 | 南亞 | 1303 | 上市 | PENDING | 1303.TW | 1303 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 中型股 (Mid Cap) | S2 |
| A 上游材料 | A1 玻纖布 / 玻纖紗 | 宏和 | 1446 | 上市 | PENDING | 1446.TW | 1446 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| A 上游材料 | A2 銅箔基板 CCL | 台光電 | 2383 | 上市 | PENDING | 2383.TW | 2383 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| A 上游材料 | A2 銅箔基板 CCL | 台燿 | 6274 | 上市 | PENDING | 6274.TW | 6274 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| A 上游材料 | A2 銅箔基板 CCL | 聯茂 | 6288 | 上市 | PENDING | 6288.TW | 6288 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| A 上游材料 | A2 銅箔基板 CCL | 騰輝電子-KY | 6672 | 上櫃 | PENDING | 6672.TWO | 6672 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| A 上游材料 | A2 銅箔基板 CCL | 聯致 | 3585 | 上櫃 | PENDING | 3585.TWO | 3585 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| A 上游材料 | A2 銅箔基板 CCL | 南亞 | 1303 | 上市 | PENDING | 1303.TW | 1303 TT | SAT | SECONDARY | N(避免重複計數) | LEADER (領先龍頭) | 中型股 (Mid Cap) | S2 |
| A 上游材料 | A3 銅箔 / 樹脂 / 化工基材 | 金居 | 8358 | 上櫃 | PENDING | 8358.TWO | 8358 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| A 上游材料 | A3 銅箔 / 樹脂 / 化工基材 | 長興 | 1717 | 上市 | PENDING | 1717.TW | 1717 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| A 上游材料 | A3 銅箔 / 樹脂 / 化工基材 | 南亞 | 1303 | 上市 | PENDING | 1303.TW | 1303 TT | SAT | SECONDARY | N(避免重複計數) | LEADER (領先龍頭) | 中型股 (Mid Cap) | S2 |
| A 上游材料 | A3 銅箔 / 樹脂 / 化工基材 | 台虹 | 8039 | 上櫃 | PENDING | 8039.TWO | 8039 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| A 上游材料 | A3 銅箔 / 樹脂 / 化工基材 | 永光 | 1711 | 上市 | PENDING | 1711.TW | 1711 TT | SAT | PRIMARY | Y | LAGGARD (自動剔除) | 小型股 (Small Cap) | S2 |
| A 上游材料 | A4 半導體化學品 / 光阻 / 耗材 | 崇越 | 5434 | 上市 | PENDING | 5434.TW | 5434 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| A 上游材料 | A4 半導體化學品 / 光阻 / 耗材 | 華立 | 3010 | 上市 | PENDING | 3010.TW | 3010 TT | CORE | PRIMARY | Y | PEER (同步跟風) | 中型股 (Mid Cap) | S2 |
| A 上游材料 | A4 半導體化學品 / 光阻 / 耗材 | 三福化 | 4755 | 上市 | PENDING | 4755.TW | 4755 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| A 上游材料 | A4 半導體化學品 / 光阻 / 耗材 | 勝一 | 1773 | 上市 | PENDING | 1773.TW | 1773 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| A 上游材料 | A4 半導體化學品 / 光阻 / 耗材 | 長興 | 1717 | 上市 | PENDING | 1717.TW | 1717 TT | SAT | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| A 上游材料 | A4 半導體化學品 / 光阻 / 耗材 | 信紘科 | 6667 | 上櫃 | LOCKED | 6667.TWO | 6667 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 小型股 (Small Cap) | S1+S2 |
| A 上游材料 | A4 半導體化學品 / 光阻 / 耗材 | 康普 | 4739 | 上櫃 | PENDING | 4739.TWO | 4739 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| A 上游材料 | A4 半導體化學品 / 光阻 / 耗材 | 美琪瑪 | 4721 | 上櫃 | PENDING | 4721.TWO | 4721 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 大型股 (Large Cap) | S2 |
| A 上游材料 | A5 矽晶圓 / 靶材 / 研磨材 | 環球晶 | 6488 | 上櫃 | LOCKED | 6488.TWO | 6488 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| A 上游材料 | A5 矽晶圓 / 靶材 / 研磨材 | 合晶 | 6182 | 上櫃 | PENDING | 6182.TWO | 6182 TT | CORE | PRIMARY | Y | PEER (同步跟風) | 小型股 (Small Cap) | S2 |
| A 上游材料 | A5 矽晶圓 / 靶材 / 研磨材 | 中砂 | 1560 | 上市 | PENDING | 1560.TW | 1560 TT | CORE | PRIMARY | Y | PEER (同步跟風) | 小型股 (Small Cap) | S2 |
| A 上游材料 | A5 矽晶圓 / 靶材 / 研磨材 | 辛耘 | 3583 | 上市 | LOCKED | 3583.TW | 3583 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 小型股 (Small Cap) | S1+S2 |
| A 上游材料 | A5 矽晶圓 / 靶材 / 研磨材 | 光洋科 | 1785 | 上櫃 | PENDING | 1785.TWO | 1785 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| B 載板與 PCB | B1 ABF / FC-BGA 載板 | 欣興 | 3037 | 上市 | LOCKED | 3037.TW | 3037 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| B 載板與 PCB | B1 ABF / FC-BGA 載板 | 南電 | 8046 | 上市 | LOCKED | 8046.TW | 8046 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| B 載板與 PCB | B1 ABF / FC-BGA 載板 | 景碩 | 3189 | 上市 | LOCKED | 3189.TW | 3189 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| B 載板與 PCB | B1 ABF / FC-BGA 載板 | 臻鼎-KY | 4958 | 上市 | PENDING | 4958.TW | 4958 TT | SAT | SECONDARY | N(避免重複計數) | LEADER (領先龍頭) | 大型股 (Large Cap) | S2 |
| B 載板與 PCB | B2 BT 載板 / 記憶體載板 | 南電 | 8046 | 上市 | LOCKED | 8046.TW | 8046 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 小型股 (Small Cap) | S1+S2 |
| B 載板與 PCB | B2 BT 載板 / 記憶體載板 | 景碩 | 3189 | 上市 | LOCKED | 3189.TW | 3189 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 小型股 (Small Cap) | S1+S2 |
| B 載板與 PCB | B2 BT 載板 / 記憶體載板 | 欣興 | 3037 | 上市 | LOCKED | 3037.TW | 3037 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 小型股 (Small Cap) | S1+S2 |
| B 載板與 PCB | B2 BT 載板 / 記憶體載板 | 華通 | 2313 | 上市 | PENDING | 2313.TW | 2313 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| B 載板與 PCB | B3 AI 高速板 / HDI / 主板 PCB | 金像電 | 2368 | 上市 | PENDING | 2368.TW | 2368 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| B 載板與 PCB | B3 AI 高速板 / HDI / 主板 PCB | 健鼎 | 3044 | 上市 | PENDING | 3044.TW | 3044 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| B 載板與 PCB | B3 AI 高速板 / HDI / 主板 PCB | 臻鼎-KY | 4958 | 上市 | PENDING | 4958.TW | 4958 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 大型股 (Large Cap) | S2 |
| B 載板與 PCB | B3 AI 高速板 / HDI / 主板 PCB | 華通 | 2313 | 上市 | PENDING | 2313.TW | 2313 TT | SAT | SECONDARY | N(避免重複計數) | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| B 載板與 PCB | B3 AI 高速板 / HDI / 主板 PCB | 燿華 | 2367 | 上市 | PENDING | 2367.TW | 2367 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 中型股 (Mid Cap) | S2 |
| B 載板與 PCB | B3 AI 高速板 / HDI / 主板 PCB | 瀚宇博 | 5469 | 上市 | PENDING | 5469.TW | 5469 TT | SAT | PRIMARY | Y | PEER (同步跟風) | 小型股 (Small Cap) | S2 |
| B 載板與 PCB | B3 AI 高速板 / HDI / 主板 PCB | 定穎投控 | 3715 | 上櫃 | PENDING | 3715.TWO | 3715 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| B 載板與 PCB | B3 AI 高速板 / HDI / 主板 PCB | 敬鵬 | 2355 | 上市 | PENDING | 2355.TW | 2355 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| B 載板與 PCB | B4 軟板 FPC | 臻鼎-KY | 4958 | 上市 | PENDING | 4958.TW | 4958 TT | SAT | SECONDARY | N(避免重複計數) | LEADER (領先龍頭) | 大型股 (Large Cap) | S2 |
| B 載板與 PCB | B4 軟板 FPC | 台郡 | 6269 | 上市 | PENDING | 6269.TW | 6269 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 中型股 (Mid Cap) | S2 |
| B 載板與 PCB | B4 軟板 FPC | 嘉聯益 | 6153 | 上櫃 | PENDING | 6153.TWO | 6153 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 大型股 (Large Cap) | S2 |
| B 載板與 PCB | B4 軟板 FPC | 旭軟 | 3390 | 上櫃 | PENDING | 3390.TWO | 3390 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| B 載板與 PCB | B4 軟板 FPC | 毅嘉 | 2402 | 上櫃 | PENDING | 2402.TWO | 2402 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| B 載板與 PCB | B5 PCB 設備 / 鑽針 / 檢測 | 牧德 | 3563 | 上櫃 | PENDING | 3563.TWO | 3563 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| B 載板與 PCB | B5 PCB 設備 / 鑽針 / 檢測 | 由田 | 3455 | 上櫃 | PENDING | 3455.TWO | 3455 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| B 載板與 PCB | B5 PCB 設備 / 鑽針 / 檢測 | 志聖 | 2467 | 上市 | LOCKED | 2467.TW | 2467 TT | CORE | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| B 載板與 PCB | B5 PCB 設備 / 鑽針 / 檢測 | 雷科 | 6207 | 上市 | PENDING | 6207.TW | 6207 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| B 載板與 PCB | B5 PCB 設備 / 鑽針 / 檢測 | 尖點 | 8021 | 上櫃 | PENDING | 8021.TWO | 8021 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| B 載板與 PCB | B5 PCB 設備 / 鑽針 / 檢測 | 大量 | 3167 | 上櫃 | LOCKED | 3167.TWO | 3167 TT | SAT | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| B 載板與 PCB | B5 PCB 設備 / 鑽針 / 檢測 | 興普 | 6432 | 上市 | PENDING | 6432.TW | 6432 TT | WATCH | PRIMARY | Y |  |  | S3對話研究 |
| C 半導體製造與封裝 | C1 晶圓代工 | 台積電 | 2330 | 上市 | LOCKED | 2330.TW | 2330 TT | CORE | PRIMARY | Y | LEADER | 大型股 (Large Cap) | S1+S2 |
| C 半導體製造與封裝 | C1 晶圓代工 | 聯電 | 2303 | 上市 | LOCKED | 2303.TW | 2303 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| C 半導體製造與封裝 | C1 晶圓代工 | 世界先進 | 5347 | 上櫃 | LOCKED | 5347.TWO | 5347 TT | CORE | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| C 半導體製造與封裝 | C1 晶圓代工 | 力積電 | 6770 | 上市 | LOCKED | 6770.TW | 6770 TT | CORE | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| C 半導體製造與封裝 | C2 先進封裝設備 (CoWoS / SoIC) | 弘塑 | 3131 | 上櫃 | LOCKED | 3131.TWO | 3131 TT | CORE | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| C 半導體製造與封裝 | C2 先進封裝設備 (CoWoS / SoIC) | 辛耘 | 3583 | 上市 | LOCKED | 3583.TW | 3583 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| C 半導體製造與封裝 | C2 先進封裝設備 (CoWoS / SoIC) | 萬潤 | 6187 | 上櫃 | LOCKED | 6187.TWO | 6187 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| C 半導體製造與封裝 | C2 先進封裝設備 (CoWoS / SoIC) | 均華 | 6640 | 上櫃 | PENDING | 6640.TWO | 6640 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| C 半導體製造與封裝 | C2 先進封裝設備 (CoWoS / SoIC) | 志聖 | 2467 | 上市 | LOCKED | 2467.TW | 2467 TT | CORE | SECONDARY | N(避免重複計數) | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| C 半導體製造與封裝 | C2 先進封裝設備 (CoWoS / SoIC) | 京鼎 | 3413 | 上櫃 | LOCKED | 3413.TWO | 3413 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| C 半導體製造與封裝 | C2 先進封裝設備 (CoWoS / SoIC) | 家登 | 3680 | 上櫃 | LOCKED | 3680.TWO | 3680 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| C 半導體製造與封裝 | C2 先進封裝設備 (CoWoS / SoIC) | 盟立 | 2464 | 上市 | LOCKED | 2464.TW | 2464 TT | SAT | PRIMARY | Y | PEER | 中型股 (Mid Cap) | S1+S2 |
| C 半導體製造與封裝 | C2 先進封裝設備 (CoWoS / SoIC) | 漢民 | 6279 | 上櫃 | PENDING | 6279.TWO | 6279 TT | SAT | PRIMARY | Y | PEER (同步跟風) | 小型股 (Small Cap) | S2 |
| C 半導體製造與封裝 | C2 先進封裝設備 (CoWoS / SoIC) | 致茂 | 2360 | 上市 | LOCKED | 2360.TW | 2360 TT | SAT | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| C 半導體製造與封裝 | C3 廠務 / 無塵室 / 機電工程 | 漢唐 | 2404 | 上市 | LOCKED | 2404.TW | 2404 TT | CORE | PRIMARY | Y | LEADER | 中型股 (Mid Cap) | S1+S2 |
| C 半導體製造與封裝 | C3 廠務 / 無塵室 / 機電工程 | 帆宣 | 6196 | 上市 | LOCKED | 6196.TW | 6196 TT | CORE | PRIMARY | Y | LEADER | 中型股 (Mid Cap) | S1+S2 |
| C 半導體製造與封裝 | C3 廠務 / 無塵室 / 機電工程 | 亞翔 | 6139 | 上市 | LOCKED | 6139.TW | 6139 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| C 半導體製造與封裝 | C3 廠務 / 無塵室 / 機電工程 | 聖暉 | 5536 | 上櫃 | PENDING | 5536.TWO | 5536 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| C 半導體製造與封裝 | C3 廠務 / 無塵室 / 機電工程 | 信紘科 | 6667 | 上櫃 | LOCKED | 6667.TWO | 6667 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| C 半導體製造與封裝 | C3 廠務 / 無塵室 / 機電工程 | 千附 | 8383 | 上市 | LOCKED | 8383.TW | 8383 TT | SAT | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| C 半導體製造與封裝 | C3 廠務 / 無塵室 / 機電工程 | 廣運 | 6125 | 上市 | LOCKED | 6125.TW | 6125 TT | SAT | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| C 半導體製造與封裝 | C4 封測 OSAT | 日月光投控 | 3711 | 上市 | LOCKED | 3711.TW | 3711 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| C 半導體製造與封裝 | C4 封測 OSAT | 力成 | 6239 | 上市 | PENDING | 6239.TW | 6239 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| C 半導體製造與封裝 | C4 封測 OSAT | 京元電 | 2449 | 上市 | PENDING | 2449.TW | 2449 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| C 半導體製造與封裝 | C4 封測 OSAT | 頎邦 | 6147 | 上市 | PENDING | 6147.TW | 6147 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| C 半導體製造與封裝 | C4 封測 OSAT | 南茂 | 8150 | 上櫃 | PENDING | 8150.TWO | 8150 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| C 半導體製造與封裝 | C4 封測 OSAT | 矽品 | 2325 | 上市 | PENDING | 2325.TW | 2325 TT | SAT | PRIMARY | Y | PEER (同步跟風) | 小型股 (Small Cap) | S2 |
| C 半導體製造與封裝 | C4 封測 OSAT | 華泰 | 2329 | 上市 | PENDING | 2329.TW | 2329 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| C 半導體製造與封裝 | C4 封測 OSAT | 精材 | 3374 | 上櫃 | PENDING | 3374.TWO | 3374 TT | SAT | PRIMARY | Y | PEER (同步跟風) | 中型股 (Mid Cap) | S2 |
| C 半導體製造與封裝 | C4 封測 OSAT | 欣銓 | 3264 | 上櫃 | PENDING | 3264.TWO | 3264 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 中型股 (Mid Cap) | S2 |
| C 半導體製造與封裝 | C4 封測 OSAT | 長華科 | 6548 | 上櫃 | PENDING | 6548.TWO | 6548 TT | SAT | PRIMARY | Y | LAGGARD (自動剔除) | 小型股 (Small Cap) | S2 |
| C 半導體製造與封裝 | C5 測試介面 / 探針卡 / 測試座 | 穎崴 | 6515 | 上市 | PENDING | 6515.TW | 6515 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| C 半導體製造與封裝 | C5 測試介面 / 探針卡 / 測試座 | 精測 | 6510 | 上櫃 | PENDING | 6510.TWO | 6510 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| C 半導體製造與封裝 | C5 測試介面 / 探針卡 / 測試座 | 旺矽 | 6223 | 上櫃 | PENDING | 6223.TWO | 6223 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| C 半導體製造與封裝 | C5 測試介面 / 探針卡 / 測試座 | 雍智科技 | 6820 | 上櫃 | PENDING | 6820.TWO | 6820 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| C 半導體製造與封裝 | C5 測試介面 / 探針卡 / 測試座 | 中探針 | 6217 | 上市 | PENDING | 6217.TW | 6217 TT | SAT | PRIMARY | Y | PEER (同步跟風) | 小型股 (Small Cap) | S2 |
| C 半導體製造與封裝 | C6 材料分析 / 驗證檢測 | 閎康 | 3587 | 上市 | PENDING | 3587.TW | 3587 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| C 半導體製造與封裝 | C6 材料分析 / 驗證檢測 | 汎銓 | 6830 | 上櫃 | PENDING | 6830.TWO | 6830 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| C 半導體製造與封裝 | C6 材料分析 / 驗證檢測 | 宜特 | 3289 | 上櫃 | PENDING | 3289.TWO | 3289 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| D 記憶體 | D1 HBM / 高頻寬記憶體 | 創意 | 3443 | 上市 | LOCKED | 3443.TW | 3443 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 大型股 (Large Cap) | S1+S2 |
| D 記憶體 | D1 HBM / 高頻寬記憶體 | 世芯-KY | 3661 | 上市 | LOCKED | 3661.TW | 3661 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 大型股 (Large Cap) | S1+S2 |
| D 記憶體 | D1 HBM / 高頻寬記憶體 | 京元電 | 2449 | 上市 | PENDING | 2449.TW | 2449 TT | SAT | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| D 記憶體 | D2 DRAM / NOR / 利基記憶體 | 南亞科 | 2408 | 上市 | LOCKED | 2408.TW | 2408 TT | CORE | PRIMARY | Y | LEADER | 中型股 (Mid Cap) | S1+S2 |
| D 記憶體 | D2 DRAM / NOR / 利基記憶體 | 華邦電 | 2344 | 上市 | LOCKED | 2344.TW | 2344 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| D 記憶體 | D2 DRAM / NOR / 利基記憶體 | 旺宏 | 2337 | 上市 | LOCKED | 2337.TW | 2337 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| D 記憶體 | D2 DRAM / NOR / 利基記憶體 | 力積電 | 6770 | 上市 | LOCKED | 6770.TW | 6770 TT | SAT | SECONDARY | N(避免重複計數) | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| D 記憶體 | D3 記憶體模組 / 控制 IC | 群聯 | 8299 | 上櫃 | LOCKED | 8299.TWO | 8299 TT | CORE | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| D 記憶體 | D3 記憶體模組 / 控制 IC | 威剛 | 3260 | 上市 | LOCKED | 3260.TW | 3260 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| D 記憶體 | D3 記憶體模組 / 控制 IC | 十銓 | 4967 | 上櫃 | PENDING | 4967.TWO | 4967 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| D 記憶體 | D3 記憶體模組 / 控制 IC | 宜鼎 | 5289 | 上櫃 | PENDING | 5289.TWO | 5289 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| D 記憶體 | D3 記憶體模組 / 控制 IC | 創見 | 2451 | 上櫃 | PENDING | 2451.TWO | 2451 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| E IC 設計與 IP | E1 AI ASIC 設計服務 | 世芯-KY | 3661 | 上市 | LOCKED | 3661.TW | 3661 TT | CORE | PRIMARY | Y | LEADER | 大型股 (Large Cap) | S1+S2 |
| E IC 設計與 IP | E1 AI ASIC 設計服務 | 創意 | 3443 | 上市 | LOCKED | 3443.TW | 3443 TT | CORE | PRIMARY | Y | LEADER | 大型股 (Large Cap) | S1+S2 |
| E IC 設計與 IP | E1 AI ASIC 設計服務 | 智原 | 3035 | 上市 | LOCKED | 3035.TW | 3035 TT | CORE | PRIMARY | Y | PEER | 中型股 (Mid Cap) | S1+S2 |
| E IC 設計與 IP | E1 AI ASIC 設計服務 | 聯發科 | 2454 | 上市 | LOCKED | 2454.TW | 2454 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 小型股 (Small Cap) | S1+S2 |
| E IC 設計與 IP | E1 AI ASIC 設計服務 | 揚智 | 2569 | 上市 | LOCKED | 2569.TW | 2569 TT | SAT | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| E IC 設計與 IP | E2 矽智財 IP | 力旺 | 3529 | 上櫃 | LOCKED | 3529.TWO | 3529 TT | CORE | PRIMARY | Y | LEADER | 中型股 (Mid Cap) | S1+S2 |
| E IC 設計與 IP | E2 矽智財 IP | M31 | 6643 | 上櫃 | LOCKED | 6643.TWO | 6643 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| E IC 設計與 IP | E2 矽智財 IP | 晶心科 | 6533 | 上櫃 | LOCKED | 6533.TWO | 6533 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| E IC 設計與 IP | E2 矽智財 IP | 愛普 | 6531 | 上櫃 | PENDING | 6531.TWO | 6531 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| E IC 設計與 IP | E2 矽智財 IP | 創意 | 3443 | 上市 | LOCKED | 3443.TW | 3443 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 大型股 (Large Cap) | S1+S2 |
| E IC 設計與 IP | E3 高速傳輸 / 介面 IC | 祥碩 | 5269 | 上市 | PENDING | 5269.TW | 5269 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| E IC 設計與 IP | E3 高速傳輸 / 介面 IC | 譜瑞-KY | 4966 | 上市 | PENDING | 4966.TW | 4966 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| E IC 設計與 IP | E3 高速傳輸 / 介面 IC | 信驊 | 5274 | 上市 | PENDING | 5274.TW | 5274 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| E IC 設計與 IP | E3 高速傳輸 / 介面 IC | 群聯 | 8299 | 上櫃 | LOCKED | 8299.TWO | 8299 TT | SAT | SECONDARY | N(避免重複計數) | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| E IC 設計與 IP | E4 電源管理 IC (PMIC) | 茂達 | 6138 | 上市 | PENDING | 6138.TW | 6138 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| E IC 設計與 IP | E4 電源管理 IC (PMIC) | 致新 | 8081 | 上市 | PENDING | 8081.TW | 8081 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| E IC 設計與 IP | E4 電源管理 IC (PMIC) | 矽力-KY | 6415 | 上市 | PENDING | 6415.TW | 6415 TT | CORE | PRIMARY | Y | LAGGARD (自動剔除) | 中型股 (Mid Cap) | S2 |
| E IC 設計與 IP | E4 電源管理 IC (PMIC) | 通嘉 | 3588 | 上櫃 | PENDING | 3588.TWO | 3588 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| E IC 設計與 IP | E5 消費 / 網通 IC 設計 | 聯發科 | 2454 | 上市 | LOCKED | 2454.TW | 2454 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| E IC 設計與 IP | E5 消費 / 網通 IC 設計 | 聯詠 | 3034 | 上市 | PENDING | 3034.TW | 3034 TT | CORE | PRIMARY | Y | LAGGARD (自動剔除) | 小型股 (Small Cap) | S2 |
| E IC 設計與 IP | E5 消費 / 網通 IC 設計 | 瑞昱 | 2379 | 上市 | PENDING | 2379.TW | 2379 TT | CORE | PRIMARY | Y | PEER (同步跟風) | 小型股 (Small Cap) | S2 |
| E IC 設計與 IP | E5 消費 / 網通 IC 設計 | 敦泰 | 3545 | 上市 | PENDING | 3545.TW | 3545 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 中型股 (Mid Cap) | S2 |
| E IC 設計與 IP | E5 消費 / 網通 IC 設計 | 達發 | 6526 | 上櫃 | PENDING | 6526.TWO | 6526 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| E IC 設計與 IP | E5 消費 / 網通 IC 設計 | 立積 | 4968 | 上櫃 | PENDING | 4968.TWO | 4968 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| F AI 伺服器系統 | F1 AI OEM / ODM 整機櫃 (L10/L11) | 鴻海 | 2317 | 上市 | LOCKED | 2317.TW | 2317 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| F AI 伺服器系統 | F1 AI OEM / ODM 整機櫃 (L10/L11) | 廣達 | 2382 | 上市 | LOCKED | 2382.TW | 2382 TT | CORE | PRIMARY | Y | PEER | 中型股 (Mid Cap) | S1+S2 |
| F AI 伺服器系統 | F1 AI OEM / ODM 整機櫃 (L10/L11) | 緯穎 | 6669 | 上市 | LOCKED | 6669.TW | 6669 TT | CORE | PRIMARY | Y | LEADER | 大型股 (Large Cap) | S1+S2 |
| F AI 伺服器系統 | F1 AI OEM / ODM 整機櫃 (L10/L11) | 緯創 | 3231 | 上市 | LOCKED | 3231.TW | 3231 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| F AI 伺服器系統 | F1 AI OEM / ODM 整機櫃 (L10/L11) | 技嘉 | 2376 | 上市 | LOCKED | 2376.TW | 2376 TT | CORE | PRIMARY | Y | LAGGARD | 中型股 (Mid Cap) | S1+S2 |
| F AI 伺服器系統 | F1 AI OEM / ODM 整機櫃 (L10/L11) | 英業達 | 2356 | 上市 | LOCKED | 2356.TW | 2356 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 小型股 (Small Cap) | S1+S2 |
| F AI 伺服器系統 | F1 AI OEM / ODM 整機櫃 (L10/L11) | 華碩 | 2357 | 上市 | PENDING | 2357.TW | 2357 TT | SAT | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| F AI 伺服器系統 | F2 主機板 / GPU 基板 (L6) | 緯創 | 3231 | 上市 | LOCKED | 3231.TW | 3231 TT | CORE | SECONDARY | N(避免重複計數) | PEER | 小型股 (Small Cap) | S1+S2 |
| F AI 伺服器系統 | F2 主機板 / GPU 基板 (L6) | 英業達 | 2356 | 上市 | LOCKED | 2356.TW | 2356 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| F AI 伺服器系統 | F2 主機板 / GPU 基板 (L6) | 技嘉 | 2376 | 上市 | LOCKED | 2376.TW | 2376 TT | CORE | SECONDARY | N(避免重複計數) | LAGGARD | 中型股 (Mid Cap) | S1+S2 |
| F AI 伺服器系統 | F2 主機板 / GPU 基板 (L6) | 微星 | 2377 | 上市 | PENDING | 2377.TW | 2377 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| F AI 伺服器系統 | F2 主機板 / GPU 基板 (L6) | 鴻海 | 2317 | 上市 | LOCKED | 2317.TW | 2317 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 小型股 (Small Cap) | S1+S2 |
| F AI 伺服器系統 | F3 機殼 / 機櫃 / 結構件 | 勤誠 | 8210 | 上市 | LOCKED | 8210.TW | 8210 TT | CORE | PRIMARY | Y | PEER | 大型股 (Large Cap) | S1+S2 |
| F AI 伺服器系統 | F3 機殼 / 機櫃 / 結構件 | 晟銘電 | 3013 | 上市 | PENDING | 3013.TW | 3013 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| F AI 伺服器系統 | F3 機殼 / 機櫃 / 結構件 | 迎廣 | 6117 | 上櫃 | PENDING | 6117.TWO | 6117 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| F AI 伺服器系統 | F3 機殼 / 機櫃 / 結構件 | 營邦 | 3693 | 上櫃 | PENDING | 3693.TWO | 3693 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| F AI 伺服器系統 | F3 機殼 / 機櫃 / 結構件 | 喬鼎 | 3052 | 上櫃 | PENDING | 3052.TWO | 3052 TT | WATCH | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| F AI 伺服器系統 | F3 機殼 / 機櫃 / 結構件 | 華孚 | 6235 | 上櫃 | PENDING | 6235.TWO | 6235 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| F AI 伺服器系統 | F4 滑軌 / 導軌 / 精密機構 | 川湖 | 2059 | 上市 | PENDING | 2059.TW | 2059 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| F AI 伺服器系統 | F4 滑軌 / 導軌 / 精密機構 | 尚新 | 5325 | 上櫃 | PENDING | 5325.TWO | 5325 TT | WATCH | PRIMARY | Y |  |  | S3對話研究 |
| F AI 伺服器系統 | F5 連接器 / 高速線材 / 端子 | 嘉澤 | 3533 | 上市 | PENDING | 3533.TW | 3533 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| F AI 伺服器系統 | F5 連接器 / 高速線材 / 端子 | 貿聯-KY | 3665 | 上市 | LOCKED | 3665.TW | 3665 TT | CORE | PRIMARY | Y | LEADER | 大型股 (Large Cap) | S1+S2 |
| F AI 伺服器系統 | F5 連接器 / 高速線材 / 端子 | 信邦 | 3023 | 上市 | PENDING | 3023.TW | 3023 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| F AI 伺服器系統 | F5 連接器 / 高速線材 / 端子 | 凡甲 | 3526 | 上市 | PENDING | 3526.TW | 3526 TT | SAT | PRIMARY | Y | PEER (同步跟風) | 中型股 (Mid Cap) | S2 |
| F AI 伺服器系統 | F5 連接器 / 高速線材 / 端子 | 建舜電 | 3322 | 上櫃 | PENDING | 3322.TWO | 3322 TT | WATCH | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| G AI 散熱 | G1 水冷板 / CDU / 液冷系統 | 奇鋐 | 3017 | 上市 | LOCKED | 3017.TW | 3017 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| G AI 散熱 | G1 水冷板 / CDU / 液冷系統 | 雙鴻 | 3324 | 上市 | LOCKED | 3324.TW | 3324 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| G AI 散熱 | G1 水冷板 / CDU / 液冷系統 | 台達電 | 2308 | 上市 | LOCKED | 2308.TW | 2308 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 小型股 (Small Cap) | S1+S2 |
| G AI 散熱 | G1 水冷板 / CDU / 液冷系統 | 力致 | 3483 | 上市 | LOCKED | 3483.TW | 3483 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| G AI 散熱 | G1 水冷板 / CDU / 液冷系統 | 尼得科超眾(已併) | 6230 | 上市 | PENDING | 6230.TW | 6230 TT | WATCH | PRIMARY | Y |  |  | S3對話研究 |
| G AI 散熱 | G2 均熱片 / VC / 熱管 | 健策 | 3653 | 上市 | PENDING | 3653.TW | 3653 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| G AI 散熱 | G2 均熱片 / VC / 熱管 | 一詮 | 2486 | 上櫃 | PENDING | 2486.TWO | 2486 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| G AI 散熱 | G2 均熱片 / VC / 熱管 | 泰碩 | 3338 | 上櫃 | LOCKED | 3338.TWO | 3338 TT | CORE | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| G AI 散熱 | G2 均熱片 / VC / 熱管 | 邁科 | 6831 | 上櫃 | PENDING | 6831.TWO | 6831 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| G AI 散熱 | G2 均熱片 / VC / 熱管 | 動力-KY | 6591 | 上市 | LOCKED | 6591.TW | 6591 TT | CORE | PRIMARY | Y | PEER | 大型股 (Large Cap) | S1+S2 |
| G AI 散熱 | G3 快接頭 QD / 閥件 / 泵浦 | 富世達 | 6805 | 上市 | PENDING | 6805.TW | 6805 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| G AI 散熱 | G3 快接頭 QD / 閥件 / 泵浦 | 君帆 | 6421 | 上櫃 | PENDING | 6421.TWO | 6421 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| G AI 散熱 | G3 快接頭 QD / 閥件 / 泵浦 | 元山 | 6275 | 上櫃 | LOCKED | 6275.TWO | 6275 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| G AI 散熱 | G4 風扇 / 馬達 | 建準 | 2421 | 上市 | LOCKED | 2421.TW | 2421 TT | CORE | PRIMARY | Y | PEER | 中型股 (Mid Cap) | S1+S2 |
| G AI 散熱 | G4 風扇 / 馬達 | 東林 | 3018 | 上市 | PENDING | 3018.TW | 3018 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| G AI 散熱 | G4 風扇 / 馬達 | 升陽 | 8028 | 上市 | PENDING | 8028.TW | 8028 TT | WATCH | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| G AI 散熱 | G4 風扇 / 馬達 | 元山 | 6275 | 上櫃 | LOCKED | 6275.TWO | 6275 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 小型股 (Small Cap) | S1+S2 |
| G AI 散熱 | G5 熱交換器 / 漏液感測 | 高力 | 8996 | 上櫃 | PENDING | 8996.TWO | 8996 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| G AI 散熱 | G5 熱交換器 / 漏液感測 | 泰碩 | 3338 | 上櫃 | LOCKED | 3338.TWO | 3338 TT | SAT | SECONDARY | N(避免重複計數) | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| G AI 散熱 | G5 熱交換器 / 漏液感測 | 台達電 | 2308 | 上市 | LOCKED | 2308.TW | 2308 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 小型股 (Small Cap) | S1+S2 |
| G AI 散熱 | G6 浸沒式 / 兩相散熱 | 力致 | 3483 | 上市 | LOCKED | 3483.TW | 3483 TT | CORE | SECONDARY | N(避免重複計數) | PEER | 小型股 (Small Cap) | S1+S2 |
| G AI 散熱 | G6 浸沒式 / 兩相散熱 | 技嘉 | 2376 | 上市 | LOCKED | 2376.TW | 2376 TT | SAT | SECONDARY | N(避免重複計數) | LAGGARD | 中型股 (Mid Cap) | S1+S2 |
| G AI 散熱 | G6 浸沒式 / 兩相散熱 | 微星 | 2377 | 上市 | PENDING | 2377.TW | 2377 TT | SAT | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| G AI 散熱 | G6 浸沒式 / 兩相散熱 | 一詮 | 2486 | 上櫃 | PENDING | 2486.TWO | 2486 TT | SAT | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| H AI 電力與機房 | H1 伺服器電源 PSU / 電源模組 | 台達電 | 2308 | 上市 | LOCKED | 2308.TW | 2308 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| H AI 電力與機房 | H1 伺服器電源 PSU / 電源模組 | 光寶科 | 2301 | 上市 | LOCKED | 2301.TW | 2301 TT | CORE | PRIMARY | Y | PEER | 中型股 (Mid Cap) | S1+S2 |
| H AI 電力與機房 | H1 伺服器電源 PSU / 電源模組 | 全漢 | 3015 | 上市 | LOCKED | 3015.TW | 3015 TT | CORE | PRIMARY | Y | PEER | 中型股 (Mid Cap) | S1+S2 |
| H AI 電力與機房 | H1 伺服器電源 PSU / 電源模組 | 康舒 | 6282 | 上市 | PENDING | 6282.TW | 6282 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| H AI 電力與機房 | H1 伺服器電源 PSU / 電源模組 | 僑威 | 5263 | 上櫃 | LOCKED | 5263.TWO | 5263 TT | SAT | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| H AI 電力與機房 | H1 伺服器電源 PSU / 電源模組 | 旭隼 | 6409 | 上櫃 | PENDING | 6409.TWO | 6409 TT | SAT | SECONDARY | N(避免重複計數) | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| H AI 電力與機房 | H2 BBU 備援電池模組 | 新盛力 | 4931 | 上市 | LOCKED | 4931.TW | 4931 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| H AI 電力與機房 | H2 BBU 備援電池模組 | AES-KY | 6781 | 上市 | LOCKED | 6781.TW | 6781 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| H AI 電力與機房 | H2 BBU 備援電池模組 | 加百裕 | 3323 | 上市 | LOCKED | 3323.TW | 3323 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| H AI 電力與機房 | H2 BBU 備援電池模組 | 順達 | 3211 | 上市 | LOCKED | 3211.TW | 3211 TT | CORE | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| H AI 電力與機房 | H2 BBU 備援電池模組 | 新普 | 6121 | 上市 | PENDING | 6121.TW | 6121 TT | SAT | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| H AI 電力與機房 | H2 BBU 備援電池模組 | 立凱電 | 5227 | 上櫃 | PENDING | 5227.TWO | 5227 TT | WATCH | PRIMARY | Y | LEADER (領先龍頭) | 大型股 (Large Cap) | S2 |
| H AI 電力與機房 | H3 重電 / 變壓器 / 開關設備 | 華城 | 1519 | 上市 | LOCKED | 1519.TW | 1519 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| H AI 電力與機房 | H3 重電 / 變壓器 / 開關設備 | 士電 | 1503 | 上市 | LOCKED | 1503.TW | 1503 TT | CORE | PRIMARY | Y | PEER | 中型股 (Mid Cap) | S1+S2 |
| H AI 電力與機房 | H3 重電 / 變壓器 / 開關設備 | 中興電 | 1513 | 上市 | LOCKED | 1513.TW | 1513 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| H AI 電力與機房 | H3 重電 / 變壓器 / 開關設備 | 亞力 | 1514 | 上市 | LOCKED | 1514.TW | 1514 TT | CORE | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| H AI 電力與機房 | H3 重電 / 變壓器 / 開關設備 | 東元 | 1504 | 上市 | LOCKED | 1504.TW | 1504 TT | SAT | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| H AI 電力與機房 | H3 重電 / 變壓器 / 開關設備 | 大同 | 2371 | 上市 | LOCKED | 2371.TW | 2371 TT | SAT | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| H AI 電力與機房 | H3 重電 / 變壓器 / 開關設備 | 聲寶 | 1604 | 上市 | PENDING | 1604.TW | 1604 TT | WATCH | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| H AI 電力與機房 | H4 UPS / 機房基礎設施 | 台達電 | 2308 | 上市 | LOCKED | 2308.TW | 2308 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 小型股 (Small Cap) | S1+S2 |
| H AI 電力與機房 | H4 UPS / 機房基礎設施 | 飛宏 | 2457 | 上市 | PENDING | 2457.TW | 2457 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| H AI 電力與機房 | H4 UPS / 機房基礎設施 | 旭隼 | 6409 | 上櫃 | PENDING | 6409.TWO | 6409 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| H AI 電力與機房 | H4 UPS / 機房基礎設施 | 光寶科 | 2301 | 上市 | LOCKED | 2301.TW | 2301 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 中型股 (Mid Cap) | S1+S2 |
| H AI 電力與機房 | H5 電線電纜 / 匯流排 | 大亞 | 1609 | 上市 | PENDING | 1609.TW | 1609 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| H AI 電力與機房 | H5 電線電纜 / 匯流排 | 華新 | 1605 | 上市 | PENDING | 1605.TW | 1605 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| H AI 電力與機房 | H5 電線電纜 / 匯流排 | 宏泰 | 1612 | 上市 | PENDING | 1612.TW | 1612 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| I 光通訊與矽光子 | I1 CPO 共封裝光學 / 光引擎 | 台積電 | 2330 | 上市 | LOCKED | 2330.TW | 2330 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 大型股 (Large Cap) | S1+S2 |
| I 光通訊與矽光子 | I1 CPO 共封裝光學 / 光引擎 | 訊芯-KY | 6451 | 上市 | PENDING | 6451.TW | 6451 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| I 光通訊與矽光子 | I1 CPO 共封裝光學 / 光引擎 | 日月光投控 | 3711 | 上市 | LOCKED | 3711.TW | 3711 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 小型股 (Small Cap) | S1+S2 |
| I 光通訊與矽光子 | I2 FAU 光纖陣列 / 精密光學耦合 | 上詮 | 3363 | 上市 | PENDING | 3363.TW | 3363 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| I 光通訊與矽光子 | I2 FAU 光纖陣列 / 精密光學耦合 | 大立光 | 3008 | 上市 | LOCKED | 3008.TW | 3008 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 小型股 (Small Cap) | S1+S2 |
| I 光通訊與矽光子 | I2 FAU 光纖陣列 / 精密光學耦合 | 聯鈞 | 3450 | 上櫃 | PENDING | 3450.TWO | 3450 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| I 光通訊與矽光子 | I3 雷射源 / 三五族磊晶 | 聯亞 | 3081 | 上市 | PENDING | 3081.TW | 3081 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 中型股 (Mid Cap) | S2 |
| I 光通訊與矽光子 | I3 雷射源 / 三五族磊晶 | 全新 | 2455 | 上市 | PENDING | 2455.TW | 2455 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| I 光通訊與矽光子 | I3 雷射源 / 三五族磊晶 | 聯鈞 | 3450 | 上櫃 | PENDING | 3450.TWO | 3450 TT | SAT | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| I 光通訊與矽光子 | I4 光收發模組 / 光被動元件 | 光聖 | 6442 | 上櫃 | PENDING | 6442.TWO | 6442 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| I 光通訊與矽光子 | I4 光收發模組 / 光被動元件 | 華星光 | 4979 | 上櫃 | PENDING | 4979.TWO | 4979 TT | CORE | PRIMARY | Y | PEER (同步跟風) | 小型股 (Small Cap) | S2 |
| I 光通訊與矽光子 | I4 光收發模組 / 光被動元件 | 波若威 | 3163 | 上櫃 | PENDING | 3163.TWO | 3163 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| I 光通訊與矽光子 | I4 光收發模組 / 光被動元件 | 前鼎 | 4908 | 上櫃 | PENDING | 4908.TWO | 4908 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| I 光通訊與矽光子 | I4 光收發模組 / 光被動元件 | 眾達-KY | 4977 | 上櫃 | PENDING | 4977.TWO | 4977 TT | SAT | PRIMARY | Y | PEER (同步跟風) | 小型股 (Small Cap) | S2 |
| I 光通訊與矽光子 | I4 光收發模組 / 光被動元件 | 聯亞 | 3081 | 上市 | PENDING | 3081.TW | 3081 TT | SAT | SECONDARY | N(避免重複計數) | LEADER (領先龍頭) | 中型股 (Mid Cap) | S2 |
| I 光通訊與矽光子 | I5 交換器 / 白牌網通設備 | 智邦 | 2345 | 上市 | LOCKED | 2345.TW | 2345 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| I 光通訊與矽光子 | I5 交換器 / 白牌網通設備 | 明泰 | 3380 | 上市 | LOCKED | 3380.TW | 3380 TT | SAT | PRIMARY | Y | LAGGARD | 中型股 (Mid Cap) | S1+S2 |
| I 光通訊與矽光子 | I5 交換器 / 白牌網通設備 | 智易 | 3596 | 上市 | LOCKED | 3596.TW | 3596 TT | SAT | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| I 光通訊與矽光子 | I5 交換器 / 白牌網通設備 | 中磊 | 5388 | 上市 | LOCKED | 5388.TW | 5388 TT | SAT | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| I 光通訊與矽光子 | I5 交換器 / 白牌網通設備 | 啟碁 | 6285 | 上市 | LOCKED | 6285.TW | 6285 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 中型股 (Mid Cap) | S1+S2 |
| I 光通訊與矽光子 | I5 交換器 / 白牌網通設備 | 星通 | 3025 | 上櫃 | PENDING | 3025.TWO | 3025 TT | WATCH | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J1 MLCC 積層陶瓷電容 | 國巨 | 2327 | 上市 | LOCKED | 2327.TW | 2327 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| J 被動元件 | J1 MLCC 積層陶瓷電容 | 華新科 | 2492 | 上市 | LOCKED | 2492.TW | 2492 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| J 被動元件 | J1 MLCC 積層陶瓷電容 | 禾伸堂 | 3026 | 上櫃 | LOCKED | 3026.TWO | 3026 TT | CORE | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| J 被動元件 | J1 MLCC 積層陶瓷電容 | 信昌電 | 6173 | 上櫃 | LOCKED | 6173.TWO | 6173 TT | CORE | PRIMARY | Y | PEER | 大型股 (Large Cap) | S1+S2 |
| J 被動元件 | J1 MLCC 積層陶瓷電容 | 蜜望實 | 8043 | 上市 | PENDING | 8043.TW | 8043 TT | WATCH | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J2 晶片電阻 Chip Resistor | 國巨 | 2327 | 上市 | LOCKED | 2327.TW | 2327 TT | CORE | SECONDARY | N(避免重複計數) | LEADER | 小型股 (Small Cap) | S1+S2 |
| J 被動元件 | J2 晶片電阻 Chip Resistor | 華新科 | 2492 | 上市 | LOCKED | 2492.TW | 2492 TT | CORE | SECONDARY | N(避免重複計數) | PEER | 小型股 (Small Cap) | S1+S2 |
| J 被動元件 | J2 晶片電阻 Chip Resistor | 光頡 | 3624 | 上櫃 | PENDING | 3624.TWO | 3624 TT | CORE | PRIMARY | Y | PEER (同步跟風) | 小型股 (Small Cap) | S2 |
| J 被動元件 | J2 晶片電阻 Chip Resistor | 大毅 | 2478 | 上市 | PENDING | 2478.TW | 2478 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| J 被動元件 | J3 電感 / TLVR / 磁性元件 | 臺慶科 | 3357 | 上市 | PENDING | 3357.TW | 3357 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| J 被動元件 | J3 電感 / TLVR / 磁性元件 | 三集瑞-KY | 6771 | 上市 | PENDING | 6771.TW | 6771 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J3 電感 / TLVR / 磁性元件 | 乾坤 | 4767 | 上市 | PENDING | 4767.TW | 4767 TT | CORE | PRIMARY | Y | PEER (同步跟風) | 小型股 (Small Cap) | S2 |
| J 被動元件 | J3 電感 / TLVR / 磁性元件 | 鈞寶 | 6155 | 上櫃 | PENDING | 6155.TWO | 6155 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J3 電感 / TLVR / 磁性元件 | 奇力新(已併國巨) | 2456 | 上市 | PENDING | 2456.TW | 2456 TT | SAT | PRIMARY | Y | LAGGARD (自動剔除) | 中型股 (Mid Cap) | S2 |
| J 被動元件 | J3 電感 / TLVR / 磁性元件 | 千如 | 3236 | 上櫃 | PENDING | 3236.TWO | 3236 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J3 電感 / TLVR / 磁性元件 | 華容 | 5328 | 上櫃 | PENDING | 5328.TWO | 5328 TT | WATCH | PRIMARY | Y | LAGGARD (自動剔除) | 小型股 (Small Cap) | S2 |
| J 被動元件 | J4 鋁電解 / 固態電容 | 鈺邦 | 6449 | 上櫃 | PENDING | 6449.TWO | 6449 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J4 鋁電解 / 固態電容 | 立隆電 | 2472 | 上市 | PENDING | 2472.TW | 2472 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 大型股 (Large Cap) | S2 |
| J 被動元件 | J4 鋁電解 / 固態電容 | 凱美 | 2375 | 上市 | PENDING | 2375.TW | 2375 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| J 被動元件 | J4 鋁電解 / 固態電容 | 金山電 | 8042 | 上櫃 | PENDING | 8042.TWO | 8042 TT | WATCH | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J5 保護元件 | 興勤 | 2428 | 上市 | PENDING | 2428.TW | 2428 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J5 保護元件 | 聚鼎 | 6224 | 上市 | PENDING | 6224.TW | 6224 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J5 保護元件 | 佳邦 | 6284 | 上市 | PENDING | 6284.TW | 6284 TT | CORE | PRIMARY | Y | PEER (同步跟風) | 小型股 (Small Cap) | S2 |
| J 被動元件 | J6 石英 / 頻率元件 | 晶技 | 3042 | 上市 | PENDING | 3042.TW | 3042 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J6 石英 / 頻率元件 | 希華 | 2484 | 上市 | PENDING | 2484.TW | 2484 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J6 石英 / 頻率元件 | 加高 | 8182 | 上櫃 | PENDING | 8182.TWO | 8182 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J7 LTCC / 高頻被動模組 | 璟德 | 3152 | 上櫃 | PENDING | 3152.TWO | 3152 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J7 LTCC / 高頻被動模組 | 華新科 | 2492 | 上市 | LOCKED | 2492.TW | 2492 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 小型股 (Small Cap) | S1+S2 |
| J 被動元件 | J7 LTCC / 高頻被動模組 | 佳邦 | 6284 | 上市 | PENDING | 6284.TW | 6284 TT | SAT | SECONDARY | N(避免重複計數) | PEER (同步跟風) | 小型股 (Small Cap) | S2 |
| J 被動元件 | J8 變壓器 / PoE 磁性元件 | 聯寶 | 6821 | 上櫃 | PENDING | 6821.TWO | 6821 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J8 變壓器 / PoE 磁性元件 | 耀勝 | 3207 | 上櫃 | PENDING | 3207.TWO | 3207 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J8 變壓器 / PoE 磁性元件 | 台達電 | 2308 | 上市 | LOCKED | 2308.TW | 2308 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 小型股 (Small Cap) | S1+S2 |
| J 被動元件 | J9 被動元件材料 / 設備 | 信昌電 | 6173 | 上櫃 | LOCKED | 6173.TWO | 6173 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 大型股 (Large Cap) | S1+S2 |
| J 被動元件 | J9 被動元件材料 / 設備 | 九豪 | 6127 | 上櫃 | PENDING | 6127.TWO | 6127 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| J 被動元件 | J9 被動元件材料 / 設備 | 雷科 | 6207 | 上市 | PENDING | 6207.TW | 6207 TT | SAT | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| J 被動元件 | J9 被動元件材料 / 設備 | 同欣電 | 6271 | 上市 | LOCKED | 6271.TW | 6271 TT | SAT | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| K AI PC 與消費電子 | K1 AI PC 品牌 | 華碩 | 2357 | 上市 | PENDING | 2357.TW | 2357 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| K AI PC 與消費電子 | K1 AI PC 品牌 | 宏碁 | 2353 | 上市 | PENDING | 2353.TW | 2353 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| K AI PC 與消費電子 | K1 AI PC 品牌 | 微星 | 2377 | 上市 | PENDING | 2377.TW | 2377 TT | SAT | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| K AI PC 與消費電子 | K1 AI PC 品牌 | 技嘉 | 2376 | 上市 | LOCKED | 2376.TW | 2376 TT | SAT | SECONDARY | N(避免重複計數) | LAGGARD | 中型股 (Mid Cap) | S1+S2 |
| K AI PC 與消費電子 | K2 NB / PC 代工 ODM | 廣達 | 2382 | 上市 | LOCKED | 2382.TW | 2382 TT | CORE | SECONDARY | N(避免重複計數) | PEER | 中型股 (Mid Cap) | S1+S2 |
| K AI PC 與消費電子 | K2 NB / PC 代工 ODM | 仁寶 | 2324 | 上市 | PENDING | 2324.TW | 2324 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| K AI PC 與消費電子 | K2 NB / PC 代工 ODM | 緯創 | 3231 | 上市 | LOCKED | 3231.TW | 3231 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 小型股 (Small Cap) | S1+S2 |
| K AI PC 與消費電子 | K2 NB / PC 代工 ODM | 英業達 | 2356 | 上市 | LOCKED | 2356.TW | 2356 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 小型股 (Small Cap) | S1+S2 |
| K AI PC 與消費電子 | K2 NB / PC 代工 ODM | 和碩 | 4938 | 上市 | PENDING | 4938.TW | 4938 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| K AI PC 與消費電子 | K3 AI PC 零組件 · IC | 祥碩 | 5269 | 上市 | PENDING | 5269.TW | 5269 TT | CORE | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| K AI PC 與消費電子 | K3 AI PC 零組件 · IC | 譜瑞-KY | 4966 | 上市 | PENDING | 4966.TW | 4966 TT | CORE | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| K AI PC 與消費電子 | K3 AI PC 零組件 · IC | 茂達 | 6138 | 上市 | PENDING | 6138.TW | 6138 TT | CORE | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| K AI PC 與消費電子 | K3 AI PC 零組件 · IC | 致新 | 8081 | 上市 | PENDING | 8081.TW | 8081 TT | CORE | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| K AI PC 與消費電子 | K3 AI PC 零組件 · IC | 義隆 | 2458 | 上市 | PENDING | 2458.TW | 2458 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| K AI PC 與消費電子 | K3 AI PC 零組件 · IC | 瑞昱 | 2379 | 上市 | PENDING | 2379.TW | 2379 TT | SAT | SECONDARY | N(避免重複計數) | PEER (同步跟風) | 小型股 (Small Cap) | S2 |
| K AI PC 與消費電子 | K3 AI PC 零組件 · IC | 立積 | 4968 | 上櫃 | PENDING | 4968.TWO | 4968 TT | SAT | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| K AI PC 與消費電子 | K4 AI PC 零組件 · 散熱機構 | 雙鴻 | 3324 | 上市 | LOCKED | 3324.TW | 3324 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 小型股 (Small Cap) | S1+S2 |
| K AI PC 與消費電子 | K4 AI PC 零組件 · 散熱機構 | 奇鋐 | 3017 | 上市 | LOCKED | 3017.TW | 3017 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 小型股 (Small Cap) | S1+S2 |
| K AI PC 與消費電子 | K4 AI PC 零組件 · 散熱機構 | 動力-KY | 6591 | 上市 | LOCKED | 6591.TW | 6591 TT | CORE | SECONDARY | N(避免重複計數) | PEER | 大型股 (Large Cap) | S1+S2 |
| K AI PC 與消費電子 | K4 AI PC 零組件 · 散熱機構 | 建準 | 2421 | 上市 | LOCKED | 2421.TW | 2421 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 中型股 (Mid Cap) | S1+S2 |
| K AI PC 與消費電子 | K5 AI PC 零組件 · 電池電源 | 新普 | 6121 | 上市 | PENDING | 6121.TW | 6121 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| K AI PC 與消費電子 | K5 AI PC 零組件 · 電池電源 | 順達 | 3211 | 上市 | LOCKED | 3211.TW | 3211 TT | CORE | SECONDARY | N(避免重複計數) | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| K AI PC 與消費電子 | K5 AI PC 零組件 · 電池電源 | 光寶科 | 2301 | 上市 | LOCKED | 2301.TW | 2301 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 中型股 (Mid Cap) | S1+S2 |
| K AI PC 與消費電子 | K5 AI PC 零組件 · 電池電源 | 致伸 | 4915 | 上市 | PENDING | 4915.TW | 4915 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| K AI PC 與消費電子 | K6 AI PC 零組件 · 記憶體模組 | 威剛 | 3260 | 上市 | LOCKED | 3260.TW | 3260 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 小型股 (Small Cap) | S1+S2 |
| K AI PC 與消費電子 | K6 AI PC 零組件 · 記憶體模組 | 十銓 | 4967 | 上櫃 | PENDING | 4967.TWO | 4967 TT | SAT | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| K AI PC 與消費電子 | K6 AI PC 零組件 · 記憶體模組 | 宜鼎 | 5289 | 上櫃 | PENDING | 5289.TWO | 5289 TT | SAT | SECONDARY | N(避免重複計數) |  |  | S3對話研究 |
| K AI PC 與消費電子 | K6 AI PC 零組件 · 記憶體模組 | 群聯 | 8299 | 上櫃 | LOCKED | 8299.TWO | 8299 TT | SAT | SECONDARY | N(避免重複計數) | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L1 光學鏡頭 / CIS | 大立光 | 3008 | 上市 | LOCKED | 3008.TW | 3008 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L1 光學鏡頭 / CIS | 玉晶光 | 3406 | 上市 | LOCKED | 3406.TW | 3406 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L1 光學鏡頭 / CIS | 亞光 | 3019 | 上市 | LOCKED | 3019.TW | 3019 TT | CORE | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L1 光學鏡頭 / CIS | 先進光 | 3362 | 上市 | LOCKED | 3362.TW | 3362 TT | SAT | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L1 光學鏡頭 / CIS | 同欣電 | 6271 | 上市 | LOCKED | 6271.TW | 6271 TT | SAT | SECONDARY | N(避免重複計數) | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L1 光學鏡頭 / CIS | 佳凌 | 4976 | 上市 | PENDING | 4976.TW | 4976 TT | SAT | PRIMARY | Y | LAGGARD (自動剔除) | 中型股 (Mid Cap) | S2 |
| L 其他科技族群 | L2 低軌衛星 / 衛星通訊 | 昇達科 | 3491 | 上櫃 | LOCKED | 3491.TWO | 3491 TT | CORE | PRIMARY | Y | LEADER | 中型股 (Mid Cap) | S1+S2 |
| L 其他科技族群 | L2 低軌衛星 / 衛星通訊 | 台揚 | 2314 | 上市 | LOCKED | 2314.TW | 2314 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L2 低軌衛星 / 衛星通訊 | 啟碁 | 6285 | 上市 | LOCKED | 6285.TW | 6285 TT | CORE | PRIMARY | Y | PEER | 中型股 (Mid Cap) | S1+S2 |
| L 其他科技族群 | L2 低軌衛星 / 衛星通訊 | 金寶 | 2312 | 上市 | PENDING | 2312.TW | 2312 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| L 其他科技族群 | L2 低軌衛星 / 衛星通訊 | 公準 | 3178 | 上櫃 | PENDING | 3178.TWO | 3178 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| L 其他科技族群 | L2 低軌衛星 / 衛星通訊 | 同欣電 | 6271 | 上市 | LOCKED | 6271.TW | 6271 TT | SAT | SECONDARY | N(避免重複計數) | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L3 軍工航太 | 漢翔 | 2634 | 上市 | LOCKED | 2634.TW | 2634 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L3 軍工航太 | 雷虎 | 8033 | 上市 | LOCKED | 8033.TW | 8033 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L3 軍工航太 | 寶一 | 8222 | 上市 | LOCKED | 8222.TW | 8222 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L3 軍工航太 | 經緯 | 6199 | 上櫃 | PENDING | 6199.TWO | 6199 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| L 其他科技族群 | L3 軍工航太 | 千附 | 8383 | 上市 | LOCKED | 8383.TW | 8383 TT | SAT | SECONDARY | N(避免重複計數) | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L3 軍工航太 | 長榮航太 | 2645 | 上市 | PENDING | 2645.TW | 2645 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| L 其他科技族群 | L4 機器人 / 自動化 | 上銀 | 2049 | 上市 | LOCKED | 2049.TW | 2049 TT | CORE | PRIMARY | Y | LEADER | 中型股 (Mid Cap) | S1+S2 |
| L 其他科技族群 | L4 機器人 / 自動化 | 亞德客-KY | 1590 | 上市 | LOCKED | 1590.TW | 1590 TT | CORE | PRIMARY | Y | LEADER | 中型股 (Mid Cap) | S1+S2 |
| L 其他科技族群 | L4 機器人 / 自動化 | 直得 | 1597 | 上櫃 | LOCKED | 1597.TWO | 1597 TT | CORE | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L4 機器人 / 自動化 | 所羅門 | 2359 | 上市 | LOCKED | 2359.TW | 2359 TT | CORE | PRIMARY | Y | PEER | 中型股 (Mid Cap) | S1+S2 |
| L 其他科技族群 | L4 機器人 / 自動化 | 盟立 | 2464 | 上市 | LOCKED | 2464.TW | 2464 TT | SAT | SECONDARY | N(避免重複計數) | PEER | 中型股 (Mid Cap) | S1+S2 |
| L 其他科技族群 | L4 機器人 / 自動化 | 廣明 | 6188 | 上櫃 | PENDING | 6188.TWO | 6188 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| L 其他科技族群 | L4 機器人 / 自動化 | 台達電 | 2308 | 上市 | LOCKED | 2308.TW | 2308 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L5 電動車 / 車用零組件 | 和大 | 1536 | 上市 | LOCKED | 1536.TW | 1536 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L5 電動車 / 車用零組件 | 貿聯-KY | 3665 | 上市 | LOCKED | 3665.TW | 3665 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 大型股 (Large Cap) | S1+S2 |
| L 其他科技族群 | L5 電動車 / 車用零組件 | 為升 | 2231 | 上市 | LOCKED | 2231.TW | 2231 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L5 電動車 / 車用零組件 | 朋程 | 8255 | 上櫃 | LOCKED | 8255.TWO | 8255 TT | CORE | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L5 電動車 / 車用零組件 | 台達電 | 2308 | 上市 | LOCKED | 2308.TW | 2308 TT | SAT | SECONDARY | N(避免重複計數) | LEADER | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L6 資安 / 系統整合 | 精誠 | 6214 | 上櫃 | LOCKED | 6214.TWO | 6214 TT | CORE | PRIMARY | Y | PEER | 中型股 (Mid Cap) | S1+S2 |
| L 其他科技族群 | L6 資安 / 系統整合 | 零壹 | 3029 | 上市 | LOCKED | 3029.TW | 3029 TT | CORE | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L6 資安 / 系統整合 | 安碁資訊 | 6690 | 上櫃 | LOCKED | 6690.TWO | 6690 TT | CORE | PRIMARY | Y | LEADER | 中型股 (Mid Cap) | S1+S2 |
| L 其他科技族群 | L6 資安 / 系統整合 | 敦陽科 | 2480 | 上市 | LOCKED | 2480.TW | 2480 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L6 資安 / 系統整合 | 關貿 | 6183 | 上櫃 | PENDING | 6183.TWO | 6183 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| L 其他科技族群 | L7 工控 / 物流 / 供應鏈周邊 | 研華 | 2395 | 上市 | PENDING | 2395.TW | 2395 TT | CORE | PRIMARY | Y | PEER (同步跟風) | 中型股 (Mid Cap) | S2 |
| L 其他科技族群 | L7 工控 / 物流 / 供應鏈周邊 | 凌華 | 6166 | 上櫃 | PENDING | 6166.TWO | 6166 TT | CORE | PRIMARY | Y | LEADER (領先龍頭) | 大型股 (Large Cap) | S2 |
| L 其他科技族群 | L7 工控 / 物流 / 供應鏈周邊 | 台驊投控 | 2636 | 上櫃 | PENDING | 2636.TWO | 2636 TT | SAT | PRIMARY | Y | PEER (同步跟風) | 小型股 (Small Cap) | S2 |
| L 其他科技族群 | L7 工控 / 物流 / 供應鏈周邊 | 中菲行 | 5609 | 上櫃 | PENDING | 5609.TWO | 5609 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| L 其他科技族群 | L7 工控 / 物流 / 供應鏈周邊 | 欣技 | 6160 | 上櫃 | PENDING | 6160.TWO | 6160 TT | SAT | PRIMARY | Y | LEADER (領先龍頭) | 中型股 (Mid Cap) | S2 |
| L 其他科技族群 | L8 生技醫療 | 保瑞 | 6472 | 上櫃 | LOCKED | 6472.TWO | 6472 TT | CORE | PRIMARY | Y | LEADER | 大型股 (Large Cap) | S1+S2 |
| L 其他科技族群 | L8 生技醫療 | 藥華藥 | 6446 | 上市 | LOCKED | 6446.TW | 6446 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L8 生技醫療 | 美時 | 1795 | 上市 | LOCKED | 1795.TW | 1795 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| L 其他科技族群 | L8 生技醫療 | 智擎 | 4162 | 上櫃 | LOCKED | 4162.TWO | 4162 TT | SAT | PRIMARY | Y | LAGGARD | 中型股 (Mid Cap) | S1+S2 |
| L 其他科技族群 | L8 生技醫療 | 聯亞藥 | 6562 | 上櫃 | LOCKED | 6562.TWO | 6562 TT | SAT | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M1 貨櫃航運 | 長榮 | 2603 | 上市 | LOCKED | 2603.TW | 2603 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M1 貨櫃航運 | 陽明 | 2609 | 上市 | LOCKED | 2609.TW | 2609 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M1 貨櫃航運 | 萬海 | 2615 | 上市 | LOCKED | 2615.TW | 2615 TT | CORE | PRIMARY | Y | LAGGARD | 中型股 (Mid Cap) | S1+S2 |
| M 傳產輪動 | M2 散裝航運 | 裕民 | 2606 | 上市 | LOCKED | 2606.TW | 2606 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M2 散裝航運 | 慧洋-KY | 2637 | 上市 | LOCKED | 2637.TW | 2637 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M2 散裝航運 | 新興 | 2605 | 上市 | LOCKED | 2605.TW | 2605 TT | CORE | PRIMARY | Y | PEER | 大型股 (Large Cap) | S1+S2 |
| M 傳產輪動 | M2 散裝航運 | 中航 | 2612 | 上市 | LOCKED | 2612.TW | 2612 TT | SAT | PRIMARY | Y | PEER | 大型股 (Large Cap) | S1+S2 |
| M 傳產輪動 | M2 散裝航運 | 台航 | 2617 | 上市 | LOCKED | 2617.TW | 2617 TT | SAT | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M2 散裝航運 | 四維航 | 5608 | 上市 | LOCKED | 5608.TW | 5608 TT | SAT | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M2 散裝航運 | 正德 | 2641 | 上市 | LOCKED | 2641.TW | 2641 TT | SAT | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M3 航空 | 華航 | 2610 | 上市 | LOCKED | 2610.TW | 2610 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M3 航空 | 長榮航 | 2618 | 上市 | LOCKED | 2618.TW | 2618 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M3 航空 | 星宇 | 2646 | 上市 | LOCKED | 2646.TW | 2646 TT | CORE | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 中鋼 | 2002 | 上市 | LOCKED | 2002.TW | 2002 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 中鴻 | 2014 | 上市 | LOCKED | 2014.TW | 2014 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 燁輝 | 2023 | 上市 | LOCKED | 2023.TW | 2023 TT | CORE | PRIMARY | Y | PEER | 中型股 (Mid Cap) | S1+S2 |
| M 傳產輪動 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 盛餘 | 2029 | 上市 | LOCKED | 2029.TW | 2029 TT | SAT | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 燁聯 | 9957 | 上市 | LOCKED | 9957.TW | 9957 TT | SAT | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 官田鋼 | 2017 | 上市 | LOCKED | 2017.TW | 2017 TT | SAT | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M5 鋼鐵 · 條鋼 / 型鋼 | 豐興 | 2015 | 上市 | LOCKED | 2015.TW | 2015 TT | CORE | PRIMARY | Y | LEADER | 中型股 (Mid Cap) | S1+S2 |
| M 傳產輪動 | M5 鋼鐵 · 條鋼 / 型鋼 | 東和鋼鐵 | 2006 | 上市 | LOCKED | 2006.TW | 2006 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M5 鋼鐵 · 條鋼 / 型鋼 | 威致 | 2028 | 上市 | LOCKED | 2028.TW | 2028 TT | SAT | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M5 鋼鐵 · 條鋼 / 型鋼 | 春雨 | 2012 | 上市 | LOCKED | 2012.TW | 2012 TT | SAT | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M5 鋼鐵 · 條鋼 / 型鋼 | 海光 | 2038 | 上市 | PENDING | 2038.TW | 2038 TT | SAT | PRIMARY | Y |  |  | S3對話研究 |
| M 傳產輪動 | M6 金融 | 富邦金 | 2881 | 上市 | LOCKED | 2881.TW | 2881 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M6 金融 | 國泰金 | 2882 | 上市 | LOCKED | 2882.TW | 2882 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M6 金融 | 中信金 | 2891 | 上市 | PENDING | 2891.TW | 2891 TT | CORE | PRIMARY | Y |  |  | S3對話研究 |
| M 傳產輪動 | M6 金融 | 兆豐金 | 2886 | 上市 | LOCKED | 2886.TW | 2886 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M6 金融 | 玉山金 | 2884 | 上市 | LOCKED | 2884.TW | 2884 TT | CORE | PRIMARY | Y | LAGGARD | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M7 觀光餐飲 | 王品 | 2727 | 上市 | LOCKED | 2727.TW | 2727 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M7 觀光餐飲 | 瓦城 | 2729 | 上市 | LOCKED | 2729.TW | 2729 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M7 觀光餐飲 | 晶華 | 2707 | 上市 | LOCKED | 2707.TW | 2707 TT | CORE | PRIMARY | Y | PEER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M7 觀光餐飲 | 雄獅 | 2731 | 上市 | LOCKED | 2731.TW | 2731 TT | CORE | PRIMARY | Y | LEADER | 小型股 (Small Cap) | S1+S2 |
| M 傳產輪動 | M7 觀光餐飲 | 鳳凰 | 5706 | 上市 | LOCKED | 5706.TW | 5706 TT | SAT | PRIMARY | Y | LAGGARD | 中型股 (Mid Cap) | S1+S2 |
| M 傳產輪動 | M8 傳產材料 / 其他 | 厚生 | 2107 | 上市 | PENDING | 2107.TW | 2107 TT | WATCH | PRIMARY | Y | PEER (同步跟風) | 大型股 (Large Cap) | S2 |
| M 傳產輪動 | M8 傳產材料 / 其他 | 麗正 | 2302 | 上市 | PENDING | 2302.TW | 2302 TT | WATCH | PRIMARY | Y | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 |
| M 傳產輪動 | M8 傳產材料 / 其他 | 誠美材 | 4960 | 上市 | PENDING | 4960.TW | 4960 TT | WATCH | PRIMARY | Y | LEADER (領先龍頭) | 大型股 (Large Cap) | S2 |
| Z 待歸類 | Z1 待歸類 / 來源殘留 | 台特 | 8038 | 上市 | PENDING | 8038.TW | 8038 TT | WATCH | PRIMARY | N(待歸類) | LAGGARD (自動剔除) | 大型股 (Large Cap) | S2 YTD輪動｜原:先進封裝 / CoWoS / SoIC |
| Z 待歸類 | Z1 待歸類 / 來源殘留 | 欣泰 | 3024 | 上市 | PENDING | 3024.TW | 3024 TT | WATCH | PRIMARY | N(待歸類) | LEADER (領先龍頭) | 中型股 (Mid Cap) | S2 YTD輪動｜原:PCB |
| Z 待歸類 | Z1 待歸類 / 來源殘留 | 联茂 | 6213 | 上市 | PENDING | 6213.TW | 6213 TT | WATCH | PRIMARY | N(待歸類) | LEADER (領先龍頭) | 小型股 (Small Cap) | S2 YTD輪動｜原:PCB |
## Sheet: 30_國際同業
| L2 | 排名 | 公司 | 代碼 | 國別 | 上市狀態 |
| --- | --- | --- | --- | --- | --- |
| A1 玻纖布 / 玻纖紗 | 1 | 日東紡 Nittobo | 3110.T | JP | 上市 |
| A1 玻纖布 / 玻纖紗 | 2 | AGC | 5201.T | JP | 上市 |
| A1 玻纖布 / 玻纖紗 | 3 | 中國巨石 | 600176.SS | CN | 上市 |
| A1 玻纖布 / 玻纖紗 | 4 | Owens Corning | OC (NYSE) | US | 上市 |
| A1 玻纖布 / 玻纖紗 | 5 | CPIC 重慶國際複材 | 未上市 | CN | 未上市(剔除指數) |
| A2 銅箔基板 CCL | 1 | Panasonic | 6752.T | JP | 上市 |
| A2 銅箔基板 CCL | 2 | Doosan Electro | 000150.KS | KR | 上市 |
| A2 銅箔基板 CCL | 3 | 生益科技 | 600183.SS | CN | 上市 |
| A2 銅箔基板 CCL | 4 | Isola Group | 未上市 | US | 未上市(剔除指數) |
| A4 半導體化學品 / 光阻 / 耗材 | 1 | 信越化學 | 4106.T | JP | 上市 |
| A4 半導體化學品 / 光阻 / 耗材 | 2 | 東京應化 TOK | 4186.T | JP | 上市 |
| A4 半導體化學品 / 光阻 / 耗材 | 3 | Entegris | ENTG (Nasdaq) | US | 上市 |
| A4 半導體化學品 / 光阻 / 耗材 | 4 | Merck KGaA | MRK.DE | DE | 上市 |
| A4 半導體化學品 / 光阻 / 耗材 | 5 | JSR | 未上市(JIC收購) | JP | 未上市(剔除指數) |
| A5 矽晶圓 / 靶材 / 研磨材 | 1 | 信越化學 | 4106.T | JP | 上市 |
| A5 矽晶圓 / 靶材 / 研磨材 | 2 | SUMCO | 3436.T | JP | 上市 |
| B1 ABF / FC-BGA 載板 | 1 | Ibiden 揖斐電 | 4062.T | JP | 上市 |
| B1 ABF / FC-BGA 載板 | 2 | Shinko 新光電氣 | 6967.T | JP | 上市 |
| B1 ABF / FC-BGA 載板 | 3 | 三星電機 SEMCO | 009150.KS | KR | 上市 |
| B1 ABF / FC-BGA 載板 | 4 | AT&S | ATS.VI | AT | 上市 |
| B1 ABF / FC-BGA 載板 | 5 | 大德電子 | 008060.KS | KR | 上市 |
| B1 ABF / FC-BGA 載板 | 6 | 深南電路 | 002916.SZ | CN | 上市 |
| B3 AI 高速板 / HDI / 主板 PCB | 1 | TTM Technologies | TTMI (Nasdaq) | US | 上市 |
| B3 AI 高速板 / HDI / 主板 PCB | 2 | Ibiden | 4062.T | JP | 上市 |
| B3 AI 高速板 / HDI / 主板 PCB | 3 | 深南電路 | 002916.SZ | CN | 上市 |
| C1 晶圓代工 | 1 | Samsung Foundry | 005930.KS | KR | 上市 |
| C1 晶圓代工 | 2 | Intel | INTC (Nasdaq) | US | 上市 |
| C1 晶圓代工 | 3 | GlobalFoundries | GFS (Nasdaq) | US | 上市 |
| C1 晶圓代工 | 4 | 中芯國際 | 0981.HK | CN | 上市 |
| C2 先進封裝設備 (CoWoS / SoIC) | 1 | ASML | ASML (Nasdaq) | NL | 上市 |
| C2 先進封裝設備 (CoWoS / SoIC) | 2 | Applied Materials | AMAT (Nasdaq) | US | 上市 |
| C2 先進封裝設備 (CoWoS / SoIC) | 3 | Lam Research | LRCX (Nasdaq) | US | 上市 |
| C2 先進封裝設備 (CoWoS / SoIC) | 4 | Tokyo Electron | 8035.T | JP | 上市 |
| C2 先進封裝設備 (CoWoS / SoIC) | 5 | DISCO | 6146.T | JP | 上市 |
| C2 先進封裝設備 (CoWoS / SoIC) | 6 | KLA | KLAC (Nasdaq) | US | 上市 |
| C2 先進封裝設備 (CoWoS / SoIC) | 7 | Kulicke & Soffa | KLIC (Nasdaq) | US | 上市 |
| C4 封測 OSAT | 1 | Amkor | AMKR (Nasdaq) | US | 上市 |
| C4 封測 OSAT | 2 | 長電科技 | 600584.SS | CN | 上市 |
| C4 封測 OSAT | 3 | 通富微電 | 002156.SZ | CN | 上市 |
| D1 HBM / 高頻寬記憶體 | 1 | SK Hynix | 000660.KS | KR | 上市 |
| D1 HBM / 高頻寬記憶體 | 2 | Micron | MU (Nasdaq) | US | 上市 |
| D1 HBM / 高頻寬記憶體 | 3 | Samsung Electronics | 005930.KS | KR | 上市 |
| D2 DRAM / NOR / 利基記憶體 | 1 | Micron | MU (Nasdaq) | US | 上市 |
| D2 DRAM / NOR / 利基記憶體 | 2 | SK Hynix | 000660.KS | KR | 上市 |
| D2 DRAM / NOR / 利基記憶體 | 3 | Winbond/Nanya 對標: 兆易創新 | 603986.SS | CN | 上市 |
| E1 AI ASIC 設計服務 | 1 | Broadcom | AVGO (Nasdaq) | US | 上市 |
| E1 AI ASIC 設計服務 | 2 | Marvell | MRVL (Nasdaq) | US | 上市 |
| E1 AI ASIC 設計服務 | 3 | Google TPU 部門 | 未上市(GOOGL內部) | US | 未上市(剔除指數) |
| E1 AI ASIC 設計服務 | 4 | Meta MTIA 部門 | 未上市(META內部) | US | 未上市(剔除指數) |
| E1 AI ASIC 設計服務 | 5 | Microsoft Maia 部門 | 未上市(MSFT內部) | US | 未上市(剔除指數) |
| E1 AI ASIC 設計服務 | 6 | AWS Trainium 部門 | 未上市(AMZN內部) | US | 未上市(剔除指數) |
| E2 矽智財 IP | 1 | ARM | ARM (Nasdaq) | UK | 上市 |
| E2 矽智財 IP | 2 | Synopsys | SNPS (Nasdaq) | US | 上市 |
| E2 矽智財 IP | 3 | Cadence | CDNS (Nasdaq) | US | 上市 |
| E2 矽智財 IP | 4 | Siemens EDA | SIE.DE | DE | 上市 |
| E5 消費 / 網通 IC 設計 | 1 | NVIDIA | NVDA (Nasdaq) | US | 上市 |
| E5 消費 / 網通 IC 設計 | 2 | Qualcomm | QCOM (Nasdaq) | US | 上市 |
| E5 消費 / 網通 IC 設計 | 3 | AMD | AMD (Nasdaq) | US | 上市 |
| E5 消費 / 網通 IC 設計 | 4 | Broadcom | AVGO (Nasdaq) | US | 上市 |
| F1 AI OEM / ODM 整機櫃 (L10/L11) | 1 | Supermicro | SMCI (Nasdaq) | US | 上市 |
| F1 AI OEM / ODM 整機櫃 (L10/L11) | 2 | Dell | DELL (NYSE) | US | 上市 |
| F1 AI OEM / ODM 整機櫃 (L10/L11) | 3 | HPE | HPE (NYSE) | US | 上市 |
| F1 AI OEM / ODM 整機櫃 (L10/L11) | 4 | 浪潮信息 | 000977.SZ | CN | 上市 |
| F1 AI OEM / ODM 整機櫃 (L10/L11) | 5 | Wiwynn Thailand 產線 | 未上市(緯穎子公司) | TH | 未上市(剔除指數) |
| G1 水冷板 / CDU / 液冷系統 | 1 | Vertiv | VRT (NYSE) | US | 上市 |
| G1 水冷板 / CDU / 液冷系統 | 2 | Boyd Corporation | 未上市 | US | 未上市(剔除指數) |
| G1 水冷板 / CDU / 液冷系統 | 3 | CoolIT Systems | 未上市 | CA | 未上市(剔除指數) |
| G1 水冷板 / CDU / 液冷系統 | 4 | Motivair (Schneider) | SU.PA | FR | 上市 |
| G3 快接頭 QD / 閥件 / 泵浦 | 1 | Parker Hannifin | PH (NYSE) | US | 上市 |
| G3 快接頭 QD / 閥件 / 泵浦 | 2 | Eaton | ETN (NYSE) | US | 上市 |
| G3 快接頭 QD / 閥件 / 泵浦 | 3 | CEJN | 未上市 | SE | 未上市(剔除指數) |
| G3 快接頭 QD / 閥件 / 泵浦 | 4 | Staubli | 未上市 | CH | 未上市(剔除指數) |
| H1 伺服器電源 PSU / 電源模組 | 1 | Vicor | VICR (Nasdaq) | US | 上市 |
| H1 伺服器電源 PSU / 電源模組 | 2 | Infineon | IFX.DE | DE | 上市 |
| H1 伺服器電源 PSU / 電源模組 | 3 | Monolithic Power | MPWR (Nasdaq) | US | 上市 |
| H3 重電 / 變壓器 / 開關設備 | 1 | Schneider Electric | SU.PA | FR | 上市 |
| H3 重電 / 變壓器 / 開關設備 | 2 | Eaton | ETN (NYSE) | US | 上市 |
| H3 重電 / 變壓器 / 開關設備 | 3 | Hitachi Energy | 6501.T | JP | 上市 |
| H3 重電 / 變壓器 / 開關設備 | 4 | GE Vernova | GEV (NYSE) | US | 上市 |
| I1 CPO 共封裝光學 / 光引擎 | 1 | Broadcom | AVGO (Nasdaq) | US | 上市 |
| I1 CPO 共封裝光學 / 光引擎 | 2 | Marvell | MRVL (Nasdaq) | US | 上市 |
| I1 CPO 共封裝光學 / 光引擎 | 3 | NVIDIA | NVDA (Nasdaq) | US | 上市 |
| I3 雷射源 / 三五族磊晶 | 1 | Lumentum | LITE (Nasdaq) | US | 上市 |
| I3 雷射源 / 三五族磊晶 | 2 | Coherent | COHR (NYSE) | US | 上市 |
| I3 雷射源 / 三五族磊晶 | 3 | 住友電工 | 5802.T | JP | 上市 |
| I4 光收發模組 / 光被動元件 | 1 | Coherent | COHR (NYSE) | US | 上市 |
| I4 光收發模組 / 光被動元件 | 2 | Lumentum | LITE (Nasdaq) | US | 上市 |
| I4 光收發模組 / 光被動元件 | 3 | 中際旭創 | 300308.SZ | CN | 上市 |
| I4 光收發模組 / 光被動元件 | 4 | 新易盛 | 300502.SZ | CN | 上市 |
| I5 交換器 / 白牌網通設備 | 1 | Arista | ANET (NYSE) | US | 上市 |
| I5 交換器 / 白牌網通設備 | 2 | Cisco | CSCO (Nasdaq) | US | 上市 |
| I5 交換器 / 白牌網通設備 | 3 | Celestica | CLS (NYSE) | CA | 上市 |
| J1 MLCC 積層陶瓷電容 | 1 | Murata 村田 | 6981.T | JP | 上市 |
| J1 MLCC 積層陶瓷電容 | 2 | TDK | 6762.T | JP | 上市 |
| J1 MLCC 積層陶瓷電容 | 3 | Taiyo Yuden 太陽誘電 | 6976.T | JP | 上市 |
| J1 MLCC 積層陶瓷電容 | 4 | 三星電機 SEMCO | 009150.KS | KR | 上市 |
| J3 電感 / TLVR / 磁性元件 | 1 | TDK | 6762.T | JP | 上市 |
| J3 電感 / TLVR / 磁性元件 | 2 | Murata | 6981.T | JP | 上市 |
| J3 電感 / TLVR / 磁性元件 | 3 | Vishay | VSH (NYSE) | US | 上市 |
| J4 鋁電解 / 固態電容 | 1 | Nichicon | 6996.T | JP | 上市 |
| J4 鋁電解 / 固態電容 | 2 | Rubycon | 未上市 | JP | 未上市(剔除指數) |
| J4 鋁電解 / 固態電容 | 3 | Panasonic | 6752.T | JP | 上市 |
| K1 AI PC 品牌 | 1 | Lenovo 聯想 | 0992.HK | CN | 上市 |
| K1 AI PC 品牌 | 2 | HP | HPQ (NYSE) | US | 上市 |
| K1 AI PC 品牌 | 3 | Dell | DELL (NYSE) | US | 上市 |
| K1 AI PC 品牌 | 4 | Apple | AAPL (Nasdaq) | US | 上市 |
| L8 生技醫療 | 1 | Novo Nordisk | NVO (NYSE) | DK | 上市 |
| L8 生技醫療 | 2 | Pfizer | PFE (NYSE) | US | 上市 |
| L8 生技醫療 | 3 | Merck | MRK (NYSE) | US | 上市 |
| L8 生技醫療 | 4 | Samsung Biologics | 207940.KS | KR | 上市 |
## Sheet: 40_一股多族群
| TW_TICKER | 個股 | 歸屬數 | PRIMARY | SECONDARY |
| --- | --- | --- | --- | --- |
| 2308 | 台達電 | 7 | H1 伺服器電源 PSU / 電源模組 | G1 水冷板 / CDU / 液冷系統 / G5 熱交換器 / 漏液感測 / H4 UPS / 機房基礎設施 / J8 變壓器 / PoE 磁性元件 / L4 機器人 / 自動化 / L5 電動車 / 車用零組件 |
| 2376 | 技嘉 | 4 | F1 AI OEM / ODM 整機櫃 (L10/L11) | F2 主機板 / GPU 基板 (L6) / G6 浸沒式 / 兩相散熱 / K1 AI PC 品牌 |
| 2301 | 光寶科 | 3 | H1 伺服器電源 PSU / 電源模組 | H4 UPS / 機房基礎設施 / K5 AI PC 零組件 · 電池電源 |
| 1303 | 南亞 | 3 | A1 玻纖布 / 玻纖紗 | A2 銅箔基板 CCL / A3 銅箔 / 樹脂 / 化工基材 |
| 2377 | 微星 | 3 | F2 主機板 / GPU 基板 (L6) | G6 浸沒式 / 兩相散熱 / K1 AI PC 品牌 |
| 2356 | 英業達 | 3 | F2 主機板 / GPU 基板 (L6) | F1 AI OEM / ODM 整機櫃 (L10/L11) / K2 NB / PC 代工 ODM |
| 2492 | 華新科 | 3 | J1 MLCC 積層陶瓷電容 | J2 晶片電阻 Chip Resistor / J7 LTCC / 高頻被動模組 |
| 3231 | 緯創 | 3 | F1 AI OEM / ODM 整機櫃 (L10/L11) | F2 主機板 / GPU 基板 (L6) / K2 NB / PC 代工 ODM |
| 6271 | 同欣電 | 3 | J9 被動元件材料 / 設備 | L1 光學鏡頭 / CIS / L2 低軌衛星 / 衛星通訊 |
| 8299 | 群聯 | 3 | D3 記憶體模組 / 控制 IC | E3 高速傳輸 / 介面 IC / K6 AI PC 零組件 · 記憶體模組 |
| 4958 | 臻鼎-KY | 3 | B3 AI 高速板 / HDI / 主板 PCB | B1 ABF / FC-BGA 載板 / B4 軟板 FPC |
| 3443 | 創意 | 3 | E1 AI ASIC 設計服務 | D1 HBM / 高頻寬記憶體 / E2 矽智財 IP |
| 2357 | 華碩 | 2 | K1 AI PC 品牌 | F1 AI OEM / ODM 整機櫃 (L10/L11) |
| 2317 | 鴻海 | 2 | F1 AI OEM / ODM 整機櫃 (L10/L11) | F2 主機板 / GPU 基板 (L6) |
| 2379 | 瑞昱 | 2 | E5 消費 / 網通 IC 設計 | K3 AI PC 零組件 · IC |
| 2382 | 廣達 | 2 | F1 AI OEM / ODM 整機櫃 (L10/L11) | K2 NB / PC 代工 ODM |
| 2454 | 聯發科 | 2 | E5 消費 / 網通 IC 設計 | E1 AI ASIC 設計服務 |
| 2464 | 盟立 | 2 | C2 先進封裝設備 (CoWoS / SoIC) | L4 機器人 / 自動化 |
| 2421 | 建準 | 2 | G4 風扇 / 馬達 | K4 AI PC 零組件 · 散熱機構 |
| 2449 | 京元電 | 2 | C4 封測 OSAT | D1 HBM / 高頻寬記憶體 |
| 2486 | 一詮 | 2 | G2 均熱片 / VC / 熱管 | G6 浸沒式 / 兩相散熱 |
| 2467 | 志聖 | 2 | B5 PCB 設備 / 鑽針 / 檢測 | C2 先進封裝設備 (CoWoS / SoIC) |
| 3017 | 奇鋐 | 2 | G1 水冷板 / CDU / 液冷系統 | K4 AI PC 零組件 · 散熱機構 |
| 3008 | 大立光 | 2 | L1 光學鏡頭 / CIS | I2 FAU 光纖陣列 / 精密光學耦合 |
| 2330 | 台積電 | 2 | C1 晶圓代工 | I1 CPO 共封裝光學 / 光引擎 |
| 2327 | 國巨 | 2 | J1 MLCC 積層陶瓷電容 | J2 晶片電阻 Chip Resistor |
| 1717 | 長興 | 2 | A3 銅箔 / 樹脂 / 化工基材 | A4 半導體化學品 / 光阻 / 耗材 |
| 2313 | 華通 | 2 | B2 BT 載板 / 記憶體載板 | B3 AI 高速板 / HDI / 主板 PCB |
| 3211 | 順達 | 2 | H2 BBU 備援電池模組 | K5 AI PC 零組件 · 電池電源 |
| 3189 | 景碩 | 2 | B1 ABF / FC-BGA 載板 | B2 BT 載板 / 記憶體載板 |
| 3081 | 聯亞 | 2 | I3 雷射源 / 三五族磊晶 | I4 光收發模組 / 光被動元件 |
| 3037 | 欣興 | 2 | B1 ABF / FC-BGA 載板 | B2 BT 載板 / 記憶體載板 |
| 3450 | 聯鈞 | 2 | I2 FAU 光纖陣列 / 精密光學耦合 | I3 雷射源 / 三五族磊晶 |
| 3483 | 力致 | 2 | G1 水冷板 / CDU / 液冷系統 | G6 浸沒式 / 兩相散熱 |
| 3324 | 雙鴻 | 2 | G1 水冷板 / CDU / 液冷系統 | K4 AI PC 零組件 · 散熱機構 |
| 3260 | 威剛 | 2 | D3 記憶體模組 / 控制 IC | K6 AI PC 零組件 · 記憶體模組 |
| 3661 | 世芯-KY | 2 | E1 AI ASIC 設計服務 | D1 HBM / 高頻寬記憶體 |
| 3665 | 貿聯-KY | 2 | F5 連接器 / 高速線材 / 端子 | L5 電動車 / 車用零組件 |
| 3711 | 日月光投控 | 2 | C4 封測 OSAT | I1 CPO 共封裝光學 / 光引擎 |
| 4966 | 譜瑞-KY | 2 | E3 高速傳輸 / 介面 IC | K3 AI PC 零組件 · IC |
| 4967 | 十銓 | 2 | D3 記憶體模組 / 控制 IC | K6 AI PC 零組件 · 記憶體模組 |
| 4968 | 立積 | 2 | E5 消費 / 網通 IC 設計 | K3 AI PC 零組件 · IC |
| 3583 | 辛耘 | 2 | C2 先進封裝設備 (CoWoS / SoIC) | A5 矽晶圓 / 靶材 / 研磨材 |
| 3338 | 泰碩 | 2 | G2 均熱片 / VC / 熱管 | G5 熱交換器 / 漏液感測 |
| 5289 | 宜鼎 | 2 | D3 記憶體模組 / 控制 IC | K6 AI PC 零組件 · 記憶體模組 |
| 5269 | 祥碩 | 2 | E3 高速傳輸 / 介面 IC | K3 AI PC 零組件 · IC |
| 6173 | 信昌電 | 2 | J1 MLCC 積層陶瓷電容 | J9 被動元件材料 / 設備 |
| 6121 | 新普 | 2 | K5 AI PC 零組件 · 電池電源 | H2 BBU 備援電池模組 |
| 6207 | 雷科 | 2 | B5 PCB 設備 / 鑽針 / 檢測 | J9 被動元件材料 / 設備 |
| 6275 | 元山 | 2 | G3 快接頭 QD / 閥件 / 泵浦 | G4 風扇 / 馬達 |
| 6284 | 佳邦 | 2 | J5 保護元件 | J7 LTCC / 高頻被動模組 |
| 6138 | 茂達 | 2 | E4 電源管理 IC (PMIC) | K3 AI PC 零組件 · IC |
| 6285 | 啟碁 | 2 | L2 低軌衛星 / 衛星通訊 | I5 交換器 / 白牌網通設備 |
| 6409 | 旭隼 | 2 | H4 UPS / 機房基礎設施 | H1 伺服器電源 PSU / 電源模組 |
| 6667 | 信紘科 | 2 | C3 廠務 / 無塵室 / 機電工程 | A4 半導體化學品 / 光阻 / 耗材 |
| 6591 | 動力-KY | 2 | G2 均熱片 / VC / 熱管 | K4 AI PC 零組件 · 散熱機構 |
| 6770 | 力積電 | 2 | C1 晶圓代工 | D2 DRAM / NOR / 利基記憶體 |
| 8046 | 南電 | 2 | B1 ABF / FC-BGA 載板 | B2 BT 載板 / 記憶體載板 |
| 8081 | 致新 | 2 | E4 電源管理 IC (PMIC) | K3 AI PC 零組件 · IC |
| 8383 | 千附 | 2 | C3 廠務 / 無塵室 / 機電工程 | L3 軍工航太 |
## Sheet: 50_來源覆蓋核對
| 來源 | 原族群 | 個股 | TW_TICKER | 新分類 | 狀態 | 調整 |
| --- | --- | --- | --- | --- | --- | --- |
| S1 stock_group | ABF 載板 | 欣興 | 3037 | B1 ABF / FC-BGA 載板 / B2 BT 載板 / 記憶體載板 | 已納入 | KEPT |
| S1 stock_group | ABF 載板 | 南電 | 8046 | B1 ABF / FC-BGA 載板 / B2 BT 載板 / 記憶體載板 | 已納入 | KEPT |
| S1 stock_group | ABF 載板 | 景碩 | 3189 | B1 ABF / FC-BGA 載板 / B2 BT 載板 / 記憶體載板 | 已納入 | KEPT |
| S1 stock_group | ABF 載板 | 大量 | 3167 | B5 PCB 設備 / 鑽針 / 檢測 | 已納入 | RECLASSIFIED |
| S1 stock_group | AI 伺服器 | 鴻海 | 2317 | F1 AI OEM / ODM 整機櫃 (L10/L11) / F2 主機板 / GPU 基板 (L6) | 已納入 | KEPT |
| S1 stock_group | AI 伺服器 | 廣達 | 2382 | F1 AI OEM / ODM 整機櫃 (L10/L11) / K2 NB / PC 代工 ODM | 已納入 | KEPT |
| S1 stock_group | AI 伺服器 | 緯創 | 3231 | F1 AI OEM / ODM 整機櫃 (L10/L11) / F2 主機板 / GPU 基板 (L6) / K2 NB / PC 代工 ODM | 已納入 | KEPT |
| S1 stock_group | AI 伺服器 | 緯穎 | 6669 | F1 AI OEM / ODM 整機櫃 (L10/L11) | 已納入 | KEPT |
| S1 stock_group | AI 伺服器 | 技嘉 | 2376 | F1 AI OEM / ODM 整機櫃 (L10/L11) / F2 主機板 / GPU 基板 (L6) / G6 浸沒式 / 兩相散熱 / K1 AI PC 品牌 | 已納入 | KEPT |
| S1 stock_group | AI 伺服器 | 英業達 | 2356 | F1 AI OEM / ODM 整機櫃 (L10/L11) / F2 主機板 / GPU 基板 (L6) / K2 NB / PC 代工 ODM | 已納入 | KEPT |
| S1 stock_group | AI 伺服器 | 勤誠 | 8210 | F3 機殼 / 機櫃 / 結構件 | 已納入 | RECLASSIFIED |
| S1 stock_group | ASIC 設計服務 | 世芯-KY | 3661 | D1 HBM / 高頻寬記憶體 / E1 AI ASIC 設計服務 | 已納入 | KEPT |
| S1 stock_group | ASIC 設計服務 | 創意 | 3443 | D1 HBM / 高頻寬記憶體 / E1 AI ASIC 設計服務 / E2 矽智財 IP | 已納入 | KEPT |
| S1 stock_group | ASIC 設計服務 | 智原 | 3035 | E1 AI ASIC 設計服務 | 已納入 | KEPT |
| S1 stock_group | ASIC 設計服務 | 揚智 | 2569 | E1 AI ASIC 設計服務 | 已納入 | KEPT |
| S1 stock_group | BBU 備援電池 | 新盛力 | 4931 | H2 BBU 備援電池模組 | 已納入 | KEPT |
| S1 stock_group | BBU 備援電池 | AES-KY | 6781 | H2 BBU 備援電池模組 | 已納入 | KEPT |
| S1 stock_group | BBU 備援電池 | 加百裕 | 3323 | H2 BBU 備援電池模組 | 已納入 | KEPT |
| S1 stock_group | BBU 備援電池 | 順達 | 3211 | H2 BBU 備援電池模組 / K5 AI PC 零組件 · 電池電源 | 已納入 | KEPT |
| S1 stock_group | 低軌衛星 | 昇達科 | 3491 | L2 低軌衛星 / 衛星通訊 | 已納入 | KEPT |
| S1 stock_group | 低軌衛星 | 台揚 | 2314 | L2 低軌衛星 / 衛星通訊 | 已納入 | KEPT |
| S1 stock_group | 低軌衛星 | 啟碁 | 6285 | I5 交換器 / 白牌網通設備 / L2 低軌衛星 / 衛星通訊 | 已納入 | KEPT |
| S1 stock_group | 低軌衛星 | 同欣電 | 6271 | J9 被動元件材料 / 設備 / L1 光學鏡頭 / CIS / L2 低軌衛星 / 衛星通訊 | 已納入 | KEPT |
| S1 stock_group | 光學 | 大立光 | 3008 | I2 FAU 光纖陣列 / 精密光學耦合 / L1 光學鏡頭 / CIS | 已納入 | KEPT |
| S1 stock_group | 光學 | 玉晶光 | 3406 | L1 光學鏡頭 / CIS | 已納入 | KEPT |
| S1 stock_group | 光學 | 亞光 | 3019 | L1 光學鏡頭 / CIS | 已納入 | KEPT |
| S1 stock_group | 光學 | 先進光 | 3362 | L1 光學鏡頭 / CIS | 已納入 | KEPT |
| S1 stock_group | 半導體 | 台積電 | 2330 | C1 晶圓代工 / I1 CPO 共封裝光學 / 光引擎 | 已納入 | RECLASSIFIED |
| S1 stock_group | 半導體 | 聯發科 | 2454 | E1 AI ASIC 設計服務 / E5 消費 / 網通 IC 設計 | 已納入 | RECLASSIFIED |
| S1 stock_group | 半導體 | 聯電 | 2303 | C1 晶圓代工 | 已納入 | RECLASSIFIED |
| S1 stock_group | 半導體 | 世界先進 | 5347 | C1 晶圓代工 | 已納入 | RECLASSIFIED |
| S1 stock_group | 半導體 | 力積電 | 6770 | C1 晶圓代工 / D2 DRAM / NOR / 利基記憶體 | 已納入 | RECLASSIFIED |
| S1 stock_group | 半導體 | 日月光投控 | 3711 | C4 封測 OSAT / I1 CPO 共封裝光學 / 光引擎 | 已納入 | RECLASSIFIED |
| S1 stock_group | 半導體 | 環球晶 | 6488 | A5 矽晶圓 / 靶材 / 研磨材 | 已納入 | RECLASSIFIED |
| S1 stock_group | 半導體設備 | 致茂 | 2360 | C2 先進封裝設備 (CoWoS / SoIC) | 已納入 | RECLASSIFIED |
| S1 stock_group | 半導體設備 | 家登 | 3680 | C2 先進封裝設備 (CoWoS / SoIC) | 已納入 | RECLASSIFIED |
| S1 stock_group | 半導體設備 | 辛耘 | 3583 | A5 矽晶圓 / 靶材 / 研磨材 / C2 先進封裝設備 (CoWoS / SoIC) | 已納入 | RECLASSIFIED |
| S1 stock_group | 半導體設備 | 萬潤 | 6187 | C2 先進封裝設備 (CoWoS / SoIC) | 已納入 | RECLASSIFIED |
| S1 stock_group | 半導體設備 | 志聖 | 2467 | B5 PCB 設備 / 鑽針 / 檢測 / C2 先進封裝設備 (CoWoS / SoIC) | 已納入 | RECLASSIFIED |
| S1 stock_group | 台積電擴廠 | 帆宣 | 6196 | C3 廠務 / 無塵室 / 機電工程 | 已納入 | RECLASSIFIED |
| S1 stock_group | 台積電擴廠 | 漢唐 | 2404 | C3 廠務 / 無塵室 / 機電工程 | 已納入 | RECLASSIFIED |
| S1 stock_group | 台積電擴廠 | 亞翔 | 6139 | C3 廠務 / 無塵室 / 機電工程 | 已納入 | RECLASSIFIED |
| S1 stock_group | 台積電擴廠 | 信紘科 | 6667 | A4 半導體化學品 / 光阻 / 耗材 / C3 廠務 / 無塵室 / 機電工程 | 已納入 | RECLASSIFIED |
| S1 stock_group | 台積電擴廠 | 京鼎 | 3413 | C2 先進封裝設備 (CoWoS / SoIC) | 已納入 | RECLASSIFIED |
| S1 stock_group | 台積電擴廠 | 弘塑 | 3131 | C2 先進封裝設備 (CoWoS / SoIC) | 已納入 | RECLASSIFIED |
| S1 stock_group | 散熱 | 雙鴻 | 3324 | G1 水冷板 / CDU / 液冷系統 / K4 AI PC 零組件 · 散熱機構 | 已納入 | KEPT |
| S1 stock_group | 散熱 | 奇鋐 | 3017 | G1 水冷板 / CDU / 液冷系統 / K4 AI PC 零組件 · 散熱機構 | 已納入 | KEPT |
| S1 stock_group | 散熱 | 建準 | 2421 | G4 風扇 / 馬達 / K4 AI PC 零組件 · 散熱機構 | 已納入 | KEPT |
| S1 stock_group | 散熱 | 泰碩 | 3338 | G2 均熱片 / VC / 熱管 / G5 熱交換器 / 漏液感測 | 已納入 | RECLASSIFIED |
| S1 stock_group | 散熱 | 元山 | 6275 | G3 快接頭 QD / 閥件 / 泵浦 / G4 風扇 / 馬達 | 已納入 | RECLASSIFIED |
| S1 stock_group | 散熱 | 力致 | 3483 | G1 水冷板 / CDU / 液冷系統 / G6 浸沒式 / 兩相散熱 | 已納入 | KEPT |
| S1 stock_group | 散熱 | 動力-KY | 6591 | G2 均熱片 / VC / 熱管 / K4 AI PC 零組件 · 散熱機構 | 已納入 | KEPT |
| S1 stock_group | 散熱 | 廣運 | 6125 | C3 廠務 / 無塵室 / 機電工程 | 已納入 | RECLASSIFIED |
| S1 stock_group | 散裝航運 | 慧洋-KY | 2637 | M2 散裝航運 | 已納入 | KEPT |
| S1 stock_group | 散裝航運 | 裕民 | 2606 | M2 散裝航運 | 已納入 | KEPT |
| S1 stock_group | 散裝航運 | 新興 | 2605 | M2 散裝航運 | 已納入 | KEPT |
| S1 stock_group | 散裝航運 | 四維航 | 5608 | M2 散裝航運 | 已納入 | KEPT |
| S1 stock_group | 散裝航運 | 中航 | 2612 | M2 散裝航運 | 已納入 | KEPT |
| S1 stock_group | 散裝航運 | 台航 | 2617 | M2 散裝航運 | 已納入 | KEPT |
| S1 stock_group | 散裝航運 | 正德 | 2641 | M2 散裝航運 | 已納入 | KEPT |
| S1 stock_group | 條鋼 | 豐興 | 2015 | M5 鋼鐵 · 條鋼 / 型鋼 | 已納入 | KEPT |
| S1 stock_group | 條鋼 | 東和鋼鐵 | 2006 | M5 鋼鐵 · 條鋼 / 型鋼 | 已納入 | KEPT |
| S1 stock_group | 條鋼 | 威致 | 2028 | M5 鋼鐵 · 條鋼 / 型鋼 | 已納入 | KEPT |
| S1 stock_group | 條鋼 | 春雨 | 2012 | M5 鋼鐵 · 條鋼 / 型鋼 | 已納入 | KEPT |
| S1 stock_group | 機器人 | 上銀 | 2049 | L4 機器人 / 自動化 | 已納入 | KEPT |
| S1 stock_group | 機器人 | 台達電 | 2308 | G1 水冷板 / CDU / 液冷系統 / G5 熱交換器 / 漏液感測 / H1 伺服器電源 PSU / 電源模組 / H4 UPS / 機房基礎設施 / J8 變壓器 / PoE 磁性元件 / L4 機器人 / 自動化 / L5 電動車 / 車用零組件 | 已納入 | KEPT |
| S1 stock_group | 機器人 | 所羅門 | 2359 | L4 機器人 / 自動化 | 已納入 | KEPT |
| S1 stock_group | 機器人 | 直得 | 1597 | L4 機器人 / 自動化 | 已納入 | KEPT |
| S1 stock_group | 機器人 | 亞德客-KY | 1590 | L4 機器人 / 自動化 | 已納入 | KEPT |
| S1 stock_group | 機器人 | 盟立 | 2464 | C2 先進封裝設備 (CoWoS / SoIC) / L4 機器人 / 自動化 | 已納入 | KEPT |
| S1 stock_group | 生技醫療 | 保瑞 | 6472 | L8 生技醫療 | 已納入 | KEPT |
| S1 stock_group | 生技醫療 | 藥華藥 | 6446 | L8 生技醫療 | 已納入 | KEPT |
| S1 stock_group | 生技醫療 | 美時 | 1795 | L8 生技醫療 | 已納入 | KEPT |
| S1 stock_group | 生技醫療 | 智擎 | 4162 | L8 生技醫療 | 已納入 | KEPT |
| S1 stock_group | 生技醫療 | 聯亞藥 | 6562 | L8 生技醫療 | 已納入 | KEPT |
| S1 stock_group | 矽智財 IP | 力旺 | 3529 | E2 矽智財 IP | 已納入 | KEPT |
| S1 stock_group | 矽智財 IP | 晶心科 | 6533 | E2 矽智財 IP | 已納入 | KEPT |
| S1 stock_group | 矽智財 IP | M31 | 6643 | E2 矽智財 IP | 已納入 | KEPT |
| S1 stock_group | 網通設備 | 智邦 | 2345 | I5 交換器 / 白牌網通設備 | 已納入 | KEPT |
| S1 stock_group | 網通設備 | 智易 | 3596 | I5 交換器 / 白牌網通設備 | 已納入 | KEPT |
| S1 stock_group | 網通設備 | 中磊 | 5388 | I5 交換器 / 白牌網通設備 | 已納入 | KEPT |
| S1 stock_group | 網通設備 | 明泰 | 3380 | I5 交換器 / 白牌網通設備 | 已納入 | KEPT |
| S1 stock_group | 航空 | 長榮航 | 2618 | M3 航空 | 已納入 | KEPT |
| S1 stock_group | 航空 | 華航 | 2610 | M3 航空 | 已納入 | KEPT |
| S1 stock_group | 航空 | 星宇 | 2646 | M3 航空 | 已納入 | KEPT |
| S1 stock_group | 被動元件 | 國巨 | 2327 | J1 MLCC 積層陶瓷電容 / J2 晶片電阻 Chip Resistor | 已納入 | RECLASSIFIED |
| S1 stock_group | 被動元件 | 華新科 | 2492 | J1 MLCC 積層陶瓷電容 / J2 晶片電阻 Chip Resistor / J7 LTCC / 高頻被動模組 | 已納入 | KEPT |
| S1 stock_group | 被動元件 | 禾伸堂 | 3026 | J1 MLCC 積層陶瓷電容 | 已納入 | RECLASSIFIED |
| S1 stock_group | 被動元件 | 信昌電 | 6173 | J1 MLCC 積層陶瓷電容 / J9 被動元件材料 / 設備 | 已納入 | KEPT |
| S1 stock_group | 觀光餐飲 | 雄獅 | 2731 | M7 觀光餐飲 | 已納入 | KEPT |
| S1 stock_group | 觀光餐飲 | 王品 | 2727 | M7 觀光餐飲 | 已納入 | KEPT |
| S1 stock_group | 觀光餐飲 | 瓦城 | 2729 | M7 觀光餐飲 | 已納入 | KEPT |
| S1 stock_group | 觀光餐飲 | 晶華 | 2707 | M7 觀光餐飲 | 已納入 | KEPT |
| S1 stock_group | 觀光餐飲 | 鳳凰 | 5706 | M7 觀光餐飲 | 已納入 | KEPT |
| S1 stock_group | 記憶體 | 南亞科 | 2408 | D2 DRAM / NOR / 利基記憶體 | 已納入 | KEPT |
| S1 stock_group | 記憶體 | 華邦電 | 2344 | D2 DRAM / NOR / 利基記憶體 | 已納入 | KEPT |
| S1 stock_group | 記憶體 | 旺宏 | 2337 | D2 DRAM / NOR / 利基記憶體 | 已納入 | KEPT |
| S1 stock_group | 記憶體 | 群聯 | 8299 | D3 記憶體模組 / 控制 IC / E3 高速傳輸 / 介面 IC / K6 AI PC 零組件 · 記憶體模組 | 已納入 | KEPT |
| S1 stock_group | 記憶體 | 威剛 | 3260 | D3 記憶體模組 / 控制 IC / K6 AI PC 零組件 · 記憶體模組 | 已納入 | KEPT |
| S1 stock_group | 貨櫃航運 | 長榮 | 2603 | M1 貨櫃航運 | 已納入 | KEPT |
| S1 stock_group | 貨櫃航運 | 陽明 | 2609 | M1 貨櫃航運 | 已納入 | KEPT |
| S1 stock_group | 貨櫃航運 | 萬海 | 2615 | M1 貨櫃航運 | 已納入 | KEPT |
| S1 stock_group | 資安/系統整合 | 安碁資訊 | 6690 | L6 資安 / 系統整合 | 已納入 | KEPT |
| S1 stock_group | 資安/系統整合 | 敦陽科 | 2480 | L6 資安 / 系統整合 | 已納入 | KEPT |
| S1 stock_group | 資安/系統整合 | 精誠 | 6214 | L6 資安 / 系統整合 | 已納入 | KEPT |
| S1 stock_group | 資安/系統整合 | 零壹 | 3029 | L6 資安 / 系統整合 | 已納入 | KEPT |
| S1 stock_group | 軍工航太 | 漢翔 | 2634 | L3 軍工航太 | 已納入 | KEPT |
| S1 stock_group | 軍工航太 | 雷虎 | 8033 | L3 軍工航太 | 已納入 | KEPT |
| S1 stock_group | 軍工航太 | 寶一 | 8222 | L3 軍工航太 | 已納入 | KEPT |
| S1 stock_group | 軍工航太 | 千附 | 8383 | C3 廠務 / 無塵室 / 機電工程 / L3 軍工航太 | 已納入 | KEPT |
| S1 stock_group | 重電 | 華城 | 1519 | H3 重電 / 變壓器 / 開關設備 | 已納入 | KEPT |
| S1 stock_group | 重電 | 士電 | 1503 | H3 重電 / 變壓器 / 開關設備 | 已納入 | KEPT |
| S1 stock_group | 重電 | 中興電 | 1513 | H3 重電 / 變壓器 / 開關設備 | 已納入 | KEPT |
| S1 stock_group | 重電 | 亞力 | 1514 | H3 重電 / 變壓器 / 開關設備 | 已納入 | KEPT |
| S1 stock_group | 重電 | 東元 | 1504 | H3 重電 / 變壓器 / 開關設備 | 已納入 | KEPT |
| S1 stock_group | 重電 | 大同 | 2371 | H3 重電 / 變壓器 / 開關設備 | 已納入 | KEPT |
| S1 stock_group | 金融 | 富邦金 | 2881 | M6 金融 | 已納入 | KEPT |
| S1 stock_group | 金融 | 國泰金 | 2882 | M6 金融 | 已納入 | KEPT |
| S1 stock_group | 金融 | 兆豐金 | 2886 | M6 金融 | 已納入 | KEPT |
| S1 stock_group | 金融 | 玉山金 | 2884 | M6 金融 | 已納入 | KEPT |
| S1 stock_group | 鋼鐵 | 中鋼 | 2002 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 已納入 | KEPT |
| S1 stock_group | 鋼鐵 | 中鴻 | 2014 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 已納入 | KEPT |
| S1 stock_group | 鋼鐵 | 燁輝 | 2023 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 已納入 | KEPT |
| S1 stock_group | 鋼鐵 | 官田鋼 | 2017 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 已納入 | KEPT |
| S1 stock_group | 鋼鐵 | 燁聯 | 9957 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 已納入 | KEPT |
| S1 stock_group | 鋼鐵 | 盛餘 | 2029 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 已納入 | KEPT |
| S1 stock_group | 電動車 | 貿聯-KY | 3665 | F5 連接器 / 高速線材 / 端子 / L5 電動車 / 車用零組件 | 已納入 | KEPT |
| S1 stock_group | 電動車 | 和大 | 1536 | L5 電動車 / 車用零組件 | 已納入 | KEPT |
| S1 stock_group | 電動車 | 為升 | 2231 | L5 電動車 / 車用零組件 | 已納入 | KEPT |
| S1 stock_group | 電動車 | 朋程 | 8255 | L5 電動車 / 車用零組件 | 已納入 | KEPT |
| S1 stock_group | 電源管理 | 台達電 | 2308 | G1 水冷板 / CDU / 液冷系統 / G5 熱交換器 / 漏液感測 / H1 伺服器電源 PSU / 電源模組 / H4 UPS / 機房基礎設施 / J8 變壓器 / PoE 磁性元件 / L4 機器人 / 自動化 / L5 電動車 / 車用零組件 | 已納入 | KEPT |
| S1 stock_group | 電源管理 | 光寶科 | 2301 | H1 伺服器電源 PSU / 電源模組 / H4 UPS / 機房基礎設施 / K5 AI PC 零組件 · 電池電源 | 已納入 | KEPT |
| S1 stock_group | 電源管理 | 全漢 | 3015 | H1 伺服器電源 PSU / 電源模組 | 已納入 | KEPT |
| S1 stock_group | 電源管理 | 僑威 | 5263 | H1 伺服器電源 PSU / 電源模組 | 已納入 | KEPT |
| S2 YTD輪動 | AI 伺服器 | 鴻海 | 2317 | F1 AI OEM / ODM 整機櫃 (L10/L11) / F2 主機板 / GPU 基板 (L6) | 已納入 | KEPT |
| S2 YTD輪動 | AI 伺服器 | 英業達 | 2356 | F1 AI OEM / ODM 整機櫃 (L10/L11) / F2 主機板 / GPU 基板 (L6) / K2 NB / PC 代工 ODM | 已納入 | KEPT |
| S2 YTD輪動 | AI 伺服器 | 技嘉 | 2376 | F1 AI OEM / ODM 整機櫃 (L10/L11) / F2 主機板 / GPU 基板 (L6) / G6 浸沒式 / 兩相散熱 / K1 AI PC 品牌 | 已納入 | KEPT |
| S2 YTD輪動 | AI 伺服器 | 廣達 | 2382 | F1 AI OEM / ODM 整機櫃 (L10/L11) / K2 NB / PC 代工 ODM | 已納入 | KEPT |
| S2 YTD輪動 | AI 伺服器 | 緯創 | 3231 | F1 AI OEM / ODM 整機櫃 (L10/L11) / F2 主機板 / GPU 基板 (L6) / K2 NB / PC 代工 ODM | 已納入 | KEPT |
| S2 YTD輪動 | AI 伺服器 | 緯穎 | 6669 | F1 AI OEM / ODM 整機櫃 (L10/L11) | 已納入 | KEPT |
| S2 YTD輪動 | AI 伺服器 | 勤誠 | 8210 | F3 機殼 / 機櫃 / 結構件 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 先進封裝 / CoWoS / SoIC | 華立 | 3010 | A4 半導體化學品 / 光阻 / 耗材 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 先進封裝 / CoWoS / SoIC | 聯詠 | 3034 | E5 消費 / 網通 IC 設計 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 先進封裝 / CoWoS / SoIC | 欣興 | 3037 | B1 ABF / FC-BGA 載板 / B2 BT 載板 / 記憶體載板 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 先進封裝 / CoWoS / SoIC | 大量 | 3167 | B5 PCB 設備 / 鑽針 / 檢測 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 先進封裝 / CoWoS / SoIC | 景碩 | 3189 | B1 ABF / FC-BGA 載板 / B2 BT 載板 / 記憶體載板 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 先進封裝 / CoWoS / SoIC | 精材 | 3374 | C4 封測 OSAT | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 先進封裝 / CoWoS / SoIC | 矽力 | 6415 | E4 電源管理 IC (PMIC) | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 先進封裝 / CoWoS / SoIC | 長華科 | 6548 | C4 封測 OSAT | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 先進封裝 / CoWoS / SoIC | 台特 | 8038 | Z1 待歸類 / 來源殘留 | 已納入(Z待歸類) | RECLASSIFIED |
| S2 YTD輪動 | 先進封裝 / CoWoS / SoIC | 南電 | 8046 | B1 ABF / FC-BGA 載板 / B2 BT 載板 / 記憶體載板 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | MLCC 積層陶瓷電容 | 國巨 | 2327 | J1 MLCC 積層陶瓷電容 / J2 晶片電阻 Chip Resistor | 已納入 | KEPT |
| S2 YTD輪動 | MLCC 積層陶瓷電容 | 奇力新 | 2456 | J3 電感 / TLVR / 磁性元件 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | MLCC 積層陶瓷電容 | 立隆電 | 2472 | J4 鋁電解 / 固態電容 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | MLCC 積層陶瓷電容 | 大毅 | 2478 | J2 晶片電阻 Chip Resistor | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | MLCC 積層陶瓷電容 | 華新科 | 2492 | J1 MLCC 積層陶瓷電容 / J2 晶片電阻 Chip Resistor / J7 LTCC / 高頻被動模組 | 已納入 | KEPT |
| S2 YTD輪動 | MLCC 積層陶瓷電容 | 禾伸堂 | 3026 | J1 MLCC 積層陶瓷電容 | 已納入 | KEPT |
| S2 YTD輪動 | MLCC 積層陶瓷電容 | 信昌電 | 6173 | J1 MLCC 積層陶瓷電容 / J9 被動元件材料 / 設備 | 已納入 | KEPT |
| S2 YTD輪動 | AI 半導體 / 先進製程 | 中砂 | 1560 | A5 矽晶圓 / 靶材 / 研磨材 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 半導體 / 先進製程 | 勝一 | 1773 | A4 半導體化學品 / 光阻 / 耗材 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 半導體 / 先進製程 | 台積電 | 2330 | C1 晶圓代工 / I1 CPO 共封裝光學 / 光引擎 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 半導體 / 先進製程 | 漢唐 | 2404 | C3 廠務 / 無塵室 / 機電工程 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 半導體 / 先進製程 | 盟立 | 2464 | C2 先進封裝設備 (CoWoS / SoIC) / L4 機器人 / 自動化 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 半導體 / 先進製程 | 志聖 | 2467 | B5 PCB 設備 / 鑽針 / 檢測 / C2 先進封裝設備 (CoWoS / SoIC) | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 半導體 / 先進製程 | 家登 | 3680 | C2 先進封裝設備 (CoWoS / SoIC) | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 半導體 / 先進製程 | 萬潤 | 6187 | C2 先進封裝設備 (CoWoS / SoIC) | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 半導體 / 先進製程 | 帆宣 | 6196 | C3 廠務 / 無塵室 / 機電工程 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 衛星 / 通訊 | 聯亞 | 3081 | I3 雷射源 / 三五族磊晶 / I4 光收發模組 / 光被動元件 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 衛星 / 通訊 | 波若威 | 3163 | I4 光收發模組 / 光被動元件 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 衛星 / 通訊 | 上詮 | 3363 | I2 FAU 光纖陣列 / 精密光學耦合 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 衛星 / 通訊 | 眾達-KY | 4977 | I4 光收發模組 / 光被動元件 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 衛星 / 通訊 | 華星光 | 4979 | I4 光收發模組 / 光被動元件 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 衛星 / 通訊 | 光聖 | 6442 | I4 光收發模組 / 光被動元件 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 先進封裝 / CoWoS / SoIC | 永光 | 1711 | A3 銅箔 / 樹脂 / 化工基材 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 電阻 Chip Resistor | 厚生 | 2107 | M8 傳產材料 / 其他 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 電阻 Chip Resistor | 凱美 | 2375 | J4 鋁電解 / 固態電容 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 電阻 Chip Resistor | 台慶科 | 3357 | J3 電感 / TLVR / 磁性元件 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 電阻 Chip Resistor | 光頡 | 3624 | J2 晶片電阻 Chip Resistor | 已納入 | KEPT |
| S2 YTD輪動 | 未分類 / Uncategorized | 漢民 | 6279 | C2 先進封裝設備 (CoWoS / SoIC) | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 電感 Inductor / Coil | 麗正 | 2302 | M8 傳產材料 / 其他 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 電感 Inductor / Coil | 乾坤 | 4767 | J3 電感 / TLVR / 磁性元件 | 已納入 | KEPT |
| S2 YTD輪動 | 電感 Inductor / Coil | 華容 | 5328 | J3 電感 / TLVR / 磁性元件 | 已納入 | KEPT |
| S2 YTD輪動 | ABF / BT 載板 | 華通 | 2313 | B2 BT 載板 / 記憶體載板 / B3 AI 高速板 / HDI / 主板 PCB | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | ABF / BT 載板 | 台燿 | 6274 | A2 銅箔基板 CCL | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | ABF / BT 載板 | 台虹 | 8039 | A3 銅箔 / 樹脂 / 化工基材 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 電源 / PSU / BBU | 順達 | 3211 | H2 BBU 備援電池模組 / K5 AI PC 零組件 · 電池電源 | 已納入 | KEPT |
| S2 YTD輪動 | AI 電源 / PSU / BBU | 加百裕 | 3323 | H2 BBU 備援電池模組 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 電源 / PSU / BBU | 新盛力 | 4931 | H2 BBU 備援電池模組 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 電源 / PSU / BBU | AES-KY | 6781 | H2 BBU 備援電池模組 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 晶圓材料 / Silicon / Chemicals / Targets | 美琪瑪 | 4721 | A4 半導體化學品 / 光阻 / 耗材 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 晶圓材料 / Silicon / Chemicals / Targets | 合晶 | 6182 | A5 矽晶圓 / 靶材 / 研磨材 | 已納入 | KEPT |
| S2 YTD輪動 | 晶圓材料 / Silicon / Chemicals / Targets | 環球晶 | 6488 | A5 矽晶圓 / 靶材 / 研磨材 | 已納入 | KEPT |
| S2 YTD輪動 | 鋁電解 / 鋁固態電容 | 台達電 | 2308 | G1 水冷板 / CDU / 液冷系統 / G5 熱交換器 / 漏液感測 / H1 伺服器電源 PSU / 電源模組 / H4 UPS / 機房基礎設施 / J8 變壓器 / PoE 磁性元件 / L4 機器人 / 自動化 / L5 電動車 / 車用零組件 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 鋁電解 / 鋁固態電容 | 中探針 | 6217 | C5 測試介面 / 探針卡 / 測試座 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI PCB / 高速板 | 燿華 | 2367 | B3 AI 高速板 / HDI / 主板 PCB | 已納入 | KEPT |
| S2 YTD輪動 | AI PCB / 高速板 | 金像電 | 2368 | B3 AI 高速板 / HDI / 主板 PCB | 已納入 | KEPT |
| S2 YTD輪動 | AI PCB / 高速板 | 台光電 | 2383 | A2 銅箔基板 CCL | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI PCB / 高速板 | 健鼎 | 3044 | B3 AI 高速板 / HDI / 主板 PCB | 已納入 | KEPT |
| S2 YTD輪動 | AI PCB / 高速板 | 臻鼎-KY | 4958 | B1 ABF / FC-BGA 載板 / B3 AI 高速板 / HDI / 主板 PCB / B4 軟板 FPC | 已納入 | KEPT |
| S2 YTD輪動 | 工程建置 / 廠務工程 | 士電 | 1503 | H3 重電 / 變壓器 / 開關設備 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 工程建置 / 廠務工程 | 東元 | 1504 | H3 重電 / 變壓器 / 開關設備 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 工程建置 / 廠務工程 | 中興電 | 1513 | H3 重電 / 變壓器 / 開關設備 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 工程建置 / 廠務工程 | 弘塑 | 3131 | C2 先進封裝設備 (CoWoS / SoIC) | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 工程建置 / 廠務工程 | 京鼎 | 3413 | C2 先進封裝設備 (CoWoS / SoIC) | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 工程建置 / 廠務工程 | 廣運 | 6125 | C3 廠務 / 無塵室 / 機電工程 | 已納入 | KEPT |
| S2 YTD輪動 | 工程建置 / 廠務工程 | 亞翔 | 6139 | C3 廠務 / 無塵室 / 機電工程 | 已納入 | KEPT |
| S2 YTD輪動 | 工程建置 / 廠務工程 | 信紘科 | 6667 | A4 半導體化學品 / 光阻 / 耗材 / C3 廠務 / 無塵室 / 機電工程 | 已納入 | KEPT |
| S2 YTD輪動 | 機房 / 電力 / UPS | 華城 | 1519 | H3 重電 / 變壓器 / 開關設備 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 機房 / 電力 / UPS | 聲寶 | 1604 | H3 重電 / 變壓器 / 開關設備 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 機房 / 電力 / UPS | 光寶科 | 2301 | H1 伺服器電源 PSU / 電源模組 / H4 UPS / 機房基礎設施 / K5 AI PC 零組件 · 電池電源 | 已納入 | KEPT |
| S2 YTD輪動 | AI 伺服器 | 奇鋐 | 3017 | G1 水冷板 / CDU / 液冷系統 / K4 AI PC 零組件 · 散熱機構 | 已納入 | KEPT |
| S2 YTD輪動 | AI 伺服器 | 雙鴻 | 3324 | G1 水冷板 / CDU / 液冷系統 / K4 AI PC 零組件 · 散熱機構 | 已納入 | KEPT |
| S2 YTD輪動 | AI 伺服器散熱 | 建準 | 2421 | G4 風扇 / 馬達 / K4 AI PC 零組件 · 散熱機構 | 已納入 | KEPT |
| S2 YTD輪動 | AI 伺服器散熱 | 泰碩 | 3338 | G2 均熱片 / VC / 熱管 / G5 熱交換器 / 漏液感測 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 伺服器散熱 | 力致 | 3483 | G1 水冷板 / CDU / 液冷系統 / G6 浸沒式 / 兩相散熱 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 伺服器散熱 | 元山 | 6275 | G3 快接頭 QD / 閥件 / 泵浦 / G4 風扇 / 馬達 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 伺服器散熱 | 動力-KY | 6591 | G2 均熱片 / VC / 熱管 / K4 AI PC 零組件 · 散熱機構 | 已納入 | KEPT |
| S2 YTD輪動 | RF / 天線 / 濾波器 | 台揚 | 2314 | L2 低軌衛星 / 衛星通訊 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | RF / 天線 / 濾波器 | 昇達科 | 3491 | L2 低軌衛星 / 衛星通訊 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | RF / 天線 / 濾波器 | 同欣電 | 6271 | J9 被動元件材料 / 設備 / L1 光學鏡頭 / CIS / L2 低軌衛星 / 衛星通訊 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | RF / 天線 / 濾波器 | 啟碁 | 6285 | I5 交換器 / 白牌網通設備 / L2 低軌衛星 / 衛星通訊 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 供應鏈周邊 / 物流 / 工控 | 研華 | 2395 | L7 工控 / 物流 / 供應鏈周邊 | 已納入 | KEPT |
| S2 YTD輪動 | 供應鏈周邊 / 物流 / 工控 | 台驊 | 2636 | L7 工控 / 物流 / 供應鏈周邊 | 已納入 | KEPT |
| S2 YTD輪動 | 供應鏈周邊 / 物流 / 工控 | 中菲行 | 5609 | L7 工控 / 物流 / 供應鏈周邊 | 已納入 | KEPT |
| S2 YTD輪動 | 供應鏈周邊 / 物流 / 工控 | 凌華 | 6166 | L7 工控 / 物流 / 供應鏈周邊 | 已納入 | KEPT |
| S2 YTD輪動 | 封測 OSAT | 矽品 | 2325 | C4 封測 OSAT | 已納入 | KEPT |
| S2 YTD輪動 | 封測 OSAT | 華泰 | 2329 | C4 封測 OSAT | 已納入 | KEPT |
| S2 YTD輪動 | 封測 OSAT | 日月光 | 3711 | C4 封測 OSAT / I1 CPO 共封裝光學 / 光引擎 | 已納入 | KEPT |
| S2 YTD輪動 | 封測 OSAT | 力成 | 6239 | C4 封測 OSAT | 已納入 | KEPT |
| S2 YTD輪動 | 連接器 / 端子 | 建舜電 | 3322 | F5 連接器 / 高速線材 / 端子 | 已納入 | KEPT |
| S2 YTD輪動 | 連接器 / 端子 | 凡甲 | 3526 | F5 連接器 / 高速線材 / 端子 | 已納入 | KEPT |
| S2 YTD輪動 | 連接器 / 端子 | 貿聯 | 3665 | F5 連接器 / 高速線材 / 端子 / L5 電動車 / 車用零組件 | 已納入 | KEPT |
| S2 YTD輪動 | 連接器 / 端子 | 台郡 | 6269 | B4 軟板 FPC | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 連接器 / 端子 | 佳邦 | 6284 | J5 保護元件 / J7 LTCC / 高頻被動模組 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | PCB | 欣泰 | 3024 | Z1 待歸類 / 來源殘留 | 已納入(Z待歸類) | RECLASSIFIED |
| S2 YTD輪動 | PCB | 欣銓 | 3264 | C4 封測 OSAT | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | PCB | 瀚宇博 | 5469 | B3 AI 高速板 / HDI / 主板 PCB | 已納入 | KEPT |
| S2 YTD輪動 | PCB | 欣技 | 6160 | L7 工控 / 物流 / 供應鏈周邊 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | ASIC 設計服務 | 揚智 | 2569 | E1 AI ASIC 設計服務 | 已納入 | KEPT |
| S2 YTD輪動 | ASIC 設計服務 | 智原 | 3035 | E1 AI ASIC 設計服務 | 已納入 | KEPT |
| S2 YTD輪動 | ASIC 設計服務 | 創意 | 3443 | D1 HBM / 高頻寬記憶體 / E1 AI ASIC 設計服務 / E2 矽智財 IP | 已納入 | KEPT |
| S2 YTD輪動 | ASIC 設計服務 | 世芯-KY | 3661 | D1 HBM / 高頻寬記憶體 / E1 AI ASIC 設計服務 | 已納入 | KEPT |
| S2 YTD輪動 | 未分類 / Uncategorized | 旭隼 | 6409 | H1 伺服器電源 PSU / 電源模組 / H4 UPS / 機房基礎設施 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 軟板 FPC | 旭软 | 3390 | B4 軟板 FPC | 已納入 | KEPT |
| S2 YTD輪動 | 軟板 FPC | 致伸 | 4915 | K5 AI PC 零組件 · 電池電源 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 軟板 FPC | 诚美材 | 4960 | M8 傳產材料 / 其他 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 軟板 FPC | 嘉联益 | 6153 | B4 軟板 FPC | 已納入 | KEPT |
| S2 YTD輪動 | 風扇 | 东林 | 3018 | G4 風扇 / 馬達 | 已納入 | KEPT |
| S2 YTD輪動 | 風扇 | 升阳 | 8028 | G4 風扇 / 馬達 | 已納入 | KEPT |
| S2 YTD輪動 | 機房電力系統 / Data Center Power | 大同 | 2371 | H3 重電 / 變壓器 / 開關設備 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 機房 / 機櫃整合 | 佳凌 | 4976 | L1 光學鏡頭 / CIS | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | AI 機房 / 機櫃整合 | 華孚 | 6235 | F3 機殼 / 機櫃 / 結構件 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | PCB | 联茂 | 6213 | Z1 待歸類 / 來源殘留 | 已納入(Z待歸類) | RECLASSIFIED |
| S2 YTD輪動 | 機殼散熱 / 結構件 | 乔鼎 | 3052 | F3 機殼 / 機櫃 / 結構件 | 已納入 | KEPT |
| S2 YTD輪動 | 機殼散熱 / 結構件 | 迎广 | 6117 | F3 機殼 / 機櫃 / 結構件 | 已納入 | KEPT |
| S2 YTD輪動 | 電池材料 / Chemicals / Components | 康普 | 4739 | A4 半導體化學品 / 光阻 / 耗材 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 電池模組 / 工業電池 | 立凱電 | 5227 | H2 BBU 備援電池模組 | 已納入 | KEPT |
| S2 YTD輪動 | PCB | 直得 | 1597 | L4 機器人 / 自動化 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | PCB | 南亚 | 1303 | A1 玻纖布 / 玻纖紗 / A2 銅箔基板 CCL / A3 銅箔 / 樹脂 / 化工基材 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | ASIC 設計服務 | 瑞昱 | 2379 | E5 消費 / 網通 IC 設計 / K3 AI PC 零組件 · IC | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | ASIC 設計服務 | 敦泰 | 3545 | E5 消費 / 網通 IC 設計 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 光學 | 大立光 | 3008 | I2 FAU 光纖陣列 / 精密光學耦合 / L1 光學鏡頭 / CIS | 已納入 | KEPT |
| S2 YTD輪動 | 光學 | 亞光 | 3019 | L1 光學鏡頭 / CIS | 已納入 | KEPT |
| S2 YTD輪動 | 光學 | 先進光 | 3362 | L1 光學鏡頭 / CIS | 已納入 | KEPT |
| S2 YTD輪動 | 光學 | 玉晶光 | 3406 | L1 光學鏡頭 / CIS | 已納入 | KEPT |
| S2 YTD輪動 | 半導體 | 聯電 | 2303 | C1 晶圓代工 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 半導體 | 聯發科 | 2454 | E1 AI ASIC 設計服務 / E5 消費 / 網通 IC 設計 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 半導體 | 世界先進 | 5347 | C1 晶圓代工 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 半導體 | 力積電 | 6770 | C1 晶圓代工 / D2 DRAM / NOR / 利基記憶體 | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 半導體設備 | 致茂 | 2360 | C2 先進封裝設備 (CoWoS / SoIC) | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 半導體設備 | 辛耘 | 3583 | A5 矽晶圓 / 靶材 / 研磨材 / C2 先進封裝設備 (CoWoS / SoIC) | 已納入 | RECLASSIFIED |
| S2 YTD輪動 | 散裝航運 | 新興 | 2605 | M2 散裝航運 | 已納入 | KEPT |
| S2 YTD輪動 | 散裝航運 | 裕民 | 2606 | M2 散裝航運 | 已納入 | KEPT |
| S2 YTD輪動 | 散裝航運 | 中航 | 2612 | M2 散裝航運 | 已納入 | KEPT |
| S2 YTD輪動 | 散裝航運 | 台航 | 2617 | M2 散裝航運 | 已納入 | KEPT |
| S2 YTD輪動 | 散裝航運 | 慧洋-KY | 2637 | M2 散裝航運 | 已納入 | KEPT |
| S2 YTD輪動 | 散裝航運 | 正德 | 2641 | M2 散裝航運 | 已納入 | KEPT |
| S2 YTD輪動 | 散裝航運 | 四維航 | 5608 | M2 散裝航運 | 已納入 | KEPT |
| S2 YTD輪動 | 條鋼 | 東和鋼鐵 | 2006 | M5 鋼鐵 · 條鋼 / 型鋼 | 已納入 | KEPT |
| S2 YTD輪動 | 條鋼 | 春雨 | 2012 | M5 鋼鐵 · 條鋼 / 型鋼 | 已納入 | KEPT |
| S2 YTD輪動 | 條鋼 | 豐興 | 2015 | M5 鋼鐵 · 條鋼 / 型鋼 | 已納入 | KEPT |
| S2 YTD輪動 | 條鋼 | 威致 | 2028 | M5 鋼鐵 · 條鋼 / 型鋼 | 已納入 | KEPT |
| S2 YTD輪動 | 機器人 | 亞德客-KY | 1590 | L4 機器人 / 自動化 | 已納入 | KEPT |
| S2 YTD輪動 | 機器人 | 上銀 | 2049 | L4 機器人 / 自動化 | 已納入 | KEPT |
| S2 YTD輪動 | 機器人 | 所羅門 | 2359 | L4 機器人 / 自動化 | 已納入 | KEPT |
| S2 YTD輪動 | 生技醫療 | 美時 | 1795 | L8 生技醫療 | 已納入 | KEPT |
| S2 YTD輪動 | 生技醫療 | 智擎 | 4162 | L8 生技醫療 | 已納入 | KEPT |
| S2 YTD輪動 | 生技醫療 | 藥華藥 | 6446 | L8 生技醫療 | 已納入 | KEPT |
| S2 YTD輪動 | 生技醫療 | 保瑞 | 6472 | L8 生技醫療 | 已納入 | KEPT |
| S2 YTD輪動 | 生技醫療 | 聯亞藥 | 6562 | L8 生技醫療 | 已納入 | KEPT |
| S2 YTD輪動 | 矽智財 IP | 力旺 | 3529 | E2 矽智財 IP | 已納入 | KEPT |
| S2 YTD輪動 | 矽智財 IP | 晶心科 | 6533 | E2 矽智財 IP | 已納入 | KEPT |
| S2 YTD輪動 | 矽智財 IP | M31 | 6643 | E2 矽智財 IP | 已納入 | KEPT |
| S2 YTD輪動 | 網通設備 | 智邦 | 2345 | I5 交換器 / 白牌網通設備 | 已納入 | KEPT |
| S2 YTD輪動 | 網通設備 | 明泰 | 3380 | I5 交換器 / 白牌網通設備 | 已納入 | KEPT |
| S2 YTD輪動 | 網通設備 | 智易 | 3596 | I5 交換器 / 白牌網通設備 | 已納入 | KEPT |
| S2 YTD輪動 | 網通設備 | 中磊 | 5388 | I5 交換器 / 白牌網通設備 | 已納入 | KEPT |
| S2 YTD輪動 | 航空 | 華航 | 2610 | M3 航空 | 已納入 | KEPT |
| S2 YTD輪動 | 航空 | 長榮航 | 2618 | M3 航空 | 已納入 | KEPT |
| S2 YTD輪動 | 航空 | 星宇 | 2646 | M3 航空 | 已納入 | KEPT |
| S2 YTD輪動 | 觀光餐飲 | 晶華 | 2707 | M7 觀光餐飲 | 已納入 | KEPT |
| S2 YTD輪動 | 觀光餐飲 | 王品 | 2727 | M7 觀光餐飲 | 已納入 | KEPT |
| S2 YTD輪動 | 觀光餐飲 | 瓦城 | 2729 | M7 觀光餐飲 | 已納入 | KEPT |
| S2 YTD輪動 | 觀光餐飲 | 雄獅 | 2731 | M7 觀光餐飲 | 已納入 | KEPT |
| S2 YTD輪動 | 觀光餐飲 | 鳳凰 | 5706 | M7 觀光餐飲 | 已納入 | KEPT |
| S2 YTD輪動 | 記憶體 | 旺宏 | 2337 | D2 DRAM / NOR / 利基記憶體 | 已納入 | KEPT |
| S2 YTD輪動 | 記憶體 | 華邦電 | 2344 | D2 DRAM / NOR / 利基記憶體 | 已納入 | KEPT |
| S2 YTD輪動 | 記憶體 | 南亞科 | 2408 | D2 DRAM / NOR / 利基記憶體 | 已納入 | KEPT |
| S2 YTD輪動 | 記憶體 | 威剛 | 3260 | D3 記憶體模組 / 控制 IC / K6 AI PC 零組件 · 記憶體模組 | 已納入 | KEPT |
| S2 YTD輪動 | 記憶體 | 群聯 | 8299 | D3 記憶體模組 / 控制 IC / E3 高速傳輸 / 介面 IC / K6 AI PC 零組件 · 記憶體模組 | 已納入 | KEPT |
| S2 YTD輪動 | 貨櫃航運 | 長榮 | 2603 | M1 貨櫃航運 | 已納入 | KEPT |
| S2 YTD輪動 | 貨櫃航運 | 陽明 | 2609 | M1 貨櫃航運 | 已納入 | KEPT |
| S2 YTD輪動 | 貨櫃航運 | 萬海 | 2615 | M1 貨櫃航運 | 已納入 | KEPT |
| S2 YTD輪動 | 資安 / 系統整合 | 敦陽科 | 2480 | L6 資安 / 系統整合 | 已納入 | KEPT |
| S2 YTD輪動 | 資安 / 系統整合 | 零壹 | 3029 | L6 資安 / 系統整合 | 已納入 | KEPT |
| S2 YTD輪動 | 資安 / 系統整合 | 精誠 | 6214 | L6 資安 / 系統整合 | 已納入 | KEPT |
| S2 YTD輪動 | 資安 / 系統整合 | 安碁資訊 | 6690 | L6 資安 / 系統整合 | 已納入 | KEPT |
| S2 YTD輪動 | 軍工航太 | 漢翔 | 2634 | L3 軍工航太 | 已納入 | KEPT |
| S2 YTD輪動 | 軍工航太 | 雷虎 | 8033 | L3 軍工航太 | 已納入 | KEPT |
| S2 YTD輪動 | 軍工航太 | 寶一 | 8222 | L3 軍工航太 | 已納入 | KEPT |
| S2 YTD輪動 | 軍工航太 | 千附 | 8383 | C3 廠務 / 無塵室 / 機電工程 / L3 軍工航太 | 已納入 | KEPT |
| S2 YTD輪動 | 重電 | 亞力 | 1514 | H3 重電 / 變壓器 / 開關設備 | 已納入 | KEPT |
| S2 YTD輪動 | 金融 | 富邦金 | 2881 | M6 金融 | 已納入 | KEPT |
| S2 YTD輪動 | 金融 | 國泰金 | 2882 | M6 金融 | 已納入 | KEPT |
| S2 YTD輪動 | 金融 | 玉山金 | 2884 | M6 金融 | 已納入 | KEPT |
| S2 YTD輪動 | 金融 | 兆豐金 | 2886 | M6 金融 | 已納入 | KEPT |
| S2 YTD輪動 | 鋼鐵 | 中鋼 | 2002 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 已納入 | KEPT |
| S2 YTD輪動 | 鋼鐵 | 中鴻 | 2014 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 已納入 | KEPT |
| S2 YTD輪動 | 鋼鐵 | 官田鋼 | 2017 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 已納入 | KEPT |
| S2 YTD輪動 | 鋼鐵 | 燁輝 | 2023 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 已納入 | KEPT |
| S2 YTD輪動 | 鋼鐵 | 盛餘 | 2029 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 已納入 | KEPT |
| S2 YTD輪動 | 鋼鐵 | 燁聯 | 9957 | M4 鋼鐵 · 扁鋼 / 不鏽鋼 | 已納入 | KEPT |
| S2 YTD輪動 | 電動車 | 和大 | 1536 | L5 電動車 / 車用零組件 | 已納入 | KEPT |
| S2 YTD輪動 | 電動車 | 為升 | 2231 | L5 電動車 / 車用零組件 | 已納入 | KEPT |
| S2 YTD輪動 | 電動車 | 朋程 | 8255 | L5 電動車 / 車用零組件 | 已納入 | KEPT |
| S2 YTD輪動 | 電源管理 | 全漢 | 3015 | H1 伺服器電源 PSU / 電源模組 | 已納入 | KEPT |
| S2 YTD輪動 | 電源管理 | 僑威 | 5263 | H1 伺服器電源 PSU / 電源模組 | 已納入 | KEPT |
## Sheet: 60_原檔問題清單
| 來源 | 類型 | 標的 | 說明 | 建議 |
| --- | --- | --- | --- | --- |
| S1 stock_group.xlsx | 成員缺漏 | CPO 共封裝光學 | 宣告 6 檔，實際匯出 0 檔，缺 6 檔 | 重跑匯出或補建成員 |
| S1 stock_group.xlsx | 成員缺漏 | IC設計 | 宣告 4 檔，實際匯出 0 檔，缺 4 檔 | 重跑匯出或補建成員 |
| S1 stock_group.xlsx | 成員缺漏 | PCB | 宣告 5 檔，實際匯出 0 檔，缺 5 檔 | 重跑匯出或補建成員 |
| S2 YTD報告 | 規模級距異常 | 鴻海 2317 | 被歸為 小型股 (Small Cap)，與實際市值排名矛盾（market_cap 欄位疑為亂序或非還原市值） | Method B 重算：free-float 市值百分位 × ADV20 百分位 |
| S1 stock_group.xlsx | 錯置 | 大量 3167 @ ABF 載板 | 大量為 PCB／半導體設備廠，非 ABF 載板製造 | 移至 B5 PCB 設備 |
| S1 stock_group.xlsx | 錯置 | 同欣電 6271 @ 低軌衛星 | 同欣電為陶瓷基板／感測封裝，衛星僅間接 | 主歸 J9，次歸 L2 低軌衛星 |
| S1 stock_group.xlsx | 粒度過粗 | AI 伺服器 7 檔混裝 | 整機櫃、L6 板級、機殼結構混在同一格 | 拆為 F1/F2/F3 |
| S1 stock_group.xlsx | 粒度過粗 | 散熱 8 檔混裝 | 水冷板、均熱片、風扇、泵閥混在同一格 | 拆為 G1–G6 |
| S1 stock_group.xlsx | 粒度過粗 | 被動元件 4 檔混裝 | MLCC／電阻／電感／電容未分 | 拆為 J1–J9 |
| S2 YTD報告 | 錯置 | 南亞 1303 @ PCB | 南亞為玻纖布／樹脂／CCL 上游，非 PCB 製造 | 移至 A1/A2/A3 |
| S2 YTD報告 | 錯置 | 直得 1597 @ PCB | 直得為線性傳動元件（機器人） | 移至 L4 機器人 |
| S2 YTD報告 | 錯置 | 聯詠 3034／矽力 6415 @ 先進封裝 | 兩者為 IC 設計，非封裝 | 移至 E5／E4 |
| S2 YTD報告 | 錯置 | 厚生 2107 @ 電阻 | 厚生為橡塑膠／資產股 | 移至 M8 傳產其他 |
| S2 YTD報告 | 錯置 | 麗正 2302 @ 電感 | 麗正為二極體／半導體元件 | 移至 M8 待覆核 |
| S2 YTD報告 | 錯置 | 台達電 2308 @ 鋁電解電容 | 台達電為電源／散熱／被動模組，非鋁電解電容廠 | 移至 H1／G1 |
| S2 YTD報告 | 錯置 | 奇鋐 3017／雙鴻 3324 @ AI 伺服器 | 兩者為散熱模組廠 | 移至 G1 |
| S3 對話研究 | 事實待驗 | 台達電列於矽光子 CPO | 對話原文將台達電與台積電並列為 CPO 晶圓代工，屬歸類錯誤 | 台達電歸 H1/G1，CPO 僅列 I1 台廠 |
| S3 對話研究 | 事實待驗 | 2026 年營收／毛利率／市占數字 | 來源為第三方 AI 對話彙整，未經 VDF 雙重驗算 | 一律標 P 級證據，不得進入結論層 |
| S3 對話研究 | 未上市剔除 | Boyd／CoolIT／CEJN／Isola／乾坤／Wiwynn Thailand | 未上市，無法餵 yfinance | 列 30_國際同業 並標未上市，不入指數 |