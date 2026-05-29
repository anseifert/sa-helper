from app.utils.priority_accounts import match_priority_account, tasks_section_id_for_company


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


def test_tasks_section_id_for_company():
    assert tasks_section_id_for_company("Exxon") == "exxonmobil"
    assert tasks_section_id_for_company("Acme Corp") == "acme_corp"
    assert tasks_section_id_for_company("Unassigned") == "unassigned"
