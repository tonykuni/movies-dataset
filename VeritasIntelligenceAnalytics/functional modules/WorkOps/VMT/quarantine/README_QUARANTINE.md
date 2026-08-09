# 隔離區(SEND_QUARANTINED)

`VIA_BatchMailer_v001.ps1.SEND_QUARANTINED` — 2026-08-10 稽核包現場紅線掃描(ENG-036)
發現隨 VMT 併入之群發器含真實 `$mail.Send()`(Outlook COM)與 `$smtp.Send()`(Gmail SMTP),
違反永久鐵律「系統不可代為發送;.Send() 不得存在於可執行碼」。

處置:改副檔名隔離(內容一位元組未動,只增不減可回溯;非 .ps1 即不可執行=實質阻斷)。
若操作員確需群發功能,請下令建 v002 草稿版(Outlook .Display() 逐封開草稿;SMTP 路徑
無草稿概念,一律拒絕)— 未有明令前本檔維持隔離。
