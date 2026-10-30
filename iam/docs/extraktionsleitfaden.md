# Extraktionsleitfaden (Can-Do / Rohdaten)

Welche SAP-Tabellen, welche **Spalten** und in welchem Format extrahiert werden. Leitlinie:
**Datensparsamkeit** — nur was die Auswertung braucht. Insbesondere werden **keine
Passwort-Hashes** und keine personenbezogenen Klartextdaten extrahiert, die für die Can-Do-
Analyse nicht nötig sind.

:::{admonition} Bitte gegen euer System prüfen
:class: warning
Einige Spalten-/Semantik-Details sind release- und systemabhängig. Mit ⚠️ markierte Punkte
vor dem Produktivlauf einmal gegen das konkrete SAP-System verifizieren (SE11/SE16).
:::

## Format-Konventionen

- **Trennzeichen: Tab** (`\t`), UTF-8, mit Kopfzeile. Der Konverter erzeugt das automatisch aus dem
  SE16-„unkonvertiert"-Export; bei direktem CSV-Export Tab als Trenner wählen (die Load-Skripte lesen
  `FIELDTERMINATOR '\t'`).
- **Spaltenüberschriften = SAP-Feldnamen** (z. B. `BNAME`, `AGR_NAME`). So sind die
  Load-Skripte unabhängig von der Extraktionsmethode (SE16-Export, Tabellen-Download, Report).
- Dateien liegen lokal in `data/import/` und werden in Cypher als `file:///<name>.csv`
  referenziert — **keine** Windows-Absolutpfade (Linux-Container, AE-15).
- **`dataset`**: kein CSV-Feld, sondern ein **Cypher-Parameter** je Lauf (z. B.
  `acme-2026-12-31`). Der Runner setzt ihn; alle Knoten/Kanten erhalten ihn (Versionsdimension).
- **Datumsfelder** (SAP `YYYYMMDD`): Umwandlung in Neo4j-`date` beim Import (AE-07).
  `TO_DAT = '99991231'` (unbegrenzt) → `9999-12-31`; leeres/`00000000` → `1900-01-01`.
- **Datumsformat des Extrakts.** SAP schreibt Datumswerte im Format des Benutzerstamms der extrahierenden
  Person (`TT.MM.JJJJ`, `MM/TT/JJJJ`, `MM-TT-JJJJ`, `JJJJ.MM.TT`, `JJJJ/MM/TT`, `JJJJ-MM-TT`). Der Konverter schreibt
  alle Formate beim Import auf `TT.MM.JJJJ` um; die Meldung „Datumsformat … erkannt“ erscheint nach dem Import.
  Ohne diese Umwandlung würden Zeilen mit Tag > 12 nicht geladen und alle übrigen mit vertauschtem Tag/Monat.
  Bereits früher importierte Ordner werden beim nächsten Import einmalig neu konvertiert.
- **`*`/unbeschränkt**: wird gespeichert „wie geliefert" (kein Vorab-Mapping); Normalisierung
  erst in der Abfragelogik (AE-06).

## Alternative Lieferform: KAAP-Extraktor-Paket

Statt eines SE16-Listenexports kann ein SAP-Extraktor die Tabellen als **Paket** liefern. Der Import erkennt das
automatisch (oder über die Option „Quellformat“, s. [Handbuch](handbuch/funktionen.md)):

- **Container:** äußere ZIP → ein Ordner je Extraktionslauf → je Tabelle eine ZIP `<Präfix>_<TABELLE>_<NNNN>.ZIP` mit
  einer gleichnamigen `.TXT` (Teile `_0001`, `_0002`, … bei großen Tabellen). Protokolldateien (`…_<Datum>_<Uhrzeit>.TXT`),
  Bilder und XML-Beschreibungen werden ignoriert.
- **Inhalt:** UTF-8 (meist mit BOM), Zeilenende LF, Trennzeichen **`#|#`**, erste Zeile = SAP-Feldnamen (wie beim
  SE16-Export), Datumswerte `JJJJMMTT` (`00000000` = leer, `99991231` = unbegrenzt) — der Konverter schreibt sie auf
  `TT.MM.JJJJ` um.
- **Mehrere Läufe in einem Paket:** je Tabelle gewinnt der Lauf mit den meisten Spalten; Tabellen, die der Import nicht
  kennt, werden nicht ausgepackt.
- **Benutzerstamm:** Fehlt `USR02` (z. B. weil die Benutzergruppe im Extraktor nicht gelaufen ist), läuft der Import
  trotzdem, mit deutlicher Warnung (Nutzertyp/Sperre/Gültigkeit/letzte Anmeldung unbekannt). Für vollständige
  Auswertungen `USR02` nachliefern — bei Bedarf zusammen mit `V_USERNAME`, `USREFUS` und `USR06`.
