from __future__ import annotations

import os
import re

_SECRET_NAME = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")


def validate_secret_reference(reference: str) -> str:
    value = reference.strip().upper()
    if not _SECRET_NAME.fullmatch(value):
        raise ValueError("Secret-Referenz muss ein gültiger Name einer Umgebungsvariable sein.")
    return value


def read_secret(reference: str | None) -> str | None:
    if not reference:
        return None
    name = validate_secret_reference(reference)
    value = os.environ.get(name)
    return value if value else None


def secret_is_available(reference: str | None) -> bool:
    return bool(read_secret(reference))
