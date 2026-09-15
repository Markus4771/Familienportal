from familienportal.paperless import PaperlessClient


def test_paperless_client_normalizes_base_url():
    client = PaperlessClient("https://paperless.example.test/", "secret")
    assert client.base_url == "https://paperless.example.test"


def test_paperless_documents_reads_results(monkeypatch):
    client = PaperlessClient("https://paperless.example.test", "secret")
    monkeypatch.setattr(client, "_get", lambda path, params=None: {"results": [{"id": 7, "title": "Urkunde"}]})
    assert client.documents("Urkunde")[0]["id"] == 7
