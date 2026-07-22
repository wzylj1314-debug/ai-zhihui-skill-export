#!/usr/bin/env python
"""Run PaddleOCR on DingTalk screenshots and cache normalized OCR JSON."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

os.environ.setdefault("FLAGS_use_onednn", "0")
os.environ.setdefault("FLAGS_enable_pir_api", "0")

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

# Tiling: PaddleOCR downscales any side over ~4000px, which both slows OCR and
# blurs small Chinese text on long chat screenshots. Tall images are sliced into
# overlapping vertical tiles that each stay under the limit, then merged.
EDGE_MARGIN = 10  # drop boxes physically clipped at a cut edge (px)
DEDUP_Y = 25      # same text within this vertical gap == an overlap duplicate (px)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cache_key(path: Path, params: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update(file_hash(path).encode("ascii"))
    digest.update(json.dumps(params, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return digest.hexdigest()


def flatten_box(box: Any) -> list[float]:
    if box is None:
        return []
    if hasattr(box, "tolist"):
        box = box.tolist()
    try:
        if len(box) == 0:
            return []
    except TypeError:
        return []
    if isinstance(box, (list, tuple)) and box and isinstance(box[0], (list, tuple)):
        xs = [float(point[0]) for point in box if len(point) >= 2]
        ys = [float(point[1]) for point in box if len(point) >= 2]
        return [min(xs), min(ys), max(xs), max(ys)] if xs and ys else []
    if isinstance(box, (list, tuple)) and len(box) >= 4:
        return [float(box[0]), float(box[1]), float(box[2]), float(box[3])]
    return []


def normalize_prediction(result: Any) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []

    if (
        isinstance(result, (list, tuple))
        and len(result) == 2
        and isinstance(result[1], (list, tuple))
        and result[1]
        and isinstance(result[1][0], str)
    ):
        text = result[1][0]
        score = result[1][1] if len(result[1]) > 1 else None
        return [{"text": str(text), "box": flatten_box(result[0]), "conf": score}]

    if isinstance(result, list):
        for item in result:
            lines.extend(normalize_prediction(item))
        return lines

    if isinstance(result, dict):
        texts = first_present(result, "rec_texts", "texts")
        scores = first_present(result, "rec_scores", "scores")
        boxes = first_present(result, "rec_boxes", "dt_polys", "boxes")
        if texts is None:
            texts = []
        if scores is None:
            scores = []
        if boxes is None:
            boxes = []
        for index, text in enumerate(texts):
            box = boxes[index] if index < len(boxes) else []
            score = scores[index] if index < len(scores) else None
            lines.append({"text": str(text), "box": flatten_box(box), "conf": score})
        return lines

    # PaddleOCR 2.x commonly returns [[box, (text, conf)], ...].
    if isinstance(result, tuple):
        return normalize_prediction(list(result))

    return lines


def first_present(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def build_ocr(model_profile: str) -> tuple[Any, str]:
    """Construct a single PaddleOCR instance, reused across all images and tiles."""
    with contextlib.redirect_stdout(sys.stderr):
        try:
            from paddleocr import PaddleOCR
        except Exception as exc:  # pragma: no cover - depends on local venv
            raise RuntimeError("PaddleOCR is not installed. Run pip install -r requirements.txt first.") from exc

        try:
            model_args: dict[str, Any] = {}
            if model_profile == "mobile":
                model_args = {
                    "text_detection_model_name": "PP-OCRv5_mobile_det",
                    "text_recognition_model_name": "PP-OCRv5_mobile_rec",
                }
            elif model_profile == "server":
                model_args = {
                    "text_detection_model_name": "PP-OCRv5_server_det",
                    "text_recognition_model_name": "PP-OCRv5_server_rec",
                }
            ocr = PaddleOCR(
                lang="ch",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                **model_args,
            )
            return ocr, "predict"
        except TypeError:
            ocr = PaddleOCR(lang="ch", use_angle_cls=True)
            return ocr, "ocr"


def ocr_source(ocr: Any, mode: str, source: Any) -> list[dict[str, Any]]:
    """Run OCR on a file path (str) or an ndarray crop and normalize the result."""
    with contextlib.redirect_stdout(sys.stderr):
        if mode == "predict":
            result = ocr.predict(source)
        else:
            result = ocr.ocr(source, cls=True)
    return normalize_prediction(result)


def imread_unicode(path: Path) -> Any:
    """cv2.imread fails on non-ASCII paths on Windows; decode via numpy instead."""
    import cv2
    import numpy as np

    try:
        data = np.fromfile(str(path), dtype=np.uint8)
        if data.size == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None


def resize_for_ocr(img: Any, max_width: int) -> tuple[Any, float]:
    if img is None or max_width <= 0:
        return img, 1.0
    height, width = img.shape[:2]
    if width <= max_width:
        return img, 1.0
    import cv2

    scale = max_width / float(width)
    resized_height = max(1, int(round(height * scale)))
    resized = cv2.resize(img, (max_width, resized_height), interpolation=cv2.INTER_AREA)
    return resized, scale


def normalize_text(text: str) -> str:
    return "".join(str(text).split())


def dedup_overlap(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate lines detected in the shared band of adjacent tiles."""
    kept: list[dict[str, Any]] = []
    for line in sorted(lines, key=lambda item: (item.get("box") or [0, 0, 0, 0])[1]):
        text = normalize_text(line.get("text", ""))
        y0 = (line.get("box") or [0, 0, 0, 0])[1]
        duplicate = None
        for other in kept:
            if normalize_text(other.get("text", "")) == text and abs((other.get("box") or [0, 0, 0, 0])[1] - y0) <= DEDUP_Y:
                duplicate = other
                break
        if duplicate is None:
            kept.append(line)
        elif (line.get("conf") or 0) > (duplicate.get("conf") or 0):
            duplicate.update(line)
    return kept


