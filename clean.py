import json
import sys
from tqdm import tqdm

def stats(arg, variant, i):
    file_type = arg.split("/")[-1].split(".")[0]
    print(f"{file_type} header-{i} broken {len(variant['broken'])}")
    print(f"{file_type} header-{i} fine   {len(variant['fine'])}")

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(arg)
        with open(arg, "rt") as f:
            data = json.load(f)
        print("BEFORE DEDUPLICATION")
        for i, variant in enumerate(data):
            stats(arg, variant, i)
            broken_joined = {','.join(b): b for b in variant['broken']}
            fine_joined = {','.join(f): f for f in variant['fine']}
            to_delete = []
            for b_joined, b in tqdm(broken_joined.items(), desc="Scanning for quasi-duplicates"):
                for f_joined, f in fine_joined.items():
                    if b_joined == f_joined:
                        to_delete.append(b)
            for b in to_delete:
                variant["broken"].remove(b)
        print("AFTER DEDUPLICATION")
        stats(arg, variant, i)
        with open(arg.replace("data/", "data_cleaned/"), "wt") as f:
            json.dump(data, f, indent=2)
