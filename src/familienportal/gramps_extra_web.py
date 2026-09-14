from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.gramps_dates import birthday_and_memorial_rows
from familienportal.gramps_web import _client, _state
from familienportal.web import _user_from_session

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


@router.get("/modules/genealogy")
def genealogy_module_redirect():
    return RedirectResponse("/genealogy", status_code=303)


@router.get("/genealogy/families", response_class=HTMLResponse)
def family_search(request: Request, q: str = Query(""), db: Session = Depends(get_db)):
    user = _user_from_session(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    state = _state(db, user.family_id)
    results = _client(state).search(q, "families") if state and state.enabled and q.strip() else []
    return templates.TemplateResponse(request=request, name="genealogy_families.html", context={"user": user, "is_admin": user.is_superadmin, "query": q, "results": results})


@router.get("/genealogy/dates", response_class=HTMLResponse)
def genealogy_dates(request: Request, db: Session = Depends(get_db)):
    user = _user_from_session(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    state = _state(db, user.family_id)
    rows = birthday_and_memorial_rows(_client(state).people(pagesize=200)) if state and state.enabled else []
    return templates.TemplateResponse(request=request, name="genealogy_dates.html", context={"user": user, "is_admin": user.is_superadmin, "rows": rows})
