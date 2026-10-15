# Troubleshooting

This page takes the topics from {doc}`updates` one level deeper: **what runs where**, **what each action does** and
**how to tell which layer is stuck**. All checks mentioned are **read-only** and need no administrator rights.

## Which layers are there?

| Layer | Native Windows installation | Docker (development machine) |
| --- | --- | --- |
| **Neo4j** (database, APOC) | Windows service `neo4j` | container `iam-neo4j` |
| **Backend** (FastAPI, Python) | scheduled task `IAM-Backend`, Python from `.venv-win` | container `iam-backend` |
| **UI** | files from `frontend\`, served by the backend | same (mounted) |
| **Queries, rulesets, catalogs** | files in the repo (`cypher\`, `rules\`, `checks\`, `config\`) | same (mounted) |
| **Update** | scheduled task `IAM-Update` (daily 06:00) | `docker compose` or `deploy\docker-update-test.ps1` |

A change only takes effect once the **layer that reads it has reloaded**. Almost everything below follows from that.

## What does each action do?

| Action | Fetch Git state | Python packages | Restart backend | Restart Neo4j |
| --- | :---: | :---: | :---: | :---: |
| Update code (Git Pull), Admin menu | yes | no | no | no |
| **Update now** (Manage) / Update tab / 06:00 task | yes | yes | yes (only for a new or not yet activated state) | no |
| **Restart** (Manage) | no | no | yes | yes |
| Rebooting the computer | no | no | yes | yes |
| Reloading the page in the browser | no | no | no | no |

Rebooting therefore does **not** replace the update: it only reloads what is already on disk.

## Symptoms and remedies

**Buttons without effect, empty views, "Not Found" after an update.**
The UI is newer than the running backend (Git Pull button fetched, backend not restarted). Remedy: **Update now**
(activates the fetched state). The update log then says "… not yet activated — catching up package installation and
backend restart".

**Backend does not start after an update (page unreachable).**
Most common cause: a new Python module or package is missing. The backend log ("IAM manage" → *Show backend log*)
shows `ModuleNotFoundError`. Remedy: **Update now** (installs the packages). If the package installation itself
fails, the update deliberately does **not** restart the backend; the update log names the exit code and the next run
tries again (check network/proxy).

**"Update now" says "Already up to date, no restart needed" although an update was fetched.**
An older `update.ps1` without the activation marker. Replace the file in the installation folder (see {doc}`updates`).

**Update aborts ("merge --ff-only failed").**
There are local changes in the repo folder. The update deliberately does not overwrite them; check
(`git -C <repo> status`) and revert or save the changes.

**Update task does not run / Update tab is greyed out.**
The task `IAM-Update` is missing or already running (a second start is rejected). Check the state in the *Update* tab
or in the Manage window; if the task is missing, run `install.exe` once.

**Queries/evaluations fail, but the page itself loads.**
Neo4j is unreachable or still starting. Look at the Neo4j log; the database needs a moment after a start (health
check). "Restart" in Manage restarts Neo4j **and** the backend.

**An import or run was aborted after a restart/update.**
Restarting the backend interrupts running jobs. They are **resumable** (banner "Last import interrupted" or
"Resume"). So do not schedule updates in the middle of an evaluation — especially not at 06:00.

**Import log shows "Deviation" or notes.**
Notes [1]–[9] are explainable differences and are explained in the log; a **deviation** means fewer data in the graph
than expected from the source. Then check the import log and the error log (Admin) and repeat the import.

## Where are the logs?

| Log | Location / access |
| --- | --- |
| Update run | `data\logs\windows-update.log` — Manage: *Show update log*, app: *Update* tab in the Import dialog |
| Backend | `data\logs\windows-backend.log` — Manage: *Show backend log* |
| Neo4j | `<Neo4j folder>\logs\neo4j.log` — Manage: *Show Neo4j log* |
| Failed jobs | app: Admin → *Error log* (survives restarts) |
| Activated Git state | `data\logs\deployed-head.txt` (marker written by `update.ps1`) |

## With Docker

With Docker the backend reloads Python files itself (`--reload`); a **new Python module** must however be listed in the
`Dockerfile` (`COPY`) and in `docker-compose.yml`, otherwise the backend does not start. Libraries and images are
updated with `deploy\docker-update-test.ps1` (smoke test, automatic rollback; see {doc}`updates`). Check containers:
`docker compose ps`, `docker logs iam-backend`.

## When to run `install.exe`?

Only for the initial installation, changed Neo4j/APOC versions, changed tasks/services/permissions or missing
prerequisites (Python, Git, Java) — **not** for regular updates.
