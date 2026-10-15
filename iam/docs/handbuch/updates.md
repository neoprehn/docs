# Updates: Was braucht einen Neustart?

Diese Seite erklärt, **was nach einem Update wann wirksam wird** — besonders für Rechner, auf denen
niemand Entwicklungswerkzeuge hat (native Windows-Installation, „Drittrechner“).

## Kurzfassung

- Die App besteht aus zwei Teilen, die **im selben Git-Repository** liegen: der **Oberfläche**
  (Frontend: HTML-, JavaScript- und Textdateien) und dem **Backend** (Python-Programm plus Abfragen,
  Regelwerke und Konfiguration). Ein `git pull` aktualisiert deshalb **immer beide Dateisätze**.
- Die **laufenden Programme** ziehen aber unterschiedlich nach:
  - Die **Oberfläche** wird bei jedem Seitenaufruf frisch von der Festplatte gelesen — **kein
    Neustart nötig**, nur die Seite neu laden (bei Bedarf **Strg + F5**).
  - Das **Backend-Programm** (Python) wird nur beim Start gelesen — Änderungen daran wirken **erst nach
    einem Neustart** des Backends.
- **Merkregel:** Hat ein Update nur Oberfläche, Abfragen, Prüfkatalog oder Konfiguration geändert,
  genügt Neuladen. Sobald **Python-Code oder Python-Pakete** dabei sind, braucht es das vollständige
  Update **mit** Neustart.

## Was wirkt wann?

| Was hat sich geändert? | Wann wirksam? | Was ist zu tun? |
| --- | --- | --- |
| **Oberfläche** (`frontend/`: Seiten, Skripte, Übersetzungen) | sofort beim nächsten Seitenaufruf | Seite neu laden (**Strg + F5**). Kein Neustart. |
| **Abfragen** (`cypher/`) und **Prüfkatalog** (`checks/`) | beim nächsten Aufruf der Funktion | Nichts. |
| **Konfiguration und Stammdaten** (`config/`) | wird bei Gebrauch gelesen | Nichts. (Ausnahme: die Datei `.env` wird nur beim Start gelesen → Neustart.) |
| **Regelwerke** (`rules/`: Einzelfilter, SoD-Regeln, Risikokatalog) | in der Pflege-Ansicht sofort sichtbar; **im Graphen erst beim nächsten „Neuer Lauf“** (oder nach dem Speichern im Editor) | Für neue Regeln einen neuen Lauf starten. **Bereits berechnete Läufe ändern sich nicht.** |
| **Import-Logik** (`load/`, `migrations/`) | beim nächsten Import | Nichts; Schema-Migrationen laufen bei jedem Import idempotent mit. |
| **Backend-Programm** (`backend/*.py`) | **erst nach Neustart des Backends** | Neu starten (s. u.). |
| **Python-Pakete** (`backend/requirements.txt`) | erst nach Paket-Installation **und** Neustart | Vollständiges Update („Jetzt aktualisieren“). |
| **Neo4j** (Version, Speicher-, APOC-Einstellungen) | nie automatisch | Nur manuell, z. B. über „Speicher setzen + Neo4j neu starten“. |
| **Dokumentation** (`docs/`) | nur auf Read the Docs | Nicht Teil der laufenden App. |
| **`install.exe` / `manage.exe` / `update.ps1`** (Installationsordner, nicht im Git-Klon) | nur durch Austausch der Datei | Neue Fassungen werden **manuell übergeben**, ein Pull ändert sie nicht. `update.ps1` ersetzen genügt, `install.exe` bleibt unberührt. |

Daten, Backups und die `.env` fasst ein Update **nie** an: `data/`, `backups/` und `.env` bleiben
unverändert. Neue Programmlogik gilt außerdem **für neue Läufe** — vorhandene Läufe und Ergebnisse
werden nicht rückwirkend neu berechnet.

## Auf dem Drittrechner (native Windows-Installation)

Hier läuft das Backend **ohne automatisches Nachladen**. Es gibt drei Wege, den Code zu holen:

| Weg | Was passiert | Backend-Neustart? | Python-Pakete? |
| --- | --- | --- | --- |
| **Automatisch, täglich 06:00** (Aufgabe `IAM-Update`) | Holt den neuesten Stand, installiert Pakete, startet das Backend neu — aber **nur, wenn es neuen oder noch nicht aktivierten Stand gab** | ja | ja |
| **„Jetzt aktualisieren“** (Fenster „IAM verwalten“, `manage.exe`) | wie die tägliche Aufgabe, sofort | ja (bei neuem oder noch nicht aktiviertem Stand) | ja (ebenso) |
| **„Code aktualisieren (Git Pull)“** (Admin-Menü in der App) | holt **nur die Dateien** (`git pull`) | **nein** | **nein** |

Daraus folgt:

- **Der Git-Pull-Knopf ist der schnelle Weg für reine Oberflächen-, Abfrage-, Katalog- oder
  Regelwerks-Änderungen.** Danach reicht es, die Seite neu zu laden. Enthielt das Update dennoch
  Python-Änderungen, bleibt das **alte** Backend aktiv, bis „Jetzt aktualisieren“ den Stand aktiviert.
