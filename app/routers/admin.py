import os
from fastapi import APIRouter, Depends, Request, HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv

from ..database import get_db
from ..models import Party, Cabinet, Promise, Evidence, PromiseStatus, PromiseCategory, cabinet_party

load_dotenv()

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
serializer = URLSafeTimedSerializer(SECRET_KEY)


def get_session_token(request: Request) -> Optional[str]:
    return request.cookies.get("admin_session")


def require_auth(request: Request):
    token = get_session_token(request)
    if not token:
        raise HTTPException(status_code=302, headers={"Location": "/admin/login"})
    try:
        serializer.loads(token, max_age=86400)
    except Exception:
        raise HTTPException(status_code=302, headers={"Location": "/admin/login"})


def is_authenticated(request: Request) -> bool:
    token = get_session_token(request)
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
        "request": request,
        "error": "Onjuist wachtwoord"
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

    from ..models import PromiseStatus
    total_promises = db.query(Promise).count()
    total_parties = db.query(Party).count()
    total_cabinets = db.query(Cabinet).count()
    fulfilled = db.query(Promise).filter(Promise.status == PromiseStatus.waargemaakt).count()
    broken = db.query(Promise).filter(Promise.status == PromiseStatus.gebroken).count()
    in_progress = db.query(Promise).filter(Promise.status == PromiseStatus.in_uitvoering).count()
    recent_promises = db.query(Promise).order_by(Promise.created_at.desc()).limit(5).all()

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "stats": {
            "total_promises": total_promises,
            "total_parties": total_parties,
            "total_cabinets": total_cabinets,
            "fulfilled": fulfilled,
            "broken": broken,
            "in_progress": in_progress,
        },
        "recent_promises": recent_promises,
    })


# --- Parties ---

@router.get("/partijen", response_class=HTMLResponse)
def admin_parties(request: Request, db: Session = Depends(get_db)):
    redir = auth_redirect(request)
    if redir:
        return redir
    parties = db.query(Party).order_by(Party.name).all()
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
    description: str = Form(""),
):
    redir = auth_redirect(request)
    if redir:
        return redir
    existing = db.query(Party).filter(Party.abbreviation == abbreviation.upper()).first()
    if existing:
        return templates.TemplateResponse("admin/party_form.html", {
            "request": request,
            "party": None,
            "error": f"Afkorting '{abbreviation}' bestaat al."
        })
    party = Party(name=name, abbreviation=abbreviation.upper(), color=color, description=description)
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
    description: str = Form(""),
):
    redir = auth_redirect(request)
    if redir:
        return redir
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404)
    party.name = name
    party.abbreviation = abbreviation.upper()
    party.color = color
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
    cabinets = db.query(Cabinet).order_by(Cabinet.year_start.desc()).all()
    return templates.TemplateResponse("admin/cabinets.html", {"request": request, "cabinets": cabinets})


@router.get("/kabinetten/nieuw", response_class=HTMLResponse)
def new_cabinet_form(request: Request, db: Session = Depends(get_db)):
    redir = auth_redirect(request)
    if redir:
        return redir
    parties = db.query(Party).order_by(Party.name).all()
    return templates.TemplateResponse("admin/cabinet_form.html", {
        "request": request, "cabinet": None, "parties": parties, "error": None
    })


@router.post("/kabinetten/nieuw")
def create_cabinet(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    year_start: int = Form(...),
    year_end: Optional[int] = Form(None),
    description: str = Form(""),
    coalition_agreement_url: str = Form(""),
    party_ids: list[int] = Form([]),
):
    redir = auth_redirect(request)
    if redir:
        return redir
    cabinet = Cabinet(
        name=name,
        year_start=year_start,
        year_end=year_end if year_end else None,
        description=description,
        coalition_agreement_url=coalition_agreement_url if coalition_agreement_url else None,
    )
    db.add(cabinet)
    db.flush()
    for pid in party_ids:
        party = db.query(Party).filter(Party.id == pid).first()
        if party:
            cabinet.parties.append(party)
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
    selected_party_ids = [p.id for p in cabinet.parties]
    return templates.TemplateResponse("admin/cabinet_form.html", {
        "request": request, "cabinet": cabinet, "parties": parties,
        "selected_party_ids": selected_party_ids, "error": None
    })


