from app.core.security import is_token_authorized, parse_bearer_token


def test_parse_bearer_token():
    assert parse_bearer_token('Bearer abc123') == 'abc123'
    assert parse_bearer_token('bearer abc123') == 'abc123'
    assert parse_bearer_token('Token abc123') is None
    assert parse_bearer_token(None) is None


def test_token_authorization():
    allowed = ['token-one', 'token-two']
    assert is_token_authorized('token-one', allowed) is True
    assert is_token_authorized('unknown', allowed) is False
    assert is_token_authorized(None, allowed) is False
