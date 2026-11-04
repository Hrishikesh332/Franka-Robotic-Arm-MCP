# Changelog

## stable v1 — published repository

- The repository holds only the MCP. Unit tests and golden files stay local (`tests/` is Git-ignored).
- Code formatted and linted with ruff (settings in `pyproject.toml`); behaviour is unchanged and the
  26 tools keep their names, descriptions and schemas. The Ready Home joint angles are one constant.
- New README with an animated overview (`docs/franka-mcp.svg`).

## 0.1.1 — no lab-specific values in committed files

- `config.json` and `task-policy.json` are now local and Git-ignored. `config.example.json` and
  `task-policy.example.json` are the committed templates: Franka's factory address, empty pin and bridge
  host, no enabled tasks, no default workflow.
- New `python3 -m franka_mcp.config init` creates the local files from the templates (never overwrites)
  and fills `certificate_sha256` from `robot-cert.pem`. `bash setup.sh` runs it and no longer stops when
  the config still needs values.
- `check` explains an empty pin; a missing `config.json` says how to create it.
- `franka_real_capabilities` no longer fails if `task-policy.json` does not exist yet (nothing is enabled).
- Docs use placeholders and the tests use a documentation address. The tests no longer read the real
  config, and `tests/test_hygiene.py` blocks IPs, hashes, home paths and emails in committed files.
- Removed a stale folder name from the "Desk login required" message.

## 0.1.0 — structured package
- Split the single-file server into the `franka_mcp` package: `app`, `cli`, `config`, `paths`, `login`,
  `desk/` (reader, client), `tools/` (status, tasks, control, prepare), `resources/`, `prompts/`.
- `server.py` is now a thin entry point at the same path, so existing client registrations keep working.
- All 26 tools keep their names, descriptions, input schemas and annotations (pinned by `tests/golden/`).
- `desk/client.py` is the former `web_control.py`; the only change is where the project paths come from.
- New: 2 resources and 2 prompts; `--version`; local-only `--transport sse|streamable-http`;
  `python -m franka_mcp.login` and `python -m franka_mcp.config` replace `connect.py` and `franka_config.py`.
- New: 29 unit tests, `pyproject.toml`.
- Earlier in this cleanup: `connection` mode (`direct` / `tunnel`), tunnel settings in `config.json`,
  `setup.sh`, and the fix that stopped enabling tasks from wiping `task-policy.json`.
