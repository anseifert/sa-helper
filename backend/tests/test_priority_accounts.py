from app.utils.priority_accounts import match_priority_account


def test_match_exxon():
    assert match_priority_account(company_name="ExxonMobil IT", title="QBR follow-up") == "exxonmobil"


def test_match_conoco_domain():
    assert match_priority_account(company_domain="conocophillips.com") == "conocophillips"


def test_match_windstream():
    assert match_priority_account(title="Windstream renewal") == "windstream_uniti"


def test_match_epp():
    assert match_priority_account(title="EPP architecture review") == "epp"
    assert match_priority_account(description="eprod deployment") == "epp"


def test_no_match():
    assert match_priority_account(company_name="Acme Corp") is None
