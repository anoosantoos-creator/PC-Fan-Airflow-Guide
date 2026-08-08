# CFD Method and Limitations

## Question

How do three short guide geometries change the sampled downstream velocity field and pressure-demand indicator of a measured 120 mm intake-fan setup?

The model screens concepts for prototyping. It does not predict component temperature.

## Geometry and domain

- Rectangular domain: 350 mm downstream length, 200 × 200 mm cross-section
- Fan plane: x = 0 mm
- Target planes: x = 100, 130, and 350 mm
- Active inlet annulus: radius 20–52.5 mm
- Nominal inlet velocity: 2.5 m/s in the +x direction
- Side boundaries: no-slip walls
- Outlet: fixed pressure with zero-gradient velocity
- Guide surfaces: no-slip walls

The CPU and GPU distances are approximate locations, not modeled component surfaces. The case, cables, coolers, filter, rotor blades, and thermal sources are absent.

## Solver setup recorded in the logs

- OpenFOAM 13
- Steady incompressible `simpleFoam`
- `kOmegaSST` RANS turbulence model
- Base cells: approximately 4 mm
- Guide-region refinement: approximately 2 mm
- No boundary-layer cells
- 200 iterations per case
- `blockMesh`, `snappyHexMesh` for guide cases, `checkMesh`, solve, then target-plane sampling

The four `checkMesh` logs report `Mesh OK`. Cell count and mesh-quality metrics are extracted into [`../results/mesh_quality_summary.csv`](../results/mesh_quality_summary.csv).

## Published metrics

For each uniformly sampled plane, the analysis calculates:

- mean axial velocity, \(\overline{U_x}\)
- mean velocity magnitude, \(\overline{|U|}\)
- mean transverse speed, \(\overline{\sqrt{U_y^2+U_z^2}}\)
- fraction of points with \(U_x < 0\)
- mean kinematic pressure at the plane

The pressure-demand indicator is

\[
\left|\overline{p}_{100}-\overline{p}_{350}\right|,
\]

reported in OpenFOAM's kinematic-pressure units and converted to an equivalent pressure using \(\rho = 1.20\ \text{kg/m}^3\). It is useful only for comparison inside this model.

All values in [`../results/cfd_summary.csv`](../results/cfd_summary.csv) are recalculated directly from the archived `.xy` files by [`../scripts/analyze_openfoam_samples.py`](../scripts/analyze_openfoam_samples.py).

## CAD revision after the CFD pass

The first CAD exports contained disconnected vane bodies. The printable revision extends each vane through the measured active annulus and overlaps it with the hub and frame before performing a solid union. This changes the estimated geometric blockage slightly:

| Design | CFD-geometry estimate | Printable-CAD estimate |
|---|---:|---:|
| A | 3.4% | 3.95% |
| B | 6.2% | 7.02% |
| C | 3.1% | 3.56% |

The added material is at the inner and outer vane connections. The archived flow fields were not rerun with that manufacturing revision, so the numerical comparison remains a screening pass rather than final validation.

## Result quality

The logs show successful meshing and completion of 200 solver iterations. They do not establish solution convergence. Several last-iteration initial residuals remain around \(10^{-2}\), and no mesh-refinement study or inlet-velocity sensitivity study was completed. See [`../results/solver_residual_summary.csv`](../results/solver_residual_summary.csv).

The figures are target-plane sampled fields, not streamlines. No image in this repository is labeled as a streamline result.

## What the data supports

- comparing the four archived fixed-iteration cases under the same nominal inlet setup
- identifying pressure, reverse-flow, and axial-retention trade-offs
- choosing Designs A and C for the next physical test

## What the data does not support

- claiming lower CPU or GPU temperatures
- claiming a final design winner
- predicting absolute fan flow or pressure
- treating the local duct as the full PC interior
- treating the 200-iteration fields as convergence-certified CFD
- claiming that the revised printable connectors were numerically validated

## Reproduction boundary

The archive contains target-plane samples and mesh/solver logs. It does not contain the original OpenFOAM case dictionaries or volume fields. The published analysis and figures are reproducible from this repository; the exact CFD solve is not. A future rerun should publish complete cases, residual criteria, a mesh study, and the revised printable geometry.
