# Konzept: Lokaler Literatur-Wissensgraph mit agentischer Extraktion

**Projekt:** Literatur-Wissensgraph (Pilot: Identity & Access Management)
**Stand:** 31.10.2026 – Version 0.3 (ergänzt: Vorgehen Ontologie-Aufbau, Auswahl lokaler Modelle, Anbieter-Mix Claude/OpenAI)
**Zweck dieses Dokuments:** Bauplan für die Umsetzung mit Claude Code in VS Code. Claude Code arbeitet die Phase-1-Schritte (Kapitel 10) der Reihe nach ab.
**Ergänzungen:** [Ergänzung 01 – Nachnutzung, Themenerweiterung und Steuer-UI](ergaenzung-01-nachnutzung-themen-ui.md) (erweitert u. a. Kap. 1, 7 und 9 sowie die Schritte um 1.11 und 2.1–2.5; noch nicht in dieses Dokument eingearbeitet)

---

## 1. Ziel und Scope

Aus einer persönlichen Fachbibliothek (ca. 100 Bücher, ca. 400 Fachartikel, PDF, DE/EN) entsteht ein lokaler Wissensgraph. Über ihn können Mensch und Claude themenübergreifend recherchieren, Konzepte und Frameworks verknüpfen und darauf eigene Lösungen entwickeln.

| Phase | Inhalt | Umgebung |
|---|---|---|
| **1 (jetzt)** | Infrastruktur, Ingestion der gesamten Bibliothek, IAM-Pilot (Scouting, Extraktion, QA), MCP-Zugriff für Claude | Heimrechner, Docker |
| 2 (später) | Steuer-UI (Streamlit) und Skill „Neues Thema“ auf Basis des Erfahrungsprotokolls | Heimrechner |
| 3 (später) | Umgebung auf dem Arbeitsrechner ohne Docker, Übertragung des Graphen ohne Neuaufbau, weitere Themen über die UI, Entwicklung der IAM-Lösung | beide |

**Meilenstein „Prozess stabil“** (Ende Phase 1): Der IAM-Durchlauf ist abgeschlossen und im Erfahrungsprotokoll vollständig dokumentiert. Erst dann wird die UI gebaut und das System auf den Arbeitsrechner gebracht – so wird ein erprobter, eingefrorener Prozess übertragen statt einer Baustelle.

**Nicht im Scope von Phase 1:** Mandantendaten, Cloud-Hosting, Mehrbenutzerbetrieb.

## 2. Annahmen und offene Punkte

| # | Annahme / offener Punkt | Auswirkung |
|---|---|---|
| A1 | Heimrechner mit Docker Desktop; Betriebssystem noch zu bestätigen | Pfade und Compose-Details |
| A2 | GPU vorhanden; Typ und Grafikspeicher (VRAM) werden in Schritt 1.0 ermittelt | Bestimmt die Größe des lokalen Scout-Modells und ob Ollama die GPU im Container nutzt |
| A3 | Literatur liegt lokal synchron in OneDrive | **Wichtig:** Ordner auf „Immer auf diesem Gerät behalten“ stellen, sonst sind Dateien nur Platzhalter |
| A4 | PDFs haben überwiegend einen Textlayer | Gescannte PDFs werden erkannt und markiert; OCR erst bei Bedarf |
| A5 | Claude-API-Schlüssel wird über die Claude Console angelegt | Extraktion und QA über die API; Kuratierung im Chat bzw. in Claude Code |
| A6 | Literatur ist ausschließlich zum persönlichen Gebrauch, bleibt lokal | Keine Veröffentlichung von Inhalten |

## 3. Architekturprinzipien

