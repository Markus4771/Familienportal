# Familienportal 0.12.0 – Familienalltag III

Status: Entwicklung (`0.12.0-dev`)

## Ziel

0.12.0 baut die in 0.10 und 0.11 eingeführten Aufgaben, Notizen und Listen zu einem enger verzahnten Familienalltag aus. Schwerpunkt sind Bedienkomfort, echte Freigaben, Dashboard-Integration und die praktische Verbindung zwischen Listen, Notizen, Aufgaben und Kalender.

## Umsetzung

1. Entwicklungsstand auf `0.12.0-dev` setzen und Roadmap dokumentieren.
2. Dashboard-Integration fertigstellen: Notizen, Listen, offene Listeneinträge, Schnellzugriffe und zuletzt bearbeitete Inhalte unter Beachtung aller Sichtbarkeitsrechte.
3. Listenrechte für bestehende Systemrollen per eigener Alembic-Migration nachziehen; benutzerdefinierte Rollen unverändert lassen.
4. Listenverwaltung vervollständigen: Bearbeiten, Archivieren, Wiederherstellen und kontrolliertes endgültiges Löschen nach Archivierung.
5. Notizverwaltung vervollständigen: Archivansicht, Wiederherstellen und kontrolliertes endgültiges Löschen.
6. Freigaben ausbauen: private Inhalte gezielt für Familienmitglieder bzw. Haushalte freigeben, ohne Familiengrenzen zu überschreiten.
7. Content-Links produktiv nutzbar machen: aus Notizen und Listen Aufgaben oder Kalendertermine anlegen und bestehende Verknüpfungen anzeigen.
8. Content-Link-Hardening: logische Duplikate verhindern und Link-Typ, Quelle und Ziel konsistent in Service und Datenbank absichern.
9. Listenkomfort: Sortierung, Kategorien, Verantwortliche, Fälligkeiten, Mengen/Einheiten und schnelle mobile Bedienung verbessern.
10. Datenschutz und Audit härten: administrative Zugriffe auf private Inhalte auditieren; keine privaten Titel, Texte oder Listeneinträge im Audit speichern.
11. Tests, Migrationen, Regression und Transaktionssicherheit für alle 0.12-Funktionen; CI-Migrationskette aktualisieren.
12. Stable Release `0.12.0` vorbereiten und nach grünem CI freigeben.

## Leitlinien

- Familiengrenzen gelten für sämtliche Inhalte und Verknüpfungen.
- Private Inhalte bleiben standardmäßig ausschließlich beim Eigentümer.
- Administrative Sonderzugriffe müssen nachvollziehbar sein, ohne vertrauliche Inhalte ins Audit zu schreiben.
- Dauerhaftes Löschen erfolgt nur kontrolliert und grundsätzlich erst nach Archivierung.
- Aufgaben, Kalender, Notizen und Listen bleiben eigenständige Module und werden über klar definierte Services miteinander verbunden.
- Mobile Nutzung bleibt ein Kernziel der Web-Oberfläche.

## Vorgesehene Migrationen

- `0021`: Listenrechte für bestehende Systemrollen.
- `0022`: Freigaben für Notizen und Listen.
- `0023`: Content-Link-Hardening, falls Datenbankänderungen erforderlich sind.
- Weitere Migrationen nur, wenn die Umsetzung zusätzliche persistente Daten benötigt.
