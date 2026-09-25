// uxtest_all_v0100 — U/X 統包一鍵(整編令 2026-08-18)
// 串跑全部 U/X 真瀏覽器測試腳本,誠實逐支 OK/FAIL 匯總;一支敗不斷鏈。
// 需 node+playwright+chromium;容器/工作站皆可(chromium 路徑經 PW_CHROME 覆寫)。
const { execFileSync } = require('child_process');
const path = require('path');
const SUITES = [
  'uxtest_naming_ui_visuallock_v0101.js',
  'uxtest_naming_ui_layout_v0102.js',
  'uxtest_product_suite_v0100.js',
  'uxtest_product_cgc_v0100.js',
  'uxtest_hub_visuallock_v0108.js',
];
let ok = 0, fail = 0;
console.log(`=== U/X 統包 v0100 · ${SUITES.length} 套 ===`);
for (const s of SUITES) {
  const p = path.join(__dirname, s);
  try {
    const out = execFileSync('node', [p], { encoding: 'utf8', timeout: 180000 });
    const tail = out.trim().split('\n').pop();
    console.log(`  [OK  ] ${s} · ${tail}`);
    ok++;
  } catch (e) {
    const tail = ((e.stdout || '') + (e.stderr || '')).trim().split('\n').slice(-3).join(' | ');
    console.log(`  [FAIL] ${s} · ${tail.slice(0, 160)}`);
    fail++;
  }
}
console.log(`  [計] 套件 OK ${ok} · FAIL ${fail}(誠實;一支敗不斷鏈)`);
process.exit(fail ? 1 : 0);
