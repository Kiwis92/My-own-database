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

Er staat een werkende **MVP** (bewust simpel, Nederland-only, handmatig CMS):
- **Stack:** FastAPI + SQLite + SQLAlchemy + Jinja2 templates.
- **Publieke site:** homepage met statistieken, filterbare beloftes (kabinet/partij/status/
  categorie), kabinetten met voortgangsbalk, detailpagina per belofte met bewijsbronnen.
- **Admin-CMS:** login (wachtwoord via `.env`), CRUD voor partijen/kabinetten/beloftes/bewijs.
- **Datamodel:** `Party`, `Cabinet`, `Promise` (5 statussen, 13 categorieën), `Evidence`.
- **Seed data:** 27 echte beloftes van Kabinet-Schoof. Draaien: `uvicorn app.main:app --reload`.

⚠️ **Bekende blocker:** deze sessie kan niet naar `My-own-database` pushen (403 — alleen
leesrechten voor de sessie-integratie). Lezen/fetch werkt wel. Push moet door de eigenaar
zelf (bv. via GitHub Desktop) of nadat de integratie schrijfrechten krijgt op github.com.

## Belangrijke discrepantie: MVP vs. brief
De brief beschrijft een **ambitieuzere internationale, geautomatiseerde** visie (AI-matching,
meertalig, meerdere landen). De huidige code is de **handmatige NL-MVP** uit de oorspronkelijke
blauwdruk. Bij vervolgwerk: stem met de gebruiker af of we de MVP doorontwikkelen richting de
brief (i18n-laag, universeel multi-country schema, LLM-parsing, Tweede Kamer API-ingestie) of
eerst de MVP afronden.

## Gerelateerde repo
`Kiwis92/PoliTrack` (gecloned in `/home/user/PoliTrack`, branch `master`) bevat een eerdere,
**statische** website-variant (`index.html`/`style.css`/`script.js` + een map "Claude gegenereerd"
met `data.js`, `app.js`, `build_database.py`, `politiek_nl.db`). Nog te beslissen of/hoe deze
samengevoegd wordt met de FastAPI-app.
