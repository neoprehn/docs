# Phase 1 — Data Model

**Goal:** A fixed schema (labels, relationship types, property keys) as versioned migrations.
**DoD:** `neo4j-migrations` reproducibly creates the complete schema.

The business model (labels, edges, properties, the `dataset` dimension) is described in
[Data Model](../datamodel.md). This page documents the **tooling** and the **procedure**.

## Migrations Tooling (AE-02)

Schema changes run via [neo4j-migrations](https://github.com/michael-simons/neo4j-migrations)
(Flyway-like: versioned files `V001__…`, idempotent, recorded as done in the DB).

Since there is no maintained official container image, a **pinned** image is built in-house
(AE-14/AE-15): Eclipse Temurin 21 (JRE) + neo4j-migrations 4.1.0 (JVM distribution), see
`docker/neo4j-migrations.Dockerfile`. It runs as the compose service `migrations` with
`profiles: ["tools"]`, so it does **not** start on `docker compose up`.

```yaml
  migrations:
    build:
      context: ./docker
      dockerfile: neo4j-migrations.Dockerfile
    image: iam-neo4j-migrations:4.1.0
    profiles: ["tools"]
    depends_on:
      neo4j:
        condition: service_healthy
    environment:
      NEO4J_PASSWORD: ${NEO4J_PASSWORD}
    volumes:
      - ./migrations:/migrations
```

An entrypoint script sets the connection flags from the environment (`--address=bolt://neo4j:7687`,
`--username`, `--password`, `--location=file:/migrations`), so that only the subcommand needs to
be passed. The password comes from `.env` and never ends up in the image.

## Migration Files

```text
migrations/
├─ V001__constraints.cypher   # unique constraints (Community: single-property)
└─ V002__indexes.cypher       # composite lookups + ASSIGNED_TO validity (range)
```

For the key strategy (`dataset`, synthetic `key`, Community limitation), see
[Data Model](../datamodel.md#community-peculiarity-synthetic-key).

## Applying & Checking

```powershell
# Build the image once
docker compose build migrations

# Status of the migrations
docker compose run --rm migrations info

# Apply the schema
docker compose run --rm migrations

# (Verification directly in the DB)
docker exec -i iam-neo4j cypher-shell -u neo4j -p "$env:NEO4J_PASSWORD" "SHOW CONSTRAINTS;"
docker exec -i iam-neo4j cypher-shell -u neo4j -p "$env:NEO4J_PASSWORD" "SHOW INDEXES;"
```

:::{note}
`migrate` is idempotent: neo4j-migrations records applied versions in the DB
(`__Neo4jMigration` nodes) and skips them on the next run. A second invocation reports
"nothing to migrate".
:::

### Result When This Phase Was Built

`migrate` reported *"Database migrated to version 002."*. `SHOW CONSTRAINTS`/`SHOW INDEXES`
confirm:

- Unique constraints: `dataset_id`, `user_key`, `role_key`, `profile_key`, `authobject_key`,
  `transaction_key`.
- Composite lookup indexes `(dataset, id)` for User/Role/Profile/AuthObject/Transaction, a
  `dataset` index for Authorization.
- The relationship range index `assigned_to_validity` on `ASSIGNED_TO(validFrom, validTo)`.

This satisfies the DoD of phase 1 — the schema is reproducible from the repo.

## Adding a New Migration

Place the next file following the pattern `V003__<description>.cypher` in `migrations/` (LF line
endings, enforced by `.gitattributes`), then run `docker compose run --rm migrations`. **Do not**
retroactively change migrations that have already been applied (checksum check) — create a new
version instead.
