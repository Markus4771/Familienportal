import pytest

from familienportal.gramps import GrampsClient, GrampsError
from familienportal.gramps_transfer import import_gedcom, processed_export_path, task_status


def test_processed_export_path_accepts_filename():
    assert processed_export_path("family tree.ged") == "/api/exporters/ged/file/processed/family%20tree.ged"


def test_processed_export_path_rejects_traversal():
    with pytest.raises(GrampsError):
        processed_export_path("../secret")
    with pytest.raises(GrampsError):
        processed_export_path("folder/file.ged")


def test_task_status_rejects_invalid_identifier_before_network():
    client = GrampsClient("https://gramps.example.test", "token")
    with pytest.raises(GrampsError):
        task_status(client, "../../bad")


def test_import_rejects_empty_file_before_network():
    client = GrampsClient("https://gramps.example.test", "token")
    with pytest.raises(GrampsError):
        import_gedcom(client, "empty.ged", b"")
