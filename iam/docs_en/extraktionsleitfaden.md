# Extraction Guide (Can-Do / Raw Data)

Which SAP tables, which **columns**, and in what format are extracted. Guiding principle: **data
minimization** — only what the analysis needs. In particular, **no password hashes** and no
plain-text personal data that is not needed for the can-do analysis are extracted.

:::{admonition} Please verify against your own system
:class: warning
Some column/semantics details are release- and system-dependent. Verify points marked with ⚠️
once against the specific SAP system (SE11/SE16) before a production run.
:::

## Format Conventions

- **Delimiter: tab** (`\t`), UTF-8, with a header row. The converter generates this automatically
  from the SE16 "unconverted" export; for a direct CSV export, choose tab as the delimiter (the
  load scripts read `FIELDTERMINATOR '\t'`).
- **Column headers = SAP field names** (e.g., `BNAME`, `AGR_NAME`). This way the load scripts are
  independent of the extraction method (SE16 export, table download, report).
- Files live locally under `data/import/` and are referenced in Cypher as `file:///<name>.csv` —
  **no** Windows absolute paths (Linux container, AE-15).
- **`dataset`**: not a CSV field, but a **Cypher parameter** per run (e.g., `acme-2026-12-31`).
  The runner sets it; all nodes/edges receive it (the version dimension).
- **Date fields** (SAP `YYYYMMDD`): converted to Neo4j `date` on import (AE-07).
  `TO_DAT = '99991231'` (unbounded) → `9999-12-31`; empty/`00000000` → `1900-01-01`.
- **`*`/unrestricted**: stored "as delivered" (no upfront mapping); normalization only happens in
  the query logic (AE-06).

## Which Tables to Download?

The SE16 exports (one `.txt`/`.csv` per table, file name = table name) belong in the dataset
folder. The converter checks the **minimal set before import** (source:
`config/required_tables.json`) — **if a required table is missing, it aborts.** Optional tables
only enrich the data (only a notice appears if they are missing).

### Required (Minimal Set)

| Table | Purpose |
| --- | --- |
| **USR02** | user master record (type, lock, last logon, validity) |
| **AGR_DEFINE** | role definition (collective role via `PARENT_AGR`) |
| **AGR_AGRS** | collective role → single roles |
| **AGR_USERS** | user ↔ role (with validity) |
| **AGR_PROF** | role → generated profile |
| **UST04** | user → directly assigned profile (e.g., `SAP_ALL`) |
| **AGR_1251** | role authorization data (object/field/values per role) |
| **TSTCT** | transaction texts |
| **USOBT_C** | SU24 suggested values (transaction code → object/field; source for `CHECKS`) |
| **UST10S** | profile authorizations (profile contents) |
| **UST12** | authorization field values for the profile authorizations |
| **T000** | client master data (company/client/location) — basis for the company/client/time-slice grouping on the start page |

### Optional (Enrichment)

| Table | Adds |
| --- | --- |
| **USOBT** | SU24 suggested values, SAP standard (counterpart to `USOBT_C`) — the *effective* check indicator for a (transaction code, object) pair needs both layers, since the customer table can override standard values |
| **USOBX** | SU24 check indicator (active/suppressed), SAP standard — basis for a future check-indicator verification on authorization objects; ⚠️ column `OKFLAG` not yet verified |
| **USR11** | profile texts |
| **USR13** | authorization texts |
| **TOBJT** | authorization object texts |
| **AGR_TEXTS** | role texts (language-dependent, `$lang` switch) |
| **V_USERNAME** | user names (first/last name) |
| **USREFUS** | reference users |
| **UST10C** | collective profiles (profile → contained profiles) |
| **AGR_1252** | org levels of derived roles |
| **AGR_TCODES** | role menu (transaction codes of the role) |
| **AGR_1016** | profile generation status of roles (`GENERATED`/`PSTATE`, see section 22 below — **not** `AGR_1016B`) |
| **AGR_1016B** | profile assignment per role (`AGR_NAME`/`PROFILE`) — content-wise redundant with `AGR_PROF`, currently without its own loader |
| **USORG** | registry of org-relevant authorization fields, basis of the org dimension (used by loader `23`) — without it, org-field detection is lost |
| **AGR_FLAGS** | role flags/switches — usefulness for can-do still to be clarified, currently without a loader |
| **AGR_1250** | manually maintained (not via SU24 suggestion) authorizations per role — a potential deviation/risk indicator, currently without a loader |
| **USR06** | license type per user — more of an SAP license-management than a can-do topic, listed anyway at user request, currently without a loader |

