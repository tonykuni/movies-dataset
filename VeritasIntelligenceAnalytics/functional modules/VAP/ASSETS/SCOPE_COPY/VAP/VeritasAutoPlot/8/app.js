/* global EPISODES, PODCAST_STATS */
(function () {
  "use strict";

  // ===== STATE =====
  let filteredEpisodes = [...EPISODES];
  let currentPage = 1;
  const PAGE_SIZE = 25;
  let expandedRow = null;
  let activeTopic = null;
  let sortField = "rank";
  let sortDir = "asc";

  // ===== THEME TOGGLE =====
  (function initTheme() {
    const toggle = document.querySelector("[data-theme-toggle]");
    const root = document.documentElement;
    let theme = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "dark"; // default dark for Colossus aesthetic
    root.setAttribute("data-theme", theme);

    if (toggle) {
      toggle.addEventListener("click", function () {
        theme = theme === "dark" ? "light" : "dark";
        root.setAttribute("data-theme", theme);
        toggle.setAttribute("aria-label", "Switch to " + (theme === "dark" ? "light" : "dark") + " mode");
        toggle.innerHTML = theme === "dark"
          ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
          : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
        updateChart();
      });
    }
  })();

  // ===== STATS DASHBOARD =====
  function renderStats() {
    var grid = document.getElementById("stats-grid");
    var stats = [
      { label: "Total Episodes", value: PODCAST_STATS.total_episodes, meta: "Since " + PODCAST_STATS.first_episode.slice(0, 4) },
      { label: "Apple Rating", value: PODCAST_STATS.apple_rating + "★", meta: PODCAST_STATS.apple_ratings_count.toLocaleString() + " ratings", cls: "gold" },
      { label: "Spotify Rank", value: PODCAST_STATS.spotify_ranking.replace("#", "").replace(" US Business", ""), meta: "US Business", cls: "gold" },
      { label: "Monthly Listeners", value: PODCAST_STATS.monthly_listeners, meta: "Estimated range" },
      { label: "Cumulative Listens", value: PODCAST_STATS.cumulative_listeners, meta: "As of 2023" },
      { label: "X Followers", value: PODCAST_STATS.twitter_followers, meta: "@patrick_oshag" },
    ];

    grid.innerHTML = stats.map(function (s) {
      return '<div class="stat-card">' +
        '<span class="stat-label">' + s.label + '</span>' +
        '<span class="stat-value' + (s.cls ? " " + s.cls : "") + '">' + s.value + '</span>' +
        '<span class="stat-meta">' + s.meta + '</span>' +
        '</div>';
    }).join("");
  }

  // ===== TOPIC TAGS =====
  function getTopTopics() {
    var counts = {};
    EPISODES.forEach(function (ep) {
      (ep.topics || []).forEach(function (t) {
        counts[t] = (counts[t] || 0) + 1;
      });
    });
    return Object.entries(counts)
      .sort(function (a, b) { return b[1] - a[1]; })
      .slice(0, 18)
      .map(function (e) { return e[0]; });
  }

  function renderTopicTags() {
    var container = document.getElementById("topic-tags");
    var topics = getTopTopics();
    container.innerHTML = '<button class="topic-tag' + (activeTopic === null ? " active" : "") + '" data-topic="">All Topics</button>' +
      topics.map(function (t) {
        return '<button class="topic-tag' + (activeTopic === t ? " active" : "") + '" data-topic="' + t + '">' + t + '</button>';
      }).join("");

    container.querySelectorAll(".topic-tag").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var topic = this.getAttribute("data-topic");
        activeTopic = topic || null;
        currentPage = 1;
        expandedRow = null;
        applyFilters();
        renderTopicTags();
      });
    });
  }

  // ===== CHART =====
  var trendChart = null;
  function updateChart() {
    var ctx = document.getElementById("trend-chart");
    if (!ctx) return;

    var isDark = document.documentElement.getAttribute("data-theme") !== "light";
    var gridColor = isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)";
    var textColor = isDark ? "#8b92a8" : "#5a5e6e";

    // Group by quarter
    var quarters = {};
    EPISODES.forEach(function (ep) {
      if (!ep.date) return;
      var y = ep.date.slice(0, 4);
      var m = parseInt(ep.date.slice(5, 7), 10);
      var q = "Q" + Math.ceil(m / 3);
      var key = y + " " + q;
      if (!quarters[key]) quarters[key] = { scores: [], count: 0 };
      quarters[key].scores.push(ep.score);
      quarters[key].count++;
    });

    var labels = Object.keys(quarters).sort();
    var avgScores = labels.map(function (k) {
      var q = quarters[k];
      return +(q.scores.reduce(function (a, b) { return a + b; }, 0) / q.scores.length).toFixed(1);
    });
    var epCounts = labels.map(function (k) { return quarters[k].count; });

    if (trendChart) trendChart.destroy();
    trendChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Episodes",
            data: epCounts,
            backgroundColor: isDark ? "rgba(201,168,76,0.3)" : "rgba(139,105,20,0.2)",
            borderColor: isDark ? "rgba(201,168,76,0.6)" : "rgba(139,105,20,0.5)",
            borderWidth: 1,
            borderRadius: 3,
            yAxisID: "y",
            order: 2,
          },
          {
            label: "Avg Score",
            data: avgScores,
            type: "line",
            borderColor: isDark ? "#c9a84c" : "#8b6914",
            backgroundColor: "transparent",
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 4,
            tension: 0.4,
            yAxisID: "y1",
            order: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            display: true,
            position: "top",
            labels: { color: textColor, font: { family: "'DM Sans'", size: 12 }, boxWidth: 12, padding: 16 },
          },
          tooltip: {
            backgroundColor: isDark ? "#1c2440" : "#ffffff",
            titleColor: isDark ? "#e8eaf0" : "#1a1e2e",
            bodyColor: isDark ? "#8b92a8" : "#5a5e6e",
            borderColor: isDark ? "#364166" : "#c5c4bf",
            borderWidth: 1,
            padding: 12,
            titleFont: { family: "'DM Sans'", weight: 600 },
            bodyFont: { family: "'DM Sans'" },
          },
        },
        scales: {
          x: {
            grid: { color: gridColor },
            ticks: { color: textColor, font: { family: "'DM Sans'", size: 11 }, maxRotation: 45 },
          },
          y: {
            position: "left",
            title: { display: true, text: "Episodes", color: textColor, font: { family: "'DM Sans'", size: 12 } },
            grid: { color: gridColor },
            ticks: { color: textColor, font: { family: "'DM Sans'", size: 11 } },
          },
          y1: {
            position: "right",
            title: { display: true, text: "Avg Score", color: textColor, font: { family: "'DM Sans'", size: 12 } },
            grid: { drawOnChartArea: false },
            ticks: { color: textColor, font: { family: "'DM Sans'", size: 11 } },
            min: 40,
            max: 100,
          },
        },
      },
    });
  }

  // ===== FILTERING & SORTING =====
  function applyFilters() {
    var query = document.getElementById("search-input").value.toLowerCase().trim();
    var dateFrom = document.getElementById("date-from").value;
    var dateTo = document.getElementById("date-to").value;

    filteredEpisodes = EPISODES.filter(function (ep) {
      // Text search
      if (query) {
        var searchable = (ep.title + " " + ep.guest + " " + (ep.topics || []).join(" ") + " " + (ep.summary || "")).toLowerCase();
        if (searchable.indexOf(query) === -1) return false;
      }
      // Date range
      if (dateFrom && ep.date < dateFrom) return false;
      if (dateTo && ep.date > dateTo) return false;
      // Topic filter
      if (activeTopic && !(ep.topics || []).some(function (t) { return t === activeTopic; })) return false;
      return true;
    });

    applySorting();
    renderTable();
    renderPagination();
    updateResultsCount();
  }

  function applySorting() {
    var select = document.getElementById("sort-select");
    var val = select.value;

    if (val === "score-desc") { sortField = "score"; sortDir = "desc"; }
    else if (val === "score-asc") { sortField = "score"; sortDir = "asc"; }
    else if (val === "date-desc") { sortField = "date"; sortDir = "desc"; }
    else if (val === "date-asc") { sortField = "date"; sortDir = "asc"; }
    else if (val === "guest-asc") { sortField = "guest"; sortDir = "asc"; }

    filteredEpisodes.sort(function (a, b) {
      var av = a[sortField];
      var bv = b[sortField];
      if (typeof av === "string") av = av.toLowerCase();
      if (typeof bv === "string") bv = bv.toLowerCase();
      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
  }

  function updateResultsCount() {
    document.getElementById("results-count").textContent =
      "Showing " + filteredEpisodes.length + " of " + EPISODES.length + " episodes";
  }

  // ===== TABLE RENDERING =====
  function formatDate(d) {
    if (!d) return "";
    var parts = d.split("-");
    var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return months[parseInt(parts[1], 10) - 1] + " " + parseInt(parts[2], 10) + ", " + parts[0];
  }

  function cleanTitle(title) {
    return title
      .replace(/\s*-\s*\[Invest Like the Best.*?\]/i, "")
      .replace(/\s*-\s*\[Founder.*?\]/i, "")
      .replace(/\s*–\s*\[Invest Like the Best.*?\]/i, "")
      .replace(/\s*–\s*\[Founder.*?\]/i, "")
      .trim();
  }

  function renderTable() {
    var tbody = document.getElementById("episodes-body");
    var start = (currentPage - 1) * PAGE_SIZE;
    var end = Math.min(start + PAGE_SIZE, filteredEpisodes.length);
    var page = filteredEpisodes.slice(start, end);

    var html = "";
    page.forEach(function (ep) {
      var isExpanded = expandedRow === ep.rank;
      html += '<tr class="' + (isExpanded ? "expanded" : "") + '" data-rank="' + ep.rank + '">' +
        '<td class="rank-cell' + (ep.rank <= 3 ? " top-3" : "") + '">' + ep.rank + '</td>' +
        '<td class="title-cell"><span class="ep-title">' + cleanTitle(ep.title) + '</span>' +
        (ep.number ? '<span class="ep-number">EP.' + ep.number + '</span>' : '') + '</td>' +
        '<td class="guest-cell">' + (ep.guest || "—") + '</td>' +
        '<td class="date-cell">' + formatDate(ep.date) + '</td>' +
        '<td class="topics-cell">' + (ep.topics || []).map(function (t) { return '<span class="tag">' + t + '</span>'; }).join("") + '</td>' +
        '<td class="score-cell">' + ep.score +
        '<div class="score-bar-bg"><div class="score-bar-fill" style="width:' + ep.score + '%"></div></div></td>' +
        '</tr>';

      if (isExpanded) {
        html += renderDetailCard(ep);
      }
    });

    tbody.innerHTML = html;

    // Attach click handlers
    tbody.querySelectorAll("tr:not(.detail-row)").forEach(function (row) {
      row.addEventListener("click", function () {
        var rank = parseInt(this.getAttribute("data-rank"), 10);
        expandedRow = expandedRow === rank ? null : rank;
        renderTable();
      });
    });
  }

  function generateBullets(ep) {
    var summary = ep.summary || "";
    // Split summary into meaningful sentences
    var sentences = summary.split(/(?<=[.!?])\s+/).filter(function (s) { return s.length > 20; });
    var bullets = sentences.slice(0, 7);

    // If we have fewer than 5 bullets, add topic-based ones
    if (bullets.length < 5) {
      (ep.topics || []).forEach(function (t) {
        if (bullets.length < 6) {
          bullets.push("Explores themes in " + t.toLowerCase() + " and related strategies");
        }
      });
    }

    return bullets.slice(0, 7);
  }

  function renderDetailCard(ep) {
    var bullets = generateBullets(ep);
    var bd = ep.score_breakdown || {};

    return '<tr class="detail-row"><td colspan="6"><div class="detail-card">' +
      '<div class="detail-grid">' +
      '<div class="detail-section">' +
      '<h4>Key Discussion Points</h4>' +
      '<ul>' + bullets.map(function (b) { return "<li>" + b + "</li>"; }).join("") + '</ul>' +
      '</div>' +
      '<div class="detail-section">' +
      '<h4>Guest</h4>' +
      '<p class="guest-bio">' + ep.guest + ' appeared on Invest Like the Best ' +
      (ep.number ? '(Episode ' + ep.number + ')' : '') +
      ' on ' + formatDate(ep.date) + '. ' +
      'This conversation covered topics including ' + (ep.topics || []).join(", ").toLowerCase() + '.</p>' +
      '<h4>Score Breakdown</h4>' +
      '<div class="detail-score-grid">' +
      '<div class="mini-stat"><div class="mini-stat-value">' + (bd.guest_prominence || 0) + '</div><div class="mini-stat-label">Guest</div></div>' +
      '<div class="mini-stat"><div class="mini-stat-value">' + (bd.apple_signal || 0) + '</div><div class="mini-stat-label">Apple</div></div>' +
      '<div class="mini-stat"><div class="mini-stat-value">' + (bd.spotify_signal || 0) + '</div><div class="mini-stat-label">Spotify</div></div>' +
      '<div class="mini-stat"><div class="mini-stat-value">' + (bd.topic_relevance || 0) + '</div><div class="mini-stat-label">Topic</div></div>' +
      '<div class="mini-stat"><div class="mini-stat-value">' + (bd.social_engagement || 0) + '</div><div class="mini-stat-label">Social</div></div>' +
      '<div class="mini-stat"><div class="mini-stat-value">' + ep.score + '</div><div class="mini-stat-label">Overall</div></div>' +
      '</div>' +
      '<div class="detail-links">' +
      '<a href="' + ep.apple_link + '" target="_blank" rel="noopener noreferrer">' +
      '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg> Apple Podcasts</a>' +
      '<a href="' + ep.spotify_link + '" target="_blank" rel="noopener noreferrer">' +
      '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg> Spotify</a>' +
      (ep.link ? '<a href="' + ep.link + '" target="_blank" rel="noopener noreferrer">🔗 Show Notes</a>' : '') +
      '</div>' +
      '</div>' +
      '</div>' +
      '</div></td></tr>';
  }

  // ===== PAGINATION =====
  function renderPagination() {
    var totalPages = Math.ceil(filteredEpisodes.length / PAGE_SIZE);
    var container = document.getElementById("pagination");

    if (totalPages <= 1) {
      container.innerHTML = "";
      return;
    }

    var html = '<button class="page-btn" data-page="prev" ' + (currentPage === 1 ? "disabled" : "") + '>← Prev</button>';

    var startPage = Math.max(1, currentPage - 2);
    var endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
      html += '<button class="page-btn" data-page="1">1</button>';
      if (startPage > 2) html += '<span style="color:var(--color-text-faint)">…</span>';
    }

    for (var i = startPage; i <= endPage; i++) {
      html += '<button class="page-btn' + (i === currentPage ? " active" : "") + '" data-page="' + i + '">' + i + '</button>';
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) html += '<span style="color:var(--color-text-faint)">…</span>';
      html += '<button class="page-btn" data-page="' + totalPages + '">' + totalPages + '</button>';
    }

    html += '<button class="page-btn" data-page="next" ' + (currentPage === totalPages ? "disabled" : "") + '>Next →</button>';

    container.innerHTML = html;

    container.querySelectorAll(".page-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var p = this.getAttribute("data-page");
        if (p === "prev") currentPage = Math.max(1, currentPage - 1);
        else if (p === "next") currentPage = Math.min(totalPages, currentPage + 1);
        else currentPage = parseInt(p, 10);
        expandedRow = null;
        renderTable();
        renderPagination();
        document.querySelector(".table-wrapper").scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  }

  // ===== COLUMN SORTING =====
  document.querySelectorAll(".episodes-table th[data-sort]").forEach(function (th) {
    th.addEventListener("click", function () {
      var field = this.getAttribute("data-sort");
      var select = document.getElementById("sort-select");

      if (field === "score") {
        select.value = sortField === "score" && sortDir === "desc" ? "score-asc" : "score-desc";
      } else if (field === "date") {
        select.value = sortField === "date" && sortDir === "desc" ? "date-asc" : "date-desc";
      } else if (field === "guest") {
        select.value = "guest-asc";
      } else if (field === "rank") {
        select.value = "score-desc";
      }

      currentPage = 1;
      expandedRow = null;
      applyFilters();

      // Update sorted class
      document.querySelectorAll(".episodes-table th").forEach(function (h) { h.classList.remove("sorted"); });
      this.classList.add("sorted");
    });
  });

  // ===== EVENT LISTENERS =====
  var debounceTimer;
  document.getElementById("search-input").addEventListener("input", function () {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function () {
      currentPage = 1;
      expandedRow = null;
      applyFilters();
    }, 200);
  });

  document.getElementById("sort-select").addEventListener("change", function () {
    currentPage = 1;
    expandedRow = null;
    applyFilters();
  });

  document.getElementById("date-from").addEventListener("change", function () {
    currentPage = 1;
    expandedRow = null;
    applyFilters();
  });

  document.getElementById("date-to").addEventListener("change", function () {
    currentPage = 1;
    expandedRow = null;
    applyFilters();
  });

  // ===== INIT =====
  renderStats();
  renderTopicTags();
  updateChart();
  applyFilters();

})();
