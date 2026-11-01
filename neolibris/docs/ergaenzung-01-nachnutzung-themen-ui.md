# Ergänzung 01 – Nachnutzung, Themenerweiterung und Steuer-UI

**Stand:** 31.10.2026
**Bezug:** KONZEPT.md (wird erweitert, nicht ersetzt)
**Anlass:** Neolibris ist die themenübergreifende Wissensbasis (Grundlagenliteratur). IAM ist nur das erste Thema. Lösungen wie die IAM-Lösung entstehen in **separaten Folgeprojekten**, die Neolibris lesend nutzen. Weitere Themen werden über eine Oberfläche ergänzt.

- **Teil A** – Nachnutzung in Folgeprojekten
- **Teil B** – Themenerweiterung und Steuer-UI

---

## Teil A – Nachnutzung in Folgeprojekten

### 1. Rollenverteilung

| | Neolibris (dieses Projekt) | Folgeprojekt (z. B. IAM-Lösung) |
|---|---|---|
| Inhalt | Literaturwissen: Konzepte, Kontrollen, Anforderungen, Standards – mit Belegen | Projektwissen: Architektur, Entscheidungen, Anforderungen an die Lösung |
| Zugriff auf den Graphen | lesen und schreiben (Pipeline) | **nur lesen** |
| Ablage | eigenes Repository `neolibris` | eigenes Repository, eigener Ordner unter `D:\Entwicklung` |

**Grundsatz:** Projektentscheidungen gehören ins Folgeprojekt, nicht in den Literaturgraphen. So bleibt Neolibris eine saubere, themenübergreifende Quelle. Folgeprojekte verweisen auf Neolibris über stabile IDs.

### 2. Schnittstellen (der „Vertrag“)

1. **MCP-Lesezugriff:** Das Folgeprojekt bindet denselben Neo4j-MCP-Server in seiner eigenen `.mcp.json` ein, ausschließlich mit Lese-Tools. Claude Code im Folgeprojekt kann damit direkt Fragen an die Literatur stellen.
2. **Benannte Abfragen:** Wiederkehrende Fragen liegen als versionierte Cypher-Dateien in `queries/<thema>/` (z. B. `queries/iam/controls_for_risk.cypher`, `queries/iam/nist_mapping.cypher`). Sie sind die stabile Schnittstelle; ändert sich das Datenmodell, werden nur sie angepasst.
3. **Wissenspaket-Export:** `kg export --topic iam` erzeugt einen versionierten Schnappschuss (Markdown und JSON) mit Glossar, Konzepten, Kontrollen, Anforderungen und NIST-Mapping – jeweils mit Quelle und Seite. Das Folgeprojekt kann damit auch ohne laufende Datenbank arbeiten (z. B. unterwegs oder auf dem Arbeitsrechner).

### 3. Anforderungen an Neolibris, die sich daraus ergeben

- **Stabile Entitäts-IDs:** Jede Entität bekommt eine dauerhafte `entity_id` (nicht nur den Namen), damit Folgeprojekte darauf verweisen können, auch wenn sich Bezeichnungen ändern. Zusammenführungen hinterlassen einen Verweis (`MERGED_INTO`).
- **Themenneutral:** Export und benannte Abfragen funktionieren für jedes Thema gleich – IAM ist nur der erste Anwendungsfall.
- **Versionierte Exporte:** Jeder Export trägt Datum, Ontologie-Version und Prompt-Versionen, damit nachvollziehbar ist, auf welchem Wissensstand das Folgeprojekt arbeitet.

### 4. Änderung gegenüber KONZEPT.md

- Kap. 9 („Entscheidungen als Knoten“): Projektentscheidungen werden **nicht** in Neolibris geschrieben, sondern im Folgeprojekt dokumentiert. In Neolibris bleiben nur Kuratierungsentscheidungen zur Literatur und Ontologie.

### 5. Neuer Umsetzungsschritt für Phase 1