> `ADRP` (first name in addition to `V_USERNAME`) is likewise listed as optional, but contains
> personally identifiable plain-text data (PII) — clarify the purpose of use before extraction;
> therefore deliberately not listed in the table above.

The exact load order follows from the file names under `load/` (`00…99`); the required **columns
per table** are listed below.

## Columns per Table

### 01 — USR02 (Users) → `:User`
| Column | Usage |
| --- | --- |
| `BNAME` | user ID (business `id`) |
| `USTYP` | user type → subtype label (`A`=dialog, `B`=system, `C`=communication, `S`=service, `L`=reference) |
| `UFLAG` | lock indicator → subtype `Active`/`Locked` **plus** differentiated lock reasons (see below) |
| `GLTGV` | valid from (`date`) |
| `GLTGB` | valid to (`date`) |
| `TRDAT` | last logon (`date`, optional) |
| `CLASS` | user group (optional) |
| `PWDINITIAL` | password status indicator (`0`/`1`/`2`, **not a hash**) → `pwdInitial`, see below |
| `PWDCHGDATE` | last password change (`date`, **not a hash**) → `pwdChgDate` |
| `PWDSETDATE` | date of (initial/new) issuance (`date`, **not a hash**) → `pwdSetDate` |

**Lock reasons from `UFLAG`** (bit flags, decomposed on import via `apoc.bitwise.op`; ⚠️ confirm
values against your own system): `0` = not locked; bit `32` = due to failed logons; bit `64` =
by administrator (local); bit `128` = by administrator (global/ZBV). Combinations are possible
(sum of the bits, e.g., `192` = `64`+`128`). Stored as the property `lockReasons` (list) +
`uflag` (raw value); subtype label `Active` (UFLAG = 0) or `Locked` (otherwise).

**`PWDINITIAL` indicator** (⚠️ not consistently publicly documented by SAP, verify against your
own system before production use — derived empirically from the test data, see
`KONSISTENZCHECKS.md` B3): `1` correlates there 100% with `PWDCHGDATE = PWDSETDATE` ("password
never changed since issuance" — the solid finding); `2` is a mixed case (e.g., an admin-set/reset
password, a weaker signal); `0` = regularly changed.

**Deliberately NOT extracted — only the genuine hash/algorithm fields:** `BCODE*`, `BCDA*`,
`OCOD*`, `CODV*`, `PASSCODE`, `PWDSALTEDHASH`, `PWDHISTORY` (converter denylist
`convert.py:DROP_DEFAULT`). **Not** excluded are pure status/date fields such as
`PWDINITIAL`/`PWDCHGDATE`/`PWDSETDATE` — these are not hashes and do not allow the password itself
to be reconstructed (analogous to `UFLAG`/`TRDAT`, which have been loaded for a while already).
Plain-text name/address data (USR21/ADRP) is not needed for can-do — optional and separate
(did-do phase: observe pseudonymization).

> **Defense in depth:** If the hash columns were exported anyway, the converter already discards
> them during conversion (`Convert-Se16Export.ps1`, parameter `-DropColumnsLike`) — they end up
> in no CSV. The load scripts read only the needed columns anyway, so the actual hash data never
> reaches the graph.

### 02 — AGR_DEFINE (Roles) → `:Role`
| Column | Usage |
| --- | --- |
| `AGR_NAME` | role name (business `id`) |
| `PARENT_AGR` | **collective role** (confirmed) — the parent composite role; congruent with `AGR_AGRS` |
| `TEXT` | role description (single-language; canonically from `AGR_TEXTS`, see 21) → `r.text` |
| `CREATE_USR` / `CREATE_DAT` | creator / creation date (`dd.mm.yyyy` → `date`) → `r.createUsr` / `r.createDat` |
| `CHANGE_USR` / `CHANGE_DAT` | last changer / change date → `r.changeUsr` / `r.changeDat` |

Creator/changer + dates feed the **role detail page** (master-data tab). A separate **generation
date** is not contained in `AGR_DEFINE`/`AGR_1016` and is therefore not displayed.

Subtype `Composite`/`Single` is **derived**: composite = occurs in `AGR_AGRS` as `AGR_NAME` (or as
`PARENT_AGR` in AGR_DEFINE), otherwise `Single`. The subtype `Derived` and the `DERIVED_FROM` edge
(derived role → master) have **no confirmed source** in the currently extracted tables
(`PARENT_AGR` = collective role, not a derivation template) → **deferred** until the derivation
information is available.

