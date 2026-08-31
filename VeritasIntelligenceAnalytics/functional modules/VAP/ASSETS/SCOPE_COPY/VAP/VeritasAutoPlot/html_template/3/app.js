/* eslint-disable no-unused-vars */
// MegaCap 50 Dashboard — Main Application
(function () {
  "use strict";

  // ========== CHART.JS DEFAULTS ==========
  const CHART_COLORS = [
    "#1a8f94", "#b45a2e", "#1b4a50", "#a2d8dd",
    "#944454", "#e6a832", "#6e8a48", "#8b6b3e",
    "#3a7ca5", "#c76b4a", "#4a9fa4", "#d4956b"
  ];

  function getChartDefaults() {
    const style = getComputedStyle(document.documentElement);
    return {
      textColor: style.getPropertyValue("--color-text-muted").trim() || "#6b6960",
      gridColor: style.getPropertyValue("--color-divider").trim() || "#e8e5df",
      fontFamily: "'DM Sans', sans-serif",
    };
  }

  function applyChartDefaults() {
    const d = getChartDefaults();
    Chart.defaults.font.family = d.fontFamily;
    Chart.defaults.font.size = 12;
    Chart.defaults.color = d.textColor;
    Chart.defaults.plugins.legend.display = false;
    Chart.defaults.plugins.tooltip.backgroundColor = "rgba(26,25,23,0.9)";
    Chart.defaults.plugins.tooltip.titleFont = { size: 12, weight: "600" };
    Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };
    Chart.defaults.plugins.tooltip.padding = { top: 8, bottom: 8, left: 12, right: 12 };
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
    Chart.defaults.plugins.tooltip.displayColors = false;
    Chart.defaults.animation = { duration: 700, easing: "easeOutQuart" };
    Chart.defaults.scales.x = Chart.defaults.scales.x || {};
    Chart.defaults.scales.y = Chart.defaults.scales.y || {};
  }

  // ========== STATE ==========
  var state = {
    activeView: "overview",
    activeCompany: null,
    activeFilter: "all",
    compareMetric: null,
    compareCompanies: [],
    charts: [],
    compareChart: null,
  };

  // ========== DOM REFS ==========
  var $ = function (sel) { return document.querySelector(sel); };
  var $$ = function (sel) { return document.querySelectorAll(sel); };

  // ========== DARK MODE ==========
  (function initTheme() {
    var toggle = $("[data-theme-toggle]");
    var html = document.documentElement;
    var isDark = matchMedia("(prefers-color-scheme: dark)").matches;
    var theme = isDark ? "dark" : "light";
    html.setAttribute("data-theme", theme);

    if (toggle) {
      updateToggleIcon(toggle, theme);
      toggle.addEventListener("click", function () {
        theme = theme === "dark" ? "light" : "dark";
        html.setAttribute("data-theme", theme);
        updateToggleIcon(toggle, theme);
        applyChartDefaults();
        rebuildCurrentView();
      });
    }

    function updateToggleIcon(btn, t) {
      btn.innerHTML = t === "dark"
        ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
        : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
      btn.setAttribute("aria-label", "Switch to " + (t === "dark" ? "light" : "dark") + " mode");
    }
  })();

  // ========== SIDEBAR ==========
  (function initSidebar() {
    var menuBtn = $("#menuBtn");
    var sidebar = $("#sidebar");
    var closeBtn = $("#sidebarClose");

    if (menuBtn) menuBtn.addEventListener("click", function () { sidebar.classList.add("open"); });
    if (closeBtn) closeBtn.addEventListener("click", function () { sidebar.classList.remove("open"); });
  })();

  // ========== SECTOR HELPERS ==========
  function sectorClass(sector) {
    return "sector-" + sector.replace(/\s+/g, "-");
  }

  function dotClass(sector) {
    return "dot-" + sector.replace(/\s+/g, "-");
  }

  // ========== BUILD SIDEBAR LIST ==========
  function buildCompanyList() {
    var list = $("#companyList");
    var filter = state.activeFilter;
    var search = ($("#searchInput").value || "").toLowerCase();
    var html = "";

    COMPANY_DATA.companies.forEach(function (c, i) {
      if (filter !== "all" && c.sector !== filter) return;
      if (search && c.name.toLowerCase().indexOf(search) === -1 && c.id.toLowerCase().indexOf(search) === -1) return;

      var isActive = state.activeCompany === c.id ? " active" : "";
      html += '<button class="company-item' + isActive + '" data-id="' + c.id + '" role="listitem">';
      html += '<span class="rank">' + (i + 1) + '</span>';
      html += '<span class="sector-dot ' + dotClass(c.sector) + '"></span>';
      html += '<span class="name">' + c.name + '</span>';
      html += '<span class="mcap">' + c.marketCap + '</span>';
      html += '</button>';
    });

    list.innerHTML = html;

    list.querySelectorAll(".company-item").forEach(function (btn) {
      btn.addEventListener("click", function () {
        showCompanyDetail(btn.dataset.id);
        var sidebar = $("#sidebar");
        if (sidebar) sidebar.classList.remove("open");
      });
    });
  }

  // ========== FILTERS ==========
  $$(".filter-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      $$(".filter-btn").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
      state.activeFilter = btn.dataset.filter;
      buildCompanyList();
    });
  });

  // ========== SEARCH ==========
  var searchInput = $("#searchInput");
  if (searchInput) {
    searchInput.addEventListener("input", buildCompanyList);
  }

  // ========== COMPARE TOGGLE ==========
  var compareToggle = $("#compareToggle");
  if (compareToggle) {
    compareToggle.addEventListener("click", function () {
      if (state.activeView === "compare") {
        showOverview();
      } else {
        showCompare();
      }
    });
  }

  // ========== VIEW SWITCHING ==========
  function switchView(viewName) {
    state.activeView = viewName;
    $$(".view").forEach(function (v) { v.classList.remove("active"); });
    var view = $("#" + viewName + "View");
    if (view) view.classList.add("active");

    if (compareToggle) {
      compareToggle.classList.toggle("active", viewName === "compare");
    }
  }

  // ========== DESTROY CHARTS ==========
  function destroyCharts() {
    state.charts.forEach(function (c) { if (c) c.destroy(); });
    state.charts = [];
  }

  // ========== OVERVIEW ==========
  function showOverview() {
    destroyCharts();
    switchView("overview");
    $("#topBarTitle").textContent = "Overview";
    state.activeCompany = null;
    buildCompanyList();
    buildOverview();
  }

  function buildOverview() {
    // Stats
    var total = COMPANY_DATA.companies.length;
    var sectors = new Set(COMPANY_DATA.companies.map(function (c) { return c.sector; })).size;
    var countries = new Set(COMPANY_DATA.companies.map(function (c) { return c.country; })).size;

    var statsHtml = '';
    statsHtml += '<div class="stat-card"><div class="stat-value">' + total + '</div><div class="stat-label">Companies Tracked</div></div>';
    statsHtml += '<div class="stat-card"><div class="stat-value">' + sectors + '</div><div class="stat-label">Industry Sectors</div></div>';
    statsHtml += '<div class="stat-card"><div class="stat-value">' + countries + '</div><div class="stat-label">Countries</div></div>';
    statsHtml += '<div class="stat-card"><div class="stat-value">Mar 2026</div><div class="stat-label">Last Updated</div></div>';
    $("#overviewStats").innerHTML = statsHtml;

    // Cards
    var grid = $("#overviewGrid");
    var cardsHtml = "";

    COMPANY_DATA.companies.forEach(function (c, i) {
      var revData = c.financials.revenue ? c.financials.revenue.data : {};
      var years = Object.keys(revData).sort();
      var latestRev = years.length ? revData[years[years.length - 1]] : "—";

      cardsHtml += '<div class="card" data-id="' + c.id + '">';
      cardsHtml += '<div class="card-top">';
      cardsHtml += '<span class="card-rank">#' + (i + 1) + '</span>';
      cardsHtml += '<span class="card-sector ' + sectorClass(c.sector) + '">' + c.sector + '</span>';
      cardsHtml += '</div>';
      cardsHtml += '<div class="card-name">' + c.name + '</div>';
      cardsHtml += '<div class="card-industry">' + c.industry + ' · ' + c.country + '</div>';
      cardsHtml += '<div class="card-mcap">' + c.marketCap + '</div>';
      cardsHtml += '<div class="card-mcap-label">Market Cap</div>';
      cardsHtml += '<div class="card-sparkline"><canvas id="spark-' + c.id + '"></canvas></div>';
      cardsHtml += '</div>';
    });

    grid.innerHTML = cardsHtml;

    // Sparklines
    COMPANY_DATA.companies.forEach(function (c) {
      var revData = c.financials.revenue ? c.financials.revenue.data : {};
      var years = Object.keys(revData).sort();
      var values = years.map(function (y) { return revData[y]; });

      var canvas = document.getElementById("spark-" + c.id);
      if (!canvas || values.length < 2) return;

      var ctx = canvas.getContext("2d");
      var chart = new Chart(ctx, {
        type: "line",
        data: {
          labels: years,
          datasets: [{
            data: values,
            borderColor: getComputedStyle(document.documentElement).getPropertyValue("--color-primary").trim(),
            borderWidth: 2,
            fill: true,
            backgroundColor: getComputedStyle(document.documentElement).getPropertyValue("--color-primary-muted").trim(),
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 3,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          scales: {
            x: { display: false },
            y: { display: false }
          },
          animation: { duration: 400 }
        }
      });
      state.charts.push(chart);
    });

    // Card click handlers
    grid.querySelectorAll(".card").forEach(function (card) {
      card.addEventListener("click", function () {
        showCompanyDetail(card.dataset.id);
      });
    });
  }

  // ========== COMPANY DETAIL ==========
  function showCompanyDetail(companyId) {
    destroyCharts();
    var company = COMPANY_DATA.companies.find(function (c) { return c.id === companyId; });
    if (!company) return;

    state.activeCompany = companyId;
    switchView("detail");
    buildCompanyList();

    var idx = COMPANY_DATA.companies.indexOf(company) + 1;
    $("#topBarTitle").textContent = company.name;

    // Header
    var headerHtml = '';
    headerHtml += '<button class="detail-back" id="detailBack">';
    headerHtml += '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>';
    headerHtml += 'Back to Overview';
    headerHtml += '</button>';
    headerHtml += '<div class="detail-title-row">';
    headerHtml += '<h1 class="detail-company-name">' + company.name + '</h1>';
    headerHtml += '<span class="detail-ticker">' + company.id + '</span>';
    headerHtml += '</div>';
    headerHtml += '<div class="detail-meta">';
    headerHtml += '<span class="detail-meta-item"><strong>Rank:</strong> #' + idx + '</span>';
    headerHtml += '<span class="detail-meta-item"><strong>Market Cap:</strong> ' + company.marketCap + '</span>';
    headerHtml += '<span class="detail-meta-item"><strong>Sector:</strong> ' + company.sector + '</span>';
    headerHtml += '<span class="detail-meta-item"><strong>Industry:</strong> ' + company.industry + '</span>';
    headerHtml += '<span class="detail-meta-item"><strong>Country:</strong> ' + company.country + '</span>';
    headerHtml += '</div>';
    headerHtml += '<p class="detail-description">' + company.description + '</p>';

    $("#detailHeader").innerHTML = headerHtml;

    // Back button
    $("#detailBack").addEventListener("click", showOverview);

    // Financial charts
    buildChartSection(company.financials, "#financialCharts", false);

    // Non-financial charts
    buildNonFinancialSection(company, "#nonFinancialCharts");
  }

  function buildChartSection(financials, containerSel, showCompare) {
    var container = $(containerSel);
    container.innerHTML = "";

    var keys = Object.keys(financials);
    keys.forEach(function (key, idx) {
      var metric = financials[key];
      var data = metric.data;
      var years = Object.keys(data).sort();
      var values = years.map(function (y) { return data[y]; });

      var latestVal = values[values.length - 1];
      var prevVal = values.length > 1 ? values[values.length - 2] : null;

      var card = document.createElement("div");
      card.className = "chart-card";

      var valueStr = formatValue(latestVal, metric.label);
      card.innerHTML = '<div class="chart-card-title">' + metric.label + '</div>'
        + '<div class="latest-value">' + valueStr + '</div>'
        + '<div class="latest-label">Latest (' + years[years.length - 1] + ')</div>'
        + '<canvas></canvas>';

      container.appendChild(card);

      var canvas = card.querySelector("canvas");
      var ctx = canvas.getContext("2d");
      var d = getChartDefaults();

      var chart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: years,
          datasets: [{
            data: values,
            backgroundColor: CHART_COLORS[idx % CHART_COLORS.length] + "cc",
            borderColor: CHART_COLORS[idx % CHART_COLORS.length],
            borderWidth: 1,
            borderRadius: 4,
            barPercentage: 0.7,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            tooltip: {
              callbacks: {
                label: function (ctx2) {
                  return formatValue(ctx2.parsed.y, metric.label);
                }
              }
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: d.textColor, font: { size: 11 } }
            },
            y: {
              grid: { color: d.gridColor },
              ticks: {
                color: d.textColor,
                font: { size: 11 },
                callback: function (v) { return abbreviateNum(v); }
              },
              beginAtZero: shouldBeginAtZero(values)
            }
          }
        }
      });
      state.charts.push(chart);
    });
  }

  function buildNonFinancialSection(company, containerSel) {
    var container = $(containerSel);
    container.innerHTML = "";

    company.nonFinancials.forEach(function (metric, idx) {
      var data = metric.data;
      var years = Object.keys(data).sort();
      var values = years.map(function (y) { return data[y]; });

      var latestVal = values[values.length - 1];
      var valueStr = formatValue(latestVal, metric.label);

      var card = document.createElement("div");
      card.className = "chart-card";

      var compareBtn = "";
      if (metric.comparable) {
        compareBtn = '<button class="chart-card-compare" data-comparable="' + metric.comparable + '">Compare</button>';
      }

      card.innerHTML = '<div class="chart-card-title">' + metric.label + '</div>'
        + compareBtn
        + '<div class="latest-value">' + valueStr + '</div>'
        + '<div class="latest-label">Latest (' + years[years.length - 1] + ')</div>'
        + '<canvas></canvas>';

      container.appendChild(card);

      // Compare button handler
      var compBtn = card.querySelector(".chart-card-compare");
      if (compBtn) {
        compBtn.addEventListener("click", function (e) {
          e.stopPropagation();
          showCompare(metric.comparable);
        });
      }

      var canvas = card.querySelector("canvas");
      var ctx = canvas.getContext("2d");
      var d = getChartDefaults();
      var primaryColor = getComputedStyle(document.documentElement).getPropertyValue("--color-primary").trim();

      var chartType = metric.type === "area" ? "line" : (metric.type || "bar");
      var isFill = metric.type === "area";

      var dataset = {
        data: values,
        borderWidth: chartType === "line" ? 2.5 : 1,
        borderRadius: chartType === "bar" ? 4 : 0,
        barPercentage: 0.7,
        tension: 0.35,
        pointRadius: chartType === "line" ? 3 : 0,
        pointHoverRadius: chartType === "line" ? 5 : 0,
      };

      if (chartType === "line") {
        dataset.borderColor = CHART_COLORS[idx % CHART_COLORS.length];
        dataset.backgroundColor = isFill ? CHART_COLORS[idx % CHART_COLORS.length] + "30" : "transparent";
        dataset.fill = isFill;
        dataset.pointBackgroundColor = CHART_COLORS[idx % CHART_COLORS.length];
      } else {
        dataset.backgroundColor = CHART_COLORS[idx % CHART_COLORS.length] + "cc";
        dataset.borderColor = CHART_COLORS[idx % CHART_COLORS.length];
      }

      var chart = new Chart(ctx, {
        type: chartType === "bar" ? "bar" : "line",
        data: {
          labels: years,
          datasets: [dataset]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            tooltip: {
              callbacks: {
                label: function (ctx2) {
                  return formatValue(ctx2.parsed.y, metric.label);
                }
              }
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: d.textColor, font: { size: 11 } }
            },
            y: {
              grid: { color: d.gridColor },
              ticks: {
                color: d.textColor,
                font: { size: 11 },
                callback: function (v) { return abbreviateNum(v); }
              },
              beginAtZero: shouldBeginAtZero(values)
            }
          }
        }
      });
      state.charts.push(chart);
    });
  }

  // ========== COMPARE VIEW ==========
  function showCompare(metricKey) {
    destroyCharts();
    switchView("compare");
    $("#topBarTitle").textContent = "Compare Companies";
    state.activeCompany = null;
    buildCompanyList();

    if (metricKey) {
      state.compareMetric = metricKey;
      state.compareCompanies = COMPANY_DATA.comparables[metricKey]
        ? COMPANY_DATA.comparables[metricKey].companies.map(function (c) { return c.id; })
        : [];
    }

    buildComparePicker();
    buildCompareCompanyPicker();
    buildCompareChart();
  }

  function buildComparePicker() {
    var picker = $("#comparePicker");
    var html = "";

    Object.keys(COMPANY_DATA.comparables).forEach(function (key) {
      var comp = COMPANY_DATA.comparables[key];
      var label = friendlyComparableName(key);
      var count = comp.companies.length;
      var isActive = state.compareMetric === key ? " active" : "";
      html += '<button class="metric-btn' + isActive + '" data-key="' + key + '">';
      html += label + ' <span style="opacity:0.6">(' + count + ')</span>';
      html += '</button>';
    });

    picker.innerHTML = html;

    picker.querySelectorAll(".metric-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        state.compareMetric = btn.dataset.key;
        state.compareCompanies = COMPANY_DATA.comparables[btn.dataset.key]
          ? COMPANY_DATA.comparables[btn.dataset.key].companies.map(function (c) { return c.id; })
          : [];
        buildComparePicker();
        buildCompareCompanyPicker();
        buildCompareChart();
      });
    });
  }

  function buildCompareCompanyPicker() {
    var picker = $("#compareCompanyPicker");
    if (!state.compareMetric || !COMPANY_DATA.comparables[state.compareMetric]) {
      picker.innerHTML = "";
      return;
    }

    var companies = COMPANY_DATA.comparables[state.compareMetric].companies;
    var html = "";

    companies.forEach(function (c) {
      var isActive = state.compareCompanies.indexOf(c.id) > -1 ? " active" : "";
      html += '<button class="company-chip' + isActive + '" data-id="' + c.id + '">' + c.name + '</button>';
    });

    picker.innerHTML = html;

    picker.querySelectorAll(".company-chip").forEach(function (chip) {
      chip.addEventListener("click", function () {
        var idx = state.compareCompanies.indexOf(chip.dataset.id);
        if (idx > -1) {
          state.compareCompanies.splice(idx, 1);
        } else {
          state.compareCompanies.push(chip.dataset.id);
        }
        buildCompareCompanyPicker();
        buildCompareChart();
      });
    });
  }

  function buildCompareChart() {
    var wrap = $("#compareChartWrap");

    if (state.compareChart) {
      state.compareChart.destroy();
      state.compareChart = null;
    }

    if (!state.compareMetric || !COMPANY_DATA.comparables[state.compareMetric] || state.compareCompanies.length === 0) {
      wrap.innerHTML = '<div class="compare-empty"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 20V10M12 20V4M6 20v-6"/></svg><div>Select a metric and companies to compare</div></div>';
      return;
    }

    wrap.innerHTML = '<canvas id="compareCanvas"></canvas>';

    var comp = COMPANY_DATA.comparables[state.compareMetric];
    var selectedCompanies = comp.companies.filter(function (c) {
      return state.compareCompanies.indexOf(c.id) > -1;
    });

    // Collect all years
    var allYears = new Set();
    selectedCompanies.forEach(function (c) {
      Object.keys(c.data).forEach(function (y) { allYears.add(y); });
    });
    var years = Array.from(allYears).sort();

    var datasets = selectedCompanies.map(function (c, i) {
      return {
        label: c.name,
        data: years.map(function (y) { return c.data[y] !== undefined ? c.data[y] : null; }),
        borderColor: CHART_COLORS[i % CHART_COLORS.length],
        backgroundColor: CHART_COLORS[i % CHART_COLORS.length] + "30",
        borderWidth: 2.5,
        tension: 0.35,
        pointRadius: 4,
        pointHoverRadius: 6,
        fill: false,
        spanGaps: true,
        pointBackgroundColor: CHART_COLORS[i % CHART_COLORS.length],
      };
    });

    var d = getChartDefaults();
    var canvas = document.getElementById("compareCanvas");
    var ctx = canvas.getContext("2d");

    state.compareChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: years,
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: "top",
            labels: {
              usePointStyle: true,
              pointStyle: "circle",
              padding: 20,
              font: { size: 12, family: d.fontFamily },
              color: d.textColor,
            }
          },
          tooltip: {
            mode: "index",
            intersect: false,
            callbacks: {
              label: function (ctx2) {
                var val = ctx2.parsed.y;
                if (val === null || val === undefined) return ctx2.dataset.label + ": N/A";
                return ctx2.dataset.label + ": " + formatValue(val, comp.label);
              }
            }
          }
        },
        interaction: {
          mode: "nearest",
          axis: "x",
          intersect: false
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: d.textColor, font: { size: 12 } }
          },
          y: {
            grid: { color: d.gridColor },
            ticks: {
              color: d.textColor,
              font: { size: 12 },
              callback: function (v) { return abbreviateNum(v); }
            }
          }
        }
      }
    });
  }

  // ========== HELPERS ==========
  function formatValue(val, label) {
    if (val === null || val === undefined) return "—";
    var l = (label || "").toLowerCase();

    if (l.indexOf("(%)") > -1 || l.indexOf("share") > -1 || l.indexOf("rate") > -1 || l.indexOf("growth") > -1 || l.indexOf("margin") > -1 || l.indexOf("penetration") > -1) {
      return val.toFixed(1) + "%";
    }
    if (l.indexOf("($b") > -1 || l.indexOf("($t") > -1) {
      if (Math.abs(val) >= 1000) return "$" + (val / 1000).toFixed(2) + "T";
      return "$" + val.toFixed(1) + "B";
    }
    if (l.indexOf("($m") > -1) {
      return "$" + val.toFixed(1) + "M";
    }
    if (l.indexOf("($)") > -1 || l.indexOf("eps") > -1 || l.indexOf("ticket") > -1 || l.indexOf("per user") > -1 || l.indexOf("per sqm") > -1 || l.indexOf("per warehouse") > -1 || l.indexOf("per customer") > -1) {
      return "$" + val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    if (Math.abs(val) >= 10000) {
      return abbreviateNum(val);
    }
    if (Number.isInteger(val)) return val.toLocaleString();
    return val.toFixed(1);
  }

  function abbreviateNum(val) {
    if (val === null || val === undefined) return "";
    var abs = Math.abs(val);
    if (abs >= 1e12) return (val / 1e12).toFixed(1) + "T";
    if (abs >= 1e9) return (val / 1e9).toFixed(1) + "B";
    if (abs >= 1e6) return (val / 1e6).toFixed(1) + "M";
    if (abs >= 1e3) return (val / 1e3).toFixed(1) + "K";
    if (Number.isInteger(val)) return val.toString();
    return val.toFixed(1);
  }

  function shouldBeginAtZero(values) {
    var min = Math.min.apply(null, values);
    var max = Math.max.apply(null, values);
    if (min < 0) return false;
    if (min === 0) return true;
    return (min / max) < 0.5;
  }

  function friendlyComparableName(key) {
    var map = {
      "datacenter_gpus": "Data Center GPUs",
      "active_devices": "Digital / Active Users",
      "dau": "Daily Active Users",
      "cloud_revenue": "Cloud Revenue",
      "data_centers": "Data Center Count",
      "mau": "Monthly Active Users",
      "capex": "Capital Expenditure",
      "renewable_capacity": "Renewable Energy Capacity",
      "rd_spending": "R&D Spending",
    };
    return map[key] || key;
  }

  function rebuildCurrentView() {
    if (state.activeView === "overview") {
      destroyCharts();
      buildOverview();
    } else if (state.activeView === "detail" && state.activeCompany) {
      showCompanyDetail(state.activeCompany);
    } else if (state.activeView === "compare") {
      buildCompareChart();
    }
  }

  // ========== INIT ==========
  applyChartDefaults();
  buildCompanyList();
  buildOverview();

})();
