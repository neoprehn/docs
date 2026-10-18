# Data Model

Fixed schema (labels, relationship types, property keys). Reproducibly created via
`neo4j-migrations` (AE-02), see [Phase 1](phasen/phase-1.md).

## Two Separate Time Axes

The model deliberately separates two things that are both "time", but mean different things:

| Axis | Meaning | Place in the model |
| --- | --- | --- |
| **Validity** | When an assignment is valid *within* an extract (reference date) | `validFrom`/`validTo` as `date` on the edge (AE-07/AE-08) |
| **Extract/version** | Which export snapshot: e.g., `2025-12-31` vs. `2026-12-31` | `dataset` property on every node/every edge |

## The `dataset` Dimension (Versioning & Comparison)

A **`dataset`** is a complete, self-contained SAP extract (one client at one point in time), e.g.,
`acme-2026-12-31`. Every node and every edge carries the `dataset` property. This means several
snapshots live in parallel in **one** DB and are comparable (diff query via the business `id`); a
snapshot can be removed in isolation via `DETACH DELETE … WHERE n.dataset = $x`.

**Distinction from multiple clients:** Different *clients* are **not** mixed via `dataset`, but
kept in **separate Neo4j instances** (confidentiality; moreover, Neo4j Community can only have one
user database). `dataset` serves to compare snapshots of the *same* client. Cross-client
benchmarks only on anonymized data.

### Community Peculiarity: Synthetic Key

Neo4j Community only knows **single-property unique constraints** — composite keys
(`(dataset, id)`) as a constraint are Enterprise. Solution: a synthetic key

```
key = "<dataset>|<id>"
```

with a single-property unique constraint. The import `MERGE`s on this. Additionally, a
**composite index** on `(dataset, id)` (composite *indexes* are allowed in Community) for fast,
dataset-filtered lookups and the version comparison.

## Nodes (Labels)

| Label | Business `id` | Source | Subtype labels (layering) |
| --- | --- | --- | --- |
| `Dataset` | extract name (globally unique) | — (registry/provenance) | — |

In addition to `id`/`uid`, `Dataset` also carries **`asOf`** (Neo4j `date`) — the extract's
reference date, as a rule the download date of the SAP tables (AE-16). `asOf` is **not a
run/filter input**: it is set once on first import (`load/00_dataset.cypher`, ON CREATE) and read
server-side from the dataset by all analyses/consistency checks (`backend/app.py`,
`_dataset_asof()`, lazy backfill for older imports without the value: derived from the import
folder's file timestamps — `_infer_dataset_asof()`, all tables of an extract practically always
share the same export day —, only if the folder is missing, as a last resort, `today`). A
deliberate correction runs exclusively globally via `PUT /datasets/{id}/asof`.
| `User` | `BNAME` | USR02 | `User:Dialog\|System\|Communication`, `User:Active\|Locked` |
| `Role` | `AGR_NAME` | AGR_DEFINE | `Role:Composite\|Single\|Derived` |
| `Profile` | `PROFN` | USR10/UST10 | `Profile:Single\|Collective\|Critical` |
| `Authorization` | — (no business key, AE-03) | AGR_1251 | — |
| `AuthObject` | `OBJECT` (e.g., `S_TCODE`) | TOBJ | `AuthObject:Critical` |
| `Transaction` | `TCODE` | TSTC | `Transaction:Critical` |

Primary label + subtype + ruleset marker (`:Critical`). Org values remain **properties**, not
their own labels/nodes (AE-05). `*`/unrestricted is "taken as it comes" and only normalized in the
query logic (AE-06).

### Authorization: Node, Not Edge (AE-03)

An authorization groups AND-combined field values (e.g., `ACTVT=01` AND `BUKRS=1000`). This
grouping must not disintegrate into individual edges — hence a dedicated `Authorization` node,
whose field values sit as **properties**. Identity arises via the edges (`HAS_AUTH`,
`FOR_OBJECT`), not via a business key.

## Edges (Relationship Types)

