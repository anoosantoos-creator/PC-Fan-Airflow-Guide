# Complete OpenFOAM cases

This directory contains the complete inputs for the current OpenFOAM 13 rerun.
Each case includes initial fields, physical and turbulence properties, meshing
dictionaries, the metre-scale obstruction STL, solver controls, sampling
controls, and an executable `Allrun` script.

| Case | Solid geometry |
|---|---|
| `baseline_no_guide` | Measured fan frame and inactive hub |
| `design_A_low_blockage` | Current connected Design A STL |
| `design_B_angled_guide` | Current connected Design B STL |
| `design_C_balanced_revision` | Current connected Design C STL |

## Rebuild the cases

The tracked case surfaces are deterministic metre-scale copies of the
printable STLs:

```bash
npm run cad
npm run cfd:prepare
```

## Run all four cases

Start an OpenFOAM 13 shell, then run:

```bash
CFD_JOBS=4 CFD_RUN_ROOT=/path/to/new/run-directory npm run cfd:run
```

`CFD_JOBS` may be 1 through 4. The run directory must not already exist. A
temporary directory is created when `CFD_RUN_ROOT` is omitted.

To run one case in place instead:

```bash
cd openfoam_cases/design_A_low_blockage
./Allrun
```

The pipeline executes `blockMesh`, `surfaceCheck`, `snappyHexMesh`,
`createPatch`, `checkMesh`, `foamRun -solver incompressibleFluid`, and
`foamPostProcess`. The native `createPatch` step separates the active
20--52.5 mm inlet annulus from the blocked fan-face area without compiled
boundary code.

## Numerical layout

- Domain: x = -4 to 396 mm; y and z = -100 to 100 mm
- Base mesh: 4 mm cells; local guide refinement down to about 1 mm
- Inlet: 2.5 m/s on the active annulus; blocked elsewhere
- Outlet: fixed kinematic pressure at zero
- Walls and solid geometry: no slip
- Model: steady incompressible RANS with `kOmegaSST`
- Limit: 800 iterations, with residual controls for earlier termination
- Samples: raw `U` and `p` on fixed 50 × 50 grids at x = 100, 130, and 350 mm

Generated meshes and volume fields are run outputs, not case inputs, and are
therefore kept out of the tracked case directories. The dictionaries and
surfaces needed to regenerate them are all included.
