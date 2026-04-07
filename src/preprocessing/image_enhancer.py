"""Conservative image preprocessing for blueprint vision extraction."""

from __future__ import annotations

import base64
import io
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageFilter, ImageOps

try:
    import cv2  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    cv2 = None

SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MIN_WIDTH = 1200
MAX_DESKEW_ANGLE = 15.0
DESKEW_SAMPLE_STEP = 1.0


@dataclass
class EnhancementResult:
    image_base64: str
    media_type: str
    enhanced: bool
    debug_path: str
    operations: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)



def _load_image(image_path: str | Path) -> Image.Image:
    path = Path(image_path)
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported image format: {path.suffix}")
    return Image.open(path).convert("RGB")



def _to_grayscale_array(image: Image.Image) -> np.ndarray:
    return np.asarray(image.convert("L"), dtype=np.uint8)



def _edge_strength(gray: np.ndarray) -> float:
    arr = gray.astype(np.float32)
    gx = np.abs(np.diff(arr, axis=1))
    gy = np.abs(np.diff(arr, axis=0))
    return float((gx.mean() + gy.mean()) / 2.0)



def _estimate_noise(gray: np.ndarray) -> float:
    blurred = np.asarray(Image.fromarray(gray).filter(ImageFilter.GaussianBlur(radius=1.2)), dtype=np.float32)
    residual = gray.astype(np.float32) - blurred
    return float(np.std(residual))



def _estimate_contrast(gray: np.ndarray) -> float:
    p5, p95 = np.percentile(gray, [5, 95])
    return float(p95 - p5)



def _score_rotation(gray: np.ndarray, angle: float) -> float:
    rotated = Image.fromarray(gray).rotate(angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=255)
    arr = np.asarray(rotated, dtype=np.float32)
    darkness = 255.0 - arr
    row_profile = darkness.mean(axis=1)
    if row_profile.size < 2:
        return 0.0
    return float(np.var(row_profile))



def _detect_skew_angle(gray: np.ndarray) -> float:
    best_angle = 0.0
    best_score = _score_rotation(gray, 0.0)
    for angle in np.arange(-MAX_DESKEW_ANGLE, MAX_DESKEW_ANGLE + DESKEW_SAMPLE_STEP, DESKEW_SAMPLE_STEP):
        score = _score_rotation(gray, float(angle))
        if score > best_score:
            best_score = score
            best_angle = float(angle)
    return best_angle



def _autocontrast_preserve_background(image: Image.Image, cutoff: float = 1.0) -> Image.Image:
    return ImageOps.autocontrast(image, cutoff=cutoff)



def _apply_clahe_rgb(image: Image.Image) -> Image.Image:
    if cv2 is None:
        return _autocontrast_preserve_background(image, cutoff=1.0)

    rgb = np.asarray(image)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    merged = cv2.merge((l2, a, b))
    out = cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)
    return Image.fromarray(out)



def _light_denoise(image: Image.Image) -> Image.Image:
    if cv2 is None:
        return image.filter(ImageFilter.GaussianBlur(radius=0.6))

    rgb = np.asarray(image)
    denoised = cv2.fastNlMeansDenoisingColored(rgb, None, 3, 3, 7, 21)
    return Image.fromarray(denoised)



def _images_mean_delta(a: Image.Image, b: Image.Image) -> float:
    arr_a = np.asarray(a.resize((512, int(max(1, a.height * 512 / a.width)))), dtype=np.float32)
    arr_b = np.asarray(b.resize((512, int(max(1, b.height * 512 / b.width)))), dtype=np.float32)
    h = min(arr_a.shape[0], arr_b.shape[0])
    w = min(arr_a.shape[1], arr_b.shape[1])
    arr_a = arr_a[:h, :w]
    arr_b = arr_b[:h, :w]
    return float(np.mean(np.abs(arr_a - arr_b)))



def _save_debug_image(image: Image.Image, source_path: str | Path) -> str:
    source = Path(source_path)
    root = Path(__file__).resolve().parents[2]
    out_dir = root / "validation" / "preprocessed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{source.stem}_enhanced.png"
    image.save(out_path, format="PNG")
    return str(out_path)



def enhance_image_for_vision(image_path: str | Path) -> EnhancementResult:
    source = Path(image_path)
    original = _load_image(source)
    working = original.copy()
    gray = _to_grayscale_array(original)

    contrast = _estimate_contrast(gray)
    edges = _edge_strength(gray)
    noise = _estimate_noise(gray)
    skew_angle = _detect_skew_angle(gray)

    metrics = {
        "contrast": round(contrast, 2),
        "edge_strength": round(edges, 2),
        "noise": round(noise, 2),
        "skew_angle": round(skew_angle, 2),
        "width": original.width,
        "height": original.height,
    }

    clean_image = (
        original.width >= MIN_WIDTH
        and contrast >= 150
        and edges >= 14
        and noise <= 12
        and abs(skew_angle) <= 0.8
    )

    operations: list[str] = []

    if working.width < MIN_WIDTH:
        scale = MIN_WIDTH / float(working.width)
        new_size = (MIN_WIDTH, int(round(working.height * scale)))
        working = working.resize(new_size, Image.Resampling.LANCZOS)
        operations.append(f"upscale:{new_size[0]}x{new_size[1]}")

    if not clean_image and abs(skew_angle) >= 0.8:
        working = working.rotate(-skew_angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=(255, 255, 255))
        operations.append(f"deskew:{round(skew_angle, 2)}deg")

    post_gray = _to_grayscale_array(working)
    post_contrast = _estimate_contrast(post_gray)
    post_noise = _estimate_noise(post_gray)

    if not clean_image and post_contrast < 165:
        working = _apply_clahe_rgb(working)
        operations.append("contrast")

    if not clean_image and post_noise > 14:
        working = _light_denoise(working)
        operations.append("denoise")

    if not clean_image:
        working = working.filter(ImageFilter.UnsharpMask(radius=1.2, percent=115, threshold=3))
        operations.append("sharpen")

    delta = _images_mean_delta(original, working)
    if clean_image and not operations:
        operations.append("quality-check-skip")
    elif delta < 0.75 and operations:
        operations = ["minimal-adjustment"] + operations

    debug_path = _save_debug_image(working, source)

    buffer = io.BytesIO()
    working.save(buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

    metrics["post_mean_delta"] = round(delta, 3)
    metrics["clean_image"] = clean_image

    return EnhancementResult(
        image_base64=encoded,
        media_type="image/png",
        enhanced=not clean_image or working.width != original.width or delta >= 0.75,
        debug_path=debug_path,
        operations=operations,
        metrics=metrics,
    )
