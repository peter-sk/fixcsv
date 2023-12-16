import json
import sys
from tqdm import tqdm

from augment import guess_data_type
from config import CAT_COLS, DEBUG

def align(header, parts, row, types):
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
        print(f"guessing {val} for {col}")
    ts = types[col]
    t = guess_data_type(val, col)
    if t == 'str' and col in CAT_COLS:
        raise RuntimeError(f"could not parse {val} from {parts[:3]} for {col}")
    if t in ts:
        try:
            new_row = align(header[1:], parts[1:], row+(val,), types)
            return new_row
        except ValueError:
            pass
    if len(parts) <= 1 or not 'float' in ts:
        raise ValueError(f"could not parse {val} from {parts[:3]} for {col}")
    val = ','.join(parts[:2])
    if DEBUG:
        print(f"guessing {val} for {col}")
    t = guess_data_type(val, col)
    if t in ts:
        return align(header[1:], parts[2:], row+(val,), types)
    if DEBUG:
        print(ts, t, col, parts[:3])
    raise ValueError(f"could not parse {val} from {parts[:3]} for {col}")

if __name__ == "__main__":
    for arg in tqdm(sys.argv[1:], desc="Aligning rows"):
        if DEBUG:
            print(arg)
        with open(arg, "rt") as f:
            augmented = json.load(f)
        types, variants = augmented["types"], augmented["variants"]
        for variant in variants:
            header = variant["header"]
            rows = []
            for row in tqdm(variant["rows"], desc=f"Fixing rows for {arg}"):
                if DEBUG:
                    print("-"*80)
                    print(header)
                    print(row)
                rows.append(align(header, row, (), types))
            assert(len(rows) == len(variant["rows"]))
            assert(all(len(row) == len(header) for row in rows))
            assert(all(len(row) != len(header) for row in variant["rows"]))
            variant["rows"] = rows
        with open(arg.replace("data_augmented/", "data_fixed/"), "wt") as f:
            json.dump(variants, f, indent=2)
