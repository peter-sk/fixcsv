from collections import defaultdict
import json
import sys
from tqdm import tqdm

from config import MAGICS, FILE_TYPES, guess_file_type

def split(s, sep, quote='"'):
    orig = s
    parts = []
    quoted = False
    s = s+sep
    part = ''
    while s:
        c, s = s[0], s[1:]
        if quoted:
            if c == quote:
                if s and s[0] == quote:
                    part += quote
                    part += quote
                    s = s[1:]
                else:
                    quoted = False
            elif c == "\\":
                part += "\\"
                while s[0] == quote:
                    part += s[0]
                    s = s[1:]
            else:
                part += c
        elif c == sep:
            parts.append(part)
            part = ''
        elif c == quote:
            quoted = True
            if part:
                print(repr(orig))
                print(repr(part))
            assert(not part)
        else:
            part += c
    return tuple([part.strip() for part in parts])

def stats(data):
    for file_type, variants in data.items():
        header_type = 0
        for _, rows in variants.items():
            header_type += 1
            print(f"{file_type} header-{header_type} broken {len(rows[True])}")
            print(f"{file_type} header-{header_type} fine   {len(rows[False])}")

if __name__ == "__main__":
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    errors = []
    for arg in tqdm(sys.argv[1:], desc="Extracting data"):
        file_ext = arg.split(".")[-1]
        if file_ext == "xls":
            print(arg, file_type, file_ext, "SKIPPING")
            continue
        file_type = arg.split("/")[-1].split("."+file_ext)[0].lower()
        #print(arg, file_type, file_ext, end=' ')
        if file_type not in FILE_TYPES:
            file_type = guess_file_type(file_type)
        with open(arg, "rt", encoding="latin1") as f:
            content = [c.strip() for c in f.readlines()]
        skipped = 0
        #print(len(content), end=' ')
        while content:
            parts = content[0].split('"')
            if len(parts) > 0 and any(parts[0].startswith(m) for m in MAGICS):
                sep = "\t"
                quoted = False
                with open(arg, "rt", encoding="latin1") as f:
                    content = [c.strip() for c in f.readlines()]
                break
            if len(parts) > 1 and parts[1] in MAGICS:
                sep = parts[2]
                quoted = True
                break
            content = content[1:]
            skipped += 1
        else:
            assert(False)
        #print(skipped, repr(sep), quoted, len(content), end=' ')
        assert(skipped in (0,2,3))
        header, rest = content[0], content[1:]
        hparts = split(header, sep)
        for i, line in enumerate(rest):
            lparts = split(line, sep)
            error = len(lparts) != len(hparts)
            if error and sep != ',':
                errors.append((arg, file_type, i, len(hparts), len(lparts)))
            data[file_type][hparts][error].append(lparts)
        #print(f"DONE")
    print(errors)
    print("BEFORE DEDUPLICATION")
    stats(data)
    for file_type, variants in tqdm(data.items(), desc="Deduplicating data"):
        for header, rows in variants.items():
            for error in rows:
                data[file_type][header][error] = list(set(rows[error]))
                data[file_type][header][error].sort()
    print("AFTER DEDUPLICATION")
    stats(data)
    for file_type, variants in tqdm(data.items(), desc="Saving data"):
        with open(f"data_splitted/{file_type}.json", "wt") as f:
            variants = [{"header": header, "broken": rows[True], "fine": rows[False]} for header, rows in variants.items()]
            json.dump(variants, f, indent=2)
