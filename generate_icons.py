#!/usr/bin/env python3
"""
Generate PWA icons for SafeKid Flash.
Requires: pip install pillow
Fallback: Creates SVG icon if Pillow not available.
"""
import os
import sys
from pathlib import Path

STATIC_DIR = Path(__file__).parent / "safekid" / "kid_ui" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

SVG_ICON = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0f0c29"/>
      <stop offset="50%" style="stop-color:#302b63"/>
      <stop offset="100%" style="stop-color:#667eea"/>
    </linearGradient>
    <linearGradient id="shieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea"/>
      <stop offset="100%" style="stop-color:#764ba2"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="8" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <!-- Background circle -->
  <circle cx="256" cy="256" r="256" fill="url(#bgGrad)"/>

  <!-- Glow effect -->
  <circle cx="256" cy="256" r="180" fill="rgba(102,126,234,0.08)" filter="url(#glow)"/>

  <!-- Shield body -->
  <path d="M256 100 L380 155 L380 270 C380 340 330 395 256 420 C182 395 132 340 132 270 L132 155 Z"
        fill="url(#shieldGrad)" opacity="0.95"/>

  <!-- Shield inner highlight -->
  <path d="M256 120 L365 168 L365 270 C365 333 320 383 256 406 C192 383 147 333 147 270 L147 168 Z"
        fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="2"/>

  <!-- Star in center -->
  <polygon points="256,175 268,215 310,215 277,238 289,278 256,255 223,278 235,238 202,215 244,215"
           fill="#FFD93D" filter="url(#glow)" opacity="0.95"/>

  <!-- Small decorative stars -->
  <circle cx="190" cy="200" r="4" fill="#FFD93D" opacity="0.6"/>
  <circle cx="322" cy="180" r="3" fill="#aed6f1" opacity="0.5"/>
  <circle cx="170" cy="300" r="2" fill="#FFD93D" opacity="0.4"/>
  <circle cx="340" cy="320" r="3" fill="#aed6f1" opacity="0.4"/>
</svg>'''


def create_svg_icon():
    """Save SVG icon to static folder."""
    svg_path = STATIC_DIR / "icon.svg"
    svg_path.write_text(SVG_ICON, encoding="utf-8")
    print(f"Created SVG: {svg_path}")


def create_png_icons():
    """Generate PNG icons using Pillow."""
    try:
        from PIL import Image, ImageDraw
        import io, base64

        for size in [192, 512]:
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Background circle
            draw.ellipse([0, 0, size, size], fill=(15, 12, 41, 255))

            # Shield (simplified)
            cx, cy = size // 2, size // 2
            scale = size / 512

            # Purple gradient fill (approximate)
            shield_color = (102, 126, 234, 242)
            pts = [
                (cx, int(100 * scale)),
                (int(380 * scale), int(155 * scale)),
                (int(380 * scale), int(270 * scale)),
                (cx, int(420 * scale)),
                (int(132 * scale), int(270 * scale)),
                (int(132 * scale), int(155 * scale)),
            ]
            draw.polygon(pts, fill=shield_color)

            # Star (5-point)
            star_pts = []
            import math
            cx2, cy2 = cx, int(220 * scale)
            r_outer = int(55 * scale)
            r_inner = int(22 * scale)
            for i in range(10):
                angle = math.radians(i * 36 - 90)
                r = r_outer if i % 2 == 0 else r_inner
                star_pts.append((
                    cx2 + int(r * math.cos(angle)),
                    cy2 + int(r * math.sin(angle))
                ))
            draw.polygon(star_pts, fill=(255, 217, 61, 242))

            out_path = STATIC_DIR / f"icon-{size}.png"
            img.save(out_path, "PNG")
            print(f"Created PNG icon: {out_path}")

        return True

    except ImportError:
        print("Pillow not installed — skipping PNG. SVG icon created instead.")
        print("Install: pip install pillow")
        return False


if __name__ == "__main__":
    create_svg_icon()
    created = create_png_icons()

    if not created:
        # Create minimal 1x1 placeholder PNG (valid PNG header)
        import struct, zlib

        def minimal_png(size):
            def write_chunk(chunk_type, data):
                c = chunk_type + data
                return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

            w = h = size
            header = b'\x89PNG\r\n\x1a\n'
            ihdr = write_chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))

            # Solid purple pixel row
            raw = b'\x00' + b'\x30\x2b\x63' * w
            compressed = zlib.compress(raw * h)
            idat = write_chunk(b'IDAT', compressed)
            iend = write_chunk(b'IEND', b'')
            return header + ihdr + idat + iend

        for size in [192, 512]:
            path = STATIC_DIR / f"icon-{size}.png"
            path.write_bytes(minimal_png(size))
            print(f"Created placeholder PNG: {path}")

    print("\nDone! Icons saved to:", STATIC_DIR)