| Type | From → To | Source | Properties |
| --- | --- | --- | --- |
| `ASSIGNED_TO` | `User` → `Role` | AGR_USERS | `validFrom`, `validTo` (`date`, AE-07) |
| `CONTAINS` | `Role`(Composite) → `Role`(Single) | AGR_AGRS | — |
| `DERIVED_FROM` | `Role`(Derived) → `Role`(Master) | AGR_DEFINE | — |
| `HAS_PROFILE` | `User`/`Role` → `Profile` | UST04 / AGR_1016B | possibly `validFrom`/`validTo` |
| `HAS_AUTH` | `Role`/`Profile` → `Authorization` | AGR_1251 | — |
| `FOR_OBJECT` | `Authorization` → `AuthObject` | AGR_1251 | — |
| `CHECKS` | `Transaction` → `AuthObject` | USOBT_C/USOBX_C (SU24) | — |
| `PROPOSES` | `Transaction` → `AuthObject` | USOBT_C (SU24, `FIELD`/`LOW`/`HIGH`) | `field`, `low`, `high` — one edge per (TCode, object, field) row; several edges between the same two nodes are the normal case (several fields per object, or differing suggested values per TCode). The basis for the USOBT-based query builder, see [ROADMAP-V2.md](https://github.com/neoprehn/iam/blob/main/ROADMAP-V2.md#phase-1--admin-editor-v2-und-regelpflege). |
| `CONTAINS` | `Profile`(Collective) → `Profile`(Single) | UST10C | — |
| `HAS_REFERENCE` | `User` → `User` (reference user) | USREFUS | — |
| `HAS_MENU` | `Role` → `Transaction` (role menu, informational) | AGR_TCODES | — |
| `GRANTS` | `Role`/`Profile` → `Authorization` | derived (`load/91_materialize_grants.cypher`) | — |

**Invariant:** edges always run *within* a `dataset` (both endpoints share the same `dataset`
value). An extract is self-contained.

**`GRANTS` is not a raw-data edge**, but the pre-flattened transitive closure over
`CONTAINS`/`HAS_PROFILE` down to the `Authorization` (evidence performance) — it saves the
otherwise necessary `CONTAINS|HAS_PROFILE*0..4` path search on every analysis. It is materialized
once per dataset on import (not per ruleset/run) and regenerates on every (re-)import.

### Import Evidence (Derived Metadata Layer)

Likewise not raw data, but written by the backend after every import (completeness proof against
the source SAP extract, see {ref}`consistency-checks`, consistency check I1):

```
(:Dataset)-[:HAS_IMPORT]->(:Import {dataset, importedAt, importedAtEpoch, lang, durationSec, source, options,
                                   appVersion, derivedRoles, reconstructedAt})
                          -[:HAS_TABLE]->(:ImportTable {table, sourceRows, droppedColumns, filteredRows, expectedGraph, rowsSource,
                                              fileName, fileBytes, fileMtime, sha256, hashOf})
                          -[:HAS_NODE_COUNT]->(:ImportNodeCount {labels, count})
                          -[:HAS_EDGE_COUNT]->(:ImportEdgeCount {type, count})
```

One `(:Import)` node per import run (never overwritten → a history across re-imports).
`ImportNodeCount.labels` is the **exact** label combination of a node (e.g.,
`['User','Dialog','Active']`), not just the main label — queries must sum accordingly across all
combinations that contain a sought label, instead of expecting exact equality.

## Diagram

```{mermaid}
graph LR
  User(("User"))
  Role(("Role"))
  Profile(("Profile"))
  Auth(("Authorization"))
  AuthObject(("AuthObject"))
  Transaction(("Transaction"))

  User -- "ASSIGNED_TO (validFrom/validTo)" --> Role
  Role -- "CONTAINS" --> Role
  Role -- "DERIVED_FROM" --> Role
  User -- "HAS_PROFILE" --> Profile
  Role -- "HAS_PROFILE" --> Profile
  Role -- "HAS_AUTH" --> Auth
  Profile -- "HAS_AUTH" --> Auth
  Auth -- "FOR_OBJECT" --> AuthObject
  Transaction -- "CHECKS" --> AuthObject
```

*Every node additionally carries `dataset` (+ a synthetic `key`); the `Dataset` registry node
stands beside it without edges. Can-do runs `User → Role/Profile → Authorization → AuthObject`;
`Transaction → AuthObject` (SU24) is the connecting point for did-do (AE-12).*

## Validity Along the Path (AE-08)

Analyses are tied to a reference date (parameterized). With nested collective roles, the date
predicate must act on **every** relevant edge of the path
(`all(rel IN relationships(p) WHERE …)`), otherwise false-positive/-negative hits arise.
`TO_DAT = '99991231'` (unbounded) is mapped on import to a far-future date or a `null`
convention.

## Schema in Migrations

- `migrations/V001__constraints.cypher` — unique constraints on `Dataset.id` and the synthetic
  `key` of `User`, `Role`, `Profile`, `AuthObject`, `Transaction`.
- `migrations/V002__indexes.cypher` — composite lookup indexes `(dataset, id)`, a `dataset` index
  for `Authorization`, as well as the range index `ASSIGNED_TO(validFrom, validTo)`.

Extensions as needed: `AuthField`, `ObjectClass`, `OrgValue` (only if a pivot is needed),
`Service`/`FioriTile` (S/4) — as further migrations. `V003__authorization_key.cypher` adds the
unique constraint on `Authorization.key` (performance, see [Phase 2](phasen/phase-2.md)).

## Analysis Layer (Phase 3)

Above the can-do layer lie three clearly separated areas (details:
[Phase 3](phasen/phase-3.md)):

**Ruleset — constant, without `dataset`** (reference data, per `ruleset`):
- `(:Query)` (functional building block) `-[:REQUIRES]->(:AuthReq)` (object/field/values/`andLogic`).
- `(:SoDRule) -[:USES {var}]-> (:Query)` and the CNF clauses
  `(:SoDRule)-[:HAS_CLAUSE]->(:Clause)-[:NEEDS]->(:Query)`.
- `(:Risk)` (CSI-native), linked per rule.

**Org-field registry — per `dataset`:** `(:OrgField)` from USORG (which fields are org-relevant).
**Org value names — per `dataset`:** `(:OrgValue {field, value, text})` from T001/T001W/T014/T024E/TVKO
(company code, plant, credit control area, purchasing/sales organization) — display enrichment of org values
only, not part of the authorization logic; key `dataset|field|value` (constraint `orgvalue_key`, V007).
**License type:** `User.licenseType` (+ `licenseSystem`) from USR06 (loader `31`).

**Run/snapshot layer — regenerable, with provenance** (AE-10):
- Intermediate result "who can do what": `(:User)-[:MATCHES {ruleset, asOf, runId}]->(:Query)`.
- Findings: `(:User)-[:VIOLATES]->(:SoDConflict {ruleId, ruleset, dataset, asOf, runId,
  criticality, userSleeping})-[:BASED_ON]->(:SoDRule)`. Risk/criticality comes from the rule and
  is only attached.

Keys analogous to the can-do layer via synthetic `key` (`ruleset|id`); the constraints
(`query_key`, `sodrule_key`, `clause_key`, `sodconflict_key`) are created idempotently by the
ruleset loader or the evaluator.
