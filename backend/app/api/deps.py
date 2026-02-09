from collections.abc import Generator

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import is_token_authorized, parse_bearer_token


def get_db(request: Request) -> Generator[Session, None, None]:
    session_maker = request.app.state.session_maker
    db = session_maker()
    try:
        yield db
    finally:
        db.close()


def require_write_access(request: Request) -> None:
    tokens = [item.strip() for item in settings.admin_api_tokens.split(',') if item.strip()]
    if not tokens and settings.environment == 'development':
        return

    auth_header = request.headers.get('Authorization')
    token = parse_bearer_token(auth_header)
    if not is_token_authorized(token, tokens):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized write access',
        )