1. **Infrastruktur in Docker, Pipeline als normales Python-Paket.** Neo4j und Ollama laufen in Docker. Die Pipeline läuft in einer Python-Umgebung (venv) direkt auf dem Rechner. Für den Arbeitsrechner (Phase 3) wird nur die Infrastruktur getauscht, der Code bleibt identisch.
2. **Neo4j ist die einzige Wahrheit.** Graph, Vektorindex, Arbeitswarteschlange und Protokoll liegen in Neo4j. Jeder Lauf ist fortsetzbar.
3. **Deterministischer Orchestrator.** Die Verteilung der Arbeit ist Code (Zustandsmaschine mit Routing-Tabelle), kein frei entscheidendes LLM. Jeder Schritt wird protokolliert.
4. **Nachvollziehbarkeit (Provenance) ist Pflicht.** Jede extrahierte Aussage verweist auf Chunk, Dokument, Seite, Modell, Prompt-Version und Lauf.
5. **Idempotenz und stabile IDs.** Dokument-IDs entstehen aus dem Datei-Hash, Pfade werden relativ zum Bibliotheks-Stamm gespeichert. Das ist die Voraussetzung für die Übertragung in Phase 3.
6. **Literatur ist schreibgeschützt.** Die Pipeline liest die Bibliothek nur, sie verändert nie etwas darin.
7. **Günstig vor teuer.** Embeddings und Vorfilter laufen lokal, das lokale LLM nur für Grauzonen, die Claude-API nur, wo Qualität zählt.

## 4. Komponenten

| Komponente | Aufgabe | Technik | Läuft |
|---|---|---|---|
| Neo4j | Graph, Vektorindex, Warteschlange, Protokoll | Neo4j Community ≥ 5.15 mit APOC (Version beim Setup prüfen, inzwischen Kalenderversionierung) | Docker |
| Ollama | Embeddings und lokales LLM für den Scout | Ollama, mehrsprachiges Embedding-Modell (Kandidat: `bge-m3`), kleines Instruct-Modell | Docker |
| Pipeline `kg` | Ingestion, Chunking, Embedding, Agenten, Orchestrator, CLI | Python ≥ 3.11, `neo4j`, `pymupdf` (Fallback `docling`), `anthropic`, `typer`, `pydantic` | venv |
| LLM-APIs | Extraktor, Prüfer, Eskalation | Claude (Sonnet/Haiku) und optional OpenAI; Anbieter und Modell je Agent in `config.yaml` (Kap. 8a) | Cloud |
| Neo4j-MCP-Server | Zugriff von Claude Code auf den Graphen | offizieller Neo4j-MCP, STDIO | lokal |
| LLM Graph Builder | Explorer und Chat-Oberfläche | Neo4j Labs, optional | Docker (Phase 1b) |

## 5. Docker-Setup (Skizze)

Claude Code erstellt daraus die finale `docker-compose.yml`.

```yaml
services:
  neo4j:
    image: neo4j:<aktuelle-version>-community
    ports:
      - "127.0.0.1:7474:7474"   # Browser
      - "127.0.0.1:7687:7687"   # Bolt
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc"]'
      NEO4J_server_memory_heap_max__size: 4G
      NEO4J_server_memory_pagecache_size: 2G
    volumes:
      - ./data/neo4j/data:/data
      - ./data/neo4j/logs:/logs
      - ./data/neo4j/import:/import

  ollama:
    image: ollama/ollama
    ports:
      - "127.0.0.1:11434:11434"
    volumes:
      - ./data/ollama:/root/.ollama
    # GPU optional, nur wenn vorhanden (NVIDIA):
    # deploy: { resources: { reservations: { devices: [ { capabilities: [gpu] } ] } } }
```

- Alle Ports nur an `127.0.0.1` binden.
- Speicherwerte an den Rechner anpassen (16–32 GB RAM reichen).
- Die Literatur wird **nicht** in Container gemountet; die Pipeline liest sie direkt vom Dateisystem.
- **Umgesetzt mit Abweichungen** (Schritt 1.0, Begründung in `docs/erfahrungen.md`): Host-Ports 17474/17687 statt 7474/7687, benannte Volumes für Neo4j-Store und Ollama-Modelle, Neo4j 5.26 LTS.

## 6. Datenmodell in Neo4j

### 6.1 Basisschicht (kompatibel zum LLM Graph Builder – in Schritt 1.4 zu verifizieren)

