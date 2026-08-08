#!/usr/bin/env python3
"""Check public-release integrity for data, CAD exports, and documentation."""

from __future__ import annotations

import csv
import json
import re
import struct
import zlib
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RERUN_ROOT = ROOT / "data" / "rerun_v2"

OPENFOAM_CASE_SOURCES = {
    "baseline_no_guide": "fan_reference.stl",
    "design_A_low_blockage": "design_A_low_blockage.stl",
    "design_B_angled_guide": "design_B_angled_guide.stl",
    "design_C_balanced_revision": "design_C_balanced_revision.stl",
}

OPENFOAM_CASE_FILES = {
    "0/U",
    "0/p",
    "0/k",
    "0/omega",
    "0/nut",
    "constant/momentumTransport",
    "constant/physicalProperties",
    "constant/triSurface/obstruction.stl",
    "system/blockMeshDict",
    "system/snappyHexMeshDict",
    "system/createPatchDict",
    "system/meshQualityDict",
    "system/controlDict",
    "system/fvSchemes",
    "system/fvSolution",
    "system/sampleDict",
    "Allrun",
    "README.md",
    "case_metadata.json",
}

DESIGN_DEPTHS = {
    "design_A_low_blockage.stl": 20.0,
    "design_B_angled_guide.stl": 25.0,
    "design_C_balanced_revision.stl": 22.0,
}

STEP_EXPORTS = {
    "design_A_low_blockage.step",
    "design_B_angled_guide.step",
    "design_C_balanced_revision.step",
    "fan_reference.step",
}

REPRODUCIBLE_STEP_TIMESTAMP = "2000-01-01T00:00:00"
STEP_TIMESTAMP_PATTERN = re.compile(
    r"FILE_NAME\('Open CASCADE Shape Model','([^']+)'"
)

FIGURE_EXPORTS = {
    "screening_tradeoffs.png",
    "velocity_magnitude_x100.png",
    "velocity_magnitude_x130.png",
    "velocity_magnitude_x350.png",
}

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

PROHIBITED_TEXT = {
    "private Windows path": re.compile(r"[A-Za-z]:[/\\]Users[/\\]|/mnt/c/Users/", re.IGNORECASE),
    "private workspace path": re.compile(r"/workspace/(?:scratch|upload|work)/", re.IGNORECASE),
    "unfinished marker": re.compile(r"\bTODO\b|\bplaceholder\b", re.IGNORECASE),
}

TEXT_SUFFIXES = {
    "",
    ".cjs",
    ".csv",
    ".gitignore",
    ".json",
    ".log",
    ".md",
    ".py",
    ".sh",
    ".txt",
    ".yaml",
    ".yml",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def ignored_path(path: Path) -> bool:
    return any(
        part in {".git", "node_modules", "__pycache__"}
        for part in path.relative_to(ROOT).parts
    )


def read_binary_stl(path: Path):
    data = path.read_bytes()
    if len(data) < 84:
        fail(f"STL is too short: {path}")
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + triangle_count * 50:
        fail(f"STL byte count does not match its triangle count: {path}")
    record = np.dtype(
        [("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attribute", "<u2")]
    )
    triangles = np.frombuffer(
        data, dtype=record, offset=84, count=triangle_count
    )["vertices"].astype(np.float64)
    return triangles


def mesh_topology(triangles: np.ndarray, quantization: int = 100_000):
    flat_vertices = triangles.reshape(-1, 3)
    quantized = np.rint(flat_vertices * quantization).astype(np.int64)
    vertex_ids = {}
    indexed_vertices = []
    for vertex in map(tuple, quantized):
        if vertex not in vertex_ids:
            vertex_ids[vertex] = len(vertex_ids)
        indexed_vertices.append(vertex_ids[vertex])

    faces = np.asarray(indexed_vertices, dtype=np.int64).reshape(-1, 3)
    edge_counts = Counter()
    adjacency = defaultdict(set)
    for face in faces:
        for first, second in (
            (face[0], face[1]),
            (face[1], face[2]),
            (face[2], face[0]),
        ):
            first = int(first)
            second = int(second)
            edge = (min(first, second), max(first, second))
            edge_counts[edge] += 1
            adjacency[first].add(second)
            adjacency[second].add(first)

    seen = set()
    component_count = 0
    for vertex_id in range(len(vertex_ids)):
        if vertex_id in seen:
            continue
        component_count += 1
        stack = [vertex_id]
        seen.add(vertex_id)
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)

    return {
        "boundary_edges": sum(count == 1 for count in edge_counts.values()),
        "nonmanifold_edges": sum(count > 2 for count in edge_counts.values()),
        "components": component_count,
    }