def run_paddle(
    ocr: Any,
    mode: str,
    image: Path,
    tile_height: int,
    tile_overlap: int,
    max_untiled_height: int,
    max_width: int,
) -> tuple[list[dict[str, Any]], int, dict[str, Any]]:
    img = imread_unicode(image)
    if img is not None:
        original_height, original_width = img.shape[:2]
        img, scale = resize_for_ocr(img, max_width)
        resized_height, resized_width = img.shape[:2]
    else:
        original_height = original_width = resized_height = resized_width = 0
        scale = 1.0

    meta = {
        "original_width": original_width,
        "original_height": original_height,
        "ocr_width": resized_width,
        "ocr_height": resized_height,
        "scale": scale,
    }

    # Short images (and any decode failure) keep the proven whole-image path.
    if img is None:
        lines = ocr_source(ocr, mode, str(image))
        lines.sort(key=lambda item: ((item.get("box") or [0, 0, 0, 0])[1], (item.get("box") or [0, 0, 0, 0])[0]))
        return lines, 1, meta

    if img.shape[0] <= max_untiled_height:
        source = img if scale != 1.0 else str(image)
        lines = ocr_source(ocr, mode, source)
        if scale != 1.0:
            for line in lines:
                box = line.get("box") or []
                if len(box) == 4:
                    box[0] /= scale
                    box[1] /= scale
                    box[2] /= scale
                    box[3] /= scale
        lines.sort(key=lambda item: ((item.get("box") or [0, 0, 0, 0])[1], (item.get("box") or [0, 0, 0, 0])[0]))
        return lines, 1, meta

    height, width = img.shape[:2]
    step = max(1, tile_height - tile_overlap)
    total_tiles = math.ceil(max(1, height - tile_height) / step) + 1
    log(f"OCR image {image.name}: {original_width}x{original_height} -> {width}x{height}, {total_tiles} tile(s)")
    merged: list[dict[str, Any]] = []
    tiles = 0
    y_start = 0
    while True:
        y_end = min(y_start + tile_height, height)
        log(f"OCR tile {tiles + 1}/{total_tiles}: y={y_start}-{y_end}")
        crop = img[y_start:y_end, 0:width]
        tile_lines = ocr_source(ocr, mode, crop)
        for line in tile_lines:
            box = line.get("box") or []
            if len(box) == 4:
                box[1] += y_start
                box[3] += y_start
                if scale != 1.0:
                    box[0] /= scale
                    box[1] /= scale
                    box[2] /= scale
                    box[3] /= scale
        # Drop fragments physically clipped at a cut edge (not the true top/bottom);
        # the overlap guarantees the line exists intact in the neighbouring tile.
        top_cut = y_start > 0
        bottom_cut = y_end < height
        for line in tile_lines:
            box = line.get("box") or [0, 0, 0, 0]
            if top_cut and (box[1] - y_start) < EDGE_MARGIN:
                continue
            if bottom_cut and (y_end - box[3]) < EDGE_MARGIN:
                continue
            merged.append(line)
        tiles += 1
        if y_end >= height:
            break
        y_start += step

    lines = dedup_overlap(merged)
    lines.sort(key=lambda item: ((item.get("box") or [0, 0, 0, 0])[1], (item.get("box") or [0, 0, 0, 0])[0]))
    return lines, tiles, meta


