#!/usr/bin/env python3
"""Recalculate the published CFD summary and figures from the v2 rerun."""

from __future__ import annotations

import csv
import json
import math
import os
import re
import tempfile
from pathlib import Path

if "MPLCONFIGDIR" not in os.environ:
    matplotlib_cache = Path(tempfile.gettempdir()) / "pc-fan-airflow-guide-matplotlib"
    matplotlib_cache.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(matplotlib_cache)

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RUN_EVIDENCE_ROOT = ROOT / "data" / "rerun_v2"
SAMPLE_ROOT = RUN_EVIDENCE_ROOT / "openfoam_samples"
LOG_ROOT = RUN_EVIDENCE_ROOT / "openfoam_logs"
MANIFEST_PATH = RUN_EVIDENCE_ROOT / "run_manifest.json"
RESULTS_ROOT = ROOT / "results"
FIGURE_ROOT = RESULTS_ROOT / "figures"

PLANES_MM = (100, 130, 350)
AIR_DENSITY_KG_M3 = 1.20
ACTIVE_ANNULUS_AREA_MM2 = math.pi * (52.5**2 - 20.0**2)

CASES = {
    "baseline_no_guide": {
        "label": "Baseline",
        "depth_mm": 0.0,
        "vane_count": 0,
        "vane_bias_deg": 0.0,
        "vane_thickness_mm": 0.0,
        "decision": "Reference case",
    },
    "design_A_low_blockage": {
        "label": "Design A",
        "depth_mm": 20.0,
        "vane_count": 6,
        "vane_bias_deg": 0.0,
        "vane_thickness_mm": 1.5,
        "decision": "Physical-test candidate",
    },
    "design_B_angled_guide": {
        "label": "Design B",
        "depth_mm": 25.0,
        "vane_count": 8,
        "vane_bias_deg": 14.0,
        "vane_thickness_mm": 2.0,
        "decision": "Comparison design",
    },
    "design_C_balanced_revision": {
        "label": "Design C",
        "depth_mm": 22.0,
        "vane_count": 6,
        "vane_bias_deg": 9.0,
        "vane_thickness_mm": 1.35,
        "decision": "Physical-test candidate",
    },
}


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def sample_path(case: str, plane_mm: int) -> Path:
    sample_time = str(load_manifest()["cases"][case]["sample_time"])
    return (
        SAMPLE_ROOT
        / case
        / "postProcessing"
        / "targetPlaneSamples"
        / sample_time
        / f"plane_x_{plane_mm}mm.xy"
    )


def load_samples(case: str, plane_mm: int) -> np.ndarray:
    values = np.loadtxt(sample_path(case, plane_mm), comments="#")
    if values.ndim != 2 or values.shape[1] != 7:
        raise ValueError(f"Unexpected sample shape for {case} at x={plane_mm} mm")
    if not np.isfinite(values).all():
        raise ValueError(f"Non-finite sample value for {case} at x={plane_mm} mm")
    return values


def printable_blockage_percent(metadata: dict[str, float]) -> float:
    if metadata["vane_count"] == 0:
        return 0.0
    active_vane_length_mm = 52.5 - 20.0
    vane_area_mm2 = (
        metadata["vane_count"]
        * metadata["vane_thickness_mm"]
        * active_vane_length_mm
    )
    return 100.0 * vane_area_mm2 / ACTIVE_ANNULUS_AREA_MM2


