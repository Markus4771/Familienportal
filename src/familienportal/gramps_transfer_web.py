from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.gramps import GrampsError
from familienportal.gramps_transfer import download_result, import_gedcom, start_gedcom_export, task_status
from familienportal.gramps_web import _client, _state
from familienportal.platform_web import _admin

router = APIRouter(include_in_schema=False)


def _admin_client(request: Request, db: Session):
    admin = _admin(request, db)
    state = _state(db, admin.family_id)
    if not state or not state.enabled:
        raise HTTPException(status_code=409, detail="Gramps Web ist nicht aktiviert")
    return admin, _client(state)


def _gateway_error(exc: GrampsError) -> HTTPException:
    return HTTPException(status_code=502, detail=str(exc))


@router.post("/platform/gramps/export/gedcom")
def export_gedcom(request: Request, db: Session = Depends(get_db)):
    _admin_user, client = _admin_client(request, db)
    try:
        return JSONResponse(start_gedcom_export(client))
    except GrampsError as exc:
        raise _gateway_error(exc) from exc


@router.get("/platform/gramps/tasks/{task_id}")
def export_task(task_id: str, request: Request, db: Session = Depends(get_db)):
    _admin_user, client = _admin_client(request, db)
    try:
        return JSONResponse(task_status(client, task_id))
    except GrampsError as exc:
        raise _gateway_error(exc) from exc


@router.get("/platform/gramps/export/file")
def export_file(path: str, request: Request, db: Session = Depends(get_db)):
    _admin_user, client = _admin_client(request, db)
    try:
        content = download_result(client, path)
    except GrampsError as exc:
        raise HTTPException(status_code=400 if "Ungültiger Exportpfad" in str(exc) or "Exportdateiname" in str(exc) else 502, detail=str(exc)) from exc
    return StreamingResponse(iter([content]), media_type="application/x-gedcom", headers={"Content-Disposition": "attachment; filename=familienportal-export.ged", "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.post("/platform/gramps/import/gedcom")
async def import_gedcom_file(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    _admin_user, client = _admin_client(request, db)
    filename = file.filename or ""
    if not filename.lower().endswith((".ged", ".gedcom")):
        raise HTTPException(status_code=400, detail="Nur GEDCOM-Dateien sind zulässig")
    content = await file.read(25 * 1024 * 1024 + 1)
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="GEDCOM-Datei ist größer als 25 MiB")
    if not content.strip():
        raise HTTPException(status_code=400, detail="GEDCOM-Datei ist leer")
    try:
        return JSONResponse(import_gedcom(client, filename, content))
    except GrampsError as exc:
        raise _gateway_error(exc) from exc