```
(:Document {doc_id, title, authors, year, doc_type, rel_path, file_name, sha256, pages, has_text_layer, ingested_at})
(:Chunk {chunk_id, text, page_start, page_end, position, token_count, embedding, heading_path})
(:Chunk)-[:PART_OF]->(:Document)
(:Document)-[:FIRST_CHUNK]->(:Chunk)
(:Chunk)-[:NEXT_CHUNK]->(:Chunk)
(:Chunk)-[:SIMILAR {score}]->(:Chunk)      // optional
(:Chunk)-[:HAS_ENTITY]->(:__Entity__)
```

- `doc_id` = SHA-256 des Dateiinhalts → identisch auf Heim- und Arbeitsrechner.
- `rel_path` relativ zum Bibliotheks-Stamm (`LIBRARY_ROOT` in `.env`).
- Vektorindex auf `Chunk.embedding` (Dimension je nach Embedding-Modell).

### 6.2 Themen und Arbeitswarteschlange

```
(:Topic {topic_id, name, description, embedding, examples, ontology_version, status})
(:Chunk)-[:TAGGED {score, method, model, confirmed}]->(:Topic)
(:WorkItem {item_id, topic_id, chunk_id, stage, attempts, last_error, updated_at})
(:Run {run_id, agent, model, prompt_version, started_at, finished_at, items, input_tokens, output_tokens})
```

**Stufen eines WorkItems:** `new → scouted → extracting → extracted → qa_passed | qa_failed → (retry) → done | needs_human`

### 6.3 Fachschicht (Entitäten)

- Alle Entitäten tragen zusätzlich das Label `:__Entity__` (Graph-Builder-Kompatibilität) sowie `canonical_name`, `aliases` (DE/EN), `definition`, `topics`.
- Jede fachliche Beziehung trägt `source_chunk_id`, `run_id`, `confidence` und ein kurzes Belegzitat (`evidence`, max. 25 Wörter).

## 7. IAM-Ontologie

### 7.0 Vorgehen beim Aufbau (gemeinsam mit Claude)

Eine Ontologie ist hier schlicht die Festlegung: **Welche Arten von Dingen gibt es, wie dürfen sie zusammenhängen, und wie heißen sie einheitlich?** Ein formales OWL/RDF-Modell ist nicht nötig; ein Property Graph mit einer YAML-Datei genügt.

| Schritt | Was passiert | Wer |
|---|---|---|
| O1 Kompetenzfragen | 10–15 Fragen, die der Graph später beantworten soll (z. B. „Welche Kontrollen mitigieren verwaiste Konten?“, „Welche NIST-Anforderungen gelten für AAL2 und welche Quellen beschreiben die Umsetzung?“) | Mirko formuliert, Claude ergänzt |
| O2 Begriffssammlung | Begriffe aus Inhaltsverzeichnis und Glossar des IAM-Buchs, NIST SP 800-63-4, eigener Praxis | Claude sammelt, Mirko kürzt |
| O3 Typen bilden | Begriffe zu 8–12 Knotentypen gruppieren (Startentwurf: Tabelle 7.1) | Claude schlägt vor, Mirko entscheidet |
| O4 Beziehungen festlegen | Erlaubte Verbindungen zwischen Typen, je mit Definition und Beispiel | gemeinsam |
| O5 Regeln schreiben | Je Typ: Definition, 2–3 Positiv- und 1 Negativbeispiel, Benennungsregeln, Abgrenzungen | Claude entwirft |
| O6 Probeextraktion | 2–3 Seiten per Hand bzw. mit dem Extraktor; Ergebnis gegen die Kompetenzfragen prüfen | gemeinsam |
| O7 Nachschärfen | Fehlende Typen ergänzen, unscharfe zusammenlegen → Version v0.2 | Mirko gibt frei |

**Faustregeln:** lieber wenige, klar abgegrenzte Typen als viele; jede Beziehung muss mindestens eine Kompetenzfrage bedienen; bestehende Vokabulare (NIST-Glossar, ISO/IEC 27000) als Referenz für Definitionen nutzen.

### 7.1 Startentwurf v0.1

