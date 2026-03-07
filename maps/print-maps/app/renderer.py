"""Stub map renderer using Pillow to generate placeholder PNGs."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# Paper sizes in mm
PAPER_DIMENSIONS: dict[str, tuple[float, float]] = {
    "A4": (210, 297),
    "A3": (297, 420),
    "letter": (215.9, 279.4),
    "tabloid": (279.4, 431.8),
}


def _mm_to_px(mm: float, dpi: int) -> int:
    return int(mm / 25.4 * dpi)


def render_map(
    title: str,
    center_lat: float,
    center_lng: float,
    zoom: int,
    paper_size: str,
    paper_width_mm: float | None,
    paper_height_mm: float | None,
    orientation: str,
    dpi: int,
    overlay_layers: list[str],
    include_legend: bool,
    include_scale_bar: bool,
    include_north_arrow: bool,
    include_grid: bool,
    include_date: bool,
    output_dir: str,
    job_id: int,
) -> str:
    """Generate a placeholder PNG map image. Returns the output file path."""
    if paper_size == "custom" and paper_width_mm and paper_height_mm:
        w_mm, h_mm = paper_width_mm, paper_height_mm
    else:
        w_mm, h_mm = PAPER_DIMENSIONS.get(paper_size, PAPER_DIMENSIONS["A4"])

    if orientation == "landscape":
        w_mm, h_mm = h_mm, w_mm

    # Scale down for stub: use 1/4 DPI to keep files small
    stub_dpi = max(dpi // 4, 36)
    width = _mm_to_px(w_mm, stub_dpi)
    height = _mm_to_px(h_mm, stub_dpi)

    img = Image.new("RGB", (width, height), color=(240, 240, 230))
    draw = ImageDraw.Draw(img)

    # Border
    draw.rectangle([2, 2, width - 3, height - 3], outline=(100, 100, 100), width=2)

    # Title
    draw.text((10, 10), f"Map: {title}", fill=(30, 30, 30))
    draw.text((10, 30), f"Center: {center_lat:.4f}, {center_lng:.4f}", fill=(80, 80, 80))
    draw.text((10, 50), f"Zoom: {zoom} | {paper_size} {orientation} {dpi}dpi", fill=(80, 80, 80))

    y = 80
    if overlay_layers:
        draw.text((10, y), f"Layers: {', '.join(overlay_layers)}", fill=(80, 80, 80))
        y += 20

    elements = []
    if include_legend:
        elements.append("Legend")
    if include_scale_bar:
        elements.append("Scale Bar")
    if include_north_arrow:
        elements.append("North Arrow")
    if include_grid:
        elements.append("Grid")
    if include_date:
        elements.append("Date")
    if elements:
        draw.text((10, y), f"Elements: {', '.join(elements)}", fill=(80, 80, 80))
        y += 20

    # Crosshair at center
    cx, cy = width // 2, height // 2
    draw.line([(cx - 15, cy), (cx + 15, cy)], fill=(200, 50, 50), width=1)
    draw.line([(cx, cy - 15), (cx, cy + 15)], fill=(200, 50, 50), width=1)

    # Placeholder text
    draw.text(
        (cx - 60, cy + 20),
        "[STUB RENDER]",
        fill=(180, 180, 180),
    )

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    file_path = str(out_path / f"map_{job_id}.png")
    img.save(file_path, "PNG")
    return file_path
