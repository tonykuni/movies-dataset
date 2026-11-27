#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""Optional host browser verification, separate from unit tests. [VIA:ACCEL-BRIDGE]"""
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

VIEWPORTS = ((1440, 1000), (390, 844))

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--html', required=True)
    parser.add_argument('--browser', help='Optional installed Chromium executable')
    parser.add_argument('--output', required=True, help='New JSON evidence file')
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright
    results = []
    with sync_playwright() as api:
        settings = {'headless': True}
        if args.browser:
            settings['executable_path'] = args.browser
        browser = api.chromium.launch(**settings)
        try:
            for width, height in VIEWPORTS:
                page = browser.new_page(viewport={'width': width, 'height': height})
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(Path(args.html).resolve().as_uri(), wait_until='load')
                assert page.locator('#tabs button').count() == 9
                page.locator('#search').fill('Amydoc')
                assert page.locator('#tbody tr').count() == 1
                assert 'IDENTITY_UNRESOLVED' in page.locator('#tbody').inner_text()
                page.locator('#search').fill('not-a-real-tool-xyz')
                assert '目前沒有符合項目' in page.locator('#tbody').inner_text()
                for index in range(9):
                    page.locator('#tabs button').nth(index).click()
                    assert page.locator('#tabs button').nth(index).get_attribute('aria-pressed') == 'true'
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                with page.expect_download() as download:
                    page.locator('#download').click()
                assert download.value.suggested_filename == 'VCGC_Matrix_Evidence.json'
                assert not errors, errors
                results.append({'viewport': [width, height], 'status': 'PASS', 'tabs': 9, 'page_errors': errors})
                page.close()
        finally:
            browser.close()
    with Path(args.output).open('x', encoding='utf-8') as output:
        json.dump({'status': 'PASS', 'cases': results}, output, indent=2)
    print(json.dumps(results))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
