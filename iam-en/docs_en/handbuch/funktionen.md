# Function Reference

What each command in the ribbon bar does — and what the selection options mean.

## Start page

Entry point before the actual analysis, grouped **company → SAP client → dataset (time slice)**.
Each dataset gets exactly **one** card with its as-of date (or the dataset ID, if no as-of date is
on record); the most recent dataset per client is marked "Current". If a dataset has **multiple
runs** (e.g. re-evaluated with a different scope), the card shows a dropdown to pick the run
(default: latest) — the **findings**/**rules**/optional **sleeping** badges and the ruleset always
reflect whichever run is currently selected in the dropdown. Datasets without any run yet (freshly
imported, not evaluated) show a hint instead of the badges. **Open** jumps straight into the
analysis (`analysis.html`) for the selected run.

**Ribbon on the home page.** Above the tabs the functions are in four groups: **1 · Data** (Import, Guided import), **2 · Analysis**
(All together — from two datasets; Compare — as soon as two datasets are selected; Cross-system), **3 · Backup** (Backup / Restore) and
**4 · Manage** (Delete). **Backup / Restore** creates a backup of the selected dataset (optionally "clear afterwards") and lists existing
backups with "Restore" (re-import) and "Download"; run backups stay in the analysis. **Delete** removes the selected dataset including its
runs and cross-system analyses after confirmation; in the "Danger zone" "Delete all datasets…" removes everything — only after typing a
confirmation word.

**Two ways to start a new import:** "Import" jumps straight to the analysis page (import dialog); "✨ Guided import"
immediately starts the 7-step assistant there at step ① Import — which shows an
overview of existing datasets before the actual upload, to avoid exactly the mix-up described in
the user finding below.

**Compare.** A checkbox on each dataset card selects up to two datasets **within the same client
group** — one card means one checkbox, so comparing a dataset against itself is structurally
impossible. This only works within the **same ruleset** — datasets whose currently selected run has
a different ruleset get disabled as soon as one is selected (switching the dropdown re-evaluates
the lock). "Compare concepts" opens the comparison page (see below); the run with the **earlier
as-of date** is used as the **baseline**.

**Tabs "Single system" / "Cross-system".** At the top of the home page there are two tabs (as everywhere: the active tab is
larger). **Single system** is the previous view. **Cross-system** lists the saved [cross-system SoD analyses](cross-system)
(one card per analysis with systems, ruleset, date and number of findings, persons and rules; "Open", "Delete") and starts the
flow via "+ New cross-system analysis".

(cross-system)=
## Cross-System SoD Analysis

Checks **the same person in two systems** (datasets/clients): an SoD rule counts as violated if the **union** of the matches
from system A and system B satisfies all clauses of the rule — but **no single system** satisfies it alone. A conflict within one
system is a normal single-system finding and is in that system's runs; only findings that need **both** systems appear here. The
basis is the already materialized matches (one run per system, same ruleset). The flow (page `cross.html`, tabs as everywhere):

1. **Systems.** Choose system A and B (different) and a **run** each (default: latest). Besides the dataset ID the selection shows
   **company and client** from the system master data (`T000`), so the system can be recognized. Both runs must have the same ruleset. If
   a run was calculated with a restricted selection, its non-materialized queries are missing — matching findings cannot arise;
   the result points this out.
2. **SoD filters.** Which rules are checked: filter by name (with `*`) and criticality, "select all (filtered)" / "clear
   selection". Default: all rules.
3. **User comparison.** Beforehand it must be ensured that the person is recognized in both systems. The comparison shows users
   per system, **identical IDs**, those **linked by mapping** and the differences **only in A** / **only in B** (searchable). For
   differing spellings (case, special characters) the page makes **suggestions** that can be applied individually or all at once.
   The **mapping** (ID in A → ID in B) can be **exported as CSV** (existing mappings plus all open A users as a template),
   completed externally and **imported** (semicolon or comma CSV; "replace existing mapping" optional) or entered/removed
   individually. IDs that do not exist in the respective system are reported as invalid on import. The mapping applies per
   system pair and stays saved. A mapping overrides ID equality.
4. **Analysis.** Enter a name, "Start analysis". The result is stored **separately from the single-system runs** and can be opened
   again at any time from the home page (tab "Cross-system").

**Result.** Tiles (findings, persons, rules, linked persons, users without counterpart), the **Per rule** table (click filters)
and the **Individual findings** with user in A and B, kind of link (identical ID/mapping) and, per clause, which queries from which
system satisfy it — **with the causing roles and profiles**: for each query it shows which roles assigned to the user (valid on
the as-of date) or directly assigned profiles satisfy it **alone** (same semantics as "causing roles" in the single system; based on
the evidence phase of the runs). If no single actor satisfies the query, "combination of several roles" is shown. The table
**Causing roles and profiles** counts per system which roles/profiles take part in how many findings and rules; a click filters the
findings. If a system lacks evidence (run calculated without evidence), the page points this out. Filter by user ID, **export
XLSX/CSV/PDF**, "Delete analysis". Only technical user IDs appear.

**PDF report.** "Export PDF" creates a landscape report: header block (company, audit purpose, author — optional via "Header
fields"; plus system A/B with as-of date, ruleset, date), **summary**, **method and significance** (definition, linking of persons,
limitations such as non-materialized queries or missing role evidence), **findings per rule**, **causing roles and profiles** per
system (top 15) and the **individual findings** with clause evidence (the first 300; the XLSX/CSV export contains all). The Excel
export additionally contains the "Roles/profiles" columns per system and a "Causing roles" sheet. When a dataset is
deleted (Clean up), its cross-system analyses and mappings are removed as well.

## Concept comparison

A separate page (`compare.html`) to **compare** two runs with the same ruleset — deliberately
separate from the analysis: compare first, then (as a second step) audit specific items. The
**baseline** is on the left, the **compared run** on the right; "Swap direction" exchanges them (an
active category filter flips between *New* and *Gone* accordingly).

**SoD conflicts** (per user and rule) and **single-filter matches** (per user and query) are
compared. Every finding falls into exactly one category:

| Category | Meaning |
|---|---|
| **New** | only present in the compared run |
| **Gone** | only present in the baseline |
| **Changed** | present in both, but with a **different cause** — criticality, sleeping status, triggering roles or profiles differ (e.g. the same violation now arises through another role) |
| **Unchanged** | present in both with the same cause |

Single-filter matches carry no further attributes and are therefore never *Changed*.

**Exception comparison.** A fifth tile, **"Exception changed"**, shows for how many findings the
**exception decision** (category and justification) differs between the two states. It only
considers findings that occur in **both** runs — regardless of whether the finding itself is
*Changed* or *Unchanged* (so you can see, e.g., an unchanged finding that was assessed differently
the following year). Decisions belong to the dataset, not to the run. A missing decision counts as
the default category without justification, so "not yet auto-categorized" does not produce a false
difference. The tile acts as an additional filter (combinable with category, type and user), the
detail list shows "Exception: category A → category B" (with a note if the justification changed),
the "Per rule / filter" table has an *Exception* column, and both exports contain the category and
justification of both states. Exception values are not cached; they are read fresh on every call.

**Follow-up — carrying decisions over.** The **"Carry over decisions…"** button copies the exception
decisions (category + justification) of the **baseline** into the dataset of the **compared state**,
e.g. from last year into the new dataset, so that only what is new or different needs to be assessed
again. A **preview** with counts comes first; nothing is written until you confirm:

- Only findings present in **both** runs are carried over, and only **explicit** decisions of the
  baseline (not the default category without justification).
- By default only **unchanged** findings; findings with a **different basis** (category *Changed*,
  the old decision may no longer fit) only if explicitly ticked.
- Only **open** spots are filled (decision missing, or still the default category without
  justification). An **existing, differing** decision of the compared state stays untouched unless
  you tick "Also replace existing, differing decisions". The counts show "open" and "with a
  differing decision" per group.
- Baseline and compared state must be in **different** datasets. Carried-over decisions record their
  origin (source dataset) and are never overwritten by the automatic categorization. The direction
  follows "Swap direction".

