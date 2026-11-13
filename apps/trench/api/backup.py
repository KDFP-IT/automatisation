"""Online SQLite backup; invoke inside the API container, then docker compose cp it out."""
from contextlib import closing
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

source = Path(os.environ.get('DATABASE_PATH', '/data/trench.sqlite3'))
folder = source.parent / 'backups'
folder.mkdir(exist_ok=True)
target = folder / ('trench-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f') + '.sqlite3')
with closing(sqlite3.connect(source)) as origin, closing(sqlite3.connect(target)) as destination:
    origin.backup(destination)
print(target)
