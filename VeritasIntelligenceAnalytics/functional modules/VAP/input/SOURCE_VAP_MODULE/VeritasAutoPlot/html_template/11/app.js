(function () {
  "use strict";

  // ──────────────────────────────────────
  // Annotations — key events in rate history
  // ──────────────────────────────────────
  const annotations = [
    {
      date: "1979-08-01",
      title: "Volcker Becomes Fed Chair",
      body: "Paul Volcker takes over as Federal Reserve Chairman, vowing to crush double-digit inflation through aggressive monetary tightening."
    },
    {
      date: "1980-06-01",
      title: "Volcker Shock — Rates Hit 17%+",
      body: "The Fed funds rate peaks near 20% as Volcker engineers the most aggressive tightening in Fed history to break the back of stagflation. Mortgage rates exceed 18%."
    },
    {
      date: "1981-07-01",
      title: "Peak Rate: 19.1%",
      body: "The effective fed funds rate reaches its all-time high of 19.1%. The US enters a deep recession, but inflation begins its long decline from 14.8% to under 4% by 1983."
    },
    {
      date: "1987-10-01",
      title: "Black Monday Crash",
      body: "The Dow Jones drops 22.6% in a single day on October 19, 1987 — the largest one-day percentage decline in history. The Fed provides emergency liquidity."
    },
    {
      date: "1990-08-01",
      title: "Gulf War & Recession",
      body: "Iraq invades Kuwait, oil prices spike, and the US enters a recession lasting through March 1991. The Fed begins cutting rates from 8% toward 3%."
    },
    {
      date: "1994-02-01",
      title: "1994 Bond Massacre",
      body: "The Fed surprises markets by hiking rates 7 times in 12 months, nearly doubling the rate to 6%. Bond markets worldwide suffer their worst losses in decades."
    },
    {
      date: "1997-07-01",
      title: "Asian Financial Crisis",
      body: "Currency collapses spread across Thailand, Indonesia, South Korea, and beyond. Global contagion fears rise, though the US economy remains resilient."
    },
    {
      date: "1998-09-01",
      title: "LTCM Collapse & Russia Default",
      body: "Russia defaults on its debt and hedge fund Long-Term Capital Management nearly triggers a systemic crisis. The Fed cuts rates three times as an insurance measure."
    },
    {
      date: "2001-01-01",
      title: "Dot-Com Bust",
      body: "The Nasdaq has fallen 45% from its March 2000 peak. The Fed begins an aggressive easing cycle, cutting rates 11 times in 2001 from 6.5% to 1.75%."
    },
    {
      date: "2001-09-01",
      title: "9/11 Attacks",
      body: "The September 11 terrorist attacks devastate markets. The Fed cuts rates by 50 bps at an emergency meeting on September 17, adding to an already aggressive easing campaign."
    },
    {
      date: "2004-06-01",
      title: "Greenspan's Measured Tightening",
      body: "After holding rates at 1% for a year, the Fed begins a long campaign of 17 consecutive 25-bps hikes over two years, fueling what would become the housing bubble."
    },
    {
      date: "2007-08-01",
      title: "Subprime Crisis Begins",
      body: "BNP Paribas freezes three investment funds, signaling the start of the global financial crisis. Credit markets seize up as subprime mortgage losses mount."
    },
    {
      date: "2008-09-01",
      title: "Lehman Brothers Collapses",
      body: "Lehman Brothers files for bankruptcy on September 15, 2008, triggering the worst financial crisis since the Great Depression. The Fed slashes rates toward zero."
    },
    {
      date: "2008-12-01",
      title: "Zero Interest Rate Policy (ZIRP)",
      body: "The Fed cuts rates to 0–0.25% and launches the first round of Quantitative Easing. Rates would remain near zero for 7 years — an unprecedented era."
    },
    {
      date: "2011-08-01",
      title: "US Debt Downgrade",
      body: "S&P downgrades US sovereign debt from AAA for the first time in history, citing political dysfunction over the debt ceiling. Markets whipsaw but rates stay near zero."
    },
    {
      date: "2013-06-01",
      title: "Taper Tantrum",
      body: "Fed Chair Bernanke hints at tapering bond purchases, causing Treasury yields to spike and emerging market turmoil. The 10-year yield jumps from 1.6% to 3%."
    },
    {
      date: "2015-12-01",
      title: "First Rate Hike in 9 Years",
      body: "After 7 years at zero, the Fed raises rates by 25 bps under Chair Yellen. The \"liftoff\" marks the beginning of a cautious normalization cycle."
    },
    {
      date: "2018-12-01",
      title: "Powell's Rate Hike Backlash",
      body: "The Fed raises rates to 2.25–2.50%, sparking a near-20% stock market selloff. President Trump publicly attacks Fed Chair Powell, demanding rate cuts."
    },
    {
      date: "2019-08-01",
      title: "Trade War Rate Cuts",
      body: "Amid escalating US-China trade war uncertainty, the Fed cuts rates three times in 2019 in what Powell calls a \"mid-cycle adjustment.\""
    },
    {
      date: "2020-03-01",
      title: "COVID-19 Emergency Cuts",
      body: "As the pandemic shuts down the global economy, the Fed slashes rates to zero in two emergency meetings — 150 bps in just 13 days. Trillions in stimulus follow."
    },
    {
      date: "2022-03-01",
      title: "Post-COVID Rate Hikes Begin",
      body: "With inflation at 8.5%, the Fed begins the fastest tightening cycle in 40 years. Over 16 months, rates rise from near-zero to 5.25–5.50%."
    },
    {
      date: "2023-03-01",
      title: "SVB & Banking Crisis",
      body: "Silicon Valley Bank collapses in the second-largest US bank failure ever, followed by Signature Bank. The Fed creates an emergency lending facility while continuing to fight inflation."
    },
    {
      date: "2024-09-01",
      title: "First Cut Since COVID",
      body: "The Fed cuts rates by 50 bps — the first reduction since 2020. After holding at 5.25–5.50% for over a year, Powell signals confidence that inflation is trending toward 2%."
    }
  ];

  // ──────────────────────────────────────
  // Recession periods (NBER)
  // ──────────────────────────────────────
  const recessions = [
    { start: "1980-01-01", end: "1980-07-01" },
    { start: "1981-07-01", end: "1982-11-01" },
    { start: "1990-07-01", end: "1991-03-01" },
    { start: "2001-03-01", end: "2001-11-01" },
    { start: "2007-12-01", end: "2009-06-01" },
    { start: "2020-02-01", end: "2020-04-01" }
  ];

  // ──────────────────────────────────────
  // Parse & render
  // ──────────────────────────────────────
  const parseDate = d3.timeParse("%Y-%m-%d");
  const formatDate = d3.timeFormat("%B %Y");
  const formatYear = d3.timeFormat("%Y");

  let svg, xScale, yScale, width, height, data;
  let tooltipEl, annotationTooltipEl, crosshairLine, crosshairDot;

  const margin = { top: 56, right: 24, bottom: 36, left: 48 };

  function init() {
    const container = document.getElementById("chart");

    // Create tooltip elements
    tooltipEl = document.createElement("div");
    tooltipEl.className = "tooltip";
    tooltipEl.innerHTML = '<div class="tooltip-date"></div><div class="tooltip-rate"></div>';
    container.appendChild(tooltipEl);

    annotationTooltipEl = document.createElement("div");
    annotationTooltipEl.className = "annotation-tooltip";
    annotationTooltipEl.innerHTML =
      '<div class="annotation-tooltip-title"></div>' +
      '<div class="annotation-tooltip-date"></div>' +
      '<div class="annotation-tooltip-body"></div>';
    container.appendChild(annotationTooltipEl);

    d3.csv("./data.csv").then(function (raw) {
      data = raw
        .map(function (d) {
          return { date: parseDate(d.observation_date), rate: +d.FEDFUNDS };
        })
        .filter(function (d) { return d.date && !isNaN(d.rate); });

      draw();
      window.addEventListener("resize", draw);
    });
  }

  function draw() {
    var container = document.getElementById("chart");
    var rect = container.getBoundingClientRect();
    var W = rect.width;
    var H = rect.height;

    if (W < 100 || H < 100) return;

    width = W - margin.left - margin.right;
    height = H - margin.top - margin.bottom;

    // Clear previous
    d3.select("#chart svg").remove();

    svg = d3.select("#chart")
      .append("svg")
      .attr("width", W)
      .attr("height", H)
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Scales
    xScale = d3.scaleTime()
      .domain(d3.extent(data, function (d) { return d.date; }))
      .range([0, width]);

    yScale = d3.scaleLinear()
      .domain([0, d3.max(data, function (d) { return d.rate; }) * 1.08])
      .range([height, 0]);

    // Clip path
    svg.append("defs").append("clipPath")
      .attr("id", "chart-clip")
      .append("rect")
      .attr("width", width)
      .attr("height", height);

    var chartArea = svg.append("g").attr("clip-path", "url(#chart-clip)");

    // Recession bands
    recessions.forEach(function (r) {
      var s = parseDate(r.start);
      var e = parseDate(r.end);
      var domainStart = xScale.domain()[0];
      var domainEnd = xScale.domain()[1];
      if (e < domainStart || s > domainEnd) return;
      chartArea.append("rect")
        .attr("class", "recession-band")
        .attr("x", xScale(d3.max([s, domainStart])))
        .attr("y", 0)
        .attr("width", xScale(d3.min([e, domainEnd])) - xScale(d3.max([s, domainStart])))
        .attr("height", height);
    });

    // Area gradient
    var gradient = svg.select("defs")
      .append("linearGradient")
      .attr("id", "area-gradient")
      .attr("x1", "0").attr("y1", "0")
      .attr("x2", "0").attr("y2", "1");

    gradient.append("stop")
      .attr("offset", "0%")
      .attr("stop-color", "var(--color-area-top)");
    gradient.append("stop")
      .attr("offset", "100%")
      .attr("stop-color", "var(--color-area-bottom)");

    // Area
    var area = d3.area()
      .x(function (d) { return xScale(d.date); })
      .y0(height)
      .y1(function (d) { return yScale(d.rate); })
      .curve(d3.curveMonotoneX);

    chartArea.append("path")
      .datum(data)
      .attr("class", "rate-area")
      .attr("fill", "url(#area-gradient)")
      .attr("d", area);

    // Line
    var line = d3.line()
      .x(function (d) { return xScale(d.date); })
      .y(function (d) { return yScale(d.rate); })
      .curve(d3.curveMonotoneX);

    chartArea.append("path")
      .datum(data)
      .attr("class", "rate-line")
      .attr("d", line);

    // Y Axis
    var yAxis = d3.axisLeft(yScale)
      .ticks(6)
      .tickSize(-width)
      .tickFormat(function (d) { return d + "%"; });

    svg.append("g")
      .attr("class", "axis-y")
      .call(yAxis)
      .selectAll(".tick text")
      .attr("dx", -4);

    // X Axis
    var tickCount = W < 600 ? 6 : W < 900 ? 10 : 15;
    var xAxis = d3.axisBottom(xScale)
      .ticks(tickCount)
      .tickSize(4)
      .tickFormat(formatYear);

    svg.append("g")
      .attr("class", "axis-x")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis);

    // Title
    svg.append("text")
      .attr("class", "chart-title")
      .attr("x", 0)
      .attr("y", -28)
      .text("Federal Funds Rate");

    svg.append("text")
      .attr("class", "chart-subtitle")
      .attr("x", 0)
      .attr("y", -12)
      .text("Monthly effective rate, 1975–2026");

    // Crosshair elements
    crosshairLine = chartArea.append("line")
      .attr("class", "crosshair-line")
      .attr("y1", 0)
      .attr("y2", height)
      .style("display", "none");

    crosshairDot = chartArea.append("g")
      .style("display", "none");

    crosshairDot.append("circle")
      .attr("r", 5)
      .attr("fill", "var(--color-bg)")
      .attr("stroke", "var(--color-accent)")
      .attr("stroke-width", 2);

    crosshairDot.append("circle")
      .attr("r", 2)
      .attr("fill", "var(--color-accent)");

    // Interaction overlay (below annotations so annotations get pointer events)
    var overlay = svg.append("rect")
      .attr("width", width)
      .attr("height", height)
      .attr("fill", "transparent")
      .attr("cursor", "crosshair");

    // Annotation markers (drawn AFTER overlay so they sit on top)
    var annotationLayer = svg.append("g").attr("class", "annotation-layer");
    drawAnnotations(annotationLayer);

    var bisector = d3.bisector(function (d) { return d.date; }).left;

    overlay.on("mousemove", function (event) {
      var coords = d3.pointer(event);
      var x0 = xScale.invert(coords[0]);
      var i = bisector(data, x0, 1);
      var d0 = data[i - 1];
      var d1 = data[i];
      if (!d0 || !d1) return;
      var d = x0 - d0.date > d1.date - x0 ? d1 : d0;

      var px = xScale(d.date);
      var py = yScale(d.rate);

      crosshairLine
        .attr("x1", px)
        .attr("x2", px)
        .style("display", null);

      crosshairDot
        .attr("transform", "translate(" + px + "," + py + ")")
        .style("display", null);

      // Update tooltip
      tooltipEl.querySelector(".tooltip-date").textContent = formatDate(d.date);
      tooltipEl.querySelector(".tooltip-rate").innerHTML =
        d.rate.toFixed(2) + "<span>%</span>";
      tooltipEl.classList.add("visible");

      // Position tooltip
      var ttRect = tooltipEl.getBoundingClientRect();
      var containerRect = container.getBoundingClientRect();
      var absX = px + margin.left;
      var absY = py + margin.top;

      var left = absX + 14;
      if (left + ttRect.width > containerRect.width - 8) {
        left = absX - ttRect.width - 14;
      }
      var top = absY - ttRect.height / 2;
      top = Math.max(4, Math.min(top, containerRect.height - ttRect.height - 4));

      tooltipEl.style.left = left + "px";
      tooltipEl.style.top = top + "px";
    });

    overlay.on("mouseleave", function () {
      crosshairLine.style("display", "none");
      crosshairDot.style("display", "none");
      tooltipEl.classList.remove("visible");
    });
  }

  function drawAnnotations(chartArea) {
    var container = document.getElementById("chart");

    annotations.forEach(function (ann) {
      var d = parseDate(ann.date);
      if (!d) return;
      var domainStart = xScale.domain()[0];
      var domainEnd = xScale.domain()[1];
      if (d < domainStart || d > domainEnd) return;

      // Find closest data point
      var bisector = d3.bisector(function (dd) { return dd.date; }).left;
      var i = bisector(data, d, 1);
      var d0 = data[i - 1];
      var d1 = data[i];
      if (!d0) return;
      var closest = !d1 ? d0 : (d - d0.date > d1.date - d ? d1 : d0);

      var px = xScale(closest.date);
      var py = yScale(closest.rate);

      // Stem from top
      var stemTop = Math.max(py - 40, -20);

      var g = chartArea.append("g")
        .attr("class", "annotation-marker")
        .attr("transform", "translate(" + px + ", 0)");

      g.append("line")
        .attr("class", "marker-stem")
        .attr("x1", 0).attr("y1", stemTop)
        .attr("x2", 0).attr("y2", py - 6);

      g.append("circle")
        .attr("class", "marker-ring")
        .attr("cx", 0).attr("cy", stemTop)
        .attr("r", 6);

      g.append("circle")
        .attr("class", "marker-dot")
        .attr("cx", 0).attr("cy", stemTop)
        .attr("r", 3);

      // Hover
      g.on("mouseenter", function () {
        // Hide rate tooltip when hovering annotation
        crosshairLine.style("display", "none");
        crosshairDot.style("display", "none");
        tooltipEl.classList.remove("visible");

        annotationTooltipEl.querySelector(".annotation-tooltip-title").textContent = ann.title;
        annotationTooltipEl.querySelector(".annotation-tooltip-date").textContent =
          formatDate(closest.date) + "  ·  Rate: " + closest.rate.toFixed(2) + "%";
        annotationTooltipEl.querySelector(".annotation-tooltip-body").textContent = ann.body;
        annotationTooltipEl.classList.add("visible");

        var ttRect = annotationTooltipEl.getBoundingClientRect();
        var containerRect = container.getBoundingClientRect();
        var absX = px + margin.left;
        var absStemY = stemTop + margin.top;

        var left = absX + 12;
        if (left + ttRect.width > containerRect.width - 12) {
          left = absX - ttRect.width - 12;
        }
        left = Math.max(8, left);

        var top = absStemY - ttRect.height / 2;
        top = Math.max(4, Math.min(top, containerRect.height - ttRect.height - 4));

        annotationTooltipEl.style.left = left + "px";
        annotationTooltipEl.style.top = top + "px";
      });

      g.on("mouseleave", function () {
        annotationTooltipEl.classList.remove("visible");
      });
    });
  }

  init();
})();
