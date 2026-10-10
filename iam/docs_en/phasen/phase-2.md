# Phase 2 — Data Import (Can-Do / Raw Data)

**Goal:** SAP authorization master data as a graph. **DoD:** both authorization paths
(role-based + direct) fully in the graph, verifiable by spot-checking against SAP.

Which tables/columns are extracted is in the [Extraction Guide](../extraktionsleitfaden.md). This
page describes the **tooling**, the **import strategy**, and the **procedure**.

## Tooling (No Python)

The import consists of three building blocks — all container-only or host PowerShell, **no
Python, no local Java** (AE-15):

1. **Converter** `load/Convert-Se16Export.ps1` (PowerShell). SE16 "unconverted" exports (`.txt`,
   Windows-1252, pipe-delimited, fixed width, marker column) → clean UTF-8 CSV, **tab-delimited**,
   with a header row carrying the SAP field names. Removes padding and `"` characters.
2. **Load scripts** `load/00…11_*.cypher` (Cypher). Executed by **`cypher-shell` inside the
   container** (`docker exec … -f /load/…`), batched via `apoc.periodic.iterate`. The `load/`
   directory is mounted read-only into the Neo4j container.
3. **Orchestration**: running the `load/*.cypher` files in order with `-P "dataset => '…'"` /
   `-P "lang => […]"` — bundled in the runner `run/run_import.ps1` (phase 5).

## Import Strategy

**Tables by pattern:**

| Source | Target | Pattern |
| --- | --- | --- |
| USR02 | `:User` (+ subtype labels) | node MERGE |
| AGR_DEFINE | `:Role` | node MERGE |
| TSTCT | `:Transaction` (+ text, `SPRSL='DE'`) | node MERGE |
| AGR_PROF / USR11 | `:Profile` (+ text) | node MERGE |
| AGR_AGRS | `CONTAINS` | edge MERGE |
| AGR_USERS | `ASSIGNED_TO` (+ validity) | edge MERGE |
| AGR_PROF / UST04 | `HAS_PROFILE` | edge MERGE |
| USOBT_C | `CHECKS` | edge MERGE (deduplicated, ran quickly) |
| AGR_1251 | `:Authorization` (+ HAS_AUTH/FOR_OBJECT) | node/edge MERGE + dynamic `f_<FIELD>` — **the heaviest step** |

**Cross-cutting conventions:**

- **One `$dataset` parameter** controls the path (`file:///$dataset/<table>.csv`) **and** the
  `dataset` property on all nodes/edges. Folder name = `dataset`.
- **MERGE on the synthetic `key`** (`<dataset>|<id>`, constraint-backed) → fast, duplicate-free
  lookups. The migrations from phase 1 must have been applied beforehand.
- **Date** `DD.MM.YYYY` → Neo4j `date`; `31.12.9999` → `9999-12-31`; `00.00.0000` → `null`.
  `*`/unrestricted is preserved (normalization only happens in the query, AE-06).
- **Batching** consistently uses `apoc.periodic.iterate`, `parallel:false`, `batchSize` 2–10k.
- **Performance — the key index is decisive.** The auth loaders (`08`/`18`/`19`/`20`)
  MERGE/MATCH on `Authorization.key`. Without the index on it, every access is a full label scan
  over >150k nodes — imports take hours. The index comes from migration `V003` (unique constraint
  `authorization_key`) — apply it **before** loading (the `migrations` service). The earlier
  assumption "aggregate-first gains nothing" only held *without* this index (both variants did a
  full scan).
- **`08` (AGR_1251) and `19` (UST12) as a two-pass.** First group field values per (auth, field)
  into a map via `collect(DISTINCT)`, then merge the node once and set all f_ properties in
  **one** `SET a += props` — instead of per-row `coalesce+toSet+setProperty` (O(n²), escalating
  batch times). `18`/`20` have no O(n²) (pure MERGE/MATCH) and only need the key index. Verified
  (byte-identical data): `08` ~3 h → 7 s, `18` 88 min → 3 s, `19` 4.6 h → 9 s, `20` >33 min → 3 s.
  The whole pipeline is now < 1 min.
- **Order:** `00 dataset → 01–09 nodes/edges → 10 SU24 → 11 subtype labels →
  99 validation`. Subtype labels (role `Composite`/`Single`) are deliberately last, so that roles
  created only later (via AGR_1251/AGR_USERS) are also captured.
- **Idempotency/re-run:** everything is MERGE-based → running again creates no duplicates. For a
  clean reload of a snapshot, reset it beforehand:
  `MATCH (n {dataset:$dataset}) DETACH DELETE n`.

## Procedure

