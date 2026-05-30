import openpyxl

file_path = r'C:\Users\hp\Downloads\Suivi des Incidents DP 2026 FF 06.05.2026.xlsm'

try:
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    sheet = wb['Observations']
    
    print(f"\n--- Reading full sheet: Observations ---")
    for row in sheet.iter_rows(values_only=True):
        print(row)
            
except Exception as e:
    print(f"Error: {e}")
