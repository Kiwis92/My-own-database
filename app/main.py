from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from .database import engine
from . import models
from .i18n import SUPPORTED
from .routers import public, admin

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="PoliTrack", description="Politieke beloftes tracker")

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.middleware("http")
async def persist_language(request: Request, call_next):
    """Onthoud een expliciete taalkeuze (?lang=xx) in een cookie."""
    response = await call_next(request)
    lang = request.query_params.get("lang")
    if lang in SUPPORTED:
        response.set_cookie("lang", lang, max_age=60 * 60 * 24 * 365)
    return response


app.include_router(public.router)
app.include_router(admin.router)
