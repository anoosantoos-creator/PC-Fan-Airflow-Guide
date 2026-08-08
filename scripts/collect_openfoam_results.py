#!/usr/bin/env python3
"""Copy a completed OpenFOAM run into the repository's evidence directory."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from decimal import Decimal, InvalidOperation
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "data" / "rerun_v2"
CASES = (
    "baseline_no_guide",
    "design_A_low_blockage",
    "design_B_angled_guide",
    "design_C_balanced_revision",
)
LOG_FILES = (
    "blockMesh.log",
    "surfaceCheck.log",
    "snappyHexMesh.log",
    "createPatch.log",
    "checkMesh.log",
    "foamRun.log",
    "sample.log",
)
PLANES_MM = (100, 130, 350)


def numeric_time(path: Path) -> Decimal | None:
    try:
        return Decimal(path.name)
    except InvalidOperation:
        return None


def latest_sample_directory(case_directory: Path) -> Path:
    sample_root = case_directory / "postProcessing" / "targetPlaneSamples"
    candidates = [
        (value, path)
        for path in sample_root.iterdir()
        if path.is_dir() and (value := numeric_time(path)) is not None
    ]
    if not candidates:
        raise FileNotFoundError(f"No target-plane samples found under {sample_root}")
    return max(candidates, key=lambda item: item[0])[1]


def last_iteration(log_text: str) -> int:
    matches = re.findall(r"^Time = ([0-9]+)s$", log_text, flags=re.MULTILINE)
    if not matches:
        raise ValueError("Could not find the final iteration in foamRun.log")
    return int(matches[-1])


def copy_file(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def copy_log(source: Path, destination: Path, run_root: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    text = source.read_text(encoding="utf-8", errors="replace")
    text = text.replace(str(run_root), "<run-root>")
    text = re.sub(
        r"^Case\s+:\s+.*$",
        f"Case   : <run-root>/{source.parent.name}",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'^Host\s+:\s+"[^"]+"$',
        'Host   : "<compute-host>"',
        text,
        flags=re.MULTILINE,
    )
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    text = "\n".join(lines) + "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def collect(run_root: Path) -> None:
    run_root = run_root.resolve()
    manifest: dict[str, object] = {
        "case_set": "printable-geometry-rerun-v2",
        "openfoam_version": 13,
        "cases": {},
    }

    for case in CASES:
        source_case = run_root / case
        log_destination = DESTINATION / "openfoam_logs" / case
        for log_name in LOG_FILES:
            copy_log(source_case / log_name, log_destination / log_name, run_root)

        solver_text = (source_case / "foamRun.log").read_text(
            encoding="utf-8", errors="replace"
        )
        sample_directory = latest_sample_directory(source_case)
        sample_destination = (
            DESTINATION
            / "openfoam_samples"
            / case
            / "postProcessing"
            / "targetPlaneSamples"
            / sample_directory.name
        )

        for plane_mm in PLANES_MM:
            filename = f"plane_x_{plane_mm}mm.xy"
            copy_file(sample_directory / filename, sample_destination / filename)

        build_match = re.search(r"^Build\s+:\s+(.+)$", solver_text, re.MULTILINE)
        manifest["cases"][case] = {
            "iterations": last_iteration(solver_text),
            "residual_controls_satisfied": "SIMPLE solution converged in" in solver_text,
            "sample_time": sample_directory.name,
            "mesh_check": "OK" if "Mesh OK." in (source_case / "checkMesh.log").read_text() else "review",
            "surface_closed": "Surface is closed." in (source_case / "surfaceCheck.log").read_text(),
            "build": build_match.group(1).strip() if build_match else "OpenFOAM 13",
        }
        print(f"Collected {case} at iteration {sample_directory.name}")

    DESTINATION.mkdir(parents=True, exist_ok=True)
    (DESTINATION / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path, help="Directory printed by cfd:run")
    arguments = parser.parse_args()
    collect(arguments.run_root)


if __name__ == "__main__":
    main()
