from app.utils.domain import company_key_for_email, domain_to_company_name, is_consumer_domain


def test_domain_to_company():
    assert domain_to_company_name("acme-corp.com") == "Acme Corp"


def test_consumer_domain():
    assert is_consumer_domain("gmail.com") is True
    assert is_consumer_domain("acme.com") is False


def test_company_key_internal():
    assert company_key_for_email("sa@redhat.com", "redhat.com") is None


def test_company_key_external():
    assert company_key_for_email("bob@acme.com", "redhat.com") == "acme.com"
