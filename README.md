# Familienportal

Modulare, selbst gehostete Plattform für Kleinfamilien und Großfamilien.

## Geplante Kernfunktionen

- Profile für Kleinfamilie und Großfamilie
- erweiterbares Modul- und Connector-Framework
- Nextcloud-Integration für Cloud, Dateien, Kalender und Kontakte
- Mailcow-Integration für E-Mail
- Nachrichtenportal und Kleinanzeigen
- Support- und Ticketsystem
- öffentliche Schnittstelle und SDK für externe Module

## Technologie

- Python 3.12+
- FastAPI
- SQLAlchemy 2
- PostgreSQL produktiv
- SQLite für Entwicklung und Tests
- Alembic für Datenbankmigrationen
- Jinja2, HTMX und Bootstrap für die Weboberfläche

## Entwicklungsstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn familienportal.main:app --reload
```

Danach ist die Anwendung unter `http://127.0.0.1:8000` erreichbar.

## Projektstatus

Aktuelle Entwicklungsphase: **0.1 – Core, Profile und Erweiterungsschnittstellen**.

Siehe auch:

- [PROJECT.md](PROJECT.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [REQUIREMENTS.md](REQUIREMENTS.md)
- [BACKLOG.md](BACKLOG.md)
- [ROADMAP.md](ROADMAP.md)
