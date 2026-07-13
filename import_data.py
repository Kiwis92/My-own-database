"""
Importeert de volledige Nederlandse dataset in het universele schema.

Bronnen:
1. data/politiek_nl.json — partijen, verkiezingen, kabinetten (Kok II t/m Schoof),
   51 verkiezingsprogramma-beloftes, wetten + stemgedrag, financiën, aanwezigheid.
2. Ingebouwde lijst met 27 regeerakkoord-beloftes van Kabinet-Schoof (hoofdlijnenakkoord
   2024) inclusief voorbeeldbewijs.

Gebruik:  python import_data.py [--reset]
  --reset  verwijdert eerst de bestaande database
"""
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, DATABASE_URL
from app import models
from app.models import (
    Country, Party, Election, SeatResult, Cabinet, Promise, Motion, VoteRecord,
    Evidence, PartyFinance, PartyAttendance,
    PromiseStatus, PromiseSource, VoteChoice, MotionKind,
)

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "politiek_nl.json")

STATUS_MAP = {
    "nagekomen": PromiseStatus.waargemaakt,
    "deels": PromiseStatus.deels_waargemaakt,
    "gebroken": PromiseStatus.gebroken,
}
VOTE_MAP = {
    "voor": VoteChoice.voor,
    "tegen": VoteChoice.tegen,
    "onthouden": VoteChoice.onthouden,
    "afwezig": VoteChoice.afwezig,
}


def parse_date(s):
    return date.fromisoformat(s) if s else None


