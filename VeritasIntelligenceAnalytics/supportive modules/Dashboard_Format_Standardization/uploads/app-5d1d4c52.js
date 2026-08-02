/* ============================================================
   DRUCK // MACRO TERMINAL — Core Application
   Renders interactive terminal dashboard from pre-fetched FRED data
   ============================================================ */

// --- FRED Series Definitions ---
const SERIES = {
  liquidity: {
    FEDFUNDS: { name: "Fed Funds Rate", unit: "%", freq: "m", transform: "val" },
    M2SL: { name: "M2 Money Supply", unit: "B$", freq: "m", transform: "val" },
    WALCL: { name: "Fed Balance Sheet", unit: "M$", freq: "w", transform: "val" },
    T10Y2Y: { name: "10Y-2Y Spread", unit: "%", freq: "d", transform: "val" },
    DGS10: { name: "10Y Treasury Yield", unit: "%", freq: "d", transform: "val" },
    DGS2: { name: "2Y Treasury Yield", unit: "%", freq: "d", transform: "val" },
    BAMLH0A0HYM2: { name: "HY Credit Spread", unit: "%", freq: "d", transform: "val" },
  },
  growth: {
    GDP: { name: "Real GDP", unit: "B$", freq: "q", transform: "val" },
    A191RL1Q225SBEA: { name: "Real GDP Growth", unit: "%", freq: "q", transform: "val" },
    INDPRO: { name: "Industrial Production", unit: "idx", freq: "m", transform: "val" },
    DGORDER: { name: "Durable Goods Orders", unit: "M$", freq: "m", transform: "val" },
    RSAFS: { name: "Retail Sales", unit: "M$", freq: "m", transform: "val" },
    UMCSENT: { name: "Consumer Sentiment", unit: "idx", freq: "m", transform: "val" },
    NAPM: { name: "Manufacturing Employment", unit: "K", freq: "m", transform: "val" },
  },
  inflation: {
    CPIAUCSL: { name: "CPI (All Items)", unit: "idx", freq: "m", transform: "yoy" },
    CPILFESL: { name: "Core CPI", unit: "idx", freq: "m", transform: "yoy" },
    PCEPI: { name: "PCE Price Index", unit: "idx", freq: "m", transform: "yoy" },
    PCEPILFE: { name: "Core PCE", unit: "idx", freq: "m", transform: "yoy" },
    T10YIE: { name: "10Y Breakeven Inflation", unit: "%", freq: "d", transform: "val" },
    T5YIE: { name: "5Y Breakeven Inflation", unit: "%", freq: "d", transform: "val" },
    MICH: { name: "UMich Inflation Exp 1Y", unit: "%", freq: "m", transform: "val" },
  },
  housing: {
    PERMIT: { name: "Building Permits", unit: "K", freq: "m", transform: "val" },
    HOUST: { name: "Housing Starts", unit: "K", freq: "m", transform: "val" },
    CSUSHPINSA: { name: "Case-Shiller Home Price", unit: "idx", freq: "m", transform: "yoy" },
    MORTGAGE30US: { name: "30Y Mortgage Rate", unit: "%", freq: "w", transform: "val" },
    MSACSR: { name: "Months Supply", unit: "mo", freq: "m", transform: "val" },
    HSN1F: { name: "New Home Sales", unit: "K", freq: "m", transform: "val" },
  },
  labor: {
    UNRATE: { name: "Unemployment Rate", unit: "%", freq: "m", transform: "val" },
    PAYEMS: { name: "Nonfarm Payrolls", unit: "K", freq: "m", transform: "val" },
    ICSA: { name: "Initial Claims", unit: "K", freq: "w", transform: "val" },
    CCSA: { name: "Continuing Claims", unit: "K", freq: "w", transform: "val" },
    CES0500000003: { name: "Avg Hourly Earnings", unit: "$", freq: "m", transform: "val" },
    JTSJOL: { name: "Job Openings (JOLTS)", unit: "K", freq: "m", transform: "val" },
    CIVPART: { name: "Labor Force Participation", unit: "%", freq: "m", transform: "val" },
  },
  markets: {
    DTWEXBGS: { name: "Trade Weighted USD", unit: "idx", freq: "d", transform: "val" },
    DCOILWTICO: { name: "WTI Crude Oil", unit: "$", freq: "d", transform: "val" },
    GOLDAMGBD228NLBM: { name: "Copper Price", unit: "$/lb", freq: "m", transform: "val" },
    DEXUSEU: { name: "EUR/USD", unit: "", freq: "d", transform: "val" },
    SP500: { name: "S&P 500", unit: "idx", freq: "d", transform: "val" },
    NASDAQCOM: { name: "NASDAQ Composite", unit: "idx", freq: "d", transform: "val" },
  },
  fiscal: {
    GFDEBTN: { name: "Federal Debt Total", unit: "M$", freq: "q", transform: "val" },
    FYFSD: { name: "Federal Surplus/Deficit", unit: "M$", freq: "a", transform: "val" },
    FGEXPND: { name: "Federal Spending", unit: "B$", freq: "q", transform: "val" },
    FGRECPT: { name: "Federal Receipts", unit: "B$", freq: "q", transform: "val" },
    A091RC1Q027SBEA: { name: "Interest Payments", unit: "B$", freq: "q", transform: "val" },
    GFDEGDQ188S: { name: "Debt-to-GDP Ratio", unit: "%", freq: "q", transform: "val" },
  }
};

