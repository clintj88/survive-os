"""Barcode/QR code support for inventory items."""

import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .database import query

router = APIRouter(prefix="/api/scanning", tags=["scanning"])


def _generate_qr_png(data: str) -> bytes:
    import qrcode

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


@router.get("/qr/{item_id}")
def generate_qr(item_id: int) -> StreamingResponse:
    results = query("SELECT id, name, qr_code FROM items WHERE id = ?", (item_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Item not found")

    item = results[0]
    qr_data = item["qr_code"] or f"INV-ITEM-{item_id}"
    png_bytes = _generate_qr_png(qr_data)

    return StreamingResponse(
        io.BytesIO(png_bytes),
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename=item-{item_id}-qr.png"},
    )


@router.get("/lookup")
def lookup_by_code(code: str) -> dict:
    results = query(
        """SELECT i.*, l.name as location_name
           FROM items i LEFT JOIN locations l ON i.location_id = l.id
           WHERE i.qr_code = ?""",
        (code,),
    )
    if not results:
        raise HTTPException(status_code=404, detail="No item found for this code")
    return results[0]
