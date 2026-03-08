import os
import rasterio
from pystac_client import Client
import sys
import json
import numpy as np


def generate_stretch_parameters(input_tif, output_json):
    """
    Calculates global 2nd and 98th percentiles via windowed reading
    and exports the parameters to a JSON file.
    """
    hist_16bit = np.zeros(65536, dtype=np.int64)

    # Accumulate global histogram
    with rasterio.open(input_tif) as src:
        nodata = src.nodata if src.nodata is not None else 0
        for _, window in src.block_windows(1):
            data = src.read(1, window=window)
            valid_data = data[data != nodata]
            counts = np.bincount(valid_data.ravel(), minlength=65536)
            hist_16bit += counts[:65536]

    # Compute CDF and extract percentiles
    total_valid = np.sum(hist_16bit)
    if total_valid == 0:
        raise ValueError(f"No valid data pixels found in {input_tif}.")

    cdf = np.cumsum(hist_16bit) / total_valid
    p2 = int(np.argmax(cdf >= 0.02))
    p98 = int(np.argmax(cdf >= 0.98))

    # Construct parameter dictionary
    params = {
        "file": os.path.basename(input_tif),
        "p2": p2,
        "p98": p98
    }

    # Export to JSON
    with open(output_json, 'w') as f:
        json.dump(params, f, indent=4)
    print(f"Parameters exported to {output_json}: P2={p2}, P98={p98}")


# 1. Initialize Client and execute search
catalog = Client.open("https://earth-search.aws.element84.com/v1")
search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=[8.0, 46.4, 8.1, 46.6],
    datetime="2023-06-01/2024-09-30",
    query={"eo:cloud_cover": {"lt": 30}}
)

items = list(search.items())
if not items:
    print("Error: No STAC items matched the search criteria.")
    sys.exit(1)

item = items[0]
print(f"Selected Item Date: {item.datetime}")

# 2. Define required bands and output mapping
bands = {
    "blue": ("B02", item.assets["blue"].href),
    "green": ("B03", item.assets["green"].href),
    "red": ("B04", item.assets["red"].href)
}

# 3. Sequential extraction and writing
for color, (band_id, url) in bands.items():
    output_filename = f"data/interim/aletsch_{color}.tif"
    print(f"Downloading {band_id} ({color}) from {url}...")
    with rasterio.open(url) as src:
        profile = src.profile.copy()
        profile.update(driver='GTiff')
        with rasterio.open(output_filename, "w", **profile) as dst:
            dst.write(src.read(1), 1)
    # compute the normalization parameters
    generate_stretch_parameters(f"data/interim/aletsch_{color}.tif", f"data/interim/aletsch_{color}_params.json")

print("Multispectral download complete.")
