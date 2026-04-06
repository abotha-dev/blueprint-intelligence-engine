"""
Roofing cost estimator — standard gable roof, 4/12 pitch.
Source: NAHB 2024, RSMeans residential averages.
"""

class RoofingCalculator:
    PITCH_FACTOR = 1.30   # roof area = floor_area * 1.30 for 4/12 pitch
    WASTE_FACTOR = 1.10   # 10% shingle waste

    # 2025-2026 national average unit costs per sqft of ROOF area
    COSTS = {
        "budget":   {"shingles_per_sqft": 1.20, "decking_per_sqft": 0.90, "underlayment_per_sqft": 0.30, "labor_per_sqft": 2.50},
        "standard": {"shingles_per_sqft": 1.80, "decking_per_sqft": 1.10, "underlayment_per_sqft": 0.40, "labor_per_sqft": 3.20},
        "premium":  {"shingles_per_sqft": 3.50, "decking_per_sqft": 1.30, "underlayment_per_sqft": 0.50, "labor_per_sqft": 4.00},
        "luxury":   {"shingles_per_sqft": 6.00, "decking_per_sqft": 1.50, "underlayment_per_sqft": 0.60, "labor_per_sqft": 5.50},
    }

    def calculate(self, floor_area_sqft: float, quality_tier: str = "standard") -> dict:
        """
        Returns line items: shingles, decking, underlayment, labor.
        Returns total_material_cost, total_labor_cost, grand_total, roof_area_sqft.
        """
        costs = self.COSTS.get(quality_tier, self.COSTS["standard"])

        roof_area_sqft = floor_area_sqft * self.PITCH_FACTOR
        shingles_area = roof_area_sqft * self.WASTE_FACTOR

        shingles_cost = shingles_area * costs["shingles_per_sqft"]
        decking_cost = roof_area_sqft * costs["decking_per_sqft"]
        underlayment_cost = roof_area_sqft * costs["underlayment_per_sqft"]
        labor_cost = roof_area_sqft * costs["labor_per_sqft"]

        total_material = shingles_cost + decking_cost + underlayment_cost
        total_labor = labor_cost

        return {
            "roof_area_sqft": round(roof_area_sqft, 2),
            "line_items": {
                "shingles": {
                    "quantity": round(shingles_area, 2),
                    "unit": "sqft",
                    "material_cost": round(shingles_cost, 2),
                    "labor_cost": 0.0,
                    "total_cost": round(shingles_cost, 2),
                },
                "decking": {
                    "quantity": round(roof_area_sqft, 2),
                    "unit": "sqft",
                    "material_cost": round(decking_cost, 2),
                    "labor_cost": 0.0,
                    "total_cost": round(decking_cost, 2),
                },
                "underlayment": {
                    "quantity": round(roof_area_sqft, 2),
                    "unit": "sqft",
                    "material_cost": round(underlayment_cost, 2),
                    "labor_cost": 0.0,
                    "total_cost": round(underlayment_cost, 2),
                },
                "labor": {
                    "quantity": round(roof_area_sqft, 2),
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
