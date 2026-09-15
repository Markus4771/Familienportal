from familienportal.paperless import PaperlessBinary, PaperlessClient


def test_paperless_client_normalizes_base_url():
    client = PaperlessClient("https://paperless.example.test/", "secret")
    assert client.base_url == "https://paperless.example.test"


def test_paperless_documents_reads_results(monkeypatch):
    client = PaperlessClient("https://paperless.example.test", "secret")
    monkeypatch.setattr(client, "_get", lambda path, params=None: {"results": [{"id": 7, "title": "Urkunde"}]})
    assert client.documents("Urkunde")[0]["id"] == 7


def test_paperless_document_reads_detail(monkeypatch):
    client = PaperlessClient("https://paperless.example.test", "secret")
    monkeypatch.setattr(client, "_get", lambda path, params=None: {"id": 7, "title": "Urkunde"})
    assert client.document(7)["title"] == "Urkunde"


def test_binary_result_structure():
    result = PaperlessBinary(b"PDF", "application/pdf", "urkunde.pdf")
    assert result.content == b"PDF"
    assert result.content_type == "application/pdf"
    assert result.filename == "urkunde.pdf"
