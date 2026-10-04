"""Convert page 1 of docs/architecture.pdf to docs/architecture.png.

  python scripts/pdf_to_png.py                 # default: page 1 at 180 DPI
  python scripts/pdf_to_png.py --dpi 240 --page 2
"""
from __future__ import annotations
import argparse
from pathlib import Path
import fitz   # PyMuPDF


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pdf", default="docs/architecture.pdf")
    p.add_argument("--png", default="docs/architecture.png")
    p.add_argument("--page", type=int, default=1, help="1-indexed")
    p.add_argument("--dpi", type=int, default=180)
    a = p.parse_args()
    src = Path(a.pdf)
    if not src.exists():
        raise FileNotFoundError(f"{src}: drop the submitted design PDF here first")
    doc = fitz.open(src)
    page = doc[a.page - 1]
    mat = fitz.Matrix(a.dpi / 72, a.dpi / 72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    Path(a.png).parent.mkdir(parents=True, exist_ok=True)
    pix.save(a.png)
    print(f"  {a.png}  ({pix.width}x{pix.height}, {Path(a.png).stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
