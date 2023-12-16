from collections import defaultdict
from dateutil.parser import parse as date_parse
import json
import sys
from tqdm import tqdm

from config import CAT_COLS, STR_COLS

def is_float(x):
    if x.endswith(".00"):
        x = x[:-3]
    parts = x.split(',') if "," in x else x.split('.')
    if len(parts) > 2:
        return False
    try:
        float('.'.join(parts))
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

def is_time(x):
    parts = x.split(":") if ":" in x else x.split(".")
    if len(parts) != 3 or any(not part.isnumeric() for part in parts):
        return False
    hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
    if hours < 0 or hours > 24:
        return False
    if minutes < 0 or minutes > 60:
        return False
    if seconds < 0 or seconds > 60:
        return False
    return True

def are_date(year, month, day):
    year, month, day = int(year), int(month), int(day)
    if year < 1800 or year > 2100:
        return False
    if month < 1 or month > 12:
        return False
    if day < 1 or day > 31:
        return False
    return True

def is_date(x):
    parts = x.split("-")
    if len(parts) == 3 and all(part.isnumeric() for part in parts):
        return True
    if not x.isnumeric():
        return False
    if len(x) != 8:
        return False
    if are_date(x[:4], x[4:6], x[6:]):
        return True
    if are_date(x[-4:], x[2:4], x[:2]):
        return True
    return False
    try:
        date_parse(x)
        return True
    except:
        return False

def is_str(col):
    return col in STR_COLS

def is_cat(val, col):
    if not col in CAT_COLS:
        return False
    return val in CAT_COLS[col]

def guess_data_type(val, col):
    if is_str(col):
        types[col]['str'] += 1
    elif is_cat(val, col):
        types[col]['cat'] += 1
    elif is_date(val):
        types[col]['date'] += 1
    elif is_time(val):
        types[col]['time'] += 1
    elif is_int(val):
        types[col]['int'] += 1
    elif is_float(val):
        types[col]['float'] += 1
    elif is_missing(val):
        types[col]['missing'] += 1
    else:
        raise ValueError(f"unable to guess type of value {val} for column {col}")

if __name__ == "__main__":
    for arg in tqdm(sys.argv[1:], desc="Guessing types of columns"):
        #print(arg)
        cols = defaultdict(list)
        with open(arg, "rt") as f:
            variants = json.load(f)
        for variant in variants:
            header = variant["header"]
            #print(",".join(header))
            for row in variant["fine"]:
                for col, val in zip(header, row):
                    cols[col].append(val)
        types = defaultdict(lambda: defaultdict(lambda: 0))
        for col, vals in cols.items():
            for val in vals:
                t = guess_data_type(val, col)
        for col, type_counter in types.items():
            if 'int' in type_counter and 'date' in type_counter and type_counter['int'] > type_counter['date']:
                type_counter['date'] += type_counter['int']
                del type_counter['int']
            if 'int' in type_counter and 'float' in type_counter:
                type_counter['float'] += type_counter['int']
                del type_counter['int']
            if 'float' in type_counter and 'missing' in type_counter:
                type_counter['float'] += type_counter['missing']
                del type_counter['missing']
            if 'int' in type_counter and 'missing' in type_counter:
                type_counter['int'] += type_counter['missing']
                del type_counter['missing']
        augmented = {
#            "cols": cols,
            "types": types,
            "variants": [{"header": variant["header"], "rows": variant["broken"]} for variant in variants],
        }
        with open(arg.replace("data_cleaned/", "data_augmented/"), "wt") as f:
            json.dump(augmented, f, indent=2)
