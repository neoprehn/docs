# Erfahrungsprotokoll

Chronologisch, Struktur gemäß KONZEPT.md Kap. 10a.

## [31.10.2026] Schritt 1.0a – Hardware ausmessen

- Was getan: Hardware und Docker erfasst, GPU-Zugriff im Container getestet, Metadaten der möglichen Literaturordner ausgewertet. Steckbrief in `docs/hardware.md`.
- Was funktioniert hat: Der Container sieht die GPU ohne weitere Einrichtung; Docker Desktop bringt die NVIDIA-Runtime mit.
- Probleme und Lösung: Die Bibliothek weicht vom Konzept ab. Statt rund 500 Dokumenten liegen 1.541 PDF in `Literatur` und 216 PDF in `Bücher`, zusammen 9,5 GB. `Normen` enthält weitere 28.489 PDF (28,2 GB). 1.710 der 1.757 PDF aus `Literatur` und `Bücher` sind nur in der Cloud vorhanden, Annahme A3 ist also noch nicht erfüllt. Bis zur Klärung bleibt `LIBRARY_ROOT` leer.
- Entscheidungen (mit Begründung): Keine. Umfang der Bibliothek und `LIBRARY_ROOT` entscheidet Mirko.
- Finale Parameter: GPU GTX 1650 mit 4 GB VRAM.
- Aufwand: wenige Minuten, keine API-Kosten.
- Was ein Nutzer bei einem neuen Thema selbst entscheiden muss: Bei einem neuen Thema nichts; die Hardware wird einmal je Rechner erfasst.
- Was automatisch laufen kann: Hardware-Erfassung, GPU-Test, Zählung von Dokumenten und reinen Cloud-Dateien.

## [31.10.2026] Schritt 1.0 – Repository und Infrastruktur

- Was getan: Git-Repository mit `neoprehn/neolibris` verbunden (privat), `new_chat_rule.md`, `.env.example`, `.env`, `.gitignore`, `docker-compose.yml`, `config.yaml` und `topics/_vorlage.yaml` angelegt, Neo4j und Ollama gestartet, `bge-m3` geladen.
- Was funktioniert hat: `docker compose up` startet beide Dienste gesund. Neo4j-Browser antwortet unter `localhost:17474`, APOC 5.26.32 ist aktiv. Ollama liefert 1.024-dimensionale Embeddings zu 100 % auf der GPU. Stichprobe: „Rezertifizierung von Zugriffsrechten“ zu „access recertification campaign“ 0,71, zu „Rezept für Apfelkuchen“ 0,29.
- Probleme und Lösung: Die Konzept-Ports 7474 und 7687 belegt `iam-neo4j`, daher 17474 und 17687 sowie `server.bolt.advertised_address` passend gesetzt. Die Abnahme „Browser unter 7474“ gilt entsprechend für 17474.
- Entscheidungen (mit Begründung):
  - Benannte Volumes für Neo4j-Store und Ollama-Modelle statt Bind-Mounts: Ein Store auf einem Windows-Laufwerk ist in der Docker-VM langsam und anfällig; `iam` macht es aus demselben Grund so. Logs und Import bleiben unter `data/`. Die Sicherung läuft ohnehin über `neo4j-admin database dump`.
  - Neo4j 5.26.32 (LTS) statt 2026.10: bewährt auf diesem Rechner durch `iam`, Image bereits vorhanden. In Phase 3 muss der Arbeitsrechner dieselbe Hauptversion nutzen.
  - `reviewer` zunächst auf Claude, bis Kap. 14 Nr. 5 entschieden ist.
  - `src/kg/`, `.mcp.json` und `ontology/iam.yaml` bewusst noch nicht angelegt; sie gehören zu den Schritten 1.1, 1.5 und 1.6a.
- Finale Parameter: Neo4j-Heap 4 GB, Pagecache 2 GB, Embedding `bge-m3`, Dimension 1.024, `num_ctx` 4.096 (Ollama-Standard bei 4 GB VRAM).
- Aufwand: eine Sitzung, keine API-Kosten.
- Was ein Nutzer bei einem neuen Thema selbst entscheiden muss: Bei einem neuen Thema nichts; die Infrastruktur ist themenneutral. Je Rechner: `LIBRARY_ROOT` und API-Schlüssel.
- Was automatisch laufen kann: Start der Dienste, Laden der Modelle, Gesundheitsprüfung.

