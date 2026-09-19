/* Generated VIA browser smoke test. Paste into DevTools on the target file:// page. */
(()=>{
  const manifest={
  "contract": "VIA_MODULE_VALIDATION/1.0",
  "industry": "investment-research",
  "profile_name": "investment-research",
  "html": "/home/ubuntu/VIA-SYNCHRONIZER-Standalone.html",
  "required_dom_ids": [
    "templateSelect",
    "templateMode",
    "applyTemplate",
    "exportTemplate",
    "addModule",
    "addChart",
    "applyPivot",
    "exportExcel",
    "exportExcel2",
    "jsonPreview",
    "loadState",
    "clearState"
  ],
  "required_tokens": [
    "localStorage",
    "BroadcastChannel",
    "SpreadsheetML",
    "PivotSummary",
    "modules",
    "charts",
    "history",
    "version"
  ],
  "required_labels": [
    "investment-research"
  ],
  "ir": {
    "contract": "VIA_SPEC_IR/1.0",
    "version": "0100",
    "min_items": 441,
    "min_ui_items": 152,
    "observed_ids": [
      "syncNow",
      "exportJson",
      "exportCsv",
      "exportHistory",
      "exportExcel",
      "importData",
      "source",
      "channelStatus",
      "lastSync",
      "version",
      "storageCheck",
      "channelCheck",
      "syncScope",
      "conflictRule",
      "debounceMs",
      "ruleSummary",
      "applyRules",
      "templateSelect",
      "templateMode",
      "applyTemplate",
      "exportTemplate",
      "templateSummary",
      "chartId",
      "chartName",
      "chartType",
      "chartMetric",
      "addChart",
      "templateName",
      "chartCount",
      "historyCount",
      "chartList",
      "pivotRow",
      "pivotColumn",
      "pivotValue",
      "pivotAgg",
      "applyPivot",
      "historySummary",
      "syncAddonSlot",
      "syncAddonSlotBody",
      "moduleCount",
      "moduleId",
      "moduleName",
      "moduleType",
      "modulePinned",
      "addModule",
      "moduleList",
      "density",
      "theme",
      "motion",
      "hints",
      "live",
      "autoApply",
      "applyView",
      "fontScale",
      "headerHeight",
      "panelHeight",
      "equalPanels",
      "surface",
      "exportJson2",
      "exportCsv2",
      "exportHistory2",
      "exportCharts",
      "exportExcel2",
      "jsonPreview",
      "loadState",
      "clearState",
      "log"
    ]
  }
}; const failures=[]; const q=s=>document.querySelector(s);
  const check=(ok,msg)=>{if(!ok) failures.push(msg)};
  manifest.required_dom_ids.forEach(id=>check(!!document.getElementById(id),`missing DOM id: ${id}`));
  manifest.required_labels.forEach(label=>check(document.body.innerText.includes(label),`missing label: ${label}`));
  const template=q('#templateSelect');
  if(template && [...template.options].some(o=>o.value===manifest.industry)){
    template.value=manifest.industry;
    q('#applyTemplate')?.click();
  }
  const state=JSON.parse(localStorage.getItem('via.sync.state.v2')||'null');
  check(!!state, 'missing v2 local state after template action');
  check(!!state?.analytics, 'missing analytics state');
  check(Array.isArray(state?.modules), 'missing modules array');
  check(Array.isArray(state?.analytics?.charts), 'missing charts array');
  const result={ok:!failures.length, failures, industry:manifest.industry, modules:state?.modules?.length||0, charts:state?.analytics?.charts?.length||0};
  console.log('VIA_MODULE_VALIDATION',result); return result;
})();