```powershell
# 1. Export SE16 tables ("unconverted"), place the .txt under data/import/<dataset>/
#    (folder name = dataset, e.g. data/import/acme/)

# 2. Convert to CSV — ALL tables in the folder; sensitive credential columns
#    (PWDSALTEDHASH, BCODE, PASSCODE, OCOD*/BCDA*/CODV* ...) are automatically
#    discarded in the process (-DropColumnsLike), so they end up in no CSV.
.\load\Convert-Se16Export.ps1 -Folder data\import\acme

# 3. Ensure the schema (phase 1)
docker compose run --rm migrations

# 4. Load (order 00..11) — dataset = folder name, language via the $lang switch
$pw = $env:NEO4J_PASSWORD
$ds = "dataset => 'acme'"
# Language switch from .env (IMPORT_LANG, e.g. "DE,DEU,D"); empty = default DE,DEU,D
$codes = ($env:IMPORT_LANG, 'DE,DEU,D' -ne '')[0].Split(',').ForEach({ "'$($_.Trim())'" }) -join ','
$lang = "lang => [$codes]"
foreach ($f in (Get-ChildItem .\load\*.cypher | Sort-Object Name)) {
  docker exec iam-neo4j cypher-shell -u neo4j -p $pw -P $ds -P $lang -f "/load/$($f.Name)"
}

# 5. Validate
docker exec iam-neo4j cypher-shell -u neo4j -p $pw -P $ds -P $lang -f /load/99_validate.cypher
```

The **`$lang` switch** is a list of accepted language codes. Only the text scripts `09`
(TSTCT/`SPRSL`), `13` (TOBJT/`LANGU`), and `20` (USR13/`LANGU`) evaluate it: the first listed hit
wins, otherwise the first existing text is kept. The extra `-P $lang` on the other scripts is
harmless. The default covers the German spellings `DE`/`DEU`/`D` (SAP stores ISO-2, ISO-3, or the
1-character `SPRAS` code depending on the table). A different language = set `IMPORT_LANG` in
`.env` (e.g., `EN,ENG,E`).

:::{note}
`Convert-Se16Export.ps1` and the `.cypher` files are release/export-dependent regarding the date
format (**`DD.MM.YYYY`**, in this dataset). The language key, on the other hand, is parameterized
via the `$lang` switch (`IMPORT_LANG`) and no longer needs to be touched in Cypher — the default
list covers the German spellings (`DE`/`DEU`/`D`).
:::

## Result / Validation

`99_validate.cypher` counts per **node and edge type** (transaction, authorization, role
including single/composite, profile, auth object, user including subtypes; CHECKS, HAS_AUTH,
FOR_OBJECT, ASSIGNED_TO, HAS_PROFILE, CONTAINS …) and makes the import verifiable by spot-checking
against SAP.

> **No concrete figures in this documentation.** Volume figures are client-/snapshot-specific and
> do not belong in the repo (trust boundary: documentation = logic/procedure only). The current
> counters are delivered by `99_validate.cypher` on the respective `dataset`.

Both paths are modeled: **role-based** (`User -ASSIGNED_TO-> Role -HAS_AUTH-> Authorization
-FOR_OBJECT-> AuthObject`) and **direct** (`User -HAS_PROFILE-> Profile`). Data minimization: no
password/hash fields were loaded from USR02.

## Extended Sources (Scripts 12–24)

Additionally included beyond the core:

| Script | Source | Result |
| --- | --- | --- |
| 12 | V_USERNAME | `:User.name/.nameLast/.persNumber` (personal data, local) |
| 13 | TOBJT | `:AuthObject.text` (object texts, language-switched `$lang`) |
| 14 | USREFUS | `(:User)-[:HAS_REFERENCE]->(:User)` — reference-user assignment (if maintained in the client) |
| 15 | UST10C | `(:Profile)-[:CONTAINS]->(:Profile)` (collective profiles, + `:Collective`) |
| 16 | AGR_1252 | `:Role.org_<VARBL>` (org levels of derived roles) |
| 17 | AGR_TCODES | `(:Role)-[:HAS_MENU]->(:Transaction)` (role menu, informational) |
| 18 | UST10S | `(:Profile)-[:HAS_AUTH]->(:Authorization{scope:'profile'})-[:FOR_OBJECT]->…` (structure) |
| 19 | UST12 | field values `f_<FIELD>` on the profile templates (**lossless, all profiles**) |
| 20 | USR13 | `:Authorization.authText` (authorization texts, language-switched) |
| 21 | AGR_TEXTS | `:Role.text` (role texts, language-switched `$lang`) |
| 22 | AGR_1016B | `:Role.profileGenerated/.profileState` (profile generation status, concept-independent) |
| 23 | USORG | `(:OrgField)` — registry of the organizational fields (for the org dimension of the analysis) |
| 24 | — | Resolve org-level placeholders: `$<field>` in the role's own auths → real values from `Role.org_$<field>` (AGR_1252) |

:::{admonition} Lossless by construction
:class: important
Script 19 loads the profile field values **without** assumption-based narrowing — every profile
gets its actual values from the source, even if (in this concept) they match the role auths.
Other authorization concepts may differ; the import must not rely on it. Performance is solved
structurally, **never** by leaving out data. Likewise, the language/text filters are robust
(German preferred, otherwise fallback), not hard-coded to one language.
:::

## Further Snapshots (e.g., 2026)

Run the same set of scripts with a different `dataset` (= a new folder under `data/import/`).
Both snapshots then live in one DB and are comparable via the business `id` (see
[Data Model](../datamodel.md)).