def calculate_metrics() -> tuple[dict[str, dict], dict[str, dict[int, np.ndarray]]]:
    metrics: dict[str, dict] = {}
    sample_sets: dict[str, dict[int, np.ndarray]] = {}

    for case, metadata in CASES.items():
        plane_metrics = {}
        sample_sets[case] = {}
        for plane_mm in PLANES_MM:
            values = load_samples(case, plane_mm)
            sample_sets[case][plane_mm] = values
            velocity = values[:, 3:6]
            plane_metrics[plane_mm] = {
                "mean_ux": float(np.mean(velocity[:, 0])),
                "mean_speed": float(np.mean(np.linalg.norm(velocity, axis=1))),
                "mean_transverse_speed": float(
                    np.mean(np.linalg.norm(velocity[:, 1:3], axis=1))
                ),
                "mean_pressure": float(np.mean(values[:, 6])),
                "reverse_flow_percent": float(100.0 * np.mean(velocity[:, 0] < 0.0)),
            }

        pressure_demand = abs(
            plane_metrics[100]["mean_pressure"]
            - plane_metrics[350]["mean_pressure"]
        )
        metrics[case] = {
            **metadata,
            "cad_blockage_percent": printable_blockage_percent(metadata),
            "planes": plane_metrics,
            "kinematic_pressure_demand_m2_s2": pressure_demand,
            "pressure_demand_pa_at_1p2kg_m3": pressure_demand
            * AIR_DENSITY_KG_M3,
            "average_reverse_flow_percent": float(
                np.mean(
                    [
                        plane_metrics[plane]["reverse_flow_percent"]
                        for plane in PLANES_MM
                    ]
                )
            ),
        }

    baseline = metrics["baseline_no_guide"]
    for entry in metrics.values():
        for plane_mm in PLANES_MM:
            entry["planes"][plane_mm]["axial_velocity_retention_percent"] = (
                100.0
                * entry["planes"][plane_mm]["mean_ux"]
                / baseline["planes"][plane_mm]["mean_ux"]
            )
    return metrics, sample_sets


