import os
import json
import rasterio
from pathlib import Path
from mpi4py import MPI

from exopp.mpi_parallel import mpi_orchestrator
from exopp.rioproc import context_factory, process_payload, initiator_multi
from exopp.transform import stack_transform


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    # 1. Environment and Configuration Parsing
    input_dir = Path(os.environ.get("INPUT_PATH", './data/interim/'))
    output_dir = Path(os.environ.get("OUTPUT_PATH", './data/final'))
    config_path = Path(os.environ.get("CONFIG_JSON",
                                      './config/combine_rgb.json'))

    with open(config_path, 'r') as f:
        config = json.load(f)

    source_paths = [input_dir / fname for fname in config['input_files']]
    dest_path = output_dir / config.get('output_file', 'rgb_mpi.tif')
    window_size = config.get('window_size', 512)

    # 2. Synchronized Metadata Extraction
    meta = None
    if rank == 0:
        output_dir.mkdir(parents=True, exist_ok=True)
        with rasterio.open(source_paths[0]) as src:
            meta = src.meta.copy()

        meta.update({
            'count': len(source_paths),
            'dtype': 'uint8',
            'nodata': 0,
            'compress': 'lzw',
            'tiled': True,
            'blockxsize': window_size,
            'blockysize': window_size
        })

    # The metadata dictionary is broadcast to ensure all ranks possess identical state
    meta = comm.bcast(meta, root=0)

    # 3. Pipeline Execution
    mpi_orchestrator(
        initiator=initiator_multi,
        job=stack_transform,
        aggregator_cf=context_factory,
        aggregator_processor=process_payload,
        initiator_kwargs={
            'source_paths': source_paths,
            'window_size': window_size
        },
        aggregator_cf_kwargs={
            'dest_path': str(dest_path),
            'meta': meta
        }
    )

if __name__ == '__main__':
    main()
