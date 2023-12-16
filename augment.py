from collections import defaultdict
import json
import sys

from config import STR_COLS

def is_float(x):
    try:
        float(x)
        return True
    except:
        return False

def is_int(x):
    try:
        int(x)
        return True
    except:
        return False

def is_missing(x):
    return x in (
        '',
        '???'
    )

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(arg)
        cols = defaultdict(list)
        with open(arg, "rt") as f:
            variants = json.load(f)
        for variant in variants:
            header = variant["header"]
            print(",".join(header))
            for row in variant["fine"]:
                for col, val in zip(header, row):
                    cols[col].append(val)
        types = defaultdict(lambda: defaultdict(lambda: 0))
        for col, vals in cols.items():
            for val in vals:
                if is_int(val):
                    types[col]['int'] += 1
                elif is_float(val):
                    types[col]['float'] += 1
                elif is_missing(val):
                    types[col]['missing'] += 1
                else:
                    raise ValueError(f"unable to identify type of value {val} for column {col}")            
        augmented = {
            "cols": cols,
            "types": types,
            "variants": [variant["fine"] for variant in variants],
        }
        with open(arg.replace("data_cleaned/", "data_augmented/"), "wt") as f:
            json.dump(augmented, f, indent=2)
