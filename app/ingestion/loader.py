"""
Schrijft universele records (base.py) naar de database.

Fractienamen uit bron-API's worden gematcht op afkorting, naam of alias;
onbekende fracties worden als nieuwe partij aangemaakt zodat geen stem
verloren gaat.
"""
from sqlalchemy.orm import Session

from ..models import Country, Party, Motion, VoteRecord, MotionKind, VoteChoice
from .base import UniversalMotion

# Aliassen: fractienaam in de bron -> afkorting in onze database
PARTY_ALIASES = {
    "nl": {
        "GroenLinks-PvdA": "GL",       # gecombineerde fractie sinds 2023
        "ChristenUnie": "CU",
        "Partij voor de Dieren": "PvdD",
        "Forum voor Democratie": "FvD",
        "FVD": "FvD",
        "50PLUS": "50+",
        "Groep Van Haga": "BVNL",
        "BIJ1": "Bij1",
    }
}

KIND_MAP = {
    "wet": MotionKind.wet,
    "motie": MotionKind.motie,
    "amendement": MotionKind.amendement,
}


def resolve_party(db: Session, country: Country, source_name: str) -> Party:
    """Zoek een partij op afkorting, naam of alias; maak anders een nieuwe aan."""
    aliases = PARTY_ALIASES.get(country.code, {})
    abbr = aliases.get(source_name, source_name)

    party = (db.query(Party)
             .filter(Party.country_id == country.id)
             .filter((Party.abbreviation == abbr) | (Party.name == source_name))
             .first())
    if party:
        return party

    party = Party(
        country_id=country.id,
        abbreviation=abbr[:20],
        name=source_name,
        color="#64748B",
        active=True,
        description="Automatisch aangemaakt door ingestie.",
    )
    db.add(party)
    db.flush()
    return party


def store_motions(db: Session, country: Country, motions: list[UniversalMotion]) -> dict:
    """Sla universele moties + stemmen op. Idempotent op (country, external_id)."""
    created, skipped, votes_added = 0, 0, 0

    for um in motions:
        exists = (db.query(Motion)
                  .filter(Motion.country_id == country.id,
                          Motion.external_id == um.external_id)
                  .first())
        if exists:
            skipped += 1
            continue

        motion = Motion(
            country_id=country.id,
            external_id=um.external_id,
            kind=KIND_MAP.get(um.kind, MotionKind.motie),
            title=um.title[:500],
            summary=um.summary,
            date=um.date,
            year=um.date.year if um.date else None,
            source_url=um.source_url,
        )
        db.add(motion)
        db.flush()
        created += 1

        for uv in um.votes:
            party = resolve_party(db, country, uv.party)
            db.add(VoteRecord(
                motion_id=motion.id,
                party_id=party.id,
                vote=VoteChoice[uv.vote],
                is_roll_call=uv.is_roll_call,
                politician=uv.politician,
            ))
            votes_added += 1

    db.commit()
    return {"created": created, "skipped": skipped, "votes": votes_added}
