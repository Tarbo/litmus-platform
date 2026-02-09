from hmac import compare_digest


def parse_bearer_token(auth_header: str | None) -> str | None:
    if not auth_header:
        return None
    parts = auth_header.strip().split(' ', 1)
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    return parts[1].strip()


def is_token_authorized(token: str | None, allowed_tokens: list[str]) -> bool:
    if token is None:
        return False
    for allowed in allowed_tokens:
        if compare_digest(token, allowed):
            return True
    return False
