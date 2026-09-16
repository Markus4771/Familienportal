# Familienportal 0.8.6 – Datenschutz & Privatsphäre

## Ziel

Version 0.8.6 schützt Daten lebender Personen in der Ahnenforschung zentral und familienbezogen. Datenschutz wird nicht nur im HTML-Template angewendet, sondern auch auf API-, Beziehungs-, Medien-, Dokument- und Kalenderpfaden.

## Datenschutzstatus

Eine Person gilt als nicht lebend, wenn ein Sterbedatum vorhanden ist. Ein expliziter Gramps-Lebendstatus wird berücksichtigt. Fehlen eindeutige Angaben, wird aus Datenschutzgründen von einer lebenden Person ausgegangen. Das konfigurierbare Alterslimit liegt standardmäßig bei 110 Jahren und kann pro Familie zwischen 80 und 130 Jahren eingestellt werden.

## Modi

- `redact`: Die Person bleibt sichtbar, sensible Felder werden entfernt.
- `hide`: Ohne besondere Berechtigung wird die Person vollständig ausgeblendet.

Die Einstellungen werden als `FamilySetting` gespeichert:

- `genealogy.privacy.living_mode`
- `genealogy.privacy.living_age_years`

## Berechtigungen

- `genealogy.read`: allgemeiner Zugriff auf die Ahnenforschung.
- `genealogy.write`: Bearbeitung/Verknüpfung von Inhalten.
- `genealogy.living.read`: vollständige Daten lebender Personen.
- Superadmins erhalten vollständigen Zugriff.

## Geschützte Oberflächen

### Personendetails und Beziehungen

Personen werden vor der Darstellung durch die zentrale Datenschutzfunktion gefiltert. Im Modus `hide` liefert eine geschützte Person 404. Im Modus `redact` werden sensible Daten entfernt. Beziehungen verwenden ebenfalls nur gefilterte Personendaten.

### REST-API

Personendetail, Personensuche und Datumslisten wenden dieselbe Datenschutzregel an. Dadurch lässt sich die HTML-Sperre nicht über die API umgehen.

### Medien und externe Dokumente

Gramps-Medien sowie mit Nextcloud oder Paperless-ngx verknüpfte Dokumente werden für geschützte lebende Personen nicht ausgeliefert. Der Dokumentproxy prüft Person, Familie und Berechtigung vor der Auslieferung.

### Kalender

Der gemeinsame automatisch erzeugte Gramps-Kalender enthält derzeit grundsätzlich keine Termine lebender Personen. Ein gemeinsamer Kalender kann die individuelle Berechtigung `genealogy.living.read` nicht zuverlässig pro Betrachter durchsetzen. Dies ist daher absichtlich ein Fail-Closed-Verhalten. Eine spätere Kalender-ACL kann differenzierte Freigaben ermöglichen.

## Administration

Administratoren konfigurieren die Familienrichtlinie unter `/genealogy/privacy`. Änderungen werden im Audit-Log protokolliert.

## Noch folgende Härtung

Für 0.8.7 bzw. spätere Versionen vorgesehen:

- feinere Rollen-/Kalender-ACLs für Erwachsene, Kinder und Gäste,
- Live-Tests mit Gramps Web,
- zusätzliche Datenschutztests für komplette HTTP-Flows,
- Prüfung weiterer Gramps-Felder auf sensible Inhalte,
- optional getrennte Rechte für Medien und Dokumente.