// --- Commentary Generators ---
const COMMENTARY = {
  liquidity: {
    title: "Druckenmiller's Liquidity Framework",
    generate(data) {
      const ffr = getLatest(data.FEDFUNDS);
      const t10y2y = getLatest(data.T10Y2Y);
      const hySpread = getLatest(data.BAMLH0A0HYM2);
      const m2 = getLatest(data.M2SL);
      const m2Prev = getPrevYear(data.M2SL);

      let html = `<p>"Earnings don't move the overall market; it's the Federal Reserve Board... focus on the central banks and focus on the movement of liquidity." — Stanley Druckenmiller</p>`;

      if (ffr) {
        const f = parseFloat(ffr.value);
        html += `<p>The <span class="highlight">Fed Funds Rate</span> stands at ${ffr.value}%, `;
        if (f > 4.5) html += `deep in restrictive territory. Druckenmiller watches for the Fed's pivot closely — rate-sensitive sectors (housing, autos, durables) lead economic weakness when rates stay elevated this long.`;
        else if (f > 2.5) html += `in moderately restrictive territory. The key question: is the Fed tightening into a slowing economy, or merely normalizing?`;
        else html += `in accommodative territory. Loose monetary policy historically fuels risk assets and economic expansion.`;
        html += `</p>`;
      }

      if (t10y2y) {
        const spread = parseFloat(t10y2y.value);
        html += `<p>The <span class="${spread < 0 ? "danger" : "highlight"}">10Y-2Y spread</span> is at ${t10y2y.value}% — `;
        if (spread < 0) html += `the curve remains inverted, a historically reliable recession signal. Druckenmiller pays close attention to yield curve dynamics as a leading indicator of economic regime change.`;
        else if (spread < 0.5) html += `nearly flat or recently un-inverted. A steepening from inversion often signals the recession is about to arrive, not that the coast is clear. This is the most dangerous phase.`;
        else html += `positively sloped. A normal curve suggests the bond market sees a stable growth trajectory ahead.`;
        html += `</p>`;
      }

      if (hySpread) {
        const hy = parseFloat(hySpread.value);
        html += `<p>High-yield credit spreads at <span class="${hy > 5 ? "danger" : hy > 3.5 ? "warn" : "highlight"}">${hySpread.value}%</span> `;
        if (hy > 5) html += `signal significant credit stress. When junk bond spreads blow out, financial conditions are tightening aggressively.`;
        else if (hy > 3.5) html += `show modest widening — not panic, but the market is pricing in some credit risk. Worth monitoring for acceleration.`;
        else html += `remain tight, suggesting risk appetite is healthy and financial conditions are loose — favorable for equities.`;
        html += `</p>`;
      }

      if (m2 && m2Prev) {
        // Use raw observation values for YoY calculation
        const m2Curr = data.M2SL?.observations?.[0]?.value || parseFloat(m2.value);
        const m2Yr = data.M2SL?.observations?.[12]?.value || parseFloat(m2Prev.value);
        const m2Chg = ((m2Curr - m2Yr) / m2Yr * 100).toFixed(1);
        html += `<p>M2 money supply has moved <span class="${parseFloat(m2Chg) < 0 ? "danger" : "highlight"}">${m2Chg}% YoY</span>. `;
        if (parseFloat(m2Chg) < -2) html += `Monetary contraction of this magnitude is historically rare and deeply deflationary. "I use liquidity" — and this liquidity backdrop is hostile.`;
        else if (parseFloat(m2Chg) < 2) html += `Growth is subdued. The Fed's QT program continues to drain reserves, keeping liquidity constrained.`;
        else html += `Money supply is expanding again, providing a tailwind for risk assets and economic activity.`;
        html += `</p>`;
      }

      return html;
    }
  },

  growth: {
    title: "Economic Cycle Assessment",
    generate(data) {
      const gdpGrowth = getLatest(data.A191RL1Q225SBEA);
      const sentiment = getLatest(data.UMCSENT);
      const durables = getLatest(data.DGORDER);
      const retail = getLatest(data.RSAFS);

      let html = `<p>"The most important thing is having the right liquidity framework and understanding where we are in the economic cycle." — Druckenmiller</p>`;

      if (gdpGrowth) {
        const g = parseFloat(gdpGrowth.value);
        html += `<p>Real GDP growth came in at <span class="${g < 0 ? "danger" : g < 1.5 ? "warn" : "highlight"}">${gdpGrowth.value}%</span> (annualized). `;
        if (g < 0) html += `The economy is contracting. Druckenmiller's regime change detection would be on high alert.`;
        else if (g < 1.5) html += `Below-trend growth suggests the cycle is maturing. The question is whether this decelerates further.`;
        else if (g > 3) html += `Strong growth, but Druckenmiller would ask: is this priced in? And does it reignite inflation?`;
        else html += `Trend-like growth — the Goldilocks zone.`;
        html += `</p>`;
      }

      if (sentiment) {
        const s = parseFloat(sentiment.value);
        html += `<p>Consumer sentiment is at <span class="${s < 60 ? "danger" : s < 80 ? "warn" : "highlight"}">${sentiment.value}</span>. `;
        if (s < 60) html += `Deeply depressed confidence historically precedes pullbacks in spending, especially on big-ticket items — exactly the leading indicators Druckenmiller monitors.`;
        else if (s < 80) html += `Below average but not crisis-level. Consumers are cautious but still spending.`;
        else html += `Healthy confidence supports the consumer spending that drives ~70% of GDP.`;
        html += `</p>`;
      }

      if (durables) {
        const dRaw = data.DGORDER?.observations?.[0]?.value || parseFloat(durables.value);
        const dVal = typeof dRaw === 'number' ? dRaw : parseFloat(dRaw);
        html += `<p>Durable goods orders — one of Druckenmiller's three key leading indicators alongside housing and autos — stand at <span class="highlight">$${(dVal / 1000).toFixed(0)}B</span>. These big-ticket, interest-rate-sensitive purchases are the canary in the coal mine for economic turning points.</p>`;
      }

      if (retail) {
        const rRaw = data.RSAFS?.observations?.[0]?.value || parseFloat(retail.value);
        const rVal = typeof rRaw === 'number' ? rRaw : parseFloat(rRaw);
        html += `<p>Retail sales at <span class="highlight">$${(rVal / 1000).toFixed(0)}B</span>. The consumer remains the engine of the US economy. Watch for divergence between headline retail and real (inflation-adjusted) spending.</p>`;
      }

      return html;
    }
  },

  inflation: {
    title: "Inflation Regime Analysis",
    generate(data) {
      const corePce = getLatest(data.PCEPILFE);
      const breakeven10 = getLatest(data.T10YIE);
      const umichExp = getLatest(data.MICH);
      const coreCpi = getLatest(data.CPILFESL);

      let html = `<p>Druckenmiller has warned that the Fed "declared victory too early" on inflation. He watches for regime shifts — a sustained move above or below the Fed's 2% target signals a new macro environment.</p>`;

      if (corePce) {
        const pce = parseFloat(corePce.value);
        html += `<p>Core PCE — the Fed's preferred gauge — is running at <span class="${pce > 3 ? "danger" : pce > 2.5 ? "warn" : "highlight"}">${corePce.value}% YoY</span>. `;
        if (pce > 3) html += `Well above target. If the Fed needs to tighten further, it creates a headwind for risk assets.`;
        else if (pce > 2.5) html += `Still sticky above target. The last mile of disinflation is proving difficult — services inflation remains persistent.`;
        else if (pce > 2) html += `Approaching the 2% target but not quite there. The trajectory matters more than the level.`;
        else html += `At or below target, giving the Fed room to ease if growth weakens.`;
        html += `</p>`;
      }

      if (breakeven10) {
        const be = parseFloat(breakeven10.value);
        html += `<p>Market-based inflation expectations (10Y breakeven) at <span class="${be > 2.8 ? "warn" : "highlight"}">${breakeven10.value}%</span>. `;
        if (be > 2.8) html += `Elevated — the bond market is pricing in persistent inflation.`;
        else if (be > 2.2) html += `Anchored near the Fed's target range, suggesting bond market trust in the disinflationary trajectory.`;
        else html += `Subdued, suggesting deflationary risks may be emerging.`;
        html += `</p>`;
      }

      if (umichExp) {
        const ue = parseFloat(umichExp.value);
        html += `<p>Consumer inflation expectations (UMich 1Y) at <span class="${ue > 4 ? "warn" : "highlight"}">${umichExp.value}%</span>. `;
        if (ue > 4) html += `De-anchoring expectations is the Fed's nightmare — if consumers expect higher prices, they demand higher wages, creating a self-fulfilling spiral.`;
        else html += `Expectations remain contained, supporting the disinflationary narrative.`;
        html += `</p>`;
      }

      return html;
    }
  },

  housing: {
    title: "Housing — The Lead Indicator",
    generate(data) {
      const permits = getLatest(data.PERMIT);
      const mortgage = getLatest(data.MORTGAGE30US);
      const caseShiller = getLatest(data.CSUSHPINSA);
      const supply = getLatest(data.MSACSR);

      let html = `<p>"Housing, auto sales, and durable goods consumption are the three main indicators that lead an economic cycle" — this framework, central to Druckenmiller's approach, stems from their shared sensitivity to interest rates.</p>`;

      if (mortgage) {
        const rate = parseFloat(mortgage.value);
        html += `<p>The <span class="${rate > 7 ? "danger" : rate > 6 ? "warn" : "highlight"}">30Y mortgage rate at ${mortgage.value}%</span> `;
        if (rate > 7) html += `is severely restrictive. Housing affordability collapses, freezing both buyers and sellers.`;
        else if (rate > 6) html += `remains elevated, creating a significant affordability headwind. The "lock-in effect" constrains inventory.`;
        else html += `has eased enough to start thawing activity. Rate-sensitive sectors respond with a 6-12 month lag.`;
        html += `</p>`;
      }

      if (permits) {
        const pRaw = data.PERMIT?.observations?.[0]?.value || parseFloat(permits.value);
        const p = typeof pRaw === 'number' ? pRaw : parseFloat(pRaw);
        html += `<p>Building permits at <span class="highlight">${p.toFixed(0)}K</span> (annualized). `;
        if (p < 1300) html += `A decline signals builders see weakening demand ahead — this leads the broader economy by 6-12 months.`;
        else if (p < 1500) html += `Moderate levels suggest builders remain cautious but haven't pulled back sharply.`;
        else html += `Healthy permitting activity signals confidence in future demand.`;
        html += `</p>`;
      }

      if (caseShiller) {
        const cs = parseFloat(caseShiller.value);
        html += `<p>Home prices (Case-Shiller) are running <span class="highlight">${caseShiller.value}% YoY</span>. `;
        if (cs < 0) html += `Falling prices create a negative wealth effect on consumer spending.`;
        else if (cs > 8) html += `Rapid appreciation reflects supply constraints more than healthy demand.`;
        else html += `Moderate price growth is sustainable given the structural housing shortage.`;
        html += `</p>`;
      }

      if (supply) {
        html += `<p>Months' supply of homes at <span class="${parseFloat(supply.value) > 6 ? "warn" : "highlight"}">${supply.value} months</span>. `;
        if (parseFloat(supply.value) > 6) html += `Rising supply suggests the market is tilting toward buyers — potentially bearish for prices.`;
        else if (parseFloat(supply.value) < 4) html += `Extremely tight inventory keeps upward pressure on prices.`;
        else html += `Balanced supply-demand dynamics.`;
        html += `</p>`;
      }

      return html;
    }
  },

  labor: {
    title: "Labor Market Conditions",
    generate(data) {
      const ur = getLatest(data.UNRATE);
      const claims = getLatest(data.ICSA);
      const jolts = getLatest(data.JTSJOL);
      const participation = getLatest(data.CIVPART);

      let html = `<p>The labor market is a lagging indicator — by the time unemployment rises sharply, the recession is already underway. Druckenmiller focuses on leading edges: initial claims, JOLTS, and the rate of change.</p>`;

      if (ur) {
        const u = parseFloat(ur.value);
        html += `<p>Unemployment at <span class="${u > 5 ? "danger" : u > 4.5 ? "warn" : "highlight"}">${ur.value}%</span>. `;
        if (u > 5) html += `Elevated and likely rising — once unemployment crosses the 0.5% threshold above its cycle low (the Sahm Rule), recessions have always followed.`;
        else if (u > 4.5) html += `Starting to tick higher. The Sahm Rule threshold is the trigger to watch.`;
        else html += `Still tight, but the rate of change matters more than the level.`;
        html += `</p>`;
      }

      if (claims) {
        const ic = parseFloat(claims.value);
        html += `<p>Initial claims at <span class="${ic > 280 ? "danger" : ic > 230 ? "warn" : "highlight"}">${claims.value}K</span>. `;
        if (ic > 280) html += `A clear deterioration signal — layoffs are accelerating.`;
        else if (ic > 230) html += `Modestly elevated — warrants monitoring for trend acceleration.`;
        else html += `Very low, reflecting a tight labor market with minimal layoffs.`;
        html += `</p>`;
      }

      if (jolts) {
        const jRaw = data.JTSJOL?.observations?.[0]?.value || parseFloat(jolts.value);
        const j = typeof jRaw === 'number' ? jRaw : parseFloat(jRaw);
        html += `<p>Job openings (JOLTS) at <span class="highlight">${(j / 1000).toFixed(1)}M</span>. `;
        if (j < 7000) html += `The labor market has cooled meaningfully — fewer openings means less wage pressure.`;
        else if (j < 9000) html += `Normalizing from post-COVID extremes but still above pre-pandemic levels.`;
        else html += `Extremely elevated — the labor market remains historically tight.`;
        html += `</p>`;
      }

      if (participation) {
        html += `<p>Labor force participation at <span class="highlight">${participation.value}%</span>. The participation rate reflects structural trends — demographics, early retirement, disability — that shape the economy's potential growth rate.</p>`;
      }

      return html;
    }
  },

  markets: {
    title: "Cross-Asset Signals",
    generate(data) {
      const dxy = getLatest(data.DTWEXBGS);
      const oil = getLatest(data.DCOILWTICO);
      const copper = getLatest(data.GOLDAMGBD228NLBM);
      const sp = getLatest(data.SP500);
      const eur = getLatest(data.DEXUSEU);

      let html = `<p>Druckenmiller reads cross-asset signals as a system — the dollar, commodities, bonds, and equities tell a cohesive story about global conditions. Divergences often signal regime changes. He recently shifted toward tangible assets like copper over pure tech/AI plays.</p>`;

      if (oil) {
        const o = parseFloat(oil.value);
        html += `<p>WTI Crude at <span class="${o > 90 ? "danger" : "highlight"}">$${o.toFixed(0)}</span>/bbl. `;
        if (o > 90) html += `Elevated oil acts as a tax on consumers and threatens to reignite inflation.`;
        else if (o > 70) html += `In a moderate range that doesn't unduly stress consumers or the inflation picture.`;
        else html += `Low oil prices support the consumer but may signal global demand weakness.`;
        html += `</p>`;
      }

      if (copper) {
        html += `<p>Copper at <span class="highlight">$${parseFloat(copper.value).toFixed(2)}/lb</span>. Druckenmiller recently highlighted copper as a key tangible asset — it's a barometer of global industrial demand and a play on electrification and infrastructure spending.</p>`;
      }

      if (sp) {
        html += `<p>The S&P 500 at <span class="highlight">${parseFloat(sp.value).toFixed(0)}</span>. Druckenmiller looks at the "inside of the market" — sector leadership, breadth, and which parts of the market are leading — to gauge economic expectations embedded in prices.</p>`;
      }

      if (dxy) {
        html += `<p>The trade-weighted dollar at <span class="highlight">${parseFloat(dxy.value).toFixed(1)}</span>. Dollar strength tightens global financial conditions. Druckenmiller has historically made massive currency bets when macro regimes shift.</p>`;
      }

      return html;
    }
  },

  fiscal: {
    title: "Fiscal Sustainability Warning",
    generate(data) {
      const debtGdp = getLatest(data.GFDEGDQ188S);
      const interest = getLatest(data.A091RC1Q027SBEA);
      const deficit = getLatest(data.FYFSD);

      let html = `<p>Druckenmiller has been vocal about the US fiscal trajectory, warning of a potential "trust moment" where bond markets revolt against unsustainable deficits. He calls this "the most predictable crisis in history."</p>`;

      if (debtGdp) {
        const dgRaw = data.GFDEGDQ188S?.observations?.[0]?.value || parseFloat(debtGdp.value);
        const dg = typeof dgRaw === 'number' ? dgRaw : parseFloat(dgRaw);
        html += `<p>Debt-to-GDP at <span class="${dg > 120 ? "danger" : dg > 100 ? "warn" : "highlight"}">${dg.toFixed(0)}%</span>. `;
        if (dg > 120) html += `At these levels, debt dynamics become self-reinforcing — higher rates increase interest costs, which increase deficits, which increase debt.`;
        else if (dg > 100) html += `Above 100% and rising. The US is in uncharted fiscal territory for a peacetime economy.`;
        else html += `Below historic peaks but the trajectory remains the concern.`;
        html += `</p>`;
      }

      if (interest) {
        // A091RC1Q027SBEA is in billions (annualized)
        const iRaw = data.A091RC1Q027SBEA?.observations?.[0]?.value || parseFloat(interest.value);
        const i = typeof iRaw === 'number' ? iRaw : parseFloat(iRaw);
        const iStr = i >= 1000 ? `$${(i / 1000).toFixed(1)}T` : `$${i.toFixed(0)}B`;
        html += `<p>Federal interest payments running at <span class="warn">${iStr}</span> (annualized). `;
        if (i > 800) html += `Interest expense now rivals defense spending — a milestone Druckenmiller has repeatedly flagged. As old debt rolls over at higher rates, this figure accelerates.`;
        else html += `Rising as legacy low-rate debt matures and refinances at current higher yields.`;
        html += `</p>`;
      }

      if (deficit) {
        // FYFSD is in millions
        const dRaw = Math.abs(data.FYFSD?.observations?.[0]?.value || parseFloat(deficit.value));
        const dStr = dRaw >= 1e6 ? `$${(dRaw / 1e6).toFixed(1)}T` : dRaw >= 1e3 ? `$${(dRaw / 1e3).toFixed(0)}B` : `$${dRaw.toFixed(0)}M`;
        html += `<p>The federal deficit is <span class="danger">${dStr}</span>. Running deficits of this magnitude outside of a recession or war is historically unprecedented and narrows the fiscal space available for the next downturn.</p>`;
      }

      return html;
    }
  }
};