- **Enthält ein Update Python-Änderungen**, läuft danach die **alte** Programmversion weiter, bis das
  Backend neu startet. Dann kann die neue Oberfläche Funktionen aufrufen, die das alte Backend noch
  nicht kennt — typische Anzeichen sind Fehlermeldungen wie „Not Found“, leere Ansichten oder
  Schaltflächen ohne Wirkung. **Abhilfe: im Fenster „IAM verwalten“ auf „Jetzt aktualisieren“
  klicken** (aktiviert den geholten Stand) bzw. auf „Neu starten“.

**Der Aktivierungs-Marker.** Das Update-Skript merkt sich in `data\logs\deployed-head.txt`, **für welchen
Stand Pakete und Neustart zuletzt erfolgreich durchgelaufen sind**. Wurde der Code vorher per
Git-Pull-Knopf geholt, sieht „Jetzt aktualisieren“ (oder die tägliche Aufgabe), dass der geholte Stand
noch **nicht aktiviert** ist, und holt Paketinstallation und Backend-Neustart **nach**. Im Update-Log
steht dann: „Stand … ist bereits geholt …, aber noch nicht aktiviert — hole Paketinstallation und
Backend-Neustart nach.“ Schlägt die Paketinstallation fehl, wird das Backend bewusst **nicht** neu
gestartet (damit es nicht mit fehlenden Paketen anläuft) und der nächste Lauf versucht es erneut.

:::{admonition} Ältere Installationen
:class: note
Hat der Rechner noch eine **ältere `update.ps1`** (ohne Aktivierungs-Marker), meldet „Jetzt
aktualisieren“ nach dem Git-Pull-Knopf **„Bereits aktuell, kein Neustart nötig“** und startet
**nichts** neu — dort bleiben Python-Änderungen bis zum nächsten Neustart wirkungslos, neue
Python-Pakete werden nicht installiert. Erkennbar im Update-Log: die Zeile heißt „Bereits aktuell
(…)“ **ohne** „und aktiv“. Abhilfe: die Datei **`update.ps1` im Installationsordner** (dem Ordner mit
`install.exe`/`manage.exe`) durch die neue Version ersetzen. `install.exe` muss **nicht** erneut
ausgeführt werden und `manage.exe` nicht neu gebaut: Aufgabe und Fenster rufen die Datei nur per Pfad
auf. Bis dahin gilt: Git-Pull-Knopf nur, wenn sicher **keine** Python-Änderungen dabei sind, sonst
„Jetzt aktualisieren“ **ohne** vorherigen Knopf; reicht das nicht, hilft „Neu starten“.
:::

- **„Neu starten“** startet **Neo4j und das Backend** neu (nicht nur das Backend).
- Neue **Python-Pakete** installiert **ausschließlich** das vollständige Update (tägliche Aufgabe oder
  „Jetzt aktualisieren“) — auch dann, wenn der Stand vorher per Git-Pull-Knopf geholt wurde.
- Ein **Neustart unterbricht einen laufenden Lauf**. Er ist fortsetzbar, aber unnötig — Updates
  deshalb nicht mitten in eine Auswertung legen, besonders nicht um 06:00 Uhr, wenn dann noch ein
  Lauf läuft. Folgt der Rechner dem Zweig `main`, startet **jeder neue Commit** beim nächsten
  Update-Lauf das Backend neu.
- Die Update-Protokolle stehen im Fenster „IAM verwalten“ („Update-Log anzeigen“, „Backend-Log
  anzeigen“); ein Update bricht bewusst ab, wenn im Installationsordner lokale Änderungen liegen,
  statt sie zu überschreiben.

## Im Docker-Betrieb (Entwicklungsrechner)

Das Backend läuft hier im Entwicklungsmodus mit **automatischem Nachladen**: Die Python-Dateien, die in
`docker-compose.yml` einzeln eingebunden sind, werden bei einer Änderung vom Server selbst neu geladen
(kurzer Neustart des Servers, ein laufender Auswertungs-Job kann dabei abbrechen). Die Oberfläche, die
Abfragen, der Prüfkatalog, die Regelwerke und die Konfiguration sind eingebundene Ordner und gelten
sofort. Ein `git pull` im Projektordner genügt also meistens. Ausnahmen:

| Änderung | Was zu tun ist |
| --- | --- |
| **Neue Python-Datei** im Backend | Muss in `Dockerfile` (`COPY`) **und** `docker-compose.yml` (Einbindung) eingetragen sein, dann `docker compose up -d --build backend`. Sonst startet das Backend nach dem Pull gar nicht (`ModuleNotFoundError`). |
| **`requirements.txt`** oder **`Dockerfile`** | `docker compose up -d --build` (Image neu bauen). |
| **`docker-compose.yml`** (Ports, Einbindungen, Neo4j-Einstellungen) | `docker compose up -d` — Container werden neu angelegt. |

Der Knopf „Code aktualisieren (Git Pull)“ gibt es nur auf der nativen Windows-Installation; im Container
meldet er, dass er dort nicht verfügbar ist.

## Weiterführend

Installation, Aufgaben und Verwaltung der Windows-Installation:
[Native Windows-Installation](../technik/windows-native.md).
