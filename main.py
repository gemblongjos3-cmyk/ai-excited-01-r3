"""Validate and copy the competition artwork without changing its bytes."""

import hashlib
import os
from pathlib import Path
import sys

MAX_BYTES = 1048576
MAX_SIDE = 1024
SOF_MARKERS = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
               0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def dimensions(data):
    """Read dimensions from a bounded JPEG SOF segment."""
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            raise ValueError("invalid JPEG marker")
        while i < len(data) and data[i] == 0xFF:
            i += 1
        if i >= len(data):
            raise ValueError("truncated JPEG marker")
        marker = data[i]
        i += 1
        if marker in (0xDA, 0xD9):
            break
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:
            continue
        if i + 2 > len(data):
            raise ValueError("truncated JPEG segment length")
        length = int.from_bytes(data[i:i + 2], "big")
        if length < 2 or i + length > len(data):
            raise ValueError("invalid or truncated JPEG segment")
        if marker in SOF_MARKERS:
            if length < 8:
                raise ValueError("truncated JPEG SOF segment")
            components = data[i + 7]
            if not components or length != 8 + 3 * components:
                raise ValueError("invalid JPEG SOF component length")
            height = int.from_bytes(data[i + 3:i + 5], "big")
            width = int.from_bytes(data[i + 5:i + 7], "big")
            if not width or not height:
                raise ValueError("JPEG dimensions must be positive")
            return width, height
        i += length
    raise ValueError("JPEG SOF marker missing")


def main():
    source = Path(__file__).resolve().parent / "entry.jpg"
    if not source.is_file():
        source = Path.cwd() / "entry.jpg"
    if source.stat().st_size > MAX_BYTES:
        raise ValueError(f"artwork exceeds {MAX_BYTES} bytes")
    data = source.read_bytes()
    if len(data) > MAX_BYTES:
        raise ValueError(f"artwork exceeds {MAX_BYTES} bytes")
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("JPEG SOI magic bytes (ffd8) missing")
    if not data.endswith(b"\xff\xd9"):
        raise ValueError("JPEG EOI magic bytes (ffd9) missing; file may be truncated")
    width, height = dimensions(data)
    if max(width, height) > MAX_SIDE:
        raise ValueError(f"artwork side exceeds {MAX_SIDE} px: {width}x{height}")
    digest = hashlib.sha256(data).hexdigest()
    dest = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")) / "entry.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    if hashlib.sha256(dest.read_bytes()).hexdigest() != digest:
        raise ValueError("copied file SHA-256 does not match source")
    print(f"ai-excited-01 -> {dest} | {len(data)} bytes | {width}x{height} | sha256 {digest}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
