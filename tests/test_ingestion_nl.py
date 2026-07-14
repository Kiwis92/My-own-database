"""
Tests voor de Tweede Kamer-adapter en de universele loader.
Draait volledig offline op een fixture (echte OData-structuur) en een
in-memory SQLite database.

Draaien:  python -m pytest tests/ -v   (of: python tests/test_ingestion_nl.py)
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Country, Party, Motion, VoteRecord, VoteChoice
from app.ingestion.nl_tweede_kamer import TweedeKamerAdapter
from app.ingestion.loader import store_motions, resolve_party

FIXTURE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "app", "ingestion", "fixtures", "nl_zaak_moties.json")


def load_fixture():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


class TestTweedeKamerParser(unittest.TestCase):
    def setUp(self):
        self.adapter = TweedeKamerAdapter()
        self.motions = self.adapter.parse_motions(load_fixture())

    def test_parses_all_motions(self):
        self.assertEqual(len(self.motions), 3)

    def test_motion_fields(self):
        m = self.motions[0]
        self.assertEqual(m.kind, "motie")
        self.assertIn("woningbouw", m.title)
        self.assertEqual(m.date.isoformat(), "2024-11-21")
        self.assertTrue(m.source_url.startswith("https://gegevensmagazijn.tweedekamer.nl"))
        self.assertIn(m.external_id, m.source_url)

    def test_votes_mapped_to_universal_vocabulary(self):
        votes = {v.party: v.vote for v in self.motions[0].votes}
        self.assertEqual(votes["PVV"], "voor")
        self.assertEqual(votes["D66"], "tegen")
        self.assertEqual(votes["FVD"], "afwezig")
        onthouden = {v.party: v.vote for v in self.motions[1].votes}
        self.assertEqual(onthouden["SGP"], "onthouden")

    def test_motion_without_votes(self):
        self.assertEqual(self.motions[2].votes, [])


class TestLoader(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        self.country = Country(code="nl", name="Nederland", legislature_name="Tweede Kamer")
        self.db.add(self.country)
        # Bestaande partijen zoals in productie
        for abbr, name in [("PVV", "Partij voor de Vrijheid"), ("VVD", "Volkspartij voor Vrijheid en Democratie"),
                           ("GL", "GroenLinks"), ("CU", "ChristenUnie"), ("FvD", "Forum voor Democratie")]:
            self.db.add(Party(country_id=1, abbreviation=abbr, name=name))
        self.db.commit()
        self.motions = TweedeKamerAdapter().parse_motions(load_fixture())

    def test_store_creates_motions_and_votes(self):
        result = store_motions(self.db, self.country, self.motions)
        self.assertEqual(result["created"], 3)
        self.assertEqual(result["votes"], 14)
        self.assertEqual(self.db.query(Motion).count(), 3)
        self.assertEqual(self.db.query(VoteRecord).count(), 14)

    def test_idempotent_on_external_id(self):
        store_motions(self.db, self.country, self.motions)
        result = store_motions(self.db, self.country, self.motions)
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["skipped"], 3)
        self.assertEqual(self.db.query(Motion).count(), 3)

    def test_party_alias_resolution(self):
        # "GroenLinks-PvdA" (bron) -> bestaande partij GL via alias
        party = resolve_party(self.db, self.country, "GroenLinks-PvdA")
        self.assertEqual(party.abbreviation, "GL")
        # "ChristenUnie" (bron) -> CU via alias
        party = resolve_party(self.db, self.country, "ChristenUnie")
        self.assertEqual(party.abbreviation, "CU")
        # "FVD" (bron) -> FvD via alias
        party = resolve_party(self.db, self.country, "FVD")
        self.assertEqual(party.abbreviation, "FvD")

    def test_unknown_party_is_created(self):
        before = self.db.query(Party).count()
        party = resolve_party(self.db, self.country, "Nieuwe Splinterpartij")
        self.assertEqual(self.db.query(Party).count(), before + 1)
        self.assertEqual(party.name, "Nieuwe Splinterpartij")

    def test_vote_choices_stored_correctly(self):
        store_motions(self.db, self.country, self.motions)
        fvd = self.db.query(Party).filter(Party.abbreviation == "FvD").first()
        vote = self.db.query(VoteRecord).filter(VoteRecord.party_id == fvd.id).first()
        self.assertEqual(vote.vote, VoteChoice.afwezig)


if __name__ == "__main__":
    unittest.main(verbosity=2)
