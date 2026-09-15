from familienportal.extensions import BUILTIN_MODULES
from familienportal.genealogy_documents_web import router as genealogy_documents_router
from familienportal.genealogy_picker_web import router as genealogy_picker_router
from familienportal.gramps_api import router as gramps_api_router
from familienportal.gramps_extra_web import router as gramps_extra_router
from familienportal.gramps_person_web import router as gramps_person_router
from familienportal.gramps_transfer_web import router as gramps_transfer_router
from familienportal.gramps_web import router as gramps_router
from familienportal.main import app
from familienportal.role_mfa_policy import RoleMfaPolicyMiddleware
from familienportal.security_http import CsrfOriginMiddleware, SecurityHeadersMiddleware

BUILTIN_MODULES["genealogy"]["route"] = "/genealogy"

app.include_router(gramps_router)
app.include_router(gramps_extra_router)
app.include_router(gramps_api_router)
app.include_router(gramps_transfer_router)
app.include_router(gramps_person_router)
app.include_router(genealogy_documents_router)
app.include_router(genealogy_picker_router)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CsrfOriginMiddleware)
app.add_middleware(RoleMfaPolicyMiddleware)
