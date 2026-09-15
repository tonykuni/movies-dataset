/* Big Mac Index — Interactive Choropleth Explorer */
/* global topojson */
(function () {
  "use strict";

  /* ── Theme toggle ── */
  const themeToggle = document.querySelector("[data-theme-toggle]");
  const root = document.documentElement;
  let theme = window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
  root.setAttribute("data-theme", theme);

  function updateThemeIcon() {
    if (!themeToggle) return;
    themeToggle.innerHTML =
      theme === "dark"
        ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
        : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    themeToggle.setAttribute(
      "aria-label",
      "Switch to " + (theme === "dark" ? "light" : "dark") + " mode"
    );
  }
  updateThemeIcon();

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      theme = theme === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", theme);
      updateThemeIcon();
      renderLegend();
      if (trendChart) updateTrendChartColors();
    });
  }

  /* ── State ── */
  let bmData = null;
  let geoData = null;
  let currentDateIndex = 41;
  let selectedCountryIso = null;
  let sortKey = "name";
  let sortAsc = true;
  let playing = false;
  let playTimer = null;
  let trendChart = null;

  /* ── ISO mapping for GeoJSON (some codes differ) ── */
  const isoMap = {
    EUZ: null, /* Euro area doesn't map to a single country */
  };

  /* Special mapping: Big Mac uses some non-standard ISO codes */
  const geoToDataMap = {};

  /* ── Color scale: red (overvalued) → white/neutral → green (undervalued) ── */
  function getColor(val) {
    if (val === null || val === undefined) return "var(--color-map-nodata)";
    const clamped = Math.max(-80, Math.min(80, val));
    if (clamped > 0) {
      /* Overvalued: interpolate neutral → red */
      const t = Math.min(clamped / 80, 1);
      return d3.interpolateRgb("#f5f5ef", "#c0392b")(t);
    } else if (clamped < 0) {
      /* Undervalued: interpolate neutral → green */
      const t = Math.min(Math.abs(clamped) / 80, 1);
      return d3.interpolateRgb("#f5f5ef", "#27ae60")(t);
    }
    return "#f5f5ef";
  }

  function getColorForTheme(val) {
    if (val === null || val === undefined) return null;
    const clamped = Math.max(-80, Math.min(80, val));
    const isDark = root.getAttribute("data-theme") === "dark";
    /* Use a warm white/gray as center so countries stand out from bg */
    const neutral = isDark ? "#555550" : "#f5f0e0";
    const red = isDark ? "#e74c3c" : "#c0392b";
    const green = isDark ? "#2ecc71" : "#1e8449";

    if (clamped > 0) {
      const t = Math.min(clamped / 80, 1);
      return d3.interpolateRgb(neutral, red)(t);
    } else if (clamped < 0) {
      const t = Math.min(Math.abs(clamped) / 80, 1);
      return d3.interpolateRgb(neutral, green)(t);
    }
    return neutral;
  }

  /* ── Load data ── */
  async function init() {
    const [dataResp, worldResp] = await Promise.all([
      fetch("./assets/bigmac-data.json").then(function (r) { return r.json(); }),
      fetch(
        "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json"
      ).then(function (r) { return r.json(); }),
    ]);
    bmData = dataResp;
    geoData = worldResp;

    /* Build geo-to-data mapping using numeric→alpha ISO */
    buildIsoMapping();

    /* Setup slider */
    const slider = document.getElementById("year-slider");
    slider.max = bmData.dates.length - 1;
    slider.value = bmData.dates.length - 1;
    currentDateIndex = bmData.dates.length - 1;

    slider.addEventListener("input", function () {
      currentDateIndex = parseInt(this.value);
      update();
    });

    /* Play button */
    document.getElementById("play-btn").addEventListener("click", togglePlay);

    /* Tabs */
    document.querySelectorAll(".tab-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        document.querySelectorAll(".tab-btn").forEach(function (b) {
          b.classList.remove("active");
        });
        btn.classList.add("active");
        const tab = btn.dataset.tab;
        document.getElementById("panel-table").style.display =
          tab === "table" ? "flex" : "none";
        document.getElementById("panel-chart").style.display =
          tab === "chart" ? "flex" : "none";
        if (tab === "chart" && selectedCountryIso) {
          renderTrendChart(selectedCountryIso);
        }
      });
    });

    /* Sort headers */
    document.querySelectorAll(".sortable").forEach(function (el) {
      el.addEventListener("click", function () {
        const key = el.dataset.sort;
        if (sortKey === key) {
          sortAsc = !sortAsc;
        } else {
          sortKey = key;
          sortAsc = key === "name";
        }
        updateSortIndicators();
        renderTable();
      });
    });

    renderMap();
    renderLegend();
    update();
  }

  /* ── ISO numeric-to-alpha mapping ── */
  const numericToAlpha3 = {};

  function buildIsoMapping() {
    /* Standard ISO 3166-1 numeric to alpha-3 */
    const map = {
      "004":"AFG","008":"ALB","012":"DZA","020":"AND","024":"AGO",
      "028":"ATG","032":"ARG","036":"AUS","040":"AUT","031":"AZE",
      "044":"BHS","048":"BHR","050":"BGD","051":"ARM","052":"BRB",
      "056":"BEL","060":"BMU","064":"BTN","068":"BOL","070":"BIH",
      "072":"BWA","076":"BRA","084":"BLZ","086":"IOT","090":"SLB",
      "092":"VGB","096":"BRN","100":"BGR","104":"MMR","108":"BDI",
      "112":"BLR","116":"KHM","120":"CMR","124":"CAN","132":"CPV",
      "140":"CAF","144":"LKA","148":"TCD","152":"CHL","156":"CHN",
      "158":"TWN","170":"COL","174":"COM","175":"MYT","178":"COG",
      "180":"COD","184":"COK","188":"CRI","191":"HRV","192":"CUB",
      "196":"CYP","203":"CZE","204":"BEN","208":"DNK","212":"DMA",
      "214":"DOM","218":"ECU","818":"EGY","222":"SLV","226":"GNQ",
      "231":"ETH","232":"ERI","233":"EST","234":"FRO","238":"FLK",
      "242":"FJI","246":"FIN","250":"FRA","254":"GUF","258":"PYF",
      "260":"ATF","266":"GAB","270":"GMB","268":"GEO","276":"DEU",
      "288":"GHA","292":"GIB","296":"KIR","300":"GRC","304":"GRL",
      "308":"GRD","312":"GLP","316":"GUM","320":"GTM","324":"GIN",
      "328":"GUY","332":"HTI","336":"VAT","340":"HND","344":"HKG",
      "348":"HUN","352":"ISL","356":"IND","360":"IDN","364":"IRN",
      "368":"IRQ","372":"IRL","376":"ISR","380":"ITA","384":"CIV",
      "388":"JAM","392":"JPN","398":"KAZ","400":"JOR","404":"KEN",
      "408":"PRK","410":"KOR","414":"KWT","417":"KGZ","418":"LAO",
      "422":"LBN","426":"LSO","428":"LVA","430":"LBR","434":"LBY",
      "438":"LIE","440":"LTU","442":"LUX","446":"MAC","450":"MDG",
      "454":"MWI","458":"MYS","462":"MDV","466":"MLI","470":"MLT",
      "474":"MTQ","478":"MRT","480":"MUS","484":"MEX","492":"MCO",
      "496":"MNG","498":"MDA","499":"MNE","504":"MAR","508":"MOZ",
      "512":"OMN","516":"NAM","520":"NRU","524":"NPL","528":"NLD",
      "530":"ANT","533":"ABW","540":"NCL","554":"NZL","558":"NIC",
      "562":"NER","566":"NGA","570":"NIU","574":"NFK","578":"NOR",
      "580":"MNP","583":"FSM","584":"MHL","585":"PLW","586":"PAK",
      "591":"PAN","598":"PNG","600":"PRY","604":"PER","608":"PHL",
      "612":"PCN","616":"POL","620":"PRT","624":"GNB","626":"TLS",
      "630":"PRI","634":"QAT","638":"REU","642":"ROU","643":"RUS",
      "646":"RWA","654":"SHN","659":"KNA","660":"AIA","662":"LCA",
      "666":"SPM","670":"VCT","674":"SMR","678":"STP","682":"SAU",
      "686":"SEN","688":"SRB","690":"SYC","694":"SLE","702":"SGP",
      "703":"SVK","704":"VNM","705":"SVN","706":"SOM","710":"ZAF",
      "716":"ZWE","724":"ESP","728":"SSD","729":"SDN","732":"ESH",
      "736":"SDN","740":"SUR","744":"SJM","748":"SWZ","752":"SWE",
      "756":"CHE","760":"SYR","762":"TJK","764":"THA","768":"TGO",
      "772":"TKL","776":"TON","780":"TTO","784":"ARE","788":"TUN",
      "792":"TUR","795":"TKM","796":"TCA","798":"TUV","800":"UGA",
      "804":"UKR","826":"GBR","834":"TZA","840":"USA","850":"VIR",
      "854":"BFA","858":"URY","860":"UZB","862":"VEN","876":"WLF",
      "882":"WSM","887":"YEM","894":"ZMB",
      /* Kosovo */
      "-99":"XKX","900":"XKX",
    };

    Object.entries(map).forEach(function (entry) {
      numericToAlpha3[entry[0]] = entry[1];
    });
  }

  function getDataIso(geoFeature) {
    const numId = geoFeature.id;
    const alpha3 = numericToAlpha3[numId];
    if (!alpha3) return null;
    if (bmData.countries[alpha3]) return alpha3;
    return null;
  }

  /* ── Render map ── */
  let projection, path, svg, g;

  function renderMap() {
    const container = document.getElementById("map-svg-wrap");
    const rect = container.getBoundingClientRect();
    const w = rect.width || 800;
    const h = rect.height || 500;

    svg = d3.select(container).append("svg")
      .attr("viewBox", "0 0 " + w + " " + h)
      .attr("preserveAspectRatio", "xMidYMid meet");

    projection = d3.geoNaturalEarth1()
      .fitSize([w - 10, h - 10], topojson.feature(geoData, geoData.objects.countries))
      .translate([w / 2, h / 2]);

    path = d3.geoPath().projection(projection);

    const countries = topojson.feature(geoData, geoData.objects.countries);

    g = svg.append("g");

    g.selectAll("path")
      .data(countries.features)
      .join("path")
      .attr("d", path)
      .attr("class", "country-path")
      .attr("stroke", "var(--color-map-stroke)")
      .attr("stroke-width", 0.5)
      .attr("fill", "var(--color-map-nodata)")
      .on("mousemove", onMouseMove)
      .on("mouseleave", onMouseLeave)
      .on("click", onCountryClick);

    /* Zoom */
    const zoom = d3.zoom()
      .scaleExtent([1, 8])
      .on("zoom", function (event) {
        g.attr("transform", event.transform);
      });

    svg.call(zoom);
  }

  function onMouseMove(event, d) {
    const iso = getDataIso(d);
    const dateKey = bmData.dates[currentDateIndex];
    const entry = iso && bmData.data[dateKey] ? bmData.data[dateKey][iso] : null;

    const tooltip = document.getElementById("tooltip");
    if (!entry) {
      tooltip.classList.remove("visible");
      return;
    }

    const valSign = entry.valuation > 0 ? "+" : "";
    const valClass = entry.valuation > 0 ? "overvalued" : entry.valuation < 0 ? "undervalued" : "neutral";

    tooltip.innerHTML =
      '<div class="tt-name">' + entry.name + "</div>" +
      '<div class="tt-row"><span>Local price</span><span class="tt-val">' +
      entry.currency + " " + formatNum(entry.local_price) + "</span></div>" +
      '<div class="tt-row"><span>USD equivalent</span><span class="tt-val">$' +
      (entry.dollar_price !== null ? entry.dollar_price.toFixed(2) : "N/A") + "</span></div>" +
      '<div class="tt-valuation ' + valClass + '">' +
      valSign + (entry.valuation !== null ? entry.valuation.toFixed(1) : "N/A") + "% vs USD</div>";

    tooltip.classList.add("visible");

    /* Position */
    const tx = event.clientX + 14;
    const ty = event.clientY - 10;
    const tw = tooltip.offsetWidth;
    const th = tooltip.offsetHeight;

    tooltip.style.left = (tx + tw > window.innerWidth ? event.clientX - tw - 10 : tx) + "px";
    tooltip.style.top = (ty + th > window.innerHeight ? event.clientY - th - 10 : ty) + "px";

    /* Highlight */
    d3.select(event.currentTarget)
      .raise()
      .attr("stroke", "var(--color-text)")
      .attr("stroke-width", 1.5);
  }

  function onMouseLeave(event) {
    document.getElementById("tooltip").classList.remove("visible");
    d3.select(event.currentTarget)
      .attr("stroke", "var(--color-map-stroke)")
      .attr("stroke-width", 0.5);
  }

  function onCountryClick(event, d) {
    const iso = getDataIso(d);
    if (!iso) return;
    selectCountry(iso);
  }

  function selectCountry(iso) {
    selectedCountryIso = iso;
    renderTable();
    /* Switch to chart tab */
    document.querySelectorAll(".tab-btn").forEach(function (b) { b.classList.remove("active"); });
    document.querySelector('[data-tab="chart"]').classList.add("active");
    document.getElementById("panel-table").style.display = "none";
    document.getElementById("panel-chart").style.display = "flex";
    renderTrendChart(iso);
  }

  /* ── Update view ── */
  function update() {
    const dateKey = bmData.dates[currentDateIndex];
    const yearStr = dateKey.substring(0, 4);
    document.getElementById("year-display").textContent = yearStr;
    document.getElementById("year-slider").value = currentDateIndex;

    const dateData = bmData.data[dateKey] || {};

    /* Update map colors */
    g.selectAll("path").each(function (d) {
      const iso = getDataIso(d);
      const entry = iso ? dateData[iso] : null;
      const color = entry ? getColorForTheme(entry.valuation) : null;
      d3.select(this).attr("fill", color || "var(--color-map-nodata)");
    });

    renderTable();
  }

  /* ── Table ── */
  function renderTable() {
    const dateKey = bmData.dates[currentDateIndex];
    const dateData = bmData.data[dateKey] || {};

    let rows = Object.entries(dateData).map(function (entry) {
      return { iso: entry[0], ...entry[1] };
    });

    /* Sort */
    rows.sort(function (a, b) {
      let va = a[sortKey];
      let vb = b[sortKey];
      if (va === null || va === undefined) va = sortKey === "name" ? "zzz" : -9999;
      if (vb === null || vb === undefined) vb = sortKey === "name" ? "zzz" : -9999;
      if (typeof va === "string") {
        return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
      }
      return sortAsc ? va - vb : vb - va;
    });

    const tbody = document.getElementById("table-body");
    tbody.innerHTML = rows
      .map(function (r) {
        const valClass = r.valuation > 0 ? "overvalued" : r.valuation < 0 ? "undervalued" : "neutral";
        const valSign = r.valuation > 0 ? "+" : "";
        const selected = r.iso === selectedCountryIso ? " selected" : "";
        return (
          '<div class="table-row' + selected + '" data-iso="' + r.iso + '">' +
          '<span class="country-name">' + r.name + "</span>" +
          '<span class="val-cell ' + valClass + '">' +
          (r.valuation !== null ? valSign + r.valuation.toFixed(1) + "%" : "—") +
          "</span>" +
          '<span class="price-cell">$' +
          (r.dollar_price !== null ? r.dollar_price.toFixed(2) : "—") +
          "</span></div>"
        );
      })
      .join("");

    /* Click rows */
    tbody.querySelectorAll(".table-row").forEach(function (row) {
      row.addEventListener("click", function () {
        selectCountry(row.dataset.iso);
      });
    });
  }

  function updateSortIndicators() {
    document.querySelectorAll(".sortable").forEach(function (el) {
      el.classList.remove("active", "asc", "desc");
      if (el.dataset.sort === sortKey) {
        el.classList.add("active", sortAsc ? "asc" : "desc");
      }
    });
  }

  /* ── Trend chart ── */
  function renderTrendChart(iso) {
    const name = bmData.countries[iso] || iso;
    document.getElementById("chart-country-label").textContent = name + " — Valuation Trend";

    const labels = [];
    const values = [];

    bmData.dates.forEach(function (d) {
      const entry = bmData.data[d] ? bmData.data[d][iso] : null;
      if (entry && entry.valuation !== null) {
        labels.push(d.substring(0, 7));
        values.push(entry.valuation);
      }
    });

    const ctx = document.getElementById("trend-chart").getContext("2d");

    if (trendChart) {
      trendChart.destroy();
    }

    const isDark = root.getAttribute("data-theme") === "dark";
    const gridColor = isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)";
    const textColor = isDark ? "#8a8985" : "#6b6a66";
    const zeroColor = isDark ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.12)";

    trendChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "% vs USD",
            data: values,
            borderColor: function (context) {
              const val = context.raw;
              if (val === undefined) return textColor;
              return val >= 0 ? (isDark ? "#e74c3c" : "#c0392b") : (isDark ? "#2ecc71" : "#27ae60");
            },
            segment: {
              borderColor: function (ctx) {
                const v = ctx.p1.raw;
                return v >= 0 ? (isDark ? "#e74c3c" : "#c0392b") : (isDark ? "#2ecc71" : "#27ae60");
              },
            },
            backgroundColor: "transparent",
            borderWidth: 2.5,
            pointRadius: 3,
            pointHoverRadius: 5,
            pointBackgroundColor: function (context) {
              const val = context.raw;
              if (val === undefined) return textColor;
              return val >= 0 ? (isDark ? "#e74c3c" : "#c0392b") : (isDark ? "#2ecc71" : "#27ae60");
            },
            tension: 0.3,
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false,
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: isDark ? "#1a1a18" : "#ffffff",
            titleColor: isDark ? "#e0dfdc" : "#1a1a18",
            bodyColor: isDark ? "#8a8985" : "#6b6a66",
            borderColor: isDark ? "#333330" : "#e0ddd8",
            borderWidth: 1,
            padding: 10,
            cornerRadius: 6,
            callbacks: {
              label: function (context) {
                const v = context.raw;
                return (v >= 0 ? "+" : "") + v.toFixed(1) + "% vs USD";
              },
            },
          },
        },
        scales: {
          x: {
            ticks: {
              color: textColor,
              font: { family: "'DM Mono', monospace", size: 10 },
              maxTicksLimit: 10,
              maxRotation: 0,
            },
            grid: { color: gridColor },
          },
          y: {
            ticks: {
              color: textColor,
              font: { family: "'DM Mono', monospace", size: 10 },
              callback: function (val) { return val + "%"; },
            },
            grid: {
              color: function (context) {
                return context.tick.value === 0 ? zeroColor : gridColor;
              },
              lineWidth: function (context) {
                return context.tick.value === 0 ? 2 : 1;
              },
            },
          },
        },
      },
    });
  }

  function updateTrendChartColors() {
    if (selectedCountryIso) {
      renderTrendChart(selectedCountryIso);
    }
  }

  /* ── Legend ── */
  function renderLegend() {
    const container = document.getElementById("legend-bar");
    container.innerHTML = "";

    const isDark = root.getAttribute("data-theme") === "dark";
    const neutral = isDark ? "#555550" : "#f5f0e0";
    const red = isDark ? "#e74c3c" : "#c0392b";
    const green = isDark ? "#2ecc71" : "#1e8449";

    const labelLeft = document.createElement("span");
    labelLeft.textContent = "-80%";
    container.appendChild(labelLeft);

    const underLabel = document.createElement("span");
    underLabel.textContent = "Undervalued";
    underLabel.style.fontWeight = "500";
    container.appendChild(underLabel);

    const canvas = document.createElement("canvas");
    canvas.width = 220;
    canvas.height = 12;
    const ctx = canvas.getContext("2d");

    /* Draw gradient: green → neutral → red */
    const grad = ctx.createLinearGradient(0, 0, 220, 0);
    grad.addColorStop(0, green);
    grad.addColorStop(0.5, neutral);
    grad.addColorStop(1, red);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 220, 12);
    container.appendChild(canvas);

    const overLabel = document.createElement("span");
    overLabel.textContent = "Overvalued";
    overLabel.style.fontWeight = "500";
    container.appendChild(overLabel);

    const labelRight = document.createElement("span");
    labelRight.textContent = "+80%";
    container.appendChild(labelRight);
  }

  /* ── Play animation ── */
  function togglePlay() {
    const btn = document.getElementById("play-btn");
    if (playing) {
      clearInterval(playTimer);
      playing = false;
      btn.classList.remove("playing");
    } else {
      if (currentDateIndex >= bmData.dates.length - 1) {
        currentDateIndex = 0;
      }
      playing = true;
      btn.classList.add("playing");
      playTimer = setInterval(function () {
        currentDateIndex++;
        if (currentDateIndex >= bmData.dates.length) {
          currentDateIndex = bmData.dates.length - 1;
          clearInterval(playTimer);
          playing = false;
          btn.classList.remove("playing");
        }
        update();
      }, 500);
    }
  }

  /* ── Helpers ── */
  function formatNum(n) {
    if (n === null || n === undefined) return "N/A";
    if (n >= 10000) return n.toLocaleString("en-US", { maximumFractionDigits: 0 });
    if (n >= 100) return n.toLocaleString("en-US", { maximumFractionDigits: 0 });
    return n.toLocaleString("en-US", { maximumFractionDigits: 2 });
  }

  /* ── Window resize ── */
  let resizeTimer;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      const container = document.getElementById("map-svg-wrap");
      container.innerHTML = "";
      renderMap();
      update();
    }, 300);
  });

  /* ── Start ── */
  init();
})();
