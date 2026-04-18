"""
Takeoff.ai - Cost Estimation Engine

This module provides cost estimates based on material quantities
using current market pricing data.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from enum import Enum
from datetime import datetime

from .material_calculator import MaterialQuantity


class QualityTier(Enum):
    """Quality tiers for materials."""
    BUDGET = "budget"
    STANDARD = "standard"
    PREMIUM = "premium"
    LUXURY = "luxury"


class Region(Enum):
    """Geographic regions for pricing."""
    US_NATIONAL = "us_national"
    US_NORTHEAST = "us_northeast"
    US_SOUTHEAST = "us_southeast"
    US_MIDWEST = "us_midwest"
    US_SOUTHWEST = "us_southwest"
    US_WEST = "us_west"


class LaborAvailability(Enum):
    """Labor market availability levels."""
    LOW = "low"          # Labor shortage - higher costs
    AVERAGE = "average"  # Normal market conditions
    HIGH = "high"        # Labor surplus - lower costs


# Labor availability multipliers
LABOR_AVAILABILITY_MULTIPLIERS = {
    LaborAvailability.LOW: 1.15,      # +15% labor cost (shortage)
    LaborAvailability.AVERAGE: 1.00,  # No adjustment
    LaborAvailability.HIGH: 0.90,     # -10% labor cost (surplus)
}

MEP_MULTIPLIER = 0.25  # 25% of structural shell — midpoint of 22–28% NAHB range


class RoomType(Enum):
    """Room types for category-specific calculations."""
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    BEDROOM = "bedroom"
    LIVING_ROOM = "living_room"
    DINING_ROOM = "dining_room"
    OTHER = "other"


@dataclass
class PricePoint:
    """Price information for a material at a specific quality tier."""
    price_per_unit: float
    unit: str
    quality_tier: QualityTier
    brand_example: str = ""
    notes: str = ""


@dataclass
class MaterialPricing:
    """Complete pricing information for a material type."""
    material_type: str
    display_name: str
    price_points: Dict[QualityTier, PricePoint] = field(default_factory=dict)
    labor_rate_per_unit: float = 0.0  # Labor cost per unit installed
    labor_unit: str = "sq ft"
    category: str = "general"  # Category for grouping (flooring, kitchen, bathroom, etc.)


@dataclass
class CostEstimate:
    """Cost estimate for a specific material."""
    material_type: str
    display_name: str
    quality_tier: QualityTier
    units_needed: int
    unit: str
    material_cost: float
    labor_cost: float
    total_cost: float
    price_per_unit: float
    brand_example: str = ""
    notes: str = ""
    category: str = "general"


@dataclass
class ProjectEstimate:
    """Complete cost estimate for a project."""
    project_name: str
    timestamp: str
    region: Region
    estimates: List[CostEstimate] = field(default_factory=list)
    subtotal_materials: float = 0.0
    subtotal_labor: float = 0.0
    contingency_percent: float = 0.10
    contingency_amount: float = 0.0
    total_estimate: float = 0.0
    notes: List[str] = field(default_factory=list)
    mep_breakdown: Optional[Dict[str, Union[float, str, List[str]]]] = None
    demo_breakdown: Optional[Dict] = None


class PricingDatabase:
    """
    Material pricing database with current market rates.
    
    Prices are approximate US national averages as of 2024-2025.
    Actual prices vary by region, supplier, and market conditions.
    """
    
    # Material pricing data
    PRICING_DATA: Dict[str, MaterialPricing] = {
        # ==================== FLOORING ====================
        "flooring_hardwood": MaterialPricing(
            material_type="flooring_hardwood",
            display_name="Hardwood Flooring",
            price_points={
                QualityTier.BUDGET: PricePoint(2.50, "sq ft", QualityTier.BUDGET, "Builder's Pride", "Thin veneer, limited warranty"),
                QualityTier.STANDARD: PricePoint(5.00, "sq ft", QualityTier.STANDARD, "Bruce, Mohawk", "3/4\" solid, 25-year warranty"),
                QualityTier.PREMIUM: PricePoint(8.00, "sq ft", QualityTier.PREMIUM, "Shaw, Armstrong", "Premium species, lifetime warranty"),
                QualityTier.LUXURY: PricePoint(15.00, "sq ft", QualityTier.LUXURY, "Carlisle, Duchateau", "Wide plank, exotic species"),
            },
            labor_rate_per_unit=4.00,
            labor_unit="sq ft",
            category="flooring"
        ),
        "flooring_laminate": MaterialPricing(
            material_type="flooring_laminate",
            display_name="Laminate Flooring",
            price_points={
                QualityTier.BUDGET: PricePoint(1.00, "sq ft", QualityTier.BUDGET, "TrafficMaster", "6mm, basic warranty"),
                QualityTier.STANDARD: PricePoint(2.50, "sq ft", QualityTier.STANDARD, "Pergo, Mohawk", "10mm, 20-year warranty"),
                QualityTier.PREMIUM: PricePoint(4.00, "sq ft", QualityTier.PREMIUM, "Quick-Step", "12mm, waterproof"),
                QualityTier.LUXURY: PricePoint(6.00, "sq ft", QualityTier.LUXURY, "Kaindl, Kronotex", "Premium European"),
            },
            labor_rate_per_unit=2.50,
            labor_unit="sq ft",
            category="flooring"
        ),
        "flooring_tile": MaterialPricing(
            material_type="flooring_tile",
            display_name="Ceramic/Porcelain Tile",
            price_points={
                QualityTier.BUDGET: PricePoint(1.50, "sq ft", QualityTier.BUDGET, "MSI, Florida Tile", "Basic ceramic"),
                QualityTier.STANDARD: PricePoint(4.00, "sq ft", QualityTier.STANDARD, "Daltile, Marazzi", "Porcelain, varied patterns"),
                QualityTier.PREMIUM: PricePoint(8.00, "sq ft", QualityTier.PREMIUM, "Emser, Crossville", "Large format, premium finish"),
                QualityTier.LUXURY: PricePoint(15.00, "sq ft", QualityTier.LUXURY, "Artistic Tile, Ann Sacks", "Designer, natural stone"),
            },
            labor_rate_per_unit=6.00,
            labor_unit="sq ft",
            category="flooring"
        ),
        "flooring_carpet": MaterialPricing(
            material_type="flooring_carpet",
            display_name="Carpet",
            price_points={
                QualityTier.BUDGET: PricePoint(1.00, "sq ft", QualityTier.BUDGET, "LifeProof", "Basic polyester"),
                QualityTier.STANDARD: PricePoint(3.00, "sq ft", QualityTier.STANDARD, "Shaw, Mohawk", "Nylon, stain resistant"),
                QualityTier.PREMIUM: PricePoint(6.00, "sq ft", QualityTier.PREMIUM, "Karastan", "Premium nylon, plush"),
                QualityTier.LUXURY: PricePoint(12.00, "sq ft", QualityTier.LUXURY, "Stanton, Masland", "Wool, custom patterns"),
            },
            labor_rate_per_unit=1.50,
            labor_unit="sq ft",
            category="flooring"
        ),
        
        # ==================== PAINT ====================
        "paint_wall": MaterialPricing(
            material_type="paint_wall",
            display_name="Interior Wall Paint",
            price_points={
                QualityTier.BUDGET: PricePoint(25.00, "gallon", QualityTier.BUDGET, "Glidden, Valspar", "Basic latex"),
                QualityTier.STANDARD: PricePoint(45.00, "gallon", QualityTier.STANDARD, "Behr, PPG", "Premium latex, washable"),
                QualityTier.PREMIUM: PricePoint(65.00, "gallon", QualityTier.PREMIUM, "Benjamin Moore, Sherwin-Williams", "Designer colors, low VOC"),
                QualityTier.LUXURY: PricePoint(100.00, "gallon", QualityTier.LUXURY, "Farrow & Ball, Fine Paints", "Artisan, specialty finishes"),
            },
            labor_rate_per_unit=2.00,
            labor_unit="sq ft",
            category="paint"
        ),
        "paint_ceiling": MaterialPricing(
            material_type="paint_ceiling",
            display_name="Ceiling Paint",
            price_points={
                QualityTier.BUDGET: PricePoint(20.00, "gallon", QualityTier.BUDGET, "Glidden Ceiling", "Flat white"),
                QualityTier.STANDARD: PricePoint(35.00, "gallon", QualityTier.STANDARD, "Behr Ceiling", "Ultra flat, splatter-resistant"),
                QualityTier.PREMIUM: PricePoint(55.00, "gallon", QualityTier.PREMIUM, "Benjamin Moore", "Premium ceiling paint"),
                QualityTier.LUXURY: PricePoint(80.00, "gallon", QualityTier.LUXURY, "Fine Paints of Europe", "Specialty ceiling"),
            },
            labor_rate_per_unit=1.50,
            labor_unit="sq ft",
            category="paint"
        ),
        
        # ==================== DRYWALL ====================
        "drywall": MaterialPricing(
            material_type="drywall",
            display_name="Drywall",
            price_points={
                QualityTier.BUDGET: PricePoint(12.00, "sheet", QualityTier.BUDGET, "USG, National Gypsum", "1/2\" standard"),
                QualityTier.STANDARD: PricePoint(15.00, "sheet", QualityTier.STANDARD, "USG Sheetrock", "1/2\" moisture resistant"),
                QualityTier.PREMIUM: PricePoint(25.00, "sheet", QualityTier.PREMIUM, "USG Mold Tough", "Mold/moisture resistant"),
                QualityTier.LUXURY: PricePoint(40.00, "sheet", QualityTier.LUXURY, "QuietRock", "Soundproof drywall"),
            },
            labor_rate_per_unit=2.00,
            labor_unit="sq ft",
            category="drywall"
        ),
        
        # ==================== TRIM ====================
        "baseboard": MaterialPricing(
            material_type="baseboard",
            display_name="Baseboard Trim",
            price_points={
                QualityTier.BUDGET: PricePoint(1.00, "linear ft", QualityTier.BUDGET, "MDF primed", "3.25\" MDF"),
                QualityTier.STANDARD: PricePoint(2.50, "linear ft", QualityTier.STANDARD, "Pine, poplar", "Solid wood, paintable"),
                QualityTier.PREMIUM: PricePoint(5.00, "linear ft", QualityTier.PREMIUM, "Oak, maple", "Hardwood, stainable"),
                QualityTier.LUXURY: PricePoint(10.00, "linear ft", QualityTier.LUXURY, "Custom millwork", "Custom profiles"),
            },
            labor_rate_per_unit=3.00,
            labor_unit="linear ft",
            category="trim"
        ),
        "crown_molding": MaterialPricing(
            material_type="crown_molding",
            display_name="Crown Molding",
            price_points={
                QualityTier.BUDGET: PricePoint(1.50, "linear ft", QualityTier.BUDGET, "Polystyrene", "Foam, lightweight"),
                QualityTier.STANDARD: PricePoint(4.00, "linear ft", QualityTier.STANDARD, "MDF, pine", "3.5\" profile"),
                QualityTier.PREMIUM: PricePoint(8.00, "linear ft", QualityTier.PREMIUM, "Hardwood", "5.25\" ornate"),
                QualityTier.LUXURY: PricePoint(15.00, "linear ft", QualityTier.LUXURY, "Custom millwork", "Multi-piece crown"),
            },
            labor_rate_per_unit=5.00,
            labor_unit="linear ft",
            category="trim"
        ),
        
        # ==================== KITCHEN CABINETS ====================
        "cabinets_base": MaterialPricing(
            material_type="cabinets_base",
            display_name="Base Cabinets",
            price_points={
                QualityTier.BUDGET: PricePoint(75.00, "linear ft", QualityTier.BUDGET, "Hampton Bay, In-Stock", "Thermofoil, basic hardware"),
                QualityTier.STANDARD: PricePoint(150.00, "linear ft", QualityTier.STANDARD, "KraftMaid, Diamond", "Plywood box, soft-close"),
                QualityTier.PREMIUM: PricePoint(300.00, "linear ft", QualityTier.PREMIUM, "Wellborn, Medallion", "All-plywood, dovetail drawers"),
                QualityTier.LUXURY: PricePoint(500.00, "linear ft", QualityTier.LUXURY, "Custom, Wood-Mode", "Custom built, premium wood"),
            },
            labor_rate_per_unit=50.00,
            labor_unit="linear ft",
            category="kitchen"
        ),
        "cabinets_wall": MaterialPricing(
            material_type="cabinets_wall",
            display_name="Wall Cabinets",
            price_points={
                QualityTier.BUDGET: PricePoint(65.00, "linear ft", QualityTier.BUDGET, "Hampton Bay, In-Stock", "Thermofoil, basic hardware"),
                QualityTier.STANDARD: PricePoint(125.00, "linear ft", QualityTier.STANDARD, "KraftMaid, Diamond", "Plywood box, soft-close"),
                QualityTier.PREMIUM: PricePoint(250.00, "linear ft", QualityTier.PREMIUM, "Wellborn, Medallion", "All-plywood, dovetail"),
                QualityTier.LUXURY: PricePoint(450.00, "linear ft", QualityTier.LUXURY, "Custom, Wood-Mode", "Custom built, premium wood"),
            },
            labor_rate_per_unit=40.00,
            labor_unit="linear ft",
            category="kitchen"
        ),
        
        # ==================== COUNTERTOPS ====================
        "countertop_laminate": MaterialPricing(
            material_type="countertop_laminate",
            display_name="Laminate Countertop",
            price_points={
                QualityTier.BUDGET: PricePoint(15.00, "sq ft", QualityTier.BUDGET, "Formica, Wilsonart", "Basic patterns"),
                QualityTier.STANDARD: PricePoint(25.00, "sq ft", QualityTier.STANDARD, "Formica 180fx", "Stone-look patterns"),
                QualityTier.PREMIUM: PricePoint(40.00, "sq ft", QualityTier.PREMIUM, "Wilsonart HD", "Premium edge profiles"),
                QualityTier.LUXURY: PricePoint(60.00, "sq ft", QualityTier.LUXURY, "Custom laminate", "Integrated backsplash"),
            },
            labor_rate_per_unit=10.00,
            labor_unit="sq ft",
            category="kitchen"
        ),
        "countertop_granite": MaterialPricing(
            material_type="countertop_granite",
            display_name="Granite Countertop",
            price_points={
                QualityTier.BUDGET: PricePoint(40.00, "sq ft", QualityTier.BUDGET, "Level 1 granite", "Builder grade, limited colors"),
                QualityTier.STANDARD: PricePoint(60.00, "sq ft", QualityTier.STANDARD, "Level 2-3 granite", "Popular colors, eased edge"),
                QualityTier.PREMIUM: PricePoint(85.00, "sq ft", QualityTier.PREMIUM, "Level 4-5 granite", "Exotic patterns, ogee edge"),
                QualityTier.LUXURY: PricePoint(150.00, "sq ft", QualityTier.LUXURY, "Rare/exotic granite", "Book-matched, waterfall edge"),
            },
            labor_rate_per_unit=25.00,
            labor_unit="sq ft",
            category="kitchen"
        ),
        "countertop_quartz": MaterialPricing(
            material_type="countertop_quartz",
            display_name="Quartz Countertop",
            price_points={
                QualityTier.BUDGET: PricePoint(50.00, "sq ft", QualityTier.BUDGET, "MSI Q, Allen+Roth", "Basic colors"),
                QualityTier.STANDARD: PricePoint(75.00, "sq ft", QualityTier.STANDARD, "Silestone, Cambria", "Popular patterns"),
                QualityTier.PREMIUM: PricePoint(100.00, "sq ft", QualityTier.PREMIUM, "Caesarstone", "Premium veining"),
                QualityTier.LUXURY: PricePoint(150.00, "sq ft", QualityTier.LUXURY, "Dekton, Neolith", "Ultra-premium, large format"),
            },
            labor_rate_per_unit=25.00,
            labor_unit="sq ft",
            category="kitchen"
        ),
        
        # ==================== KITCHEN FIXTURES ====================
        "backsplash_tile": MaterialPricing(
            material_type="backsplash_tile",
            display_name="Tile Backsplash",
            price_points={
                QualityTier.BUDGET: PricePoint(5.00, "sq ft", QualityTier.BUDGET, "Ceramic subway", "3x6 basic white"),
                QualityTier.STANDARD: PricePoint(15.00, "sq ft", QualityTier.STANDARD, "Glass, porcelain", "Mosaic patterns"),
                QualityTier.PREMIUM: PricePoint(30.00, "sq ft", QualityTier.PREMIUM, "Natural stone", "Marble, travertine"),
                QualityTier.LUXURY: PricePoint(50.00, "sq ft", QualityTier.LUXURY, "Designer tile", "Handmade, artistic"),
            },
            labor_rate_per_unit=12.00,
            labor_unit="sq ft",
            category="kitchen"
        ),
        "kitchen_sink": MaterialPricing(
            material_type="kitchen_sink",
            display_name="Kitchen Sink",
            price_points={
                QualityTier.BUDGET: PricePoint(150.00, "unit", QualityTier.BUDGET, "Glacier Bay", "Stainless, drop-in"),
                QualityTier.STANDARD: PricePoint(350.00, "unit", QualityTier.STANDARD, "Kraus, Elkay", "Undermount stainless"),
                QualityTier.PREMIUM: PricePoint(600.00, "unit", QualityTier.PREMIUM, "Blanco, Kohler", "Composite, farmhouse"),
                QualityTier.LUXURY: PricePoint(1200.00, "unit", QualityTier.LUXURY, "Rohl, Julien", "Fireclay, copper"),
            },
            labor_rate_per_unit=250.00,
            labor_unit="unit",
            category="kitchen"
        ),
        "kitchen_faucet": MaterialPricing(
            material_type="kitchen_faucet",
            display_name="Kitchen Faucet",
            price_points={
                QualityTier.BUDGET: PricePoint(80.00, "unit", QualityTier.BUDGET, "Glacier Bay, Peerless", "Basic pull-down"),
                QualityTier.STANDARD: PricePoint(200.00, "unit", QualityTier.STANDARD, "Moen, Delta", "Pull-down, spot-resist"),
                QualityTier.PREMIUM: PricePoint(400.00, "unit", QualityTier.PREMIUM, "Kohler, Grohe", "Touchless, pro-style"),
                QualityTier.LUXURY: PricePoint(800.00, "unit", QualityTier.LUXURY, "Brizo, Waterstone", "Designer, articulating"),
            },
            labor_rate_per_unit=150.00,
            labor_unit="unit",
            category="kitchen"
        ),
        
        # ==================== BATHROOM VANITY & FIXTURES ====================
        "vanity_cabinet": MaterialPricing(
            material_type="vanity_cabinet",
            display_name="Bathroom Vanity",
            price_points={
                QualityTier.BUDGET: PricePoint(200.00, "unit", QualityTier.BUDGET, "Glacier Bay", "24-36\" basic"),
                QualityTier.STANDARD: PricePoint(500.00, "unit", QualityTier.STANDARD, "Home Decorators", "36-48\" with top"),
                QualityTier.PREMIUM: PricePoint(1200.00, "unit", QualityTier.PREMIUM, "James Martin", "48-60\" furniture style"),
                QualityTier.LUXURY: PricePoint(2500.00, "unit", QualityTier.LUXURY, "Custom, RH", "60\"+ custom"),
            },
            labor_rate_per_unit=300.00,
            labor_unit="unit",
            category="bathroom"
        ),
        "toilet": MaterialPricing(
            material_type="toilet",
            display_name="Toilet",
            price_points={
                QualityTier.BUDGET: PricePoint(150.00, "unit", QualityTier.BUDGET, "Glacier Bay, Project Source", "Round, basic"),
                QualityTier.STANDARD: PricePoint(300.00, "unit", QualityTier.STANDARD, "American Standard, Kohler", "Elongated, comfort height"),
                QualityTier.PREMIUM: PricePoint(500.00, "unit", QualityTier.PREMIUM, "Toto, Kohler", "One-piece, soft-close"),
                QualityTier.LUXURY: PricePoint(1500.00, "unit", QualityTier.LUXURY, "Toto Neorest, Kohler Veil", "Bidet, smart toilet"),
            },
            labor_rate_per_unit=200.00,
            labor_unit="unit",
            category="bathroom"
        ),
        "bathroom_faucet": MaterialPricing(
            material_type="bathroom_faucet",
            display_name="Bathroom Faucet",
            price_points={
                QualityTier.BUDGET: PricePoint(50.00, "unit", QualityTier.BUDGET, "Glacier Bay", "Single-handle chrome"),
                QualityTier.STANDARD: PricePoint(150.00, "unit", QualityTier.STANDARD, "Moen, Delta", "Widespread, brushed nickel"),
                QualityTier.PREMIUM: PricePoint(350.00, "unit", QualityTier.PREMIUM, "Kohler, Grohe", "Designer finishes"),
                QualityTier.LUXURY: PricePoint(700.00, "unit", QualityTier.LUXURY, "Brizo, Waterworks", "Unlacquered brass, wall-mount"),
            },
            labor_rate_per_unit=125.00,
            labor_unit="unit",
            category="bathroom"
        ),
        "shower_tile": MaterialPricing(
            material_type="shower_tile",
            display_name="Shower/Tub Tile",
            price_points={
                QualityTier.BUDGET: PricePoint(4.00, "sq ft", QualityTier.BUDGET, "Ceramic subway", "Basic white 4x12"),
                QualityTier.STANDARD: PricePoint(10.00, "sq ft", QualityTier.STANDARD, "Porcelain, glass accent", "Large format"),
                QualityTier.PREMIUM: PricePoint(20.00, "sq ft", QualityTier.PREMIUM, "Natural stone", "Marble, slate"),
                QualityTier.LUXURY: PricePoint(40.00, "sq ft", QualityTier.LUXURY, "Designer tile", "Zellige, handmade"),
            },
            labor_rate_per_unit=15.00,
            labor_unit="sq ft",
            category="bathroom"
        ),
        "shower_door": MaterialPricing(
            material_type="shower_door",
            display_name="Shower Door/Enclosure",
            price_points={
                QualityTier.BUDGET: PricePoint(300.00, "unit", QualityTier.BUDGET, "Delta, Sterling", "Framed sliding"),
                QualityTier.STANDARD: PricePoint(600.00, "unit", QualityTier.STANDARD, "DreamLine", "Semi-frameless pivot"),
                QualityTier.PREMIUM: PricePoint(1200.00, "unit", QualityTier.PREMIUM, "Kohler, Basco", "Frameless, clear glass"),
                QualityTier.LUXURY: PricePoint(2500.00, "unit", QualityTier.LUXURY, "Custom glass", "Custom frameless, hardware"),
            },
            labor_rate_per_unit=350.00,
            labor_unit="unit",
            category="bathroom"
        ),
        "bathtub": MaterialPricing(
            material_type="bathtub",
            display_name="Bathtub",
            price_points={
                QualityTier.BUDGET: PricePoint(200.00, "unit", QualityTier.BUDGET, "Bootz, American Standard", "Steel alcove"),
                QualityTier.STANDARD: PricePoint(500.00, "unit", QualityTier.STANDARD, "Kohler, American Standard", "Acrylic alcove"),
                QualityTier.PREMIUM: PricePoint(1500.00, "unit", QualityTier.PREMIUM, "Kohler, Jacuzzi", "Freestanding acrylic"),
                QualityTier.LUXURY: PricePoint(4000.00, "unit", QualityTier.LUXURY, "Victoria + Albert, MTI", "Cast iron, stone resin"),
            },
            labor_rate_per_unit=500.00,
            labor_unit="unit",
            category="bathroom"
        ),
        "bathroom_exhaust_fan": MaterialPricing(
            material_type="bathroom_exhaust_fan",
            display_name="Exhaust Fan",
            price_points={
                QualityTier.BUDGET: PricePoint(30.00, "unit", QualityTier.BUDGET, "Broan, NuTone", "Basic 50 CFM"),
                QualityTier.STANDARD: PricePoint(100.00, "unit", QualityTier.STANDARD, "Panasonic WhisperCeiling", "80 CFM, quiet"),
                QualityTier.PREMIUM: PricePoint(200.00, "unit", QualityTier.PREMIUM, "Panasonic WhisperGreen", "110 CFM, humidity sensor"),
                QualityTier.LUXURY: PricePoint(400.00, "unit", QualityTier.LUXURY, "Panasonic WhisperWarm", "Fan + heater + light"),
            },
            labor_rate_per_unit=150.00,
            labor_unit="unit",
            category="bathroom"
        ),

        # ==================== ELECTRICAL ====================
        "electrical_outlet": MaterialPricing(
            material_type="electrical_outlet",
            display_name="Electrical Outlet (Duplex)",
            price_points={
                QualityTier.BUDGET: PricePoint(5.00, "unit", QualityTier.BUDGET, "Leviton, Pass & Seymour", "Basic 15A duplex"),
                QualityTier.STANDARD: PricePoint(12.00, "unit", QualityTier.STANDARD, "Leviton Decora", "15A tamper-resistant"),
                QualityTier.PREMIUM: PricePoint(25.00, "unit", QualityTier.PREMIUM, "Lutron, Legrand", "USB-A/C combo, TR"),
                QualityTier.LUXURY: PricePoint(60.00, "unit", QualityTier.LUXURY, "Legrand Radiant", "USB-C 30W, designer plate"),
            },
            labor_rate_per_unit=20.00,
            labor_unit="unit",
            category="electrical"
        ),
        "electrical_gfi_outlet": MaterialPricing(
            material_type="electrical_gfi_outlet",
            display_name="GFI Outlet",
            price_points={
                QualityTier.BUDGET: PricePoint(15.00, "unit", QualityTier.BUDGET, "Leviton", "15A GFCI, basic"),
                QualityTier.STANDARD: PricePoint(25.00, "unit", QualityTier.STANDARD, "Leviton SmartlockPro", "20A GFCI, self-test"),
                QualityTier.PREMIUM: PricePoint(45.00, "unit", QualityTier.PREMIUM, "Lutron, Legrand", "20A GFCI with USB"),
                QualityTier.LUXURY: PricePoint(80.00, "unit", QualityTier.LUXURY, "Legrand Radiant", "Designer GFCI with USB-C"),
            },
            labor_rate_per_unit=25.00,
            labor_unit="unit",
            category="electrical"
        ),
        "electrical_switch": MaterialPricing(
            material_type="electrical_switch",
            display_name="Light Switch",
            price_points={
                QualityTier.BUDGET: PricePoint(5.00, "unit", QualityTier.BUDGET, "Leviton", "Single-pole, basic"),
                QualityTier.STANDARD: PricePoint(12.00, "unit", QualityTier.STANDARD, "Leviton Decora", "Single-pole or 3-way"),
                QualityTier.PREMIUM: PricePoint(35.00, "unit", QualityTier.PREMIUM, "Lutron Caseta", "Smart dimmer, app control"),
                QualityTier.LUXURY: PricePoint(120.00, "unit", QualityTier.LUXURY, "Lutron RA3", "Whole-home smart, keypads"),
            },
            labor_rate_per_unit=20.00,
            labor_unit="unit",
            category="electrical"
        ),
        "electrical_light_fixture": MaterialPricing(
            material_type="electrical_light_fixture",
            display_name="Light Fixture",
            price_points={
                QualityTier.BUDGET: PricePoint(50.00, "unit", QualityTier.BUDGET, "Hampton Bay", "Basic flush mount, LED"),
                QualityTier.STANDARD: PricePoint(150.00, "unit", QualityTier.STANDARD, "Progress Lighting, Kichler", "Semi-flush, dimmable LED"),
                QualityTier.PREMIUM: PricePoint(400.00, "unit", QualityTier.PREMIUM, "Visual Comfort, Hinkley", "Designer pendant/semi-flush"),
                QualityTier.LUXURY: PricePoint(1200.00, "unit", QualityTier.LUXURY, "Kelly Wearstler, Apparatus", "Statement fixture, custom"),
            },
            labor_rate_per_unit=150.00,
            labor_unit="unit",
            category="electrical"
        ),
        "electrical_wire_run": MaterialPricing(
            material_type="electrical_wire_run",
            display_name="Electrical Wire (NM Cable)",
            price_points={
                QualityTier.BUDGET: PricePoint(0.35, "linear ft", QualityTier.BUDGET, "Southwire", "14/2 NM-B, 15A circuits"),
                QualityTier.STANDARD: PricePoint(0.55, "linear ft", QualityTier.STANDARD, "Southwire", "12/2 NM-B, 20A circuits"),
                QualityTier.PREMIUM: PricePoint(1.50, "linear ft", QualityTier.PREMIUM, "Southwire in conduit", "12/2 in EMT conduit"),
                QualityTier.LUXURY: PricePoint(3.00, "linear ft", QualityTier.LUXURY, "MC cable", "Armored cable (MC/BX)"),
            },
            labor_rate_per_unit=2.50,
            labor_unit="linear ft",
            category="electrical"
        ),
        "electrical_breaker_panel": MaterialPricing(
            material_type="electrical_breaker_panel",
            display_name="Breaker Panel",
            price_points={
                QualityTier.BUDGET: PricePoint(400.00, "unit", QualityTier.BUDGET, "Square D QO", "100A, 20-space loadcenter"),
                QualityTier.STANDARD: PricePoint(800.00, "unit", QualityTier.STANDARD, "Leviton, Square D", "200A, 40-space panel"),
                QualityTier.PREMIUM: PricePoint(1500.00, "unit", QualityTier.PREMIUM, "Siemens, Eaton", "200A smart-ready, AFCI"),
                QualityTier.LUXURY: PricePoint(3500.00, "unit", QualityTier.LUXURY, "Siemens, custom", "200A + whole-home surge + monitoring"),
            },
            labor_rate_per_unit=1500.00,
            labor_unit="unit",
            category="electrical"
        ),

        # ==================== PLUMBING ====================
        "plumbing_supply_line": MaterialPricing(
            material_type="plumbing_supply_line",
            display_name="Supply Line Rough-in",
            price_points={
                QualityTier.BUDGET: PricePoint(75.00, "unit", QualityTier.BUDGET, "PEX A (Uponor)", "PEX A supply rough-in per fixture"),
                QualityTier.STANDARD: PricePoint(120.00, "unit", QualityTier.STANDARD, "PEX A (Uponor)", "PEX A with manifold per fixture"),
                QualityTier.PREMIUM: PricePoint(200.00, "unit", QualityTier.PREMIUM, "Copper L-type", "Copper supply per fixture"),
                QualityTier.LUXURY: PricePoint(350.00, "unit", QualityTier.LUXURY, "Type K copper", "Custom copper/brass per fixture"),
            },
            labor_rate_per_unit=200.00,
            labor_unit="unit",
            category="plumbing"
        ),
        "plumbing_drain_line": MaterialPricing(
            material_type="plumbing_drain_line",
            display_name="Drain Line Rough-in",
            price_points={
                QualityTier.BUDGET: PricePoint(60.00, "unit", QualityTier.BUDGET, "ABS pipe", "ABS DWV drain per fixture"),
                QualityTier.STANDARD: PricePoint(100.00, "unit", QualityTier.STANDARD, "PVC DWV", "PVC schedule 40 DWV per fixture"),
                QualityTier.PREMIUM: PricePoint(175.00, "unit", QualityTier.PREMIUM, "Cast iron DWV", "CI riser per fixture"),
                QualityTier.LUXURY: PricePoint(300.00, "unit", QualityTier.LUXURY, "Cast iron", "Full cast iron DWV per fixture"),
            },
            labor_rate_per_unit=250.00,
            labor_unit="unit",
            category="plumbing"
        ),
        "plumbing_vent_stack": MaterialPricing(
            material_type="plumbing_vent_stack",
            display_name="Vent Stack",
            price_points={
                QualityTier.BUDGET: PricePoint(200.00, "unit", QualityTier.BUDGET, "PVC", "PVC vent stack per wet wall"),
                QualityTier.STANDARD: PricePoint(400.00, "unit", QualityTier.STANDARD, "PVC schedule 40", "PVC vent with AAV option"),
                QualityTier.PREMIUM: PricePoint(600.00, "unit", QualityTier.PREMIUM, "Cast iron", "Cast iron vent through roof"),
                QualityTier.LUXURY: PricePoint(1000.00, "unit", QualityTier.LUXURY, "Cast iron", "CI vent + custom flashing"),
            },
            labor_rate_per_unit=500.00,
            labor_unit="unit",
            category="plumbing"
        ),
        "plumbing_water_heater": MaterialPricing(
            material_type="plumbing_water_heater",
            display_name="Water Heater",
            price_points={
                QualityTier.BUDGET: PricePoint(600.00, "unit", QualityTier.BUDGET, "Rheem, AO Smith", "40-gal electric, 6yr"),
                QualityTier.STANDARD: PricePoint(900.00, "unit", QualityTier.STANDARD, "Bradford White, Rheem", "50-gal gas, 12yr"),
                QualityTier.PREMIUM: PricePoint(1500.00, "unit", QualityTier.PREMIUM, "Rinnai, Navien", "Tankless gas, on-demand"),
                QualityTier.LUXURY: PricePoint(3000.00, "unit", QualityTier.LUXURY, "Rinnai, Navien", "Tankless + recirculation pump"),
            },
            labor_rate_per_unit=600.00,
            labor_unit="unit",
            category="plumbing"
        ),
        "plumbing_shutoff_valve": MaterialPricing(
            material_type="plumbing_shutoff_valve",
            display_name="Shut-off Valve",
            price_points={
                QualityTier.BUDGET: PricePoint(15.00, "unit", QualityTier.BUDGET, "BrassCraft", "Ball valve, chrome"),
                QualityTier.STANDARD: PricePoint(25.00, "unit", QualityTier.STANDARD, "Watts, BrassCraft", "Angle stop, quarter-turn"),
                QualityTier.PREMIUM: PricePoint(45.00, "unit", QualityTier.PREMIUM, "Watts, Kohler", "Brass quarter-turn, brushed nickel"),
                QualityTier.LUXURY: PricePoint(85.00, "unit", QualityTier.LUXURY, "Kohler, custom", "Designer finish, smart valve option"),
            },
            labor_rate_per_unit=30.00,
            labor_unit="unit",
            category="plumbing"
        ),

        # ==================== APPLIANCES ====================
        "appliance_range": MaterialPricing(
            material_type="appliance_range",
            display_name="Range/Oven",
            price_points={
                QualityTier.BUDGET: PricePoint(500.00, "unit", QualityTier.BUDGET, "GE, Frigidaire", "30\" freestanding electric"),
                QualityTier.STANDARD: PricePoint(1200.00, "unit", QualityTier.STANDARD, "GE Profile, Samsung", "30\" slide-in gas"),
                QualityTier.PREMIUM: PricePoint(2500.00, "unit", QualityTier.PREMIUM, "Bosch, KitchenAid", "30\" convection, self-clean"),
                QualityTier.LUXURY: PricePoint(5000.00, "unit", QualityTier.LUXURY, "Wolf, Thermador", "36\" pro-style dual fuel"),
            },
            labor_rate_per_unit=150.00,
            labor_unit="unit",
            category="appliances"
        ),
        "appliance_dishwasher": MaterialPricing(
            material_type="appliance_dishwasher",
            display_name="Dishwasher",
            price_points={
                QualityTier.BUDGET: PricePoint(400.00, "unit", QualityTier.BUDGET, "GE, Frigidaire", "24\" built-in, 59 dBa"),
                QualityTier.STANDARD: PricePoint(700.00, "unit", QualityTier.STANDARD, "Bosch 300, Samsung", "24\", 46 dBa, stainless tub"),
                QualityTier.PREMIUM: PricePoint(1200.00, "unit", QualityTier.PREMIUM, "Bosch 800, Miele", "24\", 42 dBa, panel-ready option"),
                QualityTier.LUXURY: PricePoint(2000.00, "unit", QualityTier.LUXURY, "Miele, Gaggenau", "Panel-ready, 38 dBa, auto-open"),
            },
            labor_rate_per_unit=200.00,
            labor_unit="unit",
            category="appliances"
        ),
        "appliance_microwave_hood": MaterialPricing(
            material_type="appliance_microwave_hood",
            display_name="Microwave/Range Hood",
            price_points={
                QualityTier.BUDGET: PricePoint(200.00, "unit", QualityTier.BUDGET, "GE, Sharp", "OTR microwave, 300 CFM"),
                QualityTier.STANDARD: PricePoint(500.00, "unit", QualityTier.STANDARD, "Broan, GE Profile", "30\" wall hood, 400 CFM"),
                QualityTier.PREMIUM: PricePoint(900.00, "unit", QualityTier.PREMIUM, "Zephyr, Broan Elite", "30\" insert/wall, 600 CFM"),
                QualityTier.LUXURY: PricePoint(1500.00, "unit", QualityTier.LUXURY, "Miele, Best", "36\" pro wall hood, 900 CFM"),
            },
            labor_rate_per_unit=200.00,
            labor_unit="unit",
            category="appliances"
        ),
        "appliance_refrigerator": MaterialPricing(
            material_type="appliance_refrigerator",
            display_name="Refrigerator",
            price_points={
                QualityTier.BUDGET: PricePoint(800.00, "unit", QualityTier.BUDGET, "GE, Frigidaire", "25 cu ft French door"),
                QualityTier.STANDARD: PricePoint(1500.00, "unit", QualityTier.STANDARD, "Samsung, LG", "27 cu ft French door, ice maker"),
                QualityTier.PREMIUM: PricePoint(2500.00, "unit", QualityTier.PREMIUM, "KitchenAid, Bosch", "Counter-depth French door"),
                QualityTier.LUXURY: PricePoint(5000.00, "unit", QualityTier.LUXURY, "Sub-Zero, Thermador", "Built-in panel-ready, 48\""),
            },
            labor_rate_per_unit=100.00,
            labor_unit="unit",
            category="appliances"
        ),
        "appliance_washer": MaterialPricing(
            material_type="appliance_washer",
            display_name="Washer",
            price_points={
                QualityTier.BUDGET: PricePoint(500.00, "unit", QualityTier.BUDGET, "GE, Amana", "4.5 cu ft top load"),
                QualityTier.STANDARD: PricePoint(800.00, "unit", QualityTier.STANDARD, "Samsung, LG", "5.0 cu ft front load"),
                QualityTier.PREMIUM: PricePoint(1200.00, "unit", QualityTier.PREMIUM, "LG ThinQ, Samsung", "5.5 cu ft front load, steam"),
                QualityTier.LUXURY: PricePoint(2000.00, "unit", QualityTier.LUXURY, "Miele, Speed Queen", "W1 front load, commercial grade"),
            },
            labor_rate_per_unit=100.00,
            labor_unit="unit",
            category="appliances"
        ),
        "appliance_dryer": MaterialPricing(
            material_type="appliance_dryer",
            display_name="Dryer",
            price_points={
                QualityTier.BUDGET: PricePoint(500.00, "unit", QualityTier.BUDGET, "GE, Amana", "7.2 cu ft electric dryer"),
                QualityTier.STANDARD: PricePoint(800.00, "unit", QualityTier.STANDARD, "Samsung, LG", "7.4 cu ft electric, sensor dry"),
                QualityTier.PREMIUM: PricePoint(1200.00, "unit", QualityTier.PREMIUM, "LG ThinQ, Samsung", "7.8 cu ft steam dryer"),
                QualityTier.LUXURY: PricePoint(2000.00, "unit", QualityTier.LUXURY, "Miele, Speed Queen", "T1 heat-pump, commercial grade"),
            },
            labor_rate_per_unit=100.00,
            labor_unit="unit",
            category="appliances"
        ),

        # ==================== DEMO/REMOVAL (labor-only; shown via remodel mode toggle) ====================
        "demo_cabinet_removal": MaterialPricing(
            material_type="demo_cabinet_removal",
            display_name="Cabinet Removal",
            price_points={
                QualityTier.BUDGET: PricePoint(40.00, "linear ft", QualityTier.BUDGET, "", "Rough removal, no salvage"),
                QualityTier.STANDARD: PricePoint(50.00, "linear ft", QualityTier.STANDARD, "", "Standard removal + haul"),
                QualityTier.PREMIUM: PricePoint(60.00, "linear ft", QualityTier.PREMIUM, "", "Careful removal, salvage hardware"),
                QualityTier.LUXURY: PricePoint(75.00, "linear ft", QualityTier.LUXURY, "", "Full salvage + recycling program"),
            },
            labor_rate_per_unit=0.00,
            labor_unit="linear ft",
            category="demo"
        ),
        "demo_flooring_removal": MaterialPricing(
            material_type="demo_flooring_removal",
            display_name="Flooring Removal",
            price_points={
                QualityTier.BUDGET: PricePoint(2.00, "sq ft", QualityTier.BUDGET, "", "Basic scrape and demo"),
                QualityTier.STANDARD: PricePoint(3.00, "sq ft", QualityTier.STANDARD, "", "Standard removal + haul"),
                QualityTier.PREMIUM: PricePoint(3.50, "sq ft", QualityTier.PREMIUM, "", "Careful removal, subfloor prep"),
                QualityTier.LUXURY: PricePoint(4.00, "sq ft", QualityTier.LUXURY, "", "Full prep + subfloor patch"),
            },
            labor_rate_per_unit=0.00,
            labor_unit="sq ft",
            category="demo"
        ),
        "demo_drywall_removal": MaterialPricing(
            material_type="demo_drywall_removal",
            display_name="Drywall Removal",
            price_points={
                QualityTier.BUDGET: PricePoint(1.50, "sq ft", QualityTier.BUDGET, "", "Tear-out, minimal dust control"),
                QualityTier.STANDARD: PricePoint(2.25, "sq ft", QualityTier.STANDARD, "", "Standard demo + plastic barrier"),
                QualityTier.PREMIUM: PricePoint(2.75, "sq ft", QualityTier.PREMIUM, "", "Dust-controlled, framing protected"),
                QualityTier.LUXURY: PricePoint(3.00, "sq ft", QualityTier.LUXURY, "", "Full containment + air scrubber"),
            },
            labor_rate_per_unit=0.00,
            labor_unit="sq ft",
            category="demo"
        ),
        "demo_fixture_removal": MaterialPricing(
            material_type="demo_fixture_removal",
            display_name="Fixture Removal",
            price_points={
                QualityTier.BUDGET: PricePoint(100.00, "unit", QualityTier.BUDGET, "", "Disconnect and remove per fixture"),
                QualityTier.STANDARD: PricePoint(200.00, "unit", QualityTier.STANDARD, "", "Remove + cap supply/drain"),
                QualityTier.PREMIUM: PricePoint(250.00, "unit", QualityTier.PREMIUM, "", "Remove + cap + patch wall"),
                QualityTier.LUXURY: PricePoint(300.00, "unit", QualityTier.LUXURY, "", "White-glove removal + salvage"),
            },
            labor_rate_per_unit=0.00,
            labor_unit="unit",
            category="demo"
        ),
        "demo_haul_away": MaterialPricing(
            material_type="demo_haul_away",
            display_name="Haul-away / Dumpster",
            price_points={
                QualityTier.BUDGET: PricePoint(500.00, "unit", QualityTier.BUDGET, "", "10-yd dumpster, small project"),
                QualityTier.STANDARD: PricePoint(800.00, "unit", QualityTier.STANDARD, "", "15-yd dumpster, mid project"),
                QualityTier.PREMIUM: PricePoint(1200.00, "unit", QualityTier.PREMIUM, "", "20-yd dumpster, full remodel"),
                QualityTier.LUXURY: PricePoint(1500.00, "unit", QualityTier.LUXURY, "", "20-yd + junk hauler, sorted recycling"),
            },
            labor_rate_per_unit=0.00,
            labor_unit="unit",
            category="demo"
        ),
    }
    
    # Regional price adjustments (multipliers)
    REGIONAL_ADJUSTMENTS: Dict[Region, float] = {
        Region.US_NATIONAL: 1.00,
        Region.US_NORTHEAST: 1.25,  # Higher costs (NYC, Boston)
        Region.US_SOUTHEAST: 0.90,  # Lower costs
        Region.US_MIDWEST: 0.95,
        Region.US_SOUTHWEST: 1.00,
        Region.US_WEST: 1.20,  # Higher costs (CA, WA)
    }
    
    @classmethod
    def get_pricing(cls, material_type: str) -> Optional[MaterialPricing]:
        """Get pricing information for a material type."""
        return cls.PRICING_DATA.get(material_type)
    
    @classmethod
    def get_regional_multiplier(cls, region: Region) -> float:
        """Get the price adjustment multiplier for a region."""
        return cls.REGIONAL_ADJUSTMENTS.get(region, 1.0)
    
    @classmethod
    def get_materials_by_category(cls, category: str) -> Dict[str, MaterialPricing]:
        """Get all materials in a specific category."""
        return {k: v for k, v in cls.PRICING_DATA.items() if v.category == category}
    
    @classmethod
    def get_kitchen_materials(cls) -> Dict[str, MaterialPricing]:
        """Get all kitchen-specific materials."""
        return cls.get_materials_by_category("kitchen")
    
    @classmethod
    def get_bathroom_materials(cls) -> Dict[str, MaterialPricing]:
        """Get all bathroom-specific materials."""
        return cls.get_materials_by_category("bathroom")


class RoomTypeDetector:
    """Detect room type from room name."""
    
    KITCHEN_KEYWORDS = ['kitchen', 'kitchenette', 'galley']
    BATHROOM_KEYWORDS = ['bathroom', 'bath', 'restroom', 'powder room', 'half bath', 
                         'full bath', 'master bath', 'ensuite', 'wc', 'lavatory']
    BEDROOM_KEYWORDS = ['bedroom', 'master bedroom', 'guest room', 'nursery']
    LIVING_KEYWORDS = ['living room', 'living area', 'family room', 'great room', 
                       'sitting room', 'den', 'lounge']
    DINING_KEYWORDS = ['dining room', 'dining area', 'breakfast nook', 'eat-in']
    
    @classmethod
    def detect(cls, room_name: str) -> RoomType:
        """Detect room type from room name."""
        name_lower = room_name.lower().strip()
        
        for keyword in cls.KITCHEN_KEYWORDS:
            if keyword in name_lower:
                return RoomType.KITCHEN
        
        for keyword in cls.BATHROOM_KEYWORDS:
            if keyword in name_lower:
                return RoomType.BATHROOM
        
        for keyword in cls.BEDROOM_KEYWORDS:
            if keyword in name_lower:
                return RoomType.BEDROOM
        
        for keyword in cls.LIVING_KEYWORDS:
            if keyword in name_lower:
                return RoomType.LIVING_ROOM
        
        for keyword in cls.DINING_KEYWORDS:
            if keyword in name_lower:
                return RoomType.DINING_ROOM
        
        return RoomType.OTHER


class CostEstimator:
    """
    Calculate cost estimates based on material quantities and pricing.
    """
    
    def __init__(
        self,
        quality_tier: QualityTier = QualityTier.STANDARD,
        region: Region = Region.US_NATIONAL,
        include_labor: bool = True,
        contingency_percent: float = 0.10,
        labor_availability: LaborAvailability = LaborAvailability.AVERAGE
    ):
        """
        Initialize the cost estimator.
        
        Args:
            quality_tier: Default quality tier for materials
            region: Geographic region for pricing
            include_labor: Whether to include labor costs
            contingency_percent: Contingency percentage (0.10 = 10%)
            labor_availability: Local labor market availability (affects labor costs)
        """
        self.quality_tier = quality_tier
        self.region = region
        self.include_labor = include_labor
        self.contingency_percent = contingency_percent
        self.labor_availability = labor_availability
        self.regional_multiplier = PricingDatabase.get_regional_multiplier(region)
        self.labor_availability_multiplier = LABOR_AVAILABILITY_MULTIPLIERS.get(labor_availability, 1.0)
    
    def estimate_material(
        self,
        material_key: str,
        quantity: MaterialQuantity,
        quality_tier: QualityTier = None
    ) -> Optional[CostEstimate]:
        """
        Calculate cost estimate for a single material.
        
        Args:
            material_key: Key for the material (e.g., 'flooring_hardwood')
            quantity: MaterialQuantity from the calculator
            quality_tier: Override quality tier (uses default if None)
        
        Returns:
            CostEstimate or None if pricing not available
        """
        tier = quality_tier or self.quality_tier
        pricing = PricingDatabase.get_pricing(material_key)
        
        if not pricing or tier not in pricing.price_points:
            return None
        
        price_point = pricing.price_points[tier]
        
        # Calculate material cost
        material_cost = quantity.units_needed * price_point.price_per_unit * self.regional_multiplier
        
        # Calculate labor cost based on area/length
        labor_cost = 0.0
        if self.include_labor:
            # Convert quantity to labor units (sq ft or linear ft)
            if pricing.labor_unit == "sq ft":
                labor_area = quantity.quantity * 10.7639  # m² to sq ft
            elif pricing.labor_unit == "linear ft":
                labor_area = quantity.quantity * 3.28084  # m to ft
            else:  # unit-based (fixtures)
                labor_area = quantity.units_needed
            
            labor_cost = labor_area * pricing.labor_rate_per_unit * self.regional_multiplier * self.labor_availability_multiplier
        
        total_cost = material_cost + labor_cost
        
        return CostEstimate(
            material_type=material_key,
            display_name=pricing.display_name,
            quality_tier=tier,
            units_needed=quantity.units_needed,
            unit=quantity.unit,
            material_cost=round(material_cost, 2),
            labor_cost=round(labor_cost, 2),
            total_cost=round(total_cost, 2),
            price_per_unit=price_point.price_per_unit,
            brand_example=price_point.brand_example,
            notes=price_point.notes,
            category=pricing.category
        )
    
    def estimate_fixture(
        self,
        material_key: str,
        count: int = 1,
        quality_tier: QualityTier = None
    ) -> Optional[CostEstimate]:
        """
        Calculate cost estimate for a fixture (unit-based item).
        
        Args:
            material_key: Key for the fixture (e.g., 'toilet', 'kitchen_sink')
            count: Number of fixtures
            quality_tier: Override quality tier (uses default if None)
        
        Returns:
            CostEstimate or None if pricing not available
        """
        tier = quality_tier or self.quality_tier
        pricing = PricingDatabase.get_pricing(material_key)
        
        if not pricing or tier not in pricing.price_points:
            return None
        
        price_point = pricing.price_points[tier]
        
        # Calculate material cost
        material_cost = count * price_point.price_per_unit * self.regional_multiplier
        
        # Calculate labor cost
        labor_cost = 0.0
        if self.include_labor:
            labor_cost = count * pricing.labor_rate_per_unit * self.regional_multiplier * self.labor_availability_multiplier
        
        total_cost = material_cost + labor_cost
        
        # Create a simple MaterialQuantity for fixtures
        quantity = MaterialQuantity(
            material_type=material_key,
            quantity=count,
            unit="unit",
            units_needed=count,
            waste_factor=1.0
        )
        
        return CostEstimate(
            material_type=material_key,
            display_name=pricing.display_name,
            quality_tier=tier,
            units_needed=count,
            unit="unit",
            material_cost=round(material_cost, 2),
            labor_cost=round(labor_cost, 2),
            total_cost=round(total_cost, 2),
            price_per_unit=price_point.price_per_unit,
            brand_example=price_point.brand_example,
            notes=price_point.notes,
            category=pricing.category
        )
    
    def estimate_project(
        self,
        project_name: str,
        material_totals: Dict[str, MaterialQuantity],
        selected_materials: Dict[str, QualityTier] = None,
        include_mep: bool = False
    ) -> ProjectEstimate:
        """
        Calculate complete cost estimate for a project.
        
        Args:
            project_name: Name for the project
            material_totals: Dictionary of material quantities from MaterialCalculator
            selected_materials: Optional dict mapping material_key to quality tier
        
        Returns:
            ProjectEstimate with all costs
        """
        estimates = []
        demo_estimates = []
        subtotal_materials = 0.0
        subtotal_labor = 0.0

        for material_key, quantity in material_totals.items():
            # Get quality tier for this material
            tier = self.quality_tier
            if selected_materials and material_key in selected_materials:
                tier = selected_materials[material_key]

            estimate = self.estimate_material(material_key, quantity, tier)
            if estimate:
                if estimate.category == "demo":
                    demo_estimates.append(estimate)
                else:
                    estimates.append(estimate)
                    subtotal_materials += estimate.material_cost
                    subtotal_labor += estimate.labor_cost

        # Calculate contingency (excludes demo costs)
        subtotal = subtotal_materials + subtotal_labor
        contingency_amount = subtotal * self.contingency_percent
        total_estimate = subtotal + contingency_amount

        mep_breakdown = None
        if include_mep:
            structural_shell_cost = subtotal_materials + subtotal_labor
            mep_estimate = structural_shell_cost * MEP_MULTIPLIER
            total_estimate += mep_estimate
            mep_breakdown = {
                "mep_estimate": round(mep_estimate, 2),
                "mep_multiplier": MEP_MULTIPLIER,
                "disclaimer": "Rough MEP estimate only (±30%). Actual costs vary significantly by complexity, local codes, and existing infrastructure.",
                "includes": ["HVAC rough-in", "Electrical rough-in", "Plumbing rough-in"],
            }

        # Build demo_breakdown (always included if demo items exist; displayed via frontend toggle)
        demo_breakdown = None
        if demo_estimates:
            demo_subtotal = sum(e.total_cost for e in demo_estimates)
            demo_breakdown = {
                "line_items": [
                    {
                        "material_type": e.material_type,
                        "display_name": e.display_name,
                        "units_needed": e.units_needed,
                        "unit": e.unit,
                        "material_cost": e.material_cost,
                        "labor_cost": e.labor_cost,
                        "total_cost": e.total_cost,
                        "price_per_unit": e.price_per_unit,
                    }
                    for e in demo_estimates
                ],
                "subtotal": round(demo_subtotal, 2),
                "disclaimer": "Demo/removal costs are labor only. Actual costs vary by accessibility, material condition, and local disposal fees.",
            }

        return ProjectEstimate(
            project_name=project_name,
            timestamp=datetime.now().isoformat(),
            region=self.region,
            estimates=estimates,
            subtotal_materials=round(subtotal_materials, 2),
            subtotal_labor=round(subtotal_labor, 2),
            contingency_percent=self.contingency_percent,
            contingency_amount=round(contingency_amount, 2),
            total_estimate=round(total_estimate, 2),
            mep_breakdown=mep_breakdown,
            demo_breakdown=demo_breakdown,
        )


def compare_quality_tiers(
    material_totals: Dict[str, MaterialQuantity],
    region: Region = Region.US_NATIONAL,
    include_labor: bool = True,
    contingency_percent: float = 0.10,
    labor_availability: LaborAvailability = LaborAvailability.AVERAGE
) -> Dict[str, float]:
    """
    Compare total project costs across all quality tiers.
    
    Args:
        material_totals: Dictionary of material quantities
        region: Geographic region for pricing
        include_labor: Whether to include labor costs
        contingency_percent: Contingency percentage
        labor_availability: Local labor market availability
    
    Returns:
        Dictionary mapping tier name to total estimate
    """
    results = {}
    
    for tier in QualityTier:
        estimator = CostEstimator(
            quality_tier=tier,
            region=region,
            include_labor=include_labor,
            contingency_percent=contingency_percent,
            labor_availability=labor_availability
        )
        estimate = estimator.estimate_project("Comparison", material_totals)
        results[tier.value] = estimate.total_estimate
    
    return results


def format_cost_report(estimate: ProjectEstimate) -> str:
    """Render a readable plain-text cost summary for CLI/tests."""
    lines = [
        f"Project: {estimate.project_name}",
        f"Region: {estimate.region.value if hasattr(estimate.region, 'value') else estimate.region}",
        "",
        "Cost Breakdown:",
    ]

    for item in estimate.estimates:
        lines.extend([
            f"- {item.display_name}:",
            f"  Material: ${item.material_cost:,.2f}",
            f"  Labor: ${item.labor_cost:,.2f}",
            f"  Total: ${item.total_cost:,.2f}",
        ])

    lines.extend([
        "",
        f"Materials subtotal: ${estimate.subtotal_materials:,.2f}",
        f"Labor subtotal: ${estimate.subtotal_labor:,.2f}",
        f"Contingency ({estimate.contingency_percent:.0%}): ${estimate.contingency_amount:,.2f}",
        f"Grand total: ${estimate.total_estimate:,.2f}",
    ])

    return "\n".join(lines)
