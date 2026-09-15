from __future__ import annotations

from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request as UrlRequest, urlopen
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.database import get_db
from familienportal.extensions import BUILTIN_CONNECTORS, BUILTIN_MODULES
from familienportal.models import Family, Role, User, UserStatus
from familienportal.platform_models import ConnectorState, FamilySetting, ModuleState

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")

GUIDED_CONNECTORS = {"nextcloud", "mailcow", "paperless", "gramps"}

def _admin(request: Request, db: Session) -> User:
    user_id=request.session.get("user_id")
    if not user_id: raise HTTPException(status_code=401,detail="Nicht angemeldet")
    try: user=db.get(User,UUID(user_id))
    except ValueError as exc: raise HTTPException(status_code=401,detail="Ungültige Sitzung") from exc
    if not user or user.status != UserStatus.ACTIVE.value: raise HTTPException(status_code=401,detail="Ungültige Sitzung")
    if not (user.is_superadmin or any(r.name=="Administrator" for r in user.roles)): raise HTTPException(status_code=403,detail="Administratorrecht erforderlich")
    return user

def _module_rows(db:Session,family_id:UUID):
    states={i.module_key:i for i in db.scalars(select(ModuleState).where(ModuleState.family_id==family_id)).all()}
    return [{"key":k,**d,"enabled":states[k].enabled if k in states else bool(d.get("default"))} for k,d in BUILTIN_MODULES.items()]

def _connector_rows(db:Session,family_id:UUID):
    states={i.connector_key:i for i in db.scalars(select(ConnectorState).where(ConnectorState.family_id==family_id)).all()}; rows=[]
    for k,d in BUILTIN_CONNECTORS.items():
        s=states.get(k); rows.append({"key":k,**d,"enabled":bool(s and s.enabled),"base_url":s.base_url if s else "","username":s.username if s else "","secret_reference":s.secret_reference if s else "","health_status":s.health_status if s else "not_checked","health_message":s.health_message if s else None,"guided":k in GUIDED_CONNECTORS})
    return rows

def _probe_url(base_url:str):
    parsed=urlparse(base_url)
    if parsed.scheme not in {"http","https"} or not parsed.hostname: return "error","Ungültige URL. Erlaubt sind HTTP und HTTPS."
    req=UrlRequest(base_url,method="HEAD",headers={"User-Agent":"Familienportal/0.13"})
    try:
        with urlopen(req,timeout=5) as response: return "ok",f"Dienst erreichbar (HTTP {response.getcode()})."
    except HTTPError as exc:
        return ("ok",f"Dienst erreichbar (HTTP {exc.code}; Zugriff ggf. geschützt).") if 400<=exc.code<500 else ("error",f"Dienst antwortet mit HTTP {exc.code}.")
    except (URLError,TimeoutError) as exc: return "error",f"Verbindung fehlgeschlagen: {getattr(exc,'reason',exc)}"

def _state(db,admin,key):
    if key not in BUILTIN_CONNECTORS: raise HTTPException(status_code=404,detail="Connector nicht gefunden")
    s=db.scalar(select(ConnectorState).where(ConnectorState.family_id==admin.family_id,ConnectorState.connector_key==key))
    if not s: s=ConnectorState(family_id=admin.family_id,connector_key=key); db.add(s)
    return s

@router.get("/platform",response_class=HTMLResponse)
def platform_page(request:Request,db:Session=Depends(get_db)):
    admin=_admin(request,db); return templates.TemplateResponse(request=request,name="platform.html",context={"user":admin,"is_admin":True,"modules":_module_rows(db,admin.family_id),"connectors":_connector_rows(db,admin.family_id)})

@router.get("/admin/integrations",response_class=HTMLResponse)
def integration_assistant(request:Request,db:Session=Depends(get_db)):
    admin=_admin(request,db); return templates.TemplateResponse(request=request,name="integrations.html",context={"user":admin,"is_admin":True,"connectors":[r for r in _connector_rows(db,admin.family_id) if r["guided"]]})

@router.post("/admin/integrations/{connector_key}")
def configure_integration(connector_key:str,request:Request,base_url:str=Form(...),username:str=Form(""),secret_reference:str=Form(""),db:Session=Depends(get_db)):
    admin=_admin(request,db)
    if connector_key not in GUIDED_CONNECTORS: raise HTTPException(status_code=404,detail="Integration nicht unterstützt")
    s=_state(db,admin,connector_key); url=base_url.strip().rstrip("/"); status,message=_probe_url(url)
    s.enabled=True; s.base_url=url; s.username=username.strip() or None; s.secret_reference=secret_reference.strip() or None; s.health_status=status; s.health_message=message; s.health_checked_at=datetime.now(timezone.utc)
    audit(db,"connector.guided_configured",actor=admin,target_type="connector",target_id=connector_key,details=status); db.commit(); return RedirectResponse(f"/admin/integrations#{connector_key}",status_code=303)

