# Phase 5 — Runners & Orchestration

Two PowerShell runners bundle the manual `cypher-shell` calls into a few commands — one for the
**import**, one for the **analysis**. Container-only via the running `iam-neo4j`; the password
comes from `.env`, never in plain text in the script.

## `run/run_import.ps1` — SE16 Export → Graph

```powershell
.\run\run_import.ps1 -Dataset <name> [-Lang DE,DEU,D] [-SkipConvert]
```

Steps: **convert** (`Convert-Se16Export.ps1` including the minimal-set check + credential
denylist) → **migrate** (`docker compose run --rm migrations`) → all `load/*.cypher` in order
with `-P dataset` / `-P lang` → `99_validate`. Expects the export under
`data/import/<Dataset>/`. Each step is checked via `$LASTEXITCODE`.

## `run/run_evaluate.ps1` — Ruleset → Findings

```powershell
.\run\run_evaluate.ps1 -Ruleset sap_r3 -Dataset <name> -AsOf 2023-12-31 `
    [-UserTypeProfile dialog-service] [-OrgProfile standard] `
    [-SleepDays 180] [-MinCriticalityRank 5] [-SodRules @('BCX_0001')] `
    [-SkipRulesetLoad] [-SkipMaterialize]
```

Steps: **load the ruleset** (`cypher/ruleset/load_ruleset.cypher`) → **materialize**
(`cypher/sod/materialize_matches_*.cypher`) → **evaluate SoD**
(`cypher/sod/evaluate_sod_*.cypher`). Materializing/evaluating internally run as reset (one-time)
→ determine candidates → per unit (query or rule, `Invoke-Phase` in the script) — the same files
as the app (`backend/app.py:_run_phase()`), just without its progress display/checkpoint (the host
runner is a one-off interactive run; if it aborts, simply restart — all steps are idempotent).
Evidence (VIA_ROLE/VIA_PROFILE + intra/inter) is **not** computed here — for that, use the app's
`POST /runs/{id}/explain`. The **profiles** (`-UserTypeProfile`, `-OrgProfile`, sleeping, scope)
are **resolved** from `config/analysis_profiles.json` and passed as `-P` Cypher literals — the
user does **not** maintain any JSON by hand. At the end: a summary (findings / rules / sleeping).

:::{important} Reference date (`-AsOf`)
Must match the **data snapshot** (snapshot date, not "today") — it controls role validity **and**
the sleeping evaluation. See [Phase 3](phase-3.md).
:::

## Relationship to the App (Phase 9)

The runners are at the same time the **backend operations** of the later, portable app: there
they are invoked as API/jobs, with the frontend supplying the parameters (instead of the `-P`
flags).

## PowerShell Notes

- `$ErrorActionPreference = 'Continue'` + an explicit `$LASTEXITCODE` check (native tools such as
  `docker compose` write progress to stderr — under `'Stop'`, PS 5.1 would incorrectly treat this
  as fatal).
- The summary query is passed as an **argument** to `cypher-shell` (not via an stdin pipe —
  otherwise a BOM issue).

**DoD:** A fresh run on a second machine delivers identical results (given the same data).
