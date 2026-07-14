"""
Adapter voor de Nederlandse Tweede Kamer (OData v4 "Gegevensmagazijn").

API-documentatie: https://opendata.tweedekamer.nl/documentatie/odata-api
Basis-URL:        https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0

Datamodel in de bron:
  Zaak (Soort='Motie') --> Besluit --> Stemming (per fractie: Soort=Voor/Tegen)

Elke motie krijgt een verificatielink naar de officiële bron zodat elke
statuswijziging/koppeling controleerbaar is (anti-hallucinatie-eis uit de brief).
"""
from datetime import date, datetime
from typing import Iterable, Optional

import requests

from .base import CountryAdapter, UniversalMotion, UniversalVote

BASE_URL = "https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0"

# Mapping van TK-stemsoorten naar het universele vocabulaire
VOTE_MAP = {
    "Voor": "voor",
    "Tegen": "tegen",
    "Onthouding": "onthouden",
    "Niet deelgenomen": "afwezig",
}


class TweedeKamerAdapter(CountryAdapter):
    country_code = "nl"
    legislature_name = "Tweede Kamer"

    def __init__(self, session: Optional[requests.Session] = None, timeout: int = 30):
        self.session = session or requests.Session()
        self.timeout = timeout

    # --- Netwerk ---

    def fetch_motions(self, limit: int = 25, since: Optional[date] = None) -> Iterable[UniversalMotion]:
        filters = ["Soort eq 'Motie'", "Verwijderd eq false"]
        if since:
            filters.append(f"GestartOp ge {since.isoformat()}T00:00:00Z")
        params = {
            "$filter": " and ".join(filters),
            "$orderby": "GestartOp desc",
            "$top": str(limit),
            "$expand": "Besluit($expand=Stemming)",
        }
        response = self.session.get(f"{BASE_URL}/Zaak", params=params, timeout=self.timeout)
        response.raise_for_status()
        return self.parse_motions(response.json())

    # --- Parsen (netwerk-onafhankelijk; ook gebruikt door tests/fixtures) ---

    def parse_motions(self, raw: dict) -> list[UniversalMotion]:
        motions = []
        for zaak in raw.get("value", []):
            votes = []
            for besluit in zaak.get("Besluit") or []:
                for stemming in besluit.get("Stemming") or []:
                    if stemming.get("Verwijderd"):
                        continue
                    universal = VOTE_MAP.get(stemming.get("Soort"))
                    fractie = stemming.get("ActorFractie")
                    if not universal or not fractie:
                        continue
                    votes.append(UniversalVote(
                        party=fractie,
                        vote=universal,
                        is_roll_call=not stemming.get("FractieGrootte"),
                        politician=stemming.get("ActorNaam") if not stemming.get("FractieGrootte") else None,
                    ))
            motions.append(UniversalMotion(
                external_id=zaak["Id"],
                kind="motie",
                title=zaak.get("Titel") or zaak.get("Onderwerp") or "Onbekende motie",
                summary=zaak.get("Onderwerp"),
                date=self._parse_date(zaak.get("GestartOp")),
                source_url=f"{BASE_URL}/Zaak({zaak['Id']})",
                votes=votes,
            ))
        return motions

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[date]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            return None
