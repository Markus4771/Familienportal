# Gramps ↔ Kalender 0.8.1

## Ziel

Geburtstage und Gedenktage aus Gramps Web werden automatisch in einen eigenen Portal-Kalender `Familie & Ahnen` übernommen.

## Verhalten

- Quelle: aktivierter Gramps-Web-Connector der jeweiligen Familie
- Zielkalender: `Familie & Ahnen` (`slug=family-ancestry`)
- Kategorien: `birthday` und `memorial`
- Quelle am Termin: `source=gramps`
- stabile externe UID: `gramps:<typ>:<person-handle>:<jahr>`
- Synchronisationsfenster: aktuelles Jahr plus zwei Folgejahre
- vorhandene Termine werden aktualisiert statt dupliziert
- Termine, die in Gramps nicht mehr vorhanden sind, werden als gelöscht markiert
- 29. Februar wird in Nicht-Schaltjahren am 28. Februar dargestellt

## Automatischer Betrieb

Der separate systemd-Timer läuft alle 30 Minuten:

```bash
systemctl status familienportal-gramps-calendar-sync.timer
systemctl list-timers 'familienportal-*'
```

Die Erstinstallation ab 0.8.1 installiert und aktiviert den Timer automatisch.

## Bestehende Installation aktualisieren

Nach einem Update auf 0.8.1 die beiden neuen Units einmalig installieren und aktivieren, falls der Lifecycle-Manager sie auf dem bestehenden System noch nicht übernommen hat:

```bash
sudo install -m 0644 /opt/familienportal/deploy/systemd/familienportal-gramps-calendar-sync.service /etc/systemd/system/
sudo install -m 0644 /opt/familienportal/deploy/systemd/familienportal-gramps-calendar-sync.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now familienportal-gramps-calendar-sync.timer
```

## Manuell testen

```bash
cd /opt/familienportal
sudo -u familienportal \
  /opt/familienportal/.venv/bin/python -m familienportal.gramps_calendar_worker
```

Die Ausgabe enthält Zähler für Familien, neue, geänderte, gelöschte und unveränderte Termine sowie Fehler.

## Kein neues Datenbankschema

0.8.1 verwendet die bereits vorhandenen Felder `external_uid` und `source` in `calendar_events`. Daher ist keine zusätzliche Alembic-Migration erforderlich.

## Datenschutz

Es werden nur Lebensdaten in den Portal-Kalender kopiert, die der konfigurierte Gramps-Web-Zugang über die API liefert. Die Sichtbarkeit im Portal folgt anschließend den bestehenden Kalenderberechtigungen.
