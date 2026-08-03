# Backlog

Statuswerte: `Idee`, `Geplant`, `In Arbeit`, `Erledigt`, `Zurückgestellt`.
Prioritäten: `Muss`, `Soll`, `Kann`.

## Epic FP-E01 – Plattform-Core

| ID | Anforderung | Priorität | Status |
|---|---|---|---|
| FP-001 | FastAPI-Grundanwendung und Konfiguration | Muss | In Arbeit |
| FP-002 | PostgreSQL- und SQLAlchemy-Basis | Muss | Geplant |
| FP-003 | Benutzer, Haushalte und Familienzweige | Muss | Geplant |
| FP-004 | Rollen- und Berechtigungssystem | Muss | Geplant |
| FP-005 | Auditprotokoll | Muss | Geplant |
| FP-006 | Dashboard und Navigation | Muss | Geplant |
| FP-007 | Benachrichtigungssystem | Soll | Geplant |

## Epic FP-E02 – Profile

| ID | Anforderung | Priorität | Status |
|---|---|---|---|
| FP-020 | Profil Kleinfamilie | Muss | Geplant |
| FP-021 | Profil Großfamilie | Muss | Geplant |
| FP-022 | Module je Profil vorbelegen | Muss | Geplant |
| FP-023 | Profil nachträglich wechseln | Soll | Geplant |

## Epic FP-E03 – Modulplattform

| ID | Anforderung | Priorität | Status |
|---|---|---|---|
| FP-030 | Modulmanifest und Lebenszyklus definieren | Muss | In Arbeit |
| FP-031 | Module installieren, aktivieren und deaktivieren | Muss | Geplant |
| FP-032 | Modulberechtigungen anzeigen und bestätigen | Muss | Geplant |
| FP-033 | API, Menü und Widgets dynamisch registrieren | Muss | Geplant |
| FP-034 | Event-Bus für Module | Muss | Geplant |
| FP-035 | Modulabhängigkeiten und Kompatibilität prüfen | Muss | Geplant |
| FP-036 | Module deinstallieren und Daten behandeln | Soll | Geplant |
| FP-037 | Signierte Modulpakete | Soll | Zurückgestellt |
| FP-038 | Öffentlicher Modul-Store | Kann | Idee |
| FP-039 | SDK, CLI und Beispielmodul | Soll | Geplant |

## Epic FP-E04 – Connector-Framework

| ID | Anforderung | Priorität | Status |
|---|---|---|---|
| FP-040 | Einheitliche Connector-Schnittstelle | Muss | In Arbeit |
| FP-041 | Fähigkeiten maschinenlesbar veröffentlichen | Muss | Geplant |
| FP-042 | Mehrere Instanzen eines Connectors | Soll | Geplant |
| FP-043 | Verbindungs- und Gesundheitstest | Muss | Geplant |
| FP-044 | Sichere Geheimnisverwaltung | Muss | Geplant |
| FP-045 | Connector-Ereignisse und Protokolle | Soll | Geplant |

## Epic FP-E05 – Nextcloud

| ID | Anforderung | Priorität | Status |
|---|---|---|---|
| FP-050 | Nextcloud-Verbindung und Statusprüfung | Muss | Geplant |
| FP-051 | Benutzer- und Gruppenzuordnung | Muss | Geplant |
| FP-052 | Dateien und Familienordner | Muss | Geplant |
| FP-053 | Freigaben und Speicherbelegung | Soll | Geplant |
| FP-054 | WebDAV-Integration | Muss | Geplant |
| FP-055 | CalDAV-Kalender | Soll | Geplant |
| FP-056 | CardDAV-Kontakte | Soll | Geplant |
| FP-057 | Single Sign-on prüfen | Soll | Idee |

## Epic FP-E06 – Mailcow

| ID | Anforderung | Priorität | Status |
|---|---|---|---|
| FP-060 | Mailcow-Verbindung und API-Status | Muss | Geplant |
| FP-061 | Postfächer anlegen und verwalten | Muss | Geplant |
| FP-062 | Aliasse und Familienverteiler | Muss | Geplant |
| FP-063 | Quotas und Kontostatus | Soll | Geplant |
| FP-064 | Passwortänderung und Sperrung | Muss | Geplant |
| FP-065 | Webmail-Verknüpfung | Soll | Geplant |
| FP-066 | Ungelesene Nachrichten im Dashboard prüfen | Kann | Idee |

