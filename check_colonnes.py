import pandas as pd

FICHIER = r"C:\Users\hp\Downloads\Suivi des Incidents DP 2026 FF 06.05.2026.xlsm"

df = pd.read_excel(FICHIER, sheet_name="Suivi des incidents", header=1)
print("Colonnes exactes :")
for i, col in enumerate(df.columns.tolist()):
    print(f"  {i}: '{col}'")
print("\nPremière ligne :")
print(df.iloc[0])