"""Download only the selected CSVs from Kaggle; never extracts archive paths.

Run: python scripts/download_datasets.py [--force]
Uses existing .env credentials, or anonymous access for public datasets.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
from io import BytesIO, StringIO
import json
from pathlib import Path
import sys
from zipfile import ZipFile

import requests
from decouple import AutoConfig

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ml.datasets import DATASET_SOURCES, normalize_column


def download_all(force=False):
    config = AutoConfig(search_path=str(ROOT))
    username = config('KAGGLE_USERNAME', default='')
    key = config('KAGGLE_KEY', default='')
    auth = (username, key) if username and key else None
    destination = ROOT / 'datasets'
    destination.mkdir(exist_ok=True)
    manifest_path = destination / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    for source in DATASET_SOURCES:
        path = destination / source['filename']
        if path.exists() and not force:
            print(f"Already present: {path.name}; use --force to replace.")
            continue
        response = requests.get(
            'https://www.kaggle.com/api/v1/datasets/download/' + source['kaggle_slug'],
            auth=auth, timeout=90,
        )
        response.raise_for_status()
        with ZipFile(BytesIO(response.content)) as archive:
            names = [name for name in archive.namelist()
                     if name.rsplit('/', 1)[-1] == source['archive_filename']]
            if len(names) != 1:
                raise ValueError(f"Expected CSV missing or ambiguous for {source['slug']}")
            info = archive.getinfo(names[0])
            if info.file_size > 100 * 1024 * 1024:
                raise ValueError('Dataset exceeds the selected CSV size limit.')
            content = archive.read(names[0])
        reader = csv.DictReader(StringIO(content.decode('utf-8-sig')))
        columns = reader.fieldnames or []
        missing = set(source['required_columns']) - {normalize_column(c) for c in columns}
        if missing:
            raise ValueError(f"Invalid schema for {source['slug']}: {sorted(missing)}")
        rows = sum(1 for _ in reader)
        if not rows:
            raise ValueError('Downloaded CSV is empty.')
        temporary = path.with_suffix('.csv.part')
        temporary.write_bytes(content)
        temporary.replace(path)
        manifest[source['slug']] = {
            'filename': path.name,
            'source_url': 'https://www.kaggle.com/datasets/' + source['kaggle_slug'],
            'archive_filename': source['archive_filename'],
            'downloaded_at_utc': datetime.now(timezone.utc).isoformat(),
            'rows': rows,
            'columns': columns,
            'sha256': hashlib.sha256(content).hexdigest(),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        print(f"Downloaded {path.name}: {rows:,} rows; schema verified.")
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    try:
        download_all(args.force)
    except (requests.RequestException, ValueError, OSError) as exc:
        # URLs in network exceptions can include signed cloud credentials.
        print(f'Download failed ({type(exc).__name__}); check Kaggle access and credentials.', file=sys.stderr)
        sys.exit(1)
