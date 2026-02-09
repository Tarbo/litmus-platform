from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': {
                'type': 'http_error',
                'message': exc.detail,
                'request_id': getattr(request.state, 'request_id', None),
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            'error': {
                'type': 'internal_server_error',
                'message': 'An unexpected error occurred',
                'request_id': getattr(request.state, 'request_id', None),
            }
        },
    )
