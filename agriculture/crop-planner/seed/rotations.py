"""Default rotation templates and crop seed data."""

from app.database import execute, execute_many


def seed_defaults() -> None:
    """Seed default crops and rotation templates."""
    # Seed crops with planting offsets relative to last spring frost
    crops = [
        # Legumes (nitrogen fixers)
        ("Peas", "Fabaceae", "legume", 60, -28, -14, None, 50, 80, "Cool season, direct sow"),
        ("Beans (Bush)", "Fabaceae", "legume", 55, None, 14, None, 55, 80, "After last frost"),
        ("Beans (Pole)", "Fabaceae", "legume", 65, None, 14, None, 60, 100, "Needs trellis"),
        ("Lentils", "Fabaceae", "legume", 80, None, -14, None, 70, 90, "Cool season crop"),
        # Leafy greens
        ("Lettuce", "Asteraceae", "leaf", 45, -42, -14, -7, 40, 65, "Succession plant"),
        ("Spinach", "Amaranthaceae", "leaf", 40, -42, -21, None, 35, 55, "Cool weather crop"),
        ("Kale", "Brassicaceae", "leaf", 55, -42, -14, -7, 50, 120, "Frost tolerant"),
        ("Swiss Chard", "Amaranthaceae", "leaf", 55, -28, -7, None, 50, 100, "Cut and come again"),
        ("Cabbage", "Brassicaceae", "leaf", 70, -42, None, -7, 65, 90, "Start indoors"),
        # Fruiting crops
        ("Tomato", "Solanaceae", "fruit", 75, -42, None, 14, 70, 120, "Needs warm soil"),
        ("Pepper", "Solanaceae", "fruit", 70, -56, None, 14, 65, 110, "Start early indoors"),
        ("Cucumber", "Cucurbitaceae", "fruit", 55, -21, 7, 14, 50, 90, "Warm season"),
        ("Squash (Summer)", "Cucurbitaceae", "fruit", 50, -21, 7, None, 45, 80, "Direct sow after frost"),
        ("Squash (Winter)", "Cucurbitaceae", "fruit", 100, -21, 7, None, 90, 110, "Needs long season"),
        ("Zucchini", "Cucurbitaceae", "fruit", 50, -21, 7, None, 45, 80, "Prolific producer"),
        # Root crops
        ("Carrot", "Apiaceae", "root", 70, None, -14, None, 60, 90, "Loose soil needed"),
        ("Beet", "Amaranthaceae", "root", 55, None, -14, None, 45, 70, "Direct sow"),
        ("Radish", "Brassicaceae", "root", 25, None, -21, None, 20, 30, "Fast growing"),
        ("Potato", "Solanaceae", "root", 90, None, -14, None, 70, 100, "Hill as they grow"),
        ("Onion", "Amaryllidaceae", "root", 100, -56, -14, -7, 90, 110, "Long season"),
        ("Garlic", "Amaryllidaceae", "root", 240, None, None, None, 200, 250, "Plant in fall"),
        # Herbs (general companions)
        ("Basil", "Lamiaceae", "fruit", 60, -28, 7, 14, 50, 100, "Companion to tomatoes"),
        ("Dill", "Apiaceae", "leaf", 40, None, -7, None, 35, 60, "Self-seeds readily"),
        ("Cilantro", "Apiaceae", "leaf", 45, None, -14, None, 40, 55, "Bolts in heat"),
    ]

    execute_many(
        """INSERT OR IGNORE INTO crops (name, family, rotation_group, days_to_maturity,
           sow_indoor_offset, sow_outdoor_offset, transplant_offset,
           harvest_start_offset, harvest_end_offset, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [tuple(c) for c in crops],
    )

    # Seed default rotation templates
    template_id = execute(
        "INSERT OR IGNORE INTO rotation_templates (name, climate_zone, description) VALUES (?, ?, ?)",
        ("Classic Four-Year", "temperate", "Traditional four-year rotation: legume, leaf, fruit, root"),
    )
    if template_id:
        execute_many(
            "INSERT INTO rotation_steps (template_id, year_offset, rotation_group, notes) VALUES (?, ?, ?, ?)",
            [
                (template_id, 0, "legume", "Fix nitrogen in soil"),
                (template_id, 1, "leaf", "Use nitrogen from legumes"),
                (template_id, 2, "fruit", "Heavy feeders benefit from built-up fertility"),
                (template_id, 3, "root", "Break up soil, lower nutrient demands"),
            ],
        )

    template_id = execute(
        "INSERT OR IGNORE INTO rotation_templates (name, climate_zone, description) VALUES (?, ?, ?)",
        ("Three-Year Simple", "temperate", "Simplified three-year: legume, brassica, root"),
    )
    if template_id:
        execute_many(
            "INSERT INTO rotation_steps (template_id, year_offset, rotation_group, notes) VALUES (?, ?, ?, ?)",
            [
                (template_id, 0, "legume", "Nitrogen fixation"),
                (template_id, 1, "leaf", "Brassicas and leafy greens"),
                (template_id, 2, "root", "Root crops and alliums"),
            ],
        )