@router.post("/platform/modules/{module_key}/toggle")
def toggle_module(module_key:str,request:Request,db:Session=Depends(get_db)):
    admin=_admin(request,db)
    if module_key not in BUILTIN_MODULES: raise HTTPException(status_code=404,detail="Modul nicht gefunden")
    s=db.scalar(select(ModuleState).where(ModuleState.family_id==admin.family_id,ModuleState.module_key==module_key))
    if not s: s=ModuleState(family_id=admin.family_id,module_key=module_key,enabled=not bool(BUILTIN_MODULES[module_key].get("default"))); db.add(s)
    else: s.enabled=not s.enabled
    audit(db,"module.toggled",actor=admin,target_type="module",target_id=module_key,details=f"enabled={s.enabled}"); db.commit(); return RedirectResponse("/platform#modules",status_code=303)

@router.post("/platform/connectors/{connector_key}")
def save_connector(connector_key:str,request:Request,enabled:bool=Form(False),base_url:str=Form(""),db:Session=Depends(get_db)):
    admin=_admin(request,db); s=_state(db,admin,connector_key); s.enabled=enabled; s.base_url=base_url.strip().rstrip("/") or None; s.health_status="configured" if enabled and s.base_url else "not_checked"; s.health_message=None; audit(db,"connector.updated",actor=admin,target_type="connector",target_id=connector_key); db.commit(); return RedirectResponse("/platform#connectors",status_code=303)

@router.post("/platform/connectors/{connector_key}/health")
def check_connector(connector_key:str,request:Request,db:Session=Depends(get_db)):
    admin=_admin(request,db); s=_state(db,admin,connector_key)
    if not s.enabled or not s.base_url: s.health_status,s.health_message="error","Connector ist nicht vollständig konfiguriert."
    else: s.health_status,s.health_message=_probe_url(s.base_url)
    s.health_checked_at=datetime.now(timezone.utc); audit(db,"connector.health_checked",actor=admin,target_type="connector",target_id=connector_key,details=s.health_status); db.commit(); return RedirectResponse("/platform#connectors",status_code=303)

@router.get("/settings",response_class=HTMLResponse)
def settings_page(request:Request,db:Session=Depends(get_db)):
    admin=_admin(request,db); family=db.get(Family,admin.family_id); stored={i.setting_key:i.value for i in db.scalars(select(FamilySetting).where(FamilySetting.family_id==admin.family_id)).all()}; return templates.TemplateResponse(request=request,name="settings.html",context={"user":admin,"is_admin":True,"family":family,"settings":stored})

@router.post("/settings")
def save_settings(request:Request,portal_title:str=Form("Familienportal"),timezone_name:str=Form("Europe/Berlin"),language:str=Form("de"),profile:str=Form("small_family"),db:Session=Depends(get_db)):
    admin=_admin(request,db)
    if profile not in {"small_family","extended_family"}: raise HTTPException(status_code=400,detail="Ungültiges Familienprofil")
    family=db.get(Family,admin.family_id)
    if family: family.profile=profile
    for key,value in {"portal_title":portal_title.strip() or "Familienportal","timezone":timezone_name.strip() or "Europe/Berlin","language":language.strip() or "de"}.items():
        item=db.scalar(select(FamilySetting).where(FamilySetting.family_id==admin.family_id,FamilySetting.setting_key==key))
        if item: item.value=value
        else: db.add(FamilySetting(family_id=admin.family_id,setting_key=key,value=value))
    audit(db,"settings.updated",actor=admin,target_type="family",target_id=str(admin.family_id)); db.commit(); return RedirectResponse("/settings?saved=1",status_code=303)

@router.get("/admin/roles",response_class=HTMLResponse)
def roles_page(request:Request,db:Session=Depends(get_db)):
    admin=_admin(request,db); roles=db.scalars(select(Role).where(Role.family_id==admin.family_id).order_by(Role.name)).all(); return templates.TemplateResponse(request=request,name="roles.html",context={"user":admin,"is_admin":True,"roles":roles,"modules":BUILTIN_MODULES})

@router.post("/admin/roles/{role_id}")
def save_role(role_id:UUID,request:Request,permissions:str=Form(""),db:Session=Depends(get_db)):
    admin=_admin(request,db); role=db.get(Role,role_id)
    if not role or role.family_id!=admin.family_id: raise HTTPException(status_code=404,detail="Rolle nicht gefunden")
    role.permissions=",".join(sorted({i.strip() for i in permissions.split(",") if i.strip()})); audit(db,"role.permissions.updated",actor=admin,target_type="role",target_id=str(role.id)); db.commit(); return RedirectResponse("/admin/roles?saved=1",status_code=303)

@router.post("/admin/users/{user_id}/roles")
def save_user_roles(user_id:UUID,request:Request,role_ids:list[str]=Form(default=[]),db:Session=Depends(get_db)):
    admin=_admin(request,db); user=db.get(User,user_id)
    if not user or user.family_id!=admin.family_id: raise HTTPException(status_code=404,detail="Benutzer nicht gefunden")
    try: ids=[UUID(v) for v in role_ids]
    except ValueError as exc: raise HTTPException(status_code=400,detail="Ungültige Rollen-ID") from exc
    roles=db.scalars(select(Role).where(Role.family_id==admin.family_id,Role.id.in_(ids))).all() if ids else []; user.roles=list(roles); audit(db,"user.roles.updated",actor=admin,target_type="user",target_id=str(user.id),details=",".join(r.name for r in roles)); db.commit(); return RedirectResponse("/admin#users",status_code=303)
