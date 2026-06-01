from app.utils.task_filters import is_calendar_task, is_gmail_calendar_notification


def test_calendar_source_excluded():
    assert is_calendar_task(source="calendar", badge_source="calendar", task_type="schedule_meeting")


def test_calendar_action_excluded():
    assert is_calendar_task(source="gmail", badge_source="gmail", task_type="calendar_action")


def test_gmail_meeting_request_not_excluded():
    assert not is_calendar_task(
        source="gmail",
        badge_source="gmail",
        task_type="schedule_meeting",
        title="QBR follow-up — Schedule or confirm meeting",
        description="Can we schedule a call next week?",
    )


def test_gmail_calendar_invite_excluded():
    assert is_gmail_calendar_notification(
        subject="Invitation: Team sync @ Tue 3pm",
        from_header="calendar-notification@google.com",
    )
    assert is_calendar_task(
        source="gmail",
        badge_source="gmail",
        task_type="schedule_meeting",
        title="Invitation: Team sync @ Tue 3pm",
        from_header="calendar-notification@google.com",
    )
