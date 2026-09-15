from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from familienportal.api import current_user
from familienportal.database import get_db
from familienportal.genealogy_privacy import privacy_policy, visible_person
from familienportal.gramps import GrampsError
from familienportal.gramps_dates import birthday_and_memorial_rows
from familienportal.gramps_web import _client, _state
from familienportal.models import User
from familienportal.permissions import has_permission

router = APIRouter(prefix="/api/v1/gramps", tags=["gramps"])


def _allowed(user: User) -> None:
    if not has_permission(user, "genealogy.read"):
        raise HTTPException(status_code=403, detail="Berechtigung genealogy.read erforderlich")


def _connected(user: User, db: Session):
    state = _state(db, user.family_id)
    if not state or not state.enabled:
        raise HTTPException(status_code=409, detail="Gramps Web ist nicht aktiviert")
    return _client(state)


def _api_error(exc: GrampsError) -> HTTPException:
    return HTTPException(status_code=502, detail=str(exc))


@router.get("/search")
def search(q: str = Query(..., min_length=1, max_length=200), object_type: str = Query("people"), user: User = Depends(current_user), db: Session = Depends(get_db)):
    _allowed(user)
    if object_type not in {"people", "families"}:
        raise HTTPException(status_code=400, detail="object_type muss people oder families sein")
    try:
        results = _connected(user, db).search(q.strip(), object_type)
    except GrampsError as exc:
        raise _api_error(exc) from exc
    if object_type == "people":
        mode, age = privacy_policy(db, user.family_id)
        results = [item for raw in results if (item := visible_person(user, raw, mode, age)) is not None]
    return {"results": results}


@router.get("/people/{handle}")
def person(handle: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _allowed(user)
    try:
        raw = _connected(user, db).person(handle)
    except GrampsError as exc:
        raise _api_error(exc) from exc
    mode, age = privacy_policy(db, user.family_id)
    result = visible_person(user, raw, mode, age)
    if result is None:
        raise HTTPException(status_code=404, detail="Person nicht gefunden")
    return result


@router.get("/families/{handle}")
def family(handle: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _allowed(user)
    try:
        return _connected(user, db).family(handle)
    except GrampsError as exc:
        raise _api_error(exc) from exc


@router.get("/dates")
def dates(user: User = Depends(current_user), db: Session = Depends(get_db)):
    _allowed(user)
    try:
        people = _connected(user, db).all_people()
    except GrampsError as exc:
        raise _api_error(exc) from exc
    mode, age = privacy_policy(db, user.family_id)
    visible = [item for raw in people if (item := visible_person(user, raw, mode, age)) is not None]
    return {"items": birthday_and_memorial_rows(visible)}
