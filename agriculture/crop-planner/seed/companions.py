"""Companion planting seed data."""

from app.database import execute_many


def seed_companions() -> None:
    """Seed companion planting compatibility data."""
    # Format: (crop_a, crop_b, relationship, notes) - alphabetical order for a,b
    companions = [
        # Beneficial pairings
        ("Basil", "Tomato", "beneficial", "Basil repels aphids and improves tomato flavor"),
        ("Beans (Bush)", "Potato", "beneficial", "Beans fix nitrogen, potatoes repel bean beetles"),
        ("Beans (Pole)", "Carrot", "beneficial", "Complementary root depths"),
        ("Beet", "Lettuce", "beneficial", "Lettuce provides shade for beets"),
        ("Carrot", "Onion", "beneficial", "Onion deters carrot fly"),
        ("Carrot", "Tomato", "beneficial", "Tomatoes repel carrot fly"),
        ("Cucumber", "Dill", "beneficial", "Dill attracts beneficial insects"),
        ("Cucumber", "Peas", "beneficial", "Peas fix nitrogen for cucumbers"),
        ("Kale", "Onion", "beneficial", "Onion deters cabbage pests"),
        ("Lettuce", "Radish", "beneficial", "Radish marks rows, loosens soil"),
        ("Pepper", "Basil", "beneficial", "Basil improves pepper growth and flavor"),
        ("Pepper", "Carrot", "beneficial", "Good use of space, different root depths"),
        ("Spinach", "Peas", "beneficial", "Peas provide shade and nitrogen"),
        ("Squash (Summer)", "Beans (Bush)", "beneficial", "Three sisters planting"),
        ("Swiss Chard", "Beans (Bush)", "beneficial", "Complementary nutrient needs"),
        ("Tomato", "Carrot", "beneficial", "Tomatoes provide shade for carrots"),

        # Antagonistic pairings
        ("Beans (Bush)", "Onion", "antagonistic", "Onions inhibit bean growth"),
        ("Beans (Pole)", "Beet", "antagonistic", "Compete for nutrients"),
        ("Cabbage", "Tomato", "antagonistic", "Both heavy feeders, compete for nutrients"),
        ("Carrot", "Dill", "antagonistic", "Dill can cross-pollinate and stunt carrots"),
        ("Cucumber", "Potato", "antagonistic", "Potatoes inhibit cucumber growth"),
        ("Garlic", "Beans (Bush)", "antagonistic", "Alliums inhibit legume growth"),
        ("Garlic", "Peas", "antagonistic", "Alliums inhibit legume growth"),
        ("Onion", "Peas", "antagonistic", "Onions stunt pea growth"),
        ("Pepper", "Beans (Bush)", "antagonistic", "Can spread disease between them"),
        ("Potato", "Tomato", "antagonistic", "Same family, share diseases like blight"),
        ("Squash (Summer)", "Potato", "antagonistic", "Potatoes can inhibit squash"),

        # Neutral pairings
        ("Basil", "Lettuce", "neutral", "No significant interaction"),
        ("Beet", "Cabbage", "neutral", "Tolerate each other well"),
        ("Kale", "Peas", "neutral", "No significant interaction"),
    ]

    execute_many(
        "INSERT OR IGNORE INTO companions (crop_a, crop_b, relationship, notes) VALUES (?, ?, ?, ?)",
        [tuple(c) for c in companions],
    )
