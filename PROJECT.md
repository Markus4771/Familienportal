# Projektvision: Familienportal

## Ziel

Das Familienportal ist eine zentrale, selbst gehostete Plattform für Organisation, Kommunikation und digitale Dienste einer Familie oder Großfamilie. Bewährte Open-Source-Systeme werden über standardisierte Connectoren integriert. Neue Funktionen werden als austauschbare Module entwickelt.

## Zielgruppen

### Kleinfamilie

Ein Haushalt mit wenigen Benutzern. Schwerpunkt: Kalender, Aufgaben, Einkauf, Dokumente, Nachrichten und Alltag.

### Großfamilie

Mehrere Haushalte, Generationen oder Familienzweige. Zusätzlich: Nextcloud, Mailcow, Kleinanzeigen, Nachrichtenportal, Ressourcen, Familiengruppen, Supportteams, gemeinsame Dokumente und feinere Berechtigungen.

## Verbindliche Grundsätze

1. Modularität vor monolithischer Entwicklung.
2. Konfiguration und Erweiterungsschnittstellen statt Änderungen am Core.
3. PostgreSQL als produktive Hauptdatenbank.
4. Python und FastAPI als primäre Backend-Plattform.
5. Nextcloud für Cloud-, Datei-, Kalender- und Kontaktfunktionen.
6. Mailcow für E-Mail-Funktionen.
7. Externe Dienste werden über austauschbare Connectoren angebunden.
8. Datenschutz, Datensparsamkeit und transparente Berechtigungen sind Kernanforderungen.
9. Externe Entwickler sollen eigene Module mit einem SDK erstellen können.
10. Der Core bleibt klein und enthält nur Plattformfunktionen.

## Kernumfang

- Benutzer, Haushalte, Familienzweige und Gruppen
- Rollen- und Berechtigungsverwaltung
- Profile Kleinfamilie/Großfamilie
- Modulmanager
- Connectormanager
- Dashboard
- Ereignissystem
- Benachrichtigungen
- Support-API
- Auditprotokoll

## Erste Fachmodule

- Nachrichtenportal
- Kleinanzeigen
- Support und Tickets
- Kalender und Aufgaben
- Nextcloud-Connector
- Mailcow-Connector

## Langfristige Vision

Das Familienportal wird zum privaten digitalen Einstiegspunkt mit einer Anmeldung, einer einheitlichen Oberfläche und einem sicheren Modul-Ökosystem.