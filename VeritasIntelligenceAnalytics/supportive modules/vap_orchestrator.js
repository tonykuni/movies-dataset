/* =============================================================================
def VeritasAutoPlot Central Orchestrator
def Policy: SSOT-driven · additive-only · global-state · cross-filter ready
============================================================================= */
(function () {
  "use strict";

  const VAP_STATE = {
    activePage: "map",
    selectedRegion: null,
    selectedAsset: null,
    selectedIndicator: null,
    globalTimeIndex: 0,
    data: null,
    errors: []
  };

  async function def_loadJson(url) {
    const resp = await fetch(url, { cache: "no-store" });
    if (!resp.ok) throw new Error("Load failed: " + url + " / " + resp.status);
    return await resp.json();
  }

  function def_log(level, message, extra) {
    const row = { time: new Date().toISOString(), level, message, extra: extra || null };
    if (level === "ERROR") VAP_STATE.errors.push(row);
    console.log("[VAP]", row);
  }

  function def_emit(name) {
    document.dispatchEvent(new CustomEvent(name, { detail: JSON.parse(JSON.stringify(VAP_STATE)) }));
  }

  function def_setGlobalTime(t) {
    VAP_STATE.globalTimeIndex = Number(t) || 0;

    if (window.VAP_MapSparkline?.setTimeIndex) window.VAP_MapSparkline.setTimeIndex(VAP_STATE.globalTimeIndex);
    if (window.VAP_Finance?.setTimeIndex) window.VAP_Finance.setTimeIndex(VAP_STATE.globalTimeIndex);
    if (window.VAP_Econ?.setTimeIndex) window.VAP_Econ.setTimeIndex(VAP_STATE.globalTimeIndex);

    def_emit("vap:time");
  }

  function def_setPage(page) {
    VAP_STATE.activePage = page;

    document.querySelectorAll("[data-vap-page]").forEach(x => {
      x.classList.toggle("active", x.dataset.vapPage === page);
    });

    document.querySelectorAll("[data-vap-tab]").forEach(x => {
      x.classList.toggle("active", x.dataset.vapTab === page);
    });

    def_emit("vap:page");
  }

  function def_setRegion(region) {
    VAP_STATE.selectedRegion = region;

    if (window.VAP_Finance?.filterByRegion) window.VAP_Finance.filterByRegion(region);
    if (window.VAP_Econ?.filterByRegion) window.VAP_Econ.filterByRegion(region);

    def_emit("vap:region");
  }

  function def_setAsset(asset) {
    VAP_STATE.selectedAsset = asset;

    if (window.VAP_MapSparkline?.highlightAsset) window.VAP_MapSparkline.highlightAsset(asset);

    def_emit("vap:asset");
  }

  async function def_init() {
    try {
      VAP_STATE.data = await def_loadJson("./unified_veritas_data.json");

      document.querySelectorAll("[data-vap-tab]").forEach(btn => {
        btn.addEventListener("click", () => def_setPage(btn.dataset.vapTab));
      });

      const slider = document.getElementById("vapGlobalTimeSlider");
      if (slider) slider.addEventListener("input", e => def_setGlobalTime(e.target.value));

      def_log("OK", "Orchestrator ready", VAP_STATE.data.meta || {});
      def_emit("vap:ready");
    } catch (err) {
      def_log("ERROR", err.message);
      def_emit("vap:error");
    }
  }

  window.VAP_Orchestrator = {
    init: def_init,
    setPage: def_setPage,
    setGlobalTime: def_setGlobalTime,
    setRegion: def_setRegion,
    setAsset: def_setAsset,
    getState: () => JSON.parse(JSON.stringify(VAP_STATE))
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", def_init);
  else def_init();
})();
