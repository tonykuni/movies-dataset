# internal/ 缺檔(2026-11-06)

v0310 引擎第 110–130 行的 hard gate 要 `internal/NON_STOCK_CORE_v0200.py`(REUSE_MANIFEST_v0310:54,135 B · SHA-256 `92f53d82c2facb41e599bf730b8be524901ed5d355aaed22a73444e85dccfa27`)。
附件(engine · manifest · closeout · QA · ps1)兩次都沒帶這支;本倉、VRN-1 倉、桌機 $HOME 也沒有。它是 Story / Claim / Evidence / Guards 的核心(Claim · SourceBlock · def_extract_claims · def_profile_router …),無法用 VIA 既有模組代替。
把那支檔放進本夾(SHA 要對)後,`python engine/VIA_NON_STOCK_SUMMARIZER_ENGINE_v0310.py --selftest` 才會過 hard gate。
`reuse/vrn2/` 三支本倉已用 VIA 自己的席位轉接提供(TableRestorer 正本 · PyMuPDF + SUP_MDL743 版面 · 本地抽取式 + SUP_MDL866 NLP),SHA 自然與 manifest 不同(manifest 的是另一工作階段打包的副本),引擎的 gate 只查存在不查 SHA。
