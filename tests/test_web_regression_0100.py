from familienportal.content_web import router as content_router
from familienportal.main import app
from familienportal.tasks_web import router as tasks_router
from familienportal.web import router as web_router


def _routes(routes):
    return {
        (route.path, method)
        for route in routes
        for method in (getattr(route, "methods", None) or set())
    }


def test_core_web_routes_remain_registered():
    routes = _routes(web_router.routes)
    expected = {
        ("/setup", "GET"),
        ("/setup", "POST"),
        ("/login", "GET"),
        ("/login", "POST"),
        ("/logout", "POST"),
        ("/dashboard", "GET"),
        ("/admin", "GET"),
        ("/admin/users", "POST"),
        ("/admin/households", "POST"),
    }
    assert expected <= routes


def test_task_web_routes_remain_registered():
    routes = _routes(tasks_router.routes)
    expected = {
        ("/tasks", "GET"),
        ("/tasks", "POST"),
        ("/tasks/{task_id}/edit", "GET"),
        ("/tasks/{task_id}/edit", "POST"),
        ("/tasks/{task_id}/status", "POST"),
        ("/tasks/{task_id}/quick-complete", "POST"),
        ("/tasks/{task_id}/archive", "POST"),
        ("/tasks/{task_id}/restore", "POST"),
        ("/tasks/{task_id}/delete", "POST"),
    }
    assert expected <= routes


def test_content_web_routes_are_registered():
    routes = _routes(content_router.routes)
    assert {
        ("/notes", "GET"),
        ("/notes", "POST"),
        ("/notes/{note_id}/edit", "POST"),
        ("/notes/{note_id}/archive", "POST"),
        ("/lists", "GET"),
        ("/lists", "POST"),
        ("/lists/{list_id}/items", "POST"),
        ("/lists/{list_id}/items/{item_id}/toggle", "POST"),
    } <= routes


def test_system_routes_remain_registered_on_main_application():
    routes = _routes(app.routes)
    assert {
        ("/health", "GET"),
        ("/ready", "GET"),
        ("/api/v1/system/runtime", "GET"),
        ("/api/v1/system/capabilities", "GET"),
    } <= routes
