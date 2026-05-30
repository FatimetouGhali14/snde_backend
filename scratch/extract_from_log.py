import openpyxl

file_path = r'C:\Users\hp\Downloads\Suivi des Incidents DP 2026 FF 06.05.2026.xlsm'

try:
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    sheet = wb['Suivi des incidents']
    
    sites_forages = {}
    
    # Headers are on row 2
    for row in sheet.iter_rows(min_row=3, values_only=True):
        if not any(row): continue
        site = row[1]
        forage = row[2] # Localisation
        brigade = row[7]
        
        if site and forage and brigade:
            if site not in sites_forages:
                sites_forages[site] = {"brigade": brigade, "forages": set()}
            sites_forages[site]["forages"].add(forage)
            
    # Print results
    total_forages = 0
    for site, info in sites_forages.items():
        print(f"Site: {site} ({info['brigade']})")
        print(f"Forages: {sorted(list(info['forages']))}")
        total_forages += len(info['forages'])
        
    print(f"\nTotal unique forages found in incidents: {total_forages}")
    print(f"Total sites: {len(sites_forages)}")

except Exception as e:
    print(f"Error: {e}")
