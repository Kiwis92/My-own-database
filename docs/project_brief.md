# Project Brief: Internationaal Politiek Belofte- & Stemgedrag Platform (Civic Tech)

Dit document dient als context-prompt voor AI-assistenten (zoals Cursor, ChatGPT, Claude) om direct de volledige scope, architectuur en het businessmodel van dit project te begrijpen.

---

## 1. Project Definitie & Doelstelling
Het project betreft een schaalbare webapplicatie/mobiele app (Civic Tech) die verkiezingsbeloften van politieke partijen automatisch vergelijkt met hun daadwerkelijke stemgedrag en acties in het parlement. 

### Kerngegevens:
* **Founder Rol:** Solo-ontwikkelaar die zelf het design, de UX en de volledige development oppakt met intensieve AI-ondersteuning (Cursor, Copilot, LLM-API's).
* **Architectuur:** Vanaf dag één meertalig opgezet (i18n: Nederlands, Engels, Frans, Duits, Spaans) en modulair ontworpen, zodat nieuwe landen als plug-and-play modules (microservices) kunnen worden toegevoegd.
* **Core Logic:** Verkiezingsprogramma's worden via een LLM-API opgeknipt in concrete, meetbare beloftes. Binnenkomende parlementaire data (stemmingen/moties) worden via AI gematcht aan deze beloftes met een verificatielink naar de officiële overiteitsbron om hallucinaties te voorkomen.

---

## 2. Landenanalyse & Data-Infrastructuur
De focus ligt op landen met een hoge mate van openheid en machine-readable data (JSON/XML via stabiele API's):

1. **Nederland (Fase 1 - Basis):** Tweede Kamer API. Goede data, per fractie en soms hoofdelijk. Basis voor lokale subsidies.
2. **Europees Parlement (Fase 2):** Open Data Portal (OAS3 API). Strategisch cruciaal voor grote EU-subsidies. Levert *roll-call votes* (hoofdelijk).
3. **Spanje (Fase 2):** *El Congreso de los Diputados* API (JSON/XML/CSV). Uitstekende data-infrastructuur. Politiek zeer relevant vanwege complexe coalities waarbij beloftes snel worden opgeofferd. Tevens de poort naar de Spaanstalige wereld.
4. **Duitsland (Fase 2):** *DIP API* van de Bondsdag. Degelijke data, grote afzetmarkt.
5. **Amerika (Fase 3):** `api.congress.gov` & ProPublica Congress API. Extreem hoge datakwaliteit en enorme markt voor crowdfunding.
6. **Engeland (Fase 3):** `api.parliament.uk`. Uitstekende open data traditie, bruikbaar voor snelle AI-integratie.
7. **Australië (Fase 3):** Vergelijkbaar met het Britse Westminster-model, zeer gestructureerd.
8. **Brazilië (Fase 4):** *Dados Abertos* (OpenAPI). Superieure technische structuur in Zuid-Amerika, perfecte match voor de uitbreiding na Spanje.

*Opmerking over Suriname:* Heeft momenteel geen openbare API (veel handwerk/ongestructureerde PDF's), daarom uitgesteld naar latere fases.

---

## 3. Financiering & Verdienmodel
Om van dit project een fulltime baan te maken, wordt een hybride model gehanteerd van subsidies (korte termijn cashflow) en terugkerende inkomsten (lange termijn stabiliteit).

### Subsidies:
* **SIDN Fonds (NL):** €10.000 (pioniersfase) tot €75.000. Focus op maatschappelijke internetwaarde.
* **SVDJ (Stimuleringsfonds voor de Journalistiek - NL):** €10.000 - €75.000 voor innovatieve informatievoorziening.
* **EU CERV Programme (Citizens, Equality, Rights and Values):** €50.000 - €250.000+. Vereist Europese schaal/consortium (vandaar de vroege integratie van de EU en Spanje/Duitsland).
* **Civitates:** €50.000 - €150.000. Europees fonds tegen desinformatie en voor democratische transparantie.

### Alternatieve Inkomstenstromen:
* **Crowdfunding & Memberships (B2C):** Via platforms zoals Patreon of Steady. Doelgroep: politiek geëngageerde burgers. Premium features zoals realtime push-notificaties bij belofte-breuk. Potentieel: €3.000 - €5.000+ p.m. bij internationale schaal.
* **B2B Data API:** Toegang tot opgeschoonde, gestructureerde politieke data verkopen aan mediahuizen, universiteiten en denktanks. (€250 - €1.500 p.m. per afnemer).
* **White-labeling:** De softwarestructuur licentiëren aan buitenlandse NGO's die zelf hun lokale data invoeren. (€5.000 - €20.000 eenmalig + support fees).

---

## 4. Bedrijfsstructuur & Fiscaliteit (Nederlandse Eenmanszaak)
Het project wordt gestart als een **Eenmanszaak** bij de KvK.

* **Aansprakelijkheid:** Volledig privé-aansprakelijk. *Cruciaal:* Disclaimers en waterdichte Algemene Voorwaarden om juridische claims van politici/partijen te voorkomen bij data-mismatch.
* **Inkomstenbelasting (Box 1):** Belasting over de nettowinst (Omzet minus aftrekbare kosten zoals hosting, AI-API's, hardware).
* **Fiscale Voordelen (bij >1225 uur/jaar):** Zelfstandigenaftrek, Startersaftrek en Mkb-winstvrijstelling (12,7% winst belastingvrij). Effectieve belastingdruk op modale winst ligt rond de 20-25% (excl. 5,3% Zvw-bijdrage).
* **Btw-regels (Internationaal):**
  * *Subsidies:* Vrijgesteld van btw.
  * *Crowdfunding (Patreon):* Patreon fungeert als *Merchant of Record*, regelt de lokale btw en stort de netto-omzet door.
  * *B2B Binnen EU:* Btw verleggen naar het buitenlandse btw-nummer van de klant (0%).
  * *B2B Buiten EU (VS/VK):* Buiten de scope van EU-btw (0%).

---

## 5. Roadmap & Uitroltijdspad (12 Maanden)

* **Maand 1 - 3 (Fase 1: De Basis):** * Ontwikkeling meertalige core-architectuur.
  * Koppeling Nederlandse Tweede Kamer API + AI-belofte-matching engine.
  * Aanvraag SIDN / SVDJ opstartsubsidies (€10k - €25k).
* **Maand 4 - 6 (Fase 2: EU & Spanje):**
  * Integratie Europees Parlement, Spanje (Congreso) en Duitsland (Bundestag).
  * Activering Spaanse en Duitse taalversies (AI-generated + native review).
  * Lancering Patreon/Steady crowdfunding.
  * Grote EU-subsidieaanvragen (CERV / Civitates).
* **Maand 7 - 9 (Fase 3: De Anglo-Saksische Golf):**
  * Integratie Amerika (Congress API), Engeland en Australië.
  * Marketingpush op internationale communities (Reddit, ProductHunt).
  * Start B2B API-verkoop aan media en universiteiten.
  * *Doelstelling:* Crowdfunding groeit naar €1.000 - €2.500 p.m.
* **Maand 10 - 12 (Fase 4: Wereldwijd & B2B Opschaling):**
  * Integratie Brazilië (Dados Abertos) en uitrol volledige Spaanse/Portugese markt.
  * Verkoop van White-label softwarelicenties aan buitenlandse NGO's.
  * *Doelstelling:* Transitie naar fulltime inkomen (€3.000 - €5.000+ Monthly Recurring Revenue) + uitbetaling grote EU-subsidies als buffer.

---

## 6. Instructies voor de AI bij vervolgsessies
Wanneer dit document wordt ingeladen, help de gebruiker met de volgende prioriteiten:
1. Schrijf schone, modulaire code (bij voorkeur Python voor scrapers/AI en TypeScript/React of Vue voor frontend) die voldoet aan de i18n-standaarden.
2. Ontwerp API-parsers die flexibel genoeg zijn om data van verschillende landen (met behoud van specifieke velden zoals *votaciones* of *roll-call votes*) te mappen naar één universeel database-schema.
3. Help bij het formuleren van prompts voor de LLM-API om verkiezingsprogramma's betrouwbaar te ontleden in atomische, testbare beloftes.