/* ============================================
   SCOTUS Analytics Dashboard — Main Application
   ============================================ */

(function () {
  "use strict";

  // ---- State ----
  let ideologyData = {};
  let alignmentData = {};
  let casesData = [];
  let predictionData = {};

  let currentView = "ideology";
  let caseSort = { key: "term", dir: "desc" };
  let casePage = 1;
  const PAGE_SIZE = 50;

  // Color palette for justice lines
  const JUSTICE_COLORS = [
    "#2563eb","#dc2626","#16a34a","#d97706","#7c3aed",
    "#db2777","#0891b2","#65a30d","#ea580c","#6366f1",
    "#0d9488","#ca8a04","#be123c","#4f46e5","#059669",
    "#b91c1c","#1d4ed8","#9333ea","#c2410c","#0e7490",
    "#15803d","#a21caf","#b45309","#1e40af","#9f1239",
    "#7e22ce","#c026d3","#166534","#92400e","#4338ca",
    "#0f766e","#78350f","#6d28d9","#991b1b","#115e59",
    "#854d0e","#5b21b6","#881337","#155e75","#3f6212"
  ];

  // ---- Data Loading ----
  async function loadData() {
    const [ideology, alignment, cases, prediction] = await Promise.all([
      fetch("./ideology.json").then(r => r.json()),
      fetch("./alignment.json").then(r => r.json()),
      fetch("./cases.json").then(r => r.json()),
      fetch("./prediction.json").then(r => r.json())
    ]);

    ideologyData = ideology;
    alignmentData = alignment;
    casesData = cases;
    predictionData = prediction;

    initApp();
  }

  // ---- App Initialization ----
  function initApp() {
    setupNavigation();
    setupThemeToggle();
    setupMobileMenu();
    populateControls();
    renderIdeologyChart();
    renderAlignmentChart();
    setupCaseExplorer();
    setupPrediction();
  }

  // ---- Navigation ----
  function setupNavigation() {
    document.querySelectorAll(".nav-item").forEach(btn => {
      btn.addEventListener("click", () => {
        const view = btn.dataset.view;
        switchView(view);
      });
    });
  }

  const VIEW_TITLES = {
    ideology: ["Justice Ideology Timeline", "Ideological drift of Supreme Court justices from 1946 to present"],
    alignment: ["Voting Alignment Heatmap", "Pairwise agreement rates between justices across decades"],
    explorer: ["Case Explorer", "Search and filter 9,341 Supreme Court cases"],
    predict: ["Predict the Court", "Estimate outcomes based on historical voting patterns"]
  };

  function switchView(view) {
    currentView = view;
    document.querySelectorAll(".nav-item").forEach(b => b.classList.toggle("active", b.dataset.view === view));
    document.querySelectorAll(".view").forEach(v => v.classList.toggle("active", v.id === `view-${view}`));
    document.getElementById("viewTitle").textContent = VIEW_TITLES[view][0];
    document.getElementById("viewSubtitle").textContent = VIEW_TITLES[view][1];

    // Close mobile menu
    document.getElementById("sidebar").classList.remove("open");

    // Trigger re-render for resize-dependent charts
    if (view === "ideology") renderIdeologyChart();
    if (view === "alignment") renderAlignmentChart();
    if (view === "explorer") renderCaseExplorer();
  }

  // ---- Theme Toggle ----
  function setupThemeToggle() {
    const toggle = document.querySelector("[data-theme-toggle]");
    const root = document.documentElement;
    let theme = matchMedia("(prefers-color-scheme:dark)").matches ? "dark" : "light";
    root.setAttribute("data-theme", theme);

    toggle.addEventListener("click", () => {
      theme = theme === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", theme);
      toggle.innerHTML = theme === "dark"
        ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
        : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';

      // Re-render charts with updated colors
      if (currentView === "ideology") renderIdeologyChart();
      if (currentView === "alignment") renderAlignmentChart();
      if (currentView === "explorer") renderCaseExplorer();
    });
  }

  function setupMobileMenu() {
    document.getElementById("mobileMenuBtn").addEventListener("click", () => {
      document.getElementById("sidebar").classList.toggle("open");
    });
  }

  // ---- Populate Controls ----
  function populateControls() {
    // Ideology highlight select
    const highlightSel = document.getElementById("ideologyHighlight");
    const justiceList = Object.entries(ideologyData)
      .sort((a, b) => b[1].endTerm - a[1].endTerm);
    justiceList.forEach(([key, j]) => {
      const opt = document.createElement("option");
      opt.value = key;
      opt.textContent = j.name;
      highlightSel.appendChild(opt);
    });

    // Alignment decades
    const decadeSel = document.getElementById("alignmentDecade");
    const decades = Object.keys(alignmentData).sort((a, b) => b - a);
    decades.forEach(d => {
      const opt = document.createElement("option");
      opt.value = d;
      opt.textContent = `${d}s`;
      decadeSel.appendChild(opt);
    });

    // Case issue areas
    const issueSel = document.getElementById("caseIssue");
    const issueAreas = [...new Set(casesData.map(c => c.ia))].sort();
    issueAreas.forEach(area => {
      if (area === "Unknown") return;
      const opt = document.createElement("option");
      opt.value = area;
      opt.textContent = area;
      issueSel.appendChild(opt);
    });

    // Predict issue areas
    const predictIssueSel = document.getElementById("predictIssue");
    Object.keys(predictionData.issueStats).sort().forEach(area => {
      const opt = document.createElement("option");
      opt.value = area;
      opt.textContent = area;
      predictIssueSel.appendChild(opt);
    });

    // Event listeners for controls
    document.getElementById("ideologyEra").addEventListener("change", renderIdeologyChart);
    highlightSel.addEventListener("change", renderIdeologyChart);
    decadeSel.addEventListener("change", renderAlignmentChart);
    document.getElementById("alignmentSort").addEventListener("change", renderAlignmentChart);
  }

  // ============================================
  //  IDEOLOGY TIMELINE
  // ============================================

  let ideologyHighlighted = null;

  function renderIdeologyChart() {
    const container = document.getElementById("ideologyChart");
    container.innerHTML = "";

    const era = document.getElementById("ideologyEra").value;
    const highlight = document.getElementById("ideologyHighlight").value;

    // Determine term range
    let minTerm = 1946, maxTerm = 2024;
    if (era === "vinson") { minTerm = 1946; maxTerm = 1953; }
    else if (era === "warren") { minTerm = 1953; maxTerm = 1969; }
    else if (era === "burger") { minTerm = 1969; maxTerm = 1986; }
    else if (era === "rehnquist") { minTerm = 1986; maxTerm = 2005; }
    else if (era === "roberts") { minTerm = 2005; maxTerm = 2024; }

    // Filter justices
    const justices = Object.entries(ideologyData)
      .filter(([, j]) => j.endTerm >= minTerm && j.startTerm <= maxTerm)
      .sort((a, b) => a[1].startTerm - b[1].startTerm);

    const rect = container.getBoundingClientRect();
    const width = Math.max(rect.width - 32, 400);
    const numJustices = Object.entries(ideologyData)
      .filter(([, j]) => j.endTerm >= minTerm && j.startTerm <= maxTerm).length;
    const height = numJustices > 20 ? 600 : 460;
    const margin = { top: 40, right: 140, bottom: 40, left: 80 };

    const svg = d3.select(container)
      .append("svg")
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", `0 0 ${width} ${height}`);

    const xScale = d3.scaleLinear()
      .domain([minTerm, maxTerm])
      .range([margin.left, width - margin.right]);

    const yScale = d3.scaleLinear()
      .domain([-1, 1])
      .range([height - margin.bottom, margin.top]);

    // Get computed CSS colors
    const style = getComputedStyle(document.documentElement);
    const textColor = style.getPropertyValue("--color-text-muted").trim();
    const dividerColor = style.getPropertyValue("--color-divider").trim();
    const bgColor = style.getPropertyValue("--color-surface").trim();

    // Grid lines
    const yTicks = [-1, -0.5, 0, 0.5, 1];
    svg.selectAll(".grid-line")
      .data(yTicks)
      .enter()
      .append("line")
      .attr("x1", margin.left)
      .attr("x2", width - margin.right)
      .attr("y1", d => yScale(d))
      .attr("y2", d => yScale(d))
      .attr("stroke", dividerColor)
      .attr("stroke-dasharray", d => d === 0 ? "none" : "4,4")
      .attr("stroke-width", d => d === 0 ? 1.5 : 0.5);

    // Zero line label
    svg.append("text")
      .attr("x", margin.left - 8)
      .attr("y", yScale(0))
      .attr("dy", "0.35em")
      .attr("text-anchor", "end")
      .attr("fill", textColor)
      .attr("font-size", "11px")
      .text("Center");

    // Y-axis labels
    svg.append("text")
      .attr("x", margin.left - 8)
      .attr("y", yScale(1))
      .attr("dy", "0.35em")
      .attr("text-anchor", "end")
      .attr("fill", style.getPropertyValue("--color-conservative").trim())
      .attr("font-size", "10px")
      .attr("font-weight", "600")
      .text("Conservative");

    svg.append("text")
      .attr("x", margin.left - 8)
      .attr("y", yScale(-1))
      .attr("dy", "0.35em")
      .attr("text-anchor", "end")
      .attr("fill", style.getPropertyValue("--color-liberal").trim())
      .attr("font-size", "10px")
      .attr("font-weight", "600")
      .text("Liberal");

    // X-axis
    const xAxis = d3.axisBottom(xScale)
      .tickFormat(d3.format("d"))
      .ticks(Math.min(maxTerm - minTerm, 10));

    svg.append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(xAxis)
      .selectAll("text")
      .attr("fill", textColor)
      .attr("font-size", "11px");

    svg.selectAll(".domain").attr("stroke", dividerColor);
    svg.selectAll(".tick line").attr("stroke", dividerColor);

    // Tooltip
    const tooltip = d3.select(container)
      .append("div")
      .attr("class", "chart-tooltip");

    // Line generator
    const line = d3.line()
      .x(d => xScale(d.term))
      .y(d => yScale(d.score))
      .curve(d3.curveCatmullRom.alpha(0.5));

    // Collect end labels for collision avoidance
    const endLabels = [];

    // Draw justice lines
    justices.forEach(([key, justice], i) => {
      const data = justice.timeline.filter(t => t.term >= minTerm && t.term <= maxTerm);
      if (data.length < 2) return;

      const color = JUSTICE_COLORS[i % JUSTICE_COLORS.length];
      const isHighlighted = highlight !== "none" && key === highlight;
      const isDimmed = highlight !== "none" && key !== highlight;

      svg.append("path")
        .datum(data)
        .attr("d", line)
        .attr("fill", "none")
        .attr("stroke", color)
        .attr("stroke-width", isHighlighted ? 3 : 1.5)
        .attr("opacity", isDimmed ? 0.12 : (isHighlighted ? 1 : 0.6))
        .attr("class", "justice-line")
        .attr("data-justice", key);

      // Collect end label
      const lastPt = data[data.length - 1];
      if (!isDimmed || isHighlighted) {
        endLabels.push({
          x: xScale(lastPt.term) + 6,
          y: yScale(lastPt.score),
          name: getShortName(justice.name),
          color: color,
          weight: isHighlighted ? "700" : "500",
          opacity: isDimmed ? 0.2 : 1
        });
      }

      // Hover circles
      svg.selectAll(`.dot-${i}`)
        .data(data)
        .enter()
        .append("circle")
        .attr("cx", d => xScale(d.term))
        .attr("cy", d => yScale(d.score))
        .attr("r", isHighlighted ? 4 : 2.5)
        .attr("fill", color)
        .attr("opacity", isDimmed ? 0.1 : 0)
        .attr("class", "justice-dot")
        .on("mouseenter", function (event, d) {
          d3.select(this).attr("opacity", 1).attr("r", 5);
          tooltip
            .html(`
              <div class="tooltip-title">${justice.name}</div>
              <div class="tooltip-row"><span>Term</span><span class="tooltip-value">${d.term}–${d.term + 1}</span></div>
              <div class="tooltip-row"><span>Ideology Score</span><span class="tooltip-value">${d.score > 0 ? "+" : ""}${d.score.toFixed(2)}</span></div>
              <div class="tooltip-row"><span>Liberal Votes</span><span class="tooltip-value">${d.liberal_pct}%</span></div>
              <div class="tooltip-row"><span>Conservative Votes</span><span class="tooltip-value">${d.conservative_pct}%</span></div>
              <div class="tooltip-row"><span>Total Votes</span><span class="tooltip-value">${d.total_votes}</span></div>
            `)
            .classed("visible", true)
            .style("left", `${event.offsetX + 15}px`)
            .style("top", `${event.offsetY - 10}px`);
        })
        .on("mouseleave", function () {
          d3.select(this).attr("opacity", isDimmed ? 0.1 : 0).attr("r", isHighlighted ? 4 : 2.5);
          tooltip.classed("visible", false);
        });
    });

    // Render end labels with collision avoidance
    // In "All Eras" with many justices, limit to current/recent justices
    const CURRENT_JUSTICES = ["JGRoberts","CThomas","SAAlito","SSotomayor","EKagan","NMGorsuch","BMKavanaugh","ACBarrett","KBJackson"];
    let labelsToRender = endLabels;
    if (era === "all" && endLabels.length > 15 && highlight === "none") {
      // Show only justices active in the last 20 years
      labelsToRender = endLabels.filter(lbl =>
        CURRENT_JUSTICES.some(cj => getShortName(ideologyData[cj]?.name || "") === lbl.name) ||
        lbl.y >= yScale(0.8) && lbl.y <= yScale(-0.8)
      );
      // Actually simpler: just show labels for justices whose last term is within 20 years of max
      labelsToRender = [];
      justices.forEach(([key, justice]) => {
        const lastTerm = Math.min(justice.endTerm, maxTerm);
        const isRecent = lastTerm >= maxTerm - 20;
        const isCurrent = CURRENT_JUSTICES.includes(key);
        if (isRecent || isCurrent) {
          const match = endLabels.find(l => l.name === getShortName(justice.name));
          if (match) labelsToRender.push(match);
        }
      });
    }

    // Sort by y, nudge apart, clamp within chart area
    labelsToRender.sort((a, b) => a.y - b.y);
    const labelHeight = 11;
    const yMin = margin.top;
    const yMax = height - margin.bottom - 4;
    for (let i = 1; i < labelsToRender.length; i++) {
      const prev = labelsToRender[i - 1];
      const curr = labelsToRender[i];
      if (curr.y - prev.y < labelHeight) {
        curr.y = prev.y + labelHeight;
      }
    }
    // If labels overflow bottom, push all up
    if (labelsToRender.length > 0) {
      const lastLabel = labelsToRender[labelsToRender.length - 1];
      if (lastLabel.y > yMax) {
        const overflow = lastLabel.y - yMax;
        labelsToRender.forEach(lbl => { lbl.y -= overflow; });
      }
      // Clamp top
      if (labelsToRender[0].y < yMin) {
        const shift = yMin - labelsToRender[0].y;
        labelsToRender.forEach(lbl => { lbl.y += shift; });
      }
    }

    labelsToRender.forEach(lbl => {
      svg.append("text")
        .attr("x", lbl.x)
        .attr("y", Math.max(yMin, Math.min(yMax, lbl.y)))
        .attr("dy", "0.35em")
        .attr("fill", lbl.color)
        .attr("font-size", "10px")
        .attr("font-weight", lbl.weight)
        .attr("opacity", lbl.opacity)
        .text(lbl.name);
    });

    // Legend
    renderIdeologyLegend(justices, highlight);
  }

  function renderIdeologyLegend(justices, highlight) {
    const legend = document.getElementById("ideologyLegend");
    legend.innerHTML = "";

    justices.forEach(([key, justice], i) => {
      const color = JUSTICE_COLORS[i % JUSTICE_COLORS.length];
      const isHighlighted = highlight !== "none" && key === highlight;
      const isDimmed = highlight !== "none" && key !== highlight;

      const item = document.createElement("div");
      item.className = `legend-item${isHighlighted ? " highlighted" : ""}${isDimmed ? " dimmed" : ""}`;
      item.innerHTML = `
        <span class="legend-swatch" style="background:${color}"></span>
        <span class="legend-name">${getShortName(justice.name)}</span>
      `;
      item.addEventListener("click", () => {
        const sel = document.getElementById("ideologyHighlight");
        sel.value = sel.value === key ? "none" : key;
        renderIdeologyChart();
      });
      legend.appendChild(item);
    });
  }

  // ============================================
  //  ALIGNMENT HEATMAP
  // ============================================

  function renderAlignmentChart() {
    const container = document.getElementById("alignmentChart");
    container.innerHTML = "";

    const decade = document.getElementById("alignmentDecade").value;
    const sortBy = document.getElementById("alignmentSort").value;

    const data = alignmentData[decade];
    if (!data) return;

    let justices = [...data.justices];

    // Sort justices
    if (sortBy === "ideology" && ideologyData) {
      justices.sort((a, b) => {
        const aScore = ideologyData[a]?.avgScore ?? 0;
        const bScore = ideologyData[b]?.avgScore ?? 0;
        return aScore - bScore;
      });
    }

    const n = justices.length;
    const cellSize = Math.min(Math.max(Math.floor((container.getBoundingClientRect().width - 160) / (n + 1)), 28), 52);
    const labelWidth = 110;
    const margin = { top: labelWidth + 10, right: 20, bottom: 20, left: labelWidth + 10 };
    const chartW = margin.left + n * cellSize + margin.right;
    const chartH = margin.top + n * cellSize + margin.bottom;

    const svg = d3.select(container)
      .append("svg")
      .attr("width", chartW)
      .attr("height", chartH);

    const style = getComputedStyle(document.documentElement);
    const textColor = style.getPropertyValue("--color-text-muted").trim();
    const bgColor = style.getPropertyValue("--color-surface").trim();

    // Color scale: low agreement (blue) -> high agreement (warm)
    const colorScale = d3.scaleSequential()
      .domain([45, 95])
      .interpolator(d3.interpolateRgbBasis(["#2563eb", "#93c5fd", "#fefce8", "#fca5a5", "#dc2626"]));

    const tooltip = document.getElementById("alignmentTooltip");

    // Draw cells
    justices.forEach((j1, i) => {
      justices.forEach((j2, j) => {
        const val = data.matrix[j1]?.[j2];
        if (val == null) return;

        const rect = svg.append("rect")
          .attr("x", margin.left + j * cellSize)
          .attr("y", margin.top + i * cellSize)
          .attr("width", cellSize - 1)
          .attr("height", cellSize - 1)
          .attr("rx", 2)
          .attr("fill", i === j ? bgColor : colorScale(val))
          .attr("stroke", i === j ? style.getPropertyValue("--color-divider").trim() : "none")
          .style("cursor", i !== j ? "pointer" : "default");

        if (i !== j) {
          rect.on("mouseenter", function (event) {
            const name1 = data.justiceNames[j1] || j1;
            const name2 = data.justiceNames[j2] || j2;
            tooltip.innerHTML = `
              <div style="font-weight:600;color:var(--color-text);margin-bottom:4px">${getShortName(name1)} & ${getShortName(name2)}</div>
              <div style="color:var(--color-text-muted)">Agreement: <span style="font-weight:700;color:var(--color-text)">${val}%</span></div>
            `;
            tooltip.classList.add("visible");
            tooltip.style.left = `${event.clientX + 12}px`;
            tooltip.style.top = `${event.clientY - 10}px`;
          })
            .on("mousemove", function (event) {
              tooltip.style.left = `${event.clientX + 12}px`;
              tooltip.style.top = `${event.clientY - 10}px`;
            })
            .on("mouseleave", function () {
              tooltip.classList.remove("visible");
            });
        }

        // Value text for larger cells
        if (cellSize >= 36 && i !== j && val != null) {
          // Determine text color based on cell brightness
          const textFill = val > 72 ? "#1a1816" : "#ffffff";
          svg.append("text")
            .attr("x", margin.left + j * cellSize + cellSize / 2 - 0.5)
            .attr("y", margin.top + i * cellSize + cellSize / 2)
            .attr("dy", "0.35em")
            .attr("text-anchor", "middle")
            .attr("fill", textFill)
            .attr("font-size", "9px")
            .attr("font-weight", "600")
            .attr("font-variant-numeric", "tabular-nums")
            .attr("pointer-events", "none")
            .text(Math.round(val));
        }
      });
    });

    // Row labels (left)
    justices.forEach((j, i) => {
      const name = getShortName(data.justiceNames[j] || j);
      svg.append("text")
        .attr("x", margin.left - 6)
        .attr("y", margin.top + i * cellSize + cellSize / 2)
        .attr("dy", "0.35em")
        .attr("text-anchor", "end")
        .attr("fill", textColor)
        .attr("font-size", "11px")
        .attr("font-weight", "500")
        .text(name);
    });

    // Column labels (top, rotated)
    justices.forEach((j, i) => {
      const name = getShortName(data.justiceNames[j] || j);
      svg.append("text")
        .attr("x", 0)
        .attr("y", 0)
        .attr("transform", `translate(${margin.left + i * cellSize + cellSize / 2},${margin.top - 6}) rotate(-55)`)
        .attr("text-anchor", "start")
        .attr("fill", textColor)
        .attr("font-size", "11px")
        .attr("font-weight", "500")
        .text(name);
    });

    // Color legend
    const legendW = 200;
    const legendH = 10;
    const legendX = margin.left;
    const legendY = chartH - 10;

    const defs = svg.append("defs");
    const gradient = defs.append("linearGradient")
      .attr("id", "heatmap-gradient");

    [0, 25, 50, 75, 100].forEach(pct => {
      gradient.append("stop")
        .attr("offset", `${pct}%`)
        .attr("stop-color", colorScale(45 + (95 - 45) * pct / 100));
    });

    svg.append("rect")
      .attr("x", legendX)
      .attr("y", legendY)
      .attr("width", legendW)
      .attr("height", legendH)
      .attr("rx", 3)
      .attr("fill", "url(#heatmap-gradient)");

    svg.append("text").attr("x", legendX).attr("y", legendY - 4).attr("fill", textColor).attr("font-size", "9px").text("45%");
    svg.append("text").attr("x", legendX + legendW).attr("y", legendY - 4).attr("fill", textColor).attr("font-size", "9px").attr("text-anchor", "end").text("95%");
    svg.append("text").attr("x", legendX + legendW / 2).attr("y", legendY - 4).attr("fill", textColor).attr("font-size", "9px").attr("text-anchor", "middle").text("Agreement");
  }

  // ============================================
  //  CASE EXPLORER
  // ============================================

  function setupCaseExplorer() {
    const inputs = ["caseSearch", "caseIssue", "caseDirection", "termStart", "termEnd", "caseUnanimous"];
    inputs.forEach(id => {
      document.getElementById(id).addEventListener("input", () => {
        casePage = 1;
        renderCaseExplorer();
      });
      document.getElementById(id).addEventListener("change", () => {
        casePage = 1;
        renderCaseExplorer();
      });
    });

    // Table sorting
    document.querySelectorAll(".sortable").forEach(th => {
      th.addEventListener("click", () => {
        const key = th.dataset.sort;
        if (caseSort.key === key) {
          caseSort.dir = caseSort.dir === "asc" ? "desc" : "asc";
        } else {
          caseSort.key = key;
          caseSort.dir = key === "term" ? "desc" : "asc";
        }
        renderCaseExplorer();
      });
    });

    renderCaseExplorer();
  }

  function getFilteredCases() {
    const search = document.getElementById("caseSearch").value.toLowerCase();
    const issue = document.getElementById("caseIssue").value;
    const direction = document.getElementById("caseDirection").value;
    const termStart = parseInt(document.getElementById("termStart").value) || 1946;
    const termEnd = parseInt(document.getElementById("termEnd").value) || 2024;
    const unanimous = document.getElementById("caseUnanimous").value;

    return casesData.filter(c => {
      if (search && !c.n.toLowerCase().includes(search) && !(c.ci||'').toLowerCase().includes(search)) return false;
      if (issue !== "all" && c.ia !== issue) return false;
      if (direction !== "all" && c.dc !== parseInt(direction)) return false;
      if (c.t < termStart || c.t > termEnd) return false;
      if (unanimous === "yes" && !c.u) return false;
      if (unanimous === "no" && c.u) return false;
      return true;
    });
  }

  function renderCaseExplorer() {
    const filtered = getFilteredCases();

    // Map short keys for sorting
    const sortKeyMap = { term: 't', name: 'n', issueArea: 'ia', direction: 'd', margin: 'm', chief: 'ch' };
    const sk = sortKeyMap[caseSort.key] || caseSort.key;

    // Sort
    filtered.sort((a, b) => {
      let va = a[sk];
      let vb = b[sk];
      if (typeof va === "string") va = va.toLowerCase();
      if (typeof vb === "string") vb = vb.toLowerCase();
      if (va < vb) return caseSort.dir === "asc" ? -1 : 1;
      if (va > vb) return caseSort.dir === "asc" ? 1 : -1;
      return 0;
    });

    // Stats
    const stats = document.getElementById("explorerStats");
    const liberalCount = filtered.filter(c => c.dc === 2).length;
    const conservativeCount = filtered.filter(c => c.dc === 1).length;
    const unanimousCount = filtered.filter(c => c.u).length;

    stats.innerHTML = `
      <div class="stat-card"><div class="stat-value">${filtered.length.toLocaleString()}</div><div class="stat-label">Cases</div></div>
      <div class="stat-card"><div class="stat-value" style="color:var(--color-liberal)">${liberalCount.toLocaleString()}</div><div class="stat-label">Liberal</div></div>
      <div class="stat-card"><div class="stat-value" style="color:var(--color-conservative)">${conservativeCount.toLocaleString()}</div><div class="stat-label">Conservative</div></div>
      <div class="stat-card"><div class="stat-value">${unanimousCount.toLocaleString()}</div><div class="stat-label">Unanimous</div></div>
    `;

    // Mini charts
    renderExplorerCharts(filtered);

    // Table headers
    document.querySelectorAll(".sortable").forEach(th => {
      th.classList.remove("sorted-asc", "sorted-desc");
      if (th.dataset.sort === caseSort.key) {
        th.classList.add(caseSort.dir === "asc" ? "sorted-asc" : "sorted-desc");
      }
    });

    // Paginate
    const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
    if (casePage > totalPages) casePage = totalPages;
    const start = (casePage - 1) * PAGE_SIZE;
    const pageCases = filtered.slice(start, start + PAGE_SIZE);

    // Render rows
    const tbody = document.getElementById("caseTableBody");
    tbody.innerHTML = pageCases.map(c => `
      <tr>
        <td>${c.t}</td>
        <td class="case-name-cell" title="${escapeHtml(c.n)}">${escapeHtml(c.n)}</td>
        <td>${c.ia}</td>
        <td><span class="tag tag-${c.d.toLowerCase()}">${c.d}</span></td>
        <td>${c.m}</td>
        <td>${c.ch}</td>
      </tr>
    `).join("");

    // Pagination
    renderPagination(totalPages);
  }

  function renderExplorerCharts(filtered) {
    const chartsDiv = document.getElementById("explorerCharts");
    chartsDiv.innerHTML = `
      <div class="mini-chart" id="issueDistChart"><div class="mini-chart-title">Cases by Issue Area</div></div>
      <div class="mini-chart" id="timelineChart"><div class="mini-chart-title">Decisions Over Time</div></div>
    `;

    // Issue area distribution (horizontal bars)
    const issueCounts = {};
    filtered.forEach(c => {
      issueCounts[c.ia] = (issueCounts[c.ia] || 0) + 1;
    });

    const issueEntries = Object.entries(issueCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);
    const maxCount = Math.max(...issueEntries.map(e => e[1]), 1);

    const issueChart = document.getElementById("issueDistChart");
    const barContainer = document.createElement("div");
    barContainer.style.cssText = "display:flex;flex-direction:column;gap:4px;";

    issueEntries.forEach(([area, count]) => {
      const row = document.createElement("div");
      row.style.cssText = "display:flex;align-items:center;gap:8px;font-size:12px;";
      row.innerHTML = `
        <span style="width:120px;text-align:right;color:var(--color-text-muted);flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${area}">${area}</span>
        <div style="flex:1;height:16px;background:var(--color-surface-offset);border-radius:3px;overflow:hidden">
          <div style="width:${(count / maxCount * 100)}%;height:100%;background:var(--color-primary);border-radius:3px;transition:width 400ms"></div>
        </div>
        <span style="min-width:36px;text-align:right;font-weight:600;color:var(--color-text);font-variant-numeric:tabular-nums">${count}</span>
      `;
      barContainer.appendChild(row);
    });
    issueChart.appendChild(barContainer);

    // Timeline sparkline (decisions per term)
    const termCounts = {};
    filtered.forEach(c => {
      termCounts[c.t] = (termCounts[c.t] || 0) + 1;
    });

    const termData = Object.entries(termCounts)
      .map(([t, c]) => ({ term: parseInt(t), count: c }))
      .sort((a, b) => a.term - b.term);

    if (termData.length > 1) {
      const tlChart = document.getElementById("timelineChart");
      const svgW = tlChart.getBoundingClientRect().width - 32;
      const svgH = 140;

      const svg = d3.select(tlChart)
        .append("svg")
        .attr("width", svgW)
        .attr("height", svgH);

      const xScale = d3.scaleLinear()
        .domain(d3.extent(termData, d => d.term))
        .range([30, svgW - 10]);

      const yScale = d3.scaleLinear()
        .domain([0, d3.max(termData, d => d.count)])
        .range([svgH - 20, 5]);

      const area = d3.area()
        .x(d => xScale(d.term))
        .y0(svgH - 20)
        .y1(d => yScale(d.count))
        .curve(d3.curveBasis);

      const style = getComputedStyle(document.documentElement);

      svg.append("path")
        .datum(termData)
        .attr("d", area)
        .attr("fill", style.getPropertyValue("--color-primary").trim())
        .attr("opacity", 0.15);

      const lineGen = d3.line()
        .x(d => xScale(d.term))
        .y(d => yScale(d.count))
        .curve(d3.curveBasis);

      svg.append("path")
        .datum(termData)
        .attr("d", lineGen)
        .attr("fill", "none")
        .attr("stroke", style.getPropertyValue("--color-primary").trim())
        .attr("stroke-width", 2);

      // Simple x-axis labels
      const ticks = xScale.ticks(5);
      ticks.forEach(t => {
        svg.append("text")
          .attr("x", xScale(t))
          .attr("y", svgH - 4)
          .attr("text-anchor", "middle")
          .attr("fill", style.getPropertyValue("--color-text-faint").trim())
          .attr("font-size", "10px")
          .text(t);
      });
    }
  }

  function renderPagination(totalPages) {
    const pag = document.getElementById("pagination");
    if (totalPages <= 1) { pag.innerHTML = ""; return; }

    let html = `<button class="page-btn" ${casePage <= 1 ? "disabled" : ""} data-page="${casePage - 1}">‹</button>`;

    const range = [];
    range.push(1);
    for (let i = Math.max(2, casePage - 2); i <= Math.min(totalPages - 1, casePage + 2); i++) {
      range.push(i);
    }
    if (totalPages > 1) range.push(totalPages);

    const unique = [...new Set(range)].sort((a, b) => a - b);
    let prev = 0;
    unique.forEach(p => {
      if (p - prev > 1) html += `<span style="color:var(--color-text-faint)">…</span>`;
      html += `<button class="page-btn${p === casePage ? " active" : ""}" data-page="${p}">${p}</button>`;
      prev = p;
    });

    html += `<button class="page-btn" ${casePage >= totalPages ? "disabled" : ""} data-page="${casePage + 1}">›</button>`;
    pag.innerHTML = html;

    pag.querySelectorAll(".page-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const p = parseInt(btn.dataset.page);
        if (p >= 1 && p <= totalPages) {
          casePage = p;
          renderCaseExplorer();
        }
      });
    });
  }

  // ============================================
  //  PREDICT THE COURT
  // ============================================

  function setupPrediction() {
    document.getElementById("predictBtn").addEventListener("click", runPrediction);
    renderHistoryCards();
  }

  function runPrediction() {
    const issueArea = document.getElementById("predictIssue").value;
    const lean = document.querySelector("input[name='predictLean']:checked")?.value || "conservative";

    if (!issueArea) {
      return;
    }

    const results = document.getElementById("predictResults");
    const issueStats = predictionData.issueStats[issueArea];
    const recentJustices = predictionData.recentJustices;
    const justiceIssueStats = predictionData.justiceIssueStats;

    if (!issueStats || !recentJustices) {
      results.innerHTML = '<div class="predict-placeholder"><p>Insufficient data for prediction</p></div>';
      return;
    }

    // Current justices (as of 2024 term)
    const currentJusticeKeys = [
      "JGRoberts", "CThomas", "SAAlito", "SSotomayor", "EKagan",
      "NMGorsuch", "BMKavanaugh", "ACBarrett", "KBJackson"
    ];

    // Predict each justice's vote
    const justiceVotes = [];
    Object.entries(recentJustices)
      .filter(([key]) => currentJusticeKeys.includes(key))
      .forEach(([key, justice]) => {
      // Get issue-specific stats if available
      const issueSpecific = justiceIssueStats[key]?.[issueArea];
      const conservativePct = issueSpecific ? issueSpecific.conservativePct : justice.conservativePct;

      // Predict: for conservative argument, conservative justices more likely to vote in favor
      let voteProb;
      if (lean === "conservative") {
        voteProb = conservativePct / 100;
      } else {
        voteProb = 1 - conservativePct / 100;
      }

      justiceVotes.push({
        name: justice.name,
        key: key,
        probability: voteProb,
        conservativePct: conservativePct,
        predictedVote: lean === "conservative" ? (voteProb > 0.5 ? "conservative" : "liberal") : (voteProb > 0.5 ? "liberal" : "conservative")
      });
    });

    // Sort by probability
    justiceVotes.sort((a, b) => b.probability - a.probability);

    // Count predicted votes
    const inFavor = justiceVotes.filter(j => j.probability > 0.5).length;
    const against = justiceVotes.length - inFavor;
    const petitionerWins = inFavor > against;

    // Historical base rate
    const baseRate = lean === "conservative" ? issueStats.conservativePct : issueStats.liberalPct;

    // Confidence
    const avgProb = justiceVotes.reduce((s, j) => s + j.probability, 0) / justiceVotes.length;
    const confidence = Math.round(Math.max(avgProb, 1 - avgProb) * 100);

    results.innerHTML = `
      <div class="result-header">
        <div>
          <div class="result-verdict" style="color:var(--color-${petitionerWins ? (lean === "conservative" ? "conservative" : "liberal") : (lean === "conservative" ? "liberal" : "conservative")})">
            Likely ${petitionerWins ? inFavor : against}–${petitionerWins ? against : inFavor} ${petitionerWins ? "for" : "against"} petitioner
          </div>
          <div class="result-confidence">
            ${confidence}% model confidence · ${baseRate}% historical base rate for ${lean} outcomes in ${issueArea}
          </div>
        </div>
      </div>
      <div class="justice-votes">
        ${justiceVotes.map(j => `
          <div class="justice-vote-card vote-${j.predictedVote}">
            <span>${getShortName(j.name)}</span>
            <span class="justice-pct">${Math.round(j.probability * 100)}%</span>
          </div>
        `).join("")}
      </div>
    `;
  }

  function renderHistoryCards() {
    const cards = document.getElementById("historyCards");
    const issueStats = predictionData.issueStats;

    const html = Object.entries(issueStats)
      .sort((a, b) => b[1].total - a[1].total)
      .slice(0, 8)
      .map(([area, stats]) => `
        <div class="history-card">
          <div class="history-card-title">${area}</div>
          <div class="history-bar">
            <div class="history-bar-liberal" style="width:${stats.liberalPct}%"></div>
            <div class="history-bar-conservative" style="width:${stats.conservativePct}%"></div>
          </div>
          <div class="history-stats">
            <span>Liberal <span class="history-stat-value">${stats.liberalPct}%</span></span>
            <span>${stats.total} cases</span>
            <span>Conservative <span class="history-stat-value">${stats.conservativePct}%</span></span>
          </div>
        </div>
      `).join("");

    cards.innerHTML = html;
  }

  // ---- Utility ----
  function getShortName(fullName) {
    // Extract a meaningful last name from full justice name
    const parts = fullName.replace(/\s+(Jr\.|Sr\.|II|III|IV)$/i, "").trim().split(" ");
    return parts[parts.length - 1];
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // ---- Boot ----
  loadData().catch(err => {
    console.error("Failed to load data:", err);
    document.getElementById("main").innerHTML =
      '<div style="padding:2rem;color:var(--color-error)">Failed to load data. Please refresh.</div>';
  });
})();
