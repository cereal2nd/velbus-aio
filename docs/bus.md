# Bus transports (`velbusaio.bus`)

Velbus I/O is split into two backends under `velbusaio/bus/`:

| Package                 | DSN                              | Role                                   |
| ----------------------- | -------------------------------- | -------------------------------------- |
| `velbusaio.bus.manager` | `manager://host:port`            | Signum Manager REST API v2 + WebSocket |
| `velbusaio.bus.raw`     | `tcp://`, `tls://`, serial paths | Direct `VelbusProtocol` link           |

`Velbus` (`velbusaio/controller.py`) holds a single `_backend: VelbusBusBackend` and
delegates `connect`, `start`, `stop`, `scan`, `send`, `sync_clock`, and queue draining.

## `VelbusBusBackend`

Defined in `velbusaio/bus/base.py`. Both backends implement:

- `is_connected`, `connect`, `start`, `stop`, `scan`, `send`, `sync_clock`
- `schedule_reconnect()` — no-op on manager; raw bus retries TCP/serial
- `wait_on_all_messages_sent_async()` — raw send queue only

Use `velbus.manager_backend` when you need manager-only APIs (`set_memo_text`,
`wait_for_bus_link`, thing-id maps). Raw internals are exposed as `velbus.raw_backend`
for tests.

See [manager.md](./manager.md) for Signum Manager details.