# --- 27 regeerakkoord-beloftes Kabinet-Schoof (hoofdlijnenakkoord 2024) ---
SCHOOF_PROMISES = [
    ("Invoering van de strengste migratieaanpak ooit in Nederland", "Migratie", PromiseStatus.in_uitvoering,
     "Opt-out Europees asielbeleid, permanente grenscontroles en versnelde terugkeer van afgewezen asielzoekers.",
     "Nederland voert de strengste migratieaanpak ooit in. Wij vragen een opt-out aan voor het Europees asielbeleid."),
    ("Permanente grenscontroles aan de Nederlandse grenzen", "Migratie", PromiseStatus.waargemaakt,
     "Nederland voert grenscontroles in aan de binnengrenzen van het Schengengebied om illegale immigratie tegen te gaan.",
     "Nederland voert permanente grenscontroles in aan alle binnengrenzen."),
    ("Verlaging van de asielinstroom naar minder dan 15.000 per jaar", "Migratie", PromiseStatus.in_uitvoering,
     "De totale asielinstroom structureel beperken tot minder dan 15.000 personen per jaar.",
     "De instroom van asielzoekers wordt structureel beperkt tot maximaal 15.000 per jaar."),
    ("Invoering van aanmeldcentra met gesloten karakter bij de grens", "Migratie", PromiseStatus.beloofd,
     "Asielzoekers worden direct bij aankomst in gesloten aanmeldcentra geplaatst tijdens de beoordeling.", None),
    ("Geen permanente verblijfsstatus voor erkende vluchtelingen", "Migratie", PromiseStatus.in_uitvoering,
     "Erkende vluchtelingen krijgen tijdelijke bescherming die periodiek wordt beoordeeld.",
     "Vluchtelingen ontvangen tijdelijke in plaats van permanente bescherming."),
    ("Bouw van 100.000 nieuwe woningen per jaar", "Wonen", PromiseStatus.in_uitvoering,
     "Minimaal 100.000 nieuwe woningen per jaar om de woningmarktcrisis aan te pakken.",
     "Er worden jaarlijks minimaal 100.000 woningen gebouwd."),
    ("Afschaffing van de overdrachtsbelasting voor starters", "Wonen", PromiseStatus.beloofd,
     "Voor starters wordt de overdrachtsbelasting afgeschaft om woningbezit toegankelijker te maken.", None),
    ("Versnelling van woningbouwprojecten door minder regelgeving", "Wonen", PromiseStatus.in_uitvoering,
     "Procedures voor woningbouw worden ingekort en regelgeving verminderd.", None),
    ("Verlaging van de lasten op arbeid", "Belasting", PromiseStatus.in_uitvoering,
     "De belastingdruk op arbeid wordt verlaagd zodat werken meer loont.",
     "De lasten op arbeid worden substantieel verlaagd."),
    ("Koopkrachtherstel voor alle Nederlanders", "Economie", PromiseStatus.in_uitvoering,
     "Verbetering van de koopkracht voor alle inkomensgroepen, met nadruk op middeninkomens.", None),
    ("Afschaffing van de eigen bijdrage in de Wmo", "Zorg", PromiseStatus.geparkeerd,
     "De eigen bijdrage voor Wmo-diensten wordt afgeschaft om zorgkosten te verlagen.",
     "De eigen bijdrage voor de Wmo wordt afgeschaft."),
    ("Begrotingstekort onder de EU-norm van 3% BBP houden", "Economie", PromiseStatus.in_uitvoering,
     "Nederland houdt zich aan de Europese begrotingsregels.", None),
    ("Geen verhoging van de AOW-leeftijd boven de 67 jaar", "Pensioenen", PromiseStatus.beloofd,
     "De AOW-leeftijd wordt deze kabinetsperiode niet verhoogd boven de 67 jaar.",
     "De AOW-leeftijd stijgt niet boven de 67 jaar."),
    ("Verlaging van de energiebelasting voor huishoudens", "Belasting", PromiseStatus.waargemaakt,
     "De energiebelasting voor huishoudens wordt verlaagd om energiekosten betaalbaar te houden.", None),
    ("Verlaging van het eigen risico in de zorgverzekering", "Zorg", PromiseStatus.in_uitvoering,
     "Het eigen risico wordt verlaagd van €385 naar €165 in 2027.",
     "Het eigen risico wordt in stappen verlaagd naar €165 in 2027."),
    ("Meer geld voor de geestelijke gezondheidszorg (GGZ)", "Zorg", PromiseStatus.beloofd,
     "Extra investeringen in de GGZ om wachttijden te verminderen.", None),
    ("Aanpak van wachttijden in de zorg", "Zorg", PromiseStatus.in_uitvoering,
     "Structurele aanpak van wachttijden in curatieve zorg, GGZ en gehandicaptenzorg.", None),
    ("3.000 extra agenten op straat", "Veiligheid", PromiseStatus.in_uitvoering,
     "Uitbreiding van de politiecapaciteit met 3.000 agenten.",
     "Er komen 3.000 extra politieagenten."),
    ("Hardere aanpak van ondermijnende criminaliteit", "Veiligheid", PromiseStatus.in_uitvoering,
     "Versterkte aanpak van drugscriminaliteit, witwassen en ondermijning.", None),
    ("Minimumstraffen invoeren voor zware delicten", "Justitie", PromiseStatus.beloofd,
     "Voor ernstige misdrijven worden minimumstraffen ingevoerd.", None),
    ("Defensiebudget naar 2% van het BBP", "Defensie", PromiseStatus.in_uitvoering,
     "Het defensiebudget stijgt naar minimaal 2% BBP conform de NAVO-norm.",
     "Het defensiebudget stijgt naar 2% BBP conform de NAVO-norm."),
    ("Aanschaf van nieuwe F-35 gevechtsvliegtuigen", "Defensie", PromiseStatus.in_uitvoering,
     "Uitbreiding van de F-35-vloot van de Nederlandse luchtmacht.", None),
    ("Geen extra klimaatmaatregelen die de economie schaden", "Klimaat", PromiseStatus.in_uitvoering,
     "Bestaande klimaatdoelen worden heroverwogen; geen aanvullende maatregelen die de economie schaden.",
     "Nederland neemt geen extra klimaatmaatregelen die de economie schaden."),
    ("Geen verplichte warmtepomp voor huishoudens", "Klimaat", PromiseStatus.waargemaakt,
     "De verplichting tot aanschaf van een warmtepomp vervalt; de keuze blijft bij de consument.", None),
    ("Herziening van de stikstofaanpak", "Landbouw", PromiseStatus.in_uitvoering,
     "De stikstofaanpak wordt herzien met meer perspectief voor de agrarische sector.",
     "De stikstofaanpak wordt herzien met behoud van perspectief voor de boer."),
    ("Aanpak van het lerarentekort", "Onderwijs", PromiseStatus.in_uitvoering,
     "Maatregelen tegen het lerarentekort: betere arbeidsvoorwaarden en zij-instroom.", None),
    ("Meer aandacht voor basisvaardigheden in het onderwijs", "Onderwijs", PromiseStatus.in_uitvoering,
     "Versterking van taal, rekenen en digitale vaardigheden in het funderend onderwijs.", None),
]


