from app.extractors.calendar import CalendarExtractor


def test_parse_action_items():
    ext = CalendarExtractor.__new__(CalendarExtractor)
    items = ext._parse_action_items(
        "Action item: Send proposal\n- [ ] Review architecture doc",
        "Customer QBR",
    )
    assert len(items) >= 1
    assert any("proposal" in i.lower() or "review" in i.lower() for i in items)
