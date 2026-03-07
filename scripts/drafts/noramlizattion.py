import rasterio
import numpy as np
import json
import os


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

# Execution
generate_stretch_parameters("aletsch_red.tif", "aletsch_red_params.json")
