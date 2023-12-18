from collections import defaultdict
import json
import sys
from tqdm import tqdm

from config import CAT_COLS, DEBUG, EXTRA_RANGES, EXTRA_TYPES, STR_COLS

def is_float(x):
    if x.endswith(".00"):
        x = x[:-3]
    parts = x.split(',') if "," in x else x.split('.')
    if len(parts) > 2:
        return False
    try:
        y = float('.'.join(parts))
        return True, y
    except:
        return False, None

def is_int(x):
    try:
        y = int(x)
        return True, y
    except:
        return False, None

def is_missing(x):
    return x in (
        '',
        '???'
    )

def is_time(x):
    parts = x.split(":") if ":" in x else x.split(".")
    if len(parts) != 3 or any(not part.isnumeric() for part in parts):
        return False, None
    hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
    if hours < 0 or hours > 24:
        return False, None
    if minutes < 0 or minutes > 60:
        return False, None
    if seconds < 0 or seconds > 60:
        return False, None
    return True, ":".join(x)

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
        if are_date(*parts):
            return True, f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        if are_date(parts[2], parts[0], parts[1]):
            return True, f"{int(parts[2]):04d}-{int(parts[1]):02d}-{int(parts[0]):02d}"
        return False, None
    if not x.isnumeric():
        return False, None
    if len(x) != 8:
        return False, None
    if are_date(x[:4], x[4:6], x[6:]):
        return True, f"{x[:4]}-{x[4:6]}-{x[6:]}"
    if are_date(x[-4:], x[2:4], x[:2]):
        return True, f"{x[-4:]}-{x[4:6]}-{x[:2]}"
    return False, None

def is_str(col):
    return col in STR_COLS

def is_cat(val, col):
    if not col in CAT_COLS:
        return False
    return val in CAT_COLS[col]

# def guess_data_type(val, col):
#     if is_str(col):
#         types[col]['str'] += 1
#     elif is_cat(val, col):
#         types[col]['cat'] += 1
#     elif is_date(val):
#         types[col]['date'] += 1
#     elif is_time(val):
#         types[col]['time'] += 1
#     elif is_int(val):
#         types[col]['int'] += 1
#     elif is_float(val):
#         types[col]['float'] += 1
#     elif is_missing(val):
#         types[col]['missing'] += 1
#     else:
#         raise ValueError(f"unable to guess type of value {val} for column {col}")
def guess_data_type(val, col):
    if is_str(col):
        return 'str', val
    if is_cat(val, col):
        return 'cat', val
    res, new_val = is_date(val)
    if res:
        return 'date', new_val
    res, new_val = is_time(val)
    if res:
        return 'time', new_val
    res, new_val = is_int(val)
    if res:
        return 'int', new_val
    res, new_val = is_float(val)
    if res:
        return 'float', new_val
    if is_missing(val):
        return 'missing', ''
    else:
        raise ValueError(f"unable to guess type of value {val} for column {col}")

if __name__ == "__main__":
    for arg in tqdm(sys.argv[1:], desc="Guessing types of columns"):
        if DEBUG:
            print(arg)
        cols = defaultdict(list)
        with open(arg, "rt") as f:
            variants = json.load(f)
        for variant in variants:
            header = variant["header"]
            if DEBUG:
                print(",".join(header))
            for row in variant["fine"]:
                for col, val in zip(header, row):
                    cols[col].append(val)
        types = defaultdict(lambda: defaultdict(lambda: 0))
        ranges = defaultdict(lambda: defaultdict(list))
        for col, vals in cols.items():
            for val in vals:
                t, new_val = guess_data_type(val, col)
                if t == 'cat':
                    ranges[col][t].extend(CAT_COLS[col])
                types[col][t] += 1
                ranges[col][t].append(new_val)
        # for col, type_counter in types.items():
        #     if 'int' in type_counter and 'date' in type_counter and type_counter['int'] > type_counter['date']:
        #         type_counter['date'] += type_counter['int']
        #         del type_counter['int']
        #     if 'int' in type_counter and 'float' in type_counter:
        #         type_counter['float'] += type_counter['int']
        #         del type_counter['int']
        #     if 'float' in type_counter and 'missing' in type_counter:
        #         type_counter['float'] += type_counter['missing']
        #         del type_counter['missing']
        #     if 'int' in type_counter and 'missing' in type_counter:
        #         type_counter['int'] += type_counter['missing']
        #         del type_counter['missing']
        for col, range in ranges.items():
            for t, vals in range.items():
                ranges[col][t] = (min(vals), max(vals))
        file_type = arg.split("/")[-1].split(".json")[0]
        types.update(EXTRA_TYPES.get(file_type, {}))
        ranges.update(EXTRA_RANGES.get(file_type, {}))
        augmented = {
            "types": types,
            "ranges": ranges,
            "variants": [{"header": variant["header"], "broken": variant["broken"], "fine": variant["fine"]} for variant in variants],
        }
        with open(arg.replace("data_cleaned/", "data_augmented/"), "wt") as f:
            json.dump(augmented, f, indent=2)
