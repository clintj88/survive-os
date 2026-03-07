"""Seed data: common lab tests and panels."""

from app.database import execute, query

TESTS = [
    # CBC panel tests
    {"name": "WBC", "specimen_type": "blood", "ref_range_min": 4.5, "ref_range_max": 11.0,
     "critical_low": 2.0, "critical_high": 30.0, "units": "x10^9/L",
     "description": "White Blood Cell Count", "turnaround_hours": 4},
    {"name": "RBC", "specimen_type": "blood", "ref_range_min": 4.7, "ref_range_max": 6.1,
     "critical_low": 2.0, "critical_high": 8.0, "units": "x10^12/L",
     "description": "Red Blood Cell Count", "turnaround_hours": 4},
    {"name": "Hemoglobin", "specimen_type": "blood", "ref_range_min": 12.0, "ref_range_max": 17.0,
     "critical_low": 7.0, "critical_high": 20.0, "units": "g/dL",
     "description": "Hemoglobin", "turnaround_hours": 4},
    {"name": "Hematocrit", "specimen_type": "blood", "ref_range_min": 36.0, "ref_range_max": 54.0,
     "critical_low": 20.0, "critical_high": 60.0, "units": "%",
     "description": "Hematocrit", "turnaround_hours": 4},
    {"name": "Platelet Count", "specimen_type": "blood", "ref_range_min": 150.0, "ref_range_max": 400.0,
     "critical_low": 50.0, "critical_high": 1000.0, "units": "x10^9/L",
     "description": "Platelet Count", "turnaround_hours": 4},
    # BMP panel tests
    {"name": "Glucose", "specimen_type": "blood", "ref_range_min": 70.0, "ref_range_max": 100.0,
     "critical_low": 40.0, "critical_high": 500.0, "units": "mg/dL",
     "description": "Fasting Blood Glucose", "turnaround_hours": 2},
    {"name": "BUN", "specimen_type": "blood", "ref_range_min": 7.0, "ref_range_max": 20.0,
     "critical_low": None, "critical_high": 100.0, "units": "mg/dL",
     "description": "Blood Urea Nitrogen", "turnaround_hours": 2},
    {"name": "Creatinine", "specimen_type": "blood", "ref_range_min": 0.7, "ref_range_max": 1.3,
     "critical_low": None, "critical_high": 10.0, "units": "mg/dL",
     "description": "Serum Creatinine", "turnaround_hours": 2},
    {"name": "Sodium", "specimen_type": "blood", "ref_range_min": 136.0, "ref_range_max": 145.0,
     "critical_low": 120.0, "critical_high": 160.0, "units": "mEq/L",
     "description": "Serum Sodium", "turnaround_hours": 2},
    {"name": "Potassium", "specimen_type": "blood", "ref_range_min": 3.5, "ref_range_max": 5.0,
     "critical_low": 2.5, "critical_high": 6.5, "units": "mEq/L",
     "description": "Serum Potassium", "turnaround_hours": 2},
    {"name": "Chloride", "specimen_type": "blood", "ref_range_min": 98.0, "ref_range_max": 106.0,
     "critical_low": 80.0, "critical_high": 120.0, "units": "mEq/L",
     "description": "Serum Chloride", "turnaround_hours": 2},
    {"name": "CO2", "specimen_type": "blood", "ref_range_min": 23.0, "ref_range_max": 29.0,
     "critical_low": 10.0, "critical_high": 40.0, "units": "mEq/L",
     "description": "Carbon Dioxide / Bicarbonate", "turnaround_hours": 2},
    # Individual tests
    {"name": "Urinalysis", "specimen_type": "urine", "ref_range_min": None, "ref_range_max": None,
     "critical_low": None, "critical_high": None, "units": "",
     "description": "Complete Urinalysis", "turnaround_hours": 4},
    {"name": "HbA1c", "specimen_type": "blood", "ref_range_min": 4.0, "ref_range_max": 5.6,
     "critical_low": None, "critical_high": 14.0, "units": "%",
     "description": "Hemoglobin A1c (Glycated)", "turnaround_hours": 24},
    {"name": "Total Cholesterol", "specimen_type": "blood", "ref_range_min": None, "ref_range_max": 200.0,
     "critical_low": None, "critical_high": 400.0, "units": "mg/dL",
     "description": "Total Cholesterol", "turnaround_hours": 24},
    {"name": "TSH", "specimen_type": "blood", "ref_range_min": 0.4, "ref_range_max": 4.0,
     "critical_low": 0.1, "critical_high": 20.0, "units": "mIU/L",
     "description": "Thyroid Stimulating Hormone", "turnaround_hours": 24},
    {"name": "Malaria Rapid Test", "specimen_type": "blood", "ref_range_min": None, "ref_range_max": None,
     "critical_low": None, "critical_high": None, "units": "",
     "description": "Rapid Diagnostic Test for Malaria", "turnaround_hours": 1},
    {"name": "HIV Rapid Test", "specimen_type": "blood", "ref_range_min": None, "ref_range_max": None,
     "critical_low": None, "critical_high": None, "units": "",
     "description": "Rapid HIV Antibody Test", "turnaround_hours": 1},
]

PANELS = [
    {"name": "CBC", "description": "Complete Blood Count",
     "tests": ["WBC", "RBC", "Hemoglobin", "Hematocrit", "Platelet Count"]},
    {"name": "BMP", "description": "Basic Metabolic Panel",
     "tests": ["Glucose", "BUN", "Creatinine", "Sodium", "Potassium", "Chloride", "CO2"]},
]


def seed() -> None:
    """Seed common lab tests and panels if the catalog is empty."""
    existing = query("SELECT COUNT(*) AS cnt FROM test_catalog")
    if existing[0]["cnt"] > 0:
        return

    for t in TESTS:
        execute(
            """INSERT INTO test_catalog
               (name, specimen_type, ref_range_min, ref_range_max,
                critical_low, critical_high, units, description, turnaround_hours)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (t["name"], t["specimen_type"], t["ref_range_min"], t["ref_range_max"],
             t["critical_low"], t["critical_high"], t["units"],
             t["description"], t["turnaround_hours"]),
        )

    for p in PANELS:
        panel_id = execute(
            "INSERT INTO lab_panels (name, description) VALUES (?, ?)",
            (p["name"], p["description"]),
        )
        for i, test_name in enumerate(p["tests"]):
            test_rows = query("SELECT id FROM test_catalog WHERE name = ?", (test_name,))
            if test_rows:
                execute(
                    "INSERT INTO panel_tests (panel_id, test_id, sort_order) VALUES (?, ?, ?)",
                    (panel_id, test_rows[0]["id"], i),
                )
