# 批152 收容記(local_nlp_stack_upgrade)

- 來源:操作員批152 附件 `local_nlp_stack_upgrade.zip`
  (sha256 `49f654f7c3ec64753b90019b0ac4da22f49af165b9bae8161ae19605dc14b93b`,30.8KB)
- 收容:2026-08-25;12 件 byte-exact 展開 `local_nlp_stack_upgrade/`。
- 對勘批141(`VIA_KnowledgeStack_Batch141/`):三引擎檔
  (knowledge_extraction_engine / local_knowledge_engine / local_knowledge_cli)
  **byte 全同=讓位**;本包真價值=批141 缺席的 **npl_preprocessor 正主件**
  (550 行:OpenCC 簡繁+全形收斂+spaCy EntityRuler 設計)+雙測試檔
  (本環境實跑 12 passed·4 skipped=spaCy 缺誠實跳過)+研究/需求文件。
- 整合:`functional modules/VRN/VRN_ENG064_KnowledgeStack_v0101.py`
  (正主檔案級載入優先;spaCy 缺=混血[正主 Normalizer+補殼規則 NLP],
  裝 `spacy`+`zh_core_web_sm` 即自動全正主;載入敗回滾退 v0100 補殼)。
  九檢綠;VRN_ENG065 MailIntel glob 自動吃版八檢綠。原件零觸碰。
