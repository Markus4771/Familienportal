# Betriebskonzept

## Verbindliche Zielplattform

Das Familienportal wird für Debian als Hauptplattform entwickelt und getestet.

- Betriebssystem: Debian Stable
- Reverse Proxy: vorhandenes Nginx
- Anwendung: Familienportal als eigener Dienst
- Datenbank: PostgreSQL als eigener Dienst
- Cloud: Nextcloud als getrennte Installation
- E-Mail: Mailcow als getrennte Installation
- TLS: Terminierung über Nginx bzw. den jeweils zuständigen Dienst

## Diensttrennung

Familienportal, Nextcloud und Mailcow werden unabhängig voneinander installiert, aktualisiert, überwacht und gesichert. Sie teilen weder Anwendungscontainer noch Datenbanken.

```text
Internet / internes Netz
          |
        Nginx
          |
   +------+------+----------------+
   |             |                |
Familienportal  Nextcloud       Mailcow
   |             |                |
PostgreSQL   eigene Datenbank   Mailcow-Stack
```

Mailcow wird wegen seines eigenen Reverse-Proxy-, Mail- und Container-Stacks separat betrieben. Eine Integration erfolgt ausschließlich über dokumentierte APIs, Links und später Single Sign-on.

## Familienportal-Dienst

Bevorzugte produktive Installation:

- eigener Linux-Systembenutzer `familienportal`
- Anwendung unter `/opt/familienportal`
- Konfiguration unter `/etc/familienportal`
- veränderliche Daten unter `/var/lib/familienportal`
- Protokolle über systemd-journald
- systemd-Dienst `familienportal.service`
- interne Bindung nur an `127.0.0.1`, beispielsweise Port `8080`
- öffentliche Bereitstellung ausschließlich über Nginx

## Nginx

Nginx übernimmt für das Familienportal:

- HTTPS
- Weiterleitung auf den lokalen Anwendungsport
- sichere Header
- Upload-Limits
- Zeitüberschreitungen
- optional Rate-Limiting
- Weitergabe der ursprünglichen Client-IP

Die Nginx-Konfiguration darf bestehende Nextcloud- oder Mailcow-Konfigurationen nicht überschreiben.

## DNS und Namen

Empfohlene getrennte Hostnamen:

- `portal.example.de` für das Familienportal
- `cloud.example.de` für Nextcloud
- `mail.example.de` für Mailcow und Webmail

Die tatsächlichen Namen bleiben installationsabhängig und werden im Installationsassistenten konfiguriert.

## Netzwerk und Firewall

- Das Familienportal benötigt keinen direkten öffentlichen Anwendungsport.
- PostgreSQL bleibt lokal oder in einem privaten Servernetz.
- Connectorzugriffe auf Nextcloud und Mailcow erfolgen über HTTPS.
- API-Schlüssel werden nicht im Repository gespeichert.
- Ausgehende Verbindungen werden dokumentiert und auf notwendige Ziele begrenzt.

## Updates

Jeder Dienst besitzt einen eigenen Updatezyklus:

- Familienportal: eigenes Debian-Paket und später optional eigener APT-Kanal
- Nextcloud: nach dem unterstützten Nextcloud-Verfahren
- Mailcow: nach dem unterstützten Mailcow-Verfahren
- Nginx und PostgreSQL: über Debian-Paketverwaltung

Vor Updates werden Kompatibilität, Datenbankmigrationen und verfügbare Sicherungen geprüft.

## Backup

Sicherungen werden je Dienst getrennt erzeugt, aber als gemeinsamer Wiederherstellungsplan dokumentiert:

- Familienportal-Datenbank
- Familienportal-Konfiguration
- Modul- und Connector-Einstellungen
- Nextcloud-Daten und Datenbank
- Mailcow-Konfiguration und Maildaten
- Nginx-Konfiguration und Zertifikatsinformationen

Geheimnisse müssen verschlüsselt gesichert werden. Regelmäßige Wiederherstellungstests sind verpflichtend.

## Noch festzulegen

- unterstützte Debian-Hauptversionen
- Standardport des lokalen Familienportal-Dienstes
- Paketname und APT-Repository
- Installationsassistent und Ersteinrichtung
- Backupziel und Aufbewahrungsfristen
- Hochverfügbarkeit ist für Version 1.0 nicht vorgesehen