| Schritt | Inhalt | Abnahmekriterium |
|---|---|---|
| 1.11 | Nachnutzbarkeit herstellen: `entity_id`, `queries/iam/`, `kg export --topic iam`, Vorlage `.mcp.json` (nur lesend) für Folgeprojekte | Aus einem leeren Testordner heraus beantwortet Claude Code über den MCP eine IAM-Frage mit Quelle und Seite; Wissenspaket IAM liegt versioniert vor |

---

## Teil B – Themenerweiterung und Steuer-UI

### 1. Grundsatz

Themen sind gleichberechtigte Module. IAM ist Thema Nr. 1 und dient als Muster. Jedes weitere Thema durchläuft denselben Prozess, wird über dieselbe Oberfläche gesteuert und über dieselben Schnittstellen (Teil A) von Folgeprojekten genutzt. Mögliche Folgethemen sind z. B. Cloud Governance oder Risikoquantifizierung; die Auswahl trifft Mirko.

### 2. Ontologie-Architektur: Kern plus Themenmodule

| Ebene | Inhalt | Datei |
|---|---|---|
| Kern-Ontologie | Themenübergreifende Typen: `Concept`, `Principle`, `Process`, `Actor`, `Control`, `Requirement`, `Standard`, `StandardClause`, `Risk` sowie die allgemeinen Beziehungen | `ontology/core.yaml` |
| Themenmodul | Zusätzliche, themenspezifische Typen und Beziehungen (IAM z. B. `AccessModel`, IAM-`Component`) | `ontology/<thema>.yaml` |

**Regeln:**
- Eine Entität existiert nur **einmal**, auch wenn sie in mehreren Themen vorkommt (z. B. eine ISO-27001-Kontrolle in IAM und Cloud). Die Eigenschaft `topics` listet alle Themen.
- Ein neues Themenmodul darf Kern-Typen nicht umdefinieren, nur ergänzen.
- Neue Typen, die sich in mehreren Themen bewähren, wandern nach Freigabe in den Kern.
- Themenübergreifende Abfragen (z. B. „Welche Kontrollen sind für IAM und Cloud zugleich relevant?“) sind dadurch ohne Zusatzaufwand möglich.

Beim Einarbeiten: Die IAM-Ontologie aus KONZEPT.md Kap. 7 wird in `core.yaml` und `iam.yaml` aufgeteilt.

### 3. Lebenszyklus eines Themas

`angelegt → kalibriert → in Extraktion → stabil → gepflegt`

| Status | Bedeutung | Übergang |
|---|---|---|
| angelegt | Name, Beschreibung, Few-Shot-Beispiele, Ontologiemodul vorhanden | Mirko startet Kalibrierung |
| kalibriert | Scout-Stichprobe geprüft, Probeextraktion eines Kapitels freigegeben | Mirko gibt Massenlauf frei |
| in Extraktion | Batch-Läufe laufen | alle WorkItems `done` oder `needs_human` |
| stabil | Prüferquote im Zielbereich, Export erstellt | automatisch |
| gepflegt | neue Literatur wird inkrementell verarbeitet | dauerhaft |

### 4. Neue Literatur

- `kg ingest` erkennt neue Dokumente per Hash.
- Neue Chunks werden automatisch für **alle Themen** im Status „stabil“ oder „gepflegt“ gescoutet; relevante landen in der jeweiligen Warteschlange.
- Ein neues Thema kann umgekehrt auf die gesamte bereits indexierte Bibliothek zugreifen – nichts muss neu eingelesen werden.

### 5. Steuer-UI (Phase 2)

**Technik:** Streamlit, lokal unter `127.0.0.1`, liest und schreibt ausschließlich über das Paket `kg` (keine eigene Geschäftslogik in der UI).

**Funktionsumfang:**

