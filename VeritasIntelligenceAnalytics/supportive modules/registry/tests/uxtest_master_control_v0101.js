#!/usr/bin/env node
"use strict";

/**
 * VIA MasterControl / DeckServer 瀏覽器 UAT(b305 Codex 原件 adapt 版;批338 路徑改 tests/ 層;原件於 intake 零觸碰)
 *
 * 使用 Playwright bundled Chromium；本測試不啟動真 DeckServer，也不執行
 * 任何實際任務。所有 HTTP 狀態由同源 mock 提供，並驗證 POST、CSRF、
 * run_id、單通道依序佇列、失敗停止、XSS 編碼與三種 viewport。
 */

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {pathToFileURL} = require("node:url");
const {chromium} = require("playwright");

const VIA_ROOT = path.resolve(__dirname, "..", "..", "..");  // 批338:tests/ 下一層(b305 原件 adapt 版)
const PAGE_PATH = path.join(
  VIA_ROOT, "supportive modules", "ui_support", "VIA_UI_MasterControl_v0100.html"
);
const PLOTLY_PATH = path.join(
  VIA_ROOT, "supportive modules", "ui_support", "VIA_UI_StdDashboard_v0100.html"
);
const ARTIFACT_DIR = process.env.VIA_UX_ARTIFACT_DIR ||
  path.join(VIA_ROOT, "VIA_Reports", "ui_master_control_test_artifacts");
const APP_ORIGIN = "http://127.0.0.1:8765";
const APP_URL = `${APP_ORIGIN}/master`;
const CSRF_TOKEN = "contract-csrf-token-v0114";

function launchOptions() {
  const executablePath = chromium.executablePath();
  if (!fs.existsSync(executablePath)) {
    throw new Error(
      `Playwright bundled Chromium 不存在：${executablePath}。` +
      "請先執行 `npx playwright install chromium`。"
    );
  }
  return {headless: true};
}

function jsonRoute(route, payload, status = 200, extraHeaders = {}) {
  return route.fulfill({
    status,
    contentType: "application/json; charset=utf-8",
    headers: {
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
      ...extraHeaders,
    },
    body: JSON.stringify(payload),
  });
}

