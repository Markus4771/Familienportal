# Sicherheit 0.7.1

## Umfang

0.7.1 erweitert den Sicherheitskern um:

- WebAuthn-/Passkey-Registrierung
- Anmeldung per Passkey
- mehrere Passkeys pro Benutzer mit Bezeichnung und Löschfunktion
- QR-Code bei der TOTP-Einrichtung
- persistente Rate-Limits für Passwort-, MFA- und Passkey-Anmeldung
- zeitweise Sperre nach zu vielen Fehlversuchen
- Administrator-Notfallreset für 2FA
- Migration `0011_security_071.py`

## Passkeys / WebAuthn

Passkeys werden unter `/security/passkeys` verwaltet. Die Anmeldung erfolgt auf `/login` über „Mit Passkey anmelden“. Die E-Mail-Adresse wird vor dem Passkey-Dialog eingegeben; dadurch arbeitet 0.7.1 mit nicht-discoverable und discoverable Credentials gleichermaßen über die gespeicherte Benutzerzuordnung.

Das Hinzufügen eines neuen Passkeys ist als Step-up-Vorgang geschützt: Vor dem Start der WebAuthn-Registrierung muss das aktuelle Portal-Passwort erneut bestätigt werden. Ist TOTP aktiviert, muss zusätzlich ein gültiger TOTP- oder Recovery-Code angegeben werden.

Gespeichert werden nur Credential-ID, öffentlicher Schlüssel, Signaturzähler, Bezeichnung und Zeitstempel. Private Schlüssel verbleiben auf dem Gerät bzw. im Passkey-Provider.

WebAuthn-Challenges werden nur für die laufende Registration/Authentication in der signierten Portal-Session gehalten. Registrierung und Anmeldung prüfen RP-ID, Origin und User Verification.

Konfiguration:

```text
FAMILIENPORTAL_WEBAUTHN_RP_ID=portal.example.de
FAMILIENPORTAL_WEBAUTHN_RP_NAME=Familienportal
FAMILIENPORTAL_WEBAUTHN_ORIGIN=https://portal.example.de
```

Wenn RP-ID und Origin nicht explizit gesetzt werden, werden sie aus `FAMILIENPORTAL_PUBLIC_URL` abgeleitet.

## Login-Rate-Limit

Standardwerte:

```text
FAMILIENPORTAL_LOGIN_MAX_FAILURES=5
FAMILIENPORTAL_LOGIN_WINDOW_MINUTES=15
FAMILIENPORTAL_LOGIN_LOCK_MINUTES=15
```

Die Schlüssel für die Drosselung enthalten keine Klartext-E-Mail-Adresse. Scope, Benutzerkennung und Client-IP werden vor Speicherung per SHA-256 zusammengefasst. Nach erfolgreicher Anmeldung wird der betreffende Zähler gelöscht.

Die Drosselung gilt für:

- Passwortlogin im Browser
- Passwortlogin über REST
- TOTP-/Recovery-Code-Prüfung
- Passkey-Anmeldung

## TOTP-QR-Code

Während `/security/mfa/start` ist der QR-Code unter `/security/mfa/qr` nur für die angemeldete Sitzung und nur während der noch nicht bestätigten 2FA-Einrichtung abrufbar. Nach erfolgreicher Aktivierung ist der QR-Endpunkt für diesen Seed nicht mehr verfügbar. Er wird dynamisch aus dem verschlüsselt gespeicherten TOTP-Seed erzeugt und mit `Cache-Control: no-store` ausgeliefert.

## Admin-2FA-Notfallreset

Administratoren finden `/admin/security/mfa-reset` über die Sicherheitsseite. Für einen Reset sind das aktuelle Administrator-Passwort und – falls beim Administrator aktiviert – ein eigener TOTP- oder Recovery-Code erforderlich.

Beim Reset werden für das Zielkonto:

- TOTP deaktiviert,
- der verschlüsselte Seed entfernt,
- Recovery-Codes verworfen,
- alle aktiven Sitzungen widerrufen,
- ein Audit-Eintrag geschrieben.

## Datenbank

Migration `0011_security_071.py` ergänzt `login_throttles`.

Upgrade:

```bash
cd /opt/familienportal
sudo -u familienportal .venv/bin/alembic upgrade head
sudo systemctl restart familienportal
```

## Abhängigkeiten

0.7.1 verwendet `webauthn` 3.x und aktualisiert deshalb `cryptography` auf 49.x. Für den lokalen TOTP-QR-Code wird `qrcode[pil]` verwendet.

Nach einem Quellcode-Update muss das virtuelle Environment deshalb die aktualisierten Projektabhängigkeiten erhalten:

```bash
cd /opt/familienportal
sudo -u familienportal .venv/bin/pip install -U .
```

## Tests

`tests/test_security_071.py` prüft die Ableitung von RP-ID/Origin, den Import des WebAuthn-Service und die anonymisierte Rate-Limit-Schlüsselbildung. Die bestehende CI installiert die aktuellen Dependencies und führt die gesamte Pytest-Suite unter Python 3.12 aus.

## Noch offen für 0.7.2 / Hardening

- CSRF-Schutz für alle POST-Formulare und Fetch-Endpunkte
- feinere MFA-Richtlinien pro Rolle
- Security-Header/CSP
- automatische Bereinigung alter Throttle- und Recovery-Datensätze
- optional discoverable Passkey-Login ohne vorherige E-Mail-Eingabe
