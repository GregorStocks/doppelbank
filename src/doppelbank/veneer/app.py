from fastapi import FastAPI

from doppelbank.veneer.endpoints.transactions import router

app = FastAPI()

app.include_router(router)
