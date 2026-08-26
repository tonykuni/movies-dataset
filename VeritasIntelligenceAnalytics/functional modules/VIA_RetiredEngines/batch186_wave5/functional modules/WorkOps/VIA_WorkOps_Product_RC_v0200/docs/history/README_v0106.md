# VIA WorkOps Smart Workflow v0106 — Accuracy First

This release does not primarily add workflow features. It adds a central accuracy control plane.

## New engines
- ENG-046 Evidence Integrity & Contradiction Guard
- ENG-047 Confidence Calibration & Accuracy Gate
- ENG-048 Feedback Weight Optimizer
- ENG-049 Evidence-based Progress Estimator
- ENG-050 Project Health & Accuracy Aggregator

## Accuracy rules
1. Evidence beats inference.
2. User-confirmed classification remains authoritative.
3. Independent signal diversity raises confidence.
4. Candidate score margin matters.
5. Contradictions fail closed for high-impact decisions.
6. Progress is estimated from evidence-backed components and shown beside user-entered progress; it never silently replaces it.
7. Feedback learning only proposes JSON weight overlays. It never mutates canonical parameters automatically.

## New UI
`ui/accuracy_center.html`
- Project Health
- Accuracy Confidence
- Evidence Coverage
- Contradictions
- User vs System Progress Delta
- Review-required filtering

## Recommended accuracy chain
ENG-032 Project Fusion
→ ENG-046 Integrity Guard
→ ENG-047 Confidence Calibration
→ Human Confirm
→ ENG-048 Feedback Weight Proposal
→ ENG-049 Evidence Progress
→ ENG-050 Health + Accuracy
→ Project Cockpit / Accuracy Center

## Important
No project classification is automatically confirmed.
No progress value is silently overwritten.
No closure passes when evidence contradictions exist.
