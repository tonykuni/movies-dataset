# VIA_Workbench_Brand_v0100(工作台品牌正本:標誌 + icon 組;鎖站 v0106_4 四檔不動)

操作員 2026-11-09:「我們的 U/I 的 ICON 不像我們的 U/I 優雅 請協助增加」「LOGO … 將 Intelligence Analytics 放大 且以 Veritas 字體為主 · 不超過大生命之樹的寬度」。

- `veritas_logo_header_v0106.png`:segments.zip 四段(tree · veritas · intelligence-analytics)合成,420×384 = 鎖定 css `.brand-logo` 的 aspect-ratio,真透明。
  生命樹 = 版面寬;Veritas 照原比例(樹寬 58%);「Intelligence Analytics」以襯線字(FreeSerif · 最接近 Veritas 字形的可用字型)重排、放大到寬 = 樹寬、字高略小於 Veritas。
- `icons_v0100.json`:正本 js 的 render 契約(每 icon = [[tag, attrs], …] · viewBox 24)不變;細線 1.6 · 圓角端點 · currentColor;六個正本名(search · sliders · layers · reset · download · grid)+ 四個備用(lamp · inspect · export · filter)。
- 套用:`docs/handoff/ai/VIA_WorkbenchLock_v0101.py build`(換 base64 · 換 ICONS 字面 · 重算 CSP);`check` 驗三項。
- `sha256sum -c SHA256SUMS.txt` 要 2/2 OK;要換品牌出 v0101 夾,不原地改。
