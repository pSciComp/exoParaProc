import os
import json
from pathlib import Path

from exopp.stac_io import fetch_stac_assets, download_asset


def main():
    # 1. Environment and Configuration Initialization
    interim_dir = Path(os.environ.get("INTERIM_PATH", './data/interim/'))
    config_path = Path(os.environ.get("CONFIG_FETCH_JSON",
                                      './config/stac_download.json'))

    interim_dir.mkdir(parents=True, exist_ok=True)

    with open(config_path, 'r') as f:
        config = json.load(f)

    # 2. STAC Catalog Search
    assets = fetch_stac_assets(
        api_url=config['api_url'],
        collections=config['collections'],
        bbox=config['bbox'],
        datetime=config['datetime'],
        query=config['query']
    )

    # 3. Asset Download and Parameter Extraction
    prefix = config['prefix']
    for color, asset_key in config['bands'].items():
        if asset_key not in assets:
            continue

        url = assets[asset_key].href
        output_filename = interim_dir / f"{prefix}_{color}.tif"

        download_asset(url, output_filename)


if __name__ == '__main__':
    main()
