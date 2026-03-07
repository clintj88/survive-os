"""Default exchange rates for the trade/barter system.

Base unit: labor hours. All rates are expressed as
"1 unit of commodity = X labor hours".
"""

from app.database import execute


DEFAULT_RATES = [
    ("labor_hours", "labor_hours", 1.0, "system"),
    ("kg_wheat", "labor_hours", 0.5, "system"),
    ("kg_corn", "labor_hours", 0.4, "system"),
    ("kg_rice", "labor_hours", 0.6, "system"),
    ("kg_potatoes", "labor_hours", 0.3, "system"),
    ("kg_dried_beans", "labor_hours", 0.7, "system"),
    ("kg_vegetables", "labor_hours", 0.5, "system"),
    ("kg_fruit", "labor_hours", 0.6, "system"),
    ("kg_meat", "labor_hours", 2.0, "system"),
    ("kg_fish", "labor_hours", 1.5, "system"),
    ("dozen_eggs", "labor_hours", 1.0, "system"),
    ("liter_milk", "labor_hours", 0.8, "system"),
    ("liter_fuel", "labor_hours", 3.0, "system"),
    ("liter_water_purified", "labor_hours", 0.2, "system"),
    ("kg_firewood", "labor_hours", 0.3, "system"),
    ("kg_salt", "labor_hours", 1.0, "system"),
    ("kg_sugar", "labor_hours", 1.2, "system"),
    ("box_ammo_50", "labor_hours", 5.0, "system"),
    ("meter_rope", "labor_hours", 0.2, "system"),
    ("meter_fabric", "labor_hours", 0.8, "system"),
    ("kg_nails", "labor_hours", 1.5, "system"),
    ("medical_bandage", "labor_hours", 0.5, "system"),
    ("bottle_antibiotics", "labor_hours", 10.0, "system"),
    ("battery_aa", "labor_hours", 0.3, "system"),
    ("candle", "labor_hours", 0.2, "system"),
]


def seed_rates() -> None:
    """Insert default exchange rates into the database."""
    for commodity_a, commodity_b, rate, set_by in DEFAULT_RATES:
        execute(
            """INSERT INTO exchange_rates (commodity_a, commodity_b, rate, set_by)
               VALUES (?, ?, ?, ?)""",
            (commodity_a, commodity_b, rate, set_by),
        )
