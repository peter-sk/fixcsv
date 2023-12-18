import json
import sys
from tqdm import tqdm

from augment import guess_data_type
from config import CAT_COLS, DEBUG, MAX_ERRORS, OOR_ALLOWANCE, OOR_DEFAULT_WIDTH

def oor(val, ranges, t, indent):
    if t == 'date':
        return False
    range = ranges[t]
    if t in ('int', 'float'):
        width = range[1]-range[0]
        if width == 0:
            width = OOR_DEFAULT_WIDTH*range[0]
        left = range[0]-OOR_ALLOWANCE*width
        right = range[1]+OOR_ALLOWANCE*width
    elif t == 'str':
        left = chr(ord(range[0][0])-1)+range[0][1:] if range[0] else range[0]
        right = chr(ord(range[1][0])+1)+range[1][1:] if range[1] else range[1]
    else:
        left, right = range
    left, right = min((left, right)), max((left, right))
    if DEBUG:
        print(f"{indent*' '}left = {left}, right = {right}")
    return not (left <= val <= right)

def align(header, parts, row, types, ranges, error, indent=0):
    if error > MAX_ERRORS:
        raise ValueError(f"too many errors")
    if not header:
        if parts:
            raise ValueError(f"unparsed values {parts}")
        return row
    if not parts:
        raise ValueError(f"no values for {header}")
    if len(header) > len(parts) or len(parts) > 2*len(header):
        raise ValueError(f"misaligned lengths")
    col, val = header[0], parts[0]
    if DEBUG:
        print(f"{indent*' '}guessing {val} for {col}")
    ts = types[col]
    t, new_val = guess_data_type(val, col)
    if DEBUG:
        print(f"{indent*' '}{val} has guessed type {t} and new value {new_val}")
    if t == 'str' and col in CAT_COLS:
        raise RuntimeError(f"could not parse {val} from {parts[:3]} for {col}")
    if t == 'int' and len(parts) > 1 and 'float' in ts:
        val2 = ','.join(parts[:2])
        if DEBUG:
            print(f"{indent*' '}guessing {val2} for {col}")
        try:
            t2, new_val2 = guess_data_type(val2, col)
            if DEBUG:
                print(f"{indent*' '}{val2} has guessed type {t2} and new value {new_val2}")
            if t2 in ts:
                new_error = error+1 if oor(new_val2, ranges[col], t2, indent) else error
                if DEBUG:
                    print(f"{indent*' '}oor is {oor(new_val2, ranges[col], t2, indent)} for col {col}, new_val {new_val2}, range {ranges[col]}, and type {t2}")
                new_row = align(header[1:], parts[2:], row+(val2,), types, ranges, new_error, indent=indent+2)
                return new_row
        except ValueError as e:
            if DEBUG:
                print(f"{indent*' '}for {val2} got {e}")
            pass
        if DEBUG:
            print(f"{indent*' '}back to {val} for {col} with type {t} and new_val {new_val}")
    if t in ts:
        new_error = error+1 if oor(new_val, ranges[col], t, indent) else error
        if DEBUG:
            print(f"{indent*' '}oor is {oor(new_val, ranges[col], t, indent)} for col {col}, new_val {new_val}, range {ranges[col]}, and type {t}")
        return align(header[1:], parts[1:], row+(val,), types, ranges, new_error, indent=indent+2)
    if DEBUG:
        print(f"{indent*' '}{ts} {t} {col} {parts[:3]}")
    raise ValueError(f"could not parse {val} from {parts[:3]} for {col}")

if __name__ == "__main__":
    for arg in tqdm(sys.argv[1:], desc="Aligning rows"):
        if DEBUG:
            print(arg)
        with open(arg, "rt") as f:
            augmented = json.load(f)
        types, ranges, variants = augmented["types"], augmented["ranges"], augmented["variants"]
        for variant in variants:
            header = variant["header"]
            fine_rows = list(variant["fine"])
            broken_rows = []
            for row in tqdm(variant["broken"], desc=f"Fixing rows for {arg}"):
                if DEBUG:
                    print("-"*80)
                    print(list(enumerate(header)))
                    print(list(enumerate(row)))
                    print(list(enumerate([types[col] for col in header])))
                try:
                    fine_rows.append(align(header, row, (), types, ranges, 0))
                except ValueError:
                    print("ouch")
                    broken_rows.append(row)
            assert(len(broken_rows)+len(fine_rows) == len(variant["broken"])+len(variant["fine"]))
            assert(all(len(row) == len(header) for row in fine_rows))
            assert(all(len(row) != len(header) for row in broken_rows))
            variant["fine"] = fine_rows
            variant["broken"] = broken_rows
        with open(arg.replace("data_augmented/", "data_fixed/"), "wt") as f:
            json.dump(augmented, f, indent=2)
