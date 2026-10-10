# Phase 10 — Distribution & Reproducibility

**Goal:** Get the project running identically on a different machine — as a colleague demo or as
your own second device (e.g., a laptop for development on the go) — **without client data
traveling via GitHub/the cloud**.

:::{admonition} Trust boundary
:class: important
Two strictly separate things travel by different routes: **code/logic** via Git/GitHub
(non-critical, publicly viewable), **client data** (SAP extracts, DB content, backups) only
manually and encrypted (USB stick, encrypted container) — never by email, cloud sharing, or
commit.
:::

## Prerequisite on the Target Machine

Docker Desktop with the WSL2 backend — a general Windows prerequisite, not an IAM-specific step
(details: [Docker docs](https://docs.docker.com/desktop/setup/install/windows-install/)).

A typical error on first start: *"WSL is missing"*. The fix in most cases (PowerShell as
administrator, then restart):

```powershell
wsl --install
```

If that fails, there are usually two causes: virtualization disabled in the BIOS/UEFI (task
manager → performance → CPU → "virtualization") or the Windows version too old (`winver`, at
least version 2004 / build 19041). RAM requirement: Neo4j requests **8 GB heap + 4 GB page cache**
via `docker-compose.yml` (see phase 9) — WSL2 reserves ~50% of the host RAM by default; from
**16 GB** host RAM onward this is comfortably sufficient, below that, consider reducing the
heap/page-cache values in `docker-compose.yml` for the target machine.

**Set `.wslconfig` explicitly (recommended, independent of the RAM calculation above).** WSL2's
default allocation varies by Windows/WSL version — instead of relying on it, set the limit
explicitly in `C:\Users\<username>\.wslconfig` (a plain text file, create it if needed):
```ini
[wsl2]
memory=16GB
```
With 32 GB of host RAM, this comfortably covers Neo4j's requirement and leaves Windows itself
enough room. Apply it afterward:
```powershell
wsl --shutdown
```
and restart Docker Desktop. Docker Desktop sometimes proactively points this step out itself
(e.g., after a memory-intensive operation such as the `neo4j-admin dump`/`load` further below).

## Transferring the Code — Two Ways

**Way A — `git clone` (clean, recommended with internet access to GitHub):**
```powershell
git clone https://github.com/neoprehn/iam.git
```

**Way B — copy the entire folder (e.g., via USB, no GitHub access needed):**
All paths in `docker-compose.yml` are relative — the folder is portable 1:1, independent of the
drive letter (`D:\` vs. `C:\` does not matter). `.env` can be copied along unchanged (the password
remains valid). Connect it to Git afterward (e.g., for later `git pull` updates), without losing
local content:
```powershell
cd <copied-folder>
git init
git remote add origin https://github.com/neoprehn/iam.git
git fetch origin
git checkout -f -B main origin/main
```
`git checkout -f` only overwrites **tracked** files with the GitHub state (non-critical given an
identical starting state); `.env`, `data/`, `backups/` are gitignored and remain untouched.

## Starting the Environment

```powershell
docker compose up -d --build
docker compose run --rm migrations      # create the schema, idempotent
```
Wait until `docker compose ps` shows **"healthy"** for `iam-neo4j`. App: `http://localhost:8000/`.

## Transferring the Analysis — Two Methods

The actual Neo4j graph is **not** in the project folder, but in a Docker-managed **named volume**
(`iam_neo4j_db`) — a plain folder transfer does not take it along. Two ways, depending on need:

**a) The app's own backup/restore** (ribbon "save") — dataset backup (source CSV) + run backup
(findings). Lightweight, operable via the UI, **but deliberately without evidence**
(`VIA_ROLE`/`VIA_PROFILE`) — root-cause graphs must be recomputed after a restore (the "evidence"
button). Suitable when only a single dataset/run is needed.

**b) `neo4j-admin database dump`/`load`** — the complete graph in a single file: all datasets, all
rulesets, all runs/findings **including evidence**, no recomputation needed. **Verified live
end-to-end on 2026-07-12** (5.66 GiB of raw data, dump in 41 s, load in 17 s, node count before/
after identical: 3,932,567).

Neo4j **Community Edition cannot pause a single database** (`STOP DATABASE` is Enterprise-only
and reports "Unsupported administration command") — the dump therefore needs the **entire `neo4j`
container stopped**, not just the database. On Windows/Git Bash, be sure to use **PowerShell**
(Git Bash incorrectly translates `/tmp` paths into Windows paths).

Dump (source machine):
```powershell
cd D:\Entwicklung\iam\iam
docker compose stop backend neo4j
docker compose run --rm -v "${PWD}\backups:/hostout" neo4j neo4j-admin database dump neo4j --to-path=/hostout --overwrite-destination=true
docker compose up -d
```
→ the file then sits under `backups\neo4j.dump`; like any client-data file, it travels only
manually (USB/encrypted).

Load (target machine, after `docker compose up -d --build` + `migrations`, with `neo4j.dump`
already copied into `backups\`):
```powershell
docker compose stop backend neo4j
docker compose run --rm -v "${PWD}\backups:/hostout" neo4j neo4j-admin database load neo4j --from-path=/hostout --overwrite-destination=true
docker compose up -d
```

## Code Changes After `git pull` — What the Running Container Picks Up Automatically

Almost all of the app code is **bind-mounted**, not baked into the image (`backend/app.py`,
`backend/convert.py`, `frontend/`, `cypher/`, `rules/`, `config/`); the backend container runs
with `uvicorn --reload`. A `git pull` on a second device is therefore, in the vast majority of
cases, **picked up automatically** — no rebuild, no restart:

| Change | Action needed? |
| --- | --- |
| `backend/app.py`, `backend/convert.py`, `frontend/*`, `cypher/*`, `rules/*`, `config/*` | **No** — hot reload |
| `backend/requirements.txt` (new dependency), `Dockerfile` | `docker compose up -d --build` |
| `migrations/*.cypher` (schema change) | `docker compose run --rm migrations` |

For context on how often these two exceptional cases actually occur (as of 2026-07-12, 146
commits of project history): `requirements.txt` changed 3 times, `migrations/` 4 times — so the
normal case is the automatic hot-reload path.

## Several of Your Own Working Devices (Home + Mobile)

Deliberately **deferred, not currently needed**: a fixed synchronization routine for client data
between two of your own devices. If needed, the same `dump`/`load` mechanism as above applies,
just recurring instead of one-time. For the code, simple discipline suffices (solo project, one
branch): commit + push before switching machines, `git pull` first on arrival.

A mobile device that carries client data makes the trust boundary more practically relevant than
on a stationary home machine: full-disk encryption (BitLocker) is recommended; when working with
real datasets on the go, observe the usual professional-confidentiality precautions (no public
Wi-Fi for data access, screen lock, privacy screen).

## Status & Open Items

**Verified (2026-07-12):** a complete folder transfer (relative paths, drive-independent), a
retroactive Git connection without data loss, `neo4j-admin dump`/`load` end-to-end including a
restore test in a throwaway volume, hot-reload behavior.

**Open:** finally cross-checking the `docker-compose.yml` versions; a standalone onboarding
document in the top-level README (this phase text already covers the content, but not yet in the
concise short form for the README); a synchronization routine for several of one's own devices
(see above, deliberately deferred).

**DoD (phase 10):** A colleague — or your own second device — gets the project running
identically, without client data touching the repo.
