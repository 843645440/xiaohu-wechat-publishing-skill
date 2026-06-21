#!/usr/bin/env python3
"""Detect obvious tofu-box failures in generated WeChat images.

This is intentionally conservative: it does not try to OCR Chinese. It scans
for repeated hollow square glyphs (□-like outlines) that appear when Chinese
fonts are missing in browser screenshots.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image


def is_dark(pixel, threshold=120):
    r, g, b = pixel[:3]
    return r < threshold and g < threshold and b < threshold


def looks_like_tofu_square(img: Image.Image, x: int, y: int, size: int = 18) -> bool:
    """Return True if a small region looks like a hollow missing-glyph box."""
    w, h = img.size
    if x + size >= w or y + size >= h:
        return False
    # Sample border and inner pixels. Tofu boxes have dark borders and mostly light interiors.
    border = []
    inner = []
    for i in range(size):
        border.append(img.getpixel((x + i, y)))
        border.append(img.getpixel((x + i, y + size - 1)))
        border.append(img.getpixel((x, y + i)))
        border.append(img.getpixel((x + size - 1, y + i)))
    for yy in range(y + 4, y + size - 4, 2):
        for xx in range(x + 4, x + size - 4, 2):
            inner.append(img.getpixel((xx, yy)))
    border_dark = sum(is_dark(p, 145) for p in border) / max(1, len(border))
    inner_dark = sum(is_dark(p, 145) for p in inner) / max(1, len(inner))
    return border_dark > 0.42 and inner_dark < 0.18


def count_tofu_boxes(path: Path) -> int:
    img = Image.open(path).convert("RGB")
    # Downscale high-DPI screenshots to logical-ish size for stable scanning.
    if img.width > 1200:
        scale = 900 / img.width
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    count = 0
    # Step coarse enough to avoid high cost, fine enough for repeated boxes.
    for y in range(0, img.height - 20, 4):
        for x in range(0, img.width - 20, 4):
            if looks_like_tofu_square(img, x, y):
                count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="Check generated images for tofu-box glyphs")
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--max-boxes", type=int, default=8)
    args = parser.parse_args()

    failed = False
    for path in args.images:
        n = count_tofu_boxes(path)
        print(f"{path}: tofu_like_boxes={n}")
        if n > args.max_boxes:
            failed = True
    if failed:
        raise SystemExit("Possible missing Chinese font/tofu boxes detected")


if __name__ == "__main__":
    main()
