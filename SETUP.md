# Setup guide

How to get this folder working on a machine, connect to the robot, and fix the usual
problems. For a short overview see [README.md](README.md).

## 1. Requirements

- Python **3.10 or newer** (`python3 --version`).
- A way to reach the robot. Set `"connection"` in `config.json`: `direct` if the machine is on the
  robot's Ethernet, `tunnel` if it is on Wi-Fi and goes through the Raspberry Pi (see CONNECTION.md).
- For the login: SSH access to the bridge host (`desk_tunnel.bridge_host` in `config.json`, `tunnel`
  mode only) and your Desk username and password.
- macOS for the double-click launchers. On Linux the server works the same; use the
  equivalent commands in section 5.

## 2. Install

**Fresh clone.** Nothing lab-specific is committed, so a clone starts from templates:

```sh
bash setup.sh
```

**Moving an existing setup.** On the old machine `bash setup.sh pack` writes
`../<folder>-portable.zip` (about 100 KB) without the venv, the login token or the archive. It
**does** include your local `config.json`, `task-policy.json`, `robot-cert.pem` and `plans/`, so
keep it private. Unzip it anywhere and run `bash setup.sh` in that folder.

`setup.sh` will:

1. check for Python 3.10+;
2. create `.venv` (and rebuild it if it was copied from another machine);
3. install the pinned dependencies from `requirements.lock.txt`;
4. create `config.json` and `task-policy.json` from `config.example.json` and
   `task-policy.example.json` if they do not exist (it never overwrites them), and fill
   `certificate_sha256` from `robot-cert.pem` when that file is present;
5. validate `config.json` and confirm its pin matches `robot-cert.pem`. If values are still missing it
   says so and carries on, so you still get the registration below;
6. make the launchers executable and clear the macOS quarantine flag;
7. print the MCP registration with this folder's real paths.

A different Python: `PYTHON=/path/to/python3.12 bash setup.sh`.

On a fresh clone, finish with the three steps in section 6, "First-time configuration".

## 3. Register the MCP

Use the block `setup.sh` printed. Templates:

**Codex**: add to `~/.codex/config.toml`:

```toml
[mcp_servers.franka-real]
command = "/path/to/franka-mcp/.venv/bin/python"
args = ["/path/to/franka-mcp/server.py"]
startup_timeout_sec = 20
tool_timeout_sec = 40
```

**Claude Code**:

```sh
claude mcp add franka-real -- /path/to/franka-mcp/.venv/bin/python /path/to/franka-mcp/server.py
```

**Claude Desktop** (`claude_desktop_config.json`):

```json
{ "mcpServers": { "franka-real": {
    "command": "/path/to/franka-mcp/.venv/bin/python",
    "args": ["/path/to/franka-mcp/server.py"] } } }
```

Restart the client afterwards. The server name is `franka-real`; the tools start with
`franka_real_`.

## 4. Check it works (nothing moves)

```sh
python3 -m franka_mcp.config check   # config + certificate pin, offline
.venv/bin/python server.py --probe    # one read-only status read from the robot
```

The probe makes read-only requests and needs the robot reachable. In your client you can
also call `franka_real_capabilities`, which also reports whether you are logged in.

## 5. Connect each session

1. **`Connect Desk over WiFi.command`**: opens the tunnel (`tunnel` mode only; skip it when `connection` is `direct`). It shows the defaults from
   `config.json`; press Enter to accept or type another bridge host or user. Enter the
   SSH password when asked and **keep the window open**.
2. **`Connect Franka.command`**: asks for the Desk username and password (hidden) and
   saves a session token. It then offers to enable tasks.
3. **`Enable Franka Tasks.command`** (optional): lists taught tasks, shows each one you
   pick, and enables it only if you type `ENABLE`. Each run replaces the approvals, and
   blank means none, so nothing can execute until you do this.

Without the launchers (Linux, or a blocked file):

```sh
ssh -N -L 127.0.0.1:8443:<robot_host>:443 <user>@<bridge_host>   # terminal 1, keep open
.venv/bin/python -m franka_mcp.login                               # terminal 2
.venv/bin/python -m franka_mcp.login --enable-tasks                # optional
```

## 6. Configuration reference

### First-time configuration

`config.json` and `task-policy.json` are yours alone: local, Git-ignored, created from the committed
`*.example.json` templates by `bash setup.sh`.

1. Save the robot's certificate as `robot-cert.pem` and check it is your robot's (commands below;
   compare its SHA-256 fingerprint with the one your browser shows for `https://<robot_host>/` on a network you trust).
2. Edit `config.json`: `robot_host`, `connection` (`direct` or `tunnel`) and, for `tunnel`, the
   `desk_tunnel` section.
3. Run `python3 -m franka_mcp.config init` (fills the empty `certificate_sha256` from `robot-cert.pem`;
   it never overwrites anything else), then `python3 -m franka_mcp.config check`.

### `config.json`

| Key | Meaning |
|---|---|
| `robot_host` | Robot IP address. The template has Franka's factory address, `172.16.0.2`. |
| `connection` | `direct` (robot_host:443) or `tunnel` (local SSH tunnel via the Pi). Default `direct`; applies to the MCP and the login. |
| `certificate_sha256` | SHA-256 of the robot's TLS certificate (64 lowercase hex characters). Empty in the template; `init` fills it from `robot-cert.pem`. Checked before any request. |
| `timeout_seconds` | Network timeout, above 0 and at most 10. Default 5. |
| `desk_tunnel.bridge_host` | Default SSH bridge for the launcher; empty means the launcher asks. |
| `desk_tunnel.bridge_user` | Default SSH user. The template has `pi`, the Raspberry Pi OS default; set your own. |
| `desk_tunnel.local_port` | Local tunnel port, 1024 to 65535. Default 8443. Always bound to 127.0.0.1. |