## [31.10.2026] Schritt 1.1 – Python-Paket `kg`, `kg init`

- Was getan: Paket `kg` unter `src/kg/` mit CLI (`typer`), Konfigurations-Loader für `config.yaml` und `.env` und `kg init`. Es legt Constraints für `doc_id`, `chunk_id`, `topic_id`, `item_id`, `run_id` und `entity_id` an, Indizes auf `sha256`, `rel_path` und die Arbeitswarteschlange sowie den Vektorindex `chunk_embedding`.
- Was funktioniert hat: Alle Abhängigkeiten gibt es als fertige Wheels für Python 3.14, eine ältere Version war nicht nötig. `kg init` lief zweimal ohne Änderung, `--dry-run` zeigt die Statements an. Drei Tests bestanden, davon ein Integrationstest gegen Neo4j.
- Probleme und Lösung:
  - Typer macht aus einem einzelnen Befehl den Hauptbefehl, `kg init` wurde nicht erkannt. Ein `@app.callback()` erzwingt die Befehlsstruktur, die mit den weiteren Befehlen ohnehin kommt.
  - Neo4j 5.26 legt Vektorindizes standardmäßig mit Quantisierung an. Für die erwartete Größe unkritisch, ein Wechsel von Modell oder Dimension erzwingt aber einen neuen Index. `kg init` bricht in dem Fall ab, statt still einen falschen Index zu behalten.
- Entscheidungen (mit Begründung):
  - `entity_id` bekommt schon jetzt eine Eindeutigkeitsbedingung, weil Ergänzung 01 stabile Entitäts-IDs verlangt. Später wäre sie nur mit Aufwand nachzurüsten.
  - Die Pakete `anthropic` und `openai` kommen erst in Schritt 1.6b dazu, `pymupdf` in 1.2.
  - Cosine-Ähnlichkeit, da `bge-m3` darauf trainiert ist.
- Finale Parameter: Vektorindex 1.024 Dimensionen, cosine, HNSW `m` 16 und `ef_construction` 100 (Neo4j-Standard).
- Aufwand: eine Sitzung, keine API-Kosten.
- Was ein Nutzer bei einem neuen Thema selbst entscheiden muss: Nichts; das Schema ist themenneutral und wird einmal je Datenbank angelegt.
- Was automatisch laufen kann: `kg init`, bei Bedarf als Teil jedes Starts.

## [31.10.2026] Schritt 1.2 – Ingestion und Chunking (IAM-Buch)

- Was getan: `kg ingest` liest PDFs mit `pymupdf`, bildet `doc_id` als SHA-256 des Inhalts, speichert den Pfad relativ zu `LIBRARY_ROOT`, zerlegt den Text in Chunks (ca. 800 Tokens, 100 Überlappung, keine Chunks über Kapitelgrenzen) und schreibt `Document`, `Chunk`, `PART_OF`, `NEXT_CHUNK` und `FIRST_CHUNK` nach Neo4j. Getestet mit `Bücher/Identity and Access Management.pdf`: 649 Seiten, 352 Chunks, rund 213.000 Tokens (genähert).
- Was funktioniert hat:
  - Zweiter Lauf erfasst nichts neu, ohne die Datei zu öffnen. `--dry-run` zeigt Seiten, Chunks und Textlayer-Befund ohne zu schreiben.
  - `doc_id` stimmt mit einer unabhängigen SHA-256-Berechnung überein.
  - Abnahme übererfüllt: Statt 5 Chunks habe ich alle 352 gegen das PDF geprüft (Wortabdeckung auf dem angegebenen Seitenbereich). 351 liegen bei mindestens 95 %, einer bei 94 %. Gedruckte Seitenzahlen (`page_label_start/end`) stehen zusätzlich zum PDF-Seitenindex am Chunk, weil beide nach vorn verschoben sind (PDF-Seite 100 ist Buchseite 69).
