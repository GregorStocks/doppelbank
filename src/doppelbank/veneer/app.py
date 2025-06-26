import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from doppelbank.lib.logging_config import configure_logging
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
app.include_router(link_router)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors and log the full request details."""
    # Get request body
    body = None
    try:
        body = await request.body()
        body_str = body.decode('utf-8') if body else None
    except Exception as e:
        body_str = f"<Error reading body: {e}>"
    
    # Log the full request details
    logger.warning(
        f"404 Not Found: {request.method} {request.url} - "
        f"Headers: {dict(request.headers)} - "
        f"Body: {body_str}"
    )
    
    return JSONResponse(
        status_code=404,
        content={"detail": "Not found"}
    )