- Der Extraktor protokolliert je Tabelle die **Zeilenzahl der Quelle** (`…_RECORDCOUNT_…`); sie lässt sich gegen das
  Import-Protokoll halten.

## Excel-Extraktor (`CSI_Tabellen.xlsm`)

Für den SAP-Download liegt ein **Excel-Extraktor** bei: `data/extractors/CSI_Tabellen.xlsm` (Reiter „Extractor" mit
VBA-Makro, Reiter „Stammdaten" mit der Tabellen- und Feldliste). Er kommt mit der Installation bzw. dem täglichen
Update auf den Rechner; die Makros müssen in Excel einmalig zugelassen werden. Die Liste im Reiter „Stammdaten" wird aus
`config/required_tables.json` erzeugt (`python data/extractors/generate_csi_stammdaten.py`) und enthält je Tabelle, ob sie
Pflicht oder optional ist — **nach jeder Änderung an der Tabellenliste neu erzeugen**, damit der Extraktor nicht von der
App-Prüfung abweicht. Die Datei enthält bewusst keine Verbindungsdaten (Systemname, Zugangsdaten) — vor dem Einchecken
einer geänderten Fassung prüfen, dass beim Speichern keine hinzugekommen sind.

Alles unter `data/extractors/` wird mit verteilt, darunter die Extraktionsdefinition `NEO-CSI.xml` (aus `config/required_tables.json`
erzeugt mit `python data/extractors/generate_extraction_xml.py`; sie enthält nur Tabellen- und Feldlisten).

## Welche Tabellen herunterladen?

Die SE16-Exporte (eine `.txt`/`.csv` je Tabelle, Dateiname = Tabellenname) gehören in den
Dataset-Ordner. Der Konverter prüft das **Minimalset vor dem Import** (Quelle:
`config/required_tables.json`) — **fehlt eine Pflicht-Tabelle, bricht er ab.** Pflicht sind nur Tabellen, ohne die
die Auswertung selbst nicht möglich ist. Optionale Tabellen reichern an: Fehlen sie, läuft der Import trotzdem; bei den
**empfohlenen** (`AGR_DEFINE`, `TSTCT`, `USOBT_C`, `T000`) zeigt die Vorprüfung eine Warnung mit den Folgen, bei den übrigen
steht das Fehlen nur im Import-Protokoll.

### Pflicht (Minimalset)

| Tabelle | Zweck |
| --- | --- |
| **USR02** | Benutzer-Stammsatz (Typ, Sperre, letzter Logon, Gültigkeit) |
| **AGR_AGRS** | Sammelrolle → Einzelrollen |
| **AGR_USERS** | Benutzer ↔ Rolle (mit Gültigkeit) |
| **AGR_PROF** | Rolle → generiertes Profil |
| **UST04** | Benutzer → direkt zugewiesenes Profil (z. B. `SAP_ALL`) |
| **AGR_1251** | Rollen-Berechtigungsdaten (Objekt/Feld/Werte je Rolle) |
| **UST10S** | Profil-Berechtigungen (Profilinhalte) |
| **UST12** | Berechtigungs-Feldwerte zu den Profilberechtigungen |

### Empfohlen (optional, Warnung bei Fehlen)

Der Import läuft ohne diese Tabellen; die **Auswertung** (Einzelfilter, SoD) ist nicht betroffen. Die Vorprüfung warnt mit den Folgen.

| Tabelle | Zweck — und was ohne sie fehlt |
| --- | --- |
| **AGR_DEFINE** | Rollen-Definition (Rollentext, Ersteller/Änderer, Sammel-/abgeleitete Rolle über `PARENT_AGR`). Ohne sie entstehen die Rollen trotzdem aus den Zuordnungs- und Berechtigungstabellen; Rollen-Detailseite und Rollen-Ranglisten sind eingeschränkt |
| **TSTCT** | Transaktionstexte. Ohne sie haben TCodes keinen Klartext (Anzeige, Rollenmenü, Berichte) |
| **USOBT_C** | SU24-Vorschlagswerte (TCode → Objekt/Feld; Quelle für `CHECKS`/`PROPOSES`). Ohne sie liefern der PFCG-Vorschlag („Aus TCode ableiten", Assistent im Aufbau-Tab) und die Konsistenzprüfung zu SU24-Prüfungen nichts |
| **T000** | Mandant-Stammdaten (Firma/Mandant/Ort/Währung). Ohne sie bleibt die Gliederung nach Firma/Mandant auf der Startseite und der Kopf der Berichte leer |

### Optional (Anreicherung)

| Tabelle | Ergänzt |
| --- | --- |
| **USOBT** | SU24-Vorschlagswerte, SAP-Standard (Gegenstück zu `USOBT_C`) — für den *effektiven* Prüfvermerk je (TCode, Objekt) braucht es beide Ebenen, da die Kundentabelle Standardwerte überschreiben kann |
| **USOBX** | SU24-Prüfkennzeichen (aktiv/unterdrückt), SAP-Standard — Grundlage für eine künftige Prüfvermerkprüfung auf Berechtigungsobjekte (BO); ⚠️ Spalte `OKFLAG` noch unverifiziert |
| **USR11** | Profiltexte |
| **USR13** | Berechtigungstexte |
| **TOBJT** | Berechtigungsobjekt-Texte |
| **AGR_TEXTS** | Rollentexte (sprachabhängig, `$lang`-Schalter) |
| **V_USERNAME** | Benutzernamen (Vor-/Nachname) |
| **USREFUS** | Referenzbenutzer |
| **UST10C** | Sammelprofile (Profil → enthaltene Profile) |
| **AGR_1252** | Org-Ebenen abgeleiteter Rollen |
| **AGR_TCODES** | Rollenmenü (TCodes der Rolle) |
| **AGR_1016** | Profil-Generierungsstatus der Rollen (`GENERATED`/`PSTATE`, s. Abschnitt 22 unten — **nicht** `AGR_1016B`) |
| **AGR_1016B** | Profilzuordnung je Rolle (`AGR_NAME`/`PROFILE`) — inhaltlich redundant zu `AGR_PROF`, aktuell ohne eigenen Loader |
| **USORG** | Registry der org-relevanten Berechtigungsfelder, Grundlage der Org-Dimension (genutzt von Loader `23`) — ohne sie entfällt die Org-Feld-Erkennung |
| **AGR_FLAGS** | Rollen-Flags/-Schalter — Nutzen für Can-Do noch zu klären, aktuell ohne Loader |
| **AGR_1250** | Manuell (nicht per SU24-Vorschlag) gepflegte Berechtigungen je Rolle — potenzieller Abweichungs-/Risikoindikator, aktuell ohne Loader |
| **USR06** | Lizenztyp je Nutzer (`User.licenseType`, Loader `31`) — Grundlage der Konsistenzchecks **B8** (aktive Dialog-User ohne Lizenztyp) und **B9** (Lizenztyp-Übersicht). Gültigkeitsfelder (`VONDAT`/`BISDAT`) liegen in Exporten häufig als `00.00.0000` vor und werden nicht geladen |
| **T001**, **T001W**, **T014**, **T024E**, **TVKO** | Org-Stammdaten (Buchungskreise, Werke, Kreditkontrollbereiche, Einkaufs-/Verkaufsorganisationen) — liefern die **Klartextbezeichnung** zu Org-Werten (`:OrgValue`, Loader `26`–`30`); reine Anzeige-Anreicherung, z. B. „0001 – Werk Nord" in der Werteauswahl der Org-Varianten. Je Tabelle genügen Schlüssel und Bezeichnung (`BUKRS`/`BUTXT`, `WERKS`/`NAME1`, `KKBER`/`KKBTX`, `EKORG`/`EKOTX`, `VKORG`/`VTEXT`) |

> `ADRP` (Vorname zusätzlich zu `V_USERNAME`) ist ebenfalls als optional hinterlegt, enthält aber
> personenbezogene Klartextdaten (PII) — Einsatzzweck vor Extraktion klären, daher bewusst nicht in
> der Tabelle oben mitgelistet.

Die genaue Ladereihenfolge ergibt sich aus den Dateinamen unter `load/` (`00…99`); die
benötigten **Spalten je Tabelle** stehen unten.

## Security-Erweiterung: RFC-Vertrauensstellungen (optional, noch kein Loader)

Eigene, bewusst **nicht** Teil von Pflicht/Optional oben, da unverifiziert und noch ohne
Lade-Skript — Datengrundlage für die geplante Security-Angriffspfade-Sicht
(`backend/security.py`, [ROADMAP-V2.md, Abschnitt „Security-Sicht — Angriffspfade"](https://github.com/neoprehn/iam/blob/main/ROADMAP-V2.md#security-sicht--angriffspfade-folgeschritte)):
Ziel ist eine Kante „User X kann per RFC-Destination auf System Y wechseln, ohne sich erneut
anzumelden" — das bereits geladene `S_RFC` deckt nur ab, *ob* ein User RFC-Bausteine ausführen
darf, nicht *wohin* eine Destination mit hinterlegten Zugangsdaten führt.

:::{admonition} Unverifiziert — vor Nutzung gegen ein echtes System prüfen
:class: warning
Feldnamen stammen aus Doku-Erinnerung, nicht aus einem geprüften Extrakt (Stand 2026-10-10, s.
`config/required_tables.json` → `rfcTrust`). Vor dem Bau eines Loaders zwingend gegen SE11/ein
reales System verifizieren — insbesondere die Kodierung von `RFCOPTIONS`.
:::

| Tabelle | Zweck | Quelle (SAP) |
| --- | --- | --- |
| **RFCDES** | RFC-Zielsystem-Definitionen — Verbindungstyp, Anmeldeverfahren (fest hinterlegter Benutzer vs. aktueller Benutzer vs. Trusted System), kodiert in `RFCOPTIONS` | SM59 |
| **RFCSYSACL** | Trusted-System-Vertrauensstellungen — welches Quellsystem/Mandant darf sich per Trusted RFC ohne erneute Anmeldung anmelden | SMT1/SMT2 |

Felder je Tabelle (identisch zu `config/required_tables.json` → `rfcTrust.fields`):

| Tabelle | Felder |
| --- | --- |
| `RFCDES` | `MANDT`, `RFCDEST`, `RFCTYPE`, `RFCOPTIONS` |
| `RFCSYSACL` | `MANDT`, `RFCSYSID`, `RFCCLIENT` |

**Blocker:** Es fehlt aktuell ein Testsystem/-dataset, um diese Erweiterung gegen echte Daten zu
verifizieren und einen Loader zu bauen — rein dokumentarisch vorbereitet, bis ein passendes
System verfügbar ist.

## Did-Do: Nutzungsdaten (STAD/ST03N) beschaffen (optional, noch kein Loader)

Eigene, bewusst **nicht** Teil von Pflicht/Optional oben — Datengrundlage für die geplante
Did-Do-Auswertung ([ROADMAP-V2.md, Phase 4](https://github.com/neoprehn/iam/blob/main/ROADMAP-V2.md#phase-4--neuer-extraktor-und-did-do)):
Can-Do sagt, was ein User **darf**, Did-Do, was er im Betrachtungszeitraum **tatsächlich
ausgeführt** hat. Daraus entstehen u. a. „ungenutzte Berechtigungen" (Least-Privilege) und die
Gegenüberstellung Can-Do × Did-Do.

**Anders als bei den Can-Do-Tabellen gibt es keinen einfachen SE16-Export.** SAP speichert die
Einzelsatzstatistik (STAD) clusterartig (Report `RSCOLL00` → Tabelle `MONI`) und stellt sie nur über
Transaktionen, das Service-Tool `/SDF/ST03DL` oder Funktionsbausteine bereit.

:::{admonition} Unverifiziert — vor Nutzung gegen ein echtes System prüfen
:class: warning
Stand 2026-10-13, noch kein realer Auszug vorhanden. Insbesondere offen: **ob und wie lange die
Workload-Aggregation eine User-Ebene (User × Transaktion) vorhält.** Die Standardaggregation je
Transaktion enthält keinen User; ob ein Benutzer-/Transaktionsprofil verfügbar ist und wie lange es
aufbewahrt wird, hängt von Release, ST-PI-Stand und Collector-Einstellungen ab. Feldnamen s.
`config/required_tables.json` → `didDo`.
:::

**Was Did-Do mindestens braucht:** je `(User, TCode)` im Betrachtungszeitraum (max. 1 Jahr) die
Anzahl der Aufrufe sowie erster und letzter Aufruf. Did-Do hängt am `Transaction`-Knoten (AE-12),
Einzelsätze mit Laufzeit-/Datenbankkennzahlen sind dafür nicht nötig.

### Mögliche Wege

| Weg | Inhalt | Einschätzung |
| --- | --- | --- |
| **ST03N** (Expertenmodus, Benutzer-/Transaktionsprofil) | aggregiert je User und Transaktion: Aufrufzahl, Zeitraum | Einstieg ohne Entwicklung, die Basis kann den Export machen. **Verfügbarkeit der User-Ebene und Aufbewahrung prüfen** (s. Warnung). |
| **Funktionsbaustein `SWNC_COLLECTOR_GET_AGGREGATES`** | dieselben Aggregate maschinenlesbar | Weg für den späteren Extraktor; braucht einen kleinen Z-Report oder RFC-Aufruf. Kein Tabellenexport im bisherigen Sinn. |
| **STAD** (Einzelsatzstatistik) | einzelne Dialogschritte mit Zeitstempel | Aufbewahrung meist nur Tage bis wenige Wochen (Parameter `stat/*`, Archivierung) — für ein Jahr nur nutzbar, wenn die Dateien regelmäßig gesichert wurden. |
| **`/SDF/ST03DL`** (OSS-Hinweis 2943445) | Download der Workload-Daten | Gut, sofern der ST-PI-Stand es zulässt. |
| **Security Audit Log (SM20/SAL)** | Audit-Ereignisse (Anmeldung, Transaktionsstart) | Nur wenn aktiviert gewesen; **kein Nutzungsprotokoll** im engeren Sinn (AE-13), eher für Forensik. |

### Empfohlene Reihenfolge

1. **Stichprobe beschaffen.** Mit ST03N-Zugriff einen kleinen Auszug (Benutzer-/Transaktionsprofil
   über den längstmöglichen Zeitraum) exportieren lassen. Damit werden die Feldnamen in `didDo` am
   echten Format verifiziert — das ist der aktuelle Blocker für Phase 4.
2. **`EXECUTED`-Kante und Can-Do × Did-Do-Matrix bauen** (User → Transaction mit `count`,
   `firstSeen`, `lastSeen`, `asOf`, `runId`).
3. **Extraktor** (Z-Report/RFC) erst, wenn das Format feststeht.

### Beim Kunden vorab klären

- **Aufbewahrung:** Wie weit reichen die Workload-Daten zurück, und gibt es die User-Ebene über den
  gesamten Zeitraum? Prüfbar in ST03N sowie in den Einstellungen des Workload-Collectors.
- **Datenschutz/Mitbestimmung:** Nutzungsdaten sind personenbezogen. Vorgesehen ist
  Pseudonymisierung der User-ID, Klartext nur im begründeten Einzelfall.
- **Grenzen der Aussage:** Selten, aber wichtige Transaktionen (z. B. Jahresabschluss) liegen ggf.
  außerhalb des Fensters; indirekte Aufrufe (Batch, RFC, Aufruf aus anderen Programmen) tauchen
  anders oder gar nicht als Transaktion auf. „Nicht genutzt" ist ein Hinweis, kein Beweis.

## Spalten je Tabelle

### 01 — USR02 (Benutzer) → `:User`
| Spalte | Verwendung |
| --- | --- |
| `BNAME` | User-ID (fachliche `id`) |
| `USTYP` | Benutzertyp → Subtyp-Label (`A`=Dialog, `B`=System, `C`=Communication, `S`=Service, `L`=Reference) |
| `UFLAG` | Sperrkennzeichen → Subtyp `Active`/`Locked` **plus** differenzierte Sperrgründe (s. u.) |
| `GLTGV` | gültig von (`date`) |
| `GLTGB` | gültig bis (`date`) |
| `TRDAT` | letzter Logon (`date`, optional) |
| `CLASS` | Benutzergruppe (optional) |
| `PWDINITIAL` | Passwort-Status-Kennzeichen (`0`/`1`/`2`, **kein Hash**) → `pwdInitial`, s. u. |
| `PWDCHGDATE` | letzte Passwortänderung (`date`, **kein Hash**) → `pwdChgDate` |
| `PWDSETDATE` | Datum der (Erst-/Neu-)Vergabe (`date`, **kein Hash**) → `pwdSetDate` |

**Sperrgründe aus `UFLAG`** (Bit-Flags, beim Import via `apoc.bitwise.op` zerlegt; ⚠️ Werte
gegen euer System bestätigen): `0` = nicht gesperrt; Bit `32` = durch Fehlanmeldungen; Bit `64`
= durch Administrator (lokal); Bit `128` = durch Administrator (global/ZBV). Kombinationen
möglich (Summe der Bits, z. B. `192` = `64`+`128`). Gespeichert als Property `lockReasons`
(Liste) + `uflag` (Rohwert); Subtyp-Label `Active` (UFLAG = 0) bzw. `Locked` (sonst).

**`PWDINITIAL`-Kennzeichen** (⚠️ von SAP nicht einheitlich öffentlich dokumentiert, vor
Produktivnutzung gegen das eigene System verifizieren — empirisch hergeleitet aus dem
Testdatenbestand, s. `KONSISTENZCHECKS.md` B3): `1` korreliert dort durchgehend mit
`PWDCHGDATE = PWDSETDATE` („Passwort seit Vergabe nie geändert" — der belastbare Befund); `2` ist
ein Mischfall (z. B. admin-gesetztes/zurückgesetztes Passwort, schwächeres Signal); `0` = regulär
geändert.

**Bewusst NICHT extrahieren — nur die echten Hash-/Algorithmus-Felder:** `BCODE*`, `BCDA*`,
`OCOD*`, `CODV*`, `PASSCODE`, `PWDSALTEDHASH`, `PWDHISTORY` (Konverter-Denyliste
`convert.py:DROP_DEFAULT`). **Nicht** ausgeschlossen sind reine Status-/Datumsfelder wie
`PWDINITIAL`/`PWDCHGDATE`/`PWDSETDATE` — diese sind keine Hashes und lassen das Passwort selbst
nicht rekonstruieren (analog zu `UFLAG`/`TRDAT`, die schon länger geladen werden). Klartextname/
Adressdaten (USR21/ADRP) sind für Can-Do nicht nötig — optional und separat (Did-Do-Phase:
Pseudonymisierung beachten).

> **Defense in Depth:** Falls die Hash-Spalten doch mitexportiert wurden, verwirft sie der
> Konverter (`Convert-Se16Export.ps1`, Parameter `-DropColumnsLike`) bereits bei der
> Umwandlung — sie landen in keiner CSV. Die Load-Skripte lesen ohnehin nur die benötigten
> Spalten, sodass die eigentlichen Hash-Daten den Graphen nie erreichen.

### 02 — AGR_DEFINE (Rollen) → `:Role`
| Spalte | Verwendung |
| --- | --- |
| `AGR_NAME` | Rollenname (fachliche `id`) |
| `PARENT_AGR` | **Sammelrolle** (bestätigt) — übergeordnete Composite-Rolle; deckungsgleich mit `AGR_AGRS` |
| `TEXT` | Rollenbeschreibung (einsprachig; kanonisch aus `AGR_TEXTS`, s. 21) → `r.text` |
| `CREATE_USR` / `CREATE_DAT` | Ersteller / Erstelldatum (`dd.mm.yyyy` → `date`) → `r.createUsr` / `r.createDat` |
| `CHANGE_USR` / `CHANGE_DAT` | letzter Änderer / Änderungsdatum → `r.changeUsr` / `r.changeDat` |

Ersteller/Änderer + Daten speisen die **Rollen-Detailseite** (Stammdaten-Reiter). Ein separates
**Generierungsdatum** ist in `AGR_DEFINE`/`AGR_1016` nicht enthalten und wird daher nicht angezeigt.

Subtyp `Composite`/`Single` wird **abgeleitet**: Composite = tritt in `AGR_AGRS` als `AGR_NAME`
(bzw. als `PARENT_AGR` in AGR_DEFINE) auf, sonst `Single`. Der Subtyp `Derived` und die Kante
`DERIVED_FROM` (abgeleitete Rolle → Master) haben in den aktuell extrahierten Tabellen **keine
bestätigte Quelle** (`PARENT_AGR` = Sammelrolle, nicht Ableitungsvorlage) → **zurückgestellt**,
bis die Ableitungs-Information vorliegt.

### 21 — AGR_TEXTS (Rollentexte) → `:Role.text`
| Spalte | Verwendung |
| --- | --- |
| `AGR_NAME` | Rollenname (Join auf `:Role`) |
| `SPRAS` *(bzw. `SPRSL`)* | Sprachschlüssel → `$lang`-Schalter; Loader liest robust beide |
| `TEXT` | Rollenbeschreibung → `r.text` |

Kanonische, **sprachabhängige** Quelle für Rollentexte (`AGR_DEFINE.TEXT` in `02` ist
einsprachig und lückenhaft). Läuft nach `02`: bevorzugte Sprache aus `$lang` überschreibt,
sonst bleibt der erste vorhandene Text. Siehe `load/21_role_texts.cypher`.

### 22 — AGR_1016 (Profil-Generierungsstatus) → `:Role`-Properties
| Spalte | Verwendung |
| --- | --- |
| `AGR_NAME` | Rollenname (Join auf `:Role`) |
| `GENERATED` | `'X'` = Profil generiert → `r.profileGenerated` (true, wenn **alle** Profile der Rolle) |
| `PSTATE` | Profilstatus (roh, ohne Interpretation) → `r.profileState` (Liste distinct) |

> ⚠️ **Tabelle heißt `AGR_1016`, nicht `AGR_1016B`.** Die `GENERATED`/`PSTATE`-Spalten stehen in
> `AGR_1016`. Ein früherer Stand las `agr_1016b.csv` → die Datei fehlte, `r.profileGenerated` blieb
> bei allen Rollen `NULL` (und Konsistenzcheck **D4** damit wirkungslos). Bitte `AGR_1016` extrahieren.

Verlustfrei/konzeptunabhängig: hält fest, ob die generierten Profile einer Rolle vorhanden/aktiv
sind. In Konzepten mit nicht generierten/veralteten Rollen sind deren AGR_1251-Berechtigungen
zur Laufzeit nicht (vollständig) aktiv — das **Finding** dazu (betroffene Rollen) gehört in die
Auswertung (Phase 3, AE-10), hier nur das Rohfaktum. Eine Rolle kann mehrere Profile haben
(`COUNTER`>1, Split bei >150 Objekten) → Aggregation je Rolle. Siehe `load/22_role_profile_status.cypher`.

:::{admonition} ⚠️ PSTATE-Bedeutung nicht offiziell dokumentiert
:class: warning
`PSTATE` wird bewusst **roh** gespeichert. Bisher beobachteter Wert: `'A'` = **Aktiv** (aktuell
generierte Version) — allgemein gebräuchliche SAP-Konvention, aber **nicht** einheitlich öffentlich
dokumentiert (analog `PWDINITIAL`, s. USR02). Die Rollen-Detailseite zeigt diese Interpretation nur
für `'A'` an (mit Hinweis-Icon); andere Codes erscheinen roh. Vor Produktivnutzung gegen das eigene
System verifizieren, falls weitere Codes auftauchen.
:::

### 03 — AGR_AGRS (Rollenhierarchie) → `CONTAINS`
| Spalte | Verwendung |
| --- | --- |
| `AGR_NAME` | Sammelrolle (Composite) |
| `CHILD_AGR` | enthaltene Einzelrolle |

### 04 — AGR_USERS (User-Rollen-Zuordnung) → `ASSIGNED_TO`
| Spalte | Verwendung |
| --- | --- |
| `UNAME` | User-ID |
| `AGR_NAME` | Rolle |
| `FROM_DAT` | Gültig-von der Zuordnung (`validFrom`, `date`) |
| `TO_DAT` | Gültig-bis der Zuordnung (`validTo`, `date`; `99991231`→`9999-12-31`) |

### 05 — AGR_PROF (Rolle → Profil) → `HAS_PROFILE`
| Spalte | Verwendung |
| --- | --- |
| `AGR_NAME` | Rolle |
| `PROFILE` | generiertes Berechtigungsprofil der Rolle |

`AGR_PROF` (Spalten `AGR_NAME`, `PROFILE`) genügt für `HAS_PROFILE` — `AGR_1016B` ist **nicht**
zusätzlich nötig.

### 06 — UST04 (User → Profil direkt) → `HAS_PROFILE`
| Spalte | Verwendung |
| --- | --- |
| `BNAME` | User-ID |
| `PROFILE` | direkt zugewiesenes Profil (z. B. `SAP_ALL`) |

### 07 — USR11 (Profiltexte) → `:Profile`-Properties
| Spalte | Verwendung |
| --- | --- |
| `PROFN` | Profilname (fachliche `id`) |
| `PTEXT` | Profiltext |
| `LANGU` | Sprache (Filter, z. B. `D`/`E`) |

Profil-Knoten entstehen aus den referenzierenden Quellen (AGR_PROF, UST04) und werden hier um
den Text angereichert.

### 08 — AGR_1251 (Berechtigungsdaten) → `:Authorization`, `HAS_AUTH`, `FOR_OBJECT`
| Spalte | Verwendung |
| --- | --- |
| `AGR_NAME` | Rolle (Träger der Berechtigung) |
| `OBJECT` | Berechtigungsobjekt (→ `:AuthObject`, z. B. `S_TCODE`) |
| `AUTH` | Auth-Instanz-Name (Gruppierungsschlüssel) |
| `FIELD` | Berechtigungsfeld (z. B. `ACTVT`, `BUKRS`, `TCD`) |
| `LOW` | Wert/Von-Wert |
| `HIGH` | Bis-Wert (bei Bereichen) |
| `DELETED` | Kennzeichen — Zeilen mit `X` ausfiltern |

**Gruppierung (AE-03):** ein `:Authorization`-Knoten je (`AGR_NAME`, `OBJECT`, `AUTH`) innerhalb
eines `dataset`. Feldwerte als Properties am Knoten: pro Feld `f_<FELD>` als Liste; Bereiche als
`"LOW..HIGH"`. `*` bleibt erhalten (AE-06).

### 09 — TSTC (Transaktions-Katalog) → `:Transaction`
| Spalte | Verwendung |
| --- | --- |
| `TCODE` | Transaktionscode (fachliche `id`) |
| `PGMNA` | Programmname (optional) |

### 10 — USOBT_C (SU24: Vorschlagswerte) → `CHECKS` + `PROPOSES`
| Spalte | Verwendung |
| --- | --- |
| `NAME` | Transaktionscode |
| `OBJECT` | Berechtigungsobjekt (SU24-Vorschlag) |
| `FIELD` | Berechtigungsfeld (Vorschlagswert) |
| `LOW` | Vorschlags-Von-Wert (kann leer sein — dann ist nur das Feld selbst relevant, ohne Default) |
| `HIGH` | Vorschlags-Bis-Wert (meist leer, außer bei echten Bereichen) |

Kante `(:Transaction)-[:CHECKS]->(:AuthObject)` aus den eindeutigen (`NAME`, `OBJECT`)-Paaren
(`load/10_su24_checks.cypher`). Zusätzlich (seit 2026-09-08, `load/11_su24_proposals.cypher`) eine
`(:Transaction)-[:PROPOSES {field, low, high}]->(:AuthObject)`-Kante pro (`NAME`,`OBJECT`,`FIELD`)-
Zeile — Grundlage für den USOBT-gestützten Query-Builder
([ROADMAP-V2.md](https://github.com/neoprehn/iam/blob/main/ROADMAP-V2.md#phase-1--admin-editor-v2-und-regelpflege)). `FIELD`/`LOW`/`HIGH`
sind **bereits im bisherigen Extraktumfang enthalten** (2026-09-08 gegen einen echten Datensatz
bestätigt, Felder durchgehend belegt) — keine zusätzliche SAP-seitige Extraktion nötig, nur bisher
ungenutzt. `LOW`/`HIGH` können SAP-Parameter-ID-Platzhalter enthalten (`$EKORG`, `$WERKS`, …statt
eines konkreten Werts) — das markiert ein Org-Ebenen-Feld, analog zu den bereits bekannten
Org-Feldern der Can-Do-Auswertung.

Die Unterscheidung „Prüfung aktiv/unterdrückt" (`USOBX_C.OKFLAG`) fehlt weiterhin — bei Bedarf
später über das optionale `USOBX_C` präzisieren (Spaltenname/Wertebedeutung vor Nutzung an einer
echten Extraktprobe verifizieren, noch **kein** Extrakt vorhanden).

### 25 — T000 (Mandant-Stammdaten) → `:Dataset`-Properties
| Spalte | Verwendung |
| --- | --- |
| `MANDT` | Mandantennummer → `d.mandant` |
| `MTEXT` | Firmenname/Mandantenbezeichnung → `d.companyName` |
| `ORT01` | Ort → `d.city` |
| `MWAER` | Währung → `d.currency` |
| `LOGSYS` | Logisches System → `d.logicalSystem` |

⚠️ T000 listet **alle** im System bekannten Mandanten, nicht nur den extrahierten — ein realer
Extrakt hatte 6 Zeilen statt der ursprünglich angenommenen einen. Welche Zeile zum Extrakt gehört,
steht nirgends explizit; `load/25_dataset_meta.cypher` ermittelt es daher über `USR02.MANDT`
(SE16-Extraktionen laufen immer in genau einem Mandanten-Kontext, jede USR02-Zeile trägt also
denselben Wert) und schreibt nur die dazu passende T000-Zeile auf den bereits existierenden
`:Dataset`-Knoten (läuft nach `00_dataset.cypher`). Grundlage der Firma-/Mandant-/Zeitscheiben-
Gliederung auf der Startseite
([ROADMAP-V2.md](https://github.com/neoprehn/iam/blob/main/ROADMAP-V2.md#phase-3--vergleich-interview-ergebnisse-und-erweiterte-exporte)).
Die übrigen Spalten (`ADRNR`, `CC*`-Systemänderbarkeits-Kennzeichen, `CHANGEUSER`/`CHANGEDATE`) sind
im Extraktumfang dokumentiert, aber ohne erkennbaren Nutzen für Can-Do (noch) ungenutzt.

## Validierung (AE: Importvalidierung)

Nach dem Import werden Zähler je Knoten-/Kantentyp gegen die Quell-Rowcounts der CSVs
geprüft (Skript `load/99_validate.cypher`, Phase-2-Abschluss). Stichproben gegen SAP
(einzelne User/Rollen) sichern die fachliche Nachvollziehbarkeit (DoD).

## Was hier (noch) NICHT abgebildet ist

- **Profil-Eigenwerte** (manuell gepflegte Profile via `UST12`/`USR12`, Profil-Inhalte
  `UST10S`): der rollenbasierte Pfad über `AGR_1251` ist abgedeckt; reine Profil-Auth-Werte
  außerhalb von Rollen bei Bedarf in einem Folgeschritt.
- **`DERIVED_FROM` / abgeleitete Rollen**: keine bestätigte Quelle in den extrahierten
  Tabellen (`PARENT_AGR` = Sammelrolle). Nachrüstbar, sobald die Ableitungsvorlage vorliegt.
- **Prüfkennzeichen** (`USOBX_C.OKFLAG`): nicht extrahiert; `CHECKS` basiert auf den
  USOBT_C-Vorschlagsobjekten. Präzisierung „aktiv/unterdrückt" später möglich.
- **Fiori/OData-Ebene** (S/4): bewusst zurückgestellt (siehe [Datenmodell](datamodel.md)).
- **Org-Ebenen-Pivot** (`AGR_1252`, `OrgValue`-Knoten): optional, nur falls benötigt.