- Probleme und Lösung:
  - **200 von 649 Seiten haben keinen Textlayer** (31 %), in zusammenhängenden Blöcken mitten im Buch. Es sind keine Leerseiten, sondern gescannte Anhänge (z. B. der Implementierungsleitfaden zum Access Review and Certification Tool). Sie werden erkannt, in `pages_without_text` am Dokument vermerkt und im Lauf gemeldet, aber nicht übersprungen oder verworfen. `has_text_layer` ist nur bei mehr als 50 % Textseiten wahr, hier also wahr, obwohl ein Drittel fehlt. Wer Lücken sucht, muss `pages_without_text` prüfen.
  - Laufköpfe standen im Text, weil der Randfilter bei 5 % der Seitenhöhe zu eng war (Köpfe liegen bei 5–6,4 %). Mit 8 % und Ausnahme für Abbildungs- und Tabellenunterschriften sind sie weg.
  - Punktlinien im Inhaltsverzeichnis („Sensors…… 59“) kosten Tokens ohne Inhalt und werden auf „…“ gekürzt.
  - Meine erste Stichprobenprüfung mit 70 Zeichen am Stück schlug fehl, weil der Chunk Textblöcke in Leserichtung ordnet und die einfache Seitenextraktion nicht. Verlässlicher ist der Vergleich über Wörter, nicht über Zeichenfolgen.
- Entscheidungen (mit Begründung):
  - `ingest_status` (`ingesting`, `complete`, `failed`) am Dokument: Nur `complete` wird übersprungen, ein abgebrochener Lauf setzt sauber fort, fehlerhafte Dateien werden mit Fehlertext vermerkt und beim nächsten Lauf erneut versucht.
  - Tokens werden über 4 Zeichen je Token genähert (`config.yaml`), eine echte Tokenisierung ist für die Chunkgröße nicht nötig.
  - Der Abschnittspfad kommt aus dem PDF-Inhaltsverzeichnis (hier 305 Einträge) und gilt seitenweise. Beginnt auf einer Seite ein neuer Abschnitt, gilt der neue Pfad für die ganze Seite. Fehlt ein Inhaltsverzeichnis, bleibt der Pfad leer.
  - Chunkanfänge können auf der Seite davor liegen, weil die Überlappung mitzählt. `page_start` gibt deshalb die früheste Seite mit Text des Chunks an.
- Finale Parameter: 800 Tokens, 100 Überlappung, 4 Zeichen je Token, Randfilter 8 % bei höchstens 100 Zeichen, Textlayer ab 50 % Textseiten, mindestens 30 Zeichen je Chunk.
- Aufwand: eine Sitzung, keine API-Kosten.
- Was ein Nutzer bei einem neuen Thema selbst entscheiden muss: Nichts; die Ingestion ist themenneutral. Je Bibliothek: welche Ordner einbezogen werden und wie mit gescannten Seiten umgegangen wird (überspringen oder OCR).
- Was automatisch laufen kann: Einlesen neuer Dokumente (erkannt per Hash), Textlayer-Prüfung, Fehlerbericht.

## [31.10.2026] Schritt 1.3 – Embedding über Ollama

- Was getan: `kg embed` berechnet fehlende Embeddings mit `bge-m3` in Batches von 32 und speichert sie am Chunk (`embedding`, `embedding_model`). `kg search` fragt den Vektorindex ab. Alle 352 Chunks des IAM-Buchs sind eingebettet.
- Was funktioniert hat: Der Lauf ist fortsetzbar und verarbeitet nur Chunks ohne Embedding zum konfigurierten Modell, ein Modellwechsel würde also automatisch alles neu einbetten. Durchsatz 1,3 s je Chunk auf der GTX 1650. Englische Anfragen liefern sauber das Kapitel „Access Review and Certification“ (Buchseiten 437–458).
- Probleme und Lösung:
  - Einzelne deutsche Wörter wie „Rezertifizierung“ treffen weniger sicher: Die richtige Stelle liegt auf Platz 2 und 4, dazwischen drängeln sich Tabellen des Credential-Reifegradmodells. Ursache ist vermutlich eine schwächere sprachübergreifende Suche, bei Fachbegriffen mit deutscher Zusammensetzung („Funktionstrennung“, „Verzeichnisdienst“) bleiben die Treffer im Test ganz aus.
  - Der erste Test mit 4 Anfragen reichte nicht für eine Entscheidung. Deshalb Test mit 20 Anfragen (10 Themen, je Deutsch und Englisch) in `scripts/eval_embedding.py`.
