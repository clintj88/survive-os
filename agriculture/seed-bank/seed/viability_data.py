"""Species-specific seed viability data.

Each entry contains:
- max_years: maximum viable storage life under ideal conditions
- half_life_years: years until germination rate drops to ~50%
- ideal_temp_c: ideal storage temperature in Celsius
- ideal_humidity_pct: ideal relative humidity percentage

These are approximate values for common crop species stored
under reasonable conditions (cool, dry, dark).
"""

VIABILITY_CURVES: dict[str, dict] = {
    "onion": {
        "max_years": 1,
        "half_life_years": 0.75,
        "ideal_temp_c": 5,
        "ideal_humidity_pct": 30,
    },
    "parsnip": {
        "max_years": 1,
        "half_life_years": 0.75,
        "ideal_temp_c": 5,
        "ideal_humidity_pct": 30,
    },
    "leek": {
        "max_years": 2,
        "half_life_years": 1.5,
        "ideal_temp_c": 5,
        "ideal_humidity_pct": 30,
    },
    "corn": {
        "max_years": 2,
        "half_life_years": 1.5,
        "ideal_temp_c": 10,
        "ideal_humidity_pct": 35,
    },
    "pepper": {
        "max_years": 2,
        "half_life_years": 1.5,
        "ideal_temp_c": 10,
        "ideal_humidity_pct": 35,
    },
    "bean": {
        "max_years": 3,
        "half_life_years": 2.0,
        "ideal_temp_c": 10,
        "ideal_humidity_pct": 35,
    },
    "pea": {
        "max_years": 3,
        "half_life_years": 2.0,
        "ideal_temp_c": 10,
        "ideal_humidity_pct": 35,
    },
    "carrot": {
        "max_years": 3,
        "half_life_years": 2.0,
        "ideal_temp_c": 5,
        "ideal_humidity_pct": 30,
    },
    "lettuce": {
        "max_years": 3,
        "half_life_years": 2.0,
        "ideal_temp_c": 5,
        "ideal_humidity_pct": 30,
    },
    "spinach": {
        "max_years": 3,
        "half_life_years": 2.0,
        "ideal_temp_c": 5,
        "ideal_humidity_pct": 30,
    },
    "beet": {
        "max_years": 4,
        "half_life_years": 3.0,
        "ideal_temp_c": 10,
        "ideal_humidity_pct": 35,
    },
    "squash": {
        "max_years": 4,
        "half_life_years": 3.0,
        "ideal_temp_c": 10,
        "ideal_humidity_pct": 35,
    },
    "cucumber": {
        "max_years": 5,
        "half_life_years": 3.5,
        "ideal_temp_c": 10,
        "ideal_humidity_pct": 35,
    },
    "melon": {
        "max_years": 5,
        "half_life_years": 3.5,
        "ideal_temp_c": 10,
        "ideal_humidity_pct": 35,
    },
    "radish": {
        "max_years": 5,
        "half_life_years": 3.5,
        "ideal_temp_c": 10,
        "ideal_humidity_pct": 35,
    },
    "cabbage": {
        "max_years": 4,
        "half_life_years": 3.0,
        "ideal_temp_c": 5,
        "ideal_humidity_pct": 30,
    },
    "broccoli": {
        "max_years": 4,
        "half_life_years": 3.0,
        "ideal_temp_c": 5,
        "ideal_humidity_pct": 30,
    },
    "tomato": {
        "max_years": 4,
        "half_life_years": 3.0,
        "ideal_temp_c": 10,
        "ideal_humidity_pct": 35,
    },
    "eggplant": {
        "max_years": 4,
        "half_life_years": 3.0,
        "ideal_temp_c": 10,
        "ideal_humidity_pct": 35,
    },
    "watermelon": {
        "max_years": 5,
        "half_life_years": 3.5,
        "ideal_temp_c": 10,
        "ideal_humidity_pct": 35,
    },
}


def get_viability_data(species: str) -> dict | None:
    """Look up viability data for a species (case-insensitive)."""
    return VIABILITY_CURVES.get(species.lower())


def list_known_species() -> list[str]:
    """Return all species with known viability data."""
    return sorted(VIABILITY_CURVES.keys())
