"""Seed data for the clinical concept dictionary."""

from app.database import execute, query


def _insert_concept(name: str, short_name: str, datatype: str, concept_class: str,
                    description: str = "", units: str = "") -> int:
    return execute(
        """INSERT INTO concepts (name, short_name, datatype, concept_class, description, units)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, short_name, datatype, concept_class, description, units),
    )


def _insert_mapping(concept_id: int, source: str, code: str, name: str = "") -> int:
    return execute(
        "INSERT INTO concept_mappings (concept_id, source, code, name) VALUES (?, ?, ?, ?)",
        (concept_id, source, code, name),
    )


def _insert_answer(concept_id: int, answer_concept_id: int, sort_order: int = 0) -> int:
    return execute(
        "INSERT INTO concept_answers (concept_id, answer_concept_id, sort_order) VALUES (?, ?, ?)",
        (concept_id, answer_concept_id, sort_order),
    )


def seed_all() -> None:
    """Seed all clinical concepts."""
    # --- Vital Signs ---
    vitals = {
        "Temperature": ("Temp", "numeric", "finding", "Body temperature", "C"),
        "Heart Rate": ("HR", "numeric", "finding", "Pulse rate", "bpm"),
        "Systolic BP": ("SBP", "numeric", "finding", "Systolic blood pressure", "mmHg"),
        "Diastolic BP": ("DBP", "numeric", "finding", "Diastolic blood pressure", "mmHg"),
        "Respiratory Rate": ("RR", "numeric", "finding", "Breaths per minute", "breaths/min"),
        "SpO2": ("SpO2", "numeric", "finding", "Oxygen saturation", "%"),
        "Weight": ("Wt", "numeric", "finding", "Body weight", "kg"),
        "Height": ("Ht", "numeric", "finding", "Body height", "cm"),
        "BMI": ("BMI", "numeric", "finding", "Body mass index", "kg/m2"),
    }
    vital_ids = {}
    for name, (short, dt, cls, desc, unit) in vitals.items():
        vital_ids[name] = _insert_concept(name, short, dt, cls, desc, unit)

    # --- Common Diagnoses ---
    diagnoses = {
        "Hypertension": ("HTN", "Essential hypertension", "I10"),
        "Diabetes Type 2": ("DM2", "Type 2 diabetes mellitus", "E11"),
        "Pneumonia": ("PNA", "Pneumonia, unspecified", "J18.9"),
        "Malaria": ("Mal", "Malaria, unspecified", "B54"),
        "Tuberculosis": ("TB", "Respiratory tuberculosis", "A15"),
        "HIV": ("HIV", "HIV disease", "B20"),
        "Fracture": ("Fx", "Fracture, unspecified", "T14.8"),
        "Laceration": ("Lac", "Laceration, unspecified", "T14.1"),
        "Dehydration": ("Dehyd", "Dehydration", "E86.0"),
        "Anemia": ("Ane", "Anemia, unspecified", "D64.9"),
    }
    for name, (short, desc, icd10) in diagnoses.items():
        cid = _insert_concept(name, short, "text", "diagnosis", desc)
        _insert_mapping(cid, "icd10", icd10, name)

    # --- Lab Tests ---
    labs = {
        "Blood Glucose": ("Gluc", "Blood glucose level", "mg/dL"),
        "Hemoglobin": ("Hgb", "Hemoglobin concentration", "g/dL"),
        "WBC Count": ("WBC", "White blood cell count", "cells/uL"),
        "RBC Count": ("RBC", "Red blood cell count", "M/uL"),
        "Platelet Count": ("Plt", "Platelet count", "K/uL"),
        "Creatinine": ("Cr", "Serum creatinine", "mg/dL"),
        "BUN": ("BUN", "Blood urea nitrogen", "mg/dL"),
        "Sodium": ("Na", "Serum sodium", "mEq/L"),
        "Potassium": ("K", "Serum potassium", "mEq/L"),
        "Urinalysis": ("UA", "Urinalysis", ""),
    }
    for name, (short, desc, unit) in labs.items():
        _insert_concept(name, short, "numeric", "test", desc, unit)

    # --- Drug Categories ---
    drugs = [
        ("Antibiotic", "Abx", "Anti-infective medication"),
        ("Analgesic", "Analg", "Pain relief medication"),
        ("Antipyretic", "Antipyr", "Fever-reducing medication"),
        ("Antihypertensive", "AntiHTN", "Blood pressure lowering medication"),
        ("Antidiabetic", "AntiDM", "Blood sugar lowering medication"),
        ("Antiretroviral", "ARV", "HIV treatment medication"),
    ]
    for name, short, desc in drugs:
        _insert_concept(name, short, "text", "drug", desc)

    # --- Blood Type (coded concept with answers) ---
    bt_id = _insert_concept("Blood Type", "BT", "coded", "finding", "ABO blood group and Rh factor")
    blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    for i, bt in enumerate(blood_types):
        ans_id = _insert_concept(bt, bt, "text", "misc", f"Blood type {bt}")
        _insert_answer(bt_id, ans_id, i)

    # --- Vital Signs Concept Set ---
    set_id = execute(
        "INSERT INTO concept_sets (name, description) VALUES (?, ?)",
        ("Vital Signs", "Standard vital sign measurements"),
    )
    for i, (name, vid) in enumerate(vital_ids.items()):
        execute(
            "INSERT INTO concept_set_members (set_id, concept_id, sort_order) VALUES (?, ?, ?)",
            (set_id, vid, i),
        )