### 21 — AGR_TEXTS (Role Texts) → `:Role.text`
| Column | Usage |
| --- | --- |
| `AGR_NAME` | role name (joins to `:Role`) |
| `SPRAS` *(or `SPRSL`)* | language key → `$lang` switch; the loader robustly reads either |
| `TEXT` | role description → `r.text` |

The canonical, **language-dependent** source for role texts (`AGR_DEFINE.TEXT` in `02` is
single-language and has gaps). Runs after `02`: the preferred language from `$lang` overwrites,
otherwise the first existing text remains. See `load/21_role_texts.cypher`.

### 22 — AGR_1016 (Profile Generation Status) → `:Role` properties
| Column | Usage |
| --- | --- |
| `AGR_NAME` | role name (joins to `:Role`) |
| `GENERATED` | `'X'` = profile generated → `r.profileGenerated` (true if **all** profiles of the role) |
| `PSTATE` | profile status (raw, uninterpreted) → `r.profileState` (distinct list) |

> ⚠️ **The table is named `AGR_1016`, not `AGR_1016B`.** The `GENERATED`/`PSTATE` columns are in
> `AGR_1016`. An earlier version read `agr_1016b.csv` → the file was missing, `r.profileGenerated`
> stayed `NULL` for all roles (and consistency check **D4** was thus ineffective). Please extract
> `AGR_1016`.

Lossless/concept-independent: records whether a role's generated profiles are present/active. In
concepts with non-generated/outdated roles, their AGR_1251 authorizations are not (fully) active
at runtime — the **finding** for this (affected roles) belongs in the analysis (phase 3, AE-10);
here only the raw fact. A role can have several profiles (`COUNTER`>1, split above 150 objects) →
aggregation per role. See `load/22_role_profile_status.cypher`.

:::{admonition} ⚠️ PSTATE meaning not officially documented
:class: warning
`PSTATE` is deliberately stored **raw**. Value observed so far: `'A'` = **active** (currently
generated version) — a commonly used SAP convention, but **not** consistently publicly documented
(analogous to `PWDINITIAL`, see USR02). The role detail page shows this interpretation only for
`'A'` (with a notice icon); other codes appear raw. Verify against your own system before
production use, should further codes appear.
:::

### 03 — AGR_AGRS (Role Hierarchy) → `CONTAINS`
| Column | Usage |
| --- | --- |
| `AGR_NAME` | collective role (composite) |
| `CHILD_AGR` | contained single role |

### 04 — AGR_USERS (User-Role Assignment) → `ASSIGNED_TO`
| Column | Usage |
| --- | --- |
| `UNAME` | user ID |
| `AGR_NAME` | role |
| `FROM_DAT` | valid-from of the assignment (`validFrom`, `date`) |
| `TO_DAT` | valid-to of the assignment (`validTo`, `date`; `99991231`→`9999-12-31`) |

### 05 — AGR_PROF (Role → Profile) → `HAS_PROFILE`
| Column | Usage |
| --- | --- |
| `AGR_NAME` | role |
| `PROFILE` | the role's generated authorization profile |

`AGR_PROF` (columns `AGR_NAME`, `PROFILE`) suffices for `HAS_PROFILE` — `AGR_1016B` is **not**
additionally needed.

### 06 — UST04 (User → Profile Directly) → `HAS_PROFILE`
| Column | Usage |
| --- | --- |
| `BNAME` | user ID |
| `PROFILE` | directly assigned profile (e.g., `SAP_ALL`) |

### 07 — USR11 (Profile Texts) → `:Profile` properties
| Column | Usage |
| --- | --- |
| `PROFN` | profile name (business `id`) |
| `PTEXT` | profile text |
| `LANGU` | language (filter, e.g., `D`/`E`) |

Profile nodes are created from the referencing sources (AGR_PROF, UST04) and are enriched here
with the text.

### 08 — AGR_1251 (Authorization Data) → `:Authorization`, `HAS_AUTH`, `FOR_OBJECT`
| Column | Usage |
| --- | --- |
| `AGR_NAME` | role (carrier of the authorization) |
| `OBJECT` | authorization object (→ `:AuthObject`, e.g., `S_TCODE`) |
| `AUTH` | auth instance name (grouping key) |
| `FIELD` | authorization field (e.g., `ACTVT`, `BUKRS`, `TCD`) |
| `LOW` | value/from-value |
| `HIGH` | to-value (for ranges) |
| `DELETED` | indicator — rows with `X` are filtered out |

