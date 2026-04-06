"""
Foundation cost estimator — slab-on-grade (most common residential).
Source: NAHB 2024, RSMeans residential averages.
"""

class FoundationCalculator:
    # Slab-on-grade assumptions
    SLAB_THICKNESS_IN = 4          # inches
    CONCRETE_WASTE_FACTOR = 1.08   # 8% waste

    # 2025-2026 national average unit costs
    COSTS = {
        "budget":   {"concrete_per_sqft": 5.50, "labor_per_sqft": 3.20, "rebar_per_sqft": 0.80, "forming_per_sqft": 1.20},
        "standard": {"concrete_per_sqft": 6.50, "labor_per_sqft": 4.00, "rebar_per_sqft": 1.00, "forming_per_sqft": 1.50},
        "premium":  {"concrete_per_sqft": 8.00, "labor_per_sqft": 5.00, "rebar_per_sqft": 1.20, "forming_per_sqft": 1.80},
        "luxury":   {"concrete_per_sqft": 10.00,"labor_per_sqft": 6.50, "rebar_per_sqft": 1.50, "forming_per_sqft": 2.20},
    }

    def calculate(self, floor_area_sqft: float, quality_tier: str = "standard") -> dict:
        """
        Returns line items: concrete, rebar, forming, labor.
        Returns total_material_cost, total_labor_cost, grand_total.
        """
        costs = self.COSTS.get(quality_tier, self.COSTS["standard"])

        effective_area = floor_area_sqft * self.CONCRETE_WASTE_FACTOR

        concrete_cost = effective_area * costs["concrete_per_sqft"]
        rebar_cost = floor_area_sqft * costs["rebar_per_sqft"]
        forming_cost = floor_area_sqft * costs["forming_per_sqft"]
        labor_cost = floor_area_sqft * costs["labor_per_sqft"]

        total_material = concrete_cost + rebar_cost + forming_cost
        total_labor = labor_cost

        return {
            "line_items": {
                "concrete": {
                    "quantity": round(effective_area, 2),
                    "unit": "sqft",
                    "material_cost": round(concrete_cost, 2),
                    "labor_cost": 0.0,
                    "total_cost": round(concrete_cost, 2),
                },
                "rebar": {
                    "quantity": round(floor_area_sqft, 2),
                    "unit": "sqft",
                    "material_cost": round(rebar_cost, 2),
                    "labor_cost": 0.0,
                    "total_cost": round(rebar_cost, 2),
                },
                "forming": {
                    "quantity": round(floor_area_sqft, 2),
                    "unit": "sqft",
                    "material_cost": round(forming_cost, 2),
                    "labor_cost": 0.0,
                    "total_cost": round(forming_cost, 2),
                },
                "labor": {
                    "quantity": round(floor_area_sqft, 2),
                    "unit": "sqft",
                    "material_cost": 0.0,
                    "labor_cost": round(labor_cost, 2),
                    "total_cost": round(labor_cost, 2),
                },
            },
            "total_material": round(total_material, 2),
            "total_labor": round(total_labor, 2),
            "grand_total": round(total_material + total_labor, 2),
        }
