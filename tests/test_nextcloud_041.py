from familienportal.nextcloud import NextcloudClient
from familienportal.secrets import validate_secret_reference


def test_nextcloud_dav_endpoints() -> None:
    client = NextcloudClient("https://cloud.example.test/", "max mustermann", "secret")
    endpoints = client.dav_endpoints()
    assert endpoints["webdav"].endswith("/remote.php/dav/files/max%20mustermann/")
    assert endpoints["caldav"].endswith("/remote.php/dav/calendars/max%20mustermann/")
    assert endpoints["carddav"].endswith("/remote.php/dav/addressbooks/users/max%20mustermann/")


def test_secret_reference_is_normalized() -> None:
    assert validate_secret_reference("familienportal_nextcloud_app_password") == "FAMILIENPORTAL_NEXTCLOUD_APP_PASSWORD"
