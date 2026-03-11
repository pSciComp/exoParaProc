import sys
import rasterio
from pathlib import Path
from pystac_client import Client


def fetch_stac_assets(
    api_url: str,
    collections: list[str],
    bbox: list[float],
    datetime: str,
    query: dict
) -> dict:
    """
    Queries a STAC catalog and returns the assets of the first matching item.
    """
    catalog = Client.open(api_url)
    search = catalog.search(
        collections=collections,
        bbox=bbox,
        datetime=datetime,
        query=query
    )

    items = list(search.items())
    if not items:
        sys.exit("Error: No STAC items matched the search criteria.")

    item = items[0]
    return item.assets


def download_asset(url: str, output_filename: Path) -> None:
    """Downloads a raster asset via its URL to local storage."""
    with rasterio.open(url) as src:
        profile = src.profile.copy()
        profile.update(driver='GTiff')
        with rasterio.open(output_filename, "w", **profile) as dst:
            dst.write(src.read(1), 1)
