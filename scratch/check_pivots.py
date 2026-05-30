import openpyxl

file_path = r'C:\Users\hp\Downloads\Suivi des Incidents DP 2026 FF 06.05.2026.xlsm'

try:
    wb = openpyxl.load_workbook(file_path)
    for sn in wb.sheetnames:
        sheet = wb[sn]
        if hasattr(sheet, '_pivots') and sheet._pivots:
            print(f"Sheet {sn} has pivot tables!")
            for pivot in sheet._pivots:
                print(f"Pivot: {pivot.name}, Source: {pivot.cache.cacheSource}")
            
except Exception as e:
    print(f"Error: {e}")
