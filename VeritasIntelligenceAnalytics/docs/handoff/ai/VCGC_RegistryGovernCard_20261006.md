# VCGC 母系統 治理卡:表頭冊 + 功能矩陣(20261006)

> L114 ③:子系統登記留白 → 母系統顯示衝突 → 操作員+AI 裁 → 母系統測試通過發號 → 子系統讀回並遵守。紅 = 擋號;黃 = 提醒不擋。

## 貼回包
```
[計] vcgc registry govern --apply · 表 269(紅 0 黃 229 綠 40 發 0)· 功 20587(紅 0 黃 6677 綠 13879 發 0)· YELLOW
[計] 黃燈提醒分類 · F3=8199 · T5=147 · T6=198
  [YEL] 表 VCGC|via_activationgateway_v02_hotfix_manifest|77346f5e095960a6 · 同欄名異型(跨表):Time,Value | 非snake:Time;非snake:Round;非snake:Layer;非snake:Name;非snake:Status;非snake:Risk;非snake:Action;非snake:Metric;數字存字串:Value;非
  [YEL] 表 VCGC|via_activationgateway_v03_stablehotfix_manifest|77346f5e095960a6 · 同欄名異型(跨表):Time,Value | 非snake:Time;非snake:Round;非snake:Layer;非snake:Name;非snake:Status;非snake:Risk;非snake:Action;非snake:Metric;數字存字串:Value;非
  [YEL] 表 VCGC|via_activationgateway_v04_inlineready_manifest|77346f5e095960a6 · 同欄名異型(跨表):Time,Value | 非snake:Time;非snake:Round;非snake:Layer;非snake:Name;非snake:Status;非snake:Risk;非snake:Action;非snake:Metric;數字存字串:Value;非
  [YEL] 表 VCGC|via_activationgateway_v05_paramfirst_manifest|e429aebd45fffde1 · 同欄名異型(跨表):Time,Value | 非snake:Time;非snake:Round;非snake:Layer;非snake:Name;非snake:Status;非snake:Risk;非snake:FixClass;非snake:Metric;數字存字串:Value
  [YEL] 表 VCGC|via_canon_registry_entries|d753b3150d73a495 · 同欄名異型(跨表):group,ts | 格內巢狀:group;格內巢狀:yields;格內巢狀:mislabeled;格內巢狀:members;無主鍵候選
  [YEL] 表 VCGC|via_central_params_ssot_locked_alignment|cf200273cf177b97 · 格內巢狀:drift
  [YEL] 表 VCGC|via_central_params_ssot_books|1f34ff41fdab810a · 格內巢狀:top_keys
  [YEL] 表 VCGC|via_central_synonym_regex_regex|c657206549457a82 · 同欄名異型(跨表):rule,files | 格內巢狀:rule;格內巢狀:flags
NEXT: 零紅 → 子系統跑 table number pull / fn number pull 讀號;黃表留卡逐批裁
```

