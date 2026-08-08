# Physical Test Plan

The CFD screen leaves two useful prototypes: Design A and Design C. This procedure compares them against the unmodified fan without turning a single temperature reading into a cooling claim.

## Configurations

1. Baseline fan with no guide
2. Design A, mounted in the same position
3. Design C, mounted in the same position

Design B is not part of the first print cycle because it combines the highest blockage with the weakest downstream axial result.

## Controlled conditions

- Same room and PC location
- Same case panels, filter state, cable positions, and fan orientation
- Same fan-control curve or fixed PWM setting
- Same CPU/GPU workload and duration
- Same monitoring software and logging interval
- Same sound-measurement position, if noise is recorded
- A cooldown to a comparable starting temperature before each run

Record ambient temperature. Compare component temperature rise above ambient, not raw temperature alone.

## Procedure

1. Power the PC down and install the configuration.
2. Rotate the fan by hand to confirm full blade clearance.
3. Check that every fastener has positive retention and that the guide cannot shift toward the rotor.
4. Boot the PC and record idle fan RPM, vibration, and unusual noise.
5. Run the same combined CPU/GPU workload for 20 minutes.
6. Log ambient, CPU, GPU, fan RPM, and noise observations once per minute.
7. Use the final five minutes to calculate the steady-state average.
8. Return the system to a comparable starting temperature.
9. Repeat each configuration three times and rotate the test order if time permits.

## Decision fields

- Mechanical fit and blade clearance
- Mount stability after the run
- CPU temperature rise above ambient
- GPU temperature rise above ambient
- Fan RPM at the controlled setting
- New tonal noise, rattle, or vibration
- Repeatability across runs
- Whether observed airflow direction matches the intended guide behavior

## Stop conditions

Stop immediately for rotor contact, guide movement, abnormal vibration, burning smell, unexpected fan stoppage, or a temperature outside the PC's established safe operating range.

The selected design should earn its place through repeatable physical evidence. If neither guide improves the combined thermal/noise result, the baseline remains the correct engineering choice.