| Knotentyp | Beispiele |
|---|---|
| `Concept` | Identität, Digitale Identität, Vertrauensniveau |
| `Principle` | Least Privilege, Need-to-know, Segregation of Duties, Zero Trust |
| `Process` | Joiner-Mover-Leaver, Rezertifizierung, Notfallzugriff |
| `AccessModel` | RBAC, ABAC, PBAC, JIT-Access |
| `Component` | IGA, PAM, IdP, SSO, Verzeichnisdienst, MFA |
| `Actor` | Rolleneigner, Data Owner, Prüfer, Administrator |
| `Control` | Berechtigungsfreigabe, Access Review, Passwortrichtlinie |
| `Requirement` | aus Literatur abgeleitete Anforderung |
| `Standard` | NIST SP 800-63-4, ISO/IEC 27001, BSI IT-Grundschutz, DORA |
| `StandardClause` | NIST-Anforderung (IAL/AAL/FAL), ISO-Control |
| `Risk` | Rechteausweitung, verwaiste Konten, Credential Stuffing |

**Beziehungen:** `PART_OF`, `REQUIRES`, `IMPLEMENTS`, `SUPPORTS`, `MITIGATES`, `CONFLICTS_WITH`, `DEFINED_IN`, `MAPS_TO`, `RESPONSIBLE_FOR`, `ALIAS_OF`.

**Regeln für den Begriffsabgleich:**
1. Vor dem Anlegen einer Entität: Suche nach ähnlichen `canonical_name`/`aliases` (Embedding-Ähnlichkeit plus exakter Abgleich).
2. Treffer über Schwellwert → bestehende Entität verwenden und ggf. Alias ergänzen.
3. Grauzone → LLM-Bestätigung; bleibt Unsicherheit → `needs_human`.
4. Kanonische Namen auf Englisch, Aliase in beiden Sprachen.

Die Ontologie liegt versioniert in `ontology/iam.yaml`. Änderungen erfordern deine Freigabe.

## 8. Pipeline und Agenten

| Stufe | Agent | Modell | Logik |
|---|---|---|---|
| Ingestion | – | – | PDF → Text je Seite, Metadaten, Textlayer-Prüfung |
| Chunking | – | – | ca. 800 Tokens, 100 Überlappung, Überschriften respektieren, Seitenbereich mitführen |
| Embedding | – | Ollama (lokal) | einmal je Chunk; Batch-Verarbeitung |
| Scouting | Scout | Embedding-Vorfilter, dann Ollama, Eskalation Haiku | Stufe 1: Ähnlichkeit zur Themenbeschreibung (klar rein / klar raus). Stufe 2: Grauzone per lokalem LLM mit Few-Shot-Beispielen. Stufe 3: unsicher → Haiku |
| Extraktion | Extraktor | Sonnet | Strukturierte Ausgabe per JSON-Schema (Tool Use), Ontologie per Prompt-Caching, Begriffsabgleich gemäß Kap. 7 |
| Prüfung | Prüfer | Claude (eigener Prompt) | Stichprobe (Start: 20 %, später 5–10 %): Stimmen Entitäten und Beziehungen mit dem Originaltext überein? Urteil `pass`/`fail` mit Begründung |
| Orchestrierung | – | Code | Routing-Tabelle und Eskalationsregeln (unten) |

**Routing- und Eskalationsregeln (Startwerte, in `config.yaml`):**
- Scout unsicher (Score in Grauzone) → lokales LLM; weiterhin unsicher → Haiku.
- Extraktor liefert ungültiges JSON → 1 Wiederholung; danach stärkeres Modell; danach `needs_human`.
- Prüfer `fail` → 1 Neuextraktion mit Prüferhinweis; erneut `fail` → `needs_human`.
- Budget-Grenze je Lauf (Tokens bzw. Euro) → Lauf pausiert automatisch.

## 8a. Modelle und Anbieter

