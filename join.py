import pandas as pd
import sys
from tqdm import tqdm

from config import JOIN_COL, PROJECT_COLS

if __name__ == "__main__":
    dfs = []
    for arg in tqdm(sys.argv[1:], desc="Loading data"):
        file_ext = arg.split(".")[-1]
        file_type = arg.split("/")[-1].split("."+file_ext)[0].lower()
        df = pd.read_csv(arg, sep="\t", quotechar="'", low_memory=False)
        dfs.append((file_type, df))
    for i, (file_type, df) in tqdm(enumerate(dfs), total=len(dfs), desc="Joining data"):
        if PROJECT_COLS[file_type] is None:
            continue
        if PROJECT_COLS[file_type]:
            df = df[[JOIN_COL[file_type]]+PROJECT_COLS[file_type]]
        df.loc[:,JOIN_COL[file_type]] = df[JOIN_COL[file_type]].astype(str)
        df = df.drop_duplicates(subset=[JOIN_COL[file_type]], inplace=False, ignore_index=True)
        if i == 0:
            joined = df
        else:
            joined = joined.merge(df, left_on=prev, right_on=JOIN_COL[file_type], how="inner", sort=True, validate="one_to_one")
        prev = JOIN_COL[file_type]
    joined.to_csv("data_joined/joined.tsv", sep="\t", index=False)