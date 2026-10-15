# Overview

**IAM** is a local web app for **graph-based analysis of SAP authorizations** with
**SoD conflict detection** (Segregation of Duties). It answers two questions:

- **Can-do** — *Who can do what?* (authorizations from roles and directly assigned profiles)
- **SoD** — *Who can combine incompatible things?* (e.g., create a vendor **and** release a payment)

The analysis runs **container-only** (Docker) and entirely **locally**. Everything is operated in
the browser at <http://localhost:8000/>.

:::{admonition} Data stays local
:class: important
**No client data** ever leaves the environment. SAP extracts, the database, and backups stay
local and are excluded from version control. Only the operating interface is "outside".
:::

## The Lifecycle of an Analysis

The interface is organized as a **ribbon bar** that follows exactly this flow:

```
 1 Data        →   2 Analysis     →   3 Results        →   4 Save           →   5 Manage     ·   6 Admin
 Import            New run            KPIs/Findings         Backup/Restore       Clear/Reset      Rulesets
 (ZIP/folder)      (parameters)       CSV export                                                  (planned)
```

1. **Data** — load the SAP exports of a system (via ZIP upload or an existing folder).
2. **Analysis** — start an SoD run with parameters (ruleset, reference date, user type …).
3. **Results** — view metrics and findings, export as CSV.
4. **Save** — back up the source data of a system, restore it, download it.
5. **Manage** — clear a single dataset or all data (the ruleset is preserved).
6. **Admin** — loaded rulesets; editor/filter-set import are in preparation.

## Starting

A detailed step-by-step guide (Docker **and** native Windows installation, with screenshots) is in
[Installation](installation.md); here is the short version for Docker:

```bash
docker compose up -d --build      # start Neo4j + backend
docker compose run --rm migrations  # create schema once (idempotent)
# Open browser: http://localhost:8000/
```

On first start, the images are pulled and the backend is built. After that, the app is reachable
on port **8000**; the Neo4j browser is on **7474**.

## Terms in Brief

| Term | Meaning |
| --- | --- |
| **Dataset** | a data/system snapshot (one SAP client at a point in time). Multiple snapshots can coexist. |
| **Ruleset** | the rule set (e.g., SAP R/3, CSI) with queries and SoD rules. Constant, applies across all datasets. |
| **Run** | an analysis with fixed parameters; carries a reference date, user-type/org selection, and the findings. |
| **Finding** | a detected SoD conflict: *this user* violates *this rule*. |

Continue to the [Workflow](workflow.md) (step by step) or to the
[Function Reference](funktionen.md) (what each command does).
