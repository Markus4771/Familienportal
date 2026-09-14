# Sicherheit 0.7.0

## Umfang

0.7.0 führt den Sicherheitskern für das Familienportal ein:

- TOTP-Zwei-Faktor-Authentifizierung
- einmalige Recovery-Codes
- Passwort-Zurücksetzung per E-Mail
- serverseitige, widerrufbare Sitzungen
- Sitzungsübersicht und Session-Widerruf
- optionale 2FA-Pflicht für Administratoren
- Datenmodell für spätere Passkeys/WebAuthn

## TOTP und Recovery-Codes

TOTP-Seeds werden nicht im Klartext gespeichert. Sie werden mit `FAMILIENPORTAL_SECURITY_ENCRYPTION_KEY` verschlüsselt. Recovery-Codes werden nur als SHA-256-Verifier gespeichert und nach erfolgreicher Verwendung aus der Liste entfernt.

Die Einrichtung erfolgt unter `/security`. Nach erfolgreicher TOTP-Bestätigung werden die Recovery-Codes einmalig angezeigt und müssen vom Benutzer sicher gespeichert werden.

## Passwort-Reset

`/forgot-password` antwortet unabhängig davon, ob ein Konto existiert, neutral. Für vorhandene aktive Konten wird ein zufälliger Reset-Token erzeugt. In der Datenbank wird nur dessen Hash gespeichert. Die Standardgültigkeit beträgt 30 Minuten und kann über `FAMILIENPORTAL_PASSWORD_RESET_TTL_MINUTES` geändert werden.

Nach einem erfolgreichen Passwort-Reset werden alle aktiven Sitzungen des Kontos widerrufen.

## Sitzungen

Neue Logins erzeugen einen Datensatz in `login_sessions`. Die Browser-Session enthält nur Benutzer-ID und Session-ID. Widerrufene oder abgelaufene Sessions werden serverseitig abgewiesen.

Unter `/security` können Benutzer ihre Sitzungen sehen, einzelne Sitzungen widerrufen oder alle anderen Sitzungen abmelden.

## Administrator-2FA

`FAMILIENPORTAL_REQUIRE_ADMIN_MFA=true` erzwingt TOTP für Administratoren beim Login. Vor dem Aktivieren dieser Richtlinie muss mindestens ein Administrator 2FA eingerichtet haben, damit kein Administratorkonto ausgesperrt wird.

## Konfiguration

Wichtige Variablen:

```text
FAMILIENPORTAL_SECURITY_ENCRYPTION_KEY=<langer zufälliger Wert>
FAMILIENPORTAL_PASSWORD_RESET_TTL_MINUTES=30
FAMILIENPORTAL_MFA_ISSUER=Familienportal
FAMILIENPORTAL_REQUIRE_ADMIN_MFA=false
```

Bei Neuinstallationen erzeugt `deploy/install.sh` den Security-Schlüssel automatisch. Bei bestehenden Installationen muss ein stabiler, zufälliger Wert manuell in `/etc/familienportal/familienportal.env` gesetzt werden. Der Schlüssel darf später nicht ohne Migration geändert werden, da sonst vorhandene TOTP-Seeds nicht mehr entschlüsselt werden können.

In `production` verweigert die Anwendung den Start, wenn weiterhin der eingebaute Entwicklungswert für `FAMILIENPORTAL_SESSION_SECRET_KEY` oder `FAMILIENPORTAL_SECURITY_ENCRYPTION_KEY` verwendet wird. Dadurch kann 0.7.0 nicht versehentlich mit Standard-Secrets produktiv betrieben werden.

## Datenbank

Migration `0010_security_070.py` legt folgende Tabellen an:

- `user_mfa_states`
- `account_recovery_requests`
- `login_sessions`
- `passkey_credentials`

Upgrade:

```bash
sudo -u familienportal /opt/familienportal/.venv/bin/alembic -c /opt/familienportal/alembic.ini upgrade head
```

## Tests

`tests/test_security_070.py` prüft TOTP-Erzeugung, Verschlüsselungs-Roundtrip, Einmalverwendung von Recovery-Codes, Token-Hashing sowie die Production-Validierung der Security-Secrets. Zusätzlich läuft `.github/workflows/ci.yml` unter Python 3.12 bei Pushes und Pull Requests.

## Manueller Test auf Debian

Nach dem Upgrade sollten mindestens diese Abläufe geprüft werden:

1. Anmeldung ohne aktivierte 2FA.
2. TOTP unter `/security` einrichten und Recovery-Codes sichern.
3. Abmelden und Login mit TOTP durchführen.
4. Login mit einem Recovery-Code durchführen und denselben Code anschließend erneut ablehnen lassen.
5. Unter `/security` eine zweite Sitzung widerrufen.
6. Passwort-Reset unter `/forgot-password` anfordern und Link aus der E-Mail verwenden.
7. Prüfen, dass nach dem Passwort-Reset alte Sitzungen ungültig sind.
8. Erst danach optional `FAMILIENPORTAL_REQUIRE_ADMIN_MFA=true` setzen.

## Noch nicht in 0.7.0

- echte WebAuthn-/Passkey-Registrierung und Anmeldung
- Login-Rate-Limits und temporäre Kontosperren
- Administrator-Notfall-Reset für 2FA
- feinere 2FA-Richtlinien pro Rolle
- globaler CSRF-Schutz für alle bestehenden Formulare

Diese Punkte sind für 0.7.1 bzw. das anschließende Hardening vorgesehen.
