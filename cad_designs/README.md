# CAD Files

All dimensions are millimeters. The x-axis is guide depth; the y-z plane is the 120 × 120 mm fan face.

| File pair | Description | Print status |
|---|---|---|
| `design_A_low_blockage` | 20 mm, six straight 1.5 mm vanes | First-cycle prototype candidate |
| `design_B_angled_guide` | 25 mm, eight 14° biased 2.0 mm vanes | Comparison design; lower priority |
| `design_C_balanced_revision` | 22 mm, six 9° biased 1.35 mm vanes | First-cycle prototype candidate |
| `fan_reference` | Dimensional frame and hub reference | Reference assembly, not a print recommendation |

The three guide STLs are each one connected, watertight manifold component. Their vanes overlap the hub and frame before the final Boolean union. `fan_reference` intentionally contains a separate hub because it represents the fan's inactive center rather than a printable guide.

Regenerate the exports from the repository root:

```bash
npm install
npm run cad
```

Print the guide with a 120 × 120 mm face on the bed and inspect the slicer preview before committing material. Hole fit, screw length, material choice, fan clearance, and case-specific mounting still require a physical check.
