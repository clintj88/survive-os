"""Paper backup generator.

Generates printable summaries of critical data with QR codes
for re-digitization. Outputs HTML suitable for printing or
PDF conversion.
"""

import base64
import json
from typing import Any

from shared.db.timestamps import utcnow

try:
    import qrcode
    import qrcode.image.svg
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False


def generate_qr_svg(data: str, box_size: int = 4) -> str:
    """Generate a QR code as inline SVG markup.

    Falls back to a placeholder if qrcode library is not installed.
    """
    if not HAS_QRCODE:
        return f'<div class="qr-placeholder">[QR: {data[:50]}...]</div>'
    qr = qrcode.QRCode(version=None, box_size=box_size, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    return img.to_string().decode("utf-8")


def _table_html(headers: list[str], rows: list[list[str]]) -> str:
    """Generate an HTML table."""
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = ""
    for row in rows:
        cells = "".join(f"<td>{c}</td>" for c in row)
        body += f"<tr>{cells}</tr>\n"
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def generate_paper_backup(
    title: str,
    sections: list[dict[str, Any]],
    include_qr: bool = True,
) -> str:
    """Generate a printable HTML paper backup.

    Args:
        title: Document title.
        sections: List of section dicts, each with:
            - "heading": Section heading
            - "headers": List of column headers
            - "rows": List of row data (list of lists)
            - "qr_data": Optional data to encode as QR code
        include_qr: Whether to include QR codes.

    Returns:
        Complete HTML document string.
    """
    generated = utcnow()
    sections_html = ""

    for section in sections:
        heading = section.get("heading", "")
        headers = section.get("headers", [])
        rows = section.get("rows", [])
        qr_data = section.get("qr_data", "")

        sections_html += f"<h2>{heading}</h2>\n"
        if headers and rows:
            sections_html += _table_html(headers, rows)

        if include_qr and qr_data:
            sections_html += '<div class="qr-section">\n'
            # QR codes have ~4296 byte limit; chunk if needed
            if len(qr_data) <= 2000:
                sections_html += generate_qr_svg(qr_data)
            else:
                chunks = [qr_data[i:i+2000] for i in range(0, len(qr_data), 2000)]
                for idx, chunk in enumerate(chunks):
                    sections_html += f"<p>QR {idx + 1}/{len(chunks)}</p>\n"
                    sections_html += generate_qr_svg(chunk)
            sections_html += "</div>\n"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{ font-family: 'Courier New', monospace; margin: 2cm; font-size: 10pt; }}
h1 {{ border-bottom: 2px solid #000; padding-bottom: 4px; }}
h2 {{ margin-top: 1.5em; border-bottom: 1px solid #666; }}
table {{ border-collapse: collapse; width: 100%; margin: 0.5em 0; }}
th, td {{ border: 1px solid #333; padding: 4px 8px; text-align: left; font-size: 9pt; }}
th {{ background: #eee; }}
.qr-section {{ margin: 1em 0; page-break-inside: avoid; }}
.qr-placeholder {{ border: 1px dashed #999; padding: 8px; font-style: italic; }}
.footer {{ margin-top: 2em; font-size: 8pt; color: #666; border-top: 1px solid #ccc; padding-top: 4px; }}
@media print {{
    body {{ margin: 1cm; }}
    .no-print {{ display: none; }}
}}
</style>
</head>
<body>
<h1>{title}</h1>
<p>Generated: {generated}</p>
{sections_html}
<div class="footer">
SURVIVE OS Paper Backup — generated {generated} — verify QR codes with any scanner
</div>
</body>
</html>"""
