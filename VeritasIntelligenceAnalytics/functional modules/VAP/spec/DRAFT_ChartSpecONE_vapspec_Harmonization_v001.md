# DRAFT · Chart Spec ONE ↔ vap_spec 細粒度併軌案 v001

**狀態:草案(review_before_apply,未生效)** · 2026-08-04

## 1. 爭點:兩套鎖並存

| 屬性 | Chart Spec ONE / UNIT03 治理基準 | vap_spec.json v1.0.0(2026-08-02,自稱唯一真相) |
|---|---|---|
| 線粗 | 1 | 1(一致) |
| 折線透明度 | (未分項,籠統 0.75) | **0.9**(line.opacity) |
| 折線下填色 | 0.75 | 0.75(areaUnderLine;有陰影時 0.5)(一致) |
| 柱面填色 | 0.75 | **0.6**(barFace)/ **0.8**(barFaceDense) |
| 事件區間陰影 | — | 0.3 |
| 另一域 | Macro Dashboard Seaborn bar 0.80(獨立域,互不覆寫) | — |

## 2. 已知不一致實例

1. **正本引擎** `via_autoplot_engine_v001.py` L343:`stroke-opacity="{FILL_OPACITY}"`(=0.75)——與 vap_spec `line.opacity=0.9` 不合;正本把「填色鎖」誤用到線條。
2. **Chart Library Builder 候選**(v0112 修補版):折線 0.9 與 vap_spec 一致,填色已由 0.4 修至 0.75(UNIT03 基準);但依 vap_spec 細則,柱面應為 0.6/0.8 而非 0.75。
3. **UNIT03 v0109–v0112 管線**的判定基準是單值 0.75——vap_spec 生效後需升級為分項判定表,否則會把「柱面 0.6(合規)」誤判 RED。

## 3. 併軌提案(擇一,待核准)

- **方案 A(vap_spec 為準,建議)**:vap_spec v1.0.x 升為唯一視覺真相;UNIT03 判定表改讀 vap_spec(線 0.9/區域 0.75/柱 0.6·0.8/事件 0.3);正本引擎 L343 修為 line.opacity;Chart Spec ONE 降格為歷史文件並註記由 vap_spec 取代。
- **方案 B(維持 0.75 單值)**:vap_spec 的 line.opacity/barFace 條目升版修訂為 0.75 對齊(違反其只增不減精神,不建議)。
- **共同前提**:Macro Dashboard Seaborn 0.80 域不受影響;任何落地修改各自獨立 hash-locked 交易 + UNIT03 迴歸測試。

## 4. 待操作員核准事項

- [ ] 選定方案 A 或 B
- [ ] 核准 UNIT03 判定表升級(單值 → 分項)
- [ ] 核准正本引擎 L343 修正(單行,hash-locked)
