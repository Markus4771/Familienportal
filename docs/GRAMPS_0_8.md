# Gramps Web / Ahnenforschung 0.8

## Ziel

Gramps Web bleibt ein eigener Dienst. Das Familienportal ersetzt Gramps nicht, sondern bindet die REST-API ein und stellt Suche, Benutzerzuordnung, Lebensdaten sowie GEDCOM-Transfer zentral bereit.

## Voraussetzungen

- Gramps Web separat betreiben, idealerweise hinter dem vorhandenen Reverse Proxy.
- Im Familienportal den Connector `gramps` aktivieren.
- Basis-URL der Gramps-Web-Instanz konfigurieren.
- Einen geeigneten Gramps-Web-Access-Token als Umgebungsvariable bereitstellen.
- Im Connector wird ausschließlich der Name dieser Umgebungsvariable gespeichert.

Beispiel:

```text
FAMILIENPORTAL_GRAMPS_ACCESS_TOKEN=...
```

Der Secret-Wert selbst wird nicht in der Portal-Datenbank gespeichert.

## Funktionen

### Connector und Healthcheck

Administration: `/platform/gramps`

Der Healthcheck ruft die Gramps-Web-API authentifiziert auf und speichert den Status im bestehenden Connector-State.

### Ahnenforschung

- `/genealogy` – Personensuche
- `/genealogy/families` – Familiensuche
- `/genealogy/dates` – Geburtstage und Gedenktage aus den verfügbaren Personendaten

REST-Endpunkte:

- `GET /api/v1/gramps/search?q=...&object_type=people|families`
- `GET /api/v1/gramps/people/{handle}`
- `GET /api/v1/gramps/families/{handle}`
- `GET /api/v1/gramps/dates`

Für die REST-Endpunkte wird `genealogy.read` verlangt.

### Benutzer- und Rechtezuordnung

Migration `0012_genealogy_mapping.py` legt `gramps_user_mappings` an. Pro Portal-Benutzer können Gramps-Benutzername, Gramps-Rolle und optional der Handle der eigenen Person hinterlegt werden.

Die Zuordnung ist eine Portal-Metadatenzuordnung. Sie verändert nicht automatisch die Benutzerverwaltung von Gramps Web.

### GEDCOM

Administratoren können über `/platform/gramps` einen GEDCOM-Export als Gramps-Web-Task starten und GEDCOM-Dateien importieren. Der Import ist auf `.ged`/`.gedcom` und maximal 25 MiB begrenzt.

Verwendete Gramps-Web-API-Oberflächen:

- `POST /api/exporters/ged/file`
- `GET /api/tasks/{task_id}`
- `GET /api/exporters/ged/file/processed/{filename}`
- `POST /api/importers/ged/file`

Der Import verändert den verbundenen Stammbaum und ist deshalb ausschließlich im Administrationsbereich verfügbar.

## Datenschutz

Genealogiedaten können Informationen über lebende Personen und Familienbeziehungen enthalten. Das Portal übernimmt Daten nur auf Anforderung aus Gramps Web und speichert in 0.8.0 keine vollständige lokale Kopie des Stammbaums. Dauerhaft gespeichert werden nur Connector-Konfiguration und Benutzerzuordnungen.

## Upgrade

```bash
sudo familienportalctl backup
sudo familienportalctl update /pfad/zur/neuen/version
```

Alternativ die Release-basierte Aktualisierung aus 0.7.3 verwenden. Die Migration `0012` wird beim Dienststart automatisch angewendet.

## Nächste Ausbaustufe

Für 0.8.1 vorgesehen:

- echte Synchronisation ausgewählter Geburtstage/Gedenktage in einen Portal-Kalender
- Medien-/Dokument-Verknüpfungen
- komfortablere Personendetailseiten und Beziehungen
- optional SSO/OIDC zwischen Portal und Gramps Web
