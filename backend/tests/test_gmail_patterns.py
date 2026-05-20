from datetime import datetime, timedelta, timezone

from app.extractors.gmail_patterns import classify_gmail_thread


def test_user_owes_reply_on_customer_ask():
    results = classify_gmail_thread(
        user_email="sa@redhat.com",
        user_domain="redhat.com",
        last_from_user=False,
        last_message_at=datetime.now(timezone.utc),
        subject="Question about deployment",
        snippet="Can you send the sizing guide?",
        has_user_reply_after_customer=False,
        customer_asked_no_reply=False,
    )
    types = {r[0] for r in results}
    assert "user_owes_reply" in types


def test_stale_thread_when_user_sent_last():
    old = datetime.now(timezone.utc) - timedelta(days=10)
    results = classify_gmail_thread(
        user_email="sa@redhat.com",
        user_domain="redhat.com",
        last_from_user=True,
        last_message_at=old,
        subject="Follow up",
        snippet="Just checking in",
        has_user_reply_after_customer=False,
        customer_asked_no_reply=False,
        stale_days=7,
    )
    assert any(r[0] == "stale_thread" for r in results)


def test_meeting_language_detected():
    results = classify_gmail_thread(
        user_email="sa@redhat.com",
        user_domain="redhat.com",
        last_from_user=False,
        last_message_at=datetime.now(timezone.utc),
        subject="Sync",
        snippet="Can we schedule a zoom call next week?",
        has_user_reply_after_customer=False,
        customer_asked_no_reply=False,
    )
    assert any(r[0] == "schedule_meeting" for r in results)


def test_customer_ask_pending():
    results = classify_gmail_thread(
        user_email="sa@redhat.com",
        user_domain="redhat.com",
        last_from_user=True,
        last_message_at=datetime.now(timezone.utc),
        subject="Request",
        snippet="Please review",
        has_user_reply_after_customer=False,
        customer_asked_no_reply=True,
    )
    assert any(r[0] == "customer_ask_pending" for r in results)
