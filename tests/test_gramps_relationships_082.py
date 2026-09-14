from familienportal.gramps_relationships import family_handles, relationship_summary


def test_family_handles_collects_supported_shapes():
    person = {
        "family_list": ["F1", {"handle": "F2"}],
        "parent_family_list": [{"handle": "F3"}],
    }
    assert family_handles(person) == ["F1", "F2", "F3"]


def test_relationship_summary_resolves_parents_partner_and_children():
    people = {
        "P1": {"handle": "P1", "name": "Alex"},
        "P2": {"handle": "P2", "name": "Robin"},
        "P3": {"handle": "P3", "name": "Chris"},
        "P4": {"handle": "P4", "name": "Dana"},
        "P5": {"handle": "P5", "name": "Emil"},
    }
    families = [
        {"father_handle": "P4", "mother_handle": "P5", "child_ref_list": [{"ref": "P1"}]},
        {"father_handle": "P1", "mother_handle": "P2", "child_ref_list": [{"ref": "P3"}]},
    ]
    result = relationship_summary(people["P1"], families, people)
    assert [item.name for item in result["parents"]] == ["Dana", "Emil"]
    assert [item.name for item in result["partners"]] == ["Robin"]
    assert [item.name for item in result["children"]] == ["Chris"]
