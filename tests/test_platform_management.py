from familienportal.extensions import BUILTIN_MODULES
from familienportal.platform_web import _probe_url


def test_all_builtin_modules_define_permission_and_route() -> None:
    for key, module in BUILTIN_MODULES.items():
        assert module["permission"]
        assert str(module["route"]).startswith("/modules/")
        assert str(module["route"]).endswith(key)


def test_connector_probe_rejects_invalid_scheme() -> None:
    status, message = _probe_url("ftp://example.invalid")
    assert status == "error"
    assert "HTTP" in message
