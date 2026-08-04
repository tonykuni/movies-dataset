(function () {
  "use strict";

  let allData = [];
  let filteredData = [];
  let markers = [];
  let map;
  let activeStatus = "all";
  let activeCompany = "all";
  let activeRegion = "all";
  let searchTerm = "";
  let statsOpen = true;

  const STATUS_COLORS = {
    under_construction: "#f59e0b",
    announced: "#8b5cf6",
    planned: "#6366f1",
    operational: "#22c55e",
  };

  const STATUS_LABELS = {
    under_construction: "Under Construction",
    announced: "Announced",
    planned: "Planned",
    operational: "Operational",
  };

  /* ── Company Colors ── */
  const COMPANY_COLORS = {
    Microsoft: "#00a4ef",
    Google: "#4285f4",
    Meta: "#0866ff",
    "Amazon (AWS)": "#ff9900",
    Oracle: "#f80000",
    xAI: "#1a1a2e",
    Apple: "#a2aaad",
    CoreWeave: "#7c3aed",
    SoftBank: "#e60012",
    "Digital Realty": "#2563eb",
    Equinix: "#ed1c24",
    "Applied Digital": "#06b6d4",
    NVIDIA: "#76b900",
  };

  /* ── Init ── */
  async function init() {
    initMap();
    await loadData();
    populateFilters();
    applyFilters();
    updateStats();
    bindEvents();
  }

  /* ── Map ── */
  function initMap() {
    map = L.map("map", {
      center: [25, 0],
      zoom: 3,
      minZoom: 2,
      maxZoom: 16,
      zoomControl: true,
      attributionControl: true,
    });

    /* Light tile layer (default) */
    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> &copy; <a href="https://carto.com/" target="_blank" rel="noopener noreferrer">CARTO</a>',
        subdomains: "abcd",
        maxZoom: 20,
      }
    ).addTo(map);

    /* Legend control */
    const legend = L.control({ position: "bottomright" });
    legend.onAdd = function () {
      const div = L.DomUtil.create("div", "map-legend");
      div.innerHTML = `
        <div class="legend-title">Status</div>
        <div class="legend-item"><span class="legend-dot" style="background:${STATUS_COLORS.under_construction}"></span>Under Construction</div>
        <div class="legend-item"><span class="legend-dot" style="background:${STATUS_COLORS.announced}"></span>Announced</div>
        <div class="legend-item"><span class="legend-dot" style="background:${STATUS_COLORS.planned}"></span>Planned</div>
        <div class="legend-item"><span class="legend-dot" style="background:${STATUS_COLORS.operational}"></span>Operational</div>
        <div style="margin-top:6px;border-top:1px solid var(--border);padding-top:6px;">
          <div class="legend-title">Size = Investment</div>
          <div class="legend-item"><span class="legend-dot" style="width:8px;height:8px"></span>&lt; $5B</div>
          <div class="legend-item"><span class="legend-dot" style="width:12px;height:12px"></span>$5B - $15B</div>
          <div class="legend-item"><span class="legend-dot" style="width:16px;height:16px"></span>&gt; $15B</div>
        </div>
      `;
      return div;
    };
    legend.addTo(map);
  }

  /* ── Data ── */
  async function loadData() {
    try {
      const resp = await fetch("./data.json");
      allData = await resp.json();
    } catch (e) {
      console.error("Failed to load data:", e);
      allData = [];
    }
  }

  /* ── Filters ── */
  function populateFilters() {
    const companies = [...new Set(allData.map((d) => d.company))].sort();
    const regions = [...new Set(allData.map((d) => d.region))].sort();

    const compSel = document.getElementById("companyFilter");
    companies.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      compSel.appendChild(opt);
    });

    const regSel = document.getElementById("regionFilter");
    regions.forEach((r) => {
      const opt = document.createElement("option");
      opt.value = r;
      opt.textContent = r;
      regSel.appendChild(opt);
    });
  }

  function applyFilters() {
    const term = searchTerm.toLowerCase().trim();

    filteredData = allData.filter((d) => {
      if (activeStatus !== "all" && d.status !== activeStatus) return false;
      if (activeCompany !== "all" && d.company !== activeCompany) return false;
      if (activeRegion !== "all" && d.region !== activeRegion) return false;
      if (term) {
        const hay = (
          d.name +
          " " +
          d.company +
          " " +
          d.location +
          " " +
          d.details
        ).toLowerCase();
        if (!hay.includes(term)) return false;
      }
      return true;
    });

    renderMarkers();
    updateStats();
    document.getElementById("countBadge").textContent =
      filteredData.length + " facilities";
  }

  /* ── Markers ── */
  function renderMarkers() {
    /* Clear existing */
    markers.forEach((m) => map.removeLayer(m));
    markers = [];

    filteredData.forEach((d) => {
      const inv = d.investment_num || 0;
      let sizeClass = "";
      let markerSize = 14;
      if (inv > 15e9) {
        sizeClass = "size-mega";
        markerSize = 22;
      } else if (inv > 5e9) {
        sizeClass = "size-large";
        markerSize = 18;
      }

      const icon = L.divIcon({
        className: "",
        html: `<div class="dc-marker status-${d.status} ${sizeClass}"></div>`,
        iconSize: [markerSize, markerSize],
        iconAnchor: [markerSize / 2, markerSize / 2],
      });

      const marker = L.marker([d.lat, d.lng], { icon: icon });

      /* Tooltip */
      let invDisplay = "Undisclosed";
      if (d.investment && d.investment !== "Not disclosed") {
        let raw = d.investment.split("(")[0].trim();
        /* Further shorten for tooltip: extract just the dollar figure */
        const dollarMatch = raw.match(/(\$[\d.]+\s*(?:billion|million|trillion|B|M|T))/i);
        invDisplay = dollarMatch ? dollarMatch[1] : (raw.length > 15 ? raw.substring(0, 15) + "..." : raw);
      }
      let capDisplay = d.capacity || "N/A";
      /* Truncate long capacity strings for tooltip */
      if (capDisplay.length > 20) {
        const mwMatch = capDisplay.match(/(\d[\d,.]*\s*(?:MW|GW|mw|gw))/i);
        capDisplay = mwMatch ? mwMatch[1] : capDisplay.substring(0, 20) + "...";
      }

      marker.bindTooltip(
        `<div class="tooltip-company">${escHtml(d.company)}</div>
       <div class="tooltip-name">${escHtml(d.name)}</div>
       <div class="tooltip-location">${escHtml(d.location)}</div>
       <div class="tooltip-meta">
         <div class="tooltip-meta-item">
           <span class="tooltip-meta-label">Investment</span>
           <span class="tooltip-meta-value">${escHtml(invDisplay)}</span>
         </div>
         <div class="tooltip-meta-item">
           <span class="tooltip-meta-label">Capacity</span>
           <span class="tooltip-meta-value">${escHtml(capDisplay)}</span>
         </div>
       </div>`,
        {
          className: "dc-tooltip",
          direction: "top",
          offset: [0, -8],
          opacity: 1,
        }
      );

      marker.on("click", function () {
        openDetail(d);
      });

      marker.addTo(map);
      markers.push(marker);
    });
  }

  /* ── Detail Panel ── */
  function openDetail(d) {
    const panel = document.getElementById("detailPanel");
    const content = document.getElementById("detailContent");

    const statusLabel = STATUS_LABELS[d.status] || d.status;
    const invDisplay =
      d.investment && d.investment !== "Not disclosed"
        ? d.investment
        : "Not disclosed";

    let metricsHtml = "";

    if (d.investment && d.investment !== "Not disclosed") {
      metricsHtml += `<div class="detail-metric">
        <div class="detail-metric-label">Investment</div>
        <div class="detail-metric-value">${escHtml(d.investment.split("(")[0].trim())}</div>
      </div>`;
    }

    if (d.capacity) {
      metricsHtml += `<div class="detail-metric">
        <div class="detail-metric-label">Power Capacity</div>
        <div class="detail-metric-value">${escHtml(d.capacity)}</div>
      </div>`;
    }

    if (d.gpu_count && d.gpu_count !== "Not disclosed") {
      metricsHtml += `<div class="detail-metric">
        <div class="detail-metric-label">GPUs</div>
        <div class="detail-metric-value">${escHtml(d.gpu_count)}</div>
      </div>`;
    }

    if (d.timeline) {
      metricsHtml += `<div class="detail-metric">
        <div class="detail-metric-label">Timeline</div>
        <div class="detail-metric-value">${escHtml(d.timeline)}</div>
      </div>`;
    }

    content.innerHTML = `
      <div class="detail-header">
        <div class="detail-company">${escHtml(d.company)}</div>
        <h2 class="detail-name">${escHtml(d.name)}</h2>
        <div class="detail-location">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
          ${escHtml(d.location)}
        </div>
        <div class="detail-status-badge ${d.status}">
          <span class="dot dot-${d.status === "under_construction" ? "construction" : d.status}"></span>
          ${statusLabel}
        </div>
      </div>
      <div class="detail-grid">${metricsHtml}</div>
      ${
        d.details
          ? `<div class="detail-section">
        <div class="detail-section-title">Details</div>
        <p class="detail-description">${escHtml(d.details)}</p>
      </div>`
          : ""
      }
      ${
        d.source_url
          ? `<a href="${escAttr(d.source_url)}" target="_blank" rel="noopener noreferrer" class="detail-source">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
        Source
      </a>`
          : ""
      }
    `;

    panel.classList.add("open");

    /* Center map on this point */
    map.flyTo([d.lat, d.lng], Math.max(map.getZoom(), 6), {
      duration: 0.8,
    });
  }

  function closeDetail() {
    document.getElementById("detailPanel").classList.remove("open");
  }

  /* ── Stats ── */
  function updateStats() {
    const data = filteredData;

    document.getElementById("statTotal").textContent = data.length;
    document.getElementById("statConstruction").textContent = data.filter(
      (d) => d.status === "under_construction"
    ).length;

    /* Total investment */
    const totalInv = data.reduce((sum, d) => sum + (d.investment_num || 0), 0);
    document.getElementById("statInvestment").textContent =
      formatDollars(totalInv);

    /* Top company */
    const companyCounts = {};
    data.forEach((d) => {
      companyCounts[d.company] = (companyCounts[d.company] || 0) + 1;
    });
    const sorted = Object.entries(companyCounts).sort((a, b) => b[1] - a[1]);
    document.getElementById("statTopCompany").textContent = sorted.length
      ? sorted[0][0]
      : "-";

    /* Region bars */
    const regionCounts = {};
    data.forEach((d) => {
      regionCounts[d.region] = (regionCounts[d.region] || 0) + 1;
    });
    const maxRegion = Math.max(...Object.values(regionCounts), 1);
    let regionHtml = "";
    Object.entries(regionCounts)
      .sort((a, b) => b[1] - a[1])
      .forEach(([r, n]) => {
        regionHtml += `<div class="stat-bar-row">
        <span class="stat-bar-label">${escHtml(r)}</span>
        <div class="stat-bar-track"><div class="stat-bar-fill" style="width:${(n / maxRegion) * 100}%"></div></div>
        <span class="stat-bar-count">${n}</span>
      </div>`;
      });
    document.getElementById("regionStats").innerHTML = regionHtml;

    /* Company bars (top 8) */
    const maxComp = sorted.length ? sorted[0][1] : 1;
    let compHtml = "";
    sorted.slice(0, 8).forEach(([c, n]) => {
      compHtml += `<div class="stat-bar-row">
        <span class="stat-bar-label">${escHtml(c)}</span>
        <div class="stat-bar-track"><div class="stat-bar-fill" style="width:${(n / maxComp) * 100}%"></div></div>
        <span class="stat-bar-count">${n}</span>
      </div>`;
    });
    document.getElementById("companyStats").innerHTML = compHtml;
  }

  /* ── Events ── */
  function bindEvents() {
    /* Status chips */
    document.querySelectorAll("#statusFilters .chip").forEach((chip) => {
      chip.addEventListener("click", function () {
        document
          .querySelectorAll("#statusFilters .chip")
          .forEach((c) => c.classList.remove("active"));
        this.classList.add("active");
        activeStatus = this.dataset.filter;
        applyFilters();
      });
    });

    /* Company select */
    document
      .getElementById("companyFilter")
      .addEventListener("change", function () {
        activeCompany = this.value;
        applyFilters();
      });

    /* Region select */
    document
      .getElementById("regionFilter")
      .addEventListener("change", function () {
        activeRegion = this.value;
        applyFilters();
      });

    /* Search */
    let searchTimeout;
    document
      .getElementById("searchInput")
      .addEventListener("input", function () {
        clearTimeout(searchTimeout);
        const val = this.value;
        searchTimeout = setTimeout(function () {
          searchTerm = val;
          applyFilters();
        }, 200);
      });

    /* Stats toggle */
    document
      .getElementById("statsToggle")
      .addEventListener("click", function () {
        statsOpen = !statsOpen;
        const content = document.getElementById("statsContent");
        if (statsOpen) {
          content.classList.remove("collapsed");
        } else {
          content.classList.add("collapsed");
        }
      });

    /* Detail close */
    document
      .getElementById("detailClose")
      .addEventListener("click", closeDetail);

    /* Close detail on Escape */
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeDetail();
    });

    /* Click map to close detail */
    map.on("click", function (e) {
      /* Only close if not clicking a marker */
      if (!e.originalEvent.target.closest(".dc-marker")) {
        closeDetail();
      }
    });
  }

  /* ── Helpers ── */
  function escHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function escAttr(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function formatDollars(num) {
    if (num >= 1e12) return "$" + (num / 1e12).toFixed(1) + "T";
    if (num >= 1e9) return "$" + (num / 1e9).toFixed(0) + "B";
    if (num >= 1e6) return "$" + (num / 1e6).toFixed(0) + "M";
    if (num > 0) return "$" + num.toLocaleString();
    return "$0";
  }

  /* ── Go ── */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