## 表(每鍵一列)
| 鍵 | 燈 | 號 | 測 | 旗 |
|---|---|---|---|---|
| VCGC|governanceregistry_language_adapters|e57046547d500202 | GREEN | SSOT-VCGC-VCGC-TBL0001 | — |  |
| VCGC|via_activationgateway_v02_hotfix_manifest|77346f5e095960a6 | YELLOW | SSOT-VCGC-VCGC-TBL0002 | — | T5 同欄名異型(跨表):Time,Value; T6 非snake:Time;非snake:Round;非snake:Layer;非snake:Name;非snake:Status;非snake:Risk;非snake:Action;非snake:Metric;數字存字串:Value;非snake:Value;非snake:Message;非snake:Path;非sna |
| VCGC|via_activationgateway_v03_stablehotfix_manifest|77346f5e095960a6 | YELLOW | SSOT-VCGC-VCGC-TBL0063 | — | T5 同欄名異型(跨表):Time,Value; T6 非snake:Time;非snake:Round;非snake:Layer;非snake:Name;非snake:Status;非snake:Risk;非snake:Action;非snake:Metric;數字存字串:Value;非snake:Value;非snake:Message;非snake:Path;非sna |
| VCGC|via_activationgateway_v04_inlineready_manifest|77346f5e095960a6 | YELLOW | SSOT-VCGC-VCGC-TBL0064 | — | T5 同欄名異型(跨表):Time,Value; T6 非snake:Time;非snake:Round;非snake:Layer;非snake:Name;非snake:Status;非snake:Risk;非snake:Action;非snake:Metric;數字存字串:Value;非snake:Value;非snake:Message;非snake:Path;非sna |
| VCGC|via_activationgateway_v05_paramfirst_manifest|e429aebd45fffde1 | YELLOW | SSOT-VCGC-VCGC-TBL0065 | — | T5 同欄名異型(跨表):Time,Value; T6 非snake:Time;非snake:Round;非snake:Layer;非snake:Name;非snake:Status;非snake:Risk;非snake:FixClass;非snake:Metric;數字存字串:Value;非snake:Value;非snake:Message;非snake:Path;非s |
| VCGC|via_canon_registry_entries|d753b3150d73a495 | YELLOW | SSOT-VCGC-VCGC-TBL0066 | — | T5 同欄名異型(跨表):group,ts; T6 格內巢狀:group;格內巢狀:yields;格內巢狀:mislabeled;格內巢狀:members;無主鍵候選 |
| VCGC|via_central_params_ssot_locked_alignment|cf200273cf177b97 | YELLOW | SSOT-VCGC-VCGC-TBL0003 | — | T6 格內巢狀:drift |
| VCGC|via_central_params_ssot_books|1f34ff41fdab810a | YELLOW | SSOT-VCGC-VCGC-TBL0004 | — | T6 格內巢狀:top_keys |
| VCGC|via_central_synonym_regex_regex|c657206549457a82 | YELLOW | SSOT-VCGC-VCGC-TBL0005 | — | T5 同欄名異型(跨表):rule,files; T6 格內巢狀:rule;格內巢狀:flags |
| VCGC|via_central_synonym_regex_rulings|711d8f78f27fd875 | YELLOW | SSOT-VCGC-VCGC-TBL0006 | — | T5 同欄名異型(跨表):rule; T6 格內巢狀:aliases |
| VCGC|via_central_synonym_regex_synonyms_meta|3aa6a298abee1c34 | YELLOW | SSOT-VCGC-VCGC-TBL0007 | — | T5 同欄名異型(跨表):source; T6 數字存字串:canonical |
| VCGC|via_dataframecontract_ssot_laws|d0355d728d8df946 | YELLOW | SSOT-VCGC-VCGC-TBL0008 | — | T5 同欄名異型(跨表):zh |
| VCGC|via_dataframe_lock_ledger|51f338f17fb8e61e | YELLOW | SSOT-VCGC-VCGC-TBL0009 | — | T5 同欄名異型(跨表):rows,keys; T6 格內巢狀:keys |
| VCGC|via_deprecatedgateway_ignoremanifest_deprecated_files|e020e52d91289135 | YELLOW | SSOT-VCGC-VCGC-TBL0010 | — | T6 非snake:Name;非snake:Path;非snake:Reason |
| VCGC|via_engineregistry_20260626_174457_dup|a506399437374a3d | YELLOW | SSOT-VCGC-VCGC-TBL0011 | — | T6 非snake:EngineID;非snake:FunctionName;非snake:EngineName;非snake:EngineType;非snake:Language;非snake:SourcePath;非snake:SourceSha256;非snake:Risk;非snake:Priority;非snake |
| VCGC|via_engineregistry|a506399437374a3d | YELLOW | SSOT-VCGC-VCGC-TBL0012 | — | T6 非snake:EngineID;非snake:FunctionName;非snake:EngineName;非snake:EngineType;非snake:Language;非snake:SourcePath;非snake:SourceSha256;非snake:Risk;非snake:Priority;非snake |
| VCGC|via_envregistry_items|a7e01a80090e2da4 | YELLOW | SSOT-VCGC-VCGC-TBL0013 | — | T5 同欄名異型(跨表):Exists; T6 非snake:Path;非snake:Name;非snake:Exists;非snake:Role;非snake:Kind;非snake:Ext;非snake:SizeKB;非snake:LastWriteTime;非snake:HasSSOT;非snake:HasRegex;非snake:HasSchema;非sna |
| VCGC|via_essentia_cardbook_cgc_cards|d7942522c0422595 | YELLOW | SSOT-VCGC-VCGC-TBL0014 | — | T6 數字存字串:version;格內巢狀:verbs;格內巢狀:flags;格內巢狀:contract;格內巢狀:owns;格內巢狀:tables;格內巢狀:deps |
| VCGC|via_essentia_cardbook_vdf_cards|d7942522c0422595 | YELLOW | SSOT-VCGC-VCGC-TBL0015 | — | T6 數字存字串:version;格內巢狀:verbs;格內巢狀:flags;格內巢狀:contract;格內巢狀:owns;格內巢狀:tables;格內巢狀:deps |
| VCGC|via_essentia_cardbook_vrn_cards|d7942522c0422595 | YELLOW | SSOT-VCGC-VCGC-TBL0016 | — | T6 數字存字串:version;格內巢狀:verbs;格內巢狀:flags;格內巢狀:contract;格內巢狀:owns;格內巢狀:tables;格內巢狀:deps |
| VCGC|via_essentia_product_ssot_verbs|2065070f1e0d2594 | GREEN | SSOT-VCGC-VCGC-TBL0017 | — |  |
| VCGC|via_lamplock_wkf|09a71903e699f512 | YELLOW | SSOT-VCGC-VCGC-TBL0019 | — | T5 同欄名異型(跨表):level; T6 格內巢狀:versions;格內巢狀:numbered;格內巢狀:registered |
| VCGC|via_lamplock_wkf_open|74228630944aac4a | YELLOW | SSOT-VCGC-VCGC-TBL0020 | — | T6 格內巢狀:open;格內巢狀:steps |
| VCGC|via_libregistry_items|a7e01a80090e2da4 | YELLOW | SSOT-VCGC-VCGC-TBL0021 | — | T5 同欄名異型(跨表):Exists; T6 非snake:Path;非snake:Name;非snake:Exists;非snake:Role;非snake:Kind;非snake:Ext;非snake:SizeKB;非snake:LastWriteTime;非snake:HasSSOT;非snake:HasRegex;非snake:HasSchema;非sna |
| VCGC|via_mastergovernance_ssot_subsystems|577e0545b098ec86 | YELLOW | SSOT-VCGC-VCGC-TBL0022 | — | T5 同欄名異型(跨表):zh; T6 格內巢狀:verbs;格內巢狀:stores;格內巢狀:ui_sections |
| VCGC|via_mastergovernance_ssot_v0100_local_subsystems|577e0545b098ec86 | YELLOW | SSOT-VCGC-VCGC-TBL0023 | — | T5 同欄名異型(跨表):zh; T6 格內巢狀:verbs;格內巢狀:stores;格內巢狀:ui_sections |
| VCGC|via_masterregistry_items|a7e01a80090e2da4 | YELLOW | SSOT-VCGC-VCGC-TBL0024 | — | T5 同欄名異型(跨表):Exists; T6 非snake:Path;非snake:Name;非snake:Exists;非snake:Role;非snake:Kind;非snake:Ext;非snake:SizeKB;非snake:LastWriteTime;非snake:HasSSOT;非snake:HasRegex;非snake:HasSchema;非sna |
| VCGC|via_netgate_wiring_register_engines|10771e2a82f84f6f | GREEN | SSOT-VCGC-VCGC-TBL0025 | — |  |
| VCGC|via_numbering_ssot_subsystems|93e31ef59ec8243b | YELLOW | SSOT-VCGC-VCGC-TBL0026 | — | T5 同欄名異型(跨表):zh |
| VCGC|via_numbering_ssot_kinds|2e19df41ca7a0f68 | YELLOW | SSOT-VCGC-VCGC-TBL0027 | — | T5 同欄名異型(跨表):zh |
| VCGC|via_numbering_ssot_books|6663fbc17e27e290 | YELLOW | SSOT-VCGC-VCGC-TBL0028 | — | T5 同欄名異型(跨表):n,files; T6 格內巢狀:compact;格內巢狀:inherit;格內巢狀:files |
| VCGC|via_output_header_ssot_candidates_tables|e4c1884b6018ab7d | YELLOW | SSOT-VCGC-VCGC-TBL0029 | — | T5 同欄名異型(跨表):source,keys,columns; T6 格內巢狀:keys;格內巢狀:columns;格內巢狀:issues |
| VCGC|via_output_header_ssot_tables|f1812a48a938fe5e | YELLOW | SSOT-VCGC-VCGC-TBL0030 | — | T5 同欄名異型(跨表):source,columns; T6 格內巢狀:source;格內巢狀:columns |
| VCGC|via_policy_dbpanel_ast_classes|18cda6f862a7c40d | GREEN | SSOT-VCGC-VCGC-TBL0031 | — |  |
| VCGC|via_policy_laws_ssot_lessons|2cde8156f5229ddf | YELLOW | SSOT-VCGC-VCGC-TBL0032 | — | T5 同欄名異型(跨表):zh |
| VCGC|via_productgate_gates|294166f335ae943c | GREEN | SSOT-VCGC-VCGC-TBL0033 | — |  |
| VCGC|via_productgate_projects|582bce7b0731edd7 | YELLOW | SSOT-VCGC-VCGC-TBL0034 | — | T5 同欄名異型(跨表):zh,n; T6 非snake:OK;非snake:CODE;非snake:DATA |
| VCGC|via_registry_architecture_ssot_layers|434d449c0aac6431 | GREEN | SSOT-VCGC-VCGC-TBL0035 | — |  |
| VCGC|via_registry_architecture_ssot_namespaces|faff4e403a7bb787 | YELLOW | SSOT-VCGC-VCGC-TBL0036 | — | T6 數字存字串:example |
| VCGC|via_registry_architecture_ssot_entity_primary|9ba3523d0d0bbfa4 | YELLOW | SSOT-VCGC-VCGC-TBL0037 | — | T6 格內巢狀:aliases |
| VCGC|via_registry_architecture_ssot_flow|c72bd0ef71d4b72d | GREEN | SSOT-VCGC-VCGC-TBL0038 | — |  |
| VCGC|via_registry_architecture_ssot_risks|c36402206b580edb | GREEN | SSOT-VCGC-VCGC-TBL0039 | — |  |
| VCGC|via_releaseregistry_items|a7e01a80090e2da4 | YELLOW | SSOT-VCGC-VCGC-TBL0040 | — | T5 同欄名異型(跨表):Exists; T6 非snake:Path;非snake:Name;非snake:Exists;非snake:Role;非snake:Kind;非snake:Ext;非snake:SizeKB;非snake:LastWriteTime;非snake:HasSSOT;非snake:HasRegex;非snake:HasSchema;非sna |
| VCGC|via_sourcelanelock|943029d1475ac5c3 | YELLOW | SSOT-VCGC-VCGC-TBL0041 | — | T5 同欄名異型(跨表):symbol,market; T6 數字存字串:code |
| VCGC|via_ssot_itemnumbers_items|20a9b64015388bbe | YELLOW | SSOT-VCGC-VCGC-TBL0042 | — | T5 同欄名異型(跨表):zh,source; T6 混型:value |
| VCGC|via_ssot_numbers_vrn_entries|21c42fa2ada96685 | GREEN | SSOT-VCGC-VCGC-TBL0043 | — |  |
| VCGC|via_ssot_periodrules_value_shapes|444e9be1b1e28b5c | YELLOW | SSOT-VCGC-VCGC-TBL0044 | — | T6 數字存字串:example |
| VCGC|via_ssot_periodrules_cadences|ab28fa33614eb2b6 | YELLOW | SSOT-VCGC-VCGC-TBL0045 | — | T6 格內巢狀:due |
| VCGC|via_ssot_periodrules_cadence_candidates|95dce8252156c74f | GREEN | SSOT-VCGC-VCGC-TBL0046 | — |  |
| VCGC|via_ssot_periodrules_ledger|3015eba72332b240 | YELLOW | SSOT-VCGC-VCGC-TBL0047 | — | T5 同欄名異型(跨表):ts,op |
| VCGC|via_ssot_regexdict_dropped_uncompilable|8d6eca6b89262dcc | GREEN | SSOT-VCGC-VCGC-TBL0048 | — |  |
| VCGC|via_ssot_regexdict_zone_stat|6b2c7a9dd5107082 | YELLOW | SSOT-VCGC-VCGC-TBL0049 | — | T5 同欄名異型(跨表):files,patterns |
| VCGC|via_ssot_regexdict_top_shared|4a127bb178243b76 | YELLOW | SSOT-VCGC-VCGC-TBL0050 | — | T5 同欄名異型(跨表):files; T6 格內巢狀:files |
| VCGC|via_ssot_regexdict_synonyms|989f86e22a14c443 | YELLOW | SSOT-VCGC-VCGC-TBL0051 | — | T5 同欄名異型(跨表):keys |
| VCGC|via_ssot_synonymunion_key_alias|40e8ff997f9dce99 | GREEN | SSOT-VCGC-VCGC-TBL0052 | — |  |
| VCGC|via_ssot_synonymunion_deny_leak|152e637df5ce6e18 | YELLOW | SSOT-VCGC-VCGC-TBL0067 | — | T6 無主鍵候選 |
| VCGC|via_ssot_synonymunion_gate_bypass|fd3aad6395ebf081 | GREEN | SSOT-VCGC-VCGC-TBL0053 | — |  |
| VCGC|via_ssot_synonymunion_rulings|2e2acd06aa8dbb6b | YELLOW | SSOT-VCGC-VCGC-TBL0068 | — | T5 同欄名異型(跨表):base,kept; T6 格內巢狀:base;格內巢狀:upload;格內巢狀:base_src;格內巢狀:demoted;格內巢狀:upload_said;格內巢狀:kept |
| VCGC|via_ssot_synonymunion_unverified|ec6795bcb6b6864e | GREEN | SSOT-VCGC-VCGC-TBL0054 | — |  |
| VCGC|via_statuslock_locked|354aabe9abf59f38 | YELLOW | SSOT-VCGC-VCGC-TBL0055 | — | T6 格內巢狀:lamps;格內巢狀:cycles |
| VCGC|via_toolregistry_items|a7e01a80090e2da4 | YELLOW | SSOT-VCGC-VCGC-TBL0056 | — | T5 同欄名異型(跨表):Exists; T6 非snake:Path;非snake:Name;非snake:Exists;非snake:Role;非snake:Kind;非snake:Ext;非snake:SizeKB;非snake:LastWriteTime;非snake:HasSSOT;非snake:HasRegex;非snake:HasSchema;非sna |
| VCGC|via_workflow_hub_ssot_sequence|752486b48a506f1b | GREEN | SSOT-VCGC-VCGC-TBL0057 | — |  |
| VCGC|via_workflow_ssot_workflows|6826d93fa9323d8a | YELLOW | SSOT-VCGC-VCGC-TBL0058 | — | T5 同欄名異型(跨表):zh,gate; T6 格內巢狀:nodes |
| VCGC|via_workflow_vap_ssot_workflows|a5cb283c4da232cb | YELLOW | SSOT-VCGC-VCGC-TBL0059 | — | T5 同欄名異型(跨表):spec; T6 格內巢狀:spec;格內巢狀:plan;格內巢狀:steps;格內巢狀:tests |
| VCGC|via_workflow_vcgc_ssot_workflows|a5cb283c4da232cb | YELLOW | SSOT-VCGC-VCGC-TBL0060 | — | T5 同欄名異型(跨表):spec; T6 格內巢狀:spec;格內巢狀:plan;格內巢狀:steps;格內巢狀:tests |
| VCGC|via_workflow_vdf_ssot_workflows|a5cb283c4da232cb | YELLOW | SSOT-VCGC-VCGC-TBL0061 | — | T5 同欄名異型(跨表):spec; T6 格內巢狀:spec;格內巢狀:plan;格內巢狀:steps;格內巢狀:tests |
| VCGC|via_workflow_vrn_ssot_workflows|a5cb283c4da232cb | YELLOW | SSOT-VCGC-VCGC-TBL0062 | — | T5 同欄名異型(跨表):spec; T6 格內巢狀:spec;格內巢狀:plan;格內巢狀:steps;格內巢狀:tests |
| VCGC|via_finalparameters_canonicalregistry_h2|fe6b440cb3fd6519 | YELLOW | SSOT-VCGC-VCGC-TBL0069 | — | T5 同欄名異型(跨表):def_occurrences,def_distinct_values,def_is_noise,def_score; T6 數字存字串:def_preferred_value;數字存字串:def_occurrences;數字存字串:def_distinct_values;數字存字串:def_score |
| VDF|taiwanstockgroup_sources|85edc9756ecc9afd | YELLOW | SSOT-VCGC-VDF-TBL0001 | — | T5 同欄名異型(跨表):rows |
| VDF|taiwanstockgroup_categories|5ff7b05ceab8ba82 | YELLOW | SSOT-VCGC-VDF-TBL0002 | — | T6 格內巢狀:subcategories |
| VDF|taiwanstockgroup_themes|6e01554e387b87cc | YELLOW | SSOT-VCGC-VDF-TBL0003 | — | T6 格內巢狀:mentioned |
| VDF|taiwanstockgroup_tickers|0729aa3e67ef8fa3 | YELLOW | SSOT-VCGC-VDF-TBL0004 | — | T6 格內巢狀:groups |
| VDF|vdf_adjprice_rule_ssot_rules|7b5d3381528924f7 | YELLOW | SSOT-VCGC-VDF-TBL0006 | — | T5 同欄名異型(跨表):zh; T6 格內巢狀:raw_columns;格內巢狀:factor_row;格內巢狀:adj_columns;格內巢狀:markets;格內巢狀:second_source_sample |
| VDF|vdf_akshareselection_macroshipping_overrides|7d95887e1b55f998 | YELLOW | SSOT-VCGC-VDF-TBL0007 | — | T5 同欄名異型(跨表):symbol; T6 格內巢狀:symbol;格內巢狀:__rows__ |
| VDF|vdf_fetchgroups_ssot_groups|f859275ff106a3d3 | YELLOW | SSOT-VCGC-VDF-TBL0008 | — | T5 同欄名異型(跨表):zh,en,exclude; T6 格內巢狀:engines;格內巢狀:sources;格內巢狀:refill;格內巢狀:asof_args;格內巢狀:default_members;格內巢狀:member_args;格內巢狀:start_args |
| VDF|vdf_fetchgroups_ssot_categories|2174a9a3c581ef61 | YELLOW | SSOT-VCGC-VDF-TBL0009 | — | T5 同欄名異型(跨表):zh; T6 格內巢狀:groups |
| VDF|vdf_fetchone_matrix_registry_items|1af879c7fa546c47 | YELLOW | SSOT-VCGC-VDF-TBL0010 | — | T5 同欄名異型(跨表):source,freq,fields; T6 數字存字串:refs |
| VDF|vdf_fetchsystem_ssot_engines|57ce184009f0c57c | YELLOW | SSOT-VCGC-VDF-TBL0011 | — | T5 同欄名異型(跨表):group; T6 數字存字串:id;格內巢狀:needs;格內巢狀:run_args;格內巢狀:fetch_functions;格內巢狀:outputs;格內巢狀:group_also;格內巢狀:test_args;格內巢狀:requires;格內巢狀:env;格內巢狀:nodata_markers;格內巢狀:tables |
| VDF|vdf_fetch_orders_orders|75084499b21feb8d | YELLOW | SSOT-VCGC-VDF-TBL0012 | — | T5 同欄名異型(跨表):ts,source; T6 數字存字串:order_id;格內巢狀:lanes;格內巢狀:runs;格內巢狀:storage_decision;格內巢狀:outputs |
| VDF|vdf_inputuniverse_ssot_inputs|62a888429aa03c61 | YELLOW | SSOT-VCGC-VDF-TBL0013 | — | T5 同欄名異型(跨表):group,zh,market,exclude,rule; T6 格內巢狀:market;格內巢狀:reader;格內巢狀:floor;格內巢狀:engines;格內巢狀:require;格內巢狀:exclude;格內巢狀:members |
| VDF|vdf_inputuniverse_ssot_outputs|73d3b1a976ca45cd | YELLOW | SSOT-VCGC-VDF-TBL0014 | — | T5 同欄名異型(跨表):zh,columns,keys,required; T6 混型:header_row;格內巢狀:columns;格內巢狀:engines;格內巢狀:keys;格內巢狀:required;格內巢狀:store_v0101;格內巢狀:for;格內巢狀:columns_ref;格內巢狀:source_tables;格內巢狀:zh_for_ref;格內巢狀:extra_columns |
| VDF|vdf_inputuniverse_ssot_engines|b67c514351c237d8 | YELLOW | SSOT-VCGC-VDF-TBL0015 | — | T5 同欄名異型(跨表):zh; T6 格內巢狀:writes;格內巢狀:candidate;格內巢狀:verbs_v0101;格內巢狀:writes_v0101 |
| VDF|vdf_inputuniverse_ssot_sources|1b4b7498dd5b891c | YELLOW | SSOT-VCGC-VDF-TBL0016 | — | T5 同欄名異型(跨表):zh |
| VDF|vdf_inputuniverse_ssot_terms|af851a9dc4483734 | YELLOW | SSOT-VCGC-VDF-TBL0017 | — | T5 同欄名異型(跨表):zh |
| VDF|vdf_input_interface_matrix_sections|9e3b855ac135fbba | YELLOW | SSOT-VCGC-VDF-TBL0018 | — | T6 格內巢狀:editable;格內巢狀:items;格內巢狀:removed_items;格內巢狀:tickers;格內巢狀:removed_tickers;格內巢狀:period_modes;格內巢狀:input_focus;格內巢狀:removed_focus;格內巢狀:modes;格內巢狀:removed_mode |
| VDF|vdf_input_interface_matrix_changelog|5607445de5ba51de | YELLOW | SSOT-VCGC-VDF-TBL0019 | — | T5 同欄名異型(跨表):ts,op |
| VDF|vdf_mdl401_registryschema_properties|9719de6521f6b97e | YELLOW | SSOT-VCGC-VDF-TBL0020 | — | T5 同欄名異型(跨表):required; T6 格內巢狀:required;非snake:additionalProperties;格內巢狀:properties;非snake:minItems;格內巢狀:items |
| VDF|vdf_mdl401_registryschema_definitions|2ab564306ab25fe0 | YELLOW | SSOT-VCGC-VDF-TBL0021 | — | T5 同欄名異型(跨表):required; T6 格內巢狀:required;非snake:additionalProperties;格內巢狀:properties |
| VDF|vdf_mdl402_registrysample_items|aa7cc62da70fddf9 | YELLOW | SSOT-VCGC-VDF-TBL0022 | — | T5 同欄名異型(跨表):freq; T6 格內巢狀:tags;格內巢狀:sources;格內巢狀:validation;格內巢狀:downstream_modules |
| VDF|vdf_mdl403_registryfull_items|e3938eb800b58e97 | YELLOW | SSOT-VCGC-VDF-TBL0023 | — | T5 同欄名異型(跨表):freq; T6 格內巢狀:sources;格內巢狀:validation;格內巢狀:downstream_modules;格內巢狀:tags |
| VDF|vdf_param_engine_map_by_engine|33749fa8142c80dd | YELLOW | SSOT-VCGC-VDF-TBL0024 | — | T6 格內巢狀:cli;格內巢狀:consts |
| VDF|vdf_param_engine_map_by_param|2b3987b418d3610d | YELLOW | SSOT-VCGC-VDF-TBL0025 | — | T6 格內巢狀:engines;格內巢狀:values;格內巢狀:governance |
| VDF|vdf_param_registry_params|de265717569b6490 | YELLOW | SSOT-VCGC-VDF-TBL0074 | — | T6 數字存字串:value;無主鍵候選 |
| VDF|vdf_param_registry_canonical|b891deb0ec3579ef | YELLOW | SSOT-VCGC-VDF-TBL0026 | — | T6 數字存字串:ruling;格內巢狀:variants |
| VDF|vdf_subsystem_manifest_artifacts|f214675308fa44d0 | GREEN | SSOT-VCGC-VDF-TBL0027 | — |  |
| VDF|vdf_ta_engine_spec_universe|1b564dbec3172d69 | YELLOW | SSOT-VCGC-VDF-TBL0028 | — | T5 同欄名異型(跨表):zh |
| VDF|vdf_ta_engine_spec_changelog|5607445de5ba51de | YELLOW | SSOT-VCGC-VDF-TBL0029 | — | T5 同欄名異型(跨表):ts,op |
| VDF|vdf_twequity_dailyrow_schema_columns|cb328599b2958307 | YELLOW | SSOT-VCGC-VDF-TBL0030 | — | T5 同欄名異型(跨表):zh,source,required |
| VDF|vdf_twequity_dailyrow_schema_changelog|5607445de5ba51de | YELLOW | SSOT-VCGC-VDF-TBL0031 | — | T5 同欄名異型(跨表):ts,op |
| VDF|vdf_tw_focus_universe_members|197429d4b3f52d6d | YELLOW | SSOT-VCGC-VDF-TBL0075 | — | T5 同欄名異型(跨表):market,group; T6 數字存字串:ticker;無主鍵候選 |
| VDF|vdf_usmacro_agencies_agencies|bca818322e1de506 | YELLOW | SSOT-VCGC-VDF-TBL0032 | — | T5 同欄名異型(跨表):zh,rows; T6 格內巢狀:rows |
| VDF|vdf_usmacro_coverage_map_assets_measured|21d2866e448a5b5c | YELLOW | SSOT-VCGC-VDF-TBL0033 | — | T5 同欄名異型(跨表):columns,rows; T6 格內巢狀:column_list;格內巢狀:series |
| VDF|vdf_usmacro_detail_fetch_roster_changelog|5607445de5ba51de | YELLOW | SSOT-VCGC-VDF-TBL0034 | — | T5 同欄名異型(跨表):ts,op |
| VDF|vdf_usmacro_fedmore_add|264a97e90486aeb8 | YELLOW | SSOT-VCGC-VDF-TBL0035 | — | T5 同欄名異型(跨表):zh; T6 數字存字串:value |
| VDF|vdf_usmacro_fedmore_stale|9e5a9c8e2f70b221 | YELLOW | SSOT-VCGC-VDF-TBL0036 | — | T5 同欄名異型(跨表):zh |
| VDF|vdf_usmacro_gap_verified|e01697ba8a6c1681 | YELLOW | SSOT-VCGC-VDF-TBL0037 | — | T6 數字存字串:value |
| VDF|vdf_usmacro_gap_anchors|e01697ba8a6c1681 | YELLOW | SSOT-VCGC-VDF-TBL0038 | — | T6 數字存字串:value |
| VDF|vdf_usmacro_probe|bd36758a4aa1cd5c | YELLOW | SSOT-VCGC-VDF-TBL0039 | — | T6 數字存字串:value |
| VDF|vdf_usmacro_tree_families|1dbfecb120675d05 | YELLOW | SSOT-VCGC-VDF-TBL0040 | — | T5 同欄名異型(跨表):zh,rejected,rule; T6 格內巢狀:kinds;格內巢狀:parent_codes;格內巢狀:finer_on_file;格內巢狀:synonyms;格內巢狀:add;格內巢狀:declared;格內巢狀:rejected;格內巢狀:yfinance_cross |
| VDF|vrn_mdl010_vrn_basicfinancial_confidence_method_review__financialdata__v0_0_canonicalevidence|63a29a53c597f0c6 | YELLOW | SSOT-VCGC-VDF-TBL0041 | — | T5 同欄名異型(跨表):Exists; T6 非snake:Key;非snake:Type;非snake:Path;非snake:RelPath;非snake:Exists;非snake:ExpectedRows;非snake:ActualRows;非snake:ColumnCount;非snake:ColumnsSample;非snake:SHA256;非sna |
| VDF|vrn_mdl010_vrn_basicfinancial_confidence_method_review__financialdata__v0_0_confidencedimensions|4a53db7e7b27a0c0 | YELLOW | SSOT-VCGC-VDF-TBL0042 | — | T6 非snake:Area;非snake:Dimension;非snake:Weight;非snake:RequiredSignals;非snake:HitSignals;非snake:CoveragePct;非snake:Score;非snake:Status;非snake:Risk;非snake:Recommendat |
| VDF|vrn_mdl010_vrn_basicfinancial_confidence_method_review__financialdata__v0_0_methodregistry|826573718e30e162 | YELLOW | SSOT-VCGC-VDF-TBL0043 | — | T6 非snake:MethodClass;非snake:Topic;非snake:Zone;非snake:RelPath;非snake:FullPath;非snake:Name;非snake:Ext;非snake:Modified;非snake:Signals;非snake:Risk;非snake:Note |
| VDF|vrn_mdl010_vrn_basicfinancial_confidence_method_review__financialdata__v0_0_actionqueue|41086084d3f878ea | YELLOW | SSOT-VCGC-VDF-TBL0044 | — | T5 同欄名異型(跨表):Mutation; T6 非snake:Order;非snake:Priority;非snake:Area;非snake:Issue;非snake:CurrentStatus;非snake:FixType;非snake:Recommendation;非snake:Mutation;非snake:DbWrite;非snake:Network |
| VDF|vrn_mdl010_vrn_basicfinancial_confidence_method_review__financialdata__v0_0_inventory|f4c7943d7bbe6c9e | YELLOW | SSOT-VCGC-VDF-TBL0045 | — | T6 非snake:RelPath;非snake:FullPath;非snake:Name;非snake:Ext;非snake:Modified;非snake:SizeKB;非snake:Zone;非snake:Topic |
| VDF|vrn_mdl011_vrn_basicfinancial_confidence_method_review__financialdata__v0_0_canonicalevidence|63a29a53c597f0c6 | YELLOW | SSOT-VCGC-VDF-TBL0046 | — | T5 同欄名異型(跨表):Exists; T6 非snake:Key;非snake:Type;非snake:Path;非snake:RelPath;非snake:Exists;非snake:ExpectedRows;非snake:ActualRows;非snake:ColumnCount;非snake:ColumnsSample;非snake:SHA256;非sna |
| VDF|vrn_mdl011_vrn_basicfinancial_confidence_method_review__financialdata__v0_0_confidencedimensions|4a53db7e7b27a0c0 | YELLOW | SSOT-VCGC-VDF-TBL0047 | — | T6 非snake:Area;非snake:Dimension;非snake:Weight;非snake:RequiredSignals;非snake:HitSignals;非snake:CoveragePct;非snake:Score;非snake:Status;非snake:Risk;非snake:Recommendat |
| VDF|vrn_mdl011_vrn_basicfinancial_confidence_method_review__financialdata__v0_0_methodregistry|826573718e30e162 | YELLOW | SSOT-VCGC-VDF-TBL0048 | — | T6 非snake:MethodClass;非snake:Topic;非snake:Zone;非snake:RelPath;非snake:FullPath;非snake:Name;非snake:Ext;非snake:Modified;非snake:Signals;非snake:Risk;非snake:Note |
| VDF|vrn_mdl011_vrn_basicfinancial_confidence_method_review__financialdata__v0_0_actionqueue|41086084d3f878ea | YELLOW | SSOT-VCGC-VDF-TBL0049 | — | T5 同欄名異型(跨表):Mutation; T6 非snake:Order;非snake:Priority;非snake:Area;非snake:Issue;非snake:CurrentStatus;非snake:FixType;非snake:Recommendation;非snake:Mutation;非snake:DbWrite;非snake:Network |
| VDF|vrn_mdl011_vrn_basicfinancial_confidence_method_review__financialdata__v0_0_inventory|f4c7943d7bbe6c9e | YELLOW | SSOT-VCGC-VDF-TBL0050 | — | T6 非snake:RelPath;非snake:FullPath;非snake:Name;非snake:Ext;非snake:Modified;非snake:SizeKB;非snake:Zone;非snake:Topic |
| VDF|vrn_mdl012_vrn_basicfinancial_confidence_method_review__financialdata__v0_0_canonicalevidence|63a29a53c597f0c6 | YELLOW | SSOT-VCGC-VDF-TBL0051 | — | T5 同欄名異型(跨表):Exists; T6 非snake:Key;非snake:Type;非snake:Path;非snake:RelPath;非snake:Exists;非snake:ExpectedRows;非snake:ActualRows;非snake:ColumnCount;非snake:ColumnsSample;非snake:SHA256;非sna |
| VDF|vrn_mdl012_vrn_basicfinancial_confidence_method_review__financialdata__v0_0_confidencedimensions|4a53db7e7b27a0c0 | YELLOW | SSOT-VCGC-VDF-TBL0052 | — | T6 非snake:Area;非snake:Dimension;非snake:Weight;非snake:RequiredSignals;非snake:HitSignals;非snake:CoveragePct;非snake:Score;非snake:Status;非snake:Risk;非snake:Recommendat |
| VDF|vrn_mdl012_vrn_basicfinancial_confidence_method_review__financialdata__v0_0_methodregistry|826573718e30e162 | YELLOW | SSOT-VCGC-VDF-TBL0053 | — | T6 非snake:MethodClass;非snake:Topic;非snake:Zone;非snake:RelPath;非snake:FullPath;非snake:Name;非snake:Ext;非snake:Modified;非snake:Signals;非snake:Risk;非snake:Note |
| VDF|vrn_mdl012_vrn_basicfinancial_confidence_method_review__financialdata__v0_0_actionqueue|41086084d3f878ea | YELLOW | SSOT-VCGC-VDF-TBL0054 | — | T5 同欄名異型(跨表):Mutation; T6 非snake:Order;非snake:Priority;非snake:Area;非snake:Issue;非snake:CurrentStatus;非snake:FixType;非snake:Recommendation;非snake:Mutation;非snake:DbWrite;非snake:Network |
| VDF|vrn_mdl012_vrn_basicfinancial_confidence_method_review__financialdata__v0_0_inventory|f4c7943d7bbe6c9e | YELLOW | SSOT-VCGC-VDF-TBL0055 | — | T6 非snake:RelPath;非snake:FullPath;非snake:Name;非snake:Ext;非snake:Modified;非snake:SizeKB;非snake:Zone;非snake:Topic |
| VDF|vrn_mdl272_vrn_v140k_basicinfo_financialdata_sidecar_sync_basicinfo_matrix|b9d443a131294d25 | YELLOW | SSOT-VCGC-VDF-TBL0056 | — | T5 同欄名異型(跨表):Time,Page,Value; T6 非snake:Time;非snake:Page;非snake:Gate;數字存字串:Value;非snake:Value;非snake:Status;非snake:Severity;非snake:Message |
| VDF|vrn_mdl272_vrn_v140k_basicinfo_financialdata_sidecar_sync_basicinfo_validation|8d62e0f5a8c56ca2 | YELLOW | SSOT-VCGC-VDF-TBL0057 | — | T5 同欄名異型(跨表):Value,Expected; T6 非snake:Check;混型:Value;非snake:Value;混型:Expected;非snake:Expected;非snake:Pass |
| VDF|vrn_mdl272_vrn_v140k_basicinfo_financialdata_sidecar_sync_basicinfo_table_scan|595595fda2edfb5d | GREEN | SSOT-VCGC-VDF-TBL0058 | — |  |
| VDF|vrn_mdl272_vrn_v140k_basicinfo_financialdata_sidecar_sync_basicinfo_pointers_written|82e4342439d62e52 | GREEN | SSOT-VCGC-VDF-TBL0059 | — |  |
| VDF|vrn_mdl272_vrn_v140k_basicinfo_financialdata_sidecar_sync_basicinfo_written_pointer_objects|4ae0ee327c44931e | YELLOW | SSOT-VCGC-VDF-TBL0060 | — | T6 格內巢狀:schema_first_12;格內巢狀:usage_policy;格內巢狀:recommended_consumers |
| VDF|vrn_mdl272_vrn_v140k_basicinfo_financialdata_sidecar_sync__basicinfo__matrix|b9d443a131294d25 | YELLOW | SSOT-VCGC-VDF-TBL0061 | — | T5 同欄名異型(跨表):Time,Page,Value; T6 非snake:Time;非snake:Page;非snake:Gate;數字存字串:Value;非snake:Value;非snake:Status;非snake:Severity;非snake:Message |
| VDF|vrn_mdl272_vrn_v140k_basicinfo_financialdata_sidecar_sync__basicinfo__validation|8d62e0f5a8c56ca2 | YELLOW | SSOT-VCGC-VDF-TBL0062 | — | T5 同欄名異型(跨表):Value,Expected; T6 非snake:Check;混型:Value;非snake:Value;混型:Expected;非snake:Expected;非snake:Pass |
| VDF|vrn_mdl272_vrn_v140k_basicinfo_financialdata_sidecar_sync__basicinfo__table_scan|595595fda2edfb5d | GREEN | SSOT-VCGC-VDF-TBL0063 | — |  |
| VDF|vrn_mdl272_vrn_v140k_basicinfo_financialdata_sidecar_sync__basicinfo__pointers_written|82e4342439d62e52 | GREEN | SSOT-VCGC-VDF-TBL0064 | — |  |
| VDF|vrn_mdl272_vrn_v140k_basicinfo_financialdata_sidecar_sync__basicinfo__written_pointer_objects|4ae0ee327c44931e | YELLOW | SSOT-VCGC-VDF-TBL0065 | — | T6 格內巢狀:schema_first_12;格內巢狀:usage_policy;格內巢狀:recommended_consumers |
| VDF|vdf_mdl401_registryschema_v1_properties|9719de6521f6b97e | YELLOW | SSOT-VCGC-VDF-TBL0066 | — | T5 同欄名異型(跨表):required; T6 格內巢狀:required;非snake:additionalProperties;格內巢狀:properties;非snake:minItems;格內巢狀:items |
| VDF|vdf_mdl401_registryschema_v1_definitions|2ab564306ab25fe0 | YELLOW | SSOT-VCGC-VDF-TBL0067 | — | T5 同欄名異型(跨表):required; T6 格內巢狀:required;非snake:additionalProperties;格內巢狀:properties |
| VDF|via_extraction_matrix_v8|93d5c1cd126053ca | YELLOW | SSOT-VCGC-VDF-TBL0068 | — | T6 數字存字串:#;非snake:#;非snake:大項目;非snake:小項目;非snake:標的/代碼;非snake:主要來源;非snake:頻率;非snake:多來源並存;非snake:證據層;非snake:用途;非snake:QA |
| VDF|via_vdf_fetch_contract_domains|45657c8065489a19 | YELLOW | SSOT-VCGC-VDF-TBL0069 | — | T6 格內巢狀:items |
| VDF|via_vdf_fetch_contract_revisions|d6e1650ff3f6e8a5 | GREEN | SSOT-VCGC-VDF-TBL0070 | — |  |
| VDF|vdf_2_enginecapability_h2|d71b3cb7967e7dc0 | YELLOW | SSOT-VCGC-VDF-TBL0071 | — | T5 同欄名異型(跨表):found |
| VDF|vdf_dormant_ledger|ccf0a8d239804a96 | YELLOW | SSOT-VCGC-VDF-TBL0076 | — | T5 同欄名異型(跨表):base,ts |
| VDF|vdf_functionmatrix_items_h2|c1849daf33afd0b6 | YELLOW | SSOT-VCGC-VDF-TBL0077 | — | T5 同欄名異型(跨表):source; T6 數字存字串:body_sha;格內巢狀:issues;格內巢狀:similar;格內巢狀:history |
| VDF|stockreportfinancialdata_h2|929567135d8551a1 | YELLOW | SSOT-VCGC-VDF-TBL0078 | — | T5 同欄名異型(跨表):Page,TableIndex,RowIndex,ColumnIndex,PeriodOk; T6 非snake:SourceFile;數字存字串:Ticker;非snake:Ticker;非snake:Broker;非snake:ReportDate;數字存字串:Page;非snake:Page;數字存字串:TableIndex;非snake:TableIndex;數字存字串:RowIndex;非snake:Row |
| VRN|vrn_audit_evidence_findings|339959b67747763a | GREEN | SSOT-VCGC-VRN-TBL0001 | — |  |
| VRN|vrn_audit_evidence_verified_sources|5f52aae043a46f06 | GREEN | SSOT-VCGC-VRN-TBL0002 | — |  |
| VRN|vrn_chainnodeledger_timeouts|d8a197c628f04d53 | GREEN | SSOT-VCGC-VRN-TBL0003 | — |  |
| VRN|vrn_docclass_ssot_classes|fe5b38cd43cb4b05 | YELLOW | SSOT-VCGC-VRN-TBL0004 | — | T5 同欄名異型(跨表):zh |
| VRN|vrn_docclass_ssot_rules|4c5514bdd4e7b282 | YELLOW | SSOT-VCGC-VRN-TBL0005 | — | T5 同欄名異型(跨表):base; T6 格內巢狀:when |
| VRN|vrn_essentia_cardbook_vrn_cards|d7942522c0422595 | YELLOW | SSOT-VCGC-VRN-TBL0006 | — | T6 數字存字串:version;格內巢狀:verbs;格內巢狀:flags;格內巢狀:contract;格內巢狀:owns;格內巢狀:tables;格內巢狀:deps |
| VRN|vrn_extractionlogic_ssot_ladder|cdf6a8ac5a58d484 | YELLOW | SSOT-VCGC-VRN-TBL0007 | — | T6 格內巢狀:adapters |
| VRN|vrn_fieldspec_ssot_fields|1051bc4b4a13aeff | YELLOW | SSOT-VCGC-VRN-TBL0008 | — | T5 同欄名異型(跨表):zh,spec,source,rule |
| VRN|vrn_fileregistry_stage|47646e60e5f305ba | YELLOW | SSOT-VCGC-VRN-TBL0009 | — | T6 數字存字串:file_size;數字存字串:page_count;數字存字串:pages_extracted;數字存字串:text_chars;數字存字串:elapsed_sec |
| VRN|vrn_incremental_db_result_files|327cfb7dfdaccd23 | YELLOW | SSOT-VCGC-VRN-TBL0010 | — | T6 數字存字串:ticker |
| VRN|vrn_logicarchitecture_ssot_layers|4bb85f457286454b | YELLOW | SSOT-VCGC-VRN-TBL0011 | — | T6 格內巢狀:nodes |
| VRN|vrn_logicarchitecture_ssot_placed_by_batch662|8ef2734fb320bc72 | GREEN | SSOT-VCGC-VRN-TBL0012 | — |  |
| VRN|vrn_logicarchitecture_ssot_off_book_pending|c009f67d88902348 | GREEN | SSOT-VCGC-VRN-TBL0013 | — |  |
| VRN|vrn_logicarchitecture_ssot_rule_canons|5b899a645c00f7d1 | YELLOW | SSOT-VCGC-VRN-TBL0014 | — | T5 同欄名異型(跨表):exists |
| VRN|vrn_logicarchitecture_ssot_rulings_today|cd767159fbd87265 | YELLOW | SSOT-VCGC-VRN-TBL0015 | — | T6 格內巢狀:landed_in |
| VRN|vrn_logicarchitecture_ssot_known_gaps|48c81a3db2ae6ea2 | GREEN | SSOT-VCGC-VRN-TBL0016 | — |  |
| VRN|vrn_mdl024_vrn_v139o_appendonly_bridge_injector_matrix__module__matrix|b9d443a131294d25 | YELLOW | SSOT-VCGC-VRN-TBL0017 | — | T5 同欄名異型(跨表):Time,Page,Value; T6 非snake:Time;非snake:Page;非snake:Gate;數字存字串:Value;非snake:Value;非snake:Status;非snake:Severity;非snake:Message |
| VRN|vrn_mdl024_vrn_v139o_appendonly_bridge_injector_matrix__module__patched|cd1afbafed694bb1 | YELLOW | SSOT-VCGC-VRN-TBL0018 | — | T6 非snake:Path;非snake:FileType;非snake:Risk;非snake:Status;非snake:Severity;非snake:Backup;非snake:ShaBefore;非snake:ShaAfter;非snake:RolledBack;非snake:Message |
| VRN|vrn_mdl033_vrn_hydra_containment_registry__support_rule__v0_0_canonicalvalidation|bdeb5f4c34b7d8a0 | YELLOW | SSOT-VCGC-VRN-TBL0019 | — | T5 同欄名異型(跨表):Exists; T6 非snake:Key;非snake:Type;非snake:FullPath;非snake:RelPath;非snake:Exists;非snake:ExpectedRows;非snake:ActualRows;非snake:SHA256;非snake:Status;非snake:Risk;非snake:Note |
| VRN|vrn_mdl033_vrn_hydra_containment_registry__support_rule__v0_0_reclassifiederrors|b2b5a9220ed4a488 | YELLOW | SSOT-VCGC-VRN-TBL0020 | — | T6 非snake:OriginalRisk;非snake:Category;非snake:RelPath;非snake:FullPath;非snake:Evidence;非snake:RootCause;非snake:ReclassifiedAs;非snake:IsTrueBlocker;非snake:SealDecisi |
| VRN|vrn_mdl033_vrn_hydra_containment_registry__support_rule__v0_0_evidenceonlydenylist|ebe2d466e9ce7179 | YELLOW | SSOT-VCGC-VRN-TBL0021 | — | T6 非snake:Policy;非snake:Reason;非snake:RelPath;非snake:FullPath;非snake:Category;非snake:Risk;非snake:AllowedAsMaster;非snake:AllowedAsEvidence;非snake:AllowedToRead;非sna |
| VRN|vrn_mdl069_vrn_canonical_active_manifest__module__v0_0_evidence|535227ae76eb25ff | YELLOW | SSOT-VCGC-VRN-TBL0022 | — | T5 同欄名異型(跨表):Exists; T6 非snake:Light;非snake:Confidence;非snake:Key;非snake:Type;非snake:Exists;非snake:ExpectedRows;非snake:ActualRows;非snake:Status;非snake:Risk;非snake:Note;非snake:Path;非sna |
| VRN|vrn_mdl089_vrn_v141d8a2_safegetter_sourcemanifestextractor__module__summary|7eb5592307ae3775 | YELLOW | SSOT-VCGC-VRN-TBL0023 | — | T5 同欄名異型(跨表):Time,Value,Expected; T6 非snake:Validation Status;非snake:Time;非snake:Category;非snake:Item;數字存字串:Value;非snake:Value;數字存字串:Expected;非snake:Expected;非snake:Pass;非snake:Severity;非snake:Vali |
| VRN|vrn_mdl089_vrn_v141d8a2_safegetter_sourcemanifestextractor__module__previous_d8a_diagnosis|f7cc6f27f7adbfa9 | YELLOW | SSOT-VCGC-VRN-TBL0024 | — | T5 同欄名異型(跨表):Exists,Value; T6 非snake:Validation Status;非snake:Item;非snake:Path;非snake:Exists;非snake:Value;非snake:Validation Note |
| VRN|vrn_mdl089_vrn_v141d8a2_safegetter_sourcemanifestextractor__module__source_manifest_validated|42e438e35c2f08b9 | YELLOW | SSOT-VCGC-VRN-TBL0025 | — | T5 同欄名異型(跨表):Exists; T6 非snake:Validation Status;非snake:Source ID;非snake:Filename;非snake:Path;非snake:Extension;非snake:Exists;非snake:Allowed For D8;數字存字串:Parsed Ticker;非snake:Parsed Tic |
| VRN|vrn_mdl089_vrn_v141d8a2_safegetter_sourcemanifestextractor__module__text_anchor_evidence|1fdb6743cc0cf479 | YELLOW | SSOT-VCGC-VRN-TBL0026 | — | T6 非snake:Validation Status;非snake:Source ID;非snake:Filename;非snake:Path;非snake:Extract Method;非snake:Text Chars;數字存字串:Ticker From Filename;非snake:Ticker From File |
| VRN|vrn_mdl089_vrn_v141d8a2_safegetter_sourcemanifestextractor__module__basic_info_candidates|a20e3a430e891f34 | YELLOW | SSOT-VCGC-VRN-TBL0027 | — | T6 非snake:Validation Status;非snake:Source ID;非snake:Report Date;非snake:Report Code;非snake:Filename;非snake:Broker;非snake:Analyst;數字存字串:Ticker;非snake:Ticker;非snake:Y |
| VRN|vrn_mdl089_vrn_v141d8a2_safegetter_sourcemanifestextractor__module__financial_data_text_candidates|c317bea1f2374258 | YELLOW | SSOT-VCGC-VRN-TBL0127 | — | T5 同欄名異型(跨表):Value; T6 非snake:Validation Status;數字存字串:Ticker;非snake:Ticker;非snake:Filename;非snake:Category;非snake:Account;數字存字串:Year;非snake:Year;非snake:Unit;數字存字串:Value;非snake:Value;非 |
| VRN|vrn_mdl089_vrn_v141d8a2_safegetter_sourcemanifestextractor__module__issues|839216bb877b059b | YELLOW | SSOT-VCGC-VRN-TBL0112 | — | T6 非snake:Validation Status;非snake:Dataset;非snake:Source ID;非snake:Filename;非snake:Issue Type;非snake:Problem;非snake:Suggested Fix;無主鍵候選 |
| VRN|vrn_mdl089_vrn_v141d8a2_safegetter_sourcemanifestextractor__module__lineage|ef9a482c499db90c | YELLOW | SSOT-VCGC-VRN-TBL0028 | — | T6 非snake:Validation Status;非snake:Source ID;非snake:Origin File;非snake:Origin SHA256;非snake:Run ID;非snake:Module Chain;非snake:Page Evidence;非snake:Table Evidence;非 |
| VRN|vrn_mdl089_vrn_v141d8a2_safegetter_sourcemanifestextractor__module__d9_gate|99bc06970b47e044 | YELLOW | SSOT-VCGC-VRN-TBL0029 | — | T6 非snake:Validation Status;非snake:Target Output;非snake:Source Candidate;非snake:Write Enable;非snake:Manual Gate Required;非snake:Validation Note |
| VRN|vrn_mdl090_vrn_v141d8a3_singlequoted_sourcemanifestextractor__module__summary|7eb5592307ae3775 | YELLOW | SSOT-VCGC-VRN-TBL0030 | — | T5 同欄名異型(跨表):Time,Value,Expected; T6 非snake:Validation Status;非snake:Time;非snake:Category;非snake:Item;數字存字串:Value;非snake:Value;數字存字串:Expected;非snake:Expected;非snake:Pass;非snake:Severity;非snake:Vali |
| VRN|vrn_mdl090_vrn_v141d8a3_singlequoted_sourcemanifestextractor__module__previous_d8a2_diagnosis|f7cc6f27f7adbfa9 | YELLOW | SSOT-VCGC-VRN-TBL0031 | — | T5 同欄名異型(跨表):Exists,Value; T6 非snake:Validation Status;非snake:Item;非snake:Path;非snake:Exists;非snake:Value;非snake:Validation Note |
| VRN|vrn_mdl090_vrn_v141d8a3_singlequoted_sourcemanifestextractor__module__source_manifest_validated|42e438e35c2f08b9 | YELLOW | SSOT-VCGC-VRN-TBL0032 | — | T5 同欄名異型(跨表):Exists; T6 非snake:Validation Status;非snake:Source ID;非snake:Filename;非snake:Path;非snake:Extension;非snake:Exists;非snake:Allowed For D8;數字存字串:Parsed Ticker;非snake:Parsed Tic |
| VRN|vrn_mdl090_vrn_v141d8a3_singlequoted_sourcemanifestextractor__module__text_anchor_evidence|1fdb6743cc0cf479 | YELLOW | SSOT-VCGC-VRN-TBL0033 | — | T6 非snake:Validation Status;非snake:Source ID;非snake:Filename;非snake:Path;非snake:Extract Method;非snake:Text Chars;數字存字串:Ticker From Filename;非snake:Ticker From File |
| VRN|vrn_mdl090_vrn_v141d8a3_singlequoted_sourcemanifestextractor__module__basic_info_candidates|a20e3a430e891f34 | YELLOW | SSOT-VCGC-VRN-TBL0034 | — | T6 非snake:Validation Status;非snake:Source ID;非snake:Report Date;非snake:Report Code;非snake:Filename;非snake:Broker;非snake:Analyst;數字存字串:Ticker;非snake:Ticker;非snake:Y |
| VRN|vrn_mdl090_vrn_v141d8a3_singlequoted_sourcemanifestextractor__module__financial_data_text_candidates|c317bea1f2374258 | YELLOW | SSOT-VCGC-VRN-TBL0128 | — | T5 同欄名異型(跨表):Value; T6 非snake:Validation Status;數字存字串:Ticker;非snake:Ticker;非snake:Filename;非snake:Category;非snake:Account;數字存字串:Year;非snake:Year;非snake:Unit;數字存字串:Value;非snake:Value;非 |
| VRN|vrn_mdl090_vrn_v141d8a3_singlequoted_sourcemanifestextractor__module__issues|839216bb877b059b | YELLOW | SSOT-VCGC-VRN-TBL0113 | — | T6 非snake:Validation Status;非snake:Dataset;非snake:Source ID;非snake:Filename;非snake:Issue Type;非snake:Problem;非snake:Suggested Fix;無主鍵候選 |
| VRN|vrn_mdl090_vrn_v141d8a3_singlequoted_sourcemanifestextractor__module__lineage|ef9a482c499db90c | YELLOW | SSOT-VCGC-VRN-TBL0035 | — | T6 非snake:Validation Status;非snake:Source ID;非snake:Origin File;非snake:Origin SHA256;非snake:Run ID;非snake:Module Chain;非snake:Page Evidence;非snake:Table Evidence;非 |
| VRN|vrn_mdl090_vrn_v141d8a3_singlequoted_sourcemanifestextractor__module__d9_gate|99bc06970b47e044 | YELLOW | SSOT-VCGC-VRN-TBL0036 | — | T6 非snake:Validation Status;非snake:Target Output;非snake:Source Candidate;非snake:Write Enable;非snake:Manual Gate Required;非snake:Validation Note |
| VRN|vrn_mdl105_vrn_donotredo_doneregistry__support_rule__v0_0_donotredoregistry|5c7377db36326608 | YELLOW | SSOT-VCGC-VRN-TBL0037 | — | T6 非snake:Item;非snake:Status;非snake:DoNotRedo;非snake:Evidence;非snake:Reason;非snake:NextAction;非snake:Risk |
| VRN|vrn_mdl105_vrn_donotredo_doneregistry__support_rule__v0_0_currentbaseevidence|25341170dde825dc | YELLOW | SSOT-VCGC-VRN-TBL0038 | — | T5 同欄名異型(跨表):Exists; T6 非snake:Key;非snake:Type;非snake:Path;非snake:Exists;非snake:ExpectedRows;非snake:ActualRows;非snake:SHA256;非snake:Status;非snake:Risk;非snake:Note |
| VRN|vrn_mdl105_vrn_donotredo_doneregistry__support_rule__v0_0_nextorder|6cd4818c71fac9fa | YELLOW | SSOT-VCGC-VRN-TBL0039 | — | T5 同欄名異型(跨表):Mutation; T6 非snake:Order;非snake:Phase;非snake:Action;非snake:DependsOn;非snake:ShouldRunNow;混型:Mutation;非snake:Mutation;非snake:Reason;非snake:Risk |
| VRN|vrn_mdl117_vrn_activation_registryonly_dry_v1_0_27__support_rule__v1_0|128ec8cd77ac5e02 | YELLOW | SSOT-VCGC-VRN-TBL0114 | — | T5 同欄名異型(跨表):Page,Value; T6 非snake:Page;非snake:Gate;數字存字串:Value;非snake:Value;非snake:Status;非snake:Severity;非snake:Message;無主鍵候選 |
| VRN|vrn_mdl130_vrn_v140r_release_index_pointer_module|29dce0d3b4993ee3 | YELLOW | SSOT-VCGC-VRN-TBL0040 | — | T6 非snake:Flow;非snake:Pass;非snake:Severity;非snake:Message;格內巢狀:Outputs;非snake:Outputs;格內巢狀:Rows;非snake:Rows;非snake:PSComputerName;非snake:RunspaceId;非snake:PSShowCo |
| VRN|vrn_mdl133_vrn_v140j_registry_sidecar_write_gate__support_rule__matrix|b9d443a131294d25 | YELLOW | SSOT-VCGC-VRN-TBL0041 | — | T5 同欄名異型(跨表):Time,Page,Value; T6 非snake:Time;非snake:Page;非snake:Gate;非snake:Value;非snake:Status;非snake:Severity;非snake:Message |
| VRN|vrn_mdl133_vrn_v140j_registry_sidecar_write_gate__support_rule__validation|8d62e0f5a8c56ca2 | YELLOW | SSOT-VCGC-VRN-TBL0042 | — | T5 同欄名異型(跨表):Value,Expected; T6 非snake:Check;混型:Value;非snake:Value;混型:Expected;非snake:Expected;非snake:Pass |
| VRN|vrn_mdl134_vrn_v140i_ssot_registry_pointer_preview__support_rule__matrix|b9d443a131294d25 | YELLOW | SSOT-VCGC-VRN-TBL0043 | — | T5 同欄名異型(跨表):Time,Page,Value; T6 非snake:Time;非snake:Page;非snake:Gate;數字存字串:Value;非snake:Value;非snake:Status;非snake:Severity;非snake:Message |
| VRN|vrn_mdl134_vrn_v140i_ssot_registry_pointer_preview__support_rule__supportive_ast_preview|c748ed30be883f4a | YELLOW | SSOT-VCGC-VRN-TBL0044 | — | T5 同欄名異型(跨表):Exists; T6 非snake:Path;非snake:Exists;非snake:AstOk;非snake:FunctionCount;非snake:ClassCount;非snake:Sha256;非snake:Error |
| VRN|vrn_mdl203_vrn_master_governance_registry_v0615703__governance__registry_rows|d3f6b8a8311ae40a | YELLOW | SSOT-VCGC-VRN-TBL0045 | — | T6 非snake:Status Lights;非snake:run dir;非snake:html path;非snake:json path;非snake:html exists;非snake:json exists;非snake:html sha256;非snake:json sha256;非snake:Severit |
| VRN|vrn_mdl203_vrn_master_governance_registry_v0615703__governance__supportive_assets|14c0ff3f2f48bdbb | YELLOW | SSOT-VCGC-VRN-TBL0046 | — | T5 同欄名異型(跨表):exists,required; T6 非snake:Status Lights;非snake:Severity |
| VRN|vrn_mdl203_vrn_master_governance_registry_v0615703__governance__governance_gates|e259bae93075c17b | YELLOW | SSOT-VCGC-VRN-TBL0047 | — | T5 同欄名異型(跨表):Value; T6 非snake:Status Lights;非snake:Gate;非snake:Value;非snake:Severity |
| VRN|vrn_mdl203_vrn_master_governance_registry_v0615703__governance__future_flow|2ce86cb98f3faf1a | YELLOW | SSOT-VCGC-VRN-TBL0048 | — | T5 同欄名異型(跨表):Mutation; T6 非snake:Status Lights;非snake:Flow;非snake:Step;非snake:Description;非snake:Mutation;非snake:Severity |
| VRN|vrn_mdl203_vrn_master_governance_registry_v0615703__governance__hard_rules|b0c0f6c3065b6f03 | YELLOW | SSOT-VCGC-VRN-TBL0049 | — | T5 同欄名異型(跨表):Value; T6 非snake:Status Lights;非snake:Rule;非snake:Value;非snake:Severity |
| VRN|vrn_mdl204_vrn_master_governance_registry_v0615703__governance__registry_rows|d3f6b8a8311ae40a | YELLOW | SSOT-VCGC-VRN-TBL0050 | — | T6 非snake:Status Lights;非snake:run dir;非snake:html path;非snake:json path;非snake:html exists;非snake:json exists;非snake:html sha256;非snake:json sha256;非snake:Severit |
| VRN|vrn_mdl204_vrn_master_governance_registry_v0615703__governance__supportive_assets|14c0ff3f2f48bdbb | YELLOW | SSOT-VCGC-VRN-TBL0051 | — | T5 同欄名異型(跨表):exists,required; T6 非snake:Status Lights;非snake:Severity |
| VRN|vrn_mdl204_vrn_master_governance_registry_v0615703__governance__governance_gates|e259bae93075c17b | YELLOW | SSOT-VCGC-VRN-TBL0052 | — | T5 同欄名異型(跨表):Value; T6 非snake:Status Lights;非snake:Gate;非snake:Value;非snake:Severity |
| VRN|vrn_mdl204_vrn_master_governance_registry_v0615703__governance__future_flow|2ce86cb98f3faf1a | YELLOW | SSOT-VCGC-VRN-TBL0053 | — | T5 同欄名異型(跨表):Mutation; T6 非snake:Status Lights;非snake:Flow;非snake:Step;非snake:Description;非snake:Mutation;非snake:Severity |
| VRN|vrn_mdl204_vrn_master_governance_registry_v0615703__governance__hard_rules|b0c0f6c3065b6f03 | YELLOW | SSOT-VCGC-VRN-TBL0054 | — | T5 同欄名異型(跨表):Value; T6 非snake:Status Lights;非snake:Rule;非snake:Value;非snake:Severity |
| VRN|vrn_matrixapplicability_ssot_rules|eee27e78d7408166 | YELLOW | SSOT-VCGC-VRN-TBL0055 | — | T6 格內巢狀:not_applicable_when |
| VRN|vrn_matrixapplicability_ssot_pending_operator|fe7b70a6da712e79 | GREEN | SSOT-VCGC-VRN-TBL0056 | — |  |
| VRN|vrn_pluginhub_ssot_stages|1a10d0bb3f838496 | YELLOW | SSOT-VCGC-VRN-TBL0057 | — | T5 同欄名異型(跨表):zh |
| VRN|vrn_pluginhub_ssot_providers|9993cd23bf8d4480 | YELLOW | SSOT-VCGC-VRN-TBL0058 | — | T6 格內巢狀:stages;格內巢狀:imports |
| VRN|vrn_pluginhub_ssot_plans|e41bc3fb65373e5b | YELLOW | SSOT-VCGC-VRN-TBL0059 | — | T6 格內巢狀:xcheck_table |
| VRN|vrn_pluginhub_ssot_ast_categories|0d36e6d9b4b4c0ba | GREEN | SSOT-VCGC-VRN-TBL0060 | — |  |
| VRN|vrn_report_parser_integrated_ssot_support_modules|bf5645c9d0b0de3b | YELLOW | SSOT-VCGC-VRN-TBL0061 | — | T6 格內巢狀:functions;格內巢狀:classes |
| VRN|vrn_report_parser_integrated_ssot_date_regex|6b5cc9b2db38dd99 | YELLOW | SSOT-VCGC-VRN-TBL0062 | — | T6 格內巢狀:flags;格內巢狀:examples_pass;格內巢狀:examples_fail |
| VRN|vrn_report_parser_integrated_ssot_report_date_regex|61bbaf85ccf3d554 | GREEN | SSOT-VCGC-VRN-TBL0063 | — |  |
| VRN|vrn_report_parser_integrated_ssot_broker_aliases|ef7a78b1c42536ae | YELLOW | SSOT-VCGC-VRN-TBL0115 | — | T5 同欄名異型(跨表):source,gate; T6 格內巢狀:aliases;格內巢狀:meta;無主鍵候選 |
| VRN|vrn_report_parser_integrated_ssot_financial_accounts|ef12e130d863b28f | YELLOW | SSOT-VCGC-VRN-TBL0116 | — | T5 同欄名異型(跨表):source; T6 格內巢狀:aliases;無主鍵候選 |
| VRN|vrn_report_parser_integrated_ssot_via_raw_regex|78d8af48b00f4632 | YELLOW | SSOT-VCGC-VRN-TBL0064 | — | T6 格內巢狀:flags;格內巢狀:examples_pass;格內巢狀:examples_fail |
| VRN|vrn_report_parser_integrated_ssot_via_raw_lists|185244608c6de473 | YELLOW | SSOT-VCGC-VRN-TBL0065 | — | T6 格內巢狀:items |
| VRN|vrn_report_parser_integrated_ssot_via_raw_synonyms|f8d1af2c596aca59 | YELLOW | SSOT-VCGC-VRN-TBL0066 | — | T5 同欄名異型(跨表):group; T6 格內巢狀:aliases |
| VRN|vrn_researchreport_ssot|7ff8df49ccd4fd40 | YELLOW | SSOT-VCGC-VRN-TBL0067 | — | T5 同欄名異型(跨表):confidence; T6 數字存字串:confidence;數字存字串:filtered_target_price_proposals;數字存字串:final_primary_ticker_proposals;數字存字串:final_primary_tickers_review_ready;數字存字串:final_ticker_proposal |
| VRN|vrn_researchreport_ssot_schema_v1_fields|8e56b86b26469aae | YELLOW | SSOT-VCGC-VRN-TBL0068 | — | T5 同欄名異型(跨表):required |
| VRN|vrn_s05_fieldregistry_all_regex|f92fc3fe8ca8d3b6 | YELLOW | SSOT-VCGC-VRN-TBL0069 | — | T6 格內巢狀:examples_pass;格內巢狀:examples_fail |
| VRN|vrn_s05_fieldregistry_email_domain_to_broker|d4e7dd2485198593 | YELLOW | SSOT-VCGC-VRN-TBL0070 | — | T5 同欄名異型(跨表):confidence |
| VRN|vrn_s05_fieldregistry_valuation_methods_v0595|5602dfa26f726fe1 | YELLOW | SSOT-VCGC-VRN-TBL0071 | — | T6 格內巢狀:key_synonyms_zh;格內巢狀:key_synonyms_en |
| VRN|vrn_s05_fieldregistry_basicinfo_fields|4f252262df314978 | YELLOW | SSOT-VCGC-VRN-TBL0072 | — | T6 格內巢狀:tolerance;格內巢狀:validation_layers |
| VRN|vrn_s05_fieldregistry_financialdata_fields|247a2c5699ce0036 | YELLOW | SSOT-VCGC-VRN-TBL0073 | — | T6 格內巢狀:tolerance;格內巢狀:source_layer;格內巢狀:validation_layers |
| VRN|vrn_sisterlineage_sync_files|f3f4453df0312db4 | GREEN | SSOT-VCGC-VRN-TBL0074 | — |  |
| VRN|vrn_sourceprovenance_ssot_sources|92956847a14c0d7c | GREEN | SSOT-VCGC-VRN-TBL0075 | — |  |
| VRN|vrn_sourceprovenance_ssot_escalation|71aeab06339f1d24 | YELLOW | SSOT-VCGC-VRN-TBL0117 | — | T6 無主鍵候選 |
| VRN|vrn_stagealias_map_map|e95049abd4f53226 | GREEN | SSOT-VCGC-VRN-TBL0076 | — |  |
| VRN|vrn_tabfields_tabs|87cdbcc709e736ae | YELLOW | SSOT-VCGC-VRN-TBL0077 | — | T5 同欄名異型(跨表):fields; T6 格內巢狀:fields;格內巢狀:cells |
| VRN|vrn_valuationmethod_ssot_methods|85e864f381159929 | YELLOW | SSOT-VCGC-VRN-TBL0078 | — | T5 同欄名異型(跨表):group,en; T6 格內巢狀:legacy_canonical;格內巢狀:en;格內巢狀:en_case_sensitive;格內巢狀:zh_tw;格內巢狀:zh_hk;格內巢狀:zh_cn;格內巢狀:variants;格內巢狀:context_required |
| VRN|vrn_workflow_vrn_ssot_workflows|a5cb283c4da232cb | YELLOW | SSOT-VCGC-VRN-TBL0080 | — | T5 同欄名異型(跨表):spec; T6 格內巢狀:spec;格內巢狀:plan;格內巢狀:steps;格內巢狀:tests |
| VRN|vrn_researchreport_ssot_record_schema_v2_allof|e235f1d58ea7f56f | YELLOW | SSOT-VCGC-VRN-TBL0118 | — | T6 格內巢狀:else;格內巢狀:if;格內巢狀:then;無主鍵候選 |
| VRN|vrn_researchreport_ssot_record_schema_v2_properties|add44235a4f66847 | YELLOW | SSOT-VCGC-VRN-TBL0081 | — | T6 混型:type;格內巢狀:type;非snake:x-via-observed-null-count;非snake:x-via-observed-present-count;非snake:x-via-source;格內巢狀:items;格內巢狀:enum |
| VRN|vrn_researchreport_ssot_schema_v2_full_conditional_rules_materialized|e235f1d58ea7f56f | YELLOW | SSOT-VCGC-VRN-TBL0119 | — | T6 格內巢狀:else;格內巢狀:if;格內巢狀:then;無主鍵候選 |
| VRN|vrn_researchreport_ssot_schema_v2_full_fields|c7d9d16d3cd358ec | YELLOW | SSOT-VCGC-VRN-TBL0082 | — | T5 同欄名異型(跨表):required |
| VRN|vrn_researchreport_ssot_v2|50e72043a5997938 | YELLOW | SSOT-VCGC-VRN-TBL0120 | — | T5 同欄名異型(跨表):confidence; T6 數字存字串:confidence;數字存字串:filtered_target_price_proposals;數字存字串:final_primary_ticker_proposals;數字存字串:final_primary_tickers_review_ready;數字存字串:final_ticker_proposal |
| VRN|vrn_researchreport_ssot_v2_records60_pre_promote_f124bc875468191e|50e72043a5997938 | YELLOW | SSOT-VCGC-VRN-TBL0083 | — | T5 同欄名異型(跨表):confidence; T6 數字存字串:confidence;數字存字串:filtered_target_price_proposals;數字存字串:final_primary_ticker_proposals;數字存字串:final_primary_tickers_review_ready;數字存字串:final_ticker_proposal |
| VRN|vrn_researchreport_ssot_v2_records64_v0155_2f771c00c6dd8d6e|50e72043a5997938 | YELLOW | SSOT-VCGC-VRN-TBL0121 | — | T5 同欄名異型(跨表):confidence; T6 數字存字串:confidence;數字存字串:filtered_target_price_proposals;數字存字串:final_primary_ticker_proposals;數字存字串:final_primary_tickers_review_ready;數字存字串:final_ticker_proposal |
| VRN|vrn_keywordssot_keywords|d92b7f6ad1d3dafc | YELLOW | SSOT-VCGC-VRN-TBL0084 | — | T5 同欄名異型(跨表):freq; T6 格內巢狀:aliases;格內巢狀:sources;格內巢狀:cooccur |
| VRN|vrn_keywordssot_ingest_log|a51c03a46ab9ff21 | YELLOW | SSOT-VCGC-VRN-TBL0085 | — | T5 同欄名異型(跨表):ts,source |
| VRN|synonym_library_v3_scopes|1bd8821d88a78610 | YELLOW | SSOT-VCGC-VRN-TBL0086 | — | T5 同欄名異型(跨表):op,n; T6 格內巢狀:元大;非snake:元大;格內巢狀:元大證券;非snake:元大證券;格內巢狀:元大投顧;非snake:元大投顧;格內巢狀:yuanta;格內巢狀:yuanta securities;非snake:yuanta securities;格內巢狀:凱基;非snake:凱基;格內巢狀:凱基證券;非snake:凱基證 |
| VRN|vrn_annualextract_ssot_items|cccebb42701400bb | YELLOW | SSOT-VCGC-VRN-TBL0087 | — | T5 同欄名異型(跨表):zh,en; T6 格內巢狀:zh;格內巢狀:en |
| VRN|vrn_broker_dict_brokers|eb8acb5be6695bf2 | YELLOW | SSOT-VCGC-VRN-TBL0088 | — | T5 同欄名異型(跨表):source; T6 格內巢狀:aliases |
| VRN|vrn_broker_dict_brokers_extended|bf2225f6b72b5c6b | YELLOW | SSOT-VCGC-VRN-TBL0089 | — | T5 同欄名異型(跨表):en,zh; T6 格內巢狀:aliases |
| VRN|vrn_canonical_trilingual_fill_fills|bfb0e8fc1e79e6be | YELLOW | SSOT-VCGC-VRN-TBL0090 | — | T5 同欄名異型(跨表):zh,en |
| VRN|vrn_findata_synonym_metrics|753b4a3c5a4572d7 | YELLOW | SSOT-VCGC-VRN-TBL0091 | — | T5 同欄名異型(跨表):zh,en,patterns; T6 格內巢狀:synonyms_zh;格內巢狀:synonyms_en;格內巢狀:patterns;格內巢狀:sources;格內巢狀:mops_official;格內巢狀:field_map;格內巢狀:validation_rules;格內巢狀:mdl008_aliases;格內巢狀:merged_from;格內巢狀:r |
| VRN|vrn_finstatement_synonym_statements|7a5dbacb5d66360d | YELLOW | SSOT-VCGC-VRN-TBL0092 | — | T5 同欄名異型(跨表):zh,en; T6 格內巢狀:aliases;格內巢狀:items |
| VRN|vrn_lexicon_fill_template_tree|15e3d0717ba52c5a | YELLOW | SSOT-VCGC-VRN-TBL0093 | — | T5 同欄名異型(跨表):zh,en; T6 格內巢狀:children |
| VRN|vrn_lexicon_tree|15e3d0717ba52c5a | YELLOW | SSOT-VCGC-VRN-TBL0094 | — | T5 同欄名異型(跨表):zh,en; T6 格內巢狀:children |
| VRN|vrn_lexicon_entries|2b5c84276897e9c0 | YELLOW | SSOT-VCGC-VRN-TBL0095 | — | T5 同欄名異型(跨表):zh,en; T6 格內巢狀:aliases;格內巢狀:sources |
| VRN|vrn_lexicon_history|bb2e1e1d3597509d | YELLOW | SSOT-VCGC-VRN-TBL0122 | — | T5 同欄名異型(跨表):op,ts,rejected,kept; T6 格內巢狀:docs |
| VRN|vrn_rating_dict_levels|7b7a4ab98400ca3e | YELLOW | SSOT-VCGC-VRN-TBL0096 | — | T5 同欄名異型(跨表):level,zh,en,source; T6 格內巢狀:score_range;格內巢狀:zh;格內巢狀:en |
| VRN|vrn_broker_list_brokers|5040e556eb9b251e | YELLOW | SSOT-VCGC-VRN-TBL0097 | — | T6 格內巢狀:aliases;格內巢狀:source_layers;格內巢狀:merged_b541 |
| VRN|vrn_broker_list_merge_log|a4bdfe7fca90ec80 | GREEN | SSOT-VCGC-VRN-TBL0098 | — |  |
| VRN|vrn_outputs_ssot_def_output_bundles|3faefcd5e7a13c28 | YELLOW | SSOT-VCGC-VRN-TBL0099 | — | T6 格內巢狀:def_outputs |
| VRN|vrn_outputs_ssot_def_canonical_ids|9195158ac8c51e94 | YELLOW | SSOT-VCGC-VRN-TBL0100 | — | T6 格內巢狀:def_required_in;格內巢狀:def_sector_codes |
| VRN|vrn_outputs_ssot_def_table_contracts|f204ad5b2ba40a77 | YELLOW | SSOT-VCGC-VRN-TBL0101 | — | T6 格內巢狀:def_primary_key;格內巢狀:def_required_columns |
| VRN|vrn_outputs_ssot_def_validation_gates|b36617618b4a43ea | GREEN | SSOT-VCGC-VRN-TBL0102 | — |  |
| VRN|vrn_production_manifest_files|513a2d842ea9ed1d | YELLOW | SSOT-VCGC-VRN-TBL0103 | — | T5 同欄名異型(跨表):required,exists |
| VRN|vrn_report_basic_info_ssot_def_validation_gates|ad96797d0a099a89 | GREEN | SSOT-VCGC-VRN-TBL0104 | — |  |
| VRN|vrn_report_basic_info_ssot_def_historical_quality_evidence_not_revalidated_here|ca62e87418f4a6c5 | GREEN | SSOT-VCGC-VRN-TBL0105 | — |  |
| VRN|vrn_report_data_ssot_index_def_datasets|3440957b44db0616 | YELLOW | SSOT-VCGC-VRN-TBL0106 | — | T6 格內巢狀:def_primary_key;格內巢狀:def_business_key;格內巢狀:def_foreign_key |
| VRN|vrn_report_data_ssot_index_def_artifact_manifest|01bdea8b2ff11184 | GREEN | SSOT-VCGC-VRN-TBL0107 | — |  |
| VRN|vrn_report_financial_data_ssot_def_validation_gates|ad96797d0a099a89 | GREEN | SSOT-VCGC-VRN-TBL0108 | — |  |
| VRN|vrn_report_financial_data_ssot_def_historical_quality_evidence_not_revalidated_here|79a241a446fb66c2 | GREEN | SSOT-VCGC-VRN-TBL0109 | — |  |
| VRN|vrn_ssot_adopt_ledger|e025c46716d8a38a | YELLOW | SSOT-VCGC-VRN-TBL0123 | — | T5 同欄名異型(跨表):ts |
| VRN|vrn_verified_module_registry_h2|fb2366d307046ce1 | YELLOW | SSOT-VCGC-VRN-TBL0110 | — | T5 同欄名異型(跨表):ModuleNo,SizeBytes; T6 數字存字串:ModuleNo;非snake:ModuleNo;非snake:ModuleId;非snake:Name;非snake:Role;非snake:Phase;非snake:SourcePath;非snake:TargetPath;非snake:Extension;數字存字串:SizeBytes;非snake: |
| VRN|vrn_finlexicon_ssot|275a1bf11b086bba | YELLOW | SSOT-VCGC-VRN-TBL0126 | — | T5 同欄名異型(跨表):zh,en; T6 格內巢狀:zh;格內巢狀:en;無主鍵候選 |
| VRN|vrn_dormant_ledger|ccf0a8d239804a96 | YELLOW | SSOT-VCGC-VRN-TBL0124 | — | T5 同欄名異型(跨表):base,ts |
| VRN|vrn_functionmatrix_items_h2|c1849daf33afd0b6 | YELLOW | SSOT-VCGC-VRN-TBL0125 | — | T5 同欄名異型(跨表):source; T6 數字存字串:body_sha;格內巢狀:issues;格內巢狀:similar;格內巢狀:history |

