import numpy as np
import rasterio as rio
from pathlib import Path


def normalize_array(data_16bit, p2, p98, gamma=0.6):
    data_float = data_16bit.astype(float)
    norm = (data_float - p2) / (p98 - p2)
    norm = np.clip(norm, 0.0, 1.0)
    data_8bit = (np.power(norm, gamma) * 255).astype(np.uint8)
    data_8bit[data_16bit == 0] = 0
    return data_8bit


def transform(source_path: str | Path, window):
    p2 = 200
    p98 = 9800

    with rio.open(source_path) as src:
        data = src.read(1, window=window)
        processed_data = normalize_array(data, p2, p98, gamma=0.6)
        return window, processed_data


def stack_transform(source_paths: list[str | Path], window):
    bands_data = []
    for source_path in source_paths:
        # Relies on the previously corrected transform() function
        _, data = transform(source_path=source_path, window=window)
        bands_data.append(data)

    # np.stack enforces the (bands, rows, columns) convention required by GDAL
    return window, np.stack(bands_data)
