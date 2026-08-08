#!/usr/bin/env python3
"""Build deterministic, runnable OpenFOAM 13 cases from the printable STLs."""

from __future__ import annotations

import json
import struct
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAD_ROOT = ROOT / "cad_designs"
CASE_ROOT = ROOT / "openfoam_cases"

CASES = {
    "baseline_no_guide": {
        "label": "Baseline",
        "source": "fan_reference.stl",
        "description": "Measured fan frame and inactive hub, without guide vanes.",
    },
    "design_A_low_blockage": {
        "label": "Design A",
        "source": "design_A_low_blockage.stl",
        "description": "Current connected 20 mm guide with six straight vanes.",
    },
    "design_B_angled_guide": {
        "label": "Design B",
        "source": "design_B_angled_guide.stl",
        "description": "Current connected 25 mm guide with eight 14 degree vanes.",
    },
    "design_C_balanced_revision": {
        "label": "Design C",
        "source": "design_C_balanced_revision.stl",
        "description": "Current connected 22 mm guide with six 9 degree vanes.",
    },
}


def cleaned(text: str) -> str:
    return textwrap.dedent(text).lstrip()


U = cleaned(
    r"""
    FoamFile
    {
        format      ascii;
        class       volVectorField;
        location    "0";
        object      U;
    }

    dimensions      [0 1 -1 0 0 0 0];

    // Uniform initialization estimate. The prescribed mass flow comes from
    // the fixed 20--52.5 mm annular inlet patch below.
    internalField   uniform (0.52 0 0);

    boundaryField
    {
        fan_active_annulus
        {
            type            fixedValue;
            value           uniform (2.5 0 0);
        }

        inlet_blocked
        {
            type            noSlip;
        }

        outlet
        {
            type            inletOutlet;
            inletValue      uniform (0 0 0);
            value           uniform (0.52 0 0);
        }

        walls
        {
            type            noSlip;
        }

        solidSurfaces
        {
            type            noSlip;
        }
    }
    """
)

P = cleaned(
    """
    FoamFile
    {
        format      ascii;
        class       volScalarField;
        location    "0";
        object      p;
    }

    dimensions      [0 2 -2 0 0 0 0];
    internalField   uniform 0;

    boundaryField
    {
        fan_active_annulus
        {
            type            zeroGradient;
        }
        inlet_blocked
        {
            type            zeroGradient;
        }
        outlet
        {
            type            fixedValue;
            value           uniform 0;
        }
        walls
        {
            type            zeroGradient;
        }
        solidSurfaces
        {
            type            zeroGradient;
        }
    }
    """
)

K = cleaned(
    """
    FoamFile
    {
        format      ascii;
        class       volScalarField;
        location    "0";
        object      k;
    }

    dimensions      [0 2 -2 0 0 0 0];
    internalField   uniform 0.0234375;

    boundaryField
    {
        fan_active_annulus
        {
            type            turbulentIntensityKineticEnergyInlet;
            intensity       0.05;
            value           uniform 0.0234375;
        }
        inlet_blocked
        {
            type            kqRWallFunction;
            value           uniform 0.0234375;
        }
        outlet
        {
            type            inletOutlet;
            inletValue      uniform 0.0234375;
            value           uniform 0.0234375;
        }
        walls
        {
            type            kqRWallFunction;
            value           uniform 0.0234375;
        }
        solidSurfaces
        {
            type            kqRWallFunction;
            value           uniform 0.0234375;
        }
    }
    """
)

OMEGA = cleaned(
    """
    FoamFile
    {
        format      ascii;
        class       volScalarField;
        location    "0";
        object      omega;
    }

    dimensions      [0 0 -1 0 0 0 0];
    internalField   uniform 61.5;

    boundaryField
    {
        fan_active_annulus
        {
            type            turbulentMixingLengthFrequencyInlet;
            mixingLength    0.00455;
            value           uniform 61.5;
        }
        inlet_blocked
        {
            type            omegaWallFunction;
            value           uniform 61.5;
        }
        outlet
        {
            type            inletOutlet;
            inletValue      uniform 61.5;
            value           uniform 61.5;
        }
        walls
        {
            type            omegaWallFunction;
            value           uniform 61.5;
        }
        solidSurfaces
        {
            type            omegaWallFunction;
            value           uniform 61.5;
        }
    }
    """
)

