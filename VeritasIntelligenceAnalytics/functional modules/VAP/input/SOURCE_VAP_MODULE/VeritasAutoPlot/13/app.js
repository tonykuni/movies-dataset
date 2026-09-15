/* global QA_DATA */
(function () {
  "use strict";

  // === COMPANY COLORS ===
  const COMPANY_COLORS = {
    Apple: "#555555",
    Microsoft: "#00a4ef",
    Alphabet: "#4285f4",
    Amazon: "#ff9900",
    Meta: "#0668e1",
    Nvidia: "#76b900",
    Tesla: "#cc0000",
  };

  // === HELPERS ===
  function scoreClass(score) {
    if (score >= 0.6) return "high";
    if (score >= 0.4) return "mid";
    return "low";
  }

  function scoreLabel(score) {
    if (score >= 0.8) return "Very Direct";
    if (score >= 0.65) return "Direct";
    if (score >= 0.5) return "Moderate";
    if (score >= 0.35) return "Evasive";
    return "Very Avoidant";
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function highlightText(text, query) {
    if (!query) return escapeHtml(text);
    const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const regex = new RegExp("(" + escaped + ")", "gi");
    return escapeHtml(text).replace(
      regex,
      '<span class="search-highlight">$1</span>'
    );
  }

  // === COMPUTE LEADERBOARD DATA ===
  function computeLeaderboard(filterRole) {
    const byPerson = {};
    QA_DATA.forEach(function (item) {
      const name = item.rn;
      const title = item.rt || "";
      if (filterRole === "ceo" && !title.toLowerCase().includes("ceo")) return;
      if (filterRole === "cfo" && !title.toLowerCase().includes("cfo")) return;

      if (!byPerson[name]) {
        byPerson[name] = {
          name: name,
          title: title,
          company: item.co,
          scores: [],
        };
      }
      byPerson[name].scores.push(item.sc);
    });

    return Object.values(byPerson)
      .map(function (p) {
        const avg =
          p.scores.reduce(function (a, b) {
            return a + b;
          }, 0) / p.scores.length;
        return {
          name: p.name,
          title: p.title,
          company: p.company,
          avgScore: avg,
          count: p.scores.length,
        };
      })
      .filter(function (p) {
        return p.count >= 3;
      })
      .sort(function (a, b) {
        return b.avgScore - a.avgScore;
      });
  }

  function renderLeaderboard(filterRole) {
    var container = document.getElementById("leaderboard-container");
    var data = computeLeaderboard(filterRole);

    container.innerHTML = data
      .map(function (person, i) {
        var cls = scoreClass(person.avgScore);
        var rankClass = i < 3 ? " rank-" + (i + 1) : "";
        var color = COMPANY_COLORS[person.company] || "#888";
        return (
          '<div class="leaderboard-row' +
          rankClass +
          '" data-person="' +
          escapeHtml(person.name) +
          '">' +
          '<div class="rank">' +
          (i + 1) +
          "</div>" +
          '<div class="person-info">' +
          '<span class="person-name">' +
          escapeHtml(person.name) +
          "</span>" +
          '<span class="person-meta">' +
          '<span class="company-dot" style="background:' +
          color +
          '"></span>' +
          escapeHtml(person.company) +
          " &middot; " +
          escapeHtml(person.title) +
          " &middot; " +
          person.count +
          " answers" +
          "</span>" +
          "</div>" +
          '<div class="bar-container">' +
          '<div class="bar-fill bar-' +
          cls +
          '" style="width:' +
          (person.avgScore * 100).toFixed(0) +
          '%"></div>' +
          "</div>" +
          '<div class="score-badge score-' +
          cls +
          '">' +
          person.avgScore.toFixed(2) +
          "</div>" +
          "</div>"
        );
      })
      .join("");

    // Click to navigate to explorer with filter
    container.querySelectorAll(".leaderboard-row").forEach(function (row) {
      row.addEventListener("click", function () {
        var personName = this.getAttribute("data-person");
        switchTab("explorer");
        document.getElementById("filter-respondent").value = personName;
        document.getElementById("filter-respondent").dispatchEvent(
          new Event("change")
        );
      });
    });
  }

  // === COMPANY SUMMARY ===
  function renderCompanySummary() {
    var container = document.getElementById("company-summary");
    var byCompany = {};
    QA_DATA.forEach(function (item) {
      if (!byCompany[item.co]) {
        byCompany[item.co] = { scores: [], quarters: new Set() };
      }
      byCompany[item.co].scores.push(item.sc);
      byCompany[item.co].quarters.add(item.q);
    });

    var companies = Object.keys(byCompany)
      .map(function (name) {
        var scores = byCompany[name].scores;
        var avg =
          scores.reduce(function (a, b) {
            return a + b;
          }, 0) / scores.length;
        return {
          name: name,
          avg: avg,
          count: scores.length,
          quarters: byCompany[name].quarters.size,
        };
      })
      .sort(function (a, b) {
        return b.avg - a.avg;
      });

    container.innerHTML = companies
      .map(function (co) {
        var cls = scoreClass(co.avg);
        var color = COMPANY_COLORS[co.name] || "#888";
        return (
          '<div class="company-card" style="border-left-color:' +
          color +
          '">' +
          '<div class="company-card-name">' +
          '<span class="company-dot" style="background:' +
          color +
          '"></span>' +
          escapeHtml(co.name) +
          "</div>" +
          '<div class="company-card-score score-' +
          cls +
          '">' +
          co.avg.toFixed(2) +
          "</div>" +
          '<div class="company-card-detail">' +
          co.count +
          " answers across " +
          co.quarters +
          " quarters &middot; " +
          scoreLabel(co.avg) +
          "</div>" +
          "</div>"
        );
      })
      .join("");
  }

  // === EXPLORER ===
  var explorerPage = 0;
  var ITEMS_PER_PAGE = 20;
  var currentFiltered = [];

  function getFilteredData() {
    var company = document.getElementById("filter-company").value;
    var respondent = document.getElementById("filter-respondent").value;
    var quarter = document.getElementById("filter-quarter").value;
    var sort = document.getElementById("sort-by").value;

    var filtered = QA_DATA.filter(function (item) {
      if (company !== "all" && item.co !== company) return false;
      if (respondent !== "all" && item.rn !== respondent) return false;
      if (quarter !== "all" && item.q !== quarter) return false;
      return true;
    });

    if (sort === "score-desc") {
      filtered.sort(function (a, b) {
        return b.sc - a.sc;
      });
    } else if (sort === "score-asc") {
      filtered.sort(function (a, b) {
        return a.sc - b.sc;
      });
    } else if (sort === "company") {
      filtered.sort(function (a, b) {
        return a.co.localeCompare(b.co) || b.sc - a.sc;
      });
    }

    return filtered;
  }

  function renderQACard(item, searchQuery) {
    var cls = scoreClass(item.sc);
    var color = COMPANY_COLORS[item.co] || "#888";
    var questionText = searchQuery
      ? highlightText(item.qn, searchQuery)
      : escapeHtml(item.qn);
    var answerText = searchQuery
      ? highlightText(item.ans, searchQuery)
      : escapeHtml(item.ans);
    var needsCollapse = item.ans.length > 400;

    return (
      '<div class="qa-card">' +
      '<div class="qa-card-header">' +
      '<div class="qa-meta">' +
      '<span class="qa-company-badge" style="background:' +
      color +
      '22;color:' +
      color +
      '">' +
      escapeHtml(item.co) +
      "</span>" +
      '<span class="qa-quarter">' +
      escapeHtml(item.q) +
      "</span>" +
      '<span class="qa-respondent">' +
      escapeHtml(item.rn) +
      "</span>" +
      "</div>" +
      '<div class="qa-score-pill pill-' +
      cls +
      '">' +
      '<span>' +
      item.sc.toFixed(2) +
      "</span>" +
      '<span style="font-weight:400">&middot; ' +
      scoreLabel(item.sc) +
      "</span>" +
      "</div>" +
      "</div>" +
      '<div class="qa-body">' +
      '<div class="qa-question-label">Question</div>' +
      '<div class="qa-analyst">' +
      escapeHtml(item.an) +
      (item.af ? " &middot; " + escapeHtml(item.af) : "") +
      "</div>" +
      '<div class="qa-question-text">' +
      questionText +
      "</div>" +
      '<div class="qa-answer-label">Answer</div>' +
      '<div class="qa-answer-text' +
      (needsCollapse ? " collapsed" : "") +
      '">' +
      answerText +
      "</div>" +
      (needsCollapse
        ? '<button class="qa-expand-btn" onclick="this.previousElementSibling.classList.toggle(\'collapsed\');this.textContent=this.textContent===\'Show more\'?\'Show less\':\'Show more\'">Show more</button>'
        : "") +
      "</div>" +
      "</div>"
    );
  }

  function renderExplorer() {
    currentFiltered = getFilteredData();
    explorerPage = 0;
    var list = document.getElementById("explorer-list");
    var visible = currentFiltered.slice(0, ITEMS_PER_PAGE);

    list.innerHTML = visible
      .map(function (item) {
        return renderQACard(item);
      })
      .join("");

    var stats = document.getElementById("explorer-stats");
    if (currentFiltered.length > 0) {
      var avgScore =
        currentFiltered.reduce(function (sum, item) {
          return sum + item.sc;
        }, 0) / currentFiltered.length;
      stats.innerHTML =
        "Showing " +
        currentFiltered.length +
        " answers &middot; Average directness: <strong class='score-" +
        scoreClass(avgScore) +
        "'>" +
        avgScore.toFixed(2) +
        "</strong> &middot; " +
        scoreLabel(avgScore);
    } else {
      stats.innerHTML = "No results match your filters.";
    }

    var loadMore = document.querySelector(".load-more-container");
    if (currentFiltered.length > ITEMS_PER_PAGE) {
      loadMore.classList.remove("hidden");
    } else {
      loadMore.classList.add("hidden");
    }
  }

  function loadMoreExplorer() {
    explorerPage++;
    var start = explorerPage * ITEMS_PER_PAGE;
    var end = start + ITEMS_PER_PAGE;
    var visible = currentFiltered.slice(start, end);
    var list = document.getElementById("explorer-list");

    visible.forEach(function (item) {
      list.insertAdjacentHTML("beforeend", renderQACard(item));
    });

    if (end >= currentFiltered.length) {
      document.querySelector(".load-more-container").classList.add("hidden");
    }
  }

  function populateFilters() {
    // Respondents
    var respondents = {};
    QA_DATA.forEach(function (item) {
      if (!respondents[item.rn]) {
        respondents[item.rn] = item.co;
      }
    });
    var select = document.getElementById("filter-respondent");
    select.innerHTML = '<option value="all">All Respondents</option>';
    Object.keys(respondents)
      .sort()
      .forEach(function (name) {
        var opt = document.createElement("option");
        opt.value = name;
        opt.textContent = name + " (" + respondents[name] + ")";
        select.appendChild(opt);
      });

    // Quarters
    var quarters = new Set();
    QA_DATA.forEach(function (item) {
      quarters.add(item.q);
    });
    var qSelect = document.getElementById("filter-quarter");
    qSelect.innerHTML = '<option value="all">All Quarters</option>';
    Array.from(quarters)
      .sort()
      .forEach(function (q) {
        var opt = document.createElement("option");
        opt.value = q;
        opt.textContent = q;
        qSelect.appendChild(opt);
      });
  }

  // === SEARCH ===
  var searchTimeout;
  function handleSearch() {
    var query = document.getElementById("search-input").value.trim();
    var results = document.getElementById("search-results");
    var empty = document.getElementById("search-empty");

    if (query.length < 2) {
      results.innerHTML = "";
      empty.style.display = "block";
      return;
    }

    var lower = query.toLowerCase();
    var matches = QA_DATA.filter(function (item) {
      return (
        item.qn.toLowerCase().includes(lower) ||
        item.ans.toLowerCase().includes(lower) ||
        item.an.toLowerCase().includes(lower) ||
        item.rn.toLowerCase().includes(lower) ||
        item.co.toLowerCase().includes(lower)
      );
    }).sort(function (a, b) {
      // Prioritize matches in question text
      var aInQ = a.qn.toLowerCase().includes(lower) ? 1 : 0;
      var bInQ = b.qn.toLowerCase().includes(lower) ? 1 : 0;
      return bInQ - aInQ || b.sc - a.sc;
    });

    empty.style.display = matches.length === 0 ? "block" : "none";

    if (matches.length === 0) {
      empty.innerHTML =
        '<p>No results for "' +
        escapeHtml(query) +
        '"</p><p class="search-hint">Try a broader search term</p>';
      results.innerHTML = "";
      return;
    }

    var shown = matches.slice(0, 30);
    results.innerHTML =
      '<p style="font-size:var(--text-sm);color:var(--color-text-muted);margin-bottom:var(--space-4)">' +
      matches.length +
      " result" +
      (matches.length === 1 ? "" : "s") +
      " found</p>" +
      shown
        .map(function (item) {
          return renderQACard(item, query);
        })
        .join("");
  }

  // === TAB SWITCHING ===
  function switchTab(tabName) {
    document.querySelectorAll(".tab-panel").forEach(function (panel) {
      panel.classList.remove("active");
    });
    document.querySelectorAll(".nav-btn").forEach(function (btn) {
      btn.classList.remove("active");
    });
    document.getElementById("tab-" + tabName).classList.add("active");
    document
      .querySelector('[data-tab="' + tabName + '"]')
      .classList.add("active");

    if (tabName === "search") {
      setTimeout(function () {
        document.getElementById("search-input").focus();
      }, 100);
    }
  }

  // === THEME TOGGLE ===
  (function () {
    var toggle = document.querySelector("[data-theme-toggle]");
    var root = document.documentElement;
    var currentTheme = matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
    root.setAttribute("data-theme", currentTheme);
    if (toggle) {
      updateToggleIcon(toggle, currentTheme);
      toggle.addEventListener("click", function () {
        currentTheme = currentTheme === "dark" ? "light" : "dark";
        root.setAttribute("data-theme", currentTheme);
        toggle.setAttribute(
          "aria-label",
          "Switch to " + (currentTheme === "dark" ? "light" : "dark") + " mode"
        );
        updateToggleIcon(toggle, currentTheme);
      });
    }

    function updateToggleIcon(el, theme) {
      if (theme === "dark") {
        el.innerHTML =
          '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';
      } else {
        el.innerHTML =
          '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
      }
    }
  })();

  // === INIT ===
  renderLeaderboard("all");
  renderCompanySummary();
  populateFilters();
  renderExplorer();

  // Event listeners
  document.querySelectorAll(".nav-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      switchTab(this.getAttribute("data-tab"));
    });
  });

  document
    .getElementById("leaderboard-filter")
    .addEventListener("change", function () {
      renderLeaderboard(this.value);
    });

  ["filter-company", "filter-respondent", "filter-quarter", "sort-by"].forEach(
    function (id) {
      document.getElementById(id).addEventListener("change", renderExplorer);
    }
  );

  document
    .getElementById("load-more-btn")
    .addEventListener("click", loadMoreExplorer);

  document
    .getElementById("search-input")
    .addEventListener("input", function () {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(handleSearch, 200);
    });

  // Keyboard shortcut: / to focus search
  document.addEventListener("keydown", function (e) {
    if (
      e.key === "/" &&
      !e.ctrlKey &&
      !e.metaKey &&
      document.activeElement.tagName !== "INPUT"
    ) {
      e.preventDefault();
      switchTab("search");
    }
  });
})();
