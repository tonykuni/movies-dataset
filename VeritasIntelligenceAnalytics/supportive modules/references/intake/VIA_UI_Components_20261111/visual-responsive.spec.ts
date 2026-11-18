import { test, expect, type Page } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

type Viewport = { name: 'desktop' | 'laptop' | 'tablet' | 'mobile'; width: number; height: number };
type Density = {
  name: 'compact' | 'normal' | 'comfortable';
  selector: string;
  expected: number;
  active: string;
};
type PanelOverlap = {
  container: string;
  first: string;
  second: string;
  overlapX: number;
  overlapY: number;
};
type TableMetric = {
  id: string;
  rows: number;
  columns: number;
  parentOverflowX: string;
  scrollWidth: number;
  clientWidth: number;
};
type AuditMetrics = {
  title: string;
  lang: string;
  h1: number;
  main: number;
  innerWidth: number;
  documentWidth: number;
  bodyWidth: number;
  unnamedButtons: number;
  unnamedControls: number;
  fontBelow12Warnings: number;
  tables: TableMetric[];
  overlaps: PanelOverlap[];
  activeDensity: string | null;
  viewport: Viewport['name'];
  density: Density['name'];
};

const viewports: Viewport[] = [
  { name: 'desktop', width: 1920, height: 1080 },
  { name: 'laptop', width: 1440, height: 900 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'mobile', width: 390, height: 844 },
];

const densities: Density[] = [
  { name: 'compact', selector: '[data-density="compact"]', expected: 0.86, active: 'compact' },
  { name: 'normal', selector: '[data-density="balanced"]', expected: 1.00, active: 'balanced' },
  { name: 'comfortable', selector: '[data-density="comfortable"]', expected: 1.15, active: 'comfortable' },
];

// Run from VIA_HTML_UI/ui-auto-optimizer; CI writes artifacts under output/.
const outputDir = path.resolve(process.env.VIA_OPTIMIZER_OUTPUT ?? 'output');
const screenshotDir = path.join(outputDir, 'screenshots');

async function applyDensity(page: Page, viewportWidth: number, density: Density): Promise<void> {
  // Mobile/tablet settings controls live in the collapsible sidebar.
  if (viewportWidth <= 820) {
    const sidebar = page.locator('#sidebar');
    if (!(await sidebar.evaluate((el) => el.classList.contains('mobile-open')))) {
      await page.locator('#mobileMenu').click();
    }
  }

  await page.locator('[data-open-settings]').first().click();
  await page.locator('#settingsBackdrop').waitFor({ state: 'visible' });
  await page.locator(`#densityControl ${density.selector}`).click();

  const cssDensity = await page.evaluate(() =>
    Number.parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--density')),
  );
  expect(cssDensity).toBeCloseTo(density.expected, 2);

  await page.locator('#settingsBackdrop .drawer-bottom [data-close-settings]').last().click();
  if (viewportWidth <= 820) {
    const sidebar = page.locator('#sidebar');
    if (await sidebar.evaluate((el) => el.classList.contains('mobile-open'))) {
      await page.locator('#mobileMenu').click();
    }
  }
  await page.waitForTimeout(80);
}

