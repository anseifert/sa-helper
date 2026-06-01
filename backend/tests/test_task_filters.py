from app.utils.task_filters import (
    is_calendar_task,
    is_excluded_subject,
    is_gmail_calendar_notification,
    task_subject_line,
)


def test_task_subject_line_splits_suffix():
    assert task_subject_line("Re: Hello — You owe a reply") == "Re: Hello"


def test_excluded_prefixes():
    assert is_excluded_subject("Re: Follow up thread")
    assert is_excluded_subject("Notes Call summary")
    assert is_excluded_subject("Invitation Team sync")
    assert not is_excluded_subject("Follow up on proposal")


def test_calendar_source_excluded():
    assert is_calendar_task(source="calendar", badge_source="calendar", task_type="schedule_meeting")


def test_gmail_meeting_request_not_excluded():
    assert not is_calendar_task(
        source="gmail",
        badge_source="gmail",
        task_type="schedule_meeting",
        title="QBR follow-up — Schedule or confirm meeting",
        description="Can we schedule a call next week?",
    )


def test_gmail_re_prefix_excluded():
    assert is_calendar_task(
        source="gmail",
        badge_source="gmail",
        task_type="user_owes_reply",
        title="Re: Pricing — You owe a reply",
    )


def test_gmail_calendar_invite_excluded():
    assert is_gmail_calendar_notification(
        subject="Invitation: Team sync @ Tue 3pm",
        from_header="calendar-notification@google.com",
    )
