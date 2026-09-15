import pytest

from familienportal.nextcloud import NextcloudClient, NextcloudError


@pytest.fixture
def client():
    return NextcloudClient("https://cloud.example.test", "user", "secret")


@pytest.mark.parametrize("path", [
    "../secret.txt",
    "folder/../secret.txt",
    "%2e%2e/secret.txt",
    "%252e%252e/secret.txt",
    "/absolute/path.txt",
    "\\absolute\\path.txt",
    "folder//file.txt",
    "folder/%2e/file.txt",
])
def test_rejects_unsafe_paths(client, path):
    with pytest.raises(NextcloudError):
        client._safe_relative_path(path)


def test_accepts_normal_relative_path(client):
    assert client._safe_relative_path("Familie/Urkunden/test.pdf") == "Familie/Urkunden/test.pdf"
