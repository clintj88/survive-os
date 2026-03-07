"""Tests for paper backup generation."""

from app.paper import generate_paper_backup, generate_qr_svg


def test_generate_paper_backup():
    sections = [
        {
            "heading": "Inventory Summary",
            "headers": ["Item", "Qty", "Location"],
            "rows": [
                ["Rice (50kg)", "12", "Warehouse A"],
                ["Diesel (L)", "500", "Fuel Depot"],
            ],
            "qr_data": '{"items": [{"name": "Rice", "qty": 12}]}',
        }
    ]
    html = generate_paper_backup("SURVIVE OS Backup — 2026-03-07", sections)
    assert "<!DOCTYPE html>" in html
    assert "Inventory Summary" in html
    assert "Rice (50kg)" in html
    assert "Warehouse A" in html


def test_generate_paper_no_qr():
    sections = [{"heading": "Test", "headers": ["A"], "rows": [["1"]]}]
    html = generate_paper_backup("Test", sections, include_qr=False)
    assert '<div class="qr-section">' not in html


def test_qr_svg_without_library():
    # Will use placeholder if qrcode not installed
    result = generate_qr_svg("test data")
    assert isinstance(result, str)
    assert len(result) > 0
