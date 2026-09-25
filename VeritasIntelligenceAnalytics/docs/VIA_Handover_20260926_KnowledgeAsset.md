# VIA handover 2026-09-26 · knowledge assets

Door: VCGC only (`VIA_FROM_VCGC=YES`).
Book: `supportive modules/registry/VIA_KnowledgeAsset_Book_v0100.json`.
Check: `CGC_MDL191_KnowledgeAsset_v0100.py`.

The US-macro files were not moved. Each door already opens a fixed path. The book is the structure: process, then inventory, then method, then the handover, then the refresh engines.

A new series still follows `VIA_USMacro_SSOT_Process_v0100.json`. It is not added by editing this catalog's inventory rows in place of a probe. This door does not refresh `us_macro` and does not edit the intake SSOT.
