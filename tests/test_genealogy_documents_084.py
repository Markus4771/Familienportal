from familienportal.genealogy_document_models import GenealogyDocumentLink


def test_genealogy_document_link_model_fields():
    link = GenealogyDocumentLink(person_handle="P1", provider="nextcloud", external_ref="Familie/Urkunden/P1.pdf", title="Geburtsurkunde", category="Urkunde")
    assert link.person_handle == "P1"
    assert link.provider == "nextcloud"
    assert link.title == "Geburtsurkunde"


def test_supported_external_reference_can_be_document_id():
    link = GenealogyDocumentLink(person_handle="P2", provider="paperless", external_ref="4711", title="Heiratsurkunde")
    assert link.external_ref == "4711"