- Entscheidungen (mit Begründung):
  - `bge-m3` bleibt. Es ist das einzige Kandidatenmodell, ein Vergleich mit anderen lohnt erst mit deutschen Dokumenten (Schritt 1.6), weil das IAM-Buch rein englisch ist und deutsche Anfragen hier sprachübergreifend suchen müssen.
  - Der Kapitelpfad bleibt dem Text vorangestellt (`include_heading`): Der Test zeigt keinen Unterschied (Precision@5 Deutsch 0,44 mit gegenüber 0,42 ohne, Englisch 0,68 gegenüber 0,72). Ein Neuaufbau brächte nichts.
  - Abnahme „Rezertifizierung findet passende Chunks, auch englische“: knapp erfüllt. Die Abnahme wurde bewusst am englischen Buch geprüft, die Schwäche bei deutschen Anfragen ist die offene Folgefrage.
- Finale Parameter: Modell `bge-m3`, 1.024 Dimensionen, Batch 32, Kapitelpfad im Embedding. Precision@5 (grobe Stichwortdefinition, Untergrenze): Englisch 0,72, Deutsch 0,42.
- Aufwand: 7 Minuten Rechenzeit für das Buch, keine API-Kosten.
- Was ein Nutzer bei einem neuen Thema selbst entscheiden muss: Sprache der Themenbeschreibung und der Beispiele. Bei überwiegend englischer Literatur englisch oder zweisprachig formulieren, sonst findet die Vorfilterung des Scouts weniger.
- Was automatisch laufen kann: `kg embed` für alle neuen Chunks, Wiederaufnahme nach Abbruch.

## [31.10.2026] Schritt 1.5 – Lesender MCP-Server und Hybridsuche (in Arbeit)

- Was getan: Volltextindex `chunk_fulltext` in `kg init`, `kg/search.py` (Vektorsuche je Formulierung plus Stichwortsuche, Rangfusion per RRF), `kg/mcp_server.py` mit `search_chunks`, `get_chunk_context`, `get_schema`, `read_cypher`, `.mcp.json` und Vorlage `docs/mcp-vorlage.json` für Folgeprojekte. `kg search` nutzt jetzt dieselbe Hybridsuche.
- Was funktioniert hat: Als echter MCP-Client getestet. Eine deutsche Frage zur Rezertifizierung, ergänzt um englische Formulierungen und Stichwörter, liefert als Erstes Buchseite 437 (Kapitelanfang „Access Review and Certification“), dann 458–460 und 457. Ein Schreibversuch über `read_cypher` wird abgelehnt, es entsteht kein Knoten.
- Probleme und Lösung:
  - Die MCP-Bibliothek ist in Version 2 umgebaut (`MCPServer` statt `FastMCP`); die Schnittstelle habe ich im installierten Paket nachgesehen statt zu raten.
  - Deutsche Anfragen ohne Hilfe treffen falsch: „Funktionstrennung“ landet bei „Functional Roles“, weil „Funktions…“ ähnlich klingt. Mit Übersetzung und Stichwörtern kommen die Regeln und Einschränkungen von Rollen. Das Buch behandelt „Segregation of Duties“ nur knapp (7 Chunks), der Befund liegt also auch am Inhalt.
  - Der Treffer „Bibliography“ bei der Stichwortsuche ist Rauschen: Literaturverzeichnisse und Inhaltsverzeichnisse sollten später gefiltert oder abgewertet werden.
- Entscheidungen (mit Begründung):
  - Eigener Server statt des offiziellen Neo4j-MCP: kann Anfragen einbetten, hält Zugangsdaten aus der Konfiguration heraus, Schreibsperre ist technisch erzwungen. Folge: Wir pflegen ihn selbst, ein Folgeprojekt braucht dazu den Pfad zur venv von neolibris.
  - Volltextanalyse ohne Stoppwörter und Stemming (`standard-no-stop-words`), weil die Literatur zweisprachig ist. Wer „provision“ und „provisioning“ finden will, nutzt `provision*`.
  - Die Übersetzung deutscher Fragen übernimmt Claude, nicht der Server: keine Zusatzkosten, keine zweite Modellstufe, und Claude kennt die Absicht der Frage.