**Grouping (AE-03):** one `:Authorization` node per (`AGR_NAME`, `OBJECT`, `AUTH`) within a
`dataset`. Field values as properties on the node: per field `f_<FIELD>` as a list; ranges as
`"LOW..HIGH"`. `*` is preserved (AE-06).

### 09 — TSTC (Transaction Catalog) → `:Transaction`
| Column | Usage |
| --- | --- |
| `TCODE` | transaction code (business `id`) |
| `PGMNA` | program name (optional) |

### 10 — USOBT_C (SU24: Suggested Values) → `CHECKS` + `PROPOSES`
| Column | Usage |
| --- | --- |
| `NAME` | transaction code |
| `OBJECT` | authorization object (SU24 suggestion) |
| `FIELD` | authorization field (suggested value) |
| `LOW` | suggested from-value (can be empty — then only the field itself is relevant, without a default) |
| `HIGH` | suggested to-value (usually empty, except for genuine ranges) |

The edge `(:Transaction)-[:CHECKS]->(:AuthObject)` is built from the unique (`NAME`, `OBJECT`)
pairs (`load/10_su24_checks.cypher`). Additionally (since 2026-09-08,
`load/11_su24_proposals.cypher`) a `(:Transaction)-[:PROPOSES {field, low, high}]->(:AuthObject)`
edge per (`NAME`,`OBJECT`,`FIELD`) row — the basis for the USOBT-based query builder
([ROADMAP-V2.md](ROADMAP-V2.md#phase-1--admin-editor-v2-und-regelpflege)). `FIELD`/`LOW`/`HIGH`
are **already included in the extraction scope so far** (confirmed on 2026-09-08 against a real
dataset, 100% field population) — no additional SAP-side extraction needed, just unused until
now. `LOW`/`HIGH` can contain SAP parameter-ID placeholders (`$EKORG`, `$WERKS`, … instead of a
concrete value) — this marks an org-level field, analogous to the already-known org fields of the
can-do analysis.

The distinction "check active/suppressed" (`USOBX_C.OKFLAG`) is still missing — if needed, this
can be refined later via the optional `USOBX_C` (verify the column name/meaning against a real
extract sample before use; no extract available yet).

### 25 — T000 (Client Master Data) → `:Dataset` properties
| Column | Usage |
| --- | --- |
| `MANDT` | client number → `d.mandant` |
| `MTEXT` | company name/client label → `d.companyName` |
| `ORT01` | location → `d.city` |
| `MWAER` | currency → `d.currency` |
| `LOGSYS` | logical system → `d.logicalSystem` |

⚠️ T000 lists **all** clients known in the system, not just the extracted one — a real extract had
6 rows instead of the one originally assumed. Which row belongs to the extract is not stated
explicitly anywhere; `load/25_dataset_meta.cypher` therefore determines it via `USR02.MANDT`
(SE16 extractions always run in exactly one client context, so every USR02 row carries the same
value) and writes only the matching T000 row onto the already-existing `:Dataset` node (runs after
`00_dataset.cypher`). Basis for the company/client/time-slice grouping on the start page
([ROADMAP-V2.md](ROADMAP-V2.md#phase-3--vergleich-interview-ergebnisse-und-erweiterte-exporte)).
The remaining columns (`ADRNR`, `CC*` system-changeability indicators, `CHANGEUSER`/`CHANGEDATE`)
are documented within the extraction scope, but (so far) unused, with no recognizable benefit for
can-do.

## Validation (AE: Import Validation)

After the import, counters per node/edge type are checked against the source row counts of the
CSVs (script `load/99_validate.cypher`, end of phase 2). Spot checks against SAP (individual
users/roles) secure the business traceability (DoD).

## What Is (Still) NOT Modeled Here

- **Profile own values** (manually maintained profiles via `UST12`/`USR12`, profile contents
  `UST10S`): the role-based path via `AGR_1251` is covered; pure profile-auth values outside of
  roles can be added in a follow-up step if needed.
- **`DERIVED_FROM` / derived roles**: no confirmed source in the extracted tables (`PARENT_AGR` =
  collective role). Can be retrofitted once the derivation template is available.
- **Check indicator** (`USOBX_C.OKFLAG`): not extracted; `CHECKS` is based on the USOBT_C
  suggestion objects. Refining "active/suppressed" is possible later.
- **Fiori/OData layer** (S/4): deliberately deferred (see [Data Model](datamodel.md)).
- **Org-level pivot** (`AGR_1252`, `OrgValue` nodes): optional, only if needed.
