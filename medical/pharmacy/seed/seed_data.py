"""Seed the pharmacy database with initial data."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import execute, init_db, query, set_db_path
from seed.dosing_rules import seed_dosing_rules
from seed.interactions import seed_interactions
from seed.natural_medicine import seed_natural_medicines


def main() -> None:
    set_db_path("/var/lib/survive/pharmacy/pharmacy.db")
    init_db()
    seed_interactions(execute, query)
    seed_natural_medicines(execute, query)
    seed_dosing_rules(execute, query)
    print("Pharmacy database seeded successfully.")


if __name__ == "__main__":
    main()
