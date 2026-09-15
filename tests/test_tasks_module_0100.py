from familienportal.extensions import BUILTIN_MODULES


def test_tasks_is_registered_as_builtin_module():
    module = BUILTIN_MODULES["tasks"]
    assert module["name"] == "Aufgaben"
    assert module["route"] == "/tasks"
    assert module["permission"] == "tasks.read"


def test_tasks_is_enabled_and_visible_in_menu_by_default():
    module = BUILTIN_MODULES["tasks"]
    assert module["default"] is True
    assert module["menu"] is True


def test_tasks_has_dashboard_icon_and_description():
    module = BUILTIN_MODULES["tasks"]
    assert module["icon"] == "bi-check2-square"
    assert "Aufgaben" in module["description"]
