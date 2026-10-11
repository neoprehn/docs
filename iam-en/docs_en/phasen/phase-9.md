# Phase 9 — Application (Portable Docker App)

A **user-friendly, portable app** that makes the entire process of an analysis operable without
any JSON maintenance — **import, analysis, results, save, clean up**. It **builds on everything
that already exists** (runners, Cypher, profiles, the `dataset` dimension, findings in the
graph); nothing is thrown away. Operated in the browser at `http://localhost:8000/`.

:::{admonition} Trust boundary
:class: important
Only the operating interface is "outside". **No client data leaves** the environment: SAP extracts
(`data/import/`), the DB volume, and the backups (`backups/`) stay local and are gitignored.
:::

## Runtime Architecture

```
 Browser (http://localhost:8000/)
   │   static ribbon UI (frontend/index.html), served by the backend
   ▼
 iam-backend  (FastAPI, port 8000)            ← runner-as-API, asynchronous jobs
   │   import (folder/ZIP) · analysis · findings/export · backup/restore · clear/reset
   │   orchestrates the cypher/load/migrations files via the Neo4j driver
   ▼
 iam-neo4j  (Neo4j 5 Community + APOC, Bolt 7687 / browser 7474)
   ├─ raw layer per `dataset`  (user/role/profile/authorization/…)
   ├─ constant ruleset layer (query/SoDRule/AuthReq/clause)
   └─ regenerable findings (:SoDConflict) + (:Run) scope/provenance
```

Everything is **local**, everything is in **one compose file**. The backend is
**platform-independent** as a container (more portable than the PowerShell runners, which are
retained as a host variant). It uses apoc-**core**; because `apoc.cypher.runFile` (apoc-extended)
is not available, the `.cypher` files are split in the backend into individual statements and run
via the driver — `apoc.load.json` within them continues to run server-side.

## Interface — Ribbon Following the Lifecycle

The commands sit at the top in a **ribbon bar**, organized like the flow of an analysis; each
command opens a **dialog**, and the **main area** continuously shows the **results** (KPIs ·
runs · findings).

| Group | Command | Effect |
| --- | --- | --- |
| **1 Data** | Import | upload a ZIP **or** choose an existing folder → import job |
| **2 Analysis** | New run | parameter form (instead of JSON) → materialization + analysis |
| **3 Results** | Refresh · Export CSV | reload runs/findings · export the active run's findings as CSV |
| **4 Save** | Backup / Restore | create a source-data ZIP (opt. "backup & clear"), restore, download |
| **5 Manage** | Clean up | delete a dataset · reset everything (ruleset & schema are preserved) |
| **6 Admin** | Admin | rulesets/connectors: shows loaded rulesets; ruleset editor & filter-set import *(planned)* |

## API Surface (Runners as Endpoints)

Long-running steps run as **asynchronous jobs**; progress is shown via `GET /jobs/{id}`
(status/step/result counter).

| Endpoint | Purpose |
| --- | --- |
| `GET /health`, `GET /profiles` | readiness; form master data (rulesets, profiles, sleeping) |
| `GET /datasets`, `GET /import-folders` | existing snapshots; import folders (txt/csv count) |
| `POST /imports` `{dataset,…}` | import of an existing folder (convert→schema→load→validate) |
| `POST /imports/upload` (ZIP) | import via file upload (unzip→convert if needed→import) |
| `POST /runs` `{ruleset,dataset,asOf,profile…}` | materialization + analysis |
| `GET /runs` | list of `(:Run)` including finding/rule/sleeping counts |
| `GET /findings?runId=…&minRank=…` | findings of a run (table) |
| `GET /findings/export?runId=…` | findings as **CSV** (semicolon, UTF-8 BOM → Excel-ready) |
| `POST /datasets/{d}/backup` (`?clear=true`) | source-data backup (optionally clearing afterward) |
| `GET /backups`, `GET /backups/{file}/download` | list / download backups |
| `POST /backups/{file}/restore` | restore = unzip + re-import |
| `POST /datasets/{d}/clear`, `POST /reset` | clear a dataset / reset everything (ruleset & schema are preserved) |
| `GET|PUT /admin/masterdata/criticalities` | read/maintain the criticality catalog (level/label/rank/color/KRI) |
| `GET|PUT /admin/masterdata/modules` | read/maintain module master data |
| `GET|PUT /admin/masterdata/query-types` | read/maintain query-type master data |
| `GET|PUT /admin/masterdata/reason-codes` | read/maintain reason-code master data |
| `GET|PUT /admin/rulesets/{ruleset}/queries/{id}`, `GET|PUT /admin/rulesets/{ruleset}/sodrules/{id}` | edit query/SoD metadata in the overlay (catalog-validated) |