## 功(只列紅/黃與本輪發號)
| 鍵 | 類 | 燈 | 號 | 測 | 旗 |
|---|---|---|---|---|---|
| VCGC|CLS|AdvancedNetworkDataFetcher_OPTIMIZED|UserAgentRotator|v0000 | CLS | YELLOW | VIA-SUP-MDL908-CLS003 | — | F3 同名 UserAgentRotator 散在 3 模組 |
| VCGC|CLS|FLOW_MDL003_FlowSystemOneShot|SystemManager|v0101 | CLS | YELLOW | VIA-SUP-MDL269-CLS007 | — | F3 同名 SystemManager 散在 2 模組 |
| VCGC|CLS|SUP_MDL001_RuntimeImportFirewall|VIA_RuntimeImportFirewall|v0000 | CLS | YELLOW | VIA-SUP-MDL001-CLS001 | — | F3 同名 VIA_RuntimeImportFirewall 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|CLS|SUP_MDL035_VETFVIARuntimeImportFirewall|VIA_RuntimeImportFirewall|v0000 | CLS | YELLOW | VIA-SUP-MDL074-CLS001 | — | F3 同名 VIA_RuntimeImportFirewall 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|CLS|SUP_MDL115_ControlTower|Handler|v0000 | CLS | YELLOW | VIA-SUP-MDL257-CLS003 | — | F3 同名 Handler 散在 4 模組 |
| VCGC|CLS|SUP_MDL122_Docforge|BloomFilter|v0000 | CLS | YELLOW | VIA-SUP-MDL292-CLS002 | — | F3 同名 BloomFilter 散在 2 模組 |
| VCGC|CLS|SUP_MDL122_Docforge|Dedup|v0000 | CLS | YELLOW | VIA-SUP-MDL292-CLS003 | — | F3 同名 Dedup 散在 2 模組 |
| VCGC|CLS|SUP_MDL241_Base20260626173914Dup|Candidate|v0000 | CLS | YELLOW | VIA-SUP-MDL437-CLS003 | — | F3 同名 Candidate 散在 2 模組 |
| VCGC|CLS|SUP_MDL241_Base20260626173914Dup|Requirement|v0000 | CLS | YELLOW | VIA-SUP-MDL437-CLS002 | — | F3 同名 Requirement 散在 2 模組 |
| VCGC|CLS|SUP_MDL287_Exceptions20260626173917Dup|HTTPError|v0000 | CLS | YELLOW | VIA-SUP-MDL458-CLS004 | — | F3 同名 HTTPError 散在 2 模組 |
| VCGC|CLS|SUP_MDL287_Exceptions20260626173917Dup|InvalidHeader|v0000 | CLS | YELLOW | VIA-SUP-MDL458-CLS016 | — | F3 同名 InvalidHeader 散在 2 模組 |
| VCGC|CLS|SUP_MDL287_Exceptions20260626173917Dup|ProxyError|v0000 | CLS | YELLOW | VIA-SUP-MDL458-CLS006 | — | F3 同名 ProxyError 散在 2 模組 |
| VCGC|CLS|SUP_MDL287_Exceptions20260626173917Dup|SSLError|v0000 | CLS | YELLOW | VIA-SUP-MDL458-CLS007 | — | F3 同名 SSLError 散在 2 模組 |
| VCGC|CLS|SUP_MDL287_Exceptions20260626173917Dup|Timeout|v0000 | CLS | YELLOW | VIA-SUP-MDL458-CLS008 | — | F3 同名 Timeout 散在 2 模組 |
| VCGC|CLS|SUP_MDL287_Exceptions20260626173917Dup|UnrewindableBodyError|v0000 | CLS | YELLOW | VIA-SUP-MDL458-CLS022 | — | F3 同名 UnrewindableBodyError 散在 2 模組 |
| VCGC|CLS|SUP_MDL288_Exceptions20260626173920Dup|HTTPError|v0000 | CLS | YELLOW | VIA-SUP-MDL459-CLS001 | — | F3 同名 HTTPError 散在 2 模組 |
| VCGC|CLS|SUP_MDL288_Exceptions20260626173920Dup|InvalidHeader|v0000 | CLS | YELLOW | VIA-SUP-MDL459-CLS033 | — | F3 同名 InvalidHeader 散在 2 模組 |
| VCGC|CLS|SUP_MDL288_Exceptions20260626173920Dup|ProxyError|v0000 | CLS | YELLOW | VIA-SUP-MDL459-CLS006 | — | F3 同名 ProxyError 散在 2 模組 |
| VCGC|CLS|SUP_MDL288_Exceptions20260626173920Dup|SSLError|v0000 | CLS | YELLOW | VIA-SUP-MDL459-CLS005 | — | F3 同名 SSLError 散在 2 模組 |
| VCGC|CLS|SUP_MDL288_Exceptions20260626173920Dup|UnrewindableBodyError|v0000 | CLS | YELLOW | VIA-SUP-MDL459-CLS037 | — | F3 同名 UnrewindableBodyError 散在 2 模組 |
| VCGC|CLS|SUP_MDL352_PkgResources|Distribution|v0000 | CLS | YELLOW | VIA-SUP-MDL478-CLS003 | — | F3 同名 Distribution 散在 2 模組 |
| VCGC|CLS|SUP_MDL352_PkgResources|Environment|v0000 | CLS | YELLOW | VIA-SUP-MDL478-CLS004 | — | F3 同名 Environment 散在 3 模組 |
| VCGC|CLS|SUP_MDL354_Poolmanager|ProxyManager|v0000 | CLS | YELLOW | VIA-SUP-MDL479-CLS002 | — | F3 同名 ProxyManager 散在 3 模組 |
| VCGC|CLS|SUP_MDL376_Resolution|Resolver|v0000 | CLS | YELLOW | VIA-SUP-MDL486-CLS002 | — | F3 同名 Resolver 散在 3 模組 |
| VCGC|CLS|SUP_MDL377_Resolver20260626173914Dup|Resolver|v0000 | CLS | YELLOW | VIA-SUP-MDL487-CLS001 | — | F3 同名 Resolver 散在 3 模組 |
| VCGC|CLS|SUP_MDL418_Securetransport|WrappedSocket|v0000 | CLS | YELLOW | VIA-SUP-MDL516-CLS001 | — | F3 同名 WrappedSocket 散在 2 模組 |
| VCGC|CLS|SUP_MDL440_Style20260626173919Dup|Style|v0000 | CLS | YELLOW | VIA-SUP-MDL525-CLS002 | — | F3 同名 Style 散在 2 模組 |
| VCGC|CLS|SUP_MDL459_Utils20260626173916Dup|InvalidWheelFilename|v0000 | CLS | YELLOW | VIA-SUP-MDL528-CLS002 | — | F3 同名 InvalidWheelFilename 散在 2 模組 |
| VCGC|CLS|SUP_MDL477_Wheel20260626173914Dup|File|v0000 | CLS | YELLOW | VIA-SUP-MDL542-CLS001 | — | F3 同名 File 散在 2 模組 |
| VCGC|CLS|SUP_MDL513_InProcess|BackendUnavailable|v0000 | CLS | YELLOW | VIA-SUP-MDL761-CLS001 | — | F3 同名 BackendUnavailable 散在 2 模組 |
| VCGC|CLS|SUP_MDL513_InProcess|HookMissing|v0000 | CLS | YELLOW | VIA-SUP-MDL761-CLS002 | — | F3 同名 HookMissing 散在 2 模組 |
| VCGC|CLS|SUP_MDL531_MDL081VISVRNNewReportCompatibilityGateV01REPORT|CompatibilityDecision|v01 | CLS | YELLOW | VIA-SUP-MDL822-CLS001 | — | F3 同名 CompatibilityDecision 散在 2 模組;同 body 另見 2 處(候選共用 LIB) |
| VCGC|CLS|SUP_MDL673_MDL263VrnUnifiedOperationDbUiV0582MODULE|Handler|v0582 | CLS | YELLOW | VIA-SUP-MDL1036-CLS001 | — | F3 同名 Handler 散在 4 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|CLS|SUP_MDL674_MDL264VrnUnifiedOperationDbUiV0582MODULE|Handler|v0582 | CLS | YELLOW | VIA-SUP-MDL1037-CLS001 | — | F3 同名 Handler 散在 4 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|CLS|SUP_MDL713_Console20260626173918Dup|Console|v0000 | CLS | YELLOW | VIA-SUP-MDL1089-CLS016 | — | F3 同名 Console 散在 5 模組 |
| VCGC|CLS|SUP_MDL716_Requirements20260626173916Dup|Requirement|v0000 | CLS | YELLOW | VIA-SUP-MDL1090-CLS002 | — | F3 同名 Requirement 散在 2 模組 |
| VCGC|CLS|SUP_MDL738_InvokeVIASSDResourceGuard|ResourceSnapshot|v0100 | CLS | YELLOW | VIA-SUP-MDL194-CLS004 | — | F3 同名跨系統 VCGC,VRN |
| VCGC|CLS|VETF_VIA_RegistryCore_v1|def_ModuleIdentity|v0000 | CLS | YELLOW | VIA-VCGC-MDL1294-CLS001 | — | F3 同名 def_ModuleIdentity 散在 2 模組;同名 def_ModuleIdentity 散在 2 模組;同 body 另見 5 處(候選共用 LIB);同 body 另見 5 處(候選共用 LIB) |
| VCGC|CLS|VETF_VIA_RegistryCore_v1|def_ModuleRecord|v0000 | CLS | YELLOW | VIA-VCGC-MDL1294-CLS002 | — | F3 同名 def_ModuleRecord 散在 2 模組;同名 def_ModuleRecord 散在 2 模組;同 body 另見 5 處(候選共用 LIB);同 body 另見 5 處(候選共用 LIB) |
| VCGC|CLS|VETF_VIA_RegistryCore_v1|def_RegistryState|v0000 | CLS | YELLOW | VIA-VCGC-MDL1294-CLS003 | — | F3 同名 def_RegistryState 散在 2 模組;同名 def_RegistryState 散在 2 模組;同 body 另見 5 處(候選共用 LIB);同 body 另見 5 處(候選共用 LIB) |
| VCGC|CLS|VETF_VIA_Runtime_Bridge_All_in_One|def_VIARuntimeContext|v0000 | CLS | YELLOW | VIA-SUP-MDL1008-CLS001 | — | F3 同名 def_VIARuntimeContext 散在 2 模組;同名 def_VIARuntimeContext 散在 2 模組;同 body 另見 5 處(候選共用 LIB);同 body 另見 5 處(候選共用 LIB) |
| VCGC|CLS|VETF_VIA_SSOT_Unified|SSOT|v0000 | CLS | YELLOW | VIA-SUP-MDL1061-CLS002 | — | F3 同名 SSOT 散在 3 模組;同名 SSOT 散在 3 模組;同 body 另見 5 處(候選共用 LIB);同 body 另見 5 處(候選共用 LIB) |
| VCGC|CLS|VETF_VIA_SSOT_Unified|VIAFinancialSubjectMatch|v0000 | CLS | YELLOW | VIA-SUP-MDL1061-CLS003 | — | F3 同名 VIAFinancialSubjectMatch 散在 2 模組;同名 VIAFinancialSubjectMatch 散在 2 模組;同 body 另見 5 處(候選共用 LIB);同 body 另見 5 處(候選共用 LIB) |
| VCGC|CLS|VETF_VIA_SSOT_Unified|_VIAStateBox|v0000 | CLS | YELLOW | VIA-SUP-MDL1061-CLS001 | — | F3 同 body 另見 11 處(候選共用 LIB);同 body 另見 11 處(候選共用 LIB) |
| VCGC|CLS|VETF_VIA_Supportive_Runtime_HardGate_Bridge|def_ModuleGate|v0000 | CLS | YELLOW | VIA-SUP-MDL1009-CLS001 | — | F3 同名 def_ModuleGate 散在 2 模組;同名 def_ModuleGate 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|VETF_VIA_Supportive_Runtime_HardGate_Bridge|def_RuntimeState|v0000 | CLS | YELLOW | VIA-SUP-MDL1009-CLS002 | — | F3 同名 def_RuntimeState 散在 2 模組;同名 def_RuntimeState 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|VETF_VIS_InstallHealthRegistry|VISHealthRecord|v0000 | CLS | YELLOW | VIA-VCGC-MDL1295-CLS001 | — | F3 同名 VISHealthRecord 散在 2 模組;同名 VISHealthRecord 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|VETF_VIS_VRN_HistoricalValidationPolicy|def_ValidationSource|v0100 | CLS | YELLOW | VIA-VRN-MDL254-CLS001 | — | F3 同名 def_ValidationSource 散在 2 模組;同名 def_ValidationSource 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|VIA_AutoCodeGenerator|SSOT|v0100 | CLS | YELLOW | VIA-VCGC-MDL1296-CLS002 | — | F3 同名 SSOT 散在 3 模組 |
| VCGC|CLS|VIA_CentralGovernanceConsole|Console|v0000 | CLS | YELLOW | VIA-SUP-MDL231-CLS001 | — | F3 同名 Console 散在 5 模組 |
| VCGC|CLS|VIA_CentralGovernanceConsole|FileRecord|v0000 | CLS | YELLOW | VIA-SUP-MDL231-CLS005 | — | F3 同名 FileRecord 散在 2 模組 |
| VCGC|CLS|VIA_CentralGovernanceConsole|Gate|v0000 | CLS | YELLOW | VIA-SUP-MDL231-CLS015 | — | F3 同名 Gate 散在 2 模組 |
| VCGC|CLS|VIA_CentralGovernanceConsole|SynonymSSOT|v0000 | CLS | YELLOW | VIA-SUP-MDL231-CLS014 | — | F3 同名 SynonymSSOT 散在 2 模組 |
| VCGC|CLS|VIA_CentralGovernanceEngine|Console|v0000 | CLS | YELLOW | VIA-SUP-MDL232-CLS001 | — | F3 同名 Console 散在 5 模組;同 body 另見 2 處(候選共用 LIB) |
| VCGC|CLS|VIA_Central_SSOT_Contract_Sync_Engine|FieldSpec|v0000 | CLS | YELLOW | VIA-VCGC-MDL1297-CLS003 | — | F3 同名 FieldSpec 散在 2 模組 |
| VCGC|CLS|VIA_Central_SSOT_Contract_Sync_Engine|Gate|v0000 | CLS | YELLOW | VIA-VCGC-MDL1297-CLS001 | — | F3 同名 Gate 散在 2 模組 |
| VCGC|CLS|VIA_DownwardController|Capability|v0000 | CLS | YELLOW | VIA-SUP-MDL233-CLS002 | — | F3 同名跨系統 VCGC,VRN |
| VCGC|CLS|VIA_DownwardController|Console|v0000 | CLS | YELLOW | VIA-SUP-MDL233-CLS001 | — | F3 同名 Console 散在 5 模組;同 body 另見 2 處(候選共用 LIB) |
| VCGC|CLS|VIA_FilePriorityRouter|Console|v0000 | CLS | YELLOW | VIA-SUP-MDL234-CLS001 | — | F3 同名 Console 散在 5 模組;同 body 另見 2 處(候選共用 LIB) |
| VCGC|CLS|VIA_FilePriorityRouter|FileRecord|v0000 | CLS | YELLOW | VIA-SUP-MDL234-CLS003 | — | F3 同名 FileRecord 散在 2 模組 |
| VCGC|CLS|VIA_Financial_Institution_SSOT|TextBlock|v0100 | CLS | YELLOW | VIA-SUP-MDL1066-CLS008 | — | F3 同名跨系統 VCGC,VRN |
| VCGC|CLS|VIA_RegistryCore_v1|def_ModuleIdentity|v0000 | CLS | YELLOW | VIA-VCGC-MDL1303-CLS001 | — | F3 同名 def_ModuleIdentity 散在 2 模組;同名 def_ModuleIdentity 散在 2 模組;同名 def_ModuleIdentity 散在 2 模組;同名 def_ModuleIdentity 散在 2 模組; |
| VCGC|CLS|VIA_RegistryCore_v1|def_ModuleRecord|v0000 | CLS | YELLOW | VIA-VCGC-MDL1303-CLS002 | — | F3 同名 def_ModuleRecord 散在 2 模組;同名 def_ModuleRecord 散在 2 模組;同名 def_ModuleRecord 散在 2 模組;同名 def_ModuleRecord 散在 2 模組;同 body 另 |
| VCGC|CLS|VIA_RegistryCore_v1|def_RegistryState|v0000 | CLS | YELLOW | VIA-VCGC-MDL1303-CLS003 | — | F3 同名 def_RegistryState 散在 2 模組;同名 def_RegistryState 散在 2 模組;同名 def_RegistryState 散在 2 模組;同名 def_RegistryState 散在 2 模組;同 bo |
| VCGC|CLS|VIA_Runtime_Bridge_All_in_One|def_VIARuntimeContext|v0000 | CLS | YELLOW | VIA-SUP-MDL1014-CLS001 | — | F3 同名 def_VIARuntimeContext 散在 2 模組;同名 def_VIARuntimeContext 散在 2 模組;同名 def_VIARuntimeContext 散在 2 模組;同名 def_VIARuntimeCont |
| VCGC|CLS|VIA_SSOT_Unified|SSOT|v0000 | CLS | YELLOW | VIA-SUP-MDL1071-CLS002 | — | F3 同名 SSOT 散在 3 模組;同名 SSOT 散在 3 模組;同名 SSOT 散在 3 模組;同名 SSOT 散在 3 模組;同 body 另見 5 處(候選共用 LIB);同 body 另見 5 處(候選共用 LIB);同 body 另 |
| VCGC|CLS|VIA_SSOT_Unified|VIAFinancialSubjectMatch|v0000 | CLS | YELLOW | VIA-SUP-MDL1071-CLS003 | — | F3 同名 VIAFinancialSubjectMatch 散在 2 模組;同名 VIAFinancialSubjectMatch 散在 2 模組;同名 VIAFinancialSubjectMatch 散在 2 模組;同名 VIAFinanc |
| VCGC|CLS|VIA_SSOT_Unified|_VIAStateBox|v0000 | CLS | YELLOW | VIA-SUP-MDL1071-CLS001 | — | F3 同 body 另見 11 處(候選共用 LIB);同 body 另見 11 處(候選共用 LIB);同 body 另見 11 處(候選共用 LIB);同 body 另見 11 處(候選共用 LIB) |
| VCGC|CLS|VIA_Supportive_Runtime_HardGate_Bridge|def_ModuleGate|v0000 | CLS | YELLOW | VIA-SUP-MDL1015-CLS001 | — | F3 同名 def_ModuleGate 散在 2 模組;同名 def_ModuleGate 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|VIA_Supportive_Runtime_HardGate_Bridge|def_RuntimeState|v0000 | CLS | YELLOW | VIA-SUP-MDL1015-CLS002 | — | F3 同名 def_RuntimeState 散在 2 模組;同名 def_RuntimeState 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|VIS_InstallHealthRegistry|VISHealthRecord|v0000 | CLS | YELLOW | VIA-VCGC-MDL1304-CLS001 | — | F3 同名 VISHealthRecord 散在 2 模組;同名 VISHealthRecord 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|VIS_VRN_HistoricalValidationPolicy|def_ValidationSource|v0100 | CLS | YELLOW | VIA-VRN-MDL255-CLS001 | — | F3 同名 def_ValidationSource 散在 2 模組;同名 def_ValidationSource 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|VIS_VRN_NewReportCompatibilityGate|CompatibilityDecision|v01 | CLS | YELLOW | VIA-VRN-MDL256-CLS001 | — | F3 同名 CompatibilityDecision 散在 2 模組;同名 CompatibilityDecision 散在 2 模組;同 body 另見 2 處(候選共用 LIB);同 body 另見 2 處(候選共用 LIB) |
| VCGC|CLS|VeritasAegisNexus|AntiAntiScrape|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS001 | — | F3 同名 AntiAntiScrape 散在 2 模組;同名 AntiAntiScrape 散在 2 模組;同名 AntiAntiScrape 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 |
| VCGC|CLS|VeritasAegisNexus|AsyncHTTPClient|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS002 | — | F3 同名 AsyncHTTPClient 散在 2 模組;同名 AsyncHTTPClient 散在 2 模組;同名 AsyncHTTPClient 散在 2 模組 |
| VCGC|CLS|VeritasAegisNexus|AsyncVDSFetcher|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS003 | — | F3 同名 AsyncVDSFetcher 散在 2 模組;同名 AsyncVDSFetcher 散在 2 模組;同名 AsyncVDSFetcher 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候 |
| VCGC|CLS|VeritasAegisNexus|AutoFailover|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS004 | — | F3 同名 AutoFailover 散在 2 模組;同名 AutoFailover 散在 2 模組;同名 AutoFailover 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB); |
| VCGC|CLS|VeritasAegisNexus|CircuitBreaker|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS005 | — | F3 同名 CircuitBreaker 散在 2 模組;同名 CircuitBreaker 散在 2 模組;同名 CircuitBreaker 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 |
| VCGC|CLS|VeritasAegisNexus|CircuitBreakerListener|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS006 | — | F3 同名 CircuitBreakerListener 散在 2 模組;同名 CircuitBreakerListener 散在 2 模組;同名 CircuitBreakerListener 散在 2 模組;同 body 另見 3 處(候選共用 |
| VCGC|CLS|VeritasAegisNexus|CircuitBreakerOpen|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS007 | — | F3 同名 CircuitBreakerOpen 散在 2 模組;同名 CircuitBreakerOpen 散在 2 模組;同名 CircuitBreakerOpen 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body |
| VCGC|CLS|VeritasAegisNexus|CloudflareBypass|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS008 | — | F3 同名 CloudflareBypass 散在 2 模組;同名 CloudflareBypass 散在 2 模組;同名 CloudflareBypass 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3  |
| VCGC|CLS|VeritasAegisNexus|ComplianceProfile|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS009 | — | F3 同名 ComplianceProfile 散在 2 模組;同名 ComplianceProfile 散在 2 模組;同名 ComplianceProfile 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 |
| VCGC|CLS|VeritasAegisNexus|ComplianceReactor|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS010 | — | F3 同名 ComplianceReactor 散在 2 模組;同名 ComplianceReactor 散在 2 模組;同名 ComplianceReactor 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 |
| VCGC|CLS|VeritasAegisNexus|DataSourceFailover|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS011 | — | F3 同名 DataSourceFailover 散在 2 模組;同名 DataSourceFailover 散在 2 模組;同名 DataSourceFailover 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body |
| VCGC|CLS|VeritasAegisNexus|DuckDBTypeGuard|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS012 | — | F3 同名 DuckDBTypeGuard 散在 2 模組;同名 DuckDBTypeGuard 散在 2 模組;同名 DuckDBTypeGuard 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候 |
| VCGC|CLS|VeritasAegisNexus|ExponentialBackoff|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS013 | — | F3 同名 ExponentialBackoff 散在 2 模組;同名 ExponentialBackoff 散在 2 模組;同名 ExponentialBackoff 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body |
| VCGC|CLS|VeritasAegisNexus|HeadersBuilder|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS014 | — | F3 同名 HeadersBuilder 散在 2 模組;同名 HeadersBuilder 散在 2 模組;同名 HeadersBuilder 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 |
| VCGC|CLS|VeritasAegisNexus|HttpConfig|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS015 | — | F3 同名 HttpConfig 散在 2 模組;同名 HttpConfig 散在 2 模組;同名 HttpConfig 散在 2 模組 |
| VCGC|CLS|VeritasAegisNexus|HttpxClient|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS016 | — | F3 同名 HttpxClient 散在 2 模組;同名 HttpxClient 散在 2 模組;同名 HttpxClient 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB);同 b |
| VCGC|CLS|VeritasAegisNexus|IPBlacklistDetector|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS017 | — | F3 同名 IPBlacklistDetector 散在 2 模組;同名 IPBlacklistDetector 散在 2 模組;同名 IPBlacklistDetector 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 b |
| VCGC|CLS|VeritasAegisNexus|LibraryInfo|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS018 | — | F3 同名 LibraryInfo 散在 2 模組;同名 LibraryInfo 散在 2 模組;同名 LibraryInfo 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB);同 b |
| VCGC|CLS|VeritasAegisNexus|LibraryRegistry|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS019 | — | F3 同名 LibraryRegistry 散在 2 模組;同名 LibraryRegistry 散在 2 模組;同名 LibraryRegistry 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候 |
| VCGC|CLS|VeritasAegisNexus|MockDataManager|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS020 | — | F3 同名 MockDataManager 散在 2 模組;同名 MockDataManager 散在 2 模組;同名 MockDataManager 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候 |
| VCGC|CLS|VeritasAegisNexus|NetworkHealthChecker|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS021 | — | F3 同名 NetworkHealthChecker 散在 2 模組;同名 NetworkHealthChecker 散在 2 模組;同名 NetworkHealthChecker 散在 2 模組;同 body 另見 3 處(候選共用 LIB); |
| VCGC|CLS|VeritasAegisNexus|ProxyInfo|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS022 | — | F3 同名 ProxyInfo 散在 2 模組;同名 ProxyInfo 散在 2 模組;同名 ProxyInfo 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB);同 body 另見 |
| VCGC|CLS|VeritasAegisNexus|ProxyManager|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS023 | — | F3 同名 ProxyManager 散在 3 模組;同名 ProxyManager 散在 3 模組;同名 ProxyManager 散在 3 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB); |
| VCGC|CLS|VeritasAegisNexus|QuotaSaverCache|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS024 | — | F3 同名 QuotaSaverCache 散在 2 模組;同名 QuotaSaverCache 散在 2 模組;同名 QuotaSaverCache 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候 |
| VCGC|CLS|VeritasAegisNexus|RateLimiter|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS025 | — | F3 同名 RateLimiter 散在 3 模組;同名 RateLimiter 散在 3 模組;同名 RateLimiter 散在 3 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB);同 b |
| VCGC|CLS|VeritasAegisNexus|ResilientHTTPClient|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS026 | — | F3 同名 ResilientHTTPClient 散在 2 模組;同名 ResilientHTTPClient 散在 2 模組;同名 ResilientHTTPClient 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 b |
| VCGC|CLS|VeritasAegisNexus|ScrapingStrategy|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS027 | — | F3 同名 ScrapingStrategy 散在 2 模組;同名 ScrapingStrategy 散在 2 模組;同名 ScrapingStrategy 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3  |
| VCGC|CLS|VeritasAegisNexus|TaiwanDataSources|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS028 | — | F3 同名 TaiwanDataSources 散在 2 模組;同名 TaiwanDataSources 散在 2 模組;同名 TaiwanDataSources 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 |
| VCGC|CLS|VeritasAegisNexus|UserAgentRotator|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS029 | — | F3 同名 UserAgentRotator 散在 3 模組;同名 UserAgentRotator 散在 3 模組;同名 UserAgentRotator 散在 3 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3  |
| VCGC|CLS|VeritasAegisNexus|VDSCircuitBreaker|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS030 | — | F3 同名 VDSCircuitBreaker 散在 2 模組;同名 VDSCircuitBreaker 散在 2 模組;同名 VDSCircuitBreaker 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 |
| VCGC|CLS|VeritasAegisNexus|VDSFailoverEngine|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS031 | — | F3 同名 VDSFailoverEngine 散在 2 模組;同名 VDSFailoverEngine 散在 2 模組;同名 VDSFailoverEngine 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 |
| VCGC|CLS|VeritasAegisNexus|VDSFailoverEngineX|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS032 | — | F3 同名 VDSFailoverEngineX 散在 2 模組;同名 VDSFailoverEngineX 散在 2 模組;同名 VDSFailoverEngineX 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body |
| VCGC|CLS|VeritasAegisNexus|VDSNotificationProvider|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS033 | — | F3 同名 VDSNotificationProvider 散在 2 模組;同名 VDSNotificationProvider 散在 2 模組;同名 VDSNotificationProvider 散在 2 模組;同 body 另見 3 處(候 |
| VCGC|CLS|VeritasAegisNexus|VDSProtocolError|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS034 | — | F3 同名 VDSProtocolError 散在 2 模組;同名 VDSProtocolError 散在 2 模組;同名 VDSProtocolError 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3  |
| VCGC|CLS|VeritasAegisNexus|VDSProtocolGuard|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS035 | — | F3 同名 VDSProtocolGuard 散在 2 模組;同名 VDSProtocolGuard 散在 2 模組;同名 VDSProtocolGuard 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3  |
| VCGC|CLS|VeritasAegisNexus|VDSResilienceEngine|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS036 | — | F3 同名 VDSResilienceEngine 散在 2 模組;同名 VDSResilienceEngine 散在 2 模組;同名 VDSResilienceEngine 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 b |
| VCGC|CLS|VeritasAegisNexus|VDSYahooFetcher|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS037 | — | F3 同名 VDSYahooFetcher 散在 2 模組;同名 VDSYahooFetcher 散在 2 模組;同名 VDSYahooFetcher 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候 |
| VCGC|CLS|VeritasAegisNexus|_AegisLazyModule|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS038 | — | F3 同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|VeritasAegisNexus|_VIAStateBox|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS039 | — | F3 同 body 另見 11 處(候選共用 LIB);同 body 另見 11 處(候選共用 LIB);同 body 另見 11 處(候選共用 LIB) |
| VCGC|CLS|VeritasAegisNexus|yFinanceShield|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS040 | — | F3 同名 yFinanceShield 散在 2 模組;同名 yFinanceShield 散在 2 模組;同名 yFinanceShield 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候選共用 |
| VCGC|CLS|VeritasAegisNexus|yFinanceShieldX|v0000 | CLS | YELLOW | VIA-SUP-ENG019-CLS041 | — | F3 同名 yFinanceShieldX 散在 2 模組;同名 yFinanceShieldX 散在 2 模組;同名 yFinanceShieldX 散在 2 模組;同 body 另見 3 處(候選共用 LIB);同 body 另見 3 處(候 |
| VCGC|CLS|VeritasCeleritas|DataValidator|v1141 | CLS | YELLOW | VIA-SUP-ENG014-CLS009 | — | F3 同名跨系統 VCGC,VDF |
| VCGC|CLS|VeritasCeleritas|FinanceEngine|v1141 | CLS | YELLOW | VIA-SUP-ENG014-CLS026 | — | F3 同名 FinanceEngine 散在 2 模組;同名 FinanceEngine 散在 2 模組 |
| VCGC|CLS|VeritasCeleritas|Timer|v1141 | CLS | YELLOW | VIA-SUP-ENG014-CLS045 | — | F3 同名 Timer 散在 2 模組;同名 Timer 散在 2 模組 |
| VCGC|CLS|VeritasCeleritas|_VIAStateBox|v1141 | CLS | YELLOW | VIA-SUP-ENG014-CLS102 | — | F3 同 body 另見 11 處(候選共用 LIB);同 body 另見 11 處(候選共用 LIB) |
| VCGC|CLS|_dists|Distribution|v0000 | CLS | YELLOW | VIA-SUP-MDL554-CLS002 | — | F3 同名 Distribution 散在 2 模組 |
| VCGC|CLS|_envs|Environment|v0000 | CLS | YELLOW | VIA-SUP-MDL556-CLS002 | — | F3 同名 Environment 散在 3 模組 |
| VCGC|CLS|_impl|BackendUnavailable|v0000 | CLS | YELLOW | VIA-SUP-MDL558-CLS002 | — | F3 同名 BackendUnavailable 散在 2 模組 |
| VCGC|CLS|_impl|HookMissing|v0000 | CLS | YELLOW | VIA-SUP-MDL558-CLS003 | — | F3 同名 HookMissing 散在 2 模組 |
| VCGC|CLS|_macos|CFConst|v0000 | CLS | YELLOW | VIA-SUP-MDL563-CLS001 | — | F3 同名 CFConst 散在 2 模組 |
| VCGC|CLS|_parser|Node|v0000 | CLS | YELLOW | VIA-SUP-MDL567-CLS001 | — | F3 同名 Node 散在 2 模組 |
| VCGC|CLS|_parser|ParsedRequirement|v0000 | CLS | YELLOW | VIA-SUP-MDL567-CLS005 | — | F3 同名 ParsedRequirement 散在 2 模組 |
| VCGC|CLS|_stack|Stack|v0000 | CLS | YELLOW | VIA-SUP-MDL572-CLS001 | — | F3 同名 Stack 散在 2 模組 |
| VCGC|CLS|adapters|HTTPAdapter|v0000 | CLS | YELLOW | VIA-SUP-MDL582-CLS002 | — | F3 同名 HTTPAdapter 散在 2 模組 |
| VCGC|CLS|adapter|CacheControlAdapter|v0000 | CLS | YELLOW | VIA-SUP-MDL581-CLS001 | — | F3 同名 CacheControlAdapter 散在 2 模組 |
| VCGC|CLS|bindings|CFConst|v0000 | CLS | YELLOW | VIA-SUP-MDL591-CLS001 | — | F3 同名 CFConst 散在 2 模組 |
| VCGC|CLS|cache|Cache|v0000 | CLS | YELLOW | VIA-SUP-MDL993-CLS001 | — | F3 同名 Cache 散在 2 模組 |
| VCGC|CLS|exceptions|InvalidWheelFilename|v0000 | CLS | YELLOW | VIA-SUP-MDL615-CLS017 | — | F3 同名 InvalidWheelFilename 散在 2 模組 |
| VCGC|CLS|layout|Layout|v0000 | CLS | YELLOW | VIA-SUP-MDL1118-CLS008 | — | F3 同名跨系統 VCGC,VRN |
| VCGC|CLS|layout|LayoutError|v0000 | CLS | YELLOW | VIA-SUP-MDL1118-CLS002 | — | F3 同名跨系統 VCGC,VDF |
| VCGC|CLS|markers|Environment|v0000 | CLS | YELLOW | VIA-SUP-MDL647-CLS004 | — | F3 同名 Environment 散在 3 模組 |
| VCGC|CLS|markup|Tag|v0000 | CLS | YELLOW | VIA-SUP-MDL648-CLS001 | — | F3 同名 Tag 散在 2 模組 |
| VCGC|CLS|prepare|File|v0000 | CLS | YELLOW | VIA-SUP-MDL661-CLS001 | — | F3 同名 File 散在 2 模組 |
| VCGC|CLS|pretty|Node|v0000 | CLS | YELLOW | VIA-SUP-MDL662-CLS002 | — | F3 同名 Node 散在 2 模組 |
| VCGC|CLS|progress|Progress|v0000 | CLS | YELLOW | VIA-SUP-MDL663-CLS019 | — | F3 同名 Progress 散在 3 模組 |
| VCGC|CLS|pyopenssl|WrappedSocket|v0000 | CLS | YELLOW | VIA-SUP-MDL668-CLS001 | — | F3 同名 WrappedSocket 散在 2 模組 |
| VCGC|CLS|req_file|ParsedRequirement|v0000 | CLS | YELLOW | VIA-SUP-MDL674-CLS001 | — | F3 同名 ParsedRequirement 散在 2 模組 |
| VCGC|CLS|resolver|Resolver|v0000 | CLS | YELLOW | VIA-SUP-MDL676-CLS001 | — | F3 同名 Resolver 散在 3 模組 |
| VCGC|CLS|resources|Resource|v0000 | CLS | YELLOW | VIA-SUP-MDL677-CLS003 | — | F3 同名 Resource 散在 2 模組 |
| VCGC|CLS|session|CacheControlAdapter|v0000 | CLS | YELLOW | VIA-SUP-MDL690-CLS004 | — | F3 同名 CacheControlAdapter 散在 2 模組 |
| VCGC|CLS|session|HTTPAdapter|v0000 | CLS | YELLOW | VIA-SUP-MDL690-CLS003 | — | F3 同名 HTTPAdapter 散在 2 模組 |
| VCGC|CLS|spinners|RateLimiter|v0000 | CLS | YELLOW | VIA-SUP-MDL697-CLS004 | — | F3 同名 RateLimiter 散在 3 模組 |
| VCGC|CLS|ssot_synonyms|SynonymSSOT|v0000 | CLS | YELLOW | VIA-SUP-MDL170-CLS001 | — | F3 同名 SynonymSSOT 散在 2 模組 |
| VCGC|CLS|style|Style|v0000 | CLS | YELLOW | VIA-SUP-MDL701-CLS002 | — | F3 同名 Style 散在 2 模組 |
| VCGC|CLS|tags|Tag|v0000 | CLS | YELLOW | VIA-SUP-MDL703-CLS001 | — | F3 同名 Tag 散在 2 模組 |
| VCGC|CLS|terms|Candidate|v0000 | CLS | YELLOW | VIA-SUP-MDL153-CLS001 | — | F3 同名 Candidate 散在 2 模組 |
| VCGC|CLS|test_executor_and_di|Resource|v0000 | CLS | YELLOW | VIA-SUP-MDL254-CLS003 | — | F3 同名 Resource 散在 2 模組 |
| VCGC|CLS|timeout|Timeout|v0000 | CLS | YELLOW | VIA-SUP-MDL706-CLS001 | — | F3 同名 Timeout 散在 2 模組 |
| VCGC|CLS|traceback|Stack|v0000 | CLS | YELLOW | VIA-SUP-MDL708-CLS003 | — | F3 同名 Stack 散在 2 模組 |
| VCGC|CLS|util|Cache|v0000 | CLS | YELLOW | VIA-SUP-MDL716-CLS004 | — | F3 同名 Cache 散在 2 模組 |
| VCGC|CLS|util|Progress|v0000 | CLS | YELLOW | VIA-SUP-MDL716-CLS007 | — | F3 同名 Progress 散在 3 模組 |
| VCGC|CLS|via_aegis_netcore|AntiAntiScrape|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS014 | — | F3 同名 AntiAntiScrape 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|AsyncHTTPClient|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS033 | — | F3 同名 AsyncHTTPClient 散在 2 模組 |
| VCGC|CLS|via_aegis_netcore|AsyncVDSFetcher|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS035 | — | F3 同名 AsyncVDSFetcher 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|AutoFailover|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS016 | — | F3 同名 AutoFailover 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|CircuitBreaker|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS011 | — | F3 同名 CircuitBreaker 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|CircuitBreakerListener|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS024 | — | F3 同名 CircuitBreakerListener 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|CircuitBreakerOpen|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS010 | — | F3 同名 CircuitBreakerOpen 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|CloudflareBypass|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS015 | — | F3 同名 CloudflareBypass 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|ComplianceProfile|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS039 | — | F3 同名 ComplianceProfile 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|ComplianceReactor|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS041 | — | F3 同名 ComplianceReactor 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|DataSourceFailover|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS032 | — | F3 同名 DataSourceFailover 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|DuckDBTypeGuard|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS022 | — | F3 同名 DuckDBTypeGuard 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|ExponentialBackoff|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS009 | — | F3 同名 ExponentialBackoff 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|HeadersBuilder|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS006 | — | F3 同名 HeadersBuilder 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|HttpConfig|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS012 | — | F3 同名 HttpConfig 散在 2 模組 |
| VCGC|CLS|via_aegis_netcore|HttpxClient|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS034 | — | F3 同名 HttpxClient 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|IPBlacklistDetector|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS030 | — | F3 同名 IPBlacklistDetector 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|LibraryInfo|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS003 | — | F3 同名 LibraryInfo 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|LibraryRegistry|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS004 | — | F3 同名 LibraryRegistry 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|MockDataManager|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS036 | — | F3 同名 MockDataManager 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|NetworkHealthChecker|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS031 | — | F3 同名 NetworkHealthChecker 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|ProxyInfo|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS007 | — | F3 同名 ProxyInfo 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|ProxyManager|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS008 | — | F3 同名 ProxyManager 散在 3 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|QuotaSaverCache|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS021 | — | F3 同名 QuotaSaverCache 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|RateLimiter|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS017 | — | F3 同名 RateLimiter 散在 3 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|ResilientHTTPClient|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS013 | — | F3 同名 ResilientHTTPClient 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|ScrapingStrategy|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS040 | — | F3 同名 ScrapingStrategy 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|TaiwanDataSources|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS019 | — | F3 同名 TaiwanDataSources 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|UserAgentRotator|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS005 | — | F3 同名 UserAgentRotator 散在 3 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|VDSCircuitBreaker|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS025 | — | F3 同名 VDSCircuitBreaker 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|VDSFailoverEngine|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS020 | — | F3 同名 VDSFailoverEngine 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|VDSFailoverEngineX|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS038 | — | F3 同名 VDSFailoverEngineX 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|VDSNotificationProvider|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS029 | — | F3 同名 VDSNotificationProvider 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|VDSProtocolError|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS023 | — | F3 同名 VDSProtocolError 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|VDSProtocolGuard|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS026 | — | F3 同名 VDSProtocolGuard 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|VDSResilienceEngine|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS027 | — | F3 同名 VDSResilienceEngine 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|VDSYahooFetcher|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS028 | — | F3 同名 VDSYahooFetcher 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|_AegisLazyModule|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS002 | — | F3 同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|_VIAStateBox|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS001 | — | F3 同 body 另見 11 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|yFinanceShield|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS018 | — | F3 同名 yFinanceShield 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_aegis_netcore|yFinanceShieldX|v0100 | CLS | YELLOW | VIA-SUP-MDL1001-CLS037 | — | F3 同名 yFinanceShieldX 散在 2 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|CLS|via_engines|FinanceEngine|v0000 | CLS | YELLOW | VIA-SUP-MDL177-CLS005 | — | F3 同名 FinanceEngine 散在 2 模組 |
| VCGC|CLS|via_engines|SSOTEngine|v0000 | CLS | YELLOW | VIA-SUP-MDL177-CLS002 | — | F3 同名 SSOTEngine 散在 2 模組 |
| VCGC|CLS|via_forge|BloomFilter|v0000 | CLS | YELLOW | VIA-SUP-MDL300-CLS005 | — | F3 同名 BloomFilter 散在 2 模組 |
| VCGC|CLS|via_forge|Dedup|v0000 | CLS | YELLOW | VIA-SUP-MDL300-CLS006 | — | F3 同名 Dedup 散在 2 模組 |
| VCGC|CLS|via_forge|Progress|v0000 | CLS | YELLOW | VIA-SUP-MDL300-CLS008 | — | F3 同名 Progress 散在 3 模組 |
| VCGC|CLS|via_forge|Timer|v0000 | CLS | YELLOW | VIA-SUP-MDL300-CLS009 | — | F3 同名 Timer 散在 2 模組 |
| VCGC|CLS|via_iface_autosync|FieldSpec|v0101 | CLS | YELLOW | VIA-VCGC-MDL1342-CLS001 | — | F3 同名 FieldSpec 散在 2 模組 |
| VCGC|CLS|via_manager|SystemManager|v0000 | CLS | YELLOW | VIA-SUP-MDL1121-CLS001 | — | F3 同名 SystemManager 散在 2 模組;同名 SystemManager 散在 2 模組 |
| VCGC|CLS|via_pmine|SSOTEngine|v0000 | CLS | YELLOW | VIA-SUP-MDL307-CLS003 | — | F3 同名 SSOTEngine 散在 2 模組 |
| VCGC|CLS|via_server|Handler|v0000 | CLS | YELLOW | VIA-SUP-MDL310-CLS001 | — | F3 同名 Handler 散在 4 模組 |
| VDF|CLS|VDF_ENG044_MDLXXXYFinanceGlobalDataFetcher|DataValidator|v0000 | CLS | YELLOW | VIA-VDF-ENG002-CLS002 | — | F3 同名跨系統 VCGC,VDF; F3 同名 DataValidator 散在 2 模組 |
| VDF|CLS|VDF_ENG044_MDLXXXYFinanceGlobalDataFetcher|FileManager|v0000 | CLS | YELLOW | VIA-VDF-ENG002-CLS001 | — | F3 同名 FileManager 散在 2 模組 |
| VDF|CLS|VDF_ENG044_MDLXXXYFinanceGlobalDataFetcher|FinancialDataFetcher|v0000 | CLS | YELLOW | VIA-VDF-ENG002-CLS003 | — | F3 同名 FinancialDataFetcher 散在 2 模組 |
| VDF|CLS|VDF_MDL002_YFinanceFetchingEngine|DataValidator|v0000 | CLS | YELLOW | VIA-VDF-MDL126-CLS002 | — | F3 同名跨系統 VCGC,VDF; F3 同名 DataValidator 散在 2 模組;同名 DataValidator 散在 2 模組 |
| VDF|CLS|VDF_MDL002_YFinanceFetchingEngine|FileManager|v0000 | CLS | YELLOW | VIA-VDF-MDL126-CLS001 | — | F3 同名 FileManager 散在 2 模組;同名 FileManager 散在 2 模組 |
| VDF|CLS|VDF_MDL002_YFinanceFetchingEngine|FinancialDataFetcher|v0000 | CLS | YELLOW | VIA-VDF-MDL126-CLS004 | — | F3 同名 FinancialDataFetcher 散在 2 模組;同名 FinancialDataFetcher 散在 2 模組 |
| VDF|CLS|VDF_MDL003_SentimentMacroEngine|OutputManager|v0000 | CLS | YELLOW | VIA-VDF-MDL127-CLS005 | — | F3 同名 OutputManager 散在 3 模組;同名 OutputManager 散在 3 模組;同名 OutputManager 散在 3 模組 |
| VDF|CLS|VDF_MDL006_FinancialModel|OutputManager|v0100 | CLS | YELLOW | VIA-VDF-MDL159-CLS003 | — | F3 同名 OutputManager 散在 3 模組 |
| VDF|CLS|VDF_MDL012_FetchGroups|LayoutError|v0105 | CLS | YELLOW | VIA-VDF-MDL193-CLS001 | — | F3 同名跨系統 VCGC,VDF |
| VDF|CLS|VDF_MDL101_OutputManager|OutputManager|v0100R | CLS | YELLOW | VIA-VDF-MDL160-CLS001 | — | F3 同名 OutputManager 散在 3 模組;同名 OutputManager 散在 3 模組 |
| VRN|CLS|InvestmentRegexPattern_VALIDATED|ValidationResult|v0000 | CLS | YELLOW | VIA-VRN-MDL019-CLS009 | — | F3 同名 ValidationResult 散在 2 模組 |
| VRN|CLS|VIA_SummarizerEngine_2|ResourceSnapshot|v0000 | CLS | YELLOW | VIA-VRN-MDL043-CLS002 | — | F3 同名跨系統 VCGC,VRN |
| VRN|CLS|VIA_VRN_FirstPageEngine|Layout|v0000 | CLS | YELLOW | VIA-VRN-MDL150-CLS002 | — | F3 同名跨系統 VCGC,VRN |
| VRN|CLS|VIA_WebScraping_Compliance_syntaxfix|ComplianceFinding|v0100 | CLS | YELLOW | VIA-VRN-MDL220-CLS001 | — | F3 同名 ComplianceFinding 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VRN|CLS|VIA_WebScraping_Compliance|ComplianceFinding|v0101 | CLS | YELLOW | VIA-VRN-MDL221-CLS001 | — | F3 同名 ComplianceFinding 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VRN|CLS|VIA_WebScraping_DualEngine_Governance_Controller|Capability|v0000 | CLS | YELLOW | VIA-VRN-MDL222-CLS001 | — | F3 同名跨系統 VCGC,VRN |
| VRN|CLS|VRN_Complete_FeatureAudit_Ultra|ValidationResult|v0000 | CLS | YELLOW | VIA-VRN-MDL078-CLS004 | — | F3 同名 ValidationResult 散在 2 模組 |
| VRN|CLS|VRN_MDL002_LayoutExtractor|TextBlock|v0100 | CLS | YELLOW | VIA-VRN-MDL092-CLS002 | — | F3 同名跨系統 VCGC,VRN |
| VCGC|FNC|AdvancedNetworkDataFetcher_OPTIMIZED|OptimizedYFinanceFetcher.format_name|v0000 | FNC | YELLOW | VIA-SUP-MDL908-FNC017 | — | F3 同名 format_name 散在 2 模組 |
| VCGC|FNC|AdvancedNetworkDataFetcher_OPTIMIZED|SmartExchangeDetector.is_valid_tw_ticker|v0000 | FNC | YELLOW | VIA-SUP-MDL908-FNC026 | — | F3 同名 is_valid_tw_ticker 散在 3 模組 |
| VCGC|FNC|AdvancedNetworkDataFetcher_OPTIMIZED|SmartHTTPSession.get|v0000 | FNC | YELLOW | VIA-SUP-MDL908-FNC029 | — | F3 同名 get 散在 27 模組 |
| VCGC|FNC|AdvancedNetworkDataFetcher_OPTIMIZED|_via_net|v0000 | FNC | YELLOW | VIA-SUP-MDL908-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 28 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL001_CentralGovernanceEngine|_via_net|v0402 | FNC | YELLOW | VIA-VCGC-MDL006-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 28 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL001_CentralGovernanceEngine|add_synonym|v0402 | FNC | YELLOW | VIA-VCGC-MDL006-FNC022 | — | F3 同名 add_synonym 散在 3 模組 |
| VCGC|FNC|CGC_MDL001_CentralGovernanceEngine|append_ledger|v0402 | FNC | YELLOW | VIA-VCGC-MDL006-FNC014 | — | F3 同名 append_ledger 散在 2 模組 |
| VCGC|FNC|CGC_MDL001_CentralGovernanceEngine|family_of|v0402 | FNC | YELLOW | VIA-VCGC-MDL006-FNC027 | — | F3 同名 family_of 散在 3 模組 |
| VCGC|FNC|CGC_MDL001_CentralGovernanceEngine|harvest|v0402 | FNC | YELLOW | VIA-VCGC-MDL006-FNC017 | — | F3 同名跨系統 VCGC,VRN; F3 同名 harvest 散在 4 模組 |
| VCGC|FNC|CGC_MDL001_CentralGovernanceEngine|load_json|v0402 | FNC | YELLOW | VIA-VCGC-MDL006-FNC012 | — | F3 同名 load_json 散在 7 模組 |
| VCGC|FNC|CGC_MDL001_CentralGovernanceEngine|norm|v0402 | FNC | YELLOW | VIA-VCGC-MDL006-FNC002 | — | F3 同名跨系統 VCGC,VRN; F3 同名 norm 散在 7 模組 |
| VCGC|FNC|CGC_MDL001_CentralGovernanceEngine|normalize_temporal|v0402 | FNC | YELLOW | VIA-VCGC-MDL006-FNC032 | — | F3 同名 normalize_temporal 散在 2 模組 |
| VCGC|FNC|CGC_MDL001_CentralGovernanceEngine|now_iso|v0402 | FNC | YELLOW | VIA-VCGC-MDL006-FNC009 | — | F3 同名跨系統 VCGC,VRN; F3 同名 now_iso 散在 6 模組 |
| VCGC|FNC|CGC_MDL001_CentralGovernanceEngine|ratio|v0402 | FNC | YELLOW | VIA-VCGC-MDL006-FNC004 | — | F3 同名 ratio 散在 2 模組 |
| VCGC|FNC|CGC_MDL001_CentralGovernanceEngine|run_pipeline|v0402 | FNC | YELLOW | VIA-VCGC-MDL006-FNC042 | — | F3 同名跨系統 VCGC,VRN |
| VCGC|FNC|CGC_MDL001_CentralGovernanceEngine|save_json|v0402 | FNC | YELLOW | VIA-VCGC-MDL006-FNC013 | — | F3 同名 save_json 散在 3 模組 |
| VCGC|FNC|CGC_MDL001_CentralGovernanceEngine|write_html|v0402 | FNC | YELLOW | VIA-VCGC-MDL006-FNC045 | — | F3 同名跨系統 VCGC,VRN; F3 同名 write_html 散在 20 模組 |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_candidate_match|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC017 | — | F3 同名 def_candidate_match 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_classify_module|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC021 | — | F3 同名 def_classify_module 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_clean_text|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC007 | — | F3 同名跨系統 VCGC,VDF; F3 同名 def_clean_text 散在 24 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_completion_check|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC029 | — | F3 同名 def_completion_check 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_depth|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC016 | — | F3 同名 def_depth 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_enrich_inventory|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC022 | — | F3 同名 def_enrich_inventory 散在 2 模組 |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_ensure_dir|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC004 | — | F3 同名 def_ensure_dir 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_file_sha12|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC006 | — | F3 同名 def_file_sha12 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_html_escape|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC015 | — | F3 同名 def_html_escape 散在 7 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_log|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC002 | — | F3 同名跨系統 VCGC,VRN; F3 同名 def_log 散在 4 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_main|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC035 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 def_main 散在 77 模組 |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_make_alias|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC026 | — | F3 同名 def_make_alias 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_make_classes|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC024 | — | F3 同名 def_make_classes 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_make_counter|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC027 | — | F3 同名 def_make_counter 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_make_top10_libs|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC028 | — | F3 同名 def_make_top10_libs 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_normalize_duplicate_key|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC019 | — | F3 同名 def_normalize_duplicate_key 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_now_utc|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC001 | — | F3 同名 def_now_utc 散在 3 模組 |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_read_json|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC003 | — | F3 同名 def_read_json 散在 19 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_read_text_sniff|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC014 | — | F3 同名 def_read_text_sniff 散在 2 模組 |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_safe_filename|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC013 | — | F3 同名 def_safe_filename 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_safe_rel|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC012 | — | F3 同名 def_safe_rel 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_scan_files|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC018 | — | F3 同名 def_scan_files 散在 3 模組 |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_seed_master|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC025 | — | F3 同名 def_seed_master 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_sha12_text|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC005 | — | F3 同名 def_sha12_text 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_stage_files|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC023 | — | F3 同名 def_stage_files 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_status_counts|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC033 | — | F3 同名 def_status_counts 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_table_html|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC032 | — | F3 同名 def_table_html 散在 28 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_version_score|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC020 | — | F3 同名 def_version_score 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_write_df|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC030 | — | F3 同名 def_write_df 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_write_duckdb|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC031 | — | F3 同名 def_write_duckdb 散在 4 模組 |
| VCGC|FNC|CGC_MDL023_AutoCodeRegistryEngine|def_write_html|v0000 | FNC | YELLOW | VIA-VCGC-MDL042-FNC034 | — | F3 同名 def_write_html 散在 50 模組 |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|_via_net|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 28 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_align_wide|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC017 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_apply_transforms|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC018 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_audit_python_modules|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC008 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_effective_start|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC011 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_fetch_fred_api|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC014 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_fetch_fred_csv|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC015 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_fetch_fred_series|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC016 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_fetch_yfinance_series|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC013 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_flatten_manifest|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC010 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_import_pandas|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC004 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_import_requests|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC005 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_json_dump|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC002 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_load_manifest|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC009 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_main|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC022 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同 body 跨系統(候選共用 LIB); F3 同名 def_main 散在 77 模組 |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_main_fetch|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC021 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_module_available|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC006 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_package_check|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC007 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_sha256|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC003 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同 body 跨系統(候選共用 LIB); F3 同名 def_sha256 散在 5 模組 |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_start_minus_years|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC012 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_write_frame|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC019 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL028_ManifestFetchAdapter|def_write_long|v0000 | FNC | YELLOW | VIA-VCGC-MDL043-FNC020 | — | F3 同名跨系統 VCGC,VDF; F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL034_MDL015VrnFinalProductionLockRegistryV061573SUPPORTRULEV061573|def_clean|v0000 | FNC | YELLOW | VIA-VCGC-MDL044-FNC001 | — | F3 同名 def_clean 散在 13 模組;同 body 另見 8 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL034_MDL015VrnFinalProductionLockRegistryV061573SUPPORTRULEV061573|def_find_latest_dir|v0000 | FNC | YELLOW | VIA-VCGC-MDL044-FNC003 | — | F3 同名 def_find_latest_dir 散在 14 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL034_MDL015VrnFinalProductionLockRegistryV061573SUPPORTRULEV061573|def_html_table|v0000 | FNC | YELLOW | VIA-VCGC-MDL044-FNC009 | — | F3 同名 def_html_table 散在 12 模組 |
| VCGC|FNC|CGC_MDL034_MDL015VrnFinalProductionLockRegistryV061573SUPPORTRULEV061573|def_light|v0000 | FNC | YELLOW | VIA-VCGC-MDL044-FNC002 | — | F3 同名 def_light 散在 15 模組 |
| VCGC|FNC|CGC_MDL034_MDL015VrnFinalProductionLockRegistryV061573SUPPORTRULEV061573|def_main|v0000 | FNC | YELLOW | VIA-VCGC-MDL044-FNC012 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 def_main 散在 77 模組 |
| VCGC|FNC|CGC_MDL034_MDL015VrnFinalProductionLockRegistryV061573SUPPORTRULEV061573|def_read_json|v0000 | FNC | YELLOW | VIA-VCGC-MDL044-FNC005 | — | F3 同名 def_read_json 散在 19 模組;同 body 另見 7 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL034_MDL015VrnFinalProductionLockRegistryV061573SUPPORTRULEV061573|def_sha256_file|v0000 | FNC | YELLOW | VIA-VCGC-MDL044-FNC004 | — | F3 同名跨系統 VCGC,VRN; F3 同名 def_sha256_file 散在 5 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL034_MDL015VrnFinalProductionLockRegistryV061573SUPPORTRULEV061573|def_write_csv|v0000 | FNC | YELLOW | VIA-VCGC-MDL044-FNC007 | — | F3 同名 def_write_csv 散在 51 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL034_MDL015VrnFinalProductionLockRegistryV061573SUPPORTRULEV061573|def_write_html|v0000 | FNC | YELLOW | VIA-VCGC-MDL044-FNC010 | — | F3 同名 def_write_html 散在 50 模組 |
| VCGC|FNC|CGC_MDL034_MDL015VrnFinalProductionLockRegistryV061573SUPPORTRULEV061573|def_write_json|v0000 | FNC | YELLOW | VIA-VCGC-MDL044-FNC006 | — | F3 同名 def_write_json 散在 64 模組;同 body 另見 22 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL035_MDL256RestoreVisVrnMasterRegistryBridgeV0611ManifestGOVERNANCE|def_main|v0611 | FNC | YELLOW | VIA-VCGC-MDL045-FNC013 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 def_main 散在 77 模組 |
| VCGC|FNC|CGC_MDL035_MDL256RestoreVisVrnMasterRegistryBridgeV0611ManifestGOVERNANCE|def_normalize_header|v0611 | FNC | YELLOW | VIA-VCGC-MDL045-FNC010 | — | F3 同名 def_normalize_header 散在 3 模組 |
| VCGC|FNC|CGC_MDL035_MDL256RestoreVisVrnMasterRegistryBridgeV0611ManifestGOVERNANCE|def_scan_module|v0611 | FNC | YELLOW | VIA-VCGC-MDL045-FNC006 | — | F3 同名 def_scan_module 散在 3 模組 |
| VCGC|FNC|CGC_MDL035_MDL256RestoreVisVrnMasterRegistryBridgeV0611ManifestGOVERNANCE|def_sha256|v0611 | FNC | YELLOW | VIA-VCGC-MDL045-FNC002 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 def_sha256 散在 5 模組 |
| VCGC|FNC|CGC_MDL035_MDL256RestoreVisVrnMasterRegistryBridgeV0611ManifestGOVERNANCE|def_status_lights|v0611 | FNC | YELLOW | VIA-VCGC-MDL045-FNC001 | — | F3 同名 def_status_lights 散在 8 模組 |
| VCGC|FNC|CGC_MDL035_MDL256RestoreVisVrnMasterRegistryBridgeV0611ManifestGOVERNANCE|def_table_html|v0611 | FNC | YELLOW | VIA-VCGC-MDL045-FNC011 | — | F3 同名 def_table_html 散在 28 模組 |
| VCGC|FNC|CGC_MDL035_MDL256RestoreVisVrnMasterRegistryBridgeV0611ManifestGOVERNANCE|def_write_csv|v0611 | FNC | YELLOW | VIA-VCGC-MDL045-FNC003 | — | F3 同名 def_write_csv 散在 51 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL035_MDL256RestoreVisVrnMasterRegistryBridgeV0611ManifestGOVERNANCE|def_write_html|v0611 | FNC | YELLOW | VIA-VCGC-MDL045-FNC012 | — | F3 同名 def_write_html 散在 50 模組 |
| VCGC|FNC|CGC_MDL035_MDL256RestoreVisVrnMasterRegistryBridgeV0611ManifestGOVERNANCE|def_write_json|v0611 | FNC | YELLOW | VIA-VCGC-MDL045-FNC004 | — | F3 同名 def_write_json 散在 64 模組;同 body 另見 6 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL036_BuildPkgPointers|build|v0101 | FNC | YELLOW | VIA-VCGC-MDL047-FNC002 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL037_BuildSpecMaster|build|v0100 | FNC | YELLOW | VIA-VCGC-MDL048-FNC005 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL037_BuildSpecMaster|esc|v0100 | FNC | YELLOW | VIA-VCGC-MDL048-FNC001 | — | F3 同名 esc 散在 9 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL038_BuildSubsystemPages|build|v0103 | FNC | YELLOW | VIA-VCGC-MDL052-FNC002 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL039_BuildViaMother|build|v0106 | FNC | YELLOW | VIA-VCGC-MDL059-FNC003 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL039_BuildViaMother|esc|v0106 | FNC | YELLOW | VIA-VCGC-MDL059-FNC001 | — | F3 同名 esc 散在 9 模組;同 body 另見 2 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL041_ArticleIntake|export|v0100 | FNC | YELLOW | VIA-VCGC-MDL061-FNC007 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 export 散在 4 模組 |
| VCGC|FNC|CGC_MDL041_ArticleIntake|fetch_url|v0100 | FNC | YELLOW | VIA-VCGC-MDL061-FNC006 | — | F3 同名 fetch_url 散在 3 模組 |
| VCGC|FNC|CGC_MDL041_ArticleIntake|segment|v0100 | FNC | YELLOW | VIA-VCGC-MDL061-FNC005 | — | F3 同名跨系統 VCGC,VRN |
| VCGC|FNC|CGC_MDL043_AutocoderEngine|CentralRegistrationEngine.listing|v0100 | FNC | YELLOW | VIA-VCGC-MDL066-FNC005 | — | F3 同名 listing 散在 2 模組 |
| VCGC|FNC|CGC_MDL045_DedupIndex|cmd_build|v0000 | FNC | YELLOW | VIA-VCGC-MDL068-FNC003 | — | F3 同名跨系統 VCGC,VRN; F3 同名 cmd_build 散在 5 模組 |
| VCGC|FNC|CGC_MDL045_DedupIndex|cmd_check|v0000 | FNC | YELLOW | VIA-VCGC-MDL068-FNC005 | — | F3 同名跨系統 VCGC,VDF |
| VCGC|FNC|CGC_MDL045_DedupIndex|sha256_of|v0000 | FNC | YELLOW | VIA-VCGC-MDL068-FNC001 | — | F3 同名跨系統 VCGC,VRN; F3 同名 sha256_of 散在 3 模組 |
| VCGC|FNC|CGC_MDL046_DepSuper|_arg_after|v0101 | FNC | YELLOW | VIA-VCGC-MDL070-FNC032 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL046_DepSuper|_via_load|v0101 | FNC | YELLOW | VIA-VCGC-MDL070-FNC002 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL046_DepSuper|_via_net|v0101 | FNC | YELLOW | VIA-VCGC-MDL070-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 28 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL046_DepSuper|analyze|v0101 | FNC | YELLOW | VIA-VCGC-MDL070-FNC015 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 analyze 散在 5 模組 |
| VCGC|FNC|CGC_MDL046_DepSuper|canon|v0101 | FNC | YELLOW | VIA-VCGC-MDL070-FNC004 | — | F3 同名 canon 散在 4 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL046_DepSuper|cmd_selftest|v0101 | FNC | YELLOW | VIA-VCGC-MDL070-FNC031 | — | F3 同名 cmd_selftest 散在 4 模組 |
| VCGC|FNC|CGC_MDL046_DepSuper|cmd_tree|v0101 | FNC | YELLOW | VIA-VCGC-MDL070-FNC025 | — | F3 同名跨系統 VCGC,VRN |
| VCGC|FNC|CGC_MDL047_DownloadsOrganizer|build_repo_index|v0100 | FNC | YELLOW | VIA-VCGC-MDL071-FNC002 | — | F3 同名 build_repo_index 散在 2 模組 |
| VCGC|FNC|CGC_MDL047_DownloadsOrganizer|classify|v0100 | FNC | YELLOW | VIA-VCGC-MDL071-FNC003 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 classify 散在 20 模組 |
| VCGC|FNC|CGC_MDL047_DownloadsOrganizer|h12|v0100 | FNC | YELLOW | VIA-VCGC-MDL071-FNC001 | — | F3 同名 h12 散在 2 模組 |
| VCGC|FNC|CGC_MDL048_DownloadsRegisterAllCrossAnalysisBuilderV20260702|classify|v0000 | FNC | YELLOW | VIA-VCGC-MDL072-FNC001 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 classify 散在 20 模組 |
| VCGC|FNC|CGC_MDL048_DownloadsRegisterAllCrossAnalysisBuilderV20260702|sha256_file|v0000 | FNC | YELLOW | VIA-VCGC-MDL072-FNC002 | — | F3 同名跨系統 VCGC,VRN; F3 同名 sha256_file 散在 16 模組 |
| VCGC|FNC|CGC_MDL048_DownloadsRegisterAllCrossAnalysisBuilderV20260702|write_html|v0000 | FNC | YELLOW | VIA-VCGC-MDL072-FNC004 | — | F3 同名跨系統 VCGC,VRN; F3 同名 write_html 散在 20 模組 |
| VCGC|FNC|CGC_MDL049_EnvPlan|_consent|v0103 | FNC | YELLOW | VIA-VCGC-MDL076-FNC002 | — | F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL049_EnvPlan|_via_load|v0103 | FNC | YELLOW | VIA-VCGC-MDL076-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL049_EnvPlan|dryrun_stage|v0103 | FNC | YELLOW | VIA-VCGC-MDL076-FNC005 | — | F3 同名 dryrun_stage 散在 2 模組 |
| VCGC|FNC|CGC_MDL049_EnvPlan|snapshot|v0103 | FNC | YELLOW | VIA-VCGC-MDL076-FNC004 | — | F3 同名 snapshot 散在 6 模組 |
| VCGC|FNC|CGC_MDL050_EnvRebuild|_arg_after|v0109 | FNC | YELLOW | VIA-VCGC-MDL086-FNC034 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL050_EnvRebuild|canon|v0109 | FNC | YELLOW | VIA-VCGC-MDL086-FNC002 | — | F3 同名 canon 散在 4 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL050_EnvRebuild|cmd_selftest|v0109 | FNC | YELLOW | VIA-VCGC-MDL086-FNC033 | — | F3 同名 cmd_selftest 散在 4 模組 |
| VCGC|FNC|CGC_MDL050_EnvRebuild|discover_envs|v0109 | FNC | YELLOW | VIA-VCGC-MDL086-FNC009 | — | F3 同名 discover_envs 散在 2 模組 |
| VCGC|FNC|CGC_MDL050_EnvRebuild|dryrun_stage|v0109 | FNC | YELLOW | VIA-VCGC-MDL086-FNC029 | — | F3 同名 dryrun_stage 散在 2 模組 |
| VCGC|FNC|CGC_MDL050_EnvRebuild|scan_env|v0109 | FNC | YELLOW | VIA-VCGC-MDL086-FNC011 | — | F3 同名 scan_env 散在 2 模組 |
| VCGC|FNC|CGC_MDL053_GovernanceConsole|check|v0100 | FNC | YELLOW | VIA-VCGC-MDL091-FNC001 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL054_IfaceContract|_arg|v0103 | FNC | YELLOW | VIA-VCGC-MDL095-FNC017 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL054_IfaceContract|do_status|v0103 | FNC | YELLOW | VIA-VCGC-MDL095-FNC016 | — | F3 同名 do_status 散在 2 模組 |
| VCGC|FNC|CGC_MDL054_IfaceContract|load_spec|v0103 | FNC | YELLOW | VIA-VCGC-MDL095-FNC006 | — | F3 同名 load_spec 散在 4 模組 |
| VCGC|FNC|CGC_MDL056_InstallGate|machine_hash|v0104 | FNC | YELLOW | VIA-VCGC-MDL102-FNC001 | — | F3 同名 machine_hash 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL056_InstallGate|pip_check|v0104 | FNC | YELLOW | VIA-VCGC-MDL102-FNC003 | — | F3 同名 pip_check 散在 2 模組 |
| VCGC|FNC|CGC_MDL057_Intake|classify|v0101 | FNC | YELLOW | VIA-VCGC-MDL104-FNC004 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 classify 散在 20 模組 |
| VCGC|FNC|CGC_MDL057_Intake|h12|v0101 | FNC | YELLOW | VIA-VCGC-MDL104-FNC001 | — | F3 同名 h12 散在 2 模組 |
| VCGC|FNC|CGC_MDL057_Intake|load_reg|v0101 | FNC | YELLOW | VIA-VCGC-MDL104-FNC006 | — | F3 同名 load_reg 散在 5 模組 |
| VCGC|FNC|CGC_MDL058_Lessons|__getattr__|v0103 | FNC | YELLOW | VIA-VCGC-MDL1537-FNC002 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 13 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL058_Lessons|_vnum|v0103 | FNC | YELLOW | VIA-VCGC-MDL1537-FNC001 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL058_Lessons|load_ledger|v0103 | FNC | YELLOW | VIA-VCGC-MDL1537-FNC005 | — | F3 同名 load_ledger 散在 2 模組 |
| VCGC|FNC|CGC_MDL059_MasterHub|build_ssot|v0108 | FNC | YELLOW | VIA-VCGC-MDL115-FNC004 | — | F3 同名跨系統 VCGC,VRN |
| VCGC|FNC|CGC_MDL060_NumberEngine|load|v0100 | FNC | YELLOW | VIA-VCGC-MDL116-FNC001 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL062_Provision|machine_hash|v0102 | FNC | YELLOW | VIA-VCGC-MDL120-FNC001 | — | F3 同名 machine_hash 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL064_SelftestGrid|battery|v0504 | FNC | YELLOW | VIA-VCGC-MDL1438-FNC007 | — | F3 同名 battery 散在 2 模組 |
| VCGC|FNC|CGC_MDL064_SelftestGrid|run_one|v0504 | FNC | YELLOW | VIA-VCGC-MDL1438-FNC026 | — | F3 同名跨系統 VCGC,VDF; F3 同名 run_one 散在 3 模組 |
| VCGC|FNC|CGC_MDL065_SsotEvolve|harvest|v0100 | FNC | YELLOW | VIA-VCGC-MDL520-FNC002 | — | F3 同名跨系統 VCGC,VRN; F3 同名 harvest 散在 4 模組 |
| VCGC|FNC|CGC_MDL066_StructureForge|StructureForge.forge|v0000 | FNC | YELLOW | VIA-VCGC-MDL521-FNC016 | — | F3 同名 forge 散在 2 模組 |
| VCGC|FNC|CGC_MDL066_StructureForge|banner|v0000 | FNC | YELLOW | VIA-VCGC-MDL521-FNC003 | — | F3 同名 banner 散在 3 模組 |
| VCGC|FNC|CGC_MDL067_SupportBridgeInject|inject|v0101 | FNC | YELLOW | VIA-VCGC-MDL523-FNC002 | — | F3 同名跨系統 VCGC,VRN; F3 同名 inject 散在 4 模組 |
| VCGC|FNC|CGC_MDL070_T0Audit|sha256|v0100 | FNC | YELLOW | VIA-VCGC-MDL540-FNC002 | — | F3 同名 sha256 散在 5 模組 |
| VCGC|FNC|CGC_MDL071_Namereg|assign|v0102 | FNC | YELLOW | VIA-VCGC-MDL543-FNC005 | — | F3 同名 assign 散在 3 模組 |
| VCGC|FNC|CGC_MDL071_Namereg|family_key|v0102 | FNC | YELLOW | VIA-VCGC-MDL543-FNC001 | — | F3 同名 family_key 散在 2 模組 |
| VCGC|FNC|CGC_MDL071_Namereg|kind_of|v0102 | FNC | YELLOW | VIA-VCGC-MDL543-FNC004 | — | F3 同名跨系統 VCGC,VRN |
| VCGC|FNC|CGC_MDL071_Namereg|write_ui|v0102 | FNC | YELLOW | VIA-VCGC-MDL543-FNC006 | — | F3 同名 write_ui 散在 2 模組 |
| VCGC|FNC|CGC_MDL072_ProductUi|build|v0100 | FNC | YELLOW | VIA-VCGC-MDL544-FNC009 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL073_EngineCatalog|build|v0100 | FNC | YELLOW | VIA-VCGC-MDL545-FNC001 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL073_EngineCatalog|write_ui|v0100 | FNC | YELLOW | VIA-VCGC-MDL545-FNC003 | — | F3 同名 write_ui 散在 2 模組 |
| VCGC|FNC|CGC_MDL075_CentralGov|_log|v0106 | FNC | YELLOW | VIA-VCGC-MDL553-FNC001 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL075_CentralGov|build_ui|v0106 | FNC | YELLOW | VIA-VCGC-MDL553-FNC015 | — | F3 同名 build_ui 散在 4 模組 |
| VCGC|FNC|CGC_MDL075_CentralGov|classify|v0106 | FNC | YELLOW | VIA-VCGC-MDL553-FNC009 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 classify 散在 20 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL075_CentralGov|cmd_regex|v0106 | FNC | YELLOW | VIA-VCGC-MDL553-FNC019 | — | F3 同名 cmd_regex 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL075_CentralGov|cmd_run|v0106 | FNC | YELLOW | VIA-VCGC-MDL553-FNC017 | — | F3 同名 cmd_run 散在 3 模組 |
| VCGC|FNC|CGC_MDL075_CentralGov|cmd_ssot|v0106 | FNC | YELLOW | VIA-VCGC-MDL553-FNC018 | — | F3 同名 cmd_ssot 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL075_CentralGov|is_archive|v0106 | FNC | YELLOW | VIA-VCGC-MDL553-FNC007 | — | F3 同名 is_archive 散在 2 模組 |
| VCGC|FNC|CGC_MDL075_CentralGov|iter_py|v0106 | FNC | YELLOW | VIA-VCGC-MDL553-FNC008 | — | F3 同名 iter_py 散在 3 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL075_CentralGov|main|v0106 | FNC | YELLOW | VIA-VCGC-MDL553-FNC021 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL075_CentralGov|round1_scan|v0106 | FNC | YELLOW | VIA-VCGC-MDL553-FNC010 | — | F3 同名 round1_scan 散在 2 模組 |
| VCGC|FNC|CGC_MDL075_CentralGov|round2_ssot_hydra|v0106 | FNC | YELLOW | VIA-VCGC-MDL553-FNC011 | — | F3 同名 round2_ssot_hydra 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL075_CentralGov|round3_polish|v0106 | FNC | YELLOW | VIA-VCGC-MDL553-FNC012 | — | F3 同名 round3_polish 散在 2 模組 |
| VCGC|FNC|CGC_MDL076_SyntaxRescue|cmd_scan|v0102 | FNC | YELLOW | VIA-VCGC-MDL556-FNC010 | — | F3 同名 cmd_scan 散在 2 模組 |
| VCGC|FNC|CGC_MDL077_RenameEngine|build_ref_index|v0100 | FNC | YELLOW | VIA-VCGC-MDL557-FNC004 | — | F3 同名 build_ref_index 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL077_RenameEngine|cmd_commit|v0100 | FNC | YELLOW | VIA-VCGC-MDL557-FNC010 | — | F3 同名 cmd_commit 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL077_RenameEngine|cmd_plan|v0100 | FNC | YELLOW | VIA-VCGC-MDL557-FNC009 | — | F3 同名 cmd_plan 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL077_RenameEngine|cmd_undo|v0100 | FNC | YELLOW | VIA-VCGC-MDL557-FNC011 | — | F3 同名 cmd_undo 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL077_RenameEngine|commit|v0100 | FNC | YELLOW | VIA-VCGC-MDL557-FNC007 | — | F3 同名 commit 散在 7 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL077_RenameEngine|load_reg|v0100 | FNC | YELLOW | VIA-VCGC-MDL557-FNC001 | — | F3 同名 load_reg 散在 5 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL077_RenameEngine|migrate_reg_key|v0100 | FNC | YELLOW | VIA-VCGC-MDL557-FNC006 | — | F3 同名 migrate_reg_key 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL077_RenameEngine|plan|v0100 | FNC | YELLOW | VIA-VCGC-MDL557-FNC005 | — | F3 同名跨系統 VCGC,VDF; F3 同名 plan 散在 19 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL077_RenameEngine|save_reg|v0100 | FNC | YELLOW | VIA-VCGC-MDL557-FNC002 | — | F3 同名 save_reg 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL077_RenameEngine|strip_ver|v0100 | FNC | YELLOW | VIA-VCGC-MDL557-FNC003 | — | F3 同名 strip_ver 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL077_RenameEngine|undo|v0100 | FNC | YELLOW | VIA-VCGC-MDL557-FNC008 | — | F3 同名 undo 散在 6 模組 |
| VCGC|FNC|CGC_MDL078_TreeAtlas|_run|v0100 | FNC | YELLOW | VIA-VCGC-MDL558-FNC008 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL078_TreeAtlas|active_items|v0100 | FNC | YELLOW | VIA-VCGC-MDL558-FNC004 | — | F3 同名 active_items 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL078_TreeAtlas|build_tree_html|v0100 | FNC | YELLOW | VIA-VCGC-MDL558-FNC005 | — | F3 同名 build_tree_html 散在 2 模組 |
| VCGC|FNC|CGC_MDL078_TreeAtlas|cmd_build|v0100 | FNC | YELLOW | VIA-VCGC-MDL558-FNC006 | — | F3 同名跨系統 VCGC,VRN; F3 同名 cmd_build 散在 5 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL078_TreeAtlas|cmd_env|v0100 | FNC | YELLOW | VIA-VCGC-MDL558-FNC007 | — | F3 同名 cmd_env 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL078_TreeAtlas|cmd_ladder|v0100 | FNC | YELLOW | VIA-VCGC-MDL558-FNC009 | — | F3 同名 cmd_ladder 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL078_TreeAtlas|env_matrix|v0100 | FNC | YELLOW | VIA-VCGC-MDL558-FNC003 | — | F3 同名 env_matrix 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL078_TreeAtlas|load_reg|v0100 | FNC | YELLOW | VIA-VCGC-MDL558-FNC001 | — | F3 同名 load_reg 散在 5 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL078_TreeAtlas|main|v0100 | FNC | YELLOW | VIA-VCGC-MDL558-FNC011 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL078_TreeAtlas|probe_lib|v0100 | FNC | YELLOW | VIA-VCGC-MDL558-FNC002 | — | F3 同名 probe_lib 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL078_TreeAtlas|selftest|v0100 | FNC | YELLOW | VIA-VCGC-MDL558-FNC010 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL079_MatrixConsole|build_html|v0100 | FNC | YELLOW | VIA-VCGC-MDL559-FNC005 | — | F3 同名 build_html 散在 5 模組 |
| VCGC|FNC|CGC_MDL079_MatrixConsole|chart_svg|v0100 | FNC | YELLOW | VIA-VCGC-MDL559-FNC004 | — | F3 同名 chart_svg 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL079_MatrixConsole|cmd_build|v0100 | FNC | YELLOW | VIA-VCGC-MDL559-FNC006 | — | F3 同名跨系統 VCGC,VRN; F3 同名 cmd_build 散在 5 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL079_MatrixConsole|extract_cols|v0100 | FNC | YELLOW | VIA-VCGC-MDL559-FNC001 | — | F3 同名 extract_cols 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL079_MatrixConsole|lex_groups|v0100 | FNC | YELLOW | VIA-VCGC-MDL559-FNC003 | — | F3 同名 lex_groups 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL079_MatrixConsole|main|v0100 | FNC | YELLOW | VIA-VCGC-MDL559-FNC008 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL079_MatrixConsole|scan_verified|v0100 | FNC | YELLOW | VIA-VCGC-MDL559-FNC002 | — | F3 同名 scan_verified 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL079_MatrixConsole|selftest|v0100 | FNC | YELLOW | VIA-VCGC-MDL559-FNC007 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL080_Wrapup|sha256|v0101 | FNC | YELLOW | VIA-VCGC-MDL561-FNC001 | — | F3 同名 sha256 散在 5 模組 |
| VCGC|FNC|CGC_MDL081_SubsystemManagerV2|adjudicate|v0101 | FNC | YELLOW | VIA-VCGC-MDL563-FNC003 | — | F3 同名 adjudicate 散在 2 模組 |
| VCGC|FNC|CGC_MDL083_CentralGovernment|run_audit|v0100 | FNC | YELLOW | VIA-VCGC-MDL566-FNC003 | — | F3 同名跨系統 VCGC,VRN |
| VCGC|FNC|CGC_MDL087_TestPyramid|_via_net|v0101 | FNC | YELLOW | VIA-VCGC-MDL571-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 28 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL087_TestPyramid|build_ui|v0101 | FNC | YELLOW | VIA-VCGC-MDL571-FNC006 | — | F3 同名 build_ui 散在 4 模組 |
| VCGC|FNC|CGC_MDL088_SystemTestPages|assemble|v0104 | FNC | YELLOW | VIA-VCGC-MDL576-FNC004 | — | F3 同名 assemble 散在 2 模組 |
| VCGC|FNC|CGC_MDL088_SystemTestPages|build_ui|v0104 | FNC | YELLOW | VIA-VCGC-MDL576-FNC012 | — | F3 同名 build_ui 散在 4 模組 |
| VCGC|FNC|CGC_MDL088_SystemTestPages|classify|v0104 | FNC | YELLOW | VIA-VCGC-MDL576-FNC001 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 classify 散在 20 模組 |
| VCGC|FNC|CGC_MDL088_SystemTestPages|status|v0104 | FNC | YELLOW | VIA-VCGC-MDL576-FNC014 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 status 散在 26 模組 |
| VCGC|FNC|CGC_MDL089_UIBaseTemplate|__getattr__|v0101 | FNC | YELLOW | VIA-VCGC-MDL1397-FNC003 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 13 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL089_UIBaseTemplate|_via_net|v0101 | FNC | YELLOW | VIA-VCGC-MDL1397-FNC006 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 15 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL089_UIBaseTemplate|_vnum|v0101 | FNC | YELLOW | VIA-VCGC-MDL1397-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 12 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL089_UIBaseTemplate|main|v0101 | FNC | YELLOW | VIA-VCGC-MDL1397-FNC005 | — | F3 同 body 另見 2 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL089_UIBaseTemplate|ssot_tail|v0101 | FNC | YELLOW | VIA-VCGC-MDL1397-FNC002 | — | F3 同名 ssot_tail 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL090_SystemHub|build|v0102 | FNC | YELLOW | VIA-VCGC-MDL580-FNC004 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL090_SystemHub|harvest|v0102 | FNC | YELLOW | VIA-VCGC-MDL580-FNC002 | — | F3 同名跨系統 VCGC,VRN; F3 同名 harvest 散在 4 模組 |
| VCGC|FNC|CGC_MDL090_SystemHub|render|v0102 | FNC | YELLOW | VIA-VCGC-MDL580-FNC003 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL091_CharterAudit|audit|v0101 | FNC | YELLOW | VIA-VCGC-MDL582-FNC004 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 audit 散在 11 模組 |
| VCGC|FNC|CGC_MDL091_CharterAudit|build|v0101 | FNC | YELLOW | VIA-VCGC-MDL582-FNC006 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL093_GovernanceMatrix|build|v0100 | FNC | YELLOW | VIA-VCGC-MDL594-FNC005 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL093_GovernanceMatrix|harvest|v0100 | FNC | YELLOW | VIA-VCGC-MDL594-FNC002 | — | F3 同名跨系統 VCGC,VRN; F3 同名 harvest 散在 4 模組 |
| VCGC|FNC|CGC_MDL093_GovernanceMatrix|render|v0100 | FNC | YELLOW | VIA-VCGC-MDL594-FNC004 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL094_CommandDeck|build|v0101 | FNC | YELLOW | VIA-VCGC-MDL596-FNC003 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL094_CommandDeck|render|v0101 | FNC | YELLOW | VIA-VCGC-MDL596-FNC002 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL095_DeckServer|H.do_GET|v0161 | FNC | YELLOW | VIA-VCGC-MDL1494-FNC057 | — | F3 同名 do_GET 散在 5 模組 |
| VCGC|FNC|CGC_MDL095_DeckServer|H.do_POST|v0161 | FNC | YELLOW | VIA-VCGC-MDL1494-FNC059 | — | F3 同名 do_POST 散在 5 模組 |
| VCGC|FNC|CGC_MDL095_DeckServer|H.log_message|v0161 | FNC | YELLOW | VIA-VCGC-MDL1494-FNC060 | — | F3 同名 log_message 散在 3 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL095_DeckServer|console_mod|v0161 | FNC | YELLOW | VIA-VCGC-MDL1494-FNC018 | — | F3 同名 console_mod 散在 2 模組 |
| VCGC|FNC|CGC_MDL095_DeckServer|serve|v0161 | FNC | YELLOW | VIA-VCGC-MDL1494-FNC044 | — | F3 同名 serve 散在 3 模組 |
| VCGC|FNC|CGC_MDL095_DeckServer|start_task|v0161 | FNC | YELLOW | VIA-VCGC-MDL1494-FNC014 | — | F3 同名 start_task 散在 2 模組 |
| VCGC|FNC|CGC_MDL096_SyncStatus|render|v0110 | FNC | YELLOW | VIA-VCGC-MDL668-FNC009 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL097_PortalUI|render|v0100 | FNC | YELLOW | VIA-VCGC-MDL669-FNC002 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL098_DataCatalog|catalog|v0103 | FNC | YELLOW | VIA-VCGC-MDL673-FNC001 | — | F3 同名跨系統 VCGC,VRN; F3 同名 catalog 散在 3 模組 |
| VCGC|FNC|CGC_MDL098_DataCatalog|render|v0103 | FNC | YELLOW | VIA-VCGC-MDL673-FNC002 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL099_GlobalMarkets|gather|v0101 | FNC | YELLOW | VIA-VCGC-MDL675-FNC002 | — | F3 同名跨系統 VCGC,VRN; F3 同名 gather 散在 10 模組 |
| VCGC|FNC|CGC_MDL099_GlobalMarkets|render|v0101 | FNC | YELLOW | VIA-VCGC-MDL675-FNC003 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL100_ReportCards|gather|v0100 | FNC | YELLOW | VIA-VCGC-MDL676-FNC001 | — | F3 同名跨系統 VCGC,VRN; F3 同名 gather 散在 10 模組 |
| VCGC|FNC|CGC_MDL100_ReportCards|render|v0100 | FNC | YELLOW | VIA-VCGC-MDL676-FNC002 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL101_PSAstRepair|inventory|v0100 | FNC | YELLOW | VIA-VCGC-MDL677-FNC002 | — | F3 同名跨系統 VCGC,VDF; F3 同名 inventory 散在 4 模組 |
| VCGC|FNC|CGC_MDL101_PSAstRepair|render|v0100 | FNC | YELLOW | VIA-VCGC-MDL677-FNC008 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL101_PSAstRepair|scan|v0100 | FNC | YELLOW | VIA-VCGC-MDL677-FNC006 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL101_PSAstRepair|zone_of|v0100 | FNC | YELLOW | VIA-VCGC-MDL677-FNC003 | — | F3 同名 zone_of 散在 4 模組 |
| VCGC|FNC|CGC_MDL102_CommandRoster|gather|v0101 | FNC | YELLOW | VIA-VCGC-MDL679-FNC004 | — | F3 同名跨系統 VCGC,VRN; F3 同名 gather 散在 10 模組 |
| VCGC|FNC|CGC_MDL102_CommandRoster|render|v0101 | FNC | YELLOW | VIA-VCGC-MDL679-FNC005 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL103_AccelCoverage|inject|v0101 | FNC | YELLOW | VIA-VCGC-MDL681-FNC007 | — | F3 同名跨系統 VCGC,VRN; F3 同名 inject 散在 4 模組 |
| VCGC|FNC|CGC_MDL103_AccelCoverage|scan|v0101 | FNC | YELLOW | VIA-VCGC-MDL681-FNC002 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL104_TestResultsHub|gather|v0103 | FNC | YELLOW | VIA-VCGC-MDL685-FNC002 | — | F3 同名跨系統 VCGC,VRN; F3 同名 gather 散在 10 模組 |
| VCGC|FNC|CGC_MDL104_TestResultsHub|render|v0103 | FNC | YELLOW | VIA-VCGC-MDL685-FNC004 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL105_GovernanceConsole|gates|v0125 | FNC | YELLOW | VIA-VCGC-MDL711-FNC002 | — | F3 同名 gates 散在 4 模組 |
| VCGC|FNC|CGC_MDL105_GovernanceConsole|page_families|v0125 | FNC | YELLOW | VIA-VCGC-MDL711-FNC001 | — | F3 同名 page_families 散在 2 模組 |
| VCGC|FNC|CGC_MDL105_GovernanceConsole|render|v0125 | FNC | YELLOW | VIA-VCGC-MDL711-FNC003 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL106_GovConsole|banner|v0101 | FNC | YELLOW | VIA-VCGC-MDL713-FNC001 | — | F3 同名 banner 散在 3 模組 |
| VCGC|FNC|CGC_MDL106_GovConsole|classify_ps|v0101 | FNC | YELLOW | VIA-VCGC-MDL713-FNC011 | — | F3 同名 classify_ps 散在 2 模組 |
| VCGC|FNC|CGC_MDL106_GovConsole|inventory|v0101 | FNC | YELLOW | VIA-VCGC-MDL713-FNC004 | — | F3 同名跨系統 VCGC,VDF; F3 同名 inventory 散在 4 模組 |
| VCGC|FNC|CGC_MDL106_GovConsole|zone_of|v0101 | FNC | YELLOW | VIA-VCGC-MDL713-FNC003 | — | F3 同名 zone_of 散在 4 模組 |
| VCGC|FNC|CGC_MDL107_UISpecManager|__getattr__|v0101 | FNC | YELLOW | VIA-VCGC-MDL1398-FNC003 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 13 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL107_UISpecManager|_via_net|v0101 | FNC | YELLOW | VIA-VCGC-MDL1398-FNC006 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 15 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL107_UISpecManager|_vnum|v0101 | FNC | YELLOW | VIA-VCGC-MDL1398-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 12 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL107_UISpecManager|main|v0101 | FNC | YELLOW | VIA-VCGC-MDL1398-FNC005 | — | F3 同 body 另見 2 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL107_UISpecManager|ssot_tail|v0101 | FNC | YELLOW | VIA-VCGC-MDL1398-FNC002 | — | F3 同名 ssot_tail 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL108_ChatToDoc|banner|v0100 | FNC | YELLOW | VIA-VCGC-MDL715-FNC001 | — | F3 同名 banner 散在 3 模組 |
| VCGC|FNC|CGC_MDL108_ChatToDoc|extract_code|v0100 | FNC | YELLOW | VIA-VCGC-MDL715-FNC005 | — | F3 同名 extract_code 散在 2 模組 |
| VCGC|FNC|CGC_MDL109_PromptManager|add|v0100 | FNC | YELLOW | VIA-VCGC-MDL716-FNC003 | — | F3 同名 add 散在 19 模組 |
| VCGC|FNC|CGC_MDL109_PromptManager|render|v0100 | FNC | YELLOW | VIA-VCGC-MDL716-FNC004 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL110_TriTestMatrix|gather|v0100 | FNC | YELLOW | VIA-VCGC-MDL717-FNC003 | — | F3 同名跨系統 VCGC,VRN; F3 同名 gather 散在 10 模組 |
| VCGC|FNC|CGC_MDL110_TriTestMatrix|render|v0100 | FNC | YELLOW | VIA-VCGC-MDL717-FNC005 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL111_UIComponentRoster|_mod|v0100 | FNC | YELLOW | VIA-VCGC-MDL718-FNC001 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL111_UIComponentRoster|gather|v0100 | FNC | YELLOW | VIA-VCGC-MDL718-FNC002 | — | F3 同名跨系統 VCGC,VRN; F3 同名 gather 散在 10 模組 |
| VCGC|FNC|CGC_MDL111_UIComponentRoster|render|v0100 | FNC | YELLOW | VIA-VCGC-MDL718-FNC003 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL112_SystemAtlas|gather|v0100 | FNC | YELLOW | VIA-VCGC-MDL719-FNC002 | — | F3 同名跨系統 VCGC,VRN; F3 同名 gather 散在 10 模組 |
| VCGC|FNC|CGC_MDL112_SystemAtlas|render|v0100 | FNC | YELLOW | VIA-VCGC-MDL719-FNC003 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL113_UnifiedRegistry|assign|v0100 | FNC | YELLOW | VIA-VCGC-MDL720-FNC004 | — | F3 同名 assign 散在 3 模組 |
| VCGC|FNC|CGC_MDL113_UnifiedRegistry|collect|v0100 | FNC | YELLOW | VIA-VCGC-MDL720-FNC003 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 collect 散在 13 模組 |
| VCGC|FNC|CGC_MDL113_UnifiedRegistry|render|v0100 | FNC | YELLOW | VIA-VCGC-MDL720-FNC005 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL114_CommandCenterBridge|probe|v0100 | FNC | YELLOW | VIA-VCGC-MDL721-FNC002 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 probe 散在 8 模組 |
| VCGC|FNC|CGC_MDL114_CommandCenterBridge|register_merge|v0100 | FNC | YELLOW | VIA-VCGC-MDL721-FNC005 | — | F3 同名跨系統 VCGC,VRN |
| VCGC|FNC|CGC_MDL114_CommandCenterBridge|render|v0100 | FNC | YELLOW | VIA-VCGC-MDL721-FNC004 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL115_SSOTRegexDict|render|v0101 | FNC | YELLOW | VIA-VCGC-MDL723-FNC005 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL115_SSOTRegexDict|scan|v0101 | FNC | YELLOW | VIA-VCGC-MDL723-FNC004 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL116_UnifiedShell|_mod|v0114 | FNC | YELLOW | VIA-VCGC-MDL738-FNC003 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL116_UnifiedShell|_type_scale|v0114 | FNC | YELLOW | VIA-VCGC-MDL738-FNC001 | — | F3 同 body 另見 2 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL116_UnifiedShell|apply_type_scale|v0114 | FNC | YELLOW | VIA-VCGC-MDL738-FNC002 | — | F3 同名 apply_type_scale 散在 3 模組;同 body 另見 2 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL116_UnifiedShell|gather|v0114 | FNC | YELLOW | VIA-VCGC-MDL738-FNC018 | — | F3 同名跨系統 VCGC,VRN; F3 同名 gather 散在 10 模組 |
| VCGC|FNC|CGC_MDL116_UnifiedShell|page_families|v0114 | FNC | YELLOW | VIA-VCGC-MDL738-FNC004 | — | F3 同名 page_families 散在 2 模組 |
| VCGC|FNC|CGC_MDL117_AccelCoverage|scan|v0101 | FNC | YELLOW | VIA-VCGC-MDL740-FNC003 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL118_PlotDataLaw|audit|v0102 | FNC | YELLOW | VIA-VCGC-MDL743-FNC009 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 audit 散在 11 模組 |
| VCGC|FNC|CGC_MDL119_SystemAPI|home|v0106 | FNC | YELLOW | VIA-VCGC-MDL750-FNC009 | — | F3 同名 home 散在 2 模組 |
| VCGC|FNC|CGC_MDL119_SystemAPI|revenue|v0106 | FNC | YELLOW | VIA-VCGC-MDL750-FNC016 | — | F3 同名跨系統 VCGC,VDF |
| VCGC|FNC|CGC_MDL120_SystemUI|build|v0107 | FNC | YELLOW | VIA-VCGC-MDL758-FNC004 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL121_CompletionAutomator|plan|v0105 | FNC | YELLOW | VIA-VCGC-MDL764-FNC004 | — | F3 同名跨系統 VCGC,VDF; F3 同名 plan 散在 19 模組 |
| VCGC|FNC|CGC_MDL122_IntakeRoster|render|v0113 | FNC | YELLOW | VIA-VCGC-MDL778-FNC005 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL122_IntakeRoster|roster|v0113 | FNC | YELLOW | VIA-VCGC-MDL778-FNC004 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 roster 散在 5 模組 |
| VCGC|FNC|CGC_MDL123_DataHome|_is_sandbox|v0106 | FNC | YELLOW | VIA-VCGC-MDL785-FNC008 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL123_DataHome|_sha|v0106 | FNC | YELLOW | VIA-VCGC-MDL785-FNC012 | — | F3 同 body 另見 2 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL123_DataHome|catalog|v0106 | FNC | YELLOW | VIA-VCGC-MDL785-FNC021 | — | F3 同名跨系統 VCGC,VRN; F3 同名 catalog 散在 3 模組 |
| VCGC|FNC|CGC_MDL123_DataHome|find|v0106 | FNC | YELLOW | VIA-VCGC-MDL785-FNC016 | — | F3 同名 find 散在 3 模組 |
| VCGC|FNC|CGC_MDL123_DataHome|link|v0106 | FNC | YELLOW | VIA-VCGC-MDL785-FNC018 | — | F3 同名 link 散在 3 模組 |
| VCGC|FNC|CGC_MDL123_DataHome|plan|v0106 | FNC | YELLOW | VIA-VCGC-MDL785-FNC022 | — | F3 同名跨系統 VCGC,VDF; F3 同名 plan 散在 19 模組 |
| VCGC|FNC|CGC_MDL123_DataHome|status|v0106 | FNC | YELLOW | VIA-VCGC-MDL785-FNC015 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 status 散在 26 模組 |
| VCGC|FNC|CGC_MDL124_BridgeSweeper|main|v0110 | FNC | YELLOW | VIA-VCGC-MDL1559-FNC004 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 4 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL125_FixAll|plan|v0111 | FNC | YELLOW | VIA-VCGC-MDL806-FNC004 | — | F3 同名跨系統 VCGC,VDF; F3 同名 plan 散在 19 模組 |
| VCGC|FNC|CGC_MDL127_SixStreams|render|v0102 | FNC | YELLOW | VIA-VCGC-MDL811-FNC013 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL128_SystemCharter|_type_scale|v0102 | FNC | YELLOW | VIA-VCGC-MDL813-FNC001 | — | F3 同 body 另見 2 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL128_SystemCharter|apply_type_scale|v0102 | FNC | YELLOW | VIA-VCGC-MDL813-FNC002 | — | F3 同名 apply_type_scale 散在 3 模組;同 body 另見 2 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL128_SystemCharter|evaluate|v0102 | FNC | YELLOW | VIA-VCGC-MDL813-FNC009 | — | F3 同名 evaluate 散在 3 模組 |
| VCGC|FNC|CGC_MDL128_SystemCharter|probe|v0102 | FNC | YELLOW | VIA-VCGC-MDL813-FNC010 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 probe 散在 8 模組 |
| VCGC|FNC|CGC_MDL128_SystemCharter|render|v0102 | FNC | YELLOW | VIA-VCGC-MDL813-FNC013 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL129_LifecycleRACI|_type_scale|v0101 | FNC | YELLOW | VIA-VCGC-MDL814-FNC001 | — | F3 同 body 另見 2 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL129_LifecycleRACI|apply_type_scale|v0101 | FNC | YELLOW | VIA-VCGC-MDL814-FNC002 | — | F3 同名 apply_type_scale 散在 3 模組;同 body 另見 2 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL129_LifecycleRACI|evidence|v0101 | FNC | YELLOW | VIA-VCGC-MDL814-FNC006 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL129_LifecycleRACI|render|v0101 | FNC | YELLOW | VIA-VCGC-MDL814-FNC009 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL130_UIBridge|build|v0101 | FNC | YELLOW | VIA-VCGC-MDL815-FNC011 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL130_UIBridge|gather|v0101 | FNC | YELLOW | VIA-VCGC-MDL815-FNC006 | — | F3 同名跨系統 VCGC,VRN; F3 同名 gather 散在 10 模組 |
| VCGC|FNC|CGC_MDL131_ProjectCompletion|build|v0106 | FNC | YELLOW | VIA-VCGC-MDL822-FNC011 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL131_ProjectCompletion|classify_fail|v0106 | FNC | YELLOW | VIA-VCGC-MDL822-FNC002 | — | F3 同名 classify_fail 散在 2 模組 |
| VCGC|FNC|CGC_MDL131_ProjectCompletion|digest|v0106 | FNC | YELLOW | VIA-VCGC-MDL822-FNC012 | — | F3 同名跨系統 VCGC,VRN; F3 同名 digest 散在 4 模組 |
| VCGC|FNC|CGC_MDL131_ProjectCompletion|latest_grid|v0106 | FNC | YELLOW | VIA-VCGC-MDL822-FNC001 | — | F3 同名 latest_grid 散在 2 模組 |
| VCGC|FNC|CGC_MDL131_ProjectCompletion|render|v0106 | FNC | YELLOW | VIA-VCGC-MDL822-FNC013 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL133_ProductGate|build|v0102 | FNC | YELLOW | VIA-VCGC-MDL830-FNC027 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL133_ProductGate|classify_fail|v0102 | FNC | YELLOW | VIA-VCGC-MDL830-FNC004 | — | F3 同名 classify_fail 散在 2 模組 |
| VCGC|FNC|CGC_MDL133_ProductGate|digest|v0102 | FNC | YELLOW | VIA-VCGC-MDL830-FNC028 | — | F3 同名跨系統 VCGC,VRN; F3 同名 digest 散在 4 模組 |
| VCGC|FNC|CGC_MDL133_ProductGate|gate|v0102 | FNC | YELLOW | VIA-VCGC-MDL830-FNC013 | — | F3 同名跨系統 VCGC,VDF; F3 同名 gate 散在 2 模組 |
| VCGC|FNC|CGC_MDL133_ProductGate|latest_grid|v0102 | FNC | YELLOW | VIA-VCGC-MDL830-FNC003 | — | F3 同名 latest_grid 散在 2 模組 |
| VCGC|FNC|CGC_MDL133_ProductGate|register_tail|v0102 | FNC | YELLOW | VIA-VCGC-MDL830-FNC005 | — | F3 同名 register_tail 散在 2 模組 |
| VCGC|FNC|CGC_MDL133_ProductGate|render|v0102 | FNC | YELLOW | VIA-VCGC-MDL830-FNC030 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL133_ProductGate|verdict|v0102 | FNC | YELLOW | VIA-VCGC-MDL830-FNC025 | — | F3 同名跨系統 VCGC,VDF; F3 同名 verdict 散在 3 模組 |
| VCGC|FNC|CGC_MDL134_ParallelLanes|_via_net|v0101 | FNC | YELLOW | VIA-VCGC-MDL832-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 28 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL134_ParallelLanes|assign|v0101 | FNC | YELLOW | VIA-VCGC-MDL832-FNC005 | — | F3 同名 assign 散在 3 模組 |
| VCGC|FNC|CGC_MDL134_ParallelLanes|digest|v0101 | FNC | YELLOW | VIA-VCGC-MDL832-FNC022 | — | F3 同名跨系統 VCGC,VRN; F3 同名 digest 散在 4 模組 |
| VCGC|FNC|CGC_MDL134_ParallelLanes|plan|v0101 | FNC | YELLOW | VIA-VCGC-MDL832-FNC021 | — | F3 同名跨系統 VCGC,VDF; F3 同名 plan 散在 19 模組 |
| VCGC|FNC|CGC_MDL134_ParallelLanes|preflight|v0101 | FNC | YELLOW | VIA-VCGC-MDL832-FNC014 | — | F3 同名跨系統 VCGC,VDF; F3 同名 preflight 散在 3 模組 |
| VCGC|FNC|CGC_MDL134_ParallelLanes|render|v0101 | FNC | YELLOW | VIA-VCGC-MDL832-FNC024 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL135_EnvGovernance|__getattr__|v0118 | FNC | YELLOW | VIA-VCGC-MDL1561-FNC003 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 17 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL135_EnvGovernance|_via_net|v0118 | FNC | YELLOW | VIA-VCGC-MDL1561-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 28 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL135_EnvGovernance|main|v0118 | FNC | YELLOW | VIA-VCGC-MDL1561-FNC008 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 4 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL136_EntryBridge|_ts|v0100 | FNC | YELLOW | VIA-VCGC-MDL851-FNC001 | — | F3 同 body 另見 3 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL136_EntryBridge|env_roots|v0100 | FNC | YELLOW | VIA-VCGC-MDL851-FNC011 | — | F3 同名 env_roots 散在 3 模組 |
| VCGC|FNC|CGC_MDL136_EntryBridge|lamp|v0100 | FNC | YELLOW | VIA-VCGC-MDL851-FNC003 | — | F3 同名 lamp 散在 4 模組 |
| VCGC|FNC|CGC_MDL136_EntryBridge|plan|v0100 | FNC | YELLOW | VIA-VCGC-MDL851-FNC019 | — | F3 同名跨系統 VCGC,VDF; F3 同名 plan 散在 19 模組 |
| VCGC|FNC|CGC_MDL136_EntryBridge|render_html|v0100 | FNC | YELLOW | VIA-VCGC-MDL851-FNC018 | — | F3 同名跨系統 VCGC,VDF; F3 同名 render_html 散在 8 模組 |
| VCGC|FNC|CGC_MDL136_EntryBridge|roster|v0100 | FNC | YELLOW | VIA-VCGC-MDL851-FNC010 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 roster 散在 5 模組 |
| VCGC|FNC|CGC_MDL136_EntryBridge|status|v0100 | FNC | YELLOW | VIA-VCGC-MDL851-FNC017 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 status 散在 26 模組 |
| VCGC|FNC|CGC_MDL137_RunGate|__getattr__|v0109 | FNC | YELLOW | VIA-VCGC-MDL1404-FNC004 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 13 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL137_RunGate|_via_net|v0109 | FNC | YELLOW | VIA-VCGC-MDL1404-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 15 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL137_RunGate|_vnum|v0109 | FNC | YELLOW | VIA-VCGC-MDL1404-FNC002 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 4 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL137_RunGate|main|v0109 | FNC | YELLOW | VIA-VCGC-MDL1404-FNC006 | — | F3 同 body 另見 2 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL138_FamilyUI|_arg|v0103 | FNC | YELLOW | VIA-VCGC-MDL864-FNC015 | — | F3 同 body 另見 4 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL138_FamilyUI|_ts|v0103 | FNC | YELLOW | VIA-VCGC-MDL864-FNC001 | — | F3 同 body 另見 3 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL138_FamilyUI|hub_live|v0103 | FNC | YELLOW | VIA-VCGC-MDL864-FNC004 | — | F3 同名 hub_live 散在 2 模組 |
| VCGC|FNC|CGC_MDL138_FamilyUI|log_event|v0103 | FNC | YELLOW | VIA-VCGC-MDL864-FNC003 | — | F3 同名 log_event 散在 3 模組 |
| VCGC|FNC|CGC_MDL138_FamilyUI|python_for|v0103 | FNC | YELLOW | VIA-VCGC-MDL864-FNC005 | — | F3 同名 python_for 散在 2 模組 |
| VCGC|FNC|CGC_MDL138_FamilyUI|status|v0103 | FNC | YELLOW | VIA-VCGC-MDL864-FNC013 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 status 散在 26 模組 |
| VCGC|FNC|CGC_MDL139_InputConsole|_arg|v0111 | FNC | YELLOW | VIA-VCGC-MDL876-FNC052 | — | F3 同 body 另見 4 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL139_InputConsole|_duckdb|v0111 | FNC | YELLOW | VIA-VCGC-MDL876-FNC016 | — | F3 同 body 另見 2 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL139_InputConsole|_now|v0111 | FNC | YELLOW | VIA-VCGC-MDL876-FNC002 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL139_InputConsole|_ts|v0111 | FNC | YELLOW | VIA-VCGC-MDL876-FNC001 | — | F3 同 body 另見 3 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL139_InputConsole|build|v0111 | FNC | YELLOW | VIA-VCGC-MDL876-FNC048 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL139_InputConsole|family_python|v0111 | FNC | YELLOW | VIA-VCGC-MDL876-FNC017 | — | F3 同名 family_python 散在 4 模組 |
| VCGC|FNC|CGC_MDL139_InputConsole|hub_live|v0111 | FNC | YELLOW | VIA-VCGC-MDL876-FNC015 | — | F3 同名 hub_live 散在 2 模組 |
| VCGC|FNC|CGC_MDL139_InputConsole|load_spec|v0111 | FNC | YELLOW | VIA-VCGC-MDL876-FNC006 | — | F3 同名 load_spec 散在 4 模組 |
| VCGC|FNC|CGC_MDL139_InputConsole|log_event|v0111 | FNC | YELLOW | VIA-VCGC-MDL876-FNC003 | — | F3 同名 log_event 散在 3 模組 |
| VCGC|FNC|CGC_MDL139_InputConsole|status|v0111 | FNC | YELLOW | VIA-VCGC-MDL876-FNC046 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 status 散在 26 模組 |
| VCGC|FNC|CGC_MDL140_HandoverConsole|__getattr__|v0105 | FNC | YELLOW | VIA-VCGC-MDL1572-FNC003 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 15 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL140_HandoverConsole|_via_net|v0105 | FNC | YELLOW | VIA-VCGC-MDL1572-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 15 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL140_HandoverConsole|_vnum|v0105 | FNC | YELLOW | VIA-VCGC-MDL1572-FNC002 | — | F3 同 body 另見 6 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL140_HandoverConsole|sha|v0105 | FNC | YELLOW | VIA-VCGC-MDL1572-FNC004 | — | F3 同名 sha 散在 3 模組 |
| VCGC|FNC|CGC_MDL141_ClosingGate|_arg|v0111 | FNC | YELLOW | VIA-VCGC-MDL889-FNC023 | — | F3 同 body 另見 4 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL141_ClosingGate|_duckdb|v0111 | FNC | YELLOW | VIA-VCGC-MDL889-FNC005 | — | F3 同 body 另見 2 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL141_ClosingGate|console_mod|v0111 | FNC | YELLOW | VIA-VCGC-MDL889-FNC006 | — | F3 同名 console_mod 散在 2 模組 |
| VCGC|FNC|CGC_MDL141_ClosingGate|log_event|v0111 | FNC | YELLOW | VIA-VCGC-MDL889-FNC004 | — | F3 同名 log_event 散在 3 模組 |
| VCGC|FNC|CGC_MDL141_ClosingGate|run_chain|v0111 | FNC | YELLOW | VIA-VCGC-MDL889-FNC018 | — | F3 同名跨系統 VCGC,VRN; F3 同名 run_chain 散在 2 模組 |
| VCGC|FNC|CGC_MDL141_ClosingGate|to_markdown|v0111 | FNC | YELLOW | VIA-VCGC-MDL889-FNC016 | — | F3 同名跨系統 VCGC,VRN; F3 同名 to_markdown 散在 4 模組 |
| VCGC|FNC|CGC_MDL142_AccelImport|__getattr__|v0101 | FNC | YELLOW | VIA-VCGC-MDL891-FNC004 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 13 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL142_AccelImport|_load_as|v0101 | FNC | YELLOW | VIA-VCGC-MDL891-FNC002 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL142_AccelImport|_vnum|v0101 | FNC | YELLOW | VIA-VCGC-MDL891-FNC001 | — | F3 同 body 另見 7 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL142_AccelImport|pinned_accelerator|v0101 | FNC | YELLOW | VIA-VCGC-MDL891-FNC003 | — | F3 同名 pinned_accelerator 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL142_TWNameBook|book|v0101 | FNC | YELLOW | VIA-VCGC-MDL893-FNC004 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 book 散在 2 模組 |
| VCGC|FNC|CGC_MDL142_TWNameBook|refresh|v0101 | FNC | YELLOW | VIA-VCGC-MDL893-FNC009 | — | F3 同名跨系統 VCGC,VDF; F3 同名 refresh 散在 3 模組 |
| VCGC|FNC|CGC_MDL142_TWNameBook|status|v0101 | FNC | YELLOW | VIA-VCGC-MDL893-FNC010 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 status 散在 26 模組 |
| VCGC|FNC|CGC_MDL143_MergeMedic|__getattr__|v0105 | FNC | YELLOW | VIA-VCGC-MDL1504-FNC003 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 15 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL143_MergeMedic|classify|v0105 | FNC | YELLOW | VIA-VCGC-MDL1504-FNC004 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 classify 散在 20 模組 |
| VCGC|FNC|CGC_MDL143_MergeMedic|main|v0105 | FNC | YELLOW | VIA-VCGC-MDL1504-FNC007 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 4 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL144_CopyDoctor|build|v0102 | FNC | YELLOW | VIA-VCGC-MDL901-FNC009 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL144_CopyDoctor|digest|v0102 | FNC | YELLOW | VIA-VCGC-MDL901-FNC010 | — | F3 同名跨系統 VCGC,VRN; F3 同名 digest 散在 4 模組 |
| VCGC|FNC|CGC_MDL144_CopyDoctor|inspect|v0102 | FNC | YELLOW | VIA-VCGC-MDL901-FNC007 | — | F3 同名跨系統 VCGC,VRN; F3 同名 inspect 散在 2 模組 |
| VCGC|FNC|CGC_MDL144_CopyDoctor|register_tail|v0102 | FNC | YELLOW | VIA-VCGC-MDL901-FNC004 | — | F3 同名 register_tail 散在 2 模組 |
| VCGC|FNC|CGC_MDL145_PsTestGate|build|v0100 | FNC | YELLOW | VIA-VCGC-MDL902-FNC007 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL145_PsTestGate|find_pwsh|v0100 | FNC | YELLOW | VIA-VCGC-MDL902-FNC001 | — | F3 同名 find_pwsh 散在 3 模組 |
| VCGC|FNC|CGC_MDL146_PsAstRepair|build|v0104 | FNC | YELLOW | VIA-VCGC-MDL907-FNC018 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL146_PsAstRepair|find_pwsh|v0104 | FNC | YELLOW | VIA-VCGC-MDL907-FNC001 | — | F3 同名 find_pwsh 散在 3 模組 |
| VCGC|FNC|CGC_MDL146_PsAstRepair|panorama|v0104 | FNC | YELLOW | VIA-VCGC-MDL907-FNC005 | — | F3 同名 panorama 散在 2 模組 |
| VCGC|FNC|CGC_MDL146_PsAstRepair|render|v0104 | FNC | YELLOW | VIA-VCGC-MDL907-FNC020 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL147_EngineSmokeGate|ratchet|v0103 | FNC | YELLOW | VIA-VCGC-MDL911-FNC011 | — | F3 同名 ratchet 散在 3 模組 |
| VCGC|FNC|CGC_MDL148_EngineBus|_is_sandbox|v0131 | FNC | YELLOW | VIA-VCGC-MDL943-FNC001 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL148_EngineBus|call|v0131 | FNC | YELLOW | VIA-VCGC-MDL943-FNC022 | — | F3 同名 call 散在 4 模組 |
| VCGC|FNC|CGC_MDL148_EngineBus|catalog|v0131 | FNC | YELLOW | VIA-VCGC-MDL943-FNC017 | — | F3 同名跨系統 VCGC,VRN; F3 同名 catalog 散在 3 模組 |
| VCGC|FNC|CGC_MDL148_EngineBus|child_env|v0131 | FNC | YELLOW | VIA-VCGC-MDL943-FNC010 | — | F3 同名 child_env 散在 4 模組 |
| VCGC|FNC|CGC_MDL148_EngineBus|data_home|v0131 | FNC | YELLOW | VIA-VCGC-MDL943-FNC002 | — | F3 同名跨系統 VCGC,VDF; F3 同名 data_home 散在 2 模組 |
| VCGC|FNC|CGC_MDL148_EngineBus|load_spec|v0131 | FNC | YELLOW | VIA-VCGC-MDL943-FNC015 | — | F3 同名 load_spec 散在 4 模組 |
| VCGC|FNC|CGC_MDL148_EngineBus|matrix|v0131 | FNC | YELLOW | VIA-VCGC-MDL943-FNC023 | — | F3 同名跨系統 VCGC,VRN; F3 同名 matrix 散在 7 模組 |
| VCGC|FNC|CGC_MDL148_EngineBus|python_for|v0131 | FNC | YELLOW | VIA-VCGC-MDL943-FNC016 | — | F3 同名 python_for 散在 2 模組 |
| VCGC|FNC|CGC_MDL148_EngineBus|render|v0131 | FNC | YELLOW | VIA-VCGC-MDL943-FNC033 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL149_BoxesFlow|_load|v0100 | FNC | YELLOW | VIA-VCGC-MDL944-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 9 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_BoxesFlow|is_stock|v0100 | FNC | YELLOW | VIA-VCGC-MDL944-FNC006 | — | F3 同名 is_stock 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_BoxesFlow|read_page1|v0100 | FNC | YELLOW | VIA-VCGC-MDL944-FNC007 | — | F3 同名 read_page1 散在 2 模組 |
| VCGC|FNC|CGC_MDL149_BoxesFlow|sample_dir|v0100 | FNC | YELLOW | VIA-VCGC-MDL944-FNC002 | — | F3 同名 sample_dir 散在 7 模組;同 body 另見 6 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_ChainAll|_load|v0101 | FNC | YELLOW | VIA-VCGC-MDL946-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 8 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_Closeout|score|v0101 | FNC | YELLOW | VIA-VCGC-MDL948-FNC001 | — | F3 同名 score 散在 3 模組 |
| VCGC|FNC|CGC_MDL149_EntryLock|canon|v0101 | FNC | YELLOW | VIA-VCGC-MDL950-FNC002 | — | F3 同名 canon 散在 4 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_EntryLock|matrix|v0101 | FNC | YELLOW | VIA-VCGC-MDL950-FNC003 | — | F3 同名跨系統 VCGC,VRN; F3 同名 matrix 散在 7 模組 |
| VCGC|FNC|CGC_MDL149_FilenameCut|_load|v0100 | FNC | YELLOW | VIA-VCGC-MDL951-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 9 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_FilenameCut|sample_dir|v0100 | FNC | YELLOW | VIA-VCGC-MDL951-FNC002 | — | F3 同名 sample_dir 散在 7 模組;同 body 另見 6 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_GreenMatrix|render|v0100 | FNC | YELLOW | VIA-VCGC-MDL952-FNC004 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL149_Identity|accept|v0100 | FNC | YELLOW | VIA-VCGC-MDL953-FNC002 | — | F3 同名跨系統 VCGC,VDF |
| VCGC|FNC|CGC_MDL149_Integrate|_load|v0100 | FNC | YELLOW | VIA-VCGC-MDL954-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 9 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_LayoutUse|_load|v0100 | FNC | YELLOW | VIA-VCGC-MDL955-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 9 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_LayoutUse|is_stock|v0100 | FNC | YELLOW | VIA-VCGC-MDL955-FNC005 | — | F3 同名 is_stock 散在 2 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_LayoutUse|read_page1|v0100 | FNC | YELLOW | VIA-VCGC-MDL955-FNC006 | — | F3 同名 read_page1 散在 2 模組 |
| VCGC|FNC|CGC_MDL149_LayoutUse|sample_dir|v0100 | FNC | YELLOW | VIA-VCGC-MDL955-FNC002 | — | F3 同名 sample_dir 散在 7 模組;同 body 另見 6 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_LayoutUse|zone_of|v0100 | FNC | YELLOW | VIA-VCGC-MDL955-FNC003 | — | F3 同名 zone_of 散在 4 模組 |
| VCGC|FNC|CGC_MDL149_OneDragon|_lamp_rc|v0100 | FNC | YELLOW | VIA-VCGC-MDL956-FNC004 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_OneDragon|_quiet|v0100 | FNC | YELLOW | VIA-VCGC-MDL956-FNC002 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_OneDragon|execute|v0100 | FNC | YELLOW | VIA-VCGC-MDL956-FNC005 | — | F3 同名 execute 散在 8 模組 |
| VCGC|FNC|CGC_MDL149_OneDragon|real_calls|v0100 | FNC | YELLOW | VIA-VCGC-MDL956-FNC006 | — | F3 同名 real_calls 散在 2 模組 |
| VCGC|FNC|CGC_MDL149_PageCrosscheck|_load|v0100 | FNC | YELLOW | VIA-VCGC-MDL957-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 9 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_PageCrosscheck|sample_dir|v0100 | FNC | YELLOW | VIA-VCGC-MDL957-FNC002 | — | F3 同名 sample_dir 散在 7 模組;同 body 另見 6 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_PasteBlock|build|v0101 | FNC | YELLOW | VIA-VCGC-MDL959-FNC005 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL149_PasteBlock|paste|v0101 | FNC | YELLOW | VIA-VCGC-MDL959-FNC006 | — | F3 同名 paste 散在 3 模組 |
| VCGC|FNC|CGC_MDL149_ReadLanes|_load|v0100 | FNC | YELLOW | VIA-VCGC-MDL960-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 9 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_ReadLanes|_sample|v0100 | FNC | YELLOW | VIA-VCGC-MDL960-FNC002 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_RoundMatrix|classify|v0100 | FNC | YELLOW | VIA-VCGC-MDL961-FNC004 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 classify 散在 20 模組 |
| VCGC|FNC|CGC_MDL149_RoundMatrix|locate|v0100 | FNC | YELLOW | VIA-VCGC-MDL961-FNC001 | — | F3 同名跨系統 VCGC,VRN; F3 同名 locate 散在 2 模組 |
| VCGC|FNC|CGC_MDL149_StatementCheck|_load|v0100 | FNC | YELLOW | VIA-VCGC-MDL964-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 9 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_StatementCheck|measure|v0100 | FNC | YELLOW | VIA-VCGC-MDL964-FNC006 | — | F3 同名跨系統 VCGC,VRN; F3 同名 measure 散在 6 模組 |
| VCGC|FNC|CGC_MDL149_StatementCheck|sample_dir|v0100 | FNC | YELLOW | VIA-VCGC-MDL964-FNC002 | — | F3 同名 sample_dir 散在 7 模組;同 body 另見 6 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_Sync|_load|v0102 | FNC | YELLOW | VIA-VCGC-MDL967-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 9 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_Sync|_sample|v0102 | FNC | YELLOW | VIA-VCGC-MDL967-FNC002 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_TableTake|_load|v0101 | FNC | YELLOW | VIA-VCGC-MDL969-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 9 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_TableTake|dedup|v0101 | FNC | YELLOW | VIA-VCGC-MDL969-FNC006 | — | F3 同名 dedup 散在 2 模組 |
| VCGC|FNC|CGC_MDL149_TextGrade|_load|v0100 | FNC | YELLOW | VIA-VCGC-MDL970-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 9 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_TextGrade|measure|v0100 | FNC | YELLOW | VIA-VCGC-MDL970-FNC007 | — | F3 同名跨系統 VCGC,VRN; F3 同名 measure 散在 6 模組 |
| VCGC|FNC|CGC_MDL149_TextGrade|sample_dir|v0100 | FNC | YELLOW | VIA-VCGC-MDL970-FNC002 | — | F3 同名 sample_dir 散在 7 模組;同 body 另見 6 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_UnitScale|upside_pct|v0101 | FNC | YELLOW | VIA-VCGC-MDL972-FNC008 | — | F3 同名跨系統 VCGC,VRN |
| VCGC|FNC|CGC_MDL149_VRNLive|sample_dir|v0100 | FNC | YELLOW | VIA-VCGC-MDL975-FNC001 | — | F3 同名 sample_dir 散在 7 模組;同 body 另見 6 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_VeritasCentralGovernanceConsole|__getattr__|v0190 | FNC | YELLOW | VIA-VCGC-MDL1543-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 17 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_VeritasCentralGovernanceConsole|cached|v0190 | FNC | YELLOW | VIA-VCGC-MDL1543-FNC002 | — | F3 同名 cached 散在 2 模組 |
| VCGC|FNC|CGC_MDL149_VeritasCentralGovernanceConsole|main|v0190 | FNC | YELLOW | VIA-VCGC-MDL1543-FNC004 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_WorkflowMatrix|_lamp_rc|v0100 | FNC | YELLOW | VIA-VCGC-MDL1040-FNC003 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_WorkflowMatrix|_quiet|v0100 | FNC | YELLOW | VIA-VCGC-MDL1040-FNC002 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL149_WorkflowMatrix|execute|v0100 | FNC | YELLOW | VIA-VCGC-MDL1040-FNC004 | — | F3 同名 execute 散在 8 模組 |
| VCGC|FNC|CGC_MDL149_WorkflowMatrix|real_calls|v0100 | FNC | YELLOW | VIA-VCGC-MDL1040-FNC005 | — | F3 同名 real_calls 散在 2 模組 |
| VCGC|FNC|CGC_MDL150_CentralGovernanceFamily|_arg|v0103 | FNC | YELLOW | VIA-VCGC-MDL1044-FNC022 | — | F3 同 body 另見 4 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL150_CentralGovernanceFamily|_ts|v0103 | FNC | YELLOW | VIA-VCGC-MDL1044-FNC001 | — | F3 同 body 另見 3 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL150_CentralGovernanceFamily|child_env|v0103 | FNC | YELLOW | VIA-VCGC-MDL1044-FNC015 | — | F3 同名 child_env 散在 4 模組 |
| VCGC|FNC|CGC_MDL150_CentralGovernanceFamily|plan|v0103 | FNC | YELLOW | VIA-VCGC-MDL1044-FNC020 | — | F3 同名跨系統 VCGC,VDF; F3 同名 plan 散在 19 模組 |
| VCGC|FNC|CGC_MDL150_CentralGovernanceFamily|status|v0103 | FNC | YELLOW | VIA-VCGC-MDL1044-FNC019 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 status 散在 26 模組 |
| VCGC|FNC|CGC_MDL152_VtmraGate|_arg|v0103 | FNC | YELLOW | VIA-VCGC-MDL1411-FNC012 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL152_VtmraGate|child_env|v0103 | FNC | YELLOW | VIA-VCGC-MDL1411-FNC003 | — | F3 同名 child_env 散在 4 模組 |
| VCGC|FNC|CGC_MDL152_VtmraGate|family_python|v0103 | FNC | YELLOW | VIA-VCGC-MDL1411-FNC002 | — | F3 同名 family_python 散在 4 模組 |
| VCGC|FNC|CGC_MDL152_VtmraGate|render_html|v0103 | FNC | YELLOW | VIA-VCGC-MDL1411-FNC008 | — | F3 同名跨系統 VCGC,VDF; F3 同名 render_html 散在 8 模組 |
| VCGC|FNC|CGC_MDL152_VtmraGate|status|v0103 | FNC | YELLOW | VIA-VCGC-MDL1411-FNC010 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 status 散在 26 模組 |
| VCGC|FNC|CGC_MDL152_VtmraGate|test|v0103 | FNC | YELLOW | VIA-VCGC-MDL1411-FNC009 | — | F3 同名 test 散在 5 模組 |
| VCGC|FNC|CGC_MDL152_VtmraGate|verdict|v0103 | FNC | YELLOW | VIA-VCGC-MDL1411-FNC007 | — | F3 同名跨系統 VCGC,VDF; F3 同名 verdict 散在 3 模組 |
| VCGC|FNC|CGC_MDL153_WorkflowComposer|_arg|v0102 | FNC | YELLOW | VIA-VCGC-MDL1050-FNC002 | — | F3 同 body 另見 4 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL153_WorkflowComposer|_now|v0102 | FNC | YELLOW | VIA-VCGC-MDL1050-FNC001 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL153_WorkflowComposer|page_html|v0102 | FNC | YELLOW | VIA-VCGC-MDL1050-FNC022 | — | F3 同名跨系統 VCGC,VRN; F3 同名 page_html 散在 3 模組 |
| VCGC|FNC|CGC_MDL153_WorkflowComposer|validate|v0102 | FNC | YELLOW | VIA-VCGC-MDL1050-FNC007 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 validate 散在 6 模組 |
| VCGC|FNC|CGC_MDL153_WorkflowComposer|write_page|v0102 | FNC | YELLOW | VIA-VCGC-MDL1050-FNC023 | — | F3 同名 write_page 散在 4 模組 |
| VCGC|FNC|CGC_MDL154_VIAFunctionalAcceptance|child_env|v0100 | FNC | YELLOW | VIA-VCGC-MDL1051-FNC003 | — | F3 同名 child_env 散在 4 模組 |
| VCGC|FNC|CGC_MDL154_VIAFunctionalAcceptance|now|v0100 | FNC | YELLOW | VIA-VCGC-MDL1051-FNC001 | — | F3 同名 now 散在 15 模組 |
| VCGC|FNC|CGC_MDL154_VIAFunctionalAcceptance|render_html|v0100 | FNC | YELLOW | VIA-VCGC-MDL1051-FNC010 | — | F3 同名跨系統 VCGC,VDF; F3 同名 render_html 散在 8 模組 |
| VCGC|FNC|CGC_MDL154_VIAFunctionalAcceptance|run_station|v0100 | FNC | YELLOW | VIA-VCGC-MDL1051-FNC004 | — | F3 同名 run_station 散在 2 模組 |
| VCGC|FNC|CGC_MDL155_VIAUnifiedSSOTAutoCode|_normalise_argv_b534|v0101 | FNC | YELLOW | VIA-VCGC-MDL1053-FNC019 | — | F3 同 body 跨系統(候選共用 LIB) |
| VCGC|FNC|CGC_MDL155_VIAUnifiedSSOTAutoCode|classify|v0101 | FNC | YELLOW | VIA-VCGC-MDL1053-FNC017 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 classify 散在 20 模組 |
| VCGC|FNC|CGC_MDL155_VIAUnifiedSSOTAutoCode|now_iso|v0101 | FNC | YELLOW | VIA-VCGC-MDL1053-FNC001 | — | F3 同名跨系統 VCGC,VRN; F3 同名 now_iso 散在 6 模組 |
| VCGC|FNC|CGC_MDL155_VIAUnifiedSSOTAutoCode|render_html|v0101 | FNC | YELLOW | VIA-VCGC-MDL1053-FNC015 | — | F3 同名跨系統 VCGC,VDF; F3 同名 render_html 散在 8 模組 |
| VCGC|FNC|CGC_MDL155_VIAUnifiedSSOTAutoCode|resolve|v0101 | FNC | YELLOW | VIA-VCGC-MDL1053-FNC003 | — | F3 同名跨系統 VCGC,VRN; F3 同名 resolve 散在 16 模組 |
| VCGC|FNC|CGC_MDL155_VIAUnifiedSSOTAutoCode|sha256|v0101 | FNC | YELLOW | VIA-VCGC-MDL1053-FNC002 | — | F3 同名 sha256 散在 5 模組 |
| VCGC|FNC|CGC_MDL156_VIAAcceleratorControl|_vnum|v0112 | FNC | YELLOW | VIA-VCGC-MDL1573-FNC001 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL157_VIAUniqueEntryControl|__getattr__|v0106 | FNC | YELLOW | VIA-VCGC-MDL1418-FNC003 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 15 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL157_VIAUniqueEntryControl|_via_net|v0106 | FNC | YELLOW | VIA-VCGC-MDL1418-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 15 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL157_VIAUniqueEntryControl|_vnum|v0106 | FNC | YELLOW | VIA-VCGC-MDL1418-FNC002 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 12 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL157_VIAUniqueEntryControl|read|v0106 | FNC | YELLOW | VIA-VCGC-MDL1418-FNC006 | — | F3 同名跨系統 VCGC,VRN; F3 同名 read 散在 22 模組 |
| VCGC|FNC|CGC_MDL158_VIAPanoramaAuditRepair|__getattr__|v0117 | FNC | YELLOW | VIA-VCGC-MDL1477-FNC003 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 15 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL158_VIAPanoramaAuditRepair|_via_net|v0117 | FNC | YELLOW | VIA-VCGC-MDL1477-FNC001 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 15 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL158_VIAPanoramaAuditRepair|_vnum|v0117 | FNC | YELLOW | VIA-VCGC-MDL1477-FNC002 | — | F3 同 body 另見 6 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL158_VIAPanoramaAuditRepair|route|v0117 | FNC | YELLOW | VIA-VCGC-MDL1477-FNC019 | — | F3 同名 route 散在 3 模組 |
| VCGC|FNC|CGC_MDL159_VIAUnifiedConsole|build_html|v0101 | FNC | YELLOW | VIA-VCGC-MDL1089-FNC010 | — | F3 同名 build_html 散在 5 模組 |
| VCGC|FNC|CGC_MDL159_VIAUnifiedConsole|collect|v0101 | FNC | YELLOW | VIA-VCGC-MDL1089-FNC006 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 collect 散在 13 模組 |
| VCGC|FNC|CGC_MDL160_UIUnifyGate|owners|v0109 | FNC | YELLOW | VIA-VCGC-MDL1099-FNC017 | — | F3 同名跨系統 VCGC,VRN |
| VCGC|FNC|CGC_MDL160_UIUnifyGate|plan|v0109 | FNC | YELLOW | VIA-VCGC-MDL1099-FNC021 | — | F3 同名跨系統 VCGC,VDF; F3 同名 plan 散在 19 模組 |
| VCGC|FNC|CGC_MDL160_UIUnifyGate|scan|v0109 | FNC | YELLOW | VIA-VCGC-MDL1099-FNC018 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL160_UIUnifyGate|write_out|v0109 | FNC | YELLOW | VIA-VCGC-MDL1099-FNC022 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同 body 跨系統(候選共用 LIB); F3 同名 write_out 散在 7 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL161_PEISCapabilityEngine|book|v0107 | FNC | YELLOW | VIA-VCGC-MDL1105-FNC019 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 book 散在 2 模組 |
| VCGC|FNC|CGC_MDL161_PEISCapabilityEngine|call|v0107 | FNC | YELLOW | VIA-VCGC-MDL1105-FNC008 | — | F3 同名 call 散在 4 模組 |
| VCGC|FNC|CGC_MDL161_PEISCapabilityEngine|report|v0107 | FNC | YELLOW | VIA-VCGC-MDL1105-FNC031 | — | F3 同名跨系統 VCGC,VDF; F3 同名 report 散在 8 模組 |
| VCGC|FNC|CGC_MDL161_PEISCapabilityEngine|scan|v0107 | FNC | YELLOW | VIA-VCGC-MDL1105-FNC014 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL161_PEISCapabilityEngine|status|v0107 | FNC | YELLOW | VIA-VCGC-MDL1105-FNC013 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 status 散在 26 模組 |
| VCGC|FNC|CGC_MDL161_PEISCapabilityEngine|write_out|v0107 | FNC | YELLOW | VIA-VCGC-MDL1105-FNC032 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 write_out 散在 7 模組 |
| VCGC|FNC|CGC_MDL162_CommandCardFreeze|parse|v0100 | FNC | YELLOW | VIA-VCGC-MDL1106-FNC004 | — | F3 同名跨系統 VCGC,VDF; F3 同名 parse 散在 5 模組 |
| VCGC|FNC|CGC_MDL162_CommandCardFreeze|verify|v0100 | FNC | YELLOW | VIA-VCGC-MDL1106-FNC008 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 verify 散在 5 模組 |
| VCGC|FNC|CGC_MDL162_CommandCardFreeze|write_out|v0100 | FNC | YELLOW | VIA-VCGC-MDL1106-FNC010 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同 body 跨系統(候選共用 LIB); F3 同名 write_out 散在 7 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL163_MasterFileCard|build|v0100 | FNC | YELLOW | VIA-VCGC-MDL1107-FNC006 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL163_MasterFileCard|render|v0100 | FNC | YELLOW | VIA-VCGC-MDL1107-FNC007 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL163_MasterFileCard|write_out|v0100 | FNC | YELLOW | VIA-VCGC-MDL1107-FNC008 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同 body 跨系統(候選共用 LIB); F3 同名 write_out 散在 7 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL164_GovernanceCompletenessAudit|audit|v0109 | FNC | YELLOW | VIA-VCGC-MDL1117-FNC004 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 audit 散在 11 模組 |
| VCGC|FNC|CGC_MDL164_GovernanceCompletenessAudit|plan|v0109 | FNC | YELLOW | VIA-VCGC-MDL1117-FNC013 | — | F3 同名跨系統 VCGC,VDF; F3 同名 plan 散在 19 模組 |
| VCGC|FNC|CGC_MDL164_GovernanceCompletenessAudit|write_out|v0109 | FNC | YELLOW | VIA-VCGC-MDL1117-FNC014 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同 body 跨系統(候選共用 LIB); F3 同名 write_out 散在 7 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL165_CommandRunGate|classify|v0101 | FNC | YELLOW | VIA-VCGC-MDL1119-FNC005 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 classify 散在 20 模組 |
| VCGC|FNC|CGC_MDL165_CommandRunGate|plan|v0101 | FNC | YELLOW | VIA-VCGC-MDL1119-FNC008 | — | F3 同名跨系統 VCGC,VDF; F3 同名 plan 散在 19 模組 |
| VCGC|FNC|CGC_MDL165_CommandRunGate|register|v0101 | FNC | YELLOW | VIA-VCGC-MDL1119-FNC001 | — | F3 同名跨系統 VCGC,VRN; F3 同名 register 散在 10 模組 |
| VCGC|FNC|CGC_MDL165_CommandRunGate|scan|v0101 | FNC | YELLOW | VIA-VCGC-MDL1119-FNC007 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL165_CommandRunGate|write_out|v0101 | FNC | YELLOW | VIA-VCGC-MDL1119-FNC009 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同 body 跨系統(候選共用 LIB); F3 同名 write_out 散在 7 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL166_LibraryConsolidationGate|audit|v0100 | FNC | YELLOW | VIA-VCGC-MDL1120-FNC005 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 audit 散在 11 模組 |
| VCGC|FNC|CGC_MDL166_LibraryConsolidationGate|plan|v0100 | FNC | YELLOW | VIA-VCGC-MDL1120-FNC006 | — | F3 同名跨系統 VCGC,VDF; F3 同名 plan 散在 19 模組 |
| VCGC|FNC|CGC_MDL166_LibraryConsolidationGate|write_out|v0100 | FNC | YELLOW | VIA-VCGC-MDL1120-FNC007 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同 body 跨系統(候選共用 LIB); F3 同名 write_out 散在 7 模組;同 body 另見 3 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL167_RegenRevert|classify|v0100 | FNC | YELLOW | VIA-VCGC-MDL1121-FNC006 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 classify 散在 20 模組 |
| VCGC|FNC|CGC_MDL167_RegenRevert|load_book|v0100 | FNC | YELLOW | VIA-VCGC-MDL1121-FNC004 | — | F3 同名跨系統 VCGC,VDF; F3 同名 load_book 散在 2 模組 |
| VCGC|FNC|CGC_MDL167_RegenRevert|repo_root|v0100 | FNC | YELLOW | VIA-VCGC-MDL1121-FNC003 | — | F3 同名跨系統 VCGC,VRN |
| VCGC|FNC|CGC_MDL167_RegenRevert|report|v0100 | FNC | YELLOW | VIA-VCGC-MDL1121-FNC009 | — | F3 同名跨系統 VCGC,VDF; F3 同名 report 散在 8 模組 |
| VCGC|FNC|CGC_MDL169_VIAStateMatrix|_spec_mod|v0104 | FNC | YELLOW | VIA-VCGC-MDL1128-FNC025 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL169_VIAStateMatrix|collect|v0104 | FNC | YELLOW | VIA-VCGC-MDL1128-FNC024 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 collect 散在 13 模組 |
| VCGC|FNC|CGC_MDL169_VIAStateMatrix|grid_evidence|v0104 | FNC | YELLOW | VIA-VCGC-MDL1128-FNC010 | — | F3 同名 grid_evidence 散在 2 模組 |
| VCGC|FNC|CGC_MDL169_VIAStateMatrix|load_json|v0104 | FNC | YELLOW | VIA-VCGC-MDL1128-FNC005 | — | F3 同名 load_json 散在 7 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL169_VIAStateMatrix|newest|v0104 | FNC | YELLOW | VIA-VCGC-MDL1128-FNC002 | — | F3 同名跨系統 VCGC,VRN; F3 同名 newest 散在 11 模組 |
| VCGC|FNC|CGC_MDL169_VIAStateMatrix|rel|v0104 | FNC | YELLOW | VIA-VCGC-MDL1128-FNC004 | — | F3 同名 rel 散在 5 模組 |
| VCGC|FNC|CGC_MDL169_VIAStateMatrix|render|v0104 | FNC | YELLOW | VIA-VCGC-MDL1128-FNC030 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL169_VIAStateMatrix|row|v0104 | FNC | YELLOW | VIA-VCGC-MDL1128-FNC006 | — | F3 同名 row 散在 2 模組 |
| VCGC|FNC|CGC_MDL169_VIAStateMatrix|scan_env|v0104 | FNC | YELLOW | VIA-VCGC-MDL1128-FNC012 | — | F3 同名 scan_env 散在 2 模組 |
| VCGC|FNC|CGC_MDL169_VIAStateMatrix|write_html|v0104 | FNC | YELLOW | VIA-VCGC-MDL1128-FNC034 | — | F3 同名跨系統 VCGC,VRN; F3 同名 write_html 散在 20 模組 |
| VCGC|FNC|CGC_MDL169_VIAStateMatrix|write_log|v0104 | FNC | YELLOW | VIA-VCGC-MDL1128-FNC035 | — | F3 同名 write_log 散在 4 模組 |
| VCGC|FNC|CGC_MDL170_VDFChainRunner|__getattr__|v0105 | FNC | YELLOW | VIA-VCGC-MDL1515-FNC002 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 17 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL170_VDFChainRunner|_body|v0105 | FNC | YELLOW | VIA-VCGC-MDL1515-FNC003 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL170_VDFChainRunner|_vnum|v0105 | FNC | YELLOW | VIA-VCGC-MDL1515-FNC001 | — | F3 同 body 另見 6 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL170_VDFChainRunner|run_one|v0105 | FNC | YELLOW | VIA-VCGC-MDL1515-FNC005 | — | F3 同名跨系統 VCGC,VDF; F3 同名 run_one 散在 3 模組 |
| VCGC|FNC|CGC_MDL170_VDFChainRunner|say|v0105 | FNC | YELLOW | VIA-VCGC-MDL1515-FNC004 | — | F3 同名 say 散在 7 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL171_PanoramaBatchPlanner|_spec_mod|v0101 | FNC | YELLOW | VIA-VCGC-MDL1134-FNC001 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL171_PanoramaBatchPlanner|build|v0101 | FNC | YELLOW | VIA-VCGC-MDL1134-FNC017 | — | F3 同名跨系統 VCGC,VDF,VRN |
| VCGC|FNC|CGC_MDL171_PanoramaBatchPlanner|collect|v0101 | FNC | YELLOW | VIA-VCGC-MDL1134-FNC015 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 collect 散在 13 模組 |
| VCGC|FNC|CGC_MDL171_PanoramaBatchPlanner|load_json|v0101 | FNC | YELLOW | VIA-VCGC-MDL1134-FNC007 | — | F3 同名 load_json 散在 7 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL171_PanoramaBatchPlanner|newest|v0101 | FNC | YELLOW | VIA-VCGC-MDL1134-FNC006 | — | F3 同名跨系統 VCGC,VRN; F3 同名 newest 散在 11 模組 |
| VCGC|FNC|CGC_MDL171_PanoramaBatchPlanner|rel|v0101 | FNC | YELLOW | VIA-VCGC-MDL1134-FNC005 | — | F3 同名 rel 散在 5 模組 |
| VCGC|FNC|CGC_MDL171_PanoramaBatchPlanner|render|v0101 | FNC | YELLOW | VIA-VCGC-MDL1134-FNC021 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL171_PanoramaBatchPlanner|write_html|v0101 | FNC | YELLOW | VIA-VCGC-MDL1134-FNC024 | — | F3 同名跨系統 VCGC,VRN; F3 同名 write_html 散在 20 模組 |
| VCGC|FNC|CGC_MDL171_PanoramaBatchPlanner|write_log|v0101 | FNC | YELLOW | VIA-VCGC-MDL1134-FNC025 | — | F3 同名 write_log 散在 4 模組 |
| VCGC|FNC|CGC_MDL172_VRNChainRunner|__getattr__|v0108 | FNC | YELLOW | VIA-VCGC-MDL1516-FNC002 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 17 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL172_VRNChainRunner|_body|v0108 | FNC | YELLOW | VIA-VCGC-MDL1516-FNC003 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL172_VRNChainRunner|_vnum|v0108 | FNC | YELLOW | VIA-VCGC-MDL1516-FNC001 | — | F3 同 body 另見 6 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL172_VRNChainRunner|main|v0108 | FNC | YELLOW | VIA-VCGC-MDL1516-FNC007 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL172_VRNChainRunner|say|v0108 | FNC | YELLOW | VIA-VCGC-MDL1516-FNC004 | — | F3 同名 say 散在 7 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL173_MatrixReportSpec|console|v0100 | FNC | YELLOW | VIA-VCGC-MDL1143-FNC003 | — | F3 同名 console 散在 4 模組 |
| VCGC|FNC|CGC_MDL173_MatrixReportSpec|css|v0100 | FNC | YELLOW | VIA-VCGC-MDL1143-FNC005 | — | F3 同名 css 散在 2 模組 |
| VCGC|FNC|CGC_MDL173_MatrixReportSpec|demo|v0100 | FNC | YELLOW | VIA-VCGC-MDL1143-FNC012 | — | F3 同名 demo 散在 2 模組 |
| VCGC|FNC|CGC_MDL173_MatrixReportSpec|html_table|v0100 | FNC | YELLOW | VIA-VCGC-MDL1143-FNC009 | — | F3 同名 html_table 散在 2 模組 |
| VCGC|FNC|CGC_MDL173_MatrixReportSpec|page|v0100 | FNC | YELLOW | VIA-VCGC-MDL1143-FNC008 | — | F3 同名 page 散在 4 模組 |
| VCGC|FNC|CGC_MDL173_MatrixReportSpec|page_html|v0100 | FNC | YELLOW | VIA-VCGC-MDL1143-FNC010 | — | F3 同名跨系統 VCGC,VRN; F3 同名 page_html 散在 3 模組 |
| VCGC|FNC|CGC_MDL173_MatrixReportSpec|rel|v0100 | FNC | YELLOW | VIA-VCGC-MDL1143-FNC001 | — | F3 同名 rel 散在 5 模組 |
| VCGC|FNC|CGC_MDL173_MatrixReportSpec|table|v0100 | FNC | YELLOW | VIA-VCGC-MDL1143-FNC004 | — | F3 同名 table 散在 8 模組 |
| VCGC|FNC|CGC_MDL174_PackagingGate|_head_ct|v0101 | FNC | YELLOW | VIA-VCGC-MDL1145-FNC010 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL174_PackagingGate|collect|v0101 | FNC | YELLOW | VIA-VCGC-MDL1145-FNC021 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 collect 散在 13 模組 |
| VCGC|FNC|CGC_MDL174_PackagingGate|excluded|v0101 | FNC | YELLOW | VIA-VCGC-MDL1145-FNC005 | — | F3 同名 excluded 散在 3 模組 |
| VCGC|FNC|CGC_MDL174_PackagingGate|grid_evidence|v0101 | FNC | YELLOW | VIA-VCGC-MDL1145-FNC011 | — | F3 同名 grid_evidence 散在 2 模組 |
| VCGC|FNC|CGC_MDL174_PackagingGate|newest|v0101 | FNC | YELLOW | VIA-VCGC-MDL1145-FNC002 | — | F3 同名跨系統 VCGC,VRN; F3 同名 newest 散在 11 模組 |
| VCGC|FNC|CGC_MDL174_PackagingGate|print_plain|v0101 | FNC | YELLOW | VIA-VCGC-MDL1145-FNC026 | — | F3 同名 print_plain 散在 2 模組 |
| VCGC|FNC|CGC_MDL174_PackagingGate|rel|v0101 | FNC | YELLOW | VIA-VCGC-MDL1145-FNC001 | — | F3 同名 rel 散在 5 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL174_PackagingGate|render|v0101 | FNC | YELLOW | VIA-VCGC-MDL1145-FNC024 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL174_PackagingGate|roster|v0101 | FNC | YELLOW | VIA-VCGC-MDL1145-FNC008 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 roster 散在 5 模組 |
| VCGC|FNC|CGC_MDL174_PackagingGate|row|v0101 | FNC | YELLOW | VIA-VCGC-MDL1145-FNC003 | — | F3 同名 row 散在 2 模組 |
| VCGC|FNC|CGC_MDL174_PackagingGate|to_markdown|v0101 | FNC | YELLOW | VIA-VCGC-MDL1145-FNC023 | — | F3 同名跨系統 VCGC,VRN; F3 同名 to_markdown 散在 4 模組 |
| VCGC|FNC|CGC_MDL174_PackagingGate|write_log|v0101 | FNC | YELLOW | VIA-VCGC-MDL1145-FNC025 | — | F3 同名 write_log 散在 4 模組 |
| VCGC|FNC|CGC_MDL175_AutoDeploy|_head_ct|v0101 | FNC | YELLOW | VIA-VCGC-MDL1147-FNC003 | — | F3 同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL175_AutoDeploy|plan|v0101 | FNC | YELLOW | VIA-VCGC-MDL1147-FNC007 | — | F3 同名跨系統 VCGC,VDF; F3 同名 plan 散在 19 模組 |
| VCGC|FNC|CGC_MDL175_AutoDeploy|print_plain|v0101 | FNC | YELLOW | VIA-VCGC-MDL1147-FNC013 | — | F3 同名 print_plain 散在 2 模組 |
| VCGC|FNC|CGC_MDL175_AutoDeploy|rel|v0101 | FNC | YELLOW | VIA-VCGC-MDL1147-FNC002 | — | F3 同名 rel 散在 5 模組;同 body 另見 1 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL175_AutoDeploy|render|v0101 | FNC | YELLOW | VIA-VCGC-MDL1147-FNC011 | — | F3 同名跨系統 VCGC,VDF,VRN; F3 同名 render 散在 53 模組 |
| VCGC|FNC|CGC_MDL175_AutoDeploy|step|v0101 | FNC | YELLOW | VIA-VCGC-MDL1147-FNC006 | — | F3 同名 step 散在 2 模組 |
| VCGC|FNC|CGC_MDL175_AutoDeploy|to_markdown|v0101 | FNC | YELLOW | VIA-VCGC-MDL1147-FNC009 | — | F3 同名跨系統 VCGC,VRN; F3 同名 to_markdown 散在 4 模組 |
| VCGC|FNC|CGC_MDL175_AutoDeploy|write_log|v0101 | FNC | YELLOW | VIA-VCGC-MDL1147-FNC012 | — | F3 同名 write_log 散在 4 模組 |
| VCGC|FNC|CGC_MDL176_SynonymUnion|__getattr__|v0103 | FNC | YELLOW | VIA-VCGC-MDL1501-FNC002 | — | F3 同 body 跨系統(候選共用 LIB); F3 同 body 另見 15 處(候選共用 LIB) |
| VCGC|FNC|CGC_MDL176_SynonymUnion|_vnum|v0103 | FNC | YELLOW | VIA-VCGC-MDL1501-FNC001 | — | F3 同 body 跨系統(候選共用 LIB) |