def validate_cad() -> None:
    for filename, expected_depth in DESIGN_DEPTHS.items():
        path = ROOT / "cad_designs" / filename
        triangles = read_binary_stl(path)
        bounds_min = triangles.reshape(-1, 3).min(axis=0)
        bounds_max = triangles.reshape(-1, 3).max(axis=0)
        size = bounds_max - bounds_min
        topology = mesh_topology(triangles)

        if not np.allclose(size, [expected_depth, 120.0, 120.0], atol=0.01):
            fail(f"Unexpected CAD envelope for {filename}: {size}")
        if not np.allclose(bounds_min, [0.0, -60.0, -60.0], atol=0.01):
            fail(f"Unexpected minimum coordinates for {filename}: {bounds_min}")
        if topology != {
            "boundary_edges": 0,
            "nonmanifold_edges": 0,
            "components": 1,
        }:
            fail(f"Mesh topology failed for {filename}: {topology}")

    for filename in STEP_EXPORTS:
        path = ROOT / "cad_designs" / filename
        match = STEP_TIMESTAMP_PATTERN.search(path.read_text(encoding="utf-8"))
        if not match:
            fail(f"STEP timestamp is missing from {filename}")
        if match.group(1) != REPRODUCIBLE_STEP_TIMESTAMP:
            fail(f"STEP timestamp is not reproducible in {filename}: {match.group(1)}")


def validate_openfoam_cases() -> None:
    case_root = ROOT / "openfoam_cases"
    for case, source_name in OPENFOAM_CASE_SOURCES.items():
        case_directory = case_root / case
        present_files = {
            str(path.relative_to(case_directory))
            for path in case_directory.rglob("*")
            if path.is_file()
        }
        missing = OPENFOAM_CASE_FILES - present_files
        if missing:
            fail(f"OpenFOAM case {case} is incomplete: {sorted(missing)}")

        if not (case_directory / "Allrun").stat().st_mode & 0o111:
            fail(f"OpenFOAM Allrun is not executable: {case}")

        source_triangles = read_binary_stl(ROOT / "cad_designs" / source_name)
        case_triangles = read_binary_stl(
            case_directory / "constant" / "triSurface" / "obstruction.stl"
        )
        if source_triangles.shape != case_triangles.shape or not np.allclose(
            case_triangles, source_triangles * 0.001, atol=1e-9
        ):
            fail(f"OpenFOAM surface is not a metre-scaled CAD copy: {case}")

        topology = mesh_topology(case_triangles, quantization=100_000_000)
        expected_components = 2 if case == "baseline_no_guide" else 1
        if topology != {
            "boundary_edges": 0,
            "nonmanifold_edges": 0,
            "components": expected_components,
        }:
            fail(f"OpenFOAM surface topology failed for {case}: {topology}")

        allrun = (case_directory / "Allrun").read_text(encoding="utf-8")
        for command in (
            "blockMesh",
            "surfaceCheck",
            "snappyHexMesh",
            "createPatch",
            "checkMesh",
            "foamRun",
            "foamPostProcess",
        ):
            if command not in allrun:
                fail(f"OpenFOAM Allrun is missing {command}: {case}")

        u_text = (case_directory / "0" / "U").read_text(encoding="utf-8")
        if "codedFixedValue" in u_text or "fan_active_annulus" not in u_text:
            fail(f"OpenFOAM inlet is not the native annular patch setup: {case}")

        sample_text = (case_directory / "system" / "sampleDict").read_text(
            encoding="utf-8"
        )
        if (
            "type                sets;" not in sample_text
            or "type                surfaces;" in sample_text
        ):
            fail(f"OpenFOAM sampling is not a fixed point-set grid: {case}")
        for plane_mm in (100, 130, 350):
            if f"plane_x_{plane_mm}mm" not in sample_text:
                fail(f"OpenFOAM sampling plane x={plane_mm} mm is missing: {case}")
            coordinate = plane_mm / 1000.0
            if sample_text.count(f"({coordinate:.3f} ") != 2500:
                fail(f"OpenFOAM fixed sampling grid is incomplete at x={plane_mm} mm: {case}")


