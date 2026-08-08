# Results

The tables and figures in this directory are rebuilt from the archived OpenFOAM target-plane samples and logs.

- `cfd_summary.csv` — corrected velocity, pressure-demand, reverse-flow, and blockage comparison
- `mesh_quality_summary.csv` — values extracted from each `checkMesh.log`
- `solver_residual_summary.csv` — last-iteration initial residuals and continuity error
- `figures/` — shared-scale velocity maps and the screening trade-off chart

## Interpretation

Design A has the lowest pressure-demand indicator but does not reduce the average sampled reverse-flow fraction. Design C has the lowest reverse-flow fraction and the highest downstream axial retention among the guides, but its pressure demand and transverse velocity are substantially higher. Design B does not lead a useful category strongly enough to justify first-cycle printing.

That leaves A and C as deliberately different physical prototypes. The data does not justify naming either one the final design.

The four runs stopped at 200 iterations. The residual summary is published because a completed solver log is not the same thing as demonstrated convergence.
