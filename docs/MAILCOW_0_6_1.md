# Mailcow 0.6.1

## Ziel

0.6.1 erweitert den lesenden Mailcow-Connector um eine Verwaltungs- und Zuordnungsschicht für Familienportal-Benutzer.

## Funktionen

- Portal-Benutzer einem Mailcow-Postfach zuordnen
- Postfach über die Mailcow-API anlegen
- Anzeigename, Quota und Aktivstatus eines Postfachs ändern
- Alias bzw. Verteileradresse anlegen
- Alias-Ziel und Aktivstatus über die API ändern
- Domains, Postfächer, Aliase und Quota weiterhin lesen
- Link zu SOGo/Webmail aus der Mailcow-Verwaltung
- Startpasswörter werden nicht in der Datenbank des Familienportals gespeichert

## Routen

- `GET /platform/mailcow`
- `GET /platform/mailcow/management`
- `POST /api/v1/mailcow/mapping`
- `POST /api/v1/mailcow/mailboxes`
- `POST /api/v1/mailcow/mailboxes/{mailbox}/settings`
- `POST /api/v1/mailcow/aliases`
- `POST /api/v1/mailcow/aliases/{alias_id}/settings`

## Datenmodell

`mailcow_user_mappings` verbindet einen Familienportal-Benutzer eindeutig mit einem Postfach innerhalb derselben Familie.

Migration `0009_mailcow_061.py` ergänzt außerdem die bereits im Reminder-Worker verwendeten Retry-Spalten `attempts` und `last_attempt_at` für `job_deliveries`.

## Sicherheit

Der Mailcow-API-Key bleibt über `ConnectorState.secret_reference` als Referenz auf eine Umgebungsvariable gespeichert. Der Key selbst wird nicht in der Datenbank persistiert. Startpasswörter werden nur für den jeweiligen API-Aufruf verarbeitet und nicht gespeichert.

Für schreibende Mailcow-Funktionen muss der konfigurierte API-Key über die notwendigen Schreibrechte verfügen. Der Mailcow-API-Zugriff sollte auf die IP des Familienportals eingeschränkt werden.

## Webmail

Die Verwaltungsseite erzeugt aus der Mailcow-Basis-URL einen Link auf `/SOGo/`. Eine automatische SSO-Anmeldung in SOGo ist noch nicht Bestandteil von 0.6.1.

## Noch offen

- Postfach löschen statt nur deaktivieren
- Alias löschen in der GUI
- Verteiler mit komfortabler Mehrfachauswahl
- Passwort-Reset-Workflow über das Familienportal
- optional SSO zu SOGo