def run(reset: bool = False):
    if reset and "sqlite" in DATABASE_URL:
        db_file = DATABASE_URL.split("///")[-1].lstrip("./")
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_file)
        if os.path.exists(path):
            os.remove(path)
            print(f"Database verwijderd: {path}")

    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(Party).count() > 0:
            print("Database bevat al data. Gebruik --reset om opnieuw te importeren.")
            return

        with open(DATA_PATH, encoding="utf-8") as f:
            data = json.load(f)

        # 1. Land
        nl = Country(
            code="nl", name="Nederland", legislature_name="Tweede Kamer",
            api_source="https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0",
        )
        db.add(nl)
        db.flush()

        # 2. Partijen
        party_by_abbr = {}
        for p in data["partijen"]:
            party = Party(
                country_id=nl.id,
                abbreviation=p["id"],
                name=p["naam"],
                ideology=p.get("ideologie"),
                color=p.get("kleur", "#3B82F6"),
                founded_year=p.get("opgericht"),
                active=p.get("actief", True),
                current_seats=p.get("huidigeZetels"),
                description=p.get("omschrijving"),
            )
            db.add(party)
            party_by_abbr[p["id"]] = party
        db.flush()
        print(f"Partijen: {len(party_by_abbr)}")

        # 3. Verkiezingen + zetels
        n_seats = 0
        for v in data["verkiezingen"]:
            election = Election(country_id=nl.id, year=v["jaar"], date=parse_date(v.get("datum")),
                                turnout=v.get("opkomst"))
            db.add(election)
            db.flush()
            for abbr, seats in v.get("zetels", {}).items():
                if abbr in party_by_abbr:
                    db.add(SeatResult(election_id=election.id, party_id=party_by_abbr[abbr].id, seats=seats))
                    n_seats += 1
        print(f"Verkiezingen: {len(data['verkiezingen'])} ({n_seats} zetelresultaten)")

        # 4. Kabinetten
        cabinet_by_slug = {}
        for k in data["kabinetten"]:
            cab = Cabinet(
                country_id=nl.id,
                slug=k["id"],
                name=k["naam"],
                premier=k.get("premier"),
                premier_party_id=party_by_abbr[k["partijPremier"]].id if k.get("partijPremier") in party_by_abbr else None,
                start_date=parse_date(k.get("start")),
                end_date=parse_date(k.get("eind")),
                seats=k.get("zetels"),
                fell=bool(k.get("gevallen")),
                fall_reason=k.get("valReden"),
                description=k.get("beschrijving"),
                highlights=json.dumps(k.get("hoogtepunten", []), ensure_ascii=False),
            )
            cab.parties = [party_by_abbr[a] for a in k.get("coalitie", []) if a in party_by_abbr]
            db.add(cab)
            cabinet_by_slug[k["id"]] = cab
        db.flush()
        # Regeerakkoord-links
        if "schoof" in cabinet_by_slug:
            cabinet_by_slug["schoof"].coalition_agreement_url = (
                "https://www.rijksoverheid.nl/documenten/publicaties/2024/05/16/hoofdlijnenakkoord-2024-2028-hoop-lef-en-trots")
        if "rutte4" in cabinet_by_slug:
            cabinet_by_slug["rutte4"].coalition_agreement_url = (
                "https://www.rijksoverheid.nl/documenten/publicaties/2021/12/15/coalitieakkoord-omzien-naar-elkaar-vooruitkijken-naar-de-toekomst")
        print(f"Kabinetten: {len(cabinet_by_slug)}")

        # 5a. Verkiezingsprogramma-beloftes (uit JSON)
        for b in data["beloftes"]:
            if b["partij"] not in party_by_abbr:
                continue
            db.add(Promise(
                source_kind=PromiseSource.verkiezingsprogramma,
                party_id=party_by_abbr[b["partij"]].id,
                election_year=b["jaar"],
                title=b["omschrijving"],
                category=b.get("categorie", "Overig"),
                status=STATUS_MAP.get(b["status"], PromiseStatus.beloofd),
            ))
        print(f"Verkiezingsprogramma-beloftes: {len(data['beloftes'])}")

        # 5b. Regeerakkoord-beloftes Kabinet-Schoof
        schoof = cabinet_by_slug.get("schoof")
        evidence_targets = {}
        for title, cat, status, desc, source in SCHOOF_PROMISES:
            promise = Promise(
                source_kind=PromiseSource.regeerakkoord,
                cabinet_id=schoof.id if schoof else None,
                title=title, category=cat, status=status,
                description=desc, source_text=source,
            )
            db.add(promise)
            evidence_targets[title] = promise
        db.flush()
        print(f"Regeerakkoord-beloftes (Schoof): {len(SCHOOF_PROMISES)}")

        # 5c. Voorbeeldbewijs
        ev1 = evidence_targets.get("Permanente grenscontroles aan de Nederlandse grenzen")
        if ev1:
            db.add(Evidence(
                promise_id=ev1.id,
                title="Nederland begint met grenscontroles",
                url="https://nos.nl/artikel/2542200-nederland-begint-maandag-met-grenscontroles",
                description="Nederland is op 9 december 2024 begonnen met grenscontroles aan de landsgrenzen.",
                source_type="Nieuwsartikel", date_published=date(2024, 12, 9),
            ))
        ev2 = evidence_targets.get("Verlaging van de energiebelasting voor huishoudens")
        if ev2:
            db.add(Evidence(
                promise_id=ev2.id,
                title="Belastingplan 2025: verlaging energiebelasting huishoudens",
                url="https://www.rijksoverheid.nl/onderwerpen/belastingplan",
                description="Onderdeel van het Belastingplan 2025 is de verlaging van de energiebelasting voor kleinverbruikers.",
                source_type="Wetgeving", date_published=date(2024, 9, 17),
            ))

        # 6. Wetten + stemgedrag
        motion_by_ext = {}
        for w in data["wetten"]:
            motion = Motion(
                country_id=nl.id,
                external_id=f"wet-{w['id']}",
                kind=MotionKind.wet,
                title=w["naam"],
                summary=w.get("omschrijving"),
                year=w.get("jaar"),
            )
            db.add(motion)
            motion_by_ext[w["id"]] = motion
        db.flush()
        n_votes = 0
        for s in data["stemgedrag"]:
            if s["wetId"] in motion_by_ext and s["partij"] in party_by_abbr:
                db.add(VoteRecord(
                    motion_id=motion_by_ext[s["wetId"]].id,
                    party_id=party_by_abbr[s["partij"]].id,
                    vote=VOTE_MAP[s["stem"]],
                ))
                n_votes += 1
        print(f"Wetten: {len(motion_by_ext)}, stemmen: {n_votes}")

        # 7. Financiën & aanwezigheid
        for f_ in data.get("financien", []):
            if f_["partij"] in party_by_abbr:
                db.add(PartyFinance(party_id=party_by_abbr[f_["partij"]].id, year=f_["jaar"],
                                    subsidy=f_.get("subsidie"), donations=f_.get("donaties"),
                                    contributions=f_.get("contributies")))
        for a in data.get("aanwezigheid", []):
            if a["partij"] in party_by_abbr:
                db.add(PartyAttendance(party_id=party_by_abbr[a["partij"]].id, year=a["jaar"],
                                       percentage=a["percentage"]))
        print(f"Financiën: {len(data.get('financien', []))}, aanwezigheid: {len(data.get('aanwezigheid', []))}")

        db.commit()
        print("\n✓ Import voltooid")
        print(f"  Beloftes totaal: {db.query(Promise).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
