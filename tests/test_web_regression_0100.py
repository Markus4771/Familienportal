from familienportal.main import app


def _routes():
    return {(route.path, method) for route in app.routes for method in getattr(route, "methods", set())}


def test_core_web_routes_remain_registered():
    routes = _routes()
    expected = {
        ("/setup", "GET"),
        ("/setup", "POST"),
        ("/login", "GET"),
        ("/login", "POST"),
        ("/logout", "POST"),
        ("/dashboard", "GET"),
        ("/admin/users", "GET"),
        ("/admin/households", "GET"),
    }
    assert expected <= routes


def test_task_web_routes_are_registered_on_main_application():
    routes = _routes()
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


def test_system_routes_remain_registered():
    routes = _routes()
    assert {("/health", "GET"), ("/ready", "GET"), ("/api/v1/system/runtime", "GET"), ("/api/v1/system/capabilities", "GET")} <= routes
