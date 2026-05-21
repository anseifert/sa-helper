from app.extractors.gmail_patterns import classify_concur_message, classify_redhat_direct


def test_concur_detected():
    hits = classify_concur_message(
        subject="SAP Concur expense report approval",
        snippet="Please approve payment request",
        from_header="noreply@concur.com",
    )
    assert hits and hits[0][0] == "concur_payment"


def test_redhat_direct():
    hits = classify_redhat_direct(
        user_email="you@redhat.com",
        from_header="manager@redhat.com",
        to_header="you@redhat.com",
        subject="Feedback needed on proposal",
        snippet="Please review by Friday",
        last_from_user=False,
    )
    assert hits and hits[0][0] == "redhat_attention"


def test_redhat_skips_user_sent():
    assert (
        classify_redhat_direct(
            user_email="you@redhat.com",
            from_header="you@redhat.com",
            to_header="peer@redhat.com",
            subject="Re: update",
            snippet="Thanks",
            last_from_user=True,
        )
        == []
    )
