from familienportal.gramps import GrampsClient
from familienportal.gramps_dates import birthday_and_memorial_rows, life_dates


def test_gramps_rows_accept_list_and_wrapped_results():
    assert GrampsClient._rows([{"handle": "A"}]) == [{"handle": "A"}]
    assert GrampsClient._rows({"results": [{"handle": "B"}]}) == [{"handle": "B"}]
    assert GrampsClient._rows({"data": [{"handle": "C"}]}) == [{"handle": "C"}]


def test_life_dates_support_profile_payload():
    item = life_dates({"handle": "P1", "gramps_id": "I0001", "profile": {"name": "Ada Beispiel", "birth": "1900-01-02", "death": "1980-03-04"}})
    assert item["name"] == "Ada Beispiel"
    assert item["birth"] == "1900-01-02"
    assert item["death"] == "1980-03-04"


def test_birthday_and_memorial_rows_drop_people_without_dates():
    rows = birthday_and_memorial_rows([
        {"gramps_id": "I1", "name": "Mit Datum", "birth": "2000-01-01"},
        {"gramps_id": "I2", "name": "Ohne Datum"},
    ])
    assert [row["gramps_id"] for row in rows] == ["I1"]


def test_search_url_uses_supported_object_type(monkeypatch):
    client = GrampsClient("https://gramps.example.test", "test-token")
    seen = {}

    def fake_request(path):
        seen["path"] = path
        return []

    monkeypatch.setattr(client, "_request", fake_request)
    client.search("Muster", "families")
    assert seen["path"].startswith("/api/search/")
    assert "type=families" in seen["path"]
