"""Read-only comparison with the pre-restructuring database and file baseline.

Run immediately after restructuring. Later legitimate user/database changes will
make the database comparison differ. No rows, credentials or hashes are printed.
"""
import hashlib
import json
import os
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


def main():
    import django
    django.setup()
    from django.db import connection

    baseline = json.loads((BASE_DIR / 'docs/restructuring_baseline.json').read_text())
    tables = {}
    with connection.cursor() as cursor:
        for table in sorted(connection.introspection.table_names()):
            cursor.execute('SELECT * FROM ' + connection.ops.quote_name(table))
            rows = sorted(repr(row) for row in cursor.fetchall())
            tables[table] = {
                'count': len(rows),
                'sha256': hashlib.sha256('\n'.join(rows).encode()).hexdigest(),
            }
    if tables != baseline['tables']:
        raise SystemExit('Database differs from the inspection baseline.')
    print(f'PASS: all {len(tables)} database tables match baseline counts and contents.')

    hashes = json.loads((BASE_DIR / 'docs/original_file_hashes.json').read_text())
    protected = [name for name in hashes if (
        # Training code now evolves with dataset integration; protect data/history.
        name in ('.env', 'db.sqlite3', 'requirements.txt')
        or name.startswith(('templates/', 'static/', 'datasets/', 'ml_models/'))
        or '/migrations/' in name
    )]
    for name in protected:
        relocated = name.replace('accounts/migrations/', 'apps/authentication/migrations/').replace('predictions/migrations/', 'apps/core/legacy/predictions/migrations/').replace('wellness/migrations/', 'apps/core/legacy/wellness/migrations/')
        for app in ('dashboard', 'recommendations'):
            relocated = relocated.replace(app + '/migrations/', 'apps/core/legacy/' + app + '/migrations/')
        if name == 'requirements.txt':
            relocated = 'requirements/base.txt'
        for old, new in [('accounts', 'authentication'), ('dashboard', 'core/dashboard'), ('predictions', 'core/predictions'), ('recommendations', 'core/recommendations'), ('wellness', 'core/wellness')]:
            relocated = relocated.replace('templates/' + old + '/', 'templates/' + new + '/')
        # Template includes necessarily change when their directories move.
        if name.startswith('templates/'):
            continue
        current = hashlib.sha256((BASE_DIR / relocated).read_bytes()).hexdigest()
        if current != hashes[name]:
            raise SystemExit(f'Protected file changed: {name}')
    print(f'PASS: all {len(protected)} protected files are byte-for-byte unchanged.')


if __name__ == '__main__':
    main()
