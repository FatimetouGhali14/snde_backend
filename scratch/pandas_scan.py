import pandas as pd

file_path = r'C:\Users\hp\Downloads\Suivi des Incidents DP 2026 FF 06.05.2026.xlsm'

try:
    xl = pd.ExcelFile(file_path)
    print(f"Sheets: {xl.sheet_names}")
    
    for sn in xl.sheet_names:
        df = xl.parse(sn, nrows=10)
        print(f"\n--- Sheet: {sn} ---")
        print(df.head())
        
except Exception as e:
    print(f"Error: {e}")
