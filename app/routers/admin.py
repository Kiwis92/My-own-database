import os
from datetime import date
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv

from ..database import get_db
from ..models import (
    Country, Party, Cabinet, Promise, Evidence,
    PromiseStatus, PromiseSource,
)

load_dotenv()

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
serializer = URLSafeTimedSerializer(SECRET_KEY)


def is_authenticated(request: Request) -> bool:
    token = request.cookies.get("admin_session")
    if not token:
        return False
    try:
        serializer.loads(token, max_age=86400)
        return True
    except Exception:
        return False


def auth_redirect(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    return None


def default_country(db: Session) -> Country:
    country = db.query(Country).filter(Country.code == "nl").first()
    if not country:
        country = Country(code="nl", name="Nederland", legislature_name="Tweede Kamer")
        db.add(country)
        db.flush()
    return country


def distinct_categories(db: Session):
    rows = db.query(Promise.category).distinct().order_by(Promise.category).all()
    return [r[0] for r in rows if r[0]]


def parse_date_str(s: Optional[str]):
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


# --- Auth ---

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": None})


@router.post("/login")
def login(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        token = serializer.dumps("authenticated")
        response = RedirectResponse(url="/admin", status_code=302)
        response.set_cookie("admin_session", token, httponly=True, max_age=86400)
        return response
    return templates.TemplateResponse("admin/login.html", {
        "request": request, "error": "Onjuist wachtwoord"
    })


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_session")
    return response


# --- Dashboard ---

@router.get("", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    redir = auth_redirect(request)
    if redir:
        return redir

    stats = {
        "total_promises": db.query(Promise).count(),
        "total_parties": db.query(Party).count(),
        "total_cabinets": db.query(Cabinet).count(),
        "fulfilled": db.query(Promise).filter(Promise.status == PromiseStatus.waargemaakt).count(),
        "broken": db.query(Promise).filter(Promise.status == PromiseStatus.gebroken).count(),
        "in_progress": db.query(Promise).filter(Promise.status == PromiseStatus.in_uitvoering).count(),
    }
    recent_promises = db.query(Promise).order_by(Promise.id.desc()).limit(5).all()

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request, "stats": stats, "recent_promises": recent_promises,
    })


# --- Parties ---

@router.get("/partijen", response_class=HTMLResponse)
def admin_parties(request: Request, db: Session = Depends(get_db)):
    redir = auth_redirect(request)
    if redir:
        return redir
    parties = db.query(Party).order_by(Party.active.desc(), Party.name).all()
    return templates.TemplateResponse("admin/parties.html", {"request": request, "parties": parties})


@router.get("/partijen/nieuw", response_class=HTMLResponse)
def new_party_form(request: Request):
    redir = auth_redirect(request)
    if redir:
        return redir
    return templates.TemplateResponse("admin/party_form.html", {"request": request, "party": None, "error": None})


@router.post("/partijen/nieuw")
def create_party(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    abbreviation: str = Form(...),
    color: str = Form("#3B82F6"),
    ideology: str = Form(""),
    founded_year: Optional[int] = Form(None),
    current_seats: Optional[int] = Form(None),
    active: Optional[str] = Form(None),
    description: str = Form(""),
):
    redir = auth_redirect(request)
    if redir:
        return redir
    country = default_country(db)
    existing = db.query(Party).filter(
        Party.country_id == country.id, Party.abbreviation == abbreviation).first()
    if existing:
        return templates.TemplateResponse("admin/party_form.html", {
            "request": request, "party": None,
            "error": f"Afkorting '{abbreviation}' bestaat al."
        })
    party = Party(
        country_id=country.id, name=name, abbreviation=abbreviation, color=color,
        ideology=ideology or None, founded_year=founded_year,
        current_seats=current_seats, active=bool(active), description=description,
    )
    db.add(party)
    db.commit()
    return RedirectResponse(url="/admin/partijen", status_code=302)


@router.get("/partijen/{party_id}/bewerk", response_class=HTMLResponse)
def edit_party_form(request: Request, party_id: int, db: Session = Depends(get_db)):
    redir = auth_redirect(request)
    if redir:
        return redir
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("admin/party_form.html", {"request": request, "party": party, "error": None})


@router.post("/partijen/{party_id}/bewerk")
def update_party(
    request: Request,
    party_id: int,
    db: Session = Depends(get_db),
    name: str = Form(...),
    abbreviation: str = Form(...),
    color: str = Form("#3B82F6"),
    ideology: str = Form(""),
    founded_year: Optional[int] = Form(None),
    current_seats: Optional[int] = Form(None),
    active: Optional[str] = Form(None),
    description: str = Form(""),
):
    redir = auth_redirect(request)
    if redir:
        return redir
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404)
    party.name = name
    party.abbreviation = abbreviation
    party.color = color
    party.ideology = ideology or None
    party.founded_year = founded_year
    party.current_seats = current_seats
    party.active = bool(active)
    party.description = description
    db.commit()
    return RedirectResponse(url="/admin/partijen", status_code=302)


