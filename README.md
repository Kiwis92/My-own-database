# PoliTrack

**Houden politici hun beloftes?** PoliTrack is een onafhankelijk civic-tech platform dat
politieke beloftes uit verkiezingsprogramma's en regeerakkoorden centraliseert en de
uitvoering ervan transparant monitort — per partij, per kabinet, met bewijsbronnen.

> Volledige projectvisie: [`docs/project_brief.md`](docs/project_brief.md)

## Snel starten

```bash
pip install -r requirements.txt
cp .env.example .env            # pas SECRET_KEY en ADMIN_PASSWORD aan
python import_data.py --reset   # laadt de volledige NL-dataset
uvicorn app.main:app --reload
```

- **Publieke site:** http://localhost:8000
- **Beheer (CMS):** http://localhost:8000/admin — wachtwoord uit `.env`

## Wat zit erin

| Onderdeel | Inhoud |
|---|---|
| **Data** | 21 partijen, 9 verkiezingen (1998–2023), 10 kabinetten (Kok II → Schoof), 78 beloftes, 12 wetten met 108 fractiestemmen, partijfinanciën, aanwezigheid |
| **Dashboard per partij** | `/partij/{id}`: beloftes per verkiezingsjaar met status, stemgedrag, kabinetsdeelname, zetelhistorie |
| **Dashboard per kabinet** | `/kabinet/{id}`: regeerakkoord-beloftes, voortgang, valreden, verkiezingsbeloftes van de coalitie |
| **Statussen** | Beloofd · In Uitvoering · Deels Waargemaakt · Waargemaakt · Gebroken · Geparkeerd |
| **i18n** | NL/EN volledig; DE/FR/ES basis. Taalkiezer in de navigatie (`?lang=en`) |
| **Admin-CMS** | CRUD voor partijen, kabinetten, beloftes en bewijsbronnen |

## Architectuur

```
app/
  models.py        # universeel multi-country schema (Country → Party/Cabinet/Motion/...)
  i18n.py          # vertaallaag; teksten in app/locales/*.json
  routers/         # public (website) + admin (CMS)
  templates/       # Jinja2
  ingestion/       # land-adapters (plug-and-play, zie hieronder)
data/politiek_nl.json   # NL-brondata
import_data.py          # eenmalige import
tests/                  # offline tests (fixtures, in-memory db)
```

### Data-ingestie per land

Elke parlementaire API wordt via een adapter gemapt naar één universeel schema
(`Motion` + `VoteRecord`, incl. roll-call votes). Nederland (Tweede Kamer OData) is
geïmplementeerd; EU/ES/DE/US/GB/AU/BR volgen conform de fasering in de brief.

```bash
python -m app.ingestion.run nl --limit 25      # live Tweede Kamer API
python -m app.ingestion.run nl --fixture       # offline demo met voorbeelddata
python tests/test_ingestion_nl.py              # tests (geen netwerk nodig)
```

Elke motie krijgt een **verificatielink naar de officiële bron** — koppelingen aan
beloftes (tabel `promise_matches`) zijn daardoor altijd controleerbaar.

## Roadmap (samengevat uit de brief)

1. **Fase 1 (nu):** NL-basis, handmatige redactie + TK-ingestie
2. **Fase 2:** EU-Parlement, Spanje, Duitsland + AI-belofte-matching
3. **Fase 3:** VS, VK, Australië + B2B data-API
4. **Fase 4:** Brazilië, white-labeling
