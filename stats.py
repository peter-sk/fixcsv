import json
import sys

from clean import stats

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        with open(arg, "rt") as f:
            augmented = json.load(f)
        variants = augmented["variants"]
        for i, variant in enumerate(variants):
            header = variant["header"]
            fine_rows = list(variant["fine"])
            broken_rows = list(variant["broken"][10000:])
            stats(arg, variant, i)