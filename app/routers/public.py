import json
from datetime import date as date_type
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import (
    Party, Cabinet, Promise, Evidence, Election, SeatResult, Motion, VoteRecord,
    PartyAttendance, PromiseStatus, PromiseSource,
)
from ..i18n import get_locale, translate
from ..content import load_document

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def render(template: str, request: Request, **ctx):
    locale = get_locale(request)
    ctx.update(request=request, locale=locale,
               _=lambda key, **kw: translate(locale, key, **kw))
    return templates.TemplateResponse(template, ctx)


def status_counts(db: Session, query_filter=None):
    counts = {}
    for status in PromiseStatus:
        q = db.query(Promise).filter(Promise.status == status)
        if query_filter is not None:
            q = q.filter(query_filter)
        counts[status.name] = q.count()
    return counts


def distinct_categories(db: Session):
    rows = db.query(Promise.category).distinct().order_by(Promise.category).all()
    return [r[0] for r in rows if r[0]]


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    cabinets = db.query(Cabinet).order_by(Cabinet.start_date.desc()).all()
    total = db.query(Promise).count()
    counts = status_counts(db)
    fulfilled = counts["waargemaakt"] + counts["deels_waargemaakt"]
    pct_fulfilled = round(counts["waargemaakt"] / total * 100) if total else 0

    parties = (db.query(Party).filter(Party.active == True, Party.current_seats > 0)
               .order_by(Party.current_seats.desc()).all())

    return render("index.html", request,
                  cabinets=cabinets[:6], parties=parties,
                  stats={
                      "total": total,
                      "fulfilled": counts["waargemaakt"],
                      "deels": counts["deels_waargemaakt"],
                      "in_progress": counts["in_uitvoering"],
                      "broken": counts["gebroken"],
                      "beloofd": counts["beloofd"],
                      "geparkeerd": counts["geparkeerd"],
                      "pct_fulfilled": pct_fulfilled,
                  })


@router.get("/beloftes", response_class=HTMLResponse)
def promises_list(
    request: Request,
    db: Session = Depends(get_db),
    cabinet_id: Optional[int] = None,
    party_id: Optional[int] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
):
    per_page = 20
    query = db.query(Promise)

    if cabinet_id:
        query = query.filter(Promise.cabinet_id == cabinet_id)
    if party_id:
        query = query.filter(Promise.party_id == party_id)
    if status and status in PromiseStatus.__members__:
        query = query.filter(Promise.status == PromiseStatus[status])
    if category:
        query = query.filter(Promise.category == category)
    if source and source in PromiseSource.__members__:
        query = query.filter(Promise.source_kind == PromiseSource[source])
    if search:
        query = query.filter(Promise.title.ilike(f"%{search}%"))

    total = query.count()
    promises = (query.order_by(Promise.election_year.desc().nullslast(), Promise.id.desc())
                .offset((page - 1) * per_page).limit(per_page).all())
    total_pages = (total + per_page - 1) // per_page

    cabinets = db.query(Cabinet).order_by(Cabinet.start_date.desc()).all()
    parties = db.query(Party).order_by(Party.name).all()

    return render("promises.html", request,
                  promises=promises, cabinets=cabinets, parties=parties,
                  statuses=list(PromiseStatus), sources=list(PromiseSource),
                  categories=distinct_categories(db),
                  filters={
                      "cabinet_id": cabinet_id, "party_id": party_id, "status": status,
                      "category": category, "source": source, "search": search,
                  },
                  pagination={"page": page, "total_pages": total_pages, "total": total})


@router.get("/belofte/{promise_id}", response_class=HTMLResponse)
def promise_detail(request: Request, promise_id: int, db: Session = Depends(get_db)):
    promise = db.query(Promise).filter(Promise.id == promise_id).first()
    if not promise:
        raise HTTPException(status_code=404, detail="Belofte niet gevonden")
    return render("promise_detail.html", request, promise=promise)


@router.get("/partijen", response_class=HTMLResponse)
def parties_list(request: Request, db: Session = Depends(get_db)):
    parties = db.query(Party).order_by(Party.active.desc(), Party.current_seats.desc().nullslast()).all()
    party_stats = []
    for party in parties:
        total = db.query(Promise).filter(Promise.party_id == party.id).count()
        kept = db.query(Promise).filter(
            Promise.party_id == party.id,
            Promise.status == PromiseStatus.waargemaakt).count()
        partly = db.query(Promise).filter(
            Promise.party_id == party.id,
            Promise.status == PromiseStatus.deels_waargemaakt).count()
        broken = db.query(Promise).filter(
            Promise.party_id == party.id,
            Promise.status == PromiseStatus.gebroken).count()
        party_stats.append({
            "party": party, "total": total, "kept": kept, "partly": partly, "broken": broken,
            "pct": round(kept / total * 100) if total else None,
        })
    return render("parties.html", request, party_stats=party_stats)


