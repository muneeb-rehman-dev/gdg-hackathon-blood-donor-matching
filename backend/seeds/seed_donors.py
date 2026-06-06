"""
Run from the backend/ directory AFTER generating the CSV:
    python data/generate_donors.py
    python seeds/seed_donors.py

Loads donors.csv into the SQLite database via SQLAlchemy (sync mode for seeding).
"""

import csv
import sys
from datetime import date
from pathlib import Path

# Allow running from backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os
os.environ.setdefault("ANTHROPIC_API_KEY", "placeholder-for-seed")

from app.config import settings
from app.database import Base
from app.models.donor import Donor  # noqa: F401
from app.models.blood_request import BloodRequest  # noqa: F401
from app.models.outreach_wave import OutreachWave  # noqa: F401
from app.models.donor_response import DonorResponse  # noqa: F401

# Use sync engine for the seed script
sync_url = settings.database_url.replace("sqlite+aiosqlite", "sqlite")
engine = create_engine(sync_url, echo=False)
Session = sessionmaker(engine)


def seed() -> None:
    # Create all tables
    Base.metadata.create_all(engine)

    csv_path = Path(__file__).parent.parent / "data" / "donors.csv"
    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found. Run data/generate_donors.py first.")
        sys.exit(1)

    with Session() as session:
        existing = session.query(Donor).count()
        if existing > 0:
            print(f"Database already has {existing} donors. Skipping seed.")
            return

        donors = []
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                last_donation = None
                if row.get("last_donation_date"):
                    try:
                        last_donation = date.fromisoformat(row["last_donation_date"])
                    except ValueError:
                        pass

                donors.append(
                    Donor(
                        id=row["id"],
                        name=row["name"],
                        phone=row["phone"],
                        blood_group=row["blood_group"],
                        area=row["area"],
                        lat=float(row["lat"]),
                        lng=float(row["lng"]),
                        last_donation_date=last_donation,
                        health_status=row["health_status"],
                        response_rate=float(row["response_rate"]),
                        total_donations=int(row["total_donations"]),
                    )
                )

        session.add_all(donors)
        session.commit()
        print(f"Seeded {len(donors)} donors into the database.")


if __name__ == "__main__":
    seed()