// --- Data Loading ---
let allData = null;
let fetchTimestamp = "";

async function loadData() {
  const resp = await fetch("./data.json");
  const json = await resp.json();
  allData = json.data;
  fetchTimestamp = json.fetched_at;
  return allData;
}

function getTabData(tabName) {
  if (!allData || !allData[tabName]) return {};
  return allData[tabName];
}

// --- Data Helpers ---
function getLatest(series) {
  if (!series || !series.observations || series.observations.length === 0) return null;
  const obs = series.observations;
  const meta = series.meta || {};

  if (meta.transform === "yoy" && obs.length > 12) {
    const latest = obs[0].value;
    const yearAgo = obs[11]?.value || obs[obs.length - 1].value;
    const yoyPct = ((latest - yearAgo) / yearAgo * 100).toFixed(1);
    return { date: obs[0].date, value: yoyPct };
  }

  return { date: obs[0].date, value: fmtNum(obs[0].value, meta.unit) };
}

function getPrevYear(series) {
  if (!series || !series.observations) return null;
  const obs = series.observations;
  const meta = series.meta || {};
  if (obs.length < 13) return null;
  return { date: obs[12].date, value: fmtNum(obs[12].value, meta.unit) };
}

function fmtNum(val, unit) {
  if (val === null || val === undefined) return "—";
  const n = typeof val === "number" ? val : parseFloat(val);
  if (isNaN(n)) return val;

  // Unit-aware formatting
  // M$ = millions of dollars -> display in T/B
  if (unit === "M$") {
    if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1) + "T";
    if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(0) + "B";
    return n.toFixed(0) + "M";
  }
  // B$ = billions of dollars -> display in T/B
  if (unit === "B$") {
    if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1) + "T";
    return n.toFixed(0) + "B";
  }

  // Generic formatting
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1) + "M";
  if (Math.abs(n) >= 1e4) return (n / 1e3).toFixed(0) + "K";
  if (Math.abs(n) >= 100) return n.toFixed(0);
  if (Math.abs(n) >= 10) return n.toFixed(1);
  return n.toFixed(2);
}

