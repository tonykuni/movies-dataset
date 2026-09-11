# ============================================================================
#  Invoke-VeritasCodexNexus.ps1  加掛任務（只增不減）
#  把這段貼進 $Engines 的 Governance.tasks 區塊，其餘一行都不要動。
#  原本長這樣：
#      Governance = @{
#          registry = 'GovernanceRegistry.json'
#          output   = 'GovernanceRegistry.json'
#          tasks    = [ordered]@{
#              BuildReport = @{ tool=''; args={ param($s,$o) @() } }
#          }
#      }
#  在 BuildReport 那一行「後面」插入以下兩個 task：
# ============================================================================

            InjectCeleritas = @{
                tool = 'VIA_CeleritasInjector.py'
                args = {
                    param($s, $o)
                    @(
                        '--root',      $s,
                        '--celeritas', (Join-Path $Root 'VeritasCeleritas.py'),
                        '--out',       $o,
                        '--stage',     (Join-Path $o '_celeritas_stage')
                    )
                }
            }

            InjectCeleritasCommit = @{
                tool = 'VIA_CeleritasInjector.py'
                args = {
                    param($s, $o)
                    @(
                        '--root',      $s,
                        '--celeritas', (Join-Path $Root 'VeritasCeleritas.py'),
                        '--out',       $o,
                        '--commit'
                    )
                }
            }
