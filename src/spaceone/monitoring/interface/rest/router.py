from fastapi import FastAPI
from spaceone.monitoring.interface.rest.v1 import event

app = FastAPI()
app.include_router(
    event.router,
    prefix='/monitoring/v1'
)

