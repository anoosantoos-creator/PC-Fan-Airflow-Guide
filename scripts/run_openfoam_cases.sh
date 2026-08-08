#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CASE_NAMES=(
    baseline_no_guide
    design_A_low_blockage
    design_B_angled_guide
    design_C_balanced_revision
)

for command_name in \
    blockMesh surfaceCheck snappyHexMesh createPatch checkMesh foamRun foamPostProcess
do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        printf 'Required OpenFOAM command is not on PATH: %s\n' "$command_name" >&2
        exit 1
    fi
done

PARALLEL_CASES=${CFD_JOBS:-1}
if [[ ! "$PARALLEL_CASES" =~ ^[1-4]$ ]]; then
    printf 'CFD_JOBS must be an integer from 1 through 4.\n' >&2
    exit 1
fi

if [[ -n ${CFD_RUN_ROOT:-} ]]; then
    if [[ -e "$CFD_RUN_ROOT" ]]; then
        printf 'CFD_RUN_ROOT already exists; choose a new directory: %s\n' "$CFD_RUN_ROOT" >&2
        exit 1
    fi
    mkdir -p "$(dirname "$CFD_RUN_ROOT")"
    mkdir "$CFD_RUN_ROOT"
    RUN_ROOT=$(cd "$CFD_RUN_ROOT" && pwd)
else
    RUN_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/pc-fan-openfoam.XXXXXX")
fi

python "$REPOSITORY_ROOT/scripts/prepare_openfoam_cases.py"

run_logged() {
    local log_path=$1
    shift
    if ! "$@" >"$log_path" 2>&1; then
        printf 'Command failed; last log lines from %s:\n' "$log_path" >&2
        tail -80 "$log_path" >&2
        return 1
    fi
}

require_log_marker() {
    local log_path=$1
    local marker=$2
    if grep -Fq "FOAM FATAL" "$log_path" || ! grep -Fq "$marker" "$log_path"; then
        printf 'Required completion marker is missing from %s: %s\n' \
            "$log_path" "$marker" >&2
        tail -80 "$log_path" >&2
        return 1
    fi
}

run_case() {
    local case_name=$1
    local case_directory="$RUN_ROOT/$case_name"

    cp -a "$REPOSITORY_ROOT/openfoam_cases/$case_name" "$case_directory"
    cd "$case_directory"

    printf 'Meshing %s\n' "$case_name"
    run_logged blockMesh.log blockMesh
    run_logged surfaceCheck.log surfaceCheck constant/triSurface/obstruction.stl
    require_log_marker surfaceCheck.log "Surface is closed."
    run_logged snappyHexMesh.log snappyHexMesh
    require_log_marker snappyHexMesh.log "Finished meshing without any errors"
    run_logged createPatch.log createPatch
    run_logged checkMesh.log checkMesh
    require_log_marker checkMesh.log "Mesh OK."

    printf 'Solving %s\n' "$case_name"
    run_logged foamRun.log foamRun -solver incompressibleFluid
    require_log_marker foamRun.log "End"
    run_logged sample.log foamPostProcess -dict system/sampleDict -latestTime
    require_log_marker sample.log "Executing functionObjects"
    require_log_marker sample.log "End"

    printf 'Completed %s\n' "$case_name"
}

process_ids=()
overall_status=0

wait_for_batch() {
    local process_id
    for process_id in "${process_ids[@]}"; do
        if ! wait "$process_id"; then
            overall_status=1
        fi
    done
    process_ids=()
}

for case_name in "${CASE_NAMES[@]}"; do
    run_case "$case_name" &
    process_ids+=("$!")
    if (( ${#process_ids[@]} == PARALLEL_CASES )); then
        wait_for_batch
    fi
done

if (( ${#process_ids[@]} > 0 )); then
    wait_for_batch
fi

if (( overall_status != 0 )); then
    printf 'One or more OpenFOAM cases failed. Run directory: %s\n' "$RUN_ROOT" >&2
    exit "$overall_status"
fi

printf 'All OpenFOAM cases completed. Run directory: %s\n' "$RUN_ROOT"