## Epic FP-E07 – Großfamilienmodule

| ID | Anforderung | Priorität | Status |
|---|---|---|---|
| FP-070 | Nachrichtenportal | Muss | Geplant |
| FP-071 | Kleinanzeigen mit Suchen, Tauschen und Verschenken | Muss | Geplant |
| FP-072 | Familiengruppen und Familienzweige | Muss | Geplant |
| FP-073 | Ressourcen- und Geräteverleih | Soll | Geplant |
| FP-074 | Abstimmungen und Familienrat | Soll | Geplant |
| FP-075 | Newsletter und Rundschreiben | Soll | Geplant |
| FP-076 | Familienchronik und Stammbaum | Kann | Idee |

## Epic FP-E08 – Supportmodul

| ID | Anforderung | Priorität | Status |
|---|---|---|---|
| FP-080 | Tickets mit Nummer, Kategorie, Priorität und Status | Muss | Geplant |
| FP-081 | Benutzer-, Support- und Administratorrollen | Muss | Geplant |
| FP-082 | Ticketverlauf und Anhänge | Muss | Geplant |
| FP-083 | Öffentliche Antworten und interne Notizen | Muss | Geplant |
| FP-084 | Ticketzuweisung und Supportteams | Soll | Geplant |
| FP-085 | Wissensdatenbank | Soll | Geplant |
| FP-086 | Benachrichtigungen bei Änderungen | Soll | Geplant |
| FP-087 | Datenschutzgerechte Diagnosedaten | Muss | Geplant |
| FP-088 | Support-API für alle Module und Connectoren | Muss | Geplant |
| FP-089 | Rückrufwunsch und Vertrauensperson | Kann | Idee |

## Epic FP-E09 – Betrieb und Qualität

| ID | Anforderung | Priorität | Status |
|---|---|---|---|
| FP-090 | Debian-Paket | Soll | Geplant |
| FP-091 | Docker-Deployment | Soll | Geplant |
| FP-092 | Backup- und Wiederherstellungskonzept | Muss | Geplant |
| FP-093 | Automatisierte Tests | Muss | In Arbeit |
| FP-094 | Deutsche Dokumentation | Muss | In Arbeit |
| FP-095 | Mehrsprachigkeit vorbereiten | Soll | Geplant |
| FP-096 | PWA für Smartphone und Tablet | Soll | Geplant |

## Epic FP-E10 – Zwei-Faktor-Authentifizierung

| ID | Anforderung | Priorität | Status |
|---|---|---|---|
| FP-100 | TOTP-basierte Zwei-Faktor-Authentifizierung mit Authenticator-Apps | Muss | Geplant |
| FP-101 | QR-Code und manueller Einrichtungsschlüssel | Muss | Geplant |
| FP-102 | Einmalige Wiederherstellungscodes erzeugen und sicher speichern | Muss | Geplant |
| FP-103 | Zwei-Faktor-Authentifizierung für Administratoren verpflichtend konfigurierbar machen | Muss | Geplant |
| FP-104 | Zwei-Faktor-Authentifizierung pro Benutzer aktivieren und deaktivieren | Muss | Geplant |
| FP-105 | Bestätigung durch Passwort und zweiten Faktor vor sicherheitskritischen Änderungen | Muss | Geplant |
| FP-106 | Fehlversuche begrenzen und zeitweise Kontosperre einführen | Muss | Geplant |
| FP-107 | Aktivierung, Deaktivierung und Wiederherstellung im Auditprotokoll erfassen | Muss | Geplant |
| FP-108 | Gerätebezeichnung und mehrere TOTP-Geräte prüfen | Soll | Idee |
| FP-109 | WebAuthn/FIDO2 mit Sicherheitsschlüsseln und Passkeys unterstützen | Soll | Idee |
| FP-110 | Notfall-Zurücksetzung durch Administrator mit zusätzlicher Bestätigung | Soll | Geplant |
| FP-111 | 2FA-Richtlinien je Rolle und Familienbereich | Soll | Geplant |
| FP-112 | Zentrale 2FA-/SSO-Strategie für Nextcloud, Mailcow und Gramps Web prüfen | Soll | Geplant |
