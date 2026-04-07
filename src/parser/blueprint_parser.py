"""
Blueprint Parser - Core module for extracting room data from floor plans using AI Vision.

Supports multiple AI providers: OpenAI GPT-4o and Anthropic Claude 3.5 Sonnet.
This is the heart of Takeoff.ai's Phase 1 Proof of Concept.
"""

import os
import json
import base64
import tempfile
import logging
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass, asdict
from openai import OpenAI
from dotenv import load_dotenv

from preprocessing.image_enhancer import enhance_image_for_vision

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class Room:
    """Represents a room extracted from a blueprint."""
    name: str
    width: Optional[str] = None
    length: Optional[str] = None
    area: Optional[str] = None
    unit: str = "unknown"  # "imperial", "metric", or "unknown"
    confidence: str = "medium"  # "high", "medium", "low"


@dataclass
class BlueprintAnalysis:
    """Complete analysis result from a blueprint."""
    filename: str
    rooms: list[Room]
    total_area: Optional[str] = None
    unit_system: str = "unknown"
    warnings: list[str] = None
    raw_response: str = None
    model_used: str = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "filename": self.filename,
            "rooms": [asdict(r) for r in self.rooms],
            "total_area": self.total_area,
            "unit_system": self.unit_system,
            "warnings": self.warnings,
            "model_used": self.model_used
        }
    
    def to_json(self, indent=2):
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class BlueprintParser:
    """
    Parses blueprint images using AI Vision to extract room information.
    Supports both OpenAI GPT-4o and Anthropic Claude 3.5 Sonnet.
    """
    
    # The prompt that instructs AI Vision how to analyze blueprints
    ANALYSIS_PROMPT = """You are an expert construction estimator analyzing a residential floor plan. Extract room dimensions using a strict hierarchy: read labels first, use scale second, estimate proportionally only as a last resort.

STEP 1 — FIND SCALE INDICATOR (do this before anything else):
Look for any of the following anywhere on the image:
- A labeled scale bar (e.g., a line labeled "0  5  10  20 ft" or "0  2  4m")
- A scale ratio (e.g., "Scale 1:100", "1/4\" = 1'-0\"", "1:50")
- A north arrow with scale notation
If found: record scale_found=true, scale_text="<exact text>"
If not found: scale_found=false

STEP 2 — DETECT UNIT SYSTEM:
- METRIC: measurements use m, cm, mm, or m²
- IMPERIAL: measurements use ft, ', ", sq ft
- Ambiguous: default to metric when values look like 2–8 range; imperial when 10–25 range

STEP 3 — EXTRACT LABELED DIMENSIONS (highest priority):
For every room with visible dimension annotations:
- Read the EXACT numbers from dimension lines, room labels (e.g., "BEDROOM 12×14"), or area stamps (e.g., "14.8 m²")
- confidence = "high"
- Do NOT modify, round, or convert the values

STEP 4 — SCALE-ANCHORED MEASUREMENTS (rooms missing labels, scale available):
Only if scale_found=true AND the room has no explicit dimension labels:
- Visually estimate the room's footprint relative to the scale bar or a labeled room
- Calculate the real-world size from that proportion
- confidence = "medium"
- Add warning: "Area derived from scale measurement, not labeled"

STEP 5 — PROPORTION-ONLY ESTIMATE (last resort: no scale, no label):
Only if scale_found=false AND the room has no explicit dimension labels:
a) Identify the LARGEST room in the plan visually. Assign it an anchor area:
   - Metric plans: anchor = 25 m² for the largest room
   - Imperial plans: anchor = 270 sq ft for the largest room
b) Compare every other room's visual footprint to the largest room. Assign areas proportionally.
   Example: if a bedroom looks roughly 60% as large as the living room, its area = 0.6 × 25 = 15 m²
c) confidence = "low" for ALL rooms estimated this way
d) Add warning: "Area estimated by visual proportion only — no scale or labels found"
- NEVER use NAHB industry averages or per-room-type lookup tables

CRITICAL RULES:
- ALWAYS list every room you can identify in the floor plan. Never omit a room.
- ALWAYS provide a numeric area estimate. area=null is not allowed — use proportional estimation if nothing else.
- "medium" confidence = scale-derived only. Never assign "medium" without a scale reference.
- "low" confidence = proportion estimate. Every room gets a proportional estimate if no better data.
- Keep all values in ORIGINAL units — no conversion.
- Include halls, closets, balconies if labeled or scalable.

Return ONLY this JSON:
{
    "scale_found": true or false,
    "scale_text": "exact scale text or null",
    "rooms": [
        {
            "name": "Room name",
            "width": "number only or null",
            "length": "number only or null",
            "area": "number only",
            "confidence": "high | medium | low"
        }
    ],
    "total_area": "sum of room areas",
    "unit_system": "imperial or metric",
    "warnings": ["per-room or global warnings"]
}

Return ONLY the JSON object, no additional text."""

    OCR_PASS_PROMPT = """Extract all visible text and numbers from this floor plan. Focus especially on scale indicators and dimension labels.

Return ONLY this JSON (no extra text):
{
  "scale_indicator": {
    "found": true or false,
    "raw_text": "exact text of scale bar/ratio/notation or null",
    "type": "bar | ratio | notation | null",
    "value": "parsed scale value e.g. 1:100 or 1/4inch=1ft or null"
  },
  "unit_system": "imperial or metric or unknown",
  "room_labels": [
    {"name": "Room Name", "dimensions_text": "e.g. 14x12 or 4.5m x 3.2m or null", "area_text": "e.g. 14.8 m\u00b2 or null"}
  ],
  "dimension_annotations": ["list of all raw dimension strings found anywhere on the plan"],
  "other_text": ["any other text labels not captured above"]
}"""

    TWO_PASS_ANALYSIS_PROMPT_TEMPLATE = """You are analyzing a floor plan. The OCR pass below extracted text, labels, and scale data. Use it to extract accurate room dimensions.

OCR PASS DATA:
{ocr_context}

INSTRUCTIONS:
1. Check OCR data for scale_indicator. If found=true, use the scale to compute room dimensions.
2. Match room_labels and dimension_annotations to rooms visible in the image.
3. Confidence rules — follow strictly:
   - "high": dimension explicitly labeled on the plan (read from OCR or image)
   - "medium": no explicit label but scale was found — measure proportionally using scale
   - "low": no scale, no label — proportion estimate relative to a known-size room only
   - NEVER assign "medium" without a scale reference. Use "low" if uncertain.
4. Do NOT use NAHB averages or per-room-type lookup tables. Only use what is visible in the image or in OCR data.
5. ALWAYS include every room you can identify. ALWAYS provide a numeric area — use proportional estimation (largest room anchor = 25 m² or 270 sq ft) if no other data. area=null is not allowed.

Return ONLY this JSON:
{{
    "scale_found": true or false,
    "scale_text": "exact scale text or null",
    "rooms": [
        {{
            "name": "Room name",
            "width": "number only or null",
            "length": "number only or null",
            "area": "number only or null",
            "confidence": "high | medium | low"
        }}
    ],
    "total_area": "sum of non-null room areas",
    "unit_system": "imperial or metric",
    "warnings": ["per-room or global warnings"]
}}

Return ONLY the JSON object, no additional text."""

    # Supported AI providers
    PROVIDER_OPENAI = "openai"
    PROVIDER_CLAUDE = "claude"
    
    def __init__(self, api_key: Optional[str] = None, model: str = None, provider: str = None):
        """
        Initialize the parser.
        
        Args:
            api_key: API key for the provider. Defaults to env var based on provider.
            model: Model to use. Defaults to env var or provider's best model.
            provider: AI provider to use ('openai' or 'claude'). Defaults to AI_PROVIDER env var or 'openai'.
        """
        # Determine provider
        self.provider = provider or os.getenv("AI_PROVIDER", self.PROVIDER_OPENAI).lower()
        
        if self.provider == self.PROVIDER_CLAUDE:
            self._init_claude(api_key, model)
        else:
            self._init_openai(api_key, model)
    
    def _init_openai(self, api_key: Optional[str], model: Optional[str]):
        """Initialize OpenAI client."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.client = OpenAI(api_key=self.api_key)
    
    def _init_claude(self, api_key: Optional[str], model: Optional[str]):
        """Initialize Anthropic Claude client."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable.")
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def _encode_image(self, image_path: str) -> tuple[str, str]:
        """
        Encode an image file to base64.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (base64_data, media_type)
        """
        path = Path(image_path)
        
        # Determine media type
        suffix = path.suffix.lower()
        media_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        media_type = media_types.get(suffix, 'image/png')
        
        # Read and encode
        with open(path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        return image_data, media_type
    
    def _call_openai(self, image_data: str, media_type: str, prompt: str) -> str:
        """Call OpenAI Vision API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0
        )
        return response.choices[0].message.content
    
    def _call_claude(self, image_data: str, media_type: str, prompt: str) -> str:
        """Call Anthropic Claude Vision API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        return response.content[0].text

    def _call_model(self, image_data: str, media_type: str, prompt: str) -> str:
        if self.provider == self.PROVIDER_CLAUDE:
            return self._call_claude(image_data, media_type, prompt)
        return self._call_openai(image_data, media_type, prompt)

    def _parse_json_response(self, raw_response: str) -> dict:
        json_str = raw_response
        if "```json" in json_str:
            json_str = json_str.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in json_str:
            json_str = json_str.split("```", 1)[1].split("```", 1)[0]
        return json.loads(json_str.strip())
    
    def parse(self, image_source: Union[str, bytes], filename: str = "blueprint", two_pass: bool = False) -> BlueprintAnalysis:
        """
        Parse a blueprint image and extract room information.
        
        Args:
            image_source: Either a file path (str) or raw image bytes
            filename: Name to use in the result (defaults to "blueprint")
            
        Returns:
            BlueprintAnalysis object with extracted room data
        """
        temp_file_path = None
        
        try:
            image_path_for_processing = None
            if isinstance(image_source, bytes):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                    tmp.write(image_source)
                    temp_file_path = tmp.name
                image_path_for_processing = temp_file_path
            else:
                image_path_for_processing = str(image_source)
                filename = Path(image_source).name

            enhancement = enhance_image_for_vision(image_path_for_processing)
            image_data, media_type = enhancement.image_base64, enhancement.media_type
            logger.info(
                "Blueprint preprocessing for %s | enhanced=%s | operations=%s | debug=%s",
                filename,
                enhancement.enhanced,
                ", ".join(enhancement.operations),
                enhancement.debug_path,
            )

            raw_response = None
            try:
                if two_pass:
                    ocr_raw_response = self._call_model(image_data, media_type, self.OCR_PASS_PROMPT)
                    ocr_data = self._parse_json_response(ocr_raw_response)
                    ocr_context = json.dumps(ocr_data, indent=2)
                    raw_response = self._call_model(
                        image_data,
                        media_type,
                        self.TWO_PASS_ANALYSIS_PROMPT_TEMPLATE.format(ocr_context=ocr_context),
                    )
                else:
                    raw_response = self._call_model(image_data, media_type, self.ANALYSIS_PROMPT)

                data = self._parse_json_response(raw_response)
            except json.JSONDecodeError as e:
                warning = f"Failed to parse AI response: {str(e)}"
                if two_pass:
                    warning += " (two-pass mode)"
                return BlueprintAnalysis(
                    filename=filename,
                    rooms=[],
                    warnings=[warning],
                    raw_response=raw_response,
                    model_used=f"{self.provider}:{self.model}"
                )
            
            # Convert to Room objects
            rooms = []
            for room_data in data.get("rooms", []):
                room = Room(
                    name=room_data.get("name", "Unknown"),
                    width=room_data.get("width"),
                    length=room_data.get("length"),
                    area=room_data.get("area"),
                    unit=data.get("unit_system", "unknown"),
                    confidence=room_data.get("confidence", "medium")
                )
                rooms.append(room)
            
            # Create the analysis result
            warnings = list(data.get("warnings", []))
            warnings.append(
                f"Image enhancement applied: {enhancement.enhanced} ({', '.join(enhancement.operations)})"
            )
            if two_pass:
                warnings.append("Two-pass extraction mode enabled")

            analysis = BlueprintAnalysis(
                filename=filename,
                rooms=rooms,
                total_area=data.get("total_area"),
                unit_system=data.get("unit_system", "unknown"),
                warnings=warnings,
                raw_response=raw_response,
                model_used=f"{self.provider}:{self.model}"
            )
            
            return analysis
            
        finally:
            # Clean up temp file if we created one
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def parse_batch(self, image_paths: list[str], verbose: bool = True) -> list[BlueprintAnalysis]:
        """
        Parse multiple blueprint images.
        
        Args:
            image_paths: List of paths to blueprint images
            verbose: Whether to print progress
            
        Returns:
            List of BlueprintAnalysis objects
        """
        results = []
        for i, path in enumerate(image_paths):
            if verbose:
                print(f"Processing {i+1}/{len(image_paths)}: {path}")
            result = self.parse(path)
            results.append(result)
        return results
