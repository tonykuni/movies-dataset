(function () {
  "use strict";

  // ── Dark mode toggle ──
  const toggle = document.querySelector("[data-theme-toggle]");
  const root = document.documentElement;
  let theme = matchMedia("(prefers-color-scheme:dark)").matches
    ? "dark"
    : "light";
  root.setAttribute("data-theme", theme);

  if (toggle) {
    updateToggleIcon();
    toggle.addEventListener("click", function () {
      theme = theme === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", theme);
      toggle.setAttribute(
        "aria-label",
        "Switch to " + (theme === "dark" ? "light" : "dark") + " mode"
      );
      updateToggleIcon();
      if (typeof drawChart === "function") {
        drawChart();
      }
    });
  }

  function updateToggleIcon() {
    if (!toggle) return;
    toggle.innerHTML =
      theme === "dark"
        ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
        : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  }

  // ── Globals ──
  var allData = [];
  var filteredData = [];
  var currentScale = "log";
  var currentSector = "all";
  var searchTerm = "";
  var highlightedSymbols = [];

  // ── Findings data ──
  var findings = [
    {
      number: "Finding 1",
      title: "NVIDIA: Highest Profit Margin Among Mega-Caps",
      desc: "NVIDIA earns $120.1B on $215.9B revenue — a staggering 55.6% net margin — making it the most profitable mega-cap by margin. Its $4.4T market cap is the largest in the index, yet its revenue is just half of Apple's. The market is pricing in enormous AI-driven growth.",
      tickers: ["NVDA", "AAPL", "MSFT"]
    },
    {
      number: "Finding 2",
      title: "Alphabet Outearns Apple Despite Lower Revenue",
      desc: "Google's parent generated $132.2B in net income on $402.9B revenue, surpassing Apple's $117.8B net income on $435.6B revenue. Alphabet's 32.8% net margin vs. Apple's 27% illustrates how digital advertising and cloud scale to near-zero marginal cost.",
      tickers: ["GOOGL", "AAPL"]
    },
    {
      number: "Finding 3",
      title: "Walmart: Revenue Giant, Profit Minnow",
      desc: "With $713.2B in TTM revenue, Walmart is the S&P 500's top-line leader, but its $21.9B net income yields just a 3.1% net margin. It earned less profit than NVIDIA despite generating 3.3x more revenue — the starkest illustration of how value has shifted from physical retail to tech.",
      tickers: ["WMT", "NVDA", "AMZN"]
    },
    {
      number: "Finding 4",
      title: "The Healthcare Revenue Paradox",
      desc: "UnitedHealth ($447.6B revenue), CVS ($402.1B), and McKesson ($397.9B) are among the top-5 revenue generators, but their net margins are razor-thin (0.4%-2.7%). These companies move enormous dollar volumes through insurance premiums and drug distribution with minimal profit per dollar.",
      tickers: ["UNH", "CVS", "MCK", "COR"]
    },
    {
      number: "Finding 5",
      title: "Memory Chip Revenge: SNDK Up 1,011%, MU Up 347%",
      desc: "SanDisk, Western Digital, Micron, and Seagate were the biggest gainers over 12 months, with memory and storage stocks surging on AI data center demand. The semiconductor cycle turned sharply positive, propelling these stocks from losses to massive profits.",
      tickers: ["SNDK", "WDC", "MU", "STX"]
    },
    {
      number: "Finding 6",
      title: "Palantir: The Valuation Outlier",
      desc: "Palantir commands a $358B market cap on just $4.5B revenue — a revenue-to-market-cap ratio of 1.2%, the lowest in the entire S&P 500. At 80x trailing revenue, it is priced as though it will become one of the largest software companies on Earth.",
      tickers: ["PLTR", "APP", "CRWD"]
    },
    {
      number: "Finding 7",
      title: "12 Companies Losing Money but Stocks Soaring",
      desc: "Ford (-$8.2B net income, +22%), Intel (-$267M, +129%), Moderna (-$2.8B, +55%), and Albemarle (-$511M, +122%) all posted TTM losses yet saw double-digit stock gains. Markets are pricing in turnaround stories and cyclical recoveries.",
      tickers: ["F", "INTC", "MRNA", "ALB", "VTRS"]
    },
    {
      number: "Finding 8",
      title: "Broadcom's Ascent to the $1.6T Club",
      desc: "Broadcom's market cap reached $1.64T — larger than Meta — despite having only $68.3B in revenue. Its 87% stock gain reflects the AI networking chip boom. With a 36.6% net margin, it pairs strong profitability with premium valuation.",
      tickers: ["AVGO", "META", "NVDA"]
    },
    {
      number: "Finding 9",
      title: "Visa and Mastercard: The Profit Machines",
      desc: "Visa (50.2% net margin) and Mastercard (45.6% net margin) sit in a class of their own among large companies. Visa turns $41.4B revenue into $20.8B profit, while MA converts $32.8B into $15.0B. Their near-zero marginal cost per transaction makes them some of the most efficient businesses ever built.",
      tickers: ["V", "MA"]
    },
    {
      number: "Finding 10",
      title: "Real Estate: Highest Margins, Smallest Revenues",
      desc: "Simon Property Group (72.5% net margin) and VICI Properties (69.1%) are the S&P 500's most profitable by margin, but they operate on relatively small revenue bases ($6.4B and $4.0B). REITs benefit from rental income structures that pass most revenue straight to the bottom line.",
      tickers: ["SPG", "VICI", "CME"]
    },
    {
      number: "Finding 11",
      title: "The GE Vernova Breakout",
      desc: "Spun off from General Electric, GE Vernova surged 207% in its first year as a public company, reaching a $225B market cap on $38.1B revenue. The energy transition and power infrastructure demand made it the highest-gaining non-memory stock in the index.",
      tickers: ["GEV", "GE", "GEHC"]
    },
    {
      number: "Finding 12",
      title: "UnitedHealth's Historic Crash",
      desc: "Despite being the 3rd-largest company by revenue at $447.6B, UnitedHealth plunged 40.6% over 12 months — the steepest drop among mega-revenue companies. Its market cap fell to $258B, less than companies with a fraction of its revenue.",
      tickers: ["UNH", "MOH", "CNC"]
    }
  ];

  // ── Format helpers ──
  function fmtDollar(val) {
    var abs = Math.abs(val);
    if (abs >= 1e12) return "$" + (val / 1e12).toFixed(2) + "T";
    if (abs >= 1e9) return "$" + (val / 1e9).toFixed(1) + "B";
    if (abs >= 1e6) return "$" + (val / 1e6).toFixed(0) + "M";
    return "$" + val.toFixed(0);
  }

  function fmtPct(val) {
    var sign = val >= 0 ? "+" : "";
    return sign + val.toFixed(1) + "%";
  }

  // ── Color scale: red → gray → green ──
  function priceChangeColor(pct) {
    // Clamp to [-60, 120] for meaningful spread
    var clamped = Math.max(-60, Math.min(120, pct));
    if (clamped < 0) {
      // Red range: -60 → 0
      var t = (clamped + 60) / 60;
      return d3.interpolateRgb("#c0392b", "#95a5a6")(t);
    } else {
      // Green range: 0 → 120
      var t2 = clamped / 120;
      return d3.interpolateRgb("#95a5a6", "#1a8c3e")(t2);
    }
  }

  // ── Load data ──
  d3.json("./data.json").then(function (data) {
    allData = data.filter(function (d) {
      return d.ttm_revenue > 0 && d.market_cap > 0;
    });

    // Populate sector filter
    var sectors = Array.from(new Set(allData.map(function (d) { return d.sector; }))).sort();
    var sel = document.getElementById("sector-filter");
    sectors.forEach(function (s) {
      var opt = document.createElement("option");
      opt.value = s;
      opt.textContent = s;
      sel.appendChild(opt);
    });

    // Stats
    updateStats(allData);

    // Render findings
    renderFindings();

    // Initial draw
    applyFilters();
    drawChart();

    // Event listeners
    sel.addEventListener("change", function () {
      currentSector = this.value;
      applyFilters();
      drawChart();
    });

    document.querySelectorAll(".toggle-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        document.querySelectorAll(".toggle-btn").forEach(function (b) { b.classList.remove("active"); });
        this.classList.add("active");
        currentScale = this.dataset.scale;
        drawChart();
      });
    });

    document.getElementById("search-input").addEventListener("input", function () {
      searchTerm = this.value.trim().toLowerCase();
      applyFilters();
      drawChart();
    });

    window.addEventListener("resize", debounce(drawChart, 200));
  });

  function applyFilters() {
    filteredData = allData.filter(function (d) {
      var sectorMatch = currentSector === "all" || d.sector === currentSector;
      var searchMatch = true;
      if (searchTerm) {
        searchMatch =
          d.symbol.toLowerCase().includes(searchTerm) ||
          d.company_name.toLowerCase().includes(searchTerm);
      }
      return sectorMatch && searchMatch;
    });
    updateStats(filteredData);
  }

  function updateStats(data) {
    document.getElementById("stat-count").textContent = data.length + " companies";
    var totalMcap = data.reduce(function (s, d) { return s + d.market_cap; }, 0);
    document.getElementById("stat-mcap-total").textContent = "Total: " + fmtDollar(totalMcap);
  }

  // ── Chart drawing ──
  function drawChart() {
    var container = document.getElementById("chart");
    container.innerHTML = "";

    var rect = document.getElementById("chart-container").getBoundingClientRect();
    var width = Math.max(rect.width, 600);
    var height = Math.max(Math.min(width * 0.55, 700), 450);

    var margin = { top: 36, right: 40, bottom: 56, left: 80 };
    var innerW = width - margin.left - margin.right;
    var innerH = height - margin.top - margin.bottom;

    var svg = d3.select(container)
      .append("svg")
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", "0 0 " + width + " " + height);

    var g = svg.append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var data = filteredData;
    if (!data.length) return;

    // Scales
    var xDomain, yDomain;
    var xScale, yScale;

    // Filter out companies with negative revenue for log scale
    var chartData = data;

    if (currentScale === "log") {
      var posRevData = chartData.filter(function (d) { return d.ttm_revenue > 0; });
      var hasNegIncome = posRevData.some(function (d) { return d.ttm_net_income < 0; });

      // Use symlog for y-axis to handle negative values
      xScale = d3.scaleLog()
        .domain(d3.extent(posRevData, function (d) { return d.ttm_revenue; }))
        .range([0, innerW])
        .nice();

      yScale = d3.scaleSymlog()
        .constant(1e8)
        .domain(d3.extent(posRevData, function (d) { return d.ttm_net_income; }))
        .range([innerH, 0])
        .nice();

      chartData = posRevData;
    } else {
      xScale = d3.scaleLinear()
        .domain([0, d3.max(chartData, function (d) { return d.ttm_revenue; }) * 1.05])
        .range([0, innerW])
        .nice();

      yScale = d3.scaleLinear()
        .domain([
          d3.min(chartData, function (d) { return d.ttm_net_income; }) * 1.1,
          d3.max(chartData, function (d) { return d.ttm_net_income; }) * 1.1
        ])
        .range([innerH, 0])
        .nice();
    }

    // Bubble size
    var sizeScale = d3.scaleSqrt()
      .domain([0, d3.max(chartData, function (d) { return d.market_cap; })])
      .range([3, 60]);

    // Get CSS colors
    var style = getComputedStyle(document.documentElement);
    var gridColor = style.getPropertyValue("--grid-color").trim();
    var axisColor = style.getPropertyValue("--axis-color").trim();
    var textColor = style.getPropertyValue("--color-text").trim();
    var mutedColor = style.getPropertyValue("--color-text-muted").trim();

    // Gridlines
    var xTickValues;
    if (currentScale === "log") {
      xTickValues = [1e8, 3e8, 1e9, 3e9, 1e10, 3e10, 1e11, 3e11, 1e12];
    }
    var xAxis = d3.axisBottom(xScale)
      .tickFormat(function (d) { return fmtDollar(d); });
    if (xTickValues) xAxis.tickValues(xTickValues.filter(function(v) { return v >= xScale.domain()[0] && v <= xScale.domain()[1]; }));
    else xAxis.ticks(8);

    var yTickValues;
    if (currentScale === "log") {
      yTickValues = [-2e10, -1e10, -5e9, 0, 5e9, 1e10, 2e10, 4e10, 6e10, 1e11, 1.4e11];
      yTickValues = yTickValues.filter(function(v) { return v >= yScale.domain()[0] && v <= yScale.domain()[1]; });
    }
    var yAxis = d3.axisLeft(yScale)
      .tickFormat(function (d) { return fmtDollar(d); });
    if (yTickValues) yAxis.tickValues(yTickValues);
    else yAxis.ticks(8);

    // X grid
    var xGridAxis = d3.axisBottom(xScale).tickSize(-innerH).tickFormat("");
    if (xTickValues) xGridAxis.tickValues(xTickValues.filter(function(v) { return v >= xScale.domain()[0] && v <= xScale.domain()[1]; }));
    else xGridAxis.ticks(8);
    g.append("g")
      .attr("class", "grid-x")
      .attr("transform", "translate(0," + innerH + ")")
      .call(xGridAxis)
      .selectAll("line")
      .attr("stroke", gridColor)
      .attr("stroke-dasharray", "2,3");

    g.selectAll(".grid-x .domain").remove();

    // Y grid
    var yGridAxis = d3.axisLeft(yScale).tickSize(-innerW).tickFormat("");
    if (yTickValues) yGridAxis.tickValues(yTickValues);
    else yGridAxis.ticks(8);
    g.append("g")
      .attr("class", "grid-y")
      .call(yGridAxis)
      .selectAll("line")
      .attr("stroke", gridColor)
      .attr("stroke-dasharray", "2,3");

    g.selectAll(".grid-y .domain").remove();

    // Zero line for y
    var zeroY = yScale(0);
    if (zeroY >= 0 && zeroY <= innerH) {
      g.append("line")
        .attr("x1", 0).attr("x2", innerW)
        .attr("y1", zeroY).attr("y2", zeroY)
        .attr("stroke", axisColor)
        .attr("stroke-width", 1.5)
        .attr("stroke-dasharray", "6,3")
        .attr("opacity", 0.6);

      g.append("text")
        .attr("x", innerW - 4)
        .attr("y", zeroY - 6)
        .attr("text-anchor", "end")
        .text("Breakeven")
        .attr("fill", mutedColor)
        .attr("font-size", "11px")
        .attr("font-weight", "500");
    }

    // Axes
    g.append("g")
      .attr("transform", "translate(0," + innerH + ")")
      .call(xAxis)
      .selectAll("text")
      .attr("fill", axisColor)
      .attr("font-size", "11px");

    g.append("g")
      .call(yAxis)
      .selectAll("text")
      .attr("fill", axisColor)
      .attr("font-size", "11px");

    g.selectAll(".domain").attr("stroke", gridColor);
    g.selectAll(".tick line").attr("stroke", gridColor);

    // Axis labels
    svg.append("text")
      .attr("x", margin.left + innerW / 2)
      .attr("y", height - 8)
      .attr("text-anchor", "middle")
      .attr("fill", mutedColor)
      .attr("font-size", "13px")
      .attr("font-weight", "500")
      .text("TTM Revenue →");

    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -(margin.top + innerH / 2))
      .attr("y", 16)
      .attr("text-anchor", "middle")
      .attr("fill", mutedColor)
      .attr("font-size", "13px")
      .attr("font-weight", "500")
      .text("↑ TTM Net Income");

    // Sort bubbles: largest underneath
    chartData.sort(function (a, b) { return b.market_cap - a.market_cap; });

    // Draw bubbles
    var tooltip = document.getElementById("tooltip");

    var bubbles = g.selectAll(".bubble")
      .data(chartData, function (d) { return d.symbol; })
      .join("circle")
      .attr("class", "bubble")
      .attr("cx", function (d) { return xScale(d.ttm_revenue); })
      .attr("cy", function (d) { return yScale(d.ttm_net_income); })
      .attr("r", 0)
      .attr("fill", function (d) { return priceChangeColor(d.pct_change_12m); })
      .attr("fill-opacity", function (d) {
        if (highlightedSymbols.length > 0) {
          return highlightedSymbols.includes(d.symbol) ? 0.85 : 0.12;
        }
        return 0.75;
      })
      .attr("stroke", function (d) {
        if (highlightedSymbols.length > 0 && highlightedSymbols.includes(d.symbol)) {
          return textColor;
        }
        return priceChangeColor(d.pct_change_12m);
      })
      .attr("stroke-width", function (d) {
        return highlightedSymbols.length > 0 && highlightedSymbols.includes(d.symbol) ? 2 : 0.5;
      })
      .attr("cursor", "pointer")
      .on("mouseenter", function (event, d) {
        d3.select(this).attr("fill-opacity", 0.95).attr("stroke", textColor).attr("stroke-width", 2);
        showTooltip(event, d);
      })
      .on("mousemove", function (event) {
        moveTooltip(event);
      })
      .on("mouseleave", function (event, d) {
        var isHL = highlightedSymbols.includes(d.symbol);
        d3.select(this)
          .attr("fill-opacity", highlightedSymbols.length > 0 ? (isHL ? 0.85 : 0.12) : 0.75)
          .attr("stroke", isHL ? textColor : priceChangeColor(d.pct_change_12m))
          .attr("stroke-width", isHL ? 2 : 0.5);
        hideTooltip();
      });

    // Animate in
    bubbles.transition()
      .duration(600)
      .delay(function (d, i) { return Math.min(i * 2, 400); })
      .ease(d3.easeCubicOut)
      .attr("r", function (d) { return sizeScale(d.market_cap); });

    // Labels for largest companies — prioritize the top 5 mega-caps
    var topByMcap = chartData
      .slice()
      .sort(function (a, b) { return b.market_cap - a.market_cap; });
    var labelData = topByMcap.slice(0, 20);

    // If we have highlighted symbols, label those instead
    if (highlightedSymbols.length > 0) {
      labelData = chartData.filter(function (d) {
        return highlightedSymbols.includes(d.symbol);
      });
    }

    // Simple collision avoidance for labels
    var placedLabels = [];
    function findLabelPos(d) {
      var cx = xScale(d.ttm_revenue);
      var cy = yScale(d.ttm_net_income);
      var r = sizeScale(d.market_cap);
      // Try positions: top, right, left, bottom-right, bottom, inside
      var topY = cy - r - 5;
      if (topY < 6) topY = cy + 4; // push inside if clipped at top
      var candidates = [
        { x: cx, y: topY, anchor: "middle" },
        { x: cx + r + 4, y: cy + 4, anchor: "start" },
        { x: cx - r - 4, y: cy + 4, anchor: "end" },
        { x: cx + r + 4, y: cy - r * 0.5, anchor: "start" },
        { x: cx - r - 4, y: cy - r * 0.5, anchor: "end" },
        { x: cx, y: cy + r + 14, anchor: "middle" },
        { x: cx, y: cy + 4, anchor: "middle" }
      ];
      for (var ci = 0; ci < candidates.length; ci++) {
        var c = candidates[ci];
        // Skip if out of chart bounds
        if (c.y < -5 || c.y > innerH + 5 || c.x < -30 || c.x > innerW + 30) continue;
        var overlap = false;
        for (var pi = 0; pi < placedLabels.length; pi++) {
          var p = placedLabels[pi];
          if (Math.abs(c.x - p.x) < 52 && Math.abs(c.y - p.y) < 16) {
            overlap = true;
            break;
          }
        }
        if (!overlap) {
          placedLabels.push({ x: c.x, y: c.y });
          return c;
        }
      }
      // Fallback: use last candidate
      var fallback = candidates[candidates.length - 1];
      placedLabels.push({ x: fallback.x, y: fallback.y });
      return fallback;
    }

    labelData.forEach(function (d) {
      var pos = findLabelPos(d);
      g.append("text")
        .attr("class", "bubble-label")
        .attr("x", pos.x)
        .attr("y", pos.y)
        .attr("text-anchor", pos.anchor)
        .attr("fill", textColor)
        .attr("font-size", "11px")
        .attr("font-weight", "600")
        .attr("pointer-events", "none")
        .attr("opacity", 0)
        .text(d.symbol)
        .transition()
        .duration(600)
        .delay(400)
        .attr("opacity", 1);
    });
  }

  function showTooltip(event, d) {
    var tt = document.getElementById("tooltip");
    var changeClass = d.pct_change_12m >= 0 ? "tt-positive" : "tt-negative";
    var marginVal = d.ttm_revenue > 0
      ? (d.ttm_net_income / d.ttm_revenue * 100).toFixed(1) + "%"
      : "N/A";

    tt.innerHTML =
      '<div class="tt-name">' + d.symbol + " — " + d.company_name + "</div>" +
      '<div class="tt-sector">' + d.sector + " · " + (d.industry || "") + "</div>" +
      '<div class="tt-grid">' +
      '<span class="tt-label">Revenue (TTM)</span><span class="tt-value">' + fmtDollar(d.ttm_revenue) + "</span>" +
      '<span class="tt-label">Net Income (TTM)</span><span class="tt-value">' + fmtDollar(d.ttm_net_income) + "</span>" +
      '<span class="tt-label">Market Cap</span><span class="tt-value">' + fmtDollar(d.market_cap) + "</span>" +
      '<span class="tt-label">12M Price Change</span><span class="tt-value ' + changeClass + '">' + fmtPct(d.pct_change_12m) + "</span>" +
      '<span class="tt-label">Net Margin</span><span class="tt-value">' + marginVal + "</span>" +
      "</div>";

    tt.classList.add("visible");
    moveTooltip(event);
  }

  function moveTooltip(event) {
    var tt = document.getElementById("tooltip");
    var container = document.getElementById("chart-container");
    var cr = container.getBoundingClientRect();
    var x = event.clientX - cr.left + 16;
    var y = event.clientY - cr.top - 10;

    if (x + 320 > cr.width) x = x - 340;
    if (y + 180 > cr.height) y = y - 180;
    if (y < 0) y = 10;

    tt.style.left = x + "px";
    tt.style.top = y + "px";
  }

  function hideTooltip() {
    document.getElementById("tooltip").classList.remove("visible");
  }

  // ── Render findings ──
  function renderFindings() {
    var grid = document.getElementById("findings-grid");
    grid.innerHTML = "";

    findings.forEach(function (f) {
      var card = document.createElement("div");
      card.className = "finding-card";
      card.innerHTML =
        '<div class="finding-number">' + f.number + "</div>" +
        '<div class="finding-title">' + f.title + "</div>" +
        '<div class="finding-desc">' + f.desc + "</div>" +
        '<div class="finding-tickers">' +
        f.tickers.map(function (t) { return '<span class="ticker-tag">' + t + "</span>"; }).join("") +
        "</div>";

      card.addEventListener("click", function () {
        highlightedSymbols = f.tickers.slice();
        drawChart();
        document.getElementById("chart-container").scrollIntoView({ behavior: "smooth", block: "start" });
      });

      grid.appendChild(card);
    });

    // Add a "clear highlights" card at the end
    var clearCard = document.createElement("div");
    clearCard.className = "finding-card";
    clearCard.style.display = "flex";
    clearCard.style.alignItems = "center";
    clearCard.style.justifyContent = "center";
    clearCard.style.opacity = "0.6";
    clearCard.innerHTML = '<div class="finding-title" style="text-align:center;color:var(--color-text-muted)">Clear Highlights</div>';
    clearCard.addEventListener("click", function () {
      highlightedSymbols = [];
      drawChart();
    });
    grid.appendChild(clearCard);
  }

  // ── Debounce ──
  function debounce(fn, delay) {
    var timer;
    return function () {
      clearTimeout(timer);
      timer = setTimeout(fn, delay);
    };
  }
})();
