# Result Handover (Database Dump/Restore)

This procedure hands over the **complete Neo4j database state** (all datasets, runs, findings) to
another environment — e.g. to a colleague or another machine of your own. It is different from the
app's **Backup/Restore** feature (ribbon "Save"): that only backs up the **cleaned source data of a
single dataset** as a ZIP, with no findings and no other datasets. For a full handover of the
entire DB state, `neo4j-admin database dump`/`load` is the right approach instead.

:::{admonition} Trust boundary
:class: important
A dump contains the complete data set and therefore potentially client data. Handing it over is
subject to the same requirements as the rest of the environment — transferred encrypted, only to
authorized recipients, under the applicable client confidentiality rules. This page describes only
the technical procedure, not approval or transmission rules.
:::

## Prerequisite

Neo4j **Community Edition** cannot pause a single database (`STOP DATABASE` is Enterprise-only) —
so for both dump and restore, the **entire** `neo4j` container is briefly stopped. The app is
unreachable during that time.

## Creating a Dump (Source Environment)

```powershell
# 1. Stop the container (the backend may stay up, but loses its DB connection)
docker compose stop neo4j

# 2. Write the dump -- <host> is any local target folder for the output file
docker compose run --rm -v <host>:/hostout neo4j neo4j-admin database dump neo4j --to-path=/hostout

# 3. Start the container again
docker compose start neo4j
```

The result is a single `neo4j.dump` file in the given `<host>` folder. Encrypt this file before
handing it over (e.g. 7-Zip with a password, or a procedure mandated by the client) — the dump
itself is not encrypted.

## Restore (Target Environment)

```powershell
# 1. Stop the container
docker compose stop neo4j

# 2. Load the dump file from the same <host> folder -- existing data gets overwritten
docker compose run --rm -v <host>:/hostin neo4j neo4j-admin database load neo4j --from-path=/hostin --overwrite-destination=true

# 3. Start the container again
docker compose start neo4j
```

`--overwrite-destination=true` is required as soon as the target database already exists (e.g.
after the first `docker compose up`) — without the flag, the load aborts.

## Verified

The procedure was verified end-to-end against a separate test volume: dump from the source
environment, load into a fresh target environment, node count between source and target **1:1**
identical. No deviations from the dump/restore cycle itself.