function getDelta(series) {
  if (!series || !series.observations || series.observations.length < 2) return null;
  const curr = series.observations[0].value;
  const prev = series.observations[1].value;
  if (prev === 0) return { pct: "0.0", dir: "flat" };
  const pct = ((curr - prev) / Math.abs(prev) * 100).toFixed(1);
  const dir = parseFloat(pct) > 0.05 ? "up" : parseFloat(pct) < -0.05 ? "down" : "flat";
  return { pct, dir };
}

// --- Rendering ---
const chartInstances = {};

const TAB_TITLES = {
  liquidity: ["Liquidity & Monetary Policy", "Fed policy, yield curve, credit spreads, money supply — the engine of everything."],
  growth: ["Economic Growth & Activity", "GDP, industrial production, durable goods, retail sales, consumer sentiment."],
  inflation: ["Inflation & Price Stability", "CPI, PCE, breakevens, expectations — the regime Druckenmiller watches most closely."],
  housing: ["Housing & Rate-Sensitive Sectors", "Building permits, housing starts, mortgage rates — the leading indicators of the cycle."],
  labor: ["Labor Market", "Employment, claims, JOLTS, wages — lagging but critical when they turn."],
  markets: ["Cross-Asset Market Signals", "Dollar, commodities, equities — the price signals that confirm or deny the macro thesis."],
  fiscal: ["Fiscal & Government Debt", "Deficits, debt-to-GDP, interest expense — the slow-motion crisis."],
};

