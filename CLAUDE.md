# PoliTrack — Projectgeheugen

## Wat dit project is
Een **Civic Tech platform** dat verkiezingsbeloftes van politieke partijen automatisch
vergelijkt met hun daadwerkelijke stemgedrag en acties in het parlement. Elke belofte
krijgt een status: **Beloofd, In Uitvoering, Waargemaakt, Gebroken, Geparkeerd**.

> **Volledige context:** zie [`docs/project_brief.md`](docs/project_brief.md) — dit is de
> leidende brief (scope, architectuur, landen-roadmap, businessmodel, fiscaliteit).
> Lees dit bestand altijd in aan het begin van een sessie.

## Kernpunten uit de brief (samenvatting)
- **Founder:** solo-ontwikkelaar met intensieve AI-ondersteuning. Bedrijfsvorm: eenmanszaak (KvK).
- **Architectuur:** vanaf dag één **meertalig (i18n:** NL, EN, FR, DE, ES) en **modulair** —
  nieuwe landen als plug-and-play modules (microservices) op één universeel DB-schema.
- **Core logic:** LLM-API knipt verkiezingsprogramma's op in atomische, meetbare beloftes;
  parlementaire data (stemmingen/moties) wordt via AI gematcht aan beloftes, altijd met een
  **verificatielink naar de officiële overheidsbron** (tegen hallucinaties).
- **Landen-roadmap:** Fase 1 Nederland (Tweede Kamer API) → Fase 2 EU-Parlement, Spanje,
  Duitsland → Fase 3 VS, VK, Australië → Fase 4 Brazilië.
- **Verdienmodel:** subsidies (SIDN, SVDJ, EU CERV, Civitates) + crowdfunding/memberships
  (Patreon/Steady) + B2B Data API + white-labeling aan buitenlandse NGO's.
- **AI-prioriteiten in vervolgsessies:** (1) schone modulaire code — Python voor scrapers/AI,
  TypeScript/React of Vue voor frontend, i18n-proof; (2) flexibele API-parsers die
  landspecifieke velden (bv. *votaciones*, *roll-call votes*) mappen naar één universeel schema;
  (3) prompts voor betrouwbare belofte-ontleding.

## Huidige stand van de code (deze repo: `Kiwis92/My-own-database`)
Branch: `claude/build-politrack-app-yFM7H`

De app is doorontwikkeld van NL-MVP naar de **architectuur uit de brief**:
- **Stack:** FastAPI + SQLite + SQLAlchemy + Jinja2. Start: `python import_data.py --reset`
  daarna `uvicorn app.main:app --reload`. Tests: `python tests/test_ingestion_nl.py`.
- **Universeel multi-country schema** (`app/models.py`): `Country` als wortel;
  `Party`, `Election`+`SeatResult`, `Cabinet` (premier/datums/valreden/hoogtepunten),
  `Promise` (source_kind regeerakkoord|verkiezingsprogramma, election_year,
  6 statussen incl. *Deels Waargemaakt*, vrije categorie-strings), `Motion`+`VoteRecord`
  (universeel stemgedrag, roll-call-ready), `PromiseMatch` (voor AI-matching, nog leeg),
  `Evidence`, `PartyFinance`, `PartyAttendance`.
- **Ingestie-architectuur** (`app/ingestion/`): `CountryAdapter`-interface (base.py),
  Tweede Kamer OData-adapter (nl_tweede_kamer.py), loader met partij-aliassen en
  idempotentie op (country, external_id), CLI: `python -m app.ingestion.run nl
  [--fixture]`. 9 offline tests op een echte-structuur fixture.
- **i18n vanaf dag één** (`app/i18n.py` + `app/locales/*.json`): NL/EN volledig,
  DE/FR/ES basis; keuze via `?lang=`, onthouden in cookie; fallback locale→en→nl.
- **Publieke site:** partijdashboard `/partij/{id}` (beloftes per verkiezingsjaar,
  stemgedrag, kabinetsdeelname, zetelhistorie, aanwezigheid), kabinetsdashboard,
  filterbare beloftes, homepage met statistieken.
- **Admin-CMS:** CRUD voor alles, incl. soort belofte/verkiezingsjaar/valreden.

⚠️ **Bekende blocker:** deze sessie kan niet naar `My-own-database` pushen (403 — alleen
leesrechten voor de sessie-integratie). Lezen/fetch werkt wel. Push moet door de eigenaar
zelf (bv. via GitHub Desktop) of nadat de integratie schrijfrechten krijgt op github.com.
Ook uitgaand netwerkverkeer naar externe API's (bv. gegevensmagazijn.tweedekamer.nl) is
in deze omgeving geblokkeerd — gebruik `--fixture` voor offline demo's; live ingestie
werkt op de machine van de eigenaar.

## Volgende stappen richting de brief
1. **AI-belofte-matching:** stemmingen/moties koppelen aan beloftes via LLM →
   vullen van `promise_matches` (relatie steunt/weerspreekt + confidence + verificatie).
2. **LLM-parsing van verkiezingsprogramma's** naar atomische beloftes.
3. **Fase 2-adapters:** EU-Parlement (OAS3), Spanje (Congreso), Duitsland (DIP).
4. Vertalingen DE/FR/ES compleet maken (native review conform brief).

## Consolidatie (besloten)
**Deze repo (`My-own-database`) is de ene canonieke codebasis.** De repo `Kiwis92/PoliTrack`
bevatte een eerdere statische website-variant; de waardevolle inhoud daarvan is overgenomen:

- **`data/politiek_nl.json`** — volledige dataset geëxtraheerd uit `data.js` van die repo:
  21 partijen (incl. historische), 9 verkiezingen (1998–2023), 10 kabinetten (Kok II → Schoof,
  met valredenen en hoogtepunten), 51 partijbeloftes per verkiezingsjaar (status:
  nagekomen/deels/gebroken), 12 wetten + 108 stemgedrag-records per fractie, partijfinanciën
  en aanwezigheidspercentages.
- De statische site zelf, `build_database.py` en de lege `politiek_nl.db` zijn **niet**
  overgenomen (vervangen door de FastAPI-app; db was leeg; script wees naar dood pad).
- De `PoliTrack`-repo geldt als archief; nieuw werk gebeurt hier.

Let op datavocabulaire in de JSON: belofte-statussen zijn `nagekomen`/`deels`/`gebroken`
(dus incl. "deels" — neem een status *Deels Waargemaakt* op in het datamodel), stemmen zijn
`voor`/`tegen`/`onthouden`.