The four tiles at the top double as filters (a click sets/clears the category). Below, the
**All / SoD rules / Single filters** switch selects the type and the field takes a **user ID**
(Enter). The **By rule / filter** table shows, per entry, the count in baseline and compared run
plus the four categories; clicking a row narrows the detail list below to that rule or filter. The
detail list loads page by page ("Load more"). The counters and the "By rule / filter" table always
cover the **whole** comparison — only the detail list follows the filters.

**Export.** "Export XLSX" delivers two sheets (*By rule/filter* and *Findings*), "Export CSV" only
the findings — in both cases **all** rows matching the current filter (not just the loaded page).
Only technical user IDs appear, no real names, so the anonymization toggle is not needed. A
comparison result is cached briefly so that filter and page changes respond quickly; the first
calculation can take a few seconds on large data sets.

## Banner

At the top left, the wordmark; at the top right, the **light/dark toggle** (remembers the choice
in the browser), the **anonymization toggle** (see below), the chip showing the **actively
applied ruleset** of the currently displayed run, and two further **status chips**: the database
connection and the context **"N datasets · M runs"** (refreshes after every action).

**Dataset filter.** The selection in the banner decides **which dataset** the whole UI shows: runs, backups, selection
lists in all dialogs, import log, consistency checks and the security view then refer only to this dataset and its
evaluations. Opening a dataset ("Open") on the start page lands in the evaluation with this filter. Switching opens
the **newest run** of the selected dataset. The entry **"All datasets"** removes the filter; on the start page the
button **"Evaluate all datasets together"** leads there (shown from two datasets). The filter is remembered in the
browser; when opened directly without parameters the last used value applies, otherwise the newest dataset. A newly
imported dataset immediately becomes the active filter.

**Language of error messages and reports.** The interface follows the language switch in the page header
(German/English). The same language applies to what the server returns: **error messages** (e.g. "Run … not found") and
the **labels of the reports** — consistency report, import evidence, import log, one-pager, exception workbook, result
overviews, comparison export and the cross-system SoD check (PDF, Excel, CSV). The server learns the language from the
parameter `?lang=de|en`, otherwise from the header `X-Lang` or the cookie `iam_lang`, which the interface sets when the
language is switched (so downloads via a link use the right language as well); without any of them the default language
from the master data applies. Content that comes from the catalogs and data is deliberately **not** translated: texts of
the consistency checks, query/rule/risk descriptions, categories and justifications, table descriptions and technical
identifiers (CSV column headers of the result exports stay English and machine-readable). The exception workbook is read
back by column position and accepts the sheet names of both languages.