@router.post("/partijen/{party_id}/verwijder")
def delete_party(request: Request, party_id: int, db: Session = Depends(get_db)):
    redir = auth_redirect(request)
    if redir:
        return redir
    party = db.query(Party).filter(Party.id == party_id).first()
    if party:
        db.delete(party)
        db.commit()
    return RedirectResponse(url="/admin/partijen", status_code=302)


# --- Cabinets ---

@router.get("/kabinetten", response_class=HTMLResponse)
def admin_cabinets(request: Request, db: Session = Depends(get_db)):
    redir = auth_redirect(request)
    if redir:
        return redir
    cabinets = db.query(Cabinet).order_by(Cabinet.start_date.desc()).all()
    return templates.TemplateResponse("admin/cabinets.html", {"request": request, "cabinets": cabinets})


@router.get("/kabinetten/nieuw", response_class=HTMLResponse)
def new_cabinet_form(request: Request, db: Session = Depends(get_db)):
    redir = auth_redirect(request)
    if redir:
        return redir
    parties = db.query(Party).order_by(Party.name).all()
    return templates.TemplateResponse("admin/cabinet_form.html", {
        "request": request, "cabinet": None, "parties": parties,
        "selected_party_ids": [], "error": None
    })


@router.post("/kabinetten/nieuw")
def create_cabinet(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    premier: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
    fell: Optional[str] = Form(None),
    fall_reason: str = Form(""),
    description: str = Form(""),
    coalition_agreement_url: str = Form(""),
    party_ids: list[int] = Form([]),
):
    redir = auth_redirect(request)
    if redir:
        return redir
    country = default_country(db)
    cabinet = Cabinet(
        country_id=country.id, name=name, premier=premier or None,
        start_date=parse_date_str(start_date), end_date=parse_date_str(end_date),
        fell=bool(fell), fall_reason=fall_reason or None,
        description=description or None,
        coalition_agreement_url=coalition_agreement_url or None,
    )
    db.add(cabinet)
    db.flush()
    cabinet.parties = [p for p in db.query(Party).filter(Party.id.in_(party_ids)).all()] if party_ids else []
    db.commit()
    return RedirectResponse(url="/admin/kabinetten", status_code=302)


@router.get("/kabinetten/{cabinet_id}/bewerk", response_class=HTMLResponse)
def edit_cabinet_form(request: Request, cabinet_id: int, db: Session = Depends(get_db)):
    redir = auth_redirect(request)
    if redir:
        return redir
    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=404)
    parties = db.query(Party).order_by(Party.name).all()
    return templates.TemplateResponse("admin/cabinet_form.html", {
        "request": request, "cabinet": cabinet, "parties": parties,
        "selected_party_ids": [p.id for p in cabinet.parties], "error": None
    })


