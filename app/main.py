from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import engine
from . import models
from .routers import public, admin

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="PoliTrack", description="Politieke beloftes tracker")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(public.router)
app.include_router(admin.router)
