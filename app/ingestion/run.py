"""
CLI voor data-ingestie per land.

Gebruik:
    python -m app.ingestion.run nl [--limit 25] [--since 2024-01-01]
    python -m app.ingestion.run nl --fixture   # offline demo met voorbeelddata

Nieuwe landen: voeg een adapter toe aan ADAPTERS (plug-and-play, zie base.py).
"""
import argparse
import json
import os
import sys
from datetime import date

from ..database import SessionLocal
from ..models import Country
from .loader import store_motions
from .nl_tweede_kamer import TweedeKamerAdapter

ADAPTERS = {
    "nl": TweedeKamerAdapter,
    # "eu": EuropeesParlementAdapter,   # Fase 2 (brief §2)
    # "es": CongresoAdapter,            # Fase 2
    # "de": BundestagDipAdapter,        # Fase 2
}


def main():
    parser = argparse.ArgumentParser(description="PoliTrack data-ingestie")
    parser.add_argument("country", choices=sorted(ADAPTERS), help="landcode")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--since", type=date.fromisoformat, default=None)
    parser.add_argument("--fixture", action="store_true",
                        help="gebruik de meegeleverde voorbeelddata i.p.v. de live API")
    args = parser.parse_args()

    adapter = ADAPTERS[args.country]()
    db = SessionLocal()
    try:
        country = db.query(Country).filter(Country.code == args.country).first()
        if not country:
            print(f"Land '{args.country}' niet gevonden. Draai eerst import_data.py.")
            sys.exit(1)

        if args.fixture:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "fixtures", f"{args.country}_zaak_moties.json")
            print(f"Fixture laden: {path}")
            with open(path, encoding="utf-8") as f:
                motions = adapter.parse_motions(json.load(f))
        else:
            print(f"Ophalen: {adapter.legislature_name} (max {args.limit})...")
            motions = list(adapter.fetch_motions(limit=args.limit, since=args.since))
        print(f"Ontvangen: {len(motions)} moties")

        result = store_motions(db, country, motions)
        print(f"Opgeslagen: {result['created']} nieuw, {result['skipped']} bestond al, "
              f"{result['votes']} stemmen")
    finally:
        db.close()


if __name__ == "__main__":
    main()
