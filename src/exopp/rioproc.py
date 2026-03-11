from collections.abc import Callable
from typing import ContextManager
import rasterio
from rasterio.windows import Window
from pathlib import Path


def initiator(source_path: str | Path,
              window_size: int):
    jobs = []
    with rasterio.open(source_path) as src:
        width = src.width
        height = src.height

        for row_off in range(0, height, window_size):
            for col_off in range(0, width, window_size):
                window_h = min(window_size, height - row_off)
                window_w = min(window_size, width - col_off)

                window = Window(col_off, row_off, window_w, window_h)
                jobs.append({
                    'window': window, 
                    'source_path': source_path
                })
    return jobs


def initiator_multi(source_paths: list[str | Path], window_size: int):
    """Generates localized processing windows for multivariate inputs."""
    jobs = []
    # Base spatial dimensions are extracted from the primary reference file
    with rasterio.open(source_paths[0]) as src:
        width = src.width
        height = src.height

        for row_off in range(0, height, window_size):
            for col_off in range(0, width, window_size):
                window_h = min(window_size, height - row_off)
                window_w = min(window_size, width - col_off)

                window = Window(col_off, row_off, window_w, window_h)
                jobs.append({
                    'window': window, 
                    # The parameter key is updated to match stack_transform signature
                    'source_paths': source_paths 
                })
    return jobs


def context_factory(dest_path: str,
                    meta: dict) -> Callable[[], ContextManager]:
    def factory():
        return rasterio.open(dest_path, 'w', **meta)
    return factory


def process_payload(context: rasterio.io.DatasetWriter,
                    payload: tuple) -> None:
    window, data_chunk = payload
    context.write(data_chunk, window=window)
