import pandas as pd
import os

label_dir = r"C:\Users\KiTE\Desktop\model\label"
clips_root = r"C:\Users\KiTE\Desktop\model\clips"

all_dfs = []

for i in range(1, 14):   # 1..13
    csv_name = f"dataset{i}.csv"
    csv_path = os.path.join(label_dir, csv_name)

    df = pd.read_csv(csv_path)

    # add the full relative path to each clip
    clip_folder = f"dataset{i}"
    df["filepath"] = df["filename"].apply(
        lambda x: os.path.join("clips", clip_folder, x + ".mp4")
    )

    all_dfs.append(df)

merged = pd.concat(all_dfs, ignore_index=True)

out_path = os.path.join(label_dir, "all_labels.csv")
merged.to_csv(out_path, index=False)

print("Saved merged labels to:", out_path)
print("Total clips:", len(merged))
print(merged.head())
