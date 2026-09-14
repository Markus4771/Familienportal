from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.mailcow import MailcowClient, MailcowError
from familienportal.platform_models import ConnectorState
from familienportal.secrets import read_secret


def get_mailcow_client(db: Session, family_id) -> MailcowClient:
    state = db.scalar(select(ConnectorState).where(ConnectorState.family_id == family_id, ConnectorState.connector_key == "mailcow"))
    if not state or not state.enabled or not state.base_url or not state.secret_reference:
        raise MailcowError("Mailcow ist nicht vollständig konfiguriert")
    api_key = read_secret(state.secret_reference)
    if not api_key:
        raise MailcowError("Mailcow API-Key ist nicht verfügbar")
    return MailcowClient(state.base_url, api_key)


def get_mailcow_summary(db: Session, family_id):
    return get_mailcow_client(db, family_id).summary()
