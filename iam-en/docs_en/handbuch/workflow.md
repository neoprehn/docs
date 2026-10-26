# Workflow Step by Step

A complete analysis from raw data to results — following the ribbon bar.

## 1 · Load Data (Import)

Ribbon **Data → Import**. Two ways:

- **Upload ZIP** *(recommended)* — a `.zip` with the SAP exports (`.txt` from SE16 **or**
  already-converted `.csv`). Optionally assign a **dataset name** (otherwise taken from the file name).
- **Existing folder** — a folder already located under `data/import/<dataset>/`.

The import automatically runs: **convert → ensure schema → load → verify**. Progress is shown as
a status line below the ribbon. Result: a **dataset** in the graph (users, roles, profiles,
authorizations, …).

:::{admonition} Which tables are needed?
:class: note
**Required (minimal set):** `USR02`, `AGR_AGRS`, `AGR_USERS`, `AGR_PROF`, `UST04`, `AGR_1251`,
`UST10S`, `UST12`. If any of these is missing, the import aborts with a clear message. **Recommended**
(the import runs without them, the pre-check warns with the consequences): `AGR_DEFINE`, `TSTCT`,
`USOBT_C`, `T000`. **Optional** (enrichment): among others `AGR_TEXTS`, `USR11`, `AGR_1252`,
`AGR_TCODES`, `AGR_1016B`. The complete list with purpose and columns is in the
[Extraction Guide](../extraktionsleitfaden.md#which-tables-to-download). Sensitive columns
(password hashes) are **discarded** during conversion and never reach the graph.
:::

## 2 · Analyze (New Run)

Ribbon **Analysis → New Run**. The form fills in the parameters internally — **no JSON**:

| Parameter | Meaning |
| --- | --- |
| **Ruleset** | which rule set applies (e.g., SAP R/3). |
| **System (dataset)** | which data snapshot is analyzed. |
| **Reference date** | the evaluation date — determines role validity and sleeping status. **No manual entry**: it is automatically derived at import time from the download date of the extracts and only displayed; a deliberate correction is possible only via "change…" (takes effect globally for the dataset). |
| **User-type profile** | which users count (see [Function Reference](funktionen.md)). |
| **Org profile** | org restriction (default: none). |
| **Sleeping (days)** | from when a user counts as "sleeping" (no logon for X days). |
| **Minimum criticality** | only rules at or above a level (e.g., "critical and above"). |
| **Run ID** | optional name for the run (otherwise automatic). |

The run performs two steps: **materialization** ("who can do what", takes a while depending on
size) and **analysis** (the SoD rules applied to the intermediate result). Both run as a background
job with a progress display. Below the progress bar, next to the counter (e.g., "query 58/103"),
is the **time per unit**: the average of the queries computed so far, how long the current one has
already been running, and a **rough** estimate of the remaining time. The remaining time is the
average multiplied by the remaining queries; queries vary in cost, so it fluctuates, especially at
the start, and only applies to the current step.

:::{tip}
If you have already materialized the same reference date before, you can check **"skip
materialization"** — then only the (fast) rule evaluation runs.
:::

## 3 · View Results

The **main area** shows the results throughout:

- **KPIs** — findings, affected rules, of which "sleeping".
- **Run list** — all runs with their finding count; a click loads the run (KPIs + findings). The
  title and an optional multi-line description can be changed at any time afterward via the pencil
  icon on each run card (a pure metadata update, it re-evaluates nothing) — useful with several
  named variants (see org profiles) whose name should still be changed in hindsight.
- **Findings table** — user · rule · criticality · sleeping (sorted by criticality).
- **Export CSV** (ribbon **Results → Export CSV**) — the findings of the active run as CSV
  (semicolon-separated, UTF-8 — opens directly in Excel).

## 4 · Save (Backup/Restore)

Ribbon **Save → Backup / Restore**:

- **Create backup** — packs the cleaned source data of the dataset into a ZIP.
- **then clear (Backup & Clear)** — back up and then remove the snapshot from the graph
  afterward (e.g., to make room for a different system).
- **Backup list** — for each backup, **↻ restore** (re-import) or **↓ download**
  (portable, e.g., for colleagues).

:::{admonition} What's in the backup?
:class: note
Only the **source data** (the cleaned `.csv` files) — not the findings. Findings are
*regenerable*: after restoring, simply run the analysis again (a run's parameters are
reproducible). You export results for reports separately as CSV (step 3).
:::

## 5 · Manage (Clean Up)

Ribbon **Manage → Clean up**:

- **Delete this dataset** — removes one snapshot including its runs/findings.
- **Delete all datasets** (danger zone) — removes **all** datasets and runs, not only the selected one; confirmation by typing a text.

In **both** cases, the **ruleset and schema are preserved** — afterward you can import and
analyze again immediately, without reloading the ruleset.

## 6 · Admin

Ribbon **Admin** shows the **loaded rulesets**. Fine-tuning SoD filters and importing new filter
sets (for additional systems) are planned and anchored there — see
[Function Reference](funktionen.md).

## Typical Flow

```
Import (ZIP)  →  New run (reference date = data snapshot, user type = dialog active)
              →  Review findings + export CSV
              →  Create backup  →  optionally clean dataset / load next system
```
