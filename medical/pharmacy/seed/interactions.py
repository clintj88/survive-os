"""Drug interaction seed data - 50+ common interaction pairs."""

INTERACTIONS = [
    # NSAIDs + Anticoagulants
    ("Warfarin", "Ibuprofen", "major", "Increased bleeding risk", "NSAIDs inhibit platelet function and may displace warfarin from protein binding", "Avoid combination; use acetaminophen for pain"),
    ("Warfarin", "Aspirin", "major", "Significantly increased bleeding risk", "Aspirin inhibits platelet aggregation and may increase warfarin effect", "Use only if specifically indicated; monitor INR closely"),
    ("Warfarin", "Naproxen", "major", "Increased bleeding risk", "NSAIDs inhibit platelet function", "Avoid combination; consider acetaminophen"),

    # Anticoagulant interactions
    ("Warfarin", "Metronidazole", "major", "Increased anticoagulant effect", "Metronidazole inhibits warfarin metabolism (CYP2C9)", "Monitor INR; reduce warfarin dose"),
    ("Warfarin", "Fluconazole", "major", "Greatly increased anticoagulant effect", "Fluconazole inhibits CYP2C9 and CYP3A4", "Reduce warfarin dose by 50%; monitor INR frequently"),
    ("Warfarin", "Amiodarone", "major", "Increased anticoagulant effect", "Amiodarone inhibits warfarin metabolism", "Reduce warfarin dose by 30-50%; monitor INR"),
    ("Warfarin", "Sulfamethoxazole", "major", "Increased bleeding risk", "Sulfamethoxazole inhibits CYP2C9", "Monitor INR closely; consider dose reduction"),

    # NSAID + NSAID / GI risk
    ("Ibuprofen", "Aspirin", "moderate", "Reduced cardioprotective effect of aspirin; increased GI bleeding", "Ibuprofen competes for COX-1 binding site", "Take aspirin 30 min before ibuprofen if both needed"),
    ("Ibuprofen", "Naproxen", "moderate", "Increased GI bleeding and renal toxicity risk", "Additive COX inhibition", "Do not combine NSAIDs; choose one"),
    ("Aspirin", "Naproxen", "moderate", "Increased GI bleeding risk", "Additive COX inhibition", "Avoid combination if possible"),

    # NSAIDs + other
    ("Ibuprofen", "Lisinopril", "moderate", "Reduced antihypertensive effect; increased renal risk", "NSAIDs reduce renal prostaglandin synthesis", "Monitor blood pressure and renal function"),
    ("Ibuprofen", "Methotrexate", "major", "Increased methotrexate toxicity", "NSAIDs reduce renal clearance of methotrexate", "Avoid with high-dose methotrexate"),
    ("Ibuprofen", "Lithium", "moderate", "Increased lithium levels", "NSAIDs reduce renal lithium clearance", "Monitor lithium levels; consider dose reduction"),

    # ACE Inhibitors
    ("Lisinopril", "Potassium chloride", "moderate", "Risk of hyperkalemia", "ACE inhibitors reduce aldosterone, retaining potassium", "Monitor potassium levels"),
    ("Lisinopril", "Spironolactone", "major", "Significant hyperkalemia risk", "Both retain potassium", "Monitor potassium closely if combination necessary"),

    # Antibiotics
    ("Amoxicillin", "Methotrexate", "major", "Increased methotrexate toxicity", "Amoxicillin reduces renal clearance of methotrexate", "Monitor methotrexate levels"),
    ("Ciprofloxacin", "Theophylline", "major", "Increased theophylline toxicity (seizures, arrhythmias)", "Ciprofloxacin inhibits CYP1A2", "Reduce theophylline dose; monitor levels"),
    ("Ciprofloxacin", "Warfarin", "major", "Increased bleeding risk", "Ciprofloxacin inhibits warfarin metabolism", "Monitor INR closely"),
    ("Ciprofloxacin", "Antacids", "moderate", "Reduced ciprofloxacin absorption", "Metal cations chelate fluoroquinolones", "Take ciprofloxacin 2 hours before antacids"),
    ("Metronidazole", "Alcohol", "contraindicated", "Disulfiram-like reaction (nausea, vomiting, flushing)", "Metronidazole inhibits aldehyde dehydrogenase", "Avoid alcohol during and 48 hours after treatment"),
    ("Tetracycline", "Antacids", "moderate", "Reduced tetracycline absorption", "Metal cations chelate tetracyclines", "Separate doses by 2-3 hours"),
    ("Tetracycline", "Iron", "moderate", "Reduced absorption of both drugs", "Chelation complex formation", "Separate doses by 2-3 hours"),
    ("Erythromycin", "Simvastatin", "contraindicated", "Risk of rhabdomyolysis", "Erythromycin inhibits CYP3A4, increasing statin levels", "Use alternative antibiotic or statin"),
    ("Erythromycin", "Carbamazepine", "major", "Increased carbamazepine toxicity", "Erythromycin inhibits CYP3A4", "Monitor carbamazepine levels; consider azithromycin"),
    ("Doxycycline", "Antacids", "moderate", "Reduced doxycycline absorption", "Chelation with metal cations", "Separate by 2-3 hours"),

    # Cardiac medications
    ("Digoxin", "Amiodarone", "major", "Increased digoxin toxicity", "Amiodarone reduces renal and non-renal clearance of digoxin", "Reduce digoxin dose by 50%"),
    ("Digoxin", "Verapamil", "major", "Increased digoxin levels", "Verapamil reduces digoxin clearance", "Reduce digoxin dose; monitor levels"),
    ("Digoxin", "Furosemide", "moderate", "Increased digoxin toxicity risk", "Furosemide-induced hypokalemia increases sensitivity to digoxin", "Monitor potassium; supplement if needed"),
    ("Amiodarone", "Simvastatin", "contraindicated", "Risk of rhabdomyolysis", "Amiodarone inhibits CYP3A4", "Max simvastatin 20mg/day; consider alternative statin"),
    ("Atenolol", "Verapamil", "major", "Excessive bradycardia and heart block", "Additive negative chronotropic and dromotropic effects", "Avoid combination; monitor closely if necessary"),
    ("Metoprolol", "Verapamil", "major", "Risk of severe bradycardia and heart failure", "Additive cardiac depression", "Avoid combination"),

    # Diabetes medications
    ("Metformin", "Alcohol", "moderate", "Increased risk of lactic acidosis", "Alcohol potentiates metformin effect on lactate metabolism", "Limit alcohol intake"),
    ("Glipizide", "Fluconazole", "major", "Severe hypoglycemia risk", "Fluconazole inhibits CYP2C9, increasing glipizide levels", "Monitor blood glucose; reduce glipizide dose"),
    ("Insulin", "Beta-blockers", "moderate", "Masked hypoglycemia symptoms", "Beta-blockers blunt tachycardia response to hypoglycemia", "Monitor blood glucose more frequently"),

    # Psychiatric medications
    ("Fluoxetine", "Tramadol", "contraindicated", "Serotonin syndrome risk; reduced tramadol efficacy", "Both increase serotonin; fluoxetine inhibits CYP2D6", "Avoid combination"),
    ("Fluoxetine", "MAOIs", "contraindicated", "Life-threatening serotonin syndrome", "Excessive serotonergic activity", "14-day washout between drugs"),
    ("Sertraline", "Tramadol", "major", "Serotonin syndrome risk", "Additive serotonergic effects", "Avoid if possible; monitor for symptoms"),
    ("Sertraline", "Warfarin", "moderate", "Increased bleeding risk", "SSRIs impair platelet function; possible CYP interaction", "Monitor INR; watch for bleeding"),
    ("Lithium", "Furosemide", "major", "Increased lithium toxicity", "Furosemide reduces renal lithium clearance via sodium depletion", "Monitor lithium levels; consider alternative diuretic"),
    ("Lithium", "ACE inhibitors", "major", "Increased lithium levels", "ACE inhibitors reduce renal lithium excretion", "Monitor lithium levels closely"),
    ("Carbamazepine", "Oral contraceptives", "major", "Reduced contraceptive efficacy", "Carbamazepine induces CYP3A4", "Use additional contraceptive method"),
    ("Phenytoin", "Warfarin", "major", "Altered warfarin effect (variable)", "Complex CYP interaction; initially increases then decreases warfarin effect", "Monitor INR frequently"),

    # Pain medications
    ("Tramadol", "MAOIs", "contraindicated", "Seizures and serotonin syndrome", "Additive serotonergic and noradrenergic effects", "Avoid combination; 14-day washout"),
    ("Morphine", "Benzodiazepines", "contraindicated", "Respiratory depression and death", "Additive CNS depression", "Avoid combination; if necessary, use lowest effective doses"),
    ("Codeine", "Fluoxetine", "major", "Reduced codeine efficacy", "Fluoxetine inhibits CYP2D6, blocking conversion to morphine", "Consider alternative analgesic"),
    ("Acetaminophen", "Warfarin", "moderate", "Increased INR with regular use", "Acetaminophen metabolite may inhibit vitamin K cycle", "Monitor INR if using >2g/day for multiple days"),
    ("Acetaminophen", "Alcohol", "major", "Increased hepatotoxicity risk", "Alcohol induces CYP2E1, increasing toxic metabolite formation", "Limit acetaminophen to 2g/day in regular drinkers"),

    # Miscellaneous important interactions
    ("Methotrexate", "Trimethoprim", "contraindicated", "Pancytopenia risk", "Both are folate antagonists", "Avoid combination"),
    ("Theophylline", "Cimetidine", "major", "Increased theophylline toxicity", "Cimetidine inhibits CYP1A2 and CYP3A4", "Use ranitidine or famotidine instead"),
    ("Sildenafil", "Nitrates", "contraindicated", "Severe hypotension", "Additive vasodilation via nitric oxide/cGMP pathway", "Absolutely contraindicated; 24-hour separation minimum"),
    ("Potassium chloride", "Spironolactone", "major", "Life-threatening hyperkalemia", "Both increase serum potassium", "Avoid combination; monitor potassium if necessary"),
    ("Prednisone", "NSAIDs", "moderate", "Increased GI bleeding risk", "Additive GI mucosal damage", "Use gastroprotection if combination necessary"),
    ("Isoniazid", "Acetaminophen", "moderate", "Increased hepatotoxicity risk", "Isoniazid induces CYP2E1", "Monitor liver function; limit acetaminophen dose"),
]


def seed_interactions(execute_fn, query_fn) -> None:
    """Seed the drug interactions table."""
    existing = query_fn("SELECT COUNT(*) as count FROM drug_interactions")
    if existing[0]["count"] > 0:
        return

    for drug_a, drug_b, severity, desc, mechanism, recommendation in INTERACTIONS:
        execute_fn(
            """INSERT INTO drug_interactions
               (drug_a, drug_b, severity, description, mechanism, recommendation)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (drug_a, drug_b, severity, desc, mechanism, recommendation),
        )
