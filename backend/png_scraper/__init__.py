# png_scraper/__init__.py
"""
PNG Real Estate Scraper Engine
===============================
Public API surface:

    from png_scraper import run_all, Listing

    # Programmatic usage (async)
    import asyncio
    listings = asyncio.run(run_all(include_facebook=False))

    # CLI
    python -m png_scraper.main --help
"""

from png_scraper.engine import Listing, make_listing, normalise_price, detect_suburb
from png_scraper.main   import run_all

__all__ = ["Listing", "make_listing", "normalise_price", "detect_suburb", "run_all"]