### Lokale Modelle (Ollama)
| Zweck | Anforderung | Auswahlverfahren |
|---|---|---|
| Embedding | mehrsprachig DE/EN, gute Retrieval-Qualität | Kandidat `bge-m3`; Test in Schritt 1.3 mit 20 Suchanfragen |
| Scout (Grauzone) | kleines Instruct-Modell, passt in RAM/GPU, verlässliche Klassifikation | 2–3 Kandidaten an 50 von Mirko gelabelten Chunks vergleichen (Schritt 1.6b); Kriterien: Trefferquote, Geschwindigkeit, Formattreue |

Modelle werden per `ollama pull` geladen; Namen stehen ausschließlich in `config.yaml`.

### Anbieter-Mix Claude / OpenAI
- Alle LLM-Aufrufe laufen über eine dünne **Provider-Abstraktion** (`src/kg/llm/`) mit einheitlicher Schnittstelle: Prompt + Pydantic-Schema rein, validiertes Objekt plus Token-Verbrauch raus.
- Adapter: `anthropic` (Tool Use für strukturierte Ausgabe), `openai` (Structured Outputs), `ollama` (lokal).
- Anbieter und Modell werden **je Agent** in `config.yaml` gewählt, z. B.:

```yaml
agents:
  scout:      { provider: ollama,    model: <lokales-modell>, escalate_to: { provider: anthropic, model: <haiku> } }
  extractor:  { provider: anthropic, model: <sonnet> }
  reviewer:   { provider: openai,    model: <aktuelles-modell> }   # bewusst anderer Anbieter
  resolver:   { provider: anthropic, model: <sonnet> }
```

