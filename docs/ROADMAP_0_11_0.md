# Familienportal 0.11.0 – Familienalltag II

Status: Entwicklung (`0.11.0-dev`)

## Ziel

0.11.0 erweitert den Familienalltag um ein datenschutzbewusstes Notiz- und Listensystem. Die Funktionen bauen auf dem bestehenden Familien-, Haushalts-, Rollen-, Aufgaben-, Kalender- und Audit-System auf.

## Umsetzung

1. Entwicklungsstand auf `0.11.0-dev` setzen und Roadmap dokumentieren.
2. Notizen-Grundsystem: gemeinsame, persönliche und private Notizen; Titel, Inhalt, Familie, Haushalt, Eigentümer, Archivierung und Zeitstempel.
3. Rechte und Freigaben: Lesen, Erstellen, Bearbeiten, Archivieren, Löschen, Freigeben und administratives Verwalten; private Notizen nur für Eigentümer oder ausdrücklich berechtigte Benutzer.
4. Universelles Listen-System für Einkauf, Packlisten, Wunschlisten und freie Listen.
5. Listeneinträge mit Menge, Einheit, Kategorie, Verantwortlichem, Status, Sortierung und optionaler Fälligkeit.
6. Verknüpfungen von Notizen und Listen mit Aufgaben und Kalenderterminen.
7. Dashboard-Widgets und Schnellzugriffe.
8. Audit und Datenschutz ohne Speicherung privater Notizinhalte im Audit-Protokoll.
9. Mobile Web-Oberfläche unter `/notes` und `/lists`.
10. Tests und Alembic-Migrationen.
11. Regression und Hardening bestehender Funktionen.
12. Stable Release `0.11.0`.

## Rechte für Notizen

- `notes.read` – freigegebene/notwendige Familiennotizen lesen.
- `notes.create` – Notizen erstellen.
- `notes.edit` – eigene Notizen bearbeiten.
- `notes.archive` – eigene Notizen archivieren/wiederherstellen.
- `notes.delete` – eigene archivierte Notizen löschen, sofern die Produktlogik dies zulässt.
- `notes.share` – Notizen für andere Familienmitglieder freigeben.
- `notes.private.read` – private Notizen anderer Benutzer lesen; standardmäßig keiner normalen Rolle zugewiesen.
- `notes.manage` – administrative Verwaltung aller Notizen innerhalb der Familie.

## Datenschutzregeln

- Familiengrenzen dürfen niemals überschritten werden.
- Private Notizen sind standardmäßig ausschließlich für den Eigentümer sichtbar.
- `notes.manage` bzw. Superadmin kann administrativ zugreifen; dieser Zugriff muss auditierbar sein.
- Titel und Inhalt privater Notizen werden nicht in Audit-Metadaten übernommen.
- Dauerhaftes Löschen soll analog zu Aufgaben nur kontrolliert und nach Archivierung erfolgen.

## Vorgesehene Migrationen

- `0017`: Notizen-Grundmodell.
- `0018`: Notizrechte für bestehende Systemrollen, sofern die Rollenmigration getrennt gehalten wird.
- Weitere Migrationen für Listen und Verknüpfungen folgen innerhalb 0.11.x.