def write_cfd_summary(metrics: dict[str, dict]) -> None:
    path = RESULTS_ROOT / "cfd_summary.csv"
    columns = [
        "case",
        "design",
        "depth_mm",
        "vane_count",
        "vane_bias_deg",
        "vane_thickness_mm",
        "vane_blockage_percent_estimate",
        "mean_ux_x100_m_s",
        "mean_ux_x130_m_s",
        "mean_ux_x350_m_s",
        "axial_retention_x350_percent_of_baseline",
        "mean_speed_x130_m_s",
        "mean_transverse_speed_x130_m_s",
        "mean_speed_x350_m_s",
        "mean_transverse_speed_x350_m_s",
        "kinematic_pressure_demand_m2_s2",
        "pressure_demand_pa_at_1p2kg_m3",
        "average_reverse_flow_percent",
        "decision",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for case, entry in metrics.items():
            writer.writerow(
                {
                    "case": case,
                    "design": entry["label"],
                    "depth_mm": f'{entry["depth_mm"]:.1f}',
                    "vane_count": entry["vane_count"],
                    "vane_bias_deg": f'{entry["vane_bias_deg"]:.1f}',
                    "vane_thickness_mm": f'{entry["vane_thickness_mm"]:.2f}',
                    "vane_blockage_percent_estimate": f'{entry["cad_blockage_percent"]:.2f}',
                    "mean_ux_x100_m_s": f'{entry["planes"][100]["mean_ux"]:.5f}',
                    "mean_ux_x130_m_s": f'{entry["planes"][130]["mean_ux"]:.5f}',
                    "mean_ux_x350_m_s": f'{entry["planes"][350]["mean_ux"]:.5f}',
                    "axial_retention_x350_percent_of_baseline": f'{entry["planes"][350]["axial_velocity_retention_percent"]:.2f}',
                    "mean_speed_x130_m_s": f'{entry["planes"][130]["mean_speed"]:.5f}',
                    "mean_transverse_speed_x130_m_s": f'{entry["planes"][130]["mean_transverse_speed"]:.5f}',
                    "mean_speed_x350_m_s": f'{entry["planes"][350]["mean_speed"]:.5f}',
                    "mean_transverse_speed_x350_m_s": f'{entry["planes"][350]["mean_transverse_speed"]:.5f}',
                    "kinematic_pressure_demand_m2_s2": f'{entry["kinematic_pressure_demand_m2_s2"]:.5f}',
                    "pressure_demand_pa_at_1p2kg_m3": f'{entry["pressure_demand_pa_at_1p2kg_m3"]:.5f}',
                    "average_reverse_flow_percent": f'{entry["average_reverse_flow_percent"]:.3f}',
                    "decision": entry["decision"],
                }
            )


def last_residuals(log_text: str) -> dict[str, float]:
    residuals = {}
    for field in ("Ux", "Uy", "Uz", "p", "k", "omega"):
        matches = re.findall(
            rf"Solving for {field}, Initial residual = ([0-9.eE+-]+)", log_text
        )
        residuals[field] = float(matches[-1]) if matches else math.nan
    continuity = re.findall(
        r"global = ([0-9.eE+-]+), cumulative", log_text
    )
    residuals["continuity_global"] = (
        float(continuity[-1]) if continuity else math.nan
    )
    return residuals


def write_solver_summary() -> None:
    path = RESULTS_ROOT / "solver_residual_summary.csv"
    columns = [
        "case",
        "iterations",
        "last_initial_residual_ux",
        "last_initial_residual_uy",
        "last_initial_residual_uz",
        "last_initial_residual_p",
        "last_initial_residual_k",
        "last_initial_residual_omega",
        "last_global_continuity_error",
        "status",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        manifest = load_manifest()
        for case in CASES:
            text = (LOG_ROOT / case / "foamRun.log").read_text(
                encoding="utf-8", errors="replace"
            )
            residuals = last_residuals(text)
            case_manifest = manifest["cases"][case]
            converged = bool(case_manifest["residual_controls_satisfied"])
            writer.writerow(
                {
                    "case": case,
                    "iterations": case_manifest["iterations"],
                    "last_initial_residual_ux": f'{residuals["Ux"]:.8g}',
                    "last_initial_residual_uy": f'{residuals["Uy"]:.8g}',
                    "last_initial_residual_uz": f'{residuals["Uz"]:.8g}',
                    "last_initial_residual_p": f'{residuals["p"]:.8g}',
                    "last_initial_residual_k": f'{residuals["k"]:.8g}',
                    "last_initial_residual_omega": f'{residuals["omega"]:.8g}',
                    "last_global_continuity_error": f'{residuals["continuity_global"]:.8g}',
                    "status": (
                        "Residual controls satisfied"
                        if converged
                        else "Maximum iteration count reached before all residual controls"
                    ),
                }
            )


def extract_one(pattern: str, text: str, cast=float):
    match = re.search(pattern, text)
    if not match:
        return None
    return cast(match.group(1))


def write_mesh_summary() -> None:
    path = RESULTS_ROOT / "mesh_quality_summary.csv"
    columns = [
        "case",
        "cells",
        "max_aspect_ratio",
        "max_non_orthogonality_deg",
        "average_non_orthogonality_deg",
        "max_skewness",
        "check_mesh_status",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for case in CASES:
            text = (LOG_ROOT / case / "checkMesh.log").read_text(
                encoding="utf-8", errors="replace"
            )
            non_orth = re.search(
                r"Mesh non-orthogonality Max: ([0-9.eE+-]+) average: ([0-9.eE+-]+)",
                text,
            )
            writer.writerow(
                {
                    "case": case,
                    "cells": extract_one(r"cells:\s+([0-9]+)", text, int),
                    "max_aspect_ratio": extract_one(
                        r"Max aspect ratio = ([0-9.eE+-]+)", text
                    ),
                    "max_non_orthogonality_deg": (
                        float(non_orth.group(1)) if non_orth else None
                    ),
                    "average_non_orthogonality_deg": (
                        float(non_orth.group(2)) if non_orth else None
                    ),
                    "max_skewness": extract_one(
                        r"Max skewness = ([0-9.eE+-]+)", text
                    ),
                    "check_mesh_status": "OK" if "Mesh OK." in text else "Review log",
                }
            )


def grid_field(values: np.ndarray, field: np.ndarray):
    y_coordinates = np.round(values[:, 1], 9)
    z_coordinates = np.round(values[:, 2], 9)
    y_values = np.unique(y_coordinates)
    z_values = np.unique(z_coordinates)
    grid = np.full((len(z_values), len(y_values)), np.nan)
    y_index = {value: index for index, value in enumerate(y_values)}
    z_index = {value: index for index, value in enumerate(z_values)}
    for y_value, z_value, result in zip(y_coordinates, z_coordinates, field):
        grid[z_index[z_value], y_index[y_value]] = result
    return y_values * 1000.0, z_values * 1000.0, grid


def plot_velocity_planes(sample_sets: dict[str, dict[int, np.ndarray]]) -> None:
    all_speeds = []
    for case in CASES:
        for plane in PLANES_MM:
            velocity = sample_sets[case][plane][:, 3:6]
            all_speeds.extend(np.linalg.norm(velocity, axis=1))
    vmax = float(np.quantile(np.asarray(all_speeds), 0.995))

    for plane in PLANES_MM:
        fig, axes = plt.subplots(2, 2, figsize=(10, 9), constrained_layout=True)
        mesh = None
        for axis, (case, metadata) in zip(axes.flat, CASES.items()):
            values = sample_sets[case][plane]
            speed = np.linalg.norm(values[:, 3:6], axis=1)
            y, z, grid = grid_field(values, speed)
            mesh = axis.pcolormesh(
                y,
                z,
                grid,
                shading="nearest",
                cmap="viridis",
                vmin=0.0,
                vmax=vmax,
            )
            axis.set_title(metadata["label"])
            axis.set_aspect("equal")
            axis.set_xlabel("y (mm)")
            axis.set_ylabel("z (mm)")
        colorbar = fig.colorbar(mesh, ax=axes, shrink=0.88)
        colorbar.set_label("Velocity magnitude (m/s)")
        fig.suptitle(f"OpenFOAM sampled velocity magnitude at x = {plane} mm")
        fig.savefig(
            FIGURE_ROOT / f"velocity_magnitude_x{plane}.png",
            dpi=180,
            bbox_inches="tight",
        )
        plt.close(fig)


def plot_tradeoffs(metrics: dict[str, dict]) -> None:
    labels = [entry["label"] for entry in metrics.values()]
    colors = ["#7f8c8d", "#4c78a8", "#f58518", "#54a24b"]
    x = np.arange(len(labels))

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6), constrained_layout=True)
    pressure = [
        entry["pressure_demand_pa_at_1p2kg_m3"] for entry in metrics.values()
    ]
    reverse = [entry["average_reverse_flow_percent"] for entry in metrics.values()]
    transverse_x130 = [
        entry["planes"][130]["mean_transverse_speed"]
        for entry in metrics.values()
    ]

    for axis, values, title, ylabel, label_format in (
        (
            axes[0],
            pressure,
            "Pressure-demand indicator",
            "Equivalent pressure (Pa)\nusing ρ = 1.20 kg/m³",
            "%.2f",
        ),
        (
            axes[1],
            reverse,
            "Average sampled reverse flow",
            "Points with Ux < 0 (%)",
            "%.1f",
        ),
        (
            axes[2],
            transverse_x130,
            "Directional component at x = 130 mm",
            "Mean transverse speed (m/s)",
            "%.3f",
        ),
    ):
        bars = axis.bar(x, values, color=colors)
        axis.set_title(title)
        axis.set_ylabel(ylabel)
        axis.set_xticks(x, labels)
        axis.grid(axis="y", alpha=0.25)
        axis.bar_label(bars, fmt=label_format, padding=3, fontsize=8)

    fig.suptitle("OpenFOAM 13 printable-geometry rerun trade-offs")
    fig.savefig(
        FIGURE_ROOT / "screening_tradeoffs.png",
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


def main() -> None:
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    metrics, sample_sets = calculate_metrics()
    write_cfd_summary(metrics)
    write_solver_summary()
    write_mesh_summary()
    plot_velocity_planes(sample_sets)
    plot_tradeoffs(metrics)
    print("Rebuilt CFD tables and figures from the OpenFOAM v2 rerun.")


if __name__ == "__main__":
    main()
