# PC Fan Airflow Guide

A measured 120 mm intake-fan project comparing three internal airflow guides. The repository contains parametric CAD, printable STEP/STL exports, complete OpenFOAM 13 cases, raw rerun evidence, and scripts that recalculate every published table and figure.

The goal is narrow: determine which concepts are worth printing and testing. The CFD does **not** prove lower CPU or GPU temperatures.

![CFD screening trade-offs](results/figures/screening_tradeoffs.png)

## Current result

The printable-geometry rerun leaves two useful physical prototypes:

- **Design A** is the straight-vane control. It has low printable blockage and the smallest mean transverse component at the 130 mm target plane.
- **Design C** is the balanced directional candidate. It has the lowest pressure-demand indicator, low printable blockage, and a transverse component between A and B at 130 mm.
- **Design B** remains the aggressive comparison. It has the lowest average reverse-flow fraction, but also the highest blockage, pressure-demand indicator, and 130 mm transverse component among the guides.

No design is declared final. The next decision requires a baseline-versus-A-versus-C physical test.

| Case | Printable blockage estimate | Pressure-demand indicator* | Mean reverse-flow samples | Transverse speed at 130 mm |
|---|---:|---:|---:|---:|
| Baseline | 0.00% | 0.245 Pa | 41.3% | 0.0823 m/s |
| Design A | 3.95% | 0.248 Pa | 41.1% | 0.0745 m/s |
| Design B | 7.02% | 0.259 Pa | 39.7% | 0.1066 m/s |
| Design C | 3.56% | 0.229 Pa | 40.4% | 0.0924 m/s |

\* OpenFOAM stores kinematic pressure for this incompressible setup. The table converts the sampled pressure difference using an assumed air density of 1.20 kg/m³. Treat it as a comparison indicator, not a fan-pressure measurement.

The full calculation is in [`results/cfd_summary.csv`](results/cfd_summary.csv). Mean axial velocity at 350 mm is within 0.01% across all four cases because the closed duct and equal inlet flow constrain that plane average; it is a mass-flow check, not a design-ranking metric. All four runs reached the 800-iteration limit before satisfying every strict residual control, and no mesh-independence study has been completed. Those limitations are carried into the decision instead of being hidden.

## Designs

| Design | Depth | Vanes | Bias | Vane thickness | Intended role |
|---|---:|---:|---:|---:|---|
| A — low blockage | 20 mm | 6 | 0° | 1.50 mm | Straight-vane control candidate |
| B — angled guide | 25 mm | 8 | 14° | 2.00 mm | High-blockage comparison |
| C — balanced revision | 22 mm | 6 | 9° | 1.35 mm | Balanced directional candidate |

All three printable exports are single connected solids, watertight, manifold, and confined to their declared depth. The vanes overlap both the central hub and outer frame so they do not float as separate bodies.

## Rebuild and check

Requirements:

- Node.js 20 or newer for CAD export
- Python 3.10 or newer for analysis
- OpenFOAM 13 only when rebuilding the CFD solutions

```bash
npm ci
python -m pip install -r requirements.txt
npm run check
```

Individual commands:

```bash
npm run cad
npm run cfd:prepare
npm run analysis
npm run validate
```

To rebuild the meshes and solutions from a clean OpenFOAM 13 shell:

```bash
CFD_JOBS=4 CFD_RUN_ROOT=/path/to/new/run-directory npm run cfd:run
npm run cfd:collect -- /path/to/new/run-directory
npm run analysis
npm run validate
```

The validation step checks STL envelopes and topology, complete case inputs, CAD-to-CFD geometry identity, raw solver evidence, recalculated CFD values, local document links, and the public tree.

## Repository map

- [`cad_designs/`](cad_designs/) — printable STEP/STL files and a dimensional fan reference
- [`scripts/generate_cad.cjs`](scripts/generate_cad.cjs) — parametric CAD source
- [`openfoam_cases/`](openfoam_cases/) — complete OpenFOAM inputs and one-command case runners
- [`data/`](data/) — current and original OpenFOAM target-plane samples and run logs
- [`scripts/run_openfoam_cases.sh`](scripts/run_openfoam_cases.sh) — clean four-case meshing, solving, and sampling pipeline
- [`scripts/analyze_openfoam_samples.py`](scripts/analyze_openfoam_samples.py) — table and figure generation
- [`results/`](results/) — corrected summaries, mesh checks, residuals, and figures
- [`docs/measurements.md`](docs/measurements.md) — measured fan and case constraints
- [`docs/cfd_method.md`](docs/cfd_method.md) — numerical method, provenance, and limitations
- [`docs/physical_test_plan.md`](docs/physical_test_plan.md) — repeatable prototype test procedure
- [`docs/sources.md`](docs/sources.md) — technical references

## Safety and scope

Power the PC down before installation. Confirm blade clearance by hand, secure the guide mechanically, and stop testing if the guide shifts, touches the rotor, or causes abnormal vibration or temperature.

This is an airflow-screening and prototyping project. It is not a certified thermal product or a universal fit for every 120 mm fan.

## License

Released under the [MIT License](LICENSE).
