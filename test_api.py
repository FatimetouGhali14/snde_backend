import requests
from middleware.auth import generate_token

# Mock un utilisateur pour le test
token = generate_token("123", "test@snde.mr", "admin")
headers = {"Authorization": f"Bearer {token}"}

try:
    print("Test /api/forages...")
    r1 = requests.get("http://localhost:5000/api/forages", headers=headers)
    print("Status code:", r1.status_code)
    print("Response:", r1.json())
except Exception as e:
    print("Error:", e)

try:
    print("\nTest /api/forages/carte...")
    r2 = requests.get("http://localhost:5000/api/forages/carte", headers=headers)
    print("Status code:", r2.status_code)
    print("Response:", r2.json())
except Exception as e:
    print("Error:", e)
