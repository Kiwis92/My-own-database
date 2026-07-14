"""
Basis voor land-adapters (zie docs/project_brief.md §2).

Elke adapter vertaalt de eigen API van een parlement (Tweede Kamer OData,
EU Open Data Portal, Congreso-API, DIP, api.congress.gov, ...) naar de
universele records hieronder. Daardoor blijft de rest van de applicatie
land-onafhankelijk: nieuwe landen zijn plug-and-play.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Optional


@dataclass
class UniversalVote:
    """Stem van een fractie (of individueel lid bij roll-call) op een motie/wet."""
    party: str                       # fractienaam of afkorting in de bron
    vote: str                        # voor | tegen | onthouden | afwezig
    is_roll_call: bool = False
    politician: Optional[str] = None


@dataclass
class UniversalMotion:
    """Parlementaire handeling, gemapt vanuit een landspecifieke bron."""
    external_id: str                 # ID in de bron-API
    kind: str                        # wet | motie | amendement
    title: str
    summary: Optional[str] = None
    date: Optional[date] = None
    source_url: Optional[str] = None  # verificatielink naar de officiële bron
    votes: list[UniversalVote] = field(default_factory=list)


class CountryAdapter(ABC):
    """Interface voor een land. Implementaties: app/ingestion/<land>_*.py"""

    country_code: str                # bv. "nl"
    legislature_name: str            # bv. "Tweede Kamer"

    @abstractmethod
    def fetch_motions(self, limit: int = 25, since: Optional[date] = None) -> Iterable[UniversalMotion]:
        """Haal recente moties/wetten met stemmingen op, als universele records."""
        raise NotImplementedError

    @abstractmethod
    def parse_motions(self, raw: dict) -> list[UniversalMotion]:
        """Parseer een ruwe API-respons (ook bruikbaar voor fixtures/tests)."""
        raise NotImplementedError
