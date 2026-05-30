import openpyxl

file_path = r'C:\Users\hp\Downloads\Suivi des Incidents DP 2026 FF 06.05.2026.xlsm'

try:
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    sheet = wb['Suivi des incidents']
    
    unique_locs = set()
    for row in sheet.iter_rows(min_row=3, max_row=1000, values_only=True):
        if row[2]: # Localisation
            unique_locs.add(str(row[2]).strip())
            
    print(f"Total unique localisations: {len(unique_locs)}")
    print("First 50 unique localisations:")
    for loc in sorted(list(unique_locs))[:50]:
        print(loc)
            
except Exception as e:
    print(f"Error: {e}")