### `task-policy.json`

The execution policy, also local: `approved_tasks` (task id mapped to the exact content hash; empty
means nothing can run), `required_home` (Ready Home joint angles and tolerances) and an optional
`default_workflow`. The template enables nothing. The enable step edits only `approved_tasks`.
If the file is missing, nothing can run.

### Using a different robot or replacing its certificate

Only after you have verified it is the right robot:

```sh
openssl s_client -connect <robot_ip>:443 </dev/null 2>/dev/null | openssl x509 > robot-cert.pem
openssl x509 -in robot-cert.pem -outform der | shasum -a 256
```

Put the IP in `robot_host`, then either put the hash in `certificate_sha256` or set it to `""` and
run `python3 -m franka_mcp.config init`, and finish with `python3 -m franka_mcp.config check`. Task ids and names in `franka_mcp/desk/client.py` and `plans/` belong to
the original robot's taught tasks; a different robot needs those tasks created first.

## 7. Keeping secrets out of Git

`.gitignore` excludes: this lab's `config.json` and `task-policy.json` (addresses, SSH user, certificate
pin, enabled tasks; only the `*.example.json` templates are committed), the Desk session
(`.session.json`, which holds an admin token),
`.franka-*` temp files, `.env*`, all keys and certificates (`*.pem`, including
`robot-cert.pem`, `*.crt`, `*.key`), Codex and other client registration files
(`codex-config*.toml`, `.codex/`, `.mcp.json`), anything named like credentials, password
or token, `.venv/`, `diagnostics/`, `plans/`, `archive/` and zip bundles.

`config.json`, `task-policy.json`, `robot-cert.pem` and `plans/` stay on your disk and in
`bash setup.sh pack` bundles, but never reach GitHub. `plans/` holds the checked task data that `franka_mcp/desk/client.py` reads before
starting a task and in the `franka_real_prepare_*` tools; a clone without it refuses to
execute (it fails closed), so copy `plans/` over from your packed bundle. A fresh clone also has none of the
local files: `bash setup.sh` creates `config.json` and `task-policy.json` from the templates, and
`python3 -m franka_mcp.config check` tells you what is still missing (usually the pin, until you save
`robot-cert.pem`; see "First-time configuration" in section 6).

Before pushing, check what would be committed:

```sh
git status --short --ignored      # .session.json must appear with "!!"
git ls-files | grep -i -E "session|token|secret|password|\.key"   # expect no output
```

`.gitignore` only protects files that are not already tracked. If any of these were
committed earlier, stop tracking them (this keeps the files on disk):

```sh
git rm --cached --ignore-unmatch config.json task-policy.json robot-cert.pem plans codex-config.toml .session.json
git commit -m "Stop tracking local-only files"
```

That does not erase them from past commits. Check with
`git log --all --oneline -- .session.json config.json task-policy.json robot-cert.pem plans 'codex-config*'`. If
`.session.json` appears, remove it from history, treat that token as leaked, and log out of
Desk or restart the session on the robot. The certificate and the Codex template hold no
credentials, so for them a clean-up commit is enough.

If `config.json` or `task-policy.json` were committed earlier, their history still shows this lab's
addresses, SSH user and certificate pin. They are not credentials, but rewrite the history or keep that
repository private if you do not want them public.

Also scan the tracked files for lab-specific values. Only loopback addresses and Franka's factory
address `172.16.0.2` should appear, and no 64-character hashes, home-directory paths or email addresses:

```sh
git grep -nE '([0-9]{1,3}\.){3}[0-9]{1,3}|[0-9a-f]{64}|/(Users|home)/[A-Za-z]|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[a-z]{2,}'
```

A force-push does not remove an old commit from GitHub: anyone with its ID can still open it. If
something private was pushed, delete and recreate the repository (or ask GitHub Support to purge it),
and change any password it contained.

## 8. Troubleshooting

| Message or symptom | Fix |
|---|---|
| `Could not open the Desk tunnel at 127.0.0.1:8443` | Run step 1 and keep its window open. Check `desk_tunnel.local_port` matches. |
| `Desk login required` or `Desk login expired` | Run step 2 again. |
| `Desk tunnel presented a different robot certificate` | The tunnel points at the wrong machine. Check `robot_host` and the bridge host. |
| `Robot TLS certificate changed; verify the robot…` | Do not just update the pin. Verify the robot, then follow section 6. |
| `Robot read failed … check Ethernet and local network access` | This machine cannot reach `robot_host:443`. Check the cable, IP and routing. |
| `Task is not locally enabled with this exact content` | Run `Enable Franka Tasks.command`; any change to the task changes its hash. |
| Launcher "cannot be opened" on macOS | Run `bash setup.sh` (clears quarantine), or right-click then Open. |
| `.venv` errors after copying the folder | Run `bash setup.sh`; it rebuilds the venv. |
| `config.json … is missing` or invalid | Run `bash setup.sh` (creates it from `config.example.json`), then see section 6. |
| `certificate_sha256 is empty` | Save the robot's certificate as `robot-cert.pem`, then `python3 -m franka_mcp.config init` (section 6). |
| `Python 3.10 or newer is required` | Install one and run `PYTHON=/path/to/python3.12 bash setup.sh`. |

## 9. Maintenance

- Add or upgrade a dependency: edit `requirements.txt`, then
  `.venv/bin/python -m pip install -r requirements.txt` and
  `.venv/bin/python -m pip freeze > requirements.lock.txt`.
- Remove the install: delete `.venv/` and `.session.json`; remove the registration from
  your client.
- Code style: `ruff format .` and `ruff check .` (settings in `pyproject.toml`).
- Old material lives in the local `archive/` folder, which is not in Git.
