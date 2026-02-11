import json
import logging
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger('litmus.request')


async def request_context_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = int((time.perf_counter() - start) * 1000)
        request.app.state.request_metrics.record(
            method=request.method,
            path=request.url.path,
            status_code=500,
            duration_ms=duration_ms,
        )
        logger.exception(
            json.dumps(
                {
                    'event': 'request_error',
                    'request_id': request_id,
                    'path': request.url.path,
                    'method': request.method,
                    'duration_ms': duration_ms,
                }
            )
        )
        raise

    duration_ms = int((time.perf_counter() - start) * 1000)
    request.app.state.request_metrics.record(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    response.headers['X-Request-ID'] = request_id
    logger.info(
        json.dumps(
            {
                'event': 'request_complete',
                'request_id': request_id,
                'path': request.url.path,
                'method': request.method,
                'status_code': response.status_code,
                'duration_ms': duration_ms,
            }
        )
    )
    return response


async def rate_limit_middleware(request: Request, call_next):
    sensitive_prefixes = (
        '/api/v1/events',
        '/api/v1/assignments',
        '/api/v1/metrics/guardrails',
        '/api/v1/experiments/',
    )

    is_sensitive_post = request.method == 'POST' and request.url.path.startswith(sensitive_prefixes)
    if is_sensitive_post:
        limiter = request.app.state.rate_limiter
        client_host = request.headers.get('x-forwarded-for') or (request.client.host if request.client else 'unknown')
        key = f'{client_host}:{request.url.path}'
        if not limiter.allow(
            key=key,
            limit=request.app.state.rate_limit_per_minute,
            window_seconds=60,
        ):
            return JSONResponse(
                status_code=429,
                content={
                    'error': {
                        'type': 'rate_limit_exceeded',
                        'message': 'Too many requests',
                        'request_id': getattr(request.state, 'request_id', None),
                    }
                },
            )

    return await call_next(request)
