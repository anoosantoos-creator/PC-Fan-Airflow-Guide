# Technical Sources

## OpenFOAM

- [OpenFOAM 13 release and platform downloads](https://openfoam.org/version/13/)
- [OpenFOAM 13 installation on Ubuntu](https://openfoam.org/download/13-ubuntu/)
- [OpenFOAM on Windows through WSL](https://openfoam.org/download/windows/)
- [OpenFOAM v13 solver modules](https://doc.cfd.direct/openfoam/user-guide-v13/solvers-modules)
- [SIMPLE and solution controls](https://doc.cfd.direct/openfoam/user-guide-v13/fvsolution)
- [`snappyHexMesh` workflow and mesh controls](https://doc.cfd.direct/openfoam/user-guide-v13/snappyhexmesh)
- [Post-processing surfaces and streamlines](https://doc.cfd.direct/openfoam/user-guide-v13/post-processing-functionality)

## Turbulence model

- F. R. Menter, “Two-Equation Eddy-Viscosity Turbulence Models for Engineering Applications,” *AIAA Journal*, 32(8), 1598–1605, 1994. [DOI: 10.2514/3.12149](https://doi.org/10.2514/3.12149)

## Parametric CAD

- [Replicad library setup](https://replicad.xyz/docs/use-as-a-library)
- [Replicad solid export API](https://replicad.xyz/docs/api/classes/Solid/)

## Project-specific evidence

- Direct fan and case measurements are recorded in [`measurements.md`](measurements.md).
- The nominal inlet velocity is an explicit model assumption, not a manufacturer specification.
- Raw sampled fields and solver logs are preserved under [`../data/`](../data/).
- Recalculated tables and residual summaries are preserved under [`../results/`](../results/).