## Design Decisions

**Import in the container instead of PowerShell.** The SE16 converter
(`load/Convert-Se16Export.ps1`) has been ported to Python (`backend/convert.py`) — line-for-line,
including the credential denylist (password/hash columns are discarded), verified byte-identical
against the PS version. This makes the import path container-portable; PowerShell is no longer
needed.

**Backup/restore at the source-data level.** Neo4j Community can only run `neo4j-admin dump`
**offline** (DBMS stop) — unsuitable for an app button. Instead: backup = a ZIP of the converted,
**cleaned** `.csv` files (+ manifest), restore = unzip + **deterministic re-import**. This is
**online**, **portable** (a single file for colleagues), and trust-aware (never the raw `.txt`).
Findings are regenerable (AE-10) and are re-analyzed after a restore.

**Results separated from the source.** The backup secures the source (reproduces the graph);
findings are exported as a **CSV report** — not as a graph replay.

**Clear/reset preserve the ruleset & schema.** Both operations only delete the dataset-scoped
nodes (dataset clear) or all data except the ruleset layer and the migration tracking (reset).
This way, re-importing and re-analyzing is possible immediately afterward, without reloading the
ruleset. Batched via `apoc.periodic.iterate` (`cypher/admin/`).

## Starting

```bash
docker compose up -d --build          # neo4j + backend
# Browser: http://localhost:8000/
```

Create the schema once (or via the first import, which ensures it idempotently):

```bash
docker compose run --rm migrations
```

## Deployment & Operations

The distribution unit is **Docker Compose** (local, a single command). The stack is
**Kubernetes-capable** (e.g., an internal, secured corporate cluster): `neo4j` as a `StatefulSet`
with a `PVC` (Community = single instance), `backend` as a `Deployment` (for now 1 replica — jobs
are held in memory), the password as a `Secret`, `data/import` + `backups` as `PVC`s, code/config
baked into the image. Access runs **cluster-internal or behind corporate auth** (SSO/OIDC at the
ingress) — "public" means the internal, secured cluster, **not** the open internet.

**Deliberately no user/authorization concept of its own:** the app runs locally or is distributed
as a container; access is secured via the environment. An auth layer only comes once the app is
operated centrally for multiple users.

## Status & Open Items

**Implemented (build steps 1–4):** backend API over the runners, full import in the container
including ZIP upload, a ribbon interface following the lifecycle, results + CSV export,
backup/restore (including backup & clear, download), clear/reset.

**Implemented (addendum):** a branded **Cytoscape.js** frontend with a conflict-path graph on the
root-cause page (table/path graph/radial, color legend, full-screen toggle) — fully replacing the
NeoDash PoC from phase 6 (the library decision was tested on the consistency-check graph pilot
A1–A3, see phase 7 — NVL was ruled out, its license is only for Aura/a commercial Neo4j
subscription, not for the Community Edition used here). The NeoDash service/dashboard has been
removed since 2026-07-16 (see ROADMAP 9.2).

**Open (as of v1):** client **comparison** (two `dataset`s, delta) — now tracked as
[ROADMAP-V2.md, phase 3](https://github.com/neoprehn/iam/blob/main/ROADMAP-V2.md#phase-3--vergleich-interview-ergebnisse-und-erweiterte-exporte);
a **ruleset editor** (vendor base vs. custom, round-trip to the JSON) remains open backlog, see
[ROADMAP-V2.md](https://github.com/neoprehn/iam/blob/main/ROADMAP-V2.md).

**DoD (phase 9):** A portable app in which import, parameterized analysis, comparison, display,
export, and backup/restore can be operated without any JSON maintenance — locally, without
client data leaving the environment.
