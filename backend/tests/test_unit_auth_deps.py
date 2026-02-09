from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.deps import require_write_access
from app.config import settings


class _Req:
    def __init__(self, authorization: str | None = None):
        self.headers = {}
        if authorization:
            self.headers['Authorization'] = authorization


def test_require_write_access_allows_dev_without_tokens():
    prev_env = settings.environment
    prev_tokens = settings.admin_api_tokens
    settings.environment = 'development'
    settings.admin_api_tokens = ''
    try:
        require_write_access(_Req())
    finally:
        settings.environment = prev_env
        settings.admin_api_tokens = prev_tokens


def test_require_write_access_blocks_without_valid_token_when_tokens_configured():
    prev_env = settings.environment
    prev_tokens = settings.admin_api_tokens
    settings.environment = 'production'
    settings.admin_api_tokens = 'alpha,beta'
    try:
        with pytest.raises(HTTPException):
            require_write_access(_Req())
        with pytest.raises(HTTPException):
            require_write_access(_Req('Bearer gamma'))
    finally:
        settings.environment = prev_env
        settings.admin_api_tokens = prev_tokens


def test_require_write_access_allows_valid_token():
    prev_env = settings.environment
    prev_tokens = settings.admin_api_tokens
    settings.environment = 'production'
    settings.admin_api_tokens = 'alpha,beta'
    try:
        require_write_access(_Req('Bearer beta'))
    finally:
        settings.environment = prev_env
        settings.admin_api_tokens = prev_tokens
