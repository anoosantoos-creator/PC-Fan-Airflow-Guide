# CFD Method

## Question

How do three short guide geometries change the sampled downstream velocity
field and pressure-demand indicator of a measured 120 mm intake-fan setup?

The model screens concepts for prototyping. It does not predict component
temperature.

## Current geometry

The v2 rerun uses the current printable solids rather than the disconnected
vane bodies from the first screening pass.

- Baseline: measured 25 mm fan frame and inactive 40 mm hub
- Design A: current connected 20 mm, six-vane STL
- Design B: current connected 25 mm, eight-vane STL
- Design C: current connected 22 mm, six-vane STL

Every tracked simulation surface is a deterministic metre-scale copy of its
source STL in `cad_designs/`. `surfaceCheck` reports every surface closed; the
three printable guides are each one connected part. The baseline frame and hub
are intentionally two closed parts.

## Domain and boundaries

- Rectangular domain: x = -4 to 396 mm; y and z = -100 to 100 mm
- Physical fan/guide plane: x = 0 mm
- Target planes: x = 100, 130, and 350 mm
- Active inlet annulus: radius 20--52.5 mm
- Active-annulus velocity: 2.5 m/s in the +x direction
- Blocked inlet area, duct sides, and solids: no-slip walls
- Outlet: zero kinematic pressure with an inlet/outlet velocity condition

The 4 mm inlet offset prevents the obstruction surface from being coincident
with a velocity boundary. Extending the outlet to 396 mm keeps the 350 mm
target plane inside the volume instead of sampling on the outlet boundary.
`createPatch` makes the active annulus from native mesh faces, so the setup
does not require compiled boundary code.

The case, cables, coolers, filter, rotor blades, thermal sources, and
manufacturer fan curve are absent. The nominal inlet velocity remains an
equal-input assumption.

## Flow model

- OpenFOAM 13, build recorded in `data/rerun_v2/run_manifest.json`
- Steady incompressible solver module (`foamRun -solver incompressibleFluid`)
- `kOmegaSST` RANS turbulence model
- Kinematic viscosity: 1.5e-5 m²/s
- Inlet turbulence intensity: 5%
- Turbulence mixing length: 4.55 mm
- Maximum 800 SIMPLE iterations
- Residual controls: p = 1e-4; U, k, and omega = 1e-5

The solver can terminate before iteration 800 only when all residual controls
are satisfied. The manifest and residual table distinguish convergence from an
iteration-limit stop for each case. All four published runs reached iteration
800 before satisfying every control; the last residuals remain available in
[`../results/solver_residual_summary.csv`](../results/solver_residual_summary.csv).

## Mesh and sampling

The background mesh uses 4 mm hexahedra. Cells around the fan and guides are
refined, with surface cells down to about 1 mm. Boundary layers are not added.
The pipeline is:

1. `blockMesh`
2. `surfaceCheck`
3. `snappyHexMesh`
4. `createPatch`
5. `checkMesh`
6. `foamRun -solver incompressibleFluid`
7. `foamPostProcess -dict system/sampleDict -latestTime`

All four standard `checkMesh` runs must report `Mesh OK` before their results
are collected. The detailed cell count and quality values are extracted into
[`../results/mesh_quality_summary.csv`](../results/mesh_quality_summary.csv).

The post-processor interpolates `U` and kinematic `p` onto a fixed 50 × 50
cell-center grid at each target plane. The y and z coordinates run from
-98 to 98 mm at 4 mm spacing, so every case is compared at the same 2,500
locations regardless of local mesh refinement. Each row has seven columns:

```text
point_x point_y point_z U_x U_y U_z p
```

## Published metrics

For each plane, the analysis calculates:

- mean axial velocity, mean velocity magnitude, and mean transverse speed
- fraction of points with negative axial velocity
- mean kinematic pressure
- downstream axial retention relative to the v2 baseline

Because every case has the same fixed inlet flow and a closed duct, the
whole-plane downstream mean axial velocity is expected to be nearly identical.
Axial retention is therefore a mass-flow consistency check, not a design
ranking metric. Pressure demand, reverse-flow sampling, and transverse-speed
differences provide the comparative screen.

The pressure-demand indicator is

\[
\left|\overline{p}_{100}-\overline{p}_{350}\right|.
\]

OpenFOAM stores kinematic pressure for this setup. The table multiplies the
indicator by an assumed air density of 1.20 kg/m³ to show an equivalent
pressure in pascals. It is a comparison inside this model, not a fan-pressure
measurement.

## Reproduction

The complete v2 cases are included in [`../openfoam_cases/`](../openfoam_cases/).
They contain every initial field, physical property, turbulence setting,
meshing dictionary, solver control, sampling control, and obstruction surface
needed to rebuild the meshes and rerun the solves. `npm run cfd:run` executes
all four cases; [`../scripts/run_openfoam_cases.sh`](../scripts/run_openfoam_cases.sh)
is the command-level record.

Raw v2 logs and sampled fields are under [`../data/rerun_v2/`](../data/rerun_v2/).
The original v1 evidence remains under the top-level data directories for
provenance, but it is not used for the current figures or tables.

## Interpretation boundary

The rerun supports equal-input comparison of these four local duct models. It
does not establish temperature improvement, a real fan operating point, mesh
independence, turbulence-model independence, or universal fit. A physical
baseline-versus-prototype test remains the deciding experiment.