def validate_png(path: Path) -> None:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        fail(f"Invalid PNG signature: {path.relative_to(ROOT)}")

    offset = len(PNG_SIGNATURE)
    while offset < len(data):
        if len(data) - offset < 12:
            fail(f"Truncated PNG chunk: {path.relative_to(ROOT)}")

        payload_length = struct.unpack_from(">I", data, offset)[0]
        chunk_type = data[offset + 4 : offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + payload_length
        chunk_end = payload_end + 4
        if chunk_end > len(data):
            fail(f"Truncated PNG payload: {path.relative_to(ROOT)}")

        expected_crc = struct.unpack_from(">I", data, payload_end)[0]
        calculated_crc = zlib.crc32(chunk_type)
        calculated_crc = zlib.crc32(data[payload_start:payload_end], calculated_crc)
        if expected_crc != calculated_crc & 0xFFFFFFFF:
            fail(f"PNG checksum mismatch: {path.relative_to(ROOT)}")

        offset = chunk_end
        if chunk_type == b"IEND":
            if payload_length != 0 or offset != len(data):
                fail(f"Malformed PNG ending: {path.relative_to(ROOT)}")
            return

    fail(f"PNG ending is missing: {path.relative_to(ROOT)}")


def validate_figures() -> None:
    for filename in FIGURE_EXPORTS:
        validate_png(ROOT / "results" / "figures" / filename)


def validate_samples_and_summary() -> None:
    manifest = json.loads(
        (RERUN_ROOT / "run_manifest.json").read_text(encoding="utf-8")
    )
    summary_path = ROOT / "results" / "cfd_summary.csv"
    with summary_path.open(newline="", encoding="utf-8") as handle:
        rows = {row["case"]: row for row in csv.DictReader(handle)}

    expected_cases = set(OPENFOAM_CASE_SOURCES)
    if set(rows) != expected_cases or set(manifest["cases"]) != expected_cases:
        fail("The CFD summary or run manifest does not contain exactly four cases")

    for case, row in rows.items():
        case_manifest = manifest["cases"][case]
        sample_time = str(case_manifest["sample_time"])
        log_root = RERUN_ROOT / "openfoam_logs" / case

        evidence_checks = {
            "surfaceCheck.log": "Surface is closed.",
            "snappyHexMesh.log": "Finished meshing without any errors",
            "checkMesh.log": "Mesh OK.",
            "foamRun.log": "End",
            "sample.log": "Executing functionObjects",
        }
        for log_name, marker in evidence_checks.items():
            log_text = (log_root / log_name).read_text(
                encoding="utf-8", errors="replace"
            )
            if marker not in log_text or "FOAM FATAL" in log_text:
                fail(f"OpenFOAM evidence check failed: {case}/{log_name}")

        for plane_mm in (100, 130, 350):
            path = (
                RERUN_ROOT
                / "openfoam_samples"
                / case
                / "postProcessing"
                / "targetPlaneSamples"
                / sample_time
                / f"plane_x_{plane_mm}mm.xy"
            )
            samples = np.loadtxt(path, comments="#")
            if samples.shape != (2500, 7):
                fail(f"Unexpected sample dimensions: {path} -> {samples.shape}")
            if not np.isfinite(samples).all():
                fail(f"Non-finite sample value: {path}")
            reported = float(row[f"mean_ux_x{plane_mm}_m_s"])
            calculated = float(np.mean(samples[:, 3]))
            if not np.isclose(reported, calculated, atol=5e-6):
                fail(
                    f"Summary mismatch for {case} at x={plane_mm} mm: "
                    f"{reported} != {calculated}"
                )


def validate_public_text() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if ignored_path(path):
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in PROHIBITED_TEXT.items():
            if pattern.search(text):
                fail(f"{label} found in {path.relative_to(ROOT)}")


def validate_markdown_links() -> None:
    link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for path in ROOT.rglob("*.md"):
        if ignored_path(path):
            continue
        text = path.read_text(encoding="utf-8")
        for target in link_pattern.findall(text):
            target = target.split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            if ROOT not in resolved.parents and resolved != ROOT:
                fail(f"Link escapes the repository: {path} -> {target}")
            if not resolved.exists():
                fail(f"Broken local link: {path.relative_to(ROOT)} -> {target}")


def main() -> None:
    validate_cad()
    validate_openfoam_cases()
    validate_figures()
    validate_samples_and_summary()
    validate_public_text()
    validate_markdown_links()
    print("Repository validation passed.")


if __name__ == "__main__":
    main()
