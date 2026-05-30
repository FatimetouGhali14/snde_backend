import requests

data = {
    "matricule": "ADMIN001",
    "password": "Admin1234!"
}

try:
    print("Test login...")
    r = requests.post("http://localhost:5000/api/auth/login", json=data)
    print("Status code:", r.status_code)
    print("Response:", r.json())
except Exception as e:
    print("Error:", e)
