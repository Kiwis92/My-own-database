"""
Seed data script: voegt voorbeelddata toe voor PoliTrack.
Bevat Kabinet-Schoof (2024-heden) met realistische beloftes.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app import models

models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

def run():
    if db.query(models.Party).count() > 0:
        print("Database bevat al data. Seed overgeslagen.")
        return

    print("Partijen aanmaken...")
    parties = {
        "pvv": models.Party(name="Partij voor de Vrijheid", abbreviation="PVV", color="#1E3A8A", description="Nationalistische partij opgericht door Geert Wilders in 2006."),
        "vvd": models.Party(name="Volkspartij voor Vrijheid en Democratie", abbreviation="VVD", color="#FF6600", description="Liberale partij, opgericht in 1948."),
        "nsc": models.Party(name="Nieuw Sociaal Contract", abbreviation="NSC", color="#059669", description="Christendemocratische partij opgericht door Pieter Omtzigt in 2023."),
        "bbb": models.Party(name="BoerBurgerBeweging", abbreviation="BBB", color="#92400E", description="Agrarische volkspartij opgericht in 2019 door Caroline van der Plas."),
        "d66": models.Party(name="Democraten 66", abbreviation="D66", color="#00A651", description="Progressief-liberale partij, opgericht in 1966."),
        "gl_pvda": models.Party(name="GroenLinks-PvdA", abbreviation="GL-PvdA", color="#CC0000", description="Samenwerkingsverband van GroenLinks en de Partij van de Arbeid."),
        "cda": models.Party(name="Christen-Democratisch Appèl", abbreviation="CDA", color="#007B5F", description="Christendemocratische partij opgericht in 1980."),
        "sp": models.Party(name="Socialistische Partij", abbreviation="SP", color="#FF0000", description="Socialistische partij opgericht in 1971."),
        "pvda": models.Party(name="Partij van de Arbeid", abbreviation="PvdA", color="#E3000B", description="Sociaaldemocratische partij, opgericht in 1946."),
    }
    for p in parties.values():
        db.add(p)
    db.flush()
    print(f"  {len(parties)} partijen aangemaakt")

    print("Kabinetten aanmaken...")
    rutte4 = models.Cabinet(
        name="Kabinet-Rutte IV",
        year_start=2022,
        year_end=2024,
        description="Het vierde kabinet onder leiding van Mark Rutte, een coalitie van VVD, D66, CDA en ChristenUnie. Dit kabinet hield op 8 juli 2023 op te bestaan na een kabinetscrisis over het asieldossier.",
        coalition_agreement_url="https://www.rijksoverheid.nl/documenten/publicaties/2021/12/15/coalitieakkoord-omzien-naar-elkaar-vooruitkijken-naar-de-toekomst",
    )
    rutte4.parties = [parties["vvd"], parties["d66"], parties["cda"]]
    db.add(rutte4)

    schoof = models.Cabinet(
        name="Kabinet-Schoof",
        year_start=2024,
        year_end=None,
        description="Het kabinet onder leiding van Dick Schoof, een coalitie van PVV, VVD, NSC en BBB. Aangetreden op 2 juli 2024 na de historische verkiezingsoverwinning van de PVV op 22 november 2023.",
        coalition_agreement_url="https://www.rijksoverheid.nl/documenten/publicaties/2024/05/16/hoofdlijnenakkoord-2024-2028-hoop-lef-en-trots",
    )
    schoof.parties = [parties["pvv"], parties["vvd"], parties["nsc"], parties["bbb"]]
    db.add(schoof)
    db.flush()
    print("  Kabinet-Rutte IV & Kabinet-Schoof aangemaakt")

    print("Beloftes Kabinet-Schoof aanmaken...")
    promises_schoof = [
        # MIGRATIE
        dict(title="Invoering van de strengste migratieaanpak ooit in Nederland",
             description="Het kabinet streeft naar de strengste migratieaanpak in de Nederlandse geschiedenis. Dit omvat het aanvragen van een opt-out uit het Europees asielbeleid, invoering van permanente grenscontroles en versnelde terugkeer van afgewezen asielzoekers.",
             category=models.PromiseCategory.migratie, status=models.PromiseStatus.in_uitvoering,
             source_text="Nederland voert de strengste migratieaanpak ooit in. Wij vragen een opt-out aan voor het Europees asielbeleid."),
        dict(title="Permanente grenscontroles aan de Nederlandse grenzen",
             description="Nederland voert permanente grenscontroles in aan alle binnengrenzen van het Schengengebied om illegale immigratie tegen te gaan.",
             category=models.PromiseCategory.migratie, status=models.PromiseStatus.waargemaakt,
             source_text="Nederland voert permanente grenscontroles in aan alle binnengrenzen."),
        dict(title="Verlaging van de asielinstroom naar minder dan 15.000 per jaar",
             description="Het doel is de totale asielinstroom structureel te beperken tot minder dan 15.000 personen per jaar.",
             category=models.PromiseCategory.migratie, status=models.PromiseStatus.in_uitvoering,
             source_text="De instroom van asielzoekers wordt structureel beperkt tot maximaal 15.000 per jaar."),
        dict(title="Invoering van aanmeldcentra met gesloten karakter bij de grens",
             description="Asielzoekers worden direct bij aankomst in gesloten aanmeldcentra geplaatst terwijl hun verzoek wordt beoordeeld.",
             category=models.PromiseCategory.migratie, status=models.PromiseStatus.beloofd),
        dict(title="Geen permanente verblijfsstatus voor erkende vluchtelingen (tijdelijke bescherming)",
             description="Erkende vluchtelingen krijgen geen permanente verblijfstatus meer, maar tijdelijke bescherming die periodiek wordt beoordeeld.",
             category=models.PromiseCategory.migratie, status=models.PromiseStatus.in_uitvoering,
             source_text="Vluchtelingen ontvangen tijdelijke in plaats van permanente bescherming."),

        # WONEN
        dict(title="Bouw van 100.000 nieuwe woningen per jaar",
             description="Om de woningmarktcrisis aan te pakken streeft het kabinet naar de bouw van minimaal 100.000 nieuwe woningen per jaar. Dit vraagt om een enorme versnelling in de bouwproductie.",
             category=models.PromiseCategory.wonen, status=models.PromiseStatus.in_uitvoering,
             source_text="Er worden jaarlijks minimaal 100.000 woningen gebouwd."),
        dict(title="Afschaffing van de overdrachtsbelasting voor starters",
             description="Voor starters op de woningmarkt wordt de overdrachtsbelasting afgeschaft om de drempel voor woningbezit te verlagen.",
             category=models.PromiseCategory.wonen, status=models.PromiseStatus.beloofd),
        dict(title="Versnelling van woningbouwprojecten door vermindering van regelgeving",
             description="Procedures voor woningbouwprojecten worden ingekort en regelgeving verminderd om de bouw te versnellen.",
             category=models.PromiseCategory.wonen, status=models.PromiseStatus.in_uitvoering),

        # ECONOMIE
        dict(title="Verlaging van de lasten op arbeid",
             description="De belastingdruk op arbeid wordt verlaagd zodat werken meer loont. Dit wordt gerealiseerd door verhoging van de arbeidskorting.",
             category=models.PromiseCategory.economie, status=models.PromiseStatus.in_uitvoering,
             source_text="De lasten op arbeid worden substantieel verlaagd."),
        dict(title="Koopkrachtherstel voor alle Nederlanders",
             description="Het kabinet streeft naar verbetering van de koopkracht voor alle inkomensgroepen, met speciale aandacht voor middeninkomens.",
             category=models.PromiseCategory.economie, status=models.PromiseStatus.in_uitvoering),
        dict(title="Afschaffing van de eigen bijdrage in de Wmo",
             description="De eigen bijdrage voor Wmo-diensten (thuiszorg, dagbesteding) wordt afgeschaft om zorgkosten te verlagen voor kwetsbare groepen.",
             category=models.PromiseCategory.economie, status=models.PromiseStatus.geparkeerd,
             source_text="De eigen bijdrage voor de Wmo wordt afgeschaft."),

        # FINANCIEN
        dict(title="Begrotingstekort onder de EU-norm van 3% BBP houden",
             description="Nederland houdt zich aan de Europese begrotingsregels en zorgt voor een tekort van maximaal 3% van het BBP.",
             category=models.PromiseCategory.financien, status=models.PromiseStatus.in_uitvoering),
        dict(title="Geen verhoging van de AOW-leeftijd boven de 67 jaar",
             description="De AOW-leeftijd wordt niet verhoogd boven de huidige 67 jaar gedurende de kabinetsperiode.",
             category=models.PromiseCategory.financien, status=models.PromiseStatus.beloofd,
             source_text="De AOW-leeftijd stijgt niet boven de 67 jaar."),
        dict(title="Verlaging van de energiebelasting voor huishoudens",
             description="De energiebelasting voor huishoudens wordt verlaagd om de energiekosten betaalbaar te houden.",
             category=models.PromiseCategory.financien, status=models.PromiseStatus.waargemaakt),

        # ZORG
        dict(title="Verlaging van het eigen risico in de zorgverzekering",
             description="Het eigen risico in de zorgverzekering wordt verlaagd van €385 naar €165 in 2027. Dit geeft een significante lastenverlichting voor mensen die veel zorg gebruiken.",
             category=models.PromiseCategory.zorg, status=models.PromiseStatus.in_uitvoering,
             source_text="Het eigen risico wordt in stappen verlaagd naar €165 in 2027."),
        dict(title="Meer geld voor de geestelijke gezondheidszorg (GGZ)",
             description="Extra investeringen in de GGZ om wachttijden te verminderen en zorg toegankelijker te maken.",
             category=models.PromiseCategory.zorg, status=models.PromiseStatus.beloofd),
        dict(title="Aanpak van wachttijden in de zorg",
             description="Structurele aanpak van te lange wachttijden in de curatieve zorg, GGZ en gehandicaptenzorg.",
             category=models.PromiseCategory.zorg, status=models.PromiseStatus.in_uitvoering),

        # VEILIGHEID
        dict(title="3.000 extra agenten op straat",
             description="De politiecapaciteit wordt uitgebreid met 3.000 extra agenten om veiligheid op straat te verbeteren.",
             category=models.PromiseCategory.veiligheid, status=models.PromiseStatus.in_uitvoering,
             source_text="Er komen 3.000 extra politieagenten."),
        dict(title="Harder aanpak van ondermijnende criminaliteit",
             description="Versterking van de aanpak van drugscriminaliteit, witwassen en ondermijning met extra middelen voor politie en justitie.",
             category=models.PromiseCategory.veiligheid, status=models.PromiseStatus.in_uitvoering),
        dict(title="Minimumstraffen invoeren voor zware delicten",
             description="Voor ernstige misdrijven zoals moord, zware mishandeling en zedendelicten worden minimumstraffen ingevoerd.",
             category=models.PromiseCategory.veiligheid, status=models.PromiseStatus.beloofd),

        # DEFENSIE
        dict(title="Defensiebudget naar 2% van het BBP",
             description="Nederland voldoet aan de NAVO-norm door het defensiebudget te verhogen naar minimaal 2% van het bruto binnenlands product.",
             category=models.PromiseCategory.defensie, status=models.PromiseStatus.in_uitvoering,
             source_text="Het defensiebudget stijgt naar 2% BBP conform de NAVO-norm."),
        dict(title="Aanschaf van nieuwe F-35 gevechtsvliegtuigen",
             description="Uitbreiding van de F-35 vloot om de slagkracht van de Nederlandse luchtmacht te versterken.",
             category=models.PromiseCategory.defensie, status=models.PromiseStatus.in_uitvoering),

        # KLIMAAT
        dict(title="Vaart terug op klimaatbeleid – geen extra klimaatmaatregelen",
             description="Het kabinet ziet af van aanvullende klimaatmaatregelen die de economie schaden. Bestaande klimaatdoelen worden heroverwogen.",
             category=models.PromiseCategory.klimaat, status=models.PromiseStatus.in_uitvoering,
             source_text="Nederland neemt geen extra klimaatmaatregelen die de economie schaden."),
        dict(title="Geen verplichte warmtepomp voor huishoudens",
             description="Huishoudens worden niet verplicht een warmtepomp aan te schaffen. De keuze voor verwarmingssysteem blijft bij de consument.",
             category=models.PromiseCategory.klimaat, status=models.PromiseStatus.waargemaakt),
        dict(title="Herziening van de stikstofaanpak",
             description="De stikstofaanpak wordt herzien met meer perspectief voor de agrarische sector en minder gedwongen onteigeningen.",
             category=models.PromiseCategory.klimaat, status=models.PromiseStatus.in_uitvoering,
             source_text="De stikstofaanpak wordt herzien met behoud van perspectief voor de boer."),

        # ONDERWIJS
        dict(title="Aanpak van het lerarentekort",
             description="Gerichte maatregelen om het groeiende lerarentekort te bestrijden, waaronder betere arbeidsvoorwaarden en zij-instroom.",
             category=models.PromiseCategory.onderwijs, status=models.PromiseStatus.in_uitvoering),
        dict(title="Meer aandacht voor basisvaardigheden in het onderwijs",
             description="Versterking van taal, rekenen en digitale vaardigheden als basiscompetenties in het primair en voortgezet onderwijs.",
             category=models.PromiseCategory.onderwijs, status=models.PromiseStatus.in_uitvoering),
    ]

    for p_data in promises_schoof:
        promise = models.Promise(
            cabinet_id=schoof.id,
            **p_data,
        )
        db.add(promise)
    db.flush()
    print(f"  {len(promises_schoof)} beloftes aangemaakt voor Kabinet-Schoof")

    print("Voorbeeldbewijs toevoegen...")
    from datetime import date

    migr_promise = db.query(models.Promise).filter(
        models.Promise.cabinet_id == schoof.id,
        models.Promise.title.ilike("%grenscontroles%")
    ).first()
    if migr_promise:
        db.add(models.Evidence(
            promise_id=migr_promise.id,
            title="IND: grenscontroles van start per 9 december 2024",
            url="https://nos.nl/artikel/2542200-nederland-begint-maandag-met-grenscontroles",
            description="Nederland is op 9 december 2024 begonnen met tijdelijke grenscontroles aan de landsgrenzen. De maatregel is gebaseerd op de Schengengrenscode.",
            source_type="Nieuwsartikel",
            date_published=date(2024, 12, 9),
        ))

    rek_promise = db.query(models.Promise).filter(
        models.Promise.cabinet_id == schoof.id,
        models.Promise.title.ilike("%energiebelasting%")
    ).first()
    if rek_promise:
        db.add(models.Evidence(
            promise_id=rek_promise.id,
            title="Belastingplan 2025: verlaging energiebelasting huishoudens",
            url="https://www.rijksoverheid.nl/onderwerpen/belastingplan",
            description="Onderdeel van het Belastingplan 2025 is de verlaging van de energiebelasting voor kleinverbruikers.",
            source_type="Wetgeving",
            date_published=date(2024, 9, 17),
        ))

    db.commit()
    print("\n✓ Seed data succesvol geladen!")
    print(f"  Partijen: {db.query(models.Party).count()}")
    print(f"  Kabinetten: {db.query(models.Cabinet).count()}")
    print(f"  Beloftes: {db.query(models.Promise).count()}")
    print(f"  Bewijsbronnen: {db.query(models.Evidence).count()}")
    print("\nStart de app met: uvicorn app.main:app --reload")
    print("Publiek: http://localhost:8000")
    print("Admin:   http://localhost:8000/admin  (wachtwoord: admin123)")

if __name__ == "__main__":
    run()
    db.close()
