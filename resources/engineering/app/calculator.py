"""Construction Material Calculator API routes."""

import math

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/calculator", tags=["calculator"])


class LumberRequest(BaseModel):
    length_ft: float = 0
    width_in: float = 0
    thickness_in: float = 0
    wall_length_ft: float = 0
    spacing_in: float = 16


class ConcreteRequest(BaseModel):
    length_ft: float = 0
    width_ft: float = 0
    depth_in: float = 0
    diameter_in: float = 0
    height_ft: float = 0
    shape: str = "slab"


class RoofingRequest(BaseModel):
    length_ft: float
    width_ft: float
    pitch: float = 4.0


class FencingRequest(BaseModel):
    perimeter_ft: float
    post_spacing_ft: float = 8
    wire_strands: int = 3


class PaintRequest(BaseModel):
    walls: list[dict]
    coats: int = 2
    doors: int = 0
    windows: int = 0


@router.post("/lumber")
def calculate_lumber(req: LumberRequest) -> dict:
    results: dict = {}
    if req.length_ft and req.width_in and req.thickness_in:
        board_feet = (req.length_ft * req.width_in * req.thickness_in) / 12
        results["board_feet"] = round(board_feet, 2)
    if req.wall_length_ft:
        stud_count = math.ceil((req.wall_length_ft * 12) / req.spacing_in) + 1
        results["stud_count"] = stud_count
        results["wall_length_ft"] = req.wall_length_ft
        results["spacing_in"] = req.spacing_in
    return results


@router.post("/concrete")
def calculate_concrete(req: ConcreteRequest) -> dict:
    if req.shape == "column":
        radius_ft = (req.diameter_in / 2) / 12
        volume_cf = math.pi * radius_ft ** 2 * req.height_ft
    else:
        volume_cf = req.length_ft * req.width_ft * (req.depth_in / 12)

    cubic_yards = volume_cf / 27
    bags_60lb = math.ceil(volume_cf / 0.45)
    bags_80lb = math.ceil(volume_cf / 0.6)

    return {
        "volume_cubic_ft": round(volume_cf, 2),
        "volume_cubic_yards": round(cubic_yards, 2),
        "bags_60lb": bags_60lb,
        "bags_80lb": bags_80lb,
        "shape": req.shape,
    }


@router.post("/roofing")
def calculate_roofing(req: RoofingRequest) -> dict:
    pitch_factor = math.sqrt(1 + (req.pitch / 12) ** 2)
    area = req.length_ft * req.width_ft * pitch_factor
    squares = area / 100
    bundles = math.ceil(squares * 3)
    panel_area = 3 * 1.167  # 3ft x 14in standard metal panel
    panels = math.ceil(area / panel_area)

    return {
        "area_sq_ft": round(area, 2),
        "squares": round(squares, 2),
        "shingle_bundles": bundles,
        "metal_panels": panels,
        "pitch_factor": round(pitch_factor, 3),
    }


@router.post("/fencing")
def calculate_fencing(req: FencingRequest) -> dict:
    post_count = math.ceil(req.perimeter_ft / req.post_spacing_ft) + 1
    wire_length = req.perimeter_ft * req.wire_strands
    gate_suggestion = max(1, math.floor(req.perimeter_ft / 200))

    return {
        "post_count": post_count,
        "wire_length_ft": round(wire_length, 2),
        "gate_suggestion": gate_suggestion,
        "perimeter_ft": req.perimeter_ft,
    }


@router.post("/paint")
def calculate_paint(req: PaintRequest) -> dict:
    total_area = 0.0
    for wall in req.walls:
        total_area += wall.get("length", 0) * wall.get("height", 0)

    total_area -= req.doors * 20
    total_area -= req.windows * 15
    total_area = max(0, total_area)
    total_area *= req.coats

    gallons = math.ceil(total_area / 350)

    return {
        "wall_area_sq_ft": round(total_area / req.coats, 2) if req.coats else 0,
        "adjusted_area_sq_ft": round(total_area, 2),
        "coats": req.coats,
        "gallons_needed": gallons,
    }
