# IAM — SAP Authorization Analysis with Neo4j

Graph-based analysis of SAP authorizations (R/3 and S/4HANA): **can-do** (authorization) analysis and
**SoD conflict analysis**, operated as a local web app. The environment runs **container-only** via
Docker Desktop/WSL2 — without a local Neo4j or Java installation on the host.

The documentation is organized into two parts:

- **User handbook** — what the app can do, what each function does, and what the workflow looks like.
- **Technical documentation** — architecture (current state), data model, extraction, and the
  **development history** (how we got to the current state, phase by phase).

:::{admonition} Trust boundary
:class: important

This documentation describes exclusively **logic, environment, and procedure** — never client data.
SAP extracts, the DB volume, and backups stay local (`data/`, `backups/`, gitignored).
:::

```{toctree}
:maxdepth: 2
:caption: User Handbook

handbuch/ueberblick
handbuch/workflow
handbuch/funktionen
```

```{toctree}
:maxdepth: 2
:caption: Technical Documentation

technik/architektur
technik/windows-native
technik/ergebnisuebergabe
datamodel
extraktionsleitfaden
```

```{toctree}
:maxdepth: 1
:caption: Development History (Phases)

phasen/phase-0
phasen/phase-1
phasen/phase-2
phasen/phase-3
phasen/phase-5
phasen/phase-9
phasen/phase-10
```

## Further Reading

- Full roadmap & architecture decisions: `ROADMAP.md` in the repo root.
- Source code & environment: <https://github.com/neoprehn/iam>
