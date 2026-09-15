import pytest

from familienportal.nextcloud import NextcloudBinary, NextcloudClient, NextcloudError


def test_nextcloud_binary_structure():
    result = NextcloudBinary(b"image", "image/jpeg", "familie.jpg")
    assert result.content == b"image"
    assert result.content_type == "image/jpeg"
    assert result.filename == "familie.jpg"


def test_nextcloud_file_path_is_encoded():
    client = NextcloudClient("https://cloud.example.test", "family user", "secret")
    path = client._dav_file_path("Familie/Fotos/Oma & Opa.jpg")
    assert path == "/remote.php/dav/files/family%20user/Familie/Fotos/Oma%20%26%20Opa.jpg"


def test_nextcloud_rejects_parent_traversal():
    client = NextcloudClient("https://cloud.example.test", "user", "secret")
    with pytest.raises(NextcloudError):
        client._dav_file_path("Familie/../secret.txt")
