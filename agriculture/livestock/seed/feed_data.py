"""Pre-seed feed requirement data for common livestock species."""

from app.database import execute, execute_many


def seed_feed_data() -> None:
    """Seed feed requirement reference data and common feed types."""
    # Feed types
    feed_types = [
        ("Hay (grass)", "kg", 1800, 8),
        ("Hay (alfalfa)", "kg", 2200, 18),
        ("Corn (grain)", "kg", 3400, 9),
        ("Oats", "kg", 2800, 12),
        ("Soybean meal", "kg", 3200, 44),
        ("Pasture (fresh)", "kg", 600, 15),
        ("Silage (corn)", "kg", 1400, 8),
        ("Layer feed", "kg", 2800, 16),
        ("Broiler feed", "kg", 3100, 22),
        ("Pig grower feed", "kg", 3200, 16),
        ("Mineral supplement", "kg", 0, 0),
    ]
    execute_many(
        "INSERT OR IGNORE INTO feed_types (name, unit, calories_per_unit, protein_pct) VALUES (?, ?, ?, ?)",
        [tuple(ft) for ft in feed_types],
    )

    # Feed requirements: (species, stage, min_wt, max_wt, dm_pct_bw, protein_pct, notes)
    requirements = [
        # Cattle
        ("cattle", "maintenance", 400, 700, 2.0, 7, "Mature cow at rest"),
        ("cattle", "growing", 100, 400, 2.8, 12, "Growing calves/yearlings"),
        ("cattle", "pregnant", 400, 700, 2.2, 9, "Last trimester increase"),
        ("cattle", "lactating", 400, 700, 3.0, 14, "Peak lactation needs"),
        # Goats
        ("goat", "maintenance", 30, 80, 3.0, 8, "Mature goat at rest"),
        ("goat", "growing", 5, 30, 4.0, 14, "Growing kids"),
        ("goat", "pregnant", 30, 80, 3.5, 10, "Late gestation"),
        ("goat", "lactating", 30, 80, 5.0, 14, "Dairy goats peak lactation"),
        # Sheep
        ("sheep", "maintenance", 40, 90, 2.5, 8, "Mature sheep at rest"),
        ("sheep", "growing", 10, 40, 3.5, 14, "Growing lambs"),
        ("sheep", "pregnant", 40, 90, 3.0, 10, "Late gestation ewes"),
        ("sheep", "lactating", 40, 90, 4.0, 14, "Lactating ewes"),
        # Chickens (values per bird, weight in kg)
        ("chicken", "maintenance", 1.5, 4, 3.5, 12, "Adult layer maintenance"),
        ("chicken", "growing", 0.1, 1.5, 6.0, 20, "Chick/pullet growth"),
        ("chicken", "lactating", 1.5, 4, 4.5, 16, "Active laying period (use 'lactating' stage)"),
        # Pigs
        ("pig", "maintenance", 100, 300, 2.5, 12, "Mature pig at rest"),
        ("pig", "growing", 10, 100, 4.0, 18, "Growing pigs to market weight"),
        ("pig", "pregnant", 100, 300, 2.5, 14, "Gestating sow"),
        ("pig", "lactating", 100, 300, 4.5, 18, "Lactating sow"),
    ]
    execute_many(
        """INSERT OR IGNORE INTO feed_requirements
           (species, production_stage, min_weight_kg, max_weight_kg,
            daily_dm_pct_bw, crude_protein_pct, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [tuple(r) for r in requirements],
    )


if __name__ == "__main__":
    from app.database import init_db, set_db_path
    set_db_path("/var/lib/survive/livestock/livestock.db")
    init_db()
    seed_feed_data()
    print("Feed data seeded successfully.")
