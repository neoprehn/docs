# Neo4j LLM Graph Builder als Betrachter (Schritt 1.4)

**Stand:** 31.10.2026. Der Graph Builder ist ein Neo4j-Labs-Experiment (ohne Produktunterstützung). Wir nutzen ihn
nur zum **Ansehen** des Graphen, nicht zum Extrahieren.

## Aufbau

- Quellcode: `git clone https://github.com/neo4j-labs/llm-graph-builder.git data/llm-graph-builder`
  (getestet mit Commit `a728de6`, 23.10.2026). Der Ordner `data/` ist nicht im Git.
- Dienste in `docker-compose.graphbuilder.yml` (Profil `graphbuilder`, startet nie von selbst):
  - Oberfläche: <http://127.0.0.1:18080>, Backend: `127.0.0.1:18000` (die Standardports 8080 und 8000 sind belegt).
  - Beide Dienste hängen im selben Docker-Netz wie Neo4j und erreichen es als `bolt://neo4j:7687`.
- Start: `docker compose -f docker-compose.yml -f docker-compose.graphbuilder.yml --profile graphbuilder up -d`
  (beim ersten Mal mit `--build`, rund 15 Minuten wegen torch und der Dokumentbibliotheken)
- Stopp: `docker compose -f docker-compose.yml -f docker-compose.graphbuilder.yml --profile graphbuilder stop gb-backend gb-frontend`
- Vor dem ersten Start einmal `kg graphbuilder-prepare` ausführen (setzt die Zusatzeigenschaften unten).

## Verbinden in der Oberfläche

Beim Verbinden fragt der Graph Builder nach den Neo4j-Daten. Weil sein Backend im Container läuft, gilt:

| Feld | Wert |
|---|---|
| URI | `bolt://neo4j:7687` (nicht `localhost`) |
| Benutzer | `neo4j` |
| Passwort | `NEO4J_PASSWORD` aus der `.env` |
| Datenbank | `neo4j` |

## Was er von unserem Datenmodell erwartet

Beziehungen (`PART_OF`, `FIRST_CHUNK`, `NEXT_CHUNK`, `HAS_ENTITY`) stimmen mit unserem Modell überein. Abweichend sind
die Eigenschaftsnamen. `kg graphbuilder-prepare` ergänzt sie, rein additiv und wiederholbar, ohne etwas zu ändern:

| Knoten | Zusatzeigenschaft | Quelle |
|---|---|---|
| Document | `fileName` (Schlüssel beim Graph Builder) | `rel_path`, weil Dateinamen allein nicht eindeutig sind |
| Document | `fileSource`, `fileType`, `fileSize`, `status`, `total_chunks`, `processed_chunk`, `chunkNodeCount`, `createdAt`, `updatedAt` | eigene Werte |
| Chunk | `id`, `fileName`, `page_number`, `length` | `chunk_id`, `rel_path`, `page_start`, Textlänge |

`page_number` ist die **PDF-Seite**, nicht die gedruckte Buchseite. Für Quellenangaben gilt weiter `page_label_start`.

## Risiken

- **Schreibrechte.** Der Graph Builder nutzt dieselben Zugangsdaten. Neo4j Community hat keine eingeschränkten
  Benutzer, daher kann er in der Oberfläche **löschen und überschreiben** (z. B. „Delete files“, „Generate graph“).
  Nur bei Bedarf starten, danach stoppen, nichts anklicken außer Ansehen. „Generate graph“ würde ohne LLM-Schlüssel
  scheitern; wir haben dem Backend bewusst keine mitgegeben.
- **Sicherung** vor Experimenten: `neo4j-admin database dump` (siehe `docs/erfahrungen.md`, Schritt 1.4).
- **Indexe:** Beim Verbinden legt er keine eigenen Indizes an. Beim Verarbeiten würde er einen Vektorindex `vector`
  mit anderer Dimension anlegen; das würden wir nicht zulassen.
