import os
import json
import rasterio
from pathlib import Path

from exopp.parallel import orchestrator, aggregator
from exopp.rioproc import context_factory, process_payload
from exopp.rioproc import initiator_multi
from exopp.transform import stack_transform


def main():
    # 1. Environment and Configuration Initialization
    interim_dir = Path(os.environ.get("INTERIM_PATH", './data/interim/'))
    output_dir = Path(os.environ.get("OUTPUT_PATH", './data/final'))
    config_path = Path(os.environ.get("CONFIG_COMBINE_JSON",
                                      './config/combine_rgb.json'))

    # Configuration loading
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Parameter extraction
    input_files = config.get('input_files', [])
    output_filename = config.get('output_file', 'rgb.tif')
    window_size = config.get('window_size', 512)

    # Directory generation ensures the destination path exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Path Construction
    # Source paths are concatenated using the input directory
    source_paths = [interim_dir / fname for fname in input_files]

    # Destination path is concatenated using the output directory
    dest_path = output_dir / output_filename

    # 3. Metadata Compilation
    # Geotransform and CRS are inherited from the primary grid
    with rasterio.open(source_paths[0]) as src:
        meta = src.meta.copy()

    # Metadata is explicitly mutated to reflect output transformations
    meta.update({
        'count': len(source_paths),
        'dtype': 'uint8',            # Forced by normalize_array output
        'nodata': 0,
        'compress': 'lzw',           # Recommended for reproducible storage
        'tiled': True,
        'blockxsize': window_size,   # Dynamically aligned with processing window
        'blockysize': window_size
    })

    # 4. Pipeline Execution
    orchestrator(
        initiator=initiator_multi,
        job=stack_transform,
        aggregator_func=aggregator,
        aggregator_cf=context_factory,
        aggregator_processor=process_payload,
        initiator_kwargs={
            'source_paths': source_paths,
            'window_size': window_size
        },
        aggregator_cf_kwargs={
            'dest_path': dest_path,
            'meta': meta
        },
        nbrcpu=None,           # Utilizes all available processing cores
        start_method='spawn'   # Enforces strict process isolation
    )


if __name__ == '__main__':
    main()