- Finale Parameter: RRF-Konstante 60, je Quelle 30 Kandidaten, höchstens 25 Treffer, Textauszug 1.500 Zeichen, höchstens 200 Zeilen bei `read_cypher`.
- Aufwand: eine Sitzung, keine API-Kosten.
- Was ein Nutzer bei einem neuen Thema selbst entscheiden muss: Nichts; der Server ist themenneutral.
- Was automatisch laufen kann: Suche, Kontextabruf und Abfragen durch Claude; die Freigabe der `.mcp.json` je Projekt erteilt der Nutzer einmal.

## [31.10.2026] Schritt 1.4 – Spike Graph-Builder-Kompatibilität

- Was getan: Graph Builder (Neo4j Labs, Commit `a728de6`) lokal gebaut und mit unserem Neo4j verbunden, Details in `docs/graph-builder.md`. Vorher Sicherung mit `neo4j-admin database dump` (6 MB), damit auch das Verfahren aus Kap. 12 einmal erprobt ist. Befehl `kg graphbuilder-prepare` ergänzt die Eigenschaften, die er erwartet.
- Was funktioniert hat: Beziehungsmodell passt, nur Eigenschaftsnamen wichen ab (`fileName`, `status`, `Chunk.id`, `page_number`). Backend listet das IAM-Buch mit 352 Chunks; die Chunk-Ansicht liefert 1 Dokument, 50 Chunks und 58 Beziehungen. Das Verbinden verändert unsere Datenbank nicht (keine neuen Indizes, Embeddings unverändert). Befehl ist wiederholbar.
- Probleme und Lösung:
  - Die Standardports 8000 und 8080 sind auf diesem Rechner belegt (`iam-backend`, `bio-verwaltung`), und das mitgelieferte Compose bindet an alle Adressen. Eigene Compose-Datei mit 18000/18080 an `127.0.0.1`, gebaut aus dem Klon, ohne ihn zu ändern.
  - Der Graph Builder schlüsselt Dokumente nach `fileName`. Dateinamen allein wären in der Bibliothek nicht eindeutig, daher `fileName = rel_path`.
  - Er verbindet mit denselben Zugangsdaten und hat damit Schreibrechte (`write_access: true`). Neo4j Community hat keine eingeschränkten Benutzer. Gegenmaßnahme: nur bei Bedarf starten, Sicherung, Hinweis in der Doku.
- Entscheidungen (mit Begründung):
  - Angleichung als eigener Befehl statt im Ingest: Unser Modell bleibt unabhängig vom Graph Builder, falls er später entfällt. Entscheidung über Dauerbetrieb bleibt bei Kap. 14 Nr. 3.
  - Dem Backend keine LLM-Schlüssel mitgegeben: Er soll nur anzeigen.
  - `page_number` im Graph Builder ist die PDF-Seite, nicht die gedruckte Buchseite.
- Finale Parameter: Ports 18080 (Oberfläche) und 18000 (Backend), nur `127.0.0.1`, 2 Worker.
- Aufwand: eine Sitzung, Image-Build rund 15 Minuten, keine API-Kosten.
- Was ein Nutzer bei einem neuen Thema selbst entscheiden muss: Nichts; der Graph Builder ist themenneutral.
- Was automatisch laufen kann: Start und Stopp der Dienste, Setzen der Zusatzeigenschaften nach jedem Ingest.
- Abnahme: Mirko hat die Oberfläche geprüft. „Generated Graph“ zeigt das Buch mit 50 Chunks je Ansicht, verbunden über `PART_OF`, dazwischen die `NEXT_CHUNK`-Kette. Die Knoten sind mit dem relativen Pfad beschriftet, der in der Ansicht abgeschnitten wird.

## [01.11.2026] Schritt 1.5 – Abnahme und Doku-Veröffentlichung

