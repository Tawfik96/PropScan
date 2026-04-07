import sqlite3
import json
import os

def generate_gt_template(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("SELECT * FROM listings").fetchall()

    print("GT_ROWS = [\n")

    for r in rows:
        d = dict(r)

        # Ensure JSON fields are clean
        phones = d.get("phone_numbers")
        if phones:
            try:
                phones = json.loads(phones)
            except:
                phones = [phones]
        else:
            phones = []

        print("    {")
        for k, v in d.items():

            if k == "id":
                continue

            if k == "phone_numbers":
                print(f'        "{k}": json.dumps({phones}),')
            elif v is None:
                print(f'        "{k}": None,')
            elif isinstance(v, str):
                print(f'        "{k}": "{v}",')
            else:
                print(f'        "{k}": {v},')

        print("    },\n")

    print("]")

    conn.close()


if __name__ == "__main__":
    import sys
    generate_gt_template(sys.argv[1])