def iter_images(paths: list[Path]) -> list[Path]:
    images: list[Path] = []
    for path in paths:
        if path.is_dir():
            images.extend(sorted(item for item in path.iterdir() if item.suffix.lower() in IMAGE_EXTS and item.is_file()))
        elif path.suffix.lower() in IMAGE_EXTS:
            images.append(path)
    return images


def main() -> int:
    parser = argparse.ArgumentParser(description="OCR screenshots into normalized JSON cache.")
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--conf-threshold", type=float, default=0.70)
    parser.add_argument("--tile-height", type=int, default=2400)
    parser.add_argument("--tile-overlap", type=int, default=120)
    parser.add_argument("--max-untiled-height", type=int, default=4000)
    parser.add_argument("--max-width", type=int, default=960)
    parser.add_argument("--model-profile", choices=["mobile", "server", "auto"], default="mobile")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    out_dir = args.cache_dir / args.date
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[str] = []

    images = iter_images(args.images)
    profile = "mobile" if args.model_profile == "auto" else args.model_profile
    ocr_params = {
        "model_profile": profile,
        "tile_height": args.tile_height,
        "tile_overlap": args.tile_overlap,
        "max_untiled_height": args.max_untiled_height,
        "max_width": args.max_width,
    }
    pending = [img for img in images if args.force or not (out_dir / f"{cache_key(img, ocr_params)}.json").exists()]
    ocr = mode = None
    if pending:
        log(f"OCR model profile: {profile}")
        ocr, mode = build_ocr(profile)

    for image in images:
        digest = file_hash(image)
        key = cache_key(image, ocr_params)
        out_path = out_dir / f"{key}.json"
        if out_path.exists() and not args.force:
            log(f"OCR cache hit: {image.name}")
            outputs.append(str(out_path))
            continue
        lines, tiles, image_meta = run_paddle(
            ocr,
            mode,
            image,
            args.tile_height,
            args.tile_overlap,
            args.max_untiled_height,
            args.max_width,
        )
        for line in lines:
            conf = line.get("conf")
            line["low_confidence"] = conf is not None and float(conf) < args.conf_threshold
        payload = {
            "image": str(image),
            "hash": digest,
            "cache_key": key,
            "ocr_params": ocr_params,
            "image_meta": image_meta,
            "tiled": tiles > 1,
            "tiles": tiles,
            "lines": lines,
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        outputs.append(str(out_path))

    for path in outputs:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
