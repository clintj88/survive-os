# Medical Specialty Module - SURVIVE OS

Specialty medical care sub-modules: prenatal/childbirth, dental, mental health, and veterinary.

## Sub-modules

- **Prenatal**: Patient records, visit scheduling, growth tracking, delivery log, postpartum follow-ups
- **Dental**: Tooth chart (adult 32/pediatric 20), treatment history, emergency protocols, preventive care
- **Mental Health**: Privacy-first wellness check-ins, trend tracking, coping resources (no diagnosis codes, no forced reporting)
- **Veterinary**: Livestock health records, condition reference, treatment protocols, herd health reports

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8040
```

## Configuration

Copy `medical-specialty.yml` to `/etc/survive/medical-specialty.yml` and update the SQLCipher key.

## Testing

```bash
pip install pytest httpx
cd medical/specialty && python -m pytest tests/ -v
```

## Encryption

Production uses SQLCipher (pysqlcipher3) for encryption at rest. Development/testing falls back to standard sqlite3.

## Port

8040 (shared medical port)

## Privacy Policy (Mental Health)

- All mental health data is voluntary
- No mandatory reporting
- No diagnosis codes
- No involuntary holds
- No data sharing without explicit patient consent
- Patients can delete their own data at any time
