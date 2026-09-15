from familienportal.gramps import GrampsClient


def test_rows_supports_common_collection_shapes():
    assert GrampsClient._rows([{"handle": "A"}]) == [{"handle": "A"}]
    assert GrampsClient._rows({"data": [{"handle": "A"}]}) == [{"handle": "A"}]
    assert GrampsClient._rows({"results": [{"handle": "B"}]}) == [{"handle": "B"}]


def test_all_pages_collects_multiple_pages_without_duplicates():
    client = GrampsClient("https://gramps.example.test", "token")
    pages = {
        1: [{"handle": f"P{i}"} for i in range(200)],
        2: [{"handle": "P199"}, {"handle": "P200"}],
    }

    def loader(*, page: int, pagesize: int):
        assert pagesize == 200
        return pages.get(page, [])

    result = client._all_pages(loader)
    assert len(result) == 201
    assert result[-1]["handle"] == "P200"


def test_all_pages_stops_if_server_repeats_same_page():
    client = GrampsClient("https://gramps.example.test", "token")
    row = {"handle": "same"}

    def loader(*, page: int, pagesize: int):
        return [row] * pagesize

    result = client._all_pages(loader, max_pages=10)
    assert result == [row]
