from fastapi import FastAPI
from spaceone.monitoring.interface.rest.v1 import common, event, alert


app = FastAPI()
app.include_router(common.router)
app.include_router(
    event.router,
    prefix='/monitoring/v1'
)
app.include_router(
    alert.router,
    prefix='/monitoring/v1'
)