NUT = cleaned(
    """
    FoamFile
    {
        format      ascii;
        class       volScalarField;
        location    "0";
        object      nut;
    }

    dimensions      [0 2 -1 0 0 0 0];
    internalField   uniform 0;

    boundaryField
    {
        fan_active_annulus
        {
            type            calculated;
            value           uniform 0;
        }
        inlet_blocked
        {
            type            nutkWallFunction;
            value           uniform 0;
        }
        outlet
        {
            type            calculated;
            value           uniform 0;
        }
        walls
        {
            type            nutkWallFunction;
            value           uniform 0;
        }
        solidSurfaces
        {
            type            nutkWallFunction;
            value           uniform 0;
        }
    }
    """
)

PHYSICAL_PROPERTIES = cleaned(
    """
    FoamFile
    {
        format      ascii;
        class       dictionary;
        location    "constant";
        object      physicalProperties;
    }

    viscosityModel  constant;
    nu              [0 2 -1 0 0 0 0] 1.5e-05;
    """
)

MOMENTUM_TRANSPORT = cleaned(
    """
    FoamFile
    {
        format      ascii;
        class       dictionary;
        location    "constant";
        object      momentumTransport;
    }

    simulationType  RAS;

    RAS
    {
        model           kOmegaSST;
        turbulence      on;
    }
    """
)

BLOCK_MESH_DICT = cleaned(
    """
    FoamFile
    {
        format      ascii;
        class       dictionary;
        object      blockMeshDict;
    }

    scale 1;

    // A 4 mm inlet offset prevents the solid from being coincident with the
    // velocity boundary. The 46 mm outlet extension keeps x=350 mm internal.
    vertices
    (
        (-0.004 -0.1 -0.1)
        ( 0.396 -0.1 -0.1)
        ( 0.396  0.1 -0.1)
        (-0.004  0.1 -0.1)
        (-0.004 -0.1  0.1)
        ( 0.396 -0.1  0.1)
        ( 0.396  0.1  0.1)
        (-0.004  0.1  0.1)
    );

    blocks
    (
        hex (0 1 2 3 4 5 6 7) (100 50 50) simpleGrading (1 1 1)
    );

    edges ();

    boundary
    (
        inlet_blocked
        {
            type wall;
            faces ((0 4 7 3));
        }
        outlet
        {
            type patch;
            faces ((1 2 6 5));
        }
        walls
        {
            type wall;
            faces
            (
                (0 1 5 4)
                (3 7 6 2)
                (0 3 2 1)
                (4 5 6 7)
            );
        }
    );

    mergePatchPairs ();
    """
)

SNAPPY_HEX_MESH_DICT = cleaned(
    """
    FoamFile
    {
        format      ascii;
        class       dictionary;
        object      snappyHexMeshDict;
    }

    castellatedMesh true;
    snap            true;
    addLayers       false;

    geometry
    {
        obstruction
        {
            type triSurface;
            file "obstruction.stl";
        }

        guideRegion
        {
            type box;
            min (-0.002 -0.065 -0.065);
            max ( 0.030  0.065  0.065);
        }
    }

    castellatedMeshControls
    {
        maxLocalCells       1200000;
        maxGlobalCells      1200000;
        minRefinementCells  10;
        maxLoadUnbalance    0.10;
        nCellsBetweenLevels 2;

        features ();

        refinementSurfaces
        {
            obstruction
            {
                level (1 2);
                patchInfo
                {
                    type wall;
                    inGroups (solidSurfaces);
                }
            }
        }

        resolveFeatureAngle 30;

        refinementRegions
        {
            guideRegion
            {
                mode inside;
                level 1;
            }
        }

        insidePoint (0.2 0 0);
        allowFreeStandingZoneFaces true;
    }

    snapControls
    {
        nSmoothPatch        5;
        tolerance           1.0;
        nSolveIter          100;
        nRelaxIter          10;
        nFeatureSnapIter    0;
        implicitFeatureSnap false;
        explicitFeatureSnap false;
        multiRegionFeatureSnap false;
    }

    addLayersControls
    {
        relativeSizes true;
        layers {};
        expansionRatio 1.0;
        finalLayerThickness 0.3;
        minThickness 0.1;
        nGrow 0;
        featureAngle 100;
        slipFeatureAngle 30;
        nRelaxIter 3;
        nSmoothSurfaceNormals 1;
        nSmoothNormals 3;
        nSmoothThickness 10;
        maxFaceThicknessRatio 0.5;
        maxThicknessToMedialRatio 0.3;
        minMedianAxisAngle 90;
        nBufferCellsNoExtrude 0;
        nLayerIter 50;
    }

    meshQualityControls
    {
        #include "meshQualityDict"
    }

    writeFlags (scalarLevels);
    mergeTolerance 1e-6;
    """
)