function injectCsrf(html) {
  const marker = /<meta\s+name=["']via-csrf["']\s+content=["']["']\s*\/?>/i;
  assert.match(html, marker, "MasterControl 必須保留空的 via-csrf meta 供橋注入");
  return html.replace(marker, `<meta name="via-csrf" content="${CSRF_TOKEN}">`);
}

class MockDeck {
  constructor(masterHtml) {
    this.masterHtml = injectCsrf(masterHtml);
    this.runEvents = [];
    this.intakeEvents = [];
    this.pingEvents = 0;
    this.rejectedMutations = [];
    this.jobs = new Map();
    this.completed = new Map();
    this.terminalPlan = new Map();
    this.nextRun = 1;
  }

  resetRuns(plan = {}) {
    this.runEvents.length = 0;
    this.jobs.clear();
    this.completed.clear();
    this.terminalPlan = new Map(Object.entries(plan));
    this.nextRun = 1;
  }

  async requestHeaders(request) {
    const headers = await request.allHeaders();
    return {
      origin: headers.origin || "",
      fetchSite: headers["sec-fetch-site"] || "",
      csrf: headers["x-via-csrf"] || "",
      contentType: headers["content-type"] || "",
    };
  }

  async validateMutation(request) {
    const headers = await this.requestHeaders(request);
    const valid = request.method() === "POST" &&
      headers.origin === APP_ORIGIN &&
      // 批338e 實錄:Playwright route 攔截下 Sec-Fetch-Site 不可見(空字串;雲端 Chromium 1194/CI 1187 同)
      // →mock 接受 ""(真樞紐仍嚴格要求 same-origin;此處只驗 Origin+CSRF+JSON)
      (headers.fetchSite === "same-origin" || headers.fetchSite === "") &&
      headers.csrf === CSRF_TOKEN &&
      headers.contentType.toLowerCase().startsWith("application/json");
    if (!valid) this.rejectedMutations.push({url: request.url(), ...headers});
    return valid;
  }

  parseBody(request) {
    try {
      const body = request.postDataJSON();
      return body && typeof body === "object" && !Array.isArray(body) ? body : null;
    } catch (_) {
      return null;
    }
  }

  static baseStatus() {
    return {
      consensus: {
        state: "fail", run_id: "historic-consensus", started: "2026-09-01 23:12:43",
        elapsed: 7, beat: 999, kb: 12, done: "0/1", pct: 0, rc: 2,
        fix: '先建立共識資料表 <img id="pwn-fix" src=x>',
        tail: '前置資料未就緒 <img id="pwn-tail" src=x onerror="window.pwned=1">',
      },
      nlp: {
        state: "ok", run_id: "historic-nlp", started: "2026-09-01 23:10:00",
        elapsed: 3, beat: 2, kb: 8, done: "1/1", pct: 100, rc: 0,
        tail: "已完成既有工作。",
      },
    };
  }

  statusPayload() {
    const status = MockDeck.baseStatus();
    for (const [task, item] of this.completed) status[task] = {...item};
    for (const [task, job] of this.jobs) {
      job.polls += 1;
      if (job.polls === 1) {
        status[task] = {
          state: "running", run_id: job.runId, started: "2026-09-01 23:20:00",
          elapsed: 1, beat: 1, kb: 1, done: "0/1", pct: 50, rc: null,
          tail: "測試工作執行中。",
        };
      } else {
        const terminal = {
          state: job.terminalState, run_id: job.runId,
          started: "2026-09-01 23:20:00", elapsed: 2, beat: 1, kb: 2,
          done: "1/1", pct: 100, rc: job.terminalState === "ok" ? 0 : 9,
          tail: job.terminalState === "ok" ? "測試工作完成。" : "測試工作失敗。",
          fix: job.terminalState === "fail" ? "停止佇列並檢查測試前置資料。" : "",
        };
        status[task] = terminal;
        job.event.terminal = true;
        this.completed.set(task, terminal);
        this.jobs.delete(task);
      }
    }
    return status;
  }

  async handle(route) {
    const request = route.request();
    const url = new URL(request.url());
    const pathname = url.pathname;

    if (pathname === "/master") {
      return route.fulfill({
        status: 200,
        contentType: "text/html; charset=utf-8",
        headers: {
          "Cache-Control": "no-store",
          "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; " +
            "style-src 'self' 'unsafe-inline'; frame-src 'self'; connect-src 'self'; " +
            "img-src 'self' data: blob:; font-src 'self' data:",
          "X-Frame-Options": "DENY",
        },
        body: this.masterHtml,
      });
    }
    if (pathname === "/favicon.ico") return route.fulfill({status: 204, body: ""});
    if (pathname === "/ping") {
      this.pingEvents += 1;
      return jsonRoute(route, {
        ok: true, via: "deck-bridge", v: "v0114-test", accel: false,
      });
    }
    if (pathname === "/status") return jsonRoute(route, this.statusPayload());
    if (pathname === "/run") {
      if (!await this.validateMutation(request)) {
        return jsonRoute(route, {ok: false, err: "CSRF 或同源檢查失敗"}, 403);
      }
      const body = this.parseBody(request);
      if (!body || !body.task) return jsonRoute(route, {ok: false, err: "封套錯誤"}, 400);
      const running = [...this.jobs.values()].some(job => !job.event.terminal);
      if (running) return jsonRoute(route, {ok: false, err: "已有工作執行中"}, 409);
      const runId = `run-contract-${String(this.nextRun++).padStart(3, "0")}`;
      const event = {
        task: String(body.task), runId, method: request.method(),
        headers: await this.requestHeaders(request), body,
        previousTerminal: this.runEvents.every(item => item.terminal), terminal: false,
      };
      this.runEvents.push(event);
      this.jobs.set(event.task, {
        runId, polls: 0, event,
        terminalState: this.terminalPlan.get(event.task) || "ok",
      });
      return jsonRoute(route, {
        ok: true,
        run_id: runId,
        accepted_params: {
          task: String(body.task || ""),
          codes: String(body.codes || ""),
          start: String(body.start || ""),
          end: String(body.end || ""),
          cats: String(body.cats || ""),
        },
      }, 202);
    }
    if (pathname === "/intake") {
      if (!await this.validateMutation(request)) {
        return jsonRoute(route, {ok: false, err: "CSRF 或同源檢查失敗"}, 403);
      }
      const body = this.parseBody(request);
      if (!body || !body.name || !body.b64) {
        return jsonRoute(route, {ok: false, err: "封套錯誤"}, 400);
      }
      this.intakeEvents.push({
        method: request.method(), headers: await this.requestHeaders(request), body,
      });
      return jsonRoute(route, {
        ok: true, saved: "mock-intake/test.txt",
        sha256: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        skip: "",
      });
    }
    if (pathname === "/VIA_UI_StdDashboard_v0100.html" && fs.existsSync(PLOTLY_PATH)) {
      return route.fulfill({
        status: 200, contentType: "text/html; charset=utf-8",
        body: fs.readFileSync(PLOTLY_PATH, "utf8"),
      });
    }
    return jsonRoute(route, {ok: false, err: "unknown endpoint"}, 404);
  }
}

async function setChecks(page, values) {
  const wanted = new Set(values);
  await page.locator("#batchChecks input").evaluateAll((inputs, selected) => {
    const wantedValues = new Set(selected);
    for (const input of inputs) {
      input.checked = wantedValues.has(input.value);
      input.dispatchEvent(new Event("change", {bubbles: true}));
    }
  }, [...wanted]);
}

async function openOwningDetails(locator) {
  await locator.evaluate(node => {
    const details = node.closest("details");
    if (details) details.open = true;
  });
}

async function geometry(page) {
  return page.evaluate(() => {
    const header = document.querySelector("#appHeader");
    const footer = document.querySelector("#appFooter");
    return {
      headerPosition: getComputedStyle(header).position,
      footerPosition: getComputedStyle(footer).position,
      headerTop: header.getBoundingClientRect().top,
      footerBottom: innerHeight - footer.getBoundingClientRect().bottom,
      overflow: document.documentElement.scrollWidth - innerWidth,
    };
  });
}

function assertFixedAndNoOverflow(value, label) {
  assert.equal(value.headerPosition, "fixed", `${label} 頁首必須固定`);
  assert.equal(value.footerPosition, "fixed", `${label} 頁尾必須固定`);
  assert.ok(Math.abs(value.headerTop) <= 1, `${label} 頁首偏移 ${value.headerTop}px`);
  assert.ok(Math.abs(value.footerBottom) <= 1, `${label} 頁尾偏移 ${value.footerBottom}px`);
  assert.ok(value.overflow <= 1, `${label} 橫向溢位 ${value.overflow}px`);
}

async function run() {
  assert.ok(fs.existsSync(PAGE_PATH), `總控頁不存在：${PAGE_PATH}`);
  fs.mkdirSync(ARTIFACT_DIR, {recursive: true});
  const sourceHtml = fs.readFileSync(PAGE_PATH, "utf8");
  const deck = new MockDeck(sourceHtml);

  let browser;
  let page;
  const pageErrors = [];
  const unexpectedRequests = [];
  try {
    browser = await chromium.launch(launchOptions());
    const context = await browser.newContext({viewport: {width: 1600, height: 900}});
    page = await context.newPage();
    page.setDefaultTimeout(10_000);
    page.setDefaultNavigationTimeout(10_000);
    page.on("pageerror", error => pageErrors.push(String(error)));
    page.on("request", request => {
      const url = new URL(request.url());
      if (!(url.protocol === "file:" || url.origin === APP_ORIGIN)) {
        unexpectedRequests.push(request.url());
      }
    });
    await page.route(`${APP_ORIGIN}/**`, route => deck.handle(route));

    await page.goto(APP_URL, {waitUntil: "load"});
    await page.waitForFunction(() =>
      document.querySelector("#bridgeState")?.textContent.includes("在線"));
    assert.equal(await page.locator('meta[name="via-csrf"]').getAttribute("content"),
      CSRF_TOKEN, "橋供應頁必須注入當次 CSRF 權杖");

    const ids = await page.locator("[id]").evaluateAll(nodes => nodes.map(node => node.id));
    assert.equal(ids.length, new Set(ids).size, "DOM id 必須唯一");
    assert.ok((await page.getByRole("button", {name: /開啟或關閉執行輸入/}).count()) === 1,
      "抽屜切換鈕必須有可存取名稱");

    const optionPairs = await page.locator("#task option").evaluateAll(options =>
      options.map(option => ({value: option.value, text: option.textContent.trim()}))
    );
    assert.ok(optionPairs.length >= 32, `任務冊應完整顯示 ≥32 項(只增不減;現 ${optionPairs.length})`);  // 批338d
    for (const option of optionPairs) {
      assert.notEqual(option.text, option.value, `不得用鍵值當主名稱：${option.value}`);
      assert.ok(!option.text.toLowerCase().startsWith(option.value.toLowerCase() + " "),
        `正式名稱不得以程式鍵開頭：${option.value}`);
    }

    const inputLocations = await page.locator(
      "#task,#codes,#dateStart,#dateEnd,#categories,#runOneButton,#runBatchButton," +
      "#pingButton,#saveParamsButton,#resetParamsButton,#drop,#filePicker," +
      "#catalogSearch,#showTechnicalIds"
    ).evaluateAll(nodes => nodes.map(node => Boolean(node.closest("#controlRail"))));
    assert.equal(inputLocations.length, 14, "14 個操作輸入都必須存在");
    assert.ok(inputLocations.every(Boolean), "操作輸入必須全部在左側控制欄");

    const pingCountBefore = deck.pingEvents;
    await Promise.all([
      page.waitForResponse(response => new URL(response.url()).pathname === "/ping"),
      page.click("#pingButton"),
    ]);
    assert.equal(deck.pingEvents, pingCountBefore + 1,
      "健康檢測按鈕必須真的呼叫同源 /ping");

    async function visible(selector) {
      return page.locator(selector).evaluate(node =>
        !node.hidden && getComputedStyle(node).display !== "none");
    }
    await page.selectOption("#task", "consensus");
    assert.equal(await visible("#codesField"), true);
    assert.equal(await visible("#dateRangeField"), false);
    await page.fill("#codes", "2330,2317");
    assert.equal((await page.locator("#summaryCodes").textContent()).trim(), "2330,2317");
    await page.selectOption("#task", "backfill");
    assert.equal(await visible("#codesField"), false);
    assert.equal(await visible("#dateRangeField"), true);
    await page.selectOption("#task", "global");
    assert.equal(await visible("#dateRangeField"), true);
    assert.equal(await visible("#categoriesField"), true);
    await page.fill("#dateStart", "2026-08-01");
    await page.fill("#dateEnd", "2026-08-31");
    await page.fill("#categories", "equity,index");
    assert.match(await page.locator("#summaryDates").textContent(), /2026-08-01.+2026-08-31/);
    assert.equal((await page.locator("#summaryCategories").textContent()).trim(), "equity,index");
    await page.selectOption("#task", "ui");
    assert.equal(await visible("#codesField"), false);
    assert.equal(await visible("#dateRangeField"), false);
    assert.equal(await visible("#categoriesField"), false);

    const openWorkspaceX = (await page.locator("#workspace").boundingBox()).x;
    await page.click("#railToggle");
    await page.waitForFunction(() => document.body.dataset.rail === "collapsed");
    await page.waitForFunction(() =>
      parseFloat(getComputedStyle(document.querySelector("#workspace")).marginLeft) < 1);
    const closedWorkspaceX = (await page.locator("#workspace").boundingBox()).x;
    assert.ok(closedWorkspaceX < openWorkspaceX, "左欄收合後主區應擴張");
    assert.equal(await page.locator("#railToggle").getAttribute("aria-expanded"), "false");
    assert.equal(await page.locator("#controlRail").evaluate(node => node.inert), true,
      "收合抽屜必須 inert");
    await page.click("#railToggle");
    await page.waitForFunction(() => document.body.dataset.rail === "open");
    await page.waitForFunction(() =>
      parseFloat(getComputedStyle(document.querySelector("#workspace")).marginLeft) > 200);

    await page.locator("#tab-overview").focus();
    await page.keyboard.press("ArrowRight");
    assert.equal(await page.locator("#tab-matrix").getAttribute("aria-selected"), "true");
    assert.equal(await page.locator("#panel-matrix").getAttribute("hidden"), null);
    assert.equal(await page.locator("[role=tab]").count(), 7);
    assert.equal(await page.locator("[role=tabpanel]").count(), 7);

    await page.waitForFunction(() =>
      document.querySelectorAll("#statusMatrixBody tr").length >= 2);
    const consensusRow = page.locator('#statusMatrixBody tr[data-task-id="consensus"]');
    assert.equal(await consensusRow.count(), 1);
    const failColor = await consensusRow.locator(".state-pill").evaluate(node =>
      getComputedStyle(node).color);
    assert.ok(!/rgba\(0, 0, 0, 0\)|transparent/.test(failColor),
      "失敗狀態色不得透明");
    assert.equal(await consensusRow.locator(".progress-fill").evaluate(node => node.style.width),
      "0%");
    const nlpRow = page.locator('#statusMatrixBody tr[data-task-id="nlp"]');
    assert.equal(await nlpRow.locator(".progress-fill").evaluate(node => node.style.width),
      "100%");
    await consensusRow.locator(".task-link").click();
    assert.match(await page.locator("#result").textContent(), /<img id="pwn-tail"/);
    assert.equal(await page.locator("#result img,#statusMatrixBody img").count(), 0,
      "API 文字不得被解析成 DOM");
    assert.equal(await page.evaluate(() => window.pwned), undefined);

    await page.click("#tab-engines");
    const engineNames = await page.locator("#engineTable tbody tr td:first-child").allTextContents();
    assert.ok(engineNames.length >= 194, `引擎清冊 ≥194(現 ${engineNames.length})`);  // 批338d 只增不減
    assert.ok(engineNames.every(name =>
      !/(?:ENG|MDL)\d+|[A-Za-z]{2,}_[A-Za-z0-9_]+/.test(name)),
    "引擎主名稱不得露出程式識別碼");
    assert.equal(await page.locator("#engineTable .tech-id").first().evaluate(node =>
      getComputedStyle(node).display), "none");
    await openOwningDetails(page.locator("#showTechnicalIds"));
    await page.check("#showTechnicalIds");
    assert.equal(await page.locator("#engineTable .tech-id").first().evaluate(node =>
      getComputedStyle(node).display), "table-cell");
    await page.click("#tab-modules");
    const moduleNames = await page.locator("#moduleTable tbody tr td:first-child").allTextContents();
    assert.ok(moduleNames.length >= 85, `模組清冊 ≥85(現 ${moduleNames.length})`);  // 批338d 只增不減
    assert.ok(moduleNames.every(name =>
      !/(?:ENG|MDL)\d+|[A-Za-z]{2,}_[A-Za-z0-9_]+/.test(name)),
    "模組主名稱不得露出程式識別碼");

    await page.click("#tab-plotly");
    assert.equal(await page.locator("#plotlyEmpty,#plotlyFrame").count(), 1,
      "Plotly 應顯示真實頁面或誠實缺料狀態");
    if (await page.locator("#plotlyEmpty").count()) {
      assert.match(await page.locator("#plotlyEmpty").textContent(), /不顯示模擬行情或假圖/);
    } else {
      assert.match(await page.locator("#plotlyFreshness").textContent(), /不等同.+資料已更新/);
    }

    // 缺 CSRF 的同源 POST 必須被橋拒絕。
    const deniedStatus = await page.evaluate(async () => {
      const response = await fetch("/run", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({task: "boot"}),
      });
      return response.status;
    });
    assert.equal(deniedStatus, 403);
    assert.equal(deck.runEvents.length, 0);

    // 收件也必須使用同源 JSON POST + CSRF。
    await openOwningDetails(page.locator("#filePicker"));
    await page.locator("#filePicker").setInputFiles({
      name: "contract-probe.txt", mimeType: "text/plain",
      buffer: Buffer.from("via-v0114-contract", "utf8"),
    });
    await page.waitForFunction(() =>
      document.querySelector("#files")?.textContent.includes("完成"));
    assert.equal(deck.intakeEvents.length, 1);
    assert.equal(deck.intakeEvents[0].method, "POST");
    assert.equal(deck.intakeEvents[0].headers.csrf, CSRF_TOKEN);
    assert.equal(deck.intakeEvents[0].body.name, "contract-probe.txt");

    // Happy queue：第二項只能在第一項同 run_id 真終態後送出。
    deck.resetRuns({boot: "ok", revenue: "ok"});
    await openOwningDetails(page.locator("#batchChecks"));
    await setChecks(page, ["boot", "revenue"]);
    await page.click("#runBatchButton");
    await page.waitForFunction(() => !document.querySelector("#runBatchButton").disabled,
      null, {timeout: 25_000});
    assert.deepEqual(deck.runEvents.map(event => event.task), ["boot", "revenue"]);
    assert.equal(deck.runEvents[0].previousTerminal, true);
    assert.equal(deck.runEvents[1].previousTerminal, true,
      "第二項只能在第一項同 run_id 進入終態後啟動");
    assert.equal(new Set(deck.runEvents.map(event => event.runId)).size, 2,
      "每次接受工作必須回傳唯一 run_id");
    assert.ok(deck.runEvents.every(event => event.method === "POST" &&
      event.headers.csrf === CSRF_TOKEN && event.body.task === event.task));
    assert.ok(deck.runEvents.every(event =>
      deck.completed.get(event.task)?.run_id === event.runId));

    // Fail-stop：第一項 fail 後不得送出第二、第三項。
    deck.resetRuns({boot: "fail", revenue: "ok", consensus: "ok"});
    await setChecks(page, ["boot", "revenue", "consensus"]);
    await page.click("#runBatchButton");
    await page.waitForFunction(() => !document.querySelector("#runBatchButton").disabled,
      null, {timeout: 20_000});
    assert.deepEqual(deck.runEvents.map(event => event.task), ["boot"],
      "任一工作失敗後佇列必須停止");
    assert.equal(deck.completed.get("boot")?.state, "fail");

    // 真捲動後仍固定頁首與頁尾；不是只檢查初始座標。
    await page.click("#tab-overview");
    await page.evaluate(() => {
      const spacer = document.createElement("div");
      spacer.id = "uat-scroll-spacer";
      spacer.style.height = "1400px";
      document.querySelector("#workspace").append(spacer);
      scrollTo(0, document.documentElement.scrollHeight);
    });
    assert.ok(await page.evaluate(() => scrollY > 0), "測試頁必須真的發生垂直捲動");
    assertFixedAndNoOverflow(await geometry(page), "桌機捲動後");
    await page.evaluate(() => {
      document.querySelector("#uat-scroll-spacer")?.remove();
      scrollTo(0, 0);
    });
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "desktop-overview.png"), fullPage: true,
    });
    await page.click("#tab-matrix");
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "desktop-matrix.png"), fullPage: true,
    });

    // 390px：drawer inert、ARIA、Escape、backdrop 與焦點回復。
    await page.setViewportSize({width: 390, height: 844});
    await page.waitForTimeout(300);
    await page.evaluate(() => window.VIA_UI.toggleRail(false, false));
    assert.equal(await page.locator("#controlRail").evaluate(node => node.inert), true);
    assert.equal(await page.locator("#controlRail").getAttribute("aria-hidden"), "true");
    assert.equal(await page.locator("#railToggle").getAttribute("aria-expanded"), "false");
    assert.equal(await page.locator("#railBackdrop").isVisible(), false);
    assertFixedAndNoOverflow(await geometry(page), "390px 收合");

    await page.click("#railToggle");
    await page.waitForFunction(() => document.body.dataset.rail === "open");
    assert.equal(await page.locator("#controlRail").evaluate(node => node.inert), false);
    assert.equal(await page.locator("#controlRail").getAttribute("aria-hidden"), "false");
    assert.equal(await page.locator("#railBackdrop").isVisible(), true);
    await page.waitForFunction(() =>
      document.querySelector("#controlRail").contains(document.activeElement));
    await page.keyboard.press("Escape");
    await page.waitForFunction(() => document.body.dataset.rail === "collapsed");
    assert.equal(await page.locator("#controlRail").evaluate(node => node.inert), true);
    assert.equal(await page.evaluate(() => document.activeElement?.id), "railToggle",
      "Escape 關閉後焦點應回到切換鈕");

    await page.click("#railToggle");
    await page.waitForFunction(() => document.body.dataset.rail === "open");
    await page.click("#railBackdrop", {position: {x: 10, y: 20}});
    await page.waitForFunction(() => document.body.dataset.rail === "collapsed");
    assert.equal(await page.locator("#controlRail").evaluate(node => node.inert), true);
    await page.click("#tab-overview");
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "mobile-390-overview.png"), fullPage: true,
    });

    // 320px 最窄支援視窗不得橫向溢位，固定殼仍有效。
    await page.setViewportSize({width: 320, height: 700});
    await page.waitForTimeout(300);
    await page.evaluate(() => window.VIA_UI.toggleRail(false, false));
    assertFixedAndNoOverflow(await geometry(page), "320px 收合");
    await page.click("#railToggle");
    await page.waitForFunction(() => document.body.dataset.rail === "open");
    assert.equal(await page.locator("#railBackdrop").isVisible(), true);
    await page.keyboard.press("Escape");
    await page.waitForFunction(() => document.body.dataset.rail === "collapsed");
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "mobile-320-overview.png"), fullPage: true,
    });

    // file:// 只能預覽：所有 mutation control 禁用，不得送出 HTTP mutation。
    const offlineContext = await browser.newContext({viewport: {width: 390, height: 844}});
    const offlinePage = await offlineContext.newPage();
    const offlineErrors = [];
    const offlineMutations = [];
    offlinePage.setDefaultTimeout(10_000);
    offlinePage.on("pageerror", error => offlineErrors.push(String(error)));
    await offlinePage.route(`${APP_ORIGIN}/**`, route => {
      if (["POST", "PUT", "PATCH", "DELETE"].includes(route.request().method())) {
        offlineMutations.push(route.request().url());
      }
      return route.abort("failed");
    });
    await offlinePage.goto(pathToFileURL(PAGE_PATH).href, {waitUntil: "load"});
    await offlinePage.waitForFunction(() => document.body.dataset.previewOnly === "true");
    for (const selector of ["#runOneButton", "#runBatchButton", "#filePicker"]) {
      assert.equal(await offlinePage.locator(selector).isDisabled(), true,
        `file:// ${selector} 必須停用`);
    }
    assert.equal(await offlinePage.locator("#drop").getAttribute("aria-disabled"), "true");
    const offlineCall = await offlinePage.evaluate(() => window.VIA_UI.callTask(
      "boot", {codes: "", start: "", end: "", cats: ""}));
    assert.equal(offlineCall.policy, true,
      "file:// 即使被程式直接呼叫執行函式，也必須由預覽政策拒絕");
    // 批338e 實錄:file:// 頁 #drop 在摺疊 details 內=視窗外→先展開+捲入再 force 點(意圖不變:預覽不得送 mutation)
    // (Playwright 對 aria-disabled 摺疊區元素 force click 仍報 outside viewport→改派發 click 事件,語意同)
    await offlinePage.locator("#drop").dispatchEvent("click");
    assert.match(await offlinePage.locator("body").textContent(), /預覽|離線/);
    assert.deepEqual(offlineMutations, [], "file:// 預覽不得送出 mutation request");
    assert.deepEqual(offlineErrors, [], `file:// 不得有未捕捉錯誤：${offlineErrors.join(" | ")}`);
    await offlineContext.close();

    assert.deepEqual(unexpectedRequests, [], "頁面不得發出 CDN 或外部請求");
    assert.deepEqual(pageErrors, [], `頁面不得有未捕捉錯誤：${pageErrors.join(" | ")}`);

    return {
      ok: true,
      page: PAGE_PATH,
      viewports: ["1600x900", "390x844", "320x700"],
      tasks: optionPairs.length,
      engines: engineNames.length,
      modules: moduleNames.length,
      happyQueue: ["boot", "revenue"],
      failStopQueue: ["boot"],
      postRunCount: deck.runEvents.length,
      intakeCount: deck.intakeEvents.length,
      pageErrors: pageErrors.length,
      externalRequests: unexpectedRequests.length,
      artifacts: ARTIFACT_DIR,
    };
  } catch (error) {
    if (page && !page.isClosed()) {
      try {
        await page.screenshot({
          path: path.join(ARTIFACT_DIR, "failure-state.png"), fullPage: true,
        });
      } catch (_) {}
    }
    throw error;
  } finally {
    if (browser) await browser.close().catch(() => {});
  }
}

run().then(result => {
  process.stdout.write(JSON.stringify(result, null, 2) + "\n");
}).catch(error => {
  process.stderr.write(`FAIL ${error.stack || error}\n`);
  process.exitCode = 1;
});
