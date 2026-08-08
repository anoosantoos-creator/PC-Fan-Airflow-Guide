# Results

The tables and figures in this directory are rebuilt from the current OpenFOAM printable-geometry rerun.

- `cfd_summary.csv` — corrected velocity, pressure-demand, reverse-flow, and blockage comparison
- `mesh_quality_summary.csv` — values extracted from each `checkMesh.log`
- `solver_residual_summary.csv` — last-iteration initial residuals and continuity error
- `figures/` — shared-scale velocity maps and the screening trade-off chart

## Interpretation

Design A has the smallest mean transverse component at the 130 mm target plane and retains a low-blockage straight-vane geometry. Design C has the lowest pressure-demand indicator and adds a moderate directional component with slightly lower blockage than A. Design B has the lowest average reverse-flow fraction, but it also has the highest blockage, pressure-demand indicator, and 130 mm transverse component among the guides.

That leaves A and C as deliberately different physical prototypes. The data does not justify naming either one the final design.

The fixed inlet flow makes whole-plane mean axial velocity nearly identical downstream, so axial retention is treated as a mass-flow consistency check rather than a ranking metric. All four runs reached 800 iterations before every strict residual control was satisfied. The residual summary is published because a completed solver log is not the same thing as demonstrated convergence.
