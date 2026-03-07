"""Seed data for the frequency database with common emergency/survival frequencies."""

from app.database import execute

SEED_FREQUENCIES = [
    # HF Emergency / Survival
    (3.860, "80m SSB Emergency Net", "80m", "SSB", "emergency", "ARES/RACES primary"),
    (5.3305, "60m Channel 1", "60m", "USB", "emergency", "FEMA interop channel"),
    (5.3465, "60m Channel 2", "60m", "USB", "emergency", "FEMA interop channel"),
    (5.3570, "60m Channel 3", "60m", "USB", "emergency", "FEMA interop primary"),
    (5.3715, "60m Channel 4", "60m", "USB", "emergency", "FEMA interop channel"),
    (5.4035, "60m Channel 5", "60m", "USB", "emergency", "FEMA interop channel"),
    (7.240, "40m SSB Emergency Net", "40m", "SSB", "emergency", "ARES/RACES primary"),
    (7.285, "40m Salvation Army (SATERN)", "40m", "SSB", "net", "SATERN net frequency"),
    (14.300, "20m Emergency Net", "20m", "SSB", "emergency", "International assistance"),
    (14.313, "20m Intercon Net", "20m", "SSB", "net", "Maritime/mobile net"),
    (21.360, "15m Emergency/Traffic", "15m", "SSB", "emergency", "Daytime long-haul"),
    (28.400, "10m SSB Calling", "10m", "SSB", "general", "10m SSB calling frequency"),

    # VHF/UHF Simplex
    (146.520, "2m National Simplex Calling", "2m", "FM", "simplex", "Primary 2m simplex"),
    (146.550, "2m Simplex", "2m", "FM", "simplex", "Secondary simplex"),
    (146.580, "2m Simplex", "2m", "FM", "simplex", "Alternate simplex"),
    (147.420, "2m Simplex", "2m", "FM", "simplex", "Alternate simplex"),
    (147.450, "2m Simplex", "2m", "FM", "simplex", "Alternate simplex"),
    (147.570, "2m ARES Simplex", "2m", "FM", "emergency", "ARES simplex coordination"),
    (223.500, "1.25m National Simplex", "1.25m", "FM", "simplex", "220 band calling"),
    (446.000, "70cm National Simplex Calling", "70cm", "FM", "simplex", "Primary 70cm simplex"),
    (446.500, "70cm Simplex", "70cm", "FM", "simplex", "Alternate 70cm simplex"),

    # Digital modes
    (7.078, "40m JS8Call", "40m", "JS8", "digital", "JS8Call default frequency"),
    (14.078, "20m JS8Call", "20m", "JS8", "digital", "JS8Call default frequency"),
    (7.070, "40m PSK31", "40m", "PSK31", "digital", "Digital mode calling"),
    (14.070, "20m PSK31", "20m", "PSK31", "digital", "Digital mode calling"),
    (3.583, "80m FT8/JS8", "80m", "FT8", "digital", "HF digital"),
    (14.074, "20m FT8", "20m", "FT8", "digital", "FT8 frequency"),

    # Winlink
    (3.596, "80m Winlink", "80m", "ARDOP", "winlink", "Winlink gateway frequency"),
    (7.101, "40m Winlink", "40m", "ARDOP", "winlink", "Winlink gateway frequency"),
    (10.145, "30m Winlink", "30m", "ARDOP", "winlink", "Winlink gateway frequency"),
    (14.096, "20m Winlink", "20m", "ARDOP", "winlink", "Winlink gateway frequency"),

    # Marine/Weather
    (2.182, "Marine Distress (MF)", "MF", "SSB", "emergency", "International distress"),
    (156.800, "Marine Ch 16 (VHF)", "VHF", "FM", "emergency", "Marine distress/calling"),
    (162.550, "NOAA Weather 1", "VHF", "FM", "weather", "WX broadcast"),
    (162.400, "NOAA Weather 2", "VHF", "FM", "weather", "WX broadcast"),
    (162.475, "NOAA Weather 3", "VHF", "FM", "weather", "WX broadcast"),

    # FRS/GMRS
    (462.5625, "FRS/GMRS Ch 1", "UHF", "FM", "frs", "Family Radio Service"),
    (462.5875, "FRS/GMRS Ch 2", "UHF", "FM", "frs", "Family Radio Service"),
    (462.6125, "FRS/GMRS Ch 3", "UHF", "FM", "frs", "Family Radio Service"),
    (462.6375, "FRS/GMRS Ch 4", "UHF", "FM", "frs", "Family Radio Service"),
    (462.6625, "FRS/GMRS Ch 5", "UHF", "FM", "frs", "Family Radio Service"),
    (462.6875, "FRS/GMRS Ch 6", "UHF", "FM", "frs", "Family Radio Service"),
    (462.7125, "FRS/GMRS Ch 7", "UHF", "FM", "frs", "Family Radio Service"),

    # MURS
    (151.820, "MURS Ch 1", "VHF", "FM", "murs", "Multi-Use Radio Service"),
    (151.880, "MURS Ch 2", "VHF", "FM", "murs", "Multi-Use Radio Service"),
    (151.940, "MURS Ch 3", "VHF", "FM", "murs", "Multi-Use Radio Service"),
    (154.570, "MURS Ch 4", "VHF", "FM", "murs", "Multi-Use Radio Service"),
    (154.600, "MURS Ch 5", "VHF", "FM", "murs", "Multi-Use Radio Service"),
]


def seed_frequencies() -> None:
    """Insert seed frequency data into the database."""
    for freq_mhz, name, band, mode, usage, notes in SEED_FREQUENCIES:
        execute(
            "INSERT INTO frequencies (freq_mhz, name, band, mode, usage, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (freq_mhz, name, band, mode, usage, notes),
        )
