# OpenFOAM evidence

The current printable-geometry rerun is stored in `rerun_v2/`:

- `run_manifest.json` records the OpenFOAM build, final iteration, convergence
  status, mesh check, and sampled time for every case.
- `openfoam_logs/` contains the complete meshing, patch-creation, mesh-check,
  solver, and sampling logs.
- `openfoam_samples/` contains the raw x-y-z position, velocity components,
  and kinematic pressure on fixed 50 × 50 grids at the 100, 130, and 350 mm
  target planes.

Each target-plane `.xy` file has seven columns:

```text
point_x point_y point_z U_x U_y U_z p
```

The top-level `openfoam_logs/` and `openfoam_samples/` directories preserve the
original 200-iteration v1 screening evidence. They are retained for provenance
but are no longer the source for the published tables and figures. The v1
printable connectors were revised after those runs, and its original case
dictionaries were unavailable.

The complete v2 inputs are tracked in [`../openfoam_cases/`](../openfoam_cases/).
After a clean solve, `npm run cfd:collect -- /path/to/run-directory` rebuilds
`rerun_v2/` from the completed run. Run `npm run analysis` to rebuild the
public results from that evidence.
