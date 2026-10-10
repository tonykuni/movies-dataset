#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA MasterControl / DeckServer 零外網契約測試(b305 Codex 原件 adapt 版;批338:路徑改尾版律,原件於 intake 零觸碰)。

v0102→v0103(操作員 2026-10-10 裁定 A:VDF / VRN / VCGC 各自獨立,MasterControl 降為唯讀總覽):
  test_11 只鎖頁面骨架,不再鎖全樹盤點快照。盤點列(引擎 / 模組的說明取自各子系統文件開頭)與
  盤點數量屬各子系統自己的冊,任一子系統出新薄尾就會改字;舊版把它們併進總頁快照,
  一支子系統的薄尾就讓總測試紅(PR #518 CI 實錄:CGC_MDL156 v0113 · CGC_MDL183 v0105 · CGC_MDL257 v0102)。
  本版比對前把盤點列與數量中性化;骨架(版面 · 輸入 · 抽屜 · 安全封套 · 腳本)照舊全文嚴格比對。
  盤點本身的正確性(列數下限 · 識別碼唯一 · 退役存證)仍由 test_01 對產生器即時驗;test_24 另驗中性化
  只吃盤點區(骨架的一個字改了照樣紅)。其餘測試原樣沿用 v0102(載入前版,不複製)。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / "test_master_control_contract_v0102.py"  # 前版本體(固定前一版,不取尾版:本檔自己就是尾版)

_spec = importlib.util.spec_from_file_location("via_mc_contract_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

_PRIOR_NORMALIZE = PRIOR.normalized_generated_page

# 盤點區:各子系統冊產生的列與數量(唯一會隨子系統薄尾改字的地方)
_INVENTORY_ROW = re.compile(r'<tr data-search="[^"]*">.*?</tr>', re.S)
_STAT_COUNT = re.compile(r'(<article class="stat[^"]*"><b>)\d+(</b>)')
_ENGINE_COUNT = re.compile(r'\d+ 現役 · \d+ 存證')
_MODULE_COUNT = re.compile(r'(<span>)\d+( 個模組</span>)')


def normalized_generated_page(page: str) -> str:
    """v0102 的中性化(Plotly 分頁 · 產生時間)+ 盤點列與盤點數量中性化;骨架全文保留。"""
    page = _PRIOR_NORMALIZE(page)
    page = _INVENTORY_ROW.sub("", page)
    page = _STAT_COUNT.sub(r"\1#\2", page)
    page = _ENGINE_COUNT.sub("# 現役 · # 存證", page)
    page = _MODULE_COUNT.sub(r"\1#\2", page)
    return page


# 前版測試以模組全域名呼叫 normalized_generated_page;換掉這一個名字,其餘測試原樣沿用
PRIOR.normalized_generated_page = normalized_generated_page


class MasterControlContractTests(PRIOR.MasterControlContractTests):
    def test_24_normalization_only_touches_inventory(self):
        page = self.page
        rows = _INVENTORY_ROW.findall(page)
        self.assertGreater(len(rows), 0, "產生頁沒有盤點列:中性化規則對不上頁面")
        # 盤點列改字 → 中性化後相同(子系統薄尾不讓總覽紅)
        edited = page.replace(rows[0], rows[0].replace("</td>", "·改字</td>", 1), 1)
        self.assertNotEqual(edited, page)
        self.assertEqual(normalized_generated_page(edited), normalized_generated_page(page))
        # 骨架改字 → 中性化後仍不同(骨架照舊嚴格)
        anchor = 'class="tab-panel"'
        self.assertIn(anchor, page)
        broken = page.replace(anchor, 'class="tab-panel-x"', 1)
        self.assertNotEqual(normalized_generated_page(broken), normalized_generated_page(page))


class DeckHTTPContractTests(PRIOR.DeckHTTPContractTests):
    pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
