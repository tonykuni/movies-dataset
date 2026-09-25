import assert from "node:assert/strict";
import { test } from "node:test";
import { MOTHER_INCOMING } from "./incoming-roster.ts";
import { isNonStock, matchBroker } from "./knowledge.ts";
import { packFinance, parseFilename, parseReportDate, validationRisk } from "./vrn.ts";

test("C:\\incoming 64 names: ROC date, 華南 2637, 3014TT, CTBC yyMMdd", () => {
  assert.equal(MOTHER_INCOMING.length, 64);
  assert.equal(parseReportDate("華南投顧-2637-慧洋-KY-1141202.pdf"), "2025-12-02");
  const a = parseFilename("華南投顧-2637-慧洋-KY-1141202.pdf");
  assert.equal(a.ticker, "2637");
  assert.equal(a.reportDate, "2025-12-02");
  assert.ok(/華南|HuaNan/i.test(a.broker));
  const b = parseFilename("3014TT-20231005.pdf");
  assert.equal(b.ticker, "3014");
  assert.equal(b.bloomberg, "3014 TT");
  const c = parseFilename("瑞基(4171,NR_未評等)-CTBC251208.pdf");
  assert.equal(c.ticker, "4171");
  assert.equal(c.reportDate, "2025-12-08");
  const d = parseFilename("【國泰證期研究部】神達(3706 TT)-初次評等買進(+30.4_)-大顯神威，營運騰達-20250822.pdf");
  assert.equal(d.ticker, "3706");
  assert.equal(d.reportDate, "2025-08-22");
});

test("incoming roster: stock files GREEN; 晨會／產業／早報 YELLOW not RED", () => {
  let green = 0;
  let yellow = 0;
  let red = 0;
  for (const name of MOTHER_INCOMING) {
    const p = parseFilename(name);
    const ext = name.split(".").pop() ?? "";
    const risk = validationRisk({ status: "ok", name, ext, size: 100_000 }, p);
    if (risk === "GREEN") green += 1;
    else if (risk === "YELLOW") yellow += 1;
    else red += 1;
  }
  assert.equal(red, 0);
  assert.ok(green >= 30, `green ${green}`);
  assert.ok(yellow >= 8, `yellow ${yellow}`);
  assert.ok(isNonStock("20251205兆豐晨會報告(一)-當日新聞與重要訊息評論.pdf"));
  assert.ok(matchBroker("華南投顧-2606-裕民-1141202.pdf"));
});

test("no body does not invent TSMC financials on 慧洋", () => {
  const name = "華南投顧-2637-慧洋-KY-1141202.pdf";
  const p = parseFilename(name);
  const rows = packFinance(
    {
      id: "x",
      name,
      ext: "pdf",
      size: 80_000,
      lastModified: 0,
      origin: "folder",
      skipDup: false,
      fingerprint: "incoming:x",
      status: "ok",
      stuckStep: null,
      stuckDetail: null,
      steps: {},
    },
    p,
    "ok",
  );
  assert.equal(rows.length, 0);
});
