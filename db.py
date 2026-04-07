# import sqlite3

# conn = sqlite3.connect("llm_output.db")

# conn.execute("""
# CREATE TABLE IF NOT EXISTS listings (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     property_type TEXT,
#     transaction_type TEXT,
#     price REAL,
#     area_sqm REAL,
#     bedrooms INTEGER,
#     bathrooms INTEGER,
#     compound_name TEXT
# )
# """)

# conn.execute("""
# INSERT INTO listings (property_type, transaction_type, price, area_sqm, bedrooms)
# VALUES ('apartment', 'rent', 35000, 110, 2)
# """)

# conn.commit()
# conn.close()
import os
import tempfile

temp_db = tempfile.NamedTemporaryFile(delete=False)
os.environ["DB_PATH"] = temp_db.name

print("DB PATH:", os.path.abspath(os.environ["DB_PATH"]))