@router.post("/kabinetten/{cabinet_id}/bewerk")
def update_cabinet(
    request: Request,
    cabinet_id: int,
    db: Session = Depends(get_db),
    name: str = Form(...),
    premier: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
    fell: Optional[str] = Form(None),
    fall_reason: str = Form(""),
    description: str = Form(""),
    coalition_agreement_url: str = Form(""),
    party_ids: list[int] = Form([]),
):
    redir = auth_redirect(request)
    if redir:
        return redir
    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=404)
    cabinet.name = name
    cabinet.premier = premier or None
    cabinet.start_date = parse_date_str(start_date)
    cabinet.end_date = parse_date_str(end_date)
    cabinet.fell = bool(fell)
    cabinet.fall_reason = fall_reason or None
    cabinet.description = description or None
    cabinet.coalition_agreement_url = coalition_agreement_url or None
    cabinet.parties = [p for p in db.query(Party).filter(Party.id.in_(party_ids)).all()] if party_ids else []
    db.commit()
    return RedirectResponse(url="/admin/kabinetten", status_code=302)


@router.post("/kabinetten/{cabinet_id}/verwijder")
def delete_cabinet(request: Request, cabinet_id: int, db: Session = Depends(get_db)):
    redir = auth_redirect(request)
    if redir:
        return redir
    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if cabinet:
        db.delete(cabinet)
        db.commit()
    return RedirectResponse(url="/admin/kabinetten", status_code=302)


# --- Promises ---

def promise_form_context(request: Request, db: Session, promise=None, error=None):
    return {
        "request": request,
        "promise": promise,
        "cabinets": db.query(Cabinet).order_by(Cabinet.start_date.desc()).all(),
        "parties": db.query(Party).order_by(Party.name).all(),
        "statuses": list(PromiseStatus),
        "sources": list(PromiseSource),
        "categories": distinct_categories(db),
        "error": error,
    }


@router.get("/beloftes", response_class=HTMLResponse)
def admin_promises(
    request: Request,
    db: Session = Depends(get_db),
    cabinet_id: Optional[int] = None,
    party_id: Optional[int] = None,
    status: Optional[str] = None,
):
    redir = auth_redirect(request)
    if redir:
        return redir
    query = db.query(Promise)
    if cabinet_id:
        query = query.filter(Promise.cabinet_id == cabinet_id)
    if party_id:
        query = query.filter(Promise.party_id == party_id)
    if status and status in PromiseStatus.__members__:
        query = query.filter(Promise.status == PromiseStatus[status])
    promises = query.order_by(Promise.id.desc()).all()
    return templates.TemplateResponse("admin/promises.html", {
        "request": request,
        "promises": promises,
        "cabinets": db.query(Cabinet).order_by(Cabinet.start_date.desc()).all(),
        "parties": db.query(Party).order_by(Party.name).all(),
        "statuses": list(PromiseStatus),
        "filters": {"cabinet_id": cabinet_id, "party_id": party_id, "status": status},
    })


@router.get("/beloftes/nieuw", response_class=HTMLResponse)
def new_promise_form(request: Request, db: Session = Depends(get_db)):
    redir = auth_redirect(request)
    if redir:
        return redir
    return templates.TemplateResponse("admin/promise_form.html",
                                      promise_form_context(request, db))


@router.post("/beloftes/nieuw")
def create_promise(
    request: Request,
    db: Session = Depends(get_db),
    source_kind: str = Form("regeerakkoord"),
    cabinet_id: Optional[int] = Form(None),
    party_id: Optional[int] = Form(None),
    election_year: Optional[int] = Form(None),
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form("Overig"),
    status: str = Form("beloofd"),
    source_text: str = Form(""),
):
    redir = auth_redirect(request)
    if redir:
        return redir
    if not cabinet_id and not party_id:
        return templates.TemplateResponse(
            "admin/promise_form.html",
            promise_form_context(request, db, error="Kies minimaal een kabinet of een partij."))
    promise = Promise(
        source_kind=PromiseSource[source_kind] if source_kind in PromiseSource.__members__ else PromiseSource.regeerakkoord,
        cabinet_id=cabinet_id or None,
        party_id=party_id or None,
        election_year=election_year,
        title=title,
        description=description or None,
        category=category.strip() or "Overig",
        status=PromiseStatus[status] if status in PromiseStatus.__members__ else PromiseStatus.beloofd,
        source_text=source_text or None,
    )
    db.add(promise)
    db.commit()
    return RedirectResponse(url=f"/admin/beloftes/{promise.id}", status_code=302)