function renderTab(tabName, data) {
  // Destroy existing charts
  Object.keys(chartInstances).forEach(k => {
    if (k.startsWith(tabName + "_")) {
      chartInstances[k].destroy();
      delete chartInstances[k];
    }
  });

  const seriesMap = SERIES[tabName];
  const entries = Object.entries(seriesMap);
  const kpiEntries = entries.slice(0, 4);
  const commentaryDef = COMMENTARY[tabName];

  let html = `<div class="tab-panel active" id="panel-${tabName}">`;

  // Header
  html += `<div class="panel-header">
    <div class="panel-title">${TAB_TITLES[tabName][0]}</div>
    <div class="panel-subtitle">${TAB_TITLES[tabName][1]}</div>
  </div>`;

  // KPIs
  html += `<div class="kpi-row">`;
  kpiEntries.forEach(([id]) => {
    const series = data[id];
    if (!series) return;
    const meta = series.meta || SERIES[tabName][id];
    const latest = getLatest(series);
    const delta = getDelta(series);
    const unitSuffix = meta.transform === "yoy" ? "% YoY" : (meta.unit === "%" ? "%" : "");
    const prefix = meta.unit === "$" || meta.unit === "$/lb" ? "$" : "";

    html += `<div class="kpi-card">
      <div class="kpi-label">${meta.name}</div>
      <div class="kpi-value">${prefix}${latest ? latest.value : "—"}${unitSuffix}</div>`;

    if (delta) {
      const arrow = delta.dir === "up" ? "&#9650;" : delta.dir === "down" ? "&#9660;" : "&#8212;";
      html += `<div class="kpi-delta ${delta.dir}">${arrow} ${delta.pct}%</div>`;
    }

    if (latest) {
      html += `<div class="kpi-period">${latest.date}</div>`;
    }

    html += `</div>`;
  });
  html += `</div>`;

  // Commentary
  if (commentaryDef) {
    html += `<div class="commentary">
      <div class="commentary-title">${commentaryDef.title}</div>
      ${commentaryDef.generate(data)}
    </div>`;
  }

  // Charts
  html += `<div class="chart-grid">`;
  entries.forEach(([id]) => {
    const series = data[id];
    if (!series) return;
    const meta = series.meta || SERIES[tabName][id];
    const freqLabel = { d: "Daily", w: "Weekly", m: "Monthly", q: "Quarterly", a: "Annual" }[meta.freq] || "";

    html += `<div class="chart-card">
      <div class="chart-title">${meta.name} <span class="badge">${id}</span></div>
      <div class="chart-desc">${meta.unit ? "Unit: " + meta.unit + " · " : ""}${freqLabel}</div>
      <div class="chart-container"><canvas id="chart-${tabName}-${id}"></canvas></div>
    </div>`;
  });
  html += `</div>`;

  html += `</div>`;
  return html;
}