@router.get("/partij/{party_id}", response_class=HTMLResponse)
def party_detail(request: Request, party_id: int, db: Session = Depends(get_db)):
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Partij niet gevonden")

    # Beloftes gegroepeerd per verkiezingsjaar (nieuwste eerst)
    promises = (db.query(Promise).filter(Promise.party_id == party.id)
                .order_by(Promise.election_year.desc().nullslast()).all())
    by_year = {}
    for p in promises:
        by_year.setdefault(p.election_year, []).append(p)

    # Kabinetsdeelname (nieuwste eerst; kabinetten zonder startdatum achteraan)
    cabinets = sorted(party.cabinets,
                      key=lambda c: c.start_date or date_type.min,
                      reverse=True)

    # Zetelhistorie (met vooraf berekende balkbreedte)
    seat_rows = (db.query(SeatResult, Election).join(Election)
                 .filter(SeatResult.party_id == party.id)
                 .order_by(Election.year).all())
    max_seats = max((r.seats for r, _e in seat_rows), default=0)
    seat_history = [
        {"year": e.year, "seats": r.seats,
         "pct": round(r.seats / max_seats * 100) if max_seats else 0}
        for r, e in seat_rows
    ]

    # Stemgedrag op wetten
    votes = (db.query(VoteRecord, Motion).join(Motion)
             .filter(VoteRecord.party_id == party.id)
             .order_by(Motion.year.desc()).all())

    # Aanwezigheid
    attendance = (db.query(PartyAttendance).filter(PartyAttendance.party_id == party.id)
                  .order_by(PartyAttendance.year).all())

    total = len(promises)
    kept = sum(1 for p in promises if p.status == PromiseStatus.waargemaakt)
    partly = sum(1 for p in promises if p.status == PromiseStatus.deels_waargemaakt)
    broken = sum(1 for p in promises if p.status == PromiseStatus.gebroken)

    return render("party_detail.html", request,
                  party=party, promises_by_year=by_year, cabinets=cabinets,
                  seat_history=seat_history, votes=votes, attendance=attendance,
                  stats={"total": total, "kept": kept, "partly": partly, "broken": broken,
                         "pct": round(kept / total * 100) if total else None})


@router.get("/juridisch", response_class=HTMLResponse)
def juridisch(request: Request):
    doc = load_document("juridisch/algemene-voorwaarden.md")
    if not doc:
        raise HTTPException(status_code=404, detail="Document niet gevonden")
    return render("juridisch.html", request, doc=doc)


@router.get("/kabinetten", response_class=HTMLResponse)
def cabinets_list(request: Request, db: Session = Depends(get_db)):
    cabinets = db.query(Cabinet).order_by(Cabinet.start_date.desc()).all()
    cabinet_stats = []
    for cab in cabinets:
        total = db.query(Promise).filter(Promise.cabinet_id == cab.id).count()
        fulfilled = db.query(Promise).filter(
            Promise.cabinet_id == cab.id,
            Promise.status == PromiseStatus.waargemaakt).count()
        cabinet_stats.append({
            "cabinet": cab, "total": total, "fulfilled": fulfilled,
            "pct": round(fulfilled / total * 100) if total else 0,
            "highlights": json.loads(cab.highlights) if cab.highlights else [],
        })
    return render("cabinets.html", request, cabinet_stats=cabinet_stats)


@router.get("/kabinet/{cabinet_id}", response_class=HTMLResponse)
def cabinet_detail(request: Request, cabinet_id: int, db: Session = Depends(get_db)):
    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=404, detail="Kabinet niet gevonden")

    promises_by_status = {}
    for status in PromiseStatus:
        count = db.query(Promise).filter(
            Promise.cabinet_id == cabinet_id, Promise.status == status).count()
        promises_by_status[status.value] = count

    promises_by_category = {}
    for cat in distinct_categories(db):
        count = db.query(Promise).filter(
            Promise.cabinet_id == cabinet_id, Promise.category == cat).count()
        if count > 0:
            promises_by_category[cat] = count

    total = sum(promises_by_status.values())
    promises = (db.query(Promise).filter(Promise.cabinet_id == cabinet_id)
                .order_by(Promise.category).all())

    # Verkiezingsprogramma-beloftes van coalitiepartijen in de periode van dit kabinet
    coalition_promises = []
    if cabinet.start_date:
        party_ids = [p.id for p in cabinet.parties]
        if party_ids:
            coalition_promises = (
                db.query(Promise)
                .filter(Promise.party_id.in_(party_ids),
                        Promise.source_kind == PromiseSource.verkiezingsprogramma,
                        Promise.election_year != None,
                        Promise.election_year <= cabinet.start_date.year,
                        Promise.election_year >= cabinet.start_date.year - 2)
                .order_by(Promise.party_id).all())

    return render("cabinet_detail.html", request,
                  cabinet=cabinet, promises=promises,
                  promises_by_status=promises_by_status,
                  promises_by_category=promises_by_category,
                  coalition_promises=coalition_promises,
                  highlights=json.loads(cabinet.highlights) if cabinet.highlights else [],
                  total=total, statuses=list(PromiseStatus))
