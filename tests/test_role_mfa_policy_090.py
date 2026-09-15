from familienportal.role_mfa_policy import session_user_id


class DummyRequest:
    def __init__(self, scope):
        self.scope = scope


def test_missing_session_scope_is_safe():
    assert session_user_id(DummyRequest({})) is None


def test_invalid_session_scope_is_safe():
    assert session_user_id(DummyRequest({"session": "invalid"})) is None


def test_session_user_is_read_from_scope():
    assert session_user_id(DummyRequest({"session": {"user_id": "123"}})) == "123"
