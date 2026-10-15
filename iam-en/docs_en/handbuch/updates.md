# Updates: What Needs a Restart?

This page explains **what takes effect when after an update** — especially for machines where nobody
has development tools (native Windows installation, "third-party machine").

## In Short

- The app consists of two parts that live **in the same Git repository**: the **user interface**
  (frontend: HTML, JavaScript and text files) and the **backend** (Python program plus queries, rule
  sets and configuration). A `git pull` therefore **always updates both sets of files**.
- The **running programs**, however, pick up changes differently:
  - The **user interface** is read fresh from disk on every page load — **no restart needed**, just
    reload the page (if necessary **Ctrl + F5**).
  - The **backend program** (Python) is only read at startup — changes to it take effect **only after
    the backend is restarted**.
- **Rule of thumb:** if an update only changed the interface, queries, check catalog or
  configuration, reloading is enough. As soon as **Python code or Python packages** are involved, you
  need the full update **with** a restart.

## What Takes Effect When?

| What changed? | When does it take effect? | What to do? |
| --- | --- | --- |
| **Interface** (`frontend/`: pages, scripts, translations) | immediately on the next page load | Reload the page (**Ctrl + F5**). No restart. |
| **Queries** (`cypher/`) and **check catalog** (`checks/`) | on the next call of the function | Nothing. |
| **Configuration and master data** (`config/`) | read on use | Nothing. (Exception: the `.env` file is only read at startup → restart.) |
| **Rule sets** (`rules/`: single filters, SoD rules, risk catalog) | visible in the maintenance view immediately; **in the graph only at the next "New run"** (or after saving in the editor) | Start a new run for new rules. **Runs that were already computed do not change.** |
| **Import logic** (`load/`, `migrations/`) | at the next import | Nothing; schema migrations run idempotently with every import. |
| **Backend program** (`backend/*.py`) | **only after the backend is restarted** | Restart (see below). |
| **Python packages** (`backend/requirements.txt`) | only after package installation **and** restart | Full update ("Update now"). |
| **Neo4j** (version, memory, APOC settings) | never automatically | Manually only, e.g. via "Set memory + restart Neo4j". |
| **Documentation** (`docs/`) | only on Read the Docs | Not part of the running app. |
| **`install.exe` / `manage.exe` / `update.ps1`** (installation folder, not in the Git clone) | only by replacing the file | New versions are **handed over manually**; a pull does not change them. Replacing `update.ps1` is enough, `install.exe` stays untouched. |

An update **never** touches data, backups or the `.env`: `data/`, `backups/` and `.env` stay
unchanged. New program logic also applies **to new runs** — existing runs and results are not
recomputed retroactively.

## On the Third-Party Machine (Native Windows Installation)

Here the backend runs **without automatic reloading**. There are three ways to fetch the code:

| Way | What happens | Backend restart? | Python packages? |
| --- | --- | --- | --- |
| **Automatic, daily at 06:00** (task `IAM-Update`) | Fetches the latest state, installs packages, restarts the backend — but **only if there was a new or not yet activated state** | yes | yes |
| **"Update now"** (window "Manage IAM", `manage.exe`) | like the daily task, immediately | yes (on a new or not yet activated state) | yes (likewise) |
| **"Update code (Git Pull)"** (Admin menu in the app) | fetches **only the files** (`git pull`) | **no** | **no** |

It follows that:

- **The Git Pull button is the quick way for pure interface, query, catalog or rule-set changes.**
  Afterwards, reloading the page is enough. If the update nevertheless contained Python changes, the
  **old** backend stays active until "Update now" activates the fetched state.
- **If an update contains Python changes**, the **old** program version keeps running until the
  backend restarts. The new interface may then call functions the old backend does not know yet —
  typical signs are messages like "Not Found", empty views or buttons that do nothing. **Remedy: click
  "Update now" in the "Manage IAM" window** (activates the fetched state) or "Restart".

**The activation marker.** The update script records in `data\logs\deployed-head.txt` **for which state
packages and restart last ran successfully**. If the code was fetched beforehand with the Git Pull
button, "Update now" (or the daily task) sees that the fetched state is **not yet activated** and
**catches up** with the package installation and backend restart. The update log then says: "State …
is already fetched …, but not yet activated — catching up on package installation and backend
restart." If the package installation fails, the backend is deliberately **not** restarted (so it does
not start with missing packages) and the next run tries again.