- Was getan: Abnahme von Schritt 1.5 in einer frischen Claude-Code-Sitzung; `.mcp.json` freigegeben, Server `neolibris` steht unter „Project“ auf „Connected“. Außerdem die Doku über ein öffentliches Doku-Repo auf Read the Docs veröffentlicht.
- Was funktioniert hat: `search_chunks` mit übersetzten Formulierungen und Stichwörtern („segregation of duties“, „SoD“) liefert die einschlägigen Chunks des IAM-Buchs mit Titel und gedruckter Seite (S. 489–494, 516–517). Ein Schreibversuch über `read_cypher` (`CREATE`) wird abgelehnt, danach existiert kein Testknoten.
- Probleme und Lösung:
  - Read the Docs (Community) kann nicht aus privaten Repos bauen; der Build bricht nach 2 s mit „Unknown problem“ ab. Lösung wie bei IAM: GitHub Action spiegelt den Doku-Stand nach `neoprehn/docs` (Ordner `neolibris/`), dort baut RTD mit Konfigurationspfad `neolibris`.
  - RTD löst Pfade in der Konfigurationsdatei relativ zum Repo-Root auf; der Workflow schreibt sie deshalb auf `neolibris/…` um. `KONZEPT.md` liegt außerhalb von `docs/` und wird beim Spiegeln als `docs/konzept.md` eingesetzt, weil das Elternverzeichnis im Doku-Repo fehlt.
  - Das Secret `DOCS_MIRROR_TOKEN` gilt je Repo und muss in jedem spiegelnden Repo neu eingetragen werden.
- Entscheidungen (mit Begründung): Spiegel-Repo statt Veröffentlichung des Code-Repos, damit Quellcode und Verlauf privat bleiben; es wird nur der aktuelle Snapshot der Doku kopiert.
- Aufwand: eine Sitzung, keine API-Kosten.
- Was ein Nutzer bei einem neuen Thema selbst entscheiden muss: Welche Dokumente öffentlich sein dürfen (der Spiegel veröffentlicht alles unter `docs/`, auch `mcp-vorlage.json` mit lokalem Pfad); Ablaufdatum des Tokens im Blick behalten.
- Was automatisch laufen kann: Spiegeln bei jedem Push auf `main`, Bauen auf Read the Docs.

## [01.11.2026] Schritt 1.6-OCR – Texterkennung für Bildseiten

- Was getan: Seiten ohne Textlayer werden beim Einlesen per OCR gelesen (`ocr:` in `config.yaml`, Code in `src/kg/ingest/reader.py`). Tesseract 5.4 per `winget install UB-Mannheim.TesseractOCR`; die Sprachdaten `deu`, `eng`, `osd` liegen in `.tessdata/` (nicht im Git). PyMuPDF bringt die Erkennung selbst mit und braucht nur diesen Ordner, die Tesseract-Installation dient zusätzlich der Kommandozeile.
- Was funktioniert hat: IAM-Buch mit `--force` neu erfasst: 199 von 200 Bildseiten erhalten Text (rund 1 s je Seite bei 300 dpi), mittlere Güte 0,962, Chunks von 352 auf 461. Die Anhänge mit den Implementierungsleitfäden sind damit durchsuchbar.
- Probleme und Lösung:
  - Dokumentierte Befunde bleiben getrennt: `pages_without_text` meint weiterhin „kein Textlayer“, neu sind `pages_ocr`, `ocr_quality` und `pages_ocr_low_quality` am Dokument. So bleibt sichtbar, was gelesen und was erkannt wurde.
  - Die Güte (Anteil Buchstaben und Ziffern an allen Zeichen) ist nur ein grobes Maß: Punktlinien im Inhaltsverzeichnis erzeugen Buchstabenmüll (z. B. „sccscczscc…“), der die Güte nicht senkt. Bessere Filter sind offen.
  - Die Sprachwahl `deu+eng` gilt für alle Dokumente; eine Spracherkennung je Dokument fehlt noch.
  - `--force` löscht die Chunks samt Embeddings, die neuen Chunk-IDs verschieben sich; danach muss `kg embed` alles neu berechnen (rund 11 Minuten für 461 Chunks).
