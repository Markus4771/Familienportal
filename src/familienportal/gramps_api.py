from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from familienportal.api import current_user
from familienportal.database import get_db
from familienportal.gramps_dates import birthday_and_memorial_rows
from familienportal.gramps_web import _client, _state
from familienportal.models import User
from familienportal.permissions import has_permission

router = APIRouter(prefix="/api/v1/gramps", tags=["gramps"])


def _allowed(user: User) -> None:
    if not has_permission(user, "genealogy.read"):
        raise HTTPException(status_code=403, detail="Berechtigung genealogy.read erforderlich")


@router.get("/search")
def search(q: str = Query(..., min_length=1), object_type: str = Query("people"), user: User = Depends(current_user), db: Session = Depends(get_db)):
    _allowed(user)
    state = _state(db, user.family_id)
    if not state or not state.enabled:
        raise HTTPException(status_code=409, detail="Gramps Web ist nicht aktiviert")
    if object_type not in {"people", "families"}:
        raise HTTPException(status_code=400, detail="object_type muss people oder families sein")
    return {"results": _client(state).search(q, object_type)}


@router.get("/people/{handle}")
def person(handle: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _allowed(user)
    state = _state(db, user.family_id)
    if not state or not state.enabled:
        raise HTTPException(status_code=409, detail="Gramps Web ist nicht aktiviert")
    return _client(state).person(handle)


@router.get("/families/{handle}")
def family(handle: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _allowed(user)
    state = _state(db, user.family_id)
    if not state or not state.enabled:
        raise HTTPException(status_code=409, detail="Gramps Web ist nicht aktiviert")
    return _client(state).family(handle)


@router.get("/dates")
def dates(user: User = Depends(current_user), db: Session = Depends(get_db)):
    _allowed(user)
    state = _state(db, user.family_id)
    if not state or not state.enabled:
        raise HTTPException(status_code=409, detail="Gramps Web ist nicht aktiviert")
    return {"items": birthday_and_memorial_rows(_client(state).people(pagesize=200))}
