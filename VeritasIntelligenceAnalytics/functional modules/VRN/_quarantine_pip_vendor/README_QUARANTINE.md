# Quarantine: pip/vendor internals — NOT VRN code

These seven .py files are internals leaked from a Python packaging toolchain
(pip `_internal`/`_vendor`, resolvelib, rich), not Veritas Report Nova modules:

reporter.py · reporters.py · table.py · editable_legacy.py ·
installation_report.py · metadata_editable.py · wheel_editable.py

They were found loose in the operator's canonical VRN folder and are kept here
untouched for provenance only. They are excluded from the VRN artifact
registry and must not be imported by VRN engines.
