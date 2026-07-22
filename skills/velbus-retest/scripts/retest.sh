#!/usr/bin/env bash
# Velbus local retest: clean cache, then run read_bus.py twice.
#
# The whole body lives inside main(), invoked on the final line as
# `main "$@"; exit $?`. Bash reads scripts incrementally (it lseeks back to just
# after each parsed command), so an autosave/formatter touching this file during
# the ~8 min runtime can corrupt later reads. Two things make this safe:
#   1. main()/run_once() are parsed into memory before main runs, so executing
#      them never re-reads the file.
#   2. The trailing `exit $?` (same line as the call) means that once main
#      returns, bash terminates instead of reading the (possibly rewritten) file
#      again to look for the next command.
set -u

run_once() {
    local label="$1"
    local seconds="$2"
    local connect="$3"
    local outdir="$4"
    local log="$outdir/${label}.log"
    echo "[retest] ===== $label: starting (${seconds}s) ====="
    # SIGINT after $seconds so asyncio can unwind; SIGKILL 10s later if stuck.
    timeout --signal=INT --kill-after=10 "$seconds" \
        python examples/read_bus.py --connect "$connect" >"$log" 2>&1
    local rc=$?
    echo "[retest] ===== $label: stopped (exit=$rc, timeout-stop is expected) ====="
    echo "[retest] log: $log"
}

main() {
    # Connection string (DSN). Resolution order:
    #   1. first positional argument ($1)
    #   2. $VELBUS_CONNECT environment variable
    #   3. default TLS gateway below
    # Supported schemes: tls://host:port, tcp://host:port, bare host:port (tcp),
    # a serial device path (e.g. /dev/ttyACM0), or esphome://host:port.
    local default_connect="tls://localhost:27015"
    local connect="${1:-${VELBUS_CONNECT:-$default_connect}}"
    local cache="$HOME/.velbuscache"
    # run1 scans with a cold cache and needs more time to finish the full scan;
    # run2 reuses run1's cache and completes much faster.
    local run1_seconds=300
    local run2_seconds=180
    local outdir="/tmp/velbus_retest"

    # Resolve repo root by walking up from the (symlink-resolved) script dir until
    # examples/read_bus.py is found. This keeps the script working no matter where
    # the skill was invoked from (skills/, .cursor/skills/, .claude/skills/, ...).
    local script_dir
    script_dir="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
    local repo_root="$script_dir"
    while [ "$repo_root" != "/" ] && [ ! -f "$repo_root/examples/read_bus.py" ]; do
        repo_root="$(dirname "$repo_root")"
    done
    if [ ! -f "$repo_root/examples/read_bus.py" ]; then
        echo "[retest] ERROR: could not locate repo root (examples/read_bus.py)" >&2
        exit 2
    fi

    # Python venv — NOT hardcoded. Resolution order:
    #   1. $VELBUS_VENV environment variable (venv root)
    #   2. $VIRTUAL_ENV (a venv already activated in the caller's shell)
    #   3. a .venv/ directory at the repo root
    # If none resolves to a usable venv, fail and ask the caller to set VELBUS_VENV.
    local venv="${VELBUS_VENV:-${VIRTUAL_ENV:-}}"
    if [ -z "$venv" ] && [ -f "$repo_root/.venv/bin/activate" ]; then
        venv="$repo_root/.venv"
    fi
    if [ -z "$venv" ] || [ ! -f "$venv/bin/activate" ]; then
        echo "[retest] ERROR: no usable venv found." >&2
        echo "[retest]        Set VELBUS_VENV=/path/to/venv, activate a venv," >&2
        echo "[retest]        or create <repo>/.venv before running." >&2
        exit 2
    fi

    mkdir -p "$outdir"

    echo "[retest] repo root : $repo_root"
    echo "[retest] connect   : $connect"
    echo "[retest] venv      : $venv"
    echo "[retest] cache dir : $cache"
    echo "[retest] out dir   : $outdir"

    # Step 1: clean cache (only after the venv check above, so a misconfigured
    # venv never wipes the cache before failing).
    echo "[retest] removing cache dir"
    rm -rf "$cache"

    # Step 2: load venv.
    # shellcheck disable=SC1091
    source "$venv/bin/activate"
    echo "[retest] python: $(command -v python)"

    cd "$repo_root" || exit 2

    run_once run1 "$run1_seconds" "$connect" "$outdir"
    echo "[retest] cache files after run1: $(ls -1 "$cache" 2>/dev/null | wc -l)"

    # Step 5: rerun the same command (keep cache from run1).
    run_once run2 "$run2_seconds" "$connect" "$outdir"
    echo "[retest] cache files after run2: $(ls -1 "$cache" 2>/dev/null | wc -l)"

    echo "[retest] done. Validate with:"
    echo "  $venv/bin/python $script_dir/validate_run.py $outdir/run1.log"
    echo "  $venv/bin/python $script_dir/validate_run.py $outdir/run2.log"
}

main "$@"; exit $?