CREATE_PATCH_DICT = cleaned(
    """
    FoamFile
    {
        format      ascii;
        class       dictionary;
        location    "system";
        object      createPatchDict;
    }

    // Split the active fan annulus from the blocked part of the inlet. Using
    // a native zone generator avoids run-time compilation of a coded field.
    patches
    {
        fan_active_annulus
        {
            patchInfo
            {
                type patch;
            }

            constructFrom zone;

            zone
            {
                type        annulus;
                zoneType    face;
                point1      (-0.0041 0 0);
                point2      (-0.0039 0 0);
                outerRadius 0.0525;
                innerRadius 0.0200;
            }
        }
    }
    """
)

MESH_QUALITY_DICT = cleaned(
    """
    FoamFile
    {
        format      ascii;
        class       dictionary;
        object      meshQualityDict;
    }

    #includeEtc "caseDicts/mesh/generation/meshQualityDict"
    minFaceWeight 0.02;
    """
)

CONTROL_DICT = cleaned(
    """
    FoamFile
    {
        format      ascii;
        class       dictionary;
        location    "system";
        object      controlDict;
    }

    solver          incompressibleFluid;
    startFrom       startTime;
    startTime       0;
    stopAt          endTime;
    endTime         800;
    deltaT          1;

    writeControl    timeStep;
    writeInterval   25;
    purgeWrite      2;
    writeFormat     binary;
    writePrecision  8;
    writeCompression off;
    timeFormat      general;
    timePrecision   6;
    runTimeModifiable true;
    """
)

FV_SCHEMES = cleaned(
    """
    FoamFile
    {
        format      ascii;
        class       dictionary;
        location    "system";
        object      fvSchemes;
    }

    ddtSchemes
    {
        default steadyState;
    }

    gradSchemes
    {
        default         Gauss linear;
        grad(U)         cellLimited Gauss linear 1;
        grad(k)         cellLimited Gauss linear 1;
        grad(omega)     cellLimited Gauss linear 1;
    }

    divSchemes
    {
        default         none;
        div(phi,U)      bounded Gauss linearUpwind grad(U);
        div(phi,k)      bounded Gauss limitedLinear 1;
        div(phi,omega)  bounded Gauss limitedLinear 1;
        div((nuEff*dev2(T(grad(U))))) Gauss linear;
    }

    laplacianSchemes
    {
        default Gauss linear corrected;
    }

    interpolationSchemes
    {
        default linear;
    }

    snGradSchemes
    {
        default corrected;
    }

    wallDist
    {
        method meshWave;
    }
    """
)

FV_SOLUTION = cleaned(
    """
    FoamFile
    {
        format      ascii;
        class       dictionary;
        location    "system";
        object      fvSolution;
    }

    solvers
    {
        p
        {
            solver          GAMG;
            smoother        GaussSeidel;
            tolerance       1e-7;
            relTol          0.01;
        }

        "(U|k|omega)"
        {
            solver          smoothSolver;
            smoother        symGaussSeidel;
            tolerance       1e-8;
            relTol          0.05;
        }
    }

    SIMPLE
    {
        nNonOrthogonalCorrectors 1;
        consistent yes;

        residualControl
        {
            p       1e-4;
            U       1e-5;
            k       1e-5;
            omega   1e-5;
        }
    }

    relaxationFactors
    {
        equations
        {
            U       0.7;
            k       0.6;
            omega   0.6;
        }
    }
    """
)

def plane_sample_points(x_coordinate: float) -> str:
    coordinates = (-0.098 + 0.004 * index for index in range(50))
    values = tuple(coordinates)
    return "\n".join(
        f"                ({x_coordinate:.3f} {y:.3f} {z:.3f})"
        for y in values
        for z in values
    )