- **Empfehlung:** Prüfer von einem anderen Anbieter als der Extraktor. Unterschiedliche Modelle machen unterschiedliche Fehler – das ist ein echtes Vier-Augen-Prinzip.
- Jeder `Run`-Knoten speichert Anbieter und Modell; Kosten werden je Anbieter ausgewiesen.
- Prompts liegen anbieterneutral unter `prompts/`; nur wenn nötig gibt es anbieterspezifische Varianten.
- Zwei API-Schlüssel in `.env` (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`); OpenAI ist optional, das System läuft auch nur mit Claude.

**CLI (Arbeitsname `kg`):**

```
kg init                          # Indizes, Constraints anlegen
kg ingest [--path ...]           # Dokumente einlesen und chunken
kg embed                         # fehlende Embeddings berechnen
kg topic add iam --file topics/iam.yaml
kg scout --topic iam
kg extract --topic iam --batch 30 [--dry-run]
kg qa --topic iam --sample 0.2
kg review                        # needs_human-Fälle anzeigen
kg status [--topic iam]          # Fortschritt, Kosten
```

Jeder Befehl ist fortsetzbar und darf jederzeit abgebrochen werden.

## 9. Zugriff für Claude (MCP)

- **Eigener MCP-Server `kg.mcp_server`** (STDIO, eingebunden über `.mcp.json`) statt des offiziellen Neo4j-MCP. Gründe: Der offizielle Server kann Anfragen nicht in Vektoren umrechnen (keine semantische Suche), die Zugangsdaten würden in der Konfiguration stehen, und eine Schreibsperre ließe sich nur per Einstellung statt technisch erzwingen. Der eigene Server liest die `.env` selbst und führt Cypher nur in Lesetransaktionen aus.
Vergleich mit den fertigen Servern (offiziell, Labs, `mcp-neo4j-graphrag`): `docs/mcp-vergleich.md`.
- **Werkzeuge:** `search_chunks` (Hybridsuche: Vektor für mehrere Formulierungen plus Stichwortsuche, fusioniert per Reciprocal Rank Fusion), `get_chunk_context` (Nachbar-Chunks), `get_schema`, `read_cypher`.
- **Mehrsprachigkeit:** Die Vektorsuche trifft englische Texte mit englischen Anfragen deutlich besser (Schritt 1.3). Claude übersetzt deutsche Fragen deshalb in 2–4 englische Formulierungen und gibt feste Begriffe als Stichwörter mit. Das steht auch in den Anweisungen des Servers.
- **Volltextindex** `chunk_fulltext` (Chunktext und Kapitelpfad) ergänzt den Vektorindex und ist über Cypher abfragbar.
- **Standard: lesend.** Neo4j Community kennt keine feingranularen Rollen; der Lesemodus wird daher über die Konfiguration des MCP-Servers erzwungen (nur Lese-Tools freigeben).
- Schreibender Zugriff nur bewusst für Kuratierung (z. B. Ontologie-Korrekturen, Entscheidungen als Knoten), getrennt konfiguriert.
- Typische Abfragen: „Welche Quellen stützen JIT-Access und wie mappt das auf NIST AAL2?“ – mit Rückverweis auf Dokument und Seite.

## 10. Umsetzungsplan Phase 1 (für Claude Code)

Jeder Schritt endet erst, wenn das Abnahmekriterium erfüllt ist. **Status:** `[x]` erledigt und abgenommen, `[~]` in Arbeit, `[ ]` offen; wird nach jedem Schritt zusammen mit „Aktueller Stand“ in `CLAUDE.md` nachgezogen. Nach jedem Schritt wird `CLAUDE.md` (Abschnitt „Aktueller Stand“) aktualisiert **und ein Eintrag im Erfahrungsprotokoll angelegt** (Kapitel 10a).

| Status | Schritt | Inhalt | Abnahmekriterium |
|---|---|---|---|
| [x] | 1.0a | Hardware ausmessen: GPU-Typ, VRAM, Treiber, RAM, freier Speicher; GPU-Zugriff für Docker prüfen (bei NVIDIA: aktueller Treiber, Docker Desktop mit GPU-Unterstützung bzw. NVIDIA Container Toolkit) | Hardware-Steckbrief in `docs/hardware.md`; Testcontainer sieht die GPU |
| [x] | 1.0 | Repository-Struktur, `.env.example`, `.gitignore`, `docker-compose.yml` (mit GPU-Freigabe für Ollama), `config.yaml`; Embedding-Modell per `ollama pull` laden | `docker compose up` startet Neo4j und Ollama; Neo4j-Browser unter `localhost:7474` erreichbar; Ollama antwortet auf Testanfrage und nutzt die GPU |
| [x] | 1.1 | Python-Paket `kg`, `kg init` | Constraints und Vektorindex in Neo4j vorhanden |
| [x] | 1.2 | Ingestion und Chunking, Test mit **dem IAM-Buch** | Chunks mit korrekten Seitenzahlen; Stichprobe von 5 Chunks gegen PDF geprüft |
| [x] | 1.3 | Embedding über Ollama | Semantische Testabfrage („Rezertifizierung“) findet passende Chunks, auch englische |
| [x] | 1.4 | Spike Graph-Builder-Kompatibilität (optional starten) | Graph Builder zeigt das IAM-Buch mit Chunks an |
| [x] | 1.5 | Eigener lesender MCP-Server `kg.mcp_server` (Hybridsuche, Kontext, Cypher) mit Volltextindex, Einbindung über `.mcp.json` in Claude Code | Claude Code beantwortet eine deutsche Frage aus dem Graphen mit Seitenangabe; Schreibzugriff ist technisch ausgeschlossen |
| [ ] | 1.6 | Ingestion und Embedding der gesamten Bibliothek | Alle Dokumente erfasst; Bericht über gescannte/fehlerhafte PDFs |
| [~] | 1.6-OCR | OCR für Seiten ohne Textlayer (Tesseract, `ocr:` in `config.yaml`), Gütewert je Dokument | IAM-Buch: 199 von 200 Bildseiten mit Text im Graphen, Qualitätsscore je Dokument und Seite, Stichprobe gegen PDF geprüft |
| [ ] | 1.6c | Abbildungen beschreiben (Vorschlag, Kap. 14 Nr. 6): Vision-Modell mit Kontext, Beschreibung als durchsuchbarer Chunk | Probelauf an Figur 2.1 und 3.5 des IAM-Buchs, Stichprobe durch Mirko, Kosten hochgerechnet |
| [ ] | 1.6a | Ontologie v0.1 erstellen nach Kap. 7.0 (O1–O6) | Kompetenzfragen, `ontology/iam.yaml` mit Definitionen und Beispielen; Probeextraktion von 2–3 Seiten beantwortet mindestens die Hälfte der Kompetenzfragen |
| [ ] | 1.6b | Provider-Abstraktion `src/kg/llm/` und Auswahl des lokalen Scout-Modells | Alle Adapter mit Testaufruf; Vergleich von 2–3 Scout-Kandidaten an 50 gelabelten Chunks dokumentiert |
| [ ] | 1.7 | Thema IAM anlegen, Scout | IAM-Chunks markiert; Stichprobe von 30 Zuordnungen durch Mirko geprüft |
| [ ] | 1.8 | Extraktor und Prüfer, **Probelauf mit einem Kapitel** | Prüferquote und manuelle Sichtung zufriedenstellend; Ontologie ggf. auf v0.2 |
| [ ] | 1.9 | Batch-Extraktion IAM | Alle IAM-WorkItems `done` oder `needs_human`; Kostenbericht |
| [ ] | 1.10 | Erfahrungsprotokoll auswerten, Runbook „Neues Thema“ und Themenvorlage ableiten | Ein zweites Thema ließe sich allein mit Runbook und Vorlage starten; Meilenstein „Prozess stabil“ erreicht |

## 10a. Erfahrungsprotokoll

Ziel: Alles, was beim IAM-Piloten gelernt wird, so festhalten, dass daraus später Runbook, Skill „Neues Thema“ und die UI-Masken entstehen.

**Ablage:** `docs/erfahrungen.md` (chronologisch) plus `topics/_vorlage.yaml` (wird mit jedem Schritt verfeinert).

**Eintrag je Schritt (feste Struktur):**

```
## [Datum] Schritt 1.x – Titel
- Was getan:
- Was funktioniert hat:
- Probleme und Lösung:
- Entscheidungen (mit Begründung):
- Finale Parameter: (Schwellwerte, Batchgröße, Modell, Stichprobenquote)
- Aufwand: (Dauer, Tokens, Kosten)
- Was ein Nutzer bei einem neuen Thema selbst entscheiden muss:  → wird zum UI-Feld
- Was automatisch laufen kann:                                 → wird zum UI-Knopf
```

**Auswertung in Schritt 1.10:**
- Die Zeilen „selbst entscheiden“ ergeben die Eingabemasken der UI (z. B. Themenbeschreibung, Beispiele, Ontologie-Variante, Budget).
- Die Zeilen „automatisch“ ergeben die Steuerknöpfe (Scout, Extraktion, QA starten).
- Die „finalen Parameter“ werden Standardwerte in `config.yaml` und `topics/_vorlage.yaml`.
- Wiederkehrende Probleme werden zu Prüfungen im Code oder zu Hinweisen im Runbook.

## 11. Repository-Struktur

```
literatur-kg/
├── CLAUDE.md
├── KONZEPT.md
├── docker-compose.yml
├── .env.example          # NEO4J_PASSWORD, ANTHROPIC_API_KEY, OPENAI_API_KEY (optional), LIBRARY_ROOT, OLLAMA_URL
├── .gitignore            # .env, data/
├── .mcp.json
├── config.yaml           # Modelle, Schwellwerte, Batchgrößen, Budget
├── ontology/
│   └── iam.yaml
├── topics/
│   └── iam.yaml          # Beschreibung, Few-Shot-Beispiele
├── prompts/              # versionierte Prompts: scout, extract, qa, resolve
├── src/kg/
│   ├── cli.py
│   ├── ingest/  chunking/  embed/
│   ├── llm/     (base.py, anthropic.py, openai.py, ollama.py)
│   ├── agents/  (scout.py, extractor.py, reviewer.py, resolver.py)
│   ├── orchestrator.py
│   └── graph/   (schema.py, queries.py)
├── tests/
├── docs/
│   ├── erfahrungen.md    # Erfahrungsprotokoll (Kap. 10a)
│   └── runbook.md
└── data/                 # Docker-Volumes, nicht im Git
```

## 12. Sicherheit und Betrieb

- API-Schlüssel und Passwörter ausschließlich in `.env`, nie im Git.
- Ports nur lokal; kein Zugriff von außen in Phase 1.
- Regelmäßige Sicherung: `neo4j-admin database dump` (Container kurz stoppen) auf das NAS.
- Kostenkontrolle: Token-Zählung je Lauf, Budget-Grenze in `config.yaml`.
- Keine Mandantendaten im System.

## 13. Ausblick Phase 3: Arbeitsrechner ohne Docker

- **Infrastruktur nativ:** Neo4j (Desktop oder Server-Installation als Dienst), Ollama per Installer, gleiche Python-Pipeline in venv.
- **Übertragung ohne Neuaufbau:** Datenbank-Dump vom Heimrechner (`neo4j-admin database dump`) und auf dem Arbeitsrechner laden (`load`), bei gleicher Neo4j-Hauptversion. Weil `doc_id` aus dem Datei-Hash entsteht und Pfade relativ gespeichert sind, genügt das Setzen von `LIBRARY_ROOT`.
- **Embeddings wandern mit,** aber für neue Suchen muss dasselbe Embedding-Modell verwendet werden.
- **Abgleich bei neuen Dokumenten:** `kg ingest` erkennt per Hash, was bereits vorhanden ist.
- **Vorab klären:** interne Vorgaben zur Nutzung der Claude-API auf dem Arbeitsrechner; ggf. Extraktion nur zu Hause, Arbeitsrechner nur lesend.

## 14. Offene Entscheidungen

1. ~~Betriebssystem des Heimrechners sowie GPU-Typ und VRAM.~~ Geklärt in Schritt 1.0a: Windows 11 Pro, GeForce GTX 1650 mit 4 GB VRAM, siehe `docs/hardware.md`.
2. Finales Embedding-Modell: `bge-m3` ist gesetzt. In Schritt 1.3 war die Suche mit englischen Anfragen gut (Precision@5 0,72), mit deutschen schwächer (0,42) auf dem rein englischen IAM-Buch. Endgültig entscheiden nach Schritt 1.6 mit deutschen Dokumenten (`scripts/eval_embedding.py` erneut laufen lassen).
3. Graph Builder in Phase 1 nutzen oder erst nach Schritt 1.9.
4. Budgetrahmen für die IAM-Extraktion.
5. OpenAI zusätzlich nutzen (Empfehlung: für den Prüfer) oder zunächst nur Claude.
6. Abbildungen auswerten (Vorschlag vom 01.11.2026, von Mirko mitgetragen, Umsetzung als Schritt 1.6c):
   - **Eingabe je Abbildung:** Seitenbild (bei Bedarf zugeschnitten), Bildunterschrift mit Figurennummer, Abschnittspfad und gedruckte Seite, Text vor und nach der Abbildung, bereits extrahierter Text aus dem Bild.
   - **Ausgabe:** strukturiert, nicht frei: Typ (Konzeptbild, Prozess, Architektur, Tabelle, Kurve, Screenshot), Thema, Aussage in 1–3 Sätzen, Elemente und Beziehungen, `confidence`, Belegzitat aus der Unterschrift.
   - **Annahme von Mirko:** Im Fließtext der Artikel und Bücher gibt es fast immer einen Verweis auf die Abbildung oder eine Beschreibung ihres Inhalts. Dieser Text trägt die Beschreibung; das Bild ergänzt sie.
   - **Qualitätsscore:** Liefert der umgebende Text zu wenig (kein Verweis, keine Unterschrift, kaum Bildtext), sinkt der Score; die Beschreibung wird als unsicher markiert und für die Stichprobe vorgemerkt.
   - **Speicherung:** Knoten `Figure` (verbunden mit `Document` und dem benachbarten `Chunk`; Seite, Figurennummer, Typ, Score) und die Beschreibung als durchsuchbarer Chunk mit Embedding. Neuer Knotentyp: erst nach Mirkos Freigabe der Ontologie.
   - **Vorgaben:** Prompt versioniert unter `prompts/`, Modell nur in `config.yaml`, Provenance (`run_id`, `confidence`), vor dem Massenlauf `--dry-run` und Kostenhochrechnung; nur Seiten mit Abbildungen verarbeiten.
