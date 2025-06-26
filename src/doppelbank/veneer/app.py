import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from doppelbank.lib.logging_config import configure_logging
from doppelbank.veneer.endpoints.accounts import router as accounts_router
from doppelbank.veneer.endpoints.institutions import router as institutions_router
from doppelbank.veneer.endpoints.link import router as link_router
from doppelbank.veneer.endpoints.transactions import router as transactions_router

# Configure logging
configure_logging(module_name="veneer")
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions_router)
app.include_router(accounts_router)
app.include_router(link_router)
app.include_router(institutions_router)


async def error_handler(
    request: Request,
    exc: HTTPException | RequestValidationError | StarletteHTTPException,
) -> JSONResponse:
    """Handle all HTTP errors and validation errors with detailed logging."""
    # Get request body safely
    try:
        body = await request.body()
        body_str = body.decode("utf-8") if body else None
    except Exception as e:
        body_str = f"<Error reading body: {e}>"

    # Handle validation errors (422s)
    if isinstance(exc, RequestValidationError):
        logger.warning(
            f"HTTP 422 Validation Error: {request.method} {request.url} - "
            f"Body: {body_str} - Errors: {exc.errors()}"
        )
        return JSONResponse(
            status_code=422,
            content={"detail": "Validation error", "errors": exc.errors()},
        )

    # Handle all HTTP errors (including Starlette's built-in 404s)
    status_code = exc.status_code
    detail = exc.detail if hasattr(exc, "detail") else str(exc)

    logger.warning(
        f"HTTP {status_code} {detail}: {request.method} {request.url} - "
        f"Body: {body_str}"
    )
    return JSONResponse(status_code=status_code, content={"detail": detail})


# Register the handler for all exception types
app.exception_handler(HTTPException)(error_handler)
app.exception_handler(RequestValidationError)(error_handler)
app.exception_handler(StarletteHTTPException)(error_handler)