SAMPLE_DICT = cleaned(
    """
    FoamFile
    {
        format      ascii;
        class       dictionary;
        location    "system";
        object      sampleDict;
    }

    targetPlaneSamples
    {
        type                sets;
        libs                ("libsampling.so");
        setFormat           raw;
        interpolationScheme cellPoint;
        fields              (U p);

        sets
        {
            plane_x_100mm
            {
                type        points;
                ordered     no;
                axis        xyz;
                points
                (
    __POINTS_100__
                );
            }
            plane_x_130mm
            {
                type        points;
                ordered     no;
                axis        xyz;
                points
                (
    __POINTS_130__
                );
            }
            plane_x_350mm
            {
                type        points;
                ordered     no;
                axis        xyz;
                points
                (
    __POINTS_350__
                );
            }
        }
    }
    """
).replace("__POINTS_100__", plane_sample_points(0.100)).replace(
    "__POINTS_130__", plane_sample_points(0.130)
).replace("__POINTS_350__", plane_sample_points(0.350))

ALLRUN = cleaned(
    """
    #!/bin/sh
    cd "${0%/*}" || exit 1
    . "${WM_PROJECT_DIR:?}/bin/tools/RunFunctions"

    runApplication blockMesh
    runApplication surfaceCheck constant/triSurface/obstruction.stl
    runApplication snappyHexMesh
    runApplication createPatch
    runApplication checkMesh
    runApplication foamRun -solver incompressibleFluid
    runApplication foamPostProcess -dict system/sampleDict -latestTime
    """
)

CASE_FILES = {
    "0/U": U,
    "0/p": P,
    "0/k": K,
    "0/omega": OMEGA,
    "0/nut": NUT,
    "constant/physicalProperties": PHYSICAL_PROPERTIES,
    "constant/momentumTransport": MOMENTUM_TRANSPORT,
    "system/blockMeshDict": BLOCK_MESH_DICT,
    "system/snappyHexMeshDict": SNAPPY_HEX_MESH_DICT,
    "system/createPatchDict": CREATE_PATCH_DICT,
    "system/meshQualityDict": MESH_QUALITY_DICT,
    "system/controlDict": CONTROL_DICT,
    "system/fvSchemes": FV_SCHEMES,
    "system/fvSolution": FV_SOLUTION,
    "system/sampleDict": SAMPLE_DICT,
    "Allrun": ALLRUN,
}


def scaled_binary_stl(source: Path, case_name: str) -> bytes:
    data = source.read_bytes()
    if len(data) < 84:
        raise ValueError(f"STL is too short: {source}")

    triangle_count = struct.unpack_from("<I", data, 80)[0]
    expected_size = 84 + triangle_count * 50
    if len(data) != expected_size:
        raise ValueError(f"Expected a binary STL with {triangle_count} triangles: {source}")

    header_text = f"PC Fan Airflow Guide OpenFOAM geometry: {case_name}"
    output = bytearray(header_text.encode("ascii")[:80].ljust(80, b" "))
    output.extend(struct.pack("<I", triangle_count))

    for triangle_index in range(triangle_count):
        offset = 84 + triangle_index * 50
        values = list(struct.unpack_from("<12fH", data, offset))
        for index in range(3, 12):
            values[index] *= 0.001
        output.extend(struct.pack("<12fH", *values))

    return bytes(output)


def write_if_changed(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        encoded = content.encode("utf-8")
    else:
        encoded = content
    if not path.exists() or path.read_bytes() != encoded:
        path.write_bytes(encoded)


def case_readme(case_name: str, metadata: dict[str, str]) -> str:
    return cleaned(
        f"""
        # {metadata['label']} OpenFOAM case

        {metadata['description']}

        The tracked obstruction surface is a metre-scaled copy of
        `cad_designs/{metadata['source']}`. Run `./Allrun` from an OpenFOAM 13
        shell to mesh, solve, and sample the 100, 130, and 350 mm planes.

        Case identifier: `{case_name}`
        """
    )


def main() -> None:
    CASE_ROOT.mkdir(parents=True, exist_ok=True)

    for case_name, metadata in CASES.items():
        case_dir = CASE_ROOT / case_name
        for relative_path, content in CASE_FILES.items():
            write_if_changed(case_dir / relative_path, content)

        stl = scaled_binary_stl(CAD_ROOT / metadata["source"], case_name)
        write_if_changed(case_dir / "constant/triSurface/obstruction.stl", stl)
        write_if_changed(case_dir / "README.md", case_readme(case_name, metadata))
        write_if_changed(
            case_dir / "case_metadata.json",
            json.dumps({"case": case_name, **metadata}, indent=2, sort_keys=True) + "\n",
        )
        (case_dir / "Allrun").chmod(0o755)
        print(f"Prepared {case_name}")


if __name__ == "__main__":
    main()
