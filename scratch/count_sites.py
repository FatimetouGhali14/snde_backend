import openpyxl

file_path = r'C:\Users\hp\Downloads\Suivi des Incidents DP 2026 FF 06.05.2026.xlsm'

try:
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    sheet = wb['Suivi des incidents']
    
    sites = set()
    for row in sheet.iter_rows(min_row=3, max_row=2000, values_only=True):
        if row[1]: # Site
            sites.add(str(row[1]).strip())
            
    print(f"Total unique sites: {len(sites)}")
    print(sorted(list(sites)))
            
except Exception as e:
    print(f"Error: {e}")
