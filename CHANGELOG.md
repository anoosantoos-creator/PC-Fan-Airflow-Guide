# Changelog

## 0.2.0 — 2026-08-09

- Added complete OpenFOAM 13 cases for the baseline and all three printable guides.
- Added deterministic case generation, four-case execution, and evidence-collection scripts.
- Rebuilt the meshes from the current STL exports and required every standard `checkMesh` run to report `Mesh OK`.
- Reran all four steady simulations with native annular inlet patches and an 800-iteration limit.
- Rebuilt the published tables and figures from fixed-grid target-plane samples and solver logs.
- Expanded validation to check case completeness, CAD-to-CFD geometry identity, raw sample dimensions, and run evidence.
- Preserved the original screening evidence as provenance while making the printable-geometry rerun the current result set.

## 0.1.0 — 2026-08-08

- Rebuilt all three guide models as single connected solids.
- Extended vanes into the hub and frame so the exports are physically printable.
- Kept Designs A, B, and C within 20 mm, 25 mm, and 22 mm depth envelopes.
- Recalculated pressure as a positive comparison indicator with explicit units.
- Replaced the single-winner claim with an A-versus-C prototype decision.
- Added solver-residual and mesh-quality summaries.
- Replaced misleading streamline filenames with sampled-plane velocity figures.
- Removed local-machine paths and non-public working files.
- Added automated CAD, data, link, and public-text validation.
