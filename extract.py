import json
import sys
from tqdm import tqdm

from config import DEBUG, MERGE

def merge(h1, h2, m):
    if not h1:
        if not h2:
            return m
        if not h2[0] in m:
            m.append(h2[0])
        return merge(h1, h2[1:], m)
    if not h2:
        if not h1[0] in m:
            m.append(h1[0])
        return merge(h1[1:], h2, m)
    if h1[0] == h2[0]:
        if not h1[0] in m:
            m.append(h1[0])
        return merge(h1[1:], h2[1:], m)
    elif h1[0] < h2[0]:
        if not h1[0] in m:
            m.append(h1[0])
        return merge(h1[1:], h2, m)
    else:
        if not h2[0] in m:
            m.append(h2[0])
        return merge(h1, h2[1:], m)

if __name__ == "__main__":
    for arg in tqdm(sys.argv[1:], desc="Extracting rows"):
        if DEBUG:
            print(arg)
        with open(arg, "rt") as f:
            fixed = json.load(f)
        types, variants = fixed["types"], fixed["variants"]
        merged_header = []
        for i, variant in enumerate(variants):
            header = variant["header"]
            if DEBUG:
                print(f"header-{i} = {header}")
            merged_header = merge(merged_header, header, [])
        if DEBUG:
            print(f"merged_header = {merged_header}")
        assert(len(merged_header) == len(set(merged_header)))
        assert(not any("\t" in h for h in merged_header))
        new_rows = []
        for i, variant in enumerate(variants):
            if not MERGE:
                new_rows.clear()
            header = variant["header"]
            fine_rows = list(variant["fine"])
            for row in tqdm(fine_rows, desc=f"Extracting rows for {arg}"):
                assert(len(header) == len(row))
                row2val = dict(zip(header, row))
                new_row = [row2val.get(h, '') for h in (merged_header if MERGE else header)]
                if DEBUG:
                    print(f"new_row = {new_row}")
                new_rows.append(new_row)
            assert(not any("\t" in new_row for new_row in new_rows))
            if not MERGE:
                with open(arg.replace("data_fixed/", "data_extracted/").replace(".json", f"-header-{i}.tsv"), "wt") as f:
                    print("\t".join(header), file=f)
                    for new_row in new_rows:
                        print("\t".join(new_row), file=f)
        if MERGE:
            with open(arg.replace("data_fixed/", "data_extracted/").replace(".json", ".tsv"), "wt") as f:
                print("\t".join(merged_header), file=f)
                for new_row in new_rows:
                    print("\t".join(new_row), file=f)

