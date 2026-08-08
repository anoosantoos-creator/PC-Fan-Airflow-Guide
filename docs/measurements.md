# Baseline Measurements

These dimensions were taken from the fan and PC interior before the first design pass.

## Direct measurements

| Item | Value |
|---|---:|
| Fan outer frame | 120 × 120 mm |
| Active blade/opening diameter | 105 mm |
| Central hub diameter | 40 mm |
| Fan thickness | 25 mm |
| Screw-hole spacing | 105 × 105 mm |
| Screw-hole diameter | approximately 4.9 mm |
| Available guide depth | approximately 20–25 mm |
| Fan center to CPU-cooler area | approximately 100 mm |
| Fan center to GPU region | approximately 130 mm |
| Straight internal path after fan | approximately 350 mm |

The fan is installed as an intake. The guide sits inside the case, downstream of the rotor. The intake mesh can be removed.

## Mounting constraint

The internal screw holes are accessible but are not threaded. The CAD therefore uses through-holes at the measured spacing; installation will require longer screws with nuts, another positive-retention fastener, or a later clip revision. A friction-only mount is not acceptable near the rotor.

## Derived CFD input

The measured active annulus is bounded by a 20 mm hub radius and a 52.5 mm opening radius:

\[
A = \pi(0.0525^2 - 0.0200^2) = 0.007402\ \text{m}^2
\]

The current OpenFOAM comparison uses a nominal 2.5 m/s axial inlet over that annulus:

\[
Q = AU \approx 0.0185\ \text{m}^3/\text{s} \approx 39\ \text{CFM}
\]

The velocity is an equal-input assumption for comparing designs. It was not measured from the fan and was not taken from a manufacturer fan curve.

## Evidence still needed

- A ruler/caliper photo for each critical dimension
- An installed-fit photograph showing rotor and component clearance
- The exact fan model and manufacturer pressure-flow data, if available
- A final fastener and retention check before powered testing
