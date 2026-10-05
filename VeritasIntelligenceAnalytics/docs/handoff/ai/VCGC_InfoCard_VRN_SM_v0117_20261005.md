# VCGC 資訊卡 · VRN_SystemManager v0117 自測吞掉前版輸出(2026-10-05)

> L111:VCGC 不改 VRN 正本,只監控、出資訊卡。本卡交 VRN 管理員。

## 現象
- PR #468 合入 `functional modules/VRN/VRN_SystemManager_v0117.py` 後,4 個交接案收據 rc 0 但 marker 不見,轉為 EVIDENCE_INVALID(test did not prove target success):
  - `manager`(VRN-REQ007):要 `[VRN 來源入口] fail=0`
  - `vrn_engine`(VCGC-REQ117):要 `[計] VRN_SystemManager v0114 本版 6/6 · 前版 PASS`
  - `vrn_engine_params`(VCGC-REQ133):要 `[計] VRN_SystemManager v0115 本版 7/7 · 前版 PASS · 合計 PASS`
  - `vrn_outputs`(VDF-REQ017):要 `[計] VRN_SystemManager v0111 薄尾 11/11 · 前版 PASS · 合計 PASS`
- v0117 自身自測 `[計] VRN_SystemManager_v0117 自測 10/10 · PASS`,前版鏈也是 PASS(印出 `v0116 本版 6/6 · 前版 PASS · 合計 PASS`)。

## 定位
`VRN_SystemManager_v0117.py:277-280`(selftest ⑨):

```python
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    prc = PRIOR.selftest()
tail = [...][-1:]          # 只印最後一行
```

前版鏈(v0116 → … → v0111)的逐行輸出被緩衝吞掉,只留最後一行,所以各版的標記行不再出現在 stdout。功能沒壞,是證據被藏起來。

## 建議(VRN 端,出 v0118 薄尾;v0117 已發布不就地改)
- 前版自測輸出照原樣印出(不 redirect),或把緩衝內容整段印回 stdout 後再做判斷。
- 修完後 VCGC 重跑 `handoff test manager vrn_engine vrn_engine_params vrn_outputs`,收據轉回 VERIFIED。

## VCGC 不做的事
- 不改 VRN 檔(L111)。
- 不把四案的 success_marker 放寬成 v0117 那一行 —— 那會把「各版標記逐行可驗」降成「最後一行說 PASS」,證據變弱。
