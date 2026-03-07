"""Pediatric and adult dosing rules seed data."""

DOSING_RULES = [
    # Acetaminophen (Tylenol/Paracetamol)
    {
        "medication_name": "Acetaminophen",
        "indication": "Pain/Fever",
        "age_min_months": 0,
        "age_max_months": 2160,
        "dose_mg_per_kg": 15.0,
        "frequency_hours": 4,
        "max_single_dose_mg": 1000.0,
        "max_daily_dose_mg": 4000.0,
        "adult_dose_mg": 650.0,
        "notes": "Do not exceed 4g/day in adults. Reduce max to 2g/day in liver disease or regular alcohol use.",
    },
    # Ibuprofen
    {
        "medication_name": "Ibuprofen",
        "indication": "Pain/Fever/Inflammation",
        "age_min_months": 6,
        "age_max_months": 2160,
        "dose_mg_per_kg": 10.0,
        "frequency_hours": 6,
        "max_single_dose_mg": 800.0,
        "max_daily_dose_mg": 3200.0,
        "adult_dose_mg": 400.0,
        "notes": "Not for infants under 6 months. Take with food. Avoid in renal impairment, GI bleeding, or last trimester of pregnancy.",
    },
    # Amoxicillin - Standard dose
    {
        "medication_name": "Amoxicillin",
        "indication": "Bacterial infections (standard dose)",
        "age_min_months": 1,
        "age_max_months": 2160,
        "dose_mg_per_kg": 25.0,
        "frequency_hours": 8,
        "max_single_dose_mg": 500.0,
        "max_daily_dose_mg": 1500.0,
        "adult_dose_mg": 500.0,
        "notes": "Standard dose for mild-moderate infections. Double dose (high-dose) for otitis media or resistant organisms.",
    },
    # Amoxicillin - High dose
    {
        "medication_name": "Amoxicillin",
        "indication": "Bacterial infections (high dose - otitis media)",
        "age_min_months": 1,
        "age_max_months": 144,
        "dose_mg_per_kg": 45.0,
        "frequency_hours": 12,
        "max_single_dose_mg": 1000.0,
        "max_daily_dose_mg": 3000.0,
        "adult_dose_mg": 875.0,
        "notes": "High-dose for AOM, sinusitis, or areas with penicillin-resistant pneumococcus.",
    },
    # Azithromycin
    {
        "medication_name": "Azithromycin",
        "indication": "Bacterial infections",
        "age_min_months": 6,
        "age_max_months": 2160,
        "dose_mg_per_kg": 10.0,
        "frequency_hours": 24,
        "max_single_dose_mg": 500.0,
        "max_daily_dose_mg": 500.0,
        "adult_dose_mg": 500.0,
        "notes": "Day 1: 10mg/kg (max 500mg). Days 2-5: 5mg/kg (max 250mg). Z-pack: 500mg day 1, 250mg days 2-5.",
    },
    # Cefalexin
    {
        "medication_name": "Cefalexin",
        "indication": "Bacterial infections (skin, UTI, pharyngitis)",
        "age_min_months": 1,
        "age_max_months": 2160,
        "dose_mg_per_kg": 12.5,
        "frequency_hours": 6,
        "max_single_dose_mg": 500.0,
        "max_daily_dose_mg": 4000.0,
        "adult_dose_mg": 500.0,
        "notes": "First-generation cephalosporin. Cross-reactivity with penicillin allergy is low (~1%) but consider.",
    },
    # Metronidazole
    {
        "medication_name": "Metronidazole",
        "indication": "Anaerobic infections, parasitic infections",
        "age_min_months": 1,
        "age_max_months": 2160,
        "dose_mg_per_kg": 7.5,
        "frequency_hours": 8,
        "max_single_dose_mg": 500.0,
        "max_daily_dose_mg": 2000.0,
        "adult_dose_mg": 500.0,
        "notes": "Absolutely no alcohol during treatment and 48 hours after. Metallic taste is common.",
    },
    # Prednisolone (pediatric steroid)
    {
        "medication_name": "Prednisolone",
        "indication": "Asthma exacerbation, croup, allergic reactions",
        "age_min_months": 1,
        "age_max_months": 2160,
        "dose_mg_per_kg": 1.0,
        "frequency_hours": 24,
        "max_single_dose_mg": 60.0,
        "max_daily_dose_mg": 60.0,
        "adult_dose_mg": 40.0,
        "notes": "Short course (3-5 days) usually doesn't need taper. Give with food. For croup: single dose of 2mg/kg.",
    },
    # Diphenhydramine (Benadryl)
    {
        "medication_name": "Diphenhydramine",
        "indication": "Allergic reactions, urticaria, anaphylaxis adjunct",
        "age_min_months": 24,
        "age_max_months": 2160,
        "dose_mg_per_kg": 1.25,
        "frequency_hours": 6,
        "max_single_dose_mg": 50.0,
        "max_daily_dose_mg": 300.0,
        "adult_dose_mg": 50.0,
        "notes": "Not for children under 2. Causes significant sedation. For anaphylaxis: epinephrine is first-line, not antihistamines.",
    },
    # Ondansetron (Zofran)
    {
        "medication_name": "Ondansetron",
        "indication": "Nausea and vomiting",
        "age_min_months": 6,
        "age_max_months": 2160,
        "dose_mg_per_kg": 0.15,
        "frequency_hours": 8,
        "max_single_dose_mg": 4.0,
        "max_daily_dose_mg": 16.0,
        "adult_dose_mg": 4.0,
        "notes": "Can cause QT prolongation. Single dose often sufficient for gastroenteritis-related vomiting in children.",
    },
    # Oral Rehydration Salts
    {
        "medication_name": "ORS (Oral Rehydration Salts)",
        "indication": "Dehydration from diarrhea/vomiting",
        "age_min_months": 0,
        "age_max_months": 2160,
        "dose_mg_per_kg": 75.0,
        "frequency_hours": 4,
        "max_single_dose_mg": 0.0,
        "max_daily_dose_mg": 0.0,
        "adult_dose_mg": 0.0,
        "notes": "Dose is mL/kg, not mg/kg. 75 mL/kg over 4 hours for moderate dehydration. Sip frequently. WHO formula: 2.6g NaCl, 13.5g glucose, 2.9g trisodium citrate, 1.5g KCl per liter.",
    },
    # Albendazole
    {
        "medication_name": "Albendazole",
        "indication": "Intestinal parasites (roundworm, hookworm, pinworm)",
        "age_min_months": 12,
        "age_max_months": 2160,
        "dose_mg_per_kg": 0.0,
        "frequency_hours": 24,
        "max_single_dose_mg": 400.0,
        "max_daily_dose_mg": 400.0,
        "adult_dose_mg": 400.0,
        "notes": "Fixed dose: 400mg single dose for most intestinal parasites. Children 12-24 months: 200mg. Take with fatty food for better absorption.",
    },
    # Epinephrine
    {
        "medication_name": "Epinephrine",
        "indication": "Anaphylaxis (IM injection)",
        "age_min_months": 0,
        "age_max_months": 2160,
        "dose_mg_per_kg": 0.01,
        "frequency_hours": 0,
        "max_single_dose_mg": 0.5,
        "max_daily_dose_mg": 0.0,
        "adult_dose_mg": 0.3,
        "notes": "0.01 mg/kg of 1:1000 solution IM in lateral thigh. Max 0.3mg for children, 0.5mg for adults. May repeat every 5-15 minutes. EpiPen Jr: 0.15mg (<30kg), EpiPen: 0.3mg (>30kg).",
    },
]


def seed_dosing_rules(execute_fn, query_fn) -> None:
    """Seed the dosing rules table."""
    existing = query_fn("SELECT COUNT(*) as count FROM dosing_rules")
    if existing[0]["count"] > 0:
        return

    for rule in DOSING_RULES:
        execute_fn(
            """INSERT INTO dosing_rules
               (medication_name, indication, age_min_months, age_max_months,
                dose_mg_per_kg, frequency_hours, max_single_dose_mg,
                max_daily_dose_mg, adult_dose_mg, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (rule["medication_name"], rule["indication"],
             rule["age_min_months"], rule["age_max_months"],
             rule["dose_mg_per_kg"], rule["frequency_hours"],
             rule["max_single_dose_mg"], rule["max_daily_dose_mg"],
             rule["adult_dose_mg"], rule["notes"]),
        )
