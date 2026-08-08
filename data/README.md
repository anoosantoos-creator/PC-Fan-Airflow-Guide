# Archived OpenFOAM Evidence

This directory preserves the numerical evidence available from the first CFD pass.

- `openfoam_samples/` contains x-y-z position, velocity components, and kinematic pressure at x = 100, 130, and 350 mm for all four cases.
- `openfoam_logs/` contains meshing, mesh-check, solver, and sampling logs.

Each target-plane `.xy` file has seven columns:

```text
point_x point_y point_z U_x U_y U_z p
```

The samples and logs support recalculating the tables, checking mesh statistics, and inspecting last-iteration residuals. They do not reconstruct the exact solve because the original OpenFOAM dictionaries and volume fields are not part of the archive.

Run `npm run analysis` from the repository root to rebuild the public results.