- Entscheidungen (mit Begründung): OCR läuft beim Einlesen und nicht als eigener Schritt, damit jeder Chunk dieselbe Herkunft und Seitenangabe hat; die Seitenzahlen bleiben unverändert. Abbildungen werden getrennt als Schritt 1.6c behandelt (KONZEPT.md Kap. 14 Nr. 6), weil OCR Diagramminhalt nicht versteht.
- Finale Parameter: 300 dpi, Sprachen `deu+eng`, Mindestgüte 0,6.
- Aufwand: eine Sitzung, keine API-Kosten.
- Was ein Nutzer bei einem neuen Thema selbst entscheiden muss: Ob gescannte Dokumente per OCR gelesen werden und mit welchen Sprachen; Tesseract und Sprachdaten einmal je Rechner installieren.
- Was automatisch laufen kann: Erkennung der Bildseiten, OCR, Gütewert und Bericht am Ende von `kg ingest`.


## [07.11.2026] Schritt 1.6 – Literatur einlesen (Ordner `Literatur`), Protokoll, Word/PowerPoint

- Was getan: Alle PDF in `Literatur` mit OCR eingelesen, danach Word (`.docx`) und PowerPoint (`.pptx`) als weitere Formate. Jeder Lauf schreibt ein Protokoll nach `reports/ingest-<Zeit>.md` und `.jsonl` (nicht im Git, enthält Dateinamen): Fehler, Duplikate, nicht gelesene Dateien, Seiten ohne Text, OCR mit niedriger Güte, verworfene Chunks und Randblöcke, übersprungene bekannte Dateien.
- Zahlen: PDF 1.397 neu erfasst (107.340 Chunks, 138.400 Seiten, davon 7.116 ohne Textlayer), 97 Duplikate, 0 Fehler, rund 1,5 Stunden. Office: 250 Dateien neu (23.187 Chunks), 132 Duplikate (meist .docx und PDF desselben Dokuments), 0 Fehler. Embedding: rund 1,3 s je Chunk, etwa 29 Stunden für den Rest.
- Probleme und Lösung:
  - Randfilter entfernte echten Text (Überschriften, Satzenden am Seitenrand), das zeigte erst das Protokoll. Jetzt wird ein Randblock nur entfernt, wenn er Seitenzahl oder Interpunktion ist oder sich ohne Ziffern auf mindestens `margin_min_repeats` Seiten wiederholt.
  - Dateinamen mit zerlegten Umlauten brachen die Ausgabe in der Windows-Konsole ab; Ausgabe jetzt UTF-8.
  - Ein PDF mit kaputter Schriftkodierung lieferte Zeichensalat mit NUL-Zeichen; Ollama antwortete mit 413, der ganze Embedding-Lauf brach ab. Jetzt zählen Blöcke mit NUL als nicht lesbar (OCR springt ein), NUL wird vor dem Senden entfernt, und ein defekter Chunk wird einzeln isoliert und mit `embedding_error` markiert, statt den Lauf zu beenden. Salat ohne NUL wird weiterhin nicht erkannt.
  - Eine `.pptx` war in Wirklichkeit ein PDF; das Format wird am Dateikopf erkannt, nicht an der Endung. Zwei `.docx` hatten beschädigte Bilder im Archiv; sie werden ohne diese Teile gelesen.
- Entscheidungen (mit Begründung): Word hat keine gedruckte Seite; Beleg ist Überschriftenpfad plus „Abschn. n“ (oberste Überschriftenebene mit mindestens drei Vorkommen), bei PowerPoint die Folie. Tabellen zeilenweise mit wiederholter Kopfzeile. Zu kurze Chunk-Reste werden an den vorherigen Chunk desselben Abschnitts gehängt statt verworfen. `.doc`, `.ppt` (Legacy) und Excel bleiben draußen und werden im Protokoll gezählt; Excel-Kontrollkataloge eignen sich später als Struktur (Knoten statt Text), nicht als Fließtext.
- Was ein Nutzer bei einem neuen Thema selbst entscheiden muss: Welche Dateitypen einbezogen werden (Office, Excel) und ob ein Beleg „Abschn. n“ statt Seite genügt; das Protokoll nach dem ersten Lauf ansehen, bevor der ganze Bestand läuft.
- Was automatisch laufen kann: Einlesen, OCR, Duplikaterkennung, Protokoll, Embedding (fortsetzbar).
- Offen: OCR-Salat und zerstörte Tabellen (Güte erkennt Punktlinien nicht) für Schritt 1.6c und den Prüfer (1.8); Spracherkennung je Dokument; Durchsatz des Embeddings (Batchgröße/Parallelität in Ollama nicht getestet).
