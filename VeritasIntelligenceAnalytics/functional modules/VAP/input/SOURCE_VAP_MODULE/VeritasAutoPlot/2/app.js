/* =============================================================
   YC Catalog — App Logic
   ============================================================= */

(function () {
  "use strict";

  /* ---- State ---- */
  let allCompanies = [];
  let filtered = [];
  let currentPage = 1;
  const PAGE_SIZE = 50;
  let sortCol = null;
  let sortDir = "asc";
  let batchSortCol = "batch";
  let batchSortDir = "desc";
  let batchChart = null;

  /* ---- DOM refs ---- */
  const $searchInput = document.getElementById("searchInput");
  const $filterBatch = document.getElementById("filterBatch");
  const $filterStatus = document.getElementById("filterStatus");
  const $filterIndustry = document.getElementById("filterIndustry");
  const $filterTeamSize = document.getElementById("filterTeamSize");
  const $clearFilters = document.getElementById("clearFilters");
  const $resultsInfo = document.getElementById("resultsInfo");
  const $tableBody = document.getElementById("tableBody");
  const $pagination = document.getElementById("pagination");
  const $companyCount = document.getElementById("companyCount");

  /* ---- Theme toggle ---- */
  (function () {
    var t = document.querySelector("[data-theme-toggle]");
    var r = document.documentElement;
    var d = matchMedia("(prefers-color-scheme:dark)").matches ? "dark" : "light";
    r.setAttribute("data-theme", d);
    function updateIcon() {
      if (!t) return;
      t.innerHTML =
        d === "dark"
          ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
          : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
      t.setAttribute("aria-label", "Switch to " + (d === "dark" ? "light" : "dark") + " mode");
    }
    updateIcon();
    if (t) {
      t.addEventListener("click", function () {
        d = d === "dark" ? "light" : "dark";
        r.setAttribute("data-theme", d);
        updateIcon();
        if (batchChart) {
          updateBatchChartColors();
        }
      });
    }
  })();

  /* ---- View Toggle ---- */
  document.querySelectorAll(".view-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".view-btn").forEach(function (b) {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      var view = btn.dataset.view;
      document.querySelectorAll(".view-panel").forEach(function (p) {
        p.classList.remove("active");
      });
      document.getElementById(view + "View").classList.add("active");
      if (view === "batches" && allCompanies.length > 0) {
        renderBatchView();
      }
    });
  });

  /* ---- Load data ---- */
  showSkeleton();
  fetch("./data.json")
    .then(function (r) { return r.json(); })
    .then(function (data) {
      allCompanies = data;
      $companyCount.textContent = formatNum(data.length) + " companies";
      populateFilters();
      applyFilters();
    })
    .catch(function (err) {
      console.error("Failed to load data:", err);
      $resultsInfo.textContent = "Failed to load data.";
    });

  /* ---- Populate filter dropdowns ---- */
  function populateFilters() {
    var batches = [];
    var batchSet = {};
    var industries = {};
    allCompanies.forEach(function (c) {
      if (c.b && c.b !== "N/A" && !batchSet[c.b]) {
        batchSet[c.b] = true;
        batches.push({ short: c.b, full: c.bf });
      }
      if (c.i) industries[c.i] = true;
    });

    batches.sort(function (a, b) {
      return batchSortValue(b.full) - batchSortValue(a.full);
    });

    batches.forEach(function (bt) {
      var opt = document.createElement("option");
      opt.value = bt.short;
      opt.textContent = bt.short + " — " + bt.full;
      $filterBatch.appendChild(opt);
    });

    Object.keys(industries).sort().forEach(function (ind) {
      var opt = document.createElement("option");
      opt.value = ind;
      opt.textContent = ind;
      $filterIndustry.appendChild(opt);
    });
  }

  /* ---- Filter logic ---- */
  var filterTimeout;
  $searchInput.addEventListener("input", debounceFilter);
  $filterBatch.addEventListener("change", applyFilters);
  $filterStatus.addEventListener("change", applyFilters);
  $filterIndustry.addEventListener("change", applyFilters);
  $filterTeamSize.addEventListener("change", applyFilters);
  $clearFilters.addEventListener("click", function () {
    $searchInput.value = "";
    $filterBatch.value = "";
    $filterStatus.value = "";
    $filterIndustry.value = "";
    $filterTeamSize.value = "";
    applyFilters();
  });

  function debounceFilter() {
    clearTimeout(filterTimeout);
    filterTimeout = setTimeout(applyFilters, 200);
  }

  function applyFilters() {
    var q = $searchInput.value.toLowerCase().trim();
    var batch = $filterBatch.value;
    var status = $filterStatus.value;
    var industry = $filterIndustry.value;
    var teamSize = $filterTeamSize.value;

    filtered = allCompanies.filter(function (c) {
      if (q && c.n.toLowerCase().indexOf(q) === -1 && (c.d || "").toLowerCase().indexOf(q) === -1) return false;
      if (batch && c.b !== batch) return false;
      if (status && c.s !== status) return false;
      if (industry && c.i !== industry) return false;
      if (teamSize && !matchTeamSize(c.ts, teamSize)) return false;
      return true;
    });

    var hasFilter = q || batch || status || industry || teamSize;
    $clearFilters.style.display = hasFilter ? "inline-flex" : "none";

    currentPage = 1;
    if (sortCol) {
      sortData(sortCol, sortDir, false);
    }
    renderTable();
  }

  function matchTeamSize(ts, range) {
    if (!ts) ts = 0;
    switch (range) {
      case "1-10": return ts >= 1 && ts <= 10;
      case "11-50": return ts >= 11 && ts <= 50;
      case "51-200": return ts >= 51 && ts <= 200;
      case "201-1000": return ts >= 201 && ts <= 1000;
      case "1001+": return ts > 1000;
      default: return true;
    }
  }

  /* ---- Sorting ---- */
  document.querySelectorAll("#companyTable th.sortable").forEach(function (th) {
    th.addEventListener("click", function () {
      var col = th.dataset.sort;
      if (sortCol === col) {
        sortDir = sortDir === "asc" ? "desc" : "asc";
      } else {
        sortCol = col;
        sortDir = "asc";
      }
      document.querySelectorAll("#companyTable th").forEach(function (h) {
        h.classList.remove("sort-asc", "sort-desc");
      });
      th.classList.add(sortDir === "asc" ? "sort-asc" : "sort-desc");
      sortData(sortCol, sortDir, true);
      renderTable();
    });
  });

  function sortData(col, dir, updateUI) {
    var mult = dir === "asc" ? 1 : -1;
    filtered.sort(function (a, b) {
      var va, vb;
      switch (col) {
        case "batch":
          va = batchSortValue(a.bf);
          vb = batchSortValue(b.bf);
          break;
        case "name":
          va = a.n.toLowerCase();
          vb = b.n.toLowerCase();
          return va < vb ? -1 * mult : va > vb ? 1 * mult : 0;
        case "status":
          va = statusOrder(a.s);
          vb = statusOrder(b.s);
          break;
        case "industry":
          va = a.i.toLowerCase();
          vb = b.i.toLowerCase();
          return va < vb ? -1 * mult : va > vb ? 1 * mult : 0;
        case "team":
          va = a.ts || 0;
          vb = b.ts || 0;
          break;
        case "funding":
          va = parseMoney(a.f);
          vb = parseMoney(b.f);
          break;
        case "valuation":
          va = parseMoney(a.v);
          vb = parseMoney(b.v);
          break;
        default:
          va = 0; vb = 0;
      }
      return (va - vb) * mult;
    });
  }

  function statusOrder(s) {
    return { "Public": 4, "Active": 3, "Acquired": 2, "Dead": 1 }[s] || 0;
  }

  function parseMoney(s) {
    if (!s) return 0;
    var num = parseFloat(s.replace(/[^0-9.]/g, ""));
    if (s.indexOf("B") !== -1) return num * 1e9;
    if (s.indexOf("M") !== -1) return num * 1e6;
    if (s.indexOf("K") !== -1) return num * 1e3;
    return num;
  }

  /* ---- Render company table ---- */
  function renderTable() {
    var total = filtered.length;
    var totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    if (currentPage > totalPages) currentPage = totalPages;
    var start = (currentPage - 1) * PAGE_SIZE;
    var pageData = filtered.slice(start, start + PAGE_SIZE);

    $resultsInfo.textContent = formatNum(total) + " companies found" + (total !== allCompanies.length ? " (filtered)" : "");

    if (pageData.length === 0) {
      $tableBody.innerHTML =
        '<tr><td colspan="8">' +
        '<div class="empty-state">' +
        '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/><path d="M8 11h6"/></svg>' +
        "<h3>No companies found</h3><p>Try adjusting your filters or search query.</p></div></td></tr>";
      $pagination.innerHTML = "";
      return;
    }

    var html = "";
    pageData.forEach(function (c) {
      var statusClass = "status-" + c.s.toLowerCase();
      var topBadge = c.t ? '<span class="cell-top-badge">TOP</span>' : "";
      html +=
        "<tr>" +
        '<td><span class="cell-batch">' + esc(c.b) + "</span></td>" +
        '<td><span class="cell-name"><a href="' + esc(c.u || "#") + '" target="_blank" rel="noopener noreferrer">' + esc(c.n) + "</a>" + topBadge + "</span></td>" +
        '<td><span class="cell-desc" title="' + esc(c.d || "") + '">' + esc(c.d || "—") + "</span></td>" +
        '<td><span class="status-badge ' + statusClass + '">' + esc(c.s) + "</span></td>" +
        '<td><span style="font-size:var(--text-xs)">' + esc(c.i) + "</span></td>" +
        '<td><span class="cell-team">' + (c.ts ? formatNum(c.ts) : '<span class="cell-na">—</span>') + "</span></td>" +
        '<td><span class="cell-funding">' + (c.f ? esc(c.f) : '<span class="cell-na">—</span>') + "</span></td>" +
        '<td><span class="cell-valuation">' + (c.v ? esc(c.v) : '<span class="cell-na">—</span>') + "</span></td>" +
        "</tr>";
    });
    $tableBody.innerHTML = html;
    renderPagination(totalPages);
  }

  /* ---- Pagination ---- */
  function renderPagination(totalPages) {
    if (totalPages <= 1) {
      $pagination.innerHTML = "";
      return;
    }

    var html = "";
    html += '<button class="page-btn" data-page="prev" ' + (currentPage === 1 ? "disabled" : "") + ">← Prev</button>";

    var pages = getPageNumbers(currentPage, totalPages);
    pages.forEach(function (p) {
      if (p === "...") {
        html += '<span class="page-ellipsis">…</span>';
      } else {
        html += '<button class="page-btn' + (p === currentPage ? " active" : "") + '" data-page="' + p + '">' + p + "</button>";
      }
    });

    html += '<button class="page-btn" data-page="next" ' + (currentPage === totalPages ? "disabled" : "") + ">Next →</button>";
    $pagination.innerHTML = html;

    $pagination.querySelectorAll(".page-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var p = btn.dataset.page;
        if (p === "prev") currentPage = Math.max(1, currentPage - 1);
        else if (p === "next") currentPage = Math.min(totalPages, currentPage + 1);
        else currentPage = parseInt(p, 10);
        renderTable();
        document.querySelector(".table-container").scrollTo({ top: 0, behavior: "smooth" });
      });
    });
  }

  function getPageNumbers(current, total) {
    if (total <= 7) {
      var arr = [];
      for (var i = 1; i <= total; i++) arr.push(i);
      return arr;
    }
    var pages = [1];
    if (current > 3) pages.push("...");
    for (var j = Math.max(2, current - 1); j <= Math.min(total - 1, current + 1); j++) {
      pages.push(j);
    }
    if (current < total - 2) pages.push("...");
    pages.push(total);
    return pages;
  }

  /* ---- Skeleton ---- */
  function showSkeleton() {
    var rows = "";
    for (var i = 0; i < 12; i++) {
      rows += '<tr class="skeleton-row">';
      for (var j = 0; j < 8; j++) {
        var w = [50, 120, 200, 60, 80, 40, 70, 70][j];
        rows += '<td><div class="skeleton-cell" style="width:' + w + "px\"></div></td>";
      }
      rows += "</tr>";
    }
    $tableBody.innerHTML = rows;
  }

  /* ---- Batch Performance View ---- */
  function renderBatchView() {
    var stats = computeBatchStats();
    renderBatchKpis(stats);
    renderBatchChart(stats);
    renderBatchTable(stats);
  }

  function computeBatchStats() {
    var map = {};
    allCompanies.forEach(function (c) {
      var b = c.b;
      if (!b || b === "N/A") return;
      if (!map[b]) {
        map[b] = { batch: b, batchFull: c.bf, total: 0, active: 0, public: 0, acquired: 0, dead: 0, topCos: 0, teamSizes: [] };
      }
      var s = map[b];
      s.total++;
      if (c.s === "Active") s.active++;
      else if (c.s === "Public") s.public++;
      else if (c.s === "Acquired") s.acquired++;
      else if (c.s === "Dead") s.dead++;
      if (c.t) s.topCos++;
      if (c.ts > 0) s.teamSizes.push(c.ts);
    });

    return Object.values(map).sort(function (a, b) {
      return batchSortValue(b.batchFull) - batchSortValue(a.batchFull);
    });
  }

  function renderBatchKpis(stats) {
    var totalCompanies = allCompanies.length;
    var totalBatches = stats.length;
    var totalActive = 0, totalPublic = 0, totalAcquired = 0, totalDead = 0, totalTop = 0;

    stats.forEach(function (s) {
      totalActive += s.active;
      totalPublic += s.public;
      totalAcquired += s.acquired;
      totalDead += s.dead;
      totalTop += s.topCos;
    });

    var survivalRate = totalCompanies > 0 ? ((totalActive + totalPublic + totalAcquired) / totalCompanies * 100).toFixed(1) : 0;

    document.getElementById("batchKpis").innerHTML =
      kpiCard("Total Companies", formatNum(totalCompanies), "Across " + totalBatches + " batches") +
      kpiCard("Active", formatNum(totalActive), ((totalActive / totalCompanies * 100).toFixed(1)) + "% of all") +
      kpiCard("Public", formatNum(totalPublic), ((totalPublic / totalCompanies * 100).toFixed(1)) + "% of all") +
      kpiCard("Acquired", formatNum(totalAcquired), ((totalAcquired / totalCompanies * 100).toFixed(1)) + "% of all") +
      kpiCard("Survival Rate", survivalRate + "%", "Active + Public + Acquired") +
      kpiCard("Top Companies", formatNum(totalTop), "Flagged by YC");
  }

  function kpiCard(label, value, sub) {
    return '<div class="kpi-card"><div class="kpi-label">' + label + '</div><div class="kpi-value">' + value + '</div><div class="kpi-sub">' + sub + "</div></div>";
  }

  function renderBatchChart(stats) {
    var chartStats = stats.slice().reverse();

    var labels = chartStats.map(function (s) { return s.batch; });
    var activeData = chartStats.map(function (s) { return s.active; });
    var publicData = chartStats.map(function (s) { return s.public; });
    var acquiredData = chartStats.map(function (s) { return s.acquired; });
    var deadData = chartStats.map(function (s) { return s.dead; });

    var ctx = document.getElementById("batchChart").getContext("2d");

    if (batchChart) {
      batchChart.destroy();
    }

    var isDark = document.documentElement.getAttribute("data-theme") === "dark";
    var gridColor = isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)";
    var textColor = isDark ? "#8c8c86" : "#6b6b66";

    batchChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          { label: "Active", data: activeData, backgroundColor: isDark ? "#22c55e" : "#16a34a", borderRadius: 2 },
          { label: "Public", data: publicData, backgroundColor: isDark ? "#60a5fa" : "#2563eb", borderRadius: 2 },
          { label: "Acquired", data: acquiredData, backgroundColor: isDark ? "#a78bfa" : "#7c3aed", borderRadius: 2 },
          { label: "Dead", data: deadData, backgroundColor: isDark ? "#f87171" : "#dc2626", borderRadius: 2 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            position: "top",
            labels: { color: textColor, font: { size: 11, family: "'Inter', sans-serif" }, boxWidth: 12, padding: 16 }
          },
          tooltip: {
            backgroundColor: isDark ? "#2a2a28" : "#fff",
            titleColor: isDark ? "#e5e5e0" : "#1a1a18",
            bodyColor: isDark ? "#8c8c86" : "#6b6b66",
            borderColor: isDark ? "#3d3d3a" : "#d5d4cf",
            borderWidth: 1,
            cornerRadius: 6,
            padding: 10,
            titleFont: { size: 12, weight: 600 },
            bodyFont: { size: 11 }
          }
        },
        scales: {
          x: {
            stacked: true,
            grid: { display: false },
            ticks: { color: textColor, font: { size: 10, family: "'JetBrains Mono', monospace" }, maxRotation: 45 }
          },
          y: {
            stacked: true,
            grid: { color: gridColor },
            ticks: { color: textColor, font: { size: 11 } }
          }
        }
      }
    });
  }

  function updateBatchChartColors() {
    if (!batchChart) return;
    var isDark = document.documentElement.getAttribute("data-theme") === "dark";
    var gridColor = isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)";
    var textColor = isDark ? "#8c8c86" : "#6b6b66";

    batchChart.data.datasets[0].backgroundColor = isDark ? "#22c55e" : "#16a34a";
    batchChart.data.datasets[1].backgroundColor = isDark ? "#60a5fa" : "#2563eb";
    batchChart.data.datasets[2].backgroundColor = isDark ? "#a78bfa" : "#7c3aed";
    batchChart.data.datasets[3].backgroundColor = isDark ? "#f87171" : "#dc2626";

    batchChart.options.scales.x.ticks.color = textColor;
    batchChart.options.scales.y.ticks.color = textColor;
    batchChart.options.scales.y.grid.color = gridColor;
    batchChart.options.plugins.legend.labels.color = textColor;
    batchChart.options.plugins.tooltip.backgroundColor = isDark ? "#2a2a28" : "#fff";
    batchChart.options.plugins.tooltip.titleColor = isDark ? "#e5e5e0" : "#1a1a18";
    batchChart.options.plugins.tooltip.bodyColor = isDark ? "#8c8c86" : "#6b6b66";
    batchChart.options.plugins.tooltip.borderColor = isDark ? "#3d3d3a" : "#d5d4cf";

    batchChart.update();
  }

  function renderBatchTable(stats) {
    var sorted = stats.slice();
    sortBatchTable(sorted);

    var html = "";
    sorted.forEach(function (s) {
      var survival = s.total > 0 ? ((s.active + s.public + s.acquired) / s.total * 100).toFixed(1) : "0.0";
      var avgTeam = s.teamSizes.length > 0 ? Math.round(s.teamSizes.reduce(function (a, b) { return a + b; }, 0) / s.teamSizes.length) : 0;

      html += "<tr>" +
        '<td><span class="cell-batch">' + esc(s.batch) + "</span></td>" +
        "<td>" + formatNum(s.total) + "</td>" +
        '<td><span style="color:var(--color-success)">' + formatNum(s.active) + "</span></td>" +
        '<td><span style="color:var(--color-blue)">' + formatNum(s.public) + "</span></td>" +
        '<td><span style="color:var(--color-purple)">' + formatNum(s.acquired) + "</span></td>" +
        '<td><span style="color:var(--color-error)">' + formatNum(s.dead) + "</span></td>" +
        '<td><span class="survival-pct">' + survival + '%</span><span class="survival-bar"><span class="bar-fill" style="width:' + survival + '%"></span></span></td>' +
        "<td>" + (s.topCos > 0 ? formatNum(s.topCos) : '<span class="cell-na">—</span>') + "</td>" +
        '<td><span class="cell-team">' + (avgTeam > 0 ? formatNum(avgTeam) : '<span class="cell-na">—</span>') + "</span></td>" +
        "</tr>";
    });
    document.getElementById("batchTableBody").innerHTML = html;
  }

  /* Batch table sorting */
  document.querySelectorAll("#batchTable th.sortable").forEach(function (th) {
    th.addEventListener("click", function () {
      var col = th.dataset.sort;
      if (batchSortCol === col) {
        batchSortDir = batchSortDir === "asc" ? "desc" : "asc";
      } else {
        batchSortCol = col;
        batchSortDir = col === "batch" ? "desc" : "desc";
      }
      document.querySelectorAll("#batchTable th").forEach(function (h) {
        h.classList.remove("sort-asc", "sort-desc");
      });
      th.classList.add(batchSortDir === "asc" ? "sort-asc" : "sort-desc");
      renderBatchView();
    });
  });

  function sortBatchTable(arr) {
    var mult = batchSortDir === "asc" ? 1 : -1;
    arr.sort(function (a, b) {
      var va, vb;
      switch (batchSortCol) {
        case "batch":
          va = batchSortValue(a.batchFull);
          vb = batchSortValue(b.batchFull);
          break;
        case "total":   va = a.total; vb = b.total; break;
        case "active":  va = a.active; vb = b.active; break;
        case "public":  va = a.public; vb = b.public; break;
        case "acquired": va = a.acquired; vb = b.acquired; break;
        case "dead":    va = a.dead; vb = b.dead; break;
        case "survival":
          va = a.total > 0 ? (a.active + a.public + a.acquired) / a.total : 0;
          vb = b.total > 0 ? (b.active + b.public + b.acquired) / b.total : 0;
          break;
        case "topcos":  va = a.topCos; vb = b.topCos; break;
        case "avgteam":
          va = a.teamSizes.length > 0 ? a.teamSizes.reduce(function (x, y) { return x + y; }, 0) / a.teamSizes.length : 0;
          vb = b.teamSizes.length > 0 ? b.teamSizes.reduce(function (x, y) { return x + y; }, 0) / b.teamSizes.length : 0;
          break;
        default:
          va = 0; vb = 0;
      }
      return (va - vb) * mult;
    });
  }

  /* ---- Utilities ---- */
  function batchSortValue(fullBatch) {
    if (!fullBatch) return 0;
    var parts = fullBatch.split(" ");
    if (parts.length !== 2) return 0;
    var seasonOrder = { "Winter": 0, "Spring": 1, "Summer": 2, "Fall": 3 };
    var year = parseInt(parts[1], 10) || 0;
    var season = seasonOrder[parts[0]] || 0;
    return year * 10 + season;
  }

  function formatNum(n) {
    if (n === undefined || n === null) return "—";
    return n.toLocaleString("en-US");
  }

  function esc(s) {
    if (!s) return "";
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }
})();
