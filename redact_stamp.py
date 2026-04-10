from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

try:
    import fitz  # PyMuPDF
except ModuleNotFoundError:
    import pymupdf as fitz


ProgressCallback = Callable[[int, int, str], None]
LogCallback = Callable[[str], None]


def detect_red_mask(image: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    lower1 = np.array([0, 80, 80])
    upper1 = np.array([10, 255, 255])
    lower2 = np.array([160, 80, 80])
    upper2 = np.array([180, 255, 255])

    mask_hsv = cv2.inRange(hsv, lower1, upper1) | cv2.inRange(hsv, lower2, upper2)
    mask_lab = cv2.inRange(lab[:, :, 1], 135, 255)

    mask = cv2.bitwise_or(mask_hsv, mask_lab)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def find_stamp_boxes(mask: np.ndarray) -> list[tuple[int, int, int, int]]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 2000:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        if h == 0:
            continue

        ratio = w / h
        if not (0.6 < ratio < 1.4):
            continue

        fill_ratio = area / (w * h)
        if fill_ratio < 0.3:
            continue

        boxes.append((x, y, w, h))

    return boxes


def remove_duplicate_boxes(
    boxes: list[tuple[int, int, int, int]], iou_threshold: float = 0.3
) -> list[tuple[int, int, int, int]]:
    def iou(box1: tuple[int, int, int, int], box2: tuple[int, int, int, int]) -> float:
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2

        xa = max(x1, x2)
        ya = max(y1, y2)
        xb = min(x1 + w1, x2 + w2)
        yb = min(y1 + h1, y2 + h2)

        inter = max(0, xb - xa) * max(0, yb - ya)
        union = w1 * h1 + w2 * h2 - inter
        return inter / union if union > 0 else 0.0

    sorted_boxes = sorted(boxes, key=lambda box: box[2] * box[3], reverse=True)
    result = []

    for box in sorted_boxes:
        if any(iou(box, existing) > iou_threshold for existing in result):
            continue
        result.append(box)

    return result


def apply_stamp_mosaic(image: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x, y, w, h = box

    image_height, image_width = image.shape[:2]
    x = max(0, x)
    y = max(0, y)
    w = min(w, image_width - x)
    h = min(h, image_height - y)

    roi = image[y : y + h, x : x + w]
    if roi.size == 0:
        return image

    center_x, center_y = w // 2, h // 2
    radius = min(w, h) // 2
    outer_radius = int(radius * 0.95)
    inner_radius = int(radius * 0.45)

    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, (center_x, center_y), outer_radius, 255, -1)
    cv2.circle(mask, (center_x, center_y), inner_radius, 0, -1)

    small = cv2.resize(roi, (max(1, w // 25), max(1, h // 25)))
    mosaic = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    roi[mask == 255] = mosaic[mask == 255]
    image[y : y + h, x : x + w] = roi
    return image


def _emit_progress(
    callback: ProgressCallback | None, current: int, total: int, message: str
) -> None:
    if callback is not None:
        callback(current, total, message)


def _log(callback: LogCallback | None, message: str) -> None:
    if callback is not None:
        callback(message)


def redact_pdf_mosaic(
    input_pdf: str | Path,
    output_pdf: str | Path,
    debug: bool = False,
    debug_dir: str | Path = "debug",
    scale: int = 3,
    progress_callback: ProgressCallback | None = None,
    log_callback: LogCallback | None = None,
) -> Path:
    input_path = Path(input_pdf).expanduser().resolve()
    output_path = Path(output_pdf).expanduser().resolve()
    debug_path = Path(debug_dir).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_path}")
    if input_path.suffix.lower() != ".pdf":
        raise ValueError("Input file must be a PDF")
    if input_path == output_path:
        raise ValueError("Output PDF must be different from input PDF")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if debug:
        debug_path.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(input_path)
    new_doc = fitz.open()

    try:
        total_pages = len(doc)
        _emit_progress(progress_callback, 0, total_pages, "Opening PDF...")
        _log(log_callback, f"Opened: {input_path}")

        for page_index, page in enumerate(doc, start=1):
            page_message = f"Processing page {page_index}/{total_pages}"
            _emit_progress(progress_callback, page_index - 1, total_pages, page_message)
            _log(log_callback, page_message)

            pix = page.get_pixmap(
                matrix=fitz.Matrix(scale, scale),
                colorspace=fitz.csRGB,
                alpha=False,
            )

            image_rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, 3
            ).copy()
            image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

            mask = detect_red_mask(image_bgr)
            boxes = remove_duplicate_boxes(find_stamp_boxes(mask))
            boxes = sorted(boxes, key=lambda box: box[2] * box[3], reverse=True)

            if boxes:
                max_area = boxes[0][2] * boxes[0][3]
                boxes = [box for box in boxes if (box[2] * box[3]) > max_area * 0.3]

            boxes = boxes[:2]
            _log(log_callback, f"  Found {len(boxes)} candidate stamp area(s)")

            for box in boxes:
                image_bgr = apply_stamp_mosaic(image_bgr, box)

            if debug:
                cv2.imwrite(str(debug_path / f"page_{page_index}.png"), image_bgr)
                cv2.imwrite(str(debug_path / f"mask_{page_index}.png"), mask)

            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            success, encoded = cv2.imencode(".png", image_bgr)
            if not success:
                raise RuntimeError(f"Failed to encode page {page_index} as PNG")
            new_page.insert_image(new_page.rect, stream=encoded.tobytes())

            _emit_progress(
                progress_callback, page_index, total_pages, f"Finished page {page_index}/{total_pages}"
            )

        new_doc.save(output_path, deflate=True)
        _log(log_callback, f"Saved output: {output_path}")
        _emit_progress(progress_callback, total_pages, total_pages, "Completed")
        return output_path
    finally:
        new_doc.close()
        doc.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Redact red PDF stamps with mosaic.")
    parser.add_argument("input_pdf", nargs="?", default="input.pdf", help="Input PDF file")
    parser.add_argument(
        "output_pdf", nargs="?", default="output_mosaic.pdf", help="Output PDF file"
    )
    parser.add_argument("--debug", action="store_true", help="Write debug page and mask images")
    parser.add_argument(
        "--debug-dir", default="debug", help="Directory for debug images when --debug is enabled"
    )
    parser.add_argument("--scale", type=int, default=3, help="Render scale for PDF pages")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_path = redact_pdf_mosaic(
        args.input_pdf,
        args.output_pdf,
        debug=args.debug,
        debug_dir=args.debug_dir,
        scale=args.scale,
        log_callback=print,
    )
    print(f"Done: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
