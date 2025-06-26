from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from doppelbank.veneer.endpoints.link import router as link_router
from doppelbank.veneer.endpoints.transactions import router as transactions_router

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