async function auditPage(page: Page, viewport: Viewport, density: Density): Promise<AuditMetrics> {
  const metrics = await page.evaluate(() => {
    const buttons = [...document.querySelectorAll('button')];
    const controls = [...document.querySelectorAll('input,select,textarea')];
    const unnamedButtons = buttons.filter((el) =>
      !(el.getAttribute('aria-label') || el.getAttribute('title') || el.textContent?.trim()),
    );
    const unnamedControls = controls.filter((el) => {
      if (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')) return false;
      if (el.labels?.length) return false;
      return !el.id || !document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
    });
    const fontBelow12Warnings = [...document.querySelectorAll('body *')]
      .map((el) => Number.parseFloat(getComputedStyle(el).fontSize))
      .filter((size) => Number.isFinite(size) && size < 12).length;
    const tables: TableMetric[] = [...document.querySelectorAll('table')].map((table, index) => ({
      id: table.id || table.getAttribute('aria-label') || `table-${index + 1}`,
      rows: table.rows.length,
      columns: table.rows[0]?.cells.length || 0,
      parentOverflowX: getComputedStyle(table.parentElement as Element).overflowX,
      scrollWidth: table.scrollWidth,
      clientWidth: (table.parentElement as Element).clientWidth,
    }));

    const overlaps: PanelOverlap[] = [];
    for (const selector of ['#investmentDesk .investment-body', '.content-grid', '.bottom-grid']) {
      const container = document.querySelector(selector);
      if (!container) continue;
      const items = [...container.children].filter((el) => {
        const style = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
      });
      for (let i = 0; i < items.length; i += 1) {
        for (let j = i + 1; j < items.length; j += 1) {
          const a = items[i].getBoundingClientRect();
          const b = items[j].getBoundingClientRect();
          const overlapX = Math.min(a.right, b.right) - Math.max(a.left, b.left);
          const overlapY = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
          if (overlapX > 1 && overlapY > 1) {
            overlaps.push({
              container: selector,
              first: String(items[i].className),
              second: String(items[j].className),
              overlapX,
              overlapY,
            });
          }
        }
      }
    }

    return {
      title: document.title,
      lang: document.documentElement.lang,
      h1: document.querySelectorAll('h1').length,
      main: document.querySelectorAll('main').length,
      innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      bodyWidth: document.body.scrollWidth,
      unnamedButtons: unnamedButtons.length,
      unnamedControls: unnamedControls.length,
      fontBelow12Warnings,
      tables,
      overlaps,
      activeDensity: document.querySelector('#densityControl button.active')?.getAttribute('data-density') ?? null,
    };
  });

  expect(metrics.title.length).toBeGreaterThan(0);
  expect(metrics.lang).toBe('zh-Hant');
  expect(metrics.h1).toBe(1);
  expect(metrics.main).toBe(1);
  expect(metrics.documentWidth).toBeLessThanOrEqual(metrics.innerWidth + 1);
  expect(metrics.bodyWidth).toBeLessThanOrEqual(metrics.innerWidth + 1);
  expect(metrics.overlaps, `${viewport.name}/${density.name} panels must not overlap`).toEqual([]);
  expect(metrics.unnamedButtons).toBe(0);
  expect(metrics.unnamedControls).toBe(0);
  expect(metrics.activeDensity).toBe(density.active);

  for (const table of metrics.tables) {
    if (table.scrollWidth > table.clientWidth + 2) {
      expect(
        ['auto', 'scroll', 'overlay'].includes(table.parentOverflowX),
        `${table.id} overflows without a scroll wrapper`,
      ).toBeTruthy();
    }
  }
  return { ...metrics, viewport: viewport.name, density: density.name };
}

test('VIA responsive × density matrix, accessibility, visual snapshots and browser errors', async ({ page }) => {
  fs.mkdirSync(screenshotDir, { recursive: true });
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  const externalRequests: string[] = [];
  const matrix: AuditMetrics[] = [];

  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', (error) => pageErrors.push(String(error)));
  page.on('request', (request) => {
    if (new URL(request.url()).hostname !== '127.0.0.1') externalRequests.push(request.url());
  });

  // Stable timestamp prevents clocks/status labels from making screenshot snapshots flaky.
  await page.clock.install({ time: new Date('2026-01-15T10:00:00Z') });

  for (const viewport of viewports) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto('/optimized.html', { waitUntil: 'networkidle' });
    await page.waitForLoadState('networkidle');
    await page.evaluate(() => document.fonts.ready);
    await expect(page.locator('#investmentDesk')).toBeVisible();
    await expect(page.locator('#marketChart')).toBeVisible();

    for (const density of densities) {
      await applyDensity(page, viewport.width, density);
      const result = await auditPage(page, viewport, density);
      matrix.push(result);

      await page.screenshot({
        path: path.join(screenshotDir, `${viewport.name}-${density.name}.png`),
        animations: 'disabled',
      });
      if (density.name === 'normal') {
        await expect(page.locator('body')).toHaveScreenshot(`${viewport.name}-normal.png`, {
          maxDiffPixelRatio: 0.01,
        });
      }
    }
  }

  expect(externalRequests, 'optimized UI must not request remote assets').toEqual([]);
  expect(consoleErrors, 'browser console should be clean').toEqual([]);
  expect(pageErrors, 'page JavaScript errors should be absent').toEqual([]);
  expect(matrix).toHaveLength(viewports.length * densities.length);

  fs.writeFileSync(
    path.join(outputDir, 'responsive-matrix.json'),
    `${JSON.stringify({ viewports, densities, results: matrix, consoleErrors, pageErrors, externalRequests }, null, 2)}\n`,
  );
  fs.writeFileSync(
    path.join(outputDir, 'visual-report.json'),
    `${JSON.stringify({
      schema: 'VIA.UI.VISUAL.REPORT',
      screenshotCount: matrix.length,
      snapshotBaselineCount: viewports.length,
      maxDiffPixelRatio: 0.01,
      results: matrix,
    }, null, 2)}\n`,
  );
});
