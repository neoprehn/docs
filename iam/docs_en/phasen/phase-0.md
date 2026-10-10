# Phase 0 — Foundation & Environment

**Goal:** A working local Neo4j environment and the repo scaffold. **DoD:** A freshly cloned repo
brings up an empty, working environment with a few commands.

The environment is **container-only** (AE-15): Neo4j, NeoDash, and APOC run as containers via
Docker Desktop with the WSL2 backend. **No** Neo4j or Java installation is needed on the Windows
host; `cypher-shell` is invoked via the running container.

## Prerequisites (Host)

One-time, on the Windows machine. Both steps need administrator rights and a restart.

### 1. Install WSL2

In a PowerShell started **as administrator**:

```powershell
wsl --install
```

Then **restart the machine**.

### 2. Install Docker Desktop

Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop), leaving the
option *"Use WSL 2 instead of Hyper-V"* enabled. Then start Docker Desktop and wait until the
engine is running.

### 3. Verify

```powershell
wsl -l -v
docker --version
docker compose version
```

Expected: WSL lists a distro with `VERSION 2`, `docker` and `docker compose` respond with a
version number. Reference when this phase was built: Docker `29.5.3`, Compose `v5.1.4`.

## Repo Scaffold

The target structure strictly separates logic (in the repo) from data (local, gitignored —
AE-01):

```text
iam/
├─ docker-compose.yml   # Neo4j + NeoDash, versions pinned, APOC
├─ migrations/          # neo4j-migrations: constraints, indexes (phase 1)
├─ load/               # LOAD CSV scripts (phase 2)
├─ rules/              # rule catalog sod_matrix.csv (phase 3)
├─ cypher/
│  ├─ checks/          # individual-authorization checks
│  └─ sod/             # SoD queries
├─ dashboards/         # NeoDash export (JSON, phase 6)
├─ run/                # runner (phase 5)
├─ docs/               # this documentation (Sphinx/MyST) + docs/legacy
└─ data/              # GITIGNORED: SAP CSV + DB volume + import
```

### `docker-compose.yml`

Pinned versions ensure reproducibility (AE-14). APOC is automatically loaded to match the Neo4j
version via `NEO4J_PLUGINS` — no separate image.

```yaml
services:
  neo4j:
    image: neo4j:5.26.27-community
    container_name: iam-neo4j
    ports:
      - "7474:7474"   # Neo4j Browser (HTTP)
      - "7687:7687"   # Bolt
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc"]'
      NEO4J_apoc_import_file_enabled: "true"
      NEO4J_apoc_import_file_use__neo4j__config: "true"
      NEO4J_dbms_security_procedures_unrestricted: "apoc.*"
    volumes:
      - ./data/db:/data
      - ./data/import:/var/lib/neo4j/import   # file:///<name>.csv (AE-15)
      - ./data/logs:/logs
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://localhost:7474 || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 10
      start_period: 40s
    restart: unless-stopped

  neodash:
    image: neo4jlabs/neodash:2.4.11
    container_name: iam-neodash
    ports:
      - "5005:5005"
    depends_on:
      neo4j:
        condition: service_healthy
    restart: unless-stopped
```

Important for Windows: relative paths with forward slashes (`./data/db:/data`), a fixed container
name `iam-neo4j` (so that `docker exec` in the later runner stays stable).

### Protective Files

`.gitignore` keeps data, secrets, and dumps out of the repo (AE-01):

```text
/data/
.env
*.dump
```

`.gitattributes` enforces LF line endings for scripts that run in the Linux container — otherwise
execution fails on CRLF (AE-15):

```text
*.cypher text eol=lf
*.sh     text eol=lf
*.ps1    text eol=crlf
```

`.env.example` is the template; the real `.env` (with the Neo4j password, min. 8 characters) stays
local and gitignored.

## Start & Verification

```powershell
# Create credentials (local, gitignored)
Copy-Item .env.example .env
notepad .env            # set NEO4J_PASSWORD (min. 8 characters)

# Start the environment (first start pulls images + APOC, takes a while)
docker compose up -d

# Status
docker compose ps
```

:::{note}
Neo4j only takes over the password from `NEO4J_AUTH` on the **first** start, as long as `data/db`
is empty. A later password change only takes effect after deleting the DB volume.
:::

Reachability of the web interfaces:

- Neo4j browser: <http://localhost:7474>
- NeoDash: <http://localhost:5005>

Run Cypher via the container (no local `cypher-shell` needed — AE-15):

```powershell
docker exec -i iam-neo4j cypher-shell -u neo4j -p "$env:NEO4J_PASSWORD" "RETURN 1 AS ok;"
docker exec -i iam-neo4j cypher-shell -u neo4j -p "$env:NEO4J_PASSWORD" "RETURN apoc.version();"
```

### Result When This Phase Was Built

| Check | Result |
| --- | --- |
| `iam-neo4j` | Up, **healthy** (ports 7474/7687) |
| `iam-neodash` | Up (port 5005) |
| Neo4j browser `:7474` | HTTP 200 |
| NeoDash `:5005` | HTTP 200 |
| `cypher-shell … RETURN 1` | `ok = 1` |
| APOC | `5.26.27` loaded |

This satisfies the DoD of phase 0.

## Useful Commands

```powershell
docker compose ps                 # status
docker logs iam-neo4j             # Neo4j logs
docker compose down               # stop (data stays in the volume)
docker compose down -v            # stop + delete volumes (reset, dev ONLY)
docker compose up -d              # (re-)start
```
