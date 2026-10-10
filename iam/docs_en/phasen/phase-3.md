# Phase 3 — Analysis Logic (Checks & SoD)

Individual-authorization checks and SoD conflict analysis on the can-do graph. The rulesets are
**query-/expression-based** (SAP R/3 / CSI tools): a **query** is a functional building block
(authorization objects + transaction codes), an **SoD rule** is a boolean expression over query
variables.

## Axes of an Analysis

```
SoD run  =  ruleset (constant)  ×  dataset (system)  ×  reference date  ×  profiles (org / scope / user type / sleeping)
```

Rulesets are constant reference data (repo); only the system (`dataset`) changes. Everything else
is a **parameter** — nothing is hard-wired in Cypher.

## Loading a Ruleset into the Graph

`cypher/ruleset/load_ruleset.cypher` (`-P dir=…`, `-P ruleset=…`) loads the normalized JSON
(`rules/<ruleset>/`) via `apoc.load.json` into the constant ruleset layer: `(:Query)`,
`(:Query)-[:REQUIRES]->(:AuthReq)`, `(:SoDRule)`, and the CNF clauses
`(:SoDRule)-[:HAS_CLAUSE]->(:Clause)-[:NEEDS]->(:Query)`. `load/23_org_fields.cypher` loads the
registry of organizational fields `(:OrgField)` from USORG.

## Individual Authorizations (Matching)

`cypher/checks/query_match.cypher` determines which users satisfy a query — according to the
`combinationSemantics`: values AND/OR per `andLogic`, fields/objects **AND**, transaction codes
**OR** (`*` = any), the auth part **AND** the transaction-code part; `*`/ranges `LOW..HIGH` cover
it (AE-06). Effective authorizations run via roles/profiles/composite/collective;
`ASSIGNED_TO` is filtered by the reference date. Simple checks such as `cypher/checks/sap_all.cypher`
are the degenerate case.

## SoD — Two Steps via the Intermediate Result

The expensive part (matching against auths) happens **once**; SoD is afterward pure set logic:

1. **`cypher/sod/materialize_matches_*.cypher`** — materializes the intermediate result "who can
   do what": `(:User)-[:MATCHES]->(:Query)` (only the SoD-relevant queries).
2. **`cypher/sod/evaluate_sod_*.cypher`** — evaluates on top of that: a user violates a rule if
   **every clause** (CNF) contains ≥1 query matched by them → `(:SoDConflict)` with provenance
   (`ruleset`, `dataset`, `asOf`, `runId`). **Risk/criticality comes from `(:SoDRule)`** and is
   only attached — never re-evaluated.

Both steps (plus `cypher/sod/explain_sod_*.cypher` for the evidence) have, since the
progress/resume extension (ROADMAP archive), each been split into three files instead of a single,
uninterruptible call: `..._reset`/`..._init` (one-time, only on a fresh phase start),
`..._candidates` (the list of units — query/rule/actor), `..._one` (the core logic for **one**
unit, called unit by unit by the backend, with progress + a checkpoint between each unit). The
business logic is unchanged; only the iteration control moves from `apoc.periodic.iterate`
(internal to Neo4j) to a Python loop (`_run_phase()` in `backend/app.py`).

## Parameters

| Parameter | Meaning | Default / Example |
| --- | --- | --- |
| `ruleset` | constant ruleset | `sap_r3` / `csi` / `csi_bi` |
| `dataset` | variable system | import folder name |
| `asOf` | **reference date** (Neo4j `date`) — role validity **and** sleeping | **set to the snapshot date, not "today"** |
| `userTypes` | user-type filter (subtype labels) | `[]` = all · `['Dialog','Service']` (A/S) · `['Dialog']` |
| `sleepDays` | sleeping threshold in days | `180` (freely selectable) |
| `orgFilters` | org-field restriction per field, a 2-level criteria tree (ROADMAP 9.3) | `{}` = all "don't care" (like `*`) · `{BUKRS:{op:'OR',children:[{type:'group',op:'AND',children:[{type:'value',value:'1000'},{type:'value',value:'2000'}]},{type:'value',value:'3000'}]}}` = "(1000 AND 2000) OR 3000" |

Named profiles for these are in `config/analysis_profiles.json` (org modes, scope selectors,
user-type profiles, sleeping) — a run binds profiles instead of individual flags.

### Reference Date — Important

The `asOf` must match the **data snapshot**. An extract is a point-in-time snapshot; with
`asOf = today` against an older snapshot, for example, "sleeping" is true for **everyone**
(formally correct, but meaningless), and time-limited role assignments are evaluated incorrectly.
Reference date = snapshot date.

### Org Dimension

- **Default "don't care"** (`orgFilters = {}`): org fields do not restrict — "can the user
  perform the function at all".
- **`filtered`**: the org field's auth value must cover the filter (`*`/ranges count, AE-06). For
  each field, a **2-level criteria tree** (`{op:'AND'|'OR', children:[...]}`): a child is either
  a leaf (`{type:'value',value}`/`{type:'range',from,to}`) or a group
  (`{type:'group', op:'AND'|'OR', children:[Leaf,...]}` — deliberately only one level deep, no
  group-within-group). This allows expressions like "(1000 AND 2000) OR 3000" per field. Older
  profiles in the flat format (`{op:'AND'|'OR', values:[...]}`/`{op:'RANGE', from, to}`) are
  automatically translated into this tree form on read (`backend/app.py:_normalize_org_filter()`),
  never written back to disk.
- :::{admonition} Open: org-level placeholders
  :class: warning
  Org-mandatory (derived) roles carry a **placeholder** (`$BUKRS`) in the auth field; the real
  values sit on the role (`Role.org_$<field>` from AGR_1252). The org filter currently only checks
  `f_<field>` and does **not yet** resolve the placeholder — `filtered` is therefore only complete
  for literal org values. Resolving the placeholder is the next development step.
  :::

### Sleeping Rule

`userSleeping` = no logon within `sleepDays` days before `asOf` (or never). As a dedicated check
(`cypher/checks/sleeping_users.cypher`) **and** as a flag on every `(:SoDConflict)` — this allows
separating "active vs. sleeping" conflicts.

## Presentation

Findings are materialized (`(:SoDConflict)`); **NeoDash** reads and displays them in a
parameterizable way (KPI tiles, conflict table with drill-down, graph of conflict paths),
dashboard JSON under `dashboards/`. See phase 6.

**DoD:** A reproducible SoD run for a freely selectable ruleset, dataset, reference date, and
profile, with a complete chain of evidence (rule → clauses → matched queries → user; reference
date, run, ruleset).
