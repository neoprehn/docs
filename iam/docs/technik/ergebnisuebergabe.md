# Ergebnisübergabe (Datenbank-Dump/-Restore)

Dieses Verfahren übergibt den **kompletten Neo4j-Datenbankstand** (alle Datasets, Läufe, Findings)
an eine andere Umgebung — z. B. an einen Kollegen oder einen anderen eigenen Rechner. Es ist etwas
anderes als die **Backup/Restore**-Funktion in der App (Ribbon „Sichern"): die sichert nur die
**bereinigten Quelldaten eines einzelnen Datasets** als ZIP, keine Findings und keine anderen
Datasets. Für eine vollständige Übergabe des gesamten DB-Stands ist stattdessen `neo4j-admin
database dump`/`load` der richtige Weg.

:::{admonition} Vertrauensgrenze
:class: important
Ein Dump enthält den vollständigen Datenbestand, also potenziell Mandantendaten. Die Weitergabe
unterliegt denselben Auflagen wie der Rest der Umgebung — verschlüsselt übertragen, nur an
berechtigte Empfänger, unter den geltenden Mandanten-/Berufsgeheimnis-Vorgaben. Diese Seite
beschreibt ausschließlich das technische Vorgehen, keine Freigabe- oder Versandregeln.
:::

## Voraussetzung

Neo4j **Community Edition** kann keine einzelne Datenbank pausieren (`STOP DATABASE` ist
Enterprise-only) — deshalb wird für Dump und Restore jeweils kurz der **gesamte** `neo4j`-Container
gestoppt. Während dieser Zeit ist die App nicht erreichbar.

## Dump erstellen (Quell-Umgebung)

```powershell
# 1. Container stoppen (Backend bleibt optional an, verliert aber die DB-Verbindung)
docker compose stop neo4j

# 2. Dump schreiben -- <host> ist ein beliebiger lokaler Zielordner für die Ausgabedatei
docker compose run --rm -v <host>:/hostout neo4j neo4j-admin database dump neo4j --to-path=/hostout

# 3. Container wieder starten
docker compose start neo4j
```

Das Ergebnis ist eine einzelne `neo4j.dump`-Datei im angegebenen `<host>`-Ordner. Diese Datei vor
der Weitergabe verschlüsseln (z. B. 7-Zip mit Passwort, oder ein vom Mandanten vorgegebenes
Verfahren) — der Dump selbst ist unverschlüsselt.

## Restore (Ziel-Umgebung)

```powershell
# 1. Container stoppen
docker compose stop neo4j

# 2. Dump-Datei aus demselben <host>-Ordner einspielen -- vorhandene Daten werden überschrieben
docker compose run --rm -v <host>:/hostin neo4j neo4j-admin database load neo4j --from-path=/hostin --overwrite-destination=true

# 3. Container wieder starten
docker compose start neo4j
```

`--overwrite-destination=true` ist nötig, sobald die Zieldatenbank bereits existiert (z. B. nach
dem ersten `docker compose up`) — ohne das Flag bricht der Load ab.

## Verifiziert

Der Ablauf wurde Ende-zu-Ende gegen ein separates Test-Volume geprüft: Dump aus der
Quell-Umgebung, Load in eine frische Zielumgebung, Knotenzahl zwischen Quelle und Ziel **1:1**
identisch. Keine Abweichungen durch den Dump/Restore-Zyklus selbst.
