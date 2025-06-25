from fastapi import FastAPI

from doppelbank.veneer.endpoints.link import router as link_router
from doppelbank.veneer.endpoints.transactions import router as transactions_router

app = FastAPI()

app.include_router(transactions_router)
app.include_router(link_router)