**Anonymization.** A single, global toggle (chip "names visible"/"names anonymized") replaces
real user names (from USR02/ADRP) everywhere with a stable pseudonym ("Anonymous-XXXXXX", always
the same for a given user ID) — the technical user ID itself remains unchanged, and
filters/drill-downs/exports continue to work unchanged. It takes effect **server-side and
globally** (unlike language/theme, which are only remembered in the browser): once toggled, all
views **and** all exports (CSV/Excel, including the detailed user breakdown) show pseudonyms
until the next toggle — intended for screenshots/demos/handoffs where the structure of the
analysis should remain visible, but not real names. This affects every place where a user name is
displayed: the individual filter results list (column "Name"), the full tree view, the user detail
page, the role detail page (assigned users as well as the role's creator/last changer), and the
corresponding exports. The findings table (SoD results) only ever shows the user ID, never a
name — there is nothing to anonymize there.

## 1 · Data

| Command | Effect |
| --- | --- |
| **Import** | Opens the import dialog: **upload ZIP** (`.txt`/`.csv` inside the ZIP) or **existing folder**. Starts the import job (convert → schema → load → verify). |

Options in the dialog: **languages** (for language-dependent text tables, default `DE,DEU,D`),
**skip schema** (if constraints/indexes already exist), **skip conversion** (if `.csv` files are
already present).

**Dataset name for ZIP/folder upload is now required** and must be **unique** — it is no longer
silently derived from the file name (live finding 2026-10-11: a field left empty landed unnoticed
in an existing dataset instead of a new one). If the entered name matches an existing dataset and
"clear first" is unchecked, the app explicitly asks for confirmation before sending whether the
new data should really be merged into that existing dataset.

**"or existing folder" never creates a new dataset** — the dropdown only lists folders already
present under `data/import/`, meant for resuming an interrupted import or reloading after manually
adding files (live finding 2026-10-12: "import folder" clicked instead of "import ZIP", unintentionally
reloading the one existing folder because no other option was listed). Without an active resume
state and without "clear first", the app asks for confirmation here too before sending. For a
**new** dataset, always use the upload section above.

**Pre-check of the extract.** Before anything is loaded or deleted, the import checks the extract automatically (step
"Pre-check extract"): required tables and columns, separator, empty tables, invalid dates and dates in a format that was
not converted, unknown user types, encoding errors. **Errors stop the import** — the existing graph stays unchanged
(also with "clear first"); **warnings and notes** appear in the import result. The date format of the user master (e.g.
`MM/DD/YYYY`) is rewritten to `DD.MM.YYYY` automatically during conversion. The **"Check only"** button ("Existing
folder" tab) converts and checks without importing anything — useful for a new extract before the actual import. Large
tables are checked by sample (start of the file).

**Source format (SE16 or KAAP extractor package).** In the ZIP/folder upload and in the "Existing folder" tab, the field
**"Source format"** selects how the data was delivered. **"detect automatically"** is the default and is usually enough:

- **SE16 list export** (`.txt`, `|`-separated, fixed width) — the previous way.
- **KAAP extractor package**: a ZIP with one folder per extraction run, each containing one ZIP per table
  `<prefix>_<TABLE>_<NNNN>.ZIP` (large tables in several parts) holding a UTF-8 text file, delimiter `#|#`, first line =
  field names, dates as `YYYYMMDD`. The import unpacks the package, takes only the tables it knows (log files,
  images and unrelated large tables are ignored), merges parts and rewrites dates to `DD.MM.YYYY`. If the package
  contains several runs, the run with the most columns wins per table. Credential columns are dropped as usual.
- **Missing user master:** with an KAAP extractor package `USR02` may be missing — the import still runs, but the pre-check
  warns explicitly: user type, lock status, validity and last logon are unknown, users only arise from the
  role/profile assignments, and checks by user type, lock or sleeping return no hits. The import log keeps showing
  `USR02` as a missing required table.

(import-log)=
### Import Log (Completeness Evidence)

The **Import log** command (menu "Admin", group "7 · Admin" — next to the error log) shows **which data was imported when and whether everything was taken
over into the graph completely** — as evidence for the audit documentation. It is created automatically with every
import; older imports can be evidenced afterwards (see below). For each dataset and import, the page shows:

- **Tabs:** the page is organized by topic — *Overview* (overall result, tiles, master data), *Source files*
  (evidence per file with explanation of the notes), *Key figures* (breakdowns) and *Not used*.
- **Overall result** (*OK*, *OK with notes* or *Deviation*) with **status tiles** per status (OK, note, deviation, …).
- **Notes are numbered:** a *note* means "not an error, but the result differs from the plain source comparison for a
  **known, explainable reason**" (e.g. roles that only occur in assignments). Each row carries a number **[1]–[9]**; the
  matching explanation is shown **below the table** and in **all exports** (Excel: sheet "Erlaeuterungen", CSV: columns
  *hintNumber*/*hintTitle* plus legend, PDF: page "Erläuterung der Hinweise") — so a printout is readable without
  follow-up questions.
- **Key-figure tiles** for **users, roles, profiles, authorizations and transactions** — the numbers are **counted
  in the graph** after the import and, where a matching source table exists, **held against its rows** (e.g. users
  against `USR02`). Below, the breakdown (users by type and status, roles by single/composite/derived role, profiles,
  relationships).
- **Master data of the import:** import time and duration, source (ZIP name or folder), languages, **as-of date**,
  the **system master data from `T000`** (company, client, city, currency, logical system) and the program version.
- **Evidence per source file:** file, **size and SHA-256 checksum**, source rows, deliberately skipped rows, the
  **expected value from the source** and the graph result, plus status and explanation. **All** tables of the
  extract are covered: those in use with reconciliation, those currently not evaluated (without a loader) separately
  as "present in the extract but not evaluated" — also with checksum. The table can be filtered with the buttons **All /
  OK + note / OK / Note / Deviation** (each with a count) and **sorted ascending and descending** via the column headers
  (table, required/optional, source rows, skipped, expected, graph, status; not name, MB, SHA-256 and note). The
  "Deviation" filter turns red as soon as there is one. A **note** that merely explains an expected technical
  difference (numbers 1–4) additionally carries a green **OK** in the status column — the data is complete; notes
  with a limitation (5–10) get no OK. The same applies to the tables in the **Key figures** tab: colored column
  headers, fixed column widths and the additional OK badge in the status column; the table in the **Not used** tab has the
  same colored header design.
- **Red only for a real import problem.** A **deviation** means: the graph is missing something compared with the
  source. Everything else is at most a **note**, including a required table that is allowed to be missing by import
  option (e.g. the user master `USR02` with the KAAP extractor package, note [10]). The overall status then reads "OK
  with notes".
- **Import history:** the "Import" selection lets you view any earlier import of the same dataset.

**How the reconciliation works.** The mapping *source table → usage* lives in **one** place
(`config/import_sources.json`, the source catalog); a test ensures that every table read by the load scripts is listed
in it. Where the load logic deliberately skips or merges rows, the **expected value is recomputed directly from the
source file** — by the same rules as the loader (distinct keys without the skipped rows). Examples: `AGR_USERS` has
more rows than the graph has assignments, because several rows of the same pair (different validity periods) become
**one** edge — the evidence shows that the number of distinct pairs **exactly** equals the edge count; `TSTCT` is a
language table with several rows per transaction. If the graph has **more** nodes than the source table (e.g. roles
that only occur in assignments but are not defined in `AGR_DEFINE`), that is a **note** with the difference; **fewer**
nodes than expected is a **deviation**.

**Additional checks.** *Recount graph now* counts the graph once more **now** and flags every key figure that deviates
since the import (the graph was changed after the import). If a source file was **changed after the import** (its
modification time is later than the import), it is flagged; its evidence is then only of limited reliability.

**Evidencing older imports.** *Reconstruct source file evidence* determines source rows, dropped columns, size,
modification time, checksum and expected values from the **current content of the import folder** and adds them to
the latest import. The graph counts from the time of the import stay unchanged (they were measured back then); the
log notes the time of the reconstruction. This takes a few minutes for large extracts (all files are read). It
requires the import folder `data/import/<dataset>` to still exist.

**Export.** *Export Excel* (default) creates a workbook with the sheets **Protokoll** (master data and overall
result), **Kennzahlen**, **Quelldateien**, **Nicht genutzt** and **Importverlauf**; *Export PDF* a landscape document
with master data, key-figure tiles and source files including checksum; *Export CSV* the file evidence for further
processing. In the collapsible "Header fields for the export" area, company, audit purpose and preparer can be
entered. The labels in the export are in German.

## 2 · Analysis

| Command | Effect |
| --- | --- |
| **New run** | Opens the parameter form and starts materialization + SoD analysis. |

### User-Type Profile

Which users are included in the analysis:

| Profile | Meaning |
| --- | --- |
| **all** | all user types, including locked ones. |
| **dialog-service** | dialog + service (A/S), including locked ones. |
| **dialog-active** | dialog + service **and not locked** — the audit-relevant view. |
| **dialog-only** | dialog only (A). |

> User type and "locked" are two separate axes: A/S says nothing about active/locked status.
> `dialog-active` combines both.

### Org Profile

Whether the analysis is restricted to organizational levels (e.g., company code):

| Mode | Meaning |
| --- | --- |
| **Default** | no org restriction — *"can the user perform the function at all?"* |
| **Cross-org** | only counts if the authorization carries the full range (`*`). |
| **Filtered** | one condition per org field (AND/OR/range) — preconfigured via profiles. |

> Org filtering applies across **all** org levels (company code `BUKRS`, plant `WERKS`, purchasing
> org `EKORG`, sales org `VKORG`, …, from USORG) **and combinations** (e.g., company code *and*
> purchasing org). What is evaluated are the users' **actual authorization values** (from the
> role/profile auths), not SU24 suggestions. The chosen mode/filter is logged on the run.

### Individual Filter Scope

Which queries of the ruleset materialization even considers (`(:User)-[:MATCHES]->(:Query)` — the
basis for both the SoD analysis and the individual filter view/overview):

| Mode | Meaning |
| --- | --- |
| **All individual filters + SoD** (default) | materializes **every** query of the ruleset, including those that are not used as a clause in any SoD rule. |
| **Only SoD-relevant individual filters** | restricts materialization to exactly the queries that the SoD rules of this ruleset actually need — faster, but the individual filter results/overview then only show this (ruleset-dependent) subset. |

> "All" computes noticeably more queries than "only SoD-relevant" and therefore takes
> correspondingly longer — for a catalog with significantly more individual filters than SoD
> clauses, by a multiple. The extra effort only occurs on the **first** run for a given reference
> date: "skip materialization" (see below) reuses the already-computed intermediate result on
> repeat runs. Which queries count as "SoD-relevant" depends on the respective ruleset (e.g., a
> different count for a different filter set) and is stored on the run (`queryScope`) — a run's
> individual filter selection/overview always shows exactly the queries that were actually
> materialized in **this** run.

### Preset (instead of "Individual Filter Scope"/User-Type Profile/Sleeping)

Besides the coarse "all/only SoD-relevant" scope above, the next run can also be restricted to a
**deliberately chosen subset** of individual filters and/or SoD rules — **and**, at the same time,
determine the **user-type profile** and **sleeping (days)** — via the **"saved scope"** field in
the form. Two sources feed this preset, with a fixed priority:

1. **A saved scope** (selected in the dropdown) — created via the admin page **"Scope"** (see
   below), reusable across any number of runs/datasets of the same ruleset.
2. **An ad hoc selection from the guided analysis** (wizard, step "Scoping", stage "SoD rules") —
   applies only to the current session and disappears when the wizard is restarted.
3. If both are empty, "individual filter scope", user-type profile, and sleeping remain their own,
   freely editable fields as usual (today's default behavior).

If one of the two sources is active, a summary line replaces the "individual filter scope" toggle
**and** hides the dedicated fields for user-type profile/sleeping — the preset determines all
three. Two kinds of analysis result automatically from the individual filter/SoD selection:
**individual filters only** (no SoD rule included) materializes exclusively these individual
filters and skips the SoD analysis entirely ("can-do"); if **SoD rules are also** selected, the
run materializes only their clause queries (instead of all SoD-relevant queries of the ruleset)
and evaluates only these rules.

**Preselecting a scope in the wizard:** In the wizard step "Scoping", the dropdown **"Load saved
scope"** loads a scope profile as the preselection — individual filters, SoD rules, user-type
profile, and sleeping days are then already ticked and remain adjustable.

**Two paths through the wizard:**

1. **Step by step** — with **Next/Back** (from step ④ on, in a bar below the stepper) through
   consistency, SoD, and root cause. SoD/root cause need an open run; if there is none, the bar
   offers "Start run with scoping…".
2. **Select everything, then compute in one go** — in Scoping, "Run everything / schedule…" opens
   "New run" with the selection as preset. With **"Start at a scheduled time"** the run (including
   several org variants) is queued on the server and started at the chosen time, e.g. overnight —
   the browser does not need to stay open. Queued runs are listed at the top of the dialog and can
   be cancelled. Optionally the server also stores the **consistency report** (CSV, or PDF with
   header block) after the run; it is listed under "Generated reports" in the same dialog for
   download (stored locally under `backups/reports/`).

   **Import as the first phase.** If the data is already in `data/import/<dataset>`, the **import (step ①)** can be
   scheduled as well: tick "Run the import (step ①) first, at the scheduled time" in the dialog (choose the source
   format, optionally "Clear the dataset first") — or pick "⏱ Schedule import → scoping" right in **step ①** of the
   assistant: it then goes straight to scoping (the dataset does not have to be loaded yet), and "Run everything /
   schedule…" plans import, evaluation and optionally the report as **one chain**. At the scheduled time the phases run
   one after the other; if one fails, the evaluation does not start.

   **Continue from the phase.** A phase that has completed is not repeated: "Continue" resumes at the first phase that is
   not complete, using that phase's own checkpoint (import from the last load step, evaluation from the saved run state).
   If the import is done and the evaluation fails, only the evaluation runs again.

   **Schedule log (image).** The "Schedule log (image)…" button in the dialog shows each chain's phases as a graphic with
   status (open/running/done/error/cancelled), start, end, duration, attempts and the error message. "Save as image (PNG)"
   stores it as a file; "Continue" — or "Start now" for a chain that is still waiting — resumes the chain. The log is kept in
   `data/logs/chains/` and **survives a restart** of the backend: a chain that is no longer running at its time shows as
   "interrupted (restart)" and can be continued. The waiting plan itself still lives only in memory — after a restart it
   does not start by itself but only via "Start now".

### Further Parameters

- **Reference date** — evaluation date (role validity + sleeping). **No longer an input field**,
  but a property of the selected dataset (= download date of the SAP extracts): it is
  automatically determined from the extracts' file timestamps on first import and only displayed;
  a deliberate correction runs via "change…" next to the display and takes effect **globally** on
  all future runs/checks of this dataset, not just the next one.
- **Sleeping (days)** — threshold "no logon for X days" (default 180), freely selectable.
- **Minimum criticality** — `all` · `medium` and above · `high` and above · `critical` and above ·
  `very-critical` only.
- **Skip materialization/ruleset loading** — accelerator for repeat runs.

## 3 · Results

Groups with several commands (here and under "Admin") expand as a **menu** — clicking the group
opens a list of commands, clicking elsewhere or on a command closes it again (behaves like a
familiar application menu rather than buttons placed side by side).

| Command | Effect |
| --- | --- |
| **Refresh** | reloads runs, datasets, backups. |
| **Evidence** | recomputes VIA_ROLE/VIA_PROFILE + intra/inter for the active run — since the evidence performance improvement, this is a standard part of every new run; this command is now only needed for older runs without evidence, or after "skip evidence" was used in the run form. |
| **Export CSV/PDF/…** | Exports **exactly the currently visible view** — the label and format switch automatically: findings, matches, and user list (each a genuine table) are exported as **CSV**, with the same active filters/sorting as on screen; without active filters, the complete run. Role detail and root cause (not a flat table) are exported as **PDF** via the browser's print dialog ("save as PDF"). The findings export also includes the rule's **label** (not just the ID). In the **individual authorizations/SoD overview**, the command instead opens a dialog with three formats: **CSV**, **Excel** (native `.xlsx`, subtly colored table headers), and **detailed Excel** — the latter unfolds, below each row (query or SoD rule), the affected users (ID/name/type/status) via Excel's outline/grouping feature (collapsed, expandable by clicking the "+" on the left edge), and for each user in turn a second, nested level with the role(s)/profile(s) carrying the match — for individual filters, additionally with the covered authorization object or the transaction-code check. For very large numbers of hits (>200 users per query), this role/object breakdown is skipped for performance reasons (a notice line instead of data; the user list itself remains complete) — for these cases, the interactive root cause for each individual user remains the source. |
| **Individual authorizations** | Overview: **every** query with at least one hit in this run (within the individual filter scope chosen for the run, see "New run"), with criticality and the number of matching users. The tile at the top shows the **distinct** total number of affected users across all rows (the individual rows are not summed, since a user usually matches several queries). Clicking a row jumps to the normal individual filter view, filtered to exactly this query. |
| **SoD rules** | The same overview for SoD rules (number of violating users instead of matching ones, tile accordingly). Clicking jumps to the normal findings view, filtered to this rule. |

In the main area: **KPI tiles** (see below), **run list** (click = load run; each card shows
label, reference date, and creation date/time), and the **results table** (findings or matches,
depending on result type — see below).

### Filter

On the left in the sidebar: **user type** (checkbox dropdown — A/B/S/C/L =
dialog/system/service/communication/reference), **user**, **individual authorization**, and
**SoD** — the latter two show **ID + label** (short label if maintained, otherwise the long
label); the ID comes **first** so that it is not cut off by the fixed dropdown width when labels
are long. The selection is applied via "filter" or immediately when clicking a user cell in the
findings table. If a **user** is selected, the **individual authorization** and **SoD** dropdowns
automatically narrow to what was actually found for them (cascading filter) instead of always
showing the full catalog/all of the run's rules. **Individual authorization**/**SoD** also show,
on their own, only what was actually in scope for **this run**: if the run was run with a catalog
selection/preset (see "preset" above), only the individual filters or SoD rules chosen there are
available for selection — not the entire ruleset catalog.

Above the results table, in its own row: **criticality** (very-critical…low) always, **result
type** (`all` / `individual filter` / `SoD`) **only outside the entry table** (see below), and —
only when the result type is "all" — **sleeping** (`all` / `only sleeping` / `not sleeping` /
`unknown`) as well as **locked** (`all` / `locked` / `not locked`) as colored clickable buttons
(pills), taking effect immediately. The **criticality** applies to the criticality of the **query** for result type "individual filter" (and also narrows the query dropdown), and to that of the **rule** for "SoD". For "only sleeping"/"not sleeping", a **days quick-select**
additionally appears (`run default` / `90` / `180` / `360`) — if it deviates from the `sleepDays`
window set on the run, the filter calculates live against the logon date instead of against the
value materialized on the run (only works if TRDAT is present in the extract). For "locked", the
**lock reason** additionally appears (`all` / `failed logons` / `admin (local)` / `admin
(global)`, from the UFLAG bit field) — this only applies to runs that did not already exclude
locked users during materialization (user-type profile without "not locked", see above), otherwise
their findings are missing from the start. Right-aligned in the same row: the **table/bar/tree
toggle** — independent of the sidebar filters, following only `result type` (SoD/individual
filter):

- **Bar**: one row per SoD rule or individual filter, bar length = number of affected users, color
  = criticality. Clicking jumps to the filtered table view.
- **Tree**: the same rows, but expandable/collapsible (accordion, with only one sibling branch
  open per level at a time) — clicking expands the affected users, clicking a user expands the
  role(s) carrying the authorization or the directly assigned profile. Clicking a user or role
  chip opens an overlay with its master data. There is additionally a **full view** (Cytoscape
  graph for exactly the expanded path, with a color legend and zoom slider/full screen, like the
  root cause page).
- **Roles** (only with exactly one selected single authorization): shows the **causing roles** — roles and composite
  roles that are assigned to an affected user on the run's as-of date and fulfil the authorization **on their own**.
  Each role gets a bar with the number of affected users, below it a table with "directly assigned", "via composite
  role" and the most frequent composite roles; clicking a role opens its master data. Users who only receive the
  authorization from several roles or through a directly assigned profile are **not covered** and are reported
  separately ("X of Y users …").

"Individual filter" shows the **matches table** ("who matches which query") even **without**
first selecting a specific individual authorization in the sidebar — in that case for all queries,
otherwise only for the one selected.

**Entry table.** If **no** filter is active (freshly loaded run or "reset"), the last column shows
**sleeping** instead of **root cause** — with (potentially hundreds of) unfiltered findings,
jumping to root cause per row is not yet worthwhile. As soon as any filter applies (user, rule,
criticality, user type), the last column switches to **root cause**. "SoD"/"all" show the
**findings table**. An active filter additionally appears as a chip with "reset".

The **result-type pill row** ("all"/"individual filter"/"SoD") is always visible, even in the
entry table — clicking "individual filter" then shows **all** individual filter hits of the run
across all queries (matches table), capped at the first 500 (analogous to the "TOP 500" for
findings — for several thousand hits, an uncapped query would otherwise be noticeably slow). For a
complete, uncapped overview without a root-cause jump per row, use the **bar** or **tree** view
(uses `/queries/summary` or `/sodrules/summary`, independent of the table view's 500 limit).

### User-centric Selection: KPI Tiles, Causing Roles

As soon as a **user** is filtered, a **master data tile** (user ID · name · type · status, via
`GET /users/{id}`) replaces the KPI tile in the slot where otherwise nothing third would stand. If
a **rule** is additionally selected (e.g., via the root-cause access point, see below), the user
filter is retained and a chip **"rule: …"** appears above the KPI tiles (additive drill-down:
first user, then user **and** rule — not exclusive).

If **user and rule are set together** (exactly one finding), a dedicated field **"causing
roles/profiles"** appears below the KPI tiles — the roles/profiles that, according to the evidence
(`VIA_ROLE`/`VIA_PROFILE`), trigger this conflict, plus a dedicated **root cause** button (see
below). Without computed evidence (ribbon "evidence" not run), a notice appears there instead of
the list.

### Root Cause

Both the **findings table** (SoD) and the **matches table** ("who matches", individual filter)
have a **"root cause"** button per row. It switches (no dialog/overlay, unlike the
findings/consistency-check view) to a **dedicated page** with "← back" — at the top, the **query
or SoD rule** in question along with its short/long label (from the already-loaded query/SoD
cache, no new request), below it the general explanatory text, grouped **per authorization
object** of the query (heading with the parenthetical "(authorization object check)", analogous
to "S_TCODE (transaction code check)") — for an SoD rule, additionally **per clause** (for the
query of that clause actually matched by the user; the block heading additionally shows its
label): for each object, first the **requirement** — `FIELD (AND/OR): value1, value2, …` —
followed by the **role(s)/profile(s)** that satisfy exactly this object with which specific
authorization; the value that actually applies in each case (or `*`/a covering range) is
highlighted in green within it — making it visible at a glance **why** a row matches, without
manually comparing requirement and values. Unlike the evidence (which only shows "which role"),
this makes visible when **different objects/clauses are covered by different roles** — the actual
root cause, not just the carrier of the conflict.

A toggle **"without technical" / "all (incl. technically generated)" / "only generated roles"**
above the results list controls which actors are shown. **"without technical"** (default) hides
SAP-generated profiles: a directly assigned profile counts as "technical" if any role in the data
generates this profile (role `HAS_PROFILE`, regardless of the user in question) **or** the name
starts with `T-` (a name-based fallback for "orphaned" generated profiles whose generating role no
longer exists in the extract — the authorization still remains active according to `UST04`, so it
is deliberately **not** hidden but marked with a notice). **"all"** additionally shows these
technical profiles. **"only generated roles"** shows the **runtime view**: only roles that are
actually active via their **generated profile** (what actually feeds into `UST04`) — pure design
rows without profile coverage (D4 divergence) are dropped —, **plus** directly assigned profiles
(e.g., `SAP_ALL`), so that no critical direct access falls out of the picture. A counter or notice
shows how many rows are currently hidden.

The graph views also have a **full-screen** button and a **zoom slider** on the right edge for
quickly zooming in/out.

**View: table · path graph · radial.** Above the results list, a second toggle switches between
the **table** (default, with all annotations below) and two **graph representations of the same
data**. The **path graph** shows the path **user → rule → clause → query → authorization object →
role/profile** as a tree from **left to right** (so wide labels sit side by side in one level; the
same applies to the tree full view and the security paths); the **radial** view places the user at
the center and
arranges the causes outward in rings. Each actor (role/profile) is shown **only once, independent
of the profile filter**, even if it carries several objects/transaction-code checks of a query —
this turns the graph into a DAG (several object nodes point to the same actor node), instead of
repeating a role per object and thereby suggesting more parties responsible than actually exist.
Authorization objects and the transaction-code check appear as their own, color-distinguished
boxes, still **with** the object/transaction-code label and the specific requirement values in the
label (e.g., `TCD=SU01,SU10,…`) — colors distinguish rule/clause/query/transaction-code
check/authorization object/role/profile (role and transaction-code check deliberately clearly
different, magenta vs. blue); **technical/generated** profiles are dashed and paler, **orphaned**
ones outlined in red; **AND/OR** are shown on the edges (does the user need *all* or *one* of the
prerequisites). The "without technical" filter also applies here. All object→role/profile edges
("CONTAINS") look **uniform** — whether a role satisfies the object via its own definition or via
its generated profile (or a contained collective role) is shown **only** in the hover tooltip of
the respective edge, no longer as a separate edge style: an earlier red dashed extra edge for this
looked, with roles that matched multiple times (deduplicated), like a confusing tangle of edges,
without the difference being self-explanatory (user finding). Hovering shows details on both nodes
and edges (technical/own definition/via profile/via role/specific field values). The graph view
complements the table for the overview — for gapless value-by-value comparison (green-highlighted
matches, D4 divergence link), the table remains the detail view.

**Clicking a node** leads — depending on its type — directly to the matching view instead of
merely highlighting the path: **user** → results list filtered to this user, **query** → "who
matches" results list for this query, **role** → role detail page; for all other node types (rule,
clause, object/transaction-code box) it remains at path highlighting (the rest grayed out).
**Right-clicking** a node with more than one meaningful action instead opens a context menu — for
a query and an SoD rule, for example, both "show result" and "details (master data)"; the latter
opens Query Management in a new tab with the ruleset and entry already selected. For the **user**
node, the context menu offers, in addition to "show user analysis" (filtered results list), the
entry **"user detail"** — opens the user detail page (see below). "Fit" centers the view and is
also clickable while full screen is active (the fit/full-screen buttons are placed inside the
graph canvas for this reason, not in the toolbar above it — otherwise they would be unreachable in
full screen).

**User detail page.** A standalone view (not an overlay) with master record (name, type, user
group, status/lock reason, last login, sleeping, validity period, password history/initial-
password notice), below it a **criticality score**: the highest occurring level as a badge, plus
the full distribution below it (e.g., "N× very critical · M× critical · …", counted across
individual filter hits **and** SoD findings together — deliberately no single weighted value, so
the derivation always remains traceable). Two tabs below list this user's **individual
authorization** and **SoD** hits, with a criticality badge and a "root cause" button each, which
jumps directly to the matching query or rule root cause. "Back" returns to the root-cause graph
(cleanly closing an active full-screen view first, if open).

**Legend + custom colors.** Below the graph, a legend shows all occurring node types together with
their border modifiers (technical/orphaned). Clicking a color dot opens the native system color
picker; the chosen color takes effect immediately on all open graphs (path/radial/full tree view)
and is stored locally in the browser (no server config, purely a personal setting per
device/browser).

**Source marking.** The same actor can reach a match via **several sources** — this is indicated
per row as a short annotation. Pairs with identical values from the own definition and the
generated profile are merged into **one** row (in that case the profile is only the compiled form
of the definition); only when the values **differ** do both rows remain — that is the meaningful
divergence case (→ D4). Several rows for the same role with **different** values are therefore not
a display error, but genuinely different authorization instances, or a design-≠-generated
divergence:

| Annotation | Meaning |
| --- | --- |
| **(own definition)** | The role carries the authorization directly itself (`AGR_1251` → role `HAS_AUTH`) — appears only if there is additionally a second source for the same actor. |
| **(own definition = generated profile X)** | The own definition **and** the generated profile X carry **exactly the same** values for this object — the profile here is only the compiled form of the definition. Both are then merged into **one** row (instead of two rows with identical values). |
| **(via generated profile X)** | Comes via the profile X generated by the role (role `HAS_PROFILE` → profile `HAS_AUTH`) — what is actually written to `UST04` during the user comparison and checked at runtime. Appears on its own only if it **differs** from the own definition (otherwise merged, see above). |
| **(via contained role X)** | The displayed role is a **collective role** that bundles role X as a single role (`CONTAINS`); X itself carries the authorization. |

If "own definition" and "generated profile" **diverge** for the **same** authorization object, a
red link additionally appears that jumps directly to the detail view of consistency check **D4**
("outdated/non-generated profiles") — in two variants: **"deviates from the generated profile ·
D4"** (a profile exists for this object, but has different values per field) and **"no matching
generated profile found · D4"** (the generated profile has **no** hit at all for this object — the
more serious case, with no value comparison). Background: in SAP, a role only becomes effective at
runtime after the profile has been generated — if the maintained definition deviates from the
generated profile, or the profile hit is missing entirely, the "own definition" row shows
something that may **no longer** be active. This assumption (role definition ≈ generated profile)
is not a root-cause peculiarity, but applies to the app's entire can-do/SoD analysis
(`materialize_matches_*.cypher`); D4 is the consistency check designated for this. In the **graph
views**, the same check appears (without a clickable link, since the hover tooltip is not
interactive) as an additional red line in the edge tooltip of the affected role.

**Follow-up profiles.** For large roles, PFCG creates several generated profiles (base name plus
running number, e.g., `T-F0100831`, `T-F01008319`), but in the data only the first one is attached
to the role. Profiles with a role's base name plus digits (at most 12 characters) therefore count
as generated by that role: they are shown as "via generated profile" of the role, do not appear as
"orphaned", and do not trigger the D4 link.

**Grouping + value filter.** A role with **several authorization instances** for the same object
(permitted in SAP; the instances must **not** be aggregated, see AE-03) appears **once** as a
header, with its matching instances indented below it — instead of many rows with the same role
name. A second toggle **"all" / "matches only"** (default **"matches only"**) shows either all
field values (matches highlighted green) or **only** the values matching the requirement (without
highlighting) — helpful for roles with very many transaction codes/values. This applies equally in
the table and in the **graph views** (node label + hover tooltip show the same reduction); if the
reduction yields no hit for a field (e.g., because the hit only comes about via a different
field), the display falls back to the full values instead of staying empty.

**Role clickable → detail page.** Role names (table) or role nodes (graph) open a **role detail
page** on click (the left filter/runs sidebar remains visible). At the top, always visible, are
the **master data** (description, subtype, parent role, generated profile + generation status
including the meaning of the profile status, creator/last changer as "name (initials)" + date,
validity of the viewed user's assignment, number of assigned users) — analogous to the
always-visible metadata in the query editor. Creator/changer **and** the assignment validity show
the user name, provided the respective user is (still) present in the dataset — otherwise only the
SAP initials (basis team accounts without dialog access, for example, are not necessarily present
as their own user in the extract). The **number of assigned users** is clickable and opens a
dedicated **user list** (ID · name · user type · user group · last login · sleeping) — the same
list page as in the consistency-check drill-down (see below). Below that, as tabs: **transaction
codes** (effective, from `S_TCODE` + role menu), **authorization objects** (with the **field values** maintained in the role per instance; an
**instance** is one authorization (AUTH) of the object in the role — several exist e.g. for
different org values and are not merged; values: ranges as `from..to`, `*` unchanged, long lists
truncated with a tooltip),
**individual authorizations** (which individual filters the role satisfies **on its own**), and
**SoD rules** (which rules the role can trigger **on its own** — intra-role conflict); the latter
two are **role-centric** (freshly computed, independent of the run). If a role has **no S_TCODE
authorization of its own** (composite role, derived role, or a pure data/org authorization role),
the **TCodes** tab shows an explanatory text instead of the lists — the emptiness then matches the
extract, it is not an import error. A separate **generation
date** is not contained in the SAP extract and is therefore not shown.

For this, the matches table shows **user · name · query · label (query's short label) ·
criticality · root cause** — user type/status are deliberately omitted here (they may appear in
the master data tile); instead, it is visible at a glance **which** query matched with **which**
criticality. The findings table no longer shows a sleeping column (instead the root-cause button,
see above). The **rule cell** of the findings table is clickable — it filters (analogous to the
clickable user cell and the rule/query column of the results overview) the same view to this rule,
instead of switching to the root-cause page (which always needs a specific user).

(consistency-checks)=
## 4 · Consistency Checks

A menu with three items — all of them switch the main area (in place of filter/results) to the
check catalog of the respective area; "← back to results" switches back.

| Command | Effect |
| --- | --- |
| **User-specific** | Check catalog categories A/B/C/D/E (critical authorizations, user-master hygiene, assignment consistency, validity/time reference, referential integrity). |
| **Role-specific** | Check catalog category R (role design/quality — structure/generation, assignment/scope, risk/SoD, maintainability). |
| **Import** | Check catalog category I — import evidence (I1): completeness proof against the source SAP extract, matching source rows against the graph result per source table (audit evidence trail). Dataset-wide, no user/role reference. |

**Role rankings (R19, R20) and clickable roles.** The "Risk & SoD" box of the role catalog holds two
rankings: **R19** — roles with the most **SoD findings** (intra- and inter-role conflicts together;
requires the run's evidence) and **R20** — roles that **satisfy the most single-filter queries on
their own** (only queries with hits in the run; composite roles count with their single roles,
column "Type"). Both have the **Top-N** parameter (10/25/50/100) and a **Run** column naming the
evaluated run; for R19 this is the latest run with SoD evidence, for R20 the latest run with
single-filter hits. In every result table of the role checks the **role is clickable** and opens the
**role detail page** (master data, TCodes, authorization objects with values, individual
authorizations, SoD rules); "← back" returns to the check's result table. The dataset comes from the
row's run or the latest run of the selected dataset. R20 takes a few seconds on the first call (about
half a minute with all queries of the ruleset) and is cached briefly afterwards.

**Import evidence (I1) in detail.** (The more detailed view — with key figures, file hash, master data and export —
is the {ref}`Import log <import-log>` in the "Admin" menu.) Uses the reconciliation record automatically recorded with
every import (no separate run needed — provided the dataset was (server-)imported since this
check was introduced; otherwise a notice appears instead of figures). Per source table: source
rows, any filtered rows (e.g., `DELETED='X'`), discarded sensitive columns, the resulting graph
result (node/edge count), and a status — **OK** (genuine 1:1 expectation met), **notice** (the
table deliberately bundles/deduplicates, e.g., authorization field values per AE-03, or an edge
type is shared by several source tables), **deviation** (genuine 1:1 expectation not met), or
**not in the extract** (an optional table was missing). On the check detail page, there is
additionally a dedicated **report block** (PDF/CSV) with the **complete** table-by-table
reconciliation, including a cover sheet (company/system/occasion/author/reference date) — the
general "download report" (see below) shows I1 only as a single catalog entry with a hit count;
this dedicated report is intended for the gapless audit evidence trail.

Addresses the **quality and general risks of the loaded authorization concept itself** —
independent of any specific SoD rule. **Each grid box has its own, framed table** — in the user
area, laid out by category: a 2×2 layout (A·B / C·D) plus **E centered below it**, with
**category pills A–E** (+ "all") above; in the role area, laid out by topic (structure &
generation, assignment & scope, risk & SoD, maintainability & design), likewise 2×2 with topic
pills above — instead of a single long table. Per row, the **check appears bold, with the
rationale in small text below it** — understandable even without specialist knowledge, not just
the short title. The last column, **"results"**, shows the hit count last seen for each check in
this session, otherwise **"not yet run"**, as long as no check logic exists.

Clicking a row **switches** (no pop-up/dialog, the same principle as the catalog itself) to a
**dedicated result view**: the check title on the left, **ID/category/priority chips + "← back to
catalog"** right-aligned at the level of the heading; below it, **two columns, like the findings
view**. **Left:** rationale (always visible, even for checks not yet implemented), below it — as
soon as the check logic exists — a narrow form with **dataset selection** and the display of the
**reference date** (= download date of the SAP extracts, a property of the dataset, no longer a
run filter — correctable globally via "change…", which then applies to all future runs/checks of
this dataset) with **"run"** (shows a spinner during the request), below that a **quick selection
"more checks · …"** with all checks of the same box (category or topic, analogous to the run list,
also works from a check not yet implemented) — clicking switches directly to the next check
without having to go back to the catalog; the dataset selection is retained, so that an entire box
can be clicked through with the same dataset. **Right** the result: some checks show a **pill
filter row** above the table (e.g., lock reason for "locked users with critical roles", status
active/locked, sleeping days 90/180/360) — clicking a pill immediately starts a new run while a
result is already visible, without having to click "run" again — next to it a **table/graph
pill**: live for **A1–A3** (SAP_ALL/SAP_NEW/critical standard profiles) — shows the
user→(role→)profile path as a graph (Cytoscape.js, user node blue, profile node green); for all
other checks it remains disabled ("coming later", analogous to the SoD results). If the check has
both a summary **and** a detail list (e.g., "who has SAP_ALL"), the table view shows **summary
tiles** at the top (human-readable values, e.g., "active"/"locked" instead of raw column names),
with the **detail table** below (columns vary per check, headings likewise translated to be
human-readable instead of the raw Cypher column names) — **column headers are clickable and sort
the table** (numerically or alphabetically depending on content), a small triangle (▲/▼) shows the
column and direction; clicking again reverses it. For some checks (currently A4), a **"root
cause" button** additionally appears per row, which switches to the same **root cause page** as
the SoD/individual-filter root cause (see above) and shows which specific role(s)/profile(s), with
which authorization values, trigger the hit; its "← back" leads back to this consistency check
result (not to the catalog). Checks without a summary show only the detail table. If the summary
consists of **exactly one** tile and the detail table is a user list (e.g., "active dialog users
without a logon" B1), the large metric is **clickable** and opens — freshly enriched from the
database (ID · name · user type · user group · last login · sleeping) — the same user list page as
for "assigned users" on the role detail page. "← back to catalog" (its own button on the check
result itself) switches back to the catalog. Checks not yet implemented show only a notice on the
right instead of a result.

**No persistence (deliberately):** a check run does not create a `(:Run)` node and is not stored
anywhere — the result lives only in the browser for the duration of the session. The last-seen
**hit count** is cached client-side and then replaces the "not yet run" placeholder in the catalog
table — this is a pure UI cache, not server state, and is lost when the page reloads. The complete
catalog with rationale is in [`KONSISTENZCHECKS.md`](https://github.com/neoprehn/iam/blob/main/KONSISTENZCHECKS.md),
the technical framework in [`ROADMAP-ARCHIV.md`](https://github.com/neoprehn/iam/blob/main/ROADMAP-ARCHIV.md),
phase 7.

## 5 · Save

| Command | Effect |
| --- | --- |
| **Backup / Restore** | Opens the dialog: **create backup** (source-data ZIP), the option **then clear** (backup & clear), and the **backup list** with **↻ restore** and **↓ download**. |

Backups contain only the **cleaned source data** — no findings (these are re-analyzed after
restoring). Backups stay local.

In the same dialog, separately below: **run backups** — backs up a single **analysis run** (run +
findings, without evidence; that can be recomputed at any time via "evidence" in the ribbon) as
its own ZIP. For this, every dataset carries a **dataset UID**, which is compared on restore with
the UID stored in the run backup: if it deviates (the dataset has since been repopulated), the app
explicitly asks before the restore.

## 6 · Manage

| Command | Effect |
| --- | --- |
| **Clean up** | Dialog: **delete this dataset** (only the selected dataset, after confirmation) or — set apart in the "danger zone" — **delete all datasets**, which affects **all** datasets and requires typing a confirmation ("DELETE ALL") (the ruleset & schema are preserved in both cases), as well as, separately, **delete a single analysis run** (run + findings; the dataset and other runs remain unaffected). |

Both actions ask for confirmation before executing.

## 7 · Admin

| Command | Effect |
| --- | --- |
| **Query Management** | Link directly to its own page `/admin.html` (no intermediate dialog). |
| **Masterdata** | Link directly to its own page `/admin-masterdata.html` (no intermediate dialog). |
| **Scope** | Link directly to its own page `/admin-scopes.html` (no intermediate dialog). |
| **Documentation** | Opens the documentation on Read the Docs in a new tab — in the currently selected language (German or English). |
| **Import log** | Opens the **import log (completeness evidence)** of the selected dataset (see {ref}`Import Log <import-log>`). |
| **Error log** | Dialog with failed jobs (import/run/backup/restore/clean-up) — **persistent**, survives a container restart (file `data/logs/job_errors.jsonl`). Newest first. |

### Query Management (own page, own ribbon bar)

Reachable via the menu "Admin" (group "7 · Admin") → "Query Management". Its own ribbon groups:
**view** (refresh), **edit** (change/save/cancel; save/cancel become active as soon as something
has been changed), **PFCG suggestion** (only in individual-filter mode, see below), **backup**
(download the overlay file of the selected ruleset), and **back** (to the analysis).

The previously embedded Masterdata panel has been removed from Query Management; catalog
maintenance now happens centrally on the dedicated **Masterdata** page (`/admin-masterdata.html`).

Left: select a **filter set** (currently 3 rulesets), below it the **mode toggle "individual
filter"/"SoD"** — switches the list, filter, and detail area, without discarding the selection in
the other mode. Below that, **search** (supports `*` as a wildcard, e.g., "BC-SEC*", applies in
both modes) and, per mode, its own filters: **individual filter** by **module/criticality/query
type**, **SoD** only by **criticality**. The list shows ID + label, with own/derived or edited
entries marked.

**Individual filter mode** — on the right, after selecting a query: at the top, permanently
visible, the **master data** (short/long label, criticality, module, query type, "ignore
transaction code" — it is the **short label** that appears as the name in the analysis's sidebar
filters), below it three **tabs**:

- **Structure** — the query's transactions and authorization objects. Editable as a **text
  editor** in edit mode (one entry per line — transactions: one TCode per line; authorization
  objects: `Object | Field | AND/OR | Value1,Value2`), analogous to the clause text editor for SoD
  rules. Rare `audit`/`stad` flags on lines that were not touched are preserved on save, even
  though the plain text format does not surface them.

  **Assistant** (button in edit mode, above the two editors) — guided selection of the
  authorization objects and values for **one** TCode instead of typing everything as text. If the
  query contains several TCodes, a choice is offered first; with exactly one, the same dialog as
  "Derive from TCode" opens directly (pick the dataset, SU24 suggestion and real values as chips).
  It is **pre-filled from the current query** (including unsaved changes in the editor): objects
  the query already contains are checked and show their current values, further objects checked per
  SU24 are **not** checked and can be ticked to add them. "Apply" **only writes the result back into
  the text editor** — save afterwards as usual via "Save" or "Save as…". In doing so, an
  **unchecked** object is removed with all its lines; objects unknown to the TCode (added manually)
  and fields outside the SU24 suggestions of a checked object stay **untouched**; changed lines keep
  their position. In the dialog, a **dropdown** lists the query's TCodes; switching reloads the
  suggestion (changes in the dialog that were not yet applied are lost) — so you can switch quickly
  if you change your mind. "Apply" closes the dialog; for another TCode, simply start the
  assistant again.
- **Risk** — risk type/level/status (dropdowns), free text on the potential risk of this
  authorization, a **threat walkthrough** (step-by-step attack path for the threat analysis), as
  well as **sources** (internet sources/references, one URL per line).
- **Controls** — free text: mitigating measures.

**Save as&hellip;** (button next to "Save", edit mode only) creates a fully **independent copy**
of the currently open query under a new ID — carrying over the **current form state, including
unsaved changes** (also to the structure). Before creating it, a warning explains that the copy
will be independent and later changes to either query will not affect the other.

**PFCG suggestion** (ribbon button "derive from transaction code", individual filter mode only) —
builds a completely **new** query, instead of copying an existing one: select a dataset and a
transaction (TCode); "load suggestion" shows, for each authorization object checked by the
transaction, the fields with the **SU24 suggestion** (from USOBT_C) **and** the **real, most
frequently observed values** from the already-imported roles of this dataset (with a hit share,
e.g., "01 (32%)") — clicking a real value chip carries it over into the row's value field. Org
fields are marked with an **"org"** badge and preset to `*` by default (the actual org restriction
runs via org profiles, not via the query itself). Each object can be deselected (checkbox), and
each field's **AND**/OR for multiple values can be toggled. Assign a new query ID + label; "save &
apply" creates the query in the same overlay (`queries.custom.json`) as "derive" — fields without
a value are not carried over.

**SoD mode** — on the right, after selecting a rule: master data (short/long label, criticality,
reason code), below it three **tabs**:

- **Structure** — the CNF clause structure: for each clause, the queries it contains (ID + label);
  all clauses together are AND-combined, within a clause one matched query suffices. If a ruleset
  does not yet have `clauses` stored (currently CSI/CSI_BI, see ROADMAP), the tab instead shows the
  raw expression (`expression`) and the variable mapping.
- **Risk** / **Controls** — as with the individual filter, with their own free-text fields per SoD
  rule.

**Save as&hellip;** (same as for individual filters, see above) creates a new, independent SoD rule
under a new ID — carrying over master data, risk, and the clauses currently in the form (including
unsaved changes). Save/cancel (ribbon **or** detail area) as well as "save overlay" (ribbon
**backup**) act, in whichever mode is active, on the matching overlay (`queries.custom.json` or
`sod_rules.custom.json`).

**One-pager (PDF)** (ribbon group "export", in both modes) — exports the query or SoD rule
selected on the left as a single-page PDF (A4 portrait) with all available information: master
data, criticality badge (color as in the frontend), risk (type/level/status, risk description,
threat walkthrough, sources), controls, and the structure — for a query, the transaction(s) and the
authorization-objects table; for an SoD rule, the resolved clause structure (or expression +
variable mapping, if no `clauses` are stored), including the short labels of the referenced
queries. Empty sections (e.g., no risk recorded) are omitted rather than shown empty. The layout is
designed for a single sheet and fits reliably for the usual data volumes; an unusually large number
of authorization rows overflows onto a second page rather than cutting off content.

Changes are **never** written to the vendor file (`queries.json`), but to a separate overlay
(`queries.custom.json`) per ruleset — vendor updates therefore do not overwrite custom
adjustments. Save/derive takes effect **immediately** (no extra reload step needed).

### Masterdata (own page, own ribbon bar)

Reachable via the menu "Admin" (group "7 · Admin") → "Masterdata".

The page bundles the maintenance of the central catalogs:

- **Criticalities** (ID computed internally; label/rank/color/KRI editable)
- **Reason codes (SoD)**
- **Modules** (ID technical, derived from the label)
- **Query types** (ID technical, derived from the label, with description)
- **Company logo and name in the product name** — the logo replaces the default badge in the
  header. The field **"name in the product name"** sets the first word of KARMA's expansion
  ("… Access Risk & Monitoring Assistant") in the header and footer; left empty, the default
  remains "Key". Both are stored only **locally** in `config/branding.json` and are never
  committed to the repository.

These catalogs are used in Query Management as **dropdowns instead of free text**
(criticality/data-protection/risk level as well as module/query type/reason code).

The section "criticality shown prominently on individual filter/SoD" describes the UI use of the
catalog values (badges/colors/filters) and is **not** a separate master-data catalog.

### Scope (own page, own ribbon bar)

Reachable via the menu "Admin" (group "7 · Admin") → "Scope". Manages **persistent, named scope
profiles** — the same catalog selection (individual filters/SoD rules, filterable by name pattern
**on the label**/module/criticality/query type, multiple selection via checkbox) as in the wizard
step "scoping", but **permanently saved** and reusable across any number of runs/datasets of the
same ruleset (see "saved scope" above).

Left: select a **ruleset**, below it the list of scopes saved for this ruleset (with a count "N
individual filters, M SoD rule(s)"), "+ new scope". On the right, a freely clickable mini-stepper
**① individual filters · ② SoD rules · ③ save**:

- **① Individual filters** — catalog table (about 20 rows visible, the rest scrolls), filter by
  name pattern (matches the label)/module/query type/criticality, "select all (filtered)"/"clear
  selection". Optional — can proceed to ② even with no selection at all.
- **② SoD rules** — the same table logic for SoD rules, with an additional toggle **"all" / "only
  possible"**: "only possible" shows only rules whose clauses are all covered by the individual
  filters selected under ① (bidirectional linking via the ruleset's CNF clause structure —
  currently only present for the SAP R/3 ruleset; without this structure, a notice appears instead
  of the toggle, and all rules remain visible).
- **③ Save** — name (editable only on initial creation), description, **user-type profile**, and
  **sleeping (days)** (the same axes as in the "new run" form), and a summary. If an SoD rule is
  selected whose clause queries are not already checked under ①, the app **automatically** adds
  them on save (never removing anything) — the summary states this ("of which N automatically
  added"), so that the rule can actually be analyzed later as well. Saving requires at least one
  individual filter **or** one SoD rule.

A **new** scope starts guided at ①; an **existing** scope opens directly at ③ (summary) — via the
stepper, you can go back to ①/② at any time to adjust it, then save again or delete it.

Scope profiles refer to query/SoD-rule **IDs** of a ruleset — purely catalog vocabulary, not client
data — and therefore live, like the individual-filter/SoD-rule overlays, in the ruleset folder
(`rules/<Ruleset>/scope_profiles.custom.json`), tracked by git.

**Planned** in this area:

- **Master-data sheet: query → system type** (SAP R/3, S/4HANA, more planned in the future).
- **Import a new filter set** — additional systems as their own ruleset, prospectively **SAP
  S/4HANA, Azure AD / Entra, Microsoft Dynamics, Salesforce** (the data model stays the same).

> The app **deliberately has no user/authorization concept of its own**: it runs locally or is
> distributed as a container; access is secured via the environment.

## SAP Security: Attack Paths (Prototype)

Ribbon **8 · Security → Attack Paths**. The idea is similar to BloodHound: accounts are nodes,
"can do X" are edges, and the shortest paths to **tier-zero accounts** are sought (SAP_ALL/SAP_NEW
directly or via a role, plus configurable role patterns/accounts). The edges are derived
**statically from the authorization values** — the result is *potential* paths for audit and
security, not proven exploits; nothing is executed.

| Type | Authorization | Meaning |
|---|---|---|
| lateral | `S_USER_GRP` ACTVT 02 (CLASS pattern) | Change the password/master data of accounts in this user group |
| lateral | `S_BTCH_NAM` (BTCUNAME pattern) | Schedule a background job under the name of the target account |
| direct | `S_DEVELOP` 02 + DEBUG | Debug/Replace |
| direct | `S_TABU_NAM`/`S_TABU_DIS` change | Change authorization/user tables |
| direct | `S_LOG_COM` COMMAND `*` | arbitrary OS commands |
| direct | `S_USER_AGR` 02 on own role; 02 + 22 with `S_USER_GRP` | grant oneself rights |
| direct | `S_RFC` ACTVT 16 on critical modules | Remote call of critical function modules |
| remote marker | `S_RFC` ACTVT 16 on `*` or critical function groups/modules | the step is possible remotely (RFC) |

The analysis is evaluated as of the **dataset's reference date**; locked, expired, and reference
accounts do not count. The view shows KPI tiles (accounts with a path, direct/lateral,
remote-capable), filters, a table with a path graph per account, and **bottlenecks**
(roles/profiles through which most accounts gain their first escalation capability, and
intermediate accounts). The catalog (objects, activities, critical RFC modules, table list,
tier-zero definition) is in `config/security_catalog.json` and is a **sample catalog** that must be
reviewed and extended by subject-matter experts before production use. Limitations: a static view
(locks/validity are taken into account, runtime checks are not), one system per dataset; RFC trust
relationships (SM59/RFCDES) are not yet part of the extraction.
