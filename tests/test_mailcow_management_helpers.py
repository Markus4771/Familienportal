from familienportal.mailcow_management import normalize_destinations


def test_multiple_destinations_are_normalized():
    assert normalize_destinations("one@example.de; two@example.de") == "one@example.de,two@example.de"
