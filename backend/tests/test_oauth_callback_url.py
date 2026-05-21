from unittest.mock import MagicMock

from app.config import get_settings
from app.services.oauth_google import public_callback_url


def test_public_callback_url_uses_configured_redirect_uri():
    get_settings.cache_clear()
    settings = get_settings()
    settings.google_redirect_uri = "https://sa-hub.example.com/api/v1/oauth/google/callback"

    request = MagicMock()
    request.query_params.multi_items = lambda: [
        ("state", "abc"),
        ("iss", "https://accounts.google.com"),
        ("code", "4/0TEST"),
        ("scope", "email"),
        ("authuser", "0"),
        ("hd", "redhat.com"),
    ]

    url = public_callback_url(request)
    assert url.startswith(settings.google_redirect_uri)
    assert "code=4%2F0TEST" in url
    assert "state=abc" in url
    assert "iss=" not in url
    assert "hd=" not in url
