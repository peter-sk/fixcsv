import json
import sys
from tqdm import tqdm

from config import DEBUG

def stats(arg, variant, i):
    file_type = arg.split("/")[-1].split(".")[0]
    print(f"{file_type} header-{i} broken {len(variant['broken'])}")
    print(f"{file_type} header-{i} fine   {len(variant['fine'])}")

if __name__ == "__main__":
    for arg in tqdm(sys.argv[1:], desc="Scanning for quasi-duplicates"):
        if DEBUG:
            print(arg)
        with open(arg, "rt") as f:
            data = json.load(f)
        if DEBUG:
            print("BEFORE DEDUPLICATION")
        for i, variant in enumerate(data):
            stats(arg, variant, i)
            broken_joined = {','.join(b): b for b in variant['broken']}
            fine_joined = {','.join(f): f for f in variant['fine']}
            to_delete = []
            for b_joined, b in broken_joined.items():
                for f_joined, f in fine_joined.items():
                    if b_joined == f_joined:
                        to_delete.append(b)
            for b in to_delete:
                variant["broken"].remove(b)
        if DEBUG:
            print("AFTER DEDUPLICATION")
            stats(arg, variant, i)
        with open(arg.replace("data_splitted/", "data_cleaned/"), "wt") as f:
            json.dump(data, f, indent=2)
