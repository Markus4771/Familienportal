# Gramps Web – Personendetails und Beziehungen 0.8.2

## Ziel

0.8.2 ergänzt die Gramps-Web-Integration um eine eigene Personendetailseite im Familienportal. Personen werden nicht lokal dupliziert; Beziehungen werden bei Aufruf aus den Gramps-Daten aufgelöst.

## Seiten

- `/genealogy` – Personensuche
- `/genealogy/person/{handle}` – Personendetailseite
- `/genealogy/families` – Familiensuche
- `/genealogy/dates` – Geburtstage und Gedenktage

## Beziehungen

Die Detailseite zeigt, soweit Gramps Web die Informationen liefert:

- Eltern
- Partner
- Kinder
- Geburts-/Sterbeinformationen
- Gramps-ID
- direkten Link zur Person in Gramps Web

Die Personen in den Beziehungsgruppen sind anklickbar und öffnen wiederum die jeweilige Personendetailseite.

## Berechtigungen

Für den Zugriff ist `genealogy.read` erforderlich. Administratorrechte sind für die reine Anzeige nicht notwendig.

## Datenhaltung

Es werden für diese Funktion keine neuen lokalen Stammdaten gespeichert. Die vorhandenen Gramps-Handles dienen als stabile Referenzen. Daher ist keine zusätzliche Alembic-Migration erforderlich.

## Tests

`tests/test_gramps_relationships_082.py` prüft die unterstützten Familienreferenz-Formate sowie die Auflösung von Eltern, Partnern und Kindern.

## Nächster Schritt

0.8.3 soll Medien und Dokumente mit Personen verknüpfen, insbesondere Familienfotos und Urkunden über Nextcloud sowie optional Dokumente über Paperless-ngx.
