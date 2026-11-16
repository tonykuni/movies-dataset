# VIA Grok Space

這個資料夾是台股晨報這次升級的登記處。倉庫裡原有的電影資料和其他模組沒有改動。

- 參數定義只有一份：`data/via/parameter-definition.json`（VIA-PAR-001）
- 計算引擎只有一個：`code/vqg/engine.ts`（VIA-ENG-001）
- 觀察清單引擎只有一個：`code/via/engine.ts`（VIA-WCH-000）
- 同步程式只有一支：`synchronizer.py`。它只讀參數、寫報價，不算指標。

編號固定。公式、參數或天數變了才把指標版本加一。舊版本不覆蓋。

```bash
python synchronizer.py
```
