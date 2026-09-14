# Mailcow 0.6.2

## Ziel

0.6.2 erweitert die Mailcow-Verwaltung um tägliche Administrationsaufgaben, die nach 0.6.1 noch fehlten.

## Neue Funktionen

- Passwort eines Mailcow-Postfachs aus dem Familienportal setzen
- Portal-Benutzer/Postfach-Zuordnung wieder lösen
- Alias und Verteiler mit mehreren Zieladressen pflegen
- Zieladressen mit Komma, Semikolon oder Zeilenumbruch eingeben
- doppelte Ziele werden beim Normalisieren entfernt
- Alias-Ziele und Aktivstatus ändern
- Alias direkt aus der Verwaltungsoberfläche löschen
- Capabilities für Passwort-Reset, Alias-Löschen, Verteiler und Unmapping

## Passwort-Sicherheit

Das neue Passwort wird ausschließlich an die Mailcow-API übermittelt. Es wird weder in `mailcow_user_mappings` noch in einer anderen Familienportal-Tabelle gespeichert.

Die Oberfläche setzt für neue Passwörter mindestens acht Zeichen voraus. Die endgültigen Passwortregeln von Mailcow bleiben zusätzlich maßgeblich.

## Verteiler

Ein Verteiler wird über die bestehende Mailcow-Alias-Funktion abgebildet. Mehrere Empfänger können mit Komma, Semikolon oder einer neuen Zeile getrennt werden.

Beispiel:

```text
mutter@example.de
vater@example.de
kind@example.de
```

wird als normalisierte Zielmenge an Mailcow übertragen.

## Endpunkte

- `POST /api/v1/mailcow/mailboxes/{mailbox}/password`
- `POST /api/v1/mailcow/mapping/{user_id}/delete`
- `POST /api/v1/mailcow/aliases/{alias_id}/settings`
- `POST /api/v1/mailcow/aliases/{alias_id}/delete`

## Datenbank

Für 0.6.2 ist keine zusätzliche Migration erforderlich. Die bestehende Tabelle `mailcow_user_mappings` aus Migration 0009 wird weiterverwendet.

## Nicht enthalten

- endgültiges Löschen eines Postfachs
- SSO nach SOGo
- Self-Service-Passwortänderung durch normale Portal-Benutzer

Diese Funktionen sollten erst mit zusätzlichen Schutzmechanismen bzw. dem Sicherheitsblock 0.7 umgesetzt werden.
