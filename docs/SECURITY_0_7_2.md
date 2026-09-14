# Sicherheit 0.7.2

## Umfang

0.7.2 härtet den bestehenden Sicherheitskern weiter ab:

- zentraler Same-Origin-/CSRF-Schutz für schreibende Browser-Anfragen
- Security-Header und Content-Security-Policy
- HSTS bei HTTPS-Betrieb
- rollenbasierte 2FA-Pflicht
- automatische Bereinigung alter Login-Throttles, Recovery-Anfragen und abgelaufener/widerrufener Sessions
- täglicher systemd-Cleanup-Timer

## CSRF / Same-Origin

Der produktive Dienst startet seit 0.7.2 über `familienportal.application:app`. Die zusätzliche Middleware prüft bei POST, PUT, PATCH und DELETE die Browser-Header `Origin`, `Referer` und `Sec-Fetch-Site` gegen `FAMILIENPORTAL_PUBLIC_URL`.

Cross-Site-Anfragen werden mit HTTP 403 blockiert. Nicht-Browser-API-Clients ohne Browser-Origin-Header bleiben kompatibel.

## Security-Header

Antworten erhalten unter anderem:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy`
- `Content-Security-Policy`
- bei HTTPS zusätzlich `Strict-Transport-Security`

Die aktuelle CSP erlaubt noch Inline-Skripte und Inline-Styles, weil bestehende Templates diese verwenden. In einer späteren Hardening-Stufe sollen Nonces bzw. ausgelagerte Skripte die Inline-Ausnahmen entfernen.

## Rollenbasierte 2FA

Konfiguration:

```text
FAMILIENPORTAL_MFA_REQUIRED_ROLES=Administrator
```

Mehrere Rollen können kommasepariert angegeben werden, zum Beispiel:

```text
FAMILIENPORTAL_MFA_REQUIRED_ROLES=Administrator,Erwachsene
```

Ein angemeldeter Benutzer mit einer verpflichteten Rolle wird bis zur erfolgreichen 2FA-Einrichtung auf `/security` geführt. Nach aktivierter TOTP-2FA greift beim nächsten Login der bestehende 2FA-Login-Flow.

## Automatische Bereinigung

Der Timer `familienportal-security-cleanup.timer` läuft täglich. Standardmäßig werden alte Sicherheitsdatensätze nach 30 Tagen entfernt.

Konfiguration:

```text
FAMILIENPORTAL_SECURITY_CLEANUP_DAYS=30
```

Bereinigt werden:

- alte Login-Throttle-Datensätze
- abgelaufene oder bereits verwendete Account-Recovery-Anfragen
- alte abgelaufene oder widerrufene Login-Sessions

## Installation / Update

Nach dem Update:

```bash
cd /opt/familienportal
sudo -u familienportal .venv/bin/pip install -U .
sudo systemctl daemon-reload
sudo systemctl restart familienportal
sudo systemctl enable --now familienportal-security-cleanup.timer
```

Der aktuelle `deploy/install.sh` installiert und aktiviert den Cleanup-Timer automatisch.

## Tests

`tests/test_security_072.py` prüft Security-Header sowie erlaubte und blockierte Same-Origin-/Cross-Origin-Anfragen.

## Noch offen

- CSP ohne `unsafe-inline`
- optional echte synchronizer CSRF-Tokens zusätzlich zur Origin-Prüfung
- passwortloser discoverable Passkey-Login ohne E-Mail-Vorabfrage
- weitergehende rollen- und risikobasierte Richtlinien
