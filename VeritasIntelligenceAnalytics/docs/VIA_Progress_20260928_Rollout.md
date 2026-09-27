# VIA 進度表 · 2026-09-28 操作員裁定落地(每步一個還原點,推 GitHub 即更新)

側線 2026-09-28(主線批號由併線的手指定 L25)· 分支 `claude/vcgc-vrn-read-forward`。
操作員裁定:① 依擬建議(P1–P7 依建議順序套)② Z218 批345 正本**退役** ③ 加速器 / 網路工具 / layout 一律用**最新版**;附件(Gemini 對話)「適度採用、不大幅修正」,過時或與樹不符者不採用。

還原方法(任一步都可退):`git checkout <還原點 SHA> -- <檔>`,或整批 `git revert <該步 commit>`;不用 force、不用 Remove-Item。

| 步 | 內容 | 還原點(做之前的 HEAD) | 狀態 | 證據 |
|---|---|---|---|---|
| R0 | 起點(PR #327 已併;本分支多 3 筆紀錄 commit) | 83613315 | — | — |
| R1 | P7:`.gitattributes` 補三支原位元 sha 鎖的 `-text` | 83613315 | 完成 | `git check-attr text` 三支 unset、對照檔 unspecified |
| R2 | P1:`__future__` 橋位三支新版號(SUP_MDL749 v0115 · VDF_ENG088 v0104 · CGC_MDL180 v0101)+ P4:VRN 邏輯索引冊 build | 5cd370c2 | 完成 | MDL749 v0115 50/50 · MDL180 v0101 7/7;邏輯冊 53/53 過期 0;status SSOT 連動 BROKEN 4→0(YELLOW 7 · GREEN 5)、邏輯庫 RED→OK、VRN 系統管理 RED→STALE/NODATA |
| R3 | P2:`VIA_SYSTEM_MANAGER_v0150`(在自己的 namespace 跑 v0148 本體 + v0149 拔 TALib 鍵;模組層覆寫 OUT/TEMPLATE_OUT 生效)+ 追蹤頁 `VIA_UI_MasterControl_v0100.html` 依正主重生(test_11) | c8594d1c | 完成(容器);CI 待推送後量 | `test_master_control_contract_v0102` 容器 19 測 OK(原 4 測 setUpClass 就炸)· v0150 --selftest rc0 十檢 10/10 · v0148 與 v0150 產頁逐字同(146 族、486 個「正式名稱待治理」)|
| R4 | Z218 退役:基線冊 `immutable_b345.retired_20260928` + `CGC_MDL183_CeleritasPolicyGate_v0101`(只改 ⑤) | 6b10cc50 | 完成 | v0101 --selftest 8 檢 OK 8 · FAIL 0(原 7/1);[PS ] 基線外新缺 0;[PY ] 缺橋 91 照舊(Z223) |
