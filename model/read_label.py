import pandas as pd

csv_path = r"C:\Users\KiTE\Desktop\model\label\dataset13.csv"  # change only this
df13 = pd.read_csv(csv_path)

print(df13.head())
print("Shape:", df13.shape)
print(df13['label'].value_counts())
