import openpyxl

file_path = r'C:\Users\hp\Downloads\Suivi des Incidents DP 2026 FF 06.05.2026.xlsm'

try:
    wb = openpyxl.load_workbook(file_path, read_only=False, data_only=True)
    print(f"Defined Names: {list(wb.defined_names.keys())}")
    
    for dn in wb.defined_names.definedName:
        print(f"Name: {dn.name}, Dest: {dn.destinations}")
            
except Exception as e:
    print(f"Error: {e}")
