"""
Takeoff.ai - Structural Calculator

Estimates structural material quantities from blueprint-derived measurements.
All outputs are inference-based using standard residential construction ratios.
Target accuracy: ±15% for typical single-family residential.

Phase 1 scope: Framing lumber only.
Phase 2+ will add foundation, roofing, MEP.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


M_TO_FT = 3.28084
FT_TO_M = 1 / M_TO_FT


@dataclass
class MaterialQuantity:
    """A single structural material quantity in both unit systems."""
    name: str
    quantity_metric: float
    unit_metric: str
    quantity_imperial: float
    unit_imperial: str
    category: str = "structural"
    confidence: str = "estimated"
    note: str = "Based on standard residential construction ratios"

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "quantity_metric": round(self.quantity_metric, 2),
            "unit_metric": self.unit_metric,
            "quantity_imperial": round(self.quantity_imperial, 2),
            "unit_imperial": self.unit_imperial,
            "category": self.category,
            "confidence": self.confidence,
            "note": self.note,
        }


class StructuralCalculator:
    """
    Estimates structural material quantities for residential construction.

    All calculations use standard residential ratios and are labeled as
    estimated. No actual blueprint structural drawings are parsed in Phase 1.

    Args:
        ceiling_height: Floor-to-ceiling height in metres (default 2.7 m / ~9 ft)
        stories: Number of above-grade stories (default 1)
        wall_thickness: Framing wall thickness in metres (default 0.14 m / ~5.5 in)
    """

    STUD_SPACING_FT = 16 / 12  # 16" OC → ~1.333 ft per stud bay
    STUDS_PER_FT = 1 / STUD_SPACING_FT  # ~0.75 studs per linear ft of wall
    INTERIOR_PARTITION_RATIO = 0.40  # interior studs ≈ 40% of exterior studs
    PLATE_LAYERS = 3  # double top plate + single bottom plate
    BOARD_LENGTH_FT = 8  # standard stud board length in feet
    HEADER_RATIO = 0.10  # header stock ≈ 10% of perimeter in LF

    def __init__(
        self,
        ceiling_height: float = 2.7,
        stories: int = 1,
        wall_thickness: float = 0.14,
    ):
        self.ceiling_height = ceiling_height  # metres
        self.stories = stories
        self.wall_thickness = wall_thickness  # metres

    # ------------------------------------------------------------------
    # Framing
    # ------------------------------------------------------------------

    def calculate_framing(
        self,
        perimeter_m: float,
        floor_area_m2: float,
    ) -> Dict[str, Dict]:
        """
        Calculate framing lumber quantities for exterior and interior walls.

        Args:
            perimeter_m: Exterior wall perimeter in metres
            floor_area_m2: Total floor area in square metres

        Returns:
            Dict mapping material key → MaterialQuantity.to_dict()
            Keys: exterior_studs, interior_partition_studs,
                  top_bottom_plates_boards, header_stock_lf
        """
        perimeter_ft = perimeter_m * M_TO_FT
        # floor_area_sqft kept for future use / validation
        # floor_area_sqft = floor_area_m2 * (M_TO_FT ** 2)

        # --- Exterior studs ---
        # (perimeter_ft / stud_spacing_ft) × stories
        exterior_studs = (perimeter_ft * self.STUDS_PER_FT) * self.stories
        exterior_studs_rounded = round(exterior_studs)

        # --- Interior partition studs ---
        interior_studs = exterior_studs * self.INTERIOR_PARTITION_RATIO
        interior_studs_rounded = round(interior_studs)

        # --- Top/bottom plates ---
        # 3 plates × perimeter_ft / 8 ft per board
        plates_lf = perimeter_ft * self.PLATE_LAYERS * self.stories
        plates_boards = plates_lf / self.BOARD_LENGTH_FT
        plates_boards_rounded = round(plates_boards)

        # Metric equivalent: linear metres of plate material
        plates_lm = plates_lf * FT_TO_M

        # --- Header stock ---
        header_lf = perimeter_ft * self.HEADER_RATIO * self.stories
        header_lm = header_lf * FT_TO_M

        results = {
            "exterior_studs": MaterialQuantity(
                name="Exterior Wall Studs",
                quantity_metric=exterior_studs_rounded,
                unit_metric="pieces",
                quantity_imperial=exterior_studs_rounded,
                unit_imperial="pieces",
            ),
            "interior_partition_studs": MaterialQuantity(
                name="Interior Partition Studs",
                quantity_metric=interior_studs_rounded,
                unit_metric="pieces",
                quantity_imperial=interior_studs_rounded,
                unit_imperial="pieces",
            ),
            "top_bottom_plates_boards": MaterialQuantity(
                name="Top & Bottom Plates",
                quantity_metric=round(plates_lm, 1),
                unit_metric="linear metres",
                quantity_imperial=plates_boards_rounded,
                unit_imperial="8-ft boards",
            ),
            "header_stock_lf": MaterialQuantity(
                name="Header Stock",
                quantity_metric=round(header_lm, 1),
                unit_metric="linear metres",
                quantity_imperial=round(header_lf, 1),
                unit_imperial="linear feet",
            ),
        }

        return {key: mq.to_dict() for key, mq in results.items()}


# ------------------------------------------------------------------
# Framing cost estimator
# ------------------------------------------------------------------

FRAMING_UNIT_COSTS = {
    "stud": {"material": 4.50, "labor": 2.50},
    "plate": {"material": 4.00, "labor": 1.50},
    "header": {"material": 6.00, "labor": 3.00},
}

QUALITY_TIER_MULTIPLIERS = {
    "budget": 0.85,
    "standard": 1.0,
    "premium": 1.25,
    "luxury": 1.60,
}


def calculate_framing_costs(framing_quantities: Dict[str, Dict], quality_tier: str = "standard") -> Dict:
    """
    Calculate framing costs from StructuralCalculator quantities.

    Returns line items for studs, plates, and headers plus totals.
    """
    tier_multiplier = QUALITY_TIER_MULTIPLIERS.get(quality_tier, 1.0)

    exterior_studs = framing_quantities.get("exterior_studs", {}).get("quantity_imperial", 0)
    interior_studs = framing_quantities.get("interior_partition_studs", {}).get("quantity_imperial", 0)
    total_studs = exterior_studs + interior_studs

    plate_boards = framing_quantities.get("top_bottom_plates_boards", {}).get("quantity_imperial", 0)
    header_lf = framing_quantities.get("header_stock_lf", {}).get("quantity_imperial", 0)

    studs_material = total_studs * FRAMING_UNIT_COSTS["stud"]["material"] * tier_multiplier
    studs_labor = total_studs * FRAMING_UNIT_COSTS["stud"]["labor"] * tier_multiplier

    plates_material = plate_boards * FRAMING_UNIT_COSTS["plate"]["material"] * tier_multiplier
    plates_labor = plate_boards * FRAMING_UNIT_COSTS["plate"]["labor"] * tier_multiplier

    headers_material = header_lf * FRAMING_UNIT_COSTS["header"]["material"] * tier_multiplier
    headers_labor = header_lf * FRAMING_UNIT_COSTS["header"]["labor"] * tier_multiplier

    total_material = studs_material + plates_material + headers_material
    total_labor = studs_labor + plates_labor + headers_labor

    return {
        "line_items": {
            "studs": {
                "quantity": round(total_studs, 2),
                "unit": "studs",
                "material_cost": round(studs_material, 2),
                "labor_cost": round(studs_labor, 2),
                "total_cost": round(studs_material + studs_labor, 2),
            },
            "plates": {
                "quantity": round(plate_boards, 2),
                "unit": "8-ft boards",
                "material_cost": round(plates_material, 2),
                "labor_cost": round(plates_labor, 2),
                "total_cost": round(plates_material + plates_labor, 2),
            },
            "headers": {
                "quantity": round(header_lf, 2),
                "unit": "linear ft",
                "material_cost": round(headers_material, 2),
                "labor_cost": round(headers_labor, 2),
                "total_cost": round(headers_material + headers_labor, 2),
            },
        },
        "total_material": round(total_material, 2),
        "total_labor": round(total_labor, 2),
        "grand_total": round(total_material + total_labor, 2),
    }
