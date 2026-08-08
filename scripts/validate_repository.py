#!/usr/bin/env python3
"""Check public-release integrity for data, CAD exports, and documentation."""

from __future__ import annotations

import csv
import re
import struct
import zlib
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]

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

REMOVED_PUBLIC_ARTIFACTS = {
    "OPEN_ME.html",
    "README_FIRST.txt",
    "RUN_REAL_OPENFOAM_CFD.md",
    "run_status.md",
    "cfd_results_comparison_surrogate.csv",
    "review_exports",
}

PROHIBITED_TEXT = {
    "private Windows path": re.compile(r"[A-Za-z]:[/\\]Users[/\\]|/mnt/c/Users/", re.IGNORECASE),
    "unfinished marker": re.compile(r"\bTODO\b|\bplaceholder\b", re.IGNORECASE),
}

TEXT_SUFFIXES = {
    ".cjs",
    ".csv",
    ".gitignore",
    ".json",
    ".log",
    ".md",
    ".py",
    ".txt",
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


def mesh_topology(triangles: np.ndarray):
    flat_vertices = triangles.reshape(-1, 3)
    quantized = np.rint(flat_vertices * 100_000).astype(np.int64)
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
    summary_path = ROOT / "results" / "cfd_summary.csv"
    with summary_path.open(newline="", encoding="utf-8") as handle:
        rows = {row["case"]: row for row in csv.DictReader(handle)}

    for case, row in rows.items():
        for plane_mm in (100, 130, 350):
            path = (
                ROOT
                / "data"
                / "openfoam_samples"
                / case
                / "postProcessing"
                / "targetPlaneSamples"
                / "200"
                / f"plane_x_{plane_mm}mm.xy"
            )
            samples = np.loadtxt(path, comments="#")
            if samples.shape != (2601, 7):
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
    for removed in REMOVED_PUBLIC_ARTIFACTS:
        if (ROOT / removed).exists():
            fail(f"Release-only artifact is still present: {removed}")

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
    validate_figures()
    validate_samples_and_summary()
    validate_public_text()
    validate_markdown_links()
    print("Repository validation passed.")


if __name__ == "__main__":
    main()