@router.get("/beloftes/{promise_id}", response_class=HTMLResponse)
def admin_promise_detail(request: Request, promise_id: int, db: Session = Depends(get_db)):
    redir = auth_redirect(request)
    if redir:
        return redir
    promise = db.query(Promise).filter(Promise.id == promise_id).first()
    if not promise:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("admin/promise_detail.html",
                                      promise_form_context(request, db, promise=promise))


@router.post("/beloftes/{promise_id}/bewerk")
def update_promise(
    request: Request,
    promise_id: int,
    db: Session = Depends(get_db),
    source_kind: str = Form("regeerakkoord"),
    cabinet_id: Optional[int] = Form(None),
    party_id: Optional[int] = Form(None),
    election_year: Optional[int] = Form(None),
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form("Overig"),
    status: str = Form("beloofd"),
    source_text: str = Form(""),
):
    redir = auth_redirect(request)
    if redir:
        return redir
    promise = db.query(Promise).filter(Promise.id == promise_id).first()
    if not promise:
        raise HTTPException(status_code=404)
    if source_kind in PromiseSource.__members__:
        promise.source_kind = PromiseSource[source_kind]
    promise.cabinet_id = cabinet_id or None
    promise.party_id = party_id or None
    promise.election_year = election_year
    promise.title = title
    promise.description = description or None
    promise.category = category.strip() or "Overig"
    if status in PromiseStatus.__members__:
        promise.status = PromiseStatus[status]
    promise.source_text = source_text or None
    db.commit()
    return RedirectResponse(url=f"/admin/beloftes/{promise_id}", status_code=302)


@router.post("/beloftes/{promise_id}/verwijder")
def delete_promise(request: Request, promise_id: int, db: Session = Depends(get_db)):
    redir = auth_redirect(request)
    if redir:
        return redir
    promise = db.query(Promise).filter(Promise.id == promise_id).first()
    if promise:
        db.delete(promise)
        db.commit()
    return RedirectResponse(url="/admin/beloftes", status_code=302)


# --- Evidence ---

@router.post("/beloftes/{promise_id}/bewijs/nieuw")
def add_evidence(
    request: Request,
    promise_id: int,
    db: Session = Depends(get_db),
    title: str = Form(...),
    url: str = Form(""),
    description: str = Form(""),
    source_type: str = Form(""),
    date_published: Optional[str] = Form(None),
):
    redir = auth_redirect(request)
    if redir:
        return redir
    evidence = Evidence(
        promise_id=promise_id,
        title=title,
        url=url or None,
        description=description or None,
        source_type=source_type or None,
        date_published=parse_date_str(date_published),
    )
    db.add(evidence)
    db.commit()
    return RedirectResponse(url=f"/admin/beloftes/{promise_id}", status_code=302)


@router.post("/bewijs/{evidence_id}/verwijder")
def delete_evidence(request: Request, evidence_id: int, db: Session = Depends(get_db)):
    redir = auth_redirect(request)
    if redir:
        return redir
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    promise_id = evidence.promise_id if evidence else None
    if evidence:
        db.delete(evidence)
        db.commit()
    if promise_id:
        return RedirectResponse(url=f"/admin/beloftes/{promise_id}", status_code=302)
    return RedirectResponse(url="/admin/beloftes", status_code=302)
