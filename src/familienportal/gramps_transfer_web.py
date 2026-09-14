from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from familienportal.database import get_db
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


@router.post("/platform/gramps/export/gedcom")
def export_gedcom(request: Request, db: Session = Depends(get_db)):
    _admin_user, client = _admin_client(request, db)
    return JSONResponse(start_gedcom_export(client))


@router.get("/platform/gramps/tasks/{task_id}")
def export_task(task_id: str, request: Request, db: Session = Depends(get_db)):
    _admin_user, client = _admin_client(request, db)
    return JSONResponse(task_status(client, task_id))


@router.get("/platform/gramps/export/file")
def export_file(path: str, request: Request, db: Session = Depends(get_db)):
    if not path.startswith("/api/exporters/ged/file/processed/"):
        raise HTTPException(status_code=400, detail="Ungültiger Exportpfad")
    _admin_user, client = _admin_client(request, db)
    content = download_result(client, path)
    return StreamingResponse(iter([content]), media_type="application/x-gedcom", headers={"Content-Disposition": "attachment; filename=familienportal-export.ged"})


@router.post("/platform/gramps/import/gedcom")
async def import_gedcom_file(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    _admin_user, client = _admin_client(request, db)
    if not (file.filename or "").lower().endswith((".ged", ".gedcom")):
        raise HTTPException(status_code=400, detail="Nur GEDCOM-Dateien sind zulässig")
    content = await file.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="GEDCOM-Datei ist größer als 25 MiB")
    return JSONResponse(import_gedcom(client, file.filename or "import.ged", content))
