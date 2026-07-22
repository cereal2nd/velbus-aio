---
name: velbus-retest
description: Run the live Velbus bus read_bus.py retest twice against the TLS gateway, then monitor the runs for tracebacks, errors, exceptions, and verify every found module produced a correct per-address cache json. Use when asked to retest the bus, do a local retest, re-scan modules, or validate ~/.velbuscache after a run.
disable-model-invocation: true
---

# Velbus local retest

Runs the live bus scan twice and validates the output and cache.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 0: Ask the user which bus to connect to and which Python venv to use
- [ ] Step 1: Run both iterations (scripts/retest.sh)
- [ ] Step 2: Validate run 1 (scripts/validate_run.py)
- [ ] Step 3: Validate run 2 (scripts/validate_run.py)
- [ ] Step 4: Report findings
```

### Step 0: Ask which bus and which venv to use

Before running, ask the user for **two** things — neither is hardcoded:

**1. The connection string (DSN)** to test against. Offer the default TLS gateway
`tls://velbus.iot.home.m17.be:27015` as the recommended option. Supported formats:

- `tls://host:port` — TLS gateway (default)
- `tcp://host:port` or bare `host:port` — plain TCP gateway
- `/dev/ttyACM0` (or similar) — local serial device
- `esphome://host:port` — ESPHome bridge

Pass the chosen value as the first argument to `retest.sh` (or via
`VELBUS_CONNECT`). If the user does not care, run without an argument to use the
default.

**2. The Python virtualenv** to run in. Pass its root path via the `VELBUS_VENV`
environment variable. `retest.sh`
resolves the venv in this order and aborts (before touching anything) if none is
usable:

1. `VELBUS_VENV` — the venv root you provide
2. `VIRTUAL_ENV` — a venv already activated in the shell
3. `<repo>/.venv/` — a virtualenv at the repo root

Ask the user for `VELBUS_VENV` unless they already have a venv activated or a
repo-local `.venv/`.

### Step 1: Run both iterations

Run from the repo root, passing the connection and venv chosen in Step 0:

```bash
VELBUS_VENV="/path/to/venv" skills/velbus-retest/scripts/retest.sh "tls://velbus.iot.home.m17.be:27015"
```

The connection can also be supplied via the `VELBUS_CONNECT` environment
variable, and omitting it entirely falls back to the default TLS gateway. If a
venv is already activated (or `<repo>/.venv/` exists) you can drop `VELBUS_VENV`:

```bash
VELBUS_VENV="/path/to/venv" skills/velbus-retest/scripts/retest.sh              # default connection
VELBUS_VENV="/path/to/venv" VELBUS_CONNECT="tcp://192.168.1.9:27015" skills/velbus-retest/scripts/retest.sh
```

This performs, in order:

1. resolves and validates the venv (aborts here if none is usable)
2. `rm -rf ~/.velbuscache`
3. sources the resolved venv's `bin/activate`
4. runs `python examples/read_bus.py --connect <chosen DSN>`
5. stops run 1 after 5 minutes (300s) — the cold-cache scan needs the extra time
6. reruns the exact same command for 3 minutes (180s), keeping run 1's cache

Logs are written to `/tmp/velbus_retest/run1.log` and `/tmp/velbus_retest/run2.log`.
The whole thing takes ~8.5 minutes; start it with a generous `block_until_ms`
(e.g. `540000`) or background it and poll.

### Step 2 & 3: Validate each run

```bash
"$VELBUS_VENV/bin/python" skills/velbus-retest/scripts/validate_run.py /tmp/velbus_retest/run1.log
"$VELBUS_VENV/bin/python" skills/velbus-retest/scripts/validate_run.py /tmp/velbus_retest/run2.log
```

The validator monitors each run for:

- **Tracebacks** — `Traceback (most recent call last)` blocks (printed in full).
- **Errors** — `ERROR` / `CRITICAL` log lines.
- **Exceptions** — lines mentioning an exception being raised/logged.
- **Cache correctness** — for every module reported via `Module found:` (address
  parsed from the repr), a matching `~/.velbuscache/{address}.json` must exist and
  be a valid dict with a non-empty `name` and a `channels` key. Missing, corrupt,
  or empty-name cache files are reported.

Exit code is `0` when the run is clean, non-zero when any issue is found.

## What "correct" means for a cache file

A cache file `~/.velbuscache/{address}.json` is written by `Module._cache()` from
`Module.to_cache()`. A correct file is valid JSON, is a dict, and has:

- `name`: non-empty string (module name was resolved from the bus)
- `channels`: object (may be empty only for interface-type modules)
- `sub_addresses` and `properties`: present as objects

Address in the filename is the **decimal** module address, matching the
`address:<N>` field in the `Module found:` log repr.

## Notes

- The second run reuses the cache produced by the first run — this is expected and
  is what verifies cache reuse works. Do not delete the cache between runs.
- If `retest.sh` cannot reach the chosen connection target, the run logs will
  show connection errors; report that rather than treating it as a code bug.
  The actual target used is echoed at the top of the output as `[retest] connect`.
- `read_bus.py` runs forever (`asyncio.sleep`), so each run is stopped with
  `timeout` (300s for run 1, 180s for run 2); a killed-by-timeout exit is normal
  and not an error.
