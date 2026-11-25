import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import backend.database as db
import os

print('DATABASE_URL:', db.DATABASE_URL)
print('DB_FILE:', db.DB_FILE)
print('DB_ENGINE:', db.DB_ENGINE)
print('CWD:', os.getcwd())
