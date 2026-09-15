import pytest

from familienportal.nextcloud import NextcloudClient, NextcloudError
from familienportal.nextcloud_family_scope import path_in_roots, picker_path


@pytest.fixture
def client():
    return NextcloudClient("https://cloud.example.test", "user", "secret")


def test_path_inside_family_root_is_allowed(client):
    assert path_in_roots(client, "Familie/Urkunden/test.pdf", ["Familie"]) == "Familie/Urkunden/test.pdf"


def test_root_itself_is_allowed(client):
    assert path_in_roots(client, "Familie", ["Familie"]) == "Familie"


def test_similar_prefix_is_not_allowed(client):
    with pytest.raises(NextcloudError):
        path_in_roots(client, "Familie-Privat/test.pdf", ["Familie"])


def test_other_folder_is_not_allowed(client):
    with pytest.raises(NextcloudError):
        path_in_roots(client, "Privat/test.pdf", ["Familie"])


def test_encoded_traversal_is_not_allowed(client):
    with pytest.raises(NextcloudError):
        path_in_roots(client, "Familie/%2e%2e/Privat/test.pdf", ["Familie"])


def test_picker_defaults_to_first_family_root(client):
    assert picker_path(client, "", ["Familie", "Archiv"]) == "Familie"


def test_picker_requires_configured_root(client):
    with pytest.raises(NextcloudError):
        picker_path(client, "", [])
