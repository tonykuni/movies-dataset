# VIA 全新電腦一條 PS v0100(操作員 2026-11-09「以全新電腦先安裝 PS 最新版本及所有工具的加速 PS 令進行安裝 … 跳出 HTML U/I … 最少參數」)

貼法:開 Windows 內建 PowerShell(不用管理員),先 `$env:VIA_NET_CONSENT = 'YES'`(同意閘只能你設),再整段貼 `VIA_FreshPC_Boot_v0100.txt` 最後那一段 `& { … }`。

| 步 | 誰做 | 說明 |
|---|---|---|
| ① PS7 + Git | winget(已有就略過) | 之後全部用 pwsh 跑 |
| ② 倉 | git clone / fetch + merge --no-ff main | 不 rebase、不動你本機提交;衝突會停在這一步 |
| ③ 降壓 + 環境總檢 + 布建 | `VIA_DesktopFourBlocks_v0100.py --blocks 1,2 --install` | ① CPU / 記憶體 / TEMP 門檻(--cpu-max 80 · --mem-min-gb 3)· ② EnvManager check → EnvGovernance run / tools / **conflicts** → 無衝突才 `tools --apply --approve`(你本令授權);有衝突停,印衝突表 |
| ④ MCP + VDF + 全景 | `--blocks 3,4,5 --mode live --jobs 5` | ④ 走 `VDF_MDL012_FetchGroups` run(先 --dry 再 live);2022-01-01 起由 ENG064 HistoryBackfill 分年段補,TEMP 斷點續跑 |
| ⑤ 工作台 | `VIA_WorkbenchLock_v0101.py all --open` | 五系統頁 + hub + api/*.json,品牌(新標誌 + icon)套用,自動開 hub |

不做的:不裝 Ponytail / OmniRoute / Graphify 以外的第三方;不設同意閘;不改 .ps1;不 push。
速度:②④ 都先 dry 再真跑,並行 5 流上限由 ① 的門檻擋;要更快不要改參數,要看 ⑤ 報告裡的瓶頸列。
