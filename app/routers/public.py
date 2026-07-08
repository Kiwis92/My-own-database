from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from ..database import get_db
from ..models import Party, Cabinet, Promise, Evidence, PromiseStatus, PromiseCategory

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    cabinets = db.query(Cabinet).order_by(Cabinet.year_start.desc()).all()
    total_promises = db.query(Promise).count()
    fulfilled = db.query(Promise).filter(Promise.status == PromiseStatus.waargemaakt).count()
    in_progress = db.query(Promise).filter(Promise.status == PromiseStatus.in_uitvoering).count()
    broken = db.query(Promise).filter(Promise.status == PromiseStatus.gebroken).count()
    beloofd = db.query(Promise).filter(Promise.status == PromiseStatus.beloofd).count()
    geparkeerd = db.query(Promise).filter(Promise.status == PromiseStatus.geparkeerd).count()

    pct_fulfilled = round(fulfilled / total_promises * 100) if total_promises else 0

    return templates.TemplateResponse("index.html", {
        "request": request,
        "cabinets": cabinets,
        "stats": {
            "total": total_promises,
            "fulfilled": fulfilled,
            "in_progress": in_progress,
            "broken": broken,
            "beloofd": beloofd,
            "geparkeerd": geparkeerd,
            "pct_fulfilled": pct_fulfilled,
        }
    })


@router.get("/beloftes", response_class=HTMLResponse)
def promises_list(
    request: Request,
    db: Session = Depends(get_db),
    cabinet_id: Optional[int] = None,
    party_id: Optional[int] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
):
    per_page = 20
    query = db.query(Promise)

    if cabinet_id:
        query = query.filter(Promise.cabinet_id == cabinet_id)
    if party_id:
        query = query.filter(Promise.party_id == party_id)
    if status:
        query = query.filter(Promise.status == status)
    if category:
        query = query.filter(Promise.category == category)
    if search:
        query = query.filter(Promise.title.ilike(f"%{search}%"))

    total = query.count()
    promises = query.order_by(Promise.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page

    cabinets = db.query(Cabinet).order_by(Cabinet.year_start.desc()).all()
    parties = db.query(Party).order_by(Party.name).all()

    return templates.TemplateResponse("promises.html", {
        "request": request,
        "promises": promises,
        "cabinets": cabinets,
        "parties": parties,
        "statuses": list(PromiseStatus),
        "categories": list(PromiseCategory),
        "filters": {
            "cabinet_id": cabinet_id,
            "party_id": party_id,
            "status": status,
            "category": category,
            "search": search,
        },
        "pagination": {
            "page": page,
            "total_pages": total_pages,
            "total": total,
        }
    })


@router.get("/belofte/{promise_id}", response_class=HTMLResponse)
def promise_detail(request: Request, promise_id: int, db: Session = Depends(get_db)):
    promise = db.query(Promise).filter(Promise.id == promise_id).first()
    if not promise:
        raise HTTPException(status_code=404, detail="Belofte niet gevonden")
    return templates.TemplateResponse("promise_detail.html", {
        "request": request,
        "promise": promise,
    })


@router.get("/kabinetten", response_class=HTMLResponse)
def cabinets_list(request: Request, db: Session = Depends(get_db)):
    cabinets = db.query(Cabinet).order_by(Cabinet.year_start.desc()).all()
    cabinet_stats = []
    for cab in cabinets:
        total = db.query(Promise).filter(Promise.cabinet_id == cab.id).count()
        fulfilled = db.query(Promise).filter(
            Promise.cabinet_id == cab.id,
            Promise.status == PromiseStatus.waargemaakt
        ).count()
        cabinet_stats.append({
            "cabinet": cab,
            "total": total,
            "fulfilled": fulfilled,
            "pct": round(fulfilled / total * 100) if total else 0,
        })
    return templates.TemplateResponse("cabinets.html", {
        "request": request,
        "cabinet_stats": cabinet_stats,
    })


@router.get("/kabinet/{cabinet_id}", response_class=HTMLResponse)
def cabinet_detail(request: Request, cabinet_id: int, db: Session = Depends(get_db)):
    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=404, detail="Kabinet niet gevonden")

    promises_by_status = {}
    for status in PromiseStatus:
        count = db.query(Promise).filter(
            Promise.cabinet_id == cabinet_id,
            Promise.status == status
        ).count()
        promises_by_status[status.value] = count

    promises_by_category = {}
    for cat in PromiseCategory:
        count = db.query(Promise).filter(
            Promise.cabinet_id == cabinet_id,
            Promise.category == cat
        ).count()
        if count > 0:
            promises_by_category[cat.value] = count

    total = sum(promises_by_status.values())
    promises = db.query(Promise).filter(Promise.cabinet_id == cabinet_id).order_by(Promise.category).all()

    return templates.TemplateResponse("cabinet_detail.html", {
        "request": request,
        "cabinet": cabinet,
        "promises": promises,
        "promises_by_status": promises_by_status,
        "promises_by_category": promises_by_category,
        "total": total,
        "statuses": list(PromiseStatus),
        "categories": list(PromiseCategory),
    })
