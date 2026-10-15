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
| **Python packages** (`backend/requirements.txt`) | only after package installation **and** restart | Full update ("Update now") — see the trap below. |
| **Neo4j** (version, memory, APOC settings) | never automatically | Manually only, e.g. via "Set memory + restart Neo4j". |
| **Documentation** (`docs/`) | only on Read the Docs | Not part of the running app. |
| **`install.exe` / `manage.exe`** | only by replacing the file | Rebuilt files are **handed over manually**; a pull does not change them. |

An update **never** touches data, backups or the `.env`: `data/`, `backups/` and `.env` stay
unchanged. New program logic also applies **to new runs** — existing runs and results are not
recomputed retroactively.

## On the Third-Party Machine (Native Windows Installation)

Here the backend runs **without automatic reloading**. There are three ways to fetch the code:

| Way | What happens | Backend restart? | Python packages? |
| --- | --- | --- | --- |
| **Automatic, daily at 06:00** (task `IAM-Update`) | Fetches the latest state, installs packages, restarts the backend — but **only if there was a new state** | yes | yes |
| **"Update now"** (window "Manage IAM", `manage.exe`) | like the daily task, immediately | yes (on a new state) | yes (on a new state) |
| **"Update code (Git Pull)"** (Admin menu in the app) | fetches **only the files** (`git pull`) | **no** | **no** |

It follows that:

- **The Git Pull button is the quick way for pure interface, query, catalog or rule-set changes.**
  Afterwards, reloading the page is enough.
- **If an update contains Python changes**, the **old** program version keeps running until the
  backend restarts. The new interface may then call functions the old backend does not know yet —
  typical signs are messages like "Not Found", empty views or buttons that do nothing. **Remedy: click
  "Restart" in the "Manage IAM" window.**

:::{admonition} Trap: "Update now" after the Git Pull button
:class: warning
If the Git Pull button has already fetched the state, "Update now" reports **"Already up to date, no
restart needed"** and exits — **without** restarting the backend and **without** installing Python
packages. The hint in the Git Pull button ("for that keep using 'Update now'") therefore does not
apply in this case.

**Rule of thumb:** when in doubt, **do not** use the Git Pull button but go straight to **"Update
now"** — it does everything in one step. If the button was already used and the update contained
Python changes, **"Restart"** helps. If **new Python packages** were involved, they stay
**uninstalled** in this case (only the full update installs them, and only when it fetches the new
state itself) — the backend may then abort at startup with an import error. So use the Git Pull
button only when you are sure there are **no** Python changes.
:::

- **"Restart"** restarts **Neo4j and the backend** (not just the backend).
- New **Python packages** are installed **exclusively** by the full update (daily task or "Update
  now"), and only if it fetches the new state itself.
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

## Further Reading

Installation, tasks and administration of the Windows installation:
[Native Windows installation](../technik/windows-native.md).