function renderCharts(tabName, data) {
  const seriesMap = SERIES[tabName];
  const colors = [
    "rgba(32, 217, 151, 1)", "rgba(88, 166, 255, 1)", "rgba(240, 196, 56, 1)",
    "rgba(240, 83, 101, 1)", "rgba(179, 136, 255, 1)", "rgba(57, 197, 207, 1)",
    "rgba(240, 136, 62, 1)",
  ];

  Object.entries(seriesMap).forEach(([id], idx) => {
    const canvas = document.getElementById(`chart-${tabName}-${id}`);
    if (!canvas) return;

    const series = data[id];
    if (!series || !series.observations || series.observations.length === 0) return;

    const meta = series.meta || {};
    const obs = [...series.observations].reverse();
    const labels = obs.map(o => o.date);
    const values = obs.map(o => o.value);
    const color = colors[idx % colors.length];
    const colorFaded = color.replace(", 1)", ", 0.12)");

    const chartKey = `${tabName}_${id}`;
    if (chartInstances[chartKey]) {
      chartInstances[chartKey].destroy();
    }

    const ctx = canvas.getContext("2d");
    chartInstances[chartKey] = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          data: values,
          borderColor: color,
          backgroundColor: colorFaded,
          borderWidth: 1.5,
          pointRadius: 0,
          pointHitRadius: 10,
          fill: true,
          tension: 0.3,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 600, easing: "easeOutQuart" },
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#ffffff",
            borderColor: "#dce1e8",
            borderWidth: 1,
            titleColor: "#2c3440",
            bodyColor: "#11161c",
            titleFont: { family: "'JetBrains Mono'", size: 11 },
            bodyFont: { family: "'JetBrains Mono'", size: 12, weight: "bold" },
            padding: 10,
            displayColors: false,
            callbacks: {
              title: (items) => items[0]?.label || "",
              label: (item) => {
                const v = item.parsed.y;
                const prefix = (meta.unit === "$" || meta.unit === "$/lb") ? "$" : "";
                const suffix = meta.unit === "%" ? "%" : "";
                return `${prefix}${v.toLocaleString(undefined, { maximumFractionDigits: 2 })}${suffix}`;
              }
            }
          }
        },
        scales: {
          x: {
            type: "time",
            time: { parser: "yyyy-MM-dd", tooltipFormat: "MMM dd, yyyy" },
            ticks: {
              color: "#5d6b7a",
              font: { family: "'JetBrains Mono'", size: 10 },
              maxTicksLimit: 6,
              maxRotation: 0,
            },
            grid: { color: "rgba(20, 30, 45, 0.08)", drawBorder: false },
            border: { display: false },
          },
          y: {
            ticks: {
              color: "#5d6b7a",
              font: { family: "'JetBrains Mono'", size: 10 },
              maxTicksLimit: 5,
              callback(val) {
                if (Math.abs(val) >= 1e6) return (val / 1e6).toFixed(1) + "M";
                if (Math.abs(val) >= 1e3) return (val / 1e3).toFixed(0) + "K";
                return val;
              }
            },
            grid: { color: "rgba(20, 30, 45, 0.08)", drawBorder: false },
            border: { display: false },
          }
        }
      }
    });
  });
}