@router.post("/kabinetten/{cabinet_id}/bewerk")
def update_cabinet(
    request: Request,
    cabinet_id: int,
    db: Session = Depends(get_db),
    name: str = Form(...),
    year_start: int = Form(...),
    year_end: Optional[int] = Form(None),
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
    cabinet.year_start = year_start
    cabinet.year_end = year_end if year_end else None
    cabinet.description = description
    cabinet.coalition_agreement_url = coalition_agreement_url if coalition_agreement_url else None
    cabinet.parties = []
    for pid in party_ids:
        party = db.query(Party).filter(Party.id == pid).first()
        if party:
            cabinet.parties.append(party)
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

@router.get("/beloftes", response_class=HTMLResponse)
def admin_promises(
    request: Request,
    db: Session = Depends(get_db),
    cabinet_id: Optional[int] = None,
    status: Optional[str] = None,
):
    redir = auth_redirect(request)
    if redir:
        return redir
    query = db.query(Promise)
    if cabinet_id:
        query = query.filter(Promise.cabinet_id == cabinet_id)
    if status:
        query = query.filter(Promise.status == status)
    promises = query.order_by(Promise.created_at.desc()).all()
    cabinets = db.query(Cabinet).order_by(Cabinet.year_start.desc()).all()
    return templates.TemplateResponse("admin/promises.html", {
        "request": request,
        "promises": promises,
        "cabinets": cabinets,
        "statuses": list(PromiseStatus),
        "filters": {"cabinet_id": cabinet_id, "status": status},
    })


@router.get("/beloftes/nieuw", response_class=HTMLResponse)
def new_promise_form(request: Request, db: Session = Depends(get_db)):
    redir = auth_redirect(request)
    if redir:
        return redir
    cabinets = db.query(Cabinet).order_by(Cabinet.year_start.desc()).all()
    parties = db.query(Party).order_by(Party.name).all()
    return templates.TemplateResponse("admin/promise_form.html", {
        "request": request,
        "promise": None,
        "cabinets": cabinets,
        "parties": parties,
        "statuses": list(PromiseStatus),
        "categories": list(PromiseCategory),
        "error": None,
    })


@router.post("/beloftes/nieuw")
def create_promise(
    request: Request,
    db: Session = Depends(get_db),
    cabinet_id: int = Form(...),
    party_id: Optional[int] = Form(None),
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form("overig"),
    status: str = Form("beloofd"),
    source_text: str = Form(""),
):
    redir = auth_redirect(request)
    if redir:
        return redir
    promise = Promise(
        cabinet_id=cabinet_id,
        party_id=party_id if party_id else None,
        title=title,
        description=description,
        category=category,
        status=status,
        source_text=source_text if source_text else None,
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
    cabinets = db.query(Cabinet).order_by(Cabinet.year_start.desc()).all()
    parties = db.query(Party).order_by(Party.name).all()
    return templates.TemplateResponse("admin/promise_detail.html", {
        "request": request,
        "promise": promise,
        "cabinets": cabinets,
        "parties": parties,
        "statuses": list(PromiseStatus),
        "categories": list(PromiseCategory),
    })


@router.post("/beloftes/{promise_id}/bewerk")
def update_promise(
    request: Request,
    promise_id: int,
    db: Session = Depends(get_db),
    cabinet_id: int = Form(...),
    party_id: Optional[int] = Form(None),
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form("overig"),
    status: str = Form("beloofd"),
    source_text: str = Form(""),
):
    redir = auth_redirect(request)
    if redir:
        return redir
    promise = db.query(Promise).filter(Promise.id == promise_id).first()
    if not promise:
        raise HTTPException(status_code=404)
    promise.cabinet_id = cabinet_id
    promise.party_id = party_id if party_id else None
    promise.title = title
    promise.description = description
    promise.category = category
    promise.status = status
    promise.source_text = source_text if source_text else None
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
    from datetime import date
    date_obj = None
    if date_published:
        try:
            date_obj = date.fromisoformat(date_published)
        except ValueError:
            pass
    evidence = Evidence(
        promise_id=promise_id,
        title=title,
        url=url if url else None,
        description=description if description else None,
        source_type=source_type if source_type else None,
        date_published=date_obj,
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
