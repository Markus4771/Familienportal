from familienportal.gramps_media import media_handles, normalize_media


def test_media_handles_accepts_common_gramps_shapes():
    person = {"media_list": [{"ref": "M1"}, {"handle": "M2"}, "M3", {"ref": "M1"}]}
    assert media_handles(person) == ["M1", "M2", "M3"]


def test_normalize_media():
    item = {"handle": "M1", "gramps_id": "O0001", "description": "Hochzeitsfoto", "path": "photos/wedding.jpg", "mime": "image/jpeg"}
    result = normalize_media(item)
    assert result["title"] == "Hochzeitsfoto"
    assert result["path"] == "photos/wedding.jpg"
    assert result["mime"] == "image/jpeg"