// --- Tab Navigation ---
let activeTab = "liquidity";
const tabs = document.querySelectorAll(".tab");
const mainContent = document.getElementById("main-content");

function switchTab(tabName) {
  activeTab = tabName;

  tabs.forEach(t => {
    const isActive = t.dataset.tab === tabName;
    t.classList.toggle("active", isActive);
    t.setAttribute("aria-selected", isActive);
  });

  const data = getTabData(tabName);
  if (!data || Object.keys(data).length === 0) {
    mainContent.innerHTML = `<div class="loading-screen">
      <div class="loading-text">
        <span class="prompt" style="color:var(--red)">&gt;</span> No data available for ${tabName.toUpperCase()}<br>
        <span class="prompt">&gt;</span> Try another tab.
      </div>
    </div>`;
    return;
  }

  mainContent.innerHTML = renderTab(tabName, data);
  // Render charts after DOM is ready
  requestAnimationFrame(() => renderCharts(tabName, data));
}

// Click handlers
tabs.forEach(tab => {
  tab.addEventListener("click", () => switchTab(tab.dataset.tab));
});

// Keyboard navigation
document.addEventListener("keydown", (e) => {
  // Don't intercept if user is typing in an input
  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

  const tabOrder = ["liquidity", "growth", "inflation", "housing", "labor", "markets", "fiscal"];
  const num = parseInt(e.key);
  if (num >= 1 && num <= 7) {
    e.preventDefault();
    switchTab(tabOrder[num - 1]);
    return;
  }

  if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
    e.preventDefault();
    const idx = tabOrder.indexOf(activeTab);
    const next = e.key === "ArrowRight"
      ? tabOrder[(idx + 1) % tabOrder.length]
      : tabOrder[(idx - 1 + tabOrder.length) % tabOrder.length];
    switchTab(next);
  }
});

// Clock
function updateClock() {
  const el = document.getElementById("clock");
  if (el) {
    el.textContent = new Date().toLocaleTimeString("en-US", {
      hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit"
    });
  }
}
updateClock();
setInterval(updateClock, 1000);

// --- Init ---
(async function init() {
  try {
    await loadData();
    switchTab("liquidity");
  } catch (err) {
    mainContent.innerHTML = `<div class="loading-screen">
      <div class="loading-text">
        <span class="prompt" style="color:var(--red)">&gt;</span> Failed to load data: ${err.message}<br>
        <span class="prompt">&gt;</span> Refresh to retry.
      </div>
    </div>`;
  }
})();
