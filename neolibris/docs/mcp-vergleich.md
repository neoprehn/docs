# Vergleich: MCP-Server für den Zugriff auf den Graphen

**Stand:** 31.10.2026. Grundlage sind die Projektseiten der Server, abgerufen am selben Tag. Nicht jede Angabe
steht dort, offene Punkte sind markiert. Die Entscheidung für den eigenen Server fiel in Schritt 1.5.

## Kandidaten

| | Offizieller Neo4j MCP | `mcp-neo4j-cypher` (Neo4j Labs) | `mcp-neo4j-graphrag` | Eigener Server `kg.mcp_server` |
|---|---|---|---|---|
| Herkunft | Neo4j, `github.com/neo4j/mcp`, Version 2 | Neo4j Labs, `neo4j-contrib/mcp-neo4j`, „aktiv gepflegt, ohne Garantien“ | Einzelperson, `neo4j-field/mcp-neo4j-graphrag`, Beta, 0.4.2 (17.07.2026), 3 Sterne | dieses Repository |
| Lesen mit Cypher | ja (`read-cypher`) | ja | ja (`read_neo4j_cypher`) | ja (`read_cypher`) |
| Schema abrufen | ja (`get-schema`) | ja (braucht APOC) | ja (inkl. Indizes) | ja (`get_schema`) |
| Vektorsuche | nein | nein | ja (`vector_search`) | ja |
| Volltextsuche | nein | nein | ja (`fulltext_search`, Lucene) | ja |
| Hybrid mit Rangfusion | nein | nein | nur über eigene Cypher-Vorlage, keine Fusion beschrieben | ja (RRF, mehrere Formulierungen je Anfrage) |
| Einbettung der Anfrage | – | – | über LiteLLM, Ollama als `ollama/<Modell>` (Basis-URL nicht dokumentiert, `bge-m3` nicht erwähnt) | direkt über unser Ollama, dasselbe Modell wie bei den Chunks |
| Schreibzugriff | `write-cypher`, abschaltbar mit `NEO4J_MCP_READ_ONLY=true` | ja, Abschaltung nicht dokumentiert | `write_neo4j_cypher`, **kein** globaler Lesemodus beschrieben | gibt es nicht |
| Wie „lesend“ erzwungen wird | Prüfung per `EXPLAIN`; die Seite warnt, dass eigene Procedures fälschlich als lesend gelten können | – | nur über Werkzeugwahl | Lesetransaktion, Neo4j lehnt Schreiben ab (getestet) |
| Zugangsdaten | Umgebungsvariablen `NEO4J_MCP_*` | Umgebungsvariablen/Flags | Umgebungsvariablen `NEO4J_*` | liest `.env` selbst, nichts in `.mcp.json` |
| Ergebnisse mit Seitenzahl und Titel | nein, nur rohe Zeilen | nein | nur Knoteneigenschaften, Titel erst über zweite Abfrage | ja, in jedem Treffer |
| Wartung | Neo4j | Neo4j Labs | eine Person | wir (rund 200 Zeilen, 6 Tests zu Suche und Leser) |

Weitere Server aus dem Labs-Repository (`mcp-neo4j-memory`, `-data-modeling`, `-cloud-aura-api`) lösen andere
Aufgaben (Sitzungsgedächtnis, Datenmodellierung, Aura-Verwaltung) und kommen nicht in Frage.

## Bewertung

- Der offizielle und der Labs-Server bieten laut ihren Seiten **keine** Vektor- oder Volltextsuche. Mit ihnen
  hätte Claude nur Cypher, und die semantische Suche aus Schritt 1.3 wäre über MCP nicht erreichbar.
- `mcp-neo4j-graphrag` schließt diese Lücke, hat aber Schwächen für unseren Zweck: kein Lesemodus (das
  Schreibwerkzeug lässt sich laut Seite nicht abschalten), keine Fusion, unklare Anbindung von `bge-m3`,
  kleiner Reifegrad. Die Regel „Neolibris wird von Folgeprojekten nur gelesen“ (Ergänzung 01) wäre damit nur
  durch Disziplin, nicht technisch erfüllt.
- **Entscheidung:** Der eigene Server bleibt. Er erfüllt als Einziger Lesesperre, Hybridsuche mit demselben
  Embedding-Modell und Treffer mit Titel und Seite zugleich. Preis: Wir pflegen ihn selbst.
- **Rückweg:** Der Server ist klein und die Werkzeuge heißen wie bei den fertigen Servern ähnlich. Wird
  `mcp-neo4j-graphrag` später reifer und bekommt einen Lesemodus, ist ein Wechsel mit Anpassung von
  `.mcp.json` und den Anweisungen in `CLAUDE.md` möglich.

## Offene Punkte der Quellen

- Offizieller Server: vollständige Werkzeugliste, Transporte und unterstützte Neo4j-Versionen standen auf den
  abgerufenen Seiten nicht (Dokumentation unter `neo4j.com/docs/mcp/current/`).
- `mcp-neo4j-graphrag`: Testabdeckung, Transport und Ollama-Basis-URL nicht geprüft (`docs/ADVANCED.md` im Repository).

## Quellen

- https://github.com/neo4j/mcp
- https://neo4j.com/docs/mcp/current/
- https://github.com/neo4j-contrib/mcp-neo4j
- https://pypi.org/project/mcp-neo4j-graphrag/
- https://github.com/neo4j-field/mcp-neo4j-graphrag
- https://neo4j.com/blog/developer/neo4j-graphrag-retrievers-as-mcp-server/
