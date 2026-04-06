"""
Exterior finishes estimator — windows, doors, siding, trim.
Quantities derived from floor area, perimeter, and room type counts.
Source: NAHB 2024, RSMeans residential averages.
"""


class ExteriorCalculator:
    # Window ratios: standard residential
    # ~1 window per 150 sqft of conditioned space (not garage)
    WINDOW_SQFT_RATIO = 150
    WINDOWS_PER_BEDROOM = 2   # bedrooms typically have 2 windows
    WINDOWS_PER_LIVING = 3    # living/family room
    WINDOWS_PER_KITCHEN = 1
    WINDOWS_MIN = 4           # minimum for any house

    # Door counts
    EXTERIOR_DOORS_BASE = 2   # front + back standard
    INTERIOR_DOOR_PER_BEDROOM = 1
    INTERIOR_DOOR_PER_BATHROOM = 1
    INTERIOR_DOOR_BASE = 2    # closets, utility

    # 2025-2026 unit costs (material + install)
    COSTS = {
        "budget": {
            "window_double_hung": {"material": 280, "labor": 120},
            "exterior_door_front": {"material": 600, "labor": 200},
            "exterior_door_standard": {"material": 350, "labor": 150},
            "interior_door": {"material": 150, "labor": 80},
            "siding_per_sqft": {"material": 3.50, "labor": 2.50},
            "trim_per_lf": {"material": 1.20, "labor": 1.00},
        },
        "standard": {
            "window_double_hung": {"material": 450, "labor": 150},
            "exterior_door_front": {"material": 900, "labor": 250},
            "exterior_door_standard": {"material": 500, "labor": 175},
            "interior_door": {"material": 220, "labor": 100},
            "siding_per_sqft": {"material": 5.50, "labor": 3.50},
            "trim_per_lf": {"material": 2.00, "labor": 1.50},
        },
        "premium": {
            "window_double_hung": {"material": 750, "labor": 200},
            "exterior_door_front": {"material": 1800, "labor": 300},
            "exterior_door_standard": {"material": 900, "labor": 220},
            "interior_door": {"material": 400, "labor": 130},
            "siding_per_sqft": {"material": 9.00, "labor": 4.50},
            "trim_per_lf": {"material": 3.50, "labor": 2.00},
        },
        "luxury": {
            "window_double_hung": {"material": 1400, "labor": 300},
            "exterior_door_front": {"material": 4000, "labor": 400},
            "exterior_door_standard": {"material": 1800, "labor": 300},
            "interior_door": {"material": 800, "labor": 180},
            "siding_per_sqft": {"material": 15.00, "labor": 6.00},
            "trim_per_lf": {"material": 6.00, "labor": 3.00},
        },
    }

    def calculate(
        self,
        floor_area_sqft: float,
        perimeter_ft: float,
        rooms: list,  # list of dicts with 'name' and 'area'
        quality_tier: str = "standard",
        ceiling_height_ft: float = 9.0,
    ) -> dict:
        """
        Returns windows, exterior doors, interior doors, siding, trim costs.

        rooms: list of room dicts from blueprint analysis
        """
        costs = self.COSTS.get(quality_tier, self.COSTS["standard"])

        # --- Count room types ---
        bedrooms = sum(1 for r in rooms if "bed" in r.get("name", "").lower())
        bathrooms = sum(1 for r in rooms if "bath" in r.get("name", "").lower())
        has_garage = any("garage" in r.get("name", "").lower() for r in rooms)

        # Conditioned area = total minus garage
        garage_area = sum(r.get("area", 0) for r in rooms if "garage" in r.get("name", "").lower())
        conditioned_sqft = floor_area_sqft - garage_area

        # --- Windows ---
        window_count = max(
            self.WINDOWS_MIN,
            round(conditioned_sqft / self.WINDOW_SQFT_RATIO)
        )
        # Adjust for bedroom count (more bedrooms = more windows)
        window_count = max(window_count, bedrooms * self.WINDOWS_PER_BEDROOM + 2)

        window_material = window_count * costs["window_double_hung"]["material"]
        window_labor = window_count * costs["window_double_hung"]["labor"]

        # --- Exterior doors ---
        ext_door_count = self.EXTERIOR_DOORS_BASE
        if has_garage:
            ext_door_count += 1  # garage access door

        front_door_material = costs["exterior_door_front"]["material"]
        front_door_labor = costs["exterior_door_front"]["labor"]
        other_doors_material = (ext_door_count - 1) * costs["exterior_door_standard"]["material"]
        other_doors_labor = (ext_door_count - 1) * costs["exterior_door_standard"]["labor"]

        ext_door_material = front_door_material + other_doors_material
        ext_door_labor = front_door_labor + other_doors_labor

        # --- Interior doors ---
        int_door_count = (
            bedrooms * self.INTERIOR_DOOR_PER_BEDROOM +
            bathrooms * self.INTERIOR_DOOR_PER_BATHROOM +
            self.INTERIOR_DOOR_BASE
        )
        int_door_count = max(int_door_count, 3)

        int_door_material = int_door_count * costs["interior_door"]["material"]
        int_door_labor = int_door_count * costs["interior_door"]["labor"]

        # --- Exterior siding ---
        # Wall area = perimeter * ceiling height, minus window/door openings (~15%)
        wall_area_sqft = perimeter_ft * ceiling_height_ft * 0.85
        siding_material = wall_area_sqft * costs["siding_per_sqft"]["material"]
        siding_labor = wall_area_sqft * costs["siding_per_sqft"]["labor"]

        # --- Exterior trim ---
        # Trim = perimeter * 2 (windows + corners + fascia rough estimate)
        trim_lf = perimeter_ft * 2.0
        trim_material = trim_lf * costs["trim_per_lf"]["material"]
        trim_labor = trim_lf * costs["trim_per_lf"]["labor"]

        # --- Totals ---
        total_material = (
            window_material + ext_door_material + int_door_material +
            siding_material + trim_material
        )
        total_labor = (
            window_labor + ext_door_labor + int_door_labor +
            siding_labor + trim_labor
        )

        return {
            "window_count": window_count,
            "exterior_door_count": ext_door_count,
            "interior_door_count": int_door_count,
            "wall_area_sqft": round(wall_area_sqft, 1),
            "line_items": {
                "windows": {
                    "quantity": window_count,
                    "unit": "windows",
                    "material_cost": round(window_material, 2),
                    "labor_cost": round(window_labor, 2),
                    "total_cost": round(window_material + window_labor, 2),
                },
                "exterior_doors": {
                    "quantity": ext_door_count,
                    "unit": "doors",
                    "material_cost": round(ext_door_material, 2),
                    "labor_cost": round(ext_door_labor, 2),
                    "total_cost": round(ext_door_material + ext_door_labor, 2),
                },
                "interior_doors": {
                    "quantity": int_door_count,
                    "unit": "doors",
                    "material_cost": round(int_door_material, 2),
                    "labor_cost": round(int_door_labor, 2),
                    "total_cost": round(int_door_material + int_door_labor, 2),
                },
                "exterior_siding": {
                    "quantity": round(wall_area_sqft, 1),
                    "unit": "sqft",
                    "material_cost": round(siding_material, 2),
                    "labor_cost": round(siding_labor, 2),
                    "total_cost": round(siding_material + siding_labor, 2),
                },
                "exterior_trim": {
                    "quantity": round(trim_lf, 1),
                    "unit": "linear ft",
                    "material_cost": round(trim_material, 2),
                    "labor_cost": round(trim_labor, 2),
                    "total_cost": round(trim_material + trim_labor, 2),
                },
            },
            "total_material": round(total_material, 2),
            "total_labor": round(total_labor, 2),
            "grand_total": round(total_material + total_labor, 2),
        }
