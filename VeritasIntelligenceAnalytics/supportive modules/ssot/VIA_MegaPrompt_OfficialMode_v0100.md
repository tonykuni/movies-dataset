# VIA Mega-Prompt · 公定處理模式 v0100

**登錄**:2026-08-05 由操作員指定為本對話之公定處理模式(standing directive)。
**適用**:所有子系統(VRN / VDF / VAP / VMT / 其他子專案)的修正、部署、整合、穩定化作業。
**治理**:本文件為 SSOT,只增不減;修改必升版 + changelog。三輪上限為硬性限制(避免修壞風險)。
**對應工具**:Control Tower 20 加速器面板、六步驟管線、HTML Matrix、via-* 指令集。

---

## 🟦 中文版本(最終 Mega-Prompt)

請啟動「自動沙盒測試修正系統」,並啟用全部 20 個加速器,對所有子系統(VRN / VDF / VAP / 其他子專案)執行三輪全景式分析、自動修正、自動部署、自動整合、自動穩定化流程。
同時:

* 註冊所有函式庫
* 擴充所有功能
* 整合成 Python Engine
* 生成一支 PowerShell 啟動器(不關閉、不阻塞、不卡斷)
* 自動部署所有模組、路徑、環境
* 啟動所有系統與 HTML UI
* 內建 20 個加速器
* 內建動態進度條(Dynamic Progress Bar)
* 內建動態說明(Dynamic Status Narration)

### 一、三輪全景式分析(每輪必做)

每輪必須執行:

1. 全景式分析(Panoramic Analysis)
2. 全錯誤識別(Error Identification)
3. 優化點定位(Optimization Points)
4. AST 結構分析(AST Structural Analysis)
5. SSOT 對齊檢查(SSOT Alignment)
6. 九頭龍風險偵測(Hydra Risk Detection)
7. 錯誤分類:
   * 可同時修正(Parallel-Fixable)
   * 需順序修正(Sequence-Dependent)
8. 多子系統同步檢視(Multi-Subsystem Synchronization)
9. 自動產生 HTML UI Matrix(含紅黃綠燈)
10. 動態進度條(Dynamic Progress Bar)
11. 動態說明(Dynamic Status Narration)

### 二、三輪修正策略(不得超過三輪)

**第 1 輪:全面性修正(Comprehensive Fix)**

* 修正所有 Parallel-Fixable 問題
* 避免觸碰高 Hydra 節點

**第 2 輪:順序性修正(Sequential Fix)**

* 依依賴拓撲排序逐步修正
* 每一步皆需沙盒驗證
* 高風險節點 → 產生建議,不自動修正

**第 3 輪:收尾性修正(Final Polishing)**

* 微調、格式化、刪除死碼、性能優化
* 確保系統穩定、乾淨、可維護

**限制:不得超過三輪,以避免修壞風險。**

### 三、每輪修正後必須重新執行三輪全景式分析

每次修正後必須:

* 再分析
* 再分類
* 再偵測 Hydra
* 再找優化點
* 再產生 HTML Matrix
* 再更新動態進度條
* 再更新動態說明

### 四、沙盒測試與驗證循環(每輪必做)

每次修正後執行:

```
test → debug → optimize → test → debug → consolidate → test → debug → user-test → debug → activate → test → debug
```

直到系統完全穩定。

### 五、系統啟動後仍需持續:

```
activate system → test → debug → until perfect
```

### 六、啟用全部 20 個加速器(Accelerators)

**原本 15 個加速器(完整保留)**

1. AST 精準解析
2. 多語言語意模型
3. 九頭龍風險預測
4. 依賴拓撲排序
5. 沙盒隔離執行
6. 自動修正建議生成
7. 三輪全景式分析
8. SSOT 對齊
9. 視覺化矩陣生成
10. 錯誤分類與分群
11. 性能與複雜度分析
12. 多子系統同步檢視
13. 版本差異與回滾
14. 覆蓋率與回歸檢查
15. 修正順序最佳化

**新增 5 個加速器(不會卡斷、不會阻塞、不會中斷)**

16. 動態進度條加速器(Dynamic Progress Bar Accelerator)
17. 動態說明加速器(Dynamic Status Narration Accelerator)
18. 非阻塞 PowerShell 執行加速器(Non-Blocking PowerShell Accelerator)
19. 多引擎整合加速器(Python + PowerShell + UI Accelerator)
20. 自動部署與環境初始化加速器(Auto-Deploy & Init Accelerator)

### 七、多子系統同步治理(VRN / VDF / VAP)

* 同步分析
* 同步修正
* 同步 SSOT 對齊
* 同步 Hydra 風險控管
* 同步 Matrix 視覺化
* 同步動態進度條
* 同步動態說明

### 八、輸出 HTML UI Matrix(每輪必做)

包含:

* 錯誤矩陣
* 優化矩陣
* Hydra 風險矩陣
* 依賴矩陣
* 修正順序矩陣
* 紅黃綠燈健康度
* 數量校驗
* SSOT 對照
* 多子系統比較
* 動態進度條
* 動態說明