:::{admonition} Older installations
:class: note
If the machine still has an **older `update.ps1`** (without the activation marker), "Update now"
reports **"Already up to date, no restart needed"** after the Git Pull button and restarts
**nothing** — Python changes stay ineffective there until the next restart, and new Python packages
are not installed. You can tell from the update log: the line reads "Bereits aktuell (…)" **without**
"und aktiv". Remedy: replace the file **`update.ps1` in the installation folder** (the folder with
`install.exe`/`manage.exe`) with the new version. `install.exe` does **not** need to be run again and
`manage.exe` does not need to be rebuilt: the task and the window only call the file by path. Until
then: use the Git Pull button only when you are sure there are **no** Python changes, otherwise
"Update now" **without** pressing the button first; if that is not enough, "Restart" helps.
:::

- **"Restart"** restarts **Neo4j and the backend** (not just the backend).
- New **Python packages** are installed **exclusively** by the full update (daily task or "Update
  now") — also when the state was fetched beforehand with the Git Pull button.
- A **restart interrupts a running run**. It can be resumed but is unnecessary — so do not schedule
  updates in the middle of an evaluation, especially not at 06:00 when a run is still going. If the
  machine follows the `main` branch, **every new commit** restarts the backend at the next update run.
- The update logs are available in the "Manage IAM" window ("Show update log", "Show backend log");
  an update deliberately aborts if there are local changes in the installation folder instead of
  overwriting them.

## With Docker (Development Machine)

The backend runs here in development mode with **automatic reloading**: the Python files that are
mounted individually in `docker-compose.yml` are reloaded by the server itself when they change (a
short server restart; a running evaluation job may abort). The interface, queries, check catalog,
rule sets and configuration are mounted folders and take effect immediately. A `git pull` in the
project folder is therefore usually enough. Exceptions:

| Change | What to do |
| --- | --- |
| **New Python file** in the backend | Must be entered in the `Dockerfile` (`COPY`) **and** `docker-compose.yml` (mount), then `docker compose up -d --build backend`. Otherwise the backend does not start at all after the pull (`ModuleNotFoundError`). |
| **`requirements.txt`** or **`Dockerfile`** | `docker compose up -d --build` (rebuild the image). |
| **`docker-compose.yml`** (ports, mounts, Neo4j settings) | `docker compose up -d` — containers are recreated. |

The "Update code (Git Pull)" button only exists in the native Windows installation; in the container
it reports that it is not available there.

## Updating Libraries and Docker Components (with Test and Rollback)

Versions are **pinned**: Python base image (`backend/Dockerfile`), Neo4j image (`docker-compose.yml`),
neo4j-migrations (`docker/neo4j-migrations.Dockerfile`) and all Python packages (`backend/requirements.txt`).
Updating takes two steps: raise the pins in the files, then run `deploy\docker-update-test.ps1`
(no administrator rights needed, only the Docker client is used):

```powershell
deploy\docker-update-test.ps1                 # update, test, automatic rollback on failure
deploy\docker-update-test.ps1 -VolumeBackup   # additionally back up the Neo4j data volume (for a Neo4j version jump)
deploy\docker-update-test.ps1 -Mode Check     # only test the current state, change nothing
deploy\docker-update-test.ps1 -Mode Rollback  # manually go back to the saved state
```

Sequence: the script saves the **running** images as `iam-rollback/*:pre`, builds and starts the new state and runs a
**smoke test**: Neo4j and APOC (including matching versions and `apoc.load.json` on the rulesets), backend (`/health`,
UI, database access), package consistency (`pip check`), import of all modules, PDF/Excel generation, the **unit tests
in the new image**, the migrations and an **unchanged graph** (fingerprint of node and edge counts per label — no
numbers are printed). If anything fails, the script restarts with the saved images itself and checks that the stack
is healthy again. Afterwards revert the changed pins with `git checkout -- <file>`. `-ForceRollbackTest` lets you
rehearse the rollback path.

```{note}
The **native Windows installation** has its own versions (`Neo4jVersion`/`ApocVersion` in `install.ps1`; APOC must
match the Neo4j patch version). They are not touched by the Docker update; raising them there requires a rebuilt
`install.exe`/`manage.exe` and a handover to the third-party machine.
```

## Further Reading

Installation, tasks and administration of the Windows installation:
[Native Windows installation](../technik/windows-native.md).
