from familienportal.mailcow import MailcowClient, MailcowError


def test_create_mailbox_payload(monkeypatch):
    client = MailcowClient("https://mail.example.test", "key")
    captured = {}

    def fake_request(path, method="GET", payload=None):
        captured.update(path=path, method=method, payload=payload)
        return [{"type": "success", "msg": "mailbox_added"}]

    monkeypatch.setattr(client, "_request", fake_request)
    client.create_mailbox(address="max@example.test", name="Max", password="Example-123!", quota_mb=2048)
    assert captured["path"] == "/api/v1/add/mailbox"
    assert captured["method"] == "POST"
    assert captured["payload"]["local_part"] == "max"
    assert captured["payload"]["domain"] == "example.test"
    assert captured["payload"]["quota"] == "2048"


def test_create_mailbox_rejects_invalid_address():
    client = MailcowClient("https://mail.example.test", "key")
    try:
        client.create_mailbox(address="invalid", name="Test", password="Example-123!", quota_mb=1024)
    except MailcowError:
        pass
    else:
        raise AssertionError("invalid address must fail")


def test_edit_mailbox_uses_items_and_attr(monkeypatch):
    client = MailcowClient("https://mail.example.test", "key")
    captured = {}

    def fake_request(path, method="GET", payload=None):
        captured.update(path=path, method=method, payload=payload)
        return [{"type": "success"}]

    monkeypatch.setattr(client, "_request", fake_request)
    client.edit_mailbox("max@example.test", name="Max Mustermann", quota_mb=4096, active=True)
    assert captured["path"] == "/api/v1/edit/mailbox"
    assert captured["payload"]["items"] == ["max@example.test"]
    assert captured["payload"]["attr"]["active"] == "1"
    assert captured["payload"]["attr"]["quota"] == "4096"
