# Troubleshooting

Diese Seite legt die Dinge aus {doc}`updates` eine Ebene tiefer: **was läuft eigentlich wo**, **was bewirkt welche
Aktion** und **woran erkennt man, welche Schicht klemmt**. Alle genannten Prüfungen sind **lesend** und brauchen
keine Administratorrechte.

## Welche Schichten gibt es?

| Schicht | Native Windows-Installation | Docker (Entwicklungsrechner) |
| --- | --- | --- |
| **Neo4j** (Datenbank, APOC) | Windows-Dienst `neo4j` | Container `iam-neo4j` |
| **Backend** (FastAPI, Python) | geplanter Task `IAM-Backend`, Python aus `.venv-win` | Container `iam-backend` |
| **Oberfläche** | Dateien aus `frontend\`, vom Backend ausgeliefert | dasselbe (eingebunden) |
| **Abfragen, Regelwerke, Kataloge** | Dateien im Repo (`cypher\`, `rules\`, `checks\`, `config\`) | dasselbe (eingebunden) |
| **Update** | geplanter Task `IAM-Update` (täglich 06:00) | `docker compose` bzw. `deploy\docker-update-test.ps1` |

Eine Änderung wirkt erst, wenn die **Schicht, die sie liest, neu geladen** hat. Daraus folgt fast alles Weitere.

## Was bewirkt welche Aktion?

| Aktion | Git-Stand holen | Python-Pakete | Backend neu | Neo4j neu |
| --- | :---: | :---: | :---: | :---: |
| Code aktualisieren (Git Pull), Admin-Menü | ja | nein | nein | nein |
| **Jetzt aktualisieren** (Manage) / Update-Reiter / 06:00-Task | ja | ja | ja (nur bei neuem oder noch nicht aktiviertem Stand) | nein |
| **Neu starten** (Manage) | nein | nein | ja | ja |
| Neustart des Rechners | nein | nein | ja | ja |
| Seite im Browser neu laden | nein | nein | nein | nein |

Ein Rechner-Neustart ersetzt das Update also **nicht**: Er lädt nur neu, was bereits auf der Platte liegt.

## Symptome und Abhilfe

**Schaltflächen ohne Wirkung, leere Ansichten, „Not Found“ nach einem Update.**
Die Oberfläche ist neuer als das laufende Backend (Git-Pull-Knopf geholt, Backend nicht neu gestartet).
Abhilfe: **Jetzt aktualisieren** (aktiviert den geholten Stand). Im Update-Log steht dann „… noch nicht aktiviert —
hole Paketinstallation und Backend-Neustart nach“.

**Backend startet nach einem Update nicht (Seite nicht erreichbar).**
Häufigste Ursache: ein neues Python-Modul oder -Paket fehlt. Im Backend-Log (Fenster „IAM verwalten“ →
*Backend-Log anzeigen*) steht dann `ModuleNotFoundError`. Abhilfe: **Jetzt aktualisieren** (installiert die Pakete).
Schlägt die Paketinstallation selbst fehl, startet das Update das Backend bewusst **nicht** neu; das Update-Log nennt
den Exit-Code, der nächste Lauf versucht es erneut (Netzwerk/Proxy prüfen).

**„Jetzt aktualisieren“ meldet „Bereits aktuell, kein Neustart nötig“, obwohl ein Update geholt wurde.**
Ältere `update.ps1` ohne Aktivierungs-Marker. Die Datei im Installationsordner ersetzen (siehe {doc}`updates`).

**Update bricht ab („merge --ff-only fehlgeschlagen“).**
Im Repo-Ordner liegen lokale Änderungen. Das Update überschreibt sie bewusst nicht; Änderungen prüfen
(`git -C <Repo> status`) und zurücknehmen oder sichern.

**Update-Task läuft nicht / Update-Reiter ist ausgegraut.**
Der Task `IAM-Update` fehlt oder läuft bereits (ein zweiter Start wird abgelehnt). Zustand im Reiter *Update* bzw.
im Manage-Fenster ansehen; fehlt der Task, einmalig `install.exe` ausführen.

**Abfragen/Auswertungen liefern Fehler, die Seite selbst lädt.**
Neo4j ist nicht erreichbar oder noch am Starten. Neo4j-Log ansehen; die Datenbank braucht nach einem Start einen
Moment (Health-Prüfung). „Neu starten“ in Manage startet Neo4j **und** Backend.

**Ein Import oder Lauf ist nach einem Neustart/Update abgebrochen.**
Ein Neustart des Backends unterbricht laufende Jobs. Sie sind **fortsetzbar** (Banner „Letzter Import
unterbrochen“ bzw. „Weitermachen“). Updates deshalb nicht in eine laufende Auswertung legen — besonders nicht um
06:00 Uhr.

**Import-Protokoll zeigt „Abweichung“ oder Hinweise.**
Hinweise [1]–[9] sind erklärbare Unterschiede und im Protokoll erläutert; eine **Abweichung** bedeutet weniger Daten
im Graphen als nach der Quelle erwartet. Dann Import-Log und Fehlerprotokoll (Admin) ansehen und den Import
wiederholen.

## Wo stehen die Protokolle?

| Protokoll | Ort / Zugang |
| --- | --- |
| Update-Lauf | `data\logs\windows-update.log` — Manage: *Update-Log anzeigen*, App: Reiter *Update* im Import-Dialog |
| Backend | `data\logs\windows-backend.log` — Manage: *Backend-Log anzeigen* |
| Neo4j | `<Neo4j-Ordner>\logs\neo4j.log` — Manage: *Neo4j-Log anzeigen* |
| Fehlgeschlagene Jobs | App: Admin → *Fehlerprotokoll* (überlebt Neustarts) |
| Aktivierter Git-Stand | `data\logs\deployed-head.txt` (Marker von `update.ps1`) |

## Docker-Betrieb

Im Docker-Betrieb lädt das Backend Python-Dateien selbst nach (`--reload`); ein **neues Python-Modul** muss aber im
`Dockerfile` (`COPY`) und in `docker-compose.yml` eingetragen sein, sonst startet das Backend nicht. Bibliotheken und
Images aktualisiert man mit `deploy\docker-update-test.ps1` (Smoke-Test, automatischer Rollback; siehe
{doc}`updates`). Container prüfen: `docker compose ps`, `docker logs iam-backend`.

## Wann `install.exe`?

Nur bei Erstinstallation, geänderten Neo4j-/APOC-Versionen, geänderten Aufgaben/Diensten/Rechten oder fehlenden
Voraussetzungen (Python, Git, Java) — **nicht** für regelmäßige Updates.
