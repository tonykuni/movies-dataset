# VIA state and module schema

## Envelope

```json
{
  "version": 2,
  "updatedAt": "ISO-8601",
  "source": "SYNCHRONIZER|UI|REMOTE",
  "view": {},
  "modules": [],
  "analytics": {},
  "layout": {},
  "sync": {}
}
```

## Module

Required stable fields:

```json
{
  "id": "quality-center",
  "name": "品質中心",
  "type": "dashboard|data|automation|governance|integration",
  "enabled": true,
  "pinned": false,
  "order": 3,
  "system": false,
  "note": "良率與批次追蹤"
}
```

System modules should remain present when a template uses replace mode. Custom modules are the records with `system: false`.

## Analytics

```json
{
  "templateId": "smart-manufacturing",
  "templateName": "智慧製造",
  "charts": [
    {"id":"oee-trend","name":"OEE 趨勢","type":"line","metric":"oee","groupBy":"date","enabled":true}
  ],
  "history": [
    {"date":"2026-09-14","moduleId":"oee-monitor","metric":"oee","value":87.3,"category":"OEE"}
  ],
  "pivot": {"rowField":"date","columnField":"metric","valueField":"value","aggregation":"sum"}
}
```

CSV headers:

- Modules: `module_id,module_name,module_type,enabled,pinned,order,system,note`
- Charts: `chart_id,chart_name,chart_type,metric,group_by,enabled`
- History: `date,module_id,metric,value,category`

## Layout

```json
{"fontScale":0.94,"headerHeight":44,"panelHeight":292,"equalPanels":true,"surface":"light"}
```

Clamp user-entered layout values before applying CSS variables. The central UI bridge must preserve `analytics` and `layout` when normalizing incoming state; otherwise opening the UI can erase SYNCHRONIZER-specific fields.

## Excel sheets

The SpreadsheetML export should include `Template`, `Layout`, `SyncRules`, `View`, `Modules`, `Charts`, `History`, and `PivotSummary`. Keep XML escaping enabled for every cell.
