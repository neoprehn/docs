# Architecture (Current State)

This page describes the system **as it is built today**. How it got there is covered in the
[development history](../index.md) (the phase pages).

## Components

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

 iam-migrations (schema, profile "tools")
```

The graph visualization (conflict paths, root cause) runs directly in the ribbon UI via vendored
Cytoscape.js — the earlier `iam-neodash` PoC container (port 5005, phase 6) has been fully replaced
and removed since 2026-07-16 (see ROADMAP 9.2).

Everything is **local**, everything is in **a single Docker Compose**. The **backend** is
platform-independent as a container and replaces the earlier PowerShell runners (which are
retained as a host variant). It uses apoc-**core**; since `apoc.cypher.runFile` (apoc-extended) is
not available, the backend splits the `.cypher` files into individual statements and runs them via
the driver — `apoc.load.json` within them continues to run server-side on Neo4j.

## Data Layers in the Graph

| Layer | Content | Key/Dimension |
| --- | --- | --- |
| **Raw layer** | users, roles, profiles, authorizations, transactions, org fields | per **`dataset`** (system snapshot) |
| **Ruleset layer** | queries (functional building blocks), SoD rules, authorization conditions, CNF clauses | constant, per **`ruleset`** |
| **Results layer** | `(:SoDConflict)` findings, `(:Run)` with scope/provenance | per **`runId`**, regenerable |

The separation is deliberate: the results layer is **regenerable** (recomputed before every run)
and never feeds into the next derivation (see architecture decision AE-10 in the ROADMAP).
Findings arise in two steps: **materialization** (`(:User)-[:MATCHES]->(:Query)`) and
**analysis** (pure set logic over the rules' CNF clauses).

## Endpoints (Backend)

Long-running steps run as **asynchronous jobs**; progress via `GET /jobs/{id}`.

| Endpoint | Purpose |
| --- | --- |
| `GET /health`, `GET /profiles` | readiness; form master data (rulesets, profiles, sleeping) |
| `GET /datasets`, `GET /import-folders` | existing snapshots; import folders |
| `POST /imports`, `POST /imports/upload` | import (existing folder / ZIP upload) |
| `POST /runs`, `GET /runs` | start analysis; runs including finding counts |
| `GET /findings`, `GET /findings/export` | findings (table / CSV) |
| `POST /datasets/{d}/backup`, `GET /backups`, `…/download`, `…/restore` | backup/restore |
| `POST /datasets/{d}/clear`, `POST /reset` | clean up (ruleset & schema are preserved) |

## Trust Boundary

Only the operating interface is "outside". **No client data** leaves the environment: SAP
extracts (`data/import/`), the DB volume, and backups (`backups/`) stay local and are gitignored;
the repo contains exclusively logic/procedure. The backend only mounts these directories locally.

## Deployment

The distribution unit is **Docker Compose**. The stack is **Kubernetes-capable** (an internal,
secured cluster): Neo4j as a `StatefulSet` with a `PVC`, the backend as a `Deployment` (for now
one replica — jobs are held in memory), the password as a `Secret`, `data/import` + `backups` as
`PVC`s, access only cluster-internal or behind corporate auth. Details: phase 10 in the ROADMAP.

For machines without Docker (backend/Neo4j native as a Windows service/scheduled task, `git pull`
instead of a container update), there is a deliberate exception to the container-only principle:
[Native Windows installation](windows-native.md).
