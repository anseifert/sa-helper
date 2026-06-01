import json

from app.utils.gmail_recipients import (
    gmail_to_eligible_for_tasks,
    parse_to_addresses,
    user_in_to_or_cc,
)
from app.utils.task_filters import is_ineligible_gmail_recipient


def test_parse_to_addresses():
    assert parse_to_addresses("Andrew <aseifert@redhat.com>, Bob <bob@customer.com>") == [
        "aseifert@redhat.com",
        "bob@customer.com",
    ]


def test_user_in_cc_is_eligible():
    user = "aseifert@redhat.com"
    assert user_in_to_or_cc("peer@redhat.com", f"Andrew <{user}>", user)
    assert gmail_to_eligible_for_tasks(
        to_header="peer@redhat.com",
        cc_header=user,
        user_email=user,
    )


def test_user_must_appear_as_recipient():
    user = "aseifert@redhat.com"
    assert not gmail_to_eligible_for_tasks(
        to_header="peer@redhat.com",
        cc_header="other@redhat.com",
        user_email=user,
    )


def test_google_group_in_to_excluded():
    user = "aseifert@redhat.com"
    assert not gmail_to_eligible_for_tasks(
        to_header=f"{user}, sa-team@googlegroups.com",
        user_email=user,
    )


def test_list_id_google_group_excluded():
    assert not gmail_to_eligible_for_tasks(
        to_header="aseifert@redhat.com",
        user_email="aseifert@redhat.com",
        list_id="<sa-team.googlegroups.com>",
    )


def test_metadata_filter():
    meta = json.dumps(
        {
            "gmail_to_eligible": True,
            "user_in_recipients": True,
            "to_has_google_group": False,
        }
    )
    assert not is_ineligible_gmail_recipient(
        source="gmail",
        metadata_json=meta,
        user_email="aseifert@redhat.com",
    )
    assert is_ineligible_gmail_recipient(
        source="gmail",
        metadata_json=None,
        user_email="aseifert@redhat.com",
    )