| Bereich | Funktion |
|---|---|
| Übersicht | Alle Themen mit Status, Fortschritt der Warteschlange, Prüferquote, Kosten je Anbieter |
| Thema anlegen | Assistent auf Basis von `topics/_vorlage.yaml`: Name, Beschreibung, Few-Shot-Beispiele, Ontologiemodul wählen oder neu anlegen, Budget |
| Kalibrierung | Scout-Stichprobe anzeigen und bestätigen bzw. korrigieren; Probeextraktion eines Kapitels starten und sichten |
| Laufsteuerung | Scout, Extraktion, Prüfung starten, pausieren, fortsetzen; Budget-Stopp sichtbar |
| Prüfliste | `needs_human`-Fälle mit Originaltext, Extraktion und Prüferurteil; freigeben, korrigieren, verwerfen |
| Ontologie | Änderungsvorschläge (neue Typen, Zusammenführungen) freigeben oder ablehnen; Versionsstand anzeigen |
| Export | Wissenspaket je Thema erzeugen (Teil A) |

**Bewusst nicht in der UI:** Graph-Visualisierung (dafür Neo4j Browser bzw. LLM Graph Builder) und Chat mit der Literatur (dafür Claude Code über MCP).

**Herleitung:** Die Felder und Knöpfe ergeben sich aus dem Erfahrungsprotokoll (KONZEPT.md Kap. 10a, Zeilen „selbst entscheiden“ bzw. „automatisch“). Die Tabelle oben ist der Startentwurf und wird nach Schritt 1.10 abgeglichen.

### 6. Skill „Neues Thema“

Zweiter Weg neben der UI: In Claude Code führt der Skill dialogisch durch Anlage und Kalibrierung eines Themas und nutzt dieselben `kg`-Befehle. Grundlage ist das Runbook aus Schritt 1.10.

### 7. Umsetzungsschritte Phase 2

| Schritt | Inhalt | Abnahmekriterium |
|---|---|---|
| 2.1 | Ontologie in Kern und Themenmodul aufteilen; Themen-Status im Datenmodell | IAM läuft unverändert mit `core.yaml` + `iam.yaml` |
| 2.2 | Inkrementelle Verarbeitung neuer Literatur für alle aktiven Themen | Ein neu abgelegtes PDF wird automatisch eingelesen, gescoutet und eingereiht |
| 2.3 | Streamlit-UI gemäß Abschnitt 5 | Alle Funktionen gegen das IAM-Thema getestet |
| 2.4 | Skill „Neues Thema“ | Skill führt bis zum Status „kalibriert“ |
| 2.5 | **Praxistest: zweites Thema** komplett über die UI | Thema erreicht Status „stabil“ ohne Kommandozeile und ohne Nachfragen; Lücken im Erfahrungsprotokoll festgehalten |

### 8. Anpassung des Phasenplans (KONZEPT.md Kap. 1)

- Phase 2: wie oben (Schritte 2.1–2.5).
- Phase 3: Arbeitsrechner und weitere Themen. Die **Entwicklung der IAM-Lösung** ist kein Teil von Neolibris mehr, sondern ein eigenes Folgeprojekt (siehe Teil A).

---

## Hinweis für Claude Code

Diese Ergänzung in `KONZEPT.md` einarbeiten – bestehende Inhalte nicht löschen, nur erweitern:

1. Neues Kapitel „Nachnutzung in Folgeprojekten“ (Teil A) mit Schritt 1.11; Kap. 9 anpassen: Projektentscheidungen gehören in Folgeprojekte, nicht in Neolibris.
2. Neues Kapitel „Themenerweiterung und Steuer-UI“ (Teil B); Kap. 7 um die Struktur Kern-Ontologie plus Themenmodule erweitern; Schritte 2.1–2.5 aufnehmen.
3. Phasenplan in Kap. 1 anpassen: Die Entwicklung der IAM-Lösung ist ein eigenes Folgeprojekt.
4. In `CLAUDE.md` ergänzen:
   - „Neolibris enthält nur Literaturwissen; Projektentscheidungen gehören in Folgeprojekte. Entitäten brauchen stabile `entity_id`.“
   - „IAM ist das erste von mehreren Themen – alles themenneutral bauen; die UI enthält keine eigene Geschäftslogik.“
5. Danach `KONZEPT.md` auf Widersprüche zwischen den Kapiteln prüfen und diese auflisten, bevor korrigiert wird.
