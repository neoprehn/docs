# Native Windows Installation (without Docker)

The standard path is **container-only** via Docker Desktop/WSL2 (see [Architecture](architektur.md)
and the main `README.md`). For exactly one case, there is a deliberate, additional departure from
this: a third-party machine on which Docker Desktop must not or cannot be installed, but the
individual components (Python, Java, Neo4j) can be. Scripts, the full guide, and troubleshooting
live in the repo under [`deploy/windows-native/`][repo-deploy] — this page describes the purpose,
procedure, and the trust boundary for it.

[repo-deploy]: https://github.com/neoprehn/iam/tree/main/deploy/windows-native

## What Is Created

- **Neo4j Community Server** as a native Windows service (no container) — memory/APOC/import
  settings are taken 1:1 from `docker-compose.yml`, so that the Docker and native installation
  behave functionally identically.
- **Backend** (`uvicorn`) as a scheduled task that runs automatically on every system start, even
  without a login — functionally the Windows equivalent of the `iam-backend` container.
- A **daily update task**: `git fetch` + `merge --ff-only`, synchronize Python dependencies,
  restart the backend. Deliberately a simple pull instead of a real CI/CD build server — no
  additional operational overhead, code comes unmodified from the git repo. It aborts (instead of
  overwriting) if the local state cannot be updated via fast-forward.
- A small **management window** ("Manage IAM", desktop shortcut) for start/stop/restart, "update
  now", opening the web app, viewing the update/Neo4j log, and a verify click — without having to
  operate PowerShell.
- Both entry points (installer, management window) are also available as standalone `.exe` files
  (`ps2exe`, `-requireAdmin` manifest) — no manual PowerShell window, no file-association
  pitfalls on double-click.

The package (`install.ps1`, `manage.ps1`, `update.ps1`, `start-backend.ps1`, `build-exe.ps1`) is
self-contained and runnable: `install.ps1` clones the app itself via `git clone`. A prior full
checkout is not necessary — the folder is enough, e.g., sent to the third-party machine as a ZIP.

## Installation

**Recommended:** double-click `install.exe` — it automatically requests admin rights via a UAC
dialog. An alternative for automated runs, or when only the `.ps1` files are available, as an
administrator:

```powershell
.\install.ps1
```

Without `-InstallDir`, a folder selection dialog opens for the target location (canceling uses the
default `C:\iam`). The script is idempotent — running it multiple times skips steps already
completed.

:::{admonition} Trust boundary: do not choose a target folder under OneDrive
:class: important

The chosen target folder contains SAP extracts, backups, and credentials — that is, real client
data (see below, "Where is the data?"). A OneDrive-synchronized path would automatically upload
these to the Microsoft cloud — this is not a performance detail, but violates this project's trust
boundary (client data never leaves the local machine). `install.ps1` automatically detects a
OneDrive path and explicitly asks before installation; the default answer is "no".
Recommendation: a simple local path such as `C:\iam`.
:::

Immediately after installation, go through the **verify step** (README, section "Verify"): Neo4j
reads the ruleset files under `rules/` via a fixed path (`apoc.load.json('file:///rules/...')`,
identical to the Docker bind mount), which `install.ps1` replicates without a container via an NTFS
junction. This is the only non-trivial assumption in this setup and can be directly tested against
with a single `cypher-shell` command.

## Where Is the Data?

Everything that is created locally per installation hangs off **one** place — the chosen target
folder (`$InstallDir`, default `C:\iam`):

| What | Where | In git? |
|---|---|---|
| SAP extracts (raw data) | `<InstallDir>\data\import` | No (gitignored) |
| Backups (dataset/run ZIPs) | `<InstallDir>\backups` | No (gitignored) |
| Credentials (`NEO4J_PASSWORD`) | `<InstallDir>\.env` | No (gitignored) |
| App code (backend/frontend/cypher/rules) | `<InstallDir>\...` | Yes |

The **Neo4j database itself** is deliberately located outside of `$InstallDir`, directly under the
drive root (`<drive>:\neo4j\neo4j-community-<version>\...`) — technically because of the rules
junction, but practically also an additional safeguard: even if `$InstallDir` were accidentally
located in a synchronized folder, the database would remain unaffected by it.

## Updates

Automatically daily (scheduled task `IAM-Update`) or manually via a click in the management
window. An update run only touches **the code** — `data/`, `backups/`, and `.env` remain
untouched; Neo4j itself (version, memory/APOC configuration) is not automatically updated, just as
a Docker Compose change there would not trigger an automatic update either.

## Details, Troubleshooting, Uninstallation

Fully documented in [`deploy/windows-native/README.md`][repo-deploy] in the repo — among other
things, management via the command line as an alternative to the management window, handling a
failed fast-forward update, memory tuning, and uninstallation.
